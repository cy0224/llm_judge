#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试嵌套JSON提取功能
"""

import pytest
import json
from src.llm_judge.utils.json_extractor import JSONExtractor


class TestNestedJSONExtraction:
    """嵌套JSON提取测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.extractor = JSONExtractor()
        
        # 用户提供的测试数据
        self.test_data = {
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "message": {
                    "content": "以下是一个生成的用户信息示例：\n\n```json\n{\n  \"user\": {\n    \"name\": \"李四\",\n    \"contact\": {\n      \"email\": \"lisi@example.com\",\n      \"phone\": \"13900139000\"\n    }\n  }\n}\n```\n\n如果需要更多示例或特定格式，请告诉我！",
                    "role": "assistant"
                }
            }],
            "created": 1756806582,
            "id": "021756806581167530d45f3e18d6c5c13bff8621e54f4f62367c4",
            "model": "deepseek-v3-241226",
            "service_tier": "default",
            "object": "chat.completion",
            "usage": {
                "completion_tokens": 67,
                "prompt_tokens": 39,
                "total_tokens": 106,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 0}
            }
        }
        
        self.test_data_str = json.dumps(self.test_data, ensure_ascii=False)
    
    def test_extract_content_then_json(self):
        """测试提取content内容然后提取其中的JSON字符串"""
        # 测试 $.choices[0].message.content.$
        result = self.extractor.extract(self.test_data_str, "$.choices[0].message.content.$")
        
        # 验证结果是有效的JSON
        parsed_result = json.loads(result)
        assert "user" in parsed_result
        assert parsed_result["user"]["name"] == "李四"
        assert parsed_result["user"]["contact"]["email"] == "lisi@example.com"
    
    def test_extract_nested_user_object(self):
        """测试提取content中JSON字符串的user对象"""
        # 测试 $.choices[0].message.content.$.user
        result = self.extractor.extract(self.test_data_str, "$.choices[0].message.content.$.user")
        
        # 验证结果
        parsed_result = json.loads(result)
        assert parsed_result["name"] == "李四"
        assert parsed_result["contact"]["email"] == "lisi@example.com"
        assert parsed_result["contact"]["phone"] == "13900139000"
    
    def test_extract_nested_user_name(self):
        """测试提取content中JSON字符串的user.name字段"""
        # 测试 $.choices[0].message.content.$.user.name
        result = self.extractor.extract(self.test_data_str, "$.choices[0].message.content.$.user.name")
        
        # 验证结果
        assert result == "李四"
    
    def test_extract_nested_contact_email(self):
        """测试提取content中JSON字符串的user.contact.email字段"""
        # 测试 $.choices[0].message.content.$.user.contact.email
        result = self.extractor.extract(self.test_data_str, "$.choices[0].message.content.$.user.contact.email")
        
        # 验证结果
        assert result == "lisi@example.com"
    
    def test_multiple_nested_extractions(self):
        """测试多层嵌套提取"""
        # 创建一个包含多层嵌套JSON的测试数据
        nested_data = {
            "response": {
                "data": '{"result": {"info": "{\\"final\\": \\"success\\"}"}}'  
            }
        }
        nested_data_str = json.dumps(nested_data, ensure_ascii=False)
        
        # 测试多层嵌套：$.response.data.$.result.info.$.final
        result = self.extractor.extract(nested_data_str, "$.response.data.$.result.info.$.final")
        assert result == "success"
    
    def test_has_nested_extraction_detection(self):
        """测试嵌套提取检测功能"""
        # 测试包含嵌套提取的路径
        assert self.extractor._has_nested_extraction("$.choices[0].message.content.$") == True
        assert self.extractor._has_nested_extraction("$.choices[0].message.content.$.user") == True
        
        # 测试不包含嵌套提取的路径
        assert self.extractor._has_nested_extraction("$.choices[0].message.content") == False
        assert self.extractor._has_nested_extraction("$.user.name") == False
        assert self.extractor._has_nested_extraction("$") == False
    
    def test_extract_json_string_from_text(self):
        """测试从文本中提取JSON字符串的功能"""
        # 测试包含markdown代码块的文本
        markdown_text = "以下是JSON数据：\n\n```json\n{\"name\": \"测试\", \"value\": 123}\n```\n\n请查看。"
        result = self.extractor._extract_json_string_from_text(markdown_text)
        
        parsed_result = json.loads(result)
        assert parsed_result["name"] == "测试"
        assert parsed_result["value"] == 123
    
    def test_nested_extraction_error_handling(self):
        """测试嵌套提取的错误处理"""
        # 测试无效的嵌套路径
        result = self.extractor.extract(self.test_data_str, "$.nonexistent.$.field")
        
        # 应该回退到原始内容（根据默认的ignore模式）
        assert result == self.test_data_str
    
    def test_simple_nested_case(self):
        """测试简单的嵌套情况"""
        # 创建一个简单的测试用例
        simple_data = {
            "message": '{"user": "张三", "age": 25}'
        }
        simple_data_str = json.dumps(simple_data, ensure_ascii=False)
        
        # 测试 $.message.$
        result = self.extractor.extract(simple_data_str, "$.message.$")
        parsed_result = json.loads(result)
        assert parsed_result["user"] == "张三"
        assert parsed_result["age"] == 25
        
        # 测试 $.message.$.user
        result = self.extractor.extract(simple_data_str, "$.message.$.user")
        assert result == "张三"


if __name__ == "__main__":
    pytest.main([__file__])