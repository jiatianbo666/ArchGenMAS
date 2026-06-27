"""架构设计 Agent — 选型体系风格、生成C4模型、4+1视图、技术方案"""
import json
from agents.base import BaseAgent, AgentResult
from models.blackboard import (
    BlackboardState, AgentStatus, ArchitectureOutput,
    C4Model, C4Layer, View41Model, View41Item,
)
from utils.llm_client import get_client
from config import AGENT_MODELS


SYSTEM_PROMPT = """你是一位资深软件架构师。请根据结构化需求设计完整的软件架构。严格按JSON格式输出：

{
  "architecture_style": "选定的体系风格",
  "style_rationale": "为什么选这个风格（3-5句话）",
  "tech_stack": {"前端": "技术", "后端": "技术", "数据库": "技术", "中间件": "技术"},
  "tech_plan": "技术方案说明（300-500字）",
  "c4_model": {
    "context": {
      "title": "系统上下文图",
      "description": "系统和外部用户/系统的交互关系",
      "entities": [{"name": "名称", "type": "Person/System", "description": "描述"}],
      "relationships": [{"from": "源", "to": "目标", "label": "交互说明"}],
      "plantuml": "PlantUML C4 Context代码"
    },
    "container": {
      "title": "容器图",
      "description": "系统内部的容器划分",
      "entities": [{"name": "名称", "type": "WebApp/API/Mobile/DB/Queue", "description": "描述", "technology": "技术栈"}],
      "relationships": [{"from": "源", "to": "目标", "label": "协议/用途"}],
      "plantuml": "PlantUML C4 Container代码"
    },
    "component": {
      "title": "组件图",
      "description": "每个容器内部的组件划分",
      "entities": [{"name": "名称", "type": "Component", "description": "描述", "container": "所属容器"}],
      "relationships": [{"from": "源", "to": "目标", "label": "调用方式"}],
      "plantuml": "PlantUML C4 Component代码"
    }
  },
  "views_41": {
    "logical_view": {
      "title": "逻辑视图",
      "description": "核心类/组件及其交互关系",
      "diagram_type": "class_diagram",
      "elements": [{"name": "类/组件名", "type": "class/interface/component", "responsibilities": "职责", "methods": ["方法1"]}],
      "plantuml": "PlantUML类图代码"
    },
    "development_view": {
      "title": "开发视图",
      "description": "代码模块组织与包依赖",
      "diagram_type": "package_diagram",
      "elements": [{"name": "包/模块名", "type": "package", "description": "包含内容"}],
      "plantuml": "PlantUML包图代码"
    },
    "process_view": {
      "title": "进程视图",
      "description": "运行时进程/线程通信与并发",
      "diagram_type": "sequence_diagram",
      "elements": [{"name": "进程/线程", "type": "process", "description": "职责"}],
      "plantuml": "PlantUML时序图代码"
    },
    "physical_view": {
      "title": "物理视图",
      "description": "软硬件部署拓扑",
      "diagram_type": "deployment_diagram",
      "elements": [{"name": "节点", "type": "server/client/cloud", "description": "配置"}],
      "plantuml": "PlantUML部署图代码"
    },
    "scenario_view": {
      "title": "场景视图",
      "description": "关键业务用例流程",
      "diagram_type": "usecase_diagram",
      "elements": [{"name": "用例/角色", "type": "actor/usecase", "description": "描述"}],
      "plantuml": "PlantUML用例图代码"
    }
  }
}

设计要求：
1. 根据需求自动选择最合适的体系风格（微服务/单体/分层/事件驱动/管道过滤器等）
2. C4模型必须从上到下一致，L1实体映射到L2容器，L2容器映射到L3组件
3. 4+1五个视图必须相互印证，逻辑视图的组件应出现在开发视图中
4. PlantUML代码必须语法正确，可直接用PlantUML渲染
5. 技术栈选型要合理，考虑学生/初学者可上手的方案"""


class ArchitectureAgent(BaseAgent):
    """架构设计 Agent — 核心生成引擎"""

    def __init__(self):
        super().__init__(
            name="architecture",
            role="软件架构师",
            description="选型体系风格，生成C4分层架构图和4+1视图模型",
        )

    def _build_prompt(self, blackboard: BlackboardState) -> str:
        """根据黑板数据构建设计输入"""
        v = blackboard.validation
        if v and v.structured_requirements:
            req = v.structured_requirements
            parts = [
                f"项目名称：{req.project_name}",
                f"用户角色：{', '.join(req.user_roles)}",
                f"功能需求：",
            ]
            for fr in req.functional_requirements:
                parts.append(f"  - {fr.id} {fr.title}: {fr.description} (优先级:{fr.priority})")
            parts.append("非功能需求：")
            for nfr in req.non_functional_requirements:
                parts.append(f"  - {nfr.id} [{nfr.category}] {nfr.description} (指标:{nfr.metric})")
            parts.append(f"业务约束：{'; '.join(req.business_constraints)}")
            parts.append(f"系统边界：{req.system_boundary}")
            if blackboard.architecture_style_preference != "auto":
                parts.append(f"用户偏好风格：{blackboard.architecture_style_preference}")
            return "\n".join(parts)
        return f"请根据以下原始需求设计架构：\n\n{blackboard.raw_document}"

    async def process(self, blackboard: BlackboardState) -> AgentResult:
        self.set_status(blackboard, AgentStatus.RUNNING)
        self.log(blackboard, "开始架构设计...")

        # 如果有评审意见，加入修正提示
        feedback = ""
        if blackboard.review and blackboard.review.requires_revision:
            issues = "\n".join(
                f"- [{i.category}] {i.description} → 建议: {i.suggestion}"
                for i in blackboard.review.issues
            )
            feedback = f"\n\n【重要】上次评审发现问题，请修正：\n{issues}"
            self.log(blackboard, f"收到评审反馈，第{blackboard.iteration + 1}次迭代修改...")

        try:
            llm = get_client(AGENT_MODELS.get("architecture"))
            user_prompt = self._build_prompt(blackboard) + feedback + "\n\n请设计完整架构方案，输出JSON。"
            result = await llm.chat_json(SYSTEM_PROMPT, user_prompt, max_tokens=16384)

            # 解析 C4 模型
            c4_data = result.get("c4_model", {})
            c4 = C4Model(
                context=C4Layer(**c4_data.get("context", {})),
                container=C4Layer(**c4_data.get("container", {})),
                component=C4Layer(**c4_data.get("component", {})),
                code=C4Layer(**c4_data["code"]) if c4_data.get("code") else None,
            )

            # 解析 4+1 视图
            v41_data = result.get("views_41", {})
            v41 = View41Model(
                logical_view=View41Item(**v41_data.get("logical_view", {})),
                development_view=View41Item(**v41_data.get("development_view", {})),
                process_view=View41Item(**v41_data.get("process_view", {})),
                physical_view=View41Item(**v41_data.get("physical_view", {})),
                scenario_view=View41Item(**v41_data.get("scenario_view", {})),
            )

            arch = ArchitectureOutput(
                architecture_style=result.get("architecture_style", ""),
                style_rationale=result.get("style_rationale", ""),
                c4_model=c4,
                views_41=v41,
                tech_stack=result.get("tech_stack", {}),
                tech_plan=result.get("tech_plan", ""),
            )

            blackboard.architecture = arch
            self.log(blackboard, f"架构设计完成，风格: {arch.architecture_style}")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"architecture": arch.model_dump()})

        except Exception as e:
            self.log(blackboard, f"架构设计失败: {str(e)}")
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error=str(e))
