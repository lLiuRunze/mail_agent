# Mail Agent - 运行测试说明

## 环境要求

- Python 3.8+
- Node.js 18+
- 邮箱账号（支持IMAP/SMTP）

## 快速启动

### 1. 后端启动

```bash
# 激活虚拟环境（如使用conda）
conda activate F:\MyCode\mail_agent\.conda

# 启动后端服务
python -m uvicorn server:app --reload
```

后端服务运行在：http://localhost:8000

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

前端界面访问：http://localhost:5173

## 功能测试

### 登录测试
1. 打开 http://localhost:5173
2. 输入邮箱账号、IMAP/SMTP配置
3. 点击登录

### 邮件列表测试
- 查看收件箱邮件
- 切换分类：所有邮件、星标、已发送
- 筛选：全部/已读/未读

### AI助手测试
在右侧聊天框输入自然语言指令：

```
查看最近10封邮件
回复第一封邮件
搜索标题包含账单的邮件
总结最近的邮件
```

### 邮件操作测试
1. **回复邮件**：输入"回复第一封邮件"
   - 查看生成的邮件预览
   - 点击"编辑"修改内容
   - 点击"发送"确认发送

2. **新建邮件**：点击"写邮件"按钮
   - 填写收件人、主题、内容
   - 发送邮件

## 常见问题

### IMAP连接错误
- 检查IMAP/SMTP配置是否正确
- 确认邮箱开启了IMAP/SMTP服务
- 某些邮箱需要使用应用专用密码

### 端口占用
- 后端：8000端口被占用，修改启动命令端口
- 前端：5173端口被占用，Vite会自动尝试其他端口

### 邮件标志不显示
- 已读/未读状态依赖IMAP FLAGS
- 确保邮箱服务器支持标准IMAP协议

## API文档

访问 http://localhost:8000/docs 查看完整API文档（FastAPI自动生成）

## 目录结构

```
mail_agent/
├── server.py          # FastAPI服务器
├── nlu.py            # NLU引擎
├── tasks.py          # 任务执行器
├── mailer.py         # 邮件客户端
├── frontend/         # 前端代码
│   └── src/
│       ├── App.tsx              # 主应用
│       ├── components/          # 组件
│       │   ├── AssistantPanel.tsx
│       │   ├── EmailList.tsx
│       │   ├── Sidebar.tsx
│       │   └── ComposeModal.tsx
│       └── login.tsx            # 登录页面
└── TEST.md           # 本文档
```
