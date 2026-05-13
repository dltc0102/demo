import pygame
from scripts.ui.font import Font
from paths import asset

class MomDialogueChoice:
    def __init__(self, game, text, choices, mom):
        self.game = game
        self.text = text
        self.choices = choices
        self.mom = mom
        self.font = Font(asset("assets/fonts/large_font_white.png"), scale=1)
        self.choice_font = Font(asset("assets/fonts/large_font_white.png"), scale=1)
        
        self.visible_chars = 0
        self.char_timer = 0
        self.char_delay = 28
        self.text_finished = False
        self.selected_choice = None
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 400
        
        self.choice_buttons = []
        self.hovered_choice = None
        
        mom_width = 91
        self.dialogue_box_x = 20 + mom_width + 15
        self.dialogue_box_y = self.game.internal_h - 150
        self.dialogue_box_width = self.game.internal_w - self.dialogue_box_x - 20
        self.dialogue_box_height = 130
        
    def is_finished(self):
        return self.selected_choice is not None
        
    def update(self, dt):
        if self.alpha < self.target_alpha:
            self.alpha = min(self.target_alpha, self.alpha + self.fade_speed * dt)
        
        if not self.text_finished:
            self.char_timer += dt * 1000
            if self.char_timer >= self.char_delay:
                self.char_timer = 0
                self.visible_chars += 1
                if self.visible_chars >= len(self.text):
                    self.visible_chars = len(self.text)
                    self.text_finished = True
                    self.build_choice_buttons()
        
        mx, my = self.get_mouse_pos()
        self.hovered_choice = None
        for i, rect in enumerate(self.choice_buttons):
            if rect.collidepoint(mx, my):
                self.hovered_choice = i
                break
                
    def handle_click(self, mx, my):
        if not self.text_finished:
            return None
        for i, rect in enumerate(self.choice_buttons):
            if rect.collidepoint(mx, my):
                self.selected_choice = i
                return self.choices[i]
        return None
        
    def get_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        return int(mx / self.game.scale_x), int(my / self.game.scale_y)
        
    def build_choice_buttons(self):
        self.choice_buttons = []
        
        button_spacing = 8
        button_height = 45
        start_y = self.dialogue_box_y + 55
        
        available_width = self.dialogue_box_width - 30
        button_width = (available_width - button_spacing * 2) // 3
        start_x = self.dialogue_box_x + 15
        
        for i in range(len(self.choices)):
            button_x = start_x + i * (button_width + button_spacing)
            self.choice_buttons.append(pygame.Rect(button_x, start_y, button_width, button_height))
            
    def render(self, surface):
        if self.alpha <= 0:
            return
        
        alpha_val = int(self.alpha)
        
        box_surf = pygame.Surface((self.dialogue_box_width, self.dialogue_box_height), pygame.SRCALPHA)
        box_surf.fill((20, 18, 22, int(230 * (alpha_val / 255))))
        pygame.draw.rect(box_surf, (180, 175, 185, int(200 * (alpha_val / 255))), (0, 0, self.dialogue_box_width, self.dialogue_box_height), 3)
        surface.blit(box_surf, (self.dialogue_box_x, self.dialogue_box_y))
        
        visible_text = self.text[:self.visible_chars]
        
        wrapped_lines = []
        max_text_width = self.dialogue_box_width - 30
        words = visible_text.split(' ')
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if self.font.text_width(test_line) > max_text_width and current_line:
                wrapped_lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line = test_line
        if current_line:
            wrapped_lines.append(current_line.strip())
        
        text_x = self.dialogue_box_x + 15
        text_y = self.dialogue_box_y + 12
        
        if alpha_val < 255:
            text_surf = pygame.Surface((self.dialogue_box_width - 30, 20 * len(wrapped_lines)), pygame.SRCALPHA)
            for line in wrapped_lines:
                self.font.render(text_surf, line, (0, text_y - self.dialogue_box_y - 12))
                text_y += 18
            text_surf.set_alpha(alpha_val)
            surface.blit(text_surf, (text_x, self.dialogue_box_y + 12))
        else:
            for line in wrapped_lines:
                self.font.render(surface, line, (text_x, text_y))
                text_y += 18
        
        if self.text_finished:
            for i, (choice, rect) in enumerate(zip(self.choices, self.choice_buttons)):
                is_hovered = i == self.hovered_choice
                bg_color = (60, 55, 65, int(240 * (alpha_val / 255))) if is_hovered else (35, 32, 38, int(220 * (alpha_val / 255)))
                border_color = (200, 195, 205, int(200 * (alpha_val / 255))) if is_hovered else (150, 145, 155, int(180 * (alpha_val / 255)))
                
                button_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                button_surf.fill(bg_color)
                pygame.draw.rect(button_surf, border_color, (0, 0, rect.width, rect.height), 2)
                surface.blit(button_surf, (rect.x, rect.y))
                
                choice_wrapped = []
                choice_words = choice.split(' ')
                choice_line = ""
                max_choice_width = rect.width - 16
                
                for word in choice_words:
                    test = choice_line + word + " "
                    if self.choice_font.text_width(test) > max_choice_width and choice_line:
                        choice_wrapped.append(choice_line.strip())
                        choice_line = word + " "
                    else:
                        choice_line = test
                if choice_line:
                    choice_wrapped.append(choice_line.strip())
                
                choice_y = rect.y + 8
                for choice_text_line in choice_wrapped:
                    if alpha_val < 255:
                        line_surf = pygame.Surface((rect.width - 16, 15), pygame.SRCALPHA)
                        self.choice_font.render(line_surf, choice_text_line, (0, 0))
                        line_surf.set_alpha(alpha_val)
                        surface.blit(line_surf, (rect.x + 8, choice_y))
                    else:
                        self.choice_font.render(surface, choice_text_line, (rect.x + 8, choice_y))
                    choice_y += 14


