
# 🚀 wukong-ai 
🙏 **致敬源项目**
特别感谢 rahulmkarthik 团队创造的革命性多智能体股票分析框架 AlphaCouncil，为本项目提供了宝贵的架构灵感！
基于 React + FastAPI + LangChain 打造的**企业级智能对话股票分析应用**。通过模拟真实金融机构的投研团队，将大语言模型转化为协同作战的 AI 智能体矩阵，为用户提供从数据挖掘到决策输出的全链路沉浸式分析体验。
## 🌟 核心亮点：多流程协同与投研级报告
告别单点问答的局限，wukong-ai 的灵魂在于**“多智能体协同工作流”**。就像真实的券商研究所一样，系统会将复杂的分析任务拆解，分发给不同职能的 AI Agent 并行处理，最终汇聚成一份结构化的专业研报：
* 🤝 **多Agent投研阵型**：内置“数据采集员”、“宏观/基本面分析师”、“情绪解读员”、“风控合规官”等多个专职 Agent。各 Agent 独立推理、实时通信、交叉验证，避免单一模型的“幻觉”。
* 🔄 **可视化多流程编排**：基于 LangGraph 提供直观的节点拖拽编排。用户可自定义分析流：如`舆情抓取 -> LLM摘要 -> 基本面比对 -> 风控评估 -> 报告生成`，让分析逻辑完全透明且可控。
* 📑 **专业级分析报告输出**：突破传统对话流，系统在多流程跑通后，可自动渲染并导出标准化的《股票深度分析报告》。报告涵盖：核心观点提炼、多维度数据图表、买卖评级建议及风险提示，支持一键分享与存档。
## 🎯 功能特性
### 📈 深度股票分析引擎
- **多维数据融合**：无缝接入实时行情数据、财经新闻、公司公告、研报文本等多源异构数据。
- **个性化交易策略**：支持用户自定义策略（如“均线突破+放量”、“高股息低估值”），Agent 将基于您的策略框架进行回测与推演。
- **三种记忆模式**：
  - `none` - 无痕模式，仅基于当前输入进行快问快答。
  - `full` - 全量记忆，发送所有历史消息，适合深度长程复盘。
  - `enhanced` - 记忆增强，AI自动提取摘要 + 保留最近2条消息，兼顾效率与上下文连贯。
### 💬 极致智能对话体验
- **多厂家模型自由切换**：无缝对接 DeepSeek、OpenAI、Anthropic、阿里云百炼、智谱AI、月之暗面等 12+ 主流大模型厂商。您可以为“数据清洗”配置廉价快速模型，为“最终决策”配置最强推理模型。
- **参数精调**：灵活调整 Temperature（创意度）、Max Tokens（输出长度）等核心参数，适应不同投研场景。
- **多对话并行与历史管理**：支持同时追踪多只股票的独立分析对话，消息发送与接收互不阻塞，内置高效的对话历史检索库。
### 🔀 强大的工作流编排系统
- **丰富的节点组件**：
  - 🟢 **开始节点**：定义全局输入变量（如股票代码、分析周期）。
  - 🧠 **LLM 节点**：调用大模型进行推理、提取或总结。
  - 📊 **工具节点**：挂载股票API查询、搜索引擎等外部能力。
  - 🔴 **结束节点**：规范输出格式或触发报告生成。
- **条件分支与循环**：支持在编排中加入“若市盈率高于行业平均则进入风险提示节点”等逻辑，实现真正的动态工作流。
### 🛠️ 工程化与系统管理
- 📋 **用户行为日志**：详细记录用户操作轨迹与 Agent 调用链路，便于复盘与模型调优。
- 🗄️ **轻量级数据库管理**：持久化存储用户配置、对话历史及生成的分析报告。
- 🌗 **深色/浅色主题切换**：适配不同光线环境，保护分析师视力。
- 📱 **全端响应式设计**：从电脑端的大屏看盘到移动端的碎片化阅读，提供一致且优雅的交互体验。
---

## 技术栈

- **前端**: React + Vite
- **后端**: FastAPI (Python)
- **LLM 框架**: LangChain
- **工作流**: LangGraph
- **数据库**: SQLite

## 快速开始

### 后端启动

```bash
cd llm-chat-app/backend
start "" "venv/Scripts/uvicorn.exe" app.main:app --reload --port 8000 --host 0.0.0.0
```

