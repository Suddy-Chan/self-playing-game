# AI Village Simulation

A game where AI characters learn to play themselves based on reinforcement learning. Watch as Alice, Bob, and Charlie learn to survive by gathering resources, building houses, and farming food.

## How to Run

1. Make sure you have Python 3.x installed on your system
2. Install the required dependency:

```bash
pip install pygame
```

3. Clone this repository
4. Navigate to the project directory
5. Run the game:

```bash
python run.py
```

## Game Overview

In this simulation, three AI characters with different personalities interact with their environment to survive. Each character:
- Has a health (HP) system that slowly decays over time
- Dies permanently when HP reaches 0
- Moves faster when healthy and slower when injured
- Can gather resources, build houses, and farm food
- Learns from their actions through a Q-learning system
- Has unique personality traits affecting their behavior

## Controls

As a player, you can help the AI characters by adding resources to the environment:
1. Move your mouse to the desired location in the game area
2. Press keys:
   - `1`: Plant a tree
   - `2`: Plant food
3. Use the +/- buttons at the top to control simulation speed (1x to 5x)

## Characters

The simulation features three characters with distinct colors:
- Alice (Green)
- Bob (Red)
- Charlie (Blue)

Each character has:
- Health Points (HP)
- Food inventory
- Unique personality traits affecting:
  - Gathering efficiency
  - Building preference
  - Farming preference

## Actions

Characters can perform various actions:
- Chop trees for wood
- Harvest food
- Build houses (requires 5 wood)
- Farm food (requires 1 food, produces 2 food)

## UI Elements

The game interface shows:
- Player controls and instructions
- World resources (Trees, Food, Next resource spawn timer)
- Character stats (Name, HP, Food inventory)
- Visual feedback for actions and resource spawns

## Resource System

- Resources regenerate automatically over time
- Maximum limits: 20 trees, 10 food sources
- Resources only spawn in the game area (below UI panels)
- Visual animations show when new resources appear

## Learning System

Characters use Q-learning to:
- Learn from their actions and rewards
- Adapt their behavior based on needs
- Balance exploration and exploitation
- Consider their personality traits when making decisions

## Building System

Houses can be upgraded up to level 3:
- Level 1: Basic house (Costs 5 wood)
  - Provides basic HP regeneration (0.05 HP/tick)
- Level 2: Improved house (Costs 8 wood)
  - Increased HP regeneration (0.1 HP/tick)
  - Larger size
- Level 3: Advanced house (Costs 15 wood)
  - Maximum HP regeneration (0.2 HP/tick)
  - Largest size
  - Premium appearance

Characters will automatically upgrade nearby houses if they have enough resources.
