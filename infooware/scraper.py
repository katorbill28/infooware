"""
API discovery module for identifying public and non-public schools.
Fetches data from NYC Open Data and NYS Open Data APIs.
"""

import requests
import logging
from typing import List, Dict
from config import PUBLIC_SCHOOLS_API, NON_PUBLIC_SCHOOLS_API, PROCESS_LOG, LOG_FORMAT, LOG_LEVEL

logger = logging.getLogger(__name__)
handler = logging.FileHandler(PROCESS_LOG)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

def fetch_public_schools(zip_codes: List[str]) -> List[Dict]:
    """Fetch public schools from NYC Open Data for given ZIP codes."""
    logger.info(f"Fetching public schools for ZIPs: {zip_codes}")
    schools = []
    
    for zip_code in zip_codes:
        params = {
            "postcode": zip_code,
            "$limit": 1000
        }
        try:
            response = requests.get(PUBLIC_SCHOOLS_API, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    schools.append({
                        "School": item.get("school_name", "N/A"),
                        "city": "New York",
                        "category": "Public Schools",
                        "website": item.get("website", "N/A"),
                        "description": item.get("overview_paragraph", "N/A"),
                        "verification_status": "Verified",
                        "address": f"{item.get('primary_address_line_1', '')}, New York, NY {item.get('postcode', '')}",
                        "phone": item.get("phone_number", "N/A")
                    })
                logger.info(f"Found {len(data)} public schools in {zip_code}")
            else:
                logger.error(f"Error fetching public schools for {zip_code}: {response.status_code}")
        except Exception as e:
            logger.error(f"Exception for public schools {zip_code}: {e}")
            
    return schools

def fetch_non_public_schools(zip_codes: List[str]) -> List[Dict]:
    """Fetch non-public schools from NYS Open Data for given ZIP codes."""
    logger.info(f"Fetching non-public schools for ZIPs: {zip_codes}")
    schools = []
    
    for zip_code in zip_codes:
        params = {
            "county": "NEW YORK",
            "zip_code": zip_code,
            "$limit": 1000
        }
        try:
            response = requests.get(NON_PUBLIC_SCHOOLS_API, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    schools.append({
                        "School": item.get("school_name", "N/A"),
                        "city": "New York",
                        "category": "Private Schools",
                        "website": item.get("website", "N/A"),
                        "description": item.get("description", "N/A"),
                        "verification_status": "Unverified",
                        "address": f"{item.get('street_address', '')}, New York, NY {item.get('zip_code', '')}",
                        "phone": item.get("phone_number", "N/A")
                    })
                logger.info(f"Found {len(data)} non-public schools in {zip_code}")
            else:
                logger.error(f"Error fetching non-public schools for {zip_code}: {response.status_code}")
        except Exception as e:
            logger.error(f"Exception for non-public schools {zip_code}: {e}")
            
    return schools
