import sqlite3
import xlwings as xw
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


def get_active_book() -> str:
    try:
        return xw.books.active.name
    except xw.XlwingsError:
        return "-"


def get_book_names(active: str) -> list[str]:
    try:
        book_names = ["-"]
        [book_names.append(book.name) for book in xw.books if book.name != active]
        return book_names
    except xw.XlwingsError:
        return []


class ExcelHandler:
    def __init__(self) -> None:
        self.apps = xw.apps


class Model:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute(CREATE_TABLE)
        self.selected_book = self.active_book
        # self.active_book = get_active_book()
        # self.book_names = get_book_names(self.active_book)

    @property
    def active_book(self):
        try:
            return xw.books.active.name
        except xw.XlwingsError:
            return "-"

    @property
    def book_names(self):
        try:
            book_names = ["-"]
            [
                book_names.append(book.name)
                for book in xw.books
                if book.name != self.selected_book
            ]
            return book_names
        except xw.XlwingsError:
            return []

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
