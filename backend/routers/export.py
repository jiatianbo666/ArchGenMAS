"""文档导出接口"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from orchestrator.mediator import mediator
from services.pdf_exporter import generate_pdf
from config import RESULT_DIR

router = APIRouter()


@router.get("/export/{project_id}/pdf")
async def export_pdf(project_id: str):
    """导出 PDF 架构设计文档"""
    blackboard = mediator.get_blackboard(project_id)
    if not blackboard:
        raise HTTPException(404, "项目不存在")

    # 获取Markdown内容
    markdown_content = ""
    if blackboard.agent_statuses.get("document"):
        # DocumentAgent的结果存储在blackboard的log或专门的字段
        # 这里我们从最近的AgentResult中获取
        pass

    # 如果DocumentAgent还未生成，用基础数据构造Markdown
    if not markdown_content:
        markdown_content = _build_fallback_markdown(blackboard)

    # 生成PDF
    output_path = RESULT_DIR / f"{project_id}" / "architecture_doc.pdf"
    try:
        pdf_path = await generate_pdf(markdown_content, output_path)
    except Exception as e:
        raise HTTPException(500, f"PDF生成失败: {str(e)}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"ArchGenMAS_{project_id}.pdf",
    )


@router.get("/export/{project_id}/markdown")
async def export_markdown(project_id: str):
    """导出 Markdown 架构设计文档"""
    from fastapi.responses import PlainTextResponse

    blackboard = mediator.get_blackboard(project_id)
    if not blackboard:
        raise HTTPException(404, "项目不存在")

    markdown = _build_fallback_markdown(blackboard)
    return PlainTextResponse(markdown, media_type="text/markdown")


def _build_fallback_markdown(blackboard) -> str:
    """当LLM生成的Markdown不可用时，用现有数据构建"""
    b = blackboard
    parts = [f"# 软件架构设计文档\n"]
    parts.append(f"> 生成时间: {b.created_at}")
    parts.append(f"> 迭代次数: {b.iteration}")

    # 需求
    if b.validation:
        v = b.validation
        parts.append(f"\n## 需求概述\n\n完整性评分: {v.completeness_score}/10\n\n{v.summary}")

    # 架构
    if b.architecture:
        a = b.architecture
        parts.append(f"\n## 体系风格\n\n**{a.architecture_style}**\n\n{a.style_rationale}")
        parts.append(f"\n## 技术栈\n")
        for layer, tech in a.tech_stack.items():
            parts.append(f"- **{layer}**: {tech}")
        parts.append(f"\n## C4 模型\n")
        for layer_name, layer in [
            ("系统上下文图 (L1)", a.c4_model.context),
            ("容器图 (L2)", a.c4_model.container),
            ("组件图 (L3)", a.c4_model.component),
        ]:
            parts.append(f"### {layer_name}\n")
            if layer.plantuml:
                parts.append(f"```plantuml\n{layer.plantuml}\n```\n")

        parts.append(f"\n## 4+1 视图\n")
        for view_name, view in [
            ("逻辑视图", a.views_41.logical_view),
            ("开发视图", a.views_41.development_view),
            ("进程视图", a.views_41.process_view),
            ("物理视图", a.views_41.physical_view),
            ("场景视图", a.views_41.scenario_view),
        ]:
            parts.append(f"### {view_name}\n")
            if view.plantuml:
                parts.append(f"```plantuml\n{view.plantuml}\n```\n")

    # 风险
    if b.risk:
        r = b.risk
        parts.append(f"\n## 风险评估\n\n总体风险等级: **{r.overall_risk_level}**\n\n{r.summary}\n")
        parts.append("| ID | 维度 | 等级 | 描述 | 缓解措施 |")
        parts.append("|----|------|------|------|----------|")
        for risk in r.risks:
            parts.append(f"| {risk.id} | {risk.dimension} | {risk.risk_level} | {risk.description} | {risk.mitigation} |")

    # 评审
    if b.review:
        rv = b.review
        parts.append(f"\n## 评审意见\n\n总评分: **{rv.overall_score}/10**\n")

    return "\n".join(parts)
