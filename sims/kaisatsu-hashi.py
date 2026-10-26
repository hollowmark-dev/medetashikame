"""駅の改札、空いている端と人の多い真ん中、どっちが早く抜けられる？ 同じ所から同時に歩き出して1万回。— 2026-10-22 作成（公開予定 10/26）

モデル（改札機6台が1列に並ぶ。混む朝。1回ごとに人数・人の来かた・歩く速さ・通る時間をでたらめに変える）
  主役2人 : 同じ場所から同時に歩き出す。同じ速さ（1.2〜1.4 m/秒）・同じ通る時間（同じ人がどちらを選んでもいい形にして、場所だけをくらべる）。
            A… 近い真ん中（3・4番）の列の「最後」に並ぶ。 B… 端（1番か6番）の空いた改札まで歩いて、そこに並ぶ。
            スタート地点は 改札から 8.5〜10.5 m 手前（仮定）。横は 3番と4番の境目から ±0.45台ぶんの中（仮定）。2人は 0.7 m 離れて並んで立つ（端へ行く人は端の側）。
            歩くのは 直線。並ぶ場所は「いま並んでいる人の最後尾」。端は、スタートのときに人が少ないほう（同じなら近いほう）を選ぶ。
  改札1台の通過時間 : 1人あたり 対数正規（真ん中 1.17秒・ばらつき 0.22）を 1.0〜2.4秒で切る（平均 約1.3秒）。
            根拠: ICカード対応の改札は「1分間に最大60人」＝1人1秒（ITmedia 2024-12 の次期ICカード改札の記事
            https://www.itmedia.co.jp/news/article/2412/17/1241217170/3 ）。英国の鉄道安全基準の計画値は 1台1分25人（混雑時の平均・余裕込み）＝2.4秒
            （https://en.wikipedia.org/wiki/Automated_fare_collection ）、ロンドンのICカードで 1分40人＝1.5秒
            （Cubic の TfL 事例 https://go.cubic.com/hubfs/CTS%20Collateral/CTS/Case%20Studies/Cubic%20Transportation%20Systems%20Transport%20for%20London%20Case%20Study.pdf ）。
            → 1.0〜2.4秒に収まるようにした。
  ときどき止まる人 : 2%の人が 4〜10秒止まる（残高不足などでエラー→引き返す。仮定。主役は止まらない）。
  人の来かた（混む朝）:
            歩き出す8.35秒前に、列の長さを配る（仮定）: 真ん中（3・4番）は 3〜8人、その外（2・5番）は 1〜5人、端（1・6番）は 0〜2人。
            そのあと後ろから人が来る（1秒あたりの人数。仮定）: 3・4番 0.68人、2・5番 0.45人、1・6番 0.15人。近い改札（真ん中寄り）を選ぶ人が多い、という形。
            → 主役が並ぶときに見える列の長さ: 真ん中 平均◯人・端 平均◯人（--model で出す）。
  列に並ぶと前の人に合わせて進む（先頭が改札を通り始めたら、次の人が1つ前へ）。列は1台ずつ「先に並んだ順」。
  測るもの : 歩き出してから、改札を抜けるまでの時間（A と B）。
  ひねり   : 「では、ガラガラの時間なら？」 同じ1万回で、人の来かたを少なくする（列は 0〜1人・来るのは 1秒あたり 0.10人、端は 0.07人）。

問い: 「駅の改札、端と真ん中、/ どっちが早く抜けられる？」 端 ／ ほぼ同じ ／ 真ん中（並びは ORDER で決める。下の「記号」）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「端の人が先に抜けた回」の割合 p と、抜けた時刻の差（真ん中 − 端）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 2秒 なら「端」、p ≤ 40% かつ g ≤ −2秒 なら「真ん中」、それ以外は「ほぼ同じ」。
      結果がどれでも、そのまま答えにする。
記号: 10/25 の回の正解が B なので、この回の正解は B 以外にする。計算が終わってから、選択肢の並び（ORDER）だけ入れ替える。規則と計算は変えない。
締め: 「あなたは、端まで歩く派？ 近くに並ぶ派？」（答えは出さない）

乱数の種は見本（並んで歩く2人）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "kaisatsu-hashi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
N_LANE = 6
PITCH = (0.90, 1.00)                              # 改札1台の幅（m）
DIST_L = (8.5, 10.5)                              # スタートから改札までの距離（m。仮定）
START_GAP = 0.35                                  # 2人が立つ位置は 真ん中の点から 横に ±0.35 m（0.7 m 離れて並ぶ）
XS_K = 0.45                                       # スタートの横位置は 3番と4番の境目から ±XS_K 台ぶん
WALK = (1.2, 1.4)                                 # 歩く速さ（m/秒）
SVC_MED, SVC_SIG, SVC_CLIP = 1.17, 0.22, (1.0, 2.4)   # 1人の通過時間（秒）
P_STUCK, STUCK = 0.02, (4.0, 10.0)                # 止まる人の割合と、止まる時間（秒）
Q_GAP = 0.70                                      # 列で1人ぶんの間隔（m）
D_HEAD = 0.50                                     # 先頭の人が立つ位置（改札から m）
VAC = 0.40                                        # 通過時間のうち、進み始めるまでの割合（先頭が動いたら次の人が前へ）
PRE = 8.35                                        # 冒頭（歩き出す前）の秒。列はこの間も流れている
# 列の長さと人の来かた（種類ごと）: 歩き出す PRE 秒前の人数（両端を含む）と、1秒あたりの来る人数
PROFILES = {
    "busy": {"mid": ((3, 8), 0.68), "out": ((1, 5), 0.45), "edge": ((0, 2), 0.15)},
    "quiet": {"mid": ((0, 1), 0.10), "out": ((0, 1), 0.08), "edge": ((0, 1), 0.07)},
}
KIND = {1: "edge", 2: "out", 3: "mid", 4: "mid", 5: "out", 6: "edge"}
T_END = 40.0                                      # この秒まで人を流す

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 2.0
NAMES = ["端", "ほぼ同じ", "真ん中"]              # 規則での番号 0・1・2


def answer_by_rule(p_edge, gap_med):
    """p_edge = 端の人が先に抜けた回の割合、gap_med = (真ん中 − 端) の抜けた時刻の差の真ん中の値（秒）。返り値: NAMES の番号"""
    if p_edge >= RULE_HI and gap_med >= RULE_GAP:
        return 0                                  # 端
    if p_edge <= RULE_LO and gap_med <= -RULE_GAP:
        return 2                                  # 真ん中
    return 1                                      # ほぼ同じ


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def service(rng, n):
    """通過時間（秒）。対数正規を 1.0〜2.4秒で切る（範囲の外は引き直す）"""
    out = np.empty(0)
    while len(out) < n:
        x = rng.lognormal(math.log(SVC_MED), SVC_SIG, max(8, 3 * n))
        out = np.concatenate([out, x[(x >= SVC_CLIP[0]) & (x <= SVC_CLIP[1])]])
    return out[:n]


def schedule(a, b, x, f0=None):
    """1列の時刻表。a 到着・b 通過の基本時間・x 止まる時間。f0 は先頭の人（通過の途中から始まる）の抜ける時刻。
    返り値: start 通り始める・f 抜けた・v 進み出す（列の次の人が前へ）・tap ピッとタッチして扉が開く"""
    n = len(a)
    start = np.zeros(n)
    f = np.zeros(n)
    for j in range(n):
        if j == 0 and f0 is not None:
            f[0] = f0
            start[0] = f0 - (b[0] + x[0])
        else:
            start[j] = max(a[j], f[j - 1] if j else -1e9)
            f[j] = start[j] + b[j] + x[j]
    return start, f, start + x + VAC * b, start + x + 0.2 * b


def make_lane(rng, kind, profile):
    """1列ぶん。人は 到着時刻 a の順。返り値 dict(a, b, x, start, f, v, tap, f0)。
    a … 列に着いた時刻（−PRE より前から並んでいた人は −PRE−0.05×順）、b … 通過の基本時間、x … 止まる時間（ふつうは0）、
    start … 改札を通り始める時刻、f … 抜けた時刻、v … 先頭から進み出す時刻（次の人が前へ）、tap … ピッと鳴って扉が開く時刻"""
    (m_lo, m_hi), lam = PROFILES[profile][kind]
    m0 = int(rng.integers(m_lo, m_hi + 1))
    t0 = -PRE
    n_arr = int(rng.poisson(lam * (T_END - t0)))
    a = np.concatenate([t0 - 0.05 * np.arange(m0, 0, -1) - 0.01, np.sort(rng.uniform(t0, T_END, n_arr))])
    n = len(a)
    b = service(rng, n)
    x = (rng.uniform(size=n) < P_STUCK) * rng.uniform(STUCK[0], STUCK[1], n)
    resid = float(rng.uniform(0.1, 1.0))
    f0 = t0 + resid * (b[0] + x[0]) if (m0 > 0 and n > 0) else None
    start, f, v, tap = schedule(a, b, x, f0)
    return dict(a=a, b=b, x=x, start=start, f=f, v=v, tap=tap, f0=f0, m0=m0)


def lane_cnt(lane, t):
    """時刻 t（配列可）に列に並んでいる人数（進み始めた人は、0.5秒かけて抜けていく）"""
    t = np.atleast_1d(np.asarray(t, float))
    if len(lane["a"]) == 0:
        return np.zeros_like(t)
    arrived = (lane["a"][None, :] <= t[:, None])
    left = smooth((t[:, None] - lane["v"][None, :]) / 0.5)
    return (arrived * (1 - left)).sum(1)


TG = np.arange(0.0, 30.0, 0.02)                   # 歩く時間の探し方の刻み


def walk_to(lane, xs, L, xl, v):
    """直線で (xl, 列の最後尾) まで歩く。最後尾は歩いている間にも動く。返り値: 着く時刻・着く位置(横, 改札から)"""
    d_tail = D_HEAD + Q_GAP * lane_cnt(lane, TG)
    g = v * TG - np.hypot(xl - xs, L - d_tail)
    k = int(np.argmax(g >= 0))
    t = float(TG[k])
    return t, (xl, float(d_tail[k]))


def trial(seed_i, profile="busy", full=False):
    """1回ぶん。full=True なら絵のために全部の列（と人）も作る"""
    rng = np.random.default_rng(seed_i)
    p = float(rng.uniform(*PITCH))
    L = float(rng.uniform(*DIST_L))
    xs = float(rng.uniform(-XS_K * p, XS_K * p))
    v = float(rng.uniform(*WALK))
    s_own = float(service(rng, 1)[0])
    xl = {k: (k - 3.5) * p for k in range(1, N_LANE + 1)}
    lanes = {k: make_lane(rng, KIND[k], profile) for k in (1, 6)}
    c1, c6 = float(lane_cnt(lanes[1], 0.0)[0]), float(lane_cnt(lanes[6], 0.0)[0])
    if abs(c1 - c6) > 1e-9:
        lb = 1 if c1 < c6 else 6                   # 端は、人が少ないほう（同じなら近いほう）
    else:
        lb = 1 if abs(xl[1] - xs) <= abs(xl[6] - xs) else 6
    sg = 1 if lb == 6 else -1                      # 2人は 0.7 m 離れて並んで立つ。端へ行く人は、その端の側
    xs_a, xs_b = xs - sg * START_GAP, xs + sg * START_GAP
    la = 3 if xs_a < 0 else 4                      # A は近い真ん中
    lanes[la] = make_lane(rng, KIND[la], profile)
    res = {}
    for key, k, x0 in (("a", la, xs_a), ("b", lb, xs_b)):
        ln = lanes[k]
        ta, e = walk_to(ln, x0, L, xl[k], v)
        ahead = int(np.searchsorted(ln["a"], ta, side="right"))
        last_f = float(ln["f"][ahead - 1]) if ahead > 0 else -1e9
        st = max(ta, last_f)
        n_ahead = int(np.sum((ln["a"] <= ta) & (ln["f"] > ta)))
        stuck_ahead = bool(np.any(ln["x"][:ahead] > 0)) if ahead else False
        d = math.hypot(e[0] - x0, L - e[1])
        res[key] = dict(lane=k, x0=x0, t_arr=ta, end=e, start=st, fin=st + s_own, n_ahead=n_ahead, wait=st - ta, dist=d,
                        t_walk=ta, stuck_ahead=stuck_ahead)
    out = dict(p=p, L=L, xs=xs, v=v, s_own=s_own, xl=xl, la=la, lb=lb, A=res["a"], B=res["b"], lanes=lanes, seed=seed_i,
               profile=profile)
    if full:
        r2 = np.random.default_rng(list(seed_i) + [9])
        for k in range(1, N_LANE + 1):
            if k not in lanes:
                lanes[k] = make_lane(r2, KIND[k], profile)
    return out


def run(seed, profile="busy", n=N_TRIAL):
    rows = []
    for i in range(n):
        r = trial([seed, i], profile)
        A, B = r["A"], r["B"]
        rows.append((A["fin"], B["fin"], A["t_arr"], B["t_arr"], A["wait"], B["wait"], A["n_ahead"], B["n_ahead"],
                     B["dist"] - A["dist"], r["la"], r["lb"], r["v"], r["s_own"], r["L"], r["xs"],
                     float(A["stuck_ahead"]), float(B["stuck_ahead"])))
    a = np.array(rows, float)
    keys = ["fin_m", "fin_e", "arr_m", "arr_e", "wait_m", "wait_e", "n_m", "n_e", "extra", "la", "lb", "v", "s_own", "L", "xs",
            "stuck_m", "stuck_e"]
    return {k: a[:, i] for i, k in enumerate(keys)}


SEED_MAIN, SEED_QUIET = 20261026, 20261027
_RES = {}


def results(profile="busy"):
    if profile not in _RES:
        cache = OUT / "cache" / f"model_{profile}_{SEED_MAIN if profile == 'busy' else SEED_QUIET}_v3.npz"
        if cache.exists():
            _RES[profile] = dict(np.load(cache))
        else:
            r = run(SEED_MAIN if profile == "busy" else SEED_QUIET, profile)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **r)
            _RES[profile] = r
    return _RES[profile]


def stats(r):
    gap = r["fin_m"] - r["fin_e"]                  # 正 ＝ 端のほうが先
    win_e = r["fin_e"] < r["fin_m"]
    return dict(p_edge=float(np.mean(win_e)), n_edge=int(win_e.sum()), n_mid=int((~win_e).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                fin_m_med=float(np.median(r["fin_m"])), fin_e_med=float(np.median(r["fin_e"])),
                fin_m_mean=float(r["fin_m"].mean()), fin_e_mean=float(r["fin_e"].mean()),
                wait_m=float(r["wait_m"].mean()), wait_e=float(r["wait_e"].mean()),
                walk_m=float(r["arr_m"].mean()), walk_e=float(r["arr_e"].mean()),
                n_m=float(r["n_m"].mean()), n_e=float(r["n_e"].mean()),
                n_m_q=np.percentile(r["n_m"], [5, 25, 50, 75, 95]), n_e_q=np.percentile(r["n_e"], [5, 25, 50, 75, 95]),
                extra_q=np.percentile(r["extra"], [5, 25, 50, 75, 95]))


def shown():
    return stats(results("busy"))


def shown_quiet():
    return stats(results("quiet"))


def report():
    for prof in ("busy", "quiet"):
        sh = stats(results(prof))
        print(f"[{prof}] 端が先 {sh['p_edge']:.4f}（{sh['n_edge']}回 / 真ん中が先 {sh['n_mid']}回）  差の中央値 {sh['gap_med']:+.2f}秒  "
              f"平均 {sh['gap_mean']:+.2f}  10/25/75/90% {np.round(sh['gap_q'], 1)}   答え {NAMES[answer_by_rule(sh['p_edge'], sh['gap_med'])]}")
        print(f"   抜けるまで 中央値 真ん中 {sh['fin_m_med']:.1f}秒 / 端 {sh['fin_e_med']:.1f}秒   平均 {sh['fin_m_mean']:.1f} / {sh['fin_e_mean']:.1f}")
        print(f"   歩く平均 真ん中 {sh['walk_m']:.1f}秒 / 端 {sh['walk_e']:.1f}秒   並んで待つ平均 真ん中 {sh['wait_m']:.1f}秒 / 端 {sh['wait_e']:.1f}秒")
        print(f"   並ぶとき前にいた人 真ん中 平均{sh['n_m']:.1f}人 5/25/50/75/95% {sh['n_m_q']}  端 平均{sh['n_e']:.1f}人 {sh['n_e_q']}")
        print(f"   端のほうの余分な歩き 5/25/50/75/95% {np.round(sh['extra_q'], 1)} m")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（同じ所から歩き出す2人）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 前にいた人が 真ん中 5〜6人・端 0人、止まる人はいない、スタートまでの距離 8.6〜9.2 m（絵に収まる）、
    端の余分な歩きが 3〜5 m。その中で、抜けるまでの時間が 1万回の真ん中の値（真ん中 約12秒・端 約8.6秒）に近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results("busy")
    sh = shown()
    ok = ((r["n_m"] >= 5) & (r["n_m"] <= 6) & (r["n_e"] == 0) & (r["stuck_m"] == 0) & (r["stuck_e"] == 0)
          & (r["L"] >= 8.6) & (r["L"] <= 9.2) & (r["extra"] >= 3.0) & (r["extra"] <= 5.0))
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    sc = np.abs(r["fin_e"][cand] - sh["fin_e_med"]) / 0.4 + np.abs(r["fin_m"][cand] - sh["fin_m_med"]) / 0.6 \
        + np.abs(np.abs(r["xs"][cand]) - 0.25)
    best = int(cand[int(np.argmin(sc))])
    tr = trial([SEED_MAIN, best], "busy", full=True)
    assert abs(tr["A"]["fin"] - r["fin_m"][best]) < 1e-9 and abs(tr["B"]["fin"] - r["fin_e"][best]) < 1e-9
    _SAMPLE = dict(i=best, tr=tr, fin_m=tr["A"]["fin"], fin_e=tr["B"]["fin"], gap=tr["A"]["fin"] - tr["B"]["fin"],
                   A=tr["A"], B=tr["B"])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    tr = s["tr"]
    print("見本", s["i"], "A（真ん中）レーン", tr["la"], "到着", round(tr["A"]["t_walk"], 2), "前", tr["A"]["n_ahead"], "待ち", round(tr["A"]["wait"], 2),
          "抜ける", round(tr["A"]["fin"], 2), "／ B（端）レーン", tr["lb"], "到着", round(tr["B"]["t_walk"], 2), "前", tr["B"]["n_ahead"],
          "抜ける", round(tr["B"]["fin"], 2), " L", round(tr["L"], 2), "xs", round(tr["xs"], 2), "v", round(tr["v"], 2), "p", round(tr["p"], 2))
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, stills  # noqa: E402

note.use()
note.DATE = "10.26"                               # 日付欄（公開予定日）

COL_E, INK_E = "#8fbbe8", "#2f63a8"               # 端（青）
COL_M, INK_M = "#f4ad6a", "#b8601a"               # 真ん中（橙）
SKIN = "#f6dcc6"
SHIRTS = ["#b8b3a2", "#a7bfa5", "#c7a8b8", "#c9b98e", "#9fb3b8", "#c8a79a", "#b2a9c9", "#a8a8a0"]
HAIRS = ["#3a2f2a", "#5a4632", "#2b2b33", "#7a5a3a", "#8c8c8c", "#4a3b2c"]
PANTS = ["#4a5878", "#5d5a52", "#3f4a5c", "#6b5d4f", "#4d4d55"]
SLAB = "#c9bfa9"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
assert abs(T_GO - PRE) < 1e-9                     # 列は冒頭の間も流れていて、歩き出す瞬間が計算の0秒
SLOW_SPAN = 2.5                                   # 先に抜ける人の何秒前（実際の秒）から等倍にするか
RACE_LEN = 9.6                                    # T_GO から2人とも抜けるまで（動画の秒）
BIG_Q = ["駅の改札、端と真ん中、", "どっちが早く抜ける？"]
DETAIL = "改札6台。空いている端と、人の多い真ん中"
ORDER = [0, 1, 2]                                 # 画面の A・B・C に並べる NAMES の番号（端・ほぼ同じ・真ん中）。正解を B にしない
LABELS = [NAMES[i] for i in ORDER]
CORRECT = 0                                       # answer_by_rule で計算結果から決めた答え（画面での位置）。ずれたら run_checks が止める
TAG = {"e": "ABC"[ORDER.index(0)], "m": "ABC"[ORDER.index(2)]}
NAME = {"e": "端", "m": "真ん中"}
COL = {"e": COL_E, "m": COL_M}
INKC = {"e": INK_E, "m": INK_M}

# ---------- 場面（場面の座標: 幅1080・高さ SCENE_H。画面へは layout で縮めて置く） ----------
SCENE_H = 1015.0
CX = 575.0
Y_G = 640.0                                       # 改札の線（奥行き0）の足元の y
KX = 169.0                                        # 横 1 m ぶんの px（改札の線の上）
K_D = 58.0                                        # 奥行き 1 m ぶんの px（改札の線の上）
D0 = 25.0                                         # 遠近の強さ
PERSON_PX = 240.0                                 # 人の背の高さ（px。改札の線の上）
GATE_PX = 143.0                                   # 改札機の高さ（px）。人の背の 1.7 分の 1
GATE_W = 0.34                                     # 改札機の幅（m）
LAY_INTRO = (1.0, 705.0)                          # (縮める倍率, 場面の上端の y)
LAY_RACE = (1.0, 585.0)
PIT = 0.95                                        # 絵の改札1台の幅（見本の値を setup で入れる）


def proj(xm, d):
    """横 xm（改札の列の真ん中から m）・奥行き d（改札から手前へ m）→ 場面の (x, y, 縮み)"""
    s = 1.0 / (1.0 + d / D0)
    return CX + xm * KX * s, Y_G - K_D * d * s, s


def smooth_s(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


# ---------- 人と列の絵のための準備 ----------
_VIS = None


def look_of(k, j, prot=""):
    if prot == "e":
        return dict(shirt=COL_E, hair="#2b2b33", pants="#3f4a5c", style=0, h=1.2)
    if prot == "m":
        return dict(shirt=COL_M, hair="#3a2f2a", pants="#4a5878", style=1, h=1.2)
    r = np.random.default_rng([3, k, j])
    return dict(shirt=SHIRTS[int(r.integers(len(SHIRTS)))], hair=HAIRS[int(r.integers(len(HAIRS)))],
                pants=PANTS[int(r.integers(len(PANTS)))], style=int(r.integers(3)), h=float(r.uniform(0.93, 1.05)))


def visual():
    """見本の1万回中の1回から、列ごとの人のリスト（主役2人を入れた時刻表）を作る"""
    global _VIS
    if _VIS is not None:
        return _VIS
    s = sample()
    tr = s["tr"]
    xl = tr["xl"]
    lanes = {}
    for k in range(1, N_LANE + 1):
        ln = tr["lanes"][k]
        a, b, x = ln["a"].copy(), ln["b"].copy(), ln["x"].copy()
        prot = np.array([""] * len(a), dtype=object)
        for key, info in (("m", tr["A"]), ("e", tr["B"])):
            if info["lane"] == k:
                j = int(np.searchsorted(a, info["t_walk"]))
                a, b, x = np.insert(a, j, info["t_walk"]), np.insert(b, j, tr["s_own"]), np.insert(x, j, 0.0)
                prot = np.insert(prot, j, key)
        start, f, v, tap = schedule(a, b, x, ln["f0"])
        n = len(a)
        r = np.random.default_rng([5, k])
        jit = r.uniform(-0.10, 0.10, n)
        side = np.where(r.uniform(size=n) < 0.5, -1, 1)
        vw = r.uniform(1.15, 1.45, n)
        dx0 = r.uniform(1.2, 2.6, n) * (1 if xl[k] > 0 else -1)      # 来る人は両側の奥から斜めに入ってくる（真ん中の奥は主役の場所）
        d0 = r.uniform(8.5, 11.5, n)
        slot_a = np.array([float(np.sum(1 - smooth((a[j] - v[:j]) / 0.5))) if j else 0.0 for j in range(n)])
        ex = xl[k] + jit
        ed = D_HEAD + Q_GAP * slot_a
        spawn = np.full(n, -1e9)
        w0 = np.zeros(n)                                 # 歩き出す時刻（直線で歩く時間の始まり）
        px0, pd0 = np.zeros(n), np.zeros(n)
        for j in range(n):
            if prot[j]:
                px0[j], pd0[j] = (tr["A"] if prot[j] == "m" else tr["B"])["x0"], tr["L"]
                jit[j] = 0.0
                ex[j] = xl[k]
                spawn[j] = -1e9                          # 主役は最初から立っている
                w0[j] = 0.0
                vw[j] = tr["v"]
            elif a[j] > -PRE:
                px0[j], pd0[j] = xl[k] + dx0[j], d0[j]
                spawn[j] = a[j] - math.hypot(px0[j] - ex[j], pd0[j] - ed[j]) / vw[j]
                w0[j] = spawn[j]
        looks = [look_of(k, j, prot[j]) for j in range(n)]
        lanes[k] = dict(a=a, b=b, x=x, start=start, f=f, v=v, tap=tap, prot=prot, jit=jit, side=side, vw=vw, spawn=spawn, w0=w0,
                        px0=px0, pd0=pd0, ex=ex, ed=ed, looks=looks, n=n)
    _VIS = dict(lanes=lanes, xl=xl, xs=tr["xs"], L=tr["L"], v=tr["v"], p=tr["p"])
    return _VIS


def find_prot(key):
    V = visual()
    for k, ln in V["lanes"].items():
        for j in range(ln["n"]):
            if ln["prot"][j] == key:
                return k, j
    raise KeyError(key)


def setup():
    global TL, RACE_X, T_FIN1, T_FIN2, T_RACE_END, T_G0, T_G1, T_REV, T_WHY, T_TW, T_TW_RUN, T_Q, DURATION, PIT
    s = sample()
    PIT = s["tr"]["p"]
    f1, f2 = sorted((s["fin_m"], s["fin_e"]))

    def build(rx):
        ts = np.arange(0, 80, 1 / 300)
        tau = np.zeros_like(ts)
        v = -PRE
        tau[0] = v
        for k in range(1, len(ts)):
            t = ts[k]
            if t < T_GO:
                sp = 1.0
            else:
                sp = 1.0 + (rx - 1.0) * ease((t - T_GO) / 0.8)
                w = smooth_s((v - (f1 - SLOW_SPAN - 0.8)) / 0.8)
                sp = sp * (1 - w) + 1.0 * w
            v += sp / 300
            tau[k] = v
        return ts, tau

    lo, hi = 1.0, 8.0
    for _ in range(30):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        t_end = float(np.interp(f2, tau, ts))
        if t_end > T_GO + RACE_LEN:
            lo = mid
        else:
            hi = mid
    RACE_X = hi
    ts, tau = build(RACE_X)
    TL = dict(t=ts, tau=tau)
    T_FIN1 = float(np.interp(f1, tau, ts))
    T_FIN2 = float(np.interp(f2, tau, ts))
    T_RACE_END = T_FIN2 + 2.4                     # 抜けた付箋を読む時間
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.4
    T_REV = T_G1 + 0.8                            # 答え
    T_WHY = T_REV + 3.8                           # なぜ
    T_TW = T_WHY + 4.6                            # ひねり
    T_TW_RUN = T_TW + 3.0
    T_Q = T_TW_RUN + 5.2                          # 締め
    DURATION = T_Q + 4.2


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    """計算の秒 τ → 動画の秒"""
    return float(np.interp(tau, TL["tau"], TL["t"]))


def speed_now(t):
    return (tau_of(t + 0.02) - tau_of(t - 0.02)) / 0.04 if t > 0.03 else 1.0


# ---------- 場面の置き場所 ----------

def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def to_dev(t, x, y):
    sc, y0 = layout(t)
    return CX + (x - CX) * sc, y0 + y * sc


def apply_scene(ctx, t):
    sc, y0 = layout(t)
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)


def scene_box(t):
    sc, y0 = layout(t)
    return CX * (1 - sc), y0, W * sc, SCENE_H * sc


# ---------- 絵: 人（正面から。ペン描きの線） ----------

def _limb(ctx, pts, w, col, ink=INK, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink, a))
    ctx.set_line_width(w + 3.6)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def draw_person(ctx, X, Y, h, look, phase=0.0, amp=0.0, reach=0.0, side=1, a=1.0):
    """正面（こちらに向かって歩く）の人。足元が (X, Y)。h は背の高さ(px)。amp は歩きの大きさ、reach はICカードをかざす腕（side 側）"""
    if a <= 0:
        return
    s = h / 170.0
    ctx.save()
    ctx.translate(X, Y)
    ctx.scale(s, s)
    if a < 1:
        ctx.push_group()
    ctx.save()                                          # 影
    ctx.scale(1, 0.22)
    ctx.arc(0, 0, 30, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.15, 0.13, 0.1, 0.14)
    ctx.fill()
    bob = 2.4 * amp * abs(math.sin(phase))
    hip = -80.0 - bob
    for j in (0, 1):                                    # 足
        sg = -1 if j == 0 else 1
        ph = phase + j * math.pi
        lift = max(0.0, math.sin(ph)) * amp * 9.0
        fx = sg * (9.0 + 2.0 * amp * math.cos(ph))
        fy = -lift + 3.0 * amp * math.sin(ph)
        _limb(ctx, [(sg * 7.5, hip), (fx, fy - 4)], 14, look["pants"])
        fill(ctx, INK)
        ctx.save()
        ctx.translate(fx + sg * 1.5, fy - 1.5)
        ctx.scale(1.0, 0.5)
        ctx.arc(0, 0, 11.0, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if look["style"] == 1:                              # 長い髪（うしろ。体より先に描く）
        core.rrect(ctx, -20, -152.0 - bob - 6, 40, 44, 14)
        fill(ctx, look["hair"])
        ctx.fill()
    core.rrect(ctx, -19, -134 - bob, 38, 58, 12)       # 体
    fill(ctx, look["shirt"])
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(2.8)
    ctx.stroke()
    for j in (0, 1):                                    # 腕
        sg = -1 if j == 0 else 1
        ph = phase + (j + 1) * math.pi
        up = reach if sg == side else 0.0
        sw = 7.0 * amp * math.sin(ph)
        hand = (sg * (26.0 + 16.0 * up), -76.0 - bob + sw - 32.0 * up)
        el = (sg * (27.0 + 5.0 * up), -102.0 - bob + 0.5 * sw - 10.0 * up)
        _limb(ctx, [(sg * 19.0, -127.0 - bob), el, hand], 11.0, look["shirt"])
        fill(ctx, SKIN)
        ctx.arc(hand[0], hand[1], 6.2, 0, 2 * math.pi)
        ctx.fill()
    hy = -152.0 - bob                                   # 頭
    fill(ctx, INK)
    ctx.arc(0, hy, 20.4, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, SKIN)
    ctx.arc(0, hy, 17.6, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, look["hair"])                             # 前髪
    if look["style"] == 2:
        ctx.arc(0, hy - 1, 17.8, math.pi * 1.03, math.pi * 1.97)
    else:
        ctx.arc(0, hy - 2, 17.8, math.pi * 1.0, math.pi * 2.0)
        ctx.line_to(11, hy - 6)
        ctx.line_to(-11, hy - 8)
    ctx.close_path()
    ctx.fill()
    fill(ctx, INK)                                      # 目と口
    for ex in (-6.2, 6.2):
        ctx.arc(ex, hy + 1.5, 2.3, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.set_line_width(1.8)
    ctx.arc(0, hy + 7.5, 4.0, math.pi * 0.15, math.pi * 0.85)
    ctx.stroke()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: 改札機 ----------

def gate_x(j):
    """改札機 j（0〜6）の横（m）。列 k は 機 k−1 と k のあいだ"""
    return (j - 3) * PIT


def draw_floor(ctx):
    top, bot = -4.5, 15.0
    fill(ctx, hexrgb("#e6dfc9", 0.55))
    y_top, y_bot = proj(0, bot)[1], proj(0, top)[1]
    ctx.rectangle(-20, y_top, W + 40, y_bot - y_top)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.18))
    ctx.set_line_width(1.8)
    for d in range(int(top), int(bot) + 1):
        y = proj(0, d)[1]
        ctx.move_to(-20, y)
        ctx.line_to(W + 20, y)
    for m in range(-9, 10):
        ctx.move_to(proj(m, bot)[0], proj(m, bot)[1])
        ctx.line_to(proj(m, top)[0], proj(m, top)[1])
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.30))                 # 列の仕切り（床の線）
    ctx.set_line_width(3)
    ctx.set_dash([14, 10])
    for j in range(N_LANE + 1):
        ctx.move_to(proj(gate_x(j), 0.3)[0], proj(gate_x(j), 0.3)[1])
        ctx.line_to(proj(gate_x(j), bot)[0], proj(gate_x(j), bot)[1])
    ctx.stroke()
    ctx.set_dash([])


def draw_walls(ctx):
    """改札の列の両端の壁（端の改札の外）"""
    for sg in (-1, 1):
        xe, ye, s = proj(gate_x(3 + sg * 3), -0.25)
        xe += sg * GATE_W * KX * s / 2
        hh = 0.95 * GATE_PX
        x0, x1 = (-30, xe) if sg < 0 else (xe, W + 30)
        fill(ctx, hexrgb(SLAB))
        ctx.rectangle(x0, ye - hh, x1 - x0, hh)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK, 0.25))
        ctx.set_line_width(2)
        for i in range(1, 4):
            y = ye - hh * i / 4
            ctx.move_to(x0, y)
            ctx.line_to(x1, y)
        ctx.stroke()


def gate_state(k, tau):
    """列 k の扉の開き具合（0〜1）・止まっている人がいるか・読み取り機の光（機の番号→0〜1）"""
    ln = visual()["lanes"][k]
    o = smooth((tau - ln["tap"]) / 0.15) * (1 - smooth((tau - ln["f"] + 0.28) / 0.18))
    openamt = float(o.max()) if len(o) else 0.0
    flash = {}
    fl = np.clip(1 - np.abs(tau - ln["tap"]) / 0.22, 0, 1)
    for j in np.nonzero(fl > 0)[0]:
        cab = k if ln["side"][j] > 0 else k - 1
        flash[cab] = max(flash.get(cab, 0.0), float(fl[j]))
    blocked = bool(np.any((ln["x"] > 0) & (ln["start"] + 0.05 <= tau) & (tau < ln["tap"])))
    return openamt, blocked, flash


def draw_gates(ctx, tau):
    sts = {k: gate_state(k, tau) for k in range(1, N_LANE + 1)}
    for j in range(N_LANE + 1):
        xm = gate_x(j)
        X, Y, s = proj(xm, -0.25)
        w, hgt = GATE_W * KX * s, GATE_PX * s
        fill(ctx, hexrgb("#d3dbe8"))
        ctx.rectangle(X - w / 2, Y - hgt, w, hgt)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.95))
        ctx.set_line_width(3)
        ctx.stroke()
        fill(ctx, hexrgb("#eef2f8"))                    # 上の面と読み取り機
        ctx.move_to(X - w / 2, Y - hgt)
        ctx.line_to(X - w / 2 + 7, Y - hgt - 17)
        ctx.line_to(X + w / 2 - 7, Y - hgt - 17)
        ctx.line_to(X + w / 2, Y - hgt)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.stroke()
        fl = max([sts[k][2].get(j, 0.0) for k in range(1, N_LANE + 1)] + [0.0])
        fill(ctx, hexrgb("#5b8fd6") if fl < 0.05 else hexrgb("#c9f2ff"))
        ctx.rectangle(X - w * 0.24, Y - hgt - 13, w * 0.48, 9)
        ctx.fill()
        for k, dx in ((j, -w * 0.25), (j + 1, w * 0.25)):   # ランプ: 左は列 j・右は列 j+1
            if not 1 <= k <= N_LANE:
                continue
            op, blk, _ = sts[k]
            col = "#35b06a" if op > 0.5 else "#e0524d"
            fill(ctx, hexrgb(col))
            ctx.arc(X + dx, Y - hgt * 0.80, 8.0 * s, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.85))
            ctx.set_line_width(1.6)
            ctx.arc(X + dx, Y - hgt * 0.80, 8.0 * s, 0, 2 * math.pi)
            ctx.stroke()
        fill(ctx, hexrgb(INK, 0.12))                    # 足元の影
        ctx.rectangle(X - w / 2, Y - 3, w, 6)
        ctx.fill()
    for k in range(1, N_LANE + 1):                      # 扉（フラップ）
        op, blk, _ = sts[k]
        xa, ya, s = proj(gate_x(k - 1), -0.25)
        xb, yb, _ = proj(gate_x(k), -0.25)
        xa += GATE_W * KX * s / 2
        xb -= GATE_W * KX * s / 2
        half = (xb - xa) / 2 - 1.5
        c = 1.0 - 0.9 * op
        yf = ya - GATE_PX * s * 0.52
        for x0, sg in ((xa, 1), (xb, -1)):
            ln_ = half * c
            fill(ctx, hexrgb("#e0524d" if blk else "#6aa0e0", 0.95))
            core.rrect(ctx, min(x0, x0 + sg * ln_), yf - 7 * s, max(1.0, abs(ln_)), 14 * s, 4)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.9))
            ctx.set_line_width(2.2)
            ctx.stroke()


# ---------- 人の位置（その時刻の τ で） ----------

def lane_items(k, tau):
    """列 k の、いま見えている人 [(奥行き d, dict)]"""
    V = visual()
    ln = V["lanes"][k]
    xl = V["xl"][k]
    v = ln["v"]
    left = 1 - smooth((tau - v) / 0.5)
    cs = np.concatenate([[0.0], np.cumsum(left)[:-1]])
    left2 = 1 - smooth((tau - 0.15 - v) / 0.5)
    cs2 = np.concatenate([[0.0], np.cumsum(left2)[:-1]])
    out = []
    idx = np.nonzero((ln["spawn"] <= tau) & (tau <= ln["f"] + 1.7))[0]
    for j in idx:
        a_j, f_j, v_j = ln["a"][j], ln["f"][j], ln["v"][j]
        moving = 1.0
        reach = 0.0
        alpha = 1.0
        if tau < a_j:                                   # 歩いてくる
            u = clamp01((tau - ln["w0"][j]) / max(1e-6, a_j - ln["w0"][j]))
            xm = ln["px0"][j] + (ln["ex"][j] - ln["px0"][j]) * u
            d = ln["pd0"][j] + (ln["ed"][j] - ln["pd0"][j]) * u
            if ln["prot"][j] and tau <= 0:
                moving = 0.0
        elif tau < v_j:                                 # 列に並ぶ
            xm = xl + ln["jit"][j]
            d = D_HEAD + Q_GAP * cs[j]
            moving = 1.0 if abs(cs[j] - cs2[j]) > 0.004 else 0.0
            rt = ln["tap"][j]
            reach = smooth_s((tau - (rt - 0.28)) / 0.12) * (1 - smooth_s((tau - (rt + 0.32)) / 0.12))
        elif tau < f_j:                                 # 改札を通る
            u = clamp01((tau - v_j) / max(1e-6, f_j - v_j))
            xm = xl + ln["jit"][j] * (1 - u)
            d = D_HEAD - (D_HEAD + 0.9) * ease(u)
        else:                                           # 通りすぎて、こちらへ
            dt = tau - f_j
            xm = xl + ln["side"][j] * 0.18 * dt
            d = -0.9 - 1.3 * dt
            alpha = 1.0 - smooth_s((dt - 0.35) / 0.9)             # 通りすぎた人は すっと消える（通路を空けて、下の数字を読めるように）
        out.append((d, dict(k=k, j=int(j), xm=xm, look=ln["looks"][j], moving=moving, reach=reach, side=int(ln["side"][j]),
                            prot=ln["prot"][j], alpha=alpha, phase=2 * math.pi * 0.95 * tau + 1.7 * j)))
    return out


def prot_state(key, tau):
    """主役の状態: 'walk' 歩いている / 'wait' 並んでいる（前に n 人）/ 'pass' 通っている / 'done' 抜けた"""
    V = visual()
    k, j = find_prot(key)
    ln = V["lanes"][k]
    if tau < ln["a"][j]:
        return dict(st="walk", n=0)
    if tau >= ln["f"][j]:
        return dict(st="done", n=0)
    if tau >= ln["start"][j]:
        return dict(st="pass", n=0)
    n = int(np.sum((np.arange(ln["n"]) < j) & (ln["f"] > tau)))
    return dict(st="wait", n=n)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    ctx.push_group()                                    # 透明度の組
    ctx.push_group()                                    # 場面の組（あとでふち取りのマスクを掛ける）
    ctx.save()
    bx, by, bw, bh = scene_box(t)
    ctx.rectangle(bx, by, bw, bh)
    ctx.clip()
    ctx.save()
    apply_scene(ctx, t)
    draw_floor(ctx)
    draw_walls(ctx)
    items = []
    for k in range(1, N_LANE + 1):
        items += lane_items(k, tau)
    items.append((-0.25, None))                         # 改札機は奥行き −0.25
    items.sort(key=lambda z: -(z[0] - (1.2 if (z[1] and z[1]["prot"]) else 0.0)))   # 主役は 1.2 m 手前にいるものとして重ねる（人に隠れない）
    prots = {}
    for d, it in items:
        if it is None:
            draw_gates(ctx, tau)
            continue
        X, Y, s = proj(it["xm"], d)
        hh = PERSON_PX * s * it["look"]["h"]
        if it["prot"]:
            ctx.save()                                  # 体のまわりの輪（A=青・C=だいだい）
            ctx.translate(X, Y - hh * 0.50)
            ctx.scale(0.40 * hh, 0.60 * hh)
            ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*hexrgb(INKC[it["prot"]], 0.16))
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INKC[it["prot"]], 0.92))
            ctx.set_line_width(7)
            ctx.stroke()
            ctx.save()                                  # 足元の輪
            ctx.translate(X, Y)
            ctx.scale(1, 0.26)
            ctx.set_source_rgba(*hexrgb(INKC[it["prot"]], 0.95))
            ctx.set_line_width(9)
            ctx.arc(0, 0, 0.46 * KX * s, 0, 2 * math.pi)
            ctx.stroke()
            ctx.restore()
        amp = 1.0 if it["moving"] else (0.12 if it["prot"] else 0.06)
        ph = it["phase"] if it["moving"] else 0.9 * t * 2
        draw_person(ctx, X, Y, hh, it["look"], phase=ph, amp=amp, reach=it["reach"], side=it["side"], a=it["alpha"])
        if it["prot"] and d > -1.2:                     # 改札を抜けて少し歩いたら、丸は消す
            prots[it["prot"]] = (X, Y, hh, s)
    ctx.restore()
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.mask_surface(fade_mask(bx, by, bw, bh)[0], bx, by)   # 上・下・左右はふわっと消える
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.push_group()
    for key, (X, Y, hh, s) in prots.items():            # 頭の上に A・C の丸（マスクの外に描く）
        xd, yd = to_dev(t, X, Y - hh - 46 * s)
        sc = layout(t)[0]
        r = max(24.0, 33 * sc * s)
        fill(ctx, (1, 1, 1, 0.94))
        ctx.arc(xd, yd, r, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, xd, yd, r, r, INKC[key], seed=13 + (key == "e"), width=3.4)
        text(ctx, TAG[key], xd, yd, 40, INKC[key])
        ctx.set_source_rgba(*hexrgb(INKC[key]))         # ▼
        ctx.move_to(xd - 10, yd + r + 1)
        ctx.line_to(xd + 10, yd + r + 1)
        ctx.line_to(xd, yd + r + 16)
        ctx.close_path()
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


_MASK = {}


def fade_mask(bx, by, bw, bh):
    """場面の四辺をふわっと消すマスク（A8）。箱の大きさごとに作って覚えておく"""
    key = (round(bx), round(by), round(bw), round(bh))
    if key in _MASK:
        return _MASK[key]
    if len(_MASK) > 40:
        _MASK.clear()
    w, h = int(math.ceil(bw)), int(math.ceil(bh))
    yy = np.arange(h)[:, None].astype(float)
    xx = np.arange(w)[None, :].astype(float)
    a = np.clip(yy / 44.0, 0, 1) * np.clip((h - yy) / 40.0, 0, 1) * np.clip(xx / 36.0, 0, 1) * np.clip((w - xx) / 36.0, 0, 1)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
    buf = np.zeros((h, stride), np.uint8)
    buf[:, :w] = (a * 255).astype(np.uint8)
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_A8, w, h, stride)
    _MASK[key] = (surf, buf)
    return _MASK[key]


# ---------- 読み取り ----------

def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    s = sample()
    sp = speed_now(t)
    fill(ctx, (*hexrgb(PAPER)[:3], 0.70 * a))                     # 床の上の帯（人が通っても読める）
    core.rrect(ctx, 70, 1262, 940, 188, 22)
    ctx.fill()
    text(ctx, f"再生 {sp:.1f}倍" if sp < 1.95 else f"再生 {sp:.0f}倍", 100, 1282, 24, PENCIL, bold=False, align="left", alpha=a)
    cols = sorted((("e", s["fin_e"]), ("m", s["fin_m"])), key=lambda z: TAG[z[0]])
    for (k, t_fin), cx in zip(cols, (330.0, 720.0)):
        st = prot_state(k, tau)
        done = st["st"] == "done"
        text(ctx, f"{TAG[k]} {NAME[k]}", cx, 1300, 46, INKC[k], alpha=a)
        if st["st"] == "walk":
            stat = "歩いている"
        elif st["st"] == "wait":
            stat = f"並んでいる（前に {st['n']}人）"
        elif st["st"] == "pass":
            stat = "改札を通る"
        else:
            stat = "抜けた！"
        text(ctx, stat, cx, 1352, 34, RED if done else INK, bold=done, alpha=a)
        if done:
            u = clamp01((t - t_of(t_fin)) / 0.35)
            text(ctx, f"{t_fin:.1f}秒", cx, 1408, 62, INKC[k], alpha=a)
            note.pen_circle(ctx, cx, 1408, 135, 44, RED, seed=70 + (k == "e"), width=6, progress=u, alpha=a)
        else:
            text(ctx, f"{max(tau, 0.0):.1f}秒", cx, 1408, 62, INK, alpha=a)
    if t >= T_FIN2:
        b = a * ease_out((t - T_FIN2 - 0.2) / 0.3)
        w = "e" if s["fin_e"] < s["fin_m"] else "m"
        dd = abs(s["fin_e"] - s["fin_m"])
        note.sticky(ctx, f"{NAME[w]}が" + chr(10) + f"{dd:.1f}秒 早く抜けた", 580, 960, 52, "yellow", a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 7
G_X0, G_Y0 = 560 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results("busy")
    win_e = (r["fin_e"] < r["fin_m"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_M), bgra(COL_E)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_e[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_WHY) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results("busy")
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000回（1マス＝1回）", 580, 614, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    win_e = r["fin_e"][:m] < r["fin_m"][:m]
    rows = sorted((("e", int(win_e.sum()), COL_E), ("m", int(m - win_e.sum()), COL_M)), key=lambda z: TAG[z[0]])
    for i, (k, cnt, col) in enumerate(rows):
        y = 1248 + i * 56
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(190, y - 19, 38, 38)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(190, y - 19, 38, 38)
        ctx.stroke()
        text(ctx, f"{TAG[k]} {NAME[k]}が先に抜けた", 250, y, 38, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 38, INK, align="right", alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"残念、{'ABC'[CORRECT]} {NAMES[ORDER[CORRECT]]}が正解。\n"
                         f"端が先は 約{pct_i(sh['p_edge'])}。差は 約{sh['gap_med']:.0f}秒", 580, 1398, 38, "yellow",
                    a=b, tilt=-0.015)


# ---------- なぜ ----------

def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def bars(ctx, t, t0, rows, ys, a, x0=300.0, ln=480.0, vmax=1.0, fmt_v=pct_i, half=True, step=0.45, hh=22, lab=34, val=38, lab_dy=52):
    """横の棒。rows = [(ラベル, 値, 色)]。値は 0〜vmax"""
    yt, yb = ys[0] - hh - 18, ys[-1] + hh + 18
    if half:
        ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
        ctx.set_line_width(3)
        ctx.set_dash([9, 8])
        ctx.move_to(x0 + ln / 2, yt)
        ctx.line_to(x0 + ln / 2, yb)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "半々", x0 + ln / 2, yb + 30, 34, RED, alpha=a)
    for i, ((lab_s, v_, col), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * step
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab_s, x0, y - lab_dy, lab, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - hh, ln, 2 * hh)
        ctx.stroke()
        w = ln * min(1.0, v_ / vmax) * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - hh, w, 2 * hh, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, fmt_v(v_), x0 + ln + 16, y, val, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "1回あたり、余分にかかった時間（平均）", 580, 660, 40, INK, alpha=a)
    wait_x = sh["wait_m"] - sh["wait_e"]
    walk_x = sh["walk_e"] - sh["walk_m"]
    rows = [("真ん中は 前の人を待つ", wait_x, COL_M), ("端は 横へ歩く", walk_x, COL_E)]
    bars(ctx, t, T_WHY, rows, (860.0, 1090.0), a, x0=230.0, ln=480.0, vmax=8.0, fmt_v=lambda v: f"{v:.1f}秒", half=False,
         hh=34, lab=42, val=50, lab_dy=70)
    tb = T_WHY + 0.3 + 2 * 0.45 + 0.5
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"待つ時間のほうが 長い。\n差し引き 約{wait_x - walk_x:.0f}秒、端が早い", 580, 1320, 48, "yellow", a=b, tilt=-0.02)


# ---------- ひねり: ガラガラの時間なら？ ----------

def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + 2 * 0.45 + 0.5


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh, sq = shown(), shown_quiet()
    text(ctx, "端の人が 先に抜けた割合（1万回ずつ）", 580, 660, 40, INK, alpha=a)
    text(ctx, "同じ歩き方で、人の来かただけ少なく", 580, 722, 32, PENCIL, bold=False, alpha=a)
    rows = [("混んでいる朝", sh["p_edge"], COL_E), ("ガラガラの時間", sq["p_edge"], COL_E)]
    bars(ctx, t, T_TW_RUN, rows, (900.0, 1110.0), a, x0=270.0, ln=470.0, hh=34, lab=42, val=50, lab_dy=70)
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"ガラガラなら、近い列が先。\nでも差は 約{abs(sq['gap_med']):.1f}秒", 580, 1345, 44, "pink", fg=RED, a=b, tilt=-0.02)


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


CD_X, CD_Y = 190.0, 1385.0
Q_CX = 565.0                                      # 問いの中心（x 130〜1000 に収める）
Q_W = 860.0                                       # 問いの幅（この幅いっぱいに大きく）


class KIntro(note.Intro):
    """この回だけの冒頭。上: 大きな問い2行・前提・三択（横1列）。その下いっぱいに、改札と人の流れ（0秒目から動いている）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        w = max(core.text_width(l, 100) for l in BIG_Q)
        sz = min(96.0, 100.0 * Q_W / w)
        pop = 1 + 0.025 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (440, 440 + sz * 1.12)):
            ctx.save()
            ctx.translate(Q_CX, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        yl = 440 + sz * 1.12 + sz * 0.56
        note.pen_line(ctx, Q_CX - w2 / 2 - 6, yl + 4, Q_CX + w2 / 2 + 6, yl - 2, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        yd = yl + 44
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 575, yd, 34, INK, bold=False, alpha=a1)
        yc = yd + 54
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 820)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, yc, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, yc, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, yc, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.94 * a2))
            core.rrect(ctx, cx - 125, cy - 150, 250, 220, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 150, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 98, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 54, 52, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 74, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        w = max(core.text_width(l, 100) for l in BIG_Q)
        sz = min(56.0, 100.0 * 800.0 / w)
        text(ctx, BIG_Q[0], 540, 406, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 406 + sz * 1.13, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        yl = 406 + sz * 1.13 + sz * 0.56
        note.pen_line(ctx, 540 - w2 / 2 - 6, yl + 3, 540 + w2 / 2 + 6, yl, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = yl + 50
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7, progress=rev)
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


INTRO = KIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "スタート", 290, 1110, 40, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、ガラガラの時間なら？", 560, 980, a=ba, t_rel=t - T_TW, size=54)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\n端まで歩く派？\n近くに並ぶ派？", 570, 1000, 66, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 570, 1330, 44, INK, bold=False, alpha=r)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def build_audio():
    s = sample()
    V = visual()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for k, ln in V["lanes"].items():                   # ピッ（タッチ）。主役は少し大きく
        for j in range(ln["n"]):
            tv_tau = float(ln["tap"][j])
            if tv_tau < -PRE:
                continue
            tv = t_of(tv_tau)
            if tv >= T_G0 or tv <= 0.05:
                continue
            if ln["prot"][j]:
                mx.add(tv, blip(1568.0, 0.1), 0.28)
            elif speed_now(tv) < 1.6:
                mx.add(tv, tick(2200.0 + 140 * k, 0.03), 0.05)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_FIN1 - 1.2, bpm=124, vol=0.32)
    mx.add(T_FIN1, bell(784.0, 1.2), 0.45)
    mx.add(T_FIN2, bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(2):                                 # なぜ
        mx.add(T_WHY + 0.3 + i * 0.45, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(2):
        mx.add(T_TW_RUN + 0.3 + i * 0.45, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh, sq = shown(), shown_quiet()
    checks = []
    # (1) 通過時間: 範囲 1.0〜2.4秒に収まり、平均が 約1.3秒
    x = service(np.random.default_rng(1), 400000)
    checks.append(("通過時間の平均（秒）", float(x.mean()), 1.30, 0.03))
    checks.append(("通過時間が 1.0〜2.4秒の外に出ていない", float(x.min() >= 1.0 and x.max() <= 2.4), 1.0, 0.0))
    checks.append(("通過時間の9割が 1.0〜1.8秒", float(np.mean(x <= 1.8)), 0.93, 0.04))
    # (2) 恒等式: 差の平均 = 待ちの差の平均 − 歩きの差の平均（抜ける時刻 = 歩く + 待つ + 自分の通過時間。通過時間は2人同じ）
    checks.append(("差の平均 ＝ 待ちの差 − 歩きの差", sh["gap_mean"], (sh["wait_m"] - sh["wait_e"]) - (sh["walk_e"] - sh["walk_m"]), 1e-9))
    # (3) 人が少ない回（待ちが0）は、差 ＝ 歩く距離の差 ÷ 歩く速さ（刻み 0.02秒）
    worst = 0.0
    for i in range(400):
        tr = trial([SEED_QUIET, i], "quiet")
        A, B = tr["A"], tr["B"]
        if A["wait"] == 0.0 and B["wait"] == 0.0:
            worst = max(worst, abs((A["fin"] - B["fin"]) - (A["dist"] - B["dist"]) / tr["v"]))
    checks.append(("待ちが0の回の 差 − 式（最大・秒）", worst, 0.0, 0.03))
    # (4) 端の余分な歩きの真ん中の値が 3〜6 m
    checks.append(("端の余分な歩き（真ん中の値・m）が 3〜6 m", float(3.0 <= sh["extra_q"][2] <= 6.0), 1.0, 0.0))
    # (5) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ。正解の記号は B にしない
    checks.append(("画面の答えが、規則で出した答えと同じ", float(ORDER[INTRO.correct]), float(answer_by_rule(sh["p_edge"], sh["gap_med"])), 0.0))
    checks.append(("正解の記号が B ではない（10/25 の正解が B）", float(INTRO.correct != 1), 1.0, 0.0))
    # (6) 先に抜けた回の合計が1万（同時は無い）
    checks.append(("先に抜けた回の合計", float(sh["n_edge"] + sh["n_mid"]), float(N_TRIAL), 0.0))
    # (7) ひねり: ガラガラのほうが、端が先の割合が低い
    checks.append(("ガラガラのほうが 端が先の割合が低い", float(sq["p_edge"] < sh["p_edge"]), 1.0, 0.0))
    # (8) 見本は1万回の中の1回で、差が真ん中の値の近く。絵の時刻表（主役を入れて組み直したもの）が計算と同じ
    smp = sample()
    checks.append(("見本の差（秒）が真ん中の値の近く", smp["gap"], sh["gap_med"], 1.0))
    V = visual()
    for key, fin in (("m", smp["fin_m"]), ("e", smp["fin_e"])):
        k, j = find_prot(key)
        checks.append((f"絵の時刻表の抜ける時刻 {NAME[key]}（秒）", float(V["lanes"][k]["f"][j]), fin, 0.03))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.2f}倍  抜ける {T_FIN1:.2f} / {T_FIN2:.2f}秒  答え {T_REV:.1f}  なぜ {T_WHY:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（真ん中 {s['fin_m']:.1f}秒 / 端 {s['fin_e']:.1f}秒）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, T_FIN1 - 0.5, T_FIN1 + 0.5, T_FIN2 - 0.5, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 3.0, T_TW + 1.0, T_TW_RUN + 2.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
