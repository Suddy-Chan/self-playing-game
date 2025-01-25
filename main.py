import random
import pygame
import math
from enum import Enum

class Action(Enum):
    BUILD_HOUSE = "build_house"
    CHOP_TREE = "chop_tree"
    HARVEST_FOOD = "harvest_food"
    FARM_FOOD = "farm_food"

class Resource(Enum):
    WOOD = "wood"
    FOOD = "food"
    HOUSE = "house"
    FARM = "farm"

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

class Character:
    def __init__(self, name, x, y):
        self.name = name
        self.inventory = {
            Resource.WOOD: 0,
            Resource.FOOD: 0,
            Resource.HOUSE: 0,
            Resource.FARM: 0,
        }
        # Q-learning parameters
        self.q_table = {
            Action.CHOP_TREE: random.uniform(0.1, 0.3),
            Action.HARVEST_FOOD: random.uniform(0.1, 0.3),
            Action.BUILD_HOUSE: random.uniform(0.1, 0.3),
            Action.FARM_FOOD: random.uniform(0.1, 0.3)
        }
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.2
        self.min_epsilon = 0.05
        self.epsilon_decay = 0.9995
        
        # Position and movement
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.speed = 3
        self.size = 20
        self.color = (255, 0, 0)
        
        # Animation
        self.current_action = None
        self.action_timer = 0
        
        # Add state tracking
        self.last_action = None
        self.last_reward = 0
        self.total_reward = 0
        self.is_moving = False
        self.current_target = None
        self.action_state = "idle"  # States: "idle", "moving", "gathering"
        self.gathering_time = 0
        self.gathering_duration = 60  # 1 second at 60 FPS
        
        # Add health system with reduced decay rate
        self.max_hp = 100
        self.hp = self.max_hp
        self.hp_decay = 0.02  # Reduced from 0.1 to 0.02
        self.hp_per_food = 30  # HP gained from eating food
        
        # Add personality traits to make characters behave differently
        self.traits = {
            'gatherer': random.uniform(0.8, 1.2),  # Affects resource gathering
            'builder': random.uniform(0.8, 1.2),   # Affects building preference
            'farmer': random.uniform(0.8, 1.2)     # Affects farming preference
        }

    def move_to_target(self):
        if not self.current_target:
            return True
            
        dx = self.current_target[0] - self.x
        dy = self.current_target[1] - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > self.speed:
            self.x += (dx/distance) * self.speed
            self.y += (dy/distance) * self.speed
            return False
        else:
            self.x = self.current_target[0]
            self.y = self.current_target[1]
            return True

    def update(self):
        if self.action_state == "moving":
            if self.move_to_target():
                self.action_state = "gathering"
                self.gathering_time = 0
        elif self.action_state == "gathering":
            self.gathering_time += 1
            if self.gathering_time >= self.gathering_duration:
                self.action_state = "idle"
                return True
        return False

    def update_needs(self):
        # Decay HP over time
        self.hp = max(0, self.hp - self.hp_decay)

    def choose_action(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        if random.random() < self.epsilon:
            return random.choice(list(Action))
            
        action_weights = {}
        
        # Base weights from Q-table
        for action in Action:
            action_weights[action] = self.q_table[action]
        
        # Modify weights based on current needs and personality
        if self.hp < 70:  # Changed from hunger to HP
            action_weights[Action.HARVEST_FOOD] *= 1.5 * self.traits['gatherer']
            action_weights[Action.FARM_FOOD] *= 1.3 * self.traits['farmer']
            
        if self.inventory[Resource.WOOD] < 3:
            action_weights[Action.CHOP_TREE] *= 1.2 * self.traits['gatherer']
            
        if self.inventory[Resource.WOOD] >= 5:
            action_weights[Action.BUILD_HOUSE] *= 1.2 * self.traits['builder']
            
        if self.inventory[Resource.FOOD] >= 1:
            action_weights[Action.FARM_FOOD] *= 1.1 * self.traits['farmer']
            
        # Add small random variation to prevent ties
        for action in action_weights:
            action_weights[action] += random.uniform(0, 0.1)
            
        return max(action_weights.items(), key=lambda x: x[1])[0]

    def learn(self, action, reward):
        # Update Q-value with more sophisticated reward calculation
        old_value = self.q_table[action]
        next_max = max(self.q_table.values())  # Maximum future reward
        
        # Calculate new value incorporating future rewards
        new_value = (1 - self.learning_rate) * old_value + \
                   self.learning_rate * (reward + self.discount_factor * next_max)
        
        self.q_table[action] = new_value
        self.last_action = action
        self.last_reward = reward
        self.total_reward += reward

    def draw(self, screen):
        # Draw character
        pygame.draw.rect(screen, self.color, (self.x - self.size/2, self.y - self.size/2, 
                                            self.size, self.size))
        
        # Draw status bars
        self.draw_status_bars(screen)
        
        # Draw name
        font = pygame.font.Font(None, 20)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.x - name_text.get_width()/2, self.y - 65))
        
        # Draw current action if any
        if self.current_action:
            action_text = font.render(self.current_action.value, True, (255, 255, 0))
            screen.blit(action_text, (self.x - action_text.get_width()/2, self.y - 80))

    def draw_status_bars(self, screen):
        bar_width = 50
        bar_height = 4
        start_y = self.y - 50
        
        # Draw HP bar (red)
        hp_percentage = self.hp / self.max_hp
        pygame.draw.rect(screen, (100, 0, 0), 
                        (self.x - bar_width/2, start_y, bar_width, bar_height))
        pygame.draw.rect(screen, (255, 0, 0), 
                        (self.x - bar_width/2, start_y, 
                         bar_width * hp_percentage, bar_height))

