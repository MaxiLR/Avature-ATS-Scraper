# Avature ATS Scraper

Scraper for extracting job postings from Avature-hosted career sites.

## Setup

1. Install Poetry if needed.
2. Install dependencies:

```bash
poetry install
```

## Usage

### 1. Add sites to scrape

Edit `input/sites.txt` with Avature career site URLs:

```
https://bloomberg.avature.net/careers
https://uclahealth.avature.net/careers
# Add more sites here
```

### 2. Run the scraper

```bash
poetry run python -m avature_scraper
```

### Options

```bash
# Custom input/output files
poetry run python -m avature_scraper -i my_sites.txt -o my_output.jsonl

# Adjust delay between requests (default: 0.5s)
poetry run python -m avature_scraper --delay 1.0

# Parallel workers for faster scraping (default: 1)
poetry run python -m avature_scraper --workers 8

# Discover job counts without scraping
poetry run python -m avature_scraper --discover-only
```

## Output Format

Jobs are saved as JSON Lines (`.jsonl`), one job per line:

```json
{
  "title": "Software Engineer",
  "description": "<div>Job description HTML...</div>",
  "apply_url": "https://bloomberg.avature.net/careers/JobDetail/Software-Engineer/1234",
  "location": "New York",
  "posted_at": "Thu, 01 Aug 2024 00:00:00 +0000",
  "metadata": {
    "business_area": "Engineering",
    "ref_id": "10035763"
  },
  "source_site": "bloomberg.avature.net"
}
```

## How It Works

1. Reads Avature site URLs from input file
2. Fetches `/sitemap.xml` from each site (single request to get all job URLs)
3. Fetches each job detail page for full description and metadata
4. Writes jobs to JSONL output file
