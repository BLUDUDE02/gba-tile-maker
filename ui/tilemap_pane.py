import tkinter as tk
from tkinter import Scrollbar, Canvas

class TilemapPane(tk.Frame):
    def __init__(self, master, tile_data_source, palette_source, tile_size=8):
        super().__init__(master)
        self.tile_data_source = tile_data_source
        self.palette_source = palette_source

        self.tile_map_width = 32
        self.tile_map_height = 32
        self.tile_size = tile_size
        self.scale = 4

        self.flip_h = False
        self.flip_v = False

        self.tile_map = [[(0, False, False) for _ in range(self.tile_map_width)] for _ in range(self.tile_map_height)]

        self.canvas = tk.Canvas(self, bg='white')
        self.h_scrollbar = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.v_scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar.pack(side='bottom', fill='x')
        self.v_scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        # Bind events
        self.canvas.bind("<Button-1>", self.place_tile)
        self.canvas.bind("<B1-Motion>", self.place_tile)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())  # Focus on mouse enter
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)
        
        # Bind key events to the canvas
        self.canvas.bind("<Key>", self.on_keypress)
        self.canvas.focus_set()  # Set initial focus
        
        # Store the current palette version for cache invalidation
        self.current_palette_version = 0

        self.tile_image_cache = {}
        self._image_refs = []

        self.hover_x = -1
        self.hover_y = -1

        self.fill_empty_tiles()
        self.draw_map()

    def render_tile_image(self, tile_index, flip_h, flip_v):
        """Render a tile image with current palette, using versioned cache key"""
        # Include palette version in cache key
        key = (tile_index, flip_h, flip_v, self.scale, self.current_palette_version)
        
        if key in self.tile_image_cache:
            return self.tile_image_cache[key]

        try:
            tile = self.tile_data_source.tiles_data[tile_index]
        except (IndexError, AttributeError):
            tile = [0] * (self.tile_size * self.tile_size)

        size = self.tile_size
        scaled_size = size * self.scale
        img = tk.PhotoImage(width=scaled_size, height=scaled_size)

        for i, color_index in enumerate(tile):
            px = i % size
            py = i // size
            if flip_h:
                px = size - 1 - px
            if flip_v:
                py = size - 1 - py
            try:
                color = self.palette_source.palette[color_index]
            except (IndexError, AttributeError):
                color = (255, 0, 255)  # Fallback color (magenta)
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            img.put(hex_color, to=(px * self.scale, py * self.scale, 
                                  (px + 1) * self.scale, (py + 1) * self.scale))

        self.tile_image_cache[key] = img
        return img
    
    def draw_map(self):
        self.canvas.delete("all")
        self._image_refs = []
        size = self.tile_size * self.scale

        for y in range(self.tile_map_height):
            for x in range(self.tile_map_width):
                tile_index, flip_h, flip_v = self.tile_map[y][x]
                img = self.render_tile_image(tile_index, flip_h, flip_v)
                self.canvas.create_image(x * size, y * size, image=img, anchor='nw')
                self._image_refs.append(img)

        width = self.tile_map_width * size
        height = self.tile_map_height * size

        for x in range(self.tile_map_width + 1):
            self.canvas.create_line(x * size, 0, x * size, height, fill='red')
        for y in range(self.tile_map_height + 1):
            self.canvas.create_line(0, y * size, width, y * size, fill='red')

        self.canvas.config(scrollregion=(0, 0, width, height))

    def place_tile(self, event):
        grid_size = self.tile_size * self.scale
        x = int(self.canvas.canvasx(event.x) // grid_size)
        y = int(self.canvas.canvasy(event.y) // grid_size)

        if 0 <= x < self.tile_map_width and 0 <= y < self.tile_map_height:
            tile_index = self.tile_data_source.active_tile_index
            h_flip = self.flip_h
            v_flip = self.flip_v
            self.tile_map[y][x] = (tile_index, h_flip, v_flip)
            self.draw_map()

    def on_mouse_move(self, event):
        grid_size = self.tile_size * self.scale
        x = int(self.canvas.canvasx(event.x) // grid_size)
        y = int(self.canvas.canvasy(event.y) // grid_size)
        
        if 0 <= x < self.tile_map_width and 0 <= y < self.tile_map_height:
            self.hover_x = x
            self.hover_y = y
            # Set focus when mouse moves over canvas to ensure key presses work
            self.canvas.focus_set()

    def on_keypress(self, event):
        # Only process if we have a valid hover position
        if not (0 <= self.hover_x < self.tile_map_width and 
                0 <= self.hover_y < self.tile_map_height):
            return

        tile_index, flip_h, flip_v = self.tile_map[self.hover_y][self.hover_x]
        
        if event.keysym.lower() == 'h':
            flip_h = not flip_h
            self.tile_map[self.hover_y][self.hover_x] = (tile_index, flip_h, flip_v)
            self.draw_map()
        elif event.keysym.lower() == 'v':
            flip_v = not flip_v
            self.tile_map[self.hover_y][self.hover_x] = (tile_index, flip_h, flip_v)
            self.draw_map()
        elif event.keysym.lower() == 'space':
            # Bonus: Space to place current tile with current flip settings
            tile_index = self.tile_data_source.active_tile_index
            self.tile_map[self.hover_y][self.hover_x] = (tile_index, flip_h, flip_v)
            self.draw_map()


    def on_zoom(self, event):
        if event.delta > 0:
            self.scale = min(self.scale + 1, 8)
        else:
            self.scale = max(self.scale - 1, 1)
        self.tile_image_cache.clear()
        self.draw_map()

    def fill_empty_tiles(self):
        for y in range(self.tile_map_height):
            for x in range(self.tile_map_width):
                tile_index, flip_h, flip_v = self.tile_map[y][x]
                if (tile_index is None or 
                    tile_index < 0 or 
                    not hasattr(self.tile_data_source, 'tiles_data') or
                    tile_index >= len(self.tile_data_source.tiles_data)):
                    self.tile_map[y][x] = (0, False, False)

    def set_active_tile(self, tile_index):
        self.tile_data_source.active_tile_index = tile_index

    def update_tile_data(self, tile_data):
        """Update the tileset and refresh all tiles that use the updated tiles"""
        old_tile_data = self.tile_data_source
        self.tile_data_source = tile_data
        
        # If the number of tiles changed, validate all tile indices
        if (hasattr(old_tile_data, 'tiles_data') and 
            hasattr(tile_data, 'tiles_data') and 
            len(old_tile_data.tiles_data) != len(tile_data.tiles_data)):
            self.fill_empty_tiles()
        
        # Clear the entire cache as tile data may have changed
        self.tile_image_cache.clear()
        self.draw_map()

    def update_palette(self, palette):
        """Update the palette and refresh all tiles to reflect color changes"""
        self.palette_source = palette
        self.current_palette_version += 1  # Increment version to invalidate cache
        
        # Clear the entire image cache as all colors may have changed
        self.tile_image_cache.clear()
        
        # Redraw the entire map with new colors
        self.draw_map()

    def notify_tile_update(self, tile_index):
        """Update specific tile in the cache and redraw affected tiles"""
        # Remove all cached variants of this tile index
        keys_to_remove = [k for k in self.tile_image_cache if k[0] == tile_index]
        for k in keys_to_remove:
            del self.tile_image_cache[k]
        
        # Redraw all tiles that use this tile index
        need_redraw = False
        for y in range(self.tile_map_height):
            for x in range(self.tile_map_width):
                if self.tile_map[y][x][0] == tile_index:
                    need_redraw = True
                    break
            if need_redraw:
                break
        
        if need_redraw:
            self.draw_map()