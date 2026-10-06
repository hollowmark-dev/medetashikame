"""行列の店は本当においしい？ 2つの店に100人が順番に並ぶ。まずい店に行列ができる確率は？

モデル（情報カスケード、Bikhchandani・Hirshleifer・Welch 1992 のいちばん簡単な形）:
- A店はおいしい、B店はまずい。だれもそれを知らない
- 1人ずつ来て、自分の舌（6割の確率で A を「おいしい」と感じる）と、前の人たちが並んだ数を見て決める
- どちらかに2人以上多く並んでいれば、自分の舌は無視して多いほうに並ぶ。差が1人以下なら自分の舌に従う
はじめの2人がそろって B を選ぶと、そこから先は全員 B（行列が行列を呼ぶ）。
理論: まずい店に行列ができる確率 ＝ 0.4² ÷ (0.6² ＋ 0.4²) ≈ 30.8%。
追い打ち: 同じ100人が行列を見ずに自分の舌だけで選ぶと、まずい店のほうが多くなるのは 1.7%（二項分布）。
正解は C「約30%」。

構成（「データで語る棒人間」から取り入れた5つ。CHANNEL.md）:
- 0秒目は2軒の店（Canva）。1人ずつ来て並ぶ。吹き出し＝その人の舌が「おいしい」と言う店
- 3人目は自分の舌は A なのに、2人並んだ B へ → スポットライト
- 1万の町（100×100のマス）。色＝行列ができた店。「まずい店に行列ができた町」と「自分の舌の正しさ 60%」を並べて出しっぱなし
- 追い打ち（自分の舌だけなら？）→ 名前「情報カスケード」→ 締めの問いかけ（答えは概要欄）

照合: 20万の町で、まずい店に行列 vs 0.3077、自分の舌だけでまずい店が多数 vs 二項分布の 0.0168。
画面の回の2つの割合が、小数1桁（%）で理論値と同じになること。

画像（店・並ぶ人）は Canva で作成（公開リポジトリには同梱しない）。assets/gyoretsu/ が無いときは線画で代わりに描く。
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
from engine.parts import bgra, loop_back, r1, stills

note.use()
note.DATE = "10.6"                                # 日付欄（公開予定日）

SLUG = "gyoretsu-mise"
N, P = 10000, 100                                 # 町の数、1つの町に来る人の数
ACC = 0.6                                         # 自分の舌が正しい確率
GOOD, BAD = "#e0892a", "#7b6fa8"                  # おいしいA店（橙）、まずいB店（紫がかった灰）

EXACT_WRONG = (1 - ACC) ** 2 / (ACC ** 2 + (1 - ACC) ** 2)                         # 0.3077
EXACT_OWN = sum(math.comb(P, k) * ACC ** k * (1 - ACC) ** (P - k) for k in range(P // 2))   # 0.0168


def towns(seed, n=N):
    """n の町で100人ずつ。戻り値: まずい店に行列ができたか、自分の舌だけならまずい店が多かったか"""
    rng = np.random.default_rng(seed)
    sig = rng.random((n, P)) < ACC                # True ＝ 舌が「A がおいしい」と言う
    d = np.zeros(n, np.int32)                     # A に並んだ人 − B に並んだ人
    cnt_a = np.zeros(n, np.int32)
    for i in range(P):
        act = np.where(d >= 2, True, np.where(d <= -2, False, sig[:, i]))
        d += np.where(act, 1, -1)
        cnt_a += act
    return (P - cnt_a) > cnt_a, sig.sum(axis=1) < P / 2


for SEED in range(1, 5000):
    WRONG, OWN_BAD = towns(SEED)
    if r1(WRONG.mean() * 100) == r1(EXACT_WRONG * 100) and r1(OWN_BAD.mean() * 100) == r1(EXACT_OWN * 100):
        break
ORDER = np.random.default_rng(SEED + 3).permutation(N)

# ---------- 冒頭の見本の町（8人） ----------
S_SIG = [False, False, True, True, False, True, True, False]   # 舌が言う店（True＝A）。3人目と4人目は A なのに…
S_ACT = []
_d = 0
for s in S_SIG:
    a = True if _d >= 2 else False if _d <= -2 else s
    S_ACT.append(a)
    _d += 1 if a else -1
SPOT = 2                                          # スポットライトを当てる人（3人目）

# ---------- 時間割 ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
S_T = [0.3, 1.1, 2.0, 3.9, 4.5, 5.1, 5.7, 6.3]     # 1人ずつ来る時刻
WALK = 0.55                                       # 列まで歩く時間
T_SPOT = S_T[SPOT] + WALK + 0.1                   # 3人目のスポットライト
T_S_STICKY = S_T[-1] + WALK + 0.4
T_GO = T_S_STICKY + 3.0
T_BANNER = T_GO
T_M0 = T_BANNER + 2.1                             # 1万の町
M_DUR = 6.0
T_M_END = T_M0 + M_DUR
T_REV = T_M_END + 0.4
T_P2 = T_REV + 3.2                                # 追い打ち「自分の舌だけで選んだら？」
T_RE = T_P2 + 2.3                                 # 塗り直し
T_RE_END = T_RE + 1.2
T_NAME = T_RE_END + 3.0                           # 「情報カスケード」
T_Q = T_NAME + 3.4
DURATION = T_Q + 4.0


def m_count(t):
    if t < T_M0:
        return 0
    return int(N * clamp01((t - T_M0) / M_DUR) ** 1.4)


# ---------- 絵 ----------
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "gyoretsu"


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


_KEYS = ("shop", "queuer")
IMG = {k: _load(f"{k}.png") for k in _KEYS} if all((ASSETS / f"{k}.png").exists() for k in _KEYS) else None


def sprite(ctx, key, cx, by, h, a=1.0, flip=False):
    surf = IMG[key][0]
    k = h / surf.get_height()
    ctx.save()
    ctx.translate(cx, by)
    ctx.scale(-k if flip else k, k)
    ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height())
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(a)
    ctx.restore()


SHOP_H = 250


def shop(ctx, cx, by, letter, col, a=1.0):
    """店（看板に A / B を書く）"""
    if IMG is not None:
        sprite(ctx, "shop", cx, by, SHOP_H, a)
    else:
        ctx.set_source_rgba(*hexrgb("#b07a46", a))
        ctx.rectangle(cx - SHOP_H * 0.45, by - SHOP_H * 0.8, SHOP_H * 0.9, SHOP_H * 0.8)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb("#3d3a3a", a))
        ctx.move_to(cx - SHOP_H * 0.52, by - SHOP_H * 0.78)
        ctx.line_to(cx, by - SHOP_H * 0.98)
        ctx.line_to(cx + SHOP_H * 0.52, by - SHOP_H * 0.78)
        ctx.fill()
    ly = by - SHOP_H * 0.905                                         # 看板の中（木の色に埋もれないよう白い札を敷く）
    ctx.set_source_rgba(1, 0.98, 0.93, 0.92 * a)
    core.rrect(ctx, cx - 27, ly - 25, 54, 50, 8)
    ctx.fill()
    text(ctx, letter, cx, ly, 46, col, alpha=a)


def person(ctx, cx, by, h, a=1.0, flip=False):
    if IMG is not None:
        sprite(ctx, "queuer", cx, by, h, a, flip)
        return
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(h * 0.05)
    ctx.arc(cx, by - h * 0.88, h * 0.1, 0, 2 * math.pi)
    ctx.stroke()
    ctx.move_to(cx, by - h * 0.78)
    ctx.line_to(cx, by - h * 0.4)
    ctx.line_to(cx - h * 0.1, by)
    ctx.move_to(cx, by - h * 0.4)
    ctx.line_to(cx + h * 0.1, by)
    ctx.stroke()


def bubble(ctx, x, y, letter, col, a=1.0):
    """その人の舌が「おいしい」と言う店の吹き出し"""
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    core.rrect(ctx, x - 22, y - 22, 44, 42, 12)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(x - 6, y + 20)
    ctx.line_to(x, y + 31)
    ctx.line_to(x + 6, y + 20)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    ctx.fill()
    text(ctx, letter, x, y - 1, 30, col, alpha=a)


# 冒頭の町（画面の座標）
AX, BX, SHOP_BY, FEET = 290, 830, 775, 865   # 店の上（y 370〜480）は付箋の置き場
PH = 150                                          # 並ぶ人の高さ


def spot_xy(act, k):
    """k番目に並んだ人の立ち位置（A は店の右へ、B は店の左へ並ぶ）"""
    if act:
        return AX + 105 + k * 50, FEET
    return BX - 100 - k * 50, FEET


def draw_town(ctx, t, a):
    if a <= 0:
        return
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.45 * a))   # 道
    ctx.set_line_width(4)
    ctx.move_to(110, FEET + 4)
    ctx.line_to(1000, FEET + 4)
    ctx.stroke()
    shop(ctx, AX, SHOP_BY, "A", GOOD, a)
    shop(ctx, BX, SHOP_BY, "B", BAD, a)
    if t >= 0.8:
        b = ease_out((t - 0.8) / 0.25) * a
        text(ctx, "本当はおいしい", AX, 490, 30, GOOD, alpha=b)
        text(ctx, "本当はまずい", BX, 490, 30, BAD, alpha=b)
    qa = qb = 0
    for i, (sig, act) in enumerate(zip(S_SIG, S_ACT)):
        t0 = S_T[i]
        k = qa if act else qb
        if act:
            qa += 1
        else:
            qb += 1
        if t < t0:
            continue
        x1, y1 = spot_xy(act, k)
        p = ease(clamp01((t - t0) / WALK))
        x0, y0 = 575, 930
        x, y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
        if i == SPOT and t >= T_SPOT:                 # スポットライト
            s = ease_out((t - T_SPOT) / 0.4)
            g = cairo.RadialGradient(x, y - PH * 0.6, 10, x, y - PH * 0.6, 150)
            g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.6 * s * a)
            g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
            ctx.set_source(g)
            ctx.arc(x, y - PH * 0.6, 150, 0, 2 * math.pi)
            ctx.fill()
        person(ctx, x, y, PH, a, flip=act)            # A の列は左を向く（店のほう）
        q = ease_out((t - t0) / 0.25)
        bubble(ctx, x, y - PH - 34, "A" if sig else "B", GOOD if sig else BAD, a * q)
    if t >= T_SPOT and t < T_S_STICKY:
        s = ease_out((t - T_SPOT) / 0.3) * a
        note.sticky(ctx, "自分の舌はAなのに、2人並んだBへ", 575, 412, 36, "yellow", fg=RED, a=s, tilt=0.01)
    if t >= T_S_STICKY:
        b = ease_out((t - T_S_STICKY) / 0.25) * a
        note.sticky(ctx, "まずいB店に行列ができた", 575, 412, 44, "pink", fg=RED, a=b)


class GIntro(note.Intro):
    """この回だけの冒頭。2軒の店に1人ずつ並ぶ（カウントダウンの間も続く）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_town(ctx, t, a)
        w = core.text_width(BIG_Q, 56)
        text(ctx, BIG_Q, 570, 960, 56, INK, alpha=a)
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


