import requests
from bs4 import BeautifulSoup


class SitemapParser:
    def __init__(self, session: requests.Session):
        self.session = session

    def get_job_urls(self, base_url: str) -> list[str]:
        """Fetch all job URLs from sitemap.xml in a single request."""
        sitemap_url = f"{base_url}/sitemap.xml"

        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Sitemap fetch error: {e}")
            return []

        return self._parse_sitemap(response.text)

    def _parse_sitemap(self, html: str) -> list[str]:
        """Parse sitemap and extract JobDetail URLs."""
        soup = BeautifulSoup(html, "lxml")

        urls = []
        for link in soup.select("[hreflang][href*='/JobDetail/']"):
            href = link.get("href")
            if href and "/JobDetail/" in href:
                path_parts = href.split("/JobDetail/")
                if len(path_parts) > 1 and path_parts[1]:
                    urls.append(href)

        return urls
