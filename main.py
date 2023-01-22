from gui.model import Model
from gui.presenter import Presenter
from gui.view import MTFCalculator
from gui.excel import XwingsHandler


def main() -> None:
    excel_handler = XwingsHandler()
    model = Model(excel_handler=excel_handler)
    view = MTFCalculator()
    presenter = Presenter(model, view)
    presenter.run()


if __name__ == "__main__":
    main()
