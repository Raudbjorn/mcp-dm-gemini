# Project Tasks

This document outlines the tasks for the development of the TTRPG Assistant.

## Phase 1: Core Functionality (Completed)

- [x] Implement PDF parsing to extract text and structure from rulebooks.
- [x] Set up Redis database for storing content chunks.
- [x] Implement vector embedding generation and storage.
- [x] Create a semantic search tool (`search`).
- [x] Create a tool to add new sources (`add_source`).
- [x] Develop tools for generating character backstories and NPCs (`generate_backstory`, `generate_npc`).
- [x] Implement session management tools (`manage_session`).
- [x] Implement map generation (`generate_map`).
- [x] Implement content packaging (`create_content_pack`, `install_content_pack`).

## Phase 2: Documentation and Support

- [x] Create comprehensive documentation for installation and configuration.
- [x] Update `README.md` to be a user-friendly entry point.
- [x] Add instructions for integrating with the Claude.ai desktop tool.
- [x] Clean up the codebase, removing dead and commented-out code.
- [x] Set up containerization with Docker (`Dockerfile`, `docker-compose.yml`).
- [x] Implement a CI/CD pipeline with GitHub Actions for automated testing.
- [x] Create a suite of tests for the application's tools and services.
- [x] Update design, requirements, and task documents to reflect the current state of the project.

## Future Work (Backlog)

- **Web UI**: Develop a simple web interface for interacting with the assistant's tools.
- **Expanded Content Support**: Add support for other document formats besides PDF (e.g., EPUB, plain text).
- **Advanced Map Generation**: Improve the map generator to create more complex and varied maps.
- **More Game Systems**: Add pre-packaged content and specialized support for more TTRPG systems.
- **Cloud Deployment**: Create guides and scripts for deploying the assistant to cloud services.
- **Improved Testing**: Increase test coverage to include more edge cases and integration tests.
