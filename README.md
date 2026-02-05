# Avature ATS Scraper

Scraper for extracting job postings from Avature-hosted career sites.

**Time Investment**: ~12 hours

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

## Data Quality Summary

> **Note**: Due to time constraints, not all edge cases are handled. The focus was on identifying global, repeatable patterns across Avature ATS sources and designing a dynamic discovery mechanism for new sources.

### Current Dataset Statistics

| Metric                 | Value       |
| ---------------------- | ----------- |
| Total jobs scraped     | 1,857       |
| Unique apply URLs      | 100%        |
| Avg description length | 8,308 chars |

### Field Completeness

| Field       | Coverage | Notes                                        |
| ----------- | -------- | -------------------------------------------- |
| title       | 93.8%    | Missing on some error/redirect pages         |
| description | 68.1%    | Varies by site template                      |
| location    | 34.8%    | Different HTML structures per domain         |
| posted_at   | 0%       | Available via RSS feed (not yet implemented) |
| metadata    | 34.9%    | Only on sites with labeled fields            |

### Jobs by Source (Sample)

| Source                   | Jobs |
| ------------------------ | ---- |
| careers.mantech.com      | 615  |
| bloomberg.avature.net    | 444  |
| careers.tesco.com        | 428  |
| careers.qatarairways.com | 219  |
| careers.avature.net      | 101  |
| baufest.avature.net      | 50   |

### Known Limitations

- **Posted dates**: Not extracted from job pages (available via RSS feed endpoint)
- **Location extraction**: Varies significantly across domains due to different HTML templates
- **Metadata fields**: Only populated for sites using Avature's standard labeled field structure

## Handled Domains

The following 20 Avature career sites have been discovered and tested:

| Domain                     | Portal Path                   |
| -------------------------- | ----------------------------- |
| baufest.avature.net        | /jobs                         |
| bloomberg.avature.net      | /careers                      |
| careers.avature.net        | /es_ES/main                   |
| careers.mantech.com        | /en_US/careers                |
| careers.qatarairways.com   | /global                       |
| careers.tesco.com          | /en_GB/careersmarketplace     |
| careers.tql.com            | /en_US/TQLexternalcareers     |
| cdcn.avature.net           | /careers                      |
| deloittecm.avature.net     | /en_US/careers                |
| forvis.avature.net         | /experiencedcareers           |
| gpshospitality.avature.net | /careers                      |
| infor.avature.net          | /en_US/consultingservicesjobs |
| jobs.justice.gov.uk        | /careers                      |
| jobs.totalenergies.com     | /en_US/careers                |
| jobsearch.harman.com       | /en_US/careers                |
| mercadona.avature.net      | /es_ES/Careers                |
| nva.avature.net            | /jobs                         |
| primero.avature.net        | /en_GB/careers                |
| uclahealth.avature.net     | /careers                      |
| unifi.avature.net          | /careers                      |

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

### Scraping

1. Reads Avature site URLs from input file
2. Fetches `/sitemap.xml` from each site (single request to get all job URLs)
3. Fetches each job detail page for full description and metadata
4. Writes jobs to JSONL output file

## Parsing Strategy

The scraper uses a hybrid parsing approach to handle inconsistencies across Avature domains:

- **Global parser**: Handles common Avature HTML patterns (title, description, labeled metadata fields)
- **Site-specific fallbacks**: Custom extraction logic for domains with unique HTML structures
  - Example: UCLA Health uses `<strong>Work Location:</strong>` instead of labeled fields

**Posted Date Solution**:
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
