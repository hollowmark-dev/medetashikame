"""0.001度ずつずらした2段の振り子1万本。10秒後どうなる？

物理: 同じ長さ・同じ重さの棒2本をつないだ二重振り子（摩擦なし、点の重り）。
標準の運動方程式を RK4（刻み 1/600 秒）で、1万本ぶん numpy でまとめて積分する。
はじめの角度は、2本の棒とも 135度（真下から）。1本ごとに 0.001度×i だけ全体を傾ける（i = 0〜9999）。

直感の外れ: 「0.001度しか違わないんだから、そろったまま／少しずれるだけ」（A・B）。正解はバラバラ（C、カオス）。
見本: 0.001度ちがいの2本（青と赤のペン）→ 1万本（虹色）→ 10秒後にバラバラ。
追い打ち: 0.000001度ずつ（1000分の1）にしても、ほどけるのが少し遅れるだけ。
締め: 「なんで、ほんの少しの違いがこんなに大きくなるの？」→ 答えは概要欄。

照合（check_answers）:
- 全振り子のエネルギー保存（相対誤差の最大値）
- 小さく振らせたときの周期が、運動方程式の線形化から出る固有振動（ω² = (2−√2) g/L）と一致すること
- 刻みを半分にしても「ほどけた時刻」が変わらないこと（1000本の間引きで確かめる）
- 10秒後の先端の広がりが、腕の長さの半分を超えていること（＝バラバラ）

2026-10-02 スワイプ対策で冒頭を作り直した（案1・2・4。時間割のところに詳細）。
2026-10-02 紺の画面（旧型）からノートの見た目に作り直した。旧版（紺の画面）は out/furiko-10000/furiko-10000.dark.py。
1万本は紙の上に色ペンで描いたように、重なるほど濃くなる（足し算で光らせるのは紺の画面のときの描き方）。
"""
import colorsys
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.parts import loop_back, stills
from engine.core import (W, H, FPS, SR, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, _t)

note.use()
note.DATE = "10.3"                                # 日付欄（公開予定日）

SLUG = "furiko-10000"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
G, L = 9.81, 1.0
N = 10000
TH0 = 135.0                       # はじめの角度（度）
STEP_A = 0.001                    # 1本ごとのずれ（度）
STEP_B = 0.000001                 # 追い打ち
DT = 1 / 600                      # RK4 の刻み（秒）
SPD_A, SPD_B = 1.5, 2.5           # 動画1秒あたりの振り子の秒数
T_PHYS = 10.0
THRESH = 0.5                      # 「バラバラ」: 先端の広がり（標準偏差）が腕の長さの半分を超えた

BLUE_PEN = "#2f62c9"
PAIR = (BLUE_PEN, RED)


# ---------- 物理 ----------

def deriv(s):
    """二重振り子（m1=m2, l1=l2=L）の運動方程式。s = [θ1, θ2, ω1, ω2]"""
    t1, t2, w1, w2 = s
    d = t1 - t2
    den = 3 - np.cos(2 * d)
    a1 = (-3 * G * np.sin(t1) - G * np.sin(t1 - 2 * t2)
          - 2 * np.sin(d) * (w2 * w2 * L + w1 * w1 * L * np.cos(d))) / (L * den)
    a2 = (2 * np.sin(d) * (2 * w1 * w1 * L + 2 * G * np.cos(t1)
                           + w2 * w2 * L * np.cos(d))) / (L * den)
    return np.array([w1, w2, a1, a2])


def energy(s):
    """1本あたりの力学的エネルギー（m=1、いちばん低い位置を0とする）"""
    t1, t2, w1, w2 = s
    T = 0.5 * L * L * w1 ** 2 + 0.5 * (L * L * w1 ** 2 + L * L * w2 ** 2
                                        + 2 * L * L * w1 * w2 * np.cos(t1 - t2))
    V = -2 * G * L * np.cos(t1) - G * L * np.cos(t2) + 3 * G * L
    return T + V


