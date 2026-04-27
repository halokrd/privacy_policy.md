from __future__ import annotations

from .game import DominosGame


def show_hand(game: DominosGame) -> None:
    print("\nYour hand:")
    for i, tile in enumerate(game.player.hand):
        print(f"  {i}: [{tile.left}|{tile.right}]")


def handle_player_turn(game: DominosGame) -> None:
    while True:
        print(f"\n{game.table_state()}")
        show_hand(game)
        choice = input("Choose tile index to play, 'D' to draw/pass, or 'Q' to quit: ").strip()

        if choice.upper() == "Q":
            raise SystemExit("Game ended by player.")

        if choice.upper() == "D":
            result = game.player_draw_or_pass()
            print(result.message)
            if "drew" in result.message.lower() and game.left_end is not None:
                continue
            break

        if not choice.isdigit():
            print("Invalid input. Enter a numeric tile index, D, or Q.")
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


if __name__ == "__main__":
    main()
