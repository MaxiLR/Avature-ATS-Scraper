# Avature ATS Scraper

Scraper for extracting job postings from Avature-hosted career sites.

**Time Investment**: ~12 hours

| Input                          | Output              | Performance                                |
| ------------------------------ | ------------------- | ------------------------------------------ |
| `input/sites.txt` (20 domains) | `output/jobs.jsonl` | **10,623 jobs** in 1h 15m (`--workers 15`) |

## Project Structure

```
src/avature_scraper/
├── __init__.py
├── __main__.py           # Entry point
├── main.py               # CLI argument parsing
├── scraper.py            # Main scraper orchestration
├── http.py               # HTTP client with rate limiting
├── sitemap_parser.py     # Sitemap XML parsing
├── models.py             # Job data model
├── discovery.py          # Automated source discovery
└── parsers/              # Domain-specific parsing layer
    ├── __init__.py
    ├── base.py           # Abstract base parser
    ├── standard.py       # Standard Avature parser (14 sites)
    ├── baufest.py        # Baufest custom template parser
    ├── gps.py            # GPS Hospitality parser
    ├── nva.py            # NVA Jobs parser
    └── registry.py       # Parser selection by domain
```

## Prerequisites

- **Python 3.11+**
- **Poetry** for dependency management
- **Playwright** (optional, for automated source discovery)

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install Playwright browsers (only needed for --discover-sources)
poetry run playwright install chromium
```

## Usage

### 1. Discover Avature career sites (optional)

Automatically discover Avature career sites via Google search:

```bash
poetry run python -m avature_scraper --discover-sources
```

This uses Playwright to search Google for `site:*.avature.net inurl:SearchJobs`, extracts portal URLs, validates them against their sitemaps, and optionally appends them to your `input/sites.txt`.

> **Note**: All 20 domains in `input/sites.txt` were discovered using this tool. The discovery feature is experimental and may fail on some runs due to CAPTCHAs or unhandled pop-ups. Re-running usually resolves the issue.

Options:

- `--max-pages N` - Number of Google search pages to scan (default: 3)
- `--max-results N` - Maximum sources to discover (default: 50)

### 2. Add sites to scrape

Edit `input/sites.txt` with Avature career site URLs:

```
https://bloomberg.avature.net/careers
https://uclahealth.avature.net/careers
# Add more sites here
```

### 3. Run the scraper

```bash
poetry run python -m avature_scraper
```

### Options

```bash
# Custom input/output files
poetry run python -m avature_scraper -i my_sites.txt -o my_output.jsonl

# Adjust delay between requests (default: 1.5s)
poetry run python -m avature_scraper --delay 2.0

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

### Pre-scraped Data

The repository includes pre-scraped job data in `output/segments/` (split into <100MB files for GitHub):

```bash
# Merge segments into a single file
python scripts/split_output.py merge -i output/segments -o output/jobs.jsonl

# Split a large output file into segments
python scripts/split_output.py split -i output/jobs.jsonl -o output/segments
```

## Data Quality Summary

### Current Dataset Statistics

| Metric                 | Value        |
| ---------------------- | ------------ |
| Total jobs scraped     | 10,623       |
| Unique apply URLs      | 100%         |
| Avg description length | 14,058 chars |

### Field Completeness

| Field       | Coverage | Notes                                      |
| ----------- | -------- | ------------------------------------------ |
| title       | 98.5%    | Missing on some error/redirect pages       |
| description | 98.5%    | Rich content with section headers          |
| location    | 83.2%    | Constructed from city/state/country fields |
| posted_at   | 23.5%    | Extracted from date fields where available |
| metadata    | 58.4%    | Business area, ref ID, experience, etc.    |

## Handled Domains

The following 20 Avature career sites have been discovered and tested:

