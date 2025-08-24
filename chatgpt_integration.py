#!/usr/bin/env python3
"""
ChatGPT Integration for AI-SLDC MCP Server
This creates a simple API that ChatGPT can call via function calling
"""
import os
import json
import requests
from typing import Dict, Any, List
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
CLOUD_MCP_URL = os.getenv("CLOUD_MCP_URL", "http://localhost:8000")
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key-here")

class MCPClient:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(f"{self.url}/mcp", json=payload, headers=self.headers)
        return response.json()

# Initialize MCP client
mcp_client = MCPClient(CLOUD_MCP_URL, MCP_API_KEY)

@app.route("/search_docs", methods=["POST"])
def search_docs():
    """Search documentation - ChatGPT compatible endpoint"""
    try:
        data = request.json
        query = data.get("query", "")
        limit = data.get("limit", 10)
        
        result = mcp_client.call_tool("search_docs", {"query": query, "limit": limit})
        
        if result.get("error"):
            return jsonify({"error": result["error"]["message"]}), 400
        
        # Extract text content
        content = result.get("result", {}).get("content", [])
        text_content = content[0].get("text", "") if content else "No results found"
        
        return jsonify({
            "success": True,
            "results": text_content,
            "query": query
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_document", methods=["POST"])
def get_document():
    """Get specific document - ChatGPT compatible endpoint"""
    try:
        data = request.json
        path = data.get("path", "")
        
        if not path:
            return jsonify({"error": "Path parameter is required"}), 400
        
        result = mcp_client.call_tool("get_document", {"path": path})
        
        if result.get("error"):
            return jsonify({"error": result["error"]["message"]}), 400
        
        # Extract text content
        content = result.get("result", {}).get("content", [])
        text_content = content[0].get("text", "") if content else "Document not found"
        
        return jsonify({
            "success": True,
            "document": text_content,
            "path": path
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/list_documents", methods=["POST"])
def list_documents():
    """List all documents - ChatGPT compatible endpoint"""
    try:
        data = request.json or {}
        limit = data.get("limit", 50)
        
        result = mcp_client.call_tool("list_documents", {"limit": limit})
        
        if result.get("error"):
            return jsonify({"error": result["error"]["message"]}), 400
        
        # Extract text content
        content = result.get("result", {}).get("content", [])
        text_content = content[0].get("text", "") if content else "No documents found"
        
        return jsonify({
            "success": True,
            "documents": text_content
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_statistics", methods=["POST"])
def get_statistics():
    """Get documentation statistics - ChatGPT compatible endpoint"""
    try:
        result = mcp_client.call_tool("get_statistics", {})
        
        if result.get("error"):
            return jsonify({"error": result["error"]["message"]}), 400
        
        # Extract text content
        content = result.get("result", {}).get("content", [])
        text_content = content[0].get("text", "") if content else "No statistics available"
        
        return jsonify({
            "success": True,
            "statistics": text_content
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ChatGPT MCP Integration"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🤖 Starting ChatGPT MCP Integration on port {port}")
    print(f"🔗 Cloud MCP URL: {CLOUD_MCP_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)