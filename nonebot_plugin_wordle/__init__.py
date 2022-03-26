__version__ = "0.1.0"

from typing import List, Optional, Type

from nonebot import get_driver, on_command
from nonebot.exception import AdapterException, SkippedException
from nonebot.matcher import Matcher
from nonebot.params import ArgStr, Depends
from nonebot.rule import Rule
from nonebot.typing import T_State

from . import deps

try:
    from nonebot.adapters.onebot.v11 import Bot, MessageSegment
except ImportError:
    pass

from .image import IMWordle
from .util import get_answer

wordle: Optional[Type[Matcher]] = None


async def _checker(event_name: str = deps.EventName()) -> bool:
    """设置只允许私聊消息的 Rule。

    如果你只想在 handler 层面过滤，又想做多平台兼容，可以先定义 handler 函数体，更新了 annotation 后再注册。
    """
    if event_name == "message.private":
        return True
    return False


async def _handle_wordle(matcher: Matcher) -> None:
    try:
        MessageSegment
    except NameError:
        raise AdapterException("no available MessageSegment")
    if not hasattr(MessageSegment, "image"):
        await matcher.finish("当前适配器不支持图片功能，无法开始游戏")
    painter = IMWordle(get_answer())
    await matcher.send(MessageSegment.image(painter.draw([])))
    words: List[str] = []


try:
    from nonebot.adapters.onebot.v11 import PrivateMessageEvent
except ImportError:
    pass
else:
    wordle = on_command("wordle", rule=Rule(_checker))


if wordle is None:
    wordle = on_command("wordle")

lst = []


@wordle.handle()
async def _(matcher: Matcher, board: IMWordle = Depends(deps.get_current_game)) -> None:
    if lst:
        await matcher.send("恢复会话，输入单词继续")
        raise SkippedException
    await matcher.send("输入五字单词开始游戏")


@wordle.got("word")
async def _(matcher: Matcher, word: str = ArgStr()) -> None:
    if len(word) != 5 or not word.isalpha():
        await matcher.reject("输入五字单词")
    lst.append(word)
    await matcher.send(repr(lst))
    await matcher.reject()


default_start = list(get_driver().config.command_start)[0]
wordle.__help_name__ = "wordle"  # type: ignore
wordle.__help_info__ = f"{default_start}wordle  # 开始今日的 Wordle 游戏"  # type: ignore
