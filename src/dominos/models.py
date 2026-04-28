from __future__ import annotations

from dataclasses import dataclass, field
from random import Random, shuffle


@dataclass(frozen=True)
class Domino:
    left: int
    right: int

    def __post_init__(self) -> None:
        if self.left < 0 or self.right < 0:
            raise ValueError("Domino pip values must be non-negative.")

    def is_playable(self, left_end: int, right_end: int) -> bool:
        return self.left in (left_end, right_end) or self.right in (left_end, right_end)

    def rotated(self) -> "Domino":
        return Domino(self.right, self.left)

    @property
    def pip_total(self) -> int:
        return self.left + self.right

    @property
    def is_double(self) -> bool:
        return self.left == self.right


@dataclass
class Boneyard:
    tiles: list[Domino] = field(default_factory=list)

    @classmethod
    def generate(cls, max_pip: int = 6, should_shuffle: bool = True) -> "Boneyard":
        if max_pip < 0:
            raise ValueError("max_pip must be non-negative.")
        tiles = [Domino(left, right) for left in range(max_pip + 1) for right in range(left, max_pip + 1)]
        if should_shuffle:
            shuffle(tiles)
        return cls(tiles)

    @classmethod
    def double_six(cls, should_shuffle: bool = True) -> "Boneyard":
        return cls.generate(max_pip=6, should_shuffle=should_shuffle)

    def shuffle_with_rng(self, rng: Random) -> None:
        rng.shuffle(self.tiles)

    def draw(self) -> Domino | None:
        if not self.tiles:
            return None
        return self.tiles.pop()

    def __len__(self) -> int:
        return len(self.tiles)


@dataclass
class Player:
    name: str
    hand: list[Domino] = field(default_factory=list)

    def draw_tile(self, boneyard: Boneyard) -> Domino | None:
        tile = boneyard.draw()
        if tile is not None:
            self.hand.append(tile)
        return tile

    def play_tile(self, index: int) -> Domino:
        if index < 0 or index >= len(self.hand):
            raise IndexError("Tile index out of range.")
        return self.hand.pop(index)

    def has_playable_tile(self, left_end: int | None, right_end: int | None) -> bool:
        if left_end is None or right_end is None:
            return bool(self.hand)
        return any(tile.is_playable(left_end, right_end) for tile in self.hand)

    def hand_pip_total(self) -> int:
        return sum(tile.pip_total for tile in self.hand)
