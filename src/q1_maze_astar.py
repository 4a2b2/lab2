# -*- coding: utf-8 -*-
"""题目一：迷宫寻路 —— A* + 曼哈顿距离启发函数。

输入：起点坐标、终点坐标、二维网格（'.'/'S'/'E' 可通行，'X' 为障碍）。
输出：起点到终点的最短路径坐标序列（含两端）；无解返回 []。

对照实验接口：
- heuristic="zero" 退化为 Dijkstra（h=0）；
- tie_break="high_g" 在 f 相同时优先扩展离目标更近的节点。
"""
from astar import a_star
from grid_utils import DIRS, cell_weight


def manhattan(a, b):
    """曼哈顿距离 |r1-r2| + |c1-c2|。"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def make_neighbors(grid):
    """构造四方向邻居函数：每格移动代价固定为 1。"""
    rows, cols = len(grid), len(grid[0])

    def neighbors(pos):
        r, c = pos
        out = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols \
                    and cell_weight(grid[nr][nc]) is not None:
                out.append(((nr, nc), 1))
        return out

    return neighbors


def solve_maze(start, goal, grid, heuristic="manhattan", tie_break="fifo"):
    """求解迷宫最短路径。

    返回 (path, stats)；path 为坐标列表（无解时为 None）。
    heuristic: "manhattan"（曼哈顿距离）| "zero"（h=0，即 Dijkstra）
    tie_break: "fifo" | "high_g"
    """
    neighbors = make_neighbors(grid)
    if heuristic == "manhattan":
        h = lambda p: manhattan(p, goal)
    elif heuristic == "zero":
        h = lambda p: 0
    else:
        raise ValueError("未知启发函数: %s" % heuristic)
    return a_star(start, goal, neighbors, h, tie_break)


# ---------------- 测试用例（来自实验要求文档） ----------------
START, GOAL = (0, 0), (3, 4)
GRID = [
    ['S', '.', '.', 'X', '.'],
    ['.', 'X', '.', '.', '.'],
    ['.', 'X', '.', 'X', '.'],
    ['.', '.', '.', 'X', 'E'],
    ['X', 'X', '.', '.', '.'],
]

if __name__ == "__main__":
    path, stats = solve_maze(START, GOAL, GRID)
    print("题目一：迷宫寻路")
    print("最短路径:", path if path is not None else [])
    print("路径步数:", len(path) - 1 if path else "无解")
    print("A*(曼哈顿) 统计:", stats)

    # 对照组：h=0（Dijkstra）与 high_g 平局策略
    _, stats0 = solve_maze(START, GOAL, GRID, heuristic="zero")
    _, statshg = solve_maze(START, GOAL, GRID, tie_break="high_g")
    print("A*(h=0)    统计:", stats0)
    print("A*(high_g) 统计:", statshg)
