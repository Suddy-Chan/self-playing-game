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
        self.base_speed = 3  # Rename speed to base_speed
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

    def get_current_speed(self):
        # Calculate speed multiplier based on HP percentage
        hp_percentage = self.hp / self.max_hp
        # Speed ranges from 50% to 150% of base speed depending on HP
        speed_multiplier = 0.5 + hp_percentage
        return self.base_speed * speed_multiplier

    def move_to_target(self):
        if not self.current_target:
            return True
            
        dx = self.current_target[0] - self.x
        dy = self.current_target[1] - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        current_speed = self.get_current_speed()  # Get speed based on HP
        
        if distance > current_speed:
            self.x += (dx/distance) * current_speed
            self.y += (dy/distance) * current_speed
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

class House:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.level = 1
        self.max_level = 3
        # Resources needed for each upgrade
        self.upgrade_costs = {
            2: {"wood": 8},  # Level 1 -> 2
            3: {"wood": 15}  # Level 2 -> 3
        }
        # Benefits for each level
        self.level_benefits = {
            1: {"hp_regen": 0.05},
            2: {"hp_regen": 0.1},
            3: {"hp_regen": 0.2}
        }

class World:
    def __init__(self):
        self.resources = {
            Resource.WOOD: 100,
            Resource.FOOD: 50,
        }
        self.characters = []
        self.width = 800
        self.height = 700
        self.ui_height = 160  # Total height of all UI panels
        self.game_area_start = self.ui_height  # Game starts below UI
        self.tree_positions = []
        self.food_positions = []
        self.houses = []  # Replace house_positions with House objects
        self.farm_positions = []
        self.animations = []
        self.max_trees = 20
        self.max_food = 10
        self.resource_regen_timer = 0
        self.resource_regen_interval = 300  # Regenerate every 5 seconds (at 60 FPS)
        self.generate_resources()
        self.ui_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

    def add_character(self, character):
        self.characters.append(character)

    def generate_resources(self):
        margin = 50
        # Generate resources only below UI area
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
                    Animation("New Tree", x, y, (0, 255, 0)))
            
            # Regenerate food
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
                # Create new house
                new_house = House(character.x, character.y)
                self.houses.append(new_house)
                reward = 10
                
                # Add upgrade house action if near an existing house
                nearby_house = self.find_nearby_house(character)
                if nearby_house and nearby_house.level < nearby_house.max_level:
                    upgrade_cost = nearby_house.upgrade_costs[nearby_house.level + 1]["wood"]
                    if character.inventory[Resource.WOOD] >= upgrade_cost:
                        character.inventory[Resource.WOOD] -= upgrade_cost
                        nearby_house.level += 1
                        reward += 15  # Additional reward for upgrading
                        self.animations.append(
                            Animation(f"House Upgraded to Lv{nearby_house.level}!", 
                                    nearby_house.x, nearby_house.y, 
                                    (255, 215, 0)))  # Gold color for upgrade
            else:
                reward = -1

        elif action == Action.FARM_FOOD:
            if character.inventory[Resource.FOOD] >= 1:
                character.current_target = (character.x, character.y)  # Farm at current position
                character.action_state = "gathering"  # Set gathering state to require time
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
            if distance < 50:  # Within 50 pixels
                return house
        return None

    def update_characters(self):
        for character in self.characters:
            # Apply house benefits based on proximity
            nearby_house = self.find_nearby_house(character)
            if nearby_house:
                hp_regen = nearby_house.level_benefits[nearby_house.level]["hp_regen"]
                character.hp = min(character.max_hp, 
                                 character.hp + hp_regen)

    def draw(self, screen):
        # Draw game background only in game area
        pygame.draw.rect(screen, (50, 100, 50), 
                        (0, self.game_area_start, self.width, self.height - self.game_area_start))
        
        # Draw grid lines only in game area
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
            
        # Draw UI last (on top)
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

    def draw_house(self, screen, house):
        base_size = 30  # Base size for level 1
        size_increase = 10  # Size increase per level
        current_size = base_size + (house.level - 1) * size_increase
        
        # Draw house body (gets bigger with level)
        house_color = {
            1: (139, 69, 19),   # Brown
            2: (160, 82, 45),   # Sienna
            3: (178, 34, 34)    # Firebrick
        }[house.level]
        
        pygame.draw.rect(screen, house_color, 
                        (house.x - current_size/2, 
                         house.y - current_size/2, 
                         current_size, current_size))
        
        # Draw roof (gets taller with level)
        roof_height = 20 + (house.level - 1) * 5
        pygame.draw.polygon(screen, (165, 42, 42),
                          [(house.x - current_size/2 - 5, house.y - current_size/2),
                           (house.x + current_size/2 + 5, house.y - current_size/2),
                           (house.x, house.y - current_size/2 - roof_height)])
        
        # Draw level indicator
        font = pygame.font.Font(None, 20)
        level_text = font.render(f"Lv{house.level}", True, (255, 255, 255))
        screen.blit(level_text, (house.x - level_text.get_width()/2, 
                                house.y + current_size/2 + 5))

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
        # Draw main UI background
        ui_surface = pygame.Surface((self.width, self.ui_height))
        ui_surface.fill((40, 40, 40))
        screen.blit(ui_surface, (0, 0))
        
        # Draw instruction panel with different background color
        instruction_height = 45  # Increased height for better spacing
        instruction_surface = pygame.Surface((self.width, instruction_height))
        instruction_surface.fill((60, 60, 80))  # Slightly bluish dark gray
        screen.blit(instruction_surface, (0, 0))
        
        # Draw instructions in two lines with more spacing
        instructions1 = "Controls: Move mouse to desired location, then:"
        instructions2 = "Press 1 to plant tree | Press 2 to plant food"
        
        # Left-aligned instructions with padding, now in white (255, 255, 255)
        instruction_text1 = self.ui_font.render(instructions1, True, (255, 255, 255))
        instruction_text2 = self.ui_font.render(instructions2, True, (255, 255, 255))
        padding = 20
        screen.blit(instruction_text1, (padding, 8))
        screen.blit(instruction_text2, (padding, 28))
        
        # Draw world stats panel background
        stats_y = instruction_height
        stats_height = 35
        stats_surface = pygame.Surface((self.width, stats_height))
        stats_surface.fill((50, 50, 50))  # Gray for world stats
        screen.blit(stats_surface, (0, stats_y))
        
        # Draw world stats
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
        
        # Draw character stats panel background
        char_stats_y = stats_y + stats_height
        char_stats_height = 80  # Increased fixed height to cover all text
        char_stats_surface = pygame.Surface((self.width, char_stats_height))
        char_stats_surface.fill((45, 45, 55))  # Slightly bluish gray for character stats
        screen.blit(char_stats_surface, (0, char_stats_y))
        
        # Draw character stats in columns with proper spacing
        char_start_y = char_stats_y + 10
        for idx, char in enumerate(self.characters):
            x_pos = stats_padding + (idx * 260)
            
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

