# --- Imports ---
import argparse  # For parsing command-line arguments
import pygame  # For GUI and visualization
import random  # For randomizing robot movement
import numpy as np  # For efficient matrix/grid manipulation
from collections import deque  # For BFS queue

# --- Constants ---
FPS = 60  # Frames per second for the simulation
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


def draw_timer(surface, ticks, rows):
    # Draw the timer showing how many ticks have passed
    font = pygame.font.SysFont(None, 24)
    surface.blit(font.render(f"Ticks: {ticks}", True, BLACK), (5, rows * GRID_SIZE + 5))


# --- Robot Class ---
class RescueRobot:
    def __init__(self, start_pos, map_shape):
        self.pos = tuple(start_pos)  # Current position
        self.path = []  # Path to follow
        self.known_map = np.full(
            map_shape, UNKNOWN, dtype=np.int8
        )  # Map the robot builds over time
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
        # Perform BFS to find a path to unexplored areas
        visited = np.full(self.known_map.shape, False)
        pos = self.pos
        queue = deque([pos])
        visited[pos[0]][pos[1]] = True
        prev = {}

        while queue:
            r, c = queue.popleft()
            if self.known_map[r][c] == UNKNOWN:
                # Found unexplored free space
                path = [(r, c)]
                while (r, c) in prev:
                    r, c = prev[(r, c)]
                    path.append((r, c))
                return path[::-1]  # Return reversed path

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < self.known_map.shape[0]
                    and 0 <= nc < self.known_map.shape[1]
                    and not visited[nr][nc]
                    and self.known_map[nr][nc] != OBSTACLE
                ):
                    visited[nr][nc] = True
                    queue.append((nr, nc))
                    prev[(nr, nc)] = (r, c)
        return None  # No unexplored area reachable

    def move(self):
        # Main decision logic for robot movement

        # If following a planned path, continue
        if self.path:
            next = self.path.pop(0)
            # Double check if the next cell is valid (not an obstacle)
            if self.known_map[next[0]][next[1]] == OBSTACLE:
                # If it's an obstacle, find a new path
                path = self.bfs_to_unexplored()
                if path:
                    self.path = path[1:]
                    next = self.path.pop(0)
            self.pos = next
            self.update_known_map()
            return

        r, c = self.pos
        options = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        random.shuffle(options)  # Randomize movement direction

        # Priority 1: Rescue nearby victim
        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == VICTIM:
                    self.pos = (nr, nc)
                    victim_positions.discard((nr, nc))  # Remove victim from global set
                    grid[nr][nc] = 0  # Mark as cleared
                    self.update_known_map()
                    return

        # Priority 2: Move to adjacent known free cell
        for nr, nc in options:
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and grid[nr][nc] == FREE
                and self.known_map[nr][nc] == FREE
            ):
                self.pos = (nr, nc)
                self.update_known_map()
                return

        # Priority 3: Find path to nearest unexplored cell
        path = self.bfs_to_unexplored()
        if path and len(path) > 1:
            self.path = path[1:]
            self.pos = self.path.pop(0)
            self.update_known_map()
            return

        # Priority 4: Go back to traversed cell if stuck
        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == TRAVERSED:
                self.pos = (nr, nc)
                self.update_known_map()
                return

    def draw_known_map(self, surface):
        # Adjust transparency based on number of robots, minimum 50
        transparency = max(255 // len(robots), 75)
        # Show what the robot has discovered so far
        for r in range(self.known_map.shape[0]):
            for c in range(self.known_map.shape[1]):
                block = self.known_map[r][c]
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
            robots.append(RescueRobot((r, c), (rows, cols)))


# --- Main Loop ---
def main():
    ticks = 0
    run = True
    overlays = []

    # Create len(robots) overlays for each robot
    for _ in range(len(robots)):
        overlay = pygame.Surface(win.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))
        overlays.append(overlay)

    while run:
        # Handle quitting
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw_grid(win, grid)

        # Draw each robot’s known map overlay
        for i, robot in enumerate(robots):
            overlay = overlays[i]
            robot.draw_known_map(overlay)
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
