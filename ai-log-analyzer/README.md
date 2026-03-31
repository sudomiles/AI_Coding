# AI Log Analyzer - 基于 Harness Engineering 的网络安全日志分析系统

## 项目概述

本项目是一个基于 **Harness Engineering** 思路构建的网络安全日志分析工具，旨在协助安全运维人员快速分析网络设备日志，定位硬件故障和安全问题。

**特点：**
- ✅ **本地独立运行**：无需依赖特定环境，支持本地运行
- ✅ **多 LLM 支持**：支持 OpenAI、DeepSeek、Qwen 等 API
- ✅ **流式输出**：实时展示分析进度
- ✅ **测试驱动**：完整的测试用例和评估体系

## 什么是 Harness Engineering?

Harness Engineering 是一种**测试驱动开发与评估迭代**的软件工程方法论，特别适用于 AI 应用开发。其核心思想是：

### 核心理念

```
Prompts (提示词) → Test Cases (测试用例) → Evaluator (评估器) → Iteration (迭代优化)
```

### 四大核心要素

#### 1. **Prompts（提示词工程）**
- 结构化的提示词模板，定义 AI 的角色和任务
- 包含上下文信息、任务描述、输出格式要求
- 可版本化、可迭代优化

#### 2. **Test Cases（测试用例库）**
- 覆盖典型场景的测试数据集
- 包含输入数据和预期输出
- 用于验证系统功能的完整性和准确性

#### 3. **Evaluator（评估器）**
- 自动化评估 AI 输出质量的工具
- 基于规则和语义相似度的双重评估
- 提供量化指标指导优化方向

#### 4. **Results（结果追踪）**
- 记录每次运行的输入、输出和评估结果
- 支持版本对比和回归测试
- 形成优化的闭环反馈

## 项目结构

```
ai-log-analyzer/
├── README.md                    # 项目文档
├── AGENTS.md                    # 开发指南
├── main.py                     # 主程序入口
├── config.example.yaml         # 配置文件模板
├── requirements.txt            # 依赖包列表
├── prompts/
│   └── analyze_log.txt         # 日志分析提示词模板
├── test_cases/
│   └── logs.json               # 测试用例数据集
├── evaluator/
│   └── evaluator.py            # 评估器实现
└── results/
    └── output.json             # 分析结果输出
```

## 快速开始

### 1. 安装依赖

```bash
# 最小安装（仅核心功能）
pip install openai

# 完整安装（包含配置文件支持）
pip install -r requirements.txt
```

### 2. 配置 API

#### 方式一：环境变量（推荐）

**使用 OpenAI:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export LLM_MODEL="gpt-4o-mini"  # 可选，默认 gpt-4o-mini
```

**使用 DeepSeek:**
```bash
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export LLM_MODEL="deepseek-chat"  # 可选，默认 deepseek-chat
```

**使用 Qwen（通义千问）:**
```bash
export LLM_PROVIDER=qwen
export QWEN_API_KEY="your-qwen-api-key"
export LLM_MODEL="qwen-plus"  # 可选，默认 qwen-plus
```

#### 方式二：配置文件

```bash
# 复制配置模板
cp config.example.yaml config.yaml

# 编辑配置文件，填入您的 API Key
vim config.yaml

# 使用配置文件运行
python main.py --config config.yaml --log-file logs.tar.gz
```

#### 方式三：命令行参数

```bash
python main.py \
  --provider deepseek \
  --api-key "your-api-key" \
  --model "deepseek-chat" \
  --log-file logs.tar.gz
```

### 3. 运行分析

```bash
# 分析单个日志文件
python main.py --log-file /path/to/logs.tar.gz

# 分析普通文本日志
python main.py --log-file /var/log/syslog

# 运行测试模式
python main.py --test-mode

