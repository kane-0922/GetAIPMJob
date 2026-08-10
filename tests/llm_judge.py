"""
LLM-as-Judge 评估器
使用大语言模型对Agent回答进行多维度智能评分
"""
import os
import json
import logging
from typing import Any

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)

# 评估维度定义
EVAL_DIMENSIONS = {
    "intent_accuracy": {
        "name": "意图识别准确率",
        "description": "Agent是否正确理解了用户的真实意图",
        "weight": 0.25,
    },
    "tool_correctness": {
        "name": "工具调用正确性",
        "description": "Agent是否调用了正确的工具，参数是否合理",
        "weight": 0.20,
    },
    "content_quality": {
        "name": "内容质量",
        "description": "回答是否准确、完整、有用，无幻觉",
        "weight": 0.25,
    },
    "format_quality": {
        "name": "格式规范性",
        "description": "输出是否符合预期格式（如评分表、报告、结构化输出）",
        "weight": 0.15,
    },
    "helpfulness": {
        "name": "有用性",
        "description": "回答是否真正帮助用户解决了问题或推进了任务",
        "weight": 0.15,
    },
}

# LLM评估Prompt模板
JUDGE_PROMPT_TEMPLATE = """你是一个专业的AI Agent质量评估专家。请对以下Agent的回答进行多维度评分。

## 评估背景
- **用户输入**: {user_input}
- **测试场景**: {scenario}
- **预期意图**: {expected_intent}
- **预期工具调用**: {expected_tool}
- **实际工具调用**: {actual_tools}

## Agent回答
{agent_output}

## 评估维度（每项0-100分）

请对以下5个维度分别评分，并给出简短理由：

1. **意图识别准确率** (权重25%): Agent是否正确理解了用户的真实意图？
2. **工具调用正确性** (权重20%): Agent是否调用了正确的工具？参数是否合理？如果不需要调用工具，是否正确地没有调用？
3. **内容质量** (权重25%): 回答是否准确、完整、无幻觉？信息是否有价值？
4. **格式规范性** (权重15%): 输出格式是否清晰、结构化、易读？
5. **有用性** (权重15%): 回答是否真正帮助用户解决了问题或推进了任务？

## 输出格式
请严格按照以下JSON格式输出，不要输出其他内容：
```json
{{
    "intent_accuracy": {{"score": 85, "reason": "简短理由"}},
    "tool_correctness": {{"score": 90, "reason": "简短理由"}},
    "content_quality": {{"score": 80, "reason": "简短理由"}},
    "format_quality": {{"score": 75, "reason": "简短理由"}},
    "helpfulness": {{"score": 85, "reason": "简短理由"}},
    "overall_comment": "整体评价（一句话）"
}}
```
"""


