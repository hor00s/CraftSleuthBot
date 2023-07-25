import datetime as dt


__all__ = (
    'submission_is_older',
    'string_to_dt',
)


def submission_is_older(submission_date: dt.date, max_days: int) -> bool:
    current_date = dt.datetime.now().date()
    time_difference = current_date - submission_date
    if time_difference.days > max_days:
        return True
    return False


def string_to_dt(date_string: str) -> dt.datetime:
    return dt.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
