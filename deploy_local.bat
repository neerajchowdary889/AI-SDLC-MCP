@echo off
echo Starting AI-SLDC Cloud MCP Server locally...

REM Install dependencies
echo Installing dependencies...
pip install -r cloud_requirements.txt

REM Set environment variables
set MCP_API_KEY=your-secret-api-key-here
set PORT=8000
set PYTHONPATH=%CD%

REM Start the server
echo Starting cloud server on http://localhost:8000
py start_server.py