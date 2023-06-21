# EyeTrackVR App Python Backend

This is the Python backend for the EyeTrackVR App. It is a FastAPI app that runs as an `exe` and communicates with the EyeTrackVR App via WebSockets.

## Running the app
> **Note**: Make sure `poetry` and `python ^3.11.0` is installed on your system.
1. Open the project in VSCode
2. Open a terminal (Ctrl+Shift+`)
3. Run `poetry install`
4. Run `cd TrackingBackend/ && poetry run uvicorn main:app`
