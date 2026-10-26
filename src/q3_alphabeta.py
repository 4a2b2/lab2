# -*- coding: utf-8 -*-
"""题目三：极大极小博弈树 —— Minimax 与 Alpha-Beta 剪枝。

树的结点定义与实验要求文档一致：
- 叶子节点带 value（叶子得分）；
- 非叶子节点带 children 列表；
- 根节点为 MAX 玩家，评估子节点顺序从左到右。

统计口径：
- visited   ：递归进入的节点总数（含根与叶子）；
- leaf_evals：叶子得分读取次数（搜索开销的主要度量）；
- cutoffs   ：发生剪枝的次数。
"""
import random


class TreeNode:
    def __init__(self, value=None, children=None):
        self.value = value                          # 叶子节点的得分
        self.children = children if children is not None else []


class SearchStats:
    def __init__(self):
        self.visited = 0
        self.leaf_evals = 0
        self.cutoffs = 0

    def as_dict(self):
        return {"visited": self.visited, "leaf_evals": self.leaf_evals,
                "cutoffs": self.cutoffs}


def is_leaf(node):
    return not node.children


# ------------------------- Minimax（无剪枝） -------------------------
def minimax(node, maximizing, stats=None):
    """返回该子树对当前玩家而言的最佳值。"""
    if stats is None:
        stats = SearchStats()
    stats.visited += 1
    if is_leaf(node):
        stats.leaf_evals += 1
        return node.value
    if maximizing:                                   # MAX 取子节点最大值
        best = float("-inf")
        for child in node.children:
            best = max(best, minimax(child, False, stats))
        return best
    best = float("inf")                              # MIN 取子节点最小值
    for child in node.children:
        best = min(best, minimax(child, True, stats))
    return best


# ---------------------- Alpha-Beta 剪枝 ------------------------------
def alphabeta(node, maximizing, alpha=float("-inf"), beta=float("inf"),
              stats=None):
    """Alpha-Beta 主过程。

    剪枝条件：
    - MAX 节点：一旦 best >= beta（下界已不低于祖先的上界），剩余兄弟
      不可能影响祖先决策，剪断（beta cutoff）；
    - MIN 节点：一旦 best <= alpha，同理剪断（alpha cutoff）。
    """
    if stats is None:
        stats = SearchStats()
    stats.visited += 1
    if is_leaf(node):
        stats.leaf_evals += 1
        return node.value
    if maximizing:
        best = float("-inf")
        for i, child in enumerate(node.children):
            best = max(best, alphabeta(child, False, alpha, beta, stats))
            alpha = max(alpha, best)
            if alpha >= beta:                        # 剪枝
                if i < len(node.children) - 1:
                    stats.cutoffs += 1               # 仅统计真正跳过兄弟的剪枝
                break
        return best
    best = float("inf")
    for i, child in enumerate(node.children):
        best = min(best, alphabeta(child, True, alpha, beta, stats))
        beta = min(beta, best)
        if beta <= alpha:                            # 剪枝
            if i < len(node.children) - 1:
                stats.cutoffs += 1
            break
    return best


def alphabeta_ordered(node, maximizing, order_key=None, stats=None,
                      alpha=float("-inf"), beta=float("inf")):
    """带子节点排序的 Alpha-Beta（用于访问顺序对照实验）。

    order_key(children, maximizing) -> 排序后的子节点列表。
    """
    if stats is None:
        stats = SearchStats()
    stats.visited += 1
    if is_leaf(node):
        stats.leaf_evals += 1
        return node.value
    children = order_key(node.children, maximizing) if order_key \
        else node.children
    if maximizing:
        best = float("-inf")
        for i, child in enumerate(children):
            best = max(best, alphabeta_ordered(child, False, order_key,
                                               stats, alpha, beta))
            alpha = max(alpha, best)
            if alpha >= beta:
                if i < len(children) - 1:
                    stats.cutoffs += 1
                break
        return best
    best = float("inf")
    for i, child in enumerate(children):
        best = min(best, alphabeta_ordered(child, True, order_key,
                                           stats, alpha, beta))
        beta = min(beta, best)
        if beta <= alpha:
            if i < len(children) - 1:
                stats.cutoffs += 1
            break
    return best


def true_values(node, maximizing):
    """用一次独立的 Minimax 计算各子树真实价值（仅供排序实验使用，
    其开销不计入被测算法）。"""
    if is_leaf(node):
        return node.value
    vals = [true_values(c, not maximizing) for c in node.children]
    return max(vals) if maximizing else min(vals)


# ----------------------- 测试树（来自要求文档） -----------------------
def build_sample_tree():
    """按文档给出的构建代码搭树。注意：文档中 min2 的第一个孩子
    复用了 max2（同一对象），此处忠实还原该结构。"""
    leaf1, leaf2 = TreeNode(3), TreeNode(5)
    leaf3, leaf4 = TreeNode(6), TreeNode(9)
    leaf5, leaf6 = TreeNode(1), TreeNode(2)
    max1 = TreeNode(children=[leaf1, leaf2])   # -> 5
    max2 = TreeNode(children=[leaf3, leaf4])   # -> 9
    max3 = TreeNode(children=[leaf5, leaf6])   # -> 2
    min1 = TreeNode(children=[max1, max2])     # -> 5
    min2 = TreeNode(children=[max2, max3])     # -> 2
    root = TreeNode(children=[min1, min2])     # MAX -> 5
    return root


if __name__ == "__main__":
    print("题目三：极大极小博弈树的最佳得分")
    st1 = SearchStats()
    v1 = minimax(build_sample_tree(), True, st1)
    st2 = SearchStats()
    v2 = alphabeta(build_sample_tree(), True, stats=st2)
    print("Minimax    结果 = %d, 统计 = %s" % (v1, st1.as_dict()))
    print("Alpha-Beta 结果 = %d, 统计 = %s" % (v2, st2.as_dict()))
    print("预期输出: 5")
