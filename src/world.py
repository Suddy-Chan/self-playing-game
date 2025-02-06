import random
import math
import pygame
from .enums import Resource, Action
from .animation import Animation
from .buildings import House

class World:
    def __init__(self):
        self.resources = {
            Resource.WOOD: 100,
            Resource.FOOD: 50,
        }
        self.characters = []
        self.width = 800
        self.height = 700
        self.ui_height = 160
        self.game_area_start = self.ui_height
        self.tree_positions = []
        self.food_positions = []
        self.houses = []
        self.farm_positions = []
        self.animations = []
        self.max_trees = 20
        self.max_food = 10
        self.resource_regen_timer = 0
        self.resource_regen_interval = 300
        self.game_speed = 1
        self.max_speed = 5
        self.min_house_distance = 80
        self.error_message_cooldown = 0
        self.generate_resources()
        self.ui_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        # Rearrange speed control positions
        button_width = 20
        button_height = 20
        button_y = 55
        self.speed_label_pos = (500, button_y)
        self.decrease_button = pygame.Rect(560, button_y, button_width, button_height)
        self.speed_value_pos = (590, button_y)
        self.increase_button = pygame.Rect(630, button_y, button_width, button_height)

    def add_character(self, character):
        self.characters.append(character)

    def generate_resources(self):
        margin = 50
        for _ in range(self.max_trees):
            x = random.randint(margin, self.width - margin)
            y = random.randint(self.game_area_start + margin, self.height - margin)
            self.tree_positions.append((x, y))
            
        for _ in range(self.max_food):
            x = random.randint(margin, self.width - margin)
            y = random.randint(self.game_area_start + margin, self.height - margin)
            self.food_positions.append((x, y))

    def regenerate_resources(self):
        self.resource_regen_timer += 1
        if self.resource_regen_timer >= self.resource_regen_interval:
            self.resource_regen_timer = 0
            
            if len(self.tree_positions) < self.max_trees and self.resources[Resource.WOOD] < 100:
                margin = 50
                x = random.randint(margin, self.width - margin)
                y = random.randint(self.game_area_start + margin, self.height - margin)
                self.tree_positions.append((x, y))
                self.resources[Resource.WOOD] += 1
                self.animations.append(
                    Animation("New Tree", x, y, (0, 255, 0)))
            
            if len(self.food_positions) < self.max_food and self.resources[Resource.FOOD] < 50:
                margin = 50
                x = random.randint(margin, self.width - margin)
                y = random.randint(self.game_area_start + margin, self.height - margin)
                self.food_positions.append((x, y))
                self.resources[Resource.FOOD] += 1
                self.animations.append(
                    Animation("New Food", x, y, (255, 255, 0)))

    def find_nearest_resource(self, character, resource_positions):
        if not resource_positions:
            return None
        distances = [(pos, math.sqrt((character.x - pos[0])**2 + (character.y - pos[1])**2))
                    for pos in resource_positions]
        return min(distances, key=lambda x: x[1])[0]

    def remove_resource(self, position, resource_type):
        if resource_type == "tree":
            self.tree_positions.remove(position)
        elif resource_type == "food":
            self.food_positions.remove(position)

    def find_nearby_house(self, character, check_distance=None):
        if check_distance is None:
            check_distance = self.min_house_distance
        
        for house in self.houses:
            dx = house.x - character.x
            dy = house.y - character.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= check_distance:
                return house
        return None

    def can_build_house(self, x, y):
        # Check if too close to other houses
        for house in self.houses:
            dx = house.x - x
            dy = house.y - y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < self.min_house_distance:
                return False
        return True

    def perform_action(self, character, action):
        reward = 0
        
        if character.action_state != "idle":
            if character.update():
                if action == Action.CHOP_TREE:
                    if character.current_target in self.tree_positions:
                        character.inventory[Resource.WOOD] += 1
                        self.resources[Resource.WOOD] -= 1
                        reward = 5 - ((character.max_hp - character.hp) / character.max_hp * 2)
                        self.remove_resource(character.current_target, "tree")
                        
                elif action == Action.HARVEST_FOOD:
                    if character.current_target in self.food_positions:
                        character.inventory[Resource.FOOD] += 1
                        self.resources[Resource.FOOD] -= 1
                        hp_bonus = (character.max_hp - character.hp) / character.max_hp * 5
                        reward = 3 + hp_bonus
                        character.hp = min(character.max_hp, character.hp + character.hp_per_food)
                        self.remove_resource(character.current_target, "food")
                
                elif action == Action.FARM_FOOD:
                    if character.inventory[Resource.FOOD] >= 1:
                        character.inventory[Resource.FOOD] -= 1
                        character.inventory[Resource.FOOD] += 2
                        self.farm_positions.append((character.x, character.y))
                        reward = 8
                
                character.current_target = None
                character.action_state = "idle"
            return reward
        
        character.current_action = action
        
        if action == Action.CHOP_TREE:
            if self.tree_positions:
                target = self.find_nearest_resource(character, self.tree_positions)
                if target:
                    character.current_target = target
                    character.action_state = "moving"
                else:
                    reward = -2
                
        elif action == Action.HARVEST_FOOD:
            if self.food_positions:
                target = self.find_nearest_resource(character, self.food_positions)
                if target:
                    character.current_target = target
                    character.action_state = "moving"
                else:
                    reward = -2
            else:
                reward = -2
                
        elif action == Action.BUILD_HOUSE:
            if character.inventory[Resource.WOOD] >= 5:
                # Check if location is valid before building
                if self.can_build_house(character.x, character.y):
                    character.inventory[Resource.WOOD] -= 5
                    self.houses.append(House(character.x, character.y))
                    character.inventory[Resource.HOUSE] += 1
                    self.animations.append(
                        Animation("House Built!", character.x, character.y, (0, 255, 0)))
                    return 10
                else:
                    # Only show error message if cooldown is 0
                    if self.error_message_cooldown <= 0:
                        self.animations.append(
                            Animation("Too close to other houses!", character.x, character.y, (255, 0, 0)))
                        self.error_message_cooldown = 60  # Set cooldown (1 second at 60 FPS)
                    return -1
            else:
                reward = -1

        elif action == Action.FARM_FOOD:
            if character.inventory[Resource.FOOD] >= 1:
                character.current_target = (character.x, character.y)
                character.action_state = "gathering"
                self.gathering_time = 0
            else:
                reward = -1

        character.learn(action, reward)
        return reward

    def update_characters(self):
        # Update error message cooldown
        if self.error_message_cooldown > 0:
            self.error_message_cooldown -= 1
        
        # Remove dead characters
        self.characters = [char for char in self.characters if not char.is_dead]
        
        # Update remaining characters
        for character in self.characters:
            nearby_house = self.find_nearby_house(character)
            if nearby_house:
                hp_regen = nearby_house.level_benefits[nearby_house.level]["hp_regen"]
                character.hp = min(character.max_hp, character.hp + hp_regen)

    def draw(self, screen):
        # Draw game background
        pygame.draw.rect(screen, (50, 100, 50), 
                        (0, self.game_area_start, self.width, self.height - self.game_area_start))
        
        # Draw grid lines
        grid_spacing = 50
        for x in range(0, self.width, grid_spacing):
            pygame.draw.line(screen, (60, 110, 60), 
                           (x, self.game_area_start), 
                           (x, self.height))
        for y in range(self.game_area_start, self.height, grid_spacing):
            pygame.draw.line(screen, (60, 110, 60), 
                           (0, y), 
                           (self.width, y))
        
        # Draw resources and entities
        for x, y in self.tree_positions:
            self.draw_tree(screen, x, y)
        for x, y in self.food_positions:
            self.draw_food(screen, x, y)
        for house in self.houses:
            self.draw_house(screen, house)
        for x, y in self.farm_positions:
            self.draw_farm(screen, x, y)
            
        # Draw characters
        for character in self.characters:
            character.draw(screen)
            
        # Draw animations
        self.animations = [anim for anim in self.animations if anim.lifetime > 0]
        for animation in self.animations:
            animation.update()
            animation.draw(screen)
            
        # Draw UI
        self.draw_ui(screen)

    def draw_tree(self, screen, x, y):
        trunk_color = (139, 69, 19)
        leaves_color = (34, 139, 34)
        
        pygame.draw.rect(screen, trunk_color, (x - 5, y, 10, 20))
        pygame.draw.circle(screen, leaves_color, (x, y - 10), 15)

    def draw_food(self, screen, x, y):
        pygame.draw.circle(screen, (255, 215, 0), (x, y), 8)
        pygame.draw.circle(screen, (218, 165, 32), (x, y), 6)

    def draw_house(self, screen, house):
        base_size = 30
        size_increase = 10
        current_size = base_size + (house.level - 1) * size_increase
        
        house_color = {
            1: (139, 69, 19),
            2: (160, 82, 45),
            3: (178, 34, 34)
        }[house.level]
        
        pygame.draw.rect(screen, house_color, 
                        (house.x - current_size/2, 
                         house.y - current_size/2, 
                         current_size, current_size))
        
        roof_height = 20 + (house.level - 1) * 5
        pygame.draw.polygon(screen, (165, 42, 42),
                          [(house.x - current_size/2 - 5, house.y - current_size/2),
                           (house.x + current_size/2 + 5, house.y - current_size/2),
                           (house.x, house.y - current_size/2 - roof_height)])
        
        font = pygame.font.Font(None, 20)
        level_text = font.render(f"Lv{house.level}", True, (255, 255, 255))
        screen.blit(level_text, (house.x - level_text.get_width()/2, 
                                house.y + current_size/2 + 5))

        # Add tooltip on hover
        mouse_pos = pygame.mouse.get_pos()
        house_rect = pygame.Rect(house.x - 20, house.y - 20, 40, 40)
        
        if house_rect.collidepoint(mouse_pos):
            tooltip_lines = [
                f"Level {house.level} House",
                f"HP Recovery: {house.level_benefits[house.level]['hp_regen'] * 100}% per second"
            ]
            tooltip_font = pygame.font.Font(None, 20)
            line_height = 20
            
            # Calculate tooltip dimensions
            max_width = max(tooltip_font.size(line)[0] for line in tooltip_lines)
            tooltip_width = max_width + 10
            tooltip_height = (len(tooltip_lines) * line_height) + 10
            
            # Adjust position to keep tooltip on screen
            tooltip_x = min(mouse_pos[0] + 10, self.width - tooltip_width - 10)
            tooltip_y = min(mouse_pos[1] + 10, self.height - tooltip_height - 10)
            
            # Draw background for tooltip
            tooltip_bg = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
            pygame.draw.rect(screen, (40, 40, 40), tooltip_bg)
            pygame.draw.rect(screen, (100, 100, 100), tooltip_bg, 1)
            
            # Draw each line of text
            for i, line in enumerate(tooltip_lines):
                tooltip_surface = tooltip_font.render(line, True, (255, 255, 255))
                screen.blit(tooltip_surface, 
                           (tooltip_x + 5, 
                            tooltip_y + 5 + (i * line_height)))

    def draw_farm(self, screen, x, y):
        farm_color = (205, 133, 63)
        crop_color = (154, 205, 50)
        
        pygame.draw.rect(screen, farm_color, (x - 15, y - 15, 30, 30))
        for i in range(3):
            for j in range(3):
                pygame.draw.line(screen, crop_color,
                               (x - 10 + i*10, y - 10 + j*10),
                               (x - 10 + i*10, y - 15 + j*10), 2)

    def draw_ui(self, screen):
        # Draw main UI background
        ui_surface = pygame.Surface((self.width, self.ui_height))
        ui_surface.fill((40, 40, 40))
        screen.blit(ui_surface, (0, 0))
        
        # Draw instruction panel
        instruction_height = 45
        instruction_surface = pygame.Surface((self.width, instruction_height))
        instruction_surface.fill((60, 60, 80))
        screen.blit(instruction_surface, (0, 0))
        
        instructions1 = "Controls: Move mouse to desired location, then:"
        instructions2 = "Press 1 to plant tree | Press 2 to plant food"
        
        instruction_text1 = self.ui_font.render(instructions1, True, (255, 255, 255))
        instruction_text2 = self.ui_font.render(instructions2, True, (255, 255, 255))
        padding = 20
        screen.blit(instruction_text1, (padding, 8))
        screen.blit(instruction_text2, (padding, 28))
        
        # Draw world stats panel
        stats_y = instruction_height
        stats_height = 35
        stats_surface = pygame.Surface((self.width, stats_height))
        stats_surface.fill((50, 50, 50))
        screen.blit(stats_surface, (0, stats_y))
        
        stats_padding = 20
        world_stats = [
            f"Trees: {self.resources[Resource.WOOD]}",
            f"Food: {self.resources[Resource.FOOD]}",
            f"Next Resource: {(self.resource_regen_interval - self.resource_regen_timer) // 60}s"
        ]
        
        x_pos = stats_padding
        stats_text_y = stats_y + 10
        for i, text in enumerate(world_stats):
            text_surface = self.ui_font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (x_pos, stats_text_y))
            # Add extra spacing before the speed text
            x_pos += 200 if i == 2 else 150
        
        # Draw character stats panel
        char_stats_y = stats_y + stats_height
        char_stats_height = 80
        char_stats_surface = pygame.Surface((self.width, char_stats_height))
        char_stats_surface.fill((45, 45, 55))
        screen.blit(char_stats_surface, (0, char_stats_y))
        
        char_start_y = char_stats_y + 10
        for idx, char in enumerate(self.characters):
            x_pos = stats_padding + (idx * 260)
            
            name_text = self.title_font.render(char.name, True, (255, 255, 0))
            screen.blit(name_text, (x_pos, char_start_y))
            
            stats_text = [
                f"HP: {char.hp:.0f}/{char.max_hp}",
                f"Food: {char.inventory[Resource.FOOD]}"
            ]
            
            for i, text in enumerate(stats_text):
                text_surface = self.ui_font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (x_pos, char_start_y + 25 + i * 20))
        
        # Draw speed controls in new order
        # Draw "Speed:" label
        speed_label = self.ui_font.render("Speed:", True, (255, 255, 255))
        screen.blit(speed_label, self.speed_label_pos)
        
        # Draw decrease button (-)
        pygame.draw.rect(screen, (100, 100, 100), self.decrease_button)
        pygame.draw.rect(screen, (200, 200, 200), self.decrease_button, 2)
        minus_text = self.ui_font.render("-", True, (255, 255, 255))
        screen.blit(minus_text, (self.decrease_button.centerx - 4, self.decrease_button.centery - 8))
        
        # Draw speed value
        speed_value = self.ui_font.render(f"{self.game_speed}x", True, (255, 255, 255))
        screen.blit(speed_value, self.speed_value_pos)
        
        # Draw increase button (+)
        pygame.draw.rect(screen, (100, 100, 100), self.increase_button)
        pygame.draw.rect(screen, (200, 200, 200), self.increase_button, 2)
        plus_text = self.ui_font.render("+", True, (255, 255, 255))
        screen.blit(plus_text, (self.increase_button.centerx - 4, self.increase_button.centery - 8))

    def handle_mouse_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.decrease_button.collidepoint(event.pos):
                self.game_speed = max(1, self.game_speed - 1)
            elif self.increase_button.collidepoint(event.pos):
                self.game_speed = min(self.max_speed, self.game_speed + 1) 