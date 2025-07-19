# TTRPG Assistant MCP Server

This project is a Model Context Protocol (MCP) server designed to assist with Tabletop Role-Playing Games (TTRPGs). It provides an AI assistant with access to parsed TTRPG rulebooks and campaign management capabilities, accessible via a web interface, a command-line tool, and a Discord bot.

## Features

*   **Rulebook Search:** Perform semantic searches for rules, spells, monsters, and items within your TTRPG rulebooks.
*   **Campaign Management:** Store, retrieve, and manage campaign-specific data like characters, NPCs, locations, and plot points.
*   **PDF Processing:** Add new TTRPG rulebooks in PDF format to the system. The server will parse the content, create vector embeddings, and make it available for searching.
*   **LLM Personality Configuration:** Automatically extracts a "personality" from each rulebook to configure the LLM's voice and style.
*   **Character Generation:** Tools to help you create player characters and generate rich backstories.
*   **NPC Generation:** A flexible tool for generating non-player characters with stats appropriate to the player characters' level.
*   **Map Generation:** Generate simple SVG maps for combat encounters.
*   **Content Packs:** Create and share content packs with other users.
*   **Web Interface:** A user-friendly web UI for interacting with all the major features of the assistant.
*   **Interactive CLI:** Interactive sessions for character and NPC creation for a guided experience.
*   **Discord Bot:** Interact with the TTRPG Assistant through a Discord bot.
*   **MCP Integration:** Exposes a standardized MCP interface for AI assistants to interact with the TTRPG data.
*   **Export/Import:** Export and import campaign data for sharing and backup.

## Documentation

For detailed instructions on how to install and use the TTRPG Assistant, please refer to our comprehensive documentation:

*   **[Installation Guide](docs/installation.md)**
*   **[Usage Guide](docs/usage.md)**

## Getting Started

The easiest way to get started is with Docker.

```bash
docker-compose up
```

This will build the necessary containers and start the application. You can then access the web interface at [http://localhost:8000/ui](http://localhost:8000/ui).

For more detailed installation instructions, please refer to the [Installation Guide](docs/installation.md).

## For Claude Desktop Users

To use the TTRPG Assistant with the Claude Desktop application, you will need to configure it to use the `main.py` script.

1.  Open the Claude Desktop settings.
2.  Navigate to the "Model Context Protocol" section.
3.  Add a new MCP configuration with the following details:
    ```json
    {
      "mcpServers": {
        "ttrpg-assistant": {
          "command": "python",
          "args": ["/path/to/your/project/main.py"]
        }
      }
    }
    ```
    Replace `/path/to/your/project/main.py` with the actual path to the `main.py` file on your system.

## Troubleshooting

**Connection refused error when running the CLI:**
This usually means that the MCP server is not running. Make sure you have started the server by running `docker-compose up` or `./bootstrap.sh`.

**Redis connection error:**
This means that the Redis server is not running or not accessible. If you are running the application with Docker, this should not be an issue. If you are running the application manually, make sure you have installed Redis and that it is running on the default port (6379). You can check if Redis is running by executing `redis-cli ping`. If it returns `PONG`, then Redis is running.

---

# TTRPG Assistant

The TTRPG Assistant is a tool designed to help Game Masters (GMs) run their tabletop role-playing games more smoothly. It uses the Model-Context-Protocol (MCP) to provide a set of tools that can be used by AI models like Claude.

## Features

*   **Rulebook Search**: Quickly search for rules, lore, and other information from your TTRPG sourcebooks.
*   **PDF Integration**: Add new rulebooks and source material by simply providing a PDF file.
*   **Character and NPC Generation**: Generate character backstories and non-player characters (NPCs) with personalities based on your source material.
*   **Session Management**: Keep track of session notes, initiative order, and monster stats.
*   **Map Generation**: Create maps for combat encounters based on a description.
*   **Content Packs**: Package your source material into distributable content packs.

## Getting Started

For instructions on how to install and run the TTRPG Assistant, please see the [Installation Guide](./docs/installation.md).

To learn how to configure the assistant for use with tools like the Claude.ai desktop app, refer to the [Configuration Guide](./docs/configuration.md).

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License.
