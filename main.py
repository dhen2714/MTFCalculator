from gui.model import Model
from gui.presenter import Presenter
from gui.view import MTFCalculator


def main() -> None:
    model = Model()
    view = MTFCalculator()
    presenter = Presenter(model, view)
    presenter.run()


if __name__ == "__main__":
    main()
