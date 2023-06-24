import os
# change working directory to the root of the project
# i should make this a package so we can use relative imports
if os.pardir != os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
from app.logger import setup_logger
from fastapi import FastAPI
from app.etvr import ETVR

setup_logger()

etvr_app = ETVR()
etvr_app.add_routes()
app = FastAPI()
app.include_router(etvr_app.router)

if __name__ == "__main__":
    import uvicorn

    # since we should only be running this file directly once compiled with pyinstaller we shouldnt need to worry about reloading on the fly
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
