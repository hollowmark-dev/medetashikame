"""クラス35人。同じ誕生日の2人がいる確率は？（誕生日のパラドックス）

モデル: 1クラス35人、誕生日は365日のどれも同じ確率（2月29日は考えない）。1万クラスつくる。
直感の外れ: 「35人 ÷ 365日 ＝ 約10%」（A）。正解は 1 − Π_{k=0}^{34}(365−k)/365 ≈ 81.4%（C）。
ひねり: 半分を超えるのは何人から？ → 23人（P(23)=50.7%、P(22)=47.6%）。

構成（「データで語る棒人間」から取り入れた5つ。CHANNEL.md）:
- 0秒目から上半分が動く。カレンダー（12か月×日の365マス）に、生徒が1人ずつ誕生日の印を打っていく
- 同じ日に2人目が来た瞬間、その2人に寄る（スポットライト）「同じ誕生日！」
- 1万クラス（100×100のマス）。赤＝同じ誕生日の2人がいたクラス、青＝いなかったクラス。
  「同じ誕生日がいるクラス」と「35人÷365日＝約10%（よくある直感）」を並べて出しっぱなし
- ひねり「何人で半分を超える？」→ 同じ1万クラスを、先頭の10人・20人・22人・23人までで塗り直す
- 現象の名前「誕生日のパラドックス」→ 締めの問いかけ（答えは概要欄）

照合: 100万クラスで P(35)・P(23)・P(22) vs 理論、画面の % が小数1桁で理論と一致（81.4% と 50.7%）。
23人が「半分を超える最小の人数」であること。

絵（生徒）はすべてコードで描いている（素材ファイルは使わない）。
"""
import math
import sys
from collections import Counter
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01, ease,
                         ease_out, fill, hexrgb, pad, render, riser, shimmer, text, thump, tick,
                         whoosh, _t)
from engine.parts import bgra, check_true, loop_back, r1, stills

note.use()
note.DATE = "10.7"                                # 日付欄（公開予定日）

SLUG = "birthday-35nin"
N, M, D = 10000, 35, 365
HAS, NONE = "#e0545e", "#5aa0d8"                  # 同じ誕生日がいたクラス（赤系）／いなかったクラス（青系）
SEED = 2076   # 画面の回: 35人の % と 23人の % が小数1桁で理論と一致する種。8000個の種を試した中で、
              # 10・20・22・30人の値も理論にいちばん近いもの（探し方は check の欄で再確認する）

MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MSTART = np.cumsum([0] + MDAYS[:-1])


def p_exact(n):
    """n人で、同じ誕生日の2人がいる確率"""
    return 1 - math.prod((D - k) / D for k in range(n))


def first_collision(b):
    """各クラスで、何人目に初めて前の誰かと誕生日がかぶったか（1始まり）。かぶりなしは M+1"""
    n, m = b.shape
    f = np.full(n, m + 1)
    for j in range(1, m):
        hit = (b[:, :j] == b[:, j:j + 1]).any(1)
        f = np.where(hit & (f > m), j + 1, f)
    return f


def simulate(seed, n=N):
    rng = np.random.default_rng(seed)
    b = rng.integers(0, D, size=(n, M)).astype(np.int16)
    return b, first_collision(b)


BDAY, FIRSTC = simulate(SEED)
HAS_ANY = FIRSTC <= M


def p_sim(n):
    return float((FIRSTC <= n).mean())


# ---------- 冒頭の見本のクラス ----------
# 35人のうち、同じ誕生日のかぶりがちょうど1組。最初のかぶりは13〜15人目。日付が真ん中あたり
def _good(c):
    if not 13 <= FIRSTC[c] <= 15:
        return False
    days = BDAY[c]
    if len(set(days.tolist())) != M - 1:             # かぶりが1組だけ（3人同じ日もなし）
        return False
    d = [k for k, v in Counter(days.tolist()).items() if v == 2][0]
    return 90 <= d <= 280


SAMPLE = next(c for c in range(N) if _good(c))
S_DAYS = BDAY[SAMPLE].astype(int)
CI = int(FIRSTC[SAMPLE]) - 1                         # かぶった2人目（0始まり）
PD = int(S_DAYS[CI])                                 # かぶった日
PI = int(np.where(S_DAYS[:CI] == PD)[0][0])          # 1人目（0始まり）


def month_of(d):
    return int(np.searchsorted(MSTART, d, side="right")) - 1


def date_jp(d):
    m = month_of(d)
    return f"{m + 1}月{d - MSTART[m] + 1}日"


