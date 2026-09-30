"""床の線に針を1万本落とす。線に重なるのは何本？（ビュフォンの針）

針の長さ＝線の間かく。針の中心は線と線の間のどこでも同じくらい、向きもでたらめ。
線に重なる確率は 2/π ≈ 63.7%（B 約6400本）。直感の外れは「重なるか、重ならないかだから半分」（A 約5000本）。
2026-09-29 ユーザー指摘で言葉を「かかる」→「重なる」に。円周率は「3.1415…じゃない」と突っ込まれないよう、
見積もりを「3.141…」まで出し、本物の 3.14159… と並べて「ほぼ同じ」と言う（1万本でぴったりにはならないので、そう言わない）。
→ 追い打ち: 落とした本数×2 ÷ 重なった本数 ＝ 3.141…。針を落とすだけで円周率が出てくる。

照合: 重なった割合を 2/π と、そこから出した円周率を π と照べる。
見本の8本も、1万本と同じ乱数から取り出して同じ判定をする（絵と判定が食い違わないよう、線との交わりは絵の座標で決める）。

2026-09-29 ユーザーが Fable との案出しの中から選んだ題材（「3番おもしろそう」）。ノートの罫線をそのまま床の線に使う。
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
from engine.parts import loop_back, pct, stills

note.use()
note.DATE = "9.30"                                # 日付欄（公開予定日）

SLUG = "hari-10000"
N = 10000
LINE_C = "#6f93c4"                                # 床の線（罫線より濃い青）
NEEDLE_C = "#5b6475"                              # かからなかった針（銀）
EXACT_P = 2 / math.pi

# ---------- 1万本 ----------
# 1万本モードの床: x は BX0〜BX1、線は BY0 から D おきに K+1 本
BX0, BX1, BY0, D, K = 100, 940, 700, 50, 10     # 2026-09-29 iPhone 対応で上を空けたぶん、床を低く（線11本）
L = D                                             # 針の長さ＝線の間かく


def drop(seed):
    rng = np.random.default_rng(seed)
    cx = rng.uniform(BX0 + L / 2, BX1 - L / 2, N)
    cy = rng.uniform(BY0, BY0 + K * D, N)
    th = rng.uniform(0, math.pi, N)
    dy = L / 2 * np.sin(th)
    y1, y2 = cy - dy, cy + dy
    # 線 BY0 + k*D にかかる ⇔ y1〜y2 の間に線がある（絵の座標のまま判定する）
    cross = np.floor((y2 - BY0) / D) > np.floor((y1 - BY0) / D)
    return cx, cy, th, cross


def pi_est(c):
    return 2 * N / c


# 乱数の種: 表示する%（整数）と円周率（小数2桁）が理論値の四捨五入と一致するものを選ぶ。統計は1万本全部から
for SEED in range(1, 20000):
    CX, CY, TH, CROSS = drop(SEED)
    C = int(CROSS.sum())
    # 見積もりが小数3桁まで本物と同じ（3.141…）になる種を選ぶ。20000/C の小数3桁の切り捨てが 3.141 になるのは C=6366〜6367
    if pct(C / N) == pct(EXACT_P) and math.floor(pi_est(C) * 1000) == math.floor(math.pi * 1000):
        break
SIM_P, SIM_PI = C / N, pi_est(C)

# ---------- 見本（大きな床に8本） ----------
SB0, SB1, SY0, SD, SK = 140, 900, 740, 150, 3    # 見本の床: 線は4本、間かく150px
SL = SD
S_N = 8
_srng = np.random.default_rng(SEED + 1000)
S_CX = _srng.uniform(SB0 + SL / 2, SB1 - SL / 2, S_N)
S_CY = _srng.uniform(SY0, SY0 + SK * SD, S_N)
S_TH = _srng.uniform(0, math.pi, S_N)
_sy1 = S_CY - SL / 2 * np.sin(S_TH)
_sy2 = S_CY + SL / 2 * np.sin(S_TH)
S_CROSS = np.floor((_sy2 - SY0) / SD) > np.floor((_sy1 - SY0) / SD)

# ---------- 時間割 ----------
T_A0 = note.Intro.T_GO                            # 冒頭の問題画面（約8秒）のあと
FALL = 0.4                                        # 1本が落ちてくる時間
S_TIMES = [T_A0 + 0.3 + i * 1.0 for i in range(4)] + [T_A0 + 4.3 + i * 0.55 for i in range(4)]
T_S_END = S_TIMES[-1] + FALL + 0.3
T_BANNER = T_S_END + 2.7                          # 「8本中 □本が重なった」を読む時間
T_M0 = T_BANNER + 2.4                             # 1万本モード
M_DUR = 7.0
T_M_END = T_M0 + M_DUR
T_REV = T_M_END + 0.6
T_P2 = T_REV + 3.4                                # 追い打ち「20000 ÷ □ ＝ ？」
T_PI = T_P2 + 2.3                                 # 「＝ 3.14…」
T_PI2 = T_PI + 1.4                                # 「円周率」
T_Q = T_PI2 + 3.4                                 # 締め「なんで円周率が出てくる？」（答えは概要欄）
DURATION = T_Q + 4.0


def dropped(t):
    """1万本モードで、いま何本落ちたか（はじめはゆっくり、だんだん土砂降り）"""
    if t < T_M0:
        return 0
    return int(N * clamp01((t - T_M0) / M_DUR) ** 2.2)


# ---------- 描画 ----------

def needle(ctx, cx, cy, th, ln, col, a=1.0, width=4.0):
    """針（片方に小さな穴の輪）"""
    dx, dy = ln / 2 * math.cos(th), ln / 2 * math.sin(th)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - dx, cy - dy)
    ctx.line_to(cx + dx, cy + dy)
    ctx.stroke()
    if width >= 3:
        ctx.set_line_width(width * 0.6)
        ctx.arc(cx + dx * 0.92, cy + dy * 0.92, width * 1.1, 0, 2 * math.pi)
        ctx.stroke()


def floor_lines(ctx, x0, x1, y0, gap, k, a=1.0, width=4.0):
    ctx.set_source_rgba(*hexrgb(LINE_C, 0.9 * a))
    ctx.set_line_width(width)
    for i in range(k + 1):
        y = y0 + i * gap
        ctx.move_to(x0 - 20, y)
        ctx.line_to(x1 + 20, y)
    ctx.stroke()


def falling(ctx, t, t0, cx, cy, th, ln, cross, width=5.0):
    """t0 に落ち始め、FALL 秒で床に着く。着いたら、線に重なった針は赤"""
    age = t - t0
    if age < 0:
        return False
    p = clamp01(age / FALL)
    e = p * p
    y = cy - 260 * (1 - e)
    ang = th + (1 - e) * 2.5                       # くるくる回りながら落ちる
    landed = p >= 1
    col = (RED if cross else NEEDLE_C) if landed else INK
    needle(ctx, cx, y, ang, ln, col, a=1.0, width=width)
    if landed and cross and age - FALL < 0.35:     # 重なった瞬間、交わりに蛍光ペンの丸
        q = (age - FALL) / 0.35
        ctx.set_source_rgba(*hexrgb(MARKER, 0.8 * (1 - q)))
        ctx.arc(cx, cy, 20 + 40 * q, 0, 2 * math.pi)
        ctx.fill()
    return landed


# 冒頭の右上: 小さな床に針がぽとぽと落ち続ける（1コマ目から「針を落とす話だ」と分かるように）
MINI = dict(x0=600, x1=995, y0=400, gap=80, k=2)   # iPhone で上の約370pxが隠れるので、その下に
_mrng = np.random.default_rng(77)
MINI_N = 40
MINI_CX = _mrng.uniform(645, 955, MINI_N)
MINI_CY = _mrng.uniform(400, 560, MINI_N)
MINI_TH = _mrng.uniform(0, math.pi, MINI_N)
_m1, _m2 = MINI_CY - 40 * np.sin(MINI_TH), MINI_CY + 40 * np.sin(MINI_TH)
MINI_CROSS = np.floor((_m2 - 400) / 80) > np.floor((_m1 - 400) / 80)
MINI_IV = 0.45
MINI_PRE = 2.2


def draw_deco(ctx, t, a):
    ctx.push_group()
    floor_lines(ctx, MINI["x0"], MINI["x1"], MINI["y0"], MINI["gap"], MINI["k"], width=3.5)
    tt = t + MINI_PRE                              # 0秒目の時点で、もう何本か床に落ちている
    k = int((tt + 0.3) / MINI_IV) + 1
    for i in range(max(0, k - 9), k):             # 9本まで残して、古いものから消える
        falling(ctx, tt, i * MINI_IV - 0.3, MINI_CX[i % MINI_N], MINI_CY[i % MINI_N], MINI_TH[i % MINI_N],
                80, MINI_CROSS[i % MINI_N], width=4.5)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


INTRO = note.Intro(["床の線に針を1万本落とす。", "線に重なるのは何本？"], ["約5000本", "約6400本", "約8000本"],
                   correct=1, msg="1万本落として確かめる", deco=draw_deco,
                   big=["床の線に針を1万本落とす。", "線に重なるのは", "何本？"],
                   rule=None)   # 2026-09-29 ユーザー「1コマ目のルールはなくそう。読むところが増えてごちゃごちゃする」

RULE = "針の長さ＝線の間。重なったら赤"


def draw_sample(ctx, t, fade):
    text(ctx, "まず8本", 540, 690, 36, PENCIL, bold=False, alpha=fade)
    ctx.push_group()
    floor_lines(ctx, SB0, SB1, SY0, SD, SK)
    n_land = n_cross = 0
    for i in range(S_N):
        if falling(ctx, t, S_TIMES[i], S_CX[i], S_CY[i], S_TH[i], SL, S_CROSS[i], width=7):
            n_land += 1
            n_cross += int(S_CROSS[i])
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(fade)
    text(ctx, f"重なった {n_cross}本 ／ 落とした {n_land}本", 540, 1240, 48, INK, alpha=fade)
    text(ctx, RULE, 540, 1420, 38, INK, alpha=fade)
    if t >= T_S_END:
        a = ease_out((t - T_S_END) / 0.25) * fade
        note.sticky(ctx, f"8本中 {int(S_CROSS.sum())}本が重なった", 540, 1325, 56, "pink", fg=RED, a=a)


# 1万本は毎コマ全部を描かず、落ちた分だけ1枚の絵に足していく（書き出しは時刻順なので速い）
_CACHE = {"n": 0, "surf": None}


def mass_surface(n):
    if _CACHE["surf"] is None or n < _CACHE["n"]:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        _CACHE.update(n=0, surf=s)
    s = _CACHE["surf"]
    c = cairo.Context(s)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_width(1.6)
    for col, sel in ((NEEDLE_C, ~CROSS), (RED, CROSS)):
        idx = np.arange(_CACHE["n"], n)
        idx = idx[sel[_CACHE["n"]:n]]
        if len(idx) == 0:
            continue
        c.set_source_rgba(*hexrgb(col, 0.75))
        dx, dy = L / 2 * np.cos(TH[idx]), L / 2 * np.sin(TH[idx])
        for x, y, a, b in zip(CX[idx], CY[idx], dx, dy):
            c.move_to(x - a, y - b)
            c.line_to(x + a, y + b)
        c.stroke()
    _CACHE["n"] = n
    return s


def draw_mass(ctx, t):
    floor_lines(ctx, BX0, BX1, BY0, D, K, width=2.5)
    n = dropped(t)
    ctx.set_source_surface(mass_surface(n), 0, 0)
    ctx.paint()
    # 落ちている途中の針（見た目だけ。数には入れない）
    if n < N:
        k = min(N - n, 40)
        for j in range(k):
            i = n + j
            yy = CY[i] - 200 * (j / 40)
            needle(ctx, CX[i], yy, TH[i] + j * 0.2, L, INK, a=0.5, width=1.6)
    c = int(CROSS[:n].sum())
    ratio = c / n * 100 if n else 0
    text(ctx, f"落とした {n:,}本", 540, 1245, 46, INK)
    text(ctx, f"重なった {c:,}本", 540, 1300, 46, RED)
    text(ctx, f"重なった割合 {ratio:.0f}%", 540, 1350, 38, INK, alpha=1 if n else 0)
    note.legend(ctx, [(RED, "線に重なった"), (NEEDLE_C, "重ならない")], 1403, 34)


def body(ctx, t):
    if t < T_A0:
        return
    if t < T_BANNER:
        fo = ease_out((t - T_A0) / 0.25) * (1 - ease((t - (T_BANNER - 0.25)) / 0.25))
        draw_sample(ctx, t, fo)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万本 落としてみる", 540, 950, a=a, t_rel=t - T_BANNER)
    else:
        draw_mass(ctx, t)
        if T_M_END <= t < T_P2 + 0.3:
            a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
            note.sticky(ctx, f"線に重なったのは\n{C:,}本（{pct(SIM_P)}%）", 540, 950, 68, "yellow", a=a)
        q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締めの問いかけに入れ替える
        if t >= T_P2 and q < 1:
            a = ease_out((t - T_P2) / 0.3) * (1 - q)
            note.sticky(ctx, f"落とした本数 × 2 ÷ 重なった本数", 540, 810, 44, "blue", a=a, tilt=-0.015)
            note.sticky(ctx, f"20000 ÷ {C} ＝ ？" if t < T_PI else f"20000 ÷ {C} ＝ {math.floor(SIM_PI * 1000) / 1000:.3f}…",
                        540, 950, 62, "yellow", a=a, fg=RED if t >= T_PI else INK)
        if t >= T_PI2 and q < 1:
            b = ease_out((t - T_PI2) / 0.3) * (1 - q)
            note.sticky(ctx, "本物の円周率は 3.14159…\n針を落とすだけで ほぼ同じ！", 540, 1120, 46, "mint", a=b, tilt=0.02)
        if q > 0:
            # 「だから何？」で終わらないよう、理由は問いかけにして、答えは概要欄に書く（2026-09-29 ユーザー提案）
            note.sticky(ctx, "でも、なんで針から\n円周率が出てくるの？", 540, 900, 64, "yellow", a=q, tilt=-0.02)
            r = ease_out((t - T_Q - 1.2) / 0.3)
            note.sticky(ctx, "答えは概要欄に", 540, 1100, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def tink(freq=3200, dur=0.12):
    """針が床に落ちるチン"""
    t = _t(dur)
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.3 * t)) * np.exp(-t * 45)


def rain(dur):
    """1万本が降る音（だんだん強く）"""
    t = _t(dur)
    n = np.random.default_rng(9).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(3) / 3, mode="same")
    return n * (t / dur) ** 1.5 * 0.35


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    for i in range(int((note.Intro.T_MOVE + MINI_PRE) / MINI_IV) + 2):      # 冒頭の右上の針
        tl = i * MINI_IV - 0.3 + FALL - MINI_PRE
        if 0 <= tl < note.Intro.T_MOVE:
            mx.add(tl, tink(3000 + 150 * (i % 3)), 0.2)
    for i in range(S_N):
        tl = S_TIMES[i] + FALL
        mx.add(S_TIMES[i], whoosh(0.3), 0.15)
        mx.add(tl, tink(), 0.5)
        if S_CROSS[i]:
            mx.add(tl + 0.03, blip(1046.5, 0.12), 0.45)
    mx.add(T_S_END, bell(784.0), 0.5)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    mx.add(T_M0, rain(M_DUR), 0.8)
    mx.add(T_M_END, shimmer(300, 0.5), 0.8)
    mx.add(T_M_END + 0.2, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(T_P2, riser(0.8), 0.4)
    mx.add(T_PI, bell(1046.5), 0.6)
    mx.add(T_PI2, chord([261.6, 329.6, 392.0, 523.3], 2.0), 0.6)
    mx.add(T_PI2, shimmer(200, 0.6), 0.7)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 重なった={C}本（{SIM_P:.4f}） 円周率の見積もり={SIM_PI:.4f} "
          f"見本8本中 {int(S_CROSS.sum())}本 長さ={DURATION:.1f}秒")
    check_answers([
        ("線に重なる割合", SIM_P, EXACT_P, 0.01),
        ("見積もった円周率", SIM_PI, math.pi, 0.002),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 1.4, 3.2, 5.0, 7.95, T_A0 + 0.6, S_TIMES[3] + 0.6, S_TIMES[7] + 0.6,
                      T_S_END + 0.8, T_BANNER + 0.6, T_M0 + 2.0, T_M0 + 5.0, T_M_END + 1.0,
                      T_P2 + 0.8, T_PI + 0.6, T_PI2 + 1.2, T_Q + 2.0, DURATION - 0.25], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
