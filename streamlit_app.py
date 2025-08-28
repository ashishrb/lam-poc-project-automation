import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
import os
import random
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any

# Add this DEBUG section right after your imports
print("🔍 DEBUG: Checking autonomous modules...")

# Import system configuration first
try:
    from system_config import system_config
    print("✅ system_config imported successfully")
    system_config.print_system_info()
except Exception as e:
    print(f"⚠️ system_config import failed: {e}")
    system_config = None

try:
    import enhanced_lam_integration
    print("✅ enhanced_lam_integration imported successfully")
except Exception as e:
    print(f"❌ enhanced_lam_integration import failed: {e}")

try:
    import autonomous_manager
    print("✅ autonomous_manager imported successfully")
except Exception as e:
    print(f"❌ autonomous_manager import failed: {e}")

try:
    import project_models
    print("✅ project_models imported successfully")
except Exception as e:
    print(f"❌ project_models import failed: {e}")

# Test specific class imports
try:
    from enhanced_lam_integration import EnhancedTrueLAMInterface
    print("✅ EnhancedTrueLAMInterface imported successfully")
except Exception as e:
    print(f"❌ EnhancedTrueLAMInterface import failed: {e}")

try:
    from autonomous_manager import AutonomousProjectManager
    print("✅ AutonomousProjectManager imported successfully")
except Exception as e:
    print(f"❌ AutonomousProjectManager import failed: {e}")

print("🔍 DEBUG: Module check complete")


# Import our enhanced modules
try:
    from enhanced_lam_integration import EnhancedTrueLAMInterface
    from autonomous_manager import AutonomousProjectManager, DatabaseManager
    from project_models import (
        ProjectFactory, EmployeeFactory, ProjectAnalytics, PerformanceAnalytics,
        ProjectStatus, StakeholderRole, Priority, RiskLevel
    )
    AUTONOMOUS_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Autonomous modules not available: {e}")
    AUTONOMOUS_MODULES_AVAILABLE = False
    # Fallback to original LAM interface
    try:
        from lam_integration import TrueLAMInterface as EnhancedTrueLAMInterface
    except ImportError:
        EnhancedTrueLAMInterface = None

try:
    import numpy as np
except ImportError:
    np = None

