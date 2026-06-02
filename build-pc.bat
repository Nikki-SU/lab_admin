@echo off
chcp 65001 >nul
echo ========================================
echo 打包 PC Client
echo ========================================
echo.

cd /d "%~dp0pc-client"
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)

echo.
echo 构建 Web 版本...
call npm run build
if errorlevel 1 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo 构建 Electron 版本...
set ELECTRON=true
call npm run electron:build

if exist "dist-electron" (
    echo.
    echo [成功] 打包完成！
    echo 输出目录: %~dp0pc-client\dist-electron
) else (
    echo.
    echo [警告] Electron 打包失败，但 Web 构建已完成
    echo Web 输出: %~dp0pc-client\dist
)
pause
