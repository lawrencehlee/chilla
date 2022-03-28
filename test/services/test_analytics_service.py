from datetime import datetime, date
from typing import List

import pytest

from models.game import Game, EmptyGame
from models.leaderboards import Leaderboard
from models.profile import Outcome, PlayerGameResult
from models.queue_models import Queue
from schemas import ingame_schema
from services import analytics_service, game_service
from test.services.game_helpers import start_test_game, transform_user


class TestGetMonthlyLeaderboard:
    def test_no_games_played_leaderboard_is_empty(self):
        leaderboard = analytics_service.get_leaderboard(2021, 9)
        assert leaderboard.start_date == date(2021, 9, 1)
        self.assert_leaderboard_is_empty(leaderboard)

    def test_no_games_played_in_time_period_leaderboard_is_empty(self):
        self.play_fake_game(datetime(2021, 8, 31), Outcome.WIN)
        leaderboard = analytics_service.get_leaderboard(2021, 9)
        self.assert_leaderboard_is_empty(leaderboard)

    def test_single_game_represented_in_leaderboard(self):
        game = self.play_fake_game(datetime(2021, 9, 1), Outcome.WIN)
        leaderboard = analytics_service.get_leaderboard(2021, 9)
        assert leaderboard.total_games == 1
        assert leaderboard.most_popular_maps == [(game.maps[0], 1)]
        assert len(leaderboard.most_games_played) == 10
        assert len(leaderboard.most_games_won) == 10
        assert len(leaderboard.highest_winrate) == 10

    def test_multiple_games_represented_in_leaderboard(self):
        self.play_fake_game(datetime(2021, 9, 1), Outcome.LOSS)
        self.play_fake_game(datetime(2021, 9, 30), Outcome.WIN)
        leaderboard = analytics_service.get_leaderboard(2021, 9)
        assert leaderboard.total_games == 2
        assert len(leaderboard.most_games_played) == 10
        assert len(leaderboard.most_games_won) == 10
        assert len(leaderboard.highest_winrate) == 10

    def test_can_get_leaderboard_for_year(self):
        self.play_fake_game(datetime(2021, 9, 1), Outcome.LOSS)
        leaderboard = analytics_service.get_leaderboard(2021, None)
        assert leaderboard.total_games == 1

    def test_can_get_leaderboard_for_month_in_current_year(self):
        self.play_fake_game(datetime.now(), Outcome.LOSS)
        leaderboard = analytics_service.get_leaderboard(None, datetime.now().month)
        assert leaderboard.total_games == 1

    def test_can_get_leaderboard_for_all_time(self):
        self.play_fake_game(datetime.now(), Outcome.LOSS)
        leaderboard = analytics_service.get_leaderboard(None, None)
        assert leaderboard.total_games == 1

    @staticmethod
    def assert_leaderboard_is_empty(leaderboard: Leaderboard):
        assert leaderboard.start_date == date(2021, 9, 1)
        assert leaderboard.end_date == date(2021, 9, 30)
        assert leaderboard.total_games == 0
        assert leaderboard.most_popular_maps == []
        assert leaderboard.most_games_played == []
        assert leaderboard.most_games_won == []
        assert leaderboard.highest_winrate == []

    @staticmethod
    def play_fake_game(timestamp: datetime, team_1_outcome: Outcome) -> Game:
        game = start_test_game(Queue.QUICKPLAY)
        game_service.finish(transform_user(game.team1_captain), team_1_outcome)
        ingame_schema.override_timestamps(game.game_id, timestamp)

        return game


class TestCalculatePopularMaps:
    def test_no_games_returns_empty(self):
        assert analytics_service.calculate_popular_maps([]) == []

    def test_one_game_returns_itself(self):
        assert analytics_service.calculate_popular_maps([self.generate_game(["M1"])]) == [("M1", 1)]

    def test_correctly_calculates_for_multiple_games(self):
        popular_maps = analytics_service.calculate_popular_maps([
            self.generate_game(["M1"]),
            self.generate_game(["M1", "M2"]),
            self.generate_game(["M3", "M4", "M2"]),
            self.generate_game(["M5", "M6"]),
            self.generate_game(["M2", "M6", "M2", "M6"]),
        ])
        assert popular_maps == [("M2", 4), ("M6", 3), ("M1", 2)]

    @staticmethod
    def generate_game(maps: List[str]):
        return EmptyGame(None, None, None, None, None, maps)


