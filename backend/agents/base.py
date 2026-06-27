"""Agent 基类"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from models.blackboard import BlackboardState, AgentStatus


class AgentResult:
    """Agent 执行结果"""

    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, error: str = ""):
        self.success = success
        self.data = data or {}
        self.error = error


class BaseAgent(ABC):
    """所有专家 Agent 的抽象基类"""

    def __init__(self, name: str, role: str, description: str = ""):
        self.name = name
        self.role = role
        self.description = description

    @abstractmethod
    async def process(self, blackboard: BlackboardState) -> AgentResult:
        """核心处理逻辑 — 每个Agent必须实现.
        从黑板读取数据，处理后写回黑板.
        """
        ...

    def get_input_keys(self) -> list[str]:
        """返回此Agent需要的黑板数据字段名列表"""
        return []

    def get_output_keys(self) -> list[str]:
        """返回此Agent会写入的黑板数据字段名列表"""
        return []

    def log(self, blackboard: BlackboardState, message: str) -> None:
        """向黑板写入日志"""
        blackboard.add_log(f"[{self.name}] {message}")

    def set_status(self, blackboard: BlackboardState, status: AgentStatus) -> None:
        """更新Agent状态"""
        blackboard.agent_statuses[self.name] = status
