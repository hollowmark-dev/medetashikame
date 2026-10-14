"""雪の結晶、同じ形はある？ 1万個をそれぞれの空で育てて、ぜんぶ比べる。— 2026-10-11 作成（公開予定 10/14）

モデル（Reiter 2005「A local cellular model for snow crystal growth」の六角形セル・オートマトン）
  格子   : 六角形のマス（半径 R=96 マスの円の中、約33,400マス）。マスの値 s は「そこにある水の量」。s≥1 が氷。
  1手    : 氷か、氷のとなりのマスを「受け取るマス」とする。受け取るマスは値をそのまま持ち、γ を足す（面の外から来る水蒸気）。
           それ以外のマスの値は、となり6マスとならす（自分 1/2・となり各 1/12。受け取るマスは 0 として数える）。
           円の外は、いつもまわりの水蒸気の量 β（Reiter の「背景の値」）。
  空の道すじ: 結晶は落ちながら、空のようす（β と γ）が何度も変わる。1個ごとに、15〜80手ごとに区切った「区間」の列を
           でたらめに作る（β 0.30〜0.80 の一様、γ 10^-4〜10^-2.3 の対数一様）。区間が変わるとき、受け取らないマスの値を
           β の比で大きく・小さくする（Reiter の図7と同じやり方）。
  小さなゆらぎ: 空気はいつも少しゆらぐ。1手ごとに、受け取らないマスの値を (1 ± 0.03%) 倍する（正規分布）。1個ごとに別の模様。
           β は 0.80 まで（0.85 を越えると先が1手に1マスで伸び、形が格子で決まってしまうため外した）。
  終わり : 結晶の先が中心から 88 マスに届いたら止める（大きさをそろえて比べる）。
  比べ方 : 2つの結晶の氷のマスの重なり（共通 ÷ どちらか）を「似ている度」とする。六角形の12通りの向き（回転6×裏返し2）の
           いちばん似る向きで比べる。「同じ形」＝氷のマスが1つ残らず一致（似ている度 100%）。
  ちがう空: 1万個（道すじも、ゆらぎも1個ごとに別）。1万×9,999÷2＝49,995,000組をぜんぶ比べる。
  同じ空  : 1,000組のふたご（道すじは同じ、ゆらぎだけ別）。

問い: 「雪の結晶、同じ形はある？」 A よくある ／ B たまにある ／ C 1組もない。
      判定のきまり（計算の前に決めた）: 同じ形が0組→C、1〜99組→B、100組以上→A。結果を見て設定を変えて合わせることはしない。
      v1（半径48マス・約8,400マス）では 49,995,000組のうち1組が同じ形だった。その1組は「1手に半マス」の速い伸び方で、
      格子の粗さによるものと考え、マスを細かく（半径96）してやり直した（2026-10-12 ユーザー依頼）。
      結果（半径96）: 同じ形 0組（→C）。いちばん似た2つ 74.8%、全組の平均 41.1%。ふたごは平均 84.9%・真ん中 86.1%、
      マス1つまで同じは0組。1,000組中868組が、ちがう空のいちばん似た2つより似ていた。
見せ方: 冒頭＝紙いっぱいに、育ちながら落ちる雪の結晶。三択の下に「でき方」の小さなメモ（氷のつぶ→水蒸気がくっつく→6方向に枝）。シミュ＝左「ちがう空」2個と右「同じ空」2個が並んで育つ（似ている度が動く）
        → 1万個（左のマス目＝1万個、右＝ふたご1,000組）。答え＝いちばん似た2つでも○%。ひねり＝同じ空のふたご。
        締め＝「なんで6本の腕は、同じ形にそろうの？ → 答えは概要欄に」。

照合（check_answers）:
 (1) 1手の更新が Reiter の式（中心 1/2・となり 1/12、受け取るマスに γ）と一致（小さな格子で、1マスずつ書いた式と比べる）
 (2) 12通りの向きが六角形の対称（12個がすべて別の並べかえ・円の中に閉じる・回して戻る）
 (3) 「似ている度」を行列の掛け算で出した値が、1組ずつ数えた値と一致（ランダムな500組）
 (4) ゆらぎ無し・6回対称な道すじで育てた結晶は、自分を60°回したものと 100% 一致（モデルが六角形の対称を守る）
 (5) 画面の数字（0組・いちばん似た%・ふたごの平均%）が集計と一致
 (6) 答え（同じ形の組の数から選ぶ）
乱数の種は見本（ゆっくり見せる4個）の見栄えのために選んでよい。画面の統計は1万個・1,000組すべてから正直に出す。
"""
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, _t, SR)
from engine.parts import loop_back

note.use()
note.DATE = "10.14"                               # 日付欄（公開予定日）

SLUG = "yuki-kesshou"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
R = 96                                            # 格子の半径（マス）。円の外は β に固定。v1 は 48（約8,400マス）→ 96（約33,400マス）
RSTOP = 88                                        # 結晶の先がここに届いたら止める（半径に比例。v1 は 44）
M = int(math.ceil(R * 2 / math.sqrt(3))) + 2      # 配列の半分の幅（斜めの座標で円が収まる）
N = 2 * M + 1
N_DIFF = 10000                                    # ちがう空
N_TWIN = 1000                                     # 同じ空のふたご（組）
K_MAX = 60                                        # 区間の数の上限（足りなくなったら最後の区間のまま）
SEG = (15, 80)                                    # 1区間の手数
BETA = (0.30, 0.80)                               # 0.85 を越えると、先が「1手に1マス」（格子の速さの上限）で伸びて
                                                  # 形が格子で決まってしまう（試しに 0.90 まで入れたら、そうした結晶どうしが同じ形になった）
LOG_GAMMA = (-4.0, -2.3)
EPS = 3e-4                                        # 空気のゆらぎ: 1手ごとに、受け取らないマスの値を (1 ± 0.03%) 倍（正規分布）
N_BANK = 211                                      # ゆらぎの模様の在庫（1個ごと・1手ごとに別の模様を選ぶ）
T_CAP = 4000                                      # 手数の上限（届かなかったら打ち切り）
SEED_HIST, SEED_NOISE = 2026, 1014

_q, _r = np.meshgrid(np.arange(-M, M + 1), np.arange(-M, M + 1), indexing="ij")
HX = _q + _r / 2.0                                # 斜めの座標 → 平面
HY = _r * math.sqrt(3) / 2
DIST = np.hypot(HX, HY)
INSIDE = DIST <= R
OUTSIDE = ~INSIDE
NEAR_EDGE = DIST >= RSTOP
SHIFTS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]   # 六角形のとなり（斜めの座標）
CELLS = np.argwhere(INSIDE)
LIN = CELLS[:, 0] * N + CELLS[:, 1]
NC = len(LIN)


def nb_sum(a):
    """となり6マスの和（配列の端の外は 0。円の外は毎手 β に戻すので、端は使われない）"""
    out = np.zeros_like(a)
    for dq, dr in SHIFTS:
        sq = slice(max(0, -dq), N - max(0, dq))
        tq = slice(max(0, dq), N - max(0, -dq))
        sr = slice(max(0, -dr), N - max(0, dr))
        tr = slice(max(0, dr), N - max(0, -dr))
        out[..., sq, sr] += a[..., tq, tr]
    return out


def step_once(s, beta, gamma):
    """Reiter の1手。s: (B,N,N)、beta/gamma: (B,1,1)"""
    ice = s >= 1
    rec = ice | (nb_sum(ice.astype(np.float32)) > 0)
    u = np.where(rec, np.float32(0), s)
    v = np.where(rec, s + gamma, np.float32(0))
    s = u + (nb_sum(u) - 6 * u) / np.float32(12) + v
    return np.where(OUTSIDE, beta, s)


def histories(n, seed):
    """1個ずつの空の道すじ: 区間ごとの β・γ と、区間の終わりの手（累積）"""
    rng = np.random.default_rng(seed)
    beta = rng.uniform(*BETA, (n, K_MAX))
    gamma = 10 ** rng.uniform(*LOG_GAMMA, (n, K_MAX))
    dur = rng.integers(SEG[0], SEG[1] + 1, (n, K_MAX))
    ends = np.cumsum(dur, 1)
    return beta, gamma, ends


_BANK = None


def bank():
    global _BANK
    if _BANK is None:
        _BANK = np.random.default_rng(SEED_NOISE).standard_normal((N_BANK, N, N)).astype(np.float32)
    return _BANK


