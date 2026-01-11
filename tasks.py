"""
任务执行模块
执行各种邮件任务，如回复邮件、归档邮件、转发邮件、删除邮件、标记邮件等
每个任务对应一个函数，接受从 agent.py 传递来的参数，执行相应的邮件处理操作
支持批量操作
"""

from typing import Any, Dict, List, Optional

import deepseek
import mailer
from config import Config


class TaskExecutor:
    """任务执行器类"""

    # 不可回复的系统地址模式
    _NON_REPLYABLE_ADDRESSES = {
        "10000@qq.com",
        "no-reply@",
        "noreply@",
        "donotreply@",
        "do-not-reply@",
        "notification@",
        "notifications@",
        "alert@",
        "alerts@",
        "info@",
        "support@",
        "help@",
        "admin@",
        "administrator@",
        "mailer-daemon@",
        "postmaster@",
        "root@",
        "server@",
        "system@",
        "auto@",
        "automated@",
    }

    def __init__(self, email_client: Optional[mailer.EmailClient] = None):
        """初始化任务执行器"""
        self.email_client = email_client or mailer.EmailClient()
        self.deepseek_api = deepseek.DeepSeekAPI()

        # 任务处理函数映射
        self.task_handlers = {
            "reply_email": self.reply_to_email,
            "archive_email": self.archive_email,
            "delete_email": self.delete_email_task,
            "forward_email": self.forward_email_task,
            "mark_read": self.mark_email_as_read,
            "mark_unread": self.mark_email_as_unread,
            "summarize_email": self.summarize_email,
            "analyze_priority": self.analyze_email_priority,
            "batch_classify": self.batch_classify_emails,
            "move_email": self.move_email_to_folder,
            "generate_reply": self.generate_auto_reply,
            "list_emails": self.list_recent_emails,
            "search_email": self.search_emails,
            "compose_email": self.compose_email,
            "get_email_detail": self.get_email_detail,
            "unknown": self.handle_unknown_intent,
        }

    def execute_task(self, intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务的统一入口

        Args:
            intent: 任务意图
            parameters: 任务参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 如果意图不在处理器中，当作 unknown 处理
        if intent not in self.task_handlers:
            intent = "unknown"
            # 保存原始用户输入到参数中
            if "user_input" not in parameters:
                parameters["user_input"] = parameters.get("content", "")

        try:
            handler = self.task_handlers[intent]
            result = handler(parameters)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"任务执行异常: {str(e)}",
                "data": None,
            }

    def _get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        获取邮件，支持特殊ID（如'latest'）、IMAP UID 和时间排序索引

        Args:
            email_id: 邮件ID、特殊标识或时间排序索引

        Returns:
            Optional[Dict[str, Any]]: 邮件信息
        """
        if email_id == "latest":
            # 获取最新的一封邮件
            emails = self.email_client.get_recent_emails(count=1)
            if emails:
                return emails[0]
            return None
        
        # 先尝试按 IMAP UID 获取（直接从IMAP服务器获取）
        email_info = self.email_client.get_email(email_id)
        if email_info:
            # 如果成功获取，添加 original_uid
            email_info["original_uid"] = email_id
            return email_info
        
        # 如果按UID获取失败，且是纯数字，尝试按索引获取
        if email_id.isdigit():
            index = int(email_id)
            return self.email_client.get_email_by_index(index)
        
        return None

    def _get_emails_by_ids(self, email_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取邮件

        Args:
            email_ids: 邮件ID列表

        Returns:
            List[Dict[str, Any]]: 邮件信息列表
        """
        emails = []
        for email_id in email_ids:
            email_info = self._get_email_by_id(email_id)
            if email_info:
                emails.append(email_info)
        return emails

    def reply_to_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        回复邮件任务

        Args:
            parameters: 包含 email_id 和可选的 reply_content

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")
        custom_reply = parameters.get("reply_content")

        # 获取原始邮件，如果不可回复则尝试后续邮件
        original_email_id = email_id
        max_attempts = 5
        # 如果email_id不是数字（如"latest"），只尝试一次
        if not original_email_id.isdigit():
            max_attempts = 1
        attempt = 0
        found_replyable = False
        email_info = None

        while attempt < max_attempts:
            if original_email_id.isdigit():
                current_email_id = str(int(original_email_id) + attempt)
            else:
                current_email_id = original_email_id
            email_info = self._get_email_by_id(current_email_id)
            if not email_info:
                break

            # 检查是否是可回复的地址
            from_address = email_info.get("from", "").lower()
            is_non_replyable = False
            for pattern in self._NON_REPLYABLE_ADDRESSES:
                if pattern.endswith("@"):
                    # 前缀模式，如 "no-reply@"
                    if from_address.startswith(pattern):
                        is_non_replyable = True
                        break
                else:
                    # 完整地址匹配
                    if from_address == pattern:
                        is_non_replyable = True
                        break

            if not is_non_replyable:
                found_replyable = True
                # 记录我们实际回复的邮件
                if attempt > 0:
                    print(f"→ 邮件 {original_email_id} 不可回复，已自动选择邮件 {current_email_id}")
                break
            else:
                attempt += 1
                # 继续尝试下一封邮件

        if not email_info or not found_replyable:
            # 获取最近的邮件列表，供用户选择
            recent_emails = self.email_client.get_recent_emails(count=5)
            email_list = []
            for i, email in enumerate(recent_emails, 1):
                from_addr = email.get("from", "未知")
                subject = email.get("subject", "无主题")
                email_list.append(f"{i}. {subject} (来自: {from_addr})")

            message = f"无法回复邮件: {original_email_id}。该地址可能无法接收回复。\n\n最近的邮件列表:\n" + "\n".join(email_list)
            return {
                "success": False,
                "message": message,
                "data": None,
            }

        # 如果没有提供自定义回复，则生成自动回复
        if not custom_reply:
            print("→ 正在生成自动回复...")
            custom_reply = self.deepseek_api.generate_reply(email_info["body"])

        # 发送回复
        success = self.email_client.send_reply(email_info, custom_reply)

        if success:
            return {
                "success": True,
                "message": f"已成功回复邮件: {email_info['subject']}",
                "data": {
                    "email_id": email_id,
                    "subject": email_info["subject"],
                    "reply_content": custom_reply,
                },
            }
        else:
            return {"success": False, "message": "回复邮件失败", "data": None}

    def archive_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        归档邮件任务（支持批量操作）

        Args:
            parameters: 包含 email_id 和可选的 folder_name，或 batch_operation 和 count

        Returns:
            Dict[str, Any]: 执行结果
        """
        folder_name = parameters.get("folder_name", Config.ARCHIVE_FOLDER)

        # 检查是否为批量操作
        if parameters.get("batch_operation") == True:
            count = parameters.get("count")
            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        "success": False,
                        "message": f"无效的邮件数量: {count}",
                        "data": None,
                    }
                return self._archive_multiple_emails(count, folder_name)

        # 检查是否有多个邮件ID
        if "email_ids" in parameters:
            return self._archive_emails_by_ids(parameters["email_ids"], folder_name)

        # 单个邮件归档
        email_id = parameters.get("email_id")
        if not email_id:
            return {"success": False, "message": "缺少邮件ID", "data": None}

        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 使用原始IMAP UID归档邮件
        original_uid = email_info.get("original_uid", email_id)
        success = self.email_client.archive_email_to_folder(original_uid, folder_name)

        if success:
            return {
                "success": True,
                "message": f"已将邮件归档到 {folder_name}: {email_info['subject']}",
                "data": {"email_id": email_id, "folder_name": folder_name},
            }
        else:
            return {"success": False, "message": "归档邮件失败", "data": None}

    def _archive_emails_by_ids(
        self, email_ids: List[str], folder_name: str
    ) -> Dict[str, Any]:
        """
        根据邮件ID列表批量归档

        Args:
            email_ids: 邮件ID列表
            folder_name: 目标文件夹

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在批量归档 {len(email_ids)} 封邮件到 {folder_name}...")

        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量归档
        result = self.email_client.batch_archive_emails(original_uids, folder_name)

        return {
            "success": True,
            "message": f"批量归档完成，成功归档 {result['success']} 封邮件到 {folder_name}，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "archived": result["success"],
                "failed": result["failed"],
                "folder_name": folder_name,
                "results": result["results"],
            },
        }

    def _archive_multiple_emails(self, count: int, folder_name: str) -> Dict[str, Any]:
        """
        批量归档多封邮件（按时间顺序）

        Args:
            count: 邮件数量
            folder_name: 目标文件夹

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在获取最近 {count} 封邮件...")

        # 获取邮件列表
        emails = self.email_client.get_recent_emails(count=count)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        print(f"→ 找到 {len(emails)} 封邮件，正在批量归档到 {folder_name}...")

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量归档
        result = self.email_client.batch_archive_emails(original_uids, folder_name)

        return {
            "success": True,
            "message": f"批量归档完成，成功归档 {result['success']} 封邮件到 {folder_name}，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "archived": result["success"],
                "failed": result["failed"],
                "folder_name": folder_name,
                "results": result["results"],
            },
        }

    def delete_email_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除邮件任务（支持批量操作）

        Args:
            parameters: 包含 email_id 或 batch_operation 和 count

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 检查是否为批量操作
        if parameters.get("batch_operation") == True:
            count = parameters.get("count")
            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        "success": False,
                        "message": f"无效的邮件数量: {count}",
                        "data": None,
                    }
                return self._delete_multiple_emails(count)

        # 检查是否有多个邮件ID
        if "email_ids" in parameters:
            return self._delete_emails_by_ids(parameters["email_ids"])

        # 单个邮件删除
        email_id = parameters.get("email_id")
        if not email_id:
            return {"success": False, "message": "缺少邮件ID", "data": None}

        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 使用原始IMAP UID删除邮件
        original_uid = email_info.get("original_uid", email_id)
        success = self.email_client.delete_email(original_uid)

        if success:
            return {
                "success": True,
                "message": f"已删除邮件: {email_info['subject']}",
                "data": {"email_id": email_id},
            }
        else:
            return {"success": False, "message": "删除邮件失败", "data": None}

    def _delete_emails_by_ids(self, email_ids: List[str]) -> Dict[str, Any]:
        """
        根据邮件ID列表批量删除

        Args:
            email_ids: 邮件ID列表

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在批量删除 {len(email_ids)} 封邮件...")

        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量删除
        result = self.email_client.batch_delete_emails(original_uids)

        return {
            "success": True,
            "message": f"批量删除完成，成功删除 {result['success']} 封邮件，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "deleted": result["success"],
                "failed": result["failed"],
                "results": result["results"],
            },
        }

    def _delete_multiple_emails(self, count: int) -> Dict[str, Any]:
        """
        批量删除多封邮件（按时间顺序）

        Args:
            count: 邮件数量

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在获取最近 {count} 封邮件...")

        # 获取邮件列表
        emails = self.email_client.get_recent_emails(count=count)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        print(f"→ 找到 {len(emails)} 封邮件，正在批量删除...")

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量删除
        result = self.email_client.batch_delete_emails(original_uids)

        return {
            "success": True,
            "message": f"批量删除完成，成功删除 {result['success']} 封邮件，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "deleted": result["success"],
                "failed": result["failed"],
                "results": result["results"],
            },
        }

    def forward_email_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        转发邮件任务（支持批量操作和多收件人）

        Args:
            parameters: 包含 email_id 和 forward_to/recipients，或 batch_operation 和 count

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 检查是否为批量操作（多封邮件转发给一个人）
        if parameters.get("batch_operation") == True:
            count = parameters.get("count")
            forward_to = parameters.get("forward_to") or parameters.get("email_address")

            if not forward_to:
                return {
                    "success": False,
                    "message": "批量转发需要指定目标邮箱地址",
                    "data": None,
                }

            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        "success": False,
                        "message": f"无效的邮件数量: {count}",
                        "data": None,
                    }
                return self._forward_multiple_emails(count, forward_to)

        # 单个邮件转发
        email_id = parameters.get("email_id")
        recipients = parameters.get("recipients", [])
        forward_to = parameters.get("forward_to") or parameters.get("email_address")

        # 获取原始邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 确定收件人列表
        if recipients and len(recipients) > 1:
            # 多收件人转发（一封邮件转发给多个人）
            return self._forward_to_multiple_recipients(email_info, recipients)
        elif forward_to:
            # 单收件人转发
            return self._forward_to_single_recipient(email_info, forward_to)
        elif recipients and len(recipients) == 1:
            # 只有一个收件人
            return self._forward_to_single_recipient(email_info, recipients[0])
        else:
            return {"success": False, "message": "缺少转发目标邮箱地址", "data": None}

    def _forward_to_single_recipient(
        self, email_info: Dict[str, Any], forward_to: str
    ) -> Dict[str, Any]:
        """转发到单个收件人"""
        success = self.email_client.forward_email(email_info, forward_to)

        if success:
            return {
                "success": True,
                "message": f"已将邮件转发到: {forward_to}",
                "data": {
                    "email_id": email_info.get("id"),
                    "forward_to": forward_to,
                    "subject": email_info["subject"],
                },
            }
        else:
            return {"success": False, "message": "转发邮件失败", "data": None}

    def _forward_to_multiple_recipients(
        self, email_info: Dict[str, Any], recipients: List[str]
    ) -> Dict[str, Any]:
        """转发到多个收件人（一封邮件转发给多个人）"""
        print(f"→ 正在将邮件转发到 {len(recipients)} 个收件人...")

        result = self.email_client.batch_forward_email(email_info, recipients)

        return {
            "success": True,
            "message": f"多收件人转发完成，成功转发到 {result['success']} 个邮箱，失败 {result['failed']} 个",
            "data": {
                "email_id": email_info.get("id"),
                "subject": email_info["subject"],
                "total": result["total"],
                "success_count": result["success"],
                "failed_count": result["failed"],
                "results": result["results"],
            },
        }

    def _forward_multiple_emails(self, count: int, forward_to: str) -> Dict[str, Any]:
        """
        批量转发多封邮件（多封邮件转发给一个人）

        Args:
            count: 邮件数量
            forward_to: 转发目标邮箱

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在获取最近 {count} 封邮件...")

        # 获取邮件列表
        emails = self.email_client.get_recent_emails(count=count)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        print(f"→ 找到 {len(emails)} 封邮件，正在批量转发到 {forward_to}...")

        # 批量转发邮件
        forwarded_count = 0
        failed_count = 0
        results = []

        for i, email in enumerate(emails, 1):
            try:
                # 为每封邮件重新建立SMTP连接
                if self.email_client.smtp_connection:
                    self.email_client.disconnect_smtp()

                success = self.email_client.forward_email(email, forward_to)
                if success:
                    forwarded_count += 1
                    results.append(
                        {"index": i, "subject": email["subject"], "status": "forwarded"}
                    )
                else:
                    failed_count += 1
                    results.append(
                        {"index": i, "subject": email["subject"], "status": "failed"}
                    )
            except Exception as e:
                failed_count += 1
                results.append(
                    {
                        "index": i,
                        "subject": email["subject"],
                        "status": f"error: {str(e)}",
                    }
                )

        return {
            "success": True,
            "message": f"批量转发完成，成功转发 {forwarded_count} 封邮件到 {forward_to}，失败 {failed_count} 封",
            "data": {
                "total": len(emails),
                "forwarded": forwarded_count,
                "failed": failed_count,
                "forward_to": forward_to,
                "results": results,
            },
        }

    def mark_email_as_read(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        标记邮件为已读（支持批量操作）

        Args:
            parameters: 包含 email_id 或 email_ids

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 检查是否有多个邮件ID
        if "email_ids" in parameters:
            return self._mark_multiple_as_read(parameters["email_ids"])

        # 单个邮件标记
        email_id = parameters.get("email_id")
        if not email_id:
            return {"success": False, "message": "缺少邮件ID", "data": None}

        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 使用原始IMAP UID标记已读
        original_uid = email_info.get("original_uid", email_id)
        success = self.email_client.mark_email_as_read(original_uid)

        if success:
            return {
                "success": True,
                "message": "已将邮件标记为已读",
                "data": {"email_id": email_id},
            }
        else:
            return {"success": False, "message": "标记邮件失败", "data": None}

    def _mark_multiple_as_read(self, email_ids: List[str]) -> Dict[str, Any]:
        """批量标记已读"""
        print(f"→ 正在批量标记 {len(email_ids)} 封邮件为已读...")

        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量标记
        result = self.email_client.batch_mark_as_read(original_uids)

        return {
            "success": True,
            "message": f"批量标记完成，成功标记 {result['success']} 封邮件为已读，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "marked": result["success"],
                "failed": result["failed"],
                "results": result["results"],
            },
        }

    def mark_email_as_unread(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        标记邮件为未读（支持批量操作）

        Args:
            parameters: 包含 email_id 或 email_ids

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 检查是否有多个邮件ID
        if "email_ids" in parameters:
            return self._mark_multiple_as_unread(parameters["email_ids"])

        # 单个邮件标记
        email_id = parameters.get("email_id")
        if not email_id:
            return {"success": False, "message": "缺少邮件ID", "data": None}

        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 使用原始IMAP UID标记未读
        original_uid = email_info.get("original_uid", email_id)
        success = self.email_client.mark_email_as_unread(original_uid)

        if success:
            return {
                "success": True,
                "message": "已将邮件标记为未读",
                "data": {"email_id": email_id},
            }
        else:
            return {"success": False, "message": "标记邮件失败", "data": None}

    def _mark_multiple_as_unread(self, email_ids: List[str]) -> Dict[str, Any]:
        """批量标记未读"""
        print(f"→ 正在批量标记 {len(email_ids)} 封邮件为未读...")

        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        # 提取原始UID
        original_uids = [
            email.get("original_uid") for email in emails if email.get("original_uid")
        ]

        # 批量标记
        result = self.email_client.batch_mark_as_unread(original_uids)

        return {
            "success": True,
            "message": f"批量标记完成，成功标记 {result['success']} 封邮件为未读，失败 {result['failed']} 封",
            "data": {
                "total": result["total"],
                "marked": result["success"],
                "failed": result["failed"],
                "results": result["results"],
            },
        }

    def summarize_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成邮件摘要（支持批量操作和搜索条件）

        Args:
            parameters: 包含 email_id 或 count（批量操作）或 sender/from（按发件人搜索）

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")
        count = parameters.get("count")
        sender = parameters.get("sender") or parameters.get("from")
        batch_operation = parameters.get("batch_operation", False)

        # 如果明确标记为批量操作但没有指定count，使用默认值5
        if batch_operation and not count and not email_id and not sender:
            count = 5

        # 如果是批量总结操作
        if count and not email_id:
            try:
                count = int(count)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "message": f"无效的邮件数量: {count}",
                    "data": None,
                }
            return self._summarize_multiple_emails(count)

        # 如果指定了发件人条件，先搜索邮件
        if not email_id and sender:
            print(f"→ 正在搜索发件人包含 '{sender}' 的邮件...")
            emails = self.email_client.get_recent_emails(count=50)
            matched_emails = [
                e for e in emails
                if sender.lower() in e.get("from", "").lower() or 
                   sender.lower() in e.get("from_name", "").lower()
            ]
            
            if not matched_emails:
                return {
                    "success": False,
                    "message": f"未找到发件人包含 '{sender}' 的邮件",
                    "data": None,
                }
            
            # 使用最近一封匹配的邮件的ID
            found_email = matched_emails[0]
            email_id = found_email.get("id")
            print(f"→ 找到邮件: {found_email.get('subject')}")

        # 单个邮件总结
        if not email_id:
            return {"success": False, "message": "缺少邮件ID或搜索条件", "data": None}

        # 获取完整的邮件信息（包含body）
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 生成摘要
        print("→ 正在生成邮件摘要...")
        summary = self.deepseek_api.summarize_email_content(email_info["body"])

        return {
            "success": True,
            "message": "邮件摘要生成成功",
            "data": {
                "email_id": email_id,
                "subject": email_info["subject"],
                "from": email_info["from"],
                "summary": summary,
            },
        }

    def _summarize_multiple_emails(self, count: int) -> Dict[str, Any]:
        """
        批量总结多封邮件

        Args:
            count: 邮件数量

        Returns:
            Dict[str, Any]: 执行结果
        """
        print(f"→ 正在获取最近 {count} 封邮件...")

        # 获取邮件列表
        emails = self.email_client.get_recent_emails(count=count)
        if not emails:
            return {"success": False, "message": "没有找到邮件", "data": None}

        print(f"→ 找到 {len(emails)} 封邮件，正在生成批量摘要...")

        # 为每封邮件生成摘要
        summaries = []
        for i, email in enumerate(emails, 1):
            try:
                summary = self.deepseek_api.summarize_email_content(email["body"])
                summaries.append(
                    {
                        "index": i,
                        "subject": email["subject"],
                        "from": email["from"],
                        "summary": summary,
                    }
                )
            except Exception as e:
                summaries.append(
                    {
                        "index": i,
                        "subject": email["subject"],
                        "from": email["from"],
                        "summary": f"摘要生成失败: {str(e)}",
                    }
                )

        return {
            "success": True,
            "message": f"批量摘要生成成功，共处理 {len(summaries)} 封邮件",
            "data": {"count": len(summaries), "summaries": summaries},
        }

    def analyze_email_priority(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析邮件优先级

        Args:
            parameters: 包含 email_id

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")

        # 获取邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 分析优先级
        print("→ 正在分析邮件优先级...")
        priority_info = self.deepseek_api.analyze_priority(
            email_info["body"], f"{email_info['from_name']} <{email_info['from']}>"
        )

        return {
            "success": True,
            "message": "优先级分析完成",
            "data": {
                "email_id": email_id,
                "subject": email_info["subject"],
                "from": email_info["from"],
                "priority_analysis": priority_info,
            },
        }

    def batch_classify_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量分类邮件内容

        Args:
            parameters: 包含 email_ids (邮件ID列表)

        Returns:
            Dict[str, Any]: 执行结果，包含所有邮件的分类信息
        """
        email_ids = parameters.get("email_ids", [])

        if not email_ids:
            return {
                "success": False,
                "message": "未提供邮件ID列表",
                "data": None,
            }

        print(f"→ 正在批量分类 {len(email_ids)} 封邮件...")
        
        classifications = []
        failed_count = 0

        for email_id in email_ids:
            try:
                # 获取邮件
                email_info = self._get_email_by_id(email_id)
                if not email_info:
                    print(f"✗ 未找到邮件: {email_id}")
                    failed_count += 1
                    continue

                # 分析邮件内容
                analysis_result = self.deepseek_api.analyze_email_content(email_info["body"])

                classifications.append({
                    "email_id": email_id,
                    "subject": email_info["subject"],
                    "from": email_info["from"],
                    "classification": analysis_result,
                })
                
                print(f"✓ 邮件 {email_id} 分类完成: {analysis_result.get('category', 'N/A')}")

            except Exception as e:
                print(f"✗ 分类邮件 {email_id} 失败: {str(e)}")
                failed_count += 1

        success_count = len(classifications)
        total_count = len(email_ids)

        return {
            "success": True,
            "message": f"批量分类完成，成功 {success_count}/{total_count}",
            "data": {
                "total": total_count,
                "success": success_count,
                "failed": failed_count,
                "classifications": classifications,
            },
        }

    def move_email_to_folder(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        移动邮件到指定文件夹

        Args:
            parameters: 包含 email_id 和 folder_name

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")
        folder_name = parameters.get("folder_name")

        if not folder_name:
            return {"success": False, "message": "缺少目标文件夹名称", "data": None}

        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 使用原始IMAP UID移动邮件
        original_uid = email_info.get("original_uid", email_id)
        success = self.email_client.move_email_to_folder(original_uid, folder_name)

        if success:
            return {
                "success": True,
                "message": f"已将邮件移动到: {folder_name}",
                "data": {"email_id": email_id, "folder_name": folder_name},
            }
        else:
            return {"success": False, "message": "移动邮件失败", "data": None}

    def generate_auto_reply(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成自动回复（不发送）

        Args:
            parameters: 包含 email_id

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")

        # 获取邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                "success": False,
                "message": f"未找到邮件: {email_id}",
                "data": None,
            }

        # 生成回复
        print("→ 正在生成自动回复...")
        reply_content = self.deepseek_api.generate_reply(email_info["body"])

        return {
            "success": True,
            "message": "自动回复生成成功",
            "data": {
                "email_id": email_id,
                "subject": email_info["subject"],
                "from": email_info["from"],
                "reply_content": reply_content,
            },
        }

    def list_recent_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出最近的邮件

        Args:
            parameters: 包含 count（可选，默认10）

        Returns:
            Dict[str, Any]: 执行结果
        """
        count = parameters.get("count", 10)
        folder = parameters.get("folder")

        # 确保count是整数
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 10

        # 获取邮件列表
        emails = self.email_client.get_recent_emails(count=count, folder=folder)

        if emails:
            # 格式化邮件列表
            email_list = []
            for i, email in enumerate(emails, 1):
                email_list.append(
                    {
                        "index": i,
                        "id": email.get("id"),
                        "subject": email["subject"],
                        "from": email["from"],
                        "from_name": email["from_name"],
                        "date": email["date"],
                    }
                )

            return {
                "success": True,
                "message": f"找到 {len(emails)} 封邮件",
                "data": {"count": len(emails), "emails": email_list},
            }
        else:
            return {"success": False, "message": "未找到邮件", "data": None}

    def search_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索邮件（支持按内容、发件人搜索）

        Args:
            parameters: 包含 content（搜索关键词）或 sender/from（发件人）

        Returns:
            Dict[str, Any]: 执行结果
        """
        search_content = parameters.get("content", "")
        sender = parameters.get("sender") or parameters.get("from")

        if not search_content and not sender:
            return {"success": False, "message": "缺少搜索关键词或发件人", "data": None}

        # 获取最近的邮件并进行简单搜索
        all_emails = self.email_client.get_recent_emails(count=50)

        # 搜索匹配的邮件
        matched_emails = []
        for email in all_emails:
            # 按内容搜索
            content_match = not search_content or (
                search_content.lower() in email["subject"].lower()
                or search_content.lower() in email["body"].lower()
            )
            
            # 按发件人搜索
            sender_match = not sender or (
                sender.lower() in email.get("from", "").lower()
                or sender.lower() in email.get("from_name", "").lower()
            )
            
            if content_match and sender_match:
                matched_emails.append(
                    {
                        "id": email.get("id"),
                        "subject": email["subject"],
                        "from": email["from"],
                        "from_name": email["from_name"],
                        "date": email["date"],
                    }
                )

        if matched_emails:
            search_desc = []
            if search_content:
                search_desc.append(f'内容包含"{search_content}"')
            if sender:
                search_desc.append(f'发件人包含"{sender}"')
            
            return {
                "success": True,
                "message": f"找到 {len(matched_emails)} 封相关邮件（{' 且 '.join(search_desc)}）",
                "data": {
                    "search_term": search_content,
                    "sender": sender,
                    "count": len(matched_emails),
                    "emails": matched_emails,
                },
            }
        else:
            search_desc = []
            if search_content:
                search_desc.append(f'内容包含"{search_content}"')
            if sender:
                search_desc.append(f'发件人包含"{sender}"')
            
            return {
                "success": False,
                "message": f'未找到满足条件的邮件（{" 且 ".join(search_desc)}）',
                "data": None,
            }

    def get_email_detail(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取邮件详细内容

        Args:
            parameters: 包含 email_id

        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get("email_id")
        
        if not email_id:
            return {"success": False, "message": "缺少邮件ID", "data": None}

        email_info = self._get_email_by_id(email_id)
        
        if email_info:
            return {
                "success": True,
                "message": "获取邮件详情成功",
                "data": {
                    "id": email_info.get("id") or email_info.get("original_uid") or email_id,
                    "subject": email_info.get("subject", "(无主题)"),
                    "from": email_info.get("from", ""),
                    "from_name": email_info.get("from_name", ""),
                    "to": email_info.get("to", []),
                    "cc": email_info.get("cc", []),
                    "date": email_info.get("date", ""),
                    "body": email_info.get("body", ""),
                    "attachments": email_info.get("attachments", []),
                    "read": email_info.get("read", False),
                },
            }
        else:
            return {
                "success": False,
                "message": f"未找到邮件 ID: {email_id}",
                "data": None,
            }

    def compose_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        撰写并发送新邮件任务

        Args:
            parameters: 包含 to_addr, subject, content_prompt/content, cc, bcc 等

        Returns:
            Dict[str, Any]: 执行结果
        """
        to_addr = parameters.get("to_addr")
        subject = parameters.get("subject")
        content_prompt = parameters.get("content_prompt") or parameters.get("content")
        cc = parameters.get("cc", [])
        bcc = parameters.get("bcc", [])

        if not to_addr:
            return {"success": False, "message": "缺少收件人邮箱地址", "data": None}

        # 如果没有提供主题，生成一个
        if not subject:
            print("→ 正在生成邮件主题...")
            # 使用deepseek API根据内容提示生成主题
            if content_prompt:
                subject = self.deepseek_api.generate_email_subject(content_prompt)
            else:
                subject = "新邮件"

        # 如果没有提供内容，根据内容提示生成
        if not content_prompt:
            return {"success": False, "message": "缺少邮件内容或内容提示", "data": None}

        print("→ 正在生成邮件内容...")
        # 使用deepseek API根据内容提示生成完整邮件内容
        email_content = self.deepseek_api.generate_email_content(content_prompt)

        # 发送邮件
        success = self.email_client.send_email(
            to_addr=to_addr,
            subject=subject,
            content=email_content,
            cc=cc if isinstance(cc, list) else [cc] if cc else [],
            bcc=bcc if isinstance(bcc, list) else [bcc] if bcc else []
        )

        if success:
            return {
                "success": True,
                "message": f"邮件已发送到: {to_addr}",
                "data": {
                    "to_addr": to_addr,
                    "subject": subject,
                    "content": email_content,
                    "cc": cc,
                    "bcc": bcc,
                },
            }
        else:
            return {"success": False, "message": "发送邮件失败", "data": None}

    def handle_unknown_intent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理未知意图，使用 AI 生成友好回复

        Args:
            parameters: 包含 user_input（用户原始输入）

        Returns:
            Dict[str, Any]: 执行结果
        """
        user_input = parameters.get("user_input", parameters.get("content", ""))
        
        if not user_input:
            return {
                "success": False,
                "message": "我无法理解您的请求，请提供更多信息。",
                "data": None,
            }

        # 使用 DeepSeek API 生成自然的回复
        try:
            print("→ 正在生成回复...")
            response = self.deepseek_api.chat(
                f"""你是一个智能邮件助手。用户输入了以下内容：

"{user_input}"

这不是一个邮件管理任务（如查看、发送、搜索、归档邮件等）。请生成一个友好、自然的回复。

如果是打招呼，友好地回应并介绍你的功能。
如果是提问，尽量回答或引导用户使用正确的功能。
如果是闲聊，简短回应并提醒用户你的主要功能。

回复要简洁、友好、有帮助。"""
            )
            
            return {
                "success": True,
                "message": response,
                "data": {"ai_reply": response},
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"我无法理解您的请求。我是邮件助手，可以帮您管理邮件。您可以尝试：查看最近邮件、搜索邮件、发送邮件等。",
                "data": None,
            }


# 创建全局任务执行器实例
task_executor = TaskExecutor()


# ==================== 便捷函数 ====================


def execute_task(intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """执行任务（便捷函数）"""
    return task_executor.execute_task(intent, parameters)


if __name__ == "__main__":
    # 测试代码
    print("测试任务执行模块...")
    print("注意：需要先配置邮箱账户才能运行测试")
