import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def __init__(self, delay: float = 0.5, max_retries: int = 3, workers: int = 1):
        self.delay = delay
        self.max_retries = max_retries
        self.workers = workers
        self.job_parser = JobParser()
        self._local = threading.local()

    def _get_session(self) -> requests.Session:
        """Get thread-local session."""
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.session.headers.update(self.DEFAULT_HEADERS)
        return self._local.session

    def _get_sitemap_parser(self) -> SitemapParser:
        """Get thread-local sitemap parser."""
        if not hasattr(self._local, "sitemap_parser"):
            self._local.sitemap_parser = SitemapParser(self._get_session())
        return self._local.sitemap_parser

    def discover_all(self, urls: list[str]) -> dict[str, int]:
        """Discover job counts for all sites without scraping."""
        results = {}
        total = 0

        for url in urls:
            url = url.rstrip("/")
            job_urls = self._get_sitemap_parser().get_job_urls(url)
            count = len(job_urls)
            results[url] = count
            total += count
            print(f"  {url}: {count} jobs")

        print(f"\nTotal: {total} jobs across {len(urls)} site(s)")
        return results

    def scrape_all(self, urls: list[str], output_path: str | Path) -> int:
        """Scrape all sites and write jobs to output file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total_jobs = 0
        lock = threading.Lock()

        with open(output_path, "w", encoding="utf-8") as f:
            for url in urls:
                print(f"\nScraping: {url}")
                for job in self._scrape_site_parallel(url, f, lock):
                    total_jobs += 1

        print(f"\nTotal jobs scraped: {total_jobs}")
        return total_jobs

    def _scrape_site_parallel(self, base_url: str, file, lock: threading.Lock):
        """Scrape all jobs from a site using parallel workers."""
        base_url = base_url.rstrip("/")
        source_site = urlparse(base_url).netloc

        job_urls = self._get_sitemap_parser().get_job_urls(base_url)
        total = len(job_urls)
        print(f"  Found {total} jobs in sitemap")

        if self.workers == 1:
            for i, job_url in enumerate(job_urls, 1):
                job = self._fetch_job_details(job_url, source_site)
                if job:
                    print(f"  [{i}/{total}] {job.title[:50]}...")
                    with lock:
                        file.write(json.dumps(job.to_dict(), ensure_ascii=False) + "\n")
                        file.flush()
                    yield job
                time.sleep(self.delay)
        else:
            completed = 0
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {
                    executor.submit(self._fetch_job_details, url, source_site): url
                    for url in job_urls
                }

                for future in as_completed(futures):
                    completed += 1
                    job = future.result()
                    if job:
                        print(f"  [{completed}/{total}] {job.title[:50]}...")
                        with lock:
                            file.write(
                                json.dumps(job.to_dict(), ensure_ascii=False) + "\n"
                            )
                            file.flush()
                        yield job

    def _fetch_job_details(self, url: str, source_site: str) -> Job | None:
        """Fetch and parse a job detail page."""
        session = self._get_session()

        for attempt in range(self.max_retries):
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                return self.job_parser.parse(response.text, url, None, source_site)
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    print(f"  Failed to fetch {url}: {e}")
                    return None
        return None
