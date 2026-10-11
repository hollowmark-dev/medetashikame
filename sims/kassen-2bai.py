"""合戦で兵が2倍。勝った側は何人残る？ 100人 vs 50人が弓で撃ち合う。— 2026-10-08 作成（公開予定 10/10 ごろ）

モデル（ランチェスターの2次法則を、確率で。1916年 F. W. Lanchester）
  一斉射撃 : 両軍が同時に撃つ。生きている兵 1人1人が、相手の生きている兵からでたらめに1人を狙い、確率 p で倒す。
             倒された兵は、その一斉射撃の終わりに退場（同じ一斉射撃のあいだは、倒される兵も撃つ）。
             同じ兵に2本当たっても、倒れるのは1人。
  腕前     : 両軍同じ p = 0.04（1回の射撃で相手1人を倒す確率）。
  勝敗     : どちらかが全滅したら終わり。残った側が勝ち。
  1万回    : 100人 vs 50人を1万回。勝った側の残り人数の分布。
  腕前の差 : 少ない側（50人）の腕前を k 倍（k = 1〜6、p×k）にして、k ごとに1万回。50人側が勝つ割合。
  ひねり   : 80人 vs 100人。(a) 100人が一度に来る、(b) 100人が50人ずつ2つに分かれて順に来る（先の50人と戦い、勝った生き残りがそのまま次の50人と戦う）。それぞれ1万回。

  理論（連続の近似。倒す速さは自分の人数に比例する）: 生き残り = √(R² − B²)。100 vs 50 なら √(100²−50²) = 86.6人。
  兵が少なくなると1回ごとの運に左右され（「ばらつき」が効く）、また同じ兵に2本当たることもあるので、平均は理論値より少し小さく出る。
  腕前を k 倍にした 50人側が互角になるのは k = (100/50)² = 4 のとき。

照合（check_answers）:
 (1) 1回の一斉射撃で倒れる人数の期待値: 閉じた式 B×(1−(1−p/B)^R) と、速い数え方・1人ずつ追う数え方の平均が一致（いくつかの R, B）
 (2) 速い数え方と、1人ずつ追う数え方（画面の見本と同じ）で、勝った側の残り人数の平均が一致
 (3) 1万回の平均が、理論の連続近似 √(R²−B²) と近い（確率のゆらぎぶん小さい）／平均場（期待値の漸化式）とも近い
 (4) 腕前 k 倍で50人側の勝率が50%になる k が、理論の 4 に近い
 (5) ひねり: 80人 vs 100人が一度に来ると負ける（理論 √(80²−100²) は虚数＝勝てない）／分かれて来ると勝つ割合・残りが平均場と整合
 (6) 画面に出す数字（平均・勝率・残り）が、別の乱数で1万回やり直しても同じ丸め
 (7) 答えは C（約85人）
乱数の種は、画面の見本（冒頭〜答え合わせ1、ひねりの絵）を「ふつうの結果」にするために選んでよい。画面の統計は全試行から正直に出している。
"""
import math
import os
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, _t, SR)
from engine.parts import loop_back, stills

note.use()
note.DATE = "10.10"                               # 日付欄（公開予定日）

SLUG = "kassen-2bai"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
P_HIT = 0.04                                      # 1回の射撃で相手1人を倒す確率（両軍同じ）
N_R, N_B = 100, 50                                # 赤軍・青軍
N_TRIALS = 10000
K_LIST = (1, 2, 3, 4, 5, 6)                       # 少ない側の腕前の倍率
TW_R, TW_G = 80, 50                               # ひねり: 赤軍80人 vs 青軍100人（50人ずつ2つ）


# ---------- 戦いの計算 ----------

def fight_fast(R, B, pR, pB, rng):
    """速い数え方（人数だけ追う）。1回の一斉射撃で「当たった矢の数」を二項分布で出し、当たった矢が
    でたらめな相手に当たる → 異なる相手が何人かを数える（同じ兵に2本当たっても倒れるのは1人）"""
    v = 0
    while R > 0 and B > 0:
        sR = int(rng.binomial(R, pR))
        sB = int(rng.binomial(B, pB))
        dB = len(set(rng.integers(0, B, sR).tolist())) if sR else 0
        dR = len(set(rng.integers(0, R, sB).tolist())) if sB else 0
        R -= dR
        B -= dB
        v += 1
    return R, B, v


def fight_explicit(ids_a, ids_b, pa, pb, rng, max_v=400):
    """1人ずつ追う数え方（画面の見本はこれ）。返り値: 一斉射撃ごとの射撃の記録、生き残り A、生き残り B。
    射撃の記録 = (A側の射撃 [(撃った兵, 狙われた兵, 当たったか)], B側の射撃)"""
    A, Bl = list(ids_a), list(ids_b)
    volleys = []
    while A and Bl and len(volleys) < max_v:
        sa = [(s, Bl[int(rng.integers(len(Bl)))], bool(rng.random() < pa)) for s in A]
        sb = [(s, A[int(rng.integers(len(A)))], bool(rng.random() < pb)) for s in Bl]
        volleys.append((sa, sb))
        dead_b = {t for _, t, h in sa if h}
        dead_a = {t for _, t, h in sb if h}
        A = [x for x in A if x not in dead_a]
        Bl = [x for x in Bl if x not in dead_b]
    return volleys, A, Bl


def one_step_expect(R, B, p):
    """閉じた式: 1回の一斉射撃で、B 人の側のうち倒れる人数の期待値（R 人が撃つ）。
    B の1人が生き残る確率 = どの射手も「この兵を狙って当てる」ことがない = (1 − p/B)^R"""
    return B * (1.0 - (1.0 - p / B) ** R)


def mean_field(R, B, pR, pB):
    """平均場: 人数を実数のまま、上の期待値で1回ずつ進める。返り値: (R, B, 回数)"""
    v = 0
    while R > 0.5 and B > 0.5 and v < 2000:
        dB = one_step_expect(R, B, pR) if R > 0 else 0.0
        dR = one_step_expect(B, R, pB) if B > 0 else 0.0
        R, B = R - dR, B - dB
        v += 1
    return R, B, v


# ---------- 1万回 ----------
SEED_MAIN, SEED_K, SEED_TW, SEED_CHECK = 11, 12, 13, 99


def _trials_main(seed, n):
    rng = np.random.default_rng(seed)
    rem = np.empty(n, np.int64)
    side = np.empty(n, np.int8)                                      # 1 = 赤が勝った, -1 = 青が勝った, 0 = 全滅
    for i in range(n):
        R, B, _ = fight_fast(N_R, N_B, P_HIT, P_HIT, rng)
        rem[i] = max(R, B)
        side[i] = 1 if R > 0 else (-1 if B > 0 else 0)
    return rem, side


def _trials_k(seed, n):
    """k ごとに、50人側（腕前 k 倍）が勝った回数"""
    out = []
    for k in K_LIST:
        rng = np.random.default_rng(seed * 100 + k)
        wins = 0
        for _ in range(n):
            R, B, _ = fight_fast(N_B, N_R, min(1.0, k * P_HIT), P_HIT, rng)   # R = 50人側
            wins += R > 0
        out.append(wins)
    return np.array(out)


def _trials_tw(seed, n):
    rng = np.random.default_rng(seed)
    once_win = 0
    split_win = 0
    split_rem = []
    for _ in range(n):
        R, B, _ = fight_fast(TW_R, 2 * TW_G, P_HIT, P_HIT, rng)
        once_win += R > 0
    rng = np.random.default_rng(seed + 1)
    for _ in range(n):
        R, B, _ = fight_fast(TW_R, TW_G, P_HIT, P_HIT, rng)
        if R > 0:
            R, B, _ = fight_fast(R, TW_G, P_HIT, P_HIT, rng)
        if R > 0:
            split_win += 1
            split_rem.append(R)
    return once_win, split_win, np.array(split_rem)


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    rem, side = _trials_main(SEED_MAIN, N_TRIALS)
    kw = _trials_k(SEED_K, N_TRIALS)
    ow, sw, sr = _trials_tw(SEED_TW, N_TRIALS)
    # 別の乱数でやり直す（画面の数字が同じ丸めか）
    rem2, side2 = _trials_main(SEED_CHECK, N_TRIALS)
    kw2 = _trials_k(SEED_CHECK, N_TRIALS)
    ow2, sw2, sr2 = _trials_tw(SEED_CHECK, N_TRIALS)
    # 1回の一斉射撃の期待値の照合（速い数え方と1人ずつ追う数え方）
    step = []
    for (R, B) in ((100, 50), (50, 100), (60, 30), (20, 20), (80, 50), (10, 40)):
        rng = np.random.default_rng(1000 + R + B)
        nn = 20000
        fast = np.empty(nn)
        for i in range(nn):
            s = int(rng.binomial(R, P_HIT))
            fast[i] = len(set(rng.integers(0, B, s).tolist())) if s else 0
        rng = np.random.default_rng(2000 + R + B)
        nn2 = 3000
        expl = np.empty(nn2)
        for i in range(nn2):
            hit = {int(rng.integers(0, B)) for _ in range(R) if rng.random() < P_HIT}
            expl[i] = len(hit)
        step.append((R, B, fast.mean(), fast.std(ddof=1) / math.sqrt(nn), expl.mean(), expl.std(ddof=1) / math.sqrt(nn2)))
    # 勝った側の残り人数: 1人ずつ追う数え方（見本と同じ実装）でも
    rng = np.random.default_rng(555)
    rem_e = np.array([max(len(a), len(b)) for _, a, b in
                      (fight_explicit(range(N_R), range(N_B), P_HIT, P_HIT, rng) for _ in range(2000))])
    np.savez(OUT / "data.npz", rem=rem, side=side, kw=kw, tw=np.array([ow, sw]), sr=sr,
             rem2=rem2, side2=side2, kw2=kw2, tw2=np.array([ow2, sw2]), sr2=sr2, step=np.array(step), rem_e=rem_e)


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = OUT / "data.npz"
        if not f.exists():
            compute()
        z = np.load(f)
        _DATA = {k: z[k] for k in z.files}
    return _DATA


# ---------- 見本の戦い（冒頭〜答え合わせ1 / ひねり）の記録 ----------

