from bs4 import BeautifulSoup

from .base import BaseJobParser


class BaufestParser(BaseJobParser):
    """Parser for Baufest-style portal structure (custom template)."""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        return self._extract_title_from_tag(soup)

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc_el = soup.select_one(".jobDescription")
        if desc_el:
            return str(desc_el)
        return ""

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}

        for label_el in soup.select(".jobInfoLabel"):
            text = label_el.get_text(strip=True)
            if text.startswith("Ref#:"):
                metadata["ref_id"] = text.replace("Ref#:", "").strip()
            elif text.startswith("Ref #:"):
                metadata["ref_id"] = text.replace("Ref #:", "").strip()

        return metadata

    def _extract_location(self, soup: BeautifulSoup, metadata: dict) -> str | None:
        loc_el = soup.select_one(".jobInfoLocation")
        if loc_el:
            return loc_el.get_text(strip=True)
        return None
