# -*- coding: utf-8 -*-
"""对照实验脚本：一键复现实验报告中的全部数据。

运行方式（在项目根目录）：
    python experiments/run_experiments.py

输出：
    results/experiments.json —— 报告与图表的数据来源；
    控制台同步打印摘要。
"""
import json
import random
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from astar import a_star
from grid_utils import DIRS, cell_weight
from q1_maze_astar import solve_maze, GRID as MAZE_GIVEN, START, GOAL, manhattan
import q2_weighted_astar as q2
import q3_alphabeta as q3
import q4_treasure as q4

results = {}


# ------------------------------------------------------------------
# 实验地图构造
# ------------------------------------------------------------------
def bfs_solvable(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    seen, dq = {start}, deque([start])
    while dq:
        r, c = dq.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols \
                    and grid[nr][nc] != 'X' and (nr, nc) not in seen:
                seen.add((nr, nc))
                dq.append((nr, nc))
    return False


def random_maze(seed=42, size=21, wall_p=0.28):
    """随机障碍迷宫：从 seed 起尝试，直到起点终点连通。"""
    goal = (size - 1, size - 1)
    for s in range(seed, seed + 500):
        rng = random.Random(s)
        grid = [['X' if rng.random() < wall_p else '.'
                 for _ in range(size)] for _ in range(size)]
        grid[0][0], grid[goal[0]][goal[1]] = 'S', 'E'
        if bfs_solvable(grid, (0, 0), goal):
            return grid, s
    raise RuntimeError("未生成可解迷宫")


def random_maze_sequence(count, seed=42, size=21, wall_p=0.28):
    """顺序生成 count 张互不相同且可解的随机迷宫（供多种子实验）。"""
    goal = (size - 1, size - 1)
    out, s = [], seed
    while len(out) < count:
        rng = random.Random(s)
        grid = [['X' if rng.random() < wall_p else '.'
                 for _ in range(size)] for _ in range(size)]
        grid[0][0], grid[goal[0]][goal[1]] = 'S', 'E'
        if bfs_solvable(grid, (0, 0), goal):
            out.append((grid, s))
        s += 1
    return out


def serpentine_maze(rows=15, cols=15):
    """蛇形走廊迷宫：唯一通路蛇形贯穿全图，启发函数易被误导。"""
    grid = [['.'] * cols for _ in range(rows)]
    for r in range(1, rows, 2):
        for c in range(cols):
            grid[r][c] = 'X'
        grid[r][cols - 1 if (r // 2) % 2 == 0 else 0] = '.'
    grid[0][0] = 'S'
    grid[rows - 1][0] = 'E'
    return grid


# ------------------------------------------------------------------
# 实验一：题目一 启发函数与平局策略对照
# ------------------------------------------------------------------
def exp_q1():
    mazes = {
        "given_5x5": (MAZE_GIVEN, START, GOAL),
        "random_21x21": None,
        "serpentine_15x15": None,
    }
    grid, used_seed = random_maze()
    mazes["random_21x21"] = (grid, (0, 0), (20, 20))
    mazes["serpentine_15x15"] = (serpentine_maze(), (0, 0), (14, 0))

    runs = []
    for name, (grid, s, g) in mazes.items():
        base = None
        for tag, kw in (("h=0(Dijkstra)", dict(heuristic="zero")),
                        ("曼哈顿", dict(heuristic="manhattan")),
                        ("曼哈顿+high_g", dict(heuristic="manhattan",
                                               tie_break="high_g"))):
            path, st = solve_maze(s, g, grid, **kw)
            steps = len(path) - 1
            if tag.startswith("h=0"):
                base = steps
            runs.append({"maze": name, "heuristic": tag,
                         "expanded": st["expanded"],
                         "generated": st["generated"],
                         "max_open": st["max_open"],
                         "path_steps": steps,
                         "optimal_steps": base if base else steps})
        assert all(r["path_steps"] == base for r in runs[-3:]), \
            "各启发函数路径长度应一致（最优）"
    # 多种子稳健性：5 张不同的随机迷宫重复实验
    multi = []
    for grid, used in random_maze_sequence(5):
        for tag, kw in (("h=0(Dijkstra)", dict(heuristic="zero")),
                        ("曼哈顿", dict(heuristic="manhattan")),
                        ("曼哈顿+high_g", dict(heuristic="manhattan",
                                               tie_break="high_g"))):
            path, st = solve_maze((0, 0), (20, 20), grid, **kw)
            multi.append({"maze": "random_21x21#%d" % used,
                          "heuristic": tag, "expanded": st["expanded"],
                          "path_steps": len(path) - 1})
    results["q1"] = {"maze_seeds": {"random_21x21": used_seed},
                     "runs": runs, "multi_seed": multi}
    print("[q1] 启发函数对照：")
    for r in runs:
        print("   %-18s %-14s expanded=%-5d generated=%-5d 路径长=%d"
              % (r["maze"], r["heuristic"], r["expanded"],
                 r["generated"], r["path_steps"]))
    avg = {t: sum(m["expanded"] for m in multi
                  if m["heuristic"] == t) / 5 for t in
           ("h=0(Dijkstra)", "曼哈顿", "曼哈顿+high_g")}
    print("[q1] 5 张随机迷宫平均扩展：", avg)


# ------------------------------------------------------------------
# 实验二：题目二 代价累计与启发可采纳性
# ------------------------------------------------------------------
def q2_accumulation(grid, start, goal):
    """沿最优路径逐步记录 entered_cost / g / h / f（两种启发）。"""
    c_min = q2.min_entry_cost(grid)
    h_adj = lambda p: max(0, manhattan(p, goal) - 1) * c_min
    h_man = lambda p: manhattan(p, goal)
    path, _ = a_star(start, goal, q2.make_weighted_neighbors(grid), h_adj)
    rows, g = [], 0
    for i, p in enumerate(path):
        w = 0 if i == 0 else cell_weight(grid[p[0]][p[1]])
        g += w
        rows.append({"step": i, "pos": list(p), "entered_cost": w, "g": g,
                     "h_adj": h_adj(p), "f_adj": g + h_adj(p),
                     "h_man": h_man(p), "f_man": g + h_man(p)})
    return rows


def exp_q2():
    out = {}
    # 小图（题目给定）
    runs = []
    for hname in ("zero", "manhattan", "adjusted"):
        cost, path, st = q2.solve_weighted(q2.START, q2.GOAL, q2.GRID,
                                           heuristic=hname)
        runs.append({"heuristic": hname, "cost": cost,
                     "expanded": st["expanded"],
                     "generated": st["generated"]})
        assert cost == 7, "给定图最小代价应为 7"
    out["given"] = {"runs": runs,
                    "accumulation": q2_accumulation(q2.GRID, q2.START,
                                                    q2.GOAL)}
    # 沼泽图（15x15，权值 1/3/8）
    rng = random.Random(7)
    grid = [[rng.choice([1, 1, 1, 3, 3, 8]) for _ in range(15)]
            for _ in range(15)]
    grid[0][0], grid[14][14] = 'S', 'E'
    runs = []
    for hname in ("zero", "manhattan", "adjusted"):
        cost, path, st = q2.solve_weighted((0, 0), (14, 14), grid,
                                           heuristic=hname)
        runs.append({"heuristic": hname, "cost": cost,
                     "expanded": st["expanded"],
                     "generated": st["generated"]})
    assert len({r["cost"] for r in runs}) == 1, "三种启发代价应一致"
    out["swamp_15x15"] = {"runs": runs}
    results["q2"] = out

    print("[q2] 代价与启发对照：")
    for key in ("given", "swamp_15x15"):
        for r in out[key]["runs"]:
            print("   %-12s %-9s cost=%-3d expanded=%-4d"
                  % (key, r["heuristic"], r["cost"], r["expanded"]))


# ------------------------------------------------------------------
# 实验三：题目三 Minimax / Alpha-Beta 与访问顺序
# ------------------------------------------------------------------
def build_random_tree(depth, branching, rng):
    if depth == 0:
        return q3.TreeNode(value=rng.randint(0, 99))
    return q3.TreeNode(children=[build_random_tree(depth - 1, branching, rng)
                                 for _ in range(branching)])


def exp_q3():
    # 样例树（题目给定）
    st_mm = q3.SearchStats()
    v_mm = q3.minimax(q3.build_sample_tree(), True, st_mm)
    st_ab = q3.SearchStats()
    v_ab = q3.alphabeta(q3.build_sample_tree(), True, stats=st_ab)
    assert v_mm == v_ab == 5
    results_q3 = {"sample": {"value": v_mm,
                             "minimax": st_mm.as_dict(),
                             "alphabeta": st_ab.as_dict()}}

    # 大随机树：深度 8、分支 3（6561 个叶子）
    rng = random.Random(5)
    root = build_random_tree(8, 3, rng)
    st = q3.SearchStats()
    q3.minimax(root, True, st)
    mm = st.as_dict()

    memo = {}

    def true_val(node, maxing):
        key = (id(node), maxing)
        if key not in memo:
            if not node.children:
                memo[key] = node.value
            else:
                vals = [true_val(c, not maxing) for c in node.children]
                memo[key] = max(vals) if maxing else min(vals)
        return memo[key]

    def order_key(mode):
        def key(children, maximizing):
            if mode == "natural":
                return list(children)
            if mode == "random":
                cs = list(children)
                random.shuffle(cs)
                return cs
            keyed = [(true_val(c, not maximizing), i, c)
                     for i, c in enumerate(children)]
            if mode == "best":       # MAX 降序 / MIN 升序：最优子节点先访问
                keyed.sort(key=lambda t: ((-t[0] if maximizing else t[0]),
                                          t[1]))
            elif mode == "worst":    # 最差子节点先访问
                keyed.sort(key=lambda t: ((t[0] if maximizing else -t[0]),
                                          t[1]))
            return [t[2] for t in keyed]
        return key

    def run_ab(mode):
        st = q3.SearchStats()
        v = q3.alphabeta_ordered(root, True, order_key(mode), st)
        assert v == mm_v, "各访问顺序结果必须一致"
        return st.as_dict()

    mm_v = q3.minimax(root, True, q3.SearchStats())

    ab = {mode: run_ab(mode) for mode in ("natural", "best", "worst")}
    rnd = []
    for s in range(20):
        random.seed(s)
        rnd.append(run_ab("random")["leaf_evals"])
    ab["random"] = {"leaf_evals": sum(rnd) / len(rnd),
                    "min": min(rnd), "max": max(rnd)}

    results_q3["random_tree"] = {
        "params": {"depth": 8, "branching": 3, "seed": 5,
                   "leaves": 3 ** 8},
        "minimax": mm, "alphabeta": ab,
    }
    results["q3"] = results_q3
    print("[q3] 样例树: value=%d  minimax=%s  alphabeta=%s"
          % (v_mm, st_mm.as_dict(), st_ab.as_dict()))
    print("[q3] 深度8分支3: minimax leaf=%d" % mm["leaf_evals"])
    for mode, d in ab.items():
        print("   AB-%-8s leaf_evals=%s" % (mode, d["leaf_evals"]))


# ------------------------------------------------------------------
# 实验四：题目四 距离矩阵与博弈搜索对照
# ------------------------------------------------------------------
def first_move_values():
    """H=2 / H=4 下 A 每个首步的纯 Minimax 值（用于决策差异分析）。"""
    dist = q4.distance_matrix(q4.MAP)
    root = q4.GameState("A", "B", frozenset(q4.VALUES), 0, 0, "A")
    out = {}
    for H in (2, 4):
        vals = {}
        for t, gain, nxt in q4.legal_moves(root, dist):
            st = q4.GameStats()
            vals[t] = q4.game_search(nxt, H - 1, dist, st)
        out["H=%d" % H] = vals
    return out


def exp_q4():
    dist = q4.distance_matrix(q4.MAP)
    matrix = [[dist[(r, c)] for c in q4.LABELS] for r in q4.LABELS]

    methods = [("minimax", {}),
               ("minimax+memo", {"memo": True}),
               ("alphabeta", {"use_ab": True}),
               ("alphabeta+smart_order", {"use_ab": True, "order": "smart"}),
               ("alphabeta+reverse_order", {"use_ab": True,
                                            "order": "reverse"})]
    search = []
    expected = {2: ("T2", -1), 4: ("T3", 3)}
    for H in (2, 4):
        for name, kw in methods:
            t, v, st = q4.best_first_move(H, **kw)
            search.append({"H": H, "method": name, "best_target": t,
                           "best_value": v, **st.as_dict(),
                           "match_expected": (t, v) == expected[H]})
    results["q4"] = {"labels": q4.LABELS, "matrix": matrix,
                     "search": search, "first_moves": first_move_values()}

    print("[q4] 距离矩阵：")
    for r, row in zip(q4.LABELS, matrix):
        print("   %-3s %s" % (r, row))
    print("[q4] 博弈搜索：")
    for s in search:
        print("   H=%d %-24s target=%s value=%-3d expanded=%-4d "
              "evaluated=%-4d cutoffs=%-3d match=%s"
              % (s["H"], s["method"], s["best_target"], s["best_value"],
                 s["expanded"], s["evaluated"], s["cutoffs"],
                 s["match_expected"]))


# ------------------------------------------------------------------
if __name__ == "__main__":
    exp_q1()
    exp_q2()
    exp_q3()
    exp_q4()
    out = ROOT / "results" / "experiments.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("\n已写入", out)
