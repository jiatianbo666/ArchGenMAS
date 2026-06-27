"""结果查询接口"""
from fastapi import APIRouter, HTTPException

from orchestrator.mediator import mediator
from services.c4_generator import get_c4_plantuml_all, get_view_plantuml_all
from services.view_generator import extract_views_summary
from services.risk_analyzer import get_risk_summary_for_display, count_risks_by_level, count_risks_by_dimension

router = APIRouter()


@router.get("/result/{project_id}")
async def get_result(project_id: str):
    """获取项目完整生成结果"""
    blackboard = mediator.get_blackboard(project_id)
    # 内存没有就尝试从磁盘加载（后端重启后恢复）
    if not blackboard:
        blackboard = mediator.load_from_disk(project_id)
    if not blackboard:
        raise HTTPException(404, "项目不存在")

    result = {
        "project_id": blackboard.project_id,
        "stage": blackboard.pipeline_stage,
        "created_at": blackboard.created_at,
        "updated_at": blackboard.updated_at,
    }

    # 需求校验结果
    if blackboard.validation:
        result["validation"] = blackboard.validation.model_dump()

    # 架构设计结果
    if blackboard.architecture:
        arch = blackboard.architecture
        result["architecture"] = {
            "style": arch.architecture_style,
            "style_rationale": arch.style_rationale,
            "tech_stack": arch.tech_stack,
            "tech_plan": arch.tech_plan,
            "c4_plantuml": get_c4_plantuml_all(arch),
            "views_plantuml": get_view_plantuml_all(arch),
            "views_summary": extract_views_summary(arch),
        }

    # 评审结果
    if blackboard.review:
        result["review"] = blackboard.review.model_dump()

    # 风险检测结果
    if blackboard.risk:
        result["risk"] = {
            **blackboard.risk.model_dump(),
            "risk_items_display": get_risk_summary_for_display(blackboard.risk),
            "count_by_level": count_risks_by_level(blackboard.risk),
            "count_by_dimension": count_risks_by_dimension(blackboard.risk),
        }

    # 日志
    result["logs"] = blackboard.logs

    return result


@router.get("/result/{project_id}/summary")
async def get_result_summary(project_id: str):
    """获取项目结果摘要（轻量）"""
    blackboard = mediator.get_blackboard(project_id)
    if not blackboard:
        blackboard = mediator.load_from_disk(project_id)
    if not blackboard:
        raise HTTPException(404, "项目不存在")

    return {
        "project_id": blackboard.project_id,
        "stage": blackboard.pipeline_stage,
        "project_name": (
            blackboard.validation.structured_requirements.project_name
            if blackboard.validation and blackboard.validation.structured_requirements
            else "未命名项目"
        ),
        "architecture_style": (
            blackboard.architecture.architecture_style
            if blackboard.architecture
            else ""
        ),
        "review_score": blackboard.review.overall_score if blackboard.review else None,
        "risk_level": blackboard.risk.overall_risk_level if blackboard.risk else None,
        "iteration": blackboard.iteration,
        "created_at": blackboard.created_at,
    }