### 前端启动

```bash
cd llm-chat-app/frontend
npm run dev
```

### 访问应用

- **前端界面**：http://localhost:5173
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

## 项目结构

```
llm-chat-app/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 主应用入口
│   │   ├── routers/           # API 路由
│   │   │   ├── chat.py        # 聊天 API
│   │   │   ├── workflow.py    # 工作流 API
│   │   │   ├── logs.py        # 日志 API
│   │   │   ├── database.py    # 数据库 API
│   │   │   └── llm_config.py  # 模型配置 API
│   │   ├── services/           # 业务逻辑
│   │   │   ├── llm/           # LangChain 服务
│   │   │   │   ├── factory.py     # LLM 工厂
│   │   │   │   ├── chat_service.py # 聊天服务
│   │   │   │   └── memory.py     # 记忆管理
│   │   │   ├── workflow/      # LangGraph 工作流
│   │   │   │   └── langgraph_executor.py
│   │   │   └── config_service.py
│   │   └── models/            # 数据模型
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/                  # React + Vite 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── TopNav.jsx
│   │   │   ├── ModelConfig.jsx
│   │   │   ├── ProviderManager.jsx  # 厂家管理
│   │   │   ├── Logs.jsx
│   │   │   ├── DatabaseManager.jsx
│   │   │   └── workflow/     # 工作流模块
│   │   ├── api/
│   │   │   └── config.js     # API 调用
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 支持的厂家

| 厂家 | 显示名称 | 支持模型 |
|------|----------|----------|
| deepseek | DeepSeek | deepseek-chat, deepseek-reasoner, deepseek-coder |
| openai | OpenAI | gpt-4o, gpt-4, gpt-3.5-turbo |
| anthropic | Anthropic | claude-3.5-sonnet, claude-3-opus |
| dashscope | 阿里云百炼 | qwen-turbo, qwen-plus, qwen-max |
| 302ai | 302.AI | 多种主流模型聚合 |
| zhipu | 智谱AI | glm-4, glm-3-turbo |
| moonshot | 月之暗面 | moonshot-v1-8k/32k/128k |
| baidu | 百度智能云 | ernie-4.0, ernie-3.5 |
| minimax | MiniMax | abab6.5s-chat |
| google | Google AI | gemini-1.5-pro, gemini-1.5-flash |
| azure | Azure OpenAI | gpt-4o, gpt-4 |
| openrouter | OpenRouter | 多种模型聚合 |

## API 接口

### 对话历史管理

#### POST /api/conversations
创建新对话

#### GET /api/conversations
获取所有对话列表

#### GET /api/conversations/{conv_id}
获取单个对话详情

#### DELETE /api/conversations/{conv_id}
删除对话

### 聊天接口

#### POST /api/chat
非流式对话

#### POST /api/chat/stream
流式对话接口（支持上下文记忆）

### 厂家配置

#### GET /api/config/providers
获取所有厂家

#### POST /api/config/providers
添加厂家

#### GET /api/config/models
获取所有模型配置

#### POST /api/config/models
添加/更新模型配置

### 工作流接口

#### POST /api/workflows/run
执行工作流

```json
{
  "nodes": [
    {"id": "1", "type": "start", "data": {"config": {"variable_name": "input"}}},
    {"id": "2", "type": "llm", "data": {"config": {"model": "deepseek-chat", "prompt": "{{start.input}}"}}}
  ],
  "edges": [
    {"source": "1", "target": "2"}
  ],
  "inputs": {"input": "你好"}
}
```

### 日志接口

#### GET /api/logs
获取用户行为日志

### 数据库接口

#### GET /api/database/stats
获取数据库统计信息

#### POST /api/database/cleanup
清理历史数据

## 开发说明

### 环境要求

- Node.js 18+
- Python 3.11+
- 至少一个厂家的 API Key

### 安装依赖

```bash
# 后端
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 启动服务

```bash
# 后端
cd backend
venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

### 配置厂家

1. 访问前端 http://localhost:5173
2. 进入「厂家管理」页面
3. 点击「初始化预设厂家」或手动添加
4. 在厂家配置中填写 API Key
5. 在「模型配置」中添加模型并设置参数

### Docker 部署

```bash
docker-compose up -d
```

## License

MIT
