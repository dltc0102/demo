import pygame

class IntroScene:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.initial_black_time = 1500
        self.fade_in_time = 2200
        self.hold_time = 4000
        self.fade_out_time = 2200

        self.text_lines = [
            "Disclaimer",
            "",
            "This game contains themes related to mental health,",
            "stress, anxiety, intrusive thoughts, and hallucinations.",
            "",
            "It is not intended to represent every person's experience.",
            "",
            "Please take breaks if you need to."
        ]

    def run(self):
        start_time = pygame.time.get_ticks()

        while True:
            now = pygame.time.get_ticks()
            elapsed = now - start_time

            total_time = self.initial_black_time + self.fade_in_time + self.hold_time + self.fade_out_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        return "continue"

            self.game.display.fill((0, 0, 0))

            if elapsed < self.initial_black_time:
                alpha = 0

            elif elapsed < self.initial_black_time + self.fade_in_time:
                fade_elapsed = elapsed - self.initial_black_time
                alpha = int(255 * (fade_elapsed / self.fade_in_time))

            elif elapsed < self.initial_black_time + self.fade_in_time + self.hold_time:
                alpha = 255

            elif elapsed < total_time:
                fade_elapsed = (
                    elapsed
                    - self.initial_black_time
                    - self.fade_in_time
                    - self.hold_time
                )

                alpha = int(255 * (1 - fade_elapsed / self.fade_out_time))

            else:
                return "continue"

            self.render_disclaimer(alpha)

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)

    def render_disclaimer(self, alpha):
        y = self.game.internal_h // 2 - 110

        for idx, line in enumerate(self.text_lines):
            font = self.font if idx == 0 else self.small_font

            text_surf = font.render(line, True, (240, 240, 240))
            text_surf.set_alpha(alpha)

            x = self.game.internal_w // 2 - text_surf.get_width() // 2
            self.game.display.blit(text_surf, (x, y))

            y += 34 if idx == 0 else 26