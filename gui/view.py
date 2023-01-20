from typing import Protocol
import tkinter as tk
import tkinterdnd2 as tkdnd2
from tkinterdnd2 import DND_FILES


TITLE = "MTFCalculator"


class Presenter(Protocol):
    def handle_files_dropped(self, event=None) -> None:
        ...

    def handle_delete(self, event=None) -> None:
        ...

    def handle_clear(self, event=None) -> None:
        ...


class MTFCalculator(tkdnd2.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.geometry("500x300")

    def init_ui(self, presenter: Presenter) -> None:
        self.frame = tk.Frame(self)
        self.frame.pack()
        self.frame.drop_target_register(DND_FILES)
        self.frame.dnd_bind("<<Drop>>", presenter.handle_files_dropped)

        tk.Label(self.frame, text="DICOM images to process:").pack()
        self.image_list = tk.Listbox(self.frame, height=10, width=30)
        self.image_list.bind("<<ListboxSelect>>", self.on_select_task)
        self.image_list.bind("<FocusOut>", self.on_focus_out)
        self.image_list.pack()

        self.image_list_buttons = tk.Frame(self)
        self.button_delete_selected = tk.Button(
            self.image_list_buttons,
            text="Delete selected",
            command=presenter.handle_delete,
        )
        self.button_delete_selected.pack(side=tk.LEFT)
        self.button_clear_all = tk.Button(
            self.image_list_buttons, text="Clear all", command=presenter.handle_clear
        )
        self.button_clear_all.pack(side=tk.LEFT)
        self.image_list_buttons.pack()

    @property
    def selected_image(self) -> str:
        return self.image_list.get(self.image_list.curselection())

    def on_select_task(self, event=None) -> None:
        self.button_delete_selected.config(state=tk.NORMAL)

    def on_focus_out(self, event=None) -> None:
        # self.image_list.selection_clear(0, tk.END)
        self.button_delete_selected.config(state=tk.DISABLED)

    def update_image_list(self, image_list: list[str]) -> None:
        self.image_list.delete(0, tk.END)
        for image in image_list:
            self.image_list.insert(tk.END, image)
        self.image_list.yview(tk.END)
