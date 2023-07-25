from pathlib import Path
from sqlitewrapper import Model, Datatype, Row


__all__ = (
    'Datatype',
    'Posts',
    'Row',
)


class Posts(Model):
    def __init__(self, db_name: str, save_path: Path) -> None:
        self.__table = {
            'username': Datatype.STR,
            'title': Datatype.STR,
            'text': Datatype.STR,
            'post_id': Datatype.STR,
            'deletion_method': Datatype.STR,
            'post_last_edit': Datatype.STR,
            'record_created': Datatype.STR,
            'record_edited': Datatype.STR,
        }
        super().__init__(db_name, save_path, **self.__table)
