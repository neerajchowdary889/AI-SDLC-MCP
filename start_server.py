#!/usr/bin/env python3
"""
Production server startup script
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Cloud MCP Server on {host}:{port}")
    print("Auto-reload disabled for production stability")
    
    uvicorn.run(
        "cloud_server:app",
        host=host,
        port=port,
        reload=False,  # Explicitly disable reload
        log_level="info"
    )