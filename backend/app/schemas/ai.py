"""
Pydantic Schemas for AI API
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., min_length=1, description="用户问题")
    note_ids: Optional[List[int]] = Field(default=None, description="相关笔记 ID 列表（可选）")
    top_k: int = Field(default=5, ge=1, le=20, description="语义搜索检索笔记数量")
    stream: bool = Field(default=False, description="是否流式输出")
    system_prompt: Optional[str] = Field(default=None, description="自定义系统提示词（可选）")


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str = Field(..., description="AI 回复")
    referenced_notes: List[dict] = Field(default=[], description="引用的笔记列表")


class SummarizeResponse(BaseModel):
    """摘要响应"""
    note_id: int
    summary: str


class AutoTagResponse(BaseModel):
    """自动标签响应"""
    note_id: int
    tags: List[str]
