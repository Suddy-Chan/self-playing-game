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
        self.generate_resources()
        self.ui_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

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
                    reward = -1
            else:
                reward = -2
                
        elif action == Action.HARVEST_FOOD:
            if self.food_positions:
                target = self.find_nearest_resource(character, self.food_positions)
                if target:
                    character.current_target = target
                    character.action_state = "moving"
                else:
                    reward = -1
            else:
                reward = -2
                
        elif action == Action.BUILD_HOUSE:
            if character.inventory[Resource.WOOD] >= 5:
                character.inventory[Resource.WOOD] -= 5
                new_house = House(character.x, character.y)
                self.houses.append(new_house)
                reward = 10
                
                nearby_house = self.find_nearby_house(character)
                if nearby_house and nearby_house.level < nearby_house.max_level:
                    upgrade_cost = nearby_house.upgrade_costs[nearby_house.level + 1]["wood"]
                    if character.inventory[Resource.WOOD] >= upgrade_cost:
                        character.inventory[Resource.WOOD] -= upgrade_cost
                        nearby_house.level += 1
                        reward += 15
                        self.animations.append(
                            Animation(f"House Upgraded to Lv{nearby_house.level}!", 
                                    nearby_house.x, nearby_house.y, 
                                    (255, 215, 0)))
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

    def find_nearby_house(self, character):
        for house in self.houses:
            dx = house.x - character.x
            dy = house.y - character.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance < 50:
                return house
        return None

    def update_characters(self):
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
        for text in world_stats:
            text_surface = self.ui_font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (x_pos, stats_text_y))
            x_pos += 150
        
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