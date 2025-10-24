#!/usr/bin/env python3
"""
NLP-Powered Job Search Components for Streamlit (Improved Version)
Features:
- Fixed Glassdoor job saving and display
- Better handling of both Reddit and Glassdoor job sources
- Improved job details view for both sources
- Enhanced saved jobs functionality
"""

import time
import uuid
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Import the NLP job discovery system
try:
    from nlp_job_discovery import scrape_jobs_with_nlp, NLPJobDiscoverySystem
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    st.error("⚠️ NLP job discovery system not available. Please install required packages.")

# Import the Glassdoor scraper
try:
    from glassdoor_job_scraper import GlassdoorSeleniumScraper, JobListing
    GLASSDOOR_AVAILABLE = True
except ImportError:
    GLASSDOOR_AVAILABLE = False

def job_search_page():
    """Multi-source job search page with AI and Glassdoor"""
    
    st.header("🔍 Multi-Source Job Search")
    st.markdown("Search jobs from multiple sources: AI-powered Reddit analysis + Glassdoor scraping!")
    
    # Add source selection tabs
    tab1, tab2 = st.tabs(["🧠 AI-Powered (Reddit)", "🏢 Glassdoor Jobs"])
    
    with tab1:
        nlp_job_search_section()
    
    with tab2:
        glassdoor_job_search_section()

def nlp_job_search_section():
    """NLP-powered job search section (existing functionality)"""
    
    st.markdown("### 🧠 AI-Powered Job Discovery")
    st.markdown("Advanced semantic job discovery using state-of-the-art NLP models!")
    
    # Check if NLP system is available
    if not NLP_AVAILABLE:
        st.error("🚫 NLP system is not properly configured.")
        st.info("""
        📋 **Required installations:**
        ```bash
        pip install sentence-transformers transformers torch spacy nltk scikit-learn
        python -m spacy download en_core_web_sm
        ```
        """)
        return
    
    # Search interface with NLP capabilities
    st.markdown("### 🎯 Describe Your Ideal Job")
    search_query = st.text_area(
        "Natural Language Job Description:",
        placeholder="e.g., 'I'm a final year data science student looking for machine learning internships in healthcare. I know Python, TensorFlow, and have experience with medical data analysis.'",
        height=100,
        help="Be specific! The AI will understand context, skills, experience level, and preferences."
    )
    
    # Store in session state
    st.session_state.search_query = search_query
    
    # Advanced search options
    with st.expander("🔧 Advanced Search Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            max_jobs = st.selectbox(
                "Jobs to analyze:",
                [25, 50, 100, 200],
                index=1,
                help="More jobs = better analysis but slower processing"
            )
            st.session_state.max_jobs = max_jobs
            
            priority_subreddits = st.multiselect(
                "Priority subreddits:",
                ["jobs", "forhire", "remotework", "internships", "cscareerquestions", "webdev", "datascience"],
                default=["jobs", "forhire"],
                help="Focus on specific communities"
            )
            st.session_state.priority_subreddits = priority_subreddits
        
        with col2:
            min_confidence = st.slider(
                "Minimum job confidence:",
                0.0, 1.0, 0.30, 0.05,
                help="Higher = more relevant but fewer results"
            )
            st.session_state.min_confidence = min_confidence
            
            experience_preference = st.selectbox(
                "Experience preference:",
                ["No preference", "Entry Level", "Mid Level", "Senior Level"],
                help="Filter by experience level"
            )
            st.session_state.experience_preference = experience_preference
        
        col3, col4 = st.columns(2)
        with col3:
            work_arrangement = st.selectbox(
                "Work arrangement:",
                ["No preference", "Remote only", "Hybrid", "On-site only"],
                help="Filter by work location type"
            )
            st.session_state.work_arrangement = work_arrangement
        
        with col4:
            include_freelance = st.checkbox(
                "Include freelance/contract work",
                value=True,
                help="Include non-permanent positions"
            )
            st.session_state.include_freelance = include_freelance
    
    # Search button
    if st.button("🚀 Start AI Job Discovery", type="primary", use_container_width=True):
        if search_query.strip():
            st.session_state.search_performed = True
            st.session_state.jobs_analyzed = False  # Reset analysis state
            st.rerun()
        else:
            st.error("Please enter a job description first!")
    
    # Show search results
    if st.session_state.get('search_performed', False):
        show_nlp_search_results()

