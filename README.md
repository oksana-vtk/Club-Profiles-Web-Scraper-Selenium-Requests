# Club Profiles Web Scraper (Selenium + Requests)
### Project Overview

This project is a two-phase web scraping pipeline designed to collect structured data 
from 323 club profiles on a target website.

The scraper:

- Extracts preview data from listing pages
- Visits each individual club profile
- Collects static and dynamic content
- Produces a clean, fully structured CSV file
- Guarantees no empty cells (uses / as fallback)

The solution combines Selenium, Requests, and BeautifulSoup to ensure both performance and reliability.

### Key Features

- Scrapes 323 club profiles
- Handles dynamic JavaScript content
- Uses environment variables for configuration
- Partial CSV saving every N records (fault-tolerant)
- Robust logging system
- Clean, fixed-column CSV output
- No empty cells (/ used where data is missing)

## Architecture
#### Phase 1 — Listing Page Scraping (Selenium)

- Opens search page
- Handles pop-ups
- Expands search filters
- Triggers search results
- Extracts preview-level club data
- Saves results to CSV

#### Phase 2 — Detail Page Scraping

**Hybrid approach:**
- Requests + BeautifulSoup → static content
- Selenium → dynamic tabs (Installations & Committee)

This significantly improves speed while still capturing dynamic data.

### Output Files
| File                  | Description                         |
| --------------------- | ----------------------------------- |
| `OUTPUT_FILE_1`       | Clubs listing (preview data)        |
| `OUTPUT_FILE_2`       | Final structured dataset            |
| `OUTPUT_FILE_PARTIAL` | Partial backup file (every N clubs) |
| `LOG_FILE`            | Execution logs                      |


**All CSV files use:**

- UTF-8 with BOM
- `*` as separator (safe for addresses)

### Final CSV Columns

The final dataset contains one row per club with fixed columns:
- `club_id`
- `name_preview`
- `postal_code_preview`
- `city_preview`
- `preview_line_3`
- `detailed_url`
- `logo_url_preview`
- `full_name`
- `full_address`
- `PostalCityCountry`
- `phone`
- `website`
- `email`
- `total_members`
- `installation_1`
- `installation_2`
- `installation_3`
- `installation_4`
- `president`

No empty cells — missing values are replaced with `/`.

### Extracted Data Details
**Preview (Listing Page)**

- Club ID
- Name
- Postal code
- City
- Court / installation preview
- Profile URL
- Logo image URL

**Detail Page**

- Full official name
- Street address
- Postal code, city & country
- Phone number
- Email
- Website
- Total members
- Up to 4 installations (dynamic content)
- Club president (dynamic content)

### Configuration (.env)

All selectors, URLs, and paths are externalized what makes the 
scraper easy to maintain and adapt if the website changes.

- `BASE_URL=`
- `SEARCH_URL=`
- `OUTPUT_FILE_1=`
- `OUTPUT_FILE_2=`
- `OUTPUT_FILE_PARTIAL=`
- `LOG_FILE=`
- `PARTIAL_SAVE_EVERY=`
- `POP_UP_SELECTOR=`
- `SEARCH_SELECTOR=`
- `EXPANDED_SEARCH_PANEL=`
- `BUTTON_PATH=`
- `RESULTS_SELECTOR=`
- `NAME_LINK_SELECTOR=`
- `INSTALLATION_TAB_XPATH=`
- `INSTALL_PANEL_XPATH=`
- `PRESIDENT_PANEL_XPATH=`
- `PRESIDENT_SELECTOR=`


### Reliability & Safety

- Randomized delays to reduce blocking
- Partial CSV backups every N clubs
- Graceful error handling per club
- Browser auto-cleanup
- Detailed logging with timestamps

### Tech Stack

- Python 3
- Selenium (Chrome)
- Requests
- BeautifulSoup
- Pandas
- dotenv
- Logging

## Result

- Successfully scraped all required fields
- Delivered fully structured CSV
- Meets all job requirements
- Ready for analysis, BI tools, or database import