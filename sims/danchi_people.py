"""昭和40年代の申込者（横向き・平塗り）の絵 — 2026-11-02 作成（団地の抽選ロングの試し）

参考: 桶狭間の今のサムネ（11/1 差し替え）の人の感じ。
  - 黒い輪郭線なし・陰はうすく1段だけ（奥の手足を1段暗く）
  - 丸い大きな頭・点の目・ほほえみ。小さくしても人と分かる頭身（約3.3頭身）
  - 群れごとに1色。服も髪もその色の濃淡で塗り、肌だけ肌色寄り

draw_person(ctx, x, y, h, kind, color, phase, facing, pose)
  (x, y) = 足もと中央、h = 身長（足の裏から頭のてっぺん）
  kind  : "man" 父（半袖シャツ・ズボン）／"woman" 母（ボブ・ブラウス・ひざ丈スカート）／"kid" 子（帽子・半ズボン）
  color : 群れの色（例 "#3d6db3"）。濃淡はここから作る
  pose  : "walk"（phase 0〜1 で1歩きの周期）／"stand"
draw_crowd(ctx, x0, y0, x1, y1, n, colors, ...) 群れを奥から手前へぎっしり並べる
palette(color) で色の濃淡を返す（建物などにも使う）
"""
import math
import random

import cairo


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(int(max(0, min(1, c)) * 255) for c in rgb)


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] * (1 - t) + rb[i] * t for i in range(3)])


def palette(color):
    """群れの色から、明るい・ふつう・暗い・いちばん暗い・肌・髪 を作る。"""
    # 暖色は白を混ぜると肌と同じ色になり、シャツを着ていないように見える（2026-11-04）。元の色のまま使う
    r, g, b = _rgb(color)
    warm = r > g > b and r - b > 0.25
    return {
        "light": color if warm else mix(color, "#ffffff", 0.55),
        "mid": mix(color, "#000000", 0.14) if warm else color,
        "dark": mix(color, "#000000", 0.28),
        "darkest": mix(color, "#000000", 0.5),
        "skin": mix("#f7dcc4", color, 0.10),
        "skin_sh": mix("#e9bf9c", color, 0.16),
        "hair": mix(color, "#101018", 0.62),
        "cheek": mix("#f2a49a", color, 0.10),
    }


def _set(ctx, h, a=1.0):
    r, g, b = _rgb(h)
    ctx.set_source_rgba(r, g, b, a)


def _limb(ctx, x0, y0, length, width, ang, col, a=1.0):
    """丸い先の棒（腕・脚）。ang は真下から前向きへの角度（ラジアン）。"""
    x1 = x0 + math.sin(ang) * length
    y1 = y0 + math.cos(ang) * length
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(width)
    _set(ctx, col, a)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    return x1, y1


