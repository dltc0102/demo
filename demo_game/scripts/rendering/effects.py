import pygame, math, random

class Effects:
    def __init__(self, game) -> None:
        self.game = game

    def get_internal_mouse_pos(self) -> tuple[int, int]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x = int(mouse_x / self.game.scale_x)
        mouse_y = int(mouse_y / self.game.scale_y)
        return mouse_x, mouse_y

    def render_fade(self, alpha: int | float) -> None:
        fade = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
        fade.fill((0, 0, 0, int(alpha)))
        self.game.display.blit(fade, (0, 0))

    def destabilize_backgrounds(self) -> None:
        self.render_glitch(slices=45, max_offset=10, dark_alpha=65, speed=90, jitter_chance=0.35, big_jump_chance=0.08)
        self.render_screen_warp(strength=5, wave_size=24, speed=0.006, step=2)

    def render_glitch(self, slices: int = 45, max_offset: int = 10, dark_alpha: int = 0, speed: int = 90, jitter_chance: float = 0.35, big_jump_chance: float = 0.08, strength: int | None = None) -> None:
        if strength is not None:
            max_offset = strength

        max_offset = max(1, max_offset)

        original: pygame.Surface = self.game.display.copy()
        glitched: pygame.Surface = original.copy()

        screen_w, screen_h = self.game.display.get_size()
        slice_h: int = max(1, screen_h // slices)
        tick: int = pygame.time.get_ticks() // speed

        for i in range(slices):
            y: int = i * slice_h
            h: int = slice_h

            if y + h > screen_h:
                h = screen_h - y

            base_offset: int = ((tick + i * 19) % (max_offset * 2)) - max_offset

            if (tick + i * 7) % 100 > jitter_chance * 100:
                offset: int = 0
            else:
                offset = base_offset

            if (tick + i * 13) % 100 < big_jump_chance * 100:
                offset *= 2

            slice_rect = pygame.Rect(0, y, screen_w, h)
            slice_img = original.subsurface(slice_rect).copy()
            glitched.blit(slice_img, (offset, y))

        self.game.display.blit(glitched, (0, 0))

        if dark_alpha > 0:
            overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, dark_alpha))
            self.game.display.blit(overlay, (0, 0))

    def render_screen_warp(self, strength: int = 4, wave_size: int = 28, speed: float = 0.006, step: int = 2, intensity: int | None = None) -> None:
        if intensity is not None:
            strength = intensity

        original: pygame.Surface = self.game.display.copy()
        tick: float = pygame.time.get_ticks() * speed

        for y in range(0, self.game.internal_h, step):
            wave: float = math.sin((y / wave_size) + tick)
            offset_x: int = int(wave * strength)

            source_rect = pygame.Rect(0, y, self.game.internal_w, step)
            slice_img = original.subsurface(source_rect).copy()

            self.game.display.blit(slice_img, (offset_x, y))

    def render_cursor_magnet(self, radius: int = 70, strength: float = 0.35, step: int = 2) -> None:
        mouse_x, mouse_y = self.get_internal_mouse_pos()
        original: pygame.Surface = self.game.display.copy()

        for y in range(mouse_y - radius, mouse_y + radius, step):
            for x in range(mouse_x - radius, mouse_x + radius, step):
                dx: int = mouse_x - x
                dy: int = mouse_y - y
                distance: float = math.sqrt(dx * dx + dy * dy)

                if distance == 0 or distance > radius:
                    continue

                pull: float = (1 - distance / radius) * strength

                source_x: int = int(x + dx * pull)
                source_y: int = int(y + dy * pull)

                if 0 <= x < self.game.internal_w and 0 <= y < self.game.internal_h and 0 <= source_x < self.game.internal_w and 0 <= source_y < self.game.internal_h:
                    color = original.get_at((source_x, source_y))
                    pygame.draw.rect(self.game.display, color, pygame.Rect(x, y, step, step))

    def render_cursor_distortion(self, radius: int = 45, slices: int = 12, max_offset: int = 8) -> None:
        mouse_x, mouse_y = self.get_internal_mouse_pos()
        original: pygame.Surface = self.game.display.copy()

        area = pygame.Rect(mouse_x - radius, mouse_y - radius, radius * 2, radius * 2)
        area = area.clip(self.game.display.get_rect())

        if area.width <= 0 or area.height <= 0:
            return

        sample: pygame.Surface = original.subsurface(area).copy()
        distortion = pygame.Surface((area.width, area.height), pygame.SRCALPHA)

        slice_h: int = max(1, sample.get_height() // slices)

        for i in range(slices):
            y: int = i * slice_h
            h: int = slice_h

            if y + h > sample.get_height():
                h = sample.get_height() - y

            offset: int = random.randint(-max_offset, max_offset)

            slice_rect = pygame.Rect(0, y, sample.get_width(), h)
            slice_img = sample.subsurface(slice_rect).copy()

            distortion.blit(slice_img, (offset, y))

        self.game.display.blit(distortion, area.topleft)

    def render_cursor_blur(self, radius: int = 62, blur_scale: int = 8) -> None:
        mouse_x, mouse_y = self.get_internal_mouse_pos()

        area = pygame.Rect(mouse_x - radius, mouse_y - radius, radius * 2, radius * 2)
        area = area.clip(self.game.display.get_rect())

        if area.width <= 0 or area.height <= 0:
            return

        patch: pygame.Surface = self.game.display.subsurface(area).copy()

        small_w: int = max(1, area.width // blur_scale)
        small_h: int = max(1, area.height // blur_scale)

        patch = pygame.transform.smoothscale(patch, (small_w, small_h))
        patch = pygame.transform.smoothscale(patch, (area.width, area.height))

        mask = pygame.Surface((area.width, area.height), pygame.SRCALPHA)

        local_mouse_x: int = mouse_x - area.x
        local_mouse_y: int = mouse_y - area.y

        pygame.draw.circle(mask, (255, 255, 255, 170), (local_mouse_x, local_mouse_y), radius)

        blurred = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
        blurred.blit(patch, (0, 0))
        blurred.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.game.display.blit(blurred, area.topleft)