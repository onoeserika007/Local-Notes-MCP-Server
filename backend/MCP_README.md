# MCP Server 使用指南

## 概述

本项目实现了 MCP (Model Context Protocol) Server，让 VS Code 的 Cline 插件可以直接访问和操作你的笔记库。

## 架构

```
Cline (VS Code插件) ←→ MCP Server ←→ Notes Database
     (AI客户端)           (纯数据接口)     (SQLite + ChromaDB)
```

**注意**: MCP Server 不调用 AI，AI 推理由 Cline 自己完成！

## 已实现的功能

### Tools（工具）- AI可以调用的操作

1. **search_notes** - 搜索笔记
   - 支持关键词搜索（keyword）
   - 支持语义搜索（semantic）
   - 参数：query, mode, limit

2. **get_note** - 获取笔记详情
   - 参数：note_id

3. **list_notes** - 列出所有笔记
   - 可选按标签筛选
   - 参数：tag（可选）

4. **get_notes_by_tag** - 获取指定标签的笔记
   - 参数：tag

5. **list_all_tags** - 列出所有标签
   - 无参数

### Resources（资源）- AI可以读取的数据

1. **notes://stats** - 笔记库统计信息
2. **notes://{id}** - 单条笔记内容

## 使用方法

### 1. 配置已完成

MCP Server 已自动配置到 Cline，配置文件位于：
```
~/.vscode-server/data/User/globalStorage/hybridtalentcomputing.cline-chinese/settings/cline_mcp_settings.json
```

### 2. 重启 VS Code 或重新加载 Cline

重启 VS Code 窗口，或在 Cline 中点击"重新连接 MCP"。

### 3. 在 Cline 中使用

现在你可以在 Cline 对话框中直接操作笔记：

**示例对话：**

```
你: "搜索我关于 Raft 的笔记"
Cline: [自动调用 search_notes("Raft", mode="semantic")]
Cline: "找到了 5 条相关笔记：..."

你: "帮我总结第 123 号笔记"
Cline: [自动调用 get_note(123)]
Cline: [阅读笔记内容]
Cline: "这条笔记主要讲了..."

你: "我学了哪些分布式系统相关的内容？"
Cline: [调用 get_notes_by_tag("分布式系统")]
Cline: "你学习了以下主题：..."

你: "我的笔记库有多少条笔记？"
Cline: [读取 notes://stats]
Cline: "你的笔记库包含 341 条笔记..."
```

### 4. 高级用法

**知识库问答：**
```
你: "基于我的笔记，解释 Raft 的 Leader 选举机制"
Cline: [搜索相关笔记 → 阅读内容 → 基于你的笔记回答]
```

**学习路径建议：**
```
你: "我想深入学习分布式事务，我现在掌握了什么基础？"
Cline: [分析你的笔记库 → 给出建议]
```

**代码辅助：**
```
你: "参考我的笔记，帮我实现一个线程安全的队列"
Cline: [搜索 C++ 多线程笔记 → 生成代码]
```

## 与 Web 应用的关系

**双模式架构：**

1. **Web 模式**（已有）
   ```
   React 前端 ←→ FastAPI 后端 ←→ 通义千问 API
                     ↓
                 SQLite/ChromaDB
   ```
   - 适合：普通用户，友好的 UI
   - AI：后端调用通义千问

2. **MCP 模式**（新增）
   ```
   Cline ←→ MCP Server ←→ SQLite/ChromaDB
   (自带AI)   (纯数据接口)
   ```
   - 适合：开发者，在 VS Code 中使用
   - AI：Cline 自己的 AI

**两者共享同一个数据库**，互不冲突！

## 排错

### MCP Server 未连接

1. 检查配置文件：
   ```bash
   cat ~/.vscode-server/data/User/globalStorage/hybridtalentcomputing.cline-chinese/settings/cline_mcp_settings.json
   ```

2. 检查 Python 环境：
   ```bash
   cd /home/inory/agent_ws/backend
   python mcp_server.py  # 应该等待输入（正常）
   ```

3. 查看 Cline 的日志（在 VS Code 中）

### 数据库不存在

确保 FastAPI 后端至少运行过一次，创建了数据库表。

### 语义搜索失败

需要先运行向量化服务：
```bash
cd /home/inory/agent_ws/backend
python -c "from app.services.vector_service import initialize_embeddings; initialize_embeddings()"
```

## 技术细节

- **协议**: Model Context Protocol (Anthropic 标准)
- **通信**: stdio (标准输入输出)
- **数据库**: 共享 Web 应用的 SQLite 数据库
- **向量搜索**: 共享 ChromaDB 向量库
- **AI**: 无（由 Cline 提供）

## 下一步

可以扩展的功能：
- [ ] create_note - 创建笔记
- [ ] update_note - 更新笔记
- [ ] delete_note - 删除笔记
- [ ] summarize_note - 生成摘要（需要调用通义千问）
- [ ] find_related_notes - 查找相关笔记
- [ ] analyze_knowledge_graph - 分析笔记关联

目前实现的是**只读操作**，避免意外修改数据。
