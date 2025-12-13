# AI Notes - 智能笔记应用

> 基于通义千问 API 的智能笔记管理系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 项目简介

一个功能强大的 AI 增强笔记应用，结合通义千问大模型，提供智能摘要、语义搜索、智能问答等功能。

### 核心特性

- 📝 **笔记管理** - 支持 Markdown 格式的笔记创建、编辑、删除
- 🔍 **智能搜索** - 全文搜索 + 语义搜索
- 🤖 **AI 增强** - 自动摘要、智能问答、标签推荐
- 🏷️ **标签系统** - 灵活的标签分类和过滤
- 🎨 **现代 UI** - 响应式设计，支持明暗主题

## 🏗 技术架构

### 后端
- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy
- **LLM**: 通义千问 (dashscope)
- **向量库**: ChromaDB (计划)
- **语言**: Python 3.11+

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **UI 库**: Ant Design / shadcn/ui
- **状态管理**: Zustand + React Query

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- 通义千问 API Key（Week 2 开始需要）

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
python -m app.main
```

访问 http://localhost:8000/docs 查看 API 文档

### 前端启动（Week 3 开始）

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## 📚 API 文档

### 笔记 API

#### 创建笔记
```http
POST /api/notes
Content-Type: application/json

{
  "title": "笔记标题",
  "content": "# Markdown 内容",
  "tags": ["标签1", "标签2"]
}
```

#### 获取笔记列表
```http
GET /api/notes?page=1&limit=10&tag=标签&search=关键词
```

#### 获取单个笔记
```http
GET /api/notes/{id}
```

#### 更新笔记
```http
PUT /api/notes/{id}
Content-Type: application/json

{
  "title": "新标题",
  "content": "新内容"
}
```

#### 删除笔记
```http
DELETE /api/notes/{id}
```

完整 API 文档：http://localhost:8000/docs

## 📁 项目结构

```
Local-Notes-MCP-Server/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── core/              # 核心配置
│   │   ├── db/                # 数据库
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模式
│   │   └── api/               # API 路由
│   ├── tests/                 # 测试
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # 前端代码（Week 3）
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── DEVELOPMENT_PLAN.md         # 开发计划
├── README.md
└── .gitignore
```

## 🗓 开发路线图

- [x] **Week 1**: 后端基础框架 + 笔记 CRUD API ✅
- [ ] **Week 2**: 通义千问 API 集成
- [ ] **Week 3**: 前端基础 UI
- [ ] **Week 4**: 前后端联调 + MVP 部署
- [ ] **Week 5**: 全文搜索
- [ ] **Week 6-7**: 语义搜索 + ChromaDB
- [ ] **Week 8**: 标签系统
- [ ] **Week 9**: AI 聊天增强
- [ ] **Week 10+**: 用户认证、高级功能

详细计划见 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

## 🧪 测试

### 后端测试

```bash
cd backend
pytest
```

### 手动测试

使用 Swagger UI：http://localhost:8000/docs

或使用 curl：

```bash
# 创建笔记
curl -X POST "http://localhost:8000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"测试笔记","content":"# Hello\n这是一条测试笔记","tags":["test"]}'

# 获取笔记列表
curl "http://localhost:8000/api/notes"
```

## 💡 使用示例

### 创建笔记
1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/notes` 端点
3. 点击 "Try it out"
4. 输入笔记数据并执行

### 搜索笔记
```bash
# 按标签搜索
curl "http://localhost:8000/api/notes?tag=工作"

# 关键词搜索
curl "http://localhost:8000/api/notes?search=Python"

# 组合搜索
curl "http://localhost:8000/api/notes?search=AI&tag=学习&page=1&limit=20"
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [开发计划](DEVELOPMENT_PLAN.md)
- [后端文档](backend/README.md)
- [通义千问 API 文档](https://help.aliyun.com/zh/dashscope/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 📧 联系方式

如有问题，请提交 Issue 或联系维护者。

---

**当前状态**: Week 1 MVP 开发中 🚧

**最后更新**: 2025-12-13
