"""
任务执行模块
执行各种邮件任务，如回复邮件、归档邮件、转发邮件、删除邮件、标记邮件等
每个任务对应一个函数，接受从 agent.py 传递来的参数，执行相应的邮件处理操作
支持批量操作
"""

from typing import Dict, Any, Optional, List
import mailer
import deepseek
from config import Config


class TaskExecutor:
    """任务执行器类"""
    
    def __init__(self):
        """初始化任务执行器"""
        self.email_client = mailer.EmailClient()
        self.deepseek_api = deepseek.DeepSeekAPI()
        # 缓存：保存最近为某封邮件生成的自动回复（按不可变UID索引）
        # 结构：{ uid: { 'reply_content': str, 'subject': str, 'from': str, 'index': int|None, 'created_at': float } }
        self.generated_reply_cache: dict[str, dict] = {}
        
        # 任务处理函数映射
        self.task_handlers = {
            'reply_email': self.reply_to_email,
            'archive_email': self.archive_email,
            'delete_email': self.delete_email_task,
            'forward_email': self.forward_email_task,
            'mark_read': self.mark_email_as_read,
            'mark_unread': self.mark_email_as_unread,
            'summarize_email': self.summarize_email,
            'analyze_priority': self.analyze_email_priority,
            'move_email': self.move_email_to_folder,
            'generate_reply': self.generate_auto_reply,
            'send_generated_reply': self.send_generated_reply,
            'list_emails': self.list_recent_emails,
            'search_email': self.search_emails
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
        if intent not in self.task_handlers:
            return {
                'success': False,
                'message': f'不支持的任务类型: {intent}',
                'data': None
            }
        
        try:
            handler = self.task_handlers[intent]
            result = handler(parameters)
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'任务执行异常: {str(e)}',
                'data': None
            }
    
    def _get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        获取邮件，支持特殊ID（如'latest'）和时间排序索引
        
        Args:
            email_id: 邮件ID、特殊标识或时间排序索引
            
        Returns:
            Optional[Dict[str, Any]]: 邮件信息
        """
        if email_id == 'latest':
            # 获取最新的一封邮件
            emails = self.email_client.get_recent_emails(count=1)
            if emails:
                return emails[0]
            return None
        elif email_id.isdigit():
            # 如果是数字，按时间排序索引获取
            index = int(email_id)
            return self.email_client.get_email_by_index(index)
        else:
            # 尝试按原始IMAP UID获取（向后兼容）
            email_info = self.email_client.get_email(email_id)
            if email_info:
                email_info['original_uid'] = email_id
            return email_info
    
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
        email_id = parameters.get('email_id')
        custom_reply = parameters.get('reply_content')
        
        # 获取原始邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 如果没有提供自定义回复：仅生成并返回供审核，不发送
        if not custom_reply:
            print("→ 正在生成自动回复...")
            auto_reply = self.deepseek_api.generate_reply(email_info['body'])
            # 使用原始IMAP UID作为稳定键，避免时间索引变化导致错发
            from time import time as _now
            uid_key = email_info.get('original_uid') or email_info.get('id') or str(email_id)
            if uid_key:
                self.generated_reply_cache[uid_key] = {
                    'reply_content': auto_reply,
                    'subject': email_info.get('subject', ''),
                    'from': email_info.get('from', ''),
                    'index': email_info.get('index'),
                    'created_at': _now()
                }
            return {
                'success': True,
                'message': '已生成自动回复（未发送），请审核后决定是否发送',
                'data': {
                    'email_id': email_id,
                    'subject': email_info['subject'],
                    'reply_content': auto_reply
                }
            }
        
        # 提供了自定义回复内容：执行发送
        success = self.email_client.send_reply(email_info, custom_reply)
        if success:
            return {
                'success': True,
                'message': f'已成功回复邮件: {email_info["subject"]}',
                'data': {
                    'email_id': email_id,
                    'subject': email_info['subject'],
                    'reply_content': custom_reply
                }
            }
        else:
            return {
                'success': False,
                'message': '回复邮件失败',
                'data': None
            }

    def send_generated_reply(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送最近为某封邮件生成并缓存的自动回复
        
        Args:
            parameters: 可包含 email_id（可选，不传则尝试使用最近一次缓存）
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get('email_id')
        email_info = None
        uid_key = None

        # 选择缓存项：优先指定 email_id，否则按创建时间选择最新的
        if email_id:
            # 尝试解析邮件以获得其 UID
            email_info = self._get_email_by_id(email_id)
            if not email_info:
                return {
                    'success': False,
                    'message': f'未找到邮件: {email_id}',
                    'data': None
                }
            uid_key = email_info.get('original_uid') or email_info.get('id') or str(email_id)
        else:
            if not self.generated_reply_cache:
                return {
                    'success': False,
                    'message': '没有可发送的自动回复草稿，请先生成自动回复',
                    'data': None
                }
            # 选择 created_at 最大的缓存项
            uid_key = max(self.generated_reply_cache.items(), key=lambda kv: kv[1].get('created_at', 0))[0]

        if not uid_key or uid_key not in self.generated_reply_cache:
            return {
                'success': False,
                'message': '未找到对应的自动回复草稿，请先生成自动回复',
                'data': None
            }
        
        # 使用稳定 UID 精确获取原邮件，避免“第1封”随时间变化
        if not email_info:
            # 直接用 IMAP UID 获取
            try:
                email_info = self.email_client.get_email(uid_key)
            except Exception:
                email_info = None
        
        cache_entry = self.generated_reply_cache[uid_key]
        reply_content = cache_entry.get('reply_content', '')

        # 若仍无法获取原邮件，使用快照信息构造最小 email_info 发送（无线程头）
        if not email_info:
            email_info = {
                'from': cache_entry.get('from', ''),
                'subject': cache_entry.get('subject', ''),
            }
        
        # 简单提醒：noreply 地址可能无法接收
        try:
            recipient = (email_info.get('from') or '').lower()
            if 'noreply' in recipient or 'no-reply' in recipient:
                print("提示: 目标似为 noreply 地址，可能不会接收回复。")
        except Exception:
            pass

        success = self.email_client.send_reply(email_info, reply_content)
        if success:
            # 发送成功后移除缓存，避免重复发送
            try:
                del self.generated_reply_cache[uid_key]
            except KeyError:
                pass
            return {
                'success': True,
                'message': f'已发送自动回复: {email_info.get("subject", "")} ',
                'data': {
                    'email_id': email_info.get('id') or uid_key or email_id,
                    'subject': email_info.get('subject', '')
                }
            }
        else:
            return {
                'success': False,
                'message': '发送自动回复失败',
                'data': None
            }
    
    def archive_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        归档邮件任务（支持批量操作）
        
        Args:
            parameters: 包含 email_id 和可选的 folder_name，或 batch_operation 和 count
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        folder_name = parameters.get('folder_name', Config.ARCHIVE_FOLDER)
        
        # 检查是否为批量操作
        if parameters.get('batch_operation') == True:
            count = parameters.get('count')
            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        'success': False,
                        'message': f'无效的邮件数量: {count}',
                        'data': None
                    }
                return self._archive_multiple_emails(count, folder_name)
        
        # 检查是否有多个邮件ID
        if 'email_ids' in parameters:
            return self._archive_emails_by_ids(parameters['email_ids'], folder_name)
        
        # 单个邮件归档
        email_id = parameters.get('email_id')
        if not email_id:
            return {
                'success': False,
                'message': '缺少邮件ID',
                'data': None
            }
        
        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 使用原始IMAP UID归档邮件
        original_uid = email_info.get('original_uid', email_id)
        success = self.email_client.archive_email_to_folder(original_uid, folder_name)
        
        if success:
            return {
                'success': True,
                'message': f'已将邮件归档到 {folder_name}: {email_info["subject"]}',
                'data': {
                    'email_id': email_id,
                    'folder_name': folder_name
                }
            }
        else:
            return {
                'success': False,
                'message': '归档邮件失败',
                'data': None
            }
    
    def _archive_emails_by_ids(self, email_ids: List[str], folder_name: str) -> Dict[str, Any]:
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量归档
        result = self.email_client.batch_archive_emails(original_uids, folder_name)
        
        return {
            'success': True,
            'message': f'批量归档完成，成功归档 {result["success"]} 封邮件到 {folder_name}，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'archived': result['success'],
                'failed': result['failed'],
                'folder_name': folder_name,
                'results': result['results']
            }
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        print(f"→ 找到 {len(emails)} 封邮件，正在批量归档到 {folder_name}...")
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量归档
        result = self.email_client.batch_archive_emails(original_uids, folder_name)
        
        return {
            'success': True,
            'message': f'批量归档完成，成功归档 {result["success"]} 封邮件到 {folder_name}，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'archived': result['success'],
                'failed': result['failed'],
                'folder_name': folder_name,
                'results': result['results']
            }
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
        if parameters.get('batch_operation') == True:
            count = parameters.get('count')
            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        'success': False,
                        'message': f'无效的邮件数量: {count}',
                        'data': None
                    }
                return self._delete_multiple_emails(count)
        
        # 检查是否有多个邮件ID
        if 'email_ids' in parameters:
            return self._delete_emails_by_ids(parameters['email_ids'])
        
        # 单个邮件删除
        email_id = parameters.get('email_id')
        if not email_id:
            return {
                'success': False,
                'message': '缺少邮件ID',
                'data': None
            }
        
        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 使用原始IMAP UID删除邮件
        original_uid = email_info.get('original_uid', email_id)
        success = self.email_client.delete_email(original_uid)
        
        if success:
            return {
                'success': True,
                'message': f'已删除邮件: {email_info["subject"]}',
                'data': {
                    'email_id': email_id
                }
            }
        else:
            return {
                'success': False,
                'message': '删除邮件失败',
                'data': None
            }
    
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量删除
        result = self.email_client.batch_delete_emails(original_uids)
        
        return {
            'success': True,
            'message': f'批量删除完成，成功删除 {result["success"]} 封邮件，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'deleted': result['success'],
                'failed': result['failed'],
                'results': result['results']
            }
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        print(f"→ 找到 {len(emails)} 封邮件，正在批量删除...")
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量删除
        result = self.email_client.batch_delete_emails(original_uids)
        
        return {
            'success': True,
            'message': f'批量删除完成，成功删除 {result["success"]} 封邮件，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'deleted': result['success'],
                'failed': result['failed'],
                'results': result['results']
            }
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
        if parameters.get('batch_operation') == True:
            count = parameters.get('count')
            forward_to = parameters.get('forward_to') or parameters.get('email_address')
            
            if not forward_to:
                return {
                    'success': False,
                    'message': '批量转发需要指定目标邮箱地址',
                    'data': None
                }
            
            if count:
                try:
                    count = int(count)
                except (ValueError, TypeError):
                    return {
                        'success': False,
                        'message': f'无效的邮件数量: {count}',
                        'data': None
                    }
                return self._forward_multiple_emails(count, forward_to)
        
        # 单个邮件转发
        email_id = parameters.get('email_id')
        recipients = parameters.get('recipients', [])
        forward_to = parameters.get('forward_to') or parameters.get('email_address')
        
        # 获取原始邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
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
            return {
                'success': False,
                'message': '缺少转发目标邮箱地址',
                'data': None
            }
    
    def _forward_to_single_recipient(self, email_info: Dict[str, Any], forward_to: str) -> Dict[str, Any]:
        """转发到单个收件人"""
        success = self.email_client.forward_email(email_info, forward_to)
        
        if success:
            return {
                'success': True,
                'message': f'已将邮件转发到: {forward_to}',
                'data': {
                    'email_id': email_info.get('id'),
                    'forward_to': forward_to,
                    'subject': email_info['subject']
                }
            }
        else:
            return {
                'success': False,
                'message': '转发邮件失败',
                'data': None
            }
    
    def _forward_to_multiple_recipients(self, email_info: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
        """转发到多个收件人（一封邮件转发给多个人）"""
        print(f"→ 正在将邮件转发到 {len(recipients)} 个收件人...")
        
        result = self.email_client.batch_forward_email(email_info, recipients)
        
        return {
            'success': True,
            'message': f'多收件人转发完成，成功转发到 {result["success"]} 个邮箱，失败 {result["failed"]} 个',
            'data': {
                'email_id': email_info.get('id'),
                'subject': email_info['subject'],
                'total': result['total'],
                'success_count': result['success'],
                'failed_count': result['failed'],
                'results': result['results']
            }
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
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
                    results.append({
                        'index': i,
                        'subject': email['subject'],
                        'status': 'forwarded'
                    })
                else:
                    failed_count += 1
                    results.append({
                        'index': i,
                        'subject': email['subject'],
                        'status': 'failed'
                    })
            except Exception as e:
                failed_count += 1
                results.append({
                    'index': i,
                    'subject': email['subject'],
                    'status': f'error: {str(e)}'
                })
        
        return {
            'success': True,
            'message': f'批量转发完成，成功转发 {forwarded_count} 封邮件到 {forward_to}，失败 {failed_count} 封',
            'data': {
                'total': len(emails),
                'forwarded': forwarded_count,
                'failed': failed_count,
                'forward_to': forward_to,
                'results': results
            }
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
        if 'email_ids' in parameters:
            return self._mark_multiple_as_read(parameters['email_ids'])
        
        # 单个邮件标记
        email_id = parameters.get('email_id')
        if not email_id:
            return {
                'success': False,
                'message': '缺少邮件ID',
                'data': None
            }
        
        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 使用原始IMAP UID标记已读
        original_uid = email_info.get('original_uid', email_id)
        success = self.email_client.mark_email_as_read(original_uid)
        
        if success:
            return {
                'success': True,
                'message': f'已将邮件标记为已读',
                'data': {
                    'email_id': email_id
                }
            }
        else:
            return {
                'success': False,
                'message': '标记邮件失败',
                'data': None
            }
    
    def _mark_multiple_as_read(self, email_ids: List[str]) -> Dict[str, Any]:
        """批量标记已读"""
        print(f"→ 正在批量标记 {len(email_ids)} 封邮件为已读...")
        
        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量标记
        result = self.email_client.batch_mark_as_read(original_uids)
        
        return {
            'success': True,
            'message': f'批量标记完成，成功标记 {result["success"]} 封邮件为已读，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'marked': result['success'],
                'failed': result['failed'],
                'results': result['results']
            }
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
        if 'email_ids' in parameters:
            return self._mark_multiple_as_unread(parameters['email_ids'])
        
        # 单个邮件标记
        email_id = parameters.get('email_id')
        if not email_id:
            return {
                'success': False,
                'message': '缺少邮件ID',
                'data': None
            }
        
        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 使用原始IMAP UID标记未读
        original_uid = email_info.get('original_uid', email_id)
        success = self.email_client.mark_email_as_unread(original_uid)
        
        if success:
            return {
                'success': True,
                'message': f'已将邮件标记为未读',
                'data': {
                    'email_id': email_id
                }
            }
        else:
            return {
                'success': False,
                'message': '标记邮件失败',
                'data': None
            }
    
    def _mark_multiple_as_unread(self, email_ids: List[str]) -> Dict[str, Any]:
        """批量标记未读"""
        print(f"→ 正在批量标记 {len(email_ids)} 封邮件为未读...")
        
        # 获取邮件信息
        emails = self._get_emails_by_ids(email_ids)
        if not emails:
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        # 提取原始UID
        original_uids = [email.get('original_uid') for email in emails if email.get('original_uid')]
        
        # 批量标记
        result = self.email_client.batch_mark_as_unread(original_uids)
        
        return {
            'success': True,
            'message': f'批量标记完成，成功标记 {result["success"]} 封邮件为未读，失败 {result["failed"]} 封',
            'data': {
                'total': result['total'],
                'marked': result['success'],
                'failed': result['failed'],
                'results': result['results']
            }
        }
    
    def summarize_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成邮件摘要（支持批量操作）
        
        Args:
            parameters: 包含 email_id 或 count（批量操作）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get('email_id')
        count = parameters.get('count')
        
        # 如果是批量总结操作
        if count and not email_id:
            try:
                count = int(count)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'message': f'无效的邮件数量: {count}',
                    'data': None
                }
            return self._summarize_multiple_emails(count)
        
        # 单个邮件总结
        if not email_id:
            return {
                'success': False,
                'message': '缺少邮件ID',
                'data': None
            }
        
        # 获取邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 生成摘要
        print("→ 正在生成邮件摘要...")
        summary = self.deepseek_api.summarize_email_content(email_info['body'])
        
        return {
            'success': True,
            'message': '邮件摘要生成成功',
            'data': {
                'email_id': email_id,
                'subject': email_info['subject'],
                'from': email_info['from'],
                'summary': summary
            }
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
            return {
                'success': False,
                'message': '没有找到邮件',
                'data': None
            }
        
        print(f"→ 找到 {len(emails)} 封邮件，正在生成批量摘要...")
        
        # 为每封邮件生成摘要
        summaries = []
        for i, email in enumerate(emails, 1):
            try:
                summary = self.deepseek_api.summarize_email_content(email['body'])
                summaries.append({
                    'index': i,
                    'subject': email['subject'],
                    'from': email['from'],
                    'summary': summary
                })
            except Exception as e:
                summaries.append({
                    'index': i,
                    'subject': email['subject'],
                    'from': email['from'],
                    'summary': f"摘要生成失败: {str(e)}"
                })
        
        return {
            'success': True,
            'message': f'批量摘要生成成功，共处理 {len(summaries)} 封邮件',
            'data': {
                'count': len(summaries),
                'summaries': summaries
            }
        }
    
    def analyze_email_priority(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析邮件优先级
        
        Args:
            parameters: 包含 email_id
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get('email_id')
        
        # 获取邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 分析优先级
        print("→ 正在分析邮件优先级...")
        priority_info = self.deepseek_api.analyze_priority(
            email_info['body'],
            f"{email_info['from_name']} <{email_info['from']}>"
        )
        
        return {
            'success': True,
            'message': '优先级分析完成',
            'data': {
                'email_id': email_id,
                'subject': email_info['subject'],
                'from': email_info['from'],
                'priority_analysis': priority_info
            }
        }
    
    def move_email_to_folder(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        移动邮件到指定文件夹
        
        Args:
            parameters: 包含 email_id 和 folder_name
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get('email_id')
        folder_name = parameters.get('folder_name')
        
        if not folder_name:
            return {
                'success': False,
                'message': '缺少目标文件夹名称',
                'data': None
            }
        
        # 获取邮件信息
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 使用原始IMAP UID移动邮件
        original_uid = email_info.get('original_uid', email_id)
        success = self.email_client.move_email_to_folder(original_uid, folder_name)
        
        if success:
            return {
                'success': True,
                'message': f'已将邮件移动到: {folder_name}',
                'data': {
                    'email_id': email_id,
                    'folder_name': folder_name
                }
            }
        else:
            return {
                'success': False,
                'message': '移动邮件失败',
                'data': None
            }
    
    def generate_auto_reply(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成自动回复（不发送）
        
        Args:
            parameters: 包含 email_id
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        email_id = parameters.get('email_id')
        
        # 获取邮件
        email_info = self._get_email_by_id(email_id)
        if not email_info:
            return {
                'success': False,
                'message': f'未找到邮件: {email_id}',
                'data': None
            }
        
        # 生成回复
        print("→ 正在生成自动回复...")
        reply_content = self.deepseek_api.generate_reply(email_info['body'])
        
        return {
            'success': True,
            'message': '自动回复生成成功',
            'data': {
                'email_id': email_id,
                'subject': email_info['subject'],
                'from': email_info['from'],
                'reply_content': reply_content
            }
        }
    
    def list_recent_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出最近的邮件
        
        Args:
            parameters: 包含 count（可选，默认10）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        count = parameters.get('count', 10)
        folder = parameters.get('folder')
        
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
                email_list.append({
                    'index': i,
                    'id': email.get('id'),
                    'subject': email['subject'],
                    'from': email['from'],
                    'from_name': email['from_name'],
                    'date': email['date']
                })
            
            return {
                'success': True,
                'message': f'找到 {len(emails)} 封邮件',
                'data': {
                    'count': len(emails),
                    'emails': email_list
                }
            }
        else:
            return {
                'success': False,
                'message': '未找到邮件',
                'data': None
            }
    
    def search_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        搜索邮件（简单实现）
        
        Args:
            parameters: 包含 content（搜索关键词）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        search_content = parameters.get('content', '')
        
        if not search_content:
            return {
                'success': False,
                'message': '缺少搜索关键词',
                'data': None
            }
        
        # 获取最近的邮件并进行简单搜索
        all_emails = self.email_client.get_recent_emails(count=50)
        
        # 在主题和正文中搜索
        matched_emails = []
        for email in all_emails:
            if (search_content.lower() in email['subject'].lower() or 
                search_content.lower() in email['body'].lower()):
                matched_emails.append({
                    'id': email.get('id'),
                    'subject': email['subject'],
                    'from': email['from'],
                    'from_name': email['from_name'],
                    'date': email['date']
                })
        
        if matched_emails:
            return {
                'success': True,
                'message': f'找到 {len(matched_emails)} 封相关邮件',
                'data': {
                    'search_term': search_content,
                    'count': len(matched_emails),
                    'emails': matched_emails
                }
            }
        else:
            return {
                'success': False,
                'message': f'未找到包含 "{search_content}" 的邮件',
                'data': None
            }


# 创建全局任务执行器实例
task_executor = TaskExecutor()


# ==================== 便捷函数 ====================

def execute_task(intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """执行任务（便捷函数）"""
    return task_executor.execute_task(intent, parameters)


if __name__ == '__main__':
    # 测试代码
    print("测试任务执行模块...")
    print("注意：需要先配置邮箱账户才能运行测试")