#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON提取功能的集成测试
"""

import pytest
import json
from src.llm_judge.utils.comparator import TextComparator, ComparisonType
from src.llm_judge.utils.json_extractor import JSONExtractor


class TestJSONExtractionIntegration:
    """JSON提取功能集成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.comparator = TextComparator()
        self.test_json_expected = {
            "name": "小明",
            "age": 19,
            "score": {
                "Chinese": 90,
                "English": 60
            }
        }
        self.test_json_actual = {
            "name": "小明",
            "age": 19,
            "score": {
                "Chinese": 90,
                "English": 60
            }
        }
        
        self.expected_str = json.dumps(self.test_json_expected, ensure_ascii=False)
        self.actual_str = json.dumps(self.test_json_actual, ensure_ascii=False)
    
    def test_exact_match_with_extraction(self):
        """测试带提取的精确匹配"""
        # 提取name字段进行比较
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=self.actual_str,
            comparison_type=ComparisonType.EXACT,
            expected_extract_path="$.name",
            actual_extract_path="$.name"
        )
        
        assert result.is_match == True
        assert result.similarity_score == 1.0
        assert result.details['extracted_expected'] == "小明"
        assert result.details['extracted_actual'] == "小明"
    
    def test_json_match_with_extraction(self):
        """测试带提取的JSON匹配"""
        # 提取score对象进行比较
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=self.actual_str,
            comparison_type=ComparisonType.JSON,
            expected_extract_path="$.score",
            actual_extract_path="$.score"
        )
        
        assert result.is_match == True
        assert result.similarity_score == 1.0
    
    def test_mismatch_with_extraction(self):
        """测试提取后不匹配的情况"""
        # 修改actual数据中的分数
        modified_actual = {
            "name": "小明",
            "age": 19,
            "score": {
                "Chinese": 85,  # 不同的分数
                "English": 60
            }
        }
        modified_actual_str = json.dumps(modified_actual, ensure_ascii=False)
        
        # 提取Chinese分数进行比较
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=modified_actual_str,
            comparison_type=ComparisonType.EXACT,
            expected_extract_path="$.score.Chinese",
            actual_extract_path="$.score.Chinese"
        )
        
        assert result.is_match == False
        assert result.details['extracted_expected'] == "90"
        assert result.details['extracted_actual'] == "85"
    
    def test_extraction_from_markdown(self):
        """测试从Markdown代码块中提取并比较"""
        markdown_expected = '''这是期望结果：
```json
{"name":"小明","age":19,"score":{"Chinese":90,"English":60}}
```
'''
        
        markdown_actual = '''这是实际结果：
```json
{"name":"小明","age":19,"score":{"Chinese":90,"English":60}}
```
'''
        
        # 提取name字段进行比较
        result = self.comparator.compare(
            expected=markdown_expected,
            actual=markdown_actual,
            comparison_type=ComparisonType.EXACT,
            expected_extract_path="$.name",
            actual_extract_path="$.name"
        )
        
        assert result.is_match == True
        assert result.similarity_score == 1.0
    
    def test_extraction_failure_handling(self):
        """测试提取失败的处理"""
        # 使用不存在的路径
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=self.actual_str,
            comparison_type=ComparisonType.EXACT,
            expected_extract_path="$.nonexistent",
            actual_extract_path="$.nonexistent"
        )
        
        # 默认情况下应该回退到原始内容比较
        assert result.is_match == True  # 因为原始JSON相同
    
    def test_asymmetric_extraction(self):
        """测试不对称提取（期望和实际使用不同的提取路径）"""
        # 期望提取整个score对象，实际只提取Chinese分数
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=self.actual_str,
            comparison_type=ComparisonType.EXACT,
            expected_extract_path="$.score",
            actual_extract_path="$.score.Chinese"
        )
        
        # 应该不匹配，因为一个是对象，一个是数字
        assert result.is_match == False
    
    def test_no_extraction_paths(self):
        """测试不提供提取路径的情况"""
        result = self.comparator.compare(
            expected=self.expected_str,
            actual=self.actual_str,
            comparison_type=ComparisonType.JSON
        )
        
        # 应该直接比较原始JSON
        assert result.is_match == True
        assert result.similarity_score == 1.0


if __name__ == "__main__":
    pytest.main([__file__])