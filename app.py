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
import hashlib
import uuid

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

def authenticate_user(email, password):
    """Check user credentials in Neo4j"""
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        with neo4j_connection.get_session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                RETURN u.password_hash as hash, u.salt as salt
            """, {'email': email})
            
            record = result.single()
            if record:
                stored_hash = record['hash']
                salt = record['salt']
                input_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return stored_hash == input_hash.hex()
            
    except Exception as e:
        st.error(f"Authentication error: {e}")
    
    return False

def register_user(email, password, name):
    """Register new user in Neo4j"""
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        # Generate salt and hash password
        salt = str(uuid.uuid4())
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
        
        with neo4j_connection.get_session() as session:
            # Check if user exists
            existing = session.run("MATCH (u:User {email: $email}) RETURN u", {'email': email}).single()
            if existing:
                return False
            
            # Create user
            session.run("""
                CREATE (u:User {
                    id: $id,
                    email: $email,
                    name: $name,
                    password_hash: $password_hash,
                    salt: $salt,
                    created_at: datetime(),
                    updated_at: datetime()
                })
            """, {
                'id': str(uuid.uuid4()),
                'email': email,
                'name': name,
                'password_hash': password_hash,
                'salt': salt
            })
            
            return True
            
    except Exception as e:
        st.error(f"Registration error: {e}")
        return False

def simple_auth():
    """Simple email + password authentication"""
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = None
    
    if not st.session_state.authenticated:
        st.title("🚀 Resume Intelligence AI")
        st.subheader("Please login or create an account to continue")
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])
        
        with tab1:
            st.subheader("Welcome Back!")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary"):
                if authenticate_user(email, password):
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with tab2:
            st.subheader("Create Your Account")
            st.info("Join to save your resume analysis and track your progress!")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_name = st.text_input("Full Name", key="reg_name")
            
            if st.button("Create Account", type="primary"):
                if reg_email and reg_password and reg_name:
                    if register_user(reg_email, reg_password, reg_name):
                        st.success("Account created successfully! Please switch to the Login tab.")
                    else:
                        st.error("Registration failed - email may already exist")
                else:
                    st.error("Please fill in all fields")
        
        return False
    
    return True

def display_resume_from_database(resume_content_b64, resume_filename):
    """Display resume content stored in database as base64"""
    
    st.header("📄 Original Resume")
    
    try:
        import base64
        
        # Decode the base64 content
        resume_content = base64.b64decode(resume_content_b64)
        file_size = len(resume_content)
        file_extension = Path(resume_filename).suffix.lower()
        
        st.success("✅ Resume loaded from database")
        st.info(f"**File:** {resume_filename}")
        st.info(f"**Size:** {file_size:,} bytes")
        st.info(f"**Type:** {file_extension}")
        
        
        # Display content in browser based on file type
        if file_extension == '.pdf':
            st.subheader("📖 PDF Viewer")
            # Display PDF directly in browser using base64
            pdf_base64 = base64.b64encode(resume_content).decode('utf-8')
            pdf_display = f"""
            <iframe src="data:application/pdf;base64,{pdf_base64}" 
                    width="100%" height="800px" type="application/pdf">
                <p>Your browser doesn't support PDF viewing. 
                   <a href="data:application/pdf;base64,{pdf_base64}" download="{resume_filename}">
                   Click here to download the PDF</a>
                </p>
            </iframe>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)
            
        elif file_extension in ['.txt']:
            st.subheader("📝 Text Content:")
            try:
                content = resume_content.decode('utf-8')
                st.text_area("Resume Content", content, height=600, disabled=True)
            except UnicodeDecodeError:
                st.warning("Could not decode text content for preview")
                
        elif file_extension in ['.docx']:
            st.subheader("📄 Word Document")
            st.info("Word documents cannot be displayed directly in browser, but you can download it above.")
            
            # Try to extract and show text content
            try:
                # Save temporarily to extract text
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                    tmp_file.write(resume_content)
                    tmp_file_path = tmp_file.name
                
                from text_extractor import DocumentTextExtractor
                extractor = DocumentTextExtractor()
                extraction_result = extractor.extract_text(tmp_file_path)
                
                # Handle tuple return (text, metadata) or just text
                if isinstance(extraction_result, tuple):
                    extracted_text = extraction_result[0]
                else:
                    extracted_text = extraction_result
                
                if extracted_text:
                    st.subheader("📝 Text Preview:")
                    st.text_area("Extracted Content", extracted_text, height=600, disabled=True)
                
                # Clean up temp file
                import os
                os.unlink(tmp_file_path)
                        
            except Exception as e:
                st.warning(f"Could not extract text for preview: {e}")
        else:
            st.info("File type not supported for browser viewing. You can download it above.")
            
    except Exception as e:
        st.error(f"Error displaying resume from database: {e}")

