"""
Initialize FTS5 full-text search table
"""
import asyncio
from sqlalchemy import text, select
from app.db.database import engine, AsyncSessionLocal
from app.models.note import Note
from app.services.search_service import sync_note_to_fts


async def init_fts5():
    """创建 FTS5 虚拟表并同步数据"""
    async with engine.begin() as conn:
        # 创建 FTS5 虚拟表
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                note_id UNINDEXED,
                title,
                content,
                tags,
                tokenize='unicode61 remove_diacritics 2'
            )
        """))
        
        # 同步现有数据到 FTS 表
        await conn.execute(text("""
            INSERT OR REPLACE INTO notes_fts(note_id, title, content, tags)
            SELECT 
                id,
                title,
                COALESCE(content, ''),
                COALESCE(
                    (SELECT GROUP_CONCAT(value, ' ') 
                     FROM json_each(notes.tags)),
                    ''
                )
            FROM notes
        """))
        
        print("✅ FTS5 table initialized and data synced")


async def rebuild_fts_index():
    """重建 FTS 索引，使用 jieba 分词重新同步所有笔记"""
    async with engine.begin() as conn:
        # 清空 FTS 表
        await conn.execute(text("DELETE FROM notes_fts"))
        print("✅ Cleared FTS table")
    
    # 重新同步所有笔记
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Note))
        notes = result.scalars().all()
        
        count = 0
        for note in notes:
            await sync_note_to_fts(db, note)
            count += 1
        
        await db.commit()
        print(f"✅ FTS5 index rebuilt with jieba tokenization: {count} notes synced")


if __name__ == "__main__":
    asyncio.run(init_fts5())
