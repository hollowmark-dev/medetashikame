"""合戦で兵が2倍。「数が多いほうが勝つ」は、どれくらい本当か【1万回で確かめた】（横型ロング）。
主戦場は 赤1万人 vs 青5千人（v2。v1 は 100 vs 50 → sims/kassen-long.v1.py）。

このファイルは公開日まで非公開（答えが書いてある）。
この部分はモデル（数字の計算・種の選び方・照合・数字の書き出し）。場面（描画）は同じファイルに後から足す。

モデル（ランチェスターの法則を、兵1人1人の確率で。F. W. Lanchester, 1916）
  時間      : 一斉射撃（ターン）ごと。両軍が同時に処理する（倒される兵も、その回は撃つ／斬る）。
  撃ち合い  : （2次法則）生きている兵がそれぞれ、相手の生きている兵からでたらめに1人を狙い、確率 p で倒す。
              同じ兵に2本当たっても倒れるのは1人。両軍同じ p = 0.04（ショートと同じ）。
  斬り合い  : （1次法則）前線で向き合った組だけが戦う。組の数 = min(赤の生存, 青の生存, 前線の幅 W)。
              各組は毎ターン確率 q で決着し、どちらが倒れるかは腕前の比で決まる（腕前が k 倍なら、勝つ確率は k/(1+k)）。
              q = 2p = 0.08（腕前が同じなら、1人が1ターンに相手を倒す確率が p ＝ 撃ち合いと同じ強さ）。
  狭い道    : 撃ち合いでも斬り合いでも、一度に戦える人数を両軍とも W に制限（残りは後ろで待つ）。
              撃ち合いは、前の W 人どうしで狙う／狙われる。
  相手を分ける: 片方が2つ・3つ…に分かれて順に来る。前の組が全滅してから次が来る（生き残りはそのまま次と戦う）。
  腕前      : 青の腕前を k 倍（撃ち合い: p → k×p、斬り合い: 勝つ確率 k/(1+k)）。

理論（連続の近似）
  2次法則（撃ち合い）: 残り = √(R² − B²)。1万 vs 5千 なら 8660（100 vs 50 なら 86.6。同じ割合）。互角にする腕前 k = (R/B)² = 4。
  1次法則（斬り合い）: 残り = R − k×B。1万 vs 5千（k=1）なら 5000。互角にする腕前 k = R/B = 2。
  狭い道では撃ち合いも「向き合うのは W 人ずつ」になって 1次法則に近づく（互角の k が 4 → 2 に近づく）。
  分かれた相手: 残り² = R² − ΣB²。7500 vs 5000+5000 → √(7500²−2×5000²)=2500。（ショートの 80 vs 50+50 → 37.4）
  離散の確率モデルは、理論（連続）より約2人少なく出る。理由は3つ: ①同じ兵に2本当たる（無駄玉。倒した数は「当たった数」より少ない）
  ②1ターンごとの運（ばらつき）が、兵が少なくなった終盤に効く ③一斉射撃は同時処理で、倒される兵もその回は撃つ。
  p を小さくすると理論に近づく（--check の p 掃引で確認）。

台本の章と、ここで作るもの（主戦場は 赤1万人 vs 青5千人。画面では足軽1人の絵＝100人）
  1章: 1万 vs 5千 の撃ち合い 1万回（残りの平均・中央値・分布、青が勝った回数、ターン数）。種を変えた3回
  2章: 最初の一斉射撃の期待値（10000p と 5000p）、兵1人あたりの狙われ方（0.5本 と 2本）
  3章: 青の腕前 k = 1,2,3,3.5,4,4.5,5,6 の勝率、互角の k（規模が大きいと4倍を境に崖のように変わる）
  4章: 斬り合い 1万 vs 5千（残り 理論 5000）、互角の腕前（理論 2）
  5章: 狭い道（W = 50,100,300,1000,3000 と野原）。台本で使うのは幅50。撃ち合い・斬り合いの残りと、互角の k
  6章: 相手を分ける（赤7500 vs 青1万 を 一度に／2つ／3つ／4つ／5つ／10こ、境目の人数。斬り合いで分けても変わらない）
  7章: ターン数（早送りの設計）。画面の見本（1回ぶんの戦いの経過）も data.json の samples に入れる
  小さい規模のまま残すもの（規模によらない性質の照合）: ショートの数字との照合（100 vs 50）、ショートのおさらい
  （80 vs 50+50）、1人ずつ追う数え方との一致、p 掃引。残りの割合が規模によらず約85%なことは N_SWEEP（10〜5000）で示す
  計算時間を減らすため、互角の k の探索・境目の二分探索は n=2000（N_TRIALS_SEARCH）。主要な統計は各1万回

使い方
  python sims/kassen-long.py --check      照合だけ（数字の再計算を含む。キャッシュを使う）
  python sims/kassen-long.py --numbers    数字の書き出し（out/kassen-long/numbers.md）
  python sims/kassen-long.py --recompute  キャッシュを捨てて全部やり直す
  python sims/kassen-long.py              照合 → numbers.md
  python sims/kassen-long.py --seeds      画面の見本の種の探し直し（data.json の統計から「ふつうの結果」を選ぶ）
  python sims/kassen-long.py --samples    画面の見本（samples）だけ作り直して data.json に入れる
乱数の種は、画面の見本（1回の戦い）を「ふつうの結果」にするために選んでよい。画面の統計は全試行から正直に出している。
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers
from engine.parts import r1

SLUG = "kassen-long"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ============================================================
# モデルの値（変えると別の戦場になる）
# ============================================================
P_HIT = 0.04            # 撃ち合い: 1回の射撃で相手1人を倒す確率（両軍同じ。ショートと同じ）
Q_DUEL = 2 * P_HIT      # 斬り合い: 向き合った1組が1ターンに決着する確率（腕前が同じなら、1人あたり p と同じ強さ）
N_R, N_B = 10000, 5000  # 赤軍・青軍（主戦場）。画面では足軽1人の絵＝100人
SMALL_R, SMALL_B = 100, 50   # 規模によらない性質の照合に使う小さい規模（ショートの数字・1人ずつ追う数え方・p 掃引）
N_TRIALS = 10000
N_TRIALS_SEARCH = 2000  # 互角の k の探索・境目の二分探索など繰り返しの多いもの（規模が大きいとばらつきが小さいので十分）
W_WIDE = 1000000        # 広い野原（前線の幅の制限なし）
W_LIST = (50, 100, 300, 1000, 3000)      # 狭い道の幅（広い野原は別に出す）。台本で使うのは幅50
W_SMALL = 5                               # 小さい規模（100 vs 50）の狭い道。1人ずつ追う数え方との照合用
K_LIST = (1, 2, 3, 3.5, 4, 4.5, 5, 6)    # 青の腕前の倍率（4倍を境に崖）
K_LIST_SHORT = (1, 2, 3, 4, 5, 6)        # ショートとの照合（100 vs 50）
K_DUEL = (1, 1.5, 2, 2.5, 3)
P_LIST = (0.01, 0.02, 0.04, 0.07, 0.1)  # p を変えても結果が同じか（100 vs 50）
N_SWEEP = (10, 25, 50, 100, 200, 400, 1000, 5000)   # 大きさを変える（青の人数。赤は2倍）
SPLIT_R = 7500          # 6章: 赤7500人 vs 青1万人
SPLITS = {"一度に": (10000,), "2つ": (5000, 5000), "3つ": (3334, 3333, 3333)}
SPLIT_EXTRA = {"4つ": (2500,) * 4, "5つ": (2000,) * 5, "10こ": (1000,) * 10}
SPLIT_LABEL = {"一度に": "一度に(1万)", "2つ": "2つ(5000×2)", "3つ": "3つ(3334+3333+3333)", "4つ": "4つ(2500×4)",
               "5つ": "5つ(2000×5)", "10こ": "10こ(1000×10)"}
CURVE_R = tuple(range(4000, 11001, 500))  # 勝率曲線の赤の人数
TH_LO, TH_HI, TH_TOL = 2000, 12000, 10    # 境目の二分探索（10人単位）
SHORT_TWIST = (80, (50, 50))             # ショートの「ひねり」（おさらい用。100人規模のまま）
SEED_RUNS = (101, 102, 103)              # 1章: 種を変えた3回（各1万回）
SEED_CHECK = 999                         # 別の乱数でやり直す
# 画面の見本（1回の戦い）の種。--seeds で探し直せる
SEED_SAMPLES = (6, 16, 24)                 # 1万 vs 5千 の撃ち合い 3回（"ふつうの結果"）
SEED_DUEL_SAMPLE = 1                      # 斬り合い 野原
SEED_NARROW_SAMPLE = 13                   # 狭い道 幅50 撃ち合い
SEED_SPLIT_SAMPLE = 11                    # 7500 vs 3つ（3334+3333+3333）
SAMPLE_W = 50

# ============================================================
# 画面に出す数字（照合の相手）。ショートの数字（司令塔から 2026-10-08）
# ============================================================
SHORT_MEAN, SHORT_SD, SHORT_MEAN_2 = 84.55, 4.73, 84.53         # 100 vs 50 の残り（ショート: 別乱数でも 84.53）
SHORT_K_WIN = (0.0, 0.0001, 0.065, 0.517, 0.886, 0.984)          # k=1〜6 で50人側の勝率
SHORT_K50 = 3.96
SHORT_TWIST_SHOT = (0.005, 0.89, 33.4)                           # 80 vs 100: 一度に→80人側の勝率／50+50→勝率／残り平均


# ============================================================
# 1. 戦いの計算（1万回を一斉に進める）
# ============================================================
def _distinct(s, m, rng):
    """m 個の的に s 本をでたらめに当てたとき、的に当たった異なる数（的ごとの重なりを除く）。s, m は配列"""
    d = np.zeros(len(s), np.int64)
    mx = int(s.max()) if len(s) else 0
    for j in range(mx):
        idx = np.flatnonzero(s > j)
        if idx.size == 0:
            break
        new = rng.random(idx.size) < (m[idx] - d[idx]) / m[idx]
        d[idx] += new
    return d


def shoot_batch(R0, B0, pR, pB, rng, W=W_WIDE, track=0):
    """撃ち合いを n 回ぶん一斉に進める。R0, B0 は人数（配列でも整数でも）。
    返り値: R, B（最後の人数）, turns（ターン数）, [track>0 のとき] 各ターン後の (R, B) の配列（n×(track+1)×2）"""
    R = np.array(R0, np.int64)
    B = np.array(B0, np.int64)
    if R.ndim == 0:
        R = np.full(1, int(R))
    n = len(R)
    if B.ndim == 0:
        B = np.full(n, int(B))
    turns = np.zeros(n, np.int64)
    tr = None
    if track:
        tr = np.zeros((n, track + 1, 2), np.int64)
        tr[:, 0, 0], tr[:, 0, 1] = R, B
    t = 0
    while True:
        idx = np.flatnonzero((R > 0) & (B > 0))
        if idx.size == 0:
            break
        r, b = R[idx], B[idx]
        ar, ab = np.minimum(r, W), np.minimum(b, W)
        sR = rng.binomial(ar, pR)
        sB = rng.binomial(ab, pB)
        dB = _distinct(sR, ab, rng)
        dR = _distinct(sB, ar, rng)
        R[idx], B[idx] = r - dR, b - dB
        turns[idx] += 1
        t += 1
        if track and t <= track:
            tr[:, t, 0], tr[:, t, 1] = R, B
    if track:
        for u in range(t + 1, track + 1):
            tr[:, u] = tr[:, t]
        return R, B, turns, tr
    return R, B, turns


def duel_batch(R0, B0, q, kb, rng, W=W_WIDE, track=0):
    """斬り合いを n 回ぶん一斉に進める。kb = 青の腕前 ÷ 赤の腕前。組の数 = min(R, B, W)。
    各組は確率 q で決着し、赤が倒れる確率は kb/(1+kb)。track>0 のときは各ターン後の (R, B) も返す"""
    R = np.array(R0, np.int64)
    B = np.array(B0, np.int64)
    if R.ndim == 0:
        R = np.full(1, int(R))
    n = len(R)
    if B.ndim == 0:
        B = np.full(n, int(B))
    turns = np.zeros(n, np.int64)
    pred = kb / (1.0 + kb)
    tr = None
    if track:
        tr = np.zeros((n, track + 1, 2), np.int64)
        tr[:, 0, 0], tr[:, 0, 1] = R, B
    t = 0
    while True:
        idx = np.flatnonzero((R > 0) & (B > 0))
        if idx.size == 0:
            break
        r, b = R[idx], B[idx]
        pairs = np.minimum(np.minimum(r, b), W)
        ev = rng.binomial(pairs, q)
        rf = rng.binomial(ev, pred)
        R[idx], B[idx] = r - rf, b - (ev - rf)
        turns[idx] += 1
        t += 1
        if track and t <= track:
            tr[:, t, 0], tr[:, t, 1] = R, B
    if track:
        for u in range(t + 1, track + 1):
            tr[:, u] = tr[:, t]
        return R, B, turns, tr
    return R, B, turns


def run_batch(mode, R0, B0, rng, W=W_WIDE, k=1.0, p=P_HIT):
    """mode = "shoot"（撃ち合い）／"duel"（斬り合い）。青の腕前は k 倍"""
    if mode == "shoot":
        return shoot_batch(R0, B0, p, min(1.0, k * p), rng, W)
    return duel_batch(R0, B0, Q_DUEL * (p / P_HIT), k, rng, W)


def run_sequence(mode, R0, groups, n, rng, W=W_WIDE, k=1.0, p=P_HIT):
    """赤 R0 人が、青の組 groups（人数のタプル）と順に戦う。前の組が全滅してから次が来る。
    返り値: 赤の最後の人数（負けは0）, 総ターン数, 負けた組の番号（勝ちは -1）"""
    R = np.full(n, R0, np.int64)
    turns = np.zeros(n, np.int64)
    lost = np.full(n, -1, np.int64)
    for gi, g in enumerate(groups):
        idx = np.flatnonzero((R > 0) & (lost < 0))
        if idx.size == 0:
            break
        Rn, Bn, t = run_batch(mode, R[idx], g, rng, W, k, p)
        R[idx] = Rn
        turns[idx] += t
        lost[idx[Rn == 0]] = gi
    R[lost >= 0] = 0
    return R, turns, lost


def summarize(R, B, turns):
    """勝敗と、勝った側の残り人数・ターン数の要約。R, B は戦いの最後の人数"""
    red, blue, tie = (R > 0) & (B == 0), (B > 0) & (R == 0), (R == 0) & (B == 0)
    rem = np.where(red, R, np.where(blue, B, 0))
    win = rem[red | blue]
    d = dict(n=len(R), red=int(red.sum()), blue=int(blue.sum()), tie=int(tie.sum()))
    if len(win):
        d.update(rem_mean=float(win.mean()), rem_median=float(np.median(win)), rem_sd=float(win.std(ddof=1)),
                 rem_p5=float(np.percentile(win, 5)), rem_p95=float(np.percentile(win, 95)),
                 rem_min=int(win.min()), rem_max=int(win.max()))
    if red.any():
        d.update(red_rem_mean=float(R[red].mean()), red_rem_median=float(np.median(R[red])),
                 red_rem_sd=float(R[red].std(ddof=1)) if red.sum() > 1 else 0.0)
    d.update(turns_mean=float(turns.mean()), turns_median=float(np.median(turns)),
             turns_p10=float(np.percentile(turns, 10)), turns_p90=float(np.percentile(turns, 90)),
             turns_max=int(turns.max()))
    return d


def blue_rate(d):
    """青が勝った割合（引き分けは含めない）"""
    return d["blue"] / d["n"]


# ============================================================
# 2. 1人ずつ追う数え方（速い数え方の照合に使う。小さい規模で）
# ============================================================
def shoot_explicit(ids_a, ids_b, pa, pb, rng, W=W_WIDE, max_v=3000):
    """1人ずつ追う撃ち合い。返り値: ターンごとの記録 [(A側の射撃, B側の射撃)], 生き残り A, B。
    射撃 = [(撃った兵, 狙われた兵, 当たったか)]。前線 = 並びの先頭 W 人（倒れたら後ろから入る）"""
    A, Bl = list(ids_a), list(ids_b)
    vol = []
    while A and Bl and len(vol) < max_v:
        fa, fb = A[:W], Bl[:W]
        sa = [(s, fb[int(rng.integers(len(fb)))], bool(rng.random() < pa)) for s in fa]
        sb = [(s, fa[int(rng.integers(len(fa)))], bool(rng.random() < pb)) for s in fb]
        vol.append((sa, sb))
        dead_b = {t for _, t, h in sa if h}
        dead_a = {t for _, t, h in sb if h}
        A = [x for x in A if x not in dead_a]
        Bl = [x for x in Bl if x not in dead_b]
    return vol, A, Bl


def duel_explicit(ids_a, ids_b, q, pred_a, rng, W=W_WIDE, max_v=100000):
    """1人ずつ追う斬り合い。pred_a = A が倒れる確率（決着したとき）。返り値: ターンごとの記録
    [[(A の兵, B の兵, 倒れたのは 'A'/'B'/None)]], 生き残り A, B"""
    A, Bl = list(ids_a), list(ids_b)
    vol = []
    while A and Bl and len(vol) < max_v:
        n = min(len(A), len(Bl), W)
        rec, da, db = [], set(), set()
        for i in range(n):
            if rng.random() < q:
                if rng.random() < pred_a:
                    rec.append((A[i], Bl[i], "A"))
                    da.add(A[i])
                else:
                    rec.append((A[i], Bl[i], "B"))
                    db.add(Bl[i])
            else:
                rec.append((A[i], Bl[i], None))
        vol.append(rec)
        A = [x for x in A if x not in da]
        Bl = [x for x in Bl if x not in db]
    return vol, A, Bl


def alive_counts(vol, nA, nB, kind="shoot"):
    """ターンごとの (A, B) 生き残り（そのターンが終わったあと）"""
    a, b = nA, nB
    out = []
    for v in vol:
        if kind == "shoot":
            sa, sb = v
            a -= len({t for _, t, h in sb if h})
            b -= len({t for _, t, h in sa if h})
        else:
            a -= sum(1 for _, _, f in v if f == "A")
            b -= sum(1 for _, _, f in v if f == "B")
        out.append((a, b))
    return out


# ============================================================
# 3. 理論
# ============================================================
def lanchester_square(R, B):
    """2次法則（連続）: 残り = √(R²−B²)。R≦B なら 0"""
    return math.sqrt(R * R - B * B) if R > B else 0.0


def lanchester_linear(R, B, k=1.0):
    """1次法則（連続）: 残り = R − k×B。青の腕前が k 倍。負けは 0"""
    return max(0.0, R - k * B)


def one_step_kills(shooters, targets, p):
    """閉じた式: 1回の一斉射撃で、targets 人の側のうち倒れる人数の期待値。
    1人が生き残る確率 = どの射手もその兵を狙って当てない = (1 − p/targets)^shooters"""
    return targets * (1.0 - (1.0 - p / targets) ** shooters)


def mean_field(mode, R, B, k=1.0, W=W_WIDE, p=P_HIT, max_v=20000):
    """平均場: 人数を実数のまま期待値で1ターンずつ進める。返り値: (R, B, ターン数)"""
    R, B = float(R), float(B)
    v = 0
    while R > 0.5 and B > 0.5 and v < max_v:
        if mode == "shoot":
            ar, ab = min(R, W), min(B, W)
            dB = one_step_kills(ar, ab, min(1.0, k * p))
            dR = one_step_kills(ab, ar, p)
        else:
            ev = Q_DUEL * (p / P_HIT) * min(R, B, W)
            dR, dB = ev * k / (1 + k), ev / (1 + k)
        R, B = R - dR, B - dB
        v += 1
    return max(R, 0.0), max(B, 0.0), v


def mean_field_remain(mode, R, B, **kw):
    r, b, _ = mean_field(mode, R, B, **kw)
    return r if r > b else 0.0


def mean_field_sequence(mode, R, groups, **kw):
    for g in groups:
        R, b, _ = mean_field(mode, R, g, **kw)
        if R <= b:
            return 0.0
    return R




# ============================================================
# 4. 章ごとの計算
# ============================================================
def rng_for(seed, *keys):
    return np.random.default_rng([seed, *keys])


def k_scan(mode, W, ks, seed, n=N_TRIALS, p=P_HIT, nr=N_R, nb=N_B):
    """青の腕前 k ごとの、青が勝った割合（引き分けは別）と、勝った側の残りの平均"""
    out = []
    for k in ks:
        rng = rng_for(seed, int(round(k * 1000)), W)
        R, B, t = run_batch(mode, np.full(n, nr), nb, rng, W, k, p)
        d = summarize(R, B, t)
        out.append((float(k), d["blue"] / n, d["tie"] / n, d))
    return out


def k50_find(mode, W, seed, n=N_TRIALS, p=P_HIT, lo=1.0, hi=6.0, nr=N_R, nb=N_B):
    """青の勝率が 50% になる k。粗い格子（0.25刻み）→ 細かい格子（0.05刻み）→ 直線補間"""
    ks = np.arange(lo, hi + 1e-9, 0.25)
    sc = k_scan(mode, W, ks, seed, n, p, nr, nb)
    rates = [r for _, r, _, _ in sc]
    j = next((i for i in range(len(rates) - 1) if rates[i] < 0.5 <= rates[i + 1]), None)
    if j is None:
        return float("nan")
    ks2 = np.arange(ks[j], ks[j + 1] + 1e-9, 0.05)
    sc2 = k_scan(mode, W, ks2, seed + 1, n, p, nr, nb)
    r2 = [r for _, r, _, _ in sc2]
    for i in range(len(r2) - 1):
        if r2[i] < 0.5 <= r2[i + 1]:
            a, b = ks2[i], ks2[i + 1]
            return float(a + (0.5 - r2[i]) / (r2[i + 1] - r2[i]) * (b - a))
    return float(ks2[int(np.argmin([abs(r - 0.5) for r in r2]))])


def split_stats(mode, R0, groups, seed, n=N_TRIALS, W=W_WIDE, k=1.0, p=P_HIT):
    rng = rng_for(seed, R0, sum(groups), len(groups), 7)
    R, t, lost = run_sequence(mode, R0, groups, n, rng, W, k, p)
    win = R > 0
    return dict(n=n, win=float(win.mean()), rem_mean=float(R[win].mean()) if win.any() else 0.0,
                rem_median=float(np.median(R[win])) if win.any() else 0.0,
                rem_sd=float(R[win].std(ddof=1)) if win.sum() > 1 else 0.0,
                turns_mean=float(t.mean()), turns_median=float(np.median(t)),
                turns_p10=float(np.percentile(t, 10)), turns_p90=float(np.percentile(t, 90)),
                lost_at=[int((lost == i).sum()) for i in range(len(groups))])


def split_threshold(mode, groups, seed, n=N_TRIALS_SEARCH, lo=TH_LO, hi=TH_HI, tol=TH_TOL, W=W_WIDE):
    """赤が何人いれば勝率 50% 以上か（二分探索。勝率は人数に対して増えるとみなす。tol 人の精度）。
    返り値: (境目の人数, その人数の勝率, 境目より tol 人以内で少ない人数の勝率, その人数)"""
    a, b = lo, hi
    memo = {}

    def rate(R0):
        if R0 not in memo:
            memo[R0] = split_stats(mode, R0, groups, seed, n, W)["win"]
        return memo[R0]
    assert rate(a) < 0.5 <= rate(b), (mode, groups, rate(a), rate(b))
    while b - a > tol:
        m = (a + b) // 2
        if rate(m) >= 0.5:
            b = m
        else:
            a = m
    return b, rate(b), rate(a), a


def mean_field_threshold(groups, lo=1000, hi=20000):
    """平均場（期待値だけの漸化式）で、赤が全部の組に勝てる最小の人数（1人刻みの二分探索）"""
    while hi - lo > 1:
        m = (lo + hi) // 2
        if mean_field_sequence("shoot", m, groups) > 0:
            hi = m
        else:
            lo = m
    return hi


def explicit_check(mode, W, n, seed, nr=SMALL_R, nb=SMALL_B):
    """1人ずつ追う数え方での、勝った側の残りの平均と標準誤差、赤の勝率（小さい規模）"""
    rng = rng_for(seed, 31, W, 0 if mode == "shoot" else 1)
    rem, redwin = [], 0
    for _ in range(n):
        if mode == "shoot":
            _, A, Bl = shoot_explicit(range(nr), range(nb), P_HIT, P_HIT, rng, W)
        else:
            _, A, Bl = duel_explicit(range(nr), range(nb), Q_DUEL, 0.5, rng, W)
        rem.append(max(len(A), len(Bl)))
        redwin += len(A) > 0
    rem = np.array(rem, float)
    return float(rem.mean()), float(rem.std(ddof=1) / math.sqrt(n)), redwin / n


# ---- 画面の見本: 1回ぶんの戦いの経過（ターンごとの人数）----
def sample_shoot(seed, R0=N_R, B0=N_B, W=W_WIDE, track=9000):
    """撃ち合い 1回ぶん。返り値: dict(seed, path=[[赤,青]…], red_left, blue_left, turns)"""
    rng = np.random.default_rng(seed)
    R, B, t, tr = shoot_batch(R0, B0, P_HIT, P_HIT, rng, W, track=track)
    T = int(t[0])
    assert T < track, "track が足りない"
    return dict(seed=seed, path=tr[0, :T + 1].tolist(), red_left=int(R[0]), blue_left=int(B[0]), turns=T)


def sample_duel(seed, R0=N_R, B0=N_B, W=W_WIDE, track=9000):
    """斬り合い 1回ぶん"""
    rng = np.random.default_rng(seed)
    R, B, t, tr = duel_batch(R0, B0, Q_DUEL, 1.0, rng, W, track=track)
    T = int(t[0])
    assert T < track, "track が足りない"
    return dict(seed=seed, path=tr[0, :T + 1].tolist(), red_left=int(R[0]), blue_left=int(B[0]), turns=T)


def sample_split(seed, R0=SPLIT_R, groups=SPLITS["3つ"], W=W_WIDE, track=2000):
    """相手を分けた撃ち合い 1回ぶん。path = [[赤, いま戦っている組の青, 組の番号]…]。
    組が変わるところは、前の組が0になった行の次に、次の組の満員の行が入る"""
    rng = np.random.default_rng(seed)
    path, R = [], R0
    for gi, g in enumerate(groups):
        Rn, Bn, t, tr = shoot_batch(R, g, P_HIT, P_HIT, rng, W, track=track)
        T = int(t[0])
        assert T < track
        path += [[int(a), int(b), gi] for a, b in tr[0, :T + 1]]
        R = int(Rn[0])
        if R == 0:
            break
    return dict(seed=seed, path=path, red_left=R, groups=list(groups), turns=len(path) - len(groups))


def compute_samples():
    ss = dict(main=[sample_shoot(s) for s in SEED_SAMPLES], duel=sample_duel(SEED_DUEL_SAMPLE),
              narrow=sample_shoot(SEED_NARROW_SAMPLE, W=SAMPLE_W), split3=sample_split(SEED_SPLIT_SAMPLE))
    ss["narrow"]["W"] = SAMPLE_W
    return ss


def compute_small(seed):
    """小さい規模（100 vs 50）。ショートの数字・1人ずつ追う数え方との照合用"""
    n = N_TRIALS
    sm = dict()
    R, B, t = shoot_batch(np.full(n, SMALL_R), SMALL_B, P_HIT, P_HIT, rng_for(seed, 101))
    sm["ch1"] = summarize(R, B, t)
    sm["ch1"]["theory"] = lanchester_square(SMALL_R, SMALL_B)
    sm["ch1"]["mean_field"] = mean_field_remain("shoot", SMALL_R, SMALL_B)
    R, B, t = duel_batch(np.full(n, SMALL_R), SMALL_B, Q_DUEL, 1.0, rng_for(seed, 104))
    sm["duel"] = summarize(R, B, t)
    sm["w_small"] = dict(W=W_SMALL)
    for mode in ("shoot", "duel"):
        R, B, t = run_batch(mode, np.full(n, SMALL_R), SMALL_B, rng_for(seed, 105, 0 if mode == "shoot" else 1), W_SMALL)
        sm["w_small"][mode] = summarize(R, B, t)
    sm["k_rows"] = []
    for k, br, tr_, d in k_scan("shoot", W_WIDE, K_LIST_SHORT, seed + 110, nr=SMALL_R, nb=SMALL_B):
        sm["k_rows"].append(dict(k=k, blue=br, tie=tr_, rem_mean=d.get("rem_mean", 0.0)))
    sm["k50"] = k50_find("shoot", W_WIDE, seed + 120, nr=SMALL_R, nb=SMALL_B)
    sm["theory_k50"] = (SMALL_R / SMALL_B) ** 2
    r0, gs = SHORT_TWIST
    sm["twist"] = dict(once=split_stats("shoot", r0, (sum(gs),), seed + 95),
                       split=split_stats("shoot", r0, gs, seed + 96),
                       theory=math.sqrt(r0 ** 2 - sum(g * g for g in gs)))
    # p を変えても（100 vs 50）
    sm["p_rows"] = []
    for pp in P_LIST:
        rng = rng_for(seed, 8, int(pp * 1000))
        R, B, t = shoot_batch(np.full(n, SMALL_R), SMALL_B, pp, pp, rng)
        d = summarize(R, B, t)
        sm["p_rows"].append(dict(p=pp, rem_mean=d["rem_mean"], rem_median=d["rem_median"], rem_sd=d["rem_sd"],
                                 blue=d["blue"], turns_mean=d["turns_mean"],
                                 k50=k50_find("shoot", W_WIDE, seed + 100 + int(pp * 1000), p=pp, lo=2.0, hi=6.0,
                                              nr=SMALL_R, nb=SMALL_B) if pp in (0.02, 0.04, 0.07, 0.1) else None,
                                 mean_field=mean_field_remain("shoot", SMALL_R, SMALL_B, p=pp)))
    # 1人ずつ追う数え方
    sm["explicit"] = []
    for mode, W, nn in (("shoot", W_WIDE, 3000), ("shoot", W_SMALL, 400), ("duel", W_WIDE, 3000), ("duel", W_SMALL, 400)):
        m, se, rw = explicit_check(mode, W, nn, seed)
        sm["explicit"].append(dict(mode=mode, W=W, n=nn, mean=m, se=se, red_win=rw))
    # 1回の一斉射撃の期待値: 閉じた式 ／ 速い数え方（分布） ／ 1人ずつ
    sm["step"] = []
    for (r_, b_) in ((100, 50), (50, 100), (60, 30), (20, 20), (80, 50), (10, 40), (10000, 5000), (5000, 10000)):
        rng = rng_for(seed, 11, r_, b_)
        nn = 40000 if r_ <= 100 else 5000
        fast = _distinct(rng.binomial(r_, P_HIT, nn), np.full(nn, b_), rng)
        if r_ <= 100:
            nn2 = 4000
            ex = np.array([len({int(rng.integers(0, b_)) for _ in range(r_) if rng.random() < P_HIT}) for _ in range(nn2)])
            expl, expl_se = float(ex.mean()), float(ex.std(ddof=1) / math.sqrt(nn2))
        else:
            expl, expl_se = None, None
        sm["step"].append(dict(R=r_, B=b_, closed=one_step_kills(r_, b_, P_HIT), fast=float(fast.mean()),
                               fast_se=float(fast.std(ddof=1) / math.sqrt(nn)), expl=expl, expl_se=expl_se))
    return sm


def compute(seed=1):
    """全部の数字を計算して dict で返す（JSON にできる形）"""
    t0 = time.time()
    res = dict(params=dict(P_HIT=P_HIT, Q_DUEL=Q_DUEL, N_R=N_R, N_B=N_B, N_TRIALS=N_TRIALS,
                           N_TRIALS_SEARCH=N_TRIALS_SEARCH, W_LIST=W_LIST, K_LIST=K_LIST, seed=seed))

    def tick(label):
        print(f"  [{time.time() - t0:6.1f}秒] {label}", flush=True)

    # ---- 1章: 1万 vs 5千 の撃ち合い ----
    n = N_TRIALS
    rng = rng_for(seed, 1)
    R, B, t, tr = shoot_batch(np.full(n, N_R), N_B, P_HIT, P_HIT, rng, track=60)
    ch1 = summarize(R, B, t)
    win = np.where(R > 0, R, B)
    hist = np.bincount(win, minlength=N_R + 1)
    ch1["hist"] = {int(i): int(c) for i, c in enumerate(hist) if c}
    ch1["theory"] = lanchester_square(N_R, N_B)
    ch1["mean_field"] = mean_field_remain("shoot", N_R, N_B)
    ch1["traj_R"] = [float(x) for x in tr[:, :, 0].mean(axis=0)]
    ch1["traj_B"] = [float(x) for x in tr[:, :, 1].mean(axis=0)]
    ch1["traj_diff"] = [float(x) for x in (tr[:, :, 0].astype(float) ** 2 - tr[:, :, 1].astype(float) ** 2).mean(axis=0)]
    ch1["turn_hist"] = {int(a): int(c) for a, c in zip(*np.unique(t, return_counts=True))}
    ch1["runs"] = []
    for s in SEED_RUNS:
        r_, b_, t_ = shoot_batch(np.full(n, N_R), N_B, P_HIT, P_HIT, rng_for(s, 1))
        ch1["runs"].append(dict(seed=s, **summarize(r_, b_, t_)))
    res["ch1"] = ch1
    tick("1章")

    # ---- 2章: 最初の一斉射撃 ----
    p = P_HIT
    ch2 = dict(hits_red=N_R * p, hits_blue=N_B * p,
               kills_red_closed=one_step_kills(N_B, N_R, p), kills_blue_closed=one_step_kills(N_R, N_B, p),
               aimed_per_red=N_B / N_R, aimed_per_blue=N_R / N_B,
               die_red=1 - (1 - p / N_R) ** N_B, die_blue=1 - (1 - p / N_B) ** N_R)
    rng = rng_for(seed, 2)
    nn = 20000
    sR = rng.binomial(N_R, p, nn)
    sB = rng.binomial(N_B, p, nn)
    ch2["hits_blue_sim"] = float(sB.mean())        # 青が撃って当てた数（赤が受ける）
    ch2["hits_red_sim"] = float(sR.mean())         # 赤が撃って当てた数（青が受ける）
    kb = _distinct(sR, np.full(nn, N_B), rng)      # 倒れた青
    kr = _distinct(sB, np.full(nn, N_R), rng)      # 倒れた赤
    ch2["kills_blue_sim"], ch2["kills_red_sim"] = float(kb.mean()), float(kr.mean())
    ch2["kills_blue_sd"], ch2["kills_red_sd"] = float(kb.std(ddof=1)), float(kr.std(ddof=1))
    ch2["kills_blue_se"], ch2["kills_red_se"] = float(kb.std(ddof=1) / math.sqrt(nn)), float(kr.std(ddof=1) / math.sqrt(nn))
    ch2["ratio_die"] = ch2["die_blue"] / ch2["die_red"]
    # 狙われた本数を1人ずつ数える（赤・青それぞれ、兵1人あたりの平均）
    reps = 500
    aimed_r = np.zeros(N_R)
    aimed_b = np.zeros(N_B)
    for _ in range(reps):
        aimed_r += np.bincount(rng.integers(0, N_R, N_B), minlength=N_R)
        aimed_b += np.bincount(rng.integers(0, N_B, N_R), minlength=N_B)
    ch2["aimed_red_sim"] = float(aimed_r.mean() / reps)
    ch2["aimed_blue_sim"] = float(aimed_b.mean() / reps)
    res["ch2"] = ch2
    tick("2章")

    # ---- 3章: 青の腕前 k ----
    ch3 = dict(rows=[], k50=None)
    for k, br, tr_, d in k_scan("shoot", W_WIDE, K_LIST, seed + 10):
        ch3["rows"].append(dict(k=k, blue=br, tie=tr_, red=d["red"] / d["n"], rem_mean=d.get("rem_mean", 0.0),
                                red_rem=d.get("red_rem_mean"), turns_mean=d["turns_mean"], turns_median=d["turns_median"]))
    ch3["k50"] = k50_find("shoot", W_WIDE, seed + 20, n=N_TRIALS_SEARCH)
    ch3["theory_k50"] = (N_R / N_B) ** 2
    res["ch3"] = ch3
    tick("3章")

    # ---- 4章: 斬り合い ----
    rng = rng_for(seed, 4)
    R, B, t = duel_batch(np.full(n, N_R), N_B, Q_DUEL, 1.0, rng)
    ch4 = summarize(R, B, t)
    ch4["theory"] = lanchester_linear(N_R, N_B)
    ch4["mean_field"] = mean_field_remain("duel", N_R, N_B)
    win = np.where(R > 0, R, B)
    ch4["hist"] = {int(i): int(c) for i, c in enumerate(np.bincount(win, minlength=N_R + 1)) if c}
    ch4["rows"] = []
    for k, br, tr_, d in k_scan("duel", W_WIDE, K_DUEL, seed + 30):
        ch4["rows"].append(dict(k=k, blue=br, tie=tr_, rem_mean=d.get("rem_mean", 0.0), turns_mean=d["turns_mean"]))
    ch4["k50"] = k50_find("duel", W_WIDE, seed + 40, n=N_TRIALS_SEARCH, lo=1.0, hi=4.0)
    ch4["theory_k50"] = N_R / N_B
    res["ch4"] = ch4
    tick("4章")

    # ---- 5章: 狭い道 ----
    ch5 = dict(rows=[])
    for W in list(W_LIST) + [W_WIDE]:
        row = dict(W=W)
        for mode in ("shoot", "duel"):
            rng = rng_for(seed, 5, W, 0 if mode == "shoot" else 1)
            R, B, t = run_batch(mode, np.full(n, N_R), N_B, rng, W)
            d = summarize(R, B, t)
            row[mode] = d
            row[mode]["mean_field"] = mean_field_remain(mode, N_R, N_B, W=W)
            row[mode]["k50"] = k50_find(mode, W, seed + 50 + (0 if mode == "shoot" else 7), n=N_TRIALS_SEARCH,
                                        lo=1.0, hi=6.0)
        ch5["rows"].append(row)
        tick(f"5章 W={W}")
    res["ch5"] = ch5

    # ---- 6章: 相手を分ける ----
    allsplits = {**SPLITS, **SPLIT_EXTRA}
    ch6 = dict(rows=[], thresholds=[], duel_thresholds=[], twist=None)
    for name, gs in allsplits.items():
        st = split_stats("shoot", SPLIT_R, gs, seed + 60)
        st["name"] = name
        st["groups"] = list(gs)
        st["theory"] = math.sqrt(max(0.0, SPLIT_R ** 2 - sum(g * g for g in gs)))
        st["mean_field"] = mean_field_sequence("shoot", SPLIT_R, gs)
        ch6["rows"].append(st)
    tick("6章 勝率")
    for name, gs in allsplits.items():
        b, rb, ra, a_ = split_threshold("shoot", gs, seed + 70)
        ch6["thresholds"].append(dict(name=name, groups=list(gs), N=b, rate=rb, rate_below=ra, below=a_,
                                      theory=math.sqrt(sum(g * g for g in gs))))
        tick(f"6章 境目 {name} → {b}")
    # 斬り合いで分けたら（1次法則は分けても効かない）
    ch6["duel_rows"] = []
    for name, gs in SPLITS.items():
        st = split_stats("duel", SPLIT_R, gs, seed + 80)
        st["name"] = name
        ch6["duel_rows"].append(st)
        b, rb, ra, a_ = split_threshold("duel", gs, seed + 85)
        ch6["duel_thresholds"].append(dict(name=name, groups=list(gs), N=b, rate=rb, rate_below=ra, below=a_,
                                           theory=float(sum(gs))))
    tick("6章 斬り合いで分けた場合")
    # 勝率の曲線（赤の人数ごと）
    ch6["curve"] = []
    for R0 in CURVE_R:
        row = dict(R=R0)
        for name, gs in SPLITS.items():
            row[name] = split_stats("shoot", R0, gs, seed + 90, n=4000)["win"]
        ch6["curve"].append(row)
    res["ch6"] = ch6
    tick("6章 曲線")

    # ---- 小さい規模（ショートの数字・1人ずつ追う数え方・p 掃引）----
    res["sm"] = compute_small(seed)
    tick("小さい規模（100 vs 50）")

    # ---- 大きさを変える（青 10〜5000、赤は2倍）----
    chk = dict(n_rows=[])
    for nb in N_SWEEP:
        rng = rng_for(seed, 9, nb)
        R, B, t = shoot_batch(np.full(n, 2 * nb), nb, P_HIT, P_HIT, rng)
        d = summarize(R, B, t)
        chk["n_rows"].append(dict(nb=nb, nr=2 * nb, rem_mean=d["rem_mean"], rem_sd=d["rem_sd"],
                                  theory=lanchester_square(2 * nb, nb), blue=d["blue"],
                                  mean_field=mean_field_remain("shoot", 2 * nb, nb), turns_mean=d["turns_mean"]))
    res["chk"] = chk
    tick("大きさの掃引")

    # ---- 画面の見本 ----
    res["samples"] = compute_samples()
    tick("画面の見本")

    # ---- 別の乱数でやり直す（画面の数字が同じ丸めか）----
    res["again"] = compute_again(SEED_CHECK)
    tick("別の乱数")
    res["elapsed"] = time.time() - t0
    return res


def compute_again(seed):
    """画面に出す数字だけ、別の乱数でやり直す"""
    n = N_TRIALS
    out = {}
    R, B, t = shoot_batch(np.full(n, N_R), N_B, P_HIT, P_HIT, rng_for(seed, 1))
    out["ch1"] = summarize(R, B, t)
    out["k_rows"] = [dict(k=k, blue=b) for k, b, _, _ in k_scan("shoot", W_WIDE, K_LIST, seed + 10)]
    R, B, t = duel_batch(np.full(n, N_R), N_B, Q_DUEL, 1.0, rng_for(seed, 4))
    out["ch4"] = summarize(R, B, t)
    out["w_rows"] = []
    for W in list(W_LIST) + [W_WIDE]:
        row = dict(W=W)
        for mode in ("shoot", "duel"):
            R, B, t = run_batch(mode, np.full(n, N_R), N_B, rng_for(seed, 5, W, 0 if mode == "shoot" else 1), W)
            row[mode] = summarize(R, B, t)
        out["w_rows"].append(row)
    out["split_rows"] = [dict(name=nm, **split_stats("shoot", SPLIT_R, gs, seed + 60))
                         for nm, gs in {**SPLITS, **SPLIT_EXTRA}.items()]
    # 小さい規模（ショートの別乱数との照合）
    R, B, t = shoot_batch(np.full(n, SMALL_R), SMALL_B, P_HIT, P_HIT, rng_for(seed, 101))
    out["sm_ch1"] = summarize(R, B, t)
    r0, gs = SHORT_TWIST
    out["twist"] = dict(once=split_stats("shoot", r0, (sum(gs),), seed + 95),
                        split=split_stats("shoot", r0, gs, seed + 96))
    return out


def load(recompute=False):
    f = OUT / "data.json"
    if f.exists() and not recompute:
        res = json.loads(f.read_text(encoding="utf-8"))
        pr = res.get("params", {})
        if pr.get("P_HIT") == P_HIT and pr.get("N_TRIALS") == N_TRIALS and pr.get("N_R") == N_R:
            return res
    print("計算します（数十分かかります）…", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = compute()
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def refresh_samples():
    """画面の見本だけ作り直して data.json に入れる"""
    f = OUT / "data.json"
    res = json.loads(f.read_text(encoding="utf-8"))
    res["samples"] = compute_samples()
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


# ============================================================
# 5. 画面で使う関数（絵の担当が呼ぶ）
# ============================================================
def mean_path(res, key="traj_R"):
    """1章: 1万 vs 5千 の、ターンごとの平均の生き残り（key = traj_R / traj_B / traj_diff）"""
    return res["ch1"][key]


def sample_path(res, i=0):
    """画面の見本 1回の、ターンごとの [赤, 青] 生き残り（最初の [10000, 5000] を含む）"""
    return res["samples"]["main"][i]["path"]


def _typical(kind, res, start=1, count=1, tol_sd=0.3):
    """画面の見本の種を探す: 赤が勝ち、残りが全試行の中央値±tol_sd×SD 以内、ターン数も中央値付近"""
    if kind == "main":
        ref, fn = res["ch1"], sample_shoot
    elif kind == "duel":
        ref, fn = res["ch4"], sample_duel
    elif kind == "narrow":
        ref, fn = next(r for r in res["ch5"]["rows"] if r["W"] == SAMPLE_W)["shoot"], lambda s: sample_shoot(s, W=SAMPLE_W)
    else:
        ref, fn = None, None
    found, s = [], start
    while len(found) < count and s < start + 3000:
        if kind == "split3":
            r = sample_split(s)
            ref6 = next(x for x in res["ch6"]["rows"] if x["name"] == "3つ")
            ok = r["red_left"] > 0 and abs(r["red_left"] - ref6["rem_median"]) <= tol_sd * ref6["rem_sd"]
        else:
            r = fn(s)
            sd_t = max(1.0, (ref["turns_p90"] - ref["turns_p10"]) / 2.56)
            ok = (r["red_left"] > 0 and abs(r["red_left"] - ref["rem_median"]) <= tol_sd * ref["rem_sd"]
                  and abs(r["turns"] - ref["turns_median"]) <= max(1.0, 0.25 * sd_t))
        if ok:
            found.append(s)
        s += 1
    return found


def find_samples(res):
    return dict(main=_typical("main", res, count=3), duel=_typical("duel", res), narrow=_typical("narrow", res),
                split3=_typical("split3", res))


# ============================================================
# 6. 照合
# ============================================================
def se_diff(a, b):
    """2つの要約（rem_sd, n）の平均の差の標準誤差"""
    return math.hypot(a["rem_sd"] / math.sqrt(a["n"]), b["rem_sd"] / math.sqrt(b["n"]))


def check(res):
    ch1, ch2, ch3, ch4, ch5, ch6, chk, sm, ag, ss = (res[k] for k in
        ("ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "chk", "sm", "again", "samples"))
    checks = []
    sh = sm["ch1"]
    # ---------- 小さい規模（100 vs 50）: ショートの数字・1人ずつ追う数え方 ----------
    # (1) 1回の一斉射撃の期待値
    for s in sm["step"]:
        checks.append((f"1回の一斉射撃 {s['R']}人が{s['B']}人を撃つ: 速い数え方 vs 閉じた式", s["fast"], s["closed"], 4 * s["fast_se"]))
        if s["expl"] is not None:
            checks.append((f"1回の一斉射撃 {s['R']}人が{s['B']}人を撃つ: 1人ずつ vs 閉じた式", s["expl"], s["closed"], 4 * s["expl_se"]))
    # (2) 速い数え方（ここで使う一斉処理）と、1人ずつ追う数え方（100 vs 50）
    for e in sm["explicit"]:
        mode, W = e["mode"], e["W"]
        if mode == "shoot":
            ref = sh if W == W_WIDE else sm["w_small"]["shoot"]
        else:
            ref = sm["duel"] if W == W_WIDE else sm["w_small"]["duel"]
        tol = 4 * math.hypot(e["se"], ref["rem_sd"] / math.sqrt(ref["n"]))
        checks.append((f"1人ずつ追う vs 一斉処理（100 vs 50）: {'撃ち合い' if mode == 'shoot' else '斬り合い'} W={'広い' if W == W_WIDE else W} 残りの平均",
                       e["mean"], ref["rem_mean"], tol))
    # (3) ショートの数字（100 vs 50）
    checks += [
        ("ショート照合 100 vs 50 残りの平均 vs ショート（84.55±0.3）", sh["rem_mean"], SHORT_MEAN, 0.3),
        ("ショート照合 100 vs 50 残りのSD vs ショート（4.73±0.15）", sh["rem_sd"], SHORT_SD, 0.15),
        ("ショート照合 100 vs 50 別乱数の残りの平均 vs ショートの別乱数（84.53±0.3）", ag["sm_ch1"]["rem_mean"], SHORT_MEAN_2, 0.3),
        ("ショート照合 100 vs 50 残りの平均 vs 連続理論 86.6（離散は2人ほど少ない。±3）", sh["rem_mean"], sh["theory"], 3.0),
        ("ショート照合 100 vs 50 残りの平均 vs 平均場（±1.5）", sh["rem_mean"], sh["mean_field"], 1.5),
        ("ショート照合 100 vs 50 青が勝った回数 ≦ 3", float(sh["blue"]), 0.0, 3.0),
        ("ショート照合 互角の k ＝ 4（理論）±0.2", sm["k50"], sm["theory_k50"], 0.2),
        ("ショート照合 互角の k vs ショート 3.96（±0.1）", sm["k50"], SHORT_K50, 0.1),
    ]
    for row, sk in zip(sm["k_rows"], SHORT_K_WIN):
        checks.append((f"ショート照合 k={int(row['k'])} 50人側の勝率 vs ショート（±1.2pt）", row["blue"], sk, 0.012))
    tw = sm["twist"]
    checks += [
        ("ショートのおさらい: 80 vs 100 一度に 勝率 vs ショート 0.5%（±0.4pt）", tw["once"]["win"], SHORT_TWIST_SHOT[0], 0.004),
        ("ショートのおさらい: 80 vs 50+50 勝率 vs ショート 89%（±1.2pt）", tw["split"]["win"], SHORT_TWIST_SHOT[1], 0.012),
        ("ショートのおさらい: 80 vs 50+50 残り vs ショート 33.4（±0.6）", tw["split"]["rem_mean"], SHORT_TWIST_SHOT[2], 0.6),
        ("ショートのおさらい: 80 vs 50+50 勝率（整数%）が別乱数でも同じ（差≦1pt）", tw["split"]["win"], ag["twist"]["split"]["win"], 0.01),
    ]
    # p を変えても（100 vs 50）
    ps = {r["p"]: r for r in sm["p_rows"]}
    checks += [
        ("p 掃引: 0.02〜0.1 の残りの平均の幅 ≦ 4人（100 vs 50）", max(ps[x]["rem_mean"] for x in (0.02, 0.04, 0.07, 0.1)) - min(ps[x]["rem_mean"] for x in (0.02, 0.04, 0.07, 0.1)), 0.0, 4.0),
        ("p 掃引: p=0.01 の残りが理論 86.6 に近い（±1.2）", ps[0.01]["rem_mean"], lanchester_square(SMALL_R, SMALL_B), 1.2),
        ("p 掃引: pが小さいほど理論に近づく（0.1 < 0.04 < 0.01）", float(ps[0.1]["rem_mean"] < ps[0.04]["rem_mean"] < ps[0.01]["rem_mean"]), 1.0, 0),
    ]
    for x in (0.02, 0.04, 0.07, 0.1):
        checks.append((f"p 掃引: p={x} の互角の k ≒ 4（±0.3）", ps[x]["k50"], 4.0, 0.3))
    # 大きさを変える
    nrows = chk["n_rows"]
    checks.append(("大きさ: 青が25〜5000人でも 残り÷理論 が一定（最大と最小の差 ≦ 0.02）",
                   max(r["rem_mean"] / r["theory"] for r in nrows[1:]) - min(r["rem_mean"] / r["theory"] for r in nrows[1:]), 0.0, 0.02))
    for r in nrows:
        if r["nb"] >= 50:
            checks.append((f"大きさ: 青{r['nb']}人（赤{r['nr']}人）の残りの割合 ≒ 85%（±1pt）", r["rem_mean"] / r["nr"], 0.85, 0.01))
    checks.append(("大きさ: 大きいほどばらつき（SD÷平均）が小さい（青10人 > 青100人 > 青5000人）",
                   float(nrows[0]["rem_sd"] / nrows[0]["rem_mean"] > nrows[3]["rem_sd"] / nrows[3]["rem_mean"] > nrows[-1]["rem_sd"] / nrows[-1]["rem_mean"]), 1.0, 0))
    checks.append(("大きさ: ばらつきは √N に比例（SD÷平均 の比 青100人 ÷ 青5000人 ≒ √50＝7.07。±15%）",
                   (nrows[3]["rem_sd"] / nrows[3]["rem_mean"]) / (nrows[-1]["rem_sd"] / nrows[-1]["rem_mean"]), math.sqrt(50), 0.15 * math.sqrt(50)))

    # ---------- 主戦場（1万 vs 5千）----------
    # 1章
    th1 = ch1["theory"]
    checks += [
        ("1章 連続理論 √(10000²−5000²)＝8660", th1, 8660.25, 0.01),
        ("1章 残りの割合 ≒ 100 vs 50 のときの 84.55%（規模によらない。±0.5pt）", ch1["rem_mean"] / N_R, SHORT_MEAN / 100, 0.005),
        ("1章 残りの平均 vs 連続理論（離散は約2%少ない。±3%）", ch1["rem_mean"], th1, 0.03 * th1),
        ("1章 離散の残りは理論より少ない", float(ch1["rem_mean"] < th1), 1.0, 0),
        ("1章 残りの平均 vs 平均場（期待値の漸化式。±1%）", ch1["rem_mean"], ch1["mean_field"], 0.01 * ch1["mean_field"]),
        ("1章 残りのSD vs ショートのSD×√100（100 vs 50 の 4.73 を √(N比) 倍。±10%）", ch1["rem_sd"], SHORT_SD * math.sqrt(N_R / SMALL_R), 0.10 * SHORT_SD * math.sqrt(N_R / SMALL_R)),
        ("1章 青が勝った回数 ≦ 3（1万回で）", float(ch1["blue"]), 0.0, 3.0),
        ("1章 引き分けの回数 ≦ 3", float(ch1["tie"]), 0.0, 3.0),
        ("1章 3回の1万回の平均の最大差（標準誤差の差×4 以内）",
         max(r["rem_mean"] for r in ch1["runs"]) - min(r["rem_mean"] for r in ch1["runs"]), 0.0, 4 * math.sqrt(2) * ch1["rem_sd"] / math.sqrt(ch1["n"])),
        ("1章 画面の平均（百の位に丸め）が、別乱数でも同じ", round(ch1["rem_mean"], -2), round(ag["ch1"]["rem_mean"], -2), 0),
        ("1章 平均が別乱数でも近い（差 ≦ 標準誤差の差×4）", ch1["rem_mean"], ag["ch1"]["rem_mean"], 4 * se_diff(ch1, ag["ch1"])),
        ("1章 画面の中央値（百の位に丸め）が、別乱数でも同じ", round(ch1["rem_median"], -2), round(ag["ch1"]["rem_median"], -2), 0),
        ("1章 ターン数の中央値が別乱数でも同じ", ch1["turns_median"], ag["ch1"]["turns_median"], 1),
    ]
    for i, r in enumerate(ch1["runs"]):
        checks.append((f"1章 種を変えた{i + 1}回目（seed={r['seed']}）の平均が同じ（標準誤差の差×4 以内）", r["rem_mean"], ch1["rem_mean"], 4 * se_diff(r, ch1)))
    # R²−B² の保存（理論 N_R²−N_B² ＝ 7.5e7）: 最初の数ターンで保たれる
    cons = float(N_R ** 2 - N_B ** 2)
    checks.append(("1章 R²−B² が3ターン目でも 7.5×10⁷ の±3% 以内（保存量。平均）", ch1["traj_diff"][3], cons, 0.03 * cons))
    # 2章
    checks += [
        ("2章 赤が当てる本数の期待 10000p＝400", ch2["hits_red_sim"], ch2["hits_red"], 0.6),
        ("2章 青が当てる本数の期待 5000p＝200", ch2["hits_blue_sim"], ch2["hits_blue"], 0.45),
        ("2章 狙われる本数 赤1人あたり 0.5", ch2["aimed_red_sim"], 0.5, 0.005),
        ("2章 狙われる本数 青1人あたり 2.0", ch2["aimed_blue_sim"], 2.0, 0.02),
        ("2章 青1人の狙われ方 ÷ 赤1人の狙われ方 ＝ 4倍", ch2["aimed_blue_sim"] / ch2["aimed_red_sim"], 4.0, 0.1),
        ("2章 実際に倒れる青（重なりを除く）vs 閉じた式", ch2["kills_blue_sim"], ch2["kills_blue_closed"], 4 * ch2["kills_blue_se"]),
        ("2章 実際に倒れる赤 vs 閉じた式", ch2["kills_red_sim"], ch2["kills_red_closed"], 4 * ch2["kills_red_se"]),
        ("2章 倒れる青 ≒ 5000×(1−e^−0.08)＝384.4（閉じた式。指数の近似との差は0.05以内）", ch2["kills_blue_closed"], N_B * (1 - math.exp(-0.08)), 0.05),
        ("2章 倒れる赤 ≒ 10000×(1−e^−0.02)＝198.0（閉じた式）", ch2["kills_red_closed"], N_R * (1 - math.exp(-0.02)), 0.05),
    ]
    # 3章
    checks.append(("3章 互角の k ＝ 4（理論）±0.1", ch3["k50"], ch3["theory_k50"], 0.1))
    rows3 = {row["k"]: row for row in ch3["rows"]}
    for k in (1, 2, 3, 3.5):
        checks.append((f"3章 k={k:g} 青の勝率 ≦ 0.5%", rows3[k]["blue"], 0.0, 0.005))
    for k in (4.5, 5, 6):
        checks.append((f"3章 k={k:g} 青の勝率 ≧ 99.5%", rows3[k]["blue"], 1.0, 0.005))
    checks.append(("3章 k=4 青の勝率は 40〜60%（互角）", rows3[4]["blue"], 0.5, 0.1))
    for row, ar in zip(ch3["rows"], ag["k_rows"]):
        checks.append((f"3章 k={row['k']:g} 勝率（整数%）が別乱数でも同じ（差 ≦ 2pt。k=4 は二項分布のぶれ）", row["blue"], ar["blue"], 0.02))
    # 4章
    checks += [
        ("4章 斬り合い 1万 vs 5千 の残り vs 理論 N1−N2＝5000（k=1 は R−B が保存。±5）", ch4["rem_mean"], ch4["theory"], 5.0),
        ("4章 斬り合いの残り vs 平均場（±5）", ch4["rem_mean"], ch4["mean_field"], 5.0),
        ("4章 斬り合いで青が勝った回数 ≦ 3", float(ch4["blue"]), 0.0, 3.0),
        ("4章 互角の k ＝ 2（理論）±0.1", ch4["k50"], ch4["theory_k50"], 0.1),
        ("4章 画面の平均が別乱数でも近い（標準誤差の差×4 以内）", ch4["rem_mean"], ag["ch4"]["rem_mean"], 4 * se_diff(ch4, ag["ch4"])),
        ("4章 SD は撃ち合いの約2倍以上（斬り合いは運が効く）", float(ch4["rem_sd"] > 1.5 * ch1["rem_sd"]), 1.0, 0),
    ]
    rows4 = {r["k"]: r for r in ch4["rows"]}
    checks += [("4章 k=1.5 青の勝率 ≦ 0.5%", rows4[1.5]["blue"], 0.0, 0.005),
               ("4章 k=2.5 青の勝率 ≧ 99.5%", rows4[2.5]["blue"], 1.0, 0.005),
               ("4章 k=2 青の勝率は 35〜65%（互角）", rows4[2]["blue"], 0.5, 0.15)]
    # 5章（狭い道）
    wide = ch5["rows"][-1]
    narrow = ch5["rows"][0]
    assert narrow["W"] == SAMPLE_W
    checks += [
        (f"5章 W={SAMPLE_W} の撃ち合いの残り ≒ 1次法則 5000（終盤の端数で少し多い。±1%）", narrow["shoot"]["rem_mean"], 5000.0, 50.0),
        (f"5章 W={SAMPLE_W} の撃ち合いの互角の k ≒ 2（±0.2）", narrow["shoot"]["k50"], 2.0, 0.2),
        ("5章 広い野原の撃ち合いの互角の k ≒ 4（±0.2）", wide["shoot"]["k50"], 4.0, 0.2),
        (f"5章 斬り合いは道幅で残りが変わらない（W={SAMPLE_W} と広い野原の差が標準誤差の差×4 以内）", narrow["duel"]["rem_mean"], wide["duel"]["rem_mean"], 4 * se_diff(narrow["duel"], wide["duel"])),
        (f"5章 斬り合いの互角の k は W={SAMPLE_W} でも ≒ 2（±0.12）", narrow["duel"]["k50"], 2.0, 0.12),
        ("5章 道幅が狭いほど、撃ち合いの互角の k は小さい（W=50 < 1000 < 広い野原）",
         float(narrow["shoot"]["k50"] < next(r for r in ch5["rows"] if r["W"] == 1000)["shoot"]["k50"] < wide["shoot"]["k50"]), 1.0, 0),
        ("5章 撃ち合いの互角の k は W が大きいほど増える（隣どうし誤差0.05を許す）",
         float(all(a["shoot"]["k50"] <= b["shoot"]["k50"] + 0.05 for a, b in zip(ch5["rows"], ch5["rows"][1:]))), 1.0, 0),
        ("5章 撃ち合いの残りは W が大きいほど増える（幅50 < 3000 < 広い野原。おなじ人数でも広い方が有利）",
         float(narrow["shoot"]["rem_mean"] < next(r for r in ch5["rows"] if r["W"] == 3000)["shoot"]["rem_mean"] < wide["shoot"]["rem_mean"]), 1.0, 0),
        ("5章 広い野原の行が 1章と同じ（撃ち合い 平均の差が標準誤差の差×4 以内）", wide["shoot"]["rem_mean"], ch1["rem_mean"], 4 * se_diff(wide["shoot"], ch1)),
    ]
    for row, ar in zip(ch5["rows"], ag["w_rows"]):
        wl = "広い野原" if row["W"] == W_WIDE else row["W"]
        checks.append((f"5章 W={wl} 撃ち合いの平均が別乱数でも近い（標準誤差の差×4 以内）", row["shoot"]["rem_mean"], ar["shoot"]["rem_mean"], 4 * se_diff(row["shoot"], ar["shoot"])))
        checks.append((f"5章 W={wl} 斬り合いの平均が別乱数でも近い（標準誤差の差×4 以内）", row["duel"]["rem_mean"], ar["duel"]["rem_mean"], 4 * se_diff(row["duel"], ar["duel"])))
        checks.append((f"5章 W={wl} 撃ち合いの平均 vs 平均場（±1.5%）", row["shoot"]["rem_mean"], row["shoot"]["mean_field"], 0.015 * row["shoot"]["mean_field"]))
    # 6章
    byname = {r["name"]: r for r in ch6["rows"]}
    checks += [
        ("6章 7500 vs 1万が一度に来る: 7500人側の勝率 ≦ 0.5%", byname["一度に"]["win"], 0.0, 0.005),
        ("6章 7500 vs 3つ: 勝率 ≧ 99%", float(byname["3つ"]["win"] >= 0.99), 1.0, 0),
        ("6章 7500 vs 3つ: 残り vs 平均場（±3%）", byname["3つ"]["rem_mean"], byname["3つ"]["mean_field"], 0.03 * byname["3つ"]["mean_field"]),
        ("6章 分けるほど勝ちやすい（勝率 一度に < 2つ ≦ 3つ ≦ 4つ ≦ 5つ ≦ 10こ）",
         float(byname["一度に"]["win"] < byname["2つ"]["win"] <= byname["3つ"]["win"] <= byname["4つ"]["win"] <= byname["5つ"]["win"] <= byname["10こ"]["win"]), 1.0, 0),
        ("6章 分けるほど残りが増える（2つ < 3つ < 4つ < 5つ < 10こ）",
         float(byname["2つ"]["rem_mean"] < byname["3つ"]["rem_mean"] < byname["4つ"]["rem_mean"] < byname["5つ"]["rem_mean"] < byname["10こ"]["rem_mean"]), 1.0, 0),
    ]
    for nm in ("2つ", "3つ", "4つ", "5つ", "10こ"):
        r = byname[nm]
        checks.append((f"6章 7500 vs {nm}: 勝ったときの残り vs 平均場（±1%）", r["rem_mean"], r["mean_field"], 0.01 * r["mean_field"]))
        checks.append((f"6章 7500 vs {nm}: 勝ったときの残りは連続理論 √(7500²−ΣB²) より少ない（差の2乗を取るので、離散のズレが大きく見える）",
                       float(0.5 * r["theory"] < r["rem_mean"] < r["theory"]), 1.0, 0))
    th = {t["name"]: t for t in ch6["thresholds"]}
    checks.append(("6章 境目: 一度に来るなら 1万人（理論 10000。R＝B は対称で五分）±100", th["一度に"]["N"], 10000.0, 100.0))
    for nm in ("2つ", "3つ", "4つ", "5つ", "10こ"):
        mf = mean_field_threshold(th[nm]["groups"])
        checks.append((f"6章 境目: {nm} は平均場の境目 {mf} と一致（±(10人+0.3%)）", th[nm]["N"], float(mf), TH_TOL + 0.003 * mf))
        checks.append((f"6章 境目: {nm} は理論 {th[nm]['theory']:.0f} より多く必要（理論の1.00〜1.10倍。分ける回数が多いほど離散のズレが積もる）",
                       th[nm]["N"] / th[nm]["theory"], 1.05, 0.05))
    checks.append(("6章 境目が 一度に > 2つ > 3つ > 4つ > 5つ > 10こ",
                   float(th["一度に"]["N"] > th["2つ"]["N"] > th["3つ"]["N"] > th["4つ"]["N"] > th["5つ"]["N"] > th["10こ"]["N"]), 1.0, 0))
    for nm, t in th.items():
        checks.append((f"6章 境目 {nm}: その人数の勝率 ≧ 50% かつ {TH_TOL}人少ないと < 50%", float(t["rate"] >= 0.5 > t["rate_below"] and t["N"] - t["below"] <= TH_TOL), 1.0, 0))
    # 斬り合いで分けても変わらない
    dth = {t["name"]: t for t in ch6["duel_thresholds"]}
    for r in ch6["duel_rows"]:
        checks.append((f"6章 斬り合いで分ける（{r['name']}）: 7500 vs 1万 赤の勝率 ≦ 0.5%（分けても効かない）", r["win"], 0.0, 0.005))
    for nm, t in dth.items():
        checks.append((f"6章 斬り合いで分ける（{nm}）: 境目 ≒ 1万人（1次法則は R > ΣB）±300", t["N"], 10000.0, 300.0))
    checks.append(("6章 斬り合いの境目は、分け方でほとんど変わらない（最大と最小の差 ≦ 200人）",
                   max(t["N"] for t in dth.values()) - min(t["N"] for t in dth.values()), 0.0, 200.0))
    for r, ar in zip(ch6["rows"], ag["split_rows"]):
        checks.append((f"6章 {r['name']} 勝率（整数%）が別乱数でも同じ（差≦1.5pt）", r["win"], ar["win"], 0.015))
        if r["win"] > 0.05:
            checks.append((f"6章 {r['name']} 残りの平均が別乱数でも近い（標準誤差の差×4 以内）", r["rem_mean"], ar["rem_mean"],
                           4 * math.hypot(r["rem_sd"] / math.sqrt(r["n"] * r["win"]), ar["rem_sd"] / math.sqrt(ar["n"] * ar["win"]))))
    # 画面の見本（1回ぶんの戦い）が「ふつうの結果」か
    def typical(label, smp, ref, sd_t):
        checks.append((f"見本 {label}: 赤が勝ち、残りが中央値±0.5SD 以内", smp["red_left"], ref["rem_median"], 0.5 * ref["rem_sd"]))
        checks.append((f"見本 {label}: ターン数が中央値付近（±0.5SD または ±2）", smp["turns"], ref["turns_median"], max(2.0, 0.5 * sd_t)))
        checks.append((f"見本 {label}: 青が全滅、赤が生き残る", float(smp["red_left"] > 0 and smp["path"][-1][1] == 0), 1.0, 0))
    sdt = lambda ref: (ref["turns_p90"] - ref["turns_p10"]) / 2.56
    for i, smp in enumerate(ss["main"]):
        typical(f"1万 vs 5千 撃ち合い {i + 1}回目（seed={smp['seed']}）", smp, ch1, sdt(ch1))
    typical(f"斬り合い野原（seed={ss['duel']['seed']}）", ss["duel"], ch4, sdt(ch4))
    typical(f"狭い道 幅{SAMPLE_W}（seed={ss['narrow']['seed']}）", ss["narrow"], narrow["shoot"], sdt(narrow["shoot"]))
    r3 = byname["3つ"]
    checks.append((f"見本 7500 vs 3つ（seed={ss['split3']['seed']}）: 赤が勝ち、残りが中央値±0.5SD 以内", ss["split3"]["red_left"], r3["rem_median"], 0.5 * r3["rem_sd"]))
    checks.append(("見本 7500 vs 3つ: 3組とも倒して終わる（最後の行で青0・組番号2）", float(ss["split3"]["path"][-1][1] == 0 and ss["split3"]["path"][-1][2] == 2), 1.0, 0))
    check_answers(checks)
    print(f"全部の照合 OK（{len(checks)}項目）")


# ============================================================
# 7. numbers.md
# ============================================================
def pc(x, d=0):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def n0(x):
    return f"{x:,.0f}"


def write_numbers(res):
    ch1, ch2, ch3, ch4, ch5, ch6, chk, sm, ag, ss = (res[k] for k in
        ("ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "chk", "sm", "again", "samples"))
    L = []
    a = L.append
    n = N_TRIALS
    ns = N_TRIALS_SEARCH
    sh = sm["ch1"]
    a("# 合戦ロング（ランチェスター）数字一覧 — 赤1万人 vs 青5千人（v2）")
    a("")
    a(f"自動生成（sims/kassen-long.py --numbers）。**手で編集しない。** 計算 {res['elapsed']:.0f}秒。100 vs 50 版は numbers.v1.md。")
    a(f"撃ち合いは p={P_HIT}（ショートと同じ）。斬り合いは q={Q_DUEL}（腕前が同じなら、1人が1ターンに相手を倒す確率が p と同じになる強さ）。")
    a(f"特に断らない限り、各条件 {n:,} 回。引き分け（同じターンに両軍全滅）は勝ちに数えない。勝った側の残りは「勝った側」のみで平均。")
    a(f"**n を {ns:,} に下げたもの**（規模が大きく、ばらつきが小さいので十分。値の精度はそのぶん落ちる）: "
      "3章の互角の k／4章の互角の k／5章の各幅の互角の k／6章の境目の二分探索（撃ち合い・斬り合い）。"
      f"6章の勝率曲線は各 4,000 回。それ以外（1章・2章・3章の各k・4章・5章の残り・6章の勝率・ショート照合・p 掃引・大きさの掃引）は {n:,} 回。")
    a("画面の見本は足軽1人の絵＝100人（1万人＝絵100人、5千人＝絵50人）。")
    a("")
    a("## 台本の判断材料: 理論 8660 と実際 8478 のズレ")
    a("")
    a(f"- 連続の理論 √(10000²−5000²) ＝ {ch1['theory']:.0f}。{n:,}回の平均は **{ch1['rem_mean']:.0f}**（差 {ch1['theory'] - ch1['rem_mean']:.0f}人、{(ch1['theory'] - ch1['rem_mean']) / ch1['theory'] * 100:.1f}%）。"
      f"割合で見ると 100 vs 50 のとき {sh['rem_mean']:.2f}% → 1万 vs 5千 で {ch1['rem_mean'] / N_R * 100:.2f}%（**規模によらず約85%**）。")
    a("- **理由（1行）**: 理論は「人数が連続的に減る」近似で、現実は①同じ兵に2本当たる無駄玉（倒れた数は当たった数より少ない）"
      "②1ターンごとの運のぶれが終盤の少人数で効く ③同時処理で、倒れる兵もその回は撃つ、の3つで少しずつ損をするため。")
    p001 = next(r["rem_mean"] for r in sm["p_rows"] if r["p"] == 0.01)
    p01 = next(r["rem_mean"] for r in sm["p_rows"] if r["p"] == 0.1)
    a(f"- 裏づけ（100 vs 50 で p を変える）: p を小さくすると理論に寄る。p=0.01 で平均 {p001:.1f}（理論 86.6）、p=0.1 で {p01:.1f}。"
      f"1万 vs 5千 の平均場（ばらつきなしで期待値だけを追った計算）は {ch1['mean_field']:.0f}。")
    a(f"- 台本での言い方の案: 「計算では約8,660人。実際にやると約8,500人（平均{ch1['rem_mean']:.0f}）。ほぼ式どおり」。ズレそのものは主張にしない（結論は『2乗で効く』で変わらない）。")
    a("")
    a("## 1章: 赤1万人 vs 青5千人の撃ち合い")
    a("")
    a(f"| 項目 | 値 |\n|---|---|\n| 勝った側の残り 平均 | **{ch1['rem_mean']:.1f}** 人 |\n| 中央値 | {ch1['rem_median']:.0f} 人 |\n"
      f"| 標準偏差 | {ch1['rem_sd']:.1f} |\n| 5%点〜95%点 | {ch1['rem_p5']:.0f}〜{ch1['rem_p95']:.0f} 人 |\n"
      f"| 最小〜最大 | {ch1['rem_min']}〜{ch1['rem_max']} 人 |\n| 赤（1万人）が勝った回数 | {ch1['red']:,} / {n:,} |\n"
      f"| **青（5千人）が勝った回数** | **{ch1['blue']}** / {n:,}（引き分け {ch1['tie']}） |\n"
      f"| 連続理論 √(10000²−5000²) | {ch1['theory']:.0f} 人 |\n| 平均場（期待値だけの計算） | {ch1['mean_field']:.0f} 人 |\n"
      f"| 決着までのターン数 | 平均 {ch1['turns_mean']:.1f}、中央値 {ch1['turns_median']:.0f}、10%点〜90%点 {ch1['turns_p10']:.0f}〜{ch1['turns_p90']:.0f}、最小〜最大 {min(int(k) for k in ch1['turn_hist'])}〜{ch1['turns_max']} |")
    a("")
    a("勝った側の残り人数の分布（50人ごとの階級: 回数）:")
    a("")
    bins = {}
    for k, v in ch1["hist"].items():
        b = int(k) // 50 * 50
        bins[b] = bins.get(b, 0) + v
    a("`" + ", ".join(f"{b}〜{b + 49}:{v}" for b, v in sorted(bins.items())) + "`")
    a("")
    a("**種を変えた3回（各1万回）**（「偶然ではない」用）:")
    a("")
    a("| 回 | 種 | 残りの平均 | 中央値 | SD | 青が勝った回数 |\n|---|---|---|---|---|---|")
    for i, r in enumerate(ch1["runs"]):
        a(f"| {i + 1} | {r['seed']} | {r['rem_mean']:.1f} | {r['rem_median']:.0f} | {r['rem_sd']:.1f} | {r['blue']} |")
    a(f"| 別の乱数（照合） | {SEED_CHECK} | {ag['ch1']['rem_mean']:.1f} | {ag['ch1']['rem_median']:.0f} | {ag['ch1']['rem_sd']:.1f} | {ag['ch1']['blue']} |")
    a("")
    a("画面の見本（1回ぶんの戦い。種 → 赤の残り・ターン数。全試行の中央値は "
      f"{ch1['rem_median']:.0f}人・{ch1['turns_median']:.0f}ターン、SD {ch1['rem_sd']:.0f}人）: " +
      "、".join(f"seed={s['seed']}: {s['red_left']}人・{s['turns']}ターン" for s in ss["main"]))
    a("")
    a("1ターンごとの平均の生き残り（ターン0〜、赤／青／R²−B²）。R²−B² は理論では 7.5×10⁷ のまま動かない（2次法則の保存量）。終盤は片方が0になるので崩れる:")
    a("")
    a("| ターン | 赤 | 青 | R²−B² |\n|---|---|---|---|")
    for t in range(0, min(len(ch1["traj_R"]), 21)):
        a(f"| {t} | {ch1['traj_R'][t]:.0f} | {ch1['traj_B'][t]:.0f} | {ch1['traj_diff'][t]:.3g} |")
    a("")
    a("## 2章: なぜ2乗か（最初の一斉射撃）")
    a("")
    a(f"| 項目 | 赤（1万人） | 青（5千人） |\n|---|---|---|\n| 1回で当てる本数の期待（人数×p） | {ch2['hits_red']:.0f}（10000p） | {ch2['hits_blue']:.0f}（5000p） |\n"
      f"| **1回の一斉射撃で倒れる人数**（重なりを除く。閉じた式） | **青が {ch2['kills_blue_closed']:.1f} 人倒れる** | **赤が {ch2['kills_red_closed']:.1f} 人倒れる** |\n"
      f"| 同（シミュレーション 2万回。平均±SD） | 青が {ch2['kills_blue_sim']:.1f}±{ch2['kills_blue_sd']:.1f} 人 | 赤が {ch2['kills_red_sim']:.1f}±{ch2['kills_red_sd']:.1f} 人 |\n"
      f"| 兵1人あたりが狙われる本数 | **{ch2['aimed_per_red']:.1f}本**（青5千本÷赤1万人） | **{ch2['aimed_per_blue']:.1f}本**（赤1万本÷青5千人） |\n"
      f"| 同（シミュレーション） | {ch2['aimed_red_sim']:.3f} | {ch2['aimed_blue_sim']:.3f} |\n"
      f"| 兵1人が最初の1回で倒れる確率 | {pc(ch2['die_red'], 2)} | {pc(ch2['die_blue'], 2)} |\n"
      f"| 当たった本数 − 実際に倒れた人数（同じ兵に重なった無駄玉） | 赤の矢 {ch2['hits_red'] - ch2['kills_blue_closed']:.1f} 本ぶん | 青の矢 {ch2['hits_blue'] - ch2['kills_red_closed']:.1f} 本ぶん |")
    a("")
    a(f"- 青1人は赤1人の **{ch2['aimed_per_blue'] / ch2['aimed_per_red']:.0f}倍** 狙われる（狙われる本数）。倒れる確率でも {ch2['ratio_die']:.2f}倍。")
    a(f"- 赤は1回で青を約{ch2['kills_blue_closed']:.0f}人、青は赤を約{ch2['kills_red_closed']:.0f}人倒す → 倒す数の比 ≒ {ch2['kills_blue_closed'] / ch2['kills_red_closed']:.2f}。")
    a(f"  倒す数は自分の人数に比例（1万:5千＝2:1）。でも軍全体に対する割合で見ると、青は1回で {pc(ch2['die_blue'], 1)}、赤は {pc(ch2['die_red'], 1)} を失う（約4倍）。"
      "人数が少ないほど1人に矢が集中する ＝ 倒す数（比2）と、集中の度合い（比2）が掛け算になる。これが2乗の正体。")
    a("")
    a("## 3章: 青（5千人）の腕前 k 倍（撃ち合い）")
    a("")
    a("規模が大きいと、勝率は4倍を境に崖のように変わる（3.5倍で0%、4倍でほぼ半々、4.5倍で100%）。")
    a("")
    a("| k | 青の勝率 | 引き分け | 赤の勝率 | 勝った側の残り 平均 | ターン数 平均 | 別乱数の勝率 |\n|---|---|---|---|---|---|---|")
    for row, ar in zip(ch3["rows"], ag["k_rows"]):
        a(f"| {row['k']:g} | {pc(row['blue'], 2)} | {pc(row['tie'], 2)} | {pc(row['red'], 2)} | {row['rem_mean']:.0f} | {row['turns_mean']:.1f} | {pc(ar['blue'], 1)} |")
    a("")
    a(f"- 勝率 50% になる k = **{ch3['k50']:.2f}**（理論 {ch3['theory_k50']:.0f}。n={ns:,}。100 vs 50 のとき {sm['k50']:.2f}、ショートは {SHORT_K50}）")
    a("- 100 vs 50 での k ごとの勝率（ショートの数字との照合。ショートの勝率を括弧内）: " +
      "、".join(f"k={int(r['k'])}: {pc(r['blue'], 1)}（{pc(sk, 1)}）" for r, sk in zip(sm["k_rows"], SHORT_K_WIN)))
    a("")
    a("## 4章: 刀の1対1（1次法則）")
    a("")
    a(f"| 項目 | 値 |\n|---|---|\n| 1万 vs 5千 勝った側の残り 平均 | **{ch4['rem_mean']:.0f}** 人（理論 {ch4['theory']:.0f}） |\n| 中央値 | {ch4['rem_median']:.0f} |\n"
      f"| SD | {ch4['rem_sd']:.0f} |\n| 5%点〜95%点 | {ch4['rem_p5']:.0f}〜{ch4['rem_p95']:.0f} |\n| 青が勝った回数 | {ch4['blue']} / {n:,} |\n"
      f"| ターン数 | 平均 {ch4['turns_mean']:.0f}、中央値 {ch4['turns_median']:.0f}、10〜90%点 {ch4['turns_p10']:.0f}〜{ch4['turns_p90']:.0f} |\n"
      f"| 平均場 | {ch4['mean_field']:.0f} |")
    a("")
    a("青の腕前 k 倍:")
    a("")
    a("| k | 青の勝率 | 勝った側の残り 平均 | ターン数 平均 |\n|---|---|---|---|")
    for r in ch4["rows"]:
        a(f"| {r['k']:g} | {pc(r['blue'], 1)} | {r['rem_mean']:.0f} | {r['turns_mean']:.0f} |")
    a("")
    a(f"- 勝率 50% になる k = **{ch4['k50']:.2f}**（理論 {ch4['theory_k50']:.0f}。n={ns:,}）。撃ち合いの {ch3['k50']:.1f} より小さい。")
    a(f"- 残りのばらつきが大きい: 斬り合い SD {ch4['rem_sd']:.0f} ／ 撃ち合い SD {ch1['rem_sd']:.0f}（運の効きが違う）。")
    a("")
    a("## 5章: 狭い道（前線の幅 W。両軍とも W 人までしか戦えない）。台本で使うのは **幅50人**")
    a("")
    a("1万 vs 5千:")
    a("")
    a("| 幅 W | 撃ち合い 残り平均 | SD | 青の勝ち | 平均場 | ターン数 平均 | 斬り合い 残り平均 | SD | 青の勝ち | ターン数 平均 |\n|---|---|---|---|---|---|---|---|---|---|")
    for row in ch5["rows"]:
        s, d = row["shoot"], row["duel"]
        wl = "広い野原" if row["W"] == W_WIDE else f"{row['W']}人"
        a(f"| {wl} | {s['rem_mean']:.0f} | {s['rem_sd']:.0f} | {s['blue']} | {s['mean_field']:.0f} | {s['turns_mean']:.0f} | {d['rem_mean']:.0f} | {d['rem_sd']:.0f} | {d['blue']} | {d['turns_mean']:.0f} |")
    a("")
    a(f"5千人側が勝つ（勝率50%）のに必要な腕前 k（n={ns:,}）:")
    a("")
    a("| 幅 W | 撃ち合い | 斬り合い |\n|---|---|---|")
    for row in ch5["rows"]:
        wl = "広い野原" if row["W"] == W_WIDE else f"{row['W']}人"
        a(f"| {wl} | {row['shoot']['k50']:.2f} | {row['duel']['k50']:.2f} |")
    a("")
    a("- 撃ち合いは道が狭いほど 1次法則（残り N1−N2＝5000、必要な k=2）に近づく。斬り合いは道幅を変えても残りも k も変わらない（時間だけ延びる）。")
    a("")
    a("## 6章: 相手を分ける")
    a("")
    a(f"赤 {SPLIT_R:,}人 vs 青1万人（撃ち合い）:")
    a("")
    a("| 青の来かた | 赤の勝率 | 勝ったときの残り 平均 | 中央値 | SD | 理論 √(7500²−Σ青²) | 平均場 | ターン数 平均 | 負けた組 |\n|---|---|---|---|---|---|---|---|---|")
    for r in ch6["rows"]:
        a(f"| {SPLIT_LABEL[r['name']]} | {pc(r['win'], 1)} | {r['rem_mean']:.0f} | {r['rem_median']:.0f} | {r['rem_sd']:.0f} | {r['theory']:.0f} | {r['mean_field']:.0f} | {r['turns_mean']:.0f} | {r['lost_at']} |")
    a("")
    a(f"赤が何人いれば勝率50%以上になるか（青1万人の来かた別。撃ち合い。二分探索 {TH_TOL}人単位・n={ns:,}。台本では百の位に丸める）:")
    a("")
    a("| 青の来かた | 境目の人数 | その勝率 | 少ない側（境目−10人以内）の人数と勝率 | 理論 √(Σ青²) |\n|---|---|---|---|---|")
    for t in ch6["thresholds"]:
        a(f"| {SPLIT_LABEL[t['name']]} | **{t['N']:,}人**（百の位で {round(t['N'], -2):,}） | {pc(t['rate'], 1)} | {t['below']:,}人: {pc(t['rate_below'], 1)} | {t['theory']:.0f} |")
    a("")
    a("赤の人数ごとの勝率（各4000回）:")
    a("")
    a("| 赤の人数 | " + " | ".join(SPLIT_LABEL[k] for k in SPLITS) + " |\n|---|" + "---|" * len(SPLITS))
    for r in ch6["curve"]:
        a(f"| {r['R']:,} | " + " | ".join(pc(r[nm], 1) for nm in SPLITS) + " |")
    a("")
    a("斬り合い（1次法則）で分けたら: 分けても効かない（線形は R − B の足し算なので、順に来ても同じ。境目はどれも 1万人 ＝ 青の合計）:")
    a("")
    a(f"| 青の来かた | 赤{SPLIT_R:,}人の勝率 | 勝ったときの残り | 境目の人数（勝率50%、n={ns:,}） | その勝率 |\n|---|---|---|---|---|")
    dth = {t["name"]: t for t in ch6["duel_thresholds"]}
    for r in ch6["duel_rows"]:
        t = dth[r["name"]]
        a(f"| {SPLIT_LABEL[r['name']]} | {pc(r['win'], 1)} | {r['rem_mean']:.0f} | {t['N']:,}人 | {pc(t['rate'], 1)} |")
    tw = sm["twist"]
    a("")
    a("**ショートのおさらい（80人 vs 100人。100人規模のまま）**:")
    a("")
    a(f"- 一度に来る: 80人側の勝率 {pc(tw['once']['win'], 2)}（ショート {pc(SHORT_TWIST_SHOT[0], 1)}）")
    a(f"- 50人ずつ2つに分かれて順に来る: 80人側の勝率 **{pc(tw['split']['win'], 1)}**（ショート {pc(SHORT_TWIST_SHOT[1])}）、勝ったときの残り 平均 **{tw['split']['rem_mean']:.1f}人**"
      f"（ショート {SHORT_TWIST_SHOT[2]}、理論 √(80²−50²−50²)＝{tw['theory']:.1f}）")
    a(f"- 別乱数: 勝率 {pc(ag['twist']['split']['win'], 1)}、残り {ag['twist']['split']['rem_mean']:.1f}人")
    a("")
    a("## 7章: ターン数（早送りの設計）")
    a("")
    a("| 条件 | ターン数 平均 | 中央値 | 10%点〜90%点 |\n|---|---|---|---|")
    a(f"| 撃ち合い 1万 vs 5千（広い野原） | {ch1['turns_mean']:.1f} | {ch1['turns_median']:.0f} | {ch1['turns_p10']:.0f}〜{ch1['turns_p90']:.0f} |")
    a(f"| 斬り合い 1万 vs 5千（広い野原） | {ch4['turns_mean']:.0f} | {ch4['turns_median']:.0f} | {ch4['turns_p10']:.0f}〜{ch4['turns_p90']:.0f} |")
    for row in ch5["rows"][:-1]:
        s, d = row["shoot"], row["duel"]
        a(f"| 撃ち合い W={row['W']} | {s['turns_mean']:.0f} | {s['turns_median']:.0f} | {s['turns_p10']:.0f}〜{s['turns_p90']:.0f} |")
        a(f"| 斬り合い W={row['W']} | {d['turns_mean']:.0f} | {d['turns_median']:.0f} | {d['turns_p10']:.0f}〜{d['turns_p90']:.0f} |")
    for r in ch6["rows"]:
        a(f"| 撃ち合い {SPLIT_R:,} vs 1万（{SPLIT_LABEL[r['name']]}。全部の組の合計） | {r['turns_mean']:.1f} | {r['turns_median']:.0f} | {r['turns_p10']:.0f}〜{r['turns_p90']:.0f} |")
    a("")
    a("画面の見本（1回ぶんの戦い。data.json の samples に1ターンごとの人数あり）:")
    a("")
    a("| 見本 | 種 | 赤の残り | ターン数 |\n|---|---|---|---|")
    for i, s in enumerate(ss["main"]):
        a(f"| 撃ち合い 野原 {i + 1} | {s['seed']} | {s['red_left']} | {s['turns']} |")
    a(f"| 斬り合い 野原 | {ss['duel']['seed']} | {ss['duel']['red_left']} | {ss['duel']['turns']} |")
    a(f"| 撃ち合い 狭い道 幅{ss['narrow']['W']} | {ss['narrow']['seed']} | {ss['narrow']['red_left']} | {ss['narrow']['turns']} |")
    a(f"| 撃ち合い 7500 vs 3つ | {ss['split3']['seed']} | {ss['split3']['red_left']} | {ss['split3']['turns']}（組の切り替えを除く） |")
    a("")
    a("## 照合（台本には出さない・信用の裏づけ）")
    a("")
    a("**以下は小さい規模（100 vs 50）のまま。** 規模によらない性質の照合（1万人を1人ずつ追うと遅すぎるため）。")
    a("")
    a("p を変えても（100 vs 50 の撃ち合い）:")
    a("")
    a("| p | 残り平均 | 中央値 | SD | 青の勝ち | ターン数 平均 | 平均場 | 互角の k |\n|---|---|---|---|---|---|---|---|")
    for r in sm["p_rows"]:
        kk = "—" if r["k50"] is None else f"{r['k50']:.2f}"
        a(f"| {r['p']} | {r['rem_mean']:.1f} | {r['rem_median']:.0f} | {r['rem_sd']:.1f} | {r['blue']} | {r['turns_mean']:.1f} | {r['mean_field']:.1f} | {kk} |")
    a("")
    a("大きさを変えても（赤は青の2倍、p=0.04）。**残りの割合（残り÷赤）は規模によらず約85%。ゆらぎ（SD÷平均）は大きいほど小さくなる。理論との差（バイアス）は人数ではなく p で決まる**ので、大きくしても0にはならない:")
    a("")
    a("| 青 | 赤 | 残り平均 | 残り÷赤 | 理論 | 平均÷理論 | SD | SD÷平均 | 青の勝ち | ターン数 平均 |\n|---|---|---|---|---|---|---|---|---|---|")
    for r in chk["n_rows"]:
        a(f"| {r['nb']:,} | {r['nr']:,} | {r['rem_mean']:.1f} | {pc(r['rem_mean'] / r['nr'], 1)} | {r['theory']:.1f} | {r['rem_mean'] / r['theory']:.3f} | {r['rem_sd']:.2f} | {r['rem_sd'] / r['rem_mean']:.4f} | {r['blue']} | {r['turns_mean']:.1f} |")
    a("")
    a("1人ずつ追う数え方 vs 一斉処理（100 vs 50。勝った側の残りの平均）:")
    a("")
    a("| 型 | 幅 | 回数 | 1人ずつ（平均±標準誤差） | 一斉処理 1万回 |\n|---|---|---|---|---|")
    for e in sm["explicit"]:
        if e["mode"] == "shoot":
            ref = sh if e["W"] == W_WIDE else sm["w_small"]["shoot"]
        else:
            ref = sm["duel"] if e["W"] == W_WIDE else sm["w_small"]["duel"]
        a(f"| {'撃ち合い' if e['mode'] == 'shoot' else '斬り合い'} | {'広い' if e['W'] == W_WIDE else e['W']} | {e['n']} | {e['mean']:.2f}±{e['se']:.2f} | {ref['rem_mean']:.2f} |")
    a("")
    a("1回の一斉射撃で倒れる人数の期待値（R人がB人を撃つ。1人ずつは小さい規模のみ）:")
    a("")
    a("| R | B | 閉じた式 | 一斉処理 | 1人ずつ |\n|---|---|---|---|---|")
    for s in sm["step"]:
        ex = "—" if s["expl"] is None else f"{s['expl']:.3f}±{s['expl_se']:.3f}"
        a(f"| {s['R']:,} | {s['B']:,} | {s['closed']:.3f} | {s['fast']:.3f}±{s['fast_se']:.3f} | {ex} |")
    a("")
    a(f"ショートの数字との照合（100 vs 50、撃ち合い）: 残り 平均 {sh['rem_mean']:.2f}（ショート {SHORT_MEAN}）、SD {sh['rem_sd']:.2f}（ショート {SHORT_SD}）、"
      f"別乱数 {ag['sm_ch1']['rem_mean']:.2f}（ショート {SHORT_MEAN_2}）、互角の k {sm['k50']:.2f}（ショート {SHORT_K50}）。")
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "numbers.md"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("書き出し:", f)


# ============================================================
# モデルの CLI（--check / --numbers / --recompute / --seeds / --samples）。場面の CLI（--stills など）はファイルの最後
_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers", "--recompute", "--seeds", "--samples"))
if __name__ == "__main__" and _MODEL_CLI:
    args = sys.argv[1:]
    if "--seeds" in args:
        r = load()
        print("画面の見本の種（中央値±0.3SD の「ふつうの結果」）:", find_samples(r))
        raise SystemExit
    if "--samples" in args:
        res = refresh_samples()
        for i, s in enumerate(res["samples"]["main"]):
            print(f"main{i}: seed={s['seed']} 赤{s['red_left']} {s['turns']}ターン")
        raise SystemExit
    res = load(recompute="--recompute" in args)
    if "--numbers" not in args:
        check(res)
    if "--check" not in args:
        write_numbers(res)
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・音・CLI）。2026-10-08 追加。絵コンテ: research/kassen_long_storyboard.md
# モデル部分（上）は変えない。足軽・戦場・音の部品はショート sims/kassen-2bai.py からコピーして寸法を直した（ショート側は触らない）
# ####################################################################################################
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, shimmer, text,
                         text_width, thump, tick, whoosh, riser, beat, _t, SR)
from engine.note import INK, PENCIL, RED, MARKER, PAPER, pen_circle, pen_line, sticky
from engine.voice import split_reading

lf.use()
RES = load()                                         # data.json（モデルの結果。画面の数字はすべてここから）
VOICE_DIR = OUT / "voice"
FLAG_R, FLAG_B = "#d8434e", "#3a73c8"
LX0_, LY0_, LX1_, LY1_ = lf.LEFT
RX = 1050                                            # 右ページの書き出しの x


def figs(n):
    """人数 → 絵の足軽の数（1体＝100人。100減るごとに1体倒れる）"""
    return -(-int(n) // 100)


def fmt(n):
    return f"{int(round(n)):,}"


def round100(x):
    return int(round(x / 100.0)) * 100


# ============================================================
# 台本 → 時間割（ナレーションの文言は publish/kassen-long/script.md v3 のまま。読みの指定 {表記|よみ} だけ足した。
# 字幕が2行に収まらない文は、文言を変えずに2つの Line に分けた）
# ============================================================
CH_TITLES = ["1万人 vs 5千人", "1万回で確かめる", "1人に寄る", "では、腕前で補えるなら？", "では、刀で1対1なら？",
             "では、狭い道なら？", "では、相手を分けたら？", "ランチェスターの法則", "まとめ"]
(CH_OPEN, CH_MANY, CH_ONE, CH_SKILL, CH_SWORD, CH_ROAD, CH_SPLIT, CH_NAME, CH_END) = range(9)
SPEED = 1.0          # 声の速さ（バス回と同じ。数字の多い説明なので既定の 1.05 より遅く）
FAKE = "--fake-voice" in sys.argv                    # AivisSpeech なしで長さを見積もる確認用（無音）。本番では使わない


def _items():
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        L("c0_1", "野原に、赤い軍が{1万人|いちまんにん}。青い軍が{5千人|ごせんにん}。", pause=0.2),   # 字幕の折り返しのため2文に分けた（文言は同じ）
        L("c0_1b", "戦国時代のような{合戦|かっせん}です。", pause=0.5),
        L("c0_2", "絵の{足軽|あしがる}{1人|ひとり}が、{100人|ひゃくにん}ぶんです。", pause=0.5),
        L("c0_3", "武器は弓。合図で全員が{一斉|いっせい}に撃ち、倒れた分だけ減って、また撃ちます。", pause=0.4),
        L("c0_4", "腕前は同じ。どちらの矢も、当たる確率は同じ、{25本|にじゅうごほん}に{1本|いっぽん}です。", pause=0.5),
        L("c0_5", "一度だけ、戦わせてみます。", pause=0.1),
        G("g0", 10.5),
        L("c0_6", "青が全滅。赤が勝ちました。", pause=0.5),
        L("c0_7", "赤は、だいたい何人残るでしょう。", pause=1.0),
        L("c1_1", "兵の数が{2倍|にばい}なら、{2倍|にばい}強い。そう思えます。", pause=0.4),
        L("c1_2", "ふつうに考えると、こうなりそうです。", pause=0.4),
        L("c1_3", "腕前は同じだから、青の{5千人|ごせんにん}を倒すあいだに、赤も{5千人|ごせんにん}ほど倒される。", pause=0.4),
        L("c1_4", "だから、残るのは{5千人|ごせんにん}。", pause=0.8),
        L("c1_5", "確かめてみます。", pause=1.1),   # 章カードまで約0.5秒の間を足した（2026-10-09 初見チェック）
        C(CH_TITLES[1], id="ch1", gap=2.4),
        L("c2_1", "同じ{合戦|かっせん}を、{1万回|いちまんかい}繰り返します。{1回|いっかい}ごとに、赤が何人残ったかを記録します。", pause=0.3),
        G("g2", 12.0),
        L("c2_2", "{1万回|いちまんかい}の平均は、{約8,500人|やくはっせんごひゃくにん}。", pause=0.4),
        L("c2_3", "{5千人|ごせんにん}ではなく、{8,500人|はっせんごひゃくにん}。青の{5千人|ごせんにん}を倒すのに、"
                  "赤は{1,500人|せんごひゃくにん}しか失いませんでした。", pause=0.5),
        L("c2_4", "青が勝った回数は、{1万回|いちまんかい}中、ゼロ回です。", pause=0.6),
        L("c2_5", "偶然かもしれないので、乱数を変えて、もう{3回|さんかい}、{1万回|いちまんかい}ずつ。", pause=0.2),
        G("g2b", 2.6),
        L("c2_6", "どれも{約8,500人|やくはっせんごひゃくにん}。青は一度も勝てません。", pause=0.9),
        C(CH_TITLES[2], id="ch2", gap=1.6),
        L("c3_1", "なぜでしょう。最初の{一斉|いっせい}射撃に寄ってみます。", pause=0.5),
        L("c3_2", "赤は{1万人|いちまんにん}。矢は{1万本|いちまんぼん}。それが、青の{5千人|ごせんにん}に向かいます。", pause=1.2),
        L("c3_3", "青の兵{1人|ひとり}あたり、{2本|にほん}。", pause=0.8),
        L("c3_4", "青は{5千人|ごせんにん}。矢は{5千本|ごせんぼん}。それが、赤の{1万人|いちまんにん}に向かいます。", pause=1.2),
        L("c3_5", "赤の兵{1人|ひとり}あたり、{0.5本|れいてんごほん}。{2人|ふたり}で{1本|いっぽん}です。", pause=0.8),
        L("c3_6", "{2本|にほん}と、{0.5本|れいてんごほん}。青の兵は、赤の兵の{4倍|よんばい}、狙われています。", pause=2.0),
        L("c3_7", "兵が{2倍|にばい}いると、撃つ矢が{2倍|にばい}になる。", pause=0.2),
        L("c3_7b", "それだけではありません。", pause=0.3),
        L("c3_8", "相手の矢が、{2倍|にばい}の人数に散らばって、半分に薄まる。", pause=0.4),
        L("c3_9", "{2倍|にばい}かける{2倍|にばい}で、{4倍|よんばい}。", pause=0.6),
        L("c3_10", "だから、兵の数は、{2乗|にじょう}で効きます。", pause=0.8),
        L("c3_11", "この考え方で式を立てると、{残りは|のこりわ}{約8,700人|やくはっせんななひゃくにん}。", pause=0.6),
        L("c3_12", "実際にやると、平均{8,500人|はっせんごひゃくにん}ほど。ほぼ式どおりです。", pause=0.9),
        C(CH_TITLES[3], id="ch3", gap=1.6),
        L("c4_1", "では、少ない側が、腕前で補えるなら？", pause=0.4),
        L("c4_2", "青の腕前を上げます。矢が当たる確率を、赤の{2倍|にばい}にします。", pause=0.2),
        G("g4a", 3.4),
        L("c4_3", "{1万回|いちまんかい}やって、青の勝ちは、ゼロ回。", pause=0.4),
        L("c4_4", "{3倍|さんばい}でも、ゼロ回。{3.5倍|さんてんごばい}でも、まだゼロ回です。", pause=0.5),
        L("c4_5", "{4倍|よんばい}で、ちょうど半々。", pause=0.6),
        L("c4_6", "{4.5倍|よんてんごばい}にすると、今度は青が、{1万回|いちまんかい}すべて勝ちます。", pause=0.2),
        G("g4b", 3.4),
        L("c4_7a", "これだけの大軍になると、運が入りこむ余地は、ほとんどありません。", pause=0.25),
        L("c4_7b", "{4倍|よんばい}の手前では必ず負け、少し越えると必ず勝つ。", pause=0.6),
        L("c4_8", "人数が{2倍|にばい}なら、腕前は{4倍|よんばい}ないと追いつかない。", pause=0.2),
        L("c4_8b", "ここにも、{2倍|にばい}の{2乗|にじょう}が出てきます。", pause=0.9),
        C(CH_TITLES[4], id="ch4", gap=1.6),
        L("c5_1", "では、{弓|ゆみ}ではなく、刀で{斬り合う|きりあう}なら？", pause=0.4),
        L("c5_2", "{斬り合い|きりあい}は、向かい合った相手としか戦えません。後ろの兵は、自分の前の味方が倒れるまで、順番を待ちます。", pause=0.4),
        L("c5_3", "腕前は同じで、{1万回|いちまんかい}。", pause=0.1),
        G("g5", 6.0),
        L("c5_4", "赤の残りは、平均{5千人|ごせんにん}。最初の素朴な予想と、同じ数です。", pause=0.5),
        L("c5_5", "どれだけ兵がいても、{斬り合う|きりあう}のは{1対1|いったいいち}。矢が集中する、ということが起きません。", pause=0.4),
        L("c5_6", "だから、兵の数は{2乗|にじょう}ではなく、そのまま引き算で効きます。", pause=0.5),
        L("c5_7", "青の腕前を上げてみます。", pause=0.3),
        L("c5_7b", "{2倍|にばい}で、ちょうど半々。", pause=0.5),
        L("c5_8", "{互角|ごかく}に必要な腕前は、弓なら{4倍|よんばい}、刀なら{2倍|にばい}。武器が変わると、戦いの算数が変わります。", pause=0.9),
        C(CH_TITLES[5], id="ch5", gap=1.6),
        L("c6_1", "では、武器は弓のまま、戦う場所を狭い道にしたら？", pause=0.4),
        L("c6_2", "道の幅は、{50人|ごじゅうにん}ぶん。", pause=0.25),
        L("c6_2b", "ここでは、撃てるのは両軍とも先頭の{50人|ごじゅうにん}だけ、と決めます。後ろは順番を待ちます。",
          pause=0.2),
        G("g6", 5.0),
        L("c6_3", "赤の残りは、{約5千人|やくごせんにん}。野原の{8,500人|はっせんごひゃくにん}から、刀の{斬り合い|きりあい}と同じ数まで下がりました。",
          pause=0.5),
        L("c6_4", "{1万人|いちまんにん}いても、矢を撃てるのは先頭の{50人|ごじゅうにん}。青も{50人|ごじゅうにん}。先頭では、{50対50|ごじゅうたいごじゅう}です。",
          pause=0.5),
        L("c6_5", "青が{互角|ごかく}に戦うのに必要な腕前は、野原では{4倍|よんばい}。幅{50人|ごじゅうにん}の道なら、{約2倍|やくにばい}。", pause=0.2),
        G("g6b", 3.6),
        L("c6_6a", "少ない軍が、わざわざ狭い場所で待ち受ける。", pause=0.25),
        L("c6_6b", "歴史には、そういう話があります。理由の{1つ|ひとつ}は、この算数にあるのかもしれません。", pause=0.9),
        C(CH_TITLES[6], id="ch6", gap=1.6),
        L("c7_1", "では、少ない側が、相手を分けて戦えたら？", pause=0.4),
        L("c7_2a", "前のショート動画で確かめましたが、{80人|はちじゅうにん}でも、", pause=0.1),
        L("c7_2b", "相手の{100人|ひゃくにん}が{50人|ごじゅうにん}ずつ{2回|にかい}に分かれて来てくれれば、{約9割|やくきゅうわり}勝てます。",
          pause=0.6),
        L("c7_3", "今度は、赤の{1万人|いちまんにん}を分けて、順番に{来させます|こさせます}。青は何人いれば、半分以上勝てるでしょう。", pause=0.4),
        L("c7_4", "一度に来るなら、{1万人|いちまんにん}。同じ数で、やっと半々です。", pause=0.5),
        L("c7_5", "{2つ|ふたつ}に分かれて来るなら、{約7,200人|やくななせんにひゃくにん}。", pause=0.5),
        L("c7_6", "{3つ|みっつ}なら、{約5,900人|やくごせんきゅうひゃくにん}。", pause=0.5),
        L("c7_7", "{10個|じゅっこ}に分かれてくれるなら、{約3,400人|やくさんぜんよんひゃくにん}で足ります。", pause=0.6),
        L("c7_8", "ちなみに、刀の{斬り合い|きりあい}なら、分けても変わりません。引き算は、順番を変えても答えが同じだからです。", pause=0.5),
        L("c7_9", "大軍を分けて、{1つ|ひとつ}ずつ破る。これも、歴史に出てくる話です。", pause=0.9),
        C(CH_TITLES[7], id="ch7", gap=1.6),
        L("c8_1", "兵の数が{2乗|にじょう}で効く、という話には名前があります。ランチェスターの法則。", pause=0.6),
        L("c8_2", "{1916年|せんきゅうひゃくじゅうろくねん}にイギリスで書かれた、航空機と戦争についての本の中の式です。", pause=0.5),
        L("c8_3", "日本ではのちに、この考え方が会社どうしの競争にも当てはめられ、「ランチェスター戦略」と呼ばれています。", pause=0.6),
        L("c8_4", "ただし、これは単純化したモデルです。", pause=0.4),
        L("c8_5", "この野原の兵は、逃げないし、疲れないし、矢も尽きません。地形は道の幅だけ。士気も、補給も入っていません。", pause=0.5),
        L("c8_6", "実際の戦いの記録に当てはめた研究もありますが、合うものもあれば、合わないものもあります。", pause=0.9),
        C(CH_TITLES[8], id="ch8", gap=1.6),
        L("c9_1", "兵が{2倍|にばい}なら、{2倍|にばい}強い。そう思っていました。", pause=0.5),
        L("c9_2", "撃ち合いなら、{4倍|よんばい}。数の差は、思ったより大きく効きます。", pause=0.6),
        L("c9_3", "だから少ない側は、狭い場所を選び、相手を分ける工夫をしてきたのかもしれません。", pause=0.6),
        L("c9_4", "あなたなら、{5千人|ごせんにん}で{1万人|いちまんにん}に、どう挑みますか？", pause=1.2),
        L("c9_5", "このチャンネルでは、こんなふうにシミュレーションで確かめる動画を上げていきます。", pause=0.3),
        L("c9_6", "よければ、チャンネル登録と高評価をお願いします。", pause=0.0),
        G("g_end", 2.0),   # 言い終わって約2秒で終わる（バス回と同じ。終了画面の要素は重ねない）
    ]


@dataclass
class _FakeClip:
    """--fake-voice 用の無音（長さは字数からの見積もり）"""
    text: str
    spoken: str
    duration: float

    def samples(self):
        return np.zeros(16, np.float32)


def _fake_synth(text_, cache_dir, speed=SPEED, **kw):
    shown, spoken = split_reading(text_)
    # 実測（バス回 1.0 倍）で表示1字あたり約0.16秒。読みを指定した数字は読みのカナで数える
    n = len(shown) + sum(max(0, len(m.group(2)) * 0.55 - len(m.group(1)))
                         for m in __import__("re").finditer(r"\{([^{}|]*)\|([^{}]*)\}", text_))
    return _FakeClip(shown, spoken, 0.25 + n * 0.158 / speed)


# 字幕の折り返しを指定する文（自動だと「分か／れて」のように語の途中で折れるもの）。この動画の中だけで差し替える
_SUB_BREAK = {"相手の100人が50人ずつ2回に分かれて来てくれれば、約9割勝てます。": ["相手の100人が50人ずつ2回に分かれて", "来てくれれば、約9割勝てます。"]}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)


def _timeline():
    return lf.Timeline(_items(), VOICE_DIR, lead=3.0, synth=_fake_synth if FAKE else None)


tl = _timeline()
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


# ============================================================
# 小さな道具（バス回と同じ）
# ============================================================
def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def prog(t, t0, s, cps=9.0):
    return clamp01((t - t0) / lf.write_dur(s, cps))


def wr(ctx, s, x, y, size, color, t0, t, cps=9.0, align="left", alpha=1.0, bold=True):
    """t0 から手書きで書き進む文字（書き終わったらそのまま残る）"""
    if alpha <= 0.003:
        return
    lf.write_on(ctx, s, x, y, size, color, prog(t, t0, s, cps), align=align, alpha=alpha, bold=bold)


def grp(ctx, a, fn, *args):
    if a <= 0.003:
        return
    if a >= 0.997:
        fn(ctx, *args)
        return
    ctx.push_group()
    fn(ctx, *args)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def fit(s, size, maxw, bold=True):
    w = text_width(s, size, bold)
    return size if w <= maxw else max(26.0, size * maxw / w)


def out_fade(t, t1, d=0.35):
    """t1 から d 秒で 1→0"""
    return 1 - clamp01((t - t1) / d)


def ease_in_out(x):
    return ease(clamp01(x))


# ============================================================
# 絵: 足軽（ショート kassen-2bai.py の draw_soldier をコピー。刀を持つ形と、光る矢を足した）
# ============================================================
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
                 shadow=True, banner=True, weapon="bow"):
    """足軽1人。足元が (x, y)、k = 1単位の画面での大きさ（背の高さは約 104 単位）。face=+1 は右向き。
    draw: 弓なら 0（構え）〜1（めいっぱい引いた）、刀なら 0（振りかぶる）〜1（振り下ろす）、fall: 0（立つ）〜1（倒れた）"""
    tm = TEAM[team]
    g = clamp01(fall * 1.6)
    gray = g * 0.82
    c_armor, c_sleeve = _mix(tm["armor"], GRAY, gray), _mix(tm["sleeve"], GRAY, gray)
    c_flag = _mix(tm["flag"], GRAY, gray)
    c_skin, c_hat, c_leg = _mix(SKIN, GRAY, gray * 0.8), _mix(HAT, GRAY, gray), _mix(LEGC, GRAY, gray)
    c_wood = _mix(WOOD, GRAY, gray)
    iw = (1.5 + 0.8 * k) / k
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
    lean = (-0.045 * draw if weapon == "bow" else 0.06 * draw)
    ctx.rotate(-fall * 1.50 + (lean + sway) * (1 - fall))
    if fall > 0:
        ctx.translate(0, -3 * fall)
    if alpha < 1:
        ctx.push_group()
    d = draw
    if banner:
        wv = 2.6 * math.sin(flutter * 7.0) + 1.0
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.set_line_width(2.4)
        ctx.move_to(-8, -52)
        ctx.line_to(-8, -118)
        ctx.stroke()
        _poly(ctx, [(-8, -116), (-21 - wv * 0.7, -115), (-21 - wv, -92), (-8, -93)], c_flag, iw)
    sh = (3, -68)
    if weapon == "bow":
        pull = _lerp2((3, -45), (6.5, -73), d)
        elb = _lerp2((-1, -55), (-8, -74), d)
    else:
        pull = _lerp2((10, -84), (22, -60), d)       # 刀は両手で持つ
        elb = _lerp2((0, -80), (8, -62), d)
    _limb(ctx, [sh, elb, pull], 7.4, c_sleeve, iw)
    _limb(ctx, [(-2, -40), (-6, -21), (-8, -3), (-1, -2)], 9.4, c_leg, iw)
    _poly(ctx, [(-10, -38), (10, -38), (12, -70), (-9, -72)], c_armor, iw)
    _poly(ctx, [(-12, -37), (13, -37), (15, -26), (-14, -26)], _mix(tm["armor"], "#7a6a58", 0.18 + gray * 0.5), iw)
    ctx.set_source_rgba(*hexrgb(INK, 0.45))
    ctx.set_line_width(1.0)
    for yy in (-50, -58, -65):
        ctx.move_to(-9, yy)
        ctx.line_to(11, yy)
    ctx.stroke()
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
    _limb(ctx, [(3, -40), (8, -21), (10, -3), (18, -2)], 9.4, c_leg, iw)
    if weapon == "bow":
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
        if d > 0.25:
            ctx.set_line_width(1.8)
            ctx.move_to(px, by)
            ctx.line_to(bx + 11, by)
            ctx.stroke()
            _poly(ctx, [(bx + 11, by), (bx + 6, by - 2.6), (bx + 6, by + 2.6)], hexrgb(INK), 1.0)
        _dot(ctx, hand[0], hand[1], 3.2, c_skin, iw)
    else:
        hand = pull
        elb2 = _lerp2((8, -78), (14, -62), d)
        _limb(ctx, [sh, elb2, hand], 7.4, c_sleeve, iw)
        ang = lerp(-1.95, -0.15, ease(d))             # 刃の向き（上に振りかぶる → 前へ振り下ろす）
        ux, uy = math.cos(ang), math.sin(ang)
        hx, hy = hand
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*hexrgb(INK))           # 刃（墨の縁＋銀）
        ctx.set_line_width(4.6)
        ctx.move_to(hx + ux * 5, hy + uy * 5)
        ctx.line_to(hx + ux * 50, hy + uy * 50)
        ctx.stroke()
        ctx.set_source_rgba(*_mix("#eef2f6", GRAY, gray))
        ctx.set_line_width(2.4)
        ctx.move_to(hx + ux * 6, hy + uy * 6)
        ctx.line_to(hx + ux * 49, hy + uy * 49)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK))           # つかと、つば
        ctx.set_line_width(4.0)
        ctx.move_to(hx - ux * 7, hy - uy * 7)
        ctx.line_to(hx + ux * 4, hy + uy * 4)
        ctx.stroke()
        ctx.move_to(hx + ux * 4 - uy * 4, hy + uy * 4 + ux * 4)
        ctx.line_to(hx + ux * 4 + uy * 4, hy + uy * 4 - ux * 4)
        ctx.stroke()
        _dot(ctx, hx, hy, 3.2, c_skin, iw)
    _dot(ctx, pull[0], pull[1], 3.2, c_skin, iw)
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


# ---------- のぼり旗（ショートの Battle._noboris を、1本ずつ描ける関数にした） ----------
def nobori(ctx, xr, gy, s, ze, side, t, ph):
    """さおの根元 (xr, gy)。s は遠近の倍率、ze は足軽の大きさの倍率"""
    face = 1 if side == "R" else -1
    tm = TEAM[side]
    ht, bw, bh = 168 * s * ze, 30 * s * ze, 104 * s * ze
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(3.6 * ze ** 0.8)
    ctx.move_to(xr, gy)
    ctx.line_to(xr, gy - ht)
    ctx.stroke()
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


# ---------- 戦場の背景（ショートの draw_field。横の範囲 x0〜x1 を引数にした） ----------
def draw_field(ctx, y0, y1, ze, x0=112.0, x1=898.0):
    rng = np.random.default_rng(7)
    xs = np.linspace(x0, x1, 40)
    top = [(x, y0 + (8 * math.sin(x / 70) + float(rng.normal(0, 2.0))) * ze) for x in xs]
    bot = [(x, y1 + (6 * math.sin(x / 55 + 1) + float(rng.normal(0, 2.0))) * ze) for x in xs[::-1]]
    ctx.move_to(*top[0])
    for p in top[1:] + bot:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#dbe8c0", 0.8))
    ctx.fill()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    wd = x1 - x0
    for _ in range(80):
        x = x0 + float(rng.uniform(0.015, 0.985)) * wd
        v = float(rng.uniform(0.05, 0.98))
        y = y0 + 14 * ze + v * (y1 - y0 - 20 * ze)
        ctx.set_source_rgba(*hexrgb("#6f8f4a", 0.55))
        ctx.set_line_width(2.2 * ze)
        for dx, h in ((-5, 7), (0, 10), (5, 7)):
            ctx.move_to(x + dx * 0.4 * ze, y)
            ctx.line_to(x + dx * ze, y - h * ze)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.5))
    ctx.set_line_width(3 * ze ** 0.8)
    for u0, u1, h in ((0.005, 0.385, 34), (0.52, 0.995, 44)):
        a0, a1 = x0 + u0 * wd, x0 + u1 * wd
        ctx.move_to(a0, y0 - 2)
        for i in range(0, 21):
            u = i / 20
            ctx.line_to(a0 + (a1 - a0) * u, y0 - 2 - (h * math.sin(math.pi * u) ** 1.4 + 3 * math.sin(u * 17)) * ze)
        ctx.stroke()


# ---------- 矢（1本） ----------
def arrow_at(ctx, xs, ys, xe, ye, h, u, ze, glow=False, col=INK, alpha=0.8):
    """放物線の途中 u（0〜1）にある矢。glow は腕前を上げた側の、太く光る矢"""
    uu = min(1.0, u)
    x = xs + (xe - xs) * uu
    y = ys + (ye - ys) * uu - 4 * h * uu * (1 - uu)
    dxv = xe - xs
    dyv = (ye - ys) - 4 * h * (1 - 2 * uu)
    n = math.hypot(dxv, dyv) or 1.0
    ux, uy = dxv / n, dyv / n
    L = 20 * ze * (1.25 if glow else 1.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if glow:
        ctx.set_source_rgba(1.0, 0.85, 0.25, 0.55 * alpha)
        ctx.set_line_width(7.5 * ze)
        ctx.move_to(x - ux * L, y - uy * L)
        ctx.line_to(x, y)
        ctx.stroke()
    c = hexrgb(col)
    ctx.set_source_rgba(c[0], c[1], c[2], alpha)
    ctx.set_line_width((2.8 if glow else 1.7) * ze)
    ctx.move_to(x - ux * L, y - uy * L)
    ctx.line_to(x, y)
    ctx.stroke()
    hs = ze * (1.3 if glow else 1.0)
    ctx.move_to(x + ux * 3.5 * hs, y + uy * 3.5 * hs)
    ctx.line_to(x - ux * 3 * hs - uy * 3.2 * hs, y - uy * 3 * hs + ux * 3.2 * hs)
    ctx.line_to(x - ux * 3 * hs + uy * 3.2 * hs, y - uy * 3 * hs - ux * 3.2 * hs)
    ctx.close_path()
    ctx.fill()


def stuck_arrow(ctx, x, y, ze, ang=-0.9, col=INK, alpha=0.85):
    """地面に刺さった矢（矢羽根の側が上）"""
    c = hexrgb(col)
    ux, uy = math.cos(ang), math.sin(ang)
    L = 15 * ze
    ctx.set_source_rgba(c[0], c[1], c[2], alpha)
    ctx.set_line_width(2.2 * ze)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y)
    ctx.line_to(x + ux * L, y + uy * L)
    ctx.stroke()
    ctx.set_line_width(1.4 * ze)
    for s_ in (-1, 1):
        ctx.move_to(x + ux * L, y + uy * L)
        ctx.line_to(x + ux * (L - 5 * ze) + s_ * uy * 3.5 * ze, y + uy * (L - 5 * ze) - s_ * ux * 3.5 * ze)
    ctx.stroke()


# ============================================================
# 戦場（ショートの Geo・Battle をコピー。v1 の並び（legacy）は使わない。glow・死体を片づける時刻・見かけの差し替えを足した）
# ============================================================
class Geo:
    """兵の並びの寸法。s は「ショート v1（足軽の背の高さ 約72px）」に対する大きさの倍率"""

    def __init__(self, s, col_sp, row_y0, row_dy, depth=10):
        self.s = s
        self.k_near = 0.60 * s
        self.col_sp = col_sp
        self.row_y0 = row_y0
        self.row_dy = row_dy
        self.depth = depth

    def gy(self, row):
        return self.row_y0 + self.row_dy * row

    def persp(self, gy):
        return 0.74 + 0.26 * (gy - self.row_y0) / (self.row_dy * (self.depth - 1))

    def k(self, gy):
        return self.k_near * self.persp(gy)


GEO = Geo(s=1.2, col_sp=38.4, row_y0=602.0, row_dy=31.8, depth=10)   # ショートの冒頭と同じ並び
X_LEFT = 160.0
XF_R = X_LEFT + 9 * GEO.col_sp + 26 * GEO.s          # 赤軍の最前列（世界座標）
XF_B = XF_R + 175.0                                  # 青軍の最前列
WX0, WX1 = 142.0, 928.0                              # 草地の左右（世界座標）
VIEW_MAIN = (1.0, 1.0, -30.0, -132.0)                # 世界 → 左ページ（Zx, Zy, ox, oy）。列の足元は y 470〜756
VIEW_STRIP = (0.55, 0.55, 505 - 0.55 * 535, 772 - 0.55 * 602)   # 2章: 下の帯に縮めた戦場


def view_lerp(v0, v1, u):
    return tuple(lerp(a, b, u) for a, b in zip(v0, v1))


class Battle:
    """兵の並びと、一斉射撃の記録（誰が誰を狙って、当たったか）から、各時刻の絵を作る。
    groups: {名前: dict(side, n, cols, rows, xf, poles, march=(t0, t1, dx) or None, clear=時刻 or None)}
            clear: その時刻から、この組の倒れた兵を薄くして片づける（次の組が来る前に）
    fights: [dict(ga, gb, vols, times, flight=(a, b), roll, arc, dust, glow=("B",))]  vols は make_vols の記録
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
            assert len(slots) == c["n"], (g, len(slots))
            perm = rng.permutation(len(slots))
            for i in range(c["n"]):
                u = self.base[g] + i
                x, gy = slots[perm[i]]
                self.x0[u] = x + float(rng.uniform(-2.5, 2.5)) * geo.s
                self.gy[u] = gy + float(rng.uniform(-2.0, 2.0)) * geo.s
                self.gid[u] = gi
                self.face[u] = face
                self.team[u] = c["side"]
        self.gnames = list(groups)
        self.k = np.array([geo.k(g) for g in self.gy])
        self.order = np.argsort(self.gy, kind="stable")
        rel, arr, sxw, syw, exw, eyw, hit, hgt, shooter, target, glow = [], [], [], [], [], [], [], [], [], [], []
        self.volley_land = []
        dust_p = []
        for f in fights:
            ga, gb = f["ga"], f["gb"]
            fa, fb = f["flight"]
            gl = f.get("glow", ())
            for i, (sa, sb) in enumerate(f["vols"]):
                t0 = f["times"][i]
                self.volley_land.append(t0 + f["roll"] / 2 + fa + fb * 0.4)
                for shots, gs, gt in ((sa, ga, gb), (sb, gb, ga)):
                    for (s, t, h) in shots:
                        us, ut = self.base[gs] + s, self.base[gt] + t
                        r = t0 + float(rng.random()) * f["roll"]
                        xs, ys = self.pos(us, r)
                        tf = fa + fb * abs(self.x0[ut] - self.x0[us]) * 0.001
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
                        glow.append(self.groups[gs]["side"] in gl)
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
        self.glow = np.array(glow, bool)[o]
        dust_p = np.array(dust_p)[o]
        self.td = np.full(n_all, np.inf)
        for u, t, h in zip(self.target, self.arr, self.hit):
            if h and t < self.td[u]:
                self.td[u] = t
        rels = [[] for _ in range(n_all)]
        for u, r in zip(self.shooter, self.rel):
            rels[u].append(r)
        self.rels = [sorted(v) for v in rels]
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

    def center_x(self, g, t, view=None):
        Zx, Zy, ox, oy = view or self.view(t)
        c = self.groups[g]
        face = 1 if c["side"] == "R" else -1
        xc = c["xf"] - face * (c["cols"] - 1) * self.geo.col_sp / 2 + self.shift(g, t)
        return ox + Zx * xc

    def screen(self, u, t, view=None):
        """兵 u の足元の画面座標と、画面での大きさ k"""
        Zx, Zy, ox, oy = view or self.view(t)
        x, gy = self.pos(u, t)
        return ox + Zx * x, oy + Zy * gy, self.k[u] * Zx

    # ---- 描く ----
    def draw(self, ctx, t, a=1.0, shake=True, view=None, field=True, arrows=True):
        if a <= 0:
            return
        if a < 1:
            ctx.push_group()
        ctx.save()
        sx, sy = self.shake(t) if shake else (0.0, 0.0)
        ctx.translate(sx, sy)
        Zx, Zy, ox, oy = view or self.view(t)
        geo = self.geo
        ze = geo.s * Zx
        if field:
            ytop = oy + Zy * geo.row_y0 - 24 * ze
            ybot = oy + Zy * geo.gy(geo.depth - 1) + 20 * ze
            draw_field(ctx, ytop, ybot, ze, ox + Zx * WX0, ox + Zx * WX1)
        for g, c in self.groups.items():
            self._noboris(ctx, g, c, t, Zx, Zy, ox, oy, ze)
        for dead_pass in (True, False):
            for u in self.order:
                dead = t >= self.td[u]
                if dead != dead_pass:
                    continue
                x, gy = self.pos(u, t)
                X, Y = ox + Zx * x, oy + Zy * gy
                if X < 20 or X > 990:                 # 左ページの外（出番を待つ隊）は描かない。はみ出しは clip_left で切る
                    continue
                team = self.team[u]
                k = self.k[u] * Zx
                if dead:
                    f = ease_out((t - self.td[u]) / 0.42)
                    al = 1.0 - 0.38 * f
                    clr = self.groups[self.gnames[self.gid[u]]].get("clear")
                    if clr is not None and t > clr:
                        al *= 1 - clamp01((t - clr) / 0.6)
                        if al <= 0.01:
                            continue
                    draw_soldier(ctx, X, Y, k, team, 0.0, int(self.face[u]), f, al, t)
                else:
                    sway = 0.012 * math.sin(t * 2.2 + self.sway_ph[u])
                    draw_soldier(ctx, X, Y, k, team, self.draw_amount(u, t), int(self.face[u]), 0.0, 1.0,
                                 t + self.sway_ph[u], sway)
        if arrows:
            self._arrows(ctx, t, Zx, Zy, ox, oy, ze)
            self._dust(ctx, t, Zx, Zy, ox, oy, ze)
        ctx.restore()
        if a < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)

    def _noboris(self, ctx, g, c, t, Zx, Zy, ox, oy, ze):
        geo = self.geo
        face = 1 if c["side"] == "R" else -1
        if c.get("hide_dead_poles") and self.alive(g, t) == 0 and t > self.last_death(g) + 0.5:
            return                                     # 全滅した隊の旗は片づける（7章）
        xr0 = c["xf"] - face * (c["cols"] - 1) * geo.col_sp - face * 26 * geo.s + self.shift(g, t)
        for j, row in enumerate(c["poles"]):
            gyw = geo.gy(row)
            xw = xr0 + face * (j % 2) * 30 * geo.s
            xr, gy = ox + Zx * xw, oy + Zy * gyw
            if xr > 990:
                continue
            nobori(ctx, xr, gy, geo.persp(gyw), ze, c["side"], t, j * 1.7 + (0.5 if c["side"] == "B" else 0.0))

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
            if u < 1.0:
                arrow_at(ctx, xs, ys, xe, ye, h, u, ze, glow=bool(self.glow[i]))
            elif not self.hit[i]:
                dxv, dyv = xe - xs, (ye - ys) + 4 * h
                n = math.hypot(dxv, dyv) or 1.0
                ux, uy = dxv / n, dyv / n
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


