"""
AI API Routes
通义千问 AI 功能接口
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.note import Note
from app.services.qwen_service import QwenService, get_qwen_service
from app.services.vector_service import search_similar
from app.schemas.ai import (
    ChatRequest, 
    ChatResponse, 
    SummarizeResponse,
    AutoTagResponse
)
from app.schemas.note import NoteResponse

router = APIRouter(prefix="/ai", tags=["AI"])
logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat_with_notes(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    qwen: QwenService = Depends(get_qwen_service)
):
    """
    基于笔记的 AI 对话（RAG核心功能）
    
    工作流程：
    1. 如果指定了note_ids，直接使用这些笔记作为上下文
    2. 否则，使用语义搜索检索相关笔记
    3. 构建上下文并调用LLM生成回答
    
    - **query**: 用户问题
    - **note_ids**: 相关笔记 ID 列表（可选）
    - **top_k**: 语义搜索检索笔记数量（默认5）
    - **stream**: 是否流式输出（默认false）
    - **system_prompt**: 自定义系统提示词（可选）
    """
    try:
        logger.info(f"Chat request: query='{request.query}', note_ids={request.note_ids}, stream={getattr(request, 'stream', False)}")
        
        context_notes = []
        referenced_notes = []
        
        # 获取上下文笔记
        if request.note_ids:
            # 使用指定的笔记
            result = await db.execute(
                select(Note).where(Note.id.in_(request.note_ids))
            )
            notes = result.scalars().all()
            
            context_notes = [note.content for note in notes if note.content]
            referenced_notes = [
                {
                    "id": note.id,
                    "title": note.title,
                    "preview": (note.content or "")[:200]
                }
                for note in notes
            ]
        else:
            # 使用语义搜索相关笔记
            top_k = getattr(request, 'top_k', 5)
            similar_notes = search_similar(
                query=request.query,
                top_k=top_k
            )
            
            if similar_notes:
                # similar_notes是字典列表，每项包含note_id, similarity等
                note_ids = [item['note_id'] for item in similar_notes]
                result = await db.execute(
                    select(Note).where(Note.id.in_(note_ids))
                )
                notes = result.scalars().all()
                
                # 按相似度排序
                notes_dict = {note.id: note for note in notes}
                for item in similar_notes:
                    note_id = item['note_id']
                    if note_id in notes_dict:
                        note = notes_dict[note_id]
                        context_notes.append(note.content or "")
                        referenced_notes.append({
                            "id": note.id,
                            "title": note.title,
                            "preview": (note.content or "")[:200],
                            "similarity": round(item['similarity'], 3)
                        })
        
        logger.info(f"Found {len(context_notes)} context notes")
        
        # 检查是否支持流式输出
        stream = getattr(request, 'stream', False)
        
        if stream:
            # 流式响应（SSE）
            async def generate():
                try:
                    for chunk in qwen.chat_with_context(
                        query=request.query,
                        context_notes=context_notes,
                        system_prompt=request.system_prompt,
                        stream=True
                    ):
                        # SSE格式：data: <content>\n\n
                        yield f"data: {chunk}\n\n"
                    
                    # 发送完成信号
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Stream generation error: {str(e)}")
                    yield f"data: [ERROR] {str(e)}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # 非流式响应
            reply = qwen.chat_with_context(
                query=request.query,
                context_notes=context_notes,
                system_prompt=request.system_prompt,
                stream=False
            )
            
            return ChatResponse(
                reply=reply,
                referenced_notes=referenced_notes
            )
        
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/summarize/{note_id}", response_model=NoteResponse)
async def summarize_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    qwen: QwenService = Depends(get_qwen_service)
):
    """
    生成笔记摘要
    
    - **note_id**: 笔记 ID
    """
    try:
        # 获取笔记
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # 生成摘要
        summary = qwen.summarize(note.content, max_length=200)
        
        # 保存摘要到数据库
        note.summary = summary
        await db.commit()
        await db.refresh(note)
        
        logger.info(f"Summary generated for note {note_id}")
        
        return note
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarize API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/auto-tag/{note_id}", response_model=NoteResponse)
async def auto_tag_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    qwen: QwenService = Depends(get_qwen_service)
):
    """
    AI 自动打标签
    
    - **note_id**: 笔记 ID
    """
    try:
        # 获取笔记
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # 生成标签
        tags = qwen.auto_tag(note.content, max_tags=5)
        
        # 合并现有标签（去重）
        existing_tags = set(note.tags or [])
        new_tags = list(existing_tags | set(tags))
        
        note.tags = new_tags
        await db.commit()
        await db.refresh(note)
        
        logger.info(f"Auto tags generated for note {note_id}: {tags}")
        
        return note
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto tag API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.get("/health")
async def ai_health_check(qwen: QwenService = Depends(get_qwen_service)):
    """
    AI 服务健康检查
    """
    try:
        # 简单的测试调用
        test_messages = [{"role": "user", "content": "hi"}]
        response = qwen.chat(test_messages, max_tokens=10)
        
        return {
            "status": "healthy",
            "model": qwen.model,
            "api_configured": bool(qwen.api_key)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
