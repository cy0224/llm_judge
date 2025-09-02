#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON提取器功能
"""

import pytest
import json
from src.llm_judge.utils.json_extractor import JSONExtractor


class TestJSONExtractor:
    """JSON提取器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.extractor = JSONExtractor()
        self.test_json = {
            "name": "小明",
            "age": 19,
            "score": {
                "Chinese": 90,
                "English": 60
            },
            "hobbies": ["reading", "swimming", "coding"]
        }
        self.test_json_str = json.dumps(self.test_json, ensure_ascii=False)
    
    def test_extract_root(self):
        """测试提取根节点"""
        result = self.extractor.extract(self.test_json_str, "$")
        assert result == self.test_json_str
        
        # 测试空字符串默认为根节点
        result = self.extractor.extract(self.test_json_str, "")
        assert result == self.test_json_str
    
    def test_extract_simple_field(self):
        """测试提取简单字段"""
        result = self.extractor.extract(self.test_json_str, "$.name")
        assert result == "小明"
        
        result = self.extractor.extract(self.test_json_str, "$.age")
        assert result == "19"
    
    def test_extract_nested_field(self):
        """测试提取嵌套字段"""
        result = self.extractor.extract(self.test_json_str, "$.score")
        expected = json.dumps({"Chinese": 90, "English": 60}, ensure_ascii=False, separators=(',', ':'))
        assert result == expected
        
        result = self.extractor.extract(self.test_json_str, "$.score.Chinese")
        assert result == "90"
        
        result = self.extractor.extract(self.test_json_str, "$.score.English")
        assert result == "60"
    
    def test_extract_array_element(self):
        """测试提取数组元素"""
        result = self.extractor.extract(self.test_json_str, "$.hobbies")
        expected = json.dumps(["reading", "swimming", "coding"], ensure_ascii=False, separators=(',', ':'))
        assert result == expected
        
        result = self.extractor.extract(self.test_json_str, "$.hobbies[0]")
        assert result == "reading"
        
        result = self.extractor.extract(self.test_json_str, "$.hobbies[2]")
        assert result == "coding"
    
    def test_extract_all_array_elements(self):
        """测试提取所有数组元素"""
        result = self.extractor.extract(self.test_json_str, "$.hobbies[*]")
        expected = json.dumps(["reading", "swimming", "coding"], ensure_ascii=False, separators=(',', ':'))
        assert result == expected
    
    def test_extract_from_markdown(self):
        """测试从Markdown代码块中提取JSON"""
        markdown_content = '''这是一些文本
```json
{"name":"小明","age":19,"score":{"Chinese":90,"English":60}}
```
更多文本'''
        
        result = self.extractor.extract(markdown_content, "$.name")
        assert result == "小明"
        
        result = self.extractor.extract(markdown_content, "$.score.Chinese")
        assert result == "90"
    
    def test_extract_nonexistent_field(self):
        """测试提取不存在的字段"""
        # 默认模式：ignore，返回原始内容
        result = self.extractor.extract(self.test_json_str, "$.nonexistent")
        assert result == self.test_json_str
        
        # error模式：抛出异常
        extractor_error = JSONExtractor(extraction_failure_mode="error")
        with pytest.raises(ValueError):
            extractor_error.extract(self.test_json_str, "$.nonexistent")
        
        # empty模式：返回空字符串
        extractor_empty = JSONExtractor(extraction_failure_mode="empty")
        result = extractor_empty.extract(self.test_json_str, "$.nonexistent")
        assert result == ""
    
    def test_extract_invalid_json(self):
        """测试处理无效JSON"""
        invalid_json = "这不是JSON"
        
        # 默认模式：ignore，返回原始内容
        result = self.extractor.extract(invalid_json, "$.name")
        assert result == invalid_json
        
        # error模式：抛出异常
        extractor_error = JSONExtractor(extraction_failure_mode="error")
        with pytest.raises(ValueError):
            extractor_error.extract(invalid_json, "$.name")
    
    def test_validate_path(self):
        """测试路径验证"""
        # 有效路径
        assert self.extractor.validate_path("$") == True
        assert self.extractor.validate_path("$.name") == True
        assert self.extractor.validate_path("$.score.Chinese") == True
        assert self.extractor.validate_path("$.hobbies[0]") == True
        assert self.extractor.validate_path("$.hobbies[*]") == True
        
        # 无效路径
        assert self.extractor.validate_path("name") == False
        assert self.extractor.validate_path(".name") == False
        assert self.extractor.validate_path("$name") == False
        assert self.extractor.validate_path("$..") == False


if __name__ == "__main__":
    pytest.main([__file__])