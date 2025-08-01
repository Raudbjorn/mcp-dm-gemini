# Changelog

All notable changes to the TTRPG Assistant MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive .gitignore file for better repository management
- CONTRIBUTING.md with detailed contribution guidelines
- CHANGELOG.md for tracking project changes

## [2.0.0] - 2025-01-XX

### 🔄 MAJOR UPDATE: ChromaDB Migration

This release represents a significant architecture change from Redis to ChromaDB.

### Added
- **ChromaDB Integration**: Complete migration from Redis to ChromaDB for vector storage
- **Hybrid Search**: Advanced search combining semantic similarity with keyword matching (BM25)
- **Query Suggestions**: Auto-completion and query suggestions based on vocabulary
- **Search Explanations**: Detailed explanations of search results and relevance factors
- **Search Statistics**: Analytics and performance monitoring for search operations
- **Adaptive PDF Processing**: Machine learning-based content classification with pattern caching
- **Enhanced Session Management**: Improved campaign data storage using ChromaDB documents
- **Cross-Platform Configuration**: Automatic config file discovery across Windows, Linux, macOS
- **MCP Protocol Standardization**: Full-featured MCP server implementation alongside FastMCP
- **Enhanced Error Handling**: Better error messages and graceful failure handling

### Enhanced
- **PDF Parser**: Now includes adaptive learning capabilities and pattern recognition
- **Search Service**: Complete rewrite with hybrid search capabilities
- **MCP Tools**: All tools now support enhanced parameters and better error handling
- **Configuration System**: Robust cross-platform configuration utilities
- **Documentation**: Comprehensive updates to reflect new architecture

### Changed
- **⚠️ BREAKING**: Migrated from Redis to ChromaDB (data migration required)
- **⚠️ BREAKING**: Updated configuration format (Redis config → ChromaDB config)
- **Script Names**: `start_mcp_server.*` → `mcp_stdio.*` for clarity
- **Dependencies**: Updated requirements.txt for ChromaDB and enhanced features

### Added Tools
- `quick_search`: Fast search for simple lookups
- `suggest_completions`: Query completion suggestions
- `explain_search`: Detailed search result explanations  
- `get_search_stats`: Search service statistics and analytics

### Fixed
- Windows configuration file path issues
- MCP protocol compliance errors
- Memory efficiency in PDF processing
- Cross-platform script compatibility

### Removed
- Redis dependencies and configuration
- Legacy search implementations
- Deprecated script names

### Migration Guide
For users upgrading from v1.x:
1. Install new dependencies: `pip install -r requirements.txt`
2. Run bootstrap script: `./bootstrap.sh`
3. Update configuration files (automatic migration provided)
4. Use new script names: `mcp_stdio.sh` instead of `start_mcp_server.sh`

## [1.2.0] - 2024-XX-XX

### Added
- Discord bot integration for TTRPG assistance
- Content pack marketplace for sharing processed rulebooks
- Map generation with SVG output
- Enhanced session management tools
- Interactive CLI for character and NPC creation
- Web-based user interface

### Enhanced
- Improved PDF processing with better section detection
- Enhanced campaign data management
- Better error handling and logging

### Fixed
- Memory leaks in large PDF processing
- Session data persistence issues
- Character generation edge cases

## [1.1.0] - 2024-XX-XX

### Added
- Character backstory generation
- NPC generation with level-appropriate stats
- Rulebook personality extraction and configuration
- Flavor source material support
- Session management (initiative tracking, monster HP, notes)

### Enhanced
- Improved search relevance scoring
- Better PDF text extraction
- Enhanced MCP tool descriptions

### Fixed
- PDF parsing for complex layouts
- Memory usage optimization
- Search result ranking issues

## [1.0.0] - 2024-XX-XX

### Initial Release

#### Core Features
- **MCP Server**: Model Context Protocol server for AI assistant integration
- **PDF Processing**: Extract and parse TTRPG rulebooks from PDF files
- **Vector Search**: Semantic search using sentence transformers and Redis
- **Campaign Management**: Store and retrieve campaign data
- **Web Interface**: User-friendly web UI for all features
- **CLI Tools**: Command-line interface for advanced users

#### MCP Tools
- `search`: Search through TTRPG rulebooks and content
- `add_source`: Process and add new PDF sources
- `manage_campaign`: Campaign data management
- `get_rulebook_personality`: Extract rulebook personality text
- `get_character_creation_rules`: Retrieve character creation rules
- `generate_backstory`: Generate character backstories
- `generate_npc`: Create NPCs with appropriate stats
- `manage_session`: Session management tools
- `generate_map`: Create simple combat maps
- `create_content_pack`: Package content for sharing
- `install_content_pack`: Install shared content packs

#### Technical Features
- Redis vector database integration
- Sentence transformer embeddings
- FastAPI web server
- Docker containerization
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions

---

## Release Notes Format

Each release includes:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

### Versioning Strategy
- **Major** (X.0.0): Breaking changes, major new features
- **Minor** (X.Y.0): New features, backward compatible
- **Patch** (X.Y.Z): Bug fixes, backward compatible

### Support Policy
- **Current Release**: Full support with new features and bug fixes
- **Previous Major**: Security fixes and critical bug fixes only
- **Older Releases**: Community support only