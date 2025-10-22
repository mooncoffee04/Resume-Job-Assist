#!/usr/bin/env python3
"""Enhanced Gemini resume extraction - captures ALL resume information"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Optional

# Load environment variables
load_dotenv()

def extract_resume_with_gemini(resume_text: str, api_key: str) -> Dict:
    """
    API-compatible function for resume extraction
    
    Args:
        resume_text: The extracted text from the resume
        api_key: Gemini API key
        
    Returns:
        Dict: Structured resume insights
    """
    
    print(f"🧠 Analyzing resume with Gemini AI...")
    print(f"📄 Resume text length: {len(resume_text)} characters")
    
    if not api_key:
        print("❌ No API key provided")
        return _get_fallback_response("No API key provided")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Enhanced comprehensive prompt
        prompt = f"""
You are an expert resume analyzer. Extract ALL information from this resume into structured JSON.

**CRITICAL INSTRUCTIONS:**
1. Extract EVERYTHING - don't skip any section
2. Be thorough - capture all skills, projects, internships, achievements
3. Infer proficiency levels based on context (beginner/intermediate/advanced)
4. Return ONLY valid JSON, no additional text

**JSON Structure (fill ALL fields):**

{{
  "personal_info": {{
    "name": "Full Name",
    "email": "email if present",
    "phone": "phone if present",
    "education_level": "BTech/MTech/MBA/etc",
    "graduation_year": 2026,
    "field_of_study": "Data Science/Computer Science/etc",
    "university": "University name",
    "cgpa": "CGPA if mentioned"
  }},
  
  "technical_skills": [
    {{
      "skill": "Python",
      "category": "programming_language",
      "proficiency": "beginner/intermediate/advanced",
      "confidence": 0.9
    }}
  ],
  
  "soft_skills": [
    {{
      "skill": "Leadership",
      "evidence": "Where it was demonstrated"
    }}
  ],
  
  "projects": [
    {{
      "title": "Project Name",
      "technologies": ["Tech1", "Tech2"],
      "description": "Full project description",
      "domain": "healthcare/finance/web/ai_ml/other",
      "complexity": "beginner/intermediate/advanced"
    }}
  ],
  
  "internships": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Month Year - Current/Month Year",
      "status": "current/completed",
      "responsibilities": "What they're working on",
      "technologies": ["Tech used"]
    }}
  ],
  
  "achievements": [
    {{
      "title": "Achievement name",
      "description": "Details about the achievement",
      "impact": "high/medium/low"
    }}
  ],
  
  "certifications": [
    {{
      "name": "Certification Name",
      "issuer": "Organization/Platform",
      "skills": ["Skills covered"]
    }}
  ],
  
  "domains": [
    {{
      "domain": "healthcare/ai_ml/finance/web_dev/data_science/other",
      "confidence": 0.9,
      "evidence": ["Project 1", "Internship X"]
    }}
  ],
  
  "experience_level": {{
    "level": "entry/mid/senior",
    "confidence": 0.95,
    "reasoning": "Why - student/years of experience/internships"
  }},
  
  "summary": {{
    "profile_strength": "low/medium/high/exceptional",
    "key_strengths": ["Strength 1", "Strength 2"],
    "potential_roles": ["Job titles they'd be good for"],
    "salary_range_estimate": "Expected range"
  }}
}}

Resume Text:
{resume_text}

