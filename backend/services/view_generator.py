"""4+1视图生成辅助服务"""
from models.blackboard import View41Model, View41Item, ArchitectureOutput


def extract_views_summary(arch: ArchitectureOutput) -> dict:
    """提取4+1视图摘要信息，用于前端展示"""
    v = arch.views_41
    views = {}
    for key, item in [
        ("logical", v.logical_view),
        ("development", v.development_view),
        ("process", v.process_view),
        ("physical", v.physical_view),
        ("scenario", v.scenario_view),
    ]:
        views[key] = {
            "title": item.title or key,
            "description": item.description or "",
            "diagram_type": item.diagram_type or "",
            "element_count": len(item.elements),
            "plantuml": item.plantuml or "",
        }
    return views


def get_consistency_check(arch: ArchitectureOutput) -> list[str]:
    """检查4+1视图之间的一致性，返回不一致清单"""
    issues = []
    v = arch.views_41

    # 逻辑视图的组件应该出现在开发视图的包中
    logical_names = {e.get("name", "") for e in v.logical_view.elements}
    dev_names = {e.get("name", "") for e in v.development_view.elements}

    # 进程视图的参与者应该能在物理视图中找到
    process_actors = {e.get("name", "") for e in v.process_view.elements}
    physical_nodes = {e.get("name", "") for e in v.physical_view.elements}

    # 场景视图的用例应该引用逻辑视图的组件
    scenario_refs = set()
    for e in v.scenario_view.elements:
        desc = e.get("description", "")
        for name in logical_names:
            if name in desc:
                scenario_refs.add(name)

    if logical_names and dev_names and not logical_names.intersection(dev_names):
        issues.append("逻辑视图与开发视图：组件命名不一致")

    if process_actors and physical_nodes:
        common = process_actors.intersection(physical_nodes)
        if len(common) < len(process_actors) * 0.3:
            issues.append("进程视图与物理视图：参与者与部署节点对应关系不足")

    return issues
