#!/usr/bin/env python3
"""
Resume Intelligence AI - Streamlit Frontend (MVP Version)
Upload → Extract → Analyze → Display (Neo4j optional)
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local imports
from connection import init_neo4j
from text_extractor import DocumentTextExtractor
from gemini_resume_parser import extract_resume_with_gemini
from data_adapter import adapt_gemini_output_for_neo4j
# Add these imports after line 12
try:
    from resume_storage import ResumeNeo4jStorage
    NEO4J_STORAGE_AVAILABLE = True
except ImportError:
    NEO4J_STORAGE_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Resume Intelligence AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Dark Mode
st.markdown("""
<style>
    /* Dark mode styling */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    .main-header {
        font-size: 2.5rem;  /* Reduced from 3rem */
        font-weight: bold;
        color: #00d4ff;  /* Changed to cyan for dark mode */
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .success-box {
        background-color: #1e3a2e;
        border: 1px solid #4caf50;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    
    .info-box {
        background-color: #1a2332;
        border: 1px solid #00d4ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    
    /* Fix metric text overflow */
    .metric-container .metric-value {
        font-size: 1.2rem !important;
        word-wrap: break-word;
        max-width: 100%;
    }
    
    /* Dark mode for dataframes */
    .stDataFrame {
        background-color: #262730;
    }
    
    /* Dark mode for charts */
    .stPlotlyChart {
        background-color: transparent;
    }
    
    /* Sidebar dark mode */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* Text inputs dark mode */
    .stTextInput input {
        background-color: #262730;
        color: #fafafa;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🚀 Resume Intelligence AI</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>Transform your resume into actionable career insights!</strong><br>
        Upload your resume → AI extracts skills & experience → Get comprehensive analysis
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Navigation")
        page = st.selectbox("Choose a page:", [
            "🏠 Upload & Process",
            "📈 Analytics Dashboard", 
            "🔧 Settings"
        ])
    
    # Route to different pages
    if page == "🏠 Upload & Process":
        upload_and_process_page()
    elif page == "📈 Analytics Dashboard":
        analytics_dashboard_page()
    elif page == "🔧 Settings":
        settings_page()

def upload_and_process_page():
    """Main upload and processing page"""
    
    st.header("📤 Upload Your Resume")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=['pdf', 'docx'],
        help="Upload a PDF or DOCX resume file for AI-powered analysis"
    )
    
    if uploaded_file is not None:
        # Show file details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 File Name", uploaded_file.name)
        with col2:
            st.metric("📊 File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("📋 File Type", uploaded_file.type)
        
        # Process button
        if st.button("🚀 Process Resume", type="primary", use_container_width=True):
            process_resume(uploaded_file)

def process_resume(uploaded_file):
    """Process the uploaded resume through the complete pipeline"""
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Save uploaded file
        status_text.text("📝 Step 1/3: Saving uploaded file...")
        progress_bar.progress(10)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        progress_bar.progress(25)
        
        # Step 2: Extract text
        status_text.text("🔍 Step 2/3: Extracting text from document...")
        
        extractor = DocumentTextExtractor()
        extracted_text, error = extractor.extract_text(temp_file_path)
        
        if error:
            st.error(f"❌ Text extraction failed: {error}")
            return
        
        progress_bar.progress(50)
        
        # Show text preview
        with st.expander("📄 Extracted Text Preview"):
            st.text_area(
                "First 500 characters:",
                extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                height=200
            )
        
        # Step 3: Analyze with Gemini
        status_text.text("🧠 Step 3/3: Analyzing with Gemini AI...")
        
        from secrets_helper import GEMINI_API_KEY
        api_key = GEMINI_API_KEY
        if not api_key:
            st.error("❌ Gemini API key not found! Please set GEMINI_API_KEY in your environment.")
            return
        
        analysis_results = extract_resume_with_gemini(extracted_text, api_key)
        
        if analysis_results.get('extraction_method') == 'fallback':
            st.error(f"❌ Gemini analysis failed: {analysis_results.get('error')}")
            return
        
        progress_bar.progress(100)
        status_text.text("✅ Processing completed successfully!")
        
        # Adapt data structure
        adapted_data = adapt_gemini_output_for_neo4j(analysis_results)
        
        # Show success message
        st.markdown("""
        <div class="success-box">
            <h3>🎉 Resume Processing Completed!</h3>
            <p>Your resume has been successfully analyzed by AI.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display results
        display_analysis_results(adapted_data)
        
        # Save results for download
        result_file = save_results_to_file(adapted_data, uploaded_file.name)
        
        with open(result_file, 'rb') as f:
            st.download_button(
                label="📥 Download Analysis Results (JSON)",
                data=f.read(),
                file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        # Auto-store in Neo4j
        if NEO4J_STORAGE_AVAILABLE:
            with st.spinner("Storing in Neo4j database..."):
                try_neo4j_storage(adapted_data)
        else:
            st.info("Neo4j storage not available - skipping database storage")
        
    except Exception as e:
        st.error(f"❌ Processing failed: {e}")
        import traceback
        st.error(traceback.format_exc())
    
    finally:
        # Clean up temp file
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

def try_neo4j_storage(adapted_data):
    """Try to store in Neo4j if credentials are available"""
    
    if not NEO4J_STORAGE_AVAILABLE:
        st.warning("⚠️ Neo4j storage modules not available")
        return
    
    try:
        # Get email for storage
        personal_info = adapted_data.get('personal_info', {})
        user_email = personal_info.get('email', f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com")
        
        from connection import init_neo4j
        init_neo4j()
        
        # Use your full storage system
        storage = ResumeNeo4jStorage()
        user_id = storage.store_complete_resume(user_email, adapted_data)
        
        st.success(f"✅ Successfully stored complete resume in Neo4j!")
        st.info(f"User ID: {user_id}")
        st.info(f"Email: {user_email}")
        
    except Exception as e:
        st.error(f"❌ Neo4j storage failed: {e}")

def display_analysis_results(analysis_data):
    """Display the analysis results in a beautiful format"""
    
    st.header("📊 Analysis Results")
    
    # Personal info
    personal = analysis_data.get('personal_info', {})
    if personal:
        st.subheader("👤 Personal Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            name = personal.get('name', 'Not found')
            if len(name) > 15:
                name = name[:12] + "..."
            st.metric("🎓 Name", name)
        with col2:
            education = f"{personal.get('education_level', '')} {personal.get('field_of_study', '')}"
            if len(education) > 20:
                education = education[:17] + "..."
            st.metric("📚 Education", education)
        with col3:
            university = personal.get('university', 'Not found')
            if len(university) > 15:
                university = university[:12] + "..."
        st.metric("🏫 University", university)
    
    # Technical skills
    tech_skills = analysis_data.get('technical_skills', [])
    if tech_skills:
        st.subheader("🛠️ Technical Skills")
        
        # Create skills dataframe for visualization
        skills_df = pd.DataFrame(tech_skills)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📊 Total Skills", len(tech_skills))
            
            # Skills by category
            if 'category' in skills_df.columns:
                category_counts = skills_df['category'].value_counts()
                fig = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title="Skills by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3  # Better colors for dark mode
                )
                # Update layout for dark mode
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top skills
            if 'confidence' in skills_df.columns:
                top_skills = skills_df.nlargest(10, 'confidence')[['skill', 'proficiency', 'confidence']]
                st.dataframe(top_skills, use_container_width=True)
            else:
                st.dataframe(skills_df[['skill', 'category']][:10], use_container_width=True)
    
    # Projects
    projects = analysis_data.get('projects', [])
    if projects:
        st.subheader("🚀 Projects")
        
        for i, project in enumerate(projects[:5]):  # Show top 5 projects
            with st.expander(f"📋 {project.get('title', f'Project {i+1}')}"):
                st.write(f"**Domain:** {project.get('domain', 'Not specified')}")
                st.write(f"**Complexity:** {project.get('complexity', 'Not specified')}")
                st.write(f"**Description:** {project.get('description', 'No description')}")
                
                technologies = project.get('technologies', [])
                if technologies:
                    st.write(f"**Technologies:** {', '.join(technologies)}")
    
    # Experience level and summary
    exp_level = analysis_data.get('experience_level', {})
    summary = analysis_data.get('summary', {})

    if exp_level or summary:
        st.subheader("📈 Profile Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if exp_level:
                level = exp_level.get('level', 'Unknown').upper()
                st.metric("📊 Experience", level[:10])  # Truncate long text
        
        with col2:
            if summary:
                strength = summary.get('profile_strength', 'Unknown').upper()
                st.metric("💪 Strength", strength[:8])  # Truncate long text
        
        with col3:
            if summary:
                salary = summary.get('salary_range_estimate', 'Not estimated')
                # Truncate salary if too long
                if len(salary) > 15:
                    salary = salary[:12] + "..."
                st.metric("💰 Salary", salary)

def analytics_dashboard_page():
    """Analytics dashboard showing processed resumes"""
    
    st.header("📈 Analytics Dashboard")
    st.info("🚧 Coming soon! This will show insights from all processed resumes.")
    
    # Show sample metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Resumes Processed", "15")
    with col2:
        st.metric("🛠️ Unique Skills Found", "89")
    with col3:
        st.metric("🚀 Projects Analyzed", "47")
    with col4:
        st.metric("💼 Companies Mentioned", "12")

def settings_page():
    """Settings and configuration page"""
    
    st.header("🔧 Settings")
    
    # Environment variables status
    st.subheader("🌍 Environment Variables")
    
    from secrets_helper import GEMINI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

    env_vars = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USER": NEO4J_USER,
        "NEO4J_PASSWORD": NEO4J_PASSWORD
    }
    
    for var, value in env_vars.items():
        if value:
            st.success(f"✅ {var}: {'*' * 10}")
        else:
            st.error(f"❌ {var}: Not set")
    
    # Instructions
    st.subheader("📝 Setup Instructions")
    st.markdown("""
    1. **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. **Neo4j Aura**: Create free instance at [Neo4j Aura](https://console.neo4j.io/)
    3. **Environment Variables**: Add to `.streamlit/secrets.toml` for deployment
    """)

def save_results_to_file(data, original_filename):
    """Save analysis results to a JSON file"""
    
    # Create results directory if it doesn't exist
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(original_filename).stem
    result_filename = results_dir / f"{base_name}_analysis_{timestamp}.json"
    
    # Save data
    with open(result_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    return result_filename

if __name__ == "__main__":
    main()