def nb_or(out, a):
    """out |= となり6マスのどれかが a（bool）"""
    for dq, dr in SHIFTS:
        sq = slice(max(0, -dq), N - max(0, dq))
        tq = slice(max(0, dq), N - max(0, -dq))
        sr = slice(max(0, -dr), N - max(0, dr))
        tr = slice(max(0, dr), N - max(0, -dr))
        out[..., sq, sr] |= a[..., tq, tr]
    return out


INSIDE_F = INSIDE.astype(np.float32)
RING_LIN = np.nonzero((NEAR_EDGE & INSIDE).reshape(-1))[0]


def grow(beta, gamma, ends, noise_ids, eps=EPS):
    """まとめて育てる。返り値: 凍った手 tf（-1＝氷でない, int16）、止まった手、届いたか。
    1手の中身は step_once と同じ（速さのため、同じ式を配列を使い回して書いた）。
    ゆらぎ: 受け取らないマスの値を、ならす前に (1 + EPS×模様) 倍する。模様は在庫から
    (番号×7919＋手×104729) mod 211 番を選ぶ（ふたごは番号が別なので模様も別）"""
    B = len(beta)
    S = np.repeat(beta[:, 0].astype(np.float32)[:, None, None], N, 1).repeat(N, 2)
    S[:, M, M] = 1.0
    nid = np.asarray(noise_ids, np.int64)
    BK = bank() if eps > 0 else None
    tf = np.full((B, N, N), -1, np.int16)
    tf[:, M, M] = 0
    t_end = np.full(B, T_CAP, np.int32)
    reached = np.zeros(B, bool)
    act = np.arange(B)
    stage = np.zeros(B, int)
    TF = tf.copy()
    half, twelfth = np.float32(0.5), np.float32(1 / 12)
    for t in range(1, T_CAP + 1):
        ice = S >= 1
        rec = nb_or(ice.copy(), ice)
        ns = np.minimum((ends[act] < t).sum(1), K_MAX - 1)
        sw = ns != stage[act]
        if sw.any():                              # 区間が変わった: まわりの水蒸気を新しい β に合わせる
            ratio = (beta[act, ns] / beta[act, stage[act]]).astype(np.float32)
            ratio = np.where(sw, ratio, np.float32(1))[:, None, None]
            S = np.where(rec, S, S * ratio)
            stage[act] = ns
        b = beta[act, stage[act]].astype(np.float32)[:, None, None]
        g = gamma[act, stage[act]].astype(np.float32)[:, None, None]
        u = np.where(rec, np.float32(0), S)       # 受け取らないマス
        if BK is not None:
            f = BK[(nid[act] * 7919 + t * 104729) % N_BANK]
            f *= np.float32(eps)
            f += np.float32(1)
            u *= f
        nb = nb_sum(u)
        nb *= twelfth
        u *= half
        nb += u                                   # ならした値（自分 1/2 ＋ となり 1/12）
        S += g
        S *= rec                                  # 受け取るマス: 値＋γ（それ以外は 0）
        nb += S
        S = np.where(OUTSIDE, b, nb)
        ice = S >= 1
        new = ice & (TF < 0)
        TF[new] = t
        done = (S.reshape(len(act), -1)[:, RING_LIN] >= 1).any(1)
        if done.any():
            t_end[act[done]] = t
            reached[act[done]] = True
            tf[act[done]] = TF[done]
            keep = ~done
            act, S, TF = act[keep], S[keep], TF[keep]
            if len(act) == 0:
                break
    if len(act):
        tf[act] = TF
    return tf, t_end, reached


def _job(args):
    beta, gamma, ends, nid = args
    return grow(beta, gamma, ends, nid)


def run_all(beta, gamma, ends, nid, chunk=150):
    jobs = [(beta[i:i + chunk], gamma[i:i + chunk], ends[i:i + chunk], nid[i:i + chunk])
            for i in range(0, len(beta), chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(14, (os.cpu_count() or 4) - 2))) as ex:
        parts = list(ex.map(_job, jobs))
    return (np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts]),
            np.concatenate([p[2] for p in parts]))


# ---------- 六角形の12通りの向き ----------
def sym_index(k, refl):
    """向き k（60°×k 回す）と裏返しで、マス i が移る先（CELLS の番号ではなく N×N の通し番号）"""
    a, b = (CELLS[:, 1] - M, CELLS[:, 0] - M) if refl else (CELLS[:, 0] - M, CELLS[:, 1] - M)
    for _ in range(k):
        a, b = -b, a + b                          # 斜めの座標で 60° 回す
    return (a + M) * N + (b + M)


SYM = [sym_index(k, f) for f in (False, True) for k in range(6)]
_POS = np.full(N * N, -1)
_POS[LIN] = np.arange(NC)
SYM_C = [_POS[s] for s in SYM]                    # CELLS の番号で


def masks_of(tf):
    """凍った手の配列 → 円の中のマスの氷（bool, (B, NC)）"""
    return tf.reshape(len(tf), -1)[:, LIN] >= 0


def iou_pair(a, b):
    """1組の似ている度（12通りの向きでいちばん高いもの）と、そのときの向きの番号"""
    best, bk = -1.0, 0
    for k, idx in enumerate(SYM_C):
        bb = b[idx]
        inter = np.count_nonzero(a & bb)
        uni = np.count_nonzero(a | bb)
        v = inter / uni if uni else 1.0
        if v > best:
            best, bk = v, k
    return best, bk


def all_pairs(mk, block=1000):
    """全部の組の似ている度（行列の掛け算で、共通のマス数を数える）。
    返り値: 同じ形の組の数・似ている度のヒストグラム（1%きざみ）・i より前の結晶とのいちばん似た相手と値"""
    n = len(mk)
    X = mk.astype(np.float32)
    cnt = X.sum(1)
    best_prev = np.full(n, -1.0)
    best_prev_j = np.full(n, -1)
    hist = np.zeros(101, np.int64)
    identical = 0
    XT = np.ascontiguousarray(X.T)
    inv = [np.argsort(idx) for idx in SYM_C]       # Σ a[c]·b[g(c)] ＝ Σ a[g⁻¹(d)]·b[d]（A のほうを並べかえる）
    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        best = np.zeros((i1 - i0, n), np.float32)
        for iv in inv:
            inter = np.ascontiguousarray(X[i0:i1][:, iv]) @ XT
            uni = cnt[i0:i1, None] + cnt[None, :] - inter
            np.maximum(best, inter / uni, out=best)
        # 下三角（j < i）だけを数える
        jj = np.arange(n)[None, :]
        ii = np.arange(i0, i1)[:, None]
        low = jj < ii
        vals = best[low]
        identical += int(np.count_nonzero(vals >= 1.0 - 1e-7))
        hist += np.bincount(np.minimum((vals * 100 + 1e-6).astype(int), 100), minlength=101)
        bm = np.where(low, best, -1.0)
        best_prev[i0:i1] = bm.max(1)
        best_prev_j[i0:i1] = bm.argmax(1)
        print(f"    比べた {i1:,}/{n:,}個", flush=True)
    return identical, hist, best_prev, best_prev_j


def compute():
    import time
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    beta, gamma, ends = histories(N_DIFF + N_TWIN, SEED_HIST)
    # ふたご: 道すじ N_DIFF..N_DIFF+N_TWIN-1 を2回ずつ（ゆらぎの番号は別）
    tb = np.concatenate([beta, beta[N_DIFF:]])
    tg = np.concatenate([gamma, gamma[N_DIFF:]])
    te = np.concatenate([ends, ends[N_DIFF:]])
    nid = np.arange(len(tb))
    tf, t_end, reached = run_all(tb, tg, te, nid)
    print(f"  育てた {len(tf):,}個 {time.time() - t0:.0f}秒  届かなかった {int((~reached).sum())}個")
    mk = masks_of(tf)
    print("  全部の組を比べる…")
    ident, hist, bp, bpj = all_pairs(mk[:N_DIFF])
    tw = np.array([iou_pair(mk[N_DIFF + k], mk[N_DIFF + N_TWIN + k])[0] for k in range(N_TWIN)])
    print(f"  計算 {time.time() - t0:.0f}秒")
    np.savez_compressed(OUT / "data.npz", tf=tf, t_end=t_end, reached=reached, beta=tb, gamma=tg, ends=te,
                        identical=ident, hist=hist, best_prev=bp, best_prev_j=bpj, twin=tw)


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = Path(os.environ["YUKI_DATA"]) if os.environ.get("YUKI_DATA") else OUT / "data.npz"   # 絵の下見用に別の結果も読める
        if not f.exists():
            compute()
        z = np.load(f)
        _DATA = {k: z[k] for k in z.files}
        _DATA["mk"] = masks_of(_DATA["tf"])
    return _DATA


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def pct1(x):
    return math.floor(x * 1000 + 0.5) / 10


