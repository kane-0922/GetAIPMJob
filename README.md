# 在线访问：
[code.coze.cn/web-sdk/7671105250899689535](https://code.coze.cn/web-sdk/7671105250899689535) (本项目基于扣子平台搭建)

# GetAIPMJob — AI产品经理求职助手

基于 LangGraph 多智能体架构的 AI 产品方向一站式求职辅助系统。集成简历解析、JD 匹配诊断、企业背调、专业知识问答（RAG + 知识图谱双引擎）、职业规划、模拟面试等核心能力，帮助 AI 产品方向求职者完成从简历优化到面试通过的全流程。

## 核心功能

### 📄 简历解析与优化

- 支持 PDF、Word（.doc/.docx）、TXT 格式简历上传与解析
- 自动提取个人信息、教育背景、工作经历、项目经验、技能清单
- 提供初步资质分析与竞争力评估
- 跨会话记忆，后续对话可直接引用已解析的简历信息

### 🎯 JD 匹配与诊断

- 支持直接粘贴 JD 文本或发送 JD 截图（多模态识别）
- 结合简历数据进行多维度量化匹配评分（技能匹配度、经验匹配度、学历匹配度、行业匹配度）
- 结合知识图谱进行岗位技能清单查询和技能差距分析
- 生成针对性改进建议：简历优化方向、技能补充、面试重点

### 🔍 企业背调

- 输入公司名称，自动搜索企业基本信息（注册资本、员工规模、融资情况等）
- 查询企业经营状况、口碑评价与风险提示
- 结合知识图谱查询公司 AI 产品布局与技术栈
- 综合给出「建议投递」「谨慎投递」「不建议投递」结论

### 📚 专业知识问答（RAG + 知识图谱双引擎）

- **RAG 引擎**：基于 AI 产品专业知识库的向量检索问答，覆盖 Prompt 工程、RAG 技术、Agent 架构、大模型基础、面试技巧等
- **知识图谱引擎**：支持结构化关系推理，包括：
  - 🔍 实体搜索：技术、岗位、产品、公司
  - 📖 学习路径：技术前置知识推理
  - 🚀 职业路径：岗位发展路线规划
  - 📊 技能差距分析：已有技能 vs 目标岗位要求
  - 🔗 关联分析：技术/产品的上下游关系
  - 🛠️ 技术栈查询：产品技术架构
  - 🏆 竞品分析：产品竞争格局

### 🎤 模拟面试系统

- 扮演 AI 产品方向资深面试官
- 根据求职身份（实习生/校招/社招）动态调整提问难度
- 每次提一个问题，即时点评与追问
- 面试结束后生成多维度评价报告（专业知识、产品思维、表达能力、逻辑思维、行业认知）
- 自动保存面试记录，支持历史回顾

### 👤 用户画像持久化

- 自动识别并保存用户信息（姓名、身份、学历、目标岗位、技能评估等）
- 跨会话记忆，老用户回归自动加载历史画像
- 学习进度追踪，记录已掌握与待提升的知识点
- 基于画像的主动推荐与个性化服务

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (React + Vite)                │
│               ChatUI · TailwindCSS · Markdown          │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/SSE
┌─────────────────────┴───────────────────────────────┐
│                   FastAPI 服务层                       │
│  /run · /stream_run · /async_run · /v1/chat/completions │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                 LangGraph Agent 引擎                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 系统提示词 │ │ 滑动窗口  │ │ 工具调用  │              │
│  │  编排    │ │ 记忆管理  │ │ 中间件   │              │
│  └──────────┘ └──────────┘ └──────────┘              │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                    工具层 (8 个工具)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ 简历解析工具  │ │ 企业背调工具  │ │ 知识问答工具  │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ 知识图谱工具  │ │ 用户画像工具  │ │ 学习进度工具  │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
│  ┌──────────────┐ ┌──────────────┐                    │
│  │ 面试记录工具  │ │ 画像查询工具  │                    │
│  └──────────────┘ └──────────────┘                    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│                   存储与知识层                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │ Supabase │ │ Postgres │ │ 知识库 + 知识图谱      │  │
│  │ (用户数据) │ │ (Checkpoint)│ │ (RAG + GraphRAG)   │  │
│  └──────────┘ └──────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

| 层级       | 技术选型                                              |
| ---------- | ----------------------------------------------------- |
| 前端       | React 19 + Vite 8 + TailwindCSS 3 + Lucide Icons      |
| 后端框架   | FastAPI + Uvicorn                                     |
| Agent 框架 | LangGraph 1.0 + LangChain 1.0                         |
| LLM        | 豆包 Seed 2.0 Pro（兼容 OpenAI API）                  |
| 数据库     | Supabase（用户数据）+ PostgreSQL（Checkpoint 持久化） |
| 知识库     | 向量检索（RAG）+ 知识图谱（GraphRAG）                 |
| 文件解析   | PyPDF / docx2python / openpyxl / python-pptx          |
| 包管理     | uv（阿里云镜像加速）                                  |

## 项目结构

```
GetAIPMJob/
├── src/
│   ├── main.py                      # FastAPI 服务入口 + GraphService
│   ├── agents/
│   │   └── agent.py                 # Agent 构建：工具注册 + LLM 配置 + 中间件
│   ├── tools/
│   │   ├── resume_parser_tool.py    # 简历解析工具（PDF/Word/TXT）
│   │   ├── company_research_tool.py # 企业背调工具（联网搜索）
│   │   ├── knowledge_qa_tool.py     # 知识库 RAG 问答工具
│   │   ├── knowledge_graph_tool.py  # 知识图谱查询工具（8 种查询类型）
│   │   ├── knowledge_graph_engine.py# 知识图谱引擎（BFS 路径推理 + 技能分析）
│   │   └── user_profile_tool.py     # 用户画像 CRUD 工具（Supabase）
│   ├── storage/
│   │   ├── database/
│   │   │   ├── db.py                # 数据库连接管理
│   │   │   ├── supabase_client.py   # Supabase 客户端
│   │   │   └── shared/model.py      # ORM 模型
│   │   ├── memory/
│   │   │   └── memory_saver.py      # LangGraph Checkpoint 持久化
│   │   └── s3/
│   │       └── s3_storage.py        # S3 对象存储
│   └── utils/
│       └── file/file.py             # 文件工具
├── config/
│   └── agent_llm_config.json        # LLM 配置 + 系统提示词 + 工具定义
├── assets/
│   └── knowledge_base/
│       ├── ai_product_knowledge.txt          # AI 产品知识库文本
│       ├── ai_product_knowledge_graph.json   # 知识图谱结构化数据
│       ├── interview_questions.txt           # 面试题库
│       ├── industry_terms.txt                # 行业术语库
│       └── case_studies.txt                  # 案例分析库
├── scripts/
│   ├── setup.sh                     # 环境初始化（依赖安装）
│   ├── load_env.sh                  # 环境变量加载
│   ├── local_run.sh                 # 本地运行脚本
│   ├── http_run.sh                  # HTTP 服务启动脚本
│   ├── pack.sh                      # 打包脚本
│   └── init_knowledge.py            # 知识库初始化
├── tests/
│   ├── test_cases.json              # 自动化测试用例集
│   ├── harness_engine.py            # 测试执行引擎
│   └── run_tests.py                 # 测试入口
├── frontend/                        # 前端项目（React + Vite）
│   ├── src/
│   │   ├── App.jsx                  # 应用入口
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx       # 聊天窗口
│   │   │   ├── Header.jsx           # 顶部导航
│   │   │   ├── MessageBubble.jsx    # 消息气泡（Markdown 渲染）
│   │   │   ├── MessageInput.jsx     # 消息输入框
│   │   │   ├── TypingIndicator.jsx  # 输入状态指示器
│   │   │   └── WelcomeScreen.jsx    # 欢迎页
│   │   ├── hooks/useChat.js         # 聊天逻辑 Hook
│   │   └── api/chat.js              # API 请求层
│   └── package.json
└── pyproject.toml                   # Python 项目配置
```

## 快速开始

### 环境要求

- Python >= 3.12
- Node.js >= 18（前端）
- uv 包管理器

### 1. 克隆项目并安装依赖

```bash
# 安装 Python 依赖
bash scripts/setup.sh
```

### 2. 配置环境变量

确保以下环境变量已设置：

| 环境变量                          | 说明                                       |
| --------------------------------- | ------------------------------------------ |
| `COZE_WORKSPACE_PATH`             | 工作空间路径（默认 `/workspace/projects`） |
| `COZE_WORKLOAD_IDENTITY_API_KEY`  | LLM API 密钥                               |
| `COZE_INTEGRATION_MODEL_BASE_URL` | LLM API 地址                               |
| `COZE_SESSION_ID`                 | 会话 ID（用于用户画像持久化）              |
| `SUPABASE_URL`                    | Supabase 实例地址                          |
| `SUPABASE_KEY`                    | Supabase API 密钥                          |

### 3. 启动服务

```bash
# 方式一：启动 HTTP 服务（默认端口 5000）
bash scripts/http_run.sh -p 5000

# 方式二：直接运行
python src/main.py -m http -p 5000

# 开发模式（支持热重载）
# 设置 COZE_PROJECT_ENV=DEV 后启动
```

### 4. 启动前端（可选）

```bash
cd frontend
npm install
npm run dev
```

## 运行方式

项目支持多种运行模式，通过 `-m` 参数指定：

| 模式       | 命令                                                     | 说明                   |
| ---------- | -------------------------------------------------------- | ---------------------- |
| HTTP 服务  | `bash scripts/http_run.sh -p 5000`                       | 启动 FastAPI HTTP 服务 |
| 流程运行   | `bash scripts/local_run.sh -m flow -i '{"text":"你好"}'` | 单次运行完整工作流     |
| 节点运行   | `bash scripts/local_run.sh -m node -n node_name`         | 单独运行指定节点       |
| Agent 模式 | `python src/main.py -m agent`                            | 交互式 Agent 对话      |

## API 接口

| 接口                   | 方法 | 说明                                 |
| ---------------------- | ---- | ------------------------------------ |
| `/run`                 | POST | 同步执行 Agent，返回完整结果         |
| `/stream_run`          | POST | 流式执行 Agent，SSE 格式实时推送     |
| `/async_run`           | POST | 异步执行，返回 task_id 后可轮询结果  |
| `/task/{task_id}`      | GET  | 查询异步任务状态与结果               |
| `/cancel/{run_id}`     | POST | 取消指定 run_id 的执行               |
| `/node_run/{node_id}`  | POST | 单独运行工作流中的指定节点           |
| `/graph_parameter`     | GET  | 获取工作流输入/输出 Schema           |
| `/v1/chat/completions` | POST | OpenAI Chat Completions API 兼容接口 |
| `/health`              | GET  | 健康检查                             |

### 流式调用示例

```bash
curl -X POST http://localhost:5000/stream_run \
  -H "Content-Type: application/json" \
  -H "x-run-id: my-run-001" \
  -d '{"messages": [{"role": "user", "content": "帮我分析一下RAG技术的学习路径"}]}'
```

### OpenAI 兼容接口示例

```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seed-2-0-pro",
    "messages": [{"role": "user", "content": "AI产品经理需要掌握哪些核心技能？"}],
    "stream": false
  }'
```

## 配置说明

### Agent 配置（[config/agent_llm_config.json](config/agent_llm_config.json)）

- `model`：使用的 LLM 模型
- `temperature`：生成温度（0-1）
- `thinking`：深度思考模式（`disabled` / `enabled`）
- `sp`：系统提示词（System Prompt），定义了 Agent 的角色、核心能力、意图识别规则和输出格式

### 知识库

知识库文件位于 [assets/knowledge_base/](assets/knowledge_base/)：

- `ai_product_knowledge.txt`：AI 产品领域知识文本，用于 RAG 向量检索
- `ai_product_knowledge_graph.json`：知识图谱结构化数据，定义实体（技术、技能、岗位、公司、产品、主题）和关系，支持路径推理与关联分析
- `interview_questions.txt`：模拟面试题库
- `industry_terms.txt`：AI 行业术语
- `case_studies.txt`：典型案例分析

### 数据库

项目使用双数据库架构：

- **Supabase**：存储用户画像、学习进度、面试记录等业务数据
- **PostgreSQL**：存储 LangGraph Checkpoint，实现对话记忆的持久化与恢复

## 测试

```bash
# 运行自动化测试
cd tests
python run_tests.py
```

测试用例覆盖简历解析、JD 匹配、企业背调、知识问答、知识图谱查询、模拟面试、用户画像管理等核心模块，详见 [tests/test_cases.json](tests/test_cases.json)。

## License

Private
