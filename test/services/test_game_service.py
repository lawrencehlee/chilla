import math
from typing import Set, Dict

from models.game import Game, GameStatus
from models.ingame_models import SwapError, SwapResult, ScrambleError
from models.profile import Profile, Outcome
from models.queue_models import Queue, UserInGame
from services import game_service, queue_service, profile_service
from services.game_service import get_games
from test.services.game_helpers import start_test_game, transform_user
from test.user_generators import generate_user


class TestGetGames:
    def test_no_games_started_returns_no_games(self):
        user1 = generate_user(1, "Bob")
        user2 = generate_user(2, "Cary")

        queue_service.add(user1, Queue.QUICKPLAY)
        queue_service.add(user2, Queue.COMPETITIVE)

        games = get_games()
        assert len(games) == 0

        games = get_games(Queue.QUICKPLAY)
        assert len(games) == 0

        games = get_games(Queue.COMPETITIVE)
        assert len(games) == 0

    def test_game_started_then_returns_game_status(self):
        start_test_game(Queue.QUICKPLAY)

        games = get_games()
        assert len(games) == 1
        self.assert_game_looks_correct(games[0])

    def test_multiple_games_started(self):
        start_test_game(Queue.QUICKPLAY, 0)
        start_test_game(Queue.COMPETITIVE, 1)
        start_test_game(Queue.QUICKPLAY, 2)
        start_test_game(Queue.QUICKPLAY, 3)
        start_test_game(Queue.COMPETITIVE, 4)

        games = get_games()
        assert len(games) == 5
        for game in games:
            self.assert_game_looks_correct(game)

    @staticmethod
    def assert_game_looks_correct(game: Game):
        assert game.status == GameStatus.STARTED

        assert len(game.team1_players) == 5
        assert len(game.team2_players) == 5

        team1_captain_name = game.get_team1_captain_name()
        assert team1_captain_name not in game.get_team1_others_names()

        team2_captain_name = game.get_team2_captain_name()
        assert team2_captain_name not in game.get_team2_others_names()

        assert team1_captain_name != team2_captain_name
        assert set(game.get_team1_others_names()).isdisjoint(set(game.get_team2_others_names()))


class TestShuffle:
    def test_shuffled_teams_have_no_repeats(self):
        teams_seen = set()

        game = start_test_game(Queue.QUICKPLAY)

        teams_seen.add(frozenset([player.user_id for player in game.team1_players]))
        teams_seen.add(frozenset([player.user_id for player in game.team2_players]))

        for i in range(125):
            game = game_service.shuffle_teams(game.game_id)
            team1 = frozenset([player.user_id for player in game.team1_players])
            team2 = frozenset([player.user_id for player in game.team2_players])

            assert team1 not in teams_seen
            assert team2 not in teams_seen

            teams_seen.add(team1)
            teams_seen.add(team2)


class TestSwap:
    def test_user_not_in_game(self):
        user1 = generate_user(1, "User 1")
        user2 = generate_user(2, "User 2")

        result = game_service.swap(user1, user2)

        assert result.error == SwapError.USER_NOT_IN_GAME

    def test_target_not_in_game(self):
        game = start_test_game(Queue.COMPETITIVE)
        user_not_in_game = generate_user(9999, "k")

        result = game_service.swap(transform_user(game.team1_players[0]), user_not_in_game)

        assert result.error == SwapError.TARGET_NOT_IN_GAME

    def test_swap_non_captains(self):
        game = start_test_game(Queue.COMPETITIVE)

        user = game.team1_others[0]
        target = game.team2_others[0]

        expected_team1_players = set(game.team1_players).difference({user}).union({target})
        expected_team2_players = set(game.team2_players).difference({target}).union({user})

        result = game_service.swap(transform_user(user), transform_user(target))

        self.assert_swap_result_success(result, user, target)
        self.assert_teams_are_correct(result.game, expected_team1_players, expected_team2_players)

    def test_user_is_captain(self):
        game = start_test_game(Queue.COMPETITIVE)

        user = game.team1_captain
        target = game.team2_others[0]

        result = game_service.swap(transform_user(user), transform_user(target))

        user.is_captain = False
        target.is_captain = True
        expected_team1_players = set(game.team1_players).difference({user}).union({target})
        expected_team2_players = set(game.team2_players).difference({target}).union({user})

        self.assert_swap_result_success(result, user, target)
        self.assert_teams_are_correct(result.game, expected_team1_players, expected_team2_players)

    def test_target_is_captain(self):
        game = start_test_game(Queue.QUICKPLAY)

        user = game.team1_others[0]
        target = game.team2_captain

        result = game_service.swap(transform_user(user), transform_user(target))

        user.is_captain = True
        target.is_captain = False
        expected_team1_players = set(game.team1_players).difference({user}).union({target})
        expected_team2_players = set(game.team2_players).difference({target}).union({user})

        self.assert_swap_result_success(result, user, target)
        self.assert_teams_are_correct(result.game, expected_team1_players, expected_team2_players)

    def test_both_are_captains(self):
        game = start_test_game(Queue.QUICKPLAY)

        user = game.team1_captain
        target = game.team2_captain

        result = game_service.swap(transform_user(user), transform_user(target))

        expected_team1_players = set(game.team1_players).difference({user}).union({target})
        expected_team2_players = set(game.team2_players).difference({target}).union({user})

        self.assert_swap_result_success(result, user, target)
        self.assert_teams_are_correct(result.game, expected_team1_players, expected_team2_players)

    @staticmethod
    def assert_swap_result_success(result: SwapResult, user, target):
        assert result.error is None
        assert result.user_name == user.name
        assert result.target_name == target.name

        assert len(result.game.team1_players) == 5
        assert len(result.game.team2_players) == 5
        assert result.game.team1_captain is not None
        assert result.game.team2_captain is not None

    @staticmethod
    def assert_teams_are_correct(game: Game, expected_team_a: Set[UserInGame], expected_team_b: Set[UserInGame]):
        actual_team_1 = set(game.team1_players)
        actual_team_2 = set(game.team2_players)

        assert actual_team_1 == expected_team_a and actual_team_2 == expected_team_b


