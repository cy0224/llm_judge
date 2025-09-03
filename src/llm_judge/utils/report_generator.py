"""测试报告生成器"""

import json
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import asdict
from loguru import logger

try:
    import pandas as pd
except ImportError:
    pd = None


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, 
                           test_results: List[Any],
                           statistics: Dict[str, Any],
                           test_type: str = "LLM",
                           title: str = None) -> str:
        """生成HTML报告
        
        Args:
            test_results: 测试结果列表
            statistics: 统计信息
            test_type: 测试类型 (LLM/HTTP)
            title: 报告标题
        
        Returns:
            str: 生成的HTML文件路径
        """
        if title is None:
            title = f"{test_type}测试报告"
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"{test_type.lower()}_report_{timestamp}.html"
        filepath = self.output_dir / filename
        
        html_content = self._generate_html_content(test_results, statistics, test_type, title)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {filepath}")
        return str(filepath)
    
    def _generate_html_content(self, 
                              test_results: List[Any],
                              statistics: Dict[str, Any],
                              test_type: str,
                              title: str) -> str:
        """生成HTML内容"""
        
        # 统计信息HTML
        stats_html = self._generate_statistics_html(statistics)
        
        # 测试结果HTML
        results_html = self._generate_results_html(test_results, test_type)
        
        # 完整HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 20px;
            border-radius: 4px;
        }}
        .stat-card.success {{
            border-left-color: #28a745;
        }}
        .stat-card.danger {{
            border-left-color: #dc3545;
        }}
        .stat-card.warning {{
            border-left-color: #ffc107;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .results-section {{
            margin-top: 40px;
        }}
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .results-table th,
        .results-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .results-table th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .results-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .status-pass {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-fail {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .status-code-mismatch {{
            color: #dc3545;
            font-weight: bold;
        }}
        .details-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .expandable {{
            cursor: pointer;
        }}
        .expandable:hover {{
            background-color: #e9ecef;
        }}
        .diff-content {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.8em;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }}
        .diff-content .diff-line {{
            display: block;
            margin: 0;
            padding: 2px 4px;
            border-radius: 2px;
        }}
        .diff-content .diff-added {{
            background-color: #d4edda !important;
            color: #155724 !important;
        }}
        .diff-content .diff-removed {{
            background-color: #f8d7da !important;
            color: #721c24 !important;
        }}
        .diff-content .diff-unchanged {{
            background-color: transparent;
        }}
        .content-textarea {{
            width: 100%;
            min-height: 80px;
            max-height: 200px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85em;
            background-color: #f8f9fa;
            resize: vertical;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .content-textarea:focus {{
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
        }}
        .textarea-container {{
            position: relative;
        }}
        .expand-btn {{
            position: absolute;
            top: 5px;
            right: 5px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-size: 0.7em;
            cursor: pointer;
            z-index: 10;
        }}
        .expand-btn:hover {{
            background: #0056b3;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        .modal-content {{
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
            max-height: 80%;
            overflow-y: auto;
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .modal-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}
        .close {{
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        .close:hover,
        .close:focus {{
            color: #000;
            text-decoration: none;
        }}
        .modal-textarea {{
            width: 100%;
            min-height: 400px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            background-color: #f8f9fa;
            resize: vertical;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .error-message {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            color: #721c24;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .detail-section {{
            margin-bottom: 15px;
        }}
        .detail-label {{
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }}
    </style>
    <script>
        function toggleDetails(element) {{
            const content = element.nextElementSibling;
            if (content.style.display === 'none' || content.style.display === '') {{
                content.style.display = 'block';
                element.textContent = element.textContent.replace('▶', '▼');
            }} else {{
                content.style.display = 'none';
                element.textContent = element.textContent.replace('▼', '▶');
            }}
        }}
        
        function openModal(content, title) {{
            const modal = document.getElementById('contentModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalTextarea = document.getElementById('modalTextarea');
            
            modalTitle.textContent = title;
            modalTextarea.value = content;
            modal.style.display = 'block';
        }}
        
        function closeModal() {{
            const modal = document.getElementById('contentModal');
            modal.style.display = 'none';
        }}
        
        // 点击模态框外部关闭
        window.onclick = function(event) {{
            const modal = document.getElementById('contentModal');
            if (event.target == modal) {{
                modal.style.display = 'none';
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div class="content">
            {stats_html}
            {results_html}
        </div>
    </div>
    
    <!-- 模态框 -->
    <div id="contentModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span id="modalTitle" class="modal-title">内容详情</span>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <textarea id="modalTextarea" class="modal-textarea" readonly></textarea>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _generate_statistics_html(self, statistics: Dict[str, Any]) -> str:
        """生成统计信息HTML"""
        if not statistics:
            return "<p>无统计信息</p>"
        
        stats_cards = []
        
        # 基本统计
        if 'total_tests' in statistics:
            stats_cards.append(f"""
            <div class="stat-card">
                <div class="stat-value">{statistics['total_tests']}</div>
                <div class="stat-label">总测试数</div>
            </div>
            """)
        
        if 'passed_tests' in statistics:
            stats_cards.append(f"""
            <div class="stat-card success">
                <div class="stat-value">{statistics['passed_tests']}</div>
                <div class="stat-label">通过测试</div>
            </div>
            """)
        
        if 'failed_tests' in statistics:
            stats_cards.append(f"""
            <div class="stat-card danger">
                <div class="stat-value">{statistics['failed_tests']}</div>
                <div class="stat-label">失败测试</div>
            </div>
            """)
        
        if 'pass_rate' in statistics:
            pass_rate = statistics['pass_rate'] * 100
            card_class = "success" if pass_rate >= 80 else "warning" if pass_rate >= 60 else "danger"
            stats_cards.append(f"""
            <div class="stat-card {card_class}">
                <div class="stat-value">{pass_rate:.1f}%</div>
                <div class="stat-label">通过率</div>
            </div>
            """)
        
        if 'average_similarity' in statistics:
            similarity = statistics['average_similarity'] * 100
            stats_cards.append(f"""
            <div class="stat-card">
                <div class="stat-value">{similarity:.1f}%</div>
                <div class="stat-label">平均相似度</div>
            </div>
            """)
        
        if 'average_execution_time' in statistics:
            avg_time = statistics['average_execution_time']
            stats_cards.append(f"""
            <div class="stat-card">
                <div class="stat-value">{avg_time:.2f}s</div>
                <div class="stat-label">平均执行时间</div>
            </div>
            """)
        
        return f"""
        <h2>测试统计</h2>
        <div class="stats-grid">
            {''.join(stats_cards)}
        </div>
        """
    
    def _generate_results_html(self, test_results: List[Any], test_type: str) -> str:
        """生成测试结果HTML"""
        if not test_results:
            return "<p>无测试结果</p>"
        
        rows = []
        for i, result in enumerate(test_results):
            # 根据测试类型提取不同的信息
            if test_type.upper() == "LLM":
                rows.append(self._generate_llm_result_row(result, i))
            else:
                rows.append(self._generate_http_result_row(result, i))
        
        return f"""
        <div class="results-section">
            <h2>测试结果详情</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>测试ID</th>
                        <th>状态</th>
                        <th>对比类型</th>
                        <th>相似度</th>
                        <th>执行时间</th>
                        <th>详情</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_llm_result_row(self, result: Any, index: int) -> str:
        """生成LLM测试结果行"""
        test_case = result.test_case
        comparison = result.comparison_result
        llm_response = result.llm_response
        
        status_class = "status-pass" if comparison.is_match else "status-fail"
        status_text = "通过" if comparison.is_match else "失败"
        
        similarity_percent = comparison.similarity_score * 100
        
        # 构建详情内容
        details_id = f"details_{index}"
        
        # 检查是否有提取后的内容和提取路径
        extracted_expected = ""
        extracted_actual = ""
        if comparison.details and 'extracted_expected' in comparison.details:
            expected_path = comparison.details.get('expected_extract_path', '$')
            if not expected_path or expected_path == "":
                expected_path = "$"
            extracted_expected = f'<div class="detail-section"><div class="detail-label">提取后的期望输出 (路径: {self._escape_html(expected_path)}):</div>{self._create_textarea_with_modal(str(comparison.details["extracted_expected"]), f"提取后的期望输出 (路径: {expected_path})")}</div>'
        if comparison.details and 'extracted_actual' in comparison.details:
            actual_path = comparison.details.get('actual_extract_path', '$')
            if not actual_path or actual_path == "":
                actual_path = "$"
            extracted_actual = f'<div class="detail-section"><div class="detail-label">提取后的实际输出 (路径: {self._escape_html(actual_path)}):</div>{self._create_textarea_with_modal(str(comparison.details["extracted_actual"]), f"提取后的实际输出 (路径: {actual_path})")}</div>'
        
        # 构建LLM推理过程显示
        reasoning_content = ""
        if comparison.comparison_type.value == "llm" and comparison.details and 'llm_reasoning' in comparison.details:
            reasoning = comparison.details['llm_reasoning']
            if reasoning:
                reasoning_content = f'<div class="detail-section"><div class="detail-label">LLM推理过程:</div>{self._create_textarea_with_modal(reasoning, "LLM推理过程")}</div>'
        
        # 构建错误信息显示
        error_content = ""
        if llm_response.error or comparison.error_message:
            error_msg = llm_response.error or comparison.error_message
            error_content = f'<div class="detail-section"><div class="detail-label">错误信息:</div><div class="error-message">{self._escape_html(error_msg)}</div></div>'
        
        # 构建阈值信息显示（所有比较类型都显示）
        threshold_content = ""
        if comparison.details and 'threshold' in comparison.details:
            threshold = comparison.details['threshold']
            threshold_content = f'<div class="detail-section"><div class="detail-label">比较阈值:</div><p><strong>阈值:</strong> {threshold:.3f}</p></div>'
        
        details_content = f"""
        <div style="display: none;" id="{details_id}">
            <div class="detail-section">
                <div class="detail-label">模型信息:</div>
                <p><strong>模型:</strong> {llm_response.model}</p>
                <p><strong>响应时间:</strong> {llm_response.response_time:.3f}s</p>
            </div>
            {threshold_content}
            <div class="detail-section">
                <div class="detail-label">输入:</div>
                {self._create_textarea_with_modal(test_case.input, "输入内容")}
            </div>
            <div class="detail-section">
                <div class="detail-label">期望输出:</div>
                {self._create_textarea_with_modal(test_case.expected, "期望输出内容")}
            </div>
            <div class="detail-section">
                <div class="detail-label">实际输出:</div>
                {self._create_textarea_with_modal(llm_response.content, "实际输出内容")}
            </div>
            {extracted_expected}
            {extracted_actual}
            {reasoning_content}
            {error_content}
            {f'<div class="detail-section"><div class="detail-label">差异对比:</div><div class="diff-content">{self._format_diff_content(comparison.diff)}</div></div>' if comparison.diff else ''}
        </div>
        """
        
        return f"""
        <tr>
            <td>{index + 1}</td>
            <td>{test_case.id}</td>
            <td><span class="status-badge {status_class}">{status_text}</span></td>
            <td>{comparison.comparison_type.value}</td>
            <td>{similarity_percent:.1f}%</td>
            <td>{result.execution_time:.3f}s</td>
            <td>
                <div class="expandable" onclick="toggleDetails(this)">▶ 查看详情</div>
                {details_content}
            </td>
        </tr>
        """
    
    def _generate_http_result_row(self, result: Any, index: int) -> str:
        """生成HTTP测试结果行"""
        test_case = result.test_case
        comparison = result.comparison_result
        http_response = result.http_response
        
        status_class = "status-pass" if comparison.is_match else "status-fail"
        status_text = "通过" if comparison.is_match else "失败"
        
        similarity_percent = comparison.similarity_score * 100
        
        # 构建详情内容
        details_id = f"details_{index}"
        
        # 检查是否有提取后的内容和提取路径
        extracted_expected = ""
        extracted_actual = ""
        if comparison.details and 'extracted_expected' in comparison.details:
            expected_path = comparison.details.get('expected_extract_path', '$')
            if not expected_path or expected_path == "":
                expected_path = "$"
            extracted_expected = f'<div class="detail-section"><div class="detail-label">提取后的期望响应 (路径: {self._escape_html(expected_path)}):</div>{self._create_textarea_with_modal(str(comparison.details["extracted_expected"]), f"提取后的期望响应 (路径: {expected_path})")}</div>'
        if comparison.details and 'extracted_actual' in comparison.details:
            actual_path = comparison.details.get('actual_extract_path', '$')
            if not actual_path or actual_path == "":
                actual_path = "$"
            extracted_actual = f'<div class="detail-section"><div class="detail-label">提取后的实际响应 (路径: {self._escape_html(actual_path)}):</div>{self._create_textarea_with_modal(str(comparison.details["extracted_actual"]), f"提取后的实际响应 (路径: {actual_path})")}</div>'
        
        # 构建LLM推理过程显示
        reasoning_content = ""
        if comparison.comparison_type.value == "llm" and comparison.details and 'llm_reasoning' in comparison.details:
            reasoning = comparison.details['llm_reasoning']
            if reasoning:
                reasoning_content = f'<div class="detail-section"><div class="detail-label">LLM推理过程:</div>{self._create_textarea_with_modal(reasoning, "LLM推理过程")}</div>'
        
        # 构建错误信息显示
        error_content = ""
        if http_response.error or comparison.error_message:
            error_msg = http_response.error or comparison.error_message
            error_content = f'<div class="detail-section"><div class="detail-label">错误信息:</div><div class="error-message">{self._escape_html(error_msg)}</div></div>'
        
        # 构建阈值信息显示（所有比较类型都显示）
        threshold_content = ""
        if comparison.details and 'threshold' in comparison.details:
            threshold = comparison.details['threshold']
            threshold_content = f'<div class="detail-section"><div class="detail-label">比较阈值:</div><p><strong>阈值:</strong> {threshold:.3f}</p></div>'
        
        # 检查状态码是否匹配
        status_code_match = result.status_code_match if hasattr(result, 'status_code_match') else True
        expected_status = test_case.expected_status_code or 200
        status_code_class = "" if status_code_match else "status-code-mismatch"
        
        details_content = f"""
        <div style="display: none;" id="{details_id}">
            <div class="detail-section">
                <div class="detail-label">请求信息:</div>
                <p><strong>请求:</strong> {test_case.method.upper()} {test_case.endpoint}</p>
                <p><strong>状态码:</strong> <span class="{status_code_class}">{http_response.status_code}</span> (期望: {expected_status})</p>
                <p><strong>响应时间:</strong> {http_response.response_time:.3f}s</p>
            </div>
            {threshold_content}
            <div class="detail-section">
                <div class="detail-label">期望响应:</div>
                {self._create_textarea_with_modal(test_case.expected, "期望响应内容")}
            </div>
            <div class="detail-section">
                <div class="detail-label">实际响应:</div>
                {self._create_textarea_with_modal(http_response.content, "实际响应内容")}
            </div>
            {extracted_expected}
            {extracted_actual}
            {reasoning_content}
            {error_content}
            {f'<div class="detail-section"><div class="detail-label">差异对比:</div><div class="diff-content">{self._format_diff_content(comparison.diff)}</div></div>' if comparison.diff else ''}
        </div>
        """
        
        return f"""
        <tr>
            <td>{index + 1}</td>
            <td>{test_case.id}</td>
            <td><span class="status-badge {status_class}">{status_text}</span></td>
            <td>{comparison.comparison_type.value}</td>
            <td>{similarity_percent:.1f}%</td>
            <td>{result.execution_time:.3f}s</td>
            <td>
                <div class="expandable" onclick="toggleDetails(this)">▶ 查看详情</div>
                {details_content}
            </td>
        </tr>
        """
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))
    
    def _create_textarea_with_modal(self, content: str, title: str, css_class: str = "content-textarea") -> str:
        """创建带有弹窗按钮的文本框"""
        escaped_content = self._escape_html(content)
        escaped_title = self._escape_html(title)
        # 转义JavaScript字符串中的特殊字符
        js_content = (content.replace('\\', '\\\\')
                            .replace("'", "\\'")
                            .replace('"', '\\"')
                            .replace('\n', '\\n')
                            .replace('\r', '\\r')
                            .replace('\t', '\\t'))
        js_title = (title.replace('\\', '\\\\')
                         .replace("'", "\\'")
                         .replace('"', '\\"')
                         .replace('\n', '\\n')
                         .replace('\r', '\\r')
                         .replace('\t', '\\t'))
        
        return f'''
        <div class="textarea-container">
            <textarea class="{css_class}" readonly>{escaped_content}</textarea>
            <button class="expand-btn" onclick='openModal("{js_content}", "{js_title}")'>展开</button>
        </div>
        '''
    
    def _format_diff_content(self, diff_text: str) -> str:
        """格式化差异内容，为不同类型的行添加背景色"""
        if not diff_text:
            return ""
        
        lines = diff_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            escaped_line = self._escape_html(line)
            # 跳过diff头部信息（文件名和位置信息）
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                formatted_lines.append(f'<span class="diff-line diff-unchanged">{escaped_line}</span>')
            elif line.startswith('+'):
                formatted_lines.append(f'<span class="diff-line diff-added">{escaped_line}</span>')
            elif line.startswith('-'):
                formatted_lines.append(f'<span class="diff-line diff-removed">{escaped_line}</span>')
            else:
                formatted_lines.append(f'<span class="diff-line diff-unchanged">{escaped_line}</span>')
        
        return '\n'.join(formatted_lines)
    
    def generate_json_report(self, 
                           test_results: List[Any],
                           statistics: Dict[str, Any],
                           test_type: str = "LLM") -> str:
        """生成JSON报告
        
        Args:
            test_results: 测试结果列表
            statistics: 统计信息
            test_type: 测试类型
        
        Returns:
            str: 生成的JSON文件路径
        """
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"{test_type.lower()}_report_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # 转换测试结果为字典格式
        results_data = []
        for result in test_results:
            if hasattr(result, '__dict__'):
                result_dict = asdict(result)
            else:
                result_dict = result
            results_data.append(result_dict)
        
        report_data = {
            'metadata': {
                'test_type': test_type,
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_results': len(test_results)
            },
            'statistics': statistics,
            'results': results_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"JSON报告已生成: {filepath}")
        return str(filepath)
    
    def generate_excel_report(self, 
                            test_results: List[Any],
                            statistics: Dict[str, Any],
                            test_type: str = "LLM") -> str:
        """生成Excel报告
        
        Args:
            test_results: 测试结果列表
            statistics: 统计信息
            test_type: 测试类型
        
        Returns:
            str: 生成的Excel文件路径
        """
        if pd is None:
            raise ImportError("请安装pandas库: pip install pandas openpyxl")
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"{test_type.lower()}_report_{timestamp}.xlsx"
        filepath = self.output_dir / filename
        
        # 准备数据
        data_rows = []
        for result in test_results:
            if test_type.upper() == "LLM":
                # 获取提取后的内容和提取路径
                extracted_expected = ""
                extracted_actual = ""
                expected_extract_path = ""
                actual_extract_path = ""
                if result.comparison_result.details:
                    extracted_expected = str(result.comparison_result.details.get('extracted_expected', ''))
                    extracted_actual = str(result.comparison_result.details.get('extracted_actual', ''))
                    expected_extract_path = str(result.comparison_result.details.get('expected_extract_path', '$'))
                    actual_extract_path = str(result.comparison_result.details.get('actual_extract_path', '$'))
                
                # 获取阈值信息（所有比较类型）
                threshold = ""
                if result.comparison_result.details:
                    threshold = str(result.comparison_result.details.get('threshold', ''))
                
                # 获取推理信息（仅LLM类型）
                reasoning = ""
                if result.comparison_result.comparison_type.value == "llm" and result.comparison_result.details:
                    reasoning = str(result.comparison_result.details.get('llm_reasoning', ''))
                
                row = {
                    '测试ID': result.test_case.id,
                    '输入': result.test_case.input,
                    '期望输出': result.test_case.expected,
                    '实际输出': result.llm_response.content,
                    '提取后的期望输出': extracted_expected,
                    '提取后的实际输出': extracted_actual,
                    '期望提取路径': expected_extract_path,
                    '实际提取路径': actual_extract_path,
                    '模型': result.llm_response.model,
                    '对比类型': result.comparison_result.comparison_type.value,
                    '是否匹配': '是' if result.comparison_result.is_match else '否',
                    '相似度': f"{result.comparison_result.similarity_score:.3f}",
                    '比较阈值': threshold,
                    'LLM推理过程': reasoning,
                    '执行时间(s)': f"{result.execution_time:.3f}",
                    'LLM响应时间(s)': f"{result.llm_response.response_time:.3f}" if result.llm_response.response_time else '',
                    '错误信息': result.llm_response.error or result.comparison_result.error_message or '',
                    '时间戳': result.timestamp
                }
            else:  # HTTP
                # 获取提取后的内容和提取路径
                extracted_expected = ""
                extracted_actual = ""
                expected_extract_path = ""
                actual_extract_path = ""
                if result.comparison_result.details:
                    extracted_expected = str(result.comparison_result.details.get('extracted_expected', ''))
                    extracted_actual = str(result.comparison_result.details.get('extracted_actual', ''))
                    expected_extract_path = str(result.comparison_result.details.get('expected_extract_path', '$'))
                    actual_extract_path = str(result.comparison_result.details.get('actual_extract_path', '$'))
                
                # 获取阈值信息（所有比较类型）
                threshold = ""
                if result.comparison_result.details:
                    threshold = str(result.comparison_result.details.get('threshold', ''))
                
                # 获取推理信息（仅LLM类型）
                reasoning = ""
                if result.comparison_result.comparison_type.value == "llm" and result.comparison_result.details:
                    reasoning = str(result.comparison_result.details.get('llm_reasoning', ''))
                
                row = {
                    '测试ID': result.test_case.id,
                    '请求方法': result.test_case.method,
                    '端点': result.test_case.endpoint,
                    '期望响应': result.test_case.expected,
                    '实际响应': result.http_response.content,
                    '提取后的期望响应': extracted_expected,
                    '提取后的实际响应': extracted_actual,
                    '期望提取路径': expected_extract_path,
                    '实际提取路径': actual_extract_path,
                    '状态码': result.http_response.status_code,
                    '期望状态码': result.test_case.expected_status_code or 200,
                    '状态码匹配': '是' if result.status_code_match else '否',
                    '对比类型': result.comparison_result.comparison_type.value,
                    '内容匹配': '是' if result.comparison_result.is_match else '否',
                    '相似度': f"{result.comparison_result.similarity_score:.3f}",
                    '比较阈值': threshold,
                    'LLM推理过程': reasoning,
                    '执行时间(s)': f"{result.execution_time:.3f}",
                    '响应时间(s)': f"{result.http_response.response_time:.3f}",
                    '错误信息': result.http_response.error or result.comparison_result.error_message or '',
                    '时间戳': result.timestamp
                }
            data_rows.append(row)
        
        # 创建DataFrame
        df_results = pd.DataFrame(data_rows)
        df_stats = pd.DataFrame([statistics])
        
        # 写入Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name='测试结果', index=False)
            df_stats.to_excel(writer, sheet_name='统计信息', index=False)
        
        logger.info(f"Excel报告已生成: {filepath}")
        return str(filepath)