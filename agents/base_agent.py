# -*- coding: utf-8 -*-
"""Agent 基类：所有指令集研发智能体的公共抽象。

设计原则（沿用多 Agent + JSON 契约风格，参照本机成熟项目）：
- 每个 Agent 输入/输出均为 schema 化的 JSON 契约（字典），落盘于 data/ 对应目录；
- Agent 之间不直接互相调用，统一由 Orchestrator 路由；
- LLM 调用统一走 services.llm_gateway，支持云端 → 本地 Ollama 降级；
- 纯规则/模板能力不依赖 LLM 也能运行，LLM 仅作为增强。
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseAgent:
    """所有指令集 Agent 的基类。"""

    name: str = "base"
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None, data_dir: Optional[Path] = None):
        self.agent_id = f"{self.name}_{uuid.uuid4().hex[:8]}"
        self.config = config or {}
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 契约 IO
    # ------------------------------------------------------------------
    def _write_contract(self, sub_dir: str, filename: str, payload: Dict[str, Any]) -> Path:
        """将 Agent 产出以 JSON 契约形式落盘。"""
        target_dir = self.data_dir / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / filename
        payload.setdefault("_meta", {})
        payload["_meta"].update({
            "agent": self.name,
            "agent_id": self.agent_id,
            "ts": int(time.time()),
        })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("[%s] 契约已写入: %s", self.name, path)
        return path

    def _read_contract(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # 入口（子类实现）
    # ------------------------------------------------------------------
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务。task 为 Orchestrator 下发的 JSON 契约。"""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # LLM 快捷调用
    # ------------------------------------------------------------------
    def llm(self, gateway, prompt: str, **kwargs) -> str:
        return gateway.chat(prompt, **kwargs)
