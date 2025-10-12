#!/usr/bin/env python3
"""
邮件连接测试脚本
用于测试 IMAP 和 SMTP 连接是否正常
"""

import imaplib
import smtplib
import ssl
from config import Config


def test_imap_connection():
    """测试 IMAP 连接"""
    print("测试 IMAP 连接...")
    
    try:
        # 创建 SSL 上下文
        context = ssl.create_default_context()
        
        # 连接到 IMAP 服务器
        if Config.IMAP_USE_SSL:
            server = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT, ssl_context=context)
        else:
            server = imaplib.IMAP4(Config.IMAP_SERVER, Config.IMAP_PORT)
        
        # 登录
        server.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
        print("✓ IMAP 连接成功")
        
        # 选择收件箱
        server.select(Config.DEFAULT_FOLDER)
        print("✓ 收件箱访问成功")
        
        # 断开连接
        server.close()
        server.logout()
        print("✓ IMAP 连接已断开")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"✗ IMAP 连接失败: {e}")
        return False
    except Exception as e:
        print(f"✗ IMAP 连接异常: {e}")
        return False


def test_smtp_connection():
    """测试 SMTP 连接"""
    print("\n测试 SMTP 连接...")
    
    try:
        # 创建 SSL 上下文
        context = ssl.create_default_context()
        
        # 连接到 SMTP 服务器
        if Config.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, context=context)
        else:
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            if Config.SMTP_USE_TLS:
                server.starttls(context=context)
        
        # 登录
        server.login(Config.EMAIL_ACCOUNT, Config.EMAIL_PASSWORD)
        print("✓ SMTP 连接成功")
        
        # 断开连接
        server.quit()
        print("✓ SMTP 连接已断开")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ SMTP 认证失败: {e}")
        print("提示: 请检查邮箱地址和密码是否正确，Gmail 需要使用应用专用密码")
        return False
    except Exception as e:
        print(f"✗ SMTP 连接异常: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("邮件连接测试")
    print("=" * 50)
    
    # 显示当前配置
    print(f"邮箱账户: {Config.EMAIL_ACCOUNT}")
    print(f"IMAP 服务器: {Config.IMAP_SERVER}:{Config.IMAP_PORT}")
    print(f"SMTP 服务器: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
    print("=" * 50)
    
    # 测试连接
    imap_success = test_imap_connection()
    smtp_success = test_smtp_connection()
    
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"IMAP 连接: {'✓ 成功' if imap_success else '✗ 失败'}")
    print(f"SMTP 连接: {'✓ 成功' if smtp_success else '✗ 失败'}")
    
    if imap_success and smtp_success:
        print("\n🎉 所有连接测试通过！邮件代理可以正常使用。")
    else:
        print("\n❌ 连接测试失败，请检查配置：")
        print("1. 确保邮箱地址正确")
        print("2. 确保密码是 Gmail 应用专用密码（不是普通密码）")
        print("3. 确保已启用 2 步验证")
        print("4. 检查网络连接")
    
    print("=" * 50)


if __name__ == '__main__':
    main()
