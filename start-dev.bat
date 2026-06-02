@echo off
chcp 65001 >nul
echo ========================================
echo LabVault 开发环境启动脚本
echo ========================================
echo.

REM 启动 Hub Server
echo [1/3] 启动 Hub Server...
start "LabVault Hub" cmd /k "cd /d %~dp0hub-server && if not exist venv (python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && python main.py"

timeout /t 3 /nobreak >nul

REM 启动 PC Client
echo [2/3] 启动 PC Client...
start "LabVault Client" cmd /k "cd /d %~dp0pc-client && if not exist node_modules (npm install) && npm run dev"

echo.
echo ========================================
echo 启动完成！
echo Hub Server: http://localhost:8000
echo PC Client: http://localhost:3000
echo API 文档: http://localhost:8000/docs
echo ========================================
echo.
echo 提示: 要启动 Leaf Agent，请在另一个终端运行:
echo   cd leaf-agent
echo   python main.py
echo.
pause
