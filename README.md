# 智能邮件代理系统

一个基于 AI 的智能邮件管理系统，集成 Web 界面和命令行界面，支持邮件搜索、AI 自动回复、邮件撰写等功能。

## ✨ 功能特性

- 🎨 **Web 界面**: 现代化的邮件管理界面，支持邮件列表、搜索、详情查看
- 🤖 **AI 智能回复**: 基于 DeepSeek AI 的自动邮件回复生成
- ✍️ **AI 写邮件**: 使用自然语言描述需求，AI 自动生成邮件内容
- 📧 **邮件管理**: 支持归档、删除、转发、标记等完整操作
- 🔍 **智能搜索**: 按内容、发件人快速搜索邮件
- 💬 **命令行模式**: 使用自然语言指令控制邮件操作

## 🚀 快速开始

### 前置要求

- Python 3.13+
- Node.js 18+
- UV（Python 包管理器）或 pip
- 邮箱账号（支持 QQ、Gmail、Outlook 等）

### 1. 克隆项目

```bash
git clone <repository-url>
cd mail_agent
```

### 2. 配置环境变量

复制配置文件模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下**必需配置**：

```env
# DeepSeek API 
DEEPSEEK_API_KEY=your_deepseek_api_key

# IMAP/SMTP 服务器配置（QQ 邮箱示例）
IMAP_SERVER=imap.qq.com
SMTP_SERVER=smtp.qq.com
```

#### 📮 邮箱配置指南

**QQ 邮箱**：
1. 登录 QQ 邮箱 → 设置 → 账户
2. 开启 "IMAP/SMTP 服务"
3. 生成授权码（不是 QQ 密码）
4. 使用授权码作为 `EMAIL_PASSWORD`

**Gmail**：
1. 开启两步验证
2. 生成应用专用密码
3. 配置服务器：`imap.gmail.com` / `smtp.gmail.com`

**Outlook**：
- 服务器：`outlook.office365.com` / `smtp.office365.com`

#### 🔑 DeepSeek API 密钥

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并获取 API 密钥
3. 将密钥填入 `.env` 文件

### 3. 安装依赖

#### 后端依赖

使用 UV（推荐）：
```bash
uv sync
```

或使用 pip：
```bash
pip install -e .
```

#### 前端依赖

```bash
cd frontend
npm install
```

### 4. 启动应用

#### 方式一：完整 Web 应用（推荐）

**启动后端服务器**（终端 1）：
```bash
python server.py
```

后端将在 `http://localhost:8000` 运行

**启动前端开发服务器**（终端 2）：
```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 运行

打开浏览器访问 `http://localhost:5173` 即可使用 Web 界面！

#### 方式二：命令行模式

```bash
python agent.py
```

使用自然语言指令控制邮件操作（见下方示例）

## 📖 使用指南

### Web 界面功能

1. **邮件列表**：查看最近的邮件，点击查看详情
2. **搜索邮件**：点击搜索按钮，按内容或发件人搜索
3. **AI 回复**：在邮件详情页点击"回复"，AI 自动生成回复预览
4. **写邮件**：点击写邮件按钮，使用"AI 写作"功能自动生成邮件内容
5. **刷新邮件**：点击刷新按钮获取最新邮件

### 命令行模式示例

#### 基本操作
```
> 回复第一封邮件
> 归档邮件2
> 删除最近5封邮件
> 转发邮件1到user@example.com
```

#### 智能分析
```
> 总结邮件1
> 分析邮件2的优先级
> 列出最近10封邮件
```

#### 批量操作
```
> 归档前5封邮件
> 转发前3封邮件到admin@example.com
> 总结最近5封邮件
```

## 📁 项目结构

```
mail_agent/
├── agent.py              # 命令行邮件代理主程序
├── server.py             # FastAPI 后端服务器
├── config.py             # 配置文件
├── mailer.py             # 邮件客户端（IMAP/SMTP）
├── nlu.py                # 自然语言理解引擎
├── tasks.py              # 任务执行器
├── deepseek.py           # DeepSeek AI 集成
├── frontend/             # React 前端应用
│   ├── src/
│   │   ├── App.tsx       # 主应用组件
│   │   ├── components/   # 邮件组件
│   │   └── ...
│   └── package.json
├── .env.example          # 环境变量模板
└── pyproject.toml        # Python 项目配置
```

## 🔧 API 接口

后端提供以下 REST API 接口：

- `GET /api/accounts` - 获取邮箱账户列表
- `GET /api/emails` - 获取邮件列表
- `POST /api/emails/search` - 搜索邮件
- `GET /api/emails/detail` - 获取邮件详情
- `POST /api/emails/{id}/generate-reply` - 生成 AI 回复
- `POST /api/chat` - AI 对话接口
- `POST /api/generate/compose` - AI 生成邮件内容
- `POST /api/compose` - 发送邮件

详细 API 文档请参考 [API.md](API.md)

## ⚙️ 配置说明

### 支持的邮件服务商

| 服务商 | IMAP 服务器 | SMTP 服务器 | 端口 |
|--------|-------------|-------------|------|
| QQ 邮箱 | imap.qq.com | smtp.qq.com | 993/465 |
| Gmail | imap.gmail.com | smtp.gmail.com | 993/587 |
| Outlook | outlook.office365.com | smtp.office365.com | 993/587 |

### 环境变量

所有配置项都可以通过 `.env` 文件设置，详见 [.env.example](.env.example) 文件。

主要配置项：
- `EMAIL_ACCOUNT`: 邮箱账户
- `EMAIL_PASSWORD`: 邮箱密码/授权码
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `IMAP_SERVER`: IMAP 服务器地址
- `SMTP_SERVER`: SMTP 服务器地址

## 🛠️ 开发

### 构建前端

```bash
cd frontend
npm run build
```

构建产物将生成在 `frontend/dist` 目录。

### 运行测试

```bash
# 后端测试
pytest

# 前端测试
cd frontend
npm test
```

## 📝 常见问题

**Q: 邮件列表加载很慢？**  
A: 系统已优化为轻量级加载模式，默认只加载 20 封邮件。详情查看时才加载完整内容。

**Q: 无法连接邮箱服务器？**  
A: 请检查：
- `.env` 中的邮箱账户和密码是否正确
- 是否使用了授权码（不是登录密码）
- 防火墙是否允许 IMAP/SMTP 连接

**Q: AI 功能不可用？**  
A: 请确保 `DEEPSEEK_API_KEY` 已正确配置，并且账户有可用额度。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

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