def integrate(s, t_end, out_step, dt=DT):
    """RK4。out_step 秒ごとに状態を保存。エネルギーの相対誤差の最大値も返す"""
    sub = int(round(out_step / dt))
    h = out_step / sub
    E0 = energy(s)
    frames = [s.astype(np.float32)]
    emax = 0.0
    for _ in range(int(round(t_end / out_step))):
        for _ in range(sub):
            k1 = deriv(s)
            k2 = deriv(s + h / 2 * k1)
            k3 = deriv(s + h / 2 * k2)
            k4 = deriv(s + h * k3)
            s = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        frames.append(s.astype(np.float32))
        emax = max(emax, float(np.max(np.abs(energy(s) - E0) / E0)))
    return np.array(frames), emax


def start_state(step_deg, idx):
    off = np.radians(TH0 + step_deg * idx)
    return np.array([off, off, np.zeros_like(off), np.zeros_like(off)], dtype=np.float64)


def tips(fr):
    """fr: (4, n) → 先端の位置 (x, y)（腕の長さ単位、y は下向き）"""
    t1, t2 = fr[0].astype(np.float64), fr[1].astype(np.float64)
    return L * np.sin(t1) + L * np.sin(t2), L * np.cos(t1) + L * np.cos(t2)


def spread(frames):
    out = []
    for fr in frames:
        x, y = tips(fr)
        out.append(math.sqrt(x.var() + y.var()))
    return np.array(out)


def spread_time(sp, step):
    """広がりが THRESH を初めて超えた時刻（コマの間は直線で補う）"""
    i = int(np.argmax(sp > THRESH))
    if sp[i] <= THRESH:
        return float("nan")
    return (i - 1 + (THRESH - sp[i - 1]) / (sp[i] - sp[i - 1])) * step


def normal_mode_period():
    """小さく振らせた遅いほうの固有振動の周期を、積分で測る"""
    a = math.radians(0.5)
    s = np.array([[a], [math.sqrt(2) * a], [0.0], [0.0]])
    fr, _ = integrate(s, 12.0, 1 / 600)
    th = fr[:, 0, 0].astype(np.float64)
    tt = np.arange(len(th)) / 600
    z = np.where((th[:-1] > 0) & (th[1:] <= 0))[0]           # 下向きのゼロ交差
    zc = tt[z] + (th[z] / (th[z] - th[z + 1])) / 600
    return float(np.mean(np.diff(zc)))


def simulate():
    """1万本×2通り。重いので out/<slug>/cache.npz に取っておく"""
    key = f"{G},{L},{N},{TH0},{STEP_A},{STEP_B},{DT},{SPD_A},{SPD_B},{T_PHYS}"
    cache = OUT / "cache.npz"
    if cache.exists():
        z = np.load(cache)
        if str(z["key"]) == key:
            return z["A"], z["B"], float(z["eA"]), float(z["eB"])
    idx = np.arange(N)
    A, eA = integrate(start_state(STEP_A, idx), T_PHYS, SPD_A / FPS)
    B, eB = integrate(start_state(STEP_B, idx), T_PHYS, SPD_B / FPS)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(cache, key=key, A=A, B=B, eA=eA, eB=eB)
    return A, B, eA, eB


def half_step_check():
    """刻みを半分にしても、ほどけた時刻が同じか（1000本に間引いて確かめる）"""
    idx = np.arange(0, N, 10)
    res = []
    for step_deg, spd in ((STEP_A, SPD_A), (STEP_B, SPD_B)):
        s0 = start_state(step_deg, idx)
        f1, _ = integrate(s0, T_PHYS, spd / FPS, DT)
        f2, _ = integrate(s0, T_PHYS, spd / FPS, DT / 2)
        res.append((spread_time(spread(f1), spd / FPS), spread_time(spread(f2), spd / FPS)))
    return res


