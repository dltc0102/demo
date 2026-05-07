import pygame

class Button:
    def __init__(self, button_pos, image, img_scale=1):
        img_w = image.get_width()
        img_h = image.get_height()

        self.image = pygame.transform.scale(
            image,
            (int(img_w * img_scale), int(img_h * img_scale))
        )

        self.rect = self.image.get_rect()
        self.rect.topleft = button_pos
        self.clicked = False

    def render(self, surface) -> bool:
        action = False
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if self.rect.collidepoint(mouse_pos):
            if mouse_pressed and not self.clicked:
                self.clicked = True
                action = True

        if not mouse_pressed:
            self.clicked = False

        surface.blit(self.image, self.rect)
        return action
    