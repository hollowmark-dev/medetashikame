"""コウテイペンギンの一生ロングの絵の部品 — 2026-11-09 作成

tsubame_art.py と同じ考え方。
  - 平塗り・黒い輪郭線なし・陰はうすく1段だけ。丸み・やわらかい色
  - 大人は背が青黒・おなかが白・耳のあたりに黄〜橙の大きな斑・細長く下に曲がったくちばし
  - いなくなる場面は、うすくなって消えるだけ（襲われる・倒れる絵は描かない）
  - 一人称の背景はペンギン自身の体を描かない。見えている景色だけ

座標: (x, y) は基本「足もと／置いた面の中央下」。W=1920, H=1080 を想定。
確認用 PNG: python -X utf8 sims/penguin_art.py  → out/penguin-long/art_check/
"""
import math
import random
from pathlib import Path

import cairo

from danchi_people import mix
from tsubame_art import _set, _grp, ell, rrect, W, H, FONT  # noqa: F401
from danchi_people import _rgb

BACK = "#222944"        # 背・頭（黒に近い紺）
BACK_L = "#323b5f"      # 翼の明るい側
WHITE = "#f8f6ee"
WHITE_D = "#e7e2d4"     # おなかの陰
CREAM = "#f6ebc6"
PATCH_Y = "#f5b92e"
PATCH_O = "#f08f27"
BEAK = "#2d2a33"
BEAK_PINK = "#f2967a"
FOOT = "#15171f"
EGG = "#f8f3de"
CH_GREY = "#a4a6aa"
CH_GREY_L = "#c4c6c8"
CH_GREY_D = "#8a8c92"
CH_HEAD = "#1d1e25"
SNOW = "#f4f8fc"
ICE_L = "#eef5fa"
ICE_M = "#d6e6f1"
ICE_D = "#b8d0e2"
SEA_T = "#1e3a58"
SEA_B = "#0d2036"


def _lerp(a, b, t):
    return a + (b - a) * t


def _rgba(h, a=1.0):
    r, g, b = _rgb(h)
    return (r, g, b, a)


def _lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col, al in stops:
        g.add_color_stop_rgba(off, *_rgba(col, al))
    return g


