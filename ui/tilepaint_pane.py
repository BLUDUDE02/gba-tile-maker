import tkinter as tk

class TilePainterPane(tk.Frame):
    def __init__(self, master, on_tile_updated=None):
        super().__init__(master)
        self.on_tile_updated = on_tile_updated
        self.tile_pixels = [0] * 64
        self.history = []  # Undo history stack

        self.rows = 8
        self.cols = 8
        self.cell_size = 1
        self.offset_x = 0
        self.offset_y = 0
        self.palette_colors = [(255, 255, 255)] * 16
        self.active_color_index = 1

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.canvas.bind("<Configure>", self.redraw_grid)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.bind_all("<Control-z>", self.undo)  # Bind Ctrl+Z

        self.current_tile_index = 0
        self.mouse_down = False
        self.last_painted = set()  # Prevent repainting same cell during drag

    def load_tile(self, pixels, tile_index=None):
        self.tile_pixels = pixels.copy()
        if tile_index is not None:
            self.current_tile_index = tile_index
        self.redraw_grid()

    def set_on_tile_updated(self, callback):
        self.on_tile_updated = callback

    def push_undo(self):
        self.history.append(self.tile_pixels.copy())
        if len(self.history) > 50:  # Limit history size
            self.history.pop(0)

    def undo(self, event=None):
        if self.history:
            self.tile_pixels = self.history.pop()
            self.redraw_grid()
            if self.on_tile_updated:
                self.on_tile_updated(self.tile_pixels)

    def paint_pixel(self, x, y):
        idx = y * 8 + x
        if self.tile_pixels[idx] != self.active_color_index:
            self.tile_pixels[idx] = self.active_color_index
            return True
        return False

    def set_palette(self, colors):
        self.palette_colors = colors
        self.redraw_grid()

    def set_active_color_index(self, index):
        self.active_color_index = index

    def on_click(self, event):
        x, y = self.event_to_coords(event)
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.push_undo()
            self.last_painted.clear()
            self.paint_and_update(x, y)

    def on_drag(self, event):
        x, y = self.event_to_coords(event)
        if 0 <= x < self.cols and 0 <= y < self.rows:
            if (x, y) not in self.last_painted:
                self.paint_and_update(x, y)
                self.last_painted.add((x, y))

    def on_release(self, event):
        self.last_painted.clear()

    def paint_and_update(self, x, y):
        changed = self.paint_pixel(x, y)
        if changed:
            self.redraw_grid()
            if self.on_tile_updated:
                self.on_tile_updated(self.tile_pixels)

    def event_to_coords(self, event):
        x = (event.x - self.offset_x) // self.cell_size
        y = (event.y - self.offset_y) // self.cell_size
        return x, y

    def best_contrast_bw(self, rgb):
        r, g, b = rgb
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        return 'black' if luminance > 0.5 else 'white'

    def redraw_grid(self, event=None):
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.cell_size = min(width // self.cols, height // self.rows)
        self.offset_x = (width - (self.cell_size * self.cols)) // 2
        self.offset_y = (height - (self.cell_size * self.rows)) // 2

        for y in range(self.rows):
            for x in range(self.cols):
                idx = y * self.cols + x
                index = self.tile_pixels[idx]
                rgb = self.palette_colors[index]
                hex_color = self.rgb_to_hex(rgb)

                x1 = self.offset_x + x * self.cell_size
                y1 = self.offset_y + y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='red',
                    fill=hex_color
                )
                text_color = self.best_contrast_bw(rgb)
                self.canvas.create_text(
                    x1 + self.cell_size // 2,
                    y1 + self.cell_size // 2,
                    text=f"{index:X}",
                    font=("Courier", int(self.cell_size * 0.4)),
                    fill=text_color
                )

    def rgb_to_hex(self, rgb):
        return "#{:02X}{:02X}{:02X}".format(*rgb)