"""
Semantic Search API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.db.database import get_db
from app.models.note import Note
from app.schemas.note import NoteResponse, NotesResponse
from app.services.vector_service import search_similar

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/semantic", response_model=NotesResponse)
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search using vector embeddings
    
    - Converts query to vector
    - Finds similar notes by cosine similarity
    - Returns paginated results
    """
    try:
        # 向量相似度搜索
        similar_results = search_similar(q, top_k=limit * 2)  # 获取更多候选
        
        if not similar_results:
            return NotesResponse(
                notes=[],
                total=0,
                page=page,
                limit=limit
            )
        
        # 提取 note_ids 和相似度分数
        note_ids = [int(r["note_id"]) for r in similar_results]
        scores = {int(r["note_id"]): r["distance"] for r in similar_results}
        
        # 从数据库获取笔记详情
        result = await db.execute(
            select(Note).where(Note.id.in_(note_ids))
        )
        notes = result.scalars().all()
        
        # 按相似度排序（distance 越小越相似）
        notes_sorted = sorted(
            notes,
            key=lambda n: scores.get(n.id, 999)
        )
        
        # 分页
        total = len(notes_sorted)
        start = (page - 1) * limit
        end = start + limit
        paginated_notes = notes_sorted[start:end]
        
        return NotesResponse(
            notes=[NoteResponse.model_validate(note) for note in paginated_notes],
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid", response_model=NotesResponse)
async def hybrid_search(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Hybrid search combining keyword (FTS5) and semantic search
    
    - Uses both BM25 scoring and vector similarity
    - Merges and reranks results
    - Provides best of both worlds
    """
    from app.services.search_service import search_notes_fts
    
    try:
        # 1. 关键词搜索 (FTS5)
        keyword_notes = await search_notes_fts(db, q, limit=limit, offset=0)
        keyword_ids = {note.id: idx for idx, note in enumerate(keyword_notes)}
        
        # 2. 语义搜索 (Vector)
        similar_results = search_similar(q, top_k=limit)
        semantic_ids = {
            int(r["note_id"]): (idx, r["distance"]) 
            for idx, r in enumerate(similar_results)
        }
        
        # 3. 合并去重
        all_ids = set(keyword_ids.keys()) | set(semantic_ids.keys())
        
        if not all_ids:
            return NotesResponse(notes=[], total=0, page=page, limit=limit)
        
        # 4. 获取所有笔记
        result = await db.execute(
            select(Note).where(Note.id.in_(all_ids))
        )
        notes = result.scalars().all()
        
        # 5. 混合评分：关键词排名 + 语义相似度
        def hybrid_score(note):
            kw_rank = keyword_ids.get(note.id, 9999)  # 关键词排名（越小越好）
            sem_rank, sem_dist = semantic_ids.get(note.id, (9999, 999))  # 语义排名和距离
            
            # 综合分数（可调整权重）
            # 关键词匹配给予更高权重（50%），语义相似度占50%
            kw_score = 1.0 / (1 + kw_rank)  # 归一化
            sem_score = 1.0 / (1 + sem_dist) if sem_dist < 2 else 0  # 距离太大则忽略
            
            return 0.6 * kw_score + 0.4 * sem_score
        
        # 6. 按综合分数排序
        notes_sorted = sorted(notes, key=hybrid_score, reverse=True)
        
        # 7. 分页
        total = len(notes_sorted)
        start = (page - 1) * limit
        end = start + limit
        paginated_notes = notes_sorted[start:end]
        
        return NotesResponse(
            notes=[NoteResponse.model_validate(note) for note in paginated_notes],
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
