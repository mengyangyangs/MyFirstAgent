# MyFirstAgent: LLM 智能体开发实践

这是一个基于 Python 的 LLM (大语言模型) 智能体开发项目，旨在探索和实现多种经典的 Agent 设计范式。通过本项目，您可以了解如何从零构建具备推理、工具使用、规划和反思能力的智能体。

## 🌟 项目亮点

本项目实现了以下核心 Agent 范式和功能模块：

*   **多种 Agent 范式实现**:
    *   **Simple Agent**: 基础的对话式智能体。
    *   **ReAct Agent**: 结合推理 (Reasoning) 与行动 (Acting) 的智能体，支持动态调用工具解决问题。
    *   **Plan-and-Solve Agent**: 具备复杂任务拆解和规划能力的智能体，适用于多步骤任务。
    *   **Reflection Agent**: 具备自我反思与修正能力的智能体，能优化自身的回答。
*   **工具链 (Tools)**:
    *   内置计算器 (Calculator)、搜索 (Search)、天气查询 (Weather) 等基础工具示例。
    *   支持自定义工具扩展。
*   **记忆与增强 (Memory & RAG)**:
    *   实现了基本的长短期记忆机制。
    *   包含简单的 RAG (检索增强生成) 示例，支持知识库问答。
*   **协议实践**:
    *   包含 MCP (Model Context Protocol) 协议的简单服务器实现示例。

## 📂 目录结构

```text
/
├── hello_agent/                # 核心代码目录
│   ├── my_llm.py               # LLM 接口封装 (支持 OpenAI, Gemini, ModelScope 等)
│   ├── my_simple_agent.py      # 基础 Agent 实现
│   ├── my_react_agent.py       # ReAct 范式 Agent 实现
│   ├── my_PlanAndSolve_agent.py # Plan-and-Solve 范式 Agent 实现
│   ├── my_reflection_agent.py  # Reflection 范式 Agent 实现
│   ├── tool_chain_manager.py   # 工具链管理
│   ├── memory_data/            # 记忆存储
│   └── knowledge_base/         # RAG 知识库
├── protocols/                  # 协议相关实现 (如 MCP)
├── 智能体Agent.md               # 智能体理论学习笔记与思考
└── test.py                     # 测试脚本
```

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/mengyangyangs/MyFirstAgent.git
cd MyFirstAgent
```

### 2. 环境配置

本项目依赖 Python 3.10+。建议创建一个虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

安装必要的依赖库（根据实际使用的模型库安装，例如 `openai`, `python-dotenv`, `requests` 等）。

### 3. 配置 API Key

在 `hello_agent` 目录下创建一个 `.env` 文件，并填入您的 API Key：

```env
# 示例配置
OPENAI_API_KEY=sk-xxxxxx
# 或者其他模型服务的 Key
GEMINI_API_KEY=xxxxxx
MODELSCOPE_API_TOKEN=xxxxxx
```

### 4. 运行示例

您可以运行目录下的测试脚本来体验不同的 Agent：

```bash
# 运行简单的 LLM 对话
python hello_agent/my_main.py

# 运行 ReAct Agent (需要配置相关工具)
python hello_agent/my_react_agent.py
```

## 📚 学习资源

*   **课程项目主页**: [Datawhale Hello Agents](https://datawhalechina.github.io/hello-agents/#/./README)
*   根目录下的 `智能体Agent.md` 包含了关于智能体设计模式（ReAct, Plan-and-Solve, Reflection）、物理符号系统假说、强化学习等理论的深入思考和问答，是理解本项目设计思路的重要参考。

## ⚠️ 免责声明

本项目是一个学习和实验性质的仓库，代码主要用于演示 Agent 的工作原理，可能不具备生产环境的健壮性。

---

*Happy Coding! 🤖*