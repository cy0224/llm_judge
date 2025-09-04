#!/usr/bin/env python3
"""LLM和HTTP测试主脚本"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.llm_judge.config import config
from src.llm_judge.utils import ExcelReader, BatchExcelReader
from src.llm_judge.llm_test import LLMTester, LLMClientFactory
from src.llm_judge.http_test import HTTPTester
from src.llm_judge.utils.report_generator import ReportGenerator
from loguru import logger


def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "test_{time:YYYY-MM-DD}.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days"
    )


def run_llm_test(excel_file: str, 
                 provider: str = "openai",
                 model: str = None,
                 output_dir: str = "output",
                 parallel: int = 1,
                 comparison_type: str = "fuzzy",
                 threshold: float = 0.8) -> bool:
    """运行LLM测试
    
    Args:
        excel_file: Excel测试数据文件路径
        provider: LLM提供商 (openai)
        model: 模型名称
        output_dir: 输出目录
        parallel: 并行数量
        comparison_type: 比较类型
        threshold: 相似度阈值
    
    Returns:
        bool: 测试是否全部通过
    """
    logger.info(f"开始LLM测试: {excel_file}")
    
    try:
        # 创建带时间戳的输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_output_dir = os.path.join(output_dir, f"llm_{timestamp}")
        os.makedirs(timestamped_output_dir, exist_ok=True)
        
        # 读取测试数据
        reader = ExcelReader(excel_file)
        reader.load_data()  # 先加载Excel数据
        test_cases = reader.get_test_cases()
        logger.info(f"加载了 {len(test_cases)} 个测试用例")
        
        # 创建LLM客户端
        api_key = config.get(f'llm.{provider}.api_key')
        if not api_key:
            api_key = os.getenv(f'{provider.upper()}_API_KEY')
        
        if not api_key:
            raise ValueError(f"请设置{provider.upper()}_API_KEY环境变量或在config.yaml中配置api_key")
        
        # 获取base_url配置
        base_url = config.get(f'llm.{provider}.base_url')
        
        llm_client = LLMClientFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=model or config.get(f'llm.{provider}.default_model'),
            temperature=config.get(f'llm.{provider}.temperature', 0.7),
            max_tokens=config.get(f'llm.{provider}.max_tokens', 1000),
            base_url=base_url
        )
        
        # 创建比较器和测试器
        from src.llm_judge.utils.comparator import BatchComparator, ComparisonType, TextComparator
        
        # 将字符串转换为ComparisonType枚举
        comparison_enum = ComparisonType[comparison_type.upper()]
        
        # 创建文本比较器
        if comparison_enum == ComparisonType.LLM:
            # 使用专门的比较LLM配置
            text_comparator = TextComparator.create_with_comparison_llm(
                fuzzy_threshold=threshold
            )
        else:
            # 使用普通比较器
            text_comparator = TextComparator(
                fuzzy_threshold=threshold
            )
        comparator = BatchComparator(comparator=text_comparator)
        
        tester = LLMTester(
            llm_client=llm_client,
            comparator=comparator
        )
        
        # 运行测试
        results = tester.run_batch_tests(
            test_cases=test_cases,
            comparison_type=comparison_enum,
            parallel=parallel > 1
        )
        
        # 计算统计信息
        statistics = {
            'total': len(results),
            'passed': sum(1 for r in results if r.comparison_result.is_match),
            'failed': sum(1 for r in results if not r.comparison_result.is_match),
            'pass_rate': sum(1 for r in results if r.comparison_result.is_match) / len(results) if results else 0
        }
        
        # 生成报告
        report_generator = ReportGenerator(timestamped_output_dir)
        
        # 生成HTML报告
        html_report = report_generator.generate_html_report(
            test_results=results,
            statistics=statistics,
            test_type="LLM",
            title=f"LLM测试报告 - {provider.upper()}"
        )
        
        # 生成JSON报告
        json_report = report_generator.generate_json_report(
            test_results=results,
            statistics=statistics,
            test_type="LLM"
        )
        
        # 尝试生成Excel报告
        try:
            excel_report = report_generator.generate_excel_report(
                test_results=results,
                statistics=statistics,
                test_type="LLM"
            )
            logger.info(f"Excel报告: {excel_report}")
        except ImportError:
            logger.warning("跳过Excel报告生成 (需要pandas和openpyxl)")
        
        # 输出测试结果
        logger.info(f"测试完成! 通过率: {statistics['pass_rate']:.1%}")
        logger.info(f"HTML报告: {html_report}")
        logger.info(f"JSON报告: {json_report}")
        
        return statistics['pass_rate'] >= threshold
        
    except Exception as e:
        logger.error(f"LLM测试失败: {e}")
        return False


def run_http_test(excel_file: str,
                  output_dir: str = None,
                  parallel: int = None,
                  comparison_type: str = None,
                  threshold: float = None,
                  timeout: int = None) -> bool:
    """运行HTTP测试
    
    Args:
        excel_file: Excel测试数据文件路径
        output_dir: 输出目录
        parallel: 并行数量
        comparison_type: 比较类型
        threshold: 相似度阈值
        timeout: 请求超时时间
    
    Returns:
        bool: 测试是否全部通过
    """
    # 参数优先级处理：函数参数 > 配置文件 > 默认值
    output_dir = output_dir or config.get('test.output_dir', 'output')
    parallel = parallel if parallel is not None else config.get('test.parallel.max_workers', 1)
    comparison_type = comparison_type or config.get('test.comparison.default_type', 'fuzzy')
    threshold = threshold if threshold is not None else 0.8
    timeout = timeout if timeout is not None else config.get('http.timeout', 30)
    
    logger.info(f"开始HTTP测试: {excel_file}")
    logger.info(f"参数配置 - output_dir: {output_dir}, parallel: {parallel}, comparison_type: {comparison_type}, threshold: {threshold}, timeout: {timeout}")
    
    try:
        # 创建带时间戳的输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_output_dir = os.path.join(output_dir, f"http_{timestamp}")
        os.makedirs(timestamped_output_dir, exist_ok=True)
        
        # 读取测试数据
        reader = ExcelReader(excel_file)
        reader.load_data()  # 先加载Excel数据
        # 注意：HTTP测试需要不同的列映射
        test_cases = reader.get_http_test_cases()
        logger.info(f"加载了 {len(test_cases)} 个HTTP测试用例")
        
        # 创建HTTP客户端和比较器
        from src.llm_judge.http_test import HTTPClient
        from src.llm_judge.utils.comparator import BatchComparator, ComparisonType, TextComparator
        
        http_client = HTTPClient(timeout=timeout)
        
        # 将字符串转换为ComparisonType枚举
        comparison_enum = ComparisonType[comparison_type.upper()]
        
        # 创建文本比较器
        if comparison_enum == ComparisonType.LLM:
            # 使用专门的比较LLM配置
            text_comparator = TextComparator.create_with_comparison_llm(
                fuzzy_threshold=threshold
            )
        else:
            # 使用普通比较器
            text_comparator = TextComparator(fuzzy_threshold=threshold)
        
        comparator = BatchComparator(comparator=text_comparator)
        
        # 创建测试器
        tester = HTTPTester(
            http_client=http_client,
            comparator=comparator,
            max_workers=parallel
        )
        
        # 运行测试
        results = tester.run_batch_tests(
            test_cases=test_cases,
            comparison_type=comparison_enum
        )
        
        # 计算统计信息
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.comparison_result.is_match)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests) if total_tests > 0 else 0
        
        statistics = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": pass_rate
        }
        
        # 生成报告
        report_generator = ReportGenerator(timestamped_output_dir)
        
        # 生成HTML报告
        html_report = report_generator.generate_html_report(
            test_results=results,
            statistics=statistics,
            test_type="HTTP",
            title="HTTP接口测试报告"
        )
        
        # 生成JSON报告
        json_report = report_generator.generate_json_report(
            test_results=results,
            statistics=statistics,
            test_type="HTTP"
        )
        
        # 尝试生成Excel报告
        try:
            excel_report = report_generator.generate_excel_report(
                test_results=results,
                statistics=statistics,
                test_type="HTTP"
            )
            logger.info(f"Excel报告: {excel_report}")
        except ImportError:
            logger.warning("跳过Excel报告生成 (需要pandas和openpyxl)")
        
        # 输出测试结果
        logger.info(f"测试完成! 通过率: {statistics['pass_rate']:.1%}")
        logger.info(f"HTML报告: {html_report}")
        logger.info(f"JSON报告: {json_report}")
        
        return statistics['pass_rate'] >= threshold
        
    except Exception as e:
        logger.error(f"HTTP测试失败: {e}")
        return False


def run_batch_tests(data_dir: str,
                   test_type: str = None,
                   output_dir: str = None,
                   **kwargs) -> bool:
    """批量运行测试
    
    Args:
        data_dir: 测试数据目录
        test_type: 测试类型 (llm/http/both)
        output_dir: 输出目录
        **kwargs: 其他参数
    
    Returns:
        bool: 所有测试是否通过
    """
    # 参数优先级处理：函数参数 > 配置文件 > 默认值
    test_type = test_type or "both"
    output_dir = output_dir or config.get('test.output_dir', 'output')
    
    logger.info(f"开始批量测试: {data_dir}")
    logger.info(f"参数配置 - test_type: {test_type}, output_dir: {output_dir}")
    
    try:
        batch_reader = BatchExcelReader(data_dir)
        excel_files = batch_reader.find_excel_files()
        
        if not excel_files:
            logger.warning(f"在 {data_dir} 中未找到Excel文件")
            return False
        
        logger.info(f"找到 {len(excel_files)} 个Excel文件")
        
        all_passed = True
        
        for excel_file in excel_files:
            logger.info(f"处理文件: {excel_file}")
            
            # 根据文件名或内容判断测试类型
            file_name = Path(excel_file).stem.lower()
            
            if test_type == "both" or test_type == "llm":
                if "llm" in file_name or (test_type == "llm" and "http" not in file_name and "api" not in file_name):
                    # 过滤LLM测试相关的参数
                    llm_kwargs = {k: v for k, v in kwargs.items() 
                                if k in ['parallel', 'comparison_type', 'threshold', 'provider', 'model']}
                    success = run_llm_test(excel_file, output_dir=output_dir, **llm_kwargs)
                    all_passed = all_passed and success
            
            if test_type == "both" or test_type == "http":
                if "http" in file_name or "api" in file_name or (test_type == "http" and "llm" not in file_name):
                    # 过滤HTTP测试相关的参数
                    http_kwargs = {k: v for k, v in kwargs.items() 
                                 if k in ['parallel', 'comparison_type', 'threshold', 'timeout']}
                    success = run_http_test(excel_file, output_dir=output_dir, **http_kwargs)
                    all_passed = all_passed and success
        
        return all_passed
        
    except Exception as e:
        logger.error(f"批量测试失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LLM和HTTP测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例用法:
  # 运行LLM测试
  python main.py llm --file data/llm_test.xlsx --provider openai --model gpt-3.5-turbo
  
  # 运行HTTP测试
  python main.py http --file data/http_test.xlsx --timeout 30
  
  # 批量运行测试（使用并行）
  python main.py --parallel 4 batch --dir data/ --type both
        """
    )
    
    # 全局参数
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    parser.add_argument('--output-dir', default='output', help='输出目录')
    parser.add_argument('--parallel', type=int, default=1, help='并行数量')
    parser.add_argument('--comparison-type', choices=['exact', 'fuzzy', 'contains', 'json', 'llm'],
                       default='fuzzy', help='比较类型')
    parser.add_argument('--threshold', type=float, default=0.8, help='相似度阈值')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # LLM测试命令
    llm_parser = subparsers.add_parser('llm', help='运行LLM测试')
    llm_parser.add_argument('--file', required=True, help='Excel测试数据文件')
    llm_parser.add_argument('--provider', choices=['openai'], 
                           default='openai', help='LLM提供商')
    llm_parser.add_argument('--model', help='模型名称')
    
    # HTTP测试命令
    http_parser = subparsers.add_parser('http', help='运行HTTP测试')
    http_parser.add_argument('--file', required=True, help='Excel测试数据文件')
    http_parser.add_argument('--timeout', type=int, default=30, help='请求超时时间')
    
    # 批量测试命令
    batch_parser = subparsers.add_parser('batch', help='批量运行测试')
    batch_parser.add_argument('--dir', required=True, help='测试数据目录')
    batch_parser.add_argument('--type', choices=['llm', 'http', 'both'], 
                             default='both', help='测试类型')
    batch_parser.add_argument('--provider', choices=['openai'], 
                             default='openai', help='LLM提供商 (仅LLM测试)')
    batch_parser.add_argument('--model', help='模型名称 (仅LLM测试)')
    batch_parser.add_argument('--timeout', type=int, default=30, help='请求超时时间 (仅HTTP测试)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 创建输出目录
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        success = False
        
        if args.command == 'llm':
            success = run_llm_test(
                excel_file=args.file,
                provider=args.provider,
                model=args.model,
                output_dir=args.output_dir,
                parallel=args.parallel,
                comparison_type=args.comparison_type,
                threshold=args.threshold
            )
        
        elif args.command == 'http':
            success = run_http_test(
                excel_file=args.file,
                output_dir=args.output_dir,
                parallel=args.parallel,
                comparison_type=args.comparison_type,
                threshold=args.threshold,
                timeout=args.timeout
            )
        
        elif args.command == 'batch':
            kwargs = {
                'parallel': args.parallel,
                'comparison_type': args.comparison_type,
                'threshold': args.threshold
            }
            
            if args.type in ['llm', 'both']:
                kwargs.update({
                    'provider': args.provider,
                    'model': args.model
                })
            
            if args.type in ['http', 'both']:
                kwargs['timeout'] = args.timeout
            
            success = run_batch_tests(
                data_dir=args.dir,
                test_type=args.type,
                output_dir=args.output_dir,
                **kwargs
            )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())