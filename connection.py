from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from typing import Optional
import logging
from contextlib import contextmanager

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    try:
        import streamlit as st
        neo4j_uri = st.secrets.get('NEO4J_URI') or os.getenv('NEO4J_URI')
        neo4j_user = st.secrets.get('NEO4J_USER') or os.getenv('NEO4J_USER')
        neo4j_password = st.secrets.get('NEO4J_PASSWORD') or os.getenv('NEO4J_PASSWORD')
        neo4j_database = st.secrets.get('NEO4J_DATABASE') or os.getenv('NEO4J_DATABASE', 'neo4j')
    except:
        # Fallback for local development
        neo4j_uri = os.getenv('NEO4J_URI')
        neo4j_user = os.getenv('NEO4J_USER')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')

settings = Settings()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self):
        self.driver: Optional[GraphDatabase.driver] = None
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self.database = settings.neo4j_database
        
    def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=60  # 60 seconds
            )
            
            # Test the connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info(f"✅ Successfully connected to Neo4j at {self.uri}")
                    return True
                    
        except AuthError as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"❌ Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
            
        return False
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    @contextmanager
    def get_session(self):
        """Context manager for Neo4j sessions"""
        if not self.driver:
            raise Exception("Neo4j driver not initialized. Call connect() first.")
            
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def verify_connectivity(self):
        """Verify that the connection is working"""
        try:
            with self.get_session() as session:
                result = session.run("""
                    CALL dbms.components() 
                    YIELD name, versions, edition 
                    RETURN name, versions, edition
                """)
                
                for record in result:
                    logger.info(f"Connected to {record['name']} {record['versions'][0]} ({record['edition']})")
                return True
                
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False
    
    def create_constraints(self):
        """Create database constraints and indexes for optimal performance"""
        constraints = [
            # User constraints
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
            
            # Skill constraints
            "CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
            
            # Job constraints
            "CREATE CONSTRAINT job_id_unique IF NOT EXISTS FOR (j:Job) REQUIRE j.id IS UNIQUE",
            
            # Company constraints
            "CREATE CONSTRAINT company_name_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
        ]
        
        indexes = [
            # Performance indexes
            "CREATE INDEX user_created_at IF NOT EXISTS FOR (u:User) ON (u.created_at)",
            "CREATE INDEX job_posted_date IF NOT EXISTS FOR (j:Job) ON (j.posted_date)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category)",
        ]
        
        try:
            with self.get_session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.info(f"✅ Created constraint: {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                    except Exception as e:
                        logger.warning(f"Constraint may already exist: {e}")
                
                for index in indexes:
                    try:
                        session.run(index)
                        logger.info(f"✅ Created index: {index.split('FOR')[1].split('ON')[0].strip()}")
                    except Exception as e:
                        logger.warning(f"Index may already exist: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to create constraints/indexes: {e}")

# Global connection instance
neo4j_connection = Neo4jConnection()

def get_neo4j_connection():
    """Dependency function for FastAPI"""
    return neo4j_connection

# Initialize connection on import
def init_neo4j():
    """Initialize Neo4j connection"""
    try:
        neo4j_connection.connect()
        neo4j_connection.verify_connectivity()
        neo4j_connection.create_constraints()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    print("Testing Neo4j connection...")
    if init_neo4j():
        print("✅ Neo4j connection test successful!")
        neo4j_connection.close()
    else:
        print("❌ Neo4j connection test failed!")