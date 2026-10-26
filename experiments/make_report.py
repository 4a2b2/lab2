# -*- coding: utf-8 -*-
"""生成 5 页以内的精简版实验报告。

数据来源：results/experiments.json
插图来源：report/figs/*.png
运行：python experiments/make_report.py
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "report" / "figs"
OUT = (Path(sys.argv[1]) if len(sys.argv) > 1
       else ROOT / "report" / "实验报告-实验二-搜索算法.docx")
DATA = json.loads((ROOT / "results" / "experiments.json")
                  .read_text(encoding="utf-8"))

INK, TITLE, ACCENT, MUTED = "2D3748", "1F3A5F", "4A6885", "6B7A8C"
HEAD_FILL, ZEBRA = "E8EEF5", "F6F8FA"
BODY_PT = 9.5


def set_font(run, cn="宋体", en="Times New Roman", size=None, bold=None,
             color=None):
    run.font.name = en
    rpr = run._element.get_or_add_rPr()
    rpr.get_or_add_rFonts().set(qn("w:eastAsia"), cn)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def para(doc, text="", size=BODY_PT, bold=False, color=INK, align=None,
         before=0, after=2, indent=True, line=1.2, cn="宋体", en="Times New Roman"):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Pt(size * 2)
    if align is not None:
        p.alignment = align
    if text:
        set_font(p.add_run(text), cn=cn, en=en, size=size, bold=bold,
                 color=color)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style="Heading %d" % level)
    pf = p.paragraph_format
    pf.space_before = Pt(7 if level == 1 else 4)
    pf.space_after = Pt(3 if level == 1 else 2)
    pf.line_spacing = 1.1
    pf.keep_with_next = True
    r = p.add_run(text)
    if level == 1:
        set_font(r, cn="微软雅黑", en="Arial", size=12.5, bold=True,
                 color=TITLE)
        pPr = p._p.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "2"),
                     ("w:color", "C9D6E3")):
            bottom.set(qn(k), v)
        borders.append(bottom)
        pPr.insert_element_before(
            borders, "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku",
            "w:wordWrap", "w:overflowPunct", "w:topLinePunct",
            "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
            "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing",
            "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
            "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
            "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")
    else:
        set_font(r, cn="微软雅黑", en="Arial", size=10.2, bold=True,
                 color=ACCENT)
    return p


def bullets(doc, items, size=BODY_PT):
    for text in items:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Pt(18)
        pf.first_line_indent = Pt(-9)
        pf.space_before = Pt(0)
        pf.space_after = Pt(1.5)
        pf.line_spacing = 1.2
        set_font(p.add_run("· " + text), size=size, color=INK)


def caption(doc, text, before=1, after=4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run(text), size=8, color=MUTED)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def tight_cell_margins(t, top=8, bottom=8, left=50, right=50):
    tblPr = t._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for name, val in (("top", top), ("left", left),
                      ("bottom", bottom), ("right", right)):
        e = OxmlElement("w:" + name)
        e.set(qn("w:w"), str(val))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblPr.append(mar)


def table(doc, headers, rows, widths, size=8, note=None, keep=False):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tight_cell_margins(t)
    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    trPr.append(OxmlElement("w:tblHeader"))
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        set_font(p.add_run(str(h)), cn="微软雅黑", en="Arial", size=size,
                 bold=True, color="243447")
        shade(c, HEAD_FILL)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        t.rows[-1]._tr.get_or_add_trPr().append(
            OxmlElement("w:cantSplit"))
        for i, v in enumerate(row):
            c = cells[i]
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_font(p.add_run(str(v)), size=size, color=INK)
            if ri % 2 == 1:
                shade(c, ZEBRA)
    for i, w in enumerate(widths):
        for row in t.rows:
            row.cells[i].width = Cm(w)
    if keep or len(t.rows) <= 6:
        for row in t.rows[:-1]:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next = True
    for c in t.rows[-1].cells:
        for p in c.paragraphs:
            p.paragraph_format.keep_with_next = note is not None
    if note:
        caption(doc, note)
    return t


def code_block(doc, code, size=7.8):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    cell = t.rows[0].cells[0]
    cell.width = Cm(17.0)
    tight_cell_margins(t, 6, 6, 60, 60)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + edge)
        for k, v in (("w:val", "single"), ("w:sz", "4"),
                     ("w:color", "DCE3EA")):
            e.set(qn(k), v)
        borders.append(e)
    tcPr.append(borders)
    shade(cell, "F4F6F8")
    for i, line in enumerate(code.strip("\n").split("\n")):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        set_font(p.add_run(line if line else " "), cn="Consolas",
                 en="Consolas", size=size, color="33404F")
    return t


def figure(doc, name, width_cm, note=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = note is not None
    p.add_run().add_picture(str(FIGS / name), width=Cm(width_cm))
    if note:
        caption(doc, note)


# ============================== 数据 ==============================
Q1, Q2, Q3, Q4 = DATA["q1"], DATA["q2"], DATA["q3"], DATA["q4"]
q1r = {(r["maze"], r["heuristic"]): r for r in Q1["runs"]}
multi = Q1["multi_seed"]
avg = {t: sum(m["expanded"] for m in multi if m["heuristic"] == t) / 5
       for t in ("h=0(Dijkstra)", "曼哈顿", "曼哈顿+high_g")}
ids = sorted({m["maze"] for m in multi})
q2g = {r["heuristic"]: r for r in Q2["given"]["runs"]}
q2s = {r["heuristic"]: r for r in Q2["swamp_15x15"]["runs"]}
ab = Q3["random_tree"]["alphabeta"]
mm = Q3["random_tree"]["minimax"]
mat = Q4["matrix"]
fm = Q4["first_moves"]
qs = {(s["H"], s["method"]): s for s in Q4["search"]}

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin, sec.bottom_margin = Cm(1.7), Cm(1.5)
sec.header_distance, sec.footer_distance = Cm(0.9), Cm(0.8)
sec.different_first_page_header_footer = False

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(BODY_PT)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.2
normal.paragraph_format.space_after = Pt(2)

hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hp.paragraph_format.space_after = Pt(0)
set_font(hp.add_run("当代人工智能实验课 · 实验二  搜索算法"),
         cn="微软雅黑", en="Arial", size=8, color="8A98A8")

fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(fp.add_run("第 "), size=8, color=MUTED)
run = fp.add_run()
set_font(run, size=8, color=MUTED)
f1 = OxmlElement("w:fldChar")
f1.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText")
it.set(qn("xml:space"), "preserve")
it.text = "PAGE"
f2 = OxmlElement("w:fldChar")
f2.set(qn("w:fldCharType"), "end")
run._r.append(f1)
run._r.append(it)
run._r.append(f2)
set_font(fp.add_run(" 页"), size=8, color=MUTED)

# ------------------------- 标题区（不单设封面） -------------------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(1)
set_font(p.add_run("实验二：A* 搜索、Minimax 与 Alpha-Beta 剪枝"),
         cn="微软雅黑", en="Arial", size=16, bold=True, color=TITLE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
set_font(p.add_run("当代人工智能实验课    姓名：____________    "
                   "学号：____________    日期：2026 年 10 月"),
         cn="宋体", size=8.5, color=MUTED)

# ------------------------------ 摘要 ------------------------------
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after = Pt(2)
p.paragraph_format.line_spacing = 1.15
set_font(p.add_run("摘要："), cn="黑体", size=8.8, bold=True, color=TITLE)
set_font(p.add_run(
    "实现 A*、Minimax 与 Alpha-Beta 三类搜索算法，完成迷宫寻路、加权地形、"
    "博弈树求值与竞争环境宝藏分配四题；四题输出均与要求一致（最短路径 7 步、"
    "最小代价 7、最佳得分 5、H=2/H=4 时 T2(−1)/T3(3)）。在此之上以扩展节点数、"
    "叶子求值次数与剪枝次数为指标开展成组对照实验，量化了启发强度、平局策略、"
    "启发可采纳性、访问顺序与记忆化/排序的影响，并解释其机制。"),
    cn="宋体", size=8.8, color=INK)
set_font(p.add_run(" 关键词："), cn="黑体", size=8.8, bold=True, color=TITLE)
set_font(p.add_run("A*；启发函数；可采纳性；Alpha-Beta 剪枝；博弈树"),
         size=8.8, color=INK)

# --------------------------- 一、实验设置 ---------------------------
heading(doc, "一、实验设置与实现")
para(doc, "环境为 Python 3.13，算法仅用标准库（heapq、dataclasses），"
          "绘图用 matplotlib，报告由 python-docx 生成；随机实验固定种子，"
          "全部数据可由 experiments/run_experiments.py 一键复现。"
          "代码按“通用核心 + 题目脚本”组织：astar.py 是唯一的 A* 实现，"
          "四题仅注入不同的邻居函数、代价函数与启发函数，从而保证对照公平。")

para(doc, "A* 以 g(n) 为已付代价、h(n) 为剩余估计，按 f=g+h 出堆；"
          "用 g_best 字典加“懒删除”处理重复入堆，目标首次出堆即返回。"
          "Minimax 自底向上回传最值；Alpha-Beta 维护窗口 [α,β]，"
          "在 MAX 处 β 截断、MIN 处 α 截断，并在根层向兄弟子树传递当前最优值。", after=3)
code_block(doc, """while open_heap:                                   # A* 主循环
    _, _, pos, g = heapq.heappop(open_heap)        # (f, -g, 坐标, g)
    if pos in closed or g > g_best.get(pos, INF): continue   # 过期堆项
    if pos == goal: return rebuild(came_from, pos)
    closed.add(pos)
    for nxt, cost in neighbors(pos):
        if g + cost < g_best.get(nxt, INF):
            g_best[nxt] = g + cost; came_from[nxt] = pos
            heapq.heappush(open_heap,
                           (g + cost + h(nxt), -(g + cost), nxt, g + cost))

