#!/usr/bin/env python3
"""
Integrated Resume Processor
Combines text_extractor.py and gemini_resume_parser.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Import our local components
from text_extractor import DocumentTextExtractor
from gemini_resume_parser import extract_resume_with_gemini

# Load environment variables
load_dotenv()

class IntegratedResumeProcessor:
    """
    Complete resume processing pipeline that:
    1. Extracts text from PDF/DOCX using text_extractor
    2. Analyzes with Gemini AI using gemini_resume_parser
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key"""
        self.text_extractor = DocumentTextExtractor()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            print("⚠️  Warning: No Gemini API key found. Set GEMINI_API_KEY environment variable.")
    
    def process_resume(self, resume_file_path: str, save_results: bool = True) -> Tuple[Dict, Optional[str]]:
        """
        Complete resume processing pipeline
        
        Args:
            resume_file_path: Path to PDF/DOCX resume file
            save_results: Whether to save extracted text and analysis to files
            
        Returns:
            (analysis_results, error_message)
        """
        
        print(f"🚀 INTEGRATED RESUME PROCESSING")
        print(f"=" * 50)
        print(f"📄 Processing: {Path(resume_file_path).name}")
        
        # Step 1: Extract text using text_extractor
        print(f"\n📝 Step 1: Extracting text from document...")
        extracted_text, extraction_error = self.text_extractor.extract_text(resume_file_path)
        
        if extraction_error:
            error_msg = f"Text extraction failed: {extraction_error}"
            print(f"❌ {error_msg}")
            return {}, error_msg
        
        print(f"✅ Text extracted: {len(extracted_text)} characters")
        
        # Save extracted text if requested
        if save_results:
            resume_path = Path(resume_file_path)
            text_output_path = resume_path.parent / f"{resume_path.stem}_extracted.txt"
            
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            print(f"💾 Extracted text saved to: {text_output_path}")
        
        # Step 2: Analyze with Gemini AI
        print(f"\n🧠 Step 2: Analyzing with Gemini AI...")
        
        if not self.api_key:
            error_msg = "No Gemini API key available for analysis"
            print(f"❌ {error_msg}")
            return {}, error_msg
        
        analysis_results = extract_resume_with_gemini(extracted_text, self.api_key)
        
        if analysis_results.get('extraction_method') == 'fallback':
            error_msg = f"Gemini analysis failed: {analysis_results.get('error', 'Unknown error')}"
            print(f"❌ {error_msg}")
            return analysis_results, error_msg
        
        print(f"✅ Analysis completed successfully!")
        
        # Add source information
        analysis_results['source_file'] = str(resume_file_path)
        analysis_results['extracted_text_length'] = len(extracted_text)
        
        # Save analysis results if requested
        if save_results:
            resume_path = Path(resume_file_path)
            # Get name from analysis or use filename
            name = analysis_results.get('personal_info', {}).get('name', resume_path.stem)
            safe_name = name.replace(' ', '').replace('.', '').replace('/', '')
            
            analysis_output_path = resume_path.parent / f"{safe_name}_COMPLETE_analysis.json"
            
            with open(analysis_output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Analysis results saved to: {analysis_output_path}")
        
        # Display summary
        self._print_analysis_summary(analysis_results)
        
        return analysis_results, None
    
    def _print_analysis_summary(self, analysis: Dict):
        """Print a nice summary of the analysis"""
        print(f"\n📊 ANALYSIS SUMMARY")
        print(f"=" * 30)
        
        # Personal Info
        personal = analysis.get('personal_info', {})
        if personal.get('name'):
            print(f"👤 Name: {personal['name']}")
            print(f"🎓 Education: {personal.get('education_level', 'N/A')} in {personal.get('field_of_study', 'N/A')}")
        
        # Skills Count
        tech_skills = analysis.get('technical_skills', [])
        projects = analysis.get('projects', [])
        internships = analysis.get('internships', [])
        
        print(f"🛠️  Technical Skills: {len(tech_skills)}")
        print(f"🚀 Projects: {len(projects)}")
        print(f"💼 Internships: {len(internships)}")
        
        # Experience Level
        exp_level = analysis.get('experience_level', {})
        if exp_level.get('level'):
            print(f"📈 Experience Level: {exp_level['level'].upper()}")
        
        # Top Skills Preview
        if tech_skills:
            top_skills = [skill.get('skill', '') for skill in tech_skills[:5]]
            print(f"🔧 Top Skills: {', '.join(top_skills)}")


def process_single_resume(resume_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function to process a single resume
    
    Args:
        resume_path: Path to the resume file
        api_key: Optional Gemini API key (will use env variable if not provided)
        
    Returns:
        Analysis results dictionary
    """
    processor = IntegratedResumeProcessor(api_key)
    results, error = processor.process_resume(resume_path)
    
    if error:
        print(f"❌ Processing failed: {error}")
        return {}
    
    return results


def test_integration():
    """Test the integrated processor"""
    print(f"🧪 TESTING INTEGRATED RESUME PROCESSOR")
    print(f"=" * 50)
    
    # Look for resume files in current directory
    resume_files = []
    current_dir = Path('.')
    
    for pattern in ['*.pdf', '*.docx']:
        resume_files.extend(current_dir.glob(pattern))
    
    if not resume_files:
        print("❌ No PDF or DOCX files found in current directory")
        print("   Please place a resume file here or specify the path")
        return
    
    # Process the first resume found
    resume_file = resume_files[0]
    print(f"📄 Found resume: {resume_file}")
    
    # Test the integration
    processor = IntegratedResumeProcessor()
    results, error = processor.process_resume(str(resume_file))
    
    if error:
        print(f"❌ Integration test failed: {error}")
    else:
        print(f"✅ Integration test successful!")
        print(f"   - Text extraction: ✅")
        print(f"   - Gemini analysis: ✅")
        print(f"   - File saving: ✅")


if __name__ == "__main__":
    test_integration()
