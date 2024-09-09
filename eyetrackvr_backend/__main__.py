# This is the main script run by pyinstaller
from eyetrackvr_backend import main as real_main

import multiprocessing
import sys

def main():
    # check if we are running directly, if so, warn the user
    if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
        print("WARNING: backend is being run directly but has not been compiled into an executable!")
        print("It is recommended to start the backend using uvicorn CLI when not compiled as an executable.")
    else:
        multiprocessing.freeze_support()
    raise SystemExit(real_main())


if __name__ == "__main__":
    main()
