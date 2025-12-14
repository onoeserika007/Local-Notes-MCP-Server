"""
Qwen AI Service
通义千问 API 集成服务
"""
import logging
from typing import List, Optional, Generator, Dict
from dashscope import Generation, TextEmbedding
import dashscope

from app.core.config import settings

logger = logging.getLogger(__name__)


class QwenService:
    """通义千问 AI 服务封装"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 Qwen 服务
        
        Args:
            api_key: 通义千问 API Key，默认从配置读取
            model: 模型名称，默认从配置读取
        """
        self.api_key = api_key or settings.QWEN_API_KEY
        self.model = model or settings.QWEN_MODEL
        
        if not self.api_key:
            raise ValueError("QWEN_API_KEY is not configured")
        
        dashscope.api_key = self.api_key
        logger.info(f"QwenService initialized with model: {self.model}")
    
    def chat(
        self, 
        messages: List[dict], 
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        聊天接口
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            stream: 是否流式返回
            temperature: 温度参数，控制随机性 (0-2)
            max_tokens: 最大 token 数
            
        Returns:
            API 响应结果
        """
        try:
            params = {
                'model': self.model,
                'messages': messages,
                'result_format': 'message',
                'temperature': temperature,
            }
            
            if max_tokens:
                params['max_tokens'] = max_tokens
            
            if stream:
                params['stream'] = True
                params['incremental_output'] = True
            
            response = Generation.call(**params)
            
            if response.status_code == 200:
                logger.info(f"Chat API call successful")
                return response
            else:
                logger.error(f"Chat API error: {response.code} - {response.message}")
                raise Exception(f"Qwen API error: {response.message}")
                
        except Exception as e:
            logger.error(f"Chat API exception: {str(e)}")
            raise
    
    def chat_stream(
        self,
        messages: List[Dict],
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式聊天接口，逐步返回生成内容
        
        Args:
            messages: 消息列表
            temperature: 温度参数
        
        Yields:
            每次生成的文本片段
        """
        try:
            params = {
                'model': self.model,
                'messages': messages,
                'result_format': 'message',
                'temperature': temperature,
                'stream': True,
                'incremental_output': True
            }
            
            responses = Generation.call(**params)
            
            for response in responses:
                if response.status_code == 200:
                    # 提取增量内容
                    content = response.output.choices[0].message.content
                    yield content
                else:
                    logger.error(f"Stream error: {response.code} - {response.message}")
                    break
        
        except Exception as e:
            logger.error(f"Chat stream exception: {str(e)}")
            raise
    
    def summarize(
        self, 
        text: str, 
        max_length: int = 200,
        language: str = "中文"
    ) -> str:
        """
        生成文本摘要
        
        Args:
            text: 需要摘要的文本
            max_length: 摘要最大字数
            language: 摘要语言
            
        Returns:
            摘要文本
        """
        if not text or len(text.strip()) == 0:
            return ""
        
        # 构建提示词
        prompt = f"""请为以下内容生成一个简洁的摘要，要求：
1. 使用{language}
2. 不超过{max_length}字
3. 保留关键信息和要点
4. 直接输出摘要内容，不要添加"摘要："等前缀

内容：
{text[:3000]}"""  # 限制输入长度，避免超出 token 限制
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat(messages, temperature=0.5)
            summary = response.output.choices[0].message.content
            logger.info(f"Summary generated successfully, length: {len(summary)}")
            return summary.strip()
        except Exception as e:
            logger.error(f"Summarize failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本向量（用于语义搜索）
        
        Args:
            text: 需要向量化的文本
            
        Returns:
            向量列表
        """
        try:
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v2,
                input=text[:2000]  # 限制长度
            )
            
            if response.status_code == 200:
                embedding = response.output.embeddings[0].embedding
                logger.info(f"Embedding generated, dimension: {len(embedding)}")
                return embedding
            else:
                logger.error(f"Embedding API error: {response.code} - {response.message}")
                raise Exception(f"Embedding API error: {response.message}")
                
        except Exception as e:
            logger.error(f"Generate embedding failed: {str(e)}")
            raise
    
    def chat_with_context(
        self, 
        query: str, 
        context_notes: List[str],
        all_notes_overview: Optional[List[dict]] = None,  # 所有笔记的概览
        library_stats: Optional[dict] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ):
        """
        基于笔记上下文的对话（Map-Reduce方案）
        
        Args:
            query: 用户问题
            context_notes: 相关笔记完整内容列表（Reduce阶段-精读）
            all_notes_overview: 所有笔记的概览信息（Map阶段-全局视图）
            library_stats: 笔记库统计信息
            system_prompt: 自定义系统提示词
            stream: 是否流式输出
            
        Returns:
            如果stream=False，返回完整回答文本
            如果stream=True，返回生成器
        """
        
        # ============ 构建Map阶段信息（全局笔记索引）============
        notes_index = ""
        if all_notes_overview:
            # 限制最多显示前100条笔记的概览（避免token过多）
            overview_limit = min(100, len(all_notes_overview))
            notes_list = []
            for i, note in enumerate(all_notes_overview[:overview_limit]):
                tags_str = "、".join(note.get("tags", [])[:3])  # 最多3个标签
                summary = note.get("summary", "")[:100]  # 摘要最多100字
                notes_list.append(
                    f"{i+1}. 《{note['title']}》 [{tags_str}] - {summary}"
                )
            notes_index = f"\n\n【笔记库索引 - 共{len(all_notes_overview)}条，展示前{overview_limit}条】\n" + "\n".join(notes_list)
        
        # 构建笔记库概览
        library_info = ""
        if library_stats:
            topics_str = "、".join(library_stats.get("topics", [])[:15])
            library_info = f"""
【笔记库概览】
- 总笔记数：{library_stats.get('total_notes', 0)} 条
- 主要主题：{topics_str}
"""
        
        # ============ 构建Reduce阶段信息（详细上下文）============
        detailed_context = ""
        if context_notes:
            detailed_context = "\n\n---\n\n".join([
                f"相关笔记 {i+1}（详细内容）:\n{note[:2000]}"  # 每条2000字符
                for i, note in enumerate(context_notes)
            ])
        else:
            detailed_context = "未检索到高度相关的笔记详细内容。"
        
        # 默认系统提示词（强调两阶段信息）
        if not system_prompt:
            system_prompt = f"""你是一个智能笔记助手，采用Map-Reduce方式理解用户的笔记库。

{library_info}

你掌握的信息：
1. 【全局视图】所有笔记的标题、标签和摘要（帮你了解整个知识库结构）
2. 【详细内容】与当前问题高度相关的笔记完整内容（用于深度分析）

回答要求：
1. 优先基于提供的详细笔记内容回答
2. 如果详细笔记不够，可参考全局笔记索引，建议用户查看相关笔记
3. 必要时引用具体笔记标题
4. 如果知识库中确实没有相关信息，诚实告知
5. 回答简洁、准确、有条理
6. 使用中文回答"""
        
        # 组合消息（先全局视图，再详细内容，最后是问题）
        user_content = f"""{notes_index}

{"="*50}
【相关笔记详细内容】
{detailed_context}

{"="*50}
【用户问题】
{query}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            if stream:
                return self.chat_stream(messages, temperature=0.7)
            else:
                response = self.chat(messages, temperature=0.7)
                answer = response.output.choices[0].message.content
                logger.info(f"Chat with context completed, answer length: {len(answer)}")
                return answer
        except Exception as e:
            logger.error(f"Chat with context failed: {str(e)}")
            raise
    
    def auto_tag(self, content: str, max_tags: int = 5) -> List[str]:
        """
        自动生成标签
        
        Args:
            content: 笔记内容
            max_tags: 最多生成的标签数
            
        Returns:
            标签列表
        """
        prompt = f"""分析以下笔记内容，生成{max_tags}个最相关的标签。

要求：
1. 标签简短（1-3个词）
2. 反映核心主题和关键词
3. 使用中文
4. 只返回标签，用逗号分隔，不要其他说明

笔记内容：
{content[:800]}"""
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.chat(messages, temperature=0.3)
            tags_text = response.output.choices[0].message.content
            
            # 解析标签
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            tags = tags[:max_tags]  # 限制数量
            
            logger.info(f"Auto tags generated: {tags}")
            return tags
        except Exception as e:
            logger.error(f"Auto tag failed: {str(e)}")
            return []


# 全局 Qwen 服务实例（依赖注入用）
_qwen_service: Optional[QwenService] = None


def get_qwen_service() -> QwenService:
    """
    获取 QwenService 实例（依赖注入）
    
    Returns:
        QwenService 实例
    """
    global _qwen_service
    
    if _qwen_service is None:
        _qwen_service = QwenService()
    
    return _qwen_service
