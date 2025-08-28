# ui_fixes.py
def get_fixed_css():
    """Returns the corrected CSS with proper color contrast"""
    return """
    /* Fixed color issues - ensuring all text is visible */
    h2 {
        color: #2c3e50 !important;  /* Dark gray instead of white */
    }
    
    /* Fixed Predictive Analytics section */
    .predictive-header {
        color: #2c3e50 !important;  /* Changed from #FFFFFF */
    }
    
    /* Fixed Team Management section */
    .team-header {
        color: #2c3e50 !important;  /* Changed from #FFFFFF */
    }
    """