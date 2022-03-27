import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()

nonebot.get_driver().register_adapter(Adapter)

nonebot.load_plugin("nonebot_plugin_wordle_daily")


if __name__ == "__main__":
    nonebot.run()
