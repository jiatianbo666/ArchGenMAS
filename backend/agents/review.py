"""评审纠错 Agent — Critic模式，检查架构合理性、一致性、耦合度"""
import json

from agents.base import BaseAgent, AgentResult
from models.blackboard import BlackboardState, AgentStatus, ReviewReport, ReviewIssue
from utils.llm_client import get_client
from config import AGENT_MODELS


SYSTEM_PROMPT = """你是一位资深架构评审专家。对以下架构方案进行严格评审。输出JSON：

{
  "overall_score": 1-10,
  "issues": [
    {
      "id": "ISS-001",
      "category": "consistency/coupling/redundancy/compliance",
      "severity": "critical/major/minor",
      "description": "问题描述",
      "location": "问题在架构中的位置（如C4-L2容器层/逻辑视图/组件X）",
      "suggestion": "修改建议"
    }
  ],
  "suggestions": ["总体改进建议"],
  "requires_revision": true/false
}

评审维度：
1. 一致性：C4各层之间是否逻辑一致？L1的实体是否在L2有对应容器？
2. 耦合度：模块间是否存在过度耦合或循环依赖？
3. 冗余检测：是否有功能重复的组件/服务？
4. 规范合规：命名、分层、接口设计是否符合行业最佳实践？
5. 4+1五视图之间是否匹配？逻辑视图的类是否出现在开发视图的包中？

评分标准：
- 9-10: 架构合理规范，可直接使用
- 7-8: 有少量小问题，建议优化
- 5-6: 存在重要缺陷，需修改后使用
- <5: 存在严重架构问题，需要重新设计"""


class ReviewAgent(BaseAgent):
    """评审纠错 Agent — 批评者反思模式"""

    def __init__(self):
        super().__init__(
            name="review",
            role="架构评审专家",
            description="检查架构一致性、耦合度、冗余和合规性，生成评审报告",
        )

    def _build_prompt(self, blackboard: BlackboardState) -> str:
        arch = blackboard.architecture
        if not arch:
            return "（无架构数据可供评审）"

        parts = [
            f"## 架构风格\n风格: {arch.architecture_style}\n理由: {arch.style_rationale}",
            f"## 技术栈\n{json.dumps(arch.tech_stack, ensure_ascii=False)}",
            f"## C4 Context层\n{arch.c4_model.context.plantuml[:2000]}",
            f"## C4 Container层\n{arch.c4_model.container.plantuml[:2000]}",
            f"## C4 Component层\n{arch.c4_model.component.plantuml[:2000]}",
            f"## 逻辑视图\n{arch.views_41.logical_view.plantuml[:1500]}",
            f"## 开发视图\n{arch.views_41.development_view.plantuml[:1500]}",
            f"## 进程视图\n{arch.views_41.process_view.plantuml[:1500]}",
            f"## 物理视图\n{arch.views_41.physical_view.plantuml[:1500]}",
            f"## 场景视图\n{arch.views_41.scenario_view.plantuml[:1500]}",
        ]
        return "\n\n".join(parts)

    async def process(self, blackboard: BlackboardState) -> AgentResult:
        self.set_status(blackboard, AgentStatus.RUNNING)
        self.log(blackboard, "开始架构评审...")

        if not blackboard.architecture:
            self.log(blackboard, "无架构数据，跳过评审")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"skipped": True})

        try:
            llm = get_client(AGENT_MODELS.get("review"))
            user_prompt = self._build_prompt(blackboard)
            result = await llm.chat_json(SYSTEM_PROMPT, user_prompt, max_tokens=6144)

            issues = [ReviewIssue(**iss) for iss in result.get("issues", [])]
            review = ReviewReport(
                overall_score=float(result.get("overall_score", 5)),
                issues=issues,
                suggestions=result.get("suggestions", []),
                requires_revision=result.get("requires_revision", False),
            )

            blackboard.review = review
            self.log(blackboard, f"评审完成，评分: {review.overall_score}/10, 需修改: {review.requires_revision}")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"review": review.model_dump()})

        except Exception as e:
            self.log(blackboard, f"评审失败: {str(e)}")
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error=str(e))
