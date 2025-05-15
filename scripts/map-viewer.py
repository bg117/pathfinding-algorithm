import pygame
import numpy as np
import argparse

# --- Constants ---
GRID_SIZE = 20
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

OBSTACLE = 1
VICTIM = 2
ROBOT = 3


# --- Argument Parsing ---
def parse_args():
    parser = argparse.ArgumentParser(description="Map Viewer")
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        default="generated_map.bin",
        help="Path to the binary map file",
    )
    return parser.parse_args()


# --- Map Loader ---
def load_map(filename):
    with open(filename, "rb") as f:
        rows = int.from_bytes(f.read(1), byteorder="little")
        cols = int.from_bytes(f.read(1), byteorder="little")
        grid = np.fromfile(f, dtype=np.int8).reshape((rows, cols))
    print(f"Loaded map: {rows}x{cols}")
    return grid


# --- Grid Drawer ---
def draw_grid(surface, grid):
    rows, cols = grid.shape
    for r in range(rows):
        for c in range(cols):
            color = {OBSTACLE: BLACK, VICTIM: RED, ROBOT: BLUE}.get(grid[r, c], WHITE)
            pygame.draw.rect(
                surface, color, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            )
            pygame.draw.rect(
                surface, GRAY, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1
            )


# --- Main ---
def main():
    args = parse_args()
    grid = load_map(args.filename)
    rows, cols = grid.shape

    pygame.init()
    win = pygame.display.set_mode((cols * GRID_SIZE, rows * GRID_SIZE))
    pygame.display.set_caption("Map Viewer")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        win.fill(WHITE)
        draw_grid(win, grid)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
