from astrbot.core import logger

from astrbot.core.platform import AstrMessageEvent
from .message_utils import MessageUtils
import os
import platform
import time

class CommandUtils:
    def __init__(self, my_config):
        self.my_config = my_config
        self.message = MessageUtils()

    def _get_uptime(self):
        system = platform.system()
        if system == 'Linux':
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
            except FileNotFoundError:
                return "获取失败"
        elif system == 'Windows':
            try:
                import ctypes
                uptime = ctypes.windll.kernel32.GetTickCount()
                uptime_seconds = uptime / 1000.0
            except ImportError:
                return "获取失败"
        else:
            return "获取失败"

            # 转换为可读格式
        days = uptime_seconds // (24 * 3600)
        hours = (uptime_seconds % (24 * 3600)) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60

        return f"{int(days)}天{int(hours)}小时{int(minutes)}分{int(seconds)}秒"

    def recall(self, event: AstrMessageEvent):
        if not event.is_admin():
            return '我才不听你的呢'
        try:
            arr = event.get_message_str().split(" ")
            # status
            if len(arr) == 2:
                # 运行状态
                if arr[1] not in self.message.status_options():
                    return self.message.tips()
                config = self.my_config.get_all_config()
                msg = f"触发撤回：{config[1]}\n发送撤回：{config[0]}\n消息白名单检测:{config[4]}\n触发者白名单检测：{config[6]}\n不撤回图片：{config[8]}\n分段回复：{config[9]}\n触发消息白名单列表：{config[3]}\n发送消息白名单检测：{config[2]}\n触发者白名单列表:{config[5]}\n消息撤回时间:{config[7]}\n分段随机发送间隔:{config[10]}\n服务器开机时间：{self._get_uptime()}"
                return msg
            # 开关类
            elif len(arr) == 3:
                command, option, boolean = arr
                if boolean in self.message.booleans() and option in self.message.sw_options():
                    if option == "all":
                        status = self.my_config.sw(boolean, "send") and self.my_config.sw(boolean, "trigger")
                    else:
                        status = self.my_config.sw(boolean, option)
                    if status:
                        status = self.message.booleans().get(boolean)
                        msg = f"已{status}{self.message.sw_options().get(option)}"
                        return msg
                    else:
                        return "操作失败，详情原因请查看日志"
                elif option in self.message.string_options():
                    if len(boolean.split(",")) == 2 or len(boolean.split("，")) == 2:
                        status = self.my_config.set_string(option, boolean)
                    else:
                        return "值出现异常"
                    if status:
                        msg = f"已设置{option}为{boolean}"
                        return msg
                    else:
                        return "操作失败，详情原因请查看日志"
                else:
                    return self.message.tips()
            elif len(arr) == 4:
                status = False
                # recall qq_wl add 1
                command, option1, option2, option3 = arr
                if option1 not in self.message.wl_options1() or option2 not in self.message.wl_options2():
                    return self.message.tips()
                if option2 == "add":
                    if option3 in self.my_config.get_all_config()[2 if option2 == "send_wl" else (3 if option2 == "trigger_wl" else 5)]:
                        return f"白名单{option2}内存在{option3}"
                    status = self.my_config.wl_add(option1, option3)
                else:
                    if option3 in self.my_config.get_all_config()[2 if option2 == "send_wl" else (3 if option2 == "trigger_wl" else 5)]:
                        status = self.my_config.wl_remove(option1, option3)
                    else:
                        return f"白名单{option2}内无{option3}"

                if status:
                    msg = f"{self.message.wl_options1().get(option1)}:{option3}{self.message.wl_options2().get(option2)}成功"
                    return msg
                else:
                    return "操作失败，详情原因请查看日志"
            else:
                return self.message.tips()
        except Exception as e:
            logger.error(e)
            return self.message.tips()

    async def send_msg(self, client, obmsg, group_id=None, user_id=None):
        send_result = None
        if group_id:
            # 调用napcat的send_group_msg接口发送消息并将结果赋值给send_result
            send_result = await client.send_group_msg(group_id=int(group_id), message=obmsg)
        # elif 如果可以获取到sender_id则把sender_id 赋值给变量，并且进入分支
        elif user_id:
            # 调用napcat的send_private_msg接口发送消息并将结果赋值给send_result
            send_result = await client.send_private_msg(user_id=int(user_id), message=obmsg)
        return send_result

