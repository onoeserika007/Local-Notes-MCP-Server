"""
Note Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.db.database import Base


class Note(Base):
    """Note model for storing user notes"""
    
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=True)  # 对于 Obsidian 笔记，内容在文件中
    tags = Column(JSON, default=list)  # Store tags as JSON array
    summary = Column(Text, nullable=True)  # AI-generated summary (optional)
    
    # Obsidian integration
    file_path = Column(String(512), nullable=True, unique=True, index=True)  # 相对于 vault 的路径
    file_modified_time = Column(DateTime, nullable=True)  # 文件最后修改时间
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # For future user authentication
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags or [],
            "summary": self.summary,
            "file_path": self.file_path,
            "file_modified_time": self.file_modified_time.isoformat() if self.file_modified_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
