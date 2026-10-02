"""表なら持ち金1.5倍、裏なら0.6倍。コインを100回投げたら、得する人は何%？

1回あたりの平均は (1.5 + 0.6) ÷ 2 ＝ 1.05倍。得なゲームに見えるので、直感は「6割以上が得」（A）か「約半分」（B）。
正解は約14%（C 2割以下）。得をするのは表が56回以上出た人だけで、その確率は Σ_{k≥56} C(100,k)/2^100 ≈ 0.1356。
表と裏が1回ずつなら ×1.5×0.6 ＝ ×0.9 なので、半々に出た「真ん中の人」は 1000円 × 0.9^50 ≈ 5円になる。
平均が得になるのは、表が極端に多く出たごく一部の人が何億円にもなるから（1万人の1位は約4.7億円）。

1人目: 表→裏で 1000円 → 1500円 → 900円（「勝って負けたのに減った」を最初に見せる）。
一時は約1.5万円まで増えるが、100回で32円。→ 1万人の線を対数の目盛りで重ねる。線の色は、そのとき1000円より多いか少ないか。
真ん中の人の線を赤で引き、終わりに「得したのは13.6%」「真ん中の人は5円」「1位は4.7億円」。
締めは「平均は得なのに、なんで？」→ 答えは概要欄。

2026-09-30 アリ（ari-10000）がユーザー「気持ち悪いからやめよう」で没になり、その代わりに作った回。
案出し（Fable との合議）の6番「期待値プラスのコインゲーム」。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, shimmer, text, thump,
                         tick, whoosh, _t)
from engine.parts import loop_back, pct, r1, stills

note.use()
note.DATE = "10.2"                                # 日付欄（公開予定日）

SLUG = "bai-100kai"
N, F = 10000, 100
UP, DOWN = 1.5, 0.6
START = 1000                                      # はじめの持ち金（円）
L_UP, L_DN = math.log10(UP), math.log10(DOWN)
HEAD, HEAD_RIM = "#dca42a", "#9a6a12"             # 表（金）
TAIL, TAIL_RIM = "#4f6fa8", "#3a5282"             # 裏（銀の青）
METAL = {True: ("#fff1b8", "#e6b53f", "#a8761b", "#6e4a0c"),
         False: ("#f7f9fc", "#b8c4d4", "#76859b", "#4a5566")}
GAIN_C = "#c98a10"                                # 1000円より多い（金）
LOSS_C = "#5a78b0"                                # 1000円より少ない（青）

K_WIN = next(k for k in range(F + 1) if k * L_UP + (F - k) * L_DN > 0)   # 得をするのに要る表の回数（56）
EXACT_P = sum(math.comb(F, k) for k in range(K_WIN, F + 1)) / 2 ** F     # 0.1356
EXACT_MED = START * (UP * DOWN) ** (F // 2)                                # 真ん中の人（表50回）5.15円


def play(seed):
    rng = np.random.default_rng(seed)
    flips = rng.integers(0, 2, (N, F), dtype=np.int8)
    steps = np.where(flips == 1, L_UP, L_DN)
    lg = np.concatenate([np.full((N, 1), math.log10(START)), math.log10(START) + np.cumsum(steps, axis=1)], axis=1)
    return flips, lg                               # lg[i, s] ＝ s回投げたあとの持ち金（log10 円）


# 乱数の種: 得した割合が理論値と小数1桁（%）まで同じで、真ん中の人がちょうど表50回になるもの
for SEED in range(1, 2000):
    FLIPS, LG = play(SEED)
    KS = FLIPS.sum(axis=1)
    SIM_P = float((LG[:, -1] > math.log10(START)).mean())
    ks = np.sort(KS)
    if r1(SIM_P * 100) == r1(EXACT_P * 100) and ks[N // 2 - 1] == ks[N // 2] == F // 2:
        break
ORDER = np.argsort(LG[:, -1], kind="stable")
MED_I = int(ORDER[N // 2])                        # 真ん中の人（表50回）
TOP_I = int(ORDER[-1])                            # 1位
SIM_MED = 10 ** LG[MED_I, -1]
TOP_YEN = 10 ** LG[TOP_I, -1]


def yen(v):
    """持ち金を読みやすく（4.7億円・1.5万円・900円・32円・0.5円）"""
    if v >= 1e8:
        return f"{v / 1e8:.1f}億円"
    if v >= 1e4:
        return f"{v / 1e4:.1f}万円"
    if v >= 10:
        return f"{int(round(v)):,}円"
    return f"{v:.1f}円" if v >= 1 else "1円未満"


# ---------- 見本の1人 ----------
# 1投目が表・2投目が裏（1000→1500→900）、表52回で終わり（32円）、途中で一度1万円を超える
for S_SEED in range(1, 20000):
    _q = np.random.default_rng(10000 + S_SEED).integers(0, 2, F)
    _lg = math.log10(START) + np.cumsum(np.where(_q == 1, L_UP, L_DN))
    if _q[0] == 1 and _q[1] == 0 and _q.sum() == 52 and 4 < _lg.max() < 4.8 and _lg[:60].argmax() == _lg.argmax():
        break
S_SEQ = _q
S_LG = np.concatenate([[math.log10(START)], _lg])
S_PEAK = int(S_LG.argmax())

# ---------- 時間割 ----------
T_A0 = note.Intro.T_GO
FLIP = 0.7                                        # 1回のコインが回っている時間
T_F1 = T_A0 + 0.5                                 # 1投目（表）
T_F2 = T_F1 + 1.5                                 # 2投目（裏）
T_AVG = T_F2 + 1.4                                # 「平均すると ×1.05」
T_FAST = T_AVG + 2.8                              # 残り98回を早送り
FAST_DUR = 4.2
T_S_END = T_FAST + FAST_DUR
T_BANNER = T_S_END + 2.9                          # 「100回で 1000円 → 32円」を読む時間
T_M0 = T_BANNER + 2.2                             # 1万人モード
M_DUR = 9.0
T_M_END = T_M0 + M_DUR
T_REV = T_M_END + 0.6
T_P2 = T_REV + 3.0                                # 「真ん中の人は 5円」「1位は 4.7億円」
T_Q = T_P2 + 3.8                                  # 締め「平均は得なのに、なんで？」
DURATION = T_Q + 4.0


def s_steps(t):
    """見本の1人が何回投げ終わったか"""
    if t < T_F1 + FLIP:
        return 0
    if t < T_F2 + FLIP:
        return 1
    if t < T_FAST:
        return 2
    return min(F, 2 + int((F - 2) * clamp01((t - T_FAST) / FAST_DUR)))


def m_steps(t):
    """1万人モードで何回投げ終わったか（はじめはゆっくり）"""
    if t < T_M0:
        return 0
    return min(F, int(F * clamp01((t - T_M0) / M_DUR) ** 1.35 + 0.0001))


# ---------- 描画 ----------
# 金属のコイン（coin-10kai.py と同じ絵）
def _lin(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, col, al in stops:
        g.add_color_stop_rgba(o, *hexrgb(col)[:3], al)
    return g


def coin(ctx, x, y, r, heads, sx=1.0, a=1.0, lift=0.0, shadow=True):
    """金属のコイン。縁のギザギザ・盛り上がった縁・字の浮き彫り・光の反射。
    sx は横の縮み（回転中は細く、側面の厚みが見える）、lift は浮いている高さ（影が小さく薄くなる）"""
    if a < 1.0:
        ctx.push_group()
        coin(ctx, x, y, r, heads, sx, 1.0, lift, shadow)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        return
    light, base, dark, edge = METAL[bool(heads)]
    sx = max(0.04, sx)
    if shadow:                                          # 紙に落ちる影（高く浮くほど小さく薄い）
        k = 1 / (1 + lift / 110)
        ctx.save()
        ctx.translate(x + 7, y + r * 0.62)
        ctx.scale(max(sx, 0.35) * k, 0.28 * k)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, r * 1.1)
        g.add_color_stop_rgba(0, 0.12, 0.09, 0.05, 0.30 * k)
        g.add_color_stop_rgba(1, 0.12, 0.09, 0.05, 0.0)
        ctx.set_source(g)
        ctx.arc(0, 0, r * 1.1, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    ctx.save()
    ctx.translate(x, y - lift)
    ctx.scale(sx, 1)
    th = r * 0.14 * (1 - sx)                            # 側面の厚み（画面上の px）
    if th > 0.4:
        ctx.set_source(_lin(ctx, 0, -r, 0, r, [(0, dark, 1), (0.5, edge, 1), (1, dark, 1)]))
        ctx.arc(th / sx, 0, r, 0, 2 * math.pi)
        ctx.fill()
        ctx.rectangle(0, -r, th / sx, 2 * r)
        ctx.fill()
    # 縁（盛り上がり）
    ctx.set_source(_lin(ctx, -r, -r, r, r, [(0, light, 1), (0.45, base, 1), (1, dark, 1)]))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.fill()
    if sx > 0.45:                                       # 縁のギザギザ
        ctx.set_line_width(max(1.0, r * 0.018))
        ctx.set_source_rgba(*hexrgb(edge, 0.35))
        for i in range(72):
            ang = i * 2 * math.pi / 72
            ctx.move_to(r * 0.9 * math.cos(ang), r * 0.9 * math.sin(ang))
            ctx.line_to(r * 0.995 * math.cos(ang), r * 0.995 * math.sin(ang))
        ctx.stroke()
    # 地（少しへこんだ平らな面）
    ri = r * 0.82
    g = cairo.RadialGradient(-ri * 0.35, -ri * 0.4, ri * 0.05, 0, 0, ri * 1.05)
    g.add_color_stop_rgba(0, *hexrgb(light)[:3], 1)
    g.add_color_stop_rgba(0.55, *hexrgb(base)[:3], 1)
    g.add_color_stop_rgba(1, *hexrgb(dark)[:3], 1)
    ctx.set_source(g)
    ctx.arc(0, 0, ri, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(max(1.0, r * 0.035))            # 縁と地の段差（左上は影、右下は光）
    ctx.set_source(_lin(ctx, -ri, -ri, ri, ri, [(0, edge, 0.7), (1, light, 0.8)]))
    ctx.arc(0, 0, ri, 0, 2 * math.pi)
    ctx.stroke()
    if sx > 0.45:                                       # 点の輪
        ctx.set_source_rgba(*hexrgb(dark, 0.45))
        for i in range(40):
            ang = i * 2 * math.pi / 40
            ctx.arc(r * 0.71 * math.cos(ang), r * 0.71 * math.sin(ang), max(0.8, r * 0.018), 0, 2 * math.pi)
            ctx.fill()
    if sx > 0.6:                                        # 字の浮き彫り（右下に影、左上に光、本体は地より少し濃く）
        ch, size = ("表" if heads else "裏"), r * 0.74
        text(ctx, ch, r * 0.03, r * 0.05, size, edge, alpha=0.55)
        text(ctx, ch, -r * 0.025, -r * 0.02, size, light, alpha=0.9)
        text(ctx, ch, 0, 0.01 * r, size, dark)
    # 光の反射（左上の弧）
    ctx.set_line_width(r * 0.07)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(1, 1, 1, 0.45 * min(1, sx * 1.2))
    ctx.arc(0, 0, r * 0.9, math.pi * 1.08, math.pi * 1.42)
    ctx.stroke()
    ctx.restore()
    ctx.new_path()



class Chart:
    """持ち金のグラフ（横＝投げた回数、縦＝持ち金の対数目盛り）"""

    def __init__(self, x0, x1, y_bot, y_top, lo, hi, ticks):
        self.x0, self.x1, self.yb, self.yt, self.lo, self.hi, self.ticks = x0, x1, y_bot, y_top, lo, hi, ticks

    def x(self, s):
        return self.x0 + (self.x1 - self.x0) * s / F

    def y(self, lg):
        return self.yb - (self.yb - self.yt) * (np.clip(lg, self.lo, self.hi) - self.lo) / (self.hi - self.lo)

    def axes(self, ctx, a=1.0):
        ctx.set_line_width(2)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
        for lg, lab in self.ticks:
            y = self.y(lg)
            ctx.move_to(self.x0, y)
            ctx.line_to(self.x1, y)
            ctx.stroke()
            text(ctx, lab, self.x0 - 12, y, 30, PENCIL, align="right", bold=False, alpha=a)
        ys = self.y(math.log10(START))             # はじめの持ち金の線（赤の破線）
        ctx.set_source_rgba(*hexrgb(RED, 0.8 * a))
        ctx.set_line_width(3)
        ctx.set_dash([12, 9])
        ctx.move_to(self.x0, ys)
        ctx.line_to(self.x1, ys)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "1000円", self.x0 - 12, ys, 30, RED, align="right", alpha=a)
        pen = note.pen_line
        pen(ctx, self.x0, self.yb + 4, self.x1, self.yb + 2, PENCIL, seed=3, width=3, alpha=0.6 * a)


S_CHART = Chart(170, 880, 1245, 975, 0, 5, [(0, "1円"), (2, "100円"), (4, "1万円"), (5, "10万円")])
M_CHART = Chart(170, 880, 1250, 720, 0, 9, [(0, "1円"), (6, "100万円"), (9, "10億円")])


def draw_deco(ctx, t, a):
    """冒頭の右上: コインが回り続け、出た面で ×1.5 / ×0.6 が出る"""
    period = 1.6                                   # 倍率を読む時間（着地してから1秒）
    k = int(t / period)
    ph_t = t - k * period
    res = (0b1011001101 >> (k % 10)) & 1
    p = clamp01(ph_t / 0.6)
    phase = 3 * math.pi * (1 - ease_out(p))
    c = math.cos(phase)
    face = res if c >= 0 else 1 - res
    coin(ctx, 690, 480, 60, face, abs(c), a, lift=40 * math.sin(math.pi * p))
    if p >= 1:
        q = ease_out((ph_t - 0.6) / 0.15)
        sc = 1 + 0.25 * (1 - q)
        ctx.save()
        ctx.translate(865, 470)
        ctx.scale(sc, sc)
        text(ctx, "×1.5" if res else "×0.6", 0, 0, 72, HEAD_RIM if res else TAIL, alpha=a * q)
        ctx.restore()


INTRO = note.Intro(["表なら1.5倍、裏なら0.6倍を100回。", "得する人は何%？"], ["6割以上", "約半分", "2割以下"],
                   correct=2, msg="1万人で投げて確かめる", deco=draw_deco,
                   big=["表なら1.5倍、裏なら0.6倍。", "100回投げたら", "得する人は何%？"],
                   rule=None)


def draw_line(ctx, chart, lg, n, col, width, a=1.0):
    if n < 1:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ys = chart.y(lg[:n + 1])
    ctx.move_to(chart.x(0), ys[0])
    for s in range(1, n + 1):
        ctx.line_to(chart.x(s), ys[s])
    ctx.stroke()


def draw_sample(ctx, t, fade):
    text(ctx, "まず1人。持ち金1000円から", 540, 710, 36, PENCIL, bold=False, alpha=fade)
    n = s_steps(t)
    # コイン（1投目・2投目はゆっくり、早送り中は回したまま）
    if t < T_FAST:
        t0 = T_F1 if t < T_F2 else T_F2
        res = int(S_SEQ[0 if t < T_F2 else 1])
        p = clamp01((t - t0) / FLIP)
    else:
        i = max(0, n - 1)
        res = int(S_SEQ[i])
        p = 1.0 if n >= F else 0.5 + 0.5 * ((t - T_FAST) * 23 % 1)
    phase = 3 * math.pi * (1 - ease_out(p))
    c = math.cos(phase)
    face = res if c >= 0 else 1 - res
    coin(ctx, 300, 830, 70, face, abs(c), fade, lift=50 * math.sin(math.pi * p))
    money = 10 ** S_LG[n]                           # 早送り中に「万円」と「円」が入れ替わらないよう、円のまま出す
    text(ctx, f"{int(round(money)):,}円", 440, 830, 84, INK, align="left", alpha=fade)
    # 倍率のポップ（1・2投目）
    for k, t0 in ((0, T_F1), (1, T_F2)):
        age = t - (t0 + FLIP)
        if 0 <= age < 1.3 and t < T_FAST:
            q = ease_out(age / 0.2) * (1 - ease((age - 1.0) / 0.3))
            up = S_SEQ[k] == 1
            text(ctx, "表 ×1.5" if up else "裏 ×0.6", 300, 925, 42, HEAD_RIM if up else TAIL, alpha=fade * q)
    S_CHART.axes(ctx, fade)
    draw_line(ctx, S_CHART, S_LG, n, INK, 5, fade)
    if n:
        x, y = S_CHART.x(n), float(S_CHART.y(S_LG[n]))
        ctx.set_source_rgba(*hexrgb(RED, fade))
        ctx.arc(x, y, 8, 0, 2 * math.pi)
        ctx.fill()
    if n >= S_PEAK and t >= T_FAST:                 # 一番増えたところに印
        x, y = S_CHART.x(S_PEAK), float(S_CHART.y(S_LG[S_PEAK]))
        text(ctx, f"一時は {yen(10 ** S_LG[S_PEAK])}", x + 20, y - 28, 30, HEAD_RIM, align="left", alpha=fade)
    text(ctx, f"投げた回数 {n}/100", 540, 1300, 34, PENCIL, bold=False, alpha=fade)
    if T_AVG <= t < T_FAST + 0.3:
        a = ease_out((t - T_AVG) / 0.25) * (1 - ease((t - T_FAST) / 0.3)) * fade
        note.sticky(ctx, "表と裏は半々だから\n平均は1回 ×1.05（得！）", 540, 1120, 46, "mint", a=a, tilt=0.02)
    if t >= T_S_END:
        a = ease_out((t - T_S_END) / 0.25) * fade
        note.sticky(ctx, f"100回で 1000円 → {yen(10 ** S_LG[-1])}", 540, 1380, 54, "pink", fg=RED, a=a)


# 1万人は線を1本ずつ引くと網目になって濃さが見えないので、各回の「表が何回の人が何人いるか」を濃さで塗る
# （人が多いところほど濃い扇。はじめの持ち金より上は金、下は青）
_START_LG = math.log10(START)
CUMK = np.cumsum(FLIPS, axis=1, dtype=np.int16)
COUNTS = [None] + [np.bincount(CUMK[:, s - 1], minlength=F + 1) for s in range(1, F + 1)]
BAND = (L_UP - L_DN) / (M_CHART.hi - M_CHART.lo) * (M_CHART.yb - M_CHART.yt)   # となりの段の間（px）


def draw_fan(ctx, n, a=1.0):
    for step in range(1, n + 1):
        xa, xb = M_CHART.x(step - 1), M_CHART.x(step) + 0.6
        cnt = COUNTS[step]
        ks = np.flatnonzero(cnt)
        lg = _START_LG + ks * L_UP + (step - ks) * L_DN
        ys = M_CHART.y(lg)
        for k, lv, y in zip(ks, lg, ys):
            f = cnt[k] / N
            al = min(0.92, max(0.05, math.sqrt(f) * 2.4)) * a
            ctx.set_source_rgba(*hexrgb(GAIN_C if lv > _START_LG + 1e-9 else LOSS_C, al))
            ctx.rectangle(xa, y - BAND / 2, xb - xa, BAND)
            ctx.fill()


def name_tag(ctx, s, x, y, col, a):
    """線の先の名札。はじめは線の右、線が伸びたら左に（左右の端とボタン列にかからないように）"""
    if x < 420:
        text(ctx, s, x + 16, y, 30, col, align="left", alpha=a)
    else:
        text(ctx, s, x - 16, y, 30, col, align="right", alpha=a)


def draw_mass(ctx, t, dim=0.0):
    n = m_steps(t)
    M_CHART.axes(ctx)
    draw_fan(ctx, n, 1 - 0.3 * dim)
    draw_line(ctx, M_CHART, LG[TOP_I], n, HEAD_RIM, 3)   # 1位の人
    if n:
        x, y = M_CHART.x(n), float(M_CHART.y(LG[TOP_I, n]))
        name_tag(ctx, "1位の人", x, y - 30, HEAD_RIM, 1 - dim)
    draw_line(ctx, M_CHART, LG[MED_I], n, RED, 4)        # 真ん中の人
    if n:
        x, y = M_CHART.x(n), float(M_CHART.y(LG[MED_I, n]))
        ctx.set_source_rgba(*hexrgb(RED))
        ctx.arc(x, y, 7, 0, 2 * math.pi)
        ctx.fill()
        name_tag(ctx, "真ん中の人", x, y + 34, RED, 1 - dim)
    ahead = float((LG[:, n] > _START_LG).mean() * 100) if n else 0.0
    text(ctx, f"投げた回数 {n}/100", 540, 1305, 38, INK)
    text(ctx, f"1000円より多い人 {ahead:.1f}%", 540, 1360, 44, GAIN_C, alpha=1 if n else 0.4)
    note.legend(ctx, [(GAIN_C, "1000円より多い"), (LOSS_C, "少ない")], 1420, 30)   # 赤と金の線は線の先に名札


def body(ctx, t):
    if t < T_A0:
        return
    if t < T_BANNER:
        fo = ease_out((t - T_A0) / 0.25) * (1 - ease((t - (T_BANNER - 0.25)) / 0.25))
        draw_sample(ctx, t, fo)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万人で投げてみる", 540, 950, a=a, t_rel=t - T_BANNER)
    else:
        q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
        draw_mass(ctx, t, dim=clamp01((t - T_M_END) / 0.4))
        if T_M_END <= t:
            a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - q)
            note.sticky(ctx, f"得したのは 1万人中\n{int(round(SIM_P * N)):,}人（{SIM_P * 100:.1f}%）", 540, 880, 62,
                        "yellow", a=a)
        if t >= T_P2 and q < 1:
            b = ease_out((t - T_P2) / 0.3) * (1 - q)
            note.sticky(ctx, f"真ん中の人は 1000円 → {yen(SIM_MED)}", 540, 1060, 46, "pink", fg=RED, a=b, tilt=0.02)
            c2 = ease_out((t - T_P2 - 1.2) / 0.3) * (1 - q)
            note.sticky(ctx, f"1位の人は {yen(TOP_YEN)}", 540, 1175, 46, "mint", a=c2, tilt=-0.02)
        if q > 0:
            note.sticky(ctx, "平均は1回 ×1.05で得なのに\nなんで ほとんどの人が損するの？", 540, 900, 50, "yellow", a=q,
                        tilt=-0.02)
            r = ease_out((t - T_Q - 1.2) / 0.3)
            note.sticky(ctx, "答えは概要欄に", 540, 1090, 50, "pink", fg=RED, a=r, tilt=0.025)


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

def clink(freq=2600, dur=0.18):
    """コインが着地するチャリン"""
    t = _t(dur)
    return (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 1.52 * t)) * np.exp(-t * 28)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    k = 0
    while k * 1.6 + 0.6 < note.Intro.T_MOVE:                  # 冒頭の右上のコイン
        mx.add(k * 1.6 + 0.6, clink(2400 + 200 * (k % 2)), 0.18)
        k += 1
    for t0, up in ((T_F1, True), (T_F2, False)):
        mx.add(t0, whoosh(0.4), 0.15)
        mx.add(t0 + FLIP, clink(), 0.5)
        mx.add(t0 + FLIP + 0.02, blip(1046.5 if up else 392.0, 0.18), 0.45)
    mx.add(T_AVG, bell(880.0, 1.0), 0.4)
    for j in range(2, F):                                      # 早送りの98回
        tt = T_FAST + FAST_DUR * (j - 2) / (F - 2)
        mx.add(tt, tick(3000 if S_SEQ[j] else 1800), 0.25)
    mx.add(T_S_END, bell(523.3), 0.5)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    for s in range(1, F + 1):
        tt = T_M0 + M_DUR * (s / F) ** (1 / 1.35)
        mx.add(tt, tick(2200 + 400 * (s % 3)), 0.12)
    mx.add(T_M_END, shimmer(300, 0.5), 0.8)
    mx.add(T_M_END + 0.2, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([261.6, 311.1, 392.0], 1.6), 0.5)
    mx.add(T_P2, bell(659.3), 0.45)
    mx.add(T_P2 + 1.2, bell(1046.5), 0.5)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 得した人={SIM_P * N:.0f}人（{SIM_P:.4f}） 真ん中={SIM_MED:.2f}円 1位={TOP_YEN:,.0f}円（表{KS[TOP_I]}回） "
          f"見本 seed={S_SEED} 最高={10 ** S_LG.max():,.0f}円（{S_PEAK}回目） 最後={10 ** S_LG[-1]:.1f}円 長さ={DURATION:.1f}秒")
    check_answers([
        ("得した人の割合", SIM_P, EXACT_P, 0.005),
        ("真ん中の人の持ち金（円）", SIM_MED, EXACT_MED, 0.01),
        ("見本の2投目（表→裏で900円）", 10 ** S_LG[2], START * UP * DOWN, 1e-6),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 1.4, 3.2, 5.0, 7.95, T_F1 + 1.0, T_F2 + 1.0, T_AVG + 1.0, T_FAST + 2.0,
                      T_S_END + 1.0, T_BANNER + 0.6, T_M0 + 3.0, T_M0 + 7.0, T_M_END + 1.0, T_P2 + 2.0,
                      T_Q + 2.0, DURATION - 0.25], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
