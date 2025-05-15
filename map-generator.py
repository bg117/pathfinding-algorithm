import argparse
import numpy as np
import random
import time


def generate_map(rows, cols, num_obstacles, num_victims, num_robots, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    grid = np.zeros((rows, cols), dtype=np.int8)

    # Place obstacles
    grid = place_at(grid, 1, num_obstacles, rows, cols)

    # Place victims
    grid = place_at(grid, 2, num_victims, rows, cols)

    # Place robots
    grid = place_at(grid, 3, num_robots, rows, cols)

    return grid


def place_at(grid, at, num, rows, cols):
    count = 0
    while count < num:
        r, c = random.randint(0, rows - 1), random.randint(0, cols - 1)
        if grid[r, c] == 0:
            grid[r, c] = at
            count += 1
    return grid


def save_map_to_file(grid, rows, cols, filename):
    with open(filename, "wb") as f:
        f.write(rows.to_bytes(1, byteorder="little"))
        f.write(cols.to_bytes(1, byteorder="little"))
        grid.tofile(f)


parser = argparse.ArgumentParser(
    description="Generate a random map for the rescue robot simulation."
)
parser.add_argument(
    "-r", "--rows", type=int, default=25, help="Number of rows in the map"
)
parser.add_argument(
    "-c", "--cols", type=int, default=25, help="Number of columns in the map"
)
parser.add_argument(
    "-o", "--obstacles", type=int, default=100, help="Number of obstacles"
)
# mutually exclusive with -r and -c, define square map
parser.add_argument(
    "-s", "--square", type=int, help="Size of the square map (rows and cols)"
)
parser.add_argument("-v", "--victims", type=int, default=20, help="Number of victims")
parser.add_argument("-b", "--robots", type=int, default=5, help="Number of robots")
parser.add_argument(
    "-f", "--filename", type=str, default="generated_map.bin", help="Output filename"
)
args = parser.parse_args()


if __name__ == "__main__":
    rows = args.square if args.square else args.rows
    cols = args.square if args.square else args.cols
    num_obstacles = args.obstacles
    num_victims = args.victims
    num_robots = args.robots
    filename = args.filename

    if rows <= 0 or cols <= 0:
        raise ValueError("Rows and columns must be positive integers.")

    if num_obstacles < 0 or num_victims < 0 or num_robots < 0:
        raise ValueError(
            "Number of obstacles, victims, and robots must be non-negative."
        )

    if num_obstacles + num_victims + num_robots > rows * cols:
        raise ValueError(
            "Total number of obstacles, victims, and robots exceeds grid size."
        )

    grid = generate_map(
        rows, cols, num_obstacles, num_victims, num_robots, seed=int(time.time())
    )
    save_map_to_file(grid, rows, cols, filename)
    print(f"Map generated and saved to '{filename}'")
