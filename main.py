#!/usr/bin/env python3
"""
AI-SLDC MCP Server - Main entry point
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

from src.document_service import DocumentService
from src.file_watcher import FileWatcher
from src.mcp_server import MCPServer


async def main():
    """Main entry point for the MCP server"""
    try:
        # Setup logging
        logger.remove()
        logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
        
        # Initialize services
        logger.info("Starting AI-SLDC MCP Server...")
        
        document_service = DocumentService()
        file_watcher = FileWatcher(document_service, root_path="./docs")
        mcp_server = MCPServer(document_service)
        
        # Start file watcher
        await file_watcher.start()
        
        # Log statistics
        stats = document_service.get_statistics()
        logger.info(f"Loaded {stats.total_files} documents ({stats.total_words} words)")
        
        logger.info("MCP Server ready for connections")
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        if 'file_watcher' in locals():
            await file_watcher.stop()
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())