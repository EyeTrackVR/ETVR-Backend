# EyeTrackVR Python Tracking Backend

This is the eye tracking backend for the [new EyeTrackVR App](https://github.com/EyeTrackVR/EyeTrackVR/tree/SolidJSGUI). \
As this project is still in heavy development its API can and will change without warning!

## Setting up a development enviroment
### Requirements
- [Git CLI](https://git-scm.com/downloads)
- [Python ~3.11](https://www.python.org/downloads/)
- [Poetry <1.6.0](https://python-poetry.org/docs/#installation)
- [A good text editor](https://neovim.io/)

### Setup
1. Install the latest version of the [Git CLI](https://git-scm.com/downloads)

2. Install and setup a version of [Python 3.11](https://www.python.org/downloads/)

3. Install [Poetry](https://python-poetry.org/docs/#installation) (*it is recomened you install poetry globally with the shell script and not pip*)

4. Clone this repository with
```bash
git clone --recusive https://github.com/EyeTrackVR/ETVR-Backend.git
```

5. navigate into the cloned repository
```bash
cd ETVR-Backend
```

6. Install project dependencies with poetry
```bash
poetry install --no-root
```

### Running a development server
By default the development server will be hosted on `http://127.0.0.1:8000/` \
The backend is controlled entirely through its rest API by itself this backend does not provide a GUI, i recomend reading the docs located at `http://127.0.0.1:8000/docs#/` to get a better understanding of how the app and it's API works.

Please note that by default hot reloading is enabled, saving code while processes are active can result in undefined behavour! \
To start the local development server run either of the following commands.
```bash
python build.py run
```
```bash
cd TrackingBackend/ && poetry run uvicorn --factory main:setup_app --reload --port 8000
```

### Profiling
If you encounter any performance issues you can profile the backend using [viztracer](https://github.com/gaogaotiantian/viztracer). \
To start profiling run the following command, this will start the backend and generate a `result.json` which can be opened with `vizviewer` \
If you dont like viztracer you can use almost any other profiler (multi-processing and multi-threading support is required)\
*currently using the build script to start profiling is broken*
```bash
cd TrackingBackend/ && poetry run viztracer main.py
```

### Running the CI/CD pipeline locally
This project utilizes the following in its automated CI/CD pipeline: \
`black` for code formatting, `ruff` for linting, `pytest` for unit testing and `mypy` for type checking. \
To run the CI/CD pipeline locally you can use the lint command in the build script.
```bash
python build.py lint
```

### Building the backend
Building the backend is done with pyinstaller, the build script will automatically install pyinstaller and bundle the backend into a single executable. \
*On linux you may need to install pyinstaller using your package manager*
```bash
python build.py build
```
If you want to build the backend manually you can do so with the following command.
```bash
poetry run pyinstaller ETVR.spec TrackingBackend/main.py
```