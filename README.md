# ArchGenMAS — 多智能体协同软件架构自动生成系统

**Architecture Generation Multi-Agent System**

输入自然语言业务需求 → 5 大 AI 专家 Agent 协同 → 一键输出 C4 模型、4+1 视图、风险评估、PDF 架构文档。

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                     前 端 (Vue 3)                        │
│         上传需求 → 配置参数 → 实时进度 → 成果展示           │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼───────────────────────────────────┐
│              中介者调度引擎 (Mediator)                     │
│         控制执行顺序 · 并发调度 · 迭代回流                  │
└──┬──────────┬──────────┬──────────┬──────────┬───────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ 需求 │ │ 架构 │ │ 评审 │ │ 风险 │ │ 文档 │
│ 校验 │ │ 设计 │ │ 纠错 │ │ 检测 │ │ 生成 │
│Agent │ │Agent │ │Agent │ │Agent │ │Agent │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │       │
   └───────┴───────┴───┬───┴───────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│              黑板数据层 (Blackboard)                       │
│        全局共享数据结构 · 所有Agent读写同一份数据             │
└──────────────────────────────────────────────────────────┘
```

**五大专家 Agent**：

| Agent | 角色 | 职责 |
|-------|------|------|
| 需求校验 Agent | 需求分析师 | 检测需求完整性、冲突、模糊点，输出结构化需求 |
| 架构设计 Agent | 软件架构师 | 选型体系风格，生成 C4 四层模型 + 4+1 五套视图 |
| 评审纠错 Agent | 架构评审专家 | 检查一致性、耦合度、冗余，Critic 批评者反馈 |
| 风险检测 Agent | 安全/性能专家 | 四维度风险扫描：性能、安全、扩展性、并发 |
| 文档生成 Agent | 技术文档工程师 | 整合所有产物，输出 Markdown + PDF 架构文档 |

**四种智能体设计模式**：

| 模式 | 体现位置 | 作用 |
|------|---------|------|
| 提示链 (Prompt Chaining) | 5 个 Agent 严格串行，前一输出 = 后一输入 | 复杂任务分解 |
| 并行化 (Parallelization) | 评审 Agent 与风险 Agent 同时并发执行 | 减少延迟 50% |
| 反思 (Reflection) | 评审 + 风险双重批评 → 架构 Agent 迭代修正 | 自我优化闭环 |
| 中介者 (Mediator) | 中央调度器统一协调，Agent 之间无直接耦合 | 通信解耦 |

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 + TypeScript | Composition API |
| UI 组件 | Element Plus | 中文生态完善 |
| 图表渲染 | Kroki API + pako | PlantUML → SVG 可视化 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| 后端框架 | FastAPI (Python) | 异步高性能 + 自动 OpenAPI 文档 |
| LLM 调用 | httpx + OpenAI 兼容接口 | 支持 SiliconFlow / DeepSeek / 通义千问 |
| 数据存储 | SQLite (aiosqlite) | 历史记录持久化 |
| 文件解析 | python-docx | 支持 .txt / .docx 需求文档 |
| PDF 生成 | ReportLab | 纯 Python，支持中文 |
| 实时通信 | WebSocket | 流水线进度实时推送 |

---

## 快速启动

### 1. 环境要求

- Python 3.9+
- Node.js 20+
- pnpm

### 2. 配置 LLM API Key

编辑 `backend/.env`：

```env
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3.5-35B-A3B
```

> 支持任何 OpenAI 兼容接口。推荐 [SiliconFlow](https://siliconflow.cn)（便宜）或 [DeepSeek](https://platform.deepseek.com)（中文好）。

### 3. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
pnpm install
```

### 4. 启动

**终端 1 — 后端**（端口 8000）：

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**终端 2 — 前端**（端口 5173）：

```bash
cd frontend
pnpm dev
```

浏览器打开 `http://localhost:5173`

### 5. 使用

1. 在首页点击「开始使用」
2. 上传需求文档（.txt / .docx）或直接粘贴需求文本
3. 选择体系风格偏好（可选）和最大迭代次数
4. 点击「开始生成架构」
5. 观察 5 个 Agent 依次/并行执行
6. 查看结果：C4 渲染图、4+1 视图、技术方案、风险报告
7. 下载 PDF 或查看历史记录

---

## 项目结构

