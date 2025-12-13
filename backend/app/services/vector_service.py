"""
Vector Search Service using ChromaDB and Sentence Transformers
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 全局向量模型和数据库实例
_embedding_model = None
_chroma_client = None
_collection = None

# 使用轻量级的多语言模型（支持中英文）
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # 384维，50MB
COLLECTION_NAME = "notes_embeddings"


def get_embedding_model():
    """获取或初始化 embedding 模型（单例）"""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _embedding_model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _embedding_model


def get_chroma_client():
    """获取或初始化 ChromaDB 客户端（单例）"""
    global _chroma_client
    if _chroma_client is None:
        # 存储在 backend/chroma_data 目录
        persist_directory = Path(__file__).parent.parent.parent / "chroma_data"
        persist_directory.mkdir(exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at: {persist_directory}")
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info("ChromaDB client initialized")
    return _chroma_client


def get_collection():
    """获取或创建 ChromaDB collection（单例）"""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Note embeddings for semantic search"}
        )
        logger.info(f"ChromaDB collection ready: {COLLECTION_NAME}")
    return _collection


def embed_text(text: str) -> List[float]:
    """
    将文本转换为向量
    
    Args:
        text: 输入文本
        
    Returns:
        384维向量列表
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_note(note_id: int, title: str, content: str, tags: List[str] = None):
    """
    为单个笔记生成向量并存入 ChromaDB
    
    Args:
        note_id: 笔记ID
        title: 笔记标题
        content: 笔记内容
        tags: 标签列表
    """
    collection = get_collection()
    
    # 组合标题和内容用于向量化
    combined_text = f"{title}\n\n{content or ''}"
    if tags:
        combined_text += f"\n\n标签: {', '.join(tags)}"
    
    # 生成向量
    embedding = embed_text(combined_text)
    
    # 存入 ChromaDB
    collection.upsert(
        ids=[str(note_id)],
        embeddings=[embedding],
        metadatas=[{
            "note_id": note_id,
            "title": title,
            "has_content": bool(content)
        }]
    )
    
    logger.debug(f"Embedded note {note_id}: {title}")


async def delete_note_embedding(note_id: int):
    """从 ChromaDB 删除笔记向量"""
    collection = get_collection()
    try:
        collection.delete(ids=[str(note_id)])
        logger.debug(f"Deleted embedding for note {note_id}")
    except Exception as e:
        logger.warning(f"Failed to delete embedding for note {note_id}: {e}")


def search_similar(
    query: str,
    top_k: int = 20,
    filter_metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    语义相似搜索
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        filter_metadata: 元数据过滤条件
        
    Returns:
        相似笔记列表，每项包含 note_id, distance, metadata
    """
    collection = get_collection()
    
    # 查询向量化
    query_embedding = embed_text(query)
    
    # 向量检索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=filter_metadata
    )
    
    # 格式化结果
    similar_notes = []
    if results['ids'] and results['ids'][0]:
        for i, note_id_str in enumerate(results['ids'][0]):
            similar_notes.append({
                'note_id': int(note_id_str),
                'distance': results['distances'][0][i],
                'similarity': 1 - results['distances'][0][i],  # 距离转相似度
                'metadata': results['metadatas'][0][i]
            })
    
    return similar_notes


async def update_embeddings(note_ids: List[int], notes_data: List[Dict[str, Any]]):
    """
    批量更新笔记向量
    
    Args:
        note_ids: 笔记ID列表
        notes_data: 笔记数据列表，每项包含 title, content, tags
    """
    for note_id, data in zip(note_ids, notes_data):
        await embed_note(
            note_id=note_id,
            title=data['title'],
            content=data['content'],
            tags=data.get('tags')
        )


def get_collection_stats() -> Dict[str, Any]:
    """获取向量库统计信息"""
    collection = get_collection()
    count = collection.count()
    return {
        "collection_name": COLLECTION_NAME,
        "total_embeddings": count,
        "embedding_dimension": 384,
        "model": MODEL_NAME
    }
