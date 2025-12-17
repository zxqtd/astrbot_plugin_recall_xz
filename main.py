import asyncio

from aiocqhttp import CQHttp

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core import AstrBotConfig
from astrbot.api import logger

from .utils.command_utils import CommandUtils
from .utils.my_config_utils import MyConfigUtils

@register("recall", "小钊", "自动撤回机器人发送的消息", "1.1.2")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        self.config = config
        self.my_config_utils = MyConfigUtils(config)
        self.command = CommandUtils(self.my_config_utils)
        self.recall_task = []
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # @filter.command("test")
    async def test(self, event: AstrMessageEvent, a: int, b: int):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!传入的参数a {a},b {b}") # 发送一条纯文本消息

    async def terminate(self):
        for task in self.recall_task:
            task.cancel()
        self.config.save_config()

        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    async def _recall_msg(self, client: CQHttp, message_id: int = 1):
        """撤回消息"""
        await asyncio.sleep(self.config["recall_time"])
        try:
            if message_id:
                await client.delete_msg(message_id=message_id)
                logger.debug(f"已自动撤回消息: {message_id}")
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")

    def remove_task(self, task):
        try:
            self.recall_task.remove(task)
        except:
            pass

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        """检测到有消息发出时自动调用撤回方法，以实现触发词和发送内容的撤回"""
        # if 如果全局撤回、触发撤回、发送撤回都未开启则直接退出，交由其他插件处理
        if not self.config['send_is_recall'] and not self.config['trigger_is_recall']:
            return
        # 初始化client
        client = event.bot
        # if 开启了全局撤回或 开启了触发撤回则撤回触发机器人的消息
        if self.config['trigger_is_recall']:
            # 获取触发机器人的消息id
            trigger_message_id = int(event.message_obj.message_id)
            # 调用撤回函数撤回消息
            task = asyncio.create_task(self._recall_msg(client, trigger_message_id))
            # 为任务添加一个结束回调函数，用来删除已完成的任务
            task.add_done_callback(self.remove_task)
            # 将任务添加到撤回任务列表内
            self.recall_task.append(task)
        # if 开启了全局撤回或 开启了发送撤回则撤回机器人发送的消息
        if self.config['send_is_recall']:
            # 获取原始消息内容
            chain = event.get_result().chain
            # 将原始内容格式化napcat api对应的格式
            obmsg = await event._parse_onebot_json(MessageChain(chain=chain))
            # 初始化发送的结果
            send_result = None
            # if 如果可以获取到group_id则把group_id 赋值给变量，并且进入分支
            if group_id := event.get_group_id():
                # 调用napcat的send_group_msg接口发送消息并将结果赋值给send_result
                send_result = await client.send_group_msg(group_id=int(group_id), message=obmsg)
            # elif 如果可以获取到sender_id则把sender_id 赋值给变量，并且进入分支
            elif user_id := event.get_sender_id():
                # 调用napcat的send_private_msg接口发送消息并将结果赋值给send_result
                send_result = await client.send_private_msg(user_id=int(user_id), message=obmsg)
            # 获取发送的消息id
            send_message_id = int(send_result.get("message_id"))
            # 调用撤回函数撤回消息
            task = asyncio.create_task(self._recall_msg(client, send_message_id))
            # 为任务添加一个结束回调函数，用来删除已完成的任务
            task.add_done_callback(self.remove_task)
            # 将任务添加到撤回任务列表内
            self.recall_task.append(task)
            # 将原始消息链清空，避免消息被多次发送
            chain.clear()
            # 结束事件
            event.stop_event()

    # 过滤指令recall
    @filter.command("recall")
    async def recall(self, event: AstrMessageEvent):
        res = self.command.recall(event)
        yield event.plain_result(res)

