from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import os
import sys

# Ensure the current directory is in the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nlu import NLUEngine
from tasks import TaskExecutor
from mailer import EmailClient

app = FastAPI(title="Mail Agent API")

# Enable CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
nlu_engine = None
task_executors: Dict[str, TaskExecutor] = {}

try:
    nlu_engine = NLUEngine()
    # Don't auto-initialize with default config - let users login manually
    print("NLU Engine initialized successfully")
    print("No accounts logged in. Waiting for user login...")
except Exception as e:
    print(f"Error initializing engines: {e}")

class ChatRequest(BaseModel):
    message: str
    email: Optional[str] = None
    preview_only: Optional[bool] = False  # 如果为True，只生成预览不实际发送

class ChatResponse(BaseModel):
    intent: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    message: str

class LoginRequest(BaseModel):
    email: str
    password: str
    provider: str  # '163', 'qq', 'gmail', 'outlook', 'custom'
    imap_server: Optional[str] = None
    imap_port: Optional[int] = 993
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = 465

class SendEmailRequest(BaseModel):
    email: Optional[str] = None  # Sender email account
    to: str
    subject: str
    content: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class EmailOperationRequest(BaseModel):
    email: Optional[str] = None
    email_id: Optional[str] = None
    email_ids: Optional[List[str]] = None
    content: Optional[str] = None
    sender: Optional[str] = None
    to: Optional[List[str]] = None
    subject: Optional[str] = None
    folder: Optional[str] = None
    status: Optional[str] = None  # 'read' or 'unread'
    count: Optional[int] = None
    auto_generate: Optional[bool] = False
    tone: Optional[str] = "正式"
    comment: Optional[str] = None
    query: Optional[str] = None

PROVIDER_SETTINGS = {
    '163': {
        'imap_server': 'imap.163.com',
        'imap_port': 993,
        'smtp_server': 'smtp.163.com',
        'smtp_port': 465
    },
    'qq': {
        'imap_server': 'imap.qq.com',
        'imap_port': 993,
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465
    },
    'gmail': {
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 465
    },
    'outlook': {
        'imap_server': 'outlook.office365.com',
        'imap_port': 993,
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587
    }
}

@app.get("/health")
async def health_check():
    return {"status": "ok", "engines_loaded": nlu_engine is not None}

@app.get("/api/check-auth")
async def check_auth():
    """Check if the user is logged in (task_executors is not empty)"""
    accounts = list(task_executors.keys())
    if accounts:
        return {
            "authenticated": True, 
            "accounts": accounts,
            "active_account": accounts[0] # Default to first account
        }
    return {"authenticated": False, "accounts": []}

@app.post("/api/logout")
async def logout(email: Optional[str] = None):
    """Logout from one or all accounts"""
    global task_executors
    
    if email:
        # Logout specific account
        if email in task_executors:
            # Disconnect IMAP and SMTP
            executor = task_executors[email]
            if executor.email_client:
                executor.email_client.disconnect_imap()
                executor.email_client.disconnect_smtp()
            del task_executors[email]
            return {"success": True, "message": f"Logged out from {email}"}
        else:
            raise HTTPException(status_code=404, detail=f"Account {email} not found")
    else:
        # Logout all accounts
        for executor in task_executors.values():
            if executor.email_client:
                executor.email_client.disconnect_imap()
                executor.email_client.disconnect_smtp()
        task_executors.clear()
        return {"success": True, "message": "Logged out from all accounts"}

