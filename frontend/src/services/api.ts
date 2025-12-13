/**
 * API 服务层 - 封装所有后端 API 调用
 */
import axios from 'axios';
import type {
  Note,
  NotesResponse,
  CreateNoteRequest,
  UpdateNoteRequest,
  AIResponse,
  ChatRequest,
} from '../types/note';

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== 笔记 CRUD ====================

/**
 * 获取笔记列表
 */
export const getNotes = async (params?: {
  page?: number;
  limit?: number;
  search?: string;
  tags?: string;
}): Promise<NotesResponse> => {
  const response = await api.get<NotesResponse>('/notes/', { params });
  return response.data;
};

/**
 * 获取单个笔记
 */
export const getNote = async (id: number): Promise<Note> => {
  const response = await api.get<Note>(`/notes/${id}`);
  return response.data;
};

/**
 * 根据文件路径获取笔记
 */
export const getNoteByPath = async (filePath: string): Promise<Note> => {
  const response = await api.get<Note>(`/notes/by-path`, {
    params: { file_path: filePath }
  });
  return response.data;
};

/**
 * 创建笔记
 */
export const createNote = async (data: CreateNoteRequest): Promise<Note> => {
  const response = await api.post<Note>('/notes/', data);
  return response.data;
};

/**
 * 更新笔记
 */
export const updateNote = async (
  id: number,
  data: UpdateNoteRequest
): Promise<Note> => {
  const response = await api.put<Note>(`/notes/${id}`, data);
  return response.data;
};

/**
 * 删除笔记
 */
export const deleteNote = async (id: number): Promise<void> => {
  await api.delete(`/notes/${id}`);
};

// ==================== AI 功能 ====================

/**
 * 生成笔记摘要
 */
export const summarizeNote = async (noteId: number): Promise<Note> => {
  const response = await api.post<Note>('/ai/summarize', { note_id: noteId });
  return response.data;
};

/**
 * 自动生成标签
 */
export const autoTagNote = async (noteId: number): Promise<Note> => {
  const response = await api.post<Note>('/ai/auto-tag', { note_id: noteId });
  return response.data;
};

/**
 * AI 对话（带上下文）
 */
export const chatWithContext = async (
  query: string,
  noteIds?: number[]
): Promise<AIResponse> => {
  const data: ChatRequest = { query, note_ids: noteIds };
  const response = await api.post<AIResponse>('/ai/chat-with-context', data);
  return response.data;
};

/**
 * 获取文件夹结构（懒加载）
 */
export const getFolderStructure = async (path?: string): Promise<{
  items: Array<{
    name: string;
    path: string;
    is_folder: boolean;
    note_count: number;
  }>;
}> => {
  const params = path ? { path } : {};
  const response = await api.get('/notes/folders', { params });
  return response.data;
};

/**
 * 按文件夹路径获取笔记
 */
export const getNotesByFolder = async (folderPath: string): Promise<Note[]> => {
  const response = await api.get<NotesResponse>('/notes/', {
    params: { page: 1, limit: 1000 }
  });
  
  // 前端过滤该路径下的笔记
  return response.data.notes.filter(note => {
    if (!note.file_path) return false;
    return note.file_path.startsWith(folderPath + '/') || note.file_path === folderPath;
  });
};

/**
 * AI 对话（无上下文）
 */
export const chat = async (query: string): Promise<AIResponse> => {
  const response = await api.post<AIResponse>('/ai/chat', { query });
  return response.data;
};

// ==================== Obsidian 集成 ====================

/**
 * 导入 Obsidian vault
 */
export const importObsidian = async (forceUpdate = false) => {
  const response = await api.post('/obsidian/import', null, {
    params: { force_update: forceUpdate },
  });
  return response.data;
};

/**
 * 获取 Obsidian 状态
 */
export const getObsidianStatus = async () => {
  const response = await api.get('/obsidian/status');
  return response.data;
};

/**
 * 全量同步
 */
export const fullSync = async () => {
  const response = await api.post('/obsidian/sync/full');
  return response.data;
};

export default api;
