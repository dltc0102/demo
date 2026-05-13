import pygame
from paths import asset

class EndScene:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 28)
        self.body_font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 18)

        gap = 24
        button_h = self.game.get_font_height(self.game.button_font) + 12 * 2
        bottom_y = self.game.internal_h - 62
        center_y = bottom_y - (button_h // 2) - (gap // 2)
        self.action_buttons = self.game.create_centered_text_buttons(
            [
                ("menu", "BACK TO MENU"),
                ("quit", "QUIT"),
            ],
            center_y=center_y,
            gap=gap,
        )
    
    def get_lines_for_milk_result(self):
        milk_result = getattr(self.game, "milk_result_type", "milk")
        
        if milk_result == "milk":
            return [
                "Congratulations.",
                "You finally went to sleep",
                "after a big gulp of milk.",
                "",
                "For tonight, that is enough.",
            ]
        elif milk_result == "water":
            return [
                "Well, at least you're hydrated.",
                "Water isn't milk, but hey,",
                "maybe next time you'll get it right.",
                "",
                "For tonight, that is enough.",
            ]
        elif milk_result == "juice":
            return [
                "Juice? Really?",
                "At least it's hydrating.",
                "Maybe try better next time.",
                "",
                "For tonight, that is enough.",
            ]
        elif milk_result == "expired":
            return [
                "You're just unlucky.",
                "",
                "...",
            ]
        elif milk_result == "dropped":
            return [
                "You dropped it.",
                "At least you tried.",
                "That counts for something, right?",
                "",
                "For tonight, that is enough.",
            ]
        else:
            return [
                "For tonight, that is enough.",
            ]

    def get_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)

    def run(self) -> str:
        pygame.mouse.set_visible(True)
        self.game.sfx.stop_all_gameplay_audio()

        fade_alpha = 255
        fade_speed = 160
        
        lines = self.get_lines_for_milk_result()

        while True:
            dt = self.game.clock.get_time() / 1000
            self.game.display.fill((0, 0, 0))
            self.game.effects.destabilize_backgrounds()

            title = "END OF DEMO"
            title_surf = self.title_font.render(title, True, (237, 220, 147))
            self.game.display.blit(
                title_surf,
                (self.game.internal_w // 2 - title_surf.get_width() // 2, 95)
            )

            y = 175
            for line in lines:
                if line == "":
                    y += 18
                    continue

                text_surf = self.body_font.render(line, True, (230, 230, 230))
                self.game.display.blit(
                    text_surf,
                    (self.game.internal_w // 2 - text_surf.get_width() // 2, y)
                )
                y += 34

            self.game.effects.render_cursor_magnet(radius=100, strength=1)
            result = self.game.render_text_buttons(self.action_buttons)
            if fade_alpha > 0:
                fade_alpha = max(0, fade_alpha - fade_speed * dt)
                fade = pygame.Surface((self.game.internal_w, self.game.internal_h))
                fade.fill((0, 0, 0))
                fade.set_alpha(int(fade_alpha))
                self.game.display.blit(fade, (0, 0))

            if result == "menu":
                return "menu"
            if result == "quit":
                self.game.quit_game()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)