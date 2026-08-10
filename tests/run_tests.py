"""
Agent自动化测试运行器
用法: python tests/run_tests.py [--module MODULE] [--case-id CASE_ID] [--baseline] [--save-baseline] [--llm-judge]
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime

# 确保项目路径在 sys.path 中
project_root = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tests.harness_engine import HarnessEngine


def load_test_cases(test_cases_path: str = None) -> dict:
    """加载测试用例"""
    if test_cases_path is None:
        test_cases_path = os.path.join(project_root, "tests", "test_cases.json")
    with open(test_cases_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_single_test(agent_builder, input_text: str, timeout: int = 60) -> dict:
    """
    运行单条测试，返回 agent 输出和工具调用记录
    """
    result = {
        "output": "",
        "tools_called": [],
        "latency_sec": 0.0,
        "error": ""
    }

    try:
        agent = agent_builder()
        start = time.time()

        # 调用 agent
        response = agent.invoke(
            {"messages": [{"role": "user", "content": input_text}]},
            config={"configurable": {"thread_id": f"test_{datetime.now().strftime('%f')}"}}
        )

        result["latency_sec"] = time.time() - start

        # 提取输出和工具调用
        messages = response.get("messages", [])
        for msg in messages:
            msg_type = type(msg).__name__
            if msg_type == "AIMessage":
                result["output"] = msg.content if isinstance(msg.content, str) else str(msg.content)
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        result["tools_called"].append({
                            "tool_name": tc.get("name", ""),
                            "tool_args": tc.get("args", {}),
                        })
            elif msg_type == "ToolMessage":
                result["tools_called"].append({
                    "tool_name": getattr(msg, "name", ""),
                    "tool_output": msg.content[:200] if msg.content else "",
                })

    except Exception as e:
        result["error"] = str(e)
        result["latency_sec"] = time.time() - start

    return result


def run_test_suite(
    agent_builder,
    modules_filter: str = None,
    case_ids_filter: list = None,
    use_llm_judge: bool = False,
) -> dict:
    """
    运行完整测试套件

    Args:
        agent_builder: Agent构建函数
        modules_filter: 模块筛选
        case_ids_filter: 用例ID筛选
        use_llm_judge: 是否使用LLM-as-Judge评估
    """
    engine = HarnessEngine(use_llm_judge=use_llm_judge)
    engine.start_time = datetime.now()

    test_data = load_test_cases()
    modules = test_data.get("modules", {})

    total_cases = sum(len(m.get("cases", [])) for m in modules.values())
    eval_mode = "LLM-as-Judge" if use_llm_judge else "规则评估"
    print(f"\n🧪 开始执行Agent自动化测试...")
    print(f"   测试用例总数: {total_cases}")
    print(f"   评估模式: {eval_mode}")
    if modules_filter:
        print(f"   筛选模块: {modules_filter}")
    if case_ids_filter:
        print(f"   筛选用例: {case_ids_filter}")
    print("-" * 60)

    executed = 0
    for module_name, module_data in modules.items():
        if modules_filter and module_name != modules_filter:
            continue

        cases = module_data.get("cases", [])
        print(f"\n  📦 模块: {module_name} ({module_data.get('description', '')})")

        for case in cases:
            if case_ids_filter and case["id"] not in case_ids_filter:
                continue

            executed += 1
            print(f"    [{executed}/{total_cases}] 运行 {case['id']}: {case['name']}...", end=" ", flush=True)

            # 运行测试
            test_result = run_single_test(agent_builder, case["input"])

            # 评估
            eval_result = engine.evaluate_case(
                case=case,
                module_name=module_name,
                agent_output=test_result["output"],
                tools_called=test_result["tools_called"],
                latency_sec=test_result["latency_sec"],
                error_msg=test_result["error"],
                user_input=case["input"]
            )
            engine.results.append(eval_result)

            status = "✅" if eval_result.passed else "❌"
            print(f"{status} 得分:{eval_result.total_score:.1f} 延迟:{eval_result.latency_sec:.1f}s")

    # 生成报告
    report = engine.generate_report()
    engine.print_report(report)

    return report


def save_baseline(report: dict, baseline_path: str = None):
    """保存当前报告为基线"""
    if baseline_path is None:
        baseline_path = os.path.join(project_root, "tests", "baseline_report.json")
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 基线已保存: {baseline_path}")


def run_regression(agent_builder, baseline_path: str = None, use_llm_judge: bool = False) -> dict:
    """执行回归测试"""
    if baseline_path is None:
        baseline_path = os.path.join(project_root, "tests", "baseline_report.json")

    print("\n🔄 执行回归测试...")

    # 运行当前测试
    current_report = run_test_suite(agent_builder, use_llm_judge=use_llm_judge)

    # 对比基线
    engine = HarnessEngine(use_llm_judge=use_llm_judge)
    comparison = engine.compare_with_baseline(current_report, baseline_path)

    # 打印回归结果
    summary = comparison.get("summary", {})
    print("\n" + "=" * 60)
    print("  📊 回归对比结果")
    print("=" * 60)
    print(f"  基线通过率: {summary.get('baseline_pass_rate', 'N/A')}%")
    print(f"  当前通过率: {summary.get('current_pass_rate', 'N/A')}%")
    print(f"  通过率变化: {summary.get('pass_rate_diff', 0):+.1f}%")
    print(f"  总变更数: {summary.get('total_changes', 0)}")
    print(f"  回归数: {summary.get('regressions', 0)}")
    print(f"  改进数: {summary.get('improvements', 0)}")

    if comparison.get("regressions"):
        print("\n  ⚠️ 回归项:")
        for r in comparison["regressions"]:
            print(f"    ❌ [{r['case_id']}] {r['case_name']}: {r['baseline_score']} → {r['current_score']} ({r['diff']:+.1f})")

    if comparison.get("improvements"):
        print("\n  🎉 改进项:")
        for imp in comparison["improvements"]:
            print(f"    ✅ [{imp['case_id']}] {imp['case_name']}: {imp['baseline_score']} → {imp['current_score']} ({imp['diff']:+.1f})")

    print("=" * 60)

    # 保存回归报告
    regression_path = os.path.join(project_root, "tests", "reports", f"regression_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(regression_path), exist_ok=True)
    with open(regression_path, "w", encoding="utf-8") as f:
        json.dump({"comparison": comparison, "current_report": current_report}, f, ensure_ascii=False, indent=2)
    print(f"\n  📁 回归报告已保存: {regression_path}")

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Agent自动化测试运行器")
    parser.add_argument("--module", type=str, help="只运行指定模块的测试")
    parser.add_argument("--case-id", type=str, nargs="+", help="只运行指定用例ID")
    parser.add_argument("--baseline", action="store_true", help="与基线对比（回归测试）")
    parser.add_argument("--save-baseline", action="store_true", help="保存当前结果为基线")
    parser.add_argument("--quick", action="store_true", help="快速模式：只运行核心用例")
    parser.add_argument("--llm-judge", action="store_true", help="使用LLM-as-Judge评估（更准确但更慢）")
    args = parser.parse_args()

    # 动态导入 agent builder
    try:
        from agents.agent import build_agent
        print("✅ Agent模块加载成功")
    except ImportError as e:
        print(f"❌ 无法导入Agent模块: {e}")
        sys.exit(1)

    if args.baseline:
        # 回归测试模式
        comparison = run_regression(build_agent, use_llm_judge=args.llm_judge)
        regressions = comparison.get("summary", {}).get("regressions", 0)
        if regressions > 0:
            print(f"\n⚠️ 发现 {regressions} 个回归项，请检查！")
            sys.exit(1)
        else:
            print("\n✅ 回归测试通过，无回归问题")
    else:
        # 常规测试模式
        report = run_test_suite(
            build_agent,
            modules_filter=args.module,
            case_ids_filter=args.case_id,
            use_llm_judge=args.llm_judge,
        )

        # 保存报告
        engine = HarnessEngine(use_llm_judge=args.llm_judge)
        engine.save_report(report)

        if args.save_baseline:
            save_baseline(report)

        # 退出码
        failed = report["summary"]["failed"]
        if failed > 0:
            print(f"\n⚠️ {failed} 个用例失败，请检查！")
            sys.exit(1)
        else:
            print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    main()
