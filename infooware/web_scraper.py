"""
Web scraper for collecting private school information.
Handles extraction from school websites and web search results.
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse
from config import REQUEST_TIMEOUT, REQUEST_RETRIES, REQUEST_RETRY_DELAY, LOG_FORMAT, LOG_LEVEL, PROCESS_LOG

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler(PROCESS_LOG)
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

class SchoolScraper:
    """Web scraper for extracting school information."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch URL content with retry logic and error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()
                logger.info(f"Successfully fetched: {url}")
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{REQUEST_RETRIES} failed for {url}: {e}")
                if attempt < REQUEST_RETRIES - 1:
                    time.sleep(REQUEST_RETRY_DELAY)
                else:
                    logger.error(f"Failed to fetch {url} after {REQUEST_RETRIES} attempts")
                    return None
    
    def extract_text_content(self, html: str, selectors: List[str]) -> str:
        """
        Extract text content from HTML using CSS selectors.
        
        Args:
            html: HTML content
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted text or "N/A"
        """
        soup = BeautifulSoup(html, 'html.parser')
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text[:500]  # Limit description length
            except Exception as e:
                logger.debug(f"Error extracting with selector {selector}: {e}")
        return "N/A"
    
    def extract_email(self, html: str) -> str:
        """Extract email address from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        # Look for email in common patterns
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        if emails:
            return emails[0]
        return "N/A"
    
    def extract_phone(self, html: str) -> str:
        """Extract phone number from HTML."""
        # Common phone patterns
        phone_patterns = [
            r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',  # (212) 123-4567, 212-123-4567, 212 123 4567
            r'\d{3}\.\d{3}\.\d{4}',                 # 212.123.4567
            r'Tel:\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            r'Phone:\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                phone = match.group(0)
                # If it started with Tel: or Phone:, strip it
                phone = re.sub(r'^(Tel|Phone):\s*', '', phone, flags=re.IGNORECASE)
                # Clean up the phone number
                phone = re.sub(r'[^\d\-\(\)\+\s]', '', phone).strip()
                logger.debug(f"Extracted phone: {phone}")
                return phone
        
        return "N/A"
    
    def extract_address(self, html: str) -> str:
        """Extract address from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator=' ')
        
        # Enhanced pattern for NYC addresses
        # Match street number + street name + optional suite + New York + NY + ZIP
        address_pattern = r'\d+\s+[A-Za-z0-9\s\.\-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Place|Pl|Way|West|East|North|South|W|E|N|S)\.?\s*(?:(?:Suite|Ste|Floor|Fl|#)\s*[A-Za-z0-9\-]+\s*)?,?\s*New York\s*,?\s*NY\s*,?\s*\d{5}(?:-\d{4})?'
        
        match = re.search(address_pattern, text, re.IGNORECASE)
        if match:
            address = match.group(0)
            # Normalize whitespace and commas
            address = re.sub(r'\s+', ' ', address).strip()
            address = re.sub(r'\s*,\s*', ', ', address)
            logger.debug(f"Extracted address: {address}")
            return address
        
        # Fallback: Look for "New York, NY" and try to capture the preceding part
        fallback_pattern = r'[^>\r\n]+New York\s*,?\s*NY\s*,?\s*\d{5}'
        match = re.search(fallback_pattern, text, re.IGNORECASE)
        if match:
            address = match.group(0).strip()
            if len(address) > 10:
                return address
        
        return "N/A"
    
    def scrape_school_website(self, school_name: str, website_url: str) -> Dict[str, str]:
        """
        Scrape information from a school's website.
        
        Args:
            school_name: Name of the school
            website_url: URL of the school's website
            
        Returns:
            Dictionary with extracted school information
        """
        logger.info(f"Scraping {school_name} from {website_url}")
        
        # Ensure URL has protocol
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        
        html = self.fetch_url(website_url)
        if not html:
            logger.error(f"Could not fetch website for {school_name}")
            return self._get_empty_school_dict(school_name, website_url)
        
        # Extract various fields
        school_data = {
            "School": school_name,
            "city": "New York",
            "category": "Private Schools",
            "website": website_url,
            "description": self._extract_description(html),
            "verification_status": "Unverified",  # Will be marked verified after manual review
            "address": self.extract_address(html),
            "phone": self.extract_phone(html),
        }
        
        logger.info(f"Successfully scraped {school_name}")
        return school_data
    
    def _extract_description(self, html: str) -> str:
        """Extract school description from HTML."""
        selectors = [
            'meta[name="description"]',
            '[class*="mission"]',
            '[class*="about"]',
            'p',
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('meta'):
                    soup = BeautifulSoup(html, 'html.parser')
                    meta = soup.select_one(selector)
                    if meta and meta.get('content'):
                        return meta.get('content')[:500]
                else:
                    soup = BeautifulSoup(html, 'html.parser')
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if text and len(text) > 50:
                            return text[:500]
            except Exception as e:
                logger.debug(f"Error extracting description with {selector}: {e}")
        
        return "N/A"
    
    def _get_empty_school_dict(self, school_name: str, website_url: str) -> Dict[str, str]:
        """Get empty school dictionary for schools that couldn't be scraped."""
        return {
            "School": school_name,
            "city": "New York",
            "category": "Private Schools",
            "website": website_url,
            "description": "N/A",
            "verification_status": "Unverified",
            "address": "N/A",
            "phone": "N/A",
        }

    def discover_school_website(self, school_name: str, directories: List[str]) -> str:
        """Try to discover a school website using public directory search results."""
        query = quote_plus(f"{school_name} New York private school")
        for directory in directories:
            search_url = f"{directory}/search?query={query}"
            html = self.fetch_url(search_url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.select('a[href]'):
                href = link.get('href')
                if not href:
                    continue
                href = href.strip()
                if directory in href and school_name.lower().split()[0] in href.lower():
                    return self._normalize_discovered_url(href)
                if 'http' in href and school_name.lower() in href.lower() and 'niche' not in href.lower():
                    return self._normalize_discovered_url(href)

        return "N/A"

    def _normalize_discovered_url(self, href: str) -> str:
        """Normalize a discovered URL to an absolute URL."""
        if href.startswith('//'):
            return f'https:{href}'
        if href.startswith('/'):
            return f'https://{urlparse(href).netloc or ""}{href}'
        return href


def scrape_schools(schools_config: List[Dict]) -> List[Dict[str, str]]:
    """
    Scrape information for a list of schools.
    
    Args:
        schools_config: List of school configurations with name and website
        
    Returns:
        List of school data dictionaries
    """
    scraper = SchoolScraper()
    schools_data = []
    
    for school in schools_config:
        logger.info(f"Processing {school['name']}")
        school_data = scraper.scrape_school_website(
            school['name'],
            school['website']
        )
        schools_data.append(school_data)
        
        # Rate limiting - be respectful to servers
        time.sleep(1 / 2)  # Max 2 requests per second
    
    return schools_data
