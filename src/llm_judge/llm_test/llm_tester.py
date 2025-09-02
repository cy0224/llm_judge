"""LLM测试执行器"""

import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger

from .llm_client import BaseLLMClient, LLMResponse
from ..utils.comparator import BatchComparator, ComparisonResult, ComparisonType


@dataclass
class TestCase:
    """测试用例"""
    id: str
    input: str
    expected: str
    system_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """测试结果"""
    test_case: TestCase
    llm_response: LLMResponse
    comparison_result: ComparisonResult
    execution_time: float
    timestamp: str


class LLMTester:
    """LLM测试器"""
    
    def __init__(self, 
                 llm_client: BaseLLMClient,
                 comparator: BatchComparator = None,
                 max_workers: int = 5,
                 progress_bar: bool = True):
        self.llm_client = llm_client
        self.comparator = comparator or BatchComparator()
        self.max_workers = max_workers
        self.progress_bar = progress_bar
        self.test_results: List[TestResult] = []
    
    def run_single_test(self, 
                       test_case: TestCase,
                       comparison_type: ComparisonType = ComparisonType.EXACT,
                       **llm_kwargs) -> TestResult:
        """运行单个测试用例
        
        Args:
            test_case: 测试用例
            comparison_type: 对比类型
            **llm_kwargs: LLM调用参数
        
        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 调用LLM生成响应
            llm_response = self.llm_client.generate(
                prompt=test_case.input,
                system_message=test_case.system_message,
                **llm_kwargs
            )
            
            # 从测试用例metadata中获取提取路径
            expected_extract_path = "$"
            actual_extract_path = "$"
            if test_case.metadata:
                expected_extract_path = test_case.metadata.get('expected_extract_path', '$')
                actual_extract_path = test_case.metadata.get('actual_extract_path', '$')
            
            # 对比结果
            comparison_result = self.comparator.comparator.compare(
                expected=test_case.expected,
                actual=llm_response.content,
                comparison_type=comparison_type,
                expected_extract_path=expected_extract_path,
                actual_extract_path=actual_extract_path
            )
            
            execution_time = time.time() - start_time
            
            logger.info(f"测试用例 {test_case.id} 完成，匹配: {comparison_result.is_match}")
            
            return TestResult(
                test_case=test_case,
                llm_response=llm_response,
                comparison_result=comparison_result,
                execution_time=execution_time,
                timestamp=timestamp
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"测试用例 {test_case.id} 执行失败: {e}")
            
            # 创建错误响应
            error_response = LLMResponse(
                content="",
                model=self.llm_client.model,
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
            
            return TestResult(
                test_case=test_case,
                llm_response=error_response,
                comparison_result=error_comparison,
                execution_time=execution_time,
                timestamp=timestamp
            )
    
    def run_batch_tests(self, 
                       test_cases: List[TestCase],
                       comparison_type: ComparisonType = ComparisonType.EXACT,
                       parallel: bool = True,
                       **llm_kwargs) -> List[TestResult]:
        """批量运行测试用例
        
        Args:
            test_cases: 测试用例列表
            comparison_type: 对比类型
            parallel: 是否并行执行
            **llm_kwargs: LLM调用参数
        
        Returns:
            List[TestResult]: 测试结果列表
        """
        logger.info(f"开始执行 {len(test_cases)} 个测试用例")
        
        if parallel and self.max_workers > 1:
            return self._run_parallel_tests(test_cases, comparison_type, **llm_kwargs)
        else:
            return self._run_sequential_tests(test_cases, comparison_type, **llm_kwargs)
    
    def _run_sequential_tests(self, 
                             test_cases: List[TestCase],
                             comparison_type: ComparisonType,
                             **llm_kwargs) -> List[TestResult]:
        """顺序执行测试"""
        results = []
        
        iterator = tqdm(test_cases, desc="执行测试") if self.progress_bar else test_cases
        
        for test_case in iterator:
            result = self.run_single_test(test_case, comparison_type, **llm_kwargs)
            results.append(result)
            
            if self.progress_bar and hasattr(iterator, 'set_postfix'):
                iterator.set_postfix({
                    'passed': sum(1 for r in results if r.comparison_result.is_match),
                    'failed': sum(1 for r in results if not r.comparison_result.is_match)
                })
        
        self.test_results.extend(results)
        return results
    
    def _run_parallel_tests(self, 
                           test_cases: List[TestCase],
                           comparison_type: ComparisonType,
                           **llm_kwargs) -> List[TestResult]:
        """并行执行测试"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_test = {
                executor.submit(self.run_single_test, test_case, comparison_type, **llm_kwargs): test_case
                for test_case in test_cases
            }
            
            # 处理完成的任务
            if self.progress_bar:
                futures = tqdm(as_completed(future_to_test), total=len(test_cases), desc="执行测试")
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
                    logger.error(f"测试用例 {test_case.id} 执行异常: {e}")
        
        # 按原始顺序排序结果
        test_case_order = {tc.id: i for i, tc in enumerate(test_cases)}
        results.sort(key=lambda r: test_case_order.get(r.test_case.id, float('inf')))
        
        self.test_results.extend(results)
        return results
    
    def get_summary_statistics(self, results: List[TestResult] = None) -> Dict[str, Any]:
        """获取测试统计信息
        
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
        error_tests = sum(1 for r in results if r.llm_response.error)
        
        execution_times = [r.execution_time for r in results]
        similarity_scores = [r.comparison_result.similarity_score for r in results]
        
        # LLM响应统计
        response_times = [r.llm_response.response_time for r in results if r.llm_response.response_time]
        token_usage = []
        for r in results:
            if r.llm_response.usage and 'total_tokens' in r.llm_response.usage:
                token_usage.append(r.llm_response.usage['total_tokens'])
        
        stats = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0.0,
            'average_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            'min_similarity': min(similarity_scores) if similarity_scores else 0.0,
            'max_similarity': max(similarity_scores) if similarity_scores else 0.0,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'total_execution_time': sum(execution_times)
        }
        
        if response_times:
            stats.update({
                'average_llm_response_time': sum(response_times) / len(response_times),
                'min_llm_response_time': min(response_times),
                'max_llm_response_time': max(response_times)
            })
        
        if token_usage:
            stats.update({
                'total_tokens_used': sum(token_usage),
                'average_tokens_per_test': sum(token_usage) / len(token_usage)
            })
        
        return stats
    
    def export_results(self, 
                      results: List[TestResult] = None,
                      format: str = 'dict') -> Any:
        """导出测试结果
        
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
                'llm_response': asdict(result.llm_response),
                'comparison_result': asdict(result.comparison_result),
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
        logger.info("已清空测试结果")