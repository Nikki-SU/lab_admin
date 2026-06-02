@echo off
chcp 65001 >nul
echo ========================================
echo LabVault Windows 打包脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查 Node.js 是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

set "BUILD_DIR=%~dp0dist"
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

echo.
echo [1/4] 打包 Hub Server...
cd /d "%~dp0hub-server"
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean hub.spec
if exist "dist\labvault-hub.exe" (
    copy /Y "dist\labvault-hub.exe" "%BUILD_DIR%\"
    copy /Y ".env.example" "%BUILD_DIR%\hub.env.example"
    echo [成功] Hub Server 打包完成
) else (
    echo [错误] Hub Server 打包失败
    pause
    exit /b 1
)
deactivate

echo.
echo [2/4] 打包 Leaf Agent...
cd /d "%~dp0leaf-agent"
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean leaf.spec
if exist "dist\labvault-leaf.exe" (
    copy /Y "dist\labvault-leaf.exe" "%BUILD_DIR%\"
    copy /Y ".env.example" "%BUILD_DIR%\leaf.env.example"
    echo [成功] Leaf Agent 打包完成
) else (
    echo [错误] Leaf Agent 打包失败
    pause
    exit /b 1
)
deactivate

echo.
echo [3/4] 构建 PC Client...
cd /d "%~dp0pc-client"
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)
call npm run build
if errorlevel 1 (
    echo [错误] PC Client 构建失败
    pause
    exit /b 1
)

echo.
echo [4/4] 打包 Electron 应用...
set ELECTRON=true
call npm run electron:build
if exist "dist-electron" (
    xcopy /E /I /Y "dist-electron" "%BUILD_DIR%\pc-client\"
    echo [成功] PC Client 打包完成
) else (
    echo [警告] Electron 打包失败，但 Web 构建已完成
    if exist "dist" (
        xcopy /E /I /Y "dist" "%BUILD_DIR%\pc-web\"
    )
)

echo.
echo ========================================
echo 打包完成！
echo 输出目录: %BUILD_DIR%
echo ========================================
echo.
echo 文件列表:
dir /B "%BUILD_DIR%"
echo.
pause
