#!/usr/bin/env python3
"""
Complete End-to-End Test
1. Extract text from PDF → 2. Analyze with Gemini → 3. Store in Neo4j
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.append('.')
sys.path.append('..')

# Load environment variables
load_dotenv()

def run_complete_pipeline():
    """Run the complete resume processing pipeline"""
    
    print("🚀 COMPLETE RESUME PROCESSING PIPELINE")
    print("=" * 60)
    print("Pipeline: PDF → Text Extraction → Gemini Analysis → Neo4j Storage")
    print()
    
    # Step 1: Check if we have a resume file
    resume_files = []
    for pattern in ['*.pdf', '*.docx']:
        resume_files.extend(Path('.').glob(pattern))
    
    if not resume_files:
        print("❌ No resume files found in current directory")
        print("   Please place a PDF or DOCX resume file here")
        return False
    
    resume_file = resume_files[0]
    print(f"📄 Using resume: {resume_file}")
    
    # Step 2: Run text extraction + Gemini analysis
    print(f"\n📝 STEP 1-2: Text Extraction + Gemini Analysis")
    print("-" * 50)
    
    try:
        from backend.resume_parser.test_connection import process_resume_step_by_step
        
        analysis_results = process_resume_step_by_step(str(resume_file))
        
        if not analysis_results:
            print("❌ Analysis failed")
            return False
        
        print("✅ Analysis completed successfully!")
        
        # Save results for storage step
        output_file = "pipeline_analysis_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Analysis step failed: {e}")
        return False
    
    # Step 3: Store in Neo4j
    print(f"\n🗄️  STEP 3: Neo4j Storage")
    print("-" * 50)
    
    try:
        from store_analysis_to_neo4j import store_tested_analysis_to_neo4j, verify_storage
        from data_adapter import adapt_gemini_output_for_neo4j
        
        # Check Neo4j connection first
        try:
            from connection import init_neo4j
        except ImportError:
            try:
                from neo4j_service.connection import init_neo4j
            except ImportError:
                print("❌ Could not import Neo4j connection")
                return False
    except Exception as e:
        print(f"❌ Import failed: {e}")
        
        if not init_neo4j():
            print("❌ Neo4j connection failed")
            print("   Check your Neo4j credentials in .env file:")
            print("   NEO4J_URI=bolt://localhost:7687")
            print("   NEO4J_USER=neo4j")
            print("   NEO4J_PASSWORD=your_password")
            return False
        
        print("✅ Neo4j connection successful")
        
        # Adapt and store data
        adapted_data = adapt_gemini_output_for_neo4j(analysis_results)
        
        # Get email for storage
        email = analysis_results.get('personal_info', {}).get('email', '<unknown>')