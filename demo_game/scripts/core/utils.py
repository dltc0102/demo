import pygame

def load_image(path: str, convert_white=False, convert_black=False) -> tuple[int, int, pygame.Surface]:
    img = pygame.image.load(path).convert_alpha()
    if convert_white: img.set_colorkey((255, 255, 255))
    if convert_black: img.set_colorkey((0, 0, 0))
    img_w, img_h = img.get_size()
    return img, img_w, img_h