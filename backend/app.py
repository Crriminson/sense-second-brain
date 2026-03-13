# app.py
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from network import print_connection_qr
from interfaces.sockets import router as sockets_router
from interfaces.rest import router as rest_router
from interfaces.auth import router as auth_router
from store.sql.connection import init_db
from starlette.middleware.sessions import SessionMiddleware
import secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Print the QR code exactly when the server starts
    print_connection_qr()
    try:
        yield
    except asyncio.CancelledError:
        # Uvicorn/Starlette can cancel lifespan receive on Ctrl+C in dev.
        pass
    finally:
        print("\n[SERVER] Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

# Add the websocket routes to the app
app.include_router(sockets_router)
app.include_router(rest_router, prefix="/api")
app.include_router(auth_router, prefix="/auth")

# Basic health check
@app.get("/")
def read_root():
    return {"status": "Second Brain is running"}

if __name__ == "__main__":
    # Host 0.0.0.0 is REQUIRED so the phone can connect over WiFi
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_excludes=[
                "*.db",
                "*.db-wal",
                "*.db-shm",
                "chroma_data/*",
                "*.pyc",
                "__pycache__/*",
                "*.log",
            ],
        )
    except KeyboardInterrupt:
        # Ctrl+C during dev shutdown can bubble KeyboardInterrupt from asyncio.
        pass
