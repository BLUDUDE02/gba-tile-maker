import tkinter as tk

class TilesetPane(tk.Frame):
    TOTAL_TILES = 512
    TILE_SIZE = 8  # Original tile pixel size
    MIN_SCALE = 3
    MAX_SCALE = 6

    def __init__(self, master, palette_pane=None, on_tile_selected=None):
        super().__init__(master)
        self.on_tile_selected = on_tile_selected
        self.palette_pane = palette_pane
        self.active_tile_index = 0
        self.tiles_data = [[0]*64 for _ in range(self.TOTAL_TILES)]
        self.bg = 'white'
        self.scale = 4
        self.tiles_per_row = 8
        
        # Initialize palette colors with default
        self.palette_colors = [(0, 0, 0)] * 16  # Default 16-color palette
        
        self.label = tk.Label(self, text="Tileset", font=("Arial", 12, "bold"))
        self.label.pack(side="top", pady=4)

        canvas_wrapper = tk.Frame(self)
        canvas_wrapper.pack(side='top', fill='both', expand=True)

        self.canvas = tk.Canvas(canvas_wrapper, bg='white')
        self.scrollbar = tk.Scrollbar(canvas_wrapper, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_click)  # For click-and-drag selection

        self.update_zoom_layout()

    def set_palette(self, palette_colors):
        """Update the palette and redraw all tiles with new colors"""
        if palette_colors is None or len(palette_colors) == 0:
            return
            
        self.palette_colors = palette_colors
        
        # Update background color based on palette[0]
        try:
            base_color = self.palette_colors[0]
            base_color_hex = f"#{base_color[0]:02x}{base_color[1]:02x}{base_color[2]:02x}"
            self.canvas.configure(bg=base_color_hex)
        except (IndexError, AttributeError):
            pass
            
        self.draw_tiles()
        
    def set_active_color_index(self, index):
        """Currently not used, but kept for interface compatibility"""
        pass

    def draw_tiles(self):
        """Redraw all tiles with current palette and tileset data"""
        self.canvas.delete("all")
        tile_w = self.TILE_SIZE * self.scale
        tile_h = tile_w
        tiles_per_row = self.tiles_per_row
        
        # Determine text color based on background
        text_color = self.best_contrast_bw(self.palette_colors[0]) if self.palette_colors else 'black'
        
        for index in range(self.TOTAL_TILES):
            col = index % tiles_per_row
            row = index // tiles_per_row
            x = col * tile_w
            y = row * tile_h
            
            # Draw tile background and index text
            self.canvas.create_rectangle(x, y, x + tile_w, y + tile_h, outline='gray')
            self.canvas.create_text(
                x + tile_w // 2,
                y + tile_h // 2,
                text=f"{index:03X}",
                font=('Courier', max(8, int(8 * self.scale * 0.25))),
                fill=text_color
            )

            # Draw pixel overlay if tile not all zero
            pixels = self.tiles_data[index]
            if any(pixel != 0 for pixel in pixels) and self.palette_colors:
                pixel_size = max(1, tile_w // 8)
                for i, color_index in enumerate(pixels):
                    px = i % 8
                    py = i // 8

                    # Safely get color from palette
                    if 0 <= color_index < len(self.palette_colors):
                        color = self.palette_colors[color_index]
                        color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    else:
                        color_hex = "#FF00FF"  # Magenta for invalid indices

                    self.canvas.create_rectangle(
                        x + px * pixel_size,
                        y + py * pixel_size,
                        x + (px + 1) * pixel_size,
                        y + (py + 1) * pixel_size,
                        fill=color_hex,
                        outline=""
                    )

            # Highlight active tile
            if index == self.active_tile_index:
                self.canvas.create_rectangle(x, y, x + tile_w, y + tile_h, outline='red', width=2)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def update_tileset(self, tiles_data):
        """Update the entire tileset data and redraw"""
        if tiles_data is None or len(tiles_data) != self.TOTAL_TILES:
            return
            
        self.tiles_data = tiles_data
        self.draw_tiles()

    def update_tile(self, tile_index, tile_data):
        """Update a single tile and redraw if visible"""
        if 0 <= tile_index < self.TOTAL_TILES:
            self.tiles_data[tile_index] = tile_data
            # Only redraw if this tile is currently visible
            visible_start = int(self.canvas.canvasy(0) // (self.TILE_SIZE * self.scale))
            visible_end = visible_start + (self.canvas.winfo_height() // (self.TILE_SIZE * self.scale)) + 1
            
            row = tile_index // self.tiles_per_row
            if visible_start <= row <= visible_end:
                self.draw_tiles()

    def on_palette_changed(self, palette):
        """Handle palette updates from palette pane"""
        self.set_palette(palette)

    def on_click(self, event):
        """Handle tile selection via mouse click"""
        tile_w = self.TILE_SIZE * self.scale
        tile_h = tile_w

        # Convert visible y to full canvas y to account for scrolling
        y = self.canvas.canvasy(event.y)

        col = event.x // tile_w
        row = int(y // tile_h)

        index = row * self.tiles_per_row + col

        if 0 <= index < self.TOTAL_TILES:
            self.active_tile_index = index
            if self.on_tile_selected:
                self.on_tile_selected(index, self.tiles_data[index])
            self.draw_tiles()

    def update_zoom_layout(self):
        """Update layout when zoom level changes"""
        self.canvas.update_idletasks()
        available_width = self.canvas.winfo_width()
        self.tiles_per_row = max(1, (available_width // (self.TILE_SIZE * self.scale)) - 1)
        self.draw_tiles()

    def on_resize(self, event):
        """Handle window resize events"""
        available_width = event.width
        new_tiles_per_row = max(1, (available_width // (self.TILE_SIZE * self.scale)) - 1)

        if new_tiles_per_row != self.tiles_per_row:
            self.tiles_per_row = new_tiles_per_row
            self.draw_tiles()

    def zoom_in(self):
        """Zoom in (increase scale)"""
        if self.scale < self.MAX_SCALE:
            self.scale += 1
            self.update_zoom_layout()

    def zoom_out(self):
        """Zoom out (decrease scale)"""
        if self.scale > self.MIN_SCALE:
            self.scale -= 1
            self.update_zoom_layout()
            
    def best_contrast_bw(self, rgb):
        """
        Given an (R,G,B) tuple with each component in 0-255,
        returns 'black' or 'white' string for best contrast.
        """
        r, g, b = rgb
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        return 'black' if luminance > 0.5 else 'white'