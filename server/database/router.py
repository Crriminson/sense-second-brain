# database/router.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from . import crud

router = APIRouter()


# ── Request models ──

class WorkspaceInput(BaseModel):
    name: str

class NoteInput(BaseModel):
    raw_text: str
    tags: list[str] = []
    workspace_id: Optional[str] = None
    source: str = "voice"


# ═══════════════════════════════════════
#  WORKSPACES
# ═══════════════════════════════════════

@router.get("/workspaces")
async def api_list_workspaces():
    return await crud.list_workspaces()


@router.get("/workspaces/active")
async def api_active_workspace():
    ws = await crud.get_active_workspace()
    if not ws:
        raise HTTPException(404, "No active workspace")
    return ws


@router.post("/workspaces/switch")
async def api_switch_workspace(data: WorkspaceInput):
    return await crud.switch_workspace(data.name)


@router.delete("/workspaces/{workspace_id}")
async def api_delete_workspace(workspace_id: str):
    ok = await crud.delete_workspace(workspace_id)
    if not ok:
        raise HTTPException(404, "Workspace not found")
    return {"ok": True}


# ═══════════════════════════════════════
#  NOTES
# ═══════════════════════════════════════

@router.get("/notes")
async def api_list_notes(
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    return await crud.list_notes(workspace_id=workspace_id, limit=limit)


@router.get("/notes/{note_id}")
async def api_get_note(note_id: str):
    note = await crud.get_note(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.post("/notes")
async def api_create_note(data: NoteInput):
    try:
        return await crud.save_note(
            raw_text=data.raw_text,
            tags=data.tags,
            workspace_id=data.workspace_id,
            summary=data.raw_text[:80],
            source=data.source,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/notes/{note_id}")
async def api_delete_note(note_id: str):
    ok = await crud.delete_note(note_id)
    if not ok:
        raise HTTPException(404, "Note not found")
    return {"ok": True}


# ═══════════════════════════════════════
#  SESSIONS
# ═══════════════════════════════════════

@router.post("/sessions/start")
async def api_start_session():
    try:
        return await crud.start_session()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sessions/{session_id}/append")
async def api_append_transcript(session_id: str, text: str):
    ok = await crud.append_transcript(session_id, text)
    if not ok:
        raise HTTPException(404, "Session not found or not active")
    return {"ok": True}


@router.get("/sessions/{session_id}")
async def api_get_session(session_id: str):
    session = await crud.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/sessions/active")
async def api_active_session():
    session = await crud.get_active_session()
    if not session:
        raise HTTPException(404, "No active session")
    return session


# ═══════════════════════════════════════
#  GRAPH
# ═══════════════════════════════════════

@router.get("/graph")
async def api_get_graph(workspace_id: Optional[str] = Query(None)):
    return await crud.get_graph(workspace_id)


@router.get("/graph/{note_id}/edges")
async def api_get_edges(note_id: str):
    return await crud.get_edges(note_id)


# ═══════════════════════════════════════
#  STATS
# ═══════════════════════════════════════

@router.get("/stats")
async def api_stats():
    workspaces = await crud.list_workspaces()
    note_count = await crud.count_notes()
    active = await crud.get_active_workspace()
    return {
        "workspace_count": len(workspaces),
        "note_count": note_count,
        "active_workspace": active,
    }
