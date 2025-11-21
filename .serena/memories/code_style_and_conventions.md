# Code Style and Conventions

## Python Style
- **Python Version**: 3.11
- **Imports**: Standard library first, then third-party, then local imports
- **Type Hints**: Used extensively (typing module: Dict, List, Optional, Any, Union)
- **String Formatting**: Mix of f-strings and .format()

## Naming Conventions
- **Functions**: snake_case (e.g., `build_cumulative_context`, `create_memory_block`)
- **Variables**: snake_case (e.g., `agent_id`, `block_data`, `existing_context`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_CONTEXT_SNIPPET_LENGTH`, `DEFAULT_MAX_NODES`)
- **Private Functions**: Leading underscore for internal/helper functions (e.g., `_build_cumulative_context`)

## Documentation
- **Docstrings**: Used for public functions, typically simple one-line descriptions
- **Comments**: Inline comments for complex logic, especially for fixes and workarounds
- **Special Markers**: 
  - `# CRITICAL FIX:` for important bug fixes
  - `# Defensive fix:` for error handling improvements
  - `[COMPONENT_NAME]` in print statements for logging categorization

## Code Organization
- **Modular Structure**: Functionality split into focused modules (config, memory, context, integrations)
- **Error Handling**: Try-except blocks with informative error messages
- **Logging**: Print statements with categorized prefixes (e.g., `[ERROR]`, `[AGENT_TRACKER]`, `[AUTO_TOOL_ATTACHMENT]`)

## API Patterns
- **HTTP Requests**: Using requests library with retry strategies
- **Response Handling**: .raise_for_status() for error checking
- **Headers**: Consistent use of LETTA_API_HEADERS with user_id when needed
- **URL Construction**: Helper functions (get_api_url) for consistent endpoint formatting

## Testing Patterns
- Test files prefixed with `test_`
- Integration tests for API interactions
- Simulation framework for comprehensive testing
- Debug scripts for specific component verification
