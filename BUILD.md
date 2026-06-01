# LabVault 打包说明
本指南将帮助您打包和部署 LabVault 系统。

## 目录
1. [Hub 服务器打包](#hub-服务器打包)
2. [PC 客户端打包](#pc-客户端打包)
3. [Leaf 代理打包](#leaf-代理打包)
4. [完整部署](#完整部署)

---

## Hub 服务器打包

### 方法一：直接运行源码部署（推荐用于开发）

```bash
cd hub-server

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置您的配置

# 运行服务器
python main.py
```

### 方法二：使用 Docker 部署（推荐用于生产）

创建 `Dockerfile`（需要您自己创建）：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

---

## PC 客户端打包

### 开发模式
```bash
cd pc-client

# 安装依赖
npm install

# 开发模式运行
npm run dev

# 构建生产版本
npm run build
```

### 打包为可执行文件（使用 Electron）

如需打包为独立可执行文件，您可以使用以下工具：

1. **使用 Vite + Electron：
```bash
# 需要配置 Electron 相关的依赖（需要您进一步扩展）
```

或者使用其他打包工具：
- **Electron Builder** 或 **Tauri** 等。

---

## Leaf 代理打包

### 直接运行
```bash
cd leaf-agent

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# 编辑 .env 文件配置

python main.py
```

### 打包为 Windows 可执行文件（使用 PyInstaller）

创建 `build-leaf.bat`（Windows）：
```batch
@echo off
cd leaf-agent
pip install pyinstaller
pyinstaller --onefile --name leaf-agent --icon icon.ico main.py
```

---

## 完整部署

### 一键启动脚本（Windows）

创建项目根目录的 `start-all.bat`：
```batch
@echo off
echo Starting LabVault...

echo.
echo Starting Hub Server...
start "Hub Server" cmd /k "cd hub-server && python main.py"

timeout /t 3 /nobreak

echo.
echo Starting PC Client...
start "PC Client" cmd /k "cd pc-client && npm run dev"

echo.
echo All services started!
pause
```

### 生产环境部署建议

1. **Hub 服务器**：
   - 使用 systemd 或 Docker 容器部署
   - 配置 Nginx 作为反向代理
   - 使用 HTTPS 证书配置

2. **PC 客户端**：
   - 部署到 CDN 或静态文件服务器
   - 或打包为桌面应用程序

3. **Leaf 代理**：
   - 配置为开机自启动服务
   - 使用 Supervisor 或 Windows 服务

---

## 配置说明

### 重要配置项

#### Hub 服务器 `.env`：
```
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
ACCESS_TOKEN_EXPIRE_MINUTES=1440
STORAGE_DIR=storage
```

#### Leaf 代理 `.env`：
```
HUB_URL=http://localhost:8000
DEVICE_NAME=Your-Device
WATCH_DIR=./watch
ZONE=DATA
```

---

## 常见问题

### Q: 如何更新系统？

A: Git pull 更新代码，然后重启服务即可。

### Q: 数据库迁移？

A: 数据库结构如有变化会自动初始化，SQLite 数据库文件会自动创建。

### Q: 备份数据？

A: 备份 `hub-server/storage/` 目录和 `labvault.db` 数据库文件。

