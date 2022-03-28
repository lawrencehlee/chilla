from typing import List

from discord import User


def generate_user(user_id: int, name: str) -> User:
    user = User(state=None, data={
        "username": name,
        "id": user_id,
        "discriminator": None,
        "avatar": None
    })
    user.id = user_id
    user.name = name

    return user


def generate_users(num_users: int, min_user_id: int = 0) -> List[User]:
    return [generate_user(min_user_id + i, f"User {i}") for i in range(num_users)]
