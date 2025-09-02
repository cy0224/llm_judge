"""LLM客户端模块"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from loguru import logger

try:
    import openai
except ImportError:
    openai = None




@dataclass
class LLMResponse:
    """LLM响应结果"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[Any] = None


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, 
                 api_key: str,
                 model: str,
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    @abstractmethod
    def generate(self, 
                prompt: str, 
                **kwargs) -> LLMResponse:
        """生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
        
        Returns:
            LLMResponse: 生成结果
        """
        pass
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """带退避的重试机制"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"第 {attempt + 1} 次尝试失败，{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"所有重试都失败了: {e}")
        
        raise last_exception


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    def __init__(self, 
                 api_key: str,
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 base_url: str = None,
                 **kwargs):
        super().__init__(api_key, model, **kwargs)
        
        if openai is None:
            raise ImportError("请安装openai库: pip install openai")
        
        # 创建OpenAI客户端，支持自定义base_url
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.client = openai.OpenAI(**client_kwargs)
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(self, 
                prompt: str, 
                system_message: str = None,
                temperature: float = None,
                max_tokens: int = None,
                **kwargs) -> LLMResponse:
        """生成文本"""
        start_time = time.time()
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                timeout=self.timeout,
                **kwargs
            )
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                usage=response.usage.model_dump() if response.usage else None,
                response_time=response_time,
                raw_response=response
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"OpenAI API调用失败: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                response_time=response_time,
                error=str(e)
            )





class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client(provider: str, **config) -> BaseLLMClient:
        """创建LLM客户端
        
        Args:
            provider: 提供商名称 (openai)
            **config: 配置参数
        
        Returns:
            BaseLLMClient: LLM客户端实例
        """
        provider = provider.lower()
        
        if provider == "openai":
            return OpenAIClient(**config)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """获取可用的提供商列表"""
        providers = []
        
        if openai is not None:
            providers.append("openai")
        
        return providers