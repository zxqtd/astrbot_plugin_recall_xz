from astrbot.core import AstrBotConfig, logger


class MyConfigUtils:
    def __init__(self, config: AstrBotConfig):
        self.config = config
    
    def sw(self, boolean: str, option: str):
        try:
            _sw = ["msg_wl", "qq_wl", "seg_send", "image_no_recall"]
            boolean = True if boolean == "enable" else False
            if option not in _sw:
                self.config[option + '_is_recall'] = boolean
            else:
                self.config[option + '_sw'] = boolean
            self.config.save_config()
            return True
        except Exception as e:
            logger.error(e)
            return False
    
    def wl_add(self, option1, option3):
        try:
            self.config[option1].append(option3)
            self.config.save_config()
            return True
        except Exception as e:
            logger.error(e)
            return False
    
    def wl_remove(self, option1, option3):
        try:
            self.config[option1].remove(option3)
            self.config.save_config()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def set_string(self,option,option1):
        try:
            self.config[option] = option1
            self.config.save_config()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def get_all_config(self):
        try:
            _sw = ["msg_wl", "qq_wl"]
            config = [
                self.config['send_is_recall'], # 0
                self.config['trigger_is_recall'], # 1
                self.config['send_wl'], # 2
                self.config['trigger_wl'], # 3
                self.config['msg_wl_sw'], # 4
                self.config['qq_wl'], # 5
                self.config['qq_wl_sw'],# 6
                self.config['recall_time'], #7
                self.config['image_no_recall_sw'], # 8
                self.config['seg_send_sw'], # 9
                self.config['seg_random_time'] # 10
            ]
            return config
        except Exception as e:
            logger.error(e)