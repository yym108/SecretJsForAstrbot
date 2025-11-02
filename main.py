import subprocess
import shlex  # 导入 shlex 模块用于安全地分割命令
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import event_message_type, EventMessageType

@register("NodeRunner", "user_custom", "通过QQ消息直接执行Node.js命令", "1.0", "")
class NodeRunnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent) -> MessageEventResult:
        """
        处理执行 Node.js 命令相关的消息。
        """
        msg_obj = event.message_obj
        text = msg_obj.message_str or ""
        command_prefix = ".node "

        # --- 指令帮助 ---
        if text.strip() == ".nodehelp":
            help_message = (
                "Node.js 命令执行器\n\n"
                "用法：\n"
                ".node <文件名> [参数...]\n\n"
                "示例：\n"
                "1. 执行脚本：\n"
                ".node /path/to/your/script.js\n\n"
                "2. 执行脚本并传入参数：\n"
                ".node script.js '参数一' '参数二 with spaces'\n\n"
                "3. 查看 node 版本：\n"
                ".node -v\n\n"
                "⚠️ **严重安全警告** ⚠️\n"
                "此插件允许执行服务器上的任意 Node.js 命令，"
                "具有极高的安全风险。请仅在完全可信的环境中使用，"
                "并确保只有授权用户才能访问此机器人。"
            )
            yield event.plain_result(help_message)
            return

        # --- 执行命令 ---
        if text.startswith(command_prefix):
            # 获取 ".node " 后面的所有内容作为要执行的命令
            command_content = text[len(command_prefix):].strip()

            if not command_content:
                yield event.plain_result("请输入要执行的命令。\n使用 .nodehelp 查看帮助。")
                return

            try:
                # 使用 shlex.split 来正确处理带引号的参数
                command_args = shlex.split(command_content)

                # 准备完整的执行命令
                command_to_run = ["node"] + command_args

                # 执行命令并捕获输出
                # 设置超时时间（例如 60 秒）防止脚本无限运行
                result = subprocess.run(
                    command_to_run,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=60
                )

                # 组合标准输出和标准错误输出
                output = ""
                if result.stdout:
                    output += f"--- 标准输出 (stdout) ---\n{result.stdout}\n"
                if result.stderr:
                    output += f"--- 错误输出 (stderr) ---\n{result.stderr}\n"

                # 如果脚本执行了但没有任何输出
                if not output:
                    output = "✅ 命令执行完毕，但没有任何输出。"

                # 返回完整输出
                yield event.plain_result(output.strip())

            except FileNotFoundError:
                yield event.plain_result("❌ 错误：未找到 'node' 命令。\n请确保 Node.js 已正确安装并配置在系统的 PATH 环境变量中。")
            except subprocess.TimeoutExpired:
                yield event.plain_result("❌ 错误：命令执行超时（超过60秒）。")
            except Exception as e:
                yield event.plain_result(f"❌ 执行命令时发生未知错误：\n{str(e)}")

            return