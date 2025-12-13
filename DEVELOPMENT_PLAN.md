# AI 笔记应用开发计划

> 基于通义千问 API 的智能笔记管理系统
> 
> 创建时间：2025-12-13

## 📋 项目概述

一个类似 Local Notes MCP Server 的 AI 增强笔记应用，使用通义千问 API，包含完整的前后端实现。

### 核心特性
- 📝 本地笔记管理（CRUD）
- 🔍 全文搜索 + 语义搜索
- 🤖 AI 智能摘要、问答、推荐
- 🏷️ 标签分类系统
- 🎨 现代化 Web UI

## 🏗 技术架构

### 后端技术栈
```yaml
语言: Python 3.11+
框架: FastAPI
数据库: SQLite + SQLAlchemy
LLM: 通义千问 (dashscope SDK)
向量库: ChromaDB
搜索: SQLite FTS5
认证: JWT
```

### 前端技术栈
```yaml
框架: React 18 + TypeScript
构建工具: Vite
UI 库: Ant Design / shadcn/ui
状态管理: Zustand + React Query
样式: TailwindCSS
```

### 项目结构
```
my-notes-ai-app/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── notes.py     # 笔记 CRUD
│   │   │       ├── search.py    # 搜索接口
│   │   │       ├── ai.py        # AI 功能
│   │   │       └── auth.py      # 用户认证
│   │   ├── models/              # 数据模型
│   │   │   ├── note.py
│   │   │   └── user.py
│   │   ├── services/
│   │   │   ├── note_service.py
│   │   │   ├── qwen_service.py  # 通义千问集成
│   │   │   ├── vector_service.py
│   │   │   └── search_service.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── migrations/
│   │   └── core/
│   │       ├── config.py
│   │       └── security.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── NoteEditor.tsx
│   │   │   ├── NoteList.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── TagManager.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NoteDetail.tsx
│   │   │   └── Settings.tsx
│   │   ├── api/
│   │   │   └── client.ts        # API 调用封装
│   │   ├── hooks/
│   │   │   ├── useNotes.ts
│   │   │   └── useChat.ts
│   │   ├── store/
│   │   │   └── noteStore.ts
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docker-compose.yml
├── README.md
└── DEVELOPMENT_PLAN.md (本文件)
```

## 🚀 迭代开发计划

### 第一阶段：MVP 核心功能（3-4周）

#### Week 1: 后端基础框架
- [x] 项目初始化
  - FastAPI 项目搭建
  - 数据库设计（SQLite + SQLAlchemy）
  - 环境配置管理
- [ ] 笔记基础 API
  - 创建笔记 (POST /api/notes)
  - 读取笔记 (GET /api/notes/:id)
  - 更新笔记 (PUT /api/notes/:id)
  - 删除笔记 (DELETE /api/notes/:id)
  - 列表查询 (GET /api/notes)
- [ ] 数据模型设计
  ```python
  Note:
    - id: int
    - title: str
    - content: str (Markdown)
    - tags: list[str]
    - created_at: datetime
    - updated_at: datetime
    - user_id: int (可选)
  ```

#### Week 2: 通义千问集成
- [ ] SDK 集成
  - dashscope SDK 安装配置
  - API Key 管理
  - 错误处理和重试机制
- [ ] AI 基础功能
  - 文本摘要 API (POST /api/ai/summarize)
  - 聊天对话 API (POST /api/ai/chat)
  - Embedding 生成 (内部服务)
- [ ] 单元测试
  - QwenService 测试
  - API 端点测试

#### Week 3: 前端基础 UI
- [ ] React 项目初始化
  - Vite + React + TypeScript 配置
  - 路由设置 (React Router)
  - UI 库集成 (Ant Design / shadcn)
- [ ] 核心组件开发
  - NoteList: 笔记列表展示
  - NoteEditor: Markdown 编辑器
  - SearchBar: 搜索框
  - Layout: 整体布局
- [ ] API 集成
  - Axios/Fetch 封装
  - React Query 数据管理
  - CRUD 操作对接

#### Week 4: MVP 联调测试
- [ ] 前后端联调
  - CORS 配置
  - API 对接验证
  - 错误处理统一
- [ ] 基础功能测试
  - 笔记创建/编辑流程
  - AI 摘要功能验证
  - 用户体验优化
- [ ] MVP 部署
  - Docker 镜像构建
  - docker-compose 配置
  - 本地部署测试

**里程碑 1**: ✅ 能够创建、编辑笔记，使用 AI 生成摘要

