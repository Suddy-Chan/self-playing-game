import random
import math
import pygame
from .enums import Action, Resource

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
        self.base_speed = 3
        self.size = 20
        self.color = (255, 0, 0)
        
        # Animation
        self.current_action = None
        self.action_timer = 0
        
        # State tracking
        self.last_action = None
        self.last_reward = 0
        self.total_reward = 0
        self.is_moving = False
        self.current_target = None
        self.action_state = "idle"
        self.gathering_time = 0
        self.gathering_duration = 60
        
        # Health system
        self.max_hp = 100
        self.hp = self.max_hp
        self.hp_decay = 0.02
        self.hp_per_food = 30
        
        # Personality traits
        self.traits = {
            'gatherer': random.uniform(0.8, 1.2),
            'builder': random.uniform(0.8, 1.2),
            'farmer': random.uniform(0.8, 1.2)
        }

        # Add after other initializations
        self.is_dead = False

    def get_current_speed(self):
        hp_percentage = self.hp / self.max_hp
        speed_multiplier = 0.5 + hp_percentage
        return self.base_speed * speed_multiplier

    def move_to_target(self):
        if not self.current_target:
            return True
            
        dx = self.current_target[0] - self.x
        dy = self.current_target[1] - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        current_speed = self.get_current_speed()
        
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
        self.hp = max(0, self.hp - self.hp_decay)
        if self.hp <= 0:
            self.is_dead = True

    def choose_action(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        if random.random() < self.epsilon:
            return random.choice(list(Action))
            
        action_weights = {}
        
        for action in Action:
            action_weights[action] = self.q_table[action]
        
        if self.hp < 70:
            action_weights[Action.HARVEST_FOOD] *= 1.5 * self.traits['gatherer']
            action_weights[Action.FARM_FOOD] *= 1.3 * self.traits['farmer']
            
        if self.inventory[Resource.WOOD] < 3:
            action_weights[Action.CHOP_TREE] *= 1.2 * self.traits['gatherer']
            
        if self.inventory[Resource.WOOD] >= 5:
            action_weights[Action.BUILD_HOUSE] *= 1.2 * self.traits['builder']
            
        if self.inventory[Resource.FOOD] >= 1:
            action_weights[Action.FARM_FOOD] *= 1.1 * self.traits['farmer']
            
        for action in action_weights:
            action_weights[action] += random.uniform(0, 0.1)
            
        return max(action_weights.items(), key=lambda x: x[1])[0]

    def learn(self, action, reward):
        old_value = self.q_table[action]
        next_max = max(self.q_table.values())
        
        new_value = (1 - self.learning_rate) * old_value + \
                   self.learning_rate * (reward + self.discount_factor * next_max)
        
        self.q_table[action] = new_value
        self.last_action = action
        self.last_reward = reward
        self.total_reward += reward

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, 
                        (self.x - self.size/2, self.y - self.size/2, 
                         self.size, self.size))
        
        self.draw_status_bars(screen)
        
        font = pygame.font.Font(None, 20)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.x - name_text.get_width()/2, self.y - 65))

    def draw_status_bars(self, screen):
        bar_width = 50
        bar_height = 4
        start_y = self.y - 50
        
        hp_percentage = self.hp / self.max_hp
        pygame.draw.rect(screen, (100, 0, 0), 
                        (self.x - bar_width/2, start_y, bar_width, bar_height))
        pygame.draw.rect(screen, (255, 0, 0), 
                        (self.x - bar_width/2, start_y, 
                         bar_width * hp_percentage, bar_height)) 