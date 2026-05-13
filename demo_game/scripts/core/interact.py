import pygame, math

class InteractZone:
    def __init__(self, points: list[tuple[int, int]], prompt: str, font, glow_surf: pygame.Surface, proximity_inflate: int = 40, fade_speed: float = 650, show_glow: bool = True, prompt_position: str = "center"):
        self.points = points
        self.prompt = prompt
        self.font = font
        self.glow_surf = glow_surf
        self.proximity_inflate = proximity_inflate
        self.fade_speed = fade_speed
        self.show_glow = show_glow
        self.prompt_position = prompt_position
        self._prompt_alpha: float = 0.0
        self._bounding_rect = self._make_bounding_rect()

    def _make_bounding_rect(self) -> pygame.Rect:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        x, y = min(xs), min(ys)
        return pygame.Rect(x, y, max(xs) - x, max(ys) - y)

    def _screen_points(self, scroll_x: int) -> list[tuple[int, int]]:
        return [(x - scroll_x, y) for x, y in self.points]

    def _center(self, scroll_x: int) -> tuple[int, int]:
        pts = self._screen_points(scroll_x)
        return (int(sum(p[0] for p in pts) / len(pts)), int(sum(p[1] for p in pts) / len(pts)))

    @property
    def is_visible(self) -> bool:
        return self._prompt_alpha > 0

    def update(self, dt: float, player_rect: pygame.Rect, scroll_x: int) -> None:
        inflated = self._bounding_rect.inflate(self.proximity_inflate, self.proximity_inflate)
        near = player_rect.colliderect(inflated)
        target = 255.0 if near else 0.0
        step = self.fade_speed * dt
        if self._prompt_alpha < target:
            self._prompt_alpha = min(target, self._prompt_alpha + step)
        else:
            self._prompt_alpha = max(target, self._prompt_alpha - step)

    def render(self, display: pygame.Surface, scroll_x: int) -> None:
        if not self.is_visible: return
        a = int(self._prompt_alpha)
        screen_pts = self._screen_points(scroll_x)
        self.glow_surf.fill((0, 0, 0, 0))
        if self.show_glow:
            pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2
            outline_alpha = int(a * 0.75 * (0.7 + pulse * 0.3))
            pygame.draw.polygon(self.glow_surf, (255, 255, 255, outline_alpha), screen_pts, width=1)
            display.blit(self.glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        text_surf = self.make_text_surface()
        text_surf.set_alpha(int(a * 0.9))
        x, y = self.prompt_loc(text_surf, screen_pts, display)
        display.blit(text_surf, (x, y))

    def make_text_surface(self) -> pygame.Surface:
        if hasattr(self.font, "text_width") and hasattr(self.font, "characters"):
            w = max(1, int(self.font.text_width(self.prompt)))
            h = max(1, int(next(iter(self.font.characters.values())).get_height()))
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self.font.render(surf, self.prompt, (0, 0))
            return surf
        return self.font.render(self.prompt, True, (255, 255, 255))

    def prompt_loc(self, text_surf: pygame.Surface, screen_pts: list[tuple[int, int]], display: pygame.Surface) -> tuple[int, int]:
        min_x = min(p[0] for p in screen_pts)
        max_x = max(p[0] for p in screen_pts)
        min_y = min(p[1] for p in screen_pts)
        max_y = max(p[1] for p in screen_pts)
        cx = (min_x + max_x) // 2
        cy = (min_y + max_y) // 2
        tw = text_surf.get_width()
        th = text_surf.get_height()
        if self.prompt_position == "top":
            x = cx - tw // 2
            y = min_y - th - 10
        elif self.prompt_position == "bottom":
            x = cx - tw // 2
            y = max_y + 10
        else:
            x = cx - tw // 2
            y = cy - th // 2
        margin = 4
        screen_w = display.get_width()
        screen_h = display.get_height()
        if x < margin: x = margin
        if x + tw > screen_w - margin: x = screen_w - margin - tw
        if y < margin: y = margin
        if y + th > screen_h - margin: y = screen_h - margin - th
        return x, y
