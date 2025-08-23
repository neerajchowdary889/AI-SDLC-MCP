import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from loguru import logger

from .document_service import DocumentService
from .models import ContextQuery, MCPToolResult


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


class MCPToolHandlers:
    """MCP tool handlers for document operations"""
    
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
                output = f"## {i}. {doc.title}\n"
                output += f"**Path:** {doc.relative_path}\n"
                output += f"**Last Modified:** {doc.last_modified.isoformat()}\n"
                
                if doc.tags:
                    output += f"**Tags:** {', '.join(doc.tags)}\n"
                
                if result.score > 0:
                    output += f"**Relevance Score:** {result.score * 100:.1f}%\n"
                
                output += f"**Excerpt:** {doc.excerpt}\n"
                
                if result.matches:
                    output += "**Matches:**\n"
                    for match in result.matches[:3]:
                        output += f"- Line {match.line}: \"{match.text}\"\n"
                
                formatted_results.append(output)
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Found {len(results)} document(s):\n\n" + "\n---\n\n".join(formatted_results)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error in handle_search_docs: {e}")
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
            
            output = f"# {document.title}\n\n"
            output += f"**Path:** {document.relative_path}\n"
            output += f"**Last Modified:** {document.last_modified.isoformat()}\n"
            output += f"**Size:** {document.size} bytes\n"
            output += f"**Word Count:** {document.word_count}\n"
            
            if document.tags:
                output += f"**Tags:** {', '.join(document.tags)}\n"
            
            if document.metadata.custom_fields:
                output += "**Metadata:**\n"
                for key, value in document.metadata.custom_fields.items():
                    output += f"- {key}: {value}\n"
            
            output += f"\n---\n\n{document.content}"
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": output
                }]
            )
            
        except Exception as e:
            logger.error(f"Error in handle_get_document: {e}")
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
                output = f"{i}. **{doc.title}**\n"
                output += f"   Path: {doc.relative_path}\n"
                output += f"   Modified: {doc.last_modified.isoformat()}\n"
                output += f"   Size: {doc.size} bytes, {doc.word_count} words\n"
                
                if doc.tags:
                    output += f"   Tags: {', '.join(doc.tags)}\n"
                
                formatted_list.append(output)
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Found {len(documents)} document(s):\n\n" + "\n".join(formatted_list)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error in handle_list_documents: {e}")
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
                    "text": f"Available tags:\n\n" + "\n".join(tag_list)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error in handle_get_tags: {e}")
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
            
            output = "# Documentation Statistics\n\n"
            output += f"**Total Documents:** {stats.total_files}\n"
            output += f"**Total Size:** {stats.total_size / 1024:.2f} KB\n"
            output += f"**Total Words:** {stats.total_words:,}\n"
            output += f"**Last Activity:** {stats.last_activity.isoformat()}\n\n"
            
            if stats.file_types:
                output += "**File Types:**\n"
                sorted_types = sorted(stats.file_types.items(), key=lambda x: x[1], reverse=True)
                for ext, count in sorted_types:
                    ext_display = ext if ext else 'no extension'
                    output += f"- {ext_display}: {count} file{'s' if count != 1 else ''}\n"
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": output
                }]
            )
            
        except Exception as e:
            logger.error(f"Error in handle_get_statistics: {e}")
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error retrieving statistics: {str(e)}"
                }]
            )


class MCPServer:
    """MCP Server implementation"""
    
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service
        self.handlers = MCPToolHandlers(document_service)
        self.connected_clients: Dict[str, WebSocket] = {}
        
        # Define available tools
        self.tools = [
            {
                "name": "search_docs",
                "description": "Search through documentation content using text queries, tags, or file paths",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search for in document content and titles"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter documents by tags"
                        },
                        "path": {
                            "type": "string",
                            "description": "Filter documents by file path (partial match)"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results to return (default: 10)",
                            "minimum": 1,
                            "maximum": 50
                        },
                        "sortBy": {
                            "type": "string",
                            "enum": ["relevance", "modified", "created", "title"],
                            "description": "Sort results by relevance, modification date, creation date, or title"
                        }
                    }
                }
            },
            {
                "name": "get_document",
                "description": "Retrieve a specific document by its file path",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The relative file path of the document to retrieve"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "list_documents",
                "description": "List all available documents with optional filtering",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of documents to return (default: 50)",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter documents by tags"
                        }
                    }
                }
            },
            {
                "name": "get_tags",
                "description": "Get all available tags used in the documentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_statistics",
                "description": "Get statistics about the documentation collection",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP request"""
        try:
            if request.method == "tools/list":
                return MCPResponse(
                    id=request.id,
                    result={"tools": self.tools}
                )
            
            elif request.method == "tools/call":
                if not request.params:
                    raise ValueError("Missing parameters for tool call")
                
                tool_name = request.params.get("name")
                tool_args = request.params.get("arguments", {})
                
                # Route to appropriate handler
                if tool_name == "search_docs":
                    result = await self.handlers.handle_search_docs(tool_args)
                elif tool_name == "get_document":
                    result = await self.handlers.handle_get_document(tool_args)
                elif tool_name == "list_documents":
                    result = await self.handlers.handle_list_documents(tool_args)
                elif tool_name == "get_tags":
                    result = await self.handlers.handle_get_tags()
                elif tool_name == "get_statistics":
                    result = await self.handlers.handle_get_statistics()
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return MCPResponse(
                    id=request.id,
                    result=result.dict()
                )
            
            else:
                raise ValueError(f"Unknown method: {request.method}")
        
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": str(e)
                }
            )
    
    async def handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection for MCP communication"""
        await websocket.accept()
        self.connected_clients[client_id] = websocket
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    # Parse MCP request
                    request_data = json.loads(data)
                    request = MCPRequest(**request_data)
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Send response
                    await websocket.send_text(response.json())
                    
                except json.JSONDecodeError as e:
                    error_response = MCPResponse(
                        error={
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    )
                    await websocket.send_text(error_response.json())
                
                except Exception as e:
                    error_response = MCPResponse(
                        error={
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    )
                    await websocket.send_text(error_response.json())
        
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        
        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        if not self.connected_clients:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.connected_clients.items():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected_clients:
            del self.connected_clients[client_id]