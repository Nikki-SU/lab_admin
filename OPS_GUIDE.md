# LabVault 运维手册

## 目录

1. [系统概述](#系统概述)
2. [静态风险分析](#静态风险分析)
3. [动态风险分析](#动态风险分析)
4. [物理风险应对](#物理风险应对)
5. [日常运维](#日常运维)
6. [备份与恢复](#备份与恢复)
7. [故障排查](#故障排查)

---

## 系统概述

LabVault 是一个实验室数据存储与管理系统，包含三个核心组件：

| 组件 | 职责 | 技术栈 |
|------|------|--------|
| **Hub Server** | 中央服务器，负责数据存储、权限管理、日志记录 | Python + FastAPI + SQLite |
| **Leaf Agent** | 部署在实验电脑，自动监控和上传数据 | Python + Watchdog |
| **PC Client** | 个人客户端，提供用户界面 | React + TypeScript + (Electron) |

### 关键特性

- 数据只读存储 + 编辑可追溯
- 四级权限体系
- 全程操作日志
- 文件自动同步

---

## 静态风险分析

### 1. 依赖与库风险

#### 1.1 已知依赖版本

**Hub Server / Leaf Agent ([requirements.txt](file:///workspace/hub-server/requirements.txt))**

| 依赖 | 当前版本 | 风险等级 | 说明 |
|------|----------|----------|------|
| fastapi | 0.115.0 | 🟡 中等 | 活跃维护，但需关注安全更新 |
| uvicorn | 0.32.0 | 🟡 中等 | ASGI 服务器，稳定 |
| sqlalchemy | 2.0.35 | 🟡 中等 | ORM 框架，功能完整 |
| pydantic | 2.9.2 | 🟡 中等 | 数据验证库 |
| python-jose | 3.3.0 | 🔴 高 | 2022年后无更新，需密切关注 |
| passlib | 1.7.4 | 🔴 高 | 2020年后无更新，考虑替换为 bcrypt |
| python-multipart | 0.0.12 | 🟡 中等 | 表单解析库 |
| python-dotenv | 1.0.1 | 🟢 低 | 环境变量管理 |
| pyinstaller | 6.11.0 | 🟡 中等 | 打包工具 |
| requests | 2.31.0 | 🔴 高 | 2023年版本，存在已知漏洞，建议升级 |
| watchdog | 5.0.3 | 🟡 中等 | 文件系统监控 |

**PC Client ([package.json](file:///workspace/pc-client/package.json))**

| 依赖 | 当前版本 | 风险等级 | 说明 |
|------|----------|----------|------|
| react | 18.2.0 | 🟡 中等 | 主流版本，2023年 |
| react-dom | 18.2.0 | 🟡 中等 | 同上 |
| axios | 1.6.0 | 🟡 中等 | HTTP 客户端 |
| electron | 28.x | 🟡 中等 | 桌面应用框架 |

#### 1.2 依赖风险应对

**高风险项替换计划：**

1. **passlib → bcrypt**
   - passlib 已停止维护
   - 替换为 `bcrypt` 库直接处理密码哈希
   - 影响文件：[hub-server/main.py](file:///workspace/hub-server/main.py)

2. **requests 升级**
   - 当前版本有 CVE 漏洞
   - 升级到 2.32.x 或更高版本

3. **python-jose 替换**
   - 考虑迁移到 `authlib` 或 `PyJWT`

**依赖监控方法：**
```bash
# 检查 Python 依赖漏洞
pip install safety
safety check --full-report

# 检查 npm 依赖漏洞
cd pc-client
npm audit
```

**更新策略：**
- 每季度进行一次安全更新
- 生产环境使用 `==` 固定版本号
- 测试环境先验证，再升级生产环境

---

### 2. 系统更新风险

#### 2.1 操作系统兼容性

**Linux 平台：**
- ✅ 主流发行版（Ubuntu 20.04+, Debian 11+, CentOS 8+）
- ⚠️ 需要 Python 3.8+
- ⚠️ 系统级 Python 更新可能破坏虚拟环境

**Windows 平台：**
- ✅ Windows 10/11
- ⚠️ Windows Server 2019+
- ⚠️ 打包的 EXE 可能在大版本更新后需要重新打包

**macOS 平台（未测试）：**
- ❌ 需要额外适配 M 系列芯片

#### 2.2 系统更新应对

**操作系统更新前：**
1. 完整备份数据和数据库
2. 在测试环境先验证更新
3. 记录当前运行状态（进程、端口、配置）

**更新后检查清单：**
- [ ] 数据库文件完整性
- [ ] Hub Server 端口监听正常
- [ ] Leaf Agent 监控功能正常
- [ ] PC Client 登录和上传功能正常
- [ ] 权限控制正常工作

---

### 3. 数据库风险

#### 3.1 SQLite 限制

**已知问题：**
- 并发写入性能差（SQLite 锁机制）
- 没有用户/密码认证（文件系统权限保护）
- 单文件存储，损坏风险较高
- 无内置复制/集群支持

**代码位置：** [hub-server/database.py](file:///workspace/hub-server/database.py#L7-L10)

#### 3.2 数据库风险应对

**权限保护：**
```bash
# 设置数据库文件权限（仅运行用户可读写）
chmod 600 labvault.db
chown labvault:labvault labvault.db
```

**并发处理建议：**
- 当前已设置 `check_same_thread=False`，但这不是真正的并发安全
- 考虑添加数据库连接池（SQLAlchemy 连接池已部分解决）
- 高并发场景考虑迁移到 PostgreSQL/MySQL

**定期检查：**
- 每半年执行一次数据库完整性检查
- 监控文件大小增长，设置告警阈值

---

## 动态风险分析

### 1. 同步冲突

#### 1.1 冲突场景

| 场景 | 风险等级 | 影响 | 实际概率 |
|------|----------|------|----------|
| **多 Leaf Agent 同时上传同一路径文件** | 🟢 低 | 后上传的会覆盖先上传的，且标记为编辑 | **极低** - 不同实验室电脑负责不同实验类型 |
| **同一文件在短时间内多次修改** | 🟡 中等 | 产生大量版本，占用存储空间 | 中等 - 同一设备上的文件可能被编辑 |
| **网络中断导致部分上传** | 🟡 中等 | 产生不完整的文件记录 | 中等 - 网络不稳定时可能发生 |

#### 1.2 当前实现分析

**后端冲突处理：** [hub-server/main.py](file:///workspace/hub-server/main.py#L256-L324)
- ✅ 检测相同路径文件
- ✅ 标记为编辑状态并增加编辑计数
- ❌ 没有版本号/时间戳比较
- ❌ 没有冲突解决界面

**实际场景说明：**
由于 Leaf Agent 部署在不同的实验室电脑上，每台设备负责特定类型的实验（如 FT-IR、XRD、GC-MS 等），天然产生不同类型的数据文件，**多设备上传同一文件路径的概率极低**。系统设计已通过设备名称作为路径前缀（`/${DEVICE_NAME}/path`）进一步隔离数据，确保不同设备的数据不会冲突。

#### 1.3 同步冲突应对

**运维措施：**
1. **路径隔离** - 系统已自动使用设备名称作为路径前缀，确保不同设备的数据天然隔离
2. **编辑检测** - 同一设备上的文件修改会被标记为"已编辑"，便于追溯
3. **定期审查** - 定期查看 `edited=True` 的文件列表，确认是否为正常操作

**配置建议（Leaf Agent）：**
```env
# leaf-agent/.env
DEVICE_NAME=FT-IR-Analyzer-01  # 使用有意义的设备名称，便于识别
WATCH_DIR=./watch
```

**冲突场景的实际处理：**
- **同一设备多次修改**：正常流程，系统会记录编辑次数和标记
- **误操作上传相同文件**：会被标记为编辑，可通过日志追溯操作者和时间
- **网络中断**：Leaf Agent 已实现 3 次重试机制，减少部分上传的概率

---

### 2. 多线程/并发冲突

#### 2.1 并发问题点

| 组件 | 问题 | 代码位置 |
|------|------|----------|
| **Hub Server** | 数据库写操作无事务保护 | [hub-server/main.py](file:///workspace/hub-server/main.py) |
| **Hub Server** | 文件写入无原子性保证 | [hub-server/main.py](file:///workspace/hub-server/main.py#L267-L269) |
| **Leaf Agent** | 状态文件读写无锁 | [leaf-agent/main.py](file:///workspace/leaf-agent/main.py#L37-L43) |

#### 2.2 并发风险应对

**数据库事务增强：**
当前部分操作有事务，但建议所有写操作都显式使用事务。

**文件写入原子性：**
```python
# 改进方案示例
temp_path = f"{storage_path}.tmp"
with open(temp_path, "wb") as f:
    f.write(content)
os.rename(temp_path, storage_path)  # 原子操作
```

**Leaf Agent 状态文件保护：**
- 使用文件锁防止并发读写
- 考虑使用 SQLite 存储状态而不是 JSON

---

### 3. 超限风险

#### 3.1 已实现的限制

| 限制项 | 当前值 | 配置位置 |
|--------|--------|----------|
| 文件大小 | 100MB | [hub-server/main.py](file:///workspace/hub-server/main.py#L42) |

#### 3.2 缺失的限制

⚠️ **高优先级添加：**
- 单用户存储空间配额
- 单次上传文件数量限制
- 请求频率限制（防滥用）
- 日志文件大小限制
- Leaf Agent 状态文件大小限制

#### 3.3 超限风险应对

**配置建议：**
```env
# hub-server/.env
MAX_FILE_SIZE=104857600        # 100MB
MAX_USER_STORAGE=10737418240   # 10GB
MAX_LOG_SIZE=104857600         # 100MB
RATE_LIMIT_PER_MINUTE=100      # 每分钟请求数
```

**监控指标：**
- 每用户存储使用量
- 每日上传文件数量
- 存储空间总使用率（告警阈值：85%）

---

### 4. 运行时异常风险

#### 4.1 关键异常点

| 位置 | 风险 | 当前处理 | 建议 |
|------|------|----------|------|
| [hub-server/main.py](file:///workspace/hub-server/main.py) | 文件系统满 | 无 | 磁盘空间监控 + 优雅降级 |
| [leaf-agent/main.py](file:///workspace/leaf-agent/main.py) | 网络断开 | 重试3次 | 指数退避 + 本地队列 |
| [leaf-agent/main.py](file:///workspace/leaf-agent/main.py) | 监控目录被删除 | 无 | 健康检查 + 告警 |

#### 4.2 异常应对建议

**添加健康检查端点（Hub Server）：**
```python
@api_router.get("/health")
def health_check():
    # 检查数据库连接
    # 检查磁盘空间
    # 检查存储目录权限
    return {"status": "healthy"}
```

**添加 Leaf Agent 心跳：**
- 定期向 Hub 上报状态
- Hub 检测离线设备并告警

---

## 物理风险应对

### 1. 硬件风险

#### 1.1 服务器硬件故障

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 硬盘损坏 | 🟡 中 | 🔴 高 | RAID 1/5/6 + 定期备份 |
| 电源故障 | 🟢 低 | 🟡 中 | UPS + 双电源 |
| 网络中断 | 🟡 中 | 🟡 中 | 多网卡绑定 + 备用网络 |
| 服务器整机故障 | 🟢 低 | 🔴 高 | 冷备机器 + 快速恢复流程 |

#### 1.2 硬盘损坏应对

**推荐配置：**
- Hub Server 使用 RAID 1（镜像）或 RAID 5
- 存储目录使用独立分区
- 操作系统与数据分离

**检测预警：**
```bash
# 定期检查 SMART 状态
smartctl -a /dev/sda

# 检查文件系统错误
fsck -n /dev/sda1
```

---

### 2. 数据丢失风险

#### 2.1 数据丢失场景

| 场景 | 应对措施 | 恢复时间目标 |
|------|----------|--------------|
| 人为误删除 | 版本控制 + 回收站 | < 1小时 |
| 勒索软件攻击 | 离线备份 + 多副本 | < 4小时 |
| 自然灾害 | 异地备份 | < 24小时 |
| 软件 BUG | 事务 + 定期快照 | < 1小时 |

#### 2.2 备份策略

**3-2-1 备份原则：**
1. **3 份数据** - 生产 + 2个备份
2. **2 种介质** - 硬盘 + 云存储/磁带
3. **1 份异地** - 不同物理地点

**备份频率：**
| 数据类型 | 全量备份 | 增量备份 | 保留时间 |
|----------|----------|----------|----------|
| 数据库 | 每日 | 每小时 | 90天 |
| 文件存储 | 每日 | - | 90天 |
| 配置文件 | 每次变更 | - | 永久 |

**备份内容清单：**
- ✅ `labvault.db` 数据库文件
- ✅ `storage/` 文件存储目录
- ✅ `.env` 配置文件
- ✅ 日志文件（可选）

---

### 3. 环境风险

#### 3.1 机房环境要求

| 指标 | 推荐值 | 告警阈值 |
|------|--------|----------|
| 温度 | 18-24°C | > 28°C 或 < 15°C |
| 湿度 | 40-60% | > 70% 或 < 30% |
| 电源稳定度 | ±10% | ±20% |
| UPS 续航 | ≥ 30分钟 | < 10分钟 |

#### 3.2 环境监控建议

部署环境监控系统，实时采集：
- 温度/湿度
- 电源状态
- 烟雾检测
- 安防监控

---

### 4. 安全风险

#### 4.1 访问安全

**网络隔离：**
- Hub Server 建议部署在内网
- 如需公网访问，使用 VPN 或白名单
- 配置防火墙规则，仅开放必要端口（8000）

**认证安全：**
- 修改默认 `admin` 密码！
- 定期轮换 `SECRET_KEY`
- 建议启用 HTTPS（反向代理 + TLS）

**审计日志：**
- 所有操作已记录到 `logs` 表
- 定期审查管理员操作
- 保存审计日志 180天以上

#### 4.2 数据安全

**传输加密：**
- 生产环境必须使用 HTTPS
- 建议使用 TLS 1.3
- 可以使用 Nginx/Caddy 作为反向代理

**静态加密（可选增强）：**
- 敏感文件可考虑加密存储
- 数据库加密（SQLCipher）

---

## 日常运维

### 1. 每日检查清单

- [ ] Hub Server 进程运行状态
- [ ] 磁盘空间使用率（< 80%）
- [ ] 最近 24 小时错误日志
- [ ] Leaf Agent 在线状态
- [ ] 新上传文件数量

### 2. 每周检查清单

- [ ] 数据库完整性检查
- [ ] 备份执行情况验证
- [ ] 用户权限审计
- [ ] 磁盘 SMART 健康状态

### 3. 月度维护任务

- [ ] 依赖安全更新检查
- [ ] 日志归档和清理
- [ ] 性能指标趋势分析
- [ ] 备份恢复演练（季度）

---

## 备份与恢复

### 1. 备份脚本示例

**Windows 备份脚本（`backup.bat`）：**
```batch
@echo off
set BACKUP_DIR=D:\backups\labvault
set DATE=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%

mkdir %BACKUP_DIR%\%DATE%

REM 备份数据库
copy hub-server\labvault.db %BACKUP_DIR%\%DATE%\

REM 备份文件存储
xcopy /E /I hub-server\storage %BACKUP_DIR%\%DATE%\storage\

REM 备份配置
copy hub-server\.env %BACKUP_DIR%\%DATE%\
copy leaf-agent\.env %BACKUP_DIR%\%DATE%\leaf.env

echo Backup completed: %DATE%
```

**Linux 备份脚本（`backup.sh`）：**
```bash
#!/bin/bash
BACKUP_DIR="/data/backups/labvault"
DATE=$(date +"%Y%m%d_%H%M%S")

mkdir -p $BACKUP_DIR/$DATE

# 备份数据库
cp hub-server/labvault.db $BACKUP_DIR/$DATE/

# 备份文件存储
rsync -av hub-server/storage/ $BACKUP_DIR/$DATE/storage/

# 备份配置
cp hub-server/.env $BACKUP_DIR/$DATE/
cp leaf-agent/.env $BACKUP_DIR/$DATE/leaf.env

# 清理30天前的备份
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### 2. 恢复步骤

**完整恢复流程：**

1. **停止所有服务**
   ```bash
   # 停止 Hub Server
   # 停止所有 Leaf Agent
   # 通知用户暂时不可用
   ```

2. **恢复数据库**
   ```bash
   cp backup/labvault.db hub-server/
   chmod 600 hub-server/labvault.db
   ```

3. **恢复文件存储**
   ```bash
   rsync -av backup/storage/ hub-server/storage/
   ```

4. **恢复配置文件**
   ```bash
   cp backup/.env hub-server/
   # 检查配置项是否正确
   ```

5. **验证数据完整性**
   - 启动 Hub Server
   - 用测试账号登录
   - 验证文件列表和权限

6. **恢复服务**
   - 逐步启动 Leaf Agent
   - 通知用户系统恢复

---

## 故障排查

### 1. Hub Server 无法启动

| 症状 | 可能原因 | 排查步骤 |
|------|----------|----------|
| 端口被占用 | 其他程序使用 8000 | `netstat -ano | findstr :8000` (Windows) / `lsof -i :8000` (Linux) |
| 数据库损坏 | 文件系统错误 | 检查 `labvault.db` 完整性 |
| 配置错误 | `.env` 格式问题 | 检查日志输出 |
| 依赖缺失 | 虚拟环境问题 | 重新安装依赖 |

### 2. Leaf Agent 无法上传

| 症状 | 可能原因 | 排查步骤 |
|------|----------|----------|
| 连接失败 | 网络不通 | `ping hub-server` / 检查防火墙 |
| 认证失败 | Token 过期 | 重新认证 / 检查时间同步 |
| 权限错误 | 目录无权限 | 检查 `WATCH_DIR` 权限 |
| 文件冲突 | 同名文件存在 | 查看后端日志 |

### 3. PC Client 无法登录

| 症状 | 可能原因 | 排查步骤 |
|------|----------|----------|
| 连接超时 | API 地址错误 | 检查 `API_BASE` 配置 |
| 认证失败 | 密码错误 | 重置密码 / 检查账号状态 |
| CORS 错误 | 跨域配置 | 检查后端 CORS 配置 |

### 4. 获取日志

**Hub Server 日志：**
```bash
# 查看应用日志（标准输出）
# 建议配置日志文件输出
```

**Leaf Agent 日志：**
- 控制台输出
- 检查 `leaf_state.json` 状态文件

**数据库查询日志：**
```sql
-- 查看最近操作
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100;

-- 查看错误相关操作
SELECT * FROM logs WHERE action LIKE '%ERROR%';
```

---

## 附录

### A. 端口清单

| 端口 | 组件 | 说明 |
|------|------|------|
| 8000 | Hub Server | API 服务 |
| 3000 | PC Client (Dev) | 仅开发环境 |

### B. 目录结构说明

```
hub-server/
├── labvault.db          # 数据库文件 ⭐ 关键
├── storage/             # 文件存储目录 ⭐ 关键
├── .env                 # 配置文件
└── main.py              # 主程序

leaf-agent/
├── leaf_state.json      # 同步状态文件
├── .env                 # 配置文件
└── main.py              # 主程序
```

### C. 联系方式

- 技术支持：[待填写]
- 应急响应：[待填写]

---

**文档版本：** 1.0  
**最后更新：** 2026-06-02  
**维护者：** LabVault 运维团队
