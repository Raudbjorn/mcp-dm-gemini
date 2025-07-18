# Installation Guide

This guide will walk you through the process of installing the TTRPG Assistant on your computer.

## Step 1: Install Python

The TTRPG Assistant is written in Python. If you don't already have Python installed, you can download it from the official website:

[https://www.python.org/downloads/](https://www.python.org/downloads/)

Download and run the installer for your operating system. During installation, make sure to check the box that says "Add Python to PATH".

## Step 2: Install Redis

The TTRPG Assistant uses a database called Redis to store its data.

### Windows

The easiest way to install Redis on Windows is to use the [Memurai](https://www.memurai.com/
) installer. Download and run the installer, and it will set up Redis to run as a service on your computer.

### macOS

The easiest way to install Redis on macOS is to use [Homebrew](https://brew.sh/). If you don't have Homebrew installed, open the Terminal app and run the following command:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Once Homebrew is installed, you can install Redis by running the following command in the Terminal:

```bash
brew install redis
```

### Linux

You can install Redis using the package manager for your Linux distribution.

**For Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install redis-server
```

**For Fedora/CentOS:**
```bash
sudo dnf install redis
```

## Step 3: Download and Run the TTRPG Assistant

1.  **Download the TTRPG Assistant:** You can download the latest version of the TTRPG Assistant from the [releases page](https://github.com/your-username/ttrpg-assistant/releases) on GitHub. Download the `ttrpg-assistant.zip` file and extract it to a folder on your computer.

2.  **Run the bootstrap script:**
    *   **On Windows:** Double-click the `bootstrap.bat` file.
    *   **On macOS and Linux:** Open the Terminal, navigate to the folder where you extracted the TTRPG Assistant, and run the following command:
        ```bash
        chmod +x bootstrap.sh
        ./bootstrap.sh
        ```

The bootstrap script will set up the TTRPG Assistant and start the server. You can then access the web interface at [http://localhost:8000/ui](http://localhost:8000/ui).
