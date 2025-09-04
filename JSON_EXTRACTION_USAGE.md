# JSON内容提取功能使用指南

## 概述

JSON内容提取功能允许您在LLM和HTTP测试中指定JSONPath表达式，从JSON响应中提取特定部分进行比较，而不是比较整个JSON响应。这大大提高了测试的精确性和灵活性。

## 配置说明

### 1. 全局配置 (config.yaml)

```yaml
extensions:
  json_extraction:
    enabled: true                    # 启用JSON提取功能
    default_extract_path: "$"        # 默认提取路径（根节点）
    extraction_failure_mode: "empty" # 提取失败处理模式
    log_extraction_failures: true    # 是否记录提取失败日志
```

**提取失败处理模式说明：**
- `ignore`: 提取失败时返回原始内容
- `empty`: 提取失败时返回空字符串（推荐）
- `strict`: 提取失败时抛出异常

### 2. Excel列配置

在Excel测试文件中，您可以添加以下列来指定提取路径：

**LLM测试：**
- `期望提取路径`: 指定期望结果的JSON提取路径
- `实际提取路径`: 指定实际结果的JSON提取路径

**HTTP测试：**
- `期望提取路径`: 指定期望响应的JSON提取路径
- `实际提取路径`: 指定实际响应的JSON提取路径

## JSONPath语法支持

### 基本语法

| 表达式 | 说明 | 示例 |
|--------|------|------|
| `$` | 根节点（整个JSON） | 返回完整JSON |
| `$.field` | 提取根级字段 | `$.name` → "小明" |
| `$.field.subfield` | 提取嵌套字段 | `$.score.Chinese` → 90 |
| `$.field[0]` | 提取数组第一个元素 | `$.hobbies[0]` → "reading" |
| `$.field[*]` | 提取数组所有元素 | `$.hobbies[*]` → ["reading", "swimming", "coding"] |

### 嵌套JSON提取语法

| 表达式 | 说明 | 示例 |
|--------|------|------|
| `$.field.$` | 先提取field字段，再从中提取JSON | `$.content.$` → 提取content中的JSON对象 |
| `$.field.$.subfield` | 嵌套提取：先提取field中的JSON，再提取其subfield | `$.content.$.user` → 提取content中JSON的user字段 |
| `$.field.$.sub.$.final` | 多层嵌套提取 | 支持多层嵌套JSON提取 |

### 示例JSON数据

```json
{
  "name": "小明",
  "age": 19,
  "score": {
    "Chinese": 90,
    "English": 60
  },
  "hobbies": ["reading", "swimming", "coding"]
}
```

### 提取示例

- `$` → 完整JSON对象
- `$.name` → "小明"
- `$.age` → "19"
- `$.score` → `{"Chinese":90,"English":60}`
- `$.score.Chinese` → "90"
- `$.hobbies` → `["reading","swimming","coding"]`
- `$.hobbies[0]` → "reading"
- `$.hobbies[2]` → "coding"
- `$.hobbies[*]` → `["reading","swimming","coding"]`

### 嵌套JSON提取示例

假设有以下LLM响应数据：

