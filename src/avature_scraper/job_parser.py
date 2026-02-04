from bs4 import BeautifulSoup

from .models import Job


class JobParser:
    METADATA_FIELDS = {
        "location": "location",
        "business area": "business_area",
        "ref #": "ref_id",
        "experience level": "experience_level",
    }

    def parse(
        self, html: str, url: str, posted_at: str | None, source_site: str
    ) -> Job | None:
        """Parse job detail page HTML and extract job information. Returns None for error pages."""
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup)
        metadata = self._extract_metadata(soup)
        location = metadata.pop("location", None)
        description = self._extract_description(soup)

        if "error" in title.lower() and not description.strip():
            return None

        if not location:
            location = self._extract_location_fallback(soup)

        return Job(
            title=title,
            description=description,
            apply_url=url,
            location=location,
            posted_at=posted_at,
            metadata=metadata,
            source_site=source_site,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from page."""
        title_field = soup.select_one(
            ".article__content__view__field__value--font .article__content__view__field__value"
        )
        if title_field:
            return title_field.get_text(strip=True)

        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if " - " in title_text:
                return title_text.split(" - ")[0].strip()
            return title_text

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description from page (fields without labels or with content labels)."""
        description_parts = []

        for field in soup.select(".article__content__view__field"):
            label_el = field.select_one(".article__content__view__field__label")
            value_el = field.select_one(".article__content__view__field__value")

            if not value_el:
                continue

            if label_el:
                label = label_el.get_text(strip=True).lower()
                if label in self.METADATA_FIELDS:
                    continue

            if "field--rich-text" in field.get("class", []):
                description_parts.append(str(value_el))
            elif not label_el:
                text = value_el.get_text(strip=True)
                if text and len(text) > 50:
                    description_parts.append(str(value_el))

        return "\n".join(description_parts)

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract metadata fields (location, business area, etc.)."""
        metadata = {}

        for field in soup.select(".article__content__view__field"):
            label_el = field.select_one(".article__content__view__field__label")
            if not label_el:
                continue

            label = label_el.get_text(strip=True).lower()
            if label not in self.METADATA_FIELDS:
                continue

            value_el = field.select_one(".article__content__view__field__value")
            if value_el:
                key = self.METADATA_FIELDS[label]
                metadata[key] = value_el.get_text(strip=True)

        return metadata

    def _extract_location_fallback(self, soup: BeautifulSoup) -> str | None:
        """Extract location from UCLA Health-style 'Work Location:' format."""
        for strong in soup.find_all("strong"):
            text = strong.get_text(strip=True)
            if text.startswith("Work Location:"):
                location = text.replace("Work Location:", "").strip()
                return location

        return None