| Domain                     | Portal Path                   | Parser   | Status |
| -------------------------- | ----------------------------- | -------- | ------ |
| baufest.avature.net        | /jobs                         | Custom   | ✓      |
| bloomberg.avature.net      | /careers                      | Standard | ✓      |
| careers.avature.net        | /es_ES/main                   | Standard | ⚠️     |
| careers.mantech.com        | /en_US/careers                | Standard | ✓      |
| careers.qatarairways.com   | /global                       | Standard | ✓      |
| careers.tesco.com          | /en_GB/careersmarketplace     | Standard | ✓      |
| careers.tql.com            | /en_US/TQLexternalcareers     | Standard | ✓      |
| cdcn.avature.net           | /careers                      | Standard | ✓      |
| deloittecm.avature.net     | /en_US/careers                | Standard | ✓      |
| forvis.avature.net         | /experiencedcareers           | Standard | ✓      |
| gpshospitality.avature.net | /careers                      | Custom   | ✓      |
| infor.avature.net          | /en_US/consultingservicesjobs | Standard | ⚠️     |
| jobs.justice.gov.uk        | /careers                      | Standard | ✓      |
| jobs.totalenergies.com     | /en_US/careers                | Standard | ✓      |
| jobsearch.harman.com       | /en_US/careers                | Standard | ✓      |
| nva.avature.net            | /jobs                         | Custom   | ✓      |
| primero.avature.net        | /en_GB/careers                | Standard | ✓      |
| uclahealth.avature.net     | /careers                      | Standard | ✓      |
| unifi.avature.net          | /careers                      | Standard | ✓      |

**Legend**: ✓ = Fully working, ⚠️ = Known issues (site-specific, not parser issues)

## Rate Limiting

Based on empirical testing, Avature sites implement IP-based rate limiting.

### Findings

| Metric              | Value                               |
| ------------------- | ----------------------------------- |
| Rate limit trigger  | ~300+ rapid requests                |
| Safe sustained rate | ~0.6 req/s (36 req/min)             |
| Recovery time       | ~180 seconds (3 minutes)            |
| HTTP status code    | 406 Not Acceptable                  |
| Scope               | IP-based (not session/cookie based) |

### Test Results

1. **Single worker at natural latency (~0.6 req/s)**: 1500 requests with 0 rate limits
2. **Rapid parallel requests**: 406 triggered after ~300 requests
3. **Recovery**: Rate limit resets after ~3 minutes of inactivity
4. **Session/UA changes**: Do not bypass rate limit (IP-based)
5. **Browser-based approaches (Playwright)**: Do not bypass rate limits

### Rate Limit Handling

When a 406 response is received, the scraper automatically:

1. Logs the rate limit event
2. Waits for 180 seconds (cooldown period)
3. Retries the request
4. Repeats up to 3 times before aborting

### Throughput Estimates

| Delay          | Rate       | Jobs/hour |
| -------------- | ---------- | --------- |
| 1.5s (default) | ~0.5 req/s | ~1,800    |
| 1.0s           | ~0.7 req/s | ~2,500    |
| 0.5s           | ~1.0 req/s | ~3,600    |

Note: Actual throughput depends on network latency and server response times.

### Future: Proxy Pool Rotation

To bypass rate limits and significantly speed up scraping, a **proxy pool rotation** strategy is recommended:

- Rotate IPs across requests to avoid per-IP rate limits
- Enables parallel workers without triggering 406 errors
- Estimated throughput increase: 10-50x with a pool of 10-50 proxies

## How It Works

### Automated Discovery

The `--discover-sources` flag enables automated discovery of Avature career sites:

1. **Google Search via Playwright**: Searches `site:*.avature.net inurl:SearchJobs`
   - Uses Playwright MCP for browser automation
   - Handles CAPTCHA detection with manual solve fallback
   - Paginates through multiple result pages

2. **URL Pattern Extraction**:
   - Extracts portal base URLs from SearchJobs endpoints
   - Example: `https://baufest.avature.net/jobs/SearchJobs` → `https://baufest.avature.net/jobs`

3. **Validation**:
   - Follows redirects to resolve final URLs
   - Checks sitemap for `/JobDetail/` links to confirm active job listings
   - Reports job count per validated source

### Scraping Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Input     │───▶│  Sitemap    │───▶│   HTTP      │───▶│   Parser    │
│  sites.txt  │    │   Parser    │    │   Fetch     │    │  Registry   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │                   │                   │
                         ▼                   ▼                   ▼
                   Get job URLs        Fetch HTML         Select parser
                   from sitemap        for each job       by domain
                                                                │
                                                                ▼
                                                          ┌─────────────┐
                                                          │   Output    │
                                                          │  jobs.jsonl │
                                                          └─────────────┘
