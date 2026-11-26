"""
RRT task: starter file
======================
Fill in the two functions below, then check your work with the grader:

    python Task_RRT_grader.py student_starter.py

Rules the grader relies on (do not change the names or the parameters):
  * grid cells:   0 = free      1 = obstacle      2 = explored point (written by rrt)
  * the robot is a  robot_size x robot_size  square (default 3 x 3)
  * a tree point (r, c) is the robot's TOP-LEFT cell
  * a grid is a list of lists (a numpy array also works)
"""
import math
import random

FREE, OBSTACLE, EXPLORED = 0, 1, 2


# =============================================================================
# FUNCTION 1: create_grid
# =============================================================================

def create_grid(n, k, m):
  grid = [[FREE] * n for _ in range(n)]
  for _ in range(k):
      r = random.randint(0, n - m)
      c = random.randint(0, n - m)
      for i in range(r, r + m):
          for j in range(c, c + m):
              grid[i][j] = OBSTACLE
  return grid

def collides(grid, r, c, size):
    n = len(grid)
    for i in range(r, r + size):
        for j in range(c, c + size):
            if not (0 <= i < n and 0 <= j < n) or grid[i][j] == OBSTACLE:
                return True
    return False


def rrt(grid, start=(0, 0), goal=None, max_iters=5000, step=2.0, robot_size=3):
    explored = [row[:] for row in grid]
    tree = [tuple(start)]
    explored[start[0]][start[1]] = EXPLORED
    n = len(grid)
    if goal is None:
        goal = (n - robot_size, n - robot_size)

    for _ in range(max_iters):
        sample = (
            goal
            if random.random() < 0.5
            else (random.randint(0, n - robot_size), random.randint(0, n - robot_size))
        )
        nearest = min(tree, key=lambda x: math.dist(x, sample))
        d = math.dist(nearest, sample)
        if d == 0:
            continue

        move = min(step, d)
        dr = (sample[0] - nearest[0]) * move / d
        dc = (sample[1] - nearest[1]) * move / d
        new = (nearest[0] + dr, nearest[1] + dc)

        rr, cc = round(new[0]), round(new[1])
        if collides(grid, rr, cc, robot_size):
            continue

        tree.append(new)
        explored[rr][cc] = EXPLORED
        if math.dist(new, goal) <= 1:
            break

    return explored


# =============================================================================
# A tiny viewer to look at your result:  python student_starter.py
# =============================================================================
def show(grid):
    symbols = {FREE: ".", OBSTACLE: "#", EXPLORED: "o"}
    for row in grid:
        print(" ".join(symbols.get(int(v), "?") for v in row))


if __name__ == "__main__":
    random.seed(1)
    g = create_grid(20, 5, 3)
    if g is None:
        print("create_grid returns None: write it first.")
    else:
        print("The grid ( . free   # obstacle ):")
        show(g)
        out = rrt(g, start=(0, 0), goal=(17, 17), max_iters=2000)
        if out is None:
            print("rrt returns None: write it next.")
        else:
            print("\nAfter rrt ( o explored ):")
            show(out)
