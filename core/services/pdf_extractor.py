import re

import fitz  # PyMuPDF

from utils.logger import logger


class PDFExtractor:
    """
    Extract raw text from PDF documents.

    Responsibilities
    ----------------
    - Open PDF safely
    - Extract readable text
    - Ignore useless pages
    - Remove repeated headers/footers
    - Clean extracted text

    NOT responsible for
    -------------------
    - OCR
    - Tender parsing
    - Metadata extraction
    """

    MIN_PAGE_CHARACTERS = 30
    MIN_PAGE_WORDS = 5
    MIN_ALPHA_CHARACTERS = 15

    def extract_text(
        self,
        pdf_bytes: bytes,
    ) -> str:
        """
        Convert PDF bytes into cleaned text.

        Args:
            pdf_bytes:
                Raw PDF bytes returned by DocumentFetcher.

        Returns:
            Clean extracted text.
        """

        if not pdf_bytes:

            logger.warning(
                "PDF extraction skipped: empty document."
            )

            return ""

        try:

            with fitz.open(
                stream=pdf_bytes,
                filetype="pdf",
            ) as document:

                total_pages = len(document)

                logger.info(
                    "PDF opened successfully | pages=%s",
                    total_pages,
                )

                extracted_pages = []

                skipped_pages = 0

                total_characters = 0

                for page_number in range(total_pages):

                    page = document.load_page(
                        page_number
                    )

                    page_text = self._extract_page_text(
                        page
                    )

                    if not self._is_useful_page(
                        page_text
                    ):

                        skipped_pages += 1

                        logger.debug(
                            "Skipping low-value page %s",
                            page_number + 1,
                        )

                        continue

                    extracted_pages.append(
                        page_text
                    )

                    total_characters += len(
                        page_text
                    )

                logger.info(
                    "PDF extraction complete | "
                    "pages=%s | useful=%s | skipped=%s | chars=%s",
                    total_pages,
                    len(extracted_pages),
                    skipped_pages,
                    total_characters,
                )

                if not extracted_pages:

                    logger.warning(
                        "PDF contains no extractable text."
                    )

                    return ""

                cleaned_pages = (
                    self._remove_repeated_headers(
                        extracted_pages
                    )
                )

                full_text = "\n\n".join(
                    cleaned_pages
                )

                return self._clean_text(
                    full_text
                )

        except Exception:

            logger.exception(
                "PDF extraction failed."
            )

            return ""
        
        # ------------------------------------------------------------------
    # Page Extraction
    # ------------------------------------------------------------------

    def _extract_page_text(
        self,
        page,
    ) -> str:
        """
        Extract readable text from a single PDF page.

        Returns cleaned page text before global document cleanup.
        """

        try:

            text = page.get_text(
                "text",
                sort=True,
            )

        except Exception:

            logger.exception(
                "Failed to extract page text."
            )

            return ""

        if not text:

            return ""

        text = text.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        return text.strip()

    # ------------------------------------------------------------------
    # Page Quality
    # ------------------------------------------------------------------

    def _is_useful_page(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether a page contains useful text.

        Filters out:

        - blank pages
        - separator pages
        - image-only pages
        - signature pages
        - pages with almost no readable content
        """

        if not text:

            return False

        text = text.strip()

        if len(text) < self.MIN_PAGE_CHARACTERS:

            return False

        words = text.split()

        if len(words) < self.MIN_PAGE_WORDS:

            return False

        alpha_count = sum(
            character.isalpha()
            for character in text
        )

        if alpha_count < self.MIN_ALPHA_CHARACTERS:

            return False

        # Reject pages that are mostly numbers
        digit_count = sum(
            character.isdigit()
            for character in text
        )

        if (
            digit_count > alpha_count
            and alpha_count < 50
        ):
            return False

        # Reject pages that mostly contain symbols
        symbol_count = sum(
            not c.isalnum() and not c.isspace()
            for c in text
        )

        if (
            symbol_count > alpha_count
            and alpha_count < 40
        ):
            return False

        return True
        # ------------------------------------------------------------------
    # Header / Footer Removal
    # ------------------------------------------------------------------

    def _remove_repeated_headers(
        self,
        pages,
    ):
        """
        Remove repeated headers and footers that appear on most pages.

        Government tender PDFs often repeat items like:

            Government of India
            Page 5 of 42
            www.xyz.gov.in

        Removing them significantly improves parser accuracy.
        """

        if len(pages) <= 2:
            return pages

        header_counts = {}
        footer_counts = {}

        # ----------------------------------------------------------
        # Count repeated first and last lines
        # ----------------------------------------------------------

        for page in pages:

            lines = [
                line.strip()
                for line in page.split("\n")
                if line.strip()
            ]

            if not lines:
                continue

            header = lines[0]
            footer = lines[-1]

            header_counts[header] = (
                header_counts.get(header, 0) + 1
            )

            footer_counts[footer] = (
                footer_counts.get(footer, 0) + 1
            )

        repeated_headers = {
            line
            for line, count in header_counts.items()
            if count >= max(2, len(pages) // 2)
        }

        repeated_footers = {
            line
            for line, count in footer_counts.items()
            if count >= max(2, len(pages) // 2)
        }

        cleaned_pages = []

        # ----------------------------------------------------------
        # Remove repeated lines
        # ----------------------------------------------------------

        for page in pages:

            lines = [
                line.strip()
                for line in page.split("\n")
                if line.strip()
            ]

            if not lines:
                continue

            if (
                lines
                and lines[0] in repeated_headers
            ):
                lines = lines[1:]

            if (
                lines
                and lines[-1] in repeated_footers
            ):
                lines = lines[:-1]

            cleaned_pages.append(
                "\n".join(lines)
            )

        logger.debug(
            "Removed %s repeated headers and %s repeated footers.",
            len(repeated_headers),
            len(repeated_footers),
        )

        return cleaned_pages
        # ------------------------------------------------------------------
    # Text Cleaning
    # ------------------------------------------------------------------

    def _clean_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize extracted PDF text.

        This method intentionally preserves paragraph structure while
        removing common PDF extraction artifacts.
        """

        if not text:
            return ""

        # ----------------------------------------------
        # Normalize line endings
        # ----------------------------------------------

        text = text.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        # ----------------------------------------------
        # Normalize tabs
        # ----------------------------------------------

        text = text.replace(
            "\t",
            " ",
        )

        # ----------------------------------------------
        # Remove excessive spaces
        # ----------------------------------------------

        text = re.sub(
            r"[ ]{2,}",
            " ",
            text,
        )

        # ----------------------------------------------
        # Remove spaces around newlines
        # ----------------------------------------------

        text = re.sub(
            r" *\n *",
            "\n",
            text,
        )

        # ----------------------------------------------
        # Remove excessive blank lines
        # ----------------------------------------------

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        # ----------------------------------------------
        # Remove page numbers
        # Examples:
        #
        #   Page 4
        #   Page 4 of 28
        # ----------------------------------------------

        text = re.sub(
            r"(?im)^page\s+\d+(\s+of\s+\d+)?\s*$",
            "",
            text,
        )

        # ----------------------------------------------
        # Remove form-feed characters
        # ----------------------------------------------

        text = text.replace(
            "\f",
            "",
        )

        # ----------------------------------------------
        # Remove trailing spaces
        # ----------------------------------------------

        cleaned_lines = []

        for line in text.split("\n"):

            line = line.strip()

            if not line:
                cleaned_lines.append("")
                continue

            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # Final cleanup

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()
        # ------------------------------------------------------------------
    # Statistics Helpers
    # ------------------------------------------------------------------

    def _count_words(
        self,
        text: str,
    ) -> int:
        """
        Count words in extracted text.
        """

        if not text:
            return 0

        return len(text.split())

    def _count_alpha(
        self,
        text: str,
    ) -> int:
        """
        Count alphabetic characters.
        """

        if not text:
            return 0

        return sum(
            character.isalpha()
            for character in text
        )

    def _count_digits(
        self,
        text: str,
    ) -> int:
        """
        Count numeric characters.
        """

        if not text:
            return 0

        return sum(
            character.isdigit()
            for character in text
        )

    # ------------------------------------------------------------------
    # Public Diagnostics
    # ------------------------------------------------------------------

    def get_document_statistics(
        self,
        text: str,
    ) -> dict:
        """
        Return simple extraction statistics.

        Useful for debugging extraction quality without
        involving the TenderParser.
        """

        if not text:

            return {
                "characters": 0,
                "words": 0,
                "lines": 0,
                "alphabetic": 0,
                "digits": 0,
            }

        return {
            "characters": len(text),
            "words": self._count_words(text),
            "lines": len(text.splitlines()),
            "alphabetic": self._count_alpha(text),
            "digits": self._count_digits(text),
        }