# LabVault 单电脑调试指南

在只有一台电脑的情况下，你可以同时运行所有三个组件来调试完整系统！

## 目录

1. [环境准备](#环境准备)
2. [快速启动](#快速启动)
3. [各组件调试方法](#各组件调试方法)
4. [模拟 Leaf Agent 文件上传](#模拟-leaf-agent-文件上传)
5. [常见调试场景](#常见调试场景)

---

## 环境准备

### 前置要求

- Python 3.8+
- Node.js 18+
- Git（可选）

### 克隆/准备项目

```bash
# 进入项目目录
cd /path/to/lab_admin

# 检查目录结构
ls -la
```

### 安装依赖

#### 1. Hub Server

```bash
cd hub-server

# 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活
venv\Scripts\activate

# Linux/Mac 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. Leaf Agent

```bash
cd leaf-agent

# 创建虚拟环境（可以与 hub-server 共用，或单独创建）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. PC Client

```bash
cd pc-client

# 安装依赖
npm install
```

---

## 快速启动

### 使用提供的脚本（Windows）

最简单的方法是使用我们之前创建的脚本：

```bash
# 直接运行
start-dev.bat
```

### 手动启动各组件

需要打开 **三个独立的终端窗口**（或标签页）：

#### 终端 1：启动 Hub Server

```bash
cd hub-server
venv\Scripts\activate
python main.py
```

看到类似输出即表示启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 终端 2：启动 Leaf Agent

```bash
cd leaf-agent
venv\Scripts\activate
python main.py
```

看到类似输出即表示启动成功：
```
🔬 LabVault Leaf Agent 启动
监控目录: ./watch
Hub URL: http://localhost:8000
设备名称: Leaf-Device
目标区域: DATA
状态文件: ./leaf_state.json
--------------------------------------------------
```

#### 终端 3：启动 PC Client

```bash
cd pc-client
npm run dev
```

看到类似输出即表示启动成功：
```
 VITE v5.x.x  ready in xxx ms

 ➜  Local:   http://localhost:3000/
 ➜  Network: use --host to expose
```

### 验证系统

1. 打开浏览器访问：http://localhost:3000
2. 登录默认账号：
   - 用户名：`admin`
   - 密码：`admin123`
3. 尝试上传一个文件，验证功能正常

---

## 各组件调试方法

### Hub Server 调试

#### 查看 API 文档

启动 Hub Server 后，访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

可以直接在浏览器中测试 API 接口！

#### 查看数据库

使用 SQLite 工具查看 `labvault.db`：

```bash
# 方法 1：使用 Python
cd hub-server
python -c "import sqlite3; db = sqlite3.connect('labvault.db'); cursor = db.cursor(); print('\nTables:', [t[0] for t in cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')]); db.close()"

# 方法 2：使用 sqlite3 命令行工具（如果已安装）
sqlite3 hub-server/labvault.db
```

常用查询：
```sql
-- 查看所有用户
SELECT * FROM users;

-- 查看所有文件
SELECT * FROM files ORDER BY upload_time DESC LIMIT 20;

-- 查看操作日志
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50;
```

#### 调试特定接口

在 `main.py` 中添加打印语句：

```python
@api_router.post("/files/upload")
async def upload_file(...):
    print(f"[DEBUG] 收到上传请求: zone={zone}, path={path}")
    print(f"[DEBUG] 文件大小: {len(content)} 字节")
    # ... 其他代码
```

---

### Leaf Agent 调试

#### 测试文件监控

在 `leaf-agent/watch` 目录中创建/修改文件，观察终端输出：

```bash
# 创建测试文件
echo "Test content" > leaf-agent/watch/test1.txt

# 修改文件
echo "Updated content" >> leaf-agent/watch/test1.txt

# 删除文件（不会触发上传，但可以测试监控）
del leaf-agent/watch/test1.txt
```

#### 查看同步状态

```bash
# 查看 leaf_state.json
type leaf-agent/leaf_state.json
```

#### 调试模式

在 `leaf-agent/main.py` 中添加更多调试输出：

```python
def on_created(self, event):
    if not event.is_directory:
        print(f"[DEBUG] 检测到新文件: {event.src_path}")
        time.sleep(1)
        self.upload_file(event.src_path)
```

---

### PC Client 调试

#### 浏览器开发者工具

1. 在浏览器中按 F12 打开开发者工具
2. **Console 标签**：查看 JavaScript 日志
3. **Network 标签**：查看 API 请求和响应
4. **Application 标签**：查看本地存储、Session 等

#### 调试 API 调用

在 `App.tsx` 中添加日志：

```typescript
const handleFileUpload = async (file: any) => {
  console.log('[DEBUG] 开始上传文件:', file.name);
  try {
    // ... 现有代码
    console.log('[DEBUG] 上传成功');
  } catch (err: any) {
    console.error('[DEBUG] 上传失败:', err);
    console.error('[DEBUG] 错误详情:', err.response?.data);
  }
};
```

#### 模拟不同用户登录

你可以通过直接修改数据库来创建测试用户，或通过 API 文档界面创建。

---

## 模拟 Leaf Agent 文件上传

### 快速测试方法 1：使用 PC Client

最简单的方法是直接用 PC Client 上传文件来模拟！

### 快速测试方法 2：手动触发上传

创建一个测试脚本来模拟 Leaf Agent 上传：

```python
# 创建文件: test-upload.py
import requests
import os

# 配置
HUB_URL = "http://localhost:8000/api"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    """获取登录 token"""
    response = requests.post(
        f"{HUB_URL}/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def upload_test_file(token, file_path, target_path):
    """上传测试文件"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        data = {
            "zone": "DATA",
            "path": target_path,
            "source_device": "Test-Device",
            "is_edit": "false"
        }
        
        response = requests.post(
            f"{HUB_URL}/files/upload",
            headers=headers,
            files=files,
            data=data
        )
    
    print(f"上传结果: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    # 获取 token
    token = get_token()
    
    # 创建一个测试文件
    test_file = "test-data.txt"
    with open(test_file, "w") as f:
        f.write("This is test data from simulated Leaf Agent!\n")
        f.write("Timestamp: " + __import__("datetime").datetime.now().isoformat())
    
    # 上传
    upload_test_file(token, test_file, "/Test-Device/test-data.txt")
    
    print("测试完成！")
```

运行测试：
```bash
cd hub-server
venv\Scripts\activate
python ../test-upload.py
```

### 快速测试方法 3：使用 Swagger UI

1. 访问 http://localhost:8000/docs
2. 使用 `/token` 接口获取 token（使用 admin/admin123）
3. 点击右上角 "Authorize" 按钮，输入：`Bearer <你的token>`
4. 使用 `/files/upload` 接口上传文件

---

## 常见调试场景

### 场景 1：测试编辑检测

```bash
# 步骤 1：创建初始文件
echo "Version 1" > leaf-agent/watch/edittest.txt

# 等待上传完成...

# 步骤 2：修改文件
echo "Version 2" > leaf-agent/watch/edittest.txt

# 步骤 3：在 PC Client 中查看 - 应该看到标记为"已编辑"的文件！
```

### 场景 2：测试不同用户权限

1. 以 admin 登录
2. 通过 API 文档创建不同级别的用户（L2、L3、L4）
3. 用不同用户登录，验证权限控制

### 场景 3：测试网络中断

1. 在 Leaf Agent 上传过程中，临时停止 Hub Server（Ctrl+C）
2. 观察 Leaf Agent 的重试机制
3. 重新启动 Hub Server，验证文件是否最终上传成功

### 场景 4：测试大文件上传

创建一个较大的文件测试：

```bash
# 创建 50MB 测试文件
fsutil file createnew largefile.dat 52428800

# 复制到 watch 目录
copy largefile.dat leaf-agent/watch\
```

验证是否能正常上传（受 MAX_FILE_SIZE 配置限制）。

---

## 调试时的快捷操作

### 重置数据库（测试时有用）

⚠️ **警告**：这会删除所有数据，仅用于测试！

```bash
cd hub-server

# 停止 Hub Server（如果正在运行）

# 备份当前数据库（可选）
copy labvault.db labvault.db.backup

# 删除数据库和存储文件
del labvault.db
rmdir /s /q storage

# 重新启动 Hub Server - 会自动创建新数据库
python main.py
```

### 重置 Leaf Agent 状态

```bash
cd leaf-agent
del leaf_state.json

# 重启 Leaf Agent - 会重新上传所有文件
```

### 查看所有组件状态

创建一个状态检查脚本：

```batch
# check-status.bat
@echo off
echo === Hub Server ===
netstat -ano | findstr :8000
echo.
echo === PC Client ===
netstat -ano | findstr :3000
echo.
echo === Files ===
dir hub-server\labvault.db
dir leaf-agent\leaf_state.json
```

---

## 推荐的调试工作流

1. **启动 Hub Server** - 始终最先启动
2. **启动 PC Client** - 验证基础功能
3. **用 PC Client 做基础测试** - 上传、浏览、下载
4. **启动 Leaf Agent** - 测试自动上传
5. **做编辑测试** - 修改文件验证编辑检测
6. **权限测试** - 创建不同用户测试权限控制

---

## 常见问题排查

### 问题：端口被占用

```bash
# Windows 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 结束占用进程（替换 <PID> 为实际 ID）
taskkill /PID <PID> /F
```

### 问题：Leaf Agent 无法连接 Hub

- 确认 Hub Server 正在运行
- 检查 `HUB_URL` 配置（应该是 `http://localhost:8000`）
- 检查是否有防火墙阻止

### 问题：PC Client 无法连接 API

- 检查 `API_BASE` 配置（应该是 `/api`）
- 查看浏览器 Console 的网络请求错误

---

祝你调试顺利！有问题随时查看各组件的终端输出。
