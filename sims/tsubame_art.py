"""ツバメの一生ロングの絵の部品 — 2026-11-08 作成

ほかのロングの絵の部品と同じ考え方。
  - 平塗り・黒い輪郭線なし・陰はうすく1段だけ。丸み・やわらかい色
  - ツバメは平たい絵柄（背は濃い青・おなかはクリーム色・のどは赤茶・尾は長い二股）
  - いなくなる場面は、うすくなって消えるだけ（襲われる・倒れる絵は描かない）。カラスやヘビは小さなアイコンだけ
  - 地図は Natural Earth（パブリックドメイン）の実データ。python -X utf8 sims/tsubame_art.py で sims/tsubame_map_data.py を作る

座標: (x, y) は基本「足もと／置いた面の中央下」。W=1920, H=1080 を想定。
"""
import json
import math
import random
from pathlib import Path

import cairo

from danchi_people import _rgb, mix

W, H = 1920, 1080
FONT = "Meiryo"
INK = "#3a2c20"

NAVY = "#35538d"          # ツバメの背
NAVY_D = "#27406f"        # 翼
NAVY_Y = "#5d78a6"        # 若いツバメの背（少しうすい）
BELLY = "#f8eed8"
THROAT = "#d8694a"
THROAT_Y = "#eeb08e"
BEAKC = "#2b2b36"
LEGC = "#8a6a55"
EGGC = "#fffaf0"
MUD = "#a9795a"
MUD_D = "#7f5640"
MUD_L = "#c79b7e"
WALL = "#f2e6cc"
WALL_D = "#e3d3b2"
ROOFC = "#6a5b55"
ROOF_D = "#51443f"
WIREC = "#3c4352"