def make_vols(path, alive_a, alive_b, rng):
    """人数の軌跡（[[赤, 青], …]。最初の行を含む）から、絵の一斉射撃の記録を作る。
    1体＝100人なので、体数（ceil(人数÷100)）が減ったぶんだけ、その回にでたらめに選んだ兵が倒れる。
    生きている兵は毎回1本ずつ撃つ（倒れる兵に当たる矢を1本ずつ、ほかは外れ）。返り値: vols, 残った赤, 残った青"""
    alive_a, alive_b = list(alive_a), list(alive_b)
    vols = []

    def shots(shooters, targets, dead):
        order = list(rng.permutation(shooters))
        out = []
        for j, d in enumerate(dead):
            out.append((int(order[j % len(order)]), int(d), True))
        for s in order[len(dead):]:
            out.append((int(s), int(targets[int(rng.integers(len(targets)))]), False))
        return out

    for i in range(1, len(path)):
        da = min(len(alive_a), max(0, figs(path[i - 1][0]) - figs(path[i][0])))
        db = min(len(alive_b), max(0, figs(path[i - 1][1]) - figs(path[i][1])))
        dead_b = [int(x) for x in rng.choice(alive_b, db, replace=False)] if db else []
        dead_a = [int(x) for x in rng.choice(alive_a, da, replace=False)] if da else []
        vols.append((shots(alive_a, alive_b, dead_b) if alive_a else [], shots(alive_b, alive_a, dead_a) if alive_b else []))
        alive_a = [u for u in alive_a if u not in dead_a]
        alive_b = [u for u in alive_b if u not in dead_b]
    return vols, alive_a, alive_b


