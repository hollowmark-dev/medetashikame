"""サケの卵と魚（横向き・平塗り）の絵 — 2026-11-05 作成（サケの卵ロング #89）

danchi_people.py と同じ考え方。
  - 黒い輪郭線なし・陰はうすく1段だけ
  - 丸い目と小さなほほえみ。小さくしても卵・魚と分かる形
  - 群れごとに1色。濃淡はその色から作る

draw_egg(ctx, x, y, r, color, face)       (x, y) = 中心、r = 半径。face=True で目と口がつく
draw_fish(ctx, x, y, L, color, kind, ...) (x, y) = 体の中心、L = 鼻先から尾の先まで
  kind : "fry" 稚魚（頭が大きい・背に模様）／"adult" 成魚（細長い・脇に帯）
  phase : 尾の振り（0〜1で1周）、facing : 1 右向き／-1 左向き
draw_eggs / draw_school  群れを奥から手前へ並べる
gravel_bed / river_mouth / north_sea / set_net  背景と網
"""
import math
import random

from danchi_people import mix, palette, _rgb


def _set(ctx, h, a=1.0):
    r, g, b = _rgb(h)
    ctx.set_source_rgba(r, g, b, a)


def draw_egg(ctx, x, y, r, color="#cfdcf0", face=False, a=1.0):
    P = palette(color)
    _set(ctx, P["dark"] if not face else mix(color, "#000000", 0.18), a)
    ctx.arc(x, y + r * 0.05, r, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, color, a)
    ctx.arc(x - r * 0.04, y - r * 0.03, r * 0.95, 0, 2 * math.pi)
    ctx.fill()
    _set(ctx, "#ffffff", 0.75 * a)
    ctx.save()
    ctx.translate(x - r * 0.42, y - r * 0.5)
    ctx.rotate(-0.6)
    ctx.scale(r * 0.26, r * 0.15)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    if face:
        for dx in (-0.3, 0.3):
            _set(ctx, "#2b2118", a)
            ctx.arc(x + r * dx, y + r * 0.02, r * 0.13, 0, 2 * math.pi)
            ctx.fill()
            _set(ctx, "#ffffff", a)
            ctx.arc(x + r * dx - r * 0.04, y - r * 0.03, r * 0.045, 0, 2 * math.pi)
            ctx.fill()
        _set(ctx, "#2b2118", a)
        ctx.set_line_width(r * 0.07)
        ctx.set_line_cap(1)
        ctx.arc(x, y + r * 0.18, r * 0.17, 0.25, math.pi - 0.25)
        ctx.stroke()
        _set(ctx, "#f2706a", 0.55 * a)
        for dx in (-0.55, 0.55):
            ctx.arc(x + r * dx, y + r * 0.26, r * 0.12, 0, 2 * math.pi)
            ctx.fill()


def _body_path(ctx, L, H, nose=0.5, waist=-0.34):
    """鼻先 (+L*nose, 0) から細くなる所 (L*waist, 0) までの体。中心が原点。"""
    nx, wx = L * nose, L * waist
    wh = H * 0.13
    ctx.move_to(nx, 0)
    ctx.curve_to(nx - L * 0.1, -H * 0.52, L * 0.05, -H * 0.62, wx + L * 0.1, -wh * 1.5)
    ctx.line_to(wx, -wh)
    ctx.line_to(wx, wh)
    ctx.line_to(wx + L * 0.1, wh * 1.5)
    ctx.curve_to(L * 0.05, H * 0.58, nx - L * 0.1, H * 0.5, nx, 0)
    ctx.close_path()


