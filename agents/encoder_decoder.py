# -*- coding: utf-8 -*-
"""指令编码/解码器 Agent：指令二进制编码与反编码。

能力（纯规则可运行）：
- 对 RV32I 子集指令执行真实编码（R/I/S/B/U/J 六种格式位域拼接）；
- 解码：从 32 位二进制还原指令语义；
- 输出编码对照表与解码报告（data/encode/decode_*.json）。
"""
from __future__ import annotations

import time
from typing import Any, Dict

from .base_agent import BaseAgent

# 简化 RV32I 编码表（opcode + funct3 + funct7）
OPCODES = {
    "OP":   0b0110011, "OP_IMM": 0b0010011, "LUI": 0b0110111, "AUIPC": 0b0010111,
    "JAL":  0b1101111, "JALR": 0b1100111, "BRANCH": 0b1100011,
    "LOAD": 0b0000011, "STORE": 0b0100011, "SYSTEM": 0b1110011,
}
FUNCT3 = {
    "ADD/SUB": 0b000, "SLL": 0b001, "SLT": 0b010, "SLTU": 0b011,
    "XOR": 0b100, "SRL/SRA": 0b101, "OR": 0b110, "AND": 0b111,
    "BEQ": 0b000, "BNE": 0b001, "BLT": 0b100, "BGE": 0b101,
    "LB": 0b000, "LH": 0b001, "LW": 0b010, "SB": 0b000, "SW": 0b010,
}
FUNCT7 = {"ADD": 0b0000000, "SUB": 0b0100000, "SRA": 0b0100000, "SRL": 0b0000000}


