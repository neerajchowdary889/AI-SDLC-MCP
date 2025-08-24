# 🚀 AI-SLDC Deployment Guide

## 1. Deploy to Replit

### Step 1: Create Replit Project
1. Go to [Replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub" 
4. Enter your repository URL or upload the project files
5. Replit will automatically detect it's a Python project

### Step 2: Configure Environment Variables
In Replit, go to "Secrets" tab and add:
```
MCP_API_KEY=replit-mcp-key-2024
PORT=8000
HOST=0.0.0.0
```

### Step 3: Run the Server
- Click the "Run" button in Replit
- The server will start on port 8000
- Note your Replit URL (e.g., `https://your-project.your-username.replit.dev`)

## 2. Access Streamlit Admin Interface

### Local Development:
```bash
# Install streamlit if not already installed
pip install streamlit

# Run the admin interface
python run_streamlit.py
```
Access at: http://localhost:8501

### On Replit:
1. Open a new tab in Replit
2. Run: `python run_streamlit.py`
3. Access via the Replit webview on port 8501

## 3. Connect to Claude Desktop

### Step 1: Install Claude Desktop
Download from: https://claude.ai/download

### Step 2: Configure MCP (Direct Connection - No Proxy!)
1. Update `mcp_bridge.py` with your Replit URL:
   - Open `mcp_bridge.py`
   - Replace `https://your-replit-url.replit.dev` with your actual Replit URL

2. Locate your Claude Desktop config file:
   - **Windows**: `%APPDATA%\\Claude\\claude_desktop_config.json`
   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. Add this simple configuration:
```json
{
  "mcpServers": {
    "ai-sldc-docs": {
      "command": "python",
      "args": ["mcp_bridge.py"],
      "cwd": "/path/to/your/AI-SDLC-MCP"
    }
  }
}
```

4. Replace `/path/to/your/AI-SDLC-MCP` with your actual project path
5. Restart Claude Desktop

### Step 3: Test Connection
1. Open Claude Desktop
2. Start a new conversation
3. Try: "Search for architecture documentation"
4. Claude should now have access to your documentation!

## 4. Connect to ChatGPT

### Option A: Using Custom GPT (ChatGPT Plus required)
1. Go to ChatGPT and create a Custom GPT
2. In the Actions section, add these endpoints:
   - `POST /search_docs` - Search documentation
   - `POST /get_document` - Get specific document
   - `POST /list_documents` - List all documents
   - `POST /get_statistics` - Get statistics

3. Use your Replit URL as the base URL

### Option B: Using Function Calling (API)
Deploy the ChatGPT integration:
```bash
# Install Flask
pip install flask

# Run the ChatGPT integration
python chatgpt_integration.py
```

Then use OpenAI's function calling feature with these functions.

## 5. Upload and Manage Files

### Via Streamlit Interface:
1. Access the Streamlit admin at http://localhost:8501
2. Go to "File Upload" tab
3. Upload your documentation files (.md, .txt, .rst)
4. Files are automatically indexed and searchable

### Via API:
```bash
curl -X POST https://your-replit-url.replit.dev/upload \\
  -H "Authorization: Bearer replit-mcp-key-2024" \\
  -F "file=@your-document.md"
```

### Via File System (if using local deployment):
1. Place files in the `./docs` directory
2. The file watcher will automatically detect and index them

## 6. Testing Your Setup

### Test the Cloud Server:
```bash
curl https://your-replit-url.replit.dev/health
```

### Test MCP Tools:
```bash
curl -X POST https://your-replit-url.replit.dev/mcp \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer replit-mcp-key-2024" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Test Search:
```bash
curl -X POST https://your-replit-url.replit.dev/mcp \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer replit-mcp-key-2024" \\
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"search_docs",
      "arguments":{"query":"architecture","limit":5}
    }
  }'
```

## 7. Troubleshooting

### Common Issues:

1. **Port Already in Use**
   - Change the PORT environment variable
   - Kill existing processes: `taskkill /f /im python.exe` (Windows)

2. **Authentication Errors**
   - Verify MCP_API_KEY matches in all configurations
   - Check Authorization header format

3. **File Upload Issues**
   - Ensure docs directory exists and is writable
   - Check file permissions

4. **Claude Desktop Not Connecting**
   - Verify config file path and syntax
   - Check that simple_proxy.py is in the correct directory
   - Restart Claude Desktop after config changes

5. **Replit Deployment Issues**
   - Check that all dependencies are in cloud_requirements.txt
   - Verify environment variables are set in Replit Secrets
   - Check Replit logs for error messages

## 8. Security Considerations

### For Production:
1. **Change Default API Key**: Use a strong, unique API key
2. **Enable HTTPS**: Use SSL/TLS for all communications
3. **Restrict CORS**: Configure CORS for specific domains only
4. **File Validation**: Validate uploaded files for security
5. **Rate Limiting**: Implement rate limiting for API endpoints

### Environment Variables:
```bash
# Production settings
MCP_API_KEY=your-super-secure-api-key-here
ENVIRONMENT=production
CORS_ORIGINS=https://your-domain.com
MAX_FILE_SIZE=10485760  # 10MB
```

## 9. Scaling and Performance

### For High Traffic:
1. **Use a Production WSGI Server**: Replace uvicorn with gunicorn
2. **Add Caching**: Implement Redis for search result caching
3. **Database Storage**: Replace in-memory storage with PostgreSQL
4. **Load Balancing**: Use multiple server instances
5. **CDN**: Use a CDN for static file serving

### Monitoring:
- Use the `/stats` endpoint for basic metrics
- Implement proper logging and monitoring
- Set up health checks and alerts

## 🎉 You're All Set!

Your AI-SLDC system is now deployed and ready to enhance your AI interactions with contextual documentation!