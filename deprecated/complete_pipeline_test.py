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
        from deprecated.test_connection import process_resume_step_by_step
        
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
        personal_info = adapted_data.get('personal_info', {})\n        user_email = personal_info.get('email', 'laavanya.mishra@student.nmims.edu')\n        \n        # Store in Neo4j\n        try:\n            from resume_storage import ResumeNeo4jStorage\n        except ImportError:\n            from neo4j_service.resume_storage import ResumeNeo4jStorage\n        \n        storage = ResumeNeo4jStorage()\n        user_id = storage.store_complete_resume(user_email, adapted_data)\n        \n        print(f\"✅ Data stored successfully!\")\n        print(f\"   User ID: {user_id}\")\n        print(f\"   Email: {user_email}\")\n        \n        # Verify storage\n        print(f\"\\n🔍 Verifying storage...\")\n        profile = storage.get_user_profile(user_email)\n        \n        if profile:\n            print(f\"✅ Verification successful!\")\n            print(f\"   Retrieved profile for: {profile.get('name', 'Unknown')}\")\n            print(f\"   Skills: {len(profile.get('skills', []))}\")\n            print(f\"   Projects: {len(profile.get('projects', []))}\")\n        else:\n            print(f\"❌ Verification failed - could not retrieve profile\")\n            return False\n        \n    except Exception as e:\n        print(f\"❌ Storage step failed: {e}\")\n        import traceback\n        traceback.print_exc()\n        return False\n    \n    # Success!\n    print(f\"\\n🎉 COMPLETE PIPELINE SUCCESS!\")\n    print(f\"=\" * 40)\n    print(f\"✅ Text extraction: Complete\")\n    print(f\"✅ Gemini analysis: Complete\")\n    print(f\"✅ Neo4j storage: Complete\")\n    print(f\"✅ Data verification: Complete\")\n    \n    print(f\"\\n🚀 READY FOR NEXT PHASE:\")\n    print(f\"   1. Job scraping from Reddit\")\n    print(f\"   2. Intelligent job matching\")\n    print(f\"   3. Gap analysis & recommendations\")\n    print(f\"   4. Career advice generation\")\n    \n    return True\n\ndef check_prerequisites():\n    \"\"\"Check if all prerequisites are met\"\"\"\n    \n    print(\"🔍 CHECKING PREREQUISITES\")\n    print(\"-\" * 30)\n    \n    # Check environment variables\n    required_env_vars = ['GEMINI_API_KEY', 'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']\n    missing_vars = []\n    \n    for var in required_env_vars:\n        if not os.getenv(var):\n            missing_vars.append(var)\n    \n    if missing_vars:\n        print(f\"❌ Missing environment variables:\")\n        for var in missing_vars:\n            print(f\"   - {var}\")\n        print(f\"\\n   Add these to your .env file:\")\n        print(f\"   GEMINI_API_KEY=your_gemini_key\")\n        print(f\"   NEO4J_URI=bolt://localhost:7687\")\n        print(f\"   NEO4J_USER=neo4j\")\n        print(f\"   NEO4J_PASSWORD=your_password\")\n        return False\n    \n    print(f\"✅ Environment variables: Complete\")\n    \n    # Check required files\n    required_files = [\n        'text_extractor.py',\n        'gemini_resume_parser.py',\n        'data_adapter.py'\n    ]\n    \n    missing_files = []\n    for file in required_files:\n        if not Path(file).exists():\n            missing_files.append(file)\n    \n    if missing_files:\n        print(f\"❌ Missing required files:\")\n        for file in missing_files:\n            print(f\"   - {file}\")\n        return False\n    \n    print(f\"✅ Required files: Complete\")\n    \n    # Check resume file\n    resume_files = []\n    for pattern in ['*.pdf', '*.docx']:\n        resume_files.extend(Path('.').glob(pattern))\n    \n    if not resume_files:\n        print(f\"❌ No resume files found\")\n        print(f\"   Place a PDF or DOCX resume in current directory\")\n        return False\n    \n    print(f\"✅ Resume file: {resume_files[0]}\")\n    \n    return True\n\nif __name__ == \"__main__\":\n    print(f\"🎯 RESUME INTELLIGENCE AI - COMPLETE PIPELINE TEST\")\n    print(f\"=\" * 60)\n    \n    # Check prerequisites\n    if not check_prerequisites():\n        print(f\"\\n❌ Prerequisites not met. Fix the issues above and try again.\")\n        sys.exit(1)\n    \n    print(f\"\\n✅ All prerequisites met!\")\n    \n    # Run the pipeline\n    success = run_complete_pipeline()\n    \n    if success:\n        print(f\"\\n🏆 PIPELINE COMPLETED SUCCESSFULLY!\")\n        print(f\"   Your resume is now fully processed and stored.\")\n        print(f\"   Ready to build job matching features!\")\n    else:\n        print(f\"\\n❌ Pipeline failed. Check errors above.\")"}, {"oldText": "        personal_info = adapted_data.get('personal_info', {})", "newText": "        personal_info = adapted_data.get('personal_info', {})"}]