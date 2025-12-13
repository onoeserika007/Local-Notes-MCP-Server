#!/bin/bash
# API 测试脚本

BASE_URL="http://localhost:8000"

# JSON 格式化函数（正确显示中文）
format_json() {
    python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
}

echo "================================"
echo "测试 AI Notes API"
echo "================================"
echo ""

# 测试根路径
echo "1. 测试根路径 GET /"
curl --noproxy localhost -s $BASE_URL/ | format_json
echo -e "\n"

# 测试健康检查
echo "2. 测试健康检查 GET /health"
curl -s $BASE_URL/health | python3 -m json.tool
echo -e "\n"

# 创建笔记1
echo "3. 创建笔记 #1"
NOTE1=$(curl -s -X POST "$BASE_URL/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python 学习笔记",
    "content": "# Python 基础\n\n## 数据类型\n- 字符串\n- 列表\n- 字典\n\n## 函数\n```python\ndef hello():\n    print(\"Hello World\")\n```",
    "tags": ["Python", "编程", "学习"]
  }')
echo $NOTE1 | python3 -m json.tool
NOTE1_ID=$(echo $NOTE1 | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "\n"

# 创建笔记2
echo "4. 创建笔记 #2"
NOTE2=$(curl -s -X POST "$BASE_URL/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 实战",
    "content": "# FastAPI 教程\n\n快速构建 API 的现代框架。\n\n- 自动文档生成\n- 类型检查\n- 异步支持",
    "tags": ["FastAPI", "Web开发"]
  }')
echo $NOTE2 | python3 -m json.tool
NOTE2_ID=$(echo $NOTE2 | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "\n"

# 获取笔记列表
echo "5. 获取笔记列表 GET /api/notes"
curl -s "$BASE_URL/api/notes?page=1&limit=10" | python3 -m json.tool
echo -e "\n"

# 获取单个笔记
echo "6. 获取笔记详情 GET /api/notes/$NOTE1_ID"
curl -s "$BASE_URL/api/notes/$NOTE1_ID" | python3 -m json.tool
echo -e "\n"

# 更新笔记
echo "7. 更新笔记 PUT /api/notes/$NOTE1_ID"
curl -s -X PUT "$BASE_URL/api/notes/$NOTE1_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python 进阶笔记",
    "tags": ["Python", "编程", "学习", "进阶"]
  }' | python3 -m json.tool
echo -e "\n"

# 按标签搜索
echo "8. 按标签搜索 GET /api/notes?tag=Python"
curl -s "$BASE_URL/api/notes?tag=Python" | python3 -m json.tool
echo -e "\n"

# 关键词搜索
echo "9. 关键词搜索 GET /api/notes?search=FastAPI"
curl -s "$BASE_URL/api/notes?search=FastAPI" | python3 -m json.tool
echo -e "\n"

# 删除笔记
echo "10. 删除笔记 DELETE /api/notes/$NOTE2_ID"
curl -s -X DELETE "$BASE_URL/api/notes/$NOTE2_ID" -w "\nHTTP Status: %{http_code}\n"
echo -e "\n"

# 最终列表
echo "11. 最终笔记列表"
curl -s "$BASE_URL/api/notes" | python3 -m json.tool
echo -e "\n"

echo "================================"
echo "测试完成！"
echo "================================"
