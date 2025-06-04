import tkinter as tk
from tkinter import Menu, Frame,filedialog
import os
import json

from ui.tileset_pane import TilesetPane
from ui.editor_pane import EditorPane
from ui.palette_pane import PalettePane
from ui.tilemap_pane import TilemapPane


def get_filename_no_extension(file_path):
        filename = os.path.basename(file_path)
        name_no_ext = os.path.splitext(filename)[0]
        return name_no_ext


class GbaTileEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GBA Tile Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)  # Set minimum window size
        
        self._autosave_after_id = None
        self._last_saved_state = None
        
        # Initialize components
        self.tileset_frame = None
        self.editor_pane = None
        self.palette_pane = None
        self.tile_map_pane = None
        
        self.create_menu()
        self.create_layout()
        self.setup_event_bindings()
        self.load_autosave_if_exists()
        self.schedule_autosave()

    
    def create_menu(self):
        """Create the main menu bar"""
        menubar = Menu(self)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Import Palette+Tileset", command=self.import_palette_and_tileset)
        file_menu.add_separator()
        file_menu.add_command(label="Export Palette+Tileset", command=self.export_palette_and_tileset)
        file_menu.add_command(label="Export Tilemap", command=self.export_tilemap)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_save)
        menubar.add_cascade(label="File", menu=file_menu)
        
        self.config(menu=menubar)
        
    def exit_save(self):
        self.autosave_project()
        self.quit()
    
    def create_layout(self):
        """Create and arrange the main UI components"""
        # Main container using PanedWindow for resizable panes
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=8, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Tileset
        self.tileset_frame = TilesetPane(main_pane, on_tile_selected=self.on_tile_selected)
        main_pane.add(self.tileset_frame, minsize=200, width=250)
        
        # Right pane - Editor and Palette
        right_pane = tk.PanedWindow(main_pane, orient=tk.VERTICAL, sashwidth=8, sashrelief=tk.RAISED)
        
        # Top right - Palette
        self.palette_pane = PalettePane(right_pane, title="Color Palette")
        right_pane.add(self.palette_pane, minsize=50, height=70)
        
        # Bottom right - Editor and Tilemap
        editor_container = Frame(right_pane)
        
        self.editor_pane = EditorPane(editor_container)
        self.editor_pane.pack(fill=tk.BOTH, expand=True)
        
        # Set up connections between components
        self.setup_component_connections()
        
        right_pane.add(editor_container)
        main_pane.add(right_pane)
        
    def load_autosave_if_exists(self):
        if os.path.exists("autosave.gtproj"):
            with open("autosave.gtproj", "r") as f:
                project_data = json.load(f)

                # Load palette
                self.palette_pane.set_palette(project_data["palette"])
                
                # Load tiles
                self.tileset_frame.tiles_data = project_data["tiles"]
                self.tileset_frame.draw_tiles()

                # Load tilemap (NEW)
                self.tile_map_pane.tile_map = [
                    [
                        (entry["tile"], entry["flip_h"], entry["flip_v"])
                        for entry in row
                    ]
                    for row in project_data["tilemap"]
                ]
                self.tile_map_pane.fill_empty_tiles()
                self.tile_map_pane.draw_map()

                print(f"Project loaded from {"autosave.gtproj"}")
            print("Loaded autosave.")
        
    def schedule_autosave(self):
        if hasattr(self, '_autosave_after_id') and self._autosave_after_id is not None:
            try:
                self.after_cancel(self._autosave_after_id)
            except ValueError:
                pass  # Ignore if the ID was invalid

        self._autosave_after_id = self.after(10000, self.autosave_project)
    
    def autosave_project(self):
        print("function_called")
        autosave_path = "autosave.gtproj"
        project_data = self.get_project_data()

        safe_data = json.dumps(project_data, default=list)
        if getattr(self, "_last_autosave_data", None) != safe_data:
            with open(autosave_path, "w") as f:
                f.write(safe_data)
            self._last_autosave_data = safe_data
            print("Autosaved project.")
        self.schedule_autosave()

            
    def get_project_data(self):
        return {
            "palette": self.palette_pane.palette,  # List of (r, g, b) tuples
            "tiles": self.tileset_frame.tiles_data,  # List of 64-pixel arrays
            "tilemap": [
                [
                    {"tile": tile_idx, "flip_h": flip_h, "flip_v": flip_v}
                    for (tile_idx, flip_h, flip_v) in row
                ]
                for row in self.tile_map_pane.tile_map
            ]
        }
        
    def save_project(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".gtproj",
            filetypes=[("GBA Tile Project", "*.gtproj")]
        )
        if not file_path:
            return

        project_data = self.get_project_data()

        with open(file_path, "w") as f:
            json.dump(project_data, f)

        print(f"Project saved to {file_path}")
        
    def load_project(self):
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("GBA Tile Project", "*.gtproj")]
        )
        if not file_path:
            return

        with open(file_path, "r") as f:
            project_data = json.load(f)

        # Load palette
        self.palette_pane.set_palette(project_data["palette"])
        
        # Load tiles
        self.tileset_frame.tiles_data = project_data["tiles"]
        self.tileset_frame.draw_tiles()

        # Load tilemap (NEW)
        self.tile_map_pane.tile_map = [
            [
                (entry["tile"], entry["flip_h"], entry["flip_v"])
                for entry in row
            ]
            for row in project_data["tilemap"]
        ]
        self.tile_map_pane.fill_empty_tiles()
        self.tile_map_pane.draw_map()

        print(f"Project loaded from {file_path}")

        
    def rgb_to_gba(self, r, g, b):
        """Convert 8-bit RGB to GBA 15-bit color (0BBBBBGG GGGRRRRR)"""
        r5 = (r >> 3) & 0x1F
        g5 = (g >> 3) & 0x1F
        b5 = (b >> 3) & 0x1F
        return (b5 << 10) | (g5 << 5) | r5
    
    def import_palette_and_tileset(self):
        from tkinter import filedialog
        import re

        file_path = filedialog.askopenfilename(
            title="Import visual_data.c",
            filetypes=[("C Source File", "*.c"), ("All files", "*.*")]
        )
        if not file_path:
            return

        with open(file_path, "r") as f:
            content = f.read()

        # Extract palette (16 entries)
        palette_matches = re.findall(r"0x([0-9A-Fa-f]{4})", content)
        if len(palette_matches) < 16:
            print("Error: Not enough palette entries found.")
            return

        def gba_to_rgb(color):
            val = int(color, 16)
            r = (val & 0x1F) << 3
            g = ((val >> 5) & 0x1F) << 3
            b = ((val >> 10) & 0x1F) << 3
            return (r, g, b)

        palette = [gba_to_rgb(c) for c in palette_matches[:16]]
        self.palette_pane.set_palette(palette)
        self.tileset_frame.set_palette(palette)
        self.editor_pane.tile_painter.set_palette(palette)

        # Extract tileset bytes
        tileset_data_match = re.search(
            r"const u8 tile_set\[\s*TILE_COUNT\s*\*\s*TILE_SIZE\s*\]\s*=\s*\{(.*?)\};",
            content, re.DOTALL
        )

        if not tileset_data_match:
            print("Error: Could not find tile_set data.")
            return

        tile_bytes = re.findall(r"0x([0-9A-Fa-f]{2})", tileset_data_match.group(1))
        tile_bytes = [int(b, 16) for b in tile_bytes]

        # Convert bytes to tile format: 2 pixels per byte (low nibble = left, high nibble = right)
        tiles = []
        for i in range(0, len(tile_bytes), 32):  # 8x8 = 64 pixels = 32 bytes
            tile = []
            for byte in tile_bytes[i:i+32]:
                left = byte & 0x0F
                right = (byte >> 4) & 0x0F
                tile.extend([left, right])
            tiles.append(tile[:64])
            
        while len(tiles) < 512:
            tiles.append([0] * 64)

        self.tileset_frame.tiles_data = tiles
        self.tileset_frame.draw_tiles()

        print(f"Imported {len(tiles)} tiles and a palette from C file.")


    def export_palette_and_tileset(self):
        """Export palette and tileset to GBA-compatible C files, only including non-empty tiles"""
        from tkinter import filedialog
        import os
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select output directory")
        if not output_dir:
            return
        
        # Find last non-empty tile
        last_non_empty = 0
        for i, tile in enumerate(self.tileset_frame.tiles_data):
            if any(pixel != 0 for pixel in tile):  # Check if tile is non-empty
                last_non_empty = i
        
        # Export palette (always all 16 colors)
        palette_path = os.path.join(output_dir, "visual_data.c")
        with open(palette_path, 'w') as f:
            f.write("#include \"visual_data.h\"\n\n")
            f.write("// Palette data\n")
            f.write("const u16 palette[16] = \n{\n")
            
            r, g, b = self.palette_pane.palette[0]
            gba_color_1 = self.rgb_to_gba(r, g, b)
                
            # First color is transparent
            f.write("    0x%04X, // Transparent\n" % gba_color_1)
            
            # Remaining colors
            for i, color in enumerate(self.palette_pane.palette[1:], 1):
                r, g, b = color
                gba_color = self.rgb_to_gba(r, g, b)
                f.write("    0x%04X, // Color %d\n" % (gba_color, i))
            f.write("};\n\n")
            
            # Export tileset (only up to last non-empty tile)
            f.write("// Tileset data (each byte = 2 pixels, right then left)\n")
            f.write("const u8 tile_set[TILE_COUNT * TILE_SIZE] = \n{\n")
            
            for tile_idx, tile in enumerate(self.tileset_frame.tiles_data[:last_non_empty + 1]):
                f.write("    // Tile %d\n    " % tile_idx)
                
                # Pack 2 pixels per byte (right then left)
                for i in range(0, len(tile), 2):
                    if i+1 < len(tile):
                        byte_val = (tile[i+1] << 4) | tile[i]
                    else:
                        byte_val = tile[i]
                    
                    f.write("0x%02X, " % byte_val)
                
                f.write("\n")
            
            f.write("};\n")
        
        # Create header file
        header_path = os.path.join(output_dir, "visual_data.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef VISUAL_DATA_H\n")
            f.write("#define VISUAL_DATA_H\n\n")
            f.write("#include \"visual.h\"\n\n")
            f.write("\n#define PALETTE_COUNT 16\n")
            f.write("#define TILE_COUNT %d\n" % (last_non_empty + 1))
            f.write("#define TILE_SIZE %d\n" % self.tileset_frame.TILE_SIZE)
            f.write("extern const u16 palette[16];\n")
            f.write("extern const u8 tile_set[TILE_COUNT * TILE_SIZE];\n")
            f.write("#endif")

    def export_tilemap(self):
        """Export tilemap to GBA-compatible C file, only including used area"""
        from tkinter import filedialog
        import os
        
        # Ask for output file
        output_path = filedialog.asksaveasfilename(
            title="Export Tilemap",
            defaultextension=".c",
            filetypes=[("C files", "*.c"), ("All files", "*.*")]
        )
        if not output_path:
            return
        
        base_path = os.path.splitext(output_path)[0]
        header_path = base_path + ".h"
        name = os.path.splitext(os.path.basename(output_path))[0]
        
        # Find used tiles and boundaries
        max_x = 0
        max_y = 0
        used_tiles = set()
        
        for y in range(self.tile_map_pane.tile_map_height):
            for x in range(self.tile_map_pane.tile_map_width):
                tile_idx, flip_h, flip_v = self.tile_map_pane.tile_map[y][x]
                if tile_idx != 0:  # Only count non-zero tiles
                    used_tiles.add(tile_idx)
                    if x > max_x:
                        max_x = x
                    if y > max_y:
                        max_y = y
        
        # Adjust dimensions (add 1 because we want count, not index)
        map_width = max_x + 1 if max_x > 0 else 1  # Minimum 1x1
        map_height = max_y + 1 if max_y > 0 else 1
        
        # Find last used tile index
        last_used_tile = max(used_tiles) if used_tiles else 0
        
        # Write tilemap C file
        with open(output_path, 'w') as f:
            f.write("#include \"%s.h\"\n\n" % name)
            f.write("// Tilemap data\n")
            f.write("const u16 tile_map[%d * %d] = \n{\n" % (map_width, map_height))
            
            for y in range(map_height):
                for x in range(map_width):
                    tile_idx, flip_h, flip_v = self.tile_map_pane.tile_map[y][x]
                    f.write("    TILE_ENTRY(%d, 0, %d, %d)," % 
                        (tile_idx, int(flip_h), int(flip_v)))
                
                f.write("\n")
            
            f.write("};\n")
        
        # Write tilemap header file
        with open(header_path, 'w') as f:
            f.write("#ifndef %s_H\n" % name.upper())
            f.write("#define %s_H\n\n" % name.upper())
            f.write("#include \"visual.h\"\n\n")
            f.write("extern const u16 tile_map[%d * %d];\n" % (map_width, map_height))
            f.write("\n#define TILE_MAP_WIDTH %d\n" % map_width)
            f.write("#define TILE_MAP_HEIGHT %d\n" % map_height)
            f.write("#define LAST_USED_TILE %d\n" % last_used_tile)
            f.write("#endif")

    def setup_component_connections(self):
        """Connect all the UI components together"""
        # Connect palette to tileset and editor
        self.palette_pane.add_listener(self.tileset_frame)
        self.palette_pane.add_listener(self.editor_pane.tile_painter)
        
        # Set initial palette
        self.tileset_frame.set_palette(self.palette_pane.palette)
        self.editor_pane.tile_painter.set_palette(self.palette_pane.palette)
        self.editor_pane.tile_painter.set_active_color_index(self.palette_pane.active_index)
        
        # Set up tile update callback
        self.editor_pane.tile_painter.set_on_tile_updated(self.on_tile_updated)
        
        # Create tilemap pane
        self.tile_map_pane = TilemapPane(
            self.editor_pane.mapper_tab, 
            tile_data_source=self.tileset_frame, 
            palette_source=self.palette_pane
        )
        self.tile_map_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_event_bindings(self):
        """Set up keyboard shortcuts and other event bindings"""
        # Zoom controls
        self.bind("<Control-plus>", lambda e: self.tileset_frame.zoom_in())
        self.bind("<Control-minus>", lambda e: self.tileset_frame.zoom_out())
        self.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
        
        # Common shortcuts        
        self.bind("<Control-s>", lambda e: self.save_project())
        self.bind("<Control-o>", lambda e: self.load_project())
    
    def on_ctrl_mousewheel(self, event):
        """Handle Ctrl+MouseWheel for zooming"""
        if event.delta > 0:
            self.tileset_frame.zoom_in()
        else:
            self.tileset_frame.zoom_out()
    
    def on_tile_selected(self, index, pixels):
        """Handle tile selection from tileset"""
        self.editor_pane.tile_painter.load_tile(pixels, tile_index=index)
    
    def on_tile_updated(self, new_pixels):
        """Handle tile updates from editor"""
        idx = self.editor_pane.tile_painter.current_tile_index
        if 0 <= idx < len(self.tileset_frame.tiles_data):
            self.tileset_frame.tiles_data[idx] = new_pixels
            self.tileset_frame.draw_tiles()
            self.tile_map_pane.notify_tile_update(idx)  # Update tilemap if this tile is used


if __name__ == "__main__":
    app = GbaTileEditor()
    app.mainloop()