import pygame

def _point_in_polygon(x: float, y: float, polygon: list[tuple[int, int]]) -> bool:
    inside = False
    n = len(polygon)
    if n < 3: return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside

class WalkableZone:
    def __init__(self, points: list[tuple[int, int]], prohibited_polygons: list[list[tuple[int, int]]] | None = None, min_scale: float = 0.6, interaction_condition: list[str] | None = None):
        self.points = points
        self.prohibited_polygons = prohibited_polygons or []
        self.min_scale = float(min_scale)
        self.interaction_condition = interaction_condition or []

        ys = [p[1] for p in points]
        self.y_top: int = min(ys)
        self.y_bottom: int = max(ys)
        self._y_range: int = max(1, self.y_bottom - self.y_top)

    def is_active(self, flags: dict) -> bool:
        return all(flags.get(k, False) for k in self.interaction_condition)

    def contains(self, x: float, y: float) -> bool:
        if not _point_in_polygon(x, y, self.points): return False
        for barrier in self.prohibited_polygons:
            if _point_in_polygon(x, y, barrier): return False
        return True

    def scale_at_y(self, y: float) -> float:
        clamped_y = max(self.y_top, min(self.y_bottom, y))
        t = (clamped_y - self.y_top) / self._y_range
        return self.min_scale + (1.0 - self.min_scale) * t