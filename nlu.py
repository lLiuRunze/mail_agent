"""
自然语言理解模块
解析用户输入的自然语言句子，识别任务意图并提取相关参数
混合使用正则表达式和 DeepSeek API 进行参数提取
"""

import json
import re
from typing import Any, Dict, List, Optional

from config import Config
from deepseek import DeepSeekAPI


class NLUEngine:
    """自然语言理解引擎"""

    def __init__(self):
        """初始化 NLU 引擎"""
        self.deepseek_api = DeepSeekAPI()

        # 定义支持的意图类型
        self.supported_intents = {
            "reply_email": "回复邮件",
            "archive_email": "归档邮件",
            "delete_email": "删除邮件",
            "forward_email": "转发邮件",
            "mark_read": "标记为已读",
            "mark_unread": "标记为未读",
            "summarize_email": "总结邮件",
            "analyze_priority": "分析优先级",
            "move_email": "移动邮件",
            "generate_reply": "生成回复",
            "list_emails": "列出邮件",
            "search_email": "搜索邮件",
            "unknown": "未知意图",
        }

        # 意图关键词映射（用于快速匹配）
        self.intent_keywords = {
            "reply_email": ["回复", "回信", "答复", "reply"],
            "archive_email": ["归档", "存档", "archive"],
            "delete_email": ["删除", "删掉", "移除", "delete", "remove"],
            "forward_email": ["转发", "转给", "forward"],
            "mark_read": ["标记已读", "已读", "mark as read", "read"],
            "mark_unread": ["标记未读", "未读", "mark as unread", "unread"],
            "summarize_email": ["总结", "摘要", "概括", "summarize", "summary"],
            "analyze_priority": ["优先级", "紧急", "重要", "priority", "urgent"],
            "move_email": ["移动", "移到", "move"],
            "generate_reply": ["生成回复", "自动回复", "generate reply"],
            "list_emails": ["列出", "显示", "查看邮件", "list", "show"],
            "search_email": ["搜索", "查找", "search", "find"],
        }

        self.email_pattern = re.compile(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:\.[A-Za-z]{2,})?"
        )

    def parse_task(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户输入的自然语言任务

        Args:
            user_input: 用户输入的自然语言文本

        Returns:
            Dict[str, Any]: 包含任务类型和参数的字典
        """
        # 先尝试快速匹配意图
        quick_result = self._quick_match(user_input)
        if quick_result and quick_result["intent"] != "unknown":
            print(f"✓ 快速匹配成功: {quick_result['intent']}")
            return quick_result

        # 使用大模型进行深度分析
        print("→ 使用大模型进行意图分析...")
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
                    # 混合提取参数（正则 + DeepSeek）
                    parameters = self._extract_parameters_hybrid(user_input, intent)
                    return {
                        "intent": intent,
                        "parameters": parameters,
                        "confidence": 0.8,
                        "original_input": user_input,
                    }

        return {
            "intent": "unknown",
            "parameters": {},
            "confidence": 0.0,
            "original_input": user_input,
        }

    def _extract_email_addresses(self, text: str) -> List[str]:
        """
        使用正则表达式提取所有邮箱地址

        Args:
            text: 输入文本

        Returns:
            List[str]: 邮箱地址列表
        """
        emails = self.email_pattern.findall(text)
        # 去重并保持顺序
        seen = set()
        unique_emails = []
        for email in emails:
            if email.lower() not in seen:
                seen.add(email.lower())
                unique_emails.append(email)
        return unique_emails

    def _extract_parameters_hybrid(
        self, user_input: str, intent: str
    ) -> Dict[str, Any]:
        """
        混合提取参数：正则表达式提取邮箱，DeepSeek提取其他参数

        Args:
            user_input: 用户输入
            intent: 识别出的意图

        Returns:
            Dict[str, Any]: 提取的参数
        """
        parameters = {}

        # 1. 使用正则表达式提取邮箱地址
        email_addresses = self._extract_email_addresses(user_input)

        if email_addresses:
            if len(email_addresses) == 1:
                # 单个邮箱
                parameters["email_address"] = email_addresses[0]
                if intent == "forward_email":
                    parameters["forward_to"] = email_addresses[0]
            else:
                # 多个邮箱
                parameters["recipients"] = email_addresses
                if intent == "forward_email":
                    # 转发意图：第一个可能是发件人，其余是收件人
                    parameters["email_address"] = email_addresses[0]
                    parameters["forward_to"] = email_addresses[0]
                    if len(email_addresses) > 1:
                        parameters["recipients"] = email_addresses

        # 2. 使用 DeepSeek 提取其他参数（邮件ID、数量、文件夹等）
        deepseek_params = self._extract_parameters_deepseek(user_input, intent)

        # 3. 合并参数（DeepSeek的参数优先级更高，但不覆盖已提取的邮箱）
        for key, value in deepseek_params.items():
            if key not in ["email_address", "forward_to", "recipients"]:
                # 非邮箱参数直接使用DeepSeek的结果
                parameters[key] = value
            elif key in [
                "email_address",
                "forward_to",
                "recipients",
            ] and not parameters.get(key):
                # 如果正则没提取到邮箱，使用DeepSeek的结果
                parameters[key] = value

        # 4. 后处理：确保参数格式正确
        parameters = self._post_process_parameters(parameters, intent)

        return parameters

    def _extract_parameters_deepseek(
        self, user_input: str, intent: str
    ) -> Dict[str, Any]:
        """
        使用DeepSeek深度分析提取参数（不包括邮箱地址）

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
    "email_id": "邮件ID或邮件ID列表",
    "folder_name": "文件夹名称（如果有）",
    "count": "数量（如果有）",
    "content": "内容（如果有）",
    "batch_operation": "是否为批量操作（true/false）"
}}