def path_index(land_times, t):
    """着弾の時刻の並びから、t までに終わった一斉射撃の回数（＝人数の軌跡の行番号）"""
    return bisect_right(land_times, t)


def k_sample(k, seed):
    """青の腕前 k 倍の撃ち合い 1回ぶん（モデルの shoot_batch そのもの）"""
    rng = np.random.default_rng(seed)
    R, B, t, tr = shoot_batch(N_R, N_B, P_HIT, min(1.0, k * P_HIT), rng, track=400)
    T = int(t[0])
    return dict(seed=seed, k=k, path=tr[0, :T + 1].tolist(), red_left=int(R[0]), blue_left=int(B[0]), turns=T)


SEED_K2, SEED_K45 = 2, 5            # 腕前2倍・4.5倍の見本の種（勝った側の残りが1万回の平均の±1%以内。--ksearch で探した）
SEED_MINI = tuple(range(201, 213))  # 2章の小さな合戦12面（別の種の1回ぶん。結果はそのまま出す）


# ============================================================
# 前から順に戦う行列（刀の斬り合い・狭い道）
# ============================================================
class Queue:
    """sides = {"R"/"B": dict(n, lanes=[(画面y, k)], front=画面x, sp=間隔, poles=[(x, y, s)])}。
    兵 u は lane = u % L・前からの順番 rank = u // L。人数の軌跡（path）の体数が減るたびに、
    いちばん兵の多い列の先頭が倒れ、その列の後ろが1歩ずつ詰める"""

    def __init__(self, sides, path, times, seed, weapon="sword"):
        rng = np.random.default_rng(seed)
        self.sides, self.weapon = sides, weapon
        self.ph = rng.uniform(0, 6.28, 400)
        self.td = {}
        self.lane_deaths = {}
        self.death_events = []                       # (時刻, side, lane) 効果音・火花用
        for j, (sd, c) in enumerate(sides.items()):
            L = len(c["lanes"])
            n = c["n"]
            self.td[sd] = np.full(n, np.inf)
            queues = [[u for u in range(n) if u % L == ln] for ln in range(L)]
            self.lane_deaths[sd] = [[] for _ in range(L)]
            for i in range(1, len(path)):
                d = figs(path[i - 1][j]) - figs(path[i][j])
                step = times[i] - times[i - 1] if i < len(times) else 0.1
                for _ in range(max(0, d)):
                    cnt = np.array([len(q) for q in queues], float) + rng.uniform(0, 0.5, L)
                    ln = int(np.argmax(cnt))
                    if not queues[ln]:
                        continue
                    u = queues[ln].pop(0)
                    tdd = times[i - 1] + float(rng.uniform(0.2, 0.9)) * step
                    self.td[sd][u] = tdd
                    self.lane_deaths[sd][ln].append(tdd)
                    self.death_events.append((tdd, sd, ln))
            for ln in range(L):
                self.lane_deaths[sd][ln].sort()
        self.death_events.sort()
        self.ev_t = np.array([e[0] for e in self.death_events])

    def steps(self, sd, ln, t):
        """列 ln の先頭が何歩ぶん詰めたか（なめらか）"""
        v = 0.0
        for tdd in self.lane_deaths[sd][ln]:
            if tdd > t:
                break
            v += ease_in_out((t - tdd - 0.15) / 0.4)
        return v

    def front_x(self, sd):
        return self.sides[sd]["front"]

    def draw(self, ctx, t, a=1.0, fight=True):
        if a <= 0:
            return
        if a < 1:
            ctx.push_group()
        items = []
        for sd, c in self.sides.items():
            face = 1 if sd == "R" else -1
            L = len(c["lanes"])
            stp = [self.steps(sd, ln, t) for ln in range(L)]
            ndead = [sum(1 for x in self.lane_deaths[sd][ln] if x <= t) for ln in range(L)]
            for u in range(c["n"]):
                ln, rank = u % L, u // L
                y, k, dx = c["lanes"][ln]
                tdd = self.td[sd][u]
                if t >= tdd:
                    age = t - tdd
                    if age > 1.3:
                        continue
                    x = c["front"] + dx
                    al = (1 - 0.38 * ease_out(age / 0.42)) * (1 - clamp01((age - 0.7) / 0.6))
                    items.append((y - 0.5, 0, x + face * 4, y, k, sd, 0.0, face, ease_out(age / 0.42), al))
                    continue
                x = c["front"] + dx - face * c["sp"] * (rank - stp[ln])
                if x < 30 or x > 980:
                    continue
                is_front = fight and rank == ndead[ln]
                if self.weapon == "sword":
                    d = (0.5 + 0.5 * math.sin(t * 10.5 + self.ph[u % 400])) if is_front else 0.0
                else:
                    d = ease(((t * 2.6 + self.ph[u % 400]) % 1.0) * 1.3) if is_front else 0.0
                items.append((y, 1, x, y, k, sd, d, face, 0.0, 1.0))
        for c_ in self.sides.values():
            for (px, py, s, ze) in c_.get("poles", ()):
                items.append((py - 1, -1, px, py, s, c_["side"], ze, 0, 0, 1))
        items.sort(key=lambda z: (z[0], z[1]))
        for (_yy, kind, x, y, k, sd, d, face, fall, al) in items:
            if kind == -1:
                nobori(ctx, x, y, k, d, sd, t, x * 0.01)
            else:
                draw_soldier(ctx, x, y, k, sd, d, face, fall, al, t + x * 0.01, 0.012 * math.sin(t * 2.2 + x),
                             weapon=self.weapon)
        if a < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)

    def sparks(self, ctx, t, gap):
        """倒れた瞬間の火花（刀）。gap は向かい合う先頭の間（画面x）"""
        i0, i1 = bisect_left(self.ev_t, t - 0.3), bisect_right(self.ev_t, t)
        for (tdd, sd, ln) in self.death_events[i0:i1]:
            y, k, _dx = self.sides[sd]["lanes"][ln]
            age = (t - tdd) / 0.3
            x = gap
            yy = y - 70 * k
            ctx.set_source_rgba(1.0, 0.82, 0.2, 0.95 * (1 - age))
            ctx.set_line_width(3.2)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for j in range(6):
                ang = j * math.pi / 3 + 0.4
                r0, r1 = 4 + 10 * age, 12 + 18 * age
                ctx.move_to(x + math.cos(ang) * r0, yy + math.sin(ang) * r0)
                ctx.line_to(x + math.cos(ang) * r1, yy + math.sin(ang) * r1)
            ctx.stroke()

    def alive_from_path(self, path, times, t):
        i = bisect_right(times, t) - 1
        return path[max(0, min(len(path) - 1, i))]