def main_record(seed):
    rng = np.random.default_rng(seed)
    vol, A, Bl = fight_explicit(range(N_R), range(N_B), P_HIT, P_HIT, rng)
    return vol, A, Bl


def alive_counts(vol, nA, nB):
    """一斉射撃ごとの (A, B) 生き残り（その一斉射撃が終わったあと）"""
    a, b = nA, nB
    out = []
    for sa, sb in vol:
        a -= len({t for _, t, h in sb if h})
        b -= len({t for _, t, h in sa if h})
        out.append((a, b))
    return out


def good_main(seed):
    vol, A, Bl = main_record(seed)
    if not A or Bl:
        return False
    n = len(vol)
    ac = alive_counts(vol, N_R, N_B)
    if not (15 <= n <= 17):
        return False
    if not (83 <= len(A) <= 86):
        return False
    if not (18 <= ac[7][1] <= 30):                  # 冒頭の8回が終わったとき青軍がまだ2割以上残っている
        return False
    if ac[7][0] < 90:
        return False
    return True


def twist_record(seed):
    rng = np.random.default_rng(seed)
    v1, A1, G1 = fight_explicit(range(TW_R), range(TW_G), P_HIT, P_HIT, rng)
    if not A1:
        return v1, [], [], [], []
    v2, A2, G2 = fight_explicit(A1, range(TW_G), P_HIT, P_HIT, rng)
    return v1, v2, A1, A2, G2


def good_twist(seed):
    v1, v2, A1, A2, G2 = twist_record(seed)
    if not A2 or G2:
        return False
    if not (15 <= len(v1) <= 18 and 18 <= len(v2) <= 24):
        return False
    return 58 <= len(A1) <= 66 and 31 <= len(A2) <= 36


def find_seeds():
    sm = next(s for s in range(1, 20000) if good_main(s))
    st = next(s for s in range(1, 20000) if good_twist(s))
    return sm, st


SEED_SAMPLE, SEED_TWIST = 37, 287                   # 探索（--seeds）で選んだ見本の種


if __name__ == "__main__" and "--seeds" in sys.argv:
    print(find_seeds())


if __name__ == "__main__" and "--compute" in sys.argv:
    import time
    t0 = time.time()
    compute()
    d = data()
    print(f"計算 {time.time() - t0:.0f}秒")


# =====================================================================
# 絵: 足軽（ペン描き風）
# =====================================================================
SKIN = "#fff0d8"
HAT = "#d6c19a"
LEGC = "#dcd1ba"
WOOD = "#9a6a38"
GRAY = "#b9b9b9"
TEAM = {"R": dict(flag="#d8434e", armor="#f6b9b3", sleeve="#e79a94"),
        "B": dict(flag="#3a73c8", armor="#bad3f3", sleeve="#92b4e4")}


def _mix(c, g, k):
    a = hexrgb(c) if isinstance(c, str) else c
    b = hexrgb(g)
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, 1.0)


def _limb(ctx, pts, w, col, ink_w, ink=INK):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink))
    ctx.set_line_width(w + 2 * ink_w)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    ctx.set_source_rgba(*col)
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()


def _poly(ctx, pts, col, ink_w, ink=INK):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*col)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(ink))
    ctx.set_line_width(ink_w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def _dot(ctx, x, y, r, col, ink_w):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*col)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(ink_w)
    ctx.stroke()


def _lerp2(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def draw_soldier(ctx, x, y, k, team, draw=0.0, face=1, fall=0.0, alpha=1.0, flutter=0.0, sway=0.0,
                 shadow=True, banner=True):
    """足軽1人。足元が (x, y)、k = 1単位の画面での大きさ（背の高さは約 104 単位）。face=+1 は右向き。
    draw: 0（弓を下げて構え）〜1（めいっぱい引いた）、fall: 0（立つ）〜1（倒れた）、
    flutter: 背中の小旗のなびき（時刻）"""
    tm = TEAM[team]
    g = clamp01(fall * 1.6)                                # 倒れると灰色に
    gray = g * 0.82
    c_armor, c_sleeve = _mix(tm["armor"], GRAY, gray), _mix(tm["sleeve"], GRAY, gray)
    c_flag = _mix(tm["flag"], GRAY, gray)
    c_skin, c_hat, c_leg = _mix(SKIN, GRAY, gray * 0.8), _mix(HAT, GRAY, gray), _mix(LEGC, GRAY, gray)
    c_wood = _mix(WOOD, GRAY, gray)
    iw = (1.5 + 0.8 * k) / k                              # 画面で約1.9〜2.1pxの線（小さいほど細く）
    ctx.save()
    ctx.translate(x, y)
    if shadow:
        ctx.save()
        ctx.scale(1, 0.24)
        ctx.arc(0, 0, 21 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0.2, 0.17, 0.1, 0.17 * alpha)
        ctx.fill()
    ctx.scale(face * k, k)
    ctx.rotate(-fall * 1.50 + (-0.045 * draw + sway) * (1 - fall))
    if fall > 0:
        ctx.translate(0, -3 * fall)
    if alpha < 1:
        ctx.push_group()
    d = draw
    # 小旗（指物）: 背中のさおと、なびく旗
    if banner:
        wv = 2.6 * math.sin(flutter * 7.0) + 1.0
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.set_line_width(2.4)
        ctx.move_to(-8, -52)
        ctx.line_to(-8, -118)
        ctx.stroke()
        _poly(ctx, [(-8, -116), (-21 - wv * 0.7, -115), (-21 - wv, -92), (-8, -93)], c_flag, iw)
    # 後ろの腕（弦を引く腕）
    sh = (3, -68)
    pull = _lerp2((3, -45), (6.5, -73), d)
    elb = _lerp2((-1, -55), (-8, -74), d)
    _limb(ctx, [sh, elb, pull], 7.4, c_sleeve, iw)
    # 後ろの脚
    _limb(ctx, [(-2, -40), (-6, -21), (-8, -3), (-1, -2)], 9.4, c_leg, iw)
    # 胴（鎧）と草摺
    _poly(ctx, [(-10, -38), (10, -38), (12, -70), (-9, -72)], c_armor, iw)
    _poly(ctx, [(-12, -37), (13, -37), (15, -26), (-14, -26)], _mix(tm["armor"], "#7a6a58", 0.18 + gray * 0.5), iw)
    ctx.set_source_rgba(*hexrgb(INK, 0.45))
    ctx.set_line_width(1.0)
    for yy in (-50, -58, -65):
        ctx.move_to(-9, yy)
        ctx.line_to(11, yy)
    ctx.stroke()
    # 頭と陣笠
    _dot(ctx, 3.5, -82, 8.3, c_skin, iw)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.arc(7.2, -82.6, 1.25, 0, 2 * math.pi)
    ctx.fill()
    _poly(ctx, [(-12.5, -86), (19.5, -86), (3.5, -108)], c_hat, iw)
    ctx.set_source_rgba(*hexrgb(INK, 0.5))
    ctx.set_line_width(1.0)
    ctx.move_to(-6, -91)
    ctx.line_to(12, -91)
    ctx.stroke()
    # 前の脚
    _limb(ctx, [(3, -40), (8, -21), (10, -3), (18, -2)], 9.4, c_leg, iw)
    # 弓と、弓を持つ腕
    hand = _lerp2((17, -47), (25.5, -73), d)
    elb2 = _lerp2((11, -56), (15, -71), d)
    _limb(ctx, [sh, elb2, hand], 7.4, c_sleeve, iw)
    bx, by = hand
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(5.2)
    ctx.move_to(bx - 1, by - 26)
    ctx.curve_to(bx + 12, by - 12, bx + 12, by + 12, bx - 1, by + 26)
    ctx.stroke()
    ctx.set_source_rgba(*c_wood)
    ctx.set_line_width(3.0)
    ctx.move_to(bx - 1, by - 26)
    ctx.curve_to(bx + 12, by - 12, bx + 12, by + 12, bx - 1, by + 26)
    ctx.stroke()
    px = bx - 1 - 22 * d
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(1.2)
    ctx.move_to(bx - 1, by - 26)
    ctx.line_to(px, by)
    ctx.line_to(bx - 1, by + 26)
    ctx.stroke()
    if d > 0.25:                                           # つがえた矢
        ctx.set_line_width(1.8)
        ctx.move_to(px, by)
        ctx.line_to(bx + 11, by)
        ctx.stroke()
        _poly(ctx, [(bx + 11, by), (bx + 6, by - 2.6), (bx + 6, by + 2.6)], hexrgb(INK), 1.0)
    _dot(ctx, hand[0], hand[1], 3.2, c_skin, iw)
    _dot(ctx, pull[0], pull[1], 3.2, c_skin, iw)
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


if __name__ == "__main__" and "--sprite" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1400, 760)
    c = cairo.Context(surf)
    c.set_source_rgba(*hexrgb(PAPER))
    c.paint()
    poses = [("R", 0.0, 0.0), ("R", 0.6, 0.0), ("R", 1.0, 0.0), ("R", 1.0, 0.45), ("R", 1.0, 1.0),
             ("B", 0.0, 0.0), ("B", 1.0, 0.0), ("B", 1.0, 1.0)]
    for i, (tm, d, f) in enumerate(poses):
        draw_soldier(c, 130 + 165 * i, 560, 4.6, tm, d, 1 if tm == "R" else -1, f, 1.0 if f < 0.9 else 0.6, flutter=0.3 + i)
    surf.write_to_png(str(OUT / "sprite_big.png"))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 700, 260)
    c = cairo.Context(surf)
    c.set_source_rgba(*hexrgb(PAPER))
    c.paint()
    for r in range(4):
        for col in range(10):
            sc = 0.55 + 0.1 * r
            tm = "R"
            draw_soldier(c, 40 + col * 28 + (r % 2) * 12, 80 + r * 52, 0.64 * (0.74 + 0.08 * r) * 1.0, tm, 0.0 if col % 3 else 1.0, 1, 0.0, flutter=col)
    surf.write_to_png(str(OUT / "sprite_small.png"))
    print("ok")