Return ONLY the JSON, no markdown formatting or additional text.
"""
        
        response = model.generate_content(prompt)
        
        if not response.text:
            print("❌ Empty response from Gemini")
            return _get_fallback_response("Empty response from Gemini")
        
        # Clean response
        response_text = response.text.strip()
        
        # Remove markdown wrapper
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        insights = json.loads(response_text)
        
        # Add metadata
        insights['extraction_method'] = 'gemini'
        insights['extraction_timestamp'] = _get_timestamp()
        
        print("✅ Successfully extracted complete resume data!")
        print(f"   Technical Skills: {len(insights.get('technical_skills', []))}")
        print(f"   Projects: {len(insights.get('projects', []))}")
        print(f"   Experience Level: {insights.get('experience_level', {}).get('level', 'unknown')}")
        
        return insights
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return _get_fallback_response(f"JSON parsing failed: {e}")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return _get_fallback_response(f"Extraction failed: {e}")

def _get_fallback_response(error_message: str) -> Dict:
    """Return fallback response structure"""
    return {
        'personal_info': {},
        'technical_skills': [],
        'soft_skills': [],
        'projects': [],
        'internships': [],
        'achievements': [],
        'certifications': [],
        'domains': [],
        'experience_level': {'level': 'entry', 'confidence': 0.5},
        'summary': {'profile_strength': 'unknown'},
        'extraction_method': 'fallback',
        'extraction_timestamp': _get_timestamp(),
        'error': error_message
    }

def _get_timestamp() -> str:
    """Get current timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()

def enhanced_gemini_extraction():
    """Extract complete resume information using enhanced Gemini prompt"""
    
    print("🚀 ENHANCED GEMINI RESUME EXTRACTION")
    print("=" * 60)
    
    # Load resume text
    extracted_file = Path('AryanTuli_B.Tech_DS_CV_Aug04_extracted.txt')

    if not extracted_file.exists():
        print("❌ Extracted text file not found!")
        return None
    
    with open(extracted_file, 'r', encoding='utf-8') as f:
        resume_text = f.read()
    
    print(f"✅ Loaded resume: {len(resume_text)} characters")
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found!")
        return None
    
    print(f"✅ API key configured")
    
    # Use the new API-compatible function
    insights = extract_resume_with_gemini(resume_text, api_key)
    
    if insights.get('extraction_method') == 'fallback':
        print("❌ Extraction failed")
        return None
    
    # Display comprehensive results
    print(f"\n📊 COMPLETE EXTRACTION RESULTS")
    print("=" * 60)
    
    # Personal Info
    personal = insights.get('personal_info', {})
    print(f"\n👤 PERSONAL INFO:")
    print(f"   Name: {personal.get('name')}")
    print(f"   Education: {personal.get('education_level')} in {personal.get('field_of_study')}")
    print(f"   University: {personal.get('university', 'N/A')}")
    print(f"   Graduation: {personal.get('graduation_year')}")
    print(f"   CGPA: {personal.get('cgpa', 'N/A')}")
    
    # Technical Skills
    tech_skills = insights.get('technical_skills', [])
    print(f"\n🛠️ TECHNICAL SKILLS ({len(tech_skills)}):")
    skill_categories = {}
    for skill in tech_skills:
        category = skill.get('category', 'other')
        if category not in skill_categories:
            skill_categories[category] = []
        skill_categories[category].append(skill.get('skill'))
    
    for category, skills in sorted(skill_categories.items()):
        print(f"   {category}: {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")
    
    # Projects
    projects = insights.get('projects', [])
    print(f"\n🚀 PROJECTS ({len(projects)}):")
    for project in projects:
        print(f"   - {project.get('title')}")
        print(f"     Tech: {', '.join(project.get('technologies', [])[:5])}")
        print(f"     Domain: {project.get('domain', 'N/A')} | Complexity: {project.get('complexity', 'N/A')}")
    
    # Experience Level
    exp = insights.get('experience_level', {})
    print(f"\n📈 EXPERIENCE LEVEL:")
    print(f"   Level: {exp.get('level', 'unknown').upper()}")
    print(f"   Confidence: {exp.get('confidence', 0):.2f}")
    print(f"   Reasoning: {exp.get('reasoning', 'N/A')}")
    
    # Save complete results
    name = personal.get('name', 'resume').replace(' ', '').replace('.', '').replace('/', '')
    output_file = f"{name}_COMPLETE_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 SAVED TO: {output_file}")
    print(f"✅ EXTRACTION COMPLETED!")
    
    return insights

if __name__ == "__main__":
    result = enhanced_gemini_extraction()
    
    if result:
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. ✅ Complete resume extracted")
        print(f"   2. 📄 Ready to store in Neo4j")
        print(f"   3. 🎯 Can now power intelligent job matching")
    else:
        print(f"\n❌ Extraction failed. Check errors above.")