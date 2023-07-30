# EyeTrackVR App Python Backend

This is the Python backend for the [new EyeTrackVR App](https://github.com/EyeTrackVR/EyeTrackVR/tree/SolidJSGUI). It is a FastAPI app that runs as an `exe` and communicates with the EyeTrackVR App via WebSockets.

## Running the app
> [!NOTE]\ Make sure `poetry` and `python ^3.10.0` is installed on your system.  
> **Development**: For development run uvicorn with the `--reload` flag.
1. Clone the repository
2. Open up a terminal
3. Run `poetry install` in the root directory
4. Change into the app's directory `cd TrackingBackend`
5. Start the app `poetry run uvicorn --factory main:setup_app`

## Building the app
> [!NOTE]\ Make sure `poetry` and `python ^3.10.0` is installed on your system.
1. Clone the repository
2. Open up a terminal
3. Run `poetry install` in the root directory
4. Build the app with `poetry run pyinstaller ETVR.spec TrackingBackend/main.py`
