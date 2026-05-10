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

CELL = 64
MARGIN = 32
W = CELL * 8 + MARGIN * 2
H = CELL * 9 + MARGIN * 2

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
    for f in range(1, 10):
        x, _ = coord(f, 1)
        y_top = MARGIN
        y_bot = MARGIN + 9 * CELL
        if f == 1 or f == 9:
            draw.line([(x, y_top), (x, y_bot)], fill=LINE, width=2)
        else:
            y_riv_t = MARGIN + 4 * CELL
            y_riv_b = MARGIN + 5 * CELL
            draw.line([(x, y_top), (x, y_riv_t)], fill=LINE, width=2)
            draw.line([(x, y_riv_b), (x, y_bot)], fill=LINE, width=2)
    for r in range(1, 11):
        _, y = coord(1, r)
        x1 = MARGIN
        x2 = MARGIN + 8 * CELL
        draw.line([(x1, y), (x2, y)], fill=LINE, width=2)
    # palace diagonals
    for ranks in [(1, 3), (8, 10)]:
        a = coord(4, ranks[1])
        b = coord(6, ranks[0])
        c = coord(6, ranks[1])
        d = coord(4, ranks[0])
        draw.line([a, b], fill=LINE, width=1)
        draw.line([c, d], fill=LINE, width=1)


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
    draw.ellipse((x - r + 2, y - r + 3, x + r + 2, y + r + 3), fill=(0, 0, 0, 50))
    draw.ellipse((x - r, y - r, x + r, y + r), fill=PIECE_BG, outline=color, width=2)
    rin = r - 4
    draw.ellipse((x - rin, y - rin, x + rin, y + rin), outline=color, width=1)
    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw / 2 - bbox[0], y - th / 2 - bbox[1]), char, font=font, fill=color)


def draw_highlight(draw, file, rank):
    x, y = coord(file, rank)
    r = CELL * 0.48
    draw.ellipse((x - r, y - r, x + r, y + r), outline=HIGHLIGHT, width=3)


def render(pieces, output, highlights=None):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_board(draw)
    river_font = ImageFont.truetype(FONT_PATH, 18)
    draw_river(draw, river_font)
    if highlights:
        for f, r in highlights:
            draw_highlight(draw, f, r)
    piece_font = ImageFont.truetype(FONT_PATH, 30)
    for f, r, c, is_red in pieces:
        draw_piece(draw, f, r, c, is_red, piece_font)
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
    ]
    for filename, pieces, hl in diagrams:
        render(pieces, os.path.join(out, filename), hl)


if __name__ == "__main__":
    main()