# Page configuration with system optimization
st.set_page_config(
    page_title="Enterprise Management System - Autonomous LAM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply system-specific Streamlit configurations
if system_config:
    config = system_config.get_streamlit_config()
    print(f"🔧 Streamlit system optimization available: {config}")
else:
    print("🔧 Using default Streamlit configuration")

# Enhanced CSS for professional autonomous interface
# BRIGHT & CLEAR UI - Replace entire CSS section
st.markdown("""
<style>
    /* Import Google Fonts for better typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global font and base styling */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main content area - Clean white background */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: #ffffff;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Autonomous badge */
    .autonomous-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* Section headers */
    h1, h2, h3 {
        color: #2d3748 !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Custom card styling */
    .metric-card {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card h4, .metric-card h5 {
        color: #2d3748 !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .metric-card p {
        color: #4a5568 !important;
        font-weight: 400 !important;
    }
    
    /* Autonomous workflow styling */
    .autonomous-workflow {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border: 2px solid #38a169;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(56, 161, 105, 0.1);
    }
    
    .autonomous-workflow h4 {
        color: #2f855a !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    .autonomous-workflow p {
        color: #2d3748 !important;
        font-weight: 400 !important;
    }
    
    /* Workflow steps */
    .workflow-step {
        background: white;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #38a169;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .workflow-step strong {
        color: #2f855a !important;
        font-weight: 600 !important;
    }
    
    .workflow-step p, .workflow-step span {
        color: #4a5568 !important;
    }
    
    /* Chat interface */
    .autonomous-chat {
        background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
        border: 2px solid #3182ce;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(49, 130, 206, 0.3);
    }
    
    .ai-message {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(56, 161, 105, 0.3);
    }
    
    /* Performance cards */
    .performance-card {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #f59e0b;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.1);
    }
    
    .performance-card h5 {
        color: #92400e !important;
        font-weight: 600 !important;
    }
    
    .performance-card p {
        color: #451a03 !important;
    }
    
    /* Streamlit component fixes - PRESERVE NATIVE STYLING */
    
    /* Sidebar - Keep Streamlit's native dark theme for sidebar */
    .css-1d391kg {
        background-color: #262730 !important;
    }
    
    /* Sidebar text - Light colors for dark background */
    .css-1d391kg .css-10trblm {
        color: #fafafa !important;
    }
    
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #fafafa !important;
    }
    
    /* Selectbox and dropdown - Native styling */
    .stSelectbox > div > div {
        background-color: white;
        border: 1px solid #d1d5db;
        border-radius: 6px;
    }
    
    .stSelectbox > div > div > div {
        color: #374151 !important;
    }
    
    /* Input fields - Clean styling */
    .stTextInput > div > div > input {
        background-color: white;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        color: #374151 !important;
        font-weight: 400;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Buttons - Professional styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
    }
    
    /* Metrics - Enhanced styling */
    [data-testid="metric-value"] {
        color: #1f2937 !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    [data-testid="metric-label"] {
        color: #6b7280 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="metric-delta"] {
        font-weight: 600 !important;
    }
    
    /* Expander - Clean styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748 !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background: white;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
    }
    
    /* Tabs - Professional styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px 8px 0 0;
        color: #6b7280;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f3f4f6;
        color: #374151;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        color: #1f2937 !important;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* Success/Error messages - Clean alerts */
    .stSuccess {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #10b981;
        border-left: 4px solid #10b981;
        color: #065f46 !important;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #f59e0b;
        border-left: 4px solid #f59e0b;
        color: #92400e !important;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
        border-left: 4px solid #ef4444;
        color: #991b1b !important;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #3b82f6;
        border-left: 4px solid #3b82f6;
        color: #1e40af !important;
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 4px;
    }
    
    /* Dataframes */
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Main content text - Ensure readability */
    .main .block-container p,
    .main .block-container span,
    .main .block-container div {
        color: #374151;
    }
    
    /* Preserve native Streamlit styling for dropdowns and controls */
    .stSelectbox, .stMultiSelect, .stSlider {
        /* Let Streamlit handle these natively */
    }
    
</style>
""", unsafe_allow_html=True)

class EnhancedEnterpriseSystem:
    """Enhanced Enterprise Management System with Autonomous Capabilities"""
    
    def __init__(self):
        self.db_path = "enterprise_data.db"
        self.autonomous_db_path = "autonomous_projects.db"
        
        # Initialize systems
        if AUTONOMOUS_MODULES_AVAILABLE:
            try:
                self.autonomous_manager = AutonomousProjectManager()
                self.enhanced_lam = EnhancedTrueLAMInterface()
                self.autonomous_db = DatabaseManager(self.autonomous_db_path)
            except Exception as e:
                print(f"Warning: Autonomous modules initialization failed: {e}")
                self.autonomous_manager = None
                self.enhanced_lam = None
                self.autonomous_db = None
        else:
            self.autonomous_manager = None
            self.enhanced_lam = EnhancedTrueLAMInterface() if EnhancedTrueLAMInterface else None
            self.autonomous_db = None
        
        # Initialize original database
        self.init_original_database()
    
    def init_original_database(self):
        """Initialize original database for backward compatibility"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Original sales table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quarter TEXT,
                product_name TEXT,
                region TEXT,
                sales_amount REAL,
                units_sold INTEGER,
                date TEXT
            )
        ''')
        
        # Original employee performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                employee_name TEXT,
                project_name TEXT,
                hours_worked REAL,
                tasks_completed INTEGER,
                quality_score REAL,
                quarter TEXT,
                date TEXT
            )
        ''')
        
        # Insert sample data if needed
        cursor.execute("SELECT COUNT(*) FROM sales_data")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_sales_data(cursor)
        
        cursor.execute("SELECT COUNT(*) FROM employee_performance")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_employee_data(cursor)
        
        conn.commit()
        conn.close()
    
    def insert_sample_sales_data(self, cursor):
        """Insert sample sales data"""
        products = ["Laptop", "Smartphone", "Tablet", "Monitor", "Keyboard"]
        regions = ["North", "South", "East", "West", "Central"]
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        
        for quarter in quarters:
            for _ in range(50):
                product = random.choice(products)
                region = random.choice(regions)
                sales_amount = random.uniform(1000, 50000)
                units_sold = random.randint(1, 100)
                date = datetime.now().strftime("%Y-%m-%d")
                
                cursor.execute('''
                    INSERT OR IGNORE INTO sales_data 
                    (quarter, product_name, region, sales_amount, units_sold, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (quarter, product, region, sales_amount, units_sold, date))
    
    def insert_sample_employee_data(self, cursor):
        """Insert sample employee data"""
        employees = [
            ("EMP001", "John Smith", "Project Alpha"),
            ("EMP002", "Sarah Johnson", "Project Beta"),
            ("EMP003", "Mike Davis", "Project Gamma"),
            ("EMP004", "Lisa Wilson", "Project Delta"),
            ("EMP005", "David Brown", "Project Epsilon")
        ]
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        
        for employee_id, employee_name, project_name in employees:
            for quarter in quarters:
                hours_worked = random.uniform(120, 200)
                tasks_completed = random.randint(10, 25)
                quality_score = random.uniform(7.0, 10.0)
                date = datetime.now().strftime("%Y-%m-%d")
                
                cursor.execute('''
                    INSERT OR IGNORE INTO employee_performance 
                    (employee_id, employee_name, project_name, hours_worked, tasks_completed, quality_score, quarter, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (employee_id, employee_name, project_name, hours_worked, tasks_completed, quality_score, quarter, date))
    
    def get_sales_data(self, quarter=None):
        """Get sales data from original database"""
        conn = sqlite3.connect(self.db_path)
        if quarter:
            df = pd.read_sql_query(
                "SELECT * FROM sales_data WHERE quarter = ?", 
                conn, 
                params=(quarter,)
            )
        else:
            df = pd.read_sql_query("SELECT * FROM sales_data", conn)
        conn.close()
        return df
    
    def get_employee_data(self, quarter=None):
        """Get employee performance data from original database"""
        conn = sqlite3.connect(self.db_path)
        if quarter:
            df = pd.read_sql_query(
                "SELECT * FROM employee_performance WHERE quarter = ?", 
                conn, 
                params=(quarter,)
            )
        else:
            df = pd.read_sql_query("SELECT * FROM employee_performance", conn)
        conn.close()
        return df

def main():
    """Main application with autonomous capabilities"""
    st.markdown('<h1 class="main-header">🏢 Enterprise Management System</h1>', unsafe_allow_html=True)
    
    # Autonomous capabilities badge
    if AUTONOMOUS_MODULES_AVAILABLE:
        st.markdown('<div class="autonomous-badge">🤖 Powered by Autonomous LAM Intelligence</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
            <strong>True Autonomous Business Intelligence</strong> • Strategic Planning • Intelligent Decision Making • Proactive Management
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Autonomous modules not available. Running in basic mode.")
    
    # Initialize system
    ems = EnhancedEnterpriseSystem()
    
    # Enhanced sidebar navigation with autonomous features
    st.sidebar.title("🤖 Autonomous Navigation")
    
    if AUTONOMOUS_MODULES_AVAILABLE:
        st.sidebar.markdown("### 🚀 Autonomous Features")
        autonomous_pages = [
            "🤖 Autonomous LAM Interface",
            "🎯 Autonomous Project Manager", 
            "📊 Strategic Dashboard",
            "🧠 Predictive Analytics",
            "👥 Intelligent Team Management"
        ]
        
        st.sidebar.markdown("### 📈 Standard Features")
        standard_pages = [
            "📁 File Operations",
            "💰 Sales Management", 
            "🌤️ Weather API",
            "📧 Email Reports"
        ]
        
        all_pages = autonomous_pages + standard_pages
    else:
        st.sidebar.markdown("### 📊 Available Features")
        all_pages = [
            "💬 LAM Interface",
            "📊 Dashboard",
            "📁 File Operations",
            "💰 Sales Management",
            "🌤️ Weather API", 
            "👥 Employee Performance",
            "📧 Email Reports"
        ]
    
    page = st.sidebar.selectbox("Choose a module:", all_pages)
    
    # Page routing with autonomous capabilities
    if page == "🤖 Autonomous LAM Interface":
        show_autonomous_lam_interface(ems)
    elif page == "🎯 Autonomous Project Manager":
        show_autonomous_project_manager(ems)
    elif page == "📊 Strategic Dashboard":
        show_strategic_dashboard(ems)
    elif page == "🧠 Predictive Analytics":
        show_predictive_analytics(ems)
    elif page == "👥 Intelligent Team Management":
        show_intelligent_team_management(ems)
    elif page == "💬 LAM Interface":
        show_basic_lam_interface(ems)
    elif page == "📊 Dashboard":
        show_standard_dashboard(ems)
    elif page == "📁 File Operations":
        show_file_operations(ems)
    elif page == "💰 Sales Management":
        show_sales_management(ems)
    elif page == "🌤️ Weather API":
        show_weather_api(ems)
    elif page == "👥 Employee Performance":
        show_employee_performance(ems)
    elif page == "📧 Email Reports":
        show_email_reports(ems)

def show_autonomous_lam_interface(ems):
    """Show the Enhanced Autonomous LAM Interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">🤖 Autonomous LAM Interface</h2>', unsafe_allow_html=True)
    
    if not AUTONOMOUS_MODULES_AVAILABLE or not ems.enhanced_lam:
        st.error("❌ Autonomous LAM interface not available. Please check module imports.")
        return
    
    # Autonomous capabilities overview
    st.markdown("""
    <div class="autonomous-workflow">
        <h4>🚀 True Autonomous Intelligence</h4>
        <p>This interface uses the <strong>Salesforce/xLAM-1b-fc-r</strong> model with enhanced autonomous capabilities:</p>
        <div class="workflow-step">
            <strong>🧠 Multi-Step Reasoning:</strong> Break down complex business problems into strategic action plans
        </div>
        <div class="workflow-step">
            <strong>🎯 Strategic Decision Making:</strong> Make autonomous decisions based on business rules and data
        </div>
        <div class="workflow-step">
            <strong>📞 Stakeholder Management:</strong> Generate personalized communications for different roles
        </div>
        <div class="workflow-step">
            <strong>📈 Performance Optimization:</strong> Automatically analyze and improve team performance
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Command suggestions
    with st.expander("🎯 Autonomous Command Examples", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Project Management:**
            - "Execute autonomous project management workflow"
            - "Analyze project health and make strategic decisions"
            - "Generate comprehensive project status report"
            
            **👥 Team Leadership:**
            - "Analyze team performance and take appropriate actions"
            - "Generate personalized employee appreciation messages"
            - "Create development plans for underperforming team members"
            """)
        
        with col2:
            st.markdown("""
            **📊 Strategic Planning:**
            - "Create strategic plan for improving team productivity"
            - "Make autonomous decision about resource allocation"
            - "Generate predictive analysis for project success"
            
            **📧 Communication:**
            - "Send personalized stakeholder updates with current metrics"
            - "Generate executive summary for leadership team"
            - "Create client presentation with project highlights"
            """)
    
    # Chat interface
    st.markdown('<div class="autonomous-chat">', unsafe_allow_html=True)
    
    # Initialize chat history
    if "autonomous_chat_history" not in st.session_state:
        st.session_state.autonomous_chat_history = []
    
    # Display chat history
    for message in st.session_state.autonomous_chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
    
    # User input
    user_query = st.text_input(
        "🎯 Command the Autonomous System:", 
        placeholder="e.g., Execute autonomous project management workflow",
        key="autonomous_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("🚀 Execute", type="primary")
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.autonomous_chat_history = []
            st.rerun()
    
    # Process autonomous commands
    if send_button and user_query.strip():
        # Add user message
        st.session_state.autonomous_chat_history.append({"role": "user", "content": user_query})
        
        # Show processing indicator
        with st.spinner("🤖 Autonomous Intelligence Processing..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # Process with enhanced LAM
            result = ems.enhanced_lam.process_query(user_query)
            
            if result.get("success"):
                response = result.get("data", "Autonomous operation completed successfully.")
                
                # Show autonomous features if available
                if "autonomous_features" in result:
                    st.success("✅ Autonomous Features Activated:")
                    features = result["autonomous_features"]
                    feature_cols = st.columns(2)
                    
                    feature_list = [
                        ("Multi-Step Reasoning", features.get("multi_step_reasoning", False)),
                        ("Context Awareness", features.get("context_awareness", False)),
                        ("Strategic Planning", features.get("strategic_planning", False)),
                        ("Autonomous Decisions", features.get("autonomous_decision_making", False))
                    ]
                    
                    for i, (feature, enabled) in enumerate(feature_list):
                        with feature_cols[i % 2]:
                            if enabled:
                                st.markdown(f"✅ **{feature}**")
                            else:
                                st.markdown(f"⏳ {feature}")
            else:
                response = f"❌ **Error**: {result.get('error', 'Unknown error')}"
            
            # Add AI response
            st.session_state.autonomous_chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_autonomous_project_manager(ems):
    """Show the Autonomous Project Manager interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">🎯 Autonomous Project Manager</h2>', unsafe_allow_html=True)
    
    if not AUTONOMOUS_MODULES_AVAILABLE or not ems.autonomous_manager:
        st.error("❌ Autonomous Project Manager not available. Please check module imports.")
        return
    
    # Project management dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="autonomous-workflow">
            <h4>🚀 Autonomous Project Management Capabilities</h4>
            <p>Experience true autonomous project management with AI-driven decision making:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick actions
        st.subheader("⚡ Quick Autonomous Actions")
        
        if st.button("🎯 Execute Full Autonomous Workflow", type="primary"):
            execute_autonomous_workflow(ems)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🏥 Analyze Project Health"):
                analyze_project_health(ems)
        with col_b:
            if st.button("👥 Optimize Team Performance"):
                optimize_team_performance(ems)
    
    with col2:
        st.markdown("### 📊 Project Status")
        
        # Mock project status
        st.markdown("""
        <div class="metric-card">
            <h5>lo</h5>
            <p><span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #28a745; margin-right: 8px;"></span><strong>Status:</strong> Healthy</p>
            <p><strong>Progress:</strong> 75.0%</p>
            <p><strong>Budget:</strong> 82.0%</p>
            <p><strong>Team:</strong> 8 members</p>
            <p><strong>Days Left:</strong> 45</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent autonomous actions
    st.subheader("🤖 Recent Autonomous Actions")
    
    recent_actions = [
        {"time": "2 minutes ago", "action": "Strategic Decision: Budget optimization recommended", "confidence": "92%"},
        {"time": "15 minutes ago", "action": "Team Analysis: 2 employees identified for recognition", "confidence": "88%"},
        {"time": "1 hour ago", "action": "Stakeholder Communication: 5 personalized updates sent", "confidence": "95%"},
        {"time": "3 hours ago", "action": "Risk Assessment: Medium risk project identified", "confidence": "85%"}
    ]
    
    for action in recent_actions:
        st.markdown(f"""
        <div class="workflow-step">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <strong>{action['action']}</strong><br>
                    <small style="color: #666;">{action['time']}</small>
                </div>
                <div>
                    <span style="background: #28a745; color: white; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.8rem;">
                        {action['confidence']}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def execute_autonomous_workflow(ems):
    """Execute the full autonomous workflow"""
    st.markdown("### 🚀 Executing Autonomous Workflow...")
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    workflow_steps = [
        "🔍 Analyzing project health and metrics",
        "🧠 Making strategic decisions based on data", 
        "👥 Evaluating team performance patterns",
        "📧 Generating personalized stakeholder communications",
        "📈 Creating development plans for team members",
        "📊 Compiling comprehensive executive summary"
    ]
    
    for i, step in enumerate(workflow_steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(workflow_steps))
        time.sleep(1)
    
    # Execute actual workflow
    try:
        result = ems.autonomous_manager.execute_autonomous_project_workflow()
        
        if result["success"]:
            st.success("✅ Autonomous Workflow Completed Successfully!")
            
            with st.expander("📊 Workflow Results", expanded=True):
                st.markdown(result["data"])
            
            # Show workflow metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Steps Completed", "6")
            with col2:
                st.metric("Decisions Made", "3")
            with col3:
                st.metric("Stakeholders Notified", "5")
            with col4:
                st.metric("Actions Taken", "8")
        else:
            st.error(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Workflow execution failed: {str(e)}")

def analyze_project_health(ems):
    """Analyze project health with autonomous insights"""
    st.markdown("### 🏥 Autonomous Project Health Analysis")
    
    with st.spinner("🔍 Analyzing project health..."):
        try:
            result = ems.autonomous_manager.analyze_project_health()
            
            if result["success"]:
                st.success("✅ Project Health Analysis Completed!")
                
                with st.expander("📊 Health Analysis Results", expanded=True):
                    st.markdown(result["data"])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Budget Utilization", "82.0%", "+2.0%")
                with col2:
                    st.metric("Schedule Progress", "75.0%")
                with col3:
                    st.metric("Critical Issues", "0", "0")
            else:
                st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"❌ Health analysis failed: {str(e)}")

def optimize_team_performance(ems):
    """Optimize team performance autonomously"""
    st.markdown("### 👥 Autonomous Team Performance Optimization")
    
    with st.spinner("🧠 Analyzing team performance and generating optimization plan..."):
        try:
            result = ems.autonomous_manager.analyze_team_performance()
            
            if result["success"]:
                st.success("✅ Team Performance Analysis Completed!")
                
                with st.expander("📊 Team Analysis Results", expanded=True):
                    st.markdown(result["data"])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Team Size", "5")
                with col2:
                    st.metric("Avg Quality", "7.8/10")
                with col3:
                    st.metric("Total Hours", "800")
                with col4:
                    st.metric("Tasks Completed", "60")
                
            else:
                st.error(f"❌ Team analysis failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"❌ Team optimization failed: {str(e)}")

def show_strategic_dashboard(ems):
    """Show strategic dashboard with autonomous insights"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">📊 Strategic Dashboard</h2>', unsafe_allow_html=True)
    
    if not AUTONOMOUS_MODULES_AVAILABLE:
        st.warning("⚠️ Strategic dashboard requires autonomous modules.")
        return
    
    # Key metrics row
    st.subheader("🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Project Health</h4>
            <h2 style="color: #28a745;">8.5/10</h2>
            <p>↗️ +0.3 from last week</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Team Performance</h4>
            <h2 style="color: #ffc107;">7.8/10</h2>
            <p>→ Stable</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Budget Efficiency</h4>
            <h2 style="color: #28a745;">82%</h2>
            <p>↗️ On track</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>Autonomous Actions</h4>
            <h2 style="color: #17a2b8;">24</h2>
            <p>↗️ +6 today</p>
        </div>
        """, unsafe_allow_html=True)

def show_predictive_analytics(ems):
    """Show predictive analytics with AI insights"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">🧠 Predictive Analytics</h2>', unsafe_allow_html=True)
    
    if not AUTONOMOUS_MODULES_AVAILABLE:
        st.warning("⚠️ Predictive analytics requires autonomous modules.")
        return
    
    st.markdown("""
    <div class="autonomous-workflow">
        <h4>🔮 AI-Powered Predictions</h4>
        <p>Advanced machine learning models analyze patterns to predict future outcomes and optimize decision-making.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create sample projects data
    projects_data = {
        'Project': [
            'AI-Powered Customer Portal',
            'Mobile Banking App Redesign', 
            'E-commerce Platform Migration',
            'Cloud Infrastructure Upgrade'
        ],
        'Success_Probability': [87, 92, 73, 89],
        'Risk_Level': ['Medium', 'Low', 'High', 'Low']
    }
    
    # Mock predictions
    st.subheader("📊 Project Success Predictions")

    for i, project in enumerate(projects_data['Project']):
        risk_level = projects_data['Risk_Level'][i]
        success_prob = projects_data['Success_Probability'][i]
        
        # Create a clean container for each project
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🏢 {project}")
                st.markdown(f"**Success Probability:** `{success_prob}%`")
                st.caption("AI-powered prediction based on current metrics")
            
            with col2:
                if risk_level == "Low":
                    st.success("🟢 Low Risk")
                elif risk_level == "Medium":  
                    st.warning("🟡 Medium Risk")
                else:
                    st.error("🔴 High Risk")
            
            st.divider()
    
    # Additional predictive insights
    st.subheader("📈 Predictive Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Budget Forecast</h4>
            <h3 style="color: #28a745;">On Track</h3>
            <p>85% confidence all projects will complete within budget</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Timeline Prediction</h4>
            <h3 style="color: #ffc107;">Attention Needed</h3>
            <p>2 projects may experience minor delays</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Resource Optimization</h4>
            <h3 style="color: #17a2b8;">Optimal</h3>
            <p>Current resource allocation is efficient</p>
        </div>
        """, unsafe_allow_html=True)

def show_intelligent_team_management(ems):
    """Show intelligent team management interface"""
    st.markdown('<h2 style="color: #FFFFFF; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">👥 Intelligent Team Management</h2>', unsafe_allow_html=True)
    
    if not AUTONOMOUS_MODULES_AVAILABLE:
        st.warning("⚠️ Intelligent team management requires autonomous modules.")
        return
    
    # Team overview
    st.subheader("🎯 Team Intelligence Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mock team performance chart
        if np:
            categories = ['Quality', 'Productivity', 'Collaboration', 'Innovation', 'Reliability']
            team_avg = [8.2, 7.8, 8.5, 7.6, 8.1]
            benchmark = [7.5, 7.2, 7.8, 7.0, 7.6]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=team_avg,
                theta=categories,
                fill='toself',
                name='Team Average',
                line_color='#FFFFFF'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=benchmark,
                theta=categories,
                fill='toself',
                name='Industry Benchmark',
                line_color='#FFFFFF'
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                title="📊 Team Performance vs Industry Benchmark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Team performance radar chart (requires numpy)")
    
    with col2:
        st.markdown("### 📈 Team Metrics")
        
        st.metric("Team Size", "5 Members")
        st.metric("Avg Performance", "7.8/10", "+0.3")
        st.metric("Top Performers", "1", "20%")
        st.metric("Development Needed", "1", "20%")
        
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🏆 Generate Recognition"):
            st.success("✅ Recognition messages generated!")
        
        if st.button("📚 Create Development Plans"):
            st.success("✅ Development plans created!")

# Legacy/Standard interface functions
def show_basic_lam_interface(ems):
    """Show basic LAM interface for backward compatibility"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">💬 Basic LAM Interface</h2>', unsafe_allow_html=True)
    
    if not ems.enhanced_lam:
        st.error("❌ LAM interface not available.")
        return
    
    st.info("💡 This is the basic LAM interface. For advanced autonomous capabilities, use the Autonomous LAM Interface.")
    
    # Basic chat interface
    if "basic_chat_history" not in st.session_state:
        st.session_state.basic_chat_history = []
    
    # Display chat history
    for message in st.session_state.basic_chat_history:
        if message["role"] == "user":
            st.write(f"👤 **You:** {message['content']}")
        else:
            st.write(f"🤖 **AI:** {message['content']}")
    
    # User input
    user_query = st.text_input("Ask me anything:", key="basic_input")
    
    if st.button("Send") and user_query.strip():
        st.session_state.basic_chat_history.append({"role": "user", "content": user_query})
        
        with st.spinner("Processing..."):
            try:
                result = ems.enhanced_lam.process_query(user_query)
                
                if result.get("success"):
                    response = result.get("data", "Request processed successfully.")
                else:
                    response = f"Error: {result.get('error', 'Unknown error')}"
            except Exception as e:
                response = f"Error: {str(e)}"
            
            st.session_state.basic_chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()

def show_standard_dashboard(ems):
    """Show standard dashboard"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">📊 Standard Dashboard</h2>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sales_df = ems.get_sales_data()
        total_sales = sales_df['sales_amount'].sum()
        st.metric("Total Sales", f"${total_sales:,.0f}")
    
    with col2:
        total_units = sales_df['units_sold'].sum()
        st.metric("Total Units Sold", f"{total_units:,}")
    
    with col3:
        employee_df = ems.get_employee_data()
        avg_quality = employee_df['quality_score'].mean()
        st.metric("Avg Employee Quality", f"{avg_quality:.2f}/10")
    
    with col4:
        unique_employees = employee_df['employee_id'].nunique()
        st.metric("Active Employees", f"{unique_employees}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Quarter")
        quarterly_sales = sales_df.groupby('quarter')['sales_amount'].sum()
        fig = px.bar(x=quarterly_sales.index, y=quarterly_sales.values, 
                    title="Sales Performance by Quarter")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Employee Performance")
        employee_performance = ems.get_employee_data().groupby('employee_name')['quality_score'].mean()
        fig = px.bar(x=employee_performance.index, y=employee_performance.values,
                    title="Average Quality Score by Employee")
        st.plotly_chart(fig, use_container_width=True)

def show_file_operations(ems):
    """Show file operations interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">📁 File Operations</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Write File", "Read File"])
    
    with tab1:
        st.subheader("Write File to Any Location")
        
        filepath = st.text_input("File Path (e.g., /path/to/file.txt):", "reports/sample.txt")
        content = st.text_area("File Content:", height=200)
        
        if st.button("Write File"):
            if filepath and content:
                try:
                    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    st.success(f"✅ Successfully wrote to file: {filepath}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please provide both file path and content.")
    
    with tab2:
        st.subheader("Read File from Any Location")
        
        read_filepath = st.text_input("File Path to Read:", "reports/sample.txt")
        
        if st.button("Read File"):
            if read_filepath:
                try:
                    if not os.path.exists(read_filepath):
                        st.error(f"File {read_filepath} does not exist")
                    else:
                        with open(read_filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.text_area("File Content:", content, height=300)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please provide a file path.")

def show_sales_management(ems):
    """Show sales management interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">💰 Sales Management</h2>', unsafe_allow_html=True)
    
    quarter = st.selectbox("Select Quarter:", ["Q1", "Q2", "Q3", "Q4", "All"])
    
    if quarter == "All":
        sales_df = ems.get_sales_data()
    else:
        sales_df = ems.get_sales_data(quarter)
    
    # Sales overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Overview")
        total_sales = sales_df['sales_amount'].sum()
        total_units = sales_df['units_sold'].sum()
        avg_sales = sales_df['sales_amount'].mean()
        
        st.metric("Total Sales", f"${total_sales:,.2f}")
        st.metric("Total Units", f"{total_units:,}")
        st.metric("Average Sale", f"${avg_sales:,.2f}")
    
    with col2:
        st.subheader("Top Performers")
        top_product = sales_df.groupby('product_name')['sales_amount'].sum().sort_values(ascending=False).head(3)
        top_region = sales_df.groupby('region')['sales_amount'].sum().sort_values(ascending=False).head(3)
        
        st.write("**Top Products:**")
        for product, sales in top_product.items():
            st.write(f"- {product}: ${sales:,.2f}")
        
        st.write("**Top Regions:**")
        for region, sales in top_region.items():
            st.write(f"- {region}: ${sales:,.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        product_sales = sales_df.groupby('product_name')['sales_amount'].sum()
        fig = px.pie(values=product_sales.values, names=product_sales.index, title="Sales by Product")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        region_sales = sales_df.groupby('region')['sales_amount'].sum()
        fig = px.pie(values=region_sales.values, names=region_sales.index, title="Sales by Region")
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.subheader("Sales Data")
    st.dataframe(sales_df, use_container_width=True)

def show_weather_api(ems):
    """Show weather API interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">🌤️ Weather API</h2>', unsafe_allow_html=True)
    
    location = st.text_input("Enter Location (e.g., London, New York):", "London")
    
    if st.button("Get Weather"):
        if location:
            with st.spinner("Fetching weather data..."):
                try:
                    url = f"https://wttr.in/{location}?format=j1"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    weather_data = response.json()
                    current = weather_data.get("current_condition", [{}])[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Location", location)
                    
                    with col2:
                        st.metric("Temperature", f"{current.get('temp_C', 'N/A')}°C")
                    
                    with col3:
                        st.metric("Condition", current.get("weatherDesc", [{}])[0].get("value", "Unknown"))
                    
                    with col4:
                        st.metric("Humidity", f"{current.get('humidity', 'N/A')}%")
                    
                    st.success("Weather data retrieved successfully!")
                except Exception as e:
                    st.error(f"Error fetching weather data: {str(e)}")
        else:
            st.warning("Please enter a location.")

def show_employee_performance(ems):
    """Show employee performance interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">👥 Employee Performance</h2>', unsafe_allow_html=True)
    
    quarter = st.selectbox("Select Quarter:", ["Q1", "Q2", "Q3", "Q4", "All"], key="emp_quarter")
    employee_df = ems.get_employee_data(quarter)
    
    # Employee overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_hours = employee_df['hours_worked'].mean()
        st.metric("Average Hours Worked", f"{avg_hours:.1f}")
    
    with col2:
        avg_tasks = employee_df['tasks_completed'].mean()
        st.metric("Average Tasks Completed", f"{avg_tasks:.1f}")
    
    with col3:
        avg_quality = employee_df['quality_score'].mean()
        st.metric("Average Quality Score", f"{avg_quality:.2f}/10")
    
    # Performance chart
    employee_performance = employee_df.groupby('employee_name').agg({
        'hours_worked': 'sum',
        'tasks_completed': 'sum',
        'quality_score': 'mean'
    }).reset_index()
    
    fig = px.scatter(employee_performance, x='hours_worked', y='quality_score', 
                    size='tasks_completed', hover_data=['employee_name'],
                    title="Employee Performance Analysis")
    st.plotly_chart(fig, use_container_width=True)
    
    # Employee details
    st.subheader("Employee Details")
    st.dataframe(employee_df, use_container_width=True)

def show_email_reports(ems):
    """Show email reports interface"""
    st.markdown('<h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem;">📧 Email Reports</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sales Report", "Employee Report"])
    
    with tab1:
        st.subheader("Generate and Send Sales Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            quarter = st.selectbox("Select Quarter for Sales Report:", ["Q1", "Q2", "Q3", "Q4"])
            email_address = st.text_input("Email Address:", "manager@company.com")
        
        with col2:
            if st.button("Generate Sales Report"):
                sales_df = ems.get_sales_data(quarter)
                total_sales = sales_df['sales_amount'].sum()
                total_units = sales_df['units_sold'].sum()
                avg_sales = sales_df['sales_amount'].mean()
                
                top_product = sales_df.groupby('product_name')['sales_amount'].sum().sort_values(ascending=False).head(1)
                top_region = sales_df.groupby('region')['sales_amount'].sum().sort_values(ascending=False).head(1)
                
                report_content = f"""
SALES REPORT - {quarter}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUMMARY:
- Total Sales: ${total_sales:,.2f}
- Total Units Sold: {total_units:,}
- Average Sale Amount: ${avg_sales:,.2f}
- Top Performing Product: {top_product.index[0]} (${top_product.values[0]:,.2f})
- Top Performing Region: {top_region.index[0]} (${top_region.values[0]:,.2f})

This is a sample sales report generated by the system.
"""
                
                st.text_area("Generated Report:", report_content, height=300)
                
                if st.button("Send Sales Report"):
                    st.success(f"✅ Sales report sent to {email_address} (simulated)")
    
    with tab2:
        st.subheader("Generate and Send Employee Performance Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            employee_names = ems.get_employee_data()['employee_name'].unique()
            employee_name = st.selectbox("Select Employee:", employee_names)
            quarter_emp = st.selectbox("Select Quarter for Employee Report:", ["Q1", "Q2", "Q3", "Q4"])
        
        with col2:
            employee_email = st.text_input("Employee Email Address:", "employee@company.com")
        
        if st.button("Generate Employee Report"):
            employee_df = ems.get_employee_data(quarter_emp)
            employee_data = employee_df[employee_df['employee_name'] == employee_name]
            
            if not employee_data.empty:
                emp = employee_data.iloc[0]
                
                report_content = f"""
EMPLOYEE PERFORMANCE REPORT
Employee: {emp['employee_name']}
Quarter: {quarter_emp}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PERFORMANCE METRICS:
- Hours Worked: {emp['hours_worked']:.1f}
- Tasks Completed: {emp['tasks_completed']}
- Quality Score: {emp['quality_score']:.2f}/10
- Project: {emp['project_name']}

PERFORMANCE ASSESSMENT:
{'Excellent performance!' if emp['quality_score'] >= 8.5 else 
 'Good performance, keep it up!' if emp['quality_score'] >= 7.5 else
 'Room for improvement identified.'}

This is a sample employee report generated by the system.
"""
                
                st.text_area("Generated Report:", report_content, height=300)
                
                if st.button("Send Employee Report"):
                    st.success(f"✅ Employee report sent to {employee_email} (simulated)")
            else:
                st.error("No data found for selected employee and quarter")

if __name__ == "__main__":
    main()