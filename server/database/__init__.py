# database/__init__.py
from .connection import init_db, get_db
from .router import router as db_router
