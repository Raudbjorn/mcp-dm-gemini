# Requirements

This document outlines the functional and non-functional requirements for the TTRPG Assistant.

## 1. Functional Requirements

### 1.1. Core Features
- The system must allow users to add TTRPG source material from PDF files.
- The system must provide a semantic search capability to query the added source material.
- The system must be able to generate character backstories and NPCs based on the source material.
- The system must provide tools for managing a game session, including notes and combat tracking.
- The system must be able to generate simple maps for combat encounters.
- The system must allow for the creation and installation of content packs.

### 1.2. Integration
- The system must expose its tools via the Model-Context-Protocol (MCP).
- The system must be configurable to work with MCP-compatible clients, such as the Claude.ai desktop application.

## 2. Non-Functional Requirements

### 2.1. Performance
- Search queries should return results in a timely manner (e.g., under 2 seconds).
- PDF processing time will vary depending on the size of the document but should be reasonable for typical TTRPG rulebooks.

### 2.2. Usability
- The project must include clear documentation for installation, configuration, and usage.
- The installation process should be straightforward for users with varying technical skill levels.

### 2.3. Reliability
- The system should be stable and handle errors gracefully.
- The application should have a suite of automated tests to ensure its correctness.

### 2.4. Maintainability
- The codebase should be clean, well-documented, and easy to understand.
- Dead or commented-out code should be removed.

### 2.5. Portability
- The application must be runnable on common operating systems (Windows, macOS, Linux).
- The application must be containerizable using Docker for easy deployment.

## 3. Technical Requirements

- **Programming Language**: Python (version 3.10 or newer)
- **Database**: Redis (specifically, a version that includes the RediSearch and RedisJSON modules, like `redis/redis-stack`).
- **Dependencies**: All Python dependencies are listed in `requirements.txt`.
- **CI/CD**: The project must have a continuous integration pipeline set up (e.g., using GitHub Actions).