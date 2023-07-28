# mypy: disable-error-code=attr-defined
import os
import sys
import praw  # type: ignore
import time
import utils
import prawcore  # type: ignore
import traceback
import datetime as dt
from pathlib import Path
from logger import Logger
from jsonwrapper import AutoSaveDict
from typing import (
    Optional,
    Callable,
    Tuple,
    List,
    Set,
    Any,
)
from bot import (
    Datatype,
    Posts,
    Row,
)


def config_app(path: Path) -> AutoSaveDict:
    config = {
        'client_id': '',
        'client_secret': '',
        'user_agent': '',
        'username': '',
        'password': '',
        'sub_name': '',
        'max_days': '',
        'max_posts': '',
    }

    configuration: List[List[str]] = []

    if not os.path.exists(path):
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


config_file = Path(utils.BASE_DIR, 'config.json')
handler = config_app(config_file)
handler.init()
posts = Posts('post', utils.BASE_DIR)
logger = Logger(1)
untracked_flairs = (utils.Flair.SOLVED, utils.Flair.ABANDONED)
posts.init()
reddit = praw.Reddit(
    client_id=handler['client_id'],
    client_secret=handler['client_secret'],
    user_agent=handler['user_agent'],
    username=handler['username'],
    password=handler['password'],
)


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


def send_modmail(reddit: praw.Reddit, subreddit: str, subject: str, msg: str) -> None:
    print("Sending modmail...")
    # reddit.subreddit(subreddit).message(subject, msg)
    print(msg)


def notify_if_error(func: Callable[..., int]) -> Callable[..., int]:
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.debug("\nProgram interrupted by user")
            return 0
        except:
            author = 'https://www.reddit.com/user/kaerfkeerg'
            full_error = traceback.format_exc()
            bot_name = utils.BOT_NAME
            msg = f"Error with '{bot_name}':\n\n{full_error}\n\nPlease report to author ({author})"
            send_modmail(
                reddit,
                handler['sub_name'],
                f'An error has occured with {utils.BOT_NAME} msg',
                msg
            )
            return 1
    return wrapper


def should_be_tracked(
        flair: utils.Flair,
        untracked_flairs: Tuple[utils.Flair, ...]) -> bool:
    return flair not in untracked_flairs


def user_is_deleted(submission: praw.reddit.Submission) -> bool:
    return submission.author is None


def check_submission(submission: praw.reddit.Submission, saved_submission_ids: Set[Row]) -> None:
    if not user_is_deleted(submission) and submission.id not in saved_submission_ids:
        flair = utils.get_flair(submission.link_flair_text)
        method = remove_method(submission)
        if should_be_tracked(flair, untracked_flairs):
            if method is None and submission.author is not None:
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


@notify_if_error
def main() -> int:
    posts_to_delete: Set[Row] = set()

    if utils.parse_cmd_line_args(sys.argv, logger, config_file, posts):
        return 0

    saved_submission_ids = {row.post_id for row in posts.fetch_all()}
    max_posts = handler['max_posts']
    limit = int(max_posts) if max_posts else None
    sub_name = handler['sub_name']

    for submission in reddit.subreddit(sub_name).new(limit=limit):
        try:
            check_submission(submission, saved_submission_ids)
        except prawcore.exceptions.TooManyRequests:
            time.sleep(60)
            check_submission(submission, saved_submission_ids)

    for stored_post in posts.fetch_all():
        try:
            submission = reddit.submission(id=stored_post.post_id)
            max_days = int(handler['max_days'])
            created = utils.string_to_dt(stored_post.record_created).date()
            flair = utils.get_flair(submission.link_flair_text)

            if utils.submission_is_older(created, max_days) or flair in untracked_flairs:
                posts_to_delete.add(stored_post)
                continue

            submission = reddit.submission(id=stored_post.post_id)
            method = remove_method(submission)
            if user_is_deleted(submission):
                send_modmail(
                    reddit,
                    handler['sub_name'],
                    "User's account has been deleted",
                    utils.modmail_removal_notification(stored_post, 'Account has been deleted')
                )
                posts_to_delete.add(stored_post)

            elif method is not None and not stored_post.deletion_method:
                stored_post.deletion_method = method
                stored_post.record_edited = str(dt.datetime.now())
                posts.edit(stored_post)
                msg = utils.modmail_removal_notification(stored_post, method)
                send_modmail(
                    reddit,
                    handler['sub_name'],
                    'A post has been deleted',
                    msg
                )
                posts_to_delete.add(stored_post)
                time.sleep(utils.MSG_AWAIT_THRESHOLD)

            if submission.selftext != stored_post.text\
                or submission.selftext != stored_post.post_last_edit\
                    and not stored_post.deletion_method:
                stored_post.post_last_edit = submission.selftext
                stored_post.record_edited = str(dt.datetime.now())
                posts.edit(stored_post)
        except prawcore.exceptions.TooManyRequests:
            time.sleep(60)

    for row in posts_to_delete:
        posts.delete(post_id=row.post_id)

    posts_to_delete.clear()
    logger.info("Program finished successfully")
    logger.info(f"Total posts deleted: {len(posts_to_delete)}")
    return 0


if __name__ == '__main__':
    sys.exit(
        main()
    )
