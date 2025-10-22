# backend/neo4j_service/store_my_resume.py
import json
from pathlib import Path
from connection import init_neo4j
from resume_storage import ResumeNeo4jStorage

def store_laavanya_resume():
    """Store Laavanya's actual resume data"""
    
    # Load your Gemini extraction results
    gemini_file = Path('/Users/laavanya/Desktop/college/snlp/LaavanyaMishra_BTechDS_gemini_analysis.json')
    
    if not gemini_file.exists():
        print(f"Gemini analysis file not found: {gemini_file}")
        return
    
    with open(gemini_file, 'r') as f:
        resume_insights = json.load(f)
    
    # Check if we have valid data (not fallback)
    if resume_insights.get('extraction_method') == 'fallback':
        print("Found fallback data, using manual data instead...")
        
        # Use the successful extraction you showed me
        resume_insights = {
            'personal_info': {
                'name': 'Laavanya Mishra',
                'education_level': 'BTech',
                'field_of_study': 'Data Science',
                'graduation_year': 2026
            },
            'technical_skills': [
                {'skill': 'python', 'category': 'programming_language', 'proficiency': 'intermediate', 'confidence': 0.9},
                {'skill': 'machine learning', 'category': 'ml_library', 'proficiency': 'intermediate', 'confidence': 0.85},
                {'skill': 'neo4j', 'category': 'database', 'proficiency': 'intermediate', 'confidence': 0.9},
                {'skill': 'docker', 'category': 'tools', 'proficiency': 'intermediate', 'confidence': 0.9},
                {'skill': 'streamlit', 'category': 'framework', 'proficiency': 'intermediate', 'confidence': 0.9},
                {'skill': 'sql', 'category': 'database', 'proficiency': 'intermediate', 'confidence': 0.8},
                {'skill': 'aws', 'category': 'cloud', 'proficiency': 'beginner', 'confidence': 0.7},
                {'skill': 'tensorflow', 'category': 'ml_library', 'proficiency': 'intermediate', 'confidence': 0.8},
                {'skill': 'pandas', 'category': 'data_science', 'proficiency': 'intermediate', 'confidence': 0.9},
                {'skill': 'numpy', 'category': 'data_science', 'proficiency': 'intermediate', 'confidence': 0.9}
            ],
            'soft_skills': [
                {'skill': 'Problem-solving', 'evidence': 'Hackathon winner'},
                {'skill': 'Leadership', 'evidence': 'Sub-Head technical fest'},
                {'skill': 'Project Management', 'evidence': 'Multiple complex projects'}
            ],
            'projects': [
                {
                    'title': 'Multimodal Clinical Insight Assistant',
                    'technologies': ['neo4j', 'seaweedfs', 'docker', 'streamlit', 'python'],
                    'description': 'Healthcare platform with HIPAA compliance and voice commands',
                    'domain': 'healthcare',
                    'complexity': 'advanced'
                },
                {
                    'title': 'Breast Cancer Classification of DNA Sequences',
                    'technologies': ['python', 'machine learning', 'deep learning'],
                    'description': 'Research paper on ML/DL approach for cancer detection',
                    'domain': 'healthcare',
                    'complexity': 'advanced'
                },
                {
                    'title': 'Hospital Booking Management System',
                    'technologies': ['django', 'python', 'sql'],
                    'description': 'Full-stack appointment booking system',
                    'domain': 'healthcare',
                    'complexity': 'intermediate'
                }
            ],
            'achievements': [
                {
                    'title': 'EkaCare Hackathon First Prize',
                    'description': 'Built EkaMediBridge platform with voice assistant',
                    'impact': 'high'
                },
                {
                    'title': 'Sub-Head Taqneeq Technical Fest',
                    'description': 'Led event planning and social media',
                    'impact': 'medium'
                }
            ],
            'domains': [
                {'domain': 'healthcare', 'confidence': 0.95, 'evidence': ['Multiple healthcare projects', 'Medical platform internship']},
                {'domain': 'ai_ml', 'confidence': 0.9, 'evidence': ['Data Science degree', 'ML projects']}
            ],
            'experience_level': {'level': 'entry', 'confidence': 0.95, 'reasoning': 'BTech student, graduation 2026'},
            'summary': {
                'profile_strength': 'high',
                'key_strengths': ['Healthcare AI', 'Technical projects', 'Leadership'],
                'potential_roles': ['Junior Data Scientist', 'Healthcare AI Engineer'],
                'salary_range_estimate': '60k-80k USD'
            }
        }
    
    # Store in Neo4j
    if init_neo4j():
        storage = ResumeNeo4jStorage()
        
        print("Storing Laavanya's resume in Neo4j...")
        user_id = storage.store_complete_resume('laavanya.mishra@nmims.edu', resume_insights)
        print(f"✅ Successfully stored resume! User ID: {user_id}")
        
        # Verify storage
        profile = storage.get_user_profile('laavanya.mishra@nmims.edu')
        if profile:
            print(f"\n📊 STORED PROFILE SUMMARY:")
            print(f"   Name: {profile.get('name')}")
            print(f"   Education: {profile.get('education_level')} {profile.get('field_of_study')}")
            print(f"   Experience Level: {profile.get('experience_level')}")
            print(f"   Technical Skills: {len(profile.get('skills', []))}")
            print(f"   Projects: {len(profile.get('projects', []))}")
            print(f"   Domains: {len(profile.get('domains', []))}")
            
            print(f"\n🛠️  TOP SKILLS:")
            for skill in profile.get('skills', [])[:5]:
                print(f"     {skill['skill'].title()} ({skill['proficiency']}) - {skill['confidence']:.2f}")
            
            print(f"\n🎯 DOMAINS:")
            for domain in profile.get('domains', []):
                print(f"     {domain['domain'].title()} - {domain['confidence']:.2f}")

if __name__ == "__main__":
    store_laavanya_resume()