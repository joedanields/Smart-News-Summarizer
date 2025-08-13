import streamlit as st
import hashlib

class AppConfig:
    def __init__(self):
        self.DEBUG_PASSWORD = "aicte_debug_2024"  # Change this for security
        
    def check_debug_access(self, password):
        """Verify debug mode password"""
        return hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256(self.DEBUG_PASSWORD.encode()).hexdigest()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'app_mode' not in st.session_state:
            st.session_state.app_mode = 'showcase'  # Default to showcase mode
        if 'debug_authenticated' not in st.session_state:
            st.session_state.debug_authenticated = False

config = AppConfig()
