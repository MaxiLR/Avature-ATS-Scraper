from bs4 import BeautifulSoup

from .base import BaseJobParser


class GPSHospitalityParser(BaseJobParser):
    """Parser for GPS Hospitality portal (custom TPT template)."""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]
        return self._extract_title_from_tag(soup)

    def _extract_description(self, soup: BeautifulSoup) -> str:
        content = soup.select_one(".article__content")
        if content:
            return str(content)
        return ""

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        content = soup.select_one(".article__content")
        if content:
            text = content.get_text(strip=True)
            pairs = [
                ("Restaurant Number:", "restaurant_number"),
                ("City:", "city"),
                ("State:", "state"),
                ("Post Reference:", "ref_id"),
            ]
            for prefix, key in pairs:
                if prefix in text:
                    idx = text.find(prefix)
                    end_idx = len(text)
                    for other_prefix, _ in pairs:
                        if other_prefix != prefix and other_prefix in text:
                            other_idx = text.find(other_prefix)
                            if other_idx > idx and other_idx < end_idx:
                                end_idx = other_idx
                    value = text[idx + len(prefix) : end_idx].strip()
                    if value:
                        metadata[key] = value.split("#")[0].strip()
        return metadata

    def _extract_location(self, soup: BeautifulSoup, metadata: dict) -> str | None:
        parts = []
        if "city" in metadata:
            parts.append(metadata.pop("city"))
        if "state" in metadata:
            parts.append(metadata.pop("state"))
        return ", ".join(parts) if parts else None