class MomDialogueTree:
    def __init__(self):
        self.conversations = {
            "greeting": {
                "question": "How was your day today?",
                "choices": [
                    "It was fine, mom",
                    "Not great...",
                    "I don't want to talk about it"
                ],
                "responses": {
                    0: "That's good to hear, honey",
                    1: "Do you want to talk about it?",
                    2: "Okay, whenever you're ready"
                }
            },
            "what_doing": {
                "question": "What are you doing?",
                "choices": [
                    "Just trying to get some milk",
                    "Nothing much",
                    "None of your business"
                ],
                "responses": {
                    0: "Don't forget to check the date on it",
                    1: "Alright, don't stay up too late",
                    2: "Watch your tone with me"
                }
            },
            "glasses_warning": {
                "question": "Don't break my glasses",
                "choices": [
                    "I won't, mom",
                    "I'll be careful",
                    "Stop worrying"
                ],
                "responses": {
                    0: "Good, they're expensive",
                    1: "Thank you, sweetie",
                    2: "I'm your mother, I'll worry if I want to"
                }
            },
            "check_note": {
                "question": "Check the sticky note",
                "choices": [
                    "Yes mom, I'll buy the groceries tomorrow",
                    "Don't tell me what to do",
                    "I already saw it"
                ],
                "responses": {
                    0: "Thank you, honey. I really need those",
                    1: "I'm trying to help you remember",
                    2: "Good, just making sure"
                }
            },
            "goodnight": {
                "question": "Good night, honey",
                "choices": [
                    "Good night, mom",
                    "Yeah, whatever",
                    "Thanks"
                ],
                "responses": {
                    0: "Sleep well, sweetie",
                    1: "Love you too",
                    2: "Sweet dreams"
                }
            }
        }
        
    def get_conversation(self, scene_flags):
        if not scene_flags.get("read_sticky_note"):
            return "check_note"
        return "greeting"
    
    def get_conversation_sequence(self, scene_flags):
        conversations = []
        if not scene_flags.get("read_sticky_note"):
            conversations.append("check_note")
        else:
            conversations.append("greeting")
        conversations.append("what_doing")
        conversations.append("goodnight")
        return conversations