def display_original_resume(resume_file_path):
    """Display the original resume file"""
    
    st.header("📄 Original Resume")
    
    try:
        file_path = Path(resume_file_path)
        
        # Show file info regardless of existence
        st.info(f"**File:** {file_path.name}")
        st.info(f"**Stored Path:** {resume_file_path}")
        
        if not file_path.exists():
            st.error("⚠️ Resume file not found in deployment environment.")
            st.info("💡 **Note:** In deployed apps, uploaded files may not persist between sessions. The file was uploaded but may have been cleared by the hosting platform.")
            
            # Suggest alternatives
            st.markdown("""
            **Possible solutions:**
            1. Re-upload your resume to get a fresh analysis with in-browser viewing
            2. Files in cloud deployments are typically temporary
            """)
            return
        
        # Get file info if file exists
        file_size = file_path.stat().st_size
        file_extension = file_path.suffix.lower()
        
        st.info(f"**Size:** {file_size:,} bytes")
        st.info(f"**Type:** {file_extension}")
        
        # Provide download button
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                st.download_button(
                    label="⬇️ Download Resume",
                    data=file_data,
                    file_name=file_path.name,
                    mime="application/octet-stream",
                    use_container_width=True
                )
                st.success("✅ File found and ready for download!")
        except Exception as e:
            st.error(f"❌ Could not read file for download: {e}")
            return
        
        # Display content in browser based on file type
        if file_extension == '.pdf':
            st.subheader("📖 PDF Viewer")
            try:
                import base64
                with open(file_path, 'rb') as file:
                    pdf_content = file.read()
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    pdf_display = f"""
                    <iframe src="data:application/pdf;base64,{pdf_base64}" 
                            width="100%" height="800px" type="application/pdf">
                        <p>Your browser doesn't support PDF viewing. 
                           <a href="data:application/pdf;base64,{pdf_base64}" download="{file_path.name}">
                           Click here to download the PDF</a>
                        </p>
                    </iframe>
                    """
                    st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not display PDF: {e}")
            
        elif file_extension in ['.txt']:
            st.subheader("📝 Text Content:")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    st.text_area("Resume Content", content, height=600, disabled=True)
            except Exception as e:
                st.error(f"Could not read text content: {e}")
                
        elif file_extension in ['.docx']:
            st.subheader("📄 Word Document")
            st.info("Word documents cannot be displayed directly in browser, but you can download it above.")
            
            # Try to extract text for preview (optional)
            try:
                from text_extractor import DocumentTextExtractor
                extractor = DocumentTextExtractor()
                extraction_result = extractor.extract_text(str(file_path))
                
                # Handle tuple return (text, metadata) or just text
                if isinstance(extraction_result, tuple):
                    extracted_text = extraction_result[0]
                else:
                    extracted_text = extraction_result
                
                if extracted_text:
                    st.subheader("📝 Text Preview:")
                    st.text_area("Extracted Content", extracted_text, height=600, disabled=True)
                        
            except Exception as e:
                st.warning(f"Could not extract text for preview: {e}")
        else:
            st.info("File type not supported for browser viewing. You can download it above.")
            
    except Exception as e:
        st.error(f"Error displaying resume: {e}")
        st.info("💡 This is likely because the deployment environment doesn't persist uploaded files.")

