# -*- coding: utf-8 -*-
"""通用 A* 搜索核心实现（供题目一、二、四复用）。

约定：
- 图以隐式方式给出：neighbors_fn(pos) 返回 [(next_pos, step_cost), ...]；
- h_fn(pos) 返回启发值 h(n)；
- f(n) = g(n) + h(n)，g(n) 为起点到 n 的已付代价；
- 优先队列使用二叉堆（heapq），配合 g_best 字典做“懒删除”：
  节点权值被更新时重复入堆，出堆时丢弃过期项。

平局策略（f 相同时的出堆顺序）：
- fifo    ：按插入顺序（经典写法）；
- high_g  ：优先扩展 g 更大（离目标更近）的节点，
            通常能显著减少扩展节点数，作为对照实验使用。

统计口径：
- expanded ：出堆且非过期、真正展开后继的节点数（不含目标节点本身）；
- generated：入堆总次数（含起点）；
- max_open ：优先队列长度的峰值。
"""
import heapq
from typing import Callable, Hashable, Iterable, Tuple

INF = float("inf")


def a_star(
    start: Hashable,
    goal: Hashable,
    neighbors_fn: Callable[[Hashable], Iterable[Tuple[Hashable, float]]],
    h_fn: Callable[[Hashable], float],
    tie_break: str = "fifo",
):
    """A* 主过程。

    返回 (path, stats)：path 为从 start 到 goal 的坐标/节点序列（含两端），
    无解时为 None；stats 为 {"expanded", "generated", "max_open"}。
    """
    if tie_break == "high_g":
        def prio(f, g):
            return (f, -g)
    else:
        def prio(f, g):
            return (f, 0)

    counter = 0                      # 插入序号，保证 heap 比较可进行
    g_best = {start: 0}              # 目前发现的各节点最优 g
    came_from = {}                   # 回溯指针
    closed = set()                   # 已展开集合
    h0 = h_fn(start)
    open_heap = [(*prio(h0, 0), counter, start, 0)]
    counter += 1
    expanded = 0
    generated = 1
    max_open = 1

    while open_heap:
        _, _, _, pos, g = heapq.heappop(open_heap)
        if pos in closed or g > g_best.get(pos, INF):
            continue                 # 过期堆项，跳过
        if pos == goal:              # 首次出堆即最优，回溯路径
            path = [pos]
            while path[-1] in came_from:
                path.append(came_from[path[-1]])
            path.reverse()
            return path, {"expanded": expanded, "generated": generated,
                          "max_open": max_open}
        closed.add(pos)
        expanded += 1
        for nxt, cost in neighbors_fn(pos):
            ng = g + cost
            if ng < g_best.get(nxt, INF):
                g_best[nxt] = ng
                came_from[nxt] = pos
                f = ng + h_fn(nxt)
                heapq.heappush(open_heap, (*prio(f, ng), counter, nxt, ng))
                counter += 1
                generated += 1
                if len(open_heap) > max_open:
                    max_open = len(open_heap)
    return None, {"expanded": expanded, "generated": generated,
                  "max_open": max_open}
