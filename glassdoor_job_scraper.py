#!/usr/bin/env python3
"""
Enhanced Glassdoor Job Scraper with Selenium (Improved Version)
Features:
- Faster scraping with reduced wait times
- Full description extraction with "View More" button handling
- Deployment-ready for Streamlit Cloud
- Better error handling and robustness
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
import os

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
    """Enhanced Glassdoor scraper using Selenium WebDriver - Improved & Fast"""
    
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
        """Setup Chrome WebDriver with deployment-ready options (Fast & Optimized)"""
        try:
            chrome_options = Options()
            
            # Always run headless in deployment
            chrome_options.add_argument('--headless')
            
            # Essential arguments for deployment environments
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-tools')
            chrome_options.add_argument('--no-zygote')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Speed optimizations
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # Set binary location for deployment
            if os.path.exists('/usr/bin/chromium'):
                chrome_options.binary_location = '/usr/bin/chromium'
            elif os.path.exists('/usr/bin/chromium-browser'):
                chrome_options.binary_location = '/usr/bin/chromium-browser'
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Try different methods to initialize driver
            self.driver = None
            
            # Method 1: Use system chromedriver directly
            try:
                if os.path.exists('/usr/bin/chromedriver'):
                    service = Service('/usr/bin/chromedriver')
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("🌐 Using system ChromeDriver")
            except Exception as e1:
                logger.debug(f"System chromedriver failed: {e1}")
                
                # Method 2: Try webdriver-manager
                try:
                    from webdriver.manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("🌐 Using webdriver-manager")
                except Exception as e2:
                    raise Exception(f"All driver methods failed. Errors: {e1}, {e2}")
            
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Set faster timeouts for speed
                self.driver.implicitly_wait(5)
                self.wait = WebDriverWait(self.driver, 10)
                
                logger.info("🌟 Selenium WebDriver initialized successfully")
            else:
                raise Exception("Failed to initialize WebDriver")
            
        except Exception as e:
            logger.error(f"❌ WebDriver initialization failed: {str(e)}")
            raise

    def handle_verification_if_needed(self):
        """Handle any additional verification steps that might appear"""
        try:
            verification_indicators = [
                'captcha', 'verify', 'security', 'robot', 'human'
            ]
            
            page_source = self.driver.page_source.lower()
            
            if any(indicator in page_source for indicator in verification_indicators):
                logger.warning("⚠️ Verification step detected!")
                logger.info("🤖 Please complete any CAPTCHA or verification manually")
                logger.info("⏳ Waiting 30 seconds for manual completion...")
                time.sleep(30)
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
            time.sleep(2)  # Reduced wait time
            
            # STEP 1: Enter email
            logger.info("📧 Step 1: Entering email...")
            
            email_selectors = [
                '#userEmail', '[name="username"]', '[type="email"]', '#email',
                'input[placeholder*="email"]', '.EmailForm input'
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
            
            email_element.clear()
            time.sleep(0.5)  # Reduced wait
            email_element.send_keys(self.email)
            logger.info("✅ Email entered")
            
            # Find and click continue button
            email_continue_selectors = [
                '#emailButton', 'button[name="submit"]', '[type="submit"]',
                'button:contains("Continue")', 'button:contains("Next")', '.EmailForm button'
            ]
            
            email_continue_button = None
            for selector in email_continue_selectors:
                try:
                    email_continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if email_continue_button.is_enabled():
                        break
                except:
                    continue
            
            if not email_continue_button:
                logger.error("❌ Could not find email continue button")
                return False
            
            email_continue_button.click()
            logger.info("✅ Clicked email continue button")
            time.sleep(2)  # Reduced wait
            
            # STEP 2: Enter password
            logger.info("🔑 Step 2: Entering password...")
            
            password_selectors = [
                '#userPassword', '[name="password"]', '[type="password"]', '#password',
                'input[placeholder*="password"]', '.PasswordForm input[type="password"]'
            ]
            
            password_element = None
            for selector in password_selectors:
                try:
                    password_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not password_element:
                logger.error("❌ Could not find password input field")
                return False
            
            password_element.clear()
            time.sleep(0.5)
            password_element.send_keys(self.password)
            logger.info("✅ Password entered")
            
            # Find and click login button
            login_button_selectors = [
                '#passwordButton', 'button[name="submit"]', '[type="submit"]',
                'button:contains("Sign In")', 'button:contains("Login")', '.PasswordForm button'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_button.is_enabled():
                        break
                except:
                    continue
            
            if not login_button:
                logger.error("❌ Could not find login button")
                return False
            
            login_button.click()
            logger.info("✅ Clicked login button")
            time.sleep(3)  # Reduced wait
            
            # Check for verification
            self.handle_verification_if_needed()
            
            # Check if login was successful
            current_url = self.driver.current_url
            if 'login' not in current_url.lower():
                logger.info("🎉 Login successful!")
                return True
            else:
                logger.warning("⚠️ Login may have failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            return False

    def search_jobs(self, keywords: str, location: str = "", max_pages: int = 1) -> List[JobListing]:
        """Search for jobs on Glassdoor (Fast & Optimized)"""
        
        logger.info(f"🔍 Searching for: '{keywords}' in '{location}'")
        
        try:
            # Navigate to jobs page first
            self.driver.get(self.jobs_url)
            time.sleep(1.5)  # Reduced wait time
            
            # Try to search using the search form
            search_success = False
            
            try:
                # Find search inputs
                keyword_input = None
                location_input = None
                
                keyword_selectors = [
                    'input[placeholder*="job title"]', 'input[placeholder*="Job title"]',
                    'input[id*="keyword"]', 'input[name*="keyword"]',
                    '#searchBar-jobTitle', '.jobsearch input:first-child'
                ]
                
                for selector in keyword_selectors:
                    try:
                        keyword_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                location_selectors = [
                    'input[placeholder*="location"]', 'input[placeholder*="Location"]',
                    'input[id*="location"]', 'input[name*="location"]',
                    '#searchBar-location', '.jobsearch input:last-child'
                ]
                
                for selector in location_selectors:
                    try:
                        location_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if keyword_input and location_input:
                    keyword_input.clear()
                    time.sleep(0.5)
                    keyword_input.send_keys(keywords)
                    
                    location_input.clear()
                    time.sleep(0.5)
                    location_input.send_keys(location)
                    
                    # Find and click search button
                    search_button_selectors = [
                        'button[type="submit"]', 'button[data-test*="search"]',
                        '.searchButton', 'input[type="submit"]'
                    ]
                    
                    for selector in search_button_selectors:
                        try:
                            search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            search_button.click()
                            search_success = True
                            break
                        except:
                            continue
                    
                    if search_success:
                        logger.info("✅ Used search form successfully")
                        time.sleep(1.5)  # Reduced wait
                    
            except Exception as e:
                logger.debug(f"Search form method failed: {str(e)}")
            
            # Method 2: Direct URL construction if form search failed
            if not search_success:
                try:
                    logger.info("🌐 Trying direct URL construction...")
                    keywords_encoded = keywords.replace(' ', '-').lower()
                    
                    if self.use_india_site:
                        if 'mumbai' in location.lower():
                            direct_url = f"{self.base_url}/Job/mumbai-india-{keywords_encoded}-jobs-SRCH_IL.0,12_IC2851180_KO13,{13+len(keywords)}.htm"
                        elif 'bangalore' in location.lower():
                            direct_url = f"{self.base_url}/Job/bangalore-india-{keywords_encoded}-jobs-SRCH_IL.0,15_IC2850667_KO16,{16+len(keywords)}.htm"
                        elif 'delhi' in location.lower():
                            direct_url = f"{self.base_url}/Job/delhi-india-{keywords_encoded}-jobs-SRCH_IL.0,11_IC2861069_KO12,{12+len(keywords)}.htm"
                        else:
                            direct_url = f"{self.base_url}/Job/india-{keywords_encoded}-jobs-SRCH_IL.0,5_IN115_KO6,{6+len(keywords)}.htm"
                        
                        logger.info(f"🌐 Navigating directly to: {direct_url}")
                        self.driver.get(direct_url)
                        time.sleep(1.5)  # Reduced wait
                        
                except Exception as e:
                    logger.warning(f"⚠️ Direct URL construction failed: {str(e)}")
            
            # Verify we're on search results page
            current_url = self.driver.current_url
            if 'SRCH_' not in current_url and 'Job/' not in current_url:
                logger.error("❌ Failed to reach search results page")
                return []
            
            logger.info(f"🔍 Successfully reached search results: {current_url}")
            
            # Extract jobs from search results
            all_jobs = []
            
            for page in range(1, max_pages + 1):
                logger.info(f"📄 Processing page {page}/{max_pages}")
                
                page_jobs = self._extract_jobs_from_current_page()
                all_jobs.extend(page_jobs)
                
                logger.info(f"✅ Found {len(page_jobs)} jobs on page {page}")
                
                # Try to go to next page
                if page < max_pages:
                    if not self._go_to_next_page():
                        logger.info("📄 No more pages available")
                        break
                    time.sleep(1.5)  # Reduced wait
            
            logger.info(f"🎉 Total jobs found: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            logger.error(f"❌ Error during job search: {str(e)}")
            return []

    def _extract_jobs_from_current_page(self) -> List[JobListing]:
        """Extract job listings from current page (Fast & Optimized)"""
        
        jobs = []
        
        try:
            # Common selectors for job listings
            job_selectors = [
                '[data-test="job-listing"]', '.react-job-listing', '.jobContainer',
                '.job', '.JobsList_jobListItem', '[class*="job"]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        logger.debug(f"✅ Found job elements using selector: {selector}")
                        break
                except:
                    continue
            
            if not job_elements:
                logger.warning("⚠️ No job elements found on page")
                return jobs
            
            logger.info(f"📋 Found {len(job_elements)} job listings on page")
            
            for i, job_element in enumerate(job_elements[:15]):  # Limit for speed
                try:
                    job = self._extract_job_details_fast(job_element, i)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"⚠️ Failed to extract job {i}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from page: {str(e)}")
        
        return jobs

    def _extract_job_details_fast(self, job_element, index: int) -> Optional[JobListing]:
        """Extract details from a single job element (Fast & Enhanced)"""
        
        try:
            # Extract title
            title = "Job Title"
            title_selectors = [
                '[data-test="job-title"]', '.jobTitle', 'h2', 'h3',
                '[class*="title"]', 'a[data-test*="job-title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # Extract company
            company = "Company"
            company_selectors = [
                '[data-test="employer-name"]', '.companyName', '.employerName',
                '[class*="company"]', 'span[title]'
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    company = company_elem.text.strip()
                    if company:
                        break
                except:
                    continue
            
            # Extract location
            location = "Location"
            location_selectors = [
                '[data-test="job-location"]', '.location', '.jobLocation',
                '[class*="location"]'
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    location = location_elem.text.strip()
                    if location:
                        break
                except:
                    continue
            
            # Extract salary (if available)
            salary = None
            salary_selectors = [
                '[data-test="detailSalary"]', '.salary', '.salaryText',
                '[class*="salary"]'
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = job_element.find_element(By.CSS_SELECTOR, selector)
                    salary = salary_elem.text.strip()
                    if salary:
                        break
                except:
                    continue
            
            # Extract application URL
            app_url = ""
            try:
                link_elem = job_element.find_element(By.CSS_SELECTOR, 'a')
                app_url = link_elem.get_attribute('href')
                if app_url and not app_url.startswith('http'):
                    app_url = self.base_url + app_url
            except:
                pass
            
            # Get job description with "View More" handling
            description = "Job description not available"
            requirements = []
            company_rating = None
            
            try:
                # Click on the job to get more details
                clickable_elem = job_element.find_element(By.CSS_SELECTOR, 'a, [data-test="job-title"]')
                clickable_elem.click()
                time.sleep(1)  # Reduced wait time for speed
                
                # Extract description with "View More" button handling
                desc_selectors = [
                    '[data-test="jobDescriptionText"]', '.jobDescriptionContent',
                    '.desc', '.description', '[class*="description"]',
                    '.jobDescriptionWrapper'
                ]
                
                description_found = False
                for selector in desc_selectors:
                    try:
                        desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        # Look for "View More" or "Read full description" button
                        try:
                            view_more_selectors = [
                                'button:contains("View more")',
                                'button:contains("Read full description")', 
                                'button:contains("Show more")',
                                '[data-test="show-more"]',
                                '.showMoreButton',
                                'button[class*="showMore"]',
                                'button[class*="readMore"]',
                                '[class*="show-more"]',
                                '[class*="read-more"]'
                            ]
                            
                            for view_more_selector in view_more_selectors:
                                try:
                                    # Look for the button within or near the description element
                                    view_more_btn = None
                                    try:
                                        view_more_btn = desc_elem.find_element(By.CSS_SELECTOR, view_more_selector)
                                    except:
                                        # Try to find it in the whole page
                                        view_more_btn = self.driver.find_element(By.CSS_SELECTOR, view_more_selector)
                                    
                                    if view_more_btn and view_more_btn.is_displayed():
                                        logger.debug(f"🔍 Clicking 'View More' for full description")
                                        self.driver.execute_script("arguments[0].click();", view_more_btn)
                                        time.sleep(0.5)  # Brief wait for content to expand
                                        break
                                except:
                                    continue
                                    
                        except Exception as e:
                            logger.debug(f"No 'View More' button found: {e}")
                        
                        # Extract the (now potentially expanded) description
                        description = desc_elem.text.strip()
                        if len(description) > 50:  # Ensure we got substantial content
                            description_found = True
                            # Limit description length for performance
                            if len(description) > 3000:
                                description = description[:3000] + "..."
                            logger.debug(f"✅ Extracted description: {len(description)} characters")
                            break
                            
                    except Exception as e:
                        logger.debug(f"Description selector {selector} failed: {e}")
                        continue
                
                # If no description found, try alternative approach
                if not description_found:
                    try:
                        # Look for any large text block
                        all_text_elements = self.driver.find_elements(By.TAG_NAME, 'div')
                        largest_text = ""
                        for elem in all_text_elements[:10]:  # Limit for speed
                            try:
                                text = elem.text.strip()
                                if len(text) > len(largest_text) and len(text) > 100:
                                    if not any(word in text.lower() for word in ['navigation', 'menu', 'header', 'footer']):
                                        largest_text = text
                            except:
                                continue
                        
                        if largest_text:
                            description = largest_text[:2000]  # Reasonable limit
                            logger.debug(f"✅ Found fallback description: {len(description)} characters")
                    
                    except Exception as e:
                        logger.debug(f"Fallback description extraction failed: {e}")
                
                # Extract company rating (quick)
                rating_selectors = [
                    '[data-test="rating"]', '.rating', '.companyRating',
                    '[class*="rating"]'
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        rating_text = rating_elem.text.strip()
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            company_rating = float(rating_match.group(1))
                            break
                    except:
                        continue
                
            except Exception as e:
                logger.debug(f"Could not extract detailed info for job {index}: {str(e)}")
            
            # Create job listing
            all_text = f"{title} {company} {location} {description}".lower()
            
            job = JobListing(
                title=title,
                company=company,
                location=location,
                salary=salary,
                description=description,
                requirements=requirements,
                benefits=[],
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
            
        except Exception as e:
            logger.debug(f"Error extracting job details: {str(e)}")
            return None

    def _go_to_next_page(self) -> bool:
        """Navigate to the next page of results"""
        try:
            next_button_selectors = [
                '[data-test="pagination-next"]', '.next',
                '[aria-label="Next"]', 'button:contains("Next")'
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
            logger.info("📚 Browser closed")

def test_selenium_scraper():
    """Test the improved Glassdoor scraper"""
    logger.info("🧪 Testing Improved Glassdoor Selenium scraper...")
    
    # Initialize scraper
    scraper = GlassdoorSeleniumScraper(
        headless=True,  # Always headless for deployment
        use_india_site=True
    )
    
    try:
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
            
            time.sleep(2)  # Reduced delay between searches
        
        if all_jobs:
            scraper.save_jobs_to_json(all_jobs)
            logger.info(f"🎉 Total jobs found: {len(all_jobs)}")
        else:
            logger.warning("❌ No jobs found")
    
    except KeyboardInterrupt:
        logger.info("ℹ️ Test interrupted by user")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    test_selenium_scraper()