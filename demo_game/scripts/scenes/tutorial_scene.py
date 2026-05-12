import pygame
from demo_game.paths import asset

class TutorialScene:
    def __init__(self, game):
        self.game = game

        self.bg = pygame.image.load(asset("assets/backgrounds/bedroom_night.png")).convert()
        self.bg = pygame.transform.scale(self.bg, (self.game.internal_w, self.game.internal_h))
        self.bg = self.blur_surface(self.bg, blur_scale=12)

        self.font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 22)
        self.button_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 24)

        self.lines = [
            "Use A and D keys to move around.",
            "Press E to interact.",
            "Esc to pause and resume.",
        ]

    def blur_surface(self, surf: pygame.Surface, blur_scale: int = 10) -> pygame.Surface:
        small_w = max(1, surf.get_width() // blur_scale)
        small_h = max(1, surf.get_height() // blur_scale)

        small = pygame.transform.smoothscale(surf, (small_w, small_h))
        return pygame.transform.smoothscale(small, surf.get_size())

    def get_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)

    def render_text_button(self, text: str, y: int) -> pygame.Rect:
        mx, my = self.get_mouse_pos()

        text_surf = self.button_font.render(text, True, (240, 240, 240))
        text_rect = text_surf.get_rect(center=(self.game.internal_w // 2, y))

        button_rect = text_rect.inflate(36, 20)
        hovered = button_rect.collidepoint(mx, my)

        if hovered:
            pygame.draw.rect(self.game.display, (255, 255, 255), button_rect, 1)
            text_surf = self.button_font.render(text, True, (255, 255, 255))
        else:
            pygame.draw.rect(self.game.display, (150, 150, 150), button_rect, 1)

        self.game.display.blit(text_surf, text_rect)
        return button_rect

    def run(self) -> str:
        pygame.mouse.set_visible(True)

        fade_alpha = 255
        fade_speed = 180

        while True:
            dt = self.game.clock.get_time() / 1000

            self.game.display.blit(self.bg, (0, 0))

            dark = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 135))
            self.game.display.blit(dark, (0, 0))

            y = self.game.internal_h // 2 - 80

            for line in self.lines:
                text_surf = self.font.render(line, True, (230, 230, 230))
                x = self.game.internal_w // 2 - text_surf.get_width() // 2
                self.game.display.blit(text_surf, (x, y))
                y += 42

            continue_rect = self.render_text_button("CONTINUE", self.game.internal_h // 2 + 105)

            if fade_alpha > 0:
                fade_alpha = max(0, fade_alpha - fade_speed * dt)
                fade = pygame.Surface((self.game.internal_w, self.game.internal_h))
                fade.fill((0, 0, 0))
                fade.set_alpha(int(fade_alpha))
                self.game.display.blit(fade, (0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.quit_game()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pause_result = self.game.pause_menu()
                    if pause_result == "menu":
                        return "menu"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = self.get_mouse_pos()
                    if continue_rect.collidepoint(mx, my):
                        return "continue"

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)