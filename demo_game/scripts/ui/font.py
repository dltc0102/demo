import pygame
from demo_game.scripts.core.utils import load_image

def clip(surf, x, y, x_size, y_size):
    handle_surf = surf.copy()
    clipR = pygame.Rect(x, y, x_size, y_size)
    handle_surf.set_clip(clipR)
    image = surf.subsurface(handle_surf.get_clip())
    return image.copy()

class Font():
    def __init__(self, path, scale=1):
        self.scale = scale
        self.spacing = 1 * self.scale
        self.character_order = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','.','-',',',':','+','\'','!','?','0','1','2','3','4','5','6','7','8','9', '_', '<', '>', '[', ']', '(', ')', '{', '}'
        ]
        font_img, font_w, font_h = load_image(path, convert_black=True)
        current_char_width = 0
        self.characters = {}
        character_count = 0
        for x in range(font_img.get_width()):
            c = font_img.get_at((x, 0))
            if c[0] == 127:
                char_img = clip(font_img, x - current_char_width, 0, current_char_width, font_h)
                char_img = pygame.transform.scale(
                    char_img,
                    (char_img.get_width() * self.scale, char_img.get_height() * self.scale)
                )
                self.characters[self.character_order[character_count]] = char_img.copy()
                character_count += 1
                current_char_width = 0
            else:
                current_char_width += 1
        self.space_width = self.characters['A'].get_width()

    def render(self, surf, text, loc):
        x_offset = 0
        for char in text:
            if char != ' ':
                surf.blit(self.characters[char], (loc[0] + x_offset, loc[1]))
                x_offset += self.characters[char].get_width() + self.spacing
            else:
                x_offset += self.space_width + self.spacing

    def text_width(self, text: str) -> int:
        width = 0
        for char in text:
            if char == ' ':
                width += self.space_width + self.spacing
            elif char in self.characters:
                width += self.characters[char].get_width() + self.spacing
        return width


    def wrap_text(self, text: str, max_width: int):
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.text_width(test_line) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines


    def render_wrapped(self, surf, text, loc, max_width, line_spacing=2):
        lines = self.wrap_text(text, max_width)

        x, y = loc
        char_height = next(iter(self.characters.values())).get_height()

        for line in lines:
            self.render(surf, line, (x, y))
            y += char_height + line_spacing


        