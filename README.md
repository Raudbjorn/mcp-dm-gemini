# TTRPG Assistant MCP Server

This project is a Model Context Protocol (MCP) server designed to assist with Tabletop Role-Playing Games (TTRPGs). It provides an AI assistant with access to parsed TTRPG rulebooks and campaign management capabilities.

## Features

*   **Rulebook Search:** Perform semantic searches for rules, spells, monsters, and items within your TTRPG rulebooks.
*   **Campaign Management:** Store, retrieve, and manage campaign-specific data like characters, NPCs, locations, and plot points.
*   **PDF Processing:** Add new TTRPG rulebooks in PDF format to the system. The server will parse the content, create vector embeddings, and make it available for searching.
*   **LLM Personality Configuration:** Automatically extracts a "personality" from each rulebook to configure the LLM's voice and style.
*   **Character Generation:** Tools to help you create player characters and generate rich backstories.
*   **NPC Generation:** A flexible tool for generating non-player characters with stats appropriate to the player characters' level.
*   **Interactive CLI:** Interactive sessions for character and NPC creation.
*   **MCP Integration:** Exposes a standardized MCP interface for AI assistants to interact with the TTRPG data.
*   **Command-Line Interface:** A user-friendly CLI for interacting with the server.
*   **Export/Import:** Export and import campaign data for sharing and backup.

## Getting Started

### Prerequisites

*   Python 3.8+
*   Redis

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/ttrpg-assistant.git
    cd ttrpg-assistant
    ```
2.  Run the bootstrap script:
    ```bash
    ./bootstrap.sh
    ```
This will create a Python virtual environment, install the required dependencies, and start the necessary services.

## Usage

The TTRPG Assistant can be used via the command-line interface (CLI) or by sending requests to the MCP server directly.

### Command-Line Interface (CLI)

The CLI provides a convenient way to interact with the server.

**Interactively create a character:**
```bash
python cli.py gen-char "My Awesome Rulebook" "my-campaign"
```

**Interactively create an NPC:**
```bash
python cli.py gen-npc-interactive "My Awesome Rulebook" "my-campaign"
```

**Search for rulebook content:**
```bash
python cli.py search "what are the rules for grappling"
```

**Add a new rulebook:**
```bash
python cli.py add-rulebook "path/to/your/rulebook.pdf" "My Awesome Rulebook" "D&D 5e"
```

**Get the AI personality for a rulebook:**
```bash
python cli.py get-personality "My Awesome Rulebook"
```

**Get character creation rules:**
```bash
python cli.py get-char-rules "My Awesome Rulebook"
```

**Generate a character backstory:**
```bash
python cli.py gen-backstory "My Awesome Rulebook" '{"name": "Aragorn"}' --player_params "Loves the color blue"
```

**Generate an NPC:**
```bash
python cli.py gen-npc "My Awesome Rulebook" 5 "A grumpy blacksmith"
```

**Create a new campaign character:**
```bash
python cli.py campaign create "my-campaign" "character" --data '{"name": "Gandalf", "class": "Wizard"}'
```

**Export a campaign:**
```bash
python cli.py campaign export "my-campaign" > campaign_backup.json
```

**Import a campaign:**
```bash
python cli.py campaign import "my-campaign" --data "$(cat campaign_backup.json)"
```

### MCP Server

The MCP server runs on `http://localhost:8000`. You can send requests to the server using any HTTP client.

Refer to the `design.md` for detailed information on the tool schemas and API.

## Troubleshooting

**Connection refused error when running the CLI:**
This usually means that the MCP server is not running. Make sure you have started the server by running `./bootstrap.sh`.

**Redis connection error:**
This means that the Redis server is not running or not accessible. Make sure you have installed Redis and that it is running on the default port (6379). You can check if Redis is running by executing `redis-cli ping`. If it returns `PONG`, then Redis is running.