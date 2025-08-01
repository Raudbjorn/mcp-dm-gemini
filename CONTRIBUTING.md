# Contributing to TTRPG Assistant

Thank you for your interest in contributing to the TTRPG Assistant MCP Server! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a simple code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment for all contributors
- Remember we're all here to improve TTRPG experiences

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/mcp-dm-gemini.git
   cd mcp-dm-gemini
   ```
3. **Set up the development environment** (see Development Setup below)
4. **Create a feature branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git
- Docker (optional, for containerized development)

### Quick Setup
```bash
# Clone and setup
git clone https://github.com/your-username/mcp-dm-gemini.git
cd mcp-dm-gemini

# Run bootstrap script
./bootstrap.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Development Tools
Install additional development dependencies:
```bash
pip install black flake8 mypy pre-commit
pre-commit install
```

## Project Structure

```
mcp-dm-gemini/
├── ttrpg_assistant/          # Main package
│   ├── chromadb_manager/     # ChromaDB operations
│   ├── embedding_service/    # Vector embeddings
│   ├── pdf_parser/           # PDF processing & adaptive learning
│   ├── search_engine/        # Hybrid search capabilities
│   ├── mcp_server/           # MCP protocol implementation
│   └── ...
├── web_ui/                   # Web interface
├── discord_bot/              # Discord integration
├── tests/                    # Test suite
├── docs/                     # Documentation
├── config/                   # Configuration files
└── data/                     # Sample data
```

## Contributing Guidelines

### Types of Contributions

1. **Bug Fixes**: Fix issues in existing functionality
2. **Feature Enhancements**: Improve existing features
3. **New Features**: Add new capabilities
4. **Documentation**: Improve or add documentation
5. **Tests**: Add or improve test coverage
6. **Performance**: Optimize existing code

### Coding Standards

#### Python Style
- Follow PEP 8 style guidelines
- Use type hints where possible
- Maximum line length: 100 characters
- Use meaningful variable and function names

#### Code Organization
- Keep functions small and focused
- Use docstrings for all public functions and classes
- Follow the existing project structure
- Separate concerns appropriately

#### Example Code Style
```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Enhanced search service with hybrid capabilities."""
    
    def __init__(self, chroma_manager: ChromaDataManager) -> None:
        """Initialize the search service.
        
        Args:
            chroma_manager: ChromaDB manager instance
        """
        self.chroma_manager = chroma_manager
        self._initialized = False
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        use_hybrid: bool = True
    ) -> List[SearchResult]:
        """Perform a search query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            use_hybrid: Whether to use hybrid search
            
        Returns:
            List of search results
            
        Raises:
            SearchError: If search fails
        """
        logger.info(f"Performing search for: {query}")
        # Implementation here...
```

### Commit Messages

Use clear, descriptive commit messages following this format:
```
<type>: <short description>

<optional longer description>

<optional footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Examples:
```
feat: Add hybrid search with keyword matching

Implements BM25 keyword search alongside semantic search
for improved result accuracy. Includes query suggestions
and search result explanations.

fix: Handle empty PDF files gracefully

Previously crashed when processing empty or corrupted PDFs.
Now logs warning and continues processing other files.
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ttrpg_assistant

# Run specific test file
pytest tests/test_search_engine.py

# Run tests with output
pytest -v -s
```

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies appropriately

Example test:
```python
import pytest
from unittest.mock import Mock, patch
from ttrpg_assistant.search_engine.enhanced_search_service import EnhancedSearchService

class TestEnhancedSearchService:
    """Tests for enhanced search service."""
    
    @pytest.fixture
    def search_service(self):
        """Create search service for testing."""
        mock_chroma = Mock()
        mock_embedding = Mock()
        return EnhancedSearchService(mock_chroma, mock_embedding)
    
    async def test_search_returns_results(self, search_service):
        """Test that search returns expected results."""
        # Setup
        query = "fireball spell"
        expected_results = [...]
        
        # Execute
        results = await search_service.search(query)
        
        # Assert
        assert len(results) > 0
        assert results[0].content_chunk.content_type == "spell"
```

### Test Categories
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test performance characteristics

## Documentation

### Types of Documentation
1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: MCP tool descriptions
3. **User Documentation**: Installation and usage guides
4. **Developer Documentation**: Architecture and design docs

### Documentation Standards
- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include examples where helpful
- Update relevant design documents for architectural changes

## Pull Request Process

### Before Submitting
1. **Test your changes**: Run the full test suite
2. **Update documentation**: Ensure docs reflect your changes
3. **Check code style**: Run linting tools
4. **Update CHANGELOG.md** if applicable

### Pull Request Template
When creating a pull request, include:

1. **Description**: What does this PR do?
2. **Type of Change**: Bug fix, feature, documentation, etc.
3. **Testing**: How was this tested?
4. **Documentation**: Any documentation updates needed?
5. **Breaking Changes**: Any breaking changes?

### Example PR Description
```markdown
## Description
Adds hybrid search functionality combining semantic similarity with keyword matching using BM25.

## Type of Change
- [x] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- Added unit tests for hybrid search components
- Added integration tests for search workflows
- Tested with sample TTRPG PDFs
- Performance tested with large datasets

## Documentation
- Updated design.md with search architecture
- Added hybrid search to README.md
- Updated MCP tool documentation

## Breaking Changes
None. This is backwards compatible with existing search functionality.
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review the code
3. **Testing**: Additional testing if needed
4. **Documentation Review**: Ensure docs are accurate
5. **Merge**: PR is merged after approval

## Getting Help

- **Issues**: Check existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Refer to docs/ directory
- **Code Examples**: Look at tests/ for usage examples

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- GitHub contributors list

Thank you for contributing to the TTRPG Assistant! 🎲