#!/usr/bin/env python3
"""
NLP-Powered Job Discovery System
Uses semantic similarity, named entity recognition, and transformer models
for intelligent job matching and discovery
"""

import praw
import os
import re
import time
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# NLP Libraries
from sentence_transformers import SentenceTransformer
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure NLTK data is downloaded
nltk.download('punkt_tab')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPJobDiscoverySystem:
    """Advanced NLP-based job discovery and matching system"""
    
    def __init__(self):
        """Initialize the NLP system with pre-trained models"""
        self.reddit = None
        
        # Subreddits for job hunting
        self.job_subreddits = [
            'forhire', 'remotework', 'RemotePython', 'MachineLearningJobs',
            'BigDataJobs', 'WebDeveloperJobs', 'JavascriptJobs', 'PythonJobs',
            'DataScienceJobs', 'cscareerquestions', 'internships', 'EntryLevelJobs',
            'freelance', 'startups', 'programming', 'webdev'
        ]
        
        # Job-related embeddings for semantic matching
        self.job_intent_patterns = [
            "hiring software developer",
            "looking for programmer", 
            "seeking data scientist",
            "job opening available",
            "freelance opportunity",
            "internship position",
            "remote work opportunity",
            "full time employment",
            "part time job",
            "contract work"
        ]
        
        self.setup_reddit_connection()
        self.setup_nlp_models()
        
    def setup_reddit_connection(self):
        """Setup Reddit API connection"""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("Reddit credentials not found!")
                return
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent='NLPJobBot/2.0 by ResumeIntelligenceAI'
            )
            
            logger.info("✅ Reddit connection established!")
            
        except Exception as e:
            logger.error(f"❌ Reddit connection failed: {str(e)}")
            self.reddit = None
    
    def setup_nlp_models(self):
        """Initialize NLP models and pipelines"""
        try:
            logger.info("🧠 Loading NLP models...")
            
            # 1. Sentence Transformer for semantic similarity
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence Transformer loaded")
            
            # 2. SpaCy for Named Entity Recognition
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.warning("⚠️ SpaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
            
            # 3. Classification pipeline for job detection
            self.job_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("✅ Job classifier loaded")
            
            # 4. Text preprocessing tools
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
            
            # 5. Pre-compute job intent embeddings
            self.job_intent_embeddings = self.sentence_model.encode(self.job_intent_patterns)
            logger.info("✅ Job intent embeddings computed")
            
            logger.info("🎉 All NLP models loaded successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error loading NLP models: {str(e)}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Tokenize and lemmatize
        tokens = word_tokenize(text)
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token.isalnum()]
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def is_job_post_semantic(self, title: str, content: str) -> Tuple[bool, float]:
        """Use semantic similarity to detect job posts"""
        
        # Combine title and content
        full_text = f"{title} {content}"
        processed_text = self.preprocess_text(full_text)
        
        if not processed_text:
            return False, 0.0
        
        # Get embedding for the post
        post_embedding = self.sentence_model.encode([processed_text])
        
        # Calculate similarity with job intent patterns
        similarities = cosine_similarity(post_embedding, self.job_intent_embeddings)[0]
        max_similarity = np.max(similarities)
        
        # Use dynamic threshold based on text length and content
        if len(processed_text.split()) < 10:
            threshold = 0.4  # Higher threshold for short posts
        else:
            threshold = 0.3  # Lower threshold for longer posts
        
        is_job = max_similarity > threshold
        
        return is_job, float(max_similarity)
    
    def classify_job_type(self, title: str, content: str) -> Dict:
        """Classify job posts using zero-shot classification"""
        
        full_text = f"{title} {content}"
        
        # Job type categories
        job_categories = [
            "software development",
            "data science", 
            "machine learning",
            "web development",
            "mobile development",
            "devops engineering",
            "product management",
            "design",
            "marketing",
            "freelance work",
            "internship",
            "contract work"
        ]
        
        # Experience level categories
        experience_levels = [
            "entry level",
            "junior level", 
            "mid level",
            "senior level",
            "lead level"
        ]
        
        # Work arrangement categories
        work_types = [
            "remote work",
            "on-site work",
            "hybrid work"
        ]
        
        try:
            # Classify job type
            job_type_result = self.job_classifier(full_text, job_categories)
            top_job_type = job_type_result['labels'][0]
            job_type_confidence = job_type_result['scores'][0]
            
            # Classify experience level
            exp_result = self.job_classifier(full_text, experience_levels)
            experience_level = exp_result['labels'][0]
            exp_confidence = exp_result['scores'][0]
            
            # Classify work type
            work_result = self.job_classifier(full_text, work_types)
            work_type = work_result['labels'][0]
            work_confidence = work_result['scores'][0]
            
            return {
                'job_type': top_job_type,
                'job_type_confidence': job_type_confidence,
                'experience_level': experience_level.title(),
                'experience_confidence': exp_confidence,
                'work_arrangement': work_type,
                'work_confidence': work_confidence
            }
            
        except Exception as e:
            logger.warning(f"Classification failed: {str(e)}")
            return {
                'job_type': 'unknown',
                'job_type_confidence': 0.0,
                'experience_level': 'Not specified',
                'experience_confidence': 0.0,
                'work_arrangement': 'unknown',
                'work_confidence': 0.0
            }
    
    def extract_entities(self, text: str) -> Dict:
        """Extract named entities from job posts"""
        
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        
        entities = {
            'organizations': [],
            'locations': [],
            'technologies': [],
            'money': [],
            'dates': []
        }
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities['organizations'].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities['locations'].append(ent.text)
            elif ent.label_ == "MONEY":
                entities['money'].append(ent.text)
            elif ent.label_ == "DATE":
                entities['dates'].append(ent.text)
        
        # Extract technology keywords using custom patterns
        tech_patterns = [
            r'\b(python|javascript|react|angular|vue|node\.?js|django|flask|fastapi)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|github)\b',
            r'\b(machine learning|deep learning|tensorflow|pytorch|scikit-learn)\b',
            r'\b(html|css|typescript|java|c\+\+|go|rust|scala)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text.lower())
            entities['technologies'].extend(matches)
        
        # Remove duplicates and clean up
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def calculate_semantic_match(self, query: str, job_text: str) -> float:
        """Calculate semantic similarity between user query and job post"""
        
        # Preprocess both texts
        processed_query = self.preprocess_text(query)
        processed_job = self.preprocess_text(job_text)
        
        if not processed_query or not processed_job:
            return 0.0
        
        # Get embeddings
        embeddings = self.sentence_model.encode([processed_query, processed_job])
        
        # Calculate cosine similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        return float(similarity)
    
    def analyze_job_post(self, post) -> Optional[Dict]:
        """Comprehensive NLP analysis of a job post"""
        
        try:
            title = post.title
            content = post.selftext if hasattr(post, 'selftext') else ""
            full_text = f"{title} {content}"
            
            # Step 1: Check if it's a job post using semantic analysis
            is_job, job_confidence = self.is_job_post_semantic(title, content)
            
            if not is_job:
                return None
            
            # Step 2: Classify the job
            classification = self.classify_job_type(title, content)
            
            # Step 3: Extract entities
            entities = self.extract_entities(full_text)
            
            # Step 4: Determine location and remote status
            locations = entities.get('locations', [])
            location = locations[0] if locations else "Not specified"
            
            remote_indicators = ['remote', 'anywhere', 'worldwide', 'distributed']
            is_remote = (classification.get('work_arrangement', '').lower() == 'remote work' or
                        any(indicator in full_text.lower() for indicator in remote_indicators))
            
            # Step 5: Extract salary information
            salary_info = entities.get('money', [])
            salary = salary_info[0] if salary_info else None
            
            # Step 6: Build the result
            result = {
                'title': title,
                'content': content,
                'url': f"https://reddit.com{post.permalink}",
                'subreddit': str(post.subreddit),
                'created_date': datetime.fromtimestamp(post.created_utc),
                'score': post.score,
                
                # NLP Analysis Results
                'job_confidence': job_confidence,
                'job_type': classification.get('job_type', 'unknown'),
                'job_type_confidence': classification.get('job_type_confidence', 0.0),
                'experience_level': classification.get('experience_level', 'Not specified'),
                'experience_confidence': classification.get('experience_confidence', 0.0),
                'work_arrangement': classification.get('work_arrangement', 'unknown'),
                
                # Extracted Information
                'location': location,
                'remote': is_remote,
                'salary': salary,
                'organizations': entities.get('organizations', []),
                'technologies': entities.get('technologies', []),
                'skills_mentioned': entities.get('technologies', []),  # For compatibility
                
                # Metadata
                'analysis_timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Error analyzing post: {str(e)}")
            return None
    
    def scrape_jobs_with_nlp(self, max_jobs: int = 100, user_query: str = "") -> List[Dict]:
        """Scrape and analyze jobs using NLP"""
        
        if not self.reddit:
            logger.error("Reddit connection not available!")
            return []
        
        all_jobs = []
        jobs_per_subreddit = max(5, max_jobs // len(self.job_subreddits))
        
        logger.info(f"🚀 Starting NLP-powered job discovery for {max_jobs} jobs...")
        
        for subreddit_name in self.job_subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                logger.info(f"🔍 Analyzing r/{subreddit_name}...")
                
                # Get posts from hot and new
                posts = list(subreddit.hot(limit=jobs_per_subreddit//2)) + list(subreddit.new(limit=jobs_per_subreddit//2))
                
                for post in posts:
                    # Skip old posts
                    post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                    if post_age > timedelta(days=30):
                        continue
                    
                    # Analyze with NLP
                    job_analysis = self.analyze_job_post(post)
                    
                    if job_analysis:
                        # Add semantic matching score if user query provided
                        if user_query:
                            match_score = self.calculate_semantic_match(
                                user_query, 
                                f"{job_analysis['title']} {job_analysis['content']}"
                            )
                            job_analysis['semantic_match_score'] = match_score
                        
                        all_jobs.append(job_analysis)
                        logger.info(f"✅ Found: {job_analysis['title'][:50]}... (confidence: {job_analysis['job_confidence']:.2f})")
                    
                    if len(all_jobs) >= max_jobs:
                        break
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error with r/{subreddit_name}: {str(e)}")
                continue
            
            if len(all_jobs) >= max_jobs:
                break
        
        # Remove duplicates and sort
        unique_jobs = self.remove_duplicates(all_jobs)
        
        # Sort by semantic match score if query provided, otherwise by job confidence
        if user_query:
            unique_jobs.sort(key=lambda x: x.get('semantic_match_score', 0), reverse=True)
        else:
            unique_jobs.sort(key=lambda x: x.get('job_confidence', 0), reverse=True)
        
        logger.info(f"🎉 Found {len(unique_jobs)} unique, high-quality job posts!")
        return unique_jobs[:max_jobs]
    
    def remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs using semantic similarity"""
        
        if len(jobs) <= 1:
            return jobs
        
        unique_jobs = [jobs[0]]  # Start with first job
        
        for job in jobs[1:]:
            is_duplicate = False
            
            for unique_job in unique_jobs:
                # Check URL similarity
                if job['url'] == unique_job['url']:
                    is_duplicate = True
                    break
                
                # Check semantic similarity of titles
                title_similarity = self.calculate_semantic_match(
                    job['title'], 
                    unique_job['title']
                )
                
                if title_similarity > 0.8:  # Very similar titles
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_jobs.append(job)
        
        return unique_jobs

# Convenience function
def scrape_jobs_with_nlp(max_jobs: int = 100, user_query: str = "") -> List[Dict]:
    """
    Advanced NLP-based job scraping
    
    Args:
        max_jobs: Maximum number of jobs to find
        user_query: User's search query for semantic matching
    
    Returns:
        List of analyzed job dictionaries with NLP insights
    """
    system = NLPJobDiscoverySystem()
    return system.scrape_jobs_with_nlp(max_jobs, user_query)

# Test function
if __name__ == "__main__":
    print("🧠 Testing NLP Job Discovery System...")
    
    # Test with a user query
    test_query = "entry level data science internship machine learning python"
    jobs = scrape_jobs_with_nlp(20, test_query)
    
    print(f"\n🎯 Found {len(jobs)} relevant jobs for query: '{test_query}'")
    
    for i, job in enumerate(jobs[:5], 1):
        print(f"\n{i}. {job['title']}")
        print(f"   🎯 Job Type: {job['job_type']} (confidence: {job['job_type_confidence']:.2f})")
        print(f"   📍 Location: {job['location']} | Remote: {job['remote']}")
        print(f"   ⭐ Experience: {job['experience_level']}")
        print(f"   🛠️ Technologies: {', '.join(job['technologies'][:3])}")
        if 'semantic_match_score' in job:
            print(f"   🔍 Match Score: {job['semantic_match_score']:.2f}")
        print(f"   📊 Job Confidence: {job['job_confidence']:.2f}")
        print(f"   🏛️ Subreddit: r/{job['subreddit']}")