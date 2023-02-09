from app.logger import setup_logger
from app.etvr import ETVR
from fastapi import FastAPI

setup_logger()


etvr_app = ETVR()
etvr_app.add_routes()
app = FastAPI()
app.include_router(etvr_app.router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}
