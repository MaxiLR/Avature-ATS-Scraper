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

### Automated Discovery (Not Implemented)

**Note**: Automated source discovery is not currently implemented due to time constraints and the need for CAPTCHA solving capabilities.

**Recommended Approach for Future Implementation**:
The most effective method for discovering new Avature career sites would be:

1. **Google Search**: Query `site:*.avature.net inurl:SearchJobs`
   - This targets active job portals with the SearchJobs endpoint
   - Avoids false positives from generic subdomain enumeration

2. **URL Pattern Extraction**:
   - Extract portal URLs from SearchJobs endpoints
   - Example: `https://baufest.avature.net/jobs/SearchJobs/?jobOffset=20` → `https://baufest.avature.net/jobs`
   - Convert to sitemap: `https://baufest.avature.net/jobs/sitemap.xml`

3. **Validation**:
   - Verify sitemap exists and contains `/JobDetail/` links
   - Confirms the site is an active job portal with listings

**Why This Approach?**

- Targets real, active career sites (not just DNS records)
- SearchJobs endpoint is specific to Avature ATS job portals
- Much more accurate than subdomain enumeration (e.g., subfinder returns 1985+ subdomains, most invalid)
- Alternatives like subfinder or crt.sh are not that reliable for this task given the identified pattern

**Current Workaround**:
Manually discover sites by:

1. Searching Google for `site:*.avature.net inurl:SearchJobs`
2. Adding discovered URLs to `input/sites.txt`

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

**Future Enhancement**: Parse RSS feed to enrich job data with posting dates.

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
  - Future: Add parsers for domains with unique patterns as they're discovered

For production use at scale, each domain displaying JobDetails with significant structural differences would benefit from dedicated parsing logic, complementing the global approach. This ensures maximum data extraction while maintaining code maintainability.
