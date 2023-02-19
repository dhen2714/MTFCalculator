from abc import ABC, abstractmethod
from pathlib import Path
import re
import xlwings as xw
import numpy as np
from .errors import (
    ExcelNotFoundError,
    ValueOverwriteError,
    TemplateWriteError,
    ExcelWriteError,
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
        except xw.XlwingsError:
            raise ExcelNotFoundError

    def write_template(self, mode: str, mtf_data: np.ndarray):
        """Substitution not implemented."""
        book_name = self.selected_book
        sheet_name = self.params_dict["sheet_name"]
        xwsheet = xw.books[book_name].sheets[sheet_name]
        cell_key = self.params_dict["modes"][mode]
        edge_locations_write = self.params_dict["edge_locations"].split(", ")
        edge_indices = [
            ColumnIndex[edge_loc].value for edge_loc in edge_locations_write
        ]
        array_list = []
        for edge_index in edge_indices:
            array = np.array([mtf_data[:, 0], mtf_data[:, edge_index]]).T
            array_list.append(array)

        formatted_data = np.concatenate(array_list, axis=1)
        write_values(xwsheet, formatted_data, cell_key)

        # if contact:
        #     cell_key = self.params_dict["contact"]
        #     write_values(xwsheet, contact, cell_key)
        # if magnification:
        #     cell_key = self.params_dict["mag"]
        #     write_values(xwsheet, magnification, cell_key)
        # if tomo_proj_top:
        #     cell_key = self.params_dict["tomo_proj_top"]
        #     write_values(xwsheet, tomo_proj_top, cell_key)
        # if tomo_proj_bot:
        #     cell_key = self.params_dict["tomo_proj_bot"]
        #     write_values(xwsheet, tomo_proj_bot, cell_key)
        # if tomo_recon_top:
        #     cell_key = self.params_dict["tomo_recon_top"]
        #     write_values(xwsheet, tomo_recon_top, cell_key)
        # if tomo_recon_bot:
        #     cell_key = self.params_dict["tomo_recon_bot"]
        #     write_values(xwsheet, tomo_recon_bot, cell_key)

    def write_data(self, file_name: str, mode: str, mtf_data: np.ndarray) -> None:
        try:
            if self.write_mode == "template":
                self.write_template(mode, mtf_data)
        except xw.XlwingsError as e:
            print(e)
            raise ExcelWriteError
        except TemplateWriteError:
            print(e)
            raise ExcelWriteError


def write_values(sheet: xw.Sheet, array: np.ndarray, cell_key: str) -> None:
    """Write 2D array to Excel sheet."""
    array_shape = array.shape
    top_left_index = excelkey2ind(cell_key)
    endrow, endcol = (
        (top_left_index[0] + array_shape[0] - 1),
        (top_left_index[1] + array_shape[1] - 1),
    )

    current_values = np.array(sheet.range(top_left_index, (endrow, endcol)).value)
    if current_values.any():
        raise ValueOverwriteError
    else:
        sheet.range(top_left_index, (endrow, endcol)).value = array
