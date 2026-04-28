from __future__ import annotations

import argparse

from .game import DominosGame


def show_hand(game: DominosGame) -> None:
    print("\nYour hand:")
    for i, tile in enumerate(game.player.hand):
        legal = "/".join(game.legal_moves(tile))
        suffix = f" (play: {legal})" if legal else ""
        print(f"  {i}: [{tile.left}|{tile.right}]{suffix}")


def _print_history(game: DominosGame) -> None:
    print("\nMove history:")
    if not game.move_history:
        print("  (empty)")
        return
    for entry in game.move_history[-10:]:
        print(f"  - {entry}")


def handle_player_turn(game: DominosGame) -> DominosGame:
    while True:
        print(f"\n{game.table_state()}")
        print(game.score_summary())
        print(game.stats_summary())
        show_hand(game)
        choice = input(
            "Choose index, D=draw, A=auto-draw, H=hint, M=moves, S=save, L=load, Q=quit: "
        ).strip().upper()

        if choice == "Q":
            raise SystemExit(0)

        if choice == "H":
            playable = game.legal_move_indexes_for_player()
            if playable:
                print(f"Hint: playable tile indexes => {playable}")
            else:
                print("Hint: no playable tiles; draw is recommended.")
            continue

        if choice == "M":
            _print_history(game)
            continue

        if choice == "S":
            path = input("Save file path [dominos_save.json]: ").strip() or "dominos_save.json"
            game.save_to_file(path)
            print(f"Saved game to {path}")
            continue

        if choice == "L":
            path = input("Load file path [dominos_save.json]: ").strip() or "dominos_save.json"
            game = DominosGame.load_from_file(path)
            print(f"Loaded game from {path}")
            continue

        if choice == "A":
            result = game.player_draw_until_playable()
            print(result.message)
            if game.current_turn == "cpu":
                break
            continue

        if choice == "D":
            result = game.player_draw_or_pass()
            print(result.message)
            if "drew" in result.message.lower() and game.left_end is not None:
                continue
            break

        if not choice.isdigit():
            print("Invalid input. Enter a tile index, D, A, H, M, S, L, or Q.")
            continue

        index = int(choice)
        side = input("Play on left or right? (L/R): ").strip().upper()
        if side not in {"L", "R"}:
            print("Invalid side. Please choose L or R.")
            continue

        result = game.play_player_turn(index, side)
        print(result.message)
        if result.played:
            break
    return game


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI Dominos")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic shuffle seed")
    parser.add_argument("--max-pip", type=int, default=6, help="Highest pip value in tile set")
    parser.add_argument("--target-score", type=int, default=50, help="Match target score")
    args = parser.parse_args()

    game = DominosGame(seed=args.seed, max_pip=args.max_pip, target_score=args.target_score)
    print("Welcome to CLI Dominos.")

    while not game.match_over():
        while not game.game_over():
            if game.current_turn == "player":
                game = handle_player_turn(game)
            else:
                result = game.play_cpu_turn()
                print(f"\n{result.message}")

        if game.winner == "draw":
            print("\nRound over: blocked game ended in a draw.")
        else:
            print(f"\nRound over: {game.winner.upper()} wins!")
        print(game.score_summary())

        if game.match_over():
            break

        nxt = input("Start next round? (Y/n): ").strip().lower()
        if nxt not in {"", "y", "yes"}:
            break
        game.start_next_round()

    print("\nMatch finished.")
    if game.player_score > game.cpu_score:
        print("Overall winner: PLAYER")
    elif game.cpu_score > game.player_score:
        print("Overall winner: CPU")
    else:
        print("Overall result: DRAW")


if __name__ == "__main__":
    main()
