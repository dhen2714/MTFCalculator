import sqlite3
from typing import Protocol
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
from .sql_queries import CREATE_TABLE, INSERT_ROWS, DELETE_ALL, UPDATE_MTF_VALUES
from .errors import ExcelWriteError


@dataclass
class MTFEdge:

    fpath: str
    _name: str = field(default=None,  compare=False)
    mode: str = None
    frequency: str = None
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


class ExcelHandler(Protocol):
    selected_book: str

    @property
    def book_names(self) -> list[str]:
        ...

    def write_data(self, file_name: str, mode: str, mtf_data: np.ndarray) -> None:
        ...


def mtfcol2str(data_column: np.array) -> str:
    """Convert numpy array to comma separated string."""
    return ",".join(data_column.astype(str))


def str2mtfcol(data_str: str) -> np.array:
    return np.array(data_str.split(","), dtype=float)


class Model:
    def __init__(
        self, mtf_calculator: MTFCalculator = None, excel_handler: ExcelHandler = None
    ) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute(CREATE_TABLE)
        self.excel = excel_handler
        self.mtf_calc = mtf_calculator

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

    def get_unprocessed_paths(self) -> list[str]:
        unprocessed_rows = self.cursor.execute(
            "select fpath from edges where processed = 0"
        )
        unprocessed_paths = []
        for row in unprocessed_rows:
            unprocessed_paths.append(row[0])
        return unprocessed_paths

    def calculate_all(self) -> None:
        """
        Calculate MTF for all unprocessed image files
        """
        unprocessed = self.get_unprocessed_paths()
        for dcm_path in unprocessed:
            frequency, left, right, top, bottom, metadata = self.calculate_mtf(dcm_path)
            mode = metadata["mode"]
            self.update_mtf_values(dcm_path, mode, frequency, left, right, top, bottom)
        pass

    def get_all_processed(self) -> list[MTFEdge]:
        """
        Extract all processed entries from the database
        """
        processed_rows = self.cursor.execute(
            "select * from edges where processed = 1"
        ).fetchall()
        processed_rows = [MTFEdge(*values) for values in processed_rows]
        return processed_rows

    def write_all_processed(self) -> list[dict]:
        """
        Go through database, getting all processed edges and writing them all to
        excel.
        """
        processed_rows = self.get_all_processed()

        for row in processed_rows:
            row.frequency = str2mtfcol(row.frequency)
            row.left = str2mtfcol(row.left)
            row.right = str2mtfcol(row.right)
            row.top = str2mtfcol(row.top)
            row.bottom = str2mtfcol(row.bottom)
            mtf_data = np.array(
                [row.frequency, row.left, row.right, row.top, row.bottom]
            ).T
            try:
                self.excel.write_data(row.name, row.mode, mtf_data)
            except ExcelWriteError as e:
                print(e)
