"""江戸の町人（横向き）の手描き風の絵 — 2026-10-28 作成（夜道ロング sims/yomichi-long.py 用）

draw_townsman(ctx, x, y, h, pose, phase, facing, ...)
  (x, y) = 足もと（地面）の中央、h = 身長（足の裏から髷の上まで）。頭身は約6.5。
  pose  : "stand" 立つ／"walk" 歩く（phase 0〜1 で1歩きの周期）／"grope" 手さぐり（片手を前へ、腰が引ける、すり足）
  facing: +1 右向き／-1 左向き
  night : True なら明るい細い縁取りを足す（藍色の地でも形が分かるように）
draw_crowd(ctx, x, y, w, h, n, ...)  小さい町人を格子に並べる（262人・10人の場面）

形の決まり: ちょんまげ（月代〔さかやき〕は肌色・後ろ髪と髷は黒）、着物（すそ広がり・前合わせ）、帯、
袂〔たもと〕の垂れた袖、すねから下と草履が見える。顔は横顔の鼻・目・耳だけ。
"""
import math

import cairo

INK = "#24324a"
SKIN = "#f1cfa8"
SKIN_SH = "#d9ad85"
HAIR = "#26283a"
OBI = "#c98a3c"
ZORI = "#8a6a45"
HANAO = "#b23a3a"
KIMONO = "#4d6fb3"


