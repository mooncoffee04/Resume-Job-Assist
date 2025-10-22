from typing import Dict, List, Optional
import logging
from datetime import datetime

try:
    from connection import neo4j_connection
    from models import Neo4jModels
except ImportError:
    # Fallback for relative import (if used as a package)
    from .connection import neo4j_connection
    from .models import Neo4jModels

logger = logging.getLogger(__name__)

class ResumeNeo4jStorage:
    """Store and manage resume data in Neo4j"""
    
    def __init__(self, connection=None):
        self.connection = connection or neo4j_connection
        self.models = Neo4jModels(self.connection)
    
    def store_complete_resume(self, user_email: str, resume_insights: Dict) -> str:
        """Store complete resume analysis in Neo4j"""
        
        try:
            with self.connection.get_session() as session:
                # Start transaction for atomicity
                tx = session.begin_transaction()
                
                try:
                    # 1. Create or update user
                    user_id = self._create_or_update_user(tx, user_email, resume_insights)
                    
                    # 2. Store technical skills
                    self._store_technical_skills(tx, user_id, resume_insights.get('technical_skills', []))
                    
                    # 3. Store soft skills
                    self._store_soft_skills(tx, user_id, resume_insights.get('soft_skills', []))
                    
                    # 4. Store projects
                    self._store_projects(tx, user_id, resume_insights.get('projects', []))
                    
                    # 5. Store experience
                    self._store_experience(tx, user_id, resume_insights.get('experience', []))
                    
                    # 6. Store achievements
                    self._store_achievements(tx, user_id, resume_insights.get('achievements', []))
                    
                    # 7. Store domain expertise
                    self._store_domains(tx, user_id, resume_insights.get('domains', []))
                    
                    # 8. Store certifications
                    self._store_certifications(tx, user_id, resume_insights.get('certifications', []))
                    
                    # Commit transaction
                    tx.commit()
                    
                    logger.info(f"✅ Successfully stored resume for user: {user_email}")
                    return user_id
                    
                except Exception as e:
                    tx.rollback()
                    logger.error(f"Transaction failed, rolling back: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to store resume: {e}")
            raise
    
    def _create_or_update_user(self, tx, user_email: str, insights: Dict) -> str:
        """Create or update user profile"""
        
        personal_info = insights.get('personal_info', {})
        exp_level = insights.get('experience_level', {})
        summary = insights.get('summary', {})
        
        # Check if user exists
        existing_user = tx.run(
            "MATCH (u:User {email: $email}) RETURN u.id as id",
            {'email': user_email}
        ).single()
        
        if existing_user:
            # Update existing user
            user_id = existing_user['id']
            tx.run("""
                MATCH (u:User {id: $user_id})
                SET u.name = $name,
                    u.education_level = $education_level,
                    u.field_of_study = $field_of_study,
                    u.graduation_year = $graduation_year,
                    u.experience_level = $experience_level,
                    u.profile_strength = $profile_strength,
                    u.salary_estimate = $salary_estimate,
                    u.updated_at = datetime($updated_at)
                RETURN u
            """, {
                'user_id': user_id,
                'name': personal_info.get('name', ''),
                'education_level': personal_info.get('education_level', ''),
                'field_of_study': personal_info.get('field_of_study', ''),
                'graduation_year': personal_info.get('graduation_year'),
                'experience_level': exp_level.get('level', 'entry'),
                'profile_strength': summary.get('profile_strength', 'medium'),
                'salary_estimate': summary.get('salary_range_estimate', ''),
                'updated_at': datetime.now().isoformat()
            })
            
        else:
            # Create new user
            user_id = self._generate_user_id()
            tx.run("""
                CREATE (u:User {
                    id: $user_id,
                    email: $email,
                    name: $name,
                    education_level: $education_level,
                    field_of_study: $field_of_study,
                    graduation_year: $graduation_year,
                    experience_level: $experience_level,
                    profile_strength: $profile_strength,
                    salary_estimate: $salary_estimate,
                    created_at: datetime($created_at),
                    updated_at: datetime($updated_at)
                })
                RETURN u
            """, {
                'user_id': user_id,
                'email': user_email,
                'name': personal_info.get('name', ''),
                'education_level': personal_info.get('education_level', ''),
                'field_of_study': personal_info.get('field_of_study', ''),
                'graduation_year': personal_info.get('graduation_year'),
                'experience_level': exp_level.get('level', 'entry'),
                'profile_strength': summary.get('profile_strength', 'medium'),
                'salary_estimate': summary.get('salary_range_estimate', ''),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        return user_id
    
    def _store_technical_skills(self, tx, user_id: str, skills: List[Dict]):
        """Store technical skills with relationships"""
        
        # Clear existing skills
        tx.run("""
            MATCH (u:User {id: $user_id})-[r:HAS_SKILL]->(s:Skill)
            DELETE r
        """, {'user_id': user_id})
        
        # Add new skills
        for skill_data in skills:
            skill_name = skill_data.get('skill', '').lower().strip()
            if not skill_name:
                continue
                
            # Create or merge skill
            tx.run("""
                MERGE (s:Skill {name: $skill_name})
                ON CREATE SET 
                    s.id = $skill_id,
                    s.category = $category,
                    s.created_at = datetime($created_at)
                ON MATCH SET
                    s.category = COALESCE(s.category, $category),
                    s.updated_at = datetime($updated_at)
            """, {
                'skill_name': skill_name,
                'skill_id': self._generate_id(),
                'category': skill_data.get('category', 'technical'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
            
            # Create relationship
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (s:Skill {name: $skill_name})
                CREATE (u)-[r:HAS_SKILL {
                    proficiency: $proficiency,
                    confidence: $confidence,
                    context: $context,
                    verified: false,
                    added_at: datetime($added_at)
                }]->(s)
            """, {
                'user_id': user_id,
                'skill_name': skill_name,
                'proficiency': skill_data.get('proficiency', 'intermediate'),
                'confidence': skill_data.get('confidence', 0.7),
                'context': skill_data.get('context', ''),
                'added_at': datetime.now().isoformat()
            })
    
    def _store_soft_skills(self, tx, user_id: str, soft_skills: List[Dict]):
        """Store soft skills"""
        
        for skill_data in soft_skills:
            skill_name = skill_data.get('skill', '').lower().strip()
            if not skill_name:
                continue
                
            # Create soft skill
            tx.run("""
                MERGE (s:SoftSkill {name: $skill_name})
                ON CREATE SET 
                    s.id = $skill_id,
                    s.created_at = datetime($created_at)
            """, {
                'skill_name': skill_name,
                'skill_id': self._generate_id(),
                'created_at': datetime.now().isoformat()
            })
            
            # Create relationship
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (s:SoftSkill {name: $skill_name})
                MERGE (u)-[r:HAS_SOFT_SKILL {
                    evidence: $evidence,
                    added_at: datetime($added_at)
                }]->(s)
            """, {
                'user_id': user_id,
                'skill_name': skill_name,
                'evidence': skill_data.get('evidence', ''),
                'added_at': datetime.now().isoformat()
            })
    
    def _store_projects(self, tx, user_id: str, projects: List[Dict]):
        """Store project information"""
        
        for project_data in projects:
            project_title = project_data.get('title', '').strip()
            if not project_title:
                continue
                
            project_id = self._generate_id()
            
            # Create project
            tx.run("""
                CREATE (p:Project {
                    id: $project_id,
                    title: $title,
                    description: $description,
                    domain: $domain,
                    complexity: $complexity,
                    created_at: datetime($created_at)
                })
            """, {
                'project_id': project_id,
                'title': project_title,
                'description': project_data.get('description', ''),
                'domain': project_data.get('domain', 'general'),
                'complexity': project_data.get('complexity', 'intermediate'),
                'created_at': datetime.now().isoformat()
            })
            
            # Link to user
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (p:Project {id: $project_id})
                CREATE (u)-[:WORKED_ON {
                    role: 'developer',
                    added_at: datetime($added_at)
                }]->(p)
            """, {
                'user_id': user_id,
                'project_id': project_id,
                'added_at': datetime.now().isoformat()
            })
            
            # Link technologies to project
            technologies = project_data.get('technologies', [])
            for tech in technologies:
                tech_name = tech.lower().strip()
                if tech_name:
                    tx.run("""
                        MERGE (s:Skill {name: $tech_name})
                        ON CREATE SET s.id = $skill_id, s.category = 'technical'
                        WITH s
                        MATCH (p:Project {id: $project_id})
                        CREATE (p)-[:USES_TECHNOLOGY]->(s)
                    """, {
                        'tech_name': tech_name,
                        'skill_id': self._generate_id(),
                        'project_id': project_id
                    })
    
    def _store_experience(self, tx, user_id: str, experience: List[Dict]):
        """Store work experience"""
        
        for exp_data in experience:
            company = exp_data.get('company', '').strip()
            role = exp_data.get('role', '').strip()
            
            if not company or not role:
                continue
                
            exp_id = self._generate_id()
            
            # Create experience
            tx.run("""
                CREATE (e:Experience {
                    id: $exp_id,
                    role: $role,
                    company: $company,
                    duration: $duration,
                    type: $type,
                    created_at: datetime($created_at)
                })
            """, {
                'exp_id': exp_id,
                'role': role,
                'company': company,
                'duration': exp_data.get('duration', ''),
                'type': exp_data.get('type', 'internship'),
                'created_at': datetime.now().isoformat()
            })
            
            # Link to user
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (e:Experience {id: $exp_id})
                CREATE (u)-[:HAS_EXPERIENCE]->(e)
            """, {
                'user_id': user_id,
                'exp_id': exp_id
            })
    
    def _store_achievements(self, tx, user_id: str, achievements: List[Dict]):
        """Store achievements"""
        
        for achievement_data in achievements:
            title = achievement_data.get('title', '').strip()
            if not title:
                continue
                
            achievement_id = self._generate_id()
            
            tx.run("""
                CREATE (a:Achievement {
                    id: $achievement_id,
                    title: $title,
                    description: $description,
                    impact: $impact,
                    created_at: datetime($created_at)
                })
            """, {
                'achievement_id': achievement_id,
                'title': title,
                'description': achievement_data.get('description', ''),
                'impact': achievement_data.get('impact', 'medium'),
                'created_at': datetime.now().isoformat()
            })
            
            # Link to user
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (a:Achievement {id: $achievement_id})
                CREATE (u)-[:ACHIEVED]->(a)
            """, {
                'user_id': user_id,
                'achievement_id': achievement_id
            })
    
    def _store_domains(self, tx, user_id: str, domains: List[Dict]):
        """Store domain expertise"""
        
        for domain_data in domains:
            domain_name = domain_data.get('domain', '').strip()
            if not domain_name:
                continue
                
            # Create domain
            tx.run("""
                MERGE (d:Domain {name: $domain_name})
                ON CREATE SET 
                    d.id = $domain_id,
                    d.created_at = datetime($created_at)
            """, {
                'domain_name': domain_name,
                'domain_id': self._generate_id(),
                'created_at': datetime.now().isoformat()
            })
            
            # Create relationship
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (d:Domain {name: $domain_name})
                MERGE (u)-[r:HAS_EXPERTISE {
                    confidence: $confidence,
                    evidence: $evidence,
                    added_at: datetime($added_at)
                }]->(d)
            """, {
                'user_id': user_id,
                'domain_name': domain_name,
                'confidence': domain_data.get('confidence', 0.7),
                'evidence': ', '.join(domain_data.get('evidence', [])),
                'added_at': datetime.now().isoformat()
            })
    
    def _store_certifications(self, tx, user_id: str, certifications: List[Dict]):
        """Store certifications"""
        
        for cert_data in certifications:
            cert_name = cert_data.get('name', '').strip()
            if not cert_name:
                continue
                
            cert_id = self._generate_id()
            
            tx.run("""
                CREATE (c:Certification {
                    id: $cert_id,
                    name: $name,
                    issuer: $issuer,
                    skills: $skills,
                    created_at: datetime($created_at)
                })
            """, {
                'cert_id': cert_id,
                'name': cert_name,
                'issuer': cert_data.get('issuer', ''),
                'skills': ', '.join(cert_data.get('skills', [])),
                'created_at': datetime.now().isoformat()
            })
            
            # Link to user
            tx.run("""
                MATCH (u:User {id: $user_id})
                MATCH (c:Certification {id: $cert_id})
                CREATE (u)-[:HAS_CERTIFICATION]->(c)
            """, {
                'user_id': user_id,
                'cert_id': cert_id
            })
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_user_id(self) -> str:
        """Generate user ID"""
        return self._generate_id()
    
    def get_user_profile(self, user_email: str) -> Optional[Dict]:
        """Retrieve complete user profile from Neo4j"""
        
        try:
            with self.connection.get_session() as session:
                # Get user basic info
                user_result = session.run("""
                    MATCH (u:User {email: $email})
                    RETURN u
                """, {'email': user_email})
                
                user_record = user_result.single()
                if not user_record:
                    return None
                
                user_data = dict(user_record['u'])
                user_id = user_data['id']
                
                # Get skills
                skills_result = session.run("""
                    MATCH (u:User {id: $user_id})-[r:HAS_SKILL]->(s:Skill)
                    RETURN s.name as skill, r.proficiency as proficiency, 
                           r.confidence as confidence, s.category as category
                """, {'user_id': user_id})
                
                user_data['skills'] = [dict(record) for record in skills_result]
                
                # Get projects
                projects_result = session.run("""
                    MATCH (u:User {id: $user_id})-[:WORKED_ON]->(p:Project)
                    OPTIONAL MATCH (p)-[:USES_TECHNOLOGY]->(s:Skill)
                    RETURN p.title as title, p.description as description,
                           p.domain as domain, collect(s.name) as technologies
                """, {'user_id': user_id})
                
                user_data['projects'] = [dict(record) for record in projects_result]
                
                # Get domains
                domains_result = session.run("""
                    MATCH (u:User {id: $user_id})-[r:HAS_EXPERTISE]->(d:Domain)
                    RETURN d.name as domain, r.confidence as confidence
                """, {'user_id': user_id})
                
                user_data['domains'] = [dict(record) for record in domains_result]
                
                return user_data
                
        except Exception as e:
            logger.error(f"Failed to retrieve user profile: {e}")
            return None

# Global instance
resume_storage = ResumeNeo4jStorage()

def store_resume_in_neo4j(user_email: str, resume_insights: Dict) -> str:
    """Convenience function to store resume"""
    return resume_storage.store_complete_resume(user_email, resume_insights)

if __name__ == "__main__":
    # Test storage with sample data
    from connection import init_neo4j
    
    if init_neo4j():
        sample_insights = {
            'personal_info': {
                'name': 'Test User',
                'education_level': 'BTech',
                'field_of_study': 'Data Science',
                'graduation_year': 2026
            },
            'technical_skills': [
                {
                    'skill': 'python',
                    'category': 'programming_language',
                    'proficiency': 'intermediate',
                    'confidence': 0.9
                }
            ],
            'experience_level': {'level': 'entry'},
            'domains': [{'domain': 'healthcare', 'confidence': 0.9}]
        }
        
        user_id = store_resume_in_neo4j('test@example.com', sample_insights)
        print(f"✅ Test storage successful! User ID: {user_id}")
        
        # Test retrieval
        profile = resume_storage.get_user_profile('test@example.com')
        print(f"✅ Retrieved profile: {profile['name']} with {len(profile['skills'])} skills")