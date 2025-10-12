"""
自然语言理解模块
解析用户输入的自然语言句子，识别任务意图并提取相关参数
调用 DeepSeek 或其他大模型 API 进行意图识别
"""

import json
import re
from typing import Dict, Any, Optional, List
from deepseek import DeepSeekAPI
from config import Config


class NLUEngine:
    """自然语言理解引擎"""
    
    def __init__(self):
        """初始化 NLU 引擎"""
        self.deepseek_api = DeepSeekAPI()
        
        # 定义支持的意图类型
        self.supported_intents = {
            'reply_email': '回复邮件',
            'archive_email': '归档邮件',
            'delete_email': '删除邮件',
            'forward_email': '转发邮件',
            'mark_read': '标记为已读',
            'mark_unread': '标记为未读',
            'summarize_email': '总结邮件',
            'analyze_priority': '分析优先级',
            'move_email': '移动邮件',
            'generate_reply': '生成回复',
            'list_emails': '列出邮件',
            'search_email': '搜索邮件',
            'unknown': '未知意图'
        }
        
        # 意图关键词映射（用于快速匹配）
        self.intent_keywords = {
            'reply_email': ['回复', '回信', '答复', 'reply'],
            'archive_email': ['归档', '存档', 'archive'],
            'delete_email': ['删除', '删掉', '移除', 'delete', 'remove'],
            'forward_email': ['转发', '转给', 'forward'],
            'mark_read': ['标记已读', '已读', 'mark as read', 'read'],
            'mark_unread': ['标记未读', '未读', 'mark as unread', 'unread'],
            'summarize_email': ['总结', '摘要', '概括', 'summarize', 'summary'],
            'analyze_priority': ['优先级', '紧急', '重要', 'priority', 'urgent'],
            'move_email': ['移动', '移到', 'move'],
            'generate_reply': ['生成回复', '自动回复', 'generate reply'],
            'list_emails': ['列出', '显示', '查看邮件', 'list', 'show'],
            'search_email': ['搜索', '查找', 'search', 'find']
        }
    
    def parse_task(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户输入的自然语言任务
        
        Args:
            user_input: 用户输入的自然语言文本
            
        Returns:
            Dict[str, Any]: 包含任务类型和参数的字典
        """
        # 先尝试快速匹配
        quick_result = self._quick_match(user_input)
        if quick_result and quick_result['intent'] != 'unknown':
            return quick_result
        
        # 使用大模型进行深度分析
        result = self.analyze_intent(user_input)
        
        return result
    
    def _quick_match(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        快速关键词匹配
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[Dict[str, Any]]: 匹配结果
        """
        user_input_lower = user_input.lower()
        
        # 遍历所有意图关键词
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    # 提取参数
                    parameters = self._extract_parameters(user_input, intent)
                    return {
                        'intent': intent,
                        'parameters': parameters,
                        'confidence': 0.8,
                        'original_input': user_input
                    }
        
        return {
            'intent': 'unknown',
            'parameters': {},
            'confidence': 0.0,
            'original_input': user_input
        }
    
    def _extract_parameters(self, user_input: str, intent: str) -> Dict[str, Any]:
        """
        从用户输入中提取参数（使用DeepSeek深度分析）
        
        Args:
            user_input: 用户输入
            intent: 识别出的意图
            
        Returns:
            Dict[str, Any]: 提取的参数
        """
        # 直接使用DeepSeek深度分析
        return self._extract_parameters_deepseek(user_input, intent)
    
    
    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        使用大模型分析用户输入的任务意图
        
        Args:
            user_input: 用户输入的自然语言
            
        Returns:
            Dict[str, Any]: 包含意图和参数的字典
        """
        # 构建提示词
        intent_list = '\n'.join([f"- {key}: {value}" for key, value in self.supported_intents.items()])
        
        prompt = f"""请分析以下用户输入，识别用户的意图并提取相关参数。

支持的意图类型：
{intent_list}

用户输入："{user_input}"

请以JSON格式返回分析结果：
{{
    "intent": "意图类型（从上述列表中选择）",
    "parameters": {{
        "email_id": "邮件ID（如果有）",
        "email_address": "邮箱地址（如果有）",
        "folder_name": "文件夹名称（如果有）",
        "count": "数量（如果有）",
        "content": "内容（如果有）"
    }},
    "confidence": 0.95,
    "explanation": "简短解释为什么识别为这个意图"
}}

注意：
1. 只返回JSON格式，不要添加其他说明
2. parameters中只包含实际提取到的参数
3. confidence是0-1之间的浮点数"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的自然语言理解助手，擅长识别用户意图并提取参数。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.deepseek_api._make_request(
            messages,
            temperature=0.3,
            max_tokens=Config.INTENT_MAX_TOKENS
        )
        
        if response:
            try:
                # 提取JSON内容
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # 验证意图是否有效
                    if result.get('intent') not in self.supported_intents:
                        result['intent'] = 'unknown'
                    
                    # 添加原始输入
                    result['original_input'] = user_input
                    
                    return result
                else:
                    print("✗ 响应中未找到有效的JSON格式")
                    return self._get_default_result(user_input)
                    
            except json.JSONDecodeError as e:
                print(f"✗ 解析意图分析结果失败: {str(e)}")
                print(f"原始响应: {response}")
                return self._get_default_result(user_input)
        
        return self._get_default_result(user_input)
    
    def _get_default_result(self, user_input: str) -> Dict[str, Any]:
        """
        返回默认的分析结果
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict[str, Any]: 默认结果
        """
        return {
            'intent': 'unknown',
            'parameters': {},
            'confidence': 0.0,
            'explanation': '无法识别用户意图',
            'original_input': user_input
        }
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证参数是否完整
        
        Args:
            intent: 意图类型
            parameters: 参数字典
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 定义每个意图所需的参数
        required_params = {
            'reply_email': ['email_id'],
            'archive_email': ['email_id'],
            'delete_email': ['email_id'],
            'forward_email': ['email_id', 'email_address'],
            'mark_read': ['email_id'],
            'mark_unread': ['email_id'],
            'summarize_email': ['email_id'],  # 可以是单个邮件ID或批量操作
            'analyze_priority': ['email_id'],
            'move_email': ['email_id', 'folder_name'],
            'generate_reply': ['email_id'],
            'list_emails': [],
            'search_email': ['content']
        }
        
        if intent not in required_params:
            return True, ""  # 未知意图不验证
        
        missing_params = []
        for param in required_params[intent]:
            if param not in parameters or not parameters[param]:
                missing_params.append(param)
        
        # 特殊处理：批量操作
        if parameters.get('batch_operation') == True:
            # 批量操作，email_id和email_address不是必需的
            if intent == 'forward_email':
                # 批量转发需要email_address
                if 'email_address' not in parameters:
                    return False, "批量转发需要指定邮箱地址"
            return True, ""
        
        # 特殊处理：如果是批量总结操作，允许没有email_id
        if intent == 'summarize_email' and 'count' in parameters and not parameters.get('email_id'):
            # 批量总结操作，不需要email_id
            return True, ""
        
        if missing_params:
            return False, f"缺少必需参数: {', '.join(missing_params)}"
        
        return True, ""
    
    
    def _extract_parameters_deepseek(self, user_input: str, intent: str) -> Dict[str, Any]:
        """
        使用DeepSeek深度分析提取参数
        
        Args:
            user_input: 用户输入
            intent: 识别出的意图
            
        Returns:
            Dict[str, Any]: 提取的参数
        """
        # 构建提示词
        prompt = f"""请从以下用户输入中提取与"{intent}"意图相关的参数：

用户输入："{user_input}"
意图：{intent}

请以JSON格式返回提取到的参数：
{{
    "email_id": "邮件ID（如果有）",
    "email_address": "邮箱地址（如果有）",
    "forward_to": "转发目标邮箱地址（如果有）",
    "recipients": "收件人列表（如果有多个收件人）",
    "folder_name": "文件夹名称（如果有）",
    "count": "数量（如果有）",
    "content": "内容（如果有）",
    "batch_operation": "是否为批量操作（true/false）"
}}

重要规则：
1. 只返回JSON格式，不要添加其他说明
2. 只包含实际提取到的参数，没有的参数不要包含
3. email_id必须是数字字符串或"latest"，不能是中文
4. 如果用户说"第一封邮件"、"第一封"、"第1封"，email_id必须是"1"
5. 如果用户说"最新的邮件"、"最新邮件"、"最后一封"，email_id必须是"latest"
6. 如果用户说"第二封邮件"、"第二封"、"第2封"，email_id必须是"2"
7. 如果用户说"第三封邮件"、"第三封"、"第3封"，email_id必须是"3"
8. 如果用户说"第四封邮件"、"第四封"、"第4封"，email_id必须是"4"
9. 如果用户说"第五封邮件"、"第五封"、"第5封"，email_id必须是"5"
10. 邮箱地址要完整且正确，格式为xxx@domain.com
11. 如果意图是forward_email，需要同时设置email_address和forward_to
12. 如果用户提供多个收件人（用"和"、"、"、"、"等连接），设置recipients为数组，如["email1@domain.com", "email2@domain.com"]
13. 邮箱地址识别要准确，注意域名顺序（如stu.sufe.edu.cn，不是stu.edu.sufe.cn）
14. 如果用户说"那个重要的邮件"、"那封邮件"等模糊表达，email_id必须是"latest"
15. 如果用户说"昨天收到的邮件"、"关于xxx的邮件"等，email_id必须是"latest"
16. 如果用户说"张三发来的邮件"，email_id必须是"latest"（因为无法确定具体ID）
17. 如果用户说"给项目经理"、"发给经理"等，但项目经理不是邮箱地址，则email_address应该是"latest"或空
18. 如果用户说"回复xxx的邮件"，email_id必须是"latest"
19. 如果无法确定具体的邮箱地址，不要设置email_address参数
20. 批量操作规则：
    - 如果用户说"前三封邮件"、"前5封邮件"、"最近3封邮件"等，设置batch_operation为true，count为对应数量
    - 如果用户说"转发前三封邮件"，email_id设为"1"，batch_operation设为true，count设为"3"
    - 如果用户说"删除前5封邮件"，email_id设为"1"，batch_operation设为true，count设为"5"
    - 如果用户说"归档最近3封邮件"，email_id设为"1"，batch_operation设为true，count设为"3"

示例：
- "转发第一封邮件到test@example.com" → {{"email_id": "1", "email_address": "test@example.com", "forward_to": "test@example.com", "batch_operation": false}}
- "转发第一封邮件到test@example.com和user@domain.com" → {{"email_id": "1", "recipients": ["test@example.com", "user@domain.com"], "batch_operation": false}}
- "转发前三封邮件到test@example.com" → {{"email_id": "1", "email_address": "test@example.com", "forward_to": "test@example.com", "batch_operation": true, "count": "3"}}
- "删除前5封邮件" → {{"email_id": "1", "batch_operation": true, "count": "5"}}
- "归档最近3封邮件到工作文件夹" → {{"email_id": "1", "folder_name": "工作文件夹", "batch_operation": true, "count": "3"}}
- "删除那个重要的邮件" → {{"email_id": "latest", "batch_operation": false}}
- "把邮件归档到工作文件夹" → {{"email_id": "latest", "folder_name": "工作文件夹", "batch_operation": false}}"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的参数提取助手，擅长从自然语言中提取结构化参数。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.deepseek_api._make_request(
            messages,
            temperature=0.3,
            max_tokens=Config.INTENT_MAX_TOKENS
        )
        
        if response:
            try:
                # 提取JSON内容
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # 根据意图添加特定参数
                    if intent == 'forward_email' and 'email_address' in result:
                        result['forward_to'] = result['email_address']
                    
                    if intent == 'list_emails' and 'count' not in result:
                        result['count'] = 10  # 默认显示10封
                    
                    return result
                else:
                    return {}
                    
            except json.JSONDecodeError as e:
                return {}
        
        return {}
    
    def get_intent_description(self, intent: str) -> str:
        """
        获取意图的描述
        
        Args:
            intent: 意图类型
            
        Returns:
            str: 意图描述
        """
        return self.supported_intents.get(intent, '未知意图')


# 创建全局 NLU 引擎实例
nlu_engine = NLUEngine()


# ==================== 便捷函数 ====================

def parse_task(user_input: str) -> Dict[str, Any]:
    """
    解析用户任务（便捷函数）
    
    Args:
        user_input: 用户输入
        
    Returns:
        Dict[str, Any]: 解析结果
    """
    return nlu_engine.parse_task(user_input)


def analyze_intent(user_input: str) -> Dict[str, Any]:
    """
    分析用户意图（便捷函数）
    
    Args:
        user_input: 用户输入
        
    Returns:
        Dict[str, Any]: 意图分析结果
    """
    return nlu_engine.analyze_intent(user_input)


def validate_parameters(intent: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证参数（便捷函数）
    
    Args:
        intent: 意图类型
        parameters: 参数字典
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    return nlu_engine.validate_parameters(intent, parameters)


if __name__ == '__main__':
    # 测试代码
    print("测试自然语言理解模块...\n")
    
    # 测试用例
    test_cases = [
        "回复邮件1,2,3",
        "把邮件4,5,6归档到工作文件夹",
        "删除第5封邮件",
        "转发邮件7,8,9到2023111753.stu.sufe.edu.cn",
        "标记邮件111为已读",
        "总结最新的邮件",
        "分析邮件222的优先级",
        "列出最近10封邮件",
        "搜索关于项目的邮件",
        "帮我处理一下邮件"  # 模糊输入
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"{'='*60}")
        print(f"测试 {i}: {test_input}")
        print(f"{'='*60}")
        
        result = parse_task(test_input)
        
        print(f"意图: {result['intent']} ({nlu_engine.get_intent_description(result['intent'])})")
        print(f"置信度: {result.get('confidence', 0):.2f}")
        print(f"参数: {json.dumps(result['parameters'], ensure_ascii=False, indent=2)}")
        
        if 'explanation' in result:
            print(f"解释: {result['explanation']}")
        
        # 验证参数
        is_valid, error_msg = validate_parameters(result['intent'], result['parameters'])
        if is_valid:
            print("✓ 参数验证通过")
        else:
            print(f"✗ 参数验证失败: {error_msg}")
        
        print()