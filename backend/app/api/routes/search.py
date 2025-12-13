"""
Search API Routes
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.note import Note
from app.schemas.note import NoteListItem, NoteListResponse
from app.services.search_service import search_notes_fts, get_search_count

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=NoteListResponse)
async def search_notes(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    全文搜索笔记
    
    支持查询语法：
    - `python` - 包含 python
    - `python OR java` - 包含 python 或 java  
    - `python AND java` - 同时包含两者
    - `python NOT java` - 包含 python 但不包含 java
    - `"machine learning"` - 短语搜索
    
    **Examples:**
    - `/api/search?q=python`
    - `/api/search?q=python+AND+fastapi`
    - `/api/search?q="deep+learning"`
    """
    offset = (page - 1) * limit
    
    # 使用 FTS5 搜索
    results = await search_notes_fts(db, q, limit, offset)
    total = await get_search_count(db, q)
    
    # 转换为 NoteListItem
    notes = []
    for row in results:
        row_dict = row._mapping
        # 解析 tags JSON 字符串
        tags = json.loads(row_dict['tags']) if row_dict['tags'] else []
        note = NoteListItem(
            id=row_dict['id'],
            title=row_dict['title'],
            tags=tags,
            summary=row_dict['summary'],
            file_path=row_dict['file_path'],
            file_modified_time=row_dict['file_modified_time'],
            created_at=row_dict['created_at'],
            updated_at=row_dict['updated_at']
        )
        notes.append(note)
    
    return NoteListResponse(
        total=total,
        page=page,
        limit=limit,
        notes=notes
    )
