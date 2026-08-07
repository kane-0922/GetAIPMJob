"""企业背调工具 - 通过联网搜索获取企业信息并生成投递建议"""
import logging
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk import SearchClient

logger = logging.getLogger(__name__)


@tool
def research_company(company_name: str) -> str:
    """查询企业背景信息，包括注册资本、员工规模、参保人数、融资情况、业务范围等客观数据，并生成投递建议。
    
    Args:
        company_name: 公司名称，如"字节跳动"、"百度"、"商汤科技"
    
    Returns:
        企业背调报告，包含公司基本信息、经营状况、风险提示和投递建议
    """
    ctx = request_context.get() or new_context(method="research_company")
    logger.info(f"开始企业背调: {company_name}")

    try:
        client = SearchClient(ctx=ctx)

        # 搜索企业基本信息
        query_basic = f"{company_name} 公司注册资本 员工规模 参保人数 企业信息"
        resp_basic = client.web_search(query=query_basic, count=5)

        basic_info_parts = []
        if resp_basic.summary:
            basic_info_parts.append(f"【企业概况】\n{resp_basic.summary}")
        if resp_basic.web_items:
            for item in resp_basic.web_items[:5]:
                snippet = item.snippet or ""
                basic_info_parts.append(f"- [{item.title}]({item.url}): {snippet[:200]}")

        # 搜索融资与经营状况
        query_finance = f"{company_name} 融资轮次 估值 经营状况 最新消息"
        resp_finance = client.web_search(query=query_finance, count=5)

        finance_parts = []
        if resp_finance.summary:
            finance_parts.append(f"【融资与经营状况】\n{resp_finance.summary}")
        if resp_finance.web_items:
            for item in resp_finance.web_items[:3]:
                snippet = item.snippet or ""
                finance_parts.append(f"- [{item.title}]({item.url}): {snippet[:200]}")

        # 搜索企业口碑与风险
        query_risk = f"{company_name} 裁员 口碑 评价 风险 劳动纠纷"
        resp_risk = client.web_search(query=query_risk, count=5)

        risk_parts = []
        if resp_risk.summary:
            risk_parts.append(f"【企业口碑与风险】\n{resp_risk.summary}")
        if resp_risk.web_items:
            for item in resp_risk.web_items[:3]:
                snippet = item.snippet or ""
                risk_parts.append(f"- [{item.title}]({item.url}): {snippet[:200]}")

        # 组装报告
        report_sections = [f"=== {company_name} 企业背调报告 ===\n"]
        if basic_info_parts:
            report_sections.append("\n".join(basic_info_parts))
        if finance_parts:
            report_sections.append("\n".join(finance_parts))
        if risk_parts:
            report_sections.append("\n".join(risk_parts))

        report_sections.append("\n【投递建议】")
        report_sections.append("请根据以上信息综合判断：")
        report_sections.append("1. 公司发展前景与行业地位")
        report_sections.append("2. 企业经营稳定性（是否有裁员、资金链等问题）")
        report_sections.append("3. 企业口碑与员工评价")
        report_sections.append("4. 岗位与个人发展的匹配度")

        report = "\n\n".join(report_sections)
        logger.info(f"企业背调完成: {company_name}")
        return report

    except Exception as e:
        logger.error(f"企业背调异常: {e}")
        return f"企业背调失败: {str(e)}，请稍后重试。"