A, B, E_A, E_B = simulate()
SP_A, SP_B = spread(A), spread(B)
TS_A = spread_time(SP_A, SPD_A / FPS)          # 0.001度ずつ: ほどけた時刻
TS_B = spread_time(SP_B, SPD_B / FPS)          # 0.000001度ずつ
X_PAIR, Y_PAIR = tips(A[:, :, :2].transpose(1, 0, 2).reshape(4, -1))
X_PAIR = X_PAIR.reshape(-1, 2)
Y_PAIR = Y_PAIR.reshape(-1, 2)
D_PAIR = np.hypot(X_PAIR[:, 0] - X_PAIR[:, 1], Y_PAIR[:, 0] - Y_PAIR[:, 1])
_ip = int(np.argmax(D_PAIR > 0.3))
TP_PAIR = _ip * SPD_A / FPS                    # 見本の2本が目に見えてずれた時刻


def r1(x):
    return math.floor(x * 10 + 0.5) / 10


# ---------- 時間割 ----------
# 2026-10-02 スワイプ対策（ユーザーと Fable の案1・2・4、ゾンビの回と同じ形）:
#   1. 0秒目から画面の上半分で、見本の2本（青と赤）が大きく振れる（右上の小物ではなく主役の大きさで）
#   2. 問いは大きい字の1行「振り子1万本、10秒後は？」。前提は0.8秒後に小さく足す
#   4. 見本はカウントダウンと同時に進み、5・4・3・2・1・0 の間に2本が別々の動きになる
# 見本の2本は、はじめゆっくり（重なって1本に見えている間を読ませる）、ずれ始める前に1.5倍速へ
PAIR_SLOW, PAIR_T_SLOW, PAIR_RAMP = 0.8, 3.0, 1.0


def phys_pair(t):
    """見本: 動画の時刻 → 振り子の時刻（配列も可）。0秒目に離す"""
    t = np.clip(np.asarray(t, dtype=float), 0, None)
    d = np.clip(t - PAIR_T_SLOW, 0, None)
    dr = np.minimum(d, PAIR_RAMP)
    tau = (PAIR_SLOW * np.minimum(t, PAIR_T_SLOW)
           + PAIR_SLOW * dr + (SPD_A - PAIR_SLOW) * dr * dr / (2 * PAIR_RAMP)
           + SPD_A * (d - dr))
    return np.minimum(T_PHYS, tau)


_TG = np.arange(0, 30, 0.001)
T_PAIR_SEEN = float(np.interp(TP_PAIR, phys_pair(_TG), _TG))   # 見本の2本がずれた（動画の時刻）
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = max(T_PAIR_SEEN + 3.0, T_CD[-1] + 0.6)     # 「6.4秒で別々の動きに」を読んでから上へ
T_BANNER = T_GO
T_M0 = T_BANNER + 2.1                          # 1万本
T_M10 = T_M0 + T_PHYS / SPD_A                  # 10秒後
T_ANS = T_M10 + 0.1
T_P2 = T_ANS + 3.4                             # 追い打ち「0.000001度ずつなら？」
T_P2_RUN = T_P2 + 2.0
T_P2_10 = T_P2_RUN + T_PHYS / SPD_B
T_Q = T_P2_10 + 3.4                            # 締め「なんで？」（答えは概要欄）
DURATION = T_Q + 4.0


def phys_A(t):
    """動画の時刻 → 1万本（A）の振り子の時刻"""
    return min(T_PHYS, max(0.0, (t - T_M0) * SPD_A))


def phys_B(t):
    return min(T_PHYS, max(0.0, (t - T_P2_RUN) * SPD_B))


def frame_at(frames, tau, spd):
    """振り子の時刻 tau の状態（保存したコマの間は直線で補う）"""
    f = tau / (spd / FPS)
    i = min(int(f), len(frames) - 2)
    a = f - i
    return frames[i] * (1 - a) + frames[i + 1] * a


