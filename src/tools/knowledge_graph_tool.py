"""知识图谱查询工具 - 基于GraphRAG的结构化知识推理能力"""
import json
import logging
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from tools.knowledge_graph_engine import get_knowledge_graph

logger = logging.getLogger(__name__)


@tool
def query_knowledge_graph(query_type: str, query: str, extra: str = "") -> str:
    """查询AI产品领域知识图谱，支持多种结构化推理能力。
    
    与向量检索(RAG)互补，知识图谱擅长关系推理和路径分析。
    
    Args:
        query_type: 查询类型，支持以下值：
            - "search": 模糊搜索实体（技术、岗位、产品、公司等）
            - "prerequisites": 查找学习某技术的前置知识路径
            - "career_path": 查找某岗位的职业发展路径
            - "skill_gap": 分析用户技能与目标岗位的差距（extra参数传入用户已有技能，逗号分隔）
            - "related": 查找某实体的关联实体（技术、产品、竞品等）
            - "tech_stack": 查看某产品使用的技术栈
            - "competitors": 查看某产品的竞品信息
            - "skills_for_role": 获取某岗位所需的全部技能
        query: 查询关键词或实体名称，如"RAG"、"AI产品经理"、"豆包"
        extra: 额外参数（仅skill_gap类型使用，传入用户已有技能，逗号分隔）
    
    Returns:
        结构化的图谱查询结果
    """
    ctx = request_context.get() or new_context(method="query_knowledge_graph")
    logger.info(f"知识图谱查询: type={query_type}, query={query}")

    try:
        kg = get_knowledge_graph()

        if query_type == "search":
            results = kg.search_entity(query)
            if not results:
                return f"未找到与「{query}」相关的实体。请尝试其他关键词。"
            output = [f"找到 {len(results)} 个相关实体：\n"]
            for i, entity in enumerate(results, 1):
                output.append(f"{i}. [{entity.get('type', '')}] {entity.get('name', '')}")
                output.append(f"   {entity.get('desc', '')}")
                # 显示关系
                relations = kg.get_relations(entity["id"])
                if relations["outgoing"]:
                    rel_strs = []
                    for tgt, rtype, desc in relations["outgoing"][:5]:
                        tgt_entity = kg.get_entity(tgt)
                        tgt_name = tgt_entity.get("name", tgt) if tgt_entity else tgt
                        rel_strs.append(f"--[{rtype}]--> {tgt_name}")
                    output.append(f"   关系: {'; '.join(rel_strs)}")
                output.append("")
            return "\n".join(output)

        elif query_type == "prerequisites":
            entities = kg.search_entity(query)
            if not entities:
                return f"未找到「{query}」相关实体，无法生成学习路径。"
            target = entities[0]
            paths = kg.find_prerequisites(target["id"])
            if not paths:
                return f"「{target['name']}」没有前置依赖，可以直接学习。"
            output = [f"📚 「{target['name']}」的学习路径（前置知识）：\n"]
            output.append(f"目标: {target['name']} - {target.get('desc', '')}\n")
            sorted_paths = sorted(paths, key=lambda x: x["depth"])
            by_depth = {}
            for p in sorted_paths:
                d = p["depth"]
                if d not in by_depth:
                    by_depth[d] = []
                entity = kg.get_entity(p["entity"])
                name = entity.get("name", p["entity"]) if entity else p["entity"]
                desc = entity.get("desc", "") if entity else ""
                by_depth[d].append((name, desc))
            for depth in sorted(by_depth.keys()):
                output.append(f"第{depth}层前置知识:")
                for name, desc in by_depth[depth]:
                    output.append(f"  - {name}: {desc}")
                output.append("")
            return "\n".join(output)

        elif query_type == "career_path":
            entities = kg.search_entity(query)
            role_entity = None
            for e in entities:
                if e.get("type") == "role":
                    role_entity = e
                    break
            if not role_entity:
                return f"未找到「{query}」相关岗位。可尝试：AI产品实习生、初级AI产品经理、AI产品经理、高级AI产品经理。"
            paths = kg.find_career_path(role_entity["id"])
            output = [f"🚀 「{role_entity['name']}」的职业发展路径：\n"]
            for p in paths:
                indent = "  " * p["depth"]
                output.append(f"{indent}{'→ ' if p['depth'] > 0 else '📍 '}{p['name']}")
                output.append(f"{indent}  经验要求: {p.get('experience', 'N/A')}")
                output.append(f"{indent}  {p.get('desc', '')}")
                # 获取该岗位所需技能
                skills = kg.get_required_skills(p["role"])
                if skills:
                    skill_names = [s["name"] for s in skills]
                    output.append(f"{indent}  核心技能: {', '.join(skill_names)}")
                output.append("")
            return "\n".join(output)

        elif query_type == "skill_gap":
            entities = kg.search_entity(query)
            role_entity = None
            for e in entities:
                if e.get("type") == "role":
                    role_entity = e
                    break
            if not role_entity:
                return f"未找到「{query}」相关岗位。"
            user_skills = [s.strip() for s in extra.split(",") if s.strip()] if extra else []
            gap_result = kg.analyze_skill_gap(role_entity["id"], user_skills)
            output = [f"📊 「{role_entity['name']}」技能差距分析：\n"]
            output.append(f"目标岗位: {role_entity['name']}")
            output.append(f"总需技能: {gap_result['total_required']}项")
            output.append(f"匹配率: {gap_result['match_rate']}\n")
            if gap_result["matched"]:
                output.append("✅ 已具备的技能:")
                for s in gap_result["matched"]:
                    output.append(f"  - {s['name']}: {s['desc']}")
                output.append("")
            if gap_result["gaps"]:
                output.append("⚠️ 需要补充的技能:")
                for s in gap_result["gaps"]:
                    output.append(f"  - {s['name']}: {s['desc']}")
                    output.append(f"    要求: {s['requirement_desc']}")
                output.append("")
            if not user_skills:
                output.append("💡 提示: 传入用户已有技能（extra参数，逗号分隔）可获得更精准的差距分析。")
            return "\n".join(output)

        elif query_type == "related":
            entities = kg.search_entity(query)
            if not entities:
                return f"未找到「{query}」相关实体。"
            target = entities[0]
            related = kg.find_related_entities(target["id"])
            if not related:
                return f"「{target['name']}」暂无关联实体。"
            output = [f"🔗 「{target['name']}」的关联实体：\n"]
            outgoing = [r for r in related if r["direction"] == "outgoing"]
            incoming = [r for r in related if r["direction"] == "incoming"]
            if outgoing:
                output.append("→ 关联（出边）:")
                for r in outgoing:
                    output.append(f"  - [{r['relation']}] {r['name']}: {r['desc']}")
                output.append("")
            if incoming:
                output.append("← 被关联（入边）:")
                for r in incoming:
                    output.append(f"  - [{r['relation']}] {r['name']}: {r['desc']}")
            return "\n".join(output)

        elif query_type == "tech_stack":
            entities = kg.search_entity(query)
            product_entity = None
            for e in entities:
                if e.get("type") == "product":
                    product_entity = e
                    break
            if not product_entity:
                return f"未找到「{query}」相关产品。"
            techs = kg.get_tech_stack(product_entity["id"])
            output = [f"🛠️ 「{product_entity['name']}」的技术栈：\n"]
            output.append(f"产品: {product_entity.get('desc', '')}\n")
            for t in techs:
                output.append(f"  - {t['name']}: {t['desc']}")
            # 竞品
            competitors = kg.get_competitors(product_entity["id"])
            if competitors:
                output.append(f"\n竞品:")
                for c in competitors:
                    output.append(f"  - {c['name']}: {c['desc']}")
            return "\n".join(output)

        elif query_type == "competitors":
            entities = kg.search_entity(query)
            product_entity = None
            for e in entities:
                if e.get("type") == "product":
                    product_entity = e
                    break
            if not product_entity:
                return f"未找到「{query}」相关产品。"
            competitors = kg.get_competitors(product_entity["id"])
            techs = kg.get_tech_stack(product_entity["id"])
            output = [f"🏆 「{product_entity['name']}」竞品分析：\n"]
            output.append(f"产品: {product_entity.get('desc', '')}\n")
            if techs:
                output.append("核心技术:")
                for t in techs:
                    output.append(f"  - {t['name']}")
                output.append("")
            if competitors:
                output.append("竞品列表:")
                for c in competitors:
                    output.append(f"  - {c['name']}: {c['desc']}")
                    # 获取竞品的技术栈
                    comp_techs = kg.get_tech_stack(c["id"])
                    if comp_techs:
                        tech_names = [t["name"] for t in comp_techs]
                        output.append(f"    技术栈: {', '.join(tech_names)}")
            else:
                output.append("暂无竞品信息。")
            return "\n".join(output)

        elif query_type == "skills_for_role":
            entities = kg.search_entity(query)
            role_entity = None
            for e in entities:
                if e.get("type") == "role":
                    role_entity = e
                    break
            if not role_entity:
                return f"未找到「{query}」相关岗位。"
            skills = kg.get_required_skills(role_entity["id"])
            output = [f"📋 「{role_entity['name']}」所需技能清单：\n"]
            output.append(f"岗位: {role_entity.get('desc', '')}")
            output.append(f"经验要求: {role_entity.get('experience', 'N/A')}\n")
            by_category = {}
            for s in skills:
                cat = s.get("category", "其他")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(s)
            for cat, cat_skills in by_category.items():
                output.append(f"【{cat}】")
                for s in cat_skills:
                    output.append(f"  - {s['name']}: {s['desc']}")
                output.append("")
            return "\n".join(output)

        else:
            return f"不支持的查询类型: {query_type}。支持的类型: search, prerequisites, career_path, skill_gap, related, tech_stack, competitors, skills_for_role"

    except Exception as e:
        logger.error(f"知识图谱查询异常: {e}")
        return f"知识图谱查询失败: {str(e)}"
