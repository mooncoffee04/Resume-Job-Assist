from typing import Dict, List, Optional, Any
from datetime import datetime, date
import uuid
import logging

logger = logging.getLogger(__name__)

class Neo4jBaseModel:
    """Base class for all Neo4j node operations"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def generate_id(self) -> str:
        """Generate unique ID for nodes"""
        return str(uuid.uuid4())
    
    def format_datetime(self, dt: datetime) -> str:
        """Format datetime for Neo4j"""
        return dt.isoformat()

class UserModel(Neo4jBaseModel):
    """Handle User node operations"""
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user node"""
        user_id = user_data.get('id', self.generate_id())
        
        query = """
        CREATE (u:User {
            id: $id,
            email: $email,
            name: $name,
            experience_level: $experience_level,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN u
        """
        
        params = {
            'id': user_id,
            'email': user_data['email'],
            'name': user_data.get('name', ''),
            'experience_level': user_data.get('experience_level', 'entry'),
            'created_at': self.format_datetime(datetime.now()),
            'updated_at': self.format_datetime(datetime.now())
        }
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    logger.info(f"✅ Created user: {user_data['email']}")
                    return dict(record['u'])
                return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        query = "MATCH (u:User {email: $email}) RETURN u"
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, {'email': email})
                record = result.single()
                return dict(record['u']) if record else None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        updates['updated_at'] = self.format_datetime(datetime.now())
        
        # Build dynamic SET clause
        set_clauses = [f"u.{key} = ${key}" for key in updates.keys()]
        query = f"""
        MATCH (u:User {{id: $user_id}})
        SET {', '.join(set_clauses)}
        RETURN u
        """
        
        params = {'user_id': user_id, **updates}
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

class SkillModel(Neo4jBaseModel):
    """Handle Skill node operations"""
    
    def create_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or get existing skill"""
        query = """
        MERGE (s:Skill {name: $name})
        ON CREATE SET 
            s.id = $id,
            s.category = $category,
            s.difficulty = $difficulty,
            s.market_demand = $market_demand,
            s.created_at = datetime($created_at)
        ON MATCH SET
            s.updated_at = datetime($updated_at)
        RETURN s
        """
        
        params = {
            'id': skill_data.get('id', self.generate_id()),
            'name': skill_data['name'].lower().strip(),
            'category': skill_data.get('category', 'technical'),
            'difficulty': skill_data.get('difficulty', 'intermediate'),
            'market_demand': skill_data.get('market_demand', 'medium'),
            'created_at': self.format_datetime(datetime.now()),
            'updated_at': self.format_datetime(datetime.now())
        }
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                record = result.single()
                return dict(record['s']) if record else None
        except Exception as e:
            logger.error(f"Failed to create skill: {e}")
            raise

    def add_user_skill(self, user_id: str, skill_name: str, proficiency: str = 'intermediate', 
                      verified: bool = False) -> bool:
        """Add skill to user with proficiency level"""
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (s:Skill {name: $skill_name})
        ON CREATE SET s.id = $skill_id, s.category = 'technical'
        MERGE (u)-[r:HAS_SKILL]->(s)
        SET r.proficiency = $proficiency,
            r.verified = $verified,
            r.added_at = datetime($added_at)
        RETURN r
        """
        
        params = {
            'user_id': user_id,
            'skill_name': skill_name.lower().strip(),
            'skill_id': self.generate_id(),
            'proficiency': proficiency,
            'verified': verified,
            'added_at': self.format_datetime(datetime.now())
        }
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            logger.error(f"Failed to add user skill: {e}")
            return False

    def get_user_skills(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all skills for a user"""
        query = """
        MATCH (u:User {id: $user_id})-[r:HAS_SKILL]->(s:Skill)
        RETURN s.name as skill_name, 
               s.category as category,
               r.proficiency as proficiency,
               r.verified as verified,
               r.added_at as added_at
        ORDER BY s.name
        """
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, {'user_id': user_id})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get user skills: {e}")
            return []

class JobModel(Neo4jBaseModel):
    """Handle Job node operations"""
    
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job posting"""
        job_id = job_data.get('id', self.generate_id())
        
        query = """
        CREATE (j:Job {
            id: $id,
            title: $title,
            company: $company,
            description: $description,
            experience_level: $experience_level,
            location: $location,
            remote: $remote,
            salary_min: $salary_min,
            salary_max: $salary_max,
            source: $source,
            source_url: $source_url,
            posted_date: date($posted_date),
            scraped_at: datetime($scraped_at)
        })
        RETURN j
        """
        
        params = {
            'id': job_id,
            'title': job_data['title'],
            'company': job_data.get('company', 'Unknown'),
            'description': job_data.get('description', ''),
            'experience_level': job_data.get('experience_level', 'entry'),
            'location': job_data.get('location', 'Remote'),
            'remote': job_data.get('remote', True),
            'salary_min': job_data.get('salary_min'),
            'salary_max': job_data.get('salary_max'),
            'source': job_data.get('source', 'reddit'),
            'source_url': job_data.get('source_url', ''),
            'posted_date': job_data.get('posted_date', date.today().isoformat()),
            'scraped_at': self.format_datetime(datetime.now())
        }
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    logger.info(f"✅ Created job: {job_data['title']} at {job_data.get('company')}")
                    return dict(record['j'])
                return None
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise

    def add_job_skill_requirement(self, job_id: str, skill_name: str, 
                                importance: str = 'medium', years_needed: int = 0) -> bool:
        """Add required skill to job"""
        query = """
        MATCH (j:Job {id: $job_id})
        MERGE (s:Skill {name: $skill_name})
        ON CREATE SET s.id = $skill_id, s.category = 'technical'
        MERGE (j)-[r:REQUIRES]->(s)
        SET r.importance = $importance,
            r.years_needed = $years_needed,
            r.added_at = datetime($added_at)
        RETURN r
        """
        
        params = {
            'job_id': job_id,
            'skill_name': skill_name.lower().strip(),
            'skill_id': self.generate_id(),
            'importance': importance,
            'years_needed': years_needed,
            'added_at': self.format_datetime(datetime.now())
        }
        
        try:
            with self.connection.get_session() as session:
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            logger.error(f"Failed to add job skill requirement: {e}")
            return False

# Model factory for dependency injection
class Neo4jModels:
    """Factory class for all Neo4j models"""
    
    def __init__(self, connection):
        self.connection = connection
        self.user = UserModel(connection)
        self.skill = SkillModel(connection)
        self.job = JobModel(connection)

def get_neo4j_models(connection):
    """Factory function for FastAPI dependency injection"""
    return Neo4jModels(connection)

if __name__ == "__main__":
    # Test the models
    from connection import neo4j_connection, init_neo4j
    
    if init_neo4j():
        models = Neo4jModels(neo4j_connection)
        
        # Test user creation
        test_user = {
            'email': 'test@example.com',
            'name': 'Test User',
            'experience_level': 'entry'
        }
        
        user = models.user.create_user(test_user)
        print(f"✅ Created test user: {user}")
        
        # Test skill addition
        if user:
            models.skill.add_user_skill(user['id'], 'Python', 'intermediate', True)
            models.skill.add_user_skill(user['id'], 'Machine Learning', 'beginner', False)
            
            skills = models.skill.get_user_skills(user['id'])
            print(f"✅ User skills: {skills}")
        
        neo4j_connection.close()
        print("✅ Model tests completed!")