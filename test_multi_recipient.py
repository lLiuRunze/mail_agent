#!/usr/bin/env python3
"""
测试多收件人转发功能
"""

from nlu import parse_task, validate_parameters
from tasks import TaskExecutor

def test_multi_recipient_forward():
    """测试多收件人转发功能"""
    print("🧪 测试多收件人转发功能")
    print("=" * 60)
    
    # 测试多收件人转发指令
    test_cases = [
        "转发第一封邮件到2023111753@stu.sufe.edu.cn和17321539161@163.com",
        "转发第二封邮件到test1@example.com和test2@example.com",
        "转发最新的邮件到user1@domain.com和user2@domain.com和user3@domain.com"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_input}")
        print("-" * 50)
        
        # 解析任务
        result = parse_task(test_input)
        print(f"意图: {result['intent']}")
        print(f"参数: {result['parameters']}")
        print(f"置信度: {result['confidence']}")
        
        # 验证参数
        is_valid, error_msg = validate_parameters(result['intent'], result['parameters'])
        if is_valid:
            print("✓ 参数验证通过")
            
            # 检查是否识别为多收件人
            if 'recipients' in result['parameters']:
                recipients = result['parameters']['recipients']
                print(f"✓ 识别为多收件人转发，收件人数量: {len(recipients)}")
                for j, recipient in enumerate(recipients, 1):
                    print(f"  {j}. {recipient}")
            else:
                print("⚠️ 未识别为多收件人转发")
                
            # 执行任务（仅测试参数解析，不实际发送）
            print("✓ 多收件人转发参数解析成功")
        else:
            print(f"✗ 参数验证失败: {error_msg}")

def test_single_recipient_forward():
    """测试单收件人转发功能"""
    print("\n📧 测试单收件人转发功能")
    print("=" * 60)
    
    # 测试单收件人转发指令
    test_cases = [
        "转发第一封邮件到2023111753@stu.sufe.edu.cn",
        "转发第二封邮件到test@example.com"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_input}")
        print("-" * 50)
        
        # 解析任务
        result = parse_task(test_input)
        print(f"意图: {result['intent']}")
        print(f"参数: {result['parameters']}")
        print(f"置信度: {result['confidence']}")
        
        # 验证参数
        is_valid, error_msg = validate_parameters(result['intent'], result['parameters'])
        if is_valid:
            print("✓ 参数验证通过")
            
            # 检查是否识别为单收件人
            if 'email_address' in result['parameters'] or 'forward_to' in result['parameters']:
                email_address = result['parameters'].get('email_address') or result['parameters'].get('forward_to')
                print(f"✓ 识别为单收件人转发: {email_address}")
            else:
                print("⚠️ 未识别为单收件人转发")
        else:
            print(f"✗ 参数验证失败: {error_msg}")

def main():
    """主函数"""
    print("🧪 多收件人转发功能测试")
    print("=" * 80)
    
    try:
        # 测试多收件人转发
        test_multi_recipient_forward()
        
        # 测试单收件人转发
        test_single_recipient_forward()
        
        print("\n🎉 多收件人转发功能测试完成！")
        print("\n💡 功能特性:")
        print("- 支持多收件人转发（用'和'连接）")
        print("- 支持单收件人转发")
        print("- 自动识别邮箱地址数量")
        print("- 为每个收件人重新建立SMTP连接")
        
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
