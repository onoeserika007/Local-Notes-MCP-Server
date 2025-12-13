#!/bin/bash
# AI 功能测试脚本

BASE_URL="http://localhost:8000"

# JSON 格式化函数（正确显示中文）
format_json() {
    python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
}

echo "================================"
echo "测试 AI 功能"
echo "================================"
echo ""

# 1. 测试 AI 健康检查
echo "1. AI 健康检查 GET /api/ai/health"
curl --noproxy localhost -s "$BASE_URL/api/ai/health" | format_json
echo -e "\n"

# 2. 创建测试笔记
echo "2. 创建测试笔记"
NOTE_RESPONSE=$(curl --noproxy localhost -s -X POST "$BASE_URL/api/notes/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python 异步编程",
    "content": "# Python 异步编程指南\n\n## asyncio 基础\nasyncio 是 Python 的异步 I/O 库。\n\n### 核心概念\n- **协程 (Coroutine)**: 使用 async def 定义\n- **事件循环 (Event Loop)**: 管理协程的执行\n- **任务 (Task)**: 包装协程以便并发执行\n\n### 示例代码\n```python\nimport asyncio\n\nasync def main():\n    print(\"Hello\")\n    await asyncio.sleep(1)\n    print(\"World\")\n\nasyncio.run(main())\n```\n\n## 实际应用\n- 网络请求\n- 数据库操作\n- 文件 I/O",
    "tags": ["Python", "异步编程"]
  }')

NOTE_ID=$(echo $NOTE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "创建的笔记 ID: $NOTE_ID"
echo "$NOTE_RESPONSE" | format_json
echo -e "\n"

# 3. 生成摘要
echo "3. 生成笔记摘要 POST /api/ai/summarize/$NOTE_ID"
curl --noproxy localhost -s -X POST "$BASE_URL/api/ai/summarize/$NOTE_ID" | format_json
echo -e "\n"

# 4. 自动生成标签
echo "4. AI 自动打标签 POST /api/ai/auto-tag/$NOTE_ID"
curl --noproxy localhost -s -X POST "$BASE_URL/api/ai/auto-tag/$NOTE_ID" | format_json
echo -e "\n"

# 5. 查看更新后的笔记
echo "5. 查看更新后的笔记 GET /api/notes/$NOTE_ID"
curl --noproxy localhost -s "$BASE_URL/api/notes/$NOTE_ID" | format_json
echo -e "\n"

# 6. AI 对话 - 一般问题
echo "6. AI 对话 - 一般问题"
curl --noproxy localhost -s -X POST "$BASE_URL/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"我的笔记里有哪些编程相关的内容？"}' | format_json
echo -e "\n"

# 7. AI 对话 - 基于特定笔记
echo "7. AI 对话 - 基于特定笔记"
curl --noproxy localhost -s -X POST "$BASE_URL/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Python 异步编程的核心概念是什么？\",\"note_ids\":[$NOTE_ID]}" | format_json
echo -e "\n"

# 8. AI 对话 - 深入问题
echo "8. AI 对话 - 深入问题"
curl --noproxy localhost -s -X POST "$BASE_URL/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"解释一下协程和任务的区别\",\"note_ids\":[$NOTE_ID]}" | format_json
echo -e "\n"

# 9. 获取所有笔记列表
echo "9. 获取所有笔记列表"
curl --noproxy localhost -s "$BASE_URL/api/notes/" | format_json
echo -e "\n"

echo "================================"
echo "AI 功能测试完成！"
echo "================================"
echo ""
echo "访问 API 文档查看更多端点："
echo "  Swagger UI: http://localhost:8000/docs"
echo "  ReDoc: http://localhost:8000/redoc"
