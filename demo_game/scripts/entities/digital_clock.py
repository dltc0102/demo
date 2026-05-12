import pygame
from datetime import datetime as dt
from paths import asset

class DigitalClock:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.font = pygame.font.Font(
            asset("assets/fonts/digital-clock.ttf"),
            48
        )

        self.color = (255, 40, 40)

    def draw(self, surf):
        current_time = dt.now().strftime("%H:%M")
        text_surf = self.font.render(
            current_time,
            True,
            self.color
        )
        surf.blit(text_surf, (self.x, self.y))