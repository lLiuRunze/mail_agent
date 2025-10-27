"""
主程序 - 智能邮件代理系统
负责接收用户输入的自然语言任务，解析并执行相应的操作
调用 nlu.py 模块处理用户输入，识别任务意图
根据任务类型调用相应的任务处理函数
"""

import json
from typing import Any, Dict, Optional

from colorama import Fore, Style, init

import nlu
import tasks
from config import Config

# 初始化 colorama（用于彩色输出）
init(autoreset=True)


class EmailAgent:
    """智能邮件代理类"""

    def __init__(self):
        """初始化邮件代理"""
        self.nlu_engine = nlu.NLUEngine()
        self.task_executor = tasks.TaskExecutor()
        self.running = True

        print(f"{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}{'智能邮件代理系统 v1.0':^70}")
        print(f"{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.GREEN}✓ 系统已启动")
        print(f"{Fore.YELLOW}  输入 'help' 查看帮助")
        print(f"{Fore.YELLOW}  输入 'quit' 或 'exit' 退出系统")
        print(f"{Fore.CYAN}{'=' * 70}\n")

    def display_help(self):
        """显示帮助信息"""
        help_text = f"""
{Fore.CYAN}{"=" * 70}
{Fore.CYAN}{"帮助信息":^70}
{Fore.CYAN}{"=" * 70}

{Fore.YELLOW}【单个邮件操作】{Style.RESET_ALL}

{Fore.GREEN}1. 邮件回复：{Style.RESET_ALL}
   - 回复邮件1
   - 回复第一封邮件
   - 回复最新的邮件
   
{Fore.GREEN}2. 邮件归档：{Style.RESET_ALL}
   - 归档邮件2
   - 把邮件3归档到工作文件夹
   - 归档第一封邮件
   
{Fore.GREEN}3. 邮件删除：{Style.RESET_ALL}
   - 删除邮件5
   - 删除第一封邮件
   - 删除最新的邮件
   
{Fore.GREEN}4. 邮件转发：{Style.RESET_ALL}
   - 转发邮件1到user@example.com
   - 把第一封邮件转给test@domain.com
   
{Fore.GREEN}5. 邮件标记：{Style.RESET_ALL}
   - 标记邮件3为已读
   - 将第一封邮件标记为未读
   
{Fore.GREEN}6. 邮件摘要：{Style.RESET_ALL}
   - 总结邮件1
   - 摘要第一封邮件
   
{Fore.GREEN}7. 优先级分析：{Style.RESET_ALL}
   - 分析邮件2的优先级
   - 检查第一封邮件是否紧急

{Fore.YELLOW}【批量操作】{Style.RESET_ALL}

{Fore.GREEN}8. 批量归档：{Style.RESET_ALL}
   - 归档前5封邮件
   - 归档最近3封邮件到工作文件夹
   
{Fore.GREEN}9. 批量删除：{Style.RESET_ALL}
   - 删除前10封邮件
   - 删除最近5封邮件
   
{Fore.GREEN}10. 批量转发：{Style.RESET_ALL}
   - 转发前3封邮件到admin@example.com
   - 把最近5封邮件转给manager@domain.com
   
{Fore.GREEN}11. 多收件人转发：{Style.RESET_ALL}
   - 转发邮件1到user1@example.com和user2@example.com
   - 把第一封邮件转给test@a.com、admin@b.com
   
{Fore.GREEN}12. 批量摘要：{Style.RESET_ALL}
   - 总结最近5封邮件
   - 摘要前10封邮件

{Fore.YELLOW}【其他功能】{Style.RESET_ALL}

{Fore.GREEN}13. 列出邮件：{Style.RESET_ALL}
   - 列出最近10封邮件
   - 显示最新的5封邮件
   
{Fore.GREEN}14. 搜索邮件：{Style.RESET_ALL}
   - 搜索关于项目的邮件
   - 查找包含会议的邮件

{Fore.YELLOW}【系统命令】{Style.RESET_ALL}
   - help   : 显示此帮助信息
   - config : 显示当前配置
   - clear  : 清屏
   - quit   : 退出系统
   - exit   : 退出系统

{Fore.CYAN}{"=" * 70}
"""
        print(help_text)

    def display_config(self):
        """显示当前配置"""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}{'当前配置信息':^70}")
        print(f"{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.YELLOW}邮箱账户:{Style.RESET_ALL} {Config.EMAIL_ACCOUNT}")
        print(
            f"{Fore.YELLOW}IMAP 服务器:{Style.RESET_ALL} {Config.IMAP_SERVER}:{Config.IMAP_PORT}"
        )
        print(
            f"{Fore.YELLOW}SMTP 服务器:{Style.RESET_ALL} {Config.SMTP_SERVER}:{Config.SMTP_PORT}"
        )
        print(f"{Fore.YELLOW}DeepSeek 模型:{Style.RESET_ALL} {Config.DEEPSEEK_MODEL}")
        print(f"{Fore.YELLOW}默认文件夹:{Style.RESET_ALL} {Config.DEFAULT_FOLDER}")
        print(f"{Fore.YELLOW}归档文件夹:{Style.RESET_ALL} {Config.ARCHIVE_FOLDER}")
        print(f"{Fore.CYAN}{'=' * 70}\n")

    def clear_screen(self):
        """清屏"""
        import os

        os.system("cls" if os.name == "nt" else "clear")

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
        if user_input.lower() in ["quit", "exit", "q"]:
            print(f"{Fore.YELLOW}正在退出系统...")
            return False

        if user_input.lower() == "help":
            self.display_help()
            return True

        if user_input.lower() == "config":
            self.display_config()
            return True

        if user_input.lower() == "clear":
            self.clear_screen()
            return True

        # 解析任务
        print(f"{Fore.CYAN}→ 正在分析您的请求...")
        parse_result = self.parse_task(user_input)

        if not parse_result:
            print(f"{Fore.RED}✗ 无法理解您的请求，请重新输入")
            print(f"{Fore.YELLOW}提示: 输入 'help' 查看使用示例")
            return True

        # 显示解析结果
        self.display_parse_result(parse_result)

        # 验证参数
        is_valid, error_msg = nlu.validate_parameters(
            parse_result["intent"], parse_result["parameters"]
        )

        if not is_valid:
            print(f"{Fore.RED}✗ {error_msg}")
            print(f"{Fore.YELLOW}提示: 请提供完整的信息，例如邮件ID或邮箱地址")
            return True

        # 执行任务
        print(f"{Fore.CYAN}→ 正在执行任务...")
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
            if result["intent"] == "unknown" and result.get("confidence", 0) < 0.5:
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
            intent = parse_result["intent"]
            parameters = parse_result["parameters"]

            result = self.task_executor.execute_task(intent, parameters)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"执行任务时出错: {str(e)}",
                "data": None,
            }

    def display_parse_result(self, parse_result: Dict[str, Any]):
        """
        显示解析结果

        Args:
            parse_result: 解析结果
        """
        intent = parse_result["intent"]
        intent_desc = self.nlu_engine.get_intent_description(intent)
        confidence = parse_result.get("confidence", 0)

        print(f"\n{Fore.GREEN}✓ 识别意图: {intent_desc} (置信度: {confidence:.2f})")

        if parse_result["parameters"]:
            print(f"{Fore.YELLOW}  参数:")
            for key, value in parse_result["parameters"].items():
                if isinstance(value, list):
                    print(
                        f"{Fore.YELLOW}    - {key}: {', '.join(str(v) for v in value)}"
                    )
                else:
                    print(f"{Fore.YELLOW}    - {key}: {value}")
        print()

    def display_result(self, result: Dict[str, Any]):
        """
        显示执行结果

        Args:
            result: 执行结果
        """
        print(f"\n{Fore.CYAN}{'=' * 70}")

        if result["success"]:
            print(f"{Fore.GREEN}✓ {result['message']}")

            # 显示详细数据
            if result["data"]:
                self.display_result_data(result["data"])
        else:
            print(f"{Fore.RED}✗ {result['message']}")

        print(f"{Fore.CYAN}{'=' * 70}\n")

    def display_result_data(self, data: Dict[str, Any]):
        """
        显示结果数据

        Args:
            data: 结果数据
        """
        # 特殊处理邮件列表
        if "emails" in data:
            print(f"\n{Fore.YELLOW}邮件列表:")
            for email in data["emails"]:
                index = email.get("index", "?")
                subject = email.get("subject", "无主题")
                from_name = email.get("from_name", "")
                from_addr = email.get("from", "")
                date = email.get("date", "")

                print(f"{Fore.CYAN}  [{index}] {Fore.WHITE}{subject}")
                print(f"      {Fore.YELLOW}发件人: {from_name} <{from_addr}>")
                print(f"      {Fore.YELLOW}日期: {date}")
                print()

        # 特殊处理批量摘要
        elif "summaries" in data:
            print(f"\n{Fore.YELLOW}邮件摘要:")
            for summary_item in data["summaries"]:
                index = summary_item.get("index", "?")
                subject = summary_item.get("subject", "无主题")
                summary = summary_item.get("summary", "无摘要")

                print(f"{Fore.CYAN}  [{index}] {Fore.WHITE}{subject}")
                print(f"      {Fore.GREEN}摘要: {summary}")
                print()

        # 特殊处理批量操作结果
        elif "results" in data and isinstance(data["results"], list):
            total = data.get("total", 0)
            success = data.get(
                "archived",
                data.get(
                    "deleted",
                    data.get(
                        "forwarded", data.get("success_count", data.get("marked", 0))
                    ),
                ),
            )
            failed = data.get("failed", data.get("failed_count", 0))

            print(f"\n{Fore.YELLOW}批量操作统计:")
            print(f"  {Fore.CYAN}总数: {total}")
            print(f"  {Fore.GREEN}成功: {success}")
            print(f"  {Fore.RED}失败: {failed}")

            # 显示详细结果（只显示失败的）
            failed_items = [
                r
                for r in data["results"]
                if r.get("status")
                not in [
                    "success",
                    "archived",
                    "deleted",
                    "forwarded",
                    "marked_read",
                    "marked_unread",
                ]
            ]
            if failed_items:
                print(f"\n{Fore.RED}失败项目:")
                for item in failed_items:
                    if "subject" in item:
                        print(
                            f"  {Fore.YELLOW}• {item.get('subject', '未知')}: {item.get('status', '未知错误')}"
                        )
                    elif "recipient" in item:
                        print(
                            f"  {Fore.YELLOW}• {item.get('recipient', '未知')}: {item.get('status', '未知错误')}"
                        )

        # 特殊处理优先级分析
        elif "priority_analysis" in data:
            analysis = data["priority_analysis"]
            print(f"\n{Fore.YELLOW}优先级分析:")
            print(f"  {Fore.CYAN}优先级: {analysis.get('priority', '未知')}")
            print(f"  {Fore.CYAN}紧急程度: {analysis.get('urgency', '未知')}")
            print(
                f"  {Fore.CYAN}是否重要: {'是' if analysis.get('is_important') else '否'}"
            )
            print(f"  {Fore.CYAN}建议操作: {analysis.get('suggested_action', '无')}")
            print(f"  {Fore.YELLOW}理由: {analysis.get('reason', '无')}")

        # 特殊处理回复内容
        elif "reply_content" in data:
            print(f"\n{Fore.YELLOW}生成的回复:")
            print(f"{Fore.WHITE}{data['reply_content']}")

        # 特殊处理摘要
        elif "summary" in data:
            print(f"\n{Fore.YELLOW}邮件摘要:")
            print(f"{Fore.WHITE}{data['summary']}")

        # 通用数据显示
        else:
            print(f"\n{Fore.YELLOW}详细信息:")
            for key, value in data.items():
                if key not in [
                    "emails",
                    "summaries",
                    "results",
                    "priority_analysis",
                    "reply_content",
                    "summary",
                ]:
                    if isinstance(value, (dict, list)):
                        print(
                            f"  {Fore.CYAN}{key}: {json.dumps(value, ensure_ascii=False, indent=2)}"
                        )
                    else:
                        print(f"  {Fore.CYAN}{key}: {value}")

    def run(self):
        """运行主循环"""
        while self.running:
            try:
                # 获取用户输入
                user_input = input(f"{Fore.GREEN}>>> {Style.RESET_ALL}")

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

        print(f"{Fore.CYAN}感谢使用智能邮件代理系统！")


def main():
    """主函数"""
    try:
        # 验证配置
        if not Config.validate_config():
            print(f"{Fore.RED}✗ 配置验证失败，请检查配置文件")
            print(f"{Fore.YELLOW}提示: 请在 .env 文件中设置邮箱账户和 API 密钥")
            return

        # 创建并运行代理
        agent = EmailAgent()
        agent.run()

    except Exception as e:
        print(f"{Fore.RED}✗ 系统启动失败: {str(e)}")
        if Config.DEBUG_MODE:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
