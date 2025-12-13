"""
Obsidian Integration Service
处理 Obsidian vault 的文件读取、解析和同步
"""
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ObsidianNote:
    """Obsidian 笔记数据结构"""
    file_path: str  # 相对于 vault 的路径
    title: str
    content: str
    tags: List[str]
    frontmatter: Dict[str, any]
    wikilinks: List[str]
    modified_time: datetime
    

class ObsidianService:
    """Obsidian vault 集成服务"""
    
    def __init__(self, vault_path: Optional[str] = None):
        """
        初始化 Obsidian 服务
        
        Args:
            vault_path: Obsidian vault 根目录路径
        """
        self.vault_path = vault_path or settings.OBSIDIAN_VAULT_PATH
        
        if not self.vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH is not configured")
        
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault not found: {self.vault_path}")
        
        logger.info(f"ObsidianService initialized with vault: {self.vault_path}")
    
    def get_all_notes(self) -> List[ObsidianNote]:
        """
        获取 vault 中所有的 markdown 笔记
        
        Returns:
            笔记列表
        """
        notes = []
        vault_path = Path(self.vault_path)
        
        # 递归查找所有 .md 文件
        for md_file in vault_path.rglob("*.md"):
            # 跳过 .obsidian 配置目录
            if ".obsidian" in md_file.parts:
                continue
            
            try:
                note = self.parse_note_file(md_file)
                if note:
                    notes.append(note)
            except Exception as e:
                logger.error(f"Failed to parse {md_file}: {str(e)}")
        
        logger.info(f"Found {len(notes)} notes in vault")
        return notes
    
    def parse_note_file(self, file_path: Path) -> Optional[ObsidianNote]:
        """
        解析单个 markdown 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的笔记对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取相对路径
            rel_path = str(file_path.relative_to(self.vault_path))
            
            # 获取文件修改时间
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # 解析 frontmatter
            frontmatter, body = self._parse_frontmatter(content)
            
            # 从文件名或 frontmatter 获取标题
            title = frontmatter.get('title') or file_path.stem
            
            # 提取标签
            tags = self._extract_tags(content, frontmatter)
            
            # 提取 WikiLinks
            wikilinks = self._extract_wikilinks(body)
            
            return ObsidianNote(
                file_path=rel_path,
                title=title,
                content=body.strip(),
                tags=tags,
                frontmatter=frontmatter,
                wikilinks=wikilinks,
                modified_time=modified_time
            )
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return None
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        解析 YAML frontmatter
        
        Args:
            content: 文件内容
            
        Returns:
            (frontmatter字典, 正文内容)
        """
        frontmatter = {}
        body = content
        
        # 匹配 frontmatter (--- ... ---)
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            
            # 简单解析 YAML (只处理常见格式)
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 处理列表格式的标签
                    if key == 'tags' and value.startswith('['):
                        value = [t.strip(' "\'') for t in value.strip('[]').split(',')]
                    
                    frontmatter[key] = value
        
        return frontmatter, body
    
    def _extract_tags(self, content: str, frontmatter: Dict) -> List[str]:
        """
        提取标签（从 frontmatter 和正文中的 #标签）
        
        Args:
            content: 文件内容
            frontmatter: frontmatter 字典
            
        Returns:
            标签列表
        """
        tags = set()
        
        # 从 frontmatter 获取
        fm_tags = frontmatter.get('tags', [])
        if isinstance(fm_tags, list):
            tags.update(fm_tags)
        elif isinstance(fm_tags, str):
            tags.add(fm_tags)
        
        # 从正文提取 #标签 (但排除 # 标题)
        # 匹配 #标签 但不在行首（避免匹配标题）
        tag_pattern = r'(?:^|\s)#([^\s#]+)'
        for match in re.finditer(tag_pattern, content, re.MULTILINE):
            tag = match.group(1)
            # 过滤掉数字标签和太长的标签
            if not tag.isdigit() and len(tag) < 50:
                tags.add(tag)
        
        return list(tags)
    
    def _extract_wikilinks(self, content: str) -> List[str]:
        """
        提取 WikiLinks [[链接]]
        
        Args:
            content: 文件内容
            
        Returns:
            链接列表
        """
        wikilink_pattern = r'\[\[([^\]]+)\]\]'
        links = re.findall(wikilink_pattern, content)
        
        # 去除别名 [[链接|别名]] -> 链接
        clean_links = []
        for link in links:
            if '|' in link:
                link = link.split('|')[0]
            clean_links.append(link.strip())
        
        return clean_links
    
    def write_note_to_file(self, note_data: Dict, file_path: str = None) -> str:
        """
        将笔记写入文件（导出功能）
        
        Args:
            note_data: 笔记数据
            file_path: 文件路径（相对于 vault），如果为 None 则根据标题生成
            
        Returns:
            实际写入的文件路径
        """
        if not file_path:
            # 根据标题生成文件名
            title = note_data.get('title', 'Untitled')
            file_path = f"{title}.md"
        
        full_path = Path(self.vault_path) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建内容
        content_parts = []
        
        # 添加 frontmatter
        if note_data.get('tags'):
            content_parts.append("---")
            content_parts.append(f"tags: {note_data['tags']}")
            if note_data.get('summary'):
                content_parts.append(f"summary: {note_data['summary']}")
            content_parts.append("---")
            content_parts.append("")
        
        # 添加正文
        content_parts.append(note_data.get('content', ''))
        
        content = '\n'.join(content_parts)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Note written to: {file_path}")
        return file_path
    
    def get_note_by_path(self, file_path: str) -> Optional[ObsidianNote]:
        """
        根据相对路径获取笔记
        
        Args:
            file_path: 相对于 vault 的文件路径
            
        Returns:
            笔记对象
        """
        full_path = Path(self.vault_path) / file_path
        
        if not full_path.exists():
            return None
        
        return self.parse_note_file(full_path)


def get_obsidian_service() -> ObsidianService:
    """
    获取 ObsidianService 实例（依赖注入）
    
    Returns:
        ObsidianService 实例
    """
    return ObsidianService()
