"""风险分析辅助服务"""
from models.blackboard import RiskReport, RiskItem


def count_risks_by_dimension(risk_report: RiskReport) -> dict:
    """按维度统计风险数量"""
    counts = {"performance": 0, "security": 0, "scalability": 0, "concurrency": 0}
    for r in risk_report.risks:
        dim = r.dimension
        if dim in counts:
            counts[dim] += 1
    return counts


def count_risks_by_level(risk_report: RiskReport) -> dict:
    """按等级统计风险数量"""
    counts = {"high": 0, "medium": 0, "low": 0}
    for r in risk_report.risks:
        level = r.risk_level
        if level in counts:
            counts[level] += 1
    return counts


def get_risk_summary_for_display(risk_report: RiskReport) -> list[dict]:
    """获取前端展示用的风险摘要"""
    return [
        {
            "id": r.id,
            "dimension": r.dimension,
            "dimension_label": {
                "performance": "性能",
                "security": "安全",
                "scalability": "可扩展性",
                "concurrency": "并发",
            }.get(r.dimension, r.dimension),
            "risk_level": r.risk_level,
            "risk_color": {"high": "#F56C6C", "medium": "#E6A23C", "low": "#67C23A"}.get(r.risk_level, "#909399"),
            "description": r.description,
            "impact": r.impact,
            "mitigation": r.mitigation,
        }
        for r in risk_report.risks
    ]
