"""コインを10回投げる。表がちょうど5回になる確率は？

直感の外れ: 「表と裏は半々だから、5回がふつう → 50%」（A）。正解は C(10,5)/2^10 = 252/1024 ≈ 25%（B）。
5回は「いちばん出やすい回数」だが、4回・6回・3回…に散らばるので、ちょうど5回は4人に1人。

1人目は表が3連続から、終わってみればちょうど5回。2人目は表8回。
→ 1万人モード: 1万人が同時に1枚ずつ投げる（10×10の束が100個。コインが一斉にくるっと回る）。
  マスの色はそこまでの表と裏の差（裏が多い＝青、同じ＝紫、表が多い＝橙）。10回目のあと「ちょうど5回」の人だけ黄緑に光る
→ 1万人が「表の回数」の列へ崩れ落ちて、山になる（黄緑の列は全体の4分の1）
→ 追い打ち: そのまま100回まで投げ続けると、ちょうど50回は8%（C(100,50)/2^100 = 0.0796）。
  山は横に広がり、真ん中の列の割合はかえって減る。

2026-09-28 ノートの見た目に変更（engine/note.py）。冒頭8秒は問題の画面で、右上ではコイン3枚が回り続ける。
文字は下端 1,450px より上、本体は紙の中心にそろえる。
2026-09-29 iPhone 対応（上の約370pxが隠れ、左右が約50pxずつ切れる）で全体を下げ、1万人のマスと山を小さくした。
冒頭のルールのメモはやめた（ユーザー「読むところが増えてごちゃごちゃする」）。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01, ease,
                         ease_out, fill, hexrgb, pad, render, riser, shimmer, text, thump,
                         tick, whoosh, _t)
from engine.parts import bgra, loop_back, pct, stills

note.use()
note.DATE = "10.1"                                # 日付欄（公開予定日）

SLUG = "coin-10kai"
N, F1, F2 = 10000, 10, 100
SUB = PENCIL
# この回の差し色: 表＝橙、裏＝藍、ちょうど半分＝緑
# 2026-09-30 ユーザー「コインのデザインがちゃっちい、本物っぽく」→ 表＝金、裏＝銀の金属のコインに。
# 実在の硬貨の図柄はまねない（字は「表」「裏」だけ）
HEAD, HEAD_RIM = "#dca42a", "#9a6a12"          # 表（金）: マスの色・文字の色
TAIL, TAIL_RIM = "#4f6fa8", "#3a5282"          # 裏（銀）: マスの色は読みやすい青みの銀
METAL = {True: ("#fff1b8", "#e6b53f", "#a8761b", "#6e4a0c"),     # 表: 明るい・地・暗い・側面
         False: ("#f7f9fc", "#b8c4d4", "#76859b", "#4a5566")}   # 裏
LIME = "#2fae78"                         # ちょうど半分（紙の上で読める緑）
RAMP_STOPS = [(0.0, "#4f6fa8"), (0.5, "#9a86ad"), (1.0, "#dca42a")]   # 裏が多い（銀の青）→ 同じ → 表が多い（金）

EXACT5 = math.comb(F1, 5) / 2 ** F1              # 252/1024 = 0.2461
EXACT50 = math.comb(F2, 50) / 2 ** F2            # 0.0796


def lead(heads, n, scale):
    """表と裏の差を 0〜1 に（0.5＝同じ数）。マスの色に使う"""
    return np.clip(0.5 + (2 * np.asarray(heads) - n) / (2 * scale), 0, 1)


def ramp(frac):
    """0〜1（配列可）→ 色（BGRA の float 配列）"""
    frac = np.asarray(frac, float)
    xs = [s for s, _ in RAMP_STOPS]
    cs = np.array([bgra(c) for _, c in RAMP_STOPS], float)
    return np.stack([np.interp(frac, xs, cs[:, i]) for i in range(4)], -1)


# 乱数の種: 表示する%（四捨五入）が理論値の四捨五入と一致するものを選ぶ。統計は1万人全員から出す。
# 10回の結果は、100回投げたうちの最初の10回（追い打ちは同じ人がそのまま投げ続ける）
for SEED in range(1, 5000):
    rng = np.random.default_rng(SEED)
    FLIPS = rng.integers(0, 2, size=(N, F2), dtype=np.int8)        # 1＝表
    H10 = FLIPS[:, :F1].sum(1)
    H100 = FLIPS.sum(1)
    s5, s50 = (H10 == 5).mean(), (H100 == 50).mean()
    if pct(s5) == pct(EXACT5) and pct(1 - s5) == pct(1 - EXACT5) and pct(s50) == pct(EXACT50) \
            and H100.min() >= 25 and H100.max() <= 75:
        break
SIM5, SIM50 = float(s5), float(s50)
CUM = np.concatenate([np.zeros((N, 1), int), np.cumsum(FLIPS[:, :F1], 1)], 1)   # CUM[:, f] = f回目までの表


def _pick_a():
    """見本1: 表が3連続で始まるのに、終わってみればちょうど5回"""
    for i in range(N):
        s = FLIPS[i, :F1]
        if H10[i] == 5 and s[:3].sum() == 3 and s[3] == 0:
            return i
    raise SystemExit("見本1が見つからない")


PERSON_A = _pick_a()
PERSON_B = int(np.argmax(H10 == 8))                # 見本2: 表8回
SEQ_A = FLIPS[PERSON_A, :F1].tolist()
SEQ_B = FLIPS[PERSON_B, :F1].tolist()

# ---------- 時間割 ----------
# 2026-09-26 テンポの直し（ユーザー指摘「最初の2回で企画を理解できるか」「冒頭の1人目にもう少し時間を」）:
#   ・1人目は最初の5枚を0.85秒ずつ1枚ずつ回し（ルール説明）、ルールを1行出してから残り5枚を加速する
#   ・結果の札と合図は「0.5秒＋文字数÷6秒」以上出す（engine/pace.py で測る）
FLIP = 0.42
SLOW_N, SLOW_IV, FAST_IV = 5, 0.85, 0.32
A_TIMES = [i * SLOW_IV if i < SLOW_N else (SLOW_N - 1) * SLOW_IV + (i - SLOW_N + 1) * FAST_IV
           for i in range(F1)]            # i枚目（0始まり）を投げる時刻
B_IV = 0.16
T_A0 = note.Intro.T_GO                  # 冒頭の問題画面（約8秒）のあと
A_TIMES = [T_A0 + a for a in A_TIMES]   # 絶対時刻に
T_A_END = A_TIMES[-1] + FLIP
T_B0 = T_A_END + 2.4                    # 「表 ちょうど5回！」を読む時間
T_B1 = T_B0 + 0.3
B_TIMES = [T_B1 + i * B_IV for i in range(F1)]
T_B_END = B_TIMES[-1] + FLIP
T_BANNER = T_B_END + 2.3                # 「表 8回」を読む時間
T_M0 = T_BANNER + 1.8                   # 1万人モード開始（1投目）
FSTEP = 60 / 120                        # 1投ずつ、キックに合わせて
MFLIP = 0.2                             # 1万枚が一斉に回る時間
T_F10 = T_M0 + (F1 - 1) * FSTEP + MFLIP
T_HL = T_F10 + 0.45                     # ちょうど5回の人が光る
T_REV = T_HL + 0.4
T_FALL = T_HL + 1.9                     # 列へ崩れ落ちる
FALL_DUR = 1.6
T_FALL_END = T_FALL + FALL_DUR
T_P2 = T_FALL_END + 1.7                 # 追い打ち「100回なら？」
T_RUN2 = T_P2 + 1.5
RUN2_DUR = 1.5
T_RUN2_END = T_RUN2 + RUN2_DUR
T_HL2 = T_RUN2_END + 0.35
DURATION = T_HL2 + 3.8


def flips_done(t):
    """1万人モードで、いま何投目まで結果が出たか（コインが回りきった半分の時点で色が変わる）"""
    if t < T_M0:
        return 0
    return min(F1, int((t - T_M0 - MFLIP / 2) / FSTEP) + 1) if t >= T_M0 + MFLIP / 2 else 0


# ---------- 描画: 1人ぶん ----------
CR = 78                                  # コインの半径
COIN_XY = [(540 + (i % 5 - 2) * 172, 780 + (i // 5) * 175) for i in range(F1)]   # 2段目の字が右のボタン列（y>1000）にかからない高さ


def draw_deco(ctx, t, a):
    """冒頭の右上: コイン3枚がずっと回っている（1コマ目から「コインの話だ」と分かるように）"""
    for i, x in enumerate((630, 790, 950)):
        ph = t * 2.6 + i * 1.1
        c = math.cos(ph)
        heads = (int(ph / math.pi + 0.5) + i) % 2 == 0
        coin(ctx, x, 480 - 18 * abs(math.sin(ph)), 62, heads, abs(c), a)


INTRO = note.Intro(["コインを10回投げる。", "表がちょうど5回になる確率は？"], ["50%", f"{pct(EXACT5)}%", "10%"],
                   correct=1, msg="1万人で投げて確かめる", deco=draw_deco,
                   big=["コインを10回投げる。", "表がちょうど", "5回になる確率は？"],
                   rule=None)


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


def draw_person(ctx, t, seq, times, label, fade=1.0, first=True):
    text(ctx, label, 540, 670, 34, SUB, bold=False, alpha=fade)
    landed = 0
    heads = 0
    for i, res in enumerate(seq):
        x, y = COIN_XY[i]
        age = t - times[i]
        if age < 0:
            ctx.new_path()
            ctx.set_line_width(3)
            ctx.set_source_rgba(0.55, 0.6, 0.79, 0.35 * fade)
            ctx.arc(x, y, CR * 0.84, 0, 2 * math.pi)
            ctx.stroke()
            continue
        p = clamp01(age / FLIP)
        phase = 3 * math.pi * (1 - ease_out(p))          # 3回ひっくり返って、結果の面で止まる
        c = math.cos(phase)
        face = res if c >= 0 else 1 - res
        coin(ctx, x, y, CR, face, abs(c), fade, lift=90 * math.sin(math.pi * p))
        if p >= 1:
            landed += 1
            heads += res
            if age - FLIP < 0.3:                          # 着地のきらめき
                q = (age - FLIP) / 0.3
                ctx.set_line_width(5 * (1 - q) + 1)
                cc = hexrgb(HEAD if res else TAIL)
                ctx.set_source_rgba(cc[0], cc[1], cc[2], (1 - q) * fade)
                ctx.new_path()
                ctx.arc(x, y, CR + 6 + 30 * q, 0, 2 * math.pi)
                ctx.stroke()
    text(ctx, f"表 {heads}回", 400, 1130, 58, HEAD_RIM, alpha=fade)
    text(ctx, f"裏 {landed - heads}回", 690, 1130, 58, TAIL, alpha=fade)
    text(ctx, f"投げた回数 {max(1, sum(1 for a in times if a <= t))}/10", 540, 1200, 34, SUB,
         bold=False, alpha=fade)
    # ルールの1行（絵の読み方）。1人目の間は白、2人目は薄く
    if first:
        text(ctx, RULE, 540, 1425, 38, INK, alpha=fade)
    else:
        text(ctx, RULE, 540, 1425, 38, SUB, bold=False, alpha=fade)
    if landed == F1:
        age = t - (times[-1] + FLIP)
        a = ease_out((age - 0.1) / 0.25) * fade
        if heads == 5:
            note.sticky(ctx, "表 ちょうど5回！", 540, 1305, 58, "mint", a=a)
        else:
            note.sticky(ctx, f"表 {heads}回", 540, 1305, 58, "yellow", a=a, tilt=0.02)


RULE = "1人10回投げて、表の回数を数える"


# ---------- 描画: 1万人 ----------
GX0, GY0, PITCH, BGAP = 220, 670, 6, 4  # 10×10の束が10×10（1マス6px、束のすき間4px）。iPhone 対応で上を空けて小さく
_p = np.arange(N)
_b, _q = _p // 100, _p % 100
GRID_X = GX0 + (_b % 10) * (10 * PITCH + BGAP) + (_q % 10) * PITCH
GRID_Y = GY0 + (_b // 10) * (10 * PITCH + BGAP) + (_q // 10) * PITCH
BASE = 1320                              # 山の底
H1_X5, H1_SP, H1_PER, H1_P = 510, 70, 22, 3          # 10回: 列の間隔76px、1段18人、1マス4px（山の上に札を置くため低く）
H2_X50, H2_SP, H2_PER, H2_P = 528, 17, 5, 3          # 100回: 列の間隔17px、1段5人、1マス3px（山を低くして上に札）


def stack_xy(h, x_mid, sp, per, pitch, center):
    """表の回数 h の列に、下から詰める。並びは元のマスの位置の順（下の人から先に落ちる）"""
    x = np.zeros(N)
    y = np.zeros(N)
    order = np.lexsort((GRID_X, -GRID_Y))
    slot = np.zeros(N, int)
    counts = {}
    for i in order:
        k = int(h[i])
        slot[i] = counts.get(k, 0)
        counts[k] = slot[i] + 1
    colx = x_mid + (h - center) * sp - per * pitch / 2
    x = colx + (slot % per) * pitch
    y = BASE - (slot // per + 1) * pitch
    return x, y


HIST1_X, HIST1_Y = stack_xy(H10, H1_X5, H1_SP, H1_PER, H1_P, 5)
HIST2_X, HIST2_Y = stack_xy(H100, H2_X50, H2_SP, H2_PER, H2_P, 50)
FALL_DELAY = 0.45 * (GY0 + 640 - GRID_Y) / 640 + np.random.default_rng(3).uniform(0, 0.08, N)

RH, RW = 1000, W                          # 塗る範囲（y=400〜1400）
RY0 = 400


def sprite(size, width=None):
    """1マスの形。size 以上は丸いコイン、width を絞ると回転中の細いコイン"""
    width = size if width is None else width
    yy, xx = np.mgrid[0:size, 0:size]
    if size >= 6:
        m = ((xx + 0.5 - size / 2) / max(width / 2, 0.5)) ** 2 + ((yy + 0.5 - size / 2) / (size / 2)) ** 2 <= 1.05
    else:
        m = np.ones((size, size), bool)
    dy, dx = np.nonzero(m)
    return dy, dx


SPR = {w: sprite(5, w) for w in (5, 3, 1)}
SQ = {s: sprite(s) for s in (2, 3, 4, 5)}


def splat(xs, ys, cols, spr):
    buf = np.zeros((RH, RW, 4), np.uint8)
    xi = np.clip(np.round(xs).astype(int), 0, RW - 8)
    yi = np.clip(np.round(ys).astype(int) - RY0, 0, RH - 8)
    dy, dx = spr
    for a, b in zip(dy, dx):
        buf[yi + a, xi + b] = cols
    return buf


PAPER_C = np.array(bgra(PAPER), np.float32)


def dimmed(col, f):
    """紙の色へ寄せて薄くする（紙の上なので、暗くするより薄くするほうが「脇役」に見える）"""
    out = col.copy()
    out[:, :3] = (col[:, :3] * f + PAPER_C[:3] * (1 - f)).astype(np.uint8)
    return out


LIME_C = np.array(bgra(LIME), np.uint8)


def people_colors(t):
    """1万人の色。ちょうど半分の人が光ったあとは、黄緑とそれ以外（暗く）"""
    if t < T_P2 + 0.9:
        f = flips_done(t)
        col = ramp(lead(CUM[:, f], f, 5)).astype(np.uint8)
        if t >= T_HL:
            g = clamp01((t - T_HL) / 0.3)
            hit = H10 == 5
            col = dimmed(col, 1 - 0.6 * g)
            col[hit] = np.array(bgra(MARKER), np.uint8) if t < T_HL + 0.12 else LIME_C
        return col
    p = ease((t - T_RUN2) / RUN2_DUR)
    col = ramp(lead(H100, F2, 12)).astype(np.uint8)
    col = dimmed(col, 0.5 + 0.5 * p if t < T_HL2 else 0.5)
    if t >= T_HL2:
        col[H100 == 50] = np.array(bgra(MARKER), np.uint8) if t < T_HL2 + 0.12 else LIME_C
    return col


def people_layer(t):
    col = people_colors(t)
    if t < T_FALL:
        # 一斉に回る: 1投ごとに、コインが細くなってまた戻る
        w = 5
        if T_M0 <= t < T_F10:
            ph = (t - T_M0) % FSTEP
            if ph < MFLIP:
                w = [5, 3, 1, 1, 3, 5][min(5, int(ph / MFLIP * 6))]
        return splat(GRID_X, GRID_Y, col, SPR[w])
    if t < T_P2 + 0.9:
        p = np.clip((t - T_FALL - FALL_DELAY) / (FALL_DUR - 0.55), 0, 1)
        p = p * p * (3 - 2 * p)
        xs = GRID_X + (HIST1_X - GRID_X) * p
        ys = GRID_Y + (HIST1_Y - GRID_Y) * p ** 1.6
        spr = SPR[5] if t < T_FALL + 0.3 else SQ[2]        # 列に入ったら四角（すき間1px）
        return splat(xs, ys, col, spr)
    p = clamp01((t - T_RUN2) / RUN2_DUR)
    p = np.clip(p * 1.25 - FALL_DELAY * 0.4, 0, 1)
    p = p * p * (3 - 2 * p)
    xs = HIST1_X + (HIST2_X - HIST1_X) * p
    ys = HIST1_Y + (HIST2_Y - HIST1_Y) * p - 120 * np.sin(np.pi * p)
    return splat(xs, ys, col, SQ[2])


def ramp_legend(ctx, y, a):
    x0, x1 = 400, 680
    for i in range(64):
        c = ramp(i / 63)
        ctx.set_source_rgba(c[2] / 255, c[1] / 255, c[0] / 255, a)
        ctx.rectangle(x0 + (x1 - x0) * i / 64, y - 14, (x1 - x0) / 64 + 0.5, 28)
        ctx.fill()
    text(ctx, "裏が多い", x0 - 16, y, 36, TAIL, align="right", bold=False, alpha=a)
    text(ctx, "表が多い", x1 + 16, y, 36, HEAD_RIM, align="left", bold=False, alpha=a)


def draw_mode(ctx, t):
    buf = people_layer(t)
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, RW, RH, RW * 4)
    ctx.set_source_surface(surf, 0, RY0)
    ctx.paint()
    del surf

    a_grid = 1 - ease((t - T_FALL) / 0.3)
    if a_grid > 0:
        f = flips_done(t)
        text(ctx, f"{f}投目" if f else "1投目", 540, 1350, 54, INK, alpha=a_grid)
        ramp_legend(ctx, 1397, a_grid)
        if t < T_HL:
            text(ctx, "1マス＝1人　色＝そこまでの表と裏の差", 540, 1432, 30, INK, alpha=a_grid)
    a_h = ease((t - T_FALL - 0.8) / 0.4)
    if a_h > 0:
        two = t >= T_RUN2 + RUN2_DUR * 0.5
        ax = 1 - ease((t - T_RUN2) / 0.3) if not two else ease((t - T_RUN2 - RUN2_DUR * 0.5) / 0.3)
        a = a_h * ax
        if not two:
            for h in range(F1 + 1):
                col = LIME if h == 5 and t >= T_HL else SUB
                text(ctx, str(h), H1_X5 + (h - 5) * H1_SP, BASE + 30, 32, col, alpha=a)
            text(ctx, "表が出た回数（10回中）　1マス＝1人", 540, BASE + 80, 36, INK, alpha=a)
        else:
            for h in (30, 40, 50, 60, 70):
                col = LIME if h == 50 and t >= T_HL2 else SUB
                text(ctx, str(h), H2_X50 + (h - 50) * H2_SP, BASE + 30, 32, col, alpha=a)
            text(ctx, "表が出た回数（100回中）　1マス＝1人", 540, BASE + 80, 36, INK, alpha=a)

    if T_HL <= t < T_P2 + 0.3:
        a = ease_out((t - T_HL - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
        note.sticky(ctx, f"ちょうど5回は {pct(SIM5)}%", 540, 800, 62, "mint", a=a)
    if T_P2 <= t < T_RUN2 + 0.3:
        a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_RUN2) / 0.3))
        note.banner(ctx, "100回なら？", 540, 900, a=a, t_rel=t - T_P2)
    if t >= T_HL2:
        a = ease_out((t - T_HL2 - 0.15) / 0.3)
        note.sticky(ctx, f"100回なら ちょうど50回は {pct(SIM50)}%", 540, 760, 52, "mint", a=a, tilt=0.02)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def body(ctx, t):
    if t < T_A0:
        return
    if t < T_B0:
        fo = ease_out((t - T_A0) / 0.25) * (1 - ease((t - (T_B0 - 0.25)) / 0.25))
        draw_person(ctx, t, SEQ_A, A_TIMES, "1人目", fade=fo)
    elif t < T_BANNER:
        fi = ease((t - T_B0) / 0.25) * (1 - ease((t - (T_BANNER - 0.2)) / 0.2))
        draw_person(ctx, t, SEQ_B, B_TIMES, "2人目", fade=fi, first=False)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万人で投げる", 540, 950, a=a, t_rel=t - T_BANNER)
    else:
        draw_mode(ctx, t)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def ting(freq=2400, dur=0.35):
    """コインをはじく音（金属っぽい、少し揺れる）"""
    t = _t(dur)
    x = np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t)
    return x * np.exp(-t * 14) * (1 + 0.3 * np.sin(2 * np.pi * 30 * t)) * 0.5


def clink(freq, dur=0.18):
    """着地のチャリン"""
    t = _t(dur)
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 3.1 * t)) * np.exp(-t * 30)


def sand(dur):
    """1万人が崩れ落ちるザーッ"""
    t = _t(dur)
    n = np.random.default_rng(5).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(8) / 8, mode="same")
    return n * np.sin(np.pi * t / dur) ** 1.5 * 0.5


def person_audio(mx, seq, times, vol):
    h = 0
    for i, res in enumerate(seq):
        tt = times[i]
        mx.add(tt, ting(2300 + 60 * i), 0.4 * vol)
        h += res
        land = tt + FLIP
        mx.add(land, clink(1200 if res else 700), 0.5 * vol)
        mx.add(land, blip(523.3 * 2 ** (h / 12) if res else 330, 0.12), (0.45 if res else 0.25) * vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(123.5, 185.0, 246.9, 311.1)), 1.0, bgm=True)
    INTRO.audio(mx)
    for k in range(9):                        # 冒頭の右上のコイン: ときどき小さくチリン
        mx.add(0.05 + k * 0.85, ting(2500 + 90 * (k % 3), 0.25), 0.18)
    person_audio(mx, SEQ_A, A_TIMES, 1.0)
    ta = T_A_END + 0.1
    mx.add(ta, bell(1046.5), 0.7)
    mx.add(ta, chord([523.3, 659.3, 784.0], 1.2), 0.5)
    person_audio(mx, SEQ_B, B_TIMES, 0.8)
    tb = T_B_END + 0.1
    mx.add(tb, thump(), 0.6)
    mx.add(tb, blip(392, 0.3), 0.5)
    mx.add(T_BANNER, riser(0.9), 0.6)
    beat(mx, T_M0, T_F10 + 0.1, bpm=120, vol=0.55)
    for f in range(F1):
        tt = T_M0 + f * FSTEP
        mx.add(tt, ting(2600, 0.25), 0.35)
        mx.add(tt + MFLIP / 2, shimmer(200, 0.25, seed=f), 0.7)
    mx.add(T_HL, shimmer(300, 0.5), 1.0)
    mx.add(T_HL + 0.2, thump(), 0.8)
    mx.add(T_HL + 0.2, bell(784.0), 0.6)
    mx.add(T_HL + 0.2, chord([220.0, 277.2, 329.6], 1.6), 0.6)
    mx.add(T_FALL, sand(FALL_DUR), 0.9)
    for i in range(14):
        mx.add(T_FALL + 0.1 + i * 0.09, tick(1800 - 70 * i, 0.03), 0.3)
    mx.add(T_FALL_END - 0.2, thump(), 0.6)
    mx.add(T_P2, riser(0.8), 0.5)
    beat(mx, T_RUN2, T_RUN2_END, bpm=150, vol=0.45)
    mx.add(T_RUN2, whoosh(RUN2_DUR), 0.6)
    mx.add(T_HL2, shimmer(200, 0.4), 0.9)
    mx.add(T_HL2 + 0.15, thump(), 0.8)
    mx.add(T_HL2 + 0.15, chord([220.0, 261.6, 329.6], 1.8), 0.6)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 1人目={PERSON_A} {''.join('表' if v else '裏' for v in SEQ_A)} "
          f"2人目={PERSON_B} {''.join('表' if v else '裏' for v in SEQ_B)} 長さ={DURATION:.1f}秒")
    print(f"  100回の表の回数: 最小{H100.min()} 最大{H100.max()}  10回で表5回の列 {int((H10 == 5).sum())}人"
          f"  100回で50回の列 {int((H100 == 50).sum())}人")
    check_answers([
        ("10回でちょうど5回", SIM5, EXACT5, 0.012),
        ("100回でちょうど50回", SIM50, EXACT50, 0.008),
        ("10回で4〜6回", float(((H10 >= 4) & (H10 <= 6)).mean()),
         sum(math.comb(10, k) for k in (4, 5, 6)) / 1024, 0.015),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 1.4, 3.2, 5.0, 7.95, T_A0 + 0.5, T_A0 + 3.0, A_TIMES[6] + 0.2, T_A_END + 0.6, T_B1 + 1.0, T_B_END + 0.7, T_BANNER + 0.5,
                      T_M0 + 0.35, T_M0 + 3.35, T_HL + 1.0, T_FALL + 0.8, T_FALL_END + 1.0,
                      T_P2 + 0.5, T_RUN2 + 0.7, T_HL2 + 1.5, DURATION - 0.2], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
