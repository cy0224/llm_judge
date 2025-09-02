"""JSON内容提取器"""

import json
import re
from typing import Any, Optional, Union
from loguru import logger


class JSONExtractor:
    """JSON内容提取器
    
    支持JSONPath语法进行JSON内容提取
    """
    
    def __init__(self, 
                 extraction_failure_mode: str = "ignore",
                 log_extraction_failures: bool = True):
        """
        初始化JSON提取器
        
        Args:
            extraction_failure_mode: 提取失败时的处理方式
                - "ignore": 忽略提取失败，使用原始内容
                - "error": 提取失败时抛出异常
                - "empty": 提取失败时返回空字符串
            log_extraction_failures: 是否在提取失败时记录警告日志
        """
        self.extraction_failure_mode = extraction_failure_mode
        self.log_extraction_failures = log_extraction_failures
    
    def _extract_json_from_markdown(self, text: str) -> str:
        """从markdown代码块中提取JSON内容"""
        # 尝试匹配 ```json...``` 或 ```...``` 代码块
        json_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        match = re.search(json_pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # 如果没有找到代码块，返回原文本
        return text.strip()
    
    def _parse_json_safely(self, text: str) -> Optional[Any]:
        """安全地解析JSON字符串"""
        try:
            # 首先尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 尝试从markdown代码块中提取JSON
                clean_text = self._extract_json_from_markdown(text)
                return json.loads(clean_text)
            except json.JSONDecodeError as e:
                if self.log_extraction_failures:
                    logger.warning(f"JSON解析失败: {e}, 原始文本: {text[:100]}...")
                return None
    
    def _extract_by_path(self, data: Any, path: str) -> Any:
        """根据路径提取JSON数据
        
        支持的路径格式:
        - $: 根节点（不提取）
        - $.field: 提取根节点的field字段
        - $.field.subfield: 提取嵌套字段
        - $.field[0]: 提取数组元素
        - $.field[*]: 提取所有数组元素
        """
        if path == "$" or path == "":
            return data
        
        # 移除开头的 $.
        if path.startswith("$."):
            path = path[2:]
        elif path.startswith("$"):
            path = path[1:]
        
        # 分割路径
        parts = self._split_path(path)
        
        current = data
        for part in parts:
            try:
                if part.endswith("]"): # 数组访问
                    field, index_part = part.split("[", 1)
                    index_part = index_part.rstrip("]")
                    
                    if field:  # 先访问字段
                        current = current[field]
                    
                    if index_part == "*":  # 获取所有元素
                        if isinstance(current, list):
                            return current
                        else:
                            raise ValueError(f"尝试对非数组类型使用[*]: {type(current)}")
                    else:  # 获取特定索引
                        index = int(index_part)
                        current = current[index]
                else:  # 普通字段访问
                    current = current[part]
            except (KeyError, IndexError, TypeError, ValueError) as e:
                if self.log_extraction_failures:
                    logger.warning(f"路径提取失败: {path}, 错误: {e}")
                raise
        
        return current
    
    def _split_path(self, path: str) -> list:
        """分割路径字符串"""
        parts = []
        current = ""
        in_bracket = False
        
        for char in path:
            if char == "[":
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
                current += char
            elif char == "]":
                current += char
                parts.append(current)
                current = ""
                in_bracket = False
            elif char == "." and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def extract(self, content: str, extract_path: str) -> str:
        """提取JSON内容
        
        Args:
            content: 原始内容
            extract_path: 提取路径，支持JSONPath语法
                - $ 或 "" 表示不提取，返回原始内容
                - $.name 提取根节点的name字段
                - $.score.Chinese 提取嵌套字段
                - $.items[0] 提取数组第一个元素
                - $.choices[0].message.content.$ 嵌套JSON提取，先提取content，再从中提取JSON
                - $.choices[0].message.content.$.user 嵌套JSON提取，提取content中JSON的user字段
        
        Returns:
            str: 提取后的内容
        """
        # 如果路径为空或为$，直接返回原始内容
        if not extract_path or extract_path == "$" or extract_path == "":
            return content
        
        # 检查是否包含嵌套JSON提取（路径中有多个$）
        if self._has_nested_extraction(extract_path):
            return self._extract_nested_json(content, extract_path)
        
        try:
            # 解析JSON
            json_data = self._parse_json_safely(content)
            if json_data is None:
                return self._handle_extraction_failure(
                    f"无法解析JSON内容", content
                )
            
            # 根据路径提取数据
            extracted_data = self._extract_by_path(json_data, extract_path)
            
            # 将提取的数据转换为字符串
            if isinstance(extracted_data, (dict, list)):
                return json.dumps(extracted_data, ensure_ascii=False, separators=(',', ':'))
            else:
                return str(extracted_data)
        
        except Exception as e:
            return self._handle_extraction_failure(
                f"提取路径 '{extract_path}' 失败: {e}", content
            )
    
    def _handle_extraction_failure(self, error_msg: str, original_content: str) -> str:
        """处理提取失败的情况"""
        if self.log_extraction_failures:
            logger.warning(error_msg)
        
        if self.extraction_failure_mode == "error":
            raise ValueError(error_msg)
        elif self.extraction_failure_mode == "empty":
            return ""
        else:  # "ignore"
            return original_content
    
    def validate_path(self, path: str) -> bool:
        """验证路径格式是否正确
        
        Args:
            path: 要验证的路径
        
        Returns:
            bool: 路径是否有效
        """
        if not path:
            return False
            
        # 基本格式检查
        if not path.startswith('$'):
            return False
            
        # 检查是否有连续的点
        if '..' in path:
            return False
            
        # 如果只是$，则有效
        if path == '$':
            return True
            
        # 检查$后面必须跟点
        if len(path) > 1 and not path[1] == '.':
            return False
        
        # 检查括号匹配
        bracket_count = 0
        for char in path:
            if char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count < 0:
                    return False
        
        return bracket_count == 0
    
    def _has_nested_extraction(self, path: str) -> bool:
        """检查路径是否包含嵌套JSON提取
        
        嵌套提取的特征是路径中包含 .$ 模式，表示需要先提取某个字段的内容，
        然后将该内容作为JSON进行二次提取
        
        Args:
            path: 提取路径
            
        Returns:
            bool: 是否包含嵌套提取
        """
        # 查找 .$ 模式，但排除路径开头的 $
        return '.$' in path
    
    def _extract_nested_json(self, content: str, extract_path: str) -> str:
        """处理嵌套JSON提取
        
        当路径包含 .$ 时，分两步处理：
        1. 先按第一个 .$ 之前的路径提取内容
        2. 将提取的内容作为JSON，按 .$ 之后的路径继续提取
        
        Args:
            content: 原始内容
            extract_path: 包含嵌套提取的路径
            
        Returns:
            str: 提取后的内容
        """
        try:
            # 找到第一个 .$ 的位置
            nested_pos = extract_path.find('.$')
            if nested_pos == -1:
                # 没有找到嵌套标记，按普通路径处理
                return self.extract(content, extract_path)
            
            # 分割路径
            first_path = extract_path[:nested_pos]  # 第一段路径
            remaining_path = extract_path[nested_pos + 2:]  # 剩余路径（去掉.$）
            
            # 第一步：按第一段路径提取内容
            if first_path == "":
                # 如果第一段为空，直接使用原始内容
                intermediate_content = content
            else:
                intermediate_content = self.extract(content, first_path)
            
            # 第二步：从提取的内容中解析JSON并继续提取
            if remaining_path == "" or remaining_path == "$":
                # 如果剩余路径为空或只是$，需要从中间内容提取JSON字符串
                return self._extract_json_string_from_text(intermediate_content)
            else:
                # 继续按剩余路径提取（可能还有更多层嵌套）
                json_content = self._extract_json_string_from_text(intermediate_content)
                return self.extract(json_content, "$" + remaining_path)
                
        except Exception as e:
            return self._handle_extraction_failure(
                f"嵌套提取路径 '{extract_path}' 失败: {e}", content
            )
    
    def _extract_json_string_from_text(self, text: str) -> str:
        """从文本中提取JSON字符串
        
        这个方法用于处理嵌套JSON提取的第二步，从已提取的文本内容中
        找到并提取JSON字符串
        
        Args:
            text: 包含JSON的文本内容
            
        Returns:
            str: 提取的JSON字符串
        """
        # 首先尝试直接解析为JSON
        try:
            json.loads(text)
            return text  # 如果已经是有效JSON，直接返回
        except json.JSONDecodeError:
            pass
        
        # 尝试从markdown代码块中提取JSON
        json_from_markdown = self._extract_json_from_markdown(text)
        if json_from_markdown != text.strip():
            # 如果从markdown中提取到了不同的内容，验证是否为有效JSON
            try:
                json.loads(json_from_markdown)
                return json_from_markdown
            except json.JSONDecodeError:
                pass
        
        # 尝试使用正则表达式查找JSON对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                json.loads(match)
                return match  # 返回第一个有效的JSON对象
            except json.JSONDecodeError:
                continue
        
        # 如果都失败了，返回原始文本
        if self.log_extraction_failures:
            logger.warning(f"无法从文本中提取有效的JSON字符串: {text[:100]}...")
        
        return text