import pygame, random, math, re
from pathlib import Path
from scripts.ui.font import Font
from paths import asset

class PhysicsEntity:
    def __init__(self, game, entity_type, pos, size):
        self.game = game
        self.type = entity_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def update(self, movement=(0, 0)):
        self.pos[0] += movement[0] + self.velocity[0]
        self.pos[1] += movement[1] + self.velocity[1]

    def render(self, surface, offset=(0, 0)):
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            pygame.Rect(
                self.pos[0] - offset[0],
                self.pos[1] - offset[1],
                self.size[0],
                self.size[1],
            ),
        )

class Player(PhysicsEntity):
    def __init__(self, game, player_pos, size=(16, 32)):
        super().__init__(game, "player", player_pos, size)

        self.speed = 120
        self.jump_strength = 260
        self.gravity = 750
        self.max_fall_speed = 420
        self.grounded = False

        # animation folders
        self.idle_dir = Path(asset("assets/entities/player/idle"))
        self.walk_dir = Path(asset("assets/entities/player/walk"))

        self.idle_frames = self.load_frames(
            self.idle_dir, "sloopy_idle*.png", "idle"
        )
        
        if self.idle_frames:
            idle_w, idle_h = self.idle_frames[0].get_size()
            self.game.player_w = idle_w
            self.game.player_h = idle_h
            self.size = (idle_w, idle_h)

        self.walk_frames = self.load_frames(
            self.walk_dir, "*.png", "walk"
        )

        self.sprite_default_facing = "right"

        self.animation_state = "idle"
        self.frame_index = 0
        self.animation_timer = 0

        self.idle_frame_time = 0.18
        self.walk_frame_time = 0.12

        self.last_movement_x = 0

        self.outfit = "default"
        self.outfit_img = None

        self.base_image = None
        if self.idle_frames:
            self.base_image = self.idle_frames[0]
        elif self.walk_frames:
            self.base_image = self.walk_frames[0]

        if self.base_image:
            old_bottom = self.pos[1] + self.size[1]
            self.size = self.base_image.get_size()
            self.pos[1] = old_bottom - self.size[1]

            self.game.player_w = self.size[0]
            self.game.player_h = self.size[1]

    def load_outfit(self, path: str) -> pygame.Surface | None:
        try:
            img = pygame.image.load(path).convert()
            img.set_colorkey((255, 255, 255))
            img = self.scale_to_width(img, 64)
            return img
        except pygame.error as e:
            print(f"[player] failed to load outfit {path}: {e}")
            return None

    def set_outfit(self, outfit: str):
        # outfit: "default" | "back" | "outdoors"
        self.outfit = outfit
        if outfit == "back":
            self.outfit_img = self.load_outfit(asset("assets/entities/player/sloopy_back.png"))
        elif outfit == "outdoors":
            self.outfit_img = self.load_outfit(asset("assets/entities/player/sloopy_outdoors.png"))
        else:
            self.outfit_img = None
            
    def fit_sprite_to_canvas(self, img, canvas_size):
        canvas_w, canvas_h = canvas_size
        visible_rect = img.get_bounding_rect()
        if visible_rect.width == 0 or visible_rect.height == 0:
            return pygame.Surface(canvas_size, pygame.SRCALPHA)
        cropped = img.subsurface(visible_rect).copy()
        scale = min(
            canvas_w / cropped.get_width(),
            canvas_h / cropped.get_height()
        )
        new_w = int(cropped.get_width() * scale)
        new_h = int(cropped.get_height() * scale)
        scaled = pygame.transform.scale(cropped, (new_w, new_h))
        final_img = pygame.Surface(canvas_size, pygame.SRCALPHA)
        x = (canvas_w - new_w) // 2
        y = canvas_h - new_h
        final_img.blit(scaled, (x, y))
        return final_img
    
    def scale_to_width(self, img, target_w):
        orig_w, orig_h = img.get_size()
        scale = target_w / orig_w
        return pygame.transform.scale(img, (target_w, int(orig_h * scale)))

    def load_frames(self, folder: Path, pattern: str, animation_name: str) -> list:
        if not folder.exists():
            print(f"[player] {animation_name} folder not found: {folder}")
            return []

        def frame_number(path: str) -> int:
            match = re.search(r"(\d+)", path.stem)
            return int(match.group(1)) if match else 0

        frame_paths = sorted(folder.glob(pattern), key=frame_number)
        frames = []
        for path in frame_paths:
            try:
                img = pygame.image.load(str(path)).convert_alpha()

                if animation_name == "walk":
                    img = self.fit_to_idle_visible_size(img)

                img = self.scale_to_width(img, 64)  # ← add this
                frames.append(img)

            except pygame.error as error:
                print(f"[player] failed to load {path}: {error}")

        if not frames:
            print(f"[player] no {animation_name} frames found in {folder}")
        return frames
    
    def jump(self):
        if self.grounded:
            self.velocity[1] = -self.jump_strength
            self.grounded = False

    def update(self, movement=(0, 0), dt=1 / 60):
        self.last_movement_x = movement[0]

        self.velocity[1] += self.gravity * dt
        self.velocity[1] = min(self.velocity[1], self.max_fall_speed)

        self.pos[0] += movement[0]
        self.pos[1] += self.velocity[1] * dt

        ground_y = self.game.screen_h - self.game.ground_h - self.size[1] - 50

        if self.pos[1] >= ground_y:
            self.pos[1] = ground_y
            self.velocity[1] = 0
            self.grounded = True
        else:
            self.grounded = False

        self.update_animation(dt)

    def update_animation(self, dt):
        moving = abs(self.last_movement_x) > 0.01

        if moving and self.walk_frames:
            new_state = "walk"
            frames = self.walk_frames
            frame_time = self.walk_frame_time
        else:
            new_state = "idle"
            frames = self.idle_frames
            frame_time = self.idle_frame_time

        if not frames: return
        if new_state != self.animation_state:
            self.animation_state = new_state
            self.frame_index = 0
            self.animation_timer = 0

        self.animation_timer += dt
        while self.animation_timer >= frame_time:
            self.animation_timer -= frame_time
            self.frame_index = (self.frame_index + 1) % len(frames)

    def flip(self, image):
        return pygame.transform.flip(image, True, False)
    
    def get_current_image(self):
        if self.outfit_img is not None: return self.outfit_img

        if self.animation_state == "walk" and self.walk_frames:
            frames = self.walk_frames
        elif self.idle_frames:
            frames = self.idle_frames
        elif self.walk_frames:
            frames = self.walk_frames
        else:
            return None

        image = frames[self.frame_index % len(frames)]
        if self.game.player_facing != self.sprite_default_facing:
            image = self.flip(image)
        return image

    def render(self, surface, offset=(0, 0)):
        image = self.get_current_image()
        if image is None:
            pygame.draw.rect(
                surface,
                (255, 255, 255),
                pygame.Rect(
                    self.pos[0] - offset[0],
                    self.pos[1] - offset[1],
                    self.size[0],
                    self.size[1],
                ),
            )
            return

        rot = float(getattr(self, "rotation", 0.0))
        if abs(rot) > 0.01:
            rotated = pygame.transform.rotate(image, rot)
            orig_w, orig_h = image.get_size()
            new_w, new_h = rotated.get_size()
            bx = self.pos[0] - offset[0] + orig_w // 2
            by = self.pos[1] - offset[1] + orig_h
            x = int(bx - new_w // 2)
            y = int(by - new_h)
            surface.blit(rotated, (x, y))
            return

        x = int(self.pos[0] - offset[0])
        y = int(self.pos[1] - offset[1])
        surface.blit(image, (x, y))

    def get_visible_rect(self, img):
        rect = img.get_bounding_rect()
        if rect.width <= 0 or rect.height <= 0:
            return pygame.Rect(0, 0, img.get_width(), img.get_height())
        return rect

    def fit_to_idle_visible_size(self, img):
        if not self.idle_frames:
            return pygame.transform.scale(img, (self.game.player_w, self.game.player_h))
        
        idle_img = self.idle_frames[0]
        idle_rect = self.get_visible_rect(idle_img)
        walk_rect = self.get_visible_rect(img)
        cropped_walk = img.subsurface(walk_rect).copy()
        scale = idle_rect.height / cropped_walk.get_height()

        new_w = max(1, int(cropped_walk.get_width() * scale))
        new_h = max(1, int(cropped_walk.get_height() * scale))

        scaled_walk = pygame.transform.scale(cropped_walk, (new_w, new_h))
        final_img = pygame.Surface(idle_img.get_size(), pygame.SRCALPHA)
        x = idle_rect.centerx - new_w // 2
        y = idle_rect.bottom - new_h
        final_img.blit(scaled_walk, (x, y))
        return final_img

class NPC(PhysicsEntity):
    def __init__(self, game, name, pos, size=(16, 32), dialogue=None):
        super().__init__(game, "npc", pos, size)

        self.name = name
        self.dialogue = dialogue or []
        self.dialogue_index = 0
        self.interact_distance = 45
        self.talking = False
        self.npc_font = Font(asset("assets/fonts/large_font_red.png"), scale=1)

    def is_player_close(self, player):
        return self.rect().inflate(self.interact_distance, self.interact_distance).colliderect(player.rect())

    def interact(self):
        if not self.talking:
            self.talking = True
            self.dialogue_index = 0
        else:
            self.dialogue_index += 1

            if self.dialogue_index >= len(self.dialogue):
                self.talking = False
                self.dialogue_index = 0

    def render(self, surface, offset=(0, 0)):
        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]

        pygame.draw.rect(surface, (200, 80, 80), pygame.Rect(x, y, self.size[0], self.size[1]))

        name_x = x + self.size[0] // 2
        name_y = y - 14
        self.npc_font.render(surface, self.name, (name_x - 10, name_y))
        return
        
    def render_dialogue(self, surface, offset=(0, 0)):
        if not self.talking or not self.dialogue: return

        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]

        text = self.dialogue[self.dialogue_index]
        max_width = 180
        lines = self.npc_font.wrap_text(text, max_width)

        line_height = next(iter(self.npc_font.characters.values())).get_height()
        total_height = len(lines) * (line_height + 2)

        prompt_x = x + self.size[0] // 2 - max_width // 2
        prompt_y = y - 10 - total_height

        prompt_x = max(5, min(prompt_x, self.game.internal_w - max_width - 5))

        self.npc_font.render_wrapped(surface, text, (prompt_x, prompt_y), max_width)
        return
    
