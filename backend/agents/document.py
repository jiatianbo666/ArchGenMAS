"""文档生成 Agent — 整合所有产物，生成Markdown+PDF"""
import json

from agents.base import BaseAgent, AgentResult
from models.blackboard import BlackboardState, AgentStatus
from utils.llm_client import get_client
from config import AGENT_MODELS


SYSTEM_PROMPT = """你是一位资深技术文档工程师。请将以下架构设计产物整合为一份完整的Markdown格式架构设计文档。

文档结构：
```markdown
# {项目名称} — 软件架构设计文档

> 生成时间: {时间}
> 体系风格: {风格}
> 综合风险等级: {等级}

---

## 第1章 需求概述

### 1.1 项目背景
（根据需求数据总结）

### 1.2 用户角色
（列出角色及说明）

### 1.3 功能需求清单
（表格列出）

### 1.4 非功能需求
（分类列出）

---

## 第2章 体系风格选型

### 2.1 选定风格
（风格名称及详细说明）

### 2.2 选型理由
（为什么选这个风格，对比其他风格）

### 2.3 技术栈
（表格列出各层技术选型）

---

## 第3章 C4架构模型

### 3.1 系统上下文图 (L1)
（PlantUML代码 + 实体说明表）

### 3.2 容器图 (L2)
（PlantUML代码 + 容器说明表）

### 3.3 组件图 (L3)
（PlantUML代码 + 组件说明表）

---

## 第4章 4+1视图

### 4.1 逻辑视图
（类/组件关系图 + 说明）

### 4.2 开发视图
（包/模块组织图 + 说明）

### 4.3 进程视图
（进程通信时序图 + 说明）

### 4.4 物理视图
（部署拓扑图 + 说明）

### 4.5 场景视图（+1）
（关键用例流程图 + 说明）

---

## 第5章 技术方案说明
（展开技术方案文本）

---

## 第6章 架构风险评估

### 6.1 风险评估总览
（总体风险等级 + 风险分布概述）

### 6.2 风险清单
（表格：编号/维度/等级/描述/影响/缓解措施）

### 6.3 优化建议
（分维度详细建议）

---

## 第7章 评审意见

### 7.1 评审评分
（总体评分/10）

### 7.2 问题清单
（表格列出）

### 7.3 改进建议
（总结建议）

---

## 附录
- 术语表
- PlantUML代码汇总
```

输出要求：
1. 直接输出完整Markdown，不要包裹在json中
2. PlantUML代码用 ```plantuml 代码块包裹
3. 表格使用Markdown表格语法
4. 不少于2000字，内容充实专业"""


class DocumentAgent(BaseAgent):
    """文档生成 Agent"""

    def __init__(self):
        super().__init__(
            name="document",
            role="技术文档工程师",
            description="整合所有架构产物，生成标准化的Markdown架构设计文档",
        )

    def _build_prompt(self, blackboard: BlackboardState) -> str:
        parts = []

        if blackboard.validation:
            v = blackboard.validation
            parts.append(f"### 需求校验结果\n- 完整性评分: {v.completeness_score}/10\n- 总结: {v.summary}")
            parts.append(f"### 结构化需求\n```json\n{v.structured_requirements.model_dump_json(indent=2)}\n```")

        if blackboard.architecture:
            a = blackboard.architecture
            parts.append(f"### 架构风格: {a.architecture_style}")
            parts.append(f"### 选型理由: {a.style_rationale}")
            parts.append(f"### 技术栈\n```json\n{json.dumps(a.tech_stack, ensure_ascii=False, indent=2)}\n```")
            parts.append(f"### 技术方案\n{a.tech_plan}")
            parts.append(f"### C4 Context\n```plantuml\n{a.c4_model.context.plantuml}\n```")
            parts.append(f"### C4 Container\n```plantuml\n{a.c4_model.container.plantuml}\n```")
            parts.append(f"### C4 Component\n```plantuml\n{a.c4_model.component.plantuml}\n```")
            parts.append(f"### 逻辑视图\n```plantuml\n{a.views_41.logical_view.plantuml}\n```")
            parts.append(f"### 开发视图\n```plantuml\n{a.views_41.development_view.plantuml}\n```")
            parts.append(f"### 进程视图\n```plantuml\n{a.views_41.process_view.plantuml}\n```")
            parts.append(f"### 物理视图\n```plantuml\n{a.views_41.physical_view.plantuml}\n```")
            parts.append(f"### 场景视图\n```plantuml\n{a.views_41.scenario_view.plantuml}\n```")

        if blackboard.review:
            r = blackboard.review
            parts.append(f"### 评审评分: {r.overall_score}/10")
            parts.append(f"### 评审问题\n{json.dumps(r.model_dump(), ensure_ascii=False, indent=2)[:3000]}")

        if blackboard.risk:
            rk = blackboard.risk
            parts.append(f"### 风险等级: {rk.overall_risk_level}")
            parts.append(f"### 风险清单\n{json.dumps(rk.model_dump(), ensure_ascii=False, indent=2)[:3000]}")

        return "\n\n---\n\n".join(parts)

    async def process(self, blackboard: BlackboardState) -> AgentResult:
        self.set_status(blackboard, AgentStatus.RUNNING)
        self.log(blackboard, "开始生成架构设计文档...")

        try:
            llm = get_client(AGENT_MODELS.get("document"))
            user_prompt = self._build_prompt(blackboard) + "\n\n请将以上所有架构产物整合为完整的Markdown架构设计文档。"
            markdown = await llm.chat(SYSTEM_PROMPT, user_prompt, max_tokens=8192)

            self.log(blackboard, f"文档生成完成，约{len(markdown)}字符")
            self.set_status(blackboard, AgentStatus.DONE)
            return AgentResult(success=True, data={"markdown": markdown})

        except Exception as e:
            self.log(blackboard, f"文档生成失败: {str(e)}")
            self.set_status(blackboard, AgentStatus.ERROR)
            return AgentResult(success=False, error=str(e))
