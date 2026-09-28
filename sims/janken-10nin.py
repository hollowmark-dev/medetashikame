"""10人でじゃんけん。あいこが終わるまで平均何回？

「あいこが終わる」＝勝ち負けが1人でも出る回（最後の1人が決まるまで、ではない）。
1回で決着する確率 p = 3×(2^10−2)/3^10 ≈ 5.2%、平均 1/p ≈ 19.3回（C）。直感の外れは3回（A）。
1組目は輪になった10人があいこを延々くり返す、2組目はいきなり1回で決着
→ 1万組が一斉に（丸い盤に1万マス。あいこの間は手の色がちらつき、決着した組から白くなる）
→ 平均19.3回 → 追い打ち: 50回やっても7%は決まらない。

2026-09-27 ノートの見た目に変更（engine/note.py）。紺の画面は広告に見えてスワイプされていたため。
冒頭8秒は問題の画面（問題 → 三択 → 亀 → 予想して！5・4・3・2・1）。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.parts import loop_back, stills
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, shimmer,
                         still, text, thump, tick, _t)

note.use()
note.DATE = "9.28"                                # 日付欄（公開日）

SLUG = "janken-10nin"
N, P10, ROUNDS = 10000, 10, 320
# この回の差し色: グー＝コーラル、チョキ＝すみれ、パー＝青緑。決着＝インクで塗りつぶす
HANDS = ["#f26b4f", "#9b72e8", "#1fb3a2"]
HAND_NAMES = ["グー", "チョキ", "パー"]
DECIDED, LOSE, AIKO = "#2c3a55", RED, "#6f7fb3"
WAIT_HAND = "#cfc8b6"

EXACT_P = 3 * (2 ** P10 - 2) / 3 ** P10      # 1回で勝ち負けが出る確率
EXACT_MEAN = 1 / EXACT_P
EXACT50 = (1 - EXACT_P) ** 50                # 50回やっても決まらない確率
EXACT20 = 1 - (1 - EXACT_P) ** 20


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def r1(x):
    return math.floor(x * 10 + 0.5) / 10


def simulate(seed):
    rng = np.random.default_rng(seed)
    hands = rng.integers(0, 3, size=(N, ROUNDS, P10), dtype=np.int8)
    kinds = sum((hands == k).any(axis=2).astype(np.int8) for k in range(3))
    decisive = kinds == 2                         # ちょうど2種類の手が出た回だけ勝ち負けがつく
    assert decisive.any(axis=1).all()
    r = np.argmax(decisive, axis=1) + 1           # 何回目で決着したか
    return hands, r


# 乱数の種: 表示する数字（平均は小数1桁、%は整数）が理論値の四捨五入と一致するものを選ぶ。
# 答えの統計は1万組全部で正直に出す
for SEED in range(1, 1000):
    HANDS_ALL, R = simulate(SEED)
    if r1(R.mean()) == r1(EXACT_MEAN) and pct((R > 50).mean()) == pct(EXACT50):
        break
SIM_MEAN, SIM50 = float(R.mean()), float((R > 50).mean())
SIM20, SIM1 = float((R <= 20).mean()), float((R == 1).mean())
H0 = HANDS_ALL[:, :, 0].copy()                    # 1万組モードで見せる色（各組の1人目の手）

GROUP_A = int(np.argmax((R >= 28) & (R <= 34)))   # 見本1: あいこが長引く組
GROUP_B = int(np.argmax(R == 1))                  # 見本2: いきなり決着する組
SEQ_A = HANDS_ALL[GROUP_A, :R[GROUP_A]].tolist()
SEQ_B = HANDS_ALL[GROUP_B, :R[GROUP_B]].tolist()
del HANDS_ALL


def winner(hs):
    """決着した回の、勝った手（0=グー 1=チョキ 2=パー。a は (a+1)%3 に勝つ）"""
    a, b = sorted(set(hs))
    return a if (b - a) % 3 == 1 else b


# ---------- 時間割 ----------
# 2026-09-26 テンポの直し（ユーザー指摘「最初の2回で企画を理解できるか」「冒頭の1人目にもう少し時間を」）:
#   ・1回目の「じゃんけん…」は問題を読む時間を兼ねて長くタメる。そのあと4回は1回0.9秒でゆっくり、以降加速
#   ・ルールを1行出す。札と合図は「0.5秒＋文字数÷6秒」以上出す（engine/pace.py で測る）
FIRST_SHAKE = 1.5                                 # 1回目のタメ（問題は冒頭で読んだので短く）
SLOW_N, SLOW_IV = 5, 0.9                          # 1回目を含めて5回はゆっくり


def schedule(n, first=0.5, fastest=0.13, decay=0.8):
    """各回の開始時刻（最初の SLOW_N 回はゆっくり、そのあとだんだん速く）"""
    ts, t = [], 0.0
    for k in range(n):
        ts.append(t)
        if k == 0:
            t += FIRST_SHAKE + SLOW_IV - 0.3
        elif k < SLOW_N:
            t += SLOW_IV
        else:
            t += max(fastest, first * decay ** (k - SLOW_N))
    return ts


TS_A = schedule(len(SEQ_A))
SHAKE_A = [FIRST_SHAKE] + [None] * (len(SEQ_A) - 1)   # None は間隔から自動で決める
T_A0 = note.Intro.T_GO                            # 冒頭の問題画面（約8秒）のあと
T_A_DONE = T_A0 + TS_A[-1] + 0.3
T_B0 = T_A_DONE + 2.4
TS_B = [0.0]
B_SHAKE = 0.75                                    # 2組目は「じゃんけん…」をゆっくり見せる
T_B_DONE = T_B0 + B_SHAKE
T_BANNER = T_B_DONE + 0.3 + 2.4
T_M0 = T_BANNER + 1.6
T_R20 = T_M0 + 6.8
T_P2 = T_R20 + 3.9
T_P2_RUN = T_P2 + 1.5
T_R50 = T_P2_RUN + 3.0
DURATION = T_R50 + 3.6

JIT = np.random.default_rng(11).random(N)


def clock(t):
    """1万組モードで、いま何回目か（小数。整数のとき全組がちょうどその回）"""
    if t < T_M0:
        return 1.0
    if t < T_R20:
        p = (t - T_M0) / (T_R20 - T_M0)
        return 1 + 19 * p ** 1.15
    if t < T_P2_RUN:
        return 20.0
    return 20 + 30 * clamp01((t - T_P2_RUN) / (T_R50 - T_P2_RUN))


def rounds_done(c):
    if abs(c - round(c)) < 1e-9:
        return np.full(N, int(round(c)))
    return np.floor(c + JIT).astype(int)


def shake_for(iv):
    """「じゃんけん…」のタメの長さ。速い回ではタメを省く（灰色と色が交互に出てちらつくため）"""
    return 0.0 if iv < 0.25 else min(0.3, iv * 0.45)


# ---------- 手の絵 ----------

def _finger(ctx, bx, by, ang, w, length):
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(ang)
    rrect(ctx, -w / 2, -length, w, length + w, w / 2)
    ctx.restore()


def _part(ctx, col, a, edge):
    c = hexrgb(col) if isinstance(col, str) else col
    ctx.set_source_rgba(c[0], c[1], c[2], a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*edge)
    ctx.set_line_width(4)
    ctx.stroke()


def hand(ctx, kind, cx, cy, s, col, a=1.0):
    """グー(0)・チョキ(1)・パー(2) を図形で描く。s は大きさ（手のひらの半幅くらい）"""
    if a < 1.0:
        ctx.push_group()
        hand(ctx, kind, cx, cy, s, col, 1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        return
    edge = hexrgb(INK)
    ctx.save()
    ctx.translate(cx, cy + 0.2 * s)
    if kind == 0:
        rrect(ctx, -0.85 * s, -0.55 * s, 1.7 * s, 1.25 * s, 0.4 * s)
        _part(ctx, col, a, edge)
        for i in range(4):
            ctx.new_path()
            ctx.arc(-0.63 * s + i * 0.42 * s, -0.55 * s, 0.24 * s, 0, 2 * math.pi)
            _part(ctx, col, a, edge)
        rrect(ctx, -0.95 * s, 0.0, 1.05 * s, 0.36 * s, 0.18 * s)
        _part(ctx, col, a, edge)
    elif kind == 1:
        _finger(ctx, -0.2 * s, -0.2 * s, -0.3, 0.36 * s, 1.15 * s)
        _part(ctx, col, a, edge)
        _finger(ctx, 0.22 * s, -0.2 * s, 0.3, 0.36 * s, 1.15 * s)
        _part(ctx, col, a, edge)
        rrect(ctx, -0.75 * s, -0.25 * s, 1.5 * s, 1.0 * s, 0.4 * s)
        _part(ctx, col, a, edge)
        rrect(ctx, -0.9 * s, 0.2 * s, 0.95 * s, 0.34 * s, 0.17 * s)
        _part(ctx, col, a, edge)
    else:
        for i, (ang, ln) in enumerate([(-0.28, 0.85), (-0.09, 1.0), (0.09, 0.98), (0.28, 0.82)]):
            _finger(ctx, (-0.45 + i * 0.3) * s, -0.2 * s, ang, 0.27 * s, ln * s)
            _part(ctx, col, a, edge)
        _finger(ctx, -0.55 * s, 0.35 * s, -1.05, 0.3 * s, 0.7 * s)
        _part(ctx, col, a, edge)
        rrect(ctx, -0.7 * s, -0.3 * s, 1.4 * s, 1.05 * s, 0.4 * s)
        _part(ctx, col, a, edge)
    ctx.restore()


# ---------- 描画 ----------
RC, RY, RR, HS = 540, 890, 300, 50     # 輪の中心・半径・手の大きさ
SEATS = [(RC + RR * math.cos(-math.pi / 2 + i * 2 * math.pi / P10),
          RY + RR * math.sin(-math.pi / 2 + i * 2 * math.pi / P10)) for i in range(P10)]


def draw_deco(ctx, t, a):
    """冒頭の小物: グー・チョキ・パーが順にポンと出て、上下にはずむ"""
    for i in range(3):
        age = t - 0.08 * i + 0.1                     # 0秒目から1つ目は見えている
        if age <= 0:
            continue
        sc = 0.3 + 0.7 * ease_out(age / 0.25) + 0.12 * math.sin(clamp01(age / 0.25) * math.pi)
        bob = -10 * abs(math.sin(t * 3.2 + i * 0.9))
        ctx.save()
        ctx.translate(650 + i * 140, 300 + bob)
        ctx.rotate((-0.18, 0.06, 0.2)[i])
        hand(ctx, i, 0, 0, 50 * sc, HANDS[i], a=a)
        ctx.restore()


INTRO = note.Intro(["10人でじゃんけん。", "あいこが終わるまで平均何回？"], ["3回", "8回", "19回"],
                   correct=2, msg="1万組やって確かめる", deco=draw_deco,
                   big=["10人でじゃんけん。", "あいこが終わるまで", "平均何回？"],
                   rule=["3種類とも出たら → あいこ", "2種類だけなら → 決着"])


def draw_group(ctx, t, seq, t0, ts, label, shake_len=None, shakes=None, rule_col=None):
    """1組ぶん。10人が輪になって一斉に手を出す。shakes は回ごとのタメ（None なら間隔から決める）"""
    k = 0
    for j, s in enumerate(ts):
        if t >= t0 + s:
            k = j
    iv = (ts[k + 1] - ts[k]) if k + 1 < len(ts) else (shake_len or 0.6)
    tr = t - (t0 + ts[k])                           # この回が始まってからの時間
    shake = shake_len if shake_len else shake_for(iv)
    if shakes is not None and shakes[k] is not None:
        shake = shakes[k]
    last = k == len(seq) - 1
    hs = seq[k]
    revealed = tr >= shake
    text(ctx, label, 540, 490, 36, PENCIL, bold=False)
    # 輪の床
    ctx.set_source_rgba(*hexrgb(INK, 0.05))
    ctx.arc(RC, RY, RR + 72, 0, 2 * math.pi)
    ctx.fill()
    win = winner(hs) if (last and revealed and len(set(hs)) == 2) else None
    for i, (x, y) in enumerate(SEATS):
        if not revealed:
            bob = -14 * abs(math.sin(math.pi * 2 * tr / max(shake, 0.1)))
            hand(ctx, 0, x, y + bob, HS, WAIT_HAND)
        else:
            pop = 1 + 0.25 * (1 - ease_out((tr - shake) / 0.15))
            a = 1.0
            if win is not None and hs[i] != win:
                a = 0.3
            if win is not None and hs[i] == win:
                ctx.set_source_rgba(*hexrgb(MARKER, 0.55))      # 勝った手に蛍光ペン
                ctx.arc(x, y, HS * 1.4, 0, 2 * math.pi)
                ctx.fill()
                note.pen_circle(ctx, x, y, HS * 1.45, HS * 1.45, RED, seed=i, width=4)
            hand(ctx, hs[i], x, y, HS * pop, HANDS[hs[i]], a=a)
    # 輪の真ん中: 何回目と、あいこ／決着
    text(ctx, f"{k + 1}回目", RC, RY - 45, 76, INK)
    if not revealed:
        text(ctx, "じゃんけん…", RC, RY + 50, 46, PENCIL, bold=False)
    elif win is not None:
        nwin = sum(1 for h in hs if h == win)
        text(ctx, "決着！", RC, RY + 45, 62, RED)
        text(ctx, f"{HAND_NAMES[win]}の{nwin}人が勝ち", RC, RY + 115, 36, RED, bold=False)
    else:
        text(ctx, "あいこ", RC, RY + 50, 58, AIKO)
    if rule_col == "white":
        text(ctx, RULE, 540, 1460, 38, INK)
    else:
        text(ctx, RULE, 540, 1460, 38, PENCIL, bold=False)
    return k, revealed


RULE = "3種類とも出たら あいこ　2種類なら決着"


# 1万組の丸い盤: 114×114 のマスのうち、中心に近い1万マスを使う
GS, CS = 114, 7
GX, GY = 540 - GS * CS // 2, 470
_yy, _xx = np.mgrid[0:GS, 0:GS]
_d = (_xx - (GS - 1) / 2) ** 2 + (_yy - (GS - 1) / 2) ** 2
CELLS = np.argsort(_d.ravel(), kind="stable")[:N]          # 組 i が入るマス
_cell = np.zeros((CS, CS), bool)
_cell[:CS - 1, :CS - 1] = True
CELLMASK = np.tile(_cell, (GS, GS))


def bgra(h, f=1.0):
    c = hexrgb(h)
    return [int(c[2] * 255 * f), int(c[1] * 255 * f), int(c[0] * 255 * f), 255]


def mix(h, k):
    """色を紙の色へ k だけ寄せる（あいこ中は薄く）。BGRA で返す"""
    a, b = hexrgb(h), hexrgb(PAPER)
    return [int((a[2] * (1 - k) + b[2] * k) * 255), int((a[1] * (1 - k) + b[1] * k) * 255),
            int((a[0] * (1 - k) + b[0] * k) * 255), 255]


def mix_hex(h, k):
    b, g, r, _ = mix(h, k)
    return f"#{r:02x}{g:02x}{b:02x}"


# 0-2: あいこ中（その回の手の色を薄く） 3: 決着（インク） 4: 決着した瞬間（蛍光ペン） 5: 決まらない（赤） 6: 決着（薄く）
PAL = np.array([mix(c, 0.45) for c in HANDS] + [bgra(DECIDED), bgra(MARKER), bgra(LOSE),
                                                  mix(DECIDED, 0.8)], np.uint8)


def grid_surface(c, c_prev, red=False):
    n = rounds_done(c)
    n_prev = rounds_done(c_prev)
    dec = R <= n
    idx = H0[np.arange(N), np.minimum(n, ROUNDS) - 1].astype(np.int64)
    idx[dec] = 3
    idx[dec & (R > n_prev)] = 4
    if red:
        idx[~dec] = 5
        idx[dec] = 6
    flat = np.zeros((GS * GS, 4), np.uint8)
    flat[:] = bgra(PAPER)
    flat[CELLS] = PAL[idx]
    col = flat.reshape(GS, GS, 4)
    big = np.repeat(np.repeat(col, CS, 0), CS, 1)
    big[~CELLMASK] = bgra(PAPER)
    big = np.ascontiguousarray(big)
    surf = cairo.ImageSurface.create_for_data(memoryview(big), cairo.FORMAT_ARGB32,
                                              GS * CS, GS * CS, GS * CS * 4)
    return surf, big, dec


def legend(ctx, y, red=False):
    """あいこ中は3色がちらつくので縞で見せる"""
    if red:
        note.legend(ctx, [(LOSE, "まだあいこ"), (mix_hex(DECIDED, 0.8), "決着")], y, 36)
    else:
        note.legend(ctx, [([mix_hex(c, 0.45) for c in HANDS], "あいこ中"), (DECIDED, "決着")], y, 36)


def draw(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_R20 + 0.8)

    if t < T_A0:
        pass
    elif t < T_B0:
        ctx.push_group()                                # 輪は問題が上に移り終わってから0.25秒で出す
        draw_group(ctx, t, SEQ_A, T_A0, TS_A, "1組目（10人）", shakes=SHAKE_A, rule_col="white")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ease_out((t - T_A0) / 0.25))
        if t >= T_A_DONE:
            a = ease_out((t - T_A_DONE) / 0.25)
            note.sticky(ctx, f"{len(SEQ_A)}回目で やっと決着", 540, 1345, 56, "pink", fg=RED, a=a)
    elif t < T_BANNER:
        draw_group(ctx, t, SEQ_B, T_B0, TS_B, "2組目（10人）", shake_len=B_SHAKE)
        if t >= T_B_DONE + 0.3:
            a = ease_out((t - T_B_DONE - 0.3) / 0.25)
            note.sticky(ctx, "1回目で いきなり決着", 540, 1345, 56, "mint", a=a, tilt=0.02)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万組でやる", 540, 870, a=a, t_rel=t - T_BANNER)
    else:
        c = clock(t)
        red = t >= T_R50 + 0.1
        surf, _keep, dec = grid_surface(c, clock(t - 1 / FPS), red)
        ctx.set_source_surface(surf, GX, GY)
        ctx.paint()
        text(ctx, f"{int(math.floor(c))}回目", 330, 1345, 64, INK)
        text(ctx, f"決着した組 {dec.mean() * 100:.0f}%", 700, 1345, 46, DECIDED)
        legend(ctx, 1432, red)
        text(ctx, "1マス＝10人の1組（1万組）", 540, 1505, 38, INK)
        if T_R20 <= t < T_P2 + 0.3:
            a = ease_out((t - T_R20 - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
            note.sticky(ctx, f"あいこが終わるまで\n平均 {r1(SIM_MEAN):.1f}回", 540, RY - 20, 70, "yellow", a=a)
        if T_P2 <= t < T_P2_RUN + 0.3:
            a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_P2_RUN) / 0.3))
            note.banner(ctx, "50回なら？", 540, RY - 20, a=a, t_rel=t - T_P2)
        if t >= T_R50:
            a = ease_out((t - T_R50 - 0.1) / 0.3)
            note.sticky(ctx, f"50回やっても\n{pct(SIM50)}%は決まらない", 540, RY - 20, 66, "pink", fg=RED, a=a)

    loop_back(ctx, t, DURATION, lambda c, _t: draw(c, 0.0))


# ---------- 音 ----------

def clack(dur=0.09, seed=3):
    """10人が一斉に手を出す「ぽん」"""
    t = _t(dur)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(4) / 4, mode="same")
    return (n * 0.5 + np.sin(2 * np.pi * 620 * t)) * np.exp(-t * 60)


def boo(dur=0.22):
    """あいこの「ぶっ」"""
    t = _t(dur)
    x = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.3 + np.sin(2 * np.pi * 150 * t)
    return x * np.exp(-t * 14) * 0.6


def group_audio(mx, seq, t0, ts, shake_len=None, vol=1.0, shakes=None):
    for j, s in enumerate(ts):
        iv = (ts[j + 1] - s) if j + 1 < len(ts) else 0.6
        sh = shake_len if shake_len else shake_for(iv)
        if shakes is not None and shakes[j] is not None:
            sh = shakes[j]
        if sh >= 0.2:
            mx.add(t0 + s, tick(1300, 0.04), 0.4 * vol)            # じゃん
            mx.add(t0 + s + sh / 2, tick(1500, 0.04), 0.4 * vol)   # けん
        ton = t0 + s + sh
        mx.add(ton, clack(seed=j), 0.6 * vol)                       # ぽん
        if len(set(seq[j])) == 2:
            mx.add(ton + 0.05, bell(1046.5), 0.7 * vol)
            mx.add(ton + 0.05, shimmer(80, seed=j), 0.8 * vol)
            mx.add(ton + 0.05, chord([523.3, 659.3, 784.0], 1.2), 0.5 * vol)
        else:
            mx.add(ton + 0.04, boo(), (0.5 if iv > 0.2 else 0.3) * vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(98.0, 146.8, 196.0, 246.9)), 1.0, bgm=True)
    for i in range(3):                                 # 冒頭: グー・チョキ・パーがポン
        mx.add(0.08 * i, clack(seed=20 + i), 0.45)
        mx.add(0.08 * i, blip([523.3, 659.3, 784.0][i], 0.16), 0.4)
    INTRO.audio(mx)
    group_audio(mx, SEQ_A, T_A0, TS_A, shakes=SHAKE_A)
    group_audio(mx, SEQ_B, T_B0, TS_B, shake_len=B_SHAKE)
    mx.add(T_BANNER, riser(0.9), 0.6)
    beat(mx, T_M0, T_R20, bpm=132, vol=0.55, accel=True)
    for i in range(int((T_R50 - T_M0) * FPS) + 1):
        tt = T_M0 + i / FPS
        n1, n0 = rounds_done(clock(tt)), rounds_done(clock(tt - 1 / FPS))
        new = int(((R <= n1) & (R > n0)).sum())
        if new:
            mx.add(tt, shimmer(new, seed=i), 0.7)
    mx.add(T_R20 + 0.2, thump(), 0.8)
    mx.add(T_R20 + 0.2, bell(784.0), 0.6)
    mx.add(T_P2, riser(0.8), 0.5)
    beat(mx, T_P2_RUN, T_R50, bpm=150, vol=0.45)
    mx.add(T_R50 + 0.1, thump(), 0.8)
    mx.add(T_R50 + 0.1, chord([220, 261.6, 329.6], 1.8), 0.6)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 1組目={len(SEQ_A)}回 2組目={len(SEQ_B)}回 最長={R.max()}回 長さ={DURATION:.1f}秒")
    check_answers([
        ("あいこが終わるまでの平均回数", SIM_MEAN, EXACT_MEAN, 0.6),
        ("50回で決まらない割合", SIM50, EXACT50, 0.008),
        ("20回で決着した割合", SIM20, EXACT20, 0.015),
        ("1回で決着する割合", SIM1, EXACT_P, 0.007),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 1.4, 2.2, 3.2, 5.0, 7.2, 7.95, T_A0 + 0.3, T_A0 + 1.2, T_A0 + TS_A[2] + 0.5,
                      T_A0 + TS_A[4] + 0.5, T_A_DONE + 0.6, T_B0 + 0.3,
                      T_B_DONE + 0.8, T_BANNER + 0.5, T_M0 + 3.0, T_R20 + 1.5, T_P2 + 0.4,
                      T_P2_RUN + 1.5, T_R50 + 1.5, DURATION - 0.25], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
