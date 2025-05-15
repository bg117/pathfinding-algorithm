# --- Imports ---
import argparse  # For parsing command-line arguments
import pygame  # For GUI and visualization
import random  # For randomizing robot movement
import numpy as np  # For efficient matrix/grid manipulation
from collections import deque  # For BFS queue

# --- Constants ---
FPS = 30  # Frames per second for the simulation
GRID_SIZE = 20  # Size of each grid cell in pixels

# Color definitions (RGB)
WHITE, BLACK, GRAY, RED, BLUE, GREEN, YELLOW = (
    (255, 255, 255),
    (0, 0, 0),
    (180, 180, 180),
    (255, 0, 0),
    (0, 0, 255),
    (0, 255, 0),
    (255, 255, 0),
)

# Map cell types
UNKNOWN = -2  # Unexplored cell (for robot's known map)
TRAVERSED = -1  # Already passed cell
FREE = 0  # Free space
OBSTACLE = 1  # Wall or obstacle
VICTIM = 2  # Person to rescue
ROBOT = 3  # Starting location of a robot


# --- Argument Parsing ---
def parse_args():
    # Get filename from command-line argument
    parser = argparse.ArgumentParser(description="Rescue Robot Simulation")
    parser.add_argument(
        "-f", "--filename", type=str, default="generated_map.bin", help="Input filename"
    )
    return parser.parse_args()


# --- Utilities ---
def load_map(filename):
    # Load binary-encoded map from file
    with open(filename, "rb") as f:
        rows = int.from_bytes(f.read(1), byteorder="little")
        cols = int.from_bytes(f.read(1), byteorder="little")
        grid = np.fromfile(f, dtype=np.int8).reshape((rows, cols))
    print(f"Loaded map: {rows}x{cols}")
    return grid


def draw_grid(surface, grid):
    surface.fill(WHITE)

    # Draw the full grid, showing walls and victims
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            color = {OBSTACLE: BLACK, VICTIM: RED}.get(
                grid[r, c], WHITE
            )  # Black for obstacle, red for victim
            pygame.draw.rect(
                surface, color, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            )
            pygame.draw.rect(
                surface, GRAY, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1
            )


def draw_known_map(known_map, surface):
    # Adjust transparency based on number of robots, minimum 50
    transparency = 200
    # Show what the robot has discovered so far
    for r in range(known_map.shape[0]):
        for c in range(known_map.shape[1]):
            block = known_map[r][c]
            if block == TRAVERSED:
                color = (255, 255, 0, transparency)  # Yellow with transparency
            elif block == FREE:
                color = (0, 255, 0, transparency)  # Green with transparency
            else:
                continue
            pygame.draw.rect(
                surface, color, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            )
            pygame.draw.rect(
                surface,
                GRAY,
                (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE),
                1,
            )


def draw_timer(surface, ticks, rows):
    # Draw the timer showing how many ticks have passed
    font = pygame.font.SysFont(None, 24)
    surface.blit(font.render(f"Ticks: {ticks}", True, BLACK), (5, rows * GRID_SIZE + 5))


