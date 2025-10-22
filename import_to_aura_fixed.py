#!/usr/bin/env python3
"""
Fixed Import data to Neo4j Aura - handles missing fields
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def import_to_aura_fixed():
    """Import data to Neo4j Aura with proper field handling"""
    
    print("📥 IMPORTING DATA TO NEO4J AURA (FIXED)")
    print("=" * 50)
    
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
            
            # Import users with default values for missing fields
            print("👤 Importing users...")
            for user_data in data['users']:
                # Provide defaults for missing fields
                cleaned_user = {
                    'id': user_data.get('id', 'unknown'),
                    'email': user_data.get('email', 'unknown@example.com'),
                    'name': user_data.get('name', 'Unknown User'),
                    'education_level': user_data.get('education_level', 'BTech'),
                    'field_of_study': user_data.get('field_of_study', 'Computer Science'),
                    'graduation_year': user_data.get('graduation_year', 2026),
                    'experience_level': user_data.get('experience_level', 'entry'),
                    'profile_strength': user_data.get('profile_strength', 'medium'),
                    'salary_estimate': user_data.get('salary_estimate', ''),
                    'created_at': user_data.get('created_at', '2024-01-01T00:00:00'),
                    'updated_at': user_data.get('updated_at', '2024-01-01T00:00:00')
                }
                
                print(f"   Creating user: {cleaned_user['name']} ({cleaned_user['email']})")
                
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
                        salary_estimate: $salary_estimate,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                """, cleaned_user)
            
            # Import skills and relationships
            print("🛠️ Importing skills...")
            for skill_rel in data['user_skills']:
                if skill_rel.get('skill_name') and skill_rel.get('user_email'):
                    try:
                        session.run("""
                            MERGE (s:Skill {name: $skill_name})
                            ON CREATE SET s.category = $category, s.id = randomUUID()
                            WITH s
                            MATCH (u:User {email: $user_email})
                            CREATE (u)-[:HAS_SKILL {
                                proficiency: $proficiency,
                                confidence: $confidence,
                                added_at: datetime()
                            }]->(s)
                        """, {
                            'skill_name': skill_rel['skill_name'],
                            'user_email': skill_rel['user_email'],
                            'category': skill_rel.get('category', 'technical'),
                            'proficiency': skill_rel.get('proficiency', 'intermediate'),
                            'confidence': float(skill_rel.get('confidence', 0.7))
                        })
                    except Exception as e:
                        print(f"   ⚠️ Skipped skill {skill_rel.get('skill_name')}: {e}")
            
            # Import projects
            print("🚀 Importing projects...")
            for project_rel in data['user_projects']:
                if project_rel.get('project_title') and project_rel.get('user_email'):
                    try:
                        # Create project
                        session.run("""
                            MATCH (u:User {email: $user_email})
                            CREATE (p:Project {
                                id: randomUUID(),
                                title: $project_title,
                                description: $description,
                                domain: $domain,
                                complexity: $complexity,
                                created_at: datetime()
                            })
                            CREATE (u)-[:WORKED_ON {
                                role: 'developer',
                                added_at: datetime()
                            }]->(p)
                            RETURN p
                        """, {
                            'user_email': project_rel['user_email'],
                            'project_title': project_rel['project_title'],
                            'description': project_rel.get('description', ''),
                            'domain': project_rel.get('domain', 'general'),
                            'complexity': project_rel.get('complexity', 'intermediate')
                        })
                        
                        # Link technologies
                        technologies = project_rel.get('technologies', [])
                        if isinstance(technologies, list):
                            for tech in technologies:
                                if tech and tech.strip():
                                    try:
                                        session.run("""
                                            MATCH (u:User {email: $user_email})-[:WORKED_ON]->(p:Project {title: $project_title})
                                            MERGE (s:Skill {name: $tech_name})
                                            ON CREATE SET s.id = randomUUID(), s.category = 'technical'
                                            CREATE (p)-[:USES_TECHNOLOGY]->(s)
                                        """, {
                                            'user_email': project_rel['user_email'],
                                            'project_title': project_rel['project_title'],
                                            'tech_name': tech.strip()
                                        })
                                    except Exception as e:
                                        print(f"   ⚠️ Skipped tech {tech}: {e}")
                        
                    except Exception as e:
                        print(f"   ⚠️ Skipped project {project_rel.get('project_title')}: {e}")
            
            # Import domains
            print("🎯 Importing domains...")
            for domain_rel in data['user_domains']:
                if domain_rel.get('domain_name') and domain_rel.get('user_email'):
                    try:
                        session.run("""
                            MERGE (d:Domain {name: $domain_name})
                            ON CREATE SET d.id = randomUUID(), d.created_at = datetime()
                            WITH d
                            MATCH (u:User {email: $user_email})
                            CREATE (u)-[:HAS_EXPERTISE {
                                confidence: $confidence,
                                evidence: $evidence,
                                added_at: datetime()
                            }]->(d)
                        """, {
                            'domain_name': domain_rel['domain_name'],
                            'user_email': domain_rel['user_email'],
                            'confidence': float(domain_rel.get('confidence', 0.7)),
                            'evidence': domain_rel.get('evidence', '')
                        })
                    except Exception as e:
                        print(f"   ⚠️ Skipped domain {domain_rel.get('domain_name')}: {e}")
            
        print("✅ Import completed successfully!")
        
        # Verify import
        with driver.session() as session:
            user_count = session.run("MATCH (u:User) RETURN count(u) as count").single()['count']
            skill_count = session.run("MATCH (s:Skill) RETURN count(s) as count").single()['count']
            project_count = session.run("MATCH (p:Project) RETURN count(p) as count").single()['count']
            domain_count = session.run("MATCH (d:Domain) RETURN count(d) as count").single()['count']
            
            print(f"\n📊 Import verification:")
            print(f"   Users: {user_count}")
            print(f"   Skills: {skill_count}")
            print(f"   Projects: {project_count}")
            print(f"   Domains: {domain_count}")
            
            # Show sample data
            print(f"\n👤 Sample users:")
            users = session.run("MATCH (u:User) RETURN u.name as name, u.email as email LIMIT 3").data()
            for user in users:
                print(f"   - {user['name']} ({user['email']})")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.close()
    
    return True

if __name__ == "__main__":
    success = import_to_aura_fixed()
    
    if success:
        print(f"\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"✅ Your data is now in Neo4j Aura")
        print(f"🚀 Ready to build the frontend!")
    else:
        print(f"\n❌ Migration failed - check errors above")
