# -*- coding: utf-8 -*-
"""Orchestrator：指令集研发多智能体流水线编排器。

职责：
- 解析用户意图 → 生成计划（plan）；
- 按计划路由到对应 Agent 顺序/并行执行（execute）；
- 汇总各 Agent 契约结果，输出任务报告。
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List

from . import (
    isa_architect, encoder_decoder, assembler, microarch_mapper,
    riscv_ecosystem, compat_bench,
)

logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    "isa_architect": (isa_architect.ISAAArchitect, "ISA 架构自主设计"),
    "encoder_decoder": (encoder_decoder.EncoderDecoderAgent, "指令编码/解码器"),
    "assembler": (assembler.AssemblerAgent, "汇编器/反汇编器"),
    "microarch_mapper": (microarch_mapper.MicroArchMapper, "微架构映射"),
    "riscv_ecosystem": (riscv_ecosystem.RISCVEcosystemAgent, "RISC-V 开放指令集生态"),
    "compat_bench": (compat_bench.CompatBenchAgent, "兼容性与基准测试"),
}


class Orchestrator:
    """指令集研发智能体团队编排器。"""

    def __init__(self, llm_gateway=None, data_dir=None):
        self.llm_gateway = llm_gateway
        self.data_dir = data_dir
        self._tasks: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    def plan(self, goal: str) -> List[Dict[str, Any]]:
        """根据目标关键词路由出执行计划（纯规则意图解析 + 可选 LLM 精化）。"""
        g = goal.lower()
        plan: List[Dict[str, Any]] = []
        if any(k in g for k in ["架构", "isa", "规格", "设计", "寄存器", "指令集设计", "规范"]):
            plan.append({"agent": "isa_architect", "action": "design_spec", "params": {}})
        if any(k in g for k in ["编码", "解码", "encoding", "decode", "机器码"]):
            plan.append({"agent": "encoder_decoder", "action": "encode", "params": {}})
        if any(k in g for k in ["汇编", "反汇编", "assemble", "asm", "disasm"]):
            plan.append({"agent": "assembler", "action": "assemble", "params": {}})
        if any(k in g for k in ["微架构", "流水线", "超标量", "microarch", "执行单元"]):
            plan.append({"agent": "microarch_mapper", "action": "map", "params": {}})
        if any(k in g for k in ["risc-v", "riscv", "生态", "开放", "ecosystem", "兼容"]):
            plan.append({"agent": "riscv_ecosystem", "action": "survey", "params": {}})
        if any(k in g for k in ["基准", "测试", "bench", "性能", "合规"]):
            plan.append({"agent": "compat_bench", "action": "plan", "params": {}})
        if not plan:
            plan = [{"agent": "isa_architect", "action": "design_spec", "params": {}},
                    {"agent": "encoder_decoder", "action": "encode", "params": {}},
                    {"agent": "compat_bench", "action": "plan", "params": {}}]
        return plan

    # ------------------------------------------------------------------
    def execute(self, goal: str, plan: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        """顺序执行计划中的每个 Agent 步骤。"""
        results = []
        for step in plan:
            agent_name = step["agent"]
            agent_cls, _ = AGENT_REGISTRY[agent_name]
            agent = agent_cls(config={}, data_dir=self.data_dir)
            task = dict(step.get("params", {}))
            task.update(params)
            task["action"] = step.get("action", "default")
            try:
                res = agent.run(task)
                results.append({"agent": agent_name, "ok": True, "result": res})
            except Exception as exc:  # noqa: BLE001
                logger.exception("Agent %s 失败", agent_name)
                results.append({"agent": agent_name, "ok": False, "error": str(exc)})
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        report = {
            "task_id": task_id, "goal": goal, "plan": plan,
            "results": results, "status": "done",
            "created_at": int(time.time()),
        }
        self._tasks[task_id] = report
        return report

    # ------------------------------------------------------------------
    def run(self, goal: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        params = params or {}
        plan = self.plan(goal)
        return self.execute(goal, plan, params)

    def get_task(self, task_id: str) -> Dict[str, Any] | None:
        return self._tasks.get(task_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "description": desc, "action_hint": self._hint(name)}
            for name, (cls, desc) in AGENT_REGISTRY.items()
        ]

    def _hint(self, name: str) -> str:
        hints = {
            "isa_architect": "design_spec / define_extension",
            "encoder_decoder": "encode / decode",
            "assembler": "assemble / disassemble",
            "microarch_mapper": "map",
            "riscv_ecosystem": "survey / compatibility",
            "compat_bench": "plan / benchmark",
        }
        return hints.get(name, "")
