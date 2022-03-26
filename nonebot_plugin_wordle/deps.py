from dataclasses import dataclass
from typing import Callable, Dict, List, Type, overload

from nonebot.adapters import Adapter, Bot, Event, MessageSegment
from nonebot.exception import AdapterException, FinishedException, SkippedException
from nonebot.matcher import Matcher
from nonebot.params import Depends

from .image import IMWordle


async def _event_name(event: Event) -> str:
    return event.get_event_name()


def EventName() -> str:
    return Depends(_event_name)


async def _get_adapter_name(bot: Bot) -> str:
    return bot.adapter.get_name()


def AdapterName() -> str:
    """获取 Adapter 名字。"""
    return Depends(_get_adapter_name)


def _generic_get_segment_class(event: Event) -> Type[MessageSegment]:
    from importlib import import_module

    adapter_module = import_module("..", event.__class__.__module__)
    try:
        return adapter_module.__dict__["MessageSegment"]
    except KeyError:
        return MessageSegment


async def _get_segment_class(
    event: Event, adapter_name: str = AdapterName()
) -> Type[MessageSegment]:
    if adapter_name == "Onebot V11":
        from nonebot.adapters.onebot.v11 import MessageSegment

        return MessageSegment
    elif adapter_name == "":
        ...
    return _generic_get_segment_class(event)


def MessageSegmentClass() -> Type[MessageSegment]:
    """获取 Adapter 对应的 MessageSegment 类。"""
    return Depends(_get_segment_class)


async def _get_image_segment(adapter_name: str = AdapterName()) -> MessageSegment:
    ...


def ImageSegmentMethod() -> Callable[[bytes], MessageSegment]:
    """取得 Image Segment 的构造方法。"""
    ...


@dataclass
class Item:
    user_id: str
    recv_words: List[str]


items: Dict[str, Item] = {}
# simple database


async def get_current_user(matcher: Matcher, event: Event) -> IMWordle:
    # implicit register
    raise SkippedException
