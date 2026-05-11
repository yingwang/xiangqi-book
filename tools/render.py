#!/usr/bin/env python3
"""象棋棋盘 PNG 渲染器。

坐标约定：file 1-9 (左到右，从看棋人视角)；rank 1-10 (下到上，红方在底)。
红 一线 = file 9；黑 1 路 = file 1。
红 底线 = rank 1；黑 底线 = rank 10。

执行：python3 tools/render.py images
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SS = 4  # 超采样倍数：渲染 4x 后用 LANCZOS 缩到目标尺寸，消除锯齿
CELL = 42 * SS
MARGIN = 22 * SS
W = CELL * 8 + MARGIN * 2
H = CELL * 9 + MARGIN * 2
OUT_W = W // SS
OUT_H = H // SS

BG = (245, 220, 165)
LINE = (60, 40, 20)
RED = (190, 30, 30)
BLACK = (25, 25, 25)
PIECE_BG = (252, 240, 200)
HIGHLIGHT = (220, 50, 50)

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]
FONT_PATH = next(p for p in FONT_CANDIDATES if os.path.exists(p))


def coord(file, rank):
    x = MARGIN + (file - 1) * CELL
    y = MARGIN + (10 - rank) * CELL
    return x, y


def draw_board(draw):
    lw = 2 * SS
    for f in range(1, 10):
        x, _ = coord(f, 1)
        y_top = MARGIN
        y_bot = MARGIN + 9 * CELL
        if f == 1 or f == 9:
            draw.line([(x, y_top), (x, y_bot)], fill=LINE, width=lw)
        else:
            y_riv_t = MARGIN + 4 * CELL
            y_riv_b = MARGIN + 5 * CELL
            draw.line([(x, y_top), (x, y_riv_t)], fill=LINE, width=lw)
            draw.line([(x, y_riv_b), (x, y_bot)], fill=LINE, width=lw)
    for r in range(1, 11):
        _, y = coord(1, r)
        x1 = MARGIN
        x2 = MARGIN + 8 * CELL
        draw.line([(x1, y), (x2, y)], fill=LINE, width=lw)
    # palace diagonals
    for ranks in [(1, 3), (8, 10)]:
        a = coord(4, ranks[1])
        b = coord(6, ranks[0])
        c = coord(6, ranks[1])
        d = coord(4, ranks[0])
        draw.line([a, b], fill=LINE, width=SS)
        draw.line([c, d], fill=LINE, width=SS)


def draw_river(draw, font):
    y_top = MARGIN + 4 * CELL
    y_bot = MARGIN + 5 * CELL
    cy = (y_top + y_bot) / 2
    for text, fx in [("楚  河", 2.5), ("漢  界", 6.5)]:
        x_center = MARGIN + (fx - 1) * CELL
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x_center - tw / 2, cy - th / 2 - bbox[1]), text, font=font, fill=LINE)


def draw_piece(draw, file, rank, char, is_red, font):
    x, y = coord(file, rank)
    r = CELL * 0.42
    color = RED if is_red else BLACK
    draw.ellipse((x - r + 2 * SS, y - r + 3 * SS, x + r + 2 * SS, y + r + 3 * SS), fill=(0, 0, 0, 50))
    draw.ellipse((x - r, y - r, x + r, y + r), fill=PIECE_BG, outline=color, width=2 * SS)
    rin = r - 4 * SS
    draw.ellipse((x - rin, y - rin, x + rin, y + rin), outline=color, width=SS)
    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw / 2 - bbox[0], y - th / 2 - bbox[1]), char, font=font, fill=color)


def draw_highlight(draw, file, rank):
    x, y = coord(file, rank)
    r = CELL * 0.48
    draw.ellipse((x - r, y - r, x + r, y + r), outline=HIGHLIGHT, width=3 * SS)


def render(pieces, output, highlights=None):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_board(draw)
    river_font = ImageFont.truetype(FONT_PATH, 14 * SS)
    draw_river(draw, river_font)
    if highlights:
        for f, r in highlights:
            draw_highlight(draw, f, r)
    piece_font = ImageFont.truetype(FONT_PATH, 22 * SS)
    for f, r, c, is_red in pieces:
        draw_piece(draw, f, r, c, is_red, piece_font)
    img = img.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    img.save(output)
    print(f"wrote {output}")


# === Position library ===

# Starting position
STARTING = (
    [(f, 1, c, True) for f, c in zip([1, 9], "車車")]
    + [(f, 1, c, True) for f, c in zip([2, 8], "馬馬")]
    + [(f, 1, c, True) for f, c in zip([3, 7], "相相")]
    + [(f, 1, c, True) for f, c in zip([4, 6], "仕仕")]
    + [(5, 1, "帥", True)]
    + [(f, 3, "炮", True) for f in [2, 8]]
    + [(f, 4, "兵", True) for f in [1, 3, 5, 7, 9]]
    + [(f, 10, c, False) for f, c in zip([1, 9], "車車")]
    + [(f, 10, c, False) for f, c in zip([2, 8], "馬馬")]
    + [(f, 10, c, False) for f, c in zip([3, 7], "象象")]
    + [(f, 10, c, False) for f, c in zip([4, 6], "士士")]
    + [(5, 10, "將", False)]
    + [(f, 8, "砲", False) for f in [2, 8]]
    + [(f, 7, "卒", False) for f in [1, 3, 5, 7, 9]]
)


# Killshot: 双车错
SHUANGCHE = [
    (5, 10, "將", False),
    (8, 10, "車", True),
    (6, 9, "車", True),
]
SHUANGCHE_HL = [(8, 10), (6, 9)]


# 大胆穿心: 红车冲入中宫吃中士
DADANCHUANXIN = [
    (5, 10, "將", False),
    (4, 9, "士", False),
    (6, 9, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 8, "車", True),
    (5, 1, "炮", True),
]
DADANCHUANXIN_HL = [(5, 8)]


# 闷宫
MENGGONG = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 9, "卒", False),  # 黑卒堵在将前 (杂子，如已被推过来)
    (5, 1, "炮", True),
]
MENGGONG_HL = [(5, 1), (5, 10)]


# 重炮: 双红炮叠在中线
ZHONGPAO = [
    (5, 10, "將", False),
    (4, 9, "士", False),  # 中士已被引开，残留一边
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 5, "炮", True),  # 前炮
    (5, 3, "炮", True),  # 后炮
]
ZHONGPAO_HL = [(5, 5), (5, 3)]


# 铁门栓: 红车冲中线，红炮在底二线顶住
TIEMENSHUAN = [
    (5, 10, "將", False),
    (4, 9, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 6, "車", True),  # 中线红车，已过河
    (5, 1, "炮", True),
]
TIEMENSHUAN_HL = [(5, 6), (5, 1)]


# 马后炮
MAHOUPAO = [
    (5, 10, "將", False),
    (5, 9, "馬", True),
    (5, 7, "炮", True),
]
MAHOUPAO_HL = [(5, 9), (5, 7)]


# 卧槽马
WOCAOMA = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (7, 10, "象", False),
    (3, 9, "馬", True),  # 卧槽位
    (4, 5, "車", True),  # 配合
]
WOCAOMA_HL = [(3, 9)]


# 钓鱼马
DIAOYUMA = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (7, 8, "馬", True),  # 钓鱼位
    (5, 5, "車", True),
]
DIAOYUMA_HL = [(7, 8)]


# 双马杀
SHUANGMA = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (4, 9, "馬", True),  # 挂角马
    (6, 8, "馬", True),  # 外圈
]
SHUANGMA_HL = [(4, 9), (6, 8)]


# 海底捞月
HAIDILAOYUE = [
    (5, 10, "將", False),
    (6, 10, "士", False),
    (5, 5, "車", True),
    (5, 1, "炮", True),
]
HAIDILAOYUE_HL = [(5, 5), (5, 1)]


# === 残局 (ch4) ===

# 单车胜单缺象（黑只剩一只 7 路象）
END_CHE_QUEXIANG = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (7, 10, "象", False),  # 仅剩 7 路象
    (4, 7, "車", True),
    (5, 1, "帥", True),
]


# 单车胜单士
END_CHE_DAN_SHI = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (5, 6, "車", True),
    (5, 2, "帥", True),  # 红帅在中线协同
]


# 车低兵必胜单缺象
END_CHE_DI_BING = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (7, 10, "象", False),
    (5, 9, "兵", True),  # 已挺到底二线的"低兵"
    (4, 5, "車", True),
    (5, 2, "帥", True),
]


# 单马难胜单士（演示和棋形态）
END_MA_DAN_SHI = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (3, 9, "馬", True),
    (5, 2, "帥", True),
]


# === 习题 (ch8 一步杀) ===

# 题 1: 红车在 5 路、底二线；红炮在 5 路、中线
PUZZLE_1 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 9, "車", True),
    (5, 5, "炮", True),
]

# 题 2: 红马卧槽 (7,9)，红炮 (5, 9)，黑左士在 6 路
PUZZLE_2 = [
    (5, 10, "將", False),
    (6, 10, "士", False),
    (7, 9, "馬", True),
    (5, 8, "炮", True),
]

# 题 3: 大胆穿心: 车 (4, 7), 红炮 (5, 3) 中线
PUZZLE_3 = [
    (5, 10, "將", False),
    (4, 9, "士", False),
    (6, 9, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (4, 7, "車", True),
    (5, 3, "炮", True),
]

# 题 4: 重炮 (5, 5)(5, 3)
PUZZLE_4 = [
    (5, 10, "將", False),
    (4, 9, "士", False),  # 中士已被引开，只剩一边
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 5, "炮", True),
    (5, 3, "炮", True),
]

# 题 5: 车 (4, 9)（要吃 4 路士）+ 马 (6, 9) 挂角
PUZZLE_5 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 9, "馬", True),
    (4, 8, "車", True),
]


# === 习题 (ch8 两步杀) ===

# 题 6: 红车 (5, 8) 过河中宫前，红炮底二线
PUZZLE_6 = [
    (5, 10, "將", False),
    (4, 9, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 8, "車", True),
    (5, 2, "炮", True),
]

# 题 7: 双车均沉到对方底二线
PUZZLE_7 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (5, 8, "象", False),
    (7, 9, "車", True),
    (9, 9, "車", True),
]

# 题 8: 车在 4 路 + 钓鱼马 (7, 8)
PUZZLE_8 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (6, 7, "車", True),
    (7, 8, "馬", True),
]

# 题 9: 中线车在红底 + 中线后炮
PUZZLE_9 = [
    (5, 10, "將", False),
    (4, 9, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 2, "車", True),
    (5, 3, "炮", True),
]

# 题 10: 中线双炮 + 4 路车（引离中士）
PUZZLE_10 = [
    (5, 10, "將", False),
    (5, 9, "士", False),  # 中士
    (4, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (4, 8, "車", True),
    (5, 5, "炮", True),
    (5, 3, "炮", True),
]

# 题 11: 挂角马 + 4 路车
PUZZLE_11 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (5, 8, "象", False),  # 中象 5 路
    (6, 9, "馬", True),
    (4, 9, "車", True),
]

# 题 12: 8 路沉底车 + 5 路马威胁 + 红底中线炮
PUZZLE_12 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (8, 9, "車", True),
    (5, 7, "馬", True),
    (5, 3, "炮", True),
]


# === 常见开局 (ch6) - 每个开局走完骨架后的局面 ===

def starting_dict():
    """棋盘起始局面，以 dict 返回方便后续修改：键 = (file, rank)，值 = (char, is_red)."""
    pos = {}
    # red
    for f, c in [(1, "車"), (2, "馬"), (3, "相"), (4, "仕"), (5, "帥"), (6, "仕"), (7, "相"), (8, "馬"), (9, "車")]:
        pos[(f, 1)] = (c, True)
    pos[(2, 3)] = ("炮", True)
    pos[(8, 3)] = ("炮", True)
    for f in [1, 3, 5, 7, 9]:
        pos[(f, 4)] = ("兵", True)
    # black
    for f, c in [(1, "車"), (2, "馬"), (3, "象"), (4, "士"), (5, "將"), (6, "士"), (7, "象"), (8, "馬"), (9, "車")]:
        pos[(f, 10)] = (c, False)
    pos[(2, 8)] = ("砲", False)
    pos[(8, 8)] = ("砲", False)
    for f in [1, 3, 5, 7, 9]:
        pos[(f, 7)] = ("卒", False)
    return pos


def apply(pos, src, dst):
    """从源格搬到目标格（吃子即覆盖）."""
    pos[dst] = pos[src]
    del pos[src]


def dict_to_pieces(pos):
    return [(f, r, c, is_red) for (f, r), (c, is_red) in pos.items()]


def opening_zhongpao_pingfengma():
    """1. 炮二平五 马8进7  2. 马二进三 车9平8  3. 车一平二 马2进3
       4. 兵七进一 卒7进1  5. 马八进七 炮8进4  6. 炮八平九 车8进4"""
    pos = starting_dict()
    apply(pos, (8, 3), (5, 3))   # 炮二平五
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (9, 10), (8, 10)) # 车9平8
    apply(pos, (9, 1), (8, 1))   # 车一平二
    apply(pos, (2, 10), (3, 8))  # 马2进3
    apply(pos, (3, 4), (3, 5))   # 兵七进一
    apply(pos, (7, 7), (7, 6))   # 卒7进1
    apply(pos, (2, 1), (3, 3))   # 马八进七
    apply(pos, (8, 8), (8, 4))   # 炮8进4
    apply(pos, (2, 3), (1, 3))   # 炮八平九
    apply(pos, (8, 10), (8, 6))  # 车8进4
    return dict_to_pieces(pos)


def opening_fangongma():
    """1. 炮二平五 马2进3  2. 马二进三 炮8平6  3. 兵七进一 马8进7
       4. 马八进七 车9平8  5. 车一平二 车8进4"""
    pos = starting_dict()
    apply(pos, (8, 3), (5, 3))   # 炮二平五
    apply(pos, (2, 10), (3, 8))  # 马2进3
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (8, 8), (6, 8))   # 炮8平6
    apply(pos, (3, 4), (3, 5))   # 兵七进一
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (2, 1), (3, 3))   # 马八进七
    apply(pos, (9, 10), (8, 10)) # 车9平8
    apply(pos, (9, 1), (8, 1))   # 车一平二
    apply(pos, (8, 10), (8, 6))  # 车8进4
    return dict_to_pieces(pos)


def opening_xianrenzhilu():
    """1. 兵七进一 炮8平5  2. 马八进七 马8进7  3. 马二进三 车9平8"""
    pos = starting_dict()
    apply(pos, (3, 4), (3, 5))   # 兵七进一
    apply(pos, (8, 8), (5, 8))   # 炮8平5
    apply(pos, (2, 1), (3, 3))   # 马八进七
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (9, 10), (8, 10)) # 车9平8
    return dict_to_pieces(pos)


def opening_feixiang():
    """1. 相三进五 炮8平5  2. 马二进三 马8进7  3. 车一平二 车9平8"""
    pos = starting_dict()
    apply(pos, (7, 1), (5, 3))   # 相三进五
    apply(pos, (8, 8), (5, 8))   # 炮8平5
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (9, 1), (8, 1))   # 车一平二
    apply(pos, (9, 10), (8, 10)) # 车9平8
    return dict_to_pieces(pos)


def opening_qima():
    """1. 马八进七 炮8平5  2. 车九平八 马8进7  3. 兵三进一 车9平8"""
    pos = starting_dict()
    apply(pos, (2, 1), (3, 3))   # 马八进七
    apply(pos, (8, 8), (5, 8))   # 炮8平5
    apply(pos, (1, 1), (2, 1))   # 车九平八
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (7, 4), (7, 5))   # 兵三进一
    apply(pos, (9, 10), (8, 10)) # 车9平8
    return dict_to_pieces(pos)


def opening_shunshoupao():
    """1. 炮二平五 炮2平5  2. 马二进三 马8进7  3. 车一平二 车9平8  4. 车二进六"""
    pos = starting_dict()
    apply(pos, (8, 3), (5, 3))   # 炮二平五
    apply(pos, (2, 8), (5, 8))   # 炮2平5
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (9, 1), (8, 1))   # 车一平二
    apply(pos, (9, 10), (8, 10)) # 车9平8
    apply(pos, (8, 1), (8, 7))   # 车二进六（红车过河抢肋线）
    return dict_to_pieces(pos)


# === 战术 (ch2) ===

# 捉双：红炮在中线同时威胁黑车和黑马
TACTIC_ZHUOSHUANG = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (2, 8, "車", False),
    (8, 8, "馬", False),
    (5, 6, "炮", True),
]
TACTIC_ZHUOSHUANG_HL = [(2, 8), (8, 8)]

# 抽将：红车 (5, 5) 后藏着红马 (5, 7)，马走开就形成将
TACTIC_CHOUJIANG = [
    (5, 10, "將", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (2, 9, "車", False),  # 黑车在 9 线，待会儿被红车吃
    (5, 7, "馬", True),   # 这只马挡住将
    (5, 5, "車", True),
    (2, 2, "帥", True),
]
TACTIC_CHOUJIANG_HL = [(5, 7), (2, 9)]

# 闪击：红炮 (2, 5) 后藏着红马 (5, 5)，马走开露出对黑车的攻击
TACTIC_SHANJI = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (2, 8, "車", False),
    (8, 6, "車", False),
    (5, 5, "馬", True),
    (2, 3, "炮", True),
    (5, 2, "帥", True),
]
TACTIC_SHANJI_HL = [(5, 5), (2, 8)]

# 牵制：黑车在 (5, 9)（中士已被吃）被红车 (5, 6) 牵制，一动就是黑将丢
TACTIC_QIANZHI = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 9, "車", False),
    (5, 6, "車", True),
    (5, 2, "帥", True),
]
TACTIC_QIANZHI_HL = [(5, 9)]

# 引离：红车 (4, 7) 吃 4 路士，把中士引动后红炮做杀
TACTIC_YINLI = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (5, 9, "士", False),  # 中士守住将
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (4, 7, "車", True),
    (5, 3, "炮", True),
]
TACTIC_YINLI_HL = [(4, 7), (5, 9)]


# === 习题 (ch8 三步杀 13-17) ===

# 题 13: 双车 + 中马
PUZZLE_13 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (1, 9, "車", True),
    (9, 9, "車", True),
    (5, 8, "馬", True),
]

# 题 14: 中线车 + 钓鱼马 + 4 路炮 + 黑左车回防
PUZZLE_14 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (6, 10, "車", False),
    (5, 6, "車", True),
    (7, 8, "馬", True),
    (4, 3, "炮", True),
]

# 题 15: 双过河炮 + 6 路车
PUZZLE_15 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (5, 7, "炮", True),
    (4, 7, "炮", True),
    (6, 9, "車", True),
]

# 题 16: 中线车 + 4 路马 + 7 路底炮 + 7 路黑车阻挡
PUZZLE_16 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 6, "車", False),
    (5, 6, "車", True),
    (4, 8, "馬", True),
    (7, 9, "炮", True),
]

# 题 17: 双车 + 卧槽马
PUZZLE_17 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (7, 6, "車", True),
    (4, 9, "車", True),
    (3, 9, "馬", True),
]


# === 习题 (ch8 综合 18-20) ===

# 题 18: 卧槽马 + 中兵已挺到深处 + 中线炮
PUZZLE_18 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (6, 10, "車", False),
    (7, 6, "車", True),
    (3, 9, "馬", True),
    (5, 2, "炮", True),
    (5, 7, "兵", True),
]
PUZZLE_18_HL = [(5, 7)]

# 题 19: 中局 - 中炮过河 + 各家子力对峙
PUZZLE_19 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (7, 8, "馬", False),
    (3, 8, "馬", False),
    (8, 6, "車", False),
    (1, 10, "車", False),
    (7, 9, "砲", False),
    (2, 10, "砲", False),
    (1, 7, "卒", False),
    (3, 7, "卒", False),
    (5, 7, "卒", False),
    (7, 6, "卒", False),
    (9, 7, "卒", False),
    (5, 1, "帥", True),
    (4, 1, "仕", True),
    (6, 1, "仕", True),
    (3, 1, "相", True),
    (7, 1, "相", True),
    (8, 1, "車", True),
    (3, 3, "馬", True),
    (7, 3, "馬", True),
    (5, 6, "炮", True),   # 中炮已过河
    (1, 3, "炮", True),
    (1, 4, "兵", True),
    (3, 5, "兵", True),
    (5, 4, "兵", True),
    (7, 4, "兵", True),
    (9, 4, "兵", True),
]
PUZZLE_19_HL = [(5, 6), (5, 7)]

# 题 20: 略简化的对称中局
PUZZLE_20 = [
    (5, 10, "將", False),
    (4, 10, "士", False),
    (6, 10, "士", False),
    (3, 10, "象", False),
    (7, 10, "象", False),
    (3, 8, "馬", False),
    (7, 8, "馬", False),
    (8, 7, "車", False),  # 黑右炮过河到 4 线 = rank 7
    (1, 10, "車", False),
    (7, 6, "砲", False),  # 左炮过河至 7 路五线
    (5, 1, "帥", True),
    (4, 1, "仕", True),
    (6, 1, "仕", True),
    (3, 1, "相", True),
    (7, 1, "相", True),
    (2, 1, "車", True),
    (8, 4, "車", True),   # 红左车 8 路四线
    (3, 3, "馬", True),
    (7, 3, "馬", True),
    (5, 5, "炮", True),   # 中炮过河 5 线
    (2, 3, "炮", True),
    (1, 4, "兵", True),
    (3, 4, "兵", True),
    (5, 4, "兵", True),
    (7, 4, "兵", True),
    (9, 4, "兵", True),
]
PUZZLE_20_HL = [(8, 4), (8, 7)]


# === 第九章 实战对局解析 ===

def game_phase_opening():
    """中炮 vs 屏风马 12 步后，进入中局过渡。"""
    pos = starting_dict()
    # 1-6 同 6.1 骨架
    apply(pos, (8, 3), (5, 3))
    apply(pos, (8, 10), (7, 8))
    apply(pos, (8, 1), (7, 3))
    apply(pos, (9, 10), (8, 10))
    apply(pos, (9, 1), (8, 1))
    apply(pos, (2, 10), (3, 8))
    apply(pos, (3, 4), (3, 5))
    apply(pos, (7, 7), (7, 6))
    apply(pos, (2, 1), (3, 3))
    apply(pos, (8, 8), (8, 4))
    apply(pos, (2, 3), (1, 3))
    apply(pos, (8, 10), (8, 6))
    # 7. 车九平八  炮2进4
    apply(pos, (1, 1), (2, 1))
    apply(pos, (2, 8), (2, 4))
    # 8. 兵九进一  炮2平7
    apply(pos, (9, 4), (9, 5))
    apply(pos, (2, 4), (7, 4))  # 炮2平7 = file 2 → file 7（黑视角）
    # 9. 马三退一  炮8平7
    apply(pos, (7, 3), (9, 2))  # 红马三退一（红马从七线退到九线，黑5路角落）
    apply(pos, (8, 4), (7, 4))  # 但 (7, 4) 已被黑炮占？
    return dict_to_pieces(pos)


def game_phase_middle():
    """中局攻势形成：红双车出动，攻黑左翼。简化版本以保证可视化清晰。"""
    pos = {}
    # 黑
    pos[(5, 10)] = ("將", False)
    pos[(4, 10)] = ("士", False)
    pos[(6, 10)] = ("士", False)
    pos[(3, 10)] = ("象", False)
    pos[(7, 10)] = ("象", False)
    pos[(3, 8)] = ("馬", False)
    pos[(7, 8)] = ("馬", False)
    pos[(8, 8)] = ("車", False)  # 黑车回到 8 路守
    pos[(2, 7)] = ("砲", False)  # 黑炮
    pos[(7, 4)] = ("砲", False)  # 另一只黑炮深入
    pos[(1, 7)] = ("卒", False)
    pos[(5, 7)] = ("卒", False)
    pos[(7, 6)] = ("卒", False)
    pos[(9, 7)] = ("卒", False)
    # 红
    pos[(5, 1)] = ("帥", True)
    pos[(4, 1)] = ("仕", True)
    pos[(6, 1)] = ("仕", True)
    pos[(3, 1)] = ("相", True)
    pos[(7, 1)] = ("相", True)
    pos[(2, 6)] = ("車", True)  # 红车过河攻击
    pos[(8, 6)] = ("車", True)  # 红另一车也过河
    pos[(3, 3)] = ("馬", True)
    pos[(7, 3)] = ("馬", True)
    pos[(5, 3)] = ("炮", True)  # 中炮
    pos[(1, 3)] = ("炮", True)
    pos[(1, 4)] = ("兵", True)
    pos[(3, 5)] = ("兵", True)
    pos[(5, 4)] = ("兵", True)
    pos[(7, 4)] = ("兵", True)  # 红兵 (7, 4) - 但已被覆盖为黑砲？让兵走开
    # 调整：移除冲突
    del pos[(7, 4)]
    pos[(7, 5)] = ("兵", True)
    pos[(9, 4)] = ("兵", True)
    return dict_to_pieces(pos)


def game_phase_attack():
    """攻王节点：红双车 + 卧槽马在准备杀棋。"""
    pos = {}
    # 黑（已损）
    pos[(5, 10)] = ("將", False)
    pos[(4, 10)] = ("士", False)
    pos[(3, 10)] = ("象", False)
    pos[(7, 10)] = ("象", False)
    pos[(8, 8)] = ("車", False)
    # 红
    pos[(5, 1)] = ("帥", True)
    pos[(4, 1)] = ("仕", True)
    pos[(6, 1)] = ("仕", True)
    pos[(3, 1)] = ("相", True)
    pos[(7, 1)] = ("相", True)
    pos[(4, 9)] = ("車", True)  # 红车沉到 4 路底二线
    pos[(7, 6)] = ("車", True)  # 红另一车过河保持压力
    pos[(3, 9)] = ("馬", True)  # 卧槽马
    pos[(5, 5)] = ("炮", True)
    return dict_to_pieces(pos)


def main():
    """1. 炮二平五 炮2平5  2. 马二进三 马8进7  3. 车一平二 车9平8  4. 车二进六"""
    pos = starting_dict()
    apply(pos, (8, 3), (5, 3))   # 炮二平五
    apply(pos, (2, 8), (5, 8))   # 炮2平5
    apply(pos, (8, 1), (7, 3))   # 马二进三
    apply(pos, (8, 10), (7, 8))  # 马8进7
    apply(pos, (9, 1), (8, 1))   # 车一平二
    apply(pos, (9, 10), (8, 10)) # 车9平8
    apply(pos, (8, 1), (8, 7))   # 车二进六（红车过河抢肋线）
    return dict_to_pieces(pos)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "images"
    os.makedirs(out, exist_ok=True)
    diagrams = [
        ("starting.png", STARTING, None),
        ("kill-shuangche.png", SHUANGCHE, SHUANGCHE_HL),
        ("kill-dadanchuanxin.png", DADANCHUANXIN, DADANCHUANXIN_HL),
        ("kill-menggong.png", MENGGONG, MENGGONG_HL),
        ("kill-zhongpao.png", ZHONGPAO, ZHONGPAO_HL),
        ("kill-tiemenshuan.png", TIEMENSHUAN, TIEMENSHUAN_HL),
        ("kill-mahoupao.png", MAHOUPAO, MAHOUPAO_HL),
        ("kill-wocaoma.png", WOCAOMA, WOCAOMA_HL),
        ("kill-diaoyuma.png", DIAOYUMA, DIAOYUMA_HL),
        ("kill-shuangma.png", SHUANGMA, SHUANGMA_HL),
        ("kill-haidilaoyue.png", HAIDILAOYUE, HAIDILAOYUE_HL),
        ("end-che-quexiang.png", END_CHE_QUEXIANG, None),
        ("end-che-dan-shi.png", END_CHE_DAN_SHI, None),
        ("end-che-di-bing.png", END_CHE_DI_BING, None),
        ("end-ma-dan-shi.png", END_MA_DAN_SHI, None),
        ("puzzle-01.png", PUZZLE_1, None),
        ("puzzle-02.png", PUZZLE_2, None),
        ("puzzle-03.png", PUZZLE_3, None),
        ("puzzle-04.png", PUZZLE_4, None),
        ("puzzle-05.png", PUZZLE_5, None),
        ("puzzle-06.png", PUZZLE_6, None),
        ("puzzle-07.png", PUZZLE_7, None),
        ("puzzle-08.png", PUZZLE_8, None),
        ("puzzle-09.png", PUZZLE_9, None),
        ("puzzle-10.png", PUZZLE_10, None),
        ("puzzle-11.png", PUZZLE_11, None),
        ("puzzle-12.png", PUZZLE_12, None),
        ("opening-zhongpao-pingfengma.png", opening_zhongpao_pingfengma(), None),
        ("opening-fangongma.png", opening_fangongma(), None),
        ("opening-xianrenzhilu.png", opening_xianrenzhilu(), None),
        ("opening-feixiang.png", opening_feixiang(), None),
        ("opening-qima.png", opening_qima(), None),
        ("opening-shunshoupao.png", opening_shunshoupao(), None),
        ("tactic-zhuoshuang.png", TACTIC_ZHUOSHUANG, TACTIC_ZHUOSHUANG_HL),
        ("tactic-choujiang.png", TACTIC_CHOUJIANG, TACTIC_CHOUJIANG_HL),
        ("tactic-shanji.png", TACTIC_SHANJI, TACTIC_SHANJI_HL),
        ("tactic-qianzhi.png", TACTIC_QIANZHI, TACTIC_QIANZHI_HL),
        ("tactic-yinli.png", TACTIC_YINLI, TACTIC_YINLI_HL),
        ("puzzle-13.png", PUZZLE_13, None),
        ("puzzle-14.png", PUZZLE_14, None),
        ("puzzle-15.png", PUZZLE_15, None),
        ("puzzle-16.png", PUZZLE_16, None),
        ("puzzle-17.png", PUZZLE_17, None),
        ("puzzle-18.png", PUZZLE_18, PUZZLE_18_HL),
        ("puzzle-19.png", PUZZLE_19, PUZZLE_19_HL),
        ("puzzle-20.png", PUZZLE_20, PUZZLE_20_HL),
        ("game-middle.png", game_phase_middle(), None),
        ("game-attack.png", game_phase_attack(), None),
    ]
    for filename, pieces, hl in diagrams:
        render(pieces, os.path.join(out, filename), hl)


if __name__ == "__main__":
    main()
