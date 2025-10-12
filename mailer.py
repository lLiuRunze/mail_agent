"""
邮件操作模块
负责与邮件服务的交互，包括获取邮件、发送邮件、删除邮件、归档邮件等
使用 IMAP 协议读取邮件，使用 SMTP 协议发送邮件
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import parseaddr
from typing import Dict, Any, List, Optional, Tuple
import re
from config import Config


class EmailClient:
    """邮件客户端类"""
    
    def __init__(self):
        """初始化邮件客户端"""
        self.email_account = Config.EMAIL_ACCOUNT
        self.email_password = Config.EMAIL_PASSWORD
        self.imap_server = Config.IMAP_SERVER
        self.imap_port = Config.IMAP_PORT
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        
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
                    self.imap_server, 
                    self.imap_port
                )
            else:
                self.imap_connection = imaplib.IMAP4(
                    self.imap_server, 
                    self.imap_port
                )
            
            # 登录
            self.imap_connection.login(self.email_account, self.email_password)
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
            except:
                pass
            self.imap_connection = None
    
    def connect_smtp(self) -> bool:
        """
        连接到 SMTP 服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if Config.SMTP_USE_SSL:
                self.smtp_connection = smtplib.SMTP_SSL(
                    self.smtp_server,
                    self.smtp_port
                )
            else:
                self.smtp_connection = smtplib.SMTP(
                    self.smtp_server,
                    self.smtp_port
                )
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
            except:
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
                        result.append(part.decode(encoding, errors='ignore'))
                    else:
                        result.append(part.decode('utf-8', errors='ignore'))
                except (UnicodeDecodeError, LookupError):
                    try:
                        result.append(part.decode('utf-8', errors='ignore'))
                    except:
                        result.append(part.decode('latin-1', errors='ignore'))
            else:
                try:
                    result.append(str(part))
                except:
                    result.append('')
        
        return ''.join(result)
    
    def _get_email_body(self, msg: email.message.Message) -> str:
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
                            charset = part.get_content_charset() or 'utf-8'
                            body = payload.decode(charset, errors='ignore')
                            break
                    except (UnicodeDecodeError, AttributeError):
                        try:
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                                break
                        except:
                            continue
                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            html_body = payload.decode(charset, errors='ignore')
                            # 简单去除HTML标签
                            body = re.sub(r'<[^>]+>', '', html_body)
                    except (UnicodeDecodeError, AttributeError):
                        try:
                            if payload:
                                html_body = payload.decode('utf-8', errors='ignore')
                                body = re.sub(r'<[^>]+>', '', html_body)
                        except:
                            continue
        else:
            # 单部分邮件
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
                else:
                    body = str(msg.get_payload())
            except (UnicodeDecodeError, AttributeError):
                try:
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                    else:
                        body = str(msg.get_payload())
                except:
                    body = str(msg.get_payload())
        
        return body.strip()
    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        根据邮件 ID 获取邮件信息
        
        Args:
            email_id: 邮件 ID（IMAP UID）
            
        Returns:
            Optional[Dict[str, Any]]: 邮件信息字典，失败返回 None
        """
        if not self.imap_connection:
            if not self.connect_imap():
                return None
        
        try:
            # 选择收件箱
            self.imap_connection.select(Config.DEFAULT_FOLDER)
            
            # 获取邮件
            status, data = self.imap_connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                print(f"✗ 获取邮件失败: {email_id}")
                return None
            
            # 解析邮件
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 提取邮件信息
            subject = self._decode_header_value(msg.get('Subject', ''))
            from_header = msg.get('From', '')
            from_name, from_addr = parseaddr(from_header)
            from_name = self._decode_header_value(from_name)
            
            to_header = msg.get('To', '')
            date = msg.get('Date', '')
            
            # 获取邮件正文
            body = self._get_email_body(msg)
            
            email_info = {
                'id': email_id,
                'subject': subject,
                'from': from_addr,
                'from_name': from_name,
                'to': to_header,
                'date': date,
                'body': body,
                'raw_message': msg
            }
            
            return email_info
            
        except Exception as e:
            print(f"✗ 获取邮件异常: {str(e)}")
            return None
    
    def get_recent_emails(self, count: int = 10, days: int = 30, folder: str = None) -> List[Dict[str, Any]]:
        """
        获取最近的邮件列表
        
        Args:
            count: 获取的邮件数量
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
            
            # 搜索最近30天的邮件，如果找不到则搜索所有邮件
            from datetime import datetime, timedelta
            thirty_days_ago = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
            
            # 先尝试搜索最近30天的邮件
            status, messages = self.imap_connection.search(None, f'SINCE {thirty_days_ago}')
            
            if status != 'OK' or not messages[0]:
                # 如果搜索失败或没有结果，则搜索所有邮件
                status, messages = self.imap_connection.search(None, 'ALL')
                
                if status != 'OK':
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
                email_info = self.get_email(email_id.decode())
                if email_info:
                    # 添加时间排序的索引（从1开始）
                    email_info['index'] = index
                    # 保存原始IMAP UID用于后续操作
                    email_info['original_uid'] = email_id.decode()
                    emails.append(email_info)
            
            return emails
            
        except Exception as e:
            print(f"✗ 获取邮件列表异常: {str(e)}")
            return []
    
    def get_email_by_index(self, index: int, count: int = 50, folder: str = None) -> Optional[Dict[str, Any]]:
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
            msg['From'] = self.email_account
            msg['To'] = original_email['from']
            msg['Subject'] = f"Re: {original_email['subject']}"
            
            # 添加回复内容
            msg.attach(MIMEText(reply_content, 'plain', 'utf-8'))
            
            # 发送邮件
            recipients = [original_email['from']]
            self.smtp_connection.sendmail(self.email_account, recipients, msg.as_string())
            print(f"✓ 回复邮件已发送到: {original_email['from']}")
            return True
            
        except Exception as e:
            print(f"✗ 发送回复失败: {str(e)}")
            return False
    
    def send_email(self, to_addr: str, subject: str, content: str, 
                   cc: List[str] = None, bcc: List[str] = None) -> bool:
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
            msg['From'] = self.email_account
            msg['To'] = to_addr
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 发送邮件
            recipients = [to_addr]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            self.smtp_connection.sendmail(self.email_account, recipients, msg.as_string())
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
            
            if result[0] == 'OK':
                # 标记原邮件为已删除
                self.imap_connection.store(email_id, '+FLAGS', '\\Deleted')
                # 永久删除标记为删除的邮件
                self.imap_connection.expunge()
                print(f"✓ 邮件已归档到: {folder_name}")
                return True
            else:
                print(f"✗ 归档邮件失败")
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
            self.imap_connection.store(email_id, '+FLAGS', '\\Deleted')
            
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
            msg['From'] = self.email_account
            msg['To'] = forward_to
            msg['Subject'] = f"Fwd: {original_email['subject']}"
            
            # 添加转发说明和原邮件内容
            forward_content = f"""
---------- Forwarded message ---------
From: {original_email['from_name']} <{original_email['from']}>
Date: {original_email['date']}
Subject: {original_email['subject']}

{original_email['body']}
"""
            
            msg.attach(MIMEText(forward_content, 'plain', 'utf-8'))
            
            # 发送邮件
            recipients = [forward_to]
            result = self.smtp_connection.sendmail(self.email_account, recipients, msg.as_string())
            
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
            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
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
            self.imap_connection.store(email_id, '-FLAGS', '\\Seen')
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


if __name__ == '__main__':
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