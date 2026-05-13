import pygame
from paths import asset

class TutorialScene:
    CONTINUE_APPEAR_DELAY = 3.0
    CONTINUE_FADE_DURATION = 0.6 # s

    def __init__(self, game):
        self.game = game

        self.bg = pygame.image.load(asset("assets/backgrounds/bedroom_night.png")).convert()
        self.bg = pygame.transform.scale(self.bg, (self.game.internal_w, self.game.internal_h))
        self.bg = self.blur_surface(self.bg, blur_scale=12)

        self.font = pygame.font.Font(asset("assets/fonts/Minecraftia-Regular.ttf"), 22)

        self.lines = [
            "Use the WASD keys to move around.",
            "Press E to interact.",
            "Esc to pause and resume.",
        ]

        button_y = self.game.internal_h // 2 + 105
        self.continue_buttons = self.game.create_centered_text_buttons(
            [("continue", "CONTINUE")],
            center_y=button_y,
        )

    def blur_surface(self, surf: pygame.Surface, blur_scale: int = 10) -> pygame.Surface:
        small_w = max(1, surf.get_width() // blur_scale)
        small_h = max(1, surf.get_height() // blur_scale)

        small = pygame.transform.smoothscale(surf, (small_w, small_h))
        return pygame.transform.smoothscale(small, surf.get_size())

    def get_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)

    def render_continue_button(self, alpha: int, clickable: bool) -> str | None:
        if alpha >= 255 and clickable:
            return self.game.render_text_buttons(self.continue_buttons, clickable=True)

        original_display = self.game.display
        overlay = pygame.Surface(
            (self.game.internal_w, self.game.internal_h),
            pygame.SRCALPHA,
        )
        self.game.display = overlay
        try:
            self.game.render_text_buttons(self.continue_buttons, clickable=False)
        finally:
            self.game.display = original_display

        overlay.set_alpha(alpha)
        self.game.display.blit(overlay, (0, 0))
        return None

    def run(self) -> str:
        pygame.mouse.set_visible(True)

        fade_alpha = 255
        fade_speed = 180

        elapsed = 0.0 # s

        while True:
            dt = self.game.clock.get_time() / 1000
            elapsed += dt

            self.game.display.blit(self.bg, (0, 0))

            dark = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 135))
            self.game.display.blit(dark, (0, 0))

            self.game.effects.destabilize_backgrounds()

            y = self.game.internal_h // 2 - 80
            for line in self.lines:
                text_surf = self.font.render(line, True, (230, 230, 230))
                x = self.game.internal_w // 2 - text_surf.get_width() // 2
                self.game.display.blit(text_surf, (x, y))
                y += 42

            self.game.effects.render_cursor_magnet(radius=100, strength=1)

            time_since_button = elapsed - self.CONTINUE_APPEAR_DELAY
            if time_since_button <= 0:
                button_alpha = 0
            elif time_since_button >= self.CONTINUE_FADE_DURATION:
                button_alpha = 255
            else:
                button_alpha = int(255 * (time_since_button / self.CONTINUE_FADE_DURATION))

            button_clickable = button_alpha >= 255
            click_result = None
            if button_alpha > 0:
                click_result = self.render_continue_button(button_alpha, button_clickable)

            if click_result == "continue":
                return "continue"

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

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)