# ============================================================
# 2章の部品: 小さな合戦12面・1万マス
# ============================================================
_SPR = {}


def sprite_soldier(team, fallen, k=0.17):
    """小さな合戦用の足軽（1枚描いて使い回す）"""
    key = (team, fallen, k)
    s = _SPR.get(key)
    if s is None:
        w, h = int(60 * k * 2.2) + 8, int(130 * k) + 8
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(s)
        draw_soldier(c, w / 2, h - 3, k, team, 0.0, 1 if team == "R" else -1, 1.0 if fallen else 0.0,
                     0.6 if fallen else 1.0, 0.3, shadow=False)
        _SPR[key] = s
    return s


def tiny_soldier(ctx, x, y, team, dead):
    """小さな合戦用の足軽（縁取りの少ない簡単な形。小さく描くと墨の線がつぶれるため）"""
    if dead:
        ctx.set_source_rgba(*hexrgb("#9a9a9a", 0.75))
        rrect(ctx, x - 4.5, y - 2.5, 9, 3, 1.2)
        ctx.fill()
        return
    tm = TEAM[team]
    ctx.set_source_rgba(*hexrgb(tm["flag"]))
    rrect(ctx, x - 2.2, y - 9, 4.4, 8, 1.2)              # 胴
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(HAT))
    ctx.move_to(x - 3.6, y - 9.5)                        # 陣笠
    ctx.line_to(x + 3.6, y - 9.5)
    ctx.line_to(x, y - 13)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.7))
    ctx.set_line_width(0.8)
    ctx.move_to(x, y - 1)
    ctx.line_to(x, y)
    ctx.stroke()


