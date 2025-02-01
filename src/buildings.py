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