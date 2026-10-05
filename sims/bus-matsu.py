"""バスは平均10分おき（間隔はバラバラ）。バス停に着いた人は、平均何分待つ？

モデル: バスはでたらめな間隔で来る（ポアソン過程。間隔は指数分布で平均10分）。人はでたらめな時刻にバス停へ着く。
直感の外れ: 「10分おきなら、その半分の5分」（A）。正解は約10分（C）。
長い間隔ほど、そこに着く人が多く、しかも長く待つ（待ち時間のパラドックス。平均の待ち ＝ E[L²]/(2E[L]) ＝ 10分）。
時刻表どおり10分ぴったりなら5分になる。だから問いに「間隔はバラバラ」を必ず出す。

構成（2026-10-04 「データで語る棒人間」から取り入れた5つ。CHANNEL.md）:
- 0秒目はバス停の場面（Canva で作ったバスと待つ人）。問いは大きい1行、前提は0.8秒後に小さく
- カウントダウンの間に、60分の時間の線で Bさん（2分待ち）と Aさん（18分待ち）を見せる。Aさんにスポットライト
- 1万人モード: 600分の時間の帯（6段）に1万人が落ち、色＝待った時間。「1万人の平均」と「バスの間隔の平均」を並べて出しっぱなし
- 終わりに「いちばん長く待った人」に寄り、現象の名前「待ち時間のパラドックス」を出してから、締めの問いかけ（答えは概要欄）

照合: 100万人・長い時間で平均の待ち vs 10、同じ人で時刻表どおり（10分ぴったり）なら vs 5、
画面の回の「1万人の平均」と「バスの間隔の平均」が小数1桁で 10.0 になること。

画像（バス・待つ人）は Canva で作成（公開リポジトリには同梱しない）。assets/bus/ が無いときは線画で代わりに描く。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, SR, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, shimmer, text, thump,
                         tick, whoosh, _t)
from engine.parts import loop_back, r1, stills

note.use()
note.DATE = "10.5"                                # 日付欄（公開予定日）

SLUG = "bus-matsu"
N = 10000
MU = 10.0                                         # バスの間隔の平均（分）
T_ALL = 600.0                                     # 1万人が着く時間帯（分）
COLD, HOT = "#5aa0d8", RED                        # 待ちが短い／長い


def run(seed):
    r = np.random.default_rng(seed)
    bus = np.concatenate([[0.0], np.cumsum(r.exponential(MU, 200))])
    bus = bus[:np.searchsorted(bus, T_ALL) + 1]
    arr = r.uniform(0, T_ALL, N)
    k = np.searchsorted(bus, arr, side="right")
    return bus, arr, bus[k] - arr, k


# 画面の回: 1万人の平均の待ちも、バスの間隔の平均も、小数1桁で 10.0 になる回
for SEED in range(1, 50000):
    BUS, ARR, WAIT, KNEXT = run(SEED)
    if BUS[-1] >= T_ALL and r1(WAIT.mean()) == 10.0 and r1(np.diff(BUS).mean()) == 10.0:
        break
GAPS = np.diff(BUS)
LONG_I = int(np.argmax(WAIT))                     # いちばん長く待った人

# ---------- 冒頭の見本（60分の線の上の Bさん・Aさん） ----------
for S_SEED in range(1, 20000):
    _r = np.random.default_rng(900000 + S_SEED)
    _b = np.concatenate([[0.0], np.cumsum(_r.exponential(MU, 30))])
    _b = _b[_b <= 60]
    _g = np.diff(_b)
    if len(_b) < 6 or _b[-1] < 50 or _g.max() < 20 or _g.max() > 26 or _g.min() > 3.5:
        continue
    ia, ib = int(np.argmax(_g)), int(np.argmin(_g))
    if abs(ia - ib) < 2:
        continue
    S_BUS = _b
    TA = float(_b[ia] + 0.2 * _g[ia])               # Aさんは長い間隔のはじめのほうに着く
    TB = float(_b[ib] + 0.3 * _g[ib])
    WA, WB = float(_b[ia + 1] - TA), float(_b[ib + 1] - TB)
    if 15 <= WA <= 20 and WB <= 3:
        break

# ---------- 時間割 ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_LINE = 2.6                                      # バス停の場面 → 60分の線
T_B, T_A = 3.4, 4.8                               # Bさん・Aさんが着く
WAIT_ANIM = 1.0                                   # 待った時間の線が伸びる長さ（秒）
T_S_STICKY = T_A + WAIT_ANIM + 0.6
T_GO = T_S_STICKY + 3.3
T_BANNER = T_GO
T_M0 = T_BANNER + 2.1                             # 1万人
M_DUR = 6.5
T_M_END = T_M0 + M_DUR
T_REV = T_M_END + 0.4
T_LONG = T_REV + 3.0                              # いちばん長く待った人
T_NAME = T_LONG + 2.8                             # 「待ち時間のパラドックス」
T_Q = T_NAME + 4.0
DURATION = T_Q + 4.0
ORDER = np.random.default_rng(SEED + 5).permutation(N)   # 1万人が画面に現れる順


def m_count(t):
    if t < T_M0:
        return 0
    return int(N * clamp01((t - T_M0) / M_DUR) ** 1.6)


# ---------- 絵 ----------
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "bus"


def _load(name):
    from PIL import Image
    im = np.asarray(Image.open(ASSETS / name).convert("RGBA")).astype(np.float32) / 255
    pm = im[..., :3] * im[..., 3:4]
    out = np.empty(im.shape[:2] + (4,), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = pm[..., 2] * 255, pm[..., 1] * 255, pm[..., 0] * 255
    out[..., 3] = im[..., 3] * 255
    out = np.ascontiguousarray(out)
    return cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, out.shape[1], out.shape[0],
                                              out.shape[1] * 4), out


_KEYS = ("bus", "waiter")
IMG = {k: _load(f"{k}.png") for k in _KEYS} if all((ASSETS / f"{k}.png").exists() for k in _KEYS) else None


def sprite(ctx, key, cx, by, h, a=1.0):
    """下端の中央 (cx, by) を基準に高さ h で描く"""
    surf = IMG[key][0]
    k = h / surf.get_height()
    ctx.save()
    ctx.translate(cx, by)
    ctx.scale(k, k)
    ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height())
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(a)
    ctx.restore()


def bus_shape(ctx, cx, by, h, a=1.0):
    """バス（画像が無いときの線画、と小さいバスの印）"""
    if IMG is not None and h >= 40:
        sprite(ctx, "bus", cx, by, h, a)
        return
    w = h * 3.0
    ctx.set_source_rgba(*hexrgb("#5aa0d8", a))
    core.rrect(ctx, cx - w / 2, by - h, w, h * 0.82, h * 0.18)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a * 0.9)
    for i in range(4):
        ctx.rectangle(cx - w / 2 + w * (0.08 + 0.22 * i), by - h * 0.9, w * 0.16, h * 0.32)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, a))
    for x in (cx - w * 0.3, cx + w * 0.3):
        ctx.arc(x, by - h * 0.15, h * 0.15, 0, 2 * math.pi)
        ctx.fill()


def waiter(ctx, cx, by, h, a=1.0):
    if IMG is not None:
        sprite(ctx, "waiter", cx, by, h, a)
        return
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(h * 0.05)
    ctx.arc(cx, by - h * 0.88, h * 0.1, 0, 2 * math.pi)
    ctx.stroke()
    ctx.move_to(cx, by - h * 0.78)
    ctx.line_to(cx, by - h * 0.4)
    ctx.line_to(cx - h * 0.12, by)
    ctx.move_to(cx, by - h * 0.4)
    ctx.line_to(cx + h * 0.12, by)
    ctx.stroke()


def stop_sign(ctx, x, by, a=1.0):
    """バス停の標識（どこの会社でもない、丸い板と柱）"""
    ctx.set_source_rgba(*hexrgb("#7a7f8a", a))
    ctx.rectangle(x - 5, by - 300, 10, 300)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#e9edf2", a))
    ctx.arc(x, by - 300, 48, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb("#2f62c9", a))
    ctx.set_line_width(8)
    ctx.stroke()
    bus_shape_icon(ctx, x, by - 288, 26, a)


def bus_shape_icon(ctx, cx, by, h, a=1.0):
    w = h * 1.6
    ctx.set_source_rgba(*hexrgb("#2f62c9", a))
    core.rrect(ctx, cx - w / 2, by - h, w, h * 0.8, h * 0.2)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.rectangle(cx - w * 0.38, by - h * 0.9, w * 0.76, h * 0.3)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#2f62c9", a))
    for x in (cx - w * 0.28, cx + w * 0.28):
        ctx.arc(x, by - h * 0.12, h * 0.13, 0, 2 * math.pi)
        ctx.fill()


# 冒頭のバス停（画面の座標）: バスはでたらめな間隔で右から来て止まり、左へ去る
STOP_X, GROUND = 300, 860
SCENE_BUS = [0.4, 2.3]                            # バスが止まる時刻（冒頭の場面の中）
SCENE_WAIT0 = 2.0                                 # 0秒目の時点で、もう待っている分


def draw_stop_scene(ctx, t, a):
    if a <= 0:
        return
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))   # 道
    ctx.set_line_width(4)
    ctx.move_to(110, GROUND + 4)
    ctx.line_to(1000, GROUND + 4)
    ctx.stroke()
    stop_sign(ctx, STOP_X, GROUND, a)
    for ts in SCENE_BUS:                            # バス: 1.0秒で入って0.5秒止まり、0.8秒で去る
        u = t - ts
        if -1.0 <= u < 1.3:
            if u < 0:
                x = 560 + 700 * ease(-u)
            elif u < 0.5:
                x = 560
            else:
                x = 560 - 900 * ease((u - 0.5) / 0.8)
            bus_shape(ctx, x, GROUND, 150, a)
    waiter(ctx, 470, GROUND, 330, a)
    # 待った時間（場面の中では早回し）
    last = max([ts for ts in SCENE_BUS if ts <= t], default=None)
    w = (t - last) * 4 if last is not None else SCENE_WAIT0 + t * 4
    text(ctx, "待っている時間", 860, 470, 30, PENCIL, bold=False, alpha=a)
    text(ctx, f"{w:.0f}分", 860, 530, 60, INK, alpha=a)


# 60分の線（画面の座標）
LX0, LX1, LY = 170, 955, 730


def lx(m):
    return LX0 + (LX1 - LX0) * m / 60


def draw_line_sample(ctx, t, a):
    if a <= 0:
        return
    text(ctx, "あるバス停の60分", 580, 450, 32, PENCIL, bold=False, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(4)
    ctx.move_to(LX0, LY)
    ctx.line_to(LX1, LY)
    ctx.stroke()
    for m in (0, 30, 60):
        text(ctx, f"{m}分", lx(m), LY + 40, 26, PENCIL, bold=False, alpha=a)
    for b in S_BUS:
        bus_shape_icon(ctx, lx(b), LY - 6, 40, a)
    for name, ta, wt, t0, col in (("Bさん", TB, WB, T_B, PENCIL), ("Aさん", TA, WA, T_A, RED)):
        if t < t0:
            continue
        q = ease_out((t - t0) / 0.3)
        p = clamp01((t - t0 - 0.3) / WAIT_ANIM)
        x0 = lx(ta)
        if name == "Aさん" and t >= T_S_STICKY - 0.4:   # スポットライト
            s = ease_out((t - T_S_STICKY + 0.4) / 0.4)
            g = cairo.RadialGradient(x0, LY - 90, 10, x0, LY - 90, 160)
            g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.55 * s * a)
            g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
            ctx.set_source(g)
            ctx.arc(x0, LY - 90, 160, 0, 2 * math.pi)
            ctx.fill()
        waiter(ctx, x0, LY - 50 + 30 * (1 - q), 180, a * q)
        ctx.set_source_rgba(*hexrgb(col, a))         # 待った時間の線
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x0, LY + 80)
        ctx.line_to(x0 + (lx(ta + wt) - x0) * p, LY + 80)
        ctx.stroke()
        if p > 0:
            right = x0 > 640                           # 右のほうの人は、名札を左へ伸ばす（はみ出さないように）
            text(ctx, f"{name} {wt * p:.0f}分待ち", x0 - 6 if not right else lx(ta + wt) + 10,
                 LY + 130, 40, col, align="left" if not right else "right", alpha=a * q)
    if t >= T_S_STICKY:
        b = ease_out((t - T_S_STICKY) / 0.25) * a
        note.sticky(ctx, f"同じバス停でも {WB:.0f}分と {WA:.0f}分", 580, 480, 48, "pink", fg=RED, a=b)


class BIntro(note.Intro):
    """この回だけの冒頭。バス停の場面 → カウントダウンの間に60分の線で Bさん・Aさん"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        x = clamp01((t - T_LINE) / 0.3)
        draw_stop_scene(ctx, t, a * (1 - x))
        draw_line_sample(ctx, t, a * x)
        w = core.text_width(BIG_Q, 56)
        text(ctx, BIG_Q, 570, 945, 56, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 992, 570 + w / 2 + 6, 986, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 575, 1055, 34, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1150 + i * 88
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 58, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 775, 1145, 52, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 785, 1262, 72, 68, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(785, 1262)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 106, INK, alpha=a)
            ctx.restore()


