# AI Log Analyzer - 项目开发指南

## 项目概述

本项目是一个基于 **Harness Engineering** 思路构建的网络安全日志分析系统，支持本地独立运行，兼容多种 LLM API（OpenAI、DeepSeek、Qwen 等）。

## 核心理念

**Harness Engineering 四要素：**
1. **Prompts** - 结构化提示词模板
2. **Test Cases** - 测试用例库
3. **Evaluator** - 自动化评估器
4. **Results** - 结果追踪与迭代

## 项目结构

```
ai-log-analyzer/
├── README.md                    # 项目文档（必读）
├── AGENTS.md                    # 本文件，开发指南
├── main.py                     # 主程序入口
├── config.example.yaml         # 配置文件模板
├── requirements.txt            # 依赖包列表
├── prompts/
│   └── analyze_log.txt         # 日志分析提示词模板
├── test_cases/
│   └── logs.json               # 测试用例数据集（6个场景）
├── evaluator/
│   └── evaluator.py            # 评估器实现
└── results/
    ├── output.json             # 分析结果输出
    └── evaluation_report.json  # 评估报告（运行评估后生成）
```

## 开发环境

### Python 版本
- Python 3.8+

### 依赖包安装
```bash
# 最小安装（仅核心功能）
pip install openai

# 完整安装（包含配置文件支持）
pip install -r requirements.txt
```

### 依赖说明
- `openai>=1.0.0`: OpenAI SDK，兼容多个 LLM 提供商
- `pyyaml>=6.0`: YAML 配置文件支持（可选）

## 快速开始

### 1. 配置 API

#### 环境变量方式（推荐）
```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# DeepSeek
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="your-api-key"

# Qwen
export LLM_PROVIDER=qwen
export QWEN_API_KEY="your-api-key"
```

#### 配置文件方式
```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入 API Key
```

### 2. 运行分析
```bash
# 分析日志文件
python main.py --log-file logs.tar.gz

# 测试模式
python main.py --test-mode --limit 2
```

## 核心模块说明

### main.py - 主程序
**功能：**
- 支持多种 LLM API（OpenAI、DeepSeek、Qwen）
- 解压并读取日志文件（支持 .tar.gz 和普通文本）
- 加载提示词模板
- 调用 LLM 进行智能分析
- 保存结构化分析结果

**关键类：**
- `LLMConfig`: LLM 配置管理
- `LogAnalyzer`: 日志分析器核心类

**LLM 配置优先级：**
1. 命令行参数
2. 配置文件（config.yaml）
3. 环境变量

### config.example.yaml - 配置模板
**配置项：**
```yaml
llm:
  provider: openai        # 提供商: openai, deepseek, qwen
  api_key: ""            # API Key
  base_url: ""           # API Base URL（可选）
  model: "gpt-4o-mini"   # 模型名称
  temperature: 0.3       # 温度参数
  max_tokens: 4096       # 最大输出 token
```

### prompts/analyze_log.txt - 提示词模板
**结构：**
1. 角色定义（网络安全运维专家）
2. 任务描述
3. 分析框架（5步法）
4. 输出格式（JSON Schema）
5. 分析原则
6. 特殊情况处理

**迭代优化：**
- 修改此文件后无需重启
- 建议保留历史版本用于对比

### test_cases/logs.json - 测试用例库
**当前测试场景（6个）：**
1. TC001 - 网卡驱动故障
2. TC002 - 磁盘I/O错误
3. TC003 - 内存错误
4. TC004 - 防火墙连接追踪表溢出
5. TC005 - SSH暴力破解攻击
6. TC006 - CPU温度过高

**测试用例结构：**
```json
{
  "id": "TC001",
  "name": "测试名称",
  "category": "问题分类",
  "severity": "严重程度",
  "log_content": "日志内容",
  "expected_analysis": {
    "issue_type": "问题类型",
    "affected_component": "受影响组件",
    "root_cause": "根本原因",
    "suggested_actions": ["建议措施"]
  }
}
```

### evaluator/evaluator.py - 评估器
**评估维度（总分100分）：**
1. **格式评估**（20分）：检查输出格式是否正确
2. **准确性评估**（60分）：
   - 问题类型匹配（15分）
   - 严重程度匹配（15分）
   - 根因分析相似度（15分）
   - 建议措施覆盖率（15分）
3. **完整性评估**（20分）：
   - 日志证据引用（10分）
   - 建议措施数量（10分）

**等级标准：**
- A+ (优秀): ≥90分
- A (良好): ≥80分
- B (中等): ≥70分
- C (及格): ≥60分
- D (不及格): <60分

## LLM 提供商配置

