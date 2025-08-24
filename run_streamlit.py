#!/usr/bin/env python3
"""
Run Streamlit admin interface
"""
import subprocess
import sys
import os

def main():
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    
    print("🌐 Starting Streamlit Admin Interface...")
    print("📍 Access at: http://localhost:8501")
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    main()