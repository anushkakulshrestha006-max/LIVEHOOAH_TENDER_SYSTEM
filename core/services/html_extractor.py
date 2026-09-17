import logging
import re
import unicodedata
from collections import Counter
from typing import List, Optional

from bs4 import BeautifulSoup, Comment, Tag

logger = logging.getLogger("livehooah")


class HTMLExtractor:
    """
    Extracts readable text from HTML pages.

    Responsibilities:
        - Parse HTML
        - Remove boilerplate/layout elements
        - Preserve meaningful content
        - Preserve tables
        - Normalize whitespace

    NOT responsible for:
        - Tender parsing
        - Metadata extraction
        - Business logic
        - Document validation
    """

    REMOVABLE_TAGS = (
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "template",
        "dialog",
    )

    LAYOUT_TAGS = (
        "header",
        "footer",
        "nav",
        "aside",
        "form",
    )

    REMOVABLE_KEYWORDS = {
        "nav",
        "navbar",
        "navigation",
        "menu",
        "sidebar",
        "footer",
        "header",
        "breadcrumb",
        "breadcrumbs",
        "social",
        "share",
        "cookie",
        "advert",
        "ads",
        "banner",
        "topbar",
        "top-bar",
        "toolbar",
        "masthead",
        "quicklinks",
        "quick-links",
        "leftmenu",
        "rightmenu",
        "left-nav",
        "right-nav",
        "announcement",
        "accessibility",
        "skip-link",
        "language",
        "search-box",
        "searchbar",
        "pagination",
        "related",
        "newsletter",
        "login",
        "signin",
        "signup",
        "popup",
        "modal",
        "overlay",
        "floating",
        "cookie-consent",
        "consent",
        "consent-banner",
        "gdpr",
        "privacy-banner",
        "accept-cookie",
        "acceptcookies",
        "cookiebanner",
    }

    MAIN_SELECTORS = (
        "main",
        "article",
        '[role="main"]',
    )

    # Hints used when scoring fallback content containers that don't
    # use semantic tags (common on government tender sites).
    CONTENT_HINTS = (
        "content",
        "page-content",
        "main-content",
        "maincontent",
        "container",
        "article",
        "tender",
        "document",
    )

    # Keywords that indicate a container is likely to hold genuine
    # tender/procurement content, used to bias content-root scoring.
    TENDER_KEYWORDS = (
        "tender",
        "bid",
        "proposal",
        "consultancy",
        "scope of work",
        "deadline",
        "emd",
        "corrigendum",
        "rfp",
        "eoi",
    )

    # Keywords that indicate a container is likely navigation/menu
    # chrome rather than genuine document content.
    NAV_HEAVY_KEYWORDS = (
        "home",
        "contact us",
        "about us",
        "login",
        "sign in",
        "search",
        "sitemap",
        "downloads",
        "archive",
        "circulars",
        "recruitment",
        "latest news",
    )

    HIDDEN_STYLES = (
        "display:none",
        "display: none",
        "visibility:hidden",
        "visibility: hidden",
        "opacity:0",
        "opacity: 0",
        "opacity:0.0",
        "height:0px",
        "height: 0px",
        "width:0px",
        "width: 0px",
    )

    # Content-root scoring constants (tunable without touching logic).
    MIN_CONTAINER_TEXT_LENGTH = 300
    CONTENT_HINT_BONUS = 500
    TABLE_BONUS_PER_TABLE = 200
    HEADING_BONUS_PER_HEADING = 50
    TENDER_KEYWORD_BONUS = 100
    LINK_FARM_PENALTY = 200
    NAV_HEAVY_PENALTY = 300
    NAV_HEAVY_KEYWORD_THRESHOLD = 3

    # Table filtering constants.
    MIN_TABLE_TEXT_LENGTH = 120
    TABLE_NAV_KEYWORD_THRESHOLD = 2

    # Repeated-line filtering constants.
    MIN_LINES_FOR_REPEAT_FILTERING = 20
    REPEATED_LINE_MAX_LENGTH = 80
    REPEATED_LINE_MIN_COUNT = 3

    # Boilerplate detection constants.
    MIN_MEANINGFUL_TEXT_LENGTH = 150
    MIN_MEANINGFUL_WORD_COUNT = 30
    NOISE_KEYWORD_THRESHOLD = 4

    NOISE_KEYWORDS = (
        "home",
        "login",
        "sign in",
        "search",
        "privacy policy",
        "copyright",
        "all rights reserved",
    )

    # Pages that indicate the crawler hit a block/error page rather
    # than genuine tender content.
    BLOCKED_PAGE_KEYWORDS = (
        "404",
        "access denied",
        "forbidden",
        "page not found",
        "javascript required",
        "captcha",
        "verify you're human",
        "verify you are human",
        "cloudflare",
        "security check",
        "attention required",
        "checking your browser",
    )

    _HEADING_TAG_RE = re.compile(r"^h[1-6]$")
    _SEPARATOR_LINE_RE = re.compile(r"[-_=]{3,}")
    _MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
    _PUNCTUATION_RE = re.compile(r"[^\w\s]")

    # ------------------------------------------------------------------

    def extract_text(self, html_bytes: bytes) -> str:
        """
        Convert raw HTML bytes into readable plain text.
        """

        if not html_bytes:
            return ""

        try:
            html = html_bytes.decode("utf-8", errors="ignore")

            logger.debug(
                "Starting HTML extraction (%d bytes)",
                len(html_bytes),
            )

            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception as exc:
                logger.debug(
                    "lxml parser failed: %s. Falling back to html.parser.",
                    exc,
                )
                soup = BeautifulSoup(html, "html.parser")

            removed = 0

            removed += self._remove_comments(soup)
            removed += self._remove_unwanted_tags(soup)
            removed += self._remove_layout_tags(soup)
            removed += self._remove_hidden_elements(soup)
            removed += self._remove_layout_elements(soup)

            root = self._select_content_root(soup)

            self._preserve_line_breaks(root)
            self._preserve_headings(root)
            self._preserve_paragraphs(root)
            self._preserve_lists(root)
            self._preserve_definition_lists(root)
            tables_processed = self._preserve_tables(root)

            text = root.get_text(separator="\n")

            cleaned = self._clean_text(text)

            logger.debug(
                (
                    "HTML extraction complete | "
                    "removed=%d | "
                    "chars=%d"
                ),
                removed,
                len(cleaned),
            )

            logger.debug(
                (
                    "HTML Stats | lines=%d | words=%d | tables=%d | "
                    "headings=%d | lists=%d | paragraphs=%d | "
                    "nodes_removed=%d"
                ),
                len(cleaned.splitlines()),
                len(cleaned.split()),
                tables_processed,
                len(root.find_all(self._HEADING_TAG_RE))
                if hasattr(root, "find_all")
                else 0,
                len(root.find_all("li")) if hasattr(root, "find_all") else 0,
                len(root.find_all("p")) if hasattr(root, "find_all") else 0,
                removed,
            )

            if self._looks_like_boilerplate(cleaned):
                logger.warning(
                    "HTML extraction produced low-information content."
                )

            return cleaned

        except Exception:
            logger.exception("HTML extraction failed.")
            return ""

    # ------------------------------------------------------------------

    def _remove_comments(self, soup: BeautifulSoup) -> int:
        """
        Strip HTML comments, which BeautifulSoup otherwise leaves in
        the tree (and which can otherwise leak into extracted text).
        """

        removed = 0

        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            try:
                comment.extract()
                removed += 1
            except Exception:
                continue

        return removed

    # ------------------------------------------------------------------

    def _select_content_root(self, soup: BeautifulSoup) -> Tag:
        """
        Prefer extracting from the primary document container.

        Many government tender sites do not use semantic tags
        (main/article/role=main), so if none of those are found we
        fall back to scoring candidate div/section containers by
        text length before defaulting to <body>.
        """

        for selector in self.MAIN_SELECTORS:
            try:
                node = soup.select_one(selector)
                if node:
                    logger.debug(
                        "Using content root: %s",
                        selector,
                    )
                    return node
            except Exception:
                continue

        best_node = None
        best_score = 0

        for node in soup.find_all(["div", "section"]):

            try:
                text = node.get_text(" ", strip=True)

                if len(text) < self.MIN_CONTAINER_TEXT_LENGTH:
                    continue

                score = self._score_container(node, text)

                if score > best_score:
                    best_score = score
                    best_node = node

            except Exception:
                continue

        if best_node:
            logger.debug(
                "Using scored container as content root (score=%d).",
                best_score,
            )
            return best_node

        body = soup.body

        if body:
            logger.debug("Using <body> as content root.")
            return body

        logger.debug("Using entire document as content root.")
        return soup

    # ------------------------------------------------------------------

    def _score_container(self, node: Tag, text: str) -> int:
        """
        Score a candidate content-root container.

        Rewards containers that look like genuine document content
        (content-hint classes/ids, tables, headings, tender keywords)
        and penalizes containers that look like navigation or link
        farms.
        """

        attrs = (
            " ".join(node.get("class", []))
            + " "
            + str(node.get("id", ""))
        ).lower()

        score = len(text)

        if any(hint in attrs for hint in self.CONTENT_HINTS):
            score += self.CONTENT_HINT_BONUS

        try:
            table_count = len(node.find_all("table"))
        except Exception:
            table_count = 0

        score += table_count * self.TABLE_BONUS_PER_TABLE

        try:
            heading_count = len(node.find_all(self._HEADING_TAG_RE))
        except Exception:
            heading_count = 0

        score += heading_count * self.HEADING_BONUS_PER_HEADING

        lower_text = text.lower()

        tender_hits = sum(
            keyword in lower_text for keyword in self.TENDER_KEYWORDS
        )

        score += tender_hits * self.TENDER_KEYWORD_BONUS

        try:
            link_count = len(node.find_all("a"))
        except Exception:
            link_count = 0

        try:
            paragraph_count = len(node.find_all("p"))
        except Exception:
            paragraph_count = 0

        if link_count > paragraph_count and link_count > 10:
            score -= self.LINK_FARM_PENALTY

        nav_hits = sum(
            keyword in lower_text for keyword in self.NAV_HEAVY_KEYWORDS
        )

        if nav_hits >= self.NAV_HEAVY_KEYWORD_THRESHOLD:
            score -= self.NAV_HEAVY_PENALTY

        return score

    # ------------------------------------------------------------------

    def _remove_unwanted_tags(self, soup: BeautifulSoup) -> int:
        removed = 0

        for tag in soup(self.REMOVABLE_TAGS):
            try:
                tag.decompose()
                removed += 1
            except Exception:
                continue

        return removed

    # ------------------------------------------------------------------

    def _remove_layout_tags(self, soup: BeautifulSoup) -> int:
        removed = 0

        for tag in soup.find_all(self.LAYOUT_TAGS):
            try:
                tag.decompose()
                removed += 1
            except Exception:
                continue

        return removed

    # ------------------------------------------------------------------

    def _remove_hidden_elements(self, soup: BeautifulSoup) -> int:
        """
        Remove hidden HTML elements.
        """

        removed = 0

        for tag in list(soup.find_all(True)):

            try:
                if tag.has_attr("hidden"):
                    tag.decompose()
                    removed += 1
                    continue

                if str(tag.get("aria-hidden")).lower() == "true":
                    tag.decompose()
                    removed += 1
                    continue

                style = str(tag.get("style", "")).lower()

                if any(token in style for token in self.HIDDEN_STYLES):
                    tag.decompose()
                    removed += 1

            except Exception:
                continue

        return removed

    # ------------------------------------------------------------------

    def _remove_layout_elements(self, soup: BeautifulSoup) -> int:
        """
        Remove elements whose class/id indicates page chrome.
        """

        removed = 0

        for tag in list(soup.find_all(True)):

            try:
                classes = tag.get("class") or []

                if not isinstance(classes, list):
                    classes = [str(classes)]

                class_names = " ".join(classes).lower()
                tag_id = str(tag.get("id") or "").lower()

                combined = f"{class_names} {tag_id}"

                if any(
                    keyword in combined
                    for keyword in self.REMOVABLE_KEYWORDS
                ):
                    tag.decompose()
                    removed += 1

            except Exception:
                continue

        # After layout removal, many pages contain leftover empty
        # containers (e.g. wrapper divs with no remaining text).
        # Strip those out too, except for images which carry no
        # text but may still be meaningful.
        for tag in list(soup.find_all(True)):

            try:
                if not tag.get_text(strip=True):

                    if tag.name not in ("img",):
                        tag.decompose()
                        removed += 1

            except Exception:
                continue

        return removed

    # ------------------------------------------------------------------

    def _preserve_line_breaks(self, root: Tag) -> None:
        """
        Explicitly convert <br> tags into newlines so line breaks
        survive flattening in a predictable way.
        """

        for br in root.find_all("br"):
            try:
                br.replace_with("\n")
            except Exception:
                continue

    # ------------------------------------------------------------------

    def _preserve_headings(self, root: Tag) -> None:
        """
        Preserve heading boundaries so they remain distinguishable after
        flattening the HTML.
        """

        for heading in root.find_all(self._HEADING_TAG_RE):
            try:
                text = heading.get_text(" ", strip=True)

                if not text:
                    heading.decompose()
                    continue

                heading.replace_with(f"\n\n{text}\n")

            except Exception:
                continue

    # ------------------------------------------------------------------

    def _preserve_paragraphs(self, root: Tag) -> None:
        """
        Preserve paragraph boundaries before the tree is flattened,
        so paragraph breaks survive into the extracted text instead
        of being collapsed together.
        """

        for p in root.find_all("p"):

            try:
                text = p.get_text(" ", strip=True)

                if text:
                    p.replace_with(f"\n{text}\n")

            except Exception:
                continue

    # ------------------------------------------------------------------

    def _preserve_lists(self, root: Tag) -> None:
        """
        Preserve ordered and unordered lists.
        """

        for li in root.find_all("li"):

            try:
                text = li.get_text(" ", strip=True)

                if text:
                    li.replace_with(f"\n• {text}")

            except Exception:
                continue

    # ------------------------------------------------------------------

    def _preserve_definition_lists(self, root: Tag) -> None:
        """
        Convert <dl>/<dt>/<dd> definition lists into "Term : Value"
        lines, e.g.:

            EMD : 5000
            Tender Fee : 1000
        """

        for dl in list(root.find_all("dl")):

            try:
                lines = []
                current_term = None

                for child in dl.find_all(["dt", "dd"]):

                    text = child.get_text(" ", strip=True)

                    if not text:
                        continue

                    if child.name == "dt":
                        current_term = text
                    else:
                        if current_term:
                            lines.append(f"{current_term} : {text}")
                            current_term = None
                        else:
                            lines.append(text)

                replacement = ("\n" + "\n".join(lines) + "\n") if lines else ""

                dl.replace_with(replacement)

            except Exception:
                continue

    # ------------------------------------------------------------------

    def _preserve_tables(self, root: Tag) -> int:
        """
        Convert tables into readable row-oriented text.

        Example:

        Deadline | 25-Aug-2026
        EMD | 5000
        Tender Fee | 1000

        Returns the number of tables converted.
        """

        tables_processed = 0

        for table in list(root.find_all("table")):

            try:
                table_text = table.get_text(" ", strip=True).lower()

                # Skip short tables that look like navigation menus
                # rather than genuine tender data (government sites
                # frequently lay out menus as tables).
                if len(table_text) < self.MIN_TABLE_TEXT_LENGTH:
                    continue

                nav_keyword_hits = sum(
                    keyword in table_text
                    for keyword in (
                        "home",
                        "contact",
                        "about",
                        "login",
                        "search",
                    )
                )

                if nav_keyword_hits >= self.TABLE_NAV_KEYWORD_THRESHOLD:
                    continue

                rows = []
                seen = set()

                for tr in table.find_all("tr"):

                    cells = []

                    for cell in tr.find_all(["th", "td"]):

                        value = cell.get_text(
                            " ",
                            strip=True,
                        )

                        value = " ".join(value.split())

                        if value:
                            cells.append(value)

                    if cells:

                        row = " | ".join(cells)

                        if row in seen:
                            continue

                        seen.add(row)
                        rows.append(row)

                if rows:
                    replacement = "\n" + "\n".join(rows) + "\n"
                else:
                    replacement = ""

                table.replace_with(replacement)

                tables_processed += 1

            except Exception:
                continue

        logger.debug(
            "Converted %d HTML tables.",
            tables_processed,
        )

        return tables_processed

    # ------------------------------------------------------------------

    def _clean_text(self, text: str) -> str:
        """
        Normalize extracted text while preserving structure.
        """

        if not text:
            return ""

        text = (
            text.replace("\ufeff", "")
                .replace("\u200b", "")
                .replace("\u200c", "")
                .replace("\u200d", "")
                .replace("\xa0", " ")
        )

        # Normalize Unicode (e.g. full-width characters, OCR-derived
        # HTML) into a canonical composed form.
        text = unicodedata.normalize("NFKC", text)

        lines: List[str] = []

        for line in text.splitlines():

            line = " ".join(line.split())

            if not line:
                continue

            if self._SEPARATOR_LINE_RE.fullmatch(line):
                continue

            lines.append(line)

        lines = self._remove_duplicate_lines(lines)
        lines = self._remove_repeated_blocks(lines)
        lines = self._remove_repeated_pairs(lines)

        cleaned = "\n".join(lines)

        cleaned = self._MULTI_NEWLINE_RE.sub("\n\n", cleaned)

        return cleaned.strip()

    # ------------------------------------------------------------------

    def _remove_duplicate_lines(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove consecutive duplicate lines.
        """

        cleaned: List[str] = []

        previous: Optional[str] = None

        for line in lines:

            if line == previous:
                continue

            cleaned.append(line)
            previous = line

        return cleaned

    # ------------------------------------------------------------------

    def _normalize_for_dedup(self, line: str) -> str:
        """
        Normalize a line for repeat-counting purposes only (not used
        for the output itself): lowercase, strip punctuation, and
        collapse whitespace, so near-identical boilerplate lines like

            "Tender Notice" / "Tender Notice." / "TENDER NOTICE"

        are treated as the same line when deciding what to drop.
        """

        normalized = line.lower()
        normalized = self._PUNCTUATION_RE.sub("", normalized)
        normalized = " ".join(normalized.split())

        return normalized

    # ------------------------------------------------------------------

    def _remove_repeated_blocks(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove highly repetitive lines that usually originate from
        navigation bars, repeated headers, or footers.

        Only removes lines that appear many times while preserving
        legitimate document content. Repeat counting is done on a
        normalized form so near-duplicate lines (differing only in
        case/punctuation/whitespace) are still caught.
        """

        if len(lines) < self.MIN_LINES_FOR_REPEAT_FILTERING:
            return lines

        counts = Counter(self._normalize_for_dedup(line) for line in lines)

        cleaned: List[str] = []

        for line in lines:

            normalized = self._normalize_for_dedup(line)

            if (
                len(line) < self.REPEATED_LINE_MAX_LENGTH
                and counts[normalized] > self.REPEATED_LINE_MIN_COUNT
            ):
                continue

            cleaned.append(line)

        return cleaned

    # ------------------------------------------------------------------

    def _remove_repeated_pairs(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove repeated two-line blocks, such as headers like:

            Government of India
            Ministry of ...
            Government of India
            Ministry of ...

        which duplicate-line and repeated-single-line removal don't
        catch on their own.
        """

        cleaned: List[str] = []
        i = 0

        while i < len(lines):

            if (
                i + 3 < len(lines)
                and lines[i] == lines[i + 2]
                and lines[i + 1] == lines[i + 3]
            ):
                cleaned.append(lines[i])
                cleaned.append(lines[i + 1])
                i += 4
                continue

            cleaned.append(lines[i])
            i += 1

        return cleaned

    # ------------------------------------------------------------------

    def _looks_like_boilerplate(
        self,
        text: str,
    ) -> bool:
        """
        Detect extremely poor extractions.

        This does NOT reject the document.
        It only emits diagnostics for downstream debugging.
        """

        if not text:
            return True

        if len(text) < self.MIN_MEANINGFUL_TEXT_LENGTH:
            return True

        lower = text.lower()

        if "username" in lower and "password" in lower:
            return True

        if any(keyword in lower for keyword in self.BLOCKED_PAGE_KEYWORDS):
            return True

        noise_hits = sum(
            keyword in lower for keyword in self.NOISE_KEYWORDS
        )

        if noise_hits >= self.NOISE_KEYWORD_THRESHOLD:
            return True

        meaningful_hits = sum(
            word in lower for word in self.TENDER_KEYWORDS
        )

        if meaningful_hits == 0:
            return True

        words = text.split()

        if len(words) < self.MIN_MEANINGFUL_WORD_COUNT:
            return True

        return False