"""
Obsidian Integration API Routes
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.note import Note
from app.services.obsidian_service import ObsidianService, get_obsidian_service
from pydantic import BaseModel

router = APIRouter(prefix="/obsidian", tags=["Obsidian"])
logger = logging.getLogger(__name__)


class ImportResponse(BaseModel):
    """导入响应"""
    total_files: int
    imported: int
    updated: int
    skipped: int
    failed: int
    message: str


class SyncStatus(BaseModel):
    """同步状态"""
    vault_path: str
    total_notes_in_vault: int
    total_notes_in_db: int
    last_sync: Optional[str] = None


@router.post("/import", response_model=ImportResponse)
async def import_obsidian_vault(
    force_update: bool = False,
    db: AsyncSession = Depends(get_db),
    obsidian: ObsidianService = Depends(get_obsidian_service)
):
    """
    从 Obsidian vault 导入所有笔记到数据库
    
    - **force_update**: 是否强制更新已存在的笔记（默认只导入新笔记）
    """
    try:
        # 获取所有笔记文件
        vault_notes = obsidian.get_all_notes()
        
        stats = {
            "total_files": len(vault_notes),
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        }
        
        for vault_note in vault_notes:
            try:
                # 检查数据库中是否已存在
                result = await db.execute(
                    select(Note).where(Note.file_path == vault_note.file_path)
                )
                existing_note = result.scalar_one_or_none()
                
                if existing_note:
                    if force_update:
                        # 更新现有笔记
                        existing_note.title = vault_note.title
                        existing_note.content = vault_note.content
                        existing_note.tags = vault_note.tags
                        existing_note.file_modified_time = vault_note.modified_time
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                        continue
                else:
                    # 创建新笔记
                    new_note = Note(
                        title=vault_note.title,
                        content=vault_note.content,
                        tags=vault_note.tags,
                        file_path=vault_note.file_path,
                        file_modified_time=vault_note.modified_time
                    )
                    db.add(new_note)
                    stats["imported"] += 1
                
            except Exception as e:
                logger.error(f"Failed to import {vault_note.file_path}: {str(e)}")
                stats["failed"] += 1
        
        await db.commit()
        
        message = f"Import completed: {stats['imported']} new, {stats['updated']} updated, {stats['skipped']} skipped, {stats['failed']} failed"
        logger.info(message)
        
        return ImportResponse(**stats, message=message)
        
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")


@router.get("/status", response_model=SyncStatus)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    obsidian: ObsidianService = Depends(get_obsidian_service)
):
    """
    获取同步状态
    """
    try:
        # 统计 vault 中的文件数
        vault_notes = obsidian.get_all_notes()
        
        # 统计数据库中的笔记数
        result = await db.execute(select(func.count()).select_from(Note))
        db_count = result.scalar()
        
        return SyncStatus(
            vault_path=obsidian.vault_path,
            total_notes_in_vault=len(vault_notes),
            total_notes_in_db=db_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{note_id}")
async def export_note_to_vault(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    obsidian: ObsidianService = Depends(get_obsidian_service)
):
    """
    将数据库中的笔记导出到 Obsidian vault
    
    - **note_id**: 笔记 ID
    """
    try:
        # 获取笔记
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # 构建笔记数据
        note_data = {
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "summary": note.summary
        }
        
        # 写入文件
        file_path = obsidian.write_note_to_file(note_data, note.file_path)
        
        # 更新数据库中的文件路径
        if not note.file_path:
            note.file_path = file_path
            await db.commit()
        
        return {
            "message": "Note exported successfully",
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.post("/sync/full")
async def full_sync(
    db: AsyncSession = Depends(get_db),
    obsidian: ObsidianService = Depends(get_obsidian_service)
):
    """
    执行完全同步：将 vault 中的所有变化同步到数据库
    用于手动触发同步或修复不一致状态
    """
    try:
        # 获取 vault 中所有笔记
        vault_notes = obsidian.get_all_notes()
        vault_paths = {note.file_path for note in vault_notes}
        
        stats = {
            "vault_total": len(vault_notes),
            "db_total": 0,
            "synced": 0,
            "added": 0,
            "updated": 0,
            "deleted": 0
        }
        
        # 获取数据库中所有笔记
        result = await db.execute(select(Note))
        db_notes = result.scalars().all()
        stats["db_total"] = len(db_notes)
        
        # 1. 更新/添加 vault 中的笔记
        for vault_note in vault_notes:
            result = await db.execute(
                select(Note).where(Note.file_path == vault_note.file_path)
            )
            existing_note = result.scalar_one_or_none()
            
            if existing_note:
                # 检查是否需要更新（比较修改时间）
                if vault_note.modified_time and existing_note.file_modified_time:
                    if vault_note.modified_time > existing_note.file_modified_time:
                        existing_note.title = vault_note.title
                        existing_note.content = vault_note.content
                        existing_note.tags = vault_note.tags
                        existing_note.file_modified_time = vault_note.modified_time
                        stats["updated"] += 1
                    else:
                        stats["synced"] += 1
                else:
                    # 如果没有时间戳，强制更新
                    existing_note.title = vault_note.title
                    existing_note.content = vault_note.content
                    existing_note.tags = vault_note.tags
                    existing_note.file_modified_time = vault_note.modified_time
                    stats["updated"] += 1
            else:
                # 添加新笔记
                new_note = Note(
                    title=vault_note.title,
                    content=vault_note.content,
                    tags=vault_note.tags,
                    file_path=vault_note.file_path,
                    file_modified_time=vault_note.modified_time
                )
                db.add(new_note)
                stats["added"] += 1
        
        # 2. 删除数据库中但 vault 里不存在的笔记
        for db_note in db_notes:
            if db_note.file_path and db_note.file_path not in vault_paths:
                await db.delete(db_note)
                stats["deleted"] += 1
        
        await db.commit()
        
        return {
            "message": "Full sync completed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Full sync failed: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.get("/watcher/status")
async def get_watcher_status():
    """获取文件监控状态"""
    from app.main import file_watcher
    
    if not file_watcher:
        return {
            "enabled": False,
            "running": False,
            "message": "File watcher not configured"
        }
    
    return {
        "enabled": True,
        "running": file_watcher.is_running(),
        "vault_path": file_watcher.vault_path
    }

