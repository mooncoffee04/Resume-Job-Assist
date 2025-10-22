# backend/neo4j_service/test_storage.py
from connection import neo4j_connection, init_neo4j
from resume_storage import ResumeNeo4jStorage

def test_storage():
    if init_neo4j():
        storage = ResumeNeo4jStorage()
        
        # Sample data from your Gemini extraction
        sample_insights = {
            'personal_info': {
                'name': 'Laavanya Mishra',
                'education_level': 'BTech',
                'field_of_study': 'Data Science',
                'graduation_year': 2026
            },
            'technical_skills': [
                {
                    'skill': 'python',
                    'category': 'programming_language',
                    'proficiency': 'intermediate',
                    'confidence': 0.9,
                    'context': 'mentioned in skills section'
                },
                {
                    'skill': 'neo4j',
                    'category': 'database',
                    'proficiency': 'intermediate', 
                    'confidence': 0.9,
                    'context': 'project technologies'
                }
            ],
            'projects': [
                {
                    'title': 'Multimodal Clinical Insight Assistant',
                    'technologies': ['neo4j', 'docker', 'streamlit'],
                    'description': 'Healthcare platform with HIPAA compliance',
                    'domain': 'healthcare',
                    'complexity': 'intermediate'
                }
            ],
            'experience_level': {'level': 'entry', 'confidence': 0.95},
            'domains': [
                {'domain': 'healthcare', 'confidence': 0.95, 'evidence': ['clinical project']}
            ],
            'summary': {
                'profile_strength': 'high',
                'salary_range_estimate': '60k-80k USD'
            }
        }
        
        print("Testing resume storage...")
        user_id = storage.store_complete_resume('laavanya@example.com', sample_insights)
        print(f"✅ Stored resume! User ID: {user_id}")
        
        # Test retrieval
        profile = storage.get_user_profile('laavanya@example.com')
        if profile:
            print(f"✅ Retrieved profile for: {profile.get('name')}")
            print(f"   Skills: {len(profile.get('skills', []))}")
            print(f"   Projects: {len(profile.get('projects', []))}")
            print(f"   Domains: {len(profile.get('domains', []))}")
        
        neo4j_connection.close()

if __name__ == "__main__":
    test_storage()