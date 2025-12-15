# AstrBot recall插件
当前版本1.1.1

这是一个astrbot自动撤回机器人发送的消息的插件，支持撤回所有插件发送的消息

This is an AstrBot plugin that automatically withdraws messages sent by the bot, supporting the withdrawal of messages sent by all plugins.

# 适配
目前只测试了astrbot可正常使用，如需适配其他端请发送issue

Currently, only AstrBot has been tested and is working normally. If you need adaptation for other platforms, please send an issue.

# 指令
~~待完善~~

# 功能列表
## 触发撤回
指的是自动撤回触发机器人的消息
## 发送撤回
指的是自动撤回机器人发送的消息
## 全局撤回
指的是自动撤回触发机器人的消息和机器人发送的消息
## 触发白名单
如果消息内包含白名单内的内容则不撤回触发机器人的消息
## 发送白名单
如果消息内包含白名单内的内容则不撤回机器人发送的消息
## 全局白名单
如果消息内包含白名单内的内容则不撤回机器人发送的消息和机器人发送的消息
## 白名单检测开关
如果开关为开时检测白名单，开关为关时不检测
## 全局撤回时间
当白名单校验为通过时自动撤回消息的时间
## 不撤回白名单
基于qq号校验，当qq号存在不撤回白名单时不会撤回发送和触发的消息
## 不撤回白名单开关
当开启时进行qq号白名单校验，反之不校验
