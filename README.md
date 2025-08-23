# AI-SLDC MCP Documentation Server

A Model Context Protocol (MCP) server that provides documentation context to AI tools like Claude. This Python implementation offers intelligent document indexing, search, and real-time monitoring with an optional Streamlit admin interface.

## Features

- 📚 **Documentation Indexing**: Automatically indexes Markdown, text, and reStructuredText files using Whoosh
- 🔍 **Smart Search**: Full-text search with relevance scoring and context matching
- 🔄 **Real-time Updates**: Watches for file changes and updates context automatically
- 🤖 **MCP Integration**: Native support for Claude and other MCP-compatible AI tools
- 🏷️ **Metadata Support**: Extracts frontmatter and metadata from documents
- 🌐 **Admin Interface**: Optional Streamlit web interface for file management and monitoring

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run MCP Server

```bash
python main.py
```

### Run Admin Interface (Optional)

```bash
streamlit run streamlit_app.py
```

## Configuration

Configure the server by modifying the file watcher patterns in your code or through the Streamlit admin interface:

- **Documentation root**: `./docs` (default)
- **Watch patterns**: `**/*.md`, `**/*.txt`, `**/*.rst`, `**/*.markdown`
- **Exclude patterns**: `node_modules/**`, `dist/**`, `.git/**`, `__pycache__/**`

## Claude Desktop Integration

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "ai-sldc-docs": {
      "command": "python",
      "args": ["path/to/ai-sldc-mcp/main.py"],
      "cwd": "path/to/ai-sldc-mcp"
    }
  }
}
```

## MCP Tools

The server provides these tools for AI assistants:

### `search_docs`
Search through documentation content
- `query` (string): Search query
- `tags` (array): Filter by tags
- `limit` (number): Maximum results (default: 10)

### `get_document`
Get a specific document by path
- `path` (string): Document file path

### `list_documents`
List all available documents
- `limit` (number): Maximum results (default: 50)

## Usage with Claude

1. Start the MCP server
2. Configure Claude Desktop to connect to this server
3. Ask Claude questions about your documentation

Example queries:
- "What does our API documentation say about authentication?"
- "Find all documents mentioning deployment procedures"
- "Show me the latest changes to our architecture docs"

## Project Structure

```
src/
├── models.py           # Pydantic data models
├── document_service.py # Document indexing and search
├── file_watcher.py     # File system monitoring
├── mcp_server.py       # MCP protocol implementation
└── __init__.py
main.py                 # MCP server entry point
streamlit_app.py        # Admin web interface
requirements.txt        # Python dependencies
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Dependencies

Key Python packages:
- `pydantic` - Data validation and models
- `whoosh` - Full-text search indexing
- `watchdog` - File system monitoring
- `streamlit` - Web admin interface
- `frontmatter` - Markdown frontmatter parsing
- `loguru` - Logging

## License

MIT