---

### 第二阶段：搜索与智能功能（4-5周）

#### Week 5: 全文搜索
- [ ] SQLite FTS5 集成
  - 全文索引配置
  - 中文分词支持
- [ ] 搜索 API 实现
  - 关键词搜索 (GET /api/search?q=keyword)
  - 标签过滤
  - 排序和分页
- [ ] 前端搜索界面
  - 实时搜索
  - 搜索结果高亮
  - 筛选器组件

#### Week 6-7: 语义搜索
- [ ] ChromaDB 集成
  - 向量数据库初始化
  - 笔记向量化流程
  - 增量索引更新
- [ ] 语义搜索实现
  - 查询向量化
  - 相似度检索
  - 混合搜索（关键词+语义）
- [ ] VectorService 开发
  ```python
  - embed_note(note_id, content)
  - search_similar(query, top_k=5)
  - update_embeddings(note_ids)
  ```

#### Week 8: 标签系统
- [ ] 标签数据模型
  - Tag 表设计
  - 多对多关系
- [ ] 标签 API
  - 创建标签
  - 笔记打标签
  - 按标签筛选
- [ ] AI 自动标签
  - 基于内容自动生成标签
  - 标签推荐

#### Week 9: AI 聊天增强
- [ ] 上下文管理
  - 基于笔记的对话
  - 多轮对话历史
  - 相关笔记自动检索
- [ ] ChatInterface 组件
  - 聊天窗口 UI
  - 流式响应支持
  - 代码高亮显示
- [ ] Prompt 工程优化
  - System prompt 设计
  - 少样本学习示例

**里程碑 2**: ✅ 支持语义搜索，AI 可基于笔记库智能问答

---

### 第三阶段：用户体验优化（3-4周）

#### Week 10: 用户认证
- [ ] JWT 认证实现
  - 注册/登录 API
  - Token 生成和验证
  - 密码加密 (bcrypt)
- [ ] 权限管理
  - 用户笔记隔离
  - API 权限中间件
- [ ] 前端认证流程
  - 登录/注册页面
  - Token 存储管理
  - 路由守卫

#### Week 11: 高级功能
- [ ] 笔记版本历史
  - 修改历史记录
  - 差异对比 (diff)
  - 版本回滚
- [ ] 笔记导入导出
  - Markdown 批量导入
  - 导出为 PDF/HTML
  - 数据备份功能
- [ ] 笔记关联
  - 双向链接
  - 相关笔记推荐
  - 知识图谱可视化（可选）

#### Week 12-13: UI/UX 优化
- [ ] 响应式设计
  - 移动端适配
  - 平板布局优化
- [ ] 性能优化
  - 虚拟列表（长列表）
  - 懒加载和分页
  - 图片压缩和缓存
- [ ] 交互细节
  - 快捷键支持
  - 拖拽排序
  - 离线草稿保存
- [ ] 主题系统
  - 明暗主题切换
  - 自定义配色

**里程碑 3**: ✅ 完整的用户系统，优秀的交互体验

---

### 第四阶段：生产就绪（持续）

#### Week 14+: 稳定性与部署

- [ ] 测试覆盖
  - 后端单元测试 (pytest)
  - 前端组件测试 (Vitest)
  - E2E 测试 (Playwright)
  - 测试覆盖率 > 80%

- [ ] 性能优化
  - 数据库查询优化
  - Redis 缓存层
  - API 响应时间监控
  - 前端 Bundle 优化

- [ ] 安全加固
  - SQL 注入防护
  - XSS 防护
  - CSRF Token
  - 敏感信息加密
  - API 速率限制

- [ ] 监控与日志
  - 结构化日志 (loguru)
  - 错误追踪 (Sentry)
  - 性能监控 (Prometheus)
  - 访问统计

- [ ] 部署方案
  - Docker 生产镜像
  - Nginx 反向代理
  - HTTPS 配置
  - 自动化部署 (CI/CD)
  - 数据备份策略

- [ ] 文档完善
  - API 文档 (Swagger)
  - 用户使用手册
  - 开发者文档
  - 部署指南

**里程碑 4**: ✅ 生产环境稳定运行

---

## 🔌 关键技术实现

### 1. 通义千问集成示例

