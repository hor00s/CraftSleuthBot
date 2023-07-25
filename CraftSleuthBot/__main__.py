__author__ = 'hor00s'
__email__ = 'hor00s199@gmail.com'
__version__ = '1.0.0 beta'
__description__ = 'This bot will go through a sub and\
 alert mods through modmail if a post has been deleted'
__license__ = 'MIT'
__dependencies__ = ('praw',)

__disclaimer__ = """Disclaimer:
This Python bot is a personal hobby project created for fun and learning purposes.
It is not intended for any commercial use or critical tasks.
While efforts have been made to ensure its functionality, there may be bugs and/or errors.
The bot is provided as-is, without any warranty or guarantee of its performance.
Use it at your own risk.

The author and maintainers of this bot are not responsible for any damages, data loss,
or any adverse consequences that may arise from its use.
We do not collect or store any personal data or information from users."""


import sys
from main import main


if __name__ == '__main__':
    sys.exit(
        main()
    )
