import argparse
import pygame
import random
import numpy as np
from collections import deque

# Constants
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

GRID_SIZE = 20

parser = argparse.ArgumentParser(description="Rescue Robot Simulation")
parser.add_argument(
    "-f", "--filename", type=str, default="generated_map.bin", help="Input filename"
)
args = parser.parse_args()


def load_map_from_file(filename):
    with open(filename, "rb") as f:
        rows = int.from_bytes(f.read(1), byteorder="little")
        cols = int.from_bytes(f.read(1), byteorder="little")
        grid = np.fromfile(f, dtype=np.int8).reshape((rows, cols))
    print(f"Loaded map with dimensions: {rows}x{cols}")
    return grid


filename = args.filename
grid = load_map_from_file(filename)
rows, cols = grid.shape
window_width = cols * GRID_SIZE
window_height = rows * GRID_SIZE

pygame.init()
pygame.display.set_caption("Rescue Robot Simulation")
win = pygame.display.set_mode((window_width, window_height + 30))
s = pygame.Surface(win.get_size(), pygame.SRCALPHA)  # transparent surface
clock = pygame.time.Clock()

obstacle_positions = set()
victim_positions = set()
robot_positions = []


def draw_grid():
    for r in range(rows):
        for c in range(cols):
            color = WHITE
            if grid[r][c] == 1:
                color = BLACK
            elif grid[r][c] == 2:
                color = RED
            pygame.draw.rect(
                win, color, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            )
            pygame.draw.rect(
                win, GRAY, (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1
            )


def bfs_to_unexplored(robot):
    start = tuple(robot["pos"])
    known = robot["known_map"]
    rows, cols = known.shape

    visited = np.full((rows, cols), False)
    queue = deque([start])
    visited[start[0]][start[1]] = True
    prev = {}

    while queue:
        r, c = queue.popleft()

        if known[r, c] == 0:
            # Found an unexplored tile
            path = [(r, c)]
            while (r, c) in prev:
                r, c = prev[(r, c)]
                path.append((r, c))
            return path[::-1]  # Reverse the path from start to goal

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < rows
                and 0 <= nc < cols
                and not visited[nr, nc]
                and known[nr, nc] != 1
            ):
                queue.append((nr, nc))
                visited[nr, nc] = True
                prev[(nr, nc)] = (r, c)

    return None  # No unexplored tiles reachable


def move_robot(robot):
    r, c = robot["pos"]
    options = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    position = None
    has_space = False

    if "path" in robot and robot["path"]:
        robot["pos"] = robot["path"].pop(0)
        update_known_map(robot, grid)
        return

    random.shuffle(options)

    for nr, nc in options:
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            # priority to move to a victim
            if grid[nr][nc] == 2:
                position = [nr, nc]
                grid[nr][nc] = 0
                victim_positions.discard((nr, nc))
                break

    if position is None:
        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
                # if not a victim, prefer to move to an empty space
                if grid[nr][nc] == 0 and robot["known_map"][nr][nc] == 0:
                    has_space = True
                    position = [nr, nc]
                    break

    # if no victim or empty space, move to any traversed space
    if position is None and not has_space:
        path = bfs_to_unexplored(robot)
        if path and len(path) > 1:
            robot["path"] = path[1:]  # Skip current pos
            robot["pos"] = robot["path"].pop(0)
            update_known_map(robot, grid)
            return

        for nr, nc in options:
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == -1:
                position = [nr, nc]
                break

    if position is None:
        raise Exception("No valid move found for the robot.")

    # update the robot's position
    robot["pos"] = position
    grid[position[0]][position[1]] = -1
    update_known_map(robot, grid)


def draw_known_map(win, robot):
    known = robot["known_map"]

    for r in range(known.shape[0]):
        for c in range(known.shape[1]):
            val = known[r][c]
            x = c * GRID_SIZE
            y = r * GRID_SIZE

            if val == -1:
                color = (255, 255, 0, 100)  # traversed
            elif val == 0:
                color = (0, 255, 0, 100)  # transparent green
            else:
                continue  # skip if unknown

            pygame.draw.rect(s, color, (x, y, GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(s, GRAY, (x, y, GRID_SIZE, GRID_SIZE), 1)

    win.blit(s, (0, 0))  # overlay on top of real map


def draw_robots():
    t = pygame.Surface(s.get_size(), pygame.SRCALPHA)  # transparent surface
    t.fill((0, 0, 0, 0))  # clear the surface
    for i, robot in enumerate(robot_positions):
        r, c = robot["pos"]
        # draw_known_map(win, robot)
        pygame.draw.circle(
            t,
            BLUE,
            (c * GRID_SIZE + GRID_SIZE // 2, r * GRID_SIZE + GRID_SIZE // 2),
            GRID_SIZE // 3,
        )
        win.blit(t, (0, 0))  # overlay on top of real map


def draw_timer(win, ticks, rows):
    font = pygame.font.SysFont(None, 24)
    time_text = font.render(f"Ticks: {ticks}", True, (0, 0, 0))
    win.blit(time_text, (5, rows * GRID_SIZE + 5))


def setup():
    # read the grid and set up the positions
    for r in range(rows):
        for c in range(cols):
            at = grid[r][c]
            if at == 1:
                obstacle_positions.add((r, c))
            elif at == 2:
                victim_positions.add((r, c))
            elif at == 3:
                robot_positions.append(
                    {"pos": [r, c], "known_map": np.full((rows, cols), -2)}
                )


def update_known_map(robot, true_map):
    r, c = robot["pos"]
    options = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]

    # Mark the current position as traversed
    robot["known_map"][r][c] = -1
    # Mark adjacent positions based on the true map
    for nr, nc in options:
        if 0 <= nr < rows and 0 <= nc < cols and robot["known_map"][nr][nc] == -2:
            robot["known_map"][nr][nc] = true_map[nr][nc]


def main():
    run = True
    ticks = 0
    for robot in robot_positions:
        update_known_map(robot, grid)

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        win.fill(WHITE)
        draw_grid()
        draw_robots()
        draw_timer(win, ticks, rows)
        pygame.display.update()

        clock.tick(FPS)
        ticks += 1
        for robot in robot_positions:
            move_robot(robot)
        if len(victim_positions) == 0:
            print("All victims rescued!")
            run = False

    print(f"Simulation finished in {ticks} ticks.")
    pygame.quit()


if __name__ == "__main__":
    setup()
    main()
