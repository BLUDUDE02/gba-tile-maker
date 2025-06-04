import tkinter as tk
from tkinter import colorchooser

class PalettePane(tk.Frame):
    PALETTE_SIZE = 16  # Standard 16-color palette
    BOX_SIZE = 20      # Size of each color box
    BORDER_WIDTH = 2   # Width of selection border

    def __init__(self, master, title="Palette"):
        super().__init__(master)
        self.color_boxes = []
        self.palette = [(0, 0, 0)] * self.PALETTE_SIZE  # Initialize with black
        self.active_index = 0
        self.listeners = []

        # Add title label
        self.title_label = tk.Label(self, text=title, font=("Arial", 10, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=self.PALETTE_SIZE, pady=(0, 5))

        # Create color boxes
        for i in range(self.PALETTE_SIZE):
            # Create container frame for each color box
            container = tk.Frame(self)
            container.grid(row=1, column=i, padx=2)

            # Create the actual color box canvas
            box = tk.Canvas(
                container, 
                width=self.BOX_SIZE, 
                height=self.BOX_SIZE, 
                highlightthickness=self.BORDER_WIDTH
            )
            box.pack()
            
            # Bind events
            box.bind("<Button-1>", lambda e, i=i: self.set_active_color(i))
            box.bind("<Button-3>", lambda e, i=i: self.open_color_picker(i))
            box.bind("<Double-Button-1>", lambda e, i=i: self.open_color_picker(i))  # Double-click also opens picker

            self.color_boxes.append(box)

        self.set_active_color(0)
        self.update_all_colors()

    def add_listener(self, listener):
        """Add a listener to be notified of palette changes"""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener):
        """Remove a listener from notification list"""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def notify_active_color_changed(self):
        """Notify all listeners about active color change"""
        for listener in self.listeners:
            if hasattr(listener, 'set_active_color_index'):
                listener.set_active_color_index(self.active_index)

    def notify_palette_changed(self):
        """Notify all listeners about palette change"""
        for listener in self.listeners:
            if hasattr(listener, 'set_palette'):
                listener.set_palette(self.palette)
            elif hasattr(listener, 'on_palette_changed'):
                listener.on_palette_changed(self.palette)

    def set_active_color(self, index):
        """Set the currently active color and update UI"""
        if 0 <= index < self.PALETTE_SIZE:
            self.active_index = index
            
            # Update all box borders
            for i, box in enumerate(self.color_boxes):
                border_color = 'red' if i == index else 'gray'
                box.config(highlightbackground=border_color)
                
            self.notify_active_color_changed()

    def open_color_picker(self, index):
        """Open color picker dialog for the specified color index"""
        current_color = self.rgb_to_hex(self.palette[index])
        result = colorchooser.askcolor(
            initialcolor=current_color,
            title=f"Select Color {index}",
            parent=self
        )
        
        if result[0]:  # User didn't cancel
            self.set_color(index, result[0])

    def set_color(self, index, rgb_tuple):
        """Set color at specified index and notify listeners"""
        if 0 <= index < self.PALETTE_SIZE:
            # Convert to 5-bit GBA color if needed (or keep 8-bit)
            r, g, b = map(int, rgb_tuple)
            self.palette[index] = (r, g, b)
            self.update_color_box(index)
            self.notify_palette_changed()

    def set_palette(self, new_palette):
        """Set the entire palette at once"""
        if len(new_palette) == self.PALETTE_SIZE:
            self.palette = [tuple(color) for color in new_palette]
            self.update_all_colors()
            self.notify_palette_changed()

    def update_color_box(self, index):
        """Update visual representation of a single color box"""
        if 0 <= index < self.PALETTE_SIZE:
            color = self.rgb_to_hex(self.palette[index])
            self.color_boxes[index].config(bg=color)

    def update_all_colors(self):
        """Update visual representation of all color boxes"""
        for i in range(self.PALETTE_SIZE):
            self.update_color_box(i)

    @staticmethod
    def rgb_to_hex(rgb):
        """Convert RGB tuple to hex color string"""
        return "#{:02X}{:02X}{:02X}".format(*rgb)

    def get_active_color_index(self):
        """Get the currently active color index"""
        return self.active_index

    def get_active_color_rgb(self):
        """Get RGB tuple of the active color"""
        return self.palette[self.active_index]