# --- Robot Class ---
class RescueRobot:
    def __init__(self, start_pos, map_shape, known_map):
        self.pos = tuple(start_pos)  # Current position
        self.path = []  # Path to follow
        self.known_map = known_map  # Map the robot builds over time
        self.update_known_map()  # Explore surroundings initially

    def update_known_map(self):
        # Update the robot’s known map based on current position
        r, c = self.pos
        self.known_map[r][c] = TRAVERSED
        for nr, nc in [
            (r + 1, c),
            (r - 1, c),
            (r, c + 1),
            (r, c - 1),
        ]:  # Up, Down, Left, Right
            if (
                0 <= nr < self.known_map.shape[0]
                and 0 <= nc < self.known_map.shape[1]
                and self.known_map[nr][nc] == UNKNOWN
            ):
                self.known_map[nr][nc] = grid[nr][nc]  # Reveal cell value

    def bfs_to_unexplored(self):
        rows, cols = self.known_map.shape
        visited = set()
        queue = deque()
        queue.append((self.pos, []))  # (current_pos, path_so_far)
        visited.add(self.pos)

        while queue:
            (r, c), path = queue.popleft()

            if self.known_map[r][c] == UNKNOWN:
                return path  # Found it, return path to this UNKNOWN

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                next_pos = (nr, nc)
                if 0 <= nr < rows and 0 <= nc < cols:
                    if next_pos not in visited:
                        tile = self.known_map[nr][nc]
                        if tile != OBSTACLE and tile != VICTIM:
                            visited.add(next_pos)
                            queue.append((next_pos, path + [next_pos]))

        return []  # No path found

    def move(self):
        # Main decision logic for robot movement

        # If following a planned path, continue
        if self.path:
            next = self.path.pop(0)

            self.pos = next
            self.update_known_map()

            next_next = self.path[0] if self.path else None
            # check if next next cell is valid (not an obstacle nor victim)
            # if not, remove it from the path
            if next_next:
                at_next = self.known_map[next_next[0]][next_next[1]]
                if at_next == VICTIM or at_next == OBSTACLE:
                    self.path.pop(0)

            return

        r, c = self.pos
        options = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        random.shuffle(options)  # Randomize movement direction

        # Priority 1: Rescue nearby victim
        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols:
                if self.known_map[nr][nc] == VICTIM:
                    self.pos = (nr, nc)
                    victim_positions.discard((nr, nc))  # Remove victim from global set
                    grid[nr][nc] = 0  # Mark as cleared
                    self.update_known_map()
                    return

        # Priority 2: Move to adjacent known free cell
        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols and self.known_map[nr][nc] == FREE:
                self.pos = (nr, nc)
                self.update_known_map()
                return

        # Priority 3: Find path to nearest unexplored cell
        path = self.bfs_to_unexplored()
        if path and len(path) > 1:
            self.path = path[1:]
            self.move()
            return

        # Priority 4: Go back to traversed cell if stuck
        for nr, nc in options:
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and self.known_map[nr][nc] == TRAVERSED
            ):
                self.pos = (nr, nc)
                self.update_known_map()
                return

    def draw(self, surface):
        # Draw robot as a blue circle
        r, c = self.pos
        pygame.draw.circle(
            surface,
            BLUE,
            (c * GRID_SIZE + GRID_SIZE // 2, r * GRID_SIZE + GRID_SIZE // 2),
            GRID_SIZE // 3,
        )


# --- Initialization ---
args = parse_args()
grid = load_map(args.filename)
known_map = np.full(grid.shape, UNKNOWN, dtype=np.int8)  # Initialize known map
rows, cols = grid.shape

# Set up Pygame window
window_size = (cols * GRID_SIZE, rows * GRID_SIZE + 30)
pygame.init()
pygame.display.set_caption("Rescue Robot Simulation")
win = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

robots = []  # List of robots
victim_positions = set()  # Track all victim positions

# Populate grid with robots and victims
for r in range(rows):
    for c in range(cols):
        if grid[r][c] == VICTIM:
            victim_positions.add((r, c))
        elif grid[r][c] == ROBOT:
            robots.append(RescueRobot((r, c), (rows, cols), known_map))


# --- Main Loop ---
def main():
    ticks = 0
    run = True
    overlay = pygame.Surface(win.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 0))

    while run:
        # Handle quitting
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw_grid(win, grid)

        # Draw each robot’s known map overlay
        draw_known_map(known_map, overlay)
        win.blit(overlay, (0, 0))

        # Draw each robot
        for robot in robots:
            robot.draw(win)

        draw_timer(win, ticks, rows)
        pygame.display.update()
        clock.tick(FPS)

        # Move all robots
        for robot in robots:
            robot.move()

        # Check if all victims are rescued
        if not victim_positions:
            print("All victims rescued!")
            run = False

        ticks += 1

    print(f"Simulation finished in {ticks} ticks.")
    pygame.quit()


# --- Entry Point ---
if __name__ == "__main__":
    main()
