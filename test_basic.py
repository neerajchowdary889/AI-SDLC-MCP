#!/usr/bin/env python3
"""
Basic test to verify the Python MCP server functionality
"""

import asyncio
import tempfile
import os
from pathlib import Path

from src.document_service import DocumentService
from src.file_watcher import FileWatcher
from src.models import ContextQuery


async def test_basic_functionality():
    """Test basic document service functionality"""
    print("🧪 Testing AI-SLDC MCP Server...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temp directory: {temp_dir}")
        
        # Create some test documents
        docs_dir = Path(temp_dir) / "docs"
        docs_dir.mkdir()
        
        # Test document 1
        doc1_path = docs_dir / "test1.md"
        doc1_content = """---
title: Test Document 1
tags: [test, example]
author: Test Author
---

# Test Document 1

This is a test document for the AI-SLDC MCP server.
It contains some sample content for testing search functionality.
"""
        doc1_path.write_text(doc1_content)
        
        # Test document 2
        doc2_path = docs_dir / "test2.md"
        doc2_content = """# Another Test Document

This document doesn't have frontmatter but should still be indexed.
It talks about different topics like deployment and configuration.
"""
        doc2_path.write_text(doc2_content)
        
        # Initialize services
        print("🔧 Initializing services...")
        document_service = DocumentService()
        file_watcher = FileWatcher(document_service, str(docs_dir))
        
        # Start file watcher (this will do initial scan)
        print("👀 Starting file watcher...")
        await file_watcher.start()
        
        # Wait a moment for indexing
        await asyncio.sleep(1)
        
        # Test statistics
        print("📊 Testing statistics...")
        stats = document_service.get_statistics()
        print(f"   Total files: {stats.total_files}")
        print(f"   Total words: {stats.total_words}")
        print(f"   File types: {stats.file_types}")
        
        # Test document listing
        print("📋 Testing document listing...")
        documents = document_service.get_all_documents()
        print(f"   Found {len(documents)} documents")
        for doc in documents:
            print(f"   - {doc.title} ({doc.relative_path})")
        
        # Test search functionality
        print("🔍 Testing search functionality...")
        
        # Search for "test"
        query = ContextQuery(query="test", limit=5)
        results = document_service.search_documents(query)
        print(f"   Search for 'test': {len(results)} results")
        for result in results:
            print(f"   - {result.document.title} (score: {result.score:.2f})")
        
        # Search by tag
        query = ContextQuery(tags=["test"], limit=5)
        results = document_service.search_documents(query)
        print(f"   Search by tag 'test': {len(results)} results")
        
        # Test getting specific document
        print("📄 Testing document retrieval...")
        doc = document_service.get_document("test1.md")
        if doc:
            print(f"   Retrieved: {doc.title}")
            print(f"   Tags: {doc.tags}")
            print(f"   Word count: {doc.word_count}")
        
        # Test tags
        print("🏷️  Testing tags...")
        tags = document_service.get_all_tags()
        print(f"   Available tags: {tags}")
        
        # Stop file watcher
        await file_watcher.stop()
        
        print("✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())