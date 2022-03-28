from models.profile import Profile
from schemas import member_schema


def get(user_id) -> Profile:
    profile_data = member_schema.get_profile_by_id(user_id)
    rank = member_schema.get_player_rank_by_id(user_id)
    wins, losses, ties = member_schema.get_player_stats(user_id)
    return Profile(user_id, profile_data["username"], profile_data["position"], profile_data["lastPlayed"],
                   profile_data["hideRank"], profile_data["gamesPlayed"], profile_data.get("bio"), rank["rank"],
                   rank["confidence"], wins, losses, ties)
