# AI Notes Frontend

基于 React + TypeScript + Vite 构建的现代化笔记管理前端。

## 技术栈

- **React 19** + **TypeScript** - 类型安全的 UI 开发
- **Vite 7** - 极速构建工具
- **pnpm** - 高效包管理（替代 npm）
- **React Router** - 路由管理
- **React Markdown** - Markdown 渲染
- **Axios** - HTTP 客户端

## 快速开始

### 1. 安装依赖（使用 pnpm）

```bash
pnpm install
```

> 注意：本项目使用 pnpm 而非 npm，速度更快且节省磁盘空间。

### 2. 启动开发服务器

```bash
pnpm dev
```

访问: http://localhost:5173/

### 3. 确保后端运行

```bash
cd ../backend
uvicorn app.main:app --reload
```

后端应运行在: http://localhost:8000

## 功能特性

- 📝 **笔记列表**：分页展示、实时搜索、标签筛选
- 📄 **Markdown 渲染**：完整的 Markdown 语法支持
- 🤖 **AI 功能**：
  - 智能摘要生成
  - 自动标签提取
  - AI 对话（带上下文）
- 🔄 **Obsidian 集成**：
  - Vault 导入（339 条笔记）
  - 文件路径显示
  - 实时同步状态

## 项目结构

```
frontend/
├── src/
│   ├── components/       # React 组件
│   ├── services/         # API 服务层
│   ├── types/            # TypeScript 类型定义
│   └── App.tsx           # 主应用
├── pnpm-lock.yaml       # pnpm 锁文件
└── package.json
```

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

## Week 3 完成情况 ✅

- ✅ 使用 pnpm 搭建项目
- ✅ 笔记列表页面（搜索、分页）
- ✅ 笔记详情页面（Markdown 渲染）
- ✅ AI 功能集成
- ✅ Obsidian 状态显示
