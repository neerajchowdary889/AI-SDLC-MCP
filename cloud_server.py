#!/usr/bin/env python3
"""
Cloud MCP Server - HTTP/WebSocket version of the MCP server
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

# Import our existing services
from src.document_service import DocumentService
from src.models import ContextQuery, MCPToolResult


# Pydantic models for API
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class DocumentUpload(BaseModel):
    filename: str
    content: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class ServerStats(BaseModel):
    total_documents: int
    total_size: int
    total_words: int
    uptime_seconds: float
    last_activity: datetime
    connected_clients: int


# Security
security = HTTPBearer()
API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key-here")


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key authentication"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


# FastAPI app
app = FastAPI(
    title="AI-SLDC Cloud MCP Server",
    description="Cloud-based MCP server for AI-SLDC documentation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
document_service = DocumentService()
connected_clients: Dict[str, WebSocket] = {}
server_start_time = datetime.now()


class CloudMCPHandlers:
    """Cloud MCP handlers that mirror the local MCP tools"""
    
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service
    
    async def handle_search_docs(self, args: Dict[str, Any]) -> MCPToolResult:
        """Handle search_docs tool call"""
        try:
            query = ContextQuery(
                query=args.get('query'),
                tags=args.get('tags', []),
                path=args.get('path'),
                limit=args.get('limit', 10),
                sort_by=args.get('sortBy', 'relevance')
            )
            
            results = self.document_service.search_documents(query)
            
            if not results:
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "No documents found matching your search criteria."
                    }]
                )
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                doc = result.document
                output = f"## {i}. {doc.title}\\n"
                output += f"**Path:** {doc.relative_path}\\n"
                output += f"**Last Modified:** {doc.last_modified.isoformat()}\\n"
                
                if doc.tags:
                    output += f"**Tags:** {', '.join(doc.tags)}\\n"
                
                if result.score > 0:
                    output += f"**Relevance Score:** {result.score * 100:.1f}%\\n"
                
                output += f"**Excerpt:** {doc.excerpt}\\n"
                
                if result.matches:
                    output += "**Matches:**\\n"
                    for match in result.matches[:3]:
                        output += f"- Line {match.line}: \\\"{match.text}\\\"\\n"
                
                formatted_results.append(output)
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Found {len(results)} document(s):\\n\\n" + "\\n---\\n\\n".join(formatted_results)
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error searching documents: {str(e)}"
                }]
            )
    
    async def handle_get_document(self, args: Dict[str, Any]) -> MCPToolResult:
        """Handle get_document tool call"""
        try:
            path = args.get('path')
            if not path:
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: path parameter is required"
                    }]
                )
            
            document = self.document_service.get_document(path)
            if not document:
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Document not found: {path}"
                    }]
                )
            
            output = f"# {document.title}\\n\\n"
            output += f"**Path:** {document.relative_path}\\n"
            output += f"**Last Modified:** {document.last_modified.isoformat()}\\n"
            output += f"**Size:** {document.size} bytes\\n"
            output += f"**Word Count:** {document.word_count}\\n"
            
            if document.tags:
                output += f"**Tags:** {', '.join(document.tags)}\\n"
            
            if document.metadata.custom_fields:
                output += "**Metadata:**\\n"
                for key, value in document.metadata.custom_fields.items():
                    output += f"- {key}: {value}\\n"
            
            output += f"\\n---\\n\\n{document.content}"
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": output
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error retrieving document: {str(e)}"
                }]
            )
    
    async def handle_list_documents(self, args: Dict[str, Any]) -> MCPToolResult:
        """Handle list_documents tool call"""
        try:
            limit = args.get('limit', 50)
            tags = args.get('tags', [])
            
            documents = self.document_service.get_all_documents()
            
            # Filter by tags if provided
            if tags:
                documents = [
                    doc for doc in documents 
                    if any(tag in doc.tags for tag in tags)
                ]
            
            # Apply limit
            documents = documents[:limit]
            
            if not documents:
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "No documents found."
                    }]
                )
            
            formatted_list = []
            for i, doc in enumerate(documents, 1):
                output = f"{i}. **{doc.title}**\\n"
                output += f"   Path: {doc.relative_path}\\n"
                output += f"   Modified: {doc.last_modified.isoformat()}\\n"
                output += f"   Size: {doc.size} bytes, {doc.word_count} words\\n"
                
                if doc.tags:
                    output += f"   Tags: {', '.join(doc.tags)}\\n"
                
                formatted_list.append(output)
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Found {len(documents)} document(s):\\n\\n" + "\\n".join(formatted_list)
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error listing documents: {str(e)}"
                }]
            )
    
    async def handle_get_tags(self) -> MCPToolResult:
        """Handle get_tags tool call"""
        try:
            tags = self.document_service.get_all_tags()
            
            if not tags:
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "No tags found in the documentation."
                    }]
                )
            
            tag_list = []
            for tag in tags:
                docs = self.document_service.get_documents_by_tag(tag)
                tag_list.append(f"- **{tag}** ({len(docs)} document{'s' if len(docs) != 1 else ''})")
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Available tags:\\n\\n" + "\\n".join(tag_list)
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error retrieving tags: {str(e)}"
                }]
            )
    
    async def handle_get_statistics(self) -> MCPToolResult:
        """Handle get_statistics tool call"""
        try:
            stats = self.document_service.get_statistics()
            
            output = "# Documentation Statistics\\n\\n"
            output += f"**Total Documents:** {stats.total_files}\\n"
            output += f"**Total Size:** {stats.total_size / 1024:.2f} KB\\n"
            output += f"**Total Words:** {stats.total_words:,}\\n"
            output += f"**Last Activity:** {stats.last_activity.isoformat()}\\n\\n"
            
            if stats.file_types:
                output += "**File Types:**\\n"
                sorted_types = sorted(stats.file_types.items(), key=lambda x: x[1], reverse=True)
                for ext, count in sorted_types:
                    ext_display = ext if ext else 'no extension'
                    output += f"- {ext_display}: {count} file{'s' if count != 1 else ''}\\n"
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": output
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error retrieving statistics: {str(e)}"
                }]
            )


# Initialize handlers
mcp_handlers = CloudMCPHandlers(document_service)


# Load initial documents
def load_initial_documents():
    """Load documents from docs directory on startup"""
    docs_path = Path("./docs")
    if docs_path.exists():
        for file_path in docs_path.rglob("*.md"):
            try:
                document = document_service.load_document(str(file_path), str(docs_path))
                if document:
                    document_service.add_document(document)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")


# API Routes
@app.on_event("startup")
async def startup_event():
    """Load initial documents on startup"""
    load_initial_documents()
    print(f"Cloud MCP Server started with {len(document_service.documents)} documents")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI-SLDC Cloud MCP Server", "status": "running"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    stats = document_service.get_statistics()
    return {
        "status": "healthy",
        "documents": stats.total_files,
        "uptime": (datetime.now() - server_start_time).total_seconds(),
        "connected_clients": len(connected_clients)
    }


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests via HTTP"""
    try:
        if request.method == "tools/list":
            tools = [
                {
                    "name": "search_docs",
                    "description": "Search through documentation content",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "number", "description": "Max results", "default": 10}
                        }
                    }
                },
                {
                    "name": "get_document",
                    "description": "Get a specific document by path",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Document path"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "list_documents",
                    "description": "List all available documents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "number", "description": "Max results", "default": 50}
                        }
                    }
                },
                {
                    "name": "get_statistics",
                    "description": "Get documentation statistics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
            
            return MCPResponse(
                id=request.id,
                result={"tools": tools}
            )
        
        elif request.method == "tools/call":
            if not request.params:
                raise ValueError("Missing parameters for tool call")
            
            tool_name = request.params.get("name")
            tool_args = request.params.get("arguments", {})
            
            # Route to appropriate handler
            if tool_name == "search_docs":
                result = await mcp_handlers.handle_search_docs(tool_args)
            elif tool_name == "get_document":
                result = await mcp_handlers.handle_get_document(tool_args)
            elif tool_name == "list_documents":
                result = await mcp_handlers.handle_list_documents(tool_args)
            elif tool_name == "get_tags":
                result = await mcp_handlers.handle_get_tags()
            elif tool_name == "get_statistics":
                result = await mcp_handlers.handle_get_statistics()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return MCPResponse(
                id=request.id,
                result=result.dict()
            )
        
        else:
            raise ValueError(f"Unknown method: {request.method}")
    
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": str(e)
            }
        )


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to the system"""
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Save to docs directory
        docs_path = Path("./docs")
        docs_path.mkdir(exist_ok=True)
        
        file_path = docs_path / file.filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        # Load into document service
        document = document_service.load_document(str(file_path), str(docs_path))
        if document:
            document_service.add_document(document)
            
            # Notify connected clients
            await broadcast_update({
                "type": "document_added",
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "path": document.relative_path
                }
            })
            
            return {
                "message": "Document uploaded successfully",
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "path": document.relative_path,
                    "size": document.size,
                    "word_count": document.word_count
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to process document")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_server_stats() -> ServerStats:
    """Get server statistics"""
    stats = document_service.get_statistics()
    return ServerStats(
        total_documents=stats.total_files,
        total_size=stats.total_size,
        total_words=stats.total_words,
        uptime_seconds=(datetime.now() - server_start_time).total_seconds(),
        last_activity=stats.last_activity,
        connected_clients=len(connected_clients)
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    client_id = str(uuid.uuid4())
    await websocket.accept()
    connected_clients[client_id] = websocket
    
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            # Echo back for now - could handle real-time queries here
            await websocket.send_text(f"Echo: {data}")
    
    except WebSocketDisconnect:
        pass
    finally:
        if client_id in connected_clients:
            del connected_clients[client_id]


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    if not connected_clients:
        return
    
    message_str = json.dumps(message)
    disconnected_clients = []
    
    for client_id, websocket in connected_clients.items():
        try:
            await websocket.send_text(message_str)
        except:
            disconnected_clients.append(client_id)
    
    # Remove disconnected clients
    for client_id in disconnected_clients:
        del connected_clients[client_id]


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Disable reload in production to prevent constant restarts
    reload_enabled = os.getenv("ENVIRONMENT", "production") == "development"
    uvicorn.run(
        "cloud_server:app",
        host="0.0.0.0",
        port=port,
        reload=reload_enabled
    )