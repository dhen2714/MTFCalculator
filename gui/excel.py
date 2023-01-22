from abc import ABC, abstractmethod
from pathlib import Path
import xlwings as xw
from .errors import ExcelNotFoundError


class ExcelHandler(ABC):
    selected_book: str

    @property
    @abstractmethod
    def book_names(self) -> list[str]:
        pass


class XwingsHandler(ExcelHandler):
    def __init__(self) -> None:
        try:
            self.selected_book = xw.books.active.name
        except xw.XlwingsError:
            self.selected_book = "-"

    @property
    def book_names(self) -> list[str]:
        try:
            book_names = ["-"]
            [
                book_names.append(book.name)
                for book in xw.books
                if book.name != self.selected_book
            ]
            return book_names
        except xw.XlwingsError:
            raise ExcelNotFoundError
