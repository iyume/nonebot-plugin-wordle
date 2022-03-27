from datetime import datetime
from functools import lru_cache
from io import BytesIO
from typing import List

from PIL import Image

from .consts import Ma, Oa


def im2bytes(im: Image.Image, format: str = "PNG") -> bytes:
    """Returns bytes of image."""
    buffer = BytesIO()
    im.save(buffer, format=format)
    return buffer.getvalue()


def _get_answer_index() -> int:
    return (datetime.now() - datetime(2021, 6, 19)).days


@lru_cache(maxsize=1)
def _get_answer(index: int) -> str:
    return Ma[index]


def get_answer() -> str:
    """Get today's wordle game answer."""
    return _get_answer(_get_answer_index())


def validate_word(word: str) -> bool:
    return word in Ma or word in Oa


# Wordle 281 2/6

# 🟨🟨⬜⬜⬜
# 🟩🟩🟩🟩🟩


def _generate_share_msg(word: str) -> str:
    answer = get_answer()
    result: List[str] = []
    for i, alpha in enumerate(word):
        if alpha == answer[i]:
            result.append("🟩")
        elif alpha in answer:
            result.append("🟨")
        else:
            result.append("⬜")
    return "".join(result)


def generate_share_msg(words: List[str]) -> str:
    return "{text}\n\n{board}".format(
        text=f"Wordle {_get_answer_index()} {len(words)}/6",
        board="\n".join(_generate_share_msg(word) for word in words),
    )
