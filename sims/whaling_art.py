"""捕鯨船ロングの絵の部品 — 2026-11-08 作成

danchi_people.py / salmon_art.py と同じ考え方。
  - 平塗り・黒い輪郭線なし・陰はうすく1段だけ
  - 人物は danchi_people.draw_person（丸い頭・点の目・ほほえみ）。船員は帽子を足す
  - 鯨は描かない。遠くの潮吹き（白い噴き上げ）だけ

座標: (x, y) は基本「足もと／水面／置いた面の中央下」。W=1920, H=1080 を想定。
"""
import math
import random

import cairo

from danchi_people import _rgb, draw_person, mix, palette

W, H = 1920, 1080
YOU = "#f39a4a"       # あなた（オレンジ）
CREW = "#9db7df"      # 新米・船員・家族（うすい青）
FONT = "Meiryo"
INK = "#3a2c20"


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


def text(ctx, s, x, y, size, col=INK, bold=True, align="center"):
    """y は文字の縦の中心。"""
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    if align == "center":
        px = x - e.width / 2 - e.x_bearing
    elif align == "left":
        px = x - e.x_bearing
    else:
        px = x - e.width - e.x_bearing
    _set(ctx, col)
    ctx.move_to(px, y + size * 0.36)
    ctx.show_text(s)
    return e.width


def label(ctx, s, x, y, size, col="#ffffff", bg="#10284a"):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    pad = size * 0.45
    _set(ctx, bg)
    rrect(ctx, x - e.width / 2 - pad, y - size * 0.55 - pad * 0.6, e.width + 2 * pad, size * 1.1 + pad * 1.2, 14)
    ctx.fill()
    text(ctx, s, x, y, size, col)


# ---------------------------------------------------------------- 人物
def draw_sailor(ctx, x, y, h, you=False, facing=1, cap=True, color=None):
    """船員・新米（男・立ち姿）。you=True でオレンジ。シャツ・ズボンは draw_person の man、帽子を足す。"""
    col = color or (YOU if you else CREW)
    draw_person(ctx, x, y, h, "man", col, 0.0, facing, "stand")
    if not cap:
        return
    P = palette(col)
    u = h / 100.0
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(u * facing, u)
    hc_y, r = -82, 17
    _set(ctx, mix(col, "#000000", 0.30))
    ctx.arc(1, hc_y - 1.5, r + 1.6, math.pi * 1.0, math.pi * 2.0)
    ctx.close_path()
    ctx.fill()
    rrect(ctx, 5, hc_y - 4.5, r + 3, 4.2, 2.1)     # つば
    ctx.fill()
    _set(ctx, P["light"] if you else "#ffffff", 0.9)  # 帽子のふち
    rrect(ctx, -r - 0.6, hc_y - 5.2, 2 * r + 3.4, 4.2, 2)
    ctx.fill()
    ctx.restore()


def draw_family(ctx, x, y, h, kind="woman", facing=1, color=CREW):
    draw_person(ctx, x, y, h, kind, color, 0.0, facing, "stand")


# ---------------------------------------------------------------- 背景の部品
def waves(ctx, x0, x1, y0, y1, col, n=40, size=60, seed=1, a=0.7):
    rnd = random.Random(seed)
    _set(ctx, col, a)
    ctx.set_line_width(max(3, size * 0.07))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        s = size * rnd.uniform(0.6, 1.2)
        ctx.arc(x, y + s * 0.3, s * 0.5, math.pi * 1.15, math.pi * 1.85)
        ctx.stroke()


def cloud(ctx, x, y, s, col="#ffffff", a=0.9):
    _set(ctx, col, a)
    for dx, dy, r in ((-0.9, 0.1, 0.55), (-0.3, -0.25, 0.75), (0.45, -0.1, 0.65), (1.0, 0.15, 0.5)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi)
        ctx.fill()
    rrect(ctx, x - 1.2 * s, y + 0.1 * s, 2.7 * s, 0.55 * s, 0.27 * s)
    ctx.fill()


