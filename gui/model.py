import sqlite3
from dataclasses import dataclass
from pathlib import Path
from .sql_queries import CREATE_TABLE, INSERT_ROWS, DELETE_ALL


@dataclass
class MTFEdge:

    fpath: str
    left: str = None
    right: str = None
    top: str = None
    bottom: str = None
    processed: int = 0

    @property
    def name(self) -> str:
        return Path(self.fpath).name

    def astuple(self) -> tuple[str, ...]:
        return (
            self.fpath,
            self.name,
            self.left,
            self.right,
            self.top,
            self.bottom,
            self.processed,
        )


class Model:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute(CREATE_TABLE)

    def add_edge_files(self, file_list: list[str]) -> None:
        new_data_rows = [MTFEdge(fpath=fpath).astuple() for fpath in file_list]
        self.cursor.executemany(INSERT_ROWS, new_data_rows)
        self.connection.commit()

    def get_edge_names(self) -> list[str]:
        edge_names: list[str] = []
        for data_row in self.cursor.execute("select fpath from edges"):
            file_name = Path(data_row[0]).name
            edge_names.append(file_name)
        return edge_names

    def delete_all(self) -> None:
        self.cursor.execute(DELETE_ALL)
        self.connection.commit()

    def delete_edge(self, name: str) -> None:
        self.cursor.execute("delete from edges where name = ?", (name,))
        self.connection.commit()