def show_user_analyses():
    """Show user's saved resume analyses"""
    
    st.header("My Saved Analyses")
    
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        user_email = st.session_state.user_email
        
        with neo4j_connection.get_session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})-[:HAS_ANALYSIS]->(a:Analysis)
                RETURN a.id as id, a.created_at as created_at, 
                       a.data as data, a.resume_name as name,
                       a.resume_file_path as resume_file_path,
                       coalesce(a.resume_content_b64, null) as resume_content_b64,
                       coalesce(a.resume_filename, null) as resume_filename
                ORDER BY a.created_at DESC
            """, {'email': user_email})
            
            analyses = list(result)
            
            if not analyses:
                st.info("No saved analyses yet. Upload a resume to get started!")
                return
            
            st.write(f"Found {len(analyses)} saved analyses:")
            
            for analysis in analyses:
                created_at = analysis['created_at']
                name = analysis['name'] or "Unknown"
                resume_file_path = analysis.get('resume_file_path')
                resume_content_b64 = analysis.get('resume_content_b64')
                resume_filename = analysis.get('resume_filename')
                
                with st.expander(f"{name} - {str(created_at)[:19]}"):
                    # Create columns for better button layout
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"📊 View Analysis", key=f"view_{analysis['id']}", use_container_width=True):
                            # Set a session state flag to show analysis outside expander
                            st.session_state[f"show_analysis_{analysis['id']}"] = True
                            st.session_state.current_analysis_data = analysis['data']
                            st.rerun()
                    
                    with col2:
                        # Check what resume data we have
                        resume_content_b64 = analysis.get('resume_content_b64')
                        resume_filename = analysis.get('resume_filename') 
                        resume_file_path = analysis.get('resume_file_path')
                        
                        # Determine if we can show resume
                        has_database_content = resume_content_b64 is not None
                        has_file_path = resume_file_path is not None
                        file_exists = Path(resume_file_path).exists() if resume_file_path else False
                        
                        can_show_resume = has_database_content or file_exists
                        
                        if can_show_resume:
                            if st.button(f"📄 View Resume", key=f"resume_{analysis['id']}", use_container_width=True):
                                # Set session state for resume viewing
                                st.session_state[f"show_resume_{analysis['id']}"] = True
                                st.session_state.current_resume_path = resume_file_path
                                st.session_state.current_resume_content_b64 = resume_content_b64
                                st.session_state.current_resume_filename = resume_filename or (Path(resume_file_path).name if resume_file_path else None)
                                st.rerun()
                        else:
                            # Show appropriate disabled button based on what's missing
                            if has_file_path and not file_exists:
                                st.button(f"📄 File Missing", key=f"resume_missing_{analysis['id']}", disabled=True, use_container_width=True)
                                st.caption("File not found in deployment")
                            else:
                                st.button(f"📄 Resume N/A", key=f"resume_na_{analysis['id']}", disabled=True, use_container_width=True)
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{analysis['id']}", type="secondary", use_container_width=True):
                            # Delete the analysis using a separate session state to avoid conflicts
                            try:
                                with neo4j_connection.get_session() as delete_session:
                                    delete_session.run("MATCH (a:Analysis {id: $id}) DETACH DELETE a", 
                                                      {'id': analysis['id']})
                                st.success("Analysis deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting analysis: {e}")
            
            # Display analysis results outside expander for full width
            for analysis in analyses:
                analysis_key = f"show_analysis_{analysis['id']}"
                if st.session_state.get(analysis_key, False):
                    st.markdown("---")
                    try:
                        saved_data = json.loads(st.session_state.current_analysis_data)
                        display_analysis_results(saved_data)
                        
                        # Add a button to hide the analysis
                        if st.button("❌ Hide Analysis", key=f"hide_analysis_{analysis['id']}"):
                            st.session_state[analysis_key] = False
                            if 'current_analysis_data' in st.session_state:
                                del st.session_state.current_analysis_data
                            st.rerun()
                            
                    except json.JSONDecodeError as e:
                        st.error(f"Error loading analysis data: {e}")
                    except Exception as e:
                        st.error(f"Error displaying analysis: {e}")
                    break  # Only show one analysis at a time
            
            # Display resume outside expander for full width
            for analysis in analyses:
                resume_key = f"show_resume_{analysis['id']}"
                if st.session_state.get(resume_key, False):
                    st.markdown("---")
                    
                    # Get resume data from session state
                    resume_content_b64 = st.session_state.get('current_resume_content_b64')
                    resume_filename = st.session_state.get('current_resume_filename') 
                    resume_path = st.session_state.get('current_resume_path')
                    
                    # Try database content first (for new records), then file path (for old records)
                    if resume_content_b64 and resume_filename:
                        display_resume_from_database(resume_content_b64, resume_filename)
                    elif resume_path and Path(resume_path).exists():
                        display_original_resume(resume_path)
                    elif resume_path:
                        # File path exists but file is missing (common in deployment)
                        st.header("📄 Original Resume")
                        st.error("⚠️ Resume file not found in deployment environment")
                        st.info(f"**Expected Path:** {resume_path}")
                        st.info("💡 **Note:** This resume was uploaded before we added database storage. The file was stored locally but deployment environments don't persist files.")
                        st.markdown("""
                        **To access this resume:**
                        1. Re-upload the same resume to get it stored in the database
                        2. The new upload will have download capability in deployment
                        """)
                    else:
                        st.error("No resume content available")
                    
                    # Add a button to hide the resume
                    if st.button("❌ Hide Resume", key=f"hide_resume_{analysis['id']}"):
                        st.session_state[resume_key] = False
                        # Clean up session state
                        for key in ['current_resume_path', 'current_resume_content_b64', 'current_resume_filename']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    break  # Only show one resume at a time
            
    except Exception as e:
        st.error(f"Error loading analyses: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

# Page config
st.set_page_config(
    page_title="Resume Intelligence AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal CSS - let Streamlit handle dark mode
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Fix metric text overflow only */
    .metric-container .metric-value {
        font-size: 1.2rem !important;
        word-wrap: break-word;
        max-width: 100%;
    }
    
    /* Remove info/success box custom colors - let Streamlit handle it */
    .success-box, .info-box {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit app"""
    
    # Check authentication first
    if not simple_auth():
        return  # Show login/register forms
    
    # Sidebar navigation
    st.sidebar.title("🚀 Resume AI")
    st.sidebar.write(f"Welcome, {st.session_state.user_email}!")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Navigation menu
    page = st.sidebar.selectbox(
        "📁 Choose a page:",
        ["🏠 Upload & Analyze", "💾 My Saved Analyses", "📊 Analytics Dashboard", "⚙️ Settings"]
    )
    
    if page == "🏠 Upload & Analyze":
        upload_and_analyze_page()
    elif page == "💾 My Saved Analyses":
        show_user_analyses()
    elif page == "📊 Analytics Dashboard":
        analytics_dashboard_page()
    elif page == "⚙️ Settings":
        settings_page()

