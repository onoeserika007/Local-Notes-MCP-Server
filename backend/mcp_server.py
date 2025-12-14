#!/home/inory/agent_ws/backend/.venv/bin/python
"""
MCP Server for Notes Application
提供笔记操作的MCP接口，供Cline等MCP客户端调用
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 切换到backend目录（确保数据库路径正确）
os.chdir(backend_dir)

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.note import Note
from app.db.database import Base
from app.services.vector_service import search_similar

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置（使用相对路径）
db_path = os.path.join(backend_dir, "notes.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
logger.info(f"Database path: {db_path}")
logger.info(f"Database exists: {os.path.exists(db_path)}")
logger.info(f"Database URL: {DATABASE_URL}")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 创建MCP Server
app = Server("notes-rag")

# ============ Helper Functions ============

async def get_db():
    """获取数据库会话"""
    async with async_session_maker() as session:
        yield session

async def get_note_by_id(note_id: int) -> Optional[Note]:
    """根据ID获取笔记"""
    async with async_session_maker() as db:
        result = await db.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

async def search_notes_db(query: str, limit: int = 20) -> List[Note]:
    """全文搜索笔记"""
    async with async_session_maker() as db:
        # 简单的LIKE搜索
        result = await db.execute(
            select(Note).where(
                (Note.title.like(f"%{query}%")) | (Note.content.like(f"%{query}%"))
            ).limit(limit)
        )
        return result.scalars().all()

async def get_all_notes() -> List[Note]:
    """获取所有笔记"""
    async with async_session_maker() as db:
        result = await db.execute(select(Note))
        notes = result.scalars().all()
        logger.info(f"get_all_notes: 找到 {len(notes)} 条笔记")
        return notes

# ============ MCP Resources ============

@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出所有可用的资源"""
    notes = await get_all_notes()
    
    resources = []
    
    # 添加笔记库统计资源
    resources.append(Resource(
        uri="notes://stats",
        name="笔记库统计",
        mimeType="application/json",
        description="笔记库的统计信息（总数、标签等）"
    ))
    
    # 添加每条笔记作为资源
    for note in notes:
        resources.append(Resource(
            uri=f"notes://{note.id}",
            name=note.title,
            mimeType="text/markdown",
            description=f"笔记: {note.title} | 标签: {', '.join(note.tags or [])}"
        ))
    
    return resources