def glassdoor_job_search_section():
    """Glassdoor job search section"""
    
    st.markdown("### 🏢 Search Glassdoor Jobs")
    st.info("Direct job search from Glassdoor with real company postings")
    
    # Check if Glassdoor scraper is available
    if not GLASSDOOR_AVAILABLE:
        st.error("🚫 Glassdoor scraper is not properly configured.")
        st.info("""
        📋 **Required installations:**
        ```bash
        pip install selenium webdriver-manager
        # Install ChromeDriver based on your system
        ```
        """)
        return
    
    # Search form
    with st.form("glassdoor_search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords = st.text_input(
                "Job Keywords:",
                placeholder="e.g., python developer, data scientist",
                help="Enter job titles or keywords to search for"
            )
        
        with col2:
            location = st.text_input(
                "Location:",
                placeholder="e.g., Bangalore, Mumbai, Delhi",
                help="Enter city name for job location"
            )
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            max_pages = st.selectbox(
                "Pages to search:",
                [1, 2, 3, 5],
                index=0,
                help="Number of result pages to scrape"
            )
        
        with col4:
            headless_mode = st.checkbox(
                "Run in background",
                value=True,
                help="Run browser in headless mode (recommended)"
            )
        
        with col5:
            use_india_site = st.checkbox(
                "Use India site",
                value=True,
                help="Use glassdoor.co.in instead of glassdoor.com"
            )
        
        # Credentials section (optional)
        with st.expander("🔐 Login Credentials (Optional)", expanded=False):
            st.info("Login can help bypass some rate limits and access more job details")
            email = st.text_input("Email:", type="default")
            password = st.text_input("Password:", type="password")
            st.warning("⚠️ Credentials are used only for this session and not stored")
        
        submitted = st.form_submit_button("🔍 Search Glassdoor Jobs", type="primary")
    
    # Perform search when form is submitted
    if submitted:
        if not keywords:
            st.error("Please enter job keywords to search")
            return
        
        if not location:
            st.error("Please enter a location")
            return
        
        # Store search parameters in session state
        st.session_state.glassdoor_search_params = {
            'keywords': keywords,
            'location': location,
            'max_pages': max_pages,
            'headless_mode': headless_mode,
            'use_india_site': use_india_site,
            'email': email if email else None,
            'password': password if password else None
        }
        st.session_state.glassdoor_search_performed = True
        st.rerun()
    
    # Show search results if search was performed
    if st.session_state.get('glassdoor_search_performed', False):
        show_glassdoor_search_results()

