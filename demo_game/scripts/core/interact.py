import pygame, math

class InteractZone:
    def __init__(self, points: list[tuple[int, int]], prompt: str, font: pygame.font.Font, glow_surf: pygame.Surface, proximity_inflate: int = 40, fade_speed: float = 650,):
        self.points = points
        self.prompt = prompt
        self.font = font
        self.glow_surf = glow_surf
        self.proximity_inflate = proximity_inflate
        self.fade_speed = fade_speed

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
        return (
            int(sum(p[0] for p in pts) / len(pts)),
            int(sum(p[1] for p in pts) / len(pts)),
        )

    @property
    def is_visible(self) -> bool:
        return self._prompt_alpha > 0

    def update(self, dt: float, player_rect: pygame.Rect, scroll_x: int) -> None:
        inflated = self._bounding_rect.inflate(
            self.proximity_inflate, self.proximity_inflate
        )
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

        pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2
        outline_alpha = int(a * 0.75 * (0.7 + pulse * 0.3))

        pygame.draw.polygon(self.glow_surf, (255, 255, 255, outline_alpha), screen_pts, width=1)
        display.blit(self.glow_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        text_surf = self.font.render(self.prompt, True, (255, 255, 255))
        text_surf.set_alpha(int(a * 0.9))
        cx, cy = self._center(scroll_x)
        display.blit(text_surf, (cx - text_surf.get_width() // 2, cy - text_surf.get_height() // 2))