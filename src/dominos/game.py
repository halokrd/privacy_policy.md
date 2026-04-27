from __future__ import annotations

from dataclasses import dataclass

from .models import Boneyard, Domino, Player


@dataclass
class MoveResult:
    played: bool
    message: str


class DominosGame:
    def __init__(self) -> None:
        self.boneyard = Boneyard.double_six(should_shuffle=True)
        self.player = Player(name="Player")
        self.cpu = Player(name="CPU")
        self.left_end: int | None = None
        self.right_end: int | None = None
        self.current_turn = "player"
        self.winner: str | None = None
        self.blocked = False
        self._consecutive_passes = 0
        self._deal_initial_hands()

    def _deal_initial_hands(self) -> None:
        for _ in range(7):
            self.player.draw_tile(self.boneyard)
            self.cpu.draw_tile(self.boneyard)

    def can_play(self, tile: Domino) -> bool:
        if self.left_end is None or self.right_end is None:
            return True
        return tile.is_playable(self.left_end, self.right_end)

    def place_tile(self, tile: Domino, side: str) -> Domino:
        side = side.upper()
        if side not in {"L", "R"}:
            raise ValueError("Side must be 'L' or 'R'.")

        if self.left_end is None or self.right_end is None:
            self.left_end, self.right_end = tile.left, tile.right
            self._consecutive_passes = 0
            return tile

        placed = tile
        if side == "L":
            if tile.right == self.left_end:
                self.left_end = tile.left
            elif tile.left == self.left_end:
                placed = tile.rotated()
                self.left_end = placed.left
            else:
                raise ValueError("Tile cannot be played on left side.")
        else:
            if tile.left == self.right_end:
                self.right_end = tile.right
            elif tile.right == self.right_end:
                placed = tile.rotated()
                self.right_end = placed.right
            else:
                raise ValueError("Tile cannot be played on right side.")

        self._consecutive_passes = 0
        return placed

    def play_player_turn(self, index: int, side: str) -> MoveResult:
        try:
            tile = self.player.hand[index]
        except IndexError:
            return MoveResult(False, "Invalid index.")

        if not self.can_play(tile):
            return MoveResult(False, "Selected tile is not playable.")

        tile = self.player.play_tile(index)
        try:
            placed = self.place_tile(tile, side)
        except ValueError as exc:
            self.player.hand.insert(index, tile)
            return MoveResult(False, str(exc))

        self._check_winner()
        if not self.winner:
            self.current_turn = "cpu"
        return MoveResult(True, f"You played [{placed.left}|{placed.right}] on {side.upper()}.")

    def player_draw_or_pass(self) -> MoveResult:
        tile = self.player.draw_tile(self.boneyard)
        if tile:
            return MoveResult(True, f"You drew [{tile.left}|{tile.right}].")

        self._consecutive_passes += 1
        self.current_turn = "cpu"
        self._check_blocked_game()
        return MoveResult(True, "Boneyard is empty. You pass.")

    def play_cpu_turn(self) -> MoveResult:
        while True:
            playable = self._cpu_playable_tiles()
            if playable:
                _, tile = max(playable, key=lambda item: item[1].pip_total)
                idx = self.cpu.hand.index(tile)
                chosen_side = self._pick_side_for_tile(tile)
                tile = self.cpu.play_tile(idx)
                placed = self.place_tile(tile, chosen_side)
                self._check_winner()
                if not self.winner:
                    self.current_turn = "player"
                return MoveResult(True, f"CPU played [{placed.left}|{placed.right}] on {chosen_side}.")

            drawn = self.cpu.draw_tile(self.boneyard)
            if drawn is None:
                self._consecutive_passes += 1
                self.current_turn = "player"
                self._check_blocked_game()
                return MoveResult(True, "CPU passes (no playable tile and boneyard empty).")

    def _pick_side_for_tile(self, tile: Domino) -> str:
        if self.left_end is None or self.right_end is None:
            return "L"
        if tile.left == self.left_end or tile.right == self.left_end:
            return "L"
        return "R"

    def _cpu_playable_tiles(self) -> list[tuple[int, Domino]]:
        if self.left_end is None or self.right_end is None:
            return list(enumerate(self.cpu.hand))
        return [
            (i, tile)
            for i, tile in enumerate(self.cpu.hand)
            if tile.is_playable(self.left_end, self.right_end)
        ]

    def _check_winner(self) -> None:
        if not self.player.hand:
            self.winner = "player"
        elif not self.cpu.hand:
            self.winner = "cpu"

    def _check_blocked_game(self) -> None:
        if self._consecutive_passes < 2 or len(self.boneyard) > 0:
            return
        player_blocked = not self.player.has_playable_tile(self.left_end, self.right_end)
        cpu_blocked = not self.cpu.has_playable_tile(self.left_end, self.right_end)
        if player_blocked and cpu_blocked:
            self.blocked = True
            player_score = self.player.hand_pip_total()
            cpu_score = self.cpu.hand_pip_total()
            if player_score < cpu_score:
                self.winner = "player"
            elif cpu_score < player_score:
                self.winner = "cpu"
            else:
                self.winner = "draw"

    def game_over(self) -> bool:
        return self.winner is not None

    def table_state(self) -> str:
        if self.left_end is None or self.right_end is None:
            return "Table is empty."
        return f"Table ends: L={self.left_end}, R={self.right_end}"
