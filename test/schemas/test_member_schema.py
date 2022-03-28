from schemas import member_schema
from test.user_generators import generate_user


class TestCheckProfile:
    def test_user_is_new_creates_profile_and_rank(self):
        user = generate_user(1, "foo")
        member_schema.check_profile(user)

        profile = member_schema.get_profile_by_id(1)
        assert profile is not None

        rank = member_schema.get_player_rank_by_id(1)
        assert rank is not None

    def test_username_gets_updated_if_changed(self):
        user = generate_user(1, "foo")
        member_schema.check_profile(user)

        profile = member_schema.get_profile_by_id(1)
        assert profile['username'] == "foo"

        user = generate_user(1, "bar")
        member_schema.check_profile(user)

        profile = member_schema.get_profile_by_id(1)
        assert profile['username'] == "bar"

        rank = member_schema.get_player_rank_by_id(1)
        assert rank['username'] == "bar"