# ---------- 描画 ----------
PX, PY = 540, 1010              # 支点（本体の座標。紙の中心にそろえる）
ARM = 175                       # 腕の長さ（px）。いちばん上まで振れても y=660
RY0, RY1 = 640, 1376            # 1万本を塗る範囲（高さは4の倍数）
KS = 96                         # 腕1本あたりの点の数

_hues = np.arange(N) / N * 0.83
RAINBOW = np.array([colorsys.hsv_to_rgb(h, 0.85, 0.82) for h in _hues], np.float32)
COL_REP = [np.repeat(RAINBOW[:, c], 2 * KS + 6) for c in range(3)]
_s = np.linspace(0, 1, KS, dtype=np.float32)


def raster(fr, gain=0.22):
    """1万本の振り子を、色ペンの点を重ねて塗る（紙の上なので、重なるほど濃くなる）"""
    t1, t2 = fr[0], fr[1]
    jx = PX + ARM * np.sin(t1)
    jy = PY + ARM * np.cos(t1)
    tx = jx + ARM * np.sin(t2)
    ty = jy + ARM * np.cos(t2)
    xs = np.concatenate([PX + (jx - PX)[:, None] * _s, jx[:, None] + (tx - jx)[:, None] * _s,
                         np.repeat(tx[:, None], 6, 1)], axis=1)
    ys = np.concatenate([PY + (jy - PY)[:, None] * _s, jy[:, None] + (ty - jy)[:, None] * _s,
                         np.repeat(ty[:, None], 6, 1)], axis=1)
    jit = np.array([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1]], np.float32)   # 先端の重りは少し太く
    xs[:, -6:] += jit[:, 0]
    ys[:, -6:] += jit[:, 1]
    xi = xs.astype(np.int32).ravel()
    yi = ys.astype(np.int32).ravel() - RY0
    hh = RY1 - RY0
    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < hh)
    idx = yi[ok] * W + xi[ok]
    wts = np.ones(2 * KS + 6, np.float32)
    wts[-6:] = 3.0
    wrep = np.tile(wts, N)[ok]
    cnt = np.bincount(idx, weights=wrep, minlength=hh * W).reshape(hh, W).astype(np.float32)
    # 色は平均すると灰色に濁るので、1マスごとに「そこを通った誰か1本」の色を出す（並びをかき混ぜてから上書き）
    order = np.random.default_rng(0).permutation(len(idx))
    col = np.zeros((hh * W, 3), np.float32)
    for c in range(3):
        col[idx[order], c] = COL_REP[c][ok][order]
    col = col.reshape(hh, W, 3)
    lum = 1 - np.exp(-gain * cnt)
    col = col * (1 - 0.35 * lum[:, :, None])                  # 濃いところは少し暗く
    out = np.empty((hh, W, 4), np.uint8)
    for c, k in ((2, 0), (1, 1), (0, 2)):                     # 乗算済みの BGRA
        out[:, :, k] = (col[:, :, c] * lum * 255).astype(np.uint8)
    out[:, :, 3] = (lum * 255).astype(np.uint8)
    out = np.ascontiguousarray(out)
    surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, W, hh, W * 4)
    return surf, out


def pivot(ctx, x=PX, y=PY, r=9):
    fill(ctx, INK)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def pendulum(ctx, x0, y0, arm, t1, t2, col, width, r1_, r2_, a=1.0):
    jx, jy = x0 + arm * math.sin(t1), y0 + arm * math.cos(t1)
    tx, ty = jx + arm * math.sin(t2), jy + arm * math.cos(t2)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(jx, jy)
    ctx.line_to(tx, ty)
    ctx.stroke()
    for (bx, by, r) in ((jx, jy, r1_), (tx, ty, r2_)):
        ctx.arc(bx, by, r, 0, 2 * math.pi)
        ctx.fill()
    return tx, ty