class Mini:
    """小さな合戦1面（赤100体・青50体）。path は1回ぶんの人数の軌跡（モデルの sample_shoot）"""

    def __init__(self, res, cx, cy, t0, length, seed):
        rng = np.random.default_rng(seed)
        self.res, self.cx, self.cy, self.t0, self.len = res, cx, cy, t0, length
        path = res["path"]
        n = len(path) - 1
        self.times = [t0 + length * i / n for i in range(n + 1)]
        self.pos = []
        for u in range(100):
            col, row = u // 10, u % 10
            self.pos.append(("R", cx - 14 - col * 6.6 + (row % 2) * 2.5, cy - 22 + row * 4.4))
        for u in range(50):
            col, row = u // 10, u % 10
            self.pos.append(("B", cx + 26 + col * 6.6 - (row % 2) * 2.5, cy - 22 + row * 4.4))
        self.td = np.full(150, np.inf)
        alive_r, alive_b = list(range(100)), list(range(100, 150))
        for i in range(1, len(path)):
            for lst, j in ((alive_r, 0), (alive_b, 1)):
                d = figs(path[i - 1][j]) - figs(path[i][j])
                if d > 0:
                    for u in rng.choice(lst, min(d, len(lst)), replace=False):
                        self.td[u] = self.times[i - 1] + float(rng.uniform(0.3, 1.0)) * (self.times[i] - self.times[i - 1])
                        lst.remove(int(u))
        self.order = sorted(range(150), key=lambda u: self.pos[u][2])
        self.t_end = self.times[-1]

    def draw(self, ctx, t, a):
        if a <= 0.003:
            return
        cx, cy = self.cx, self.cy
        ctx.push_group()
        fill(ctx, hexrgb("#dbe8c0", 0.8))
        rrect(ctx, cx - 92, cy - 52, 184, 92, 10)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6))
        ctx.set_line_width(2)
        rrect(ctx, cx - 92, cy - 52, 184, 92, 10)
        ctx.stroke()
        for u in self.order:
            team, x, y = self.pos[u]
            tiny_soldier(ctx, x, y, team, t >= self.td[u])
        if self.t0 <= t < self.t_end + 0.2:          # 小さな矢
            ctx.set_source_rgba(*hexrgb(INK, 0.7))
            ctx.set_line_width(1.3)
            ph = (t * 7) % 1.0
            for j in range(5):
                xx = cx - 10 + ((ph + j * 0.2) % 1.0) * 30
                yy = cy - 22 + j * 9
                ctx.move_to(xx, yy)
                ctx.line_to(xx + 5, yy)
            ctx.stroke()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        if t >= self.t_end:
            q = fade(t, self.t_end, 0.25) * a
            text(ctx, f"残り {fmt(self.res['red_left'])}人", cx, cy + 66, 26, RED, alpha=q)


