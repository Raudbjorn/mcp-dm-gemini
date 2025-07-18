# Usage Guide

This guide will show you how to use the TTRPG Assistant's web interface and command-line interface (CLI).

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
