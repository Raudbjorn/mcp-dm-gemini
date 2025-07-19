# Design Document

## 1. Introduction

The TTRPG Assistant is a backend service that provides a suite of tools for Tabletop Role-Playing Game (TTRPG) management. It is designed to be used as an MCP (Model-Context-Protocol) server, allowing AI models and other clients to interact with its features programmatically.

## 2. Architecture

The system is built in Python and comprises several key components:

*   **MCP Server (`main.py`)**: The main entry point of the application. It defines the tools available through the MCP interface and orchestrates the calls to the various services.
*   **Redis Data Manager (`ttrpg_assistant/redis_manager/manager.py`)**: A service responsible for all interactions with the Redis database, including storing and retrieving rulebook content, campaign data, and vector embeddings.
*   **PDF Parser (`ttrpg_assistant/pdf_parser/parser.py`)**: A service for processing PDF files, extracting text, and structuring it into content chunks.
*   **Embedding Service (`ttrpg_assistant/embedding_service/embedding.py`)**: Handles the generation of vector embeddings for text, which is used for semantic search.
*   **Content Packager (`ttrpg_assistant/content_packager/packager.py`)**: Manages the creation and installation of content packs, which are zip archives containing rulebook data.
*   **Map Generator (`ttrpg_assistant/map_generator/generator.py`)**: Generates SVG-based maps for combat encounters.
*   **Data Models (`ttrpg_assistant/data_models/models.py`)**: Defines the Pydantic data models used throughout the application.

The application uses a Redis database for data persistence. Specifically, it uses Redis Stack to leverage vector search capabilities for semantic search on rulebook content.

## 3. Tool Definitions

The following tools are exposed via the MCP server:

*   `search`: Performs a semantic search on the indexed rulebook content.
*   `add_source`: Processes a PDF file and adds its content to the system.
*   `get_rulebook_personality`: Retrieves a summary of a rulebook's "personality" or style.
*   `get_character_creation_rules`: A specialized search to find character creation rules.
*   `generate_backstory`: Generates a character backstory.
*   `generate_npc`: Generates a Non-Player Character (NPC).
*   `manage_session`: A tool for managing game session data, such as notes and initiative.
*   `generate_map`: Generates a map for a combat encounter.
*   `create_content_pack`: Creates a content pack from a source.
*   `install_content_pack`: Installs a content pack.

## 4. Deployment and Operations

The application is designed to be run both locally for development and as a containerized service.

*   **Local Development**: Can be run directly using `uv run main.py`.
*   **Containerization**: A `Dockerfile` and `docker-compose.yml` are provided for building and running the application and its Redis dependency using Docker.
*   **Continuous Integration**: A GitHub Actions workflow is configured to automatically run tests on every push and pull request to the `master` branch, ensuring code quality and stability.