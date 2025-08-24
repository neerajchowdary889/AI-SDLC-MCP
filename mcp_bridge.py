#!/usr/bin/env python3
"""
Minimal MCP Bridge - Connects Claude Desktop directly to cloud server
No proxy needed, just a simple bridge that speaks MCP protocol
"""
import asyncio
import json
import sys
import aiohttp
from typing import Any, Dict

# Your cloud server URL
CLOUD_SERVER_URL = "https://your-replit-url.replit.dev"  # Replace with your actual URL

class MCPBridge:
    def __init__(self, cloud_url: str):
        self.cloud_url = cloud_url
        self.session = None
    
    async def start_session(self):
        """Start HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def forward_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Forward MCP request to cloud server"""
        try:
            async with self.session.post(
                f"{self.cloud_url}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                return await response.json()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Bridge error: {str(e)}"
                }
            }
    
    async def handle_stdio(self):
        """Handle stdin/stdout communication with Claude Desktop"""
        await self.start_session()
        
        try:
            while True:
                # Read request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                try:
                    request = json.loads(line.strip())
                    response = await self.forward_request(request)
                    
                    # Write response to stdout
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError:
                    # Invalid JSON, send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
        finally:
            await self.close_session()

async def main():
    """Main entry point"""
    bridge = MCPBridge(CLOUD_SERVER_URL)
    await bridge.handle_stdio()

if __name__ == "__main__":
    asyncio.run(main())