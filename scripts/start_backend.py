# -*- coding: utf-8 -*-
"""Startup script: create/reuse venv, install deps, launch Uvicorn."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
PYTHON = VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"


def ensure_venv():
    if not (VENV_DIR / "pyvenv.cfg").exists():
        print("[start] Creating virtual env ...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    if not PYTHON.exists():
        raise RuntimeError("venv python missing")


def ensure_deps():
    print("[start] Checking / installing dependencies ...")
    subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()

    ensure_venv()
    if not args.skip_install:
        ensure_deps()

    print(f"[start] Serving at http://{{args.host}}:{{args.port}}")
    cmd = [str(PYTHON), "-m", "uvicorn", "web.main:app", "--host", args.host, "--port", str(args.port), "--app-dir", str(ROOT)]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()