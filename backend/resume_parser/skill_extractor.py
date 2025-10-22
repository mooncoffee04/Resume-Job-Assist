import spacy
import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ResumeSkillExtractor:
    """Extract skills, experience, and insights from resume text"""
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded successfully")
        except OSError:
            logger.error("❌ spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            raise
        
        # Comprehensive skill databases
        self.technical_skills = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'r', 'scala', 'go', 'rust',
            'php', 'ruby', 'swift', 'kotlin', 'dart', 'html', 'css', 'sql', 'bash', 'shell',
            
            # Data Science & ML
            'machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence', 
            'data science', 'statistics', 'numpy', 'pandas', 'tensorflow', 'pytorch', 'keras',
            'scikit-learn', 'sklearn', 'matplotlib', 'seaborn', 'plotly', 'opencv', 'nltk',
            'spacy', 'transformers', 'bert', 'gpt', 'computer vision', 'nlp', 'reinforcement learning',
            
            # Databases
            'neo4j', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
            'cassandra', 'dynamodb', 'bigquery', 'snowflake',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'git',
            'github', 'gitlab', 'ci/cd', 'terraform', 'ansible', 'linux', 'ubuntu',
            
            # Web Frameworks
            'django', 'flask', 'fastapi', 'react', 'angular', 'vue', 'node.js', 'express',
            'streamlit', 'gradio', 'spring', 'laravel',
            
            # Data Tools
            'tableau', 'powerbi', 'excel', 'power bi', 'jupyter', 'anaconda', 'spark', 'hadoop',
            'kafka', 'airflow', 'dbt', 'looker',
            
            # Healthcare/Domain Specific
            'hipaa', 'gdpr', 'snomed ct', 'hl7', 'fhir', 'medical imaging', 'bioinformatics',
            'clinical data', 'healthcare analytics'
        }
        
        self.soft_skills = {
            'leadership', 'communication', 'teamwork', 'problem solving', 'analytical thinking',
            'critical thinking', 'project management', 'collaboration', 'adaptability',
            'creativity', 'innovation', 'time management', 'attention to detail',
            'data storytelling', 'presentation skills', 'mentoring', 'strategic thinking',
            'curiosity', 'learning agility', 'emotional intelligence'
        }
        
        # Experience level indicators
        self.experience_indicators = {
            'entry': ['entry level', 'fresh graduate', 'new grad', 'junior', 'intern', 'trainee', '0-1 year', '0-2 years'],
            'mid': ['mid level', 'experienced', '2-5 years', '3-7 years', 'senior analyst', 'lead'],
            'senior': ['senior', 'principal', 'staff', 'architect', '5+ years', '7+ years', 'manager', 'director']
        }
        
        # Domain keywords
        self.domains = {
            'healthcare': ['healthcare', 'medical', 'clinical', 'hospital', 'patient', 'doctor', 'physician', 'medical records'],
            'finance': ['finance', 'banking', 'trading', 'investment', 'fintech', 'insurance', 'risk'],
            'ecommerce': ['ecommerce', 'retail', 'marketplace', 'shopping', 'commerce', 'supply chain'],
            'ai_ml': ['artificial intelligence', 'machine learning', 'deep learning', 'computer vision', 'nlp', 'data science'],
            'web_dev': ['web development', 'frontend', 'backend', 'full stack', 'api', 'microservices'],
            'mobile': ['mobile', 'android', 'ios', 'react native', 'flutter', 'app development']
        }
    
    def extract_all_insights(self, resume_text: str) -> Dict:
        """Extract comprehensive insights from resume"""
        doc = self.nlp(resume_text.lower())
        
        insights = {
            'technical_skills': self._extract_technical_skills(resume_text),
            'soft_skills': self._extract_soft_skills(resume_text),
            'experience_level': self._determine_experience_level(resume_text),
            'domains': self._extract_domains(resume_text),
            'education': self._extract_education(resume_text),
            'achievements': self._extract_achievements(resume_text),
            'projects': self._extract_projects(resume_text),
            'tech_stacks': self._extract_tech_stacks(resume_text),
            'certifications': self._extract_certifications(resume_text),
            'contact_info': self._extract_contact_info(resume_text)
        }
        
        # Add summary statistics
        insights['summary'] = self._generate_summary(insights)
        
        return insights
    
    def _extract_technical_skills(self, text: str) -> List[Dict]:
        """Extract technical skills with confidence scores"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.technical_skills:
            # Look for exact matches and variations
            patterns = [
                rf'\b{re.escape(skill)}\b',
                rf'\b{re.escape(skill)}s\b',  # plural
                rf'\b{re.escape(skill)}\s*\d+\b',  # with version numbers
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    # Get context around the skill
                    start = max(0, match.start() - 50)
                    end = min(len(text_lower), match.end() + 50)
                    context = text_lower[start:end]
                    
                    # Calculate confidence based on context
                    confidence = self._calculate_skill_confidence(skill, context)
                    
                    found_skills.append({
                        'skill': skill,
                        'confidence': confidence,
                        'context': context.strip(),
                        'category': self._categorize_technical_skill(skill)
                    })
                    break  # Only count once per skill
        
        # Remove duplicates and sort by confidence
        unique_skills = {}
        for skill_data in found_skills:
            skill_name = skill_data['skill']
            if skill_name not in unique_skills or skill_data['confidence'] > unique_skills[skill_name]['confidence']:
                unique_skills[skill_name] = skill_data
        
        return sorted(unique_skills.values(), key=lambda x: x['confidence'], reverse=True)
    
    def _extract_soft_skills(self, text: str) -> List[Dict]:
        """Extract soft skills from text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.soft_skills:
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, text_lower):
                # Get context
                match = re.search(pattern, text_lower)
                start = max(0, match.start() - 30)
                end = min(len(text_lower), match.end() + 30)
                context = text_lower[start:end]
                
                found_skills.append({
                    'skill': skill,
                    'context': context.strip(),
                    'category': 'soft_skill'
                })
        
        return found_skills
    
    def _extract_tech_stacks(self, text: str) -> List[Dict]:
        """Extract technology stacks from project descriptions"""
        # Look for patterns like (Tech1 + Tech2 + Tech3)
        stack_pattern = r'\(([^)]+(?:\+|,|\s+and\s+)[^)]+)\)'
        stacks = []
        
        for match in re.finditer(stack_pattern, text):
            stack_text = match.group(1)
            # Split by +, comma, or 'and'
            technologies = re.split(r'\s*[\+,]\s*|\s+and\s+', stack_text)
            
            clean_techs = []
            for tech in technologies:
                tech = tech.strip().lower()
                if len(tech) > 2 and tech in self.technical_skills:
                    clean_techs.append(tech)
            
            if len(clean_techs) >= 2:  # Valid stack has at least 2 technologies
                stacks.append({
                    'stack': clean_techs,
                    'raw_text': stack_text,
                    'context': text[max(0, match.start()-100):match.end()+100]
                })
        
        return stacks
    
    def _extract_projects(self, text: str) -> List[Dict]:
        """Extract project information"""
        projects = []
        
        # Split by project titles (usually followed by tech stack in parentheses)
        project_pattern = r'([A-Z][^(]+)\s*\(([^)]+)\)'
        
        for match in re.finditer(project_pattern, text):
            title = match.group(1).strip()
            tech_stack = match.group(2).strip()
            
            # Get project description (text after the title until next project or section)
            start_pos = match.end()
            
            # Find end of description (next capital letter start or section break)
            end_match = re.search(r'\n[A-Z][^a-z]{2,}|$', text[start_pos:])
            description_end = start_pos + (end_match.start() if end_match else len(text) - start_pos)
            
            description = text[start_pos:description_end].strip()
            
            if len(description) > 50:  # Valid project has substantial description
                projects.append({
                    'title': title,
                    'tech_stack': tech_stack,
                    'description': description[:500],  # Limit description length
                    'domain': self._identify_project_domain(title + ' ' + description)
                })
        
        return projects
    
    def _determine_experience_level(self, text: str) -> str:
        """Determine experience level from resume"""
        text_lower = text.lower()
        
        level_scores = {'entry': 0, 'mid': 0, 'senior': 0}
        
        for level, indicators in self.experience_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    level_scores[level] += 1
        
        # Additional heuristics
        # Check for graduation year (recent grads are likely entry level)
        current_year = 2025
        grad_years = re.findall(r'202[0-6]', text)  # Years 2020-2026
        recent_grad = any(int(year) >= current_year - 2 for year in grad_years)
        
        if recent_grad:
            level_scores['entry'] += 2
        
        # Count internships vs full-time roles
        internship_count = len(re.findall(r'intern', text_lower))
        if internship_count >= 2:
            level_scores['entry'] += 1
        
        # Determine final level
        max_level = max(level_scores, key=level_scores.get)
        confidence = level_scores[max_level] / max(1, sum(level_scores.values()))
        
        return {
            'level': max_level,
            'confidence': confidence,
            'reasoning': level_scores
        }
    
    def _extract_domains(self, text: str) -> List[str]:
        """Extract domain expertise"""
        text_lower = text.lower()
        found_domains = []
        
        for domain, keywords in self.domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score >= 2:  # Need at least 2 domain keywords
                found_domains.append({
                    'domain': domain,
                    'score': score,
                    'keywords_found': [kw for kw in keywords if kw in text_lower]
                })
        
        return sorted(found_domains, key=lambda x: x['score'], reverse=True)
    
    def _calculate_skill_confidence(self, skill: str, context: str) -> float:
        """Calculate confidence score for a skill based on context"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if in skills section
        if any(section in context for section in ['skill', 'technical', 'proficiency']):
            confidence += 0.3
        
        # Higher confidence if in project context
        if any(word in context for word in ['project', 'built', 'developed', 'implemented']):
            confidence += 0.2
        
        # Higher confidence if with other related skills
        related_skills = [s for s in self.technical_skills if s != skill and s in context]
        if len(related_skills) >= 2:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _categorize_technical_skill(self, skill: str) -> str:
        """Categorize technical skills"""
        categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'r'],
            'data_science': ['pandas', 'numpy', 'tensorflow', 'scikit-learn', 'matplotlib'],
            'database': ['neo4j', 'postgresql', 'mysql', 'mongodb', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'web': ['django', 'flask', 'react', 'angular', 'html', 'css'],
            'tools': ['git', 'tableau', 'excel', 'jupyter']
        }
        
        for category, skills in categories.items():
            if skill in skills:
                return category
        
        return 'other'
    
    def _extract_education(self, text: str) -> Dict:
        """Extract education information"""
        # This is a simplified version - can be enhanced
        education_pattern = r'(B\.?Tech|Bachelor|Master|PhD|MBA).*?(\d{4}[-–]\d{4}|\d{4})'
        matches = re.findall(education_pattern, text, re.IGNORECASE)
        
        return {
            'degrees': matches,
            'institutions': re.findall(r'University|College|Institute|School', text, re.IGNORECASE)
        }
    
    def _extract_achievements(self, text: str) -> List[str]:
        """Extract notable achievements"""
        achievement_indicators = [
            'first prize', 'winner', 'award', 'recognition', 'published', 'patent',
            'certification', 'leader', 'head', 'manager', 'top', 'best'
        ]
        
        achievements = []
        for indicator in achievement_indicators:
            pattern = rf'[^.]*{re.escape(indicator)}[^.]*'
            matches = re.findall(pattern, text, re.IGNORECASE)
            achievements.extend(matches)
        
        return achievements[:10]  # Limit to top 10
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        cert_pattern = r'(certification|certified|certificate)[^.]*'
        return re.findall(cert_pattern, text, re.IGNORECASE)
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information"""
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Phone pattern
        phone_pattern = r'(\+?\d{1,4}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        
        # LinkedIn pattern
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        
        return {
            'emails': emails,
            'phones': phones,
            'linkedin': linkedin
        }
    
    def _identify_project_domain(self, project_text: str) -> str:
        """Identify the domain of a project"""
        text_lower = project_text.lower()
        domain_scores = {}
        
        for domain, keywords in self.domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        return max(domain_scores, key=domain_scores.get) if domain_scores else 'general'
    
    def _generate_summary(self, insights: Dict) -> Dict:
        """Generate summary statistics"""
        return {
            'total_technical_skills': len(insights['technical_skills']),
            'total_soft_skills': len(insights['soft_skills']),
            'primary_domain': insights['domains'][0]['domain'] if insights['domains'] else 'general',
            'experience_level': insights['experience_level']['level'],
            'project_count': len(insights['projects']),
            'tech_stack_count': len(insights['tech_stacks'])
        }

# Global instance
skill_extractor = ResumeSkillExtractor()

def extract_resume_insights(resume_text: str) -> Dict:
    """Convenience function for skill extraction"""
    return skill_extractor.extract_all_insights(resume_text)

if __name__ == "__main__":
    # Test with sample resume text
    sample_text = """
    Laavanya Mishra
    BTech Data Science 2022-2026
    
    Technical Skills:
    Python, Machine Learning, Neo4j, Docker, Streamlit, TensorFlow
    
    Projects:
    Multimodal Clinical Insight Assistant (Neo4j + SeaweedFS + Docker + Streamlit)
    Built a healthcare platform with voice commands and HIPAA compliance.
    
    EkaCare's Hackathon Winner - First Prize
    """
    
    extractor = ResumeSkillExtractor()
    insights = extractor.extract_all_insights(sample_text)
    
    print("✅ Skill Extraction Test Results:")
    print(f"Technical Skills: {len(insights['technical_skills'])}")
    print(f"Experience Level: {insights['experience_level']['level']}")
    print(f"Primary Domain: {insights['summary']['primary_domain']}")
    print(f"Projects: {len(insights['projects'])}")