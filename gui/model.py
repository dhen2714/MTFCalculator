import sqlite3
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path
import xlwings as xw
import numpy as np
from .sql_queries import CREATE_TABLE, INSERT_ROWS, DELETE_ALL, UPDATE_MTF_VALUES


@dataclass
class MTFEdge:

    fpath: str
    frequency: str = None
    mode: str = None
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
            self.mode,
            self.frequency,
            self.left,
            self.right,
            self.top,
            self.bottom,
            self.processed,
        )


class MTFCalculator(Protocol):
    def calculate_mtf(self, dicom_path) -> tuple[np.ndarray, dict]:
        ...


def mtfcol2str(data_column: np.array) -> str:
    """Convert numpy array to comma separated string."""
    return ",".join(data_column.astype(str))


def str2mtfcol(data_str: str) -> np.array:
    return np.array(data_str.split(","), dype=float)


class Model:
    def __init__(self, mtf_calculator: MTFCalculator = None) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute(CREATE_TABLE)
        self.selected_book = self.active_book
        self.mtf_calc = mtf_calculator

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

    def calculate_mtf(self, dicom_path: str | Path) -> tuple[str, dict]:
        """
        Calculate MTF for a single image.
        Reads dicom image
        Calculates mtfs for available edges.
        Returns results in form of strings
        """
        results_array, metadata = self.mtf_calc.calculate_mtf(dicom_path)
        frequency = mtfcol2str(results_array[:, 0])
        left = mtfcol2str(results_array[:, 1])
        right = mtfcol2str(results_array[:, 2])
        top = mtfcol2str(results_array[:, 3])
        bottom = mtfcol2str(results_array[:, 4])
        return frequency, left, right, top, bottom, metadata

    def update_mtf_values(
        self,
        fpath: str,
        mode: str,
        frequency: str,
        left: str,
        right: str,
        top: str,
        bottom: str,
    ) -> None:
        self.cursor.execute(
            UPDATE_MTF_VALUES, (mode, frequency, left, right, top, bottom, fpath)
        )
        self.connection.commit()
