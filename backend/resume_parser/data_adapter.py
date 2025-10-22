#!/usr/bin/env python3
"""
Adapter to fix data structure compatibility between Gemini output and Neo4j storage
"""

def adapt_gemini_output_for_neo4j(analysis_data):
    """
    Adapt the Gemini analysis output to match what Neo4j storage expects
    
    Args:
        analysis_data: Dict from Gemini analysis
        
    Returns:
        Dict: Adapted data structure
    """
    
    # Make a copy to avoid modifying original
    adapted_data = analysis_data.copy()
    
    # Fix 1: Map 'internships' to 'experience' (Neo4j storage expects 'experience')
    if 'internships' in adapted_data:
        internships = adapted_data['internships']
        
        # Convert internship format to experience format
        experience_list = []
        for internship in internships:
            experience_entry = {
                'company': internship.get('company', ''),
                'role': internship.get('role', ''),
                'duration': internship.get('duration', ''),
                'type': 'internship',  # Mark as internship
                'status': internship.get('status', 'completed'),
                'responsibilities': internship.get('responsibilities', ''),
                'technologies': internship.get('technologies', [])
            }
            experience_list.append(experience_entry)
        
        # Add experience field
        adapted_data['experience'] = experience_list
    
    # Fix 2: Handle missing email in personal_info
    personal_info = adapted_data.get('personal_info', {})
    if not personal_info.get('email'):
        # Generate email based on name
        name = personal_info.get('name', 'student')
        email = f"{name.lower().replace(' ', '.')}@student.nmims.edu"
        personal_info['email'] = email
        adapted_data['personal_info'] = personal_info
    
    # Fix 3: Ensure all required fields exist with defaults
    if 'soft_skills' not in adapted_data:
        adapted_data['soft_skills'] = []
    
    if 'achievements' not in adapted_data:
        adapted_data['achievements'] = []
    
    if 'certifications' not in adapted_data:
        adapted_data['certifications'] = []
    
    if 'domains' not in adapted_data:
        adapted_data['domains'] = []
    
    # Fix 4: Handle positions_of_responsibility (convert to achievements if needed)
    if 'positions_of_responsibility' in adapted_data:
        positions = adapted_data['positions_of_responsibility']
        
        # Add to achievements if not already there
        existing_achievements = adapted_data.get('achievements', [])
        
        for position in positions:
            achievement = {
                'title': f"{position.get('title', '')} at {position.get('organization', '')}",
                'description': position.get('responsibilities', ''),
                'impact': 'medium',
                'type': 'position_of_responsibility'
            }
            existing_achievements.append(achievement)
        
        adapted_data['achievements'] = existing_achievements
    
    print(f"✅ Data adapted for Neo4j storage")
    print(f"   Experience entries: {len(adapted_data.get('experience', []))}")
    print(f"   Email: {adapted_data.get('personal_info', {}).get('email', 'Not set')}")
    
    return adapted_data

def test_adapter():
    """Test the adapter with sample data"""
    import json
    from pathlib import Path
    
    # Try to load existing analysis
    analysis_files = [
        "LaavanyaMishra_TESTED_analysis.json",
        "LaavanyaMishra_COMPLETE_analysis.json"
    ]
    
    test_data = None
    for file_path in analysis_files:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                test_data = json.load(f)
            break
    
    if not test_data:
        print("❌ No test data found")
        return
    
    print("🧪 TESTING DATA ADAPTER")
    print("=" * 30)
    
    print(f"📄 Original data structure:")
    print(f"   Has internships: {'internships' in test_data}")
    print(f"   Has experience: {'experience' in test_data}")
    print(f"   Email: {test_data.get('personal_info', {}).get('email')}")
    
    # Adapt the data
    adapted = adapt_gemini_output_for_neo4j(test_data)
    
    print(f"\n📄 Adapted data structure:")
    print(f"   Has internships: {'internships' in adapted}")
    print(f"   Has experience: {'experience' in adapted}")
    print(f"   Email: {adapted.get('personal_info', {}).get('email')}")
    print(f"   Experience count: {len(adapted.get('experience', []))}")

if __name__ == "__main__":
    test_adapter()
