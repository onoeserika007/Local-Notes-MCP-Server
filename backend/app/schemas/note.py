"""
Pydantic Schemas for Note API
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base schema for Note"""
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    tags: Optional[List[str]] = Field(default=[], description="List of tags")


class NoteCreate(NoteBase):
    """Schema for creating a new note"""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating an existing note"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    summary: Optional[str] = None


class NoteListItem(NoteBase):
    """Schema for note in list (without content)"""
    id: int
    summary: Optional[str] = None
    file_path: Optional[str] = None
    file_modified_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class NoteResponse(NoteBase):
    """Schema for note response (with content)"""
    id: int
    content: str = Field(default="", description="Note content (loaded from file if available)")
    summary: Optional[str] = None
    file_path: Optional[str] = None
    file_modified_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class NoteListResponse(BaseModel):
    """Schema for list of notes response"""
    total: int
    page: int
    limit: int
    notes: List[NoteListItem]


class NotesResponse(BaseModel):
    """Schema for notes with full content"""
    total: int
    page: int
    limit: int
    notes: List[NoteResponse]
