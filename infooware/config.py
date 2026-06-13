"""
Configuration management for school data collection.
Centralized location and school data source definitions.
"""

import logging
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Output files
OUTPUT_CSV = DATA_DIR / "schools.csv"
MISSING_DATA_REPORT = DATA_DIR / "missing_data_report.csv"
ERROR_LOG = LOGS_DIR / "errors.log"
PROCESS_LOG = LOGS_DIR / "process.log"

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# Timeout for web requests (seconds)
REQUEST_TIMEOUT = 10
REQUEST_RETRIES = 3
REQUEST_RETRY_DELAY = 2  # seconds

# Rate limiting
REQUESTS_PER_SECOND = 1  # To be respectful to websites

# Target locations and schools
# Format: {location_name: {zip_codes: [list of zips]}}
TARGET_LOCATIONS = {
    "Upper East Side": ["10021", "10028", "10044", "10065", "10075", "10128"],
    "Upper West Side": ["10023", "10024", "10025"]
}

# API Endpoints
PUBLIC_SCHOOLS_API = "https://data.cityofnewyork.us/resource/8b6c-7uty.json"
NON_PUBLIC_SCHOOLS_API = "https://data.ny.gov/resource/7964-9v95.json"

# Target schools for initial private school list (will be augmented by API)
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

# Required fields that must be populated
REQUIRED_FIELDS = [
    "School",
    "city",
    "category",
    "website",
    "description",
    "verification_status",
    "address",
    "phone"
]

# CSV column order (must match template exactly)
CSV_COLUMNS = [
    "School",
    "city",
    "category",
    "website",
    "description",
    "verification_status",
    "address",
    "phone"
]

# Data source priorities for field extraction
DATA_SOURCE_PRIORITY = {
    "phone": ["website_extraction", "directory_lookup", "manual"],
    "address": ["website_extraction", "google_maps", "manual"],
    "description": ["website_extraction", "manual"],
    "website": ["initial_data", "search_result"],
}

# Directories to search for school information
SCHOOL_DIRECTORIES = [
    "https://www.greatschools.org",
    "https://www.niche.com",
]
