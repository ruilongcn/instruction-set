# -*- coding: utf-8 -*-
"""ISA 架构设计 Agent：负责指令集架构自主设计。

能力：
- 生成 ISA 规格（寄存器文件、指令分类、寻址模式、指令格式）；
- 输出 ISA 规格 JSON 契约（data/isa/spec_*.json）；
- 支持 RISC-V 开放指令集生态基线（RV32I 等）与自主扩展指令定义。
纯规则引擎可独立运行；gateway 注入时可用 LLM 生成扩展说明。
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from .base_agent import BaseAgent

# 经典 RISC-V RV32I 基线指令分类（用于规格生成与兼容性对照）
RV32I_BASE = {
    "register_count": 32,
    "xlen": 32,
    "formats": ["R", "I", "S", "B", "U", "J"],
    "opcode_map": {
        "LUI": "0110111", "AUIPC": "0010111", "JAL": "1101111", "JALR": "1100111",
        "BRANCH": "1100011", "LOAD": "0000011", "STORE": "0100011",
        "OP_IMM": "0010011", "OP": "0110011", "SYSTEM": "1110011",
    },
    "instruction_groups": ["算术逻辑", "访存", "分支跳转", "系统", "原子/同步", "压缩指令"],
    "addressing_modes": ["立即数", "寄存器", "基址偏移", "PC相对"],
    "privilege_levels": ["U", "S", "M"],
}


class ISAAArchitect(BaseAgent):
    name = "isa_architect"
    description = "ISA 架构自主设计：寄存器文件、指令集分类、指令格式、寻址模式、特权级、扩展规划"

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "design_spec")
        if action == "design_spec":
            return self._design_spec(task)
        if action == "define_extension":
            return self._define_extension(task)
        return self._design_spec(task)

    # ------------------------------------------------------------------
    def _design_spec(self, task: Dict[str, Any]) -> Dict[str, Any]:
        name = task.get("isa_name", "CNISA-32")           # 自主指令集名称
        xlen = int(task.get("xlen", 32))
        base = task.get("base_isa", "RV32I")              # 兼容基线（RV32I / 自主）
        regs = int(task.get("register_count", 32))
        extensions = task.get("extensions", ["M", "C"])   # 扩展（M=乘除,C=压缩）

        spec = {
            "isa_name": name,
            "xlen": xlen,
            "base": base,
            "register_file": {
                "count": regs,
                "width": xlen,
                "special": {
                    "x0": "硬连线零寄存器",
                    "x1/ra": "返回地址",
                    "x2/sp": "栈指针",
                    "x8/fp": "帧指针",
                    "x10-x17/a0-a7": "参数/返回值",
                },
            },
            "instruction_formats": RV32I_BASE["formats"],
            "opcode_baseline": RV32I_BASE["opcode_map"],
            "instruction_groups": RV32I_BASE["instruction_groups"],
            "addressing_modes": RV32I_BASE["addressing_modes"],
            "privilege_levels": RV32I_BASE["privilege_levels"],
            "extensions_plan": [
                {"name": ext, "status": "planned", "note": self._extension_note(ext)}
                for ext in extensions
            ],
            "autonomy_analysis": {
                "open_baseline": base.startswith("RV"),
                "open_standard": "RISC-V 开放指令集生态（ISA 规范开放、免许可费）",
                "self_designed_parts": ["扩展指令编码分配", "自定义系统寄存器", "厂商扩展位"],
                "compliance_target": "riscv-isa-sim / riscv-tests 可运行验证",
            },
            "generated_at": int(time.time()),
        }
        path = self._write_contract("isa", f"spec_{name.lower()}_{int(time.time())}.json", spec)
        spec["contract_path"] = str(path)
        return {"status": "ok", "action": "design_spec", "isa_name": name, "spec": spec,
                "contract_path": str(path)}

    def _extension_note(self, ext: str) -> str:
        notes = {
            "M": "乘除法扩展：mul/div/rem 指令",
            "A": "原子扩展：lr/sc、amoadd 等原子操作",
            "F": "单精度浮点扩展",
            "D": "双精度浮点扩展",
            "C": "压缩指令扩展：16 位指令缩短代码体积",
            "Zicsr": "控制与状态寄存器扩展",
            "Zifencei": "指令取指屏障扩展",
            "V": "向量扩展：SIMD 数据并行",
            "Zba/Zbb/Zbs": "位操作扩展（基础位运算）",
            "H": "Hypervisor 扩展：虚拟化支持",
        }
        return notes.get(ext, "自定义扩展（自主编码分配）")

    # ------------------------------------------------------------------
    def _define_extension(self, task: Dict[str, Any]) -> Dict[str, Any]:
        ext_name = task.get("extension_name", "CNX1")
        ext_desc = task.get("description", "自定义加速指令扩展")
        new_opcodes = task.get("new_opcodes", ["0x2B", "0x2F"])  # 示例自定义 opcode 段
        ext = {
            "extension_name": ext_name,
            "description": ext_desc,
            "encoding_plan": {
                "opcode_range": new_opcodes,
                "funct3/funct7": "厂商自定义编码空间，避开标准分配",
                "encoding_space_reserved": True,
            },
            "validation_plan": [
                "与基线指令无编码冲突检查",
                "汇编器/反汇编器同步支持",
                "基准测试用例覆盖",
            ],
            "generated_at": int(time.time()),
        }
        path = self._write_contract("isa/extensions", f"ext_{ext_name.lower()}.json", ext)
        ext["contract_path"] = str(path)
        return {"status": "ok", "action": "define_extension", "extension": ext,
                "contract_path": str(path)}
