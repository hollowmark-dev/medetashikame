"""1万人の町にゾンビが1体。ゾンビは1日に1人かむ。全員ゾンビになるまで何日？

ルール: 毎日、ゾンビ1体につき1人を町の中からでたらめに選んでかむ（自分以外。すでにゾンビの人をかんだら空振り）。
かまれた人は次の日からゾンビになって、同じようにかむ。
直感の外れ: 「1日1人だから1万日 ≒ 27年」（C）。かまれた人もかむので、はじめはほぼ倍々（2^13 = 8192）。
最後は、ほとんどがゾンビの中で、かまれずに残る人が毎日およそ e 分の1 ずつ減っていくので少し長引く。
1万人で400回まわした中央値は23日（21〜31日）。正解は A「約1か月」（400回とも3〜5週間）。

見本: 36人の町（6×6の顔）。かむ線を引いて、空振り（ゾンビをかむ）も見せる → 1万人の町（100×100のマス）。
2026-10-02 スワイプ対策で冒頭を作り直した（案1・2・4。時間割のところに詳細）。見本はカウントダウンの間に走る。
締め: 「1日1人しか かまないのに、なんで27年もかからないの？」→ 答えは概要欄。

照合（check_answers）:
- 1日ごとの「新しくかまれた人」の合計が、理論の期待値 Σ H(1 − (1 − 1/(N−1))^Z) と一致すること
- はじめの数日は倍々（5日目のゾンビの平均が理論の期待値と一致）
- 画面の回（乱数の種）の日数が、400回の中央値と同じであること

2026-10-02 ユーザー「2本新作作成お願い」。案出し（Fable との合議）の2番。アリが「気持ち悪い」で没になったので、
ゾンビは怖くない丸い顔で描く（血や傷は描かない）。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, shimmer, text, thump,
                         tick, whoosh, _t)
from engine.parts import bgra, loop_back, stills

note.use()
note.DATE = "10.4"                                # 日付欄（公開予定日）

SLUG = "zombie-10000"
N = 10000
S_N = 36
SKIN, SKIN_D = "#f4c9a2", "#c98f62"               # 人間
ZOMB, ZOMB_D = "#8cc768", "#4f8a3a"               # ゾンビ（明るい黄緑。怖くしない）


def outbreak(n, rng):
    """day_of[i] ＝ i がゾンビになった日（0 は最初の1体）。bites[d] ＝ d日目の (かんだ人, かまれた人) の並び"""
    day_of = np.full(n, -1)
    day_of[0] = 0
    bites = [None]
    d = 0
    while (day_of < 0).any():
        d += 1
        z = np.flatnonzero(day_of >= 0)
        tgt = rng.integers(0, n - 1, len(z))
        tgt = tgt + (tgt >= z)                     # 自分はかまない
        bites.append((z, tgt))
        new = np.unique(tgt[day_of[tgt] < 0])
        day_of[new] = d
    return day_of, bites


def zombies_by_day(day_of, days):
    return np.array([(day_of <= d).sum() for d in range(days + 1)])


# 400回まわして、日数の分布をとる（照合にも使う）
_rng = np.random.default_rng(2026)
RUNS = [outbreak(N, _rng) for _ in range(400)]
DAYS_ALL = np.array([int(r[0].max()) for r in RUNS])
MED_DAYS = int(np.median(DAYS_ALL))
HALF_ALL = np.array([int(np.argmax(zombies_by_day(r[0], r[0].max()) >= N / 2)) for r in RUNS])
MED_HALF = int(np.median(HALF_ALL))

# 画面の回: 日数も「半分を超えた日」も中央値どおりのもの
for SEED in range(1, 5000):
    DAY_OF, BITES = outbreak(N, np.random.default_rng(SEED))
    DAYS = int(DAY_OF.max())
    ZC = zombies_by_day(DAY_OF, DAYS)
    HALF = int(np.argmax(ZC >= N / 2))
    if DAYS == MED_DAYS and HALF == MED_HALF:
        break

# 見本の36人: 8日で全員（36人の町の、よくある日数）
for S_SEED in range(1, 5000):
    S_DAY, S_BITES = outbreak(S_N, np.random.default_rng(100000 + S_SEED))
    if S_DAY.max() == 8 and any((S_DAY[S_BITES[d][1]] < d).any() for d in (3, 4)):   # 3〜4日目に空振りが見える回
        break
S_DAYS = int(S_DAY.max())

# ---------- 時間割 ----------
# 2026-10-02 スワイプ対策（ユーザーと Fable の案1・2・4）:
#   1. 0秒目から画面の上半分に、大きなゾンビと人間の追いかけっこ（右上の小物ではなく主役の大きさで）
#   2. 問いは大きい字の1行「全員ゾンビまで何日？」。前提（1万人の町・1日1人かむ）は0.8秒後に小さく足す
#   4. カウントダウンの間に、上の絵が36人の町に変わって見本が走る（待ち時間をなくし、ルールは見本で見せる）
S_DUR = [0.8, 0.7, 0.6] + [0.5] * (S_DAYS - 3)    # 見本の1日の長さ（はじめはゆっくり）
T_S0 = 2.75                                       # 見本の始まり（カウントダウンの「5」と同時）
S_T = [T_S0 + sum(S_DUR[:k]) for k in range(S_DAYS)]   # d日目（d=1..）の始まり ＝ S_T[d-1]
T_S_END = S_T[-1] + S_DUR[-1]
T_GO = T_S_END + 3.3                              # 「36人の町は 8日で全員ゾンビ」を読んでから上へ
T_BANNER = T_GO
T_M0 = T_BANNER + 2.2                             # 1万人
M_DAY = 0.42
M_T = [T_M0 + 0.8 + k * M_DAY for k in range(DAYS)]
T_M_END = M_T[-1] + M_DAY
T_REV = T_M_END + 0.4
T_P2 = T_REV + 3.0                                # 「14日目には もう半分がゾンビ」
T_Q = T_P2 + 3.4
DURATION = T_Q + 4.0
BITE = 0.32                                       # かむ線が伸びる時間（1日の始まりから）


def s_day(t):
    """見本で、いま何日目のかみつきまで終わったか、と今の日の中の経過"""
    for d in range(S_DAYS, 0, -1):
        if t >= S_T[d - 1]:
            return d, t - S_T[d - 1]
    return 0, 0.0


def m_day(t):
    for d in range(DAYS, 0, -1):
        if t >= M_T[d - 1]:
            return d, t - M_T[d - 1]
    return 0, 0.0


# ---------- 描画 ----------

def face(ctx, x, y, r, zombie, a=1.0, flash=0.0, wob=0.0):
    """丸い顔。人間は肌色で にこっ、ゾンビは黄緑で 眠そうな目と への字（怖くしない）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(wob)
    fc, dc = (ZOMB, ZOMB_D) if zombie else (SKIN, SKIN_D)
    if flash > 0:
        ctx.set_source_rgba(*hexrgb(MARKER, 0.75 * flash * a))
        ctx.arc(0, 0, r * (1.25 + 0.3 * (1 - flash)), 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(fc, a))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(dc, a))
    ctx.set_line_width(max(1.5, r * 0.09))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, a))
    lw = max(1.2, r * 0.08)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if zombie:
        for sx in (-1, 1):                         # 半分とじた目
            ctx.move_to(sx * r * 0.42 - r * 0.16, -r * 0.12)
            ctx.line_to(sx * r * 0.42 + r * 0.16, -r * 0.12)
            ctx.stroke()
            ctx.arc(sx * r * 0.42, -r * 0.08, r * 0.08, 0, math.pi)
            ctx.fill()
        ctx.move_to(-r * 0.3, r * 0.42)            # への字
        ctx.curve_to(-r * 0.1, r * 0.28, r * 0.1, r * 0.28, r * 0.3, r * 0.42)
        ctx.stroke()
    else:
        for sx in (-1, 1):
            ctx.arc(sx * r * 0.36, -r * 0.1, r * 0.1, 0, 2 * math.pi)
            ctx.fill()
        ctx.arc(0, r * 0.12, r * 0.32, 0.2 * math.pi, 0.8 * math.pi)    # にこっ
        ctx.stroke()
    ctx.restore()


