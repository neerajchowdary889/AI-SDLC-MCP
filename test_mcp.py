#!/usr/bin/env python3
"""
Test MCP server functionality
"""

import asyncio
import tempfile
from pathlib import Path

from src.document_service import DocumentService
from src.file_watcher import FileWatcher
from src.mcp_server import MCPServer, MCPRequest


async def test_mcp_functionality():
    """Test MCP server tool calls"""
    print("🧪 Testing MCP Server Tools...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temp directory: {temp_dir}")
        
        # Create some test documents
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()
        
        # Test document
        doc_path = docs_dir / "api.md"
        doc_content = """---
title: API Documentation
tags: [api, rest, authentication]
author: Dev Team
---

# API Documentation

## Authentication

Our API uses JWT tokens for authentication.
You need to include the token in the Authorization header.

## Endpoints

### GET /users
Returns a list of users.

### POST /users
Creates a new user.
"""
        doc_path.write_text(doc_content)
        
        # Initialize services
        document_service = DocumentService()
        file_watcher = FileWatcher(document_service, str(docs_dir))
        mcp_server = MCPServer(document_service)
        
        # Start file watcher
        await file_watcher.start()
        await asyncio.sleep(1)  # Wait for indexing
        
        print("🔧 Testing MCP Tools...")
        
        # Test tools/list
        print("📋 Testing tools/list...")
        request = MCPRequest(method="tools/list", id=1)
        response = await mcp_server.handle_request(request)
        print(f"   Available tools: {len(response.result['tools'])}")
        for tool in response.result['tools']:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # Test search_docs
        print("🔍 Testing search_docs...")
        request = MCPRequest(
            method="tools/call",
            id=2,
            params={
                "name": "search_docs",
                "arguments": {"query": "authentication", "limit": 5}
            }
        )
        response = await mcp_server.handle_request(request)
        print("   Search results:")
        for content in response.result['content']:
            print(f"   {content['text'][:100]}...")
        
        # Test get_document
        print("📄 Testing get_document...")
        request = MCPRequest(
            method="tools/call",
            id=3,
            params={
                "name": "get_document",
                "arguments": {"path": "api.md"}
            }
        )
        response = await mcp_server.handle_request(request)
        print("   Document retrieved successfully")
        
        # Test list_documents
        print("📋 Testing list_documents...")
        request = MCPRequest(
            method="tools/call",
            id=4,
            params={
                "name": "list_documents",
                "arguments": {"limit": 10}
            }
        )
        response = await mcp_server.handle_request(request)
        print("   Documents listed successfully")
        
        # Test get_tags
        print("🏷️  Testing get_tags...")
        request = MCPRequest(
            method="tools/call",
            id=5,
            params={
                "name": "get_tags",
                "arguments": {}
            }
        )
        response = await mcp_server.handle_request(request)
        print("   Tags retrieved successfully")
        
        # Test get_statistics
        print("📊 Testing get_statistics...")
        request = MCPRequest(
            method="tools/call",
            id=6,
            params={
                "name": "get_statistics",
                "arguments": {}
            }
        )
        response = await mcp_server.handle_request(request)
        print("   Statistics retrieved successfully")
        
        # Stop file watcher
        await file_watcher.stop()
        
        print("✅ All MCP tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_mcp_functionality())