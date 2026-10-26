# 实验二：搜索算法（A* / Minimax / Alpha-Beta 剪枝）

当代人工智能实验课 · 实验二。实现四个题目并通过对照实验分析启发函数、
访问顺序与剪枝策略对搜索效率的影响。

## 一、运行环境

- Python 3.10+（开发与测试使用 3.13）
- matplotlib（仅 `experiments/make_charts.py` 需要，用于生成报告图表）
- 无其他第三方依赖，算法部分仅使用标准库

## 二、目录结构

```
lab2/
├── src/                        # 四道题目的实现（可独立运行）
│   ├── astar.py                #   通用 A* 核心（优先队列/懒删除/统计）
│   ├── grid_utils.py           #   网格工具：方向常量、进入代价解析
│   ├── q1_maze_astar.py        #   题目一：迷宫寻路（曼哈顿启发）
│   ├── q2_weighted_astar.py    #   题目二：加权地形（可采纳启发讨论）
│   ├── q3_alphabeta.py         #   题目三：Minimax 与 Alpha-Beta
│   └── q4_treasure.py          #   题目四：距离矩阵 + 博弈搜索
├── experiments/
│   ├── run_experiments.py      # 一键复现全部对照实验数据
│   ├── make_charts.py          # 由实验数据生成报告插图
│   └── make_report.py          # 由实验数据生成 Word 报告
├── results/
│   └── experiments.json        # 实验数据（脚本自动生成）
├── report/
│   ├── figs/                   # 报告插图 fig1~fig4（脚本自动生成）
│   └── 实验报告-实验二-搜索算法.docx
└── README.md
```

## 三、快速开始

```bash
# 1. 运行四个题目的测试用例（每题文件均可独立执行）
python src/q1_maze_astar.py
python src/q2_weighted_astar.py
python src/q3_alphabeta.py
python src/q4_treasure.py

# 2. 复现全部对照实验（约几秒，输出 results/experiments.json）
python experiments/run_experiments.py

# 3. 重新生成报告插图（输出 report/figs/*.png）
python experiments/make_charts.py

# 4. 重新生成实验报告（输出 report/实验报告-实验二-搜索算法.docx）
python experiments/make_report.py
```

## 四、题目输入输出与测试结果

| 题目 | 输入 | 输出 | 测试结果 |
|---|---|---|---|
| 一 迷宫寻路 | 起点/终点 `Tuple[int,int]`，地图 `List[List[str]]` | 路径坐标序列 `List[Tuple[int,int]]`，无解返回 `[]` | 与预期路径一致（8 个坐标） |
| 二 加权地形 | 起点/终点，数字地图 | 最小总代价 `int`，无解返回 `-1` | **7**，与预期一致 |
| 三 博弈树 | `TreeNode`（叶子带 `value`，内节点带 `children`） | MAX 玩家最佳得分 | **5**，与预期一致 |
| 四 宝藏分配 | 题目给定地图与宝藏价值 | 6×6 距离矩阵；各深度下 `{"best_target", "best_value"}` | H=2 → **T2 / -1**；H=4 → **T3 / 3**，均与预期一致 |

## 五、实现要点

- **A\***（`src/astar.py`）：二叉堆优先队列按 f=g+h 出堆；`g_best` 字典 +
  懒删除处理重复入堆；回溯指针重建路径。统计口径：`expanded`（真正展开
  的节点数）、`generated`（入堆次数）、`max_open`（队列峰值）。
  支持 `high_g` 平局策略（f 相同优先扩展离目标更近的节点）。
- **题目二启发函数**：`h = max(0, d-1)·c_min` 可采纳且一致；曼哈顿
  h=d 因“进入 E 免费”最多高估 1（报告中有理论分析与数值对照）。
- **Alpha-Beta**：MAX 维护下界 α、MIN 维护上界 β，α≥β 时剪断剩余兄弟；
  根节点向兄弟子树传递当前最优值以收缩窗口。
- **题目四博弈状态**：`GameState(双方位置, 剩余宝藏, 累计得分, 当前玩家)`；
  动作 = 选一个剩余宝藏，收益 `Gain = V(Ti) − d(p, Ti)`；
  叶子评价 `U = Score_A − Score_B`；支持 Minimax / Alpha-Beta /
  记忆化 / 三种动作排序的对照开关。

## 六、主要实验结论（详见实验报告）

1. 启发函数的收益取决于地图结构：随机迷宫上 h=0 → 曼哈顿 → high_g
   依次减少扩展节点（283 → 105 → 70）；蛇形迷宫无岔路，三者同为 126。
2. 题目二中 h=d 虽不严格可采纳（最多高估 1），但在“边权≥1 且仅终点
   免费”的代价结构下仍得最优解；修正启发 h=max(0,d−1)·c_min 在沼泽图上
   开销略高但保证理论最优性。
3. Alpha-Beta 剪枝对访问顺序极其敏感：深度 8/分支 3 的树上叶子求值
   6561（Minimax）→ 161（完美排序），逼近理论界 2·b^(d/2)=162；
   最差顺序几乎退化为暴力搜索（5057）。
4. 题目四的小规模博弈树中，静态收益排序与真实价值顺序不相关，
   反而降低剪枝效率；记忆化因该博弈不存在行动换位而无增益——
   两者均为有价值的“负结果”，说明优化策略的适用前提。
