#!/usr/bin/env python3
"""
Data Adapter - Copy for Streamlit App
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
        email = f"{name.lower().replace(' ', '.')}@student.example.com"
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
    
    return adapted_data