_SUM = None


def summary():
    global _SUM
    if _SUM is not None:
        return _SUM
    d = data()
    bp = d["best_prev"]
    j = int(np.argmax(bp))
    i = int(d["best_prev_j"][j])
    tw = d["twin"]
    n_pairs = N_DIFF * (N_DIFF - 1) // 2
    hist = d["hist"]
    mean_diff = float((hist * (np.arange(101) + 0.5)).sum() / hist.sum()) / 100
    _SUM = dict(identical=int(d["identical"]), n_pairs=n_pairs, best=float(bp[j]), best_pair=(i, j),
                twin_mean=float(tw.mean()), twin_med=float(np.median(tw)), twin_min=float(tw.min()),
                twin_exact=int((tw >= 1 - 1e-9).sum()), twin_over_best=int((tw > bp[j]).sum()),
                mean_diff=mean_diff, unreached=int((~d["reached"]).sum()),
                t_end_med=float(np.median(d["t_end"])))
    return _SUM


if __name__ == "__main__" and "--compute" in sys.argv:
    compute()
    print(summary())
    raise SystemExit


# ---------- 選ぶもの（見本・冒頭の飾り） ----------
_PICK = None


def pick_samples():
    """見本: ちがう空の2個（似ている度が1万個の組の平均に近い組）と、同じ空のふたご1組（似ている度がふたごの真ん中に近い組）。
    見栄えのための選び方で、1万個の数字には関係しない"""
    global _PICK
    if _PICK is None:
        d = data()
        sm = summary()
        mk = d["mk"]
        rng = np.random.default_rng(5)
        best, pair = 9.0, (0, 1)
        for _ in range(300):
            i, j = rng.choice(N_DIFF, 2, replace=False)
            v = iou_pair(mk[i], mk[j])[0]
            sc = abs(v - sm["mean_diff"])
            if sc < best:
                best, pair = sc, (int(i), int(j))
        tw = d["twin"]
        k = int(np.argmin(np.abs(tw - sm["twin_med"])))
        _PICK = (pair, k)
    return _PICK


def twin_ids(k):
    return N_DIFF + k, N_DIFF + N_TWIN + k


# ---------- 結晶の絵 ----------
CRY_FILL = "#a9d3f0"       # うすい水色（紙の上で、ペンの線画に合う色）
SQ3 = math.sqrt(3)
_PIX = {}


def pixmap(size):
    """size×size の画素 → 格子の通し番号（円の外は -1）。腕が上下を向くように 90° 回して描く"""
    if size not in _PIX:
        c = (size - 1) / 2
        u = (RSTOP + 1.5) / (size / 2)
        yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
        lx, ly = -(yy - c) * u, (xx - c) * u
        rr = ly / (SQ3 / 2)
        qq = lx - rr / 2
        x, z = qq, rr
        y = -x - z
        rx, ry, rz = np.round(x), np.round(y), np.round(z)
        dx, dy, dz = np.abs(rx - x), np.abs(ry - y), np.abs(rz - z)
        c1 = (dx > dy) & (dx > dz)
        c2 = ~c1 & (dy > dz)
        rx = np.where(c1, -ry - rz, rx)
        rz = np.where(~c1 & ~c2, -rx - ry, rz)
        qi, ri = rx.astype(int) + M, rz.astype(int) + M
        ok = (qi >= 0) & (qi < N) & (ri >= 0) & (ri < N)
        idx = np.where(ok, qi * N + ri, 0)
        ok &= INSIDE.reshape(-1)[idx]
        _PIX[size] = np.where(ok, idx, -1)
    return _PIX[size]


def field_img(field_nn, size):
    """N×N の値（凍った手など）を size×size の画素に写す（円の外は -1）"""
    pm = pixmap(size)
    f = np.asarray(field_nn).reshape(-1)
    return np.where(pm >= 0, f[np.maximum(pm, 0)], -1)


def _bgra(col, a=1.0):
    c = hexrgb(col) if isinstance(col, str) else col
    aa = (c[3] if len(c) > 3 else 1.0) * a
    return np.array([c[2] * 255 * aa, c[1] * 255 * aa, c[0] * 255 * aa, 255 * aa], np.float32)


def ss_for(size):
    """細かい格子（1マスが1画素より小さい）を、何倍の大きさで描いてから縮めるか（ぎざぎざ・ちらつきを防ぐ）"""
    return int(min(3, max(1, math.ceil(1.6 * 2 * (RSTOP + 1.5) / size))))


def _dilate(m):
    o = m.copy()
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    return o


def mask_surface(mask, fill_col=CRY_FILL, ink_a=0.9, colors=None, red=None, line=1, ss=1):
    """氷の画素 → cairo の画像。中は水色、ふちはペンの紺。colors（画素ごとの色の番号, 色）で塗り分け、red で赤く。
    ss>1 なら、mask は ss 倍の大きさで、最後に平均して縮める"""
    h, w = mask.shape
    er = mask.copy()
    for _ in range(line):
        e2 = er.copy()
        e2[1:, :] &= er[:-1, :]
        e2[:-1, :] &= er[1:, :]
        e2[:, 1:] &= er[:, :-1]
        e2[:, :-1] &= er[:, 1:]
        er = e2
    edge = mask & ~er
    buf = np.zeros((h, w, 4), np.float32)
    if colors is None:
        buf[mask] = _bgra(fill_col)
    else:
        ids, pal = colors
        for k, col in enumerate(pal):
            sel = mask & (ids == k)
            if sel.any():
                buf[sel] = _bgra(col)
    buf[edge] = _bgra(INK, ink_a)
    if red is not None:
        buf[_dilate(red)] = _bgra("#e2595f")
    if ss > 1:
        buf = buf.reshape(h // ss, ss, w // ss, ss, 4).mean((1, 3))
        h, w = h // ss, w // ss
    arr = np.ascontiguousarray(np.clip(buf + 0.5, 0, 255).astype(np.uint8))
    surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, w, h, w * 4)
    return surf, arr


_TFIMG = {}
_SURF = {}


def tf_img(i, size):
    key = (i, size)
    if key not in _TFIMG:
        if len(_TFIMG) > 600:
            _TFIMG.clear()
        _TFIMG[key] = field_img(data()["tf"][i], size)
    return _TFIMG[key]


def crystal_surface(i, size, tt, style="plain"):
    """結晶 i を、手 tt まで育ったところで描いた画像"""
    tt = int(tt)
    key = (i, size, tt, style)
    hit = _SURF.get(key)
    if hit is None:
        if len(_SURF) > 2500:
            _SURF.clear()
        ss = ss_for(size)
        img = tf_img(i, size * ss)
        mask = (img >= 0) & (img <= tt)
        line = ss                                 # ふちは1画素（細かい枝がふちだらけで黒っぽくならないよう）
        ink = 0.5 if size < 260 else 0.7
        if style == "stage":
            d = data()
            st = np.searchsorted(d["ends"][i], np.maximum(img, 0), side="left")
            ids = band_index(d["beta"][i][np.minimum(st, K_MAX - 1)])
            hit = mask_surface(mask, colors=(ids, RING_PAL), line=line, ss=ss, ink_a=ink)
        else:
            hit = mask_surface(mask, line=line, ss=ss, ink_a=ink)
        _SURF[key] = hit
    return hit


def paint_surface(ctx, surf, cx, cy, size, a=1.0, rot=0.0):
    if a <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    if rot:
        ctx.rotate(rot)
    ctx.set_source_surface(surf, -size / 2, -size / 2)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_crystal(ctx, i, cx, cy, size, p=1.0, a=1.0, rot=0.0, style="plain"):
    """p: 育ち具合（0〜1、止まった手に対する割合）"""
    te = int(data()["t_end"][i])
    surf, _ = crystal_surface(i, size, round(p * te), style)
    paint_surface(ctx, surf, cx, cy, size, a=a, rot=rot)


# ---------- 空の道すじ（区間の帯） ----------
BAND_PAL = ["#e6def6", "#dbe6fa", "#d4eef2", "#d9f0dc", "#f3ecd0"]     # β の低い→高い（水蒸気の少ない→多い）
RING_PAL = ["#b9a6e6", "#9fc0f0", "#8fd3df", "#9fd8a8", "#e8d48a"]     # 結晶の中の、同じ区間で育った部分


def band_index(beta):
    b = np.asarray(beta)
    return np.clip(((b - BETA[0]) / (BETA[1] - BETA[0]) * len(BAND_PAL)).astype(int), 0, len(BAND_PAL) - 1)


