import hashlib
import time
from typing import Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logger import logger


class DocumentFetcher:
    """
    Production-grade document downloader.

    Responsibilities
    ----------------
    - HTTP fetching
    - Redirect handling
    - Retry logic
    - Streaming downloads
    - Size enforcement
    - MIME detection
    - Magic-byte detection
    - Login/Captcha detection
    - Content hashing
    - Structured responses

    NOT responsible for
    -------------------
    - HTML parsing
    - PDF parsing
    - Tender extraction
    """

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "application/pdf,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    RETRY_STATUS_CODES = (
        408,
        429,
        500,
        502,
        503,
        504,
    )

    DEFAULT_TIMEOUT = (
        5,
        20,
    )

    DEFAULT_RETRY_ATTEMPTS = 2

    RETRY_BACKOFF_FACTOR = 0.5

    MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024

    MAX_REDIRECTS = 10

    CHUNK_SIZE = 8192

    SUPPORTED_CONTENT_TYPES = (
        "text/html",
        "application/pdf",
        "application/xhtml+xml",
        "application/xml",
        "text/xml",
        "application/octet-stream",
    )

    UNSUPPORTED_CONTENT_TYPES = (
        "image/",
        "video/",
        "audio/",
        "application/zip",
        "application/x-rar",
        "application/x-7z",
        "application/x-msdownload",
        "application/x-executable",
        "application/vnd.android.package-archive",
    )

    LOGIN_SIGNATURES = (
        "login",
        "sign in",
        "session expired",
        "access denied",
        "unauthorized",
        "user authentication",
        "password",
    )

    CAPTCHA_SIGNATURES = (
        "captcha",
        "verify you are human",
        "verify you're human",
        "cloudflare",
        "incapsula",
        "bot detection",
        "security check",
        "human verification",
    )

    PDF_MAGIC = b"%PDF"

    HTML_MAGIC = (
        b"<!doctype html",
        b"<html",
    )

    def __init__(
        self,
        timeout=DEFAULT_TIMEOUT,
        retry_attempts=DEFAULT_RETRY_ATTEMPTS,
        max_download_size=MAX_DOWNLOAD_SIZE,
        max_redirects=MAX_REDIRECTS,
    ):
        self.timeout = timeout
        self.retry_attempts = max(
            0,
            int(retry_attempts),
        )

        self.max_download_size = int(
            max_download_size
        )

        self.max_redirects = int(
            max_redirects
        )

        self.session = requests.Session()

        self.session.headers.update(
            self.DEFAULT_HEADERS
        )

        self.session.max_redirects = (
            self.max_redirects
        )

        self._configure_retry_adapter()

    # --------------------------------------------------------
    # Session Configuration
    # --------------------------------------------------------

    def _configure_retry_adapter(self):

        retry = Retry(
            total=self.retry_attempts,
            connect=self.retry_attempts,
            read=self.retry_attempts,
            status=self.retry_attempts,
            backoff_factor=self.RETRY_BACKOFF_FACTOR,
            status_forcelist=self.RETRY_STATUS_CODES,
            allowed_methods=frozenset(
                {
                    "GET",
                    "HEAD",
                }
            ),
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=50,
            pool_maxsize=50,
        )

        self.session.mount(
            "http://",
            adapter,
        )

        self.session.mount(
            "https://",
            adapter,
        )

    # --------------------------------------------------------
    # Utility Helpers
    # --------------------------------------------------------

    @staticmethod
    def _calculate_sha256(
        content: bytes,
    ) -> str:
        return hashlib.sha256(
            content
        ).hexdigest()

    @staticmethod
    def _normalize_content_type(
        content_type: str,
    ) -> str:

        if not content_type:
            return ""

        return (
            content_type
            .split(";", 1)[0]
            .strip()
            .lower()
        )

    @staticmethod
    def _looks_like_pdf(
        content: bytes,
    ) -> bool:

        if not content:
            return False

        return content.startswith(
            DocumentFetcher.PDF_MAGIC
        )

    @staticmethod
    def _looks_like_html(
        content: bytes,
    ) -> bool:

        if not content:
            return False

        sample = (
            content[:4096]
            .lstrip()
            .lower()
        )

        return any(
            sample.startswith(sig)
            for sig in DocumentFetcher.HTML_MAGIC
        )

    @staticmethod
    def _decode_preview(
        content: bytes,
    ) -> str:

        try:
            return content[:10000].decode(
                "utf-8",
                errors="ignore",
            ).lower()

        except Exception:
            return ""

    def _contains_login_page(
        self,
        preview: str,
    ) -> bool:

        return any(
            keyword in preview
            for keyword in self.LOGIN_SIGNATURES
        )

    def _contains_captcha(
        self,
        preview: str,
    ) -> bool:

        return any(
            keyword in preview
            for keyword in self.CAPTCHA_SIGNATURES
        )
        # --------------------------------------------------------
    # Document Fetch
    # --------------------------------------------------------

    def fetch(
        self,
        url: str,
    ) -> Dict:
        """
        Download a document and return a standardized response.

        Downstream components should never have to catch
        requests exceptions.
        """

        if not url:

            return {
                "success": False,
                "content": None,
                "content_type": "",
                "mime_type": "",
                "content_hash": None,
                "content_size": 0,
                "url": url,
                "final_url": None,
                "status_code": None,
                "headers": {},
                "redirects": 0,
                "download_time": 0.0,
                "error": "URL is empty",
                "error_type": "invalid_url",
            }

        url = str(url).strip()

        if not url:

            return {
                "success": False,
                "content": None,
                "content_type": "",
                "mime_type": "",
                "content_hash": None,
                "content_size": 0,
                "url": url,
                "final_url": None,
                "status_code": None,
                "headers": {},
                "redirects": 0,
                "download_time": 0.0,
                "error": "URL is blank",
                "error_type": "invalid_url",
            }

        logger.debug(
            "Document fetch started | url=%s",
            url,
        )

        start_time = time.perf_counter()

        response = None

        try:

            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                stream=True,
            )

            response.raise_for_status()

            redirect_count = len(
                response.history
            )

            content_type = self._normalize_content_type(
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            validation_error = self._validate_response(
                response=response,
                content_type=content_type,
            )

            if validation_error is not None:

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                logger.warning(
                    "Document rejected | "
                    "status=%s | "
                    "reason=%s | "
                    "url=%s",
                    response.status_code,
                    validation_error,
                    url,
                )

                return {
                    "success": False,
                    "content": None,
                    "content_type": content_type,
                    "mime_type": content_type,
                    "content_hash": None,
                    "content_size": 0,
                    "url": url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "redirects": redirect_count,
                    "download_time": elapsed,
                    "error": validation_error,
                    "error_type": validation_error,
                }

            content, read_error = self._read_streamed_content(
                response
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            if read_error is not None:

                logger.warning(
                    "Document rejected | "
                    "reason=%s | "
                    "url=%s",
                    read_error,
                    url,
                )

                return {
                    "success": False,
                    "content": None,
                    "content_type": content_type,
                    "mime_type": content_type,
                    "content_hash": None,
                    "content_size": 0,
                    "url": url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "redirects": redirect_count,
                    "download_time": elapsed,
                    "error": read_error,
                    "error_type": read_error,
                }

            detected_mime = self._detect_mime_type(
                content,
                content_type,
            )

            preview = self._decode_preview(
                content
            )

            if (
                detected_mime == "text/html"
                and self._contains_login_page(preview)
            ):

                logger.warning(
                    "Login page detected | url=%s",
                    response.url,
                )

                return {
                    "success": False,
                    "content": None,
                    "content_type": content_type,
                    "mime_type": detected_mime,
                    "content_hash": None,
                    "content_size": len(content),
                    "url": url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "redirects": redirect_count,
                    "download_time": elapsed,
                    "error": "Login required",
                    "error_type": "login_required",
                }

            if (
                detected_mime == "text/html"
                and self._contains_captcha(preview)
            ):

                logger.warning(
                    "Captcha page detected | url=%s",
                    response.url,
                )

                return {
                    "success": False,
                    "content": None,
                    "content_type": content_type,
                    "mime_type": detected_mime,
                    "content_hash": None,
                    "content_size": len(content),
                    "url": url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "redirects": redirect_count,
                    "download_time": elapsed,
                    "error": "Captcha detected",
                    "error_type": "captcha",
                }

            logger.info(
                "Document fetched | "
                "time=%.2fs | "
                "status=%s | "
                "redirects=%s | "
                "size=%s bytes | "
                "content_type=%s | "
                "url=%s",
                elapsed,
                response.status_code,
                redirect_count,
                len(content),
                detected_mime,
                response.url,
            )

            return self._build_success_response(
                url=url,
                response=response,
                content=content,
                mime_type=detected_mime,
                elapsed=elapsed,
                redirects=redirect_count,
            )

        except requests.RequestException as error:

            logger.warning(
                "Document fetch failed | "
                "url=%s | "
                "error=%s",
                url,
                error,
            )

            return self._build_failure_response(
                url=url,
                error=error,
                response=getattr(
                    error,
                    "response",
                    None,
                ),
            )

        except Exception:

            logger.exception(
                "Unexpected fetch failure | url=%s",
                url,
            )

            raise

        finally:

            if response is not None:
                response.close()
        # --------------------------------------------------------
    # Response Validation
    # --------------------------------------------------------

    def _validate_response(
        self,
        response,
        content_type: str,
    ) -> Optional[str]:
        """
        Validate response headers before downloading the body.
        """

        declared_length = response.headers.get(
            "Content-Length"
        )

        if declared_length:

            try:

                declared_length = int(
                    declared_length
                )

                if declared_length == 0:
                    return "empty_response"

                if (
                    declared_length
                    > self.max_download_size
                ):
                    return "content_too_large"

            except (
                ValueError,
                TypeError,
            ):
                pass

        if response.status_code == 204:
            return "empty_response"

        if content_type:

            for unsupported in self.UNSUPPORTED_CONTENT_TYPES:

                if content_type.startswith(
                    unsupported
                ):
                    return "unsupported_content_type"

        return None

    # --------------------------------------------------------
    # Stream Download
    # --------------------------------------------------------

    def _read_streamed_content(
        self,
        response,
    ) -> Tuple[
        Optional[bytes],
        Optional[str],
    ]:
        """
        Stream the response while enforcing
        maximum download size.
        """

        chunks = []

        total_size = 0

        for chunk in response.iter_content(
            chunk_size=self.CHUNK_SIZE
        ):

            if not chunk:
                continue

            total_size += len(chunk)

            if (
                total_size
                > self.max_download_size
            ):
                return (
                    None,
                    "content_too_large",
                )

            chunks.append(chunk)

        if not chunks:
            return (
                None,
                "empty_response",
            )

        content = b"".join(chunks)

        if not content:
            return (
                None,
                "empty_response",
            )

        content_type = self._normalize_content_type(
            response.headers.get(
                "Content-Type",
                "",
            )
        )

        # PDF expected but HTML received

        if (
            "pdf" in content_type
            and not self._looks_like_pdf(
                content
            )
        ):

            if self._looks_like_html(
                content
            ):
                return (
                    None,
                    "fake_pdf_html",
                )

            return (
                None,
                "invalid_pdf",
            )

        detected_type = self._detect_mime_type(
            content,
            content_type,
        )

        allowed_types = {
            "application/pdf",
            "text/html",
            "application/xhtml+xml",
            "application/xml",
            "text/xml",
            "application/octet-stream",
        }

        if (
            detected_type
            not in allowed_types
        ):
            return (
                None,
                "unsupported_binary",
            )

        return (
            content,
            None,
        )

    # --------------------------------------------------------
    # MIME Detection
    # --------------------------------------------------------

    def _detect_mime_type(
        self,
        content: bytes,
        declared_type: str,
    ) -> str:
        """
        Detect the actual MIME type from the
        downloaded content.
        """

        declared_type = (
            self._normalize_content_type(
                declared_type
            )
        )

        if self._looks_like_pdf(
            content
        ):
            return "application/pdf"

        if self._looks_like_html(
            content
        ):
            return "text/html"

        if declared_type in (
            "application/xml",
            "text/xml",
        ):
            return declared_type

        return (
            declared_type
            or "application/octet-stream"
        )

    # --------------------------------------------------------
    # Binary Detection
    # --------------------------------------------------------

    @staticmethod
    def _is_binary(
        content: bytes,
    ) -> bool:
        """
        Lightweight binary detection.
        """

        if not content:
            return False

        sample = content[:4096]

        if b"\x00" in sample:
            return True

        text_chars = bytearray(
            {
                7,
                8,
                9,
                10,
                12,
                13,
                27,
            }
        )

        non_text = sum(
            byte not in text_chars
            and (
                byte < 32
                or byte > 126
            )
            for byte in sample
        )

        return (
            non_text
            > len(sample) * 0.30
        )
        # --------------------------------------------------------
    # Success Response
    # --------------------------------------------------------

    def _build_success_response(
        self,
        *,
        url: str,
        response,
        content: bytes,
        mime_type: str,
        elapsed: float,
        redirects: int,
    ) -> Dict:
        """
        Build the standardized success response used by
        downstream pipeline components.
        """

        return {
            "success": True,
            "content": content,
            "content_type": self._normalize_content_type(
                response.headers.get(
                    "Content-Type",
                    "",
                )
            ),
            "mime_type": mime_type,
            "content_hash": self._calculate_sha256(
                content
            ),
            "content_size": len(content),
            "url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "redirects": redirects,
            "download_time": elapsed,
            "error": None,
            "error_type": None,
        }

    # --------------------------------------------------------
    # Error Classification
    # --------------------------------------------------------

    def _classify_error(
        self,
        error: Exception,
    ) -> str:
        """
        Convert requests exceptions into stable
        machine-readable error codes.
        """

        if isinstance(
            error,
            requests.exceptions.ConnectTimeout,
        ):
            return "connect_timeout"

        if isinstance(
            error,
            requests.exceptions.ReadTimeout,
        ):
            return "read_timeout"

        if isinstance(
            error,
            requests.exceptions.Timeout,
        ):
            return "timeout"

        if isinstance(
            error,
            requests.exceptions.TooManyRedirects,
        ):
            return "too_many_redirects"

        if isinstance(
            error,
            requests.exceptions.ConnectionError,
        ):
            return "connection_error"

        if isinstance(
            error,
            requests.exceptions.SSLError,
        ):
            return "ssl_error"

        if isinstance(
            error,
            requests.exceptions.HTTPError,
        ):

            response = getattr(
                error,
                "response",
                None,
            )

            if response is not None:
                return (
                    f"http_{response.status_code}"
                )

            return "http_error"

        return (
            type(error).__name__.lower()
        )

    # --------------------------------------------------------
    # Failure Response
    # --------------------------------------------------------

    def _build_failure_response(
        self,
        *,
        url: str,
        error: Exception,
        response=None,
    ) -> Dict:
        """
        Build a standardized failure response.
        """

        content_type = ""
        status_code = None
        headers = {}
        final_url = None

        if response is not None:

            content_type = (
                self._normalize_content_type(
                    response.headers.get(
                        "Content-Type",
                        "",
                    )
                )
            )

            status_code = response.status_code

            headers = dict(
                response.headers
            )

            final_url = response.url

        return {
            "success": False,
            "content": None,
            "content_type": content_type,
            "mime_type": content_type,
            "content_hash": None,
            "content_size": 0,
            "url": url,
            "final_url": final_url,
            "status_code": status_code,
            "headers": headers,
            "redirects": 0,
            "download_time": 0.0,
            "error": str(error),
            "error_type": self._classify_error(
                error
            ),
        }

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    def close(
        self,
    ) -> None:
        """
        Close the underlying requests session.
        """

        self.session.close()

    def __enter__(
        self,
    ):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        self.close()
        return False


# ------------------------------------------------------------------
# End of DocumentFetcher
# ------------------------------------------------------------------