# ---------- 時間割 ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
IV = 0.24                                          # 1人ずつ来る間隔（かぶるまで）
POP = 0.34                                         # 生徒の人形が出て、点に変わるまで
S_T = [0.05 + j * IV for j in range(CI + 1)]       # かぶるまでの生徒が来る時刻
T_COLL = S_T[CI] + 0.2                             # 2人目が着いた（輪が光る）
T_SPOT = T_COLL + 0.45                             # その2人に寄る
SPOT_DUR = 2.5
T_FILL = T_SPOT + SPOT_DUR + 0.2                   # 残りの生徒が一気に来る
FILL_IV = 0.095
for _j in range(CI + 1, M):
    S_T.append(T_FILL + (_j - CI - 1) * FILL_IV)
T_FILL_END = S_T[-1] + 0.3
T_GO = max(T_FILL_END + 1.3, T_CD[-1] + 1.4)
T_BANNER = T_GO
T_M0 = T_BANNER + 2.2                              # 1万クラス
M_DUR = 5.5
T_M_END = T_M0 + M_DUR
T_REV = T_M_END + 0.4
T_TWB = T_M_END + 3.4                              # 「では、何人で半分を超える？」
T_TW0 = T_TWB + 2.9                                # 人数を増やしていく
TW_N = [10, 20, 22, 23]
TW_T = [T_TW0 + x for x in (0.0, 0.9, 1.8, 2.7)]
T_HALF = T_TW0 + 3.1                               # 「23人で50.7%、半分を超える！」
T_NAME = T_TW0 + 5.5                               # 「誕生日のパラドックス」
T_Q = T_NAME + 3.5
DURATION = T_Q + 4.2


def m_count(t):
    if t < T_M0:
        return 0
    return int(N * clamp01((t - T_M0) / M_DUR) ** 1.4)


# ---------- 絵（ペン描き風。コードで描く） ----------
BODY = ["#bfe0f5", "#cfe8b8", "#fde9a8", "#f7cfd8"]
DOTC = ["#7fb6e0", "#9cce7a", "#f0c45a", "#e89ab0"]
SKIN, HAIR = "#fff1dd", "#2a3a5a"


def _blob(ctx, cx, cy, rx, ry, seed, amp=0.04):
    n = 30
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        w = 1 + amp * math.sin(3 * a + seed) + amp * 0.6 * math.sin(5 * a + seed * 1.7)
        x, y = cx + rx * w * math.cos(a), cy + ry * w * math.sin(a)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()


def _limb(ctx, x0, y0, x1, y1, w, col, a, lw):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(w + 2 * lw)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def kid(ctx, cx, by, h, a=1.0, v=0, arms="down", face="smile"):
    """生徒の絵。足もとの中央 (cx, by)、高さ h。紺のペンの線＋うすい塗り（絵柄の見本 style1_doodle）"""
    if a <= 0 or h <= 0:
        return
    lw = max(1.4, h * 0.02)
    body = BODY[v % len(BODY)]
    sd = v * 1.3 + 0.5
    # 足
    for s in (-1, 1):
        _limb(ctx, cx + s * 0.07 * h, by - 0.30 * h, cx + s * 0.085 * h, by - 0.05 * h, 0.07 * h, "#a9c9e8", a, lw)
        ctx.set_source_rgba(*hexrgb("#ffffff", a))
        _blob(ctx, cx + s * 0.10 * h, by - 0.025 * h, 0.07 * h, 0.032 * h, sd + s)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(lw)
        ctx.stroke()
    # うで
    if arms == "cheer":
        pts = [(-1, (-0.27, -0.88)), (1, (0.27, -0.88))]
    elif arms == "up1":
        pts = [(-1, (-0.22, -0.36)), (1, (0.27, -0.88))]
    else:
        pts = [(-1, (-0.22, -0.36)), (1, (0.22, -0.36))]
    for s, (ax, ay) in pts:
        _limb(ctx, cx + s * 0.14 * h, by - 0.58 * h, cx + ax * h, by + ay * h,
              0.06 * h, body, a, lw)
    # 胴（パーカー）
    ctx.set_source_rgba(*hexrgb(body, a))
    core.rrect(ctx, cx - 0.16 * h, by - 0.63 * h, 0.32 * h, 0.37 * h, 0.08 * h)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(lw)
    ctx.stroke()
    # 頭
    hy, hr = by - 0.80 * h, 0.175 * h
    ctx.set_source_rgba(*hexrgb(SKIN, a))
    _blob(ctx, cx, hy, hr, hr * 1.04, sd, 0.03)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(lw)
    ctx.stroke()
    # 髪
    ctx.set_source_rgba(*hexrgb(HAIR, a))
    ctx.new_path()
    ctx.arc(cx, hy, hr * 1.05, math.pi * 0.98, math.pi * 2.02)
    ctx.line_to(cx + hr * 0.9, hy - hr * 0.25)
    ctx.line_to(cx + hr * 0.2, hy - hr * 0.55)
    ctx.line_to(cx - hr * 0.5, hy - hr * 0.3)
    ctx.line_to(cx - hr * 1.0, hy - hr * 0.1)
    ctx.close_path()
    ctx.fill()
    if v % 2 == 1:                                    # おかっぱ（横の髪）
        for s in (-1, 1):
            ctx.new_path()
            ctx.arc(cx + s * hr * 0.98, hy + hr * 0.15, hr * 0.28, 0, 2 * math.pi)
            ctx.fill()
    # 顔
    ctx.set_source_rgba(*hexrgb(INK, a))
    for s in (-1, 1):
        ctx.new_path()
        ctx.arc(cx + s * hr * 0.38, hy + hr * 0.12, max(1.2, hr * 0.1), 0, 2 * math.pi)
        ctx.fill()
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.new_path()
    if face == "smile":
        ctx.arc(cx, hy + hr * 0.3, hr * 0.32, math.pi * 0.15, math.pi * 0.85)
        ctx.stroke()
    else:
        ctx.arc(cx, hy + hr * 0.5, hr * 0.14, 0, 2 * math.pi)
        ctx.stroke()


