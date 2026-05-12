import pygame, math, random
from demo_game.scripts.ui.font import Font
from demo_game.paths import asset

class BaseThought:
    def __init__(self, lines: str | list[str], target, stall: int) -> None:
        self.lines: list[str] = lines if isinstance(lines, list) else [lines]
        self.target = target
        self.font: Font = Font(asset("assets/fonts/large_font_white.png"), scale=1)

        self.idx: int = 0
        self.line_start: int = pygame.time.get_ticks()

        self.fade: int = 350
        self.stall: int = stall
        self.finished: bool = False

        self.h: int = next(iter(self.font.characters.values())).get_height() + 8
        self.w: int = 1

        self.update_size()

    def current_text(self) -> str:
        return self.lines[self.idx]

    def line_duration(self) -> int:
        word_count: int = max(1, len(self.current_text().split()))
        return self.fade + self.stall + word_count * 140 + self.fade

    def update_size(self) -> None:
        self.w = max(1, self.font.text_width(self.current_text()))

    def alpha(self) -> int:
        now: int = pygame.time.get_ticks()
        age: int = now - self.line_start
        duration: int = self.line_duration()
        if age < self.fade:
            return int(255 * age / self.fade)

        if age > duration - self.fade:
            fade_age: int = age - (duration - self.fade)
            return int(255 * max(0, 1 - fade_age / self.fade))
        return 255

    def advance_line_if_needed(self) -> None:
        now: int = pygame.time.get_ticks()
        if now - self.line_start < self.line_duration(): return
        self.idx += 1
        if self.idx >= len(self.lines):
            self.finished = True
            return
        self.line_start = now
        self.update_size()

    def render_text(self, surface: pygame.Surface, text: str) -> None:
        x: int = 0
        for char in text:
            if char == " ":
                x += self.font.space_width + self.font.spacing
                continue

            if char not in self.font.characters:
                continue

            char_img: pygame.Surface = self.font.characters[char]
            surface.blit(char_img, (x, 0))
            x += char_img.get_width() + self.font.spacing

    def make_text_surface(self) -> pygame.Surface:
        text: str = self.current_text()
        surf: pygame.Surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.render_text(surf, text)
        surf.set_alpha(max(0, min(255, self.alpha())))
        return surf

class CloudThought(BaseThought):
    def __init__(
        self,
        lines: str | list[str],
        target,
        stall: int = 1400
    ) -> None:
        super().__init__(lines, target, stall)

        line_count = len(self.lines)

        if line_count < 3:
            self.bounds_w = 180
            self.bounds_h = 140
            spawn_x = 50
            spawn_y_top = 40
        else:
            self.bounds_w = 420
            self.bounds_h = 320
            spawn_x = 140
            spawn_y_top = 120

        self.x: float = random.uniform(-spawn_x, spawn_x)
        self.y: float = random.uniform(-spawn_y_top, 20)

        self.vx: float = random.uniform(-16, 16)
        self.vy: float = random.uniform(-18, -6)

    def update(self, dt: float, others: list["CloudThought"]) -> None:
        if self.finished:
            return

        self.advance_line_if_needed()

        if self.finished:
            return

        self.vy -= 4 * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.vx *= 0.985
        self.vy *= 0.985

        self.vx += random.uniform(-2, 2) * dt
        self.vy += random.uniform(-2, 2) * dt

        self.keep_inside_bounds()
        self.resolve_collisions(dt, others)

    def keep_inside_bounds(self) -> None:
        center_x = 0
        center_y = -self.bounds_h * 0.5

        radius = min(self.bounds_w, self.bounds_h) * 0.5

        thought_center_x = self.x + self.w * 0.5
        thought_center_y = self.y + self.h * 0.5

        dx = thought_center_x - center_x
        dy = thought_center_y - center_y

        dist = math.hypot(dx, dy)

        if dist > radius:
            nx = dx / dist
            ny = dy / dist

            thought_center_x = center_x + nx * radius
            thought_center_y = center_y + ny * radius

            self.x = thought_center_x - self.w * 0.5
            self.y = thought_center_y - self.h * 0.5

            dot = self.vx * nx + self.vy * ny

            self.vx -= 2 * dot * nx
            self.vy -= 2 * dot * ny

            self.vx *= 0.6
            self.vy *= 0.6

    def resolve_collisions(
        self,
        dt: float,
        others: list["CloudThought"]
    ) -> None:
        my_rect = pygame.Rect(
            int(self.x),
            int(self.y),
            self.w,
            self.h
        )

        for other in others:
            if other is self or other.finished:
                continue

            other_rect = pygame.Rect(
                int(other.x),
                int(other.y),
                other.w,
                other.h
            )

            if not my_rect.colliderect(other_rect):
                continue

            dx = my_rect.centerx - other_rect.centerx
            dy = my_rect.centery - other_rect.centery

            if dx == 0 and dy == 0:
                dx = random.choice([-1, 1])
                dy = random.choice([-1, 1])

            dist = max(1.0, math.hypot(dx, dy))

            push = 12 * dt

            self.x += dx / dist * push
            self.y += dy / dist * push

            self.vx += dx / dist * 2
            self.vy += dy / dist * 2

    def render(
        self,
        surface: pygame.Surface,
        offset: tuple[int | float, int | float] = (0, 0)
    ) -> None:
        if self.finished:
            return

        target_rect = self.target.rect()

        base_x = target_rect.centerx - offset[0]
        base_y = target_rect.top - offset[1] - 28

        text_surf = self.make_text_surface()

        surface.blit(
            text_surf,
            (
                int(base_x + self.x),
                int(base_y + self.y)
            )
        )

