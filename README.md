# EyeTrackVR App Python Backend

This is the Python backend for the [new EyeTrackVR App](https://github.com/EyeTrackVR/EyeTrackVR/tree/SolidJSGUI). It is a FastAPI app that runs as an `exe` and communicates with the EyeTrackVR App via WebSockets.

## Setup Dev Environment

The cleanest way to setup the dev-environment for the python-backend is to use Virtual Environments.

First, install `virtualenv` to your local machines python interpreter.

```bash
pip install virtualenv
```

Next, navigate to the root of the project and enable the `virtualenv` module.

```bash
python<version> -m venv <virtual-environment-name>
```

Example:

```bash
python3.10 -m venv venv
```

> [!NOTE]\
> You may need to run `python venv` or `python -m venv` without the python version depending on your setup.

Now that you have created the virtual environment, you will need to activate it before you can use it.

You don’t specifically need to activate a virtual environment, as you can just specify the full path to that environment’s Python interpreter when invoking Python. Furthermore, all scripts installed in the environment should be runnable without activating it.

In order to achieve this, scripts installed into virtual environments have a “shebang” line which points to the environment’s Python interpreter, i.e. `#!/<path-to-venv>/bin/python`. This means that the script will run with that interpreter regardless of the value of PATH. On Windows, “shebang” line processing is supported if you have the `Python Launcher for Windows` installed. Thus, double-clicking an installed script in a Windows Explorer window should run it with the correct interpreter without the environment needing to be activated or on the PATH.

When a virtual environment has been activated, the VIRTUAL_ENV environment variable is set to the path of the environment. Since explicitly activating a virtual environment is not required to use it, VIRTUAL_ENV cannot be relied upon to determine whether a virtual environment is being used.

```bash
source <path_to_venv>/bin/activate
```

or

```bash
<path_to_venv>\Scripts\Activate.ps1
```

or

```bash
<path_to_venv>\Scripts\activate
```

One the virtual environment is install and activated, or you have selected its interpreter, you need to install the project dependencies.

We will proceed as if you have activated the virtual environment, as that is the most common usage.

First, install poetry.

```bash
pip install poetry
```

Next, use poetry to install and manage project dependencies.

```bash
poetry install
```

## Running the app

> [!NOTE]\
> Make sure `poetry` and `python ^3.10.0` is installed on your system.  
> **Development**: For development run uvicorn with the `--reload` flag.

1. Clone the repository
2. Open up a terminal
3. Run `poetry install` in the root directory
4. Change into the app's directory `cd TrackingBackend`
5. Start the app `poetry run uvicorn --factory main:setup_app`

## Building the app
>
> [!NOTE]\
> Make sure `poetry` and `python ^3.10.0` is installed on your system.

1. Clone the repository
2. Open up a terminal
3. Run `poetry install` in the root directory
4. Build the app with `poetry run pyinstaller ETVR.spec TrackingBackend/main.py`
