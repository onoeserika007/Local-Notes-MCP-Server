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
        system_prompt: Optional[str] = None,
        stream: bool = False
    ):
        """
        基于笔记上下文的对话
        
        Args:
            query: 用户问题
            context_notes: 相关笔记内容列表
            system_prompt: 自定义系统提示词
            stream: 是否流式输出
            
        Returns:
            如果stream=False，返回完整回答文本
            如果stream=True，返回生成器
        """
        # 构建上下文
        if context_notes:
            context = "\n\n---\n\n".join([
                f"笔记 {i+1}:\n{note[:1000]}" 
                for i, note in enumerate(context_notes)
            ])
        else:
            context = "没有找到相关笔记。"
        
        # 默认系统提示词
        if not system_prompt:
            system_prompt = """你是一个智能笔记助手。你的任务是基于用户的笔记内容回答问题。
要求：
1. 仔细阅读提供的笔记内容
2. 基于笔记内容回答问题，必要时引用具体笔记
3. 如果笔记中没有相关信息，诚实告知用户
4. 回答要简洁、准确、有条理
5. 使用中文回答"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"参考笔记：\n{context}\n\n问题：{query}"}
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