class RaceThought(BaseThought):
    def __init__(self, lines: str | list[str], target, stall: int = 700) -> None:
        super().__init__(lines, target, stall)
        self.y_offset: int = random.randint(-75, -35)

    def progress(self) -> float:
        age: int = pygame.time.get_ticks() - self.line_start
        return min(1.0, age / self.line_duration())

    def update(self, dt: float) -> None:
        if self.finished: return
        self.advance_line_if_needed()

    def render(self, surface: pygame.Surface, offset: tuple[int | float, int | float] = (0, 0)) -> None:
        if self.finished: return
        p: float = self.progress()
        target_rect: pygame.Rect = self.target.rect()
        base_x: float = target_rect.centerx - offset[0]
        base_y: float = target_rect.top - offset[1]
        x: float = base_x - 180 + p * 360
        y: float = base_y + self.y_offset
        text_surf: pygame.Surface = self.make_text_surface()
        surface.blit(text_surf, (int(x), int(y)))

class ShakeThought:
    def __init__(self, text: str, target, stall: int = 1200) -> None:
        self.text = str(text)
        self.target = target
        self.font_white = Font(asset("assets/fonts/large_font_white.png"), scale=1)

        self.stall = stall
        self.start = pygame.time.get_ticks()
        self.finished = False

        self.shake_level = 0
        self.scale = 1.0

        self.glitch_until = 0
        self.escalate_timer = 0
        self.next_escalate = random.randint(300, 600)

    def update(self, dt: float) -> None:
        if self.finished: return
        now = pygame.time.get_ticks()
        self.escalate_timer += dt * 1000
        if self.escalate_timer >= self.next_escalate:
            self.escalate_timer = 0
            self.next_escalate = random.randint(200, 500)
            self.shake_level = min(self.shake_level + 1, 6)
            self.scale = 1 + min(self.shake_level * 0.22, 1.35)
            self.glitch_until = now + random.randint(90, 180)
        if now - self.start >= self.stall:
            self.finished = True

    def glitch_surface(self, source: pygame.Surface) -> pygame.Surface:
        glitched = source.copy()
        width = source.get_width()
        height = source.get_height()
        for _ in range(random.randint(4, 8)):
            slice_h = random.randint(2, 6)
            slice_y = random.randint(0, max(0, height - slice_h))
            offset_x = random.randint(-8, 8)

            slice_rect = pygame.Rect(0, slice_y, width, slice_h)
            slice_surf = source.subsurface(slice_rect).copy()

            glitched.blit(slice_surf, (offset_x, slice_y))
        ghost = source.copy()
        ghost.set_alpha(90)
        glitched.blit(ghost, (random.randint(-3, 3), random.randint(-2, 2)))
        return glitched

    def render(self, surface: pygame.Surface, offset: tuple = (0, 0)) -> None:
        if self.finished: return
        now = pygame.time.get_ticks()
        is_glitching = now < self.glitch_until
        max_width = 200
        raw = pygame.Surface((max_width, 80), pygame.SRCALPHA)
        self.font_white.render_wrapped(raw, self.text, (0, 0), max_width)
        bounds = raw.get_bounding_rect()

        if bounds.width <= 0 or bounds.height <= 0: return
        temp = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
        temp.blit(raw, (0, 0), bounds)
        if self.scale != 1:
            new_w = max(1, int(temp.get_width() * self.scale))
            new_h = max(1, int(temp.get_height() * self.scale))
            temp = pygame.transform.scale(temp, (new_w, new_h))

        if is_glitching: temp = self.glitch_surface(temp)
        target_rect = self.target.rect()
        x = target_rect.centerx - offset[0] - temp.get_width() // 2
        y = target_rect.top - offset[1] - 50
        y += random.randint(-2, 2)
        surface.blit(temp, (int(x), int(y)))

class ThoughtManager:
    def __init__(self) -> None:
        self.cloud_thoughts: list[CloudThought] = []
        self.race_thoughts: list[RaceThought] = []
        self.shake_thoughts: list[ShakeThought] = []

    def shakethink(self, text: str, target, stall: int = 2200) -> "ShakeThought":
        thought = ShakeThought(text, target, stall=stall)
        self.shake_thoughts.append(thought)
        return thought

    def cloudthink(self, lines: str | list[str], target, stall: int = 1400) -> CloudThought:
        thought: CloudThought = CloudThought(lines, target, stall=stall)
        self.cloud_thoughts.append(thought)
        return thought

    def racethink(self, lines: str | list[str], target, stall: int = 700) -> RaceThought:
        thought: RaceThought = RaceThought(lines, target, stall=stall)
        self.race_thoughts.append(thought)
        return thought

    def update(self, dt: float) -> None:
        for thought in self.cloud_thoughts[:]:
            thought.update(dt, self.cloud_thoughts)
            if thought.finished: self.cloud_thoughts.remove(thought)

        for thought in self.race_thoughts[:]:
            thought.update(dt)
            if thought.finished: self.race_thoughts.remove(thought)
        
        for thought in self.shake_thoughts[:]:
            thought.update(dt)
            if thought.finished: self.shake_thoughts.remove(thought)

    def render(self, surface: pygame.Surface, offset: tuple[int | float, int | float] = (0, 0)) -> None:
        for thought in self.cloud_thoughts: thought.render(surface, offset)
        for thought in self.race_thoughts: thought.render(surface, offset)
        for thought in self.shake_thoughts: thought.render(surface, offset)

    def clear(self) -> None:
        self.cloud_thoughts.clear()
        self.race_thoughts.clear()
        self.shake_thoughts.clear()