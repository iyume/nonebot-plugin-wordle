import itertools
from pathlib import Path
from typing import (
    Callable,
    Generic,
    Iterable,
    List,
    Literal,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from PIL import Image, ImageDraw, ImageFont

from .util import im2base64

T = TypeVar("T")


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


class NDArray(Generic[T]):
    """Implement 2D array. (for fun ^^)"""

    def __init__(self, object: Iterable[T], shape: Tuple[int, int] = None) -> None:
        self.data = list(object)
        if shape is None:
            shape = (len(self.data), 1)
        if len(self.data) != shape[0] * shape[1]:
            raise ValueError(f"len {len(self.data)} not match the given shape {shape}")
        self._shape = shape

    @classmethod
    def from_iterable(cls, object: Iterable[Iterable[T]]) -> "NDArray":
        # Validation
        data = [list(i) for i in object]
        if data:
            xlen = len(data[0])
            if any(len(i) != xlen for i in data):
                raise ValueError(
                    "creating a 2D array from sequences in different shape"
                )
        return NDArray(
            (x for y in data for x in y), (len(data), len(data[0]) if data else 0)
        )

    @property
    def shape(self) -> Tuple[int, int]:
        return self._shape

    @property
    def size(self) -> int:
        return self._shape[0] * self._shape[1]

    def reshape(self, x: int, y: int) -> None:
        if x * y != self.size:
            raise ValueError(
                f"cannot reshape array of size {self.size} into shape ({x},{y})"
            )
        self._shape = (x, y)

    def aslist(self) -> List[List[T]]:
        lst = iter(self.data)
        return [
            list(itertools.islice(lst, self.shape[1])) for _ in range(self.shape[0])
        ]

    def _create_selector(self, items: Iterable[int]) -> Iterable[bool]:
        items = iter(sorted(items))
        item = 0
        previous_item = -1  # assume previous
        while True:
            try:
                item = next(items)
                if not (0 <= item < self.size):
                    raise ValueError(f"item {item} out of size {self.size}")
                yield from itertools.repeat(
                    False,
                    item - previous_item - 1,
                )
                yield True
                previous_item = item
            except StopIteration:
                yield from itertools.repeat(False, self.size - item - 1)
                break

    def __len__(self) -> int:
        return self.shape[0]

    def __repr__(self) -> str:
        return repr(self.aslist())

    @overload
    def __getitem__(self, __k: int) -> List[T]:
        ...

    @overload
    def __getitem__(self, __k: Tuple[slice, int]) -> List[T]:
        ...

    @overload
    def __getitem__(self, __k: Tuple[int, slice]) -> List[T]:
        ...

    @overload
    def __getitem__(self, __k: Tuple[slice, slice]) -> "NDArray":
        ...

    @overload
    def __getitem__(self, __k: Tuple[int, int]) -> T:
        ...

    def __getitem__(
        self,
        __k: Union[
            int,
            Tuple[slice, int],
            Tuple[int, slice],
            Tuple[slice, slice],
            Tuple[int, int],
        ],
    ) -> Union[T, List[T], "NDArray"]:
        """Return Lists, not array object."""
        if isinstance(__k, int):
            # return self.data[__k].copy()
            if not (0 <= __k < self.shape[0]):
                raise IndexError("2D array index out of range")
            return list(
                itertools.islice(
                    self.data, __k * self.shape[1], (__k + 1) * self.shape[1]
                )
            )
        if not isinstance(__k, tuple):
            raise IndexError(f"2D array index {__k} is invalid")
        k1, k2 = __k
        if isinstance(k1, int):
            # return self.data[k1][k2]
            if not (0 <= k1 < self.shape[0]):
                raise IndexError("2D array index out of range")
            if isinstance(k2, int) and not (0 <= k2 < self.shape[1]):
                raise IndexError("2D array index out of range")
            # not validate for slice
            return list(
                itertools.islice(
                    self.data, k1 * self.shape[1], (k1 + 1) * self.shape[1]
                )
            )[k2]
        elif isinstance(k1, slice):
            # return [i[k2] for i in self.data][k1]
            if isinstance(k2, int):
                if not (0 <= k2 < self.shape[1]):
                    raise IndexError("2D array index out of range")
                return list(
                    itertools.compress(
                        self.data,
                        self._create_selector(
                            x * self.shape[1] + k2 for x in range(self.shape[0])[k1]
                        ),
                    )
                )
            return NDArray(
                itertools.compress(
                    self.data,
                    self._create_selector(
                        x * self.shape[1] + y
                        for x in range(self.shape[0])[k1]
                        for y in range(self.shape[1])[k2]
                    ),
                ),
                shape=(len(range(self.shape[0])[k1]), len(range(self.shape[1])[k2])),
            )
        else:
            raise IndexError(f"2D array index {__k} is invalid")


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
    debug: bool
    im: Image.Image
    imdraw: ImageDraw.ImageDraw

    def __init__(
        self,
        inputs: Tuple[str, ...],
        answer: str,
        tilesize: int = 50,
        debug: bool = True,
    ) -> None:
        # Don't make the draw session interactive
        self.words = itertools.chain.from_iterable(inputs)
        self.answer = answer
        self.tilesize = tilesize
        self.debug = debug
        self.wordle_size = (5 * tilesize + 21, 6 * tilesize + 26)  # Default 271 x 326
        """5 x 6 tile within 5px gap, addition 1px to suit line weight."""
        self.sidebar_size = (
            self.wordle_size[1] - self.wordle_size[0],
            self.wordle_size[1],
        )  # make output square
        self.im = Image.new("RGB", self.wordle_size, color="#ffffff")
        self.imdraw = ImageDraw.Draw(self.im)
        self.current_point = Point(0, 0, forward_offset=(self.tilesize, self.tilesize))

    def _draw(self, char: str = None, fill: str = None) -> None:
        if char is None:
            return
        if self.debug:
            self.im.save("debug.png")
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
        # Combine and add margin
        if base64:
            return im2base64(self.im)
        return self.im
