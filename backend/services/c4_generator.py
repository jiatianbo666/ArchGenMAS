"""C4 DSL 生成与导出服务"""
from models.blackboard import C4Model, C4Layer, ArchitectureOutput


def get_c4_plantuml_all(arch: ArchitectureOutput) -> dict[str, str]:
    """提取所有C4层的PlantUML代码"""
    c4 = arch.c4_model
    result = {
        "context": c4.context.plantuml or _generate_fallback_plantuml("context", c4.context),
        "container": c4.container.plantuml or _generate_fallback_plantuml("container", c4.container),
        "component": c4.component.plantuml or _generate_fallback_plantuml("component", c4.component),
    }
    if c4.code and c4.code.plantuml:
        result["code"] = c4.code.plantuml
    return result


def get_view_plantuml_all(arch: ArchitectureOutput) -> dict[str, str]:
    """提取所有4+1视图的PlantUML代码"""
    v = arch.views_41
    return {
        "logical": v.logical_view.plantuml,
        "development": v.development_view.plantuml,
        "process": v.process_view.plantuml,
        "physical": v.physical_view.plantuml,
        "scenario": v.scenario_view.plantuml,
    }


def _generate_fallback_plantuml(layer: str, data: C4Layer) -> str:
    """当LLM未生成PlantUML时，根据实体和关系自动生成"""
    lines = ["@startuml", "!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml", ""]
    for entity in data.entities:
        name = entity.get("name", "Unknown")
        etype = entity.get("type", "System")
        desc = entity.get("description", "")
        alias = name.replace(" ", "_").replace("-", "_")
        lines.append(f"Container({alias}, \"{name}\", \"{etype}\", \"{desc}\")")
    for rel in data.relationships:
        frm = rel.get("from", "").replace(" ", "_").replace("-", "_")
        to = rel.get("to", "").replace(" ", "_").replace("-", "_")
        label = rel.get("label", "")
        lines.append(f"Rel({frm}, {to}, \"{label}\")")
    lines.append("@enduml")
    return "\n".join(lines)