def _set(ctx, h, a=1.0):
    r, g, b = _rgb(h)
    ctx.set_source_rgba(r, g, b, a)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def ell(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(rx, ry)
    ctx.new_sub_path()
    ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
    ctx.restore()


def _grp(ctx, a, fn):
    if a <= 0.003:
        return
    if a >= 0.997:
        fn()
        return
    ctx.push_group()
    fn()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def cloud(ctx, x, y, s, col="#ffffff", a=0.9):
    _set(ctx, col, a)
    for dx, dy, r in ((-0.9, 0.1, 0.55), (-0.3, -0.25, 0.75), (0.45, -0.1, 0.65), (1.0, 0.15, 0.5)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi)
        ctx.fill()
    rrect(ctx, x - 1.2 * s, y + 0.1 * s, 2.7 * s, 0.55 * s, 0.27 * s)
    ctx.fill()


# ---------------------------------------------------------------- ツバメ
def _perch(ctx, young, col, tail_k, beak_open=0.0):
    navy = col or (NAVY_Y if young else NAVY)
    wing = mix(navy, "#000000", 0.18)
    tl = (0.5 if young else 1.0) * tail_k
    # 足
    _set(ctx, LEGC)
    ctx.set_line_width(2.6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for lx in (-1, 9):
        ctx.move_to(lx, -17)
        ctx.line_to(lx - 1, 0)
        ctx.stroke()
    # 尾（長い二股）
    _set(ctx, mix(navy, "#000000", 0.08))
    ctx.move_to(-18, -46)
    ctx.line_to(-18 - 62 * tl, -40)
    ctx.line_to(-18 - 42 * tl, -34)
    ctx.line_to(-18 - 66 * tl, -26)
    ctx.line_to(-16, -26)
    ctx.close_path()
    ctx.fill()
    # 体
    _set(ctx, navy)
    ell(ctx, 2, -35, 35, 17, -0.12)
    ctx.fill()
    _set(ctx, BELLY)
    ell(ctx, 7, -27, 28, 9.5, -0.10)
    ctx.fill()
    # 翼
    _set(ctx, wing)
    ctx.move_to(18, -47)
    ctx.curve_to(-8, -56, -40, -50, -64 * (0.85 if young else 1.0), -31)
    ctx.curve_to(-38, -34, -10, -31, 12, -38)
    ctx.close_path()
    ctx.fill()
    # 頭
    _set(ctx, navy)
    ctx.arc(30, -50, 14, 0, 2 * math.pi)
    ctx.fill()
    # のど
    _set(ctx, THROAT_Y if young else THROAT)
    ell(ctx, 37, -43.5, 9.5, 6.4, 0.2)
    ctx.fill()
    # くちばし
    _set(ctx, BEAKC)
    ctx.move_to(41, -53)
    ctx.line_to(51.5 + 3 * beak_open, -49.5)
    ctx.line_to(41, -46.5)
    ctx.close_path()
    ctx.fill()
    # 目
    _set(ctx, "#1c2230")
    ctx.arc(34, -54, 2.7, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, "#ffffff", 0.9)
    ctx.arc(34.8, -54.8, 0.9, 0, 2 * math.pi)
    ctx.fill()


def _fly(ctx, phase, young, col, tail_k):
    navy = col or (NAVY_Y if young else NAVY)
    wing = mix(navy, "#000000", 0.18)
    far = mix(navy, "#ffffff", 0.18)
    tl = (0.55 if young else 1.0) * tail_k
    w = math.sin(phase)

    def wing_path(wv, root_x):
        tip = (root_x - 44, -6 - 62 * wv)
        ctx.move_to(root_x + 12, -7)
        ctx.curve_to(root_x - 4, -7 - 36 * wv, root_x - 28, -7 - 56 * wv, *tip)
        ctx.curve_to(root_x - 36, -7 - 26 * wv, root_x - 28, -1, root_x - 12, 2)
        ctx.close_path()
    # 奥の翼
    _set(ctx, far)
    wing_path(-0.55 * w - 0.25, -4)
    ctx.fill()
    # 尾
    _set(ctx, mix(navy, "#000000", 0.08))
    ctx.move_to(-24, -4)
    ctx.line_to(-24 - 52 * tl, -12)
    ctx.line_to(-24 - 36 * tl, 2)
    ctx.line_to(-24 - 54 * tl, 14)
    ctx.line_to(-24, 6)
    ctx.close_path()
    ctx.fill()
    # 体
    _set(ctx, navy)
    ell(ctx, 0, 0, 32, 12.5, -0.08)
    ctx.fill()
    _set(ctx, BELLY)
    ell(ctx, 3, 5, 25, 7, -0.06)
    ctx.fill()
    # 頭
    _set(ctx, navy)
    ctx.arc(27, -3, 11, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, THROAT_Y if young else THROAT)
    ell(ctx, 33.5, 2.5, 7.5, 5, 0.25)
    ctx.fill()
    _set(ctx, BEAKC)
    ctx.move_to(35, -6)
    ctx.line_to(45, -2)
    ctx.line_to(35, 0)
    ctx.close_path()
    ctx.fill()
    _set(ctx, "#1c2230")
    ctx.arc(31, -6, 2.3, 0, 2 * math.pi)
    ctx.fill()
    # 手前の翼
    _set(ctx, wing)
    wing_path(w, 2)
    ctx.fill()


def draw_swallow(ctx, x, y, h, facing=1, pose="perch", phase=0.0, a=1.0, young=False, tilt=0.0, col=None, tail=1.0):
    """ツバメ。pose='perch'（とまる・(x,y)=足もと・h=足もとから頭までの高さ）／'fly'（飛ぶ・(x,y)=体の中心・h=perch と同じ尺度）。
    young=True でうすい色・短い尾・のどが淡い（巣立ったばかり）"""
    u = h / 64.0

    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(u * facing, u)
        ctx.rotate(tilt)
        if pose == "perch":
            _perch(ctx, young, col, tail)
        else:
            _fly(ctx, phase, young, col, tail)
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 卵・ヒナ
def draw_egg(ctx, x, y, r, a=1.0, spots=True, seed=0, tilt=0.0, col=EGGC, shade=True):
    """卵。(x, y)=中心・r=縦の半径（横は0.78倍）"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(tilt)
        _set(ctx, col)
        ell(ctx, 0, 0, r * 0.78, r)
        ctx.fill()
        if shade:
            _set(ctx, mix(col, "#a08560", 0.28), 0.8)
            ctx.save()
            ell(ctx, 0, 0, r * 0.78, r)
            ctx.clip()
            ell(ctx, -r * 0.18, -r * 0.22, r * 0.86, r * 1.0)
            ctx.rectangle(-r, -r, 2 * r, 2 * r)
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            ctx.fill()
            ctx.restore()
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        if spots and r >= 14:
            rnd = random.Random(seed * 7 + 3)
            _set(ctx, "#cdae92", 0.9)
            for _ in range(6):
                ang, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.1, 0.55)
                ctx.arc(math.cos(ang) * r * 0.5 * rr, math.sin(ang) * r * 0.8 * rr, r * 0.055, 0, 2 * math.pi)
                ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


def draw_chick(ctx, x, y, s, grow=0.0, beak=0.0, a=1.0, facing=1, eye_closed=False):
    """ヒナ。(x, y)=足もと・s=全体の高さ。grow 0=かえったて（ピンクの地肌）〜1=巣立ち前（青い羽）。beak 0〜1=口を開ける"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s / 100.0 * facing, s / 100.0)
        skin = mix("#eebb9f", "#c9b5a0", grow)
        # 体
        _set(ctx, skin)
        ell(ctx, 0, -28, 38, 28)
        ctx.fill()
        if grow > 0.05:
            _set(ctx, NAVY_Y, min(1.0, grow * 1.3))
            ell(ctx, -6, -34, 33, 20, -0.15)
            ctx.fill()
            _set(ctx, BELLY, min(1.0, grow * 1.2))
            ell(ctx, 4, -17, 28, 11)
            ctx.fill()
        # 頭
        _set(ctx, skin if grow < 0.5 else mix(NAVY_Y, skin, 0.35))
        ctx.arc(18, -62, 24, 0, 2 * math.pi)
        ctx.fill()
        # 口
        ob = 4 + 20 * beak
        _set(ctx, "#d9573f")
        ell(ctx, 40, -60, 9 + 4 * beak, 4 + ob * 0.5)
        ctx.fill()
        _set(ctx, "#f3c34e")
        ctx.move_to(32, -66 - ob * 0.45)
        ctx.line_to(52 + 3 * beak, -64 - ob * 0.55)
        ctx.line_to(34, -58 - ob * 0.1)
        ctx.close_path()
        ctx.fill()
        ctx.move_to(32, -56 + ob * 0.1)
        ctx.line_to(51 + 2 * beak, -56 + ob * 0.55)
        ctx.line_to(34, -52 + ob * 0.4)
        ctx.close_path()
        ctx.fill()
        # 目
        _set(ctx, "#2b2230")
        if eye_closed:
            ctx.set_line_width(3.2)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.arc(20, -72, 5.0, math.pi * 0.1, math.pi * 0.9)
            ctx.stroke()
        else:
            ctx.arc(20, -72, 3.4, 0, 2 * math.pi)
            ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


def draw_swallow_front(ctx, x, y, h, spread=1.0, a=1.0, insect=True):
    """正面（こちらを向いた）ツバメ。(x, y)=体の中心・h=全体の高さ。spread=翼の開き（0〜1.2）。くちばしに小さな虫"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(h / 100.0, h / 100.0)
        wing = mix(NAVY, "#000000", 0.18)
        for sg in (-1, 1):                      # 翼
            _set(ctx, wing)
            ctx.move_to(sg * 12, -14)
            ctx.curve_to(sg * (40 + 30 * spread), -34 - 22 * spread, sg * (75 + 20 * spread), -26 - 30 * spread, sg * (96 * (0.6 + 0.4 * spread)), -8 - 34 * spread + 10)
            ctx.curve_to(sg * (70 + 10 * spread), -2, sg * 40, 10, sg * 12, 14)
            ctx.close_path()
            ctx.fill()
        _set(ctx, NAVY_D)                      # 尾
        ctx.move_to(-10, 30)
        ctx.line_to(-18, 58)
        ctx.line_to(-3, 50)
        ctx.line_to(0, 58)
        ctx.line_to(3, 50)
        ctx.line_to(18, 58)
        ctx.line_to(10, 30)
        ctx.close_path()
        ctx.fill()
        _set(ctx, BELLY)                       # おなか
        ell(ctx, 0, 6, 17, 30)
        ctx.fill()
        _set(ctx, NAVY)                        # 頭
        ctx.arc(0, -26, 17, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, THROAT)                      # のど（くちばしのすぐ下に付く。2026-11-08 統括: 胸当てに見えないよう小さく上へ）
        ell(ctx, 0, -7, 8, 4.5)
        ctx.fill()
        ell(ctx, 0, -39.5, 5, 2.4)             # おでこの小さな赤
        ctx.fill()
        _set(ctx, "#ffffff")
        for ex in (-8, 8):
            ctx.arc(ex, -32, 3.6, 0, 2 * math.pi)
            ctx.fill()
        _set(ctx, "#1c2230")
        for ex in (-8, 8):
            ctx.arc(ex, -32, 2.0, 0, 2 * math.pi)
            ctx.fill()
        _set(ctx, "#b8403a")                   # 開いた口の中
        ell(ctx, 0, -17.5, 6.5, 3.4)
        ctx.fill()
        _set(ctx, "#f3c34e")                   # 黄色いふちの小さな三角2つ
        ctx.move_to(-10, -25)
        ctx.line_to(10, -25)
        ctx.line_to(0, -17.5)
        ctx.close_path()
        ctx.fill()
        ctx.move_to(-9, -10)
        ctx.line_to(9, -10)
        ctx.line_to(0, -17.5)
        ctx.close_path()
        ctx.fill()
        if insect:                              # 虫を横向きにくわえる（体は緑・羽2枚）
            _set(ctx, "#cfe3cf", 0.9)
            ell(ctx, -2.5, -20.5, 3.8, 1.8, -0.5)
            ctx.fill()
            ell(ctx, 2.5, -20.5, 3.8, 1.8, 0.5)
            ctx.fill()
            _set(ctx, "#4f9a3c")
            ell(ctx, 0, -17.5, 6.0, 2.6, 0.0)
            ctx.fill()
            _set(ctx, "#2f6a28")
            ctx.arc(5.5, -17.5, 1.9, 0, 2 * math.pi)
            ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 巣・家
def nest_back(ctx, x, y, w, a=1.0):
    """巣の奥側（ふちの内側）。(x, y)=ふちの中心"""
    def body():
        _set(ctx, MUD_D)
        ell(ctx, x, y, w / 2, w * 0.11)
        ctx.fill()
        _set(ctx, "#5e402f")
        ell(ctx, x, y + w * 0.012, w * 0.43, w * 0.085)
        ctx.fill()
    _grp(ctx, a, body)


def nest_front(ctx, x, y, w, a=1.0):
    """巣の手前（おわん）。卵・ヒナをこのあとに描くと隠れ、前に描くと中に見える"""
    def body():
        _set(ctx, MUD)
        ctx.move_to(x - w / 2, y)
        ctx.curve_to(x - w / 2, y + w * 0.40, x - w * 0.22, y + w * 0.47, x, y + w * 0.47)
        ctx.curve_to(x + w * 0.22, y + w * 0.47, x + w / 2, y + w * 0.40, x + w / 2, y)
        ctx.curve_to(x + w * 0.40, y + w * 0.11, x + w * 0.2, y + w * 0.115, x, y + w * 0.115)
        ctx.curve_to(x - w * 0.2, y + w * 0.115, x - w * 0.40, y + w * 0.11, x - w / 2, y)
        ctx.close_path()
        ctx.fill()
        # つちのつぶ
        rnd = random.Random(int(w) % 97)
        for _ in range(int(w / 6)):
            px = x + rnd.uniform(-0.46, 0.46) * w
            py = y + rnd.uniform(0.14, 0.44) * w
            if abs(px - x) > w * 0.5 * (1 - (py - y) / (w * 0.5) * 0.85):
                continue
            _set(ctx, MUD_L if rnd.random() < 0.5 else MUD_D, 0.55)
            ctx.arc(px, py, w * rnd.uniform(0.008, 0.02), 0, 2 * math.pi)
            ctx.fill()
        # ふちのつや
        _set(ctx, MUD_L, 0.85)
        ctx.set_line_width(max(3, w * 0.022))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(1.0, 0.22)
        ctx.new_sub_path()
        ctx.arc(0, 0, w / 2 - w * 0.01, 0.12, math.pi - 0.12)
        ctx.restore()
        ctx.stroke()
    _grp(ctx, a, body)


def draw_nest(ctx, x, y, w, eggs=0, a=1.0, seed=0):
    """卵が eggs 個入った巣（親なし）"""
    def body():
        nest_back(ctx, x, y, w)
        for i, (ex, ey, tl) in enumerate(egg_slots(x, y, w, eggs)):
            draw_egg(ctx, ex, ey, w * 0.075, spots=True, seed=seed + i, tilt=tl)
        nest_front(ctx, x, y, w)
    _grp(ctx, a, body)


def egg_slots(x, y, w, n):
    """巣の中の卵の並べ方 [(x, y, tilt)]。最大9個"""
    base = [(-0.24, 0.015, -0.3), (0.0, 0.0, 0.1), (0.24, 0.015, 0.35), (-0.12, 0.05, 0.2), (0.12, 0.05, -0.2),
            (-0.34, 0.04, 0.1), (0.34, 0.04, -0.1), (0.0, 0.07, 0.3), (-0.2, 0.075, -0.2)]
    order = {1: [1], 2: [0, 2], 3: [0, 1, 2], 4: [0, 1, 2, 3], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 7]}
    idx = order.get(n, list(range(min(n, 9))))
    return [(x + base[i][0] * w, y - w * 0.015 + base[i][1] * w, base[i][2]) for i in idx]


def bg_wall(ctx, x0=0, x1=W, y0=0, y1=H):
    """家の壁と軒（近景）。上に軒の屋根、壁、うすい板の線"""
    _set(ctx, WALL)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.fill()
    _set(ctx, WALL_D, 0.7)
    for i in range(0, int(x1 - x0), 150):
        ctx.rectangle(x0 + i, y0 + 150, 6, y1 - y0 - 150)
        ctx.fill()
    _set(ctx, ROOFC)
    ctx.rectangle(x0, y0, x1 - x0, 110)
    ctx.fill()
    _set(ctx, ROOF_D)
    ctx.rectangle(x0, y0 + 110, x1 - x0, 26)
    ctx.fill()
    _set(ctx, "#cdbb97")
    ctx.rectangle(x0, y0 + 136, x1 - x0, 14)
    ctx.fill()


def house_far(ctx, x0, x1, ytop, wall=WALL, roof=ROOFC):
    """遠景の家（軒が横に張り出す）。(x0..x1)=壁の幅・ytop=軒の下の線"""
    _set(ctx, wall)
    ctx.rectangle(x0, ytop, x1 - x0, H - ytop)
    ctx.fill()
    _set(ctx, mix(wall, "#000000", 0.07))
    ctx.rectangle(x0, ytop, x1 - x0, 22)
    ctx.fill()
    _set(ctx, roof)
    ctx.move_to(x0 - 60, ytop - 8)
    ctx.line_to(x0 + 40, ytop - 120)
    ctx.line_to(x1 - 40, ytop - 120)
    ctx.line_to(x1 + 60, ytop - 8)
    ctx.close_path()
    ctx.fill()
    _set(ctx, mix(roof, "#000000", 0.25))
    ctx.rectangle(x0 - 60, ytop - 14, x1 - x0 + 120, 16)
    ctx.fill()


def window(ctx, x, y, w, h):
    _set(ctx, "#8cb6d1")
    rrect(ctx, x, y, w, h, 8)
    ctx.fill()
    _set(ctx, "#f7f3e8")
    ctx.set_line_width(7)
    rrect(ctx, x, y, w, h, 8)
    ctx.stroke()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.stroke()


def wire(ctx, x0, y0, x1, y1, sag=14.0, w=4.0, a=1.0):
    _set(ctx, WIREC, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.curve_to(x0 + (x1 - x0) * 0.3, y0 + sag * 1.2 + (y1 - y0) * 0.3, x0 + (x1 - x0) * 0.7, y1 + sag * 1.2 - (y1 - y0) * 0.3, x1, y1)
    ctx.stroke()


def wire_y(x0, y0, x1, y1, sag, x):
    """wire() の線の上の高さ（とまる位置の計算用。ほぼ線形＋たるみ）"""
    u = (x - x0) / (x1 - x0)
    return y0 + (y1 - y0) * u + 4 * sag * 0.9 * u * (1 - u)


def pole(ctx, x, y0, y1=H, w=26):
    _set(ctx, "#6d5a49")
    ctx.rectangle(x - w / 2, y0, w, y1 - y0)
    ctx.fill()
    ctx.rectangle(x - 90, y0 + 40, 180, 14)
    ctx.fill()
    ctx.rectangle(x - 70, y0 + 120, 140, 12)
    ctx.fill()


# ---------------------------------------------------------------- 小さなアイコン
def draw_crow(ctx, x, y, s, a=1.0, facing=1):
    """カラス（小さなアイコン）。(x, y)=足もと・s=高さ"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s / 100.0 * facing, s / 100.0)
        _set(ctx, "#2b2d38")
        ell(ctx, -4, -42, 40, 24, -0.1)
        ctx.fill()
        ctx.move_to(-30, -48)
        ctx.line_to(-74, -34)
        ctx.line_to(-66, -24)
        ctx.line_to(-30, -32)
        ctx.close_path()
        ctx.fill()
        ctx.arc(30, -68, 20, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#4a4d5c")
        ctx.move_to(46, -76)
        ctx.line_to(76, -66)
        ctx.line_to(46, -58)
        ctx.close_path()
        ctx.fill()
        _set(ctx, "#ffffff")
        ctx.arc(35, -74, 4, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#1a1b22")
        ctx.arc(36, -74, 2, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#4a4d5c")
        ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for lx in (-6, 8):
            ctx.move_to(lx, -22)
            ctx.line_to(lx, 0)
            ctx.stroke()
        ctx.restore()
    _grp(ctx, a, body)


def draw_snake(ctx, x, y, s, a=1.0):
    """ヘビ（小さなアイコン）。(x, y)=下の真ん中・s=横幅"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        k = s / 200.0
        ctx.scale(k, k)
        _set(ctx, "#7fae6a")
        ctx.set_line_width(26)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-90, -14)
        ctx.curve_to(-60, -62, -30, 22, 0, -22)
        ctx.curve_to(30, -62, 60, 20, 78, -30)
        ctx.stroke()
        _set(ctx, "#6a9858")
        ctx.arc(88, -38, 17, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#ffffff")
        ctx.arc(93, -44, 4.5, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#1b2a1b")
        ctx.arc(94, -44, 2.2, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#d9573f")
        ctx.set_line_width(3.5)
        ctx.move_to(102, -36)
        ctx.line_to(116, -36)
        ctx.line_to(122, -41)
        ctx.move_to(116, -36)
        ctx.line_to(122, -31)
        ctx.stroke()
        ctx.restore()
    _grp(ctx, a, body)


def draw_tag(ctx, x, y, s, col="#ffffff"):
    """小さな発信機（点とアンテナ）。(x, y)=中心"""
    _set(ctx, "#e8505b")
    ctx.arc(x, y, s * 0.5, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, "#e8505b")
    ctx.set_line_width(max(2, s * 0.18))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y)
    ctx.line_to(x - s * 1.8, y - s * 1.6)
    ctx.stroke()


def draw_sparrow_icon(ctx, x, y, s, a=1.0):
    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s / 100.0, s / 100.0)
        _set(ctx, "#a9835e")
        ell(ctx, 0, -38, 36, 22, -0.15)
        ctx.fill()
        ctx.arc(30, -58, 17, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#f1e3c8")
        ell(ctx, 8, -26, 26, 10)
        ctx.fill()
        _set(ctx, "#6d4f36")
        ctx.move_to(-30, -42)
        ctx.line_to(-66, -30)
        ctx.line_to(-30, -30)
        ctx.close_path()
        ctx.fill()
        _set(ctx, "#2b2b36")
        ctx.move_to(44, -62)
        ctx.line_to(56, -58)
        ctx.line_to(44, -54)
        ctx.close_path()
        ctx.fill()
        ctx.arc(34, -63, 2.4, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#8a6a55")
        ctx.set_line_width(4)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for lx in (0, 12):
            ctx.move_to(lx, -22)
            ctx.line_to(lx, 0)
            ctx.stroke()
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 地図（Natural Earth の実データ）
SRC_WORLD = Path(__file__).resolve().parents[2] / "kaisetsu_movie" / "long" / "shuhasu" / "map" / "world.json"
MAP_BOX = (92.0, -12.0, 150.0, 47.0)      # 西, 南, 東, 北


def make_map():
    """sims/tsubame_map_data.py を作る。東アジア〜東南アジアの陸（ほかの国）と、塗る国の形を画面の座標でなく経緯度のまま持つ"""
    world = json.load(open(SRC_WORLD, encoding="utf-8"))
    box = MAP_BOX

    def polys(g):
        return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]

    def simp(pts, tol):
        if len(pts) < 4:
            return pts
        keep = [False] * len(pts)
        keep[0] = keep[-1] = True
        st = [(0, len(pts) - 1)]
        while st:
            a, b = st.pop()
            ax, ay = pts[a]
            bx, by = pts[b]
            dx, dy = bx - ax, by - ay
            n = math.hypot(dx, dy) or 1e-9
            best, bi = 0.0, -1
            for i in range(a + 1, b):
                d = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / n
                if d > best:
                    best, bi = d, i
            if best > tol and bi > 0:
                keep[bi] = True
                st += [(a, bi), (bi, b)]
        return [p for p, k in zip(pts, keep) if k]

    def ring(c):
        m = len(c) // 2
        p = simp(c[:m + 1], 0.02)[:-1] + simp(c[m:], 0.02)
        return [(round(x, 3), round(y, 3)) for x, y in p]

    def inside(c):
        lons = [p[0] for p in c]
        lats = [p[1] for p in c]
        return max(lons) > box[0] and min(lons) < box[2] and max(lats) > box[1] and min(lats) < box[3]

    land, picked = [], {}
    for code, g in world.items():
        if code == "ATA":
            continue
        for poly in polys(g):
            c = poly[0]
            if not inside(c):
                continue
            r = ring(c)
            if len(r) < 3:
                continue
            if code in ("PHL", "IDN", "MYS", "VNM", "JPN"):
                picked.setdefault(code, []).append(r)
            else:
                land.append(r)
    out = ['"""tsubame_art.py の make_map() が作った地図の形（Natural Earth・パブリックドメイン）。手で編集しない。経緯度のまま。"""',
           f"BOX = {box}", f"LAND = {land!r}", f"COUNTRY = {picked!r}"]
    p = Path(__file__).resolve().parent / "tsubame_map_data.py"
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("地図の形:", p, "ほかの陸", len(land), "塗る国", {k: len(v) for k, v in picked.items()})


class MapView:
    """地図を矩形 (x0, y0, x1, y1) に収める。経度の幅は中央緯度の cos を掛ける"""
    def __init__(self, x0, y0, x1, y1, box=None):
        from tsubame_map_data import BOX
        BOX = box or BOX
        self.box = BOX
        self.k = math.cos(math.radians((BOX[1] + BOX[3]) / 2))
        sw = (x1 - x0) / ((BOX[2] - BOX[0]) * self.k)
        sh = (y1 - y0) / (BOX[3] - BOX[1])
        self.s = min(sw, sh)
        self.ox = x0 + ((x1 - x0) - (BOX[2] - BOX[0]) * self.k * self.s) / 2
        self.oy = y0 + ((y1 - y0) - (BOX[3] - BOX[1]) * self.s) / 2
        self.rect = (x0, y0, x1, y1)

    def xy(self, lon, lat):
        return (self.ox + (lon - self.box[0]) * self.k * self.s, self.oy + (self.box[3] - lat) * self.s)

    def _path(self, ctx, r):
        ctx.move_to(*self.xy(*r[0]))
        for p in r[1:]:
            ctx.line_to(*self.xy(*p))
        ctx.close_path()

    def draw(self, ctx, sea="#a9d3e8", land="#ece3c8", paint=None, paint_alpha=None, vn_south=14.0):
        """paint = {国コード: 色}。ベトナムは vn_south より南だけ塗る"""
        from tsubame_map_data import COUNTRY, LAND
        x0, y0, x1, y1 = self.rect
        _set(ctx, sea)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
        ctx.fill()
        ctx.save()
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
        ctx.clip()
        for r in LAND:
            self._path(ctx, r)
        _set(ctx, land)
        ctx.fill()
        for code, rings in COUNTRY.items():
            col = (paint or {}).get(code)
            al = (paint_alpha or {}).get(code, 1.0)
            for r in rings:
                self._path(ctx, r)
                _set(ctx, land)
                ctx.fill()
                if not col:
                    continue
                ctx.save()
                if code == "VNM":
                    yy = self.xy(100, vn_south)[1]
                    ctx.rectangle(x0, yy, x1 - x0, y1 - yy)
                    ctx.clip()
                self._path(ctx, r)
                _set(ctx, col, al)
                ctx.fill()
                ctx.restore()
        ctx.restore()


if __name__ == "__main__":
    make_map()
