import random
import math
import pygame

class Monster:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 25
        self.color = (150, 0, 150)  # Purple color for monsters
        self.speed = 2
        self.damage = 2
        self.attack_range = 30
        self.attack_cooldown = 60  # 1 second at 60 FPS
        self.current_cooldown = 0
        self.max_hp = 10
        self.hp = self.max_hp
        
    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > self.speed:
            self.x += (dx/distance) * self.speed
            self.y += (dy/distance) * self.speed
            
    def can_attack(self):
        return self.current_cooldown <= 0
        
    def update_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            
    def is_dead(self):
        return self.hp <= 0

    def draw(self, screen):
        # Draw monster body
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        
        # Draw monster eyes
        eye_color = (255, 0, 0)
        eye_size = 5
        pygame.draw.circle(screen, eye_color, (int(self.x - 7), int(self.y - 5)), eye_size)
        pygame.draw.circle(screen, eye_color, (int(self.x + 7), int(self.y - 5)), eye_size)
        
        # Draw HP bar
        hp_width = 30
        hp_height = 4
        hp_x = self.x - hp_width//2
        hp_y = self.y - self.size - 10
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), (hp_x, hp_y, hp_width, hp_height))
        # Foreground (green)
        hp_remaining = (self.hp / self.max_hp) * hp_width
        pygame.draw.rect(screen, (0, 255, 0), (hp_x, hp_y, hp_remaining, hp_height)) 