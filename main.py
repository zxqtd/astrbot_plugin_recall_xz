import asyncio

from aiocqhttp import CQHttp
from astrbot.core.message.components import Plain, Image, Nodes, At, Node, ComponentType

from astrbot.api.event import filter, AstrMessageEvent
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

@register("recall", "小钊", "自动撤回机器人发送的消息", "1.2.0")
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

    def convert_to_cqcode(self, content_list):
        """将消息段数组转换为 CQ 码字符串"""
        cqcode_parts = []
        for segment in content_list:
            msg_type = segment.get("type")
            data = segment.get("data", {})

            if msg_type == "text":
                # 转义特殊字符
                text = data.get("text", "")
                text = text.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
                cqcode_parts.append(text)

            elif msg_type == "image":
                file_url_a = data.get("file", "")
                file_url = data.get("file", "")
                if file_url_a.startswith("file://"):
                    file_url = self.get_file_b64(file_url_a)
                cqcode_parts.append(f"[CQ:image,file={file_url}]")

            elif msg_type == "at":
                qq = data.get("qq", "")
                cqcode_parts.append(f"[CQ:at,qq={qq}]")

            # 其他类型可以继续添加...

        return "".join(cqcode_parts)

    def build_forward_node(self, content_list):
        return {
            "type": "node",
            "data": {
                "user_id": str(content_list["user_id"]),  # 注意：NapCat 可能用 user_id 而不是 id
                "nickname": content_list["nickname"],
                "content": self.convert_to_cqcode(content_list["content"])
            }
        }

    def get_file_b64(self, file_path):
        if file_path.startswith('file://'):
            file_path = file_path[7:]

            # 将连续多个斜杠替换为单个斜杠
        file_path = re.sub(r'/+', '/', file_path)
        with open(file_path, "rb") as image_file:
            # 读取图片二进制数据并进行Base64编码
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")
        return "base64://"+base64_string

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

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AiocqhttpMessageEvent):
        chains = event.get_result().chain
        """检测到有消息发出时自动调用撤回方法，以实现触发词和发送内容的撤回"""
        # if 如果全局撤回、触发撤回、发送撤回都未开启则直接退出，交由其他插件处理
        if not self.config['send_is_recall'] and not self.config['trigger_is_recall']:
            return
        # if 发送者qq在发送者白名单 or 开启了图片不撤回并且消息链里有Image，则退出交由其他插件处理
        if (
                (event.get_sender_id() in self.config["qq_wl"]) or
                (self.config['image_no_recall_sw'] and any([isinstance(chain, Image) for chain in chains]))
        ):
            return
        for trigger_wl in self.config["trigger_wl"]:
            if trigger_wl in event.message_obj.message_str:
                return
        for send_wl in self.config["send_wl"]:
            print(send_wl,event.get_result().get_plain_text())
            print(send_wl in event.get_result().get_plain_text())
            if send_wl in event.get_result().get_plain_text():
                return
        # if 发送的消息是Node（即合并消息）则推出交由其他插件处理
        # 初始化client
        client = event.bot
        # TODO 合并消息自动撤回
        if isinstance(chains[0], Nodes) or isinstance(chains[0], Node):
            obmsg = []
            chains_dic = chains[0].dict()
            nodes = chains_dic["nodes"] if "nodes" in chains_dic else [chains_dic]
            for node in nodes:
                dict = {
                    "nickname":node["name"],
                    "user_id": node["uin"],
                    "id": node["uin"],
                    "content": []
                }
                for content in node["content"]:
                    if content["type"] == "Image":
                        dic = {"type": "image", "data": {"file": content["file"]}}
                        dict["content"].append(dic)
                    if content["type"] == "At":
                        dic = {"type": "At", "data": {"qq": content["qq"]}}
                        dict["content"].append(dic)
                    if content["type"] == "Plain":
                        dic = {"type": "text", "data": {"text": content["text"]}}
                        dict["content"].append(dic)
                obmsg.append(dict)
            obmsg_old = [
                self.build_forward_node(content)
                for content in obmsg
            ]
            obmsg_new = {"type":"Nodes", "data":obmsg_old}
            send_result = await self.command.send_msg(client, obmsg_new, event.get_group_id(), event.get_sender_id())
            # 获取发送的消息id
            if send_result:
                send_message_id = int(send_result.get("message_id"))
                self._recall_msg(client, send_message_id)
                # 将原始消息链清空，避免消息被多次发送
                chains.clear()
                # 结束事件
                event.stop_event()
                return

        # if 开启了触发撤回则撤回触发机器人的消息
        if self.config['trigger_is_recall']:
            # 获取触发机器人的消息id
            trigger_message_id = int(event.message_obj.message_id)
            # 调用撤回函数撤回消息
            self._recall_msg(client, trigger_message_id)

        # if 开启了全局撤回或 开启了发送撤回则撤回机器人发送的消息
        if self.config['send_is_recall']:
            # 获取原始消息内容
            obmsg = {"type":"text", "data":[]}
            for chain in chains:
                if isinstance(chain, Image):
                    dic = {"type":"image","data":{"file":self.get_file_b64(chain.dict()["file"])}}
                    obmsg["data"].append(dic)
                elif isinstance(chain, At):
                    dic = {"type":"at","data":{"qq":chain.dict()["qq"]}}
                    obmsg["data"].append(dic)
                elif isinstance(chain, Plain):
                    dic = {"type":"text","data":{"text":chain.dict()["text"]}}
                    obmsg["data"].append(dic)

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

