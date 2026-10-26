# -*- coding: utf-8 -*-
"""题目四：竞争环境下的宝藏分配（A* + 博弈搜索综合题）。

建模：
- 地图为 7x7，'X' 不可通行，数字格进入代价为其数值，
  A/B/T 所在格进入代价为 1；只允许上下左右移动。
- 任务1：A* 计算 {A,B,T1..T4} 两两最小移动代价 -> 6x6 距离矩阵。
- 任务2：博弈状态 GameState 记录双方位置、剩余宝藏、累计得分、
  当前行动玩家；一个“动作”= 当前玩家选择一个剩余宝藏并沿
  最小代价路径移动过去，收益 Gain = V(Ti) - d(p, Ti)。
- 任务3：Minimax / Alpha-Beta 在深度 H（ ply 数）内搜索，
  叶子评价值 U = Score_A - Score_B；A 最大化 U，B 最小化 U。

经过其他宝藏不自动收集；已获取宝藏位置仍可通行（代价 1）；
对方玩家不阻挡寻路 —— 以上规则均已体现在距离矩阵的复用中。
"""
import json
import sys
from dataclasses import dataclass, replace
from functools import lru_cache

from astar import a_star
from grid_utils import DIRS, cell_weight
from q1_maze_astar import manhattan

# --------------------------- 地图与常量 ---------------------------
MAP = [
    ['A', 1, 1, 'X', 2, 1, 'T1'],
    [1,  'X', 6, 'X', 1, 'X', 1],
    [1,  1, 'T2', 1, 1, 1, 1],
    ['X', 1, 'X', 8, 'X', 1, 'X'],
    [1,  1, 1, 1, 'T3', 1, 1],
    [1,  'X', 9, 'X', 1, 'X', 1],
    ['T4', 1, 1, 'X', 1, 1, 'B'],
]

POINTS = {                       # 六个关键点坐标
    "A": (0, 0), "B": (6, 6),
    "T1": (0, 6), "T2": (2, 2), "T3": (4, 4), "T4": (6, 0),
}
LABELS = ["A", "B", "T1", "T2", "T3", "T4"]
VALUES = {"T1": 9, "T2": 6, "T3": 7, "T4": 7}   # 宝藏价值


def make_map_neighbors(grid):
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


def distance_matrix(grid):
    """任务1：用 A* 计算六个关键点两两最小移动代价。
    本图所有可通行格进入代价 >= 1，曼哈顿距离可采纳。"""
    neighbors = make_map_neighbors(grid)
    dist = {}
    for src in LABELS:
        for dst in LABELS:
            if src == dst:
                dist[(src, dst)] = 0
                continue
            h = lambda p: manhattan(p, POINTS[dst])
            path, _ = a_star(POINTS[src], POINTS[dst], neighbors, h)
            cost = sum(cell_weight(grid[r][c]) for r, c in path[1:])
            dist[(src, dst)] = cost
    return dist


# --------------------------- 任务2：博弈状态 ---------------------------
@dataclass(frozen=True)
class GameState:
    pos_a: str                 # A 当前所在关键点（A / T*）
    pos_b: str                 # B 当前所在关键点
    remaining: frozenset       # 剩余宝藏集合，如 {"T1","T3"}
    score_a: int               # A 累计收益
    score_b: int               # B 累计收益
    player: str                # 当前行动玩家 'A' / 'B'


def legal_moves(state, dist):
    """当前玩家的所有动作：(宝藏名, 本步收益, 下一状态)。"""
    moves = []
    pos = state.pos_a if state.player == "A" else state.pos_b
    for t in sorted(state.remaining):
        gain = VALUES[t] - dist[(pos, t)]
        if state.player == "A":
            nxt = replace(state, pos_a=t, remaining=state.remaining - {t},
                          score_a=state.score_a + gain, player="B")
        else:
            nxt = replace(state, pos_b=t, remaining=state.remaining - {t},
                          score_b=state.score_b + gain, player="A")
        moves.append((t, gain, nxt))
    return moves


# ------------------------- 任务3：博弈搜索 -------------------------
class GameStats:
    def __init__(self):
        self.expanded = 0      # 展开的内部状态数
        self.evaluated = 0     # 叶子评估次数
        self.cutoffs = 0       # Alpha-Beta 剪枝次数

    def as_dict(self):
        return {"expanded": self.expanded, "evaluated": self.evaluated,
                "cutoffs": self.cutoffs}


