# EyeTrackVR App Python Backend

This is the Python backend for the EyeTrackVR App. It is a FastAPI app that runs as an `exe` and communicates with the EyeTrackVR App via WebSockets.

## Installation

This app uses a `vscode devcontainer` to run in a Docker container. This is the recommended way to run the app. If you want to run it outside of the container, you will need to install the dependencies using the provided poetry implementation.

## Requirements

- Docker or Docker Desktop (windows - running on WSL2 backend)
- VSCode
- VSCode Dev Containers extension

## Running the app

1. Open the project in VSCode
2. Open the command palette (Ctrl+Shift+P)
3. Select `Dev-Containers: Reopen in Container`
4. Wait for container to finish building (first time only) Open a terminal (Ctrl+Shift+`)
5. Run `make` to run the app


## Running the app outside of the container

### Install dependencies

> **Note**: Make sure `make` is installed on your system.

1. Open the project in VSCode
2. Open a terminal (Ctrl+Shift+`)
3. Run `make install`

### Run the app

1. Open the project in VSCode
2. Open a terminal (Ctrl+Shift+`)
3. Run `make` to run the app
