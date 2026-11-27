"""Web scraping service for fetching and extracting text from URLs."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags to strip entirely before extracting text
STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"}

MAX_HTML_SIZE = 5 * 1024 * 1024  # 5 MB
SCRAPE_TIMEOUT = 30.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; AIQ-Bot/1.0; +https://example.com/bot)"
)


class WebScraperError(Exception):
    """Exception raised for web scraping errors."""
    pass


@dataclass
class ScrapeResult:
    """Result of a web page scrape."""
    url: str
    title: str
    text_content: str
    content_length: int
    fetch_time_ms: float


class WebScraperService:
    """Service for fetching web pages and extracting text content."""

    def __init__(self) -> None:
        logger.info("WebScraperService initialized")

    async def scrape(self, url: str, fallback_title: str = "") -> ScrapeResult:
        """Fetch a URL and extract clean text content.

        Args:
            url: The URL to scrape.
            fallback_title: Title to use if page has no <title> tag.

        Returns:
            ScrapeResult with extracted text and metadata.

        Raises:
            WebScraperError: If fetching or parsing fails.
        """
        start = time.time()

        try:
            async with httpx.AsyncClient(
                timeout=SCRAPE_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise WebScraperError(f"HTTP {e.response.status_code} for {url}") from e
        except httpx.TimeoutException:
            raise WebScraperError(f"Timeout fetching {url}")
        except httpx.RequestError as e:
            raise WebScraperError(f"Request error for {url}: {e}") from e

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise WebScraperError(
                f"Unsupported content type '{content_type}' — only HTML and plain text are supported"
            )

        raw_html = response.text
        if len(raw_html) > MAX_HTML_SIZE:
            raise WebScraperError(
                f"Page too large ({len(raw_html)} bytes, max {MAX_HTML_SIZE})"
            )

        # Parse and extract text
        soup = BeautifulSoup(raw_html, "lxml")

        # Extract title
        title = fallback_title
        if not title:
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                title = title_tag.string.strip()
            else:
                title = url

        # Remove unwanted tags
        for tag_name in STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Get text, collapse whitespace
        text = soup.get_text(separator="\n")
        # Clean up: collapse blank lines and strip
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        clean_text = "\n".join(lines)

        if not clean_text.strip():
            raise WebScraperError(
                "No text content could be extracted from the page"
            )

        fetch_time_ms = (time.time() - start) * 1000

        logger.info(
            f"Scraped {url}: {len(clean_text)} chars, "
            f"title='{title[:50]}', {fetch_time_ms:.0f}ms"
        )

        return ScrapeResult(
            url=url,
            title=title,
            text_content=clean_text,
            content_length=len(clean_text),
            fetch_time_ms=fetch_time_ms,
        )