@app.post("/api/login")
async def login(request: LoginRequest):
    global task_executors
    
    # Determine server settings
    if request.provider in PROVIDER_SETTINGS:
        settings = PROVIDER_SETTINGS[request.provider]
        imap_server = settings['imap_server']
        imap_port = settings['imap_port']
        smtp_server = settings['smtp_server']
        smtp_port = settings['smtp_port']
    else:
        # Custom provider
        if not request.imap_server or not request.smtp_server:
            raise HTTPException(status_code=400, detail="IMAP/SMTP server details required for custom provider")
        imap_server = request.imap_server
        imap_port = request.imap_port
        smtp_server = request.smtp_server
        smtp_port = request.smtp_port

    # Create new EmailClient
    try:
        client = EmailClient(
            email_account=request.email,
            email_password=request.password,
            imap_server=imap_server,
            imap_port=imap_port,
            smtp_server=smtp_server,
            smtp_port=smtp_port
        )
        
        # Verify connection
        if client.connect_imap():
            # Initialize TaskExecutor with this client
            task_executors[request.email] = TaskExecutor(email_client=client)
            return {"success": True, "message": "Login successful", "email": request.email}
        else:
            raise HTTPException(status_code=401, detail="Failed to connect to IMAP server. Check credentials.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not nlu_engine:
        raise HTTPException(status_code=503, detail="NLU engine not initialized")
        
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    # Determine which executor to use
    target_email = request.email
    if not target_email:
        # If only one account, use it
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            raise HTTPException(status_code=400, detail="Multiple accounts logged in. Please specify email.")
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")
        
    executor = task_executors[target_email]

    user_input = request.message
    
    # 1. NLU Processing
    try:
        nlu_result = nlu_engine.parse_task(user_input)
        intent = nlu_result.get("intent", "unknown")
        parameters = nlu_result.get("parameters", {})
        # 保存用户原始输入，供 unknown 意图处理使用
        if "user_input" not in parameters:
            parameters["user_input"] = user_input
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLU Error: {str(e)}")

    # 2. Check if preview_only mode (for reply/compose)
    if request.preview_only and intent in ['reply_email', 'compose_email']:
        # Only parse intent, don't execute
        return ChatResponse(
            intent=intent,
            parameters=parameters,
            result={"success": True, "preview_mode": True},
            message="Intent parsed successfully"
        )

    # 3. Task Execution
    try:
        execution_result = executor.execute_task(intent, parameters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution Error: {str(e)}")

    # 4. Construct Response
    response_message = execution_result.get("message", "")
    if execution_result.get("success"):
        if not response_message:
            response_message = f"Successfully executed task: {intent}"
    else:
        if not response_message:
            response_message = f"Failed to execute task: {intent}"

    return ChatResponse(
        intent=intent,
        parameters=parameters,
        result=execution_result,
        message=response_message
    )

@app.get("/api/folders")
async def get_folders(email: Optional[str] = None):
    """List all available email folders for the specified account"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    target_email = email
    if not target_email:
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")
        
    executor = task_executors[target_email]
    
    try:
        folders = executor.email_client.list_folders()
        return {"success": True, "folders": folders, "account": target_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing folders: {str(e)}")

@app.get("/api/emails")
async def get_emails(
    email: Optional[str] = None, 
    days: int = 30, 
    limit: int = 50, 
    folder: str = "INBOX",
    starred: Optional[bool] = None
):
    """Get recent emails for the specified account"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    # Determine which executor to use
    target_email = email
    if not target_email:
        # If only one account, use it
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            # If multiple accounts and none specified, default to the first one or error
            # For simplicity, let's default to the first one if available
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")
        
    executor = task_executors[target_email]
    
    try:
        # Use the email client directly to fetch emails
        # Note: starred filtering is now handled in mailer.py
        emails = executor.email_client.get_recent_emails(count=limit, days=days, folder=folder)
        
        return {"success": True, "emails": emails, "account": target_email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.post("/api/send-email")
async def send_email(request: SendEmailRequest):
    """Send an email using the specified account"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    # Determine which executor to use
    target_email = request.email
    if not target_email:
        # If only one account, use it
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            # If multiple accounts and none specified, default to the first one
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")
        
    executor = task_executors[target_email]
    
    try:
        success = executor.email_client.send_email(
            to_addr=request.to,
            subject=request.subject,
            content=request.content,
            cc=request.cc,
            bcc=request.bcc
        )
        
        if success:
            return {"success": True, "message": "Email sent successfully"}
        else:
            return {"success": False, "message": "Failed to send email"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.post("/api/generate/compose")
async def generate_compose_content(request: EmailOperationRequest):
    """生成新邮件的内容（预览阶段）"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    target_email = request.email
    if not target_email:
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")

    executor = task_executors[target_email]
    
    if not request.to:
        raise HTTPException(status_code=400, detail="Missing required field: to")
    
    try:
        to_addr = request.to[0] if isinstance(request.to, list) else request.to
        content_prompt = request.content or ""
        subject = request.subject
        
        # 如果没有主题，使用 AI 生成
        if not subject and content_prompt:
            subject = executor.deepseek_api.generate_email_subject(content_prompt)
        elif not subject:
            subject = "新邮件"
        
        # 使用 AI 生成完整邮件内容
        if content_prompt:
            email_content = executor.deepseek_api.generate_email_content(content_prompt)
        else:
            email_content = ""
        
        return {
            "success": True,
            "to": to_addr,
            "subject": subject,
            "content": email_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compose")
async def compose_email(request: EmailOperationRequest):
    """发送新邮件（用于预览确认后的发送）"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")

    target_email = request.email
    if not target_email:
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")

    executor = task_executors[target_email]
    
    if not request.to or not request.content:
        raise HTTPException(status_code=400, detail="Missing required fields: to, content")
    
    try:
        # 如果to是列表，取第一个
        to_addr = request.to[0] if isinstance(request.to, list) else request.to
        subject = getattr(request, 'subject', None) or "新邮件"
        
        result = executor.email_client.send_email(
            to_addr=to_addr,
            subject=subject,
            content=request.content
        )
        
        if result:
            return {"success": True, "message": f"Email sent to {to_addr}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 单邮件操作接口 ====================

@app.get("/api/emails/{email_id}")
async def get_email_detail(email_id: str, email: Optional[str] = None):
    """Get detailed information of a specific email"""
    executor = _get_executor(email)
    try:
        email_info = executor.email_client.get_email(email_id)
        if email_info:
            return {"success": True, "email": email_info}
        else:
            raise HTTPException(status_code=404, detail="Email not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")

@app.post("/api/emails/{email_id}/reply")
async def reply_email(email_id: str, request: EmailOperationRequest):
    """Reply to an email"""
    executor = _get_executor(request.email)
    
    try:
        email_info = executor.email_client.get_email(email_id)
        if not email_info:
            raise HTTPException(status_code=404, detail="Email not found")
        
        result = executor.email_client.send_reply(email_info, request.content)
        if result:
            return {"success": True, "message": "Reply sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reply")
async def reply_email_direct(request: EmailOperationRequest):
    """直接回复邮件（用于预览确认后的回复）"""
    executor = _get_executor(request.email)
    
    if not request.email_id or not request.content:
        raise HTTPException(status_code=400, detail="Missing required fields: email_id, content")
    
    try:
        email_info = executor.email_client.get_email(request.email_id)
        if not email_info:
            raise HTTPException(status_code=404, detail="Email not found")
        
        result = executor.email_client.send_reply(email_info, request.content)
        if result:
            return {"success": True, "message": "Reply sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send reply")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    executor = _get_executor(request.email)
    try:
        params = {
            "email_id": email_id,
            "reply_content": request.content,
            "auto_generate": request.auto_generate
        }
        result = executor.execute_task("reply_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error replying email: {str(e)}")

@app.post("/api/emails/{email_id}/forward")
async def forward_email(email_id: str, request: EmailOperationRequest):
    """Forward an email to recipients"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_id": email_id,
            "forward_to": request.to,
            "comment": request.comment
        }
        result = executor.execute_task("forward_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding email: {str(e)}")

@app.post("/api/emails/{email_id}/archive")
async def archive_email(email_id: str, request: EmailOperationRequest):
    """Archive an email to a folder"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_id": email_id,
            "folder_name": request.folder or "Archive"
        }
        result = executor.execute_task("archive_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving email: {str(e)}")

@app.delete("/api/emails/{email_id}")
async def delete_email(email_id: str, email: Optional[str] = None):
    """Delete an email"""
    executor = _get_executor(email)
    try:
        params = {"email_id": email_id}
        result = executor.execute_task("delete_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting email: {str(e)}")

@app.patch("/api/emails/{email_id}/mark")
async def mark_email(email_id: str, request: EmailOperationRequest):
    """Mark an email as read or unread"""
    executor = _get_executor(request.email)
    try:
        intent = "mark_read" if request.status == "read" else "mark_unread"
        params = {"email_id": email_id}
        result = executor.execute_task(intent, params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking email: {str(e)}")

# ==================== AI辅助接口 ====================

@app.post("/api/emails/{email_id}/summarize")
async def summarize_email(email_id: str, request: EmailOperationRequest):
    """Generate summary for an email"""
    executor = _get_executor(request.email)
    try:
        params = {"email_id": email_id}
        result = executor.execute_task("summarize_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing email: {str(e)}")

@app.post("/api/emails/{email_id}/analyze-priority")
async def analyze_priority(email_id: str, request: EmailOperationRequest):
    """Analyze email priority"""
    executor = _get_executor(request.email)
    try:
        params = {"email_id": email_id}
        result = executor.execute_task("analyze_priority", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing priority: {str(e)}")

@app.post("/api/emails/{email_id}/generate-reply")
async def generate_reply(email_id: str, request: EmailOperationRequest):
    """Generate automatic reply content"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_id": email_id,
            "tone": request.tone
        }
        result = executor.execute_task("generate_reply", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating reply: {str(e)}")

# ==================== 批量操作接口 ====================

@app.post("/api/emails/batch/archive")
async def batch_archive(request: EmailOperationRequest):
    """Batch archive emails"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_ids": request.email_ids,
            "folder_name": request.folder or "Archive"
        }
        result = executor.execute_task("archive_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch archiving: {str(e)}")

@app.post("/api/emails/batch/delete")
async def batch_delete(request: EmailOperationRequest):
    """Batch delete emails"""
    executor = _get_executor(request.email)
    try:
        params = {"email_ids": request.email_ids}
        result = executor.execute_task("delete_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch deleting: {str(e)}")

@app.post("/api/emails/batch/forward")
async def batch_forward(request: EmailOperationRequest):
    """Batch forward emails"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_ids": request.email_ids,
            "forward_to": request.to[0] if request.to else None
        }
        result = executor.execute_task("forward_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch forwarding: {str(e)}")

@app.post("/api/emails/batch/mark")
async def batch_mark(request: EmailOperationRequest):
    """Batch mark emails as read or unread"""
    executor = _get_executor(request.email)
    try:
        intent = "mark_read" if request.status == "read" else "mark_unread"
        params = {"email_ids": request.email_ids}
        result = executor.execute_task(intent, params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch marking: {str(e)}")

@app.post("/api/emails/batch/summarize")
async def batch_summarize(request: EmailOperationRequest):
    """Batch summarize emails"""
    executor = _get_executor(request.email)
    try:
        params = {"count": request.count or 5}
        result = executor.execute_task("summarize_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch summarizing: {str(e)}")

@app.post("/api/emails/batch/classify")
async def batch_classify(request: EmailOperationRequest):
    """Batch classify emails - returns classifications for all specified emails"""
    executor = _get_executor(request.email)
    try:
        if not request.email_ids:
            raise HTTPException(status_code=400, detail="email_ids is required for batch classification")
        
        params = {"email_ids": request.email_ids}
        result = executor.execute_task("batch_classify", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error batch classifying: {str(e)}")

@app.post("/api/emails/search")
async def search_emails(request: EmailOperationRequest):
    """Search emails by content and/or sender"""
    executor = _get_executor(request.email)
    try:
        params = {
            "content": request.content,
            "sender": request.sender,
            "count": request.count or 50
        }
        result = executor.execute_task("search_email", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")

@app.post("/api/emails/detail")
async def get_email_detail(request: EmailOperationRequest):
    """Get email detail by ID"""
    executor = _get_executor(request.email)
    try:
        params = {
            "email_id": request.email_id
        }
        result = executor.execute_task("get_email_detail", params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting email detail: {str(e)}")

# ==================== 用户配置管理接口 ====================

# 存储用户配置（内存中，可以改为数据库）
user_profiles: Dict[str, Dict[str, Any]] = {}

class ProfileRequest(BaseModel):
    email: str
    display_name: Optional[str] = ""
    avatar: Optional[str] = ""
    signature: Optional[str] = ""
    reply_tone: Optional[str] = "正式"
    auto_reply_enabled: Optional[bool] = False

@app.get("/api/profile")
async def get_profile(email: str):
    """获取用户配置"""
    if email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {email} not logged in")
    
    # 如果没有配置，返回默认值
    if email not in user_profiles:
        user_profiles[email] = {
            "display_name": "",
            "avatar": "",
            "signature": "",
            "reply_tone": "正式",
            "auto_reply_enabled": False
        }
    
    return {
        "success": True,
        "profile": user_profiles[email]
    }

@app.post("/api/profile")
async def update_profile(request: ProfileRequest):
    """更新用户配置"""
    if request.email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {request.email} not logged in")
    
    # 更新配置
    user_profiles[request.email] = {
        "display_name": request.display_name or "",
        "avatar": request.avatar or "",
        "signature": request.signature or "",
        "reply_tone": request.reply_tone or "正式",
        "auto_reply_enabled": request.auto_reply_enabled or False
    }
    
    return {
        "success": True,
        "message": "配置已更新",
        "profile": user_profiles[request.email]
    }

# ==================== 辅助函数 ====================

def _get_executor(email: Optional[str] = None):
    """Get the task executor for the specified email account"""
    if not task_executors:
        raise HTTPException(status_code=401, detail="Please login first")
    
    target_email = email
    if not target_email:
        if len(task_executors) == 1:
            target_email = list(task_executors.keys())[0]
        else:
            target_email = list(task_executors.keys())[0]
    
    if target_email not in task_executors:
        raise HTTPException(status_code=404, detail=f"Account {target_email} not logged in")
    
    return task_executors[target_email]

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
