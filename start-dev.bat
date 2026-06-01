@echo off
chcp 65001 > nul
echo ========================================
echo    LabVault 开发环境启动脚本
echo ========================================
echo.

REM 检查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查并启动 Hub 服务器...
cd hub-server
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat
if not exist "requirements.txt" (
    echo 依赖未安装，请手动运行: pip install -r requirements.txt
)
echo.
echo ========================================
echo Hub 服务器准备就绪！
echo 请在新终端运行: cd hub-server ; venv\Scripts\activate ; python main.py
echo ========================================
echo.

cd ..

echo [2/3] 检查 PC 客户端...
cd pc-client
if not exist "node_modules" (
    echo 安装 Node 依赖...
    call npm install
)
echo.
echo ========================================
echo PC 客户端准备就绪！
echo 请在新终端运行: cd pc-client ; npm run dev
echo ========================================
echo.

cd ..

echo [3/3] Leaf 代理...
cd leaf-agent
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat
if not exist "watch" mkdir watch
echo.
echo ========================================
echo Leaf 代理准备就绪！
echo 请在新终端运行: cd leaf-agent ; venv\Scripts\activate ; python main.py
echo ========================================
echo.

echo.
echo ========================================
echo    启动完成！
echo    请分别打开三个终端运行各组件
echo ========================================
echo.
pause
