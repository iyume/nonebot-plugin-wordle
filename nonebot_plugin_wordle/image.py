import itertools
from pathlib import Path
from typing import (
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from PIL import Image, ImageDraw, ImageFont

from .util import im2base64

T = TypeVar("T")

FONT_NAME = str(Path(__file__).parent / "assets" / "ClearSans-Bold.ttf")

clearsans_bold_13 = ImageFont.truetype(FONT_NAME, 13)
clearsans_bold_16 = ImageFont.truetype(FONT_NAME, 16)
clearsans_bold_32 = ImageFont.truetype(FONT_NAME, 32)


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
    def from_iterable(cls, object: Iterable[Iterable[T]]) -> "NDArray[T]":
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
    def flat(self) -> Iterable[T]:
        yield from self.data

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

    def append(self, other: Union["NDArray[T]", Iterable[Iterable[T]]]) -> None:
        if not isinstance(other, NDArray):
            other = NDArray.from_iterable(other)
        if self.shape[1] != other.shape[1]:
            raise ValueError("append 2D array with different column length")
        self.data.append(*other.data)
        self.reshape(self.shape[0] + other.shape[0], self.shape[1])

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
    def __getitem__(self, __k: Tuple[slice, slice]) -> "NDArray[T]":
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
    ) -> Union[T, List[T], "NDArray[T]"]:
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


class IMWordle:
    """Draw wordle in flexible.

    Considering the gap between tiles should be absolute,
    the code is written in size-flexible instead of resize the image.

    Args:
        tilesize: word tile size in wordle.
    """

    answer: str
    tilesize: int
    current_gameboard: Optional[Image.Image]
    current_keyboard: Optional[Image.Image]

    def __init__(self, answer: str, *, tilesize: int = 62) -> None:
        self.answer = answer
        self.tilesize = tilesize
        self.current_gameboard = None
        self.current_keyboard = None

    def get_tiles(self, words: Iterable[Union[str, None]]) -> Iterable[Image.Image]:
        imempty = Image.new("RGB", (self.tilesize, self.tilesize), color="white")
        ImageDraw.Draw(imempty).rectangle(
            ((0, 0), (self.tilesize - 1, self.tilesize - 1)), outline="#d3d6da", width=2
        )
        iter_alpha = iter(words)
        index = 0
        while True:
            try:
                alpha = next(iter_alpha)
                alpha_val = self.answer[index % 5]
                index += 1
            except StopIteration:
                return
            else:
                if alpha is None or alpha == "0":
                    yield imempty
                    continue
                im = Image.new("RGB", (self.tilesize, self.tilesize), color="white")
                imdraw = ImageDraw.Draw(im)
                if alpha == alpha_val:
                    fill = "#6aaa64"
                elif alpha in self.answer:
                    fill = "#c9b458"
                else:
                    fill = "#787c7e"
                imdraw.rectangle(
                    ((0, 0), (self.tilesize - 1, self.tilesize - 1)),
                    fill=fill,
                )
                # alpha is upper, so not need to calculate its true height
                # just give anchor "mm"
                imdraw.text(
                    (self.tilesize / 2, self.tilesize / 2),
                    alpha.upper(),
                    font=clearsans_bold_32,
                    anchor="mm",
                )
                yield im

    @overload
    def draw(self, words: List[str], base64: Literal[False]) -> Image.Image:
        ...

    @overload
    def draw(self, words: List[str], base64: Literal[True] = True) -> str:
        ...

    def draw(self, words: List[str], base64: bool = True) -> Union[Image.Image, str]:
        gameboard = Image.new(
            "RGB", (5 * self.tilesize + 20, 6 * self.tilesize + 25), color="white"
        )
        alpha_arr = NDArray.from_iterable(words)
        for index, im in enumerate(
            self.get_tiles(
                itertools.chain(
                    alpha_arr.flat, itertools.repeat(None, 30 - alpha_arr.size)
                )
            )
        ):
            x, y = index % 5, index // 5
            gameboard.paste(im, (x * (self.tilesize + 5), y * (self.tilesize + 5)))
        keyboard = Image.new("RGB", (484, 190))
        for word in words:
            ...
        # Combine and add margin
        if base64:
            return im2base64(gameboard)
        return gameboard


painter = IMWordle("world")
painter.draw(["alice", "would"], base64=False).save("debug.png")
