import os
import streamlit as st

def get_secret(key, default=None):
    """Get secret from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    # Fallback to environment variables
    return os.getenv(key, default)

# Pre-load all secrets
GEMINI_API_KEY = get_secret('GEMINI_API_KEY')
NEO4J_URI = get_secret('NEO4J_URI')
NEO4J_USER = get_secret('NEO4J_USER')
NEO4J_PASSWORD = get_secret('NEO4J_PASSWORD')
NEO4J_DATABASE = get_secret('NEO4J_DATABASE', 'neo4j')