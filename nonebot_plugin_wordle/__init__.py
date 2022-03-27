__version__ = "0.1.0"

from nonebot import require

# ensure plugins loaded
require("nonebot_plugin_params")

import asyncio
from typing import Awaitable, Callable, Type

from nonebot import get_driver, on_command
from nonebot.adapters import MessageSegment
from nonebot.exception import SkippedException
from nonebot.matcher import Matcher
from nonebot.params import ArgStr, Depends
from nonebot_plugin_params import (
    ONEBOT,
    ImageSegmentMethod,
    allow_adapters,
    is_private_message,
)

from . import deps
from .deps import User
from .image import IMWordle
from .util import generate_share_msg, get_answer, validate_word

wordle: Type[Matcher] = on_command(
    "wordle", rule=allow_adapters((ONEBOT,)) & is_private_message
)


@wordle.handle()
async def _(matcher: Matcher, user: User = Depends(deps.get_current_user)) -> None:
    if user.finished or user.wins:
        await matcher.finish("您已完成今日 Wordle")
    if user.recv_words:
        await matcher.send("已恢复会话，输入单词继续游戏")
        raise SkippedException
    await matcher.send("输入五字单词开始游戏")


@wordle.got("word")
async def _(
    matcher: Matcher,
    word: str = ArgStr(),
    get_image_segment: Callable[..., Awaitable[MessageSegment]] = ImageSegmentMethod(),
    user: User = Depends(deps.get_current_user),
) -> None:
    if len(word) != 5 or not word.isalpha():
        await matcher.reject("输入五字单词")
    elif not validate_word(word):
        await matcher.reject("单词不合法")
    user.recv_words.append(word)
    img = await get_image_segment(IMWordle().draw(user.recv_words))
    await matcher.send(img)
    await asyncio.sleep(0.5)
    if user.wins:
        await matcher.send("您已胜利")
        await matcher.finish(generate_share_msg(user.recv_words))
    if not user.finished:
        await matcher.reject()
    else:
        await matcher.finish(f"全部猜错啦~ 答案是: {get_answer()}")


default_start = list(get_driver().config.command_start)[0]
wordle.__help_name__ = "wordle"  # type: ignore
wordle.__help_info__ = f"{default_start}wordle  # 开始今日的 Wordle 游戏"  # type: ignore
