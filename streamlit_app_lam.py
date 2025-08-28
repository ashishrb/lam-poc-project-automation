import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import random
from lam_integration import TrueLAMInterface

# Page configuration
st.set_page_config(
    page_title="Enterprise Management System - True LAM",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .nlp-chat {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        text-align: right;
    }
    .model-message {
        background-color: #e9ecef;
        color: #495057;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        text-align: left;
    }
    .ai-response {
        background-color: #e8f5e8;
        color: #2d5016;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        text-align: left;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

class LAMInterface:
    """True LAM Model Interface using Salesforce/xLAM-1b-fc-r"""
    
    def __init__(self):
        # Initialize the true LAM interface
        self.true_lam = TrueLAMInterface()
    
    def process_natural_language(self, query: str) -> Dict[str, Any]:
        """Process natural language query using true LAM model"""
        return self.true_lam.process_query(query)

class EnterpriseManagementSystem:
    """Enterprise Management System with database operations"""
    
    def __init__(self):
        self.db_path = "enterprise.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the database with tables and dummy data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sales_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quarter TEXT NOT NULL,
                product TEXT NOT NULL,
                sales_amount REAL NOT NULL,
                units_sold INTEGER NOT NULL,
                region TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        
        # Create employee_performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                quarter TEXT NOT NULL,
                hours_worked INTEGER NOT NULL,
                tasks_completed INTEGER NOT NULL,
                quality_score REAL NOT NULL,
                performance_level TEXT NOT NULL,
                project_name TEXT NOT NULL
            )
        ''')
        
        # Insert dummy data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM sales_data")
        if cursor.fetchone()[0] == 0:
            self.insert_dummy_sales_data(cursor)
        
        cursor.execute("SELECT COUNT(*) FROM employee_performance")
        if cursor.fetchone()[0] == 0:
            self.insert_dummy_employee_data(cursor)
        
        conn.commit()
        conn.close()
    
    def insert_dummy_sales_data(self, cursor):
        """Insert dummy sales data for all quarters"""
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        products = ["Smartphones", "Laptops", "Tablets", "Accessories"]
        regions = ["North", "South", "East", "West"]
        
        for quarter in quarters:
            for product in products:
                for region in regions:
                    sales_amount = random.randint(10000, 100000)
                    units_sold = random.randint(50, 500)
                    date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                    
                    cursor.execute('''
                        INSERT INTO sales_data (quarter, product, sales_amount, units_sold, region, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (quarter, product, sales_amount, units_sold, region, date))
    
    def insert_dummy_employee_data(self, cursor):
        """Insert dummy employee performance data"""
        employees = ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"]
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        projects = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"]
        
        for employee in employees:
            for quarter in quarters:
                hours_worked = random.randint(140, 180)
                tasks_completed = random.randint(15, 35)
                quality_score = round(random.uniform(7.0, 9.5), 1)
                performance_level = random.choice(["Excellent", "Good", "Average"])
                project = random.choice(projects)
                
                cursor.execute('''
                    INSERT INTO employee_performance (employee_id, quarter, hours_worked, tasks_completed, quality_score, performance_level, project_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (employee, quarter, hours_worked, tasks_completed, quality_score, performance_level, project))
    
    def get_sales_data(self, quarter=None):
        """Get sales data from database"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM sales_data"
        if quarter:
            query += f" WHERE quarter = '{quarter}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_employee_data(self, quarter=None):
        """Get employee performance data from database"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM employee_performance"
        if quarter:
            query += f" WHERE quarter = '{quarter}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location"""
        try:
            formatted_location = location.replace(" ", "+")
            url = f"https://wttr.in/{formatted_location}?format=j1"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            current = weather_data.get("current_condition", [{}])[0]
            
            result = {
                "location": location,
                "temperature": f"{current.get('temp_C', 'N/A')}°C",
                "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                "humidity": f"{current.get('humidity', 'N/A')}%",
                "wind_speed": f"{current.get('windspeedKmph', 'N/A')} km/h"
            }
            
            return {"success": True, "data": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_file(self, filepath: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {"success": True, "message": f"Successfully wrote content to {filepath}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            if not os.path.exists(filepath):
                return {"success": False, "error": f"File {filepath} does not exist"}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "data": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_sales_report(self, quarter: str) -> str:
        """Generate a sales report for a specific quarter"""
        df = self.get_sales_data(quarter)
        
        if df.empty:
            return f"No sales data found for {quarter}"
        
        total_sales = df['sales_amount'].sum()
        total_units = df['units_sold'].sum()
        avg_sale = total_sales / total_units if total_units > 0 else 0
        
        top_product = df.groupby('product')['sales_amount'].sum().idxmax()
        top_region = df.groupby('region')['sales_amount'].sum().idxmax()
        
        report = f"""
SALES REPORT - {quarter}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SUMMARY:
- Total Sales: ${total_sales:,.2f}
- Total Units Sold: {total_units:,}
- Average Sale: ${avg_sale:.2f}
- Top Product: {top_product}
- Top Region: {top_region}

DETAILED BREAKDOWN:
"""
        
        # Product breakdown
        product_summary = df.groupby('product')['sales_amount'].sum().sort_values(ascending=False)
        report += "\nBy Product:\n"
        for product, sales in product_summary.items():
            report += f"- {product}: ${sales:,.2f}\n"
        
        # Region breakdown
        region_summary = df.groupby('region')['sales_amount'].sum().sort_values(ascending=False)
        report += "\nBy Region:\n"
        for region, sales in region_summary.items():
            report += f"- {region}: ${sales:,.2f}\n"
        
        return report
    
    def generate_employee_report(self, employee_id: str, quarter: str) -> str:
        """Generate an employee performance report"""
        df = self.get_employee_data(quarter)
        employee_data = df[df['employee_id'] == employee_id]
        
        if employee_data.empty:
            return f"No performance data found for {employee_id} in {quarter}"
        
        # Get the latest record for the employee in this quarter
        latest_record = employee_data.iloc[-1]
        
        report = f"""
EMPLOYEE PERFORMANCE REPORT
Employee ID: {employee_id}
Quarter: {quarter}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PERFORMANCE METRICS:
- Hours Worked: {latest_record['hours_worked']}
- Tasks Completed: {latest_record['tasks_completed']}
- Quality Score: {latest_record['quality_score']}/10
- Performance Level: {latest_record['performance_level']}
- Project: {latest_record['project_name']}

RECOMMENDATIONS:
"""
        
        # Generate recommendations based on performance
        if latest_record['quality_score'] >= 8.5:
            report += "- Continue excellent performance\n- Consider leadership opportunities\n- Mentor junior team members\n"
        elif latest_record['quality_score'] >= 7.0:
            report += "- Good performance, focus on skill development\n- Set specific goals for next quarter\n- Seek feedback from supervisors\n"
        else:
            report += "- Focus on improving quality scores\n- Consider additional training\n- Set up regular check-ins with manager\n"
        
        return report
    
    def send_email_report(self, to_email: str, subject: str, content: str, report_type: str = "general") -> Dict[str, Any]:
        """Send an email report"""
        try:
            from email_service import EmailService
            email_service = EmailService()
            
            result = email_service.send_email(
                to_email=to_email,
                subject=subject,
                content=content,
                report_type=report_type
            )
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🏢 Enterprise Management System</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Powered by True Large Action Model (LAM)</p>', unsafe_allow_html=True)
    
    # Initialize systems
    ems = EnterpriseManagementSystem()
    lam_interface = LAMInterface()
    
    # Sidebar navigation
    st.sidebar.title("🤖 Navigation")
    page = st.sidebar.selectbox(
        "Choose a module:",
        ["🤖 True LAM Interface", "📊 Dashboard", "📁 File Operations", "💰 Sales Management", 
         "🌤️ Weather API", "👥 Employee Performance", "📧 Email Reports"]
    )
    
    if page == "🤖 True LAM Interface":
        show_nlp_interface(lam_interface)
    elif page == "📊 Dashboard":
        show_dashboard(ems)
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

def show_nlp_interface(lam_interface):
    """Show the True LAM NLP Interface"""
    st.markdown('<h2 class="section-header">🤖 True LAM Interface</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #e8f5e8; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28a745;">
        <h4>🚀 True AI Understanding</h4>
        <p>This interface uses the <strong>Salesforce/xLAM-1b-fc-r</strong> model for real natural language understanding and function calling.</p>
        <p><strong>Try these commands:</strong></p>
        <ul>
            <li>"Show me sales report for this year"</li>
            <li>"Create a file called sales.txt with sales data"</li>
            <li>"What's the weather in London?"</li>
            <li>"Generate a sales report for Q1 and save it to report.txt"</li>
            <li>"Read the sales.txt file"</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface
    st.markdown('<div class="nlp-chat">', unsafe_allow_html=True)
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-response">{message["content"]}</div>', unsafe_allow_html=True)
    
    # User input
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""
    
    user_query = st.text_input("💬 Ask me anything:", placeholder="e.g., Show me sales report for this year", key="chat_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("🚀 Send", type="primary")
    
    # Only process when button is clicked and there's input
    if send_button and user_query.strip():
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        # Process the query with True LAM
        with st.spinner("🤖 AI is understanding and processing your request..."):
            result = lam_interface.process_natural_language(user_query)
            
            if result.get("success"):
                response = result.get("data", "AI processed your request successfully.")
            else:
                response = f"❌ **Error**: {result.get('error', 'Unknown error')}"
            
            # Add AI response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Clear input and rerun
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

def show_dashboard(ems):
    """Show the dashboard overview"""
    st.markdown('<h2 class="section-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
    
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
    st.markdown('<h3>📈 Sales Trends</h3>', unsafe_allow_html=True)
    
    # Sales by quarter
    quarterly_sales = sales_df.groupby('quarter')['sales_amount'].sum().reset_index()
    fig1 = px.bar(quarterly_sales, x='quarter', y='sales_amount', 
                   title='Sales by Quarter', color='quarter')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Sales by product
    product_sales = sales_df.groupby('product')['sales_amount'].sum().reset_index()
    fig2 = px.pie(product_sales, values='sales_amount', names='product', 
                   title='Sales by Product')
    st.plotly_chart(fig2, use_container_width=True)

def show_file_operations(ems):
    """Show file operations interface"""
    st.markdown('<h2 class="section-header">📁 File Operations</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Write File")
        filename = st.text_input("Filename:", value="sample.txt")
        content = st.text_area("Content:", height=200)
        
        if st.button("💾 Write File"):
            result = ems.write_file(filename, content)
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(f"Error: {result['error']}")
    
    with col2:
        st.subheader("📖 Read File")
        read_filename = st.text_input("Filename to read:", value="sample.txt")
        
        if st.button("📖 Read File"):
            result = ems.read_file(read_filename)
            if result["success"]:
                st.text_area("File Content:", value=result["data"], height=200, disabled=True)
            else:
                st.error(f"Error: {result['error']}")

def show_sales_management(ems):
    """Show sales management interface"""
    st.markdown('<h2 class="section-header">💰 Sales Management</h2>', unsafe_allow_html=True)
    
    # Sales data display
    quarter_filter = st.selectbox("Select Quarter:", ["All", "Q1", "Q2", "Q3", "Q4"])
    
    if quarter_filter == "All":
        sales_df = ems.get_sales_data()
    else:
        sales_df = ems.get_sales_data(quarter_filter)
    
    st.dataframe(sales_df, use_container_width=True)
    
    # Generate report
    st.subheader("📊 Generate Sales Report")
    report_quarter = st.selectbox("Select Quarter for Report:", ["Q1", "Q2", "Q3", "Q4"])
    
    if st.button("📊 Generate Report"):
        report = ems.generate_sales_report(report_quarter)
        st.text_area("Sales Report:", value=report, height=400, disabled=True)

def show_weather_api(ems):
    """Show weather API interface"""
    st.markdown('<h2 class="section-header">🌤️ Weather API</h2>', unsafe_allow_html=True)
    
    location = st.text_input("Enter location:", value="London")
    
    if st.button("🌤️ Get Weather"):
        result = ems.get_weather(location)
        if result["success"]:
            weather_data = result["data"]
            st.success(f"Weather for {weather_data['location']}")
            st.write(f"Temperature: {weather_data['temperature']}")
            st.write(f"Condition: {weather_data['condition']}")
            st.write(f"Humidity: {weather_data['humidity']}")
            st.write(f"Wind Speed: {weather_data['wind_speed']}")
        else:
            st.error(f"Error: {result['error']}")

def show_employee_performance(ems):
    """Show employee performance interface"""
    st.markdown('<h2 class="section-header">👥 Employee Performance</h2>', unsafe_allow_html=True)
    
    # Employee data display
    quarter_filter = st.selectbox("Select Quarter:", ["All", "Q1", "Q2", "Q3", "Q4"], key="emp_quarter")
    
    if quarter_filter == "All":
        employee_df = ems.get_employee_data()
    else:
        employee_df = ems.get_employee_data(quarter_filter)
    
    st.dataframe(employee_df, use_container_width=True)
    
    # Generate employee report
    st.subheader("📊 Generate Employee Report")
    col1, col2 = st.columns(2)
    
    with col1:
        employee_id = st.selectbox("Select Employee:", ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"])
    
    with col2:
        report_quarter = st.selectbox("Select Quarter:", ["Q1", "Q2", "Q3", "Q4"], key="emp_report_quarter")
    
    if st.button("📊 Generate Employee Report"):
        report = ems.generate_employee_report(employee_id, report_quarter)
        st.text_area("Employee Report:", value=report, height=400, disabled=True)

def show_email_reports(ems):
    """Show email reports interface"""
    st.markdown('<h2 class="section-header">📧 Email Reports</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;">
        <h4>📧 Email Configuration</h4>
        <p>Email functionality is configured for simulation mode by default. Check the email configuration files for setup instructions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📧 Send Email")
        to_email = st.text_input("To Email:", value="manager@company.com")
        subject = st.text_input("Subject:", value="Sales Report")
        content = st.text_area("Content:", height=200)
        
        if st.button("📧 Send Email"):
            result = ems.send_email_report(to_email, subject, content)
            if result["success"]:
                st.success("Email sent successfully!")
            else:
                st.error(f"Error: {result['error']}")
    
    with col2:
        st.subheader("📊 Quick Reports")
        report_type = st.selectbox("Report Type:", ["Sales Report", "Employee Report", "Custom"])
        
        if st.button("📊 Generate & Send Report"):
            if report_type == "Sales Report":
                report_content = ems.generate_sales_report("Q4")
                result = ems.send_email_report("manager@company.com", "Sales Report Q4", report_content)
            elif report_type == "Employee Report":
                report_content = ems.generate_employee_report("EMP001", "Q4")
                result = ems.send_email_report("manager@company.com", "Employee Report EMP001", report_content)
            else:
                result = ems.send_email_report("manager@company.com", "Custom Report", "This is a custom report.")
            
            if result["success"]:
                st.success("Report sent successfully!")
            else:
                st.error(f"Error: {result['error']}")

if __name__ == "__main__":
    main() 