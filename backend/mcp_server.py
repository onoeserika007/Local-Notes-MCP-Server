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
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.note import Note
from app.db.database import Base

# 配置日志 - 同时输出到stderr和文件
log_file = os.path.join(backend_dir, "mcp_server.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_file, mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日志文件: {log_file}")

# 数据库配置（使用相对路径）
db_path = os.path.join(backend_dir, "notes.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
logger.info(f"Database path: {db_path}")
logger.info(f"Database exists: {os.path.exists(db_path)}")
logger.info(f"Database URL: {DATABASE_URL}")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 导入向量服务（用于预加载模型）
from app.services.vector_service import get_embedding_model, search_similar

# 创建全局MCP Server
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

async def search_notes_semantic(query: str, limit: int = 20) -> List[Dict]:
    """语义搜索笔记（异步包装）"""
    import asyncio
    # 在线程池中运行同步的向量搜索，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, search_similar, query, limit)
    return results

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
    logger.info("收到list_tools请求")
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
                        "description": "返回结果数量（推荐20-50）",
                        "default": 30
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
        limit = arguments.get("limit", 30)
        
        logger.info(f"=== search_notes 调用 ===")
        logger.info(f"  query: {query}")
        logger.info(f"  mode: {mode}")
        logger.info(f"  limit: {limit}")
        logger.info(f"  原始arguments: {arguments}")
        
        if mode == "semantic":
            # 语义搜索
            try:
                logger.info(f"开始语义搜索: query='{query}', limit={limit}")
                similar_notes = await search_notes_semantic(query, limit)
                logger.info(f"语义搜索完成，找到 {len(similar_notes)} 条结果")
                
                if similar_notes:
                    note_ids = [item['note_id'] for item in similar_notes]
                    logger.info(f"准备查询数据库，note_ids={note_ids[:5]}...")
                    async with async_session_maker() as db:
                        result = await db.execute(
                            select(Note).where(Note.id.in_(note_ids))
                        )
                        notes = result.scalars().all()
                        logger.info(f"数据库查询完成，找到 {len(notes)} 条笔记")
                        
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
                logger.error(f"语义搜索失败: {str(e)}", exc_info=True)
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
    import argparse
    
    parser = argparse.ArgumentParser(description="Notes MCP Server")
    parser.add_argument("--mode", choices=["stdio", "http"], default="http", 
                       help="通信模式: stdio (标准输入输出) 或 http (HTTP服务器)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP模式的监听地址")
    parser.add_argument("--port", type=int, default=8001, help="HTTP模式的端口")
    args = parser.parse_args()
    
    logger.info("========================================")
    logger.info(f"启动 Notes MCP Server (模式: {args.mode})...")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"数据库: {DATABASE_URL}")
    logger.info("========================================")
    
    # 测试数据库连接
    try:
        test_notes = await get_all_notes()
        logger.info(f"启动时数据库检查: {len(test_notes)} 条笔记")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
    
    # 在后台线程预加载模型（不阻塞服务器启动）
    def preload_model():
        try:
            logger.info("后台预加载embedding模型...")
            model = get_embedding_model()
            logger.info("模型预加载完成")
        except Exception as e:
            logger.warning(f"模型预加载失败: {e}")
    
    import threading
    threading.Thread(target=preload_model, daemon=True).start()
    logger.info("MCP Server就绪，模型正在后台加载...")
    
    if args.mode == "stdio":
        # 使用stdio通信（供Cline调用）
        from mcp.server.stdio import stdio_server
        logger.info("使用 stdio 模式")
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    else:
        # 使用HTTP通信（方便调试）
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import Response
        from starlette.requests import Request
        import uvicorn
        
        logger.info(f"使用 HTTP 模式，监听 {args.host}:{args.port}")
        
        sse_transport = SseServerTransport("/messages")
        
        async def handle_sse(request: Request):
            """处理SSE连接"""
            logger.info(f"收到SSE连接: {request.url}")
            
            async with sse_transport.connect_sse(
                request.scope,
                request.receive,
                request._send
            ) as (read_stream, write_stream):
                logger.info("SSE连接已建立，开始MCP会话")
                try:
                    await app.run(
                        read_stream,
                        write_stream,
                        app.create_initialization_options()
                    )
                    logger.info("MCP会话正常结束")
                except Exception as e:
                    logger.error(f"MCP会话异常: {e}", exc_info=True)
        
        async def handle_post_message_asgi(scope, receive, send):
            """处理POST消息 - 原始ASGI接口"""
            query_string = scope.get('query_string', b'').decode()
            logger.info(f"收到POST消息: {scope['path']} (query: {query_string})")
            await sse_transport.handle_post_message(scope, receive, send)
        
        # 包装成可调用的ASGI app
        class ASGIApp:
            def __init__(self, handler):
                self.handler = handler
            async def __call__(self, scope, receive, send):
                await self.handler(scope, receive, send)
        
        from starlette.routing import Mount
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("", app=ASGIApp(handle_post_message_asgi)),  # 匹配所有路径
            ]
        )
        
        logger.info(f"MCP Server HTTP 端点: http://{args.host}:{args.port}/sse")
        config = uvicorn.Config(
            starlette_app, 
            host=args.host, 
            port=args.port, 
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
