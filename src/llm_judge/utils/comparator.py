"""测试结果对比工具"""

import difflib
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from fuzzywuzzy import fuzz
from loguru import logger

from .json_extractor import JSONExtractor
from ..llm_test.llm_client import BaseLLMClient, LLMClientFactory
from ..config import config


class ComparisonType(Enum):
    """对比类型枚举"""
    EXACT = "exact"  # 精确匹配
    FUZZY = "fuzzy"  # 模糊匹配
    CONTAINS = "contains"  # 包含匹配
    JSON = "json"  # JSON结构匹配
    LLM = "llm"  # LLM语义匹配
    CUSTOM = "custom"  # 自定义匹配


@dataclass
class ComparisonResult:
    """对比结果"""
    is_match: bool
    similarity_score: float
    comparison_type: ComparisonType
    expected: str
    actual: str
    diff: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TextComparator:
    """文本对比器"""
    
    def __init__(self, 
                 fuzzy_threshold: float = 0.8,
                 ignore_case: bool = True,
                 ignore_whitespace: bool = True,
                 json_extractor: JSONExtractor = None,
                 llm_client: BaseLLMClient = None):
        self.fuzzy_threshold = fuzzy_threshold
        self.ignore_case = ignore_case
        self.ignore_whitespace = ignore_whitespace
        self.json_extractor = json_extractor or JSONExtractor()
        self.llm_client = llm_client
    
    @classmethod
    def create_with_comparison_llm(cls, 
                                   fuzzy_threshold: float = None,
                                   ignore_case: bool = True,
                                   ignore_whitespace: bool = True,
                                   json_extractor: JSONExtractor = None) -> 'TextComparator':
        """创建带有专门比较LLM客户端的文本比较器"""
        import os
        
        # 从配置中获取比较LLM的配置
        provider = config.get('test.comparison.llm.provider', 'openai')
        
        # 获取API密钥
        api_key = config.get(f'test.comparison.llm.{provider}.api_key')
        if not api_key:
            api_key = os.getenv(f'{provider.upper()}_API_KEY')
        
        if not api_key:
            logger.warning(f"未找到{provider.upper()}_API_KEY，LLM比较功能将不可用")
            return cls(
                fuzzy_threshold=fuzzy_threshold or 0.8,
                ignore_case=ignore_case,
                ignore_whitespace=ignore_whitespace,
                json_extractor=json_extractor,
                llm_client=None
            )
        
        # 创建专门用于比较的LLM客户端
        llm_client = LLMClientFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=config.get(f'test.comparison.llm.{provider}.model'),
            temperature=config.get(f'test.comparison.llm.{provider}.temperature', 0.0),
            max_tokens=config.get(f'test.comparison.llm.{provider}.max_tokens', 500),
            base_url=config.get(f'test.comparison.llm.{provider}.base_url'),
            timeout=config.get(f'test.comparison.llm.{provider}.timeout', 30),
            max_retries=config.get(f'test.comparison.llm.{provider}.max_retries', 2),
            retry_delay=config.get(f'test.comparison.llm.{provider}.retry_delay', 1)
        )
        
        return cls(
            fuzzy_threshold=fuzzy_threshold or 0.8,
            ignore_case=ignore_case,
            ignore_whitespace=ignore_whitespace,
            json_extractor=json_extractor,
            llm_client=llm_client
        )
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本"""
        if not isinstance(text, str):
            text = str(text)
        
        if self.ignore_case:
            text = text.lower()
        
        if self.ignore_whitespace:
            text = ' '.join(text.split())
        
        return text
    
    def _extract_json_from_markdown(self, text: str) -> str:
        """从markdown代码块中提取JSON内容"""
        import re
        
        # 尝试匹配 ```json...``` 或 ```...``` 代码块
        json_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        match = re.search(json_pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # 如果没有找到代码块，返回原文本
        return text.strip()
    
    def exact_match(self, expected: str, actual: str) -> ComparisonResult:
        """精确匹配"""
        expected_norm = self._normalize_text(expected)
        actual_norm = self._normalize_text(actual)
        
        is_match = expected_norm == actual_norm
        similarity_score = 1.0 if is_match else 0.0
        
        diff = None
        if not is_match:
            diff = '\n'.join(difflib.unified_diff(
                expected_norm.splitlines(),
                actual_norm.splitlines(),
                fromfile='expected',
                tofile='actual',
                lineterm=''
            ))
        
        return ComparisonResult(
            is_match=is_match,
            similarity_score=similarity_score,
            comparison_type=ComparisonType.EXACT,
            expected=expected,
            actual=actual,
            diff=diff
        )
    
    def fuzzy_match(self, expected: str, actual: str) -> ComparisonResult:
        """模糊匹配"""
        expected_norm = self._normalize_text(expected)
        actual_norm = self._normalize_text(actual)
        
        # 使用多种模糊匹配算法
        ratio = fuzz.ratio(expected_norm, actual_norm) / 100.0
        partial_ratio = fuzz.partial_ratio(expected_norm, actual_norm) / 100.0
        token_sort_ratio = fuzz.token_sort_ratio(expected_norm, actual_norm) / 100.0
        token_set_ratio = fuzz.token_set_ratio(expected_norm, actual_norm) / 100.0
        
        # 取最高分作为相似度
        similarity_score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)
        is_match = similarity_score >= self.fuzzy_threshold
        
        details = {
            'ratio': ratio,
            'partial_ratio': partial_ratio,
            'token_sort_ratio': token_sort_ratio,
            'token_set_ratio': token_set_ratio,
            'threshold': self.fuzzy_threshold
        }
        
        diff = None
        if not is_match:
            diff = '\n'.join(difflib.unified_diff(
                expected_norm.splitlines(),
                actual_norm.splitlines(),
                fromfile='expected',
                tofile='actual',
                lineterm=''
            ))
        
        return ComparisonResult(
            is_match=is_match,
            similarity_score=similarity_score,
            comparison_type=ComparisonType.FUZZY,
            expected=expected,
            actual=actual,
            diff=diff,
            details=details
        )
    
    def contains_match(self, expected: str, actual: str) -> ComparisonResult:
        """包含匹配"""
        expected_norm = self._normalize_text(expected)
        actual_norm = self._normalize_text(actual)
        
        is_match = expected_norm in actual_norm
        similarity_score = 1.0 if is_match else 0.0
        
        return ComparisonResult(
            is_match=is_match,
            similarity_score=similarity_score,
            comparison_type=ComparisonType.CONTAINS,
            expected=expected,
            actual=actual,
            details={'contains_check': f"'{expected_norm}' in '{actual_norm}'"}
        )
    
    def json_match(self, expected: str, actual: str) -> ComparisonResult:
        """JSON结构匹配"""
        try:
            expected_json = json.loads(expected)
            
            # 提取markdown代码块中的JSON内容
            actual_clean = self._extract_json_from_markdown(actual)
            actual_json = json.loads(actual_clean)
            
            is_match = expected_json == actual_json
            similarity_score = 1.0 if is_match else 0.0
            
            diff = None
            if not is_match:
                expected_formatted = json.dumps(expected_json, indent=2, ensure_ascii=False)
                actual_formatted = json.dumps(actual_json, indent=2, ensure_ascii=False)
                diff = '\n'.join(difflib.unified_diff(
                    expected_formatted.splitlines(),
                    actual_formatted.splitlines(),
                    fromfile='expected.json',
                    tofile='actual.json',
                    lineterm=''
                ))
            
            return ComparisonResult(
                is_match=is_match,
                similarity_score=similarity_score,
                comparison_type=ComparisonType.JSON,
                expected=expected,
                actual=actual,
                diff=diff
            )
        
        except json.JSONDecodeError as e:
            return ComparisonResult(
                is_match=False,
                similarity_score=0.0,
                comparison_type=ComparisonType.JSON,
                expected=expected,
                actual=actual,
                error_message=f"JSON解析错误: {e}"
            )
    
    def llm_match(self, expected: str, actual: str) -> ComparisonResult:
        """LLM语义匹配"""
        if self.llm_client is None:
            return ComparisonResult(
                is_match=False,
                similarity_score=0.0,
                comparison_type=ComparisonType.LLM,
                expected=expected,
                actual=actual,
                error_message="LLM客户端未配置"
            )
        
        try:
            # 构建LLM评估提示
            prompt = f"""请评估以下两个文本的语义相似度，并给出0-100的分数。

