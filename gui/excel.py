from abc import ABC, abstractmethod
from pathlib import Path
import re
import xlwings as xw
import numpy as np
from pywintypes import com_error
from .errors import (
    ExcelNotFoundError,
    ValueOverwriteError,
    TemplateWriteError,
    ExcelWriteError,
    ActiveCellError,
)
from .calculator import ColumnIndex
from .constants import DEFAULT_TEMPLATE_PATH
from .utils import read_json


def excelkey2ind(excelkey: str) -> tuple[int, int]:
    """
    Converts excel key in <letter, number> format to (row number, column number).
    E.g.
    excelkey2ind('E3') = (3, 5)
    """
    reg = re.search("\D+", excelkey)
    colxl, rowxl = excelkey[reg.start() : reg.end()], excelkey[reg.end() :]

    numletters = len(colxl)
    colnum = 0
    for i, letter in enumerate(colxl):
        power = numletters - i - 1
        colnum += (ord(letter.lower()) - 96) * (26**power)

    rownum = int(rowxl)
    return rownum, colnum


class ExcelHandler(ABC):
    selected_book: str

    @property
    @abstractmethod
    def book_names(self) -> list[str]:
        pass


class XwingsHandler(ExcelHandler):
    def __init__(self, write_mode="template", params_path=None) -> None:
        self.write_mode = write_mode
        self.active_sheet = None
        self.active_cell = None
        self.active_cell_gen = None
        try:
            self.selected_book = xw.books.active.name
        except xw.XlwingsError:
            self.selected_book = "-"
        if params_path:
            self.params_dict = read_json(params_path)
        else:
            self.params_dict = read_json(DEFAULT_TEMPLATE_PATH)

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
        except (xw.XlwingsError, com_error, OSError):
            raise ExcelNotFoundError

    def set_active_cell(self) -> None:
        xwbook = xw.books[self.selected_book]
        sheet_selection = xwbook.app.selection.sheet
        if sheet_selection.book.name != self.selected_book:
            self.active_sheet = None
            self.active_cell = None
            self.active_cell_gen = None
            raise ActiveCellError("Active cell not in selected workbook.")

        self.active_sheet = sheet_selection.name
        selected_size = xwbook.app.selection.size
        if selected_size > 1:
            raise ExcelWriteError
        self.active_cell = xwbook.app.selection.address.replace("$", "")
        self.active_cell_gen = self.write_cell_generator(self.active_cell)

    def write_cell_generator(self, active_cell: str) -> tuple[int, int]:
        row_write, col_write = excelkey2ind(active_cell)
        increment = 5
        while True:
            yield (row_write, col_write)
            col_write += increment

    def write_active(self, file_name: str, mode: str, mtf_data: np.ndarray) -> None:
        header_rows = np.array(
            [
                [file_name, mode, "", "", ""],
                ["f", "left", "right", "top", "bottom"],
            ]
        )
        write_sheet = xw.books[self.selected_book].sheets[self.active_sheet]
        write_data = np.concatenate((header_rows, mtf_data))
        write_cell = next(self.active_cell_gen)
        try:
            write_values(write_sheet, write_data, write_cell)
        except ValueOverwriteError:
            raise ActiveCellError(
                "Values detected in cells, cannot write to active cell."
            )

    def write_template(
        self, manufacturer: str, mode: str, mtf_data: np.ndarray
    ) -> None:
        """Substitution not implemented."""
        book_name = self.selected_book
        sheet_name = self.params_dict["sheet_name"]
        try:
            xwsheet = xw.books[book_name].sheets[sheet_name]
        except com_error:
            raise TemplateWriteError
        cell_key = self.params_dict["modes"][mode]
        edge_locations_write = self.params_dict[manufacturer]["edge_locations"].split(
            ", "
        )
        edge_indices = [
            ColumnIndex[edge_loc].value for edge_loc in edge_locations_write
        ]
        array_list = []
        for edge_index in edge_indices:
            array = np.array([mtf_data[:, 0], mtf_data[:, edge_index]]).T
            array_list.append(array)

        formatted_data = np.concatenate(array_list, axis=1)
        write_values(xwsheet, formatted_data, cell_key)

    def write_data(
        self, file_name: str, manufacturer: str, mode: str, mtf_data: np.ndarray
    ) -> None:
        try:
            if self.write_mode == "template":
                self.write_template(manufacturer, mode, mtf_data)
            else:
                self.write_active(file_name, mode, mtf_data)
        except xw.XlwingsError as e:
            print(e)
            raise ExcelWriteError
        except TemplateWriteError as e:
            print(e)
            raise ExcelWriteError
        except ValueOverwriteError as e:
            print(e)
            raise ExcelWriteError
        except ActiveCellError as e:
            print(e)
            self.set_active_cell()


def write_values(
    sheet: xw.Sheet, array: np.ndarray, cell_key: str | tuple[int, int]
) -> None:
    """Write 2D array to Excel sheet."""
    array_shape = array.shape

    if type(cell_key) is str:
        top_left_index = excelkey2ind(cell_key)
    else:
        top_left_index = cell_key

    endrow, endcol = (
        (top_left_index[0] + array_shape[0] - 1),
        (top_left_index[1] + array_shape[1] - 1),
    )

    current_values = np.array(sheet.range(top_left_index, (endrow, endcol)).value)
    if current_values.astype("object").any():
        error_string = (
            f"Values detected in region with {cell_key} "
            + "as the top-left index. The bottom right (row, column) "
            + f"index is {endrow, endcol}."
        )
        raise ValueOverwriteError(error_string)
    else:
        sheet.range(top_left_index, (endrow, endcol)).value = array
