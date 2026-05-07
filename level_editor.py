import pygame
import sys
import json
import os
import copy

# ── Configuration ──────────────────────────────────────────────────────────────
TILE_SIZE = 128          # source tile size in tileset sheets
DISPLAY_TILE = 32        # tile size rendered on the map canvas
EXPORT_TILE_SIZE = 16    # logical tile size written to json
SIDEBAR_W = 320
TOOLBAR_H = 72
SCREEN_W = 1500
SCREEN_H = 860
MAP_COLS = 45
MAP_ROWS = 45
FPS = 60
UNDO_LIMIT = 50

BASE_DIR = os.path.dirname(__file__)

TILESET_DIR = os.path.join(BASE_DIR, "assets", "tilesets")
SAVE_PATH = os.path.join(BASE_DIR, "assets", "levels", "map.json")

# ── Colours ────────────────────────────────────────────────────────────────────
C_BG = (18, 20, 30)
C_CANVAS = (10, 12, 20)
C_GRID = (40, 44, 60)
C_SIDEBAR = (22, 25, 38)
C_TOOLBAR = (15, 17, 28)
C_ACCENT = (100, 160, 255)
C_ERASE = (220, 80, 80)
C_TEXT = (200, 210, 230)
C_BORDER = (50, 58, 80)
C_PANEL = (32, 36, 52)
C_PANEL_HI = (48, 56, 80)
C_GREEN = (120, 220, 140)
C_YELLOW = (255, 210, 110)
C_PURPLE = (200, 140, 255)

AUTOTILE_47_COUNT = 47


# ── 47-tile autotile rules ─────────────────────────────────────────────────────
def is_same_autotile(grid, col, row, tileset_index):
    cell = grid.get((col, row))
    return (
        cell is not None
        and cell.get("kind") == "autotile"
        and cell.get("tileset") == tileset_index
    )


def tile_index_for_autotile_cell(grid, col, row, tileset_index):
    def has(dc, dr):
        return is_same_autotile(grid, col + dc, row + dr, tileset_index)

    n = has(0, -1)
    e = has(1, 0)
    s = has(0, 1)
    w = has(-1, 0)

    ne = n and e and has(1, -1)
    se = s and e and has(1, 1)
    sw = s and w and has(-1, 1)
    nw = n and w and has(-1, -1)

    if not n and not e and not s and not w:
        return 43

    if s and not n and not e and not w:
        return 0
    if n and not s and not e and not w:
        return 24
    if e and not n and not s and not w:
        return 36
    if w and not n and not s and not e:
        return 38

    if n and s and not e and not w:
        return 12
    if e and w and not n and not s:
        return 37

    if s and e and not n and not w:
        return 9 if se else 1
    if s and w and not n and not e:
        return 11 if sw else 2
    if n and e and not s and not w:
        return 33 if ne else 25
    if n and w and not s and not e:
        return 35 if nw else 26

    if e and s and w and not n:
        if se and sw:
            return 10
        if se and not sw:
            return 20
        if sw and not se:
            return 19
        return 29

    if n and s and w and not e:
        if nw and sw:
            return 23
        if nw and not sw:
            return 31
        if sw and not nw:
            return 15
        return 27

    if n and e and w and not s:
        if nw and ne:
            return 34
        if ne and not nw:
            return 40
        if nw and not ne:
            return 39
        return 41

    if n and e and s and not w:
        if ne and se:
            return 21
        if ne and not se:
            return 3
        if se and not ne:
            return 4
        return 28

    if n and e and s and w:
        if nw and ne and sw and se:
            return 22

        if not nw and not ne and not sw and not se:
            return 30

        if not ne and nw and sw and se:
            return 3
        if not se and nw and ne and sw:
            return 4
        if not sw and nw and ne and se:
            return 5
        if not nw and ne and sw and se:
            return 6

        if not ne and not sw and nw and se:
            return 32
        if not nw and not se and ne and sw:
            return 44

        if not ne and not se and nw and sw:
            return 7
        if not se and not sw and nw and ne:
            return 8
        if not sw and not nw and ne and se:
            return 18
        if not nw and not ne and sw and se:
            return 19

        if ne and not nw and not se and not sw:
            return 17
        if se and not nw and not ne and not sw:
            return 16
        if sw and not nw and not ne and not se:
            return 6
        if nw and not ne and not se and not sw:
            return 18

        return 22

    return 22


