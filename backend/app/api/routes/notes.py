"""
Notes API Routes
"""
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.database import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse, NoteListItem
from app.schemas.folder import FolderItem, FolderStructureResponse
from app.core.config import settings

router = APIRouter(prefix="/notes", tags=["Notes"])


def load_note_content(note: Note) -> str:
    """从文件加载笔记内容（如果有 file_path）"""
    if note.file_path and settings.OBSIDIAN_VAULT_PATH:
        try:
            file_path = Path(settings.OBSIDIAN_VAULT_PATH) / note.file_path
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Failed to load content from {note.file_path}: {e}")
    
    # 如果文件不存在或读取失败，返回数据库中的内容（如果有）
    return note.content or ""


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
    limit: int = Query(10, ge=1, le=500, description="Items per page"),
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


@router.get("/folders", response_model=FolderStructureResponse)
async def get_folder_structure(
    path: Optional[str] = Query(None, description="Folder path, empty for root"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定路径下的文件夹结构（懒加载）
    
    - **path**: 文件夹路径，不传或空字符串表示根目录
    
    返回该路径下的所有子项（文件夹和文件）
    """
    # 获取所有笔记的 file_path
    result = await db.execute(select(Note.file_path))
    all_paths = [p[0] for p in result.all() if p[0]]
    
    # 构建该层级的项
    items_dict = {}
    
    for file_path in all_paths:
        if not file_path:
            continue
            
        parts = file_path.split('/')
        
        # 根目录
        if not path or path == '':
            if len(parts) >= 1:
                first_part = parts[0]
                if first_part not in items_dict:
                    # 判断是文件还是文件夹
                    is_folder = len(parts) > 1 or not first_part.endswith('.md')
                    items_dict[first_part] = {
                        'name': first_part,
                        'path': first_part,
                        'is_folder': is_folder,
                        'count': 0
                    }
                items_dict[first_part]['count'] += 1
        else:
            # 子目录
            # 检查是否在指定路径下
            if file_path.startswith(path + '/'):
                # 获取相对路径
                relative = file_path[len(path) + 1:]
                rel_parts = relative.split('/')
                
                if len(rel_parts) >= 1:
                    first_part = rel_parts[0]
                    full_path = f"{path}/{first_part}"
                    
                    if first_part not in items_dict:
                        is_folder = len(rel_parts) > 1 or not first_part.endswith('.md')
                        items_dict[first_part] = {
                            'name': first_part,
                            'path': full_path,
                            'is_folder': is_folder,
                            'count': 0
                        }
                    items_dict[first_part]['count'] += 1
    
    # 转换为列表并排序（文件夹在前）
    items = [
        FolderItem(
            name=item['name'],
            path=item['path'],
            is_folder=item['is_folder'],
            note_count=item['count']
        )
        for item in items_dict.values()
    ]
    items.sort(key=lambda x: (not x.is_folder, x.name))
    
    return FolderStructureResponse(items=items)


@router.get("/by-path", response_model=NoteResponse)
async def get_note_by_path(
    file_path: str = Query(..., description="File path of the note"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据文件路径获取笔记
    
    - **file_path**: 笔记的文件路径
    """
    result = await db.execute(select(Note).where(Note.file_path == file_path))
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail=f"Note not found: {file_path}")
    
    # 加载文件内容
    note.content = load_note_content(note)
    
    return note


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
    
    # 动态加载内容
    note.content = load_note_content(note)
    
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

