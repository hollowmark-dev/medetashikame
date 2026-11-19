"""15×15の迷路、右手をつける？気分で選ぶ？ 同じ迷路を2人で歩く、を1万個。— 2026-11-04 作成（公開予定 11/19・ナレーションなし・45秒前後）

変える条件は「歩き方」だけ。同じ迷路・同じスタート（左上）とゴール（右下）で、服の色だけ違う2人を歩かせる。
計算の置き方・答えの決め方は sims/meiro_model.py の docstring に、計算の前に固定してある（結果を見て変えていない）。ここに写す:

【置き方】
  迷路  : 15×15マス。行き止まりはあるが、ぐるっと回れる道はない（全域木）。ウィルソンの方法で均等に作る。1万個。
  歩数  : マスを1つ動くごとに1歩。
  右手  : 右の壁に手をつけて歩く（右→前→左→後ろの順に進める方へ）。
  気分  : 分かれ道でだけ、来た道以外からでたらめに選ぶ。行き止まりでは引き返す。通った道は覚えていない。
  覚える（ひねり1）: 分かれ道で、まだ通っていない道からでたらめに選ぶ。なければ来た道を戻る。
  輪（ひねり2）: 同じ1万個の壁を8%ほど多めに壊して輪を作り、ゴールを真ん中に置く。右手が同じ場所・同じ向きに戻ったら「着けない」。

【答えの決め方】（answer_by_rule。計算の前に固定）
  歩数の中央値の比 r = 右手 ÷ 気分。 r ≤ 0.8 → 右手 ／ r ≥ 1.25 → 気分 ／ それ以外 → ほぼ同じ

【画面】
  選択肢: A 右手 ／ B ほぼ同じ ／ C 気分（正解の記号は A。run_checks で確かめる）
  見本の1回: 乱数の順で最初に「右手が200〜250歩、かつ、気分が1,000〜1,500歩」の迷路（結果を見て選び直していない）。
             1万個の中の1個そのもの（run_checks で、同じ乱数で数え直して一致を確かめる）。
  歩く場面: 同じ速さで歩く（右手が着くまで）→ 気分だけ早送りで最後まで → 結果。迷路は2つ並べて広く（1つ450px）、人は印つきの絵を迷路の上に重ねる。
  1万個: 歩数のヒストグラム（横は対数目盛り）が1万個ぶん積み上がる → 中央値・いちばん長い回・何回に1回。
  ひねり1: 通った道を覚えて歩く気分 → 中央値は右手と同じ（札1枚）。 ひねり2: 輪があってゴールが真ん中だと、右手は着けない回が約5回に3回（計算での見立て）。
  締め: 「右手で歩いて元の場所に戻ってきたら、あなたはどうしますか？」
  言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。
"""
import hashlib
import inspect
import math
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import meiro_model as MM  # noqa: E402

SLUG = "meiro-migite"
OUT = ROOT / "out" / SLUG

