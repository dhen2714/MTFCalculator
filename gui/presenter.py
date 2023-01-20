from __future__ import annotations
import re
from typing import Protocol
from .model import Model


class View(Protocol):
    def init_ui(self, presenter: Presenter) -> None:
        ...

    def update_image_list(self, image_list: list[str]) -> None:
        ...

    @property
    def selected_image(self) -> str:
        ...

    def mainloop(self) -> None:
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

    def run(self) -> None:
        self.view.init_ui(self)
        self.view.mainloop()

    def update_image_list(self) -> None:
        image_names = self.model.get_edge_names()
        self.view.update_image_list(image_names)

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
