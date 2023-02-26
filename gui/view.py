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

    def init_workbook_list(self) -> None:
        ...

    def update_workbook_list(self) -> None:
        ...

    def handle_workbook_selected(self, *args) -> None:
        ...

    def handle_calculate(self) -> None:
        ...

    def handle_write(self) -> None:
        ...

    def handle_calculate_write(self) -> None:
        ...

    def handle_write_mode(self) -> None:
        ...

    def handle_template_select(self) -> None:
        ...

    def handle_active_select(self) -> None:
        ...

    def handle_active_cell_refresh(self) -> None:
        ...


class MTFCalculator(tkdnd2.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.geometry("400x300")

    def init_ui(self, presenter: Presenter) -> None:
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=1, rowspan=2)
        self.frame.drop_target_register(DND_FILES)
        self.frame.dnd_bind("<<Drop>>", presenter.handle_files_dropped)

        tk.Label(self.frame, text="DICOM images to process:").pack()
        self.image_list = tk.Listbox(self.frame, height=10, width=30)
        self.image_list.bind("<<ListboxSelect>>", self.on_select_task)
        self.image_list.bind("<FocusOut>", self.on_focus_out)
        self.image_list.pack()

        self.image_list_buttons = tk.Frame(self.frame)
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

        self.workbook_frame = tk.Frame(self.frame)
        self.workbook_option_label = tk.Label(
            self.workbook_frame, text="Selected Excel workbook:"
        )
        presenter.init_workbook_list()
        self.workbook_selection = tk.StringVar(self.workbook_frame)
        self.workbook_selection.set(self.workbook_selected)
        self.workbook_option_menu = tk.OptionMenu(
            self.workbook_frame,
            self.workbook_selection,
            self.workbook_selected,
            *self.workbook_options
        )
        self.workbook_selection.trace("w", presenter.handle_workbook_selected)
        self.workbook_option_label.pack(side=tk.TOP)
        self.workbook_option_menu.pack(side=tk.BOTTOM)
        self.workbook_frame.pack()
        # Frame that contains the 'template' and 'active' radiobuttons for Excel write.
        self.write_mode_frame = tk.Frame(self)
        self.write_mode = tk.StringVar(self, value="template")
        self.write_mode_label = tk.Label(self.write_mode_frame, text="Write data to:")
        self.template_write = tk.Radiobutton(
            self.write_mode_frame,
            text="Template",
            variable=self.write_mode,
            value="template",
            command=presenter.handle_write_mode,
        )
        self.active_cell_write = tk.Radiobutton(
            self.write_mode_frame,
            text="Active cell",
            variable=self.write_mode,
            value="active_cell",
            command=presenter.handle_write_mode,
        )
        self.active_cell_refresh = tk.Button(
            self.write_mode_frame,
            text="Active cell:",
            state=tk.DISABLED,
            command=presenter.handle_active_cell_refresh,
        )
        self.active_cell = tk.StringVar(self)
        self.active_cell_value_text = tk.Label(
            self.write_mode_frame, textvariable=self.active_cell, state=tk.DISABLED
        )
        self.write_mode_label.pack()
        self.template_write.pack()
        self.active_cell_write.pack()
        self.active_cell_refresh.pack(side=tk.LEFT)
        self.active_cell_value_text.pack(side=tk.RIGHT)
        self.write_mode_frame.grid(row=0, column=0)
        # Frame for calculate and write buttons
        self.calc_button_frame = tk.Frame(self)
        self.calc_button_row1 = tk.Frame(self.calc_button_frame)
        self.calculate_button = tk.Button(
            self.calc_button_row1,
            text="Calculate MTF",
            command=presenter.handle_calculate,
        )
        self.calculate_button.pack(side=tk.LEFT)
        self.write_button = tk.Button(
            self.calc_button_row1,
            text="Write results",
            command=presenter.handle_write,
        )
        self.write_button.pack(side=tk.RIGHT)
        self.calc_button_row1.pack()
        self.calculate_write_button = tk.Button(
            self.calc_button_frame,
            text="Calculate and write",
            command=presenter.handle_calculate_write,
        )
        self.calculate_write_button.pack()
        self.calc_button_frame.grid(row=1, column=0, padx=10)

    @property
    def selected_image(self) -> str:
        try:
            return self.image_list.get(self.image_list.curselection())
        except tk.TclError:
            return ""

    @property
    def selected_workbook(self) -> str:
        return self.workbook_selection.get()

    @property
    def selected_write_mode(self) -> str:
        return self.write_mode.get()

    def set_workbook_selection(self, value: str) -> None:
        self.workbook_selection.set(value)

    def set_active_cell_text(self, value: str) -> None:
        self.active_cell.set(value)

    def on_select_task(self, event=None) -> None:
        self.button_delete_selected.config(state=tk.NORMAL)

    def on_focus_out(self, event=None) -> None:
        self.button_delete_selected.config(state=tk.DISABLED)

    def on_active_cell_select(self) -> None:
        self.active_cell_value_text.config(state=tk.NORMAL)
        self.active_cell_refresh.config(state=tk.NORMAL)

    def on_template_select(self) -> None:
        self.active_cell_value_text.config(state=tk.DISABLED)
        self.active_cell_refresh.config(state=tk.DISABLED)

    def update_image_list(self, image_list: list[str]) -> None:
        self.image_list.delete(0, tk.END)
        for image in image_list:
            self.image_list.insert(tk.END, image)
        self.image_list.yview(tk.END)

    def init_workbook_list(self, active: str, options: list[str]) -> None:
        self.workbook_selected = active
        self.workbook_options = options

    def update_workbook_list(self, options: list[str]) -> None:
        self.workbook_option_menu["menu"].delete(0, "end")
        for book in options:
            self.workbook_option_menu["menu"].add_command(
                label=book,
                command=lambda value=book: self.workbook_selection.set(value),
            )
