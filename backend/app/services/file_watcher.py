"""
文件监控服务 - 监控 Obsidian vault 目录的文件变化

设计原则：
- 不依赖移动事件，只处理创建/修改/删除
- 使用 file_path 作为唯一标识，不依赖自增 ID
- 所有状态存储在数据库中，不依赖内存状态或时间窗口
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from threading import Thread

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, 
    FileSystemEvent,
    FileMovedEvent,
    DirMovedEvent
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.obsidian_service import ObsidianService
from app.services.vector_service import embed_note, delete_note_embedding
from app.models.note import Note
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """处理 Markdown 文件的变化事件"""
    
    def __init__(self, vault_path: str, obsidian_service: ObsidianService):
        self.vault_path = Path(vault_path)
        self.obsidian_service = obsidian_service
        # 为事件处理创建新的事件循环
        self.loop = None
        self.thread = None
        self._start_event_loop()
        
    def _start_event_loop(self):
        """在单独的线程中启动事件循环"""
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=run_loop, args=(self.loop,), daemon=True)
        self.thread.start()
        
    def _schedule_coroutine(self, coro):
        """将协程调度到事件循环"""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        
    def on_created(self, event: FileSystemEvent):
        """文件创建事件 - 直接创建新记录"""
        if not event.is_directory and event.src_path.endswith('.md'):
            # 跳过 .obsidian 目录
            if '.obsidian' in event.src_path:
                return
            logger.info(f"[Watchdog] 检测到新文件: {event.src_path}")
            self._schedule_coroutine(self._handle_file_created(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if not event.is_directory and event.src_path.endswith('.md'):
            # 跳过 .obsidian 目录
            if '.obsidian' in event.src_path:
                return
            logger.info(f"[Watchdog] 检测到文件修改: {event.src_path}")
            self._schedule_coroutine(self._handle_file_modified(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件 - 直接删除记录"""
        if not event.is_directory and event.src_path.endswith('.md'):
            # 跳过 .obsidian 目录
            if '.obsidian' in event.src_path:
                return
            logger.info(f"[Watchdog] 检测到文件删除: {event.src_path}")
            self._schedule_coroutine(self._handle_file_deleted(event.src_path))
    
    def on_moved(self, event: FileSystemEvent):
        """
        文件移动事件 - 作为删除+创建处理
        注意：在某些文件系统上此事件可能不触发，依赖 on_deleted + on_created 组合
        """
        if isinstance(event, FileMovedEvent) and not event.is_directory:
            if event.src_path.endswith('.md') or event.dest_path.endswith('.md'):
                logger.info(f"检测到文件移动: {event.src_path} -> {event.dest_path}")
                # 先删除旧位置的记录
                self._schedule_coroutine(self._handle_file_deleted(event.src_path))
                # 再在新位置创建记录
                self._schedule_coroutine(self._handle_file_created(event.dest_path))
    
    async def _handle_file_created(self, file_path: str):
        """处理文件创建"""
        try:
            async with AsyncSessionLocal() as db:
                # 解析新文件（转换为 Path 对象）
                note_data = self.obsidian_service.parse_note_file(Path(file_path))
                if not note_data:
                    return
                
                # 检查是否已存在
                relative_path = str(Path(file_path).relative_to(self.vault_path))
                result = await db.execute(
                    select(Note).where(Note.file_path == relative_path)
                )
                existing_note = result.scalar_one_or_none()
                
                if existing_note:
                    logger.info(f"文件已存在于数据库: {relative_path}")
                    return
                
                # 创建新记录
                new_note = Note(
                    title=note_data.title,
                    content=note_data.content,
                    tags=note_data.tags or [],
                    file_path=relative_path,
                    file_modified_time=note_data.modified_time
                )
                db.add(new_note)
                await db.commit()
                await db.refresh(new_note)
                logger.info(f"✅ 新笔记已同步到数据库: {new_note.title}")
                
                # 嵌入向量
                try:
                    embed_note(new_note.id, new_note.title, note_data.content, new_note.tags)
                    logger.info(f"✅ 向量嵌入完成: {new_note.title}")
                except Exception as e:
                    logger.error(f"向量嵌入失败: {e}")
                
        except Exception as e:
            logger.error(f"处理文件创建失败 {file_path}: {e}")
    
    async def _handle_file_modified(self, file_path: str):
        """处理文件修改"""
        try:
            async with AsyncSessionLocal() as db:
                # 解析修改后的文件（转换为 Path 对象）
                note_data = self.obsidian_service.parse_note_file(Path(file_path))
                if not note_data:
                    return
                
                # 查找数据库记录
                relative_path = str(Path(file_path).relative_to(self.vault_path))
                result = await db.execute(
                    select(Note).where(Note.file_path == relative_path)
                )
                existing_note = result.scalar_one_or_none()
                
                if not existing_note:
                    logger.warning(f"文件不在数据库中，作为新文件处理: {relative_path}")
                    await self._handle_file_created(file_path)
                    return
                
                # 更新记录
                existing_note.title = note_data.title
                existing_note.content = note_data.content
                existing_note.tags = note_data.tags or []
                existing_note.file_modified_time = note_data.modified_time
                existing_note.updated_at = datetime.utcnow()
                
                await db.commit()
                logger.info(f"✅ 笔记已更新: {existing_note.title}")
                
                # 重新嵌入向量
                try:
                    embed_note(existing_note.id, existing_note.title, note_data.content, existing_note.tags)
                    logger.info(f"✅ 向量重新嵌入完成: {existing_note.title}")
                except Exception as e:
                    logger.error(f"向量嵌入失败: {e}")
                
        except Exception as e:
            logger.error(f"处理文件修改失败 {file_path}: {e}")
    
    async def _handle_file_deleted(self, file_path: str):
        """处理文件删除"""
        try:
            async with AsyncSessionLocal() as db:
                relative_path = str(Path(file_path).relative_to(self.vault_path))
                
                # 查找并删除记录
                result = await db.execute(
                    select(Note).where(Note.file_path == relative_path)
                )
                existing_note = result.scalar_one_or_none()
                
                if existing_note:
                    note_id = existing_note.id
                    await db.delete(existing_note)
                    await db.commit()
                    logger.info(f"✅ 笔记已从数据库删除: {relative_path}")
                    
                    # 删除向量
                    try:
                        delete_note_embedding(note_id)
                        logger.info(f"✅ 向量已删除: {note_id}")
                    except Exception as e:
                        logger.error(f"删除向量失败: {e}")
                else:
                    logger.warning(f"要删除的文件不在数据库中: {relative_path}")
                    
        except Exception as e:
            logger.error(f"处理文件删除失败 {file_path}: {e}")
    
    async def _handle_file_moved(self, src_path: str, dest_path: str):
        """处理文件移动/重命名"""
        try:
            async with AsyncSessionLocal() as db:
                old_relative_path = str(Path(src_path).relative_to(self.vault_path))
                new_relative_path = str(Path(dest_path).relative_to(self.vault_path))
                
                # 查找旧记录
                result = await db.execute(
                    select(Note).where(Note.file_path == old_relative_path)
                )
                existing_note = result.scalar_one_or_none()
                
                if not existing_note:
                    logger.warning(f"移动的源文件不在数据库中: {old_relative_path}")
                    await self._handle_file_created(dest_path)
                    return
                
                # 解析新位置的文件（标题可能也变了）（转换为 Path 对象）
                note_data = self.obsidian_service.parse_note_file(Path(dest_path))
                if note_data:
                    existing_note.file_path = new_relative_path
                    existing_note.title = note_data.title
                    existing_note.content = note_data.content
                    existing_note.tags = note_data.tags or []
                    existing_note.file_modified_time = note_data.modified_time
                    existing_note.updated_at = datetime.utcnow()
                    
                    await db.commit()
                    logger.info(f"✅ 笔记路径已更新: {old_relative_path} -> {new_relative_path}")
                    
        except Exception as e:
            logger.error(f"处理文件移动失败 {src_path} -> {dest_path}: {e}")


