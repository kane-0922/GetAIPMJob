"""知识库初始化脚本 - 将AI产品领域知识导入向量数据库"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_knowledge_base():
    from coze_coding_dev_sdk import KnowledgeClient, Config, KnowledgeDocument, DataSourceType, ChunkConfig
    from coze_coding_utils.runtime_ctx.context import new_context

    ctx = new_context(method="knowledge_init")
    config = Config()
    client = KnowledgeClient(config=config, ctx=ctx)

    workspace = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    kb_dir = os.path.join(workspace, "assets", "knowledge_base")

    files = [
        "ai_product_knowledge.txt",
        "interview_questions.txt",
        "industry_terms.txt",
        "case_studies.txt",
    ]

    chunk_config = ChunkConfig(
        separator="\n\n",
        max_tokens=800,
        remove_extra_spaces=False
    )

    for fname in files:
        fpath = os.path.join(kb_dir, fname)
        if not os.path.exists(fpath):
            logger.warning(f"File not found: {fpath}")
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by Q&A pairs or sections for better chunking
        sections = []
        current_section = []
        for line in content.split("\n"):
            if line.startswith("Q") and ":" in line[:10] and current_section:
                sections.append("\n".join(current_section))
                current_section = [line]
            elif line.startswith("案例") and ":" in line and current_section:
                sections.append("\n".join(current_section))
                current_section = [line]
            elif line.startswith("---") and current_section:
                sections.append("\n".join(current_section))
                current_section = []
            else:
                current_section.append(line)
        if current_section:
            sections.append("\n".join(current_section))

        # Filter out empty or very short sections
        sections = [s.strip() for s in sections if len(s.strip()) > 20]

        logger.info(f"Processing {fname}: {len(sections)} sections")

        # Import in batches
        batch_size = 10
        for i in range(0, len(sections), batch_size):
            batch = sections[i:i+batch_size]
            docs = [
                KnowledgeDocument(
                    source=DataSourceType.TEXT,
                    raw_data=section,
                )
                for section in batch
            ]

            try:
                response = client.add_documents(
                    documents=docs,
                    table_name="coze_doc_knowledge",
                    chunk_config=chunk_config
                )
                if response.code == 0:
                    logger.info(f"Batch {i//batch_size + 1}: imported {len(docs)} docs successfully")
                else:
                    logger.error(f"Batch {i//batch_size + 1}: import failed: {response.msg}")
            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1}: error: {e}")

    logger.info("Knowledge base initialization completed!")


if __name__ == "__main__":
    init_knowledge_base()
