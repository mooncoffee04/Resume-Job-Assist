#!/usr/bin/env python3
"""
Export data from desktop Neo4j to Cypher file
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

def export_desktop_data():
    """Export all data from desktop Neo4j"""
    
    print("📦 EXPORTING DATA FROM DESKTOP NEO4J")
    print("=" * 50)
    
    # Desktop Neo4j connection (update if different)
    desktop_uri = "neo4j://127.0.0.1:7687"
    desktop_user = "neo4j"
    desktop_password = "laavanya" 
    
    try:
        driver = GraphDatabase.driver(desktop_uri, auth=(desktop_user, desktop_password))
        
        with driver.session() as session:
            # Export all nodes and relationships
            print("🔍 Exporting nodes...")
            
            # Get all users
            users_result = session.run("MATCH (u:User) RETURN u")
            users = [dict(record['u']) for record in users_result]
            print(f"   Found {len(users)} users")
            
            # Get all skills with relationships
            skills_result = session.run("""
                MATCH (u:User)-[r:HAS_SKILL]->(s:Skill)
                RETURN u.email as user_email, s.name as skill_name, 
                       r.proficiency as proficiency, r.confidence as confidence,
                       s.category as category
            """)
            user_skills = [dict(record) for record in skills_result]
            print(f"   Found {len(user_skills)} skill relationships")
            
            # Get all projects
            projects_result = session.run("""
                MATCH (u:User)-[:WORKED_ON]->(p:Project)
                OPTIONAL MATCH (p)-[:USES_TECHNOLOGY]->(s:Skill)
                RETURN u.email as user_email, p.title as project_title,
                       p.description as description, p.domain as domain,
                       p.complexity as complexity, collect(s.name) as technologies
            """)
            user_projects = [dict(record) for record in projects_result]
            print(f"   Found {len(user_projects)} project relationships")
            
            # Get domains
            domains_result = session.run("""
                MATCH (u:User)-[r:HAS_EXPERTISE]->(d:Domain)
                RETURN u.email as user_email, d.name as domain_name,
                       r.confidence as confidence, r.evidence as evidence
            """)
            user_domains = [dict(record) for record in domains_result]
            print(f"   Found {len(user_domains)} domain relationships")
            
        # Save to JSON file for easy import
        export_data = {
            'users': users,
            'user_skills': user_skills,
            'user_projects': user_projects,
            'user_domains': user_domains
        }
        
        with open('desktop_neo4j_export.json', 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Data exported to: desktop_neo4j_export.json")
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

if __name__ == "__main__":
    export_desktop_data()