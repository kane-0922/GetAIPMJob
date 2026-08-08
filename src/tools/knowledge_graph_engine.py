"""知识图谱查询引擎 - 提供路径推理、关联分析、能力诊断等图查询能力"""
import os
import json
import logging
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)

GRAPH_FILE = "assets/knowledge_base/ai_product_knowledge_graph.json"


class KnowledgeGraph:
    """AI产品领域知识图谱引擎（单例）"""

    _instance: Optional["KnowledgeGraph"] = None
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self.entities = {}      # id -> entity dict
        self.adj = {}           # id -> [(target_id, relation_type, desc)]
        self.reverse_adj = {}   # id -> [(source_id, relation_type, desc)]
        self._load_graph()
        self._loaded = True

    def _load_graph(self):
        workspace = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        graph_path = os.path.join(workspace, GRAPH_FILE)

        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"加载知识图谱失败: {e}")
            return

        # 加载所有实体
        for category in ["technologies", "skills", "roles", "companies", "products", "topics"]:
            for entity in data.get("entities", {}).get(category, []):
                self.entities[entity["id"]] = entity

        # 加载关系，构建邻接表
        for rel in data.get("relations", []):
            src, tgt, rtype = rel["from"], rel["to"], rel["type"]
            desc = rel.get("desc", "")

            if src not in self.adj:
                self.adj[src] = []
            self.adj[src].append((tgt, rtype, desc))

            if tgt not in self.reverse_adj:
                self.reverse_adj[tgt] = []
            self.reverse_adj[tgt].append((src, rtype, desc))

        logger.info(f"知识图谱加载完成: {len(self.entities)} 个实体, {sum(len(v) for v in self.adj.values())} 条关系")

    def search_entity(self, query: str) -> list:
        """模糊搜索实体，返回匹配的实体列表"""
        query_lower = query.lower()
        results = []
        for eid, entity in self.entities.items():
            name = entity.get("name", "").lower()
            desc = entity.get("desc", "").lower()
            if query_lower in name or query_lower in desc or query_lower in eid:
                results.append(entity)
        return results[:10]

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """获取实体详情"""
        return self.entities.get(entity_id)

    def get_relations(self, entity_id: str) -> dict:
        """获取实体的所有关系（出边和入边）"""
        outgoing = self.adj.get(entity_id, [])
        incoming = self.reverse_adj.get(entity_id, [])
        return {"outgoing": outgoing, "incoming": incoming}

    def find_prerequisites(self, entity_id: str, max_depth: int = 5) -> list:
        """查找学习路径：找到掌握某技术/主题所需的所有前置知识（BFS）"""
        visited = set()
        queue = deque([(entity_id, 0, [])])
        paths = []

        while queue:
            current, depth, path = queue.popleft()
            if current in visited or depth > max_depth:
                continue
            visited.add(current)

            if path:
                paths.append({"entity": current, "depth": depth, "path": path[:]})

            for target, rtype, desc in self.adj.get(current, []):
                if rtype == "requires" and target not in visited:
                    queue.append((target, depth + 1, path + [f"{current} --requires--> {target}"]))

        return paths

    def find_career_path(self, from_role: str) -> list:
        """查找职业发展路径"""
        visited = set()
        queue = deque([(from_role, 0)])
        paths = []

        while queue:
            current, depth = queue.popleft()
            if current in visited or depth > 5:
                continue
            visited.add(current)

            entity = self.entities.get(current, {})
            paths.append({
                "role": current,
                "name": entity.get("name", current),
                "depth": depth,
                "desc": entity.get("desc", ""),
                "experience": entity.get("experience", ""),
            })

            for target, rtype, desc in self.adj.get(current, []):
                if rtype == "leads_to" and target not in visited:
                    queue.append((target, depth + 1))

        return paths

    def get_required_skills(self, role_id: str) -> list:
        """获取某岗位所需的全部技能"""
        skills = []
        for target, rtype, desc in self.adj.get(role_id, []):
            if rtype == "needs_skill":
                skill_entity = self.entities.get(target, {})
                skills.append({
                    "id": target,
                    "name": skill_entity.get("name", target),
                    "desc": skill_entity.get("desc", ""),
                    "category": skill_entity.get("category", ""),
                    "requirement_desc": desc,
                })
        return skills

    def analyze_skill_gap(self, role_id: str, user_skills: list) -> dict:
        """分析用户技能与岗位要求的差距"""
        required = self.get_required_skills(role_id)
        user_skill_lower = [s.lower() for s in user_skills]

        matched = []
        gaps = []
        for skill in required:
            name = skill["name"].lower()
            desc = skill["desc"].lower()
            is_matched = any(
                us in name or us in desc or name in us
                for us in user_skill_lower
            )
            if is_matched:
                matched.append(skill)
            else:
                gaps.append(skill)

        return {
            "role": role_id,
            "total_required": len(required),
            "matched": matched,
            "gaps": gaps,
            "match_rate": f"{len(matched) / len(required) * 100:.0f}%" if required else "N/A",
        }

    def find_related_entities(self, entity_id: str, relation_types: list = None) -> list:
        """查找关联实体（支持按关系类型过滤）"""
        results = []
        for target, rtype, desc in self.adj.get(entity_id, []):
            if relation_types and rtype not in relation_types:
                continue
            target_entity = self.entities.get(target, {})
            results.append({
                "id": target,
                "name": target_entity.get("name", target),
                "type": target_entity.get("type", ""),
                "relation": rtype,
                "desc": desc,
                "direction": "outgoing",
            })
        for source, rtype, desc in self.reverse_adj.get(entity_id, []):
            if relation_types and rtype not in relation_types:
                continue
            source_entity = self.entities.get(source, {})
            results.append({
                "id": source,
                "name": source_entity.get("name", source),
                "type": source_entity.get("type", ""),
                "relation": rtype,
                "desc": desc,
                "direction": "incoming",
            })
        return results

    def get_tech_stack(self, product_id: str) -> list:
        """获取某产品使用的技术栈"""
        techs = []
        for target, rtype, desc in self.adj.get(product_id, []):
            if rtype == "uses_tech":
                tech_entity = self.entities.get(target, {})
                techs.append({
                    "id": target,
                    "name": tech_entity.get("name", target),
                    "desc": tech_entity.get("desc", ""),
                    "relation_desc": desc,
                })
        return techs

    def get_competitors(self, product_id: str) -> list:
        """获取某产品的竞品信息"""
        competitors = []
        for target, rtype, desc in self.adj.get(product_id, []):
            if rtype == "competes_with":
                comp_entity = self.entities.get(target, {})
                competitors.append({
                    "id": target,
                    "name": comp_entity.get("name", target),
                    "desc": comp_entity.get("desc", ""),
                    "relation_desc": desc,
                })
        return competitors


# 全局单例
_kg_instance: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
