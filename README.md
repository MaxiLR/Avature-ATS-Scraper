# Avature ATS Scraper

Scraper for extracting job postings from Avature-hosted career sites.

**Time Investment**: ~8 hours

## Setup

1. Install Poetry if needed.
2. Install dependencies:

```bash
poetry install
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

## Data Quality & Edge Cases

**Posted Date Solution**:
While not all individual job pages include posting dates, Avature provides an **RSS feed API endpoint** that includes `pubDate` for each job:

Example: `https://uclahealth.avature.net/careers/SearchJobs/feed/?jobRecordsPerPage=100`

RSS Feed structure:

```xml
<item>
    <title><![CDATA[Attending Physician- Staff Anesthesiologist, Westwood]]></title>
    <description><![CDATA[ - 26192]]></description>
    <guid isPermaLink="true">https://uclahealth.avature.net/careers/JobDetail/...</guid>
    <link>https://uclahealth.avature.net/careers/JobDetail/...</link>
    <pubDate>Tue, 25 Jul 2023 00:00:00 +0000</pubDate>
</item>
```

**Handled Edge Cases**:

- ✓ Retry logic for failed requests (up to 3 retries with exponential backoff)
- ✓ Error page detection and filtering (skips jobs with "Error" in title and empty description)
- ✓ Site-specific HTML variations (Bloomberg labeled fields vs UCLA "Work Location:" format)
- ✓ Proper HTML entity decoding in job descriptions
- ✓ Timeout handling for slow-responding sites
- ✓ Thread-safe parallel scraping with proper session management
- ✓ Graceful handling of malformed HTML
- ✓ URL deduplication from sitemaps

**Parsing Strategy**:

The scraper uses a hybrid parsing approach to handle inconsistencies across Avature domains:

- **Global parser**: Handles common Avature HTML patterns (title, description, labeled metadata fields)
- **Site-specific fallbacks**: Custom extraction logic for domains with unique HTML structures
  - Example: UCLA Health uses `<strong>Work Location:</strong>` instead of labeled fields

## Future Enhancements

### Two-Stage Pipeline for Scale

For larger-scale deployments, a two-stage architecture would improve reliability and maintainability:

**Stage 1: Download & Store Raw Data**
- Fetch and store raw HTML pages with minimal processing
- Capture basic metadata extractable from URLs (job ID, source domain)
- Store lightweight index data (job title from `<title>` tag, URL)
- Upload to cloud storage (S3, GCS) with structured paths: `/{domain}/{job_id}/raw.html`
- Benefits: Decouples fetching from parsing, enables re-processing without re-fetching

**Stage 2: Parse & Transform**
- Process raw HTML through a global parser for common Avature patterns
- On parse failure, route to domain-specific parsers
- Domain parsers registered in a simple registry pattern:
  ```python
  DOMAIN_PARSERS = {
      "uclahealth.avature.net": UCLAHealthParser,
      "bloomberg.avature.net": BloombergParser,
  }
  ```
- Failed parses logged with domain + job ID for easy debugging
- New domain parsers added incrementally as edge cases are discovered

**Benefits**:
- Raw data preserved for re-processing when parsers improve
- Easy to add domain-specific logic without touching core scraping
- Failed parses don't block the pipeline, just queue for review
- Enables parallel processing of parse stage across workers

### Other Enhancements

- Parse RSS feed to enrich job data with posting dates
- Add structured data extraction from JSON-LD when available
- Implement incremental scraping (only fetch new/updated jobs)
- Add webhook notifications for new job discoveries
