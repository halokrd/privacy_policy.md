from __future__ import annotations

from dataclasses import dataclass, field
from random import Random, shuffle


@dataclass(frozen=True)
class Domino:
    left: int
    right: int

    def __post_init__(self) -> None:
        if not (0 <= self.left <= 6 and 0 <= self.right <= 6):
            raise ValueError("Domino pip values must be between 0 and 6.")

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
    def double_six(cls, should_shuffle: bool = True) -> "Boneyard":
        tiles = [Domino(left, right) for left in range(7) for right in range(left, 7)]
        if should_shuffle:
            shuffle(tiles)
        return cls(tiles)

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
