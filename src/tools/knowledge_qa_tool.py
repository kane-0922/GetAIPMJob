"""知识库检索问答工具 - 基于RAG的AI产品专业知识问答"""
import logging
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk import KnowledgeClient, Config

logger = logging.getLogger(__name__)


@tool
def search_knowledge(query: str) -> str:
    """检索AI产品领域专业知识库，包括AI产品设计、Prompt工程、RAG技术、Agent架构、大模型基础、面试技巧、行业术语、典型案例等知识。
    
    Args:
        query: 用户的专业问题，如"什么是RAG"、"AI产品经理需要什么能力"、"如何设计推荐系统"
    
    Returns:
        从知识库中检索到的相关知识内容
    """
    ctx = request_context.get() or new_context(method="search_knowledge")
    logger.info(f"知识库检索: {query}")

    try:
        config = Config()
        client = KnowledgeClient(config=config, ctx=ctx)

        response = client.search(
            query=query,
            top_k=5,
            min_score=0.3
        )

        if response.code == 0 and response.chunks:
            results = []
            for i, chunk in enumerate(response.chunks):
                results.append(f"【知识片段 {i+1}】(相关度: {chunk.score:.2f})\n{chunk.content}")
            return "\n\n---\n\n".join(results)
        else:
            return "未在知识库中找到相关内容，请尝试换个关键词或表述方式。"

    except Exception as e:
        logger.error(f"知识库检索异常: {e}")
        return f"知识库检索失败: {str(e)}"
