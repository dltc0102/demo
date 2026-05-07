import pygame

class Interactable:
    def __init__(self, name, rect, on_interact):
        self.name = name
        self.rect = pygame.Rect(rect)
        self.on_interact = on_interact

    def is_near(self, player):
        return self.rect.inflate(30, 30).colliderect(player.rect())

    def interact(self):
        self.on_interact()