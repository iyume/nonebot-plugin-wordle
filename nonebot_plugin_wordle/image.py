from itertools import chain
from pathlib import Path
from typing import Callable, Iterable, Literal, Tuple, Union, overload

from PIL import Image, ImageDraw, ImageFont

from .util import im2base64


class Point:
    __slots__ = ("x", "y", "forward_offset")

    def __init__(
        self, x: int, y: int, *, forward_offset: Tuple[int, int] = None
    ) -> None:
        self.x = x
        self.y = y
        self.forward_offset = forward_offset

    @property
    def tuple_(self) -> Tuple[int, int]:
        return (self.x, self.y)

    @property
    def tuplepair(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        if self.forward_offset is None:
            raise RuntimeError
        return (
            (self.x, self.y),
            (self.x + self.forward_offset[0], self.y + self.forward_offset[1]),
        )

    def shift(self, x: int = 0, y: int = 0) -> None:
        self.x += x
        self.y += y

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.x}, {self.y})"


def getbasewordle(tilesize: int = 50) -> Image.Image:
    """Place empty 5 x 6 tile within 5px gap."""
    im = Image.new("RGB", (5 * tilesize + 21, 6 * tilesize + 26), color="#ffffff")
    # additional 1px to right and bottom to suit line weight
    draw = ImageDraw.Draw(im)
    start_xy = Point(0, 0)
    end_xy = Point(tilesize, tilesize)
    for i in range(6):
        for j in range(5):
            draw.rectangle((start_xy.tuple_, end_xy.tuple_), outline="#d3d6da", width=2)
            start_xy.shift(x=55)
            end_xy.shift(x=55)
        start_xy.x = 0
        end_xy.x = 50
        start_xy.shift(y=55)
        end_xy.shift(y=55)
    return im


class IMWordle:
    """Draw wordle in flexible.

    Considering the gap between tiles should be absolute,
    the code is written in size-flexible instead of resize the image.

    Args:
        tilesize: Word tile size in wordle.
    """

    FONT = ImageFont.truetype(
        str(Path(__file__).parent / "assets" / "ClearSans-Regular.ttf")
    )

    words: Iterable[str]
    tilesize: int
    wordle_size: Tuple[int, int]
    sidebar_size: Tuple[int, int]
    im: Image.Image
    imdraw: ImageDraw.ImageDraw

    def __init__(
        self, inputs: Tuple[str, ...], answer: str, tilesize: int = 50
    ) -> None:
        # Don't make the draw session interactive
        self.words = chain.from_iterable(inputs)
        self.answer = answer
        self.tilesize = tilesize
        self.wordle_size = (5 * tilesize + 21, 6 * tilesize + 26)  # Default 271 x 326
        """5 x 6 tile within 5px gap, addition 1px to suit line weight."""
        self.sidebar_size = (
            self.wordle_size[1] - self.wordle_size[0],
            self.wordle_size[1],
        )  # make output square
        self.im = Image.new("RGB", self.wordle_size, color="#ffffff")
        self.imdraw = ImageDraw.Draw(self.im)
        self.current_point = Point(0, 0, forward_offset=(self.tilesize, self.tilesize))

    def add_margin(self) -> None:
        ...

    def draw_tile(self, char: str = None, fill: str = None) -> None:
        if char is None:
            return
        if len(char) != 1:
            raise RuntimeError

    def move(self) -> None:
        ...

    def drawleave(self, move: Callable[[], None]) -> None:
        ...

    @overload
    def draw(self, base64: Literal[False]) -> Image.Image:
        ...

    @overload
    def draw(self, base64: Literal[True] = True) -> str:
        ...

    def draw(self, base64: bool = True) -> Union[Image.Image, str]:
        for word in self.words:
            ...
        if base64:
            return im2base64(self.im)
        return self.im


getbasewordle().save("output.png")
