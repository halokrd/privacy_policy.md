from __future__ import annotations

from .game import DominosGame


def show_hand(game: DominosGame) -> None:
    print("\nYour hand:")
    for i, tile in enumerate(game.player.hand):
        legal = "/".join(game.legal_moves(tile))
        suffix = f" (play: {legal})" if legal else ""
        print(f"  {i}: [{tile.left}|{tile.right}]{suffix}")


def handle_player_turn(game: DominosGame) -> None:
    while True:
        print(f"\n{game.table_state()}")
        show_hand(game)
        choice = input("Choose index, D=draw, A=auto-draw, H=hint, Q=quit: ").strip().upper()

        if choice == "Q":
            raise SystemExit(0)

        if choice == "H":
            playable = game.legal_move_indexes_for_player()
            if playable:
                print(f"Hint: playable tile indexes => {playable}")
            else:
                print("Hint: no playable tiles; draw is recommended.")
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
            print("Invalid input. Enter a tile index, D, A, H, or Q.")
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


def main() -> None:
    game = DominosGame()
    print("Welcome to CLI Dominos (double-six).")

    while not game.game_over():
        if game.current_turn == "player":
            handle_player_turn(game)
        else:
            result = game.play_cpu_turn()
            print(f"\n{result.message}")

    if game.winner == "draw":
        print("\nGame over: blocked game ended in a draw.")
    else:
        print(f"\nGame over: {game.winner.upper()} wins!")
    print(game.score_summary())


if __name__ == "__main__":
    main()
