"""
Notes API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.database import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new note
    
    - **title**: Note title (required)
    - **content**: Note content in Markdown format (required)
    - **tags**: List of tags (optional)
    """
    note = Note(
        title=note_data.title,
        content=note_data.content,
        tags=note_data.tags or []
    )
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    return note


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all notes with pagination
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10, max: 100)
    - **tag**: Filter by tag (optional)
    - **search**: Search keyword (optional)
    """
    # Build query
    query = select(Note)
    
    # Filter by tag
    if tag:
        query = query.where(Note.tags.contains([tag]))
    
    # Search in title and content
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term)
            )
        )
    
    # Order by updated_at descending
    query = query.order_by(Note.updated_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(Note)
    if tag:
        count_query = count_query.where(Note.tags.contains([tag]))
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term)
            )
        )
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    notes = result.scalars().all()
    
    return NoteListResponse(
        total=total,
        page=page,
        limit=limit,
        notes=notes
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific note by ID
    
    - **note_id**: Note ID
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing note
    
    - **note_id**: Note ID
    - **title**: New title (optional)
    - **content**: New content (optional)
    - **tags**: New tags (optional)
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update fields if provided
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    await db.commit()
    await db.refresh(note)
    
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a note
    
    - **note_id**: Note ID
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    await db.delete(note)
    await db.commit()
    
    return None
