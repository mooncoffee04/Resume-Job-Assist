#!/usr/bin/env python3
"""
Enhanced Glassdoor Job Scraper with Selenium
Uses browser automation to better emulate human behavior and bypass anti-bot measures
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    """Data class for job listing information"""
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: str
    requirements: List[str]
    benefits: List[str]
    job_type: str
    experience_level: str
    technologies: List[str]
    posted_date: str
    application_url: str
    company_rating: Optional[float]
    company_size: Optional[str]
    industry: Optional[str]
    remote_type: str
    source: str = "glassdoor"

class GlassdoorSeleniumScraper:
    """Enhanced Glassdoor scraper using Selenium WebDriver"""
    
    def __init__(self, email=None, password=None, headless=True, use_india_site=True):
        """Initialize the Selenium-based scraper"""
        self.email = email
        self.password = password
        self.use_india_site = use_india_site
        self.driver = None
        self.wait = None
        
        if use_india_site:
            self.base_url = "https://www.glassdoor.co.in"
            self.jobs_url = "https://www.glassdoor.co.in/Job/index.htm"
        else:
            self.base_url = "https://www.glassdoor.com"
            self.jobs_url = "https://www.glassdoor.com/Job/index.htm"
        
        # Technology keywords for extraction
        self.tech_keywords = [
            'python', 'java', 'javascript', 'react', 'node.js', 'django', 'flask',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'data science', 'pandas', 'numpy', 'scikit-learn', 'tableau',
            'html', 'css', 'typescript', 'angular', 'vue.js', 'bootstrap',
            'c++', 'c#', 'go', 'rust', 'scala', 'kotlin', 'swift', 'php'
        ]
        
        self.setup_driver(headless)
        
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # Add arguments to make Chrome less detectable as automation
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set wait timeout
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("🌐 Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {str(e)}")
            logger.info("💡 Make sure you have ChromeDriver installed:")
            logger.info("   brew install chromedriver  # On Mac")
            logger.info("   Or download from: https://chromedriver.chromium.org/")
            raise
    
    def handle_verification_if_needed(self):
        """Handle any additional verification steps that might appear"""
        try:
            # Check for common verification elements
            verification_indicators = [
                'captcha',
                'verify',
                'security',
                'robot',
                'human'
            ]
            
            page_source = self.driver.page_source.lower()
            
            if any(indicator in page_source for indicator in verification_indicators):
                logger.warning("⚠️ Verification step detected!")
                logger.info("🤖 Please complete any CAPTCHA or verification manually")
                logger.info("⏳ Waiting 30 seconds for manual completion...")
                
                # Wait for user to complete verification
                # time.sleep(30)
                
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking for verification: {str(e)}")
            return False

    def login(self):
        """Login to Glassdoor using Selenium with two-step process"""
        if not self.email or not self.password:
            logger.warning("⚠️ No credentials provided. Proceeding without login.")
            return False
        
        try:
            logger.info("🔐 Attempting to login to Glassdoor...")
            
            # Navigate to login page
            login_url = f"{self.base_url}/profile/login_input.htm"
            self.driver.get(login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # STEP 1: Enter email and proceed to password page
            logger.info("📧 Step 1: Entering email...")
            
            # Find and fill email field
            email_selectors = [
                '#userEmail',
                '[name="username"]',
                '[type="email"]',
                '#email',
                'input[placeholder*="email"]',
                '.EmailForm input'
            ]
            
            email_element = None
            for selector in email_selectors:
                try:
                    email_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not email_element:
                logger.error("❌ Could not find email input field")
                return False
            
            # Clear and enter email
            email_element.clear()
            time.sleep(1)
            email_element.send_keys(self.email)
            logger.info("✅ Email entered")
            
            # Find and click continue/next button for email step
            email_continue_selectors = [
                '#emailButton',
                'button[name="submit"]',
                '[type="submit"]',
                'button:contains("Continue")',
                'button:contains("Next")',
                '.EmailForm button',
                '#continueBtn',
                'button[data-test="email-form-button"]'
            ]
            
            email_continue_button = None
            for selector in email_continue_selectors:
                try:
                    email_continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if email_continue_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if email_continue_button:
                email_continue_button.click()
                logger.info("✅ Email continue button clicked")
            else:
                # Try pressing Enter on email field
                from selenium.webdriver.common.keys import Keys
                email_element.send_keys(Keys.RETURN)
                logger.info("✅ Email submitted with Enter key")
            
            # Wait for redirect to password page
            logger.info("⏳ Waiting for password page...")
            time.sleep(4)
            
            # STEP 2: Enter password on the second page
            logger.info("🔑 Step 2: Entering password...")
            
            # Wait for password field to appear (it might take a moment)
            password_selectors = [
                '#userPassword',
                '[name="password"]',
                '[type="password"]',
                '#password',
                'input[placeholder*="password"]',
                '.PasswordForm input'
            ]
            
            password_element = None
            for selector in password_selectors:
                try:
                    password_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not password_element:
                logger.error("❌ Could not find password input field on second page")
                # Try to take a screenshot for debugging
                try:
                    self.driver.save_screenshot("glassdoor_password_page_debug.png")
                    logger.info("📸 Saved debug screenshot: glassdoor_password_page_debug.png")
                except:
                    pass
                return False
            
            # Clear and enter password
            password_element.clear()
            time.sleep(1)
            password_element.send_keys(self.password)
            logger.info("✅ Password entered")
            
            # Find and click login button on password page
            password_login_selectors = [
                '#signInBtn',
                '#passwordButton',
                'button[name="submit"]',
                '[type="submit"]',
                'button:contains("Sign In")',
                'button:contains("Login")',
                '.PasswordForm button',
                'button[data-test="password-form-button"]'
            ]
            
            login_button = None
            for selector in password_login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if login_button:
                login_button.click()
                logger.info("✅ Password login button clicked")
            else:
                # Try pressing Enter on password field
                from selenium.webdriver.common.keys import Keys
                password_element.send_keys(Keys.RETURN)
                logger.info("✅ Password submitted with Enter key")
            
            # Check for any verification steps before proceeding
            self.handle_verification_if_needed()
            
            # Wait for login to complete
            logger.info("⏳ Waiting for login to complete...")
            time.sleep(6)
            
            # Check if login was successful
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Multiple ways to check successful login
            login_success_indicators = [
                'dashboard' in current_url.lower(),
                'profile' in current_url.lower(),
                'account' in current_url.lower(),
                'login' not in current_url.lower(),
                'welcome' in page_source,
                'sign out' in page_source,
                'logout' in page_source
            ]
            
            if any(login_success_indicators):
                logger.info("✅ Successfully logged in to Glassdoor")
                return True
            else:
                logger.warning("⚠️ Login may have failed")
                logger.info(f"Current URL: {current_url}")
                # Save screenshot for debugging
                try:
                    self.driver.save_screenshot("glassdoor_login_result_debug.png")
                    logger.info("📸 Saved debug screenshot: glassdoor_login_result_debug.png")
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            # Save screenshot for debugging
            try:
                self.driver.save_screenshot("glassdoor_login_error_debug.png")
                logger.info("📸 Saved error screenshot: glassdoor_login_error_debug.png")
            except:
                pass
            return False
    
    def search_jobs(self, keywords: str, location: str = "India", max_pages: int = 3) -> List[JobListing]:
        """Search for jobs using Selenium automation with auto-redirect handling"""
        logger.info(f"🔍 Searching for: '{keywords}' in '{location}'")
        
        all_jobs = []
        max_pages = 3  # Limit to 3 pages to avoid long waits
        current_page = 1
        
        try:
            # Navigate to jobs page
            self.driver.get(self.jobs_url)
            time.sleep(3)
            
            # Find and fill job search field
            job_input_selectors = [
                '#searchBar-jobTitle',
                '[placeholder*="job"]',
                '[id*="job"]',
                '.job-search input'
            ]
            
            job_input = None
            for selector in job_input_selectors:
                try:
                    job_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not job_input:
                logger.error("❌ Could not find job search input")
                return []
            
            job_input.clear()
            job_input.send_keys(keywords)
            logger.info(f"✅ Job keywords entered: {keywords}")
            
            # Small delay to let the field register
            time.sleep(1)
            
            # Find and fill location field
            location_input_selectors = [
                '#searchBar-location',
                '[placeholder*="location"]',
                '[placeholder*="city"]',
                '[id*="location"]'
            ]
            
            location_input = None
            for selector in location_input_selectors:
                try:
                    location_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if location_input:
                location_input.clear()
                time.sleep(1)
                location_input.send_keys(location)
                logger.info(f"✅ Location entered: {location}")
                
                # Wait for autocomplete dropdown to appear
                time.sleep(2)
                
                # Try to click on the autocomplete suggestion
                try:
                    autocomplete_selectors = [
                        f'[data-test*="location-suggestion"]:contains("{location}")',
                        f'.autocomplete-suggestion:contains("{location}")',
                        f'[role="option"]:contains("{location}")',
                        '.autocomplete ul li',
                        '[data-test="location-suggestion"]'
                    ]
                    
                    for selector in autocomplete_selectors:
                        try:
                            # Wait for suggestions to load
                            suggestions = self.driver.find_elements(By.CSS_SELECTOR, selector.split(':contains')[0])
                            
                            if suggestions:
                                # Look for suggestion containing our location
                                for suggestion in suggestions:
                                    if location.lower() in suggestion.text.lower():
                                        logger.info(f"🎯 Clicking autocomplete suggestion: {suggestion.text}")
                                        suggestion.click()
                                        
                                        # Wait for auto-redirect
                                        logger.info("⏳ Waiting for auto-redirect...")
                                        time.sleep(4)
                                        
                                        # Check if we've been redirected to search results
                                        current_url = self.driver.current_url
                                        if 'SRCH_' in current_url or 'jobs' in current_url:
                                            logger.info("✅ Auto-redirected to search results!")
                                            break
                                        
                                break
                            
                        except Exception as e:
                            logger.debug(f"Autocomplete attempt failed: {str(e)}")
                            continue
                    
                except Exception as e:
                    logger.warning(f"⚠️ Autocomplete selection failed: {str(e)}")
            
            # If we're not on results page yet, try alternative approaches
            current_url = self.driver.current_url
            if 'SRCH_' not in current_url and 'jobs' not in current_url:
                logger.info("🔄 Trying alternative search approaches...")
                
                # Method 1: Press Enter on location field
                try:
                    if location_input:
                        from selenium.webdriver.common.keys import Keys
                        location_input.send_keys(Keys.RETURN)
                        logger.info("✅ Pressed Enter on location field")
                        time.sleep(3)
                except Exception as e:
                    logger.debug(f"Enter key method failed: {str(e)}")
                
                # Method 2: Try to click search button with JavaScript
                current_url = self.driver.current_url
                if 'SRCH_' not in current_url:
                    try:
                        search_button = self.driver.find_element(By.CSS_SELECTOR, '.SearchBar button, [type="submit"]')
                        # Use JavaScript click to avoid interception
                        self.driver.execute_script("arguments[0].click();", search_button)
                        logger.info("✅ Search button clicked with JavaScript")
                        time.sleep(3)
                    except Exception as e:
                        logger.debug(f"JavaScript click method failed: {str(e)}")
                
                # Method 3: Direct URL construction if we know the pattern
                current_url = self.driver.current_url
                if 'SRCH_' not in current_url:
                    try:
                        # Construct direct search URL (Glassdoor pattern)
                        keywords_encoded = keywords.replace(' ', '-')
                        location_encoded = location.lower().replace(' ', '-').replace(',', '')
                        
                        if 'mumbai' in location.lower():
                            direct_url = f"{self.base_url}/Job/mumbai-india-{keywords_encoded}-jobs-SRCH_IL.0,12_IC2851180_KO13,{13+len(keywords)}.htm"
                        elif 'bangalore' in location.lower():
                            direct_url = f"{self.base_url}/Job/bangalore-india-{keywords_encoded}-jobs-SRCH_IL.0,15_IC2850667_KO16,{16+len(keywords)}.htm"
                        elif 'delhi' in location.lower():
                            direct_url = f"{self.base_url}/Job/delhi-india-{keywords_encoded}-jobs-SRCH_IL.0,11_IC2861069_KO12,{12+len(keywords)}.htm"
                        else:
                            # Generic India search
                            direct_url = f"{self.base_url}/Job/india-{keywords_encoded}-jobs-SRCH_IL.0,5_IN115_KO6,{6+len(keywords)}.htm"
                        
                        logger.info(f"🌐 Navigating directly to: {direct_url}")
                        self.driver.get(direct_url)
                        time.sleep(3)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Direct URL construction failed: {str(e)}")
            
            # Verify we're on search results page
            current_url = self.driver.current_url
            if 'SRCH_' not in current_url and 'Job/' not in current_url:
                logger.error("❌ Failed to reach search results page")
                return []
            
            logger.info(f"📍 Successfully reached search results: {current_url}")
            
            # Extract jobs from search results
            all_jobs = []
            
            for page in range(1, max_pages + 1):
                logger.info(f"📄 Processing page {page}/{max_pages}")
                
                page_jobs = self._extract_jobs_from_current_page()
                all_jobs.extend(page_jobs)
                
                logger.info(f"✅ Found {len(page_jobs)} jobs on page {page}")
                
                # Check if there are more pages and if we haven't hit our limit
                if current_page >= max_pages:
                    logger.info(f"🔄 Reached maximum page limit ({max_pages} pages)")
                    break
                    
                if self._go_to_next_page():
                    current_page += 1
                    logger.info(f"📄 Moving to page {current_page}")
                    time.sleep(3)  # Wait for page to load
                else:
                    logger.info("📄 No more pages available")
                    break
            
            logger.info(f"🎉 Total jobs found: {len(all_jobs)}")

            #Remove duplicates before returning
            all_jobs = self._remove_duplicates(all_jobs)
            logger.info(f"🔄 After duplicate removal: {len(all_jobs)} unique jobs")
        
            return all_jobs
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return []
    
    def _extract_jobs_from_current_page(self) -> List[JobListing]:
        """Extract job listings from the current page with detailed information"""
        jobs = []
        
        try:
            # Wait for job listings to load
            time.sleep(2)
            
            # Get initial count of jobs on the page
            initial_job_count = self._count_jobs_on_page()
            logger.info(f"🔍 Found {initial_job_count} job listings on this page")
            
            # Increase to 15 jobs
            jobs_to_process = min(initial_job_count, 15)
            logger.info(f"🧪 Processing {jobs_to_process} jobs for testing")
            
            # Process jobs one by one
            for i in range(jobs_to_process):
                try:
                    logger.info(f"📋 Processing job {i+1}/{jobs_to_process}")
                    
                    # Re-find job containers each time (in case page refreshed)
                    job_containers = self._find_job_containers()
                    
                    if not job_containers or i >= len(job_containers):
                        logger.warning(f"⚠️ Job {i+1} not found, page may have changed")
                        break
                    
                    container = job_containers[i]
                    
                    # Extract job with details
                    job_info = self._extract_job_with_details(container, i)
                    
                    if job_info and job_info.title and job_info.title != "Not specified":
                        jobs.append(job_info)
                        logger.info(f"✅ Extracted: {job_info.title} at {job_info.company}")
                        if job_info.description:
                            logger.info(f"📝 Description length: {len(job_info.description)} characters")
                        else:
                            logger.warning("⚠️ No description extracted")
                    else:
                        logger.debug(f"⚠️ Skipped job {i+1} - insufficient data")
                    
                    # Small delay between job extractions
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing job {i+1}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from page: {str(e)}")
        
        return jobs
    
    def _count_jobs_on_page(self) -> int:
        """Count the number of job listings on the current page"""
        try:
            job_containers = self._find_job_containers()
            return len(job_containers)
        except:
            return 0
    
    def _find_job_containers(self) -> list:
        """Find job containers on the current page"""
        job_selectors = [
            '[data-test="jobListing"]',
            '.JobsList_jobListItem__wjTHv',
            '.react-job-listing',
            '.job-result',
            '[class*="JobResult"]',
            '.jobResult'
        ]
        
        job_containers = []
        for selector in job_selectors:
            try:
                job_containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if job_containers:
                    logger.debug(f"✅ Found {len(job_containers)} jobs using selector: {selector}")
                    break
            except Exception:
                continue
        
        if not job_containers:
            # Fallback: try to find any clickable job elements
            try:
                job_containers = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/job-listing/"]')
                if job_containers:
                    logger.debug(f"✅ Found {len(job_containers)} jobs using href fallback")
            except Exception:
                pass
        
        return job_containers
    
    def _extract_job_with_details(self, container, index: int) -> Optional[JobListing]:
        """Extract job details by clicking on the job and reading the right panel"""
        try:
            # First, try to extract basic info from the left panel
            basic_info = self._extract_basic_job_info(container)
            
            # Store current URL to return to search results
            search_results_url = self.driver.current_url
            
            # Try to click on the job to get detailed info
            detailed_info = {}
            navigation_succeeded = False
            
            try:
                # Find clickable element (could be the container itself or a link inside)
                clickable_element = None
                
                # Try different clickable elements
                click_selectors = [
                    'a[data-test="job-title"]',
                    'a[href*="/job-listing/"]',
                    '.jobTitle a',
                    'h3 a',
                    'a'
                ]
                
                for selector in click_selectors:
                    try:
                        clickable_element = container.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if not clickable_element:
                    # Try clicking the container itself
                    clickable_element = container
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_element)
                time.sleep(0.5)
                
                # Click the job
                try:
                    clickable_element.click()
                    logger.debug(f"✅ Clicked on job {index+1}")
                    navigation_succeeded = True
                except Exception:
                    # If direct click fails, use JavaScript
                    self.driver.execute_script("arguments[0].click();", clickable_element)
                    logger.debug(f"✅ JavaScript clicked on job {index+1}")
                    navigation_succeeded = True
                
                if navigation_succeeded:
                    # Wait for page change or right panel to load
                    time.sleep(3)
                    
                    # Check if we navigated to a new page or if details loaded in right panel
                    current_url = self.driver.current_url
                    
                    if current_url != search_results_url:
                        # We navigated to a dedicated job page
                        logger.debug(f"📄 Navigated to dedicated job page for job {index+1}")
                        
                        # Extract detailed info from dedicated page
                        detailed_info = self._extract_detailed_job_info_from_page()
                        
                        # Navigate back to search results
                        logger.debug(f"🔙 Returning to search results...")
                        self._return_to_search_results(search_results_url)
                        
                    else:
                        # Details loaded in right panel (same page)
                        logger.debug(f"📋 Details loaded in right panel for job {index+1}")
                        detailed_info = self._extract_detailed_job_info()
                
            except Exception as e:
                logger.debug(f"Could not click job {index+1}: {str(e)}")
                # Ensure we're still on the search results page
                if self.driver.current_url != search_results_url:
                    self._return_to_search_results(search_results_url)
            
            # Merge basic and detailed info
            return self._merge_job_info(basic_info, detailed_info)
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting job {index+1}: {str(e)}")
            return None
    
    def _return_to_search_results(self, search_results_url: str):
        """Return to search results page with multiple fallback methods"""
        try:
            # Method 1: Use browser back button
            self.driver.back()
            time.sleep(2)
            
            # Check if we're back on search results
            current_url = self.driver.current_url
            if 'SRCH_' in current_url or 'Job/' in current_url:
                logger.debug("✅ Successfully returned via back button")
                return
            
            # Method 2: Navigate directly to stored URL
            logger.debug(f"🔄 Back button failed, navigating directly to: {search_results_url}")
            self.driver.get(search_results_url)
            time.sleep(3)
            
            # Verify we're back
            current_url = self.driver.current_url
            if 'SRCH_' in current_url or 'Job/' in current_url:
                logger.debug("✅ Successfully returned via direct navigation")
                return
            
            # Method 3: If all else fails, log the issue
            logger.warning("⚠️ Failed to return to search results page")
            
        except Exception as e:
            logger.warning(f"⚠️ Error returning to search results: {str(e)}")
            try:
                # Last resort: navigate to the stored URL
                self.driver.get(search_results_url)
                time.sleep(3)
            except:
                pass
    
    def _extract_basic_job_info(self, container) -> Dict:
        """Extract basic job information from left panel container"""
        info = {}
        
        try:
            # Extract title
            title_selectors = [
                '[data-test="job-title"]', 
                'a[class*="jobTitle"]', 
                'h3 a', 
                '.jobTitle a',
                'a[href*="/job-listing/"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = container.find_element(By.CSS_SELECTOR, selector)
                    info['title'] = title_elem.text.strip()
                    info['application_url'] = title_elem.get_attribute('href') or ""
                    if info['title']:
                        break
                except:
                    continue
            
            # Extract company from left panel
            company_selectors = [
                '[data-test="employer-name"]',
                '.employer', 
                '[class*="company"]',
                '.companyName'
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = container.find_element(By.CSS_SELECTOR, selector)
                    info['company'] = company_elem.text.strip()
                    if info['company']:
                        break
                except:
                    continue
            
            # Extract location from left panel
            location_selectors = [
                '[data-test="job-location"]',
                '.location', 
                '[class*="location"]'
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = container.find_element(By.CSS_SELECTOR, selector)
                    info['location'] = location_elem.text.strip()
                    if info['location']:
                        break
                except:
                    continue
            
            # Extract salary from left panel
            salary_selectors = [
                '[data-test*="salary"]',
                '.salary', 
                '[class*="salary"]'
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = container.find_element(By.CSS_SELECTOR, selector)
                    salary_text = salary_elem.text.strip()
                    if salary_text and ('₹' in salary_text or '$' in salary_text or 'lakh' in salary_text.lower()):
                        info['salary'] = salary_text
                        break
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Error extracting basic info: {str(e)}")
        
        return info
    
    def _extract_detailed_job_info_from_page(self) -> Dict:
        """Extract detailed job information from a dedicated job page (if navigated to one)"""
        info = {}
        
        try:
            # Wait longer for page content to load
            logger.debug("⏳ Waiting for dedicated page content to load...")
            time.sleep(4)
            
            # On dedicated job pages, selectors might be different
            # Extract company name
            company_selectors = [
                '.employerName',
                '[data-test="employer-name"]',
                '.employer',
                'h1 + div a',  # Company often after job title
                '.companyHeader a',
                '[class*="employer"]',
                '[class*="company"]',
                '.company-name'
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    company_text = company_elem.text.strip()
                    if company_text and len(company_text) > 1 and company_text not in ['Jobs', 'Apply', 'Save']:
                        info['company'] = company_text
                        logger.debug(f"✅ Found company on dedicated page: {company_text}")
                        break
                except:
                    continue
            
            # Extract company rating
            rating_selectors = [
                '.rating',
                '[class*="rating"]',
                '.starRating',
                '[data-test*="rating"]',
                '.ratingNumber'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)★?', rating_text)
                    if rating_match:
                        info['company_rating'] = float(rating_match.group(1))
                        logger.debug(f"✅ Found rating on dedicated page: {info['company_rating']}")
                        break
                except:
                    continue
            
            # Enhanced job description extraction for dedicated pages
            logger.debug("🔍 Looking for job description on dedicated page...")
            desc_selectors = [
                # Primary selectors for dedicated pages
                '.jobDescriptionContent',
                '[data-test="jobDescription"]',
                '.jobDescription',
                '#JobDescription',
                '.jobDetailText',
                '.job-description-content',
                
                # Alternative selectors for dedicated pages
                '[class*="description"]',
                '.jobSummary',
                '.description',
                '.content',
                '.job-content',
                '.main-content',
                
                # Glassdoor specific for dedicated pages
                '.jobDescriptionWrapper',
                '.jobDesc',
                '[data-test="job-description"]',
                '.job-description-container',
                
                # Generic content selectors
                '.job-details',
                'div[class*="Job"][class*="Description"]',
                '.job-posting-description',
                
                # Fallback selectors
                'main',
                'article',
                '.content-wrapper'
            ]
            
            description_found = False
            for selector in desc_selectors:
                try:
                    desc_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for desc_elem in desc_elems:
                        description = desc_elem.text.strip()
                        # Check for substantial description (more than just title/header)
                        if description and len(description) > 100:  # Require at least 100 characters
                            # Remove common non-description text
                            if not any(phrase in description.lower() for phrase in ['navigation', 'menu', 'cookie', 'privacy policy']):
                                info['description'] = description[:3000]  # Longer for dedicated pages
                                logger.debug(f"✅ Found description on dedicated page: {len(description)} characters")
                                description_found = True
                                break
                    if description_found:
                        break
                except:
                    continue
            
            if not description_found:
                # Fallback: try to get the main content area
                logger.debug("🔄 Trying fallback description extraction on dedicated page...")
                try:
                    # Look for the main content area
                    main_content_selectors = ['main', 'article', '[role="main"]', '.main', '.content']
                    for selector in main_content_selectors:
                        try:
                            main_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            text = main_elem.text.strip()
                            if len(text) > 200:  # Substantial content
                                info['description'] = text[:3000]
                                logger.debug(f"✅ Found fallback description: {len(text)} characters")
                                description_found = True
                                break
                        except:
                            continue
                        if description_found:
                            break
                
                except Exception as e:
                    logger.debug(f"Fallback description extraction failed: {str(e)}")
            
            # Extract requirements/qualifications
            requirements = []
            req_selectors = [
                '.qualifications',
                '[class*="requirement"]',
                '[class*="qualification"]',
                '.jobRequirements',
                '#Qualifications',
                '.requirements',
                '.skills',
                '.job-requirements'
            ]
            
            for selector in req_selectors:
                try:
                    req_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    req_text = req_elem.text.strip()
                    if req_text and len(req_text) > 20:
                        # Split into list if it contains bullet points or line breaks
                        requirements = [req.strip() for req in re.split(r'[•\n]', req_text) if req.strip() and len(req.strip()) > 5]
                        logger.debug(f"✅ Found {len(requirements)} requirements on dedicated page")
                        break
                except:
                    continue
            
            info['requirements'] = requirements
            
            # Extract salary information
            salary_selectors = [
                '.salaryText',
                '[data-test*="salary"]',
                '[class*="salary"]',
                '.compensation',
                '.payRange',
                '.pay',
                '.wage'
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    salary_text = salary_elem.text.strip()
                    if salary_text and ('₹' in salary_text or '$' in salary_text or 'lakh' in salary_text.lower()):
                        info['salary'] = salary_text
                        logger.debug(f"✅ Found salary on dedicated page: {salary_text}")
                        break
                except:
                    continue
            
            # Extract location if available
            location_selectors = [
                '.location',
                '[data-test="job-location"]',
                '[class*="location"]',
                '.jobLocation'
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_elem.text.strip()
                    if location_text:
                        info['location'] = location_text
                        logger.debug(f"✅ Found location on dedicated page: {location_text}")
                        break
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Error extracting from dedicated page: {str(e)}")
        
        return info

    def _extract_detailed_job_info(self) -> Dict:
        """Extract detailed job information from the right panel"""
        info = {}
        
        try:
            # Wait longer for right panel content to load
            logger.debug("⏳ Waiting for detailed content to load...")
            time.sleep(2)
            
            # Extract company name from right panel (more reliable)
            company_selectors = [
                '.employerName',
                '[data-test="employer-name"]',
                '.employer',
                'h4 a',  # Company name is often in h4
                '[class*="employer"]',
                '.companyHeader a',
                '.company-name'
            ]
            
            for selector in company_selectors:
                try:
                    company_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in company_elems:
                        company_text = elem.text.strip()
                        if company_text and len(company_text) > 1 and company_text not in ['Jobs', 'Apply', 'Save']:
                            info['company'] = company_text
                            logger.debug(f"✅ Found company: {company_text}")
                            break
                    if 'company' in info:
                        break
                except:
                    continue
            
            # Extract company rating
            rating_selectors = [
                '.rating',
                '[class*="rating"]',
                '.starRating',
                '[data-test*="rating"]',
                '.ratingNumber'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'(\d+\.?\d*)★?', rating_text)
                    if rating_match:
                        info['company_rating'] = float(rating_match.group(1))
                        logger.debug(f"✅ Found rating: {info['company_rating']}")
                        break
                except:
                    continue
            
            # Enhanced job description extraction with "Show More" handling
            logger.debug("🔍 Looking for job description...")
            
            # First, try to click "Show More" button to expand description
            self._click_show_more_button()
            
            desc_selectors = [
                # Primary selectors for job description
                '.jobDescriptionContent',
                '[data-test="jobDescription"]',
                '.jobDescription',
                '#JobDescription',
                '.jobDetailText',
                '.job-description',
                
                # Alternative selectors
                '[class*="description"]',
                '.jobSummary',
                '.description',
                '.content',
                '.job-content',
                
                # Glassdoor specific selectors
                '.jobDescriptionWrapper',
                '.jobDesc',
                '[data-test="job-description"]',
                
                # Generic content selectors
                '.main-content',
                '.job-details',
                'div[class*="Job"][class*="Description"]'
            ]
            
            description_found = False
            for selector in desc_selectors:
                try:
                    desc_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for desc_elem in desc_elems:
                        description = desc_elem.text.strip()
                        # Check for substantial description (more than just title/header)
                        if description and len(description) > 100:  # Require at least 100 characters
                            info['description'] = description[:3000]  # Increased limit to 3000 chars
                            logger.debug(f"✅ Found description: {len(description)} characters")
                            description_found = True
                            break
                    if description_found:
                        break
                except:
                    continue
            
            # Extract requirements/qualifications
            requirements = []
            req_selectors = [
                '.qualifications',
                '[class*="requirement"]',
                '[class*="qualification"]',
                '.jobRequirements',
                '#Qualifications',
                '.requirements',
                '.skills',
                '.job-requirements'
            ]
            
            for selector in req_selectors:
                try:
                    req_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    req_text = req_elem.text.strip()
                    if req_text and len(req_text) > 20:  # Require substantial content
                        # Split into list if it contains bullet points or line breaks
                        requirements = [req.strip() for req in re.split(r'[•\n]', req_text) if req.strip() and len(req.strip()) > 5]
                        logger.debug(f"✅ Found {len(requirements)} requirements")
                        break
                except:
                    continue
            
            info['requirements'] = requirements
            
            # Look for salary information in detailed view
            salary_selectors = [
                '.salaryText',
                '[data-test*="salary"]',
                '[class*="salary"]',
                '.compensation',
                '.pay',
                '.wage'
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    salary_text = salary_elem.text.strip()
                    if salary_text and ('₹' in salary_text or '$' in salary_text or 'lakh' in salary_text.lower()):
                        info['salary'] = salary_text
                        logger.debug(f"✅ Found detailed salary: {salary_text}")
                        break
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Error extracting detailed info: {str(e)}")
        
        return info
    
    def _click_show_more_button(self):
        """Try to click 'Show More' button to expand job description"""
        show_more_selectors = [
            'button:contains("Show more")',
            'button:contains("Show More")',
            '[data-test="show-more"]',
            '.show-more-button',
            'button[class*="show"][class*="more"]',
            '.showMoreButton',
            '.readMoreButton',
            'a:contains("Show more")',
            'span:contains("Show more")'
        ]
        
        for selector in show_more_selectors:
            try:
                # Use JavaScript to find and click the button
                self.driver.execute_script(f"""
                    var buttons = document.querySelectorAll('button, a, span');
                    for (var i = 0; i < buttons.length; i++) {{
                        var text = buttons[i].textContent.toLowerCase().trim();
                        if (text.includes('show more') || text.includes('read more') || text.includes('see more')) {{
                            buttons[i].click();
                            break;
                        }}
                    }}
                """)
                
                logger.debug("🔍 Attempted to click Show More button")
                time.sleep(1)  # Wait for content to expand
                break
                
            except Exception as e:
                logger.debug(f"Show More click attempt failed: {str(e)}")
                continue
    
    def _merge_job_info(self, basic_info: Dict, detailed_info: Dict) -> JobListing:
        """Merge basic and detailed job information into a JobListing object"""
        
        # Prefer detailed info over basic info when available
        title = detailed_info.get('title') or basic_info.get('title', 'Not specified')
        company = detailed_info.get('company') or basic_info.get('company', 'Not specified')
        location = detailed_info.get('location') or basic_info.get('location', 'Not specified')
        salary = detailed_info.get('salary') or basic_info.get('salary')
        description = detailed_info.get('description', '')
        requirements = detailed_info.get('requirements', [])
        company_rating = detailed_info.get('company_rating')
        app_url = basic_info.get('application_url', '')
        
        # Analyze all text for additional information
        all_text = f"{title} {company} {description} {' '.join(requirements)}".lower()
        
        # Create job listing
        job = JobListing(
            title=title,
            company=company,
            location=location,
            salary=salary,
            description=description,
            requirements=requirements,
            benefits=[],  # Could be extracted similarly if needed
            job_type=self._determine_job_type(all_text),
            experience_level=self._determine_experience_level(all_text),
            technologies=self._extract_technologies(all_text),
            posted_date=datetime.now().strftime("%Y-%m-%d"),
            application_url=app_url,
            company_rating=company_rating,
            company_size=None,
            industry=None,
            remote_type=self._determine_remote_type(all_text)
        )
        
        return job
    
    def _go_to_next_page(self) -> bool:
        """Navigate to the next page of results"""
        try:
            next_button_selectors = [
                '[data-test="pagination-next"]',
                '.next',
                '[aria-label="Next"]',
                'button:contains("Next")'
            ]
            
            for selector in next_button_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Could not navigate to next page: {str(e)}")
            return False
    
    def _remove_duplicates(self, jobs: List[JobListing]) -> List[JobListing]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a key based on title and company (case-insensitive)
            key = f"{job.title.lower().strip()}_{job.company.lower().strip()}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
            else:
                logger.debug(f"🔄 Removed duplicate: {job.title} at {job.company}")
        
        return unique_jobs
    
    def _determine_job_type(self, text: str) -> str:
        """Determine job type from text content"""
        if any(word in text for word in ['intern', 'internship']):
            return 'internship'
        elif any(word in text for word in ['contract', 'contractor', 'freelance']):
            return 'contract'
        elif any(word in text for word in ['part time', 'part-time', 'parttime']):
            return 'part-time'
        else:
            return 'full-time'
    
    def _determine_experience_level(self, text: str) -> str:
        """Determine experience level from text content"""
        if any(word in text for word in ['entry', 'junior', 'graduate', 'fresh', 'new grad']):
            return 'entry'
        elif any(word in text for word in ['senior', 'lead', 'principal', 'staff', 'architect']):
            return 'senior'
        else:
            return 'mid'
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology keywords from text"""
        found_techs = []
        for tech in self.tech_keywords:
            if tech.lower() in text:
                found_techs.append(tech)
        return found_techs
    
    def _determine_remote_type(self, text: str) -> str:
        """Determine if job is remote, hybrid, or on-site"""
        if any(word in text for word in ['remote', 'work from home', 'distributed', 'virtual']):
            if any(word in text for word in ['hybrid', 'flexible', 'some onsite']):
                return 'hybrid'
            return 'remote'
        elif any(word in text for word in ['hybrid', 'flexible']):
            return 'hybrid'
        else:
            return 'on-site'
    
    def save_jobs_to_json(self, jobs: List[JobListing], filename: str = None):
        """Save jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"glassdoor_selenium_jobs_{timestamp}.json"
        
        jobs_data = []
        for job in jobs:
            job_dict = {
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'salary': job.salary,
                'description': job.description,
                'requirements': job.requirements,
                'benefits': job.benefits,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'technologies': job.technologies,
                'posted_date': job.posted_date,
                'application_url': job.application_url,
                'company_rating': job.company_rating,
                'company_size': job.company_size,
                'industry': job.industry,
                'remote_type': job.remote_type,
                'source': job.source
            }
            jobs_data.append(job_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(jobs)} jobs to {filename}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("🔚 Browser closed")

def test_selenium_scraper():
    """Test the Selenium-based Glassdoor scraper with two-step login"""
    logger.info("🧪 Testing Glassdoor Selenium scraper...")
    logger.info("📝 Note: Glassdoor uses a two-step login process:")
    logger.info("   1. Enter email → Continue to password page")
    logger.info("   2. Enter password → Complete login")
    
    # Initialize scraper
    scraper = GlassdoorSeleniumScraper(
        # Add your credentials here:
        email="laavanya.mishra094@nmims.edu.in",
        password="Laavanya0104",
        headless=False,  # Set to True to run in background
        use_india_site=True
    )
    
    try:
        # Login if credentials provided
        if scraper.email and scraper.password:
            logger.info("🔐 Starting two-step login process...")
            login_success = scraper.login()
            
            if login_success:
                logger.info("🎉 Login successful! Proceeding with job search...")
            else:
                logger.warning("⚠️ Login failed. Continuing without authentication...")
                logger.info("💡 Tips for login issues:")
                logger.info("   - Check your email and password")
                logger.info("   - Complete any CAPTCHA if prompted")
                logger.info("   - Check debug screenshots if saved")
        
        # Test searches
        test_searches = [
            {'keywords': 'python developer', 'location': 'Bangalore'},
            {'keywords': 'data scientist', 'location': 'Mumbai'}
        ]
        
        all_jobs = []
        
        for search in test_searches:
            logger.info(f"🔍 Testing: {search['keywords']} in {search['location']}")
            
            jobs = scraper.search_jobs(
                keywords=search['keywords'],
                location=search['location'],
                max_pages=1
            )
            
            all_jobs.extend(jobs)
            
            if jobs:
                logger.info(f"✅ Found {len(jobs)} jobs")
                sample_job = jobs[0]
                logger.info(f"📋 Sample: {sample_job.title} at {sample_job.company}")
                logger.info(f"   📍 {sample_job.location}")
                logger.info(f"   💰 {sample_job.salary or 'Not specified'}")
                logger.info(f"   🔧 Technologies: {', '.join(sample_job.technologies[:3])}")
            else:
                logger.warning("⚠️ No jobs found for this search")
            
            time.sleep(5)  # Delay between searches
        
        if all_jobs:
            scraper.save_jobs_to_json(all_jobs)
            logger.info(f"🎉 Total jobs found: {len(all_jobs)}")
        else:
            logger.warning("❌ No jobs found")
            logger.info("💡 Troubleshooting tips:")
            logger.info("   - Ensure you're logged in successfully")
            logger.info("   - Try different search terms")
            logger.info("   - Check if Glassdoor is accessible in your region")
    
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    test_selenium_scraper()