#!/usr/bin/env python3
"""
Simple MCP Server for AI-SLDC Documentation
"""

import json
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.document_service import DocumentService
from src.models import ContextQuery


class SimpleMCPServer:
    def __init__(self):
        self.document_service = DocumentService()
        self.initialized = False
        
        # Load documents from docs directory
        self.load_documents()
    
    def load_documents(self):
        """Load documents from the docs directory"""
        docs_path = Path("./docs")
        if not docs_path.exists():
            docs_path.mkdir(parents=True, exist_ok=True)
            print(f"Created docs directory: {docs_path}", file=sys.stderr)
            return
        
        print(f"Loading documents from: {docs_path.absolute()}", file=sys.stderr)
        
        # Load markdown and text files
        loaded_count = 0
        for file_path in docs_path.rglob("*.md"):
            try:
                print(f"Loading: {file_path}", file=sys.stderr)
                document = self.document_service.load_document(str(file_path), str(docs_path))
                if document:
                    self.document_service.add_document(document)
                    loaded_count += 1
                    print(f"Successfully loaded: {document.title}", file=sys.stderr)
                else:
                    print(f"Failed to create document object for: {file_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error loading {file_path}: {e}", file=sys.stderr)
        
        for file_path in docs_path.rglob("*.txt"):
            try:
                print(f"Loading: {file_path}", file=sys.stderr)
                document = self.document_service.load_document(str(file_path), str(docs_path))
                if document:
                    self.document_service.add_document(document)
                    loaded_count += 1
                    print(f"Successfully loaded: {document.title}", file=sys.stderr)
                else:
                    print(f"Failed to create document object for: {file_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error loading {file_path}: {e}", file=sys.stderr)
        
        print(f"Total documents loaded: {loaded_count}", file=sys.stderr)
    
    def send_response(self, response):
        """Send JSON response to stdout"""
        print(json.dumps(response), flush=True)
    
    def handle_initialize(self, request_id, params):
        """Handle initialize request"""
        self.initialized = True
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
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
    
    def handle_tools_list(self, request_id):
        """Handle tools/list request"""
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
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
        self.send_response(response)
    
    def handle_tool_call(self, request_id, tool_name, arguments):
        """Handle tools/call request"""
        try:
            if tool_name == "search_docs":
                query_text = arguments.get("query", "")
                limit = arguments.get("limit", 10)
                
                query = ContextQuery(query=query_text, limit=limit)
                results = self.document_service.search_documents(query)
                
                content = []
                if results:
                    text_parts = [f"Found {len(results)} document(s):\\n"]
                    for i, result in enumerate(results, 1):
                        doc = result.document
                        text_parts.append(f"{i}. **{doc.title}**")
                        text_parts.append(f"   Path: {doc.relative_path}")
                        text_parts.append(f"   Excerpt: {doc.excerpt}")
                        if result.matches:
                            text_parts.append("   Matches:")
                            for match in result.matches[:2]:
                                text_parts.append(f"   - Line {match.line}: {match.text}")
                        text_parts.append("")
                    
                    content.append({"type": "text", "text": "\\n".join(text_parts)})
                else:
                    content.append({"type": "text", "text": "No documents found matching your query."})
            
            elif tool_name == "get_document":
                path = arguments.get("path")
                if not path:
                    raise ValueError("Path is required")
                
                document = self.document_service.get_document(path)
                if document:
                    text = f"# {document.title}\\n\\n"
                    text += f"**Path:** {document.relative_path}\\n"
                    text += f"**Modified:** {document.last_modified}\\n"
                    text += f"**Size:** {document.size} bytes\\n\\n"
                    text += f"---\\n\\n{document.content}"
                    content = [{"type": "text", "text": text}]
                else:
                    content = [{"type": "text", "text": f"Document not found: {path}"}]
            
            elif tool_name == "list_documents":
                limit = arguments.get("limit", 50)
                documents = self.document_service.get_all_documents(limit)
                
                if documents:
                    text_parts = [f"Available documents ({len(documents)}):\\n"]
                    for i, doc in enumerate(documents, 1):
                        text_parts.append(f"{i}. **{doc.title}**")
                        text_parts.append(f"   Path: {doc.relative_path}")
                        text_parts.append(f"   Size: {doc.size} bytes, {doc.word_count} words")
                        text_parts.append("")
                    
                    content = [{"type": "text", "text": "\\n".join(text_parts)}]
                else:
                    content = [{"type": "text", "text": "No documents available."}]
            
            elif tool_name == "get_statistics":
                stats = self.document_service.get_statistics()
                text = f"# Documentation Statistics\\n\\n"
                text += f"**Total Documents:** {stats.total_files}\\n"
                text += f"**Total Size:** {stats.total_size / 1024:.2f} KB\\n"
                text += f"**Total Words:** {stats.total_words:,}\\n"
                text += f"**Last Activity:** {stats.last_activity}\\n"
                
                if stats.file_types:
                    text += "\\n**File Types:**\\n"
                    for ext, count in stats.file_types.items():
                        ext_display = ext if ext else 'no extension'
                        text += f"- {ext_display}: {count} file(s)\\n"
                
                content = [{"type": "text", "text": text}]
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": content}
            }
            self.send_response(response)
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            self.send_response(error_response)
    
    def handle_request(self, request):
        """Handle incoming request"""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                self.handle_initialize(request_id, params)
            elif method == "notifications/initialized":
                # No response needed for notifications
                pass
            elif method == "tools/list":
                self.handle_tools_list(request_id)
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                self.handle_tool_call(request_id, tool_name, arguments)
            else:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                self.send_response(error_response)
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            self.send_response(error_response)
    
    def run(self):
        """Main server loop"""
        print(f"Simple MCP Server starting...", file=sys.stderr)
        print(f"Loaded {len(self.document_service.documents)} documents", file=sys.stderr)
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    self.handle_request(request)
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    self.send_response(error_response)
        
        except KeyboardInterrupt:
            print("Server stopped", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)


if __name__ == "__main__":
    server = SimpleMCPServer()
    server.run()