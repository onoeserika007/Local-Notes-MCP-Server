"""
Folder Structure Schemas
"""
from typing import List, Optional
from pydantic import BaseModel


class FolderItem(BaseModel):
    """文件夹或文件项"""
    name: str
    path: str
    is_folder: bool
    note_count: int  # 该项下的笔记数量


class FolderStructureResponse(BaseModel):
    """文件夹结构响应"""
    items: List[FolderItem]
