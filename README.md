# TTRPG Assistant MCP Server

This project is a Model Context Protocol (MCP) server designed to assist with Tabletop Role-Playing Games (TTRPGs). It provides an AI assistant with access to parsed TTRPG rulebooks and campaign management capabilities, accessible via a web interface, a command-line tool, and a Discord bot.

## Features

*   **Advanced Search:** Perform hybrid semantic and keyword searches with query suggestions and completion for rules, spells, monsters, and items.
*   **Campaign Management:** Store, retrieve, and manage campaign-specific data using ChromaDB's document storage.
*   **Adaptive PDF Processing:** Add new TTRPG rulebooks with intelligent content classification that learns patterns over time.
*   **LLM Personality Configuration:** Automatically extracts a "personality" from each rulebook to configure the LLM's voice and style.
*   **Character Generation:** Tools to help you create player characters and generate rich backstories.
*   **NPC Generation:** A flexible tool for generating non-player characters with stats appropriate to the player characters' level.
*   **Map Generation:** Generate simple SVG maps for combat encounters.
*   **Content Packs:** Create and share content packs with other users.
*   **Web Interface:** A user-friendly web UI for interacting with all the major features of the assistant.
*   **Interactive CLI:** Interactive sessions for character and NPC creation for a guided experience.
*   **Discord Bot:** Interact with the TTRPG Assistant through a Discord bot.
*   **MCP Integration:** Exposes a standardized MCP interface for AI assistants with full feature parity between FastMCP and MCP protocol servers.
*   **Enhanced Features:** Session management, search statistics, result explanations, and cross-platform configuration support.
*   **Export/Import:** Export and import campaign data for sharing and backup.

## Documentation

For detailed instructions on how to install and use the TTRPG Assistant, please refer to our comprehensive documentation:

*   **[Installation Guide](docs/installation.md)**
*   **[Usage Guide](docs/usage.md)**

## Getting Started

### Option 1: Docker (Recommended)
```bash
docker-compose up
```

### Option 2: Manual Setup
```bash
./bootstrap.sh
```

After setup, you have multiple ways to use the TTRPG Assistant:

- **For Claude Desktop integration:** `./mcp_stdio.sh` 
- **For direct testing:** `./run_main.sh`
- **For web UI:** `python mcp_server.py` then visit [http://localhost:8000/ui](http://localhost:8000/ui)

The system uses ChromaDB for local vector storage - no external database required!

For more detailed installation instructions, please refer to the [Installation Guide](docs/installation.md).

## Troubleshooting

**Connection refused error when running the CLI:**
This usually means that the MCP server is not running. Make sure you have started the server by running `docker-compose up` or `./bootstrap.sh`.

**ChromaDB connection error:**
This means that there's an issue with the ChromaDB database. ChromaDB is an embedded database that doesn't require a separate server. If you encounter issues, ensure that the application has write permissions to the data directory (default: `./chroma_db`).

## Architecture Changes

**🔄 Major Update: ChromaDB Migration**

This version has migrated from Redis to ChromaDB for improved vector search performance and simplified deployment:

- **No external database required** - ChromaDB runs embedded within the application
- **Enhanced search capabilities** - Hybrid semantic + keyword search with query suggestions
- **Adaptive PDF processing** - Learns content patterns for better classification over time
- **Improved session management** - Uses ChromaDB's document storage for campaign data
- **Cross-platform configuration** - Automatic config file discovery across Windows, Linux, and macOS

## New Features

### Advanced Search
- **Hybrid Search**: Combines semantic similarity with keyword matching
- **Query Suggestions**: Get completion suggestions while typing
- **Search Explanations**: Understand why results were returned
- **Search Statistics**: Monitor search performance and usage

### Enhanced PDF Processing
- **Adaptive Learning**: System learns content type patterns from your rulebooks
- **Pattern Caching**: Reuses learned patterns for faster processing
- **Enhanced Metadata**: Better content classification and section detection

### MCP Protocol Support
- **Full Feature Parity**: Both FastMCP and standard MCP servers support all features
- **Cross-Platform Scripts**: `mcp_stdio.sh/.bat` for Claude Desktop integration
- **Direct Testing**: `run_main.sh/.bat` for FastMCP server testing
