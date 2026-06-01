# LabVault 开发环境启动脚本 (PowerShell)
# 运行方法: ./start-dev.ps1

# 设置输出编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LabVault 开发环境启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "[1/3] 检查 Hub 服务器..." -ForegroundColor Yellow
$pythonExists = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExists) {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 进入 hub-server 目录
Set-Location hub-server

# 创建虚拟环境（如果不存在）
if (-not (Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Green
    python -m venv venv
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Hub 服务器准备就绪！" -ForegroundColor Green
Write-Host "请在新终端运行:" -ForegroundColor White
Write-Host "cd hub-server ; .\venv\Scripts\Activate.ps1 ; python main.py" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 返回项目根目录
Set-Location ..

# 检查 PC 客户端
Write-Host "[2/3] 检查 PC 客户端..." -ForegroundColor Yellow
Set-Location pc-client

# 检查 Node.js
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    Write-Host "[警告] 未找到 Node.js，请安装后再运行 PC 客户端" -ForegroundColor Yellow
}

# 检查 node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "Node 模块未安装，请运行: npm install" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "PC 客户端准备就绪！" -ForegroundColor Green
Write-Host "请在新终端运行:" -ForegroundColor White
Write-Host "cd pc-client ; npm run dev" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 返回项目根目录
Set-Location ..

# 检查 Leaf 代理
Write-Host "[3/3] 检查 Leaf 代理..." -ForegroundColor Yellow
Set-Location leaf-agent

if (-not (Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Green
    python -m venv venv
}

# 创建 watch 目录
if (-not (Test-Path "watch")) {
    New-Item -ItemType Directory -Path "watch" | Out-Null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Leaf 代理准备就绪！" -ForegroundColor Green
Write-Host "请在新终端运行:" -ForegroundColor White
Write-Host "cd leaf-agent ; .\venv\Scripts\Activate.ps1 ; python main.py" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   启动完成！" -ForegroundColor Cyan
Write-Host "   请分别打开三个终端运行各组件" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "按任意键退出"
