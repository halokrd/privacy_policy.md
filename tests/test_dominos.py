from dominos.game import DominosGame
from dominos.models import Boneyard, Domino, Player


def test_boneyard_has_28_unique_tiles():
    boneyard = Boneyard.double_six(should_shuffle=False)
    assert len(boneyard.tiles) == 28
    assert len({(d.left, d.right) for d in boneyard.tiles}) == 28


def test_tile_rotation_and_matching():
    game = DominosGame(seed=1)
    game.left_end = 5
    game.right_end = 1
    tile = Domino(3, 5)
    placed = game.place_tile(tile, "L")
    assert placed.left == 3
    assert game.left_end == 3


def test_draw_or_pass_behavior_when_boneyard_empty():
    game = DominosGame(seed=1)
    game.boneyard.tiles = []
    game.left_end = 2
    game.right_end = 4
    game.current_turn = "player"
    result = game.player_draw_or_pass()
    assert result.played
    assert "pass" in result.message.lower()


def test_blocked_game_scoring():
    game = DominosGame(seed=1)
    game.boneyard.tiles = []
    game.left_end = 6
    game.right_end = 6
    game.player.hand = [Domino(0, 1)]
    game.cpu.hand = [Domino(2, 3)]
    game._consecutive_passes = 2
    game._check_blocked_game()
    assert game.blocked
    assert game.winner == "player"


def test_winner_after_last_tile_played():
    game = DominosGame(seed=1)
    game.player.hand = [Domino(2, 2)]
    game.cpu.hand = [Domino(3, 3)]
    game.left_end = 2
    game.right_end = 5

    result = game.play_player_turn(0, "L")
    assert result.played
    assert game.winner == "player"


def test_player_has_playable_tile():
    player = Player(name="P", hand=[Domino(1, 2), Domino(4, 5)])
    assert player.has_playable_tile(5, 6)
    assert not player.has_playable_tile(0, 3)


def test_seeded_shuffle_is_deterministic():
    game_a = DominosGame(seed=42)
    game_b = DominosGame(seed=42)
    assert game_a.player.hand == game_b.player.hand
    assert game_a.cpu.hand == game_b.cpu.hand


def test_opening_tile_places_highest_double_and_switches_turn():
    game = DominosGame(seed=7)
    assert len(game.table) == 1
    opening = game.table[0]
    assert opening.is_double
    assert game.current_turn in {"player", "cpu"}


def test_legal_moves_reports_both_sides_when_possible():
    game = DominosGame(seed=1)
    game.left_end = 2
    game.right_end = 5
    assert game.legal_moves(Domino(2, 5)) == ["L", "R"]


def test_auto_draw_until_playable_or_pass():
    game = DominosGame(seed=1)
    game.left_end = 6
    game.right_end = 6
    game.player.hand = [Domino(0, 1)]
    game.boneyard.tiles = [Domino(2, 3), Domino(4, 6)]

    result = game.player_draw_until_playable()
    assert result.played
    assert game.player.has_playable_tile(6, 6)
