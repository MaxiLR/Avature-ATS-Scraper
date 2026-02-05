from bs4 import BeautifulSoup

from .base import BaseJobParser


class StandardAvatureParser(BaseJobParser):
    """Parser for standard Avature portal structure (most sites)."""

    DESCRIPTION_LABELS = {
        "about the role",
        "what is in it for you",
        "you will be responsible for",
        "you will need",
        "about us",
        "responsibilities",
        "qualifications",
        "requirements",
        "description",
        "job description",
        "what you'll do",
        "what we offer",
        "who you are",
        "your role",
        "the role",
        "the opportunity",
        "overview",
        "summary",
    }

    FIELD_MAPPINGS = {
        # Location variants
        "location": "location",
        "location:": "location",
        "locations": "location",
        "workplace location": "location",
        "city": "city",
        "state": "state",
        "country": "country",
        "region": "region",
        # Business area variants
        "business area": "business_area",
        "business function": "business_area",
        "business unit": "business_area",
        "job family": "business_area",
        "job family:": "business_area",
        "department": "department",
        "career field": "career_field",
        "entity": "entity",
        # Reference ID variants
        "ref #": "ref_id",
        "ref#": "ref_id",
        "job #": "ref_id",
        "job id": "ref_id",
        "job id:": "ref_id",
        "requisition #": "ref_id",
        # Experience/seniority variants
        "experience level": "experience_level",
        "experience": "experience_level",
        "seniority": "experience_level",
        "career level": "experience_level",
        "career level:": "experience_level",
        "position level": "position_level",
        # Contract/employment type variants
        "type of contract": "contract_type",
        "worker type reference": "contract_type",
        "worker type reference:": "contract_type",
        "employment type": "employment_type",
        "post type": "post_type",
        # Work pattern variants
        "working pattern": "work_pattern",
        "onsite or remote": "work_pattern",
        "remote type": "remote_type",
        # Compensation variants
        "salary": "salary",
        "pay rate type": "pay_type",
        "pay rate type:": "pay_type",
        # Date variants
        "date": "posted_at",
        "posted date": "posted_at",
        "posting date": "posted_at",
        "date published": "posted_at",
        "closing date": "closing_date",
        # Other fields
        "domain": "domain",
        "duration": "duration",
        "civil service grade": "grade",
        "additional location": "additional_location",
        "additional location:": "additional_location",
        "number of jobs available": "positions",
        "security clearance required": "clearance",
        "name": "job_name",
        "posting title": "posting_title",
    }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_field = soup.select_one(
            ".article__content__view__field__value--font .article__content__view__field__value"
        )
        if title_field:
            return title_field.get_text(strip=True)

        for field in soup.select(".article__content__view__field"):
            label_el = field.select_one(".article__content__view__field__label")
            if label_el:
                label = self._normalize_label(label_el.get_text(strip=True))
                if label in ("job name", "job title"):
                    value_el = field.select_one(".article__content__view__field__value")
                    if value_el:
                        return value_el.get_text(strip=True)

        return self._extract_title_from_tag(soup)

    def _extract_description(self, soup: BeautifulSoup) -> str:
        description_parts = []

        for field in soup.select(".article__content__view__field"):
            label_el = field.select_one(".article__content__view__field__label")
            value_el = field.select_one(".article__content__view__field__value")

            if not value_el:
                continue

            if label_el:
                label = self._normalize_label(label_el.get_text(strip=True))
                if label in self.FIELD_MAPPINGS:
                    continue
                if label in self.DESCRIPTION_LABELS:
                    description_parts.append(
                        f"<h4>{label_el.get_text(strip=True)}</h4>\n{value_el}"
                    )
                    continue

            classes = field.get("class", [])
            if "field--rich-text" in classes or "tf_replaceFieldVideoTokens" in classes:
                description_parts.append(str(value_el))
            elif not label_el:
                text = value_el.get_text(strip=True)
                if text and len(text) > 50:
                    description_parts.append(str(value_el))

        return "\n".join(description_parts)

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}

        for field in soup.select(".article__content__view__field"):
            label_el = field.select_one(".article__content__view__field__label")
            if not label_el:
                continue

            label = self._normalize_label(label_el.get_text(strip=True))
            if label not in self.FIELD_MAPPINGS:
                continue

            value_el = field.select_one(".article__content__view__field__value")
            if value_el:
                key = self.FIELD_MAPPINGS[label]
                metadata[key] = value_el.get_text(strip=True)

        return metadata

    def _extract_location(self, soup: BeautifulSoup, metadata: dict) -> str | None:
        if "location" in metadata:
            return metadata["location"]

        for strong in soup.find_all("strong"):
            text = strong.get_text(strip=True)
            if text.startswith("Work Location:"):
                return text.replace("Work Location:", "").strip()

        parts = []
        for field in ["city", "state", "country", "region"]:
            if field in metadata:
                parts.append(metadata.pop(field))
        if parts:
            return ", ".join(parts)

        return None
