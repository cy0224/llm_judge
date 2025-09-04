# LLM Judge - LLM和HTTP响应测试框架

一个用于测试LLM生成结果和HTTP接口响应是否符合预期的Python测试框架。

## 功能特性

- 🤖 **LLM测试**: 支持OpenAI等主流LLM提供商
- 🌐 **HTTP测试**: 支持各种HTTP方法和接口测试
- 📊 **Excel数据源**: 使用Excel文件管理测试用例
- 📈 **多种比较方式**: 精确匹配、模糊匹配、包含匹配、JSON匹配、LLM语义匹配
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
export OPENAI_BASE_URL="base-url"
```

### 3. 命令行使用

#### 全局参数

| 参数名 | 默认值 | 说明 |
|--------|--------|---------|
| --log-level | "INFO" | 日志级别 (DEBUG, INFO, WARNING, ERROR) |
| --output-dir | "output" | 输出目录路径 |
| --parallel | 1 | 并行执行的进程数 |
| --comparison-type | "fuzzy" | 比较类型 (exact, fuzzy, contains, json, llm) |
| --threshold | 0.8 | 模糊匹配阈值 (0.0-1.0) |

#### LLM测试

```bash
python main.py llm [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|---------|
| --file | 必需 | 测试数据文件路径 |
| --provider | "openai" | LLM提供商 |
| --model | 配置文件中的默认模型 | 使用的模型名称 |

**使用示例：**
```bash
# 基础LLM测试
python main.py llm --file data/llm_test_example.xlsx

# 指定模型和提供商
python main.py llm --file data/llm_test_example.xlsx --provider openai --model gpt-4

# 使用LLM语义比较（推荐用于语义相似性评估）
python main.py --comparison-type llm --threshold 0.8 llm --file data/llm_test_example.xlsx
```

#### HTTP测试

```bash
python main.py http [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|---------|
| --file | 必需 | 测试数据文件路径 |
| --timeout | 30 | 请求超时时间（秒） |

**使用示例：**
```bash
# 基础HTTP测试
python main.py http --file data/http_test_example.xlsx

# 自定义超时时间
python main.py http --file data/http_test_example.xlsx --timeout 60
```

#### 批量测试

```bash
python main.py batch [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|---------|
| --dir | 必需 | 测试数据目录路径 |
| --type | "both" | 测试类型 (llm, http, both) |
| --provider | "openai" | LLM提供商 |
| --model | 配置文件中的默认模型 | 使用的模型名称 |
| --timeout | 30 | HTTP请求超时时间（秒） |

**使用示例：**
```bash
# 批量运行所有测试
python main.py batch --dir data/ --type both --parallel 4

# 只运行LLM测试
python main.py batch --dir data/ --type llm --provider openai --model gpt-4

# 自定义输出目录和日志级别
python main.py --log-level DEBUG --output-dir results batch --dir data/
```

## 测试数据格式

### LLM测试Excel格式

| ID | 输入 | 期望输出 | 期望提取路径 | 实际提取路径 |
|---|---|---|---|---|
| llm_001 | 请用一句话总结人工智能的定义 | 人工智能是让机器模拟人类智能行为的技术 | `$` | `$` |
| llm_002 | 解释什么是机器学习 | 机器学习是让计算机通过数据自动学习和改进的方法 | `$` | `$` |
| llm_003 | 生成用户信息JSON | {"name": "张三"} | `$.name` | `$.name` |

**提取路径说明**:
- `$`: 使用完整内容进行比较
- `$.name`: 从LLM响应中提取JSON内容中的name字段

### HTTP测试Excel格式

| ID | 方法 | 端点 | 请求头 | 请求体 | 期望响应 | 期望状态码 | 期望提取路径 | 实际提取路径 |
|---|---|---|---|---|---|---|---|---|
| http_001 | GET | https://api.example.com/users | {"Accept": "application/json"} | | {"data":[{"name":"张三"}]} | 200 | `$.data[0].name` | `$.data[0].name` |
| http_002 | POST | https://api.example.com/users | {"Content-Type": "application/json"} | {"name": "test"} | {"id":123,"status":"success"} | 201 | `$.id` | `$.id` |

**HTTP提取路径示例**:
- `$.data[0].name`: 提取响应JSON中第一个数据项的name字段
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
    extraction_failure_mode: "empty"  # ignore, empty, strict
    log_extraction_failures: true
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
- **empty模式**: 提取失败时返回空字符串进行比较（推荐）
- **strict模式**: 提取失败时测试标记为失败

详细使用说明请参考 [JSON_EXTRACTION_USAGE.md](JSON_EXTRACTION_USAGE.md)

## 比较方式说明

### 1. 精确匹配 (exact)
- **功能**: 进行完全一致的文本匹配
- **适用场景**: 需要严格一致性验证的场合
- **示例**: `python main.py --comparison-type exact`

### 2. 模糊匹配 (fuzzy)
- **功能**: 基于相似度的文本匹配，使用多种算法计算文本相似度
- **阈值**: 默认0.8，可通过`--threshold`参数调整
- **适用场景**: 允许一定差异的文本比较
- **示例**: `python main.py --comparison-type fuzzy --threshold 0.8`

### 3. 包含匹配 (contains)
- **功能**: 检查期望文本是否包含在实际文本中
- **适用场景**: 验证关键信息是否出现在输出中
- **示例**: `python main.py --comparison-type contains`

### 4. JSON结构匹配 (json)
- **功能**: 比较JSON数据结构的一致性
- **特性**: 支持从Markdown代码块中提取JSON内容
- **适用场景**: API响应、配置文件等结构化数据的验证
- **示例**: `python main.py --comparison-type json`

### 5. LLM语义匹配 (llm) 🆕
- **功能**: 使用大语言模型进行语义相似度评估
- **特性**: 
  - 理解文本的语义含义，而非仅仅字面匹配
  - 提供详细的评估理由和分数
  - 支持0-100分的细粒度评分
- **评估标准**:
  - 90-100分：语义完全一致或高度相似
  - 70-89分：语义基本一致，有轻微差异
  - 50-69分：语义部分相似，有明显差异
  - 30-49分：语义有一定关联，但差异较大
  - 0-29分：语义不相关或完全不同
- **适用场景**: 
  - 自然语言生成结果的语义评估
  - 翻译质量评估
  - 文本摘要准确性验证
  - 问答系统回答质量评估
- **示例**: `python main.py --comparison-type llm --threshold 0.8`
- **注意**: 需要配置LLM API密钥，会产生API调用费用

## 报告格式

测试完成后会在 `output/` 目录生成以下报告：

- **HTML报告**: 可视化的测试结果，包含详细的对比信息
  - LLM测试：显示输入、期望输出、实际输出、比较结果、LLM推理过程和比较阈值
  - HTTP测试：显示请求信息、响应内容、比较结果，当使用LLM比较时也会显示推理过程和阈值
- **JSON报告**: 机器可读的结构化数据
- **Excel报告**: 表格形式的测试结果，包含所有测试详情和比较信息（需要安装pandas和openpyxl）

## 高级配置

## 高级示例

### 1. 复杂LLM测试配置

```bash
python main.py \
  --parallel 2 \
  --comparison-type fuzzy \
  --threshold 0.8 \
  --output-dir custom_results/ \
  llm \
  --file data/llm_test_example.xlsx \
  --provider openai \
  --model gpt-4
```

### 2. 高并发HTTP接口测试

```bash
python main.py \
  --parallel 4 \
  --comparison-type contains \
  --log-level DEBUG \
  http \
  --file data/http_test_example.xlsx \
  --timeout 60
```

### 3. 生产环境批量测试

```bash
python main.py \
  --parallel 8 \
  --output-dir production_results/ \
  --comparison-type llm \
  --threshold 0.85 \
  batch \
  --dir data/ \
  --type both \
  --provider openai \
  --model gpt-4 \
  --timeout 120
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

### v1.2.1
- 🐛 修复TextComparator类未正确读取配置文件中extraction_failure_mode参数的问题
- 🔧 修正配置路径错误，确保extensions.json_extraction.extraction_failure_mode配置正确生效
- 📚 更新文档，修正JSON提取配置说明中的路径和选项错误
- ✅ 验证empty模式在提取失败时正确返回空字符串

### v1.2.0
- 🔧 修复HTTP测试中LLM比较功能的配置问题
- 📊 增强HTTP报告功能，支持显示LLM比较的阈值和推理过程
- 📋 统一LLM和HTTP报告格式，提供一致的信息展示
- 🐛 修复HTTP测试在使用LLM比较类型时的"LLM客户端未配置"错误
- 📚 更新文档，完善报告格式说明

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