# =====================================================================
# 戦場（兵の並び・矢・土ぼこり）
#   v2（2026-10-08）: 戦場を「世界座標 → 画面」の見かけの変換（view）で描く。冒頭は小さく、答え合わせからは
#   ズームして大きく（足軽は元の約1.45倍）。矢・土ぼこり・のぼりも同じ倍率。
# =====================================================================
class Geo:
    """兵の並びの寸法。s は「v1（足軽の背の高さ 約72px）」に対する大きさの倍率"""

    def __init__(self, s, col_sp, row_y0, row_dy, depth=10):
        self.s = s
        self.k_near = 0.60 * s                    # いちばん手前の兵の大きさ（1単位あたりの画面px）
        self.col_sp = col_sp                      # 兵の間隔（敵のほうへ）
        self.row_y0 = row_y0                      # 奥の列（row 0）の足元の高さ
        self.row_dy = row_dy                      # 列の間隔
        self.depth = depth                        # 列の数（遠近の計算に使う）

    def gy(self, row):
        return self.row_y0 + self.row_dy * row

    def persp(self, gy):                          # 奥 0.74 〜 手前 1.0
        return 0.74 + 0.26 * (gy - self.row_y0) / (self.row_dy * (self.depth - 1))

    def k(self, gy):
        return self.k_near * self.persp(gy)


def ease_in_out(x):
    return ease(clamp01(x))