BIG_Q = "まずい店に行列ができる確率は？"
DETAIL = "100人が順に店を選ぶ。自分の舌は6割当たる"
INTRO = GIntro(["2つの店に100人。自分の舌は6割当たる。", "まずい店に行列ができる確率は？"],
               ["1%未満", "約10%", "約30%"], correct=2, msg="", rule=None)

# ---------- 1万の町（本体の座標） ----------
CELL, BGAP = 6, 2
GW = 100 * CELL + 9 * BGAP
GX0, GY0 = 540 - GW // 2, 680
_ix = np.arange(N)
_cx = (_ix % 100) * CELL + (_ix % 100) // 10 * BGAP
_cy = (_ix // 100) * CELL + (_ix // 100) // 10 * BGAP
_perm = np.random.default_rng(SEED + 4).permutation(N)   # 町ごとのマスの位置（現れる順とは別にばらす）
POS_X, POS_Y = _cx[_perm], _cy[_perm]


def grid_surface(n, mode):
    """mode 0: 行列ができた店、1: 自分の舌だけなら多かった店"""
    img = np.zeros((GW, GW, 4), np.uint8)
    shown = ORDER[:n]
    bad = WRONG[shown] if mode == 0 else OWN_BAD[shown]
    good_c, bad_c = np.array(bgra(GOOD), np.uint8), np.array(bgra(BAD), np.uint8)
    xs, ys = POS_X[shown], POS_Y[shown]
    for k in range(CELL - 1):
        for j in range(CELL - 1):
            img[ys + k, xs + j] = np.where(bad[:, None], bad_c, good_c)
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW, GW, GW * 4), img


