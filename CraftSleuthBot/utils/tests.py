import unittest
import datetime as dt
from .actions import (
    Flair,
    get_flair,
    string_to_dt,
    submission_is_older,
)


class TestActions(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_get_flair(self) -> None:
        solved = get_flair("Solved")
        self.assertEqual(solved, Flair.SOLVED)
        abandoned = get_flair('Abandoned')
        self.assertEqual(abandoned, Flair.ABANDONED)
        uknown = get_flair('Uknown')
        self.assertEqual(uknown, Flair.UKNOWN)
        uknown = get_flair('fsdafsd')
        self.assertEqual(uknown, Flair.UKNOWN)

    def test_string_to_dt(self) -> None:
        datetime = dt.datetime.now()
        string_dt = str(datetime)
        back_to_dt = string_to_dt(string_dt)
        self.assertEqual(datetime, back_to_dt)

    def test_submission_is_older(self) -> None:
        max_days = 7
        today = dt.datetime.now()

        post_made = today - dt.timedelta(days=3)
        result = submission_is_older(post_made.date(), max_days)
        self.assertFalse(result)

        post_made = today - dt.timedelta(days=max_days)
        result = submission_is_older(post_made.date(), max_days)
        self.assertFalse(result)

        post_made = today - dt.timedelta(days=(max_days + 1))
        result = submission_is_older(post_made.date(), max_days)
        self.assertTrue(result)
