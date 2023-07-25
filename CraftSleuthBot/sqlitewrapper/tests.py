import unittest
import os
from pathlib import Path
from .model import (
    Row,
    Model,
    Datatype
)


class TestRow(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_init(self) -> None:
        name, age = 'Mary', 14
        row = Row(name=name, age=age)
        result = row.values()
        self.assertEqual(result, (name, age))


class TestModel(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = Path(__file__).parent
        self.name = 'testdb'
        self.db = Model(
            self.name,
            self.base_dir,
            name=Datatype.STR,
            age=Datatype.INT,
        )
        self.db.init()
        return super().setUp()

    def tearDown(self) -> None:
        os.remove(self.db.path)
        return super().tearDown()

    def test_init(self) -> None:
        self.assertTrue(os.path.exists(self.db.path))

    def test_save(self) -> None:
        name, age = 'John', 14
        self.db.save(Row(name=name, age=age))
        self.db.get(name=name, age=age)  # This must not raise an Exception

        with self.assertRaises(ValueError):
            self.db.save(Row(name='test'))

    def test_delete(self) -> None:
        name, age = 'John', 14
        self.db.save(Row(name=name, age=age))
        self.db.delete(name=name, age=age)
        self.assertEqual(len(tuple(self.db.fetch_all())), 0)

    def test_edit(self) -> None:
        name, age = 'John', 14
        self.db.save(Row(name=name, age=age))
        r = self.db.get(name=name, age=age)
        r.name = 'Mary'
        self.db.edit(r)
        self.assertEqual(len(tuple(self.db.fetch_all())), 1)
        self.db.get(name='Mary', age=age)  # This should not raise an exception

    def test_filter(self) -> None:
        data = (
            ('John', 14),
            ('Mary', 14),
            ('Mary', 15),
        )

        for i in data:
            self.db.save(Row(name=i[0], age=i[1]))

        age = 14
        filtered = self.db.filter(age=age)
        data = list(filtered)  # type: ignore
        self.assertTrue(all(i.age == age for i in data))  # type: ignore
        self.assertEqual(len(data), 2)
