import json, os, pygame
from scripts.core.utils import load_image

class Tileset:
    def __init__(self, path: str, source_tile_size=128, render_tile_size=16):
        self.path: str = path
        self.source_tile_size: int = source_tile_size
        self.render_tile_size: int = render_tile_size
        self.name: str = os.path.splitext(os.path.basename(path))[0]
        self.image, self.image_w, self.image_h = load_image(path)

        self.tiles = []
        self.slice_tileset()

    def slice_tileset(self):
        cols = self.image_w // self.source_tile_size
        rows = self.image_h // self.source_tile_size

        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    col * self.source_tile_size,
                    row * self.source_tile_size,
                    self.source_tile_size,
                    self.source_tile_size
                )

                tile = self.image.subsurface(rect).copy()
                tile = pygame.transform.scale(
                    tile,
                    (self.render_tile_size, self.render_tile_size)
                )

                self.tiles.append(tile)

    def get_tile(self, tile_idx: int):
        if not self.tiles: return None
        tile_idx = max(0, min(tile_idx, len(self.tiles) - 1))
        return self.tiles[tile_idx]
    
class Tilemap:
    def __init__(self, level_path: str, tileset_dir: str, level_name: str = "level_1"):
        self.level_path = level_path
        self.tileset_dir = tileset_dir
        self.level_name = level_name
        self.source_tile_size: int = 128

        self.data = self.load_json()
        self.level = self.data["levels"][self.level_name]
        self.tile_size = self.level.get("tile_size", self.data.get("tile_size", 16))
        self.width = self.level.get("width", 0)
        self.height = self.level.get("height", 0)

        self.tilesets = self.load_tilesets()

    def load_json(self):
        with open(self.level_path, "r") as f:
            return json.load(f)

    def load_tilesets(self):
        tilesets = {}

        for filename in os.listdir(self.tileset_dir):
            if not filename.lower().endswith(".png"):
                continue

            path = os.path.join(self.tileset_dir, filename)
            tileset = Tileset(
                path,
                source_tile_size=self.source_tile_size,
                render_tile_size=self.tile_size
            )

            tilesets[tileset.name] = tileset

        return tilesets

    def get_tile_surface(self, cell):
        if cell == 0:
            return None

        tileset_name = cell["tileset"]
        tile_index = cell["tile"]

        tileset = self.tilesets.get(tileset_name)
        if tileset is None:
            print(f"Missing tileset: {tileset_name}")
            return None

        return tileset.get_tile(tile_index)

    def render_layer(self, surface, layer_name, scroll_x=0, scroll_y=0):
        layer = self.level[layer_name]

        for row_idx, row in enumerate(layer):
            for col_idx, cell in enumerate(row):
                if cell == 0:
                    continue

                tile = self.get_tile_surface(cell)
                if tile is None:
                    continue

                x = col_idx * self.tile_size - scroll_x
                y = row_idx * self.tile_size - scroll_y

                surface.blit(tile, (x, y))

    def render_collision(self, surface, scroll_x=0, scroll_y=0):
        self.render_layer(surface, "collision", scroll_x, scroll_y)

    def render_decor(self, surface, scroll_x=0, scroll_y=0):
        self.render_layer(surface, "decor", scroll_x, scroll_y)

    def render(self, surface, scroll_x=0, scroll_y=0):
        self.render_collision(surface, scroll_x, scroll_y)
        self.render_decor(surface, scroll_x, scroll_y)

    def get_collision_rects(self):
        rects = []

        for row_idx, row in enumerate(self.level["collision"]):
            for col_idx, cell in enumerate(row):
                if cell == 0:
                    continue

                rect = pygame.Rect(
                    col_idx * self.tile_size,
                    row_idx * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )

                rects.append(rect)

        return rects
