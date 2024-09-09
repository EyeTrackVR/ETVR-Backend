from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

from .assets import ASSETS_DIR, IMAGES_DIR
from .etvr import ETVR
from .logger import setup_logger

def setup_app():
    setup_logger()
    etvr_app = ETVR()
    etvr_app.add_routes()
    app = FastAPI()
    app.include_router(etvr_app.router)
    app.mount("/", StaticFiles(directory=ASSETS_DIR, html=True))
    app.mount("/images", StaticFiles(directory=IMAGES_DIR))
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
                    print(f"Usage: {sys.argv[0]} [OPTIONS]")
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
