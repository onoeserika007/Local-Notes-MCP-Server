#!/usr/bin/env python3
"""重建ChromaDB向量数据库"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.note import Note, Base
from app.services.vector_service import embed_note, get_collection_stats

# 数据库配置
DATABASE_URL = f"sqlite:///{backend_dir}/notes.db"
engine = create_engine(DATABASE_URL)


async def main():
    print("开始重建向量数据库...")
    
    # 获取所有笔记
    with Session(engine) as session:
        notes = session.execute(select(Note)).scalars().all()
        total = len(notes)
        print(f"找到 {total} 条笔记")
        
        # 逐个嵌入
        for i, note in enumerate(notes, 1):
            if i % 10 == 0:
                print(f"进度: {i}/{total}")
            
            embed_note(  # 不是async函数
                note_id=note.id,
                title=note.title,
                content=note.content,
                tags=note.tags if note.tags else []
            )
    
    # 显示统计
    stats = get_collection_stats()
    print(f"\n✓ 重建完成!")
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Total: {stats['total_embeddings']} 条")
    print(f"  Model: {stats['model']}")
    print(f"  Dimension: {stats['embedding_dimension']}")


if __name__ == "__main__":
    asyncio.run(main())
