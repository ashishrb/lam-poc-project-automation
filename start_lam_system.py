#!/usr/bin/env python3
"""
Startup Script for Autonomous LAM System
Optimized for AMD Ryzen 9 9950X + RTX 4090 + 128GB RAM
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print system startup banner"""
    print("\n" + "="*80)
    print("🚀 AUTONOMOUS LAM SYSTEM STARTUP")
    print("="*80)
    print("🖥️  Optimized for AMD Ryzen 9 9950X + RTX 5090 + 128GB RAM")
    print("🧠 128GB RAM • 32 CPU Cores • CUDA Acceleration")
    print("="*80 + "\n")

def check_environment():
    """Check if virtual environment is activated"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Virtual environment not detected!")
        print("Please activate the virtual environment first:")
        print("   source venv/bin/activate")
        return False
    
    print("✅ Virtual environment is active")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'torch', 'transformers', 'streamlit', 'plotly', 
        'pandas', 'numpy', 'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
    
    return True

def optimize_system():
    """Apply system-specific optimizations"""
    print("\n🔧 Applying system optimizations...")
    
    # Set environment variables for optimal performance
    os.environ['OMP_NUM_THREADS'] = '32'  # Ryzen 9 9950X has 32 cores
    os.environ['MKL_NUM_THREADS'] = '32'
    os.environ['NUMEXPR_NUM_THREADS'] = '32'
    
    # AMD-specific optimizations
    os.environ['AMDGPU_FORCE_64BIT_PTR'] = '1'
    
    # PyTorch optimizations
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    # Streamlit optimizations
    os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
    os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'true'
    
    print("✅ System optimizations applied")

def start_performance_monitoring():
    """Start performance monitoring"""
    try:
        from performance_monitor import start_performance_monitoring
        start_performance_monitoring()
        print("✅ Performance monitoring started")
        return True
    except ImportError as e:
        print(f"⚠️ Performance monitoring not available: {e}")
        return False

def launch_streamlit():
    """Launch the Streamlit application"""
    print("\n🚀 Launching Streamlit application...")
    
    # Check if streamlit_app.py exists
    app_path = Path("streamlit_app.py")
    if not app_path.exists():
        print("❌ streamlit_app.py not found!")
        return False
    
    try:
        # Try to get system configuration
        try:
            from system_config import system_config
            server_config = system_config.get_streamlit_server_config()
            print("🔧 Using system-optimized Streamlit configuration")
        except ImportError:
            system_config = None
            server_config = None
            print("🔧 Using default Streamlit configuration")
        
        # Launch Streamlit with optimized settings
        if system_config and server_config:
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
                '--server.port', str(server_config['server_port']),
                '--server.address', server_config['server_address'],
                '--server.maxUploadSize', str(server_config['server_max_upload_size']),
                '--server.enableStaticServing', str(server_config['server_enable_static_serving']).lower(),
                '--browser.gatherUsageStats', str(server_config['browser_gather_usage_stats']).lower()
            ]
        else:
            # Fallback to default settings
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
                '--server.port', '8501',
                '--server.address', '0.0.0.0',
                '--server.maxUploadSize', '200',
                '--server.enableStaticServing', 'true',
                '--browser.gatherUsageStats', 'false'
            ]
        
        print(f"🔧 Launch command: {' '.join(cmd)}")
        print("\n🌐 Application will be available at: http://localhost:8501")
        print("📱 Press Ctrl+C to stop the application")
        
        # Launch the application
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        return False
    
    return True

def main():
    """Main startup sequence"""
    print_banner()
    
    # Step 1: Check environment
    print("🔍 Step 1: Checking environment...")
    if not check_environment():
        return False
    
    # Step 2: Check dependencies
    print("\n🔍 Step 2: Checking dependencies...")
    if not check_dependencies():
        return False
    
    # Step 3: Apply system optimizations
    print("\n🔍 Step 3: Applying system optimizations...")
    optimize_system()
    
    # Step 4: Start performance monitoring
    print("\n🔍 Step 4: Starting performance monitoring...")
    start_performance_monitoring()
    
    # Step 5: Launch application
    print("\n🔍 Step 5: Launching application...")
    return launch_streamlit()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Startup failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during startup: {e}")
        sys.exit(1)