# 2026-10-02 ユーザー「ゾンビと人、もう少しリアルに。Canva 使ってもいい」→ Canva の画像生成で描いた2人を使う。
# 血や傷は描かない（アリの回が「気持ち悪い」で没になったので）。背景の抜き方は assets/zombie/key.py
# 画像は Canva で作成（公開リポジトリには同梱していない）。assets/zombie/ が無いときは、丸い顔の絵で代わりに描く
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "zombie"


def _load(name):
    from PIL import Image
    im = np.asarray(Image.open(ASSETS / name).convert("RGBA")).astype(np.float32) / 255
    pm = im[..., :3] * im[..., 3:4]                                  # cairo は乗算済みの BGRA
    out = np.empty(im.shape[:2] + (4,), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = (pm[..., 2] * 255), (pm[..., 1] * 255), (pm[..., 0] * 255)
    out[..., 3] = im[..., 3] * 255
    out = np.ascontiguousarray(out)
    surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, out.shape[1], out.shape[0],
                                              out.shape[1] * 4)
    return surf, out


_KEYS = ("zombie", "human", "zombie_head", "human_head")
IMG = {k: _load(f"{k}.png") for k in _KEYS} if all((ASSETS / f"{k}.png").exists() for k in _KEYS) else None


def sprite(ctx, key, cx, by, h, a=1.0, rot=0.0):
    """絵を、下端の中央 (cx, by) を基準に高さ h で描く（rot は足元を中心に傾ける）"""
    surf = IMG[key][0]
    k = h / surf.get_height()
    ctx.save()
    ctx.translate(cx, by)
    ctx.rotate(rot)
    ctx.scale(k, k)
    ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height())
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_chase(ctx, t, a):
    """0秒目の主役: ゾンビが両手を前に出してのそのそ近づき、人間が振り返りながら走って逃げる"""
    if a <= 0:
        return
    if IMG is None:                                                   # 画像が無いとき（公開リポジトリ）
        face(ctx, 420 + 30 * math.sin(t * 1.4), 600, 92, True, a, wob=0.16 * math.sin(t * 2.8))
        face(ctx, 770 + 7 * math.sin(t * 10), 590 - 12 * abs(math.sin(t * 5)), 76, False, a)
        return
    ctx.set_source_rgba(0.15, 0.12, 0.08, 0.12 * a)                 # 足元の影
    for x, w in ((395, 170), (760, 190)):
        ctx.save()
        ctx.translate(x, 768)
        ctx.scale(1, 0.16)
        ctx.arc(0, 0, w / 2, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    step = t * 2.2                                                    # のそのそ（ゆっくり左右にゆれる）
    sprite(ctx, "zombie", 390 + 18 * math.sin(t * 1.1), 770 - 6 * abs(math.sin(step * math.pi)), 350, a,
           rot=0.05 * math.sin(step * math.pi))
    run = t * 4.5                                                     # 走る（上下にはずむ）
    sprite(ctx, "human", 765 + 6 * math.sin(t * 7), 762 - 16 * abs(math.sin(run * math.pi)), 340, a,
           rot=-0.04 + 0.03 * math.sin(run * math.pi))
    for k in range(3):                                                # 逃げる線
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(4)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        y = 560 + 45 * k
        ctx.move_to(615 - 12 * k, y)
        ctx.line_to(575 - 12 * k, y)
        ctx.stroke()


def badge(ctx, x, y, r, zombie, a=1.0, flash=0.0, wob=0.0):
    """36人の町の1人: 丸く切り抜いた顔（縁の色でゾンビ／人間も分かるように）"""
    if a <= 0:
        return
    if IMG is None:
        face(ctx, x, y, r, zombie, a, flash=flash, wob=wob)
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(wob)
    if flash > 0:
        ctx.set_source_rgba(*hexrgb(MARKER, 0.8 * flash * a))
        ctx.arc(0, 0, r * (1.3 + 0.3 * (1 - flash)), 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.save()
    ctx.arc(0, 0, r - 1, 0, 2 * math.pi)
    ctx.clip()
    key = "zombie_head" if zombie else "human_head"
    surf = IMG[key][0]
    k = 2.25 * r / surf.get_height()
    ctx.scale(k, k)
    ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height() * 0.46)
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(ZOMB_D if zombie else SKIN_D, a))
    ctx.set_line_width(max(2.0, r * 0.13))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()


