# -*- coding: utf-8 -*-
"""LLM 网关：云端 LLM 优先，失败/离线自动降级到本地 Ollama。

配置来源：config/models.json + .env（云端 API Key 等敏感项）。
参照本机成熟项目 services/llm_gateway.py 实现。
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class LLMGateway:
    """统一 LLM 调用入口。"""

    def __init__(self, config_dir: Optional[Path] = None, env_path: Optional[Path] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.config = self._load_config()
        self.env = self._load_env(env_path or (self.config_dir / ".env"))
        self._stats = {"calls": 0, "model_used": "", "total_tokens_est": 0}

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def chat(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """按模型链依次尝试，返回首个成功的文本结果。"""
        chain = self.config.get("default_chain", ["cloud", "local"])
        last_err = None
        for tier in chain:
            try:
                if tier == "cloud":
                    return self._chat_cloud(prompt, system, **kwargs)
                if tier == "local":
                    return self._chat_local(prompt, system, **kwargs)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                logger.warning("[llm_gateway] %s 失败: %s，尝试下一级", tier, exc)
        raise RuntimeError(f"所有 LLM 后端均失败: {last_err}")

    # ------------------------------------------------------------------
    # 云端 LLM（OpenAI 兼容协议）
    # ------------------------------------------------------------------
    def _chat_cloud(self, prompt: str, system: Optional[str], **kwargs) -> str:
        cfg = self.config.get("cloud", {})
        api_key = self.env.get(cfg.get("api_key_env", "CLOUD_LLM_API_KEY")) or os.getenv(cfg.get("api_key_env", ""))
        if not api_key:
            raise RuntimeError("云端 API Key 缺失（请在 config/.env 配置）")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = requests.post(
            f"{cfg['base_url'].rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": cfg.get("model", "deepseek-chat"),
                "messages": messages,
                "temperature": cfg.get("temperature", 0.4),
            },
            timeout=cfg.get("timeout_seconds", 120),
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        self._record("cloud", cfg.get("model", ""), data.get("usage", {}))
        return text

    # ------------------------------------------------------------------
    # 本地 Ollama 兜底
    # ------------------------------------------------------------------
    def _chat_local(self, prompt: str, system: Optional[str], **kwargs) -> str:
        cfg = self.config.get("local", {})
        base_url = cfg.get("base_url", "http://127.0.0.1:11434")
        payload = {
            "model": cfg.get("model", "qwen2.5:14b"),
            "prompt": f"{system}\n\n{prompt}" if system else prompt,
            "stream": False,
            "options": {"temperature": cfg.get("temperature", 0.4)},
        }
        try:
            resp = requests.post(f"{base_url}/api/generate", json=payload, timeout=cfg.get("timeout_seconds", 300))
        except requests.ConnectionError as exc:
            raise RuntimeError("本地 Ollama 未启动（请运行 ollama serve）") from exc
        resp.raise_for_status()
        data = resp.json()
        text = data.get("response", "")
        self._record("local", cfg.get("model", ""), {"prompt_eval_count": 0, "eval_count": len(text)})
        return text

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _record(self, tier: str, model: str, usage: Dict[str, Any]) -> None:
        self._stats["calls"] += 1
        self._stats["model_used"] = model
        tokens = int(usage.get("total_tokens", 0) or (usage.get("prompt_eval_count", 0) + usage.get("eval_count", 0)))
        self._stats["total_tokens_est"] += tokens
        logger.info("[llm_gateway] %s / %s tokens=%s", tier, model, tokens)

    def stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_dir / "models.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("config/models.json 不存在，使用默认配置")
            return {"default_chain": ["local"], "local": {"base_url": "http://127.0.0.1:11434", "model": "qwen2.5:14b"}}

    def _load_env(self, path: Path) -> Dict[str, str]:
        env: Dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        return env
