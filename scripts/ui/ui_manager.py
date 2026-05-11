import pygame


class UIManager:
    def __init__(self, game):
        self.game = game

    def render_heart_ui(self):
        bpm = int(self.game.heart_rate.current_bpm)

        self.game.display.blit(self.game.heart_icon, (20, 20))

        bpm_text = self.game.small_font.render(f"{bpm} BPM", scale=2)

        self.game.display.blit(bpm_text, (50, 18))

    def render_player_status(self):
        if self.game.heart_rate.current_bpm < 85:
            status = "[steady heartbeat]"

        elif self.game.heart_rate.current_bpm < 105:
            status = "[irregular heartbeat]"

        elif self.game.heart_rate.current_bpm < 130:
            status = "[something is wrong]"

        else:
            status = "[panic attack]"

        text = self.game.small_font.render(status, scale=2)

        rect = text.get_rect(
            center=(
                self.game.internal_w // 2,
                self.game.internal_h - 24
            )
        )

        self.game.display.blit(text, rect)

    def show_help_hints(self):
        hints = [
            "A/D - move",
            "E - interact",
            "B - breathe",
            "ESC - pause"
        ]

        y = 20

        for hint in hints:
            surf = self.game.small_font.render(hint, scale=2)

            self.game.display.blit(surf, (20, y))

            y += 18

    def create_centered_buttons(self, buttons, start_y, spacing=70):
        centered = []

        for i, button in enumerate(buttons):
            rect = button.image.get_rect(
                center=(
                    self.game.internal_w // 2,
                    start_y + i * spacing
                )
            )

            button.rect = rect

            centered.append(button)

        return centered

    def render_buttons(self, buttons):
        mouse_pos = pygame.mouse.get_pos()

        mouse_pos = (
            mouse_pos[0] / self.game.scale_x,
            mouse_pos[1] / self.game.scale_y
        )

        clicked = pygame.mouse.get_pressed()[0]

        for button in buttons:
            button.render(
                self.game.display,
                mouse_pos,
                clicked
            )