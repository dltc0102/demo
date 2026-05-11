import pygame, math, random, sys, json
from typing import Any

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


AudioDrag = tuple[str, str, pygame.Rect]
Point = tuple[float, float]
MenuTextButton = tuple[str, str, pygame.Rect]

class Game:
    def __init__(self) -> None:
        pygame.init()

        """ setup """
        self.game_name: str = "Demo"
        self.screen_w: int = 720
        self.screen_h: int = 560
        self.render_scale: int = 1
        self.internal_w: int = self.screen_w // self.render_scale
        self.internal_h: int = self.screen_h // self.render_scale
        self.fps: int = 60

        self.screen: pygame.Surface = self.create_screen()
        self.display: pygame.Surface = pygame.Surface((self.internal_w, self.internal_h))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.scale_x: float = self.screen.get_width() / self.internal_w
        self.scale_y: float = self.screen.get_height() / self.internal_h

        self.asset_paths: dict[str, str] = {
            "resume_button": "assets/buttons/resume_button.png",
            "quit_button": "assets/buttons/quit_button.png",
            "start_button": "assets/buttons/start_button.png",
            "pause_button": "assets/buttons/pause_button.png",
            "audio_button": "assets/buttons/audio_button.png",
            "back_button": "assets/buttons/back_button.png",
            "heart_icon": "assets/fonts/heart_icon.png",
            "main_menu_bg": "assets/backgrounds/kitchen_night_fridge_open.png",
        }

        """ declareables """
        self.sfx: SoundEffects = SoundEffects()
        self.audio_settings_path: str = "audio_config.json"
        self.load_audio_settings()

        self.effects: Effects = Effects(self)
        self.heart_rate: HeartRateSystem = HeartRateSystem()
        self.dialogue_manager: DialogueManager = DialogueManager(self)
        self.thought_manager: ThoughtManager = ThoughtManager()
        self.cutscene: CutsceneEngine = CutsceneEngine(self)
        self.live: LiveReloader = LiveReloader()

        """ fonts """
        self.menu_font: Font = Font("assets/fonts/large_font_white.png", scale=1)
        self.title_font: Font = Font("assets/fonts/large_font_white.png", scale=5)
        self.hint_font: Font = Font("assets/fonts/large_font_white.png", scale=1)
        self.button_font: Font = Font("assets/fonts/large_font_white.png", scale=2)
        self.heart_ui_font: pygame.font.Font = pygame.font.SysFont("arial", 18)

        """ menu background """
        self.main_menu_bg: pygame.Surface = self.load_menu_background(self.asset_paths["main_menu_bg"])

        """ audio menu """
        self.audio_menu_scroll_y: int = 0
        self.audio_menu_scroll_dragging: bool = False
        self.audio_menu_scroll_drag_offset: int = 0

        """ player """
        self.player_w: int = 59
        self.player_h: int = 111
        self.ground_h: int = 64
        self.player_x: int = 20
        self.player_y: int = self.screen_h - self.ground_h - self.player_h + 5
        self.player: Player = Player(self, (self.player_x, self.player_y), (self.player_w, self.player_h))
        self.player_movement: list[float] = [0, 0]
        self.player_speed: int = 120
        self.player_facing: str = "right"

        self.scroll: int = 0
        self.breathe_pressed: bool = False

        """ scene objects """
        self.intro_scene_obj: IntroScene = IntroScene(self)
        self.first_scene_obj: FirstScene = FirstScene(self)
        self.route_choice_scene_obj: RouteChoiceScene = RouteChoiceScene(self)
        self.quiet_route_scene_obj: QuietRouteScene = QuietRouteScene(self)
        self.busy_route_scene_obj: BusyRouteScene = BusyRouteScene(self)

        """ heartbeat icon """
        self.heart_icon, *_ = load_image(self.asset_paths["heart_icon"])
        self.heart_icon = pygame.transform.scale(self.heart_icon, (16, 16))

        """ pause button """
        pause_img, *_ = load_image(self.asset_paths["pause_button"], convert_white=True)
        self.pause_button: Button = Button((5, 5), pause_img, img_scale=1)

        """ menu buttons """
        pause_menu_center_y: int = self.internal_h // 2
        main_menu_center_y: int = int(self.internal_h * 0.68)

        self.pause_menu_text_buttons: list[MenuTextButton] = self.create_centered_text_buttons(
            [("resume", "RESUME"), ("audio", "AUDIO"), ("quit", "QUIT")],
            center_y=pause_menu_center_y,
            gap=24
        )

        self.main_menu_text_buttons: list[MenuTextButton] = self.create_centered_text_buttons(
            [("start", "START"), ("audio", "AUDIO"), ("quit", "QUIT")],
            center_y=main_menu_center_y,
            gap=24
        )

        self.menu_mouse_was_down: bool = False

        """ ghosts """
        self.ghosts: list[Ghost] = []
        self.mechanic1_active: bool = False
        self.mechanic1_used: bool = False
        self.ghost_random_active: bool = True
        self.next_ghost_time: int = pygame.time.get_ticks() + random.randint(6000, 14000)

        self.ghost_positive_dialogues: list[str] = ["you are doing okay", "keep breathing", "one step at a time", "you can pause", "you made it this far", "it is okay to slow down"]
        self.ghost_neutral_dialogues: list[str] = ["walk forward", "look around", "someone is nearby", "keep going", "wait", "listen", "check the door", "where are you going?"]
        self.ghost_negative_dialogues: list[str] = ["they are watching", "you look strange", "do not mess this up", "why are you stopping?", "they know", "you are too slow", "everyone noticed", "you cannot trust this"]

        """ help hint """
        self.show_help: bool = True
        self.help_duration: int = 15000
        self.help_fade_duration: int = 2000
        self.help_alpha: int = 255
        self.help_start_time: int = pygame.time.get_ticks()


        """ dev mode """
        self.dev_mode = True 
        self.dev_phase_hotkeys = {
            pygame.K_1: ("first_scene", "sequence"),
            pygame.K_2: ("first_scene", "get_milk"),
            pygame.K_3: ("first_scene", "go_to_bed"),
            pygame.K_4: ("first_scene", "wake_up"),
            pygame.K_5: ("route_choice_scene", "start"),
            pygame.K_6: ("route_choice_scene", "choice_maker"),
        }

    """ menus """
    def run(self) -> None:
        self.main_menu()

    def main_menu(self) -> None:
        while True:
            pygame.mouse.set_visible(True)
            self.render_start_menu()
            result: str | None = self.render_text_buttons(self.main_menu_text_buttons)

            if result == "start":
                menu_result: str | None = self.start_game_from_menu()
                if menu_result == "menu": continue
            elif result == "audio": self.audio_menu(return_to="main")
            elif result == "quit": self.quit_game()
            # result: str | None = self.render_buttons("main")
            # if result == "audio":
            #     self.audio_menu(return_to="main")
            # elif result == "quit":
            #     self.quit_game()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.quit_game()

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def start_game_from_menu(self) -> str | None:
        self.fade_to_black(duration=1200)
        result: str | None = self.intro_scene_obj.run()
        if result == "continue": result = self.first_scene_obj.run()
        if result == "route_choice": result = self.route_choice_scene_obj.run()
        if result == "quiet_route": result = self.quiet_route_scene_obj.run()
        elif result == "busy_route": result = self.busy_route_scene_obj.run()

        if result == "continue": return self.game_loop()
        if result == "menu": return "menu"
        return result

    def pause_menu(self) -> str:
        paused_frame: pygame.Surface = self.display.copy()
        while True:
            pygame.mouse.set_visible(True)
            self.render_pause_menu(paused_frame)
            result: str | None = self.render_text_buttons(self.pause_menu_text_buttons)
            if result == "resume": return "resume"
            if result == "audio": self.audio_menu(return_to="pause")
            if result == "quit": return "menu"

            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "resume"

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def audio_menu(self, return_to: str = "main") -> str:
        dragging: AudioDrag | None = None
        back_img, *_ = load_image(self.asset_paths["back_button"], convert_white=True)
        back_button: Button = Button((12, 12), back_img)

        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))

            if back_button.render(self.display): return return_to
            title: str = "Audio Settings"
            self.menu_font.render(self.display, title, (self.internal_w // 2 - self.menu_font.text_width(title) // 2, 20))

            content_top: int = 80
            content_bottom: int = self.internal_h - 20
            content_h: int = content_bottom - content_top
            total_h: int = 34 + len(self.sfx.sounds) * 38 + 20 + 34 + len(self.sfx.voices) * 38
            max_scroll: int = max(0, total_h - content_h)

            self.audio_menu_scroll_y = max(0, min(self.audio_menu_scroll_y, max_scroll))

            old_clip: pygame.Rect | None = self.display.get_clip()
            self.display.set_clip(pygame.Rect(0, content_top, self.internal_w - 18, content_h))

            y: int = content_top - self.audio_menu_scroll_y
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



    """ gameplay """
    def game_loop(self) -> str | None:
        while True:
            pygame.mouse.set_visible(False)

            dt: float = self.clock.get_time() / 1000
            self.display.fill((0, 0, 0))

            is_observed: bool = self.is_player_observed()
            self.heart_rate.update(dt=dt, is_observed=is_observed, breathe_pressed=self.breathe_pressed)
            self.sfx.play_heartbeat(self.heart_rate.bpm)

            self.effects.render_glitch()
            self.render_floor()
            self.update_random_ghost_trigger()

            stress: float = self.heart_rate.stress_amount()
            movement: list[float] = self.player_movement.copy()

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
            pause_result: str | None = self.handle_pause_button()
            if pause_result == "menu": return "menu"
            input_result: str | None = self.handle_input(dt)
            if input_result == "menu": return "menu"
            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_input(self, dt: float) -> str | None:
        key = pygame.key.get_pressed()
        was_breathing: bool = self.breathe_pressed
        self.breathe_pressed = key[pygame.K_b]

        if was_breathing and not self.breathe_pressed and self.heart_rate.coping_worked:
            self.fade_ghosts()

        self.player_movement = [0, 0]
        if not self.breathe_pressed:
            if key[pygame.K_a]:
                self.player_movement[0] -= self.player_speed * dt
                self.player_facing = "left"

            if key[pygame.K_d]:
                self.player_movement[0] += self.player_speed * dt
                self.player_facing = "right"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if self.handle_dev_shortcuts(event.key):
                    continue
                result: str | None = self.handle_keydown(event)
                if result: return result
        return None

    def handle_keydown(self, event: Any) -> str | None:
        if event.key == pygame.K_ESCAPE:
            pause_result: str = self.pause_menu()
            if pause_result == "menu": return "menu"
            return None

        if event.key == pygame.K_SPACE: self.player.jump()
        return None



    """ mechanics """
    def activate_mechanic1(self) -> None:
        if self.mechanic1_used:
            return

        self.mechanic1_used = True

        if self.ghosts:
            if all(ghost.reached_target for ghost in self.ghosts):
                for ghost in self.ghosts:
                    ghost.start_fade()

            return

        self.mechanic1_active = True
        self.ghosts = []
        used_points: list[Point] = []

        for idx in range(5):
            move_x: float = self.player.pos[0]
            move_y: float = self.player.pos[1]

            for _ in range(200):
                move_x = random.randint(35, self.internal_w - self.player_w - 35)
                move_y = random.randint(100, self.screen_h - self.ground_h - self.player_h - 20)

                if math.dist((move_x, move_y), (self.player.pos[0], self.player.pos[1])) < 120:
                    continue

                if self.point_too_close((move_x, move_y), used_points, min_radius=80):
                    continue

                break

            used_points.append((move_x, move_y))

            dialogue: list[tuple[str, str]] = [
                ("positive", random.choice(self.ghost_positive_dialogues)),
                ("neutral", random.choice(self.ghost_neutral_dialogues)),
                ("negative", random.choice(self.ghost_negative_dialogues)),
            ]

            random.shuffle(dialogue)

            ghost = Ghost(self, name=f"Ghost {idx + 1}", pos=self.player.pos.copy(), size=(self.player_w, self.player_h), move_to=(move_x, move_y), color=(255, 255, 255), dialogue=dialogue)
            self.ghosts.append(ghost)

    def update_random_ghost_trigger(self) -> None:
        if self.mechanic1_used or not self.ghost_random_active or self.ghosts:
            return

        now: int = pygame.time.get_ticks()

        if now >= self.next_ghost_time:
            self.activate_mechanic1()
            self.next_ghost_time = now + random.randint(10000, 22000)

    def fade_ghosts(self) -> None:
        for ghost in self.ghosts:
            ghost.start_fade()

    def point_too_close(self, point: Point, existing_points: list[Point], min_radius: int = 30) -> bool:
        px, py = point

        for ex, ey in existing_points:
            distance: float = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5

            if distance < min_radius:
                return True

            if abs(py - ey) < min_radius:
                return True

        return False

    def is_player_observed(self) -> bool:
        for ghost in self.ghosts:
            if abs(ghost.pos[0] - self.player.pos[0]) < 140:
                return True

        return False



    """ rendering """
    def render_pause_menu(self, paused_frame: pygame.Surface) -> None:
        blurred_bg: pygame.Surface = self.blur_surface(paused_frame, blur_scale=10)
        self.display.blit(blurred_bg, (0, 0))
        dark_overlay = pygame.Surface((self.internal_w, self.internal_h), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 115))
        self.display.blit(dark_overlay, (0, 0))
        self.effects.render_screen_warp(strength=2, wave_size=30, speed=0.006, step=2)
        self.effects.render_glitch(slices=10, max_offset=4, dark_alpha=0)
        self.effects.render_cursor_magnet(radius=70, strength=0.25)

    def render_start_menu(self) -> None:
        self.display.blit(self.main_menu_bg, (0, 0))

        self.effects.destabilize_backgrounds()
        self.effects.render_cursor_magnet(radius=100, strength=1)
        # self.effects.render_cursor_blur(radius=62, blur_scale=8)
        # self.effects.render_cursor_distortion(radius=48, slices=12, max_offset=6)

        title: str = "PEACE and QUIET"
        subtitle: str = "a demo meant to simulate how it would feel\nliving with schizophrenia"

        title_x: int = self.internal_w // 2 - self.title_font.text_width(title) // 2
        title_y: int = 80
        self.render_tinted_font(self.title_font, title, (title_x, title_y), (237, 220, 147))

        subtitle_lines: list[str] = subtitle.split("\n")
        for idx, subtitle in enumerate(subtitle_lines, 1):
            y_padding: int = 10
            subtitle_x: int = self.internal_w // 2 - self.menu_font.text_width(subtitle) // 2
            subtitle_y: int = title_y + 62 + (idx * y_padding)
            self.menu_font.render(self.display, subtitle, (subtitle_x, subtitle_y))

    def render_buttons(self, btype: str) -> str | None:
        buttons: list[tuple[str, Button]] = self.main_menu_buttons if btype == "main" else self.pause_menu_buttons
        for name, button in buttons:
            if not button.render(self.display): continue
            if name == "start_button":
                self.fade_to_black(duration=1200)
                result: str | None = self.intro_scene_obj.run()

                if result == "continue": result = self.first_scene_obj.run()
                if result == "route_choice": result = self.route_choice_scene_obj.run()

                if result == "quiet_route": result = self.quiet_route_scene_obj.run()

                elif result == "busy_route": result = self.busy_route_scene_obj.run()

                if result == "continue":
                    loop_result: str | None = self.game_loop()
                    if loop_result == "menu": return "menu"

                elif result == "menu": return "menu"
            elif name == "resume_button": return "resume"
            elif name == "audio_button": return "audio"
            elif name == "quit_button": return "quit"
        return None

    def draw_buttons_only(self, btype: str) -> None:
        buttons: list[tuple[str, Button]] = self.main_menu_buttons if btype == "main" else self.pause_menu_buttons
        for _, button in buttons:
            self.display.blit(button.image, button.rect)

    def render_floor(self) -> None:
        floor_rect = pygame.Rect(0, self.screen_h - self.ground_h, self.internal_w, self.ground_h)
        pygame.draw.rect(self.display, (25, 25, 30), floor_rect)
        pygame.draw.line(self.display, (70, 70, 80), (0, self.screen_h - self.ground_h), (self.internal_w, self.screen_h - self.ground_h), 2)

    def render_heart_ui(self) -> None:
        bpm: int = int(self.heart_rate.bpm)
        stress_units: int = getattr(self.heart_rate, "stress_units", 0)
        max_stress_units: int = getattr(self.heart_rate, "max_stress_units", 20)
        fill_ratio: float = max(0, min(1, stress_units / max_stress_units))
        pulse: float = (math.sin(self.heart_rate.pulse_timer) + 1) / 2
        icon_size: int = int(16 * (1 + pulse * 0.15))

        icon: pygame.Surface = pygame.transform.scale(self.heart_icon, (icon_size, icon_size)).copy()
        red_fill: pygame.Surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        fill_height: int = int(icon_size * fill_ratio)

        pygame.draw.rect(red_fill, (255, 0, 0, 180), pygame.Rect(0, icon_size - fill_height, icon_size, fill_height))

        mask: pygame.Surface = icon.copy()
        mask.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)

        red_fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        icon.blit(red_fill, (0, 0))

        text_surf: pygame.Surface = self.heart_ui_font.render(str(bpm), True, (255, 255, 255))
        total_width: int = icon.get_width() + 6 + text_surf.get_width()
        x: int = self.internal_w // 2 - total_width // 2
        y: int = 50

        self.display.blit(icon, (x, y))
        self.display.blit(text_surf, (x + icon.get_width() + 6, y - 1))

    def render_player_status(self) -> None:
        status: str = self.heart_rate.get_state()
        color: tuple[int, int, int] = (230, 230, 230)

        if status == "irregular": color = (255, 220, 180)
        elif status == "something is coming": color = (255, 180, 120)
        elif status == "panic attack": color = (255, 100, 100)
        elif status == "psychosis": color = (255, 40, 40)
        text_surf: pygame.Surface = self.heart_ui_font.render(f"[{status}]", True, color)

        padding_x: int = 10
        padding_y: int = 5
        box_w: int = text_surf.get_width() + padding_x * 2
        box_h: int = text_surf.get_height() + padding_y * 2
        x: int = self.internal_w // 2 - box_w // 2
        y: int = 10

        box: pygame.Surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 170))

        self.display.blit(box, (x, y))
        self.display.blit(text_surf, (x + padding_x, y + padding_y))

    def show_help_hints(self) -> None:
        hints: list[str] = [
            "Press A -- move left", 
            "Press D -- move right", 
            "Press SPACE -- jump", 
            "Press B -- breathe", 
            "Press 1 -- mechanic 1"
        ]
        char_height: int = next(iter(self.hint_font.characters.values())).get_height()
        now: int = pygame.time.get_ticks()
        elapsed: int = now - self.help_start_time
        if elapsed > self.help_duration:
            fade_elapsed: int = elapsed - self.help_duration

            if fade_elapsed >= self.help_fade_duration:
                self.show_help = False
                return

            self.help_alpha = int(255 * (1 - fade_elapsed / self.help_fade_duration))

        for idx, hint in enumerate(hints):
            self.hint_font.render(self.display, hint, (15, 45 + idx * (char_height + 6)))

    def render_audio_section(self, title: str, sounds: dict[str, Any], y: int) -> int:
        font: Font = self.menu_font
        font.render(self.display, f"{title}:", (40, y))
        y += 34

        for name, sound in sounds.items():
            volume: float = sound.get_volume()
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

    def render_audio_scrollbar(self, content_top: int, content_h: int, total_h: int, max_scroll: int) -> None:
        if max_scroll <= 0: return
        track_rect = pygame.Rect(self.internal_w - 12, content_top, 6, content_h)
        thumb_rect = self.get_audio_scrollbar_rect(content_top, content_h, total_h, max_scroll)
        pygame.draw.rect(self.display, (35, 35, 35), track_rect, border_radius=3)
        if thumb_rect:
            pygame.draw.rect(self.display, (180, 180, 180), thumb_rect, border_radius=3)

    def render_text_buttons(self, buttons: list[MenuTextButton], clickable: bool = True) -> str | None:
        mouse_pos: tuple[int, int] = self.get_scaled_mouse_pos()
        mouse_down: bool = pygame.mouse.get_pressed()[0]
        clicked_action: str | None = None

        for action, text, rect in buttons:
            hovered: bool = rect.collidepoint(mouse_pos)
            text_x: int = rect.centerx - self.button_font.text_width(text) // 2
            text_y: int = rect.centery - self.get_font_height(self.button_font) // 2

            if hovered:
                self.render_text_glow(text, self.button_font, (text_x, text_y), glow_radius=3, glow_alpha=115)
                self.button_font.render(self.display, text, (text_x + random.randint(-1, 1), text_y))
                self.effects.render_cursor_blur(radius=48, blur_scale=7)
                self.effects.render_cursor_distortion(radius=42, slices=10, max_offset=5)
                self.button_font.render(self.display, text, (text_x, text_y))

                if clickable and mouse_down and not self.menu_mouse_was_down:
                    clicked_action = action

            else:
                self.button_font.render(self.display, text, (text_x, text_y))

        if clickable: self.menu_mouse_was_down = mouse_down
        return clicked_action

    def render_text_glow(self, text: str, font: Font, pos: tuple[int, int], glow_radius: int = 2, glow_alpha: int = 90) -> None:
        text_w: int = font.text_width(text)
        text_h: int = self.get_font_height(font)
        padding: int = glow_radius + 4
        glow_surf = pygame.Surface((text_w + padding * 2, text_h + padding * 2), pygame.SRCALPHA)
        for offset_y in range(-glow_radius, glow_radius + 1):
            for offset_x in range(-glow_radius, glow_radius + 1):
                if offset_x == 0 and offset_y == 0: continue
                font.render(glow_surf, text, (padding + offset_x, padding + offset_y))
        glow_surf.set_alpha(glow_alpha)
        self.display.blit(glow_surf, (pos[0] - padding, pos[1] - padding))
        
    def render_tinted_font(self, font: Font, text: str, pos: tuple[int, int], color: tuple[int, int, int]) -> None:
        text_w = font.text_width(text)
        text_h = self.get_font_height(font)

        temp = pygame.Surface((text_w, text_h), pygame.SRCALPHA)
        font.render(temp, text, (0, 0))

        tint = pygame.Surface(temp.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))

        temp.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.display.blit(temp, pos)
        

    """ audio helpers """
    def load_audio_settings(self) -> None:
        try:
            with open(self.audio_settings_path, "r") as file:
                data: dict[str, Any] = json.load(file)

        except FileNotFoundError:
            return

        for name, volume in data.get("sfx", {}).items():
            if name in self.sfx.sounds:
                self.sfx.sounds[name].set_volume(volume)

        for name, volume in data.get("voices", {}).items():
            if name in self.sfx.voices:
                self.sfx.voices[name].set_volume(volume)

    def save_audio_settings(self) -> None:
        data: dict[str, dict[str, float]] = {
            "sfx": {name: sound.get_volume() for name, sound in self.sfx.sounds.items()},
            "voices": {name: sound.get_volume() for name, sound in self.sfx.voices.items()},
        }

        with open(self.audio_settings_path, "w") as file:
            json.dump(data, file, indent=4)

    def handle_input_audio_menu(self, return_to: str, dragging: AudioDrag | None, content_top: int, content_h: int, total_h: int, max_scroll: int) -> tuple[str | None, AudioDrag | None]:
        for event in pygame.event.get():
            quit_type: bool = event.type == pygame.QUIT
            is_keydown: bool = event.type == pygame.KEYDOWN
            using_mwheel: bool = event.type == pygame.MOUSEWHEEL
            is_mbdown: bool = event.type == pygame.MOUSEBUTTONDOWN
            is_mbup: bool = event.type == pygame.MOUSEBUTTONUP
            is_mouse_moving: bool = event.type == pygame.MOUSEMOTION

            if quit_type:
                self.quit_game()

            if is_keydown and event.key == pygame.K_ESCAPE:
                return return_to, dragging

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
                    thumb_h: int = max(30, int(content_h * content_h / total_h))
                    scrollable_track: int = max(1, content_h - thumb_h)
                    thumb_y: int = max(content_top, min(content_top + scrollable_track, my - self.audio_menu_scroll_drag_offset))
                    self.audio_menu_scroll_y = int((thumb_y - content_top) / scrollable_track * max_scroll)

                elif dragging:
                    self.set_audio_volume_from_mouse(dragging, mx)

        return None, dragging

    def handle_audio_click(self, mx: int, my: int) -> AudioDrag | None:
        y: int = 114
        result: AudioDrag | None = self.check_audio_section_click(mx, my, self.sfx.sounds, "sfx", y)
        if result: return result
        y += len(self.sfx.sounds) * 38 + 54
        return self.check_audio_section_click(mx, my, self.sfx.voices, "voices", y)

    def check_audio_section_click(self, mx: int, my: int, sounds: dict[str, Any], category: str, y: int) -> AudioDrag | None:
        for name, sound in sounds.items():
            bar_rect = pygame.Rect(250, y + 6, 300, 12)
            test_rect = pygame.Rect(570, y - 2, 95, 28)
            if bar_rect.collidepoint(mx, my):
                self.set_audio_volume(category, name, mx, bar_rect)
                return category, name, bar_rect
            if test_rect.collidepoint(mx, my):
                sound.play()
                return None
            y += 38
        return None

    def set_audio_volume_from_mouse(self, dragging: AudioDrag, mx: int) -> None:
        category, name, bar_rect = dragging
        self.set_audio_volume(category, name, mx, bar_rect)

    def set_audio_volume(self, category: str, name: str, mx: int, bar_rect: pygame.Rect) -> None:
        volume: float = max(0, min(1, (mx - bar_rect.x) / bar_rect.w))
        if category == "sfx":
            self.sfx.sounds[name].set_volume(volume)
        elif category == "voices":
            self.sfx.voices[name].set_volume(volume)
        self.save_audio_settings()



    """ helper functions """
    def blur_surface(self, surface: pygame.Surface, blur_scale: int = 8) -> pygame.Surface:
        width: int = surface.get_width()
        height: int = surface.get_height()

        small_w: int = max(1, width // blur_scale)
        small_h: int = max(1, height // blur_scale)
        blurred: pygame.Surface = pygame.transform.smoothscale(surface, (small_w, small_h))
        blurred = pygame.transform.smoothscale(blurred, (width, height))
        return blurred
    
    def load_menu_background(self, path: str) -> pygame.Surface:
        bg: pygame.Surface = pygame.image.load(path).convert()

        bg_w, bg_h = bg.get_size()
        target_w: int = self.internal_w
        target_h: int = self.internal_h

        scale: float = max(target_w / bg_w, target_h / bg_h)

        new_w: int = int(bg_w * scale)
        new_h: int = int(bg_h * scale)

        bg = pygame.transform.smoothscale(bg, (new_w, new_h))

        crop_x: int = (new_w - target_w) // 2
        crop_y: int = (new_h - target_h) // 2

        final_bg = pygame.Surface((target_w, target_h)).convert()
        final_bg.blit(bg, (-crop_x, -crop_y))

        return final_bg

    def create_centered_buttons(self, asset_keys: list[str], scale: int | float = 1) -> list[tuple[str, Button]]:
        center_x: int = self.screen_w // 2
        start_y: int = (self.screen_h // 3) * 2
        gap: int = 10

        button_data: list[tuple[str, pygame.Surface, int, int]] = []
        total_height: int = 0

        for asset_key in asset_keys:
            img, w, h = load_image(self.asset_paths[asset_key])
            button_data.append((asset_key, img, w, h))
            total_height += h

        total_height += gap * (len(button_data) - 1)

        current_y: int = start_y - total_height // 2
        buttons: list[tuple[str, Button]] = []

        for asset_key, img, w, h in button_data:
            button = Button((center_x - w // 2, current_y), img, scale)
            buttons.append((asset_key, button))
            current_y += h + gap

        return buttons

    def get_audio_scrollbar_rect(self, content_top: int, content_h: int, total_h: int, max_scroll: int) -> pygame.Rect | None:
        if max_scroll <= 0:
            return None

        track_x: int = self.internal_w - 12
        thumb_h: int = max(30, int(content_h * content_h / total_h))
        scrollable_track: int = max(1, content_h - thumb_h)
        thumb_y: int = content_top + int((self.audio_menu_scroll_y / max_scroll) * scrollable_track)

        return pygame.Rect(track_x, thumb_y, 6, thumb_h)

    def get_scaled_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.scale_x), int(my / self.scale_y)

    def handle_pause_button(self) -> str | None:
        if not self.pause_button.render(self.display): return None
        pause_result: str = self.pause_menu()
        if pause_result == "menu": return "menu"
        return None

    def fade_to_black(self, duration: int = 1000) -> None:
        fade: pygame.Surface = pygame.Surface((self.internal_w, self.internal_h))
        fade.fill((0, 0, 0))
        start: int = pygame.time.get_ticks()
        while True:
            elapsed: int = pygame.time.get_ticks() - start
            progress: float = min(1, elapsed / duration)
            alpha: int = int(progress * 255)
            fade.set_alpha(alpha)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()

            self.render_start_menu()
            self.render_text_buttons(self.main_menu_text_buttons, clickable=False)
            # self.draw_buttons_only("main")
            self.display.blit(fade, (0, 0))

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)
            if progress >= 1: return

    def scale_display_to_screen(self) -> None:
        self.scale_x = self.screen.get_width() / self.internal_w
        self.scale_y = self.screen.get_height() / self.internal_h
        self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

    def create_screen(self) -> pygame.Surface:
        pygame.display.set_caption(self.game_name)
        return pygame.display.set_mode((self.screen_w, self.screen_h))

    def get_ticks(self) -> int:
        return pygame.time.get_ticks()

    def create_centered_text_buttons(self, items: list[tuple[str, str]], center_y: int, gap: int = 24, padding_x: int = 24, padding_y: int = 12) -> list[MenuTextButton]:
        button_h: int = self.get_font_height(self.button_font) + padding_y * 2
        total_h: int = button_h * len(items) + gap * (len(items) - 1)
        current_y: int = center_y - total_h // 2
        buttons: list[MenuTextButton] = []
        for action, text in items:
            button_w: int = self.button_font.text_width(text) + padding_x * 2
            rect = pygame.Rect(self.internal_w // 2 - button_w // 2, current_y, button_w, button_h)
            buttons.append((action, text, rect))
            current_y += button_h + gap

        return buttons

    def get_font_height(self, font: Font) -> int:
        return max(character.get_height() for character in font.characters.values())


    """ dev """
    def handle_dev_shortcuts(self, key):
        if not self.dev_mode: return False
        if key not in self.dev_phase_hotkeys: return False
        scene_name, phase_name = self.dev_phase_hotkeys[key]
        self.start_dev_phase(scene_name, phase_name)
        return True

    def start_dev_phase(self, scene_name, phase_name):
        print(f"[DEV] Starting {scene_name}: {phase_name}")
        self.clear_scene_state()
        if scene_name == "first_scene":
            self.start_first_scene_phase(phase_name)
        elif scene_name == "route_choice_scene":
            self.start_route_choice_phase(phase_name)

    def clear_scene_state(self):
        if hasattr(self.dialogue_manager, "clear"): self.dialogue_manager.clear()
        if hasattr(self.thought_manager, "clear"): self.thought_manager.clear()
        self.cutscene.stop()
        if hasattr(self, "ghosts"): self.ghosts.clear()

    def handle_dev_keys(self, event) -> bool:
        if not self.dev_mode: return False
        if event.type != pygame.KEYDOWN: return False
        return self.handle_dev_shortcuts(event.key)

    def start_first_scene_phase(self, phase_name):
        self.first_scene_obj.reset()
        self.first_scene_obj.started = True
        if phase_name == "sequence":
            self.first_scene_obj.started = False
        elif phase_name == "get_milk":
            self.first_scene_obj.flags["door_unlocked"] = True
            self.first_scene_obj.flags["fridge_opened"] = True
            self.first_scene_obj.flags["note_unlocked"] = True
            self.first_scene_obj.in_kitchen = True
            self.cutscene.start(self.first_scene_obj.get_milk())
        elif phase_name == "go_to_bed":
            self.first_scene_obj.flags["holding_milk"] = True
            self.first_scene_obj.flags["read_sticky_note"] = True
            self.first_scene_obj.flags["can_sleep"] = True
            self.cutscene.start(self.first_scene_obj.go_to_bed())
        elif phase_name == "wake_up":
            self.first_scene_obj.flags["is_next_day"] = True
            self.cutscene.start(self.first_scene_obj.wake_up())

    def start_route_choice_phase(self, phase_name):
        self.current_scene = "route_choice_scene"
        if phase_name == "start":
            self.route_choice_scene_obj.reset()
        elif phase_name == "choice_maker":
            self.route_choice_scene_obj.reset()
         
    """ other """
    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()