class EncoderDecoderAgent(BaseAgent):
    name = "encoder_decoder"
    description = "指令编码/解码器：RV32I 子集真实位域编码与反解码，输出二进制对照表"

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "encode")
        if action == "encode":
            return self._encode(task)
        if action == "decode":
            return self._decode(task)
        return self._encode(task)

    # ------------------------------------------------------------------
    def _encode(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # 指令列表: [{"asm": "add x1,x2,x3"}, {"asm": "lw x4,8(x5)"}, ...]
        instructions = task.get("instructions", [
            {"asm": "add x1, x2, x3"},
            {"asm": "addi x1, x2, 100"},
            {"asm": "lw x4, 8(x5)"},
            {"asm": "sw x6, 4(x7)"},
            {"asm": "beq x1, x2, 8"},
            {"asm": "jal x1, 1024"},
        ])
        results = []
        for ins in instructions:
            asm = ins.get("asm", "")
            try:
                encoded = self._encode_one(asm)
                results.append({"asm": asm, "hex": f"0x{encoded:08X}", "bin": f"{encoded:032b}",
                                "ok": True})
            except Exception as exc:  # noqa: BLE001
                results.append({"asm": asm, "error": str(exc), "ok": False})
        payload = {
            "action": "encode", "count": len(results), "items": results,
            "note": "RV32I 子集编码示例（ADD/SUB/ADDI/LW/SW/BEQ/JAL），完整实现见 ISA 规范",
            "generated_at": int(time.time()),
        }
        path = self._write_contract("encode", f"encode_{int(time.time())}.json", payload)
        payload["contract_path"] = str(path)
        return {"status": "ok", **payload}

    def _encode_one(self, asm: str) -> int:
        import re
        asm = asm.strip().replace(",", " ")
        tokens = [t for t in re.split(r"\s+", asm) if t]
        if not tokens:
            raise ValueError("空指令")
        mnemonic = tokens[0].upper()
        regs = [t for t in tokens[1:] if re.fullmatch(r"x\d+", t.lower())]
        nums = [int(t) for t in tokens[1:] if re.fullmatch(r"-?\d+", t)]

        # R 型：ADD/SUB/XOR/OR/AND/SLL/SLT...
        if mnemonic in ("ADD", "SUB", "XOR", "OR", "AND", "SLL", "SRL", "SRA", "SLT", "SLTU"):
            rd = int(regs[0][1:]); rs1 = int(regs[1][1:]); rs2 = int(regs[2][1:])
            funct7 = FUNCT7.get(mnemonic, 0b0000000)
            funct3 = FUNCT3.get("ADD/SUB" if mnemonic in ("ADD", "SUB") else mnemonic, 0)
            return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | OPCODES["OP"]
        # I 型：ADDI/ANDI/ORI/XORI/SLLI/SRLI 及 LOAD/JALR
        if mnemonic in ("ADDI", "ANDI", "ORI", "XORI", "SLLI", "SRLI", "SRAI"):
            rd = int(regs[0][1:]); rs1 = int(regs[1][1:]); imm = nums[0] & 0xFFF
            f3 = {"ADDI": 0b000, "ANDI": 0b111, "ORI": 0b110, "XORI": 0b100,
                  "SLLI": 0b001, "SRLI": 0b101, "SRAI": 0b101}[mnemonic]
            return (imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | OPCODES["OP_IMM"]
        if mnemonic in ("LB", "LH", "LW", "LBU", "LHU"):
            rd = int(regs[0][1:]); rs1 = int(regs[1][1:]); imm = nums[0] & 0xFFF
            f3 = FUNCT3.get(mnemonic, 0b010)
            return (imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | OPCODES["LOAD"]
        # S 型：SB/SH/SW
        if mnemonic in ("SB", "SH", "SW"):
            rs2 = int(regs[0][1:]); rs1 = int(regs[1][1:]); imm = nums[0] & 0xFFF
            f3 = FUNCT3.get(mnemonic, 0b010)
            imm11_5 = (imm >> 5) & 0x7F; imm4_0 = imm & 0x1F
            return (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (imm4_0 << 7) | OPCODES["STORE"]
        # B 型：BEQ/BNE/BLT/BGE/BLTU/BGEU
        if mnemonic in ("BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"):
            rs1 = int(regs[0][1:]); rs2 = int(regs[1][1:]); off = nums[0]
            f3 = FUNCT3.get(mnemonic, 0b000)
            imm12 = (off >> 12) & 1; imm11 = (off >> 11) & 1
            imm10_5 = (off >> 5) & 0x3F; imm4_1 = (off >> 1) & 0xF
            return (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (imm4_1 << 8) | (imm11 << 7) | OPCODES["BRANCH"]
        # U 型：LUI/AUIPC
        if mnemonic in ("LUI", "AUIPC"):
            rd = int(regs[0][1:]); imm = nums[0] & 0xFFFFF
            return (imm << 12) | (rd << 7) | OPCODES[mnemonic]
        # J 型：JAL
        if mnemonic == "JAL":
            rd = int(regs[0][1:]); off = nums[0]
            imm20 = (off >> 20) & 1; imm10_1 = (off >> 1) & 0x3FF
            imm11 = (off >> 11) & 1; imm19_12 = (off >> 12) & 0xFF
            return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | (rd << 7) | OPCODES["JAL"]
        if mnemonic == "JALR":
            rd = int(regs[0][1:]); rs1 = int(regs[1][1:]); imm = nums[0] & 0xFFF
            return (imm << 20) | (rs1 << 15) | (0b000 << 12) | (rd << 7) | OPCODES["JALR"]
        raise ValueError(f"不支持的指令: {mnemonic}")

    # ------------------------------------------------------------------
    def _decode(self, task: Dict[str, Any]) -> Dict[str, Any]:
        hex_list = task.get("hex_list", ["0x002080B3", "0x06410093", "0x0082A283"])
        results = []
        for h in hex_list:
            try:
                val = int(h, 16)
                results.append({"hex": h, "decoded": self._decode_one(val), "ok": True})
            except Exception as exc:  # noqa: BLE001
                results.append({"hex": h, "error": str(exc), "ok": False})
        payload = {
            "action": "decode", "count": len(results), "items": results,
            "generated_at": int(time.time()),
        }
        path = self._write_contract("decode", f"decode_{int(time.time())}.json", payload)
        payload["contract_path"] = str(path)
        return {"status": "ok", **payload}

    def _decode_one(self, val: int) -> str:
        opcode = val & 0x7F
        rd = (val >> 7) & 0x1F
        funct3 = (val >> 12) & 0x7
        rs1 = (val >> 15) & 0x1F
        rs2 = (val >> 20) & 0x1F
        funct7 = (val >> 25) & 0x7F
        if opcode == OPCODES["OP"]:
            if funct7 == 0b0100000 and funct3 == 0b000:
                return f"sub x{rd}, x{rs1}, x{rs2}"
            return f"add x{rd}, x{rs1}, x{rs2}"
        if opcode == OPCODES["OP_IMM"]:
            imm = (val >> 20) & 0xFFF
            if funct3 == 0b000:
                return f"addi x{rd}, x{rs1}, {imm}"
        if opcode == OPCODES["LOAD"] and funct3 == 0b010:
            imm = (val >> 20) & 0xFFF
            return f"lw x{rd}, {imm}(x{rs1})"
        if opcode == OPCODES["STORE"] and funct3 == 0b010:
            imm11_5 = (val >> 25) & 0x7F; imm4_0 = (val >> 7) & 0x1F
            imm = (imm11_5 << 5) | imm4_0
            return f"sw x{rs2}, {imm}(x{rs1})"
        if opcode == OPCODES["BRANCH"]:
            return f"branch(opcode=BRANCH, funct3={funct3}, rs1=x{rs1}, rs2=x{rs2})"
        if opcode == OPCODES["JAL"]:
            return f"jal x{rd}, {val & 0xFFFFF}"
        return f"unknown(opcode=0x{opcode:02X}, funct3={funct3})"
