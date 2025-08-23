---
title: Team Workflows
tags: [workflow, collaboration, process]
author: Process Team
description: How different team roles use AI-SLDC for collaboration
---

# Team Workflows with AI-SLDC

This document describes how different team roles can leverage AI-SLDC for improved collaboration and productivity.

## Developer Workflows

### Daily Development
1. **Morning Context Check**
   - Ask Claude: "What documentation was updated yesterday?"
   - Review changes to architecture docs and API specifications
   - Check for new coding guidelines or standards

2. **Feature Development**
   - Search for existing patterns: "Find examples of authentication implementation"
   - Review API documentation: "Show me the user management API docs"
   - Check coding standards: "What are our TypeScript coding conventions?"

3. **Code Review Preparation**
   - Find related documentation: "Get docs related to payment processing"
   - Review architectural decisions: "Show me ADRs about database design"
   - Check testing guidelines: "What are our unit testing best practices?"

### Example Claude Interactions
```
Developer: "Find all documentation about our authentication system"
Claude: [Uses search_docs tool to find auth-related documents]

Developer: "Show me the API documentation for user registration"
Claude: [Uses get_document tool to retrieve specific API docs]
```

## Product Manager Workflows

### Sprint Planning
1. **Requirements Review**
   - Search for user stories: "Find all user stories for the mobile app"
   - Review feature specifications: "Show me the payment feature requirements"
   - Check acceptance criteria: "Get the testing criteria for user onboarding"

2. **Stakeholder Communication**
   - Gather project status: "What features are documented as complete?"
   - Find decision records: "Show me recent architectural decisions"
   - Review roadmap items: "Find documentation about Q4 features"

3. **Progress Tracking**
   - Monitor documentation updates: "What docs were modified this week?"
   - Check feature completeness: "List all features with complete documentation"
   - Review blockers: "Find any documented blockers or issues"

## QA Engineer Workflows

### Test Planning
1. **Test Case Development**
   - Find feature specs: "Get the complete specification for user registration"
   - Review acceptance criteria: "Show me all acceptance criteria for payments"
   - Check edge cases: "Find documentation about error handling"

2. **Test Execution**
   - Reference test procedures: "Show me the testing checklist for deployments"
   - Check known issues: "Find all documented bugs and workarounds"
   - Review test data requirements: "Get the test data setup documentation"

3. **Bug Reporting**
   - Find related docs: "Get documentation for the feature that's failing"
   - Check expected behavior: "Show me the specification for login flow"
   - Reference similar issues: "Find any documented issues with authentication"

## DevOps Engineer Workflows

### Infrastructure Management
1. **Deployment Preparation**
   - Review deployment docs: "Show me the production deployment checklist"
   - Check configuration: "Find all environment configuration documentation"
   - Verify procedures: "Get the rollback procedures for the API service"

2. **Incident Response**
   - Find troubleshooting guides: "Show me debugging docs for database issues"
   - Check runbooks: "Get the incident response procedures"
   - Review architecture: "Find the system architecture documentation"

3. **Monitoring Setup**
   - Reference monitoring docs: "Show me the monitoring and alerting setup"
   - Check SLA requirements: "Find all SLA and performance requirements"
   - Review metrics: "Get documentation about key performance indicators"

## Team Lead Workflows

### Project Oversight
1. **Status Reviews**
   - Check documentation coverage: "List all features missing documentation"
   - Review team progress: "What documentation was updated by each team member?"
   - Monitor quality: "Find any incomplete or outdated documentation"

2. **Decision Making**
   - Review architectural decisions: "Show me all ADRs from the last month"
   - Check technical debt: "Find documentation about technical debt items"
   - Analyze risks: "Get all risk assessments and mitigation plans"

3. **Team Coordination**
   - Share knowledge: "Find onboarding documentation for new team members"
   - Review processes: "Show me all process and workflow documentation"
   - Check standards: "Get the coding standards and best practices docs"

## Cross-Team Collaboration Patterns

### Documentation-Driven Development
1. **Specification First**
   - Write feature specifications before coding
   - Use Claude to review specs for completeness
   - Ensure all stakeholders can access and understand requirements

2. **Living Documentation**
   - Keep documentation updated with code changes
   - Use AI to identify outdated documentation
   - Maintain consistency across all documentation

3. **Knowledge Sharing**
   - Use tags to organize documentation by team and topic
   - Create cross-references between related documents
   - Enable easy discovery of relevant information

### Communication Workflows

#### Daily Standups
- "What documentation changes affect my work today?"
- "Are there any new architectural decisions I should know about?"
- "What features have updated specifications?"

#### Sprint Reviews
- "Show me all documentation completed this sprint"
- "Find any gaps in feature documentation"
- "Get the list of all updated user stories"

#### Retrospectives
- "What documentation issues did we encounter?"
- "Find examples of well-documented features"
- "Identify areas where documentation could be improved"

## Best Practices

### Documentation Organization
- Use consistent tagging across all documents
- Maintain clear file naming conventions
- Keep related documents in logical directory structures
- Use frontmatter metadata for better searchability

### AI Tool Usage
- Ask specific questions rather than broad queries
- Use tags to filter results when searching
- Reference specific document paths when needed
- Combine multiple tool calls for comprehensive answers

### Team Coordination
- Establish documentation update responsibilities
- Create templates for common document types
- Regular review and cleanup of outdated information
- Cross-team documentation reviews for accuracy

### Quality Assurance
- Peer review of critical documentation
- Regular audits of documentation completeness
- Automated checks for broken links and references
- Version control integration for change tracking