```
ArchGenMAS/
├── backend/                          # FastAPI 后端
│   ├── main.py                       # 入口 + CORS + 路由注册
│   ├── config.py                     # 全局配置（从 .env 加载）
│   ├── .env                          # API Key + 环境变量
│   ├── models/
│   │   └── blackboard.py             # 黑板数据模型（Pydantic）
│   ├── agents/
│   │   ├── base.py                   # Agent 抽象基类
│   │   ├── requirement.py            # 需求校验 Agent
│   │   ├── architecture.py           # 架构设计 Agent (C4+4+1)
│   │   ├── review.py                 # 评审纠错 Agent (Critic)
│   │   ├── risk.py                   # 风险检测 Agent
│   │   └── document.py               # 文档生成 Agent
│   ├── orchestrator/
│   │   └── mediator.py               # 中介者调度引擎
│   ├── services/
│   │   ├── file_parser.py            # 文件解析 (txt/docx)
│   │   ├── c4_generator.py           # C4 DSL 提取
│   │   ├── view_generator.py         # 4+1 视图提取
│   │   ├── risk_analyzer.py          # 风险统计
│   │   ├── pdf_exporter.py           # PDF 导出
│   │   └── history_db.py             # SQLite 历史记录
│   ├── routers/
│   │   ├── upload.py                 # 文件上传 API
│   │   ├── pipeline.py               # 流水线 + WebSocket API
│   │   ├── result.py                 # 结果查询 API
│   │   ├── export.py                 # 文档导出 API
│   │   └── history.py                # 历史记录 API
│   └── utils/
│       └── llm_client.py             # LLM 客户端封装
│
├── frontend/                         # Vue 3 前端
│   └── src/
│       ├── main.ts                   # 入口
│       ├── App.vue                   # 根组件
│       ├── router/index.ts           # 路由配置
│       ├── stores/                   # Pinia 状态管理
│       │   ├── workspace.ts          # 工作台状态
│       │   ├── pipeline.ts           # 流水线状态
│       │   └── result.ts             # 结果状态
│       ├── api/                      # API 请求封装
│       │   ├── client.ts             # Axios 实例
│       │   ├── upload.ts             # 文件上传
│       │   ├── pipeline.ts           # 流水线执行
│       │   ├── result.ts             # 结果查询
│       │   └── history.ts            # 历史记录
│       ├── views/                    # 页面
│       │   ├── HomePage.vue          # 首页
│       │   ├── WorkspacePage.vue     # 工作台
│       │   ├── ResultPage.vue        # 结果展示
│       │   └── HistoryPage.vue       # 历史记录
│       ├── components/viewer/
│       │   └── PlantUmlViewer.vue    # PlantUML 渲染组件
│       └── types/index.ts            # TypeScript 类型定义
│
├── test_docs/                        # 测试用需求文档
│   ├── 电商平台需求.txt
│   ├── 在线考试系统需求.txt
│   └── 智能家居控制平台需求.txt
│
└── task.md                           # 开发任务清单
```

---

## API 接口

启动后端后访问 `http://localhost:8000/docs` 查看自动生成的 Swagger 文档。

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/upload` | 上传需求文档（multipart） |
| `POST` | `/api/pipeline/run` | 启动生成流水线 |
| `GET` | `/api/pipeline/{id}/status` | 查询流水线状态 |
| `WS` | `/api/ws/pipeline/{id}` | WebSocket 实时进度 |
| `GET` | `/api/result/{id}` | 获取完整结果 |
| `GET` | `/api/result/{id}/summary` | 获取结果摘要 |
| `GET` | `/api/export/{id}/pdf` | 下载架构文档 PDF |
| `GET` | `/api/export/{id}/markdown` | 下载架构文档 Markdown |
| `GET` | `/api/history` | 历史记录列表 |
| `DELETE` | `/api/history/{id}` | 删除历史记录 |
| `GET` | `/api/health` | 健康检查 |

---

## 体系风格

ArchGenMAS 采用**复合风格**：宏观三层 B/S，业务层内部黑板 + 分层组合。

### 宏观：三层 B/S 架构

```
┌──────────────────────────────────────────┐
│  表示层 (Vue 3 + Element Plus)            │
│  浏览器端，用户交互、PlantUML 渲染         │
├──────────────────────────────────────────┤
│  业务逻辑层 (FastAPI + 5 Agent)           │
│  服务端，中介者调度 + 智能体协同           │
├──────────────────────────────────────────┤
│  数据层 (SQLite + BlackboardState)        │
│  历史记录持久化 + 内存共享数据池           │
└──────────────────────────────────────────┘
```

### 业务层内部：黑板 + 分层

```
┌─────────────────────────────────┐
│  调度中介层 (Mediator)           │  ← 分层风格
│  控制执行顺序、并发、迭代回流     │
├─────────────────────────────────┤
│  智能体插件层 (5 Agents)         │  ← 黑板风格
│  通过 BlackboardState 共享数据   │     Agent 间无直接耦合
├─────────────────────────────────┤
│  数据持久层 (SQLite)             │  ← 分层风格
└─────────────────────────────────┘
```

| 风格 | 分类归属 | 在本系统中的体现 |
|------|---------|-----------------|
| **三层 B/S** | 调用/返回 → 层次结构 | 浏览器 → 服务端 → 数据库 |
| **黑板风格** | 独立构件 / 数据中心 | 5 个 Agent 共享 BlackboardState，互不直接调用 |
| **分层插件** | 调用/返回 → 层次结构 | 调度层 → 插件层 → 持久层，上层依赖下层 |

> B/S 三层是骨架，黑板 + 分层是血肉。三层决定系统怎么跑，黑板决定 Agent 怎么协作。

---

## License

MIT — 仅供学习交流使用。
