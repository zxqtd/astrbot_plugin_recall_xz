import asyncio
import random
import time

import astrbot.api.message_components as Comp

from aiocqhttp import CQHttp
from astrbot.core.message.components import Plain, Image, Nodes, At

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core import AstrBotConfig
from astrbot.api import logger

from .utils.command_utils import CommandUtils
from .utils.my_config_utils import MyConfigUtils

import base64
import re

@register("recall", "小钊", "自动撤回机器人发送的消息", "1.1.5")
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

    def get_file_b64(self, file_path):
        if file_path.startswith('file://'):
            file_path = file_path[7:]

            # 将连续多个斜杠替换为单个斜杠
        file_path = re.sub(r'/+', '/', file_path)
        with open(file_path, "rb") as image_file:
            # 读取图片二进制数据并进行Base64编码
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")
        return base64_string

    # @filter.command("test")
    async def test(self, event: AiocqhttpMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        chain = [
            Comp.At(qq=event.get_sender_id()),  # At 消息发送者
            Comp.Plain("来看这个图："),
            Comp.Image.fromFileSystem("/Users/Zhuanz2/Desktop/AstrBot/data/plugins/astrbot_plugin_mc_admin/data/background_image/-213b827e1001c229.jpg"),  # 从本地文件目录发送图片
            Comp.Plain("这是一个图片。")
        ]
        yield event.chain_result(chain)
        # obmsg = [{'type': 'at', 'data': {'qq': event.get_sender_id()}},{'type': 'text', 'data': {'text': "来看这个图"}},{'type': 'image', 'data': {'file': "base64://"+self.get_file_b64("/Users/Zhuanz2/Desktop/AstrBot/data/plugins/astrbot_plugin_mc_admin/data/background_image/-213b827e1001c229.jpg")}},{'type': 'text', 'data': {'text': "这是一个图片"}}]
        # client = event.bot
        # group_id = event.get_group_id()
        # await client.send_group_msg(group_id=int(group_id), message=obmsg)

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

    # 暂时只适配群聊，aiocqhttp，后续考虑适配其他的
    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        chains = event.get_result().chain
        print(chains)
        """检测到有消息发出时自动调用撤回方法，以实现触发词和发送内容的撤回"""
        # if 如果全局撤回、触发撤回、发送撤回都未开启则直接退出，交由其他插件处理
        if not self.config['send_is_recall'] and not self.config['trigger_is_recall']:
            return
        # if 发送者qq在发送者白名单 or 开启了图片不撤回并且消息链里有Image，则退出交由其他插件处理
        if (event.get_sender_id() in self.config["qq_wl"]) or (self.config['image_no_recall_sw'] and any([isinstance(chain, Image) for chain in chains])):
            return
        # if 发送的消息是Node（即合并消息）则推出交由其他插件处理
        # TODO 合并消息自动撤回
        if isinstance(chains[0], Nodes):
            return
        # 初始化client
        client = event.bot
        # if 开启了触发撤回则撤回触发机器人的消息
        if self.config['trigger_is_recall']:
            # 获取触发机器人的消息id
            trigger_message_id = int(event.message_obj.message_id)
            # 调用撤回函数撤回消息
            self._recall_msg(client, trigger_message_id)

        # if 开启了全局撤回或 开启了发送撤回则撤回机器人发送的消息
        if self.config['send_is_recall']:
            # 获取原始消息内容
            obmsg = []
            for chain in chains:
                if isinstance(chain, Image):
                    dic = {"type":"image","data":{"file":"base64://"+self.get_file_b64(chain.dict()["file"])}}
                    obmsg.append(dic)
                elif isinstance(chain, At):
                    dic = {"type":"at","data":{"qq":chain.dict()["qq"]}}
                    obmsg.append(dic)
                elif isinstance(chain, Plain):
                    dic = {"type":"text","data":{"text":chain.dict()["text"]}}
                    obmsg.append(dic)

            send_result = await self.command.send_msg(client, obmsg, event.get_group_id(), event.get_sender_id())
            # 获取发送的消息id
            if send_result:
                send_message_id = int(send_result.get("message_id"))
                self._recall_msg(client,send_message_id)
                # 将原始消息链清空，避免消息被多次发送
                chains.clear()
                # 结束事件
                event.stop_event()

    # 过滤指令recall
    @filter.command("recall")
    async def recall(self, event: AstrMessageEvent):
        res = self.command.recall(event)
        yield event.plain_result(res)

