from fastapi import FastAPI
from contextlib import asynccontextmanager
from engine import process
from interfaces import rest, sockets
from store import init_store

# FastAPI setup, mounts routes, starts services

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load models, connect to DB
    print("Sense is starting up...")
    init_store()
    yield
    # Shutdown: Disconnect DB, etc.
    print("Sense is shutting down...")

app = FastAPI(lifespan=lifespan)

app.include_router(rest.router)
app.add_websocket_route("/ws", sockets.websocket_endpoint)

@app.get("/")
async def root():
    return {"message": "Sense is online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
