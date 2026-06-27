# ArchGenMAS 实现计划

> **项目全称**: Architecture Generation Multi-Agent System  
> **技术栈**: Vue 3 + TypeScript + Element Plus (前端) / FastAPI + LangChain (后端)  
> **核心功能**: 上传需求文档 → 5个AI Agent协同 → 自动生成C4/4+1视图/风险评估/PDF报告  
> **开发模式**: Claude Code 为主力开发，人工审查关键决策点

---

## 一、项目目录结构（最终形态）

```
ArchGenMAS/
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/index.ts      # 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   │   ├── workspace.ts     # 工作台状态
│   │   │   ├── pipeline.ts      # 流水线状态
│   │   │   └── result.ts        # 结果状态
│   │   ├── api/                 # API 请求封装
│   │   │   ├── client.ts        # Axios 实例
│   │   │   ├── upload.ts
│   │   │   ├── pipeline.ts
│   │   │   └── result.ts
│   │   ├── views/               # 页面组件
│   │   │   ├── HomePage.vue
│   │   │   ├── WorkspacePage.vue
│   │   │   ├── ResultPage.vue
│   │   │   └── HistoryPage.vue
│   │   ├── components/          # 公共组件
│   │   │   ├── layout/
│   │   │   ├── upload/
│   │   │   ├── pipeline/
│   │   │   └── viewer/
│   │   └── types/               # TypeScript 类型定义
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 入口 + CORS
│   ├── config.py                # 全局配置
│   ├── models/                  # Pydantic 数据模型
│   │   ├── blackboard.py        # 黑板核心数据结构
│   │   ├── requirement.py
│   │   ├── architecture.py
│   │   └── risk.py
│   ├── agents/                  # 5大专家Agent
│   │   ├── base.py              # Agent基类
│   │   ├── requirement.py       # 需求校验Agent
│   │   ├── architecture.py      # 架构设计Agent
│   │   ├── review.py            # 评审纠错Agent
│   │   ├── risk.py              # 风险检测Agent
│   │   └── document.py          # 文档生成Agent
│   ├── orchestrator/            # 中介者调度
│   │   └── mediator.py          # 核心调度+流水线
│   ├── services/                # 业务服务
│   │   ├── file_parser.py       # 文件解析
│   │   ├── c4_generator.py      # C4 DSL生成
│   │   ├── view_generator.py    # 4+1视图生成
│   │   ├── risk_analyzer.py     # 风险分析
│   │   └── pdf_exporter.py      # PDF导出
│   ├── routers/                 # API路由
│   │   ├── upload.py
│   │   ├── pipeline.py
│   │   ├── result.py
│   │   └── export.py
│   ├── utils/
│   │   └── llm_client.py        # LLM客户端封装
│   └── requirements.txt
└── task.md                      # 本文档
```

---

## 二、实现步骤（按顺序执行）

### 阶段1：项目骨架搭建
1. 创建前端 Vue3 + Vite + TS 项目
2. 创建后端 FastAPI 项目目录结构
3. 安装所有依赖
4. 配置 CORS、代理、基础路由

### 阶段2：后端数据模型
5. 实现所有 Pydantic 数据模型（黑板核心）
6. 实现 LLM 客户端封装

### 阶段3：后端5个Agent
7. 实现 Agent 基类
8. 实现需求校验 Agent
9. 实现架构设计 Agent（含C4+4+1生成）
10. 实现评审纠错 Agent
11. 实现风险检测 Agent
12. 实现文档生成 Agent

### 阶段4：后端调度与服务
13. 实现中介者调度器（含并行+迭代）
14. 实现文件解析服务
15. 实现C4 DSL/4+1视图生成服务
16. 实现风险分析引擎
17. 实现PDF导出服务
18. 实现所有API路由 + WebSocket

### 阶段5：前端开发
19. 实现路由、布局、Pinia Store
20. 实现首页
21. 实现工作台（上传+配置+进度）
22. 实现结果展示页（C4+4+1+风险+PDF下载）
23. 实现历史记录页

### 阶段6：联调测试
24. 前后端联调
25. 端到端测试

---

## 三、关键技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| LLM后端 | OpenAI兼容API（可切DeepSeek/通义千问） | 成本可控，学生友好 |
| C4图渲染 | Mermaid（前端渲染PlantUML文本） | 无需后端绘图库 |
| PDF生成 | ReportLab | 纯Python，中文支持好 |
| 实时通信 | WebSocket | FastAPI原生支持 |
| Agent框架 | 自己实现（不依赖MetaGPT/AutoGen） | 轻量、可控、方便演示 |
| 黑板存储 | 内存字典 + JSON文件持久化 | 简单够用，不需要数据库 |

---

## 四、如何执行

每完成一个步骤，标记为 ✅。依次执行，遇到问题记录。