# 1万マス（1マス＝1回の合戦。色＝赤の残り。値は 1万回の結果そのもの（ch1 の度数分布から並べ直し）。並びの順だけでたらめ）
GRID_N, GRID_C = 100, 4.4
GRID_X0, GRID_Y0 = 505 - GRID_N * GRID_C / 2, 128.0
_vals = np.repeat(np.array([int(k) for k in RES["ch1"]["hist"]], np.int64),
                  np.array(list(RES["ch1"]["hist"].values()), np.int64))
GRID_VALS = np.random.default_rng(77).permutation(_vals)          # 落ちてくる順
GRID_RUNMEAN = np.cumsum(GRID_VALS) / np.arange(1, len(GRID_VALS) + 1)
GRID_LO, GRID_HI = 8380.0, 8580.0                     # 色の幅（ほぼ全部の回が入る 5%〜95% より少し広く）


def grid_color(v):
    u = np.clip((v - GRID_LO) / (GRID_HI - GRID_LO), 0, 1)
    a = np.array(hexrgb("#f8d6d2")[:3])
    b = np.array(hexrgb("#a51d2d")[:3])
    return a[None, :] * (1 - u[:, None]) + b[None, :] * u[:, None]


class Grid:
    def __init__(self):
        n, c = GRID_N, GRID_C
        self.px = int(round(n * c))
        img = np.zeros((self.px, self.px, 4), np.uint8)
        cols = grid_color(GRID_VALS.astype(float))
        self.full = img.copy()
        self.idx = np.full((self.px, self.px), 10 ** 9, np.int64)
        for i in range(n * n):
            r, q = i // n, i % n
            y0, y1 = int(round(r * c)), int(round((r + 1) * c)) - 1
            x0, x1 = int(round(q * c)), int(round((q + 1) * c)) - 1
            col = cols[i]
            self.full[y0:y1, x0:x1, 0] = int(col[2] * 255)
            self.full[y0:y1, x0:x1, 1] = int(col[1] * 255)
            self.full[y0:y1, x0:x1, 2] = int(col[0] * 255)
            self.full[y0:y1, x0:x1, 3] = 255
            self.idx[y0:y1, x0:x1] = i
        self.empty = np.zeros_like(self.full)
        e = hexrgb("#e9e3d3")
        m = self.full[..., 3] > 0
        self.empty[m] = (int(e[2] * 255), int(e[1] * 255), int(e[0] * 255), 255)
        self._buf = None

    def draw(self, ctx, n, a=1.0):
        mask = (self.idx < n)[..., None]
        self._buf = np.ascontiguousarray(np.where(mask, self.full, self.empty))
        s = cairo.ImageSurface.create_for_data(memoryview(self._buf), cairo.FORMAT_ARGB32, self.px, self.px, self.px * 4)
        ctx.set_source_surface(s, GRID_X0, GRID_Y0)
        ctx.paint_with_alpha(a)


GRID = Grid()


# ============================================================
# 場面のデータと時刻（見本の軌跡はすべて data.json の samples か、モデルの関数で回した1回ぶん）
# ============================================================
SAMPLE_MAIN = RES["samples"]["main"][0]             # 1万 vs 5千 撃ち合い（seed 6、残り 8,490、17回）
SAMPLE_DUEL = RES["samples"]["duel"]                # 斬り合い 野原（seed 1、残り 4,974）
SAMPLE_NARROW = RES["samples"]["narrow"]            # 狭い道 幅50（seed 13、残り 5,042）
SAMPLE_SPLIT = RES["samples"]["split3"]             # 7,500 vs 3隊（seed 11、残り 4,356）
SAMPLE_K2 = k_sample(2, SEED_K2)                    # 青の腕前2倍（赤が勝つ）
SAMPLE_K45 = k_sample(4.5, SEED_K45)                # 青の腕前4.5倍（青が勝つ）
SAMPLE_MINI = [sample_shoot(s) for s in SEED_MINI]


def idle(t):
    """戦いの前の陣形（旗はゆれる）を描くための時刻"""
    return t - 100000.0


def battle_times(n, t0, t1):
    return [t0 + (t1 - t0) * i / max(1, n - 1) for i in range(n)]


# ---- 0章: 見本の合戦 ----
T_B0 = S("g0") + 0.25
_VM, _, _ = make_vols(SAMPLE_MAIN["path"], range(100), range(50), np.random.default_rng(11))
BATTLE_MAIN = Battle(
    {"R": dict(side="R", n=100, cols=10, rows=list(range(10)), xf=XF_R, poles=[3.5, 6.0, 8.5]),
     "B": dict(side="B", n=50, cols=5, rows=list(range(10)), xf=XF_B, poles=[3.0, 6.0])},
    [dict(ga="R", gb="B", vols=_VM, times=battle_times(len(_VM), T_B0, E("g0") - 1.45), flight=(0.40, 0.42),
          roll=0.22, arc=0.07, dust=0.07)], GEO, lambda t: VIEW_MAIN, seed=3)
T_END_MAIN = max(BATTLE_MAIN.last_death("R"), BATTLE_MAIN.last_death("B"))
LAND_MAIN = sorted(BATTLE_MAIN.volley_land)

# ---- 2章: 同じ合戦を早回し → 下の帯へ → 小さな合戦12面 → 1万マス ----
T2A = S("c2_1") + 0.2
FF2 = 3.0                                            # 早回しの倍率


def tau2(t):
    return T_B0 - 0.4 + (t - T2A) * FF2


T2_SH0, T2_SH1 = S("g2") - 0.7, S("g2") + 0.5        # 戦場を下の帯へ縮める
T_MINI0 = S("g2") + 0.6
MINI_C = [(210 + 195 * (i % 4), 205 + 140 * (i // 4)) for i in range(12)]
MINIS = [Mini(r, cx, cy, T_MINI0 + 0.13 * i, 1.6, 50 + i) for i, (r, (cx, cy)) in enumerate(zip(SAMPLE_MINI, MINI_C))]
T_GRID0 = S("g2") + 5.6
T_GRID1 = E("g2") - 0.4


def grid_n(t):
    u = clamp01((t - T_GRID0) / (T_GRID1 - T_GRID0))
    return int(round(10000 * u ** 2.0))


# ---- 3章: 最初の一斉射撃に寄る（矢の本数を見せる。1回の一斉射撃の「狙われ方」の平均どおりに、青1体に2本・赤2体に1本） ----
_fr = np.random.default_rng(5)
FOCUS_RED_TGT = _fr.permutation(np.repeat(np.arange(50), 2))     # 赤 u の矢 → 青の何番か（青1体に2本ずつ）
_red_sorted = sorted(range(100), key=lambda u: (round((BATTLE_MAIN.gy[u] - GEO.row_y0) / GEO.row_dy), BATTLE_MAIN.x0[u]))
FOCUS_PAIRS = [(_red_sorted[2 * i], _red_sorted[2 * i + 1]) for i in range(50)]   # 赤を隣どうし2体ずつ
FOCUS_BLUE_TGT = _fr.permutation(50)                               # 青 v の矢 → 赤の何組目か
T_FA = S("c3_2") + 0.5 * dur("c3_2")
T_FB = S("c3_4") + 0.5 * dur("c3_4")
FLY = 1.3


def _near(team, x, y):
    best, bd = None, 1e9
    for u in range(BATTLE_MAIN.n_all):
        if BATTLE_MAIN.team[u] != team:
            continue
        X, Y, _k = BATTLE_MAIN.screen(u, 0, VIEW_MAIN)
        d = math.hypot(X - x, Y - y)
        if d < bd:
            best, bd = u, d
    return best


SPOT_B = _near("B", 745, 630)                        # スポットライトを当てる青の1体
_pi = min(range(50), key=lambda i: math.hypot(*(np.array(BATTLE_MAIN.screen(FOCUS_PAIRS[i][0], 0, VIEW_MAIN)[:2]) - (420, 630))))
SPOT_R = FOCUS_PAIRS[_pi]                            # スポットライトを当てる赤の2体
T_SPOT_B, T_SPOT_R = S("c3_3"), S("c3_5")
T_SPOT_END = E("c3_6") + 1.6

# ---- 4章: 腕前（青の矢が光る） ----
T_K2 = S("c4_2") + 0.6 * dur("c4_2")
T_K45 = S("c4_6") + 0.55 * dur("c4_6")


def _k_battle(smp, t0, t1, seed):
    v, _, _ = make_vols(smp["path"], range(100), range(50), np.random.default_rng(seed))
    return Battle({"R": dict(side="R", n=100, cols=10, rows=list(range(10)), xf=XF_R, poles=[3.5, 6.0, 8.5]),
                   "B": dict(side="B", n=50, cols=5, rows=list(range(10)), xf=XF_B, poles=[3.0, 6.0])},
                  [dict(ga="R", gb="B", vols=v, times=battle_times(len(v), t0, t1), flight=(0.40, 0.42),
                        roll=0.18, arc=0.07, dust=0.06, glow=("B",))], GEO, lambda t: VIEW_MAIN, seed=seed)


BATTLE_K2 = _k_battle(SAMPLE_K2, T_K2, S("c4_3") - 0.5, 21)
BATTLE_K45 = _k_battle(SAMPLE_K45, T_K45, S("c4_7a") - 0.4, 22)

# ---- 5章: 刀の斬り合い（前の組だけ。早回し） ----
_RW = [470 + GEO.row_dy * r for r in range(10)]
DUEL_SIDES = {
    "R": dict(side="R", n=100, front=518.0, sp=GEO.col_sp,
              lanes=[(y, GEO.k(602 + GEO.row_dy * r) * 1.0, -(r % 2) * 10.0) for r, y in enumerate(_RW)],
              poles=[(150.0, _RW[3] + 15, GEO.persp(602 + GEO.row_dy * 3.5), 1.2),
                     (180.0, _RW[7] + 15, GEO.persp(602 + GEO.row_dy * 7.5), 1.2)]),
    "B": dict(side="B", n=50, front=566.0, sp=GEO.col_sp,
              lanes=[(y, GEO.k(602 + GEO.row_dy * r) * 1.0, (r % 2) * 10.0) for r, y in enumerate(_RW)],
              poles=[(760.0, _RW[3] + 15, GEO.persp(602 + GEO.row_dy * 3.5), 1.2),
                     (735.0, _RW[7] + 15, GEO.persp(602 + GEO.row_dy * 7.5), 1.2)])}
T_D0, T_D1 = S("c5_3") + 0.4, E("g5") - 0.2
DUEL_TIMES = battle_times(len(SAMPLE_DUEL["path"]), T_D0, T_D1)
DUEL = Queue(DUEL_SIDES, SAMPLE_DUEL["path"], DUEL_TIMES, 31, weapon="sword")

# ---- 6章: 狭い道（1列。先頭どうしが撃ち合う。早回し） ----
ROAD_Y, ROAD_K = 640.0, 0.85
NARROW_SIDES = {
    "R": dict(side="R", n=100, front=455.0, sp=52.0, lanes=[(ROAD_Y, ROAD_K, 0.0)], poles=[(128.0, ROAD_Y + 4, 1.0, 0.95)]),
    "B": dict(side="B", n=50, front=555.0, sp=52.0, lanes=[(ROAD_Y, ROAD_K, 0.0)], poles=[(882.0, ROAD_Y + 4, 1.0, 0.95)])}
T_N0, T_N1 = S("c6_2b") + 0.3 * dur("c6_2b"), E("g6") + 0.2
NARROW_TIMES = battle_times(len(SAMPLE_NARROW["path"]), T_N0, T_N1)
NARROW = Queue(NARROW_SIDES, SAMPLE_NARROW["path"], NARROW_TIMES, 41, weapon="bow")

# ---- 7章: 相手を分ける（青 7,500 が迎え撃ち、赤 3,334＋3,333＋3,333 が順に来る） ----
_segs = []
for _gi in range(3):
    _segs.append([[r, b] for r, b, g in SAMPLE_SPLIT["path"] if g == _gi])
T_S0, T_S1 = S("c7_3") + 0.3, E("c7_7") - 0.4
MARCH = 1.4
_nturn = sum(len(s_) - 1 for s_ in _segs)
_VI_S = (T_S1 - T_S0 - 2 * (MARCH + 0.9)) / _nturn
_rs = np.random.default_rng(61)
_alive_r = list(range(figs(SPLIT_R)))
SPLIT_FIGHTS, SPLIT_ROWS, SPLIT_LAND0 = [], [], []
_tt = T_S0
SPLIT_MARCH = []
for _gi, _seg in enumerate(_segs):
    if _gi > 0:
        SPLIT_MARCH.append((_tt, _tt + MARCH))
        _tt += MARCH + 0.1
    _v, _alive_r, _ = make_vols(_seg, _alive_r, range(figs(SAMPLE_SPLIT["groups"][_gi])), _rs)
    _times = [_tt + _VI_S * i for i in range(len(_v))]
    SPLIT_FIGHTS.append(dict(ga="R", gb=f"G{_gi}", vols=_v, times=_times, flight=(0.40, 0.42), roll=0.2, arc=0.07, dust=0.06))
    for i, row in enumerate(_seg):
        SPLIT_ROWS.append((_tt + _VI_S * (i - 1) + 0.75 if i > 0 else (_tt - MARCH - 0.1 if _gi else _tt - 0.01),
                           row[0], row[1], _gi))
    _tt = _times[-1] + 0.8
# 2026-10-09 初見チェック: 色を入れ替えない。分かれて順に来るのは赤（1万の大軍のまま）、迎え撃つのが青。
# モデルは両軍の腕前が同じで対称なので、見本の軌跡（迎え撃つ側 7,500人・来る側 3,334＋3,333＋3,333人）をそのまま色だけ入れ替えて使う
SPLIT_WAIT = 520.0                                   # 出番を待つ赤の隊は、左ページの外（左）で待つ
_gdef = {"R": dict(side="B", n=figs(SPLIT_R), cols=8, rows=list(range(10)), xf=XF_B - 72.0, poles=[3.5, 6.5])}
for _gi, _n in enumerate(figs(g) for g in SAMPLE_SPLIT["groups"]):        # 3,334・3,333・3,333人 → どれも34体
    _gdef[f"G{_gi}"] = dict(side="R", n=_n, cols=4, rows=list(range(10)), xf=XF_R - 72.0 - (SPLIT_WAIT if _gi else 0.0),
                            poles=[3.0, 6.0], march=(SPLIT_MARCH[_gi - 1][0], SPLIT_MARCH[_gi - 1][1], SPLIT_WAIT) if _gi else None,
                            clear=SPLIT_MARCH[_gi][0] if _gi < 2 else None, hide_dead_poles=True)
BATTLE_SPLIT = Battle(_gdef, SPLIT_FIGHTS, GEO, lambda t: VIEW_MAIN, seed=7)
SPLIT_ROW_T = [r[0] for r in SPLIT_ROWS]


def split_now(t):
    """いまの (赤の人数, 戦っている青の組の人数, 組の番号)"""
    i = max(0, bisect_right(SPLIT_ROW_T, t) - 1)
    _t0, r, b, g = SPLIT_ROWS[i]
    return r, b, g


# ============================================================
# 左ページ
# ============================================================
def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 1010)
    ctx.clip()


def counter(ctx, x, y, label, n, col, a=1.0, size=40):
    if a <= 0.003:
        return
    s = f"{label} {fmt(n)}人" if n is not None else label
    text(ctx, s, x, y, fit(s, size, 380), col, alpha=a)


def counters_main(ctx, r, b, a=1.0, y=360, bl="青"):
    counter(ctx, 334, y, "赤", r, FLAG_R, a)
    counter(ctx, 760, y, bl, b, FLAG_B, a)


def legend_100(ctx, a=1.0, x=150, y=868):
    """絵の足軽1人＝100人（左ページの左下）"""
    if a <= 0.003:
        return
    s = sprite_soldier("R", False, 0.42)
    ctx.set_source_surface(s, x - s.get_width() / 2, y + 22 - s.get_height())
    ctx.paint_with_alpha(a)
    text(ctx, "＝ 100人", x + 40, y - 6, 32, INK, align="left", alpha=a)


def ff_label(ctx, t, t0, t1, x=150, y=300):
    """「早回し」の印"""
    a = fade(t, t0, 0.3) * out_fade(t, t1)
    if a > 0.003:
        text(ctx, "▶▶ 早回し", x, y, 30, PENCIL, align="left", alpha=a)


def spotlight(ctx, holes, a):
    if a <= 0.003:
        return
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(LX0_ - 70, LY0_ - 60, LX1_ - LX0_ + 115, LY1_ - LY0_ + 80)
    for (x, y, rx, ry) in holes:
        ctx.new_sub_path()
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
    ctx.set_source_rgba(*hexrgb(PAPER, 0.78 * a))
    ctx.fill()
    ctx.restore()


def tag(ctx, s, x, y, size, col, a=1.0, progress=1.0):
    """白い下地つきの札（絵の上に置く字）"""
    if a <= 0.003 or progress <= 0:
        return
    w = text_width(s, size) + 26
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, x - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, x, y, size, col, progress, align="center", alpha=a)


def L_open(ctx, t):
    """0章・1章: 「合戦」の字、野原の合戦（見本1回）"""
    t_after = S("c1_1")
    BATTLE_MAIN.draw(ctx, t if t < t_after else max(t, T_END_MAIN + 0.5))
    # 0秒目に大きく「合戦」。赤い下線は0秒目から引く（0〜0.3秒で画面が動く）
    text(ctx, "合戦", 505, 190, 150, INK)
    pen_line(ctx, 385, 278, 625, 272, RED, seed=3, width=9, progress=clamp01(t / 0.6))
    a0 = fade(t, S("c0_1") + 0.2, 0.4)
    if t < S("c0_6"):
        counter(ctx, 334, 360, "赤 1万人", None, FLAG_R, a0)
        counter(ctx, 760, 360, "青 5千人", None, FLAG_B, a0)
    else:
        q = fade(t, S("c0_6"), 0.3)
        counter(ctx, 760, 360, "青 全滅", None, FLAG_B, q)
        if t < S("c0_7"):
            counter(ctx, 334, 360, "赤 1万人", None, FLAG_R, q)
        else:
            q7 = fade(t, S("c0_7") + 0.2, 0.3)
            counter(ctx, 334, 360, "赤 残り ？人", None, FLAG_R, q7)
    legend_100(ctx, fade(t, S("c0_2") + 0.3, 0.4))


def L_many(ctx, t):
    """2章: 早回し → 下の帯 → 小さな合戦12面 → 1万マス"""
    tau = min(tau2(t), T_END_MAIN + 0.6) if t < T2_SH0 else T_END_MAIN + 0.6 + (t - T2_SH0)
    u = ease_in_out((t - T2_SH0) / (T2_SH1 - T2_SH0))
    view = view_lerp(VIEW_MAIN, VIEW_STRIP, u)
    BATTLE_MAIN.draw(ctx, tau, view=view, shake=u < 0.01)
    # 早回しの人数（見本の軌跡そのまま）
    if t < T2_SH0 + 0.3:
        i = path_index(LAND_MAIN, tau)
        r, b = SAMPLE_MAIN["path"][min(i, len(SAMPLE_MAIN["path"]) - 1)]
        a = fade(t, T2A - 0.1, 0.3) * out_fade(t, T2_SH0 - 0.1)
        counters_main(ctx, r, b, a)
        ff_label(ctx, t, T2A, T2_SH0 - 0.1, x=130, y=300)
    else:
        r = SAMPLE_MAIN["red_left"]
        a = fade(t, T2_SH1 - 0.2, 0.3)
        text(ctx, f"さっきの合戦  赤の残り {fmt(r)}人", 505, 712, 30, PENCIL, bold=False, alpha=a)
    # 小さな合戦12面
    ma = fade(t, T_MINI0 - 0.3, 0.3) * out_fade(t, T_GRID0 - 0.5, 0.4)
    if ma > 0:
        for m in MINIS:
            m.draw(ctx, t, ma)
    # 1万マス
    ga = fade(t, T_GRID0 - 0.3, 0.4)
    if ga > 0:
        text(ctx, "1万回の合戦（1マス ＝ 1回）", 505, 104, 30, INK, alpha=ga)
        GRID.draw(ctx, grid_n(t), ga)
        # 色の見本
        y = GRID_Y0 + GRID_N * GRID_C + 30
        x0, x1 = 330, 680
        for i in range(40):
            v = GRID_LO + (GRID_HI - GRID_LO) * i / 39
            c = grid_color(np.array([v]))[0]
            ctx.set_source_rgba(c[0], c[1], c[2], ga)
            ctx.rectangle(x0 + (x1 - x0) * i / 40, y - 10, (x1 - x0) / 40 + 0.5, 20)
            ctx.fill()
        text(ctx, "赤の残り", 222, y, 28, PENCIL, bold=False, alpha=ga)
        text(ctx, "少", x0 - 22, y, 28, PENCIL, bold=False, alpha=ga)
        text(ctx, "多", x1 + 22, y, 28, PENCIL, bold=False, alpha=ga)
        text(ctx, "青が勝った回は 青のマス（0回）", 505, y + 40, 28, PENCIL, bold=False, alpha=ga)


def _red_shot_xy(u, t_):
    X, Y, k = BATTLE_MAIN.screen(u, 0, VIEW_MAIN)
    return X + 17 * k, Y - 60 * k


def _stuck_xy(v, j):
    X, Y, k = BATTLE_MAIN.screen(v, 0, VIEW_MAIN)
    return X + (-9 if j == 0 else 9) * k, Y + 1


_RED_REL = np.random.default_rng(8).uniform(0, 0.35, 100)
_BLUE_REL = np.random.default_rng(9).uniform(0, 0.35, 50)
_SEEN = {}
for _u in range(100):
    _v = int(FOCUS_RED_TGT[_u])
    _SEEN[_v] = _SEEN.get(_v, 0) + 1
    _SEEN[(_u, "j")] = _SEEN[_v] - 1


def focus_volleys(ctx, t, only_hl=False):
    """最初の一斉射撃をゆっくり: 赤の矢100本が青へ（1体に2本）、青の矢50本が赤へ（2体に1本）。
    only_hl はスポットライトの上に、赤くした矢だけを描き直す"""
    ze = GEO.s
    hl_b = t >= T_SPOT_B and t < T_SPOT_END
    for u in range(100):
        r = T_FA + _RED_REL[u]
        if t < r:
            continue
        v = 100 + int(FOCUS_RED_TGT[u])
        j = _SEEN[(u, "j")]
        xs, ys = _red_shot_xy(u, t)
        xe, ye = _stuck_xy(v, j)
        uu = (t - r) / FLY
        col = RED if (hl_b and v == SPOT_B) else INK
        if only_hl and col != RED:
            continue
        if uu < 1:
            arrow_at(ctx, xs, ys, xe, ye, 0.16 * abs(xe - xs) + 30, uu, ze, col=col)
        else:
            stuck_arrow(ctx, xe, ye, ze * (1.7 if col == RED else 1.0), ang=-0.75, col=col, alpha=0.95)
    hl_r = t >= T_SPOT_R and t < T_SPOT_END
    for v in range(50):
        r = T_FB + _BLUE_REL[v]
        if t < r:
            continue
        a_, b_ = FOCUS_PAIRS[int(FOCUS_BLUE_TGT[v])]
        X1, Y1, k1 = BATTLE_MAIN.screen(a_, 0, VIEW_MAIN)
        X2, Y2, k2 = BATTLE_MAIN.screen(b_, 0, VIEW_MAIN)
        X, Y, k = BATTLE_MAIN.screen(100 + v, 0, VIEW_MAIN)
        xs, ys = X - 17 * k, Y - 60 * k
        xe, ye = (X1 + X2) / 2, (Y1 + Y2) / 2 + 1
        uu = (t - r) / FLY
        col = RED if (hl_r and (a_, b_) == SPOT_R) else INK
        if only_hl and col != RED:
            continue
        if uu < 1:
            arrow_at(ctx, xs, ys, xe, ye, 0.16 * abs(xe - xs) + 30, uu, ze, col=col)
        else:
            stuck_arrow(ctx, xe, ye, ze * (1.7 if col == RED else 1.0), ang=-math.pi + 0.75, col=col, alpha=0.95)


def L_one(ctx, t):
    """3章: 最初の一斉射撃に寄る"""
    BATTLE_MAIN.draw(ctx, idle(t), shake=False)
    focus_volleys(ctx, t)
    a_end = out_fade(t, T_SPOT_END, 0.5)
    holes = []
    if t >= T_SPOT_B:
        X, Y, k = BATTLE_MAIN.screen(SPOT_B, 0, VIEW_MAIN)
        holes.append((X, Y - 45 * k, 48, 64))
    if t >= T_SPOT_R:
        X1, Y1, k1 = BATTLE_MAIN.screen(SPOT_R[0], 0, VIEW_MAIN)
        X2, Y2, k2 = BATTLE_MAIN.screen(SPOT_R[1], 0, VIEW_MAIN)
        holes.append(((X1 + X2) / 2, (Y1 + Y2) / 2 - 45 * k1, 44 + abs(X1 - X2) / 2, 64))
    if holes:
        spotlight(ctx, holes, fade(t, T_SPOT_B, 0.4) * a_end)
        focus_volleys(ctx, t, only_hl=True)
        if t >= T_SPOT_B:
            X, Y, k = BATTLE_MAIN.screen(SPOT_B, 0, VIEW_MAIN)
            pen_circle(ctx, X, Y - 45 * k, 50, 66, RED, seed=81, width=5, progress=clamp01((t - T_SPOT_B) / 0.4), alpha=a_end)
            tag(ctx, "2本", X, Y - 150 * k - 20, 44, RED, a_end * fade(t, T_SPOT_B + 0.2, 0.2), prog(t, T_SPOT_B + 0.3, "2本"))
        if t >= T_SPOT_R:
            X1, Y1, k1 = BATTLE_MAIN.screen(SPOT_R[0], 0, VIEW_MAIN)
            X2, Y2, _ = BATTLE_MAIN.screen(SPOT_R[1], 0, VIEW_MAIN)
            cx, cy = (X1 + X2) / 2, (Y1 + Y2) / 2 - 45 * k1
            pen_circle(ctx, cx, cy, 46 + abs(X1 - X2) / 2, 66, RED, seed=82, width=5,
                       progress=clamp01((t - T_SPOT_R) / 0.4), alpha=a_end)
            tag(ctx, "2人で1本", cx, cy - 105 * k1 - 20, 40, RED, a_end * fade(t, T_SPOT_R + 0.2, 0.2), prog(t, T_SPOT_R + 0.3, "2人で1本"))
    # 3章の後半: 赤の上に「撃つ矢 2倍」「受ける矢 半分」
    if t >= S("c3_7"):
        wr(ctx, "撃つ矢 2倍", 360, 318, 36, INK, S("c3_7") + 0.4, t, align="center")
    if t >= S("c3_8"):
        wr(ctx, "受ける矢 半分", 360, 372, 36, INK, S("c3_8") + 0.4, t, align="center")
    legend_100(ctx)


def L_skill(ctx, t):
    """4章: 青の腕前を上げる（青の矢が光る）。2倍 → 4.5倍"""
    sw = fade(t, T_K45 - 0.9, 0.5)
    if sw < 1:
        grp(ctx, 1 - sw, lambda c: BATTLE_K2.draw(c, t))
    if sw > 0:
        grp(ctx, sw, lambda c: BATTLE_K45.draw(c, t))
    if t < T_K45 - 0.6:
        smp, bt, lab = SAMPLE_K2, BATTLE_K2, "青の腕前 2倍"
        a = fade(t, S("c4_2") + 0.3, 0.3) * out_fade(t, T_K45 - 0.9)
    else:
        smp, bt, lab = SAMPLE_K45, BATTLE_K45, "青の腕前 4.5倍"
        a = fade(t, T_K45 - 0.6, 0.3)
    i = path_index(bt.land_t, t)
    r, b = smp["path"][min(i, len(smp["path"]) - 1)]
    counters_main(ctx, r, b, a)
    if a > 0:
        text(ctx, lab, 760, 305, 34, FLAG_B, alpha=a)
    legend_100(ctx)


def L_sword(ctx, t):
    """5章: 刀で1対1（前の組だけ斬り合う）"""
    draw_field(ctx, 446, 776, 1.2)
    DUEL.draw(ctx, t, fight=t >= T_D0 - 0.3)
    DUEL.sparks(ctx, t, 542)
    r, b = DUEL.alive_from_path(SAMPLE_DUEL["path"], DUEL_TIMES, t)
    counters_main(ctx, r, b, fade(t, S("c5_2"), 0.3))
    ff_label(ctx, t, T_D0, T_D1 + 0.3)
    legend_100(ctx)


def draw_cliffs(ctx):
    """両側が崖の細い道"""
    rng = np.random.default_rng(12)
    xs = np.linspace(112, 898, 30)
    ctx.set_source_rgba(*hexrgb("#e6d9b8", 0.9))         # 道
    ctx.rectangle(112, 575, 786, 85)
    ctx.fill()
    for (ya, yb, sgn) in ((455, 580, 1), (785, 655, -1)):
        pts = [(x, yb + sgn * float(rng.uniform(-6, 6))) for x in xs]
        ctx.move_to(112, ya)
        for p in pts:
            ctx.line_to(*p)
        ctx.line_to(898, ya)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#b8ad9a", 0.85))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK, 0.35))          # 岩の筋
        ctx.set_line_width(2)
        for _ in range(26):
            x = float(rng.uniform(125, 885))
            y = float(rng.uniform(min(ya, yb) + 12, max(ya, yb) - 14))
            ctx.move_to(x, y)
            ctx.line_to(x + float(rng.uniform(-18, 18)), y + float(rng.uniform(8, 16)) * sgn)
        ctx.stroke()


def L_road(ctx, t):
    """6章: 狭い道（先頭の1体どうしが撃ち合い、後ろは並んで待つ）"""
    draw_cliffs(ctx)
    text(ctx, "崖", 505, 512, 34, INK, alpha=0.85)
    text(ctx, "崖", 505, 728, 34, INK, alpha=0.85)
    fight = T_N0 - 0.2 <= t <= T_N1 + 0.3
    ctx.save()
    ctx.rectangle(112, 380, 786, 400)                     # 列は道の枠の外へ続く（枠で切る）
    ctx.clip()
    NARROW.draw(ctx, t, fight=fight)
    ctx.restore()
    if fight:                                            # 先頭どうしの矢
        r_, b_ = NARROW.alive_from_path(SAMPLE_NARROW["path"], NARROW_TIMES, t)
        if r_ > 0 and b_ > 0:
            xr, xb = 455 + 17 * ROAD_K, 555 - 17 * ROAD_K
            for j in range(4):
                ph = ((t - T_N0) * 4.0 + j * 0.25) % 1.0
                if j % 2 == 0:
                    arrow_at(ctx, xr, ROAD_Y - 60 * ROAD_K, xb, ROAD_Y - 40 * ROAD_K, 12, ph, 1.0)
                else:
                    arrow_at(ctx, xb, ROAD_Y - 60 * ROAD_K, xr, ROAD_Y - 40 * ROAD_K, 12, ph, 1.0)
    r, b = NARROW.alive_from_path(SAMPLE_NARROW["path"], NARROW_TIMES, t)
    counters_main(ctx, r, b, fade(t, S("c6_1") + 0.5, 0.3), y=405)
    text(ctx, "← 列は後ろへ続く →", 505, 830, 30, PENCIL, bold=False, alpha=fade(t, S("c6_2"), 0.4))
    ff_label(ctx, t, T_N0, T_N1 + 0.3, x=130, y=300)
    legend_100(ctx, y=880)


def L_split(ctx, t):
    """7章: 青1万人が3隊に分かれて、順に来る"""
    BATTLE_SPLIT.draw(ctx, t)
    r, b, g = split_now(t)
    a = fade(t, S("c7_1") + 0.4, 0.3)
    counter(ctx, 300, 360, f"赤 {g + 1}隊目", b, FLAG_R, a)
    counter(ctx, 735, 360, "青", r, FLAG_B, a)
    wr(ctx, "赤1万人が 3隊に分かれて 順に来る", 505, 300, 32, INK, S("c7_3") + 0.2, t, align="center")
    for (m0, m1) in SPLIT_MARCH:
        q = fade(t, m0 - 0.6, 0.3) * out_fade(t, m1)
        if q > 0:
            text(ctx, "← 次の隊が来る", 230, 800, 30, FLAG_R, alpha=q)
    legend_100(ctx)


def L_name(ctx, t):
    """8章: 開戦前の陣形。限界の句に合わせて鉛筆で書き込む"""
    BATTLE_MAIN.draw(ctx, idle(t), shake=False)
    t5 = S("c8_5")
    d5 = dur("c8_5")
    notes = (("逃げない", 230, 0.05), ("疲れない", 505, 0.17), ("矢が尽きない", 780, 0.3))
    for s_, x, f in notes:
        wr(ctx, s_, x, 365, 34, PENCIL, t5 + f * d5, t, align="center")
    wr(ctx, "地形は道の幅だけ・士気も補給もなし", 505, 825, 32, PENCIL, t5 + 0.55 * d5, t, align="center")
    legend_100(ctx, a=1 - fade(t, t5 + 0.5 * d5, 0.3))


def L_end(ctx, t):
    """9章: 0章の決着の絵に戻る"""
    BATTLE_MAIN.draw(ctx, T_END_MAIN + 1.5 + (t - S("ch8")), shake=False)
    text(ctx, "合戦", 505, 190, 150, INK, alpha=fade(t, S("ch8"), 0.5))
    pen_line(ctx, 385, 278, 625, 272, RED, seed=3, width=9, progress=clamp01((t - S("ch8") - 0.3) / 0.6))
    counter(ctx, 334, 360, "赤 残り", SAMPLE_MAIN["red_left"], FLAG_R, fade(t, S("ch8") + 0.6, 0.4))
    counter(ctx, 760, 360, "青 全滅", None, FLAG_B, fade(t, S("ch8") + 0.6, 0.4))
    legend_100(ctx)


# ============================================================
# 右ページ（手書きの見出し・式・表）
# ============================================================
def rule_no(ctx, i, x, y, t0, t, a=1.0):
    """①②③ の丸数字（ペンで丸を描いて数字）"""
    if t >= t0:
        pen_circle(ctx, x, y, 27, 27, INK, seed=60 + i, width=4, progress=clamp01((t - t0) / 0.3), alpha=a)
        text(ctx, str(i + 1), x, y, 34, INK, alpha=a * fade(t, t0 + 0.1, 0.2))


def R_open(ctx, t):
    tc1 = S("c1_1")
    a = out_fade(t, tc1 - 0.15, 0.4)
    if a > 0:
        rules = (("c0_1", "赤 1万人 vs 青 5千人", 200), ("c0_3", "弓で一斉に撃ち合う", 340), ("c0_4", "腕前は同じ", 440))
        for i, (cid, s_, y) in enumerate(rules):
            t0 = S(cid) + 0.3
            rule_no(ctx, i, RX + 26, y, t0, t, a)
            wr(ctx, s_, RX + 78, y, 46, INK, t0 + 0.15, t, alpha=a)
        wr(ctx, "絵の足軽1人 ＝ 100人", RX + 78, 262, 34, PENCIL, S("c0_2") + 0.2, t, alpha=a)
        wr(ctx, "当たるのは 25本に1本", RX + 78, 500, 34, PENCIL, S("c0_4") + 0.6 * dur("c0_4"), t, alpha=a)
    if t >= tc1:
        s_ = "兵が2倍なら、2倍強い？"
        t0 = tc1 + 0.2
        wr(ctx, s_, RX, 215, 52, INK, t0, t, cps=8)
        pen_line(ctx, RX - 4, 258, RX + 590, 254, RED, seed=5, width=7, progress=clamp01((t - t0 - lf.write_dur(s_, 8)) / 0.4))
    t3 = S("c1_3")
    if t >= t3:
        wr(ctx, "腕前は同じだから、", RX, 345, 38, INK, t3 + 0.2, t)
        wr(ctx, "青5千人を倒すあいだに 赤も5千人倒される？", RX, 400, 36, INK, t3 + 0.4 * dur("c1_3"), t)
    t4 = S("c1_4")
    if t >= t4:
        pre = "10,000 − 5,000 ＝ "
        wr(ctx, pre + "5,000 ？", RX, 530, 64, INK, t4 + 0.05, t, cps=8)
        w0, w5 = text_width(pre, 64), text_width("5,000", 64)
        pen_circle(ctx, RX + w0 + w5 / 2, 530, w5 / 2 + 26, 48, RED, seed=15, width=7,
                   progress=clamp01((t - (t4 + 0.05 + lf.write_dur(pre + "5,000 ？", 8) - 0.2)) / 0.4))


def R_many(ctx, t):
    t1 = S("c2_1")
    wr(ctx, "同じ合戦を 1万回", RX, 160, 50, INK, t1 + 0.3, t, cps=8)
    n = grid_n(t)
    q = fade(t, T_GRID0, 0.4) * out_fade(t, S("c2_4") - 0.3, 0.3)
    if q > 0.003:
        text(ctx, "ためした回数", 1400, 285, 30, PENCIL, bold=False, alpha=q)
        text(ctx, f"{fmt(n)} ／ 10,000", 1400, 340, 52, INK, alpha=q)
        text(ctx, "ここまでの平均の残り", 1400, 420, 30, PENCIL, bold=False, alpha=q)
        if n > 0:
            text(ctx, f"{fmt(GRID_RUNMEAN[n - 1])}人", 1400, 490, 84, RED, alpha=q)
        text(ctx, "素朴な予想は 5,000人", 1400, 565, 30, PENCIL, bold=False, alpha=q)
    t3 = S("c2_3")
    wr(ctx, f"赤が失ったのは 約{fmt(round100(N_R - RES['ch1']['rem_mean']))}人だけ", RX, 228, 36, RED,
       t3 + 0.6 * dur("c2_3"), t)
    t4 = S("c2_4")
    if t >= t4:
        wr(ctx, "青が勝った回数", RX, 300, 34, INK, t4 + 0.3, t)
        wr(ctx, f"{RES['ch1']['blue']}回 ／ 1万回", RX + 20, 368, 60, FLAG_B, t4 + 0.4 * dur("c2_4"), t, cps=8)
    t5 = S("c2_5")
    if t >= t5:
        wr(ctx, "乱数を変えて、もう3回（各1万回）", RX, 450, 32, INK, t5 + 0.2, t)
    for k, run in enumerate(RES["ch1"]["runs"]):
        ts = E("c2_5") - 0.2 + 0.85 * k
        if t < ts:
            continue
        y = 515 + 58 * k
        p = clamp01((t - ts) / 0.7)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6))
        ctx.set_line_width(2)
        rrect(ctx, RX + 10, y - 13, 230, 26, 6)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(RED, 0.75))
        rrect(ctx, RX + 12, y - 11, 226 * p, 22, 5)
        ctx.fill()
        qa = fade(t, ts + 0.7, 0.25)
        text(ctx, f"約{fmt(round100(run['rem_mean']))}人", RX + 270, y, 40, RED, align="left", alpha=qa)
        text(ctx, f"青の勝ち {run['blue']}回", RX + 500, y, 32, FLAG_B, align="left", alpha=qa)


