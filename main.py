import asyncio
import random
import time

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

@register("recall", "小钊", "自动撤回机器人发送的消息", "1.1.3")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        self.config = config
        self.my_config_utils = MyConfigUtils(config)
        self.command = CommandUtils(self.my_config_utils)
        self.recall_task = []
        try:
            self.seg_random_time = list(map(int, self.config['seg_random_time'].split("," if "," in self.config['seg_random_time'] else "，")))
        except Exception as e:
            logger.info(f"分段回复随机间隔初始化失败:{e}")
            self.seg_random_time = [1,3]
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # @filter.command("test")
    async def test(self, event: AiocqhttpMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        # msg = Plain("Hello!")
        obmsg = [{'type': 'text', 'data': {'text': '您好！有什么我可以帮助您的吗？'}}]
        group_id = event.get_group_id()
        client = event.bot
        await client.send_group_msg(group_id=int(group_id), message=obmsg)
        # yield event.plain_result(msg)

    async def terminate(self):
        for task in self.recall_task:
            task.cancel()
        self.config.save_config()

        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    def _recall_msg(self, client: CQHttp, message_id: int = 1):
        async def recall(_client: CQHttp, _message_id: int = 1):
            """撤回消息"""
            await asyncio.sleep(self.config["recall_time"])
            try:
                if _message_id:
                    await _client.delete_msg(message_id=_message_id)
                    logger.debug(f"已自动撤回消息: {_message_id}")
            except Exception as e:
                logger.error(f"撤回消息失败: {e}")
        # 调用撤回函数撤回消息
        task = asyncio.create_task(recall(client, message_id))
        # 为任务添加一个结束回调函数，用来删除已完成的任务
        task.add_done_callback(self.remove_task)
        # 将任务添加到撤回任务列表内
        self.recall_task.append(task)

    def remove_task(self, task):
        try:
            self.recall_task.remove(task)
        except:
            pass

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        chain = event.get_result().chain
        obmsg = await event._parse_onebot_json(MessageChain(chain=chain))
        """检测到有消息发出时自动调用撤回方法，以实现触发词和发送内容的撤回"""
        # if 如果全局撤回、触发撤回、发送撤回都未开启则直接退出，交由其他插件处理
        if not self.config['send_is_recall'] and not self.config['trigger_is_recall']:
            return
        # if 发送者qq在发送者白名单 or 开启了图片不撤回并且结果里有Image，则退出交由其他插件处理
        if (event.get_sender_id() in self.config["qq_wl"]) or (self.config['image_no_recall_sw'] and 'Image' in str(event.get_result().chain)):
            return
        # 初始化client
        client = event.bot
        # if 开启了全局撤回或 开启了触发撤回则撤回触发机器人的消息
        if self.config['trigger_is_recall']:
            # 获取触发机器人的消息id
            trigger_message_id = int(event.message_obj.message_id)
            # 调用撤回函数撤回消息
            self._recall_msg(client, trigger_message_id)

        # if 开启了全局撤回或 开启了发送撤回则撤回机器人发送的消息
        if self.config['send_is_recall']:
            # 获取原始消息内容
            chain = event.get_result().chain
            logger.info(chain)
            # 将原始内容格式化napcat api对应的格式
            if "Plain" in str(chain) and self.config['seg_send_sw']:
                plain_texts = event.get_result().get_plain_text()
                plain_texts_split = plain_texts.split("\n\n")
                for plain_text in plain_texts_split:
                    obmsg = [{'type': 'text', 'data': {'text': plain_text}}]
                    time.sleep(random.choice(self.seg_random_time))
                    send_result = await self.command.send_msg(client, obmsg, event.get_group_id(), event.get_sender_id())
                    # 获取发送的消息id
                    send_message_id = int(send_result.get("message_id"))
                    self._recall_msg(client, send_message_id)
                chain.clear()
                # 结束事件
                event.stop_event()
                return
            obmsg = await event._parse_onebot_json(MessageChain(chain=chain))
            # 初始化发送的结果
            # if 如果可以获取到group_id则把group_id 赋值给变量，并且进入分支
            send_result = await self.command.send_msg(client, obmsg, event.get_group_id(), event.get_sender_id())
            # 获取发送的消息id
            if send_result:
                send_message_id = int(send_result.get("message_id"))
                self._recall_msg(client,send_message_id)
                # 将原始消息链清空，避免消息被多次发送
                chain.clear()
                # 结束事件
                event.stop_event()

    # 过滤指令recall
    @filter.command("recall")
    async def recall(self, event: AstrMessageEvent):
        res = self.command.recall(event)
        yield event.plain_result(res)

