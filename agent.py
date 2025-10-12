"""
主程序 - 智能邮件代理系统
负责接收用户输入的自然语言任务，解析并执行相应的操作
调用 nlu.py 模块处理用户输入，识别任务意图
根据任务类型调用相应的任务处理函数
"""

import sys
import json
from typing import Dict, Any, Optional
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # 如果没有 colorama，定义空的颜色类
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = ''
    class Style:
        RESET_ALL = ''

import nlu
import tasks
from config import Config

class EmailAgent:
    """智能邮件代理类"""
    
    def __init__(self):
        """初始化邮件代理"""
        self.nlu_engine = nlu.NLUEngine()
        self.task_executor = tasks.TaskExecutor()
        self.running = True
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}智能邮件代理系统 v1.0")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}系统已启动，输入 'help' 查看帮助，输入 'quit' 退出")
        print()
    
    def display_help(self):
        """显示帮助信息"""
        help_text = f"""
{Fore.CYAN}{'='*60}
{Fore.CYAN}帮助信息
{Fore.CYAN}{'='*60}

{Fore.YELLOW}支持的命令示例：{Style.RESET_ALL}

{Fore.GREEN}1. 邮件回复：{Style.RESET_ALL}
   - 回复邮件123
   - 回复最新的邮件
   
{Fore.GREEN}2. 邮件归档：{Style.RESET_ALL}
   - 归档邮件456
   - 把邮件789归档到工作文件夹
   
{Fore.GREEN}3. 邮件删除：{Style.RESET_ALL}
   - 删除邮件111
   - 删除第5封邮件
   
{Fore.GREEN}4. 邮件转发：{Style.RESET_ALL}
   - 转发邮件222到example@email.com
   - 把邮件333转给test@email.com
   
{Fore.GREEN}5. 邮件标记：{Style.RESET_ALL}
   - 标记邮件444为已读
   - 将邮件555标记为未读
   
{Fore.GREEN}6. 邮件摘要：{Style.RESET_ALL}
   - 总结邮件666
   - 摘要最新的邮件
   
{Fore.GREEN}7. 优先级分析：{Style.RESET_ALL}
   - 分析邮件777的优先级
   - 检查邮件888是否紧急
   
{Fore.GREEN}8. 邮件移动：{Style.RESET_ALL}
   - 移动邮件999到重要文件夹
   
{Fore.GREEN}9. 生成回复：{Style.RESET_ALL}
   - 为邮件123生成回复
   
{Fore.GREEN}10. 列出邮件：{Style.RESET_ALL}
   - 列出最近10封邮件
   - 显示最新的5封邮件
   
{Fore.GREEN}11. 搜索邮件：{Style.RESET_ALL}
   - 搜索关于项目的邮件
   - 查找包含会议的邮件

{Fore.YELLOW}系统命令：{Style.RESET_ALL}
   - help  : 显示此帮助信息
   - config: 显示当前配置
   - quit  : 退出系统
   - exit  : 退出系统

{Fore.CYAN}{'='*60}
"""
        print(help_text)
    
    def display_config(self):
        """显示当前配置"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}当前配置信息")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}邮箱账户:{Style.RESET_ALL} {Config.EMAIL_ACCOUNT}")
        print(f"{Fore.YELLOW}IMAP 服务器:{Style.RESET_ALL} {Config.IMAP_SERVER}:{Config.IMAP_PORT}")
        print(f"{Fore.YELLOW}SMTP 服务器:{Style.RESET_ALL} {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
        print(f"{Fore.YELLOW}DeepSeek 模型:{Style.RESET_ALL} {Config.DEEPSEEK_MODEL}")
        print(f"{Fore.CYAN}{'='*60}\n")
    def process_input(self, user_input: str) -> bool:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            bool: 是否继续运行
        """
        # 去除首尾空格
        user_input = user_input.strip()
        
        # 空输入
        if not user_input:
            return True
        
        # 系统命令处理
        if user_input.lower() in ['quit', 'exit', 'q']:
            print(f"{Fore.YELLOW}正在退出系统...")
            return False
        
        if user_input.lower() == 'help':
            self.display_help()
            return True
        
        if user_input.lower() == 'config':
            self.display_config()
            return True
        
        # 解析任务
        parse_result = self.parse_task(user_input)
        
        if not parse_result:
            print(f"{Fore.RED}✗ 无法理解您的请求，请重新输入")
            return True
        
        # 显示解析结果
        self.display_parse_result(parse_result)
        
        # 验证参数
        is_valid, error_msg = nlu.validate_parameters(
            parse_result['intent'],
            parse_result['parameters']
        )
        
        if not is_valid:
            print(f"{Fore.RED}✗ {error_msg}")
            print(f"{Fore.YELLOW}提示: 请提供完整的信息，例如邮件ID或邮箱地址")
            return True
        
        # 执行任务
        result = self.execute_task(parse_result)
        
        # 显示执行结果
        self.display_result(result)
        
        return True
    
    def parse_task(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        解析用户任务
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[Dict[str, Any]]: 解析结果
        """
        try:
            result = self.nlu_engine.parse_task(user_input)
            
            # 如果是未知意图且置信度很低，返回 None
            if result['intent'] == 'unknown' and result.get('confidence', 0) < 0.5:
                return None
            
            return result
        except Exception as e:
            print(f"{Fore.RED}✗ 解析任务时出错: {str(e)}")
            return None
    
    def execute_task(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            parse_result: 解析结果
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            intent = parse_result['intent']
            parameters = parse_result['parameters']
            
            result = self.task_executor.execute_task(intent, parameters)
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'执行任务时出错: {str(e)}',
                'data': None
            }
    def display_parse_result(self, parse_result: Dict[str, Any]):
        """
        显示解析结果
        
        Args:
            parse_result: 解析结果
        """
        intent = parse_result['intent']
        intent_desc = self.nlu_engine.get_intent_description(intent)
        confidence = parse_result.get('confidence', 0)
        
        print(f"\n{Fore.GREEN}✓ 识别意图: {intent_desc} (置信度: {confidence:.2f})")
        
        if parse_result['parameters']:
            print(f"{Fore.YELLOW}  参数:")
            for key, value in parse_result['parameters'].items():
                print(f"{Fore.YELLOW}    - {key}: {value}")
        print()
    
    def display_result(self, result: Dict[str, Any]):
        """
        显示执行结果
        
        Args:
            result: 执行结果
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        
        if result['success']:
            print(f"{Fore.GREEN}✓ {result['message']}")
            
            # 显示详细数据
            if result['data']:
                self.display_result_data(result['data'])
        else:
            print(f"{Fore.RED}✗ {result['message']}")
        
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def display_result_data(self, data: Dict[str, Any]):
        """
        显示结果数据
        
        Args:
            data: 结果数据
        """
        # 特殊处理邮件列表
        if 'emails' in data:
            print(f"\n{Fore.YELLOW}邮件列表:")
            for email in data['emails']:
                index = email.get('index', '?')
                subject = email.get('subject', '无主题')
                from_name = email.get('from_name', '')
                from_addr = email.get('from', '')
                date = email.get('date', '')
                
                print(f"{Fore.CYAN}  [{index}] {subject}")
                print(f"      发件人: {from_name} <{from_addr}>")
                print(f"      日期: {date}")
                print()
        
        # 显示摘要
        elif 'summary' in data:
            print(f"\n{Fore.YELLOW}邮件摘要:")
            print(f"{Fore.CYAN}  主题: {data.get('subject', '无主题')}")
            print(f"{Fore.CYAN}  发件人: {data.get('from', '未知')}")
            print(f"{Fore.GREEN}  摘要: {data['summary']}")
        
        # 显示优先级分析
        elif 'priority_analysis' in data:
            analysis = data['priority_analysis']
            print(f"\n{Fore.YELLOW}优先级分析:")
            print(f"{Fore.CYAN}  主题: {data.get('subject', '无主题')}")
            print(f"{Fore.CYAN}  发件人: {data.get('from', '未知')}")
            print(f"{Fore.GREEN}  优先级: {analysis.get('priority', '未知')}")
            print(f"{Fore.GREEN}  紧急程度: {analysis.get('urgency', '未知')}")
            print(f"{Fore.GREEN}  是否重要: {'是' if analysis.get('is_important') else '否'}")
            print(f"{Fore.GREEN}  理由: {analysis.get('reason', '无')}")
            print(f"{Fore.GREEN}  建议: {analysis.get('suggested_action', '无')}")
        
        # 显示回复内容
        elif 'reply_content' in data:
            print(f"\n{Fore.YELLOW}生成的回复:")
            print(f"{Fore.CYAN}  主题: Re: {data.get('subject', '无主题')}")
            print(f"{Fore.CYAN}  收件人: {data.get('from', '未知')}")
            print(f"{Fore.GREEN}  内容:")
            print(f"{Fore.WHITE}  {data['reply_content']}")
        
        # 显示搜索结果
        elif 'search_term' in data:
            print(f"\n{Fore.YELLOW}搜索关键词: {data['search_term']}")
            print(f"{Fore.YELLOW}找到 {data.get('count', 0)} 封相关邮件")
            if 'emails' in data:
                for email in data['emails']:
                    print(f"{Fore.CYAN}  - {email.get('subject', '无主题')}")
                    print(f"    发件人: {email.get('from', '未知')}")
                    print()
        
        # 默认显示所有数据
        else:
            print(f"\n{Fore.YELLOW}详细信息:")
            for key, value in data.items():
                if key not in ['raw_message']:  # 跳过原始消息对象
                    print(f"{Fore.CYAN}  {key}: {value}")
    def run(self):
        """运行主循环"""
        while self.running:
            try:
                # 获取用户输入
                user_input = input(f"{Fore.MAGENTA}>>> {Style.RESET_ALL}")
                
                # 处理输入
                self.running = self.process_input(user_input)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}检测到 Ctrl+C，正在退出...")
                self.running = False
            except EOFError:
                print(f"\n{Fore.YELLOW}检测到 EOF，正在退出...")
                self.running = False
            except Exception as e:
                print(f"{Fore.RED}✗ 发生错误: {str(e)}")
                if Config.DEBUG_MODE:
                    import traceback
                    traceback.print_exc()
        
        print(f"{Fore.GREEN}感谢使用智能邮件代理系统！")
        
def main():
    """主函数"""
    # 检查配置
    if not Config.validate_config():
        print(f"{Fore.RED}✗ 配置验证失败！")
        print(f"{Fore.YELLOW}请检查以下配置项：")
        print(f"  - EMAIL_ACCOUNT: 邮箱账户")
        print(f"  - EMAIL_PASSWORD: 邮箱密码或授权码")
        print(f"  - IMAP_SERVER: IMAP 服务器地址")
        print(f"  - SMTP_SERVER: SMTP 服务器地址")
        print(f"  - DEEPSEEK_API_KEY: DeepSeek API 密钥")
        print(f"\n{Fore.YELLOW}提示: 可以通过环境变量或修改 config.py 来设置这些配置")
        sys.exit(1)
    
    # 创建并运行代理
    agent = EmailAgent()
    agent.run()


if __name__ == '__main__':
    main()