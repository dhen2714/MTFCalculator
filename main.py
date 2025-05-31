from gui.calculator import MammoTemplateCalc
from gui.model import Model
from gui.presenter import Presenter
from gui.view import MTFCalculator
from gui.excel import XwingsHandler
from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    # If running in PyInstaller bundle
    print(sys._MEIPASS)
    dll_path = os.path.join(sys._MEIPASS, "bin")
    os.add_dll_directory(dll_path)

TEMPLATE_PATH = Path(__file__).parent / "template_parameters.json"


def main() -> None:
    excel_handler = XwingsHandler(TEMPLATE_PATH)
    calculator = MammoTemplateCalc(TEMPLATE_PATH)
    model = Model(mtf_calculator=calculator, excel_handler=excel_handler)
    view = MTFCalculator()
    presenter = Presenter(model, view)
    presenter.run()


if __name__ == "__main__":
    main()
