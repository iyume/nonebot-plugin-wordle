from datetime import datetime
from functools import lru_cache
from io import BytesIO

from PIL import Image


def im2bytes(im: Image.Image, format: str = "PNG") -> bytes:
    """Returns bytes of image."""
    buffer = BytesIO()
    im.save(buffer, format=format)
    return buffer.getvalue()


@lru_cache(maxsize=1)
def _get_answer(index: int) -> str:
    from .consts import Ma

    return Ma[index]


def get_answer() -> str:
    """Get today's wordle game answer."""
    return _get_answer((datetime.now() - datetime(2021, 6, 19)).days)