```python
# backend/app/services/qwen_service.py
from dashscope import Generation, TextEmbedding
import dashscope

class QwenService:
    def __init__(self, api_key: str):
        dashscope.api_key = api_key
    
    def chat(self, messages: list, stream: bool = False):
        """聊天接口"""
        response = Generation.call(
            model='qwen-turbo',  # 或 qwen-plus, qwen-max
            messages=messages,
            stream=stream,
            result_format='message'
        )
        return response
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成文本摘要"""
        messages = [{
            'role': 'user',
            'content': f'请用不超过{max_length}字总结以下内容，保留关键信息：\n\n{text}'
        }]
        response = self.chat(messages)
        return response.output.choices[0].message.content
    
    def generate_embedding(self, text: str) -> list[float]:
        """生成文本向量"""
        response = TextEmbedding.call(
            model=TextEmbedding.Models.text_embedding_v2,
            input=text
        )
        return response.output.embeddings[0].embedding
    
    def chat_with_context(self, query: str, context_notes: list[str]) -> str:
        """基于笔记上下文的对话"""
        context = "\n\n".join([f"笔记 {i+1}:\n{note}" 
                               for i, note in enumerate(context_notes)])
        
        messages = [
            {
                "role": "system",
                "content": "你是一个智能笔记助手。基于用户的笔记内容回答问题，引用具体笔记内容。"
            },
            {
                "role": "user",
                "content": f"参考笔记：\n{context}\n\n问题：{query}"
            }
        ]
        
        response = self.chat(messages)
        return response.output.choices[0].message.content
```

### 2. 向量搜索实现

```python
# backend/app/services/vector_service.py
import chromadb
from chromadb.config import Settings

class VectorService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_note(self, note_id: int, content: str, embedding: list[float]):
        """添加笔记向量"""
        self.collection.add(
            ids=[str(note_id)],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{"note_id": note_id}]
        )
    
    def search_similar(self, query_embedding: list[float], top_k: int = 5):
        """搜索相似笔记"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results
    
    def update_note(self, note_id: int, embedding: list[float]):
        """更新笔记向量"""
        self.collection.update(
            ids=[str(note_id)],
            embeddings=[embedding]
        )
    
    def delete_note(self, note_id: int):
        """删除笔记向量"""
        self.collection.delete(ids=[str(note_id)])
```

### 3. API 路由示例

```python
# backend/app/api/routes/ai.py
from fastapi import APIRouter, Depends, HTTPException
from app.services.qwen_service import QwenService
from app.services.vector_service import VectorService
from app.services.note_service import NoteService

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat")
async def chat_with_notes(
    query: str,
    note_ids: list[int] = None,
    qwen: QwenService = Depends(),
    note_service: NoteService = Depends()
):
    """基于笔记的 AI 对话"""
    # 如果没指定笔记，使用语义搜索找相关笔记
    if not note_ids:
        query_embedding = qwen.generate_embedding(query)
        similar_notes = await note_service.search_by_vector(
            query_embedding, 
            top_k=3
        )
        note_ids = [note.id for note in similar_notes]
    
    # 获取笔记内容
    notes = await note_service.get_notes_by_ids(note_ids)
    context = [note.content for note in notes]
    
    # 调用 AI
    response = qwen.chat_with_context(query, context)
    
    return {
        "reply": response,
        "referenced_notes": [{"id": n.id, "title": n.title} for n in notes]
    }

@router.post("/summarize/{note_id}")
async def summarize_note(
    note_id: int,
    qwen: QwenService = Depends(),
    note_service: NoteService = Depends()
):
    """生成笔记摘要"""
    note = await note_service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    summary = qwen.summarize(note.content)
    
    # 可选：保存摘要到数据库
    await note_service.update_summary(note_id, summary)
    
    return {"note_id": note_id, "summary": summary}

@router.post("/auto-tag/{note_id}")
async def auto_tag_note(
    note_id: int,
    qwen: QwenService = Depends(),
    note_service: NoteService = Depends()
):
    """AI 自动打标签"""
    note = await note_service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # 提示词工程
    prompt = f"""分析以下笔记内容，生成3-5个最相关的标签。
    要求：
    1. 标签简短（1-3个词）
    2. 反映核心主题
    3. 使用中文
    4. 只返回标签，用逗号分隔
    
    笔记内容：
    {note.content[:500]}
    """
    
    messages = [{"role": "user", "content": prompt}]
    response = qwen.chat(messages)
    tags_text = response.output.choices[0].message.content
    tags = [tag.strip() for tag in tags_text.split(',')]
    
    await note_service.add_tags(note_id, tags)
    
    return {"note_id": note_id, "tags": tags}
```

### 4. 前端 API 客户端

