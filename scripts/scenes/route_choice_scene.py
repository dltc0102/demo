import pygame
import random
import math


class RouteChoiceScene:
    def __init__(self, game):
        self.game = game

        self.title_font = pygame.font.SysFont("arial", 28)
        self.font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 15)

        self.route_quiet_rect = pygame.Rect(80, 145, 560, 95)
        self.route_busy_rect = pygame.Rect(80, 285, 560, 95)

        self.player_base_y = self.game.screen_h - self.game.ground_h - self.game.player_h - 50
        self.left_bound = 235
        self.right_bound = 485

        self.pace_direction = 1
        self.pace_speed = 65
        self.pace_state = "walking"
        self.pace_timer = 0
        self.next_stress_stop = random.randint(1600, 3800)
        self.stress_hold_time = 1200

        self.look_direction_timer = 0
        self.look_direction_delay = 250
        self.stress_look_direction = "left"

        self.thought_timer = 0
        self.next_thought_time = 1200

        self.decision_thoughts = [
            "too many people...",
            "what if I get lost?",
            "I know one road...",
            "but everyone will see me",
            "why is this hard?",
            "just choose",
            "no, wait",
            "what if I choose wrong?",
            "I should go now",
            "I can't think"
        ]

        self.hovered_route = None

    def reset(self):
        self.game.player.pos = [
            self.game.internal_w // 2 - self.game.player_w // 2,
            self.player_base_y
        ]

        self.game.player.velocity = [0, 0]
        self.game.player_movement = [0, 0]
        self.game.player_facing = "right"

        self.pace_direction = 1
        self.pace_state = "walking"
        self.pace_timer = 0
        self.next_stress_stop = random.randint(1600, 3800)
        self.thought_timer = 0
        self.next_thought_time = 900

        self.game.cutscene.stop()

    def run(self):
        self.reset()

        while True:
            dt = self.game.clock.get_time() / 1000

            self.game.display.fill((9, 10, 14))

            self.handle_pacing(dt)
            self.update_thoughts(dt)

            self.render_background()
            self.render_map()
            self.render_hint()

            self.game.player.update(self.game.player_movement, dt)
            self.game.player.render(self.game.display)

            self.game.thought_manager.update(dt)
            self.game.dialogue_manager.update()

            self.game.thought_manager.render(self.game.display)
            self.game.dialogue_manager.render(self.game.display)

            result = self.handle_events()
            if result:
                return result

            self.game.handle_pause_button()
            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)

    def handle_pacing(self, dt):
        self.game.player_movement = [0, 0]
        self.pace_timer += dt * 1000

        if self.pace_state == "walking":
            movement_x = self.pace_direction * self.pace_speed * dt
            self.game.player_movement[0] = movement_x

            if self.pace_direction < 0:
                self.game.player_facing = "left"
            else:
                self.game.player_facing = "right"

            next_x = self.game.player.pos[0] + movement_x

            if next_x <= self.left_bound:
                self.pace_direction = 1

            elif next_x >= self.right_bound:
                self.pace_direction = -1

            if self.pace_timer >= self.next_stress_stop:
                self.pace_state = "stressed"
                self.pace_timer = 0
                self.stress_hold_time = random.randint(800, 1800)
                self.look_direction_timer = 0
                self.game.player_movement = [0, 0]

                if random.random() < 0.65:
                    self.spawn_random_thought()

        elif self.pace_state == "stressed":
            self.game.player_movement = [0, 0]
            self.look_direction_timer += dt * 1000

            if self.look_direction_timer >= self.look_direction_delay:
                self.look_direction_timer = 0

                if self.stress_look_direction == "left":
                    self.stress_look_direction = "right"
                else:
                    self.stress_look_direction = "left"

                self.game.player_facing = self.stress_look_direction

            if self.pace_timer >= self.stress_hold_time:
                self.pace_state = "walking"
                self.pace_timer = 0
                self.next_stress_stop = random.randint(1600, 4200)

                if random.random() < 0.5:
                    self.pace_direction *= -1

    def update_thoughts(self, dt):
        self.thought_timer += dt * 1000

        if self.thought_timer >= self.next_thought_time:
            self.thought_timer = 0
            self.next_thought_time = random.randint(1500, 3600)
            self.spawn_random_thought()

    def spawn_random_thought(self):
        thought = random.choice(self.decision_thoughts)

        if random.random() < 0.55:
            self.game.thought_manager.cloudthink(
                thought,
                self.game.player,
                stall=random.randint(1100, 1800)
            )
        else:
            self.game.thought_manager.racethink(
                thought,
                self.game.player,
                stall=random.randint(650, 1000)
            )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_1:
                    return "quiet_route"

                if event.key == pygame.K_2:
                    return "busy_route"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = self.get_mouse_pos()

                if self.route_quiet_rect.collidepoint(mx, my):
                    return "quiet_route"

                if self.route_busy_rect.collidepoint(mx, my):
                    return "busy_route"

        mx, my = self.get_mouse_pos()

        if self.route_quiet_rect.collidepoint(mx, my):
            self.hovered_route = "quiet"
        elif self.route_busy_rect.collidepoint(mx, my):
            self.hovered_route = "busy"
        else:
            self.hovered_route = None

        return None

    def get_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)

    def render_background(self):
        floor_y = self.game.screen_h - self.game.ground_h

        pygame.draw.rect(
            self.game.display,
            (18, 18, 24),
            pygame.Rect(0, floor_y, self.game.internal_w, self.game.ground_h)
        )

        pygame.draw.line(
            self.game.display,
            (55, 55, 65),
            (0, floor_y),
            (self.game.internal_w, floor_y),
            2
        )

        title = "Which route should I take?"
        title_surf = self.title_font.render(title, True, (245, 245, 245))
        self.game.display.blit(
            title_surf,
            (self.game.internal_w // 2 - title_surf.get_width() // 2, 32)
        )

        subtitle = "Both routes feel uncomfortable for different reasons."
        subtitle_surf = self.small_font.render(subtitle, True, (185, 185, 195))
        self.game.display.blit(
            subtitle_surf,
            (self.game.internal_w // 2 - subtitle_surf.get_width() // 2, 68)
        )

    def render_map(self):
        self.draw_route_card(
            rect=self.route_quiet_rect,
            route_key="quiet",
            label="1. Longer route",
            description="Less people, quieter streets, but parts are unfamiliar.",
            tags=["quiet", "long", "unfamiliar"]
        )

        self.draw_route_card(
            rect=self.route_busy_rect,
            route_key="busy",
            label="2. Shorter route",
            description="More familiar and faster, but much more crowded.",
            tags=["busy", "short", "familiar"]
        )

        home_pos = (130, 455)
        shop_pos = (590, 455)

        pygame.draw.circle(self.game.display, (220, 220, 230), home_pos, 18)
        pygame.draw.circle(self.game.display, (220, 220, 230), shop_pos, 18)

        home_text = self.small_font.render("HOME", True, (20, 20, 25))
        shop_text = self.small_font.render("SHOP", True, (20, 20, 25))

        self.game.display.blit(home_text, (home_pos[0] - home_text.get_width() // 2, home_pos[1] - 7))
        self.game.display.blit(shop_text, (shop_pos[0] - shop_text.get_width() // 2, shop_pos[1] - 7))

        self.draw_curved_route(home_pos, shop_pos, -65, (110, 110, 130))
        self.draw_curved_route(home_pos, shop_pos, 35, (90, 90, 110))

    def draw_route_card(self, rect, route_key, label, description, tags):
        is_hovered = self.hovered_route == route_key

        bg = (32, 34, 44) if not is_hovered else (48, 50, 64)
        border = (90, 90, 105) if not is_hovered else (180, 180, 205)

        pygame.draw.rect(self.game.display, bg, rect, border_radius=14)
        pygame.draw.rect(self.game.display, border, rect, 2, border_radius=14)

        label_surf = self.font.render(label, True, (245, 245, 245))
        desc_surf = self.small_font.render(description, True, (195, 195, 205))

        self.game.display.blit(label_surf, (rect.x + 22, rect.y + 16))
        self.game.display.blit(desc_surf, (rect.x + 22, rect.y + 43))

        tag_x = rect.x + 22
        tag_y = rect.y + 66

        for tag in tags:
            tag_surf = self.small_font.render(tag, True, (225, 225, 235))
            tag_rect = pygame.Rect(tag_x, tag_y, tag_surf.get_width() + 18, 22)

            pygame.draw.rect(self.game.display, (55, 57, 70), tag_rect, border_radius=11)
            self.game.display.blit(tag_surf, (tag_rect.x + 9, tag_rect.y + 3))

            tag_x += tag_rect.width + 8

    def draw_curved_route(self, start, end, curve_height, color):
        points = []

        for i in range(32):
            t = i / 31
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + math.sin(t * math.pi) * curve_height
            points.append((x, y))

        if len(points) >= 2:
            pygame.draw.lines(self.game.display, color, False, points, 3)

    def render_hint(self):
        hint = "Click a route, or press 1 / 2"
        hint_surf = self.small_font.render(hint, True, (160, 160, 170))

        self.game.display.blit(
            hint_surf,
            (self.game.internal_w // 2 - hint_surf.get_width() // 2, 408)
        )