import pygame
import random


class QuietRouteScene:
    def __init__(self, game):
        self.game = game

        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 15)

        self.started = False
        self.scene_ended = False

        self.player_start_x = 80
        self.player_y = self.game.screen_h - self.game.ground_h - self.game.player_h - 50

        self.walk_target_x = 560
        self.auto_walk_speed = 55

        self.background_scroll = 0

        self.check_stop_timer = 0
        self.next_check_stop = random.randint(1800, 3500)
        self.is_checking = False
        self.check_hold_time = 0

    def reset(self):
        self.started = False
        self.scene_ended = False

        self.game.player.pos = [self.player_start_x, self.player_y]
        self.game.player.velocity = [0, 0]
        self.game.player_movement = [0, 0]
        self.game.player_facing = "right"

        self.check_stop_timer = 0
        self.next_check_stop = random.randint(1800, 3500)
        self.is_checking = False
        self.check_hold_time = 0

        self.game.cutscene.stop()

    def run(self):
        self.reset()

        while True:
            dt = self.game.clock.get_time() / 1000

            self.game.display.fill((8, 9, 13))

            self.render_background()
            self.handle_auto_walk(dt)

            self.game.player.update(self.game.player_movement, dt)
            self.game.player.render(self.game.display)

            if not self.started:
                self.started = True
                self.game.cutscene.start(self.sequence())

            self.game.cutscene.update()
            self.game.dialogue_manager.update()
            self.game.thought_manager.update(dt)
            self.game.sfx.update()

            self.game.thought_manager.render(self.game.display)
            self.game.dialogue_manager.render(self.game.display)

            result = self.handle_events()
            if result:
                return result

            if self.scene_ended:
                return "continue"

            self.game.handle_pause_button()
            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)

    def handle_auto_walk(self, dt):
        self.game.player_movement = [0, 0]

        if self.scene_ended:
            return

        if self.is_checking:
            self.check_stop_timer += dt * 1000
            self.game.player_movement[0] = 0

            # nervous looking around
            if int(self.check_stop_timer / 250) % 2 == 0:
                self.game.player_facing = "left"
            else:
                self.game.player_facing = "right"

            if self.check_stop_timer >= self.check_hold_time:
                self.is_checking = False
                self.check_stop_timer = 0
                self.next_check_stop = random.randint(1800, 4200)
                self.game.player_facing = "right"

            return

        if self.game.player.pos[0] < self.walk_target_x:
            self.game.player_movement[0] = self.auto_walk_speed * dt
            self.game.player_facing = "right"

            self.check_stop_timer += dt * 1000

            if self.check_stop_timer >= self.next_check_stop:
                self.is_checking = True
                self.check_stop_timer = 0
                self.check_hold_time = random.randint(900, 1700)

                if random.random() < 0.75:
                    self.spawn_checking_thought()

        else:
            self.game.player_movement[0] = 0

    def spawn_checking_thought(self):
        thoughts = [
            "is this the right way?",
            "I don't remember this corner",
            "did I pass this already?",
            "go back?",
            "no, keep going",
            "what if I get lost?",
            "this street feels wrong",
            "I should have taken the other way",
        ]

        self.game.thought_manager.cloudthink(
            random.choice(thoughts),
            self.game.player,
            stall=random.randint(1100, 1800)
        )

    def sequence(self):
        self.game.sfx.set_heartbeat_bpm(82)

        yield from self.game.cutscene.wait(600)

        yield from self.game.cutscene.say(
            "I'll take the quieter way...",
            self.game.player
        )

        yield from self.game.cutscene.cloudthink(
            [
                "less people",
                "less noise",
                "just walk",
                "but I don't know this road",
            ],
            self.game.player,
            stall=1600
        )

        yield from self.game.cutscene.wait(1400)

        yield from self.game.cutscene.racethink(
            [
                "left?",
                "no, straight",
                "wait",
                "was it left?",
                "don't turn around",
            ],
            self.game.player,
            stall=700,
            gap=450
        )

        self.game.sfx.set_heartbeat_bpm(95)

        yield from self.game.cutscene.say(
            [
                "I hate not knowing where I am.",
                "It makes everything feel... unsafe."
            ],
            self.game.player
        )

        yield from self.game.cutscene.cloudthink(
            [
                "too quiet",
                "someone could be behind me",
                "check again",
                "no, don't check",
                "just get there",
            ],
            self.game.player,
            stall=1500
        )

        self.game.sfx.set_heartbeat_bpm(78)

        yield from self.game.cutscene.wait(900)

        yield from self.game.cutscene.say(
            "At least there aren't many people.",
            self.game.player
        )

        yield from self.game.cutscene.wait(1200)

        self.scene_ended = True

    def render_background(self):
        floor_y = self.game.screen_h - self.game.ground_h

        # sky / empty street
        pygame.draw.rect(
            self.game.display,
            (10, 11, 18),
            pygame.Rect(0, 0, self.game.internal_w, floor_y)
        )

        # distant simple buildings
        for x in range(-80, self.game.internal_w + 120, 160):
            pygame.draw.rect(
                self.game.display,
                (18, 19, 28),
                pygame.Rect(x, 160, 100, floor_y - 160)
            )

        # road/floor
        pygame.draw.rect(
            self.game.display,
            (22, 22, 28),
            pygame.Rect(0, floor_y, self.game.internal_w, self.game.ground_h)
        )

        pygame.draw.line(
            self.game.display,
            (65, 65, 75),
            (0, floor_y),
            (self.game.internal_w, floor_y),
            2
        )

        label = "Longer quiet route"
        label_surf = self.small_font.render(label, True, (180, 180, 190))
        self.game.display.blit(label_surf, (20, 20))

        hint = "Fewer people, but the streets feel unfamiliar."
        hint_surf = self.small_font.render(hint, True, (150, 150, 160))
        self.game.display.blit(hint_surf, (20, 42))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit_game()

            if self.game.handle_dev_keys(event): continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_RETURN:
                    return "continue"

        return None