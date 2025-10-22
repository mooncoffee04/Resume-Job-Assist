#!/usr/bin/env python3
"""
Example: Using text_extractor with gemini_resume_parser
Shows exactly how to connect the two components
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Import the two components you want to connect
from text_extractor import DocumentTextExtractor
from gemini_resume_parser import extract_resume_with_gemini

# Load environment variables
load_dotenv()

def process_resume_step_by_step(resume_file_path: str):
    """
    Step-by-step example of using text_extractor → gemini_resume_parser
    """
    
    print(f"🔄 STEP-BY-STEP RESUME PROCESSING")
    print(f"=" * 50)
    print(f"📄 Resume file: {resume_file_path}")
    
    # STEP 1: Use text_extractor to get text from PDF/DOCX
    print(f"\n📝 STEP 1: Extract text using text_extractor.py")
    print(f"-" * 30)
    
    extractor = DocumentTextExtractor()
    extracted_text, error = extractor.extract_text(resume_file_path)
    
    if error:
        print(f"❌ Text extraction failed: {error}")
        return None
    
    print(f"✅ Text extracted successfully!")
    print(f"   Length: {len(extracted_text)} characters")
    print(f"   Preview: {extracted_text[:200]}...")
    
    # STEP 2: Use gemini_resume_parser to analyze the extracted text
    print(f"\n🧠 STEP 2: Analyze with gemini_resume_parser.py")
    print(f"-" * 30)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print(f"❌ GEMINI_API_KEY not found in environment variables")
        return None
    
    print(f"✅ API key loaded")
    print(f"📤 Sending extracted text to Gemini...")
    
    # This is the key connection: pass extracted_text to gemini parser
    analysis_results = extract_resume_with_gemini(extracted_text, api_key)
    
    if analysis_results.get('extraction_method') == 'fallback':
        print(f"❌ Gemini analysis failed: {analysis_results.get('error')}")
        return None
    
    print(f"✅ Gemini analysis completed!")
    
    # STEP 3: Show the results
    print(f"\n📊 STEP 3: Results Summary")
    print(f"-" * 30)
    
    personal = analysis_results.get('personal_info', {})
    tech_skills = analysis_results.get('technical_skills', [])
    projects = analysis_results.get('projects', [])
    
    print(f"👤 Name: {personal.get('name', 'Not found')}")
    print(f"🛠️  Technical Skills: {len(tech_skills)}")
    print(f"🚀 Projects: {len(projects)}")
    print(f"📈 Experience Level: {analysis_results.get('experience_level', {}).get('level', 'unknown')}")
    
    return analysis_results

def quick_demo():
    """Quick demo of the connection"""
    
    # Look for your resume in the current directory
    resume_files = []
    for pattern in ['*.pdf', '*.docx']:
        resume_files.extend(Path('.').glob(pattern))
    
    if not resume_files:
        print("❌ No resume files found. Please place a PDF or DOCX file in this directory.")
        return
    
    # Use the first resume found
    resume_file = resume_files[0]
    print(f"📄 Found resume: {resume_file.name}")
    
    # Process it step by step
    results = process_resume_step_by_step(str(resume_file))
    
    if results:
        print(f"\n🎉 SUCCESS! The text_extractor → gemini_resume_parser connection works!")
    else:
        print(f"\n❌ Something went wrong. Check the errors above.")

if __name__ == "__main__":
    print(f"🔗 CONNECTING text_extractor.py → gemini_resume_parser.py")
    print(f"=" * 60)
    print(f"This script shows exactly how to use text_extractor output")
    print(f"with gemini_resume_parser for analysis.")
    print(f"")
    
    quick_demo()
