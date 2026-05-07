import pygame, os, sys, random, math

from scripts.core.utils import load_image
from scripts.ui.button import Button
from scripts.rendering.tilemap import Tilemap
from scripts.entities.entities import Player, NPC, Ghost, Follower
from scripts.ui.font import Font
from scripts.systems.heart_rate import HeartRateSystem
from scripts.audio.sounds import SoundEffects
from scripts.ui.dialogue_manager import DialogueManager

""" TO DRAW
o new ground.png
o new backgrounds.png (01 - 05)
o ghosts
o followers
o npcs
o animations
""" 

""" TO MAKE
o npc dialogues
o ghost haunt dialogues
o maybe voices?
o sounds?
o environment particles?

"""

class Game:
    def __init__(self): 
        pygame.init()
        self.game_name: str = "Demo"
        self.screen_w, self.screen_h = (720, 560)
        self.render_scale: int = 1
        self.screen = self.create_screen()
        self.display = self.create_display()
        self.clock = self.create_clock()
        self.sfx = SoundEffects()

        self.fps: int = 60
        self.scroll = 0

        self.asset_paths = {
            'backgrounds': 'assets/backgrounds',
            'slow_spikes': 'assets/foliage/slow_spikes',
            'levels': 'assets/levels',
            'tilesets': 'assets/tilesets',
            'ground': 'assets/snowy_ground.png',
            'resume_button': 'assets/buttons/resume_button.png',
            'quit_button': 'assets/buttons/quit_button.png',
            'start_button': 'assets/buttons/start_button.png',
            'pause_button': 'assets/buttons/pause_button.png',
            'heart_icon': 'assets/fonts/heart_icon.png',
            'bedroom_night': 'assets/backgrounds/bedroom_night.png',
            'kitchen_night': 'assets/backgrounds/kitchen_night.png',
            'fridge_open': 'assets/backgrounds/kitchen_night_fridge_open.png',
            'glass_of_milk': 'assets/entities/glass_of_milk.png',
            'sticky_note': 'assets/entities/sticky_note.png',
        }

        self.ground_image, self.ground_w, self.ground_h = load_image(self.asset_paths['ground'])

        self.main_menu_font = pygame.font.SysFont("arial", 40)
        self.main_menu_font_color = (255, 255, 255)

        self.pause_button_img, pb_w, pb_h = load_image(self.asset_paths['pause_button'], convert_white=True)
        self.pause_button = Button((5, 5), self.pause_button_img, img_scale=1)

        self.pause_menu_buttons: list[tuple[str, Button]] = self.create_centered_buttons(
            ['resume_button', 'quit_button'], scale=1
        )
        self.main_menu_buttons: list[tuple[str, Button]] = self.create_centered_buttons(
            ['start_button', 'quit_button'], scale=1
        )

        self.player_w, self.player_h = (16, 32)
        self.player_x = 20
        self.player_y = self.screen_h - self.ground_h - self.player_h + 5
        self.player_init_pos = (self.player_x, self.player_y)
        self.player = Player(self, self.player_init_pos, (self.player_w, self.player_h))
        self.player_movement = [0, 0]
        self.player_speed = 120

        self.player_facing = "right"

        self.intro_npc = NPC(
            self,
            name="NPC 1",
            pos=(self.player_x + 100, self.player_y),
            size=(16, 32),
            dialogue=[
                "You made it.",
                "Do you remember why you came here?",
                "Press E again to continue dialogue."
            ]
        )

        self.dialogue_manager = DialogueManager()

        """ mechanic 1 """
        self.ghosts = []
        self.mechanic1_active = False
        self.mechanic1_used = False
        self.ghost_random_active = True
        self.next_ghost_time = pygame.time.get_ticks() + random.randint(6000, 14000)
        self.ghost_positive_dialogues = [
            "you are doing okay",
            "keep breathing",
            "one step at a time",
            "you can pause",
            "you made it this far",
            "it is okay to slow down",
        ]

        self.ghost_neutral_dialogues = [
            "walk forward",
            "look around",
            "someone is nearby",
            "keep going",
            "wait",
            "listen",
            "check the door",
            "where are you going?",
        ]

        self.ghost_negative_dialogues = [
            "they are watching",
            "you look strange",
            "do not mess this up",
            "why are you stopping?",
            "they know",
            "you are too slow",
            "everyone noticed",
            "you cannot trust this",
        ]
        
        """ mechanic 2 """
        # self.followers = []
        # self.followers_active = False
        # self.follower_count = 6

        """ mechanic 3 """
        self.mechanic3_active = False
        self.mechanic3_transitioning = False
        self.mechanic3_target_active = False

        self.mechanic3_radius = max(self.internal_w, self.internal_h)
        self.mechanic3_min_radius = 22
        self.mechanic3_max_radius = max(self.internal_w, self.internal_h)
        self.mechanic3_speed = 480

        """ show help hint """
        self.show_help = True
        self.hint_font = Font('assets/fonts/large_font_white.png', scale=1)
        self.help_duration = 15000
        self.help_fade_duration = 2000
        self.help_alpha = 255
        self.help_start_time = pygame.time.get_ticks()

        """ heart rate system & stress"""
        self.heart_rate = HeartRateSystem()
        self.breathe_pressed = False
        self.heart_state = self.heart_rate.get_state()
        self.heart_icon, self.heart_icon_w, self.heart_icon_h = load_image(self.asset_paths['heart_icon'])
        self.heart_icon = pygame.transform.scale(self.heart_icon, (16, 16))
        self.heart_ui_font = pygame.font.SysFont("arial", 18)
        self.heart_ui_color = (255, 255, 255)
        self.thought_font = pygame.font.SysFont("arial", 16, bold=True)

        self.symptom_thoughts = [
            "something feels wrong",
            "i can feel it starting",
            "my chest feels tight",
            "it is getting louder",
            "i need to stay calm",
            "something is coming",
        ]

        self.coping_thoughts = [
            "breathing...",
            "trying to stay grounded",
            "focus on the floor",
            "slowly breathe out",
            "stay here",
            "this will pass",
        ]

        self.current_thought = ""
        self.thought_alpha = 0
        self.thought_timer = 0
        self.thought_change_delay = 1800
        self.last_thought_change = 0

        """ first scene """
        self.bedroom_night_img, *_ = load_image(self.asset_paths['bedroom_night'])
        self.kitchen_night_img, *_ = load_image(self.asset_paths['kitchen_night'])
        self.fridge_open_img, *_ = load_image(self.asset_paths['fridge_open'])
        self.milk_img, *_ = load_image(self.asset_paths['glass_of_milk'])
        self.sticky_note_img, *_ = load_image(self.asset_paths['sticky_note'])
        self.in_kitchen = False

        self.first_scene_scroll_x = 0
        self.first_scene_transitioning = False
        self.first_scene_transition_start = 0
        self.first_scene_transition_delay = 500
        self.first_scene_transition_speed = 900

        self.bedroom_to_kitchen_door = pygame.Rect(680, 330, 32, 64)

        self.first_scene_started = False
        self.first_scene_text_alpha = 0
        self.first_scene_start_time = 0
        self.first_scene_duration = 4500

        self.fade_alpha = 255
        self.fade_speed = 180

        self.scene_events = []
        self.scene_sequence = None
        self.scene_wait_until = 0

    def run(self):
        self.main_menu()

    def main_menu(self):
        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))
            self.destabilize_backgrounds()
            self.render_buttons("main")
            self.render_cursor_magnet(radius=100, strength=0.65, step=2)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pause_result = self.quit_game()
                        if pause_result:
                            self.quit_game()


            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def pause_menu(self):
        while True:
            pygame.mouse.set_visible(True)
            self.display.fill((0, 0, 0))
            self.destabilize_backgrounds()
            self.render_buttons("pause")
            self.render_cursor_magnet(radius=100, strength=0.65, step=2)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "resume"

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def destabilize_backgrounds(self):
        # self.render_background_images(parallax_increment=0.3)
        self.render_glitch(slices=45, max_offset=10, dark_alpha=65)
        self.render_screen_warp(strength=5, wave_size=24, speed=0.006, step=2)

    def render_fade(self, alpha):
        fade = pygame.Surface((self.internal_w, self.internal_h), pygame.SRCALPHA)
        fade.fill((0, 0, 0, int(alpha)))
        self.display.blit(fade, (0, 0))

    def start_sequence(self, sequence):
        self.scene_sequence = sequence
        self.scene_wait_until = 0

    def update_sequence(self):
        if not self.scene_sequence: return
        now = pygame.time.get_ticks()
        if now < self.scene_wait_until: return
        try:
            result = next(self.scene_sequence)
            if isinstance(result, int):
                self.scene_wait_until = now + result
        except StopIteration:
            self.scene_sequence = None

    def say(self, text, target, stall=1500):
        dialogue = self.dialogue_manager.dialogue_object(
            text=text,
            target=target,
            stall=stall
        )
        while not dialogue.finished: yield

    def wait_until_voice_finished(self):
        while self.sfx.is_voice_playing(): yield

    def voice(self, filename, volume=0.45):
        self.sfx.play_voice(filename, volume=volume)
        yield from self.wait_until_voice_finished()

    def render_transition_door(self):
        door = self.bedroom_to_kitchen_door.move(-self.first_scene_scroll_x, 0)
        glow = pygame.Surface((90, 120), pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) / 2
        for radius, alpha in [(50, 20), (35, 35), (22, 55)]:
            pygame.draw.circle(
                glow,
                (255, 240, 190, alpha + int(pulse * 15)),
                (45, 60),
                radius
            )
        self.display.blit(
            glow,
            (door.centerx - 45, door.centery - 60),
            special_flags=pygame.BLEND_RGBA_ADD
        )
        pygame.draw.rect(
            self.display,
            (255, 240, 200, 120),
            door,
            border_radius=3
        )
    
    def update_bedroom_to_kitchen_transition(self, dt):
        if not self.first_scene_transitioning:
            if self.player.rect().colliderect(self.bedroom_to_kitchen_door):
                self.first_scene_transitioning = True
                self.first_scene_transition_start = pygame.time.get_ticks()
                self.player_movement = [0, 0]
            return

        elapsed = pygame.time.get_ticks() - self.first_scene_transition_start

        if elapsed < self.first_scene_transition_delay:
            self.player_movement = [0, 0]
            return

        self.first_scene_scroll_x += self.first_scene_transition_speed * dt
        self.first_scene_scroll_x = min(self.first_scene_scroll_x, self.internal_w)

        self.player_movement = [0, 0]

        if self.first_scene_scroll_x >= self.internal_w:
            self.player.pos[0] = self.internal_w + 80
            self.first_scene_transitioning = False
            
    def first_scene_sequence(self):
        yield 1000
        yield from self.say("I can't sleep", self.player)
        yield 2000
        yield from self.say(
            ["i don't know why...", "they keep me up at night", "i am feeling quite a bit thirsty though"],
            self.player
        )
        yield 1000
        yield from self.voice("go_get_a_cup_of_milk.mp3")
        yield 2000
        yield from self.say("huh? okay", self.player)
        yield 1000
        # glowing -> for the level transition to kitchen
        # when player is close to the fridge, [E] to Interact will appear
        # when player pressess E, fridge door opens and player holds cup from assets/entities/cup_of_milk.png
        # voice: 'that's expired'
        # when player pressed E to close the fridge, "there's a note"
        # mouse hover over sticky note, sticky note glows, 
        # mouse clicks on sticky note, sticky note opens up
        # then pressing esc gets you out of sticky note
        # sticky note flies to the top left of screen. can be activated with Tab, like a task
        # glowing door for going back to the bedroom
        # voice: 'dont turn around'
        # level transition back to bedroom.
        # "im sleepy now"
        # voice: 'someone's at the door'
        # "i didn't hear anyone"
        # "probably one of them saying something random"
        # goes to sleep
        # end

    def first_scene(self):
        self.first_scene_start_time = pygame.time.get_ticks()
        self.fade_alpha = 255
        self.first_scene_text_alpha = 0

        # place player near bed
        self.player.pos = [110, self.screen_h - self.ground_h - self.player_h -30]
        self.player_movement = [0, 0]

        while True:
            dt = self.clock.get_time() / 1000
            now = pygame.time.get_ticks()
            elapsed = now - self.first_scene_start_time

            self.display.fill((0, 0, 0))

            """ background """
            self.display.blit(
                pygame.transform.scale(self.bedroom_night_img, (self.internal_w, self.internal_h)),
                (-self.first_scene_scroll_x, 0)
            )

            self.display.blit(
                pygame.transform.scale(self.kitchen_night_img, (self.internal_w, self.internal_h)),
                (self.internal_w - self.first_scene_scroll_x, 0)
            )

            """ door """
            self.render_transition_door()

            """ player """
            self.handle_first_scene_input(dt)

            if not self.first_scene_transitioning:
                self.player.update(self.player_movement, dt)
            else:
                self.player_movement = [0, 0]

            self.update_bedroom_to_kitchen_transition(dt)

            self.player.render(self.display, offset=(self.first_scene_scroll_x, 0))

            if not self.first_scene_started and elapsed > 1000:
                self.first_scene_started = True
                self.start_sequence(self.first_scene_sequence())

            self.update_sequence()
            self.dialogue_manager.update()
            self.dialogue_manager.render(self.display, offset=(self.first_scene_scroll_x, 0))

            if self.fade_alpha > 0:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
                self.render_fade(self.fade_alpha)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    # temporary skip for testing
                    if event.key == pygame.K_RETURN:
                        return "continue"

            # if elapsed >= self.first_scene_duration:
            #     return "continue"

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_first_scene_input(self, dt):
        key = pygame.key.get_pressed()

        self.player_movement = [0, 0]

        if key[pygame.K_a]:
            self.player_movement[0] -= self.player_speed * dt
            self.player_facing = "left"

        if key[pygame.K_d]:
            self.player_movement[0] += self.player_speed * dt
            self.player_facing = "right"
                
    def game_loop(self):
        while True:
            pygame.mouse.set_visible(False)
            dt = self.clock.get_time() / 1000
            self.display.fill((0, 0, 0))

            """ heart """
            is_observed = self.is_player_observed()

            self.heart_rate.update(
                dt=dt,
                is_observed=is_observed,
                breathe_pressed=self.breathe_pressed
            )
            self.sfx.play_heartbeat(self.heart_rate.bpm)

            """ renders """
            # self.render_background_images(parallax_increment=0.3)
            self.render_glitch(slices=45, max_offset=10, dark_alpha=65)
            self.render_ground()
            self.update_random_ghost_trigger()
            stress = self.heart_rate.stress_amount()
            movement = self.player_movement.copy()

            if stress > 0.55:
                movement[0] *= 1 - (stress * 0.35)

            if stress > 0.75 and random.random() < 0.04:
                movement[0] = 0

            self.player.update(movement, dt)
            self.intro_npc.render(self.display, offset=(self.scroll, 0))
            self.heart_rate.render(self.display)
            self.render_heart_ui()
            self.update_player_thoughts(dt)
            self.render_player_thoughts()
            self.render_player_status()

            for ghost in self.ghosts[:]:
                ghost.update()
                ghost.render(self.display, offset=(self.scroll, 0))
                ghost.render_dialogue(self.display, offset=(self.scroll, 0))

                if ghost.alpha <= 0:
                    self.ghosts.remove(ghost)

            if not self.ghosts:
                self.mechanic1_active = False

            # for follower in self.followers[:]:
            #     follower.update(self.player, self.player_facing)
            #     follower.render(self.display, offset=(self.scroll, 0))
            #     follower.render_dialogue(self.display, offset=(self.scroll, 0))

            #     if not follower.alive:
            #         self.followers.remove(follower)

            # if not self.followers:
            #     self.followers_active = False

            self.player.render(self.display, offset=(self.scroll, 0))
            if self.intro_npc.is_player_close(self.player):
                self.intro_npc.render_dialogue(self.display, offset=(self.scroll, 0))
            else:
                self.intro_npc.talking = False
                self.intro_npc.dialogue_index = 0

            # self.update_mechanic3(dt)
            # self.render_mechanic3()

            if self.show_help:
                self.show_help_hints()
                now = pygame.time.get_ticks()
                elapsed = now - self.help_start_time

                if elapsed > self.help_duration:
                    fade_elapsed = elapsed - self.help_duration

                    if fade_elapsed >= self.help_fade_duration:
                        self.show_help = False
                    else:
                        fade_progress = fade_elapsed / self.help_fade_duration
                        self.help_alpha = int(255 * (1 - fade_progress))
            
            if self.handle_pause_button(): return 'menu'

            # self.tilemap.render_collision(self.display, self.scroll)
            # self.tilemap.render_decor(self.display, self.scroll)

            self.handle_input(dt)

            self.scale_display_to_screen()
            pygame.display.update()
            self.clock.tick(self.fps)

    def handle_input(self, dt):
        key = pygame.key.get_pressed()
        was_breathing = self.breathe_pressed
        self.breathe_pressed = key[pygame.K_b]

        if was_breathing and not self.breathe_pressed:
            if self.heart_rate.coping_worked:
                self.fade_ghosts()

        self.player_movement = [0, 0]

        if self.breathe_pressed:
            self.player_movement = [0, 0]
        else:
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
                self.handle_keydown(event)

    def handle_keydown(self, event):
        press_escape: bool = event.key == pygame.K_ESCAPE
        press_interact: bool = event.key == pygame.K_e
        press_1: bool = event.key == pygame.K_1
        press_2: bool = event.key == pygame.K_2
        press_3: bool = event.key == pygame.K_3
        press_space: bool = event.key == pygame.K_SPACE
        
        if press_escape: self.pause_menu()
        elif press_interact:
            if self.intro_npc.is_player_close(self.player): 
                self.intro_npc.interact()
        elif press_1: self.activate_mechanic1()
        elif press_2: 
            # self.activate_mechanic2()
            pass
        elif press_3: 
            # self.activate_mechanic3()
            pass
        elif press_space: self.player.jump()
                
    def show_help_hints(self):
        hints = [
            'Press A -- move left',
            'Press D -- move right',
            'Press E -- interact',
            'Press SPACE -- jump',
            'Press B -- breathe',
        ]

        char_height = next(iter(self.hint_font.characters.values())).get_height()

        padding_x = 15
        padding_y = 45
        line_spacing = 6

        for idx, hint in enumerate(hints):
            y = padding_y + idx * (char_height + line_spacing)

            self.hint_font.render(
                self.display,
                hint,
                (padding_x, y)
            )

    def point_too_close(self, point, existing_points, min_radius=30):
        px, py = point
        for ex, ey in existing_points:
            distance = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
            if distance < min_radius: return True
            if abs(py - ey) < min_radius: return True
        return False

    def is_player_observed(self):
        for ghost in self.ghosts:
            distance = abs(ghost.pos[0] - self.player.pos[0])
            if distance < 140: return True
        return False
    
    def update_random_ghost_trigger(self):
        if self.mechanic1_used: return
        if not self.ghost_random_active: return
        if self.ghosts: return
        now = pygame.time.get_ticks()
        if now >= self.next_ghost_time:
            self.activate_mechanic1()
            self.next_ghost_time = now + random.randint(10000, 22000)
            
    def activate_mechanic1(self):
        if self.mechanic1_used: return
        self.mechanci1_used = True
        if self.ghosts:
            all_stopped = all(ghost.reached_target for ghost in self.ghosts)

            if all_stopped:
                for ghost in self.ghosts:
                    ghost.start_fade()
            return

        self.mechanic1_active = True
        self.ghosts = []

        player_color = (255, 255, 255)
        ghost_num = 5

        border_padding = 35
        player_avoid_radius = 120
        ghost_spacing = 80

        min_y = 100
        max_y = self.screen_h - self.ground_h - self.player_h - 20

        used_points = []

        for idx in range(ghost_num):
            move_x = self.player.pos[0]
            move_y = self.player.pos[1]

            for attempt in range(200):
                move_x = random.randint(
                    border_padding,
                    self.internal_w - self.player_w - border_padding
                )

                move_y = random.randint(
                    min_y,
                    max_y
                )

                dist_from_player = math.dist(
                    (move_x, move_y),
                    (self.player.pos[0], self.player.pos[1])
                )

                if dist_from_player < player_avoid_radius:
                    continue

                if self.point_too_close((move_x, move_y), used_points, min_radius=ghost_spacing):
                    continue

                break

            used_points.append((move_x, move_y))

            dialogue = [
                ("positive", random.choice(self.ghost_positive_dialogues)),
                ("neutral", random.choice(self.ghost_neutral_dialogues)),
                ("negative", random.choice(self.ghost_negative_dialogues)),
            ]

            random.shuffle(dialogue)

            ghost = Ghost(
                self,
                name=f"Ghost {idx + 1}",
                pos=self.player.pos.copy(),
                size=(self.player_w, self.player_h),
                move_to=(move_x, move_y),
                color=player_color,
                dialogue=dialogue,
            )

            self.ghosts.append(ghost)
    
    def fade_ghosts(self):
        for ghost in self.ghosts:
            ghost.start_fade()
            
    def activate_mechanic2(self):
        if self.followers: return
        self.followers_active = True
        self.followers = []

        spacing = 25
        start_offset = 40
        half_count = self.follower_count // 2
        follower_size = (20, 64)
        player_bottom = self.player.pos[1] + self.player.size[1]
        spawn_y = player_bottom - follower_size[1]

        for idx in range(half_count):
            spawn_x = self.player.pos[0] - start_offset - (idx * spacing)

            follower = Follower(
                self,
                name=f"Follower {len(self.followers) + 1}",
                pos=(spawn_x, spawn_y),
                size=follower_size,
            )

            self.followers.append(follower)

        for idx in range(self.follower_count - half_count):
            spawn_x = self.player.pos[0] + start_offset + (idx * spacing)

            follower = Follower(
                self,
                name=f"Follower {len(self.followers) + 1}",
                pos=(spawn_x, spawn_y),
                size=follower_size,
            )

            self.followers.append(follower)
    
    def activate_mechanic3(self):
        self.mechanic3_transitioning = True
        self.mechanic3_target_active = not self.mechanic3_target_active
        if self.mechanic3_target_active: self.mechanic3_active = True

    def update_mechanic3(self, dt):
        if not self.mechanic3_transitioning: return
        speed = self.mechanic3_speed * dt
        if self.mechanic3_target_active:
            self.mechanic3_radius -= speed
            if self.mechanic3_radius <= self.mechanic3_min_radius:
                self.mechanic3_radius = self.mechanic3_min_radius
                self.mechanic3_transitioning = False
        else:
            self.mechanic3_radius += speed
            if self.mechanic3_radius >= self.mechanic3_max_radius:
                self.mechanic3_radius = self.mechanic3_max_radius
                self.mechanic3_transitioning = False
                self.mechanic3_active = False

    def render_mechanic3(self):
        if not self.mechanic3_active: return
        self.render_mechanic3_darkness()
    
    def render_buttons(self, btype):
        if btype == "main":
            for name, button in self.main_menu_buttons:
                if button.render(self.display):
                    if name == 'start_button':
                        result = self.first_scene()
                        if result == "continue":
                            result = self.game_loop()
                        if result == "menu":
                            continue
                    elif name == 'quit_button':
                        self.quit_game()
        if btype == "pause":
            for name, button in self.pause_menu_buttons:
                if button.render(self.display):
                    if name == 'resume_button':
                        return "resume"
                    elif name == 'quit_button':
                        return self.quit_game()
        return
    
    def render_ground(self):
        for idx in range(15):
            self.display.blit(self.ground_image, ((idx * self.ground_w) - self.scroll * 2.2, self.screen_h - self.ground_h))

    def render_background_images(self, images, parallax_increment: float = 0.2):
        for idx in range(3):
            parallax_speed: float = 1
            for image in images:
                self.display.blit(image, ((idx * self.bg_width) - self.scroll * parallax_speed, 0))
                parallax_speed += parallax_increment

    def render_glitch(self, slices=45, max_offset=10, dark_alpha=65, speed=90, jitter_chance=0.35, big_jump_chance=0.08):
        original = self.display.copy()
        glitched = original.copy()

        screen_w, screen_h = self.display.get_size()
        slice_h = max(1, screen_h // slices)
        tick = pygame.time.get_ticks() // speed

        for i in range(slices):
            y = i * slice_h
            h = slice_h

            if y + h > screen_h:
                h = screen_h - y

            base_offset = ((tick + i * 19) % (max_offset * 2)) - max_offset

            if (tick + i * 7) % 100 > jitter_chance * 100:
                offset = 0
            else:
                offset = base_offset

            if (tick + i * 13) % 100 < big_jump_chance * 100:
                offset *= 2

            slice_rect = pygame.Rect(0, y, screen_w, h)
            slice_img = original.subsurface(slice_rect).copy()
            glitched.blit(slice_img, (offset, y))

        self.display.blit(glitched, (0, 0))

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, dark_alpha))
        self.display.blit(overlay, (0, 0))

    def render_cursor_magnet(self, radius=70, strength=0.35, step=2):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        original = self.display.copy()

        for y in range(mouse_y - radius, mouse_y + radius, step):
            for x in range(mouse_x - radius, mouse_x + radius, step):
                dx = mouse_x - x
                dy = mouse_y - y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance == 0 or distance > radius:
                    continue

                pull = (1 - distance / radius) * strength

                source_x = int(x + dx * pull)
                source_y = int(y + dy * pull)

                if (
                    0 <= x < self.internal_w and
                    0 <= y < self.internal_h and
                    0 <= source_x < self.internal_w and
                    0 <= source_y < self.internal_h
                ):
                    color = original.get_at((source_x, source_y))

                    pygame.draw.rect(
                        self.display,
                        color,
                        pygame.Rect(x, y, step, step)
                    )
                    
    def render_screen_warp(self, strength=4, wave_size=28, speed=0.006, step=2):
        original = self.display.copy()
        tick = pygame.time.get_ticks() * speed

        for y in range(0, self.internal_h, step):
            wave = math.sin((y / wave_size) + tick)
            offset_x = int(wave * strength)

            source_rect = pygame.Rect(0, y, self.internal_w, step)
            slice_img = original.subsurface(source_rect).copy()

            self.display.blit(slice_img, (offset_x, y))
                            
    def render_cursor_distortion(self, radius=45, slices=12, max_offset=8):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        original = self.display.copy()
        distortion = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        area = pygame.Rect(
            mouse_x - radius,
            mouse_y - radius,
            radius * 2,
            radius * 2
        )

        area.clamp_ip(self.display.get_rect())

        sample = original.subsurface(area).copy()

        slice_h = max(1, sample.get_height() // slices)

        for i in range(slices):
            y = i * slice_h
            h = slice_h

            if y + h > sample.get_height():
                h = sample.get_height() - y

            offset = random.randint(-max_offset, max_offset)

            slice_rect = pygame.Rect(0, y, sample.get_width(), h)
            slice_img = sample.subsurface(slice_rect).copy()

            distortion.blit(slice_img, (offset, y))

        self.display.blit(distortion, area.topleft)

    def update_player_thoughts(self, dt):
        bpm = self.heart_rate.bpm
        now = pygame.time.get_ticks()

        if bpm < 100:
            self.thought_alpha -= 120 * dt
            self.thought_alpha = max(0, self.thought_alpha)
            return

        if now - self.last_thought_change >= self.thought_change_delay:
            if self.breathe_pressed:
                self.current_thought = random.choice(self.coping_thoughts)
            else:
                self.current_thought = random.choice(self.symptom_thoughts)

            self.last_thought_change = now

        stress = self.heart_rate.stress_amount()
        target_alpha = int(35 + stress * 65)
        target_alpha = min(100, target_alpha)

        self.thought_alpha += (target_alpha - self.thought_alpha) * 0.08

        self.thought_change_delay = int(2200 - stress * 1100)
        self.thought_change_delay = max(700, self.thought_change_delay)

    def render_player_thoughts(self):
        if not self.current_thought or self.thought_alpha <= 1: return
        player_x = self.player.pos[0] - self.scroll
        player_y = self.player.pos[1]
        stress = self.heart_rate.stress_amount()
        is_high_stress = self.heart_rate.bpm >= 130
        color = (255, 255, 255)
        if self.breathe_pressed: color = (180, 220, 255)
            
        max_width = int(220 - stress * 80)
        words = self.current_thought.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.thought_font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())
        line_height = self.thought_font.get_height()

        for i, line in enumerate(lines):
            text_surf = self.thought_font.render(line, True, color)
            alpha = int(self.thought_alpha * (0.6 + stress * 0.4))
            text_surf.set_alpha(alpha)

            x = player_x + self.player.size[0] // 2 - text_surf.get_width() // 2
            y = player_y - 36 + (i * line_height)

            if self.breathe_pressed:
                x += random.randint(-2, 2)
                y += int(math.sin(pygame.time.get_ticks() * 0.01 + i) * (stress * 4))

            glitch_strength = int(1 + stress * 4)
            for _ in range(glitch_strength):
                    glitch = text_surf.copy()
                    glitch.set_alpha(int(self.thought_alpha * 0.6))
                    jitter_x = random.randint(-4, 4)
                    jitter_y = random.randint(-2, 2)
                    self.display.blit(glitch, (x + jitter_x, y + jitter_y))

            self.display.blit(text_surf, (x, y))

    def render_player_status(self):
        status = self.heart_rate.get_state()
        text = f"[{status}]"

        if status == "steady heartbeat":
            color = (230, 230, 230)
        elif status == "irregular":
            color = (255, 220, 180)
        elif status == "something is coming":
            color = (255, 180, 120)
        elif status == "panic attack":
            color = (255, 100, 100)
        else:
            color = (255, 40, 40)

        text_surf = self.heart_ui_font.render(text, True, color)

        padding_x = 10
        padding_y = 5

        box_w = text_surf.get_width() + padding_x * 2
        box_h = text_surf.get_height() + padding_y * 2

        x = self.internal_w // 2 - box_w // 2
        y = 10

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 170))

        self.display.blit(box, (x, y))
        self.display.blit(text_surf, (x + padding_x, y + padding_y))
        
    def handle_pause_button(self):
        if self.pause_button.render(self.display):
            result = self.pause_menu()
            if result == "quit_to_menu":
                return True
        return False

    def create_centered_buttons(self, asset_keys: list[str], scale: int = 1) -> list[tuple[str, Button]]:
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
        current_y = start_y - (total_height // 2)

        buttons = []
        for asset_key, img, w, h in button_data:
            x = center_x - (w // 2)
            y = current_y

            button = Button((x, y), img, scale)
            buttons.append((asset_key, button))

            current_y += h + gap

        return buttons

    def load_background_images(self, dirname: str) -> tuple[int, list[pygame.Surface]]:
        bg_images = []
        bg_paths: list[str] = os.listdir(dirname)
        bg_width = 0

        for idx, bg_path in enumerate(bg_paths):
            bg_image, bg_w, bg_h = load_image(os.path.join(dirname, bg_path))
            if idx == 0:
                bg_width = bg_w
            bg_images.append(bg_image)

        return bg_width, bg_images

    def render_heart_ui(self):
        bpm = int(self.heart_rate.bpm)
        state = self.heart_rate.get_state()

        if state == "calm":
            color = (255, 255, 255)
        elif state == "uneasy":
            color = (255, 200, 200)
        elif state == "overwhelmed":
            color = (255, 120, 120)
        else:
            color = (255, 60, 60)

        pulse = (math.sin(self.heart_rate.pulse_timer) + 1) / 2
        pulse_scale = 1 + pulse * 0.15

        icon_size = int(16 * pulse_scale)
        icon = pygame.transform.scale(self.heart_icon, (icon_size, icon_size)).copy()

        # stress fill amount
        stress_units = getattr(self.heart_rate, "stress_units", 0)
        max_stress_units = getattr(self.heart_rate, "max_stress_units", 20)
        fill_ratio = stress_units / max_stress_units
        fill_ratio = max(0, min(1, fill_ratio))

        # create red fill
        red_fill = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        fill_height = int(icon_size * fill_ratio)

        pygame.draw.rect(
            red_fill,
            (255, 0, 0, 180),
            pygame.Rect(0, icon_size - fill_height, icon_size, fill_height)
        )

        mask = icon.copy()
        mask.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)

        red_fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        icon.blit(red_fill, (0, 0))

        bpm_text = str(bpm)
        text_surf = self.heart_ui_font.render(bpm_text, True, color)

        gap = 6
        total_width = icon.get_width() + gap + text_surf.get_width()

        x = (self.internal_w // 2) - (total_width // 2)
        y = 50

        self.display.blit(icon, (x, y))
        self.display.blit(text_surf, (x + icon.get_width() + gap, y - 1))
        
    def scale_display_to_screen(self):
        self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

    def create_screen(self):
        pygame.display.set_caption(self.game_name)
        return pygame.display.set_mode((self.screen_w, self.screen_h))

    def create_display(self):
        self.internal_w: int = self.screen_w // self.render_scale
        self.internal_h: int = self.screen_h // self.render_scale
        return pygame.Surface((self.internal_w, self.internal_h))

    def create_clock(self):
        return pygame.time.Clock()

    def quit_game(self):
        pygame.quit()
        sys.exit()


def main():
    inst = Game()
    inst.run()


if __name__ == "__main__":
    main()
