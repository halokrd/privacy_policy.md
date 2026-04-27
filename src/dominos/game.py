from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .models import Boneyard, Domino, Player


@dataclass
class MoveResult:
    played: bool
    message: str


class DominosGame:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = Random(seed)
        self.boneyard = Boneyard.double_six(should_shuffle=False)
        self.boneyard.shuffle_with_rng(self.rng)
        self.player = Player(name="Player")
        self.cpu = Player(name="CPU")
        self.table: list[Domino] = []
        self.left_end: int | None = None
        self.right_end: int | None = None
        self.current_turn = "player"
        self.winner: str | None = None
        self.blocked = False
        self._consecutive_passes = 0
        self._deal_initial_hands()
        self._set_opening_tile()

    def _deal_initial_hands(self) -> None:
        for _ in range(7):
            self.player.draw_tile(self.boneyard)
            self.cpu.draw_tile(self.boneyard)

    def _set_opening_tile(self) -> None:
        player_best = self._highest_double(self.player)
        cpu_best = self._highest_double(self.cpu)

        if player_best is None and cpu_best is None:
            return

        if cpu_best is None or (player_best is not None and player_best[1].left >= cpu_best[1].left):
            idx, tile = player_best
            self.player.play_tile(idx)
            self.place_tile(tile, "L")
            self.current_turn = "cpu"
        else:
            idx, tile = cpu_best
            self.cpu.play_tile(idx)
            self.place_tile(tile, "L")
            self.current_turn = "player"

    def _highest_double(self, player: Player) -> tuple[int, Domino] | None:
        doubles = [(i, t) for i, t in enumerate(player.hand) if t.is_double]
        if not doubles:
            return None
        return max(doubles, key=lambda entry: entry[1].left)

    def legal_moves(self, tile: Domino) -> list[str]:
        if self.left_end is None or self.right_end is None:
            return ["L"]
        sides: list[str] = []
        if tile.left == self.left_end or tile.right == self.left_end:
            sides.append("L")
        if tile.left == self.right_end or tile.right == self.right_end:
            sides.append("R")
        return sides

    def legal_move_indexes_for_player(self) -> list[int]:
        return [i for i, tile in enumerate(self.player.hand) if self.can_play(tile)]

    def can_play(self, tile: Domino) -> bool:
        return len(self.legal_moves(tile)) > 0

    def place_tile(self, tile: Domino, side: str) -> Domino:
        side = side.upper()
        if side not in {"L", "R"}:
            raise ValueError("Side must be 'L' or 'R'.")

        if self.left_end is None or self.right_end is None:
            self.left_end, self.right_end = tile.left, tile.right
            self.table = [tile]
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
            self.table.insert(0, placed)
        else:
            if tile.left == self.right_end:
                self.right_end = tile.right
            elif tile.right == self.right_end:
                placed = tile.rotated()
                self.right_end = placed.right
            else:
                raise ValueError("Tile cannot be played on right side.")
            self.table.append(placed)

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

    def player_draw_until_playable(self) -> MoveResult:
        drawn_count = 0
        while not self.player.has_playable_tile(self.left_end, self.right_end):
            tile = self.player.draw_tile(self.boneyard)
            if tile is None:
                self._consecutive_passes += 1
                self.current_turn = "cpu"
                self._check_blocked_game()
                return MoveResult(True, f"No playable tile after {drawn_count} draws; you pass.")
            drawn_count += 1

        return MoveResult(True, f"You drew {drawn_count} tile(s) and now have a playable move.")

    def play_cpu_turn(self) -> MoveResult:
        while True:
            playable = self._cpu_playable_tiles()
            if playable:
                _, tile = max(playable, key=lambda item: (item[1].pip_total, item[1].is_double))
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
        legal = self.legal_moves(tile)
        if "L" in legal:
            return "L"
        return "R"

    def _cpu_playable_tiles(self) -> list[tuple[int, Domino]]:
        return [(i, tile) for i, tile in enumerate(self.cpu.hand) if self.can_play(tile)]

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

    def score_summary(self) -> str:
        return f"Pip totals => Player: {self.player.hand_pip_total()} | CPU: {self.cpu.hand_pip_total()}"
