# Usage Guide

This guide will show you how to use the TTRPG Assistant's web interface, command-line interface (CLI), and Discord bot.

## Web Interface

The web interface is the easiest way to use the TTRPG Assistant. Once you have the server running, you can access it by opening your web browser and navigating to [http://localhost:8000/ui](http://localhost:8000/ui).

### Search

The "Search" page allows you to search for content in your rulebooks. Simply enter your search query in the search box and click the "Search" button. The results will be displayed below the search box.

### Campaign

The "Campaign" page allows you to manage your campaign data. You can create, read, update, and delete campaign data using the form on this page.

### Add Rulebook

The "Add Rulebook" page allows you to add new rulebooks to the TTRPG Assistant. Simply enter the path to the PDF file, the name of the rulebook, and the game system, and click the "Add Rulebook" button.

### Session

The "Session" page allows you to manage your game sessions. You can start a new session, add notes, manage initiative, and track monster health.

## Command-Line Interface (CLI)

The CLI provides a powerful way to interact with the TTRPG Assistant.

### Interactive Character Creation

To start an interactive character creation session, run the following command:

```bash
python cli.py gen-char "My Awesome Rulebook" "my-campaign"
```

### Interactive NPC Creation

To start an interactive NPC creation session, run the following command:

```bash
python cli.py gen-npc-interactive "My Awesome Rulebook" "my-campaign"
```

### Other Commands

For a full list of commands and their options, run the following command:

```bash
python cli.py --help
```

## Discord Bot

The TTRPG Assistant can also be used through a Discord bot. To use the bot, you will need to create a Discord application and add the bot to your server.

### Creating a Discord Bot

1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click the "New Application" button.
3.  Give your application a name and click "Create".
4.  Go to the "Bot" tab and click "Add Bot".
5.  Copy the bot's token.
6.  Open the `config/config.yaml` file and paste the token into the `discord.token` field.
7.  Go to the "OAuth2" tab and select the "bot" scope.
8.  Select the "Send Messages" and "Read Message History" permissions.
9.  Copy the generated URL and paste it into your browser to add the bot to your server.

### Using the Bot

Once the bot is in your server, you can use the following commands:

*   `!ping`: Checks if the bot is online.
*   `!search <query>`: Searches for rulebook content.