W_, H_ = MM.W, MM.H
START, GOAL, MID = (0, 0), (W_ - 1, H_ - 1), (W_ // 2, H_ // 2)
MOVES = MM.D


# =====================================================================
# 1万個（キャッシュ）と見本の取り出し
# =====================================================================
def edge_list():
    """迷路のつながり方の並び（横の辺 → 縦の辺）。トーナメントの番号と同じ並びで保存する"""
    es = []
    for y in range(H_):
        for x in range(W_ - 1):
            es.append(((x, y), (x + 1, y)))
    for y in range(H_ - 1):
        for x in range(W_):
            es.append(((x, y), (x, y + 1)))
    return es


EDGES = edge_list()
EDGE_ID = {e: i for i, e in enumerate(EDGES)}


def eid(a, b):
    return EDGE_ID[(a, b) if (a, b) in EDGE_ID else (b, a)]


def _src_hash():
    src = "".join(inspect.getsource(f) for f in (MM.wilson, MM.right_hand, MM.mood, MM.remember, MM.add_loops, MM.stream))
    src += repr((MM.SEED, MM.N, MM.W, MM.H, MM.D))
    return hashlib.md5(src.encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万個の歩数。計算には40秒ほどかかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"arrays_{_src_hash()}.npz"
    if f.exists():
        z = np.load(f)
        m = {k: z[k] for k in z.files}
    else:
        import time
        t0 = time.time()
        n = MM.N
        right, mood, rem = np.zeros(n, np.int32), np.zeros(n, np.int32), np.zeros(n, np.int32)
        r2, mood2, rem2 = np.zeros(n, np.int32), np.zeros(n, np.int32), np.zeros(n, np.int32)
        bits = np.zeros((n, len(EDGES)), np.uint8)
        for d in MM.stream(n):
            i = d["i"]
            right[i], mood[i], rem[i] = d["right"], d["mood"], d["rem"]
            r2[i] = -1 if d["r2"] is None else d["r2"]
            mood2[i], rem2[i] = d["mood2"], d["rem2"]
            tr = d["tree"]
            bits[i] = [1 if b in tr[a] else 0 for a, b in EDGES]
        print(f"  1万個の迷路 {time.time() - t0:.0f}秒")
        m = dict(right=right, mood=mood, rem=rem, r2=r2, mood2=mood2, rem2=rem2, bits=bits)
        np.savez_compressed(f, **m)
    _RES["m"] = m
    return m


def answer_by_rule(r):
    """r: 右手の中央値 ÷ 気分の中央値。'right'（右手）/'same'（ほぼ同じ）/'mood'（気分）"""
    if r <= 0.8:
        return "right"
    if r >= 1.25:
        return "mood"
    return "same"


def op_from_bits(row):
    op = {(x, y): set() for y in range(H_) for x in range(W_)}
    for k in np.nonzero(row)[0]:
        a, b = EDGES[int(k)]
        op[a].add(b)
        op[b].add(a)
    return op


def pick_ids():
    """乱数の順で最初の、右手が200〜250歩・気分が1,000〜1,500歩の迷路 と、右手が着けない輪の迷路（乱数の順で最初）"""
    m = results()
    ok = (m["right"] >= 200) & (m["right"] <= 250) & (m["mood"] >= 1000) & (m["mood"] <= 1500)
    return int(np.nonzero(ok)[0][0]), int(np.nonzero(m["r2"] < 0)[0][0])


_SAMPLE = {}


def samples():
    """見本の迷路（歩く場面）と、輪の迷路（ひねり2）。どちらも同じ乱数で作り直す"""
    if _SAMPLE:
        return _SAMPLE
    i_main, i_loop = pick_ids()
    last = None
    for d in MM.stream(max(i_main, i_loop) + 1):
        if d["i"] == i_main:
            tree = d["tree"]
            R = random.Random()
            R.setstate(d["mood_state"])
            pm = MM.mood_path(tree, START, GOAL, R)
            pr, pd, cyc = MM.right_path(tree, START, GOAL)
            _SAMPLE.update(i=i_main, tree=tree, pm=pm, pr=pr, pd=pd, cyc=cyc, right=d["right"], mood=d["mood"], rem=d["rem"],
                           eid_r=np.array([eid(pr[k], pr[k + 1]) for k in range(len(pr) - 1)], np.int32),
                           eid_m=np.array([eid(pm[k], pm[k + 1]) for k in range(len(pm) - 1)], np.int32))
        if d["i"] == i_loop:
            last = d
    lo = last["loop"]
    pr, pd, cyc = MM.right_path(lo, START, MID)
    broken = [(a, b) for a, b in EDGES if b in lo[a] and b not in last["tree"][a]]
    _SAMPLE["loop"] = dict(i=i_loop, op=lo, tree=last["tree"], pr=pr, pd=pd, cyc=cyc, broken=broken,
                           eid_r=np.array([eid(pr[k], pr[k + 1]) for k in range(len(pr) - 1)], np.int32))
    return _SAMPLE


def stats():
    m = results()
    return dict(
        med_r=float(np.median(m["right"])), med_m=float(np.median(m["mood"])), med_c=float(np.median(m["rem"])),
        max_r=int(m["right"].max()), max_m=int(m["mood"].max()), max_c=int(m["rem"].max()),
        min_r=int(m["right"].min()), min_m=int(m["mood"].min()),
        p99_r=int(np.sort(m["right"])[MM.N * 99 // 100]), p99_m=int(np.sort(m["mood"])[MM.N * 99 // 100]),
        wins=float((m["right"] < m["mood"]).mean()), fail=int((m["r2"] < 0).sum()),
        med_r2=float(np.median(m["r2"][m["r2"] >= 0])), med_m2=float(np.median(m["mood2"])), med_c2=float(np.median(m["rem2"])))


def report():
    s = stats()
    r = s["med_r"] / s["med_m"]
    key = answer_by_rule(r)
    print(f"乱数の種 {MM.SEED}  迷路 {MM.N}個  {W_}×{H_}マス  左上→右下")
    print(f"  歩数の中央値: 右手 {s['med_r']:.0f}  気分 {s['med_m']:.0f}  覚える {s['med_c']:.0f}   比 {r:.3f} → {key}")
    print(f"  いちばん長い回: 右手 {s['max_r']}  気分 {s['max_m']:,}  覚える {s['max_c']}   99%点: 右手 {s['p99_r']}  気分 {s['p99_m']:,}")
    print(f"  右手が気分より少ない歩数で着いた回 {s['wins'] * 100:.1f}%  → 気分が同じか勝つのは 約{1 / (1 - s['wins']):.1f}回に1回")
    print(f"  輪の迷路・ゴール真ん中: 右手が着けない {s['fail']}/{MM.N}（{s['fail'] / MM.N * 100:.1f}%）  中央値 気分 {s['med_m2']:.0f}  覚える {s['med_c2']:.0f}")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)

S0 = samples()
N_R, N_M = len(S0["pr"]) - 1, len(S0["pm"]) - 1
LOOP = S0["loop"]

if __name__ == "__main__" and "--pick" in sys.argv:
    print(f"見本: 迷路 #{S0['i']}（乱数の順で最初に 右手200〜250歩・気分1,000〜1,500歩）  右手 {N_R}歩  気分 {N_M}歩  覚える {S0['rem']}歩")
    print(f"輪の迷路: #{LOOP['i']}（乱数の順で最初に右手が着けない）  壊した壁 {len(LOOP['broken'])}  輪の1周 {len(LOOP['pr']) - 1 - LOOP['cyc']}歩")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, whoosh)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.19"                                  # 日付欄（公開予定日）

C_R, C_RD = "#3f7fb5", "#2a5f8f"                     # 右手の人（青い服）
C_M, C_MD = "#ee8a2b", "#b56412"                     # 気分の人（オレンジの服）
SKIN, HAIR, PANTS = "#f6d3b0", "#4a3528", "#3b4a68"
FLOOR = "#fffdf3"
GOLD_D = "#d79a00"

LABELS = ["右手", "ほぼ同じ", "気分"]
KEY_LABEL = {"right": "右手", "same": "ほぼ同じ", "mood": "気分"}
CORRECT = 0                                          # answer_by_rule の結果の位置（A）

BIG_Q3 = ["迷路、", "右手をつける？", "気分で選ぶ？"]            # 1コマ目の3行（同じ大きさ）
BIG_Q = ["迷路、", "右手をつける？気分で選ぶ？"]                    # 定位置（上）の2行
DETAIL_RULE = "同じ迷路・同じスタートとゴール。ちがうのは歩き方だけ"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RATE = 55.0                                         # 歩く速さ（歩/秒）。右手が着くまで、ふたりとも同じ速さ
FF_T = 3.2                                          # 気分だけ早送り
MZ = 450.0                                          # 迷路1つの大きさ（px）。1マス30px
CS = MZ / W_
LX0, RX0 = 80.0, 560.0                              # 左（右手）・右（気分）の迷路の左端
P_FINAL, P_INTRO = 665.0, 880.0                     # 迷路の上端（定位置・冒頭）
CD_X, CD_Y = 540.0, 1105.0
LAP_RATE = 80.0                                     # ひねり2: 輪を回る速さ（歩/秒）


def setup():
    global T_W0, T_A, AQ, T_B, T_D0, T_H0, T_D1, T_DN, T_DN2, T_REV, T_TW1, T_TW2, T_LAP0, T_RES, T_RES2, T_Q, DURATION, SCENES
    T_W0 = T_GO + 0.5                               # 歩き出し
    T_A = T_W0 + N_R / RATE                         # 右手がゴールに着く
    AQ = max(0.0, (N_M - N_R) / (FF_T * RATE) - 1.0)
    T_B = T_A + FF_T                                # 気分が着く
    T_D0 = T_B + 3.1                                # 1万個へ
    T_H0 = T_D0 + 0.8
    T_D1 = T_H0 + 3.0                               # 積み終わる
    T_DN = T_D1 + 0.1                               # 中央値
    T_DN2 = T_DN + 3.0                              # いちばん長い回・何回に1回
    T_REV = T_DN2 + 3.3                             # 答え
    T_TW1 = T_REV + 3.0                             # ひねり1
    T_TW2 = T_TW1 + 3.8                             # ひねり2
    T_LAP0 = T_TW2 + 0.9                            # 輪を歩き出す
    lap = len(LOOP["pr"]) - 1
    T_RES = T_LAP0 + lap / LAP_RATE + 0.1           # 1周して戻ったあと、結果
    T_RES2 = T_RES + 1.4                            # 札のあと、結果の文
    T_Q = T_RES2 + 3.4                              # 締め
    DURATION = T_Q + 4.8
    SCENES = [("見本の1回（歩く）", T_GO, T_D0), ("1万個の迷路・答え", T_D0, T_TW1), ("ひねり1（覚えて歩く）", T_TW1, T_TW2),
              ("ひねり2（輪・ゴールが真ん中）", T_TW2, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def once_in(f):
    v = 1.0 / f
    return f"約{v:.1f}回に1回" if v < 10 else f"約{int(round(v))}回に1回"


def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def window(t, t0, t1, fin=0.3, fout=0.3):
    """t0 から t1 まで 1。前後はなめらかに出入り"""
    a = ease((t - t0) / fin) if fin > 0 else (1.0 if t >= t0 else 0.0)
    b = 1 - ease((t - t1 + fout) / fout) if fout > 0 else (0.0 if t >= t1 else 1.0)
    return clamp01(min(a, b))


# ---------- 絵: 迷路 ----------
_MZS = {}


def maze_surface(op, size, broken=(), key=None, lw=None):
    kk = (key, round(size))
    if key is not None and kk in _MZS:
        return _MZS[kk]
    cs = size / W_
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(size) + 12, int(size) + 12)
    c = cairo.Context(s)
    c.translate(6, 6)
    rrect(c, 0, 0, size, size, 6)
    c.set_source_rgba(*hexrgb(FLOOR))
    c.fill()
    for cell, col in ((START, "#d8f0d8"), (GOAL, "#fbd9d6")):
        c.rectangle(cell[0] * cs, cell[1] * cs, cs, cs)
        c.set_source_rgba(*hexrgb(col))
        c.fill()
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_width(lw or max(2.0, cs * 0.14))
    c.set_source_rgba(*hexrgb(INK, 0.95))
    for y in range(H_):
        for x in range(W_):
            if x < W_ - 1 and (x + 1, y) not in op[(x, y)]:
                c.move_to((x + 1) * cs, y * cs)
                c.line_to((x + 1) * cs, (y + 1) * cs)
            if y < H_ - 1 and (x, y + 1) not in op[(x, y)]:
                c.move_to(x * cs, (y + 1) * cs)
                c.line_to((x + 1) * cs, (y + 1) * cs)
    c.stroke()
    c.rectangle(0, 0, size, size)
    c.set_line_width((lw or max(2.0, cs * 0.14)) * 1.3)
    c.set_source_rgba(*hexrgb(INK, 0.95))
    c.stroke()
    if broken:                                          # 壊した壁（金の点線）
        for wmul, col in ((0.40, "#7a4f00"), (0.28, "#ffc400")):      # 太い金の線（ふちどり付き）
            c.set_line_width(max(5.0, cs * wmul))
            c.set_source_rgba(*hexrgb(col, 1.0))
            for a, b in broken:
                if a[1] == b[1]:
                    c.move_to((a[0] + 1) * cs, a[1] * cs + cs * 0.06)
                    c.line_to((a[0] + 1) * cs, (a[1] + 1) * cs - cs * 0.06)
                else:
                    c.move_to(a[0] * cs + cs * 0.06, (a[1] + 1) * cs)
                    c.line_to((a[0] + 1) * cs - cs * 0.06, (a[1] + 1) * cs)
            c.stroke()
    if key is not None:
        _MZS[kk] = s
    return s


FLOOR0 = "#cfd8e3"                                   # 冒頭: 描き始めの床の色（壁が描かれるにつれて、ふつうの床の色へ）
T_DRAW = 1.0                                         # 冒頭: 2つの迷路を同時に描き終える秒


def maze_progress(op, size, prog, key):
    """冒頭用: 壁の線が左上のスタートから斜めに順に描かれていく（prog 0〜1）。30段に丸めて取っておく"""
    q = int(round(clamp01(prog) * 30))
    kk = (key, "p", round(size), q)
    if kk in _MZS:
        return _MZS[kk]
    p = q / 30.0
    cs = size / W_
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(size) + 12, int(size) + 12)
    c = cairo.Context(s)
    c.translate(6, 6)
    f0, f1 = hexrgb(FLOOR0), hexrgb(FLOOR)
    rrect(c, 0, 0, size, size, 6)
    c.set_source_rgba(*[f0[i] + (f1[i] - f0[i]) * p for i in range(3)], 1.0)
    c.fill()
    for cell, col in ((START, "#d8f0d8"), (GOAL, "#fbd9d6")):
        c.rectangle(cell[0] * cs, cell[1] * cs, cs, cs)
        c.set_source_rgba(*hexrgb(col))
        c.fill()
    thr = p * (W_ + H_)                                # 左上からの斜めの順（x+y）
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    lw = max(2.0, cs * 0.14)
    c.set_line_width(lw)
    c.set_source_rgba(*hexrgb(INK, 0.95))
    for y in range(H_):
        for x in range(W_):
            if x < W_ - 1 and (x + 1, y) not in op[(x, y)] and x + 1 + y <= thr:
                c.move_to((x + 1) * cs, y * cs)
                c.line_to((x + 1) * cs, (y + 1) * cs)
            if y < H_ - 1 and (x, y + 1) not in op[(x, y)] and x + y + 1 <= thr:
                c.move_to(x * cs, (y + 1) * cs)
                c.line_to((x + 1) * cs, (y + 1) * cs)
    c.stroke()
    c.set_line_width(lw * 1.3)                          # まわりの壁
    for k in range(W_):
        for (x0, y0, x1, y1, d) in ((k * cs, 0, (k + 1) * cs, 0, k), (0, k * cs, 0, (k + 1) * cs, k),
                                    (k * cs, size, (k + 1) * cs, size, W_ + k), (size, k * cs, size, (k + 1) * cs, W_ + k)):
            if d <= thr:
                c.move_to(x0, y0)
                c.line_to(x1, y1)
    c.stroke()
    _MZS[kk] = s
    return s


def cell_c(x0, y0, cs, c):
    return x0 + (c[0] + 0.5) * cs, y0 + (c[1] + 0.5) * cs


def draw_flag(ctx, x, y, cs):
    k = cs / 30.0
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x - 6 * k, y + 11 * k)
    ctx.line_to(x - 6 * k, y - 13 * k)
    _stroke(ctx, 3.0 * k, INK, 0.95)
    ctx.move_to(x - 6 * k, y - 13 * k)
    ctx.line_to(x + 11 * k, y - 7 * k)
    ctx.line_to(x - 6 * k, y - 1 * k)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(RED))
    ctx.fill_preserve()
    _stroke(ctx, 2.0 * k, INK, 0.9)