def draw_grid(ctx, t, dim=0.0):
    n = m_count(t)
    mode = 1 if t >= T_RE else 0
    if T_RE <= t < T_RE_END:                         # 塗り直しは上から順に
        n_new = int(N * clamp01((t - T_RE) / (T_RE_END - T_RE)))
        s0, k0 = grid_surface(N, 0)
        s1, k1 = grid_surface(N, 1)
        ctx.set_source_surface(s0, GX0, GY0)
        ctx.paint_with_alpha(1 - dim * 0.4)
        ctx.save()
        ctx.rectangle(GX0, GY0, GW, GW * n_new / N)
        ctx.clip()
        ctx.set_source_surface(s1, GX0, GY0)
        ctx.paint_with_alpha(1 - dim * 0.4)
        ctx.restore()
    else:
        surf, _k = grid_surface(n if mode == 0 else N, mode)
        ctx.set_source_surface(surf, GX0, GY0)
        ctx.paint_with_alpha(1 - dim * 0.4)
    shown = ORDER[:n]
    if mode == 0:
        v = WRONG[shown].mean() * 100 if n else 0.0
        text(ctx, "まずい店に行列ができた町", 330, 1362, 28, INK, bold=False)
        text(ctx, f"{v:.1f}%" if n else "—", 330, 1410, 48, BAD)
    else:
        text(ctx, "舌だけなら、まずい店が多い町", 330, 1362, 28, INK, bold=False)
        text(ctx, f"{OWN_BAD.mean() * 100:.1f}%", 330, 1410, 48, BAD)
    text(ctx, "自分の舌の正しさ", 730, 1362, 28, INK, bold=False)
    text(ctx, f"{ACC * 100:.0f}%", 730, 1410, 48, GOOD)
    note.legend(ctx, [(GOOD, "おいしい店に行列"), (BAD, "まずい店に行列")], 1322, 28)