重要规则：
1. 只返回JSON格式，不要添加其他说明
2. 只包含实际提取到的参数，没有的参数不要包含
3. email_id提取规则：
   - "第一封"、"第1封" → "1"
   - "第二封"、"第2封" → "2"
   - "最新的"、"最后一封" → "latest"
   - "邮件123" → "123"
   - "邮件1,2,3" → ["1", "2", "3"]（列表形式）
   - "前三封" → batch_operation=true, count=3, email_id="1"
4. count提取规则：
   - "最近10封" → 10
   - "前5封" → 5
   - "三封邮件" → 3
5. batch_operation判断：
   - "前N封"、"最近N封"、"批量" → true
   - 单个邮件操作 → false
6. 不要提取邮箱地址（email_address、forward_to、recipients），这些由正则表达式处理

示例：
- "转发第一封邮件" → {{"email_id": "1", "batch_operation": false}}
- "转发邮件1,2,3" → {{"email_id": ["1", "2", "3"], "batch_operation": false}}
- "转发前三封邮件" → {{"email_id": "1", "batch_operation": true, "count": 3}}
- "删除最近5封邮件" → {{"email_id": "1", "batch_operation": true, "count": 5}}
- "归档邮件到工作文件夹" → {{"email_id": "latest", "folder_name": "工作文件夹", "batch_operation": false}}
- "总结最近10封邮件" → {{"batch_operation": true, "count": 10}}"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的参数提取助手，擅长从自然语言中提取结构化参数。",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.deepseek_api._make_request(
            messages,
            temperature=0.2,  # 降低温度以获得更稳定的结果
            max_tokens=Config.INTENT_MAX_TOKENS,
        )

        if response:
            try:
                # 提取JSON内容
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result
            except json.JSONDecodeError as e:
                print(f"✗ 解析DeepSeek响应失败: {str(e)}")
                return {}

        return {}

    def _post_process_parameters(
        self, parameters: Dict[str, Any], intent: str
    ) -> Dict[str, Any]:
        """
        后处理参数，确保格式正确

        Args:
            parameters: 原始参数
            intent: 意图类型

        Returns:
            Dict[str, Any]: 处理后的参数
        """
        # 处理 email_id 列表
        if "email_id" in parameters and isinstance(parameters["email_id"], list):
            # 如果是列表且只有一个元素，转为单个值
            if len(parameters["email_id"]) == 1:
                parameters["email_id"] = parameters["email_id"][0]
            # 如果是多个邮件ID，标记为批量操作
            elif len(parameters["email_id"]) > 1:
                parameters["email_ids"] = parameters["email_id"]
                parameters["email_id"] = parameters["email_id"][0]  # 保留第一个作为主ID
                parameters["batch_operation"] = True

        # 处理 count 参数
        if "count" in parameters:
            try:
                parameters["count"] = int(parameters["count"])
            except (ValueError, TypeError):
                pass

        # 处理 batch_operation
        if "batch_operation" in parameters:
            if isinstance(parameters["batch_operation"], str):
                parameters["batch_operation"] = (
                    parameters["batch_operation"].lower() == "true"
                )

        # 特殊处理：list_emails 默认数量
        if intent == "list_emails" and "count" not in parameters:
            parameters["count"] = 10

        # 特殊处理：forward_email 确保有 forward_to
        if intent == "forward_email":
            if "email_address" in parameters and "forward_to" not in parameters:
                parameters["forward_to"] = parameters["email_address"]

        return parameters

    def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        使用大模型分析用户输入的任务意图

        Args:
            user_input: 用户输入的自然语言

        Returns:
            Dict[str, Any]: 包含意图和参数的字典
        """
        # 构建提示词
        intent_list = "\n".join(
            [f"- {key}: {value}" for key, value in self.supported_intents.items()]
        )

        prompt = f"""请分析以下用户输入，识别用户的意图并提取相关参数。

支持的意图类型：
{intent_list}

用户输入："{user_input}"

请以JSON格式返回分析结果：
{{
    "intent": "意图类型（从上述列表中选择）",
    "parameters": {{
        "email_id": "邮件ID（如果有）",
        "folder_name": "文件夹名称（如果有）",
        "count": "数量（如果有）",
        "content": "内容（如果有）",
        "batch_operation": "是否为批量操作（true/false）"
    }},
    "confidence": 0.95,
    "explanation": "简短解释为什么识别为这个意图"
}}

