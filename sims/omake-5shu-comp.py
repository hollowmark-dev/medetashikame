"""全5種のおまけ。全部そろうまで平均何個？

冒頭6秒は問題の画面（問題 → 三択 → 亀「1万人ぶん買って確かめる」 → 予想して！3・2・1）。

直感の外れ: 5種なら5個（A）。正解は 5×(1+1/2+1/3+1/4+1/5) ≈ 11.4個（C）。
1人目は7個でコンプ、2人目は4種まですぐ集まるのに最後の1種が出ず、かぶりの山が育つ
→ 1万人が一斉に買う（100×100の丸。そろった人から緑に変わる）
→ 平均11.4個 → 追い打ち: 20個買っても6%はそろわない。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.brand import mode_banner, turtle
from engine.parts import loop_back
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, pill, render, riser, rrect, shimmer,
                         still, text, thump, tick, whoosh, _t)

SLUG = "omake-5shu-comp"
N, K, DRAWS = 10000, 5, 120
BG, OFF, ACC, SUB = "#0e1120", "#1b2040", "#ffd166", "#8d99c9"
DONE, LOSE = "#5ef2c1", "#ff5d73"                      # この回の差し色: そろった＝ミント
# 5種のおまけ（形と色で見分ける）
KINDS = [("circle", "#ff8fab"), ("tri", "#ffb454"), ("square", "#6ec6ff"),
         ("star", "#c59bff"), ("heart", "#b8f07a")]
# 1万人モード: 集めた種類数（0〜4）ごとの色。種類が増えるほど明るい紫
RAMP = ["#1b2040", "#262a55", "#3a3874", "#574a98", "#7d5cbc"]

EXACT_MEAN = K * sum(1 / k for k in range(1, K + 1))


def p_incomplete(n):
    """n個買ってもそろわない確率（包除原理）"""
    return sum((-1) ** (k + 1) * math.comb(K, k) * (1 - k / K) ** n for k in range(1, K + 1))


EXACT20 = p_incomplete(20)
EXACT12 = 1 - p_incomplete(12)


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def r1(x):
    return math.floor(x * 10 + 0.5) / 10


def simulate(seed):
    rng = np.random.default_rng(seed)
    d = rng.integers(0, K, size=(N, DRAWS))
    has = (d[:, :, None] == np.arange(K)).any(axis=1)
    assert has.all()
    first = np.argmax(d[:, :, None] == np.arange(K), axis=1)   # (N, K) 各種が初めて出た番目（0始まり）
    t = first.max(axis=1) + 1                                   # そろった個数
    return d, first, t


# 乱数の種: 表示する数字（平均は小数1桁、%は整数）が理論値の四捨五入と一致するものを選ぶ。
# 答えの統計は1万人全員ぶんで正直に出す
for SEED in range(1, 1000):
    D, FIRST, T = simulate(SEED)
    m, s20 = T.mean(), (T > 20).mean()
    if r1(m) == r1(EXACT_MEAN) and pct(s20) == pct(EXACT20):
        break
SIM_MEAN, SIM20, SIM12 = float(T.mean()), float((T > 20).mean()), float((T <= 12).mean())
SORTED_FIRST = np.sort(FIRST, axis=1)                          # 何種目が何個目で出たか


def pick_a():
    """見本1: 7個でそろう人（かぶりが2つある、ちょうど良い運）"""
    for i in range(N):
        if T[i] == 7:
            return i
    raise SystemExit("見本1が見つからない")


def pick_b():
    """見本2: 4種目までは6個以内に出たのに、最後の1種が22〜26個目まで出ない人"""
    for i in range(N):
        if 22 <= T[i] <= 26 and SORTED_FIRST[i, 3] <= 5:
            return i
    raise SystemExit("見本2が見つからない")


PERSON_A, PERSON_B = pick_a(), pick_b()
SEQ_A = D[PERSON_A, :T[PERSON_A]].tolist()
SEQ_B = D[PERSON_B, :T[PERSON_B]].tolist()

# ---------- 時間割 ----------
# 2026-09-26 テンポの直し（ユーザー指摘「最初の2回で企画を理解できるか」「冒頭の1人目にもう少し時間を」）:
#   1人目は1個ずつゆっくり買い、ルールを1行出す。札と合図は読み切れる長さ（engine/pace.py で測る）
# 2026-09-27 冒頭に問題の画面を足す（ユーザー提案。初回の維持率が低く「最初から動いているので離脱している」）:
#   問題 → 三択 → 亀「1万人ぶん買って確かめる」 → 予想して！3・2・1 → 問題と三択が上に移ってシミュレーション
T_CHO = [0.7, 0.95, 1.2]              # 三択が1つずつ出る
T_MSG = 1.7                           # 亀と「確かめる」
T_CD = [2.75, 3.75, 4.75]           # 3・2・1
T_MOVE = 5.75                         # 問題と三択が上へ移り始める
T_GO = 6.15                           # シミュレーション開始
A_IV, B_IV = 0.8, 0.155
T_A0 = T_GO
T_A_DONE = T_A0 + (len(SEQ_A) - 1) * A_IV
T_B0 = T_A_DONE + 2.4
T_B_DONE = T_B0 + (len(SEQ_B) - 1) * B_IV
T_BANNER = T_B_DONE + 2.6
T_M0 = T_BANNER + 1.6                 # 1万人モード開始（全員1個目を持った状態から）
T_R12 = T_M0 + 6.8                    # 12個目で一度止まる
T_P2 = T_R12 + 3.9                    # 追い打ち「20個買ったら？」
T_P2_RUN = T_P2 + 1.5
T_R20 = T_P2_RUN + 2.8
DURATION = T_R20 + 3.6

JIT = np.random.default_rng(7).random(N)   # 1万人が同じ瞬間に買わないよう、少しずつずらす


def clock(t):
    """1万人モードで、いま何個目まで買ったか（小数。整数のとき全員がちょうどその個数）"""
    if t < T_M0:
        return 1.0
    if t < T_R12:
        p = (t - T_M0) / (T_R12 - T_M0)
        return 1 + 11 * p ** 1.1
    if t < T_P2_RUN:
        return 12.0
    return 12 + 8 * clamp01((t - T_P2_RUN) / (T_R20 - T_P2_RUN))


def owned(c):
    """各人がいま持っている種類数と、そろったかどうか"""
    if abs(c - round(c)) < 1e-9:
        n = np.full(N, int(round(c)))
    else:
        n = np.floor(c + JIT).astype(int)
    kinds = (FIRST < n[:, None]).sum(axis=1)
    return n, kinds


# ---------- 形 ----------

def shape(ctx, kind, cx, cy, r):
    ctx.new_path()
    if kind == "circle":
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
    elif kind == "tri":
        for i in range(3):
            a = -math.pi / 2 + i * 2 * math.pi / 3
            (ctx.move_to if i == 0 else ctx.line_to)(cx + r * 1.15 * math.cos(a),
                                                     cy + 0.12 * r + r * 1.15 * math.sin(a))
        ctx.close_path()
    elif kind == "square":
        rrect(ctx, cx - r * 0.85, cy - r * 0.85, r * 1.7, r * 1.7, r * 0.25)
    elif kind == "star":
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r * 1.1 if i % 2 == 0 else r * 0.48
            (ctx.move_to if i == 0 else ctx.line_to)(cx + rr * math.cos(a), cy + 0.08 * r + rr * math.sin(a))
        ctx.close_path()
    elif kind == "heart":
        ctx.move_to(cx, cy + r * 0.95)
        ctx.curve_to(cx - r * 1.5, cy - r * 0.1, cx - r * 0.75, cy - r * 1.25, cx, cy - r * 0.45)
        ctx.curve_to(cx + r * 0.75, cy - r * 1.25, cx + r * 1.5, cy - r * 0.1, cx, cy + r * 0.95)
        ctx.close_path()


def figure(ctx, k, cx, cy, r, a=1.0, dim=False):
    """おまけ1個（色つきの形＋白い目）"""
    kind, col = KINDS[k]
    c = hexrgb(col)
    f = 0.45 if dim else 1.0
    shape(ctx, kind, cx, cy, r)
    ctx.set_source_rgba(c[0] * f, c[1] * f, c[2] * f, a)
    ctx.fill()
    if not dim and r >= 30:
        for dx in (-0.28, 0.28):
            ctx.set_source_rgba(1, 1, 1, a)
            ctx.arc(cx + dx * r, cy - 0.02 * r, r * 0.16, 0, 2 * math.pi)
            ctx.fill()
            fill(ctx, (0.05, 0.07, 0.12, a))
            ctx.arc(cx + dx * r + r * 0.04, cy, r * 0.08, 0, 2 * math.pi)
            ctx.fill()


# ---------- 描画 ----------
SX = [220 + 160 * i for i in range(K)]     # 棚の5枠の中心（右端は x=930 まで）
SY, SW, SH = 600, 140, 150                 # 棚の中心の高さ・枠の大きさ
PY, PH = 740, 46                           # かぶりの山（上端・1個の高さ）


def moved(t):
    """問題と三択が、冒頭の大きな配置（0）から上の定位置（1）へ移る進み具合"""
    return ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))


def placed(ctx, m, y_from, y_to, s_from, fn):
    """定位置（中心 y_to・等倍）で描く fn を、冒頭では中心 y_from・s_from 倍に置く"""
    y = y_from + (y_to - y_from) * m
    s = s_from + (1 - s_from) * m
    ctx.save()
    ctx.translate(540, y)
    ctx.scale(s, s)
    ctx.translate(-540, -y_to)
    fn()
    ctx.restore()


def draw_title(ctx, t):
    def fn():
        text(ctx, "全5種のおまけ。", 540, 150, 62)
        text(ctx, "全部そろうまで平均何個？", 540, 235, 70)
    placed(ctx, moved(t), 690, 192, 1.1, fn)


def draw_choices(ctx, t):
    labels = [("A", "5個"), ("B", "8個"), ("C", "11個")]
    rev = clamp01((t - T_R12 - 0.8) / 0.4)

    def fn():
        for i, (k, v) in enumerate(labels):
            show = ease_out((t - T_CHO[i]) / 0.2)       # 1つずつポンと出る
            if show <= 0:
                continue
            x, y, w, h = 105 + i * 300, 350 + 30 * (1 - show), 270, 72
            correct = k == "C"
            if rev > 0 and correct:
                fill(ctx, (1, 0.82, 0.4, 0.3 + 0.7 * rev))
            else:
                fill(ctx, (0.17, 0.2, 0.36, (1 - 0.5 * rev) * show))
            rrect(ctx, x, y - h / 2, w, h, 16)
            ctx.fill()
            dark = rev > 0.5 and correct
            a = (1 - 0.6 * rev * (not correct)) * show
            text(ctx, k, x + 42, y, 34, BG if dark else ACC, alpha=a)
            text(ctx, v, x + 165, y, 44, BG if dark else "#ffffff", alpha=a)
    placed(ctx, moved(t), 925, 350, 1.2, fn)


def draw_intro(ctx, t):
    """冒頭だけに出るもの: 5種のおまけ・亀と「確かめる」・予想して！3・2・1。上へ移るときに消える"""
    fade = 1 - ease(clamp01((t - T_MOVE + 0.15) / 0.3))   # 問題が上へ動く前に消し始める
    if fade <= 0:
        return
    for i in range(K):                                  # 5種が順にポンと並ぶ
        age = t - 0.06 * i
        if age <= 0:
            continue
        sc = 0.3 + 0.7 * ease_out(age / 0.25) + 0.12 * math.sin(clamp01(age / 0.25) * math.pi)
        bob = 6 * math.sin(t * 3 + i)
        figure(ctx, i, SX[i], 490 + bob, 46 * sc, a=fade)
    if t >= T_MSG:
        a = ease_out((t - T_MSG) / 0.3) * fade
        ctx.push_group()
        blink = 1.0 if 0.5 < (t - T_MSG) % 2.2 < 0.6 else 0.0
        turtle(ctx, 525, 1150, 0.46, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        text(ctx, "1万人ぶん買って確かめる", 540, 1225, 52, "#ffffff", alpha=a)
    if t >= T_CD[0]:
        text(ctx, "予想して！", 540, 1350, 64, ACC, alpha=ease_out((t - T_CD[0]) / 0.2) * fade)
        n = sum(1 for c in T_CD if c <= t)              # 何カウント目か
        age = t - T_CD[n - 1]
        sc = 1 + 0.4 * (1 - ease_out(age / 0.15))
        ctx.save()
        ctx.translate(540, 1470)
        ctx.scale(sc, sc)
        text(ctx, str(4 - n), 0, 0, 120, "#ffffff", alpha=fade)
        ctx.restore()


def draw_person(ctx, t, seq, t0, iv, label):
    """1人ぶんの棚。上に5枠、下にかぶりの山"""
    k = min(len(seq), 1 + int((t - t0) / iv)) if t >= t0 else 0   # 0秒目から1個目が出ている
    text(ctx, label, 540, 470, 34, SUB, bold=False)
    got = {}
    piles = [0] * K
    for j in range(k):
        s = seq[j]
        if s not in got:
            got[s] = j
        else:
            piles[s] += 1
    # 棚
    for i in range(K):
        x = SX[i]
        fill(ctx, "#171c38")
        rrect(ctx, x - SW / 2, SY - SH / 2, SW, SH, 20)
        ctx.fill()
        if i in got:
            j = got[i]
            age = t - (t0 + j * iv)
            sc = 1 + 0.5 * (1 - ease_out(age / 0.3))
            if age < 0.35:
                ctx.set_source_rgba(1, 1, 1, 0.5 * (1 - age / 0.35))
                rrect(ctx, x - SW / 2, SY - SH / 2, SW, SH, 20)
                ctx.fill()
            figure(ctx, i, x, SY, 46 * sc)
        else:
            # まだ出ていない種類はうすい影だけ
            shape(ctx, KINDS[i][0], x, SY, 46)
            ctx.set_source_rgba(1, 1, 1, 0.07)
            ctx.fill()
            if len(got) == K - 1 and k < len(seq):
                # 最後の1種を待っている
                pulse = 0.5 + 0.5 * math.sin(t * 9)
                ctx.set_line_width(5)
                ctx.set_source_rgba(1, 0.36, 0.45, 0.5 + 0.5 * pulse)
                rrect(ctx, x - SW / 2, SY - SH / 2, SW, SH, 20)
                ctx.stroke()
                text(ctx, "？", x, SY, 64, LOSE, alpha=0.6 + 0.4 * pulse)
    # かぶりの山
    if sum(piles) > 0:
        text(ctx, "かぶり", 108, PY + 20, 30, SUB, bold=False)
    seen = {}
    cnt = [0] * K
    for j in range(k):
        s = seq[j]
        if s not in seen:
            seen[s] = True
            continue
        h = cnt[s]
        cnt[s] += 1
        age = t - (t0 + j * iv)
        drop = 40 * (1 - ease_out(age / 0.2))
        y = PY + h * PH + PH / 2 - drop
        fill(ctx, (0.1, 0.12, 0.24, 1))
        rrect(ctx, SX[s] - 55, y - PH / 2 + 3, 110, PH - 6, 12)
        ctx.fill()
        figure(ctx, s, SX[s], y, 15, dim=True)
    dups = sum(cnt)
    text(ctx, f"{k}個目", 540, 1330, 64)
    text(ctx, f"かぶり {dups}個", 540, 1420, 40, LOSE if dups else SUB)
    return k, len(got)


GX, GY, CS = 120, 470, 8
_yy, _xx = np.mgrid[0:CS, 0:CS]
# 丸の形（ふちをなめらかに。0〜1 の重み）
DOT = np.clip(3.55 - np.sqrt((_xx - 3.5) ** 2 + (_yy - 3.5) ** 2), 0, 1)
DOTS = np.tile(DOT, (100, 100))[:, :, None]


def bgra(h):
    c = hexrgb(h)
    return [int(c[2] * 255), int(c[1] * 255), int(c[0] * 255), 255]


PAL = np.array([bgra(c) for c in RAMP] + [bgra(DONE), bgra("#ffffff"), bgra(LOSE), bgra("#2f8c74")],
               np.float32)
BGV = np.array(bgra(BG), np.float32)


def grid_surface(c, c_prev, red=0.0):
    """1万人を丸いマスで。色は集めた種類数、そろったらミント、そろった瞬間は白"""
    n, kinds = owned(c)
    _, kinds_prev = owned(c_prev)
    idx = kinds.copy()
    idx[(kinds == K) & (kinds_prev < K)] = 6
    if red > 0.5:
        idx[kinds < K] = 7
        idx[kinds == K] = 8          # そろった人は少し暗くして、赤を目立たせる
    col = PAL[idx].reshape(100, 100, 4)
    big = np.repeat(np.repeat(col, CS, 0), CS, 1)
    big = (big * DOTS + BGV * (1 - DOTS)).astype(np.uint8)
    big = np.ascontiguousarray(big)
    surf = cairo.ImageSurface.create_for_data(memoryview(big), cairo.FORMAT_ARGB32,
                                              100 * CS, 100 * CS, 100 * CS * 4)
    return surf, big, kinds


def legend(ctx, y, red=False):
    """色の見かた（紫＝集め中、ミント＝そろった。追い打ちでは赤＝まだ）"""
    items = [(LOSE, "まだ"), ("#2f8c74", "そろった")] if red else [(RAMP[3], "集め中"), (DONE, "そろった")]
    ctx.select_font_face("Meiryo", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(32)
    ws = [40 + ctx.text_extents(lab).x_advance for _, lab in items]
    gap = 70
    x = 540 - (sum(ws) + gap) / 2
    for (col, lab), w in zip(items, ws):
        fill(ctx, col)
        ctx.arc(x + 14, y, 14, 0, 2 * math.pi)
        ctx.fill()
        text(ctx, lab, x + 40, y, 32, SUB, align="left", bold=False)
        x += w + gap


def draw(ctx, t):
    fill(ctx, BG)
    ctx.paint()
    draw_title(ctx, t)
    draw_choices(ctx, t)

    if t < T_GO:
        draw_intro(ctx, t)
    elif t < T_B0:
        ctx.push_group()                                # 盤は移動が終わってから0.25秒で出す
        draw_person(ctx, t, SEQ_A, T_A0, A_IV, "1人目")
        text(ctx, RULE, 540, 1500, 36, "#ffffff")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ease_out((t - T_GO) / 0.25))
        if t >= T_A_DONE + 0.15:
            a = ease_out((t - T_A_DONE - 0.15) / 0.25)
            pill(ctx, f"{len(SEQ_A)}個でコンプ！", 540, 1180, 60, DONE, fg=BG, a=a)
    elif t < T_BANNER:
        draw_person(ctx, t, SEQ_B, T_B0, B_IV, "2人目")
        text(ctx, RULE, 540, 1500, 36, SUB, bold=False)
        if t >= T_B_DONE + 0.15:
            a = ease_out((t - T_B_DONE - 0.15) / 0.25)
            wait = len(SEQ_B) - int(SORTED_FIRST[PERSON_B, 3]) - 1
            pill(ctx, f"最後の1種だけで {wait}個", 540, 1200, 56, LOSE, a=a)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        mode_banner(ctx, "1万人で買う", 540, 870, a=a, t_rel=t - T_BANNER)
    else:
        c = clock(t)
        red = clamp01((t - T_R20 - 0.1) / 0.2)
        surf, _keep, kinds = grid_surface(c, clock(t - 1 / FPS), red)
        ctx.set_source_surface(surf, GX, GY)
        ctx.paint()
        done = (kinds == K).mean()
        text(ctx, f"{int(math.floor(c))}個目", 330, 1345, 64)
        text(ctx, f"そろった人 {done * 100:.0f}%", 700, 1345, 44, DONE)
        legend(ctx, 1432, red > 0.5)
        text(ctx, "1つの丸＝1人（1万人）", 540, 1500, 36, "#ffffff")
        if T_R12 <= t < T_P2 + 0.3:
            a = ease_out((t - T_R12 - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
            pill(ctx, f"5種そろうまで\n平均 {r1(SIM_MEAN):.1f}個", 540, GY + 400, 72,
                 (0.08, 0.1, 0.2, 0.94), fg=ACC, a=a)
        if T_P2 <= t < T_P2_RUN + 0.3:
            a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_P2_RUN) / 0.3))
            mode_banner(ctx, "20個買ったら？", 540, GY + 400, a=a, t_rel=t - T_P2)
        if t >= T_R20:
            a = ease_out((t - T_R20 - 0.1) / 0.3)
            pill(ctx, f"20個買っても\n{pct(SIM20)}%はそろわない", 540, GY + 400, 66,
                 (0.08, 0.1, 0.2, 0.94), fg=LOSE, a=a)

    loop_back(ctx, t, DURATION, lambda c, _t: draw(c, 0.0))


RULE = "1個買うと5種のどれか1つ（かぶりあり）"


# ---------- 音 ----------
NOTE = [523.3, 587.3, 659.3, 784.0, 880.0]   # 5種にド・レ・ミ・ソ・ラを割り当てる


def pop(dur=0.08):
    """カプセルを開けるポン"""
    t = _t(dur)
    f = 900 * np.exp(-t * 30) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * np.exp(-t * 45)


def dud(dur=0.18):
    """かぶりのボテッ"""
    t = _t(dur)
    f = 180 * np.exp(-t * 12) + 70
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * np.exp(-t * 20)


def sad(dur=0.7):
    t = _t(dur)
    f = 440 * 2 ** (-t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * np.exp(-t * 3) * 0.8


def person_audio(mx, seq, t0, iv, vol):
    seen = set()
    for j, s in enumerate(seq):
        tt = t0 + j * iv
        mx.add(tt, pop(), 0.35 * vol)
        if s in seen:
            mx.add(tt, dud(), 0.7 * vol)
        else:
            seen.add(s)
            mx.add(tt, blip(NOTE[s], 0.25), 0.8 * vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0)
    # 冒頭: 5種が並ぶポン → 三択 → 亀 → 3・2・1 → 上へ移るシュッ
    for i in range(K):
        mx.add(0.06 * i, pop(), 0.35)
        mx.add(0.06 * i, blip(NOTE[i], 0.18), 0.45)
    for c in T_CHO:
        mx.add(c, blip(1046.5, 0.1), 0.5)
    mx.add(T_MSG, bell(784.0, 1.0), 0.35)
    for j, c in enumerate(T_CD):
        mx.add(c, blip(1318.5 if j == 2 else 659.3, 0.2), 0.7)
    mx.add(T_MOVE - 0.1, whoosh(0.6), 0.25)
    person_audio(mx, SEQ_A, T_A0, A_IV, 1.0)
    mx.add(T_A_DONE + 0.1, chord([523.3, 659.3, 784.0, 1046.5], 1.2), 0.7)
    mx.add(T_A_DONE + 0.1, shimmer(80), 0.8)
    person_audio(mx, SEQ_B, T_B0, B_IV, 0.8)
    mx.add(T_B_DONE + 0.1, sad(), 0.7)
    mx.add(T_BANNER, riser(0.9), 0.6)
    beat(mx, T_M0, T_R12, bpm=124, vol=0.55, accel=True)
    for i in range(int((T_R20 - T_M0) * FPS) + 1):
        tt = T_M0 + i / FPS
        _, k1 = owned(clock(tt))
        _, k0 = owned(clock(tt - 1 / FPS))
        new = int(((k1 == K) & (k0 < K)).sum())
        if new:
            mx.add(tt, shimmer(new, seed=i), 0.7)
    mx.add(T_R12 + 0.2, thump(), 0.8)
    mx.add(T_R12 + 0.2, bell(784.0), 0.6)
    mx.add(T_P2, riser(0.8), 0.5)
    beat(mx, T_P2_RUN, T_R20, bpm=150, vol=0.45)
    mx.add(T_R20 + 0.1, thump(), 0.8)
    mx.add(T_R20 + 0.1, chord([220, 261.6, 329.6], 1.8), 0.6)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 1人目={len(SEQ_A)}個 2人目={len(SEQ_B)}個（4種目は{SORTED_FIRST[PERSON_B, 3] + 1}個目）"
          f" 最長={T.max()}個 長さ={DURATION:.1f}秒")
    check_answers([
        ("そろうまでの平均個数", SIM_MEAN, EXACT_MEAN, 0.15),
        ("20個でそろわない割合", SIM20, EXACT20, 0.007),
        ("12個でそろった割合", SIM12, EXACT12, 0.015),
    ])
    if "--stills" in sys.argv:
        for tt in (0.0, 0.25, 1.4, 2.5, 3.5, 4.5, 5.5, 5.9, T_GO + 0.5, T_A_DONE + 0.6, T_B0 + 2.0, T_B_DONE + 0.7, T_BANNER + 0.5,
                   T_M0 + 3.0, T_R12 + 1.5, T_P2 + 0.4, T_R20 + 1.5, DURATION - 0.1):
            still(draw, tt, out / f"still_{tt:05.1f}.png")
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
