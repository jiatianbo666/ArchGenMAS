"""风险检测 Agent — 四维度风险分析"""
import json

from agents.base import BaseAgent, AgentResult
from models.blackboard import BlackboardState, AgentStatus, RiskReport, RiskItem
from utils.llm_client import get_client
from config import AGENT_MODELS


SYSTEM_PROMPT = """你是一位资深软件安全与性能专家。对以下架构方案进行四维度风险检测。输出JSON：

{
  "overall_risk_level": "high/medium/low",
  "risks": [
    {
      "id": "RISK-001",
      "dimension": "performance/security/scalability/concurrency",
      "risk_level": "high/medium/low",
      "description": "风险描述",
      "impact": "如果发生会有什么影响",
      "probability": "high/medium/low - 发生概率",
      "mitigation": "缓解措施/优化建议"
    }
  ],
  "summary": "总体风险评估总结（3-5句话）"
}

检测维度：
1. 性能风险：是否存在性能瓶颈？高并发下的响应时间、吞吐量问题？数据库查询是否可能慢？缓存策略是否缺失？
2. 安全风险：认证授权机制是否完善？是否存在数据泄露风险？是否有注入攻击面？通信是否加密？
3. 扩展性风险：系统是否容易横向扩展？插件机制是否充分？新功能接入成本如何？数据模型是否便于扩展？
4. 并发风险：是否存在资源竞争？是否会产生死锁？数据一致性如何保证？分布式事务处理方案是否合理？

严重等级定义：
- high: 上线后大概率出问题，需立即解决
- medium: 极端场景下可能出问题，建议改进
- low: 理论风险，影响范围小"""


class RiskAgent(BaseAgent):
    """风险检测 Agent"""

    def __init__(self):
        super().__init__(
            name="risk",
            role="安全与性能评估专家",
            description="从性能、安全、扩展性、并发四维度识别架构风险",
        )

    def _build_prompt(self, blackboard: BlackboardState) -> str:
        arch = blackboard.architecture
        if not arch:
            return "（无架构数据）"

        parts = [
            f"## 架构风格: {arch.architecture_style}",
            f"## 技术栈: {json.dumps(arch.tech_stack, ensure_ascii=False)}",
            f"## C4 Container\n{arch.c4_model.container.plantuml[:2000]}",
            f"## C4 Component\n{arch.c4_model.component.plantuml[:2000]}",
            f"## 进程视图\n{arch.views_41.process_view.plantuml[:1500]}",
            f"## 物理视图\n{arch.views_41.physical_view.plantuml[:1500]}",
        ]

        # 附上需求中的非功能需求
        if blackboard.validation and blackboard.validation.structured_requirements:
            nfrs = blackboard.validation.structured_requirements.non_functional_requirements
            if nfrs:
                parts.append("## 非功能需求约束\n")
                for nfr in nfrs:
                    parts.append(f"- [{nfr.category}] {nfr.description} (指标:{nfr.metric})")

        return "\n\n".join(parts)

    async def process(self, blackboard: BlackboardState) -> AgentResult:
        self.set_status(blackboard, AgentStatus.RUNNING)
        self.log(blackboard, "开始四维度风险检测...")

        if not blackboard.architecture:
            self.log(blackboard, "无架构数据，跳过风险检测")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"skipped": True})

        try:
            llm = get_client(AGENT_MODELS.get("risk"))
            user_prompt = self._build_prompt(blackboard)
            result = await llm.chat_json(SYSTEM_PROMPT, user_prompt, max_tokens=6144)

            risks = [RiskItem(**r) for r in result.get("risks", [])]
            risk_report = RiskReport(
                overall_risk_level=result.get("overall_risk_level", "low"),
                risks=risks,
                summary=result.get("summary", ""),
            )

            blackboard.risk = risk_report
            high_count = sum(1 for r in risks if r.risk_level == "high")
            self.log(blackboard, f"风险检测完成，总体等级: {risk_report.overall_risk_level}, 高风险项: {high_count}个")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"risk": risk_report.model_dump()})

        except Exception as e:
            self.log(blackboard, f"风险检测失败: {str(e)}")
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error=str(e))
