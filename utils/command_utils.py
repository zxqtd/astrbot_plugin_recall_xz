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
            if len(arr) == 2:
                # 运行状态
                if arr[1] not in self.message.status_options():
                    return self.message.tips()
                config = self.my_config.get_all_config()
                msg = f"触发撤回：{config[1]}\n发送撤回：{config[0]}\n消息白名单检测:{config[4]}\n触发者白名单检测：{config[6]}\n触发消息白名单列表：{config[3]}\n发送消息白名单检测：{config[2]}\n触发者白名单列表:{config[5]}\n消息撤回时间:{config[7]}\n服务器开机时间：{self._get_uptime()}"
                return msg
            elif len(arr) == 3:
                command, option, boolean = arr
                if option not in self.message.sw_options() or boolean not in self.message.booleans():
                    return self.message.tips()
                if option == "all":
                    status = self.my_config.sw(boolean, "send") and self.my_config.sw(boolean, "trigger")
                else:
                    status = self.my_config.sw(boolean, option)
                if status:
                    status = "开启" if boolean == "enable" else "关闭"
                    msg = f"已{status}撤回发送消息" if option == "send" else (
                        f"已{status}撤回所有" if option == "all" else f"已{status}撤回触发消息")
                    return msg
                else:
                    return "操作失败，详情原因请查看日志"
            elif len(arr) == 4:
                status = False
                command, option1, option2, option3 = arr
                if option1 not in self.message.wl_options1() or option2 not in self.message.wl_options2():
                    return self.message.tips()
                if option2 == "add":
                    status = self.my_config.wl_add(option1, option3)
                else:
                    logger.info(self.my_config.get_all_config()[2 if option2 == "send_wl" else (3 if option2 == "trigger_wl" else 5)])
                    if option1 in self.my_config.get_all_config()[2 if option2 == "send_wl" else (3 if option2 == "trigger_wl" else 5)]:
                        status = self.my_config.wl_remove(option1, option3)
                    else:
                        return f"白名单{option2}内无{option3}"

                if status:
                    cz = "新增" if option2 == "add" else "删除"
                    msg = f"发送白名单:{option3}{cz}成功" if option1 == "send_wl" else (f"触发白名单:{option3}{cz}成功" if option1 == "trigger_wl" else f"qq白名单:{option3}{cz}成功")
                    return msg
                else:
                    return "操作失败，详情原因请查看日志"
            else:
                return self.message.tips()
        except Exception as e:
            logger.error(e)
            return self.message.tips()
