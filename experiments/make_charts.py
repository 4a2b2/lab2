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
# 图 2：题目二 最优路径 f=g+h 累计曲线 + 启发函数开销对比
# ------------------------------------------------------------------
def fig_q2():
    acc = data["q2"]["given"]["accumulation"]
    xs = [r["step"] for r in acc]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.4),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    ax1.plot(xs, [r["g"] for r in acc], "-o", color=C[0], ms=4,
             lw=1.8, label="g(n) 已付代价")
    ax1.plot(xs, [r["h_adj"] for r in acc], "-s", color=C[1], ms=4,
             lw=1.8, label="h(n)=max(0,d−1)·c_min")
    ax1.plot(xs, [r["f_adj"] for r in acc], "--^", color=C[3], ms=4,
             lw=1.6, label="f(n)=g+h")
    ax1.plot(xs, [r["f_man"] for r in acc], ":", color=C[2], ms=4,
             lw=1.6, label="f(n)（曼哈顿 h=d）")
    ax1.set_xlabel("路径步序（S → E）", fontsize=9, color=INK)
    ax1.set_title("最优路径上的 g/h/f 累计过程（给定图）",
                  fontsize=10, color=INK)
    ax1.legend(fontsize=8, frameon=False)
    style_ax(ax1, "代价")

    runs = data["q2"]["given"]["runs"] + data["q2"]["swamp_15x15"]["runs"]
    labels = ["给定图\nh=0", "给定图\nh=d", "给定图\nh=max(0,d−1)",
              "沼泽图\nh=0", "沼泽图\nh=d", "沼泽图\nh=max(0,d−1)"]
    vals = [r["expanded"] for r in runs]
    colors = [C[0], C[1], C[2]] * 2
    bars = ax2.bar(labels, vals, width=0.62, color=colors)
    annotate_bars(ax2, bars)
    ax2.set_title("搜索开销：扩展节点数（两图均得最优代价）",
                  fontsize=10, color=INK)
    ax2.tick_params(axis="x", labelsize=7.6)
    style_ax(ax2, "扩展节点数")
    ax2.set_ylim(0, max(vals) * 1.18)
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_q2_costs.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 3：题目三 大随机树上 Minimax 与不同访问顺序的 Alpha-Beta
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
    fig.savefig(FIGS / "fig3_q3_ordering.png", bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
# 图 4：题目四 H=2 / H=4 下五种搜索方法的开销
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
    fig.savefig(FIGS / "fig4_q4_search.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_q1()
    fig_q2()
    fig_q3()
    fig_q4()
    print("图表已生成至", FIGS)
