#!/usr/bin/env python3
"""
Test the connection between text_extractor and gemini_resume_parser
Using your actual resume file
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path so we can import our modules
sys.path.append('.')

from text_extractor import DocumentTextExtractor
from gemini_resume_parser import extract_resume_with_gemini

# Load environment variables
load_dotenv()

def test_with_your_resume():
    """Test the connection using your actual resume"""
    
    print("🧪 TESTING text_extractor → gemini_resume_parser CONNECTION")
    print("=" * 60)
    
    # Look for your resume (the ones I see in the directory)
    resume_files = [
        "LaavanyaMishra_BTechDS.pdf",  # If it exists here
        "../LaavanyaMishra_BTechDS.pdf",  # If it's in parent directory  
        "/mnt/project/LaavanyaMishra_BTechDS.pdf"  # If it's in project mount
    ]
    
    resume_file = None
    for file_path in resume_files:
        if Path(file_path).exists():
            resume_file = file_path
            break
    
    if not resume_file:
        print("❌ Could not find LaavanyaMishra_BTechDS.pdf")
        print("   Available files in current directory:")
        for file in Path('.').glob('*.pdf'):
            print(f"   - {file}")
        return False
    
    print(f"📄 Found your resume: {resume_file}")
    
    # Step 1: Extract text using text_extractor
    print(f"\n📝 Step 1: Extracting text...")
    extractor = DocumentTextExtractor()
    extracted_text, error = extractor.extract_text(resume_file)
    
    if error:
        print(f"❌ Text extraction failed: {error}")
        return False
    
    print(f"✅ Text extracted: {len(extracted_text)} characters")
    print(f"   Preview: {extracted_text[:100]}...")
    
    # Step 2: Analyze with Gemini
    print(f"\n🧠 Step 2: Analyzing with Gemini...")
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("   Set it in your .env file: GEMINI_API_KEY=your_key_here")
        return False
    
    results = extract_resume_with_gemini(extracted_text, api_key)
    
    if results.get('extraction_method') == 'fallback':
        print(f"❌ Gemini analysis failed: {results.get('error')}")
        return False
    
    print(f"✅ Analysis completed!")
    
    # Step 3: Show results
    print(f"\n📊 Step 3: Results for Laavanya Mishra")
    print("=" * 40)
    
    personal = results.get('personal_info', {})
    tech_skills = results.get('technical_skills', [])
    projects = results.get('projects', [])
    internships = results.get('internships', [])
    
    print(f"👤 Name: {personal.get('name', 'Not extracted')}")
    print(f"🎓 Education: {personal.get('education_level')} in {personal.get('field_of_study')}")
    print(f"🏫 University: {personal.get('university')}")
    print(f"📅 Graduation: {personal.get('graduation_year')}")
    print(f"🛠️  Technical Skills: {len(tech_skills)}")
    print(f"🚀 Projects: {len(projects)}")
    print(f"💼 Internships: {len(internships)}")
    
    if tech_skills:
        top_skills = [skill.get('skill') for skill in tech_skills[:8]]
        print(f"🔧 Top Skills: {', '.join(top_skills)}")
    
    if projects:
        print(f"📋 Project Examples:")
        for project in projects[:3]:
            print(f"   - {project.get('title')}")
    
    # Save results
    output_file = "LaavanyaMishra_TESTED_analysis.json"
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"✅ CONNECTION TEST SUCCESSFUL!")
    
    return True

if __name__ == "__main__":
    success = test_with_your_resume()
    
    if success:
        print(f"\n🎉 PERFECT! The connection works!")
        print(f"   text_extractor.py ➜ gemini_resume_parser.py ✅")
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Use integrated_resume_processor.py for full pipeline")
        print(f"   2. Connect to Neo4j storage")
        print(f"   3. Build job matching system")
    else:
        print(f"\n❌ Connection test failed - check errors above")
