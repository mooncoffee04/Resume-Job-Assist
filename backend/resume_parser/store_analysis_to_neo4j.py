#!/usr/bin/env python3
"""
Store Tested Resume Analysis to Neo4j
Loads the JSON file from your tested analysis and stores it in Neo4j
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.append('.')
sys.path.append('..')

# Import Neo4j storage and data adapter
try:
    from resume_storage import ResumeNeo4jStorage
    from connection import init_neo4j
except ImportError:
    try:
        from neo4j_service.resume_storage import ResumeNeo4jStorage
        from neo4j_service.connection import init_neo4j
    except ImportError:
        print("❌ Could not import Neo4j modules")
        print("   Make sure you're in the right directory")
        sys.exit(1)

# Import data adapter
try:
    from data_adapter import adapt_gemini_output_for_neo4j
except ImportError:
    print("❌ Could not import data_adapter - make sure data_adapter.py exists")
    sys.exit(1)

# Load environment variables
load_dotenv()

def store_tested_analysis_to_neo4j():
    """Store your tested resume analysis to Neo4j"""
    
    print("🗄️  STORING TESTED ANALYSIS TO NEO4J")
    print("=" * 50)
    
    # Look for your tested analysis JSON file
    analysis_files = [
        "LaavanyaMishra_TESTED_analysis.json",
        "LaavanyaMishra_COMPLETE_analysis.json",
        "LaavanyaMishra_BTechDS_COMPLETE_analysis.json"
    ]
    
    analysis_file = None
    for file_path in analysis_files:
        if Path(file_path).exists():
            analysis_file = file_path
            break
    
    if not analysis_file:
        print("❌ Could not find tested analysis JSON file")
        print("   Looking for files like:")
        for file in analysis_files:
            print(f"   - {file}")
        
        # Show available JSON files
        json_files = list(Path('.').glob('*.json'))
        if json_files:
            print(f"\n   Available JSON files:")
            for file in json_files:
                print(f"   - {file}")
        return False
    
    print(f"📄 Found analysis file: {analysis_file}")
    
    # Load the analysis data
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        print(f"✅ Loaded analysis data")
        print(f"   Method: {analysis_data.get('extraction_method', 'unknown')}")
        print(f"   Timestamp: {analysis_data.get('extraction_timestamp', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Failed to load analysis file: {e}")
        return False
    
    # Initialize Neo4j connection
    print(f"\n🔌 Connecting to Neo4j...")
    if not init_neo4j():
        print("❌ Failed to connect to Neo4j")
        print("   Check your Neo4j credentials in .env file")
        return False
    
    print(f"✅ Connected to Neo4j")
    
    # Get user email (from personal info or use default)
    personal_info = analysis_data.get('personal_info', {})
    user_email = personal_info.get('email')
    
    if not user_email:
        # Use a default email based on the name or file
        name = personal_info.get('name', 'LaavanyaMishra')
        user_email = f"{name.lower().replace(' ', '.')}@student.nmims.edu"
        print(f"📧 No email found, using: {user_email}")
    else:
        print(f"📧 Using email from resume: {user_email}")
    
    # Adapt data structure for Neo4j compatibility
    print(f"\n🔧 Adapting data structure...")
    adapted_data = adapt_gemini_output_for_neo4j(analysis_data)
    
    # Store to Neo4j
    print(f"\n🗄️  Storing to Neo4j...")
    try:
        storage = ResumeNeo4jStorage()
        user_id = storage.store_complete_resume(user_email, adapted_data)
        
        print(f"✅ Successfully stored resume data!")
        print(f"   User ID: {user_id}")
        print(f"   Email: {user_email}")
        
        # Show what was stored
        personal = analysis_data.get('personal_info', {})
        tech_skills = analysis_data.get('technical_skills', [])
        projects = analysis_data.get('projects', [])
        internships = analysis_data.get('internships', [])
        achievements = analysis_data.get('achievements', [])
        
        print(f"\n📊 STORED DATA SUMMARY:")
        print(f"   👤 Name: {personal.get('name', 'Not found')}")
        print(f"   🎓 Education: {personal.get('education_level')} in {personal.get('field_of_study')}")
        print(f"   🏫 University: {personal.get('university', 'Not found')}")
        print(f"   🛠️  Technical Skills: {len(tech_skills)}")
        print(f"   🚀 Projects: {len(projects)}")
        print(f"   💼 Internships: {len(internships)}")
        print(f"   🏆 Achievements: {len(achievements)}")
        
        if tech_skills:
            top_skills = [skill.get('skill', '') for skill in tech_skills[:6]]
            print(f"   🔧 Top Skills: {', '.join(top_skills)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to store in Neo4j: {e}")
        return False

def verify_storage(user_email: str):
    """Verify that the data was stored correctly"""
    
    print(f"\n🔍 VERIFYING STORAGE...")
    print(f"-" * 30)
    
    try:
        storage = ResumeNeo4jStorage()
        profile = storage.get_user_profile(user_email)
        
        if not profile:
            print(f"❌ Could not retrieve profile for {user_email}")
            return False
        
        print(f"✅ Profile retrieved successfully!")
        print(f"   Name: {profile.get('name')}")
        print(f"   Skills: {len(profile.get('skills', []))}")
        print(f"   Projects: {len(profile.get('projects', []))}")
        print(f"   Domains: {len(profile.get('domains', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main function"""
    
    # Store the analysis
    success = store_tested_analysis_to_neo4j()
    
    if not success:
        print(f"\n❌ Storage failed - check errors above")
        return
    
    # Get the email for verification
    analysis_files = [
        "LaavanyaMishra_TESTED_analysis.json",
        "LaavanyaMishra_COMPLETE_analysis.json",
        "LaavanyaMishra_BTechDS_COMPLETE_analysis.json"
    ]
    
    for file_path in analysis_files:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            personal_info = data.get('personal_info', {})
            user_email = personal_info.get('email')
            
            if not user_email:
                name = personal_info.get('name', 'LaavanyaMishra')
                user_email = f"{name.lower().replace(' ', '.')}@student.nmims.edu"
            
            # Verify storage
            verify_storage(user_email)
            break
    
    print(f"\n🎉 RESUME SUCCESSFULLY STORED IN NEO4J!")
    print(f"🚀 NEXT STEPS:")
    print(f"   1. ✅ Resume analysis completed")
    print(f"   2. ✅ Data stored in Neo4j")
    print(f"   3. 🎯 Ready for job matching!")
    print(f"   4. 📊 Can now power recommendations")

if __name__ == "__main__":
    main()
