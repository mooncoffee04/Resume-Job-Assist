#!/usr/bin/env python3
"""
Gemini Resume Parser - Copy for Streamlit App
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Optional
import re

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

        # Remove any trailing commas before closing brackets/braces
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
        # Remove any comments or extra text
        response_text = re.sub(r'//.*?\n', '', response_text)

        # Debug: show the response for troubleshooting
        print(f"DEBUG: Cleaned response first 500 chars:")
        print(response_text[:500])
        print(f"DEBUG: Last 200 chars:")
        print(response_text[-200:])
        
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
