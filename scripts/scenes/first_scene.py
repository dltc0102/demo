import pygame, math, random
from typing import *
from datetime import datetime, timedelta

from scripts.core.utils import load_image
from scripts.ui.font import Font
from scripts.core.interact import InteractZone

class FirstScene:
    """ setup """
    def __init__(self, game):
        self.game = game
        self.scene_ended: bool = False
        self.script = self.game.cutscene
        self.glow = pygame.Surface((self.game.internal_w, self.game.internal_h), pygame.SRCALPHA)

        self.asset_paths: dict[str, str] = {
            'bedroom_night'     : 'assets/backgrounds/bedroom_night.png',
            'kitchen_night'     : 'assets/backgrounds/kitchen_night.png',
            'fridge_open'       : 'assets/backgrounds/kitchen_night_fridge_open.png',
            'milk_img'          : 'assets/entities/glass_of_milk.png',
            'sticky_note_img'   : 'assets/entities/sticky_note.png',
            'bedroom_day'       : 'assets/backgrounds/bedroom_day.png',
            'kitchen_day'       : 'assets/backgrounds/kitchen_day.png',
            'outside_home': 'assets/backgrounds/outside_home.png',
        }

        for path in self.asset_paths.values():
            self.game.live.watch(path)

        self.bedroom_night_img, *_  = load_image(self.asset_paths['bedroom_night'])
        self.kitchen_night_img, *_  = load_image(self.asset_paths['kitchen_night'])
        self.fridge_open_img, *_    = load_image(self.asset_paths['fridge_open'])
        self.milk_img, *_           = load_image(self.asset_paths['milk_img'])
        self.sticky_note_img, *_    = load_image(self.asset_paths['sticky_note_img'])
        self.bedroom_day_img, *_    = load_image(self.asset_paths['bedroom_day'])
        self.kitchen_day_img, *_    = load_image(self.asset_paths['kitchen_day'])
        self.outside_home_img, *_   = load_image(self.asset_paths['outside_home'])
        self.exit_house_trigger = pygame.Rect(self.game.internal_w * 2 - 8, 300, 8, 128)

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
            "show_bedroom_pulse"    : False,
            "show_exit_pulse"       : False,
            "sticky_note_open_count": 0,
            "shake_prompt_shown"    : False,
            "shake_note_prompt_shown": False,
            "bed_sleep_done"        : False,
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
        self.fridge_transition_alpha    = 0
        self.fridge_transition_speed    = 650

        self.fridge_zone = InteractZone(
            points=[
                (self.kitchen_x + 560, 136),
                (self.kitchen_x + 718, 129),
                (self.kitchen_x + 718, 432),
                (self.kitchen_x + 636, 444),
                (self.kitchen_x + 560, 412),
            ],
            prompt="[E] to Interact",
            font=self.game.heart_ui_font,
            glow_surf=self.glow,
        )
        

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
        self.end_fade_alpha: float = 0
        self.end_fade_speed: int = 180
        self.wake_up_started: bool = False


        """ sticky note """
        self.sticky_note_font = pygame.font.Font("assets/fonts/Retrogression-Regular.ttf", 25)
        self.menu_font = Font("assets/fonts/large_font_white.png", scale=1)
        self.current_sticky_note_lines = None
        self.groceries_task = ["cereal", "fruits", "vegetables", "milk", "toilet rolls"]
        self.sticky_note_icon_rect = None
        self.note_rect: pygame.Rect | None = None
        self.note_close_rect: pygame.Rect | None = None

        """ closet """
        self.closet_rect = pygame.Rect(557, 294, 147, 122)
        self.closet_zone = InteractZone(
            points=[(557, 294), (704, 294), (704, 416), (557, 416)],
            prompt="Press [E] to change",
            font=self.game.heart_ui_font,
            glow_surf=self.glow,
        )

        """ digital clock """
        self.clock_begin_ticks = pygame.time.get_ticks()

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
        self.bedroom_day_img, *_ = load_image(self.asset_paths["bedroom_day"])
        self.kitchen_day_img, *_ = load_image(self.asset_paths["kitchen_day"])
        self.outside_home_img, *_ = load_image(self.asset_paths["outside_home"])
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
        self.end_fade_alpha = 0
        self.wake_up_started = False
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
            if self.flags["door_unlocked"]: 
                self.render_transition_prompt(dt)
            self.render_fridge_interaction(dt)
            self.render_get_milk_prompt(dt)
            self.render_get_milk_loading()
            self.render_bed_sleep_prompt(dt)
            if self.flags["is_next_day"]:
                self.closet_zone.update(dt, self.game.player.rect(), self.scroll_x)
                self.closet_zone.render(self.game.display, self.scroll_x)
            self.render_note_interaction()
            self.render_glow_prompt()
            self.render_sticky_note_icon()
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
            self.game.render_sfx_heartbeat_ui()

            self.game.thought_manager.render(self.game.display, offset=(self.scroll_x, 0))
            self.game.dialogue_manager.render(self.game.display, offset=(self.scroll_x, 0))

            self.render_open_sticky_note()
            self.game.handle_pause_button()
            result = self.handle_events()
            if result: 
                return result
            
            if self.scene_ended:
                return "route_choice"

            if self.fade_alpha > 0:
                self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
                self.render_fade(self.fade_alpha)

            if self.flags["sleeping"]:
                self.end_fade_alpha = min(255, self.end_fade_alpha + self.end_fade_speed * dt)
                self.render_fade(self.end_fade_alpha)

                if self.end_fade_alpha >= 255 and not self.wake_up_started:
                    self.wake_up_started = True
                    self.flags["sleeping"] = False
                    self.end_fade_alpha = 0
                    self.fade_alpha = 255
                    self.game.cutscene.start(self.wake_up())

            self.game.scale_display_to_screen()
            pygame.display.update()
            self.game.clock.tick(self.game.fps)


    """ story scripts """
    def sequence(self):
        self.game.sfx.start_static()
        self.game.sfx.start_whispers()
        yield from self.script.wait(1000)
        self.game.start_heartbeat(bpm=70, volume=1)
        yield from self.script.say(["ugh... I can't sleep", "again"], self.game.player)
        yield from self.script.say("I just want one quiet night.", self.game.player, interval=20)
        yield from self.script.racethink(
            ["was that outside?", "no, inside", "ignore it", "don't answer"],
            self.game.player
        )
        yield from self.script.wait(1000)
        yield from self.script.say(
            ["why am i still awake?", "did i hear something?", "no seriously"], 
            self.game.player
        )
        yield from self.script.wait(500)
        self.game.set_heartbeat_bpm(80)
        yield from self.script.shakethink("why me?!", self.game.player)
        yield from self.script.say(
            ["who- what?", "who's laughing?", "i don't know why...", "but they keep me up at night", "why me"],
            self.game.player
        )
        self.game.set_heartbeat_bpm(70)
        yield from self.script.cloudthink(
            ["...a bit thirsty...", "what to drink?", "maybe milk?", "or ice cold water?", "can of coke?", "no, sleep first"], 
            self.game.player, stall=2000
        )
        yield from self.script.wait(500)
        yield from self.script.play_voice("glass_of_milk")
        yield from self.script.wait(1500)
        self.game.set_heartbeat_bpm(80)
        yield from self.script.say(
            ["who- who's there?", "how can you hear what i'm thinking???"], 
            self.game.player
        )
        yield from self.script.racethink("what's going on", self.game.player)
        self.game.set_heartbeat_bpm(90, volume=0.35)
        yield from self.script.say(
            ["huh? I'm-", "im not", "i can't help it", "they stress me out"], 
            self.game.player
        )
        yield from self.script.wait(1000)
        yield from self.script.say(
            ["hello-?", "they don't respond to what I say", "they just talk whenever they want to", "i cant- control them"], 
            self.game.player
        )
        self.game.set_heartbeat_bpm(70, volume=0.2)
        self.flags["door_unlocked"] = True

    def get_milk(self):
        if not self.in_kitchen and not self.flags['fridge_opened']: return
        yield from self.script.wait(1000)
        self.game.set_heartbeat_bpm(70)
        yield from self.script.play_voice("dont_touch_that")
        yield from self.script.play_voice("do_it_again")
        yield from self.script.shakethink(["one thing at a time", "i can do this"], self.game.player)
        yield from self.script.play_voice("do_it_again_hale")
        yield from self.script.play_voice("theyre_all_looking_at_you")
        yield from self.script.play_voice("do_it_again_janelle")
        yield from self.script.shakethink(["you're the only one here", "just you"], self.game.player)
        yield from self.panicked_breathing_ramp()
        yield from self.script.cloudthink(
            ["this is milk right?", "check the label", "why am I checking again?"],
            self.game.player
        ).overlap_with("check_again")
        yield from self.script.play_voice("youre_like_a_turtle_with_instructions")
        yield from self.script.racethink(
            ["didn't I just drink some?", "no", "maybe", "what was I doing?"],
            self.game.player
        ).overlap_with("you_already_did_this", "nah_you_didnt")
        yield from self.script.play_voice("liar_liar")
        yield from self.script.cloudthink(
            ["something's wrong", "is this safe?", "it's just milk", "then why does it feel wrong?"],
            self.game.player
        ).overlap_with("just_trust_me")
        yield from self.script.play_voice("hes_opening_the_fridge_again")
        self.game.set_heartbeat_bpm(100, volume=.3)
        yield from self.script.shakethink(["breathe", "this feeling will pass"], self.game.player)
        yield from self.script.play_voice("dont_trust_him")
        yield from self.script.wait(500)
        yield from self.script.play_voice("drink_it").overlap_with("why_are_you_still_drinking_it")
        yield from self.script.play_voice("i_think_your_lamp_has_opinions").overlap_with("dont_trust_them")
        yield from self.script.play_voice("dont_answer")
        yield from self.script.wait(1000)
        self.script.play_voice("schizophrenia_voices")
        yield from self.script.say(["i can't tell what's real and what's not", "it's driving me nuts", "i'd love to be able to silence them", "all of them", "it's not easy", "i can't just ignore them either"], self.game.player)
        yield from self.script.shakethink("it's not easy at all", self.game.player)
        yield from self.script.shakethink("it's not as simple as you think", self.game.player)
        yield from self.script.wait(1000)
        self.game.set_heartbeat_bpm(120, volume=.4)
        yield from self.script.play_voice("dont_touch_that").overlap_with("look_behind_you")
        yield from self.script.shakethink("ahhh", self.game.player)
        self.game.set_heartbeat_bpm(120, volume=.55)
        yield from self.script.play_voice("theyre_watching")
        self.script.play_voice("what_are_you_doing")
        yield from self.script.say(["i haven't had a good sleep since foreever", "i- i'm going back to sleep", "did I drink milk yet?", "did mom already buy the groceries?", "wait..."], self.game.player)
        yield from self.script.shakethink(["pills", "where are my pills?!"], self.game.player)
        self.game.sfx.play_key("pill_bottle")
        self.script.play_voice("why_are_you_so_slow")
        yield from self.script.cloudthink(["need sleep", "can't trust my memory", "why can't i do simple things?", "this doesn't feel real", "was that glass of milk always there?", "am i dreaming?", "normal people can do this"], self.game.player)
        yield from self.script.play_voice("nizenmehaimeishuine")
        self.game.set_heartbeat_bpm(110, volume=.3)

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
            yield from self.script.wait(500)

        self.game.set_heartbeat_bpm(90, volume=.25)
        self.game.sfx.play_key("glass_on_table")
        yield from self.script.wait(450)

        self.game.sfx.play_footstep("wood")
        yield from self.script.wait(320)
        self.game.sfx.play_footstep("wood")
        yield from self.script.wait(500)
        self.game.set_heartbeat_bpm(80, volume=.15)
        yield from self.script.say("finally...", self.game.player)
        self.script.play_voice("took_you_long_enough")
        yield from self.script.wait(800)
        self.game.set_heartbeat_bpm(70, volume=.1)
        self.flags["bed_sleep_done"] = True
        self.flags["going_to_bed"] = False
        self.end_fade_alpha = 0
        self.wake_up_started = False
        self.flags["sleeping"] = True
        self.flags["sticky_note_open_count"] = 0

    def wake_up(self):
        self.flags['is_next_day'] = True
        self.game.start_heartbeat(bpm=70, volume=0.25)
        self.game.sfx.play_key("inf_laughter")
        self.game.sfx.play_key("xswl")
        yield from self.script.wait(1000)
        yield from self.script.say(["yaaaawwwwnnn", "what's all the fuzz in the morning?", "mom? are you here-?"], self.game.player)
        yield from self.script.play_voice("horse_in_the_backyard").overlap_with("groceries_groceries")
        self.game.set_heartbeat_bpm(80)
        yield from self.script.play_voice("whats_wrong_with_you")
        yield from self.script.play_voice("your_moms_not_here")
        yield from self.script.say(["oh- right, sticky note", "guh...", "groceries-", "people-", "stress-"], self.game.player)
        yield from self.script.cloudthink(["main street?", "what time should i leave?", "i hope i don't walk in circles", "what do i need to buy?"], self.game.player)
        yield from self.script.say(["wasn't it cereal and toilet paper rolls yesterday?", "did i see it wrongly?"], self.game.player)
        yield from self.script.play_voice("your_mom_left_the_house_already")
        if self.flags["read_sticky_note"]:
            self.flags["show_bedroom_pulse"] = True
            yield from self.script.say("I should check that note again before I go.", self.game.player)
            self.flags["shake_note_prompt_shown"] = True
            yield from self.script.shakethink("check the sticky note", self.game.player)
        else:
            yield from self.script.say("...I should get changed.", self.game.player)

        while not self.flags["clothes_changed"]: yield

    def change_clothes(self):
        yield from self.script.say(
            ["my body feels heavy", "getting dressed shouldn't feel this hard"],
            self.game.player
        )
        yield from self.script.play_voice("get_dressed_now")
        yield from self.script.play_voice("why_are_you_taking_so_long")
        self.game.player.set_outfit("back")
        yield from self.script.wait(400)
        self.script.play_voice("undress")
        yield from self.script.wait(800)
        self.script.play_voice("belt")
        yield from self.script.wait(600)
        self.script.play_voice("dress")
        yield from self.script.wait(900)
        self.game.player.set_outfit("outdoors")
        yield from self.script.play_voice("took_you_long_enough")
        yield from self.script.wait(400)
        yield from self.script.say("okay... jacket, cap, ready.", self.game.player)
        yield from self.script.wait(600)
        yield from self.script.racethink(["wait, am i sure?", "jacket", "cap", "do i have enough money?"], self.game.player)
        self.game.sfx.play_key("page_flip")
        yield from self.script.say(["i have enough", "i forgot what i need to buy", "what do i need to buy again?"], self.game.player)
        yield from self.script.shakethink("check the sticky note", self.game.player)
        self.game.set_heartbeat_bpm(90)
        yield from self.script.say(["did the note change?", "it changed", "got keys", "got my bag", "jacket", "cap"], self.game.player)
        yield from self.script.cloudthink(
            ["main street is faster", "too many people", "quiet route is longer", "what if I get lost?", "just choose"],
            self.game.player
        )

        self.flags["clothes_changed"] = True
        self.flags["ready_to_go"] = True
        self.flags["show_bedroom_pulse"] = False
        self.flags["show_exit_pulse"] = True
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
            if self.game.handle_dev_keys(event): continue
            if is_keydown: # only fires once, not for holding
                press_escape: bool = event.key == pygame.K_ESCAPE
                press_return: bool = event.key == pygame.K_RETURN
                press_interact: bool = event.key == pygame.K_e
                press_tab: bool = event.key == pygame.K_TAB

                if press_escape:
                    pause_result: str = self.game.pause_menu()
                    if pause_result == "menu": return "menu"
                if press_return: return "continue"
                if press_interact:
                    if self.closet_zone.is_visible and self.flags["is_next_day"]:
                        self.flags["clothes_changed"] = True
                    if self.flags["is_next_day"] and not self.flags["clothes_changed"]:
                        if self.game.player.rect().colliderect(self.closet_rect):
                            self.flags["clothes_changed"] = True
                            self.flags["show_bedroom_pulse"] = False
                            self.flags["ready_to_go"] = True
                            self.game.cutscene.start(self.change_clothes())
                            
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
                        opening = not self.flags["sticky_note_open"]
                        self.flags["sticky_note_open"] = not self.flags["sticky_note_open"]
                        if opening: self.game.sfx.play_key("page_flip")
            
            if is_mbdown:
                if (
                    self.flags["ready_to_go"]
                    and self.in_kitchen
                    and self.game.player.rect().colliderect(
                        self.exit_house_trigger.move(-self.scroll_x, 0)
                    )
                ):
                    self.scene_ended = True

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
                    self.game.sfx.play_key("page_flip")
                    if self.flags["is_next_day"] and self.flags["shake_note_prompt_shown"]:
                        self.flags["sticky_note_open_count"] += 1
                        self.flags["shake_note_prompt_shown"] = False
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
                    self.game.sfx.play_key("page_flip")
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
    
    def render_day_backgrounds(self):
        bedroom = pygame.transform.scale(self.bedroom_day_img, (self.game.internal_w, self.game.internal_h))
        kitchen = pygame.transform.scale(self.kitchen_day_img, (self.game.internal_w, self.game.internal_h))
        outside = pygame.transform.scale(self.outside_home_img, (self.game.internal_w, self.game.internal_h))

        self.game.display.blit(bedroom, (-self.scroll_x, 0))
        self.game.display.blit(kitchen, (self.game.internal_w - self.scroll_x, 0))
        self.game.display.blit(outside, (self.game.internal_w * 2 - self.scroll_x, 0))

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
    
    def render_glow_prompt(self) -> None:
        if self.transitioning: return

        if self.flags.get("show_exit_pulse") and self.in_kitchen:
            self.render_glowing_text("Exit house ->", (self.game.internal_w - 170, self.exit_house_trigger.centery), color=(180, 255, 190))
            return

        if self.in_kitchen:
            self.render_glowing_text("Bedroom <-", (40, self.kitchen_to_bedroom_trigger.centery), color=(255, 245, 180))
            return

        if self.flags.get("door_unlocked") or self.flags.get("show_exit_pulse") or self.flags.get("show_bedroom_pulse"):
            self.render_glowing_text("Kitchen ->", (self.game.internal_w - 170, self.bedroom_to_kitchen_trigger.centery), color=(255, 245, 180))

    def render_glowing_text(self, text: str, pos: tuple[int, int], color=(255, 245, 180)) -> None:
        pulse = (math.sin(pygame.time.get_ticks() * 0.004) + 1) / 2
        alpha = int(90 + pulse * 120)

        x, y = pos
        font = self.game.heart_ui_font
        text_surf = font.render(text, True, color)
        text_surf.set_alpha(alpha)

        glow_surf = font.render(text, True, color)
        glow_surf.set_alpha(int(alpha * 0.35))

        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            self.game.display.blit(glow_surf, (x + ox, y + oy))

        self.game.display.blit(text_surf, (x, y))
        
    def render_sfx_heartbeat_ui(self) -> None:
        if not getattr(self.sfx, "heartbeat_active", False): return
        bpm = int(self.sfx.heartbeat_bpm)
        pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) / 2
        icon_size = int(16 * (1 + pulse * 0.18))
        icon = pygame.transform.scale(self.heart_icon, (icon_size, icon_size))
        text_surf = self.heart_ui_font.render(str(bpm), True, (255, 255, 255))
        total_width = icon.get_width() + 6 + text_surf.get_width()
        x = self.internal_w // 2 - total_width // 2
        y = 14
        self.display.blit(icon, (x, y))
        self.display.blit(text_surf, (x + icon.get_width() + 6, y - 1))
            

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
        self.update_fridge_transition(dt)
        if self.flags["fridge_seen"]: return
        self.fridge_zone.update(dt, self.game.player.rect(), self.scroll_x)
        self.fridge_zone.render(self.game.display, self.scroll_x)
    

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

        if self.flags["is_next_day"]:
            clock_text = "10:30"
        else:
            clock_start_time = datetime.strptime("02:41", "%H:%M")
            elapsed_ms = pygame.time.get_ticks() - self.clock_begin_ticks
            current_time = clock_start_time + timedelta(milliseconds=elapsed_ms)
            clock_text = current_time.strftime("%I:%M")

        text_surf = clock_font.render(clock_text, True, clock_color)
        self.game.display.blit(text_surf, (21, 335))

    """ audio helpers """
    def panicked_breathing_ramp(self):
        self.game.sfx.play_key("male_panicked_breathing", volume=0.65)
        self.game.set_heartbeat_bpm(90, volume=.3)
        yield from self.script.wait(700)
        self.game.set_heartbeat_bpm(100, volume=.35)
        yield from self.script.wait(700)
        self.game.set_heartbeat_bpm(110, volume=.45)
        yield from self.script.wait(700)
        self.game.set_heartbeat_bpm(120, volume=.55)
        yield from self.script.wait(900)
        