def draw_instruction_screen(screen):
    # Fill screen with semi-transparent black
    overlay = pygame.Surface((800, 700))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(230)
    screen.blit(overlay, (0, 0))
    
    # Create fonts with smaller size
    title_font = pygame.font.Font(None, 48)
    text_font = pygame.font.Font(None, 28)  # Reduced from 32 to 28
    
    # Title
    title = title_font.render("Welcome to AI Village Simulation!", True, (255, 255, 255))
    screen.blit(title, (400 - title.get_width()//2, 100))  # Moved up from 150 to 100
    
    # Instructions
    instructions = [
        "In this simulation, three AI characters (Alice, Bob, and Charlie)",
        "will autonomously perform various actions:",
        "",
        "• Chop trees for wood",
        "• Harvest and farm food to survive",
        "• Build and upgrade houses",
        "",
        "Characters will make decisions based on their needs and personality traits.",
        "Their speed depends on their health, which decreases over time.",
        "",
        "You can help by planting resources:",
        "• Press 1 to plant a tree",
        "• Press 2 to plant food"
    ]
    
    y = 180  # Start text higher (changed from 250)
    line_spacing = 30  # Reduced spacing (changed from 35)
    for line in instructions:
        text = text_font.render(line, True, (255, 255, 255))
        screen.blit(text, (400 - text.get_width()//2, y))
        y += line_spacing
    
    # Start button - moved lower
    button_rect = pygame.Rect(300, 620, 200, 50)  # Moved from 600 to 620
    pygame.draw.rect(screen, (0, 200, 0), button_rect)
    pygame.draw.rect(screen, (0, 150, 0), button_rect, 3)
    
    button_text = text_font.render("Start Simulation", True, (255, 255, 255))
    screen.blit(button_text, (400 - button_text.get_width()//2, 635))  # Adjusted y position
    
    return button_rect

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 700))
    pygame.display.set_caption("AI Village Simulation")
    clock = pygame.time.Clock()
    
    # Add instruction screen state
    show_instructions = True
    start_button = None
    
    world = World()
    
    # Create three characters with positions below UI, in alphabetical order
    characters = [
        Character("Alice", 200, 400),
        Character("Bob", 400, 400),
        Character("Charlie", 600, 400)
    ]
    
    # Give each character different colors
    characters[0].color = (100, 255, 100)  # Green for Alice
    characters[1].color = (255, 100, 100)  # Red for Bob
    characters[2].color = (100, 100, 255)  # Blue for Charlie
    
    for character in characters:
        world.add_character(character)
    
    running = True
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and show_instructions:
                # Check if start button was clicked
                if start_button and start_button.collidepoint(event.pos):
                    show_instructions = False
            elif not show_instructions and event.type == pygame.KEYDOWN:
                # Only allow key inputs when instruction screen is gone
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                if mouse_y > world.game_area_start:
                    if event.key == pygame.K_1:
                        world.tree_positions.append((mouse_x, mouse_y))
                        world.resources[Resource.WOOD] += 1
                        world.animations.append(
                            Animation("Tree Planted!", mouse_x, mouse_y, (0, 255, 0)))
                    elif event.key == pygame.K_2:
                        world.food_positions.append((mouse_x, mouse_y))
                        world.resources[Resource.FOOD] += 1
                        world.animations.append(
                            Animation("Food Planted!", mouse_x, mouse_y, (255, 255, 0)))
        
        if show_instructions:
            # Draw the game world in background
            screen.fill((50, 100, 50))
            world.draw(screen)
            # Draw instructions and get button rect
            start_button = draw_instruction_screen(screen)
        else:
            # Normal game update logic
            for character in characters:
                character.update_needs()
            
            world.regenerate_resources()
            
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
            
            world.update_characters()
            
            screen.fill((50, 100, 50))
            world.draw(screen)
            
            frame_count += 1
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
