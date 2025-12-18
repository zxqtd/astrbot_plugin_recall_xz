import textwrap

SW_OPTIONS = {"all":"撤回所有", "send":"撤回发送消息", "trigger":"撤回触发消息", "msg_wl":"消息不撤回白名单检测", "qq_wl":"触发者qq白名单检测", "seg_send":"消息分段", "image_no_recall":"图片不撤回"}
BOOLEANS = {"enable":"开启", "disable":"关闭"}
WL_OPTIONS1 = {"send_wl":"发送白名单", "trigger_wl":"触发白名单", "qq_wl":"qq白名单"}
WL_OPTIONS2 = {"add":"新增", "remove":"删除"}
STATUS_OPTIONS = ["status", "运行状态"]
STRING_OPTIONS1 = {"seg_random_time":"分段随机发送间隔"}
TIPS = f"""
命令：
开关类：recall <option> <boolean>
option可选{SW_OPTIONS}
boolean可选{BOOLEANS}
-------------------
白名单类:recall option1 option2 option3
option1可选{WL_OPTIONS1}
option2可选{WL_OPTIONS2}
option3为白名单内
-------------------
查询类:recall option
option可选{STATUS_OPTIONS}
-------------------
其他配置类:recall option1 option2
option1可选{STRING_OPTIONS1}
option2为配置项目
"""

class MessageUtils:
    def __init__(self):
        pass

    def tips(self):
        return TIPS

    def sw_options(self):
        return SW_OPTIONS

    def booleans(self):
        return BOOLEANS

    def wl_options1(self):
        return WL_OPTIONS1

    def wl_options2(self):
        return WL_OPTIONS2

    def status_options(self):
        return STATUS_OPTIONS

    def string_options(self):
        return STRING_OPTIONS1