期望文本：
{expected}

实际文本：
{actual}

请按以下JSON格式回复：
{{
    "similarity_score": <0-100的数字>,
    "reasoning": "<评估理由>"
}}

评估标准：
- 90-100分：语义完全一致或高度相似
- 70-89分：语义基本一致，有轻微差异
- 50-69分：语义部分相似，有明显差异
- 30-49分：语义有一定关联，但差异较大
- 0-29分：语义不相关或完全不同

请只返回JSON格式的结果，不要包含其他内容。"""
            
            # 调用LLM进行评估
            response = self.llm_client.generate(prompt)
            
            if response.error:
                return ComparisonResult(
                    is_match=False,
                    similarity_score=0.0,
                    comparison_type=ComparisonType.LLM,
                    expected=expected,
                    actual=actual,
                    error_message=f"LLM调用错误: {response.error}"
                )
            
            # 解析LLM响应
            try:
                # 提取JSON内容
                llm_result_text = self._extract_json_from_markdown(response.content)
                llm_result = json.loads(llm_result_text)
                
                similarity_score = float(llm_result.get('similarity_score', 0)) / 100.0
                reasoning = llm_result.get('reasoning', '')
                
                # 始终根据用户设置的阈值进行最终判断，不依赖LLM的is_match
                is_match = similarity_score >= self.fuzzy_threshold
                
                details = {
                    'llm_model': response.model,
                    'llm_reasoning': reasoning,
                    'llm_raw_score': llm_result.get('similarity_score', 0),
                    'llm_response_time': response.response_time,
                    'threshold': self.fuzzy_threshold
                }
                
                return ComparisonResult(
                    is_match=is_match,
                    similarity_score=similarity_score,
                    comparison_type=ComparisonType.LLM,
                    expected=expected,
                    actual=actual,
                    details=details
                )
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                return ComparisonResult(
                    is_match=False,
                    similarity_score=0.0,
                    comparison_type=ComparisonType.LLM,
                    expected=expected,
                    actual=actual,
                    error_message=f"LLM响应解析错误: {e}，原始响应: {response.content}"
                )
                
        except Exception as e:
            logger.error(f"LLM匹配过程中发生错误: {e}")
            return ComparisonResult(
                is_match=False,
                similarity_score=0.0,
                comparison_type=ComparisonType.LLM,
                expected=expected,
                actual=actual,
                error_message=str(e)
            )
    
    def compare(self, 
                expected: str, 
                actual: str, 
                comparison_type: ComparisonType = ComparisonType.EXACT,
                expected_extract_path: str = "$",
                actual_extract_path: str = "$") -> ComparisonResult:
        """执行对比
        
        Args:
            expected: 期望结果
            actual: 实际结果
            comparison_type: 对比类型
            expected_extract_path: 期望结果的JSON提取路径
            actual_extract_path: 实际结果的JSON提取路径
        
        Returns:
            ComparisonResult: 对比结果
        """
        try:
            # 进行JSON内容提取
            extracted_expected = self.json_extractor.extract(expected, expected_extract_path)
            extracted_actual = self.json_extractor.extract(actual, actual_extract_path)
            
            # 执行对比
            if comparison_type == ComparisonType.EXACT:
                result = self.exact_match(extracted_expected, extracted_actual)
            elif comparison_type == ComparisonType.FUZZY:
                result = self.fuzzy_match(extracted_expected, extracted_actual)
            elif comparison_type == ComparisonType.CONTAINS:
                result = self.contains_match(extracted_expected, extracted_actual)
            elif comparison_type == ComparisonType.JSON:
                result = self.json_match(extracted_expected, extracted_actual)
            elif comparison_type == ComparisonType.LLM:
                result = self.llm_match(extracted_expected, extracted_actual)
            else:
                raise ValueError(f"不支持的对比类型: {comparison_type}")
            
            # 添加提取信息到结果详情中
            if result.details is None:
                result.details = {}
            result.details.update({
                'expected_extract_path': expected_extract_path,
                'actual_extract_path': actual_extract_path,
                'extracted_expected': extracted_expected,
                'extracted_actual': extracted_actual,
                'original_expected': expected,
                'original_actual': actual
            })
            
            return result
        
        except Exception as e:
            logger.error(f"对比过程中发生错误: {e}")
            return ComparisonResult(
                is_match=False,
                similarity_score=0.0,
                comparison_type=comparison_type,
                expected=expected,
                actual=actual,
                error_message=str(e)
            )


class BatchComparator:
    """批量对比器"""
    
    def __init__(self, comparator: TextComparator = None):
        self.comparator = comparator or TextComparator()
    
    def compare_batch(self, 
                     test_results: List[Dict[str, Any]], 
                     comparison_type: ComparisonType = ComparisonType.EXACT) -> List[ComparisonResult]:
        """批量对比测试结果
        
        Args:
            test_results: 测试结果列表，每个元素包含 'expected' 和 'actual' 键
            comparison_type: 对比类型
        
        Returns:
            List[ComparisonResult]: 对比结果列表
        """
        comparison_results = []
        
        for i, result in enumerate(test_results):
            try:
                expected = result.get('expected', '')
                actual = result.get('actual', '')
                
                comparison_result = self.comparator.compare(
                    expected, actual, comparison_type
                )
                
                # 添加测试用例信息
                if comparison_result.details is None:
                    comparison_result.details = {}
                comparison_result.details['test_index'] = i
                comparison_result.details['test_id'] = result.get('id', f'test_{i}')
                
                comparison_results.append(comparison_result)
                
            except Exception as e:
                logger.error(f"对比测试用例 {i} 时发生错误: {e}")
                comparison_results.append(ComparisonResult(
                    is_match=False,
                    similarity_score=0.0,
                    comparison_type=comparison_type,
                    expected=result.get('expected', ''),
                    actual=result.get('actual', ''),
                    error_message=str(e),
                    details={'test_index': i, 'test_id': result.get('id', f'test_{i}')}
                ))
        
        return comparison_results
    
    def get_summary_statistics(self, comparison_results: List[ComparisonResult]) -> Dict[str, Any]:
        """获取对比结果统计信息
        
        Args:
            comparison_results: 对比结果列表
        
        Returns:
            Dict: 统计信息
        """
        if not comparison_results:
            return {}
        
        total_count = len(comparison_results)
        match_count = sum(1 for result in comparison_results if result.is_match)
        error_count = sum(1 for result in comparison_results if result.error_message)
        
        similarity_scores = [result.similarity_score for result in comparison_results]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        
        return {
            'total_tests': total_count,
            'passed_tests': match_count,
            'failed_tests': total_count - match_count,
            'error_tests': error_count,
            'pass_rate': match_count / total_count if total_count > 0 else 0.0,
            'average_similarity': avg_similarity,
            'min_similarity': min(similarity_scores) if similarity_scores else 0.0,
            'max_similarity': max(similarity_scores) if similarity_scores else 0.0
        }