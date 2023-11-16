import tkinter as tk
from tkinter import ttk
from typing import Tuple
from tkinter import font as tkfont
import sv_ttk
from PIL import Image, ImageTk
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
        self.title("SlitherLink")

        self.board = BoardFrame(self, self.viewmodel)
        self.board.pack(side=tk.LEFT, fill=tk.Y)

        self.controls = ControlFrame(self, self.viewmodel)
        self.controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # subcribe when board changes
        self.viewmodel.add_board_changed_callback(self.draw_board)
        self.viewmodel.add_board_changed_callback(self.controls.update_stats)
        self.viewmodel.add_graph_changed_callback(self.draw_graph)

    def draw_graph(self):
        self.board.redraw_edges()

    def draw_board(self):
        self.board.redraw()


class BoardFrame(ttk.Frame):
    TAGS = ["cells", "edges", "cells"]

    def __init__(self, master, viewmodel: BoardViewModel):
        super().__init__(master, width=600, height=600)
        self.base_font = tkfont.Font(family="Arial", size=12)

        self.viewmodel = viewmodel
        self.canvas = tk.Canvas(
            self,
            bg="white",
            bd=0,
            highlightthickness=0,
        )
        self.bind("<Configure>", self.__configure)

        self.draw_intro("assets/intro.png")
        self.canvas.pack(side=tk.LEFT)

    def __configure(self, event):
        """Make canvas alway a square"""
        self.canvas.config(height=event.height)
        self.canvas.config(width=event.height)

    def draw_intro(self, filepath: str):
        img = Image.open(filepath)
        self.photo = ImageTk.PhotoImage(img)  # keep a reference

        self.canvas.create_rectangle(0, 0, img.width, img.height, fill="red")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

    def redraw_edges(self):
        rows = self.viewmodel.board.rows
        columns = self.viewmodel.board.columns

        self.size = size = max(rows, columns) + 1
        self.border_size = border_size = 4
        self.canvas_size = canvas_size = self.canvas.winfo_width()
        self.point_size = point_size = (canvas_size - 2 * border_size) / (8 * size - 7)
        self.spacer = spacer = 7 * point_size
        self.colors = ["#44222F", "#21300D", "#B4DC7F", "#3C3D00"]

        self.font_size = font_size = min(int(spacer // 2), 48)
        self.base_font.config(size=font_size)
        self.font = self.base_font

        self.canvas.delete("edges")
        for src, neighbors in self.viewmodel.board.graph.items():
            for dest in neighbors:
                self.draw_edge(src, dest)

    def redraw(self, tags=TAGS):
        rows = self.viewmodel.board.rows
        columns = self.viewmodel.board.columns

        self.size = size = max(rows, columns) + 1
        self.border_size = border_size = 4
        self.canvas_size = canvas_size = self.canvas.winfo_width()
        self.point_size = point_size = (canvas_size - 2 * border_size) / (8 * size - 7)
        self.spacer = spacer = 7 * point_size
        self.colors = ["#44222F", "#21300D", "#B4DC7F", "#3C3D00"]

        self.font_size = font_size = min(int(spacer // 2), 48)
        self.base_font.config(size=font_size)
        self.font = self.base_font
        self.draw_background()

        self.canvas.delete("all")

        # Draw point grid
        for x in range(columns + 1):
            for y in range(rows + 1):
                self.draw_node(x, y)

        cells = self.viewmodel.board.cells
        for x in range(columns):
            for y in range(rows):
                self.draw_cell(x, y, cells)
        for src, neighbors in self.viewmodel.board.graph.items():
            for dest in neighbors:
                self.draw_edge(src, dest)

    def draw_background(self):
        self.canvas.create_rectangle(
            1,
            1,
            self.canvas.winfo_width() - 1,
            self.canvas.winfo_height() - 1,
            fill="#F7F9F9",
            outline="#78D5D7",
            width=2,
        )

    def draw_cell(self, x, y, cells):
        x1 = x * (self.spacer + self.point_size) + self.border_size + self.point_size
        y1 = y * (self.spacer + self.point_size) + self.border_size + self.point_size
        centerx = x1 + self.spacer // 2
        centery = y1 + self.spacer // 2

        cell_val = cells[y][x].value

        if cell_val == -1:
            self.canvas.create_text(centerx, centery, text=" ", font=self.font)
        else:
            self.canvas.create_text(
                centerx,
                centery,
                text=str(cell_val),
                font=self.font,
                fill=self.colors[cell_val],
                tags="cells",
            )

    def draw_node(self, x, y):
        x1 = x * (self.spacer + self.point_size) + self.border_size
        y1 = y * (self.spacer + self.point_size) + self.border_size

        self.canvas.create_rectangle(
            x1,
            y1,
            x1 + self.point_size,
            y1 + self.point_size,
            fill="#D56F3E",
            tags="nodes",
        )

    def draw_edge(self, src, dest):
        y1 = src.row * (self.spacer + self.point_size) + self.border_size
        x1 = src.column * (self.spacer + self.point_size) + self.border_size

        y2 = (
            dest.row * (self.spacer + self.point_size)
            + self.border_size
            + self.point_size
        )
        x2 = (
            dest.column * (self.spacer + self.point_size)
            + self.border_size
            + self.point_size
        )
        self.canvas.create_rectangle(
            x1, y1, x2, y2, fill="#89B6A5", outline="#0A2E36", tags="edges"
        )


class ControlFrame(ttk.Frame):
    def __init__(self, master, viewmodel: BoardViewModel):
        super().__init__(master)
        self.viewmodel = viewmodel

        self.board_size = tk.StringVar()
        self.difficulty = tk.StringVar()
        self.index = tk.StringVar()
        self.animation = tk.BooleanVar(value=False)

        self.animation.set(False)

        self.time = tk.StringVar(value="0.000 ms")
        self.clauses = tk.StringVar(value="0")
        self.variables = tk.StringVar(value="0")
        self.retried = tk.StringVar(value="0")

        self.build_ui()

    def new_board(self):
        self.solve_btn["state"] = tk.DISABLED
        size = self.board_size.get()
        diff = self.difficulty.get()
        index = self.index.get()
        self.viewmodel.new_board_cmd(size, diff, index)
        self.solve_btn["state"] = tk.NORMAL

    def solve_board(self):
        self.solve_btn["state"] = tk.DISABLED
        self.new_btn["state"] = tk.DISABLED
        self.cancel_btn["state"] = tk.NORMAL

        animation = self.animation.get()

        def done():
            self.new_btn["state"] = tk.NORMAL
            self.solve_btn["state"] = tk.NORMAL
            self.cancel_btn["state"] = tk.DISABLED

        self.viewmodel.solve_board_cmd(done_callback=done, animation=animation)

    def cancel(self):
        self.solve_btn["state"] = tk.DISABLED
        self.new_btn["state"] = tk.DISABLED
        self.cancel_btn["state"] = tk.DISABLED

        def done():
            self.new_btn["state"] = tk.NORMAL
            self.solve_btn["state"] = tk.NORMAL
            self.cancel_btn["state"] = tk.DISABLED

        self.viewmodel.cancel_cmd(done_callback=done)

    def update_stats(self):
        self.time.set(f"{(self.viewmodel.stats.time * 1000):.2f} ms")
        self.clauses.set(f"{self.viewmodel.stats.clauses}")
        self.variables.set(f"{self.viewmodel.stats.variables}")
        self.retried.set(f"{self.viewmodel.stats.retried}")
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

        row10 = ttk.Frame(option_fr)
        label10 = ttk.Label(row10, text="Difficulty", width=12)
        combox10 = ttk.Combobox(
            row10,
            values=BoardViewModel.DIFFICULTY,
            state="readonly",
            textvariable=self.difficulty,
        )
        combox10.current(0)
        label10.pack(side=tk.LEFT, padx=4, pady=2)
        combox10.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row11 = ttk.Frame(option_fr)
        label11 = ttk.Label(row11, text="Puzzle Index", width=12)
        combox11 = ttk.Combobox(
            row11,
            values=BoardViewModel.NO_PUZZLES,
            state="readonly",
            textvariable=self.index,
        )
        combox11.current(0)
        label11.pack(side=tk.LEFT, padx=4, pady=2)
        combox11.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row12 = ttk.Frame(option_fr)
        label12 = ttk.Label(row12, text="Animation", width=12)
        combox12 = ttk.Combobox(
            row12,
            values=BoardViewModel.ANIMATION,
            state="readonly",
            textvariable=self.animation,
        )
        combox12.current(0)
        label12.pack(side=tk.LEFT, padx=4, pady=2)
        combox12.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row2 = ttk.Frame(option_fr)
        label2 = ttk.Label(row2, text="Time", width=12)
        timelabel = ttk.Label(row2, text="0", textvariable=self.time)
        label2.pack(side=tk.LEFT, padx=4, pady=2)
        timelabel.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row3 = ttk.Frame(option_fr)
        label3 = ttk.Label(row3, text="Clauses", width=12)
        label3_val = ttk.Label(row3, text="0", textvariable=self.clauses)
        label3.pack(side=tk.LEFT, padx=4, pady=2)
        label3_val.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row4 = ttk.Frame(option_fr)
        label4 = ttk.Label(row4, text="Variables", width=12)
        label4_val = ttk.Label(row4, text="0", textvariable=self.variables)
        label4.pack(side=tk.LEFT, padx=4, pady=2)
        label4_val.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row5 = ttk.Frame(option_fr)
        label5 = ttk.Label(row5, text="Retried", width=12)
        label5_val = ttk.Label(row5, text="0", textvariable=self.retried)
        label5.pack(side=tk.LEFT, padx=4, pady=2)
        label5_val.pack(side=tk.RIGHT, padx=2, pady=2, expand=True, fill=tk.X)

        row1.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row10.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row11.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row12.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row2.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row3.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row4.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        row5.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        option_fr.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        spacer = ttk.Frame(self)
        spacer.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        cancel_ft = ttk.Frame(self)
        cancel_btn = ttk.Button(
            cancel_ft,
            text="Cancel",
            command=self.cancel,
            state=tk.DISABLED,
        )
        cancel_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        button_fr = ttk.Frame(self)
        new_btn = ttk.Button(button_fr, text="New", command=self.new_board)
        new_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        solve_btn = ttk.Button(button_fr, text="Solve", command=self.solve_board)
        solve_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.new_btn = new_btn
        self.solve_btn = solve_btn
        self.cancel_btn = cancel_btn

        button_fr.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))
        cancel_ft.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