BIG_Q = "平均10分おきのバス、何分待つ？"
DETAIL = "バスの間隔はバラバラ。着く時刻もでたらめ"
INTRO = BIntro(["バスは平均10分おき（間隔はバラバラ）。", "バス停で平均何分待つ？"],
               ["約5分", "約7分", "約10分"], correct=2, msg="", rule=None)

# ---------- 1万人の時間の帯（本体の座標） ----------
ROWS, ROW_MIN = 6, 100
BX0, BX1 = 150, 900
RY0, RGAP, BAND = 720, 92, 56                     # 1段目の線の y、段の間、人が落ちる帯の高さ


def pos(m):
    """時刻（分）→ (x, 線の y)"""
    row = np.minimum((np.asarray(m) // ROW_MIN).astype(int), ROWS - 1)
    x = BX0 + (BX1 - BX0) * (np.asarray(m) - row * ROW_MIN) / ROW_MIN
    return x, RY0 + row * RGAP


_px, _py = pos(ARR)
_jit = np.random.default_rng(SEED + 9).uniform(0, BAND, N)
PX, PY = _px, _py - 8 - _jit
_v = np.clip(WAIT / 25, 0, 1)
_c0, _c1 = np.array(hexrgb(COLD)[:3]), np.array(hexrgb(HOT)[:3])
PCOL = _c0[None, :] * (1 - _v[:, None]) + _c1[None, :] * _v[:, None]
_CACHE = {"n": 0, "surf": None}


def people_surface(n):
    if _CACHE["surf"] is None or n < _CACHE["n"]:
        _CACHE.update(n=0, surf=cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H))
    s = _CACHE["surf"]
    c = cairo.Context(s)
    for j in ORDER[_CACHE["n"]:n]:
        c.set_source_rgba(PCOL[j, 0], PCOL[j, 1], PCOL[j, 2], 0.85)
        c.arc(PX[j], PY[j], 2.2, 0, 2 * math.pi)
        c.fill()
    _CACHE["n"] = n
    return s


def draw_band(ctx, t, dim=0.0):
    for r in range(ROWS):
        y = RY0 + r * RGAP
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(3)
        ctx.move_to(BX0, y)
        ctx.line_to(BX1, y)
        ctx.stroke()
    bx, by = pos(BUS[:-1])
    for x, y in zip(bx, by):
        bus_shape_icon(ctx, float(x), float(y) + 22, 20)
    n = m_count(t)
    ctx.set_source_surface(people_surface(n), 0, 0)
    ctx.paint_with_alpha(1 - 0.5 * dim)
    shown = ORDER[:n]
    mw = float(WAIT[shown].mean()) if n else 0.0
    text(ctx, "1万人の平均待ち時間", 330, 1300, 32, INK, bold=False)
    text(ctx, f"{mw:.1f}分" if n else "—", 330, 1352, 56, RED)
    text(ctx, "バスの間隔の平均", 690, 1300, 32, INK, bold=False)
    text(ctx, f"{GAPS.mean():.1f}分", 690, 1352, 56, INK)
    note.legend(ctx, [(COLD, "すぐ乗れた"), (HOT, "長く待った")], 1418, 30)


def body(ctx, t):
    if t < T_BANNER:
        return
    if t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万人で待ってみる", 540, 950, a=a, t_rel=t - T_BANNER)
        return
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    draw_band(ctx, t, dim=clamp01((t - T_M_END) / 0.4) * (0.4 if t < T_LONG else 1.0))
    if T_M_END <= t < T_LONG + 0.3:
        a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - ease((t - T_LONG) / 0.3))
        note.sticky(ctx, f"1万人の平均は {WAIT.mean():.1f}分\n半分の5分じゃない", 540, 880, 60, "yellow", a=a)
    if t >= T_LONG and q < 1:
        # いちばん長く待った人に寄る（スポットライト）
        s = ease_out((t - T_LONG) / 0.4) * (1 - q)
        x, y = float(PX[LONG_I]), float(PY[LONG_I])
        g = cairo.RadialGradient(x, y, 4, x, y, 90)
        g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.8 * s)
        g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
        ctx.set_source(g)
        ctx.arc(x, y, 90, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, x, y, 22, 20, RED, seed=9, width=4, progress=s, alpha=s)
        note.sticky(ctx, f"いちばん長く待った人は {WAIT[LONG_I]:.0f}分", 540, 1232, 42,
                    "pink", fg=RED, a=s, tilt=0.02)
    if t >= T_NAME and q < 1:
        b = ease_out((t - T_NAME) / 0.3) * (1 - q)
        note.sticky(ctx, "これを「待ち時間のパラドックス」と呼ぶ", 540, 950, 44, "mint", a=b, tilt=-0.015)
    if q > 0:
        note.sticky(ctx, "平均10分おきなのに\nなんで平均10分も待つの？", 540, 880, 56, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 540, 1075, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def brake(dur=0.5):
    """バスが止まる「プシュー」"""
    t = _t(dur)
    n = np.random.default_rng(3).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(6) / 6, mode="same")
    return n * np.exp(-t * 5) * 0.6


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    for ts in SCENE_BUS:
        if ts >= 0:
            mx.add(ts, brake(), 0.35)
    for t0 in (T_B, T_A):
        mx.add(t0, blip(659.3, 0.12), 0.4)
        mx.add(t0 + 0.3 + WAIT_ANIM, bell(523.3 if t0 == T_B else 392.0, 0.8), 0.35)
    mx.add(T_S_STICKY, bell(784.0), 0.4)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    mx.add(T_M0, shimmer(400, M_DUR, seed=2), 0.35)
    mx.add(T_M_END, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(T_LONG, bell(880.0), 0.45)
    mx.add(T_NAME, chord([392.0, 493.9, 587.3], 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    # 照合: 100万人・長い時間帯で、でたらめな間隔なら10分、時刻表どおり（10分ぴったり）なら5分
    rb = np.random.default_rng(1)
    big_bus = np.concatenate([[0.0], np.cumsum(rb.exponential(MU, 2_000_000))])
    big_arr = rb.uniform(0, big_bus[-1] * 0.99, 1_000_000)
    big_wait = big_bus[np.searchsorted(big_bus, big_arr, side="right")] - big_arr
    sched_wait = MU - np.mod(ARR, MU)
    print(f"seed={SEED} 1万人の平均={WAIT.mean():.3f}分 間隔の平均={GAPS.mean():.3f}分（{len(GAPS)}本） "
          f"最長の待ち={WAIT.max():.1f}分 / 見本 seed={S_SEED} A={WA:.1f}分 B={WB:.1f}分 / 長さ={DURATION:.1f}秒")
    check_answers([
        ("100万人の平均の待ち（でたらめな間隔）", float(big_wait.mean()), MU, 0.05),
        ("同じ1万人・時刻表どおり（10分ぴったり）の平均", float(sched_wait.mean()), MU / 2, 0.1),
        ("画面の「1万人の平均」（小数1桁）", r1(WAIT.mean()), 10.0, 0),
        ("画面の「バスの間隔の平均」（小数1桁）", r1(GAPS.mean()), 10.0, 0),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 0.9, 1.6, 2.4, 3.0, T_B + 1.0, T_A + 1.0, T_S_STICKY + 0.5, T_BANNER + 0.6,
                      T_M0 + 2.0, T_M0 + 5.0, T_M_END + 1.0, T_LONG + 1.0, T_NAME + 1.0, T_Q + 2.0], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
