import requests
from bs4 import BeautifulSoup


class SitemapParser:
    def __init__(self, session: requests.Session):
        self.session = session

    def get_job_urls(self, base_url: str) -> list[str]:
        """Fetch all job URLs from sitemap.xml in a single request."""
        final_url = self._follow_redirects(base_url)
        if not final_url:
            return []

        sitemap_url = f"{final_url}/sitemap.xml"

        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Sitemap fetch error: {e}")
            return []

        return self._parse_sitemap(response.text)

    def _follow_redirects(self, url: str) -> str | None:
        """Follow redirects and return the final URL without trailing slash."""
        try:
            response = self.session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            final_url = response.url.rstrip("/")
            return final_url
        except requests.RequestException as e:
            print(f"  URL validation error for {url}: {e}")
            return None

    def _parse_sitemap(self, html: str) -> list[str]:
        """Parse sitemap and extract JobDetail URLs."""
        soup = BeautifulSoup(html, "lxml-xml")

        urls = []
        for link in soup.find_all("link", attrs={"hreflang": "x-default"}):
            href = link.get("href")
            if href and "/JobDetail/" in href:
                path_parts = href.split("/JobDetail/")
                if len(path_parts) > 1 and path_parts[1]:
                    urls.append(href)

        return urls