class Ghost(PhysicsEntity):
    def __init__(self, game, name, pos, size=(16, 32), dialogue=None, move_to=(0, 0), color=(255, 255, 255)):
        super().__init__(game, "ghost", pos, size)

        self.name = name
        self.dialogue = dialogue or []
        self.dialogue_index = 0
        self.talking = True
        self.dialogue_timer = 0
        self.dialogue_delay = 2000 #ms
        self.last_dialogue_change = pygame.time.get_ticks()

        if self.dialogue:
            self.dialogue_index = random.randrange(len(self.dialogue))
            
        self.start_pos = list(pos)
        self.pos = list(pos)
        self.move_to = list(move_to)

        self.color = color
        self.alpha = 85

        self.speed = random.uniform(0.008, 0.014)
        self.progress = 0
        self.reached_target = False

        self.wave_offset = random.uniform(0, math.tau)
        self.wave_strength = random.uniform(8, 18)

        self.trail = []
        self.max_trail = 12

        self.fading = False
        self.fade_speed = 3

        self.ghost_font_white = Font(asset("assets/fonts/large_font_white.png"), scale=1)
        self.ghost_font_red = Font(asset("assets/fonts/large_font_red.png"), scale=1)
        self.previous_dialogue_type = None
        self.glitch_until = 0

        self.red_repeat_count = 0
        self.red_text_scale = 1
        self.force_red_until = 0

    def start_fade(self):
        self.fading = True

    def update(self, movement=(0, 0)):
        now = pygame.time.get_ticks()

        if self.dialogue:
            if now - self.last_dialogue_change >= self.dialogue_delay:
                stress = self.game.heart_rate.stress_amount()

                current_type = self.dialogue[self.dialogue_index][0]

                # red dialogue becomes more likely as stress increases
                red_chance = 0.25 + stress * 0.55

                if random.random() < red_chance:
                    negative_indexes = [
                        i for i, d in enumerate(self.dialogue)
                        if d[0] == "negative"
                    ]

                    if negative_indexes:
                        new_index = random.choice(negative_indexes)

                        if current_type == "negative":
                            self.red_repeat_count += 1
                        else:
                            self.red_repeat_count = 1

                        self.dialogue_index = new_index
                        self.glitch_until = now + 350
                        self.game.heart_rate.add_stress_unit(1)

                else:
                    self.red_repeat_count = 0
                    self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)

                self.last_dialogue_change = now

                # dialogue gets faster as stress rises
                self.dialogue_delay = int(2200 - stress * 1200)
                self.dialogue_delay = max(650, self.dialogue_delay)

        if self.fading:
            self.alpha -= self.fade_speed

            if self.trail:
                self.trail.pop(0)

            if self.alpha <= 0:
                self.alpha = 0
            return

        if self.reached_target:
            if self.trail:
                self.trail.pop(0)
            return

        self.trail.append(self.pos.copy())
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

        self.progress += self.speed

        if self.progress >= 1:
            self.progress = 1
            self.reached_target = True
            self.pos = self.move_to.copy()
            return

        t = self.progress
        smooth_t = 1 - pow(1 - t, 3)

        start_x, start_y = self.start_pos
        end_x, end_y = self.move_to

        base_x = start_x + (end_x - start_x) * smooth_t
        base_y = start_y + (end_y - start_y) * smooth_t

        wave_x = math.sin(t * math.tau * 2 + self.wave_offset) * self.wave_strength
        wave_y = math.cos(t * math.tau * 1.5 + self.wave_offset) * self.wave_strength * 0.5

        self.pos[0] = base_x + wave_x
        self.pos[1] = base_y + wave_y

    def render(self, surface, offset=(0, 0)):
        for i, trail_pos in enumerate(self.trail):
            alpha = int((i / self.max_trail) * 45)
            self.render_body(surface, trail_pos, offset, alpha)
        self.render_body(surface, self.pos, offset, self.alpha)

    def render_body(self, surface, pos, offset, alpha):
        x = int(pos[0] - offset[0])
        y = int(pos[1] - offset[1])
        ghost_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        if not self.reached_target:
            radius = min(self.size[0], self.size[1]) // 2
            center = (self.size[0] // 2, self.size[1] // 2)
            pygame.draw.circle(
                ghost_surf,
                (45, 45, 45, alpha),
                center,
                radius
            )
            pygame.draw.circle(
                ghost_surf,
                (95, 95, 95, int(alpha * 0.45)),
                (center[0] - 3, center[1] - 3),
                max(2, radius // 2)
            )
        else:
            pygame.draw.ellipse(
                ghost_surf,
                (35, 35, 35, alpha),
                pygame.Rect(0, 0, self.size[0], self.size[1])
            )
        surface.blit(ghost_surf, (x, y))

    def render_dialogue(self, surface, offset=(0, 0)):
        if not self.dialogue: return
        
        dialogue_type, text = self.dialogue[self.dialogue_index]
        x = self.pos[0] - offset[0] - 20
        y = self.pos[1] - offset[1] - 14

        now = pygame.time.get_ticks()
        is_glitching = now < self.glitch_until

        if dialogue_type == "negative":
            font = self.ghost_font_red
            scale = 1 + min(self.red_repeat_count * 0.25, 1.5)
        else:
            font = self.ghost_font_white
            scale = 1

        max_width = 200
        lines = font.wrap_text(text, max_width)

        line_height = next(iter(font.characters.values())).get_height()
        total_height = len(lines) * (line_height + 2)

        temp_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)

        font.render_wrapped(temp_surface, text, (0, 0), max_width)

        if scale != 1:
            new_w = int(temp_surface.get_width() * scale)
            new_h = int(temp_surface.get_height() * scale)
            temp_surface = pygame.transform.scale(temp_surface, (new_w, new_h))

        if is_glitching:
            for _ in range(3):
                jitter_x = random.randint(-4, 4)
                jitter_y = random.randint(-2, 2)
                surface.blit(temp_surface, (x + jitter_x, y + jitter_y))

        surface.blit(temp_surface, (x, y))

class Follower(PhysicsEntity):
    def __init__(self, game, name, pos, size=(20, 48), color=(0, 0, 0)):
        super().__init__(game, "follower", pos, size)

        self.name = name
        self.color = color
        self.alpha = 120

        self.alive = True
        self.following = False

        self.speed = 0.45

        self.frozen = False
        self.freeze_duration = 1500
        self.freeze_start_time = 0

        self.dialogue_pool = [
            "they noticed that",
            "why are you stopping?",
            "you look weird",
            "keep walking",
            "don't mess this up",
            "everyone is watching",
            "what are you doing?",
            "wait",
            "check behind you",
            "they know",
        ]

        self.current_text = ""
        self.last_comment_time = 0
        self.comment_delay = random.randint(2200, 5200)
        self.comment_visible_time = 1600
        self.follower_font = Font(asset("assets/fonts/large_font_white.png"), scale=1)

    def is_behind_player(self, player, player_facing):
        follower_x = self.pos[0]
        player_x = player.pos[0]

        if player_facing == "left" and follower_x > player_x: return True
        if player_facing == "right" and follower_x < player_x: return True
        return False

    def freeze(self):
        self.frozen = True
        self.freeze_start_time = pygame.time.get_ticks()

    def update(self, player, player_facing):
        if not self.alive: return
        now = pygame.time.get_ticks()
        if now - self.last_comment_time >= self.comment_delay:
            self.current_text = random.choice(self.dialogue_pool)
            self.last_comment_time = now
            self.comment_delay = random.randint(2200, 5200)

        if self.frozen:
            if now - self.freeze_start_time >= self.freeze_duration:
                self.frozen = False
            else:
                return
            
        distance_x = abs(player.pos[0] - self.pos[0])
        speed = self.speed
        if distance_x >= 50: self.pos[0] += speed
        
        behind_player = self.is_behind_player(player, player_facing)
        if behind_player:
            self.following = True
        else:
            if self.following and not self.frozen:
                self.freeze()
            self.following = False
            return
        
        if self.following:
            if self.pos[0] < player.pos[0]:
                self.pos[0] += self.speed
            elif self.pos[0] > player.pos[0]:
                self.pos[0] -= speed
            target_y = player.pos[1] + player.size[1] - self.size[1]
            self.pos[1] += (target_y - self.pos[1]) * 0.08

    def render(self, surface, offset=(0, 0)):
        if not self.alive: return
        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]
        follower_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        alpha = self.alpha
        if self.frozen: alpha = 60
        follower_surf.fill((*self.color, alpha))
        surface.blit(follower_surf, (x, y))
        if self.current_text:
            self.game.hint_font.render(surface, self.current_text, (x, y - 14))
    
    def render_dialogue(self, surface, offset=(0, 0)):
        if not self.current_text: return
        now = pygame.time.get_ticks()
        if now - self.last_comment_time > self.comment_visible_time: return
        x = self.pos[0] - offset[0]
        y = self.pos[1] - offset[1]

        jitter_x = random.randint(-1, 1)
        jitter_y = random.randint(-1, 1)

        max_width = 140

        self.follower_font.render_wrapped(
            surface,
            self.current_text,
            (x - 60 + jitter_x, y - 20 + jitter_y),
            max_width
        )