注意：
1. 只返回JSON格式，不要添加其他说明
2. parameters中只包含实际提取到的参数
3. 不要提取邮箱地址，这些由正则表达式处理
4. confidence是0-1之间的浮点数"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的自然语言理解助手，擅长识别用户意图并提取参数。",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.deepseek_api._make_request(
            messages, temperature=0.3, max_tokens=Config.INTENT_MAX_TOKENS
        )

        if response:
            try:
                # 提取JSON内容
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)

                    # 验证意图是否有效
                    if result.get("intent") not in self.supported_intents:
                        result["intent"] = "unknown"

                    # 混合提取邮箱地址
                    email_addresses = self._extract_email_addresses(user_input)
                    if email_addresses:
                        if len(email_addresses) == 1:
                            result["parameters"]["email_address"] = email_addresses[0]
                            if result["intent"] == "forward_email":
                                result["parameters"]["forward_to"] = email_addresses[0]
                        else:
                            result["parameters"]["recipients"] = email_addresses

                    # 后处理参数
                    result["parameters"] = self._post_process_parameters(
                        result["parameters"], result["intent"]
                    )

                    # 添加原始输入
                    result["original_input"] = user_input

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
            "intent": "unknown",
            "parameters": {},
            "confidence": 0.0,
            "explanation": "无法识别用户意图",
            "original_input": user_input,
        }

    def validate_parameters(
        self, intent: str, parameters: Dict[str, Any]
    ) -> tuple[bool, str]:
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
            "reply_email": ["email_id"],
            "archive_email": [],  # 批量操作时不需要email_id
            "delete_email": [],  # 批量操作时不需要email_id
            "forward_email": [],  # 需要email_id或batch_operation，以及email_address或recipients
            "mark_read": ["email_id"],
            "mark_unread": ["email_id"],
            "summarize_email": [],  # 可以是单个邮件ID或批量操作
            "analyze_priority": ["email_id"],
            "move_email": ["email_id", "folder_name"],
            "generate_reply": ["email_id"],
            "list_emails": [],
            "search_email": ["content"],
        }

        if intent not in required_params:
            return True, ""  # 未知意图不验证

        # 特殊处理：批量操作
        if parameters.get("batch_operation") == True:
            # 批量操作需要count参数
            if "count" not in parameters:
                return False, "批量操作需要指定数量"

            # 批量转发需要目标邮箱
            if intent == "forward_email":
                if "email_address" not in parameters and "recipients" not in parameters:
                    return False, "批量转发需要指定目标邮箱"

            # 批量归档需要文件夹（可选，有默认值）
            # 批量删除不需要额外参数

            return True, ""

        # 单个操作验证
        missing_params = []
        for param in required_params[intent]:
            if param not in parameters or not parameters[param]:
                missing_params.append(param)

        # 特殊处理：转发邮件需要目标邮箱
        if intent == "forward_email":
            if "email_address" not in parameters and "recipients" not in parameters:
                missing_params.append("email_address 或 recipients")

        if missing_params:
            return False, f"缺少必需参数: {', '.join(missing_params)}"

        return True, ""

    def get_intent_description(self, intent: str) -> str:
        """
        获取意图的描述

        Args:
            intent: 意图类型

        Returns:
            str: 意图描述
        """
        return self.supported_intents.get(intent, "未知意图")


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


if __name__ == "__main__":
    # 测试代码
    print("测试自然语言理解模块（混合提取策略）...\n")

    # 测试用例
    test_cases = [
        # 单个邮件操作
        "回复邮件123",
        "转发第一封邮件到test@example.com",
        "删除最新的邮件",
        # 多收件人
        "转发邮件1到user1@example.com和user2@example.com",
        "把邮件2转给test@domain.com、admin@site.com",
        # 批量操作
        "转发前三封邮件到admin@example.com",
        "删除最近5封邮件",
        "归档前10封邮件到工作文件夹",
        "总结最近3封邮件",
        # 复杂邮箱地址
        "转发邮件到2023111753@stu.sufe.edu.cn",
        "把邮件1转给user.name+tag@sub.domain.com",
        # 列表形式
        "回复邮件1,2,3",
        "删除邮件5,6,7,8",
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"{'=' * 70}")
        print(f"测试 {i}: {test_input}")
        print(f"{'=' * 70}")

        result = parse_task(test_input)

        print(
            f"意图: {result['intent']} ({nlu_engine.get_intent_description(result['intent'])})"
        )
        print(f"置信度: {result.get('confidence', 0):.2f}")
        print(f"参数: {json.dumps(result['parameters'], ensure_ascii=False, indent=2)}")

        if "explanation" in result:
            print(f"解释: {result['explanation']}")

        # 验证参数
        is_valid, error_msg = validate_parameters(
            result["intent"], result["parameters"]
        )
        if is_valid:
            print("✓ 参数验证通过")
        else:
            print(f"✗ 参数验证失败: {error_msg}")

        print()
