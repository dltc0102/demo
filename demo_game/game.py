import pygame, math, random, sys, json
from typing import Any
from pathlib import Path

from paths import asset
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
from scripts.scenes.intro_scene import IntroScene
from scripts.scenes.first_scene import FirstScene
# from scripts.scenes.route_choice_scene import RouteChoiceScene
# from scripts.scenes.quiet_route_scene import QuietRouteScene
# from scripts.scenes.busy_route_scene import BusyRouteScene
from scripts.systems.ghost_manager import GhostManager
from scripts.scenes.tutorial_scene import TutorialScene
from scripts.scenes.end_scene import EndScene


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
            "pause_button": asset("assets/buttons/pause_button.png"),
            "heart_icon": asset("assets/fonts/heart_icon.png"),
            "main_menu_bg": asset("assets/backgrounds/kitchen_night_fridge_open.png"),
        }

        """ declareables """
        self.sfx: SoundEffects = SoundEffects()
        config_dir = Path.home() / ".daniels-demo-game"
        config_dir.mkdir(exist_ok=True)
        self.audio_settings_path: str = str(config_dir / "audio_config.json")

        """ master volume + base volume state (must exist before load_audio_settings) """
        self.master_volume: float       = 1.0
        self.voices_master: float       = 1.0
        self.heartbeat_master: float    = 1.0
        self.sfx_master: float          = 1.0
        self.base_sfx_volumes: dict[str, float]   = {}
        self.base_voice_volumes: dict[str, float] = {}

        self.load_audio_settings()
        self.apply_master_volumes()

        self.effects: Effects = Effects(self)
        self.heart_rate: HeartRateSystem = HeartRateSystem()
        self.dialogue_manager: DialogueManager = DialogueManager(self)
        self.thought_manager: ThoughtManager = ThoughtManager()
        self.ghost_manager: GhostManager = GhostManager(self)
        self.cutscene: CutsceneEngine = CutsceneEngine(self)

        """ fonts """
        self.menu_font: Font = Font(asset("assets/fonts/large_font_white.png"), scale=1)
        self.title_font: Font = Font(asset("assets/fonts/large_font_white.png"), scale=5)
        self.hint_font: Font = Font(asset("assets/fonts/large_font_white.png"), scale=1)
        self.button_font: Font = Font(asset("assets/fonts/large_font_white.png"), scale=2)
        self.heart_ui_font: pygame.font.Font = pygame.font.Font(
            asset("assets/fonts/Minecraftia-Regular.ttf"), 18
        )
        self.grounding_prompt_font: pygame.font.Font = pygame.font.Font(
            asset("assets/fonts/Minecraftia-Regular.ttf"), 14
        )

        """ menu background """
        self.main_menu_bg: pygame.Surface = self.load_menu_background(self.asset_paths["main_menu_bg"])

        """ audio menu """
        self.audio_menu_scroll_y: int = 0
        self.audio_menu_scroll_dragging: bool = False
        self.audio_menu_scroll_drag_offset: int = 0

        """ player """
        self.player_w: int = 59
        self.player_h: int = 111
        self.ground_h: int = 55
        self.player_x: int = 20
        self.player_y: int = self.screen_h - self.ground_h - self.player_h + 5
        self.player: Player = Player(self, (self.player_x, self.player_y), (self.player_w, self.player_h))
        self.player_movement: list[float] = [0, 0]
        self.player_speed: int = 120
        self.player_facing: str = "right"

        self.scroll: int = 0
        self.breathe_pressed: bool = False
        self._heartbeat_target_volume: float = 0.20

        """ scene objects """
        self.intro_scene_obj: IntroScene = IntroScene(self)
        self.tutorial_scene_obj: TutorialScene = TutorialScene(self)
        self.first_scene_obj: FirstScene = FirstScene(self)
        # self.route_choice_scene_obj: RouteChoiceScene = RouteChoiceScene(self)
        # self.quiet_route_scene_obj: QuietRouteScene = QuietRouteScene(self)
        # self.busy_route_scene_obj: BusyRouteScene = BusyRouteScene(self)
        self.end_scene_obj: EndScene = EndScene(self)

        """ heartbeat icon """
        self.heart_icon, *_ = load_image(self.asset_paths["heart_icon"])
        self.heart_icon = pygame.transform.scale(self.heart_icon, (16, 16))

        """ pause button """
        pause_img, *_ = load_image(self.asset_paths["pause_button"], convert_white=True)
        self.pause_button: Button = Button((5, 5), pause_img, img_scale=1)

        """ menu buttons """
        pause_menu_center_y: int = self.internal_h // 2
        main_menu_center_y: int = int(self.internal_h * 0.68)
        self.menu_mouse_was_down: bool = False
        self.pause_menu_text_buttons: list[MenuTextButton] = self.create_centered_text_buttons(
            [("resume", "RESUME"), ("options", "OPTIONS"), ("quit", "QUIT")],
            center_y=pause_menu_center_y,
            gap=24
        )

        self.main_menu_text_buttons: list[MenuTextButton] = self.create_centered_text_buttons(
            [("start", "START"), ("options", "OPTIONS"), ("quit", "QUIT")],
            center_y=main_menu_center_y,
            gap=24
        )
        self.credits_text_button: MenuTextButton = self.create_bottom_right_text_button("credits", "CREDITS", padding=10)
        self.credits_font: pygame.font.Font = self.load_unicode_font(18)
        self.credits_small_font: pygame.font.Font = self.load_unicode_font(15)
        self.credits_items = self.load_credits()
        self.credits_scroll_y = 0


        """ ghosts """
        self.ghosts: list[Ghost] = []
        self.mechanic1_active: bool = False
        self.mechanic1_used: bool = False
        self.ghost_random_active: bool = False
        self.next_ghost_time: int = pygame.time.get_ticks() + random.randint(6000, 14000)

        self.next_ghost_stress_time: int = 0
        self.ghost_stress_interval: int = 850

        self.ghost_positive_dialogues: list[str] = [
            "you are doing okay", "keep breathing", "one step at a time", "you can pause",
            "you made it this far", "it is okay to slow down", "you can check what is real",
            "feet on the floor", "name five things you can see", "this feeling can pass",
        ]
        self.ghost_neutral_dialogues: list[str] = [
            "walk forward", "look around", "someone is nearby", "keep going", "wait", "listen",
            "check the door", "where are you going?", "did you forget something?", "turn around",
            "not that way", "was that always there?", "maybe it moved", "maybe it did not",
        ]
        self.ghost_negative_dialogues: list[str] = [
            "they are watching", "you look strange", "do not mess this up", "why are you stopping?",
            "they know", "you are too slow", "everyone noticed", "you cannot trust this",
            "they can hear you", "you said that wrong", "they are laughing", "do not drink that",
            "your hands look wrong", "something is behind you", "you forgot again", "you are not safe",
            "they put something in it", "the room is listening", "you are making it worse",
        ]

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
        self.sfx.stop_all_gameplay_audio()
        while True:
            pygame.mouse.set_visible(True)
            self.render_start_menu()
            result: str | None = self.render_text_buttons(self.main_menu_text_buttons + [self.credits_text_button])
            if result == "start":
                menu_result: str | None = self.start_game_from_menu()
                if menu_result == "menu": continue
            elif result == "options": self.options_menu(return_to="main")
            elif result == "credits": self.credits_menu()
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
        if result == "continue": result = self.tutorial_scene_obj.run()
        if result == "continue": result = self.first_scene_obj.run()
        if result == "end": result = self.end_scene_obj.run()

        # if result == "route_choice": result = self.route_choice_scene_obj.run()
        # if result == "quiet_route": result = self.quiet_route_scene_obj.run()
        # elif result == "busy_route": result = self.busy_route_scene_obj.run()

        if result == "continue": return self.game_loop()
        if result == "menu": return "menu"
        return result

    def pause_menu(self) -> str:
        paused_frame: pygame.Surface = self.display.copy()
        self.sfx.stop_all_gameplay_audio()
        while True:
            pygame.mouse.set_visible(True)
            self.render_pause_menu(paused_frame)
            result: str | None = self.render_text_buttons(self.pause_menu_text_buttons)
            if result == "resume":
                self.sfx.resume_gameplay_audio()
                return "resume"
            if result == "options": self.options_menu(return_to="pause")
            if result == "quit":
                return "menu"

            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.sfx.resume_gameplay_audio()
                    return "resume"

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def audio_menu(self, return_to: str = "main") -> str:
        dragging: AudioDrag | None = None
        back_rect = pygame.Rect(10, 10, self.button_font.text_width("BACK") + 24, self.get_font_height(self.button_font) + 16)
        back_button: MenuTextButton = ("back", "BACK", back_rect)

        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))

            result: str | None = self.render_text_buttons([back_button])
            if result == "back":
                self.save_audio_settings()
                return return_to

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

            input_result, dragging = self.handle_input_audio_menu(return_to, dragging, content_top, content_h, total_h, max_scroll)
            if input_result: return input_result

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def options_menu(self, return_to: str = "main") -> str:
        back_rect = pygame.Rect(10, 10, self.button_font.text_width("BACK") + 24, self.get_font_height(self.button_font) + 16)
        back_button: MenuTextButton = ("back", "BACK", back_rect)

        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))

            title: str = "Options"
            self.menu_font.render(self.display, title, (self.internal_w // 2 - self.menu_font.text_width(title) // 2, 20))

            dev_label: str = f"DEV MODE: {'ON' if self.dev_mode else 'OFF'}"
            buttons: list[MenuTextButton] = self.create_centered_text_buttons(
                [("audio", "AUDIO"), ("dev", dev_label)],
                center_y=self.internal_h // 2,
                gap=24,
            )

            result: str | None = self.render_text_buttons([back_button] + buttons)

            if result == "back":
                self.save_audio_settings()
                return return_to
            if result == "audio":
                if self.dev_mode:
                    self.audio_menu(return_to="options")
                else:
                    self.simple_audio_menu(return_to="options")
            if result == "dev":
                self.dev_mode = not self.dev_mode
                self.save_audio_settings()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.save_audio_settings()
                    return return_to

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def simple_audio_menu(self, return_to: str = "options") -> str:
        back_rect = pygame.Rect(10, 10, self.button_font.text_width("BACK") + 24, self.get_font_height(self.button_font) + 16)
        back_button: MenuTextButton = ("back", "BACK", back_rect)

        sliders: list[tuple[str, str, str]] = [
            ("master",    "Master",    "master_volume"),
            ("voices",    "Voices",    "voices_master"),
            ("heartbeat", "Heartbeat", "heartbeat_master"),
            ("sfx",       "SFX",       "sfx_master"),
        ]

        dragging_key: str | None = None

        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))

            title: str = "Audio"
            self.menu_font.render(self.display, title, (self.internal_w // 2 - self.menu_font.text_width(title) // 2, 20))

            result: str | None = self.render_text_buttons([back_button])
            if result == "back":
                self.save_audio_settings()
                return return_to

            font: Font = self.menu_font
            bar_w: int = 320
            bar_h: int = 14
            bar_x: int = self.internal_w // 2 - bar_w // 2
            row_h: int = 50
            y: int = 110
            slider_rects: dict[str, pygame.Rect] = {}

            for key, label, attr in sliders:
                value: float = getattr(self, attr)
                font.render(self.display, label, (bar_x, y))
                bar_rect = pygame.Rect(bar_x, y + 22, bar_w, bar_h)
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.w * value), bar_rect.h)
                pygame.draw.rect(self.display, (70, 70, 70), bar_rect, border_radius=6)
                pygame.draw.rect(self.display, (220, 220, 220), fill_rect, border_radius=6)
                pct: str = f"{int(value * 100)}%"
                font.render(self.display, pct, (bar_rect.right + 12, y + 18))
                slider_rects[key] = bar_rect
                y += row_h

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.save_audio_settings()
                    return return_to
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = self.get_scaled_mouse_pos()
                    for key, rect in slider_rects.items():
                        if rect.collidepoint(mx, my):
                            dragging_key = key
                            self._set_master_from_mouse(sliders, key, mx, rect)
                            break
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if dragging_key is not None:
                        self.save_audio_settings()
                    dragging_key = None
                if event.type == pygame.MOUSEMOTION and dragging_key is not None:
                    mx, _ = self.get_scaled_mouse_pos()
                    self._set_master_from_mouse(sliders, dragging_key, mx, slider_rects[dragging_key])

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def _set_master_from_mouse(self, sliders: list[tuple[str, str, str]], key: str, mx: int, bar_rect: pygame.Rect) -> None:
        attr: str = next(a for k, _, a in sliders if k == key)
        value: float = max(0.0, min(1.0, (mx - bar_rect.x) / bar_rect.w))
        setattr(self, attr, value)
        self.apply_master_volumes()

    def credits_menu(self) -> str:
        back_rect = pygame.Rect(10, 10, self.button_font.text_width("BACK") + 24, self.get_font_height(self.button_font) + 16)
        back_button: MenuTextButton = ("back", "BACK", back_rect)
        while True:
            pygame.mouse.set_visible(True)
            self.display.blit(self.main_menu_bg, (0, 0))
            dark = pygame.Surface((self.internal_w, self.internal_h), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 185))
            self.display.blit(dark, (0, 0))
            title = "CREDITS"
            title_surf = self.credits_font.render(title, True, (237, 220, 147))
            self.display.blit(title_surf, (self.internal_w // 2 - title_surf.get_width() // 2, 55))
            result: str | None = self.render_text_buttons([back_button])
            if result == "back": return "main"
            content_top = 100
            content_bottom = self.internal_h - 20
            content_h = content_bottom - content_top
            old_clip = self.display.get_clip()
            self.display.set_clip(pygame.Rect(0, content_top, self.internal_w, content_h))
            x = 70
            y = content_top - self.credits_scroll_y
            for section_name, items in self.credits_items.items():
                y = self.render_credits_section(section_name, items, x, y)

            self.display.set_clip(old_clip)
            total_h = max(0, y - content_top + self.credits_scroll_y)
            max_scroll = max(0, total_h - content_h)
            self.credits_scroll_y = max(0, min(self.credits_scroll_y, max_scroll))
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "main"
                if event.type == pygame.MOUSEWHEEL: self.credits_scroll_y = max(0, min(max_scroll, self.credits_scroll_y - event.y * 40))

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
            current_bpm = self.heart_rate.displayed_bpm
            self.sfx.set_heartbeat_bpm(current_bpm, volume=self._bpm_to_volume(current_bpm))
            self.sfx.play_heartbeat(current_bpm)

            self.effects.render_glitch()
            self.render_floor()
            self.update_random_ghost_trigger()
            self.update_ghost_stress(dt)

            stress: float = self.heart_rate.stress_amount()
            movement: list[float] = self.player_movement.copy()

            if stress > 0.55: movement[0] *= 1 - stress * 0.35
            if stress > 0.75 and random.random() < 0.04: movement[0] = 0
            self.player.update(movement, dt)
            self.heart_rate.render(self.display)
            self.render_heart_ui()
            self.render_player_status()
            self.render_breathing_prompt()

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
                if event.key == pygame.K_b:
                    self.heart_rate.tap_grounding()
                    continue
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
        if not self.ghost_random_active:
            self.ghosts.clear()
            self.mechanic1_active = False
            return

        if self.ghosts:
            if all(getattr(ghost, "reached_target", False) for ghost in self.ghosts):
                for ghost in self.ghosts:
                    ghost.start_fade()
            return

        self.mechanic1_used = True
        self.mechanic1_active = True
        self.ghosts = []
        used_points: list[Point] = []
        ghost_count: int = random.randint(4, 7)

        for idx in range(ghost_count):
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

            dialogue: list[tuple[str, str]] = []
            for _ in range(random.randint(3, 6)):
                kind = random.choices(["positive", "neutral", "negative"], weights=[1, 3, 4], k=1)[0]
                if kind == "positive":
                    line = random.choice(self.ghost_positive_dialogues)
                elif kind == "neutral":
                    line = random.choice(self.ghost_neutral_dialogues)
                else:
                    line = random.choice(self.ghost_negative_dialogues)
                dialogue.append((kind, line))

            ghost = Ghost(
                self,
                name=f"Fuzz {idx + 1}",
                pos=self.player.pos.copy(),
                size=(self.player_w, self.player_h),
                move_to=(move_x, move_y),
                color=(8, 8, 10),
                dialogue=dialogue
            )
            self.ghosts.append(ghost)

    def update_random_ghost_trigger(self) -> None:
        if not self.ghost_random_active or self.ghosts:
            return

        now: int = pygame.time.get_ticks()

        if now >= self.next_ghost_time:
            self.activate_mechanic1()
            self.next_ghost_time = now + random.randint(10000, 22000)

    def fade_ghosts(self) -> None:
        for ghost in self.ghosts:
            ghost.start_fade()

    def update_ghost_stress(self, dt: float) -> None:
        if not self.ghosts:
            return

        now: int = pygame.time.get_ticks()
        if now < self.next_ghost_stress_time:
            return

        negative_pressure: int = sum(1 for ghost in self.ghosts if self.ghost_has_negative_dialogue(ghost))
        amount: float = min(3.0, 0.45 + negative_pressure * 0.22)
        self.heart_rate.add_stress_unit(amount)

        if self.heart_rate.stress_units >= self.heart_rate.max_stress_units * 0.7:
            self.heart_rate.start_panic_attack(coping_worked=random.random() < 0.65)

        self.next_ghost_stress_time = now + self.ghost_stress_interval

    def ghost_has_negative_dialogue(self, ghost: Any) -> bool:
        possible_dialogues = getattr(ghost, "dialogue", None) or getattr(ghost, "dialogues", None) or []

        for item in possible_dialogues:
            if isinstance(item, tuple) and len(item) >= 2 and item[0] == "negative":
                return True

        return False

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

    def render_floor(self) -> None:
        floor_rect = pygame.Rect(0, self.screen_h - self.ground_h, self.internal_w, self.ground_h)
        pygame.draw.rect(self.display, (25, 25, 30), floor_rect)
        pygame.draw.line(self.display, (70, 70, 80), (0, self.screen_h - self.ground_h), (self.internal_w, self.screen_h - self.ground_h), 2)

    def render_sfx_heartbeat_ui(self) -> None:
        self.render_heart_ui()

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
        if self.heart_rate.should_show_grounding(): return
        status: str = self.heart_rate.get_state()
        color: tuple[int, int, int] = (230, 230, 230)

        if status == "irregular": color = (255, 220, 180)
        elif status == "something is coming": color = (255, 180, 120)
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

    def render_breathing_prompt(self) -> None:
        self.render_grounding_prompt()

    def render_grounding_prompt(self) -> None:
        if not self.heart_rate.should_show_grounding(): return
        text = self.heart_rate.coping_state_text()
        if not text: return

        in_recovery = self.heart_rate.grounding_recovery_active or self.heart_rate.grounding_progress >= 100
        font = self.grounding_prompt_font
        lines = text.split("\n")

        shadow_color = (0, 0, 0)
        if in_recovery:
            text_color = (180, 230, 200)
        elif self.heart_rate.get_state() == "psychosis":
            text_color = (255, 85, 85)
        else:
            text_color = (255, 220, 180)

        line_surfs = [font.render(line, True, text_color) for line in lines]
        shadow_surfs = [font.render(line, True, shadow_color) for line in lines]

        y = 82
        line_h = font.get_linesize()
        text_y = y
        for surf, shadow in zip(line_surfs, shadow_surfs):
            x = self.internal_w // 2 - surf.get_width() // 2
            self.display.blit(shadow, (x + 1, text_y + 1))
            self.display.blit(surf, (x, text_y))
            text_y += line_h

        if in_recovery: return

        progress = max(0.0, min(1.0, self.heart_rate.grounding_progress / 100.0))
        cx = self.internal_w // 2
        cy = text_y + 22
        radius = 18

        pygame.draw.circle(self.display, (80, 80, 80), (cx, cy), radius, 3)
        if progress > 0:
            arc_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
            start_angle = math.radians(-90)
            end_angle = math.radians(-90 + 360 * progress)
            pygame.draw.arc(self.display, (255, 70, 70), arc_rect, start_angle, end_angle, 4)

        percent_surf = font.render(f"{int(progress * 100)}%", True, (235, 235, 235))
        percent_shadow = font.render(f"{int(progress * 100)}%", True, shadow_color)
        self.display.blit(percent_shadow, (cx - percent_surf.get_width() // 2 + 1, cy - percent_surf.get_height() // 2 + 1))
        self.display.blit(percent_surf, (cx - percent_surf.get_width() // 2, cy - percent_surf.get_height() // 2))
        
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
            if title == "SFX":
                volume: float = self.base_sfx_volumes.get(name, sound.get_volume())
            else:
                volume: float = self.base_voice_volumes.get(name, sound.get_volume())
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
                    self.sfx.play_key("button_click", volume=0.5)
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
        
    def create_bottom_right_text_button(self, action: str, text: str, padding: int = 10, padding_x: int = 16, padding_y: int = 8) -> MenuTextButton:
        button_w = self.button_font.text_width(text) + padding_x * 2
        button_h = self.get_font_height(self.button_font) + padding_y * 2
        rect = pygame.Rect(0, 0, button_w, button_h)
        rect.bottomright = (self.internal_w - padding, self.internal_h - padding)
        return action, text, rect
    
    def load_unicode_font(self, size: int) -> pygame.font.Font:
        font_paths = [
            asset("assets/fonts/NotoSansCJK-Regular.ttc"),
            asset("assets/fonts/NotoSansSC-Regular.ttf"),
        ]

        for path in font_paths:
            try: return pygame.font.Font(path, size)
            except Exception: pass

        return ValueError("Could not load any unicode font")

    def render_unicode_text(self, font: pygame.font.Font, text: str, pos: tuple[int, int], color: tuple[int, int, int] = (235, 235, 235)) -> int:
        surf = font.render(text, True, color)
        self.display.blit(surf, pos)
        return surf.get_height()

    def render_credits_section(self, section_name: str, items: list[dict], x: int, y: int) -> int:
        title = section_name.replace("_", " ").upper()
        y += self.render_unicode_text(self.credits_font, title, (x, y), (237, 220, 147)) + 14
        for item in items:
            if section_name == "fonts":
                y = self.render_font_credit_item(item, x + 16, y)
            else:
                y = self.render_simple_credit_item(item, x + 16, y)
        return y + 14

    def render_simple_credit_item(self, item: dict, x: int, y: int) -> int:
        name = item.get("credit", item.get("name", item.get("title", "Unnamed")))
        source = item.get("source", "")
        author = item.get("author", "")
        note = item.get("note", "")

        y += self.render_unicode_text(self.credits_small_font, name, (x, y), (235, 235, 235)) + 5

        if author:
            y += self.render_unicode_text(self.credits_small_font, f"Author: {author}", (x + 16, y), (200, 200, 200)) + 4

        if source and source not in name:
            y += self.render_unicode_text(self.credits_small_font, f"Source: {source}", (x + 16, y), (200, 200, 200)) + 4

        if note:
            y += self.render_unicode_text(self.credits_small_font, note, (x + 16, y), (200, 200, 200)) + 4

        return y + 14
    
    def render_font_credit_item(self, item: dict, x: int, y: int) -> int:
        name = item.get("name", "Unknown font")
        credit = item.get("credit", "")
        sample = item.get("sample", name)
        font_type = item.get("font_type", "ttf")
        path = item.get("path", "")

        y += self.render_unicode_text(self.credits_small_font, f"{name} — {credit}", (x, y), (235, 235, 235)) + 6

        if font_type == "bitmap":
            try:
                sample_font = Font(path, scale=1)
                sample_font.render(self.display, sample, (x + 16, y))
                y += self.get_font_height(sample_font) + 18
            except Exception as e:
                y += self.render_unicode_text(self.credits_small_font, f"Could not load sample: {e}", (x + 16, y), (180, 180, 180)) + 18
        else:
            try:
                sample_font = pygame.font.Font(path, 20)
                surf = sample_font.render(sample, True, (235, 235, 235))
                self.display.blit(surf, (x + 16, y))
                y += surf.get_height() + 18
            except Exception as e:
                y += self.render_unicode_text(self.credits_small_font, f"Could not load sample: {e}", (x + 16, y), (180, 180, 180)) + 18

        return y


    """ audio helpers """
    def load_audio_settings(self) -> None:
        try:
            with open(self.audio_settings_path, "r") as file:
                data: dict[str, Any] = json.load(file)

        except FileNotFoundError:
            # First run — seed base volumes from current Sound defaults
            self.base_sfx_volumes = {name: s.get_volume() for name, s in self.sfx.sounds.items()}
            self.base_voice_volumes = {name: s.get_volume() for name, s in self.sfx.voices.items()}
            return

        # Per-sound base volumes (these are what the detailed menu edits)
        self.base_sfx_volumes = {
            name: float(data.get("sfx", {}).get(name, self.sfx.sounds[name].get_volume()))
            for name in self.sfx.sounds
        }
        self.base_voice_volumes = {
            name: float(data.get("voices", {}).get(name, self.sfx.voices[name].get_volume()))
            for name in self.sfx.voices
        }

        # Masters + dev mode (backward compatible: old configs without these keys still work)
        masters: dict[str, Any] = data.get("masters", {})
        self.master_volume    = float(masters.get("master", 1.0))
        self.voices_master    = float(masters.get("voices", 1.0))
        self.heartbeat_master = float(masters.get("heartbeat", 1.0))
        self.sfx_master       = float(masters.get("sfx", 1.0))
        if "dev_mode" in data:
            self.dev_mode = bool(data["dev_mode"])

        if hasattr(self.sfx, "ensure_core_sfx_audible"):
            self.sfx.ensure_core_sfx_audible()

    def save_audio_settings(self) -> None:
        data: dict[str, Any] = {
            "sfx":    dict(self.base_sfx_volumes),
            "voices": dict(self.base_voice_volumes),
            "masters": {
                "master":    self.master_volume,
                "voices":    self.voices_master,
                "heartbeat": self.heartbeat_master,
                "sfx":       self.sfx_master,
            },
            "dev_mode": self.dev_mode,
        }

        with open(self.audio_settings_path, "w") as file:
            json.dump(data, file, indent=4)

    def apply_master_volumes(self) -> None:
        """Push masters to SoundEffects + push effective base volumes to pygame Sound objects."""
        # 1. Push masters to SoundEffects so runtime playback paths can scale dynamically-set volumes.
        self.sfx.set_masters(
            master=self.master_volume,
            sfx=self.sfx_master,
            voices=self.voices_master,
            heartbeat=self.heartbeat_master,
        )

        # 2. Bake base * masters into the Sound objects for paths that just call .play() with no volume.
        for name, sound in self.sfx.sounds.items():
            base = self.base_sfx_volumes.get(name, sound.get_volume())
            sound.set_volume(base * self.sfx_master * self.master_volume)
        for name, sound in self.sfx.voices.items():
            base = self.base_voice_volumes.get(name, sound.get_volume())
            sound.set_volume(base * self.voices_master * self.master_volume)

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
                self.save_audio_settings()
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
            self.base_sfx_volumes[name] = volume
        elif category == "voices":
            self.base_voice_volumes[name] = volume
        self.apply_master_volumes()
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
        clicked = self.pause_button.render(self.display)
        if self.heart_rate.is_psychosis(): return None
        if not clicked: return None
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
            self.render_text_buttons(self.main_menu_text_buttons + [self.credits_text_button], clickable=False)
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

    def start_heartbeat(self, bpm: float = 80) -> None:
        self.heart_rate.force_bpm(bpm)
        self.sfx.bpm_boost_target = self.heart_rate
        self.sfx.start_heartbeat(bpm=bpm)

    def set_heartbeat_bpm(self, bpm: float, ramp_rate: float = 8.0) -> None:
        self.heart_rate.set_target_bpm(bpm, ramp_rate=ramp_rate)

    def _bpm_to_volume(self, bpm: float) -> float:
            resting = self.heart_rate.resting_bpm
            maximum = self.heart_rate.max_bpm
            ratio = max(0.0, min(1.0, (bpm - resting) / (maximum - resting)))
            base = 0.4 + ratio * 0.4

            return base * self.heartbeat_master * self.master_volume

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
        if hasattr(self, "ghost_manager"): self.ghost_manager.clear()

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
        # if phase_name == "start":
        #     self.route_choice_scene_obj.reset()
        # elif phase_name == "choice_maker":
        #     self.route_choice_scene_obj.reset()
         

    """ other """
    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()

    def load_credits(self) -> dict[str, list[dict[str, str]]]:
        try:
            credits_path = asset("credits.json")
            with open(credits_path, "r", encoding="utf-8") as c:
                return json.load(c)
        except FileNotFoundError:
            return {"sfx": [], "voices": [], "music": []}
        except json.JSONDecodeError as e:
            print(f"[CREDITS JSON ERROR] {e}")
            return {"sfx": [], "voices": [], "music": []}


def main() -> None:
    Game().run()

if __name__ == "__main__":
    main()
