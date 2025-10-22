#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
Place this in your project root and run it before starting the API
"""

import sys
import os
from pathlib import Path

def check_project_structure():
    """Check if the project structure is correct"""
    
    print("🔍 Checking project structure...")
    print(f"📁 Current directory: {os.getcwd()}")
    
    current_dir = Path(__file__).parent
    backend_dir = current_dir / "backend"
    resume_parser_dir = backend_dir / "resume_parser"
    neo4j_service_dir = backend_dir / "neo4j_service"
    
    print(f"📁 Backend directory: {backend_dir} (exists: {backend_dir.exists()})")
    print(f"📁 Resume parser directory: {resume_parser_dir} (exists: {resume_parser_dir.exists()})")
    print(f"📁 Neo4j service directory: {neo4j_service_dir} (exists: {neo4j_service_dir.exists()})")
    
    # Show what's actually in your directories
    print("\n📋 What we found in your project:")
    
    if backend_dir.exists():
        print("✅ backend/ directory exists")
        for subdir in backend_dir.iterdir():
            if subdir.is_dir():
                print(f"  📁 {subdir.name}/")
                for file in subdir.glob("*.py"):
                    print(f"    📄 {file.name}")
        return backend_dir, resume_parser_dir, neo4j_service_dir
    else:
        print("❌ backend/ directory not found!")
        print("📋 Files in current directory:")
        for file in current_dir.glob("*"):
            if file.is_file():
                print(f"  📄 {file.name}")
            elif file.is_dir():
                print(f"  📁 {file.name}/")
        return None, None, None

def test_imports():
    """Test all required imports"""
    
    # First check structure
    backend_dir, resume_parser_dir, neo4j_service_dir = check_project_structure()
    
    if not backend_dir:
        print("❌ Cannot proceed - backend directory not found")
        return False
    
    # Add to Python path
    sys.path.insert(0, str(resume_parser_dir))
    sys.path.insert(0, str(neo4j_service_dir))
    sys.path.insert(0, str(Path(__file__).parent))
    
    print(f"\n🧪 Testing imports...")
    print(f"📋 Added to Python path:")
    print(f"   - {resume_parser_dir}")
    print(f"   - {neo4j_service_dir}")
    
    # Test each import individually
    try:
        print("\n1️⃣ Testing text_extractor...")
        from text_extractor import DocumentTextExtractor
        print("   ✅ text_extractor imported successfully")
    except ImportError as e:
        print(f"   ❌ text_extractor failed: {e}")
        return False
    
    try:
        print("2️⃣ Testing gemini_resume_parser...")
        from gemini_resume_parser import enhanced_gemini_extraction
        print("   ✅ gemini_resume_parser imported successfully")
    except ImportError as e:
        print(f"   ❌ gemini_resume_parser failed: {e}")
        return False
    
    try:
        print("3️⃣ Testing connection...")
        from connection import init_neo4j
        print("   ✅ connection imported successfully")
    except ImportError as e:
        print(f"   ❌ connection failed: {e}")
        return False
    
    try:
        print("4️⃣ Testing resume_storage...")
        from resume_storage import store_resume_in_neo4j
        print("   ✅ resume_storage imported successfully")
    except ImportError as e:
        print(f"   ❌ resume_storage failed: {e}")
        return False
    
    print("\n🎉 All imports successful!")
    return True

def test_functionality():
    """Test basic functionality"""
    
    print("\n🔧 Testing basic functionality...")
    
    try:
        # Test text extractor
        from text_extractor import DocumentTextExtractor
        extractor = DocumentTextExtractor()
        print("   ✅ DocumentTextExtractor initialized")
        
        # Test Neo4j connection (optional)
        try:
            from connection import init_neo4j
            result = init_neo4j()
            if result:
                print("   ✅ Neo4j connection successful")
            else:
                print("   ⚠️ Neo4j connection failed (check if Neo4j is running)")
        except Exception as e:
            print(f"   ⚠️ Neo4j test failed: {e}")
        
        print("\n🚀 Ready to start the API!")
        return True
        
    except Exception as e:
        print(f"   ❌ Functionality test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 RESUME INTELLIGENCE API - IMPORT TEST")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test functionality
        functionality_ok = test_functionality()
        
        if functionality_ok:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("🚀 You can now run: python api.py")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️ IMPORTS OK, BUT FUNCTIONALITY ISSUES")
            print("🔧 Check Neo4j connection and dependencies")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ IMPORT TESTS FAILED")
        print("🔧 Check your project structure and file locations")
        print("=" * 60)

if __name__ == "__main__":
    main()