def draw_fish(ctx, x, y, L, color="#9db7df", kind="adult", phase=0.0, facing=1, a=1.0, face=True):
    P = palette(color)
    warm = P["light"] == color
    belly = mix(color, "#ffffff", 0.55)
    back = mix(color, "#000000", 0.2) if warm else P["dark"]
    H = L * (0.40 if kind == "fry" else 0.30)
    sway = math.sin(phase * 2 * math.pi)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(facing, 1)
    wx = -L * 0.34
    # 尾びれ
    tip = -L * 0.5
    ctx.move_to(wx + L * 0.02, -H * 0.1)
    ctx.line_to(tip, -H * 0.5 + sway * H * 0.16)
    ctx.line_to(tip + L * 0.05, sway * H * 0.1)
    ctx.line_to(tip, H * 0.5 + sway * H * 0.16)
    ctx.line_to(wx + L * 0.02, H * 0.1)
    ctx.close_path()
    _set(ctx, back, a)
    ctx.fill()
    # 背びれ・あぶらびれ・しりびれ
    ctx.move_to(L * 0.09, -H * 0.42)
    ctx.curve_to(L * 0.05, -H * 0.72, -L * 0.02, -H * 0.78, -L * 0.05, -H * 0.72)
    ctx.curve_to(-L * 0.06, -H * 0.6, -L * 0.08, -H * 0.5, -L * 0.11, -H * 0.36)
    ctx.close_path()
    _set(ctx, back, a)
    ctx.fill()
    ctx.arc(-L * 0.245, -H * 0.2, L * 0.022, 0, 2 * math.pi)
    ctx.fill()
    ctx.move_to(-L * 0.08, H * 0.42)
    ctx.line_to(-L * 0.18, H * 0.68)
    ctx.line_to(-L * 0.22, H * 0.28)
    ctx.close_path()
    ctx.fill()
    # 体
    _body_path(ctx, L, H)
    _set(ctx, color, a)
    ctx.fill()
    ctx.save()
    _body_path(ctx, L, H)
    ctx.clip()
    _set(ctx, belly, a)
    ctx.rectangle(-L, H * 0.14, 2 * L, H)
    ctx.fill()
    _set(ctx, back, a)
    ctx.rectangle(-L, -H, 2 * L, H * 0.62)
    ctx.fill()
    if kind == "fry":
        # 稚魚の背の模様
        for k in range(5):
            ctx.save()
            ctx.translate(L * 0.1 - k * L * 0.095, -H * 0.1)
            ctx.scale(L * 0.024, H * 0.2)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            _set(ctx, mix(back, "#000000", 0.15), a)
            ctx.fill()
    else:
        # 成魚の脇のうすい帯
        for k in range(4):
            xx = L * 0.05 - k * L * 0.085
            ctx.rectangle(xx, -H * 0.3, L * 0.022, H * 0.55)
            _set(ctx, back, 0.55 * a)
            ctx.fill()
    ctx.restore()
    # 胸びれ
    ctx.move_to(L * 0.12, H * 0.14)
    ctx.curve_to(L * 0.08, H * 0.3, L * 0.02, H * 0.42, -L * 0.01, H * 0.4)
    ctx.curve_to(L * 0.01, H * 0.28, L * 0.04, H * 0.18, L * 0.06, H * 0.1)
    ctx.close_path()
    _set(ctx, back, a)
    ctx.fill()
    if face:
        ex, ey = L * (0.27 if kind == "fry" else 0.32), -H * 0.1
        er = max(H * (0.2 if kind == "fry" else 0.17), 1.6)
        _set(ctx, "#ffffff", a)
        ctx.arc(ex, ey, er, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#2b2118", a)
        ctx.arc(ex + er * 0.15, ey, er * 0.62, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, "#ffffff", a)
        ctx.arc(ex + er * 0.02, ey - er * 0.22, er * 0.2, 0, 2 * math.pi)
        ctx.fill()
        if L > 60:
            _set(ctx, "#2b2118", a)
            ctx.set_line_width(max(L * 0.008, 1.5))
            ctx.set_line_cap(1)
            ctx.arc(L * 0.4, H * 0.1, L * 0.035, 0.2, math.pi - 0.4)
            ctx.stroke()
            _set(ctx, "#f2706a", 0.5 * a)
            ctx.arc(L * (0.2 if kind == "fry" else 0.25), H * 0.14, er * 0.55, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()


def _grid(x0, y0, x1, y1, n, rnd, jitter):
    """n 個前後を枠いっぱいに散らす。行ごとに半分ずらして、格子に見えないようにする"""
    cols = max(1, round(math.sqrt(n * (x1 - x0) / max(1, y1 - y0))))
    rows = max(1, round(n / cols))
    pts = []
    for j in range(rows):
        for i in range(cols):
            cx = (i + (0.25 if j % 2 else 0.75) + rnd.uniform(-jitter, jitter)) / cols
            cy = (j + 0.5 + rnd.uniform(-jitter, jitter)) / rows
            pts.append((x0 + (x1 - x0) * cx, y0 + (y1 - y0) * cy, rnd.random()))
    return sorted(pts, key=lambda p: p[1])


def _clear(px, py, keepout):
    return keepout is None or math.hypot(px - keepout[0], py - keepout[1]) > keepout[2]


def draw_eggs(ctx, x0, y0, x1, y1, n, color, r, seed=1, keepout=None):
    """keepout=(x, y, 半径) の中には描かない（あなたの周りをあける）"""
    rnd = random.Random(seed)
    pts = _grid(x0, y0, x1, y1, n, rnd, 0.28)
    for px, py, ph in pts:
        if _clear(px, py, keepout):
            draw_egg(ctx, px, py, r * (0.92 + 0.13 * ph), color)
    return pts


def draw_school(ctx, x0, y0, x1, y1, n, color, size, kind="adult", seed=1, facing=1, phase=0.0, keepout=None):
    rnd = random.Random(seed)
    pts = _grid(x0, y0, x1, y1, n, rnd, 0.2)
    for px, py, ph in pts:
        if _clear(px, py, keepout):
            depth = 0.85 + 0.2 * (py - y0) / max(1, y1 - y0)
            draw_fish(ctx, px, py, size * depth, color, kind, phase + ph, facing)
    return pts


def _stones(ctx, x0, y0, x1, y1, n, cols, seed, rmin, rmax):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        rx, ry = rnd.uniform(rmin, rmax), rnd.uniform(rmin, rmax) * 0.72
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(rnd.uniform(-0.3, 0.3))
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        _set(ctx, rnd.choice(cols))
        ctx.fill()


def gravel_bed(ctx, W, H, top=330):
    """川の断面: 上が水、下が砂利。"""
    _set(ctx, "#3e8fc4")
    ctx.rectangle(0, 0, W, top)
    ctx.fill()
    _set(ctx, "#5aa6d6")
    ctx.rectangle(0, 0, W, top * 0.34)
    ctx.fill()
    _set(ctx, "#ffffff", 0.35)
    ctx.set_line_width(5)
    ctx.set_line_cap(1)
    for xx, yy in ((180, 190), (640, 250), (1180, 170), (1620, 240)):
        ctx.move_to(xx, yy)
        ctx.curve_to(xx + 50, yy - 16, xx + 90, yy + 16, xx + 150, yy)
        ctx.stroke()
    _set(ctx, "#5b4a3a")
    ctx.rectangle(0, top, W, H - top)
    ctx.fill()
    _stones(ctx, -30, top - 8, W + 30, top + 44, 80, ("#8a7560", "#9b8670", "#7a6652"), 3, 26, 52)
    _stones(ctx, 0, top + 40, W, H, 150, ("#665442", "#6f5c49", "#5f4e3e"), 5, 18, 44)


def river_mouth(ctx, W, H):
    """河口: 左に陸と川、右へ海がひらく。"""
    _set(ctx, "#bfe3f2")
    ctx.rectangle(0, 0, W, H * 0.3)
    ctx.fill()
    _set(ctx, "#1f6fa8")
    ctx.rectangle(0, H * 0.3, W, H)
    ctx.fill()
    _set(ctx, "#2f86bd")
    ctx.rectangle(0, H * 0.3, W, H * 0.12)
    ctx.fill()
    _set(ctx, "#7fb56a")
    ctx.move_to(0, H * 0.3)
    ctx.line_to(W * 0.42, H * 0.3)
    ctx.curve_to(W * 0.3, H * 0.34, W * 0.14, H * 0.36, 0, H * 0.37)
    ctx.close_path()
    ctx.fill()
    _set(ctx, "#e9d9a8")
    ctx.move_to(0, H)
    ctx.line_to(W, H)
    ctx.line_to(W, H * 0.92)
    ctx.curve_to(W * 0.6, H * 0.97, W * 0.25, H * 0.86, 0, H * 0.84)
    ctx.close_path()
    ctx.fill()


def north_sea(ctx, W, H):
    """北の海: 暗い青の平塗りと、上の冷たい光。"""
    _set(ctx, "#123a63")
    ctx.paint()
    _set(ctx, "#1a4d7d")
    ctx.rectangle(0, 0, W, H * 0.34)
    ctx.fill()
    _set(ctx, "#2a6a9c")
    ctx.rectangle(0, 0, W, H * 0.12)
    ctx.fill()
    _set(ctx, "#0e2e4e")
    ctx.move_to(0, H)
    ctx.line_to(W, H)
    ctx.line_to(W, H * 0.92)
    ctx.curve_to(W * 0.7, H * 0.86, W * 0.3, H * 0.97, 0, H * 0.9)
    ctx.close_path()
    ctx.fill()


def set_net(ctx, x0, y0, x1, y1, a=1.0, cell=62):
    """沿岸の網: 白い線の格子だけ。"""
    _set(ctx, "#ffffff", 0.6 * a)
    ctx.set_line_width(4)
    x = x0
    while x <= x1 + 0.1:
        ctx.move_to(x, y0)
        ctx.line_to(x, y1)
        x += cell
    y = y0
    while y <= y1 + 0.1:
        ctx.move_to(x0, y)
        ctx.line_to(x1, y)
        y += cell
    ctx.stroke()
    _set(ctx, "#f2c14e", a)
    for xx in (x0, x1):
        ctx.arc(xx, y0 - 12, 16, 0, 2 * math.pi)
        ctx.fill()
