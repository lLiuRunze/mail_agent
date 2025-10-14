# 智能邮件代理系统

一个基于自然语言处理的智能邮件管理系统，支持自动回复、邮件归档、批量操作等功能。

## 功能特性

- 🤖 **智能回复**: 基于 DeepSeek AI 的自动邮件回复生成
- 📧 **邮件管理**: 支持归档、删除、转发、标记等操作
- 🔍 **智能分析**: 邮件优先级分析、内容摘要生成
- 📦 **批量操作**: 支持批量归档、删除、转发多封邮件
- 🎯 **自然语言**: 使用自然语言指令控制邮件操作

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制配置文件模板并填入你的信息：

```bash
cp env.example .env
```

编辑 `.env` 文件，填入以下必需配置：

```env
# 邮件账户配置
EMAIL_ACCOUNT=your_email@example.com
EMAIL_PASSWORD=your_password_or_auth_code

# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 3. 获取 API 密钥

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册账号并获取 API 密钥
3. 将密钥填入 `.env` 文件

### 4. 邮箱配置

#### QQ 邮箱配置
1. 开启 SMTP 服务
2. 生成授权码（不是登录密码）
3. 使用授权码作为 `EMAIL_PASSWORD`

#### Gmail 配置
1. 开启两步验证
2. 生成应用专用密码
3. 使用应用密码作为 `EMAIL_PASSWORD`

### 5. 运行系统

```bash
python agent.py
```

## 使用示例

### 基本操作
- `回复第一封邮件` - 生成自动回复
- `归档邮件2` - 归档指定邮件
- `删除最近5封邮件` - 批量删除
- `转发邮件1到user@example.com` - 转发邮件

### 智能分析
- `总结邮件1` - 生成邮件摘要
- `分析邮件2的优先级` - 优先级分析
- `列出最近10封邮件` - 查看邮件列表

### 批量操作
- `归档前5封邮件` - 批量归档
- `转发前3封邮件到admin@example.com` - 批量转发
- `总结最近5封邮件` - 批量摘要

## 配置说明

### 邮件服务器配置

系统支持多种邮件服务商，默认配置适用于 QQ 邮箱：

- **QQ 邮箱**: `imap.qq.com` / `smtp.qq.com`
- **Gmail**: `imap.gmail.com` / `smtp.gmail.com`
- **Outlook**: `outlook.office365.com` / `smtp.office365.com`

### 环境变量

所有配置项都可以通过环境变量设置，详见 `env.example` 文件。

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

## 开发

### 项目结构
```
mail_agent/
├── agent.py          # 主程序入口
├── config.py         # 配置管理
├── mailer.py         # 邮件操作
├── nlu.py           # 自然语言理解
├── tasks.py         # 任务执行
├── deepseek.py      # AI API 调用
└── env.example      # 配置模板
```

### 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

