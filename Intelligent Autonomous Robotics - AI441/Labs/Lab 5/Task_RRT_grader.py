#!/usr/bin/env python3
"""Auto-grader for the "random grid + RRT (4-corner robot)" assignment.

    python Task_RRT_grader.py student_file.py
    python Task_RRT_grader.py student_file.py --robot-size 3 --max-mark 10

Conventions (see the explainer page): 0 = free, 1 = obstacle, 2 = explored.
The robot is a size x size square; the tree point (r, c) is its TOP-LEFT cell and
its 4 corners are (r,c) (r,c+size-1) (r+size-1,c) (r+size-1,c+size-1).
"""
import argparse
import copy
import importlib.util
import inspect
import math
import random
import signal
import sys
import time
import traceback

try:
    import numpy as np
except ImportError:                                     # numpy is optional
    np = None

FREE, OBSTACLE, EXPLORED = 0, 1, 2
ALIASES = {                                             # parameter names we accept
    "start": ["start", "start_pos", "source", "begin"],
    "goal": ["goal", "target", "end", "goal_pos"],
    "iters": ["max_iters", "max_iter", "iterations", "n_iter", "n_iters", "num_iters", "max_steps", "steps", "num_steps"],
    "step": ["step", "step_size", "delta", "eta"],
    "robot": ["robot_size", "robot", "robot_w", "size"],
}
TIME_LIMIT = 60                                         # seconds per test (change with --time-limit)


class GraderError(Exception):
    pass


class NotApplicable(Exception):
    pass


