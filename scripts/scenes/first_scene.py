import pygame, math, random
from typing import *
from datetime import datetime, timedelta

from scripts.core.utils import load_image
from scripts.ui.font import Font

class FirstScene:
    """ setup """
    def __init__(self, game):
        self.game = game
        self.scene_ended: bool = False

        self.asset_paths: dict[str, str] = {
            'bedroom_night'     : 'assets/backgrounds/bedroom_night.png',
            'kitchen_night'     : 'assets/backgrounds/kitchen_night.png',
            'fridge_open'       : 'assets/backgrounds/kitchen_night_fridge_open.png',
            'milk_img'          : 'assets/entities/glass_of_milk.png',
            'sticky_note_img'   : 'assets/entities/sticky_note.png',
            'bedroom_day': 'assets/backgrounds/bedroom_day.png',
            'kitchen_day': 'assets/backgrounds/kitchen_day.png',
        }

        for path in self.asset_paths.values():
            self.game.live.watch(path)

        self.bedroom_night_img, *_  = load_image(self.asset_paths['bedroom_night'])
        self.kitchen_night_img, *_  = load_image(self.asset_paths['kitchen_night'])
        self.fridge_open_img, *_    = load_image(self.asset_paths['fridge_open'])
        self.milk_img, *_           = load_image(self.asset_paths['milk_img'])
        self.sticky_note_img, *_    = load_image(self.asset_paths['sticky_note_img'])

        """ flags """
        self.flags = {
            "door_unlocked"         : False,
            "fridge_seen"           : False,
            "fridge_opened"         : False,
            "note_unlocked"         : False,
            "read_sticky_note"      : False,
            "sticky_note_open"      : False,
            "sticky_note_complete"  : False,
            "milk_taken"            : False,
            "getting_milk"          : False,
            "milk_ready"            : False,
            "holding_milk"          : False,
            "drank_milk"            : False,
            "force_note_glow"       : False,
            "can_sleep"             : False,
            "going_to_bed"          : False,
            "sleeping"              : False,
            "is_next_day"           : False,
            "clothes_changed"       : False,
            "ready_to_go"           : False,
        }

        """ doors & collision areas """
        self.bed_rect                   = pygame.Rect(95, 305, 210, 120)
        self.bed_prompt_alpha           = 0
        self.bedroom_to_kitchen_trigger = pygame.Rect(717, 330, 8, 128)
        self.kitchen_to_bedroom_trigger = pygame.Rect(723, 300, 8, 128)
        self.in_kitchen: bool           = False
        self.transitioning: bool        = False
        self.transition_start: int      = 0
        self.transition_delay: int      = 500
        self.transition_speed: int      = 900
        self.scroll_x: int              = 0


        """ fridge """
        self.fridge_rect                = pygame.Rect(720 + 500, 250, 90, 190)
        self.kitchen_x                  = self.game.internal_w
        self.fridge_prompt_alpha        = 0
        self.fridge_transition_alpha    = 0
        self.fridge_transition_speed    = 650
        self.fridge_glow_active: bool   = False
        

        """ milk """
        self.get_milk_hold_time = 1800
        self.get_milk_progress = 0
        self.get_milk_prompt_alpha = 0
        self.get_milk_started_sound = False
        self.loading_angle = 0
        self.milk_hold_offset = (10, 8)
        self.milk_in_hand_img = pygame.transform.scale(self.milk_img, (18, 22))

        """ text? """
        self.started: bool = False
        self.start_time: int = 0
        self.fade_alpha: int = 255
        self.fade_speed: int = 180


        """ sticky note """
        self.sticky_note_font = pygame.font.Font("assets/fonts/Retrogression-Regular.ttf", 25)
        self.menu_font = Font("assets/fonts/large_font_white.png", scale=1)
        self.current_sticky_note_lines = None
        self.groceries_task = ["cereal", "fruits", "vegetables", "milk", "toilet rolls"]
        self.sticky_note_icon_rect = None

        """ digital clock """
        self.clock_begin_ticks = pygame.time.get_ticks()

        """ glow lines """
        self.glow = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)

    """ setup """
    def live_reload(self):
        changed = False

        for key, path in self.asset_paths.items():
            if self.game.live.changed(path):
                changed = True
                print(f"[live reload] {path}")

        if not changed:
            return

        self.bedroom_night_img, *_ = load_image(self.asset_paths["bedroom_night"])
        self.kitchen_night_img, *_ = load_image(self.asset_paths["kitchen_night"])
        self.fridge_open_img, *_ = load_image(self.asset_paths["fridge_open"])
        self.milk_img, *_ = load_image(self.asset_paths["milk_img"])
        self.sticky_note_img, *_ = load_image(self.asset_paths["sticky_note_img"])
        self.milk_in_hand_img = pygame.transform.scale(self.milk_img, (18, 22))
    
    def world_points(self, points, world_x=0) -> list[tuple[int, int]]:
        return [(x + world_x, y) for x, y in points]

    def polygon_center(self, points) -> tuple[int, int]:
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return int(x - self.scroll_x), int(y)   
    
    def get_mouse_pos(self) -> tuple[int, int]:
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)
    
    def reset(self) -> None:
        self.in_kitchen = False
        self.scroll_x = 0
        self.transitioning = False
        self.transition_start = 0
        self.started = False
        self.start_time = pygame.time.get_ticks()
        self.fade_alpha = 255
        self.game.player.pos = [ 
            110,
            self.game.screen_h - self.game.ground_h - self.game.player_h - 30
        ]
        self.game.player_movement = [0, 0]

    def run(self) -> None:
        self.reset()
        while True:
            dt = self.game.clock.get_time() / 1000
            self.live_reload()
            elapsed = pygame.time.get_ticks() - self.start_time

            self.game.display.fill((0, 0, 0))

            if not self.flags['is_next_day']: 
                self.render_backgrounds("night")
            else: 
                self.render_backgrounds("day")

            self.render_clock()
            self.update_fridge_transition(dt)
            if self.flags["door_unlocked"]: 
                self.render_transition_prompt(dt)
            self.render_fridge_interaction(dt)
            self.render_get_milk_prompt(dt)
            self.render_get_milk_loading()
            self.render_bed_sleep_prompt(dt)
            self.render_note_interaction()
            self.render_sticky_note_icon()
            self.render_open_sticky_note()
            mx, my = self.mouse_helper()
            # pygame.draw.rect(self.game.display, (255, 255, 255, 100), (64, 128, 64, 128))

            self.update_get_milk(dt)
            self.handle_input(dt)
            if not self.transitioning:
                self.game.player.update(self.game.player_movement, dt)
            else:
                self.game.player_movement = [0, 0]

            self.update_transition(dt)
            self.game.player.render(self.game.display, offset=(self.scroll_x, 0))
            self.render_milk_in_hand()
            if not self.started and elapsed > 1000:
                self.started = True
                self.game.cutscene.start(self.sequence())
            self.game.cutscene.update()
            self.game.dialogue_manager.update()
            self.game.thought_manager.update(dt)
            self.game.sfx.update()

            self.game.thought_manager.render(self.game.display, offset=(self.scroll_x, 0))
            self.game.dialogue_manager.render(self.game.display, offset=(self.scroll_x, 0))


            result = self.handle_events()
            if result: 
                return result
            
            if self.scene_ended:
                return "route_choice"

            self.game.handle_pause_button()
            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)

            if self.fade_alpha > 0:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
                self.render_fade(self.fade_alpha)

            if self.flags['sleeping']:
                self.end_fade_alpha = min(255, self.end_fade_alpha + self.end_fade_speed * dt)
                self.render_fade(self.end_fade_alpha)

                if self.end_fade_alpha >= 255:
                    self.game.cutscene.start(self.wake_up())


    """ story scripts """
    def sequence(self):
        yield from self.game.cutscene.wait(1000)
        yield from self.game.cutscene.say("ugh... I can't sleep", self.game.player)
        self.game.sfx.start_heartbeat(bpm=70, volume=0.25)
        yield from self.game.cutscene.racethink(["why am i still awake?", "did i hear something?", "no seriously"], self.game.player)
        self.game.sfx.play_voice("someones_at_the_door")
        self.game.sfx.play_voice("biexinta")
        yield from self.game.cutscene.wait(500)
        self.game.sfx.set_heartbeat_bpm(80)
        yield from self.game.cutscene.say(
            ["someone- what?", "i don't know why...", "but they keep me up at night"],
            self.game.player
        )
        yield from self.game.cutscene.wait(1000)
        self.game.sfx.set_heartbeat_bpm(70)
        yield from self.game.cutscene.cloudthink(["...a bit thirsty...", "what to drink?", "maybe milk?", "or ice cold water?", "can of coke?", "no, sleep first"], self.game.player, stall=2000)
        yield from self.game.cutscene.wait(500)
        self.game.sfx.play_voice("glass_of_milk")
        yield from self.game.cutscene.wait(1500)
        self.game.sfx.set_heartbeat_bpm(80)
        yield from self.game.cutscene.say(["who- who's there?", "how can you hear what i'm thinking???"], self.game.player)
        yield from self.game.cutscene.racethink("what's going on", self.game.player)
        self.game.sfx.set_heartbeat_bpm(90, volume=0.35)
        yield from self.game.cutscene.say(["huh? I'm-", "im not", "i can't help it", "they stress me out"], self.game.player)
        yield from self.game.cutscene.wait(1000)
        yield from self.game.cutscene.say(["hello-?", "they don't respond to what I say", "they just talk whenever they want to", "i cant- control them"], self.game.player)
        self.game.sfx.set_heartbeat_bpm(70, volume=0.2)
        self.flags["door_unlocked"] = True

    def get_milk(self):
        if not self.in_kitchen and not self.flags['fridge_opened']: return
        yield from self.game.cutscene.wait(1000)
        self.game.sfx.set_heartbeat_bpm(70)
        self.game.sfx.play_voice("dont_touch_that")
        self.game.sfx.play_voice("do_it_again")
        yield from self.game.cutscene.cloudthink(["hmm...", "this is milk right?", "am I seeing things?", "was I thirsty?", "mom wanted me to buy groceries tomorrow... I think", "didn't I just drink a glass?", "maybe I had water", "was it expired?", "why do I listen to her?", "did God send her here to spy on me?", "why do I listen and do whatever she tells me to do?", "no, before that", "what was I doing?", "did I already drink milk?", "what's next?", "double check", "there's milk in this glass", "no there isn't", "i should check again", "something's wrong", "is this poison"], self.game.player)
        self.game.sfx.set_heartbeat_bpm(100, volume=.3)
        yield from self.game.cutscene.voice("that_milks_expired")
        yield from self.game.cutscene.wait(500)
        yield from self.game.cutscene.voice("drink_it")
        yield from self.game.cutscene.voice("that_milks_expired")
        yield from self.game.cutscene.wait(1000)
        yield from self.game.cutscene.say(["i can't tell what's real and what's not", "it's driving me nuts"], self.game.player)
        yield from self.game.cutscene.wait(1000)
        self.game.sfx.set_heartbeat_bpm(120, volume=.4)
        yield from self.game.cutscene.voice("dont_touch_that")
        yield from self.game.cutscene.voice("look_behind_you")
        self.game.sfx.set_heartbeat_bpm(110, volume=.35)
        yield from self.game.cutscene.say(["i hope panadol helps", "i haven't had a good sleep since foreever", "i- i'm going back to sleep", "did I drink milk yet?", "did mom already buy the groceries?", "wait..."], self.game.player)
        self.game.sfx.play_key("pill_bottle")
        yield from self.game.cutscene.cloudthink(["need sleep", "can't trust my memory", "why can't i do simple things?", "this doesn't feel real", "was that glass of milk always there?", "am i dreaming?", "normal people can do this"], self.game.player)
        self.game.sfx.set_heartbeat_bpm(110, volume=.3)

        if not self.flags["read_sticky_note"]:
            self.flags["force_note_glow"] = True
        else:
            self.flags["can_sleep"] = True
        return
    
    def go_to_bed(self):
        self.game.player_movement = [0, 0]
        self.flags["holding_milk"] = False
        self.flags["drank_milk"] = True

        drinking_sounds = self.game.sfx.drinking_sounds.copy()
        random.shuffle(drinking_sounds)

        for sound in drinking_sounds:
            if not sound: continue
            self.game.sfx.play(sound)
            yield from self.game.cutscene.wait(500)

        self.game.sfx.set_heartbeat_bpm(90, volume=.25)
        self.game.sfx.play_key("glass_on_table")
        yield from self.game.cutscene.wait(450)

        self.game.sfx.play_footstep("wood")
        yield from self.game.cutscene.wait(320)
        self.game.sfx.play_footstep("wood")
        yield from self.game.cutscene.wait(500)
        self.game.sfx.set_heartbeat_bpm(80, volume=.15)
        yield from self.game.cutscene.say("finally...", self.game.player)
        yield from self.game.cutscene.wait(800)
        self.game.sfx.set_heartbeat_bpm(70, volume=.1)
        self.flags["bed_sleep_done"] = True
        self.flags["going_to_bed"] = False
        self.flags["sleeping"] = True

    def wake_up(self):
        self.flags['is_next_day'] = True
        self.game.sfx.start_heartbeat(bpm=70, volume=0.25)
        self.game.sfx.play_key("inf_laughter")
        self.game.sfx.play_key("xswl")
        yield from self.game.cutscene.wait(1000)
        yield from self.game.cutscene.say(["yaaaawwwwnnn", "what's all the fuzz in the morning?", "mom? are you here-?"], self.game.player)
        yield from self.game.cutscene.voice("horse_in_the_backyard")
        yield from self.game.cutscene.voice("groceries_groceries")
        self.game.sfx.set_heartbeat_bpm(80)
        yield from self.game.cutscene.voice("whats_wrong_with_you")
        yield from self.game.cutscene.voice("your_moms_not_here")
        yield from self.game.cutscene.say(["oh- right, sticky note", "guh...", "groceries-", "people-", "stress-"], self.game.player)
        yield from self.game.cutscene.cloudthink(["main street?", "what time should i leave?", "i hope i don't walk in circles", "what do i need to buy?"], self.game.player)
        # render hint 'Press [Tab] to see sticky note'
        # sticky note icon red dot notification and shakes
        # objective changed
        yield from self.game.cutscene.say(["wasn't it cereal and toilet paper rolls yesterday?", "did i see it wrongly?"], self.game.player)
        yield from self.game.cutscene.voice("your mom left the house already")
        # player wonders if it was the right objective
        # player checks sticky note
        # if sticky note read, guide player to the closet to change, press [E] to Change clothes
        # if self.flags['clothes_changed']: self.flags['ready_to_go']
        # time to go change!
        # to second_scene
        self.scene_ended = True

    """ player input"""
    def handle_input(self, dt):
        key = pygame.key.get_pressed()
        self.game.player_movement = [0, 0]
        if key[pygame.K_a]:
            self.game.player_movement[0] -= self.game.player_speed * dt
            self.game.player_facing = "left"

        if key[pygame.K_d]:
            self.game.player_movement[0] += self.game.player_speed * dt
            self.game.player_facing = "right"

        moving = self.game.player_movement[0] != 0
        if not self.flags["door_unlocked"] and not self.in_kitchen:
            max_x = 720 - self.game.player_w
            self.game.player.pos[0] = min(self.game.player.pos[0], max_x)

        if moving and not self.transitioning:
            surface = "tiles" if self.in_kitchen else "wood"
            self.game.sfx.play_footstep(surface)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            quit_type: bool = event.type == pygame.QUIT
            is_keydown: bool = event.type == pygame.KEYDOWN
            is_mbdown: bool = event.type == pygame.MOUSEBUTTONDOWN

            if quit_type: self.game.quit_game()

            if is_keydown: # only fires once, not for holding
                press_escape: bool = event.key == pygame.K_ESCAPE
                press_return: bool = event.key == pygame.K_RETURN
                press_interact: bool = event.key == pygame.K_e
                press_tab: bool = event.key == pygame.K_TAB

                if press_escape: self.game.pause_menu()
                if press_return: return "continue"
                if press_interact:
                    if self.is_near_bed() and not self.flags["going_to_bed"]:
                        self.flags["going_to_bed"] = True
                        self.game.cutscene.start(self.go_to_bed())
                        return None
                    
                    if self.game.player.rect().colliderect(self.fridge_rect.inflate(50, 50)):
                        opening = not self.flags["fridge_opened"]
                        self.flags["fridge_opened"] = opening
                        self.game.sfx.play_fridge(opened=opening)
                        self.flags["fridge_seen"] = True
                        self.flags["note_unlocked"] = True

                if press_tab:
                    if self.flags["read_sticky_note"] and not self.flags["sticky_note_complete"]:
                        self.flags["sticky_note_open"] = not self.flags["sticky_note_open"]
                
            if is_mbdown and event.button == 1:
                mx, my = self.get_mouse_pos()

                if self.flags["sticky_note_open"]:
                    if self.note_close_rect and self.note_close_rect.collidepoint(mx, my):
                        self.flags["sticky_note_open"] = False
                        return None

                    if self.note_rect and not self.note_rect.collidepoint(mx, my):
                        self.flags["sticky_note_open"] = False
                        return None

                if (
                    self.sticky_note_icon_rect
                    and self.sticky_note_icon_rect.collidepoint(mx, my)
                    and self.flags["read_sticky_note"]
                    and not self.flags["sticky_note_complete"]
                ):
                    self.flags["sticky_note_open"] = True
                    self.generate_sticky_note_lines()
                    return None
                
                note_quad = self.get_note_quad()
                screen_quad = [
                    (x - self.scroll_x, y)
                    for x, y in note_quad
                ]
                clicked_sticky_note = self.is_point_in_polygon((mx, my), screen_quad)
                if (
                    self.flags["note_unlocked"]
                    and clicked_sticky_note
                    and not self.flags["sticky_note_complete"]
                ):
                    if not self.flags["read_sticky_note"]:
                        self.flags["read_sticky_note"] = True
                        self.generate_sticky_note_lines()
                        self.flags["force_note_glow"] = False
                        self.flags["can_sleep"] = True

                    elif not self.flags["sticky_note_open"]:
                        self.generate_sticky_note_lines()

                    self.flags["sticky_note_open"] = True
                    return None
   

    """ rendering """
    def render_backgrounds(self, time_of_day="night"):
        if time_of_day == "night":
            self.render_night_backgrounds()
        else:
            self.render_day_backgrounds()

    def render_night_backgrounds(self) -> None:
        bedroom = pygame.transform.scale(self.bedroom_night_img, (self.game.internal_w, self.game.internal_h))
        kitchen_closed = pygame.transform.scale(self.kitchen_night_img, (self.game.internal_w, self.game.internal_h))
        kitchen_open = pygame.transform.scale(self.fridge_open_img, (self.game.internal_w, self.game.internal_h))

        self.game.display.blit(bedroom, (-self.scroll_x, 0))
        self.game.display.blit(kitchen_closed, (self.game.internal_w - self.scroll_x, 0))
        if self.fridge_transition_alpha > 0:
            overlay = kitchen_open.copy()
            overlay.set_alpha(int(self.fridge_transition_alpha))
            self.game.display.blit(overlay, (self.game.internal_w - self.scroll_x, 0))
    
    def render_day_backgrounds(self) -> None:
        internal_coord = (self.game_internal_w, self.game.internal_h)
        bedroom_day = pygame.transform.scale(self.bedroom_day_img, internal_coord)
        kitchen_day = pygame.transform.scale(self.kitchen_day_img, internal_coord)
        self.game.display.blit(bedroom_day, (-self.scroll_x, 0))
        self.game.display.blit(kitchen_day, (self.game.internal_w - self.scroll_x, 0))

    def render_fade(self, alpha) -> None:
        fade = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)
        fade.fill((0, 0, 0, int(alpha)))
        self.game.display.blit(fade, (0, 0))

    def render_glowing_quad(self, points: list[tuple[int, int]], alpha=51) -> None:
        self.glow.fill((0, 0, 0, 0))
        shifted = [
            (x - self.scroll_x, y)
            for x, y in points
        ]
        pulse = (math.sin(pygame.time.get_ticks() * 0.003) + 1) / 2
        pulse_alpha = int(alpha * (0.7 + pulse * 0.3))
        pygame.draw.polygon(self.glow,  (255, 255, 255, pulse_alpha), shifted, width=1)
        self.game.display.blit(self.glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def mouse_helper(self) -> tuple[int, int]:
        mx, my = self.get_mouse_pos()
        coord_text = self.game.heart_ui_font.render(
            f"{mx}, {my}",
            True,
            (255, 255, 255)
        )
        self.game.display.blit(coord_text, (50, 10))
        return mx, my         
     

    """ room transition """
    def render_transition_prompt(self, dt) -> None:
        if self.transitioning or not self.flags["door_unlocked"]: return
        lines = ["Kitchen", "->"] if not self.in_kitchen else ["Bedroom", "<-"]
        longest = max(lines, key=len)
        text_w = self.game.menu_font.text_width(longest)
        if not self.in_kitchen:
            x = self.game.internal_w - text_w - 40
        else:
            x = 40
        y = self.game.internal_h // 2 + 30
        for idx, line in enumerate(lines):
            self.game.menu_font.render(self.game.display, line, (x, y + idx * 18))
        
    def update_transition(self, dt) -> None:
        if not self.flags['door_unlocked']: return
        player_rect = self.game.player.rect()
        if not self.transitioning:
            if not self.in_kitchen and player_rect.colliderect(self.bedroom_to_kitchen_trigger):
                self.transitioning = True
                self.transition_direction = "to_kitchen"
                self.transition_start = pygame.time.get_ticks()
                self.game.player_movement = [0, 0]
                return

            if self.in_kitchen and player_rect.colliderect(self.kitchen_to_bedroom_trigger):
                self.transitioning = True
                self.transition_direction = "to_bedroom"
                self.transition_start = pygame.time.get_ticks()
                self.game.player_movement = [0, 0]
                return
            return

        elapsed = pygame.time.get_ticks() - self.transition_start
        if elapsed < self.transition_delay:
            self.game.player_movement = [0, 0]
            return

        if self.transition_direction == "to_kitchen":
            self.scroll_x += self.transition_speed * dt
            self.scroll_x = min(self.scroll_x, self.game.internal_w)

            if self.scroll_x >= self.game.internal_w:
                self.game.player.pos[0] = self.game.internal_w + 80
                self.transitioning = False
                self.in_kitchen = True

        elif self.transition_direction == "to_bedroom":
            self.scroll_x -= self.transition_speed * dt
            self.scroll_x = max(self.scroll_x, 0)

            if self.scroll_x <= 0:
                self.game.player.pos[0] = 620
                self.transitioning = False
                self.in_kitchen = False

        self.game.player_movement = [0, 0]

    
    """ fridge interaction """
    def is_near_open_fridge(self) -> bool:
        return self.game.player.rect().colliderect(self.fridge_rect.inflate(50, 50)) and self.flags["fridge_opened"]

    def update_fridge_transition(self, dt) -> None:
        target = 255 if self.flags["fridge_opened"] else 0
        if self.fridge_transition_alpha < target:
            self.fridge_transition_alpha = min(
                target,
                self.fridge_transition_alpha + self.fridge_transition_speed * dt
            )

        elif self.fridge_transition_alpha > target:
            self.fridge_transition_alpha = max(
                target,
                self.fridge_transition_alpha - self.fridge_transition_speed * dt
            )
      
    def render_fridge_interaction(self, dt) -> None:
        quad_1 = [(560, 136), (636, 128), (637, 444), (560, 412)]
        quad_2 = [(636, 128), (718, 129), (718, 432), (637, 444)]

        quad_1 = self.world_points(quad_1, self.kitchen_x)
        quad_2 = self.world_points(quad_2, self.kitchen_x)

        near_fridge = self.game.player.rect().colliderect(self.fridge_rect.inflate(50, 50))
        target_alpha = 255 if near_fridge and not self.flags["fridge_seen"] else 0
        fade_speed = 650 * dt

        if self.fridge_prompt_alpha < target_alpha:
            self.fridge_prompt_alpha = min(target_alpha, self.fridge_prompt_alpha + fade_speed)
        else:
            self.fridge_prompt_alpha = max(target_alpha, self.fridge_prompt_alpha - fade_speed)

        if self.fridge_prompt_alpha <= 0:
            return

        self.render_glowing_quad(quad_1, alpha=int(self.fridge_prompt_alpha * 0.15))
        self.render_glowing_quad(quad_2, alpha=int(self.fridge_prompt_alpha * 0.15))

        text = self.game.heart_ui_font.render("[E] to Interact", True, (255, 255, 255))
        text.set_alpha(int(self.fridge_prompt_alpha * 0.9))

        x, y = self.polygon_center(quad_1)
        self.game.display.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))
    

    """ milk interaction """
    def update_get_milk(self, dt):
        if self.flags["milk_taken"]: return
        holding_g = pygame.key.get_pressed()[pygame.K_g]
        can_get_milk = self.is_near_open_fridge()

        if not can_get_milk or not holding_g:
            self.flags["getting_milk"] = False
            self.get_milk_progress = max(0, self.get_milk_progress - 900 * dt)
            self.get_milk_started_sound = False
            return

        self.flags["getting_milk"] = True
        if not self.get_milk_started_sound:
            self.game.sfx.milk_cap(screwed_on=True)
            self.get_milk_started_sound = True

        self.get_milk_progress += 1000 * dt
        self.loading_angle = (self.loading_angle + 360 * dt) % 360
        if self.get_milk_progress >= self.get_milk_hold_time:
            self.finish_getting_milk()

    def finish_getting_milk(self):
        self.flags["getting_milk"] = False
        self.flags["milk_taken"] = True
        self.flags["milk_ready"] = True
        self.flags["holding_milk"] = True
        self.flags["drank_milk"] = False
        self.get_milk_progress = self.get_milk_hold_time
        self.game.sfx.milk_cap(screwed_on=False)
        self.game.sfx.play_key("glass_on_counter")
        self.game.sfx.play_key("pouring_milk")
        self.game.cutscene.start(self.get_milk())

    def render_get_milk_prompt(self, dt):
        if self.flags["milk_taken"]: return
        target_alpha = 255 if self.is_near_open_fridge() else 0
        fade_speed = 650 * dt
        if self.get_milk_prompt_alpha < target_alpha:
            self.get_milk_prompt_alpha = min(target_alpha, self.get_milk_prompt_alpha + fade_speed)
        else:
            self.get_milk_prompt_alpha = max(target_alpha, self.get_milk_prompt_alpha - fade_speed)

        if self.get_milk_prompt_alpha <= 0: return

        text = self.game.heart_ui_font.render("Hold [G] to get milk", True, (255, 255, 255))
        text.set_alpha(int(self.get_milk_prompt_alpha * 0.9))

        x, y = self.polygon_center(self.world_points([(560, 136), (636, 128), (637, 444), (560, 412)], self.kitchen_x))
        self.game.display.blit(text, (x - text.get_width() // 2, y + 35))

    def render_get_milk_loading(self):
        if not self.flags["getting_milk"]: return
        progress = max(0, min(1, self.get_milk_progress / self.get_milk_hold_time))
        rect = self.game.player.rect()
        cx = rect.centerx - self.scroll_x
        cy = rect.top - 34
        radius = 13
        pygame.draw.circle(self.game.display, (70, 70, 70), (cx, cy), radius, 2)
        start_angle = math.radians(-90)
        end_angle = math.radians(-90 - 360 * progress)
        arc_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        pygame.draw.arc(self.game.display, (255, 255, 255), arc_rect, start_angle, end_angle, 3)

    def render_milk_in_hand(self):
        if not self.flags["holding_milk"]: return
        rect = self.game.player.rect()
        x = rect.centerx - self.scroll_x + self.milk_hold_offset[0]
        y = rect.centery + self.milk_hold_offset[1]
        if self.game.player_facing == "left":
            x = rect.centerx - self.scroll_x - self.milk_hold_offset[0] - self.milk_in_hand_img.get_width()
        self.game.display.blit(self.milk_in_hand_img, (x, y))


    """ sticky note interaction """
    def get_note_quad(self) -> tuple[list[tuple[int, int]], int | float]:
        if self.flags["fridge_opened"]:
            return self.world_points(
                [(656, 193), (679, 198), (681, 237), (653, 236)],
                self.kitchen_x
            )
        return self.world_points(
            [(591, 192), (620, 193), (618, 236), (592, 231)],
            self.kitchen_x
        )

    def render_note_interaction(self):
        if not self.flags["note_unlocked"] or self.flags["read_sticky_note"]: return
        self.glow.fill((0, 0, 0, 0))
        note_quad = self.get_note_quad()
        screen_quad = [(x - self.scroll_x, y) for x, y in note_quad]
        mx, my = self.get_mouse_pos()
        if not self.flags["force_note_glow"] and not self.is_point_in_polygon((mx, my), screen_quad): return
        pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) / 2
        alpha = 45 + int(pulse * 30)
        pygame.draw.polygon(self.glow, (255, 245, 180, alpha), screen_quad)
        pygame.draw.polygon(self.glow, (255, 255, 255, 170), screen_quad, width=1)
        self.game.display.blit(self.glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def render_open_sticky_note(self) -> None:
        if not self.flags["sticky_note_open"]:
            self.note_rect = None
            self.note_close_rect = None
            return

        overlay = pygame.Surface(
            (self.game.internal_w, self.game.internal_h),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 120))
        self.game.display.blit(overlay, (0, 0))
        note_w = 360
        note_h = 220
        note_x = self.game.internal_w // 2 - note_w // 2
        note_y = self.game.internal_h // 2 - note_h // 2
        self.note_rect = pygame.Rect(note_x, note_y, note_w, note_h)
        pygame.draw.rect(
            self.game.display,
            (255, 245, 180),
            self.note_rect,
            border_radius=4
        )
        pygame.draw.rect(
            self.game.display,
            (80, 70, 40),
            self.note_rect,
            width=2,
            border_radius=4
        )
        close_text = "X"
        close_surf = self.sticky_note_font.render(
            close_text,
            True,
            (40, 30, 20)
        )

        close_x = self.note_rect.right - 26
        close_y = self.note_rect.top + 10

        self.note_close_rect = pygame.Rect(
            close_x - 4,
            close_y - 2,
            24,
            24
        )

        self.game.display.blit(close_surf, (close_x, close_y))
        if self.current_sticky_note_lines is None:
            self.generate_sticky_note_lines()

        lines = self.current_sticky_note_lines

        line_spacing = 28
        total_height = len(lines) * line_spacing

        start_y = self.note_rect.centery - total_height // 2 + 8

        for idx, line in enumerate(lines):
            if not line: continue
            text_surf = self.sticky_note_font.render(
                line,
                True,
                (40, 30, 20)
            )
            text_x = self.note_rect.centerx - text_surf.get_width() // 2
            text_y = start_y + idx * line_spacing
            self.game.display.blit(text_surf, (text_x, text_y))
        
    def is_point_in_polygon(self, point, polygon):
        x, y = point
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1) + xi:
                inside = not inside
            j = i
        return inside

    def generate_sticky_note_lines(self):
        choice1 = random.choice(self.groceries_task)
        choice2 = random.choice([
            food for food in self.groceries_task
            if food != choice1
        ])

        self.current_sticky_note_lines = [
            "Do you mind going for groceries?",
            "",
            f"We're out of {choice1} and {choice2},",
            "and... I'm pretty busy tomorrow.",
            "",
            "                           -- Mom"
        ]
        
    def render_sticky_note_icon(self):
        if not self.flags["read_sticky_note"]: return
        if self.flags["sticky_note_complete"]: return
        icon = pygame.transform.scale(self.sticky_note_img, (38, 38))
        x = self.game.internal_w - 55
        y = 60

        if self.flags["force_note_glow"]:
            shake = int(math.sin(pygame.time.get_ticks() * 0.04) * 2)
            x += shake

        self.game.display.blit(icon, (x, y))
        if self.flags["read_sticky_note"] and not self.flags["sticky_note_open"]:
            pygame.draw.circle(
                self.game.display,
                (220, 45, 45),
                (x + 32, y + 6),
                5
            )
        self.sticky_note_icon_rect = pygame.Rect(x, y, 38, 38)
        
    """ bed interaction """
    def get_bed_quad(self) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
        quad1 = [(88, 307), (162, 316), (166, 435), (85, 435)]
        quad2 = [(162, 316), (255, 356), (237, 435), (166, 435)]
        return ( self.world_points(quad1), self.world_points(quad2) )
    
    def is_near_bed(self):
        if self.in_kitchen: return False
        if not self.flags["holding_milk"]: return False
        if not self.flags["read_sticky_note"]: return False
        if self.flags["bed_sleep_done"]: return False

        player_rect = self.game.player.rect()
        quad1, quad2 = self.get_bed_quad()
        points = [
            player_rect.midbottom,
            player_rect.center,
            player_rect.midleft,
            player_rect.midright,
        ]
        return (
            any(self.is_point_in_polygon(point, quad1) for point in points)
            or any(self.is_point_in_polygon(point, quad2) for point in points)
        )

    def render_bed_sleep_prompt(self, dt):
        target_alpha = 255 if self.is_near_bed() else 0
        fade_speed = 650 * dt
        if self.bed_prompt_alpha < target_alpha:
            self.bed_prompt_alpha = min(target_alpha, self.bed_prompt_alpha + fade_speed)
        else:
            self.bed_prompt_alpha = max(target_alpha, self.bed_prompt_alpha - fade_speed)

        if self.bed_prompt_alpha <= 0: return
        text = self.game.heart_ui_font.render("Press [E] to sleep", True, (255, 255, 255))
        text.set_alpha(int(self.bed_prompt_alpha * 0.9))
        x = self.bed_rect.centerx - self.scroll_x
        y = self.bed_rect.top - 24
        self.game.display.blit(text, (x - text.get_width() // 2, y))


    """ digital clock """
    def render_clock(self):
        if self.in_kitchen or self.transitioning: return
        clock_font = pygame.font.Font("assets/fonts/Minecraftia-Regular.ttf", 10)
        clock_color = (57, 255, 20)
        clock_start_time = datetime.strptime("02:41", "%H:%M")
        elapsed_ms = pygame.time.get_ticks() - self.clock_begin_ticks
        current_time = clock_start_time + timedelta(milliseconds=elapsed_ms)
        clock_text = current_time.strftime("%I:%M")
        text_surf = clock_font.render(clock_text, True, clock_color)
        self.game.display.blit(text_surf, (21, 335))