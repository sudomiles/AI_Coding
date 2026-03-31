#!/usr/bin/env python3
"""
AI日志分析主程序
基于Harness Engineering思路构建的网络安全日志分析系统
支持多种 LLM API：OpenAI、DeepSeek、Qwen 等
"""

import os
import sys
import json
import argparse
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

# 尝试导入 OpenAI SDK
try:
    from openai import OpenAI
except ImportError:
    print("错误: 无法导入 openai 包，请先安装:")
    print("  pip install openai")
    sys.exit(1)

# 尝试导入 YAML（可选）
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量加载配置"""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        # 根据提供商设置默认值
        if provider == "deepseek":
            return cls(
                provider=provider,
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                model=os.getenv("LLM_MODEL", "deepseek-chat"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
            )
        elif provider == "qwen":
            return cls(
                provider=provider,
                api_key=os.getenv("QWEN_API_KEY", ""),
                base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model=os.getenv("LLM_MODEL", "qwen-plus"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
            )
        else:  # openai
            return cls(
                provider=provider,
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
            )
    
    @classmethod
    def from_yaml(cls, config_file: str) -> 'LLMConfig':
        """从 YAML 文件加载配置"""
        if not YAML_AVAILABLE:
            print("警告: 未安装 PyYAML，无法加载配置文件")
            print("  pip install pyyaml")
            return cls.from_env()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        llm_config = config_data.get('llm', {})
        return cls(
            provider=llm_config.get('provider', 'openai'),
            api_key=llm_config.get('api_key', ''),
            base_url=llm_config.get('base_url', ''),
            model=llm_config.get('model', 'gpt-4o-mini'),
            temperature=llm_config.get('temperature', 0.3),
            max_tokens=llm_config.get('max_tokens', 4096)
        )


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, project_root: Path, config: Optional[LLMConfig] = None):
        self.project_root = project_root
        self.prompts_dir = project_root / 'prompts'
        self.results_dir = project_root / 'results'
        self.results_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = config or LLMConfig.from_env()
        
        # 验证配置
        if not self.config.api_key:
            raise ValueError(
                f"未设置 API Key！请通过以下方式之一配置:\n"
                f"  1. 设置环境变量: {self.config.provider.upper()}_API_KEY\n"
                f"  2. 使用配置文件: config.yaml\n"
                f"  3. 命令行参数: --api-key"
            )
        
        # 初始化 OpenAI 客户端（兼容多个提供商）
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        print(f"✓ 已连接到 {self.config.provider.upper()} API")
        print(f"  模型: {self.config.model}")
        print(f"  Base URL: {self.config.base_url}")
    
    def load_prompt_template(self, template_name: str = 'analyze_log.txt') -> str:
        """加载提示词模板"""
        template_path = self.prompts_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"提示词模板不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_log_file(self, file_path: str) -> List[Dict]:
        """解压并读取日志文件"""
        log_files = []
        
        # 如果是tar.gz文件
        if file_path.endswith('.tar.gz') or file_path.endswith('.tgz'):
            print(f"解压文件: {file_path}")
            with tarfile.open(file_path, 'r:gz') as tar:
                # 创建临时目录
                temp_dir = tempfile.mkdtemp(prefix='log_analyzer_')
                tar.extractall(temp_dir)
                
                # 读取所有日志文件
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                log_files.append({
                                    'filename': file,
                                    'path': file_path,
                                    'content': content
                                })
                                print(f"  读取文件: {file} ({len(content)} 字节)")
                        except Exception as e:
                            print(f"  警告: 无法读取文件 {file}: {e}")
        
        # 如果是普通文件
        elif os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                log_files.append({
                    'filename': os.path.basename(file_path),
                    'path': file_path,
                    'content': content
                })
        else:
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        return log_files
    
    def analyze_log(self, log_content: str, prompt_template: str) -> Dict:
        """使用LLM分析日志"""
        # 组装完整的提示词
        full_prompt = prompt_template.replace('{LOG_CONTENT}', log_content)
        
        print("\n正在调用AI进行分析...")
        print("=" * 60)
        
        try:
            # 使用流式输出
            full_response = ""
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    full_response += text
            
            print("\n" + "=" * 60)
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分（处理可能包含的额外文本）
                json_start = full_response.find('{')
                json_end = full_response.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = full_response[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # 如果没有找到JSON，返回原始响应
                    result = {
                        'raw_response': full_response,
                        'error': '未找到有效的JSON响应'
                    }
            except json.JSONDecodeError as e:
                print(f"\n警告: JSON解析失败: {e}")
                result = {
                    'raw_response': full_response,
                    'error': str(e)
                }
            
            return result
            
        except Exception as e:
            print(f"\n错误: AI分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e)
            }
    
    def save_result(self, result: Dict, test_case_id: Optional[str] = None) -> str:
        """保存分析结果"""
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if test_case_id:
            filename = f"{test_case_id}.json"
        else:
            filename = f"output_{timestamp}.json"
        
        output_path = self.results_dir / filename
        
        # 添加元数据
        result['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'analyzer_version': '1.0',
            'llm_provider': self.config.provider,
            'llm_model': self.config.model,
            'test_case_id': test_case_id
        }
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_path}")
        return str(output_path)
    
    def run_analysis(self, log_file: str, test_case_id: Optional[str] = None) -> Dict:
        """运行完整的分析流程"""
        print("=" * 60)
        print("AI日志分析系统")
        print("=" * 60)
        print(f"输入文件: {log_file}")
        print(f"测试用例ID: {test_case_id or 'N/A'}")
        print("=" * 60)
        
        # 1. 加载提示词模板
        print("\n[1/4] 加载提示词模板...")
        try:
            prompt_template = self.load_prompt_template()
            print(f"✓ 提示词模板已加载 ({len(prompt_template)} 字节)")
        except FileNotFoundError as e:
            print(f"✗ 错误: {e}")
            return {'error': str(e)}
        
        # 2. 读取日志文件
        print("\n[2/4] 读取日志文件...")
        try:
            log_files = self.extract_log_file(log_file)
            print(f"✓ 共读取 {len(log_files)} 个日志文件")
            
            # 合并所有日志内容
            all_logs = "\n\n".join([
                f"=== {lf['filename']} ===\n{lf['content']}"
                for lf in log_files
            ])
            print(f"✓ 日志总大小: {len(all_logs)} 字节")
        except Exception as e:
            print(f"✗ 错误: {e}")
            return {'error': str(e)}
        
        # 3. AI分析
        print("\n[3/4] AI分析中...")
        result = self.analyze_log(all_logs, prompt_template)
        
        # 4. 保存结果
        print("\n[4/4] 保存分析结果...")
        output_path = self.save_result(result, test_case_id)
        
        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)
        
        result['output_path'] = output_path
        return result
    
    def run_test_mode(self, limit: Optional[int] = None) -> Dict:
        """运行测试模式（使用内置测试用例）"""
        test_cases_file = self.project_root / 'test_cases' / 'logs.json'
        if not test_cases_file.exists():
            print(f"错误: 测试用例文件不存在: {test_cases_file}")
            return {'error': 'Test cases file not found'}
        
        # 读取测试用例
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        test_cases = test_data.get('test_cases', [])
        if limit:
            test_cases = test_cases[:limit]
        
        print(f"\n找到 {len(test_cases)} 个测试用例")
        print("=" * 60)
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            test_id = test_case.get('id')
            test_name = test_case.get('name')
            log_content = test_case.get('log_content', '')
            
            print(f"\n[{i}/{len(test_cases)}] 运行测试用例: {test_name} (ID: {test_id})")
            print("-" * 60)
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
            temp_file.write(log_content)
            temp_file.close()
            
            try:
                # 运行分析
                result = self.run_analysis(temp_file.name, test_id)
                results.append({
                    'test_case_id': test_id,
                    'test_case_name': test_name,
                    'result': result
                })
            finally:
                # 清理临时文件
                os.unlink(temp_file.name)
        
        # 保存汇总结果
        summary_path = self.results_dir / 'test_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(results),
                'llm_provider': self.config.provider,
                'llm_model': self.config.model,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试汇总已保存到: {summary_path}")
        return {'results': results, 'summary_path': str(summary_path)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI日志分析系统 - 基于Harness Engineering（支持本地运行）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用 OpenAI API
  export OPENAI_API_KEY="your-api-key"
  python main.py --log-file /path/to/logs.tar.gz
  
  # 使用 DeepSeek API
  export LLM_PROVIDER=deepseek
  export DEEPSEEK_API_KEY="your-api-key"
  python main.py --log-file /path/to/logs.tar.gz
  
  # 使用 Qwen API
  export LLM_PROVIDER=qwen
  export QWEN_API_KEY="your-api-key"
  python main.py --log-file /path/to/logs.tar.gz
  
  # 使用配置文件
  python main.py --config config.yaml --log-file logs.tar.gz
  
  # 运行测试模式
  python main.py --test-mode --limit 2

支持的 LLM 提供商:
  - openai: OpenAI GPT 系列模型
  - deepseek: DeepSeek 模型
  - qwen: 阿里通义千问模型
  - 其他兼容 OpenAI API 格式的提供商
        """
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='日志文件路径（支持.tar.gz压缩包或普通文本文件）'
    )
    
    parser.add_argument(
        '--test-case-id',
        type=str,
        help='测试用例ID（用于结果追踪）'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='运行测试模式（使用内置测试用例）'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='测试模式下限制运行的用例数量'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径（YAML格式）'
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'deepseek', 'qwen'],
        help='LLM 提供商（也可通过环境变量 LLM_PROVIDER 设置）'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='API Key（也可通过环境变量设置）'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='模型名称（也可通过环境变量 LLM_MODEL 设置）'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        help='API Base URL（用于自定义端点）'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config:
        config = LLMConfig.from_yaml(args.config)
    else:
        config = LLMConfig.from_env()
    
    # 命令行参数覆盖配置
    if args.provider:
        config.provider = args.provider
        # 更新默认值
        if args.provider == "deepseek" and not config.base_url:
            config.base_url = "https://api.deepseek.com/v1"
        elif args.provider == "qwen" and not config.base_url:
            config.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    if args.api_key:
        config.api_key = args.api_key
    if args.model:
        config.model = args.model
    if args.base_url:
        config.base_url = args.base_url
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    
    try:
        # 创建分析器
        analyzer = LogAnalyzer(project_root, config)
        
        if args.test_mode:
            # 测试模式
            analyzer.run_test_mode(args.limit)
        elif args.log_file:
            # 单文件分析模式
            analyzer.run_analysis(args.log_file, args.test_case_id)
        else:
            parser.print_help()
            print("\n错误: 请指定 --log-file 或 --test-mode")
            sys.exit(1)
    except ValueError as e:
        print(f"\n配置错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
