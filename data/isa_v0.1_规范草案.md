---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: d32db8dd5a6f99a1df3565db906abe3a_372ef76fc67711f1820a525400638852
    ReservedCode1: jZA9Y4hY1vZF2IoMjhI9F+3zYRwkdnAzjX2cLlG9i7AxLog0vgvSWI53b5PvjYnlE5FIiJ5Ob5XYkX2ZEo+kj6QbgJJcrbIBr/IM30Zx5a0WP2K39/tUrbf1hN0sBUTiMesLKo985qcLw4vVA1aVsccGgLUD2GaxLmgrTlsDHazzvisO4ehLkjr6XgI=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: d32db8dd5a6f99a1df3565db906abe3a_372ef76fc67711f1820a525400638852
    ReservedCode2: jZA9Y4hY1vZF2IoMjhI9F+3zYRwkdnAzjX2cLlG9i7AxLog0vgvSWI53b5PvjYnlE5FIiJ5Ob5XYkX2ZEo+kj6QbgJJcrbIBr/IM30Zx5a0WP2K39/tUrbf1hN0sBUTiMesLKo985qcLw4vVA1aVsccGgLUD2GaxLmgrTlsDHazzvisO4ehLkjr6XgI=
---

# CFX-RISCV ISA v0.1 规范草案

> 版本：v0.1（草案）
> 日期：2026-10-12
> 状态：draft
> 编制：instruction set 智能体团队（instruction set / F:\computer fixer\instruction set）
> 配套机器可读契约：`isa_v0.1.json`（遵循 `F:\computer fixer\docs\contract-schema\isa-contract.schema.json`）

---

## 1. 总则

**CFX-RISCV** 是 computer fixer 全栈生态的自研指令集。设计原则：

1. **生态兼容**：以 RISC-V RV64GC 为基础，直接复用成熟工具链（GCC/LLVM）、操作系统移植成果与软件生态；
2. **自主扩展**：在开放基座上定义自研扩展（AI 计算、安全），作为后续 IP 授权与标准提案的载体；
3. **契约驱动**：本规范与 `isa_v0.1.json` 编码表是芯片（RTL 译码器）、汇编器、固件、OS 的唯一事实源。

## 2. 基础规格

| 项目 | 值 |
|---|---|
| ISA 名称 | CFX-RISCV |
| 版本 | v0.1（草案） |
| XLEN | 64 |
| 基础指令集 | RV64GC（G = I + M + A + F + D + Zicsr + Zifencei） |
| 自研扩展 | CFX-AI（草案）、CFX-SEC（草案） |
| 字节序 | 小端（little-endian） |

## 3. 寄存器（RV64 通用寄存器）

| 编号 | ABI 名 | 用途 |
|---|---|---|
| x0 | zero | 常量 0 |
| x1 | ra | 返回地址 |
| x2 | sp | 栈指针 |
| x3 | gp | 全局指针 |
| x4 | tp | 线程指针 |
| x5-x7 | t0-t2 | 临时 |
| x8 | s0/fp | 保存/帧指针 |
| x9 | s1 | 保存 |
| x10-x17 | a0-a7 | 参数/返回值 |
| x18-x27 | s2-s11 | 保存 |
| x28-x31 | t3-t6 | 临时 |
| pc | — | 程序计数器 |

## 4. 指令格式

```
R 型:  funct7 | rs2(5) | rs1(5) | funct3(3) | rd(5) | opcode(7)
I 型:  imm[11:0] | rs1(5) | funct3(3) | rd(5) | opcode(7)
S 型:  imm[11:5] | rs2(5) | rs1(5) | funct3(3) | imm[4:0] | opcode(7)
B 型:  imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode
U 型:  imm[31:12] | rd | opcode
J 型:  imm[20|10:1|11|19:12] | rd | opcode
```

## 5. 基础指令集（RV64I 子集，v0.1 先行落地）

### 5.1 整数运算（R 型，opcode 0x33）

| 指令 | funct3 | funct7 | 说明 |
|---|---|---|---|
| ADD | 000 | 0000000 | 加 |
| SUB | 000 | 0100000 | 减 |
| AND | 111 | 0000000 | 与 |
| OR | 110 | 0000000 | 或 |
| XOR | 100 | 0000000 | 异或 |
| SLL | 001 | 0000000 | 逻辑左移 |
| SRL | 101 | 0000000 | 逻辑右移 |
| SRA | 101 | 0100000 | 算术右移 |
| SLT | 010 | 0000000 | 有符号小于 |
| SLTU | 011 | 0000000 | 无符号小于 |

### 5.2 立即数运算（I 型，opcode 0x13）