class World:
    def __init__(self):
        self.resources = {
            Resource.WOOD: 100,
            Resource.FOOD: 50,
        }
        self.characters = []
        self.width = 800
        self.height = 700  # Increased to maintain game area size
        self.game_area_start = 100  # Where the game area begins
        self.tree_positions = []
        self.food_positions = []
        self.house_positions = []
        self.farm_positions = []
        self.animations = []
        self.max_trees = 20
        self.max_food = 10
        self.resource_regen_timer = 0
        self.resource_regen_interval = 300  # Regenerate every 5 seconds (at 60 FPS)
        self.generate_resources()
        self.ui_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.ui_height = 100  # Height of the top UI panel

    def add_character(self, character):
        self.characters.append(character)

    def generate_resources(self):
        margin = 50
        # Generate resources only in the game area
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
            
            # Regenerate trees
            if len(self.tree_positions) < self.max_trees and self.resources[Resource.WOOD] < 100:
                margin = 50
                x = random.randint(margin, self.width - margin)
                y = random.randint(self.game_area_start + margin, self.height - margin)
                self.tree_positions.append((x, y))
                self.resources[Resource.WOOD] += 1
                self.animations.append(
                    Animation("🌱 New Tree", x, y, (0, 255, 0)))
            
            # Regenerate food
            if len(self.food_positions) < self.max_food and self.resources[Resource.FOOD] < 50:
                margin = 50
                x = random.randint(margin, self.width - margin)
                y = random.randint(self.game_area_start + margin, self.height - margin)
                self.food_positions.append((x, y))
                self.resources[Resource.FOOD] += 1
                self.animations.append(
                    Animation("🌾 New Food", x, y, (255, 255, 0)))

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
        
        # If character is already performing an action, continue it
        if character.action_state != "idle":
            if character.update():  # Returns True when action is complete
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
        
        # Start new action
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
                character.inventory[Resource.HOUSE] += 1
                self.house_positions.append((character.x, character.y))
                reward = 10
                
        elif action == Action.FARM_FOOD:
            if character.inventory[Resource.FOOD] >= 1:
                character.current_target = (character.x, character.y)  # Farm at current position
                character.action_state = "gathering"  # Set gathering state to require time
                self.gathering_time = 0
            else:
                reward = -1

        character.learn(action, reward)
        return reward

    def draw(self, screen):
        # Draw background
        screen.fill((50, 100, 50))  # Dark green background
        
        # Draw grid lines
        grid_spacing = 50
        for x in range(0, self.width, grid_spacing):
            pygame.draw.line(screen, (60, 110, 60), (x, 0), (x, self.height))
        for y in range(0, self.height, grid_spacing):
            pygame.draw.line(screen, (60, 110, 60), (0, y), (self.width, y))
        
        # Draw resources and entities
        for x, y in self.tree_positions:
            self.draw_tree(screen, x, y)
        for x, y in self.food_positions:
            self.draw_food(screen, x, y)
        for x, y in self.house_positions:
            self.draw_house(screen, x, y)
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
            
        # Draw UI last
        self.draw_ui(screen)

    def draw_tree(self, screen, x, y):
        trunk_color = (139, 69, 19)
        leaves_color = (34, 139, 34)
        
        # Draw trunk
        pygame.draw.rect(screen, trunk_color, (x - 5, y, 10, 20))
        # Draw leaves
        pygame.draw.circle(screen, leaves_color, (x, y - 10), 15)

    def draw_food(self, screen, x, y):
        pygame.draw.circle(screen, (255, 215, 0), (x, y), 8)
        pygame.draw.circle(screen, (218, 165, 32), (x, y), 6)

    def draw_house(self, screen, x, y):
        # Draw house body
        pygame.draw.rect(screen, (139, 69, 19), (x - 15, y - 15, 30, 30))
        # Draw roof
        pygame.draw.polygon(screen, (165, 42, 42), 
                          [(x - 20, y - 15), (x + 20, y - 15), (x, y - 35)])

    def draw_farm(self, screen, x, y):
        farm_color = (205, 133, 63)
        crop_color = (154, 205, 50)
        
        # Draw tilled soil
        pygame.draw.rect(screen, farm_color, (x - 15, y - 15, 30, 30))
        # Draw crops
        for i in range(3):
            for j in range(3):
                pygame.draw.line(screen, crop_color,
                               (x - 10 + i*10, y - 10 + j*10),
                               (x - 10 + i*10, y - 15 + j*10), 2)

    def draw_ui(self, screen):
        # Draw UI background
        ui_surface = pygame.Surface((self.width, self.ui_height))
        ui_surface.fill((40, 40, 40))
        screen.blit(ui_surface, (0, 0))
        
        # Draw world stats
        world_stats = [
            f"Trees: {self.resources[Resource.WOOD]}",
            f"Food: {self.resources[Resource.FOOD]}",
            f"Next Resource: {(self.resource_regen_interval - self.resource_regen_timer) // 60}s"
        ]
        
        x_pos = 10
        for text in world_stats:
            text_surface = self.ui_font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (x_pos, 10))
            x_pos += 150
            
        # Draw character stats in columns
        char_start_y = 40
        for idx, char in enumerate(self.characters):
            x_pos = 10 + (idx * 260)  # Space characters horizontally
            
            # Draw character name and stats
            name_text = self.title_font.render(char.name, True, (255, 255, 0))
            screen.blit(name_text, (x_pos, char_start_y))
            
            stats_text = [
                f"HP: {char.hp:.0f}/{char.max_hp}",
                f"Food: {char.inventory[Resource.FOOD]}"
            ]
            
            for i, text in enumerate(stats_text):
                text_surface = self.ui_font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (x_pos, char_start_y + 25 + i * 20))

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 700))  # Adjusted height
    pygame.display.set_caption("AI Village Simulation")
    clock = pygame.time.Clock()
    
    world = World()
    
    # Create three characters with different starting positions
    characters = [
        Character("Bob", 200, 400),
        Character("Alice", 400, 400),
        Character("Charlie", 600, 400)
    ]
    
    # Give each character different colors
    characters[0].color = (255, 100, 100)  # Red
    characters[1].color = (100, 255, 100)  # Green
    characters[2].color = (100, 100, 255)  # Blue
    
    for character in characters:
        world.add_character(character)
    
    running = True
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update all characters
        for character in characters:
            character.update_needs()
        
        world.regenerate_resources()
        
        # Update each character's actions
        if frame_count % 60 == 0:
            for character in characters:
                if character.action_state == "idle":
                    action = character.choose_action()
                    reward = world.perform_action(character, action)
                    print(f"{character.name} performed {action.value}, got reward: {reward}")
        else:
            for character in characters:
                if character.current_action:
                    world.perform_action(character, character.current_action)
        
        # Clear screen and draw
        screen.fill((50, 100, 50))
        world.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1
    
    pygame.quit()

if __name__ == "__main__":
    main()
