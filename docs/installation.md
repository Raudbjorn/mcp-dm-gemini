# Installation Guide

This guide will walk you through setting up the TTRPG Assistant on your local machine.

## Prerequisites

Before you begin, you will need to install a few things:

1.  **Python**: This project requires Python 3.10 or newer. You can download it from the [official Python website](https://www.python.org/downloads/). When installing, make sure to check the box that says "Add Python to PATH".

2.  **Git**: You'll need Git to download the project files. You can get it from the [Git website](https://git-scm.com/downloads).

3.  **Redis**: The assistant uses Redis to store data. The easiest way to get Redis running is with Docker.
    *   Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
    *   Once Docker is running, open a terminal (like PowerShell or Command Prompt) and run the following command to start a Redis container:
        ```sh
        docker run -d -p 6379:6379 --name ttrpg-redis redis/redis-stack:latest
        ```

## Installation Steps

1.  **Open a Terminal**: You can use PowerShell or Command Prompt on Windows.

2.  **Clone the Repository**: Use `git` to download the project code.
    ```sh
    git clone https://github.com/Raudbjorn/mcp-dm-gemini.git
    ```

3.  **Navigate to the Project Directory**:
    ```sh
    cd mcp-dm-gemini
    ```

4.  **Install Dependencies**: This project uses `uv` to manage its dependencies. The `bootstrap.sh` script can set this up for you.
    ```sh
    ./bootstrap.sh
    ```
    This will install `uv` and then use it to install all the required Python packages.

## Running the Assistant

Once everything is installed, you can start the TTRPG Assistant.

1.  **Run the main script**:
    ```sh
    uv run main.py
    ```

2.  The assistant is now running and ready to be used with a compatible tool, like the Claude.ai desktop app. See the [Configuration](configuration.md) guide for details on how to connect it.

## Stopping the Assistant

To stop the assistant, press `Ctrl+C` in the terminal where it is running.

To stop the Redis container, run this command in your terminal:
```sh
docker stop ttrpg-redis
```
