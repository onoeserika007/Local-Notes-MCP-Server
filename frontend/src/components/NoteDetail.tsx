/**
 * 笔记详情组件
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getNote, summarizeNote, autoTagNote, deleteNote } from '../services/api';
import type { Note } from '../types/note';
import './NoteDetail.css';

export default function NoteDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiLoading, setAiLoading] = useState<string | null>(null);

  // 加载笔记详情
  const loadNote = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError('');
      const data = await getNote(parseInt(id));
      setNote(data);
    } catch (err) {
      setError('加载笔记失败: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNote();
  }, [id]);

  // AI 生成摘要
  const handleSummarize = async () => {
    if (!note) return;
    
    try {
      setAiLoading('summarize');
      const updated = await summarizeNote(note.id);
      setNote(updated);
    } catch (err) {
      alert('生成摘要失败: ' + (err as Error).message);
    } finally {
      setAiLoading(null);
    }
  };

  // AI 自动标签
  const handleAutoTag = async () => {
    if (!note) return;
    
    try {
      setAiLoading('tag');
      const updated = await autoTagNote(note.id);
      setNote(updated);
    } catch (err) {
      alert('生成标签失败: ' + (err as Error).message);
    } finally {
      setAiLoading(null);
    }
  };

  // 删除笔记
  const handleDelete = async () => {
    if (!note || !confirm('确定要删除这篇笔记吗？')) return;
    
    try {
      await deleteNote(note.id);
      navigate('/');
    } catch (err) {
      alert('删除失败: ' + (err as Error).message);
    }
  };

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!note) {
    return <div className="empty-state">笔记不存在</div>;
  }

  return (
    <div className="note-detail-container">
      <div className="note-detail-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← 返回列表
        </button>
        <div className="note-actions">
          <button
            onClick={handleSummarize}
            disabled={aiLoading === 'summarize'}
            className="ai-button"
          >
            {aiLoading === 'summarize' ? '生成中...' : '🤖 生成摘要'}
          </button>
          <button
            onClick={handleAutoTag}
            disabled={aiLoading === 'tag'}
            className="ai-button"
          >
            {aiLoading === 'tag' ? '生成中...' : '🏷️ 自动标签'}
          </button>
          <button onClick={handleDelete} className="delete-button">
            🗑️ 删除
          </button>
        </div>
      </div>

      <div className="note-detail-content">
        <h1 className="note-title">{note.title}</h1>

        {note.summary && (
          <div className="note-summary-box">
            <strong>📝 摘要：</strong>
            <p>{note.summary}</p>
          </div>
        )}

        {note.tags && note.tags.length > 0 && (
          <div className="note-tags">
            {note.tags.map((tag, idx) => (
              <span key={idx} className="tag">
                #{tag}
              </span>
            ))}
          </div>
        )}

        <div className="note-markdown">
          <ReactMarkdown>{note.content}</ReactMarkdown>
        </div>

        <div className="note-footer">
          {note.file_path && (
            <div className="note-file-path">
              📂 文件路径: {note.file_path}
            </div>
          )}
          <div className="note-timestamps">
            <div>创建时间: {new Date(note.created_at).toLocaleString('zh-CN')}</div>
            <div>更新时间: {new Date(note.updated_at).toLocaleString('zh-CN')}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