def upload_and_analyze_page():
    """Main upload and analysis page"""
    
    st.markdown('<h1 class="main-header">🚀 Resume Intelligence AI</h1>', unsafe_allow_html=True)
    st.markdown("Upload a resume and get instant AI-powered analysis")
    
    # File upload
    uploaded_file = st.file_uploader(
        "📄 Upload Resume (PDF, DOCX, TXT)",
        type=['pdf', 'docx', 'txt'],
        help="Upload your resume in PDF, Word, or text format"
    )
    
    if uploaded_file is not None:
        process_resume(uploaded_file)

def process_resume(uploaded_file):
    """Process the uploaded resume"""
    
    temp_file_path = None
    
    try:
        # Show file info
        st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        # Extract text
        with st.spinner("📖 Extracting text from document..."):
            extractor = DocumentTextExtractor()
            extraction_result = extractor.extract_text(temp_file_path)
            
            # Handle tuple return (text, metadata) or just text
            if isinstance(extraction_result, tuple):
                extracted_text = extraction_result[0]
            else:
                extracted_text = extraction_result
            
            if not extracted_text or not extracted_text.strip():
                st.error("❌ No text could be extracted from the document")
                return
            
            st.success(f"✅ Extracted {len(extracted_text)} characters")
        
        # AI Analysis
        with st.spinner("🤖 Running AI analysis..."):
            try:
                from secrets_helper import GEMINI_API_KEY
                analysis_result = extract_resume_with_gemini(extracted_text, GEMINI_API_KEY)
                
                if not analysis_result:
                    st.error("❌ AI analysis failed - no result returned")
                    return
                
                # Adapt for storage
                adapted_data = adapt_gemini_output_for_neo4j(analysis_result)
                
                # Display results
                display_analysis_results(adapted_data)
                
                # Save to file
                result_file = save_results_to_file(adapted_data, uploaded_file.name)
                st.info(f"💾 Results saved to: {result_file}")
                
                # Save the original resume file
                resume_file = save_resume_file(uploaded_file)
                if resume_file:
                    st.info(f"📄 Resume saved to: {resume_file}")
                else:
                    st.warning("📄 Resume file could not be saved (analysis still available)")
                
                # Try to save to Neo4j if available and user is authenticated
                if st.session_state.get('authenticated'):
                    with st.spinner("💾 Saving to your profile..."):
                        try_neo4j_storage(adapted_data, str(resume_file) if resume_file else None)
                
            except Exception as analysis_error:
                st.error(f"❌ AI analysis failed: {analysis_error}")
                return
        
    except Exception as e:
        st.error(f"❌ Processing failed: {e}")
        import traceback
        st.error(traceback.format_exc())
    
    finally:
        # Clean up temp file
        if 'temp_file_path' in locals() and temp_file_path:
            try:
                os.unlink(temp_file_path)
            except:
                pass

