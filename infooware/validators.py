"""
Data validation and quality assurance for school records.
Handles deduplication, field validation, and consistency checks.
"""

import logging
from typing import Dict, List, Tuple
import re
from config import LOG_FORMAT, LOG_LEVEL, PROCESS_LOG, REQUIRED_FIELDS

logger = logging.getLogger(__name__)
handler = logging.FileHandler(PROCESS_LOG)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)


class DataValidator:
    """Validator for school data quality and consistency."""
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format."""
        if phone == "N/A":
            return True  # N/A is acceptable
        # Should contain digits and common separators
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 10
    
    @staticmethod
    def is_valid_address(address: str) -> bool:
        """Validate address format."""
        if address == "N/A":
            return True
        return len(address) > 10 and "," in address
    
    @staticmethod
    def is_valid_website(website: str) -> bool:
        """Validate website URL format."""
        if website == "N/A":
            return True
        url_pattern = r'https?://[\w\-\.]+\.[a-zA-Z]{2,}'
        return bool(re.match(url_pattern, website)) or website.startswith('www.')
    
    @staticmethod
    def validate_school_record(record: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate a school record for completeness and format.
        
        Args:
            record: School data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"Missing required field: {field}")
            elif not record[field] or record[field].strip() == "":
                errors.append(f"Empty required field: {field}")
        
        # Validate specific formats
        if "phone" in record and record["phone"] != "N/A":
            if not DataValidator.is_valid_phone(record["phone"]):
                errors.append(f"Invalid phone format: {record['phone']}")
        
        if "address" in record and record["address"] != "N/A":
            if not DataValidator.is_valid_address(record["address"]):
                errors.append(f"Invalid address format: {record['address']}")
        
        if "website" in record:
            if not DataValidator.is_valid_website(record["website"]):
                errors.append(f"Invalid website format: {record['website']}")
        
        # Check for minimum description length
        if "description" in record and record["description"] != "N/A":
            if len(record["description"]) < 10:
                errors.append("Description too short")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to standard format."""
        if phone == "N/A":
            return phone
        # Remove all non-digit characters except leading +
        phone = re.sub(r'[^\d\+]', '', phone)
        # Try to format as (XXX) XXX-XXXX
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """Normalize address format."""
        if address == "N/A":
            return address
        # Basic cleanup
        address = address.strip()
        # Ensure New York, NY format if not present
        if "New York" not in address and "NY" not in address:
            address = f"{address}, New York, NY"
        return address
    
    @staticmethod
    def normalize_website(website: str) -> str:
        """Normalize website URL."""
        if website == "N/A":
            return website
        website = website.strip()
        if not website.startswith('http'):
            website = 'https://' + website
        return website


class DeduplicationEngine:
    """Handle detection and removal of duplicate school records."""
    
    @staticmethod
    def generate_school_fingerprint(record: Dict[str, str]) -> str:
        """
        Generate a fingerprint for deduplication.
        Uses school name and address as primary key.
        
        Args:
            record: School data dictionary
            
        Returns:
            Fingerprint string
        """
        school_name = record.get("School", "").lower().strip()
        address = record.get("address", "").lower().strip()
        phone = record.get("phone", "").lower().strip()
        
        # Create composite key
        return f"{school_name}||{address}||{phone}"
    
    @staticmethod
    def find_duplicates(schools: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Tuple[int, int]]]:
        """
        Find duplicate records in school list.
        
        Args:
            schools: List of school records
            
        Returns:
            Tuple of (deduplicated_list, duplicate_pairs)
        """
        seen = {}
        deduplicated = []
        duplicates = []
        
        for idx, school in enumerate(schools):
            fingerprint = DeduplicationEngine.generate_school_fingerprint(school)
            
            if fingerprint not in seen:
                seen[fingerprint] = idx
                deduplicated.append(school)
            else:
                duplicates.append((seen[fingerprint], idx))
                logger.warning(
                    f"Duplicate detected: {school['School']} "
                    f"(record {idx} matches record {seen[fingerprint]})"
                )
        
        return deduplicated, duplicates
    
    @staticmethod
    def merge_records(primary: Dict[str, str], secondary: Dict[str, str]) -> Dict[str, str]:
        """
        Merge two school records, preferring non-N/A values.
        
        Args:
            primary: Primary record (takes precedence)
            secondary: Secondary record (used for missing values)
            
        Returns:
            Merged record
        """
        merged = primary.copy()
        
        for field in REQUIRED_FIELDS:
            if merged[field] == "N/A" and secondary.get(field) != "N/A":
                merged[field] = secondary.get(field, "N/A")
        
        # Update verification status if primary is unverified
        if merged.get("verification_status") == "Unverified":
            if secondary.get("verification_status") == "Verified":
                merged["verification_status"] = "Verified"
        
        return merged


class MissingDataTracker:
    """Track missing data for reporting."""
    
    def __init__(self):
        self.records = []
    
    def add_missing_field(self, location: str, school_name: str, field: str, reason: str = "Not found"):
        """Record a missing field."""
        self.records.append({
            "Location": location,
            "School": school_name,
            "Issue_Type": "Missing Information",
            "Field": field,
            "Details": reason
        })
        logger.warning(f"Missing field '{field}' for {school_name} in {location}: {reason}")
    
    def add_error(self, location: str, school_name: str, error_msg: str):
        """Record a processing error."""
        self.records.append({
            "Location": location,
            "School": school_name,
            "Issue_Type": "Processing Error",
            "Field": "N/A",
            "Details": error_msg
        })
        logger.error(f"Error processing {school_name} in {location}: {error_msg}")

    def add_school_not_found(self, location: str, school_name: str):
        """Record a school that was expected but not found."""
        self.records.append({
            "Location": location,
            "School": school_name,
            "Issue_Type": "School Not Found",
            "Field": "N/A",
            "Details": "Could not locate school data during discovery phase"
        })
        logger.error(f"School not found: {school_name} in {location}")
    
    def get_report(self) -> List[Dict]:
        """Get all issue records."""
        return self.records
