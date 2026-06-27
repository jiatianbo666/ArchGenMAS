"""黑板核心数据结构 — 所有Agent共享的全局数据池"""
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class PipelineStage(str, Enum):
    IDLE = "idle"
    PARSING = "parsing"
    VALIDATING_REQUIREMENT = "validating_requirement"
    DESIGNING_ARCHITECTURE = "designing_architecture"
    REVIEWING = "reviewing"
    ANALYZING_RISK = "analyzing_risk"
    ITERATING = "iterating"
    GENERATING_DOCUMENT = "generating_document"
    DONE = "done"
    ERROR = "error"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


# ========== 需求相关 ==========

class FunctionalReq(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    priority: str = "medium"


class NonFunctionalReq(BaseModel):
    id: str = ""
    category: str = ""
    description: str = ""
    metric: str = ""


class StructuredRequirement(BaseModel):
    project_name: str = ""
    user_roles: list[str] = []
    functional_requirements: list[FunctionalReq] = []
    non_functional_requirements: list[NonFunctionalReq] = []
    business_constraints: list[str] = []
    system_boundary: str = ""


class ValidationResult(BaseModel):
    completeness_score: float = 0.0
    missing_items: list[dict] = []
    conflicts: list[dict] = []
    vague_points: list[dict] = []
    suggestions: list[str] = []
    structured_requirements: StructuredRequirement = Field(default_factory=StructuredRequirement)
    summary: str = ""


# ========== 架构相关 ==========

class C4Layer(BaseModel):
    title: str = ""
    description: str = ""
    entities: list[dict] = []
    relationships: list[dict] = []
    plantuml: str = ""


class C4Model(BaseModel):
    context: C4Layer = Field(default_factory=C4Layer)
    container: C4Layer = Field(default_factory=C4Layer)
    component: C4Layer = Field(default_factory=C4Layer)
    code: Optional[C4Layer] = None


class View41Item(BaseModel):
    title: str = ""
    description: str = ""
    diagram_type: str = ""
    elements: list[dict] = []
    plantuml: str = ""


class View41Model(BaseModel):
    logical_view: View41Item = Field(default_factory=View41Item)
    development_view: View41Item = Field(default_factory=View41Item)
    process_view: View41Item = Field(default_factory=View41Item)
    physical_view: View41Item = Field(default_factory=View41Item)
    scenario_view: View41Item = Field(default_factory=View41Item)


class ArchitectureOutput(BaseModel):
    architecture_style: str = ""
    style_rationale: str = ""
    c4_model: C4Model = Field(default_factory=C4Model)
    views_41: View41Model = Field(default_factory=View41Model)
    tech_stack: dict[str, str] = {}
    tech_plan: str = ""


# ========== 评审与风险 ==========

class ReviewIssue(BaseModel):
    id: str = ""
    category: str = ""
    severity: str = ""
    description: str = ""
    location: str = ""
    suggestion: str = ""


class ReviewReport(BaseModel):
    overall_score: float = 0.0
    issues: list[ReviewIssue] = []
    suggestions: list[str] = []
    requires_revision: bool = False


class RiskItem(BaseModel):
    id: str = ""
    dimension: str = ""
    risk_level: str = ""
    description: str = ""
    impact: str = ""
    probability: str = ""
    mitigation: str = ""


class RiskReport(BaseModel):
    overall_risk_level: str = "low"
    risks: list[RiskItem] = []
    summary: str = ""


# ========== 黑板全局状态 ==========

class BlackboardState(BaseModel):
    project_id: str = ""
    pipeline_stage: PipelineStage = PipelineStage.IDLE

    # 原始输入
    raw_document: str = ""
    raw_filename: str = ""
    architecture_style_preference: str = "auto"

    # 各Agent产出
    validation: Optional[ValidationResult] = None
    architecture: Optional[ArchitectureOutput] = None
    review: Optional[ReviewReport] = None
    risk: Optional[RiskReport] = None

    # 迭代控制
    iteration: int = 0
    max_iterations: int = 3

    # Agent 状态追踪
    agent_statuses: dict[str, AgentStatus] = {}

    # 日志
    logs: list[str] = []

    # 时间戳
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def add_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    class Config:
        use_enum_values = True
