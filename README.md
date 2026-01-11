# 智能邮件代理系统 (MailAgent)

<div align="center">

一个基于 AI 的现代化邮件管理系统，集成 Web 界面和命令行界面，支持多邮箱账户管理、智能回复、AI 写作等功能。

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.125+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-blue.svg)](https://www.typescriptlang.org/)

</div>

##  核心功能

### 现代化 Web 界面
- **多账户管理**: 同时登录和切换多个邮箱账户（网易 163、QQ、Gmail、Outlook）
- **邮件列表**: 收件箱、已发送、草稿箱、星标、归档、垃圾箱分类管理
- **邮件详情**: 完整显示邮件内容，支持 HTML 渲染
- **智能搜索**: 按邮件内容、发件人快速搜索

### AI 智能助手
- **AI 自动回复**: 一键生成得体的邮件回复草稿
- **AI 写作**: 自然语言描述需求，AI 自动生成完整邮件
- **智能对话**: 通过聊天界面使用自然语言操作邮件

### 完整邮件功能
- **发送/回复**: 支持 HTML 和纯文本邮件
- **邮件操作**: 归档、删除、转发、标记已读/未读、加星标
- **批量操作**: 批量归档、删除、分类邮件

### 命令行模式
- 使用自然语言指令控制所有邮件操作
- 适合自动化脚本和高级用户

## 快速开始

### 前置要求

- **Python 3.13+** 
- **Node.js 18+** 
- **UV**（Python 包管理器，推荐）或 **pip**
- **邮箱账号**：支持网易 163、QQ、Gmail、Outlook 等

### 1. 克隆项目

```bash
git clone https://github.com/your-username/mail_agent.git
cd mail_agent
```

### 2. 配置 DeepSeek API（必需）

本项目的 AI 功能依赖 DeepSeek API，需要配置 API 密钥：

#### 获取 API 密钥

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并获取 API 密钥（免费额度通常足够个人使用）

#### 配置方式

复制配置文件模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，**仅需配置 DeepSeek API**：

```env
# DeepSeek API 配置（必需）
DEEPSEEK_API_KEY=sk-your-api-key-here
```

> **💡 提示**：邮箱账户配置不需要在 `.env` 中填写，可以在 Web 界面登录时输入

### 3. 安装依赖

#### 后端依赖

使用 **UV**（推荐）：

```bash
uv sync
```

或使用 **pip**：

```bash
pip install -e .
```

#### 前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 启动应用

#### 方式一：Web 应用（推荐）

**第 1 步：启动后端服务**

打开终端 1：

```bash
python server.py
```

后端将在 `http://localhost:8000` 运行

**第 2 步：启动前端**

打开终端 2：

```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 运行

**第 3 步：浏览器访问**

打开浏览器访问 `http://localhost:5173`

**第 4 步：登录邮箱**

在 Web 界面：
1. 选择邮箱服务商（网易 163 / QQ / Gmail / Outlook）
2. 输入邮箱地址
3. 输入授权码（见下方[邮箱配置指南](#-邮箱配置指南)）
4. 点击登录

✅ 完成！开始使用智能邮件助手

#### 💻 方式二：命令行模式

```bash
python agent.py
```

使用自然语言指令操作邮件（见[使用示例](#-使用示例)）

## 📮 邮箱配置指南

### 网易 163 邮箱

1. 登录网页版 163 邮箱
2. 点击顶部 **设置** → **POP3/SMTP/IMAP**
3. 开启 **IMAP/SMTP 服务**
4. 点击 **新增授权密码**，按提示发送短信验证
5. 复制生成的 **授权码**（16 位字符串）作为登录密码

**服务器配置**：
- IMAP: `imap.163.com:993`
- SMTP: `smtp.163.com:465`

### QQ 邮箱

1. 登录网页版 QQ 邮箱
2. 点击顶部 **设置** → **账户**
3. 向下滚动找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务**
4. 开启 **IMAP/SMTP 服务**
5. 点击 **生成授权码**，按提示验证身份
6. 复制生成的 **授权码**（16 位字符串）作为登录密码

**服务器配置**：
- IMAP: `imap.qq.com:993`
- SMTP: `smtp.qq.com:465`

### Gmail

1. 启用 [两步验证](https://myaccount.google.com/security)
2. 访问 [应用专用密码](https://myaccount.google.com/apppasswords)
3. 生成密码（选择"邮件"和设备）
4. 使用生成的 16 位密码登录

**服务器配置**：
- IMAP: `imap.gmail.com:993`
- SMTP: `smtp.gmail.com:465`

### Outlook / Hotmail

通常可直接使用账户密码。如开启了两步验证，需生成应用密码。

**服务器配置**：
- IMAP: `outlook.office365.com:993`
- SMTP: `smtp.office365.com:587`

> **⚠️ 重要**：国内邮箱（163/QQ）必须使用 **SMTP/IMAP 授权码**，不能使用登录密码！

## 📖 使用示例

### Web 界面操作

1. **查看邮件**：左侧切换邮箱分类（收件箱/已发送/草稿等）
2. **搜索邮件**：点击搜索图标，按内容或发件人搜索
3. **AI 回复**：
   - 点击邮件查看详情
   - 点击 **回复** 按钮
   - AI 自动生成回复草稿显示在右侧聊天区
   - 可编辑后发送
4. **AI 写邮件**：
   - 点击 **写邮件** 按钮
   - 填写收件人和主题
   - 点击 **AI 写作** 按钮
   - 输入需求（如"写一封请假邮件"）
   - AI 生成内容，可编辑后点击发送图标
5. **切换账户**：鼠标悬停在左上角用户头像，选择或添加账户

### 命令行模式示例

#### 基本操作
```bash
> 回复第一封邮件
> 归档邮件2
> 删除最近5封邮件
> 转发邮件1到user@example.com
```

#### 智能分析
```bash
> 总结邮件1
> 分析邮件2的优先级
> 列出最近10封邮件
```

#### 批量操作
```bash
> 归档前5封邮件
> 转发前3封邮件到admin@example.com
> 总结最近5封邮件
```

## 🏗️ 项目架构

```
mail_agent/
├── 📁 backend (Python + FastAPI)
│   ├── server.py           # FastAPI 主服务器
│   ├── agent.py            # 命令行入口
│   ├── nlu.py              # 自然语言理解引擎
│   ├── tasks.py            # 任务执行器
│   ├── mailer.py           # IMAP/SMTP 邮件客户端
│   ├── deepseek.py         # DeepSeek AI 集成
│   └── config.py           # 配置管理
│
├── 📁 frontend (React + TypeScript)
│   ├── src/
│   │   ├── login.tsx                  # 登录页面
│   │   ├── App.tsx                    # 主应用
│   │   └── components/
│   │       ├── Sidebar.tsx            # 侧边栏
│   │       ├── EmailList.tsx          # 邮件列表
│   │       ├── EmailDetail.tsx        # 邮件详情
│   │       ├── AssistantPanel.tsx     # AI 助手聊天面板
│   │       ├── ComposeModal.tsx       # 写邮件模态框
│   │       ├── SearchModal.tsx        # 搜索模态框
│   │       └── SettingsPanel.tsx      # 设置面板
│   └── package.json
│
├── .env.example            # 环境变量模板
└── pyproject.toml          # Python 项目配置
```

## 🔧 技术栈

### 后端
- **FastAPI**: 高性能异步 Web 框架
- **imaplib2**: IMAP 协议客户端
- **smtplib**: SMTP 邮件发送
- **DeepSeek API**: 大语言模型集成

### 前端
- **React 19**: 现代化 UI 库
- **TypeScript**: 类型安全
- **Vite**: 快速构建工具
- **Axios**: HTTP 客户端
- **Lucide React**: 图标库

## 📡 API 接口

后端提供完整的 RESTful API：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/login` | POST | 登录邮箱账户 |
| `/api/logout` | POST | 退出账户 |
| `/api/accounts` | GET | 获取已登录账户列表 |
| `/api/emails` | GET | 获取邮件列表 |
| `/api/emails/search` | POST | 搜索邮件 |
| `/api/emails/detail` | GET | 获取邮件详情 |
| `/api/emails/{id}/generate-reply` | POST | AI 生成回复 |
| `/api/chat` | POST | AI 对话接口 |
| `/api/generate/compose` | POST | AI 生成邮件内容 |
| `/api/compose` | POST | 发送新邮件 |
| `/api/reply` | POST | 回复邮件 |

详细 API 文档：启动后端后访问 `http://localhost:8000/docs`

## ⚙️ 配置说明

### 支持的邮箱服务商

| 服务商 | IMAP 服务器 | SMTP 服务器 | 端口 | 授权方式 |
|--------|-------------|-------------|------|----------|
| 网易 163 | imap.163.com | smtp.163.com | 993/465 | SMTP 授权码 |
| QQ 邮箱 | imap.qq.com | smtp.qq.com | 993/465 | SMTP 授权码 |
| Gmail | imap.gmail.com | smtp.gmail.com | 993/465 | 应用专用密码 |
| Outlook | outlook.office365.com | smtp.office365.com | 993/587 | 账户密码 |

### 环境变量（可选）

如需在命令行模式下使用或跳过 Web 登录，可在 `.env` 中配置：

```env
# 邮件账户（可选，Web 界面可直接登录）
EMAIL_ACCOUNT=your_email@example.com
EMAIL_PASSWORD=your_authorization_code

# IMAP/SMTP 服务器（可选，自动根据邮箱类型配置）
IMAP_SERVER=imap.163.com
SMTP_SERVER=smtp.163.com

# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-xxx
```

完整配置项参考 [.env.example](.env.example)

## 🛠️ 开发指南

### 构建生产版本

前端：

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist/`

### 运行测试

```bash
pytest                    # 后端测试
cd frontend && npm test   # 前端测试
```

### 代码风格

```bash
cd frontend
npm run lint              # 前端代码检查
```

## 📝 常见问题

### Q: 邮件列表加载很慢？

**A**: 系统已优化为轻量级模式，默认加载 20 封邮件。如仍然缓慢：
- 检查网络连接
- 尝试切换到其他 IMAP 文件夹
- 减少加载数量（修改 `server.py` 中的 `limit` 参数）

### Q: 无法连接邮箱服务器？

**A**: 请检查：
- 邮箱是否已开启 IMAP/SMTP 服务
- 是否使用了**授权码**（国内邮箱必须）而非登录密码
- 防火墙是否允许 993/465 端口
- 服务器地址是否正确

### Q: AI 功能不可用？

**A**: 请确保：
- `DEEPSEEK_API_KEY` 已正确配置在 `.env` 文件中
- API Key 有效且账户有可用额度
- 网络可访问 `api.deepseek.com`

### Q: 网易 163 邮箱授权码在哪里？

**A**: 
1. 登录网页版 163 邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启服务后点击"新增授权密码"
4. 发送短信验证后获取 16 位授权码

### Q: QQ 邮箱提示登录失败？

**A**: 
- 确认使用的是**授权码**（16 位），不是 QQ 密码
- 授权码生成：QQ 邮箱 → 设置 → 账户 → 开启 IMAP → 生成授权码

### Q: 如何添加多个邮箱账户？

**A**: 
- 鼠标悬停在左上角用户头像
- 点击"添加账号"
- 填写新邮箱信息并登录
- 可随时切换账户

## 安全注意事项

- ⚠️ **不要提交敏感信息**: `.env` 文件已加入 `.gitignore`
- 🔐 **使用授权码**: 邮箱密码建议使用应用专用密码
- 🛡️ **保护 API 密钥**: 妥善保管 DeepSeek API 密钥

## 故障排除

### 连接问题

- 检查邮箱账户和密码是否正确
- 确认已开启 SMTP/IMAP 服务
- 验证网络连接和防火墙设置

### API 问题

- 确认 DeepSeek API 密钥有效
- 检查 API 配额和限制
- 验证网络连接

## todo list

- 实现多个邮箱使用同一个agent
- cypht前端结合
