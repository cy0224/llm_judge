"""HTTP测试执行器"""

import time
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger

from .http_client import HTTPClient, HTTPResponse
from ..utils.comparator import BatchComparator, ComparisonResult, ComparisonType


@dataclass
class HTTPTestCase:
    """HTTP测试用例"""
    id: str
    method: str
    endpoint: str
    expected: str
    data: Optional[Any] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    expected_status_code: Optional[int] = None
    timeout: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class HTTPTestResult:
    """HTTP测试结果"""
    test_case: HTTPTestCase
    http_response: HTTPResponse
    comparison_result: ComparisonResult
    status_code_match: bool
    execution_time: float
    timestamp: str


class HTTPTester:
    """HTTP测试器"""
    
    def __init__(self, 
                 http_client: HTTPClient,
                 comparator: BatchComparator = None,
                 max_workers: int = 10,
                 progress_bar: bool = True,
                 default_expected_status: int = 200):
        self.http_client = http_client
        self.comparator = comparator or BatchComparator()
        self.max_workers = max_workers
        self.progress_bar = progress_bar
        self.default_expected_status = default_expected_status
        self.test_results: List[HTTPTestResult] = []
    
    def run_single_test(self, 
                       test_case: HTTPTestCase,
                       comparison_type: ComparisonType = ComparisonType.EXACT) -> HTTPTestResult:
        """运行单个HTTP测试用例
        
        Args:
            test_case: HTTP测试用例
            comparison_type: 对比类型
        
        Returns:
            HTTPTestResult: 测试结果
        """
        start_time = time.time()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 发送HTTP请求
            http_response = self.http_client.request(
                method=test_case.method,
                endpoint=test_case.endpoint,
                data=test_case.data,
                params=test_case.params,
                headers=test_case.headers,
                timeout=test_case.timeout
            )
            
            # 检查状态码
            expected_status = test_case.expected_status_code or self.default_expected_status
            status_code_match = http_response.status_code == expected_status
            
            # 对比响应内容
            actual_content = self._extract_response_content(http_response, test_case)
            
            # 获取提取路径
            expected_extract_path = "$"
            actual_extract_path = "$"
            if test_case.metadata:
                expected_extract_path = test_case.metadata.get('expected_extract_path', '$')
                actual_extract_path = test_case.metadata.get('actual_extract_path', '$')
            
            comparison_result = self.comparator.comparator.compare(
                expected=test_case.expected,
                actual=actual_content,
                comparison_type=comparison_type,
                expected_extract_path=expected_extract_path,
                actual_extract_path=actual_extract_path
            )
            
            execution_time = time.time() - start_time
            
            # 综合判断测试是否通过
            overall_match = status_code_match and comparison_result.is_match
            comparison_result.is_match = overall_match
            
            if comparison_result.details is None:
                comparison_result.details = {}
            comparison_result.details.update({
                'status_code_match': status_code_match,
                'expected_status_code': expected_status,
                'actual_status_code': http_response.status_code
            })
            
            logger.info(f"HTTP测试用例 {test_case.id} 完成，状态码: {http_response.status_code}, 匹配: {overall_match}")
            
            return HTTPTestResult(
                test_case=test_case,
                http_response=http_response,
                comparison_result=comparison_result,
                status_code_match=status_code_match,
                execution_time=execution_time,
                timestamp=timestamp
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"HTTP测试用例 {test_case.id} 执行失败: {e}")
            
            # 创建错误响应
            error_response = HTTPResponse(
                status_code=0,
                content="",
                headers={},
                response_time=0.0,
                url=test_case.endpoint,
                method=test_case.method,
                error=str(e)
            )
            
            # 创建失败的对比结果
            error_comparison = ComparisonResult(
                is_match=False,
                similarity_score=0.0,
                comparison_type=comparison_type,
                expected=test_case.expected,
                actual="",
                error_message=str(e)
            )
            
            return HTTPTestResult(
                test_case=test_case,
                http_response=error_response,
                comparison_result=error_comparison,
                status_code_match=False,
                execution_time=execution_time,
                timestamp=timestamp
            )
    
    def _extract_response_content(self, 
                                 http_response: HTTPResponse, 
                                 test_case: HTTPTestCase) -> str:
        """提取响应内容用于对比
        
        Args:
            http_response: HTTP响应
            test_case: 测试用例
        
        Returns:
            str: 提取的内容
        """
        if http_response.error:
            return f"ERROR: {http_response.error}"
        
        content = http_response.content
        
        # 尝试解析JSON并格式化
        try:
            if content.strip().startswith(('{', '[')):
                parsed_json = json.loads(content)
                # 如果测试用例的expected也是JSON格式，则格式化输出
                try:
                    json.loads(test_case.expected)
                    content = json.dumps(parsed_json, indent=2, ensure_ascii=False, sort_keys=True)
                except json.JSONDecodeError:
                    # expected不是JSON，保持原始内容
                    pass
        except json.JSONDecodeError:
            # 不是JSON，保持原始内容
            pass
        
        return content
    
    def run_batch_tests(self, 
                       test_cases: List[HTTPTestCase],
                       comparison_type: ComparisonType = ComparisonType.EXACT,
                       parallel: bool = True) -> List[HTTPTestResult]:
        """批量运行HTTP测试用例
        
        Args:
            test_cases: 测试用例列表
            comparison_type: 对比类型
            parallel: 是否并行执行
        
        Returns:
            List[HTTPTestResult]: 测试结果列表
        """
        logger.info(f"开始执行 {len(test_cases)} 个HTTP测试用例")
        
        if parallel and self.max_workers > 1:
            return self._run_parallel_tests(test_cases, comparison_type)
        else:
            return self._run_sequential_tests(test_cases, comparison_type)
    
    def _run_sequential_tests(self, 
                             test_cases: List[HTTPTestCase],
                             comparison_type: ComparisonType) -> List[HTTPTestResult]:
        """顺序执行测试"""
        results = []
        
        iterator = tqdm(test_cases, desc="执行HTTP测试") if self.progress_bar else test_cases
        
        for test_case in iterator:
            result = self.run_single_test(test_case, comparison_type)
            results.append(result)
            
            if self.progress_bar and hasattr(iterator, 'set_postfix'):
                iterator.set_postfix({
                    'passed': sum(1 for r in results if r.comparison_result.is_match),
                    'failed': sum(1 for r in results if not r.comparison_result.is_match)
                })
        
        self.test_results.extend(results)
        return results
    
    def _run_parallel_tests(self, 
                           test_cases: List[HTTPTestCase],
                           comparison_type: ComparisonType) -> List[HTTPTestResult]:
        """并行执行测试"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_test = {
                executor.submit(self.run_single_test, test_case, comparison_type): test_case
                for test_case in test_cases
            }
            
            # 处理完成的任务
            if self.progress_bar:
                futures = tqdm(as_completed(future_to_test), total=len(test_cases), desc="执行HTTP测试")
            else:
                futures = as_completed(future_to_test)
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                    
                    if self.progress_bar and hasattr(futures, 'set_postfix'):
                        futures.set_postfix({
                            'passed': sum(1 for r in results if r.comparison_result.is_match),
                            'failed': sum(1 for r in results if not r.comparison_result.is_match)
                        })
                
                except Exception as e:
                    test_case = future_to_test[future]
                    logger.error(f"HTTP测试用例 {test_case.id} 执行异常: {e}")
        
        # 按原始顺序排序结果
        test_case_order = {tc.id: i for i, tc in enumerate(test_cases)}
        results.sort(key=lambda r: test_case_order.get(r.test_case.id, float('inf')))
        
        self.test_results.extend(results)
        return results
    
    def get_summary_statistics(self, results: List[HTTPTestResult] = None) -> Dict[str, Any]:
        """获取HTTP测试统计信息
        
        Args:
            results: 测试结果列表，如果为None则使用所有结果
        
        Returns:
            Dict: 统计信息
        """
        if results is None:
            results = self.test_results
        
        if not results:
            return {}
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.comparison_result.is_match)
        failed_tests = total_tests - passed_tests
        error_tests = sum(1 for r in results if r.http_response.error)
        status_code_failures = sum(1 for r in results if not r.status_code_match)
        
        execution_times = [r.execution_time for r in results]
        response_times = [r.http_response.response_time for r in results]
        similarity_scores = [r.comparison_result.similarity_score for r in results]
        
        # 状态码统计
        status_codes = {}
        for r in results:
            code = r.http_response.status_code
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # HTTP方法统计
        methods = {}
        for r in results:
            method = r.test_case.method.upper()
            methods[method] = methods.get(method, 0) + 1
        
        stats = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'status_code_failures': status_code_failures,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0.0,
            'average_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            'min_similarity': min(similarity_scores) if similarity_scores else 0.0,
            'max_similarity': max(similarity_scores) if similarity_scores else 0.0,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'total_execution_time': sum(execution_times),
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0.0,
            'min_response_time': min(response_times) if response_times else 0.0,
            'max_response_time': max(response_times) if response_times else 0.0,
            'status_code_distribution': status_codes,
            'method_distribution': methods
        }
        
        return stats
    
    def export_results(self, 
                      results: List[HTTPTestResult] = None,
                      format: str = 'dict') -> Any:
        """导出HTTP测试结果
        
        Args:
            results: 测试结果列表
            format: 导出格式 ('dict', 'json')
        
        Returns:
            导出的数据
        """
        if results is None:
            results = self.test_results
        
        exported_data = []
        for result in results:
            data = {
                'test_case': asdict(result.test_case),
                'http_response': asdict(result.http_response),
                'comparison_result': asdict(result.comparison_result),
                'status_code_match': result.status_code_match,
                'execution_time': result.execution_time,
                'timestamp': result.timestamp
            }
            exported_data.append(data)
        
        if format == 'json':
            import json
            return json.dumps(exported_data, indent=2, ensure_ascii=False)
        
        return exported_data
    
    def clear_results(self):
        """清空测试结果"""
        self.test_results.clear()
        logger.info("已清空HTTP测试结果")