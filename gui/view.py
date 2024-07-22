from typing import Protocol, Tuple
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import customtkinter as ctk
from PIL import Image


TITLE = "DR MAM"


class Presenter(Protocol):
    def handle_files_dropped(self, event=None) -> None: ...

    def handle_delete(self, event=None) -> None: ...

    def handle_clear(self, event=None) -> None: ...

    def init_workbook_list(self) -> None: ...

    def update_workbook_list(self) -> None: ...

    def handle_workbook_selected(self, *args) -> None: ...

    def handle_calculate(self) -> None: ...

    def handle_write(self) -> None: ...

    def handle_calculate_write(self) -> None: ...

    def handle_write_mode(self) -> None: ...

    def handle_template_select(self) -> None: ...

    def handle_active_select(self) -> None: ...

    def handle_active_cell_refresh(self) -> None: ...

    def handle_image_select(self) -> None: ...


class cTkdnd(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, fg_color: str | Tuple[str, str] | None = None, **kwargs):
        super().__init__(fg_color, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MTFCalculator(cTkdnd):
    def __init__(self) -> None:
        super().__init__()
        self.title(TITLE)
        self.geometry("900x450")

    def init_ui(self, presenter: Presenter) -> None:
        self.frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frame.grid(row=0, column=1, rowspan=2)
        self.frame.drop_target_register(DND_FILES)
        self.frame.dnd_bind("<<Drop>>", presenter.handle_files_dropped)

        self.image_list_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.listbox_header = ctk.CTkLabel(
            self.image_list_frame, text="DICOM images to process:"
        ).pack()
        self.image_list = tk.Listbox(self.image_list_frame, height=10, width=30)
        self.image_list.bind("<<ListboxSelect>>", presenter.handle_image_select)
        self.image_list.bind("<FocusOut>", self.on_focus_out)
        self.image_list.pack()

        self.image_list_buttons = ctk.CTkFrame(self.image_list_frame)
        self.button_delete_selected = ctk.CTkButton(
            self.image_list_buttons,
            text="Delete selected",
            command=presenter.handle_delete,
        )
        self.button_delete_selected.pack(side=tk.LEFT)
        self.button_clear_all = ctk.CTkButton(
            self.image_list_buttons, text="Clear all", command=presenter.handle_clear
        )
        self.button_clear_all.pack(side=tk.LEFT)
        self.image_list_buttons.pack()
        self.image_list_frame.pack()

        self.workbook_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.workbook_option_label = ctk.CTkLabel(
            self.workbook_frame, text="Selected Excel workbook:"
        )
        presenter.init_workbook_list()
        self.workbook_selection = ctk.StringVar(self.workbook_frame)
        self.workbook_selection.set(self.workbook_selected)
        self.workbook_option_menu = ctk.CTkOptionMenu(
            master=self.workbook_frame,
            variable=self.workbook_selection,
            command=presenter.handle_workbook_selected,
            values=self.workbook_options,
        )
        self.workbook_option_label.pack(side=tk.TOP)
        self.workbook_option_menu.pack(side=tk.BOTTOM)
        self.workbook_frame.pack()

        self.image_display_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.image = ctk.CTkImage(
            light_image=Image.new("RGB", (100, 100), color="white"),
            dark_image=Image.new("RGB", (100, 100), color="black"),
            size=(200, 200),
        )
        self.image_display = ctk.CTkLabel(
            self.image_display_frame, text="", image=self.image
        )
        self.image_display.pack(padx=50, pady=10)
        self.image_display_details_frame = ctk.CTkFrame(
            self.image_display_frame, fg_color="transparent"
        )
        self.image_display_details_name = ctk.CTkLabel(
            self.image_display_details_frame, text=""
        )
        self.image_display_details_name.pack(side=tk.TOP)
        self.image_display_details_acquisition = ctk.CTkLabel(
            self.image_display_details_frame, text=""
        )
        self.image_display_details_acquisition.pack(side=tk.TOP)
        self.image_display_details_manufacturer = ctk.CTkLabel(
            self.image_display_details_frame, text=""
        )
        self.image_display_details_manufacturer.pack(side=tk.TOP)
        self.image_display_details_tomo_slice = ctk.CTkLabel(
            self.image_display_details_frame, text=""
        )
        self.image_display_details_tomo_slice.pack(side=tk.BOTTOM)
        self.image_display_details_frame.pack(fill="both", expand=True)
        self.image_display_frame.grid(row=0, column=2, rowspan=4)

        # Frame that contains the 'template' and 'active' radiobuttons for Excel write.
        self.write_mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.write_mode = ctk.StringVar(self, value="template")
        self.write_mode_label = ctk.CTkLabel(
            self.write_mode_frame, text="Write data to:"
        )
        self.template_write = ctk.CTkRadioButton(
            self.write_mode_frame,
            text="Template",
            variable=self.write_mode,
            value="template",
            command=presenter.handle_write_mode,
        )
        self.active_cell_write = ctk.CTkRadioButton(
            self.write_mode_frame,
            text="Active cell",
            variable=self.write_mode,
            value="active_cell",
            command=presenter.handle_write_mode,
        )
        self.active_cell_refresh = ctk.CTkButton(
            self.write_mode_frame,
            text="Active cell:",
            state=tk.DISABLED,
            command=presenter.handle_active_cell_refresh,
        )
        self.active_cell = ctk.StringVar(self)
        self.active_cell_value_text = ctk.CTkLabel(
            self.write_mode_frame, textvariable=self.active_cell, state=tk.DISABLED
        )
        self.write_mode_label.pack()
        self.template_write.pack()
        self.active_cell_write.pack()
        self.active_cell_refresh.pack(side=tk.LEFT)
        self.active_cell_value_text.pack(side=tk.RIGHT)
        self.write_mode_frame.grid(row=0, column=0, pady=5)
        # Frame for calculate and write buttons
        self.calc_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.calc_button_row1 = ctk.CTkFrame(self.calc_button_frame)
        self.calculate_button = ctk.CTkButton(
            self.calc_button_row1,
            text="Calculate MTF",
            command=presenter.handle_calculate,
        )
        self.calculate_button.pack(side=tk.LEFT)
        self.write_button = ctk.CTkButton(
            self.calc_button_row1,
            text="Write results",
            command=presenter.handle_write,
        )
        self.write_button.pack(side=tk.RIGHT)
        self.calc_button_row1.pack()
        self.calculate_write_button = ctk.CTkButton(
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

    def on_select_image(self, event=None) -> None:
        self.button_delete_selected.configure(state=tk.NORMAL)

    def on_focus_out(self, event=None) -> None:
        self.button_delete_selected.configure(state=tk.DISABLED)

    def on_active_cell_select(self) -> None:
        self.active_cell_value_text.configure(state=tk.NORMAL)
        self.active_cell_refresh.configure(state=tk.NORMAL)

    def on_template_select(self) -> None:
        self.active_cell_value_text.configure(state=tk.DISABLED)
        self.active_cell_refresh.configure(state=tk.DISABLED)

    def update_image_list(self, image_list: list[str]) -> None:
        self.image_list.delete(0, tk.END)
        for image in image_list:
            self.image_list.insert(tk.END, image)
        self.image_list.yview(tk.END)

    def init_workbook_list(self, active: str, options: list[str]) -> None:
        self.workbook_selected = active
        self.workbook_options = options

    def update_workbook_list(self, options: list[str]) -> None:
        vals = []
        self.workbook_option_menu.configure(values=vals)
        for book in options:
            vals.append(book)
            self.workbook_option_menu.configure(values=vals)

    def update_image_display(self, im: Image, image_details: dict) -> None:
        image_new = ctk.CTkImage(light_image=im, dark_image=im, size=(200, 200))
        self.image_display.configure(image=image_new)
        self.image_display_details_name.configure(text=self.selected_image)
        self.image_display_details_acquisition.configure(
            text=f"Acquisition type: {image_details['acquisition'].capitalize()}"
        )
        self.image_display_details_manufacturer.configure(
            text=f"Manufacturer: {image_details['manufacturer'].upper()}"
        )
        self.image_display_details_tomo_slice.configure(
            text=f"Focus plane (for Tomo): {image_details['focus_plane']}"
        )
