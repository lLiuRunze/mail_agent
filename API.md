# Mail Agent API 接口文档

本文档描述了所有可用的API接口，用于与智能邮件代理系统交互。

## 基础URL
```
http://localhost:8000
```

## 认证接口

### 1. 检查认证状态
**GET** `/api/check-auth`

**响应示例：**
```json
{
  "authenticated": true,
  "accounts": ["user@example.com"],
  "active_account": "user@example.com"
}
```

### 2. 登录
**POST** `/api/login`

**请求体：**
```json
{
  "email": "user@163.com",
  "password": "授权码",
  "provider": "163",
  "imap_server": "imap.163.com",
  "imap_port": 993,
  "smtp_server": "smtp.163.com",
  "smtp_port": 465
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "Login successful",
  "email": "user@163.com"
}
```

### 3. 退出登录
**POST** `/api/logout?email=user@example.com`

**响应示例：**
```json
{
  "success": true,
  "message": "Logged out from user@example.com"
}
```

## 邮件查询接口

### 4. 获取邮件列表
**GET** `/api/emails?email=user@example.com&days=30&limit=50`

**参数：**
- `email`: 邮箱账号（可选，默认使用当前账号）
- `days`: 获取最近N天的邮件（默认30）
- `limit`: 最多返回N封邮件（默认50）

**响应示例：**
```json
{
  "success": true,
  "emails": [
    {
      "id": "12345",
      "subject": "会议通知",
      "from": "sender@example.com",
      "from_name": "发件人",
      "to": "user@example.com",
      "date": "Mon, 18 Dec 2023 10:00:00 +0800",
      "body": "邮件正文...",
      "index": 1
    }
  ],
  "account": "user@example.com"
}
```

### 5. 获取单封邮件详情
**GET** `/api/emails/{email_id}?email=user@example.com`

### 6. 搜索邮件
**POST** `/api/emails/search`

**请求体：**
```json
{
  "email": "user@example.com",
  "query": "会议",
  "count": 20
}
```

## 邮件操作接口

### 7. 发送邮件
**POST** `/api/send-email`

**请求体：**
```json
{
  "email": "user@example.com",
  "to": "recipient@example.com",
  "subject": "邮件主题",
  "content": "邮件内容",
  "cc": ["cc1@example.com"],
  "bcc": ["bcc1@example.com"]
}
```

### 8. 回复邮件
**POST** `/api/emails/{email_id}/reply`

**请求体：**
```json
{
  "email": "user@example.com",
  "content": "回复内容",
  "auto_generate": false
}
```

### 9. 转发邮件
**POST** `/api/emails/{email_id}/forward`

**请求体：**
```json
{
  "email": "user@example.com",
  "to": ["recipient1@example.com", "recipient2@example.com"],
  "comment": "转发备注"
}
```

### 10. 归档邮件
**POST** `/api/emails/{email_id}/archive`

**请求体：**
```json
{
  "email": "user@example.com",
  "folder": "工作"
}
```

### 11. 删除邮件
**DELETE** `/api/emails/{email_id}`

**参数：**
- `email`: 邮箱账号

### 12. 标记邮件
**PATCH** `/api/emails/{email_id}/mark`

**请求体：**
```json
{
  "email": "user@example.com",
  "status": "read"
}
```

## 批量操作接口

### 13. 批量归档
**POST** `/api/emails/batch/archive`

**请求体：**
```json
{
  "email": "user@example.com",
  "email_ids": ["id1", "id2", "id3"],
  "folder": "工作"
}
```

### 14. 批量删除
**POST** `/api/emails/batch/delete`

**请求体：**
```json
{
  "email": "user@example.com",
  "email_ids": ["id1", "id2", "id3"]
}
```

### 15. 批量转发
**POST** `/api/emails/batch/forward`

**请求体：**
```json
{
  "email": "user@example.com",
  "email_ids": ["id1", "id2"],
  "to": "recipient@example.com"
}
```

### 16. 批量标记
**POST** `/api/emails/batch/mark`

**请求体：**
```json
{
  "email": "user@example.com",
  "email_ids": ["id1", "id2"],
  "status": "read"
}
```

## AI辅助接口

### 17. 生成邮件摘要
**POST** `/api/emails/{email_id}/summarize`

**请求体：**
```json
{
  "email": "user@example.com"
}
```

**响应示例：**
```json
{
  "success": true,
  "summary": "这是一封关于项目会议的邮件，主要讨论了...",
  "email_id": "12345"
}
```

### 18. 批量摘要
**POST** `/api/emails/batch/summarize`

**请求体：**
```json
{
  "email": "user@example.com",
  "count": 5
}
```

### 19. 分析邮件优先级
**POST** `/api/emails/{email_id}/analyze-priority`

**请求体：**
```json
{
  "email": "user@example.com"
}
```

**响应示例：**
```json
{
  "success": true,
  "priority_analysis": {
    "priority": "高",
    "urgency": "紧急",
    "is_important": true,
    "suggested_action": "立即回复",
    "reason": "包含紧急会议通知"
  }
}
```

### 20. 生成自动回复
**POST** `/api/emails/{email_id}/generate-reply`

**请求体：**
```json
{
  "email": "user@example.com",
  "tone": "正式"
}
```

### 21. 智能对话（自然语言）
**POST** `/api/chat`

**请求体：**
```json
{
  "message": "帮我回复第一封邮件",
  "email": "user@example.com"
}
```

**响应示例：**
```json
{
  "intent": "reply_email",
  "parameters": {
    "email_id": "1"
  },
  "result": {
    "success": true,
    "message": "已成功回复邮件"
  },
  "message": "已成功回复邮件"
}
```

## 支持的自然语言指令

通过 `/api/chat` 接口，支持以下自然语言指令：

### 单邮件操作
- "回复邮件1"
- "回复第一封邮件"
- "归档邮件2到工作文件夹"
- "删除邮件3"
- "转发邮件1到user@example.com"
- "标记邮件5为已读"
- "总结邮件1"
- "分析邮件2的优先级"

### 批量操作
- "归档前5封邮件"
- "删除最近3封邮件"
- "转发前3封邮件到admin@example.com"
- "总结最近5封邮件"
- "标记前10封为已读"

### 查询操作
- "列出最近10封邮件"
- "搜索关于项目的邮件"
- "查找包含会议的邮件"

### 撰写邮件
- "发送邮件到user@example.com，主题是会议通知，内容是..."
