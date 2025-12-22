"""
邮件操作模块
负责与邮件服务的交互，包括获取邮件、发送邮件、删除邮件、归档邮件等
使用 IMAP 协议读取邮件，使用 SMTP 协议发送邮件
"""

import email
import imaplib
import re
import smtplib
from email.header import decode_header
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from config import Config

# 添加 IMAP ID 命令支持（163邮箱等需要）
imaplib.Commands["ID"] = ("AUTH",)


class EmailClient:
    """邮件客户端类"""

    def __init__(self, 
                 email_account: Optional[str] = None, 
                 email_password: Optional[str] = None,
                 imap_server: Optional[str] = None,
                 imap_port: Optional[int] = None,
                 smtp_server: Optional[str] = None,
                 smtp_port: Optional[int] = None):
        """初始化邮件客户端"""
        self.email_account = email_account or Config.EMAIL_ACCOUNT
        self.email_password = email_password or Config.EMAIL_PASSWORD
        self.imap_server = imap_server or Config.IMAP_SERVER
        self.imap_port = imap_port or Config.IMAP_PORT
        self.smtp_server = smtp_server or Config.SMTP_SERVER
        self.smtp_port = smtp_port or Config.SMTP_PORT

        self.imap_connection = None
        self.smtp_connection = None

    def connect_imap(self) -> bool:
        """
        连接到 IMAP 服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            if Config.IMAP_USE_SSL:
                self.imap_connection = imaplib.IMAP4_SSL(
                    self.imap_server, self.imap_port
                )
            else:
                self.imap_connection = imaplib.IMAP4(self.imap_server, self.imap_port)

            # 登录
            self.imap_connection.login(self.email_account, self.email_password)
            
            # 发送 IMAP ID 信息（163邮箱等需要）
            try:
                args = (
                    "name", "Haojun Wang",
                    "contact", "17321359161@163.com",
                    "version", "1.0.0",
                    "vendor", "mail-agent"
                )
                typ, dat = self.imap_connection._simple_command(
                    "ID", '("' + '" "'.join(args) + '")'
                )
                print(f"✓ IMAP ID 命令已发送")
            except Exception as e:
                # ID 命令失败不影响后续操作
                print(f"→ IMAP ID 命令发送失败（部分服务器不支持）: {str(e)}")
            
            print(f"✓ 成功连接到 IMAP 服务器: {self.imap_server}")
            return True

        except imaplib.IMAP4.error as e:
            print(f"✗ IMAP 连接失败: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ IMAP 连接异常: {str(e)}")
            return False

    def disconnect_imap(self) -> None:
        """断开 IMAP 连接"""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                print("✓ IMAP 连接已断开")
            except Exception:
                pass
            self.imap_connection = None
    
    def _check_imap_connection(self) -> bool:
        """检查 IMAP 连接是否有效"""
        if not self.imap_connection:
            return False
        
        try:
            # 使用 NOOP 命令检查连接状态
            status, _ = self.imap_connection.noop()
            return status == "OK"
        except Exception as e:
            print(f"→ IMAP 连接已失效: {str(e)}")
            self.imap_connection = None
            return False
    
    def _ensure_imap_connection(self) -> bool:
        """确保 IMAP 连接有效，如果无效则重连"""
        if self._check_imap_connection():
            return True
        
        print("→ IMAP 连接已断开，尝试重新连接...")
        return self.connect_imap()
    
    def list_folders(self) -> List[str]:
        """列出所有可用的邮件文件夹"""
        if not self._ensure_imap_connection():
            return []
        
        try:
            status, folders = self.imap_connection.list()
            if status != "OK":
                return []
            
            folder_list = []
            for folder_data in folders:
                if folder_data:
                    folder_str = folder_data.decode() if isinstance(folder_data, bytes) else str(folder_data)
                    # 提取文件夹名称（格式通常是: (\HasNoChildren) "." "FolderName"）
                    parts = folder_str.split('"')
                    if len(parts) >= 3:
                        folder_name = parts[-2]
                        folder_list.append(folder_name)
            
            return folder_list
        except Exception as e:
            print(f"✗ 列出文件夹失败: {str(e)}")
            return []

    def connect_smtp(self) -> bool:
        """
        连接到 SMTP 服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            if Config.SMTP_USE_SSL:
                self.smtp_connection = smtplib.SMTP_SSL(
                    self.smtp_server, self.smtp_port
                )
            else:
                self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if Config.SMTP_USE_TLS:
                    self.smtp_connection.starttls()

            # 登录
            self.smtp_connection.login(self.email_account, self.email_password)
            print(f"✓ 成功连接到 SMTP 服务器: {self.smtp_server}")
            return True

        except smtplib.SMTPException as e:
            print(f"✗ SMTP 连接失败: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ SMTP 连接异常: {str(e)}")
            return False

    def disconnect_smtp(self) -> None:
        """断开 SMTP 连接"""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                print("✓ SMTP 连接已断开")
            except Exception:
                pass
            self.smtp_connection = None

    def _decode_header_value(self, value: str) -> str:
        """
        解码邮件头部信息

        Args:
            value: 编码的头部值

        Returns:
            str: 解码后的字符串
        """
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    if encoding:
                        result.append(part.decode(encoding, errors="ignore"))
                    else:
                        result.append(part.decode("utf-8", errors="ignore"))
                except (UnicodeDecodeError, LookupError):
                    try:
                        result.append(part.decode("utf-8", errors="ignore"))
                    except Exception:
                        result.append(part.decode("latin-1", errors="ignore"))
            else:
                try:
                    result.append(str(part))
                except Exception:
                    result.append("")

        return "".join(result)

    def _find_folder(self, folder_type: str) -> Optional[str]:
        """根据文件夹类型查找实际的文件夹名称"""
        if folder_type.upper() == "INBOX":
            return "INBOX"
        
        # 对于 starred 类型，返回 None 表示使用 INBOX + FLAGGED 筛选
        if folder_type.lower() == "starred":
            print(f"→ starred 类型将使用 INBOX + FLAGGED 筛选")
            return None
        
        # 获取所有文件夹
        available_folders = self.list_folders()
        if not available_folders:
            return None
        
        # 从配置中获取可能的文件夹名称
        folder_type_lower = folder_type.lower()
        possible_names = Config.FOLDER_NAMES.get(folder_type_lower, [folder_type])
        
        # 第一轮：精确匹配（优先UTF-7编码和英文名）
        for possible_name in possible_names:
            if possible_name in available_folders:
                print(f"→ 精确匹配文件夹: {folder_type} -> {possible_name}")
                return possible_name
        
        # 第二轮：模糊匹配（不区分大小写）
        for possible_name in possible_names:
            for actual_folder in available_folders:
                if possible_name.lower() == actual_folder.lower():
                    print(f"→ 大小写匹配文件夹: {folder_type} -> {actual_folder}")
                    return actual_folder
        
        # 第三轮：包含匹配
        for possible_name in possible_names:
            for actual_folder in available_folders:
                if possible_name.lower() in actual_folder.lower() or actual_folder.lower() in possible_name.lower():
                    print(f"→ 模糊匹配文件夹: {folder_type} -> {actual_folder}")
                    return actual_folder
        
        # 如果没找到，尝试直接使用原始名称
        if folder_type in available_folders:
            return folder_type
        
        print(f"✗ 未找到文件夹类型: {folder_type}，可用文件夹: {available_folders}")
        return None
    
    def _select_folder(self, folder: str, retry_count: int = 2) -> bool:
        """
        选择邮件文件夹，支持163邮箱等特殊情况

        Args:
            folder: 文件夹名称
            retry_count: 重试次数

        Returns:
            bool: 是否成功选择
        """
        # 确保连接有效
        if not self._ensure_imap_connection():
            return False

        # QQ邮箱等邮件服务器要求包含空格的文件夹名必须用双引号包裹
        # 例如：Sent Messages -> "Sent Messages"
        if ' ' in folder and not (folder.startswith('"') and folder.endswith('"')):
            folder_with_quotes = f'"{folder}"'
            print(f"→ 文件夹名包含空格，添加引号: {folder} -> {folder_with_quotes}")
            folder = folder_with_quotes

        # 尝试直接选择
        for attempt in range(retry_count + 1):
            # 方法 1: 直接 SELECT
            try:
                status, response = self.imap_connection.select(folder)
                if status == "OK":
                    print(f"✓ 成功选择文件夹: {folder}")
                    return True
                else:
                    print(f"✗ SELECT 失败: {folder}, status: {status}, response: {response}")
            except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError, ConnectionError, BrokenPipeError) as e:
                error_str = str(e)
                print(f"✗ SELECT 异常 (尝试 {attempt + 1}/{retry_count + 1}): {folder}, error: {error_str}")
                
                # 检查是否是连接错误 (WinError 10054 等)
                is_connection_error = any(keyword in error_str.lower() for keyword in [
                    "10054", "连接", "connection", "abort", "socket", "broken", "reset", "eof"
                ])
                
                if is_connection_error and attempt < retry_count:
                    print(f"→ 检测到连接错误，尝试重新连接 ({attempt + 1}/{retry_count})...")
                    self.disconnect_imap()
                    import time
                    time.sleep(1)  # 等待1秒再重连
                    if not self._ensure_imap_connection():
                        print(f"✗ 重新连接失败")
                        continue
                    print(f"→ 重新连接成功，继续尝试...")
                    continue
                # 不是连接错误，继续尝试只读模式
            except Exception as e:
                error_str = str(e)
                print(f"✗ SELECT 未知异常: {folder}, error: {error_str}")
            
            # 方法 2: 尝试只读模式（readonly=True 对应 EXAMINE 命令）
            print(f"→ 尝试只读模式访问: {folder}")
            try:
                status, response = self.imap_connection.select(folder, readonly=True)
                if status == "OK":
                    print(f"✓ 成功以只读模式选择文件夹: {folder}")
                    return True
                else:
                    print(f"✗ 只读模式失败: status={status}, response={response}")
            except Exception as e:
                print(f"✗ 只读模式异常: {str(e)}")
            
            # 如果是最后一次尝试，还可以尝试重连
            if attempt < retry_count:
                print(f"→ 尝试重连后再试 ({attempt + 1}/{retry_count})...")
                self.disconnect_imap()
                import time
                time.sleep(1)
                if not self._ensure_imap_connection():
                    print(f"✗ 重新连接失败")
                    return False
                print(f"→ 重新连接成功，继续尝试...")
            else:
                # 最后一次尝试失败
                print(f"✗ 无法选择文件夹: {folder}")
                return False
        
        return False

    def _get_email_body(self, msg: Message) -> str:
        """
        提取邮件正文

        Args:
            msg: 邮件消息对象

        Returns:
            str: 邮件正文内容
        """
        body = ""

        if msg.is_multipart():
            # 多部分邮件
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # 跳过附件
                if "attachment" in content_disposition:
                    continue

                # 获取文本内容
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset, errors="ignore")  # type: ignore
                            break
                    except (UnicodeDecodeError, AttributeError):
                        try:
                            if payload:  # type: ignore
                                body = payload.decode("utf-8", errors="ignore")  # type: ignore
                                break
                        except Exception:
                            continue
                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            html_body = payload.decode(charset, errors="ignore")  # type: ignore
                            # 简单去除HTML标签
                            body = re.sub(r"<[^>]+>", "", html_body)
                    except (UnicodeDecodeError, AttributeError):
                        try:
                            if payload:  # type: ignore
                                html_body = payload.decode("utf-8", errors="ignore")  # type: ignore
                                body = re.sub(r"<[^>]+>", "", html_body)
                        except Exception:
                            continue
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")  # type: ignore
                else:
                    body = str(msg.get_payload())
            except (UnicodeDecodeError, AttributeError):
                try:
                    if payload:  # type: ignore
                        body = payload.decode("utf-8", errors="ignore")  # type: ignore
                    else:
                        body = str(msg.get_payload())
                except Exception:
                    body = str(msg.get_payload())

        return body.strip()

    def get_email(self, email_id: str, lightweight: bool = False) -> Optional[Dict[str, Any]]:
        """
        根据邮件 ID 获取邮件信息

        Args:
            email_id: 邮件 ID（IMAP UID）
            lightweight: 是否只获取轻量级信息（不获取正文，速度更快）

        Returns:
            Optional[Dict[str, Any]]: 邮件信息字典，失败返回 None
        """
        if not self._ensure_imap_connection():
            return None

        try:
            # 选择收件箱
            if not self._select_folder(Config.DEFAULT_FOLDER):
                return None

            # 如果是轻量级模式，只获取ENVELOPE和FLAGS
            if lightweight:
                status, data = self.imap_connection.fetch(
                    email_id, "(ENVELOPE FLAGS BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE)])"
                ) # type: ignore
            else:
                # 获取邮件和FLAGS
                status, data = self.imap_connection.fetch(email_id, "(RFC822 FLAGS)") # type: ignore

            if status != "OK":
                print(f"✗ 获取邮件失败: {email_id}")
                return None

            # 解析邮件
            raw_email = data[0][1] # type: ignore
            msg = email.message_from_bytes(raw_email) # type: ignore
            
            # 解析FLAGS
            flags_data = data[0][0] if len(data[0]) > 0 else b''
            flags_str = flags_data.decode() if isinstance(flags_data, bytes) else str(flags_data)
            seen = '\\Seen' in flags_str
            flagged = '\\Flagged' in flags_str

            # 提取邮件信息
            subject = self._decode_header_value(msg.get("Subject", ""))
            from_header = msg.get("From", "")
            from_name, from_addr = parseaddr(from_header)
            from_name = self._decode_header_value(from_name)

            to_header = msg.get("To", "")
            date = msg.get("Date", "")

            # 获取邮件正文（轻量级模式下跳过以提升速度）
            if lightweight:
                body = ""  # 轻量级模式不获取正文
            else:
                body = self._get_email_body(msg)

            email_info = {
                "id": email_id,
                "subject": subject,
                "from": from_addr,
                "from_name": from_name,
                "to": to_header,
                "date": date,
                "body": body,
                "raw_message": msg if not lightweight else None,
                "seen": seen,
                "flagged": flagged,
            }

            return email_info

        except Exception as e:
            print(f"✗ 获取邮件异常: {str(e)}")
            return None

    def get_recent_emails(
        self, count: int = 10, days: int = 30, folder: str = None # type: ignore
    ) -> List[Dict[str, Any]]:
        """
        获取最近的邮件列表

        Args:
            count: 获取的邮件数量
            days: 获取最近多少天的邮件
            folder: 邮件文件夹，默认为收件箱。可以是"sent"、"drafts"等类型名，会自动匹配实际文件夹

        Returns:
            List[Dict[str, Any]]: 邮件信息列表
        """
        if not self._ensure_imap_connection():
            return []

        try:
            folder = folder or Config.DEFAULT_FOLDER
            original_folder = folder
            use_starred_filter = False
            
            # 如果不是INBOX，尝试智能匹配文件夹
            if folder.upper() != "INBOX":
                actual_folder = self._find_folder(folder)
                if actual_folder:
                    folder = actual_folder
                elif original_folder.lower() == "starred":
                    # starred 类型找不到独立文件夹，使用 INBOX + FLAGGED 筛选
                    print(f"→ starred 类型没有独立文件夹，将从 INBOX 筛选 FLAGGED 邮件")
                    folder = "INBOX"
                    use_starred_filter = True
                else:
                    print(f"✗ 找不到文件夹 {folder}，返回空列表")
                    return []
            
            # 使用新的 _select_folder 方法
            if not self._select_folder(folder):
                print(f"✗ 无法选择文件夹 {folder}，返回空列表")
                return []

            # 搜索最近30天的邮件，如果找不到则搜索所有邮件
            from datetime import datetime, timedelta

            thirty_days_ago = (datetime.now() - timedelta(days=days)).strftime(
                "%d-%b-%Y"
            )

            # 先尝试搜索最近30天的邮件
            status, messages = self.imap_connection.search( # type: ignore
                None, f"SINCE {thirty_days_ago}"
            )

            if status != "OK" or not messages[0]:
                # 如果搜索失败或没有结果，则搜索所有邮件
                status, messages = self.imap_connection.search(None, "ALL") # type: ignore

                if status != "OK":
                    return []

            # 获取邮件ID列表
            email_ids = messages[0].split()

            if not email_ids:
                return []

            # 获取最近的N封邮件（从最新的开始）
            if len(email_ids) > count:
                recent_ids = email_ids[-count:]  # 获取最后N封邮件（最新的）
            else:
                recent_ids = email_ids

            recent_ids = list(reversed(recent_ids))  # 最新的在前

            emails = []
            for index, email_id in enumerate(recent_ids, 1):
                # 使用轻量级模式快速获取邮件列表（不获取正文）
                email_info = self.get_email(email_id.decode(), lightweight=True)
                if email_info:
                    # 如果需要筛选星标邮件，跳过未标记的
                    if use_starred_filter and not email_info.get('flagged', False):
                        continue
                    # 添加时间排序的索引（从1开始）
                    email_info["index"] = index
                    # 保存原始IMAP UID用于后续操作
                    email_info["original_uid"] = email_id.decode()
                    emails.append(email_info)

            return emails

        except Exception as e:
            print(f"✗ 获取邮件列表异常: {str(e)}")
            return []

    def get_email_by_index(
        self, index: int, count: int = 50, folder: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        根据时间排序的索引获取邮件

        Args:
            index: 时间排序的索引（从1开始）
            count: 获取的邮件数量（用于确保索引在范围内）
            folder: 邮件文件夹，默认为收件箱

        Returns:
            Optional[Dict[str, Any]]: 邮件信息，失败返回 None
        """
        # 获取足够多的邮件以确保索引在范围内
        emails = self.get_recent_emails(count=max(count, index), folder=folder)

        if not emails or index < 1 or index > len(emails):
            return None

        # 返回指定索引的邮件（索引从1开始，数组从0开始）
        return emails[index - 1]

    def send_reply(self, original_email: Dict[str, Any], reply_content: str) -> bool:
        """
        发送邮件回复

        Args:
            original_email: 原始邮件信息字典
            reply_content: 回复内容

        Returns:
            bool: 发送是否成功
        """
        if not self.smtp_connection:
            if not self.connect_smtp():
                return False

        try:
            # 创建回复邮件
            msg = MIMEMultipart()
            msg["From"] = self.email_account
            msg["To"] = original_email["from"]
            msg["Subject"] = f"Re: {original_email['subject']}"

            # 添加回复内容
            msg.attach(MIMEText(reply_content, "plain", "utf-8"))

            # 发送邮件
            recipients = [original_email["from"]]
            self.smtp_connection.sendmail(
                self.email_account, recipients, msg.as_string()
            )
            print(f"✓ 回复邮件已发送到: {original_email['from']}")
            return True

        except Exception as e:
            print(f"✗ 发送回复失败: {str(e)}")
            return False

    def send_email(
        self,
        to_addr: str,
        subject: str,
        content: str,
        cc: List[str] = None,
        bcc: List[str] = None,
    ) -> bool:
        """
        发送新邮件

        Args:
            to_addr: 收件人地址
            subject: 邮件主题
            content: 邮件内容
            cc: 抄送列表
            bcc: 密送列表

        Returns:
            bool: 发送是否成功
        """
        if not self.smtp_connection:
            if not self.connect_smtp():
                return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_account
            msg["To"] = to_addr
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)

            msg.attach(MIMEText(content, "plain", "utf-8"))

            # 发送邮件
            recipients = [to_addr]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            self.smtp_connection.sendmail(
                self.email_account, recipients, msg.as_string()
            )
            print(f"✓ 邮件已发送到: {to_addr}")
            return True

        except Exception as e:
            print(f"✗ 发送邮件失败: {str(e)}")
            return False

    def archive_email_to_folder(self, email_id: str, folder_name: str) -> bool:
        """
        将邮件归档到指定文件夹

        Args:
            email_id: 邮件 ID
            folder_name: 目标文件夹名称

        Returns:
            bool: 归档是否成功
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return False

        try:
            # 选择当前文件夹
            self.imap_connection.select(Config.DEFAULT_FOLDER)

            # 复制邮件到目标文件夹
            result = self.imap_connection.copy(email_id, folder_name)

            if result[0] == "OK":
                # 标记原邮件为已删除
                self.imap_connection.store(email_id, "+FLAGS", "\\Deleted")
                # 永久删除标记为删除的邮件
                self.imap_connection.expunge()
                print(f"✓ 邮件已归档到: {folder_name}")
                return True
            else:
                print("✗ 归档邮件失败")
                return False

        except Exception as e:
            print(f"✗ 归档邮件异常: {str(e)}")
            return False

    def delete_email(self, email_id: str) -> bool:
        """
        删除指定邮件

        Args:
            email_id: 邮件 ID

        Returns:
            bool: 删除是否成功
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return False

        try:
            # 选择收件箱
            self.imap_connection.select(Config.DEFAULT_FOLDER)

            # 标记邮件为已删除
            self.imap_connection.store(email_id, "+FLAGS", "\\Deleted")

            # 永久删除
            self.imap_connection.expunge()

            print(f"✓ 邮件已删除: {email_id}")
            return True

        except Exception as e:
            print(f"✗ 删除邮件失败: {str(e)}")
            return False

    def forward_email(self, original_email: Dict[str, Any], forward_to: str) -> bool:
        """
        转发邮件

        Args:
            original_email: 原始邮件信息
            forward_to: 转发目标邮箱

        Returns:
            bool: 转发是否成功
        """
        if not self.smtp_connection:
            if not self.connect_smtp():
                return False

        try:
            # 创建转发邮件
            msg = MIMEMultipart()
            msg["From"] = self.email_account
            msg["To"] = forward_to
            msg["Subject"] = f"Fwd: {original_email['subject']}"

            # 添加转发说明和原邮件内容
            forward_content = f"""
---------- Forwarded message ---------
From: {original_email["from_name"]} <{original_email["from"]}>
Date: {original_email["date"]}
Subject: {original_email["subject"]}

{original_email["body"]}
"""

            msg.attach(MIMEText(forward_content, "plain", "utf-8"))

            # 发送邮件
            recipients = [forward_to]
            result = self.smtp_connection.sendmail(
                self.email_account, recipients, msg.as_string()
            )

            # 检查发送结果
            if result:
                # 如果有失败的结果，打印详细信息
                for recipient, error in result.items():
                    print(f"✗ 转发邮件失败: {error}")
                return False
            else:
                print(f"✓ 邮件已转发到: {forward_to}")
                return True

        except Exception as e:
            print(f"✗ 转发邮件失败: {str(e)}")
            return False

    def mark_email_as_read(self, email_id: str) -> bool:
        """
        标记邮件为已读

        Args:
            email_id: 邮件 ID

        Returns:
            bool: 标记是否成功
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return False

        try:
            self.imap_connection.select(Config.DEFAULT_FOLDER)
            self.imap_connection.store(email_id, "+FLAGS", "\\Seen")
            print(f"✓ 邮件已标记为已读: {email_id}")
            return True

        except Exception as e:
            print(f"✗ 标记邮件失败: {str(e)}")
            return False

    def mark_email_as_unread(self, email_id: str) -> bool:
        """
        标记邮件为未读

        Args:
            email_id: 邮件 ID

        Returns:
            bool: 标记是否成功
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return False

        try:
            self.imap_connection.select(Config.DEFAULT_FOLDER)
            self.imap_connection.store(email_id, "-FLAGS", "\\Seen")
            print(f"✓ 邮件已标记为未读: {email_id}")
            return True

        except Exception as e:
            print(f"✗ 标记邮件失败: {str(e)}")
            return False

    def move_email_to_folder(self, email_id: str, folder_name: str) -> bool:
        """
        移动邮件到指定文件夹

        Args:
            email_id: 邮件 ID
            folder_name: 目标文件夹名称

        Returns:
            bool: 移动是否成功
        """
        return self.archive_email_to_folder(email_id, folder_name)

    def __enter__(self):
        """上下文管理器入口"""
        self.connect_imap()
        self.connect_smtp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect_imap()
        self.disconnect_smtp()

    def get_emails_by_ids(
        self, email_ids: List[str], folder: str = None
    ) -> List[Dict[str, Any]]:
        """
        批量获取多封邮件

        Args:
            email_ids: 邮件ID列表
            folder: 邮件文件夹，默认为收件箱

        Returns:
            List[Dict[str, Any]]: 邮件信息列表
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return []

        try:
            folder = folder or Config.DEFAULT_FOLDER
            self.imap_connection.select(folder)

            emails = []
            for email_id in email_ids:
                email_info = self.get_email(email_id)
                if email_info:
                    email_info["original_uid"] = email_id
                    emails.append(email_info)

            return emails

        except Exception as e:
            print(f"✗ 批量获取邮件异常: {str(e)}")
            return []

    def get_emails_by_indices(
        self, indices: List[int], count: int = 50, folder: str = None
    ) -> List[Dict[str, Any]]:
        """
        根据时间排序的索引列表批量获取邮件

        Args:
            indices: 时间排序的索引列表（从1开始）
            count: 获取的邮件总数（用于确保索引在范围内）
            folder: 邮件文件夹，默认为收件箱

        Returns:
            List[Dict[str, Any]]: 邮件信息列表
        """
        # 获取足够多的邮件以确保所有索引都在范围内
        max_index = max(indices) if indices else 0
        emails = self.get_recent_emails(count=max(count, max_index), folder=folder)

        if not emails:
            return []

        # 根据索引提取邮件
        result = []
        for index in indices:
            if 1 <= index <= len(emails):
                result.append(emails[index - 1])

        return result

    def batch_forward_email(
        self, original_email: Dict[str, Any], recipients: List[str]
    ) -> Dict[str, Any]:
        """
        批量转发邮件到多个收件人

        Args:
            original_email: 原始邮件信息
            recipients: 收件人列表

        Returns:
            Dict[str, Any]: 包含成功和失败信息的字典
        """
        success_count = 0
        failed_count = 0
        results = []

        for recipient in recipients:
            try:
                # 为每个收件人重新建立SMTP连接（避免连接超时）
                if self.smtp_connection:
                    self.disconnect_smtp()

                success = self.forward_email(original_email, recipient)
                if success:
                    success_count += 1
                    results.append({"recipient": recipient, "status": "success"})
                else:
                    failed_count += 1
                    results.append({"recipient": recipient, "status": "failed"})
            except Exception as e:
                failed_count += 1
                results.append({"recipient": recipient, "status": f"error: {str(e)}"})

        return {
            "total": len(recipients),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }

    def batch_archive_emails(
        self, email_ids: List[str], folder_name: str
    ) -> Dict[str, Any]:
        """
        批量归档多封邮件

        Args:
            email_ids: 邮件ID列表
            folder_name: 目标文件夹名称

        Returns:
            Dict[str, Any]: 包含成功和失败信息的字典
        """
        success_count = 0
        failed_count = 0
        results = []

        for email_id in email_ids:
            try:
                success = self.archive_email_to_folder(email_id, folder_name)
                if success:
                    success_count += 1
                    results.append({"email_id": email_id, "status": "archived"})
                else:
                    failed_count += 1
                    results.append({"email_id": email_id, "status": "failed"})
            except Exception as e:
                failed_count += 1
                results.append({"email_id": email_id, "status": f"error: {str(e)}"})

        return {
            "total": len(email_ids),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }

    def batch_delete_emails(self, email_ids: List[str]) -> Dict[str, Any]:
        """
        批量删除多封邮件

        Args:
            email_ids: 邮件ID列表

        Returns:
            Dict[str, Any]: 包含成功和失败信息的字典
        """
        success_count = 0
        failed_count = 0
        results = []

        for email_id in email_ids:
            try:
                success = self.delete_email(email_id)
                if success:
                    success_count += 1
                    results.append({"email_id": email_id, "status": "deleted"})
                else:
                    failed_count += 1
                    results.append({"email_id": email_id, "status": "failed"})
            except Exception as e:
                failed_count += 1
                results.append({"email_id": email_id, "status": f"error: {str(e)}"})

        return {
            "total": len(email_ids),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }

    def batch_mark_as_read(self, email_ids: List[str]) -> Dict[str, Any]:
        """
        批量标记邮件为已读

        Args:
            email_ids: 邮件ID列表

        Returns:
            Dict[str, Any]: 包含成功和失败信息的字典
        """
        success_count = 0
        failed_count = 0
        results = []

        for email_id in email_ids:
            try:
                success = self.mark_email_as_read(email_id)
                if success:
                    success_count += 1
                    results.append({"email_id": email_id, "status": "marked_read"})
                else:
                    failed_count += 1
                    results.append({"email_id": email_id, "status": "failed"})
            except Exception as e:
                failed_count += 1
                results.append({"email_id": email_id, "status": f"error: {str(e)}"})

        return {
            "total": len(email_ids),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }

    def batch_mark_as_unread(self, email_ids: List[str]) -> Dict[str, Any]:
        """
        批量标记邮件为未读

        Args:
            email_ids: 邮件ID列表

        Returns:
            Dict[str, Any]: 包含成功和失败信息的字典
        """
        success_count = 0
        failed_count = 0
        results = []

        for email_id in email_ids:
            try:
                success = self.mark_email_as_unread(email_id)
                if success:
                    success_count += 1
                    results.append({"email_id": email_id, "status": "marked_unread"})
                else:
                    failed_count += 1
                    results.append({"email_id": email_id, "status": "failed"})
            except Exception as e:
                failed_count += 1
                results.append({"email_id": email_id, "status": f"error: {str(e)}"})

        return {
            "total": len(email_ids),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        }


# 创建全局邮件客户端实例
email_client = EmailClient()


# ==================== 便捷函数 ====================


def get_email(email_id: str) -> Optional[Dict[str, Any]]:
    """获取邮件（便捷函数）"""
    return email_client.get_email(email_id)


def send_reply(email: Dict[str, Any], reply_content: str) -> bool:
    """发送回复（便捷函数）"""
    return email_client.send_reply(email, reply_content)


def archive_email_to_folder(email_id: str, folder_name: str) -> bool:
    """归档邮件（便捷函数）"""
    return email_client.archive_email_to_folder(email_id, folder_name)


def delete_email(email_id: str) -> bool:
    """删除邮件（便捷函数）"""
    return email_client.delete_email(email_id)


def forward_email(email: Dict[str, Any], forward_to: str) -> bool:
    """转发邮件（便捷函数）"""
    return email_client.forward_email(email, forward_to)


def get_emails_by_ids(email_ids: List[str]) -> List[Dict[str, Any]]:
    """批量获取邮件（便捷函数）"""
    return email_client.get_emails_by_ids(email_ids)


def get_emails_by_indices(indices: List[int]) -> List[Dict[str, Any]]:
    """根据索引批量获取邮件（便捷函数）"""
    return email_client.get_emails_by_indices(indices)


def batch_forward_email(email: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
    """批量转发邮件（便捷函数）"""
    return email_client.batch_forward_email(email, recipients)


def batch_archive_emails(email_ids: List[str], folder_name: str) -> Dict[str, Any]:
    """批量归档邮件（便捷函数）"""
    return email_client.batch_archive_emails(email_ids, folder_name)


def batch_delete_emails(email_ids: List[str]) -> Dict[str, Any]:
    """批量删除邮件（便捷函数）"""
    return email_client.batch_delete_emails(email_ids)


def batch_mark_as_read(email_ids: List[str]) -> Dict[str, Any]:
    """批量标记已读（便捷函数）"""
    return email_client.batch_mark_as_read(email_ids)


def batch_mark_as_unread(email_ids: List[str]) -> Dict[str, Any]:
    """批量标记未读（便捷函数）"""
    return email_client.batch_mark_as_unread(email_ids)


if __name__ == "__main__":
    # 测试代码
    print("测试邮件操作模块...")

    # 使用上下文管理器
    with EmailClient() as client:
        # 获取最近的5封邮件
        print("\n获取最近的邮件...")
        emails = client.get_recent_emails(count=5)

        for i, email in enumerate(emails, 1):
            print(f"\n邮件 {i}:")
            print(f"  主题: {email['subject']}")
            print(f"  发件人: {email['from_name']} <{email['from']}>")
            print(f"  日期: {email['date']}")
            print(f"  正文预览: {email['body'][:100]}...")