from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from random import Random

from .models import Boneyard, Domino, Player


@dataclass
class MoveResult:
    played: bool
    message: str


class DominosGame:
    def __init__(
        self,
        seed: int | None = None,
        *,
        max_pip: int = 6,
        target_score: int = 50,
        round_number: int = 1,
        player_score: int = 0,
        cpu_score: int = 0,
    ) -> None:
        self.seed = seed
        self.rng = Random(seed)
        self.max_pip = max_pip
        self.target_score = target_score
        self.round_number = round_number
        self.player_score = player_score
        self.cpu_score = cpu_score
        self.draw_count_player = 0
        self.draw_count_cpu = 0
        self.move_history: list[str] = []

        self.boneyard = Boneyard.generate(max_pip=max_pip, should_shuffle=False)
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
        deal_size = min(7, (self.max_pip + 1) * (self.max_pip + 2) // 4)
        for _ in range(deal_size):
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
            self.move_history.append(f"Opening: Player [{tile.left}|{tile.right}]")
        else:
            idx, tile = cpu_best
            self.cpu.play_tile(idx)
            self.place_tile(tile, "L")
            self.current_turn = "player"
            self.move_history.append(f"Opening: CPU [{tile.left}|{tile.right}]")

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

        self.move_history.append(f"Player played [{placed.left}|{placed.right}] on {side.upper()}")
        self._check_winner()
        if not self.winner:
            self.current_turn = "cpu"
        return MoveResult(True, f"You played [{placed.left}|{placed.right}] on {side.upper()}.")

    def player_draw_or_pass(self) -> MoveResult:
        tile = self.player.draw_tile(self.boneyard)
        if tile:
            self.draw_count_player += 1
            self.move_history.append(f"Player drew [{tile.left}|{tile.right}]")
            return MoveResult(True, f"You drew [{tile.left}|{tile.right}].")

        self._consecutive_passes += 1
        self.current_turn = "cpu"
        self.move_history.append("Player passed")
        self._check_blocked_game()
        return MoveResult(True, "Boneyard is empty. You pass.")

    def player_draw_until_playable(self) -> MoveResult:
        drawn_count = 0
        while not self.player.has_playable_tile(self.left_end, self.right_end):
            tile = self.player.draw_tile(self.boneyard)
            if tile is None:
                self._consecutive_passes += 1
                self.current_turn = "cpu"
                self.move_history.append("Player auto-pass")
                self._check_blocked_game()
                return MoveResult(True, f"No playable tile after {drawn_count} draws; you pass.")
            drawn_count += 1
            self.draw_count_player += 1
            self.move_history.append(f"Player auto-drew [{tile.left}|{tile.right}]")

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
                self.move_history.append(f"CPU played [{placed.left}|{placed.right}] on {chosen_side}")
                self._check_winner()
                if not self.winner:
                    self.current_turn = "player"
                return MoveResult(True, f"CPU played [{placed.left}|{placed.right}] on {chosen_side}.")

            drawn = self.cpu.draw_tile(self.boneyard)
            if drawn is None:
                self._consecutive_passes += 1
                self.current_turn = "player"
                self.move_history.append("CPU passed")
                self._check_blocked_game()
                return MoveResult(True, "CPU passes (no playable tile and boneyard empty).")
            self.draw_count_cpu += 1

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

        if self.winner is not None:
            self._apply_round_scoring()

    def _check_blocked_game(self) -> None:
        if self._consecutive_passes < 2 or len(self.boneyard) > 0:
            return
        player_blocked = not self.player.has_playable_tile(self.left_end, self.right_end)
        cpu_blocked = not self.cpu.has_playable_tile(self.left_end, self.right_end)
        if player_blocked and cpu_blocked:
            self.blocked = True
            player_pips = self.player.hand_pip_total()
            cpu_pips = self.cpu.hand_pip_total()
            if player_pips < cpu_pips:
                self.winner = "player"
            elif cpu_pips < player_pips:
                self.winner = "cpu"
            else:
                self.winner = "draw"
            self._apply_round_scoring()

    def _apply_round_scoring(self) -> None:
        if self.winner == "player":
            self.player_score += self.cpu.hand_pip_total()
        elif self.winner == "cpu":
            self.cpu_score += self.player.hand_pip_total()

    def game_over(self) -> bool:
        return self.winner is not None

    def match_over(self) -> bool:
        return self.player_score >= self.target_score or self.cpu_score >= self.target_score

    def start_next_round(self) -> None:
        self.round_number += 1
        self.draw_count_player = 0
        self.draw_count_cpu = 0
        self.move_history = []
        self.boneyard = Boneyard.generate(max_pip=self.max_pip, should_shuffle=False)
        self.boneyard.shuffle_with_rng(self.rng)
        self.player = Player(name="Player")
        self.cpu = Player(name="CPU")
        self.table = []
        self.left_end = None
        self.right_end = None
        self.current_turn = "player"
        self.winner = None
        self.blocked = False
        self._consecutive_passes = 0
        self._deal_initial_hands()
        self._set_opening_tile()

    def table_state(self) -> str:
        if self.left_end is None or self.right_end is None:
            return "Table is empty."
        return f"Table ends: L={self.left_end}, R={self.right_end}"

    def score_summary(self) -> str:
        return (
            f"Round {self.round_number} | Match Score => Player: {self.player_score} | CPU: {self.cpu_score} "
            f"| Round pips => Player: {self.player.hand_pip_total()} | CPU: {self.cpu.hand_pip_total()}"
        )

    def stats_summary(self) -> str:
        return f"Draw stats => Player draws: {self.draw_count_player}, CPU draws: {self.draw_count_cpu}"

    def save_to_file(self, path: str) -> None:
        payload = {
            "seed": self.seed,
            "max_pip": self.max_pip,
            "target_score": self.target_score,
            "round_number": self.round_number,
            "player_score": self.player_score,
            "cpu_score": self.cpu_score,
            "left_end": self.left_end,
            "right_end": self.right_end,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "blocked": self.blocked,
            "consecutive_passes": self._consecutive_passes,
            "draw_count_player": self.draw_count_player,
            "draw_count_cpu": self.draw_count_cpu,
            "table": [{"left": t.left, "right": t.right} for t in self.table],
            "player_hand": [{"left": t.left, "right": t.right} for t in self.player.hand],
            "cpu_hand": [{"left": t.left, "right": t.right} for t in self.cpu.hand],
            "boneyard": [{"left": t.left, "right": t.right} for t in self.boneyard.tiles],
            "move_history": self.move_history,
        }
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load_from_file(cls, path: str) -> "DominosGame":
        data = json.loads(Path(path).read_text())
        game = cls(
            seed=data["seed"],
            max_pip=data["max_pip"],
            target_score=data["target_score"],
            round_number=data["round_number"],
            player_score=data["player_score"],
            cpu_score=data["cpu_score"],
        )
        game.left_end = data["left_end"]
        game.right_end = data["right_end"]
        game.current_turn = data["current_turn"]
        game.winner = data["winner"]
        game.blocked = data["blocked"]
        game._consecutive_passes = data["consecutive_passes"]
        game.draw_count_player = data["draw_count_player"]
        game.draw_count_cpu = data["draw_count_cpu"]
        game.table = [Domino(**t) for t in data["table"]]
        game.player.hand = [Domino(**t) for t in data["player_hand"]]
        game.cpu.hand = [Domino(**t) for t in data["cpu_hand"]]
        game.boneyard.tiles = [Domino(**t) for t in data["boneyard"]]
        game.move_history = list(data["move_history"])
        return game
