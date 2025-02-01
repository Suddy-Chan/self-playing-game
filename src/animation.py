import pygame

class Animation:
    def __init__(self, text, x, y, color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = 60  # frames
        self.y_offset = 0

    def update(self):
        self.lifetime -= 1
        self.y_offset -= 1  # Float up

    def draw(self, screen):
        font = pygame.font.Font(None, 24)
        alpha = min(255, self.lifetime * 4)
        text_surface = font.render(self.text, True, self.color)
        text_surface.set_alpha(alpha)
        screen.blit(text_surface, (self.x, self.y + self.y_offset)) 