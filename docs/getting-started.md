---
title: Getting Started Guide
tags: [guide, setup, beginner]
author: Development Team
description: A comprehensive guide to get started with our AI-SLDC system
---

# Getting Started with AI-SLDC

Welcome to the AI-SLDC (AI Software Development Life Cycle) system! This guide will help you understand and start using our collaborative development platform.

## What is AI-SLDC?

AI-SLDC is a revolutionary approach to software development that integrates artificial intelligence throughout the entire development lifecycle. It provides:

- **Unified Context**: All team members and AI tools share the same up-to-date project context
- **Real-time Collaboration**: Changes are immediately available to all stakeholders
- **Intelligent Assistance**: AI tools can provide contextual help based on current project state
- **Documentation-Driven Development**: Keep documentation at the center of your workflow

## Key Features

### 1. Documentation Context Management
- Automatic indexing of Markdown, text, and reStructuredText files
- Smart search capabilities across all documentation
- Tag-based organization and filtering
- Real-time updates when files change

### 2. MCP Integration
- Native support for Claude and other MCP-compatible AI tools
- Standardized protocol for AI tool integration
- Secure and controlled access to project context

### 3. Team Collaboration
- Role-based context views for different team members
- Shared understanding across development, QA, DevOps, and management
- Reduced context switching and information silos

## Quick Start

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Documentation Path**
   Set the `DOCS_ROOT_PATH` environment variable to your documentation directory.

3. **Start the MCP Server**
   ```bash
   npm run build
   npm start
   ```

4. **Connect Claude**
   Add the server configuration to your Claude Desktop MCP settings.

5. **Start Asking Questions**
   Ask Claude about your documentation and project context!

## Next Steps

- Read the [Architecture Overview](architecture.md)
- Learn about [Team Workflows](workflows.md)
- Explore [Advanced Features](advanced-features.md)
- Check out [Best Practices](best-practices.md)