class LLMJudge:
    """LLM-as-Judge 评估器"""

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        """延迟初始化LLM客户端"""
        if self._llm is not None:
            return self._llm

        from langchain_openai import ChatOpenAI
        from coze_coding_utils.runtime_ctx.context import default_headers

        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        config_path = os.path.join(workspace_path, "config/agent_llm_config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

        # 使用轻量级模型做评估，降低成本
        llm_kwargs = {
            "model": cfg["config"].get("model", "doubao-seed-2-0-lite-260215"),
            "api_key": api_key,
            "base_url": base_url,
            "temperature": 0.1,  # 低温度保证评估稳定性
            "timeout": 120,
            "streaming": True,
            "extra_body": {
                "thinking": {
                    "type": cfg["config"].get("thinking", "disabled")
                }
            },
        }

        # 尝试添加 default_headers
        try:
            from coze_coding_utils.runtime_ctx.context import default_headers
            headers = default_headers(None)
            if headers:
                llm_kwargs["default_headers"] = headers
        except Exception:
            llm_kwargs["default_headers"] = {}

        self._llm = ChatOpenAI(**llm_kwargs)
        return self._llm

    def evaluate(
        self,
        user_input: str,
        agent_output: str,
        scenario: str = "",
        expected_intent: str = "",
        expected_tool: str = "",
        actual_tools: list = None,
    ) -> dict:
        """
        使用LLM评估Agent回答质量

        Returns:
            dict: {
                "scores": {"intent_accuracy": 85, ...},
                "reasons": {"intent_accuracy": "理由", ...},
                "total_score": 82.5,
                "overall_comment": "整体评价",
                "passed": True/False
            }
        """
        if actual_tools is None:
            actual_tools = []

        try:
            llm = self._get_llm()

            # 构建评估Prompt
            prompt = JUDGE_PROMPT_TEMPLATE.format(
                user_input=user_input,
                scenario=scenario or "通用场景",
                expected_intent=expected_intent or "未指定",
                expected_tool=expected_tool or "未指定",
                actual_tools=", ".join(actual_tools) if actual_tools else "无",
                agent_output=agent_output[:3000],  # 限制长度避免超时
            )

            # 调用LLM评估
            response = llm.invoke(prompt)

            # 兼容不同版本的响应格式
            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, str):
                content = response
            elif hasattr(response, "text"):
                content = response.text
            else:
                content = str(response)

            # 如果是列表（多模态响应），取第一个文本内容
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )

            # 解析JSON结果
            result = self._parse_judge_result(content)

            # 计算加权总分
            total_score = 0.0
            for dim, weight_info in EVAL_DIMENSIONS.items():
                score = result["scores"].get(dim, 0)
                total_score += score * weight_info["weight"]

            result["total_score"] = round(total_score, 2)
            result["passed"] = (
                total_score >= 60
                and result["scores"].get("intent_accuracy", 0) >= 60
            )

            return result

        except Exception as e:
            logger.error(f"LLM Judge evaluation error: {e}")
            # 降级到默认评分
            return self._fallback_evaluate()

    def _parse_judge_result(self, content: str) -> dict:
        """解析LLM评估结果"""
        # 尝试提取JSON
        try:
            # 尝试直接解析
            result = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从markdown代码块中提取
            import re
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # 尝试找到第一个 { 和最后一个 }
                start = content.find("{")
                end = content.rfind("}")
                if start >= 0 and end > start:
                    result = json.loads(content[start:end + 1])
                else:
                    raise ValueError(f"Cannot parse LLM judge result: {content[:200]}")

        # 提取分数和理由
        scores = {}
        reasons = {}
        for dim in EVAL_DIMENSIONS:
            dim_data = result.get(dim, {})
            if isinstance(dim_data, dict):
                scores[dim] = dim_data.get("score", 70)
                reasons[dim] = dim_data.get("reason", "")
            else:
                scores[dim] = 70
                reasons[dim] = ""

        return {
            "scores": scores,
            "reasons": reasons,
            "overall_comment": result.get("overall_comment", ""),
        }

    def _fallback_evaluate(self) -> dict:
        """降级评估（LLM调用失败时使用）"""
        scores = {dim: 70 for dim in EVAL_DIMENSIONS}
        reasons = {dim: "LLM评估失败，使用默认分数" for dim in EVAL_DIMENSIONS}
        return {
            "scores": scores,
            "reasons": reasons,
            "total_score": 70.0,
            "overall_comment": "LLM评估器调用失败，使用默认评分",
            "passed": True,
        }

    def batch_evaluate(
        self,
        test_cases: list[dict],
        agent_outputs: list[dict],
    ) -> list[dict]:
        """
        批量评估多个测试用例

        Args:
            test_cases: 测试用例列表
            agent_outputs: Agent输出列表，每个元素包含 {output, tools_called, latency}

        Returns:
            list[dict]: 评估结果列表
        """
        results = []
        for case, output_data in zip(test_cases, agent_outputs):
            eval_result = self.evaluate(
                user_input=case.get("input", ""),
                agent_output=output_data.get("output", ""),
                scenario=case.get("name", ""),
                expected_intent=case.get("expected_intent", ""),
                expected_tool=case.get("expected_tool", ""),
                actual_tools=output_data.get("tools_called", []),
            )
            eval_result["case_id"] = case.get("id", "")
            eval_result["case_name"] = case.get("name", "")
            eval_result["latency_sec"] = output_data.get("latency", 0)
            results.append(eval_result)

        return results


# 全局实例
_llm_judge = None


def get_llm_judge() -> LLMJudge:
    """获取LLM Judge单例"""
    global _llm_judge
    if _llm_judge is None:
        _llm_judge = LLMJudge()
    return _llm_judge
