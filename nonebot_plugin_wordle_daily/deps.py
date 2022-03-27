from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from nonebot.adapters import Event
from nonebot.matcher import Matcher

from .util import get_answer


@dataclass
class User:
    user_id: str
    recv_words: List[str]
    date: date

    @property
    def finished(self) -> bool:
        return len(self.recv_words) >= 6

    @property
    def wins(self) -> bool:
        if not self.recv_words:
            return False
        return self.recv_words[-1] == get_answer()


users: Dict[str, User] = {}
# simple database
# or OnFocus


async def get_current_user(matcher: Matcher, event: Event) -> User:
    user_id = event.get_user_id()
    # implicit register
    user = users.setdefault(user_id, User(user_id, [], date.today()))
    if user.date != date.today():
        user.date = date.today()
        user.recv_words.clear()
    return user