def order_moves(moves, order):
    """动作排序策略（对照实验用）。
    given   : 按宝藏名字典序（即题目给定顺序）；
    smart   : MAX 按收益降序、MIN 按收益升序（接近最优排序，剪枝最多）；
    reverse : 与 smart 相反（最坏排序，剪枝最少）。"""
    if order == "given":
        return moves
    if order == "smart":
        return moves  # 在搜索函数内按玩家方向处理
    if order == "reverse":
        return moves
    raise ValueError(order)


def game_search(state, depth, dist, stats, use_ab=False, order="given",
                memo=None, alpha=float("-inf"), beta=float("inf")):
    """返回当前玩家视角下可取得的最优 U 值（A 最大化、B 最小化）。"""
    if depth == 0 or not state.remaining:
        stats.evaluated += 1
        return state.score_a - state.score_b

    key = None
    if memo is not None:
        key = (state.pos_a, state.pos_b, state.remaining, state.player,
               depth)
        if key in memo:
            return memo[key]

    stats.expanded += 1
    maximizing = state.player == "A"
    moves = legal_moves(state, dist)
    if order == "smart":                     # 静态启发排序：按本步收益
        moves.sort(key=lambda m: -m[1] if maximizing else m[1])
    elif order == "reverse":
        moves.sort(key=lambda m: m[1] if maximizing else -m[1])

    if maximizing:
        best = float("-inf")
        for i, (_, _, nxt) in enumerate(moves):
            v = game_search(nxt, depth - 1, dist, stats, use_ab, order,
                            memo, alpha, beta)
            best = max(best, v)
            alpha = max(alpha, best)
            if use_ab and alpha >= beta:
                if i < len(moves) - 1:
                    stats.cutoffs += 1
                break
    else:
        best = float("inf")
        for i, (_, _, nxt) in enumerate(moves):
            v = game_search(nxt, depth - 1, dist, stats, use_ab, order,
                            memo, alpha, beta)
            best = min(best, v)
            beta = min(beta, best)
            if use_ab and beta <= alpha:
                if i < len(moves) - 1:
                    stats.cutoffs += 1
                break
    if memo is not None:
        memo[key] = best
    return best


def best_first_move(depth, use_ab=False, order="given", memo=False):
    """在深度 depth 下搜索 A 的最优首步，返回
    (best_target, best_value, stats)。

    根节点逐个尝试 A 的首步；use_ab=True 时向后续兄弟子树传递
    当前最优值 alpha（标准根节点窗口收缩），使根层也能剪枝。"""
    dist = distance_matrix(MAP)
    root = GameState("A", "B", frozenset(VALUES), 0, 0, "A")
    stats = GameStats()
    mem = {} if memo else None
    best_target, best_value = None, float("-inf")
    alpha = float("-inf")
    for t, gain, nxt in legal_moves(root, dist):
        v = game_search(nxt, depth - 1, dist, stats, use_ab, order, mem,
                        alpha, float("inf"))
        if v > best_value:
            best_value, best_target = v, t
        alpha = max(alpha, best_value)
    return best_target, best_value, stats


# ------------------------------ 主程序 ------------------------------
if __name__ == "__main__":
    print("题目四：竞争环境下的宝藏分配")
    dist = distance_matrix(MAP)

    print("\n任务1：6x6 最小移动代价距离矩阵（A*，曼哈顿启发）")
    header = "      " + "".join("%5s" % c for c in LABELS)
    print(header)
    for r in LABELS:
        print("%5s " % r + "".join("%5d" % dist[(r, c)] for c in LABELS))

    print("\n任务3：A 的最优首步与最优收益差 U = Score_A - Score_B")
    results = {}
    for H in (2, 4):
        for name, kw in (("Minimax", {}),
                         ("Alpha-Beta", {"use_ab": True})):
            t, v, st = best_first_move(H, **kw)
            results["H=%d %s" % (H, name)] = (t, v, st)
            print("H=%d %-10s -> {\"best_target\": \"%s\", "
                  "\"best_value\": %s}  统计=%s"
                  % (H, name, t, v, st.as_dict()))
    print("\n预期: H=2 -> T2 / -1 ； H=4 -> T3 / 3")
