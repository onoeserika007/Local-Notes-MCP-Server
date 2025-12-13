/**
 * 文件夹树组件 - 懒加载版本
 * 按需从后端加载文件夹结构
 */
import { useState, useEffect } from 'react';
import { getFolderStructure } from '../services/api';
import './FolderTree.css';

interface FolderItem {
  name: string;
  path: string;
  is_folder: boolean;
  note_count: number;
  children?: FolderItem[];
  loaded?: boolean;
}

interface FolderTreeProps {
  onFileSelect: (path: string) => void;  // 选中文件时的回调
  selectedPath: string | null;
}

export default function FolderTree({ onFileSelect, selectedPath }: FolderTreeProps) {
  const [rootItems, setRootItems] = useState<FolderItem[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  // 加载根目录
  useEffect(() => {
    loadFolder('');
  }, []);

  const loadFolder = async (path: string) => {
    try {
      setLoading(true);
      const data = await getFolderStructure(path);
      
      if (path === '') {
        // 根目录
        setRootItems(data.items.map(item => ({ ...item, loaded: false })));
      } else {
        // 更新子目录
        setRootItems(prev => updateChildren(prev, path, data.items));
      }
    } catch (err) {
      console.error('Failed to load folder:', err);
    } finally {
      setLoading(false);
    }
  };

  // 递归更新子节点
  const updateChildren = (items: FolderItem[], targetPath: string, children: any[]): FolderItem[] => {
    return items.map(item => {
      if (item.path === targetPath) {
        return {
          ...item,
          children: children.map(c => ({ ...c, loaded: false })),
          loaded: true
        };
      }
      if (item.children && targetPath.startsWith(item.path + '/')) {
        return {
          ...item,
          children: updateChildren(item.children, targetPath, children)
        };
      }
      return item;
    });
  };

  const toggleFolder = async (item: FolderItem) => {
    const isExpanded = expandedFolders.has(item.path);
    
    if (isExpanded) {
      // 折叠
      setExpandedFolders(prev => {
        const next = new Set(prev);
        next.delete(item.path);
        return next;
      });
    } else {
      // 展开
      setExpandedFolders(prev => new Set(prev).add(item.path));
      
      // 如果是文件夹且未加载过，则加载
      if (item.is_folder && !item.loaded) {
        await loadFolder(item.path);
      }
    }
  };

  const handleItemClick = (item: FolderItem) => {
    console.log('Item clicked:', item.name, 'is_folder:', item.is_folder, 'path:', item.path);
    if (item.is_folder) {
      // 文件夹：展开/折叠
      toggleFolder(item);
    } else {
      // 文件：通知父组件选中了文件
      console.log('Calling onFileSelect with:', item.path);
      onFileSelect(item.path);
    }
  };

  const renderItem = (item: FolderItem, level: number = 0): JSX.Element => {
    const isExpanded = expandedFolders.has(item.path);
    const isSelected = selectedPath === item.path;
    const hasChildren = item.is_folder;

    return (
      <div key={item.path} className="folder-item">
        <div
          className={`folder-header ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${level * 16}px` }}
          onClick={() => handleItemClick(item)}
        >
          {hasChildren && (
            <span className="folder-toggle">
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          {!hasChildren && <span className="folder-toggle">📄</span>}
          <span className="folder-name">{item.name}</span>
          <span className="folder-count">({item.note_count})</span>
        </div>
        {isExpanded && item.children && (
          <div className="folder-children">
            {item.children.map(child => renderItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="folder-tree">
      <div className="folder-tree-header">
        <h3>文件夹</h3>
        {loading && <span className="loading-indicator">⏳</span>}
      </div>
      {rootItems.map(item => renderItem(item, 0))}
    </div>
  );
}
