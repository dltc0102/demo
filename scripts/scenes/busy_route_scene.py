import pygame
import random


class BusyRouteScene:
    def __init__(self, game):
        self.game = game

        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 15)

        self.started = False
        self.scene_ended = False

        self.player_start_x = 80
        self.player_y = self.game.screen_h - self.game.ground_h - self.game.player_h - 50

        self.walk_target_x = 560
        self.auto_walk_speed = 70

        self.crowd = []
        self.crowd_spawn_timer = 0
        self.next_crowd_spawn = 500

        self.freeze_timer = 0
        self.next_freeze = random.randint(1400, 3200)
        self.is_frozen = False
        self.freeze_hold_time = 0

    def reset(self):
        self.started = False
        self.scene_ended = False

        self.game.player.pos = [self.player_start_x, self.player_y]
        self.game.player.velocity = [0, 0]
        self.game.player_movement = [0, 0]
        self.game.player_facing = "right"

        self.crowd = []
        self.crowd_spawn_timer = 0
        self.next_crowd_spawn = 500

        self.freeze_timer = 0
        self.next_freeze = random.randint(1400, 3200)
        self.is_frozen = False
        self.freeze_hold_time = 0

        self.game.cutscene.stop()

    def run(self):
        self.reset()

        while True:
            dt = self.game.clock.get_time() / 1000

            self.game.display.fill((13, 12, 12))

            self.render_background()
            self.update_crowd(dt)
            self.handle_auto_walk(dt)

            self.game.player.update(self.game.player_movement, dt)
            self.render_crowd()
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

        if self.is_frozen:
            self.freeze_timer += dt * 1000
            self.game.player_movement[0] = 0

            # nervous looking around
            if int(self.freeze_timer / 180) % 2 == 0:
                self.game.player_facing = "left"
            else:
                self.game.player_facing = "right"

            if self.freeze_timer >= self.freeze_hold_time:
                self.is_frozen = False
                self.freeze_timer = 0
                self.next_freeze = random.randint(1300, 3000)
                self.game.player_facing = "right"

            return

        if self.game.player.pos[0] < self.walk_target_x:
            self.game.player_movement[0] = self.auto_walk_speed * dt
            self.game.player_facing = "right"

            self.freeze_timer += dt * 1000

            if self.freeze_timer >= self.next_freeze:
                self.is_frozen = True
                self.freeze_timer = 0
                self.freeze_hold_time = random.randint(700, 1400)

                if random.random() < 0.85:
                    self.spawn_crowd_thought()

        else:
            self.game.player_movement[0] = 0

    def spawn_crowd_thought(self):
        thoughts = [
            "walk normally",
            "don't look weird",
            "they noticed",
            "why are they laughing?",
            "too close",
            "keep your head down",
            "don't stop",
            "everyone can tell",
            "just get to the shop",
        ]

        if random.random() < 0.55:
            self.game.thought_manager.racethink(
                random.choice(thoughts),
                self.game.player,
                stall=random.randint(600, 900)
            )
        else:
            self.game.thought_manager.cloudthink(
                random.choice(thoughts),
                self.game.player,
                stall=random.randint(900, 1400)
            )

    def sequence(self):
        self.game.sfx.set_heartbeat_bpm(88, volume=0.25)

        yield from self.game.cutscene.wait(600)

        yield from self.game.cutscene.say(
            "I'll take the normal road.",
            self.game.player
        )

        yield from self.game.cutscene.cloudthink(
            [
                "I know this way",
                "it's faster",
                "just get there",
                "don't think about people",
            ],
            self.game.player,
            stall=1500
        )

        self.game.sfx.set_heartbeat_bpm(105, volume=0.35)

        yield from self.game.cutscene.racethink(
            [
                "too many",
                "too loud",
                "walk normally",
                "don't look at them",
                "they're looking",
            ],
            self.game.player,
            stall=650,
            gap=420
        )

        yield from self.game.cutscene.say(
            [
                "Why does everyone feel so close?",
                "I know they're probably not watching me...",
                "but it feels like they are."
            ],
            self.game.player
        )

        yield from self.game.cutscene.voice("whats_wrong_with_you")

        self.game.sfx.set_heartbeat_bpm(118, volume=0.4)

        yield from self.game.cutscene.cloudthink(
            [
                "act normal",
                "normal normal normal",
                "stop thinking",
                "don't stop walking",
                "why did I come this way?",
            ],
            self.game.player,
            stall=1400
        )

        self.game.sfx.set_heartbeat_bpm(85, volume=0.22)

        yield from self.game.cutscene.wait(900)

        yield from self.game.cutscene.say(
            "Almost there. Just don't stop.",
            self.game.player
        )

        yield from self.game.cutscene.wait(1200)

        self.scene_ended = True

    def update_crowd(self, dt):
        self.crowd_spawn_timer += dt * 1000

        if self.crowd_spawn_timer >= self.next_crowd_spawn:
            self.crowd_spawn_timer = 0
            self.next_crowd_spawn = random.randint(450, 1100)

            person = {
                "x": random.choice([-40, self.game.internal_w + 40]),
                "y": random.randint(300, 410),
                "speed": random.uniform(35, 85),
                "direction": random.choice([-1, 1]),
                "height": random.randint(42, 62),
                "alpha": random.randint(70, 130)
            }

            if person["x"] < 0:
                person["direction"] = 1
            else:
                person["direction"] = -1

            self.crowd.append(person)

        for person in self.crowd[:]:
            person["x"] += person["direction"] * person["speed"] * dt

            if person["x"] < -80 or person["x"] > self.game.internal_w + 80:
                self.crowd.remove(person)

    def render_crowd(self):
        for person in self.crowd:
            surf = pygame.Surface((22, person["height"]), pygame.SRCALPHA)
            pygame.draw.ellipse(
                surf,
                (45, 45, 50, person["alpha"]),
                pygame.Rect(2, 0, 18, 20)
            )
            pygame.draw.rect(
                surf,
                (38, 38, 44, person["alpha"]),
                pygame.Rect(5, 18, 12, person["height"] - 18)
            )

            self.game.display.blit(
                surf,
                (int(person["x"]), int(person["y"]))
            )

    def render_background(self):
        floor_y = self.game.screen_h - self.game.ground_h

        # street background
        pygame.draw.rect(
            self.game.display,
            (18, 16, 17),
            pygame.Rect(0, 0, self.game.internal_w, floor_y)
        )

        # shop fronts / buildings
        for x in range(0, self.game.internal_w, 120):
            pygame.draw.rect(
                self.game.display,
                (30, 28, 32),
                pygame.Rect(x, 150, 90, floor_y - 150)
            )

            pygame.draw.rect(
                self.game.display,
                (55, 50, 45),
                pygame.Rect(x + 18, 190, 52, 36)
            )

        # floor
        pygame.draw.rect(
            self.game.display,
            (27, 25, 26),
            pygame.Rect(0, floor_y, self.game.internal_w, self.game.ground_h)
        )

        pygame.draw.line(
            self.game.display,
            (80, 74, 74),
            (0, floor_y),
            (self.game.internal_w, floor_y),
            2
        )

        label = "Shorter busy route"
        label_surf = self.small_font.render(label, True, (190, 180, 180))
        self.game.display.blit(label_surf, (20, 20))

        hint = "Familiar and faster, but crowded and overwhelming."
        hint_surf = self.small_font.render(hint, True, (160, 150, 150))
        self.game.display.blit(hint_surf, (20, 42))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_RETURN:
                    return "continue"

        return None