# ---------- カレンダー（冒頭の上半分。画面の座標） ----------
CX0, CY0 = 152, 452                                # 1月1日のマスの左上
CW, CHT, PY = 27, 28, 33                           # マスの幅・高さ、行の間隔
_CAL = None


def cell_xy(d):
    m = month_of(d)
    return CX0 + (d - MSTART[m]) * CW + CW / 2, CY0 + m * PY + CHT / 2


def _calendar_surface():
    global _CAL
    if _CAL is None:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        for m in range(12):
            for k in range(MDAYS[m]):
                x, y = CX0 + k * CW, CY0 + m * PY
                c.set_source_rgba(1, 1, 1, 0.6)
                c.rectangle(x + 1, y + 1, CW - 3, CHT - 2)
                c.fill()
                c.set_source_rgba(*hexrgb(PENCIL, 0.55))
                c.set_line_width(1.3)
                c.rectangle(x + 1, y + 1, CW - 3, CHT - 2)
                c.stroke()
        _CAL = s
    return _CAL


def draw_calendar(ctx, t, a):
    ctx.set_source_surface(_calendar_surface(), 0, 0)
    ctx.paint_with_alpha(a)
    for m in range(12):
        text(ctx, f"{m + 1}月", 146, CY0 + m * PY + CHT / 2, 24, PENCIL, align="right", bold=False, alpha=a)
    # 生徒たち
    arrived = [j for j in range(M) if S_T[j] <= t]
    pair_on = t >= T_COLL
    for j in arrived:
        d = int(S_DAYS[j])
        x, y = cell_xy(d)
        age = t - S_T[j]
        if pair_on and d == PD:
            x += -6 if j == PI else 6
        figure = j <= CI
        t_dot = 0.2 if figure else 0.0
        r = 10.5 * ease_out((age - t_dot) / 0.12) if age > t_dot else 0.0
        if j > CI:
            r *= 1 + 0.25 * max(0.0, 1 - (age - 0.12) / 0.15) if age < 0.27 else 1
        if j in (PI, CI) and pair_on:
            r = 8.5
        if r > 0:
            ctx.set_source_rgba(*hexrgb(DOTC[j % 4], a))
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
            ctx.set_line_width(1.6)
            ctx.stroke()
        if figure and age < POP:                      # 人形がぽんと出て、点に縮む
            s = ease_out(age / 0.12) * (1 - ease((age - 0.2) / 0.14))
            if s > 0:
                kid(ctx, x, y + CHT / 2 - 1, 56 * s, a, v=j, arms="cheer" if age > 0.1 else "down")
    # かぶった印（赤ペンの輪）
    if pair_on:
        x, y = cell_xy(PD)
        p = clamp01((t - T_COLL) / 0.25)
        note.pen_circle(ctx, x, y, 24, 20, RED, seed=4, width=4, progress=p, alpha=a)
    # 数字（カレンダーの上）
    k = len(arrived)
    pairs = 1 if t >= T_COLL else 0
    sp = 1 - ease_out((t - T_SPOT) / 0.2) + ease_out((t - (T_SPOT + SPOT_DUR)) / 0.3)    # 寄っている間は数字を消す
    c_a = a * clamp01(sp)
    text(ctx, f"{k}人目", 290, 402, 34, INK, alpha=c_a)
    text(ctx, f"同じ誕生日の2人  {pairs}組", 720, 402, 32, RED if pairs else PENCIL, alpha=c_a)