class FileWatcherService:
    """文件监控服务管理器"""
    
    def __init__(self, vault_path: str, obsidian_service: ObsidianService):
        self.vault_path = vault_path
        self.obsidian_service = obsidian_service
        self.observer: Optional[Observer] = None
        self.handler: Optional[MarkdownFileHandler] = None
    
    async def sync_all_notes(self):
        """
        全量同步：扫描 Obsidian vault 中所有笔记并同步到数据库
        启动时执行，确保数据库与文件系统一致
        """
        logger.info("开始全量同步笔记...")
        
        try:
            # 获取 vault 中所有笔记
            all_notes = self.obsidian_service.get_all_notes()
            logger.info(f"发现 {len(all_notes)} 个笔记文件")
            
            async with AsyncSessionLocal() as db:
                # 获取数据库中现有的所有笔记路径
                result = await db.execute(select(Note))
                existing_notes = result.scalars().all()
                existing_paths = {note.file_path: note for note in existing_notes}
                logger.info(f"数据库中现有 {len(existing_paths)} 条笔记记录")
                
                # 处理文件系统中的每个笔记
                vault_paths = set()
                created_count = 0
                updated_count = 0
                
                for note_data in all_notes:
                    vault_paths.add(note_data.file_path)
                    
                    if note_data.file_path in existing_paths:
                        # 已存在，检查是否需要更新
                        existing_note = existing_paths[note_data.file_path]
                        
                        # 比较修改时间
                        if (not existing_note.file_modified_time or 
                            note_data.modified_time > existing_note.file_modified_time):
                            existing_note.title = note_data.title
                            existing_note.content = note_data.content
                            existing_note.tags = note_data.tags or []
                            existing_note.file_modified_time = note_data.modified_time
                            existing_note.updated_at = datetime.utcnow()
                            updated_count += 1
                            
                            # 重新嵌入向量
                            try:
                                embed_note(existing_note.id, existing_note.title, 
                                          note_data.content, existing_note.tags)
                            except Exception as e:
                                logger.error(f"向量嵌入失败 {existing_note.title}: {e}")
                    else:
                        # 新笔记，添加到数据库
                        new_note = Note(
                            title=note_data.title,
                            content=note_data.content,
                            tags=note_data.tags or [],
                            file_path=note_data.file_path,
                            file_modified_time=note_data.modified_time
                        )
                        db.add(new_note)
                        await db.flush()  # 刷新以获取ID
                        created_count += 1
                        
                        # 嵌入向量
                        try:
                            embed_note(new_note.id, new_note.title, 
                                      note_data.content, new_note.tags)
                        except Exception as e:
                            logger.error(f"向量嵌入失败 {new_note.title}: {e}")
                
                # 删除数据库中已不存在于文件系统的笔记
                deleted_count = 0
                for file_path, existing_note in existing_paths.items():
                    if file_path not in vault_paths:
                        # 文件已被删除
                        try:
                            delete_note_embedding(existing_note.id)
                        except Exception as e:
                            logger.error(f"删除向量失败 {existing_note.id}: {e}")
                        
                        await db.delete(existing_note)
                        deleted_count += 1
                
                await db.commit()
                
                logger.info(f"✅ 全量同步完成：创建 {created_count}，更新 {updated_count}，删除 {deleted_count}")
                
        except Exception as e:
            logger.error(f"全量同步失败: {e}")
        
    def start(self):
        """启动文件监控"""
        if self.observer and self.observer.is_alive():
            logger.warning("文件监控已在运行中")
            return
        
        self.handler = MarkdownFileHandler(self.vault_path, self.obsidian_service)
        self.observer = Observer()
        self.observer.schedule(self.handler, self.vault_path, recursive=True)
        self.observer.start()
        logger.info(f"🔍 文件监控已启动，监控路径: {self.vault_path}")
    
    def stop(self):
        """停止文件监控"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)
            logger.info("⏹️  文件监控已停止")
    
    def is_running(self) -> bool:
        """检查监控是否运行中"""
        return self.observer is not None and self.observer.is_alive()