def draw_trail(ctx, x0, y0, cs, path, eids, s, color, a0=0.30, wmul=0.38):
    """歩いた跡。同じ道を通るほど濃くなる。s = 進んだ歩数（小数）"""
    k = int(min(s, len(path) - 1))
    if k > 0:
        cnt = np.bincount(eids[:k], minlength=len(EDGES))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(cs * wmul)
        for e in np.nonzero(cnt)[0]:
            a, b = EDGES[int(e)]
            ax, ay = cell_c(x0, y0, cs, a)
            bx, by = cell_c(x0, y0, cs, b)
            ctx.move_to(ax, ay)
            ctx.line_to(bx, by)
            ctx.set_source_rgba(*hexrgb(color, min(0.95, 1 - (1 - a0) ** int(cnt[e]))))
            ctx.stroke()
    if k < len(path) - 1:
        f = s - k
        ax, ay = cell_c(x0, y0, cs, path[k])
        bx, by = cell_c(x0, y0, cs, path[k + 1])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(cs * wmul)
        ctx.move_to(ax, ay)
        ctx.line_to(ax + (bx - ax) * f, ay + (by - ay) * f)
        ctx.set_source_rgba(*hexrgb(color, a0))
        ctx.stroke()


def pos_at(x0, y0, cs, path, s):
    k = int(min(s, len(path) - 1))
    f = 0.0 if k >= len(path) - 1 else s - k
    ax, ay = cell_c(x0, y0, cs, path[k])
    if f <= 0:
        return ax, ay, k
    bx, by = cell_c(x0, y0, cs, path[k + 1])
    return ax + (bx - ax) * f, ay + (by - ay) * f, k