def draw_spot(ctx, t, a):
    """かぶった2人に寄る（スポットライト）"""
    p = ease_out((t - T_SPOT) / 0.3) * (1 - ease((t - (T_SPOT + SPOT_DUR)) / 0.3))
    if p <= 0:
        return
    s = (0.75 + 0.25 * p)
    x0, y0, w, h = 148, 424, 862, 428
    ctx.set_source_rgba(*hexrgb(PAPER, 0.96 * p * a))
    core.rrect(ctx, x0, y0, w, h, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(MARKER, 0.55 * p * a))             # 2人の足もとに光
    g = cairo.RadialGradient(575, 700, 20, 575, 700, 330)
    g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.55 * p * a)
    g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
    ctx.set_source(g)
    ctx.rectangle(x0, y0, w, h)
    ctx.fill()
    kid(ctx, 440, 850, 255 * s, a * p, v=PI, arms="up1", face="smile")
    kid(ctx, 710, 850, 255 * s, a * p, v=CI + 1, arms="cheer", face="smile")
    text(ctx, "＝", 575, 735, 84, RED, alpha=a * p)
    note.sticky(ctx, f"{date_jp(PD)}生まれ\n同じ誕生日！", 575, 502, 44, "yellow", fg=RED, a=a * p, tilt=0.012)


BIG_Q1, BIG_Q2 = "クラス35人。", "同じ誕生日の2人がいる確率は？"
DETAIL = "誕生日は365日のどれも同じくらい"


