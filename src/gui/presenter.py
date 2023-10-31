from __future__ import annotations
import re
from typing import Protocol
from .model import Model
from .errors import ExcelNotFoundError, ActiveCellError


class View(Protocol):
    def init_ui(self, presenter: Presenter) -> None:
        ...

    def update_image_list(self, image_list: list[str]) -> None:
        ...

    def init_workbook_list(self, active: str, options: list[str]) -> None:
        ...

    def update_workbook_list(self, options: list[str]) -> None:
        ...

    @property
    def selected_image(self) -> str:
        ...

    @property
    def selected_workbook(self) -> str:
        ...

    @property
    def selected_write_mode(self) -> str:
        ...

    def on_active_cell_select(self) -> None:
        ...

    def on_template_select(self) -> None:
        ...

    def set_workbook_selection(self, value: str) -> None:
        ...

    def set_active_cell_text(self, value: str) -> None:
        ...

    def mainloop(self) -> None:
        ...

    def popup_version(self) -> None:
        ...


def split_event_string(event_string: str) -> list[str]:
    """
    Converts event string containing the paths of files dropped into the frame
    to a list of file paths.
    """
    # Paths with spaces are bounded by { }
    bounded = re.compile("\{[^}^{]*\}")
    paths_bounded = re.findall(bounded, event_string)
    paths_bounded = [path.strip("{}") for path in paths_bounded]
    # Paths without spaces are in the event string as is
    # Remove the bounded strings
    paths_unbounded = re.sub(bounded, "", event_string)
    paths_unbounded = paths_unbounded.split()
    return paths_bounded + paths_unbounded


class Presenter:
    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view

    def run(self, version_file=None) -> None:
        self.view.init_ui(self)
        if version_file:
            self.view.popup_version()
        self.view.mainloop()

    def update_image_list(self) -> None:
        image_names = self.model.get_edge_names()
        self.view.update_image_list(image_names)

    def init_workbook_list(self) -> None:
        selected = self.model.excel.selected_book
        try:
            book_names = self.model.excel.book_names
        except ExcelNotFoundError:
            book_names = []
        self.view.init_workbook_list(selected, book_names)
        self.view.after(2000, self.update_workbook_list)

    def update_workbook_list(self) -> None:
        try:
            book_names = self.model.excel.book_names
            self.view.update_workbook_list(book_names)
        except ExcelNotFoundError:
            self.view.update_workbook_list([])
            self.view.set_workbook_selection("-")
        self.view.after(2000, self.update_workbook_list)

    def handle_files_dropped(self, event=None) -> None:
        dropped_list = split_event_string(event.data)
        self.model.add_edge_files(dropped_list)
        self.update_image_list()

    def handle_delete(self, event=None) -> None:
        self.model.delete_edge(self.view.selected_image)
        self.update_image_list()

    def handle_clear(self, event=None) -> None:
        self.model.delete_all()
        self.update_image_list()

    def handle_workbook_selected(self, *args) -> None:
        self.model.excel.selected_book = self.view.selected_workbook

    def handle_calculate(self) -> None:
        self.model.calculate_all()

    def handle_write(self) -> None:
        self.model.write_all_processed()

    def handle_calculate_write(self) -> None:
        self.handle_calculate()
        self.handle_write()

    def handle_write_mode(self) -> None:
        write_mode = self.view.selected_write_mode
        if write_mode == "template":
            self.handle_template_select()
        elif write_mode == "active_cell":
            self.handle_active_select()

    def handle_template_select(self) -> None:
        self.view.on_template_select()
        self.model.excel.write_mode = "template"

    def handle_active_select(self) -> None:
        self.view.on_active_cell_select()
        self.model.excel.write_mode = "active_cell"
        self.handle_active_cell_refresh()

    def handle_active_cell_refresh(self) -> None:
        try:
            self.model.excel.set_active_cell()
            active_cell = self.model.excel.active_cell
        except ActiveCellError as e:
            active_cell = ""
            print(e)

        self.view.set_active_cell_text(active_cell)

    def handle_version_check(self, version_file) -> None:
        pass
