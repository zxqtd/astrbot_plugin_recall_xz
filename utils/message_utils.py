import textwrap

SW_OPTIONS = ["all", "send", "trigger", "msg_wl", "qq_wl"]
BOOLEANS = ["enable", "disable"]
WL_OPTIONS1 = ["send_wl", "trigger_wl", "qq_wl"]
WL_OPTIONS2 = ["add", "remove"]
STATUS_OPTIONS = ["status", "运行状态"]
TIPS = f"""
命令：
开关类：recall <option> <boolean>
option可选{SW_OPTIONS}
boolean可选{BOOLEANS}

白名单类:recall option1 option2 option3
option1可选{WL_OPTIONS1}
option2可选{WL_OPTIONS2}
option3为白名单内

查询类:recall option
option可选{STATUS_OPTIONS}
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

