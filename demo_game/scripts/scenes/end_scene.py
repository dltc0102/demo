import pygame
from demo_game.paths import asset
class EndScene:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 28)
        self.body_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 18)
        self.button_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 20)

        self.lines = [
            "Congratulations.",
            "You finally went to sleep",
            "after a big gulp of milk.",
            "",
            "For tonight, that is enough.",
        ]

    def get_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)

    def render_text_button(self, text: str, y: int) -> pygame.Rect:
        mx, my = self.get_mouse_pos()

        text_surf = self.button_font.render(text, True, (235, 235, 235))
        text_rect = text_surf.get_rect(center=(self.game.internal_w // 2, y))
        button_rect = text_rect.inflate(34, 18)

        hovered = button_rect.collidepoint(mx, my)
        border_color = (255, 255, 255) if hovered else (140, 140, 140)
        text_color = (255, 255, 255) if hovered else (220, 220, 220)

        text_surf = self.button_font.render(text, True, text_color)
        pygame.draw.rect(self.game.display, border_color, button_rect, 1)
        self.game.display.blit(text_surf, text_rect)

        return button_rect

    def run(self) -> str:
        pygame.mouse.set_visible(True)
        self.game.sfx.stop_all_gameplay_audio()

        fade_alpha = 255
        fade_speed = 160

        while True:
            dt = self.game.clock.get_time() / 1000
            self.game.display.fill((0, 0, 0))

            title = "END OF DEMO"
            title_surf = self.title_font.render(title, True, (237, 220, 147))
            self.game.display.blit(
                title_surf,
                (self.game.internal_w // 2 - title_surf.get_width() // 2, 95)
            )

            y = 175
            for line in self.lines:
                if line == "":
                    y += 18
                    continue

                text_surf = self.body_font.render(line, True, (230, 230, 230))
                self.game.display.blit(
                    text_surf,
                    (self.game.internal_w // 2 - text_surf.get_width() // 2, y)
                )
                y += 34

            menu_rect = self.render_text_button("BACK TO MENU", self.game.internal_h - 105)
            quit_rect = self.render_text_button("QUIT", self.game.internal_h - 62)

            if fade_alpha > 0:
                fade_alpha = max(0, fade_alpha - fade_speed * dt)
                fade = pygame.Surface((self.game.internal_w, self.game.internal_h))
                fade.fill((0, 0, 0))
                fade.set_alpha(int(fade_alpha))
                self.game.display.blit(fade, (0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = self.get_mouse_pos()

                    if menu_rect.collidepoint(mx, my):
                        return "menu"

                    if quit_rect.collidepoint(mx, my):
                        self.game.quit_game()

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)