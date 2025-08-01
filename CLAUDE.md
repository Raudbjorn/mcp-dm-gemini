# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TTRPG Assistant MCP (Model Context Protocol) Server that provides AI assistant capabilities for tabletop role-playing games. The system processes PDF rulebooks, creates vector embeddings for semantic search, and provides tools for campaign management, character/NPC generation, and map creation.

## Architecture

### Core Components

- **MCP Server** (`ttrpg_assistant/mcp_server/`): FastAPI-based server exposing MCP tools
- **PDF Parser** (`ttrpg_assistant/pdf_parser/`): Enhanced PDF processor with adaptive pattern learning for intelligent content classification
- **Embedding Service** (`ttrpg_assistant/embedding_service/`): Creates and manages vector embeddings using sentence-transformers
- **ChromaDB Manager** (`ttrpg_assistant/chromadb_manager/`): Handles data storage and vector search operations using ChromaDB
- **Search Engine** (`ttrpg_assistant/search_engine/`): Enhanced search capabilities combining semantic and keyword search with query processing
- **Web UI** (`web_ui/`): FastAPI-based web interface for user interactions
- **Discord Bot** (`discord_bot/`): Discord integration for chat-based interactions
- **CLI** (`cli.py`): Command-line interface for all major operations

### Data Models

The system uses Pydantic models defined in `ttrpg_assistant/data_models/models.py` for structured data handling across all components.

### Configuration

All configuration is centralized in `config/config.yaml` covering ChromaDB persistence directory, embedding settings, adaptive PDF processing parameters, pattern learning settings, search thresholds, and Discord bot token.

## Development Commands

### Setup and Running

```bash
# Quick start with Docker (recommended)
docker-compose up

# Manual setup and run (Linux/Mac)
./bootstrap.sh

# Manual setup (Windows)
pip install -r requirements.txt

# Run MCP server directly (from project root directory)
python mcp_server.py

# Run Discord bot (from project root directory)
python discord_bot/main.py
```

**Important for Windows users**: Always run the server commands from the project root directory (where `config/config.yaml` is located) to ensure the configuration file is found correctly.

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_mcp_server.py

# Run with coverage
python -m pytest --cov=ttrpg_assistant tests/
```

### CLI Operations

```bash
# Search rulebooks
python cli.py search "grappling rules" --rulebook "D&D 5e"

# Add new rulebook
python cli.py add-rulebook "path/to/rulebook.pdf" "Rulebook Name" "Game System"

# Interactive character creation
python cli.py gen-char "Rulebook Name" "campaign-id"

# Interactive NPC creation  
python cli.py gen-npc-interactive "Rulebook Name" "campaign-id"

# Campaign management
python cli.py campaign create "campaign-id" "character" --data '{"name": "Character Name"}'
python cli.py campaign export "campaign-id"

# Session management
python cli.py session start "campaign-id" "session-id"
```

## Key Architecture Patterns

### MCP Tool Integration
All major functionality is exposed through MCP tools in `ttrpg_assistant/mcp_server/tools.py`. Each tool corresponds to a specific FastAPI endpoint that can be called via HTTP POST to `/tools/{tool_name}`.

### Dependency Injection
The system uses FastAPI's dependency injection for ChromaDB manager, embedding service, and PDF parser instances, making components easily mockable for testing.

### Enhanced PDF Processing Pipeline
1. PDF content is parsed with adaptive pattern learning
2. Content is intelligently classified (stat blocks, spells, tables, etc.)
3. System-specific metadata is extracted (D&D 5e, Pathfinder)
4. Content is chunked based on classification type
5. Chunks are embedded using sentence-transformers
6. Embeddings are stored in ChromaDB collections with rich metadata
7. Search queries are processed with spell checking, abbreviation expansion, and intent detection
8. Hybrid search combines semantic (vector) and keyword (BM25) matching
9. Results are ranked by combined relevance score and returned with query suggestions

### Campaign Data Structure
Campaign data is stored in ChromaDB collections with campaign_id as metadata, supporting characters, NPCs, locations, sessions, and other game data types.

## Web Interface Access

- Main application: `http://localhost:8000/ui`
- MCP server endpoints: `http://localhost:8000/tools/`
- Health check: `http://localhost:8000/health`

## Enhanced Search API Endpoints

The system provides several search endpoints with different capabilities:

### Core Search Endpoints

- **`/search`**: Enhanced hybrid search with query processing, spell checking, and suggestions
  - Supports semantic + keyword search combination
  - Returns results with query suggestions and search statistics
  - Configurable through `use_hybrid`, `context`, and filtering parameters

- **`/quick_search`**: Fast search without extensive processing for simple lookups
  - Optimized for speed over comprehensiveness
  - Ideal for autocomplete and quick reference

### Query Enhancement Endpoints

- **`/suggest_completions`**: Get query completion suggestions based on vocabulary
  - Useful for implementing search autocomplete
  - Returns completions based on indexed content and TTRPG terminology

- **`/explain_search`**: Get detailed explanation of search results
  - Shows why specific results were returned
  - Includes relevance factors and scoring details
  - Helpful for debugging search behavior

### Utility Endpoints

- **`/search_stats`**: Get statistics about the search service
  - Shows vocabulary size, indexed collections, document counts
  - Useful for monitoring search service health

## Enhanced Search Features

### Query Processing
- **Abbreviation Expansion**: Automatically expands TTRPG abbreviations (AC → armor class, HP → hit points)
- **Spell Checking**: Corrects common misspellings and suggests alternatives
- **Intent Detection**: Understands query intent (rules, definitions, stats, etc.)
- **Context Awareness**: Uses current game system and rulebook context

### Hybrid Search
- **Semantic Search**: Vector-based similarity matching for conceptual queries
- **Keyword Search**: BM25-based exact term matching for specific lookups
- **Intelligent Weighting**: Automatically balances semantic and keyword search based on query type
- **Query Expansion**: Adds synonyms and related terms to improve recall

### Search Examples
```json
// Basic enhanced search
POST /tools/search
{
  "query": "what is ac",
  "use_hybrid": true,
  "max_results": 5
}

// Context-aware search
POST /tools/search
{
  "query": "spell damage",
  "rulebook": "Player's Handbook",
  "context": {
    "current_system": "D&D 5e",
    "current_rulebook": "PHB"
  }
}

// Quick search for autocomplete
POST /tools/quick_search
{
  "query": "fireball",
  "max_results": 3
}

// Query completions
POST /tools/suggest_completions
{
  "partial_query": "arm",
  "limit": 5
}
```

## Environment Requirements

- Python 3.11+
- ChromaDB (embedded database, no separate server needed)
- Dependencies listed in `requirements.txt`
- For Discord bot: Discord bot token in `config/config.yaml`