class Battle:
    """兵の並びと、一斉射撃の記録（誰が誰を狙って、当たったか）から、各時刻の絵を作る。
    groups: {名前: dict(side, n, cols, rows, xf, poles, march=(t0, t1, dx) or None, legacy=dict(xf, cols, rows))}
            legacy は v1 の並び（矢の飛ぶ時間を v1 と同じに保つため、距離の計算にだけ使う）
    fights: [dict(ga, gb, vols, times, flight=(a, b), roll)]  vols は fight_explicit の記録
    view  : view(t) -> (Zx, Zy, ox, oy)。世界座標 (x, y) → 画面 (ox + Zx x, oy + Zy y)。兵の大きさは k × Zx"""

    def __init__(self, groups, fights, geo, view, seed=1):
        rng = np.random.default_rng(seed)
        self.groups = groups
        self.geo = geo
        self.view = view
        self.base = {}
        n_all = 0
        for g, c in groups.items():
            self.base[g] = n_all
            n_all += c["n"]
        self.n_all = n_all
        self.gid = np.zeros(n_all, np.int64)
        self.face = np.zeros(n_all, np.int64)
        self.x0 = np.zeros(n_all)
        self.xL = np.zeros(n_all)                   # v1 の並びでの x（矢の飛ぶ時間の計算だけに使う）
        self.gy = np.zeros(n_all)
        self.team = [""] * n_all
        self.sway_ph = rng.uniform(0, 6.28, n_all)
        for gi, (g, c) in enumerate(groups.items()):
            face = 1 if c["side"] == "R" else -1
            slots = []
            for col in range(c["cols"]):
                for row in c["rows"]:
                    stag = (int(round(row * 2)) % 2) * 16.0 * geo.s * face * -1
                    slots.append((c["xf"] - face * col * geo.col_sp + stag, geo.gy(row)))
            slots = slots[:c["n"]]
            lg = c["legacy"]
            slots_l = []
            for col in range(lg["cols"]):
                for row in lg["rows"]:
                    stag = (int(round(row * 2)) % 2) * 16.0 * face * -1
                    slots_l.append(lg["xf"] - face * col * 32.0 + stag)
            slots_l = slots_l[:c["n"]]
            assert len(slots) == len(slots_l) == c["n"], (g, len(slots), len(slots_l))
            perm = rng.permutation(len(slots))
            for i in range(c["n"]):
                u = self.base[g] + i
                x, gy = slots[perm[i]]
                jx = float(rng.uniform(-2.5, 2.5))
                jy = float(rng.uniform(-2.0, 2.0))
                self.x0[u] = x + jx * geo.s
                self.xL[u] = slots_l[perm[i]] + jx
                self.gy[u] = gy + jy * geo.s
                self.gid[u] = gi
                self.face[u] = face
                self.team[u] = c["side"]
        self.gnames = list(groups)
        self.k = np.array([geo.k(g) for g in self.gy])
        self.order = np.argsort(self.gy, kind="stable")
        # 一斉射撃から矢のデータを作る（乱数の引き方は v1 と同じ＝時間割は v1 と同じ）
        rel, arr, sxw, syw, exw, eyw, hit, hgt, shooter, target = [], [], [], [], [], [], [], [], [], []
        self.volley_land = []
        dust_p = []
        for f in fights:
            ga, gb = f["ga"], f["gb"]
            fa, fb = f["flight"]
            for i, (sa, sb) in enumerate(f["vols"]):
                t0 = f["times"][i]
                self.volley_land.append(t0 + f["roll"] / 2 + fa + fb * 0.4)
                for shots, gs, gt in ((sa, ga, gb), (sb, gb, ga)):
                    for (s, t, h) in shots:
                        us, ut = self.base[gs] + s, self.base[gt] + t
                        r = t0 + float(rng.random()) * f["roll"]
                        xs, ys = self.pos(us, r)
                        dist0 = abs(self.xL[ut] - self.xL[us])
                        tf = fa + fb * dist0 * 0.001
                        a_t = r + tf
                        xe, ye = self.pos(ut, a_t)
                        if not h:
                            xe += float(rng.normal(0, 20)) * geo.s
                            ye += float(rng.normal(-3, 7)) * geo.s
                        dist = math.hypot(xe - xs, ye - ys)
                        rel.append(r)
                        arr.append(a_t)
                        sxw.append(xs)
                        syw.append(ys)
                        exw.append(xe)
                        eyw.append(ye)
                        hit.append(h)
                        hgt.append(f.get("arc", 0.07) * dist + 18 * geo.s)
                        shooter.append(us)
                        target.append(ut)
                        dust_p.append(f.get("dust", 0.07))
        o = np.argsort(rel)
        self.rel = np.array(rel)[o]
        self.arr = np.array(arr)[o]
        self.sxw, self.syw = np.array(sxw)[o], np.array(syw)[o]
        self.exw, self.eyw = np.array(exw)[o], np.array(eyw)[o]
        self.hit = np.array(hit, bool)[o]
        self.hgt = np.array(hgt)[o]
        self.shooter = np.array(shooter, np.int64)[o]
        self.target = np.array(target, np.int64)[o]
        dust_p = np.array(dust_p)[o]
        # 倒れる時刻
        self.td = np.full(n_all, np.inf)
        for u, t, h in zip(self.target, self.arr, self.hit):
            if h and t < self.td[u]:
                self.td[u] = t
        # 射手ごとの射撃時刻（弓を引く動きのため）
        rels = [[] for _ in range(n_all)]
        for u, r in zip(self.shooter, self.rel):
            rels[u].append(r)
        self.rels = [sorted(v) for v in rels]
        # 土ぼこり: 外れた矢の一部と、当たった矢
        pr = rng.random(len(self.rel))
        self.dust = [(self.arr[i], self.exw[i], self.eyw[i], bool(self.hit[i]), int(self.target[i]))
                     for i in range(len(self.rel)) if self.hit[i] or pr[i] < dust_p[i]]
        self.dust.sort(key=lambda d: d[0])
        self.dust_t = np.array([d[0] for d in self.dust])
        self.land_t = np.array(sorted(self.volley_land))

    def shift(self, g, t):
        m = self.groups[g].get("march")
        if not m:
            return 0.0
        t0, t1, dx = m
        return dx * ease_in_out((t - t0) / (t1 - t0))

    def pos(self, u, t):
        return self.x0[u] + self.shift(self.gnames[self.gid[u]], t), self.gy[u]

    def draw_amount(self, u, t):
        rl = self.rels[u]
        if not rl:
            return 0.0
        i = bisect_left(rl, t - 0.14)
        d = 0.0
        if i < len(rl):
            r = rl[i]
            if t < r:
                d = ease((t - (r - 0.33)) / 0.33)
            else:
                d = 1 - (t - r) / 0.14
            if i + 1 < len(rl):
                d = max(d, ease((t - (rl[i + 1] - 0.33)) / 0.33))
        return clamp01(d)

    def alive(self, g, t):
        b = self.base[g]
        return int(np.count_nonzero(self.td[b:b + self.groups[g]["n"]] > t))

    def last_death(self, g):
        b = self.base[g]
        v = self.td[b:b + self.groups[g]["n"]]
        v = v[np.isfinite(v)]
        return float(v.max()) if len(v) else 0.0

    def shake(self, t, amp=3.2):
        i0 = bisect_left(self.land_t, t - 0.45)
        i1 = bisect_right(self.land_t, t)
        sx = sy = 0.0
        for ta in self.land_t[i0:i1]:
            a = amp * math.exp(-(t - ta) * 9)
            sx += a * math.cos((t - ta) * 61)
            sy += a * 0.7 * math.sin((t - ta) * 53)
        return max(-6, min(6, sx)), max(-5, min(5, sy))

    def center_x(self, g, t):
        """軍の中心の画面x（カウンターを置く位置）"""
        Zx, Zy, ox, oy = self.view(t)
        c = self.groups[g]
        face = 1 if c["side"] == "R" else -1
        xc = c["xf"] - face * (c["cols"] - 1) * self.geo.col_sp / 2 + self.shift(g, t)
        return ox + Zx * xc

    # ---- 描く ----
    def draw(self, ctx, t, a=1.0, shake=True):
        if a <= 0:
            return
        if a < 1:
            ctx.push_group()
        ctx.save()
        sx, sy = self.shake(t) if shake else (0.0, 0.0)
        ctx.translate(sx, sy)
        Zx, Zy, ox, oy = self.view(t)
        geo = self.geo
        ze = geo.s * Zx                                   # v1 に対する足軽の大きさ
        ytop = oy + Zy * geo.row_y0 - 24 * ze
        ybot = oy + Zy * geo.gy(geo.depth - 1) + 20 * ze
        draw_field(ctx, ytop, ybot, ze)
        for g, c in self.groups.items():
            self._noboris(ctx, g, c, t, Zx, Zy, ox, oy, ze)
        # 兵（奥から手前へ。倒れた兵を先に描き、立っている兵がその上に重なる）
        for dead_pass in (True, False):
            for u in self.order:
                dead = t >= self.td[u]
                if dead != dead_pass:
                    continue
                x, gy = self.pos(u, t)
                X, Y = ox + Zx * x, oy + Zy * gy
                team = self.team[u]
                k = self.k[u] * Zx
                if dead:
                    f = ease_out((t - self.td[u]) / 0.42)
                    draw_soldier(ctx, X, Y, k, team, 0.0, int(self.face[u]), f, 1.0 - 0.38 * f, t)
                else:
                    sway = 0.012 * math.sin(t * 2.2 + self.sway_ph[u])
                    draw_soldier(ctx, X, Y, k, team, self.draw_amount(u, t), int(self.face[u]), 0.0, 1.0,
                                 t + self.sway_ph[u], sway)
        self._arrows(ctx, t, Zx, Zy, ox, oy, ze)
        self._dust(ctx, t, Zx, Zy, ox, oy, ze)
        ctx.restore()
        if a < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)

    def _noboris(self, ctx, g, c, t, Zx, Zy, ox, oy, ze):
        geo = self.geo
        face = 1 if c["side"] == "R" else -1
        tm = TEAM[c["side"]]
        xr0 = c["xf"] - face * (c["cols"] - 1) * geo.col_sp - face * 26 * geo.s + self.shift(g, t)
        for j, row in enumerate(c["poles"]):
            gyw = geo.gy(row)
            xw = xr0 + face * (j % 2) * 30 * geo.s
            xr, gy = ox + Zx * xw, oy + Zy * gyw
            s = geo.persp(gyw)
            ph = j * 1.7 + (0.5 if c["side"] == "B" else 0.0)
            ht, bw, bh = 168 * s * ze, 30 * s * ze, 104 * s * ze
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.set_line_width(3.6 * ze ** 0.8)
            ctx.move_to(xr, gy)
            ctx.line_to(xr, gy - ht)
            ctx.stroke()
            # 旗（さおに沿った縦長。自由なほうの縁が波打つ）
            n_seg = 8
            top, bot = gy - ht + 4 * ze, gy - ht + 4 * ze + bh
            pts = []
            for i in range(n_seg + 1):
                u = i / n_seg
                yy = top + (bot - top) * u
                wv = (3 + 8 * u) * s * ze * math.sin(t * 5.3 + u * 3.2 + ph)
                pts.append((xr + face * (bw + wv * 0.6 * (0.3 + u)), yy + abs(wv) * 0.15))
            ctx.move_to(xr, top)
            for p in pts:
                ctx.line_to(*p)
            ctx.line_to(xr, bot)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(tm["flag"]))
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.set_line_width(2.6 * ze ** 0.8)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
            # 白い縦の筋（模様ではなく、遠目で旗とわかるだけの飾り）
            ctx.set_source_rgba(1, 1, 1, 0.78)
            ctx.set_line_width(5 * s * ze)
            ctx.move_to(xr + face * bw * 0.5, top + 6 * ze)
            for i in range(1, n_seg):
                p = pts[i]
                ctx.line_to(xr + face * (bw * 0.5 + (abs(p[0] - xr) - bw) * 0.5), p[1])
            ctx.stroke()
            ctx.arc(xr, gy - ht, 3.6 * ze ** 0.8, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()

    def _arrows(self, ctx, t, Zx, Zy, ox, oy, ze):
        i1 = bisect_right(self.rel, t)
        sel = np.nonzero(self.arr[:i1] >= t - 0.75)[0]
        if len(sel) == 0:
            return
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ink = hexrgb(INK)
        for i in sel:
            us, ut = self.shooter[i], self.target[i]
            ks, kt = self.k[us] * Zx, self.k[ut] * Zx
            xs = ox + Zx * self.sxw[i] + self.face[us] * 17 * ks
            ys = oy + Zy * self.syw[i] - 60 * ks
            xe = ox + Zx * self.exw[i]
            ye = oy + Zy * self.eyw[i] - (36 * kt if self.hit[i] else 0.0)
            h = self.hgt[i] * Zx
            u = (t - self.rel[i]) / (self.arr[i] - self.rel[i])
            uu = min(1.0, u)
            x = xs + (xe - xs) * uu
            y = ys + (ye - ys) * uu - 4 * h * uu * (1 - uu)
            dxv = xe - xs
            dyv = (ye - ys) - 4 * h * (1 - 2 * uu)
            n = math.hypot(dxv, dyv) or 1.0
            ux, uy = dxv / n, dyv / n
            if u < 1.0:
                L = 20 * ze
                ctx.set_source_rgba(ink[0], ink[1], ink[2], 0.8)
                ctx.set_line_width(1.7 * ze)
                ctx.move_to(x - ux * L, y - uy * L)
                ctx.line_to(x, y)
                ctx.stroke()
                hs = ze
                ctx.move_to(x + ux * 3.5 * hs, y + uy * 3.5 * hs)
                ctx.line_to(x - ux * 3 * hs - uy * 3.2 * hs, y - uy * 3 * hs + ux * 3.2 * hs)
                ctx.line_to(x - ux * 3 * hs + uy * 3.2 * hs, y - uy * 3 * hs - ux * 3.2 * hs)
                ctx.close_path()
                ctx.fill()
            elif not self.hit[i]:
                age = t - self.arr[i]
                al = 0.85 * (1 - clamp01((age - 0.15) / 0.55))
                if al > 0:
                    ctx.set_source_rgba(ink[0], ink[1], ink[2], al)
                    ctx.set_line_width(2.0 * ze)
                    ctx.move_to(xe, ye)
                    ctx.line_to(xe - ux * 12 * ze, ye - uy * 12 * ze)
                    ctx.stroke()

    def _dust(self, ctx, t, Zx, Zy, ox, oy, ze):
        i0 = bisect_left(self.dust_t, t - 0.7)
        i1 = bisect_right(self.dust_t, t)
        for (ta, xw, yw, hit, ut) in self.dust[i0:i1]:
            x = ox + Zx * xw
            y = oy + Zy * yw + 4 * ze - (36 * self.k[ut] * Zx if hit else 0.0)
            age = t - ta
            u = age / 0.7
            r = (4 + 15 * ease_out(u)) * ze
            al = 0.5 * (1 - u) ** 1.5
            ctx.set_source_rgba(0.76, 0.69, 0.55, al)
            for dx, dy, rr in ((0, 0, 1.0), (-0.7, 0.1, 0.7), (0.7, -0.15, 0.75), (0.1, -0.6, 0.6)):
                ctx.arc(x + dx * r * (0.6 + u), y + dy * r - 4 * u * ze, r * rr, 0, 2 * math.pi)
                ctx.fill()
            if hit and age < 0.3:
                k = 1 - age / 0.3
                ctx.set_source_rgba(*hexrgb(RED, 0.9 * k))
                ctx.set_line_width(2.6 * ze)
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                for j in range(5):
                    ang = -math.pi / 2 + (j - 2) * 0.62
                    ctx.move_to(x + math.cos(ang) * (8 + 8 * age / 0.3) * ze, y - 26 * ze + math.sin(ang) * (8 + 8 * age / 0.3) * ze)
                    ctx.line_to(x + math.cos(ang) * (16 + 12 * age / 0.3) * ze, y - 26 * ze + math.sin(ang) * (16 + 12 * age / 0.3) * ze)
                ctx.stroke()


# ---------- 戦場の背景（草地・遠い山・草むら）。画面の矩形 (66〜1014, y0〜y1) に毎フレーム描く ----------
def draw_field(ctx, y0, y1, ze):
    rng = np.random.default_rng(7)
    xs = np.linspace(66, 1014, 40)
    top = [(x, y0 + (8 * math.sin(x / 70) + float(rng.normal(0, 2.0))) * ze) for x in xs]
    bot = [(x, y1 + (6 * math.sin(x / 55 + 1) + float(rng.normal(0, 2.0))) * ze) for x in xs[::-1]]
    ctx.move_to(*top[0])
    for p in top[1:] + bot:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#dbe8c0", 0.8))
    ctx.fill()
    # 草むら（短い3本線）。位置は矩形に対する割合で決める（ズームしても同じ場所に残る）
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(80):
        x = float(rng.uniform(80, 1000))
        v = float(rng.uniform(0.05, 0.98))
        y = y0 + 14 * ze + v * (y1 - y0 - 20 * ze)
        ctx.set_source_rgba(*hexrgb("#6f8f4a", 0.55))
        ctx.set_line_width(2.2 * ze)
        for dx, h in ((-5, 7), (0, 10), (5, 7)):
            ctx.move_to(x + dx * 0.4 * ze, y)
            ctx.line_to(x + dx * ze, y - h * ze)
        ctx.stroke()
    # 遠い山（鉛筆の線）
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.5))
    ctx.set_line_width(3 * ze ** 0.8)
    for x0, x1, h in ((70, 430, 34), (560, 1010, 44)):
        ctx.move_to(x0, y0 - 2)
        for i in range(0, 21):
            u = i / 20
            ctx.line_to(x0 + (x1 - x0) * u, y0 - 2 - (h * math.sin(math.pi * u) ** 1.4 + 3 * math.sin(u * 17)) * ze)
        ctx.stroke()


# ---------- 見本の2つの戦い ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6                             # 8.35
T_MOVE = T_GO - 0.4
T_Z0, T_Z1 = T_GO - 0.35, T_GO + 0.45            # 冒頭が終わったら、戦場を短くズーム（0.8秒）して大きくする（v2）


def t_volley_main(i):
    if i < 7:
        return -0.3 + 1.15 * i
    if i == 7:
        return T_CD[-1]                           # カウントダウンが0になる瞬間に8回目
    return 8.55 + 0.5 * (i - 8)


