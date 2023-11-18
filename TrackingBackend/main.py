import os

if os.pardir != os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.logger import setup_logger
from fastapi import FastAPI
from app.etvr import ETVR


def setup_app():
    setup_logger()
    etvr_app = ETVR()
    etvr_app.add_routes()
    app = FastAPI()
    app.include_router(etvr_app.router)
    app.mount("/images", StaticFiles(directory="assets/images"))
    app.add_route("/", FileResponse("assets/index.html"), methods=["GET"])

    return app


def main() -> int:
    import uvicorn
    import sys

    port: int = 8000
    host: str = "127.0.0.1"
    args = sys.argv[1:]
    for i, v in enumerate(args):
        try:
            match v:
                case "--help" | "-h":
                    print("Usage: python main.py [OPTIONS]")
                    print("Options:")
                    print(f"--port [PORT]    Set the port to listen on. Default: {port}")
                    print(f"--host [HOST]    Set the host to listen on. Default: {host}")
                    print(f"--help, -h       Show this help message and exit")  # noqa: F541
                    return 0
                case "--port":
                    if int(args[i + 1]) > 65535:
                        print("Port must be between 0 and 65535!")
                        return 1
                    port = int(args[i + 1])
                case "--host":
                    host = args[i + 1]
                case _:
                    if v.startswith("-"):
                        print("Unknown argument " + v)
        except IndexError:
            print("Missing value for argument " + v)
            return 1
        except ValueError:
            print("Invalid value for argument " + v)
            return 1

    app = setup_app()
    uvicorn.run(app=app, host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    import multiprocessing
    import sys

    # check if we are running directly, if so, warn the user
    if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
        print("WARNING: backend is being run directly but has not been compiled into an executable!")
        print("It is recomended to start the backend using uvicorn CLI when not compiled as an executable.")
    else:
        multiprocessing.freeze_support()
    raise SystemExit(main())