```json
{
  "choices": [{
    "message": {
      "content": "以下是用户信息：\n\n```json\n{\n  \"user\": {\n    \"name\": \"李四\",\n    \"contact\": {\n      \"email\": \"lisi@example.com\",\n      \"phone\": \"13900139000\"\n    }\n  }\n}\n```"
    }
  }]
}
```

**嵌套提取示例：**

- `$.choices[0].message.content.$` → 提取content中的JSON字符串：
  ```json
  {"user":{"name":"李四","contact":{"email":"lisi@example.com","phone":"13900139000"}}}
  ```

- `$.choices[0].message.content.$.user` → 提取content中JSON的user对象：
  ```json
  {"name":"李四","contact":{"email":"lisi@example.com","phone":"13900139000"}}
  ```

- `$.choices[0].message.content.$.user.name` → 提取用户姓名：
  ```
  "李四"
  ```

- `$.choices[0].message.content.$.user.contact.email` → 提取用户邮箱：
  ```
  "lisi@example.com"
  ```

## Excel使用示例

### LLM测试示例

| ID | 提示词 | 期望响应 | 期望提取路径 | 实际提取路径 | 比较方式 |
|----|--------|----------|--------------|--------------|----------|
| 1 | 请返回学生信息 | `{"name":"小明","score":90}` | `$.name` | `$.name` | exact |
| 2 | 计算总分 | `{"total":150}` | `$.total` | `$.total` | exact |
| 3 | 获取成绩列表 | `{"scores":[90,85,92]}` | `$.scores[0]` | `$.scores[0]` | exact |

### HTTP测试示例

| ID | 方法 | 端点 | 期望响应 | 期望提取路径 | 实际提取路径 | 比较方式 |
|----|------|------|----------|--------------|--------------|----------|
| 1 | GET | /api/user/123 | `{"id":123,"name":"张三"}` | `$.name` | `$.name` | exact |
| 2 | POST | /api/score | `{"success":true,"data":{"total":95}}` | `$.data.total` | `$.data.total` | exact |

### 嵌套JSON提取使用示例

**LLM测试中的嵌套提取：**

| ID | 提示词 | 期望响应 | 期望提取路径 | 实际提取路径 | 比较方式 |
|----|--------|----------|--------------|--------------|----------|
| 1 | 生成用户信息JSON | `{"user":{"name":"张三"}}` | `$.user.name` | `$.choices[0].message.content.$.user.name` | exact |
| 2 | 返回嵌套数据结构 | `"success"` | `$` | `$.choices[0].message.content.$.status` | exact |
| 3 | 提取特定字段 | `{"email":"test@example.com"}` | `$.email` | `$.choices[0].message.content.$.user.contact.email` | contains |

**HTTP测试中的嵌套提取：**

| ID | 方法 | 端点 | 期望响应 | 期望提取路径 | 实际提取路径 | 比较方式 |
|----|------|------|----------|--------------|--------------|----------|
| 1 | GET | /api/llm/chat | `{"name":"AI助手"}` | `$.name` | `$.data.response.$.assistant.name` | exact |
| 2 | POST | /api/generate | `"completed"` | `$` | `$.result.content.$.status` | exact |
| 3 | GET | /api/list | `{"items":[{"id":1},{"id":2}]}` | `$.items[*]` | `$.items[*]` | json |

## Markdown代码块支持

系统自动支持从Markdown代码块中提取JSON：

```markdown
这是LLM的响应：
```json
{
  "name": "小明",
  "score": 90
}
```
更多文本...
```

使用 `$.name` 可以直接提取到 "小明"。

## 实际使用场景

### 1. 精确字段比较

**场景**: LLM返回复杂JSON，但只需要验证特定字段

```
期望: {"result": "success", "data": {"score": 95}, "timestamp": "2024-01-01"}
实际: {"result": "success", "data": {"score": 95}, "timestamp": "2024-01-02"}
提取路径: $.result
结果: 匹配成功（忽略时间戳差异）
```

### 2. 数组元素验证

**场景**: 验证数组中的特定元素

```
期望: {"scores": [90, 85, 92]}
实际: {"scores": [90, 85, 92], "average": 89}
提取路径: $.scores[0]
结果: 验证第一个分数是否为90
```

### 3. 嵌套对象比较

**场景**: 只比较嵌套对象的某个部分

```
期望: {"user": {"profile": {"name": "张三", "age": 25}}}
实际: {"user": {"profile": {"name": "张三", "age": 25}, "settings": {...}}}
提取路径: $.user.profile.name
结果: 只验证用户名，忽略其他字段
```

## 错误处理

### 常见错误及解决方案

1. **路径不存在**
   - 错误: `$.nonexistent`
   - 处理: 根据 `extraction_failure_mode` 配置处理
   - 建议: 使用 `ignore` 模式，回退到原始内容比较

2. **JSON格式错误**
   - 错误: 无法解析的JSON字符串
   - 处理: 自动尝试从Markdown代码块提取
   - 建议: 确保JSON格式正确

3. **数组索引越界**
   - 错误: `$.array[10]` 但数组只有3个元素
   - 处理: 根据失败模式处理
   - 建议: 使用 `$.array[*]` 获取所有元素

## 最佳实践

1. **使用具体路径**: 尽量使用具体的字段路径，避免提取过多不相关数据
2. **统一提取路径**: 期望和实际使用相同的提取路径，除非有特殊需求
3. **测试路径有效性**: 在正式使用前，先验证JSONPath表达式是否正确
4. **合理使用失败模式**: 推荐使用 `ignore` 模式，保证测试的稳定性
5. **记录提取日志**: 启用 `log_extraction_failures` 帮助调试问题
6. **嵌套提取注意事项**:
   - 确保中间步骤提取的内容包含有效的JSON字符串
   - 支持从Markdown代码块中自动提取JSON内容
   - 可以使用多层嵌套（如 `$.field.$.sub.$.final`）
   - 嵌套提取失败时会回退到原始内容比较

## 编程接口使用

如果需要在代码中直接使用JSON提取功能：

```python
from src.llm_judge.utils.json_extractor import JSONExtractor
from src.llm_judge.utils.comparator import TextComparator, ComparisonType

# 创建提取器
extractor = JSONExtractor()

# 提取JSON内容
json_str = '{"name": "小明", "score": 90}'
name = extractor.extract(json_str, "$.name")  # 返回: "小明"

# 在比较器中使用
comparator = TextComparator()
result = comparator.compare(
    expected=expected_json,
    actual=actual_json,
    comparison_type=ComparisonType.EXACT,
    expected_extract_path="$.name",
    actual_extract_path="$.name"
)
```

## 注意事项

1. 提取路径必须以 `$` 开头
2. 字段名区分大小写
3. 数组索引从0开始
4. 提取的复杂对象会被转换为紧凑的JSON字符串
5. 提取失败时的行为取决于配置的失败模式
6. 系统会自动处理Markdown代码块中的JSON内容

通过合理使用JSON内容提取功能，您可以大大提高测试的精确性和维护性，专注于验证真正重要的数据部分。