from models.game import GameStatus
from models.queue_models import Queue
from services import game_service
from test.services.game_helpers import start_test_draft_game, transform_user


def test_can_start_draft_game():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    assert game.queue == Queue.COMPETITIVE
    assert len(game.get_all_players()) == 2
    assert game.team1_captain is not None
    assert game.team1_captain.team == 1
    assert game.team2_captain is not None
    assert game.team2_captain.team == 2
    assert len(game.unassigned_players) == 8
    assert game.game_id == draft_state.game_id
    assert draft_state.team_to_pick in (1, 2)
    assert draft_state.num_picks == 1


def test_cannot_draft_on_wrong_turn():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    captain = game.team2_captain
    player = game.unassigned_players[0]

    try:
        game_service.pick_player(transform_user(captain), [player.user_id])
    except ValueError:
        return

    assert False


def test_cannot_draft_incorrect_number_of_players():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    captain = game.team2_captain
    players = game.unassigned_players[0:2]

    try:
        game_service.pick_player(transform_user(captain), [player.user_id for player in players])
    except ValueError:
        return

    assert False


def test_can_draft_all_players_in_1_2_2_2_1_pick_order():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    draft_and_assert_looks_correct(game.game_id, 1)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 1)


def draft_and_assert_looks_correct(game_id: int, expected_num_picks: int):
    game, draft_state = game_service.get_game_and_draft_state(game_id)

    assert draft_state.num_picks == expected_num_picks

    players = game.unassigned_players[0:draft_state.num_picks]
    captain = game.team1_captain if draft_state.team_to_pick == 1 else game.team2_captain

    updated_game, updated_draft_state = game_service.pick_player(transform_user(captain),
                                                                 [player.user_id for player in players])

    assert len(updated_game.unassigned_players) == len(game.unassigned_players) - draft_state.num_picks

    for player in players:
        assert player not in updated_game.unassigned_players
        if draft_state.team_to_pick == 1:
            assert player in updated_game.team1_players
        else:
            assert player in updated_game.team2_players

    if len(updated_game.unassigned_players) == 0:
        assert updated_game.status == GameStatus.STARTED
        assert len(updated_game.team1_players) == 5
        assert len(updated_game.team2_players) == 5
    else:
        assert updated_draft_state.team_to_pick != draft_state.team_to_pick


def test_cannot_draft_after_all_players_drafted():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    draft_and_assert_looks_correct(game.game_id, 1)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 1)

    try:
        game_service.pick_player(transform_user(game.team1_captain), [12351245])
    except ValueError:
        return

    assert False


def test_draft_state_is_deleted_afterwards():
    game, draft_state = start_test_draft_game(Queue.COMPETITIVE)

    draft_and_assert_looks_correct(game.game_id, 1)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 2)
    draft_and_assert_looks_correct(game.game_id, 1)

    _, draft_state = game_service.get_game_and_draft_state(game.game_id)
    assert draft_state is None
