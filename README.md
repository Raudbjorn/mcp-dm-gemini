# TTRPG Assistant MCP Server

This project is a Model Context Protocol (MCP) server designed to assist with Tabletop Role-Playing Games (TTRPGs). It provides an AI assistant with access to parsed TTRPG rulebooks and campaign management capabilities, accessible via a web interface and a command-line tool.

## Features

*   **Rulebook Search:** Perform semantic searches for rules, spells, monsters, and items within your TTRPG rulebooks.
*   **Campaign Management:** Store, retrieve, and manage campaign-specific data like characters, NPCs, locations, and plot points.
*   **PDF Processing:** Add new TTRPG rulebooks in PDF format to the system. The server will parse the content, create vector embeddings, and make it available for searching.
*   **LLM Personality Configuration:** Automatically extracts a "personality" from each rulebook to configure the LLM's voice and style.
*   **Character Generation:** Tools to help you create player characters and generate rich backstories.
*   **NPC Generation:** A flexible tool for generating non-player characters with stats appropriate to the player characters' level.
*   **Web Interface:** A user-friendly web UI for interacting with all the major features of the assistant.
*   **Interactive CLI:** Interactive sessions for character and NPC creation for a guided experience.
*   **MCP Integration:** Exposes a standardized MCP interface for AI assistants to interact with the TTRPG data.
*   **Export/Import:** Export and import campaign data for sharing and backup.

## Documentation

For detailed instructions on how to install and use the TTRPG Assistant, please refer to our comprehensive documentation:

*   **[Installation Guide](docs/installation.md)**
*   **[Usage Guide](docs/usage.md)**

## Getting Started

### Prerequisites

*   Python 3.8+
*   Redis

### Installation and Running the Application

The `bootstrap.sh` script is the single point of entry for setting up and running the application.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ttrpg-assistant.git
    cd ttrpg-assistant
    ```
2.  **Make the bootstrap script executable:**
    ```bash
    chmod +x bootstrap.sh
    ```
3.  **Run the bootstrap script:**
    ```bash
    ./bootstrap.sh
    ```

This script will perform the following actions:
*   Create a Python virtual environment in the `.venv` directory.
*   Install all the required dependencies from `requirements.txt`.
*   Check if Redis is installed and running. If not, it will attempt to start it.
*   Start the main application server, which includes both the MCP server and the Web UI.

Once the server is running, you can access the web interface and use the CLI.

## Troubleshooting

**Connection refused error when running the CLI:**
This usually means that the MCP server is not running. Make sure you have started the server by running `./bootstrap.sh`.

**Redis connection error:**
This means that the Redis server is not running or not accessible. Make sure you have installed Redis and that it is running on the default port (6379). You can check if Redis is running by executing `redis-cli ping`. If it returns `PONG`, then Redis is running.