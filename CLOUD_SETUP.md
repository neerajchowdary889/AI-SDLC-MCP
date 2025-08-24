# AI-SLDC Cloud MCP Server Setup

This guide explains how to deploy and use the cloud-based MCP server with HTTP proxy.

## Architecture

```
Claude Desktop ↔ Local MCP Proxy ↔ HTTP ↔ Cloud MCP Server
```

## Quick Start (Local Testing)

### 1. Start Cloud Server Locally

```bash
# Install dependencies
pip install -r cloud_requirements.txt

# Start server
python cloud_server.py
```

Server will be available at `http://localhost:8000`

### 2. Configure and Test Proxy

```bash
# Update proxy_config.json with your settings
{
  "cloud_server_url": "http://localhost:8000",
  "api_key": "your-secret-api-key-here"
}

# Test proxy
python mcp_proxy.py
```

### 3. Update Claude Desktop Configuration

Use this MCP configuration:

```json
{
  "mcpServers": {
    "ai-sldc-docs-cloud": {
      "command": "py",
      "args": ["D:/CodeSection/AI-SDLC-MCP/mcp_proxy.py"],
      "cwd": "D:/CodeSection/AI-SDLC-MCP",
      "env": {
        "PYTHONPATH": "D:/CodeSection/AI-SDLC-MCP",
        "CLOUD_MCP_URL": "http://localhost:8000",
        "MCP_API_KEY": "your-secret-api-key-here"
      },
      "disabled": false,
      "autoApprove": ["search_docs", "list_documents", "get_statistics"]
    }
  }
}
```

## Cloud Deployment Options

### Option 1: Railway (Recommended)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

3. **Set Environment Variables**
   ```bash
   railway variables set MCP_API_KEY=your-secure-api-key-here
   railway variables set PORT=8000
   ```

4. **Get Your URL**
   ```bash
   railway status
   ```

### Option 2: Docker + Any Cloud Provider

1. **Build Docker Image**
   ```bash
   docker build -t ai-sldc-mcp-cloud .
   ```

2. **Run Locally**
   ```bash
   docker-compose up
   ```

3. **Deploy to Cloud**
   - Push to Docker Hub
   - Deploy on AWS ECS, Google Cloud Run, Azure Container Instances, etc.

### Option 3: Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Set Environment Variables**
   ```bash
   heroku config:set MCP_API_KEY=your-secure-api-key-here
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

## Configuration

### Environment Variables

- `MCP_API_KEY`: Secret key for API authentication
- `PORT`: Server port (default: 8000)
- `PYTHONPATH`: Python path for imports

### Proxy Configuration

Update `proxy_config.json`:

```json
{
  "cloud_server_url": "https://your-deployed-server.railway.app",
  "api_key": "your-secure-api-key-here"
}
```

## API Endpoints

### Health Check
```
GET /health
```

### MCP Requests
```
POST /mcp
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {"query": "getting started"}
  }
}
```

### Upload Documents
```
POST /upload
Authorization: Bearer your-api-key
Content-Type: multipart/form-data

file: your-document.md
```

### Statistics
```
GET /stats
Authorization: Bearer your-api-key
```

## Security

1. **Change the default API key** in all configurations
2. **Use HTTPS** in production
3. **Configure CORS** appropriately for your domain
4. **Set up rate limiting** if needed
5. **Monitor logs** for suspicious activity

## Troubleshooting

### Proxy Connection Issues

1. Check cloud server is running: `curl https://your-server.com/health`
2. Verify API key in both proxy config and server
3. Check network connectivity and firewall settings

### Claude Desktop Integration

1. Restart Claude Desktop after configuration changes
2. Check MCP server logs in Claude Desktop
3. Verify proxy is receiving requests (check stderr output)

### Cloud Server Issues

1. Check server logs for errors
2. Verify all dependencies are installed
3. Ensure documents directory exists and is readable
4. Check environment variables are set correctly

## Benefits

✅ **Centralized Documentation**: All team members access the same documents  
✅ **Real-time Updates**: Changes are immediately available  
✅ **Scalable**: Handle multiple concurrent users  
✅ **Cloud Benefits**: Backup, availability, easy updates  
✅ **Team Collaboration**: Share context across team members  

## Next Steps

1. Deploy to your preferred cloud platform
2. Update proxy configuration with cloud URL
3. Share the setup with your team
4. Upload your documentation via the API or web interface
5. Start using Claude with your centralized documentation context!