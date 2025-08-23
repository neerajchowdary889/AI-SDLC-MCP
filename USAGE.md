# AI-SLDC MCP Server Usage Guide

## 🎉 Python Implementation Ready!

You've successfully converted the AI-SLDC MCP server to Python with enhanced features including Whoosh search indexing and an optional Streamlit admin interface.

## What You've Built

### Core Features ✅
- **Advanced Document Indexing**: Uses Whoosh for full-text search with BM25F scoring
- **Real-time File Watching**: Monitors file changes with cross-platform support
- **Smart Search**: Full-text search with relevance scoring and match highlighting
- **MCP Integration**: Native Claude Desktop integration via MCP protocol
- **Rich Metadata Support**: Extracts frontmatter tags and custom metadata
- **Admin Interface**: Optional Streamlit web interface for management
- **5 MCP Tools**: Complete set of documentation query tools

## Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the MCP Server
```bash
python main.py
```

### Step 3: Optional - Start Admin Interface
```bash
streamlit run streamlit_app.py
```

### Step 4: Configure Claude Desktop
Add this to your Claude Desktop MCP configuration:
```json
{
  "mcpServers": {
    "ai-sldc-docs": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "path/to/ai-sldc-mcp",
      "env": {
        "PYTHONPATH": ".",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": ["search_docs", "list_documents", "get_tags", "get_statistics"]
    }
  }
}
```

## Available MCP Tools

### 1. `search_docs`
Advanced full-text search with Whoosh indexing
```json
{
  "query": "authentication API",
  "tags": ["api", "security"],
  "path": "docs/",
  "limit": 10,
  "sortBy": "relevance"
}
```

### 2. `get_document`
Retrieve complete document with metadata
```json
{
  "path": "docs/api.md"
}
```

### 3. `list_documents`
List documents with filtering
```json
{
  "limit": 50,
  "tags": ["guide"]
}
```

### 4. `get_tags`
Get all available tags with document counts
```json
{}
```

### 5. `get_statistics`
Comprehensive documentation statistics
```json
{}
```

## Admin Interface Features

Access the Streamlit admin at `http://localhost:8501`:

- **📊 Dashboard**: View statistics and recent documents
- **📁 File Upload**: Upload new documentation files
- **🔍 Search & Browse**: Test search functionality
- **🗑️ Manage Context**: Clear or manage indexed documents
- **📋 Admin Logs**: View system activity and actions

## Document Format Support

### Frontmatter Example
```markdown
---
title: API Authentication Guide
tags: [api, security, authentication]
author: Dev Team
version: 2.1
description: Complete guide to API authentication
created: 2024-01-15
---

# API Authentication Guide

This document explains how to authenticate with our API...
```

### Supported File Types
- `.md` - Markdown files
- `.txt` - Plain text files
- `.rst` - reStructuredText files
- `.markdown` - Markdown files

## Configuration

### Default Patterns
**Watch Patterns:**
- `**/*.md`
- `**/*.txt`
- `**/*.rst`
- `**/*.markdown`

**Exclude Patterns:**
- `node_modules/**`
- `dist/**`
- `.git/**`
- `__pycache__/**`
- `venv/**`
- `.venv/**`
- `build/**`
- `coverage/**`

### Customization
Modify patterns in the `FileWatcher` initialization or through the admin interface.

## Testing

### Run Basic Tests
```bash
python test_basic.py
```

### Run MCP Protocol Tests
```bash
python test_mcp.py
```

### Expected Output
```
🧪 Testing AI-SLDC MCP Server...
📊 Testing statistics...
   Total files: 2
   Total words: 46
🔍 Testing search functionality...
   Search for 'test': 2 results
✅ All tests completed successfully!
```

## Example Claude Interactions

### Advanced Search
**You:** "Find all documentation about API authentication and security"
**Claude:** *Uses search_docs with query "API authentication security" and returns ranked results with match highlights*

### Browse by Category
**You:** "Show me all tutorial documents"
**Claude:** *Uses list_documents with tags filter for "tutorial" and displays organized list*

### Get Project Overview
**You:** "What's the current state of our documentation?"
**Claude:** *Uses get_statistics to show document counts, file types, word counts, and last activity*

### Retrieve Specific Guide
**You:** "Show me the complete deployment guide"
**Claude:** *Uses get_document to retrieve full content with metadata*

## Architecture Benefits

### Python Advantages
- **Whoosh Integration**: Professional-grade full-text search
- **Rich Ecosystem**: Access to ML/AI libraries for future enhancements
- **Cross-platform**: Better Windows support than Node.js alternatives
- **Streamlit Admin**: Easy web interface development
- **Pydantic Models**: Type-safe data validation

### Performance Features
- **Incremental Indexing**: Only re-index changed documents
- **BM25F Scoring**: Advanced relevance ranking
- **Efficient Storage**: Whoosh index optimization
- **Memory Management**: Proper resource cleanup

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Install missing dependencies
pip install whoosh loguru python-frontmatter
```

**No Documents Found:**
- Check `./docs` directory exists
- Verify file extensions are supported
- Check console output for scanning logs

**Search Not Working:**
- Verify Whoosh index creation in `./index/` directory
- Check document content is not empty
- Try simpler search queries

**MCP Connection Issues:**
- Ensure Python path is correct in Claude config
- Restart Claude Desktop after configuration changes
- Check server startup logs for errors

### Debug Mode
Enable debug logging in `main.py`:
```python
logger.add(sys.stderr, level="DEBUG", format="{time} | {level} | {message}")
```

## Next Steps

### Immediate Enhancements
- [ ] Add more file format support (PDF, DOCX)
- [ ] Implement semantic search with embeddings
- [ ] Add document change notifications
- [ ] Create backup/restore functionality

### Integration Opportunities
- [ ] GitHub integration for issues/PRs
- [ ] Jira connector for task context
- [ ] CI/CD pipeline integration
- [ ] Slack/Teams notifications

### Advanced Features
- [ ] Multi-language support
- [ ] Document versioning
- [ ] User access controls
- [ ] Analytics dashboard

## Success Metrics

Your Python implementation provides:
- ✅ **Enhanced Search**: Whoosh-powered full-text indexing
- ✅ **Better Performance**: Optimized document processing
- ✅ **Admin Interface**: Web-based management console
- ✅ **Type Safety**: Pydantic model validation
- ✅ **Cross-platform**: Improved Windows compatibility
- ✅ **Extensible**: Ready for ML/AI enhancements

The Python implementation is production-ready and provides a solid foundation for the full AI-SLDC vision! 🚀