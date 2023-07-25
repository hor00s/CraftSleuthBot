import os
import sys
import praw  # type: ignore
import time
import utils
import traceback
import datetime as dt
from pathlib import Path
from logger import Logger
from jsonwrapper import AutoSaveDict
from typing import (
    Optional,
    Callable,
    List,
    Any,
)
from bot import (
    Datatype,
    Posts,
    Row,
)

config_file = Path(utils.BASE_DIR, 'config.json')
posts = Posts('post', utils.BASE_DIR)
logger = Logger(1)


def remove_method(submission: praw.reddit.Submission) -> Optional[str]:
    removed = submission.removed_by_category
    if removed is not None:
        if removed in ('author', 'moderator'):
            method = 'Removed by moderator'
        elif removed in ('deleted',):
            method = 'Deleted by user'
        else:
            method = 'Uknown deletion method'
        return method

    return None


def send_modmail(msg: str) -> None:
    print("Sending modmail...")
    print(msg)


def notify_if_error(func: Callable[..., int]) -> Callable[..., int]:
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)
        except:  # noqa
            full_error = traceback.format_exc()
            msg = f"Error with '{utils.BOT_NAME}':\n\n{full_error}\n\nPlease report to author"
            send_modmail(msg)
            return 1
    return wrapper


def config_app(path: Path) -> AutoSaveDict:
    config = {
        'client_id': '',
        'client_secret': '',
        'user_agent': '',
        'username': '',
        'password': '',
        'sub_name': '',
        'max_days': '',
    }

    configuration = []
    if not os.path.exists(path):
        send_modmail(f"{utils.BOT_NAME} needs configuration!")
        for key, _ in config.items():
            config_name = ' '.join(key.split('_')).title()
            user_inp = input(f"{config_name}: ")
            configuration.append([key, user_inp])

    for config_name, value in configuration:
        config[config_name] = value

    config_handler = AutoSaveDict(
        path,
        **config
    )
    return config_handler


def get_command_line_args(args: List[str]) -> None:
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


def modmail_removal_notification(submission: Row, method: str) -> str:
    return f"""A post has been removed
OP: {submission.username}
Title: {submission.title}
Post ID: reddit.com/{submission.post_id}
Deleted by: {method}
Date created: {submission.record_created}
Date found: {submission.record_edited}"""


@notify_if_error
def main() -> int:
    get_command_line_args(sys.argv)
    handler = config_app(config_file)
    handler.init()

    reddit = praw.Reddit(
        client_id=handler['client_id'],
        client_secret=handler['client_secret'],
        user_agent=handler['user_agent'],
        username=handler['username'],
        password=handler['password'],
    )

    posts.init()

    saved_submission_ids = [row.post_id for row in posts.fetch_all()]
    for submission in reddit.subreddit(handler['sub_name']).new():
        if submission.id not in saved_submission_ids:
            method = remove_method(submission)
            if method is None and submission.author.name is not None:
                original_post = Row(
                    username=submission.author.name,
                    title=submission.title,
                    text=submission.selftext,
                    post_id=submission.id,
                    deletion_method=Datatype.NULL,
                    post_last_edit=Datatype.NULL,
                    record_created=str(dt.datetime.now()),
                    record_edited=str(dt.datetime.now()),
                )
                posts.save(original_post)

        elif method is not None:
            original_post = Row(
                username='uknown',
                title=submission.title,
                text='N/A',
                post_id=submission.id,
                deletion_method=Datatype.NULL,
                post_last_edit=Datatype.NULL,
                record_created=str(dt.datetime.now()),
                record_edited=str(dt.datetime.now()),
            )
            posts.save(original_post)
            msg = modmail_removal_notification(original_post, method)
            send_modmail(msg)
        time.sleep(utils.MSG_THRESHOLD)

    for stored_post in posts.fetch_all():
        max_days = int(handler['max_days'])
        created = utils.string_to_dt(stored_post.record_created).date()
        if utils.submission_is_older(created, max_days):
            posts.delete(id=stored_post.id)
            continue

        submission = reddit.submission(id=stored_post.post_id)
        method = remove_method(submission)
        if method is not None and not stored_post.deletion_method:
            stored_post.deletion_method = method
            stored_post.record_edited = str(dt.datetime.now())
            posts.edit(stored_post)
            msg = modmail_removal_notification(stored_post, method)
            send_modmail(msg)

        if submission.selftext != stored_post.text\
            or submission.selftext != stored_post.post_last_edit\
                and not remove_method(submission):
            stored_post.post_last_edit = submission.selftext
            stored_post.record_edited = str(dt.datetime.now())
            posts.edit(stored_post)
        time.sleep(utils.MSG_THRESHOLD)

    return 0


if __name__ == '__main__':
    sys.exit(
        main()
    )
