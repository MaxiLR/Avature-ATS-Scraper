import asyncio
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class AvatureDiscovery:
    def __init__(self):
        self.discovered_urls = set()

    async def discover_sources(
        self, max_pages: int = 3, max_results: int = 50
    ) -> list[str]:
        """Discover Avature career sites using Google search via Playwright MCP."""
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@playwright/mcp@latest",
            ],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("Discovering Avature sources via Google search...")
                await self._search_and_extract(session, max_pages, max_results)

                # Close browser - we're done with Playwright
                try:
                    await session.call_tool("browser_close", arguments={})
                except:
                    pass

        # Validate discovered URLs using HTTP requests (same as main scraper)
        validated = self._validate_urls()

        return sorted(validated)

    async def _search_and_extract(
        self, session: ClientSession, max_pages: int, max_results: int
    ) -> None:
        """Perform Google search and extract Avature URLs."""
        # Navigate to Google
        await session.call_tool(
            "browser_navigate",
            arguments={"url": "https://www.google.com"},
        )

        # Wait for page to load
        await asyncio.sleep(2)

        # Check for CAPTCHA and handle it
        await self._handle_captcha_if_present(session)

        # Get snapshot to find search box ref
        snapshot = await session.call_tool("browser_snapshot", arguments={})
        snapshot_text = str(snapshot.content[0].text if snapshot.content else "")

        # Find search textbox ref (combobox or textbox with "search" or "buscar")
        search_ref = None
        for line in snapshot_text.split("\n"):
            line_lower = line.lower()
            if ("combobox" in line_lower or "textbox" in line_lower) and (
                "search" in line_lower or "buscar" in line_lower
            ):
                match = re.search(r"\[ref=(\w+)\]", line)
                if match:
                    search_ref = match.group(1)
                    break

        if not search_ref:
            print("  Could not find search box, using keyboard fallback")
            search_query = "site:*.avature.net inurl:SearchJobs"
            for char in search_query:
                await session.call_tool(
                    "browser_press_key",
                    arguments={"key": char},
                )
                await asyncio.sleep(0.03)
            await session.call_tool(
                "browser_press_key",
                arguments={"key": "Enter"},
            )
        else:
            # Type search query and submit
            await session.call_tool(
                "browser_type",
                arguments={
                    "ref": search_ref,
                    "text": "site:*.avature.net inurl:SearchJobs",
                    "submit": True,
                },
            )

        # Wait for search results to load
        await asyncio.sleep(3)

        # Check for CAPTCHA and handle it
        await self._handle_captcha_if_present(session)

        # Extract URLs from multiple pages
        for page_num in range(1, max_pages + 1):
            print(f"  Scanning page {page_num}...")

            # Extract URLs from search results using CSS selector
            result = await session.call_tool(
                "browser_evaluate",
                arguments={
                    "function": """() => {
                        const links = document.querySelectorAll('a:has(h3)');
                        return Array.from(links).map(a => a.href).filter(url => url.includes('avature.net'));
                    }"""
                },
            )

            # Process extracted URLs
            if result.content:
                content_str = str(result.content[0].text if result.content else "")
                before_count = len(self.discovered_urls)
                self._extract_avature_urls(content_str)
                found = len(self.discovered_urls) - before_count
                if found > 0:
                    print(f"    Found {found} new URLs")

            # Stop if we have enough results
            if len(self.discovered_urls) >= max_results:
                break

            # Click next page link if not last
            if page_num < max_pages:
                try:
                    result = await session.call_tool(
                        "browser_run_code",
                        arguments={
                            "code": """async (page) => {
                                const next = await page.$('#pnnext');
                                if (next) {
                                    await next.click();
                                    return true;
                                }
                                return false;
                            }"""
                        },
                    )
                    clicked = (
                        "true" in str(result.content).lower()
                        if result.content
                        else False
                    )
                    if clicked:
                        print(f"    Navigating to page {page_num + 1}...")
                        await asyncio.sleep(3)
                        await self._handle_captcha_if_present(session)
                    else:
                        print("    No more pages available")
                        break
                except Exception as e:
                    print(f"    Could not navigate to page {page_num + 1}: {e}")
                    break

    async def _handle_captcha_if_present(self, session: ClientSession) -> None:
        """Detect CAPTCHA page and attempt to solve by pressing Tab + Space."""
        try:
            if not await self._is_captcha_present(session):
                return

            print("  ⚠ CAPTCHA detected, attempting to solve...")

            # Press Tab to focus checkbox, then Space to click
            await session.call_tool(
                "browser_press_key",
                arguments={"key": "Tab"},
            )
            await asyncio.sleep(0.5)

            await session.call_tool(
                "browser_press_key",
                arguments={"key": " "},
            )

            # Wait for CAPTCHA to process
            await asyncio.sleep(5)

            # Check if CAPTCHA is still present
            if await self._is_captcha_present(session):
                print("  ⚠ Auto-solve failed. Please solve the CAPTCHA manually...")
                await asyncio.sleep(30)

        except Exception as e:
            print(f"  ⚠ CAPTCHA check error: {e}")

    async def _is_captcha_present(self, session: ClientSession) -> bool:
        """Check if CAPTCHA is present on the page."""
        try:
            snapshot = await session.call_tool("browser_snapshot", arguments={})
            content = str(snapshot.content[0].text if snapshot.content else "").lower()

            captcha_indicators = [
                "captcha",
                "recaptcha",
                "i'm not a robot",
                "not a robot",
                "unusual traffic",
                "verify you're human",
                "are you a robot",
            ]

            return any(indicator in content for indicator in captcha_indicators)
        except Exception:
            return False

    def _extract_avature_urls(self, content: str) -> None:
        """Extract Avature career site URLs from page content."""
        # Pattern to match full Avature URLs
        pattern = r"https://([a-zA-Z0-9-]+)\.avature\.net(/[^\s\"'>\]]+)?"

        matches = re.findall(pattern, content)
        for subdomain, path in matches:
            path = path or ""

            # Skip static assets
            if any(x in path.lower() for x in [".js", ".css", ".png", ".jpg", ".gif"]):
                continue

            # Extract base career portal path by removing SearchJobs/JobDetail and query params
            # e.g., /es_ES/Careers/SearchJobs?foo=bar -> /es_ES/Careers
            # e.g., /careers/JobDetail/Some-Job/123 -> /careers
            path = path.split("?")[0]  # Remove query params
            path = path.rstrip("/")

            # Remove SearchJobs or JobDetail suffix to get base path
            path_lower = path.lower()
            if "/searchjobs" in path_lower:
                path = path[: path_lower.index("/searchjobs")]
            elif "/jobdetail" in path_lower:
                path = path[: path_lower.index("/jobdetail")]

            url = (
                f"https://{subdomain}.avature.net{path}"
                if path
                else f"https://{subdomain}.avature.net"
            )
            self.discovered_urls.add(url)

    def _validate_urls(self) -> list[str]:
        """Validate URLs by following redirects and checking for sitemaps with JobDetail URLs."""
        print(f"\nValidating {len(self.discovered_urls)} discovered URLs...")
        validated = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # Group URLs by domain
        domains: dict[str, list[str]] = {}
        for url in self.discovered_urls:
            domain = urlparse(url).netloc
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(url)

        # Validate each domain's endpoints
        for domain in sorted(domains.keys()):
            endpoints = domains[domain]
            print(f"\n  {domain}:")

            for url in sorted(endpoints):
                path = urlparse(url).path or "/"
                try:
                    # Follow redirects to get final URL
                    response = requests.get(url, headers=headers, timeout=30)

                    # Skip if not 200
                    if response.status_code != 200:
                        print(f"    ✗ {path} - HTTP {response.status_code}")
                        continue

                    final_url = response.url.rstrip("/")

                    # Check if sitemap contains JobDetail URLs
                    job_count = self._check_sitemap_for_jobs(final_url, headers)
                    if job_count > 0:
                        validated.append(final_url)
                        print(f"    ✓ {path} → {final_url} ({job_count} jobs)")
                        break  # Found working endpoint, move to next domain
                    else:
                        print(f"    ✗ {path} - No JobDetail URLs in sitemap")

                except Exception as e:
                    print(f"    ✗ {path} - {e}")
                    continue

        return validated

    def _check_sitemap_for_jobs(self, base_url: str, headers: dict) -> int:
        """Check if sitemap contains JobDetail URLs using the same parser as the scraper."""
        sitemap_url = f"{base_url}/sitemap.xml"

        try:
            response = requests.get(sitemap_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml-xml")

            job_urls = []
            for link in soup.find_all("link", attrs={"hreflang": "x-default"}):
                href = link.get("href")
                if href and "/JobDetail/" in href:
                    path_parts = href.split("/JobDetail/")
                    if len(path_parts) > 1 and path_parts[1]:
                        job_urls.append(href)

            return len(set(job_urls))

        except Exception:
            return 0


async def discover_avature_sources(
    max_pages: int = 3, max_results: int = 50
) -> list[str]:
    """Main entry point for discovering Avature sources."""
    discovery = AvatureDiscovery()
    return await discovery.discover_sources(max_pages, max_results)


def run_discovery(max_pages: int = 3, max_results: int = 50) -> list[str]:
    """Synchronous wrapper for discovery."""
    return asyncio.run(discover_avature_sources(max_pages, max_results))