def _soft(ctx, cx, cy, rx, ry, col, a):
    """ふちのぼやけたしみ（殻ごしの気配・光のにじみ用）"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(rx, ry)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, *_rgba(col, a))
    g.add_color_stop_rgba(0.55, *_rgba(col, a * 0.55))
    g.add_color_stop_rgba(1, *_rgba(col, 0))
    ctx.set_source(g)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- 大人
def _foot(ctx, x, y, w=22, lift=0.0):
    _set(ctx, FOOT)
    rrect(ctx, x, y - 5.5 - lift, w, 5.5, 2.7)
    ctx.fill()


def _patch(ctx, cx, cy, rx, ry, rot=0.0):
    """耳の斑: 上は黄〜橙、下へ向かってクリーム色に溶ける"""
    ctx.save()
    g = _lin(0, cy - ry, 0, cy + ry * 1.9,
             [(0, PATCH_O, 1.0), (0.28, PATCH_Y, 1.0), (0.62, CREAM, 0.85), (1.0, CREAM, 0.0)])
    ctx.set_source(g)
    ell(ctx, cx, cy, rx, ry * 1.0, rot)
    ctx.fill()
    # 胸の上部へ続くぼかし
    ell(ctx, cx + 1, cy + ry * 0.9, rx * 0.95, ry * 0.95, rot)
    ctx.fill()
    ctx.restore()


def _adult_body(ctx, fa=0.10, head_dy=0.0, head_rot=0.0):
    """横向き（右向き）の大人。足もと y=0・全高おおよそ100"""
    # 尾
    _set(ctx, BACK)
    ctx.move_to(-14, -14)
    ctx.line_to(-31, -3)
    ctx.line_to(-12, -6)
    ctx.close_path()
    ctx.fill()
    # 背・体
    ell(ctx, -1, -46, 23.5, 39, -0.05)
    ctx.fill()
    # 首〜頭の背側
    ell(ctx, 3, -74, 13.5, 21, -0.1)
    ctx.fill()
    # おなか（陰1段）
    _set(ctx, WHITE_D)
    ell(ctx, 6.5, -43, 17.5, 34.5, 0.02)
    ctx.fill()
    _set(ctx, WHITE)
    ell(ctx, 8, -45, 15.5, 33, 0.02)
    ctx.fill()
    _set(ctx, WHITE)
    ell(ctx, 9, -62, 13.5, 17, 0.0)
    ctx.fill()
    # 頭と、のどの黒
    ctx.save()
    if head_rot:
        ctx.translate(5, -74)
        ctx.rotate(head_rot)
        ctx.translate(-5, 74)
    _set(ctx, BACK)
    ctx.arc(9, -87 + head_dy, 12.6, 0, 2 * math.pi)
    ctx.fill()
    ell(ctx, 13.5, -78 + head_dy, 7.2, 11.5, 0.05)
    ctx.fill()
    # 耳の斑
    _patch(ctx, 4.8, -79 + head_dy, 9, 13, -0.08)
    # くちばし
    ctx.save()
    ctx.translate(0, head_dy)
    _set(ctx, BEAK)
    ctx.move_to(18.5, -90.8)
    ctx.curve_to(26.5, -91.6, 33.5, -87.5, 37.5, -79.5)
    ctx.line_to(35.4, -78.6)
    ctx.curve_to(31, -83.2, 25, -84.4, 18.5, -84.6)
    ctx.close_path()
    ctx.fill()
    _set(ctx, BEAK_PINK)
    ctx.set_line_width(2.1)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(20, -85.2)
    ctx.curve_to(26, -85.6, 31, -83.6, 35.2, -79.4)
    ctx.stroke()
    ctx.restore()
    # 目
    _set(ctx, "#080910")
    ctx.arc(14.2, -90 + head_dy, 1.9, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, "#ffffff", 0.8)
    ctx.arc(14.8, -90.7 + head_dy, 0.6, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()
    # 翼（フリッパー）
    ctx.save()
    ctx.translate(-2, -68)
    ctx.rotate(fa)
    _set(ctx, BACK_L)
    ell(ctx, 0, 20, 5.8, 23, 0.0)
    ctx.fill()
    ctx.restore()


def draw_emperor(ctx, x, y, h, facing=1, pose="stand", a=1.0):
    """大人のコウテイペンギン（横向き）。pose: stand / walk / bow / swim
    swim は水中で横に伸びた姿で、h は頭から足先までの長さ。(x, y)=体の下の面"""
    s = h / 100.0

    def body():
        ctx.save()
        if pose == "swim":
            ctx.translate(x, y - 0.24 * h)
            ctx.scale(facing * s, s)
            ctx.rotate(math.pi / 2 + 0.1)
            ctx.translate(0, 50)
            _adult_body(ctx, fa=0.55, head_rot=-1.40)
            _set(ctx, FOOT)
            for fx in (-5, 5):
                ctx.move_to(fx - 5, -1)
                ctx.line_to(fx + 5, -1)
                ctx.line_to(fx, 12)
                ctx.close_path()
                ctx.fill()
        else:
            ctx.translate(x, y)
            ctx.scale(facing * s, s)
            if pose == "walk":
                ctx.rotate(0.045)
                _foot(ctx, -13, 0, 22)
                _foot(ctx, 4, -2.5, 22)
                ctx.translate(0, -1.2)
                _adult_body(ctx, fa=0.42)
            elif pose == "bow":
                _foot(ctx, -9, 0, 22)
                _foot(ctx, 3, 0, 20)
                ctx.translate(2, -24)
                ctx.rotate(0.50)
                ctx.translate(-2, 24)
                _adult_body(ctx, fa=0.16, head_dy=2.0)
            else:
                _foot(ctx, -10, 0, 22)
                _foot(ctx, 2, 0, 22)
                _adult_body(ctx, fa=0.10)
        ctx.restore()
    _grp(ctx, a, body)


def draw_emperor_front(ctx, x, y, h, a=1.0):
    """正面向きの大人。おなかの白・左右の黄色い斑"""
    s = h / 100.0

    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s, s)
        _foot(ctx, -19, 0, 17)
        _foot(ctx, 2, 0, 17)
        # 翼（後ろ）
        _set(ctx, BACK)
        ell(ctx, 0, -46, 27, 39)
        ctx.fill()
        ctx.save()
        for sx in (-1, 1):
            ctx.save()
            ctx.translate(sx * 23, -66)
            ctx.rotate(-sx * 0.12)
            _set(ctx, BACK_L)
            ell(ctx, 0, 19, 5.6, 22)
            ctx.fill()
            ctx.restore()
        ctx.restore()
        _set(ctx, WHITE_D)
        ell(ctx, 0, -43, 19.5, 34.5)
        ctx.fill()
        _set(ctx, WHITE)
        ell(ctx, 0, -45, 17.5, 33)
        ctx.fill()
        # 頭
        _set(ctx, BACK)
        ctx.arc(0, -87, 12.8, 0, 2 * math.pi)
        ctx.fill()
        ell(ctx, 0, -77, 9.5, 10)
        ctx.fill()
        _patch(ctx, -10.5, -80, 5.4, 12, 0.08)
        _patch(ctx, 10.5, -80, 5.4, 12, -0.08)
        # くちばし（こちらを向く）
        _set(ctx, BEAK)
        ell(ctx, 0, -83, 3.0, 7.5)
        ctx.fill()
        _set(ctx, BEAK_PINK)
        ell(ctx, 0, -77.5, 1.4, 2.2)
        ctx.fill()
        _set(ctx, "#080910")
        for ex in (-5.6, 5.6):
            ctx.arc(ex, -90, 1.8, 0, 2 * math.pi)
            ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


def _adult_back(ctx):
    """後ろ向き（群れ用）。足もと y=0"""
    _foot(ctx, -13, 0, 12)
    _foot(ctx, 2, 0, 12)
    _set(ctx, BACK)
    ell(ctx, 0, -46, 25.5, 40)
    ctx.fill()
    _set(ctx, BACK_L)
    for sx in (-1, 1):
        ell(ctx, sx * 23, -48, 5.2, 22, -sx * 0.1)
        ctx.fill()
    _set(ctx, BACK)
    ctx.arc(0, -87, 12.4, 0, 2 * math.pi)
    ctx.fill()
    # 後ろからも斑のはしが少し見える
    _set(ctx, PATCH_Y, 0.9)
    for sx in (-1, 1):
        ell(ctx, sx * 10.2, -83, 2.6, 6.5, sx * 0.1)
        ctx.fill()
    # 吹雪をかぶった背
    _set(ctx, "#dfe8f2", 0.30)
    ell(ctx, 0, -66, 17, 12)
    ctx.fill()


def draw_emperor_back(ctx, x, y, h, a=1.0):
    s = h / 100.0

    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(s, s)
        _adult_back(ctx)
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 卵
def _egg_path(ctx, r, dx=0.0, dy=0.0, k=1.0):
    """洋なし形（上がややとがり、下がふっくら）。原点=卵の底"""
    ctx.new_sub_path()
    n = 48
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        ex = r * k * math.sin(t) * (1 - 0.20 * math.cos(t))
        ey = -r * 1.3 - r * k * 1.3 * math.cos(t)
        px, py = ex + dx, ey + dy
        if i == 0:
            ctx.move_to(px, py)
        else:
            ctx.line_to(px, py)
    ctx.close_path()


def draw_penguin_egg(ctx, x, y, r, a=1.0):
    """卵。(x, y)=卵の底・r=横の半径（縦は約2.6r）"""
    def body():
        ctx.save()
        ctx.translate(x, y)
        _set(ctx, mix(EGG, "#b9a67a", 0.30))
        _egg_path(ctx, r)
        ctx.fill()
        _set(ctx, EGG)
        _egg_path(ctx, r, -r * 0.10, -r * 0.14, 0.9)
        ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


def draw_father_with_egg(ctx, x, y, h, facing=1, a=1.0):
    """足の上に卵をのせ、おなかの羽毛の垂れ（抱卵のふくろ）を上からかぶせている父親（横向き）"""
    s = h / 100.0

    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(facing * s, s)
        ctx.rotate(-0.03)
        _foot(ctx, -9, 0, 30)
        _foot(ctx, 3, 0, 22)
        _adult_body(ctx, fa=0.06)
        # 足の上の卵（丸い輪郭の半分以上が見える）
        ctx.save()
        ctx.translate(11, -2)
        _set(ctx, mix(EGG, "#b9a67a", 0.30))
        _egg_path(ctx, 8.6)
        ctx.fill()
        _set(ctx, EGG)
        _egg_path(ctx, 8.6, -0.8, -1.1, 0.9)
        ctx.fill()
        ctx.restore()
        # 上から薄くかぶさる羽毛の垂れ（なめらかな縁・体の白とつなぐ）
        _set(ctx, WHITE_D)
        ctx.move_to(-2, -38)
        ctx.line_to(26, -38)
        ctx.line_to(25, -21)
        ctx.curve_to(20, -13.5, 6, -13.5, -2, -21)
        ctx.close_path()
        ctx.fill()
        _set(ctx, WHITE)
        ctx.move_to(-2, -38)
        ctx.line_to(25, -38)
        ctx.line_to(24, -23.5)
        ctx.curve_to(19, -17, 6, -17, -1, -23.5)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- ヒナ
def draw_emperor_chick(ctx, x, y, h, facing=1, age=0.0, a=1.0):
    """ヒナ。facing=1/-1 は横向き、0 は正面。age 0=ふ化したて 1=巣立ち前。h=全高"""
    age = max(0.0, min(1.0, age))
    bh = _lerp(26, 39, age)             # 体の縦半径
    br = _lerp(25, 24, age)             # 体の横半径
    hr = _lerp(18.5, 16.5, age)         # 頭の半径
    hcy = -(2 * bh - 6)                 # 頭の中心
    top = 2 * bh - 6 + hr
    s = h / top
    rnd = random.Random(11)

    def fluff(cx, cy, rx, ry, col, n=16, r=4.6):
        _set(ctx, col)
        for i in range(n):
            ang = 2 * math.pi * i / n + rnd.uniform(-0.1, 0.1)
            ctx.arc(cx + math.cos(ang) * rx * 0.94, cy + math.sin(ang) * ry * 0.94,
                    r * rnd.uniform(0.85, 1.15), 0, 2 * math.pi)
            ctx.fill()

    def body():
        ctx.save()
        ctx.translate(x, y)
        ctx.scale((facing if facing else 1) * s, s)
        front = facing == 0
        # 足
        _set(ctx, "#2a2c33")
        if front:
            rrect(ctx, -17, -5, 14, 5, 2.5); ctx.fill()
            rrect(ctx, 3, -5, 14, 5, 2.5); ctx.fill()
        else:
            rrect(ctx, -10, -5, 18, 5, 2.5); ctx.fill()
        # 体
        by = -bh - 2
        fluff(0, by, br, bh, CH_GREY)
        _set(ctx, CH_GREY)
        ell(ctx, 0, by, br, bh)
        ctx.fill()
        # 陰1段
        _set(ctx, CH_GREY_D, 0.55)
        ctx.save()
        ell(ctx, 0, by, br, bh)
        ctx.clip()
        ell(ctx, 3, by - 4, br * 1.02, bh * 1.0)
        ctx.rectangle(-60, -150, 120, 160)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.fill()
        ctx.restore()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        _set(ctx, CH_GREY_L)
        ell(ctx, 4 if not front else 0, by + 4, br * 0.62, bh * 0.66)
        ctx.fill()
        # 換羽: 背中と翼に、縁がギザギザの濃い面を1〜2か所だけ（新しい羽が出た所）
        if age > 9.0:  # 換羽・斑は描かない（泥はねに見えるため）
            k = (age - 0.7) / 0.3
            rj = random.Random(8)

            def jag(cx, cy, rx, ry, rot, n=11):
                pts = []
                for i in range(n * 2):
                    an = math.pi * i / n
                    rr = 1.0 if i % 2 == 0 else rj.uniform(0.62, 0.8)
                    pts.append((rx * rr * math.cos(an), ry * rr * math.sin(an)))
                ctx.save()
                ctx.translate(cx, cy)
                ctx.rotate(rot)
                ctx.move_to(*pts[0])
                for q in pts[1:]:
                    ctx.line_to(*q)
                ctx.close_path()
                ctx.restore()
                ctx.fill()
            _set(ctx, BACK, min(1.0, 0.4 + k))
            if front:
                for sx in (-1, 1):
                    jag(sx * br * 0.72, by - bh * 0.1, 6 + 4 * k, 14 + 9 * k, sx * 0.1)
            else:
                jag(-br * 0.5, by - bh * 0.28, 7 + 5 * k, 12 + 8 * k, 0.5)
                _set(ctx, "#2f375a", min(1.0, 0.4 + k))
                jag(-br * 0.15, by + bh * 0.12, 5 + 3 * k, 10 + 7 * k, 0.2)
            # 首もとの黄色が出はじめる
            _set(ctx, PATCH_Y, k * 0.8)
            if front:
                for sx in (-1, 1):
                    ell(ctx, sx * 9, hcy + hr * 0.95, 4.4, 5.0)
                    ctx.fill()
            else:
                ell(ctx, 3, hcy + hr * 0.95, 5.2, 5.6)
                ctx.fill()
        # 頭
        hx = 0 if front else 10
        _set(ctx, CH_HEAD)
        ctx.arc(hx, hcy, hr, 0, 2 * math.pi)
        ctx.fill()
        # 白い仮面（目のまわりから顔の前側）
        _set(ctx, "#f6f3ea")
        if front:
            ell(ctx, 0, hcy + 1.5, hr * 0.80, hr * 0.74)
            ctx.fill()
            _set(ctx, "#08090d")
            for ex in (-6.3, 6.3):
                ctx.arc(ex, hcy - 1.5, 2.5, 0, 2 * math.pi)
                ctx.fill()
            _set(ctx, "#2a2a30")
            ell(ctx, 0, hcy + 4.5, 2.7, 3.4)
            ctx.fill()
        else:
            ell(ctx, hx + hr * 0.30, hcy + 1.5, hr * 0.74, hr * 0.80, 0.1)
            ctx.fill()
            # 後頭部の黒がつながるよう、上のふちは黒を残す
            _set(ctx, "#08090d")
            ctx.arc(hx + hr * 0.42, hcy - 1.5, 2.7, 0, 2 * math.pi)
            ctx.fill()
            _set(ctx, "#ffffff", 0.85)
            ctx.arc(hx + hr * 0.42 + 0.9, hcy - 2.4, 0.8, 0, 2 * math.pi)
            ctx.fill()
            _set(ctx, "#2a2a30")
            ctx.move_to(hx + hr * 0.78, hcy + 0.2)
            ctx.curve_to(hx + hr * 1.18, hcy + 1.0, hx + hr * 1.32, hcy + 4.0, hx + hr * 1.26, hcy + 6.4)
            ctx.curve_to(hx + hr * 1.08, hcy + 6.8, hx + hr * 0.86, hcy + 5.4, hx + hr * 0.72, hcy + 4.6)
            ctx.close_path()
            ctx.fill()
        ctx.restore()
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 群れ
def _kinds(rnd, n):
    return [rnd.choices(["back", "side", "front"], [0.42, 0.40, 0.18])[0] for _ in range(n)]


def huddle(ctx, x, y, w, n, a=1.0, seed=0):
    """吹雪の中でかたまる大人の群れ。(x, y)=群れの手前中央の足もと・w=幅"""
    rnd = random.Random(seed)
    hb = max(70.0, min(280.0, w * 0.80 / math.sqrt(max(n, 1))))
    items = []
    for kind in _kinds(rnd, n):
        px = x + rnd.uniform(-w / 2, w / 2) * (1 - 0.18 * rnd.random())
        py = y - rnd.uniform(0, hb * 0.36)
        items.append((py, px, hb * rnd.uniform(0.9, 1.04) * (0.9 + 0.1 * (py - (y - hb * 0.36)) / (hb * 0.36 + 1e-6)),
                      kind, rnd.choice([-1, 1])))
    items.sort()

    def body():
        for py, px, hh, kind, fc in items:
            if kind == "back":
                draw_emperor_back(ctx, px, py, hh)
            elif kind == "front":
                draw_emperor_front(ctx, px, py, hh)
            else:
                draw_emperor(ctx, px, py, hh, facing=fc)
    _grp(ctx, a, body)


def creche(ctx, x, y, w, n, seed=0, a=1.0):
    """ヒナの群れ（保育園）"""
    rnd = random.Random(seed)
    hb = max(54.0, min(230.0, w * 0.62 / math.sqrt(max(n, 1))))
    items = []
    for _ in range(n):
        py = y - rnd.uniform(0, hb * 0.5)
        items.append((py, x + rnd.uniform(-w / 2, w / 2), hb * rnd.uniform(0.85, 1.08),
                      rnd.choice([1, -1, 1, -1, 0]), rnd.uniform(0.35, 0.55)))
    items.sort()

    def body():
        for py, px, hh, fc, ag in items:
            draw_emperor_chick(ctx, px, py, hh, facing=fc, age=ag)
    _grp(ctx, a, body)


# ---------------------------------------------------------------- 景色
def sky(ctx, y0=0, y1=620):
    """南極の夕方の低い空（うすいピンク〜青）"""
    ctx.set_source(_lin(0, y0, 0, y1, [(0, "#9fb7d9", 1), (0.55, "#d9c6dc", 1), (0.85, "#f3d4d4", 1),
                                        (1, "#f8e4d8", 1)]))
    ctx.rectangle(0, y0, W, y1 - y0)
    ctx.fill()
    _soft(ctx, W * 0.72, y1 - 10, 520, 120, "#fff0d8", 0.55)


def ice_shelf(ctx, y_top, y1=H, x0=0, x1=W, a=1.0):
    """白〜うす青の氷原"""
    def body():
        ctx.set_source(_lin(0, y_top, 0, y1, [(0, ICE_L, 1), (0.35, "#e3eef6", 1), (1, ICE_M, 1)]))
        ctx.rectangle(x0, y_top, x1 - x0, y1 - y_top)
        ctx.fill()
        # ゆるいうねり（うすい1段）
        _set(ctx, "#ffffff", 0.45)
        for i, k in enumerate((0.16, 0.36, 0.6)):
            yy = y_top + (y1 - y_top) * k
            ctx.move_to(x0, yy)
            ctx.curve_to(x0 + (x1 - x0) * 0.3, yy - 14 - 6 * i, x0 + (x1 - x0) * 0.6, yy + 12 + 5 * i, x1, yy - 6)
            ctx.line_to(x1, yy + 18 + 6 * i)
            ctx.curve_to(x0 + (x1 - x0) * 0.6, yy + 28, x0 + (x1 - x0) * 0.3, yy + 6, x0, yy + 20)
            ctx.close_path()
            ctx.fill()
    _grp(ctx, a, body)


def sea(ctx, y_top, y1=H, x0=0, x1=W, t=0.0):
    """黒っぽい青の海"""
    ctx.set_source(_lin(0, y_top, 0, y1, [(0, SEA_T, 1), (1, SEA_B, 1)]))
    ctx.rectangle(x0, y_top, x1 - x0, y1 - y_top)
    ctx.fill()
    _set(ctx, "#4a7396", 0.30)
    ctx.set_line_width(3)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    rnd = random.Random(5)
    for _ in range(26):
        yy = rnd.uniform(y_top + 8, y1 - 10)
        xx = rnd.uniform(x0, x1) + 14 * math.sin(t * 0.8 + yy)
        ln = rnd.uniform(40, 130) * (0.5 + (yy - y_top) / max(1, y1 - y_top))
        ctx.move_to(xx, yy)
        ctx.curve_to(xx + ln * 0.3, yy - 3, xx + ln * 0.7, yy + 3, xx + ln, yy)
        ctx.stroke()


def ice_edge(ctx, y_top, x0, x1, depth=60, a=1.0):
    """氷の縁（氷原の手前に切り立つ面）。y_top=氷原の上面のふち"""
    def body():
        ctx.set_source(_lin(0, y_top, 0, y_top + depth, [(0, ICE_D, 1), (1, "#8fb4cf", 1)]))
        rrect(ctx, x0, y_top, x1 - x0, depth, 12)
        ctx.fill()
        _set(ctx, "#ffffff", 0.35)
        ctx.set_line_width(3)
        ctx.move_to(x0 + 14, y_top + 8)
        ctx.line_to(x1 - 14, y_top + 8)
        ctx.stroke()
    _grp(ctx, a, body)


def blizzard(ctx, t, a=0.8, n=240, seed=3, speed=1.0, size=1.0, veil=0.18):
    """斜めに流れる白い粒。t(秒) で動く。veil=全体の白いもや"""
    if a <= 0.003:
        return
    rnd = random.Random(seed)
    dx, dy = -0.93, 0.37
    ctx.save()
    if veil > 0:
        _set(ctx, "#ffffff", veil * a)
        ctx.rectangle(0, 0, W, H)
        ctx.fill()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        x0, y0 = rnd.uniform(0, W + 300), rnd.uniform(-100, H + 100)
        sp = rnd.uniform(520, 1250) * speed
        ln = rnd.uniform(16, 52) * size
        wd = rnd.uniform(2.0, 5.5) * size
        al = rnd.uniform(0.35, 0.95) * a
        px = (x0 + dx * sp * t) % (W + 300) - 100
        py = (y0 + dy * sp * t) % (H + 200) - 100
        _set(ctx, "#ffffff" if i % 3 else "#9fb2c9", al)
        ctx.set_line_width(wd)
        ctx.move_to(px, py)
        ctx.line_to(px + dx * ln, py + dy * ln)
        ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------- 一人称の背景
def _ice_scene(ctx, t, horizon=560, bliz=0.85):
    sky(ctx, 0, horizon + 40)
    ice_shelf(ctx, horizon, H)
    # 遠くの氷のうねり
    _set(ctx, "#cfdfec", 0.8)
    ctx.move_to(0, horizon + 6)
    ctx.curve_to(400, horizon - 14, 900, horizon + 8, 1400, horizon - 10)
    ctx.curve_to(1700, horizon - 18, 1800, horizon, W, horizon - 6)
    ctx.line_to(W, horizon + 30)
    ctx.line_to(0, horizon + 30)
    ctx.close_path()
    ctx.fill()
    blizzard(ctx, t, bliz, n=300, seed=4, size=1.0, veil=0.22)


def _feather_frame(ctx, cx, cy, rx, ry, base, tones, seed, n=44, blob=(150, 90), rings=2):
    """楕円のあなのまわりを、羽毛のふくらみで取りかこむ"""
    rnd = random.Random(seed)
    # 外側のかたまり
    ctx.save()
    _set(ctx, base)
    ctx.rectangle(0, 0, W, H)
    ell(ctx, cx, cy, rx, ry)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.fill()
    ctx.restore()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for ring in reversed(range(rings)):
        k = 1.0 - 0.30 * ring
        for i in range(n):
            ang = 2 * math.pi * (i + 0.5 * ring) / n + rnd.uniform(-0.05, 0.05)
            ex, ey = math.cos(ang) * rx, math.sin(ang) * ry
            nx, ny = math.cos(ang), math.sin(ang)
            push = blob[1] * 0.42 + ring * 55
            px, py = cx + ex + nx * push, cy + ey + ny * push
            _set(ctx, rnd.choice(tones))
            tang = ang + math.pi / 2
            rr = blob[1] * k * rnd.uniform(0.85, 1.15)
            ell(ctx, px, py, rr * 1.15, rr, 0.0)
            ctx.fill()
    # あなのふちの影（うすく1段）
    for wdt, al in ((30, 0.07), (14, 0.09)):
        _set(ctx, "#1d1612", al)
        ctx.set_line_width(wdt)
        ell(ctx, cx, cy, rx + 6, ry + 6)
        ctx.stroke()


def _feather_slit(ctx, cx, w_mid, base, tones, seed, r=64, lean=0.0, y0=-120, y1=H + 120):
    """羽毛のひだが左右からあわさって、縦にすき間をつくる。すき間は中ほどでいちばん広い"""
    rnd = random.Random(seed)

    def half_w(y):
        u = (y - y0) / (y1 - y0)
        return 0.5 * w_mid * max(0.08, math.sin(math.pi * u)) ** 0.8

    def mid(y):
        return cx + lean * (y - H / 2)
    for side in (-1, 1):
        # かたまり
        _set(ctx, base)
        ctx.move_to(W * (0.5 + side * 0.7), y0)
        for yy in range(int(y0), int(y1) + 1, 20):
            ctx.line_to(mid(yy) + side * half_w(yy), yy)
        ctx.line_to(W * (0.5 + side * 0.7), y1)
        ctx.close_path()
        ctx.fill()
        # ふくらみ（外側→ふち の順にかさねる）
        for row in (2, 1, 0):
            yy = y0 + (rnd.uniform(0, r * 0.8))
            while yy < y1:
                px = mid(yy) + side * (half_w(yy) + r * (0.15 + 0.7 * row))
                _set(ctx, rnd.choice(tones))
                rr = r * rnd.uniform(0.85, 1.2) * (1.0 + 0.12 * row)
                ell(ctx, px, yy, rr, rr * 1.15, side * rnd.uniform(-0.2, 0.2))
                ctx.fill()
                yy += r * rnd.uniform(0.8, 1.15)
    # すき間のふちの影（うすく1段）
    for wdt, al in ((36, 0.08), (16, 0.10)):
        _set(ctx, "#1d1612", al)
        ctx.set_line_width(wdt)
        for side in (-1, 1):
            ctx.move_to(mid(y0) + side * half_w(y0), y0)
            for yy in range(int(y0), int(y1) + 1, 20):
                ctx.line_to(mid(yy) + side * half_w(yy), yy)
            ctx.stroke()


def _foot3(ctx, cx, cy, sx, sc=1.0):
    """父親の足（横から見た平たい黒い足。前＝すき間のほうへ短い指3本、指先に小さな黒い爪）"""
    cy = cy - 40 * sc
    _set(ctx, "#12141b")
    ctx.rectangle(cx - sx * 130 * sc - 90 * sc, cy, 180 * sc, H)
    ctx.fill()
    ell(ctx, cx - sx * 50 * sc, cy, 230 * sc, 78 * sc)
    ctx.fill()
    for dy, ln in ((-32, 0), (4, 22), (40, 0)):
        tx = cx + sx * (190 + ln) * sc
        ty = cy + dy * sc
        _set(ctx, "#1d212d")
        ell(ctx, tx, ty, 100 * sc, 33 * sc)
        ctx.fill()
        ex = tx + sx * 96 * sc
        _set(ctx, "#05060a")
        ctx.move_to(ex - sx * 14 * sc, ty - 10 * sc)
        ctx.curve_to(ex + sx * 12 * sc, ty - 10 * sc, ex + sx * 26 * sc, ty + 2 * sc, ex + sx * 28 * sc, ty + 16 * sc)
        ctx.curve_to(ex + sx * 14 * sc, ty + 8 * sc, ex, ty + 10 * sc, ex - sx * 14 * sc, ty + 10 * sc)
        ctx.close_path()
        ctx.fill()


def _belly_gap(ctx, t, top=380, bot=720, shell=False, dark=("#1b2238", "#39435f"), seed=5,
               horizon=560, foot_sc=1.0, foot_y=980):
    """おなかの下から足の間を通して外を見る。上は羽毛のカーテン、下は黒い足、間に横長のすき間"""
    _ice_scene(ctx, t, horizon=horizon, bliz=1.0)

    def top_y(x):
        return top + 80 * (abs(x - W / 2) / (W / 2)) ** 1.6

    def bot_y(x):
        return bot - 70 * (abs(x - W / 2) / (W / 2)) ** 1.6
    # すき間の外は暗がり
    ctx.rectangle(0, 0, W, H)
    ctx.move_to(0, top_y(0))
    for x in range(0, W + 1, 20):
        ctx.line_to(x, top_y(x))
    for x in range(W, -1, -20):
        ctx.line_to(x, bot_y(x))
    ctx.close_path()
    ctx.set_source(_lin(0, 0, 0, H, [(0, dark[0], 1), (1, dark[1], 1)]))
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    # 羽毛のカーテン: 先の丸い幅広の房（しずく形）を白〜クリームの半透明で重ねる
    rnd = random.Random(seed)
    layers = (("#cfc9bb", 0.9, 170, 110), ("#e2ddd0", 0.7, 150, 90), ("#efeadf", 0.6, 130, 70),   # 2026-11-10 Fable: 青灰だと雲に見える→白〜クリームへ
              ("#f6f1e2", 0.5, 115, 52), ("#ffffff", 0.5, 100, 38), ("#fbf4e0", 0.45, 90, 24))
    for col, al, wd, extra in layers:
        x = -80
        while x < W + 80:
            w = wd * rnd.uniform(0.7, 1.3)
            r = w / 2
            tip = top_y(x) + extra * rnd.uniform(-0.1, 1.0)
            cxx = x + rnd.uniform(-20, 20)
            _set(ctx, col, al)
            ctx.move_to(x - r, -50)
            ctx.line_to(cxx - r, tip - r)
            ctx.arc_negative(cxx, tip - r, r, math.pi, 0)
            ctx.line_to(x + r, -50)
            ctx.close_path()
            ctx.fill()
            x += w * rnd.uniform(0.3, 0.55)
    # 黒い足（左右に大きく）
    _foot3(ctx, 420, foot_y, 1, foot_sc)
    _foot3(ctx, W - 420, foot_y, -1, foot_sc)
    if shell:
        # 手前に、弧を描く殻の縁（厚みあり・色は fp_egg_shell と同じ）
        for dy, rx, ry, col in ((0, 800, 650, "#b9a574"), (-16, 790, 640, "#f6edcc"), (-34, 770, 622, "#d6c293")):
            ell(ctx, W / 2, H + 520 + dy, rx, ry)
            _set(ctx, col)
            ctx.fill()
        rs = random.Random(3)
        _set(ctx, "#9c8456", 0.18)
        for _ in range(30):
            ell(ctx, rs.uniform(600, 1320), rs.uniform(1010, 1075), rs.uniform(4, 10), rs.uniform(3, 7))
            ctx.fill()
    g = cairo.RadialGradient(W / 2, H * 0.5, 450, W / 2, H * 0.5, 1250)
    g.add_color_stop_rgba(0, *_rgba("#0a1020", 0.0))
    g.add_color_stop_rgba(1, *_rgba("#0a1020", 0.45))
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()


def fp_in_egg_under_father(ctx, t, view="shell", crack=0.0):
    """view='shell': 卵の殻の内側から（crack 0〜1 でひびが伸びて光が差す）。
    'gap': 殻の外の、父親のおなかの羽毛のカーテンと黒い足のすき間（手前に割れた殻のふち）"""
    if view == "gap":
        _belly_gap(ctx, t, top=270, bot=760, shell=True, seed=5)
        return
    ctx.set_source(_lin(0, 0, 0, H, [(0, "#eadcb2", 1), (1, "#d6c293", 1)]))
    ctx.rectangle(0, 0, W, H)
    ctx.fill()
    _soft(ctx, W * 0.30, H * 0.26, 420, 260, "#fff6dc", 0.25)
    # 殻のうすい点々（斑）
    rs = random.Random(17)
    for _ in range(90):
        _set(ctx, "#a88f5c", rs.uniform(0.08, 0.2))
        ell(ctx, rs.uniform(0, W), rs.uniform(0, H), rs.uniform(3, 10), rs.uniform(3, 8), rs.uniform(0, 3))
        ctx.fill()
    # 卵形（縦長）に暗く落とす
    ctx.save()
    ctx.translate(W / 2, H * 0.5)
    ctx.scale(0.72, 1.5)
    g = cairo.RadialGradient(0, 0, 250, 0, 0, 760)
    g.add_color_stop_rgba(0, *_rgba("#3b2d20", 0.0))
    g.add_color_stop_rgba(0.5, *_rgba("#3b2d20", 0.35))
    g.add_color_stop_rgba(1, *_rgba("#150f09", 0.96))
    ctx.set_source(g)
    ctx.rectangle(-W, -H * 1.5, 2 * W, 3 * H)
    ctx.fill()
    ctx.restore()
    # 外にいる親の体の大きな丸い影（ぼんやり動く）
    _soft(ctx, W * 0.56 + 80 * math.sin(t * 0.35), H * 0.58 + 40 * math.cos(t * 0.3), 620, 560, "#241a12", 0.45)
    # ひび: 縁から入る細い枝分かれ線。光るのは割れ目の奥だけ
    if crack > 0:
        main = [(1500, -10), (1445, 120), (1475, 230), (1395, 340), (1425, 440)]
        branches = [(1, [(1445, 120), (1350, 170), (1300, 240)]), (3, [(1395, 340), (1500, 385), (1545, 460)])]

        def part(poly, f):
            f = max(0.0, min(1.0, f))
            if f <= 0:
                return []
            n = len(poly) - 1
            u = f * n
            out = [poly[0]]
            for i in range(n):
                if u >= i + 1:
                    out.append(poly[i + 1])
                elif u > i:
                    q = u - i
                    out.append((poly[i][0] + (poly[i + 1][0] - poly[i][0]) * q, poly[i][1] + (poly[i + 1][1] - poly[i][1]) * q))
                    break
            return out
        lines = [part(main, crack)]
        for idx, poly in branches:
            lines.append(part(poly, crack * 4 - idx))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        for wdt, col, al in ((9, "#fff4d0", 0.22), (4.5, "#4a3826", 0.9), (1.8, "#fffbea", 0.95)):
            _set(ctx, col, al)
            ctx.set_line_width(wdt)
            for ln in lines:
                if len(ln) >= 2:
                    ctx.move_to(*ln[0])
                    for q in ln[1:]:
                        ctx.line_to(*q)
                    ctx.stroke()


def fp_from_pouch(ctx, t):
    """親のおなかの袋の中から、羽毛のカーテンと黒い足のすき間ごしに、外の白い氷原と吹雪をのぞく"""
    _belly_gap(ctx, t, top=250, bot=800, shell=False, dark=("#141a2e", "#2c3552"), seed=9,
               foot_sc=0.85, foot_y=1010)
    # 袋の中の暗さ（上から）
    ctx.set_source(_lin(0, 0, 0, H * 0.6, [(0, "#0e1426", 0.35), (1, "#0e1426", 0.0)]))
    ctx.rectangle(0, 0, W, H)
    ctx.fill()


def fp_in_creche(ctx, t):
    """ヒナの群れの中。ヒナの目の高さ。まわりに灰色のヒナの背中や顔"""
    hor = 470
    sky(ctx, 0, hor + 30)
    ice_shelf(ctx, hor, H)
    rnd = random.Random(21)
    rows = [  # (足もとy, 高さ, 数, 横の範囲)
        (hor + 24, 96, 14, (0, W)),
        (hor + 80, 150, 9, (0, W)),
        (hor + 190, 270, 6, (0, W)),
    ]
    for ri, (fy, hh, cnt, (xa, xb)) in enumerate(rows):
        items = []
        for i in range(cnt):
            px = xa + (xb - xa) * (i + 0.5) / cnt + rnd.uniform(-0.3, 0.3) * (xb - xa) / cnt
            items.append((px, hh * rnd.uniform(0.9, 1.08), rnd.choice([1, -1, 0, 0]), rnd.uniform(0.35, 0.55)))
        for px, h2, fc, ag in sorted(items):
            draw_emperor_chick(ctx, px, fy + rnd.uniform(-8, 8), h2, facing=fc, age=ag)
    # 手前の子（顔が重ならないよう位置を決める）
    for px, fy, h2, fc, ag in ((430, hor + 400, 470, 1, 0.5), (1500, hor + 420, 470, -1, 0.45),
                               (130, H + 200, 640, 0, 0.5), (1800, H + 240, 680, -1, 0.55)):
        draw_emperor_chick(ctx, px, fy, h2, facing=fc, age=ag)
    blizzard(ctx, t, 0.45, n=170, seed=6, size=0.9, veil=0.10)


def fp_ice_edge(ctx, t):
    """氷の縁に立ち、足もとの先に黒い海（下を見下ろす）"""
    hor = 250
    sky(ctx, 0, hor + 30)
    sea(ctx, hor, H, t=t)
    # 遠くの氷山（うすく1段）
    _set(ctx, "#8fb0cb", 0.85)
    for bx, bw, bh in ((300, 260, 46), (980, 330, 58), (1560, 220, 40)):
        ctx.move_to(bx - bw / 2, hor + 3)
        ctx.line_to(bx - bw * 0.25, hor - bh)
        ctx.line_to(bx + bw * 0.15, hor - bh * 0.7)
        ctx.line_to(bx + bw / 2, hor + 3)
        ctx.close_path()
        ctx.fill()
    # 海に浮かぶ氷のかけら（不規則な多角形）
    rnd = random.Random(31)
    for _ in range(7):
        fx, fy = rnd.uniform(200, 1700), rnd.uniform(430, 740)
        sc = 0.6 + (fy - 430) / 300
        nv = rnd.randint(6, 8)
        ang0 = rnd.uniform(0, 1)
        vs = []
        for i in range(nv):
            an = 2 * math.pi * (i + rnd.uniform(-0.3, 0.3)) / nv + ang0
            rr = rnd.uniform(0.55, 1.2)
            vs.append((fx + math.cos(an) * 80 * sc * rr, fy + math.sin(an) * 15 * sc * rr))
        _set(ctx, "#b7d2e4", 0.9)
        ctx.move_to(*vs[0])
        for q in vs[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.fill()
        _set(ctx, "#ffffff", 0.7)
        ctx.move_to(vs[0][0], vs[0][1] - 3 * sc)
        for q in vs[1:]:
            ctx.line_to(q[0] * 0.97 + fx * 0.03, q[1] - 3 * sc)
        ctx.close_path()
        ctx.fill()
    # 足もとの氷（手前）。縁は不規則なカーブ
    ey = 790
    ctx.move_to(-10, H + 10)
    ctx.line_to(-10, ey + 10)
    ctx.curve_to(260, ey - 40, 520, ey + 30, 820, ey + 5)
    ctx.curve_to(1120, ey - 25, 1400, ey + 40, 1700, ey - 5)
    ctx.curve_to(1800, ey - 20, 1880, ey, W + 10, ey - 8)
    ctx.line_to(W + 10, H + 10)
    ctx.close_path()
    ctx.set_source(_lin(0, ey - 40, 0, H, [(0, ICE_L, 1), (1, "#dce9f3", 1)]))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    # 縁のすぐ下に青い氷の肌（厚み）
    _set(ctx, ICE_D, 0.9)
    ctx.set_line_width(46)
    ctx.move_to(-10, ey + 38)
    ctx.curve_to(260, ey - 2, 520, ey + 68, 820, ey + 43)
    ctx.curve_to(1120, ey + 13, 1400, ey + 78, 1700, ey + 33)
    ctx.curve_to(1800, ey + 18, 1880, ey + 38, W + 10, ey + 30)
    ctx.stroke()
    ctx.restore()
    ctx.new_path()
    # 縁のもう1段（段差の影）
    _set(ctx, "#a9c3d8", 0.45)
    ctx.set_line_width(9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-10, ey + 92)
    ctx.curve_to(260, ey + 52, 520, ey + 122, 820, ey + 97)
    ctx.curve_to(1120, ey + 67, 1400, ey + 132, 1700, ey + 87)
    ctx.curve_to(1800, ey + 72, 1880, ey + 92, W + 10, ey + 84)
    ctx.stroke()
    blizzard(ctx, t, 0.35, n=110, seed=7, size=0.8, veil=0.06)


def fp_underwater(ctx, t):
    """水の中から見上げる氷（上に白い氷の板、光が差す、下は暗い青）"""
    ctx.set_source(_lin(0, 0, 0, H, [(0, "#74bddf", 1), (0.35, "#2f78a6", 1), (1, "#06192e", 1)]))
    ctx.rectangle(0, 0, W, H)
    ctx.fill()
    _soft(ctx, 1500, 30, 700, 300, "#e9f9ff", 0.8)
    rnd = random.Random(14)
    for i in range(5):
        sx = 1180 + i * 130 + 24 * math.sin(t * 0.6 + i)
        ctx.move_to(sx, 0)
        ctx.line_to(sx + 38, 0)
        ctx.line_to(sx - 280 + i * 30, H * 0.9)
        ctx.line_to(sx - 330 + i * 30, H * 0.9)
        ctx.close_path()
        ctx.set_source(_lin(0, 0, 0, H * 0.9, [(0, "#e4f7ff", 0.20), (0.7, "#e4f7ff", 0.05), (1, "#e4f7ff", 0.0)]))
        ctx.fill()
    # 氷の板: 底面は不ぞろいで丸みのある凸凹・白〜淡い水色
    def depth(x):
        d = 200 + 42 * math.sin(x * 0.007) + 30 * math.sin(x * 0.021 + 1.0) + 16 * math.sin(x * 0.053 + 2.0)
        if x > 1000:
            d *= max(0.0, 1 - (x - 1000) / 380)
        return d
    ctx.move_to(-40, -10)
    for x in range(-40, 1420, 10):
        ctx.line_to(x, depth(x))
    ctx.line_to(1420, -10)
    ctx.close_path()
    ctx.set_source(_lin(0, 0, 0, 280, [(0, "#ffffff", 1), (1, "#dff1fa", 1)]))
    ctx.fill()
    # 底面の淡い影（うすく1段）
    _set(ctx, "#bfe3f3", 0.5)
    ctx.move_to(-40, 120)
    for x in range(-40, 1420, 10):
        ctx.line_to(x, depth(x) - 38)
    ctx.line_to(1420, 120)
    ctx.close_path()
    ctx.fill()
    ctx.set_source(_lin(0, 0, 0, 280, [(0, "#ffffff", 1), (1, "#e6f5fb", 1)]))
    ctx.move_to(-40, -10)
    for x in range(-40, 1420, 10):
        ctx.line_to(x, depth(x) - 44)
    ctx.line_to(1420, -10)
    ctx.close_path()
    ctx.fill()
    for _ in range(40):
        bx = rnd.uniform(0, W)
        by = (rnd.uniform(0, H) - t * rnd.uniform(25, 60)) % (H + 40)
        _set(ctx, "#e3f6ff", rnd.uniform(0.15, 0.4))
        ctx.arc(bx + 8 * math.sin(t + bx), by, rnd.uniform(3, 11), 0, 2 * math.pi)
        ctx.fill()


# ---------------------------------------------------------------- アイコン
def draw_penguin_icon(ctx, x, y, s, kind="adult", a=1.0):
    """小さく並べて数を見せる用。(x, y)=足もと・s=高さ"""
    if kind == "egg":
        draw_penguin_egg(ctx, x, y, s * 0.2, a)
    elif kind == "chick":
        draw_emperor_chick(ctx, x, y, s, facing=0, age=0.55, a=a)
    else:
        draw_emperor(ctx, x, y, s, facing=1, a=a)


# ---------------------------------------------------------------- 確認用
OUT = Path(__file__).resolve().parents[1] / "out" / "penguin-long" / "art_check"


def _surf():
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)


def _label(ctx, x, y, text):
    _set(ctx, "#333344", 0.85)
    ctx.select_font_face(FONT)
    ctx.set_font_size(22)
    ctx.move_to(x, y)
    ctx.show_text(text)


def render_parts(path):
    sf = _surf()
    ctx = cairo.Context(sf)
    sky(ctx, 0, 330)
    ice_shelf(ctx, 330, 700)
    # 左下に海
    sea(ctx, 700, H, 0, 760)
    ice_shelf(ctx, 700, H, 760, W)
    ice_edge(ctx, 690, 0, 760, 12)
    gy = 520
    draw_emperor(ctx, 120, gy, 230)
    _label(ctx, 60, gy + 34, "stand")
    draw_emperor(ctx, 330, gy, 230, pose="walk")
    _label(ctx, 280, gy + 34, "walk")
    draw_emperor(ctx, 540, gy, 230, pose="bow", facing=-1)
    _label(ctx, 490, gy + 34, "bow")
    draw_emperor_front(ctx, 740, gy, 230)
    _label(ctx, 690, gy + 34, "front")
    draw_father_with_egg(ctx, 960, gy, 230)
    _label(ctx, 890, gy + 34, "father+egg")
    for i, ag in enumerate((0.0, 0.5, 1.0)):
        draw_emperor_chick(ctx, 1130 + i * 150, gy, 120 + 40 * ag, age=ag, facing=1)
        _label(ctx, 1100 + i * 150, gy + 34, "age %.1f" % ag)
    draw_emperor_chick(ctx, 1600, gy, 150, age=0.5, facing=0)
    _label(ctx, 1570, gy + 34, "chick front")
    draw_penguin_egg(ctx, 1730, gy, 26)
    _label(ctx, 1700, gy + 34, "egg")
    for i, k in enumerate(("adult", "chick", "egg")):
        draw_penguin_icon(ctx, 1810 + i * 0, gy - 330 + i * 90, 70, kind=k)
    # 下段
    draw_emperor(ctx, 380, 880, 330, pose="swim")
    _label(ctx, 60, 1050, "swim（海の上に重ねて表示）")
    huddle(ctx, 1130, 870, 560, 16, seed=1)
    _label(ctx, 860, 1050, "huddle")
    creche(ctx, 1640, 860, 380, 9, seed=2)
    _label(ctx, 1460, 1050, "creche")
    # 吹雪の見本
    ctx.save()
    ctx.rectangle(780, 700, 560, 380)
    ctx.clip()
    blizzard(ctx, 0.7, 0.6, n=120)
    ctx.restore()
    sf.write_to_png(str(path))


def _shrink(sources, path, cols=2):
    tw = 480
    th = 270
    rows = (len(sources) + cols - 1) // cols
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, tw * cols + 8 * (cols + 1), th * rows + 8 * (rows + 1))
    ctx = cairo.Context(sf)
    _set(ctx, "#222222")
    ctx.paint()
    for i, p in enumerate(sources):
        im = cairo.ImageSurface.create_from_png(str(p))
        ctx.save()
        ctx.translate(8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 8))
        ctx.scale(tw / im.get_width(), th / im.get_height())
        ctx.set_source_surface(im, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_BEST)
        ctx.paint()
        ctx.restore()
    sf.write_to_png(str(path))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    p = OUT / "parts.png"
    render_parts(p)
    made.append(p)
    fps = [
        ("fp_egg_shell", lambda c: fp_in_egg_under_father(c, 1.0, "shell", crack=0.6)),
        ("fp_egg_gap", lambda c: fp_in_egg_under_father(c, 1.0, "gap")),
        ("fp_pouch", lambda c: fp_from_pouch(c, 1.0)),
        ("fp_creche", lambda c: fp_in_creche(c, 1.0)),
        ("fp_ice_edge", lambda c: fp_ice_edge(c, 1.0)),
        ("fp_underwater", lambda c: fp_underwater(c, 1.0)),
    ]
    for name, fn in fps:
        sf = _surf()
        fn(cairo.Context(sf))
        q = OUT / (name + ".png")
        sf.write_to_png(str(q))
        made.append(q)
    _shrink(made, OUT / "sheet_480.png", cols=2)
    print("ok", len(made))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- 大人（B案の画像・2026-11-10）
# ユーザー「大人の絵が似てなさすぎる」→ Gemini の下絵を engine/ai_cutout で切り抜いた画像（sims/penguin_sprites/*.png）に置きかえ。
# 下の4つの関数は上の同名の関数を上書きする（名前と引数は同じ。huddle などは呼んだときにこちらを使う）。
# 作り直し: python -X utf8 sims/penguin_sprites/make_sprites.py
_SPRITE_DIR = Path(__file__).resolve().parent / "penguin_sprites"
_SPRITES = {}
_H_RATIO = 0.97          # 旧部品の h に対する、頭のてっぺんから足もとまでの高さ


def _sprite(name):
    if name not in _SPRITES:
        _SPRITES[name] = cairo.ImageSurface.create_from_png(str(_SPRITE_DIR / f"{name}.png"))
    return _SPRITES[name]


def _paint_sprite(ctx, name, x, y, height=None, width=None, facing=1, a=1.0, rot=0.0, ax=0.5):
    """画像の下の端（足もと）を (x, y) に、横は ax（0=左・0.5=中央）の位置にそろえて描く"""
    if a <= 0.003:
        return
    sf = _sprite(name)
    w, h = sf.get_width(), sf.get_height()
    k = (height / h) if height is not None else (width / w)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot * facing)
    ctx.scale(facing * k, k)
    ctx.set_source_surface(sf, -w * ax, -h)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_emperor(ctx, x, y, h, facing=1, pose="stand", a=1.0):
    """大人のコウテイペンギン（横向き・画像）。pose: stand / walk / bow / swim"""
    if pose == "swim":
        _paint_sprite(ctx, "adult_swim", x, y, width=h, facing=facing, a=a)
    elif pose == "walk":
        _paint_sprite(ctx, "adult_side", x, y, height=h * _H_RATIO, facing=facing, a=a, rot=0.045)
    elif pose == "bow":
        _paint_sprite(ctx, "adult_side", x, y, height=h * _H_RATIO, facing=facing, a=a, rot=0.35)
    else:
        _paint_sprite(ctx, "adult_side", x, y, height=h * _H_RATIO, facing=facing, a=a)


def draw_emperor_front(ctx, x, y, h, a=1.0):
    _paint_sprite(ctx, "adult_front", x, y, height=h * _H_RATIO, a=a)


def draw_emperor_back(ctx, x, y, h, a=1.0):
    _paint_sprite(ctx, "adult_back", x, y, height=h * _H_RATIO, a=a)


def draw_father_with_egg(ctx, x, y, h, facing=1, a=1.0):
    _paint_sprite(ctx, "adult_egg", x, y, height=h * _H_RATIO, facing=facing, a=a)


# ---------------------------------------------------------------- ヒナ（B案の画像・2026-11-11）
# ユーザー「ヒナが変わっていない」→ ヒナもコード描きをやめ、年齢3段の画像に（ふ化したて／綿毛／巣立ち前）。
# 部品はどれも右向き。facing=-1 で左右反転、facing=0（正面）は右向きのまま描く（斜め前を向いた絵なので）。
def _chick_sprite_name(age):
    want = "chick_hatch" if age < 0.3 else ("chick_mid" if age < 0.75 else "chick_fledge")
    return want if (_SPRITE_DIR / f"{want}.png").exists() else "chick_mid"


def draw_emperor_chick(ctx, x, y, h, facing=1, age=0.0, a=1.0):
    """ヒナ（画像）。age 0=ふ化したて 0.5=綿毛 1=巣立ち前。h=全高"""
    _paint_sprite(ctx, _chick_sprite_name(max(0.0, min(1.0, age))), x, y, height=h * 0.97,
                  facing=(-1 if facing == -1 else 1), a=a)
