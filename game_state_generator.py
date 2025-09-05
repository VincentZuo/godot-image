def generate_box_pushing_state():
    """Generate a JSON string representing a new box-pushing game state"""
    import json
    import random
    
    # Grid dimensions
    grid_width = 12
    grid_height = 10
    
    # Initialize empty grid
    grid = []
    for y in range(grid_height):
        row = ['empty'] * grid_width
        grid.append(row)
    
    # Add walls around the border
    for x in range(grid_width):
        grid[0][x] = 'wall'
        grid[grid_height-1][x] = 'wall'
    for y in range(grid_height):
        grid[y][0] = 'wall'
        grid[y][grid_width-1] = 'wall'
    
    # Add some internal walls for interesting level design
    wall_count = random.randint(8, 15)
    for _ in range(wall_count):
        x = random.randint(2, grid_width-3)
        y = random.randint(2, grid_height-3)
        if grid[y][x] == 'empty':
            grid[y][x] = 'wall'
    
    # Place player in a random empty position
    while True:
        player_x = random.randint(1, grid_width-2)
        player_y = random.randint(1, grid_height-2)
        if grid[player_y][player_x] == 'empty':
            break
    
    # Place targets (goals) - 3 to 6 targets
    targets = []
    target_count = random.randint(3, 6)
    target_positions = set()
    
    for _ in range(target_count):
        while True:
            x = random.randint(1, grid_width-2)
            y = random.randint(1, grid_height-2)
            if grid[y][x] == 'empty' and (x, y) != (player_x, player_y) and (x, y) not in target_positions:
                targets.append({"x": x, "y": y, "completed": False})
                target_positions.add((x, y))
                grid[y][x] = 'target'
                break
    
    # Place boxes - same number as targets
    boxes = []
    box_positions = set()
    
    for i in range(target_count):
        while True:
            x = random.randint(1, grid_width-2)
            y = random.randint(1, grid_height-2)
            if (grid[y][x] == 'empty' and 
                (x, y) != (player_x, player_y) and 
                (x, y) not in target_positions and 
                (x, y) not in box_positions):
                
                boxes.append({
                    "x": x, 
                    "y": y, 
                    "id": i,
                    "on_target": False
                })
                box_positions.add((x, y))
                grid[y][x] = 'box'
                break
    
    # Create complete game state
    game_state = {
        "player": {
            "x": player_x,
            "y": player_y,
            "selected_box": None
        },
        "grid": grid,
        "boxes": boxes,
        "targets": targets,
        "score": {
            "points": 0,
            "moves": 0,
            "pushes": 0,
            "time_bonus": 1000,
            "level_complete": False
        },
        "rewards": {
            "move_efficiency_bonus": 0,
            "speed_bonus": 0,
            "perfect_solution": False
        },
        "level": 1,
        "turn_number": 0,
        "game_status": "playing",
        "step": 0,
        "grid_width": grid_width,
        "grid_height": grid_height
    }
    
    return json.dumps(game_state, indent=2)