def body(ctx, t):
    if t < T_BANNER:
        return
    if t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万の町でためす", 540, 950, a=a, t_rel=t - T_BANNER)
        return
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    dim = clamp01((t - T_M_END) / 0.4) if (t < T_P2 or t >= T_RE_END + 0.4) else 0.0
    draw_grid(ctx, t, dim)
    if T_M_END <= t < T_P2 + 0.3:
        a = ease_out((t - T_M_END - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
        note.sticky(ctx, f"1万の町のうち {WRONG.mean() * 100:.1f}% で\nまずい店に行列", 540, 960, 58, "yellow", a=a)
    if T_P2 <= t < T_RE + 0.3:
        a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_RE) / 0.3))
        note.banner(ctx, "行列を見ずに選んだら？", 540, 960, a=a, t_rel=t - T_P2, size=62)
    if T_RE_END <= t and q < 1:
        a = ease_out((t - T_RE_END) / 0.3) * (1 - ease((t - T_NAME) / 0.3))
        note.sticky(ctx, f"自分の舌だけなら\nまずい店が多いのは {OWN_BAD.mean() * 100:.1f}%", 540, 960, 54, "mint", a=a)
    if t >= T_NAME and q < 1:
        b = ease_out((t - T_NAME) / 0.3) * (1 - q)
        note.sticky(ctx, "これを「情報カスケード」と呼ぶ", 540, 960, 48, "mint", a=b, tilt=-0.015)
    if q > 0:
        note.sticky(ctx, "自分の舌だけなら2%なのに\nなんで行列を見ると30%に？", 540, 900, 54, "yellow", a=q, tilt=-0.02)
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

def step_snd(dur=0.07):
    t = _t(dur)
    n = np.random.default_rng(4).standard_normal(len(t))
    return n * np.exp(-t * 60) * 0.5


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    for i, t0 in enumerate(S_T):
        mx.add(t0, step_snd(), 0.3)
        mx.add(t0 + WALK, blip(523.3 if S_ACT[i] else 392.0, 0.12), 0.35)
    mx.add(T_SPOT, bell(880.0, 1.0), 0.4)
    mx.add(T_S_STICKY, bell(659.3), 0.4)
    mx.add(T_BANNER, riser(0.9), 0.5)
    beat(mx, T_M0, T_M_END, bpm=124, vol=0.5, accel=True)
    mx.add(T_M0, shimmer(400, M_DUR, seed=3), 0.35)
    mx.add(T_M_END, thump(), 0.7)
    mx.add(T_M_END + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(T_P2, riser(0.8), 0.4)
    mx.add(T_RE, whoosh(1.0), 0.3)
    mx.add(T_RE_END, bell(1046.5), 0.5)
    mx.add(T_NAME, chord([392.0, 493.9, 587.3], 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    big_w, big_o = towns(12345, 200000)
    print(f"seed={SEED} まずい店に行列={WRONG.mean():.4f} 自分の舌だけで多数がまずい店={OWN_BAD.mean():.4f} "
          f"/ 20万の町: {big_w.mean():.4f} {big_o.mean():.4f} / 見本 {['A' if a else 'B' for a in S_ACT]} / 長さ={DURATION:.1f}秒")
    check_answers([
        ("20万の町: まずい店に行列", float(big_w.mean()), EXACT_WRONG, 0.004),
        ("20万の町: 自分の舌だけでまずい店が多数", float(big_o.mean()), EXACT_OWN, 0.002),
        ("画面の「まずい店に行列」（%・小数1桁）", r1(WRONG.mean() * 100), r1(EXACT_WRONG * 100), 0),
        ("画面の「自分の舌だけなら」（%・小数1桁）", r1(OWN_BAD.mean() * 100), r1(EXACT_OWN * 100), 0),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 0.9, 1.6, 2.5, T_SPOT + 0.6, 5.0, T_S_STICKY + 0.5, T_BANNER + 0.6,
                      T_M0 + 2.0, T_M_END + 1.0, T_P2 + 0.8, T_RE + 0.6, T_RE_END + 1.0, T_NAME + 1.0,
                      T_Q + 2.0], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
