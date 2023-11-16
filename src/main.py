from views import Window
from viewmodels import BoardViewModel
from repository import BoardRepository

DB_PATH = "puzzles.txt"


class Application:
    def __init__(self):
        # board = sample_board()
        self.repository = BoardRepository()
        self.repository.confi(DB_PATH)

        self.board_viewmodel = BoardViewModel(self.repository)
        self.window = Window((1200, 800), self.board_viewmodel)

    def run(self) -> None:
        self.window.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()
