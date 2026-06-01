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

### 1. 启动 Hub 服务器

```bash
cd hub-server
pip install -r requirements.txt
python main.py
```

服务器将在 `http://localhost:8000` 启动。

默认管理员账号: `admin` / `admin123`

### 2. 启动 PC 客户端

```bash
cd pc-client
npm install
npm run dev
```

前端将在 `http://localhost:3000` 启动。

### 3. 配置 Leaf Agent (实验室电脑)

```bash
cd leaf-agent
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置文件
python main.py
```

## 技术栈

- **Hub 服务器**: Python + FastAPI + SQLite
- **PC 客户端**: React + TypeScript + Vite
- **Leaf Agent**: Python + Watchdog

## 项目结构

```
lab_admin/
├── hub-server/      # Hub 服务器
│   ├── main.py
│   ├── database.py
│   └── requirements.txt
├── pc-client/       # PC 前端客户端
│   ├── src/
│   └── package.json
└── leaf-agent/      # 实验室电脑代理
    ├── main.py
    └── requirements.txt
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

## 开发说明

本项目基于技术规格文档 SPEC1.txt 开发，包含完整的需求说明和设计文档。
