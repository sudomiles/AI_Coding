#!/usr/bin/env python3
"""
日志分析评估器
用于评估AI分析结果的质量和准确性
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher


class LogAnalysisEvaluator:
    """日志分析结果评估器"""
    
    def __init__(self):
        self.evaluation_results = []
        self.total_score = 0
        self.max_score = 0
        
    def load_test_cases(self, test_file: str) -> List[Dict]:
        """加载测试用例"""
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('test_cases', [])
    
    def load_result(self, result_file: str) -> Dict:
        """加载分析结果"""
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def evaluate_format(self, result: Dict) -> Tuple[int, List[str]]:
        """评估输出格式是否正确"""
        score = 0
        max_score = 20
        issues = []
        
        # 检查必需字段
        required_fields = ['analysis_summary', 'issues']
        for field in required_fields:
            if field in result:
                score += 5
            else:
                issues.append(f"缺少必需字段: {field}")
        
        # 检查issues数组结构
        if 'issues' in result and isinstance(result['issues'], list):
            if len(result['issues']) > 0:
                issue_fields = ['category', 'severity', 'title', 'root_cause', 'suggested_actions']
                first_issue = result['issues'][0]
                present_fields = [f for f in issue_fields if f in first_issue]
                score += int((len(present_fields) / len(issue_fields)) * 10)
                missing_fields = [f for f in issue_fields if f not in first_issue]
                if missing_fields:
                    issues.append(f"issue对象缺少字段: {', '.join(missing_fields)}")
        
        return score, issues
    
    def evaluate_accuracy(self, result: Dict, expected: Dict) -> Tuple[int, Dict[str, Any]]:
        """评估分析准确性"""
        score = 0
        max_score = 60
        details = {
            'issue_type_match': False,
            'severity_match': False,
            'root_cause_similarity': 0.0,
            'actions_coverage': 0.0
        }
        
        # 检查问题类型匹配
        if 'issues' in result and len(result['issues']) > 0:
            analyzed_issue = result['issues'][0]
            expected_issue_type = expected.get('issue_type', '')
            analyzed_category = analyzed_issue.get('category', '')
            
            if expected_issue_type in analyzed_category or analyzed_category in expected_issue_type:
                score += 15
                details['issue_type_match'] = True
        
        # 检查严重程度匹配
        if 'issues' in result and len(result['issues']) > 0:
            analyzed_severity = result['issues'][0].get('severity', '').lower()
            expected_severity = expected.get('severity', '').lower()
            
            if analyzed_severity == expected_severity:
                score += 15
                details['severity_match'] = True
        
        # 计算根因分析相似度
        if 'issues' in result and len(result['issues']) > 0:
            analyzed_root_cause = result['issues'][0].get('root_cause', '')
            expected_root_cause = expected.get('root_cause', '')
            
            similarity = self.calculate_similarity(analyzed_root_cause, expected_root_cause)
            score += int(similarity * 15)
            details['root_cause_similarity'] = similarity
        
        # 计算建议措施覆盖率
        if 'issues' in result and len(result['issues']) > 0:
            analyzed_actions = result['issues'][0].get('suggested_actions', [])
            expected_actions = expected.get('suggested_actions', [])
            
            if analyzed_actions and expected_actions:
                # 计算建议措施的重叠度
                matched_count = 0
                for exp_action in expected_actions:
                    for ana_action in analyzed_actions:
                        if self.calculate_similarity(exp_action, ana_action) > 0.5:
                            matched_count += 1
                            break
                
                coverage = matched_count / len(expected_actions)
                score += int(coverage * 15)
                details['actions_coverage'] = coverage
        
        return score, details
    
    def evaluate_completeness(self, result: Dict, test_case: Dict) -> Tuple[int, List[str]]:
        """评估分析完整性"""
        score = 0
        max_score = 20
        issues = []
        
        # 检查是否识别了所有关键日志
        log_content = test_case.get('log_content', '')
        log_lines = [line.strip() for line in log_content.split('\n') if line.strip()]
        
        if 'issues' in result and len(result['issues']) > 0:
            log_evidence = result['issues'][0].get('log_evidence', [])
            
            # 检查是否引用了关键日志
            if log_evidence:
                score += 10
            else:
                issues.append("未引用关键日志证据")
        
        # 检查是否提供了可行的建议
        if 'issues' in result and len(result['issues']) > 0:
            suggested_actions = result['issues'][0].get('suggested_actions', [])
            if len(suggested_actions) >= 3:
                score += 10
            else:
                issues.append(f"建议措施不足（当前{len(suggested_actions)}条，建议至少3条）")
        
        return score, issues
    
    def evaluate_single_case(self, test_case: Dict, result_file: str) -> Dict:
        """评估单个测试用例"""
        try:
            result = self.load_result(result_file)
            expected = test_case.get('expected_analysis', {})
            
            # 格式评估
            format_score, format_issues = self.evaluate_format(result)
            
            # 准确性评估
            accuracy_score, accuracy_details = self.evaluate_accuracy(result, expected)
            
            # 完整性评估
            completeness_score, completeness_issues = self.evaluate_completeness(result, test_case)
            
            total_score = format_score + accuracy_score + completeness_score
            max_score = 100
            
            evaluation = {
                'test_case_id': test_case.get('id'),
                'test_case_name': test_case.get('name'),
                'total_score': total_score,
                'max_score': max_score,
                'percentage': round((total_score / max_score) * 100, 2),
                'breakdown': {
                    'format': {
                        'score': format_score,
                        'max_score': 20,
                        'issues': format_issues
                    },
                    'accuracy': {
                        'score': accuracy_score,
                        'max_score': 60,
                        'details': accuracy_details
                    },
                    'completeness': {
                        'score': completeness_score,
                        'max_score': 20,
                        'issues': completeness_issues
                    }
                },
                'grade': self._get_grade(total_score)
            }
            
            return evaluation
            
        except Exception as e:
            return {
                'test_case_id': test_case.get('id'),
                'test_case_name': test_case.get('name'),
                'error': str(e),
                'total_score': 0,
                'percentage': 0
            }
    
    def _get_grade(self, score: int) -> str:
        """根据分数返回等级"""
        if score >= 90:
            return 'A+ (优秀)'
        elif score >= 80:
            return 'A (良好)'
        elif score >= 70:
            return 'B (中等)'
        elif score >= 60:
            return 'C (及格)'
        else:
            return 'D (不及格)'
    
    def run_evaluation(self, test_file: str, results_dir: str) -> Dict:
        """运行完整评估"""
        test_cases = self.load_test_cases(test_file)
        evaluations = []
        
        for test_case in test_cases:
            test_id = test_case.get('id')
            result_file = os.path.join(results_dir, f"{test_id}.json")
            
            if os.path.exists(result_file):
                evaluation = self.evaluate_single_case(test_case, result_file)
            else:
                evaluation = {
                    'test_case_id': test_id,
                    'test_case_name': test_case.get('name'),
                    'error': f'结果文件不存在: {result_file}',
                    'total_score': 0,
                    'percentage': 0
                }
            
            evaluations.append(evaluation)
        
        # 计算总体统计
        total_tests = len(evaluations)
        passed_tests = len([e for e in evaluations if e.get('total_score', 0) >= 60])
        avg_score = sum([e.get('total_score', 0) for e in evaluations]) / total_tests if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
            'average_score': round(avg_score, 2),
            'overall_grade': self._get_grade(avg_score)
        }
        
        return {
            'summary': summary,
            'evaluations': evaluations
        }
    
    def save_report(self, report: Dict, output_file: str):
        """保存评估报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"评估报告已保存到: {output_file}")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 定义路径
    test_file = project_root / 'test_cases' / 'logs.json'
    results_dir = project_root / 'results'
    output_file = results_dir / 'evaluation_report.json'
    
    # 确保results目录存在
    results_dir.mkdir(exist_ok=True)
    
    # 创建评估器并运行评估
    evaluator = LogAnalysisEvaluator()
    
    print("=" * 60)
    print("日志分析评估器")
    print("=" * 60)
    print(f"测试用例文件: {test_file}")
    print(f"结果目录: {results_dir}")
    print(f"报告输出: {output_file}")
    print("=" * 60)
    
    # 检查测试用例文件是否存在
    if not test_file.exists():
        print(f"错误: 测试用例文件不存在: {test_file}")
        sys.exit(1)
    
    # 运行评估
    report = evaluator.run_evaluation(str(test_file), str(results_dir))
    
    # 打印摘要
    print("\n评估摘要:")
    print(f"  总测试数: {report['summary']['total_tests']}")
    print(f"  通过数: {report['summary']['passed_tests']}")
    print(f"  通过率: {report['summary']['pass_rate']}%")
    print(f"  平均分: {report['summary']['average_score']}/100")
    print(f"  总体等级: {report['summary']['overall_grade']}")
    print()
    
    # 打印详细结果
    print("详细评估结果:")
    print("-" * 60)
    for evaluation in report['evaluations']:
        print(f"\n测试用例: {evaluation.get('test_case_name', 'Unknown')}")
        print(f"  ID: {evaluation.get('test_case_id')}")
        
        if 'error' in evaluation:
            print(f"  错误: {evaluation['error']}")
        else:
            print(f"  总分: {evaluation['total_score']}/100")
            print(f"  等级: {evaluation['grade']}")
            print(f"  格式分: {evaluation['breakdown']['format']['score']}/20")
            print(f"  准确性分: {evaluation['breakdown']['accuracy']['score']}/60")
            print(f"  完整性分: {evaluation['breakdown']['completeness']['score']}/20")
            
            # 显示问题
            issues = []
            issues.extend(evaluation['breakdown']['format'].get('issues', []))
            issues.extend(evaluation['breakdown']['completeness'].get('issues', []))
            if issues:
                print(f"  需要改进:")
                for issue in issues:
                    print(f"    - {issue}")
    
    # 保存报告
    evaluator.save_report(report, str(output_file))
    
    # 返回退出码
    if report['summary']['pass_rate'] >= 80:
        print("\n✓ 评估通过！")
        sys.exit(0)
    else:
        print("\n✗ 评估未达到预期，需要改进。")
        sys.exit(1)


if __name__ == '__main__':
    main()