### OpenAI
```bash
export OPENAI_API_KEY="sk-xxxxx"
export LLM_MODEL="gpt-4o-mini"  # 可选
```

### DeepSeek
```bash
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="sk-xxxxx"
export LLM_MODEL="deepseek-chat"  # 可选
```

### Qwen（通义千问）
```bash
export LLM_PROVIDER=qwen
export QWEN_API_KEY="sk-xxxxx"
export LLM_MODEL="qwen-plus"  # 可选
```

### 自定义端点（如 Ollama）
```bash
python main.py \
  --provider openai \
  --api-key "ollama" \
  --base-url "http://localhost:11434/v1" \
  --model "llama3" \
  --log-file logs.tar.gz
```

## 输出格式规范

### 分析结果 JSON 结构
```json
{
  "analysis_summary": {
    "total_issues": 1,
    "critical_count": 1,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0
  },
  "issues": [
    {
      "id": "ISSUE-001",
      "category": "hardware_network",
      "severity": "critical",
      "title": "问题标题",
      "affected_component": "受影响组件",
      "log_evidence": ["关键日志条目"],
      "root_cause": "根本原因分析",
      "impact": "问题影响范围",
      "suggested_actions": ["建议措施"],
      "references": ["参考链接"]
    }
  ],
  "overall_recommendations": ["全局性建议"],
  "additional_notes": "其他说明"
}
```

## 常见开发任务

### 添加新的测试用例
1. 编辑 `test_cases/logs.json`
2. 添加新的测试用例对象
3. 运行 `python main.py --test-mode --limit 1` 验证
4. 运行评估器查看得分

### 优化提示词
1. 编辑 `prompts/analyze_log.txt`
2. 运行测试模式验证效果
3. 对比评估报告，查看改进效果

### 切换 LLM 提供商
```bash
# 方式一：环境变量
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY="your-key"

# 方式二：配置文件
cp config.example.yaml config.yaml
# 编辑 config.yaml

# 方式三：命令行
python main.py --provider deepseek --api-key "your-key" --log-file logs.tar.gz
```

## 测试与验证

### 语法检查
```bash
python3 -m py_compile main.py evaluator/evaluator.py
```

### 运行单个测试
```bash
# 创建临时日志文件
echo "[2024-01-15 14:23:45] [KERNEL] eth0: link down" > test.log

# 运行分析
python main.py --log-file test.log
```

### 完整测试流程
```bash
# 1. 配置 API
export OPENAI_API_KEY="your-key"

# 2. 运行测试模式
python main.py --test-mode --limit 2

# 3. 运行评估器
python evaluator/evaluator.py

# 4. 查看评估报告
cat results/evaluation_report.json
```

## 故障排查

### API 连接失败
- 检查网络连接
- 验证 API Key 是否正确
- 确认 Base URL 是否正确
- 查看错误日志

### JSON 解析失败
- 检查提示词是否要求输出 JSON
- 查看原始响应内容（results/*.json 中的 raw_response 字段）
- 可能是模型输出格式不符合预期，需优化提示词

### 评估器报错
- 确认结果文件已生成（results/TC00X.json）
- 检查测试用例 ID 是否匹配

### 模型响应慢
- 尝试使用更快的模型（如 gpt-4o-mini, deepseek-chat）
- 减少 max_tokens
- 检查网络延迟

## 最佳实践

### 1. 提示词迭代
- 从简单场景开始
- 记录每次修改的原因和效果
- 使用版本控制管理提示词

### 2. 测试用例管理
- 覆盖常见场景和边界情况
- 持续扩充真实生产日志
- 标注预期输出作为基准

### 3. 评估标准优化
- 结合专家反馈调整
- 平衡自动化与人工审核
- 建立评估指标置信区间

### 4. 成本控制
- 使用 `--limit` 限制测试数量
- 选择性价比高的模型（DeepSeek 成本较低）
- 优化提示词长度

### 5. 安全建议
- 不要将 API Key 提交到代码仓库
- 将 config.yaml 加入 .gitignore
- 使用环境变量或密钥管理服务

## 未来规划

- [ ] 支持更多日志格式（防火墙、IDS、Web服务器）
- [ ] 集成知识库进行上下文增强
- [ ] 实现多轮对话式故障排查
- [ ] 添加可视化分析报告
- [ ] 支持实时日志流分析
- [ ] 支持更多 LLM 提供商

## 相关文档

- [README.md](README.md) - 项目介绍和使用说明
- [config.example.yaml](config.example.yaml) - 配置文件模板
- [prompts/analyze_log.txt](prompts/analyze_log.txt) - 提示词模板
- [test_cases/logs.json](test_cases/logs.json) - 测试用例库

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
