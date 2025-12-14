#!/usr/bin/env python3
"""测试MCP Server的客户端"""
import asyncio
import json
import sys
from pathlib import Path
import re

# 全局事件：模型加载完成
model_loaded = asyncio.Event()

async def test_mcp_server():
    """模拟Cline启动MCP Server并通信"""
    
    # 启动MCP Server进程
    backend_dir = Path(__file__).parent
    python_path = backend_dir / ".venv/bin/python"
    server_path = backend_dir / "mcp_server.py"
    
    print(f"启动MCP Server: {python_path} {server_path}")
    process = await asyncio.create_subprocess_exec(
        str(python_path),
        str(server_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # 读取stderr日志（异步），监听模型加载完成
    async def read_stderr():
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            line_str = line.decode().strip()
            print(f"[SERVER] {line_str}", file=sys.stderr)
            
            # 检测模型加载完成
            if "模型预加载完成" in line_str or "Embedding model loaded successfully" in line_str:
                model_loaded.set()
                print("[CLIENT] 检测到模型加载完成", file=sys.stderr)
    
    stderr_task = asyncio.create_task(read_stderr())
    
    # 等待服务器启动（快速启动）
    print("等待服务器启动...")
    await asyncio.sleep(5)
    
    # 发送初始化请求
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    print("\n发送初始化请求...")
    request_line = json.dumps(init_request) + "\n"
    process.stdin.write(request_line.encode())
    await process.stdin.drain()
    
    # 读取响应
    print("等待响应...")
    try:
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
        response = json.loads(response_line.decode())
        print(f"收到响应: {json.dumps(response, indent=2)}")
    except asyncio.TimeoutError:
        print("初始化请求超时！")
        process.terminate()
        await process.wait()
        return
    
    # 发送initialized通知
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    print("\n发送initialized通知...")
    notification_line = json.dumps(initialized_notification) + "\n"
    process.stdin.write(notification_line.encode())
    await process.stdin.drain()
    await asyncio.sleep(0.5)
    
    # 列出tools
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    print("\n请求工具列表...")
    request_line = json.dumps(list_tools_request) + "\n"
    process.stdin.write(request_line.encode())
    await process.stdin.drain()
    
    try:
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
        response = json.loads(response_line.decode())
        print(f"可用工具: {json.dumps(response, indent=2, ensure_ascii=False)[:500]}")
    except asyncio.TimeoutError:
        print("工具列表请求超时！检查stderr...")
        await asyncio.sleep(1)
        process.terminate()
        await process.wait()
        return
    
    # 调用search_notes
    search_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_notes",
            "arguments": {
                "query": "C++",
                "mode": "keyword",
                "limit": 3
            }
        }
    }
    
    print("\n测试关键词搜索...")
    request_line = json.dumps(search_request) + "\n"
    process.stdin.write(request_line.encode())
    await process.stdin.drain()
    
    response_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
    response = json.loads(response_line.decode())
    print(f"关键词搜索结果: 找到 {response['result']['content'][0]['text'].count('id')} 条")
    
    # 等待模型加载完成（使用事件通知）
    print("\n等待模型加载完成...")
    try:
        await asyncio.wait_for(model_loaded.wait(), timeout=30.0)
        print("模型加载完成，开始测试语义搜索")
    except asyncio.TimeoutError:
        print("警告：模型加载超时，继续测试...")
    
    # 测试语义搜索 - 第1次
    semantic_queries = [
        ("C++面试", 3),
        ("分布式系统", 3),
        ("数据库索引", 3),
    ]
    
    for idx, (query, limit) in enumerate(semantic_queries, start=1):
        semantic_search_request = {
            "jsonrpc": "2.0",
            "id": 3 + idx,
            "method": "tools/call",
            "params": {
                "name": "search_notes",
                "arguments": {
                    "query": query,
                    "mode": "semantic",
                    "limit": limit
                }
            }
        }
        
        print(f"\n测试语义搜索 #{idx}: '{query}'")
        request_line = json.dumps(semantic_search_request) + "\n"
        process.stdin.write(request_line.encode())
        await process.stdin.drain()
        
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
        response = json.loads(response_line.decode())
        
        if "result" in response:
            text = response["result"]["content"][0]["text"]
            # 提取笔记标题
            titles = re.findall(r'"title":\s*"([^"]+)"', text)
            print(f"  找到 {len(titles)} 条: {titles[:3]}")
        else:
            print(f"  错误: {response.get('error', 'Unknown error')}")
    
    # 关闭
    process.terminate()
    await process.wait()
    stderr_task.cancel()
    print("\n测试完成")

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
