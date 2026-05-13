import pygame, math
from scripts.core.utils import load_image
from paths import asset

class Mom:
    def __init__(self, game, pos):
        self.game = game
        self.pos = list(pos)
        self.alpha = 0
        self.target_alpha = 0
        self.fade_speed = 150
        self.visible = False
        self.speaking = False
        self.mouth_open_amount = 0
        self.mouth_animation_time = 0
        
        self.mom_img, *_ = load_image(asset("assets/entities/mom.png"))
        self.width = self.mom_img.get_width()
        self.height = self.mom_img.get_height()
        
    def fade_in(self):
        self.visible = True
        self.target_alpha = 255
        
    def fade_out(self):
        self.target_alpha = 0
        
    def set_speaking(self, speaking):
        self.speaking = speaking
        if not speaking:
            self.mouth_animation_time = 0
    
    def rect(self):
        return pygame.Rect(int(self.pos[0]), int(self.pos[1]), self.width, self.height)
        
    def update(self, dt):
        if self.alpha < self.target_alpha:
            self.alpha = min(self.target_alpha, self.alpha + self.fade_speed * dt)
        elif self.alpha > self.target_alpha:
            self.alpha = max(self.target_alpha, self.alpha - self.fade_speed * dt)
            if self.alpha <= 0:
                self.visible = False
        
        if self.speaking:
            self.mouth_animation_time += dt * 12
            self.mouth_open_amount = abs(math.sin(self.mouth_animation_time)) * 0.6
        else:
            self.mouth_open_amount = max(0, self.mouth_open_amount - dt * 4)
            
    def render(self, surface, offset=(0, 0)):
        if self.alpha <= 0 or not self.visible:
            return
            
        x = int(self.pos[0] - offset[0])
        y = int(self.pos[1] - offset[1])
        
        mom_surf = self.mom_img.copy()
        mom_surf.set_alpha(int(self.alpha))
        
        surface.blit(mom_surf, (x, y))
        
        if self.mouth_open_amount > 0.1:
            mouth_height = int(6 * self.mouth_open_amount)
            mouth_color = (30, 25, 28, int(self.alpha * 0.8))
            mouth_surf = pygame.Surface((14, mouth_height), pygame.SRCALPHA)
            mouth_surf.fill(mouth_color)
            mouth_x = x + self.width // 2 - 7
            mouth_y = y + int(self.height * 0.28)
            surface.blit(mouth_surf, (mouth_x, mouth_y))
            
    def get_dialogue_anchor(self, offset=(0, 0)):
        x = int(self.pos[0] - offset[0] + self.width // 2)
        y = int(self.pos[1] - offset[1])
        return (x, y)