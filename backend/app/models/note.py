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
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)  # Store tags as JSON array
    summary = Column(Text, nullable=True)  # AI-generated summary (optional)
    
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
