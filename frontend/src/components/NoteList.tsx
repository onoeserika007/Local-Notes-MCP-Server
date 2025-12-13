/**
 * 笔记列表组件 - 简化版，使用懒加载文件夹树
 */
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getNotes, getNoteByPath } from '../services/api';
import type { Note } from '../types/note';
import FolderTree from './FolderTree';
import './NoteList.css';

export default function NoteList() {
  const navigate = useNavigate();
  const [notes, setNotes] = useState<Note[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const ITEMS_PER_PAGE = 20;

  // 加载笔记
  const loadNotes = async () => {
    try {
      setLoading(true);
      setError('');
      
      // 加载所有笔记（带搜索）
      const data = await getNotes({
        page,
        limit: ITEMS_PER_PAGE,
        search: search || undefined,
      });
      setNotes(data.notes);
      setTotal(data.total);
    } catch (err) {
      setError('加载笔记失败: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和参数变化时重新加载
  useEffect(() => {
    loadNotes();
  }, [search, page]);

  const handleFileSelect = async (filePath: string) => {
    // 点击文件：根据file_path从后端获取笔记并跳转
    console.log('File selected:', filePath);
    try {
      const note = await getNoteByPath(filePath);
      console.log('Found note:', note.id, note.title);
      navigate(`/notes/${note.id}`);
    } catch (err: any) {
      console.error('Failed to find note:', err);
      if (err.response?.status === 404) {
        setError(`找不到文件: ${filePath}`);
      } else {
        setError('查找笔记失败: ' + err.message);
      }
    }
  };

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  return (
    <div className="note-list-layout">
      {/* 侧边栏 */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <button
          className="sidebar-toggle"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? '→' : '←'}
        </button>
        
        {!sidebarCollapsed && (
          <FolderTree
            onFileSelect={handleFileSelect}
            selectedPath={null}
          />
        )}
      </div>

      {/* 主内容区 */}
      <div className="main-content">
        <div className="note-list-container">
          <div className="note-list-header">
            <h1>我的笔记</h1>
            
            {/* 搜索框 */}
            <div className="search-bar">
              <input
                type="text"
                placeholder="🔍 搜索笔记标题..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading">加载中...</div>
          ) : (
            <>
              <div className="note-grid">
                {notes.map((note) => (
                  <Link
                    key={note.id}
                    to={`/notes/${note.id}`}
                    className="note-card"
                  >
                    <h2 className="note-title">{note.title}</h2>
                    {note.file_path && (
                      <div className="note-path">📄 {note.file_path}</div>
                    )}
                    {note.summary && (
                      <p className="note-summary">{note.summary}</p>
                    )}
                    {note.tags && note.tags.length > 0 && (
                      <div className="note-tags">
                        {note.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="tag">
                            {tag}
                          </span>
                        ))}
                        {note.tags.length > 3 && (
                          <span className="tag-more">+{note.tags.length - 3}</span>
                        )}
                      </div>
                    )}
                    <div className="note-date">
                      {new Date(note.updated_at).toLocaleDateString('zh-CN')}
                    </div>
                  </Link>
                ))}
              </div>

              {/* 分页 */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    上一页
                  </button>
                  <span className="page-info">
                    第 {page} / {totalPages} 页 (共 {total} 条)
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    下一页
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