# ------------------------------------------------------------------ loading
def load_module(path):
    spec = importlib.util.spec_from_file_location("student_solution", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_function(mod, explicit, candidates, keyword):
    if explicit:
        fn = getattr(mod, explicit, None)
        if callable(fn):
            return fn
        raise GraderError(f"function '{explicit}' not found")
    for name in candidates:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    for name, obj in vars(mod).items():
        if inspect.isfunction(obj) and obj.__module__ == mod.__name__ and keyword in name.lower():
            return obj
    raise GraderError(f"no function with '{keyword}' in its name was found")


class Student:
    def __init__(self, grid_fn, rrt_fn, robot_size):
        self.grid_fn, self.rrt_fn, self.size = grid_fn, rrt_fn, robot_size
        self.params = inspect.signature(rrt_fn).parameters
        sample = grid_fn(6, 1, 2)
        self.numpy_grids = np is not None and isinstance(sample, np.ndarray)

    def has(self, logical):
        return any(a in self.params for a in ALIASES[logical])

    def make_grid(self, n, k, m):
        return self.grid_fn(n, k, m)

    def like(self, g):                                  # give hand-made grids the student's own type
        return np.array(g, dtype=int) if self.numpy_grids else copy.deepcopy(g)

    def run(self, g, start=(0, 0), goal=None, iters=None, step=None):
        kwargs = {}
        wanted = [("start", start), ("goal", goal), ("iters", iters), ("step", step), ("robot", self.size)]
        for logical, value in wanted:
            if value is None:
                continue
            for alias in ALIASES[logical]:
                if alias in self.params:
                    kwargs[alias] = value
                    break
            else:
                if logical == "goal":
                    raise GraderError("rrt() has no parameter for the goal (expected 'goal')")
        out = self.rrt_fn(g, **kwargs)
        if isinstance(out, tuple) and out and looks_like_grid(out[0]):
            out = out[0]
        return out


def looks_like_grid(x):
    try:
        return len(x) > 0 and len(x[0]) > 0
    except TypeError:
        return False


def lists(g):
    return [[int(v) for v in row] for row in g]


# ------------------------------------------------------------------ test kit
TESTS = []


def test(group, title):
    def deco(fn):
        TESTS.append((group, title, fn))
        return fn
    return deco


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def seed(s):
    random.seed(s)
    if np is not None:
        np.random.seed(s)


def empty(n):
    return [[0] * n for _ in range(n)]


def fill(g, r0, r1, c0, c1):
    for r in range(r0, r1):
        for c in range(c0, c1):
            g[r][c] = 1
    return g


def cells(g, v):
    return [(r, c) for r, row in enumerate(g) for c, x in enumerate(row) if x == v]


def in_full_block(g, r, c, m):
    n = len(g)
    for a in range(max(0, r - m + 1), min(r, n - m) + 1):
        for b in range(max(0, c - m + 1), min(c, n - m) + 1):
            if all(g[i][j] == 1 for i in range(a, a + m) for j in range(b, b + m)):
                return True
    return False


def reached(out, goal, tol=2):
    return any(abs(r - goal[0]) <= tol and abs(c - goal[1]) <= tol for r, c in cells(out, EXPLORED))


def corners_ok(orig, r, c, s):
    n = len(orig)
    for i, j in [(r, c), (r, c + s - 1), (r + s - 1, c), (r + s - 1, c + s - 1)]:
        if not (0 <= i < n and 0 <= j < n) or orig[i][j] == 1:
            return False
    return True


def blocky_grid(n=40):                                  # fixed obstacles, dense enough to test the corners
    g = empty(n)
    for r0, c0, m in [(6, 8, 4), (10, 20, 5), (22, 6, 6), (18, 30, 4), (30, 14, 5), (4, 30, 3), (28, 32, 4), (14, 12, 3)]:
        fill(g, r0, r0 + m, c0, c0 + m)
    return g


# ------------------------------------------------------------------ Part A: create_grid
@test("A", "grid has the right shape and only 0/1 values")
def a1(S):
    for n, k, m in [(10, 3, 2), (25, 10, 4), (8, 0, 3), (30, 5, 5)]:
        g = lists(S.make_grid(n, k, m))
        check(len(g) == n and all(len(row) == n for row in g), f"expected an {n}x{n} grid")
        check({v for row in g for v in row} <= {0, 1}, "grid may only contain 0 and 1")


@test("A", "k = 0 gives a completely free grid")
def a2(S):
    g = lists(S.make_grid(12, 0, 3))
    check(all(v == 0 for row in g for v in row), "found obstacles although k = 0")


@test("A", "one obstacle is exactly one m x m block")
def a3(S):
    for s in range(10):
        seed(s)
        g = lists(S.make_grid(15, 1, 4))
        ones = cells(g, 1)
        check(len(ones) == 16, f"k=1, m=4 must give 16 obstacle cells, got {len(ones)}")
        rows, cols = [r for r, _ in ones], [c for _, c in ones]
        check(max(rows) - min(rows) == 3 and max(cols) - min(cols) == 3, "the 16 cells must form a 4x4 square")


@test("A", "every obstacle cell belongs to a complete m x m block")
def a4(S):
    for s in range(20):
        seed(s)
        g = lists(S.make_grid(20, 6, 3))
        for r, c in cells(g, 1):
            check(in_full_block(g, r, c, 3), f"cell ({r},{c}) is an obstacle but not part of a full 3x3 block")


@test("A", "k blocks are placed (not k-1, not k+1)")
def a5(S):
    for s in range(5):
        seed(s)
        g = lists(S.make_grid(200, 7, 3))
        count = len(cells(g, 1))
        check(55 <= count <= 63, f"7 blocks of 3x3 should give about 63 cells (55-63 with overlaps), got {count}")


@test("A", "blocks stay inside the grid but may touch every border")
def a6(S):
    top = bottom = left = right = False
    for s in range(30):
        seed(s)
        g = lists(S.make_grid(10, 40, 3))
        check(len(g) == 10 and all(len(r) == 10 for r in g), "grid size changed (block stuck out of the grid?)")
        for r, c in cells(g, 1):
            check(in_full_block(g, r, c, 3), "cut-off block at the border")
        top |= any(g[0]); bottom |= any(g[-1])
        left |= any(row[0] for row in g); right |= any(row[-1] for row in g)
    check(top and bottom and left and right, "obstacles never touched one of the borders (positions not covering the whole range)")


@test("A", "obstacles are random (different calls give different grids)")
def a7(S):
    seed(7)
    grids = [str(lists(S.make_grid(30, 8, 3))) for _ in range(6)]
    check(len(set(grids)) > 1, "six calls returned identical grids")


# ------------------------------------------------------------------ Part B: rrt
@test("B", "returns an n x n grid with values 0 / 1 / 2")
def b1(S):
    seed(1)
    out = lists(S.run(S.like(empty(20)), goal=(17, 17), iters=300))
    check(len(out) == 20 and all(len(r) == 20 for r in out), "output grid has the wrong shape")
    check({v for row in out for v in row} <= {0, 1, 2}, "output may only contain 0, 1, 2")


@test("B", "the start point is marked as explored")
def b2(S):
    seed(2)
    out = lists(S.run(S.like(empty(20)), start=(0, 0), goal=(17, 17), iters=200))
    check(out[0][0] == 2, "cell (0,0) should be marked 2 (the start is the first explored point)")


@test("B", "the start argument is used")
def b3(S):
    if not S.has("start"):
        raise NotApplicable("rrt() has no start parameter")
    seed(3)
    out = lists(S.run(S.like(empty(25)), start=(10, 12), goal=(22, 22), iters=30))
    check(out[10][12] == 2, "start=(10,12) was not marked as explored")


@test("B", "obstacles stay untouched and nothing is explored inside them")
def b4(S):
    orig = blocky_grid()
    for s in range(3):
        seed(s)
        out = lists(S.run(S.like(orig), goal=(37, 37), iters=1500))
        for r, c in cells(orig, 1):
            check(out[r][c] == 1, f"obstacle cell ({r},{c}) was changed to {out[r][c]}")
        for r, c in cells(out, 2):
            check(orig[r][c] == 0, f"explored point ({r},{c}) lies inside an obstacle")


@test("B", "the robot's 4 corners are all checked")
def b5(S):
    orig, size = blocky_grid(), S.size
    for s in range(3):
        seed(s)
        out = lists(S.run(S.like(orig), goal=(40 - size, 40 - size), iters=1500))
        for r, c in cells(out, 2):
            check(corners_ok(orig, r, c, size), f"explored point ({r},{c}): a corner of the {size}x{size} robot hits an obstacle or leaves the map")


@test("B", "new points are only a small step away from the tree")
def b_step(S):
    if not S.has("step"):
        raise NotApplicable("rrt() has no step parameter")
    seed(21)
    out = lists(S.run(S.like(empty(40)), goal=(37, 37), iters=500, step=2.0))
    pts = cells(out, 2)
    check(len(pts) >= 10, "the tree hardly grew")
    for r, c in pts:
        near = [math.dist((r, c), q) for q in pts if q != (r, c)]
        check(near and min(near) <= 2.0 + 2.0, f"explored point ({r},{c}) is far from every other point: the tree must grow one small step at a time")


@test("B", "the robot cannot cross a solid wall")
def b6(S):
    size = S.size
    g = fill(empty(30), 0, 30, 10, 14)                  # 4-cell-thick wall, no gap
    seed(6)
    out = lists(S.run(S.like(g), goal=(30 - size, 30 - size), iters=1200))
    pts = cells(out, 2)
    check(len(pts) >= 5, "the tree hardly grew at all")
    check(all(c <= 10 - size for _, c in pts), "the tree crossed (or entered) the wall")
    check(not reached(out, (30 - size, 30 - size)), "goal behind a solid wall must not be reached")


@test("B", "finds its way through a gap in the wall")
def b7(S):
    size = S.size
    g = fill(empty(30), 0, 18, 10, 14)                  # wall with an opening at the bottom
    goal = (30 - size, 30 - size)
    wins = 0
    for s in range(5):
        seed(s)
        wins += reached(lists(S.run(S.like(g), goal=goal, iters=3000)), goal)
    check(wins >= 4, f"reached the goal in only {wins} of 5 runs (needs 4)")


@test("B", "stops as soon as the goal is reached")
def b8(S):
    goal = (30 - S.size, 30 - S.size)
    seed(8)
    out = lists(S.run(S.like(empty(30)), goal=goal, iters=5000))
    check(reached(out, goal), "goal not reached on an empty grid")
    used = len(cells(out, 2))
    check(used <= 0.35 * 900, f"{used} explored cells: the algorithm kept running after reaching the goal")


@test("B", "the goal is chosen as the sample about 50% of the time")
def b9(S):
    if not S.has("iters"):
        raise NotApplicable("rrt() has no iterations parameter")
    goal = (60 - S.size, 60 - S.size)
    wins = 0
    for s in range(5):
        seed(s)
        wins += reached(lists(S.run(S.like(empty(60)), goal=goal, iters=300)), goal)
    check(wins >= 4, f"reached the far corner in {wins} of 5 runs within 300 steps: is the goal bias missing?")


@test("B", "an unreachable goal (inside an obstacle) ends cleanly")
def b10(S):
    g = fill(empty(25), 18, 24, 18, 24)
    seed(10)
    out = lists(S.run(S.like(g), goal=(20, 20), iters=600))
    check(out[20][20] == 1, "the goal cell inside the obstacle must stay 1")
    check(len(cells(out, 2)) >= 1, "nothing explored")


@test("B", "one iteration adds at most one new point")
def b11(S):
    if not S.has("iters"):
        raise NotApplicable("rrt() has no iterations parameter")
    seed(11)
    out = lists(S.run(S.like(empty(25)), goal=(22, 22), iters=1))
    n = len(cells(out, 2))
    check(1 <= n <= 2, f"after max_iters=1 there should be 1-2 explored points, found {n}")


@test("B", "the robot never leaves the map (goal in the very corner)")
def b_edge(S):
    size, n = S.size, 20
    seed(13)
    out = lists(S.run(S.like(empty(n)), goal=(n - 1, n - 1), iters=800))
    check(len(cells(out, 2)) >= 5, "the tree hardly grew")
    for r, c in cells(out, 2):
        check(corners_ok(empty(n), r, c, size), f"explored point ({r},{c}): a corner of the {size}x{size} robot is outside the map")


@test("B", "full pipeline: create_grid(...) then rrt(start=(0,0))")
def b12(S):
    n, size, ran = 30, S.size, 0
    for s in range(20):
        seed(s)
        g = lists(S.make_grid(n, 4, 3))
        if not corners_ok(g, 0, 0, size):
            continue                                    # random obstacle sits on the start: skip this seed
        ran += 1
        out = lists(S.run(S.like(g), start=(0, 0), goal=(n - size, n - size), iters=1500))
        check(out[0][0] == 2, "start not marked")
        for r, c in cells(g, 1):
            check(out[r][c] == 1, "obstacle changed")
        for r, c in cells(out, 2):
            check(corners_ok(g, r, c, size), f"explored point ({r},{c}) is not collision-free")
        if ran == 4:
            break
    check(ran >= 1, "no usable random grid was produced (is the start always blocked?)")


# ------------------------------------------------------------------ runner
class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("student_file")
    ap.add_argument("--grid-fn"); ap.add_argument("--rrt-fn")
    ap.add_argument("--robot-size", type=int, default=3)
    ap.add_argument("--max-mark", type=float, default=10)
    ap.add_argument("--time-limit", type=int, default=60, help="seconds allowed per test")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    global TIME_LIMIT
    TIME_LIMIT = args.time_limit

    try:
        mod = load_module(args.student_file)
        S = Student(find_function(mod, args.grid_fn, ["create_grid", "generate_grid", "make_grid"], "grid"),
                    find_function(mod, args.rrt_fn, ["rrt", "RRT", "run_rrt"], "rrt"), args.robot_size)
    except Exception as e:
        print(f"CANNOT LOAD THE SOLUTION: {e}")
        if not args.quiet:
            traceback.print_exc()
        return 2

    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _alarm)
    passed = 0
    print(f"Grading {args.student_file}  (robot size {args.robot_size})\n")
    for i, (group, title, fn) in enumerate(TESTS, 1):
        label = f"{group}{sum(1 for g, _, _ in TESTS[:i] if g == group)}"
        t0 = time.time()
        try:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(TIME_LIMIT)
            fn(S)
            status, note = "PASS", ""
            passed += 1
        except NotApplicable as e:
            status, note = "N/A ", f"({e}; counted as pass)"
            passed += 1
        except Timeout:
            status, note = "FAIL", f"timed out after {TIME_LIMIT}s (infinite loop?)"
        except AssertionError as e:
            status, note = "FAIL", str(e)
        except GraderError as e:
            status, note = "FAIL", str(e)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            status, note = "FAIL", f"{type(e).__name__}: {e}  (line {tb.lineno})"
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
        print(f"  [{status}] {label:<3} {title}  ({time.time() - t0:.1f}s)")
        if note:
            print(f"         -> {note}")

    total = len(TESTS)
    mark = round(args.max_mark * passed / total, 1)
    print(f"\nRESULT: {passed}/{total} tests passed -> {mark}/{args.max_mark:g}")
    print("ALL TESTS PASSED: give the full grade." if passed == total else "Some tests failed: see the messages above.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