def show_glassdoor_search_results():
    """Display Glassdoor search results"""
    
    st.markdown("---")
    st.subheader("🏢 Glassdoor Search Results")
    
    search_params = st.session_state.get('glassdoor_search_params', {})
    
    # Show search query
    with st.container():
        st.info(f"🔍 **Searching:** {search_params.get('keywords', '')} in {search_params.get('location', '')}")
    
    # Perform search if not already done
    if not st.session_state.get('glassdoor_jobs_fetched', False):
        
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🌐 Initializing Glassdoor scraper...")
                progress_bar.progress(10)
                
                # Initialize scraper
                scraper = GlassdoorSeleniumScraper(
                    email=search_params.get('email'),
                    password=search_params.get('password'),
                    headless=search_params.get('headless_mode', True),
                    use_india_site=search_params.get('use_india_site', True)
                )
                
                progress_bar.progress(25)
                status_text.text("🔐 Logging in (if credentials provided)...")
                
                # Login if credentials provided
                if search_params.get('email') and search_params.get('password'):
                    scraper.login()
                
                progress_bar.progress(40)
                status_text.text("🔍 Searching for jobs...")
                
                # Search for jobs
                jobs = scraper.search_jobs(
                    keywords=search_params.get('keywords'),
                    location=search_params.get('location'),
                    max_pages=search_params.get('max_pages', 1)
                )
                
                progress_bar.progress(90)
                status_text.text("📊 Processing results...")
                
                # Convert JobListing objects to dictionaries for easier handling
                jobs_data = []
                for job in jobs:
                    job_dict = {
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'salary': job.salary,
                        'description': job.description,
                        'requirements': job.requirements,
                        'job_type': job.job_type,
                        'experience_level': job.experience_level,
                        'technologies': job.technologies,
                        'posted_date': job.posted_date,
                        'application_url': job.application_url,
                        'company_rating': job.company_rating,
                        'remote_type': job.remote_type,
                        'source': 'glassdoor'
                    }
                    jobs_data.append(job_dict)
                
                progress_bar.progress(100)
                
                # Close the scraper
                scraper.close()
                
                # Store results
                st.session_state.glassdoor_jobs = jobs_data
                st.session_state.glassdoor_jobs_fetched = True
                
                # Clear progress indicators
                progress_container.empty()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during Glassdoor search: {str(e)}")
                
                if "Status code was: 127" in str(e):
                    st.error("""
                    🔧 **ChromeDriver Library Issue**
                    
                    This is a known issue with Streamlit Cloud deployment. 
                    The ChromeDriver needs additional system libraries.
                    
                    **Solutions:**
                    1. Check that your `packages.txt` includes all required libraries
                    2. Try redeploying the app (sometimes helps)
                    3. Contact Streamlit support if the issue persists
                    
                    **Temporary workaround:** Use the AI-Powered (Reddit) tab instead.
                    """)
                
                if 'scraper' in locals():
                    scraper.close()
                return
    
    # Display results
    if st.session_state.get('glassdoor_jobs_fetched', False):
        glassdoor_jobs = st.session_state.get('glassdoor_jobs', [])
        
        if glassdoor_jobs:
            st.success(f"🎉 Found {len(glassdoor_jobs)} jobs from Glassdoor!")
            
            # Add filter controls
            with st.expander("🔧 Filter Results", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    experience_filter = st.selectbox(
                        "Experience Level:",
                        ["All"] + list(set([job.get('experience_level', 'Not specified') for job in glassdoor_jobs])),
                        key="glassdoor_exp_filter"
                    )
                
                with col2:
                    remote_filter = st.selectbox(
                        "Remote Type:",
                        ["All"] + list(set([job.get('remote_type', 'Not specified') for job in glassdoor_jobs])),
                        key="glassdoor_remote_filter"
                    )
                
                with col3:
                    job_type_filter = st.selectbox(
                        "Job Type:",
                        ["All"] + list(set([job.get('job_type', 'Not specified') for job in glassdoor_jobs])),
                        key="glassdoor_type_filter"
                    )
            
            # Apply filters
            filtered_jobs = glassdoor_jobs
            if experience_filter != "All":
                filtered_jobs = [job for job in filtered_jobs if job.get('experience_level') == experience_filter]
            if remote_filter != "All":
                filtered_jobs = [job for job in filtered_jobs if job.get('remote_type') == remote_filter]
            if job_type_filter != "All":
                filtered_jobs = [job for job in filtered_jobs if job.get('job_type') == job_type_filter]
            
            st.info(f"Showing {len(filtered_jobs)} of {len(glassdoor_jobs)} jobs")
            
            # Display job cards
            display_glassdoor_job_cards(filtered_jobs)
            
        else:
            st.warning("No jobs found. Try different keywords or location.")

def display_glassdoor_job_cards(jobs):
    """Display Glassdoor jobs in card format"""
    
    for i, job in enumerate(jobs):
        with st.container():
            # Create a card-like container
            with st.expander(f"🏢 {job.get('title', 'Job Title')} at {job.get('company', 'Company')}", expanded=False):
                
                # Job header with key info
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📍 Location", job.get('location', 'Not specified'))
                with col2:
                    st.metric("⭐ Experience", job.get('experience_level', 'Not specified'))
                with col3:
                    st.metric("💼 Type", job.get('job_type', 'Not specified'))
                with col4:
                    if job.get('company_rating'):
                        st.metric("⭐ Rating", f"{job.get('company_rating')}/5")
                    else:
                        st.metric("🏠 Remote", job.get('remote_type', 'Not specified'))
                
                # Salary information
                if job.get('salary'):
                    st.success(f"💰 **Salary:** {job.get('salary')}")
                
                # Technologies
                if job.get('technologies'):
                    tech_tags = " ".join([f"`{tech}`" for tech in job.get('technologies', [])[:8]])
                    st.markdown(f"🛠️ **Technologies:** {tech_tags}")
                
                # Job description preview
                description = job.get('description', '')
                if description:
                    if len(description) > 500:
                        st.markdown(f"📄 **Description:** {description[:500]}...")
                        with st.expander("Read full description"):
                            st.write(description)
                    else:
                        st.markdown(f"📄 **Description:** {description}")
                
                # Requirements
                if job.get('requirements'):
                    st.markdown("📋 **Requirements:**")
                    for req in job.get('requirements', [])[:5]:  # Show first 5 requirements
                        st.markdown(f"• {req}")
                    if len(job.get('requirements', [])) > 5:
                        st.caption(f"... and {len(job.get('requirements', [])) - 5} more requirements")
                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button(f"📋 View Details", key=f"glassdoor_details_{i}", use_container_width=True):
                        st.session_state.selected_job = job
                        st.session_state.show_job_details = True
                        st.rerun()
                
                with col_btn2:
                    if job.get('application_url'):
                        st.link_button(
                            "🔗 Apply on Glassdoor",
                            job.get('application_url'),
                            use_container_width=True
                        )
                    else:
                        st.button("🔗 No Link Available", disabled=True, use_container_width=True)
                
                with col_btn3:
                    if st.button(f"💾 Save Job", key=f"glassdoor_save_{i}", use_container_width=True):
                        save_job_to_session(job)
                
        st.divider()

def init_nlp_job_search_session():
    """Initialize session state for job search"""
    # Original NLP session state
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'jobs_analyzed' not in st.session_state:
        st.session_state.jobs_analyzed = False
    if 'analyzed_jobs' not in st.session_state:
        st.session_state.analyzed_jobs = []
    if 'filtered_jobs' not in st.session_state:
        st.session_state.filtered_jobs = []
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'show_job_details' not in st.session_state:
        st.session_state.show_job_details = False
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    
    # Add Glassdoor session state
    if 'glassdoor_search_performed' not in st.session_state:
        st.session_state.glassdoor_search_performed = False
    if 'glassdoor_jobs_fetched' not in st.session_state:
        st.session_state.glassdoor_jobs_fetched = False
    if 'glassdoor_jobs' not in st.session_state:
        st.session_state.glassdoor_jobs = []
    if 'glassdoor_search_params' not in st.session_state:
        st.session_state.glassdoor_search_params = {}

def show_job_details():
    """Show detailed view of selected job (Enhanced for both Reddit and Glassdoor)"""
    
    if not st.session_state.get('show_job_details', False):
        return
    
    if not st.session_state.get('selected_job'):
        return
    
    job = st.session_state.selected_job
    
    with st.container():
        st.markdown("---")
        st.subheader(f"📋 {job.get('title', 'Job Title')}")
        
        # Basic info - handle both Reddit and Glassdoor jobs
        col1, col2, col3 = st.columns(3)
        with col1:
            location = job.get('location', 'Not specified')
            st.metric("Location", location)
        with col2:
            experience = job.get('experience_level', 'Not specified')
            st.metric("Experience", experience)
        with col3:
            # Handle different remote field names
            remote_status = "No"
            if job.get('remote'):  # Reddit jobs
                remote_status = "Yes"
            elif job.get('remote_type') and job.get('remote_type') != 'on-site':  # Glassdoor jobs
                remote_status = job.get('remote_type', 'No')
            st.metric("Remote", remote_status)
        
        # Show additional metrics for Glassdoor jobs
        if job.get('source') == 'glassdoor':
            col4, col5, col6 = st.columns(3)
            with col4:
                if job.get('company'):
                    st.metric("Company", job.get('company'))
            with col5:
                if job.get('salary'):
                    st.metric("Salary", job.get('salary'))
            with col6:
                if job.get('company_rating'):
                    st.metric("Rating", f"{job.get('company_rating')}/5")
        
        # Job description
        st.markdown("### 📄 Description")
        if job.get('source') == 'glassdoor':
            st.write(job.get('description', 'No description available'))
            
            # Show requirements if available
            if job.get('requirements'):
                st.markdown("### 📋 Requirements")
                for req in job.get('requirements', []):
                    st.markdown(f"• {req}")
            
            # Show technologies if available
            if job.get('technologies'):
                st.markdown("### 🛠️ Technologies")
                tech_cols = st.columns(min(len(job.get('technologies', [])), 4))
                for i, tech in enumerate(job.get('technologies', [])):
                    with tech_cols[i % 4]:
                        st.badge(tech)
        else:
            # Reddit jobs
            st.write(job.get('content', 'No description available'))
        
        # Link to original post
        if job.get('source') == 'glassdoor' and job.get('application_url'):
            st.markdown(f"[Apply on Glassdoor]({job['application_url']})")
        elif job.get('url'):
            st.markdown(f"[View on Reddit]({job['url']})")
        
        # Action buttons based on current page
        current_page = st.session_state.get('current_page', '')
        
        if current_page != 'saved_jobs':
            # Show save button only on job search page
            col_save, col_close = st.columns(2)
            with col_save:
                if st.button("💾 Save Job", key="save_job_detail", type="primary"):
                    save_job_to_session(job)
            with col_close:
                if st.button("❌ Close", key="close_job_detail"):
                    st.session_state.show_job_details = False
                    st.rerun()
        else:
            # Only show close button on saved jobs page
            if st.button("❌ Close", key="close_saved_job_detail"):
                st.session_state.show_job_details = False
                st.rerun()

def save_job_to_neo4j(job: Dict, user_email: str) -> bool:
    """Save a job to Neo4j database with enhanced handling for both Reddit and Glassdoor jobs"""
    
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        # Normalize job data for both sources
        job_data = {
            'job_id': str(uuid.uuid4()),
            'title': job.get('title', 'Unknown Title'),
            'company': job.get('company', job.get('organizations', ['Unknown'])[0] if job.get('organizations') else 'Unknown'),
            'location': job.get('location', 'Not specified'),
            'salary': job.get('salary'),
            'description': job.get('description', job.get('content', 'No description')),
            'url': job.get('application_url', job.get('url', '')),
            'source': job.get('source', 'unknown'),
            'job_type': job.get('job_type', 'Not specified'),
            'experience_level': job.get('experience_level', 'Not specified'),
            'remote_type': job.get('remote_type', 'on-site' if not job.get('remote') else 'remote'),
            'technologies': job.get('technologies', []),
            'requirements': job.get('requirements', []),
            'company_rating': job.get('company_rating'),
            'posted_date': job.get('posted_date', datetime.now().strftime("%Y-%m-%d")),
            'saved_at': datetime.now().isoformat(),
            # Keep Reddit-specific fields for compatibility
            'remote': job.get('remote', False),
            'subreddit': job.get('subreddit', ''),
            'job_confidence': job.get('job_confidence', 0.0),
            'saved_from_query': st.session_state.get('search_query', '')
        }
        
        with neo4j_connection.get_session() as session:
            # Check if job already saved by this user
            existing = session.run("""
                MATCH (u:User {email: $user_email})-[:SAVED]->(j:SavedJob {url: $url})
                RETURN j
            """, {'user_email': user_email, 'url': job_data['url']}).single()
            
            if existing:
                st.warning("Job already saved!")
                return False
            
            # Save the job
            session.run("""
                MATCH (u:User {email: $user_email})
                CREATE (j:SavedJob $job_data)
                CREATE (u)-[:SAVED]->(j)
            """, {'user_email': user_email, 'job_data': job_data})
        
        return True
        
    except Exception as e:
        st.error(f"Error saving job: {str(e)}")
        return False

def load_saved_jobs_from_neo4j(user_email: str) -> List[Dict]:
    """Load saved jobs from Neo4j database"""
    
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        with neo4j_connection.get_session() as session:
            result = session.run("""
                MATCH (u:User {email: $user_email})-[:SAVED]->(j:SavedJob)
                RETURN DISTINCT j
                ORDER BY j.saved_at DESC
            """, {'user_email': user_email})
            
            jobs = []
            for record in result:
                job_node = record['j']
                job = dict(job_node)
                jobs.append(job)
            
            return jobs
            
    except Exception as e:
        st.error(f"Error loading saved jobs: {str(e)}")
        return []

def delete_saved_job_from_neo4j(job_url: str, user_email: str) -> bool:
    """Delete a saved job from Neo4j"""
    
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        with neo4j_connection.get_session() as session:
            session.run("""
                MATCH (u:User {email: $user_email})-[r:SAVED]->(j:SavedJob {url: $url})
                DELETE r, j
            """, {
                'user_email': user_email,
                'url': job_url
            })
            
            return True
            
    except Exception as e:
        st.error(f"Error deleting job: {str(e)}")
        return False

def clear_all_saved_jobs(user_email: str):
    """Clear all saved jobs for a user"""
    try:
        from connection import init_neo4j, neo4j_connection
        init_neo4j()
        
        with neo4j_connection.get_session() as session:
            session.run("""
                MATCH (u:User {email: $user_email})-[r:SAVED]->(j:SavedJob)
                DELETE r, j
            """, {'user_email': user_email})
        
        st.success("All saved jobs cleared!")
        
    except Exception as e:
        st.error(f"Error clearing jobs: {str(e)}")

def saved_jobs_page():
    """Display saved jobs page with enhanced handling for both Reddit and Glassdoor jobs"""
    
    st.header("💾 Saved Jobs")
    st.markdown("Your bookmarked job opportunities from both Reddit and Glassdoor")
    
    user_email = st.session_state.get('user_email')
    if not user_email:
        st.error("Please log in to view saved jobs")
        return
    
    # Load jobs from Neo4j
    saved_jobs = load_saved_jobs_from_neo4j(user_email)
    
    if not saved_jobs:
        st.info("No saved jobs yet. Start searching and save jobs you're interested in!")
        return
    
    # Remove duplicates based on URL
    unique_jobs = []
    seen_urls = set()
    for job in saved_jobs:
        job_url = job.get('url', '')
        if job_url not in seen_urls:
            unique_jobs.append(job)
            seen_urls.add(job_url)
    
    # Display saved jobs count
    st.success(f"You have {len(unique_jobs)} unique saved jobs")
    
    # Sort options
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_option = st.selectbox(
            "Sort by:",
            ["Recently Saved", "Job Confidence", "Job Title", "Source"],
            key="saved_jobs_sort"
        )
    
    with col2:
        if st.button("🗑️ Clear All", key="clear_all_saved_jobs"):
            clear_all_saved_jobs(user_email)
            st.rerun()
    
    with col3:
        st.metric("Total Saved", len(unique_jobs))
    
    # Sort jobs
    if sort_option == "Recently Saved":
        sorted_jobs = sorted(unique_jobs, key=lambda x: x.get('saved_at', ''), reverse=True)
    elif sort_option == "Job Confidence":
        sorted_jobs = sorted(unique_jobs, key=lambda x: x.get('job_confidence', 0), reverse=True)
    elif sort_option == "Source":
        sorted_jobs = sorted(unique_jobs, key=lambda x: x.get('source', ''))
    else:  # Job Title
        sorted_jobs = sorted(unique_jobs, key=lambda x: x.get('title', '').lower())
    
    # Display jobs with enhanced info
    for i, job in enumerate(sorted_jobs):
        with st.container():
            # Job header
            col1, col2 = st.columns([8, 2])
            
            with col1:
                # Show source icon and title
                source_icon = "🏢" if job.get('source') == 'glassdoor' else "🧠"
                st.subheader(f"{source_icon} {job.get('title', 'Job Title')}")
                
                # Basic info with enhanced display for different sources
                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                
                with info_col1:
                    st.caption(f"📍 {job.get('location', 'Not specified')}")
                with info_col2:
                    st.caption(f"⭐ {job.get('experience_level', 'Not specified')}")
                with info_col3:
                    if job.get('source') == 'glassdoor':
                        st.caption(f"🏢 {job.get('company', 'Unknown')}")
                    else:
                        st.caption(f"🏛️ r/{job.get('subreddit', 'unknown')}")
                with info_col4:
                    st.caption(f"🔖 {job.get('source', 'unknown').title()}")
                
                # Show salary if available (Glassdoor jobs)
                if job.get('salary'):
                    st.success(f"💰 {job.get('salary')}")
                
                # Job preview
                content = job.get('description', job.get('content', ''))
                if content:
                    preview = content[:150] + "..." if len(content) > 150 else content
                    st.caption(preview)
            
            with col2:
                # Action buttons
                if st.button("👁️ View Details", key=f"view_saved_job_{i}", use_container_width=True):
                    st.session_state.selected_job = job
                    st.session_state.show_job_details = True
                    st.session_state.current_page = 'saved_jobs'  # Important for button logic
                    st.rerun()
                
                if st.button("🗑️ Remove", key=f"remove_job_{i}", use_container_width=True):
                    if delete_saved_job_from_neo4j(job.get('url', ''), user_email):
                        st.success("Job removed!")
                        st.rerun()
        
        st.divider()

# Additional NLP functions (keeping existing functionality)
def show_nlp_search_results():
    """Display NLP-powered search results"""
    
    st.markdown("---")
    st.subheader("🧠 AI Job Analysis Results")
    
    # Show search query
    with st.container():
        st.info(f"🎯 **AI Understanding:** {st.session_state.search_query}")
    
    # Step 1: NLP Analysis
    if not st.session_state.get('jobs_analyzed', False):
        
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("🧠 AI is analyzing job posts using advanced NLP..."):
                try:
                    # Update progress
                    status_text.text("🔍 Scanning Reddit for job posts...")
                    progress_bar.progress(25)
                    
                    # Call NLP job discovery
                    analyzed_jobs = perform_nlp_job_discovery()
                    progress_bar.progress(75)
                    
                    status_text.text("🎯 Applying semantic matching...")
                    
                    # Apply filters
                    filtered_jobs = apply_nlp_filters(analyzed_jobs)
                    progress_bar.progress(100)
                    
                    st.session_state.analyzed_jobs = analyzed_jobs
                    st.session_state.filtered_jobs = filtered_jobs
                    st.session_state.jobs_analyzed = True
                    
                    # Clear progress indicators
                    progress_container.empty()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during AI analysis: {str(e)}")
                    st.info("💡 Make sure all NLP libraries are properly installed.")
                    return
    
    # Step 2: Display analyzed results
    if st.session_state.get('jobs_analyzed', False):
        analyzed_jobs = st.session_state.get('analyzed_jobs', [])
        filtered_jobs = st.session_state.get('filtered_jobs', [])
        
        if analyzed_jobs:
            # Show analysis statistics
            show_nlp_statistics(analyzed_jobs, filtered_jobs)
            
            # Display the filtered job results
            st.success(f"🎉 Found {len(filtered_jobs)} highly relevant jobs out of {len(analyzed_jobs)} analyzed!")
            
            # Sort by job confidence
            sorted_jobs = sorted(filtered_jobs, 
                               key=lambda x: x.get('job_confidence', 0), 
                               reverse=True)
            
            display_nlp_job_cards(sorted_jobs)
            
        else:
            st.warning("No jobs found. Try adjusting your search criteria or check Reddit API connectivity.")

def show_nlp_statistics(analyzed_jobs: List[Dict], filtered_jobs: List[Dict]):
    """Show statistics about the NLP job analysis"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyzed", len(analyzed_jobs))
    
    with col2:
        st.metric("Highly Relevant", len(filtered_jobs))
    
    with col3:
        if analyzed_jobs:
            avg_confidence = sum(job.get('job_confidence', 0) for job in analyzed_jobs) / len(analyzed_jobs)
            st.metric("Avg Confidence", f"{avg_confidence:.2%}")
        else:
            st.metric("Avg Confidence", "0%")
    
    with col4:
        remote_jobs = sum(1 for job in filtered_jobs if job.get('remote', False))
        st.metric("Remote Jobs", remote_jobs)

def display_nlp_job_cards(jobs: List[Dict]):
    """Display NLP job cards"""
    
    for i, job in enumerate(jobs):
        with st.container():
            # Job confidence indicator
            confidence = job.get('job_confidence', 0)
            confidence_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
            
            with st.expander(f"{confidence_color} {job.get('title', 'Job Title')} ({confidence:.1%} match)", expanded=False):
                
                # Job metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📍 Location", job.get('location', 'Not specified'))
                with col2:
                    work_arr = job.get('work_arrangement', 'unknown')
                    if 'remote' in work_arr.lower():
                        st.caption("🏠 Remote")
                    elif 'on-site' in work_arr.lower():
                        st.caption("🏢 On-site")
                    else:
                        st.caption("📍 Location varies")
                with col3:
                    st.metric("⭐ Experience", job.get('experience_level', 'Not specified'))
                with col4:
                    st.metric("🏛️ Subreddit", f"r/{job.get('subreddit', 'unknown')}")
                
                # Job description preview
                description = job.get('content', 'No description available')
                if description:
                    preview = description[:250] + "..." if len(description) > 250 else description
                    st.caption(preview)
                
                # Extracted technologies and organizations
                col_tech, col_org = st.columns(2)
                with col_tech:
                    technologies = job.get('technologies', [])
                    if technologies:
                        tech_text = ", ".join(technologies[:4])
                        if len(technologies) > 4:
                            tech_text += f" +{len(technologies)-4} more"
                        st.caption(f"🛠️ **Tech Stack:** {tech_text}")
                
                with col_org:
                    organizations = job.get('organizations', [])
                    if organizations:
                        st.caption(f"🏢 **Company:** {organizations[0]}")
                
                # Salary information
                salary = job.get('salary')
                if salary:
                    st.caption(f"💰 **Salary:** {salary}")
                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button(f"📋 View Details", key=f"nlp_details_{i}", use_container_width=True):
                        st.session_state.selected_job = job
                        st.session_state.show_job_details = True
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"🔗 Reddit Post", key=f"nlp_reddit_{i}", use_container_width=True):
                        st.write(f"[View Original Post]({job.get('url', '#')})")
                
                with col_btn3:
                    if st.button(f"💾 Save Job", key=f"nlp_save_{i}", use_container_width=True):
                        save_job_to_session(job)
                
                # Semantic matching details
                if 'semantic_match_score' in job:
                    st.markdown("#### 🧠 Semantic Matching")
                    match_score = job['semantic_match_score']
                    st.progress(match_score)
                    st.caption(f"This job has a {match_score:.2%} semantic similarity to your search query")
        
        st.divider()

def apply_nlp_filters(jobs: List[Dict]) -> List[Dict]:
    """Apply user-specified filters to NLP-analyzed jobs"""
    
    filtered = jobs.copy()
    
    # Confidence filter
    min_confidence = st.session_state.get('min_confidence', 0.3)
    filtered = [job for job in filtered if job.get('job_confidence', 0) >= min_confidence]
    
    # Experience level filter
    exp_pref = st.session_state.get('experience_preference', 'No preference')
    if exp_pref != 'No preference':
        filtered = [job for job in filtered if exp_pref.lower() in job.get('experience_level', '').lower()]
    
    # Work arrangement filter
    work_pref = st.session_state.get('work_arrangement', 'No preference')
    if work_pref == 'Remote only':
        filtered = [job for job in filtered if job.get('remote', False)]
    elif work_pref == 'On-site only':
        filtered = [job for job in filtered if not job.get('remote', False)]
    
    return filtered

def perform_nlp_job_discovery():
    """Perform NLP-powered job discovery"""
    
    if not NLP_AVAILABLE:
        raise Exception("NLP system not available")
    
    search_query = st.session_state.get('search_query', '')
    max_jobs = st.session_state.get('max_jobs', 50)
    
    # Call the NLP job discovery system
    jobs = scrape_jobs_with_nlp(max_jobs, search_query)
    
    return jobs

def save_job_to_session(job: Dict):
    """Save a job to Neo4j database"""
    
    user_email = st.session_state.get('user_email')
    if not user_email:
        st.error("User not logged in")
        return False
    
    success = save_job_to_neo4j(job, user_email)
    
    if success:
        st.success("Job saved to database!")

# Initialize on import
init_nlp_job_search_session()