VOL_M, SURV_M, _ = main_record(SEED_SAMPLE)
N_VOL_M = len(VOL_M)
# --- 戦場の寸法（v2）。世界座標＝冒頭の画面。冒頭は倍率1、ズーム後は (ZX_M, ZY_M, OX_M, OY_M) で画面へ写す ---
GEO_M = Geo(s=1.2, col_sp=38.4, row_y0=602.0, row_dy=31.8, depth=10)   # 冒頭: 足軽は v1 の1.2倍
X_LEFT = 160.0                                    # 赤軍の左のさお（世界座標）
XF_R = X_LEFT + 9 * GEO_M.col_sp + 26 * GEO_M.s   # 赤軍の最前列
XF_B = XF_R + 175.0                               # 青軍の最前列
ZX_M = 1.22                                       # ズーム後の横の倍率（足軽の大きさ = 1.2 × 1.22 ≈ v1 の1.46倍）
OX_M = 106.0 - ZX_M * X_LEFT                      # 左のさおが x=106 に来る
Y_BACK, Y_FRONT = 812.0, 1375.0                   # ズーム後、奥の列と手前の列の足元の高さ（列の間を広げて100人を数えやすく）
ZY_M = (Y_FRONT - Y_BACK) / (9 * GEO_M.row_dy)
OY_M = Y_BACK - ZY_M * GEO_M.row_y0


def view_main(t):
    w = ease_in_out((t - T_Z0) / (T_Z1 - T_Z0))
    return 1 + (ZX_M - 1) * w, 1 + (ZY_M - 1) * w, OX_M * w, OY_M * w


BATTLE_M = Battle(
    {"R": dict(side="R", n=N_R, cols=10, rows=list(range(10)), xf=XF_R, poles=[3.5, 6.0, 8.5],
               legacy=dict(xf=420.0, cols=10, rows=list(range(10)))),
     "B": dict(side="B", n=N_B, cols=5, rows=list(range(10)), xf=XF_B, poles=[3.0, 6.0],
               legacy=dict(xf=660.0, cols=10, rows=[2.5, 3.5, 4.5, 5.5, 6.5]))},
    [dict(ga="R", gb="B", vols=VOL_M, times=[t_volley_main(i) for i in range(N_VOL_M)],
          flight=(0.40, 0.42), roll=0.22, arc=0.07, dust=0.07)], GEO_M, view_main, seed=3)
T_END_M = max(BATTLE_M.last_death("R"), BATTLE_M.last_death("B"))     # 決着（最後の1人が倒れる）
REM_M = len(SURV_M)                                                    # 見本の赤軍の残り

T_STK1 = T_END_M + 0.05                           # 付箋「2倍の軍は…」
T_G0 = T_END_M + 2.5                              # 1万回へ
T_D0 = T_G0 + 0.45
D_DUR = 2.6
T_D1 = T_D0 + D_DUR
T_MEAN = T_D1 + 0.15
T_REV = T_D1 + 0.65
T_ST_A = T_REV + 0.15
T_ST_B = T_ST_A + 0.7
T_K0 = T_ST_B + 2.0
K_DUR = 3.2                                       # 2026-10-08 ユーザー「ランチェスターのところ、切り替わるのが早すぎてついていけない」→ ゆっくり・長く
T_K1 = T_K0 + K_DUR
T_K4 = T_K0 + 2.4                                 # 付箋「4倍で、やっと互角」（曲線を引き終わってから）
T_LAN = T_K0 + 4.3                                # 付箋「ランチェスターの法則」
T_TW = T_K0 + 7.6                                 # ひねり（この場面を約7.6秒見せる）
TW_BANNER = 2.0
T_T1 = T_TW + TW_BANNER                           # ひねりの戦いが始まる
TW_STEP = 0.115

VOL_T1, VOL_T2, SURV_T1, SURV_T2, _G2 = twist_record(SEED_TWIST)
N_V1, N_V2 = len(VOL_T1), len(VOL_T2)
T_MARCH0 = T_T1 + N_V1 * TW_STEP + 0.65           # 先の50人が全滅してから、次の50人が前へ出る
T_MARCH1 = T_MARCH0 + 0.9
T_T2 = T_MARCH1 + 0.1
# ひねりの戦場（画面座標そのまま。足軽は v1 の1.46倍）。下に4行の字が入るので、手前の列は y=1190 まで
GEO_T = Geo(s=GEO_M.s * ZX_M, col_sp=41.5, row_y0=803.0, row_dy=(1190.0 - 803.0) / 11, depth=12)
XF_R_T, XF_A_T, XF_G_T = 395.0, 520.0, 779.0


def view_twist(t):
    return 1.0, 1.0, 0.0, 0.0


BATTLE_T = Battle(
    {"R": dict(side="R", n=TW_R, cols=7, rows=list(range(12)), xf=XF_R_T, poles=[2.0, 8.5],
               legacy=dict(xf=340.0, cols=8, rows=list(range(10)))),
     "A": dict(side="B", n=TW_G, cols=5, rows=list(range(1, 11)), xf=XF_A_T, poles=[5.5],
               legacy=dict(xf=480.0, cols=5, rows=list(range(10)))),
     "G": dict(side="B", n=TW_G, cols=5, rows=list(range(1, 11)), xf=XF_G_T, poles=[5.5],
               march=(T_MARCH0, T_MARCH1, XF_A_T - XF_G_T),
               legacy=dict(xf=790.0, cols=5, rows=list(range(10))))},
    [dict(ga="R", gb="A", vols=VOL_T1, times=[T_T1 + i * TW_STEP for i in range(N_V1)],
          flight=(0.22, 0.10), roll=0.06, arc=0.12, dust=0.04),
     dict(ga="R", gb="G", vols=VOL_T2, times=[T_T2 + i * TW_STEP for i in range(N_V2)],
          flight=(0.22, 0.10), roll=0.06, arc=0.12, dust=0.04)], GEO_T, view_twist, seed=4)
T_END_T = max(BATTLE_T.last_death("G"), BATTLE_T.last_death("A"))
REM_T = len(SURV_T2)
T_TW_RES = T_END_T + 0.5                          # 結果の数字
T_Q = T_TW_RES + 2.6                              # 締め
DURATION = T_Q + 3.5


# =====================================================================
# 画面に出す数字（1万回すべてから）
# =====================================================================

def fmt_n(n):
    return f"{int(n):,}"


def shown():
    d = data()
    rem, side = d["rem"], d["side"]
    red = rem[side == 1]
    kw = d["kw"] / N_TRIALS
    # 50%を横切る k（隣り合う2点を直線でつなぐ）
    ks = np.array(K_LIST, float)
    k50 = None
    for i in range(len(ks) - 1):
        if kw[i] < 0.5 <= kw[i + 1]:
            k50 = ks[i] + (0.5 - kw[i]) / (kw[i + 1] - kw[i])
            break
    ow, sw = d["tw"]
    return dict(mean=float(red.mean()), mean_i=int(math.floor(red.mean() + 0.5)), red_wins=int((side == 1).sum()),
                blue_wins=int((side == -1).sum()), draws=int((side == 0).sum()), sd=float(red.std()),
                kw=kw, k50=float(k50), once=int(ow), split=int(sw),
                split_pct=int(math.floor(sw / N_TRIALS * 100 + 0.5)),
                theory=math.sqrt(N_R ** 2 - N_B ** 2))


_PERM = np.random.default_rng(21).permutation(N_TRIALS)


def hist_counts(k):
    d = data()
    r = d["rem"][_PERM[:int(k)]]
    s = d["side"][_PERM[:int(k)]]
    return np.bincount(r[s == 1], minlength=N_R + 1)


# =====================================================================
# 冒頭
# =====================================================================
BIG_Q = "勝った側は何人残る？"
DETAIL = "100人と50人が弓で撃ち合う。腕前は同じ"
LABELS = ["約50人", "約70人", "約85人"]
FLAG_R, FLAG_B = "#d8434e", "#3a73c8"


