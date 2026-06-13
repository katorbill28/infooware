# School Data Collection System

Automated system for collecting comprehensive private school information from multiple locations. This project collects school data through web scraping, validates data quality, removes duplicates, and generates detailed reports.

## Features

- **Automated Web Scraping**: Extracts school information directly from school websites
- **Comprehensive Data Collection**: Gathers school name, address, phone, website, description, and more
- **Data Validation**: Validates phone numbers, addresses, and URLs
- **Deduplication**: Automatically detects and removes duplicate records
- **Error Handling & Logging**: Robust error handling with detailed logs for debugging
- **Missing Data Tracking**: Generates detailed reports of missing or unverified information
- **CSV Export**: Outputs data in the exact template format required

## Project Structure

```
infooware/
├── config.py              # Configuration management and constants
├── web_scraper.py         # Web scraping logic for school websites
├── validators.py          # Data validation and deduplication
├── main.py               # Main orchestration script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── data/                 # Output directory (created automatically)
│   ├── schools.csv       # Collected school data
│   └── missing_data_report.csv  # Missing data report
└── logs/                 # Log files (created automatically)
    ├── process.log       # Processing log
    └── errors.log        # Error log
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Internet connection for web scraping

## Installation

1. **Clone or download the project**:
   ```bash
   cd infooware
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.py` to add or modify schools to collect:

```python
SCHOOLS_TO_COLLECT = {
    "New York - Upper East Side": {
        "schools": [
            {
                "name": "The Brearley School",
                "website": "https://www.brearley.org",
                "type": "Private Schools"
            },
            {
                "name": "Trinity School",
                "website": "https://www.trinityschoolnyc.org",
                "type": "Private Schools"
            }
        ]
    }
}
```

### Configuration Options

- **REQUEST_TIMEOUT**: Maximum time to wait for web requests (default: 10 seconds)
- **REQUEST_RETRIES**: Number of retry attempts for failed requests (default: 3)
- **REQUEST_RETRY_DELAY**: Delay between retry attempts (default: 2 seconds)
- **REQUESTS_PER_SECOND**: Rate limiting to be respectful to websites (default: 1)

## Usage

### Run the complete data collection workflow:

```bash
python main.py
```

This will:
1. Scrape all configured schools' websites
2. Extract school information (name, address, phone, description, etc.)
3. Validate all data for completeness and format
4. Remove duplicate records
5. Generate a missing data report
6. Save output to CSV files

### Run individual components (Advanced):

```python
# Just scrape without validation
from web_scraper import scrape_schools
from config import SCHOOLS_TO_COLLECT

schools_list = []
for location, config in SCHOOLS_TO_COLLECT.items():
    schools = scrape_schools(config["schools"])
    schools_list.extend(schools)
```

## Output Files

### schools.csv
Main output file with all collected school data. Columns:
- **School**: School name
- **city**: City location
- **category**: School type (e.g., "Private Schools")
- **website**: School website URL
- **description**: School description/mission statement
- **verification_status**: Whether information has been verified
- **address**: Full address with zip code
- **phone**: Contact phone number

### missing_data_report.csv
Report of missing or unverified data:
- **School**: School name
- **Missing_Field**: Field that has missing data
- **Reason**: Why the data is missing
- **Type**: Type of issue (Missing Information or Processing Error)

## Logging

Detailed logs are saved to the `logs/` directory:

- **process.log**: All processing steps and informational messages
- **errors.log**: Error messages and issues encountered

View logs in real-time:
```bash
# Windows
Get-Content logs\process.log -Wait

# macOS/Linux
tail -f logs/process.log
```

## Data Validation

The system validates:

✓ **Required Fields**: Ensures all mandatory fields are populated
✓ **Phone Numbers**: Validates phone number format (10+ digits)
✓ **Addresses**: Checks address format includes street, city, state, zip
✓ **Websites**: Validates URL format
✓ **Descriptions**: Ensures descriptions are minimum length
✓ **Duplicates**: Detects and removes duplicate records based on school name and address

## Error Handling

The system includes robust error handling:

- **Retry Logic**: Failed requests are retried up to 3 times with delays
- **Graceful Degradation**: If a field can't be extracted, it's marked as "N/A"
- **Logging**: All errors are logged for review and debugging
- **Partial Success**: Continues processing even if some schools fail

## Troubleshooting

### No data collected
- Check internet connection
- Verify school websites are correct in `config.py`
- Check `logs/errors.log` for specific errors
- Try increasing `REQUEST_TIMEOUT` in `config.py`

### Missing fields in output
- Some fields may not be available on school websites (marked as "N/A")
- Check `missing_data_report.csv` for details
- Consider manual verification for important schools

### Slow performance
- Reduce `REQUESTS_PER_SECOND` to prevent rate limiting
- Add delays between requests if getting blocked by websites
- Run during off-peak hours

## Quality Standards

This project maintains strict quality standards:

✗ No fabricated data
✗ No estimated values
✗ No guessed contact information
✗ No guessed website URLs

All data is sourced from school websites and verified as available.

## Adding New Schools

To add new schools to collect:

1. Open `config.py`
2. Add school to the `SCHOOLS_TO_COLLECT` dictionary:
   ```python
   "name": "School Name",
   "website": "https://school-website.org",
   "type": "Private Schools"
   ```
3. Run `python main.py`

## Data Quality Report

After running the collection, review:

1. **schools.csv**: Verify all required fields are populated
2. **missing_data_report.csv**: Review any missing or unverified data
3. **logs/process.log**: Check for any warnings or issues
4. **logs/errors.log**: Review any errors encountered

## Advanced Features

### Custom Validation

Create custom validators in `validators.py`:

```python
@staticmethod
def is_valid_custom_field(value: str) -> bool:
    # Your validation logic
    return True
```

### Extending the Scraper

Add new extraction methods to `SchoolScraper` class:

```python
def extract_custom_field(self, html: str) -> str:
    # Your extraction logic
    return "extracted_value"
```

### Integration with External Systems

The output CSVs can be easily integrated with spreadsheet applications, databases, or other systems:

```python
import pandas as pd
df = pd.read_csv('data/schools.csv')
# Process as needed
```

## Performance

- Typical collection time: ~5-10 seconds per school (including retries)
- Rate limited to 1-2 requests per second (respectful scraping)
- Deduplication and validation are near-instant
- Memory efficient for large datasets

## Contributing

To improve this system:

1. Enhance web scraping methods in `web_scraper.py`
2. Add new data sources to `config.py`
3. Improve validation rules in `validators.py`
4. Add support for new school types or categories

## License

This project is provided as-is for educational and business purposes.

## Support

For issues or questions:
1. Check the logs in the `logs/` directory
2. Review the missing data report
3. Verify configuration in `config.py`
4. Ensure all dependencies are installed correctly

## Version History

### v1.0.0 (Initial Release)
- Web scraping for private schools
- Data validation and deduplication
- CSV export with template format
- Comprehensive logging and reporting

## Notes

- The system respects server resources with rate limiting
- Retries are built in for failed requests
- All data sources must be publicly available
- Manual verification of critical fields is recommended