class BIntro(note.Intro):
    """この回だけの冒頭。0秒目からカレンダーに生徒が来て、同じ日に2人目が来たらその2人に寄る"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_calendar(ctx, t, a)
        draw_spot(ctx, t, a)
        w = core.text_width(BIG_Q2, 56)
        text(ctx, BIG_Q1, 570, 898, 56, INK, alpha=a)
        text(ctx, BIG_Q2, 570, 962, 56, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 1002, 570 + w / 2 + 6, 996, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 575, 1062, 34, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1155 + i * 88
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 58, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 775, 1150, 52, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 785, 1267, 72, 68, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(785, 1267)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 106, INK, alpha=a)
            ctx.restore()


INTRO = BIntro(["クラス35人。", "同じ誕生日の2人がいる確率は？"],
               ["約10%", "約40%", "約80%"], correct=2, msg="", rule=None)

# ---------- 1万クラス（本体の座標） ----------
CELL, BGAP = 6, 2
GW = 100 * CELL + 9 * BGAP
GX0, GY0 = 540 - GW // 2, 680
_ix = np.arange(N)
_cx = (_ix % 100) * CELL + (_ix % 100) // 10 * BGAP
_cy = (_ix // 100) * CELL + (_ix // 100) // 10 * BGAP
ORDER = np.random.default_rng(SEED + 3).permutation(N)          # クラスが画面に現れる順
_perm = np.random.default_rng(SEED + 4).permutation(N)          # クラスごとのマスの位置
POS_X, POS_Y = _cx[_perm], _cy[_perm]


def grid_surface(n, nn):
    """画面に出ているクラスは n 個。先頭の nn 人までで、同じ誕生日がいたクラスを赤に"""
    img = np.zeros((GW, GW, 4), np.uint8)
    shown = ORDER[:n]
    has = FIRSTC[shown] <= nn
    has_c, none_c = np.array(bgra(HAS), np.uint8), np.array(bgra(NONE), np.uint8)
    xs, ys = POS_X[shown], POS_Y[shown]
    for k in range(CELL - 1):
        for j in range(CELL - 1):
            img[ys + k, xs + j] = np.where(has[:, None], has_c, none_c)
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW, GW, GW * 4), img


def nn_at(t):
    """いま画面に出している人数と、切り替えた時刻"""
    if t < T_TW0:
        return M, None
    nn, tc = TW_N[0], TW_T[0]
    for n_, t_ in zip(TW_N, TW_T):
        if t >= t_:
            nn, tc = n_, t_
    return nn, tc


def draw_grid(ctx, t, dim=0.0):
    n = m_count(t)
    nn, tc = nn_at(t)
    al = 1 - dim * 0.4
    if tc is not None and t - tc < 0.3 and nn != TW_N[0]:       # 塗り直しは上から順に
        prev = TW_N[TW_N.index(nn) - 1]
        s0, k0 = grid_surface(N, prev)
        s1, k1 = grid_surface(N, nn)
        ctx.set_source_surface(s0, GX0, GY0)
        ctx.paint_with_alpha(al)
        ctx.save()
        ctx.rectangle(GX0, GY0, GW, GW * clamp01((t - tc) / 0.3))
        ctx.clip()
        ctx.set_source_surface(s1, GX0, GY0)
        ctx.paint_with_alpha(al)
        ctx.restore()
    else:
        if tc is not None and nn == TW_N[0] and t - tc < 0.3:   # 35人 → 10人
            s0, k0 = grid_surface(N, M)
            s1, k1 = grid_surface(N, nn)
            ctx.set_source_surface(s0, GX0, GY0)
            ctx.paint_with_alpha(al)
            ctx.save()
            ctx.rectangle(GX0, GY0, GW, GW * clamp01((t - tc) / 0.3))
            ctx.clip()
            ctx.set_source_surface(s1, GX0, GY0)
            ctx.paint_with_alpha(al)
            ctx.restore()
        else:
            surf, _k = grid_surface(n if tc is None else N, nn)
            ctx.set_source_surface(surf, GX0, GY0)
            ctx.paint_with_alpha(al)
    shown = ORDER[:n]
    if tc is None:
        v = (FIRSTC[shown] <= M).mean() * 100 if n else 0.0
        right_l, right_v, right_c = "直感 35人÷365日", "約10%", INK
    else:
        v = p_sim(nn) * 100
        right_l, right_v, right_c = "クラスの人数", f"{nn}人", INK
    text(ctx, "同じ誕生日がいるクラス", 330, 1362, 28, INK, bold=False)
    text(ctx, f"{v:.1f}%" if (n or tc is not None) else "—", 330, 1410, 48, HAS)
    text(ctx, right_l, 715, 1362, 28, INK, bold=False)
    text(ctx, right_v, 715, 1410, 48, right_c)
    note.legend(ctx, [(HAS, "同じ誕生日の2人がいた"), (NONE, "いなかった")], 1322, 28)


def body(ctx, t):
    if t < T_BANNER:
        return
    if t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万クラスでためす", 540, 950, a=a, t_rel=t - T_BANNER)
        return
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    dim = clamp01((t - T_M_END) / 0.4) if (t < T_TW0 and t >= T_M_END) else 0.0
    if T_HALF <= t < T_NAME:
        dim = 1.0
    if t >= T_NAME:
        dim = 1.0
    draw_grid(ctx, t, dim)
    if T_M_END <= t < T_TWB + 0.3:
        a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - ease((t - T_TWB) / 0.3))
        note.sticky(ctx, f"1万クラスのうち {(FIRSTC <= M).mean() * 100:.1f}% で\n同じ誕生日の2人がいた",
                    540, 960, 54, "yellow", a=a)
    if T_TWB <= t < T_TW0 + 0.3:
        a = ease_out((t - T_TWB) / 0.25) * (1 - ease((t - T_TW0) / 0.3))
        note.banner(ctx, "では、何人で半分を超える？", 540, 960, a=a, t_rel=t - T_TWB, size=58)
    if T_HALF <= t < T_NAME:
        a = ease_out((t - T_HALF) / 0.3) * (1 - ease((t - (T_NAME - 0.3)) / 0.3))
        note.sticky(ctx, f"{TW_N[-1]}人で {p_sim(TW_N[-1]) * 100:.1f}%\n半分を超える！", 540, 960, 62,
                    "pink", fg=RED, a=a, tilt=-0.015)
    if t >= T_NAME and q < 1:
        b = ease_out((t - T_NAME) / 0.3) * (1 - q)
        note.sticky(ctx, "これを「誕生日のパラドックス」と呼ぶ", 540, 960, 46, "mint", a=b, tilt=-0.015)
    if q > 0:
        note.sticky(ctx, "365日もあるのに\nなんで35人でこんなにかぶるの？", 540, 900, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 540, 1095, 50, "pink", fg=RED, a=r, tilt=0.025)


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
PENTA = [392.0, 440.0, 523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5, 1568.0, 1760.0]


def dingdong(dur=0.5):
    """かぶった！（上がる2音）"""
    t = _t(dur)
    f = np.where(t < 0.12, 660, 990)
    env = np.where(t < 0.12, np.exp(-t * 20), np.exp(-(t - 0.12) * 7))
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * env * 0.8


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 293.7, 370.0)), 1.0, bgm=True)
    INTRO.audio(mx)
    for j, t0 in enumerate(S_T):
        if j == CI:
            continue
        mx.add(t0, blip(PENTA[month_of(S_DAYS[j])], 0.1), 0.3 if j < CI else 0.18)
    mx.add(T_COLL, dingdong(), 0.8)
    mx.add(T_COLL, thump(0.25), 0.4)
    mx.add(T_SPOT, bell(880.0, 1.0), 0.4)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    mx.add(T_M0, shimmer(400, M_DUR, seed=5), 0.35)
    mx.add(T_M_END, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(T_TWB, riser(0.8), 0.4)
    for k, t0 in enumerate(TW_T):
        mx.add(t0, whoosh(0.35), 0.25)
        mx.add(t0, blip(523.3 * (1.122 ** k), 0.15), 0.45)
    mx.add(T_HALF, bell(1046.5), 0.55)
    mx.add(T_HALF, chord([523.3, 659.3, 784.0], 1.6), 0.4)
    mx.add(T_NAME, chord([392.0, 493.9, 587.3], 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


def big_check(n_class=1_000_000, chunk=100_000):
    """100万クラス。先頭の n 人までで同じ誕生日がいる割合"""
    rng = np.random.default_rng(12345)
    cnt = {35: 0, 23: 0, 22: 0}
    for _ in range(n_class // chunk):
        b = rng.integers(0, D, size=(chunk, M)).astype(np.int16)
        for n in cnt:
            s = np.sort(b[:, :n], axis=1)
            cnt[n] += int((s[:, 1:] == s[:, :-1]).any(1).sum())
    return {n: v / n_class for n, v in cnt.items()}


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    big = big_check()
    print(f"seed={SEED} 画面の回: " + " ".join(f"{n}人={p_sim(n) * 100:.1f}%(理論{p_exact(n) * 100:.1f}%)"
                                                for n in (10, 20, 22, 23, 30, 35)))
    print(f"見本のクラス={SAMPLE} 同じ誕生日={date_jp(PD)} {PI + 1}人目と{CI + 1}人目 長さ={DURATION:.1f}秒")
    half = next(n for n in range(1, M + 1) if p_exact(n) > 0.5)
    check_answers([
        ("100万クラス: 35人で同じ誕生日がいる", big[35], p_exact(35), 0.002),
        ("100万クラス: 23人で同じ誕生日がいる", big[23], p_exact(23), 0.002),
        ("100万クラス: 22人で同じ誕生日がいる", big[22], p_exact(22), 0.002),
        ("画面の回: 35人（%・小数1桁）", r1(p_sim(35) * 100), r1(p_exact(35) * 100), 0),
        ("画面の回: 23人（%・小数1桁）", r1(p_sim(23) * 100), r1(p_exact(23) * 100), 0),
        ("画面の回: 22人（%・小数1桁）", r1(p_sim(22) * 100), r1(p_exact(22) * 100), 0),
        ("画面の回: 20人（%）", p_sim(20) * 100, p_exact(20) * 100, 0.5),
        ("画面の回: 10人（%）", p_sim(10) * 100, p_exact(10) * 100, 0.5),
        check_true("半分を超える最小の人数は23人", half == 23, f"（P(22)={p_exact(22):.4f} P(23)={p_exact(23):.4f}）"),
        check_true("よくある直感 35÷365 は約10%", abs(M / D - 0.10) < 0.01, f"（{M / D:.4f}）"),
        check_true("見本のクラスはかぶりがちょうど1組", len(set(S_DAYS.tolist())) == M - 1),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 0.9, 2.5, T_COLL + 0.1, T_SPOT + 0.9, T_FILL + 0.8, T_CD[3] + 0.3, T_GO - 0.5,
                      T_BANNER + 0.6, T_M0 + 2.0, T_M_END + 1.0, T_TWB + 0.8, TW_T[0] + 0.5, TW_T[2] + 0.6,
                      T_HALF + 1.0, T_NAME + 1.0, T_Q + 2.0], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
