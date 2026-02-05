from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from ..models import Job


class BaseJobParser(ABC):
    """Base class for job parsers with common extraction utilities."""

    FIELD_MAPPINGS: dict[str, str] = {}

    def parse(
        self, html: str, url: str, posted_at: str | None, source_site: str
    ) -> Job | None:
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)
        description = self._extract_description(soup)

        if self._is_error_page(title, description):
            return None

        metadata = self._extract_metadata(soup)
        location = self._extract_location(soup, metadata)

        if "location" in metadata:
            del metadata["location"]

        return Job(
            title=title,
            description=description,
            apply_url=url,
            location=location,
            posted_at=posted_at or metadata.pop("posted_at", None),
            metadata=metadata,
            source_site=source_site,
        )

    def _is_error_page(self, title: str, description: str) -> bool:
        return "error" in title.lower() and not description.strip()

    @abstractmethod
    def _extract_title(self, soup: BeautifulSoup) -> str:
        pass

    @abstractmethod
    def _extract_description(self, soup: BeautifulSoup) -> str:
        pass

    @abstractmethod
    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        pass

    @abstractmethod
    def _extract_location(self, soup: BeautifulSoup, metadata: dict) -> str | None:
        pass

    def _extract_title_from_tag(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if " - " in title_text:
                return title_text.split(" - ")[0].strip()
            if " | " in title_text:
                return title_text.split(" | ")[0].strip()
            return title_text
        return ""

    def _normalize_label(self, label: str) -> str:
        return label.lower().rstrip(":").strip()
