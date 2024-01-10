- [EyeTrackVR Backend](#eyetrackvr-backend)
    - [Development](#development)
        - [Requirements](#requirements)
        - [Application Architecture](#application-architecture)
        - [Setting Up A Development Enviroment](#setting-up-a-development-enviroment)
        - [Starting The Development Server](#starting-the-development-server)
        - [The Build Script](#the-build-script)
    - [Build Script Commands](#build-script-commands)
        - [Running The CI/CD Pipeline Locally](#running-the-cicd-pipeline-locally)
        - [Building The Backend](#building-the-backend)
        - [Profiling](#profiling)
    - [License](#license)


# EyeTrackVR Backend
This is the eye tracking backend for the [new EyeTrackVR App](https://github.com/EyeTrackVR/SolidJSGUI). \
As this project is still in heavy development its API can and will change without warning!

<!-- TODO: maybe ddd section on IR emitter safety? -->

## Development
### Requirements
- [Git CLI](https://git-scm.com/downloads)
- [Python ~3.11](https://www.python.org/downloads/)
- [Poetry >1.6.0](https://python-poetry.org/docs/#installation)
- [A good text editor](https://neovim.io/)

<!-- TODO: firgure out how to explain complex multi-proccessing shit better -->
### Application Architecture
*This documentation is meant to give a high level overview of the backend, things have been simplified for the sake of my sanity.*

To avoid performance problems within python itself this backend has been designed in a *unique* slightly non-pythonic way. \
The main performance bottleneck in python is the GIL (Global Interpreter Lock) which prevents multiple threads from running at the same time, we can get around this by using multiple processes instead of threads. \
So thats exactly what we do, each computationally expensive task is run in its own process, this allows us to utilize all of the CPU cores on the system while completely avoiding the GIL. \
At runtime the backend will spawn 3 sub-processes per active `Tracker` instance, this means that if you have 2 active trackers defined in the config we will spawn 6 sub-processes,
meaning in total the backend will have 7 processes running, this may seem like a lot but it doesnt impact overall system performance as much as you would think.

Rundown of the processes:
* Main Process (Only 1 will ever exist): \
    This process is responsible for spawning and managing all other processes, it also handles the rest API and config management
* Manager Process (Only 1 will ever exist): \
    This process is responsible for managing all IPC (Inter Process Communication) between the main process and all sub-processes
*  Camera Process (Each active tracker will have 1): \
    This process is responsible for capturing images from the camera and sending them to the `tracker` process
* Tracker Process (Each active tracker will have 1): \
    This process is responsible for processing the images sent by the `camera` process, it does this by running algorithms
    (defined in the config) on the image and then sending the results to the `OSC` process
* OSC Process (Each active tracker will have 1): \
    This process is responsible for sending the results from the `tracker` process to the OSC server defined in the config

All processes communicate with each other using IPC (Inter Process Communication) and are completely isolated from each other,
this means that if one process crashes it will not affect any other processes and we can simply restart the crashed process without having to restart the entire backend. \
If you are wondering how we keep a updated copy of the config in each process, the short answer is we dont directly share the config between processes because it is impossible to share a nested dict (trust me i tried for months),
instead we spawn a thread in each process that listens for changes in the config file, once a change is detected the thread will update the processes copy of the config and trigger callback functions depending on what changed. \
This means that if you change the config file while the backend is running the changes will be propegated and applied to all processes without having to restart any components of the backend.

### Setting up a development enviroment
1. Install the latest version of the [Git CLI](https://git-scm.com/downloads)

2. Install and setup a version of [Python 3.11](https://www.python.org/downloads/)

3. Install [Poetry >1.6.0](https://python-poetry.org/docs/#installation) \
(*it is recomened you install poetry globally with the shell script and not pip*)

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

### Starting the development server
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

### The build script
This project uses a custom build script to automate common tasks such as linting, testing and building. \
To see a list of all available commands run the following command.
```bash
python build.py help
```


## Build Script Commands
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

### Profiling
If you encounter any performance issues you can profile the backend using [viztracer](https://github.com/gaogaotiantian/viztracer). \
To start profiling run the following command, this will start the backend and generate a `result.json` which can be opened with `vizviewer` \
If you dont like viztracer you can use almost any other profiler (multi-processing and multi-threading support is required)\
*currently using the build script to start profiling is broken!*
```bash
cd TrackingBackend/ && poetry run viztracer main.py
```


## License
Unless explicitly stated otherwise all code contained within this repository is under the [MIT License](./LICENSE)