class KIntro(note.Intro):
    """この回だけの冒頭。上半分で合戦が0秒目から始まり、左上に大きく「合戦」。下に大きな問い"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO
    dim = 1.0

    def _intro(self, ctx, t, a):
        # 左上: 「合戦」と、軍の人数
        note.hand_text(ctx, "合戦", 112, 456, 116, INK, seed=3, alpha=a)
        x = 375
        for s, col, sd in (("100人", FLAG_R, 5), (" vs ", INK, 6), ("50人", FLAG_B, 7)):
            x += note.hand_text(ctx, s, x, 462, 56, col, seed=sd, alpha=a)
        sz = 64
        w = core.text_width(BIG_Q, sz)
        text(ctx, BIG_Q, 570, 960, sz, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 1007, 570 + w / 2 + 6, 1001, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 1070, 36, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1160 + i * 88
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 56, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 775, 1155, 52, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 785, 1272, 72, 68, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(785, 1272)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 106, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        """冒頭が終わったあと、上に小さく: 問い1行・下線・三択を横1列。答えは赤丸、ほかは取り消し線"""
        m = m * self.dim
        sz = 54
        w = core.text_width(BIG_Q, sz)
        if w > 850:
            sz *= 850 / w
            w = 850
        text(ctx, BIG_Q, 540, 425, sz, INK, alpha=m)
        note.pen_line(ctx, 540 - w / 2 - 6, 462, 540 + w / 2 + 6, 458, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        for i, v in enumerate(self.labels):
            cx, y = 540 + (i - 1) * 290, 520
            ok = i == self.correct
            a = m * (1 - 0.55 * rev * (not ok))
            vs = 46
            vw = core.text_width(v, vs)
            if 64 + vw > 252:
                vs *= (252 - 64) / vw
                vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a)
            text(ctx, v, x0 + 64, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=a)
            if ok:
                note.pen_circle(ctx, cx, y, (64 + vw) / 2 + 30, 42, RED, seed=31, width=7, progress=rev, alpha=m)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 72 + vw, y - 2, PENCIL, seed=i + 40, width=4,
                              progress=rev, alpha=0.8 * self.dim)

    def draw(self, ctx, t, reveal_t=None):
        m = self.moved(t)
        if m < 1:
            self._intro(ctx, t, 1 - clamp01(m * 2.2))
        if m > 0:
            ctx.save()
            ctx.translate(note.PAGE_DX, 0)
            self._top(ctx, t, m, reveal_t)
            ctx.restore()


INTRO = KIntro(["勝った側は", "何人残る？"], LABELS, correct=2, msg="", rule=None)


# =====================================================================
# 絵: 数字・グラフ
# =====================================================================

def number_row(ctx, parts, y, a, size=44, cx=540):
    ws = [core.text_width(s, size) for s, _ in parts]
    x = cx - sum(ws) / 2
    for (s, col), w in zip(parts, ws):
        text(ctx, s, x, y, size, col, align="left", alpha=a)
        x += w


HX0, HX1, HY0, HY1 = 215.0, 855.0, 700.0, 1040.0   # ヒストグラムの枠（紙の中心にそろえるため body を translate して描く）
XMIN, XMAX = 50, 100
YMAX_H = 1000.0
BAR_COL = "#e87473"


def hx(r):
    return HX0 + (r - XMIN) / (XMAX - XMIN + 1) * (HX1 - HX0)


def hy(c):
    return HY1 - c / YMAX_H * (HY1 - HY0)


def draw_hist_axes(ctx, a):
    if a <= 0:
        return
    note.pen_line(ctx, HX0 - 6, HY0 - 10, HX0 - 6, HY1 + 3, INK, seed=3, width=4.5, alpha=0.85 * a)
    note.pen_line(ctx, HX0 - 6, HY1 + 3, HX1 + 10, HY1 + 3, INK, seed=4, width=4.5, alpha=0.85 * a)
    for val, lab in ((0, "0"), (500, "500"), (1000, "1000")):
        yy = hy(val)
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(HX0 - 14, yy)
        ctx.line_to(HX0 - 6, yy)
        ctx.stroke()
        text(ctx, lab, HX0 - 20, yy, 28, INK, align="right", bold=False, alpha=a)
    for v in range(50, 101, 10):
        xx = hx(v) + (HX1 - HX0) / (XMAX - XMIN + 1) / 2
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, HY1 + 3)
        ctx.line_to(xx, HY1 + 12)
        ctx.stroke()
        text(ctx, str(v), xx, HY1 + 34, 28, INK, alpha=a)
    text(ctx, "勝った赤軍の残り人数（人）", (HX0 + HX1) / 2, HY1 + 120, 30, INK, bold=False, alpha=a)
    text(ctx, "回数（1万回のうち）", HX0 - 95, HY0 - 28, 28, INK, align="left", bold=False, alpha=a)


def draw_hist(ctx, t, a):
    k = N_TRIALS * clamp01((t - T_D0) / D_DUR)
    cnt = hist_counts(k)
    bw = (HX1 - HX0) / (XMAX - XMIN + 1)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for r in range(XMIN, XMAX + 1):
        c = cnt[r]
        if c <= 0:
            continue
        x, y = hx(r), hy(c)
        ctx.rectangle(x + 0.5, y, bw - 1.0, HY1 - y)
        ctx.set_source_rgba(*hexrgb(BAR_COL, 0.88 * a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.0)
        ctx.stroke()
        # 50回ぶんごとの薄い区切り（1万個の粒が積み上がっていく感じ）
        ctx.set_source_rgba(1, 1, 1, 0.38 * a)
        ctx.set_line_width(1.2)
        m = 50
        while m < c:
            yy = hy(m)
            ctx.move_to(x + 1.5, yy)
            ctx.line_to(x + bw - 1.5, yy)
            m += 50
        ctx.stroke()
    return int(k)


def draw_kplot(ctx, t, a):
    sh = shown()
    kw = sh["kw"]
    kx0, kx1 = HX0, HX1
    ky0, ky1 = HY0 + 20, HY1

    def px(k):
        return kx0 + (k - 0.5) / 6.0 * (kx1 - kx0)

    def py(p):
        return ky1 - p * (ky1 - ky0)
    note.pen_line(ctx, kx0 - 6, ky0 - 30, kx0 - 6, ky1 + 3, INK, seed=13, width=4.5, alpha=0.85 * a)
    note.pen_line(ctx, kx0 - 6, ky1 + 3, kx1 + 10, ky1 + 3, INK, seed=14, width=4.5, alpha=0.85 * a)
    for val, lab in ((0.0, "0%"), (0.5, "50%"), (1.0, "100%")):
        yy = py(val)
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(kx0 - 14, yy)
        ctx.line_to(kx0 - 6, yy)
        ctx.stroke()
        text(ctx, lab, kx0 - 20, yy, 28, INK, align="right", bold=False, alpha=a)
    for k in K_LIST:
        xx = px(k)
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, ky1 + 3)
        ctx.line_to(xx, ky1 + 12)
        ctx.stroke()
        text(ctx, f"{k}倍", xx, ky1 + 34, 28, INK, alpha=a)
    text(ctx, "50人側の腕前（相手の何倍か）", (kx0 + kx1) / 2, ky1 + 80, 30, INK, bold=False, alpha=a)
    text(ctx, "50人側が勝つ割合", kx0 - 95, ky0 - 52, 28, INK, align="left", bold=False, alpha=a)
    # 互角の線
    b = ease_out((t - T_K0 - 0.2) / 0.3) * a
    ctx.set_source_rgba(*hexrgb(RED, 0.8 * b))
    ctx.set_line_width(4)
    ctx.set_dash([14, 10])
    ctx.move_to(kx0, py(0.5))
    ctx.line_to(kx1, py(0.5))
    ctx.stroke()
    ctx.set_dash([])
    # 点と線（左から順に）
    prog = clamp01((t - T_K0 - 0.3) / (K_DUR * 0.6)) * (len(K_LIST) - 1)
    pts = [(px(k), py(kw[i])) for i, k in enumerate(K_LIST)]
    ctx.set_source_rgba(*hexrgb(FLAG_B, 0.9 * a))
    ctx.set_line_width(6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    full = int(prog)
    for i in range(1, full + 1):
        ctx.line_to(*pts[i])
    if full < len(pts) - 1:
        fr = prog - full
        ctx.line_to(pts[full][0] + (pts[full + 1][0] - pts[full][0]) * fr, pts[full][1] + (pts[full + 1][1] - pts[full][1]) * fr)
    ctx.stroke()
    for i, (x, y) in enumerate(pts):
        if i <= prog + 0.01:
            ctx.set_source_rgba(*hexrgb(FLAG_B, a))
            ctx.arc(x, y, 10, 0, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
            ctx.set_line_width(3)
            ctx.stroke()
            if i >= 2:
                lab = f"{int(math.floor(kw[i] * 100 + 0.5))}%"
                text(ctx, lab, x - (22 if i < 4 else 0), y - (30 if i > 2 else 28) - (0 if i != 3 else 6), 30, INK, alpha=a)
    return pts


# =====================================================================
# 本体
# =====================================================================

STK1_X, STK1_Y = 715.0, 1245.0                    # 付箋「2倍の軍は…」の位置（body 座標）
BANNER_Y = 725.0                                  # 付箋「相手を分けたら？」: 薄くした三択の行（y≈520）より下
TW_Y = (1245.0, 1312.0, 1380.0, 1428.0)           # ひねりの下の4行（戦場の手前の列 y=1190 より下、1450以内）
CNT_SIZE_T = 48                                   # ひねりは3つ並ぶので少し小さく
CNT_Y, CNT_SIZE = 690.0, 56                       # 「残り ○人」: 戦場の上、v1 の42pt より大きく


def counter_label(ctx, cx, y, n, a, col=INK, size=CNT_SIZE):
    """戦場の上の「残り ○人」。右端が x=1000 を超えないように寄せる（cx は body 座標）"""
    w = core.text_width(f"残り {n}人", size)
    cx = min(cx, 1000 - note.PAGE_DX - w / 2)
    text(ctx, f"残り {n}人", cx, y, size, col, alpha=a)


def counter_ring(ctx, cx, y, a, progress, seed, size=CNT_SIZE):
    """勝った軍のカウンターを赤ペンで囲む（「残り 84人」の幅に合わせる）"""
    w = core.text_width("残り 00人", size)
    cx = min(cx, 1000 - note.PAGE_DX - w / 2)
    note.pen_circle(ctx, cx, y, w / 2 + 28, 46, RED, seed=seed, width=6, progress=progress, alpha=a)


def body(ctx, t):
    sh = shown()
    # --- 答え合わせ1: 同じ合戦の続き（人数のカウンター）
    if T_GO <= t < T_G0 + 0.3:
        out = 1 - ease((t - T_G0) / 0.3)
        k = ease_out((t - (T_Z1 - 0.2)) / 0.3) * out
        cy = CNT_Y
        for g in ("R", "B"):
            n = BATTLE_M.alive(g, t)
            counter_label(ctx, BATTLE_M.center_x(g, T_Z1) - note.PAGE_DX, cy, n, k, FLAG_R if g == "R" else FLAG_B)
        if t >= T_END_M + 0.1:
            counter_ring(ctx, BATTLE_M.center_x("R", T_Z1) - note.PAGE_DX, cy, out,
                         clamp01((t - T_END_M - 0.1) / 0.4), 33)
        if t >= T_STK1:
            b = ease_out((t - T_STK1) / 0.3) * (1 - ease((t - (T_G0 - 0.15)) / 0.2))
            # 戦場の右側（倒れた青軍の上）に置く。赤軍の生き残りは隠さない
            note.sticky(ctx, "2倍の軍は、\nほとんど減らずに\n勝つ", STK1_X, STK1_Y, 40, "pink", fg=RED, a=b, tilt=-0.015)
    # --- 答え合わせ2: 1万回のヒストグラム
    if T_G0 <= t < T_K0 + 0.3:
        out = 1 - ease((t - T_K0) / 0.3)
        ca = ease((t - T_G0) / 0.3) * out
        draw_hist_axes(ctx, ca)
        kk = draw_hist(ctx, t, ca)
        if t < T_D1:
            number_row(ctx, [("ためした回数 ", INK), (fmt_n(kk), "#d8434e"), (" / 10,000", INK)], 1410, ca, size=38)
        # A・B・C の位置（軸の下）
        for i, v in enumerate((50, 70, 85)):
            xx = hx(v) + (HX1 - HX0) / (XMAX - XMIN + 1) / 2
            ok = i == 2
            rv = ease_out((t - T_REV) / 0.3)
            col = RED if (ok and t >= T_REV) else PENCIL
            text(ctx, "ABC"[i], xx, HY1 + 72, 30, col, bold=ok and t >= T_REV, alpha=ca * (0.55 if (t >= T_REV and not ok) else 1.0))
        if t >= T_MEAN:
            b = ease_out((t - T_MEAN) / 0.3) * ca
            mx_ = hx(sh["mean"]) + 0.0
            ctx.set_source_rgba(*hexrgb(RED, 0.85 * b))
            ctx.set_line_width(4)
            ctx.set_dash([12, 9])
            ctx.move_to(mx_, HY1)
            ctx.line_to(mx_, hy(1000) + 34)
            ctx.stroke()
            ctx.set_dash([])
            text(ctx, f"平均 {sh['mean_i']}人", mx_ - 18, hy(1000) + 4, 38, RED, align="right", alpha=b)
        if t >= T_ST_A:
            b = ease_out((t - T_ST_A) / 0.3) * ca
            number_row(ctx, [("赤軍が勝った回数 ", INK), (f"{fmt_n(sh['red_wins'])}回", RED), (" / 1万回", INK)], 1240, b, size=40)
        if t >= T_ST_B:
            b = ease_out((t - T_ST_B) / 0.3) * ca
            number_row(ctx, [("青軍が勝った回数 ", INK), (f"{fmt_n(sh['blue_wins'])}回", FLAG_B)], 1305, b, size=40)
    # --- 付け足し: 腕前を何倍にすれば互角か
    if T_K0 <= t < T_TW + 0.3:
        out = 1 - ease((t - (T_TW - 0.4)) / 0.3) if t >= T_TW - 0.4 else 1.0
        ka = ease((t - T_K0) / 0.3) * out
        if ka > 0:
            pts = draw_kplot(ctx, t, ka)
            if t >= T_K4:
                b = ease_out((t - T_K4) / 0.3) * ka
                note.sticky(ctx, "50人側の腕前が\n4倍で、やっと互角", 540, 1262, 42, "yellow", a=b, tilt=-0.015)
                xx, yy = pts[3]
                note.pen_circle(ctx, xx, yy, 34, 30, RED, seed=71, width=6, alpha=b, progress=clamp01((t - T_K4) / 0.5))
            if t >= T_LAN:
                b = ease_out((t - T_LAN) / 0.3) * ka
                note.sticky(ctx, "ランチェスターの法則", 540, 1395, 40, "mint", a=b, tilt=0.02)
    # --- ひねり: 相手を分けたら？
    if T_TW <= t < T_Q + 1:
        qa = 1 - ease((t - T_Q) / 0.35) if t >= T_Q else 1.0
        if t < T_T1:
            b = ease_out((t - T_TW) / 0.25) * (1 - ease((t - (T_T1 - 0.1)) / 0.25))
            note.banner(ctx, "相手を分けたら？", 520, BANNER_Y, a=b, t_rel=t - T_TW, size=56)
        # 80人 vs 100人（50人ずつ2つ）の説明と、カウンター
        if t >= T_T1:
            cy = CNT_Y
            fa = ease_out((t - T_T1) / 0.3) * qa
            for g, col in (("R", FLAG_R), ("A", FLAG_B), ("G", FLAG_B)):
                n = BATTLE_T.alive(g, t)
                if g == "A" and t >= T_MARCH0 - 0.1:
                    continue
                counter_label(ctx, BATTLE_T.center_x(g, t) - note.PAGE_DX, cy, n, fa, col, size=CNT_SIZE_T)
            if t >= T_END_T + 0.1:
                counter_ring(ctx, BATTLE_T.center_x("R", t) - note.PAGE_DX, cy, qa,
                             clamp01((t - T_END_T - 0.1) / 0.4), 34, size=CNT_SIZE_T)
        if t >= T_TW + 0.6:
            b0 = ease_out((t - T_TW - 0.6) / 0.3) * qa
            number_row(ctx, [("赤軍80人", FLAG_R), ("  vs  ", INK), ("青軍50人×2", FLAG_B)], TW_Y[0], b0, size=36)
        if t >= T_TW + 1.1:
            b = ease_out((t - T_TW - 1.1) / 0.3) * qa
            number_row(ctx, [("一度に来ると 勝ち ", INK), (f"{fmt_n(sh['once'])}回", RED)], TW_Y[1], b, size=42)
        if t >= T_TW_RES:
            b = ease_out((t - T_TW_RES) / 0.3) * qa
            number_row(ctx, [("分かれて来ると 勝ち ", INK), (f"{fmt_n(sh['split'])}回", RED)], TW_Y[2], b, size=42)
            b2 = ease_out((t - T_TW_RES - 0.5) / 0.3) * qa
            text(ctx, "（どちらも1万回のうち）", 540, TW_Y[3], 30, PENCIL, bold=False, alpha=b2)
    # --- 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで2倍の兵は、\n4倍強いの？", 520, 715, 54, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 520, 905, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    # 見本の戦い（冒頭〜答え合わせ1）
    if t < T_G0 + 0.3:
        wa = 1 - ease((t - T_G0) / 0.3) if t >= T_G0 else 1.0
        BATTLE_M.draw(ctx, t, a=wa)
    # ひねりの戦い
    if T_TW <= t < T_Q + 0.5:
        ta = ease((t - T_TW - 0.2) / 0.4)
        if t >= T_Q:
            ta *= 1 - ease((t - T_Q) / 0.35)
        BATTLE_T.draw(ctx, t, a=ta)
    INTRO.dim = 1.0
    if t >= T_TW:
        INTRO.dim = 1 - 0.65 * ease((t - T_TW) / 0.4)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# =====================================================================
# 音（太鼓・矢・ほら貝。すべて合成。うるさくしない）
# =====================================================================

def band_noise(dur, lo, hi, seed, rms, edge_lo=300.0, edge_hi=1200.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def taiko(dur=0.6, seed=1):
    """ドン。低い胴の音（周波数が下がる）に、皮を打つ短い雑音"""
    t = _t(dur)
    f = 50.0 + 90.0 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.0)
    body += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * np.exp(-t * 14)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = np.convolve(n, np.ones(14) / 14, mode="same")
    skin = n * np.exp(-t * 80) * 1.4
    return (body + skin) * np.minimum(1, t * 900)


def swish(dur=0.42, seed=1):
    """ヒュッ。矢の一斉射撃（高めの雑音がすっと上がって下がる）"""
    x = band_noise(dur, 1500.0, 6500.0, seed, 1.0)
    t = _t(dur)
    u = t / dur
    env = (u ** 0.5) * ((1 - u) ** 1.6) * 3.0
    return x * env


def landing(dur=0.3, seed=1):
    """矢が地面や盾にささる音（にぶい雑音）"""
    n = np.random.default_rng(seed).standard_normal(int(SR * dur))
    n = np.convolve(n, np.ones(10) / 10, mode="same")
    t = _t(dur)
    return n * np.exp(-t * 16) * 2.2


def thud(dur=0.06):
    t = _t(dur)
    return np.sin(2 * np.pi * 150 * t) * np.exp(-t * 55)


def horagai(dur=2.4):
    """ほら貝（法螺貝）風の低い長い音。うなりを少し入れる"""
    t = _t(dur)
    f0 = 116.5
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.6 * t)
    x = np.zeros_like(t)
    for n in range(1, 10):
        x += (1.0 / n ** 1.2) * np.sin(2 * np.pi * f0 * n * vib * t + n)
        x += 0.5 * (1.0 / n ** 1.2) * np.sin(2 * np.pi * f0 * 1.006 * n * vib * t)
    att = np.minimum(1, (t / 0.35) ** 1.5)
    rel = np.minimum(1, (dur - t) / 0.9) ** 1.2
    breath = np.convolve(np.random.default_rng(5).standard_normal(len(t)), np.ones(30) / 30, mode="same") * 0.35
    y = (x + breath) * att * rel
    return y / max(1e-9, float(np.max(np.abs(y)))) * 0.9


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(98.0, 146.8, 196.0, 293.7), vol=0.05), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, horagai(2.3), 0.5)
    # 見本の戦い: 一斉射撃ごとに太鼓・矢・着弾
    for i in range(N_VOL_M):
        ti = t_volley_main(i)
        mx.add(max(0.02, ti), taiko(seed=i), 0.9)
        if i < 7 and ti + 0.575 < T_CD[-1]:
            mx.add(ti + 0.575, taiko(seed=100 + i), 0.35)
        mx.add(max(0.0, ti + 0.04), swish(seed=10 + i), 0.38)
        mx.add(ti + 0.52, landing(seed=20 + i), 0.30)
    for u in range(BATTLE_M.n_all):
        td = BATTLE_M.td[u]
        if np.isfinite(td) and td > 0.2:
            mx.add(td, thud(), 0.06)
    mx.add(T_END_M + 0.15, chord([196.0, 293.7, 392.0], 1.6), 0.45)
    mx.add(T_STK1, blip(659.3, 0.15), 0.35)
    # 1万回
    mx.add(T_G0 - 0.5, riser(0.9), 0.5)
    beat(mx, T_D0, T_D1, bpm=124, vol=0.5, accel=True)
    rng = np.random.default_rng(5)
    for b in range(int(D_DUR * 8)):
        mx.add(T_D0 + b / 8, tick(float(rng.uniform(1700, 3300)), 0.03), 0.05 + 0.04 * (b / (D_DUR * 8)))
    mx.add(T_MEAN, thump(), 0.6)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST_A, blip(659.3, 0.15), 0.35)
    mx.add(T_ST_B, blip(784.0, 0.15), 0.35)
    # 腕前の実験
    for i in range(len(K_LIST)):
        mx.add(T_K0 + 0.3 + i * K_DUR * 0.6 / 5, blip(523.3 * (1 + 0.12 * i), 0.12), 0.3)
    mx.add(T_K4, bell(880.0, 1.2), 0.45)
    mx.add(T_LAN, blip(784.0, 0.15), 0.3)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.45)
    for i in range(N_V1):
        ti = T_T1 + i * TW_STEP
        if i % 4 == 0:
            mx.add(ti, taiko(seed=300 + i), 0.55)
        if i % 2 == 0:
            mx.add(ti + 0.02, swish(0.3, seed=400 + i), 0.22)
    mx.add(T_MARCH0, whoosh(0.9), 0.3)
    for k in range(3):
        mx.add(T_MARCH0 + 0.28 * k, taiko(seed=500 + k), 0.7)
    for i in range(N_V2):
        ti = T_T2 + i * TW_STEP
        if i % 4 == 0:
            mx.add(ti, taiko(seed=600 + i), 0.55)
        if i % 2 == 0:
            mx.add(ti + 0.02, swish(0.3, seed=700 + i), 0.22)
    for u in range(BATTLE_T.n_all):
        td = BATTLE_T.td[u]
        if np.isfinite(td) and u % 2 == 0:
            mx.add(td, thud(), 0.04)
    for (a, b_) in ((T_T1, T_T1 + N_V1 * TW_STEP + 0.4), (T_T2, T_T2 + N_V2 * TW_STEP + 0.4)):
        mx.add(a, band_noise(b_ - a, 900.0, 5200.0, int(a * 10), 0.035) *
               np.minimum(1, np.minimum(_t(b_ - a) / 0.3, (b_ - a - _t(b_ - a)) / 0.4)), 1.0, bgm=True)
    mx.add(T_END_T + 0.15, chord([196.0, 293.7, 392.0], 1.6), 0.45)
    mx.add(T_TW_RES, blip(659.3, 0.15), 0.35)
    mx.add(T_TW_RES + 0.5, blip(784.0, 0.15), 0.35)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# =====================================================================
# 照合
# =====================================================================

def run_checks():
    d = data()
    sh = shown()
    checks = []
    for (R, B, fm, fse, em, ese) in d["step"]:
        exact = one_step_expect(R, B, P_HIT)
        checks.append((f"1回の一斉射撃で倒れる人数 {R:.0f}人が{B:.0f}人を撃つ: 速い数え方の平均 vs 閉じた式 B(1-(1-p/B)^R)", float(fm), exact, 5 * float(fse) + 1e-3))
        checks.append((f"同・1人ずつ追う数え方の平均 vs 閉じた式", float(em), exact, 5 * float(ese) + 1e-3))
    red = d["rem"][d["side"] == 1]
    checks += [
        ("勝った側の残りの平均: 速い数え方(1万回) vs 1人ずつ追う数え方(2000回)", sh["mean"], float(d["rem_e"].mean()), 0.6),
    ]
    mfR, mfB, mfv = mean_field(N_R, N_B, P_HIT, P_HIT)
    checks += [
        ("勝った側の残りの平均 vs 平均場（期待値の漸化式）", sh["mean"], mfR, 1.8),
        ("勝った側の残りの平均 vs 連続の理論 sqrt(R^2-B^2)（ばらつきぶん小さい）", sh["mean"], sh["theory"], 3.0),
        ("理論の連続近似の値（約87人）", sh["theory"], 86.6, 0.1),
    ]
    k50b = None
    kw2 = d["kw2"] / N_TRIALS
    ks = np.array(K_LIST, float)
    for i in range(len(ks) - 1):
        if kw2[i] < 0.5 <= kw2[i + 1]:
            k50b = ks[i] + (0.5 - kw2[i]) / (kw2[i + 1] - kw2[i])
    checks += [
        ("50人側の勝率が50%になる腕前の倍率 k vs 理論 (100/50)^2 = 4", sh["k50"], 4.0, 0.15),
        ("同・別の乱数でやり直した k", float(k50b), sh["k50"], 0.08),
        ("k=4 の勝率（50人側）がほぼ50%", float(sh["kw"][3]), 0.5, 0.03),
    ]
    # ひねり: 80人が一度に来る100人に負ける（平均場でも勝てない）／分かれると勝つ
    r1, b1, _ = mean_field(TW_R, 2 * TW_G, P_HIT, P_HIT)
    ra, ba, _ = mean_field(TW_R, TW_G, P_HIT, P_HIT)
    rb, bb, _ = mean_field(max(ra, 0.0), TW_G, P_HIT, P_HIT)
    sr = d["sr"]
    checks += [
        ("ひねり: 平均場で、80人は一度に来る100人に勝てない（残り0.5人未満）", float(r1 < 0.5), 1.0, 0.0),
        ("ひねり: 分かれて来る相手に勝った回の残りの平均 vs 平均場（2回戦ったあと）", float(sr.mean()), float(rb), 3.5),
        ("ひねり: 一度に来ると勝つのは1%未満", float(sh["once"] < 100), 1.0, 0.0),
        ("ひねり: 分かれて来ると勝つのは8割超", float(sh["split"] > 8000), 1.0, 0.0),
    ]
    # 画面の数字が別の乱数のやり直しと同じか
    rem2 = d["rem2"][d["side2"] == 1]
    ow2, sw2 = d["tw2"]
    checks += [
        ("画面の「平均○人」（四捨五入）が別の乱数と同じ", float(sh["mean_i"]), float(math.floor(rem2.mean() + 0.5)), 0.0),
        ("画面の「青軍が勝った回数」が別の乱数と同じ（0回）", float(sh["blue_wins"]), float((d["side2"] == -1).sum()), 0.0),
        ("画面の「一度に来ると勝ち○回」が別の乱数と近い（二項分布の誤差4倍以内）", float(sh["once"]), float(ow2), 4 * math.sqrt(2 * max(1.0, sh["once"])) + 1),
        ("画面の「分かれて来ると勝ち」の%（四捨五入）が別の乱数と同じ", float(sh["split_pct"]), float(math.floor(sw2 / N_TRIALS * 100 + 0.5)), 0.0),
    ]
    # 見本の戦いの記録が画面の状態と一致
    checks += [
        ("見本: 赤軍の最後の生き残りが記録と一致", float(BATTLE_M.alive("R", 1e9)), float(REM_M), 0.0),
        ("見本: 青軍は全滅", float(BATTLE_M.alive("B", 1e9)), 0.0, 0.0),
        ("見本: 赤軍の残りは平均から2人以内（ふつうの結果）", float(REM_M), sh["mean"], 2.0),
        ("見本(ひねり): 赤軍の最後の生き残りが記録と一致", float(BATTLE_T.alive("R", 1e9)), float(REM_T), 0.0),
        ("見本(ひねり): 青軍は全滅", float(BATTLE_T.alive("A", 1e9) + BATTLE_T.alive("G", 1e9)), 0.0, 0.0),
        ("見本(ひねり): 赤軍の残りは、勝った回の平均から4人以内", float(REM_T), float(sr.mean()), 4.0),
        ("答えは C（約85人）: 平均は A(50) B(70) より C(85) にいちばん近い",
         float(abs(sh["mean"] - 85) < min(abs(sh["mean"] - 50), abs(sh["mean"] - 70))), 1.0, 0.0),
        ("答えは C: 平均は 85 から1.5人以内", sh["mean"], 85.0, 1.5),
    ]
    check_answers(checks)
    return mfR, mfv


def zoom_sheet(ts=(8.5, 10.0, 12.0, 28.0, 31.6), name="zoom_v2.png", cols=3):
    if "--times" in sys.argv:                          # 例: --zoom --times 3,26.5 （確認用）
        ts = tuple(float(x) for x in sys.argv[sys.argv.index("--times") + 1].split(","))
        name = "_zoom_try.png"
    """原寸（1080px幅）の切り出し。y 380〜1460（字の範囲）を、時刻ごとに並べる"""
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    ims = []
    for tt in ts:
        p = OUT / f"_zoom_{tt:05.1f}.png"
        core.still(draw, tt, p)
        im = Image.open(p).convert("RGB")
        ims.append(im.crop((0, 380, W, 1460)))
        p.unlink()
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (W * cols + 8 * (cols - 1), 1080 * rows + 8 * (rows - 1)), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (W + 8), (i // cols) * (1080 + 8)))
    sheet.save(OUT / name)
    print("拡大図:", OUT / name, "（時刻", list(ts), "）")


def sheet_v2(ts=(0, 1, 2, 3, 5, 8, 10, 12, 15, 18, 21, 24, 27, 30, 33, 36), name="sheet_v2.png", cols=6, thumb=(270, 480)):
    """要所の一覧。静止画は残さず一覧だけ書き出す"""
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    ims = []
    for tt in ts:
        p = OUT / f"_sheet_{tt:05.1f}.png"
        core.still(draw, float(tt), p)
        ims.append(Image.open(p).convert("RGB").resize(thumb, Image.LANCZOS))
        p.unlink()
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (thumb[0] + 8), (i // cols) * (thumb[1] + 8)))
    sheet.save(OUT / name)
    print("一覧:", OUT / name)


if __name__ == "__main__" and "--compute" not in sys.argv and "--seeds" not in sys.argv and "--sprite" not in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    d = data()
    sh = shown()
    print(f"長さ={DURATION:.1f}秒 / 見本: 一斉射撃 {N_VOL_M}回、赤の残り {REM_M}人、決着 {T_END_M:.1f}秒 / "
          f"ひねり: {N_V1}回＋{N_V2}回、赤の残り {REM_T}人、決着 {T_END_T:.1f}秒")
    print(f"1万回: 赤の勝ち {sh['red_wins']}回・青の勝ち {sh['blue_wins']}回、勝った赤軍の残り 平均 {sh['mean']:.2f}人（標準偏差 {sh['sd']:.2f}）"
          f"／理論 sqrt(100^2-50^2) = {sh['theory']:.1f}")
    print("腕前 k 倍の勝率(50人側):", {k: f"{w * 100:.2f}%" for k, w in zip(K_LIST, sh["kw"])}, f"→ 互角の k = {sh['k50']:.2f}")
    print(f"ひねり(80人 vs 100人): 一度に来ると勝ち {sh['once']}回／分かれて来ると勝ち {sh['split']}回（{sh['split'] / N_TRIALS * 100:.1f}%）、"
          f"勝った回の残り 平均 {d['sr'].mean():.1f}人")
    mfR, _ = run_checks()
    print(f"平均場の残り: {mfR:.1f}人")
    if "--zoom" in sys.argv:
        zoom_sheet()
    elif "--sheet" in sys.argv:
        sheet_v2()
    elif "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0]
        stills(draw, [x for x in ts if x < DURATION], OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
