"""简历解析工具 - 支持Word/PDF/TXT格式简历上传与解析"""
import os
import logging
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_dev_sdk.fetch import FetchClient

logger = logging.getLogger(__name__)


def _extract_text_from_url(url: str, ctx) -> str:
    """通过FetchClient从URL提取文档文本内容"""
    try:
        client = FetchClient(ctx=ctx)
        response = client.fetch(url=url)
        if response.status_code != 0:
            return f"文档获取失败: {response.status_message}"
        text_parts = []
        for item in response.content:
            if item.type == "text":
                text_parts.append(item.text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"文档解析异常: {e}")
        return f"文档解析异常: {str(e)}"


def _parse_local_file(file_path: str) -> str:
    """解析本地文件（PDF/Word/TXT）"""
    if not os.path.exists(file_path):
        return f"文件不存在: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
        elif ext in (".doc", ".docx"):
            from docx2python import docx2python
            with docx2python(file_path) as doc:
                return doc.text
        else:
            return f"不支持的文件格式: {ext}，仅支持 .pdf, .doc, .docx, .txt"
    except Exception as e:
        logger.error(f"文件解析异常: {e}")
        return f"文件解析失败: {str(e)}"


@tool
def parse_resume(file_url: str) -> str:
    """解析用户上传的简历文件（支持Word/PDF/TXT格式），提取个人信息与经历数据。
    
    Args:
        file_url: 简历文件的URL地址（支持.pdf, .doc, .docx, .txt格式）
    
    Returns:
        解析后的简历文本内容，包含个人信息、教育经历、工作经历等
    """
    ctx = request_context.get() or new_context(method="parse_resume")
    logger.info(f"开始解析简历: {file_url}")

    resume_text = _extract_text_from_url(file_url, ctx)

    if resume_text.startswith("文档获取失败") or resume_text.startswith("文档解析异常"):
        return resume_text

    if not resume_text.strip():
        return "简历内容为空，请检查文件是否正确上传。"

    result = f"=== 简历原始内容 ===\n{resume_text}\n=== 内容结束 ==="
    logger.info(f"简历解析完成，内容长度: {len(resume_text)} 字符")
    return result
