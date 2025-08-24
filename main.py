#!/usr/bin/env python3
"""
Replit entry point - starts the cloud MCP server
"""
import os
import subprocess
import sys

def install_requirements():
    """Install requirements if not already installed"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "cloud_requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def start_server():
    """Start the cloud MCP server"""
    # Set environment variables for Replit
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "8000"
    os.environ["MCP_API_KEY"] = os.getenv("MCP_API_KEY", "replit-mcp-key-2024")
    
    # Import and run the server
    import uvicorn
    uvicorn.run(
        "cloud_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )

if __name__ == "__main__":
    print("🚀 Starting AI-SLDC Cloud MCP Server on Replit...")
    install_requirements()
    start_server()