# ── Tileset loader ─────────────────────────────────────────────────────────────
class TileSet:
    def __init__(self, path, tile_size=TILE_SIZE):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.tile_size = tile_size
        self.sheet = pygame.image.load(path).convert_alpha()
        self.tiles = []
        self._extract()

    def _extract(self):
        ts = self.tile_size
        sw, sh = self.sheet.get_size()
        cols = sw // ts
        rows = sh // ts

        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(col * ts, row * ts, ts, ts)
                surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
                surf.blit(self.sheet, (0, 0), rect)
                self.tiles.append(surf)

    @property
    def count(self):
        return len(self.tiles)

    def get_tile(self, index, size=None):
        if not self.tiles:
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            return surf

        index = max(0, min(index, len(self.tiles) - 1))
        surf = self.tiles[index]
        if size and size != self.tile_size:
            return pygame.transform.smoothscale(surf, (size, size))
        return surf


# ── Level Editor ───────────────────────────────────────────────────────────────
class LevelEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Layered Multi-Level Editor")
        self.clock = pygame.time.Clock()

        self.font_sm = pygame.font.SysFont("monospace", 13)
        self.font_md = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_lg = pygame.font.SysFont("monospace", 18, bold=True)

        self.tilesets = self.load_tilesets_from_folder(TILESET_DIR)
        if not self.tilesets:
            raise FileNotFoundError(
                f"No PNG tilesets found in '{TILESET_DIR}'. "
                f"Create that folder and put your tileset PNGs inside it."
            )

        self.active_tileset_index = 0
        self.selected_tile_index = 0
        self.brush_mode = "stamp"          # "stamp" or "autotile"
        self.autotile_tileset_index = 0

        # level data:
        # {
        #   "level_name": {
        #       "collision": {(c, r): cell, ...},
        #       "decor": {(c, r): cell, ...}
        #   }
        # }
        self.levels = {}
        self.current_level_name = "level_1"
        self.active_layer = "collision"
        self.ensure_level_exists(self.current_level_name)

        self.undo_stack = []
        self.redo_stack = []

        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 1.0
        self.show_grid = True

        self.panning = False
        self.pan_start = (0, 0)
        self.cam_start = (0, 0)
        self.painting = False
        self.erasing = False
        self.last_cell = None

        self.status_msg = (
            "Ready — LMB paint · RMB erase · MMB pan · "
            "1 collision · 2 decor · Tab switch layer"
        )

        self._tile_cache = {}
        self._tileset_button_rects = []
        self._tile_rects = []

        self.reset_view()

    # ── Level helpers ─────────────────────────────────────────────────────────

    def ensure_level_exists(self, level_name):
        if level_name not in self.levels:
            self.levels[level_name] = {
                "collision": {},
                "decor": {},
            }

    def current_level(self):
        self.ensure_level_exists(self.current_level_name)
        return self.levels[self.current_level_name]

    def current_grid(self):
        return self.current_level()[self.active_layer]

    def other_grid(self):
        other = "decor" if self.active_layer == "collision" else "collision"
        return self.current_level()[other]

    def set_current_level_name(self, new_name):
        new_name = new_name.strip()
        if not new_name:
            return
        self.ensure_level_exists(new_name)
        self.current_level_name = new_name
        self.status_msg = f"Current level → {self.current_level_name}"

    # ── Loading ───────────────────────────────────────────────────────────────

    def load_tilesets_from_folder(self, folder):
        os.makedirs(folder, exist_ok=True)
        tilesets = []

        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith(".png"):
                path = os.path.join(folder, fn)
                try:
                    tilesets.append(TileSet(path, TILE_SIZE))
                except Exception as e:
                    print(f"Failed to load {path}: {e}")

        return tilesets

    # ── Helpers ───────────────────────────────────────────────────────────────

    def active_tileset(self):
        return self.tilesets[self.active_tileset_index]

    def autotile_tileset(self):
        return self.tilesets[self.autotile_tileset_index]

    def canvas_rect(self):
        size = 720
        available_w = self.screen.get_width() - SIDEBAR_W
        x = (available_w - size) // 2
        available_h = self.screen.get_height() - TOOLBAR_H
        y = TOOLBAR_H + (available_h - size) // 2
        return pygame.Rect(x, y, size, size)

    def screen_to_cell(self, sx, sy):
        cr = self.canvas_rect()
        rx = sx - cr.x - self.cam_x
        ry = sy - cr.y - self.cam_y
        ts = DISPLAY_TILE * self.zoom
        col = int(rx // ts)
        row = int(ry // ts)
        return col, row

    def cell_to_screen(self, col, row):
        cr = self.canvas_rect()
        ts = DISPLAY_TILE * self.zoom
        sx = cr.x + self.cam_x + col * ts
        sy = cr.y + self.cam_y + row * ts
        return sx, sy

    def get_tile_surface(self, tileset_index, tile_index, size):
        key = (tileset_index, tile_index, size)
        if key not in self._tile_cache:
            self._tile_cache[key] = self.tilesets[tileset_index].get_tile(tile_index, size)
        return self._tile_cache[key]

    def clear_cache(self):
        self._tile_cache.clear()

    def reset_view(self):
        cr = self.canvas_rect()
        self.zoom = 1.0
        self.cam_x = -(MAP_COLS * DISPLAY_TILE) / 2 + cr.w / 2
        self.cam_y = -(MAP_ROWS * DISPLAY_TILE) / 2 + cr.h / 2

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def snapshot(self):
        self.undo_stack.append(copy.deepcopy(self.levels))
        if len(self.undo_stack) > UNDO_LIMIT:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.levels))
            self.levels = self.undo_stack.pop()
            self.ensure_level_exists(self.current_level_name)
            self.status_msg = "Undo"

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.levels))
            self.levels = self.redo_stack.pop()
            self.ensure_level_exists(self.current_level_name)
            self.status_msg = "Redo"

    # ── Painting ──────────────────────────────────────────────────────────────

    def place_tile(self, col, row):
        grid = self.current_grid()

        if self.brush_mode == "autotile":
            grid[(col, row)] = {
                "kind": "autotile",
                "tileset": self.autotile_tileset_index,
            }
        else:
            grid[(col, row)] = {
                "kind": "stamp",
                "tileset": self.active_tileset_index,
                "tile": self.selected_tile_index,
            }
        self.last_cell = (col, row)

    def erase_tile(self, col, row):
        grid = self.current_grid()
        if (col, row) in grid:
            del grid[(col, row)]
            self.last_cell = (col, row)

    def clear_active_layer(self):
        self.snapshot()
        self.current_level()[self.active_layer].clear()
        self.status_msg = f"Cleared {self.active_layer} layer"

    def clear_current_level(self):
        self.snapshot()
        self.current_level()["collision"].clear()
        self.current_level()["decor"].clear()
        self.status_msg = f"Cleared level {self.current_level_name}"

    def fill_active_layer(self):
        self.snapshot()
        for c in range(MAP_COLS):
            for r in range(MAP_ROWS):
                self.place_tile(c, r)
        self.status_msg = f"Filled {self.active_layer} layer"

    # ── JSON conversion ───────────────────────────────────────────────────────

    def grid_bounds(self, level_dict):
        cells = set(level_dict["collision"].keys()) | set(level_dict["decor"].keys())
        if not cells:
            return 0, 0

        max_col = max(c for c, _ in cells)
        max_row = max(r for _, r in cells)
        return max(max_col + 1, 1), max(max_row + 1, 1)

    def cell_to_export_value(self, grid, col, row):
        cell = grid.get((col, row))
        if cell is None:
            return 0

        if cell["kind"] == "stamp":
            return {
                "kind": "stamp",
                "tileset": self.tilesets[cell["tileset"]].name,
                "tile": cell["tile"],
            }

        tidx = tile_index_for_autotile_cell(grid, col, row, cell["tileset"])
        tidx = max(
            0,
            min(
                tidx,
                min(AUTOTILE_47_COUNT, self.tilesets[cell["tileset"]].count) - 1
            )
        )
        return {
            "kind": "autotile",
            "tileset": self.tilesets[cell["tileset"]].name,
            "tile": tidx,
        }

    def level_to_export(self, level_name):
        level_dict = self.levels[level_name]
        width, height = self.grid_bounds(level_dict)

        collision = []
        decor = []

        for row in range(height):
            collision_row = []
            decor_row = []
            for col in range(width):
                collision_row.append(self.cell_to_export_value(level_dict["collision"], col, row))
                decor_row.append(self.cell_to_export_value(level_dict["decor"], col, row))
            collision.append(collision_row)
            decor.append(decor_row)

        return {
            "tile_size": EXPORT_TILE_SIZE,
            "width": width,
            "height": height,
            "collision": collision,
            "decor": decor,
        }

    def export_all_levels(self):
        return {
            "tile_size": EXPORT_TILE_SIZE,
            "tilesets": [os.path.basename(ts.path) for ts in self.tilesets],
            "levels": {
                level_name: self.level_to_export(level_name)
                for level_name in sorted(self.levels.keys())
            }
        }

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save_map(self, path=SAVE_PATH):
        data = self.export_all_levels()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self.status_msg = f"Saved → {os.path.basename(path)}"

    def import_legacy_tiles(self, tiles):
        level = {
            "collision": {},
            "decor": {},
        }

        for item in tiles:
            if isinstance(item, list) and len(item) >= 2:
                col, row = item[0], item[1]
                level["collision"][(col, row)] = {
                    "kind": "autotile",
                    "tileset": 0,
                }
            elif isinstance(item, dict):
                col = item["col"]
                row = item["row"]
                cell = {k: v for k, v in item.items() if k not in ("col", "row")}
                level["collision"][(col, row)] = cell

        return level

    def import_exported_level(self, exported_level):
        level = {
            "collision": {},
            "decor": {},
        }

        collision_rows = exported_level.get("collision", [])
        decor_rows = exported_level.get("decor", [])

        for row_idx, row in enumerate(collision_rows):
            for col_idx, value in enumerate(row):
                if value == 0:
                    continue
                if isinstance(value, dict):
                    tileset_name = value.get("tileset", self.tilesets[0].name)
                    tileset_index = self.find_tileset_index_by_name(tileset_name)
                    level["collision"][(col_idx, row_idx)] = {
                        "kind": value.get("kind", "stamp"),
                        "tileset": tileset_index,
                        "tile": value.get("tile", 0),
                    }

        for row_idx, row in enumerate(decor_rows):
            for col_idx, value in enumerate(row):
                if value == 0:
                    continue
                if isinstance(value, dict):
                    tileset_name = value.get("tileset", self.tilesets[0].name)
                    tileset_index = self.find_tileset_index_by_name(tileset_name)
                    level["decor"][(col_idx, row_idx)] = {
                        "kind": value.get("kind", "stamp"),
                        "tileset": tileset_index,
                        "tile": value.get("tile", 0),
                    }

        return level

    def find_tileset_index_by_name(self, tileset_name):
        for i, ts in enumerate(self.tilesets):
            if ts.name == tileset_name or os.path.basename(ts.path) == tileset_name:
                return i
        return 0

    def load_map(self, path=SAVE_PATH):
        if not os.path.exists(path):
            self.status_msg = f"File not found: {path}"
            return

        with open(path, "r") as f:
            data = json.load(f)

        self.snapshot()
        self.levels = {}

        # new format with named levels
        if "levels" in data and isinstance(data["levels"], dict):
            for level_name, exported_level in data["levels"].items():
                self.levels[level_name] = self.import_exported_level(exported_level)

        # old format fallback
        elif "tiles" in data:
            self.levels["level_1"] = self.import_legacy_tiles(data["tiles"])

        else:
            self.levels["level_1"] = {"collision": {}, "decor": {}}

        if not self.levels:
            self.levels["level_1"] = {"collision": {}, "decor": {}}

        self.current_level_name = sorted(self.levels.keys())[0]
        self.ensure_level_exists(self.current_level_name)
        self.status_msg = f"Loaded ← {os.path.basename(path)}"

    # ── Sidebar hit detection ────────────────────────────────────────────────

    def sidebar_tileset_at_pos(self, pos):
        for i, rect in enumerate(self._tileset_button_rects):
            if rect.collidepoint(pos):
                return i
        return None

    def sidebar_tile_at_pos(self, pos):
        for i, rect in self._tile_rects:
            if rect.collidepoint(pos):
                return i
        return None

    # ── Drawing helpers ───────────────────────────────────────────────────────

    def draw_grid_cells(self, canvas_surf, grid, ts, col0, row0, col1, row1, alpha=None):
        for (col, row), cell in grid.items():
            if not (col0 <= col <= col1 and row0 <= row <= row1):
                continue

            sx = int(self.cam_x + col * ts)
            sy = int(self.cam_y + row * ts)

            if cell["kind"] == "autotile":
                tidx = tile_index_for_autotile_cell(grid, col, row, cell["tileset"])
                tidx = max(
                    0,
                    min(
                        tidx,
                        min(AUTOTILE_47_COUNT, self.tilesets[cell["tileset"]].count) - 1
                    )
                )
                surf = self.get_tile_surface(cell["tileset"], tidx, ts)
            else:
                surf = self.get_tile_surface(cell["tileset"], cell["tile"], ts)

            if alpha is not None:
                surf = surf.copy()
                surf.set_alpha(alpha)

            canvas_surf.blit(surf, (sx, sy))

    def draw_hover(self, canvas_surf, ts):
        mx, my = pygame.mouse.get_pos()
        cr = self.canvas_rect()
        if not cr.collidepoint(mx, my):
            return

        hc, hr = self.screen_to_cell(mx, my)
        hx = int(self.cam_x + hc * ts)
        hy = int(self.cam_y + hr * ts)

        hover_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)

        if self.erasing:
            hover_surf.fill((220, 60, 60, 60))
            pygame.draw.rect(hover_surf, (220, 80, 80), (0, 0, ts, ts), 2)
        elif self.active_layer == "collision":
            hover_surf.fill((100, 160, 255, 40))
            pygame.draw.rect(hover_surf, (100, 160, 255), (0, 0, ts, ts), 2)
        else:
            hover_surf.fill((200, 140, 255, 40))
            pygame.draw.rect(hover_surf, (200, 140, 255), (0, 0, ts, ts), 2)

        canvas_surf.blit(hover_surf, (hx, hy))

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self):
        w, h = self.screen.get_size()
        self.screen.fill(C_BG)

        cr = self.canvas_rect()
        canvas_surf = pygame.Surface((cr.w, cr.h))
        canvas_surf.fill(C_CANVAS)

        ts = max(4, int(DISPLAY_TILE * self.zoom))

        col0 = int(-self.cam_x / ts) - 1
        row0 = int(-self.cam_y / ts) - 1
        col1 = col0 + cr.w // ts + 3
        row1 = row0 + cr.h // ts + 3

        if self.show_grid and ts > 8:
            gx = int(self.cam_x % ts)
            gy = int(self.cam_y % ts)
            for x in range(gx, cr.w + ts, ts):
                pygame.draw.line(canvas_surf, C_GRID, (x, 0), (x, cr.h))
            for y in range(gy, cr.h + ts, ts):
                pygame.draw.line(canvas_surf, C_GRID, (0, y), (cr.w, y))

        # draw both layers together
        collision_grid = self.current_level()["collision"]
        decor_grid = self.current_level()["decor"]

        if self.active_layer == "collision":
            self.draw_grid_cells(canvas_surf, collision_grid, ts, col0, row0, col1, row1, alpha=None)
            self.draw_grid_cells(canvas_surf, decor_grid, ts, col0, row0, col1, row1, alpha=120)
        else:
            self.draw_grid_cells(canvas_surf, collision_grid, ts, col0, row0, col1, row1, alpha=120)
            self.draw_grid_cells(canvas_surf, decor_grid, ts, col0, row0, col1, row1, alpha=None)

        self.draw_hover(canvas_surf, ts)

        self.screen.blit(canvas_surf, cr.topleft)
        pygame.draw.rect(self.screen, C_BORDER, cr, 1)

        self._draw_toolbar(w)
        self._draw_sidebar(w, h)
        pygame.display.flip()

    def _draw_toolbar(self, w):
        pygame.draw.rect(self.screen, C_TOOLBAR, (0, 0, w, TOOLBAR_H))
        pygame.draw.line(self.screen, C_BORDER, (0, TOOLBAR_H - 1), (w, TOOLBAR_H - 1))

        title = self.font_lg.render("LAYERED MULTI-LEVEL TILE EDITOR", True, C_ACCENT)
        self.screen.blit(title, (12, 10))

        line2 = self.font_sm.render(
            f"Level: {self.current_level_name}   Layer: {self.active_layer}   Brush: {self.brush_mode}",
            True,
            C_TEXT,
        )
        self.screen.blit(line2, (12, 40))

        status = self.font_sm.render(self.status_msg, True, C_TEXT)
        sw = status.get_width()
        self.screen.blit(status, (w - SIDEBAR_W - sw - 16, 28))

    def _draw_sidebar(self, w, h):
        sx = w - SIDEBAR_W
        pygame.draw.rect(self.screen, C_SIDEBAR, (sx, 0, SIDEBAR_W, h))
        pygame.draw.line(self.screen, C_BORDER, (sx, 0), (sx, h))

        self._tileset_button_rects = []
        self._tile_rects = []

        y = TOOLBAR_H + 10

        header = self.font_md.render("LEVELS", True, C_ACCENT)
        self.screen.blit(header, (sx + 10, y))
        y += 24

        level_names = sorted(self.levels.keys())
        preview_names = ", ".join(level_names[:6])
        if len(level_names) > 6:
            preview_names += ", ..."
        line = self.font_sm.render(preview_names or "(none)", True, C_TEXT)
        self.screen.blit(line, (sx + 12, y))
        y += 22

        layer_color = C_ACCENT if self.active_layer == "collision" else C_PURPLE
        layer_text = self.font_md.render(f"ACTIVE LAYER: {self.active_layer.upper()}", True, layer_color)
        self.screen.blit(layer_text, (sx + 10, y))
        y += 24

        mode_col = C_GREEN if self.brush_mode == "autotile" else C_ACCENT
        mode_label = self.font_md.render(f"BRUSH: {self.brush_mode.upper()}", True, mode_col)
        self.screen.blit(mode_label, (sx + 10, y))
        y += 22

        active_ts = self.active_tileset()
        auto_ts = self.autotile_tileset()

        line1 = self.font_sm.render(f"Stamp tileset: {active_ts.name}", True, C_TEXT)
        line2 = self.font_sm.render(f"Autotile set:  {auto_ts.name}", True, C_TEXT)
        self.screen.blit(line1, (sx + 12, y))
        y += 16
        self.screen.blit(line2, (sx + 12, y))
        y += 18

        pygame.draw.line(self.screen, C_BORDER, (sx + 8, y), (w - 8, y))
        y += 10

        header = self.font_md.render("TILESETS", True, C_ACCENT)
        self.screen.blit(header, (sx + 10, y))
        y += 24

        for i, ts in enumerate(self.tilesets):
            rect = pygame.Rect(sx + 10, y, SIDEBAR_W - 20, 24)
            self._tileset_button_rects.append(rect)

            fill = C_PANEL_HI if i == self.active_tileset_index else C_PANEL
            pygame.draw.rect(self.screen, fill, rect)
            pygame.draw.rect(self.screen, C_BORDER, rect, 1)

            txt_col = C_ACCENT if i == self.active_tileset_index else C_TEXT
            label = self.font_sm.render(f"{i}: {ts.name} ({ts.count})", True, txt_col)
            self.screen.blit(label, (rect.x + 6, rect.y + 5))
            y += 28

        y += 4
        pygame.draw.line(self.screen, C_BORDER, (sx + 8, y), (w - 8, y))
        y += 10

        tiles_header = self.font_md.render(f"TILES ({active_ts.count})", True, C_ACCENT)
        self.screen.blit(tiles_header, (sx + 10, y))
        y += 24

        preview = 44
        pad = 4
        cols_s = max(1, (SIDEBAR_W - pad * 2) // (preview + pad))

        for i in range(active_ts.count):
            col_s = i % cols_s
            row_s = i // cols_s
            px = sx + pad + col_s * (preview + pad)
            py = y + row_s * (preview + pad)
            rect = pygame.Rect(px, py, preview, preview)

            self._tile_rects.append((i, rect))

            surf = self.get_tile_surface(self.active_tileset_index, i, preview)
            self.screen.blit(surf, (px, py))

            if self.brush_mode == "stamp" and i == self.selected_tile_index:
                pygame.draw.rect(self.screen, C_YELLOW, rect, 3)
            else:
                pygame.draw.rect(self.screen, C_BORDER, rect, 1)

            idx_txt = self.font_sm.render(str(i), True, (120, 130, 160))
            self.screen.blit(idx_txt, (px + 2, py + preview - 14))

        rows_used = ((active_ts.count - 1) // cols_s) + 1 if active_ts.count else 0
        y += rows_used * (preview + pad) + 8

        pygame.draw.line(self.screen, C_BORDER, (sx + 8, y), (w - 8, y))
        y += 10

        stats = [
            f"Collision tiles: {len(self.current_level()['collision'])}",
            f"Decor tiles:     {len(self.current_level()['decor'])}",
            f"Zoom:            {self.zoom:.2f}x",
            f"Cam:             {int(self.cam_x)},{int(self.cam_y)}",
            f"Undo:            {len(self.undo_stack)}",
        ]
        for s in stats:
            surf = self.font_sm.render(s, True, C_TEXT)
            self.screen.blit(surf, (sx + 12, y))
            y += 18

        y += 8
        pygame.draw.line(self.screen, C_BORDER, (sx + 8, y), (w - 8, y))
        y += 10

        controls = [
            ("1 / 2",    "Collision / decor layer"),
            ("Tab",      "Switch layer"),
            ("N",        "New / next level name"),
            ("[ / ]",    "Prev / next level"),
            ("LMB",      "Paint / select tile"),
            ("RMB",      "Erase"),
            ("MMB drag", "Pan"),
            ("Scroll",   "Zoom"),
            ("B",        "Stamp brush"),
            ("T",        "Autotile brush"),
            ("G",        "Toggle grid"),
            ("C",        "Clear active layer"),
            ("Shift+C",  "Clear whole level"),
            ("Ctrl+Z",   "Undo"),
            ("Ctrl+Y",   "Redo"),
            ("Ctrl+S",   "Save all levels"),
            ("Ctrl+O",   "Load all levels"),
            ("F",        "Fill active layer"),
            ("R",        "Reset view"),
        ]
        for key, desc in controls:
            k = self.font_sm.render(key, True, C_ACCENT)
            d = self.font_sm.render(desc, True, C_TEXT)
            self.screen.blit(k, (sx + 12, y))
            self.screen.blit(d, (sx + 90, y))
            y += 16

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def _zoom(self, factor, mouse_pos):
        cr = self.canvas_rect()
        mx = mouse_pos[0] - cr.x
        my = mouse_pos[1] - cr.y

        old_zoom = self.zoom
        self.zoom = max(0.1, min(8.0, self.zoom * factor))

        scale = self.zoom / old_zoom
        self.cam_x = mx - scale * (mx - self.cam_x)
        self.cam_y = my - scale * (my - self.cam_y)

    # ── Level navigation ──────────────────────────────────────────────────────

    def level_names_sorted(self):
        return sorted(self.levels.keys())

    def prev_level(self):
        names = self.level_names_sorted()
        if not names:
            return
        idx = names.index(self.current_level_name)
        self.current_level_name = names[(idx - 1) % len(names)]
        self.status_msg = f"Current level → {self.current_level_name}"

    def next_level(self):
        names = self.level_names_sorted()
        if not names:
            return
        idx = names.index(self.current_level_name)
        self.current_level_name = names[(idx + 1) % len(names)]
        self.status_msg = f"Current level → {self.current_level_name}"

    def create_next_level_name(self):
        base = "level_"
        n = 1
        while f"{base}{n}" in self.levels:
            n += 1
        return f"{base}{n}"

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    ctrl = mods & pygame.KMOD_CTRL
                    shift = mods & pygame.KMOD_SHIFT

                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                    elif ctrl and event.key == pygame.K_s:
                        self.save_map()

                    elif ctrl and event.key == pygame.K_o:
                        self.load_map()

                    elif ctrl and event.key == pygame.K_z:
                        if mods & pygame.KMOD_SHIFT:
                            self.redo()
                        else:
                            self.undo()

                    elif ctrl and event.key == pygame.K_y:
                        self.redo()

                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                        self.status_msg = f"Grid {'on' if self.show_grid else 'off'}"

                    elif event.key == pygame.K_r:
                        self.reset_view()
                        self.status_msg = "View reset"

                    elif event.key == pygame.K_c:
                        if shift:
                            self.clear_current_level()
                        else:
                            self.clear_active_layer()

                    elif event.key == pygame.K_b:
                        self.brush_mode = "stamp"
                        self.status_msg = f"Stamp brush → {self.active_tileset().name}, tile {self.selected_tile_index}"

                    elif event.key == pygame.K_t:
                        self.brush_mode = "autotile"
                        self.autotile_tileset_index = self.active_tileset_index
                        self.status_msg = f"Autotile brush → {self.autotile_tileset().name}"

                    elif event.key == pygame.K_f:
                        self.fill_active_layer()

                    elif event.key == pygame.K_1:
                        self.active_layer = "collision"
                        self.status_msg = "Active layer → collision"

                    elif event.key == pygame.K_2:
                        self.active_layer = "decor"
                        self.status_msg = "Active layer → decor"

                    elif event.key == pygame.K_TAB:
                        self.active_layer = "decor" if self.active_layer == "collision" else "collision"
                        self.status_msg = f"Active layer → {self.active_layer}"

                    elif event.key == pygame.K_LEFTBRACKET:
                        self.prev_level()

                    elif event.key == pygame.K_RIGHTBRACKET:
                        self.next_level()

                    elif event.key == pygame.K_n:
                        self.snapshot()
                        new_name = self.create_next_level_name()
                        self.set_current_level_name(new_name)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    cr = self.canvas_rect()

                    if event.button == 2:
                        self.panning = True
                        self.pan_start = event.pos
                        self.cam_start = (self.cam_x, self.cam_y)

                    elif event.button == 1:
                        picked_tileset = self.sidebar_tileset_at_pos(event.pos)
                        picked_tile = self.sidebar_tile_at_pos(event.pos)

                        if picked_tileset is not None:
                            self.active_tileset_index = picked_tileset
                            self.selected_tile_index = min(
                                self.selected_tile_index,
                                max(0, self.active_tileset().count - 1)
                            )
                            self.status_msg = f"Active tileset → {self.active_tileset().name}"

                        elif picked_tile is not None:
                            self.selected_tile_index = picked_tile
                            self.brush_mode = "stamp"
                            self.status_msg = (
                                f"Selected tile {picked_tile} "
                                f"from {self.active_tileset().name}"
                            )

                        elif cr.collidepoint(event.pos):
                            self.painting = True
                            self.snapshot()
                            col, row = self.screen_to_cell(*event.pos)
                            self.place_tile(col, row)

                    elif event.button == 3 and cr.collidepoint(event.pos):
                        self.erasing = True
                        self.snapshot()
                        col, row = self.screen_to_cell(*event.pos)
                        self.erase_tile(col, row)

                    elif event.button == 4:
                        self._zoom(1.15, event.pos)

                    elif event.button == 5:
                        self._zoom(1 / 1.15, event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 2:
                        self.panning = False
                    elif event.button == 1:
                        self.painting = False
                    elif event.button == 3:
                        self.erasing = False

                elif event.type == pygame.MOUSEMOTION:
                    cr = self.canvas_rect()

                    if self.panning:
                        dx = event.pos[0] - self.pan_start[0]
                        dy = event.pos[1] - self.pan_start[1]
                        self.cam_x = self.cam_start[0] + dx
                        self.cam_y = self.cam_start[1] + dy

                    if self.painting and cr.collidepoint(event.pos):
                        col, row = self.screen_to_cell(*event.pos)
                        if (col, row) != self.last_cell:
                            self.place_tile(col, row)

                    if self.erasing and cr.collidepoint(event.pos):
                        col, row = self.screen_to_cell(*event.pos)
                        if (col, row) != self.last_cell:
                            self.erase_tile(col, row)

                elif event.type == pygame.VIDEORESIZE:
                    self.clear_cache()

            self.draw()


if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()