def ink_line(ctx, x0, y0, x1, y1, color=INK, seed=1, width=3.5, alpha=1.0):
    """ペンの線（揺れを小さく）"""
    if alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    b = rng.uniform(-1.6, 1.6)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(color, 0.92 * alpha))
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ctx.move_to(x0, y0)
    ctx.curve_to(x0 + (x1 - x0) / 3 + nx * b, y0 + (y1 - y0) / 3 + ny * b,
                 x0 + 2 * (x1 - x0) / 3 - nx * b * 0.6, y0 + 2 * (y1 - y0) / 3 - ny * b * 0.6, x1, y1)
    ctx.stroke()


def draw_strip(ctx, i, x0, x1, y0, y1, a=1.0, ring=False, horiz=False):
    """結晶 i が通った空の帯（上が育ちはじめ、下が止まったところ。horiz なら左→右）。帯の色＝その区間の β"""
    if a <= 0:
        return
    if horiz:                                     # 横向き: 回して、縦の帯として描く（上→下 が 左→右 になる）
        ctx.save()
        ctx.translate(x0, y1)
        ctx.rotate(-math.pi / 2)
        draw_strip(ctx, i, 0, y1 - y0, 0, x1 - x0, a=a, ring=ring)
        ctx.restore()
        return
    d = data()
    te = float(d["t_end"][i])
    ends, beta = d["ends"][i], d["beta"][i]
    pal = RING_PAL if ring else BAND_PAL
    t0 = 0.0
    for k in range(K_MAX):
        t1 = min(float(ends[k]), te)
        ya, yb = y0 + (y1 - y0) * t0 / te, y0 + (y1 - y0) * t1 / te
        ctx.set_source_rgba(*hexrgb(pal[int(band_index(beta[k]))], (0.8 if ring else 1.0) * a))
        ctx.rectangle(x0, ya, x1 - x0, yb - ya + 0.5)
        ctx.fill()
        if t1 >= te:
            break
        t0 = t1
    for (xa, ya, xb, yb, sd) in ((x0, y0, x1, y0, 91), (x1, y0, x1, y1, 92), (x1, y1, x0, y1, 93), (x0, y1, x0, y0, 94)):
        ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3, alpha=0.75 * a)


# ---------- 時間割（表示の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）。toast-butter と同じ
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_A0 = T_GO + 0.1                                 # 見本: ちがう空の2個・同じ空の2個が落ちながら育つ
A_DUR = 4.6
T_A1 = T_A0 + A_DUR
T_B0 = T_A1 + 1.4                                 # 1万個
B_DUR = 5.2
T_B1 = T_B0 + B_DUR
T_FL = T_B1 + 0.2                                 # 数字が出そろう
T_REV = T_FL + 0.6                                # 三択の答え
T_ST2 = T_REV + 0.3                               # 付箋「同じ形は0組」
T_C0 = T_ST2 + 2.4                                # いちばん似た2つ
C_DUR = 3.6
T_TW = T_C0 + C_DUR                               # ひねり: 同じ空のふたご
TW_BANNER = 2.0
T_TW_RUN = T_TW + TW_BANNER
T_TW_VAL = T_TW_RUN + 1.4
T_TW_ST = T_TW_RUN + 2.3                          # 付箋「ふたごみたいに そっくり」（見出しを読み終えてから入れかえる）
T_WHY = T_TW_RUN + 5.1                            # 形は通ってきた空の記録
T_Q = T_WHY + 3.3                                 # 締め
DURATION = T_Q + 4.3

BIG_Q = "雪の結晶、同じ形はある？"
DETAIL = "1万個を、それぞれの空で育てて比べる"
LABELS = ["よくある", "たまにある", "1組もない"]


def correct_index():
    """答えは同じ形の組の数から: 0組なら C、結晶の1%以上が同じ形の相手を持つほどなら A、そのあいだは B"""
    s = summary()
    if s["identical"] == 0:
        return 2
    return 0 if s["identical"] >= N_DIFF * 0.01 else 1


# ---------- 冒頭: 紙いっぱいに、育ちながら落ちる結晶 ----------
D_TOP, D_BOT = 600.0, 1560.0                      # 落ちる範囲（上は三択の下、下は画面の外まで）
CD_X, CD_Y = 868.0, 800.0                         # 予想して！のカウント
_DECO = None


def deco_list():
    """冒頭で落ちる結晶: [番号, x, 大きさ, 落ちる速さ px/s, 出る時刻, 回る速さ]。1万個の中から（と、ふたご1組）"""
    global _DECO
    if _DECO is None:
        rng = np.random.default_rng(14)
        pool = list(rng.choice(N_DIFF, 80, replace=False))
        lanes = [118, 262, 410, 560, 712, 860, 985]
        out = []
        k = 0
        for x in lanes:
            v = rng.uniform(95, 135)
            sp = rng.uniform(300, 360)
            t0 = -(D_BOT - D_TOP + 160) / v + rng.uniform(0, sp) / v
            while t0 < T_GO + 0.5:
                size = int(rng.uniform(150, 235)) // 2 * 2
                out.append([int(pool[k % len(pool)]), x + rng.uniform(-14, 14), size, v, t0, rng.uniform(-0.25, 0.25)])
                t0 += sp / v
                k += 1
        _DECO = out
    return _DECO


def draw_deco(ctx, t, a):
    if a <= 0:
        return
    ctx.push_group()
    for (i, x, size, v, t0, w) in deco_list():
        y = D_TOP - 80 + v * (t - t0)
        if y < D_TOP - 140 or y > D_BOT + 140:
            continue
        p = 0.12 + 0.88 * clamp01((y - (D_TOP - 80)) / (1330 - (D_TOP - 80)))
        draw_crystal(ctx, i, x, y, size, p=p, rot=w * (t - t0))
    ctx.pop_group_to_source()
    g = cairo.LinearGradient(0, D_TOP - 40, 0, D_TOP + 50)      # 上のふち（三択の下）でうすく消す
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, a)
    ctx.mask(g)


# ---------- 冒頭の小さな説明: 雪の結晶のでき方（三択とカウントのあいだ、左上のメモ） ----------
HOW_T = (2.2, 2.6, 3.0)                           # 3つの段が出る時刻
HOW_CAP_T = 3.6                                   # 「通る空の温度・湿り気で、枝の形が変わる」
HOW_X0, HOW_X1, HOW_Y0, HOW_Y1 = 118.0, 712.0, 628.0, 878.0
HOW_CX = (212.0, 415.0, 618.0)
HOW_IY = 712.0


