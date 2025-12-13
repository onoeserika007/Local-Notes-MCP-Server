"""
Initialize vector embeddings for existing notes
"""
import asyncio
from sqlalchemy import select
from app.db.database import engine, AsyncSessionLocal
from app.models.note import Note
from app.services.vector_service import embed_note, get_collection_stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_vectors():
    """为所有现有笔记生成向量"""
    async with AsyncSessionLocal() as db:
        # 获取所有笔记
        result = await db.execute(select(Note))
        notes = result.scalars().all()
        
        total = len(notes)
        logger.info(f"Found {total} notes to embed")
        
        # 批量向量化
        for i, note in enumerate(notes, 1):
            try:
                # 确保 tags 是列表类型
                tags = note.tags if isinstance(note.tags, list) else []
                
                await embed_note(
                    note_id=note.id,
                    title=note.title,
                    content=note.content,
                    tags=tags
                )
                
                if i % 10 == 0 or i == total:
                    logger.info(f"Progress: {i}/{total} ({i*100//total}%)")
                    
            except Exception as e:
                import traceback
                logger.error(f"Failed to embed note {note.id}: {e}")
                logger.error(traceback.format_exc())
        
        # 显示统计
        stats = get_collection_stats()
        logger.info(f"✅ Vector initialization complete: {stats}")


if __name__ == "__main__":
    asyncio.run(init_vectors())
