# Release v0.1.0

This is the initial release of the TTRPG Assistant.

## Features

*   **Rulebook Management**: Add and search TTRPG rulebooks from PDF files.
*   **Content Generation**: Create character backstories, NPCs, and combat maps.
*   **Session Management**: Tools to track initiative, notes, and monsters during a game.
*   **Content Packaging**: Bundle your source material into shareable content packs.
*   **MCP Server**: Exposes all features through the Model-Context-Protocol for integration with tools like the Claude.ai desktop app.

## Improvements

*   **Documentation**: Added comprehensive guides for installation, configuration, and usage.
*   **Code Quality**: Cleaned up the codebase by removing dead and commented-out code.
*   **CI/CD**: Set up a GitHub Actions workflow to automate testing.
*   **Testing**: Added an initial suite of tests for the core tools.
*   **Project Management**: Updated `design.md`, `requirements.md`, and `tasks.md` to reflect the current state of the project.

Can you review the project so far and conceptualize use-cases, especially by non-technical users, and come up with improvements and additional features that will make this software better and friendlier to use. Do not implement them; I simply want you to update the ./design.md, ./requirements.md, and finally, ./tasks.md, files. Once you're done doing that, please commit and push the changes to the files. You may then start using the entire project context to implement the new features.

Please create/improve/update documentation with instructions on how to use "$env:AppData\Claude\claude_desktop_config.json"(on windows) to congfigure the claude.ai desktop tool:
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\weather",
        "run",
        "weather.py"
      ]
    }
  }
}
with a link to: https://modelcontextprotocol.io/quickstart/server

Please go over the codebase and remove any dead code and commented-out code.


 Please create/improve/update comprehensive documentation, aimed at non-technical users, explaining how to install and run the project. Please reference this documentation in the README.md.

 Please create/improve/update ancillary support for installing, running, and testing. By that I mean appropriate containerization(eg. docker/podman), and suitable CI/CD support elements(e.g. github actions).

 Please create/improve/update tests for whatever code made so far, and make sure they run.

 Please update the ./design.md, ./requirements.md, and finally, ./tasks.md, files to retroactively reflect these improvements.

 Please add a way to add non-rulebook source material -this should influence/impact character/NPC background and stories, model personalities etc -everything except for the parts of the MCP code that provides rule search/use/applications. Essentially I want there to be a way to add "flavor", for example, if someone wants to run a D&D campaign in Icewind Dale, you could add the Drizzt Do'Urden books by R.A. Salvatore, or if running a Shadowrun campaign, you could add Snow Crash by Neal Stephenson and/or Neuromancer by William  Gibson to increase immersion and quality of the assistant, allowing further focus on the needs of the DM for details on the setting, allowing the assistant to anticipate needs and improve experience.  Please add and update tests for this feature, and update documentation.  Please update the ./design.md, ./requirements.md, and finally, ./tasks.md, files to retroactively reflect these improvements.  Please create/improve tests for whatever code made so far, and make sure they run. Then commit and push changes.


 Please add a feature for allowing the DM to generate/create a map for potential use in combat situations based in the game system, based on the rulebook(so include a grid appropriate to the unit of measure for combat movement in the source rulebook). For Blades in the Dark this could be for example a  "victorian" style blueprint of the mansion the gang is doing a heist, in D&D, it might be a dungeon or a cave.  Please add and update tests for this feature, and update documentation.  Please update the ./design.md, ./requirements.md, and finally, ./tasks.md, files to retroactively reflect these improvements.  Please create/improve tests for whatever code made so far, and make sure they run. Then commit and push changes.


 Please create/improve tests for whatever code made so far, and make sure they run. Then commit and push changes.
https://github.com/Raudbjorn/mcp-dm-gemini