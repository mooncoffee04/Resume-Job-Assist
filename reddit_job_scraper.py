#!/usr/bin/env python3
"""
Reddit Job Scraper
Scrapes job posts from multiple subreddits using PRAW (Python Reddit API Wrapper)
"""

import praw
import os
import re
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditJobScraper:
    """Scrapes job posts from Reddit using PRAW"""
    
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = None
        self.setup_reddit_connection()
        
        # Target subreddits for job hunting
        self.job_subreddits = [
            'hiring',
            'remotework', 
            'RemotePython',
            'MachineLearningJobs',
            'BigDataJobs',
            'WebDeveloperJobs',
            'JavascriptJobs',
            'PythonJobs',
            'DataScienceJobs',
            'cscareerquestions',
            'internships',
            'EntryLevelJobs'
            'ProjectManagementJobs',
            'DevOpsJobs',
            'TechJobs',
            'StartupJobs'
        ]
        
        # Keywords that indicate hiring posts
        self.hiring_keywords = [
            '[hiring]', '[remote]', '[intern]', '[internship]',
            'looking for', 'seeking', 'hiring', 'position available', 
            'job opening', 'opportunity', 'developer needed', 'join our team',
            'we are hiring', 'apply now', 'full time', 'part time', 'contract'
        ]
        
        # Keywords for filtering relevant positions
        self.relevant_keywords = [
            'python', 'data science', 'machine learning', 'ai', 'artificial intelligence',
            'backend', 'frontend', 'full stack', 'web developer', 'software engineer',
            'data analyst', 'business analyst', 'intern', 'entry level', 'junior',
            'react', 'django', 'flask', 'javascript', 'sql', 'database'
        ]
    
    def setup_reddit_connection(self):
        """Setup Reddit API connection using PRAW"""
        try:
            # You'll need to set these environment variables
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("Reddit credentials not found in environment variables!")
                logger.info("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
                return
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent='JobSearchBot/1.0 by Leading-Version2317'
            )
            
            # Test connection
            logger.info(f"Connected to Reddit as: {self.reddit.user.me() if self.reddit.user.me() else 'Anonymous'}")
            logger.info("Reddit connection successful!")
            
        except Exception as e:
            logger.error(f"Failed to connect to Reddit: {str(e)}")
            self.reddit = None
    
    def is_hiring_post(self, title: str, content: str) -> bool:
        """Check if a post is a hiring/job post"""
        text = (title + " " + content).lower()
        
        return any(keyword in text for keyword in self.hiring_keywords)
    
    def is_relevant_job(self, title: str, content: str) -> bool:
        """Check if job is relevant to target skills/positions"""
        text = (title + " " + content).lower()
        
        return any(keyword in text for keyword in self.relevant_keywords)
    
    def extract_job_info(self, post) -> Dict:
        """Extract structured information from a Reddit post"""
        
        # Get post content
        title = post.title
        content = post.selftext if hasattr(post, 'selftext') else ""
        
        # Extract location (simple regex patterns)
        location_patterns = [
            r'\b([A-Z][a-z]+,\s*[A-Z]{2})\b',  # City, ST
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z]{2})\b',  # City Name, ST
            r'\bremote\b',
            r'\banywhere\b',
            r'\bworldwide\b'
        ]
        
        location = "Not specified"
        text_to_search = (title + " " + content).lower()
        
        for pattern in location_patterns:
            match = re.search(pattern, title + " " + content, re.IGNORECASE)
            if match:
                location = match.group(1) if match.group(1) else match.group(0)
                break
        
        # Determine if remote
        remote = any(word in text_to_search for word in ['remote', 'anywhere', 'worldwide'])
        
        # Extract experience level
        experience_level = "Not specified"
        if any(word in text_to_search for word in ['intern', 'internship', 'entry level', 'junior', 'new grad']):
            experience_level = "Entry Level"
        elif any(word in text_to_search for word in ['senior', 'lead', 'principal', '5+ years', '3+ years']):
            experience_level = "Senior"
        elif any(word in text_to_search for word in ['mid level', '2-3 years', 'experienced']):
            experience_level = "Mid Level"
        
        # Extract mentioned skills (simple keyword matching)
        skill_keywords = [
            'python', 'javascript', 'react', 'django', 'flask', 'node.js', 'sql',
            'machine learning', 'data science', 'ai', 'tensorflow', 'pytorch',
            'html', 'css', 'git', 'docker', 'kubernetes', 'aws', 'azure'
        ]
        
        skills_mentioned = []
        for skill in skill_keywords:
            if skill.lower() in text_to_search:
                skills_mentioned.append(skill.title())
        
        return {
            'title': title,
            'content': content,
            'location': location,
            'experience_level': experience_level,
            'remote': remote,
            'skills_mentioned': skills_mentioned,
            'url': f"https://reddit.com{post.permalink}",
            'created_date': datetime.fromtimestamp(post.created_utc),
            'score': post.score,
            'subreddit': str(post.subreddit)
        }
    
    def scrape_subreddit_jobs(self, subreddit_name: str, limit: int = 25) -> List[Dict]:
        """Scrape job posts from a specific subreddit"""
        
        if not self.reddit:
            logger.error("Reddit connection not established!")
            return []
        
        jobs = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            logger.info(f"Scraping r/{subreddit_name}...")
            
            # Get recent posts (combining hot and new)
            posts_sources = [
                subreddit.hot(limit=limit//2),
                subreddit.new(limit=limit//2)
            ]
            
            for posts in posts_sources:
                for post in posts:
                    try:
                        # Skip if too old (more than 30 days)
                        post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                        if post_age > timedelta(days=30):
                            continue
                        
                        # Check if it's a hiring post
                        if self.is_hiring_post(post.title, post.selftext):
                            # Check if it's relevant to our target jobs
                            if self.is_relevant_job(post.title, post.selftext):
                                job_info = self.extract_job_info(post)
                                jobs.append(job_info)
                                logger.info(f"Found job: {job_info['title'][:50]}...")
                        
                        # Small delay to be respectful to Reddit's servers
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.warning(f"Error processing post: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {str(e)}")
        
        return jobs
    
    def scrape_all_jobs(self, total_limit: int = 100) -> List[Dict]:
        """Scrape jobs from all target subreddits"""
        
        if not self.reddit:
            logger.error("Cannot scrape: Reddit connection not established!")
            return []
        
        all_jobs = []
        jobs_per_subreddit = max(10, total_limit // len(self.job_subreddits))
        
        logger.info(f"Starting to scrape {total_limit} jobs from {len(self.job_subreddits)} subreddits...")
        
        for subreddit_name in self.job_subreddits:
            try:
                jobs = self.scrape_subreddit_jobs(subreddit_name, jobs_per_subreddit)
                all_jobs.extend(jobs)
                
                logger.info(f"r/{subreddit_name}: Found {len(jobs)} jobs")
                
                # Stop if we've reached our limit
                if len(all_jobs) >= total_limit:
                    break
                    
                # Be respectful - wait between subreddits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error with r/{subreddit_name}: {str(e)}")
                continue
        
        # Remove duplicates based on title and URL
        unique_jobs = []
        seen_urls = set()
        seen_titles = set()
        
        for job in all_jobs:
            if job['url'] not in seen_urls and job['title'] not in seen_titles:
                unique_jobs.append(job)
                seen_urls.add(job['url'])
                seen_titles.add(job['title'])
        
        logger.info(f"Scraped {len(unique_jobs)} unique jobs total!")
        
        # Sort by creation date (newest first)
        unique_jobs.sort(key=lambda x: x['created_date'], reverse=True)
        
        return unique_jobs[:total_limit]

# Convenience function for easy import
def scrape_reddit_jobs(max_jobs: int = 100) -> List[Dict]:
    """
    Simple function to scrape Reddit jobs
    
    Args:
        max_jobs: Maximum number of jobs to scrape (default: 100)
    
    Returns:
        List of job dictionaries
    """
    scraper = RedditJobScraper()
    return scraper.scrape_all_jobs(max_jobs)

# Test function
if __name__ == "__main__":
    # Test the scraper
    print("Testing Reddit Job Scraper...")
    jobs = scrape_reddit_jobs(20)
    
    print(f"\nFound {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. {job['title']}")
        print(f"   Location: {job['location']}")
        print(f"   Experience: {job['experience_level']}")
        print(f"   Skills: {', '.join(job['skills_mentioned'][:3])}")
        print(f"   Subreddit: r/{job['subreddit']}")
        print()