from bs4 import BeautifulSoup

from .base import BaseJobParser


class NVAParser(BaseJobParser):
    """Parser for NVA Jobs portal (custom detail template)."""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]
        return self._extract_title_from_tag(soup)

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc = soup.select_one(".detailDescription")
        if desc:
            return str(desc)

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"]

        return ""

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        return {}

    def _extract_location(self, soup: BeautifulSoup, metadata: dict) -> str | None:
        for fieldset in soup.select(".detailData .fieldSet"):
            label = fieldset.select_one(".fieldSetLabel")
            value = fieldset.select_one(".fieldSetValue")
            if label and value:
                if "location" in label.get_text(strip=True).lower():
                    return value.get_text(strip=True)
        return None
