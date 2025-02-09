import pygame
from .world import World
from .character import Character
from .enums import Resource
from .animation import Animation

def draw_instruction_screen(screen):
    overlay = pygame.Surface((800, 700))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(230)
    screen.blit(overlay, (0, 0))
    
    title_font = pygame.font.Font(None, 48)
    text_font = pygame.font.Font(None, 28)
    
    title = title_font.render("Welcome to AI Village Simulation!", True, (255, 255, 255))
    screen.blit(title, (400 - title.get_width()//2, 100))
    
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
        "• Press 2 to plant food",
        "• Use +/- buttons at the top to control simulation speed"
    ]
    
    y = 180
    line_spacing = 30
    for line in instructions:
        text = text_font.render(line, True, (255, 255, 255))
        screen.blit(text, (400 - text.get_width()//2, y))
        y += line_spacing
    
    button_rect = pygame.Rect(300, 620, 200, 50)
    pygame.draw.rect(screen, (0, 200, 0), button_rect)
    pygame.draw.rect(screen, (0, 150, 0), button_rect, 3)
    
    button_text = text_font.render("Start Simulation", True, (255, 255, 255))
    screen.blit(button_text, (400 - button_text.get_width()//2, 635))
    
    return button_rect

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 700))
    pygame.display.set_caption("AI Village Simulation")
    
    show_instructions = True
    start_button = None
    
    world = World()
    
    characters = [
        Character("Alice", 200, 400),
        Character("Bob", 400, 400),
        Character("Charlie", 600, 400)
    ]
    
    characters[0].color = (100, 255, 100)  # Green for Alice
    characters[1].color = (255, 100, 100)  # Red for Bob
    characters[2].color = (100, 100, 255)  # Blue for Charlie
    
    for character in characters:
        world.add_character(character)
    
    running = True
    frame_count = 0
    
    # Initialize base clock
    clock = pygame.time.Clock()
    base_fps = 60
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_instructions:
                    # Check if start button is clicked
                    mouse_pos = pygame.mouse.get_pos()
                    if start_button.collidepoint(mouse_pos):
                        show_instructions = False
                else:
                    world.handle_mouse_event(event)
            elif event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if not show_instructions:
                    world.handle_mouse_event(event)
            elif not show_instructions and event.type == pygame.KEYDOWN:
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
            screen.fill((50, 100, 50))
            world.draw(screen)
            start_button = draw_instruction_screen(screen)
        else:
            # Process multiple frames based on game speed
            for _ in range(world.game_speed):
                for character in characters[:]:
                    character.update_needs()
                    if character.is_dead:
                        world.animations.append(
                            Animation(f"{character.name} has died!", character.x, character.y, (255, 0, 0)))
                        characters.remove(character)
                
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
                frame_count += 1
            
            screen.fill((50, 100, 50))
            world.draw(screen)
        
        pygame.display.flip()
        # Maintain consistent base frame rate
        clock.tick(base_fps)
    
    pygame.quit()