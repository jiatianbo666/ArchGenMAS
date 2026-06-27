"""需求校验 Agent — 检查需求完整性、冲突、模糊点"""
import json
from agents.base import BaseAgent, AgentResult
from models.blackboard import (
    BlackboardState, AgentStatus, ValidationResult,
    StructuredRequirement, FunctionalReq, NonFunctionalReq,
)
from utils.llm_client import get_client
from config import AGENT_MODELS


SYSTEM_PROMPT = """你是一位资深软件需求分析师。请严格按以下JSON格式校验输入的软件需求文档：

{
  "completeness_score": 1-10的整数,
  "missing_items": [{"item": "缺失项", "severity": "high/medium/low", "suggestion": "建议"}],
  "conflicts": [{"item_a": "描述A", "item_b": "描述B", "description": "哪里矛盾", "resolution": "建议"}],
  "vague_points": [{"original": "原文", "question": "哪里模糊", "clarification_options": ["选项1","选项2"]}],
  "suggestions": ["总体改进建议"],
  "structured_requirements": {
    "project_name": "项目名称",
    "user_roles": ["角色1", "角色2"],
    "functional_requirements": [{"id": "FR-001", "title": "功能名", "description": "描述", "priority": "high/medium/low"}],
    "non_functional_requirements": [{"id": "NFR-001", "category": "性能/安全/扩展性/可用性", "description": "描述", "metric": "指标"}],
    "business_constraints": ["约束1"],
    "system_boundary": "系统边界描述"
  },
  "summary": "一句话总结需求是否清晰可用"
}

校验要点：
1. 完整性：是否包含用户角色、核心功能、业务约束、非功能需求？
2. 冲突检测：是否存在逻辑矛盾、术语不一致？
3. 模糊点识别：是否有多义表达？缺少量化指标？
4. 如果原始输入为空或太少，completeness_score给低分并详细说明缺失内容。"""


class RequirementAgent(BaseAgent):
    """需求校验 Agent"""

    def __init__(self):
        super().__init__(
            name="requirement",
            role="需求分析师",
            description="校验需求文档完整性，识别冲突与模糊点，输出结构化需求",
        )

    async def process(self, blackboard: BlackboardState) -> AgentResult:
        self.set_status(blackboard, AgentStatus.RUNNING)
        self.log(blackboard, "开始校验需求文档...")

        if not blackboard.raw_document.strip():
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error="需求文档为空")

        try:
            llm = get_client(AGENT_MODELS.get("requirement"))
            user_prompt = f"请校验以下需求文档：\n\n{blackboard.raw_document}"
            result = await llm.chat_json(SYSTEM_PROMPT, user_prompt, max_tokens=4096)

            # 解析结构化需求
            sr_data = result.get("structured_requirements", {})
            sr = StructuredRequirement(
                project_name=sr_data.get("project_name", "未命名项目"),
                user_roles=sr_data.get("user_roles", []),
                functional_requirements=[
                    FunctionalReq(**fr) for fr in sr_data.get("functional_requirements", [])
                ],
                non_functional_requirements=[
                    NonFunctionalReq(**nfr) for nfr in sr_data.get("non_functional_requirements", [])
                ],
                business_constraints=sr_data.get("business_constraints", []),
                system_boundary=sr_data.get("system_boundary", ""),
            )

            validation = ValidationResult(
                completeness_score=float(result.get("completeness_score", 5)),
                missing_items=result.get("missing_items", []),
                conflicts=result.get("conflicts", []),
                vague_points=result.get("vague_points", []),
                suggestions=result.get("suggestions", []),
                structured_requirements=sr,
                summary=result.get("summary", ""),
            )

            blackboard.validation = validation
            self.log(blackboard, f"需求校验完成，完整性评分: {validation.completeness_score}/10")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"validation": validation.model_dump()})

        except Exception as e:
            self.log(blackboard, f"需求校验失败: {str(e)}")
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error=str(e))