class TestScrambleMap:
    def test_fails_when_user_is_not_in_game(self):
        start_test_game(Queue.QUICKPLAY)
        user_not_in_game = generate_user(9999, "k")

        maps, error = game_service.scramble_map(user_not_in_game, 1)

        assert error == ScrambleError.USER_NOT_IN_GAME

    def test_fails_when_map_number_is_invalid(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)

        maps, error = game_service.scramble_map(user, 3)

        assert error == ScrambleError.INVALID_MAP_NUMBER

    def test_successfully_scrambles_map(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)
        last_map = game.maps[0]

        for i in range(14):
            maps, error = game_service.scramble_map(user, 1)

            assert error is None
            assert maps[0] != last_map

            last_map = maps[0]


class TestFinish:
    def test_fails_when_user_is_not_in_game(self):
        start_test_game(Queue.QUICKPLAY)
        user_not_in_game = generate_user(9999, "k")

        finished_game = game_service.finish(user_not_in_game, Outcome.WIN)

        assert finished_game is None

    def test_finishing_updates_game_state(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)

        finished_game = game_service.finish(user, Outcome.WIN)

        assert finished_game.status == GameStatus.FINISHED

    def test_finishing_updates_profiles_for_win(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)

        initial_profiles = self.get_initial_profiles(game)

        game_service.finish(user, Outcome.WIN)

        for user in game.team1_players:
            self.assert_profile_updated_for(user.user_id, initial_profiles, Outcome.WIN)

        for user in game.team2_players:
            self.assert_profile_updated_for(user.user_id, initial_profiles, Outcome.LOSS)

    def test_finishing_updates_ranks_for_loss(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)

        initial_profiles = self.get_initial_profiles(game)

        game_service.finish(user, Outcome.LOSS)

        for user in game.team1_players:
            self.assert_profile_updated_for(user.user_id, initial_profiles, Outcome.LOSS)

        for user in game.team2_players:
            self.assert_profile_updated_for(user.user_id, initial_profiles, Outcome.WIN)

    def test_finishing_updates_ranks_for_tie(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)

        initial_profiles = self.get_initial_profiles(game)

        game_service.finish(user, Outcome.TIE)

        for user in game.get_all_players():
            self.assert_profile_updated_for(user.user_id, initial_profiles, Outcome.TIE)

    @staticmethod
    def get_initial_profiles(game: Game) -> Dict[int, Profile]:
        return {user.user_id: profile_service.get(user.user_id) for user in game.get_all_players()}

    @staticmethod
    def assert_profile_updated_for(user_id, initial_profiles, outcome: Outcome):
        initial_profile = initial_profiles[user_id]
        updated_profile = profile_service.get(user_id)

        assert updated_profile.games_played == initial_profile.games_played + 1
        assert updated_profile.last_played is not None and initial_profile.last_played == "Never"
        assert updated_profile.confidence < initial_profile.confidence

        if outcome == Outcome.WIN:
            assert updated_profile.wins == 1
            assert updated_profile.losses == 0
            assert updated_profile.ties == 0
            assert updated_profile.rank > initial_profile.rank
        elif outcome == Outcome.LOSS:
            assert updated_profile.wins == 0
            assert updated_profile.losses == 1
            assert updated_profile.ties == 0
            assert updated_profile.rank < initial_profile.rank
        else:
            assert updated_profile.wins == 0
            assert updated_profile.losses == 0
            assert updated_profile.ties == 1
            assert math.isclose(updated_profile.rank, initial_profile.rank)


class TestGetHistory:
    def test_no_games(self):
        history = game_service.get_history()
        assert len(history) == 0

    def test_gets_one_game(self):
        game = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game.team1_captain)
        game_service.finish(user, Outcome.WIN)

        history = game_service.get_history()
        assert len(history) == 1
        historical_game = history[0]
        assert user.name in historical_game.winners

    def test_gets_five_games(self):
        game1 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game1.team1_captain)
        game_service.finish(user, Outcome.WIN)

        game2 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game2.team1_captain)
        game_service.finish(user, Outcome.LOSS)

        game3 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game3.team1_captain)
        game_service.finish(user, Outcome.TIE)

        game4 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game4.team1_captain)
        game_service.finish(user, Outcome.WIN)

        game5 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game5.team1_captain)
        game_service.finish(user, Outcome.LOSS)

        game6 = start_test_game(Queue.QUICKPLAY)
        user = transform_user(game6.team1_captain)
        game_service.finish(user, Outcome.TIE)

        history = game_service.get_history()
        assert len(history) == 5
        assert history[0].game.game_id == game6.game_id
        assert history[1].game.game_id == game5.game_id
        assert history[2].game.game_id == game4.game_id
        assert history[3].game.game_id == game3.game_id
        assert history[4].game.game_id == game2.game_id


class TestFlipResults:
    def test_can_flip_wins_or_losses(self):
        game = start_test_game(Queue.QUICKPLAY)
        winner1 = transform_user(game.team1_captain)
        game_service.finish(winner1, Outcome.WIN)

        assert game_service.flip_results(game.game_id)

        history = game_service.get_history()
        assert winner1.name in history[0].losers

    def test_cannot_flip_ties(self):
        game = start_test_game(Queue.QUICKPLAY)
        winner1 = transform_user(game.team1_captain)
        game_service.finish(winner1, Outcome.TIE)

        assert not game_service.flip_results(game.game_id)
