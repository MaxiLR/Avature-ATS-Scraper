import argparse
from pathlib import Path

from .scraper import AvatureScraper


def load_urls(input_path: Path) -> list[str]:
    """Load URLs from input file, ignoring comments and empty lines."""
    urls = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(
        description="Scrape job postings from Avature-hosted career sites"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("input/sites.txt"),
        help="Input file with Avature site URLs (default: input/sites.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/jobs.jsonl"),
        help="Output file for scraped jobs (default: output/jobs.jsonl)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between requests in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for fetching jobs (default: 1)",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only discover and count job URLs without scraping",
    )
    parser.add_argument(
        "--discover-sources",
        action="store_true",
        help="Discover new Avature career sites using automated Google search",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of Google search pages to scan (default: 3)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of sources to discover (default: 50)",
    )
    args = parser.parse_args()

    # Automated source discovery mode
    if args.discover_sources:
        from .discovery import run_discovery

        print("Starting automated source discovery...")
        print(f"Scanning up to {args.max_pages} Google search pages")
        print(f"Target: {args.max_results} sources\n")

        discovered = run_discovery(
            max_pages=args.max_pages, max_results=args.max_results
        )

        if discovered:
            print(f"\n✓ Discovered {len(discovered)} valid Avature career sites:")
            for url in discovered:
                print(f"  {url}")

            # Optionally append to sites.txt
            response = input("\nAppend these URLs to input/sites.txt? (y/n): ")
            if response.lower() == "y":
                args.input.parent.mkdir(parents=True, exist_ok=True)
                with open(args.input, "a", encoding="utf-8") as f:
                    f.write("\n# Auto-discovered sources\n")
                    for url in discovered:
                        f.write(f"{url}\n")
                print(f"✓ Appended {len(discovered)} URLs to {args.input}")
        else:
            print("\n✗ No new sources discovered")

        return 0

    # Normal scraping modes
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        print("Create the file with Avature site URLs, one per line.")
        return 1

    urls = load_urls(args.input)
    if not urls:
        print("Error: No URLs found in input file")
        return 1

    print(f"Loaded {len(urls)} site(s)")
    scraper = AvatureScraper(delay=args.delay, workers=args.workers)

    if args.discover_only:
        print("\nDiscovering job URLs...")
        scraper.discover_all(urls)
    else:
        scraper.scrape_all(urls, args.output)
        print(f"Done! Output written to: {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
