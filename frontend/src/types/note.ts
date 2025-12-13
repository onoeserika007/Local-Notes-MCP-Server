/**
 * Note 类型定义
 */

export interface Note {
  id: number;
  title: string;
  content: string;
  tags: string[];
  summary?: string;
  file_path?: string;
  file_modified_time?: string;
  created_at: string;
  updated_at: string;
}

export interface NotesResponse {
  total: number;
  page: number;
  limit: number;
  notes: Note[];
}

export interface CreateNoteRequest {
  title: string;
  content: string;
  tags?: string[];
}

export interface UpdateNoteRequest {
  title?: string;
  content?: string;
  tags?: string[];
}

export interface AIResponse {
  reply: string;
  referenced_notes?: Array<{
    id: number;
    title: string;
  }>;
}

export interface SummarizeRequest {
  note_id: number;
}

export interface AutoTagRequest {
  note_id: number;
}

export interface ChatRequest {
  query: string;
  note_ids?: number[];
}