def hexagon(ctx, cx, cy, r, a, fill_col=CRY_FILL):
    ctx.move_to(cx, cy - r)
    for k in range(1, 6):
        ang = -math.pi / 2 + k * math.pi / 3
        ctx.line_to(cx + r * math.cos(ang), cy + r * math.sin(ang))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(fill_col, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(2.5)
    ctx.stroke()


def pen_arrow(ctx, x0, x1, y, a):
    note.pen_line(ctx, x0, y, x1, y, INK, seed=63, width=4, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x1 - 13, y - 10)
    ctx.line_to(x1 + 1, y)
    ctx.line_to(x1 - 13, y + 10)
    ctx.stroke()


def draw_howto(ctx, t, a):
    """氷のつぶ → 水蒸気がくっつく → 6方向に枝がのびる、と、枝の形は通る空で変わる、の1行"""
    if a <= 0 or t < HOW_T[0]:
        return
    a0 = ease_out((t - HOW_T[0]) / 0.3) * a
    fill(ctx, (*hexrgb(PAPER)[:3], 0.9 * a0))
    core.rrect(ctx, HOW_X0, HOW_Y0, HOW_X1 - HOW_X0, HOW_Y1 - HOW_Y0, 16)
    ctx.fill()
    for (xa, ya, xb, yb, sd) in ((HOW_X0, HOW_Y0, HOW_X1, HOW_Y0, 101), (HOW_X1, HOW_Y0, HOW_X1, HOW_Y1, 102),
                                 (HOW_X1, HOW_Y1, HOW_X0, HOW_Y1, 103), (HOW_X0, HOW_Y1, HOW_X0, HOW_Y0, 104)):
        ink_line(ctx, xa, ya, xb, yb, PENCIL, seed=sd, width=2.5, alpha=0.7 * a0)
    text(ctx, "雪の結晶のでき方", HOW_X0 + 22, HOW_Y0 + 30, 26, PENCIL, align="left", bold=False, alpha=a0)
    labels = ("氷のつぶ", "水蒸気が\nくっつく", "6方向に\n枝がのびる")
    for k, (cx, lab, t0) in enumerate(zip(HOW_CX, labels, HOW_T)):
        if t < t0:
            continue
        b = ease_out((t - t0) / 0.25) * a
        if k == 0:
            hexagon(ctx, cx, HOW_IY, 10, b)
        elif k == 1:
            hexagon(ctx, cx, HOW_IY, 17, b)
            for q in range(9):                    # まわりの水蒸気（点）が寄ってくる
                ph = ((t - t0) / 1.2 + q / 9) % 1.0
                ang = q * 2.4 + 0.3
                rr = 50 - 30 * ph
                ctx.set_source_rgba(*hexrgb("#6fa8dc", b * min(1, 3 * (1 - ph))))
                ctx.arc(cx + rr * math.cos(ang), HOW_IY + rr * 0.8 * math.sin(ang), 3.2, 0, 2 * math.pi)
                ctx.fill()
        else:
            g = 0.05 + 0.95 * ease(clamp01((t - t0) / 2.0))
            draw_crystal(ctx, HOW_SAMPLE, cx, HOW_IY, 96, p=g, a=b)
        if k:
            pen_arrow(ctx, HOW_CX[k - 1] + 62, cx - 58, HOW_IY, b)
        text(ctx, lab, cx, 790 if "\n" in lab else 775, 28, INK, alpha=b)
    if t >= HOW_CAP_T:
        c = ease_out((t - HOW_CAP_T) / 0.3) * a
        text(ctx, "通る空の温度・湿り気で、枝の形が変わる", (HOW_X0 + HOW_X1) / 2, 850, 28, RED, alpha=c)


HOW_SAMPLE = 3                                    # 3段目で育てて見せる結晶（1万個のうちの1個。見た目で選んだ）


class YIntro(note.Intro):
    """この回だけの冒頭。上: 問いの1行・前提・三択（横1列）。その下の紙いっぱいに、育ちながら落ちる雪の結晶。
    予想して！とカウントは右の空き"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_deco(ctx, t, a)
        draw_howto(ctx, t, a)
        sz = 66
        w = core.text_width(BIG_Q, sz)
        if w > 800:
            sz *= 800 / w
            w = 800
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        ctx.save()
        ctx.translate(575, 418)
        ctx.scale(pop, pop)
        text(ctx, BIG_Q, 0, 0, sz, INK, alpha=a)
        ctx.restore()
        note.pen_line(ctx, 575 - w / 2 - 6, 464, 575 + w / 2 + 6, 458, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 502, 36, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            cx = 570 + (i - 1) * 290
            vs = 42
            vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2 + 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 566, 28, 28, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 566, 38, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 64, 566, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.9 * a2))
            core.rrect(ctx, cx - 125, cy - 172, 250, 66, 16)
            ctx.fill()
            note.hand_text(ctx, "予想して！", cx, cy - 140, 46, RED, seed=41, alpha=a2, align="center")
            fill(ctx, (*hexrgb(PAPER)[:3], 0.92 * a))
            ctx.arc(cx, cy, 70, 0, 2 * math.pi)
            ctx.fill()
            note.pen_circle(ctx, cx, cy, 66, 64, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 96, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        sz = 56
        w = core.text_width(BIG_Q, sz)
        if w > 850:
            sz *= 850 / w
            w = 850
        text(ctx, BIG_Q, 540, 425, sz, INK, alpha=m)
        note.pen_line(ctx, 540 - w / 2 - 6, 464, 540 + w / 2 + 6, 460, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        for i, v in enumerate(self.labels):
            cx, y = 540 + (i - 1) * 290, 522
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vs = 44
            vw = core.text_width(v, vs)
            if 64 + vw > 252:
                vs *= (252 - 64) / vw
                vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=al)
            text(ctx, v, x0 + 64, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, cx, y, (64 + vw) / 2 + 30, 42, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 72 + vw, y - 2, PENCIL, seed=i + 40, width=4,
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


_INTRO = None


def intro():
    global _INTRO
    if _INTRO is None:
        _INTRO = YIntro([BIG_Q, ""], LABELS, correct=correct_index(), msg="", rule=None)
    return _INTRO


# ---------- シミュの舞台（本体の座標。draw 側で translate(PAGE_DX)） ----------
LCX, RCX = 285.0, 735.0                           # 左「ちがう空」・右「同じ空」の中心
HEAD_Y = 618.0
S_Y0, S_Y1 = 705.0, 1235.0                        # 見本の空の帯
S_W = 150.0
S_SIZE = 176                                      # 見本の結晶の大きさ（px）
READ_Y = 1300.0


def panel_alpha(t):
    if t < T_MOVE:
        return 0.0
    return ease((t - T_MOVE) / 0.4) * (1 - ease((t - T_C0 + 0.4) / 0.4))


def a_alpha(t):
    if t < T_MOVE:
        return 0.0
    return ease((t - T_MOVE) / 0.4) * (1 - ease((t - T_A1 - 0.5) / 0.45))


def b_alpha(t):
    if t < T_A1 + 0.9:
        return 0.0
    return ease((t - T_A1 - 0.9) / 0.4) * (1 - ease((t - T_C0 + 0.4) / 0.4))


def a_prog(t):
    return ease(clamp01((t - T_A0) / A_DUR))


def partial_mask(i, p):
    d = data()
    tt = p * float(d["t_end"][i])
    v = d["tf"][i].reshape(-1)[LIN]
    return (v >= 0) & (v <= tt)


_SIMCACHE = {}


def live_sim(i, j, p):
    """育ちかけの2つの似ている度（同じ育ち具合で比べる）"""
    key = (i, j, round(p, 3))
    if key not in _SIMCACHE:
        _SIMCACHE[key] = iou_pair(partial_mask(i, p), partial_mask(j, p))[0]
    return _SIMCACHE[key]


def draw_heads(ctx, t, a):
    if a <= 0:
        return
    text(ctx, "ちがう空", LCX, HEAD_Y, 46, INK, alpha=a)
    text(ctx, "同じ空", RCX, HEAD_Y, 46, INK, alpha=a)
    sa = a * (1 - ease((t - T_A1 - 0.4) / 0.4))
    sb = a * ease((t - T_A1 - 0.9) / 0.4) if t >= T_A1 + 0.9 else 0.0
    if sa > 0:
        text(ctx, "1個ずつ別の道すじ", LCX, HEAD_Y + 48, 30, PENCIL, bold=False, alpha=sa)
        text(ctx, "2個が同じ道すじ", RCX, HEAD_Y + 48, 30, PENCIL, bold=False, alpha=sa)
    if sb > 0:
        text(ctx, "1万個（1マス＝1個）", LCX, HEAD_Y + 48, 30, PENCIL, bold=False, alpha=sb)
        text(ctx, "ふたご1,000組", RCX, HEAD_Y + 48, 30, PENCIL, bold=False, alpha=sb)
    ink_line(ctx, 510, HEAD_Y - 20, 512, 1340, PENCIL, seed=61, width=2.5, alpha=0.5 * a)


def draw_samples(ctx, t, a):
    """見本: 左は別々の空を通る2個、右は同じ空を通る2個（ふたご）。帯を上から下へ落ちながら育つ"""
    if a <= 0:
        return
    (i1, i2), k = pick_samples()
    j1, j2 = twin_ids(k)
    p = a_prog(t)
    for cx, ids in ((LCX, (i1, i2)), (RCX, (j1, j2))):
        for s, i in zip((-1, 1), ids):
            x = cx + s * (S_W / 2 + 6)
            draw_strip(ctx, i, x - S_W / 2, x + S_W / 2, S_Y0, S_Y1, a=a * 0.95)
        for s, i in zip((-1, 1), ids):
            x = cx + s * (S_W / 2 + 6)
            y = S_Y0 + 80 + (S_Y1 - S_Y0 - 160) * p
            draw_crystal(ctx, i, x, y, S_SIZE, p=max(0.04, p), a=a)
    if p >= 0.3:                                  # 育ちはじめは、どれも同じ小さな六角形なので、ある程度育ってから出す
        b = a * ease_out((p - 0.3) / 0.12)
        for cx, ids in ((LCX, (i1, i2)), (RCX, (j1, j2))):
            v = live_sim(ids[0], ids[1], max(0.04, p))
            text(ctx, f"似ている度 {pct(v)}%", cx, READ_Y, 38, RED if (cx == RCX and p > 0.95) else INK, alpha=b)


GRID_N = 100
G_CELL = 4.0
GX0, GY0 = LCX - 200, 712.0                       # 左: 100×100（1マス＝1個）
TW_COLS, TW_ROWS = 40, 25
TW_CELL = 10.0
TX0, TY0 = RCX - 200, 712.0                       # 右: 40×25（1マス＝ふたご1組）


def sim_color(v):
    """似ている度 → 色（低い＝紙に近い水色、高い＝濃い青、100%＝赤）"""
    v = np.asarray(v, np.float64)
    u = np.clip((v - 0.30) / 0.70, 0, 1)[..., None] ** 1.3
    lo = np.array(hexrgb("#e9f3fb")[:3])
    hi = np.array(hexrgb("#2a64a8")[:3])
    rgb = lo + (hi - lo) * u
    return np.where((v >= 1 - 1e-9)[..., None], np.array(hexrgb("#e2595f")[:3]), rgb)


def b_frac(t):
    return clamp01((t - T_B0) / B_DUR) ** 1.15


def count_k(t):
    return int(round(N_DIFF * b_frac(t)))


_GIMG = {}


def grid_surface(kind, k):
    """左: k 個目までの「それより前の結晶といちばん似ている度」で塗る。右: k 組目までのふたごの似ている度"""
    key = (kind, k)
    if key in _GIMG:
        return _GIMG[key]
    if len(_GIMG) > 40:
        _GIMG.clear()
    d = data()
    if kind == "diff":
        n, cols = GRID_N * GRID_N, GRID_N
        v = np.maximum(d["best_prev"][:k], 0.0)
    else:
        n, cols = TW_COLS * TW_ROWS, TW_COLS
        v = d["twin"][:k]
    rgba = np.zeros((n, 4), np.uint8)
    if k:
        rgb = sim_color(v)
        rgba[:k, 0] = (rgb[:, 2] * 255).astype(np.uint8)
        rgba[:k, 1] = (rgb[:, 1] * 255).astype(np.uint8)
        rgba[:k, 2] = (rgb[:, 0] * 255).astype(np.uint8)
        rgba[:k, 3] = 255
    arr = np.ascontiguousarray(rgba.reshape(-1, cols, 4))
    surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, cols, arr.shape[0], cols * 4)
    _GIMG[key] = (surf, arr)
    return _GIMG[key]


def draw_grid_box(ctx, x0, y0, w, h, a, seed=71):
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.3 * a))
    ctx.set_line_width(1.2)
    for qq in range(1, 10):
        ctx.move_to(x0 + w * qq / 10, y0)
        ctx.line_to(x0 + w * qq / 10, y0 + h)
    for qq in range(1, int(round(h / 40))):
        ctx.move_to(x0, y0 + 40 * qq)
        ctx.line_to(x0 + w, y0 + 40 * qq)
    ctx.stroke()
    for (xa, ya, xb, yb, sd) in ((x0, y0, x0 + w, y0, seed), (x0 + w, y0, x0 + w, y0 + h, seed + 1),
                                 (x0 + w, y0 + h, x0, y0 + h, seed + 2), (x0, y0 + h, x0, y0, seed + 3)):
        ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3.5, alpha=0.85 * a)


def draw_10k(ctx, t, a):
    if a <= 0:
        return
    sm = summary()
    d = data()
    k = count_k(t)
    m = int(round(N_TWIN * b_frac(t)))
    for kind, n_now, x0, y0, cols, rows, cell in (("diff", k, GX0, GY0, GRID_N, GRID_N, G_CELL),
                                                  ("twin", m, TX0, TY0, TW_COLS, TW_ROWS, TW_CELL)):
        if n_now > 0:
            surf, _ = grid_surface(kind, n_now)
            ctx.save()
            ctx.translate(x0, y0)
            ctx.scale(cell, cell)
            ctx.set_source_surface(surf, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_NEAREST)
            ctx.paint_with_alpha(a)
            ctx.restore()
        draw_grid_box(ctx, x0, y0, cols * cell, rows * cell, a, seed=71 if kind == "diff" else 81)
    # 同じ形の相手が見つかった結晶のマスを、赤ペンで囲む
    for h_i in np.nonzero(d["best_prev"][:k] >= 1 - 1e-9)[0]:
        cx, cy = GX0 + (h_i % GRID_N + 0.5) * G_CELL, GY0 + (h_i // GRID_N + 0.5) * G_CELL
        age = (b_frac(t) - h_i / N_DIFF) * B_DUR
        note.pen_circle(ctx, cx, cy, 24, 22, RED, seed=88, width=5, progress=clamp01(age / 0.3), alpha=a)
    # 右の下: いま比べているふたご1組
    kk = min(max(m - 1, 0), N_TWIN - 1)
    p1, p2 = twin_ids(kk)
    for s, i in zip((-1, 1), (p1, p2)):
        draw_crystal(ctx, i, RCX + s * 80, 1062, 150, p=1.0, a=a)
    # 数字（左）
    pairs = k * (k - 1) // 2
    ident = int(np.count_nonzero(d["best_prev"][:k] >= 1 - 1e-9))
    best = float(d["best_prev"][1:k].max()) if k > 1 else 0.0
    text(ctx, f"同じ形 {ident}組", LCX, 1170, 52, RED if t >= T_FL else INK, alpha=a)
    text(ctx, f"{pairs:,}組を比べた", LCX, 1228, 30, PENCIL, bold=False, alpha=a)
    if k > 1:
        text(ctx, f"いちばん似た2つ {pct1(best):.1f}%", LCX, READ_Y, 34, INK, alpha=a)
    if m > 0:
        tm = float(d["twin"][:m].mean())
        text(ctx, f"似ている度 平均 {pct(tm)}%", RCX - 12, READ_Y, 32, INK, alpha=a)
    draw_scale(ctx, 540, 1372, a)


def draw_scale(ctx, cx, y, a):
    if a <= 0:
        return
    w, h = 300, 26
    x0 = cx - w / 2 + 20
    for q in range(60):
        v = 0.30 + 0.70 * (q + 0.5) / 60 * 0.999
        ctx.set_source_rgba(*sim_color(v), a)
        ctx.rectangle(x0 + w * q / 60, y - h / 2, w / 60 + 0.6, h)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
    ctx.set_line_width(2)
    ctx.rectangle(x0, y - h / 2, w, h)
    ctx.stroke()
    text(ctx, "似ている度", x0 - 18, y, 28, INK, align="right", bold=False, alpha=a)
    text(ctx, "低い", x0 + 4, y + 36, 26, PENCIL, align="left", bold=False, alpha=a)
    text(ctx, "高い", x0 + w - 4, y + 36, 26, PENCIL, align="right", bold=False, alpha=a)
    ctx.set_source_rgba(*sim_color(1.0), a)                      # 赤＝100%（マス1つまで同じ形）
    ctx.rectangle(x0 + w + 22, y - h / 2, h, h)
    ctx.fill()
    text(ctx, "同じ形", x0 + w + 56, y, 28, RED, align="left", bold=False, alpha=a)


# ---------- 2つを大きく並べる（いちばん似た2つ・ふたご） ----------
BIG = 330
PAIR_Y = 880.0
PAIR_X = (290.0, 760.0)


def aligned(i, j):
    """j を i にいちばん似る向きにそろえた N×N の凍った手と、形がちがうマス（N×N bool）"""
    d = data()
    a, b = d["mk"][i], d["mk"][j]
    v, k = iou_pair(a, b)
    tfj = d["tf"][j].reshape(-1)[LIN][SYM_C[k]]
    arr = np.full(N * N, -1, np.int16)
    arr[LIN] = tfj
    diff = np.zeros(N * N, bool)
    diff[LIN] = a ^ b[SYM_C[k]]
    return arr.reshape(N, N), diff.reshape(N, N), v


_PAIRSURF = {}


def pair_surfaces(i, j, size=BIG):
    key = (i, j, size)
    if key not in _PAIRSURF:
        d = data()
        ss = ss_for(size)
        tfa = field_img(d["tf"][i], size * ss)
        arr, diff, v = aligned(i, j)
        tfb = field_img(arr, size * ss)
        dimg = field_img(diff.astype(np.int16), size * ss) > 0
        ln, ia = ss, 0.7
        _PAIRSURF[key] = (mask_surface(tfa >= 0, line=ln, ss=ss, ink_a=ia), mask_surface(tfb >= 0, line=ln, ss=ss, ink_a=ia),
                          mask_surface(tfa >= 0, line=ln, red=dimg, ss=ss, ink_a=ia),
                          mask_surface(tfb >= 0, line=ln, red=dimg, ss=ss, ink_a=ia), v, int(diff.sum()))
    return _PAIRSURF[key]


def draw_pair(ctx, t, i, j, t0, a, title, col, title_out=None):
    """左右に大きく並べて、少したってから、形がちがうマスを赤くする"""
    if a <= 0:
        return
    sa, sb, sar, sbr, v, nd = pair_surfaces(i, j)
    red = ease_out((t - t0 - 1.0) / 0.4)
    for x, s_plain, s_red in ((PAIR_X[0], sa, sar), (PAIR_X[1], sb, sbr)):
        paint_surface(ctx, s_plain[0], x, PAIR_Y, BIG, a=a * (1 - red))
        paint_surface(ctx, s_red[0], x, PAIR_Y, BIG, a=a * red)
    ta = a if title_out is None else a * (1 - ease((t - title_out) / 0.25))
    text(ctx, title, 525, 640, 44, INK, alpha=ta)
    text(ctx, f"似ている度 {pct1(v):.1f}%", 525, 1120, 54, col, alpha=a)
    if red > 0:
        text(ctx, f"赤＝形がちがうマス（{nd:,}マス）", 470, 1185, 32, RED, bold=False, alpha=a * red)


def draw_same(ctx, t, i, j, a):
    """同じ形だった1組: 2つの結晶と、それぞれが通ってきた空の帯（左→右）"""
    if a <= 0:
        return
    sa, sb, _sar, _sbr, v, _nd = pair_surfaces(i, j, 300)
    text(ctx, "同じ形だった、ただ1組", 525, 640, 46, INK, alpha=a)
    for x, sf in ((PAIR_X[0], sa), (PAIR_X[1], sb)):
        paint_surface(ctx, sf[0], x, 835, 300, a=a)
    text(ctx, f"似ている度 {pct1(v):.0f}%", 525, 1010, 50, RED, alpha=a)
    g = ease_out((t - T_C0 - 0.6) / 0.4)
    if g > 0:
        for x, idx in ((PAIR_X[0], i), (PAIR_X[1], j)):
            draw_strip(ctx, idx, x - 150, x + 150, 1085, 1135, a=a * g, horiz=True)
        text(ctx, "通ってきた空（育ちはじめ → おわり）", 525, 1170, 28, INK, bold=False, alpha=a * g)
    if t >= T_C0 + 1.2:
        c = ease_out((t - T_C0 - 1.2) / 0.3) * a
        note.sticky(ctx, "通ってきた空も、ほぼ同じ", 470, 1278, 42, "mint", a=c, tilt=-0.015)


# ---------- 本体 ----------
def body(ctx, t):
    sm = summary()
    pa = panel_alpha(t)
    draw_heads(ctx, t, pa)
    draw_samples(ctx, t, a_alpha(t))
    if T_A1 + 0.1 <= t < T_B0 + 0.5:
        b = ease_out((t - T_A1 - 0.1) / 0.3) * (1 - ease((t - T_B0 - 0.1) / 0.35))
        note.banner(ctx, "1万個を育てて\nぜんぶ比べる", 520, 950, a=b, t_rel=t - T_A1, size=54)
    draw_10k(ctx, t, b_alpha(t))
    if T_ST2 <= t < T_C0 + 0.3:
        b = ease_out((t - T_ST2) / 0.3) * (1 - ease((t - T_C0 - 0.1) / 0.3))
        lab = "1万個で\n同じ形は 1組だけ" if sm["identical"] == 1 else f"1万個で\n同じ形は {sm['identical']}組"
        note.sticky(ctx, lab, 470, 905, 60, "pink", fg=RED, a=b, tilt=-0.02)
    if T_C0 <= t < T_TW + 0.3:
        b = ease_out((t - T_C0) / 0.35) * (1 - ease((t - T_TW) / 0.3))
        i, j = sm["best_pair"]
        if sm["identical"] > 0:
            draw_same(ctx, t, i, j, b)
        else:
            draw_pair(ctx, t, i, j, T_C0, b, "1万個の中で、いちばん似た2つ", INK)
    if T_TW <= t < T_TW_RUN:
        b = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.2) / 0.2))
        note.banner(ctx, "同じ空を通った\n2つは？", 520, 900, a=b, t_rel=t - T_TW, size=56)
    if T_TW_RUN <= t < T_WHY + 0.3:
        b = ease_out((t - T_TW_RUN) / 0.35) * (1 - ease((t - T_WHY) / 0.3))
        _, kt = pick_samples()
        p1, p2 = twin_ids(kt)
        draw_pair(ctx, t, p1, p2, T_TW_RUN, b, "同じ空を通ったふたご", RED, title_out=T_TW_ST - 0.2)
        if t >= T_TW_VAL:
            b2 = ease_out((t - T_TW_VAL) / 0.3) * b
            if t >= T_TW_ST:
                note.sticky(ctx, "ふたごみたいに よく似る", 525, 645, 46, "pink", fg=RED,
                            a=ease_out((t - T_TW_ST) / 0.3) * b, tilt=-0.02)
            text(ctx, f"ふたご1,000組の平均 {pct(sm['twin_mean'])}%", 470, 1255, 36, INK, alpha=b2)
            text(ctx, f"（ちがう空どうしは平均 {pct(sm['mean_diff'])}%、いちばん似ても {pct(sm['best'])}%）", 470, 1303, 30,
                 PENCIL, bold=False, alpha=b2)
            if t >= T_TW_VAL + 1.0:
                b3 = ease_out((t - T_TW_VAL - 1.0) / 0.3) * b
                lab = (f"マス1つまで同じ形も {sm['twin_exact']}組" if sm["twin_exact"] > 0
                       else "それでも、マス1つまで同じは 0組")
                text(ctx, lab, 470, 1365, 36, RED, alpha=b3)
    if T_WHY <= t:
        b = ease_out((t - T_WHY) / 0.35)
        if t >= T_Q:
            b *= 1 - 0.8 * ease_out((t - T_Q) / 0.35)
        _, kt = pick_samples()
        p1, _p2 = twin_ids(kt)
        g = ease(clamp01((t - T_WHY - 0.2) / 1.8))
        draw_crystal(ctx, p1, 345, 890, 420, p=max(0.03, g), a=b, style="stage")
        draw_strip(ctx, p1, 690, 790, 690, 1110, a=b, ring=True)
        text(ctx, "通ってきた空", 740, 650, 32, INK, bold=False, alpha=b)
        yy = 690 + (1110 - 690) * g
        note.pen_line(ctx, 672, yy, 808, yy, RED, seed=77, width=5, alpha=b)
        if T_WHY + 1.0 <= t < T_Q + 0.35:
            b2 = ease_out((t - T_WHY - 1.0) / 0.3) * (1 - ease_out((t - T_Q) / 0.35))
            note.sticky(ctx, "形は、通ってきた空の記録", 470, 1250, 46, "mint", a=b2, tilt=-0.015)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで6本の腕は\n同じ形にそろうの？", 470, 760, 54, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.0) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 470, 975, 50, "pink", fg=RED, a=r, tilt=0.025)
        if t >= T_Q + 1.6:
            c = ease_out((t - T_Q - 1.6) / 0.4)
            text(ctx, "「雪は天から送られた手紙である」", 470, 1195, 36, INK, bold=False, alpha=c)
            text(ctx, "中谷宇吉郎", 700, 1250, 30, PENCIL, bold=False, alpha=c)


def scene(ctx, t):
    note.paper(ctx)
    intro().draw(ctx, t, reveal_t=T_REV)
    if t < T_MOVE:
        return
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------
def chime(freq, dur=0.5):
    tt = _t(dur)
    return ((np.sin(2 * np.pi * freq * tt) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * tt))
            * np.exp(-tt * 7) * np.minimum(1, tt * 300))


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    rng = np.random.default_rng(3)
    scale = [1568.0, 1760.0, 2093.0, 2349.3, 2637.0]
    tt = 0.05
    while tt < T_MOVE:                            # 冒頭: 結晶がきらきら
        mx.add(tt, chime(float(rng.choice(scale)), 0.6), 0.05)
        tt += rng.uniform(0.28, 0.5)
    intro().audio(mx)
    mx.add(T_A0, whoosh(0.6), 0.1)
    mx.add(T_A1 - 0.05, chime(1318.5, 0.8), 0.25)
    mx.add(T_A1 + 0.05, chime(1568.0, 0.8), 0.25)
    mx.add(T_B0 - 0.8, riser(0.8), 0.5)
    beat(mx, T_B0, T_B1, bpm=124, vol=0.5, accel=True)
    for q in range(int(B_DUR / 0.25)):
        mx.add(T_B0 + q * 0.25, core.shimmer(20 + q * 3, seed=q), 0.25)
    mx.add(T_FL, thump(), 0.6)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST2, blip(659.3, 0.15), 0.35)
    mx.add(T_C0, chime(1046.5, 0.8), 0.3)
    mx.add(T_C0 + 1.0, blip(523.3, 0.15), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)
    mx.add(T_TW_RUN, chime(1318.5, 0.9), 0.3)
    mx.add(T_TW_RUN + 1.0, blip(523.3, 0.15), 0.3)
    mx.add(T_TW_VAL, bell(1046.5, 1.6), 0.5)
    mx.add(T_WHY, chime(1568.0, 0.9), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.0, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------
def reiter_reference(s, beta, gamma):
    """Reiter の1手を、1マスずつ素直に書いたもの（照合用）"""
    n = s.shape[0]
    ice = s >= 1

    def nbs(q, r):
        return [(q + dq, r + dr) for dq, dr in SHIFTS if 0 <= q + dq < n and 0 <= r + dr < n]

    rec = np.zeros_like(ice)
    for q in range(n):
        for r in range(n):
            rec[q, r] = ice[q, r] or any(ice[a, b] for a, b in nbs(q, r))
    out = np.zeros_like(s)
    for q in range(n):
        for r in range(n):
            if OUTSIDE[q, r]:
                out[q, r] = beta
                continue
            uu = 0.0 if rec[q, r] else s[q, r]
            nsum = sum(0.0 if rec[a, b] else s[a, b] for a, b in nbs(q, r))
            out[q, r] = uu / 2 + nsum / 12 + (s[q, r] + gamma if rec[q, r] else 0.0)
    return out


def ref_grow(beta, gamma, ends, noise_ids, eps, steps):
    """grow を、step_once と同じ書き方（配列を使い回さない）で書き直したもの（照合用）。凍った手を返す"""
    B = len(beta)
    S = np.repeat(beta[:, 0].astype(np.float32)[:, None, None], N, 1).repeat(N, 2)
    S[:, M, M] = 1.0
    tf = np.full((B, N, N), -1, np.int16)
    tf[:, M, M] = 0
    stage = np.zeros(B, int)
    nid = np.asarray(noise_ids, np.int64)
    ar = np.arange(B)
    for t in range(1, steps + 1):
        ice = S >= 1
        rec = ice | (nb_sum(ice.astype(np.float32)) > 0)
        ns = np.minimum((ends < t).sum(1), K_MAX - 1)
        sw = ns != stage
        ratio = np.where(sw, beta[ar, ns] / beta[ar, stage], 1.0).astype(np.float32)[:, None, None]
        S = np.where(rec, S, S * ratio)
        stage = ns
        b = beta[ar, stage].astype(np.float32)[:, None, None]
        g = gamma[ar, stage].astype(np.float32)[:, None, None]
        u = np.where(rec, np.float32(0), S)
        if eps > 0:
            u = u * (1 + np.float32(eps) * bank()[(nid * 7919 + t * 104729) % N_BANK])
        S = u + (nb_sum(u) - 6 * u) / np.float32(12) + np.where(rec, S + g, np.float32(0))
        S = np.where(OUTSIDE, b, S)
        tf[(S >= 1) & (tf < 0)] = t
    return tf


def run_checks():
    d = data()
    sm = summary()
    checks = []
    # (1) 1手の更新
    rng = np.random.default_rng(1)
    s = (0.4 + 0.05 * rng.standard_normal((N, N))).astype(np.float32)
    s[M - 3:M + 4, M - 2:M + 3] = 1.2
    s[OUTSIDE] = 0.4
    ref = reiter_reference(s.astype(np.float64), 0.4, 0.003)
    got = step_once(s[None], np.float32(0.4), np.float32(0.003))[0]
    checks.append(("Reiter の1手: 1マスずつ書いた式との最大のずれ", float(np.max(np.abs(got - ref))), 0.0, 1e-5))
    # (1b) 速く書いた grow の1手が、素直に書いた形と同じ（3個・ゆらぎ入り・180手）
    hb, hg, he = histories(3, 55)
    T_R = 180
    he2 = np.minimum(he, 10 ** 6)
    tf_fast, _, _ = grow(hb, hg, he2, np.arange(3))
    tf_ref = ref_grow(hb, hg, he2, np.arange(3), EPS, T_R)
    fa = np.where((tf_fast >= 0) & (tf_fast <= T_R), tf_fast, -1)
    checks.append(("速い grow と素直な書き方: 180手までの凍った手が一致するマスの割合",
                   float(np.mean(fa == tf_ref)), 1.0, 1e-4))
    # (2) 12通りの向き
    checks.append(("12通りの向きが、すべて別の並べかえ", float(len({tuple(p) for p in SYM_C})), 12.0, 0.0))
    checks.append(("向きで移った先が円の中に閉じる", float(all((p >= 0).all() and len(set(p.tolist())) == NC for p in SYM_C)), 1.0, 0.0))
    r6 = np.arange(NC)
    for _ in range(6):
        r6 = r6[SYM_C[1]]
    checks.append(("60°を6回で元にもどる", float(np.array_equal(r6, np.arange(NC))), 1.0, 0.0))
    # (3) 行列の掛け算の似ている度 vs 1組ずつ
    mk = d["mk"]
    sub = np.random.default_rng(2).choice(N_DIFF, 60, replace=False)
    _id, _h, bp, _bpj = all_pairs(mk[sub], block=60)
    gap = max(abs(max(iou_pair(mk[sub[a]], mk[sub[b]])[0] for b in range(a)) - bp[a]) for a in range(1, len(sub)))
    checks.append(("似ている度: 行列の掛け算と1組ずつの最大のずれ（60個・1,770組）", float(gap), 0.0, 1e-5))
    # (4) ゆらぎ無しなら6回対称
    hb, hg, he = histories(3, 77)
    tf0, _, _ = grow(hb, hg, he, np.arange(3), eps=0.0)
    m0 = masks_of(tf0)
    sym6 = min(np.count_nonzero(m0[q] & m0[q][SYM_C[1]]) / np.count_nonzero(m0[q] | m0[q][SYM_C[1]]) for q in range(3))
    checks.append(("ゆらぎ無しの結晶が60°回しと一致（3個）", float(sym6), 1.0, 0.0))
    # (5) 画面の数字
    checks.append(("全部の組の数", float(int(d["hist"].sum())), float(sm["n_pairs"]), 0.0))
    checks.append(("同じ形の組（ヒストグラムの100%の棚）", float(sm["identical"]), float(d["hist"][100]), 0.0))
    i, j = sm["best_pair"]
    checks.append(("いちばん似た2つ: 1組ずつ数え直した値", float(iou_pair(mk[i], mk[j])[0]), sm["best"], 1e-6))
    kt = pick_samples()[1]
    checks.append(("見本のふたご: 数え直した似ている度", float(iou_pair(*[mk[q] for q in twin_ids(kt)])[0]),
                   float(d["twin"][kt]), 1e-9))
    checks.append(("止める大きさに届かなかった結晶", float(sm["unreached"]), 0.0, 0.0))
    checks.append(("画面の「同じ形 n組」（1万個を数え終えたとき）が全部の組の集計と一致",
                   float(np.count_nonzero(d["best_prev"][:N_DIFF] >= 1 - 1e-9)), float(sm["identical"]), 0.0))
    # (6) 答え
    checks.append(("答えの番号（同じ形の組の数から）", float(intro().correct), float(correct_index()), 0.0))
    checks.append(("ふたごは、ちがう空どうしより似ている（平均）", float(sm["twin_mean"] > sm["mean_diff"]), 1.0, 0.0))
    check_answers(checks)


def save_stills(times):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for tt in times:
        p = OUT / f"still_{tt:05.1f}.png"
        core.still(draw, tt, p)
        paths.append(p)
    thumb, cols = (270, 480), 6
    ims = [Image.open(p).convert("RGB").resize(thumb) for p in paths]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * (thumb[0] + 8), (k // cols) * (thumb[1] + 8)))
    sheet.save(OUT / "sheet.png")
    print("一覧:", OUT / "sheet.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    sm = summary()
    print(f"長さ={DURATION:.1f}秒")
    print(sm)
    print("見本:", pick_samples())
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.5, 5.0, 8.0, 9.5, 11.0, 12.6, 14.5, 16.0, 18.0, 20.0, 21.0, 22.5, 24.5, 25.8,
              27.5, 29.0, 30.5, 32.0, 33.5, 35.0, 36.5, 38.0]
        save_stills([x for x in ts if x < DURATION])
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
