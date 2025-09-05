import pygame
import json
import os
import sys
from typing import Dict, List, Tuple, Optional
import time
from game_state_generator import generate_box_pushing_state

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 50
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50

# Colors (Modern, vibrant color palette)
COLORS = {
    'background': (30, 30, 40),      # Dark blue-gray
    'grid_line': (80, 80, 100),     # Light gray
    'wall': (60, 60, 80),           # Dark purple-gray
    'wall_highlight': (100, 100, 130), # Lighter wall color
    'empty': (240, 245, 250),       # Very light blue-white
    'player': (65, 150, 255),       # Bright blue
    'player_outline': (40, 100, 200), # Darker blue outline
    'box': (255, 180, 50),          # Orange
    'box_outline': (200, 140, 30),  # Darker orange
    'box_on_target': (50, 255, 100), # Green (when on target)
    'target': (255, 100, 150),      # Pink
    'target_outline': (200, 70, 120), # Darker pink
    'selected': (255, 255, 100),    # Yellow highlight
    'text': (255, 255, 255),        # White
    'score_bg': (50, 50, 70),       # Dark background for UI
    'button': (100, 120, 150),      # Button color
    'button_hover': (120, 140, 170), # Button hover
}

class BoxPushingGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Box Pushing Puzzle - Use WASD to move, SPACE to select")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 18)
        
        # Game state
        self.game_state = None
        self.running = True
        self.step_counter = 0
        
        # Visual effects
        self.animations = []
        self.particle_effects = []
        
        # Load or generate initial game state
        self.load_or_generate_game_state()
        
    def load_or_generate_game_state(self):
        """Load game state from JSON file or generate new one"""
        json_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('game_state')]
        
        if json_files:
            # Load the most recent game state file
            json_files.sort(reverse=True)
            try:
                with open(json_files[0], 'r') as f:
                    self.game_state = json.load(f)
                print(f"Loaded game state from {json_files[0]}")
            except Exception as e:
                print(f"Error loading {json_files[0]}: {e}")
                self.generate_new_game_state()
        else:
            self.generate_new_game_state()
    
    def generate_new_game_state(self):
        """Generate a new random game state"""
        game_state_json = generate_box_pushing_state()
        self.game_state = json.loads(game_state_json)
        print("Generated new random game state")
    
    def save_game_state(self):
        """Save current game state to JSON file"""
        self.step_counter += 1
        filename = f"game_state_step_{self.step_counter}.json"
        
        # Update step in game state
        self.game_state['step'] = self.step_counter
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.game_state, f, indent=2)
            print(f"Saved game state to {filename}")
        except Exception as e:
            print(f"Error saving game state: {e}")
    
    def handle_input(self, event):
        """Handle keyboard input (turn-based)"""
        if event.type != pygame.KEYDOWN:
            return
            
        moved = False
        player = self.game_state['player']
        
        if event.key == pygame.K_w:
            moved = self.try_move_player(0, -1)
        elif event.key == pygame.K_s:
            moved = self.try_move_player(0, 1)
        elif event.key == pygame.K_a:
            moved = self.try_move_player(-1, 0)
        elif event.key == pygame.K_d:
            moved = self.try_move_player(1, 0)
        elif event.key == pygame.K_SPACE:
            self.handle_selection()
            moved = True
        elif event.key == pygame.K_r:
            self.generate_new_game_state()
            moved = True
        
        if moved:
            self.update_game_logic()
            self.save_game_state()
    
    def try_move_player(self, dx: int, dy: int) -> bool:
        """Try to move player in given direction"""
        player = self.game_state['player']
        new_x = player['x'] + dx
        new_y = player['y'] + dy
        
        # Check bounds
        if (new_x < 0 or new_x >= self.game_state['grid_width'] or 
            new_y < 0 or new_y >= self.game_state['grid_height']):
            return False
        
        # Check if position is valid
        grid = self.game_state['grid']
        target_cell = grid[new_y][new_x]
        
        if target_cell == 'wall':
            return False
        
        # Check if there's a box at target position
        box_at_target = self.get_box_at_position(new_x, new_y)
        
        if box_at_target:
            # Try to push the box
            if self.try_push_box(box_at_target, dx, dy):
                player['x'] = new_x
                player['y'] = new_y
                self.game_state['score']['moves'] += 1
                self.game_state['score']['pushes'] += 1
                return True
            else:
                return False
        else:
            # Simple move
            player['x'] = new_x
            player['y'] = new_y
            self.game_state['score']['moves'] += 1
            return True
    
    def try_push_box(self, box: Dict, dx: int, dy: int) -> bool:
        """Try to push a box in given direction"""
        new_x = box['x'] + dx
        new_y = box['y'] + dy
        
        # Check bounds
        if (new_x < 0 or new_x >= self.game_state['grid_width'] or 
            new_y < 0 or new_y >= self.game_state['grid_height']):
            return False
        
        # Check if target position is valid
        grid = self.game_state['grid']
        target_cell = grid[new_y][new_x]
        
        if target_cell == 'wall':
            return False
        
        # Check if there's another box at target position
        if self.get_box_at_position(new_x, new_y):
            return False
        
        # Move the box
        box['x'] = new_x
        box['y'] = new_y
        
        # Check if box is now on a target
        target_at_pos = self.get_target_at_position(new_x, new_y)
        box['on_target'] = target_at_pos is not None
        
        return True
    
    def handle_selection(self):
        """Handle space key for selection"""
        player = self.game_state['player']
        
        # Check if there's a box adjacent to player
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        adjacent_boxes = []
        
        for dx, dy in directions:
            check_x = player['x'] + dx
            check_y = player['y'] + dy
            box = self.get_box_at_position(check_x, check_y)
            if box:
                adjacent_boxes.append(box)
        
        if adjacent_boxes:
            # Select/deselect box
            if player['selected_box'] is None:
                player['selected_box'] = adjacent_boxes[0]['id']
            else:
                player['selected_box'] = None
    
    def get_box_at_position(self, x: int, y: int) -> Optional[Dict]:
        """Get box at given position"""
        for box in self.game_state['boxes']:
            if box['x'] == x and box['y'] == y:
                return box
        return None
    
    def get_target_at_position(self, x: int, y: int) -> Optional[Dict]:
        """Get target at given position"""
        for target in self.game_state['targets']:
            if target['x'] == x and target['y'] == y:
                return target
        return None
    
    def update_game_logic(self):
        """Update game state and check win conditions"""
        # Update target completion status
        completed_targets = 0
        for target in self.game_state['targets']:
            box_on_target = self.get_box_at_position(target['x'], target['y'])
            target['completed'] = box_on_target is not None
            if target['completed']:
                completed_targets += 1
        
        # Update score
        score = self.game_state['score']
        score['points'] = completed_targets * 100 + max(0, score['time_bonus'] - score['moves'])
        
        # Check win condition
        if completed_targets == len(self.game_state['targets']):
            score['level_complete'] = True
            self.game_state['game_status'] = 'won'
            
            # Calculate rewards
            rewards = self.game_state['rewards']
            if score['moves'] <= len(self.game_state['boxes']) * 2:
                rewards['move_efficiency_bonus'] = 500
            if score['moves'] <= len(self.game_state['boxes']) * 1.5:
                rewards['perfect_solution'] = True
                score['points'] += 1000
    
    def draw_grid_cell(self, x: int, y: int, cell_type: str):
        """Draw a single grid cell with enhanced visuals"""
        screen_x = GRID_OFFSET_X + x * GRID_SIZE
        screen_y = GRID_OFFSET_Y + y * GRID_SIZE
        rect = pygame.Rect(screen_x, screen_y, GRID_SIZE, GRID_SIZE)
        
        # Draw cell background
        if cell_type == 'wall':
            pygame.draw.rect(self.screen, COLORS['wall'], rect)
            pygame.draw.rect(self.screen, COLORS['wall_highlight'], rect, 2)
            # Add some texture to walls
            for i in range(3):
                for j in range(3):
                    if (i + j) % 2 == 0:
                        mini_rect = pygame.Rect(screen_x + i * 16, screen_y + j * 16, 8, 8)
                        pygame.draw.rect(self.screen, COLORS['wall_highlight'], mini_rect)
        else:
            pygame.draw.rect(self.screen, COLORS['empty'], rect)
            pygame.draw.rect(self.screen, COLORS['grid_line'], rect, 1)
    
    def draw_target(self, target: Dict):
        """Draw a target with animation"""
        screen_x = GRID_OFFSET_X + target['x'] * GRID_SIZE
        screen_y = GRID_OFFSET_Y + target['y'] * GRID_SIZE
        center_x = screen_x + GRID_SIZE // 2
        center_y = screen_y + GRID_SIZE // 2
        
        # Animated pulsing effect
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
        radius = int(15 + pulse * 5)
        
        color = COLORS['target']
        if target['completed']:
            color = COLORS['box_on_target']
        
        # Draw target circles
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, COLORS['target_outline'], (center_x, center_y), radius, 3)
        pygame.draw.circle(self.screen, COLORS['target_outline'], (center_x, center_y), radius // 2, 2)
    
    def draw_box(self, box: Dict):
        """Draw a box with enhanced visuals"""
        screen_x = GRID_OFFSET_X + box['x'] * GRID_SIZE + 5
        screen_y = GRID_OFFSET_Y + box['y'] * GRID_SIZE + 5
        box_size = GRID_SIZE - 10
        rect = pygame.Rect(screen_x, screen_y, box_size, box_size)
        
        # Choose color based on state
        color = COLORS['box_on_target'] if box['on_target'] else COLORS['box']
        outline_color = COLORS['target_outline'] if box['on_target'] else COLORS['box_outline']
        
        # Draw box with 3D effect
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, outline_color, rect, 3)
        
        # Add 3D highlight
        highlight_rect = pygame.Rect(screen_x + 2, screen_y + 2, box_size - 4, box_size // 3)
        highlight_color = tuple(min(255, c + 50) for c in color)
        pygame.draw.rect(self.screen, highlight_color, highlight_rect)
        
        # Draw selection indicator
        player = self.game_state['player']
        if player['selected_box'] == box['id']:
            pygame.draw.rect(self.screen, COLORS['selected'], 
                           pygame.Rect(screen_x - 3, screen_y - 3, box_size + 6, box_size + 6), 3)
    
    def draw_player(self):
        """Draw player with enhanced visuals"""
        player = self.game_state['player']
        screen_x = GRID_OFFSET_X + player['x'] * GRID_SIZE
        screen_y = GRID_OFFSET_Y + player['y'] * GRID_SIZE
        center_x = screen_x + GRID_SIZE // 2
        center_y = screen_y + GRID_SIZE // 2
        
        # Draw player as a circle with animated glow
        glow_radius = int(20 + 3 * abs(pygame.time.get_ticks() % 1000 - 500) / 500.0)
        
        # Glow effect
        for i in range(5):
            alpha = 50 - i * 10
            glow_color = (*COLORS['player'], alpha)
            pygame.draw.circle(self.screen, COLORS['player'], (center_x, center_y), glow_radius - i * 2)
        
        # Main player body
        pygame.draw.circle(self.screen, COLORS['player'], (center_x, center_y), 18)
        pygame.draw.circle(self.screen, COLORS['player_outline'], (center_x, center_y), 18, 3)
        
        # Eyes
        pygame.draw.circle(self.screen, COLORS['text'], (center_x - 6, center_y - 4), 3)
        pygame.draw.circle(self.screen, COLORS['text'], (center_x + 6, center_y - 4), 3)
    
    def draw_ui(self):
        """Draw user interface with score and instructions"""
        # Background for UI
        ui_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 40)
        pygame.draw.rect(self.screen, COLORS['score_bg'], ui_rect)
        
        # Score information
        score = self.game_state['score']
        score_text = f"Score: {score['points']} | Moves: {score['moves']} | Pushes: {score['pushes']}"
        text_surface = self.font.render(score_text, True, COLORS['text'])
        self.screen.blit(text_surface, (10, 10))
        
        # Level and status
        level_text = f"Level: {self.game_state['level']} | Status: {self.game_state['game_status']}"
        level_surface = self.small_font.render(level_text, True, COLORS['text'])
        self.screen.blit(level_surface, (10, SCREEN_HEIGHT - 30))
        
        # Instructions
        instructions = "WASD: Move | SPACE: Select Box | R: New Game"
        inst_surface = self.small_font.render(instructions, True, COLORS['text'])
        self.screen.blit(inst_surface, (10, SCREEN_HEIGHT - 15))
        
        # Win message
        if self.game_state['game_status'] == 'won':
            win_text = "LEVEL COMPLETE! Press R for new level"
            win_surface = self.large_font.render(win_text, True, COLORS['selected'])
            text_rect = win_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Background for win message
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, COLORS['score_bg'], bg_rect)
            pygame.draw.rect(self.screen, COLORS['selected'], bg_rect, 3)
            
            self.screen.blit(win_surface, text_rect)
        
        # Progress indicator
        completed = sum(1 for target in self.game_state['targets'] if target['completed'])
        total = len(self.game_state['targets'])
        progress_text = f"Targets: {completed}/{total}"
        progress_surface = self.font.render(progress_text, True, COLORS['text'])
        self.screen.blit(progress_surface, (SCREEN_WIDTH - 150, 10))
    
    def draw_grid_overlay(self):
        """Draw coordinate grid overlay for user reference"""
        # Draw coordinate numbers
        for x in range(self.game_state['grid_width']):
            screen_x = GRID_OFFSET_X + x * GRID_SIZE + GRID_SIZE // 2
            coord_surface = self.small_font.render(str(x), True, COLORS['grid_line'])
            coord_rect = coord_surface.get_rect(center=(screen_x, GRID_OFFSET_Y - 15))
            self.screen.blit(coord_surface, coord_rect)
        
        for y in range(self.game_state['grid_height']):
            screen_y = GRID_OFFSET_Y + y * GRID_SIZE + GRID_SIZE // 2
            coord_surface = self.small_font.render(str(y), True, COLORS['grid_line'])
            coord_rect = coord_surface.get_rect(center=(GRID_OFFSET_X - 15, screen_y))
            self.screen.blit(coord_surface, coord_rect)
    
    def draw(self):
        """Main drawing function"""
        self.screen.fill(COLORS['background'])
        
        # Draw grid
        grid = self.game_state['grid']
        for y in range(self.game_state['grid_height']):
            for x in range(self.game_state['grid_width']):
                self.draw_grid_cell(x, y, grid[y][x])
        
        # Draw grid overlay
        self.draw_grid_overlay()
        
        # Draw targets first (so they appear under boxes)
        for target in self.game_state['targets']:
            self.draw_target(target)
        
        # Draw boxes
        for box in self.game_state['boxes']:
            self.draw_box(box)
        
        # Draw player
        self.draw_player()
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.handle_input(event)
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = BoxPushingGame()
    game.run()