| 指令 | funct3 | 说明 |
|---|---|---|
| ADDI | 000 | 加立即数 |
| ANDI | 111 | 与立即数 |
| ORI | 110 | 或立即数 |
| XORI | 100 | 异或立即数 |
| SLLI | 001 | 逻辑左移立即数 |
| SRLI | 101 | 逻辑右移立即数（imm[11:5]=0） |
| SRAI | 101 | 算术右移立即数（imm[11:5]=0100000） |
| SLTI | 010 | 有符号小于立即数 |
| SLTIU | 011 | 无符号小于立即数 |

### 5.3 高立即数（U 型）

| 指令 | opcode | 说明 |
|---|---|---|
| LUI | 0x37 | 加载高立即数 |
| AUIPC | 0x17 | 加 PC 高立即数 |

### 5.4 访存（I/S 型，opcode 0x03 / 0x23）

| 指令 | opcode | funct3 | 说明 |
|---|---|---|---|
| LB | 0x03 | 000 | 加载字节 |
| LH | 0x03 | 001 | 加载半字 |
| LW | 0x03 | 010 | 加载字 |
| LD | 0x03 | 011 | 加载双字 |
| LBU | 0x03 | 100 | 加载无符号字节 |
| LHU | 0x03 | 101 | 加载无符号半字 |
| SB | 0x23 | 000 | 存储字节 |
| SH | 0x23 | 001 | 存储半字 |
| SW | 0x23 | 010 | 存储字 |
| SD | 0x23 | 011 | 存储双字 |

### 5.5 分支（B 型，opcode 0x63）

| 指令 | funct3 | 说明 |
|---|---|---|
| BEQ | 000 | 相等跳转 |
| BNE | 001 | 不等跳转 |
| BLT | 100 | 有符号小于跳转 |
| BGE | 101 | 有符号大于等于跳转 |
| BLTU | 110 | 无符号小于跳转 |
| BGEU | 111 | 无符号大于等于跳转 |

### 5.6 跳转与系统（U/J/I 型）

| 指令 | opcode | funct3 | 说明 |
|---|---|---|---|
| JAL | 0x6F | — | 跳转并链接 |
| JALR | 0x67 | 000 | 间接跳转并链接 |
| ECALL | 0x73 | 000 | 环境调用（imm=0） |
| EBREAK | 0x73 | 000 | 环境断点（imm=1） |
| FENCE | 0x0F | 000 | 内存屏障 |
| CSRRW | 0x73 | 001 | CSR 读写 |
| CSRRS | 0x73 | 010 | CSR 读置位 |
| CSRRC | 0x73 | 011 | CSR 读清除 |
| CSRRWI | 0x73 | 101 | CSR 立即数读写 |
| CSRRSI | 0x73 | 110 | CSR 立即数读置位 |
| CSRRCI | 0x73 | 111 | CSR 立即数读清除 |

## 6. 自研扩展（草案，custom opcode）

### 6.1 CFX-AI（AI 计算扩展，custom-0，opcode 0x0B）

面向本地 AI 推理加速，草案定义三类指令族（编码位段在 v0.1 仅占位，RTL 译码器按模板预留）：

| 指令族 | 助记符前缀 | 草案说明 |
|---|---|---|
| 向量点积 | CFXDOT | 64 位向量元素点积累加（v0.1 目标） |
| 激活近似 | CFXACT | tanh/ReLU 硬件近似（v0.1 草案） |
| INT8 量化 | CFXQNT | 浮点→INT8 量化转换（v0.1 草案） |

### 6.2 CFX-SEC（安全扩展，custom-1，opcode 0x1B）

| 指令族 | 助记符前缀 | 草案说明 |
|---|---|---|
| 安全访存 | CFXSM | 带权限标签的加载/存储（与 openbios 信任根联动） |
| 指针认证 | CFXPA | 指针签名/验证（返回地址保护） |

> 扩展指令完整编码位段待 v0.1 冻结评审后补充，评审焦点：与 RISC-V 保留编码空间的一致性、GCC/LLVM 后端扩展实现成本、与 CFX-SEC/可信根的联动接口。

## 7. 工具链状态

| 组件 | 状态 | 目标 |
|---|---|---|
| 汇编器 | skeleton（v0.1 先行 10 条基础指令） | 全量 RV64I + 扩展 |
| 反汇编器 | 规划 | 与汇编器同源 |
| GCC 后端 | 规划 | 复用 RISC-V 后端 + CFX 扩展 |
| RTL 译码器 | 规划 | 由 `isa_v0.1.json` 驱动生成 |

## 8. 下一步（v0.1 → v1.0 冻结路径）

1. 汇编器扩展至全量 RV64I（约 60 条），跑通自举测试；
2. CFX-AI / CFX-SEC 完成编码位段定义与 LLVM 扩展 IR 方案；
3. RTL 译码器按契约生成，接入 chip design robot CPU 核；
4. 兼容基准（compat_bench）建立，与 riscv-tests 对齐。

---

*本草案由 AI 生成，编码表以 `isa_v0.1.json` 为准，实现前需人工复核关键编码位段。*
*（内容由AI生成，仅供参考）*
