from pathlib import Path


__all__ = (
    'BASE_DIR',
    'BOT_NAME',
    'MSG_THRESHOLD',
)

BOT_NAME = 'CraftSleuthBot'
BASE_DIR = Path(__file__).parent.parent.parent
MSG_THRESHOLD = 5