class TestFindPlayersWithHighestWinrates:
    def test_no_games(self):
        assert analytics_service.find_players_with_highest_winrates([]) == []

    def test_one_game(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.LOSS),
            PlayerGameResult(3, "g1", Outcome.LOSS)
        ])
        result = analytics_service.find_players_with_highest_winrates(player_stats)
        assert set(result[:2]) == {("User 0", 1.0), ("User 1", 1.0)}
        assert result[2] in {("User 2", 0.0), ("User 3", 0.0)}

    def test_multiple_games(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.WIN),
            PlayerGameResult(3, "g1", Outcome.LOSS),
            PlayerGameResult(0, "g2", Outcome.WIN),
            PlayerGameResult(1, "g2", Outcome.WIN),
            PlayerGameResult(2, "g2", Outcome.LOSS),
            PlayerGameResult(3, "g2", Outcome.LOSS),
            PlayerGameResult(0, "g3", Outcome.WIN),
            PlayerGameResult(1, "g3", Outcome.LOSS),
            PlayerGameResult(2, "g3", Outcome.LOSS),
            PlayerGameResult(3, "g3", Outcome.LOSS),
        ])
        result = analytics_service.find_players_with_highest_winrates(player_stats)
        assert result == [("User 0", 3 / 3), ("User 1", 2 / 3), ("User 2", 1 / 3), ("User 3", 0)]


class TestFindPlayersWithMostGames:
    def test_no_games(self):
        assert analytics_service.find_players_with_most_games([]) == []

    def test_one_game(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.LOSS)
        ])
        result = analytics_service.find_players_with_most_games(player_stats)
        assert set(result) == {("User 0", 1), ("User 1", 1), ("User 2", 1)}

    def test_multiple_games(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.WIN),
            PlayerGameResult(3, "g1", Outcome.LOSS),
            PlayerGameResult(0, "g2", Outcome.WIN),
            PlayerGameResult(1, "g2", Outcome.WIN),
            PlayerGameResult(2, "g2", Outcome.LOSS),
            PlayerGameResult(0, "g3", Outcome.WIN),
            PlayerGameResult(1, "g3", Outcome.LOSS),
            PlayerGameResult(0, "g4", Outcome.LOSS)
        ])
        result = analytics_service.find_players_with_most_games(player_stats)
        assert result == [("User 0", 4), ("User 1", 3), ("User 2", 2), ("User 3", 1)]


class TestFindPlayersWithMostWins:
    def test_no_games(self):
        assert analytics_service.find_players_with_most_wins([]) == []

    def test_one_game(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.LOSS)
        ])
        result = analytics_service.find_players_with_most_wins(player_stats)
        assert result == [("User 0", 1), ("User 1", 1), ("User 2", 0)]

    def test_multiple_games(self, initialize_users):
        player_stats = analytics_service.calculate_player_stats([
            PlayerGameResult(0, "g1", Outcome.WIN),
            PlayerGameResult(1, "g1", Outcome.WIN),
            PlayerGameResult(2, "g1", Outcome.WIN),
            PlayerGameResult(3, "g1", Outcome.WIN),
            PlayerGameResult(0, "g2", Outcome.WIN),
            PlayerGameResult(1, "g2", Outcome.WIN),
            PlayerGameResult(2, "g2", Outcome.WIN),
            PlayerGameResult(3, "g2", Outcome.LOSS),
            PlayerGameResult(0, "g3", Outcome.WIN),
            PlayerGameResult(1, "g3", Outcome.WIN),
            PlayerGameResult(2, "g3", Outcome.LOSS),
            PlayerGameResult(3, "g3", Outcome.LOSS),
            PlayerGameResult(0, "g4", Outcome.WIN),
            PlayerGameResult(1, "g4", Outcome.LOSS),
            PlayerGameResult(2, "g4", Outcome.LOSS),
            PlayerGameResult(3, "g4", Outcome.LOSS),
        ])
        result = analytics_service.find_players_with_most_wins(player_stats)
        assert result == [("User 0", 4), ("User 1", 3), ("User 2", 2), ("User 3", 1)]


@pytest.fixture(scope="function")
def initialize_users():
    start_test_game(Queue.QUICKPLAY)