def R_one(ctx, t):
    wr(ctx, "最初の一斉射撃に寄る", RX, 160, 48, INK, S("c3_1") + 0.5 * dur("c3_1"), t, cps=8)
    t7, t11 = S("c3_7"), S("c3_11")
    aA = out_fade(t, t7 + 0.1, 0.4)                   # 矢の割り算（3章の前半）
    if aA > 0:
        wr(ctx, "赤の矢 10,000本 ÷ 青 5,000人", RX, 255, 40, INK, S("c3_2") + 0.4 * dur("c3_2"), t, alpha=aA)
        wr(ctx, "＝ 2本", RX + 40, 312, 46, RED, S("c3_3") + 0.4 * dur("c3_3"), t, alpha=aA)
        wr(ctx, "青の矢 5,000本 ÷ 赤 10,000人", RX, 390, 40, INK, S("c3_4") + 0.4 * dur("c3_4"), t, alpha=aA)
        wr(ctx, "＝ 0.5本", RX + 40, 447, 46, RED, S("c3_5") + 0.4 * dur("c3_5"), t, alpha=aA)
    aB = fade(t, t7 + 0.4, 0.3) * out_fade(t, t11, 0.4)   # 2倍 × 2倍（3章の中ほど）
    if aB > 0:
        wr(ctx, "撃つ矢が 2倍", RX, 255, 42, INK, t7 + 0.4, t, alpha=aB)
        wr(ctx, "相手の矢は 散らばって 半分", RX, 315, 42, INK, S("c3_8") + 0.3, t, alpha=aB)
        wr(ctx, "2倍 × 2倍 ＝ 4倍", RX, 400, 56, INK, S("c3_9") + 0.2, t, cps=8, alpha=aB)
    if t >= t11:                                       # 式（読み上げない）
        wr(ctx, "10,000² − 5,000² ＝ 残り²", RX, 255, 46, INK, t11 + 0.2, t, cps=10)
        wr(ctx, "→ 残り 約8,700人", RX + 40, 318, 46, INK, t11 + 0.6 * dur("c3_11"), t)
        wr(ctx, "実際は 平均 約8,500人", RX + 40, 395, 44, RED, S("c3_12") + 0.3, t)
    t10 = S("c3_10")
    if t >= t10:
        wr(ctx, "兵の数は 2乗で効く", RX, 470, 46, RED, t10 + 0.5 * dur("c3_10"), t)
        pen_line(ctx, RX - 4, 505, RX + 440, 501, RED, seed=9, width=6,
                 progress=clamp01((t - t10 - 0.5 * dur("c3_10") - lf.write_dur("兵の数は 2乗で効く")) / 0.4))
    t6 = S("c3_6")
    if t >= t6:                                        # 4倍（3秒以上、章の終わりまで残す）
        q = fade(t, t6 + 0.55 * dur("c3_6"), 0.35)
        text(ctx, "青は赤の", RX + 10, 590, 40, INK, align="left", alpha=q)
        text(ctx, "4倍", RX + 205, 585, 112, RED, align="left", alpha=q)
        text(ctx, "狙われる", RX + 420, 590, 40, INK, align="left", alpha=q)
        pen_circle(ctx, RX + 290, 585, 110, 66, RED, seed=33, width=6,
                   progress=clamp01((t - t6 - 0.55 * dur("c3_6") - 0.3) / 0.45), alpha=q)


K_SHOW = (2, 3, 3.5, 4, 4.5)


def _krow(k):
    return next(r for r in RES["ch3"]["rows"] if abs(r["k"] - k) < 1e-9)


def k_label(k):
    return f"{k:g}倍"


def k_rate(k):
    b = _krow(k)["blue"]
    if 0.4 < b < 0.6:
        return "約50%"
    return f"{b * 100:.0f}%"


K_ROW_T = None


def _k_row_times():
    return [S("c4_3") + 0.6 * dur("c4_3"), S("c4_4") + 0.25 * dur("c4_4"), S("c4_4") + 0.75 * dur("c4_4"),
            S("c4_5") + 0.3 * dur("c4_5"), S("c4_6") + 0.75 * dur("c4_6")]


def R_skill(ctx, t):
    wr(ctx, "青の腕前を上げると？", RX, 160, 48, INK, S("c4_1") + 0.3, t, cps=8)
    wr(ctx, "（矢が当たる確率を 赤の何倍にするか）", RX, 222, 30, PENCIL, S("c4_2") + 0.3, t)
    q = fade(t, S("c4_3"), 0.3)
    if q > 0:
        text(ctx, "青の腕前", RX + 80, 282, 30, PENCIL, bold=False, alpha=q)
        text(ctx, "青の勝率（1万回）", RX + 420, 282, 30, PENCIL, bold=False, alpha=q)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * q))
        ctx.set_line_width(2)
        ctx.move_to(RX, 306)
        ctx.line_to(RX + 700, 306)
        ctx.stroke()
    for i, (k, ts) in enumerate(zip(K_SHOW, _k_row_times())):
        if t < ts:
            continue
        y = 345 + 62 * i
        a = fade(t, ts, 0.3)
        text(ctx, k_label(k), RX + 80, y, 44, INK, alpha=a)
        rate = k_rate(k)
        text(ctx, rate, RX + 420, y, 44, FLAG_B if rate != "0%" else INK, alpha=a)
    t46 = S("c4_6")
    if t >= t46:
        y4 = 345 + 62 * 3
        pen_circle(ctx, RX + 250, y4, 300, 34, RED, seed=44, width=6, progress=clamp01((t - t46 - 0.2) / 0.5))
    t8 = S("c4_8")
    if t >= t8:
        wr(ctx, "人数 2倍 → 腕前 4倍（2の2乗）", RX, 655, 38, RED, t8 + 0.4 * dur("c4_8"), t)


def R_sword(ctx, t):
    wr(ctx, "刀で1対1なら？", RX, 160, 50, INK, S("c5_1") + 0.3, t, cps=8)
    wr(ctx, "向かい合った相手としか戦えない", RX, 228, 34, PENCIL, S("c5_2") + 0.3, t)
    t4 = S("c5_4")
    if t >= t4:
        wr(ctx, f"刀・1対1  残り {fmt(round100(RES['ch4']['rem_mean']))}人", RX, 300, 46, RED, t4 + 0.3 * dur("c5_4"), t)
    t6 = S("c5_6")
    if t >= t6:
        wr(ctx, "10,000 − 5,000 ＝ 5,000", RX, 395, 56, INK, t6 + 0.2, t, cps=10)
        wr(ctx, "→ 引き算で効く", RX + 40, 462, 40, RED, t6 + 0.65 * dur("c5_6"), t)
    t7 = S("c5_7")
    if t >= t7:
        wr(ctx, "刀: 腕前2倍で 互角", RX, 545, 44, INK, S("c5_7b") + 0.2, t)
    t8 = S("c5_8")
    if t >= t8:
        wr(ctx, "互角に必要な腕前  弓 4倍・刀 2倍", RX, 625, 38, INK, t8 + 0.2, t)


ROAD_BARS = None


def _road_rows():
    rows = [(f"幅{fmt(r['W'])}人", r["shoot"]["rem_mean"]) for r in RES["ch5"]["rows"] if r["W"] in (50, 300, 1000, 3000)]
    rows.append(("野原", RES["ch1"]["rem_mean"]))
    return rows


def R_road(ctx, t):
    wr(ctx, "狭い道なら？（弓のまま）", RX, 160, 48, INK, S("c6_1") + 0.4 * dur("c6_1"), t, cps=8)
    tg = E("c6_5")                                     # グラフに入れ替わる
    a1 = out_fade(t, tg - 0.1, 0.4)
    t2 = S("c6_2")
    if t >= t2 and a1 > 0:
        wr(ctx, "道の幅 50人", RX, 240, 46, INK, t2 + 0.3 * dur("c6_2"), t, alpha=a1)
        wr(ctx, "撃てるのは 両軍とも先頭の50人だけ", RX, 300, 34, INK, S("c6_2b") + 0.4 * dur("c6_2b"), t, alpha=a1)
    t3 = S("c6_3")
    if t >= t3 and a1 > 0:
        nar = next(r for r in RES["ch5"]["rows"] if r["W"] == 50)["shoot"]["rem_mean"]
        wr(ctx, f"狭い道（幅50人） 残り 約{fmt(round100(nar))}人", RX, 385, 42, RED, t3 + 0.25 * dur("c6_3"), t, alpha=a1)
    t4 = S("c6_4")
    if t >= t4 and a1 > 0:
        wr(ctx, "先頭では 50 対 50", RX, 455, 42, INK, t4 + 0.6 * dur("c6_4"), t, alpha=a1)
    t5 = S("c6_5")
    if t >= t5:
        wr(ctx, "互角に必要な腕前", RX, 540, 34, PENCIL, t5 + 0.2, t)
        wr(ctx, "野原 4倍 → 狭い道 約2倍", RX, 600, 48, RED, t5 + 0.6 * dur("c6_5"), t, cps=8)
    if t >= tg:                                        # 道の幅と残り（無言のグラフ）
        a = fade(t, tg, 0.4)
        text(ctx, "道の幅と、赤の残り（1万回の平均）", RX, 232, 32, INK, align="left", alpha=a)
        for i, (lab, v) in enumerate(_road_rows()):
            y = 290 + 50 * i
            ts = tg + 0.3 + 0.45 * i
            g = ease_out(clamp01((t - ts) / 0.5))
            text(ctx, lab, RX + 150, y, 30, INK, align="right", alpha=a * fade(t, ts, 0.2))
            w = 360 * v / 10000 * g
            ctx.set_source_rgba(*hexrgb(RED if lab == "野原" else "#e87473", 0.9 * a))
            rrect(ctx, RX + 170, y - 14, max(1.0, w), 28, 5)
            ctx.fill()
            if g > 0.9:
                text(ctx, f"約{fmt(round100(v))}人", RX + 180 + 360 * v / 10000 + 12, y, 30, INK, align="left",
                     alpha=a * fade(t, ts + 0.45, 0.2))


def R_split(ctx, t):
    wr(ctx, "相手を分けたら？", RX, 160, 50, INK, S("c7_1") + 0.3, t, cps=8)
    wr(ctx, "（ショート）80人 vs 50人＋50人 → 約9割 勝つ", RX, 228, 32, PENCIL, S("c7_2b") + 0.6 * dur("c7_2b"), t)
    t3 = S("c7_3")
    if t >= t3:
        a = fade(t, t3 + 0.5 * dur("c7_3"), 0.3)
        text(ctx, "赤1万人の来かた", RX + 120, 300, 30, PENCIL, bold=False, alpha=a)
        text(ctx, "青が半分勝てる人数", RX + 470, 300, 30, PENCIL, bold=False, alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * a))
        ctx.set_line_width(2)
        ctx.move_to(RX, 324)
        ctx.line_to(RX + 700, 324)
        ctx.stroke()
    th = {r["groups"].__len__(): r["N"] for r in RES["ch6"]["thresholds"]}
    rows = (("一度に", th[1], "c7_4", False), ("2つ", th[2], "c7_5", True), ("3つ", th[3], "c7_6", True),
            ("10こ", th[10], "c7_7", True))
    for i, (lab, n, cid, about) in enumerate(rows):
        ts = S(cid) + 0.45 * dur(cid)
        if t < ts:
            continue
        y = 370 + 62 * i
        a = fade(t, ts, 0.3)
        text(ctx, lab, RX + 120, y, 44, INK, alpha=a)
        s_ = f"約{fmt(round100(n))}人" if about else f"{fmt(round100(n))}人"
        text(ctx, s_, RX + 470, y, 44, RED if about else INK, alpha=a)
    t8 = S("c7_8")
    if t >= t8:
        wr(ctx, "刀なら、分けても 1万人のまま", RX, 640, 38, INK, t8 + 0.35 * dur("c7_8"), t)


