# backend/reddit_service/intelligent_reddit_scraper.py
import praw
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import re
from pathlib import Path
import os
from dotenv import load_dotenv

# Import our semantic matcher
try:
    from ..nlp_service.semantic_job_matcher import SemanticJobMatcher
    from ..neo4j_service.resume_storage import ResumeNeo4jStorage
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../nlp_service')
    sys.path.append('../neo4j_service')
    from semantic_job_matcher import SemanticJobMatcher
    from resume_storage import ResumeNeo4jStorage

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class IntelligentRedditJobScraper:
    """Smart Reddit job scraper with real-time semantic filtering"""
    
    def __init__(self, user_email: str = None, min_relevance_score: float = 0.25):
        """
        Initialize intelligent scraper
        
        Args:
            user_email: User's email to get profile context
            min_relevance_score: Minimum score to consider a job relevant (0.0-1.0)
        """
        self.user_email = user_email
        self.min_relevance_score = min_relevance_score
        
        # Initialize Reddit API
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = "IntelligentJobBot/1.0 by YourUsername"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials not found in environment variables")
        
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            logger.info("✅ Reddit API connection successful")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Reddit API: {e}")
            raise
        
        # Initialize semantic components
        self.semantic_matcher = SemanticJobMatcher()
        self.resume_storage = ResumeNeo4jStorage()
        
        # Cache user profile for efficiency
        self.user_profile = None
        self.user_profile_text = None
        
        if user_email:
            self._load_user_profile()
    
    def _load_user_profile(self):
        """Load and cache user profile"""
        try:
            self.user_profile = self.resume_storage.get_user_profile(self.user_email)
            if self.user_profile:
                self.user_profile_text = self.semantic_matcher._profile_to_text(self.user_profile)
                logger.info(f"✅ Loaded profile for {self.user_email}")
            else:
                logger.warning(f"❌ No profile found for {self.user_email}")
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
    
    def set_user_context(self, user_email: str):
        """Change user context for scraping"""
        self.user_email = user_email
        self._load_user_profile()
    
    def scrape_intelligent_jobs(self, 
                              search_query: str = "", 
                              subreddits: List[str] = None, 
                              limit_per_subreddit: int = 20) -> List[Dict]:
        """
        Intelligently scrape jobs based on user profile and search query
        
        Args:
            search_query: Natural language search (e.g. "AI healthcare internships")
            subreddits: List of subreddits to search
            limit_per_subreddit: Max posts per subreddit
            
        Returns:
            List of semantically filtered, relevant jobs
        """
        
        if not self.user_profile:
            logger.error("No user profile loaded. Set user context first.")
            return []
        
        # Default job-hunting subreddits
        if not subreddits:
            subreddits = [
                'forhire', 'hiring', 'remotework', 'jobs', 'internships',
                'MachineLearning', 'datascience', 'Python', 'webdev', 
                'cscareerquestions', 'ITCareerQuestions', 'digitalnomadJobs'
            ]
        
        # Enhance search with user context
        enhanced_search_context = self._build_search_context(search_query)
        
        logger.info(f"🔍 Intelligent scraping for: '{search_query}'")
        logger.info(f"🎯 User context: {enhanced_search_context[:100]}...")
        logger.info(f"📊 Min relevance score: {self.min_relevance_score}")
        
        all_relevant_jobs = []
        total_posts_scanned = 0
        
        for subreddit_name in subreddits:
            logger.info(f"🔎 Scanning r/{subreddit_name}...")
            
            try:
                subreddit_jobs = self._scrape_subreddit_intelligently(
                    subreddit_name, 
                    enhanced_search_context,
                    limit_per_subreddit
                )
                
                relevant_count = len(subreddit_jobs)
                all_relevant_jobs.extend(subreddit_jobs)
                
                logger.info(f"   ✅ Found {relevant_count} relevant jobs")
                
            except Exception as e:
                logger.error(f"   ❌ Error scraping r/{subreddit_name}: {e}")
                continue
        
        # Sort by relevance score
        all_relevant_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"🎉 Intelligent scraping complete!")
        logger.info(f"   📊 Total relevant jobs: {len(all_relevant_jobs)}")
        logger.info(f"   🔍 Posts scanned: {total_posts_scanned}")
        
        if all_relevant_jobs:
            logger.info(f"   🏆 Top score: {all_relevant_jobs[0]['relevance_score']:.3f}")
        
        return all_relevant_jobs
    
    def _build_search_context(self, search_query: str) -> str:
        """Build enhanced search context from user profile + query"""
        
        if not self.user_profile_text:
            return search_query
        
        if search_query:
            return f"{self.user_profile_text}. Looking for: {search_query}"
        else:
            return self.user_profile_text
    
    def _scrape_subreddit_intelligently(self, 
                                       subreddit_name: str, 
                                       search_context: str,
                                       limit: int) -> List[Dict]:
        """Scrape a single subreddit with semantic filtering"""
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            relevant_jobs = []
            posts_checked = 0
            
            # Get recent posts
            for post in subreddit.new(limit=limit * 2):  # Check more posts to find relevant ones
                posts_checked += 1
                
                # Skip old posts (older than 30 days)
                post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                if post_age > timedelta(days=30):
                    continue
                
                # Quick pre-filter: Is this likely a job post?
                if not self._is_likely_job_post(post.title, post.selftext):
                    continue
                
                # Extract job information
                job_data = self._extract_job_info(post)
                if not job_data:
                    continue
                
                # Semantic relevance check
                relevance_score = self._calculate_relevance(job_data, search_context)
                
                # Only keep if above minimum threshold
                if relevance_score >= self.min_relevance_score:
                    job_data['relevance_score'] = relevance_score
                    job_data['matched_for_user'] = self.user_email
                    job_data['search_context'] = search_context[:200]  # Store partial context
                    relevant_jobs.append(job_data)
                
                # Early exit if we have enough good matches
                if len(relevant_jobs) >= limit:
                    break
            
            return relevant_jobs
            
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")
            return []
    
    def _is_likely_job_post(self, title: str, content: str) -> bool:
        """Quick heuristic to identify potential job posts"""
        
        # Enhanced job indicators
        job_keywords = [
            # Direct job terms
            'hiring', 'job', 'position', 'role', 'opportunity', 'opening',
            'intern', 'internship', 'graduate', 'entry level',
            
            # Action words
            'looking for', 'seeking', 'need', 'wanted', 'apply',
            'join our team', 'we are hiring', 'come work',
            
            # Job types
            'developer', 'engineer', 'analyst', 'scientist', 'manager',
            'designer', 'consultant', 'specialist', 'coordinator',
            
            # Work arrangements
            'remote', 'freelance', 'contract', 'full-time', 'part-time',
            'work from home', 'flexible', 'startup'
        ]
        
        # Combine title and content
        text = (title + ' ' + content).lower()
        
        # Count job keyword matches
        job_keyword_count = sum(1 for keyword in job_keywords if keyword in text)
        
        # Check for salary/compensation mentions
        salary_patterns = [
            r'\$\d+k?', r'\$\d+,\d+', r'\d+k\s*(per|/)\s*(year|month|hour)',
            r'salary', r'compensation', r'pay', r'wage', r'benefits'
        ]
        has_salary = any(re.search(pattern, text, re.IGNORECASE) for pattern in salary_patterns)
        
        # Check for application instructions
        application_indicators = [
            'apply', 'send resume', 'cv', 'portfolio', 'contact', 'email',
            'dm me', 'message me', 'interested candidates'
        ]
        has_application_info = any(indicator in text for indicator in application_indicators)
        
        # Scoring: need multiple indicators for higher confidence
        score = 0
        if job_keyword_count >= 2:
            score += 2
        elif job_keyword_count >= 1:
            score += 1
        
        if has_salary:
            score += 1
        
        if has_application_info:
            score += 1
        
        # Title patterns (jobs often have structured titles)
        title_patterns = [
            r'\[.*hire.*\]', r'\[.*hiring.*\]', r'\[.*job.*\]',
            r'hiring:', r'job:', r'position:', r'role:'
        ]
        
        if any(re.search(pattern, title, re.IGNORECASE) for pattern in title_patterns):
            score += 2
        
        return score >= 2  # Need at least 2 points to be considered a job post
    
    def _extract_job_info(self, post) -> Optional[Dict]:
        """Extract structured job information from Reddit post"""
        
        try:
            # Basic post information
            job_data = {
                'id': post.id,
                'title': post.title,
                'content': post.selftext,
                'url': f"https://reddit.com{post.permalink}",
                'subreddit': str(post.subreddit),
                'author': str(post.author) if post.author else '[deleted]',
                'created_utc': post.created_utc,
                'score': post.score,
                'num_comments': post.num_comments,
                'scraped_at': datetime.now().isoformat(),
                'source': 'reddit_intelligent'
            }
            
            # Enhanced information extraction
            text = (post.title + ' ' + post.selftext).lower()
            
            # Extract experience level with better logic
            job_data['experience_level'] = self._extract_experience_level(text)
            
            # Extract location with enhanced patterns
            job_data['location'] = self._extract_location(text)
            
            # Enhanced remote work detection
            job_data['remote'] = self._is_remote_job(text)
            
            # Enhanced skills extraction
            job_data['skills_mentioned'] = self._extract_skills(text)
            
            # Extract salary information
            job_data['salary_info'] = self._extract_salary(text)
            
            # Extract job type (internship, full-time, etc.)
            job_data['job_type'] = self._extract_job_type(text)
            
            # Extract company size hints
            job_data['company_type'] = self._extract_company_type(text)
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting job info: {e}")
            return None
    
    def _calculate_relevance(self, job_data: Dict, search_context: str) -> float:
        """Calculate how relevant this job is to the user's profile and search"""
        
        if not self.semantic_matcher.model:
            # Fallback to keyword matching
            return self._calculate_keyword_relevance(job_data, search_context)
        
        try:
            # Convert job to text representation
            job_text = self.semantic_matcher._job_to_text(job_data)
            
            # Calculate semantic similarity
            similarity = self.semantic_matcher._calculate_semantic_similarity(search_context, job_text)
            
            # Add context-aware bonuses
            bonus = self._calculate_context_bonus(job_data, self.user_profile)
            
            return min(similarity + bonus, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.0
    
    def _calculate_keyword_relevance(self, job_data: Dict, search_context: str) -> float:
        """Fallback keyword-based relevance calculation"""
        
        job_text = f"{job_data['title']} {job_data['content']}"
        
        # Simple keyword overlap
        context_words = set(search_context.lower().split())
        job_words = set(job_text.lower().split())
        
        # Remove stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        context_words -= stop_words
        job_words -= stop_words
        
        # Calculate overlap
        intersection = len(context_words & job_words)
        union = len(context_words | job_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_context_bonus(self, job_data: Dict, user_profile: Dict) -> float:
        """Calculate bonus score based on job-profile alignment"""
        
        bonus = 0.0
        
        # Experience level alignment
        user_level = user_profile.get('experience_level', 'entry')
        job_level = job_data.get('experience_level', 'entry')
        
        if user_level == job_level:
            bonus += 0.05  # Small bonus for experience match
        
        # Remote work preference (assume students prefer remote)
        if job_data.get('remote', False) and user_level == 'entry':
            bonus += 0.03
        
        # Skills alignment
        user_skills = {skill['skill'].lower() for skill in user_profile.get('skills', [])}
        job_skills = {skill.lower() for skill in job_data.get('skills_mentioned', [])}
        
        skill_overlap = len(user_skills & job_skills)
        if skill_overlap > 0:
            bonus += min(skill_overlap * 0.05, 0.15)  # Up to 0.15 bonus
        
        # Domain expertise alignment
        user_domains = {domain['domain'].lower() for domain in user_profile.get('domains', [])}
        job_text = (job_data['title'] + ' ' + job_data['content']).lower()
        
        domain_matches = sum(1 for domain in user_domains if domain in job_text)
        if domain_matches > 0:
            bonus += min(domain_matches * 0.08, 0.16)  # Up to 0.16 bonus
        
        return min(bonus, 0.3)  # Cap total bonus at 0.3
    
    def _extract_experience_level(self, text: str) -> str:
        """Enhanced experience level extraction"""
        
        entry_indicators = [
            'entry level', 'entry-level', 'junior', 'intern', 'internship',
            'new grad', 'new graduate', 'fresh graduate', 'recent graduate',
            '0-1 year', '0-2 years', 'no experience', 'student'
        ]
        
        mid_indicators = [
            'mid level', 'mid-level', 'experienced', '2-5 years', '3-7 years',
            'intermediate', 'associate', 'ii', 'level 2'
        ]
        
        senior_indicators = [
            'senior', 'principal', 'staff', 'lead', 'manager', 'director',
            '5+ years', '7+ years', '10+ years', 'expert', 'architect'
        ]
        
        # Check in order of specificity
        for indicator in senior_indicators:
            if indicator in text:
                return 'senior'
        
        for indicator in mid_indicators:
            if indicator in text:
                return 'mid'
        
        for indicator in entry_indicators:
            if indicator in text:
                return 'entry'
        
        return 'entry'  # Default assumption
    
    def _extract_location(self, text: str) -> str:
        """Enhanced location extraction"""
        
        location_patterns = [
            # Major US cities
            r'(new york|nyc|ny|manhattan)', r'(san francisco|sf|bay area)',
            r'(los angeles|la|california|ca)', r'(chicago|chi|illinois|il)',
            r'(seattle|washington|wa)', r'(boston|massachusetts|ma)',
            r'(austin|texas|tx)', r'(denver|colorado|co)',
            
            # Countries
            r'(usa|united states|america)', r'(canada|toronto|vancouver|montreal)',
            r'(uk|united kingdom|london|england)', r'(germany|berlin|munich)',
            r'(australia|sydney|melbourne)', r'(india|bangalore|mumbai|delhi)',
            
            # Remote indicators
            r'(remote|anywhere|distributed|work from home|wfh)',
            r'(global|worldwide|international)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return 'Not specified'
    
    def _is_remote_job(self, text: str) -> bool:
        """Enhanced remote work detection"""
        
        remote_keywords = [
            'remote', 'distributed', 'anywhere', 'wfh', 'work from home',
            'virtual', 'online', 'telecommute', 'home office', 'location independent'
        ]
        
        return any(keyword in text for keyword in remote_keywords)
    
    def _extract_skills(self, text: str) -> List[str]:
        """Enhanced technical skills extraction"""
        
        # Comprehensive skill database
        skills = {
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            
            # Web technologies
            'react', 'angular', 'vue', 'node.js', 'html', 'css', 'bootstrap',
            'jquery', 'webpack', 'babel',
            
            # Data & ML
            'sql', 'nosql', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'keras',
            'scikit-learn', 'machine learning', 'deep learning', 'ai', 'nlp',
            'computer vision', 'data science', 'statistics', 'tableau', 'powerbi',
            
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'neo4j',
            'cassandra', 'dynamodb',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'terraform', 'ansible', 'linux', 'bash',
            
            # Frameworks
            'django', 'flask', 'fastapi', 'spring', 'express', 'rails',
            'streamlit', 'gradio',
            
            # Other tools
            'excel', 'jira', 'confluence', 'slack', 'figma', 'adobe'
        }
        
        found_skills = []
        for skill in skills:
            if skill in text:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_salary(self, text: str) -> Optional[str]:
        """Enhanced salary extraction"""
        
        salary_patterns = [
            r'\$(\d+)k?-?\$?(\d+)k?\s*(per|/)?\s*(year|annual|annually)',
            r'\$(\d+,?\d+)\s*-?\s*\$?(\d+,?\d+)?\s*(per|/)?\s*(year|annual|annually)',
            r'(\d+)k?\s*-\s*(\d+)k?\s*(usd|dollars?|salary)',
            r'(\d+)\s*-\s*(\d+)\s*(per hour|/hour|hourly)',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_job_type(self, text: str) -> str:
        """Extract job type (internship, full-time, etc.)"""
        
        if any(term in text for term in ['intern', 'internship']):
            return 'internship'
        elif any(term in text for term in ['full-time', 'full time', 'permanent']):
            return 'full-time'
        elif any(term in text for term in ['part-time', 'part time']):
            return 'part-time'
        elif any(term in text for term in ['contract', 'freelance', 'consultant']):
            return 'contract'
        else:
            return 'not-specified'
    
    def _extract_company_type(self, text: str) -> str:
        """Extract company type/size hints"""
        
        if any(term in text for term in ['startup', 'early stage', 'seed']):
            return 'startup'
        elif any(term in text for term in ['enterprise', 'fortune', 'multinational']):
            return 'enterprise'
        elif any(term in text for term in ['agency', 'consultancy', 'consulting']):
            return 'agency'
        else:
            return 'not-specified'

# Convenience functions
def create_intelligent_scraper(user_email: str, min_relevance: float = 0.25) -> IntelligentRedditJobScraper:
    """Create an intelligent scraper for a specific user"""
    return IntelligentRedditJobScraper(user_email, min_relevance)

def scrape_jobs_for_user(user_email: str, 
                        search_query: str = "",
                        subreddits: List[str] = None,
                        min_relevance: float = 0.25,
                        limit_per_subreddit: int = 20) -> List[Dict]:
    """Convenience function to scrape jobs for a user"""
    
    scraper = IntelligentRedditJobScraper(user_email, min_relevance)
    return scraper.scrape_intelligent_jobs(search_query, subreddits, limit_per_subreddit)

if __name__ == "__main__":
    # Test the intelligent scraper
    print("🤖 Testing Intelligent Reddit Job Scraper")
    print("=" * 60)
    
    # Test with different user profiles
    test_cases = [
        {
            'user': 'laavanya.mishra@nmims.edu',
            'query': 'healthcare AI internship data science',
            'description': 'Healthcare AI + Data Science student'
        },
        {
            'user': 'test.frontend@example.com',  # Would need a different profile
            'query': 'frontend react developer intern',
            'description': 'Frontend developer looking for React roles'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Test Case: {test_case['description']}")
        print(f"   Query: '{test_case['query']}'")
        print("-" * 40)
        
        try:
            scraper = create_intelligent_scraper(test_case['user'], min_relevance=0.2)
            
            if scraper.user_profile:
                jobs = scraper.scrape_intelligent_jobs(
                    search_query=test_case['query'],
                    subreddits=['forhire', 'hiring', 'datascience'],  # Limited for testing
                    limit_per_subreddit=5
                )
                
                print(f"   ✅ Found {len(jobs)} relevant jobs")
                
                for i, job in enumerate(jobs[:2], 1):  # Show top 2
                    print(f"\n   {i}. {job['title']}")
                    print(f"      Score: {job['relevance_score']:.3f}")
                    print(f"      Subreddit: r/{job['subreddit']}")
                    print(f"      Skills: {', '.join(job['skills_mentioned'][:3])}")
            else:
                print(f"   ❌ No profile found for {test_case['user']}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n✅ Intelligent scraper test completed!")