# 限制测试数量
python main.py --test-mode --limit 2
```

## 使用场景

### 典型场景：网络设备硬件故障分析

1. **问题描述**：网络安全设备网卡出现异常
2. **日志采集**：使用 `dmesg` 等命令导出相关日志到 tar.gz 包
3. **AI 分析**：
   - 解压并读取日志文件
   - 应用提示词模板进行智能分析
   - 识别错误类型、定位问题根源
   - 提供修复建议
4. **结果评估**：评估器验证分析结果的准确性和完整性

## Harness Engineering 工作流程

### 第一步：定义提示词模板

在 `prompts/analyze_log.txt` 中定义 AI 的分析逻辑：
- 角色定义（网络安全专家）
- 分析框架（日志分类、错误识别、根因分析）
- 输出格式（结构化 JSON）

### 第二步：构建测试用例

在 `test_cases/logs.json` 中准备多样化的测试场景：
- 网卡故障日志
- 磁盘异常日志
- 内存错误日志
- 安全事件日志

### 第三步：运行并评估

```bash
# 运行主程序
python main.py --test-mode

# 运行评估器
python evaluator/evaluator.py
```

### 第四步：迭代优化

根据评估结果：
- 优化提示词模板
- 扩充测试用例
- 调整评估标准
- 再次测试验证

## 技术实现

### AI 分析能力
- 支持多种 LLM API（OpenAI、DeepSeek、Qwen）
- 兼容 OpenAI API 格式的自定义端点
- 支持多种日志格式（dmesg、syslog、应用日志等）
- 流式输出，实时展示分析进度

### 评估体系
- **规则评估**：检查输出格式、必填字段
- **语义评估**：评估分析结果的准确性
- **综合评分**：多维度打分，指导优化方向

## 支持的 LLM 提供商

| 提供商 | 环境变量 | 默认模型 | Base URL |
|--------|---------|---------|----------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini | https://api.openai.com/v1 |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat | https://api.deepseek.com/v1 |
| Qwen | `QWEN_API_KEY` | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 自定义 | - | - | 通过 `--base-url` 指定 |

**注意事项：**
- DeepSeek 和 Qwen 使用 OpenAI 兼容的 API 格式
- 可以通过 `LLM_PROVIDER` 环境变量切换提供商
- 支持任何兼容 OpenAI API 格式的服务（如本地部署的 Ollama）

## 最佳实践

### 1. 提示词迭代
- 从简单场景开始，逐步覆盖复杂场景
- 记录每次提示词修改的原因和效果
- 建立提示词版本管理

### 2. 测试用例管理
- 覆盖常见场景和边界情况
- 持续扩充真实生产环境的日志样本
- 标注预期输出作为基准

### 3. 评估标准优化
- 结合专家反馈调整评估标准
- 平衡自动化评估与人工审核
- 建立评估指标的置信区间

### 4. 成本控制
- 使用 `--limit` 参数限制测试数量
- 选择合适的模型（如 DeepSeek 成本较低）
- 优化提示词长度，减少 token 消耗

## 常见问题

### Q: 如何使用本地部署的模型？
A: 如果您使用 Ollama 等本地部署工具，可以这样配置：
```bash
python main.py \
  --provider openai \
  --api-key "ollama" \
  --base-url "http://localhost:11434/v1" \
  --model "llama3" \
  --log-file logs.tar.gz
```

### Q: API Key 安全建议？
A:
1. 不要将 API Key 提交到代码仓库
2. 使用环境变量或配置文件（并加入 .gitignore）
3. 生产环境使用密钥管理服务

### Q: 如何切换不同的模型？
A: 通过环境变量或命令行参数：
```bash
# OpenAI
export LLM_MODEL="gpt-4o"

# DeepSeek
export LLM_MODEL="deepseek-coder"

# 或命令行
python main.py --model "gpt-4o" --log-file logs.tar.gz
```

## 未来规划

- [ ] 支持更多日志格式（防火墙、IDS、Web 服务器）
- [ ] 集成知识库进行上下文增强
- [ ] 实现多轮对话式故障排查
- [ ] 添加可视化分析报告
- [ ] 支持更多 LLM 提供商

## 贡献指南

欢迎提交 Issue 和 Pull Request，共同完善本项目！

## 许可证

MIT License
