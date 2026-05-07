import math
import pygame

from scripts.core.utils import load_image

class FirstScene:
    def __init__(self, game):
        self.game = game

        self.bedroom_night_img, *_ = load_image(
            game.asset_paths["bedroom_night"]
        )
        self.kitchen_night_img, *_ = load_image(
            game.asset_paths["kitchen_night"]
        )
        self.fridge_open_img, *_ = load_image(
            game.asset_paths["fridge_open"]
        )
        self.milk_img, *_ = load_image(
            game.asset_paths["glass_of_milk"]
        )
        self.sticky_note_img, *_ = load_image(
            game.asset_paths["sticky_note"]
        )

        self.in_kitchen = False
        self.scroll_x = 0

        self.transitioning = False
        self.transition_start = 0
        self.transition_delay = 500
        self.transition_speed = 900

        self.bedroom_to_kitchen_door = pygame.Rect(680, 330, 32, 64)

        self.started = False
        self.start_time = 0

        self.fade_alpha = 255
        self.fade_speed = 180

        self.normal_pause = 1000
        self.long_pause = 2000

    def reset(self):
        self.in_kitchen = False
        self.scroll_x = 0
        self.transitioning = False
        self.transition_start = 0
        self.started = False
        self.start_time = pygame.time.get_ticks()
        self.fade_alpha = 255

        self.game.player.pos = [
            110,
            self.game.screen_h - self.game.ground_h - self.game.player_h - 30
        ]
        self.game.player_movement = [0, 0]

    def sequence(self):
        yield self.normal_pause
        yield from self.game.say(
            "I can't sleep",
            self.game.player
        )
        yield self.long_pause
        yield from self.game.say(
            [
                "i don't know why...",
                "they keep me up at night",
                "i am feeling quite a bit thirsty though"
            ],
            self.game.player
        )
        yield self.normal_pause
        yield from self.game.voice(
            "go_get_a_cup_of_milk.mp3"
        )
        yield self.long_pause
        yield from self.game.say(
            "huh? okay",
            self.game.player
        )
        yield self.normal_pause

    def handle_input(self, dt):
        key = pygame.key.get_pressed()
        self.game.player_movement = [0, 0]

        if key[pygame.K_a]:
            self.game.player_movement[0] -= self.game.player_speed * dt
            self.game.player_facing = "left"

        if key[pygame.K_d]:
            self.game.player_movement[0] += self.game.player_speed * dt
            self.game.player_facing = "right"

    def render_backgrounds(self):
        bedroom = pygame.transform.scale(
            self.bedroom_night_img,
            (self.game.internal_w, self.game.internal_h)
        )

        kitchen = pygame.transform.scale(
            self.kitchen_night_img,
            (self.game.internal_w, self.game.internal_h)
        )

        self.game.display.blit(
            bedroom,
            (-self.scroll_x, 0)
        )

        self.game.display.blit(
            kitchen,
            (self.game.internal_w - self.scroll_x, 0)
        )

    def render_transition_door(self):
        door = self.bedroom_to_kitchen_door.move(-self.scroll_x, 0)
        glow = pygame.Surface((90, 120), pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) / 2

        for radius, alpha in [(50, 20), (35, 35), (22, 55)]:
            pygame.draw.circle(
                glow,
                (255, 240, 190, alpha + int(pulse * 15)),
                (45, 60),
                radius
            )

        self.game.display.blit(
            glow,
            (door.centerx - 45, door.centery - 60),
            special_flags=pygame.BLEND_RGBA_ADD
        )

        pygame.draw.rect(
            self.game.display,
            (255, 240, 200, 120),
            door,
            border_radius=3
        )

    def update_transition(self, dt):
        if not self.transitioning:
            if not self.in_kitchen and self.game.player.rect().colliderect(
                self.bedroom_to_kitchen_door
            ):
                self.transitioning = True
                self.transition_start = pygame.time.get_ticks()
                self.game.player_movement = [0, 0]

            return

        elapsed = pygame.time.get_ticks() - self.transition_start

        if elapsed < self.transition_delay:
            self.game.player_movement = [0, 0]
            return

        self.scroll_x += self.transition_speed * dt
        self.scroll_x = min(self.scroll_x, self.game.internal_w)

        self.game.player_movement = [0, 0]

        if self.scroll_x >= self.game.internal_w:
            self.game.player.pos[0] = self.game.internal_w + 80
            self.transitioning = False
            self.in_kitchen = True

    def render_fade(self, alpha):
        fade = pygame.Surface(
            (self.game.internal_w, self.game.internal_h),
            pygame.SRCALPHA
        )
        fade.fill((0, 0, 0, int(alpha)))
        self.game.display.blit(fade, (0, 0))

    def run(self):
        self.reset()

        while True:
            dt = self.game.clock.get_time() / 1000
            elapsed = pygame.time.get_ticks() - self.start_time

            self.game.display.fill((0, 0, 0))

            self.render_backgrounds()
            self.render_transition_door()

            self.handle_input(dt)

            if not self.transitioning:
                self.game.player.update(self.game.player_movement, dt)
            else:
                self.game.player_movement = [0, 0]

            self.update_transition(dt)

            self.game.player.render(
                self.game.display,
                offset=(self.scroll_x, 0)
            )

            if not self.started and elapsed > 1000:
                self.started = True
                self.game.start_sequence(self.sequence())

            self.game.update_sequence()
            self.game.dialogue_manager.update()
            self.game.dialogue_manager.render(
                self.game.display,
                offset=(self.scroll_x, 0)
            )

            if self.fade_alpha > 0:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
                self.render_fade(self.fade_alpha)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    if event.key == pygame.K_RETURN:
                        return "continue"

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)