def _rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def draw_person(ctx, x, y, h, kind="man", color="#3d6db3", phase=0.0, facing=1,
                pose="walk", a=1.0, face=True):
    P = palette(color)
    u = h / 100.0
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(u * facing, u)
    if a < 1.0:
        ctx.push_group()

    swing = math.sin(phase * 2 * math.pi) * (0.42 if pose == "walk" else 0.0)
    bob = -abs(math.cos(phase * 2 * math.pi)) * 1.6 if pose == "walk" else 0.0
    ctx.translate(0, bob)

    hip_y = -34
    leg_len = 30 if kind != "kid" else 28
    leg_w = 12
    if kind == "woman":
        leg_w = 9.5

    # 色の割り当て（服は群れの色の濃淡）
    if kind == "man":
        top, top_sh, bottom, bottom_sh = P["light"], P["mid"], P["darkest"], P["hair"]
    elif kind == "woman":
        top, top_sh, bottom, bottom_sh = P["light"], P["mid"], P["mid"], P["dark"]
    else:
        top, top_sh, bottom, bottom_sh = P["mid"], P["dark"], P["darkest"], P["hair"]
    shoe = P["hair"]

    # --- 奥の脚と腕（1段暗く） ---
    if kind == "woman":
        _limb(ctx, -4, -18, 15, leg_w, -swing * 0.9, P["skin_sh"])
        _limb(ctx, -4 - math.sin(swing * 0.9) * 15 + 0.6, -3.5, 3, 7.5, 1.4, shoe)
    elif kind == "kid":
        _limb(ctx, -4, hip_y + 4, 13, 12, -swing, bottom_sh)
        fx, fy = _limb(ctx, -4 - math.sin(swing) * 13, hip_y + 4 + math.cos(swing) * 13,
                       leg_len - 15, 9.5, -swing, P["skin_sh"])
        _limb(ctx, fx + 1, fy + 0.5, 3, 7.5, 1.45, shoe)
    else:
        fx, fy = _limb(ctx, -4, hip_y, leg_len - 2, leg_w, -swing, bottom_sh)
        _limb(ctx, fx + 1, fy + 0.8, 3.5, 8.5, 1.45, shoe)
    arm_top = -61 if kind != "kid" else -58
    if kind == "man":
        ex, ey = _limb(ctx, -3, arm_top, 11, 11, swing * 0.85, top_sh)
        _limb(ctx, ex, ey, 11, 8.5, swing * 0.85 + 0.15, P["skin_sh"])
    else:
        ex, ey = _limb(ctx, -3, arm_top, 9, 10, swing * 0.85, top_sh)
        _limb(ctx, ex, ey, 12, 8, swing * 0.85 + 0.15, P["skin_sh"])

    # --- 手前の脚 ---
    if kind == "woman":
        fx, fy = _limb(ctx, 4, -18, 15, leg_w, swing * 0.9, P["skin"])
        _limb(ctx, fx + 0.6, fy + 0.5, 3, 7.5, 1.4, shoe)
    elif kind == "kid":
        _limb(ctx, 4, hip_y + 4, 13, 12, swing, bottom)
        fx, fy = _limb(ctx, 4 + math.sin(swing) * 13, hip_y + 4 + math.cos(swing) * 13,
                       leg_len - 15, 9.5, swing, P["skin"])
        _limb(ctx, fx + 1, fy + 0.5, 3, 7.5, 1.45, shoe)
    else:
        fx, fy = _limb(ctx, 4, hip_y, leg_len - 2, leg_w, swing, bottom)
        _limb(ctx, fx + 1, fy + 0.8, 3.5, 8.5, 1.45, shoe)

    # --- 胴 ---
    if kind == "woman":
        # スカート（台形・ひざ丈）
        _set(ctx, bottom)
        ctx.move_to(-12, -40)
        ctx.line_to(12, -40)
        ctx.line_to(17, -16)
        ctx.curve_to(7, -14.5, -7, -14.5, -17, -16)
        ctx.close_path()
        ctx.fill()
        _set(ctx, bottom_sh)
        ctx.move_to(-12, -40)
        ctx.line_to(-5, -40)
        ctx.line_to(-8, -15)
        ctx.curve_to(-11, -15.2, -14.5, -15.6, -17, -16)
        ctx.close_path()
        ctx.fill()
        _set(ctx, top)
        _rrect(ctx, -13, -66, 26, 28, 8)
        ctx.fill()
        _set(ctx, top_sh)
        _rrect(ctx, -13, -66, 8, 28, 6)
        ctx.fill()
    elif kind == "kid":
        _set(ctx, top)
        _rrect(ctx, -13, -60, 26, 30, 8)
        ctx.fill()
        _set(ctx, top_sh)
        _rrect(ctx, -13, -60, 8, 30, 6)
        ctx.fill()
    else:
        # ズボンの腰
        _set(ctx, bottom)
        _rrect(ctx, -13, -42, 26, 12, 4)
        ctx.fill()
        _set(ctx, top)
        _rrect(ctx, -14, -66, 28, 28, 8)
        ctx.fill()
        _set(ctx, top_sh)
        _rrect(ctx, -14, -66, 8, 28, 6)
        ctx.fill()
        # ベルト
        _set(ctx, P["hair"])
        ctx.rectangle(-13, -39.5, 26, 2.8)
        ctx.fill()

    # --- 手前の腕 ---
    if kind == "man":
        ex, ey = _limb(ctx, 3, arm_top, 11, 11, -swing * 0.85, top)
        _limb(ctx, ex, ey, 11, 8.5, -swing * 0.85 + 0.15, P["skin"])
    else:
        ex, ey = _limb(ctx, 3, arm_top, 9, 10, -swing * 0.85, top)
        _limb(ctx, ex, ey, 12, 8, -swing * 0.85 + 0.15, P["skin"])
    if kind == "woman":
        # 手さげ（奥の手と手前の手のあいだでなく、手前の手に）
        hx = ex + math.sin(-swing * 0.85 + 0.15) * 12
        hy = ey + math.cos(-swing * 0.85 + 0.15) * 12
        _set(ctx, P["dark"])
        _rrect(ctx, hx - 5, hy + 1, 10, 8, 2.2)
        ctx.fill()
        ctx.set_line_width(1.4)
        ctx.arc(hx, hy + 1.5, 3, math.pi, 2 * math.pi)
        ctx.stroke()

    # --- 頭 ---
    hc_y = -82 if kind != "kid" else -79
    r = 17 if kind != "kid" else 17.5
    # 首
    _set(ctx, P["skin_sh"])
    ctx.rectangle(-3.5, hc_y + r - 6, 7, 8)
    ctx.fill()
    if kind == "woman":
        # 後ろ髪（ボブ・あごの高さまで）
        _set(ctx, P["hair"])
        _rrect(ctx, -r - 2.5, hc_y - r - 1.5, r * 1.55, r * 2.0, 11)
        ctx.fill()
    _set(ctx, P["skin"])
    ctx.arc(1, hc_y, r, 0, 2 * math.pi)
    ctx.fill()
    # 鼻（右の縁に小さなふくらみ）
    ctx.arc(r + 0.2, hc_y + 1.5, 3.0, 0, 2 * math.pi)
    ctx.fill()
    # 髪
    _set(ctx, P["hair"])
    if kind == "man":
        ctx.move_to(-r + 0.5, hc_y + 3)
        ctx.arc(1, hc_y, r + 1.2, math.pi * 0.93, math.pi * 1.86)
        ctx.curve_to(r - 2, hc_y - 9, 6, hc_y - 9, 2, hc_y - 7)
        ctx.curve_to(-3, hc_y - 5, -6, hc_y + 1, -9, hc_y + 4)
        ctx.close_path()
        ctx.fill()
    elif kind == "woman":
        ctx.move_to(-r - 1, hc_y + 12)
        ctx.arc(1, hc_y, r + 2, math.pi * 0.85, math.pi * 1.9)
        ctx.curve_to(r - 1, hc_y - 8, 8, hc_y - 11, 0, hc_y - 6)
        ctx.curve_to(-5, hc_y - 2, -7, hc_y + 6, -7, hc_y + 12)
        ctx.close_path()
        ctx.fill()
    else:
        # 帽子（つば付き・群れの色）
        _set(ctx, P["mid"])
        ctx.arc(1, hc_y - 2, r + 1.2, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.fill()
        _rrect(ctx, 4, hc_y - 4.5, r + 4, 4.5, 2.2)
        ctx.fill()
    # 耳
    _set(ctx, P["skin_sh"])
    ctx.arc(-3.5, hc_y + 2, 3.6, 0, 2 * math.pi)
    ctx.fill()
    if face:
        # 目（点）・ほお・口（ほほえみ）
        _set(ctx, "#2b2b33")
        ctx.arc(9.5, hc_y + 0.5, 2.1, 0, 2 * math.pi)
        ctx.fill()
        _set(ctx, P["cheek"], 0.55)
        ctx.arc(7.5, hc_y + 6.5, 3.0, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_line_width(1.6)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        _set(ctx, "#7a4a3e")
        ctx.arc(12.5, hc_y + 6.5, 3.2, math.pi * 0.25, math.pi * 0.8)
        ctx.stroke()

    if a < 1.0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


KINDS = ("man", "woman", "man", "woman", "kid")


def draw_crowd(ctx, x0, y0, x1, y1, n, colors, size, seed=1, facing=1, kinds=KINDS,
               pose="walk"):
    """矩形 (x0,y0)-(x1,y1) に n 人を奥から手前へ並べる。colors は1人ずつの色のリスト（長さ n）か1色。
    戻り値: 並べた人の足もと座標のリスト（描いた順）。"""
    rnd = random.Random(seed)
    w, hgt = x1 - x0, y1 - y0
    ratio = w / max(hgt, 1)
    rows = max(1, round(math.sqrt(n / ratio * 1.6)))
    cols = math.ceil(n / rows)
    dx = w / max(cols, 1)
    dy = hgt / max(rows, 1)
    spots = []
    k = 0
    for r in range(rows):
        for c in range(cols):
            if k >= n:
                break
            off = (dx / 2) * (r % 2)
            px = x0 + c * dx + off + rnd.uniform(-dx * 0.12, dx * 0.12)
            py = y0 + (r + 1) * dy + rnd.uniform(-dy * 0.08, dy * 0.08)
            spots.append((px, py))
            k += 1
    order = sorted(range(len(spots)), key=lambda i: spots[i][1])
    for i in order:
        col = colors[i] if isinstance(colors, (list, tuple)) else colors
        draw_person(ctx, spots[i][0], spots[i][1], size, kinds[i % len(kinds)], col,
                    phase=rnd.random(), facing=facing, pose=pose)
    return [spots[i] for i in order]


def draw_danchi(ctx, x, y, w, h, color, floors=5, units=8):
    """名前も印もない5階建ての団地（平塗り）。(x, y) は左下。"""
    P = palette(color)
    _set(ctx, P["light"])
    ctx.rectangle(x, y - h, w, h)
    ctx.fill()
    # 屋上のふち
    _set(ctx, P["mid"])
    ctx.rectangle(x - w * 0.01, y - h - h * 0.04, w * 1.02, h * 0.05)
    ctx.fill()
    fh = h * 0.92 / floors
    uw = w / units
    for f in range(floors):
        fy = y - h * 0.96 + f * fh
        for i in range(units):
            ux = x + i * uw
            # 窓
            _set(ctx, P["mid"])
            ctx.rectangle(ux + uw * 0.18, fy + fh * 0.18, uw * 0.64, fh * 0.42)
            ctx.fill()
            # ベランダの手すり
            _set(ctx, P["dark"])
            ctx.rectangle(ux + uw * 0.08, fy + fh * 0.62, uw * 0.84, fh * 0.2)
            ctx.fill()
    # 階段室（縦の帯）
    _set(ctx, mix(P["light"], P["mid"], 0.45))
    for i in (units // 4, units * 3 // 4):
        ctx.rectangle(x + i * uw - uw * 0.12, y - h * 0.96, uw * 0.24, h * 0.96)
        ctx.fill()


def draw_person_reach(ctx, x, y, h, kind="man", color="#3d6db3", facing=1, reach=1.0, a=1.0):
    """手を前へ差し出して立つ人（2026-11-04 追記）。draw_person の絵のまま、手前の腕の角度だけを変える。
    reach=0 で下げたまま、1 で胸の高さまで前へ出す。手さげを持たない kind="man" で使う"""
    global _limb
    orig = _limb
    state = {"arm": False}

    def limb(c, x0, y0, length, width, ang, col, al=1.0):
        if abs(x0 - 3) < 1e-9 and y0 in (-61, -58):
            state["arm"] = True
            return orig(c, x0, y0, length * (1 + 0.25 * reach), width, ang + 1.3 * reach, col, al)
        if state["arm"]:
            state["arm"] = False
            return orig(c, x0, y0, length * (1 + 0.25 * reach), width, ang + 1.3 * reach, col, al)
        return orig(c, x0, y0, length, width, ang, col, al)
    _limb = limb
    try:
        draw_person(ctx, x, y, h, kind, color, phase=0.0, facing=facing, pose="stand", a=a)
    finally:
        _limb = orig
