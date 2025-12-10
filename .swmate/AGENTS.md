# AGENTS.md

Project: {{ project_name }}
Created at {{ created_at }}

## AI Agent Roles

This document defines the roles and responsibilities of AI agents when working with this codebase.

### Code Analyzer Agent
- Analyze file structure and dependencies across C, SQL, XML, and JavaScript files
- Identify potential issues, bugs, or improvement opportunities
- Provide context-aware explanations of code functionality
- Map relationships between different file types (e.g., C files using SQL queries)

### Code Generator Agent  
- Generate new code following project conventions and patterns
- Create files based on templates and requirements
- Ensure generated code is compatible with existing codebase    
- Follow language-specific best practices for each file type

### Code Reviewer Agent
- Review code changes for correctness and quality
- Check for syntax errors and potential runtime issues
- Verify adherence to coding standards
- Suggest improvements and optimizations

## Collaboration Rules

### Code Style Guidelines
- **C/PC Files (.c, .pc)**: Follow K&R or project-specific C coding standards
- **SQL Files (.sql)**: Use uppercase for SQL keywords, proper indentation for queries
- **XML Files (.xml)**: Maintain proper nesting and attribute formatting
- **JavaScript Files (.js)**: Follow ES6+ standards, use consistent naming conventions

### Documentation Standards
- Add comments for complex logic and business rules
- Document function parameters and return values
- Explain SQL query purposes and expected results
- Note any dependencies between different file types

### Testing Approach
- Verify C code compiles without warnings
- Test SQL queries for syntax and logic correctness
- Validate XML structure and schema compliance
- Ensure JavaScript functions handle edge cases

## Project-Specific Rules

### C File Analysis
- Identify function signatures, global variables, and includes
- Check for memory leaks and pointer issues
- Analyze error handling patterns
- Map embedded SQL usage (for .pc files)

### SQL Analysis  
- Identify table structures and relationships
- Check query performance considerations
- Verify proper use of indexes and joins
- Document transaction boundaries

### XML Analysis
- Validate structure and schema compliance
- Check for proper encoding and special character handling
- Identify configuration patterns
- Map XML-to-code relationships

### JavaScript Analysis
- Identify functions, classes, and modules
- Check for async/await patterns
- Analyze error handling and validation
- Document API endpoints and data flows

## Version Management
- Review all file changes before committing
- Ensure changes maintain backward compatibility
- Update related documentation when code changes
- Test interactions between modified files of different types
