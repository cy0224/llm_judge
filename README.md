# LLM Judge - LLM和HTTP响应测试框架

一个用于测试LLM生成结果和HTTP接口响应是否符合预期的Python测试框架。

## 功能特性

- 🤖 **LLM测试**: 支持OpenAI等主流LLM提供商
- 🌐 **HTTP测试**: 支持各种HTTP方法和接口测试
- 📊 **Excel数据源**: 使用Excel文件管理测试用例
- 📈 **多种比较方式**: 精确匹配、模糊匹配、包含匹配、JSON匹配
- 🔍 **JSON内容提取**: 支持JSONPath表达式提取嵌套JSON内容进行比较
- 📋 **丰富报告**: 生成HTML、JSON、Excel格式的测试报告
- ⚡ **并行执行**: 支持多线程并行测试提高效率
- 🔧 **灵活配置**: 通过YAML配置文件自定义各种参数

## 项目结构

```
llm_judge/
├── src/llm_judge/           # 核心代码
│   ├── config/              # 配置管理
│   ├── llm_test/           # LLM测试模块
│   ├── http_test/          # HTTP测试模块
│   └── utils/              # 工具类
├── data/                   # 测试数据
├── examples/               # 示例文件
├── tests/                  # 单元测试
├── config.yaml            # 配置文件
├── main.py                # 主程序入口
└── requirements.txt       # 依赖包
```

## 快速开始

### 1. 环境准备

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

设置环境变量：

```bash
# OpenAI API密钥
export OPENAI_API_KEY="your-openai-api-key"

```

### 3. 运行测试

#### LLM测试

```bash
# 使用示例数据运行LLM测试
python main.py llm --file data/llm_test_example.xlsx --provider openai --model gpt-3.5-turbo

# 使用不同的比较方式
python main.py --comparison-type fuzzy --threshold 0.8 llm --file data/llm_test_example.xlsx
```

#### HTTP测试

```bash
# 运行HTTP接口测试
python main.py http --file data/http_test_example.xlsx --timeout 30
```

#### 批量测试

```bash
# 批量运行所有测试
python main.py --parallel 4 batch --dir data/ --type both
```

## 测试数据格式

### LLM测试Excel格式

| ID | 输入 | 期望输出 | 期望提取路径 | 实际提取路径 |
|---|---|---|---|---|
| llm_001 | 请用一句话总结人工智能的定义 | 人工智能是让机器模拟人类智能行为的技术 | $ | $ |
| llm_002 | 解释什么是机器学习 | 机器学习是让计算机通过数据自动学习和改进的方法 | $ | $ |
| llm_003 | 生成用户信息JSON | {"name": "张三"} | $.choices[0].message.content.$.name | $.choices[0].message.content.$ |

**提取路径说明**:
- `$`: 使用完整内容进行比较
- `$.choices[0].message.content.$`: 从LLM响应中提取嵌套的JSON内容
- `$.choices[0].message.content.$.name`: 进一步提取JSON中的特定字段

### HTTP测试Excel格式

| ID | 方法 | 端点 | 请求头 | 请求体 | 期望响应 | 期望状态码 | 期望提取路径 | 实际提取路径 |
|---|---|---|---|---|---|---|---|---|
| http_001 | GET | https://api.example.com/users | {"Accept": "application/json"} | | name | 200 | $.data[0].name | $.data[0].name |
| http_002 | POST | https://api.example.com/users | {"Content-Type": "application/json"} | {"name": "test"} | id | 201 | $.id | $.id |

**HTTP提取路径示例**:
- `$.data[0].name`: 提取响应JSON中第一个数据项的name字段
- `$.result.user.email`: 提取嵌套JSON中的用户邮箱
- `$`: 使用完整响应内容进行比较

## 配置说明

主要配置项在 `config.yaml` 文件中：

```yaml
# LLM配置
llm:
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-3.5-turbo"
    max_tokens: 1000
    temperature: 0.1

# 测试配置
test:
  comparison:
    default_type: "fuzzy"  # exact, fuzzy, contains, json
    similarity_threshold: 0.8
  parallel:
    max_workers: 4
  json_extraction:
    enabled: true
    default_expected_path: "$"
    default_actual_path: "$"
    error_handling: "ignore"  # ignore, strict
```

## 比较方式说明

- **exact**: 精确匹配，要求完全一致
- **fuzzy**: 模糊匹配，使用相似度算法
- **contains**: 包含匹配，检查期望内容是否包含在实际结果中
- **json**: JSON匹配，比较JSON结构和内容

## JSON内容提取功能

