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