def draw_barrel(ctx, x, y, w=110, h=140, col="#b07a48"):
    """樽。(x, y) = 底の中央。"""
    sh = mix(col, "#000000", 0.2)
    bulge = w * 0.07
    ctx.new_sub_path()
    ctx.move_to(x - w / 2, y - h)
    ctx.curve_to(x - w / 2 - bulge, y - h * 0.65, x - w / 2 - bulge, y - h * 0.35, x - w / 2, y)
    ctx.line_to(x + w / 2, y)
    ctx.curve_to(x + w / 2 + bulge, y - h * 0.35, x + w / 2 + bulge, y - h * 0.65, x + w / 2, y - h)
    ctx.close_path()
    _set(ctx, col)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    _set(ctx, sh)
    ctx.rectangle(x - w / 2 - bulge, y - h, w * 0.3, h)
    ctx.fill()
    _set(ctx, mix(col, "#ffffff", 0.18))
    ctx.rectangle(x + w * 0.08, y - h, w * 0.1, h)
    ctx.fill()
    ctx.restore()
    _set(ctx, "#4a3322")
    for f in (0.16, 0.8):
        rrect(ctx, x - w / 2 - bulge * 0.8, y - h + h * f - h * 0.045, w + bulge * 1.6, h * 0.09, h * 0.03)
        ctx.fill()


