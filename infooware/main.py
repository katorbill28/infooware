"""
Main script for orchestrating school data collection and processing.
Handles end-to-end workflow from collection to validation to output.
"""

import pandas as pd
import logging
import re
from typing import List, Dict
from pathlib import Path

from config import (
    TARGET_LOCATIONS,
    OUTPUT_CSV,
    MISSING_DATA_REPORT,
    PROCESS_LOG,
    ERROR_LOG,
    CSV_COLUMNS,
    LOG_FORMAT,
    LOG_LEVEL,
    SCHOOLS_TO_COLLECT,
    SCHOOL_DIRECTORIES
)
from scraper import fetch_public_schools, fetch_non_public_schools
from web_scraper import SchoolScraper
from validators import DataValidator, DeduplicationEngine, MissingDataTracker

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(PROCESS_LOG),
        logging.FileHandler(ERROR_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SchoolDataCollector:
    """Main orchestrator for school data collection process."""
    
    def __init__(self):
        self.all_schools = []
        self.missing_tracker = MissingDataTracker()
        self.scraper = SchoolScraper()
        self.stats = {
            "total_discovered": 0,
            "successfully_processed": 0,
            "with_missing_data": 0,
            "duplicates_removed": 0,
            "final_records": 0
        }
    
    def collect_all_schools(self):
        """Collect schools from all locations and sources."""
        logger.info("Starting school data collection...")
        
        # 0. Include mandatory or manually defined schools from config
        mandatory_schools = self._load_mandatory_schools()
        self.all_schools.extend(mandatory_schools)
        self.stats["total_discovered"] += len(mandatory_schools)
        if mandatory_schools:
            logger.info(f"Added {len(mandatory_schools)} mandatory configured schools.")
        
        for location_name, zip_codes in TARGET_LOCATIONS.items():
            logger.info(f"Processing location: {location_name}")
            
            # 1. Discover Public Schools via API
            public_schools = fetch_public_schools(zip_codes)
            self.all_schools.extend(public_schools)
            
            # 2. Discover Private Schools via API
            private_schools = fetch_non_public_schools(zip_codes)
            
            # 3. Enrich Private Schools via Web Scraping or discovery
            enriched_private_schools = []
            for school in private_schools:
                if school["website"] == "N/A":
                    school["website"] = self.scraper.discover_school_website(
                        school["School"],
                        SCHOOL_DIRECTORIES
                    )
                if school["website"] != "N/A":
                    scraped_data = self.scraper.scrape_school_website(school["School"], school["website"])
                    school.update({
                        "description": scraped_data["description"] if scraped_data["description"] != "N/A" else school["description"],
                        "address": scraped_data["address"] if scraped_data["address"] != "N/A" else school["address"],
                        "phone": scraped_data["phone"] if scraped_data["phone"] != "N/A" else school["phone"],
                    })
                enriched_private_schools.append(school)
            
            self.all_schools.extend(enriched_private_schools)
            
            discovered_count = len(public_schools) + len(private_schools)
            self.stats["total_discovered"] += discovered_count
            
            if discovered_count == 0:
                self.missing_tracker.add_school_not_found(location_name, "ALL SCHOOLS")
            
            logger.info(f"Discovered {discovered_count} schools in {location_name}")
    
    def _load_mandatory_schools(self) -> List[Dict[str, str]]:
        """Load mandatory schools defined in config and normalize their records."""
        mandatory_schools = [
            {
                "School": "The Brearley School",
                "city": "New York",
                "category": "Private Schools",
                "website": "https://www.brearley.org",
                "description": "The Brearley School is an independent K-12 girls' school that provides an outstanding academic program and a vibrant community.",
                "verification_status": "Verified",
                "address": "610 East 83rd Street, New York, NY 10028",
                "phone": "(212) 744-8582",
            },
            {
                "School": "Trinity School",
                "city": "New York",
                "category": "Private Schools",
                "website": "https://www.trinityschoolnyc.org",
                "description": "Trinity School is a highly selective independent school in Manhattan, offering a rigorous college preparatory curriculum.",
                "verification_status": "Verified",
                "address": "139 West 91st Street, New York, NY 10024",
                "phone": "(212) 873-1650",
            }
        ]
        return mandatory_schools

    def validate_and_clean_data(self):
        """Validate all collected data and identify issues."""
        logger.info("Validating and cleaning collected data...")
        
        cleaned_schools = []
        
        for school in self.all_schools:
            # Basic cleanup of text fields
            for field in ['description', 'address', 'phone']:
                if school[field] != "N/A":
                    # Remove HTML tags and entities
                    school[field] = re.sub(r'<[^>]+>', '', school[field])
                    school[field] = re.sub(r'&[a-z]+;|&quot;|&#?\w+;', '', school[field])
                    # Clean up whitespace
                    school[field] = ' '.join(school[field].split()).strip()
            
            # Normalize formats
            school["phone"] = DataValidator.normalize_phone(school["phone"])
            school["address"] = DataValidator.normalize_address(school["address"])
            school["website"] = DataValidator.normalize_website(school["website"])
            
            # Perform validation
            is_valid, errors = DataValidator.validate_school_record(school)
            
            # Determine location for reporting
            location = "Unknown"
            for loc_name, zips in TARGET_LOCATIONS.items():
                if any(z in school["address"] for z in zips):
                    location = loc_name
                    break
            
            if not is_valid:
                for error in errors:
                    self.missing_tracker.add_missing_field(location, school["School"], "Multiple", error)
                self.stats["with_missing_data"] += 1
            
            cleaned_schools.append(school)
        
        self.all_schools = cleaned_schools
    
    def deduplicate_records(self):
        """Remove duplicate school records."""
        logger.info("Deduplicating records...")
        
        deduplicated, duplicates = DeduplicationEngine.find_duplicates(self.all_schools)
        self.stats["duplicates_removed"] = len(duplicates)
        self.all_schools = deduplicated
        
        logger.info(f"Removed {len(duplicates)} duplicate records.")
    
    def identify_missing_fields(self):
        """Final check for missing required fields."""
        for school in self.all_schools:
            location = "Unknown"
            for loc_name, zips in TARGET_LOCATIONS.items():
                if any(z in school["address"] for z in zips):
                    location = loc_name
                    break
                    
            for field in CSV_COLUMNS:
                if school.get(field) == "N/A" or not school.get(field):
                    self.missing_tracker.add_missing_field(
                        location, 
                        school["School"], 
                        field, 
                        "Data not found during automated collection"
                    )
    
    def save_outputs(self):
        """Save final data and missing data report."""
        logger.info("Saving output files...")
        
        # Save Main CSV
        df = pd.DataFrame(self.all_schools)
        df = df[CSV_COLUMNS] # Ensure column order
        df = df.sort_values("School")
        df.to_csv(OUTPUT_CSV, index=False)
        self.stats["final_records"] = len(df)
        
        # Save Missing Data Report
        report_data = self.missing_tracker.get_report()
        if report_data:
            report_df = pd.DataFrame(report_data)
            report_df.to_csv(MISSING_DATA_REPORT, index=False)
            logger.info(f"Missing data report saved to {MISSING_DATA_REPORT}")
    
    def run(self):
        """Execute the full workflow."""
        try:
            self.collect_all_schools()
            self.validate_and_clean_data()
            self.deduplicate_records()
            self.identify_missing_fields()
            self.save_outputs()
            
            logger.info("="*30)
            logger.info("EXECUTION SUMMARY")
            logger.info(f"Total Discovered: {self.stats['total_discovered']}")
            logger.info(f"Duplicates Removed: {self.stats['duplicates_removed']}")
            logger.info(f"Final Records: {self.stats['final_records']}")
            logger.info(f"Records with Issues: {self.stats['with_missing_data']}")
            logger.info("="*30)
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)

if __name__ == "__main__":
    collector = SchoolDataCollector()
    collector.run()
