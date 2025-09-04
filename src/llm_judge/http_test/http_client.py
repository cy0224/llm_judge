"""HTTP客户端模块"""

import time
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from loguru import logger

# 导入配置
try:
    from ..config import config
except ImportError:
    # 如果无法导入配置，使用空配置
    class MockConfig:
        def get(self, key, default=None):
            return default
    config = MockConfig()


@dataclass
class HTTPResponse:
    """HTTP响应结果"""
    status_code: int
    content: str
    headers: Dict[str, str]
    response_time: float
    url: str
    method: str
    error: Optional[str] = None
    raw_response: Optional[requests.Response] = None


class HTTPClient:
    """HTTP客户端"""
    
    def __init__(self, 
                 base_url: str = None,
                 timeout: int = None,
                 max_retries: int = None,
                 retry_backoff_factor: float = None,
                 headers: Dict[str, str] = None,
                 auth: tuple = None,
                 verify_ssl: bool = None):
        # 参数优先级处理：构造函数参数 > 配置文件 > 默认值
        timeout = timeout if timeout is not None else config.get('http.timeout', 30)
        max_retries = max_retries if max_retries is not None else config.get('http.max_retries', 3)
        retry_backoff_factor = retry_backoff_factor if retry_backoff_factor is not None else config.get('http.retry_delay', 0.3)
        verify_ssl = verify_ssl if verify_ssl is not None else config.get('http.verify_ssl', True)
        
        # 从配置文件获取默认headers
        config_headers = config.get('http.headers', {})
        if isinstance(config_headers, dict):
            if headers:
                config_headers.update(headers)
            headers = config_headers
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        
        # 设置默认headers
        default_headers = {
            'User-Agent': 'LLM-Judge-HTTP-Client/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        
        # 设置认证
        if auth:
            self.session.auth = auth
        
        # SSL验证
        self.session.verify = verify_ssl
        
        # 设置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        if self.base_url:
            return urljoin(self.base_url.rstrip('/') + '/', endpoint.lstrip('/'))
        return endpoint
    
    def _prepare_data(self, data: Any) -> Union[str, bytes, None]:
        """准备请求数据"""
        if data is None:
            return None
        
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False)
        
        if isinstance(data, str):
            return data
        
        return str(data)
    
    def request(self, 
                method: str,
                endpoint: str,
                data: Any = None,
                params: Dict[str, Any] = None,
                headers: Dict[str, str] = None,
                timeout: int = None,
                **kwargs) -> HTTPResponse:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: 端点URL
            data: 请求数据
            params: URL参数
            headers: 请求头
            timeout: 超时时间
            **kwargs: 其他requests参数
        
        Returns:
            HTTPResponse: 响应结果
        """
        url = self._build_url(endpoint)
        start_time = time.time()
        
        # 准备请求参数
        request_kwargs = {
            'timeout': timeout or self.timeout,
            'params': params,
            **kwargs
        }
        
        # 设置请求头
        if headers:
            request_kwargs['headers'] = headers
        
        # 设置请求数据
        if data is not None:
            if method.upper() in ['GET', 'HEAD', 'DELETE']:
                # GET等方法不应该有body，将数据放到params中
                if isinstance(data, dict):
                    request_kwargs['params'] = {**(request_kwargs.get('params') or {}), **data}
            else:
                request_kwargs['data'] = self._prepare_data(data)
        
        try:
            logger.debug(f"发送 {method.upper()} 请求到 {url}")
            
            response = self.session.request(
                method=method.upper(),
                url=url,
                **request_kwargs
            )
            
            response_time = time.time() - start_time
            
            # 尝试获取响应内容
            try:
                content = response.text
            except Exception as e:
                content = f"无法解析响应内容: {e}"
            
            logger.info(f"{method.upper()} {url} - {response.status_code} ({response_time:.3f}s)")
            
            return HTTPResponse(
                status_code=response.status_code,
                content=content,
                headers=dict(response.headers),
                response_time=response_time,
                url=url,
                method=method.upper(),
                raw_response=response
            )
        
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            error_msg = f"请求超时 ({timeout or self.timeout}s)"
            logger.error(f"{method.upper()} {url} - {error_msg}")
            
            return HTTPResponse(
                status_code=0,
                content="",
                headers={},
                response_time=response_time,
                url=url,
                method=method.upper(),
                error=error_msg
            )
        
        except requests.exceptions.ConnectionError as e:
            response_time = time.time() - start_time
            error_msg = f"连接错误: {e}"
            logger.error(f"{method.upper()} {url} - {error_msg}")
            
            return HTTPResponse(
                status_code=0,
                content="",
                headers={},
                response_time=response_time,
                url=url,
                method=method.upper(),
                error=error_msg
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"请求异常: {e}"
            logger.error(f"{method.upper()} {url} - {error_msg}")
            
            return HTTPResponse(
                status_code=0,
                content="",
                headers={},
                response_time=response_time,
                url=url,
                method=method.upper(),
                error=error_msg
            )
    
    def get(self, endpoint: str, **kwargs) -> HTTPResponse:
        """发送GET请求"""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Any = None, **kwargs) -> HTTPResponse:
        """发送POST请求"""
        return self.request('POST', endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Any = None, **kwargs) -> HTTPResponse:
        """发送PUT请求"""
        return self.request('PUT', endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> HTTPResponse:
        """发送DELETE请求"""
        return self.request('DELETE', endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Any = None, **kwargs) -> HTTPResponse:
        """发送PATCH请求"""
        return self.request('PATCH', endpoint, data=data, **kwargs)
    
    def head(self, endpoint: str, **kwargs) -> HTTPResponse:
        """发送HEAD请求"""
        return self.request('HEAD', endpoint, **kwargs)
    
    def options(self, endpoint: str, **kwargs) -> HTTPResponse:
        """发送OPTIONS请求"""
        return self.request('OPTIONS', endpoint, **kwargs)
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class HTTPClientPool:
    """HTTP客户端池"""
    
    def __init__(self):
        self.clients: Dict[str, HTTPClient] = {}
    
    def get_client(self, 
                   name: str,
                   base_url: str = None,
                   **kwargs) -> HTTPClient:
        """获取或创建HTTP客户端
        
        Args:
            name: 客户端名称
            base_url: 基础URL
            **kwargs: HTTPClient参数
        
        Returns:
            HTTPClient: HTTP客户端实例
        """
        if name not in self.clients:
            self.clients[name] = HTTPClient(base_url=base_url, **kwargs)
            logger.info(f"创建HTTP客户端: {name} ({base_url})")
        
        return self.clients[name]
    
    def remove_client(self, name: str):
        """移除客户端"""
        if name in self.clients:
            self.clients[name].close()
            del self.clients[name]
            logger.info(f"移除HTTP客户端: {name}")
    
    def close_all(self):
        """关闭所有客户端"""
        for name, client in self.clients.items():
            client.close()
            logger.info(f"关闭HTTP客户端: {name}")
        self.clients.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


# 全局客户端池实例
client_pool = HTTPClientPool()