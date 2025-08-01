# Configuration

This document provides instructions on how to configure various parts of the TTRPG Assistant.

## Claude.ai Desktop Tool Integration

To use this project as a tool with the Claude.ai desktop application, you need to configure it as an MCP (Model-Context-Protocol) server.

1.  **Locate your Claude configuration file.** On Windows, this is typically found at:
    ```
    %APPDATA%\Claude\claude_desktop_config.json
    ```
    You can paste that path into your File Explorer address bar to find it.

2.  **Edit the configuration file.** Open `claude_desktop_config.json` in a text editor and add the following configuration to the `mcpServers` object. If `mcpServers` doesn't exist, you'll need to add it.

    ```json
    {
      "mcpServers": {
        "ttrpg_assistant": {
          "command": "uv",
          "args": [
            "--directory",
            "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\dn",
            "run",
            "main.py"
          ]
        }
      }
    }
    ```

    **Important:** Replace `C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\dn` with the absolute path to the `dn` directory where you cloned this project. Remember to use double backslashes (`\\`) for the path separators in the JSON file.

3.  **Save the file and restart the Claude.ai desktop app.**

Once configured, the Claude.ai desktop application will be able to use the tools provided by this TTRPG Assistant.

For more information on MCP servers, you can refer to the official documentation: [MCP Quickstart: Server](https://modelcontextprotocol.io/quickstart/server)