def draw_boat(ctx, x, y, L, facing=1, col="#7a5436", a=1.0):
    """小さなボート。(x, y) = 水面の中央。"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(L / 100.0 * facing, L / 100.0)
    _set(ctx, col, a)
    ctx.move_to(-50, -9)
    ctx.curve_to(-42, 8, 42, 8, 50, -9)
    ctx.curve_to(20, -4, -20, -4, -50, -9)
    ctx.close_path()
    ctx.fill()
    _set(ctx, mix(col, "#ffffff", 0.25), a)
    ctx.move_to(-50, -9)
    ctx.curve_to(-20, -4, 20, -4, 50, -9)
    ctx.line_to(49, -11.5)
    ctx.curve_to(20, -6.5, -20, -6.5, -49, -11.5)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


def draw_ship(ctx, x, y, L, facing=1, hull="#5b3a2a", sail="#f6f0e0", a=1.0, flag="#d65a43"):
    """3本マストの帆船。(x, y) = 水面の中央、L = 船の長さ（約100単位）。"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(L / 100.0 * facing, L / 100.0)
    if a < 1.0:
        ctx.push_group()
    dark = mix(hull, "#000000", 0.35)
    masts = ((-29, -100), (1, -116), (30, -96))
    sh = mix(sail, "#7f90a8", 0.30)
    rope = mix(hull, "#000000", 0.2)
    # 張り綱（マストの先から船首・船尾へ）
    _set(ctx, rope, 0.8)
    ctx.set_line_width(0.7)
    for (mx, top), (ex, ey) in (((-29, -100), (-52, -24)), ((1, -116), (-52, -24)), ((30, -96), (-52, -24)),
                                ((30, -96), (72, -32)), ((1, -116), (72, -32)), ((-29, -100), (1, -116))):
        ctx.move_to(mx, top)
        ctx.line_to(ex, ey)
        ctx.stroke()
    _set(ctx, dark)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for mx, top in masts:
        ctx.set_line_width(2.0)
        ctx.move_to(mx, -22)
        ctx.line_to(mx, top)
        ctx.stroke()

    def one(mx, y0, y1, w, tone):
        """横帆。ヤード（帆桁）に張られ、下がふくらむ。"""
        col = mix(sail, "#c9d2e0", tone)
        bl = w / 2
        ctx.move_to(mx - bl, y0)
        ctx.line_to(mx + bl, y0)
        ctx.curve_to(mx + bl + 1.2, (y0 + y1) / 2, mx + bl - 1.0, y1 - 1.5, mx + bl - 0.5, y1)
        ctx.curve_to(mx + bl * 0.5, y1 + 4.6, mx - bl * 0.5, y1 + 4.6, mx - bl + 0.5, y1)
        ctx.curve_to(mx - bl + 1.0, y1 - 1.5, mx - bl - 1.2, (y0 + y1) / 2, mx - bl, y0)
        ctx.close_path()
        _set(ctx, col)
        ctx.fill_preserve()
        ctx.save()
        ctx.clip()
        _set(ctx, sh, 0.85)
        ctx.rectangle(mx - bl - 2, y0, w * 0.26, y1 - y0 + 8)
        ctx.fill()
        _set(ctx, "#ffffff", 0.55)
        ctx.rectangle(mx + w * 0.06, y0, w * 0.1, y1 - y0 + 8)
        ctx.fill()
        ctx.restore()
        _set(ctx, dark)                          # ヤード
        rrect(ctx, mx - bl - 2.5, y0 - 1.3, w + 5, 2.6, 1.2)
        ctx.fill()

    for i, (mx, top) in enumerate(masts):
        t = -top - 100          # 中央マストほど高い
        tone = (0.0, 0.0, 0.0)[i]
        one(mx, -27, -55, 33, 0.0)
        one(mx, -58 - 0.5 * t, -81 - 0.5 * t, 29, 0.05)
        one(mx, -84 - 0.5 * t, -102 - 0.5 * t, 21, 0.1)
    # 船首の三角帆（2枚）
    for tipx, tipy, base in ((36, -78, 74), (31, -52, 66)):
        _set(ctx, sail)
        ctx.move_to(52, -25)
        ctx.line_to(base, -31)
        ctx.line_to(tipx, tipy)
        ctx.close_path()
        ctx.fill()
        _set(ctx, sh)
        ctx.move_to(52, -25)
        ctx.line_to(tipx, tipy)
        ctx.line_to(tipx + 5, tipy + 24)
        ctx.close_path()
        ctx.fill()
    _set(ctx, dark)
    ctx.set_line_width(1.6)
    ctx.move_to(46, -23)
    ctx.line_to(74, -31)
    ctx.stroke()
    # 船体
    ctx.new_sub_path()
    ctx.move_to(-49, -22)
    ctx.line_to(55, -26)
    ctx.curve_to(46, -3, 32, 7, 14, 7)
    ctx.line_to(-30, 7)
    ctx.curve_to(-43, 5, -48, -7, -49, -22)
    ctx.close_path()
    _set(ctx, hull)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    _set(ctx, mix(hull, "#ffffff", 0.45))
    ctx.rectangle(-60, -17.5, 130, 3.6)
    ctx.fill()
    _set(ctx, dark)
    ctx.rectangle(-60, -2, 130, 12)
    ctx.fill()
    ctx.restore()
    # 手すり
    _set(ctx, dark)
    ctx.move_to(-49.5, -23)
    ctx.line_to(55.5, -27)
    ctx.line_to(55.5, -25.2)
    ctx.line_to(-49.5, -21.2)
    ctx.close_path()
    ctx.fill()
    if a < 1.0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


def draw_spout(ctx, x, y, s, a=0.95):
    """遠くの潮吹き（白い噴き上げ）。(x, y) = 根もと、s = 高さ。鯨の体は描かない。"""
    ctx.save()
    ctx.push_group()
    _set(ctx, "#ffffff")
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(s * 0.13)
    ctx.move_to(x, y)
    ctx.line_to(x, y - s * 0.62)
    ctx.stroke()
    ctx.set_line_width(s * 0.1)
    for sg in (-1, 1):
        ctx.move_to(x, y - s * 0.62)
        ctx.curve_to(x + sg * s * 0.1, y - s * 1.02, x + sg * s * 0.36, y - s * 0.98, x + sg * s * 0.42, y - s * 0.5)
        ctx.stroke()
    ctx.set_line_width(s * 0.07)
    for sg in (-1, 1):
        ctx.move_to(x, y - s * 0.55)
        ctx.curve_to(x + sg * s * 0.04, y - s * 0.86, x + sg * s * 0.2, y - s * 0.86, x + sg * s * 0.24, y - s * 0.46)
        ctx.stroke()
    ctx.arc(x, y - s * 0.04, s * 0.12, math.pi, 2 * math.pi)   # 根もとの白いしぶき
    ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ---------------------------------------------------------------- 書類・家・工場
