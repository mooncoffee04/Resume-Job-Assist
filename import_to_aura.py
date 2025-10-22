#!/usr/bin/env python3
"""
Import data to Neo4j Aura
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def import_to_aura():
    """Import data to Neo4j Aura"""
    
    print("📥 IMPORTING DATA TO NEO4J AURA")
    print("=" * 40)
    
    # Load exported data
    with open('desktop_neo4j_export.json', 'r') as f:
        data = json.load(f)
    
    print(f"📊 Loaded export data:")
    print(f"   Users: {len(data['users'])}")
    print(f"   Skills: {len(data['user_skills'])}")
    print(f"   Projects: {len(data['user_projects'])}")
    print(f"   Domains: {len(data['user_domains'])}")
    
    # Connect to Aura
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # Clear existing data (optional)
            print("🧹 Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Import users
            print("👤 Importing users...")
            for user_data in data['users']:
                session.run("""
                    CREATE (u:User {
                        id: $id,
                        email: $email,
                        name: $name,
                        education_level: $education_level,
                        field_of_study: $field_of_study,
                        graduation_year: $graduation_year,
                        experience_level: $experience_level,
                        profile_strength: $profile_strength,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                """, user_data)
            
            # Import skills and relationships
            print("🛠️ Importing skills...")
            for skill_rel in data['user_skills']:
                session.run("""
                    MERGE (s:Skill {name: $skill_name})
                    ON CREATE SET s.category = $category
                    WITH s
                    MATCH (u:User {email: $user_email})
                    CREATE (u)-[:HAS_SKILL {
                        proficiency: $proficiency,
                        confidence: $confidence
                    }]->(s)
                """, skill_rel)
            
            # Import projects
            print("🚀 Importing projects...")
            for project_rel in data['user_projects']:
                # Create project
                session.run("""
                    MATCH (u:User {email: $user_email})
                    CREATE (p:Project {
                        title: $project_title,
                        description: $description,
                        domain: $domain,
                        complexity: $complexity
                    })
                    CREATE (u)-[:WORKED_ON]->(p)
                    RETURN p
                """, project_rel)
                
                # Link technologies
                for tech in project_rel.get('technologies', []):
                    if tech:
                        session.run("""
                            MATCH (u:User {email: $user_email})-[:WORKED_ON]->(p:Project {title: $project_title})
                            MERGE (s:Skill {name: $tech_name})
                            CREATE (p)-[:USES_TECHNOLOGY]->(s)
                        """, {
                            'user_email': project_rel['user_email'],
                            'project_title': project_rel['project_title'],
                            'tech_name': tech
                        })
            
            # Import domains
            print("🎯 Importing domains...")
            for domain_rel in data['user_domains']:
                session.run("""
                    MERGE (d:Domain {name: $domain_name})
                    WITH d
                    MATCH (u:User {email: $user_email})
                    CREATE (u)-[:HAS_EXPERTISE {
                        confidence: $confidence,
                        evidence: $evidence
                    }]->(d)
                """, domain_rel)
            
        print("✅ Import completed successfully!")
        
        # Verify import
        with driver.session() as session:
            user_count = session.run("MATCH (u:User) RETURN count(u) as count").single()['count']
            skill_count = session.run("MATCH (s:Skill) RETURN count(s) as count").single()['count']
            project_count = session.run("MATCH (p:Project) RETURN count(p) as count").single()['count']
            
            print(f"\n📊 Import verification:")
            print(f"   Users: {user_count}")
            print(f"   Skills: {skill_count}")
            print(f"   Projects: {project_count}")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    finally:
        driver.close()
    
    return True

if __name__ == "__main__":
    import_to_aura()