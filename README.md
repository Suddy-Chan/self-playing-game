# AI Village Simulation

A game where AI characters learn to survive and fight monsters using reinforcement learning. Watch as Alice, Bob, and Charlie gather resources, build houses, and defend their village.

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

In this survival simulation, three AI characters must work together to survive against increasingly difficult monsters. Each character:
- Has health (HP) that slowly decays over time
- Can level up by defeating monsters
- Gains experience points (EXP) from combat
- Has combat abilities and can attack monsters
- Dies permanently when HP reaches 0
- Moves faster when healthy and slower when injured
- Can gather resources, build houses, and farm food
- Learns from their actions through Q-learning
- Has unique personality traits affecting their behavior

## Combat System

- Characters can attack nearby monsters
- Monsters spawn from the edges of the map
- Monster levels increase every minute
- Higher level monsters have:
  - More HP
  - Higher damage
  - Increased movement speed
- Experience is shared between nearby characters
- Characters level up to become stronger:
  - Increased max HP
  - Higher attack damage
  - Full heal on level up

## Controls

As a player, you can help the AI characters by adding resources:
1. Move your mouse to the desired location
2. Press keys:
   - `1`: Plant a tree
   - `2`: Plant food
3. Use the +/- buttons to control simulation speed (1x to 5x)

## Characters

The simulation features three characters with distinct colors:
- Alice (Green)
- Bob (Red)
- Charlie (Blue)

Each character has:
- Health Points (HP)
- Attack Damage
- Experience and Level
- Resource inventory
- Unique personality traits

## Game End

The simulation ends when:
- All characters are defeated by monsters
- Final survival time is displayed
- Game over screen shows the village's accomplishments

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
- Character stats (Name, HP, Attack, EXP)
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
- Level 1: Basic shelter (5 wood)
- Level 2: Improved house (8 wood)
- Level 3: Fortified home (15 wood)

Characters will automatically upgrade nearby houses if they have enough resources.
