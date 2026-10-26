# -*- coding: utf-8 -*-
"""题目二：加权地形 —— 代价感知的 A*。

规则：
- 进入某格的代价等于该格地形权值；'E' 视为 0（最后一步免费）；
- 只能上下左右移动；无解返回 -1。

启发函数讨论（题目提示点）：
- "manhattan"：h = 曼哈顿距离 d。由于进入 E 免费，剩余真实代价
   至少为 (d-1)*c_min，因此 h=d 最多高估 1，不满足严格可采纳性
   （本实验同时从理论与数值上分析其影响）；
- "adjusted"：h = max(0, d-1) * c_min，其中 c_min 为非终点格的
   最小进入代价。该函数可采纳且一致，是本题的“安全”启发；
- "zero"    ：h=0，退化为 Dijkstra，作为搜索开销上界参照。
"""
from astar import a_star
from grid_utils import DIRS, cell_weight


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def make_weighted_neighbors(grid):
    """邻居函数：进入下一格的代价 = 下一格的地形权值。"""
    rows, cols = len(grid), len(grid[0])

    def neighbors(pos):
        r, c = pos
        out = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                w = cell_weight(grid[nr][nc])
                if w is not None:
                    out.append(((nr, nc), w))
        return out

    return neighbors


def min_entry_cost(grid):
    """非终点可通行格的最小进入代价 c_min（用于可采纳启发）。"""
    weights = [cell_weight(ch) for row in grid for ch in row]
    return min(w for w in weights if w is not None and w > 0)


def solve_weighted(start, goal, grid, heuristic="adjusted", tie_break="fifo"):
    """返回 (cost, path, stats)：cost 为最小总代价，无解时 cost=-1。"""
    neighbors = make_weighted_neighbors(grid)
    c_min = min_entry_cost(grid)
    if heuristic == "manhattan":
        h = lambda p: manhattan(p, goal)
    elif heuristic == "adjusted":
        h = lambda p: max(0, manhattan(p, goal) - 1) * c_min
    elif heuristic == "zero":
        h = lambda p: 0
    else:
        raise ValueError("未知启发函数: %s" % heuristic)

    path, stats = a_star(start, goal, neighbors, h, tie_break)
    if path is None:
        return -1, None, stats
    cost = sum(cell_weight(grid[r][c]) for r, c in path[1:])
    return cost, path, stats


# ---------------- 测试用例（来自实验要求文档） ----------------
START, GOAL = (0, 0), (4, 4)
GRID = [
    ['S', 1, 1, 8, 1],
    [1,   8, 3, 1, 1],
    [1,   8, 1, 8, 1],
    [1,   1, 1, 8, 1],
    [8,   8, 1, 1, 'E'],
]

if __name__ == "__main__":
    print("题目二：加权地形")
    for hname in ("adjusted", "manhattan", "zero"):
        cost, path, stats = solve_weighted(START, GOAL, GRID, heuristic=hname)
        print("启发=%-9s 最小代价=%s  统计=%s" % (hname, cost, stats))
        if path:
            print("   路径:", " -> ".join(str(p) for p in path))
    print("预期输出: 7")
