import tkinter as tk
from tkinter import ttk
from typing import Tuple

import sv_ttk
from viewmodels import BoardViewModel


class Window(tk.Tk):
    def __init__(self, size: Tuple[int, int], board_vmodel: BoardViewModel) -> None:
        super().__init__()
        self.size = size
        self.viewmodel = board_vmodel
        sv_ttk.set_theme("dark")
        self.build_ui()

    def build_ui(self) -> None:
        # Center the window
        width, height = self.size
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.board = BoardFrame(self, self.viewmodel)
        self.board.pack(side=tk.LEFT, fill=tk.Y)

        self.controls = ControlFrame(self, self.viewmodel)
        self.controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # subcribe when board changes
        self.viewmodel.subcribe(self.board.redraw)

    def draw_board(self):
        self.board.redraw()


class BoardFrame(ttk.Frame):
    def __init__(self, master, viewmodel: BoardViewModel):
        super().__init__(master, width=600, height=600)

        self.viewmodel = viewmodel
        self.canvas = tk.Canvas(
            self,
            bg="white",
            bd=0,
            highlightthickness=0,
        )
        self.bind("<Configure>", self.__configure)

        self.canvas.pack(side=tk.LEFT)

    def __configure(self, event):
        """Make canvas alway a square"""
        self.canvas.config(height=event.height)
        self.canvas.config(width=event.height)

    def redraw(self):
        size = self.viewmodel.board.size
        border_size = 4
        canvas_size = self.canvas.winfo_width()
        point_size = (canvas_size - 2 * border_size) / (8 * size - 7)
        spacer = 7 * point_size
        colors = ["#44222F", "#21300D", "#B4DC7F", "#3C3D00"]

        self.canvas.delete("all")
        self.canvas.create_rectangle(
            1,
            1,
            self.canvas.winfo_width() - 1,
            self.canvas.winfo_height() - 1,
            fill="#F7F9F9",
            outline="#78D5D7",
            width=2,
        )

        # Draw point grid
        for x in range(size):
            for y in range(size):
                x1 = x * (spacer + point_size) + border_size
                y1 = y * (spacer + point_size) + border_size

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x1 + point_size,
                    y1 + point_size,
                    fill="#D56F3E",
                )

        # Draw cell
        for x in range(size - 1):
            for y in range(size - 1):
                x1 = x * (spacer + point_size) + border_size + point_size
                y1 = y * (spacer + point_size) + border_size + point_size

                centerx = x1 + spacer // 2
                centery = y1 + spacer // 2

                cell_val = self.viewmodel.board.cells[y][x]

                if cell_val == -1:
                    self.canvas.create_text(
                        centerx, centery, text=" ", font=("Arial", 40)
                    )
                else:
                    self.canvas.create_text(
                        centerx,
                        centery,
                        text=str(cell_val),
                        font=("Arial", 40),
                        fill=colors[cell_val],
                    )

        # Draw edges
        for edge in self.viewmodel.board.edges:
            x1 = edge.src.row * (spacer + point_size) + border_size
            y1 = edge.src.column * (spacer + point_size) + border_size
            x2 = edge.dest.row * (spacer + point_size) + border_size + point_size
            y2 = edge.dest.column * (spacer + point_size) + border_size + point_size
            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#89B6A5",
                outline="#0A2E36",
            )


class ControlFrame(ttk.Frame):
    def __init__(self, master, viewmodel: BoardViewModel):
        super().__init__(master)
        self.viewmodel = viewmodel

        self.board_size = tk.StringVar()
        self.difficulty = tk.StringVar()

        self.build_ui()

    def new_board(self):
        size, difficulty = self.board_size.get(), self.difficulty.get()
        self.viewmodel.new_board_cmd(size, difficulty)

    def solve_board(self):
        print("solve board cmd")
        pass

    def build_ui(self):
        option_fr = ttk.Frame(self)

        row1 = ttk.Frame(option_fr)
        label1 = ttk.Label(row1, text="Board Size", width=12)
        combox1 = ttk.Combobox(
            row1,
            values=BoardViewModel.BOARD_SIZES,
            state="readonly",
            textvariable=self.board_size,
        )
        combox1.current(0)
        label1.pack(side=tk.LEFT, padx=4, pady=2)
        combox1.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row2 = ttk.Frame(option_fr)
        label2 = ttk.Label(row2, text="Difficulty", width=12)
        combox2 = ttk.Combobox(
            row2,
            values=BoardViewModel.DIFFICULTY,
            textvariable=self.difficulty,
            state="readonly",
        )
        combox2.current(0)
        label2.pack(side=tk.LEFT, padx=4, pady=2)
        combox2.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row1.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row2.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        option_fr.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        spacer = ttk.Frame(self)
        spacer.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        button_fr = ttk.Frame(self)
        new_btn = ttk.Button(button_fr, text="New", command=self.new_board)
        new_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        solve_btn = ttk.Button(button_fr, text="Solve", command=self.solve_board)
        solve_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        button_fr.pack(side=tk.TOP, fill=tk.X, pady=10)
