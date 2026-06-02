@echo off
chcp 65001 >nul
echo ========================================
echo 打包 Leaf Agent
echo ========================================
echo.

cd /d "%~dp0leaf-agent"
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean leaf.spec

if exist "dist\labvault-leaf.exe" (
    echo.
    echo [成功] 打包完成！
    echo 可执行文件: %~dp0leaf-agent\dist\labvault-leaf.exe
) else (
    echo.
    echo [错误] 打包失败
)
deactivate
pause
