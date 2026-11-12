# -*- coding: utf-8 -*-
"""根据 results/experiments.json 生成实验报告插图（report/figs/*.png）。

运行方式（在项目根目录）：
    python experiments/make_charts.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "report" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

# 中文字体与整体风格（低饱和、自然）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.color"] = "#E3E6EA"
plt.rcParams["grid.linewidth"] = 0.6

C = ["#7293B5", "#9DB4A0", "#C9B48F", "#B58F8F", "#9B8FB5"]  # 柔和五色
INK = "#3A4450"

data = json.loads((ROOT / "results" / "experiments.json")
                  .read_text(encoding="utf-8"))


def style_ax(ax, ylabel=""):
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.tick_params(colors=INK, labelsize=8.5)


def annotate_bars(ax, bars, fmt="{:.0f}"):
    for b in bars:
        ax.annotate(fmt.format(b.get_height()),
                    (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=8, color=INK,
                    xytext=(0, 1.5), textcoords="offset points")


# ------------------------------------------------------------------
# 图 1：题目一 三张迷宫 × 三种搜索策略 的扩展节点数
# ------------------------------------------------------------------
def fig_q1():
    runs = data["q1"]["runs"]
    mazes = ["given_5x5", "random_21x21", "serpentine_15x15"]
    titles = ["给定迷宫 5×5（路径长 7）", "随机迷宫 21×21（路径长 40）",
              "蛇形迷宫 15×15（路径长 126）"]
    tags = ["h=0(Dijkstra)", "曼哈顿", "曼哈顿+high_g"]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.1))
    for ax, mz, tt in zip(axes, mazes, titles):
        vals = [next(r["expanded"] for r in runs
                     if r["maze"] == mz and r["heuristic"] == t)
                for t in tags]
        bars = ax.bar(["h=0", "曼哈顿", "曼哈顿\n+high_g"], vals,
                      width=0.62, color=C[:3])
        annotate_bars(ax, bars)
        ax.set_title(tt, fontsize=10, color=INK)
        style_ax(ax, "扩展节点数")
        ax.set_ylim(0, max(vals) * 1.18)
    fig.suptitle("题目一：不同启发函数与平局策略下的 A* 扩展节点数",
                 fontsize=11.5, color=INK, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_q1_heuristic.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 2：题目二 最优路径上 g / h / f 的累计过程（给定图）
# ------------------------------------------------------------------
def fig_q2_accum():
    acc = data["q2"]["given"]["accumulation"]
    xs = [r["step"] for r in acc]
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    ax.plot(xs, [r["g"] for r in acc], "-o", color=C[0], ms=3.5, lw=1.7,
            label="g(n)：已付代价")
    ax.plot(xs, [r["h_adj"] for r in acc], "-s", color=C[1], ms=3.5, lw=1.7,
            label="h(n)=max(0,d−1)·c_min")
    ax.plot(xs, [r["f_adj"] for r in acc], "--^", color=C[3], ms=3.5, lw=1.5,
            label="f(n)=g+h（修正启发，恒为 7）")
    ax.plot(xs, [r["f_man"] for r in acc], ":", color=C[2], ms=3.5, lw=1.6,
            label="f(n)（h=d，最多高估 1）")
    ax.set_xlabel("路径步序（S → E）", fontsize=9, color=INK)
    ax.set_xticks(xs)
    ax.set_ylim(0, 9.6)
    ax.annotate("进入 E 免费：g 停在第 7 步的 7", xy=(8, 7), xytext=(4.7, 9.0),
                fontsize=8, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.7,
                                shrinkA=0, shrinkB=2))
    ax.legend(fontsize=7.6, frameon=False, loc="center left",
              bbox_to_anchor=(1.01, 0.5))
    ax.set_title("题目二：最优路径上 g / h / f 的累计过程（给定图）",
                 fontsize=10.5, color=INK)
    style_ax(ax, "代价")
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_q2_accum.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 3：题目三 样例博弈树的取值回传与剪枝位置
# ------------------------------------------------------------------
def fig_q3_tree():
    fig, ax = plt.subplots(figsize=(7.8, 3.0))
    ax.set_xlim(-4.2, 4.2)
    ax.set_ylim(-0.75, 3.65)
    ax.axis("off")
    boxes = {                       # (x, y, 文本)
        "root": (0.0, 3.0, "root (MAX) = 5"),
        "min1": (-2.1, 2.0, "min1 (MIN) = 5"),
        "min2": (2.1, 2.0, "min2 (MIN) = 2"),
        "max1": (-3.1, 1.0, "max1 = 5"),
        "max2": (-1.1, 1.0, "max2 = 9"),
        "max2b": (1.1, 1.0, "max2*"),
        "max3": (3.1, 1.0, "max3 = 2"),
    }
    leaves = [(-3.65, "3", False), (-2.55, "5", False),
              (-1.65, "6", False), (-0.55, "9", True),
              (0.55, "6", False), (1.65, "9", False),
              (2.55, "1", False), (3.65, "2", False)]
    solid = [("root", "min1"), ("root", "min2"),
             ("min1", "max1"), ("min1", "max2"),
             ("min2", "max2b"), ("min2", "max3")]
    for a_, b_ in solid:
        x1, y1 = boxes[a_][0], boxes[a_][1]
        x2, y2 = boxes[b_][0], boxes[b_][1]
        ax.plot([x1, x2], [y1 - 0.18, y2 + 0.18], color="#B9C4D0",
                lw=0.9, zorder=1)
    for k, parent in ((0, "max1"), (1, "max1"), (2, "max2"), (3, "max2"),
                      (4, "max2b"), (5, "max2b"), (6, "max3"), (7, "max3")):
        x, _, cut = leaves[k]
        x1, y1 = boxes[parent][0], boxes[parent][1]
        style = dict(ls=(0, (3, 2)), color="#C0504D", lw=1.3) if cut \
            else dict(ls="-", color="#B9C4D0", lw=0.9)
        ax.plot([x1, x], [y1 - 0.18, 0.16], zorder=1, **style)
    for _, (x, y, text) in boxes.items():
        ax.text(x, y, text, ha="center", va="center", fontsize=8.6,
                color=INK, zorder=3,
                bbox=dict(boxstyle="round,pad=0.30", fc="#F2F6FA",
                          ec="#7293B5", lw=0.9))
    for x, val, cut in leaves:
        edge = "#C0504D" if cut else "#C9D3DE"
        ax.text(x, 0.0, val, ha="center", va="center", fontsize=9,
                color="#C0504D" if cut else INK, zorder=3,
                bbox=dict(boxstyle="round,pad=0.28", fc="#FFFFFF",
                          ec=edge, lw=0.9))
        if cut:                      # 标出被剪掉的叶子
            ax.plot([x - 0.13, x + 0.13], [-0.15, 0.15], color="#C0504D",
                    lw=1.0, zorder=4)
    ax.text(-1.85, 0.58, "α=6 ≥ β=5，剪枝", fontsize=8.0, color="#C0504D",
            ha="center", va="center", zorder=5)
    ax.text(2.1, -0.62, "虚线：该叶子未被求值；max2* 为与左侧 max2 共享的"
            "同一子树，故 min2 下会再次访问", fontsize=7.6, color="#6B7A8C",
            ha="center")
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_q3_tree.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 4：题目三 大随机树上 Minimax 与不同访问顺序的 Alpha-Beta
# ------------------------------------------------------------------
def fig_q3():
    rt = data["q3"]["random_tree"]
    ab = rt["alphabeta"]
    names = ["Minimax\n(无剪枝)", "AB\n自然顺序", "AB\n随机顺序(均值)",
             "AB\n最差顺序", "AB\n完美排序"]
    vals = [rt["minimax"]["leaf_evals"], ab["natural"]["leaf_evals"],
            ab["random"]["leaf_evals"], ab["worst"]["leaf_evals"],
            ab["best"]["leaf_evals"]]
    theory = 2 * 3 ** (8 // 2)          # 最优情形理论界 ≈ 2·b^(d/2)
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    bars = ax.bar(names, vals, width=0.6,
                  color=[C[0], C[1], C[2], C[3], C[4]])
    annotate_bars(ax, bars)
    ax.axhline(theory, color=C[3], ls="--", lw=1.2)
    ax.set_xlim(-0.62, 5.9)
    ax.annotate("理论界 %d" % theory,
                xy=(4.58, theory), xycoords=("data", "data"),
                xytext=(0, 4), textcoords="offset points",
                ha="left", va="bottom", fontsize=8.5, color=C[3])
    ax.set_yscale("log")
    ax.set_ylim(80, 9000)
    ax.set_title("题目三：深度8/分支3 博弈树的叶子求值次数（对数轴）",
                 fontsize=11, color=INK)
    style_ax(ax, "叶子求值次数（log）")
    fig.tight_layout()
    fig.savefig(FIGS / "fig4_q3_ordering.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 5：题目四 H=2 / H=4 下五种搜索方法的开销
# ------------------------------------------------------------------
def fig_q4():
    search = data["q4"]["search"]
    methods = ["minimax", "minimax+memo", "alphabeta",
               "alphabeta+smart_order", "alphabeta+reverse_order"]
    short = ["Minimax", "Minimax\n+记忆化", "Alpha-Beta", "AB\n启发排序",
             "AB\n反向排序"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4))
    for ax, H in zip(axes, (2, 4)):
        rows = [next(s for s in search if s["H"] == H
                     and s["method"] == m) for m in methods]
        ev = [r["evaluated"] for r in rows]
        co = [r["cutoffs"] for r in rows]
        bars = ax.bar(short, ev, width=0.62, color=C[:5])
        annotate_bars(ax, bars)
        for b, c0 in zip(bars, co):
            ax.annotate("剪枝%d次" % c0,
                        (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="top", fontsize=7.2, color="#FFFFFF",
                        xytext=(0, -10), textcoords="offset points")
        ax.set_title("H=%d（叶子评估次数，柱内为剪枝次数）" % H,
                     fontsize=10, color=INK)
        style_ax(ax, "叶子评估次数")
        ax.set_ylim(0, max(ev) * 1.25)
        ax.tick_params(axis="x", labelsize=7.6)
    fig.suptitle("题目四：不同搜索方法与访问顺序的开销（结果均与预期一致）",
                 fontsize=11.5, color=INK, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_q4_search.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_q1()
    fig_q2_accum()
    fig_q3_tree()
    fig_q3()
    fig_q4()
    print("图表已生成至", FIGS)
