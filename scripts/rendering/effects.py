import pygame, random

class Effects:
    def __init__(self, game):
        self.game = game

    def render_fade(self, alpha):
        fade = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
        fade.fill((0, 0, 0, int(alpha)))
        self.game.display.blit(fade, (0, 0))

    def render_glitch(self, strength=6, slices=12):
        display_copy = self.game.display.copy()
        for _ in range(slices):
            y = random.randint(0, self.game.internal_h - 10)
            h = random.randint(2, 20)
            offset_x = random.randint(-strength, strength)
            rect = pygame.Rect(0, y, self.game.internal_w, h)
            self.game.display.blit(display_copy, (offset_x, y), rect)

    def render_cursor_magnet(self, strength=8):
        mx, my = pygame.mouse.get_pos()
        mx = int(mx / self.game.scale_x)
        my = int(my / self.game.scale_y)

        dx = (mx - self.game.internal_w / 2) * 0.01 * strength
        dy = (my - self.game.internal_h / 2) * 0.01 * strength
        warped = pygame.transform.smoothscale(
            self.game.display,
            (
                int(self.game.internal_w + abs(dx)),
                int(self.game.internal_h + abs(dy))
            )
        )
        self.game.display.blit(warped, (-dx / 2, -dy / 2))

    def render_screen_warp(self, intensity=4):
        display_copy = self.game.display.copy()
        for y in range(0, self.game.internal_h, 4):
            wave = int(intensity * random.uniform(-1, 1))
            strip = pygame.Rect(0, y, self.game.internal_w, 4)
            self.game.display.blit(display_copy, (wave, y), strip)

    def render_cursor_distortion(self, radius=80):
        mx, my = pygame.mouse.get_pos()
        mx = int(mx / self.game.scale_x)
        my = int(my / self.game.scale_y)
        overlay = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (255, 255, 255, 12), (mx, my), radius)
        self.game.display.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)