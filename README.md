# LabVault - 实验室数据存储系统

为理工科实验室设计的本地部署数据存储与管理系统。

## 功能特性

- 🔒 **编辑可追溯**: 数据在Hub端以只读存储，编辑操作记录日志并标记失信
- ⚠️ **失信标记**: 被编辑过的文件自动归类，明确标识
- 🔐 **权限管理**: 四级权限体系，确保数据安全
- 📤 **自动归集**: 实验室电脑数据自动上传至中央服务器
- 📝 **全程可溯**: 所有操作留痕，日志不可篡改
- 🤝 **协作共享**: 独立协作区，支持汇报资料上传下载

## 系统架构

```
┌─────────────────┐
│   Hub (服务器)  │
│  - 数据存储     │
│  - 权限管理     │
│  - 日志记录     │
└────────┬────────┘
         │
┌────────┴────────┐
│  Leaf (实验电脑) │ ← 自动上传
└─────────────────┘
         │
┌────────┴────────┐
│  PC (个人设备)   │ ← 上传/下载
└─────────────────┘
```

## 快速开始

### Windows 快速启动

直接双击运行 `start-dev.bat`，一键启动开发环境。

### 手动启动

#### 1. 启动 Hub 服务器

```bash
cd hub-server
pip install -r requirements.txt
python main.py
```

服务器将在 `http://localhost:8000` 启动。

默认管理员账号: `admin` / `admin123`

#### 2. 启动 PC 客户端

```bash
cd pc-client
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动。

#### 3. 配置 Leaf Agent (实验室电脑)

```bash
cd leaf-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置文件
python main.py
```

## 打包成可执行文件

### Windows 平台

#### 先决条件

- Python 3.8+
- Node.js 18+

#### 一键打包所有组件

双击运行 `build-windows.bat`，将自动打包所有组件到 `dist` 目录。

#### 单独打包

- **打包 Hub Server**: 双击 `build-hub.bat`
- **打包 Leaf Agent**: 双击 `build-leaf.bat`
- **打包 PC Client**: 双击 `build-pc.bat`

#### 打包输出

打包完成后，各组件位置：
- Hub Server: `hub-server/dist/labvault-hub.exe`
- Leaf Agent: `leaf-agent/dist/labvault-leaf.exe`
- PC Client: `pc-client/dist-electron/` (Electron 安装包)

### Linux 平台

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包 Hub Server
cd hub-server
pyinstaller --onefile --name labvault-hub main.py

# 打包 Leaf Agent
cd ../leaf-agent
pyinstaller --onefile --name labvault-leaf main.py

# 构建 PC Client (Web 版本)
cd ../pc-client
npm install
npm run build
```

## 技术栈

- **Hub 服务器**: Python + FastAPI + SQLite
- **PC 客户端**: React + TypeScript + Vite + Electron
- **Leaf Agent**: Python + Watchdog
- **打包工具**: PyInstaller + Electron Builder

## 项目结构

```
lab_admin/
├── hub-server/         # Hub 服务器
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   └── hub.spec       # PyInstaller 配置
├── pc-client/          # PC 前端客户端
│   ├── src/
│   ├── electron/      # Electron 主进程
│   ├── package.json
│   └── vite.config.ts
├── leaf-agent/         # 实验室电脑代理
│   ├── main.py
│   ├── requirements.txt
│   └── leaf.spec      # PyInstaller 配置
├── build-windows.bat  # Windows 一键打包脚本
├── build-hub.bat      # 打包 Hub
├── build-leaf.bat     # 打包 Leaf
├── build-pc.bat       # 打包 PC Client
└── start-dev.bat      # 开发环境一键启动
```

## 权限级别

| 级别 | 名称 | 权限 |
|------|------|------|
| L1 | ADMIN | 全部权限 |
| L2 | GROUP_ADMIN | 管理本组数据和用户 |
| L3 | MEMBER | 管理个人数据，协作区上传 |
| L4 | TRAINEE | 只读访问授权数据 |

## API 文档

启动 Hub 服务器后，访问 `http://localhost:8000/docs` 查看完整的 API 文档。

## 配置说明

复制 `.env.example` 为 `.env` 并根据需要修改配置项：

- `SECRET_KEY`: JWT 密钥（生产环境请务必修改）
- `MAX_FILE_SIZE`: 最大文件大小（字节）
- `HUB_URL`: Hub 服务器地址（Leaf Agent 使用）
- `WATCH_DIR`: Leaf Agent 监控目录

## 开发说明

本项目基于技术规格文档 SPEC1.txt 开发，包含完整的需求说明和设计文档。