支持使用JSONPath表达式从复杂的JSON响应中提取特定内容进行比较，特别适用于LLM返回的嵌套JSON结构。

### 基本语法

- `$`: 根节点，使用完整内容
- `$.field`: 提取指定字段
- `$.array[0]`: 提取数组第一个元素
- `$.choices[0].message.content.$`: 嵌套JSON提取，使用`.$`标记进行递归解析

### 嵌套JSON提取

当LLM返回的JSON中包含字符串形式的JSON时，可以使用`.$`进行多层提取：

```json
{
  "choices": [{
    "message": {
      "content": "{\"user\": {\"name\": \"张三\", \"email\": \"test@example.com\"}}"
    }
  }]
}
```

提取路径示例：
- `$.choices[0].message.content.$`: 提取并解析content中的JSON
- `$.choices[0].message.content.$.user.name`: 进一步提取用户姓名
- `$.choices[0].message.content.$.user.email`: 提取用户邮箱

### 错误处理

- **ignore模式**: 提取失败时使用原始内容进行比较
- **strict模式**: 提取失败时测试标记为失败

详细使用说明请参考 [JSON_EXTRACTION_USAGE.md](JSON_EXTRACTION_USAGE.md)

## 报告格式

测试完成后会在 `output/` 目录生成以下报告：

- **HTML报告**: 可视化的测试结果，包含详细的对比信息
- **JSON报告**: 机器可读的结构化数据
- **Excel报告**: 表格形式的测试结果（需要安装pandas和openpyxl）

## 命令行参数

### 全局参数

- `--log-level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `--output-dir`: 输出目录
- `--parallel`: 并行数量
- `--comparison-type`: 比较类型
- `--threshold`: 相似度阈值

### LLM测试参数

- `--file`: Excel测试数据文件
- `--provider`: LLM提供商 (openai)
- `--model`: 模型名称

### HTTP测试参数

- `--file`: Excel测试数据文件
- `--timeout`: 请求超时时间

### 批量测试参数

- `--dir`: 测试数据目录
- `--type`: 测试类型 (llm, http, both)

## 示例用法

### 1. 基础LLM测试

```bash
python main.py \
  --parallel 2 \
  --comparison-type fuzzy \
  --threshold 0.8 \
  llm \
  --file data/llm_test_example.xlsx \
  --provider openai \
  --model gpt-3.5-turbo
```

### 2. HTTP接口测试

```bash
python main.py \
  --parallel 4 \
  --comparison-type contains \
  http \
  --file data/http_test_example.xlsx \
  --timeout 30
```

### 3. 批量测试

```bash
python main.py \
  --parallel 3 \
  --output-dir results/ \
  batch \
  --dir data/ \
  --type both \
  --provider openai \
  --model gpt-4 \
  --timeout 60
```

## 开发指南

### 添加新的LLM提供商

1. 在 `src/llm_judge/llm_test/llm_client.py` 中继承 `BaseLLMClient`
2. 实现 `generate` 方法
3. 在 `LLMClientFactory` 中注册新的提供商

### 添加新的比较方式

1. 在 `src/llm_judge/utils/comparator.py` 中的 `ComparisonType` 枚举添加新类型
2. 在 `TextComparator` 类中实现对应的比较方法

### 自定义报告格式

1. 在 `src/llm_judge/utils/report_generator.py` 中添加新的报告生成方法
2. 在主程序中调用新的报告生成器

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查环境变量是否正确设置
   - 确认API密钥有效且有足够的配额

2. **Excel文件读取失败**
   - 检查文件路径是否正确
   - 确认Excel文件格式符合要求
   - 检查列名是否匹配配置

3. **HTTP请求失败**
   - 检查网络连接
   - 确认API端点URL正确
   - 检查请求头和请求体格式

4. **依赖包安装失败**
   - 确保使用正确的Python版本 (3.12)
   - 激活虚拟环境后再安装依赖

### 调试模式

```bash
# 启用调试日志
python main.py --log-level DEBUG llm --file data/llm_test_example.xlsx
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.1.0
- ✨ 新增JSON内容提取功能，支持JSONPath表达式
- 🔍 支持嵌套JSON提取，使用`.$`语法进行递归解析
- 📊 更新Excel模板，添加提取路径列
- 📋 报告中显示提取后的内容和提取路径
- 🐛 修复批量测试中参数传递错误的问题
- 📚 完善文档和使用示例

### v1.0.0
- 初始版本发布
- 支持OpenAI LLM测试
- 支持HTTP接口测试
- 多种比较方式和报告格式
- 并行执行和配置管理