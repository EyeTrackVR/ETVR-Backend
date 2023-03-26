from app.logger import setup_logger
from app.etvr import ETVR
from fastapi import FastAPI, WebSocket

setup_logger()


etvr_app = ETVR()
etvr_app.add_routes()
app = FastAPI()
app.include_router(etvr_app.router)


@app.get("/hello")
async def root():
    return {"message": "Hello World!"}


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    print("[FastAPI WebSocket]: Accepting client connection...")
    await websocket.accept()
    while True:
        try:
            # Wait for any message from the client
            await websocket.receive_text()
            # Send message to the client
            # resp = {'value': random.uniform(0, 1)}
            # await websocket.send_json(resp)

            # grab camera output and send over websocket

        except Exception as e:
            print("error:", e)
            break
    print("Bye..")
