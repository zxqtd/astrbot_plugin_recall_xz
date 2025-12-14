import asyncio

from aiocqhttp import CQHttp

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core import AstrBotConfig
from astrbot.api import logger

@register("recall", "XiaoZhao", "自动撤回机器人发送的消息", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        self.config = config
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    async def terminate(self):
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

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        """检测到有消息发出时自动调用撤回方法，以实现触发词和发送内容的撤回"""
        if not self.config["is_recall"]:
            return
        trigger_message_id = int(event.message_obj.message_id)
        client = event.bot
        asyncio.create_task(self._recall_msg(client, trigger_message_id))
        chain = event.get_result().chain
        obmsg = await event._parse_onebot_json(MessageChain(chain=chain))

        send_result = None
        if group_id := event.get_group_id():
            send_result = await client.send_group_msg(
                group_id=int(group_id), message=obmsg
            )
        send_message_id = int(send_result.get("message_id"))
        asyncio.create_task(self._recall_msg(client, send_message_id))
        chain.clear()
        event.stop_event()