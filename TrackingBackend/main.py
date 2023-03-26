from app.logger import setup_logger
from app.etvr import ETVR
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse


setup_logger()

etvr_app = ETVR()
etvr_app.add_routes()
app = FastAPI()
app.include_router(etvr_app.router)

if __name__ == "__main__":
    import uvicorn

    # since we should only be running this file directly once compiled with pyinstaller we shouldnt need to worry about
    # the reload flag because relisticly we wont be changing the code once compiled.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
