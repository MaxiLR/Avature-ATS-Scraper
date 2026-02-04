import json
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .job_parser import JobParser
from .models import Job
from .sitemap_parser import SitemapParser


class AvatureScraper:
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, delay: float = 0.5, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.sitemap_parser = SitemapParser(self.session)
        self.job_parser = JobParser()

    def scrape_all(self, urls: list[str], output_path: str | Path) -> int:
        """Scrape all sites and write jobs to output file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total_jobs = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for url in urls:
                print(f"\nScraping: {url}")
                for job in self.scrape_site(url):
                    f.write(json.dumps(job.to_dict(), ensure_ascii=False) + "\n")
                    f.flush()
                    total_jobs += 1

        print(f"\nTotal jobs scraped: {total_jobs}")
        return total_jobs

    def scrape_site(self, base_url: str):
        """Scrape all jobs from a single Avature site."""
        base_url = base_url.rstrip("/")
        source_site = urlparse(base_url).netloc

        job_urls = self.sitemap_parser.get_job_urls(base_url)
        print(f"  Found {len(job_urls)} jobs in sitemap")

        for i, job_url in enumerate(job_urls, 1):
            job = self._fetch_job_details(job_url, source_site)
            if job:
                print(f"  [{i}/{len(job_urls)}] {job.title[:50]}...")
                yield job
            time.sleep(self.delay)

    def _fetch_job_details(self, url: str, source_site: str) -> Job | None:
        """Fetch and parse a job detail page."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return self.job_parser.parse(response.text, url, None, source_site)
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    print(f"  Failed to fetch {url}: {e}")
                    return None
        return None
