from shutil import which, rmtree
import platform
import sys
import os


def install():
    if which("poetry") is None:
        if input("Poetry is missing, would you like to install it? [y/n]").lower() in ["y", "yes"]:
            print("Installing poetry...")
            if platform.system() == "Windows":
                os.system("powershell '(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -'")
            elif platform.system() in ["Linux", "Darwin"]:
                os.system("curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -")
            else:
                print("Unkonwn platform, please install poetry manually.")
        print("Please restart your terminal and verify that poetry is installed before running this script again.")
    else:
        os.system("poetry install")


def lint():
    print("Running black for code formatting...")
    os.system(f"poetry run black eyetrackvr_backend{os.path.sep}")
    print("-" * 80)

    print("Running ruff for linting...")
    os.system(f"poetry run ruff check eyetrackvr_backend{os.path.sep}")
    print("-" * 80)

    print("Running mypy for type checking...")
    os.system(f"poetry run mypy --ignore-missing-imports --check-untyped-defs eyetrackvr_backend{os.path.sep}")
    print("-" * 80)

    print("Running pytest for unit testing...")
    os.system(f"poetry run pytest eyetrackvr_backend{os.path.sep}")
    print("-" * 80)


def clean():
    print("Cleaning build and cache directories...")

    for folder in ["build", "dist", ".ruff_cache", ".pytest_cache", ".mypy_cache"]:
        if os.path.exists(folder):
            print(f"Deleting {folder}")
            rmtree(folder)

    for root, dirs, _ in os.walk(".", topdown=False):
        for name in dirs:
            if name == "__pycache__":
                print(f"Deleting {os.path.join(root, name)}")
                rmtree(os.path.join(root, name))


def build():
    os.system("poetry run pyinstaller ETVR.spec")


def profile():
    try:
        os.system("poetry run viztracer -m eyetrackvr_backend.__main__")
    except KeyboardInterrupt:
        exit(0)


def run():
    os.system("poetry run uvicorn --factory eyetrackvr_backend:setup_app --reload --port 8000")


def emulate():
    print("This is still a work in progress, please check back later!")


def help():
    print("Usage: python build.py [OPTIONS]")
    print("Options:")
    print("lint            Run the linter, formatter, type checker, and unit tester")
    print("run             Run the ETVR backend server in development mode")
    print("build           Build and bundle the project with pyinstaller")
    print("profile         Run the ETVR backend server with viztracer")
    print("emulate         Start the algorithm debugger and emulator")
    print("install         Install project dependencies")
    print("clean           Clean intermediate files")
    print("help            Show this help message and exit")


if __name__ == "__main__":
    if which("poetry") is None:
        install()
    else:
        # i dont want to use argparse so we are doing this the sketchy way
        try:
            eval(sys.argv[1].lower() + "()")
        except IndexError:
            help()
