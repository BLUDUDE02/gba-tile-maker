import tkinter as tk
from tkinter import ttk
from ui.tilepaint_pane import TilePainterPane

class EditorPane(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.label = tk.Label(self, text="Tilemap", font=("Arial", 12, "bold"))
        self.label.pack(side="top", pady=4)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Create the two tabs
        self.mapper_tab = tk.Frame(self.notebook, bg="white")
        self.pixel_art_tab = tk.Frame(self.notebook, bg="white")  

        # Add tabs to notebook
        self.notebook.add(self.pixel_art_tab, text="Pixel Art")
        self.notebook.add(self.mapper_tab, text="Mapper")

        # Placeholder label inside each tab
        tk.Label(self.mapper_tab, text="Mapper View").pack(pady=20)


        
        tk.Label(self.pixel_art_tab, text="Pixel Art View").pack(pady=20)
        self.tile_painter = TilePainterPane(self.pixel_art_tab)
        self.tile_painter.pack(fill='both', expand=True, pady=10) 

