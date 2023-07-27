# mypy: disable-error-code=attr-defined
import os
import datetime as dt
from bot import Posts
from pathlib import Path
from enum import Enum
from typing import List
from logger import Logger
from sqlitewrapper import Row


__all__ = (
    'Flair',
    'get_flair',
    'modmail_removal_notification',
    'parse_cmd_line_args',
    'submission_is_older',
    'string_to_dt',
)


class Flair(Enum):
    SOLVED = 'Solved'
    ABANDONED = 'Abandoned'
    UKNOWN = 'Uknown'


def get_flair(flair: str) -> Flair:
    try:
        return Flair(flair)
    except ValueError:
        return Flair('Uknown')


def modmail_removal_notification(submission: Row, method: str) -> str:
    return f"""A post has been removed

OP: {submission.username}

Title: {submission.title}

Post ID: https://reddit.com/{submission.post_id}

Deleted by: {method}

Date created: {submission.record_created}

Date found: {submission.record_edited}"""


def parse_cmd_line_args(args: List[str], logger: Logger, config_file: Path, posts: Posts) -> bool:
    help_msg = """Command line help prompt
    Command: help
    Args: []
    Decription: Prints the help prompt

    Command: reset_config
    Args: []
    Decription: Reset the bot credentials

    Command: reset_db
    Args: []
    Decription: Reset the database
"""
    if len(args) > 1:
        if args[1] == 'help':
            logger.info(help_msg)
        elif args[1] == 'reset_config':
            try:
                os.remove(config_file)
            except FileNotFoundError:
                logger.error("No configuration file found")
        elif args[1] == 'reset_db':
            try:
                os.remove(posts.path)
            except FileNotFoundError:
                logger.error("No database found")
        else:
            logger.info(help_msg)
        return True
    return False


def submission_is_older(submission_date: dt.date, max_days: int) -> bool:
    current_date = dt.datetime.now().date()
    time_difference = current_date - submission_date
    if time_difference.days > max_days:
        return True
    return False


def string_to_dt(date_string: str) -> dt.datetime:
    return dt.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