def alphabeta(node, maxing, alpha, beta):          # Alpha-Beta
    if not node.children: return node.value
    if maxing:
        best = -INF
        for c in node.children:
            best = max(best, alphabeta(c, False, alpha, beta))
            alpha = max(alpha, best)
            if alpha >= beta: break                # β 截断
        return best
    best = INF
    for c in node.children:
        best = min(best, alphabeta(c, True, alpha, beta))
        beta = min(beta, best)
        if beta <= alpha: break                    # α 截断
    return best""")

para(doc, "统计口径统一为：expanded（真正展开的节点数）、generated（入堆次数）、"
          "leaf_evals（叶子求值次数）、cutoffs（真正跳过兄弟节点的剪枝次数）。"
          "仅统计“跳过了剩余兄弟”的剪枝，避免把循环自然结束误计为剪枝。")

# ---------------------------- 二、题目一 ----------------------------
heading(doc, "二、题目一：迷宫寻路")
para(doc, "5×5 网格上以曼哈顿距离为启发，得到 7 步最短路径 "
          "(0,0)→(0,1)→(0,2)→(1,2)→(1,3)→(1,4)→(2,4)→(3,4)，与预期一致。"
          "该启发在四方向、单位代价网格上可采纳且一致，故首次扩展到目标即最优。")
rows = []
for mz, lab in (("given_5x5", "给定 5×5"), ("random_21x21", "随机 21×21"),
                ("serpentine_15x15", "蛇形 15×15")):
    for h, hl in (("h=0(Dijkstra)", "h=0"), ("曼哈顿", "曼哈顿"),
                  ("曼哈顿+high_g", "曼哈顿+high_g")):
        r = q1r[(mz, h)]
        rows.append([lab, hl, r["expanded"], r["generated"],
                     r["max_open"], r["path_steps"]])
table(doc, ["地图", "策略", "扩展", "生成", "队列峰值", "路径步数"], rows,
      [3.0, 4.0, 2.2, 2.2, 2.2, 2.2],
      note="表 1  三张地图上的搜索开销（三种策略路径长度均最优）")
figure(doc, "fig1_q1_heuristic.png", 14.6,
       "图 1  不同启发函数与平局策略下的扩展节点数")
para(doc, "给定小图上三种策略扩展 16/13/13；随机 21×21 迷宫为 283/105/70，"
          "曼哈顿相对 h=0 减少 62.9%，high_g 再减 33.3%。机理是：全部节点 f 值"
          "同为最优代价时，算法只在等值线上推进，而 high_g 把 g 更大（离目标更近）"
          "的节点提前，代价是队列峰值由 26 升至 46，属于时空权衡。"
          "蛇形走廊三者完全相等（126），因为每格仅一个后继，搜索树退化为链，"
          "任何启发都无从发挥——这说明启发的收益取决于地图的分支度，而非算法本身。")
para(doc, "为排除单图偶然性，顺序生成 5 张互不相同且可解的 21×21 迷宫重复实验："
          "每张图上三者均给出相同的 40 步最优路径，扩展数排序完全一致，"
          "平均 301.8/146.8/63.2（−51.4%、再 −57.0%）。"
          "个体收益在 33%～72% 间波动，说明 high_g 的效果依赖等 f 节点的比例。")

# ---------------------------- 三、题目二 ----------------------------
heading(doc, "三、题目二：加权地形的最小代价路径")
para(doc, "把进入格的权值作为边代价，E 记为 0。最优路径为 "
          "(0,0)→(1,0)→(2,0)→(3,0)→(3,1)→(3,2)→(4,2)→(4,3)→(4,4)，"
          "前 7 步各付 1，末步进 E 免费，总代价 7，与预期一致。")
rows = []
for lab, src in (("给定 5×5", q2g), ("沼泽 15×15", q2s)):
    for h, hl in (("zero", "h=0"), ("manhattan", "h=d"),
                  ("adjusted", "h=max(0,d−1)·c_min")):
        rows.append([lab, hl, src[h]["cost"], src[h]["expanded"],
                     src[h]["generated"]])
table(doc, ["地图", "启发函数", "最小代价", "扩展", "生成"], rows,
      [3.0, 5.4, 2.4, 2.4, 2.4],
      note="表 2  三种启发函数的代价与开销（均返回最优代价）")
para(doc, "设剩余曼哈顿距离为 d、非终点格最小进入代价为 c_min。剩余 d 步中"
          "最后一步免费，真实剩余代价至少 (d−1)·c_min，故 "
          "h=max(0,d−1)·c_min 可采纳且一致，保证最优。相反 h=d 最多高估 1"
          "（本图 c_min=1），不满足可采纳性。实验中 h=d 仍返回最优（7 与 39），"
          "但这是实例上的巧合，而非理论保证：若存在真实代价仅高 1 的次优路径且"
          "其 f 更小，就可能被错误返回。")
para(doc, "开销上，给定图 h=0 扩展 14 个、两种非零启发均 10 个；沼泽图依次为"
          "224/156/162，h=d 比修正启发少 3.7%。这正体现“估计更紧但可能失准”"
          "与“保证最优但略保守”的取舍：要求严格最优时应用修正启发或 h=0。")

# ---------------------------- 四、题目三 ----------------------------
heading(doc, "四、题目三：Minimax 与 Alpha-Beta")
para(doc, "样例树自底向上回传：max1=5、max2=9、max3=2，min1=5、min2=2，"
          "根取最大值 5，与预期一致。文档构建代码中 min2 的首个子节点复用了"
          "同一个 max2 对象，本实现忠实还原，故 Minimax 访问 15 个节点、求值 8 个叶子。")
table(doc, ["节点", "类型", "子节点值", "回传"],
      [["max1", "MAX", "3, 5", "5"], ["max2", "MAX", "6, 9", "9"],
       ["max3", "MAX", "1, 2", "2"], ["min1", "MIN", "5, 9", "5"],
       ["min2", "MIN", "9, 2", "2"], ["root", "MAX", "5, 2", "5"]],
      [2.4, 2.4, 6.0, 3.2], note="表 3  样例博弈树的逐层回传")
para(doc, "剪枝位置：根先搜 min1 得 5，于是 α=5；进入 min2 后 max2=9，β=9；"
          "max3 的首个叶子为 1，使 β=1≤α=5，该分支不可能被根选中，"
          "故 max3 的第二个叶子（2）被剪掉。Alpha-Beta 因此只求值 7 个叶子、剪枝 1 次。")
rows = [["Minimax", 9841, mm["leaf_evals"], 0, "100%"],
        ["AB 自然顺序", ab["natural"]["visited"], ab["natural"]["leaf_evals"],
         ab["natural"]["cutoffs"], "18.0%"],
        ["AB 随机顺序（20 次均值）", "—", "%.0f" % ab["random"]["leaf_evals"],
         "—", "18.6%"],
        ["AB 最差顺序", ab["worst"]["visited"], ab["worst"]["leaf_evals"],
         ab["worst"]["cutoffs"], "77.1%"],
        ["AB 完美顺序", ab["best"]["visited"], ab["best"]["leaf_evals"],
         ab["best"]["cutoffs"], "2.45%"]]
table(doc, ["策略", "访问节点", "叶子求值", "剪枝", "占 Minimax"], rows,
      [5.6, 2.8, 2.8, 2.2, 2.8],
      note="表 4  深度 8、分支 3 随机博弈树（6561 个叶子，种子 5）")
figure(doc, "fig3_q3_ordering.png", 11.2,
       "图 2  不同访问顺序下的叶子求值次数（对数轴）")
para(doc, "同一算法仅改变访问顺序，叶子求值从 161 变到 5057，相差 31 倍。"
          "完美顺序 161 与理论界 2·b^(d/2)=2·3⁴=162 几乎重合，验证了实现与理论一致；"
          "最差顺序虽记录 529 次剪枝，但每次只剪掉零星叶子，整体仍接近暴力搜索。"
          "这说明剪枝次数本身不是效率指标，必须结合叶子求值数共同判断；"
          "自然顺序已能凭借根节点先建立 α 下界而获得不错效果。")

# ---------------------------- 五、题目四 ----------------------------
heading(doc, "五、题目四：竞争环境下的宝藏分配")
para(doc, "任务 1 用 A* 计算六个关键点的两两最小移动代价（可通行格代价均 ≥1，"
          "曼哈顿可采纳）。矩阵对称，A 到 T1 为 10 而非曼哈顿 6，因 (0,3)、(1,3) "
          "为障碍需绕行；T3 居中枢纽，到 B 仅 4 步，这正是后续决策差异的根源。")
mrows = [[lab] + mat[i] for i, lab in enumerate(Q4["labels"])]
table(doc, ["", "A", "B", "T1", "T2", "T3", "T4"], mrows,
      [1.8, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
      note="表 5  六个关键点之间的最小移动代价矩阵")

para(doc, "任务 2 将状态定义为 (双方位置, 剩余宝藏, 双方得分, 当前玩家)，"
          "动作为“选一个剩余宝藏并移动过去”，收益 Gain=V(Ti)−d(p,Ti)，"
          "叶子评价 U=Score_A−Score_B，A 最大化、B 最小化。")
rows = [["T1", 9, fm["H=2"]["T1"], fm["H=4"]["T1"]],
        ["T2", 6, fm["H=2"]["T2"], fm["H=4"]["T2"]],
        ["T3", 7, fm["H=2"]["T3"], fm["H=4"]["T3"]],
        ["T4", 7, fm["H=2"]["T4"], fm["H=4"]["T4"]]]
table(doc, ["首步", "宝藏价值", "H=2 的 U", "H=4 的 U"], rows,
      [2.8, 3.0, 4.0, 4.0], note="表 6  A 各首步的 Minimax 值")
para(doc, "H=2 最优为 T2（U=−1）：A 拿 T2 得 +2，B 随后拿收益最高的 T3 得 +3。"
          "H=4 最优变为 T3（U=3）：A 取 T3 虽首步仅 −1，却夺走 B 到 T3 只需 4 步的"
          "高收益目标；主变例 A 取 T3(−1) → B 取 T1(+1) → A 取 T2(0) → B 取 T4(−5)，"
          "U=(−1+0)−(1−5)=3。可见浅层搜索只优化“自己拿多少”，"
          "深层搜索才能把“让对方少拿”折算进来。")
rows = []
for H in (2, 4):
    for m, ml in (("minimax", "Minimax"), ("minimax+memo", "Minimax+记忆化"),
                  ("alphabeta", "Alpha-Beta"),
                  ("alphabeta+smart_order", "AB+收益排序"),
                  ("alphabeta+reverse_order", "AB+反向排序")):
        s = qs[(H, m)]
        rows.append([H, ml, s["expanded"], s["evaluated"], s["cutoffs"],
                     s["best_target"]])
table(doc, ["深度", "方法", "展开状态", "叶子评估", "剪枝", "首步"], rows,
      [1.4, 4.6, 2.4, 2.4, 1.8, 1.8], keep=True,
      note="表 7  不同搜索方法的开销（结果均与预期一致）")
figure(doc, "fig4_q4_search.png", 14.2,
       "图 3  H=2 与 H=4 下五种搜索方法的叶子评估次数")
para(doc, "Alpha-Beta 把叶子评估从 12 降到 8、从 24 降到 16（各 −33.3%）。"
          "记忆化零收益（12→12、24→24）：双方位置随行动单调变化，不存在行动换位，"
          "搜索树没有汇合点，缓存永不命中。收益排序反而削弱剪枝（8→11、16→20），"
          "因为“本步收益”的顺序与“子树真实价值”的顺序不一致：A 的最优首步 T3 "
          "按收益只排第三，α 下界建立得晚；B 端同样把差棋提前，使 β 收敛变慢。"
          "这说明启发式排序必须与评估函数同向，否则会产生负收益。")

# ---------------------------- 六、结论 ----------------------------
heading(doc, "六、结论与创新点")
bullets(doc, [
    "启发函数的收益取决于问题结构：随机迷宫扩展下降 51%～63%，"
    "而蛇形走廊零收益——评估启发时应同时报告地图分支度。",
    "可采纳性是“最坏情况保证”，经验性能反映“平均情况”：h=d 在本题虽非可采纳，"
    "仍得最优且略省 3.7% 节点；要求严格最优时应改用修正启发。",
    "Alpha-Beta 的收益几乎完全由访问顺序决定（161 ～ 5057，相差 31 倍），"
    "完美顺序逼近理论界 162；剪枝次数不能单独作为效率指标。",
    "搜索深度改变策略含义：H=2 选 T2、H=4 选 T3，"
    "深层搜索才能识别阻断价值；记忆化与静态排序在本题均为负结果，"
    "提示优化策略各有适用前提。",
])
para(doc, "创新点：① f 相同时优先扩展 g 更大的 high_g 平局策略，"
          "在随机迷宫上再减 33% 扩展；② 针对“终点免费”推导并证明"
          "h=max(0,d−1)·c_min 的可采纳性与一致性；③ 用独立 Minimax 构造完美顺序，"
          "以 161 对齐理论界 162 校验实现；④ 顺序生成 5 张不同迷宫做稳健性检验；"
          "⑤ 数据与插图均由同一份 JSON 生成，报告数字可完整追溯。")

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(str(OUT))
print("报告已生成：", OUT)
