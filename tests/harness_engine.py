"""
Harness Engine - Agent自动化测试评分引擎
支持多维度评估：意图识别、工具调用、回答质量、格式规范、响应时延
"""
import os
import re
import json
import time
import traceback
from datetime import datetime
from typing import Any

# ── 评分维度权重 ──────────────────────────────────────────
WEIGHTS = {
    "intent_accuracy": 0.25,    # 意图识别准确率
    "tool_correctness": 0.20,   # 工具调用正确性
    "content_completeness": 0.20,  # 内容完整性
    "format_quality": 0.15,     # 格式规范性
    "response_latency": 0.10,   # 响应时延（归一化）
    "graceful_error": 0.10,     # 异常处理优雅度
}

# 延迟评分阈值（秒）
LATENCY_THRESHOLDS = {
    "excellent": 5,
    "good": 10,
    "acceptable": 20,
    "slow": 30,
}


class EvalResult:
    """单条用例评估结果"""
    def __init__(self, case_id: str, case_name: str, module: str):
        self.case_id = case_id
        self.case_name = case_name
        self.module = module
        self.scores = {}
        self.total_score = 0.0
        self.passed = False
        self.error_msg = ""
        self.agent_output = ""
        self.tools_called = []
        self.latency_sec = 0.0
        self.details = {}

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "module": self.module,
            "scores": self.scores,
            "total_score": round(self.total_score, 2),
            "passed": self.passed,
            "error_msg": self.error_msg,
            "tools_called": self.tools_called,
            "latency_sec": round(self.latency_sec, 2),
            "details": self.details,
        }


