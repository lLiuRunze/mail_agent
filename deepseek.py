"""
大模型 API 调用模块
负责调用 DeepSeek API 进行邮件内容分析、自动回复生成、情感分析等
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from config import Config


class DeepSeekAPI:
    """DeepSeek API 调用类"""

    def __init__(self):
        """初始化 DeepSeek API 客户端"""
        self.api_url = Config.DEEPSEEK_API_URL
        self.api_key = Config.DEEPSEEK_API_KEY
        self.model = Config.DEEPSEEK_MODEL
        self.timeout = Config.API_TIMEOUT
        self.max_retries = Config.API_MAX_RETRIES

        # 设置请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Optional[str]:
        """
        向 DeepSeek API 发送请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制生成的随机性
            max_tokens: 最大生成token数

        Returns:
            Optional[str]: API 返回的文本内容，失败返回 None
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )

                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    wait_time = 2**attempt
                    print(f"API 速率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API 请求失败，状态码: {response.status_code}")
                    print(f"错误信息: {response.text}")
                    return None

            except requests.exceptions.Timeout:
                print(f"API 请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                return None

            except requests.exceptions.RequestException as e:
                print(f"API 请求异常: {str(e)}")
                return None

            except (KeyError, json.JSONDecodeError) as e:
                print(f"解析 API 响应失败: {str(e)}")
                return None

        return None

    def analyze_email_content(self, email_content: str) -> Dict[str, Any]:
        """
        分析邮件内容，返回分类和情感分析结果

        Args:
            email_content: 邮件正文内容

        Returns:
            Dict[str, Any]: 包含分类、情感、主题等分析结果
        """
        prompt = f"""请分析以下邮件内容，并以JSON格式返回分析结果：

邮件内容：
{email_content}

请返回以下信息（必须是有效的JSON格式）：
{{
    "category": "邮件分类（工作/个人/营销/通知/其他）",
    "sentiment": "情感倾向（积极/中性/消极）",
    "urgency": "紧急程度（高/中/低）",
    "topics": ["主题1", "主题2"],
    "summary": "简短摘要（一句话）"
}}"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的邮件分析助手，擅长分析邮件内容并提取关键信息。",
            },
            {"role": "user", "content": prompt},
        ]

        response = self._make_request(messages, temperature=0.3, max_tokens=300)

        if response:
            try:
                # 尝试提取JSON内容
                # 有时模型会在JSON前后添加说明文字，需要提取纯JSON部分
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result
                else:
                    print("响应中未找到有效的JSON格式")
                    return self._get_default_analysis()
            except json.JSONDecodeError as e:
                print(f"解析邮件分析结果失败: {str(e)}")
                print(f"原始响应: {response}")
                return self._get_default_analysis()

        return self._get_default_analysis()

    def generate_reply(self, email_content: str, context: str = "") -> str:
        """
        根据邮件内容生成自动回复

        Args:
            email_content: 原始邮件内容
            context: 额外的上下文信息

        Returns:
            str: 生成的回复内容
        """
        prompt = f"""请根据以下邮件内容生成一封专业、礼貌的回复邮件：

原始邮件：
{email_content}

{f"额外信息：{context}" if context else ""}

要求：
1. 回复要简洁明了
2. 语气要专业礼貌
3. 直接给出回复内容，不需要添加"回复："等前缀
4. 不需要包含发件人、收件人等邮件头信息"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的邮件助手，擅长撰写得体的邮件回复。",
            },
            {"role": "user", "content": prompt},
        ]

        response = self._make_request(
            messages,
            temperature=Config.REPLY_TEMPERATURE,
            max_tokens=Config.REPLY_MAX_TOKENS,
        )

        return response if response else "感谢您的邮件，我会尽快处理并回复您。"

    def summarize_email_content(self, email_content: str) -> str:
        """
        生成邮件内容的简短摘要

        Args:
            email_content: 邮件正文内容

        Returns:
            str: 邮件摘要
        """
        prompt = f"""请用一到两句话总结以下邮件的核心内容：

邮件内容：
{email_content}

要求：
1. 摘要要简洁明了
2. 突出重点信息
3. 不超过100字"""

        messages = [
            {"role": "system", "content": "你是一个专业的文本摘要助手。"},
            {"role": "user", "content": prompt},
        ]

        response = self._make_request(
            messages, temperature=0.3, max_tokens=Config.SUMMARY_MAX_TOKENS
        )

        return response if response else "无法生成摘要"

    def analyze_priority(self, email_content: str, sender: str = "") -> Dict[str, Any]:
        """
        分析邮件的优先级和紧急程度

        Args:
            email_content: 邮件内容
            sender: 发件人信息

        Returns:
            Dict[str, Any]: 包含优先级、紧急程度、原因等信息
        """
        prompt = f"""请分析以下邮件的优先级和紧急程度，并以JSON格式返回结果：

{f"发件人：{sender}" if sender else ""}
邮件内容：
{email_content}

请返回以下信息（必须是有效的JSON格式）：
{{
    "priority": "优先级（高/中/低）",
    "urgency": "紧急程度（紧急/一般/不紧急）",
    "is_important": true/false,
    "reason": "判断理由",
    "suggested_action": "建议的处理方式"
}}"""

        messages = [
            {"role": "system", "content": "你是一个专业的邮件优先级分析助手。"},
            {"role": "user", "content": prompt},
        ]

        response = self._make_request(messages, temperature=0.3, max_tokens=200)

        if response:
            try:
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result
            except json.JSONDecodeError as e:
                print(f"解析优先级分析结果失败: {str(e)}")

        return {
            "priority": "中",
            "urgency": "一般",
            "is_important": False,
            "reason": "无法分析",
            "suggested_action": "正常处理",
        }

    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        返回默认的邮件分析结果

        Returns:
            Dict[str, Any]: 默认分析结果
        """
        return {
            "category": "其他",
            "sentiment": "中性",
            "urgency": "中",
            "topics": [],
            "summary": "无法分析邮件内容",
        }


# 创建全局 API 实例
deepseek_api = DeepSeekAPI()


# ==================== 便捷函数 ====================


def analyze_email_content(email_content: str) -> Dict[str, Any]:
    """
    分析邮件内容（便捷函数）

    Args:
        email_content: 邮件内容

    Returns:
        Dict[str, Any]: 分析结果
    """
    return deepseek_api.analyze_email_content(email_content)


def generate_reply(email_content: str, context: str = "") -> str:
    """
    生成邮件回复（便捷函数）

    Args:
        email_content: 原始邮件内容
        context: 额外上下文

    Returns:
        str: 生成的回复
    """
    return deepseek_api.generate_reply(email_content, context)


def summarize_email_content(email_content: str) -> str:
    """
    生成邮件摘要（便捷函数）

    Args:
        email_content: 邮件内容

    Returns:
        str: 邮件摘要
    """
    return deepseek_api.summarize_email_content(email_content)


def analyze_priority(email_content: str, sender: str = "") -> Dict[str, Any]:
    """
    分析邮件优先级（便捷函数）

    Args:
        email_content: 邮件内容
        sender: 发件人

    Returns:
        Dict[str, Any]: 优先级分析结果
    """
    return deepseek_api.analyze_priority(email_content, sender)


if __name__ == "__main__":
    # 测试代码
    print("测试 DeepSeek API 模块...")

    # 测试邮件内容
    test_email = """
    您好，
    
    关于明天的项目会议，我想确认一下时间和地点。
    另外，我已经准备好了项目进度报告，会在会议上分享。
    
    请回复确认。
    
    谢谢！
    """

    print("\n1. 测试邮件内容分析...")
    analysis = analyze_email_content(test_email)
    print(f"分析结果: {json.dumps(analysis, ensure_ascii=False, indent=2)}")

    print("\n2. 测试生成回复...")
    reply = generate_reply(test_email)
    print(f"生成的回复:\n{reply}")

    print("\n3. 测试生成摘要...")
    summary = summarize_email_content(test_email)
    print(f"邮件摘要: {summary}")

    print("\n4. 测试优先级分析...")
    priority = analyze_priority(test_email, "张三 <zhangsan@example.com>")
    print(f"优先级分析: {json.dumps(priority, ensure_ascii=False, indent=2)}")
