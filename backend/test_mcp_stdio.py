#!/home/inory/agent_ws/backend/.venv/bin/python
"""测试stdio环境下模型加载"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.vector_service import get_embedding_model

async def main():
    print("TEST: 开始加载模型...", file=sys.stderr)
    
    loop = asyncio.get_event_loop()
    model = await loop.run_in_executor(None, get_embedding_model)
    
    print("TEST: 模型加载成功", file=sys.stderr)
    
    # 模拟stdio通信
    print('{"jsonrpc": "2.0", "id": 1, "result": "ok"}')
    sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
