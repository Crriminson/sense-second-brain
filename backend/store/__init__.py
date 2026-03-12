# Exports: init_store, and sub-modules
from .sql import connection, workspaces, notes, sessions, edges
from .vectors import search

def init_store():
    print("Store initialized")
    connection.init_db()
