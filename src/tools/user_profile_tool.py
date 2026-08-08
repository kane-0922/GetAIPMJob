"""
用户画像持久化管理工具
支持跨会话的用户信息存储、学习进度追踪、面试记录管理
"""
import json
import os
from typing import Optional
from datetime import datetime

from langchain.tools import tool
from postgrest.exceptions import APIError

from storage.database.supabase_client import get_supabase_client


def _get_client():
    """获取Supabase客户端"""
    return get_supabase_client()


def _get_session_id() -> str:
    """获取当前会话ID，从环境变量或生成默认值"""
    return os.getenv("COZE_SESSION_ID", "default_session")


@tool
def save_user_profile(
    name: Optional[str] = None,
    identity_type: Optional[str] = None,
    education: Optional[str] = None,
    target_positions: Optional[str] = None,
    skills_mastered: Optional[str] = None,
    skills_to_improve: Optional[str] = None,
    resume_data: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """保存或更新用户画像信息。

    当从用户对话中提取到以下信息时调用此工具：
    - 基本信息：姓名、身份类型(intern实习/campus校招/experienced社招)
    - 教育背景：学历、学校、专业、毕业年份
    - 目标岗位：期望投递的岗位列表
    - 技能评估：已掌握技能、待提升技能
    - 简历数据：解析后的简历结构化数据
    - 备注：Agent观察到的其他重要信息

    Args:
        name: 用户姓名
        identity_type: 身份类型，可选值: intern(实习生), campus(校招), experienced(社招)
        education: 教育背景JSON字符串，格式: {"degree": "本科", "school": "xx大学", "major": "计算机", "graduation_year": 2025}
        target_positions: 目标岗位列表JSON字符串，格式: ["AI产品经理", "产品经理"]
        skills_mastered: 已掌握技能列表JSON字符串，格式: ["RAG", "Prompt工程", "数据分析"]
        skills_to_improve: 待提升技能列表JSON字符串，格式: ["Agent设计", "大模型微调"]
        resume_data: 简历结构化数据JSON字符串
        notes: Agent备注信息
    """
    client = _get_client()
    session_id = _get_session_id()

    # 构建更新数据
    update_data = {"session_id": session_id, "updated_at": datetime.now().isoformat()}

    if name is not None:
        update_data["name"] = name
    if identity_type is not None:
        update_data["identity_type"] = identity_type
    if education is not None:
        try:
            update_data["education"] = json.loads(education) if isinstance(education, str) else education
        except json.JSONDecodeError:
            update_data["education"] = {"raw": education}
    if target_positions is not None:
        try:
            update_data["target_positions"] = json.loads(target_positions) if isinstance(target_positions, str) else target_positions
        except json.JSONDecodeError:
            update_data["target_positions"] = [target_positions]
    if skills_mastered is not None:
        try:
            update_data["skills_mastered"] = json.loads(skills_mastered) if isinstance(skills_mastered, str) else skills_mastered
        except json.JSONDecodeError:
            update_data["skills_mastered"] = [skills_mastered]
    if skills_to_improve is not None:
        try:
            update_data["skills_to_improve"] = json.loads(skills_to_improve) if isinstance(skills_to_improve, str) else skills_to_improve
        except json.JSONDecodeError:
            update_data["skills_to_improve"] = [skills_to_improve]
    if resume_data is not None:
        try:
            update_data["resume_data"] = json.loads(resume_data) if isinstance(resume_data, str) else resume_data
        except json.JSONDecodeError:
            update_data["resume_data"] = {"raw": resume_data}
    if notes is not None:
        update_data["notes"] = notes

    try:
        # 先查询是否已存在
        existing = client.table("user_profiles").select("id").eq("session_id", session_id).maybe_single().execute()

        if existing and existing.data:
            # 更新已有记录
            response = client.table("user_profiles").update(update_data).eq("session_id", session_id).execute()
            return f"✅ 用户画像已更新，会话ID: {session_id}"
        else:
            # 创建新记录
            update_data["created_at"] = datetime.now().isoformat()
            response = client.table("user_profiles").insert(update_data).execute()
            return f"✅ 用户画像已创建，会话ID: {session_id}"
    except APIError as e:
        raise Exception(f"保存用户画像失败: {e.message}")


@tool
def get_user_profile() -> str:
    """获取当前用户的画像信息。

    在对话开始时调用此工具，检查是否已有该用户的历史画像数据。
    如果返回数据，说明是老用户，可以基于历史画像提供个性化服务。
    如果返回空，说明是新用户，需要引导用户填写基本信息。

    Returns:
        用户画像信息的JSON字符串，包含基本信息、技能评估、学习进度、面试记录等。
        如果没有历史记录，返回"无历史记录"。
    """
    client = _get_client()
    session_id = _get_session_id()

    try:
        response = client.table("user_profiles").select(
            "name, identity_type, education, target_positions, "
            "skills_mastered, skills_to_improve, resume_data, "
            "learning_progress, interview_history, notes, created_at, updated_at"
        ).eq("session_id", session_id).maybe_single().execute()

        if response is None or not response.data:
            return "无历史记录"

        profile: dict = response.data  # type: ignore
        result = {
            "基本信息": {
                "姓名": profile.get("name"),
                "身份类型": profile.get("identity_type"),
                "教育背景": profile.get("education"),
                "目标岗位": profile.get("target_positions"),
            },
            "技能评估": {
                "已掌握": profile.get("skills_mastered"),
                "待提升": profile.get("skills_to_improve"),
            },
            "简历数据": profile.get("resume_data"),
            "学习进度": profile.get("learning_progress"),
            "面试记录": profile.get("interview_history"),
            "备注": profile.get("notes"),
            "创建时间": profile.get("created_at"),
            "更新时间": profile.get("updated_at"),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except APIError as e:
        raise Exception(f"查询用户画像失败: {e.message}")


@tool
def update_learning_progress(
    topic: str,
    status: str = "studied",
    mastery_level: Optional[str] = None
) -> str:
    """更新用户的学习进度记录。

    当用户完成某个知识点的学习或进行模拟面试后，调用此工具记录进度。

    Args:
        topic: 学习的主题，如"RAG技术"、"Prompt工程"、"模拟面试-校招"
        status: 学习状态，可选值: studied(已学习), mastered(已掌握), weak(薄弱需加强)
        mastery_level: 掌握程度描述，如"理解基本概念"、"能独立设计RAG系统"
    """
    client = _get_client()
    session_id = _get_session_id()

    try:
        # 获取当前学习进度
        response = client.table("user_profiles").select("learning_progress").eq("session_id", session_id).maybe_single().execute()

        if response is None or not response.data:
            # 没有画像记录，先创建一个
            learning_progress = {
                "topics_studied": [{"topic": topic, "status": status, "mastery_level": mastery_level, "date": datetime.now().isoformat()}],
                "total_topics": 1,
                "mastered_count": 1 if status == "mastered" else 0,
            }
            client.table("user_profiles").insert({
                "session_id": session_id,
                "learning_progress": learning_progress,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
            return f"✅ 已记录学习进度: {topic} ({status})"

        # 更新已有记录
        resp_data: dict = response.data  # type: ignore
        current_progress: dict = resp_data.get("learning_progress") or {"topics_studied": [], "total_topics": 0, "mastered_count": 0}
        topics_studied: list = current_progress.get("topics_studied", [])

        # 检查是否已记录过该主题
        found = False
        for t in topics_studied:
            if t.get("topic") == topic:
                t["status"] = status
                t["mastery_level"] = mastery_level
                t["date"] = datetime.now().isoformat()
                found = True
                break

        if not found:
            topics_studied.append({
                "topic": topic,
                "status": status,
                "mastery_level": mastery_level,
                "date": datetime.now().isoformat()
            })

        # 更新统计
        current_progress["topics_studied"] = topics_studied
        current_progress["total_topics"] = len(topics_studied)
        current_progress["mastered_count"] = sum(1 for t in topics_studied if t.get("status") == "mastered")

        client.table("user_profiles").update({
            "learning_progress": current_progress,
            "updated_at": datetime.now().isoformat()
        }).eq("session_id", session_id).execute()

        return f"✅ 学习进度已更新: {topic} ({status})，已学习 {current_progress['total_topics']} 个主题"
    except APIError as e:
        raise Exception(f"更新学习进度失败: {e.message}")


@tool
def save_interview_record(
    interview_type: str,
    score_summary: str,
    strengths: Optional[str] = None,
    weaknesses: Optional[str] = None,
    suggestions: Optional[str] = None
) -> str:
    """保存模拟面试记录。

    当模拟面试结束后，调用此工具保存面试评价报告。

    Args:
        interview_type: 面试类型，如"校招-AI产品经理"、"社招-高级AI产品经理"
        score_summary: 评分摘要JSON字符串，格式: {"专业知识": 80, "产品思维": 75, "表达能力": 85, "综合评分": 80}
        strengths: 优势描述
        weaknesses: 待改进描述
        suggestions: 改进建议
    """
    client = _get_client()
    session_id = _get_session_id()

    try:
        # 解析评分
        try:
            scores = json.loads(score_summary) if isinstance(score_summary, str) else score_summary
        except json.JSONDecodeError:
            scores = {"综合评分": score_summary}

        # 解析列表
        try:
            strengths_list = json.loads(strengths) if strengths and isinstance(strengths, str) else ([strengths] if strengths else [])
        except json.JSONDecodeError:
            strengths_list = [strengths] if strengths else []

        try:
            weaknesses_list = json.loads(weaknesses) if weaknesses and isinstance(weaknesses, str) else ([weaknesses] if weaknesses else [])
        except json.JSONDecodeError:
            weaknesses_list = [weaknesses] if weaknesses else []

        interview_record = {
            "interview_type": interview_type,
            "scores": scores,
            "strengths": strengths_list,
            "weaknesses": weaknesses_list,
            "suggestions": suggestions,
            "date": datetime.now().isoformat()
        }

        # 获取现有面试记录
        response = client.table("user_profiles").select("interview_history").eq("session_id", session_id).maybe_single().execute()

        if response is None or not response.data:
            # 没有画像，创建新记录
            client.table("user_profiles").insert({
                "session_id": session_id,
                "interview_history": [interview_record],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).execute()
        else:
            # 追加到现有记录
            resp_data2: dict = response.data  # type: ignore
            history: list = resp_data2.get("interview_history") or []
            history.append(interview_record)
            client.table("user_profiles").update({
                "interview_history": history,
                "updated_at": datetime.now().isoformat()
            }).eq("session_id", session_id).execute()

        return f"✅ 面试记录已保存: {interview_type}，综合评分 {scores.get('综合评分', 'N/A')}"
    except APIError as e:
        raise Exception(f"保存面试记录失败: {e.message}")