def trail(ctx, x0, y0, arm, xs, ys, col, w0, w1, a=1.0):
    """先端の軌跡（古いほど薄く細く）"""
    n = len(xs)
    c = hexrgb(col)
    for k in range(1, n):
        q = k / n
        ctx.set_source_rgba(c[0], c[1], c[2], 0.45 * q * a)
        ctx.set_line_width(w0 + (w1 - w0) * q)
        ctx.move_to(x0 + arm * xs[k - 1], y0 + arm * ys[k - 1])
        ctx.line_to(x0 + arm * xs[k], y0 + arm * ys[k])
        ctx.stroke()


# 冒頭の見本（画面の座標。紙の中心 x≈580 にそろえる）
QX, QY, QARM = 575, 648, 118                     # 支点と腕の長さ。振れても y=412〜884


def draw_pair_top(ctx, t, a):
    """0秒目から: 0.001度ちがいの2本（青と赤）。重なっているあいだは1本に見える（乗算で重ねる）"""
    if a <= 0:
        return
    tau = float(phys_pair(t))
    f = tau / (SPD_A / FPS)
    ctx.push_group()
    ctx.set_operator(cairo.OPERATOR_MULTIPLY)
    n_tr = int(1.2 / (SPD_A / FPS))
    i0 = max(0, int(f) - n_tr)
    for j in (0, 1):
        trail(ctx, QX, QY, QARM, X_PAIR[i0:int(f) + 1, j], Y_PAIR[i0:int(f) + 1, j], PAIR[j], 3, 8)
    for j in (0, 1):
        fr = frame_at(A[:, :, j], tau, SPD_A)
        pendulum(ctx, QX, QY, QARM, float(fr[0]), float(fr[1]), PAIR[j], 12, 17, 24, a=0.85)
    ctx.set_operator(cairo.OPERATOR_OVER)
    pivot(ctx, QX, QY, 8)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    la = a * (1 - ease_out((t - T_PAIR_SEEN) / 0.25)) if t >= T_PAIR_SEEN else a   # 札が出たら横の字は消す
    text(ctx, "青と赤は", 145, 455, 30, PENCIL, align="left", bold=False, alpha=la)
    text(ctx, "0.001度だけ", 145, 500, 30, PENCIL, align="left", bold=False, alpha=la)
    text(ctx, "違う2本", 145, 545, 30, PENCIL, align="left", bold=False, alpha=la)
    text(ctx, f"{tau:.1f}秒後", 905, 470, 42, INK, alpha=la)
    if t >= T_PAIR_SEEN:
        b = ease_out((t - T_PAIR_SEEN) / 0.25) * a
        note.sticky(ctx, f"{r1(TP_PAIR):.1f}秒で 別々の動きに", 575, 470, 48, "pink", fg=RED, a=b)