def _rgb(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def _shade(h, k):
    r, g, b, _ = _rgb(h)
    return "#%02x%02x%02x" % tuple(int(max(0, min(1, c * k)) * 255) for c in (r, g, b))


def _path(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def _smooth(ctx, pts, close=True):
    """点列を通るなめらかな線（Catmull-Rom を Bezier に）"""
    n = len(pts)
    if n < 3:
        _path(ctx, pts, close)
        return
    P = list(pts)
    ctx.move_to(*P[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if (close or i > 0) else P[i]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (close or i + 2 < n) else P[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        ctx.close_path()


def _fill_stroke(ctx, fill, a, lw, edge=INK):
    ctx.set_source_rgba(*_rgb(fill, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*_rgb(edge, a))
    ctx.set_line_width(lw)
    ctx.stroke()


def _legs(phase, pose):
    """左右の脚（近い脚・遠い脚）の (腰からの太もも角度, ひざの曲がり)。角度は真下=0、前=+"""
    if pose == "stand":
        return [(0.05, 0.02), (-0.04, 0.02)]
    if pose == "grope":
        A, base, kb = 0.16, 0.10, 0.30                           # すり足・ひざを少し曲げる
    else:
        A, base, kb = 0.36, 0.0, 0.0
    out = []
    for off in (0.0, 0.5):
        ph = 2 * math.pi * (phase + off)
        th = base + A * math.sin(ph)
        swing = max(0.0, math.cos(ph))                             # 前へ振り出している脚はひざが曲がる
        knee = kb + (0.55 if pose == "walk" else 0.25) * swing ** 1.5 + 0.06
        out.append((th, knee))
    return out


def draw_townsman(ctx, x, y, h, pose="walk", phase=0.0, facing=1, kimono=KIMONO, a=1.0, night=False,
                  arm_reach=1.0, lean=None, detail=True, hold=False, lookup=False):
    if a <= 0.003:
        return
    if pose == "small":
        _icon(ctx, x, y, h, facing, kimono, a, night)
        return
    if night:
        # 夜は、人の形全体のまわりに明るい細い縁（輪郭だけ。中の線には出さない）
        ctx.push_group()
        _townsman(ctx, x, y, h, pose, phase, facing, kimono, 1.0, arm_reach, lean, detail, hold, lookup)
        pat = ctx.pop_group()
        r = max(1.5, h / 100.0 * 1.6)
        ctx.save()
        ctx.set_source_rgba(0.93, 0.95, 1.0, 0.75 * a)
        for k in range(12):
            ang = 2 * math.pi * k / 12
            ctx.save()
            ctx.translate(r * math.cos(ang), r * math.sin(ang))
            ctx.mask(pat)
            ctx.restore()
        ctx.restore()
        ctx.set_source(pat)
        ctx.paint_with_alpha(a)
        return
    _townsman(ctx, x, y, h, pose, phase, facing, kimono, a, arm_reach, lean, detail, hold, lookup)


HOLD_HAND = (13.0, -66.0)                                          # 傘を持つ手の位置（体の座標・足もと原点）


def _icon(ctx, x, y, h, facing, kimono, a, night):
    """群れ用の小さい町人（頭を大きめにした、ずんぐりした形）。(x, y) 足もと"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(facing * h / 100.0, h / 100.0)
    lw = 3.2
    if night:
        ctx.set_source_rgba(0.93, 0.95, 1.0, 0.7 * a)
        ctx.arc(2, -72, 20, 0, 2 * math.pi)
        ctx.fill()
        _path(ctx, [(-24, -2), (24, -2), (16, -58), (-14, -58)])
        ctx.fill()
    # 足
    ctx.set_source_rgba(*_rgb(INK, a))
    ctx.rectangle(-12, -6, 9, 6)
    ctx.rectangle(4, -6, 9, 6)
    ctx.fill()
    # 着物（すそ広がり）
    _smooth(ctx, [(-10, -56), (12, -56), (16, -30), (20, -6), (-20, -6), (-15, -30)])
    _fill_stroke(ctx, kimono, a, lw)
    ctx.set_source_rgba(*_rgb(OBI, a))
    ctx.rectangle(-13.5, -38, 28, 7)
    ctx.fill()
    # 頭・髪・髷
    ctx.arc(2, -72, 15, 0, 2 * math.pi)
    _fill_stroke(ctx, SKIN, a, lw)
    ctx.set_source_rgba(*_rgb(HAIR, a))
    ctx.arc(2, -72, 15.5, math.pi * 0.55, math.pi * 1.45)
    ctx.fill()
    ctx.save()
    ctx.translate(3, -89)
    ctx.scale(1.0, 0.45)
    ctx.arc(0, 0, 10, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    ctx.set_source_rgba(*_rgb(INK, a))
    ctx.arc(10, -73, 2.4, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def _townsman(ctx, x, y, h, pose, phase, facing, kimono, a, arm_reach, lean, detail, hold=False, lookup=False):
    night = False
    u = h / 100.0
    if hold:
        lean = 0.0
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(facing * u, u)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    lw = 1.25 if detail else 1.6                                   # 線の太さ（単位 u）
    if lean is None:
        lean = 0.10 if pose == "grope" else (0.03 if pose == "walk" else 0.0)

    # 脚の形と、体の上下（いちばん低い足が地面）
    THIGH, SHIN = 24.0, 24.0
    HIP = (0.0, -49.0)
    legs = _legs(phase, pose)
    feet, knees = [], []
    for th, kn in legs:
        kx = HIP[0] + THIGH * math.sin(th)
        ky = HIP[1] + THIGH * math.cos(th)
        sa = th - kn
        fx = kx + SHIN * math.sin(sa)
        fy = ky + SHIN * math.cos(sa)
        knees.append((kx, ky))
        feet.append((fx, fy))
    drop = -max(f[1] for f in feet)                                # 足の裏を地面（0）に合わせる
    ctx.translate(0, drop)
    if pose == "walk":
        ctx.translate(0, -0.8 * abs(math.sin(2 * math.pi * phase)))

    # 上半身の傾き（腰を中心に）
    def tilt(p):
        dx, dy = p[0] - HIP[0], p[1] - HIP[1]
        c, s = math.cos(lean), math.sin(lean)
        return (HIP[0] + dx * c - dy * s, HIP[1] + dx * s + dy * c)

    edge_w = lw
    halo = night

    def outline_halo(draw):
        """夜は明るい縁を先に太く描いて、形を地から浮かせる"""
        if not halo:
            return
        ctx.save()
        draw()
        ctx.set_source_rgba(0.93, 0.95, 1.0, 0.55 * a)
        ctx.set_line_width(edge_w + 3.2)
        ctx.stroke()
        ctx.restore()

    sh = tilt((0.6, -78.0))                                        # 肩
    # ---- 腕の位置 ----
    sw = math.sin(2 * math.pi * phase) if pose == "walk" else 0.0

    def arm_pts(near):
        if hold and near:                                          # 傘の柄を胸の前で持つ
            hx_, hy_ = HOLD_HAND[0], HOLD_HAND[1] - drop
            ex_, ey_ = sh[0] + 3.0, sh[1] + 14.0
            return (ex_, ey_), (hx_, hy_), math.atan2(hx_ - sh[0], hy_ - sh[1])
        if pose == "grope" and near:
            up = 1.15 * arm_reach                                  # 前へ差し出す（真下=0）
            el = 0.25
        elif pose == "grope":
            up, el = 0.35, 0.35
        elif pose == "walk":
            up = (-0.42 if near else 0.42) * sw
            el = 0.30 + 0.15 * max(0.0, (up))
        else:
            up, el = (0.06 if near else -0.04), 0.18
        ua = 15.5
        ex = sh[0] + ua * math.sin(up + lean)
        ey = sh[1] + ua * math.cos(up + lean)
        fa = up + el + lean
        hx = ex + 13.5 * math.sin(fa)
        hy = ey + 13.5 * math.cos(fa)
        return (ex, ey), (hx, hy), up + lean

    def draw_arm(near):
        (ex, ey), (hx, hy), ang = arm_pts(near)
        col = kimono if near else _shade(kimono, 0.78)
        # 前腕（袖口から手首まで。袖の下に描く）
        cuff0 = (ex + (hx - ex) * 0.40, ey + (hy - ey) * 0.40)
        fdx, fdy = hx - cuff0[0], hy - cuff0[1]
        fl = math.hypot(fdx, fdy) or 1
        fnx, fny = -fdy / fl * 1.9, fdx / fl * 1.9
        _path(ctx, [(cuff0[0] - fnx, cuff0[1] - fny), (hx - fnx * 0.8, hy - fny * 0.8),
                    (hx + fnx * 0.8, hy + fny * 0.8), (cuff0[0] + fnx, cuff0[1] + fny)])
        _fill_stroke(ctx, SKIN if near else SKIN_SH, a, lw * 0.9)
        # 手
        ctx.save()
        _hand(ctx, hx, hy, math.atan2(hx - ex, hy - ey), near, pose, a, lw)
        ctx.restore()
        # 袖（肩からひじ、袂が下に垂れる）
        dx, dy = ex - sh[0], ey - sh[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L                                   # 腕に直角
        if ny < 0:
            nx, ny = -nx, -ny                                      # 下向きの側を袂にする
        cuff = (ex + (hx - ex) * 0.45, ey + (hy - ey) * 0.45)      # 袖口（前腕の半ば）
        tamoto = 7.0 if (pose == "grope" and near) else 11.5
        pts = [
            (sh[0] - nx * 3.6, sh[1] - ny * 3.6),
            (cuff[0] - nx * 2.6, cuff[1] - ny * 2.6),
            (cuff[0] + nx * 3.0, cuff[1] + ny * 3.0),
            (cuff[0] + nx * 3.0 + (dx / L) * -2.0, cuff[1] + ny * tamoto),   # 垂れた袂の先
            ((sh[0] + ex) / 2 + nx * 4.0, (sh[1] + ey) / 2 + ny * (tamoto + 1.5)),
            (sh[0] + nx * 4.6, sh[1] + ny * 4.6),
        ]

        def d():
            _smooth(ctx, pts)
        outline_halo(d)
        d()
        _fill_stroke(ctx, col, a, lw)
        # 袖口の線
        ctx.set_source_rgba(*_rgb(INK, a * 0.8))
        ctx.set_line_width(lw * 0.8)
        ctx.move_to(cuff[0] - nx * 2.6, cuff[1] - ny * 2.6)
        ctx.line_to(cuff[0] + nx * 3.0, cuff[1] + ny * 3.0)
        ctx.stroke()

    # ---- 遠い腕・両脚（着物のすそで上が隠れるので先に描く） ----
    draw_arm(False)
    far = 1
    _leg(ctx, knees[far], feet[far], a, lw, far=True, halo=halo, edge_w=edge_w)
    _leg(ctx, knees[1 - far], feet[1 - far], a, lw, far=False, halo=halo, edge_w=edge_w)

    # ---- 着物（胴とすそ） ----
    # すその前後は脚に沿って広がる
    def hem_pt(i, out):
        kx, ky = knees[i]
        fx, fy = feet[i]
        t = 0.38
        return (kx + (fx - kx) * t + out, ky + (fy - ky) * t)
    front = max(range(2), key=lambda i: feet[i][0])
    back = 1 - front
    hf = hem_pt(front, 4.2)
    hb = hem_pt(back, -4.2)
    hf = (max(hf[0], 8.5), max(min(hf[1], -12.0), -17.0))
    hb = (min(hb[0], -8.5), max(min(hb[1], -12.0), -17.0))
    neck = tilt((1.2, -82.0))
    chest = tilt((7.0, -72.0))
    belly = tilt((6.6, -58.0))
    waist_f = tilt((6.8, -50.0))
    back_sh = tilt((-6.4, -77.0))
    back_w = tilt((-6.2, -55.0))
    back_hip = tilt((-7.6, -45.0))
    body = [neck, (sh[0] + 3.0, sh[1] - 1.5), chest, belly, waist_f,
            ((waist_f[0] + hf[0]) / 2 + 1.2, (waist_f[1] + hf[1]) / 2),
            hf, ((hf[0] + hb[0]) / 2, max(hf[1], hb[1]) + 1.5), hb,
            ((back_hip[0] + hb[0]) / 2 - 1.0, (back_hip[1] + hb[1]) / 2),
            back_hip, back_w, back_sh]

    def dbody():
        _smooth(ctx, body)
    outline_halo(dbody)
    dbody()
    _fill_stroke(ctx, kimono, a, lw)

    # 前合わせ（衿から斜めにすそへ）と衿
    ctx.set_source_rgba(*_rgb(INK, a * 0.85))
    ctx.set_line_width(lw * 0.9)
    p1 = tilt((3.8, -79.0))
    p2 = tilt((5.6, -62.0))
    ctx.move_to(*p1)
    ctx.curve_to(p1[0] + 1.5, p1[1] + 6, p2[0], p2[1] - 4, p2[0], p2[1])
    ctx.stroke()
    ctx.move_to(*tilt((6.4, -48.0)))
    ctx.curve_to(*tilt((7.5, -36.0)), *tilt((hf[0] - 2.0, -22.0)), hf[0] - 1.5, hf[1] + 0.5)
    ctx.stroke()
    ctx.set_source_rgba(*_rgb("#f4ead6", a))                    # 白い衿（半衿）
    _path(ctx, [tilt((0.0, -81.5)), tilt((4.4, -80.0)), tilt((3.6, -76.0)), tilt((0.4, -78.5))])
    ctx.fill()

    # 帯
    obi = [tilt((-6.6, -59.5)), tilt((6.9, -60.0)), tilt((7.1, -52.5)), tilt((-6.9, -52.0))]
    _path(ctx, obi)
    _fill_stroke(ctx, OBI, a, lw * 0.9)
    knot = tilt((-7.2, -56.0))                                   # 帯の結び目（後ろ）
    ctx.save()
    ctx.translate(*knot)
    ctx.rotate(lean)
    ctx.rectangle(-3.0, -3.2, 3.4, 6.4)
    ctx.restore()
    _fill_stroke(ctx, _shade(OBI, 0.85), a, lw * 0.8)

    # すそのしわ（2本）
    if detail:
        ctx.set_source_rgba(*_rgb(INK, a * 0.45))
        ctx.set_line_width(lw * 0.7)
        for k in (0.35, 0.68):
            sx_ = back_hip[0] + (hb[0] - back_hip[0]) * 0.2 + (hf[0] - hb[0]) * k * 0.9
            ctx.move_to(sx_ + 1.0, -40.0)
            ctx.line_to(sx_ + (k - 0.5) * 6, max(hf[1], hb[1]) - 1.5)
            ctx.stroke()

    # ---- 首・頭 ----
    hc = tilt((2.0, -90.5))
    ctx.save()
    ctx.translate(*hc)
    ctx.rotate(lean * 0.6 + (0.10 if pose == "grope" else 0.0) - (0.22 if lookup else 0.0))
    ctx.set_source_rgba(*_rgb(SKIN, a))                          # 首
    _path(ctx, [(-2.4, 4.0), (2.2, 4.0), (2.6, 9.0), (-2.6, 9.0)])
    ctx.fill()
    _head(ctx, a, lw, halo, edge_w)
    ctx.restore()

    # ---- 近い腕（いちばん手前） ----
    draw_arm(True)
    ctx.restore()


def _leg(ctx, knee, foot, a, lw, far, halo, edge_w):
    """すねから下（着物のすその下に見える部分）と草履"""
    kx, ky = knee
    fx, fy = foot
    col = SKIN_SH if far else SKIN
    ang = math.atan2(fx - kx, fy - ky)
    nx, ny = math.cos(ang), -math.sin(ang)
    w0, w1 = 2.9, 2.2
    pts = [(kx - nx * w0, ky - ny * w0), (fx - nx * w1, fy - ny * w1 - 1.5),
           (fx + nx * w1, fy + ny * w1 - 1.5), (kx + nx * w0, ky + ny * w0)]
    if halo:
        ctx.save()
        _path(ctx, pts)
        ctx.set_source_rgba(0.93, 0.95, 1.0, 0.55 * a)
        ctx.set_line_width(edge_w + 3.2)
        ctx.stroke()
        ctx.restore()
    _path(ctx, pts)
    _fill_stroke(ctx, col, a, lw)
    # 足（甲）と草履。足先は前（+x）を向く
    toe = 1.0 + 0.0 * math.sin(ang)
    sole_y = fy + 0.4
    foot_pts = [(fx - 3.4, fy - 2.6), (fx + 2.0, fy - 3.4), (fx + 6.8 * toe, fy - 1.2), (fx + 6.6 * toe, sole_y - 0.6),
                (fx - 3.6, sole_y - 0.6)]
    _smooth(ctx, foot_pts)
    _fill_stroke(ctx, col, a, lw * 0.9)
    ctx.set_source_rgba(*_rgb(ZORI, a))                          # 草履の底
    ctx.rectangle(fx - 4.4, sole_y - 0.6, 12.0, 1.9)
    ctx.fill()
    ctx.set_source_rgba(*_rgb(INK, a))
    ctx.set_line_width(lw * 0.7)
    ctx.rectangle(fx - 4.4, sole_y - 0.6, 12.0, 1.9)
    ctx.stroke()
    ctx.set_source_rgba(*_rgb(HANAO, a * (0.7 if far else 1.0)))    # 鼻緒
    ctx.set_line_width(1.3)
    ctx.move_to(fx + 4.2, sole_y - 0.6)
    ctx.line_to(fx + 1.0, fy - 3.0)
    ctx.stroke()


def _hand(ctx, hx, hy, ang, near, pose, a, lw):
    """手（指をそろえた、ややまるい形）。ang は前腕の向き"""
    ctx.translate(hx, hy)
    ctx.rotate(-ang)
    col = SKIN if near else SKIN_SH
    if pose == "grope" and near:
        # 手のひらを前に向けて、指をそろえて少し開く（横から見ると細長い）
        pts = [(-2.2, -1.0), (2.2, -1.0), (2.8, 5.0), (1.6, 8.6), (-0.6, 8.8), (-2.6, 5.4)]
    else:
        pts = [(-2.3, -1.0), (2.3, -1.0), (2.6, 3.6), (1.2, 6.2), (-1.4, 6.0), (-2.6, 3.4)]
    _smooth(ctx, pts)
    _fill_stroke(ctx, col, a, lw * 0.9)
    # 親指
    ctx.set_source_rgba(*_rgb(INK, a * 0.7))
    ctx.set_line_width(lw * 0.7)
    ctx.move_to(2.2, 1.0)
    ctx.line_to(3.4, 3.6)
    ctx.stroke()


def _head(ctx, a, lw, halo, edge_w):
    """横顔（右向き）。原点は頭の中心"""
    # 頭の形（あごと後頭部）
    head = [(-6.4, -1.0), (-5.8, -5.6), (-2.4, -8.2), (2.4, -8.0), (5.8, -5.2), (6.8, -1.6),
            (7.9, 0.6), (6.9, 1.6), (7.2, 3.0), (6.4, 4.0), (6.2, 5.4), (4.2, 7.4), (0.6, 7.6), (-3.6, 5.4), (-6.0, 2.6)]
    if halo:
        ctx.save()
        _smooth(ctx, head)
        ctx.set_source_rgba(0.93, 0.95, 1.0, 0.55 * a)
        ctx.set_line_width(edge_w + 3.2)
        ctx.stroke()
        ctx.restore()
    _smooth(ctx, head)
    _fill_stroke(ctx, SKIN, a, lw)
    # 後ろ髪・横の髪（耳の後ろから首すじへ）
    hair = [(-6.6, -1.6), (-6.0, -5.8), (-3.0, -8.3), (-1.0, -8.5), (-2.0, -6.0), (-2.2, -2.6),
            (-2.4, 1.0), (-3.6, 3.6), (-6.2, 2.6)]
    _smooth(ctx, hair)
    _fill_stroke(ctx, HAIR, a, lw * 0.8)
    # 月代（そり上げた頭のてっぺん）はうすい青み
    ctx.set_source_rgba(*_rgb("#c9d3dc", a))
    _smooth(ctx, [(-0.8, -8.5), (2.4, -8.3), (5.4, -5.8), (2.6, -6.6), (-0.6, -6.6)])
    ctx.fill()
    # 髷（頭の上に前へ向けてのせる）
    ctx.save()
    ctx.translate(0.2, -9.0)
    ctx.rotate(-0.10)
    _smooth(ctx, [(-3.6, 0.6), (-3.4, -0.9), (1.0, -1.5), (5.4, -1.1), (6.0, 0.0), (5.2, 0.7), (0.6, 0.9)])
    _fill_stroke(ctx, HAIR, a, lw * 0.8)
    ctx.restore()
    ctx.set_source_rgba(*_rgb(HAIR, a))                          # 髷の根元（元結）
    ctx.rectangle(-3.0, -9.6, 1.6, 2.0)
    ctx.fill()
    # 耳
    ctx.set_source_rgba(*_rgb(SKIN_SH, a))
    ctx.save()
    ctx.translate(-0.4, 0.4)
    ctx.scale(1.2, 1.7)
    ctx.arc(0, 0, 1.3, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill_preserve()
    ctx.set_source_rgba(*_rgb(INK, a))
    ctx.set_line_width(lw * 0.6)
    ctx.stroke()
    # 目・まゆ・口
    ctx.set_source_rgba(*_rgb(INK, a))
    ctx.arc(4.4, -1.6, 0.85, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(lw * 0.7)
    ctx.move_to(3.2, -3.9)
    ctx.line_to(5.6, -3.6)
    ctx.stroke()
    ctx.move_to(5.0, 4.4)
    ctx.line_to(6.2, 4.2)
    ctx.stroke()


def draw_crowd(ctx, x, y, w, h, n, cols=None, kimono=KIMONO, a=1.0, night=False, seed=0, t=0.0, walk=False, small=None):
    """小さい町人を格子に並べる。(x, y) 左上、(w, h) 範囲。人の高さはマスに合わせる"""
    if n <= 0 or a <= 0.003:
        return
    if cols is None:
        cols = max(1, int(round(math.sqrt(n * w / max(h, 1) * 0.45))))
    rows = int(math.ceil(n / cols))
    cw, chh = w / cols, h / rows
    ph = min(chh * 0.92, cw * 2.6)
    if small is None:
        small = ph < 90                                       # 小さいときは、ずんぐりした形で町人と分かるように
    if small:
        ph = min(chh * 0.92, cw * 1.25)
    k = 0
    for r in range(rows):
        for c in range(cols):
            if k >= n:
                return
            cx = x + (c + 0.5) * cw
            fy = y + (r + 1) * chh - chh * 0.05
            phase = ((k * 0.37 + seed * 0.11) % 1.0) + (t * 0.8 if walk else 0.0)
            draw_townsman(ctx, cx, fy, ph, pose="small" if small else ("walk" if walk else "stand"), phase=phase, facing=1,
                          kimono=kimono, a=a, night=night, detail=ph > 60)
            k += 1
