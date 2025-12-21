"""
配置文件模块
存放系统的配置项，包括邮件账户、IMAP/SMTP服务器设置、大模型API配置等
"""

import os
from typing import Any, Dict

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，忽略
    pass


class Config:
    """系统配置类"""

    # ==================== 邮件账户配置 ====================
    # 邮件账户名（从环境变量读取，必须设置）
    EMAIL_ACCOUNT: str = os.getenv("EMAIL_ACCOUNT", "")

    # 邮件账户密码或应用专用密码（从环境变量读取，必须设置）
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

    # ==================== IMAP 服务器配置 ====================
    # IMAP 服务器地址
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.qq.com")

    # IMAP 服务器端口（默认993为SSL端口）
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))

    # 是否使用SSL连接
    IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "True").lower() == "true"

    # ==================== SMTP 服务器配置 ====================
    # SMTP 服务器地址
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.qq.com")

    # SMTP 服务器端口（默认465为SSL端口，587为TLS端口）
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))

    # 是否使用SSL连接
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "True").lower() == "true"

    # 是否使用TLS连接
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "False").lower() == "true"

    # ==================== DeepSeek API 配置 ====================
    # DeepSeek API 的 URL 地址
    DEEPSEEK_API_URL: str = os.getenv(
        "DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"
    )

    # DeepSeek API 的密钥（从环境变量读取，必须设置）
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

    # DeepSeek 模型名称
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # API 请求超时时间（秒）
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

    # API 请求最大重试次数
    API_MAX_RETRIES: int = int(os.getenv("API_MAX_RETRIES", "3"))

    # ==================== 邮件处理配置 ====================
    # 默认邮件文件夹
    DEFAULT_FOLDER: str = "INBOX"

    # 不同邮件服务商的文件夹名称映射
    # 支持 QQ、163、Gmail 等邮箱的中英文及UTF-7编码文件夹名
    FOLDER_NAMES = {
        "sent": ["Sent Messages", "&XfJT0ZAB-", "已发送", "Sent"],  # QQ:"Sent Messages", 163:"&XfJT0ZAB-"
        "drafts": ["Drafts", "&g0l6P3ux-", "草稿箱", "Draft"],  # QQ:"Drafts", 163:"&g0l6P3ux-"
        "spam": ["Junk", "&V4NXPpCuTvY-", "垃圾邮件", "Spam"],  # QQ:"Junk", 163:"&V4NXPpCuTvY-"
        "trash": ["Deleted Messages", "&XfJSIJZk-", "已删除", "Trash"],  # QQ:"Deleted Messages", 163:"&XfJSIJZk-"
        "archive": ["Archive", "&dcVr0mWHTvZZOQ-", "归档"],  # 163:"&dcVr0mWHTvZZOQ-"
        "starred": ["Starred", "星标邮件", "Flagged"],  # 星标通过FLAGS实现，不是文件夹
    }

    # 归档文件夹名称（尝试列表中的第一个）
    ARCHIVE_FOLDER: str = FOLDER_NAMES["archive"][0]

    # 垃圾邮件文件夹
    SPAM_FOLDER: str = FOLDER_NAMES["spam"][0]

    # 已发送邮件文件夹
    SENT_FOLDER: str = FOLDER_NAMES["sent"][0]

    # 草稿箱文件夹
    DRAFTS_FOLDER: str = FOLDER_NAMES["drafts"][0]

    # 删除文件夹
    TRASH_FOLDER: str = FOLDER_NAMES["trash"][0]

    # 每次获取的最大邮件数量
    MAX_EMAILS_FETCH: int = int(os.getenv("MAX_EMAILS_FETCH", "50"))

    # ==================== 系统配置 ====================
    # 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # 日志文件路径
    LOG_FILE: str = os.getenv("LOG_FILE", "email_agent.log")

    # 是否启用调试模式
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"

    # ==================== 大模型参数配置 ====================
    # 生成回复时的温度参数（0-2之间，越高越随机）
    REPLY_TEMPERATURE: float = float(os.getenv("REPLY_TEMPERATURE", "0.7"))

    # 生成回复的最大token数
    REPLY_MAX_TOKENS: int = int(os.getenv("REPLY_MAX_TOKENS", "500"))

    # 摘要生成的最大token数
    SUMMARY_MAX_TOKENS: int = int(os.getenv("SUMMARY_MAX_TOKENS", "200"))

    # 意图识别的最大token数
    INTENT_MAX_TOKENS: int = int(os.getenv("INTENT_MAX_TOKENS", "100"))

    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        获取所有配置项的字典形式

        Returns:
            Dict[str, Any]: 包含所有配置项的字典
        """
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }

    @classmethod
    def validate_config(cls) -> bool:
        """
        验证配置项是否完整和有效

        Returns:
            bool: 配置是否有效
        """
        # 检查必需的配置项
        required_fields = [
            "EMAIL_ACCOUNT",
            "EMAIL_PASSWORD",
            "IMAP_SERVER",
            "SMTP_SERVER",
            "DEEPSEEK_API_KEY",
        ]

        for field in required_fields:
            value = getattr(cls, field, None)
            if not value:
                print(f"错误: 配置项 {field} 未设置")
                print(f"请设置环境变量 {field} 或创建 .env 文件")
                return False

        return True

    @classmethod
    def print_config(cls, hide_sensitive: bool = True) -> None:
        """
        打印当前配置（用于调试）

        Args:
            hide_sensitive: 是否隐藏敏感信息（如密码、API密钥）
        """
        sensitive_fields = ["EMAIL_PASSWORD", "DEEPSEEK_API_KEY"]

        print("=" * 50)
        print("当前系统配置:")
        print("=" * 50)

        for key, value in cls.get_config_dict().items():
            if hide_sensitive and key in sensitive_fields:
                print(f"{key}: {'*' * 8}")
            else:
                print(f"{key}: {value}")

        print("=" * 50)


# 创建全局配置实例
config = Config()


# ==================== 常用邮件服务器配置模板 ====================
EMAIL_PROVIDERS = {
    "gmail": {
        "IMAP_SERVER": "imap.gmail.com",
        "IMAP_PORT": 993,
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": 465,
    },
    "outlook": {
        "IMAP_SERVER": "outlook.office365.com",
        "IMAP_PORT": 993,
        "SMTP_SERVER": "smtp.office365.com",
        "SMTP_PORT": 587,
        "SMTP_USE_TLS": True,
        "SMTP_USE_SSL": False,
    },
    "qq": {
        "IMAP_SERVER": "imap.qq.com",
        "IMAP_PORT": 993,
        "SMTP_SERVER": "smtp.qq.com",
        "SMTP_PORT": 465,
    },
    "163": {
        "IMAP_SERVER": "imap.163.com",
        "IMAP_PORT": 993,
        "SMTP_SERVER": "smtp.163.com",
        "SMTP_PORT": 465,
    },
}


def setup_email_provider(provider: str) -> None:
    """
    快速设置常用邮件服务商的配置

    Args:
        provider: 邮件服务商名称（gmail, outlook, qq, 163等）
    """
    if provider.lower() in EMAIL_PROVIDERS:
        provider_config = EMAIL_PROVIDERS[provider.lower()]
        for key, value in provider_config.items():
            setattr(Config, key, value)
        print(f"已设置 {provider} 邮件服务器配置")
    else:
        print(f"不支持的邮件服务商: {provider}")
        print(f"支持的服务商: {', '.join(EMAIL_PROVIDERS.keys())}")


if __name__ == "__main__":
    # 测试配置模块
    print("测试配置模块...")
    config.print_config(hide_sensitive=True)

    # 验证配置
    if config.validate_config():
        print("\n✓ 配置验证通过")
    else:
        print("\n✗ 配置验证失败，请检查配置项")
