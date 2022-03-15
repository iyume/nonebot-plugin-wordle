from typing import Optional

import nonebot
from nonebot.adapters.onebot.v11 import MessageSegment

from . import image
from .consts import Ma, Oa

# add every day notification
wordle = nonebot.on_command("wordle")
