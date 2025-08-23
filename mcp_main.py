#!/usr/bin/env python3
"""
AI-SLDC MCP Server - Proper MCP Protocol Implementation
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from loguru import logger

from src.document_service import DocumentService
from src.file_watcher import FileWatcher
from src.mcp_server import MCPToolHandlers


class MCPStdioServer:
    """MCP Server that communicates via stdio (standard input/output)"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.file_watcher = FileWatcher(self.document_service, root_path="./docs")
        self.handlers = MCPToolHandlers(self.document_service)
        self.request_id = 0
        
        # Available tools
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
    
    async def initialize(self):
        """Initialize the server and load documents"""
        try:
            logger.info("Initializing AI-SLDC MCP Server...")
            
            # Check if docs directory exists
            docs_path = Path("./docs")
            if not docs_path.exists():
                logger.warning(f"Docs directory {docs_path} does not exist, creating it...")
                docs_path.mkdir(parents=True, exist_ok=True)
            
            # Start file watcher to load documents (with timeout)
            try:
                # Use asyncio.wait_for to prevent hanging
                await asyncio.wait_for(self.file_watcher.start(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("File watcher initialization timed out, continuing without it")
            except Exception as e:
                logger.warning(f"File watcher failed to start: {e}")
                # Continue without file watcher - documents can still be loaded manually
            
            # Log statistics
            stats = self.document_service.get_statistics()
            logger.info(f"Loaded {stats.total_files} documents ({stats.total_words} words)")
            
            logger.info("MCP Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            # Don't raise - let the server continue to run
            logger.info("Continuing with minimal initialization...")
    
    def send_response(self, response_data):
        """Send response to stdout"""
        response_json = json.dumps(response_data)
        print(response_json, flush=True)
        logger.debug(f"Sent response: {response_json}")
    
    def send_error(self, request_id, code, message):
        """Send error response"""
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        self.send_response(error_response)
    
    async def handle_request(self, request_data):
        """Handle incoming MCP request"""
        try:
            request_id = request_data.get("id")
            method = request_data.get("method")
            params = request_data.get("params", {})
            
            logger.info(f"Handling request: {method}")
            
            if method == "initialize":
                # MCP initialization - match the client's protocol version
                client_protocol = params.get("protocolVersion", "2024-11-05")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": client_protocol,
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "ai-sldc-docs",
                            "version": "1.0.0"
                        }
                    }
                }
                self.send_response(response)
                
            elif method == "notifications/initialized":
                # Client has finished initialization
                logger.info("Client initialization complete")
                # No response needed for notifications
            
            elif method == "tools/list":
                # List available tools
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }
                self.send_response(response)
            
            elif method == "tools/call":
                # Call a tool
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
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
                    self.send_error(request_id, -32601, f"Unknown tool: {tool_name}")
                    return
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result.dict()
                }
                self.send_response(response)
            
            else:
                self.send_error(request_id, -32601, f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            request_id = request_data.get("id") if isinstance(request_data, dict) else None
            self.send_error(request_id, -32603, f"Internal error: {str(e)}")
    
    async def run(self):
        """Main server loop"""
        try:
            # Initialize server with timeout
            logger.info("Starting MCP server initialization...")
            await asyncio.wait_for(self.initialize(), timeout=15.0)
            
            logger.info("MCP server ready, starting main loop...")
            
            # Create a reader for stdin
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            
            # Connect to stdin
            loop = asyncio.get_event_loop()
            transport, _ = await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            try:
                while True:
                    try:
                        # Read line with timeout to prevent hanging
                        line_bytes = await asyncio.wait_for(reader.readline(), timeout=30.0)
                        
                        if not line_bytes:
                            # EOF reached
                            logger.info("EOF reached, shutting down")
                            break
                        
                        line = line_bytes.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        logger.debug(f"Received: {line}")
                        
                        # Parse JSON request
                        try:
                            request_data = json.loads(line)
                            await self.handle_request(request_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON received: {line} - Error: {e}")
                            self.send_error(None, -32700, f"Parse error: {str(e)}")
                    
                    except asyncio.TimeoutError:
                        # Timeout is normal - just continue listening
                        continue
                    except Exception as e:
                        logger.error(f"Error processing request: {e}")
                        self.send_error(None, -32603, f"Internal error: {str(e)}")
            
            finally:
                transport.close()
        
        except asyncio.TimeoutError:
            logger.error("Server initialization timed out")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Server error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        finally:
            if hasattr(self, 'file_watcher') and self.file_watcher:
                try:
                    await self.file_watcher.stop()
                except:
                    pass
            logger.info("Server stopped")


async def main():
    """Main entry point"""
    try:
        # Setup logging to stderr (stdout is used for MCP communication)
        logger.remove()
        logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
        
        logger.info("Starting AI-SLDC MCP Server...")
        
        # Create and run server
        server = MCPStdioServer()
        await server.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())