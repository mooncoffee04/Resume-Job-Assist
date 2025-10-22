# backend/nlp_service/semantic_job_matcher.py
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
from pathlib import Path

# For semantic similarity
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")

# Import our existing modules
try:
    from ..neo4j_service.resume_storage import ResumeNeo4jStorage
    from ..neo4j_service.connection import neo4j_connection
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append('../neo4j_service')
    from resume_storage import ResumeNeo4jStorage
    from connection import neo4j_connection

logger = logging.getLogger(__name__)

class SemanticJobMatcher:
    """Match jobs to user profiles using semantic similarity"""
    
    def __init__(self):
        """Initialize the semantic job matcher"""
        
        # Initialize sentence transformer model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight, fast model for job matching
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Loaded sentence transformer model")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning("Sentence transformers not available - falling back to keyword matching")
        
        # Initialize resume storage
        self.resume_storage = ResumeNeo4jStorage()
        
        # Cache for user profiles
        self.user_profile_cache = {}
    
    def get_user_profile_text(self, user_email: str) -> Optional[str]:
        """Convert user profile to searchable text representation"""
        
        # Check cache first
        if user_email in self.user_profile_cache:
            return self.user_profile_cache[user_email]
        
        # Get user profile from Neo4j
        profile = self.resume_storage.get_user_profile(user_email)
        if not profile:
            logger.warning(f"No profile found for user: {user_email}")
            return None
        
        # Convert profile to natural language text
        profile_text = self._profile_to_text(profile)
        
        # Cache the result
        self.user_profile_cache[user_email] = profile_text
        
        return profile_text
    
    def _profile_to_text(self, profile: Dict) -> str:
        """Convert user profile dict to natural language text"""
        
        text_parts = []
        
        # Basic info
        name = profile.get('name', 'User')
        education = profile.get('education_level', '')
        field = profile.get('field_of_study', '')
        exp_level = profile.get('experience_level', 'entry')
        
        text_parts.append(f"{name} is a {exp_level} level professional")
        
        if education and field:
            text_parts.append(f"with {education} degree in {field}")
        
        # Skills
        skills = profile.get('skills', [])
        if skills:
            skill_names = [skill['skill'] for skill in skills[:15]]  # Top 15 skills
            text_parts.append(f"skilled in {', '.join(skill_names)}")
        
        # Domains
        domains = profile.get('domains', [])
        if domains:
            domain_names = [domain['domain'] for domain in domains]
            text_parts.append(f"with expertise in {', '.join(domain_names)}")
        
        # Projects
        projects = profile.get('projects', [])
        if projects:
            project_titles = [project['title'] for project in projects[:3]]  # Top 3 projects
            text_parts.append(f"having worked on projects like {', '.join(project_titles)}")
        
        return '. '.join(text_parts) + '.'
    
    def match_jobs_to_user(self, user_email: str, jobs: List[Dict], 
                          top_k: int = 10) -> List[Dict]:
        """
        Match jobs to user profile using semantic similarity
        
        Args:
            user_email: User's email to get profile
            jobs: List of job dictionaries (from Reddit scraper)
            top_k: Number of top matches to return
            
        Returns:
            List of jobs with similarity scores
        """
        
        # Get user profile text
        user_profile_text = self.get_user_profile_text(user_email)
        if not user_profile_text:
            logger.error(f"Could not get profile for user: {user_email}")
            return []
        
        logger.info(f"🎯 Matching {len(jobs)} jobs for user profile: {user_profile_text[:100]}...")
        
        # Calculate similarity scores
        job_matches = []
        
        for job in jobs:
            # Get job text representation
            job_text = self._job_to_text(job)
            
            # Calculate similarity
            if self.model:
                similarity_score = self._calculate_semantic_similarity(user_profile_text, job_text)
            else:
                similarity_score = self._calculate_keyword_similarity(user_profile_text, job_text)
            
            # Add additional scoring factors
            bonus_score = self._calculate_bonus_score(user_email, job)
            final_score = similarity_score + bonus_score
            
            job_match = {
                **job,  # Original job data
                'similarity_score': similarity_score,
                'bonus_score': bonus_score,
                'final_score': final_score,
                'match_explanation': self._explain_match(user_profile_text, job_text, final_score)
            }
            
            job_matches.append(job_match)
        
        # Sort by final score and return top k
        job_matches.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"✅ Matched jobs. Top score: {job_matches[0]['final_score']:.3f}")
        
        return job_matches[:top_k]
    
    def _job_to_text(self, job: Dict) -> str:
        """Convert job dict to searchable text"""
        
        text_parts = []
        
        # Job title and company
        title = job.get('title', '')
        company = job.get('author', '')  # Reddit author as company
        text_parts.append(f"Job: {title}")
        
        if company and company != '[deleted]':
            text_parts.append(f"at {company}")
        
        # Job content
        content = job.get('content', '')
        if content:
            # Clean and truncate content
            clean_content = content.replace('\n', ' ').strip()
            text_parts.append(clean_content[:500])  # First 500 chars
        
        # Experience level
        exp_level = job.get('experience_level', '')
        if exp_level:
            text_parts.append(f"Experience level: {exp_level}")
        
        # Location and remote
        location = job.get('location', '')
        remote = job.get('remote', False)
        
        if remote:
            text_parts.append("Remote work available")
        elif location:
            text_parts.append(f"Location: {location}")
        
        # Skills mentioned
        skills = job.get('skills_mentioned', [])
        if skills:
            text_parts.append(f"Skills: {', '.join(skills)}")
        
        return '. '.join(text_parts)
    
    def _calculate_semantic_similarity(self, profile_text: str, job_text: str) -> float:
        """Calculate semantic similarity using sentence transformers"""
        
        try:
            # Generate embeddings
            profile_embedding = self.model.encode([profile_text])
            job_embedding = self.model.encode([job_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(profile_embedding, job_embedding)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_keyword_similarity(self, profile_text: str, job_text: str) -> float:
        """Fallback keyword-based similarity"""
        
        # Simple TF-IDF style similarity
        profile_words = set(profile_text.lower().split())
        job_words = set(job_text.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        profile_words -= stop_words
        job_words -= stop_words
        
        # Calculate Jaccard similarity
        intersection = len(profile_words & job_words)
        union = len(profile_words | job_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_bonus_score(self, user_email: str, job: Dict) -> float:
        """Calculate bonus points based on job characteristics"""
        
        bonus = 0.0
        
        # Get user profile for bonus calculations
        profile = self.resume_storage.get_user_profile(user_email)
        if not profile:
            return bonus
        
        user_exp_level = profile.get('experience_level', 'entry')
        job_exp_level = job.get('experience_level', 'entry')
        
        # Experience level match bonus
        if user_exp_level == job_exp_level:
            bonus += 0.1
        
        # Remote work bonus (assuming students prefer remote)
        if job.get('remote', False):
            bonus += 0.05
        
        # Recent post bonus
        created_utc = job.get('created_utc', 0)
        if created_utc:
            days_old = (datetime.now().timestamp() - created_utc) / (24 * 3600)
            if days_old < 7:  # Less than a week old
                bonus += 0.03
        
        # Domain match bonus
        user_domains = [d['domain'] for d in profile.get('domains', [])]
        job_skills = job.get('skills_mentioned', [])
        
        # Check for domain-relevant skills
        domain_keywords = {
            'healthcare': ['healthcare', 'medical', 'clinical', 'patient', 'hospital'],
            'ai_ml': ['machine learning', 'ml', 'ai', 'neural', 'deep learning', 'nlp'],
            'web_dev': ['web', 'frontend', 'backend', 'api', 'javascript', 'react']
        }
        
        for user_domain in user_domains:
            domain_skills = domain_keywords.get(user_domain, [])
            if any(skill in ' '.join(job_skills).lower() for skill in domain_skills):
                bonus += 0.08
                break
        
        return min(bonus, 0.3)  # Cap bonus at 0.3
    
    def _explain_match(self, profile_text: str, job_text: str, score: float) -> str:
        """Generate explanation for why this job matches"""
        
        explanations = []
        
        if score > 0.7:
            explanations.append("Excellent match")
        elif score > 0.5:
            explanations.append("Good match")
        elif score > 0.3:
            explanations.append("Moderate match")
        else:
            explanations.append("Limited match")
        
        # Find common keywords
        profile_words = set(profile_text.lower().split())
        job_words = set(job_text.lower().split())
        common_words = profile_words & job_words
        
        # Filter for meaningful words
        meaningful_words = [word for word in common_words 
                          if len(word) > 3 and word not in {'with', 'have', 'been', 'this', 'that', 'they', 'them', 'were', 'will', 'work'}]
        
        if meaningful_words:
            explanations.append(f"Common keywords: {', '.join(list(meaningful_words)[:5])}")
        
        return '. '.join(explanations)
    
    def search_jobs_by_query(self, user_email: str, query: str, jobs: List[Dict], 
                            top_k: int = 10) -> List[Dict]:
        """
        Search jobs using natural language query combined with user profile
        
        Args:
            user_email: User's email
            query: Natural language search query
            jobs: Available jobs to search through
            top_k: Number of results to return
        """
        
        # Get user profile
        user_profile_text = self.get_user_profile_text(user_email)
        if not user_profile_text:
            logger.error(f"Could not get profile for user: {user_email}")
            return []
        
        # Combine user profile with search query
        enhanced_query = f"{user_profile_text}. Looking for: {query}"
        
        logger.info(f"🔍 Searching with enhanced query: {enhanced_query[:150]}...")
        
        # Calculate similarity with each job
        job_matches = []
        
        for job in jobs:
            job_text = self._job_to_text(job)
            
            if self.model:
                similarity_score = self._calculate_semantic_similarity(enhanced_query, job_text)
            else:
                similarity_score = self._calculate_keyword_similarity(enhanced_query, job_text)
            
            # Add query-specific bonus
            query_bonus = self._calculate_query_bonus(query, job)
            final_score = similarity_score + query_bonus
            
            job_match = {
                **job,
                'similarity_score': similarity_score,
                'query_bonus': query_bonus,
                'final_score': final_score,
                'search_query': query,
                'match_explanation': self._explain_match(enhanced_query, job_text, final_score)
            }
            
            job_matches.append(job_match)
        
        # Sort and return top results
        job_matches.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"✅ Search completed. Top score: {job_matches[0]['final_score']:.3f}")
        
        return job_matches[:top_k]
    
    def _calculate_query_bonus(self, query: str, job: Dict) -> float:
        """Calculate bonus based on specific query terms"""
        
        bonus = 0.0
        query_lower = query.lower()
        job_text = self._job_to_text(job).lower()
        
        # Specific keyword bonuses
        query_keywords = {
            'intern': 0.1,
            'entry': 0.1,
            'junior': 0.1,
            'remote': 0.05,
            'healthcare': 0.08,
            'ai': 0.08,
            'ml': 0.08,
            'data science': 0.1,
            'python': 0.05
        }
        
        for keyword, points in query_keywords.items():
            if keyword in query_lower and keyword in job_text:
                bonus += points
        
        return min(bonus, 0.25)  # Cap at 0.25

# Global instance
semantic_matcher = SemanticJobMatcher()

def match_jobs_for_user(user_email: str, jobs: List[Dict], top_k: int = 10) -> List[Dict]:
    """Convenience function for job matching"""
    return semantic_matcher.match_jobs_to_user(user_email, jobs, top_k)

def search_jobs_with_query(user_email: str, query: str, jobs: List[Dict], top_k: int = 10) -> List[Dict]:
    """Convenience function for job search with query"""
    return semantic_matcher.search_jobs_by_query(user_email, query, jobs, top_k)

if __name__ == "__main__":
    # Test the semantic matcher
    print("🧠 Testing Semantic Job Matcher")
    print("=" * 50)
    
    # Load test jobs (from our Reddit scrape)
    test_jobs_file = Path(__file__).parent.parent / 'reddit_scrape_test.json'
    
    if test_jobs_file.exists():
        with open(test_jobs_file, 'r') as f:
            test_jobs = json.load(f)
        
        print(f"📄 Loaded {len(test_jobs)} test jobs")
        
        # Test with Laavanya's profile
        test_email = 'laavanya.mishra@nmims.edu'
        
        # Test 1: Profile-based matching
        print(f"\n🎯 Test 1: Profile-based job matching")
        matches = match_jobs_for_user(test_email, test_jobs, top_k=3)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['title']}")
            print(f"   Score: {match['final_score']:.3f} (semantic: {match['similarity_score']:.3f}, bonus: {match['bonus_score']:.3f})")
            print(f"   Explanation: {match['match_explanation']}")
            print(f"   URL: {match['url']}")
        
        # Test 2: Query-based search
        print(f"\n🔍 Test 2: Query-based job search")
        query = "healthcare AI internship for data science student"
        search_results = search_jobs_with_query(test_email, query, test_jobs, top_k=2)
        
        for i, result in enumerate(search_results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Score: {result['final_score']:.3f}")
            print(f"   Query: '{result['search_query']}'")
            print(f"   Explanation: {result['match_explanation']}")
        
        print(f"\n✅ Semantic job matcher test completed!")
        
    else:
        print(f"❌ Test jobs file not found: {test_jobs_file}")
        print("Run the Reddit scraper first to generate test data.")