```

1. Reads Avature site URLs from input file
2. Fetches `/sitemap.xml` from each site (single request to get all job URLs)
3. Fetches each job detail page HTML
4. **Parser Registry** selects appropriate parser based on domain
5. Parser extracts title, description, location, and metadata
6. Writes jobs to JSONL output file

## Parsing Architecture

The scraper uses a **layered parsing architecture** with a parser registry that selects domain-specific parsers based on the site's HTML structure.

### Parser Types

| Parser                  | Domains                                    | Structure                                                            |
| ----------------------- | ------------------------------------------ | -------------------------------------------------------------------- |
| `StandardAvatureParser` | 14 sites (Bloomberg, Tesco, ManTech, etc.) | Uses `.article__content__view__field` classes with label/value pairs |
| `BaufestParser`         | baufest.avature.net                        | Custom template with `.jobDescription`, `.jobInfoLocation` classes   |
| `GPSHospitalityParser`  | gpshospitality.avature.net                 | Custom TPT template with `og:title` and `.article__content`          |
| `NVAParser`             | nva.avature.net                            | Custom template with `.detailDescription`, `.detailData` classes     |

### Field Extraction Analysis

Based on analyzing 17 domains, field labels vary significantly across sites:

| Field Type    | Label Variations                                                                              |
| ------------- | --------------------------------------------------------------------------------------------- |
| Location      | `Location`, `Location:`, `Workplace location`, `Work Location:`, `City` + `State` + `Country` |
| Job Reference | `Ref #`, `Ref#`, `Job #`, `Job ID`, `Job ID:`, `Requisition #`                                |
| Business Area | `Business Area`, `Business Function`, `Job Family`, `Department`, `Entity`, `Career Field`    |
| Experience    | `Experience Level`, `Experience`, `Seniority`, `Career Level`, `Position Level`               |
| Contract Type | `Type of contract`, `Worker Type Reference`, `Employment Type`, `Post Type`                   |
| Posted Date   | `Date`, `Posted Date`, `Posting Date`, `Date Published`                                       |
| Other         | `Security Clearance Required`, `Remote Type`, `Closing Date`, `Duration`                      |

### Adding New Domain Parsers

To add a custom parser for a domain with unique HTML structure:

```python
# src/avature_scraper/parsers/my_custom.py
from .base import BaseJobParser

class MyCustomParser(BaseJobParser):
    def _extract_title(self, soup):
        # Custom title extraction logic
        pass

    def _extract_description(self, soup):
        pass

    def _extract_metadata(self, soup):
        return {}

    def _extract_location(self, soup, metadata):
        return None

# Register in src/avature_scraper/parsers/registry.py
DOMAIN_PARSERS = {
    "baufest.avature.net": BaufestParser,
    "gpshospitality.avature.net": GPSHospitalityParser,
    "nva.avature.net": NVAParser,
    "my-custom-site.com": MyCustomParser,  # Add here
}
```

### Posted Date Solution

While not all individual job pages include posting dates, Avature provides an **RSS feed API endpoint** that includes `pubDate` for each job:

Example: `https://uclahealth.avature.net/careers/SearchJobs/feed/?jobRecordsPerPage=100`

## Future Enhancements

### Two-Stage Pipeline for Scale

For larger-scale deployments, a two-stage architecture would improve reliability:

**Stage 1: Download & Store Raw Data**

- Fetch and store raw HTML pages with minimal processing
- Upload to cloud storage (S3, GCS) with structured paths: `/{domain}/{job_id}/raw.html`
- Benefits: Decouples fetching from parsing, enables re-processing without re-fetching

**Stage 2: Parse & Transform**

- Process raw HTML through a global parser for common Avature patterns
- On parse failure, route to domain-specific parsers
- Failed parses logged for incremental parser improvements

### Other Enhancements

- Parse RSS feed to enrich job data with posting dates
- Add structured data extraction from JSON-LD when available
- Implement incremental scraping (only fetch new/updated jobs)
- Implement proxy pool rotation for rate limit bypass
