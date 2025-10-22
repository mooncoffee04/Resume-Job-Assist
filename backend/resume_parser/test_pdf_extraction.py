from text_extractor import DocumentTextExtractor, extract_text_from_file
from pathlib import Path

def test_pdf_extraction():
    """Test PDF text extraction"""
    
    # Your PDF file path - replace with your actual path
    pdf_path = "/Users/laavanya/Desktop/college/snlp/resume-intelligence-ai/backend/resume_parser/AryanTuli_B.Tech_DS_CV_Aug04.pdf"  # Update this with your PDF path
    
    print("🔍 Testing PDF Text Extraction")
    print("=" * 50)
    
    # Method 1: Using the convenience function
    print("Method 1: Using convenience function")
    text, error = extract_text_from_file(pdf_path)
    
    if error:
        print(f"❌ Error: {error}")
        return
    
    print(f"✅ Successfully extracted {len(text)} characters")
    print("\n📄 Extracted Text Preview (first 500 chars):")
    print("-" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 50)
    
    # Method 2: Using the class directly
    print("\nMethod 2: Using DocumentTextExtractor class")
    extractor = DocumentTextExtractor()
    
    # Get document info first
    doc_info = extractor.get_document_info(pdf_path)
    print(f"📋 Document Info:")
    for key, value in doc_info.items():
        print(f"   {key}: {value}")
    
    # Extract text
    text2, error2 = extractor.extract_text(pdf_path)
    
    if error2:
        print(f"❌ Error: {error2}")
    else:
        print(f"✅ Text extraction successful!")
        
        # Save extracted text to file for inspection
        output_file = Path(pdf_path).stem + "_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text2)
        
        print(f"💾 Full extracted text saved to: {output_file}")
        
        # Show some statistics
        lines = text2.split('\n')
        words = text2.split()
        
        print(f"\n📊 Text Statistics:")
        print(f"   Total characters: {len(text2)}")
        print(f"   Total lines: {len(lines)}")
        print(f"   Total words: {len(words)}")
        print(f"   Non-empty lines: {len([l for l in lines if l.strip()])}")

if __name__ == "__main__":
    # Update this with your actual PDF path
    pdf_path = "AryanTuli_B.Tech_DS_CV_Aug04.pdf"  # This file exists in your resume_parser folder
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please update the pdf_path variable with the correct path to your PDF file")
    else:
        test_pdf_extraction()