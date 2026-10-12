# -*- coding: utf-8 -*-
"""微架构映射 Agent：指令集到微架构（流水线/执行单元/存储层次）的映射规划。

能力：
- 生成流水线阶段划分（取指→译码→执行→访存→写回）；
- 指令到执行单元/端口的映射表；
- 寄存器重命名、乱序执行、分支预测策略建议；
- 输出 data/microarch/map_*.json 契约。
"""
from __future__ import annotations

import time
from typing import Any, Dict

from .base_agent import BaseAgent


class MicroArchMapper(BaseAgent):
    name = "microarch_mapper"
    description = "微架构映射：流水线划分、指令-执行单元映射、存储层次与乱序执行规划"

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "map")
        return self._map(task)

    def _map(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = task.get("pipeline", ["IF取指", "ID译码", "EX执行", "MEM访存", "WB写回"])
        isa_name = task.get("isa_name", "CNISA-32")
        super_scalar = bool(task.get("super_scalar", True))

        map_report = {
            "isa_name": isa_name,
            "pipeline_stages": pipeline,
            "in_order": not super_scalar,
            "execution_units": {
                "ALU0": ["add", "sub", "addi", "and", "or", "xor", "sll", "srl"],
                "ALU1": ["slt", "sltu", "slli", "srli", "srai"],
                "MUL/DIV": ["mul", "mulh", "div", "rem"],
                "LSU": ["lb", "lh", "lw", "sb", "sh", "sw"],
                "BRU": ["beq", "bne", "blt", "bge", "jal", "jalr"],
                "CSRU": ["csrrw", "csrrs", "csrrc", "ecall", "ebreak"],
            },
            "register_renaming": {
                "physical_regs": task.get("physical_regs", 64),
                "rename_buffer": "ROB 重命名，消除 WWAW/WAR 冲突",
            },
            "branch_prediction": ["静态预测", "两级自适应历史预测器", "BTB 分支目标缓冲"],
            "memory_hierarchy": {
                "L1I": "32KB 4路组相联",
                "L1D": "32KB 4路组相联, write-back",
                "L2": "256KB 8路共享",
                "L3": "可选 2MB 共享",
            },
            "cache_coherence": "MESI 协议（多核场景）",
            "critical_path_notes": [
                "取指宽度: 4 指令/周期（超标量）" if super_scalar else "取指宽度: 1 指令/周期",
                "译码宽度: 4 uop/周期",
                "访存队列深度 24，支持非阻塞访存",
            ],
            "generated_at": int(time.time()),
        }
        path = self._write_contract("microarch", f"map_{int(time.time())}.json", map_report)
        map_report["contract_path"] = str(path)
        return {"status": "ok", **map_report}