class FIntro(note.Intro):
    """この回だけの冒頭。絵が主役で、問いは大きい1行。カウントダウンの間に見本が進む"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL                              # 音（ベル）を前提の行に合わせる
    T_CD = T_CD
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_pair_top(ctx, t, a)
        w = core.text_width(BIG_Q, 72)
        text(ctx, BIG_Q, 570, 945, 72, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 1000, 570 + w / 2 + 6, 994, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 1060, 34, INK, bold=False, alpha=a1)
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


BIG_Q = "振り子1万本、10秒後は？"
DETAIL = "2段の振り子を 0.001度ずつずらして離す"
INTRO = FIntro(["0.001度ずつずらした2段の振り子1万本。", "10秒後はどうなる？"],
               ["そろったまま", "少しずれる", "バラバラ"], correct=2, msg="", rule=None)


def draw_many(ctx, frames, tau, spd, label, fade=1.0):
    fr = frame_at(frames, tau, spd)
    surf, _keep = raster(fr)
    ctx.set_source_surface(surf, 0, RY0)
    ctx.paint_with_alpha(fade)
    pivot(ctx)
    if label:
        text(ctx, label, 540, 690, 32, PENCIL, bold=False, alpha=fade)
    text(ctx, f"{tau:.1f}秒後", 540, 1415, 50, INK, alpha=fade)
    return _keep


def body(ctx, t):
    if t < T_BANNER:
        return
    if t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万本でやってみる", 540, 950, a=a, t_rel=t - T_BANNER)
    elif t < T_P2:
        tau = phys_A(t)
        draw_many(ctx, A, tau, SPD_A, "1本ごとに0.001度ずつ・色も少しずつ")
        if tau >= TS_A and t < T_ANS:
            a = ease_out((tau - TS_A) / 0.4) * (1 - ease((t - T_ANS + 0.2) / 0.2))
            note.sticky(ctx, f"{r1(TS_A):.1f}秒でほどけた", 540, 790, 52, "yellow", a=a)
        if t >= T_ANS:
            a = ease_out((t - T_ANS - 0.2) / 0.3) * (1 - ease((t - T_P2 + 0.3) / 0.3))
            note.sticky(ctx, "10秒後、1万本がバラバラ", 540, 760, 56, "mint", a=a)
    elif t < T_P2_RUN:
        tau = phys_A(T_P2 - 1e-3)
        draw_many(ctx, A, tau, SPD_A, "", fade=0.25)
        a = ease_out((t - T_P2) / 0.25)
        note.banner(ctx, "0.000001度ずつなら？", 540, 950, a=a, t_rel=t - T_P2, size=64)
    else:
        q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
        tau = phys_B(t)
        draw_many(ctx, B, tau, SPD_B, "1本ごとに0.000001度ずつ（1000分の1）", fade=1 - 0.6 * q)
        if tau >= TS_B and t < T_P2_10:
            a = ease_out((tau - TS_B) / 0.4)
            note.sticky(ctx, f"{r1(TS_B):.1f}秒でほどけた", 540, 790, 52, "yellow", a=a)
        if t >= T_P2_10 and q < 1:
            a = ease_out((t - T_P2_10 - 0.1) / 0.3) * (1 - q)
            note.sticky(ctx, f"ずれを1000分の1にしても\n{r1(r1(TS_B) - r1(TS_A)):.1f}秒 遅れるだけ", 540, 900, 56,
                        "pink", fg=RED, a=a)
        if q > 0:
            # 「だから何？」で終わらないよう、理由は問いかけにして、答えは概要欄に書く
            note.sticky(ctx, "でも、なんで ほんの少しの違いが\nこんなに大きくなるの？", 540, 880, 50, "yellow", a=q,
                        tilt=-0.02)
            r = ease_out((t - T_Q - 1.2) / 0.3)
            note.sticky(ctx, "答えは概要欄に", 540, 1070, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_ANS)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def tip_speed(frames):
    """先端の速さ (コマ, 本)"""
    t1, t2, w1, w2 = [frames[:, k].astype(np.float64) for k in range(4)]
    vx = L * (w1 * np.cos(t1) + w2 * np.cos(t2))
    vy = -L * (w1 * np.sin(t1) + w2 * np.sin(t2))
    return np.hypot(vx, vy)


def voices(mx, frames, spd, t_start, t_end, cols, vol, fade_out=0.4, seed=0, tau_of=None):
    """振り子1本ごとに1つの声。先端が速いほど高い音。重なっていれば1つの音に聞こえ、
    ほどけると和音→ざわめきに変わる。tau_of は「動画の時刻 → 振り子の時刻」（速さが変わる見本用）"""
    v = tip_speed(frames[:, :, cols])
    vmax = float(np.percentile(tip_speed(frames[:, :, ::50]), 99))
    n = int((t_end - t_start + fade_out) * SR)
    tv = np.arange(n) / SR
    tau = np.minimum(T_PHYS, tv * spd) if tau_of is None else tau_of(t_start + tv)
    fpos = tau / (spd / FPS)
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for j in range(len(cols)):
        vv = np.interp(fpos, np.arange(len(frames)), v[:, j]) / vmax
        f = 170 * 2 ** (2.3 * np.clip(vv, 0, 1.2))
        ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 2 * np.pi)
        amp = 0.35 + 0.65 * np.clip(vv, 0, 1)
        out += (np.sin(ph) + 0.25 * np.sin(2 * ph)) * amp
    out /= math.sqrt(len(cols))
    env = np.minimum(1, tv / 0.02) * np.clip((t_end - t_start + fade_out - tv) / fade_out, 0, 1)
    mx.add(t_start, out * env, vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(98.0, 146.8, 196.0, 246.9)), 1.0, bgm=True)
    INTRO.audio(mx)
    voices(mx, A, SPD_A, 0.0, T_GO, [0, 1], 0.22, tau_of=phys_pair)
    mx.add(T_PAIR_SEEN, bell(880, 1.2), 0.45)
    mx.add(T_BANNER, riser(0.9), 0.5)
    many = list(range(0, N, N // 40))
    voices(mx, A, SPD_A, T_M0, T_M10, many, 0.3, seed=1)
    beat(mx, T_M0, T_M10, bpm=128, vol=0.5, accel=True)
    mx.add(T_M0 + TS_A / SPD_A, thump(), 0.6)
    mx.add(T_ANS, thump(), 0.8)
    mx.add(T_ANS, bell(784, 1.6), 0.6)
    mx.add(T_P2, riser(0.8), 0.45)
    voices(mx, B, SPD_B, T_P2_RUN, T_P2_10, many, 0.3, seed=2)
    beat(mx, T_P2_RUN, T_P2_10, bpm=150, vol=0.45)
    mx.add(T_P2_RUN + TS_B / SPD_B, thump(), 0.6)
    mx.add(T_P2_10 + 0.1, thump(), 0.8)
    mx.add(T_P2_10 + 0.1, chord([196.0, 246.9, 293.7], 1.8), 0.6)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"見本の2本がずれた {TP_PAIR:.2f}秒 / 1万本がほどけた A {TS_A:.3f}秒 B {TS_B:.3f}秒"
          f" / 長さ={DURATION:.1f}秒")
    period = normal_mode_period()
    period_th = 2 * math.pi / math.sqrt((2 - math.sqrt(2)) * G / L)
    (a1, a2), (b1, b2) = half_step_check()
    print(f"  エネルギーの最大相対誤差: 0.001度 {E_A:.1e} / 0.000001度 {E_B:.1e}")
    print(f"  刻み半分: A {a1:.3f}→{a2:.3f}秒  B {b1:.3f}→{b2:.3f}秒 / 10秒後の広がり A {SP_A[-1]:.2f} B {SP_B[-1]:.2f}")
    check_answers([
        ("エネルギー保存 最大相対誤差（0.001度・1万本）", E_A, 0.0, 1e-6),
        ("エネルギー保存 最大相対誤差（0.000001度・1万本）", E_B, 0.0, 1e-6),
        ("小さく振らせた周期（秒） vs 線形化の固有振動", period, period_th, 0.002),
        ("刻み半分でも ほどけた時刻（0.001度）", a2, a1, 0.05),
        ("刻み半分でも ほどけた時刻（0.000001度）", b2, b1, 0.05),
        ("画面の「ほどけた」0.001度（1万本 vs 1000本間引き, 0.1秒に丸め）", r1(TS_A), r1(a1), 0.1),
        ("10秒後の先端の広がりが腕の半分を超える（0.001度）", float(SP_A[-1] > THRESH), 1.0, 0.0),
        ("10秒後の先端の広がりが腕の半分を超える（0.000001度）", float(SP_B[-1] > THRESH), 1.0, 0.0),
        ("0秒の先端の広がりは腕の半分より小さい（0.001度）", float(SP_A[0] < THRESH), 1.0, 0.0),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 0.9, 1.6, 2.2, 3.2, 4.8, 6.9, T_PAIR_SEEN + 0.6, 7.9,
                      T_BANNER + 0.6, T_M0 + 1.5, T_M0 + 3.5, T_ANS + 1.0, T_P2 + 0.8, T_P2_RUN + 2.5,
                      T_P2_10 + 1.5, T_Q + 2.0, DURATION - 0.25], OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
