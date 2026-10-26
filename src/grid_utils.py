# -*- coding: utf-8 -*-
"""网格地图通用工具：方向常量与单元格“进入代价”解析。"""

# 上下左右四个移动方向（题目规定不允许斜走）
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def cell_weight(ch):
    """返回进入该单元格的代价；'X' 为障碍，返回 None 表示不可通行。

    约定（依据实验要求）：
    - 'S'（起点）、'A'、'B'、'T*'（宝藏）所在格代价为 1；
    - 'E'（终点）视为 0，即最后一步不付出代价（题目二专门讨论点）；
    - 数字（int 或数字字符串）即为该格地形权值。
    """
    if ch == 'X':
        return None
    if ch == '.':
        return 1
    if ch == 'E':
        return 0
    if isinstance(ch, int):
        return ch
    if ch in ('S', 'A', 'B') or (isinstance(ch, str) and ch.startswith('T')):
        return 1
    return int(ch)


def in_bounds(grid, r, c):
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])