def paper(ctx, x, y, w, h, col="#fbf7ea", rot=0.0, shadow=True):
    """紙。回転しても中身を描けるよう、変換を残して返す（呼び出し側が ctx.restore() する）。座標は紙の左上が原点。"""
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(rot)
    ctx.translate(-w / 2, -h / 2)
    if shadow:
        _set(ctx, "#000000", 0.16)
        rrect(ctx, 10, 14, w, h, 10)
        ctx.fill()
    _set(ctx, col)
    rrect(ctx, 0, 0, w, h, 10)
    ctx.fill()


def seal(ctx, x, y, r, col="#c8402f"):
    _set(ctx, col)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, mix(col, "#ffffff", 0.35))
    ctx.set_line_width(r * 0.1)
    ctx.arc(x, y, r * 0.68, 0, 2 * math.pi)
    ctx.stroke()


def gray_lines(ctx, x, y, w, n, gap, col="#cfc6b0", th=14, last=0.6):
    _set(ctx, col)
    for i in range(n):
        ww = w * (last if i == n - 1 else 1.0)
        rrect(ctx, x, y + i * gap, ww, th, th / 2)
        ctx.fill()


def draw_calendar(ctx, x, y, w, h, title="3月", crossed=12, first_dow=2, days=31):
    """壁の月めくり。(x, y) = 左上。"""
    _set(ctx, "#6b4a35")
    ctx.arc(x + w / 2, y - 26, 12, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(5)
    ctx.move_to(x + w / 2, y - 26)
    ctx.line_to(x + w * 0.22, y + 14)
    ctx.move_to(x + w / 2, y - 26)
    ctx.line_to(x + w * 0.78, y + 14)
    ctx.stroke()
    _set(ctx, "#000000", 0.14)
    rrect(ctx, x + 10, y + 14, w, h, 10)
    ctx.fill()
    _set(ctx, "#fbf7ea")
    rrect(ctx, x, y, w, h, 10)
    ctx.fill()
    hh = h * 0.2
    _set(ctx, "#c0502f")
    ctx.new_sub_path()
    ctx.arc(x + 10, y + 10, 10, math.pi, 1.5 * math.pi)
    ctx.arc(x + w - 10, y + 10, 10, 1.5 * math.pi, 2 * math.pi)
    ctx.line_to(x + w, y + hh)
    ctx.line_to(x, y + hh)
    ctx.close_path()
    ctx.fill()
    text(ctx, title, x + w / 2, y + hh / 2, hh * 0.62, "#ffffff")
    cw = w / 7
    top = y + hh + h * 0.04
    rh = (h - hh - h * 0.06) / 6
    for i, d in enumerate("日月火水木金土"):
        text(ctx, d, x + cw * (i + 0.5), top + rh * 0.4, rh * 0.42, "#c0502f" if i in (0, 6) else "#6a5a48")
    for d in range(1, days + 1):
        k = first_dow + d - 1
        cx = x + cw * (k % 7 + 0.5)
        cy = top + rh * (k // 7 + 1 + 0.5)
        text(ctx, str(d), cx, cy, rh * 0.46, "#3a2c20", bold=False)
        if d <= crossed:
            _set(ctx, "#d4472f", 0.85)
            ctx.set_line_width(rh * 0.09)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            s = rh * 0.34
            ctx.move_to(cx - s, cy - s)
            ctx.line_to(cx + s, cy + s)
            ctx.move_to(cx + s, cy - s)
            ctx.line_to(cx - s, cy + s)
            ctx.stroke()


def draw_factory(ctx, x, y, w, h, brick="#b5573e"):
    """町の工場（レンガ・煙突・窓）。(x, y) = 左上、屋根から地面まで h。煙突は上に伸びる。"""
    dark = mix(brick, "#000000", 0.28)
    for fx in (0.18, 0.72):
        cx = x + w * fx
        _set(ctx, brick)
        ctx.rectangle(cx - 45, y - h * 0.55, 90, h * 0.58)
        ctx.fill()
        _set(ctx, dark)
        ctx.rectangle(cx - 45, y - h * 0.55, 26, h * 0.58)
        ctx.fill()
        ctx.rectangle(cx - 56, y - h * 0.55, 112, 26)
        ctx.fill()
    _set(ctx, brick)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    _set(ctx, dark, 0.35)
    ctx.set_line_width(3)
    rows = int(h / 26)
    for i in range(1, rows):
        yy = y + i * 26
        ctx.move_to(x, yy)
        ctx.line_to(x + w, yy)
        ctx.stroke()
        for k in range(int(w / 70) + 1):
            xx = x + k * 70 + (35 if i % 2 else 0)
            if xx < x + w:
                ctx.move_to(xx, yy)
                ctx.line_to(xx, yy + 26)
                ctx.stroke()
    _set(ctx, dark)
    ctx.rectangle(x - 14, y - 22, w + 28, 40)
    ctx.fill()
    nwin = 6
    ww = w / (nwin * 1.7)
    for row in (0.2, 0.55):
        for i in range(nwin):
            wx = x + w * 0.06 + i * (w * 0.88 / nwin)
            wy = y + h * row
            _set(ctx, dark)
            rrect(ctx, wx - 6, wy - 6, ww + 12, h * 0.22 + 12, 6)
            ctx.fill()
            _set(ctx, "#f6e6a8")
            rrect(ctx, wx, wy, ww, h * 0.22, 4)
            ctx.fill()
            _set(ctx, "#ffffff", 0.35)
            ctx.rectangle(wx, wy, ww * 0.3, h * 0.22)
            ctx.fill()
    _set(ctx, "#5b3a2a")
    rrect(ctx, x + w * 0.45, y + h * 0.7, w * 0.1, h * 0.3, 8)
    ctx.fill()


def smoke(ctx, x, y, s, n=5, drift=0.5, a=0.85):
    for i in range(n):
        t = i / max(n - 1, 1)
        _set(ctx, "#f0f2f5" if i % 2 else "#e1e6ec", a * (1 - t * 0.5))
        ctx.arc(x + t * s * 2.2 * drift * 2, y - t * s * 2.6, s * (0.55 + t * 0.55), 0, 2 * math.pi)
        ctx.fill()


def pay_envelope(ctx, x, y, w=250, rot=0.0, col="#f3e9cf", mark="給料"):
    """給料袋。(x, y) = 中央。"""
    h = w * 0.6
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    _set(ctx, "#000000", 0.14)
    rrect(ctx, -w / 2 + 6, -h / 2 + 8, w, h, 8)
    ctx.fill()
    _set(ctx, col)
    rrect(ctx, -w / 2, -h / 2, w, h, 8)
    ctx.fill()
    _set(ctx, mix(col, "#000000", 0.08))
    ctx.move_to(-w / 2, -h / 2 + 4)
    ctx.line_to(0, h * 0.08)
    ctx.line_to(w / 2, -h / 2 + 4)
    ctx.line_to(w / 2, -h / 2 + 12)
    ctx.line_to(0, h * 0.18)
    ctx.line_to(-w / 2, -h / 2 + 12)
    ctx.close_path()
    ctx.fill()
    text(ctx, mark, 0, h * 0.27, h * 0.24, "#8a5a2b")
    ctx.restore()


def draw_stamp(ctx, x, y, s, label_="沈没", rot=-0.22, col="#c8402f"):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    _set(ctx, col, 0.92)
    ctx.set_line_width(s * 0.07)
    rrect(ctx, -s * 1.05, -s * 0.55, s * 2.1, s * 1.1, s * 0.12)
    ctx.stroke()
    text(ctx, label_, 0, 0, s * 0.8, col)
    ctx.restore()


# ---------------------------------------------------------------- 地図
def draw_map(ctx, bands):
    """太平洋とインド洋の地図。bands = [(経緯度の点列, 幅px, 色, 名前, (ラベルlon, lat)), ...]。陸は Natural Earth の形だけ。"""
    from whaling_map_data import LAND, xy
    _set(ctx, "#2a6899")
    ctx.paint()
    for pts, wd, col, _name, _lab in bands:
        ctx.push_group()
        _set(ctx, col)
        ctx.set_line_width(wd)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        p = [xy(lo, la) for lo, la in pts]
        ctx.move_to(*p[0])
        for q in p[1:]:
            ctx.line_to(*q)
        ctx.stroke()
        ctx.set_operator(cairo.OPERATOR_CLEAR)       # 陸と重なる部分は消す（帯は海の上だけ）
        for r in LAND:
            ctx.move_to(*r[0])
            for q in r[1:]:
                ctx.line_to(*q)
            ctx.close_path()
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.75)
    for r in LAND:
        _set(ctx, "#a9cd8a")
        ctx.move_to(*r[0])
        for q in r[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_line_width(1.2)
        ctx.stroke()
    for _pts, _wd, col, name, (lo, la) in bands:
        if not name:
            continue
        x, y = xy(lo, la)
        label(ctx, name, x, y, 46, "#ffffff", mix(col, "#000000", 0.55))


# ---------------------------------------------------------------- 地図（海の形に沿って塗る）
SEA_NORTH = [(136, 44), (134, 50), (137, 56), (143, 59.5), (155, 60.5), (160, 62), (165, 63), (170, 65), (178, 66), (190, 66), (193, 64),
             (196, 60), (200, 58), (207, 57), (215, 57), (223, 56), (246, 56), (246, 48), (224, 48), (210, 50), (200, 52), (188, 50),
             (176, 49), (165, 48), (156, 46), (148, 44.5), (142, 43.5)]
SEA_PACIFIC = [(142, 43.5), (148, 44.5), (156, 46), (165, 48), (176, 49), (188, 50), (200, 52), (210, 50), (224, 48), (246, 48), (246, -48),
               (143, -48), (143, -38), (143, -30), (135, -14), (125, -12), (118, -9), (110, -4), (104, 2), (105, 10), (108, 20), (112, 26),
               (118, 38), (125, 46), (136, 46)]
SEA_INDIAN = [(22, -48), (143, -48), (143, -38), (135, -34), (114, -24), (110, -10), (104, -5), (98, 3), (99, 12), (98, 22), (80, 26),
              (68, 26), (58, 25), (56, 20), (52, 13), (44, 11), (40, 5), (32, 5), (22, 5)]


def draw_map_seas(ctx, regions, base="#2a6899", alpha=0.85):
    """regions = [(経緯度の多角形, 色, 0〜1の濃さ), …]。海の範囲を半透明で塗り、陸の上は塗らない（陸は Natural Earth の形）"""
    from whaling_map_data import LAND, xy
    _set(ctx, base)
    ctx.paint()
    for pts, col, k in regions:
        if k <= 0.003:
            continue
        ctx.push_group()
        _set(ctx, col)
        p = [xy(lo, la) for lo, la in pts]
        ctx.move_to(*p[0])
        for q in p[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.fill_preserve()
        _set(ctx, mix(col, "#000000", 0.55))
        ctx.set_line_width(7)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        for r in LAND:
            ctx.move_to(*r[0])
            for q in r[1:]:
                ctx.line_to(*q)
            ctx.close_path()
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha * k)
    for r in LAND:
        _set(ctx, "#a9cd8a")
        ctx.move_to(*r[0])
        for q in r[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.fill_preserve()
        _set(ctx, "#7fa862")
        ctx.set_line_width(1.2)
        ctx.stroke()
