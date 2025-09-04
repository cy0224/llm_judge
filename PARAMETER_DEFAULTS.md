# 参数默认值整理文档

本文档整理了项目中所有函数、类和配置文件的参数默认值，便于开发者快速查找和理解各组件的默认配置。

## 命令行参数和默认值

### 全局参数

| 参数名 | 默认值 | 说明 |
|--------|--------|----------|
| --log-level | "INFO" | 日志级别 (DEBUG, INFO, WARNING, ERROR) |
| --output-dir | "output" | 输出目录路径 |
| --parallel | 1 | 并行执行的进程数 |
| --comparison-type | "fuzzy" | 比较类型 (exact, fuzzy, contains, llm) |
| --threshold | 0.8 | 模糊匹配阈值 (0.0-1.0) |

### LLM测试子命令 (llm)

```bash
python main.py llm [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|----------|
| --file | 必需 | 测试数据文件路径 |
| --provider | "openai" | LLM提供商 |
| --model | 配置文件中的默认模型 | 使用的模型名称 |

### HTTP测试子命令 (http)

```bash
python main.py http [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|----------|
| --file | 必需 | 测试数据文件路径 |
| --timeout | 30 | 请求超时时间（秒） |

### 批量测试子命令 (batch)

```bash
python main.py batch [OPTIONS]
```

| 参数名 | 默认值 | 说明 |
|--------|--------|----------|
| --dir | 必需 | 测试数据目录路径 |
| --type | "both" | 测试类型 (llm, http, both) |
| --provider | "openai" | LLM提供商 |
| --model | 配置文件中的默认模型 | 使用的模型名称 |
| --timeout | 30 | HTTP请求超时时间（秒） |

### 使用示例

```bash
# LLM测试
python main.py llm --file data/llm_test.xlsx --provider openai --model gpt-4

# HTTP测试
python main.py http --file data/http_test.xlsx --timeout 60

# 批量测试
python main.py batch --dir data/ --type both --parallel 4

# 自定义输出目录和日志级别
python main.py --log-level DEBUG --output-dir results llm --file data/test.xlsx
```

## 参数优先级规则

项目统一遵循以下参数优先级链：

1. **启动参数**（最高优先级）- 命令行或函数调用时直接传入的参数
2. **配置文件** - `config.yaml` 中定义的默认值
3. **代码默认值**（最低优先级）- 代码中硬编码的兜底值

## 主要函数参数默认值

### 1. setup_logging 函数

**文件位置**: `main.py`

| 参数名 | 函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|------------|--------------|------------|---------|
| log_level | "INFO" | logging.level | "INFO" | 日志级别 |

### 2. run_llm_test 函数

**文件位置**: `main.py`

| 参数名 | 函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|------------|--------------|------------|---------|
| excel_file | - | - | 必填参数 | Excel测试数据文件路径 |
| provider | "openai" | - | "openai" | LLM提供商 |
| model | None | llm.openai.default_model | "ep-20250214150754-5ndjk" | 模型名称 |
| output_dir | "output" | - | "output" | 输出目录 |
| parallel | 1 | - | 1 | 并行数量 |
| comparison_type | "fuzzy" | - | "fuzzy" | 比较类型 |
| threshold | 0.8 | - | 0.8 | 相似度阈值 |

### 3. run_http_test 函数

**文件位置**: `main.py`

| 参数名 | 函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|------------|--------------|------------|---------|
| excel_file | - | - | 必填参数 | Excel测试数据文件路径 |
| output_dir | None | test.output_dir | "output" | 输出目录 |
| parallel | None | test.parallel.max_workers | 1 | 并行数量 |
| comparison_type | None | test.comparison.default_type | "fuzzy" | 比较类型 |
| threshold | None | - | 0.8 | 相似度阈值 |
| timeout | None | http.timeout | 30 | 请求超时时间 |

### 4. run_batch_tests 函数

**文件位置**: `main.py`

| 参数名 | 函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|------------|--------------|------------|---------|
| data_dir | - | - | 必填参数 | 测试数据目录 |
| test_type | None | - | "both" | 测试类型 (llm/http/both) |
| output_dir | None | test.output_dir | "output" | 输出目录 |
| **kwargs | - | - | - | 其他参数 |

### 5. main 函数 - 命令行参数默认值

**文件位置**: `main.py`

#### 全局参数

| 参数名 | 命令行默认值 | 说明 |
|--------|--------------|------|
| --log-level | 'INFO' | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| --output-dir | 'output' | 输出目录 |
| --parallel | 1 | 并行数量 |
| --comparison-type | 'fuzzy' | 比较类型 (exact/fuzzy/contains/json/llm) |
| --threshold | 0.8 | 相似度阈值 |

#### LLM测试子命令参数

| 参数名 | 命令行默认值 | 说明 |
|--------|--------------|------|
| --file | - | 必填参数，Excel测试数据文件 |
| --provider | 'openai' | LLM提供商 |
| --model | None | 模型名称 |

#### HTTP测试子命令参数

| 参数名 | 命令行默认值 | 说明 |
|--------|--------------|------|
| --file | - | 必填参数，Excel测试数据文件 |
| --timeout | 30 | 请求超时时间 |

#### 批量测试子命令参数

| 参数名 | 命令行默认值 | 说明 |
|--------|--------------|------|
| --dir | - | 必填参数，测试数据目录 |
| --type | 'both' | 测试类型 (llm/http/both) |
| --provider | 'openai' | LLM提供商 (仅LLM测试) |
| --model | None | 模型名称 (仅LLM测试) |
| --timeout | 30 | 请求超时时间 (仅HTTP测试) |

## 核心类参数默认值

### 1. HTTPClient 类

**文件位置**: `src/llm_judge/http_test/http_client.py`

#### 构造函数参数

| 参数名 | 构造函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|----------------|--------------|------------|---------|
| base_url | None | - | None | 基础URL |
| timeout | None | http.timeout | 30 | 请求超时时间 |
| max_retries | None | http.max_retries | 3 | 最大重试次数 |
| retry_backoff_factor | None | http.retry_delay | 0.3 | 重试延迟因子 |
| headers | None | http.headers | {} | 请求头 |
| auth | None | - | None | 认证信息 |
| verify_ssl | None | http.verify_ssl | True | SSL验证 |

#### 默认请求头

| 请求头名称 | 默认值 | 说明 |
|------------|--------|----------|
| User-Agent | 'LLM-Judge-HTTP-Client/1.0' | 用户代理 |
| Accept | 'application/json, text/plain, */*' | 接受的内容类型 |
| Content-Type | 'application/json' | 内容类型 |

#### request 方法参数

| 参数名 | 方法默认值 | 说明 |
|--------|------------|----------|
| method | - | 必填参数，HTTP方法 |
| endpoint | - | 必填参数，请求端点 |
| data | None | 请求数据 |
| params | None | URL参数 |
| headers | None | 请求头 |
| timeout | None | 超时时间（使用实例timeout） |
| **kwargs | - | 其他requests参数 |

### 2. LLMClient 相关类

**文件位置**: `src/llm_judge/llm_test/llm_client.py`

#### BaseLLMClient

| 参数名 | 构造函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|----------------|--------------|------------|---------|
| api_key | - | 环境变量 | 必填参数 | API密钥 |
| model | - | - | 必填参数 | 模型名称 |
| timeout | 30 | - | 30 | 超时时间 |
| max_retries | 3 | - | 3 | 最大重试次数 |
| retry_delay | 1.0 | - | 1.0 | 重试延迟时间 |

#### OpenAIClient

| 参数名 | 构造函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|----------------|--------------|------------|---------|
| api_key | - | llm.openai.api_key | 必填参数 | API密钥 |
| model | "gpt-3.5-turbo" | llm.openai.default_model | "ep-20250214150754-5ndjk" | 模型名称 |
| temperature | 0.7 | llm.openai.temperature | 0.1 | 温度参数 |
| max_tokens | 1000 | llm.openai.max_tokens | 1000 | 最大token数 |
| base_url | None | llm.openai.base_url | 环境变量 | 基础URL |
| **kwargs | - | - | - | 其他参数 |

### 3. LLMTester 类

**文件位置**: `src/llm_judge/llm_test/llm_tester.py`

| 参数名 | 构造函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|----------------|--------------|------------|---------|
| llm_client | - | - | 必填参数 | LLM客户端实例 |
| comparator | None | - | BatchComparator() | 比较器实例 |
| max_workers | 5 | - | 5 | 最大工作线程数 |
| progress_bar | True | - | True | 是否显示进度条 |

### 4. TextComparator 类

**文件位置**: `src/llm_judge/utils/comparator.py`

#### 构造函数参数

| 参数名 | 构造函数默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|----------------|--------------|------------|---------|
| fuzzy_threshold | 0.8 | - | 0.8 | 模糊匹配阈值 |
| ignore_case | True | test.comparison.case_sensitive | False | 忽略大小写 |
| ignore_whitespace | True | test.comparison.ignore_whitespace | True | 忽略空白字符 |
| json_extractor | None | - | JSONExtractor() | JSON提取器实例 |
| llm_client | None | - | None | LLM客户端实例 |

#### create_with_comparison_llm 类方法参数

| 参数名 | 方法默认值 | 配置文件映射 | 最终默认值 | 说明 |
|--------|------------|--------------|------------|---------|
| fuzzy_threshold | None | - | 0.8 | 模糊匹配阈值 |
| ignore_case | True | - | True | 忽略大小写 |
| ignore_whitespace | True | - | True | 忽略空白字符 |
| json_extractor | None | - | JSONExtractor() | JSON提取器实例 |

#### LLM比较专用配置

| 配置项 | 配置文件路径 | 默认值 | 说明 |
|--------|--------------|--------|---------|
| provider | test.comparison.llm.provider | "openai" | LLM提供商 |
| api_key | test.comparison.llm.openai.api_key | 环境变量 | API密钥 |
| model | test.comparison.llm.openai.model | "ep-20250214150754-5ndjk" | 模型名称 |
| temperature | test.comparison.llm.openai.temperature | 0.0 | 温度参数 |
| max_tokens | test.comparison.llm.openai.max_tokens | 500 | 最大token数 |
| base_url | test.comparison.llm.openai.base_url | 环境变量 | 基础URL |
| timeout | test.comparison.llm.openai.timeout | 30 | 超时时间 |
| max_retries | test.comparison.llm.openai.max_retries | 2 | 最大重试次数 |
| retry_delay | test.comparison.llm.openai.retry_delay | 1 | 重试延迟时间 |

## 配置文件结构

### config.yaml 完整配置项

#### 1. LLM配置 (llm)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| llm.openai.api_key | "${OPENAI_API_KEY}" | OpenAI API密钥（环境变量） |
| llm.openai.base_url | "${OPENAI_BASE_URL}" | OpenAI API基础URL（环境变量） |
| llm.openai.default_model | "ep-20250214150754-5ndjk" | 默认模型名称 |
| llm.openai.max_tokens | 1000 | 最大token数 |
| llm.openai.temperature | 0.1 | 温度参数 |
| llm.openai.timeout | 60 | 超时时间（秒） |
| llm.openai.max_retries | 3 | 最大重试次数 |
| llm.openai.retry_delay | 1 | 重试延迟时间（秒） |

#### 2. HTTP测试配置 (http)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| http.timeout | 60 | 请求超时时间（秒） |
| http.max_retries | 3 | 最大重试次数 |
| http.retry_delay | 1 | 重试延迟时间（秒） |
| http.verify_ssl | true | SSL证书验证 |
| http.follow_redirects | true | 跟随重定向 |
| http.headers.User-Agent | "LLM-Judge-Tester/1.0" | 用户代理 |
| http.headers.Accept | "application/json" | 接受的内容类型 |
| http.headers.Content-Type | "application/json" | 内容类型 |

#### 3. 测试配置 (test)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| test.data_dir | "data" | 测试数据目录 |
| test.output_dir | "output" | 输出目录 |
| test.report_formats | ["html", "json", "excel"] | 报告格式列表 |
| test.comparison.default_type | "fuzzy" | 默认比较类型 |
| test.comparison.case_sensitive | false | 大小写敏感 |
| test.comparison.ignore_whitespace | true | 忽略空白字符 |
| test.parallel.max_workers | 4 | 最大工作线程数 |
| test.parallel.chunk_size | 10 | 批处理块大小 |

#### 4. LLM比较专用配置 (test.comparison.llm)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| test.comparison.llm.provider | "openai" | LLM提供商 |
| test.comparison.llm.openai.api_key | "${OPENAI_API_KEY}" | API密钥（环境变量） |
| test.comparison.llm.openai.base_url | "${OPENAI_BASE_URL}" | 基础URL（环境变量） |
| test.comparison.llm.openai.model | "ep-20250214150754-5ndjk" | 比较专用模型 |
| test.comparison.llm.openai.max_tokens | 500 | 最大token数 |
| test.comparison.llm.openai.temperature | 0.0 | 温度参数 |
| test.comparison.llm.openai.timeout | 30 | 超时时间（秒） |
| test.comparison.llm.openai.max_retries | 2 | 最大重试次数 |
| test.comparison.llm.openai.retry_delay | 1 | 重试延迟时间（秒） |

#### 5. Excel配置 (test.excel)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| test.excel.llm_columns.id | "ID" | LLM测试ID列名 |
| test.excel.llm_columns.input | "输入" | 输入列名 |
| test.excel.llm_columns.expected | "期望输出" | 期望输出列名 |
| test.excel.llm_columns.expected_extract_path | "期望提取路径" | 期望提取路径列名 |
| test.excel.llm_columns.actual_extract_path | "实际提取路径" | 实际提取路径列名 |
| test.excel.http_columns.id | "ID" | HTTP测试ID列名 |
| test.excel.http_columns.method | "方法" | HTTP方法列名 |
| test.excel.http_columns.endpoint | "端点" | 端点URL列名 |
| test.excel.http_columns.headers | "请求头" | 请求头列名 |
| test.excel.http_columns.body | "请求体" | 请求体列名 |
| test.excel.http_columns.expected | "期望响应" | 期望响应列名 |
| test.excel.http_columns.expected_status | "期望状态码" | 期望状态码列名 |
| test.excel.http_columns.expected_extract_path | "期望提取路径" | 期望提取路径列名 |
| test.excel.http_columns.actual_extract_path | "实际提取路径" | 实际提取路径列名 |
| test.excel.sheet_names | ["Sheet1", "测试数据", "test_data"] | 工作表名称列表 |

#### 6. 日志配置 (logging)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| logging.level | "INFO" | 日志级别 |
| logging.format | "{time:YYYY-MM-DD HH:mm:ss} \| {level: <8} \| {name}:{function}:{line} - {message}" | 日志格式 |
| logging.file.enabled | true | 启用文件日志 |
| logging.file.path | "logs/test_{time:YYYY-MM-DD}.log" | 日志文件路径 |
| logging.file.rotation | "1 day" | 日志轮转周期 |
| logging.file.retention | "7 days" | 日志保留时间 |
| logging.console.enabled | true | 启用控制台日志 |
| logging.console.colorize | true | 控制台日志着色 |

#### 7. 环境配置 (environment)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| environment.development.debug | true | 开发环境调试模式 |
| environment.development.log_level | "DEBUG" | 开发环境日志级别 |
| environment.production.debug | false | 生产环境调试模式 |
| environment.production.log_level | "INFO" | 生产环境日志级别 |

#### 8. 扩展配置 (extensions)

| 配置路径 | 默认值 | 说明 |
|----------|--------|---------|
| extensions.json_extraction.enabled | true | 启用JSON提取功能 |
| extensions.json_extraction.default_extract_path | "$" | 默认提取路径 |
| extensions.json_extraction.extraction_failure_mode | "empty" | 提取失败处理方式 |
| extensions.json_extraction.log_extraction_failures | true | 记录提取失败日志 |

## 环境变量

项目使用以下环境变量：

| 环境变量名 | 用途 | 默认值 |
|------------|------|--------|
| OPENAI_API_KEY | OpenAI API密钥 | 必填 |
| OPENAI_BASE_URL | OpenAI API基础URL | 可选 |

## 参数验证规则

1. **必填参数**: 如果未提供必填参数，程序会抛出异常
2. **类型检查**: 参数类型不匹配时会进行自动转换或抛出异常
3. **范围验证**: 某些参数（如threshold）有有效范围限制
4. **环境变量回退**: API密钥等敏感信息优先从环境变量读取

## 使用建议

1. **配置文件优先**: 建议在 `config.yaml` 中设置项目级别的默认值
2. **环境变量隔离**: 敏感信息（如API密钥）使用环境变量
3. **参数覆盖**: 在特殊情况下通过函数参数覆盖默认配置
4. **日志监控**: 启用参数配置日志，便于调试和监控

---

*最后更新时间: 2025-01-15*
*文档版本: 1.0*