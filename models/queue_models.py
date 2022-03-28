from datetime import datetime
from enum import Enum

MAX_QUEUE_SIZE = 10


class Queue(Enum):
    # For legacy data processing
    CASUAL = "casual"
    QUICKPLAY = "quickplay"
    COMPETITIVE = "competitive"
    NEWBLOODS = "newbloods"
    TEST = "test"


class AddStatus(Enum):
    ALREADY_IN_QUEUE = 1
    ALREADY_IN_GAME = 2
    DELAYED = 3


class UserInGame:
    """
    A player currently in game. Equality does not account for team assignment.
    """

    def __init__(self, user_id: int, name: str, is_captain: bool, team: int = None):
        self.is_captain = is_captain
        self.name = name
        self.user_id = user_id
        self.team = team

    def __repr__(self):
        return f"UserInGame(user_id={self.user_id}, name={self.name}, is_captain={self.is_captain})"

    def __eq__(self, other):
        if not isinstance(other, UserInGame):
            return False
        return self.__repr__() == other.__repr__()

    def __hash__(self):
        return hash(self.__repr__())


class AddResult:
    def __init__(self, status: AddStatus, queue_count: int, queue: Queue, delay_seconds=None):
        self.queue = queue
        self.status = status
        self.queue_count = queue_count
        self.delay_seconds = delay_seconds

    @classmethod
    def status(cls, status: AddStatus, queue: Queue, delay_seconds=None):
        return cls(status=status, queue_count=None, queue=queue, delay_seconds=delay_seconds)

    @classmethod
    def added(cls, queue_count: int, queue: Queue):
        return cls(status=None, queue_count=queue_count, queue=queue)

    def should_start(self) -> bool:
        return self.queue_count == MAX_QUEUE_SIZE


class DelayQueueEntry:
    def __init__(self, user_id, username, queue: Queue, target: datetime, added: datetime):
        self.user_id = user_id
        self.username = username
        self.queue = queue
        self.target = target
        self.added = added
