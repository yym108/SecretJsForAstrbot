import subprocess
import shlex
import os # 导入 os 模块
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.event.filter import event_message_type, EventMessageType

@register("NodeRunner", "user_custom", "通过QQ消息直接执行Node.js命令", "1.1", "")
class NodeRunnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent) -> MessageEventResult:
        msg_obj = event.message_obj
        text = msg_obj.message_str or ""
        command_prefix = ".node "

        if text.strip() == ".nodehelp":
            # ... (帮助信息不变) ...
            help_message = (
                "Node.js 命令执行器 (v1.1)\n\n"
                "用法：\n"
                ".node <脚本文件路径> [参数...]\n\n"
                "示例：\n"
                ".node E:/path/to/index.js 08:30"
            )
            yield event.plain_result(help_message)
            return

        if text.startswith(command_prefix):
            command_content = text[len(command_prefix):].strip()
            if not command_content:
                yield event.plain_result("请输入要执行的命令。")
                return

            try:
                command_args = shlex.split(command_content)

                # --- 核心修改：设置工作目录 ---
                # 第一个参数应该是脚本的路径
                script_path = command_args[0]

                # 检查脚本文件是否存在
                if not os.path.exists(script_path):
                    yield event.plain_result(f"❌ 错误：找不到脚本文件 '{script_path}'。")
                    return

                # 获取脚本所在的目录作为工作目录 (cwd)
                script_directory = os.path.dirname(script_path)
                # --- 修改结束 ---

                command_to_run = ["node"] + command_args

                result = subprocess.run(
                    command_to_run,
                    # --- 核心修改：应用工作目录 ---
                    cwd=script_directory,
                    # --- 修改结束 ---
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=120 # 考虑到脚本可能需要运行一段时间，可以适当延长超时
                )

                output = ""
                if result.stdout:
                    output += f"--- 标准输出 (stdout) ---\n{result.stdout}\n"
                if result.stderr:
                    output += f"--- 错误输出 (stderr) ---\n{result.stderr}\n"

                if not output:
                    output = "✅ 命令执行完毕，但没有任何输出。"

                yield event.plain_result(output.strip())

            except FileNotFoundError:
                yield event.plain_result("❌ 错误：未找到 'node' 命令。")
            except subprocess.TimeoutExpired:
                yield event.plain_result("❌ 错误：命令执行超时（超过120秒）。")
            except Exception as e:
                yield event.plain_result(f"❌ 执行命令时发生未知错误：\n{str(e)}")

            return