def R_name(ctx, t):
    t1 = S("c8_1")
    tn = t1 + 0.6 * dur("c8_1")                       # 名前を言うところ
    if t >= tn:
        s_ = "ランチェスターの法則"
        wr(ctx, s_, RX, 170, 66, INK, tn, t, cps=9)
        pen_line(ctx, RX - 4, 215, RX + text_width(s_, 66) + 6, 211, RED, seed=12, width=8,
                 progress=clamp01((t - tn - lf.write_dur(s_)) / 0.4))
    t2 = S("c8_2")
    if t >= t2:
        wr(ctx, "1916年・イギリス  航空機と戦争についての本", RX, 262, 32, PENCIL, t2 + 0.3, t)
    tf = E("c8_1") - 0.2                               # 2つの式を並べて囲む
    if t >= tf:
        a = fade(t, tf, 0.3)
        text(ctx, "撃ち合い", RX + 20, 340, 30, PENCIL, align="left", bold=False, alpha=a)
        wr(ctx, "10,000² − 5,000² ＝ 残り²", RX + 170, 340, 40, INK, tf, t, cps=11)
        text(ctx, "斬り合い", RX + 20, 405, 30, PENCIL, align="left", bold=False, alpha=a)
        wr(ctx, "10,000 − 5,000 ＝ 5,000", RX + 170, 405, 40, INK, tf + 1.0, t, cps=11)
        p = clamp01((t - tf - 2.0) / 0.8)
        for (xa, ya, xb, yb, sd) in ((RX - 10, 300, RX + 720, 300, 91), (RX + 720, 300, RX + 720, 445, 92),
                                     (RX + 720, 445, RX - 10, 445, 93), (RX - 10, 445, RX - 10, 300, 94)):
            pen_line(ctx, xa, ya, xb, yb, RED, seed=sd, width=4, progress=p)
    t3 = S("c8_3")
    if t >= t3:
        wr(ctx, "→ ランチェスター戦略（会社どうしの競争）", RX, 510, 34, INK, t3 + 0.55 * dur("c8_3"), t)
    t4 = S("c8_4")
    if t >= t4:
        wr(ctx, "ただし、単純化したモデル", RX, 590, 40, RED, t4 + 0.3, t)
    t6 = S("c8_6")
    if t >= t6:
        wr(ctx, "実際の記録に 合うものも、合わないものも", RX, 655, 32, PENCIL, t6 + 0.4 * dur("c8_6"), t)


def R_end(ctx, t):
    t1, t2, t3 = S("c9_1"), S("c9_2"), S("c9_3")
    wr(ctx, "兵が2倍なら、2倍強い？", RX, 180, 50, INK, t1 + 0.2, t, cps=8)
    if t >= t2:
        pen_line(ctx, RX - 4, 182, RX + text_width("兵が2倍なら、2倍強い？", 50) + 4, 176, RED, seed=21, width=6,
                 progress=clamp01((t - t2) / 0.4))
        wr(ctx, "撃ち合いなら 4倍", RX, 290, 64, RED, t2 + 0.2, t, cps=8)
    if t >= t3:
        wr(ctx, "→ 狭い場所を選ぶ・相手を分ける", RX, 410, 42, INK, t3 + 0.35 * dur("c9_3"), t)


# ============================================================
# 右ページ下の「2つの数字」（2章で出てから最後まで出しっぱなし）
# ============================================================
NB = (1030, 712, 1800, 905)
CELLX = (1222, 1608)
LBL_Y, VAL_Y = 752, 840
SHOW_MAIN = round100(RES["ch1"]["rem_mean"])          # 約8,500人
SHOW_NAIVE = N_R - N_B                                # 素朴な予想 5,000人


def draw_numbers(ctx, t):
    t0 = S("c2_2") + 0.4 * dur("c2_2")
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3)
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.55 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to((x0 + x1) / 2, y0 + 20)
    ctx.line_to((x0 + x1) / 2, y1 - 20)
    ctx.stroke()
    l1, v1 = "残り（1万回の平均）", f"約{fmt(SHOW_MAIN)}人"
    l2, v2 = "素朴な予想", f"{fmt(SHOW_NAIVE)}人"
    lf.write_on(ctx, l1, CELLX[0], LBL_Y, 30, PENCIL, clamp01((t - t0) / 0.8), align="center", bold=False, alpha=a)
    text(ctx, v1, CELLX[0], VAL_Y, fit(v1, 76, 360), RED, alpha=a * fade(t, t0 + 0.2, 0.3))
    lf.write_on(ctx, l2, CELLX[1], LBL_Y, 30, PENCIL, clamp01((t - t0 - 0.3) / 0.6), align="center", bold=False, alpha=a)
    text(ctx, v2, CELLX[1], VAL_Y, fit(v2, 76, 360), INK, alpha=a * fade(t, t0 + 0.5, 0.3))
    tc = S("c9_1") + 0.4                               # まとめ: 2つの数字を赤で囲む
    if t >= tc:
        for i, cx in enumerate(CELLX):
            pen_circle(ctx, cx, VAL_Y - 4, 190, 58, RED, seed=101 + i, width=6, progress=clamp01((t - tc - 0.5 * i) / 0.5))


# ============================================================
# 付箋・章カード・終了画面・全体
# ============================================================
def overlays(ctx, t, idx):
    if idx == CH_MANY:
        t0 = S("ch1")
        a = fade(t, t0 + 0.15, 0.3) * out_fade(t, S("c2_1") + 0.4, 0.4)
        if a > 0:
            note.banner(ctx, "同じ合戦を1万回", lf.GUTTER, 470, a=a, t_rel=t - t0)
    elif idx != CH_OPEN:
        lf.chapter_card_at(ctx, t, tl, hold=2.0, size=60)
    tq = S("c9_4") + 0.05
    t5 = S("c9_5")
    if t >= tq:
        a = fade(t, tq, 0.35) * (1 - fade(t, t5 - 0.1, 0.3))
        if a > 0:
            sticky(ctx, "あなたなら、5千人で\n1万人に、どう挑みますか？", lf.GUTTER, 560, 56, "yellow", a=a, tilt=-0.02)
    if t >= t5:
        from engine.brand import turtle
        a = fade(t, t5 + 0.1, 0.4)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.82 * fade(t, t5 - 0.1, 0.4)))
        ctx.rectangle(0, 0, lf.W, lf.H)
        ctx.fill()
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t5) % 3.2 < 0.45 else 0.0
        turtle(ctx, lf.GUTTER - 5, 545, 0.62, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        sticky(ctx, "チャンネル登録・高評価 よろしくお願いします", lf.GUTTER, 640, 46, "pink", fg=INK,
               a=fade(t, t5 + 0.3, 0.4), tilt=-0.015)


LEFTS = [L_open, L_many, L_one, L_skill, L_sword, L_road, L_split, L_name, L_end]
RIGHTS = [R_open, R_many, R_one, R_skill, R_sword, R_road, R_split, R_name, R_end]


def _left_clipped(fn):
    def g(ctx, t):
        ctx.save()
        clip_left(ctx)
        fn(ctx, t)
        ctx.restore()
    return g


LEFTS = [_left_clipped(f) for f in LEFTS]


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    page(ctx, t, LEFTS, idx, t0)
    page(ctx, t, RIGHTS, idx, t0)
    draw_numbers(ctx, t)
    overlays(ctx, t, idx)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（ショートの太鼓・矢・ほら貝をコピー。BGM は 0秒から。効果音は控えめ）
# ============================================================
def band_noise(dur_, lo, hi, seed, rms, edge_lo=300.0, edge_hi=1200.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur_)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def taiko(dur_=0.6, seed=1):
    t = _t(dur_)
    f = 50.0 + 90.0 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.0)
    body += 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * np.exp(-t * 14)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = np.convolve(n, np.ones(14) / 14, mode="same")
    skin = n * np.exp(-t * 80) * 1.4
    return (body + skin) * np.minimum(1, t * 900)


def swish(dur_=0.42, seed=1):
    x = band_noise(dur_, 1500.0, 6500.0, seed, 1.0)
    t = _t(dur_)
    u = t / dur_
    env = (u ** 0.5) * ((1 - u) ** 1.6) * 3.0
    return x * env


def landing(dur_=0.3, seed=1):
    n = np.random.default_rng(seed).standard_normal(int(SR * dur_))
    n = np.convolve(n, np.ones(10) / 10, mode="same")
    t = _t(dur_)
    return n * np.exp(-t * 16) * 2.2


def thud(dur_=0.06):
    t = _t(dur_)
    return np.sin(2 * np.pi * 150 * t) * np.exp(-t * 55)


def horagai(dur_=2.4):
    t = _t(dur_)
    f0 = 116.5
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.6 * t)
    x = np.zeros_like(t)
    for n in range(1, 10):
        x += (1.0 / n ** 1.2) * np.sin(2 * np.pi * f0 * n * vib * t + n)
        x += 0.5 * (1.0 / n ** 1.2) * np.sin(2 * np.pi * f0 * 1.006 * n * vib * t)
    att = np.minimum(1, (t / 0.35) ** 1.5)
    rel = np.minimum(1, (dur_ - t) / 0.9) ** 1.2
    breath = np.convolve(np.random.default_rng(5).standard_normal(len(t)), np.ones(30) / 30, mode="same") * 0.35
    y = (x + breath) * att * rel
    return y / max(1e-9, float(np.max(np.abs(y)))) * 0.9


def clang(dur_=0.35, seed=1):
    """キン（刀が打ち合う音）。高めの金属の倍音がすぐ消える"""
    t = _t(dur_)
    rng = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for f, a in ((2380.0, 1.0), (3570.0, 0.6), (5190.0, 0.35)):
        f *= 1 + rng.uniform(-0.04, 0.04)
        x += a * np.sin(2 * np.pi * f * t) * np.exp(-t * (22 + f / 400))
    click = rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.4
    return (x + click) * 0.5


def battle_sfx(mx, bt, vol=1.0, every=1, thud_vol=0.05):
    """一斉射撃ごとに太鼓・矢・着弾、倒れるとき小さくドッ"""
    for i, ts in enumerate(sorted(set(round(r, 3) for r in [f for f in bt.land_t]))):
        pass
    vt = sorted(bt.volley_land)
    for i, tl_ in enumerate(vt):
        if i % every:
            continue
        t0 = tl_ - 0.8
        mx.add(max(0.02, t0), taiko(seed=i + int(t0)), 0.8 * vol)
        mx.add(max(0.0, t0 + 0.04), swish(seed=10 + i), 0.36 * vol)
        mx.add(tl_ - 0.25, landing(seed=20 + i), 0.28 * vol)
    last = -1.0
    for td in sorted(x for x in bt.td if np.isfinite(x)):
        if td - last > 0.04:
            mx.add(td, thud(), thud_vol)
            last = td


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(98.0, 146.8, 196.0, 293.7), vol=0.16), 1.0, bgm=True)
    mx.add(0.0, horagai(2.6), 0.5)
    for i in range(2, 9):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    # 0章
    for cid in ("c0_1", "c0_3", "c0_4"):
        mx.add(S(cid) + 0.3, blip(659.3, 0.12), 0.35)
    mx.add(T_B0 - 0.9, horagai(1.6), 0.35)
    battle_sfx(mx, BATTLE_MAIN, 0.75)   # 戦いの音は声より少し小さく（確認用の動画で -16dB だった）
    mx.add(T_END_MAIN + 0.2, chord([196.0, 293.7, 392.0], 1.6), 0.45)
    mx.add(S("c1_4") + 0.9, bell(392.0, 0.9), 0.4)
    # 2章（早回し → 小さな合戦 → 1万マス）
    mx.add(S("ch1") + 0.15, riser(0.9), 0.5)
    for i, tl_ in enumerate(LAND_MAIN):
        tt = T2A + (tl_ - 0.8 - (T_B0 - 0.4)) / FF2
        if T2A <= tt < T2_SH0:
            mx.add(tt, taiko(0.4, seed=200 + i), 0.45)
            mx.add(tt + 0.02, swish(0.25, seed=210 + i), 0.18)
    for m in MINIS:
        mx.add(m.t0, swish(0.3, seed=int(m.t0 * 10)), 0.12)
        mx.add(m.t_end, blip(784.0, 0.1), 0.22)
    beat(mx, T_GRID0, T_GRID1, bpm=124, vol=0.22, accel=True)
    mx.add(T_GRID0, shimmer(400, T_GRID1 - T_GRID0, seed=2), 0.3)
    mx.add(T_GRID1, thump(), 0.6)
    mx.add(T_GRID1 + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.45)
    mx.add(S("c2_2") + 0.4 * dur("c2_2"), bell(880.0, 1.2), 0.45)
    mx.add(S("c2_4") + 0.4 * dur("c2_4"), bell(659.3, 1.0), 0.4)
    for k in range(3):
        mx.add(E("c2_5") - 0.2 + 0.85 * k + 0.7, blip(784.0, 0.12), 0.35)
    # 3章
    mx.add(T_FA, swish(1.2, seed=301), 0.35)
    mx.add(T_FA + FLY, landing(0.5, seed=302), 0.35)
    mx.add(T_FB, swish(1.0, seed=303), 0.25)
    mx.add(T_FB + FLY, landing(0.4, seed=304), 0.25)
    mx.add(T_SPOT_B + 0.3, blip(659.3, 0.12), 0.35)
    mx.add(T_SPOT_R + 0.3, blip(523.3, 0.12), 0.35)
    mx.add(S("c3_6") + 0.55 * dur("c3_6"), bell(880.0, 1.4), 0.5)
    mx.add(S("c3_10") + 0.5 * dur("c3_10"), chord([392.0, 493.9, 587.3], 1.2), 0.4)
    # 4章
    battle_sfx(mx, BATTLE_K2, 0.45, thud_vol=0.03)
    battle_sfx(mx, BATTLE_K45, 0.45, thud_vol=0.03)
    for i, ts in enumerate(_k_row_times()):
        mx.add(ts, blip(523.3 * 2 ** (i / 6), 0.12), 0.35)
    mx.add(S("c4_6") + 0.2, bell(880.0, 1.2), 0.4)
    # 5章（キン）
    last = -1.0
    for (tdd, sd, ln) in DUEL.death_events:
        if tdd - last > 0.07:
            mx.add(tdd, clang(seed=int(tdd * 100)), 0.16)
            last = tdd
    mx.add(T_D1 + 0.2, chord([196.0, 293.7, 392.0], 1.4), 0.4)
    # 6章（狭い道: 細かい太鼓）
    k = 0
    tt = T_N0
    while tt < T_N1:
        mx.add(tt, taiko(0.3, seed=500 + k), 0.25 if k % 2 else 0.4)
        tt += 0.25
        k += 1
    mx.add(T_N0, band_noise(T_N1 - T_N0, 1500.0, 6000.0, 7, 0.03), 1.0, bgm=True)
    mx.add(E("c6_5") + 0.3, riser(0.6), 0.3)
    # 7章
    battle_sfx(mx, BATTLE_SPLIT, 0.32, thud_vol=0.025)   # 声と重なるので小さめ
    for (m0, m1) in SPLIT_MARCH:
        for j in range(3):
            mx.add(m0 + 0.35 * j, taiko(seed=600 + j), 0.55)
    # 8・9章
    mx.add(S("c8_1") + 0.6 * dur("c8_1"), chord([392.0, 493.9, 587.3], 1.2), 0.45)
    mx.add(S("c9_1") + 0.4, bell(659.3, 1.0), 0.35)
    mx.add(S("c9_4") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S("c9_5") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻（章ごとに要所を2枚以上）
# ============================================================
def still_times():
    ts = [0.0, 0.3, S("c0_2") + 1.5, S("c0_4") + 1.0, T_B0 + 2.5, T_B0 + 5.0, T_END_MAIN + 0.5, S("c0_7") + 1.0,
          S("c1_3") + 0.9 * dur("c1_3"), S("c1_4") + 2.0,
          S("ch1") + 1.0, T2A + 1.5, T2_SH0 + 0.2, T_MINI0 + 1.0, T_MINI0 + 3.6, T_GRID0 + 2.0, T_GRID1 + 0.2,
          S("c2_3") + 0.9 * dur("c2_3"), S("c2_4") + 0.9 * dur("c2_4"), E("g2b") - 0.1, S("c2_6") + 1.5,
          S("ch2") + 0.8, T_FA + 0.7, S("c3_3") + 1.2, T_FB + 0.7, S("c3_5") + 1.5, S("c3_6") + dur("c3_6") + 1.0,
          S("c3_9") + 1.2, S("c3_10") + 1.6, S("c3_12") + 0.9 * dur("c3_12"),
          S("ch3") + 0.8, T_K2 + 1.5, S("c4_4") + 0.9 * dur("c4_4"), T_K45 + 2.0, S("c4_7b") + 1.0, S("c4_8") + 0.9 * dur("c4_8"),
          S("ch4") + 0.8, S("c5_2") + 2.0, T_D0 + 2.5, T_D1 - 0.5, S("c5_6") + 0.9 * dur("c5_6"), S("c5_8") + 0.9 * dur("c5_8"),
          S("ch5") + 0.8, T_N0 + 2.0, T_N1 - 1.0, S("c6_3") + 0.9 * dur("c6_3"), S("c6_5") + 0.9 * dur("c6_5"),
          E("g6b") - 0.2, S("c6_6b") + 1.0,
          S("ch6") + 0.8, S("c7_2b") + 0.9 * dur("c7_2b"), T_S0 + 2.0, SPLIT_MARCH[0][0] + 0.7, SPLIT_MARCH[1][1] + 1.5,
          S("c7_7") + 0.9 * dur("c7_7"), S("c7_8") + 0.9 * dur("c7_8"),
          S("ch7") + 0.8, S("c8_1") + 0.95 * dur("c8_1"), S("c8_3") + 0.9 * dur("c8_3"), S("c8_5") + 0.9 * dur("c8_5"),
          S("c8_6") + 0.9 * dur("c8_6"),
          S("ch8") + 0.8, S("c9_2") + 0.9 * dur("c9_2"), S("c9_3") + 0.9 * dur("c9_3"), S("c9_4") + 1.5,
          S("c9_5") + 1.5, DUR - 0.1]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


# ============================================================
# 文字起こし（バス回と同じ形）と、画面の文字がどれだけの間見えているか
# ============================================================
def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・映像だけ）")
        else:
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def text_spans(step=0.25, scale=0.25):
    """画面の文字（字幕を除く）が見えている区間。core.text のログを使う"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    seen = {}
    n = int(DUR / step)
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        for e in core._LOG:
            seen.setdefault(e[1], []).append(t)
        core._LOG = None
    spans = []
    for s_, ts in seen.items():
        a = b = ts[0]
        for x in ts[1:] + [1e9]:
            if x - b > step * 1.5:
                spans.append((a, b + step, s_))
                a = x
            b = x
    spans.sort()
    return spans


def write_screen_text(path, spans):
    rows = ["# 画面の文字（字幕を除く）と、見えている区間。0.25秒ごとに描いて調べた", ""]
    for a, b, s_ in spans:
        mark = "  ←短い" if b - a < 1.5 and not any(ch.isdigit() for ch in s_) else ""
        rows.append(f"{_ts(a)}〜{_ts(b)}（{b - a:4.1f}秒） {s_}{mark}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("画面の文字:", path)


def update_description():
    """publish/kassen-long/description.txt の「▼チャプター」の段を、書き出した chapters.txt の時刻に差し替える"""
    f = Path(__file__).resolve().parents[1] / "publish" / SLUG / "description.txt"
    if not f.exists():
        return
    lines = f.read_text(encoding="utf-8").split("\n")
    i = lines.index("▼チャプター")
    j = i + 1
    while j < len(lines) and lines[j].strip():
        j += 1
    lines[i + 1:j] = tl.chapter_text().split("\n")
    f.write_text("\n".join(lines), encoding="utf-8")
    print("概要欄のチャプターを差し替え:", f)


# ============================================================
# 場面の照合（画面に出す数字が data.json と合っているか・見本の絵の体数）
# ============================================================
def _win_rate(d):
    w = d["win"]
    return w / d["n"] if w > 1 else w


def scene_checks():
    ch1, ch4 = RES["ch1"], RES["ch4"]
    th = {len(r["groups"]): r["N"] for r in RES["ch6"]["thresholds"]}
    w = {r["W"]: r for r in RES["ch5"]["rows"]}
    checks = [
        ("画面「約8,500人」＝1万回の平均の百の位", SHOW_MAIN, 8500, 0),
        ("画面「1,500人しか失わない」", round100(N_R - ch1["rem_mean"]), 1500, 0),
        ("画面「青が勝った回数 0回」", ch1["blue"], 0, 0),
        ("画面 乱数を変えた3回がどれも約8,500人", float(all(round100(r["rem_mean"]) == 8500 for r in ch1["runs"])), 1, 0),
        ("画面 乱数を変えた3回の青の勝ち 0回", float(sum(r["blue"] for r in ch1["runs"])), 0, 0),
        ("画面「約8,700人」＝ √(10000²−5000²) の百の位", round100(math.sqrt(N_R ** 2 - N_B ** 2)), 8700, 0),
        ("画面 1万マスの値の数", len(GRID_VALS), 10000, 0),
        ("画面 1万マスの平均（度数分布から並べ直し）＝ ch1 の平均", float(GRID_VALS.mean()), ch1["rem_mean"], 1e-6),
        ("画面 腕前2倍 0%", float(_krow(2)["blue"]), 0, 0),
        ("画面 腕前3倍 0%", float(_krow(3)["blue"]), 0, 0),
        ("画面 腕前3.5倍 0%", float(_krow(3.5)["blue"]), 0, 0),
        ("画面 腕前4倍 約50%（45〜55%）", float(_krow(4)["blue"]), 0.5, 0.05),
        ("画面 腕前4.5倍 100%", float(_krow(4.5)["blue"]), 1, 0),
        ("画面「刀・1対1 残り 5,000人」", round100(ch4["rem_mean"]), 5000, 0),
        ("画面「刀: 腕前2倍で互角」（互角の k）", float(ch4["k50"]), 2.0, 0.1),
        ("画面「狭い道（幅50人） 残り 約5,000人」", round100(w[50]["shoot"]["rem_mean"]), 5000, 0),
        ("画面 狭い道の互角の腕前「約2倍」", float(w[50]["shoot"]["k50"]), 2.0, 0.1),
        ("画面 幅300人 約5,100人", round100(w[300]["shoot"]["rem_mean"]), 5100, 0),
        ("画面 幅1,000人 約5,500人", round100(w[1000]["shoot"]["rem_mean"]), 5500, 0),
        ("画面 幅3,000人 約6,400人", round100(w[3000]["shoot"]["rem_mean"]), 6400, 0),
        ("画面 分けたら 一度に 10,000人", round100(th[1]), 10000, 0),
        ("画面 分けたら 2つ 約7,200人", round100(th[2]), 7200, 0),
        ("画面 分けたら 3つ 約5,900人", round100(th[3]), 5900, 0),
        ("画面 分けたら 10こ 約3,400人", round100(th[10]), 3400, 0),
        ("画面 ショートの 80 vs 50＋50「約9割」", round(_win_rate(RES["sm"]["twist"]["split"]), 1), 0.9, 0),
        # 絵（1体＝100人）
        ("絵 0章の見本の赤の生き残り ＝ ceil(8,490÷100)", BATTLE_MAIN.alive("R", 1e9), figs(SAMPLE_MAIN["red_left"]), 0),
        ("絵 0章の見本の青は全滅", BATTLE_MAIN.alive("B", 1e9), 0, 0),
        ("絵 0章の見本の決着が無音の区間のうちに終わる", float(T_END_MAIN < E("g0")), 1, 0),
        ("絵 2章の早回しが縮める前に終わる", float(tau2(T2_SH0) > T_END_MAIN), 1, 0),
        ("絵 腕前2倍の見本: 赤の生き残り", BATTLE_K2.alive("R", 1e9), figs(SAMPLE_K2["red_left"]), 0),
        ("絵 腕前4.5倍の見本: 青の生き残り", BATTLE_K45.alive("B", 1e9), figs(SAMPLE_K45["blue_left"]), 0),
        ("絵 腕前2倍の見本は赤の勝ち（1万回の平均 6,738 の±1%）", SAMPLE_K2["red_left"], _krow(2)["rem_mean"], 0.01 * _krow(2)["rem_mean"]),
        ("絵 腕前4.5倍の見本は青の勝ち（1万回の平均 1,436 の±1%）", SAMPLE_K45["blue_left"], _krow(4.5)["rem_mean"], 0.01 * _krow(4.5)["rem_mean"]),
        ("絵 刀の見本: 赤の生き残り", int(np.sum(~np.isfinite(DUEL.td["R"]))), figs(SAMPLE_DUEL["red_left"]), 0),
        ("絵 刀の見本: 青は全滅", int(np.sum(~np.isfinite(DUEL.td["B"]))), 0, 0),
        ("絵 狭い道の見本: 赤の生き残り", int(np.sum(~np.isfinite(NARROW.td["R"]))), figs(SAMPLE_NARROW["red_left"]), 0),
        ("絵 狭い道の見本: 青は全滅", int(np.sum(~np.isfinite(NARROW.td["B"]))), 0, 0),
        ("絵 分けた見本: 迎え撃つ青の生き残り", BATTLE_SPLIT.alive("R", 1e9), figs(SAMPLE_SPLIT["red_left"]), 0),
        ("絵 分けた見本: 赤3隊とも全滅", sum(BATTLE_SPLIT.alive(f"G{i}", 1e9) for i in range(3)), 0, 0),
        ("絵 3章: 青1体に赤の矢がちょうど2本", float(np.all(np.bincount(FOCUS_RED_TGT, minlength=50) == 2)), 1, 0),
        ("絵 3章: 赤2体に青の矢が1本（50組すべて）", float(len(set(FOCUS_BLUE_TGT.tolist())) == 50), 1, 0),
        ("長さ 7分00秒〜8分30秒", DUR, 465, 45),
    ]
    check_answers(checks)
    print("場面の照合 OK")


# ============================================================
# 書き出し
#   python sims/kassen-long.py --check        数字の照合だけ（モデル）
#   python sims/kassen-long.py --readings     合成エンジンが読むカナ（数字の読み違いの確認）
#   python sims/kassen-long.py --stills       要所の静止画と sheet.png（out/kassen-long/stills/）。--at 12.3,40.5 なら指定した秒だけ
#   python sims/kassen-long.py --textcheck    画面の文字が見えている区間（out/kassen-long/screen_text.txt）
#   python sims/kassen-long.py --scenecheck   場面の照合だけ（画面の数字・絵の体数・長さ）
#   python sims/kassen-long.py --preview      960×540・15fps の確認用
#   python sims/kassen-long.py                照合 → 本番（mp4・chapters.txt・transcript.long.txt）
#   --fake-voice をつけると、AivisSpeech なしで長さを見積もる（無音。静止画の確認用。本番では使えない）
# ============================================================
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for i, (t0_, title) in enumerate(tl.chapters):
        print(f"  {lf._mmss(t0_)} {title}")
    if "--readings" in sys.argv:
        from engine import voice
        for it in tl.items:
            if isinstance(it, lf.Line):
                shown, spoken = split_reading(it.text)
                print(f"{it.id}: {shown}\n    → {voice.read_aloud(spoken)}")
        raise SystemExit
    if "--scenecheck" in sys.argv:                    # 場面の照合だけ（画面の数字・絵の体数・長さ）
        scene_checks()
        raise SystemExit
    if "--textcheck" in sys.argv:
        write_screen_text(OUT / "screen_text.txt", text_spans())
        raise SystemExit
    if "--stills" in sys.argv:
        if "--at" in sys.argv:
            ts = [float(x) for x in sys.argv[sys.argv.index("--at") + 1].split(",")]
            for tt in ts:
                lf.still(draw, tt, OUT / f"at_{tt:06.1f}.png")
        else:
            lf.stills(draw, still_times(), OUT / "stills")
    elif "--preview" in sys.argv:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
    else:
        if FAKE:
            raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
        check(RES)
        scene_checks()
        lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
        write_transcript(OUT / "transcript.long.txt")
        update_description()
        write_screen_text(OUT / "screen_text.txt", text_spans())
        print("完成:", OUT / f"{SLUG}.mp4")
