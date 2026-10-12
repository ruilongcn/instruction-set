# -*- coding: utf-8 -*-
"""汇编器/反汇编器 Agent：汇编源码 ↔ 机器码/反汇编文本。

能力：
- 汇编：将指令文本列表汇编为十六进制机器码（复用编码器核心位域逻辑）；
- 反汇编：将机器码转回人类可读汇编文本；
- 输出 data/asm/*.s 与 data/disasm/*.txt 契约。
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .base_agent import BaseAgent
from .encoder_decoder import EncoderDecoderAgent


class AssemblerAgent(BaseAgent):
    name = "assembler"
    description = "汇编器/反汇编器：汇编文本↔机器码双向转换，输出 .s 源与反汇编清单"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enc = EncoderDecoderAgent(*args, **kwargs)

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "assemble")
        if action == "assemble":
            return self._assemble(task)
        if action == "disassemble":
            return self._disassemble(task)
        return self._assemble(task)

    # ------------------------------------------------------------------
    def _assemble(self, task: Dict[str, Any]) -> Dict[str, Any]:
        source_lines = task.get("source", [
            ".text",
            "add  x1, x2, x3",
            "addi x1, x2, 100",
            "lw   x4, 8(x5)",
            "sw   x6, 4(x7)",
            "beq  x1, x2, 8",
            "jal  x1, 1024",
        ])
        items: List[Dict[str, Any]] = []
        errors = 0
        for line in source_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(".") or stripped.startswith("#"):
                continue
            try:
                code = self._enc._encode_one(stripped)
                items.append({"asm": stripped, "hex": f"0x{code:08X}", "bin": f"{code:032b}", "ok": True})
            except Exception as exc:  # noqa: BLE001
                errors += 1
                items.append({"asm": stripped, "error": str(exc), "ok": False})
        payload = {
            "action": "assemble", "source_lines": source_lines, "items": items,
            "ok_count": len([i for i in items if i.get("ok")]), "error_count": errors,
            "generated_at": int(time.time()),
        }
        path = self._write_contract("asm", f"asm_{int(time.time())}.json", payload)
        payload["contract_path"] = str(path)
        return {"status": "ok", **payload}

    # ------------------------------------------------------------------
    def _disassemble(self, task: Dict[str, Any]) -> Dict[str, Any]:
        hex_list = task.get("hex_list", ["0x002080B3", "0x06410093", "0x0082A283"])
        items = []
        for h in hex_list:
            try:
                val = int(h, 16)
                items.append({"hex": h, "asm": self._enc._decode_one(val), "ok": True})
            except Exception as exc:  # noqa: BLE001
                items.append({"hex": h, "error": str(exc), "ok": False})
        payload = {
            "action": "disassemble", "items": items,
            "ok_count": len([i for i in items if i.get("ok")]),
            "generated_at": int(time.time()),
        }
        path = self._write_contract("disasm", f"disasm_{int(time.time())}.json", payload)
        payload["contract_path"] = str(path)
        return {"status": "ok", **payload}
