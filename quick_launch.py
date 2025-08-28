#!/usr/bin/env python3
"""
Quick Launch Script for LAM System
Simple launch without complex startup sequence
"""

import subprocess
import sys
import os

def main():
    print("🚀 Quick Launch - Autonomous LAM System")
    print("="*50)
    
    # Check if virtual environment is active
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Virtual environment not detected!")
        print("Please activate the virtual environment first:")
        print("   source venv/bin/activate")
        return False
    
    print("✅ Virtual environment is active")
    
    # Simple Streamlit launch
    try:
        print("\n🚀 Launching Streamlit application...")
        print("🌐 Application will be available at: http://localhost:8501")
        print("📱 Press Ctrl+C to stop the application")
        
        # Launch with basic settings
        cmd = [
            sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
            '--server.port', '8501',
            '--server.address', '0.0.0.0'
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
