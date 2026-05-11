import pygame, math, random, sys, json

from scripts.audio.sounds import SoundEffects
from scripts.core.cutscene_engine import CutsceneEngine
from scripts.core.utils import load_image
from scripts.entities.entities import Ghost, Player
from scripts.rendering.effects import Effects
from scripts.systems.heart_rate import HeartRateSystem
from scripts.ui.button import Button
from scripts.ui.dialogue_manager import DialogueManager
from scripts.ui.font import Font
from scripts.ui.thought_manager import ThoughtManager
from reloader import LiveReloader
from scripts.scenes.intro_scene import IntroScene
from scripts.scenes.first_scene import FirstScene
from scripts.scenes.route_choice_scene import RouteChoiceScene
from scripts.scenes.quiet_route_scene import QuietRouteScene
from scripts.scenes.busy_route_scene import BusyRouteScene


class Game:
    def __init__(self):
        pygame.init()

        """ setup """
        self.game_name = "Demo"
        self.screen_w, self.screen_h = 720, 560
        self.render_scale = 1
        self.internal_w = self.screen_w // self.render_scale
        self.internal_h = self.screen_h // self.render_scale
        self.fps = 60

        self.screen = self.create_screen()
        self.display = pygame.Surface((self.internal_w, self.internal_h))
        self.clock = pygame.time.Clock()
        self.scale_x = self.screen.get_width() / self.internal_w
        self.scale_y = self.screen.get_height() / self.internal_h

        self.asset_paths = {
            "resume_button": "assets/buttons/resume_button.png",
            "quit_button": "assets/buttons/quit_button.png",
            "start_button": "assets/buttons/start_button.png",
            "pause_button": "assets/buttons/pause_button.png",
            "audio_button": "assets/buttons/audio_button.png",
            "back_button": "assets/buttons/back_button.png",
            "heart_icon": "assets/fonts/heart_icon.png",
        }

        """ declareables """
        self.sfx = SoundEffects()
        self.audio_settings_path = "audio_config.json"
        self.load_audio_settings()
        self.effects = Effects(self)
        self.heart_rate = HeartRateSystem()
        self.dialogue_manager = DialogueManager(self)
        self.thought_manager = ThoughtManager()
        self.cutscene = CutsceneEngine(self)
        self.live = LiveReloader()

        """ fonts """
        self.menu_font = Font("assets/fonts/large_font_white.png", scale=1)
        self.hint_font = Font("assets/fonts/large_font_white.png", scale=1)
        self.heart_ui_font = pygame.font.SysFont("arial", 18)

        """ audio menu """
        self.audio_menu_scroll_y: int = 0
        self.audio_menu_scroll_dragging: bool = False
        self.audio_menu_scroll_drag_offset: int = 0

        """ player """
        self.player_w, self.player_h = 59, 111
        self.ground_h = 64
        self.player_x = 20
        self.player_y = self.screen_h - self.ground_h - self.player_h + 5
        self.player = Player(self, (self.player_x, self.player_y), (self.player_w, self.player_h))
        self.player_movement = [0, 0]
        self.player_speed = 120
        self.player_facing = "right"

        self.scroll = 0
        self.breathe_pressed = False

        """ scene objects """
        self.intro_scene_obj = IntroScene(self)
        self.first_scene_obj = FirstScene(self)
        self.route_choice_scene_obj = RouteChoiceScene(self)
        self.quiet_route_scene_obj = QuietRouteScene(self)
        self.busy_route_scene_obj = BusyRouteScene(self)

        """ heartbeat icon """
        self.heart_icon, *_ = load_image(self.asset_paths["heart_icon"])
        self.heart_icon = pygame.transform.scale(self.heart_icon, (16, 16))

        """ pause button """
        pause_img, *_ = load_image(self.asset_paths["pause_button"], convert_white=True)
        self.pause_button = Button((5, 5), pause_img, img_scale=1)

        """ menu buttons """
        self.pause_menu_buttons = self.create_centered_buttons(["resume_button", "audio_button", "quit_button"], scale=1)
        self.main_menu_buttons = self.create_centered_buttons(["start_button", "audio_button", "quit_button"], scale=1)

        """ ghosts """
        self.ghosts = []
        self.mechanic1_active = False
        self.mechanic1_used = False
        self.ghost_random_active = True
        self.next_ghost_time = pygame.time.get_ticks() + random.randint(6000, 14000)

        self.ghost_positive_dialogues = ["you are doing okay", "keep breathing", "one step at a time", "you can pause", "you made it this far", "it is okay to slow down"]
        self.ghost_neutral_dialogues = ["walk forward", "look around", "someone is nearby", "keep going", "wait", "listen", "check the door", "where are you going?"]
        self.ghost_negative_dialogues = ["they are watching", "you look strange", "do not mess this up", "why are you stopping?", "they know", "you are too slow", "everyone noticed", "you cannot trust this"]

        """ help hint """
        self.show_help = True
        self.help_duration = 15000
        self.help_fade_duration = 2000
        self.help_alpha = 255
        self.help_start_time = pygame.time.get_ticks()

    def fade_to_black(self, duration=1000):
        fade = pygame.Surface((self.internal_w, self.internal_h))
        fade.fill((0, 0, 0))

        start = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - start
            progress = min(1, elapsed / duration)

            alpha = int(progress * 255)
            fade.set_alpha(alpha)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

            self.display.fill((0, 0, 0))
            self.render_buttons("main")

            self.display.blit(fade, (0, 0))

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

            if progress >= 1:
                return
            
    def load_audio_settings(self):
        try:
            with open(self.audio_settings_path, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            return

        for name, volume in data.get("sfx", {}).items():
            if name in self.sfx.sounds: self.sfx.sounds[name].set_volume(volume)

        for name, volume in data.get("voices", {}).items():
            if name in self.sfx.voices: self.sfx.voices[name].set_volume(volume)

    def save_audio_settings(self):
        data = {
            "sfx": {name: sound.get_volume() for name, sound in self.sfx.sounds.items()},
            "voices": {name: sound.get_volume() for name, sound in self.sfx.voices.items()},
        }
        with open(self.audio_settings_path, "w") as file:
            json.dump(data, file, indent=4)
            
    def run(self):
        self.main_menu()

    def main_menu(self):
        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))
            self.render_buttons("main")

            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: self.quit_game()

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def pause_menu(self):
        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))
            result = self.render_buttons("pause")

            if result: return result

            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "resume"

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def audio_menu(self, return_to="main"):
        dragging = None
        back_img, *_ = load_image(self.asset_paths["back_button"], convert_white=True)
        back_button = Button((12, 12), back_img)

        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))

            if back_button.render(self.display): return return_to

            title = "Audio Settings"
            self.menu_font.render(self.display, title, (self.internal_w // 2 - self.menu_font.text_width(title) // 2, 20))

            content_top = 80
            content_bottom = self.internal_h - 20
            content_h = content_bottom - content_top
            total_h = 34 + len(self.sfx.sounds) * 38 + 20 + 34 + len(self.sfx.voices) * 38
            max_scroll = max(0, total_h - content_h)

            self.audio_menu_scroll_y = max(0, min(self.audio_menu_scroll_y, max_scroll))

            old_clip = self.display.get_clip()
            self.display.set_clip(pygame.Rect(0, content_top, self.internal_w - 18, content_h))

            y = content_top - self.audio_menu_scroll_y
            y = self.render_audio_section("SFX", self.sfx.sounds, y)
            y += 20
            self.render_audio_section("Voices", self.sfx.voices, y)

            self.display.set_clip(old_clip)
            self.render_audio_scrollbar(content_top, content_h, total_h, max_scroll)

            result, dragging = self.handle_input_audio_menu(return_to, dragging, content_top, content_h, total_h, max_scroll)
            if result: return result

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_input_audio_menu(self, return_to, dragging, content_top, content_h, total_h, max_scroll):
        for event in pygame.event.get():
            quit_type: bool = event.type == pygame.QUIT
            is_keydown: bool = event.type == pygame.KEYDOWN
            using_mwheel: bool = event.type == pygame.MOUSEWHEEL
            is_mbdown: bool = event.type == pygame.MOUSEBUTTONDOWN
            is_mbup: bool = event.type == pygame.MOUSEBUTTONUP
            is_mouse_moving: bool = event.type == pygame.MOUSEMOTION

            if quit_type: self.quit_game()
            if is_keydown and event.key == pygame.K_ESCAPE: return return_to, dragging

            if using_mwheel:
                self.audio_menu_scroll_y = max(0, min(max_scroll, self.audio_menu_scroll_y - event.y * 40))

            if is_mbdown and event.button == 1:
                mx, my = self.get_scaled_mouse_pos()
                scrollbar = self.get_audio_scrollbar_rect(content_top, content_h, total_h, max_scroll)

                if scrollbar and scrollbar.collidepoint(mx, my):
                    self.audio_menu_scroll_dragging = True
                    self.audio_menu_scroll_drag_offset = my - scrollbar.y
                else:
                    dragging = self.handle_audio_click(mx, my + self.audio_menu_scroll_y)

            if is_mbup and event.button == 1:
                dragging = None
                self.audio_menu_scroll_dragging = False

            if is_mouse_moving:
                mx, my = self.get_scaled_mouse_pos()
                if self.audio_menu_scroll_dragging:
                    thumb_h = max(30, int(content_h * content_h / total_h))
                    scrollable_track = max(1, content_h - thumb_h)
                    thumb_y = max(content_top, min(content_top + scrollable_track, my - self.audio_menu_scroll_drag_offset))
                    self.audio_menu_scroll_y = int((thumb_y - content_top) / scrollable_track * max_scroll)

                elif dragging:
                    self.set_audio_volume_from_mouse(dragging, mx)

        return None, dragging

    def get_audio_scrollbar_rect(self, content_top, content_h, total_h, max_scroll):
        if max_scroll <= 0: return None
        track_x = self.internal_w - 12
        thumb_h = max(30, int(content_h * content_h / total_h))
        scrollable_track = max(1, content_h - thumb_h)
        thumb_y = content_top + int((self.audio_menu_scroll_y / max_scroll) * scrollable_track)
        return pygame.Rect(track_x, thumb_y, 6, thumb_h)
    
    def render_audio_scrollbar(self, content_top, content_h, total_h, max_scroll):
        if max_scroll <= 0: return
        track_rect = pygame.Rect(self.internal_w - 12, content_top, 6, content_h)
        thumb_rect = self.get_audio_scrollbar_rect(content_top, content_h, total_h, max_scroll)
        pygame.draw.rect(self.display, (35, 35, 35), track_rect, border_radius=3)
        pygame.draw.rect(self.display, (180, 180, 180), thumb_rect, border_radius=3)
         
    def game_loop(self):
        while True:
            pygame.mouse.set_visible(False)
            dt = self.clock.get_time() / 1000
            self.display.fill((0, 0, 0))

            is_observed = self.is_player_observed()
            self.heart_rate.update(dt=dt, is_observed=is_observed, breathe_pressed=self.breathe_pressed)
            self.sfx.play_heartbeat(self.heart_rate.bpm)

            self.effects.render_glitch()
            self.render_floor()
            self.update_random_ghost_trigger()

            stress = self.heart_rate.stress_amount()
            movement = self.player_movement.copy()
            if stress > 0.55: movement[0] *= 1 - stress * 0.35
            if stress > 0.75 and random.random() < 0.04: movement[0] = 0

            self.player.update(movement, dt)
            self.heart_rate.render(self.display)
            self.render_heart_ui()
            self.render_player_status()

            for ghost in self.ghosts[:]:
                ghost.update()
                ghost.render(self.display, offset=(self.scroll, 0))
                ghost.render_dialogue(self.display, offset=(self.scroll, 0))
                if ghost.alpha <= 0: self.ghosts.remove(ghost)

            if not self.ghosts: self.mechanic1_active = False

            self.player.render(self.display, offset=(self.scroll, 0))

            if self.show_help: self.show_help_hints()
            if self.handle_pause_button(): return "menu"

            self.handle_input(dt)
            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_input(self, dt):
        key = pygame.key.get_pressed()
        was_breathing = self.breathe_pressed
        self.breathe_pressed = key[pygame.K_b]

        if was_breathing and not self.breathe_pressed and self.heart_rate.coping_worked: self.fade_ghosts()

        self.player_movement = [0, 0]

        if not self.breathe_pressed:
            if key[pygame.K_a]:
                self.player_movement[0] -= self.player_speed * dt
                self.player_facing = "left"
            if key[pygame.K_d]:
                self.player_movement[0] += self.player_speed * dt
                self.player_facing = "right"

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.quit_game()
            if event.type == pygame.KEYDOWN: self.handle_keydown(event)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE: 
            self.pause_menu()
            return
        elif event.key == pygame.K_1: self.activate_mechanic1()
        elif event.key == pygame.K_SPACE: self.player.jump()

    def activate_mechanic1(self):
        if self.mechanic1_used: return

        self.mechanic1_used = True

        if self.ghosts:
            if all(ghost.reached_target for ghost in self.ghosts):
                for ghost in self.ghosts: ghost.start_fade()
            return

        self.mechanic1_active = True
        self.ghosts = []
        used_points = []

        for idx in range(5):
            move_x, move_y = self.player.pos[0], self.player.pos[1]

            for _ in range(200):
                move_x = random.randint(35, self.internal_w - self.player_w - 35)
                move_y = random.randint(100, self.screen_h - self.ground_h - self.player_h - 20)
                if math.dist((move_x, move_y), (self.player.pos[0], self.player.pos[1])) < 120: continue
                if self.point_too_close((move_x, move_y), used_points, min_radius=80): continue
                break

            used_points.append((move_x, move_y))

            dialogue = [
                ("positive", random.choice(self.ghost_positive_dialogues)),
                ("neutral", random.choice(self.ghost_neutral_dialogues)),
                ("negative", random.choice(self.ghost_negative_dialogues)),
            ]

            random.shuffle(dialogue)

            self.ghosts.append(Ghost(self, name=f"Ghost {idx + 1}", pos=self.player.pos.copy(), size=(self.player_w, self.player_h), move_to=(move_x, move_y), color=(255, 255, 255), dialogue=dialogue))

    def update_random_ghost_trigger(self):
        if self.mechanic1_used or not self.ghost_random_active or self.ghosts: return

        now = pygame.time.get_ticks()

        if now >= self.next_ghost_time:
            self.activate_mechanic1()
            self.next_ghost_time = now + random.randint(10000, 22000)

    def fade_ghosts(self):
        for ghost in self.ghosts: ghost.start_fade()

    def point_too_close(self, point, existing_points, min_radius=30):
        px, py = point

        for ex, ey in existing_points:
            distance = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
            if distance < min_radius: return True
            if abs(py - ey) < min_radius: return True

        return False

    def is_player_observed(self):
        for ghost in self.ghosts:
            if abs(ghost.pos[0] - self.player.pos[0]) < 140: return True

        return False

    def render_floor(self):
        pygame.draw.rect(self.display, (25, 25, 30), pygame.Rect(0, self.screen_h - self.ground_h, self.internal_w, self.ground_h))
        pygame.draw.line(self.display, (70, 70, 80), (0, self.screen_h - self.ground_h), (self.internal_w, self.screen_h - self.ground_h), 2)

    def render_heart_ui(self):
        bpm = int(self.heart_rate.bpm)
        stress_units = getattr(self.heart_rate, "stress_units", 0)
        max_stress_units = getattr(self.heart_rate, "max_stress_units", 20)
        fill_ratio = max(0, min(1, stress_units / max_stress_units))
        pulse = (math.sin(self.heart_rate.pulse_timer) + 1) / 2
        icon_size = int(16 * (1 + pulse * 0.15))

        icon = pygame.transform.scale(self.heart_icon, (icon_size, icon_size)).copy()
        red_fill = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        fill_height = int(icon_size * fill_ratio)

        pygame.draw.rect(red_fill, (255, 0, 0, 180), pygame.Rect(0, icon_size - fill_height, icon_size, fill_height))

        mask = icon.copy()
        mask.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        red_fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        icon.blit(red_fill, (0, 0))

        text_surf = self.heart_ui_font.render(str(bpm), True, (255, 255, 255))
        total_width = icon.get_width() + 6 + text_surf.get_width()
        x = self.internal_w // 2 - total_width // 2
        y = 50

        self.display.blit(icon, (x, y))
        self.display.blit(text_surf, (x + icon.get_width() + 6, y - 1))

    def render_player_status(self):
        status = self.heart_rate.get_state()
        color = (230, 230, 230)

        if status == "irregular": color = (255, 220, 180)
        elif status == "something is coming": color = (255, 180, 120)
        elif status == "panic attack": color = (255, 100, 100)
        elif status == "psychosis": color = (255, 40, 40)

        text_surf = self.heart_ui_font.render(f"[{status}]", True, color)
        padding_x, padding_y = 10, 5
        box_w = text_surf.get_width() + padding_x * 2
        box_h = text_surf.get_height() + padding_y * 2
        x = self.internal_w // 2 - box_w // 2
        y = 10

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 170))

        self.display.blit(box, (x, y))
        self.display.blit(text_surf, (x + padding_x, y + padding_y))

    def show_help_hints(self):
        hints = ["Press A -- move left", "Press D -- move right", "Press SPACE -- jump", "Press B -- breathe", "Press 1 -- mechanic 1"]
        char_height = next(iter(self.hint_font.characters.values())).get_height()
        now = pygame.time.get_ticks()
        elapsed = now - self.help_start_time

        if elapsed > self.help_duration:
            fade_elapsed = elapsed - self.help_duration
            if fade_elapsed >= self.help_fade_duration:
                self.show_help = False
                return
            self.help_alpha = int(255 * (1 - fade_elapsed / self.help_fade_duration))

        for idx, hint in enumerate(hints):
            self.hint_font.render(self.display, hint, (15, 45 + idx * (char_height + 6)))

    def handle_pause_button(self):
        if not self.pause_button.render(self.display): return False
        self.pause_menu()
        return False

    def render_buttons(self, btype):
        buttons = self.main_menu_buttons if btype == "main" else self.pause_menu_buttons

        for name, button in buttons:
            if not button.render(self.display): continue

            if name == "start_button":
                self.fade_to_black(duration=1200)
                result = self.intro_scene_obj.run()

                if result == "continue":
                    result = self.first_scene_obj.run()

                if result == "route_choice":
                    result = self.route_choice_scene_obj.run()

                if result == "quiet_route":
                    result = self.quiet_route_scene_obj.run()

                elif result == "busy_route":
                    result = self.busy_route_scene_obj.run()

                if result == "continue":
                    self.game_loop()

                elif result == "menu":
                    return "menu"

        return None

    def render_audio_section(self, title, sounds, y):
        font = self.menu_font
        font.render(self.display, f"{title}:", (40, y))
        y += 34

        for name, sound in sounds.items():
            volume = sound.get_volume()

            font.render(self.display, str(name), (50, y))

            bar_rect = pygame.Rect(250, y + 6, 300, 12)
            fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.w * volume), bar_rect.h)
            test_rect = pygame.Rect(570, y - 2, 95, 28)

            pygame.draw.rect(self.display, (70, 70, 70), bar_rect, border_radius=6)
            pygame.draw.rect(self.display, (220, 220, 220), fill_rect, border_radius=6)
            pygame.draw.rect(self.display, (45, 45, 45), test_rect, border_radius=6)

            font.render(self.display, "Test", (test_rect.centerx - font.text_width("Test") // 2, test_rect.centery - 4))

            y += 38

        return y

    def handle_audio_click(self, mx, my):
        y = 114
        result = self.check_audio_section_click(mx, my, self.sfx.sounds, "sfx", y)
        if result: return result

        y += len(self.sfx.sounds) * 38 + 54
        return self.check_audio_section_click(mx, my, self.sfx.voices, "voices", y)

    def check_audio_section_click(self, mx, my, sounds, category, y):
        for name, sound in sounds.items():
            bar_rect = pygame.Rect(250, y + 6, 300, 12)
            test_rect = pygame.Rect(570, y - 2, 95, 28)

            if bar_rect.collidepoint(mx, my):
                self.set_audio_volume(category, name, mx, bar_rect)
                return (category, name, bar_rect)

            if test_rect.collidepoint(mx, my):
                sound.play()
                return None

            y += 38

        return None

    def set_audio_volume_from_mouse(self, dragging, mx):
        category, name, bar_rect = dragging
        self.set_audio_volume(category, name, mx, bar_rect)

    def set_audio_volume(self, category, name, mx, bar_rect):
        volume = max(0, min(1, (mx - bar_rect.x) / bar_rect.w))
        if category == "sfx": self.sfx.sounds[name].set_volume(volume)
        elif category == "voices": self.sfx.voices[name].set_volume(volume)
        self.save_audio_settings()

    def get_scaled_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale_x), int(my / self.scale_y)

    def create_centered_buttons(self, asset_keys, scale=1):
        center_x = self.screen_w // 2
        start_y = self.screen_h // 2
        gap = 20
        button_data = []
        total_height = 0

        for asset_key in asset_keys:
            img, w, h = load_image(self.asset_paths[asset_key])
            button_data.append((asset_key, img, w, h))
            total_height += h

        total_height += gap * (len(button_data) - 1)
        current_y = start_y - total_height // 2
        buttons = []

        for asset_key, img, w, h in button_data:
            button = Button((center_x - w // 2, current_y), img, scale)
            buttons.append((asset_key, button))
            current_y += h + gap

        return buttons

    def scale_display_to_screen(self):
        self.scale_x = self.screen.get_width() / self.internal_w
        self.scale_y = self.screen.get_height() / self.internal_h
        self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

    def create_screen(self):
        pygame.display.set_caption(self.game_name)
        return pygame.display.set_mode((self.screen_w, self.screen_h))

    def get_ticks(self):
        return pygame.time.get_ticks()

    def quit_game(self):
        pygame.quit()
        sys.exit()


def main():
    Game().run()


if __name__ == "__main__":
    main()