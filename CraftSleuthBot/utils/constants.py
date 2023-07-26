from pathlib import Path
from enum import Enum


__all__ = (
    'Flair',
    'BASE_DIR',
    'BOT_NAME',
    'MSG_THRESHOLD',
)


class Flair(Enum):
    SOLVED = 'Solved'
    ABANDONED = 'Abandoned'
    Uknown = 'Uknown'


BOT_NAME = 'CraftSleuthBot'
BASE_DIR = Path(__file__).parent.parent.parent
MSG_THRESHOLD = 5
