@echo off
chcp 65001 >nul
echo ============================================
echo  指令集研发智能体团队 - 一键启动
echo ============================================
cd /d "%~dp0.."

if not exist .venv (
  echo [1/2] 创建虚拟环境...
  python -m venv .venv
)

echo [2/2] 安装依赖并启动...
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
python scripts\start_backend.py
pause
