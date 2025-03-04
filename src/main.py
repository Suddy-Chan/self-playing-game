import pygame
from src.world import World
from src.character import Character
from src.enums import Resource
from src.animation import Animation

# Define the take_screenshot function directly in main.py instead of importing it
def take_screenshot(screen):
    import datetime
    import os
    
    # Create screenshots directory if it doesn't exist
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"screenshots/screenshot-{timestamp}.png"
    pygame.image.save(screen, filename)
    print(f"Screenshot saved as {filename}")

def draw_instruction_screen(screen):
    overlay = pygame.Surface((800, 700))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(230)
    screen.blit(overlay, (0, 0))
    
    title_font = pygame.font.Font(None, 48)
    text_font = pygame.font.Font(None, 28)
    
    # Define instruction box dimensions
    box_width = 600
    box_height = 520
    box_x = 400 - box_width//2
    box_y = 60
    
    # Draw instruction box background and border
    pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, (100, 100, 100), (box_x, box_y, box_width, box_height), 2)
    
    title = title_font.render("AI Village Simulation", True, (255, 255, 255))
    screen.blit(title, (400 - title.get_width()//2, box_y + 40))  # Moved title down
    
    instructions = [
        "Welcome to the AI Village!",
        "",
        "Characters will learn to survive while fighting monsters:",
        "- Characters gain EXP and level up by defeating monsters",
        "- Monsters get stronger every minute",
        "- Game ends if all characters die",
        "",
        "You can help by adding resources:",
        "- Press 1 to plant trees",
        "- Press 2 to plant food",
        "- Use +/- buttons to control simulation speed (1x to 5x)",
        "",
        "Watch the timer to see how long your village survives!"
    ]
    
    y = box_y + 120  # Moved instruction text starting position down
    for line in instructions:
        text = text_font.render(line, True, (255, 255, 255))
        screen.blit(text, (400 - text.get_width()//2, y))
        y += 30
    
    button_width = 200
    button_height = 50
    button_x = 400 - button_width//2
    button_y = 620
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    
    # Draw button background
    pygame.draw.rect(screen, (0, 255, 0), button_rect)
    # Draw button border (2 pixels wide, dark green color)
    pygame.draw.rect(screen, (0, 100, 0), button_rect, 2)
    
    start_text = text_font.render("Start Simulation", True, (0, 0, 0))
    screen.blit(start_text, (400 - start_text.get_width()//2, button_y + 15))
    
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
                mouse_pos = pygame.mouse.get_pos()
                
                if world.help_button.collidepoint(mouse_pos):
                    # Toggle help overlay and pause state
                    world.show_help = not world.show_help
                    world.paused = world.show_help
                    world.help_page = 1  # Reset to first page when opening
                elif world.show_help:
                    # Click anywhere to close help and unpause
                    world.show_help = False
                    world.paused = False
                elif show_instructions:
                    # Check if start button is clicked
                    if start_button.collidepoint(mouse_pos):
                        show_instructions = False
                else:
                    world.handle_mouse_event(event)
            elif event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if not show_instructions:
                    world.handle_mouse_event(event)
            elif event.type == pygame.KEYDOWN:
                if world.show_help:
                    if event.key == pygame.K_LEFT:
                        world.help_page = max(1, world.help_page - 1)
                    elif event.key == pygame.K_RIGHT:
                        world.help_page = min(world.total_help_pages, world.help_page + 1)
                elif event.key == pygame.K_F12:  # F12 key for screenshot
                    take_screenshot(screen)
                elif not show_instructions:
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
            # Only process game updates if not game over and not paused
            if not world.game_over and not world.paused:
                # Process multiple frames based on game speed
                for _ in range(world.game_speed):
                    for character in characters[:]:
                        character.update_needs()
                        if character.is_dead:
                            world.animations.append(
                                Animation(f"{character.name} has died!", character.x, character.y, (255, 0, 0)))
                            characters.remove(character)
                    
                    world.check_game_over()  # Check if game is over
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
                    world.update_monsters()
                    world.update_game_time()
                    frame_count += 1
            
            screen.fill((50, 100, 50))
            world.draw(screen)
        
        pygame.display.flip()
        clock.tick(base_fps)
    
    pygame.quit()