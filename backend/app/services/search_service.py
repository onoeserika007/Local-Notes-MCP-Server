"""
Full-Text Search Service using SQLite FTS5
"""
import re
import jieba
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.models.note import Note


def tokenize_text(text: str) -> str:
    """
    使用 jieba 对文本进行中文分词
    返回空格分隔的分词结果
    """
    if not text:
        return ''
    # 使用搜索引擎模式，会对长词再次切分
    words = jieba.cut_for_search(text)
    return ' '.join(words)


def sanitize_fts_query(query: str) -> str:
    """
    清理查询字符串，移除或转义 FTS5 特殊字符
    
    FTS5 特殊字符和语法：
    - 引号: " ' (用于短语搜索)
    - 括号: ( ) (用于分组)
    - 运算符: * (通配符), + - (NEAR操作符)
    - 列过滤: : (如 title:python)
    - 列前缀: ^ (如 ^title)
    - 标点: . ! ? : ; , 等
    
    策略：保留以下字符
    - 中文字符 (U+4E00 到 U+9FFF)
    - 英文字母和数字 (a-zA-Z0-9)
    - 空格（用于分词）
    - 日韩文等其他Unicode字符 (可选)
    """
    if not query or not query.strip():
        return ''
    
    # 移除或替换 FTS5 特殊字符
    # 保留：中文、英文字母、数字、空格、日文假名、韩文
    # \u3040-\u309F: 平假名
    # \u30A0-\u30FF: 片假名
    # \uAC00-\uD7AF: 韩文
    sanitized = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]', ' ', query)
    
    # 移除下划线（\w包含下划线，但在某些情况下可能有问题）
    sanitized = sanitized.replace('_', ' ')
    
    # 去除多余空格
    sanitized = ' '.join(sanitized.split())
    
    return sanitized
async def sync_note_to_fts(db: AsyncSession, note: Note):
    """同步单个笔记到 FTS 表，存储分词后的内容"""
    # 对 title 和 content 进行分词
    title_tokenized = tokenize_text(note.title)
    content_tokenized = tokenize_text(note.content or '')
    tags_str = ' '.join(note.tags) if note.tags else ''
    
    await db.execute(
        text("""
            INSERT OR REPLACE INTO notes_fts(note_id, title, content, tags)
            VALUES (:note_id, :title, :content, :tags)
        """),
        {
            "note_id": note.id,
            "title": title_tokenized,
            "content": content_tokenized,
            "tags": tags_str
        }
    )


async def delete_note_from_fts(db: AsyncSession, note_id: int):
    """从 FTS 表删除笔记"""
    await db.execute(
        text("DELETE FROM notes_fts WHERE note_id = :note_id"),
        {"note_id": note_id}
    )


async def search_notes_fts(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    offset: int = 0
):
    """
    使用 FTS5 搜索笔记
    
    支持的查询语法：
    - "python" - 包含 python
    - "python OR java" - 包含 python 或 java
    - "python AND java" - 同时包含
    - "python NOT java" - 包含 python 但不包含 java
    - "machine learning" - 短语搜索
    """
    # 清理查询字符串
    cleaned_query = sanitize_fts_query(query)
    if not cleaned_query:
        return []
    
    # 对查询词进行分词处理
    # 如果查询包含布尔操作符，保留原样；否则进行分词
    if any(op in cleaned_query.upper() for op in [' OR ', ' AND ', ' NOT ']):
        # 包含布尔操作符，不分词
        tokenized_query = cleaned_query
    else:
        # 简单查询，进行分词并用 OR 连接
        words = jieba.cut_for_search(cleaned_query)
        safe_words = [w.strip() for w in words if w.strip()]
        if not safe_words:
            return []
        tokenized_query = ' OR '.join(safe_words)
    
    # 搜索并返回结果（按相关性排序）
    result = await db.execute(
        text("""
            SELECT 
                n.*,
                bm25(notes_fts) as rank
            FROM notes_fts
            JOIN notes n ON notes_fts.note_id = n.id
            WHERE notes_fts MATCH :query
            ORDER BY rank
            LIMIT :limit OFFSET :offset
        """),
        {"query": tokenized_query, "limit": limit, "offset": offset}
    )
    
    return result.fetchall()


async def get_search_count(db: AsyncSession, query: str) -> int:
    """获取搜索结果总数"""
    # 清理查询字符串
    cleaned_query = sanitize_fts_query(query)
    if not cleaned_query:
        return 0
    
    # 对查询词进行分词处理（与 search_notes_fts 保持一致）
    if any(op in cleaned_query.upper() for op in [' OR ', ' AND ', ' NOT ']):
        tokenized_query = cleaned_query
    else:
        words = jieba.cut_for_search(cleaned_query)
        safe_words = [w.strip() for w in words if w.strip()]
        if not safe_words:
            return 0
        tokenized_query = ' OR '.join(safe_words)
    
    result = await db.execute(
        text("""
            SELECT COUNT(*) as count
            FROM notes_fts
            WHERE notes_fts MATCH :query
        """),
        {"query": tokenized_query}
    )
    row = result.fetchone()
    return row[0] if row else 0


async def rebuild_fts_index(db: AsyncSession):
    """重建整个 FTS 索引"""
    # 清空 FTS 表
    await db.execute(text("DELETE FROM notes_fts"))
    
    # 重新插入所有笔记
    await db.execute(text("""
        INSERT INTO notes_fts(note_id, title, content, tags)
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
    
    # 优化索引
    await db.execute(text("INSERT INTO notes_fts(notes_fts) VALUES('optimize')"))
