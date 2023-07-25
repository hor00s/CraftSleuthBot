from __future__ import annotations
from pathlib import Path
from sqlite3 import (
    Connection,
    connect,
)
from typing import (
    Generator,
    Optional,
    Tuple,
    List,
    Dict,
    Any,
)


__all__ = (
    'Row',
    'Model',
    'Datatype',
)


class Row:
    def __init__(self, **attrs: Any) -> None:
        for name, value in attrs.items():
            self.__dict__[name] = value

    def values(self) -> Tuple[Any, ...]:
        return tuple(self.__dict__.values())

    def keys(self) -> Tuple[Any, ...]:
        return tuple(self.__dict__.keys())

    def dict(self) -> Dict[Any, Any]:
        return self.__dict__

    def items(self) -> Any:
        return self.__dict__.items()

    def __str__(self) -> str:
        return f"<Row{self.__dict__}>"

    def __repr__(self) -> str:
        return str(self)

    def __iter__(self) -> Row:
        self.__n = 0
        return self

    def __next__(self) -> Any:
        keys = tuple(self.__dict__.keys())[:-1]  # Remove the `self.__n`
        if self.__n == len(keys):
            raise StopIteration
        data = keys[self.__n]
        self.__n += 1
        return data

    def __getitem__(self, __k: Any) -> Any:
        return self.__dict__[__k]


class Datatype:
    ID = 'INTEGER PRIMARY KEY'
    NULL = None
    INT = 'INTEGER'
    REAL = 'REAL'
    STR = 'TEXT'
    BLOB = 'BLOB'


class ConnectionManager:
    def __init__(self, db: str) -> None:
        self.db = db
        self._connection = connect(self.db)

    def __enter__(self) -> Connection:
        return self._connection

    def __exit__(self, *args: Any) -> None:
        self._connection.commit()
        self._connection.close()


class Model:
    def __init__(self, db_name: str, save_path: Path, **table: Any) -> None:
        self.name = db_name
        self.path = str(Path(f"{save_path}/.{db_name}.sqlite"))
        self.table = table
        self.table['id'] = Datatype.ID

        self.table_values = ' '.join(
            f"{name} {datatype}," for (name, datatype) in table.items()
        )[:-1]

    def __str__(self) -> str:
        data = list(self.fetch_all())
        return f"{self.__class__.__name__}{data}"

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(self.path)

    def _get_conditions(self, **where: Any) -> str:
        keys = tuple(where.keys())

        condition = ""
        for index, key in enumerate(keys):
            condition += f"{key} = ?"
            if index != len(keys) - 1:
                condition += " AND "

        return condition

    def execute(self, query: str, values: Optional[Tuple[Row, ...]] = None) -> Any:
        """Execute a query

        :param query: An SQL Query
        :type query: str
        :param values: vales to be added, if any, defaults to None
        :type values: Optional[Tuple[Row, ...]], optional
        :raises Exception: If tha database has not been initialized
                            before trying to execute any queries
        :return: Whatever the query would return
        :rtype: Any
        """
        with ConnectionManager(self.path) as cur:
            if values is None:
                data = cur.execute(query)
            else:
                data = cur.execute(query, values)
            return data.fetchall()

    def init(self) -> None:
        """Create a table based on the `self.table` (**table) kwargs
        provided upon initialization
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.name} (
            {self.table_values}
        )
        """
        self.execute(query)

    def save(self, row: Row) -> None:
        """Save a row into the db. Example:
        ```
            >>> row = Row(name='Pantelis', age=13)
            >>> self.save(row)
        ```

        :param row: A row object
        :type row: Row
        :raises ValueError: If the Row values does not match the db schema
        """
        fields = self.table
        #              - 1 for the id field
        if len(fields) - 1 != len(row.keys()):
            raise ValueError(f"Row fields {row.keys()} do not much db schema\
 {tuple(self.table.keys())[:-1]}. Consider adding 'Datatype.NULL' for the missing fields")

        marks = []
        for _ in row.values():
            marks.append('?')

        query = f"""
        INSERT INTO {self.name} {row.keys()}
        VALUES (
            {", ".join(marks)}
        )
        """
        self.execute(query, row.values())

    def delete(self, **where: Any) -> None:
        """Delete a row from the db. Example:
        ```
            >>> # Query: `DELETE FROM {self.name} WHERE name = ? AND age = ?`
            >>> # This will delete every row with name='John' and age=15
            >>> self.delete(name='John')
        ```
        """
        values = tuple(where.values())
        condition = self._get_conditions(**where)

        query = f"""
        DELETE FROM {self.name}
        WHERE
            {condition}
        """
        self.execute(query, values)

    def edit(self, row: Row) -> None:
        """After you picked and changed a row, use this instead of `save` in order
        for the entry to preserver the same `id`. Example:
        ```
            >>> row = self.get(name='john')
            >>> row.name = 'Mary'
            >>> self.edit(row)
        ```

        :param row: _description_
        :type row: Row
        """
        id = row.id
        self.delete(id=id)

        marks = []
        for _ in row.values():
            marks.append('?')

        query = f"""
        INSERT INTO {self.name} {row.keys()}
        VALUES (
            {", ".join(marks)}
        )
        """

        self.execute(query, row.values())

    def _entries_as_rows(self, data: List[Any]) -> List[Row]:
        """Take a list of entries and convert it to a list of `Row`s

        :param data: The list of entries
        :type data: List[Any]
        :return: A copy of the data as list or `Row`s
        :rtype: List[Row]
        """
        # rows = [
        #     <Row{'name': 'Pantelis', 'age': 12, 'id': 1}>,
        #     <Row{'name': 'Pantelis', 'age': 12, 'id': 2}>,
        # ]
        table_keys = tuple(self.table.keys())
        rows = []

        for row in data:
            struct = {}
            for index, col in enumerate(row):
                struct[table_keys[index]] = col
            rows.append(Row(**struct))
            struct.clear()

        return rows

    def fetch_all(self) -> Generator[Row, None, None]:
        query = f"SELECT * FROM {self.name}"
        data = self.execute(query)

        rows = self._entries_as_rows(data)
        yield from rows

    def filter(self, **where: Any) -> Generator[Row, None, None]:
        """Filter out data from the db based on the `where` conditions. Example
        ```
            >>> data = self.filter(name='Pantelis', age=13)
            >>> # Query created
            >>> # SELECT * FROM test WHERE name = Pantelis AND age = 13
            >>> for i in data:
            ...     i
            <Row{...}>
        ```

        :yield: Row
        :rtype: Generator[Row, None, None]
        """
        # cursor.execute("SELECT * FROM my_table WHERE name = ? AND age = ?", (name, age))
        values = tuple(where.values())
        condition = self._get_conditions(**where)

        query = f"""
        SELECT * FROM {self.name}
        WHERE
            {condition}
        """

        data = self.execute(query, values)
        rows = self._entries_as_rows(data)
        yield from rows

    def get(self, **where: Any) -> Row:
        """Find the first occurance matching the `where` condition(s) Example:
        ```
            >>> self.get(name="Pantelis", age=12)
            <Row{...}>
        ```

        :return: A `Row` with the values of the matching row
        :rtype: Row
        """
        values = tuple(where.values())

        condition = self._get_conditions(**where)

        query = f"""
        SELECT * FROM {self.name}
        WHERE
            {condition}
        """
        data = self.execute(query, values)[0]
        row = {}
        for value, name in zip(data, tuple(self.table.keys())):
            row[name] = value
        return Row(**row)


if __name__ == '__main__':
    pass
