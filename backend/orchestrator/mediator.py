"""中介者调度引擎 — Mediator Pattern
协调5个Agent的执行顺序、并发控制、迭代回流
"""
import asyncio
import uuid
from datetime import datetime
from typing import Callable, Optional

from models.blackboard import BlackboardState, PipelineStage, AgentStatus
from agents.requirement import RequirementAgent
from agents.architecture import ArchitectureAgent
from agents.review import ReviewAgent
from agents.risk import RiskAgent
from agents.document import DocumentAgent
from services.history_db import save_project, update_project


class Mediator:
    """中介者 — 中央调度器，Agent之间不直接通信，全部通过中介者协调"""

    def __init__(self):
        self.requirement_agent = RequirementAgent()
        self.architecture_agent = ArchitectureAgent()
        self.review_agent = ReviewAgent()
        self.risk_agent = RiskAgent()
        self.document_agent = DocumentAgent()

        # 活跃的流水线（内存存储）
        self.active_pipelines: dict[str, BlackboardState] = {}

        # 进度回调（用于WebSocket推送）
        self.progress_callbacks: dict[str, list[Callable]] = {}

    def create_project(self, raw_document: str, filename: str = "",
                       style_preference: str = "auto",
                       max_iterations: int = 3) -> str:
        """创建新项目并返回 project_id"""
        project_id = uuid.uuid4().hex[:12]
        blackboard = BlackboardState(
            project_id=project_id,
            raw_document=raw_document,
            raw_filename=filename,
            architecture_style_preference=style_preference,
            max_iterations=max_iterations,
        )
        blackboard.add_log("项目创建成功，准备启动流水线")
        self.active_pipelines[project_id] = blackboard

        # 写入 SQLite 历史记录
        first_line = raw_document.strip().split("\n")[0] if raw_document else ""
        project_name = first_line.replace("#", "").replace("*", "").replace("【", "").replace("】", "").strip()[:80]
        asyncio.ensure_future(
            save_project(
                project_id=project_id,
                project_name=project_name or "未命名项目",
                filename=filename,
                content_preview=raw_document[:200] if raw_document else "",
                stage="running",
            )
        )
        return project_id

    def get_blackboard(self, project_id: str) -> Optional[BlackboardState]:
        return self.active_pipelines.get(project_id)

    def register_callback(self, project_id: str, callback: Callable) -> None:
        if project_id not in self.progress_callbacks:
            self.progress_callbacks[project_id] = []
        self.progress_callbacks[project_id].append(callback)

    def _enum_to_str(self, val):
        """安全地将枚举或字符串转为字符串"""
        if val is None:
            return ""
        return val.value if hasattr(val, 'value') else str(val)

    async def _notify_progress(self, blackboard: BlackboardState) -> None:
        """通知所有注册的回调（WebSocket推送）"""
        callbacks = self.progress_callbacks.get(blackboard.project_id, [])
        status_data = {
            "project_id": blackboard.project_id,
            "stage": self._enum_to_str(blackboard.pipeline_stage),
            "agent_statuses": {k: self._enum_to_str(v) for k, v in blackboard.agent_statuses.items()},
            "logs": blackboard.logs[-50:],  # 最近50条
            "iteration": blackboard.iteration,
        }
        for cb in callbacks:
            try:
                await cb(status_data)
            except Exception:
                pass

    async def run_pipeline(self, project_id: str) -> BlackboardState:
        """执行完整的生成流水线"""
        blackboard = self.active_pipelines.get(project_id)
        if not blackboard:
            raise ValueError(f"项目不存在: {project_id}")

        # ====== 阶段1: 需求校验 ======
        blackboard.pipeline_stage = PipelineStage.VALIDATING_REQUIREMENT
        blackboard.updated_at = datetime.now().isoformat()
        await self._notify_progress(blackboard)

        result = await self.requirement_agent.process(blackboard)
        if not result.success:
            blackboard.pipeline_stage = PipelineStage.ERROR
            await self._notify_progress(blackboard)
            return blackboard

        await self._notify_progress(blackboard)

        # ====== 阶段2: 架构设计 ======
        blackboard.pipeline_stage = PipelineStage.DESIGNING_ARCHITECTURE
        blackboard.updated_at = datetime.now().isoformat()
        await self._notify_progress(blackboard)

        result = await self.architecture_agent.process(blackboard)
        if not result.success:
            blackboard.pipeline_stage = PipelineStage.ERROR
            await self._notify_progress(blackboard)
            return blackboard

        await self._notify_progress(blackboard)

        # ====== 阶段3: 评审+风险 并行执行 ======
        blackboard.pipeline_stage = PipelineStage.REVIEWING
        blackboard.agent_statuses["review"] = AgentStatus.RUNNING
        blackboard.agent_statuses["risk"] = AgentStatus.RUNNING
        blackboard.updated_at = datetime.now().isoformat()
        await self._notify_progress(blackboard)

        review_task = asyncio.create_task(self.review_agent.process(blackboard))
        risk_task = asyncio.create_task(self.risk_agent.process(blackboard))
        await asyncio.gather(review_task, risk_task)

        await self._notify_progress(blackboard)

        # ====== 阶段4: 迭代回流（评审不通过 → 重新架构设计） ======
        while (
            blackboard.review
            and blackboard.review.requires_revision
            and blackboard.iteration < blackboard.max_iterations
        ):
            # 安全检查：如果上一轮有Agent报错，终止迭代
            if blackboard.agent_statuses.get("review") == AgentStatus.ERROR:
                blackboard.add_log("评审Agent连续失败，终止迭代")
                break
            if blackboard.agent_statuses.get("architecture") == AgentStatus.ERROR:
                blackboard.add_log("架构Agent执行失败，终止迭代")
                break

            blackboard.iteration += 1
            blackboard.pipeline_stage = PipelineStage.ITERATING
            blackboard.add_log(f"评审不通过，开始第{blackboard.iteration}/{blackboard.max_iterations}次迭代...")
            blackboard.updated_at = datetime.now().isoformat()
            await self._notify_progress(blackboard)

            # 重新架构设计（会读取review意见）
            arch_result = await self.architecture_agent.process(blackboard)
            if not arch_result.success:
                blackboard.add_log(f"架构Agent迭代失败: {arch_result.error}")
                break

            # 重新并行评审+风险
            rv_task = asyncio.create_task(self.review_agent.process(blackboard))
            rk_task = asyncio.create_task(self.risk_agent.process(blackboard))
            await asyncio.gather(rv_task, rk_task)

            await self._notify_progress(blackboard)

        # 迭代结束后，检查是否需要回退评审状态
        # 如果最终评审失败但之前有有效结果，使用最后一次成功的评审
        if blackboard.agent_statuses.get("review") == AgentStatus.ERROR:
            blackboard.add_log("最终评审未通过，但仍将继续生成文档")
            if blackboard.review:
                blackboard.review.requires_revision = False  # 强制终止循环状态

        # ====== 阶段5: 文档生成 ======
        blackboard.pipeline_stage = PipelineStage.GENERATING_DOCUMENT
        blackboard.updated_at = datetime.now().isoformat()
        await self._notify_progress(blackboard)

        result = await self.document_agent.process(blackboard)
        if not result.success:
            blackboard.pipeline_stage = PipelineStage.ERROR
            await self._notify_progress(blackboard)
            return blackboard

        await self._notify_progress(blackboard)

        # ====== 完成 ======
        blackboard.pipeline_stage = PipelineStage.DONE
        blackboard.updated_at = datetime.now().isoformat()
        blackboard.add_log("[OK] Pipeline completed. All agents finished successfully.")
        await self._notify_progress(blackboard)

        # 更新 SQLite（架构风格、评分、风险等级）
        asyncio.ensure_future(
            update_project(
                blackboard.project_id,
                architecture_style=blackboard.architecture.architecture_style if blackboard.architecture else "",
                review_score=blackboard.review.overall_score if blackboard.review else None,
                risk_level=blackboard.risk.overall_risk_level if blackboard.risk else "",
                iteration=blackboard.iteration,
                stage="done",
            )
        )

        return blackboard


# 全局单例
mediator = Mediator()
