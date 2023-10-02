from views import Window
from viewmodels import BoardViewModel


class Application:
    def __init__(self):
        # board = sample_board()
        self.board_viewmodel = BoardViewModel()
        self.window = Window((1200, 800), self.board_viewmodel)

    def run(self) -> None:
        self.window.mainloop()


app = Application()

app.run()