# ---------- 絵: 歩く人（服の色だけ違う） ----------

def draw_walker(ctx, x, y, shirt, shirt_d, t, move=False, face=1.0, cheer=0.0, S=1.35, lean=0.0):
    """印つきの人。足もとの輪は服の色。(x, y) は足もと。face: 1 = 右向き、-1 = 左向き"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(S, S)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ph = t * 10.0
    bob = 2.2 * abs(math.sin(ph)) if move else 1.2 * math.sin(t * 2.4)
    bob += cheer * 5.0 * abs(math.sin(t * 9.0))
    ctx.save()                                           # 足もとの輪（服の色）
    ctx.translate(0, 3)
    ctx.scale(1, 0.40)
    ctx.arc(0, 0, 24, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(shirt, 0.45))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, shirt_d, 0.95)
    for sg in (-1, 1):                                   # 足
        sw = 5.0 * sg * math.sin(ph) if move else 0.0
        core.rrect(ctx, sg * 6.5 - 4.5 + sw, -17 - bob * 0.3, 9, 18, 4)
        ctx.set_source_rgba(*hexrgb(PANTS))
        ctx.fill_preserve()
        _stroke(ctx, 2.2, INK, 0.9)
    for sg in (-1, 1):                                   # うで
        sw = -6.0 * sg * math.sin(ph) if move else 0.0
        ax, ay = sg * 15, -36 - bob
        if cheer > 0:
            bx, by = sg * 20, -58 - bob - 3 * math.sin(t * 9 + sg)
        else:
            bx, by = sg * 17 + sw * 0.4, -20 - bob
        ctx.move_to(ax, ay)
        ctx.line_to(bx, by)
        ctx.set_source_rgba(*hexrgb(shirt_d))
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.arc(bx, by, 4.6, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 2.0, INK, 0.9)
    core.rrect(ctx, -15, -46 - bob, 30, 34, 11)          # 胴（服）
    ctx.set_source_rgba(*hexrgb(shirt))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.95)
    hy = -64 - bob                                       # 頭
    ctx.arc(0, hy, 15.5, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.95)
    ctx.new_path()                                       # かみ
    ctx.arc(0, hy - 1, 16.5, math.pi * 1.03, math.pi * 1.97)
    ctx.curve_to(10, hy - 12, -2, hy - 14, -13, hy - 7)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(HAIR))
    ctx.fill_preserve()
    _stroke(ctx, 2.4, INK, 0.9)
    for sg in (-1, 1):                                   # 目
        ctx.arc(sg * 5.6 + face * 2.8, hy + 1.5, 2.1, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
    ctx.arc(face * 2.8, hy + 7, 4.0, 0.15 * math.pi, 0.85 * math.pi)
    _stroke(ctx, 2.0, INK, 0.85)
    ctx.restore()


def draw_hand_on_wall(ctx, px, py, d, cs, S=1.35):
    """右手: 進む向き d の右がわの壁に手をつけている（腕を壁のほうへのばす）。(px, py) はマスの中心"""
    rd = MOVES[(d + 1) % 4]
    hx, hy = px + rd[0] * cs * 0.66, py + rd[1] * cs * 0.66
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(px, py - 26 * S * 0.8)
    ctx.line_to(hx, hy)
    ctx.set_source_rgba(*hexrgb(C_RD, 0.97))
    ctx.set_line_width(11)
    ctx.stroke()
    ctx.arc(hx, hy, 8.5, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.95)


# ---------- 歩く場面 ----------

def right_s(t):
    return min(float(N_R), max(0.0, t - T_W0) * RATE)


def mood_s(t):
    if t <= T_W0:
        return 0.0
    if t <= T_A:
        return (t - T_W0) * RATE
    u = clamp01((t - T_A) / FF_T)
    return N_R + (N_M - N_R) * (u + AQ * u * u) / (1 + AQ)


def draw_panel_maze(ctx, t, x0, y0, who):
    S = samples()
    key = "main"
    if t < T_DRAW:
        ctx.set_source_surface(maze_progress(S["tree"], MZ, ease(t / T_DRAW), key), x0 - 6, y0 - 6)
    else:
        ctx.set_source_surface(maze_surface(S["tree"], MZ, key=key), x0 - 6, y0 - 6)
    ctx.paint()
    gx, gy = cell_c(x0, y0, CS, GOAL)
    draw_flag(ctx, gx, gy, CS)
    if who == 0:
        path, eids, s, col = S["pr"], S["eid_r"], right_s(t), C_R
        shirt, shirt_d = C_R, C_RD
    else:
        path, eids, s, col = S["pm"], S["eid_m"], mood_s(t), C_M
        shirt, shirt_d = C_M, C_MD
    draw_trail(ctx, x0, y0, CS, path, eids, s, col)
    px, py, k = pos_at(x0, y0, CS, path, s)
    nxt = path[min(k + 1, len(path) - 1)]
    cur = path[min(k, len(path) - 1)]
    dx = nxt[0] - cur[0]
    if dx == 0 and k > 0:
        dx = cur[0] - path[k - 1][0]
    face = 1.0 if dx >= 0 else -1.0
    move = t < T_W0 or ((who == 0 and t < T_A) or (who == 1 and t < T_B))      # 歩き出すまでは、その場で足踏み
    done = (who == 0 and t >= T_A) or (who == 1 and t >= T_B)
    cheer = 1.0 if done else 0.0
    draw_walker(ctx, px, py + CS * 0.30, shirt, shirt_d, t, move=move, face=face, cheer=cheer)
    if who == 0 and not done:
        dd = S["pd"][min(k + 1, len(S["pd"]) - 1)]
        draw_hand_on_wall(ctx, px, py, dd, CS)


def head_label(ctx, x, y, col, s, a=1.0):
    w = core.text_width(s, 40)
    x0 = x - (w + 44) / 2
    ctx.arc(x0 + 15, y, 13, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.9 * a)
    text(ctx, s, x0 + 44, y, 40, INK, align="left", alpha=a)


def draw_walk_text(ctx, t, P0, m):
    cxs = (LX0 + MZ / 2, RX0 + MZ / 2)
    head_label(ctx, cxs[0], P0 + MZ + 32, C_R, "右手をつける")
    head_label(ctx, cxs[1], P0 + MZ + 32, C_M, "気分で選ぶ")
    for cx, l1, l2 in ((cxs[0], "右の壁に手をつけて", "そのまま進む"), (cxs[1], "分かれ道は適当に選ぶ", "通った道は覚えない")):
        cc = min(cx, 925 - core.text_width(l1, 32) / 2)
        text(ctx, l1, cc, P0 + MZ + 68, 32, INK, bold=False)
        text(ctx, l2, cc, P0 + MZ + 102, 32, INK, bold=False)
    if m < 0.999:
        return
    a2 = clamp01((t - T_GO) / 0.3)
    if a2 <= 0:
        return
    yc = 1283.0
    sr, sm = right_s(t), mood_s(t)
    fin = (t >= T_A, t >= T_B)
    for i, (cx, s_) in enumerate(((cxs[0], sr), (cxs[1], sm))):
        n = int(s_)
        w = core.text_width(f"{n:,}歩", 58)
        cc = min(cx, 925 - w / 2)
        text(ctx, f"{n:,}歩", cc, yc, 58, RED if fin[i] else INK, alpha=a2)
    if t >= T_A:                                          # ゴール！
        text(ctx, "ゴール！", cxs[0], 1336, 36, RED, alpha=ease_out((t - T_A) / 0.25))
    if T_A <= t < T_B:
        text(ctx, "ここから早送り", min(cxs[1], 925 - 130), 1336, 36, INK, alpha=ease_out((t - T_A) / 0.25))
    if t >= T_B:
        text(ctx, "ゴール！", min(cxs[1], 925 - 80), 1336, 36, RED, alpha=ease_out((t - T_B) / 0.25))
    text(ctx, "たとえば、この1回では", 500, 1392, 36, INK, alpha=a2)
    text(ctx, "旗＝ゴール　1マス＝1歩　跡が濃い道＝何度も通った道", 500, 1434, 26, PENCIL, bold=False, alpha=a2)


def scene_alpha(t):
    if t < T_D0:
        return 1.0
    return 1 - ease((t - T_D0) / 0.4)


def draw_walk_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    P0 = P_FINAL + (P_INTRO - P_FINAL) * (1 - m)
    ybot = P0 + MZ + 128
    ca = ease(clamp01(t / T_DRAW))                       # 服の色の薄い札は、迷路が描かれるあいだに色づく
    ctx.push_group()
    for x0, tint in ((LX0, "#dce9f5"), (RX0, "#fbe7d0")):    # 服の色の薄い札（迷路と説明のうしろ）
        rrect(ctx, x0 - 14, P0 - 16, MZ + 28, ybot - P0 + 16, 18)
        ctx.set_source_rgba(*hexrgb(tint, 0.95 * ca))
        ctx.fill()
    draw_panel_maze(ctx, t, LX0, P0, 0)
    draw_panel_maze(ctx, t, RX0, P0, 1)
    draw_walk_text(ctx, t, P0, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 1万個（ヒストグラム） ----------
HX0, HPW = 110.0, 800.0
LOG_LO, LOG_HI, NB = 1.4, 4.4, 40
H_TOPS, H_PH = (735.0, 995.0), 245.0                 # 右手・気分のグラフの上端と高さ


def hist_counts(vals, m):
    lv = np.log10(vals[:m].astype(float))
    c, _ = np.histogram(lv, bins=NB, range=(LOG_LO, LOG_HI))
    return c


_HMAX = {}


def hist_max():
    if "m" not in _HMAX:
        r = results()
        _HMAX["m"] = float(max(hist_counts(r["right"], MM.N).max(), hist_counts(r["mood"], MM.N).max()))
    return _HMAX["m"]


def log_x(v):
    return HX0 + (math.log10(v) - LOG_LO) / (LOG_HI - LOG_LO) * HPW


_MINI = {}


def mini_maze(i):
    if i not in _MINI:
        if len(_MINI) > 200:
            _MINI.clear()
        _MINI[i] = maze_surface(op_from_bits(results()["bits"][i]), 130, lw=2.0)
    return _MINI[i]


def draw_stats(ctx, t):
    a = window(t, T_D0, T_TW1, 0.35, 0.35)
    if a <= 0:
        return
    r = results()
    st = stats()
    ctx.push_group()
    pr = clamp01((t - T_H0) / (T_D1 - T_H0))
    m_rev = MM.N if pr >= 1 else max(1, int(MM.N * ease(pr)))
    ta = 1 - ease((t - T_REV) / 0.3)                   # 題は答えが出る前まで
    if ta > 0:
        text(ctx, "1万個の迷路で歩数をくらべる", 100, 628, 38, INK, align="left", alpha=ta)
        text(ctx, f"迷路 {m_rev:,} / 10,000 個目", 100, 670, 28, PENCIL, align="left", bold=False, alpha=ta)
        mi = min(m_rev, MM.N) - 1
        ctx.set_source_surface(mini_maze(mi), 788 - 6, 596 - 6)
        ctx.paint_with_alpha(ta * (1 - ease((t - T_DN) / 0.3)))
    ymax = hist_max()
    for k, (vals, col, nm) in enumerate(((r["right"], C_R, "右手"), (r["mood"], C_M, "気分"))):
        top = H_TOPS[k]
        base = top + H_PH
        cnt = hist_counts(vals, m_rev)
        bw = HPW / NB
        ctx.move_to(HX0 - 10, base)
        ctx.line_to(HX0 + HPW + 10, base)
        _stroke(ctx, 3, INK, 0.75)
        for v in (100, 1000, 10000):                     # 目盛りの縦線
            ctx.move_to(log_x(v), top - 4)
            ctx.line_to(log_x(v), base)
            ctx.set_dash([4, 6])
            _stroke(ctx, 1.6, PENCIL, 0.5)
            ctx.set_dash([])
        for i in range(NB):
            if cnt[i] <= 0:
                continue
            hh = max(2.0, cnt[i] / ymax * H_PH)
            rrect(ctx, HX0 + i * bw + 1.5, base - hh, bw - 3, hh, 3)
            ctx.set_source_rgba(*hexrgb(col, 0.92))
            ctx.fill()
        med, mx_ = (st["med_r"], st["max_r"]) if k == 0 else (st["med_m"], st["max_m"])
        if k == 0:                                       # 右手: 山の右の空き（右そろえ）
            al, xx = "right", 905
        else:                                            # 気分: 山の左の空き（左そろえ）
            al, xx = "left", 106
        text(ctx, nm, xx, top + 26, 42, INK, align=al)
        if t >= T_DN:                                    # 中央値の線と数字
            u = ease_out((t - T_DN) / 0.4)
            xm = log_x(med)
            ctx.move_to(xm, top + 4)
            ctx.line_to(xm, base)
            ctx.set_dash([9, 6])
            _stroke(ctx, 4, RED, 0.9 * u)
            ctx.set_dash([])
            text(ctx, f"中央値 {fmt(med)}歩", xx, top + 86, 56, RED, align=al, alpha=u)
        if t >= T_DN2:
            u = ease_out((t - T_DN2) / 0.3)
            text(ctx, f"いちばん長い回 {fmt(mx_)}歩", xx, top + 138, 34, RED, align=al, alpha=u)
    yb = H_TOPS[1] + H_PH
    for v, lab in ((100, "100"), (1000, "1,000"), (10000, "10,000")):
        text(ctx, lab, log_x(v), yb + 30, 30, INK, bold=False)
    text(ctx, "横軸＝歩数（目盛りは10倍ずつ）", 500, yb + 70, 30, INK, bold=False)
    if t >= T_DN:
        u = ease_out((t - T_DN) / 0.3)
        text(ctx, "中央値＝1万回の ちょうど真ん中の値", 500, yb + 112, 30, INK, bold=False, alpha=u * (1 - ease((t - T_REV) / 0.3)))
        q = 1 - ease((t - T_DN2) / 0.3)
        text(ctx, f"気分は右手の 約{st['med_m'] / st['med_r']:.1f}倍", 500, yb + 170, 40, INK, alpha=u * q)
    if t >= T_DN2:
        u = ease_out((t - T_DN2) / 0.3)
        text(ctx, f"気分が右手と同じか勝つのは {once_in(1 - st['wins'])}", 500, yb + 170, 34, INK, alpha=u * (1 - ease((t - T_REV) / 0.3)))
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.1) / 0.3)
        note.sticky(ctx, f"正解は『{KEY_LABEL[answer_key()]}』。", 500, 655, 46, "yellow", fg=RED, a=b, tilt=-0.02)
        c2 = ease_out((t - T_REV - 0.5) / 0.3)                 # 差を大きな札で（横軸は10倍ずつなので、差が小さく見える）
        note.sticky(ctx, f"気分は右手の約{st['med_m'] / st['med_r']:.1f}倍歩く", 500, 1410, 50, "pink", fg=RED, a=c2, tilt=0.015)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def answer_key():
    st = stats()
    return answer_by_rule(st["med_r"] / st["med_m"])


# ---------- ひねり1（通った道を覚えて歩く） ----------

def draw_tw1(ctx, t):
    a = window(t, T_TW1, T_TW2, 0.35, 0.35)
    if a <= 0:
        return
    st = stats()
    ctx.push_group()
    d = ease_out((t - T_TW1 - 0.1) / 0.3)
    note.sticky(ctx, "気分でも、通った道を\n覚えていたら？", 500, 700, 40, "pink", fg=RED, a=d, tilt=-0.015)
    rows = (("右手", C_R, st["med_r"]), ("気分（通った道を覚える）", "#4fa15f", st["med_c"]), ("気分（覚えない）", C_M, st["med_m"]))
    pr = ease(clamp01((t - T_TW1 - 0.9) / 1.2))
    for i, (nm, col, v) in enumerate(rows):
        y = 880 + i * 120
        text(ctx, nm, 100, y, 34, INK, align="left", alpha=d)
        bl = 560 * v / st["med_m"] * pr
        rrect(ctx, 100, y + 28, max(bl, 2.0), 36, 8)
        ctx.set_source_rgba(*hexrgb(col, 0.92 * d))
        ctx.fill()
        if pr >= 0.999:
            w_ = core.text_width(f"{fmt(v)}歩", 40)
            text(ctx, f"{fmt(v)}歩", 100 + bl + 16 + w_ / 2 if 100 + bl + 16 + w_ < 925 else 925 - w_ / 2, y + 46, 40, RED, alpha=d)
    text(ctx, "（歩数の中央値）", 500, 1215, 26, PENCIL, bold=False, alpha=d)
    if t >= T_TW1 + 2.0:
        e = ease_out((t - T_TW1 - 2.0) / 0.3)
        note.sticky(ctx, "通った道を覚えれば、右手と同じになる。\n右手は、同じ道を何度も通らない。\nそれが右手の強み。", 500, 1335, 34, "yellow", a=e, tilt=0.012)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- ひねり2（輪があって、ゴールが真ん中） ----------
MZ2 = 460.0
M2X, M2Y = 250.0, 728.0


def loop_pos(t):
    """輪の迷路で右手が歩く位置（歩数）。1周したあとは輪の中をぐるぐる回る"""
    lp = LOOP
    n = len(lp["pr"]) - 1
    s = max(0.0, t - T_LAP0) * LAP_RATE
    cyc = lp["cyc"]
    if s <= n:
        return s, s
    ln = n - cyc
    return cyc + ((s - cyc) % ln), float(n)           # （歩く位置, 跡に描く歩数）


def draw_loop_maze(ctx, x0, y0, size, s_walk, s_trail, t, show_walker=True, S=1.15, flag=1.0):
    lp = LOOP
    cs = size / W_
    ctx.set_source_surface(maze_surface(lp["op"], size, broken=lp["broken"], key="loop"), x0 - 6, y0 - 6)
    ctx.paint()
    gx, gy = cell_c(x0, y0, cs, MID)
    ctx.arc(gx, gy, cs * 0.55 * flag, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#fbd9d6"))
    ctx.fill()
    draw_trail(ctx, x0, y0, cs, lp["pr"], lp["eid_r"], s_trail, C_R, a0=0.30, wmul=0.38)
    draw_flag(ctx, gx, gy, cs * flag)
    if show_walker:
        path = lp["pr"]
        px, py, k = pos_at(x0, y0, cs, path, s_walk)
        nxt = path[min(k + 1, len(path) - 1)]
        dx = nxt[0] - path[k][0]
        draw_walker(ctx, px, py + cs * 0.30, C_R, C_RD, t, move=True, face=1.0 if dx >= 0 else -1.0, S=S * cs / 30.0)


def draw_tw2(ctx, t):
    a = window(t, T_TW2, T_Q, 0.35, 0.35)
    if a <= 0:
        return
    st = stats()
    ctx.push_group()
    d = ease_out((t - T_TW2 - 0.1) / 0.3)
    note.sticky(ctx, "輪のある迷路で、\nゴールが真ん中だと？", 690, 650, 38, "pink", fg=RED, a=d, tilt=-0.012)
    ctx.push_group()
    sw, stl = loop_pos(t)
    draw_loop_maze(ctx, M2X, M2Y, MZ2, sw, stl, t, flag=1.7)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(d)
    gx, gy = cell_c(M2X, M2Y, MZ2 / W_, MID)
    note.sticky(ctx, "ゴール", 842, gy - 70, 30, "yellow", fg=RED, a=d, tilt=0.03)       # 真ん中のゴールの札
    ctx.move_to(842 - 40, gy - 46)
    ctx.line_to(gx + 26, gy - 4)
    _stroke(ctx, 3.5, RED, 0.9 * d)
    if t >= T_RES:
        e = ease_out((t - T_RES) / 0.3)
        note.sticky(ctx, "右手は外の壁を1周して、元の場所に戻る。", 500, 1262, 34, "yellow", a=e, tilt=-0.012)
    elif t >= T_LAP0 + 0.5:
        e = ease_out((t - T_LAP0 - 0.5) / 0.3)
        text(ctx, "右手をつけて、ひたすら歩く…", 500, 1262, 38, INK, alpha=e)
    if t >= T_RES2:
        e = ease_out((t - T_RES2) / 0.3)
        text(ctx, "右手は 約5回に3回、着かない", 500, 1352, 46, RED, alpha=e)
        text(ctx, "気分で歩く人と、覚えて歩く人は必ず着く", 500, 1396, 30, INK, alpha=e)
        text(ctx, f"計算での見立て（金の線＝壊した壁。1万個中{st['fail']:,}個で着かない）", 500, 1435, 26, INK, bold=False, alpha=e)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 冒頭・上のブロック ----------

def choice_row(labels, size, cx, max_w, gap=40):
    vs = size
    while True:
        ws = [58 + core.text_width(v, vs) for v in labels]
        tot = sum(ws) + gap * (len(labels) - 1)
        if tot <= max_w or vs < 26:
            break
        vs -= 1
    x = cx - tot / 2
    out = []
    for v, w in zip(labels, ws):
        out.append((v, x, vs))
        x += w + gap
    return out


def big3_size(max_w=840.0):
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


Q3_SIZE = 96.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（同じ大きさ）・前提・三択（横1列）。その下に迷路2つ（0秒目から人が動き、迷路が寄ったところから引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(840.0), Q3_SIZE)
        ys = (432, 432 + sz, 432 + sz * 2.0)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q3[-1], sz)
        yl = ys[2] + sz * 0.56
        note.pen_line(ctx, 565 - w3 / 2 - 6, yl, 565 + w3 / 2 + 6, yl - 4, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL_RULE, 565, yl + 36, 30, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = yl + 84
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.96 * a2))
            core.rrect(ctx, cx - 120, cy - 130, 240, 200, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 130, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 80, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy + 4, 50, 48, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy + 4)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) + 1 - n), 0, 0, 78, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
        sz = min(56.0, 100.0 * 850.0 / wmax)
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 464, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 498, 540 + w2 / 2 + 6, 495, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 548
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 860)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7,
                                progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 66 + vw, y - 2, PENCIL, seed=i + 40, width=4,
                              progress=rev, alpha=0.8)

    def draw(self, ctx, t, reveal_t=None):
        m = self.moved(t)
        if m < 1:
            self._intro(ctx, t, 1 - clamp01(m * 2.2))
        if m > 0:
            ctx.save()
            ctx.translate(note.PAGE_DX, 0)
            self._top(ctx, t, m, reveal_t)
            ctx.restore()


INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 締め ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "右手で歩いて\n元の場所に戻ってきたら、\nあなたはどうしますか？", 520, 745, 52, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 540, 940, 36, INK, bold=False, alpha=r)
    ctx.push_group()
    sw, stl = loop_pos(T_LAP0 + (t - T_Q) + 0.2)
    draw_loop_maze(ctx, 310.0, 1000.0, 400.0, sw, stl, t)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_walk_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_stats(ctx, t)
        draw_tw1(ctx, t)
        draw_tw2(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_closing(ctx, t)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 174.6, 220.0, 293.7)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(4):                                      # 冒頭: ことこと
        mx.add(0.1 + 0.5 * i, blip(440 + 60 * i, 0.07), 0.3)
    beat(mx, T_W0, T_A, bpm=110, vol=0.35)                  # 歩く
    mx.add(T_A, bell(1046.5, 0.9), 0.45)                    # 右手が着く
    mx.add(T_A, riser(FF_T * 0.8), 0.35)                    # 早送り
    mx.add(T_B, bell(1318.5, 0.9), 0.4)
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # 1万個
    beat(mx, T_H0, T_D1, bpm=132, vol=0.5, accel=True)
    mx.add(T_D1, thump(), 0.5)
    mx.add(T_DN, bell(784.0, 0.9), 0.45)
    mx.add(T_DN2, bell(880.0, 0.9), 0.45)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_TW1, riser(0.6), 0.35)                         # ひねり1
    mx.add(T_TW1 + 0.3, bell(698.5, 1.0), 0.4)
    mx.add(T_TW1 + 2.0, blip(659.3, 0.14), 0.3)
    mx.add(T_TW2, riser(0.6), 0.35)                         # ひねり2
    mx.add(T_TW2 + 0.3, bell(698.5, 1.0), 0.4)
    beat(mx, T_LAP0, T_RES - 0.1, bpm=140, vol=0.3)
    mx.add(T_RES, bell(392.0, 1.0), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def change_fraction(t0, t1):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    arrs = []
    for t in (t0, t1):
        core._CUR_T = t
        ctx = cairo.Context(surf)
        draw(ctx, t)
        surf.flush()
        arrs.append(np.frombuffer(bytes(surf.get_data()), np.uint8).astype(np.int16))
    core._CUR_T = 0.0
    return float(np.mean(np.abs(arrs[0] - arrs[1]) > 8))


def run_checks():
    m = results()
    st = stats()
    S = samples()
    checks = []
    n = MM.N
    ref = __import__("json").loads((MM.OUT / "model.json").read_text(encoding="utf-8"))   # sims/meiro_model.py の本番の結果
    # (1) 本番の計算（meiro_model.py の main）と同じ結果か
    checks.append(("迷路の数 = 1万", float(len(m["right"])), float(n), 0.0))
    checks.append(("右手の中央値 = 本番の結果", st["med_r"], float(ref["right"]["median"]), 0.0))
    checks.append(("気分の中央値 = 本番の結果", st["med_m"], float(ref["mood"]["median"]), 0.0))
    checks.append(("覚えるの中央値 = 本番の結果", st["med_c"], float(ref["remember"]["median"]), 0.0))
    checks.append(("右手のいちばん長い回 = 本番の結果", float(st["max_r"]), float(ref["right"]["max"]), 0.0))
    checks.append(("気分のいちばん長い回 = 本番の結果", float(st["max_m"]), float(ref["mood"]["max"]), 0.0))
    checks.append(("右手が少ない歩数で着いた割合 = 本番の結果", round(st["wins"], 4), float(ref["right_beats_mood"]), 0.0))
    checks.append(("輪の迷路で右手が着けなかった数 = 本番の結果", float(st["fail"]), float(ref["island"]["fail"]), 0.0))
    checks.append(("輪の迷路: 気分の中央値 = 本番の結果", st["med_m2"], float(ref["island"]["mood"]["median"]), 0.0))
    checks.append(("輪の迷路: 覚えるの中央値 = 本番の結果", st["med_c2"], float(ref["island"]["remember"]["median"]), 0.0))
    checks.append(("輪の迷路: 右手が着いた回の中央値 = 本番の結果", st["med_r2"], float(ref["island"]["right"]["median"]), 0.0))
    # (2) 数字の向き（画面の文）
    checks.append(("右手のいちばん長い回 416 < 気分の中央値 1,217（右手は最悪でも気分の真ん中より短い）", float(st["max_r"] < st["med_m"]), 1.0, 0.0))
    checks.append(("覚えるの中央値 = 右手の中央値（ひねり1の文）", st["med_c"], st["med_r"], 0.0))
    checks.append(("気分が右手と同じか勝つのは 約17回に1回", float(int(round(1 / (1 - st["wins"]))) == 17), 1.0, 0.0))
    checks.append(("輪の迷路で右手が着けない割合は 5割台（約5回に3回の文）", float(0.5 <= st["fail"] / n <= 0.65), 1.0, 0.0))
    checks.append(("輪の迷路で気分と覚えるは必ず着く（歩数が全部ある）", float((m["mood2"] > 0).all() and (m["rem2"] > 0).all()), 1.0, 0.0))
    checks.append(("気分は右手の 約5.5倍", round(st["med_m"] / st["med_r"], 1), 5.5, 0.0))
    # (3) 答え
    ratio = st["med_r"] / st["med_m"]
    key = answer_by_rule(ratio)
    checks.append(("規則の答え = right（右手）", float(key == "right"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 右手・ほぼ同じ・気分 の順", float(LABELS == ["右手", "ほぼ同じ", "気分"]), 1.0, 0.0))
    for v_, k_ in ((0.18, "right"), (0.8, "right"), (1.0, "same"), (1.25, "mood")):
        checks.append((f"規則の道具: r={v_:.2f} → {k_}", float(answer_by_rule(v_) == k_), 1.0, 0.0))
    # (4) 見本は1万個の中の1個そのもの
    i = S["i"]
    ok = (m["right"] >= 200) & (m["right"] <= 250) & (m["mood"] >= 1000) & (m["mood"] <= 1500)
    checks.append(("見本: 条件（右手200〜250・気分1,000〜1,500）に合う最初の迷路", float(i == int(np.nonzero(ok)[0][0])), 1.0, 0.0))
    checks.append(("見本: 画面の右手の歩数 = 1万個の記録", float(N_R), float(m["right"][i]), 0.0))
    checks.append(("見本: 画面の気分の歩数 = 1万個の記録", float(N_M), float(m["mood"][i]), 0.0))
    checks.append(("見本: 1万個の記録の迷路のつながり = 画面の迷路", float(np.array_equal(m["bits"][i], np.array([1 if b in S["tree"][a] else 0 for a, b in EDGES]))), 1.0, 0.0))
    # 別の書き方で数え直す（普通の関数 right_hand / mood をそのまま呼ぶ）
    R = random.Random(MM.SEED)
    for d in MM.stream(i + 1):
        pass
    checks.append(("見本: 本番の関数 right_hand で数え直しても同じ（右手）", float(MM.right_hand(S["tree"], START, GOAL)), float(m["right"][i]), 0.0))
    R2 = random.Random()
    R2.setstate(d["mood_state"])
    checks.append(("見本: 本番の関数 mood で数え直しても同じ（気分）", float(MM.mood(S["tree"], START, GOAL, R2)), float(m["mood"][i]), 0.0))
    for nm, path in (("右手", S["pr"]), ("気分", S["pm"])):
        good = path[0] == START and path[-1] == GOAL and all(path[k + 1] in S["tree"][path[k]] for k in range(len(path) - 1))
        checks.append((f"見本: {nm}の道は、つながった道だけを通って 左上から右下まで", float(good), 1.0, 0.0))
    checks.append(("見本: 右手は 本番の歩き方で ゴールに着く（輪の始まりなし）", float(S["cyc"] is None), 1.0, 0.0))
    lp = LOOP
    checks.append(("輪の迷路: 乱数の順で最初に右手が着けない迷路", float(lp["i"] == int(np.nonzero(m["r2"] < 0)[0][0])), 1.0, 0.0))
    checks.append(("輪の迷路: 右手は同じ場所・同じ向きに戻る（輪の始まりがある）", float(lp["cyc"] is not None), 1.0, 0.0))
    checks.append(("輪の迷路: 本番の関数 right_hand でも着けない", float(MM.right_hand(lp["op"], START, MID) is None), 1.0, 0.0))
    checks.append(("輪の迷路: 壊した壁の数は 約8%（壁の数の8%）", float(len(lp["broken"])), float(int((2 * W_ * H_ - W_ - H_ - (W_ * H_ - 1)) * 0.08)), 0.0))
    checks.append(("輪の迷路: 右手の道はつながった道だけを通る", float(all(lp["pr"][k + 1] in lp["op"][lp["pr"][k]] for k in range(len(lp["pr"]) - 1))), 1.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(840.0), Q3_SIZE)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下（はずみ込み）", float(432 - s3 / 2 * 1.05 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (6) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 見本（気分が着いたあと 次の場面まで）3秒以上", float(T_D0 - T_B >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 中央値の表 3秒以上", float(T_DN2 - T_DN >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: いちばん長い回・何回に1回 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("答えが見える時間 3秒以上", float(T_TW1 - T_REV >= 3.0), 1.0, 0.0))
    checks.append(("ひねり2の結果が見える時間 3秒以上", float(T_Q - T_RES2 >= 3.0), 1.0, 0.0))
    checks.append(("歩く動きは途中で切らない: 右手が着いたあと 気分が着くまで 歩き続ける", float(T_B > T_A and T_D0 - T_B >= 3.0), 1.0, 0.0))
    checks.append(("輪の1周が歩き終わってから結果を出す", float(T_RES >= T_LAP0 + (len(lp['pr']) - 1) / LAP_RATE), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (7) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


def lint():
    n = int(round(DURATION * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    core._LOG = []
    first = probe = None
    for i in range(n):
        core._CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        if i == 0:
            surf.flush()
            first = np.frombuffer(bytes(surf.get_data()), np.uint8)
        elif i == int(0.3 * FPS):
            surf.flush()
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
    log, core._LOG = core._LOG, None
    problems = core.preflight(log, first, probe, DURATION, build_audio())
    if problems:
        print("公開前チェック相当: 要対応")
        for p_ in problems:
            print("  -", p_)
    else:
        print("公開前チェック相当: OK")
    return problems


def report_full():
    print(f"長さ {DURATION:.1f}秒  歩き出し {T_W0:.1f}  右手が着く {T_A:.1f}  気分が着く {T_B:.1f}  1万個 {T_D0:.1f}-{T_D1:.1f}  中央値 {T_DN:.1f}  長い回 {T_DN2:.1f}  答え {T_REV:.1f}  ひねり1 {T_TW1:.1f}  ひねり2 {T_TW2:.1f}（輪 {T_LAP0:.1f}〜{T_RES:.1f}）  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: 迷路 #{S0['i']}  右手 {N_R}歩  気分 {N_M}歩（覚える {S0['rem']}歩）  早送りの加速 {AQ:.2f}")
    print(f"  問い3行の文字 {min(big3_size(840.0), Q3_SIZE):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), Q3_SIZE)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_W0 + 1.0, T_W0 + 2.5, T_A - 0.2, T_A + 0.8, T_A + 1.6, T_B - 0.3, T_B + 1.5, T_D0 - 0.3,
              T_H0 + 1.2, T_D1 - 0.2, T_DN + 1.2, T_DN2 + 1.5, T_REV + 1.0, T_TW1 + 0.6, T_TW1 + 2.6, T_TW2 + 0.6, T_LAP0 + 1.5,
              T_RES + 0.4, T_RES2 + 0.8, T_RES2 + 2.6, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