class HarnessEngine:
    """Agent测试评分引擎"""

    def __init__(self):
        self.results: list[EvalResult] = []
        self.start_time = None
        self.end_time = None

    # ── 核心评估方法 ────────────────────────────────────

    def evaluate_case(
        self,
        case: dict,
        module_name: str,
        agent_output: str,
        tools_called: list[dict],
        latency_sec: float,
        error_msg: str = ""
    ) -> EvalResult:
        """评估单条测试用例"""
        result = EvalResult(
            case_id=case["id"],
            case_name=case["name"],
            module=module_name
        )
        result.agent_output = agent_output
        result.tools_called = [t.get("tool_name", "") for t in tools_called]
        result.latency_sec = latency_sec
        result.error_msg = error_msg

        criteria = case.get("eval_criteria", {})

        # 1. 意图识别准确率
        result.scores["intent_accuracy"] = self._eval_intent(case, agent_output, tools_called)

        # 2. 工具调用正确性
        result.scores["tool_correctness"] = self._eval_tool_call(case, tools_called)

        # 3. 内容完整性（关键词覆盖）
        result.scores["content_completeness"] = self._eval_content(case, agent_output)

        # 4. 格式规范性
        result.scores["format_quality"] = self._eval_format(case, agent_output)

        # 5. 响应时延
        result.scores["response_latency"] = self._eval_latency(latency_sec)

        # 6. 异常处理
        result.scores["graceful_error"] = self._eval_graceful_error(case, agent_output, error_msg)

        # 加权总分
        result.total_score = sum(
            result.scores.get(k, 0) * w
            for k, w in WEIGHTS.items()
        )

        # 通过判定：总分 >= 60 且 意图识别正确
        result.passed = (
            result.total_score >= 60
            and result.scores.get("intent_accuracy", 0) >= 80
        )

        # 记录详情
        result.details = {
            "expected_intent": case.get("expected_intent"),
            "expected_tool": case.get("expected_tool"),
            "criteria_keys": list(criteria.keys()),
        }

        return result

    # ── 各维度评估逻辑 ──────────────────────────────────

    def _eval_intent(self, case: dict, output: str, tools_called: list) -> float:
        """评估意图识别是否正确"""
        expected_intent = case.get("expected_intent")
        if not expected_intent:
            return 80  # 无明确预期时给基础分

        # 通过工具调用推断意图
        tool_names = [t.get("tool_name", "") for t in tools_called]

        intent_tool_map = {
            "resume_parse": ["parse_resume"],
            "company_research": ["research_company"],
            "knowledge_qa": ["search_knowledge", "query_knowledge_graph"],
            "jd_matching": [],  # JD匹配通常不调用工具
            "mock_interview": [],  # 面试通常不调用工具
            "mock_interview_end": [],
            "general_chat": [],
            "out_of_scope": [],
        }

        expected_tools = intent_tool_map.get(expected_intent, [])
        expected_tool = case.get("expected_tool")

        # 检查是否调用了正确的工具
        if expected_tool:
            if expected_tool in tool_names:
                return 100
            else:
                return 30  # 意图识别错误
        elif expected_tool is None:
            # 预期不调用工具
            if not tool_names or all(t == "" for t in tool_names):
                return 100
            # 调用了工具但不在预期中，检查是否相关
            return 70  # 可能正确但无法确认

        return 80

    def _eval_tool_call(self, case: dict, tools_called: list) -> float:
        """评估工具调用正确性"""
        expected_tool = case.get("expected_tool")
        tool_names = [t.get("tool_name", "") for t in tools_called]

        if expected_tool is None:
            # 预期不调用工具
            if not tool_names or all(t == "" for t in tool_names):
                return 100
            # 调用了不必要的工具
            return 50

        if expected_tool in tool_names:
            return 100

        if not tool_names:
            return 0  # 预期调用工具但未调用

        return 30  # 调用了错误的工具

    def _eval_content(self, case: dict, output: str) -> float:
        """评估内容完整性（关键词覆盖）"""
        criteria = case.get("eval_criteria", {})
        response_contains = criteria.get("response_contains", [])

        if not response_contains:
            return 80  # 无关键词要求时给基础分

        if not output:
            return 0

        output_lower = output.lower()
        matched = sum(
            1 for kw in response_contains
            if kw.lower() in output_lower
        )

        coverage = matched / len(response_contains) if response_contains else 1.0
        return min(100, coverage * 100)

    def _eval_format(self, case: dict, output: str) -> float:
        """评估格式规范性"""
        if not output:
            return 0

        score = 60  # 基础分

        # 检查是否有结构化输出
        if any(marker in output for marker in ["#", "|", "- ", "1.", "✅", "📊", "📝"]):
            score += 20

        # 检查是否有评分（如果要求）
        criteria = case.get("eval_criteria", {})
        if criteria.get("has_scoring"):
            if re.search(r'\d+\s*分', output) or re.search(r'评分[:：]?\s*\d+', output):
                score += 10
            else:
                score -= 10

        # 检查是否有改进建议（如果要求）
        if criteria.get("has_improvement_suggestions"):
            if any(kw in output for kw in ["建议", "改进", "提升", "优化"]):
                score += 10

        # 检查是否有评价报告（如果要求）
        if criteria.get("has_evaluation_report"):
            if any(kw in output for kw in ["评价", "报告", "维度", "综合"]):
                score += 10

        return min(100, score)

    def _eval_latency(self, latency_sec: float) -> float:
        """评估响应时延"""
        if latency_sec <= LATENCY_THRESHOLDS["excellent"]:
            return 100
        elif latency_sec <= LATENCY_THRESHOLDS["good"]:
            return 80
        elif latency_sec <= LATENCY_THRESHOLDS["acceptable"]:
            return 60
        elif latency_sec <= LATENCY_THRESHOLDS["slow"]:
            return 40
        else:
            return 20

    def _eval_graceful_error(self, case: dict, output: str, error_msg: str) -> float:
        """评估异常处理优雅度"""
        criteria = case.get("eval_criteria", {})

        if not criteria.get("graceful_error") and not error_msg:
            return 80  # 非异常场景给基础分

        if error_msg and not output:
            return 0  # 有错误但无输出

        if error_msg and output:
            # 有错误但有友好输出
            if any(kw in output for kw in ["抱歉", "无法", "请检查", "尝试", "建议"]):
                return 100
            return 60

        if criteria.get("graceful_error"):
            if any(kw in output for kw in ["异常", "错误", "无法", "失败", "检查", "请"]):
                return 90
            return 50

        return 80

    # ── 报告生成 ────────────────────────────────────────

    def generate_report(self) -> dict:
        """生成完整测试报告"""
        self.end_time = datetime.now()

        total_cases = len(self.results)
        passed_cases = sum(1 for r in self.results if r.passed)
        failed_cases = total_cases - passed_cases

        # 按模块统计
        module_stats = {}
        for r in self.results:
            if r.module not in module_stats:
                module_stats[r.module] = {"total": 0, "passed": 0, "avg_score": 0, "scores": []}
            module_stats[r.module]["total"] += 1
            if r.passed:
                module_stats[r.module]["passed"] += 1
            module_stats[r.module]["scores"].append(r.total_score)

        for mod in module_stats:
            scores = module_stats[mod]["scores"]
            module_stats[mod]["avg_score"] = round(sum(scores) / len(scores), 2) if scores else 0

        # 平均延迟
        avg_latency = (
            sum(r.latency_sec for r in self.results) / total_cases
            if total_cases > 0 else 0
        )

        # 各维度平均分
        dimension_avgs = {}
        for dim in WEIGHTS:
            dim_scores = [r.scores.get(dim, 0) for r in self.results if r.scores.get(dim) is not None]
            dimension_avgs[dim] = round(sum(dim_scores) / len(dim_scores), 2) if dim_scores else 0

        report = {
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "duration_sec": round((self.end_time - self.start_time).total_seconds(), 2) if self.start_time else 0,
            "summary": {
                "total_cases": total_cases,
                "passed": passed_cases,
                "failed": failed_cases,
                "pass_rate": round(passed_cases / total_cases * 100, 1) if total_cases > 0 else 0,
                "avg_score": round(sum(r.total_score for r in self.results) / total_cases, 2) if total_cases > 0 else 0,
                "avg_latency_sec": round(avg_latency, 2),
            },
            "module_stats": module_stats,
            "dimension_averages": dimension_avgs,
            "results": [r.to_dict() for r in self.results],
            "failed_details": [
                {
                    "case_id": r.case_id,
                    "case_name": r.case_name,
                    "module": r.module,
                    "score": r.total_score,
                    "error_msg": r.error_msg,
                    "scores": r.scores,
                }
                for r in self.results if not r.passed
            ],
        }

        return report

    def print_report(self, report: dict):
        """打印可读的测试报告"""
        s = report["summary"]
        print("\n" + "=" * 70)
        print(f"  🧪 Agent自动化测试报告  |  {report['report_id']}")
        print("=" * 70)
        print(f"  总用例: {s['total_cases']}  |  通过: {s['passed']}  |  失败: {s['failed']}  |  通过率: {s['pass_rate']}%")
        print(f"  平均得分: {s['avg_score']}  |  平均延迟: {s['avg_latency_sec']}s  |  总耗时: {report['duration_sec']}s")
        print("-" * 70)

        # 模块统计
        print("\n  📊 模块统计:")
        for mod, stats in report["module_stats"].items():
            status = "✅" if stats["passed"] == stats["total"] else "⚠️"
            print(f"    {status} {mod}: {stats['passed']}/{stats['total']} 通过 (平均分: {stats['avg_score']})")

        # 维度平均
        print("\n  📐 维度评分:")
        dim_names = {
            "intent_accuracy": "意图识别",
            "tool_correctness": "工具调用",
            "content_completeness": "内容完整",
            "format_quality": "格式规范",
            "response_latency": "响应时延",
            "graceful_error": "异常处理",
        }
        for dim, avg in report["dimension_averages"].items():
            bar = "█" * int(avg / 5) + "░" * (20 - int(avg / 5))
            print(f"    {dim_names.get(dim, dim): <6} [{bar}] {avg}")

        # 失败详情
        if report["failed_details"]:
            print("\n  ❌ 失败用例:")
            for f in report["failed_details"]:
                print(f"    [{f['case_id']}] {f['case_name']} (得分: {f['score']})")
                if f.get("error_msg"):
                    print(f"      错误: {f['error_msg'][:80]}")

        # 详细结果
        print("\n  📋 详细结果:")
        for r in report["results"]:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"    {status} [{r['case_id']}] {r['case_name']: <20} 得分:{r['total_score']:>6}  延迟:{r['latency_sec']:>6}s")

        print("\n" + "=" * 70)

    def save_report(self, report: dict, output_dir: str = None):
        """保存报告到文件"""
        if output_dir is None:
            output_dir = os.path.join(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"), "tests", "reports")
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n  📁 报告已保存: {filepath}")
        return filepath

    def compare_with_baseline(self, current_report: dict, baseline_path: str) -> dict:
        """与基线报告对比（回归测试）"""
        if not os.path.exists(baseline_path):
            return {"status": "no_baseline", "message": "无基线报告，跳过回归对比"}

        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        comparison = {
            "baseline_id": baseline.get("report_id"),
            "current_id": current_report.get("report_id"),
            "changes": [],
            "regressions": [],
            "improvements": [],
        }

        baseline_results = {r["case_id"]: r for r in baseline.get("results", [])}
        current_results = {r["case_id"]: r for r in current_report.get("results", [])}

        for case_id, current in current_results.items():
            if case_id in baseline_results:
                bl = baseline_results[case_id]
                score_diff = current["total_score"] - bl["total_score"]
                if abs(score_diff) >= 5:  # 5分以上变化才记录
                    change = {
                        "case_id": case_id,
                        "case_name": current["case_name"],
                        "baseline_score": bl["total_score"],
                        "current_score": current["total_score"],
                        "diff": round(score_diff, 2),
                    }
                    comparison["changes"].append(change)
                    if score_diff < -5:
                        comparison["regressions"].append(change)
                    elif score_diff > 5:
                        comparison["improvements"].append(change)

            else:
                comparison["changes"].append({
                    "case_id": case_id,
                    "case_name": current["case_name"],
                    "status": "new_case",
                    "current_score": current["total_score"],
                })

        # 检查删除的用例
        for case_id in baseline_results:
            if case_id not in current_results:
                comparison["changes"].append({
                    "case_id": case_id,
                    "status": "removed_case",
                })

        comparison["summary"] = {
            "total_changes": len(comparison["changes"]),
            "regressions": len(comparison["regressions"]),
            "improvements": len(comparison["improvements"]),
            "baseline_pass_rate": baseline["summary"]["pass_rate"],
            "current_pass_rate": current_report["summary"]["pass_rate"],
            "pass_rate_diff": round(
                current_report["summary"]["pass_rate"] - baseline["summary"]["pass_rate"], 1
            ),
        }

        return comparison