@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取指定资源的内容"""
    if uri == "notes://stats":
        # 返回统计信息
        notes = await get_all_notes()
        all_tags = set(tag for note in notes for tag in (note.tags or []))
        
        stats = {
            "total_notes": len(notes),
            "total_tags": len(all_tags),
            "tags": list(all_tags)[:20]
        }
        
        import json
        return json.dumps(stats, ensure_ascii=False, indent=2)
    
    elif uri.startswith("notes://"):
        # 提取笔记ID
        try:
            note_id = int(uri.split("//")[1])
            note = await get_note_by_id(note_id)
            
            if note:
                content = f"# {note.title}\n\n"
                if note.tags:
                    content += f"**标签**: {', '.join(note.tags)}\n\n"
                if note.summary:
                    content += f"**摘要**: {note.summary}\n\n"
                content += f"{note.content or '（无内容）'}"
                return content
            else:
                return f"笔记 ID {note_id} 不存在"
        except ValueError:
            return f"无效的笔记URI: {uri}"
    
    return f"未知资源: {uri}"

# ============ MCP Tools ============

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="search_notes",
            description="搜索笔记（支持关键词搜索和语义搜索）",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["keyword", "semantic"],
                        "description": "搜索模式：keyword（关键词）或 semantic（语义）",
                        "default": "keyword"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_note",
            description="获取指定ID的笔记详细内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "笔记ID"
                    }
                },
                "required": ["note_id"]
            }
        ),
        Tool(
            name="list_notes",
            description="列出所有笔记的标题和ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "按标签筛选（可选）"
                    }
                }
            }
        ),
        Tool(
            name="get_notes_by_tag",
            description="获取指定标签的所有笔记",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "标签名称"
                    }
                },
                "required": ["tag"]
            }
        ),
        Tool(
            name="list_all_tags",
            description="列出所有可用的标签",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具调用"""
    
    if name == "search_notes":
        query = arguments["query"]
        mode = arguments.get("mode", "keyword")
        limit = arguments.get("limit", 10)
        
        if mode == "semantic":
            # 语义搜索
            try:
                similar_notes = search_similar(query, top_k=limit)
                if similar_notes:
                    note_ids = [item['note_id'] for item in similar_notes]
                    async with async_session_maker() as db:
                        result = await db.execute(
                            select(Note).where(Note.id.in_(note_ids))
                        )
                        notes = result.scalars().all()
                        
                        # 按相似度排序
                        notes_dict = {note.id: note for note in notes}
                        results = []
                        for item in similar_notes:
                            if item['note_id'] in notes_dict:
                                note = notes_dict[item['note_id']]
                                results.append({
                                    "id": note.id,
                                    "title": note.title,
                                    "tags": note.tags or [],
                                    "summary": note.summary or (note.content or "")[:150],
                                    "similarity": round(item['similarity'], 3)
                                })
                else:
                    results = []
            except Exception as e:
                logger.error(f"语义搜索失败: {str(e)}")
                results = []
        else:
            # 关键词搜索
            notes = await search_notes_db(query, limit)
            results = [
                {
                    "id": note.id,
                    "title": note.title,
                    "tags": note.tags or [],
                    "summary": note.summary or (note.content or "")[:150]
                }
                for note in notes
            ]
        
        import json
        return [TextContent(
            type="text",
            text=f"找到 {len(results)} 条相关笔记:\n\n" + 
                 json.dumps(results, ensure_ascii=False, indent=2)
        )]
    
    elif name == "get_note":
        note_id = arguments["note_id"]
        note = await get_note_by_id(note_id)
        
        if note:
            content = f"# {note.title}\n\n"
            if note.tags:
                content += f"**标签**: {', '.join(note.tags)}\n\n"
            if note.summary:
                content += f"**摘要**: {note.summary}\n\n"
            content += f"---\n\n{note.content or '（无内容）'}"
            
            return [TextContent(type="text", text=content)]
        else:
            return [TextContent(type="text", text=f"找不到ID为 {note_id} 的笔记")]
    
    elif name == "list_notes":
        tag = arguments.get("tag")
        logger.info(f"list_notes called with tag={tag}")
        notes = await get_all_notes()
        logger.info(f"Retrieved {len(notes)} total notes")
        
        if tag:
            notes = [n for n in notes if tag in (n.tags or [])]
            logger.info(f"Filtered to {len(notes)} notes with tag '{tag}'")
        
        results = [
            {"id": note.id, "title": note.title, "tags": note.tags or []}
            for note in notes
        ]
        
        import json
        response_text = f"共 {len(results)} 条笔记:\n\n" + json.dumps(results, ensure_ascii=False, indent=2)
        logger.info(f"Returning response with {len(results)} notes")
        return [TextContent(
            type="text",
            text=response_text
        )]
    
    elif name == "get_notes_by_tag":
        tag = arguments["tag"]
        notes = await get_all_notes()
        filtered = [n for n in notes if tag in (n.tags or [])]
        
        results = [
            {
                "id": note.id,
                "title": note.title,
                "summary": note.summary or (note.content or "")[:150]
            }
            for note in filtered
        ]
        
        import json
        return [TextContent(
            type="text",
            text=f"标签 '{tag}' 下有 {len(results)} 条笔记:\n\n" + 
                 json.dumps(results, ensure_ascii=False, indent=2)
        )]
    
    elif name == "list_all_tags":
        notes = await get_all_notes()
        all_tags = set(tag for note in notes for tag in (note.tags or []))
        
        import json
        return [TextContent(
            type="text",
            text=f"共 {len(all_tags)} 个标签:\n\n" + 
                 json.dumps(sorted(all_tags), ensure_ascii=False, indent=2)
        )]
    
    return [TextContent(type="text", text=f"未知工具: {name}")]

# ============ 启动服务器 ============

async def main():
    """主函数"""
    from mcp.server.stdio import stdio_server
    
    logger.info("========================================")
    logger.info("启动 Notes MCP Server...")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"数据库: {DATABASE_URL}")
    logger.info("========================================")
    
    # 测试数据库连接
    try:
        test_notes = await get_all_notes()
        logger.info(f"启动时数据库检查: {len(test_notes)} 条笔记")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
    
    # 运行MCP服务器（使用stdio通信）
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
