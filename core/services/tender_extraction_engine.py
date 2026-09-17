import logging
from pathlib import Path
from urllib.parse import urlparse

from core.services.document_fetcher import DocumentFetcher
from core.services.html_extractor import HTMLExtractor
from core.services.pdf_extractor import PDFExtractor
from core.services.source_resolver import SourceResolver
from core.services.tender_parser import TenderParser
from .document_cleaner import DocumentCleaner

logger = logging.getLogger("livehooah")


class TenderExtractionEngine:
    """
    MASTER extraction layer.

    URL
        ↓
    Resolve URL
        ↓
    Fetch document
        ↓
    Detect document type
        ↓
    Extract PDF / HTML text
        ↓
    Clean document
        ↓
    Validate extracted content
        ↓
    Parse structured tender
        ↓
    Validate parsed result
        ↓
    Return structured tender

    This layer is responsible for determining whether a source
    contains usable tender-related content.

    It is NOT responsible for final Livehooah qualification.
    Business relevance scoring belongs to the scoring/qualification
    layers downstream.

    Important:
        This class preserves the existing public contract.

        Successful extraction:
            returns structured tender dict

        Failed extraction:
            returns {}
    """

    MIN_TEXT_LENGTH = 120

    REQUIRED_KEYWORDS = (
        "tender",
        "rfp",
        "request for proposal",
        "eoi",
        "expression of interest",
        "bid",
        "consultancy",
        "empanelment",
        "submission",
        "technical bid",
        "financial bid",
        "scope of work",
    )

    # These are strong indicators that the fetched content itself
    # is an error/access page rather than a tender document.
    STRONG_BAD_PAGE_PATTERNS = (
        "page not found",
        "access denied",
        "forbidden",
        "captcha",
    )

    # These phrases can legitimately occur inside otherwise valid
    # documents, especially when HTML/PDF content contains navigation
    # or website text. They therefore require contextual validation.
    CONTEXTUAL_BAD_PAGE_PATTERNS = (
        "home page",
        "search results",
    )

    INVALID_URL_PREFIXES = (
        "javascript:",
        "mailto:",
        "tel:",
        "#",
    )

    PDF_CONTENT_TYPES = (
        "application/pdf",
        "application/x-pdf",
        "application/octet-stream",
    )

    # ------------------------------------------------------------------
    # REJECTION REASONS
    # ------------------------------------------------------------------

    REASON_EMPTY_URL = "EMPTY_URL"
    REASON_INVALID_URL = "INVALID_URL"
    REASON_URL_RESOLUTION_FAILED = "URL_RESOLUTION_FAILED"
    REASON_FETCH_FAILED = "FETCH_FAILED"
    REASON_EMPTY_CONTENT = "EMPTY_CONTENT"
    REASON_TEXT_EXTRACTION_FAILED = "TEXT_EXTRACTION_FAILED"
    REASON_TEXT_EXTRACTION_EMPTY = "TEXT_EXTRACTION_EMPTY"
    REASON_CLEANING_FAILED = "CLEANING_FAILED"
    REASON_INVALID_CLEANED_TEXT = "INVALID_CLEANED_TEXT"
    REASON_TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    REASON_INVALID_ERROR_PAGE = "INVALID_ERROR_PAGE"
    REASON_NAVIGATION_PAGE = "NAVIGATION_PAGE"
    REASON_NO_TENDER_SIGNALS = "NO_TENDER_SIGNALS"
    REASON_PARSER_FAILED = "PARSER_FAILED"
    REASON_INVALID_STRUCTURED_RESULT = (
        "INVALID_STRUCTURED_RESULT"
    )
    REASON_INVALID_TITLE = "INVALID_TITLE"
    REASON_DEADLINE_EXPIRED = "DEADLINE_EXPIRED"

    # ------------------------------------------------------------------

    def __init__(self, save_benchmark_pdfs: bool = False):
        self.fetcher = DocumentFetcher()
        self.pdf_extractor = PDFExtractor()
        self.html_extractor = HTMLExtractor()
        self.cleaner = DocumentCleaner()
        self.parser = TenderParser()
        self.resolver = SourceResolver()

        # Development option only.
        self.save_benchmark_pdfs = save_benchmark_pdfs

    # ------------------------------------------------------------------

    def extract(self, url: str) -> dict:
        """
        Execute the complete extraction pipeline.

        Returns:
            dict:
                Structured tender data when extraction and parsing
                succeed.

            {}:
                When the source cannot be safely converted into a
                usable structured tender.

        The method intentionally preserves the existing return
        contract used by the downstream opportunity pipeline.
        """

        if not url:
            self._reject(
                self.REASON_EMPTY_URL,
                url=url,
            )
            return {}

        url = str(url).strip()

        if not url:
            self._reject(
                self.REASON_EMPTY_URL,
                url=url,
            )
            return {}

        if url.lower().startswith(self.INVALID_URL_PREFIXES):
            self._reject(
                self.REASON_INVALID_URL,
                url=url,
            )
            return {}

        # --------------------------------------------------------------
        # URL RESOLUTION
        # --------------------------------------------------------------

        try:
            resolved_url = self.resolver.resolve(url)

        except Exception:
            self._reject(
                self.REASON_URL_RESOLUTION_FAILED,
                url=url,
            )

            logger.exception(
                "Extraction failed: URL resolution exception | "
                "url=%s",
                url,
            )

            return {}

        if not resolved_url:
            self._reject(
                self.REASON_URL_RESOLUTION_FAILED,
                url=url,
            )

            return {}

        resolved_url = str(resolved_url).strip()

        if not resolved_url:
            self._reject(
                self.REASON_URL_RESOLUTION_FAILED,
                url=url,
            )

            return {}

        # --------------------------------------------------------------
        # DOCUMENT FETCH
        # --------------------------------------------------------------

        try:
            doc = self.fetcher.fetch(resolved_url)

        except Exception:
            self._reject(
                self.REASON_FETCH_FAILED,
                url=resolved_url,
            )

            logger.exception(
                "Extraction failed: fetch exception | "
                "url=%s",
                resolved_url,
            )

            return {}

        if not isinstance(doc, dict):
            self._reject(
                self.REASON_FETCH_FAILED,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: invalid fetch response type | "
                "url=%s | type=%s",
                resolved_url,
                type(doc).__name__,
            )

            return {}

        success = bool(doc.get("success"))

        if not success:
            self._reject(
                self.REASON_FETCH_FAILED,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: document fetch unsuccessful | "
                "url=%s | status=%s | content_type=%s | error=%s",
                resolved_url,
                doc.get("status_code"),
                doc.get("content_type"),
                doc.get("error") or doc.get("message"),
            )

            return {}

        content = doc.get("content")

        if not content:
            self._reject(
                self.REASON_EMPTY_CONTENT,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: fetch succeeded but content "
                "is empty | url=%s | content_type=%s",
                resolved_url,
                doc.get("content_type"),
            )

            return {}

        content_type = str(
            doc.get("content_type") or ""
        ).lower().strip()

        # --------------------------------------------------------------
        # DOCUMENT TYPE DETECTION
        # --------------------------------------------------------------

        is_pdf = self._is_pdf_document(
            url=resolved_url,
            content_type=content_type,
        )

        document_type = "pdf" if is_pdf else "html"

        logger.debug(
            "Document fetched successfully | "
            "url=%s | type=%s | content_type=%s | bytes=%s",
            resolved_url,
            document_type,
            content_type or "unknown",
            self._get_content_size(content),
        )

        # --------------------------------------------------------------
        # TEXT EXTRACTION
        # --------------------------------------------------------------

        try:

            if is_pdf:

                if self.save_benchmark_pdfs:
                    self._save_benchmark_pdf(
                        resolved_url,
                        content,
                    )

                text = self.pdf_extractor.extract_text(
                    content
                )

            else:

                text = self.html_extractor.extract_text(
                    content
                )

        except Exception:

            self._reject(
                self.REASON_TEXT_EXTRACTION_FAILED,
                url=resolved_url,
            )

            logger.exception(
                "Extraction failed: text extraction exception | "
                "type=%s | url=%s",
                document_type,
                resolved_url,
            )

            return {}

        if text is None:

            self._reject(
                self.REASON_TEXT_EXTRACTION_EMPTY,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: extractor returned None | "
                "type=%s | url=%s",
                document_type,
                resolved_url,
            )

            return {}

        logger.info("=" * 80)
        logger.info("TEXT EXTRACTED")
        logger.info("Characters: %d", len(text))
        logger.info("Preview:\n%s", text[:500])
        logger.info("=" * 80)

        # --------------------------------------------------------------
        # CLEANING
        # --------------------------------------------------------------

        try:

            text = self.cleaner.clean(text)

        except Exception:

            self._reject(
                self.REASON_CLEANING_FAILED,
                url=resolved_url,
            )

            logger.exception(
                "Extraction failed: document cleaning exception | "
                "url=%s",
                resolved_url,
            )

            return {}

        if not isinstance(text, str):

            self._reject(
                self.REASON_INVALID_CLEANED_TEXT,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: cleaner returned invalid type | "
                "url=%s | type=%s",
                resolved_url,
                type(text).__name__,
            )

            return {}

        text = text.strip()

        logger.info("=" * 80)
        logger.info("TEXT AFTER CLEANING")
        logger.info("Characters: %d", len(text))
        logger.info("Preview:\n%s", text[:500])
        logger.info("=" * 80)

        logger.debug(
            "Text extraction completed | "
            "url=%s | extracted_characters=%d",
            resolved_url,
            len(text),
        )

        # --------------------------------------------------------------
        # DOCUMENT VALIDATION
        # --------------------------------------------------------------

        logger.info("Calling _is_valid_document()")

        if not self._is_valid_document(
            text=text,
            url=resolved_url,
        ):
            return {}

        # --------------------------------------------------------------
        # STRUCTURED PARSING
        # --------------------------------------------------------------

        try:

            logger.info("=" * 80)
            logger.info("Invoking TenderParser")
            logger.info("URL : %s", resolved_url)
            logger.info("Characters : %d", len(text))
            logger.info("=" * 80)

            structured = self.parser.parse(
                text,
                source_url=resolved_url,
            )

            logger.info("=" * 80)
            logger.info("TenderParser returned")
            logger.info("Type : %s", type(structured).__name__)
            logger.info("Empty : %s", not bool(structured))
            logger.info("=" * 80)

        except Exception:

            self._reject(
                self.REASON_PARSER_FAILED,
                url=resolved_url,
            )

            logger.exception(
                "Extraction failed: parser exception | "
                "url=%s",
                resolved_url,
            )

            return {}

        if not isinstance(structured, dict):

            self._reject(
                self.REASON_INVALID_STRUCTURED_RESULT,
                url=resolved_url,
            )

            logger.warning(
                "Extraction failed: parser returned invalid type | "
                "url=%s | type=%s",
                resolved_url,
                type(structured).__name__,
            )

            return {}

        if structured == {}:

            logger.warning(
                "TenderParser returned an empty dictionary | url=%s",
                resolved_url,
            )

            return {}

        logger.info("=" * 80)
        logger.info("Tender Parser Output")
        logger.info("URL: %s", resolved_url)

        for key, value in structured.items():
            logger.info("%-20s : %s", key, value)

        logger.info("=" * 80)

        structured["source_url"] = resolved_url

        # --------------------------------------------------------------
        # STRUCTURED RESULT VALIDATION
        # --------------------------------------------------------------

        if not self._is_valid_structured_tender(
            structured
        ):

            # The document fetched and parsed without error — the
            # parser itself rejected the structured result (e.g. an
            # invalid/too-short title). This is distinct from a
            # fetch/extraction failure, so it gets its own message.
            logger.warning(
                "Parser rejected document | %s",
                resolved_url,
            )

            return {}

        logger.debug(
            "Successfully parsed tender | "
            "url=%s | title=%s",
            resolved_url,
            structured.get("title", ""),
        )

        return structured

    # ------------------------------------------------------------------

    def _save_benchmark_pdf(
        self,
        url: str,
        content: bytes,
    ) -> None:
        """
        Save downloaded PDFs for benchmarking.

        This is intended only for parser development and regression
        testing. It is disabled by default.
        """

        folder = Path(
            "data/benchmark/pdfs"
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        parsed = urlparse(url)

        filename = Path(
            parsed.path
        ).name

        if not filename:
            filename = "document.pdf"

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        filepath = folder / filename

        if not filepath.exists():

            filepath.write_bytes(content)

            logger.debug(
                "Saved benchmark PDF: %s",
                filepath,
            )

    # ------------------------------------------------------------------

    def _is_pdf_document(
        self,
        url: str,
        content_type: str,
    ) -> bool:
        """
        Determine whether the fetched document should be processed
        using the PDF extractor.

        Content-Type is preferred, but the URL extension is used as
        a fallback because some government servers incorrectly return
        generic content types.
        """

        normalized_content_type = (
            content_type or ""
        ).lower().strip()

        if normalized_content_type.startswith(
            "application/pdf"
        ):
            return True

        if normalized_content_type in (
            self.PDF_CONTENT_TYPES
        ):
            return True

        parsed = urlparse(url)

        path = (
            parsed.path or ""
        ).lower()

        return path.endswith(".pdf")

    # ------------------------------------------------------------------

    def _is_valid_document(
        self,
        text: str,
        url: str,
    ) -> bool:
        """
        Validate extracted text before invoking TenderParser.

        This is a document usability check.

        It does not perform final Livehooah business
        qualification.
        """

        logger.info("=" * 80)
        logger.info("VALIDATING DOCUMENT")
        logger.info("Characters: %d", len(text))
        logger.info("=" * 80)

        if not text:

            self._reject(
                self.REASON_TEXT_EXTRACTION_EMPTY,
                url=url,
            )

            logger.warning(
                "Document rejected: empty extracted text | "
                "url=%s",
                url,
            )

            return False

        text = text.strip()

        text_length = len(text)

        if text_length < self.MIN_TEXT_LENGTH:

            self._reject(
                self.REASON_TEXT_TOO_SHORT,
                url=url,
            )

            logger.warning(
                "Document rejected: extracted text too short | "
                "url=%s | characters=%d | minimum=%d",
                url,
                text_length,
                self.MIN_TEXT_LENGTH,
            )

            self._print_preview(text)

            return False

        lower = text.lower()

        # Only inspect the beginning and end of long documents.
        # This avoids rejecting valid tenders because of unrelated
        # words occurring deep inside the document.

        head = lower[:3000]

        tail = (
            lower[-1000:]
            if len(lower) > 3000
            else ""
        )

        window = head + tail

        # Strong error-page indicators can still reject the document
        # when found in the inspected error-prone regions.

        for pattern in self.STRONG_BAD_PAGE_PATTERNS:

            if pattern in window:

                self._reject(
                    self.REASON_INVALID_ERROR_PAGE,
                    url=url,
                )

                logger.warning(
                    "Document rejected: invalid/error page "
                    "pattern | url=%s | pattern=%s",
                    url,
                    pattern,
                )

                self._print_preview(text)

                return False

        # "home page" and "search results" are not automatically
        # considered fatal.

        if self._looks_like_navigation_or_error_page(
            text=text,
            window=window,
        ):

            self._reject(
                self.REASON_NAVIGATION_PAGE,
                url=url,
            )

            return False

        score = self._document_score(text)

        logger.debug(
            "Document validation completed | "
            "url=%s | characters=%d | relevance_score=%d",
            url,
            text_length,
            score,
        )

        if score < 2:

            self._reject(
                self.REASON_NO_TENDER_SIGNALS,
                url=url,
            )

            logger.warning(
                "Document rejected: insufficient tender-related "
                "signals | url=%s | relevance_score=%d",
                url,
                score,
            )

            self._print_preview(text)

            return False

        logger.info("Document validation PASSED")

        return True

    # ------------------------------------------------------------------

    def _looks_like_navigation_or_error_page(
        self,
        text: str,
        window: str,
    ) -> bool:
        """
        Detect pages that are primarily navigation/error pages.

        Phrases such as "home page" and "search results" are not
        sufficient by themselves to reject a document. They become
        meaningful only when combined with multiple navigation/error
        signals and little actual document content.
        """

        lower = text.lower()

        contextual_pattern_count = sum(
            1
            for pattern in (
                self.CONTEXTUAL_BAD_PAGE_PATTERNS
            )
            if pattern in window
        )

        if contextual_pattern_count == 0:
            return False

        navigation_signals = (
            "home",
            "homepage",
            "main menu",
            "menu",
            "navigation",
            "search",
            "search results",
            "back to",
            "return to",
            "click here",
            "404",
            "not found",
        )

        navigation_signal_count = sum(
            1
            for signal in navigation_signals
            if signal in window
        )

        # A genuinely short page containing multiple navigation
        # signals is more likely to be an error/navigation page
        # than a tender.

        if (
            len(text) <= 1200
            and navigation_signal_count >= 3
        ):

            logger.warning(
                "Document rejected: content appears to be a "
                "navigation/error page | signals=%d",
                navigation_signal_count,
            )

            self._print_preview(text)

            return True

        return False

    # ------------------------------------------------------------------

    def _is_valid_structured_tender(
        self,
        structured: dict,
    ) -> bool:
        """
        Validate the structured output returned by TenderParser.

        The parser is intentionally permissive and extracts as much
        information as possible. This validation ensures that the
        minimum data required by downstream components is present.

        Deadline handling:

            - A clearly expired deadline is rejected.
            - A deadline occurring today is kept.
            - A future deadline is kept.
            - A missing deadline is not rejected here.

        The deadline value is intentionally handled defensively
        because TenderParser may return different date-like formats.
        """

        if not structured:

            self._reject(
                self.REASON_INVALID_STRUCTURED_RESULT
            )

            logger.debug(
                "Parser returned empty structured data."
            )

            return False

        title = (
            structured.get("title")
            or ""
        ).strip()

        if len(title) < 10:

            self._reject(
                self.REASON_INVALID_TITLE
            )

            logger.debug(
                "Rejected parsed tender: title too short | "
                "title=%r",
                title,
            )

            return False

        return True

    # ------------------------------------------------------------------

    def _print_preview(
        self,
        text: str,
    ) -> None:
        """
        Log a short preview of rejected documents to aid debugging.
        """

        preview = (
            text[:500]
            .replace("\n", " ")
            .replace("\r", " ")
        )

        logger.debug("-" * 80)

        logger.debug(
            "Document Preview: %s",
            preview,
        )

        logger.debug("-" * 80)

    # ------------------------------------------------------------------

    def _get_content_size(
        self,
        content,
    ) -> int:
        """
        Return the approximate size of fetched content.

        This is used only for diagnostics and avoids assuming that
        every fetcher response contains bytes.
        """

        try:
            return len(content)

        except TypeError:
            return 0

    # ------------------------------------------------------------------

    def _document_score(
        self,
        text: str,
    ) -> int:
        """
        Compute a lightweight document usability score.

        This is NOT Livehooah qualification scoring.

        Its purpose is only to filter obviously invalid or unrelated
        pages before invoking TenderParser.

        Final business relevance must be handled downstream by the
        scoring and qualification layers.
        """

        lower = text.lower()

        score = 0

        # Keyword relevance.

        for keyword in self.REQUIRED_KEYWORDS:

            if keyword in lower:

                score += 2

        # Document length contributes modestly to confidence.

        if len(text) > 1000:

            score += 2

        if len(text) > 5000:

            score += 2

        return score

    # ------------------------------------------------------------------

    def _reject(
        self,
        reason: str,
        url: str = "",
    ) -> None:
        """
        Log a normalized extraction rejection reason.

        This method intentionally does not alter the return contract
        of the extraction engine.

        The pipeline still receives:
            {}

        The logs now expose:
            reason=...
        """

        if url:

            logger.warning(
                "EXTRACTION_REJECTED | "
                "reason=%s | url=%s",
                reason,
                url,
            )

        else:

            logger.warning(
                "EXTRACTION_REJECTED | "
                "reason=%s",
                reason,
            )