def try_neo4j_storage(adapted_data, resume_file_path=None):
    """Store analysis linked to authenticated user"""
    
    if not NEO4J_STORAGE_AVAILABLE:
        st.warning("Neo4j storage not available")
        return
    
    try:
        # Get the authenticated user's email
        user_email = st.session_state.user_email
        
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        # Try to store resume content as base64 for deployment environments
        resume_content_b64 = None
        resume_filename = None
        
        if resume_file_path and Path(resume_file_path).exists():
            try:
                with open(resume_file_path, 'rb') as f:
                    import base64
                    resume_content_b64 = base64.b64encode(f.read()).decode('utf-8')
                    resume_filename = Path(resume_file_path).name
                st.info("📦 Resume content stored in database for deployment compatibility")
            except Exception as e:
                st.warning(f"Could not store resume content: {e}")
        
        with neo4j_connection.get_session() as session:
            # Create analysis record linked to user
            analysis_id = str(uuid.uuid4())
            session.run("""
                MATCH (u:User {email: $email})
                CREATE (a:Analysis {
                    id: $analysis_id,
                    created_at: datetime(),
                    data: $analysis_data,
                    resume_name: $resume_name,
                    resume_file_path: $resume_file_path,
                    resume_content_b64: $resume_content_b64,
                    resume_filename: $resume_filename
                })
                CREATE (u)-[:HAS_ANALYSIS]->(a)
                RETURN a
            """, {
                'email': user_email,
                'analysis_id': analysis_id,
                'analysis_data': json.dumps(adapted_data),
                'resume_name': adapted_data.get('personal_info', {}).get('name', 'Unknown'),
                'resume_file_path': resume_file_path,
                'resume_content_b64': resume_content_b64,
                'resume_filename': resume_filename
            })
            
        st.success(f"Analysis saved to your profile!")
        st.info(f"Saved for: {user_email}")
        
    except Exception as e:
        st.error(f"Save failed: {e}")

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
    
    # Work Experience (includes internships and other experience)
    experience = analysis_data.get('experience', [])
    internships = analysis_data.get('internships', [])
    
    # Combine all experience types, avoiding duplicates
    all_experience = []
    if experience:
        all_experience.extend(experience)
    
    if internships:
        # Add internships that aren't already in experience array
        for internship in internships:
            # Check if this internship is already in experience by comparing key fields
            is_duplicate = False
            for exp in experience:
                if (exp.get('company') == internship.get('company') and 
                    exp.get('role') == internship.get('role') and
                    exp.get('duration') == internship.get('duration')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_experience.append(internship)
    
    if all_experience:
        st.subheader("💼 Work Experience")
        
        for i, exp in enumerate(all_experience):
            # Determine title based on available fields
            company = exp.get('company', f'Experience {i+1}')
            role = exp.get('role', exp.get('position', 'Role not specified'))
            exp_type = exp.get('type', 'internship' if 'internship' in str(exp).lower() else 'experience')
            
            # Create display title
            if exp_type == 'internship':
                title = f"🎓 {role} - {company} (Internship)"
            else:
                title = f"🏢 {role} - {company}"
            
            with st.expander(title):
                st.write(f"**Duration:** {exp.get('duration', 'Not specified')}")
                st.write(f"**Status:** {exp.get('status', 'Not specified').title()}")
                
                # Handle both 'responsibilities' and 'description' fields
                description = exp.get('responsibilities', exp.get('description', 'No description'))
                st.write(f"**Description:** {description}")
                
                # Technologies used
                technologies = exp.get('technologies', [])
                if technologies:
                    st.write(f"**Technologies:** {', '.join(technologies)}")
                
                # Skills used (alternative field name)
                skills_used = exp.get('skills_used', [])
                if skills_used:
                    st.write(f"**Skills Used:** {', '.join(skills_used)}")
                
                # Achievements if available
                achievements = exp.get('achievements', [])
                if achievements:
                    st.write("**Key Achievements:**")
                    for achievement in achievements:
                        st.write(f"• {achievement}")
    
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
    
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        with neo4j_connection.get_session() as session:
            # Get total analyses count
            analyses_result = session.run("MATCH (a:Analysis) RETURN count(a) as total_analyses")
            total_analyses = analyses_result.single()['total_analyses']
            
            # Get unique users count
            users_result = session.run("MATCH (u:User) RETURN count(u) as total_users")
            total_users = users_result.single()['total_users']
            
            # Get unique skills count (approximate from analysis data)
            skills_result = session.run("""
                MATCH (a:Analysis)
                WITH a.data as analysis_data
                WHERE analysis_data IS NOT NULL
                RETURN count(a) as analyses_with_skills
            """)
            analyses_with_skills = skills_result.single()['analyses_with_skills']
            
            # Estimate unique skills (rough calculation)
            estimated_skills = analyses_with_skills * 12  # Average skills per resume
            
            # Get analyses from last 30 days
            recent_result = session.run("""
                MATCH (a:Analysis)
                WHERE a.created_at >= datetime() - duration('P30D')
                RETURN count(a) as recent_analyses
            """)
            recent_analyses = recent_result.single()['recent_analyses']
        
        # Show metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Analyses", total_analyses)
        with col2:
            st.metric("👥 Registered Users", total_users)
        with col3:
            st.metric("🛠️ Est. Skills Found", estimated_skills)
        with col4:
            st.metric("📅 Recent (30 days)", recent_analyses)
        
        # Additional insights
        if total_analyses > 0:
            st.markdown("---")
            st.subheader("📊 Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_per_user = total_analyses / max(total_users, 1)
                st.metric("📈 Avg Analyses per User", f"{avg_per_user:.1f}")
            
            with col2:
                if recent_analyses > 0:
                    st.metric("🔥 Activity Level", "Active" if recent_analyses >= 5 else "Moderate")
                else:
                    st.metric("🔥 Activity Level", "Low")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        # Fallback to static numbers
        st.info("🚧 Using sample data - database connection issue")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Analyses", "0")
        with col2:
            st.metric("👥 Registered Users", "0") 
        with col3:
            st.metric("🛠️ Est. Skills Found", "0")
        with col4:
            st.metric("📅 Recent (30 days)", "0")

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

def save_resume_file(uploaded_file):
    """Save the uploaded resume file to local storage"""
    
    # Try to create resumes directory in multiple possible locations
    possible_dirs = [
        Path("resumes"),
        Path("/tmp/resumes"),
        Path.home() / "resumes",
        Path("/app/resumes")  # Common in containerized deployments
    ]
    
    resumes_dir = None
    for dir_path in possible_dirs:
        try:
            dir_path.mkdir(exist_ok=True, parents=True)
            # Test if we can write to this directory
            test_file = dir_path / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            resumes_dir = dir_path
            break
        except Exception:
            continue
    
    if not resumes_dir:
        # Fallback to temp directory
        resumes_dir = Path(tempfile.gettempdir()) / "resumes"
        resumes_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(uploaded_file.name).suffix
    base_name = Path(uploaded_file.name).stem
    resume_filename = resumes_dir / f"{base_name}_{timestamp}{file_extension}"
    
    try:
        # Save the file
        with open(resume_filename, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        st.info(f"📄 Resume saved to: {resume_filename}")
        return resume_filename
        
    except Exception as e:
        st.warning(f"Could not save resume file: {e}")
        return None

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