# 冒頭の見本（36人の町）の顔の位置（画面の座標。紙の中心 x≈580 にそろえる）
S_XY = [(560 + (i % 6 - 2.5) * 64, 445 + (i // 6) * 62) for i in range(S_N)]
S_R = 27


def draw_town(ctx, t, a):
    """カウントダウンの間に走る見本。かむ線（赤）と空振り（灰）、かまれた顔が光ってゾンビに"""
    if a <= 0:
        return
    d, age = s_day(t) if t >= T_S0 else (0, 0.0)
    if 1 <= d <= S_DAYS and age < S_DUR[d - 1] + 0.3:
        z, tgt = S_BITES[d]
        p = clamp01(age / BITE)
        for a_, b_ in zip(z, tgt):
            x0, y0 = S_XY[a_]
            x1, y1 = S_XY[b_]
            miss = S_DAY[b_] < d                    # すでにゾンビをかんだ（空振り）
            note.pen_line(ctx, x0, y0, x0 + (x1 - x0) * 0.9, y0 + (y1 - y0) * 0.9, PENCIL if miss else RED,
                          seed=int(a_) * 7 + d, width=2.5, progress=p,
                          alpha=a * (0.5 if miss else 0.9) * (1 - ease((age - BITE - 0.15) / 0.25)))
    zc = 0
    for i, (x, y) in enumerate(S_XY):
        became = S_DAY[i]
        is_z = became == 0 or (became <= d and not (became == d and age < BITE))
        fl = 0.0
        if is_z and became > 0:
            fl = 1 - clamp01((t - S_T[became - 1] - BITE) / 0.45)
        zc += int(is_z)
        badge(ctx, x, y, S_R, is_z, a, flash=fl, wob=0.1 * math.sin(t * 3 + i) if is_z else 0.0)
    text(ctx, "36人の町で", 885, 470, 32, PENCIL, bold=False, alpha=a)
    text(ctx, f"{d}日目", 885, 545, 50, INK, alpha=a)
    text(ctx, f"ゾンビ {zc}体", 885, 615, 34, ZOMB_D, alpha=a)
    text(ctx, f"人間 {S_N - zc}人", 885, 665, 34, SKIN_D, alpha=a)
    if t >= T_S_END:
        b = ease_out((t - T_S_END) / 0.25) * a
        note.sticky(ctx, f"36人の町は {S_DAYS}日で全員ゾンビ", 580, 600, 48, "pink", fg=RED, a=b)


class ZIntro(note.Intro):
    """この回だけの冒頭。絵が主役で、問いは大きい1行。カウントダウンの間に見本が走る"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL                              # 音（ベル）を前提の行に合わせる
    T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)    # 5・4・3・2・1・0。0で止める（2026-10-02 ユーザー「1で長く止まるのは違和感」）
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        # 上半分: 0〜2.75秒は追いかけっこ、そこから36人の町に入れ替わる
        x = clamp01((t - (T_S0 - 0.3)) / 0.3)
        draw_chase(ctx, t, a * (1 - x))
        draw_town(ctx, t, a * x)
        # 大きい1行の問い（赤い下線を引く）
        w = core.text_width(BIG_Q, 84)
        text(ctx, BIG_Q, 580, 830, 84, INK, alpha=a)
        note.pen_line(ctx, 580 - w / 2 - 6, 892, 580 + w / 2 + 6, 886, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        # 前提（0.8秒後に小さく）
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 950, 40, INK, bold=False, alpha=a1)
        # 三択（縦のメモ書き）
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1060 + i * 95
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 62, INK, seed=21 + i, alpha=a * show)
        # 予想して！ と 5・4・3・2・1
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 760, 1060, 56, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 770, 1185, 78, 74, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(770, 1185)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 112, INK, alpha=a)
            ctx.restore()


BIG_Q = "全員ゾンビまで何日？"
DETAIL = "1万人の町にゾンビが1体。1日に1人かむ。"
INTRO = ZIntro(["1万人の町にゾンビ1体。1日1人かむ。", "全員ゾンビになるまで何日？"],
               ["約1か月", "約1年", "約27年"], correct=0, msg="", rule=None)


# 1万人のマス（100×100、10×10の束）
CELL, BGAP = 6, 2
GW = 100 * CELL + 9 * BGAP
GX0, GY0 = 540 - GW // 2, 680
_ix = np.arange(N)
_cx = (_ix % 100) * CELL + (_ix % 100) // 10 * BGAP
_cy = (_ix // 100) * CELL + (_ix // 100) // 10 * BGAP
POS = np.random.default_rng(SEED + 7).permutation(N)          # 人の並び（町のどこに住んでいるか）
PX_, PY_ = _cx[POS], _cy[POS]


def grid_surface(d, flash_day):
    img = np.zeros((GW, GW, 4), np.uint8)
    cols = np.where(DAY_OF <= d, 1, 0)
    skin, zomb, hot = (np.array(bgra(c), np.uint8) for c in ("#f0ad74", ZOMB, "#3f9a2c"))   # マスの人間は顔より濃く（最後に残った人が見えるように）
    for k in range(CELL - 1):
        for j in range(CELL - 1):
            yy, xx = PY_ + k, PX_ + j
            img[yy, xx] = np.where(cols[:, None] == 1, zomb, skin)
            if flash_day:
                sel = DAY_OF == flash_day
                img[yy[sel], xx[sel]] = hot
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW, GW, GW * 4), img


def draw_mass(ctx, t, dim=0.0):
    d, age = m_day(t)
    surf, _keep = grid_surface(d, d if (d and age < 0.25) else 0)
    ctx.set_source_surface(surf, GX0, GY0)
    ctx.paint_with_alpha(1 - 0.3 * dim)
    if t < M_T[3] + 0.3:                            # 最初の1体に赤ペンの丸
        a = ease_out((t - T_M0) / 0.3) * (1 - ease((t - M_T[3]) / 0.3))
        x, y = GX0 + PX_[0] + 2, GY0 + PY_[0] + 2
        note.pen_circle(ctx, x, y, 22, 20, RED, seed=3, width=4, alpha=a)
        text(ctx, "最初の1体", x + (32 if x < 640 else -32), y - 34, 30, RED, align="left" if x < 640 else "right", alpha=a)
    zc = int(ZC[d])
    text(ctx, f"{d}日目", 540, 1340, 48, INK)
    text(ctx, f"ゾンビ {zc:,}体", 520, 1398, 40, ZOMB_D, align="right")          # 色が凡例を兼ねる
    text(ctx, f"人間 {N - zc:,}人", 560, 1398, 40, SKIN_D, align="left")


def body(ctx, t):
    if t < T_BANNER:
        return
    if t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万人の町では？", 540, 950, a=a, t_rel=t - T_BANNER)
    else:
        q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
        draw_mass(ctx, t, dim=clamp01((t - T_M_END) / 0.4))
        if t >= T_M_END and q < 1:
            a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - q)
            note.sticky(ctx, f"{DAYS}日で 1万人が全員ゾンビ", 540, 860, 62, "yellow", a=a)
        if t >= T_P2 and q < 1:
            b = ease_out((t - T_P2) / 0.3) * (1 - q)
            note.sticky(ctx, f"{HALF}日目には もう半分がゾンビ", 540, 1010, 48, "mint", a=b, tilt=0.02)
        if q > 0:
            # 「だから何？」で終わらないよう、理由は問いかけにして、答えは概要欄に書く
            note.sticky(ctx, "1日1人しか かまないのに\nなんで27年もかからないの？", 540, 880, 54, "yellow", a=q, tilt=-0.02)
            r = ease_out((t - T_Q - 1.2) / 0.3)
            note.sticky(ctx, "答えは概要欄に", 540, 1075, 50, "pink", fg=RED, a=r, tilt=0.025)


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

def chomp(dur=0.09, seed=0):
    """かむ「かぷっ」（短い低めの音）"""
    t = _t(dur)
    f = 420 - 1800 * t
    return np.sin(2 * np.pi * np.cumsum(f) / 44100) * np.exp(-t * 40)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(110.0, 164.8, 220.0, 277.2)), 1.0, bgm=True)
    INTRO.audio(mx)
    for d in range(1, S_DAYS + 1):
        t0 = S_T[d - 1]
        mx.add(t0, tick(1800), 0.35)
        n_hit = int((S_DAY == d).sum())
        mx.add(t0 + BITE, chomp(), min(0.7, 0.3 + 0.06 * n_hit))
        if n_hit:
            mx.add(t0 + BITE + 0.02, blip(523.3 + 40 * min(n_hit, 8), 0.12), 0.35)
    mx.add(T_S_END, bell(659.3), 0.5)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    for d in range(1, DAYS + 1):
        t0 = M_T[d - 1]
        new = int((DAY_OF == d).sum())
        mx.add(t0, tick(2200), 0.25)
        if new:
            mx.add(t0, shimmer(min(300, 5 + new // 8), 0.2, seed=d), 0.25 + 0.4 * min(1, new / 3000))
    mx.add(T_M_END, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([220.0, 277.2, 329.6], 1.6), 0.5)
    mx.add(T_P2, bell(784.0), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    # 照合1: 1日ごとの新しくかまれた人数（400回ぶんの合計）を、理論の期待値の合計とくらべる
    got = exp = 0.0
    z5 = []
    for day_of, _b in RUNS:
        zc = zombies_by_day(day_of, day_of.max())
        for d in range(1, len(zc)):
            z, h = zc[d - 1], N - zc[d - 1]
            got += zc[d] - z
            exp += h * (1 - (1 - 1 / (N - 1)) ** z)
        z5.append(zc[5])
    # 照合2: 5日目の平均（倍々のころ）。z→z+(N−z)(1−q^z) の期待値を1日ずつ（はじめは期待値のずれが小さい）
    z = 1.0
    for _ in range(5):
        z = z + (N - z) * (1 - (1 - 1 / (N - 1)) ** z)
    print(f"seed={SEED} 全員ゾンビ={DAYS}日 半分={HALF}日目 / 400回: 中央値{MED_DAYS}日 平均{DAYS_ALL.mean():.2f}日 "
          f"範囲{DAYS_ALL.min()}〜{DAYS_ALL.max()}日 / 見本 seed={S_SEED} {S_DAYS}日 / 長さ={DURATION:.1f}秒")
    check_answers([
        ("新しくかまれた人の合計（400回）÷ 理論の期待値", got / exp, 1.0, 0.003),
        ("5日目のゾンビの平均（倍々のころ）", float(np.mean(z5)), z, 0.3),
        ("画面の回の日数 ＝ 400回の中央値", DAYS, MED_DAYS, 0),
        ("400回すべて「約1か月」（2〜6週間）", float(14 <= DAYS_ALL.min() and DAYS_ALL.max() <= 42), 1.0, 0),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 0.9, 1.6, 2.2, 2.9, S_T[0] + 0.25, S_T[2] + 0.2, S_T[4] + 0.2, S_T[6] + 0.3,
                      T_S_END + 1.0, T_BANNER + 0.6, M_T[2], M_T[12], M_T[17], T_M_END + 1.0, T_P2 + 1.0,
                      T_Q + 2.0], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