```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加 Token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API 方法
export const noteApi = {
  list: (params?: { page?: number; limit?: number; tag?: string }) =>
    apiClient.get('/api/notes', { params }),
  
  get: (id: number) =>
    apiClient.get(`/api/notes/${id}`),
  
  create: (data: { title: string; content: string; tags?: string[] }) =>
    apiClient.post('/api/notes', data),
  
  update: (id: number, data: Partial<{ title: string; content: string; tags: string[] }>) =>
    apiClient.put(`/api/notes/${id}`, data),
  
  delete: (id: number) =>
    apiClient.delete(`/api/notes/${id}`),
  
  search: (query: string) =>
    apiClient.get('/api/search', { params: { q: query } }),
};

export const aiApi = {
  chat: (query: string, noteIds?: number[]) =>
    apiClient.post('/api/ai/chat', { query, note_ids: noteIds }),
  
  summarize: (noteId: number) =>
    apiClient.post(`/api/ai/summarize/${noteId}`),
  
  autoTag: (noteId: number) =>
    apiClient.post(`/api/ai/auto-tag/${noteId}`),
};
```

### 5. React Hook 示例

```typescript
// frontend/src/hooks/useNotes.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { noteApi } from '@/api/client';

export function useNotes(filters?: { tag?: string }) {
  return useQuery({
    queryKey: ['notes', filters],
    queryFn: () => noteApi.list(filters),
  });
}

export function useNote(id: number) {
  return useQuery({
    queryKey: ['note', id],
    queryFn: () => noteApi.get(id),
    enabled: !!id,
  });
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: noteApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}

export function useUpdateNote(id: number) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: any) => noteApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      queryClient.invalidateQueries({ queryKey: ['note', id] });
    },
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: noteApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });
}
```

---

## 📦 环境配置

### 后端环境变量 (.env)
```bash
# 通义千问 API
QWEN_API_KEY=sk-your-api-key-here
QWEN_MODEL=qwen-turbo  # qwen-turbo, qwen-plus, qwen-max

# 数据库
DATABASE_URL=sqlite:///./notes.db

# 向量数据库
CHROMA_PERSIST_DIR=./chroma_db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 前端环境变量 (.env)
```bash
VITE_API_BASE=http://localhost:8000
VITE_APP_TITLE=AI Notes
```

---

## 🚢 部署方案

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - QWEN_API_KEY=${QWEN_API_KEY}
      - DATABASE_URL=sqlite:///./data/notes.db
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./chroma_db:/app/chroma_db
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### 一键启动
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

---

## 💰 成本估算

### 通义千问 API 定价（2025年参考）
- **qwen-turbo**: ¥0.002/千tokens（输入），¥0.006/千tokens（输出）
- **qwen-plus**: ¥0.004/千tokens（输入），¥0.012/千tokens（输出）
- **qwen-max**: ¥0.04/千tokens（输入），¥0.12/千tokens（输出）
- **text-embedding-v2**: ¥0.0007/千tokens

### 月度成本预估（中等使用量）
- 生成 1000 次摘要：~¥5-10
- 100 次对话（含上下文）：~¥10-20
- 向量化 5000 篇笔记：~¥3-5
- **总计**: ¥20-35/月

比 OpenAI GPT-4 便宜约 70-80%

---

## 📚 参考资源

### 官方文档
- [通义千问 API 文档](https://help.aliyun.com/zh/dashscope/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [ChromaDB 文档](https://docs.trychroma.com/)

### 开源参考
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Notion Clone](https://github.com/konstantinmuenster/notion-clone)
- [Obsidian](https://obsidian.md/)

---

## ✅ 当前状态

- [x] 需求分析完成
- [x] 技术选型确定
- [x] 开发计划制定
- [ ] 项目初始化
- [ ] MVP 开发中...

---

## 📝 开发注意事项

1. **安全性优先**
   - API Key 不要硬编码
   - 使用环境变量管理敏感信息
   - 所有用户输入都要验证和清理

2. **性能考虑**
   - 向量化操作异步处理
   - 大文本分块处理
   - 合理使用缓存

3. **用户体验**
   - 流式响应提升实时感
   - 加载状态反馈
   - 错误提示友好

4. **可扩展性**
   - 模块化设计
   - 接口抽象（易于切换 LLM）
   - 数据库支持迁移

5. **测试覆盖**
   - 核心功能单元测试
   - API 集成测试
   - 前端组件测试

---

**更新日志**:
- 2025-12-13: 初始版本，完成需求分析和技术选型
