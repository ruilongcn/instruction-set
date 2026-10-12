---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: d32db8dd5a6f99a1df3565db906abe3a_b6f2fce6c07211f18019525400248c00
    ReservedCode1: XNxq/j9xGa5UbqDZxAQE4zA/40QnORTwtLbN0Y4xZ/HyN79Z2CnmoHfKhPAqqvcHFeMOktAhRglrsFXAZR7ZXgKo0/zVCIoWeAWK5178opMexpARlt8s6xQSgciaLbAtuALO2B+Xk8sNjoM7VZzLa5wRLJjziLgthrR0bbbVVJfJfJdT4ny7j0VhNmg=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: d32db8dd5a6f99a1df3565db906abe3a_b6f2fce6c07211f18019525400248c00
    ReservedCode2: XNxq/j9xGa5UbqDZxAQE4zA/40QnORTwtLbN0Y4xZ/HyN79Z2CnmoHfKhPAqqvcHFeMOktAhRglrsFXAZR7ZXgKo0/zVCIoWeAWK5178opMexpARlt8s6xQSgciaLbAtuALO2B+Xk8sNjoM7VZzLa5wRLJjziLgthrR0bbbVVJfJfJdT4ny7j0VhNmg=
---

# 指令集研发智能体团队（Instruction Set R&D Agent Team）

面向自主可控指令集（ISA）研发的网页版专业智能体团队软件。覆盖指令集架构自主设计、指令编码/解码器、汇编器/反汇编器、微架构映射、RISC-V 开放指令集生态、兼容性与基准测试。

## 技术栈

- **后端**：FastAPI + Uvicorn（Python 3.11+）
- **多智能体流水线**：Orchestrator 意图解析 → 按计划路由 Agent → JSON 契约落盘（data/）
- **前端**：原生 HTML + CSS + JavaScript（无构建步骤，零依赖）
- **LLM 网关**：云端 OpenAI 兼容协议优先，失败/离线自动降级本地 Ollama（纯规则引擎不依赖 LLM 也可运行）

## 智能体团队

| Agent | 职责 |
|---|---|
| isa_architect | ISA 架构自主设计（寄存器、指令格式、扩展规划、自主可控分析） |
| encoder_decoder | 指令编码/解码器（RV32I 子集真实位域编码） |
| assembler | 汇编器/反汇编器（汇编文本 ↔ 机器码） |
| microarch_mapper | 微架构映射（流水线、执行单元、存储层次、乱序执行） |
| riscv_ecosystem | RISC-V 开放指令集生态调研与自主 ISA 兼容策略 |
| compat_bench | 兼容性测试套件规划与基准测试 |

## 快速启动

### 方式一：双击脚本（Windows）

```bat
scripts\start.bat
```

### 方式二：命令行

```powershell
cd F:\instruction set
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python scripts\start_backend.py
```

启动后浏览器访问：<http://127.0.0.1:8001>

## 目录结构

```
F:\instruction set\
├── agents\            # 多智能体（base_agent / orchestrator / 各专业 Agent）
├── services\          # llm_gateway（云端→本地降级）
├── web\               # FastAPI 入口 + static 前端
├── scripts\           # 启动脚本
├── config\            # models.json + .env.example
├── data\              # Agent 产出契约（isa/encode/asm/...）
├── requirements.txt
├── README.md
└── 技术方案.md
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | / | 前端页面 |
| GET | /api/health | 健康检查 + LLM 状态 |
| GET | /api/agents | Agent 列表 |
| POST | /api/tasks | 提交目标，Orchestrator 规划并执行 |
| GET | /api/tasks/{id} | 查询任务报告 |
| GET | /api/contracts/{sub_dir} | 浏览 data/ 下契约产物 |

详细设计见 [技术方案.md](技术方案.md)。
*（内容由AI生成，仅供参考）*
