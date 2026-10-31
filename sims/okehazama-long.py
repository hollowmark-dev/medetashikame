"""桶狭間をもう一度戦ったら、2千人は勝てる？【1万回シミュレーション】（横型ロング・チャンネル「めでたしかめ」）

このファイルは公開日まで非公開（答えが書いてある）。
この前半はモデル（数字の計算・照合・数字の書き出し）。後半（ファイル最後の場面の部分）が場面（描画・音・照合・書き出し。densha-long.py と同じ並び）。
前の動画 sims/kassen-long.py の撃ち合いの数え方をそのまま使う（コピー。ハイフン入りのファイル名なので import はしない）。
試作は out/okehazama-long/proto/ （集計人数の近似。ここでは作り直した）。

■ モデル（正直に。織田が勝つように調整しない）
  撃ち合い  : 一斉射撃（ラウンド）ごとに、両軍が同時に撃つ。生きている兵がそれぞれ確率 p = 1/25 で当て（ショート・合戦ロングと同じ）、
              当たりは相手の（前線の）兵にでたらめに散る。同じ兵に2本当たっても倒れるのは1人（「異なる当たり」で数える）。
              倒された兵も、その回は撃つ（同時処理）。
  兵力      : 織田 2,000（信長公記「二千に不足」）。今川は総勢 25,000、そのうち義元の本陣 5,000、残り 20,000 は別の場所（兵が何か所にも分かれていた）。
  織田の勝ち: 本陣が「敗走」するか、全滅すること。本陣は、最初の人数の割合 r を失った時点で敗走する（敗走した本陣は、そこで勝負あり）。
  織田は崩れない【仮定】: 織田は最後の1人まで戦う（敗走しない）。織田が先に全滅したら負け。同じ回に両方全滅は引き分け＝勝ちに数えない。
  崩れ r    : 「もう一度戦ったら」の揺れの正体。戦いごとに r を引く。基本 r ～ 一様(0.1, 0.5)（1割〜5割）【史料に根拠なし。幅は主観】。
              敗走の条件がなければ、全滅するまで戦う。
  雨の不意打ち s: 信長公記は「今川の顔に雨が打ちつけ、晴れてから攻めた」と書く。→ 織田が s 回ぶん先に撃てる（その間、今川は撃ち返さない）。
              s は戦いごとに {0,1,2,3} から一様。【「弓が使えなかった」ではない。史料にない】
  江戸版の谷: 田楽狭間の「谷底」は江戸時代に語られた脚色（史実でない）。両軍とも前線の W 人しか撃てない（合戦ロングの幅 W の仕組み）。
              W は戦いごとに {50, 100, 200} から一様（連続の 50〜200 ではなく3つに決めた。各 W の結果も別に出す）。
  後ろの2万 : 本陣に勝ったあと、残りの今川が1組ずつ順に来る。同じ戦いの r で敗走する（戦いごとに r は1つ）。織田は生き残りで続けて戦う。
  腕前 k    : 織田の1人が1回に出す当たりの期待が k×p（k>1/p のときは1人 ceil(k p) 本に分ける）。k=1 が基本。

■ 累積ラダー（1段ごとに条件を1つ足す。各 10,000 回。種は固定）
  L1 野原・全軍 / L2 分かれていた（本陣5000だけ） / L3 +崩れ / L4 +雨の不意打ち / L5 置き方を変えたら / L6 後ろの2万人 / L7 江戸版の谷

使い方
  python -X utf8 sims/okehazama-long.py --numbers   計算 → 照合 → out/okehazama-long/data.json・numbers.md（数分）
  python -X utf8 sims/okehazama-long.py --check     data.json を読んで照合だけ
  python -X utf8 sims/okehazama-long.py --scenecheck --fake-voice   場面の照合（音声なし）
  python -X utf8 sims/okehazama-long.py --stills --fake-voice       要所の静止画と sheet_480.png（詳しくは場面の部分の先頭）
"""
import json
import math
import sys
import time
import zlib
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers  # noqa: E402

SLUG = "okehazama-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG

# ============================================================
# 0. 定数
# ============================================================
P_HIT = 1 / 25            # 1回の射撃で当たる確率（ショート・合戦ロングと同じ）
N_TRIALS = 10000          # 各条件の回数
N_BIG = 100000            # 「0/10万回」を出すための回数
N_K50 = 400               # 互角の腕前の探索（n を下げる。規模が大きく、ばらつきが小さい）
W_FIELD = 10 ** 9         # 前線の幅の制限なし（野原）

ODA = 2000                # 織田（信長公記「二千に不足」）
TOTAL = 25000             # 今川の総勢
HONJIN = 5000             # 義元の本陣
REST = TOTAL - HONJIN     # 別の場所にいた分
R_RANGE = (0.1, 0.5)      # 本陣が崩れる割合 r（1割〜5割）。戦いごとに一様に引く
S_SET = (0, 1, 2, 3)      # 雨の不意打ちで織田だけが撃てる回数。戦いごとに一様に引く
W_SET = (50, 100, 200)    # 江戸版の谷の幅。戦いごとに一様に引く

SEED = 1                  # 数字の本番
SEED_AGAIN = 777          # 別の乱数でやり直す
SEED_SAMPLE = 5150        # 画面の見本を探す種

R_CURVE = (0.02, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
GROUP = 5000              # 後ろの今川を1組ずつにするときの1組の人数


# ============================================================
# 1. 戦いの計算（n 回を一斉に進める）
# ============================================================
def rng_for(seed, *keys):
    return np.random.default_rng([seed, *keys])


def key_of(name):
    return zlib.crc32(name.encode("utf-8"))


def _distinct(s, m, rng):
    """m 個の的に s 本をでたらめに当てたとき、的に当たった異なる数（的ごとの重なりを除く）。s, m は配列（kassen-long と同じ）"""
    d = np.zeros(len(s), np.int64)
    mx = int(s.max()) if len(s) else 0
    for j in range(mx):
        idx = np.flatnonzero(s > j)
        if idx.size == 0:
            break
        new = rng.random(idx.size) < (m[idx] - d[idx]) / m[idx]
        d[idx] += new
    return d


def _vec(x, n, dtype):
    return np.broadcast_to(np.asarray(x, dtype), (n,)).copy()


def battle(O0, G0, rng, r=None, s=None, W=None, p=P_HIT, k=1.0, track=False):
    """織田 O0 人（配列。試行ごと）が、今川の1組 G0 人と戦う。両軍同時の一斉射撃を、勝負がつくまで。
    r: 敗走する割合（None なら敗走なし）, s: 織田だけが先に撃てる回数, W: 前線の幅, k: 織田の腕前（当たりの期待が k×p）
    勝ち ＝ 全滅させた／敗走させた（そのとき織田が生きている）。織田が先に全滅、または同時に全滅なら負け（tie に数える）。
    返り値 dict: O, G（最後の人数）, won, routed, tie, volleys, [track のとき traj: n×(T+1)×2 の (織田, 今川)]"""
    O = np.array(O0, np.int64)
    n = len(O)
    G = np.array(np.broadcast_to(np.asarray(G0, np.int64), (n,)))
    Gs = G.copy()
    r_a = None if r is None else _vec(r, n, float)
    thr = None if r_a is None else r_a * Gs
    s_a = _vec(0 if s is None else s, n, np.int64)
    W_a = _vec(W_FIELD if W is None else W, n, np.int64)
    m = max(1, int(math.ceil(k * p - 1e-12)))
    pO = k * p / m
    won = np.zeros(n, bool)
    routed = np.zeros(n, bool)
    tie = np.zeros(n, bool)
    ended = np.zeros(n, bool)
    volleys = np.zeros(n, np.int64)
    tr = [np.stack([O, G], 1).astype(np.int32)] if track else None
    t = 0
    while True:
        idx = np.flatnonzero(~ended)
        if idx.size == 0:
            break
        o, g = O[idx], G[idx]
        ao, ag = np.minimum(o, W_a[idx]), np.minimum(g, W_a[idx])
        sO = rng.binomial(ao * m, pO)
        sG = rng.binomial(ag, p)
        sG = np.where(t < s_a[idx], 0, sG)          # 雨の不意打ち: 今川は撃ち返せない
        dG = _distinct(sO, ag, rng)
        dO = _distinct(sG, ao, rng)
        o2, g2 = o - dO, g - dG
        O[idx], G[idx] = o2, g2
        volleys[idx] += 1
        lost = o2 <= 0
        wipe = (g2 <= 0) & (o2 > 0)
        rout = np.zeros(idx.size, bool) if thr is None else ((o2 > 0) & (g2 > 0) & ((Gs[idx] - g2) >= thr[idx] - 1e-9))
        fin = lost | wipe | rout
        tie[idx[(o2 <= 0) & (g2 <= 0)]] = True
        won[idx[wipe | rout]] = True
        routed[idx[rout]] = True
        ended[idx[fin]] = True
        t += 1
        if track:
            tr.append(np.stack([O, G], 1).astype(np.int32))
    out = dict(O=O, G=G, won=won, routed=routed, tie=tie, volleys=volleys)
    if track:
        out["traj"] = np.stack(tr, 1)
    return out


# ============================================================
# 2. 条件（cfg）を回して要約する
# ============================================================
def cfg_make(O=ODA, H=HONJIN, groups=(), r=None, s=0, W=None, Wg=None, k=1.0, p=P_HIT):
    """r: None／数／(下限,上限)  s: 数／(候補…)  W: None／数／(候補…)  groups: 本陣のあと順に来る組の人数
    Wg: None なら後ろの組は野原／"same" なら本陣と同じ幅"""
    return dict(O=O, H=H, groups=tuple(groups), r=r, s=s, W=W, Wg=Wg, k=k, p=p)


def draw_params(cfg, n, rng):
    r = cfg["r"]
    if r is None:
        ra = None
    elif isinstance(r, (tuple, list)):
        ra = rng.uniform(r[0], r[1], n)
    else:
        ra = np.full(n, float(r))
    s = cfg["s"]
    sa = rng.choice(np.array(s, np.int64), n) if isinstance(s, (tuple, list)) else np.full(n, int(s), np.int64)
    W = cfg["W"]
    if W is None:
        Wa = np.full(n, W_FIELD, np.int64)
    elif isinstance(W, (tuple, list)):
        Wa = rng.choice(np.array(W, np.int64), n)
    else:
        Wa = np.full(n, int(W), np.int64)
    return ra, sa, Wa


def simulate(cfg, n, seed, name, track=False):
    """cfg を n 回。返り値 raw: 試行ごとの値の配列（後で summarize で要約。見本探しにも使う）"""
    rng = rng_for(seed, key_of(name))
    ra, sa, Wa = draw_params(cfg, n, rng)
    O0 = np.full(n, cfg["O"], np.int64)
    b0 = battle(O0, cfg["H"], rng, r=ra, s=sa, W=Wa, p=cfg["p"], k=cfg["k"], track=track)
    raw = dict(cfg=cfg, n=n, r=ra, s=sa, W=Wa, first=b0, stages=[])
    alive = b0["won"].copy()
    O = b0["O"].copy()
    O[~alive] = 0
    reach = [int(alive.sum())]
    raw["O_after_first"] = O.copy()
    raw["stage_idx"] = []
    for gi, g in enumerate(cfg["groups"]):
        idx = np.flatnonzero(alive)
        if idx.size == 0:
            reach.append(0)
            continue
        Wg = Wa[idx] if cfg["Wg"] == "same" else None
        b = battle(O[idx], g, rng, r=None if ra is None else ra[idx], s=0, W=Wg, p=cfg["p"], k=cfg["k"], track=track)
        raw["stages"].append(dict(idx=idx, b=b, g=g))
        O[idx] = np.where(b["won"], b["O"], 0)
        alive[idx[~b["won"]]] = False
        reach.append(int(alive.sum()))
    raw["O_end"] = np.where(alive, O, 0)
    raw["alive"] = alive
    raw["reach"] = reach
    return raw


def wilson(w, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    ph = w / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def _grp_rate(mask, key_arr, vals):
    out = {}
    for v in vals:
        sel = key_arr == v
        nn = int(sel.sum())
        out[str(v)] = dict(n=nn, wins=int((mask & sel).sum()), rate=float((mask & sel).sum() / nn) if nn else 0.0)
    return out


def summarize(raw):
    cfg, n = raw["cfg"], raw["n"]
    f = raw["first"]
    H = cfg["H"]
    wins_first = int(f["won"].sum())
    alive = raw["alive"]
    wins = int(alive.sum())
    lost_frac = (H - f["G"]) / H                      # 本陣を削った割合（敗走・全滅の回も、織田が先に倒れた回も、そのまま）
    st = dict(n=n, wins=wins, wins_first=wins_first, rate=wins / n, rate_first=wins_first / n)
    st["ci"] = wilson(wins, n)
    st["ci_first"] = wilson(wins_first, n)
    st["reach"] = raw["reach"]
    st["ties"] = int(f["tie"].sum())
    st["routed_wins"] = int(f["routed"].sum())
    st["wiped_wins"] = int((f["won"] & ~f["routed"]).sum())
    st["h_lost_mean"] = float(lost_frac.mean())
    st["h_lost_sd"] = float(lost_frac.std(ddof=1)) if n > 1 else 0.0
    st["g_left_mean"] = float(f["G"].mean())
    st["volleys_mean"] = float(f["volleys"].mean())
    st["volleys_median"] = float(np.median(f["volleys"]))
    if wins_first:
        Of = raw["O_after_first"][f["won"]]
        st["surv_first_mean"] = float(Of.mean())
        st["surv_first_median"] = float(np.median(Of))
    else:
        st["surv_first_mean"] = st["surv_first_median"] = None
    if wins:
        Oe = raw["O_end"][alive]
        st["surv_mean"] = float(Oe.mean())
        st["surv_median"] = float(np.median(Oe))
        st["surv_min"], st["surv_max"] = int(Oe.min()), int(Oe.max())
    else:
        st["surv_mean"] = st["surv_median"] = None
    # 条件が戦いごとに違うときの内訳（勝ちの率）
    won = alive
    if raw["r"] is not None and isinstance(cfg["r"], (tuple, list)):
        lo, hi = cfg["r"]
        edges = [lo + (hi - lo) * i / 4 for i in range(5)] if hi - lo > 0.25 else [lo, (lo + hi) / 2, hi]
        by = []
        for a, b in zip(edges[:-1], edges[1:]):
            sel = (raw["r"] >= a) & (raw["r"] <= b if b == edges[-1] else raw["r"] < b)
            nn = int(sel.sum())
            by.append(dict(lo=a, hi=b, n=nn, wins=int((won & sel).sum()), rate=float((won & sel).sum() / nn) if nn else 0.0))
        st["by_r"] = by
    if isinstance(cfg["s"], (tuple, list)):
        st["by_s"] = _grp_rate(won, raw["s"], cfg["s"])
    if isinstance(cfg["W"], (tuple, list)):
        st["by_W"] = _grp_rate(won, raw["W"], cfg["W"])
    if wins_first and raw["r"] is not None:
        st["r_on_win_mean"] = float(raw["r"][f["won"]].mean())
    # 保存則など（照合で使う）
    inv = bool((f["O"] <= cfg["O"]).all() and (f["O"] >= 0).all() and (f["G"] <= H).all() and (f["G"] >= 0).all()
               and (f["O"][f["won"]] > 0).all() and (f["G"][f["won"] & ~f["routed"]] == 0).all()
               and wins <= wins_first <= n and (f["volleys"] >= 1).all())
    if raw["r"] is not None and wins_first and f["routed"].any():
        rr = f["routed"]
        inv = inv and bool(((H - f["G"][rr]) >= raw["r"][rr] * H - 1e-6).all())
    st["inv_ok"] = inv
    return st


def run_cfg(cfg, n, seed, name):
    raw = simulate(cfg, n, seed, name)
    st = summarize(raw)
    st["name"] = name
    return st


# ============================================================
# 3. 理論（連続の近似・期待値だけで進める）
# ============================================================
def lanchester_square(R, B):
    """2次法則: 残り = √(R²−B²)"""
    return math.sqrt(R * R - B * B) if R > B else 0.0


def one_step_kills(shooters, targets, p, m=1):
    """1回の一斉射撃で、targets 人のうち倒れる人数の期待値（閉じた式）。1人あたり m 本、1本が当たる確率 p"""
    if targets <= 0 or shooters <= 0:
        return 0.0
    return targets * (1.0 - max(0.0, 1.0 - p / targets) ** (shooters * m))


def mean_field_fight(O, G0, W=W_FIELD, s=0, k=1.0, p=P_HIT, r=None, max_v=200000):
    """平均場: 人数を実数のまま期待値で進める。返り値 dict(O, G, volleys, win, lost_frac)。
    win ＝ 今川が全滅／敗走（r の割合を失う）するまで織田が生きていること"""
    O, G = float(O), float(G0)
    m = max(1, int(math.ceil(k * p - 1e-12)))
    pk = k * p / m
    v = 0
    while O > 0.5 and G > 0.5 and v < max_v:
        ao, ag = min(O, W), min(G, W)
        dG = one_step_kills(ao, ag, pk, m)
        dO = one_step_kills(ag, ao, p) if v >= s else 0.0
        O, G = O - dO, G - dG
        v += 1
        if r is not None and (G0 - G) >= r * G0 and O > 0.5:
            return dict(O=O, G=G, volleys=v, win=True, lost_frac=(G0 - G) / G0)
    win = O > 0.5 and G <= 0.5
    return dict(O=max(O, 0.0), G=max(G, 0.0), volleys=v, win=win, lost_frac=(G0 - max(G, 0.0)) / G0)


def mean_field_cliff(O, G0, W=W_FIELD, s=0, k=1.0):
    """織田が本陣を何割まで削れるか（敗走なしで戦い続け、織田が尽きたときに削った割合）。r がこれより小さければ勝てる目安"""
    return mean_field_fight(O, G0, W=W, s=s, k=k)["lost_frac"]


def k50_mean_field(O, G0, lo=1.0, hi=3000.0):
    """全滅させる勝負が五分になる腕前 k（平均場）"""
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if mean_field_fight(O, G0, k=mid)["win"]:
            hi = mid
        else:
            lo = mid
    return hi


def win_rate_k(O, G0, k, seed, n=N_K50, key=0):
    rng = rng_for(seed, 9000, key, int(k * 1000))
    b = battle(np.full(n, O, np.int64), G0, rng, k=k)
    return float(b["won"].mean())


def k50_mc(O, G0, seed, n=N_K50, lo=1.0, hi=None, iters=11):
    """全滅させる勝負が五分になる腕前 k（1人ずつの確率の数え方。対数の二分探索）"""
    hi = hi or 2.0 * (G0 / O) ** 2
    for i in range(iters):
        mid = math.sqrt(lo * hi)
        if win_rate_k(O, G0, mid, seed, n, key=G0) >= 0.5:
            hi = mid
        else:
            lo = mid
    return math.sqrt(lo * hi)


# ============================================================
# 4. 条件の一覧（ラダー）
# ============================================================
def ladder_defs():
    """(id, 名前, cfg)。累積: 1段ごとに条件を1つ足す"""
    L1 = cfg_make(H=TOTAL)
    L2 = cfg_make(H=HONJIN)
    L3 = cfg_make(r=R_RANGE)
    L4 = cfg_make(r=R_RANGE, s=S_SET)
    L7 = cfg_make(r=R_RANGE, s=S_SET, W=W_SET)
    return [
        ("L1", "野原・全軍（2千 vs 2万5千、崩れなし・不意打ちなし）", L1),
        ("L2", "分かれていた（2千 vs 本陣5千だけ）", L2),
        ("L3", "＋崩れ（本陣が1割〜5割を失うと敗走）", L3),
        ("L4", "＋雨の不意打ち（織田が先に0〜3回撃つ）", L4),
        ("L7", "江戸版の谷（L4 ＋ 前線の幅 50/100/200）", L7),
    ]


def l5_defs():
    """L4 から1つだけ変える（置き方を変えたら）"""
    b = dict(r=R_RANGE, s=S_SET)
    return [
        ("L5-0", "基本（L4）", cfg_make(**b)),
        ("L5-1", "本陣が6千", cfg_make(H=6000, **b)),
        ("L5-2", "本陣が4千（参考）", cfg_make(H=4000, **b)),
        ("L5-3", "織田が3千（日本大百科・ブリタニカの数）", cfg_make(O=3000, **b)),
        ("L5-4", "崩れやすさ 2割〜5割（崩れやすい）", cfg_make(r=(0.2, 0.5), s=S_SET)),
        ("L5-5", "崩れやすさ 1割〜3割（崩れにくい）", cfg_make(r=(0.1, 0.3), s=S_SET)),
        ("L5-6", "崩れやすさ 3割〜5割（さらに崩れにくい）", cfg_make(r=(0.3, 0.5), s=S_SET)),
        ("L5-7", "雨の不意打ちが長い（0〜6回）", cfg_make(r=R_RANGE, s=tuple(range(7)))),
        ("L5-8", "雨の不意打ち 3回に固定", cfg_make(r=R_RANGE, s=3)),
        ("L5-9", "織田3千・本陣4千・崩れやすい2〜5割（織田に有利なものを全部）", cfg_make(O=3000, H=4000, r=(0.2, 0.5), s=S_SET)),
    ]


def l6_defs():
    """後ろの今川が1組ずつ来る。L4 の条件で本陣と戦い、勝ったら残りと続けて戦う"""
    b = dict(r=R_RANGE, s=S_SET)
    out = []
    for total in (20000, 25000, 45000):
        rest = total - HONJIN
        nz = rest // GROUP
        out.append((f"L6-{total}-1", f"総勢{total:,}: 後ろの{rest:,}が1組", cfg_make(groups=(rest,), **b)))
        out.append((f"L6-{total}-{nz}", f"総勢{total:,}: 後ろの{rest:,}が{GROUP:,}ずつ{nz}組", cfg_make(groups=(GROUP,) * nz, **b)))
    out.append(("L6-best", "総勢25,000・織田に有利なもの全部（3千・本陣4千・2〜5割）で後ろの2万が1組",
                cfg_make(O=3000, H=4000, groups=(21000,), r=(0.2, 0.5), s=S_SET)))
    out.append(("L6-best4", "同上で後ろの2.1万が5千ずつ4組超（5250×4）",
                cfg_make(O=3000, H=4000, groups=(5250,) * 4, r=(0.2, 0.5), s=S_SET)))
    out.append(("L6-valley", "江戸版の谷（幅50/100/200）のまま、後ろの2万が5千ずつ4組",
                cfg_make(groups=(GROUP,) * 4, r=R_RANGE, s=S_SET, W=W_SET, Wg="same")))
    return out


def l7_defs():
    """江戸版の谷: 幅ごと／前提を変えたとき"""
    out = []
    for W in W_SET:
        out.append((f"L7-W{W}", f"谷の幅 {W} だけ（L4 の条件）", cfg_make(r=R_RANGE, s=S_SET, W=W)))
    out += [
        ("L7-s0", "谷＋雨の不意打ちなし（L3 ＋ 谷）", cfg_make(r=R_RANGE, s=0, W=W_SET)),
        ("L7-r25", "谷＋崩れやすさ 2割〜5割", cfg_make(r=(0.2, 0.5), s=S_SET, W=W_SET)),
        ("L7-r13", "谷＋崩れやすさ 1割〜3割", cfg_make(r=(0.1, 0.3), s=S_SET, W=W_SET)),
        ("L7-r35", "谷＋崩れやすさ 3割〜5割", cfg_make(r=(0.3, 0.5), s=S_SET, W=W_SET)),
        ("L7-H6", "谷＋本陣6千", cfg_make(H=6000, r=R_RANGE, s=S_SET, W=W_SET)),
        ("L7-O3", "谷＋織田3千", cfg_make(O=3000, r=R_RANGE, s=S_SET, W=W_SET)),
        ("L7-all", "谷＋全軍25,000が谷にいた（崩れ r は全軍に）", cfg_make(H=TOTAL, r=R_RANGE, s=S_SET, W=W_SET)),
    ]
    return out


# ============================================================
# 5. 画面の見本（1回ぶんの戦いの経過）
# ============================================================
def _typical(cand, metrics):
    """cand: 候補の添字（配列）, metrics: 各候補の特徴量（行列）。中央値に最も近いものを返す（SD で割って距離）"""
    M = np.asarray(metrics, float)
    med = np.median(M, axis=0)
    sd = M.std(axis=0)
    sd[sd == 0] = 1.0
    d = (((M - med) / sd) ** 2).sum(axis=1)
    return int(cand[int(np.argmin(d))])


def sample_record(raw, i, step, kind, batch, seed, rate):
    cfg = raw["cfg"]
    f = raw["first"]
    tr = f["traj"][i][: int(f["volleys"][i]) + 1]
    won_first = bool(f["won"][i])
    rec = dict(step=step, kind=kind, seed=int(seed), batch=int(batch), index=int(i), n_batch=int(raw["n"]),
               O0=cfg["O"], H0=cfg["H"],
               r=None if raw["r"] is None else round(float(raw["r"][i]), 4),
               s=int(raw["s"][i]), W=None if int(raw["W"][i]) >= W_FIELD else int(raw["W"][i]),
               volleys=int(f["volleys"][i]),
               result=("rout" if f["routed"][i] else ("wiped" if won_first else ("tie" if f["tie"][i] else "oda_dead"))),
               O_end=int(f["O"][i]), G_end=int(f["G"][i]),
               h_lost_frac=float((cfg["H"] - f["G"][i]) / cfg["H"]),
               step_win_rate=float(rate),
               traj=[[int(a), int(b)] for a, b in tr])
    # 後ろの組（L6）
    segs = []
    for st in raw["stages"]:
        pos = np.flatnonzero(st["idx"] == i)
        if pos.size == 0:
            continue
        j = int(pos[0])
        b = st["b"]
        t2 = b["traj"][j][: int(b["volleys"][j]) + 1]
        segs.append(dict(group=int(st["g"]), volleys=int(b["volleys"][j]), won=bool(b["won"][j]),
                         result=("rout" if b["routed"][j] else ("wiped" if b["won"][j] else "oda_dead")),
                         traj=[[int(a), int(c)] for a, c in t2]))
    if segs:
        rec["later"] = segs
        rec["O_end_all"] = int(raw["O_end"][i])
    return rec


def find_sample(step, cfg, kind, seed, rate, n_batch=4000, max_batch=60):
    """kind = "win"（最後まで勝つ）／"loss"（負け）／"win_first"（本陣に勝つ＝L6の途中）。
    n_batch 回ぶんを見本の種で回し、条件に合う中で「ふつう」（ターン数と残りが中央値に近い）ものを1つ選ぶ。
    勝ちがまれな段は、勝ちが見つかるまで batch を重ねる（max_batch まで）"""
    found = None
    for b in range(max_batch):
        raw = simulate(cfg, n_batch, seed + b, f"sample:{step}", track=True)
        f = raw["first"]
        if kind == "win":
            mask = raw["alive"]
        elif kind == "win_first":
            mask = f["won"] & ~raw["alive"]
        else:
            mask = ~raw["alive"] & ~f["won"]
        cand = np.flatnonzero(mask)
        if cand.size == 0:
            continue
        if kind == "win":
            met = np.stack([f["volleys"][cand], raw["O_end"][cand]], 1)
        elif kind == "win_first":
            met = np.stack([f["volleys"][cand], raw["O_after_first"][cand]], 1)
        else:
            met = np.stack([f["volleys"][cand], f["G"][cand]], 1)
        # まれな勝ちは1回の batch で数個しか出ないので、そのままの中央値で選ぶ
        i = _typical(cand, met)
        found = sample_record(raw, i, step, kind, b, seed + b, rate)
        found["n_candidates_in_batch"] = int(cand.size)
        break
    return found


# ============================================================
# 6. 全部の数字を計算する
# ============================================================
def compute(seed=SEED):
    t0 = time.time()
    res = dict(params=dict(P_HIT=P_HIT, N_TRIALS=N_TRIALS, N_BIG=N_BIG, ODA=ODA, TOTAL=TOTAL, HONJIN=HONJIN, REST=REST,
                           R_RANGE=R_RANGE, S_SET=S_SET, W_SET=W_SET, R_CURVE=R_CURVE, GROUP=GROUP, seed=seed,
                           seed_again=SEED_AGAIN, seed_sample=SEED_SAMPLE))

    def tick(label):
        print(f"  [{time.time() - t0:6.1f}秒] {label}", flush=True)

    # ---- 乱数の数え方そのものの照合（1回の射撃の期待値）----
    rng = rng_for(seed, 1)
    nn = 20000
    out = []
    for sh, tg in ((ODA, HONJIN), (HONJIN, ODA), (TOTAL, ODA)):
        sS = rng.binomial(sh, P_HIT, nn)
        d = _distinct(sS, np.full(nn, tg), rng)
        out.append(dict(shooters=sh, targets=tg, mc=float(d.mean()), se=float(d.std(ddof=1) / math.sqrt(nn)),
                        closed=one_step_kills(sh, tg, P_HIT)))
    res["volley1"] = out
    # 異なる当たりの数え方を、実際に1本ずつ的を選んで数えた結果と比べる（小さい例）
    exp_rows = []
    rng2 = rng_for(seed, 2)
    for shots, tg in ((30, 20), (200, 100), (60, 400)):
        reps = 4000
        picks = rng2.integers(0, tg, (reps, shots))
        dist_exp = np.array([len(np.unique(row)) for row in picks])
        sS = np.full(reps, shots)
        dist_fast = _distinct(sS, np.full(reps, tg), rng2)
        exp_rows.append(dict(shots=shots, targets=tg, explicit=float(dist_exp.mean()),
                             explicit_se=float(dist_exp.std(ddof=1) / math.sqrt(reps)), fast=float(dist_fast.mean()),
                             fast_se=float(dist_fast.std(ddof=1) / math.sqrt(reps)), closed=tg * (1 - (1 - 1 / tg) ** shots)))
    res["distinct_check"] = exp_rows
    tick("射撃の数え方の照合")

    # ---- ラダー ----
    res["ladder"] = []
    for sid, nm, cfg in ladder_defs():
        st = run_cfg(cfg, N_TRIALS, seed, sid)
        st.update(id=sid, label=nm, cfg=cfg)
        res["ladder"].append(st)
        tick(f"{sid} {st['wins']}/{N_TRIALS}")
    # L1 を10万回
    big = run_cfg(cfg_make(H=TOTAL), N_BIG, seed + 1, "L1-big")
    big["label"] = "L1 を10万回"
    res["l1_big"] = big
    big2 = run_cfg(cfg_make(H=HONJIN), N_BIG, seed + 1, "L2-big")
    big2["label"] = "L2 を10万回"
    res["l2_big"] = big2
    tick("L1・L2 10万回")

    # ---- 腕前の倍率 ----
    k = {}
    for lab, G in (("L1", TOTAL), ("L2", HONJIN)):
        th = (G / ODA) ** 2
        kmf = k50_mean_field(ODA, G)
        kmc = k50_mc(ODA, G, seed, n=N_K50)
        rows = []
        for mult in (0.8, 1.0, 1.25):
            rows.append(dict(mult=mult, k=th * mult, win=win_rate_k(ODA, G, th * mult, seed + 5, n=1000, key=G)))
        k[lab] = dict(G=G, theory=th, mean_field=kmf, mc=kmc, rows=rows)
        tick(f"{lab} 腕前の倍率 理論{th:.2f} 平均場{kmf:.2f} 数え方{kmc:.2f}")
    res["k50"] = k

    # ---- L5 ----
    res["l5"] = []
    for sid, nm, cfg in l5_defs():
        st = run_cfg(cfg, N_TRIALS, seed + 2, sid)
        st.update(id=sid, label=nm, cfg=cfg)
        res["l5"].append(st)
    tick("L5")

    # ---- 崩れ r ごとの勝ち（崖）----
    curves = {}
    cdefs = [("field", "野原・雨の不意打ちあり（s=0〜3）", dict(s=S_SET)),
             ("field_s0", "野原・雨の不意打ちなし", dict(s=0)),
             ("W50", "谷 幅50・雨の不意打ちあり", dict(s=S_SET, W=50)),
             ("W100", "谷 幅100・雨の不意打ちあり", dict(s=S_SET, W=100)),
             ("W200", "谷 幅200・雨の不意打ちあり", dict(s=S_SET, W=200)),
             ("W50_s0", "谷 幅50・雨の不意打ちなし", dict(s=0, W=50))]
    for cid, lab, kw in cdefs:
        rows = []
        for rr in R_CURVE:
            cfg = cfg_make(r=rr, **kw)
            raw = simulate(cfg, N_TRIALS, seed + 3, f"curve:{cid}:{rr}")
            st = summarize(raw)
            rows.append(dict(r=rr, wins=st["wins"], n=N_TRIALS, rate=st["rate"], ci=st["ci"], surv_mean=st["surv_mean"],
                             volleys_mean=st["volleys_mean"], inv_ok=st["inv_ok"]))
        curves[cid] = dict(label=lab, rows=rows)
        tick(f"崩れ r の曲線 {cid}")
    res["rcurve"] = curves

    # 平均場の目安（織田が本陣を何割まで削れるか）
    mf = []
    for lab, kw in (("野原", dict()), ("谷 幅200", dict(W=200)), ("谷 幅100", dict(W=100)), ("谷 幅50", dict(W=50))):
        row = dict(label=lab)
        for s_ in (0, 1, 2, 3):
            row[f"s{s_}"] = mean_field_cliff(ODA, HONJIN, s=s_, **kw)
        mf.append(row)
    res["mf_cliff"] = mf
    res["mf_cliff_H6"] = {lab: mean_field_cliff(ODA, 6000, s=0, **kw) for lab, kw in (("野原", {}), ("谷 幅100", dict(W=100)))}
    res["mf_cliff_O3"] = {lab: mean_field_cliff(3000, HONJIN, s=0, **kw) for lab, kw in (("野原", {}), ("谷 幅100", dict(W=100)))}

    # 平均場と数え方の突き合わせ（敗走なしで最後まで戦った回の、本陣の削れ）
    cmp_rows = []
    for lab, kw in (("野原 s=0", dict(W=None, s=0)), ("野原 s=3", dict(W=None, s=3)), ("谷50 s=0", dict(W=50, s=0)),
                    ("谷100 s=0", dict(W=100, s=0)), ("谷200 s=0", dict(W=200, s=0)), ("谷100 s=3", dict(W=100, s=3))):
        cfg = cfg_make(**kw)
        raw = simulate(cfg, 4000, seed + 4, f"cmp:{lab}")
        f = raw["first"]
        lf = (HONJIN - f["G"]) / HONJIN
        Wm = W_FIELD if kw["W"] is None else kw["W"]
        cmp_rows.append(dict(label=lab, W=kw["W"], s=kw["s"], mc=float(lf.mean()), se=float(lf.std(ddof=1) / math.sqrt(len(lf))),
                             mf=mean_field_cliff(ODA, HONJIN, W=Wm, s=kw["s"]),
                             lanchester=(1 - lanchester_square(HONJIN, ODA) / HONJIN) if kw["W"] is None and kw["s"] == 0 else None,
                             wins=int(f["won"].sum())))
    res["mf_compare"] = cmp_rows
    tick("平均場との突き合わせ")

    # 崖の位置を挟んで勝ちが分かれるか（固定 r・平均場の崖の 0.7倍 と 1.3倍）
    cl = []
    for lab, kw in (("野原 s=0", dict(W=None, s=0)), ("谷50 s=0", dict(W=50, s=0)), ("谷100 s=0", dict(W=100, s=0)),
                    ("谷200 s=0", dict(W=200, s=0)), ("谷100 s=3", dict(W=100, s=3))):
        Wm = W_FIELD if kw["W"] is None else kw["W"]
        c = mean_field_cliff(ODA, HONJIN, W=Wm, s=kw["s"])
        row = dict(label=lab, cliff=c)
        for tag, mult in (("low", 0.7), ("high", 1.3)):
            cfg = cfg_make(r=c * mult, **kw)
            st = run_cfg(cfg, 3000, seed + 6, f"cliff:{lab}:{tag}")
            row[tag] = dict(r=c * mult, rate=st["rate"], wins=st["wins"], n=st["n"])
        cl.append(row)
    res["cliff_check"] = cl
    tick("崖の位置")

    # ---- L6 ----
    res["l6"] = []
    for sid, nm, cfg in l6_defs():
        st = run_cfg(cfg, N_TRIALS, seed + 7, sid)
        st.update(id=sid, label=nm, cfg=cfg)
        res["l6"].append(st)
    tick("L6")

    # ---- L7 ----
    res["l7"] = []
    for sid, nm, cfg in l7_defs():
        st = run_cfg(cfg, N_TRIALS, seed + 8, sid)
        st.update(id=sid, label=nm, cfg=cfg)
        res["l7"].append(st)
    tick("L7")

    # ---- 別の乱数で、ラダー（L1〜L4・L7）と L5・L6・L7 をやり直す ----
    ag = {}
    for sid, nm, cfg in ladder_defs():
        ag[sid] = run_cfg(cfg, N_TRIALS, SEED_AGAIN, sid)
    for sid, nm, cfg in l5_defs() + l6_defs() + l7_defs():
        ag[sid] = run_cfg(cfg, N_TRIALS, SEED_AGAIN + 1, sid)
    res["again"] = ag
    tick("別の乱数")

    # ---- 画面の見本 ----
    res["samples"] = compute_samples(res)
    tick("画面の見本")
    res["elapsed"] = time.time() - t0
    return res


def _lad(res, sid):
    for st in res["ladder"] + res["l5"] + res["l6"] + res["l7"]:
        if st["id"] == sid:
            return st
    raise KeyError(sid)


def compute_samples(res):
    """段ごとに、ふつうの負け1つ。L3・L4・L7 は勝ち1つも。L6 は『本陣に勝ったがその先で負ける』1つ。谷は幅ごとにも。
    勝ちが何千分の1しかない段は『まれな勝ち』（step_win_rate に率を残す）"""
    ss = {}
    seed = SEED_SAMPLE
    defs = {sid: cfg for sid, _, cfg in ladder_defs()}
    for sid in ("L1", "L2", "L3", "L4", "L7"):
        rate = _lad(res, sid)["rate"]
        ss[f"{sid}_loss"] = find_sample(sid, defs[sid], "loss", seed, rate)
        if sid in ("L3", "L4", "L7"):
            ss[f"{sid}_win"] = find_sample(sid, defs[sid], "win", seed, rate)
    for W in W_SET:
        cfg = cfg_make(r=R_RANGE, s=S_SET, W=W)
        rate = _lad(res, f"L7-W{W}")["rate"]
        ss[f"L7-W{W}_loss"] = find_sample(f"L7-W{W}", cfg, "loss", seed, rate)
        ss[f"L7-W{W}_win"] = find_sample(f"L7-W{W}", cfg, "win", seed, rate)
    # L6: 本陣に勝ったあと後ろの組で負ける
    for sid in ("L6-25000-4",):
        cfg = [c for i_, _, c in l6_defs() if i_ == sid][0]
        rate = _lad(res, sid)["rate"]
        ss["L6_first_then_loss"] = find_sample(sid, cfg, "win_first", seed, _lad(res, sid)["rate_first"])
        ss["L6_first_then_loss"]["all_win_rate"] = rate
    return ss


# ============================================================
# 7. 照合
# ============================================================
def se_rate(p, n):
    return math.sqrt((p * (1 - p) + 1.0 / n) / n)


def se_pair(a, b):
    """2つの勝率（ともに st）の差の標準誤差。0 のときも下限を持たせる"""
    return math.hypot(se_rate(a["rate"], a["n"]), se_rate(b["rate"], b["n"]))


def check(res):
    checks = []
    ld = {st["id"]: st for st in res["ladder"]}
    ag = res["again"]
    # ---------- 射撃の数え方 ----------
    for v in res["volley1"]:
        checks.append((f"1回の一斉射撃 {v['shooters']}人が{v['targets']}人を撃つ: 異なる当たりの数 vs 閉じた式", v["mc"], v["closed"], 4 * v["se"] + 1e-9))
    for e in res["distinct_check"]:
        checks.append((f"異なる当たりの数 {e['shots']}本→{e['targets']}人: 速い数え方 vs 1本ずつ的を選んだ数え方", e["fast"], e["explicit"],
                       4 * math.hypot(e["fast_se"], e["explicit_se"])))
        checks.append((f"異なる当たりの数 {e['shots']}本→{e['targets']}人: 速い数え方 vs 閉じた式", e["fast"], e["closed"], 4 * e["fast_se"]))
    # ---------- 平均場・ランチェスターとの突き合わせ ----------
    for c in res["mf_compare"]:
        tol = 0.02 if c["W"] is None else 0.03
        checks.append((f"本陣の削れ（敗走なし）{c['label']}: 数え方 vs 平均場（±{tol * 100:.0f}pt）", c["mc"], c["mf"], tol))
        if c["lanchester"] is not None:
            checks.append((f"本陣の削れ（敗走なし）{c['label']}: 数え方 vs ランチェスター 1−√(5000²−2000²)/5000（±2pt）", c["mc"], c["lanchester"], 0.02))
    # 崖の位置: 平均場の崖の 0.7倍 では大半が勝ち、1.3倍 では大半が負け
    for c in res["cliff_check"]:
        checks.append((f"崖の位置 {c['label']}: r＝平均場の崖×0.7 で勝率 ≧ 85%", float(c["low"]["rate"] >= 0.85), 1.0, 0))
        checks.append((f"崖の位置 {c['label']}: r＝平均場の崖×1.3 で勝率 ≦ 15%", float(c["high"]["rate"] <= 0.15), 1.0, 0))
    # ---------- 腕前の倍率 ----------
    k = res["k50"]
    checks.append(("腕前の倍率 L1: 平均場 vs 理論 (25000/2000)²＝156.25（±1.5%）", k["L1"]["mean_field"], k["L1"]["theory"], 0.015 * k["L1"]["theory"]))
    checks.append(("腕前の倍率 L2: 平均場 vs 理論 (5000/2000)²＝6.25（±1.5%）", k["L2"]["mean_field"], k["L2"]["theory"], 0.015 * k["L2"]["theory"]))
    checks.append(("腕前の倍率 L1: 1人ずつの数え方 vs 理論（±8%）", k["L1"]["mc"], k["L1"]["theory"], 0.08 * k["L1"]["theory"]))
    checks.append(("腕前の倍率 L2: 1人ずつの数え方 vs 理論（±8%）", k["L2"]["mc"], k["L2"]["theory"], 0.08 * k["L2"]["theory"]))
    for lab in ("L1", "L2"):
        rs = k[lab]["rows"]
        checks.append((f"腕前の倍率 {lab}: 理論の0.8倍で勝率 ≦ 10%", float(rs[0]["win"] <= 0.10), 1.0, 0))
        checks.append((f"腕前の倍率 {lab}: 理論の1.25倍で勝率 ≧ 90%", float(rs[2]["win"] >= 0.90), 1.0, 0))
        checks.append((f"腕前の倍率 {lab}: 理論どおりの倍率で勝率が 25〜75%", rs[1]["win"], 0.5, 0.25))
    # ---------- ラダー ----------
    checks.append(("L1 野原・全軍: 勝ち 0/1万回", float(ld["L1"]["wins"]), 0.0, 0))
    checks.append(("L1 野原・全軍: 勝ち 0/10万回", float(res["l1_big"]["wins"]), 0.0, 0))
    checks.append(("L2 本陣だけ（崩れなし）: 勝ち 0/1万回", float(ld["L2"]["wins"]), 0.0, 0))
    checks.append(("L2 本陣だけ（崩れなし）: 勝ち 0/10万回", float(res["l2_big"]["wins"]), 0.0, 0))
    order = ["L1", "L2", "L3", "L4", "L7"]
    for a, b in zip(order[:-1], order[1:]):
        checks.append((f"ラダーが増えていく方向: {a} ≦ {b}（誤差3SE）", float(ld[a]["rate"] <= ld[b]["rate"] + 3 * se_pair(ld[a], ld[b])), 1.0, 0))
    checks.append(("ラダー L7 ≧ L4 で、増えた分が誤差より大きい（L7−L4 ≧ 5pt）", ld["L7"]["rate"] - ld["L4"]["rate"], 0.5, 0.5 - 0.05))
    # 保存則・不変条件
    all_st = res["ladder"] + res["l5"] + res["l6"] + res["l7"] + [res["l1_big"], res["l2_big"]]
    checks.append((f"保存則: 織田は増えない・今川は0〜最初の人数・勝ちのとき織田が生きている（{len(all_st)}条件）", float(all(s["inv_ok"] for s in all_st)), 1.0, 0))
    curve_ok = all(r_["inv_ok"] for c in res["rcurve"].values() for r_ in c["rows"])
    checks.append(("保存則: 崩れ r の曲線の全試行（敗走した回は r 以上を失っている）", float(curve_ok), 1.0, 0))
    checks.append(("後ろの組: 全部に勝つ ≦ 本陣に勝つ（全条件）", float(all(s["wins"] <= s["wins_first"] for s in res["l6"])), 1.0, 0))
    for s in res["l6"]:
        checks.append((f"L6 {s['id']}: reach が減っていく", float(all(a >= b for a, b in zip(s["reach"], s["reach"][1:]))), 1.0, 0))
    checks.append(("L6 後ろの2万人まで勝ち切るのは 0 回（総勢20,000/25,000/45,000 の全条件）",
                   float(sum(s["wins"] for s in res["l6"] if s["id"].startswith("L6-2") or s["id"].startswith("L6-4"))), 0.0, 0))
    # ---------- 崩れ r の曲線 ----------
    for cid, c in res["rcurve"].items():
        rows = c["rows"]
        mono = all(b["rate"] <= a["rate"] + 3 * math.hypot(se_rate(a["rate"], a["n"]), se_rate(b["rate"], b["n"]))
                   for a, b in zip(rows[:-1], rows[1:]))
        checks.append((f"崩れ r の曲線 {cid}: r が大きいほど勝率は下がる（誤差3SE）", float(mono), 1.0, 0))
        checks.append((f"崩れ r の曲線 {cid}: 最小の r で勝率が最大", float(rows[0]["rate"] >= max(x["rate"] for x in rows) - 3 * se_rate(rows[0]["rate"], rows[0]["n"])), 1.0, 0))
    # 谷の幅が狭いほど勝ちやすい（r=0.3, s あり）
    def rate_at(cid, rr):
        return [x for x in res["rcurve"][cid]["rows"] if abs(x["r"] - rr) < 1e-9][0]["rate"]
    checks.append(("谷が狭いほど勝ちやすい（r=0.3）: 野原 ≦ 谷200 ≦ 谷100 ≦ 谷50",
                   float(rate_at("field", 0.30) <= rate_at("W200", 0.30) + 0.02 <= rate_at("W100", 0.30) + 0.04 <= rate_at("W50", 0.30) + 0.06), 1.0, 0))
    # L7 の幅ごと
    l7 = {st["id"]: st for st in res["l7"]}
    checks.append(("L7 幅ごとの平均 ≒ 幅を混ぜた L7（3SE）", (l7["L7-W50"]["rate"] + l7["L7-W100"]["rate"] + l7["L7-W200"]["rate"]) / 3, ld["L7"]["rate"],
                   3 * se_pair(ld["L7"], ld["L7"]) / 2 + 0.01))
    checks.append(("L7 幅ごと: 幅が狭いほど勝ちやすい（50 ≧ 200 − 誤差）", float(l7["L7-W50"]["rate"] >= l7["L7-W200"]["rate"] - 3 * se_pair(l7["L7-W50"], l7["L7-W200"])), 1.0, 0))
    # 勝つ回の内訳が整合: L3〜L4 の s・r 別の合計
    for sid in ("L3", "L4", "L7"):
        st = ld[sid]
        checks.append((f"{sid} の内訳(r の区間)の勝ちの合計 ＝ 全体の勝ち", float(sum(b["wins"] for b in st["by_r"])), float(st["wins"]), 0))
    checks.append(("L4 の内訳(s 別)の勝ちの合計 ＝ 全体の勝ち", float(sum(v["wins"] for v in ld["L4"]["by_s"].values())), float(ld["L4"]["wins"]), 0))
    checks.append(("L7 の内訳(幅別)の勝ちの合計 ＝ 全体の勝ち", float(sum(v["wins"] for v in ld["L7"]["by_W"].values())), float(ld["L7"]["wins"]), 0))
    # ---------- 別の乱数でやり直し（3SE 以内）----------
    n_cmp = 0
    for sid, a in ag.items():
        b = _lad(res, sid) if sid in {s["id"] for s in all_st if "id" in s} else None
        if b is None:
            continue
        tol = 3.5 * se_pair(a, b)   # 約50件の比較を並べるので、1件ごとの基準は 2SE ではなく 3.5SE（ボンフェローニ。2SE だと偶然で1〜2件は外れる）
        checks.append((f"別の乱数 {sid}: 勝率（3.5SE 以内）", a["rate"], b["rate"], tol))
        n_cmp += 1
        if a["wins"] > 200 and b["wins"] > 200 and a.get("surv_mean") and b.get("surv_mean"):
            checks.append((f"別の乱数 {sid}: 勝った回の残りの平均（±{max(25, 0.05 * b['surv_mean']):.0f}人）", a["surv_mean"], b["surv_mean"],
                           max(25.0, 0.05 * b["surv_mean"])))
    # ---------- 画面の見本 ----------
    ss = res["samples"]
    for key, sm in ss.items():
        if sm is None:
            continue
        tr = sm["traj"]
        checks.append((f"見本 {key}: 経過の最初は 織田{sm['O0']}・今川{sm['H0']}", float(tr[0] == [sm["O0"], sm["H0"]]), 1.0, 0))
        checks.append((f"見本 {key}: 経過の最後 ＝ 最終の人数", float(tr[-1] == [sm["O_end"], sm["G_end"]]), 1.0, 0))
        checks.append((f"見本 {key}: 経過の長さ ＝ 一斉射撃の回数+1", float(len(tr) == sm["volleys"] + 1), 1.0, 0))
        mono = all(b[0] <= a[0] and b[1] <= a[1] for a, b in zip(tr[:-1], tr[1:]))
        checks.append((f"見本 {key}: 人数は増えない", float(mono), 1.0, 0))
        if sm["s"] > 0:
            free = min(sm["s"], sm["volleys"])
            checks.append((f"見本 {key}: 雨の不意打ち{sm['s']}回のあいだ織田は減らない", float(all(tr[i][0] == sm["O0"] for i in range(free + 1))), 1.0, 0))
        if sm["kind"] == "win" and sm["result"] == "rout":
            checks.append((f"見本 {key}: 敗走のとき今川は r={sm['r']} 以上を失っている", float(sm["h_lost_frac"] >= sm["r"] - 1e-9), 1.0, 0))
        if sm["kind"] == "win":
            checks.append((f"見本 {key}: 勝ちなので織田が生きている", float(sm["O_end"] > 0), 1.0, 0))
        if sm["kind"] == "loss":
            checks.append((f"見本 {key}: 負けなので織田が全滅", float(sm["O_end"] == 0), 1.0, 0))
    check_answers(checks)
    print(f"照合 {len(checks)} 件 OK")


# ============================================================
# 8. numbers.md
# ============================================================
def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def pcr(st, d=2):
    lo, hi = st["ci"]
    return f"{pc(lo, d)}〜{pc(hi, d)}"


def f0(x):
    return "—" if x is None else f"{x:,.0f}"


def row_md(label, st, with_first=False):
    w, n = st["wins"], st["n"]
    star = " (★1)" if w == 0 else ""
    surv = f0(st["surv_mean"]) + (f"（中央値 {f0(st['surv_median'])}）" if st["surv_mean"] is not None else "")
    cells = [label, f"{w:,}/{n:,}{star}", pc(st["rate"], 2), pcr(st), surv, pc(st["h_lost_mean"], 1)]
    if with_first:
        cells.insert(2, f"{st['wins_first']:,}")
    return "| " + " | ".join(cells) + " |"


HEAD = "| 条件 | 織田の勝ち/回数 | 勝率 | 95%の範囲 | 勝った回の織田の残り（平均） | 本陣を削った割合（平均） |\n|---|---|---|---|---|---|"
HEAD6 = ("| 条件 | 織田の勝ち（全部）/回数 | 本陣に勝つ | 勝率 | 95%の範囲 | 本陣に勝った回の織田の残り（平均） | 後ろまで勝った回の残り |\n"
         "|---|---|---|---|---|---|---|")


# 2026-10-22 ラベルの訂正（計算は変えない）: r は「本陣が失った割合で敗走」なので、r が大きいほど崩れにくい（織田に不利）。
# data.json に入っている古いラベル（「崩れやすい」など）を numbers.md に書くときだけ言い換える。
RELABEL = {
    "崩れやすさ 2割〜5割（崩れやすい）": "崩れる所 2割〜5割（基本の1割〜5割より崩れにくい＝織田に不利）",
    "崩れやすさ 1割〜3割（崩れにくい）": "崩れる所 1割〜3割（基本より崩れやすい＝織田に有利）",
    "崩れやすさ 3割〜5割（さらに崩れにくい）": "崩れる所 3割〜5割（基本よりさらに崩れにくい＝織田にさらに不利）",
    "織田3千・本陣4千・崩れやすい2〜5割（織田に有利なものを全部）":
        "織田3千・本陣4千・崩れる所2〜5割（人数は織田に有利。ただし崩れる所の2〜5割は基本より織田に不利。『有利なもの全部』ではない）",
    "総勢25,000・織田に有利なもの全部（3千・本陣4千・2〜5割）で後ろの2万が1組":
        "総勢25,000・織田3千・本陣4千・崩れる所2〜5割（人数は有利、崩れる所は基本より不利）で後ろの2万が1組",
    "谷＋崩れやすさ 2割〜5割": "谷＋崩れる所 2割〜5割（基本より崩れにくい＝不利）",
    "谷＋崩れやすさ 1割〜3割": "谷＋崩れる所 1割〜3割（基本より崩れやすい＝有利）",
    "谷＋崩れやすさ 3割〜5割": "谷＋崩れる所 3割〜5割（基本よりさらに崩れにくい＝さらに不利）",
}


def relab(s):
    return RELABEL.get(s, s)


def write_numbers(res):
    L = []
    a = L.append
    ld = {st["id"]: st for st in res["ladder"]}
    l5 = {st["id"]: st for st in res["l5"]}
    l6 = {st["id"]: st for st in res["l6"]}
    l7 = {st["id"]: st for st in res["l7"]}
    k = res["k50"]
    n = N_TRIALS
    a("# 桶狭間ロング 数字一覧 — 織田2千 vs 今川2万5千（本陣5千）")
    a("")
    a(f"自動生成（sims/okehazama-long.py --numbers）。**手で編集しない。** 計算 {res['elapsed']:.0f}秒。")
    a(f"撃ち合いは合戦ロングと同じ（1人が1回で当てる確率 p=1/25、両軍が同時に撃つ、同じ兵に2本当たっても倒れるのは1人）。各条件 {n:,} 回、種は固定（本番 {res['params']['seed']}、やり直し {SEED_AGAIN}）。")
    a("引き分け（同じ回に両軍全滅）は勝ちに数えない。勝率の「95%の範囲」はウィルソン区間。★1＝0回のとき（10万回でも0なら、勝率は0.0037%未満）。")
    a("")
    a("## 前提（言うときはここまで）")
    a("")
    a("- **織田は崩れない（最後まで戦う）**【仮定】。織田が先に全滅したら負け。")
    a(f"- **勝ち**＝義元の本陣（{HONJIN:,}人）が敗走するか全滅すること。本陣は「最初の人数の r を失った時点」で敗走する。")
    a("- **r は戦いごとに引く**（これが「もう一度戦ったら」のばらつき）。基本は 1割〜5割の一様【史料に根拠なし。幅は主観】。")
    a("- **雨の不意打ち**: 信長公記は「雨が今川の顔に打ちつけ、晴れてから攻めた」と書く。→ 織田だけが先に s 回撃てる（s は 0〜3 から一様）。**「雨で弓が使えなかった」は史料にない。**")
    a("- **江戸版の谷**（田楽狭間の谷底）は**江戸時代の脚色**で史実ではない。義元の陣は丘の上。両軍とも前線の W 人しか撃てない（W は 50/100/200 から一様）。")
    a(f"- 総勢 {TOTAL:,}（別説 20,000／45,000）、本陣 {HONJIN:,}（別説 6,000）、織田 {ODA:,}（別説 3,000）。")
    a("")
    # ------------------------------------------------------------------
    a("## ラダー（1段ごとに条件を1つ足す。各1万回）")
    a("")
    a(HEAD)
    ladder_rows = [("L1 野原・全軍（崩れなし・不意打ちなし）", ld["L1"]),
                   ("L2 分かれていた（本陣5千だけ、崩れなし）", ld["L2"]),
                   ("L3 ＋崩れ（r は1割〜5割で毎回変わる）", ld["L3"]),
                   ("L4 ＋雨の不意打ち（織田が先に0〜3回撃つ）", ld["L4"])]
    for lab, st in ladder_rows:
        a(row_md(lab, st))
    a(row_md("（L7）江戸版の谷（L4 ＋ 幅50/100/200）", ld["L7"]))
    a("")
    a("- L1 の「本陣を削った割合」は全軍25,000に対する割合（本陣ではない）。")
    a(f"- L1 を 10万回: **{res['l1_big']['wins']}/{N_BIG:,}**。L2 を 10万回: **{res['l2_big']['wins']}/{N_BIG:,}**。")
    a(f"- L1 で今川は平均 {res['ladder'][0]['g_left_mean']:,.0f}人 残る（全軍25,000のうち）。織田が先に全滅するまでの一斉射撃は平均 {res['ladder'][0]['volleys_mean']:.1f} 回。")
    a(f"- L2 で本陣を削れるのは平均 {pc(ld['L2']['h_lost_mean'], 1)}（{ld['L2']['h_lost_mean'] * HONJIN:,.0f}人）。ランチェスターの2次法則では 1−√(5000²−2000²)/5000 ＝ {pc(1 - lanchester_square(HONJIN, ODA) / HONJIN, 1)}。**「4割」ではなく1割弱**。")
    a("")
    # ------------------------------------------------------------------
    a("## L1・L2 で五分五分になる腕前の倍率")
    a("")
    a("| 勝負 | 理論 (敵÷織田)² | 平均場 | 1人ずつの確率の数え方（n=400, 二分探索） |")
    a("|---|---|---|---|")
    for lab, nm in (("L1", "2千 vs 2万5千（全滅させる）"), ("L2", "2千 vs 本陣5千（全滅させる）")):
        a(f"| {nm} | {k[lab]['theory']:.2f} | {k[lab]['mean_field']:.1f} | {k[lab]['mc']:.1f} |")
    a("")
    a("理論の倍率のまわりの勝率（n=1,000）:")
    a("")
    a("| 勝負 | 理論の0.8倍 | 理論どおり | 理論の1.25倍 |")
    a("|---|---|---|---|")
    for lab in ("L1", "L2"):
        rs = k[lab]["rows"]
        a(f"| {lab} | k={rs[0]['k']:.1f}: {pc(rs[0]['win'], 1)} | k={rs[1]['k']:.1f}: {pc(rs[1]['win'], 1)} | k={rs[2]['k']:.1f}: {pc(rs[2]['win'], 1)} |")
    a("")
    a("（腕前 k ＝ 織田の1人が1回に出す当たりの期待が k×p。2次法則なので、2千で2万5千に五分で勝つには1人が約156倍。）")
    a("")
    # ------------------------------------------------------------------
    a("## 平均場（期待値だけで進める）: 織田は本陣を何割まで削れるか")
    a("")
    a("崩れの割合 r がこれより小さければ勝てる、の目安（敗走なしで戦い続け、織田が尽きたとき）。")
    a("")
    a("| 場所 | 雨の不意打ち s=0 | s=1 | s=2 | s=3 |")
    a("|---|---|---|---|---|")
    for r_ in res["mf_cliff"]:
        a(f"| {r_['label']} | {pc(r_['s0'], 1)} | {pc(r_['s1'], 1)} | {pc(r_['s2'], 1)} | {pc(r_['s3'], 1)} |")
    a("")
    a(f"- 本陣6千: 野原 {pc(res['mf_cliff_H6']['野原'], 1)}、谷100 {pc(res['mf_cliff_H6']['谷 幅100'], 1)}（s=0）。織田3千・本陣5千: 野原 {pc(res['mf_cliff_O3']['野原'], 1)}、谷100 {pc(res['mf_cliff_O3']['谷 幅100'], 1)}（s=0）。")
    a("- 数え方（1万回のうち4,000回）との突き合わせ:")
    a("")
    a("| 場所 | 数え方（本陣を削った割合） | 平均場 |")
    a("|---|---|---|")
    for c in res["mf_compare"]:
        a(f"| {c['label']} | {pc(c['mc'], 1)} ± {c['se'] * 100:.2f} | {pc(c['mf'], 1)} |")
    a("")
    # ------------------------------------------------------------------
    a("## L5 置き方を変えたら（L4 から1つだけ変える。各1万回）")
    a("")
    a("※ r は「本陣が失った割合で敗走」する点。**r が大きいほど崩れにくく（織田に不利）、小さいほど崩れやすい（有利）**。基本は r＝1割〜5割。")
    a("")
    a(HEAD)
    for st in res["l5"]:
        a(row_md(relab(st["label"]), st))
    a("")
    # ------------------------------------------------------------------
    a("## 崩れる割合 r で勝ちはどう変わるか（r を固定。各1万回。雨の不意打ちは s=0〜3 を毎回引く）")
    a("")
    cids = ["field", "field_s0", "W200", "W100", "W50", "W50_s0"]
    a("| r（本陣が失った割合で敗走） | 失った人数 | " + " | ".join(res["rcurve"][c]["label"] for c in cids) + " |")
    a("|---|---|" + "---|" * len(cids))
    for i, rr in enumerate(R_CURVE):
        cells = [f"{pc(res['rcurve'][c]['rows'][i]['rate'], 1)}" for c in cids]
        a(f"| {rr * 100:.0f}% | {rr * HONJIN:,.0f}人 | " + " | ".join(cells) + " |")
    a("")
    a("崖の位置（勝率が50%を切る r。直線補間）:")
    a("")
    for c in cids:
        rows = res["rcurve"][c]["rows"]
        pos = None
        for x, y in zip(rows[:-1], rows[1:]):
            if x["rate"] >= 0.5 > y["rate"]:
                pos = x["r"] + (x["rate"] - 0.5) / max(x["rate"] - y["rate"], 1e-12) * (y["r"] - x["r"])
                break
        if pos is None:
            pos = f"（最小の r={rows[0]['r'] * 100:.0f}% で既に {pc(rows[0]['rate'], 0)}）" if rows[0]["rate"] < 0.5 else "（r=50% でも50%以上）"
            a(f"- {res['rcurve'][c]['label']}: {pos}")
        else:
            a(f"- {res['rcurve'][c]['label']}: r ≒ {pos * 100:.1f}%（失う人数 ≒ {pos * HONJIN:,.0f}人）")
    a("")
    a("崖の位置が理論の目安（上の平均場の表）と一致する。野原は織田2千の火力では本陣を1割弱しか削れないので、崖が「1割」の近く。谷では直線則に近づき「4割＝2000/5000」の近く。")
    a("")
    # ------------------------------------------------------------------
    a("## L6 後ろの2万人（本陣に勝ったあと、残りの今川が1組ずつ来る。L4 の条件。野原）")
    a("")
    a(HEAD6)
    for st in res["l6"]:
        a(f"| {relab(st['label'])} | {st['wins']:,}/{st['n']:,}{' (★1)' if st['wins'] == 0 else ''} | {st['wins_first']:,}（{pc(st['rate_first'], 2)}） | {pc(st['rate'], 2)} | {pcr(st)} | "
          f"{f0(st['surv_first_mean'])} | {f0(st['surv_mean'])} |")
    a("")
    a("- 各組を倒した回数（reach: 本陣→1組目→…）:")
    for st in res["l6"]:
        a(f"  - {relab(st['label'])}: {st['reach']}")
    a("- 野原では、総勢が 2万・2万5千・4万5千 のどれでも、本陣に勝った後に後ろの組へ勝つ回は0（総勢の違いは「本陣に勝つ」までには影響しない。本陣が5千のままなので）。")
    vs = l6.get("L6-valley")
    if vs:
        a(f"- 江戸版の谷のままなら、後ろの組にも一部は勝つ（reach {vs['reach']}）。それでも2万人全部には届かない（全部に勝つ {vs['wins']}/{vs['n']:,}）。")
    a("")
    # ------------------------------------------------------------------
    a("## L7 江戸版の谷（※史実でない脚色。L4 ＋ 前線の幅）")
    a("")
    a(HEAD)
    a(row_md("L4 野原（比較）", ld["L4"]))
    a(row_md("L7 谷（幅50/100/200 を毎回引く）", ld["L7"]))
    for W in W_SET:
        a(row_md(f"　谷の幅 {W} だけ", l7[f"L7-W{W}"]))
    for sid in ("L7-s0", "L7-r25", "L7-r13", "L7-r35", "L7-H6", "L7-O3", "L7-all"):
        a(row_md(relab(l7[sid]["label"]), l7[sid]))
    a("")
    a("谷の中の勝ちの内訳（L7: 幅別・雨別・r別）:")
    a("")
    a("| 内訳 | 勝ち/回数 | 勝率 |")
    a("|---|---|---|")
    for key, v in ld["L7"]["by_W"].items():
        a(f"| 幅 {key} | {v['wins']}/{v['n']} | {pc(v['rate'], 1)} |")
    for key, v in ld["L7"]["by_s"].items():
        a(f"| 雨の不意打ち s={key} | {v['wins']}/{v['n']} | {pc(v['rate'], 1)} |")
    for v in ld["L7"]["by_r"]:
        a(f"| r {v['lo'] * 100:.0f}〜{v['hi'] * 100:.0f}% | {v['wins']}/{v['n']} | {pc(v['rate'], 1)} |")
    a("")
    a("谷の勝率の幅（幅ごと）: " + "〜".join([pc(min(l7[f'L7-W{W}']['rate'] for W in W_SET), 1), pc(max(l7[f'L7-W{W}']['rate'] for W in W_SET), 1)])
      + "。崩れる所・本陣の人数・織田の人数を変えた谷: " + "〜".join([pc(min(l7[s]['rate'] for s in ('L7-r25', 'L7-r13', 'L7-r35', 'L7-H6', 'L7-O3')), 1),
                                                                 pc(max(l7[s]['rate'] for s in ('L7-r25', 'L7-r13', 'L7-r35', 'L7-H6', 'L7-O3')), 1)]) + "。")
    a("")
    # ------------------------------------------------------------------
    a("## 各結果を動かしているもの")
    a("")
    f_mf = {r_["label"]: r_ for r_ in res["mf_cliff"]}
    a(f"- **L1（0）**: 2次法則。撃ち合いは「数の2乗」で効くので、2千で2万5千に勝つには腕前が約{k['L1']['theory']:.0f}倍必要。{N_BIG:,}回でも0。")
    a(f"- **L2（0）**: 本陣5千だけでも2次法則は同じ。五分にするには腕前が約{k['L2']['theory']:.2f}倍。織田は本陣の{pc(ld['L2']['h_lost_mean'], 0)}（{ld['L2']['h_lost_mean'] * HONJIN:,.0f}人）しか削れず全滅する。")
    a(f"- **L3（{pc(ld['L3']['rate'], 2)}）**: 崩れ r が 1割〜5割だと、織田が削れる約1割弱（{f_mf['野原']['s0'] * HONJIN:,.0f}人ほど）に届くのは r が 1割の端だけ。r の区間別の勝率: "
      + "、".join(f"{v['lo'] * 100:.0f}〜{v['hi'] * 100:.0f}%で{pc(v['rate'], 2)}" for v in ld["L3"]["by_r"]) + "。")
    a(f"- **L4（{pc(ld['L4']['rate'], 2)}）**: 雨の不意打ちで先に撃てる回が増えると、削れる割合が s=0 で{pc(f_mf['野原']['s0'], 1)}、s=3 で{pc(f_mf['野原']['s3'], 1)}。s 別の勝率: "
      + "、".join(f"s={k_}で{pc(v['rate'], 2)}" for k_, v in ld["L4"]["by_s"].items()) + "。")
    a(f"- **L5**: 織田が3千になる: {pc(l5['L5-3']['rate'], 2)}。本陣が6千: {pc(l5['L5-1']['rate'], 2)}。崩れる所 2〜5割（基本より崩れにくい＝不利）: {pc(l5['L5-4']['rate'], 2)}、1〜3割（崩れやすい＝有利）: {pc(l5['L5-5']['rate'], 2)}、3〜5割（さらに崩れにくい＝不利）: {pc(l5['L5-6']['rate'], 2)}。"
      f"織田3千・本陣4千に崩れる所2〜5割を重ねた行（旧ラベルは『有利なもの全部』）: {pc(l5['L5-9']['rate'], 2)}。この行は人数は有利だが、崩れる所は基本より不利な2〜5割を使っている（1〜3割にすれば、もっと上がる）。")
    best6 = l6.get("L6-best")
    a(f"- **L6（0）**: 本陣に勝っても、残りの2万人は別の大きな塊。織田の生き残りは平均 {f0(l6['L6-25000-1']['surv_first_mean'])}人（本陣に勝った回）。後ろの組の崩れ r を満たすには組の{R_RANGE[0] * 100:.0f}%以上を削る必要があり、数百人の織田には無理。"
      + (f"織田3千・本陣4千・崩れる所2〜5割（人数は有利・崩れる所は基本より不利）を重ねても {best6['wins']}/{best6['n']:,}。" if best6 else ""))
    a(f"- **L7（{pc(ld['L7']['rate'], 1)}）**: 谷は「前線に出られる人数」が両軍とも W に絞られ、人数の差が効かなくなる（2次法則 → 直線則）。削れる割合が{pc(f_mf['谷 幅100']['s0'], 0)}ほどに上がり、"
      f"崖が r≒4割に動く。幅が狭いほど織田に有利。幅別の勝率: " + "、".join(f"{W}で{pc(l7[f'L7-W{W}']['rate'], 1)}" for W in W_SET)
      + "。**ただし丘の上の本陣を谷に置くのは江戸の脚色で、史実の再現ではない。**")
    a("")
    a("## 見本（画面の動き用。data.json の samples）")
    a("")
    a("| 見本 | 種 | 一斉射撃の回数 | 織田の最後 | 今川の最後 | r | s | 幅 | 結果 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for key, sm in res["samples"].items():
        if sm is None:
            a(f"| {key} | （見つからず） | | | | | | | |")
            continue
        a(f"| {key} | {sm['seed']} #{sm['index']} | {sm['volleys']} | {sm['O_end']:,} | {sm['G_end']:,} | {'—' if sm['r'] is None else pc(sm['r'], 0)} | {sm['s']} | {sm['W'] or '野原'} | {sm['result']}（この段の勝率 {pc(sm['step_win_rate'], 2)}）|")
    a("")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"numbers.md を書きました: {OUT / 'numbers.md'}")


# ============================================================
# 9. 保存・読み込み・CLI
# ============================================================
def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def save(res):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(_jsonable(res), ensure_ascii=False, indent=1), encoding="utf-8")


def load():
    return json.loads((OUT / "data.json").read_text(encoding="utf-8"))


_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers", "--md"))
if __name__ == "__main__" and _MODEL_CLI:
    args = sys.argv[1:]
    if "--md" in args:                   # data.json から numbers.md だけ書き直す
        res = load()
        check(res)
        write_numbers(res)
        raise SystemExit
    if "--numbers" in args:
        print("計算します（数分）…", flush=True)
        res = _jsonable(compute())
        save(res)
        res = load()                      # 保存したものを読み直して照合・書き出し（画面側と同じ形）
    else:
        res = load()
    check(res)
    if "--numbers" in args:
        write_numbers(res)
    raise SystemExit


# ==== 場面 ====

# ####################################################################################################
# ここから下は場面（描画・音・照合・書き出し）。2026-10-22 追加（モデルの計算は変えていない）。
# 台本: publish/okehazama-long/narration_v1.md の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 形と部品は sims/densha-long.py の場面部分（見開きノート・付箋・数字の欄・章カード・終了画面・照合）。
#   足軽・のぼり・戦場の描き方は sims/kassen-long.py からコピー（織田＝左・青系、今川＝右・赤系）。
#
# 使い方
#   python -X utf8 sims/okehazama-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/okehazama-long.py --stills --fake-voice        要所の静止画と sheet_480.png（out/okehazama-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
#   python -X utf8 sims/okehazama-long.py --wraps --fake-voice         字幕の折り返しを全部表示
#   python -X utf8 sims/okehazama-long.py --readings --fake-voice      読みの確認（scene_work/readings.log）
#   （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
# ####################################################################################################
import re as _re
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (beat, bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh)
from engine.note import INK, MARKER, PAPER, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

FAKE = "--fake-voice" in sys.argv
VOICE_DIR = OUT / "voice"
WORK = OUT / "scene_work"


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本の読み込み（narration_v1.md の「- 」の行。文言は一字も変えない）
#   「- （無音 3秒・…）」＝声のない区間（Gap） ／ 「- （…）」「- 〔…〕」だけの行＝画面の指示（声にしない）
#   行の終わりの〔…〕＝その文のときの画面の絵（声にしない）
# ============================================================
NARR_PATH = ROOT / "publish" / SLUG / "narration_v1.md"
G_DEFAULT = {1: 4.0, 2: 4.0, 3: 4.0, 4: 4.0, 6: 4.0, 7: 4.0}          # 「無音」に秒数が書いていない区間の長さ


def parse_narration(path=NARR_PATH):
    chaps, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _re.match(r"##\s*(\d+)\s+(.+)$", raw)
        if m:
            cur = dict(n=int(m.group(1)), title=m.group(2).strip(), items=[])
            chaps.append(cur)
            continue
        if cur is None or not raw.startswith("- "):
            continue
        body = raw[2:].strip()
        if body.startswith("（無音"):
            ms = _re.match(r"（無音\s*(\d+(?:\.\d+)?)\s*秒", body)
            cur["items"].append(("gap", float(ms.group(1)) if ms else None, body))
        elif body.startswith("（") or body.startswith("〔"):
            cur["items"].append(("note", None, body))
        else:
            mn = _re.search(r"〔([^〕]*)〕\s*$", body)
            txt = (body[:mn.start()] if mn else body).strip()
            cur["items"].append(("line", txt, mn.group(1) if mn else ""))
    return chaps


CHAPS = parse_narration()
CH_TITLES = [c["title"] for c in CHAPS]
LINES = {}                         # 文の id -> (章, 文)
LINE_NOTE = {}                     # 文の id -> 〔画面の絵〕
GAP_NOTE = {}                      # 無音の id -> 注
CH_NOTE0 = {}                      # 章の最初の画面指示（（…）〔…〕のみの行）
SPEED_V = 1.0


SUB_MAX2 = 2 * lf.SUB_MAX                      # 字幕は2行まで（1行 28字）


def split_long(txt):
    """2行（56字）に収まらない文だけ、「。」の切れ目で分ける（文言は変えない）"""
    if len(txt) <= SUB_MAX2:
        return [txt]
    sents = [x + "。" for x in txt.split("。") if x]
    out, cur = [], ""
    for x in sents:
        if cur and len(cur) + len(x) > SUB_MAX2:
            out.append(cur)
            cur = x
        else:
            cur += x
    if cur:
        out.append(cur)
    res = []
    for part in out:                                     # 「。」で分けても 56字を超える文は、まん中に近い「、」で分ける
        if len(part) > SUB_MAX2:
            cuts = [i + 1 for i, ch_ in enumerate(part[:-1]) if ch_ == "、" and part[:i].count("{") == part[:i].count("}")]
            if cuts:
                k = min(cuts, key=lambda i: abs(i - len(part) / 2))
                res += [part[:k], part[k:]]
                continue
        res.append(part)
    return res


def _items():
    C, G = lf.Chapter, lf.Gap
    out = []
    for ch in CHAPS:
        n = ch["n"]
        out.append(C(ch["title"], id=f"ch{n}", gap=0.0 if n == 0 else 0.45))
        lines = [it for it in ch["items"] if it[0] == "line"]
        k, li = 0, 0
        for kind, val, note_ in ch["items"]:
            if kind == "line":
                li += 1
                for j, part in enumerate(split_long(val)):          # 字幕が2行に収まらない文は、文言を変えずに「。」で2つの Line に分ける
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and part is split_long(val)[-1]
                    out.append(lf.Line(lid, part, pause=0.3 if n == 0 else (0.6 if last else 0.35), speed=SPEED_V))
            elif kind == "gap":
                gid = f"g{n}"
                GAP_NOTE[gid] = note_
                out.append(G(gid, val if val else G_DEFAULT[n]))
            elif n not in CH_NOTE0:
                CH_NOTE0[n] = note_
    return out


@dataclass
class _FakeClip:
    text: str
    spoken: str
    duration: float

    def samples(self):
        return np.zeros(16, np.float32)


def _fake_synth(text_, cache_dir, speed=SPEED_V, **kw):
    shown_, spoken = split_reading(text_)
    n = len(shown_) + sum(max(0, len(m.group(2)) * 0.55 - len(m.group(1)))
                          for m in _re.finditer(r"\{([^{}|]*)\|([^{}]*)\}", text_))
    return _FakeClip(shown_, spoken, 0.25 + n * 0.158 / speed)


VOICE_PAUSES = (0.10, 0.22)
NUM_BREATH = 0.35                                    # 数字を言った文のあとは +0.35秒
CH_BREATH = 0.35


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and not it.id.startswith("c0_") and any(ch.isdigit() for ch in split_reading(it.text)[0]):          # 冒頭（0章）は数字のあとの間を足さない
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# 字幕の折り返しを指定する文（自動だと語の途中で折れるもの。--wraps で見て足す）
_SUB_BREAK = {
    "2千人で、2万5千人に挑んだ桶狭間。記録どおりに、もう一度戦ったら、勝てるのは、1万回のうち、ほんの数百回です。":
        ["2千人で、2万5千人に挑んだ桶狭間。記録どおりに、", "もう一度戦ったら、勝てるのは、1万回のうち、ほんの数百回です。"],
    "分かったことです。この戦いの勝ちは、全軍を倒すことではなく、今川の本陣を、戦えなくすることでした。":
        ["分かったことです。この戦いの勝ちは、全軍を倒すことではなく、", "今川の本陣を、戦えなくすることでした。"],
    "今川の本陣が、狭い谷で休んでいたところを、織田が攻めた、という話です。":
        ["今川の本陣が、狭い谷で休んでいたところを、", "織田が攻めた、という話です。"],
}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)


# ============================================================
# 小さな道具（densha-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"
BLUE_L = "#6a93cf"
GREEN = "#3f9a6a"
ORANGE = "#e0892a"
FLAG_O, FLAG_I = "#3a73c8", "#d8434e"                # 織田＝青系・今川＝赤系（合戦ロングと同じ色）


def lerp(a, b, u):
    return a + (b - a) * u


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


def prog(t, t0, s, cps=9.0):
    return clamp01((t - t0) / lf.write_dur(s, cps))


def wr(ctx, s, x, y, size, color, t0, t, cps=9.0, align="left", alpha=1.0, bold=True):
    if alpha <= 0.003 or t < t0:
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


def tag(ctx, s, x, y, size, col, a=1.0, progress=1.0, align="center"):
    """白い下地つきの札"""
    if a <= 0.003 or progress <= 0:
        return
    w = text_width(s, size) + 26
    cx = x + w / 2 - 13 if align == "left" else x
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, cx - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, cx, y, size, col, progress, align="center", alpha=a)


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """余白の小さい付箋。(x, y) は中心（align='left' なら左端）"""
    if a <= 0.003:
        return 0, 0
    lines = s.split("\n")
    w = max(text_width(l, size) for l in lines) + 44
    h = size * 1.25 * len(lines) + 24
    cx = x + w / 2 if align == "left" else x
    bg = STICKY.get(color, color)
    ctx.save()
    ctx.translate(cx, y)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, -w / 2 + 5, -h / 2 + 7, w, h, 5)
    ctx.fill()
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, -w / 2, -h / 2, w, h, 5)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(-w / 2, -h / 2, w, 10)
    ctx.fill()
    text(ctx, s, 0, 3, size, fg, alpha=a)
    ctx.restore()
    return w, h


def nolog(fn, *args, **kw):
    """飾りの字（重なりの検査に入れない）"""
    saved = core._LOG
    core._LOG = None
    try:
        return fn(*args, **kw)
    finally:
        core._LOG = saved


# ============================================================
# 準備（データ・時間割）
# ============================================================
lf.use()
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ---- 場面の合図: 文の一部（手がかり）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    "c0_a": (0, "2千人で、2万5千人に挑んだ桶狭間"), "c0_b": (0, "1560年"), "c0_c": (0, "1万回、戦い直します"), "c0_d": (0, "条件をひとつずつ足して"),
    "c0_e": (0, "兵の数は、資料によって"), "c0_f": (0, "ここでは、今川を2万5千人"),
    "c1_0": (1, "この章では、野原で"), "c1_first": (1, "先に言います"), "c1_bow": (1, "弓だけで戦う"), "c1_25": (1, "25本に1本"), "c1_win": (1, "相手を全滅させたら"),
    "c1_res": (1, "織田が勝ったのは"), "c1_2x": (1, "兵の数が2倍なら"), "c1_2xb": (1, "矢の数が2倍"),
    "c1_125": (1, "12.5倍"), "c1_156": (1, "その2乗"), "c1_end": (1, "分かったことです"),
    "c2_0": (2, "では、実際"), "c2_split": (2, "何か所にも"), 
    "c2_hon": (2, "大将の今川義元"), "c2_5k": (2, "5千人ほど"), "c2_res": (2, "まだ、ゼロです"),
    "c2_end": (2, "分かったことです"),
    "c3_last": (3, "最後の1人"), "c3_nobu": (3, "信長公記"), "c3_intro": (3, "この章では、ここまでの条件に足して"),
    "c3_rule": (3, "ここからは、本陣が崩れたら"), 
    "c3_r": (3, "1割から5割"), "c3_oda": (3, "最後まで戦う"), "c3_res": (3, "34回"), "c3_zero": (3, "初めて、ゼロ"),
    "c3_see": (3, "勝った回を見てみます"), "c3_this": (3, "この回は"), "c3_usual": (3, "崩れない相手なら"), 
    "c3_end": (3, "分かったことです"),
    "c4_rain": (4, "突然の激しい雨"), "c4_face": (4, "顔に打ちつけた"), "c4_stop": (4, "雨がやむと"),
    "c4_intro": (4, "この章では、ここまでの条件に、雨を足します"), "c4_s": (4, "0回から3回"), "c4_res": (4, "1万回中、627回"),
    "c4_three": (4, "3回先に放てた"), "c4_end": (4, "分かったことです"),
    "c5_1": (5, "条件のまま、諸説"), "c5_h6": (5, "6千人にすると"), "c5_h4": (5, "4千人にすると"),
    "c5_o3": (5, "3千人にすると"), "c5_r2": (5, "2割を失うまでは"), "c5_band": (5, "ゼロから5回に2回"), "c5_end": (5, "分かったことです"),
    "c6_all": (6, "同じ崩れ方で"), "c6_1": (6, "この章では、全部"), "c6_700": (6, "700人足らず"),
    "c6_res": (6, "全部に勝てた回"), "c6_tot": (6, "少なく見て"), "c6_real": (6, "まわりの城"), "c6_end": (6, "分かったことです"),
    "c7_0": (7, "もうひとつの話"), "c7_valley": (7, "狭い谷で休んで"), "c7_edo": (7, "江戸時代の本"), "c7_rec": (7, "おけはざま山"),
    "c7_1": (7, "この章では、江戸時代"), "c7_w": (7, "50人から200人"),
    "c7_res": (7, "7,272回"), "c7_why": (7, "数の差が効かず"), "c7_r3": (7, "3割を失うまでは"),
    "c7_edo2": (7, "江戸時代に語られた桶狭間なら"), "c7_rec2": (7, "記録に近い桶狭間なら"), "c7_end": (7, "分かったことです"),
    "c8_1": (8, "野原で挑めば"), "c8_2": (8, "本陣だけを相手にし"), "c8_4": (8, "多くの場合"),
    "c8_5": (8, "歴史の桶狭間"), "c8_q": (8, "あなたなら"), "c8_ch": (8, "このチャンネルでは"), "c8_sub": (8, "よければ"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_v1.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


def Mk(k, f=0.5):
    return mid(ID[k], f)


# ============================================================
# 絵: 足軽・のぼり・矢（合戦ロング sims/kassen-long.py からコピー。織田＝左・青系で右向き、今川＝右・赤系で左向き）
#   1体 ＝ 250人（2千＝8体・本陣5千＝20体・今川2万5千＝100体。どの人数も250で割り切れる）
#   武将は顔や肖像を描かない。のぼり旗と、小さな丘の上の白い陣幕（赤い2本線）だけで表す。血は描かない（倒れる兵は灰色になって寝る）
# ============================================================
FIG = 250                                            # 丘・谷の場面（本陣5千＝20体）
FIG_F = 500                                          # 野原の場面（今川全軍2万5千＝50体・織田2千＝4体）。足軽を大きく描くため
PEOPLE_LOG = []                                      # (場面の種類, x, y, 大きさ k, 倒れたか, 隊)。照合用（scan のときだけ溜める）
PEOPLE_ON = [False]


def figs(n, fig=None):
    """人数 → 絵の足軽の数（丘・谷は1体＝250人、野原は1体＝500人）"""
    return -(-int(n) // (fig or FIG))


TEAM = {"O": dict(flag=FLAG_O, armor="#bad3f3", sleeve="#92b4e4"),
        "I": dict(flag=FLAG_I, armor="#f6b9b3", sleeve="#e79a94")}

SKIN = "#fff0d8"
HAT = "#d6c19a"
LEGC = "#dcd1ba"
WOOD = "#9a6a38"
GRAY = "#b9b9b9"

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
# 戦場（kassen-long の Geo・Battle をコピー。隊に turn（向きを変える時刻）・lower（旗を下げる時刻）を足した）
# ============================================================
class Geo:
    """兵の並びの寸法。s は足軽の大きさの倍率"""

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


WX0, WX1 = 62.0, 928.0                               # 草地の左右（世界座標）
VIEW_ID = (1.0, 1.0, 0.0, 0.0)                       # 世界 ＝ 画面


def view_lerp(v0, v1, u):
    return tuple(lerp(a, b, u) for a, b in zip(v0, v1))


class Battle:
    """兵の並びと、一斉射撃の記録（誰が誰を狙って、当たったか）から、各時刻の絵を作る。
    groups: {名前: dict(side, n, cols, rows, xf, poles, march=(t0, t1, dx) or None, clear=時刻 or None)}
            clear: その時刻から、この組の倒れた兵を薄くして片づける（次の組が来る前に）
    fights: [dict(ga, gb, vols, times, flight=(a, b), roll, arc, dust, glow=("I",))]  vols は make_vols の記録
    view  : view(t) -> (Zx, Zy, ox, oy)。世界座標 (x, y) → 画面 (ox + Zx x, oy + Zy y)。兵の大きさは k × Zx"""

    def __init__(self, groups, fights, geo, view, seed=1):
        rng = np.random.default_rng(seed)
        self.groups = groups
        self.geo = geo
        self.view = view
        self.tag = "main"
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
            face = 1 if c["side"] == "O" else -1
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

    def fc(self, u, t):
        """兵 u の向き（隊に turn=時刻 があれば、その時刻から後ろ向き＝退く向きに変わる）"""
        c = self.groups[self.gnames[self.gid[u]]]
        tt = c.get("turn")
        f = int(self.face[u])
        return -f if (tt is not None and t >= tt) else f

    def n_arrows(self, t):
        i1 = bisect_right(self.rel, t)
        return int(np.count_nonzero(self.arr[:i1] >= t - 0.75))

    def shift(self, g, t):
        m = self.groups[g].get("march")
        if not m:
            return 0.0
        t0, t1, dx = m
        return dx * ease_in_out((t - t0) / (t1 - t0))

    def pos(self, u, t):
        td = getattr(self, "td", None)                    # 倒れた兵は、倒れた場所に残る（隊が退いても一緒に動かない）
        tt = t if td is None else min(t, td[u])
        return self.x0[u] + self.shift(self.gnames[self.gid[u]], tt), self.gy[u]

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
        face = 1 if c["side"] == "O" else -1
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
                if PEOPLE_ON[0]:
                    PEOPLE_LOG.append((self.tag, X, Y, self.k[u] * Zx, bool(dead), self.team[u]))
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
                    draw_soldier(ctx, X, Y, k, team, 0.0, self.fc(u, t), f, al, t)
                else:
                    sway = 0.012 * math.sin(t * 2.2 + self.sway_ph[u])
                    draw_soldier(ctx, X, Y, k, team, self.draw_amount(u, t), self.fc(u, t), 0.0, 1.0,
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
        face = 1 if c["side"] == "O" else -1
        if c.get("hide_dead_poles") and self.alive(g, t) == 0 and t > self.last_death(g) + 0.5:
            return                                     # 全滅した隊の旗は片づける（7章）
        xr0 = c["xf"] - face * (c["cols"] - 1) * geo.col_sp - face * 26 * geo.s + self.shift(g, t)
        for j, row in enumerate(c["poles"]):
            gyw = geo.gy(row)
            xw = xr0 + face * (j % 2) * 30 * geo.s
            xr, gy = ox + Zx * xw, oy + Zy * gyw
            if xr > 990:
                continue
            lw = c.get("lower")                             # 旗を下げる（本陣が崩れた）: さおの根元を軸に、後ろ（退く向き）へ倒れる
            ang = 0.0 if not lw else ease_out(clamp01((t - lw[0]) / (lw[1] - lw[0]))) * 1.3
            ctx.save()
            if ang > 0:
                ctx.translate(xr, gy)
                ctx.rotate(-face * ang)
                ctx.translate(-xr, -gy)
            nobori(ctx, xr, gy, geo.persp(gyw), ze, c["side"], t, j * 1.7 + (0.5 if c["side"] == "I" else 0.0))
            ctx.restore()
            if PEOPLE_ON[0] and c["side"] == "I":
                PEOPLE_LOG.append((self.tag, xr, gy, ang, False, "pole"))

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
                ctx.set_source_rgba(*hexrgb(MARKER, 0.95 * k))
                ctx.set_line_width(2.6 * ze)
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                for j in range(5):
                    ang = -math.pi / 2 + (j - 2) * 0.62
                    ctx.move_to(x + math.cos(ang) * (8 + 8 * age / 0.3) * ze, y - 26 * ze + math.sin(ang) * (8 + 8 * age / 0.3) * ze)
                    ctx.line_to(x + math.cos(ang) * (16 + 12 * age / 0.3) * ze, y - 26 * ze + math.sin(ang) * (16 + 12 * age / 0.3) * ze)
                ctx.stroke()

def make_vols(path, alive_a, alive_b, rng, quiet_b=0, fig=None):
    """人数の軌跡（[[織田, 今川], …]。最初の行を含む）から、絵の一斉射撃の記録を作る。
    1体＝250人なので、体数（ceil(人数÷250)）が減ったぶんだけ、その回にでたらめに選んだ兵が倒れる。
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
        da = min(len(alive_a), max(0, figs(path[i - 1][0], fig) - figs(path[i][0], fig)))
        db = min(len(alive_b), max(0, figs(path[i - 1][1], fig) - figs(path[i][1], fig)))
        dead_b = [int(x) for x in rng.choice(alive_b, db, replace=False)] if db else []
        dead_a = [int(x) for x in rng.choice(alive_a, da, replace=False)] if da else []
        vols.append((shots(alive_a, alive_b, dead_b) if alive_a else [], shots(alive_b, alive_a, dead_a) if (alive_b and i > quiet_b) else []))
        alive_a = [u for u in alive_a if u not in dead_a]
        alive_b = [u for u in alive_b if u not in dead_b]
    return vols, alive_a, alive_b


def path_index(land_times, t):
    """着弾の時刻の並びから、t までに終わった一斉射撃の回数（＝人数の軌跡の行番号）"""
    return bisect_right(land_times, t)
_SPR = {}


def sprite_soldier(team, fallen, k=0.17):
    """小さな合戦用の足軽（1枚描いて使い回す）"""
    key = (team, fallen, k)
    s = _SPR.get(key)
    if s is None:
        w, h = int(60 * k * 2.2) + 8, int(130 * k) + 8
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(s)
        draw_soldier(c, w / 2, h - 3, k, team, 0.0, 1 if team == "O" else -1, 1.0 if fallen else 0.0,
                     0.6 if fallen else 1.0, 0.3, shadow=False)
        _SPR[key] = s
    return s


# ============================================================
# 場面のデータ（数字はすべて data.json。見本の軌跡は data.json の samples）
# ============================================================
LAD = {st["id"]: st for st in RES["ladder"]}
L5 = {st["id"]: st for st in RES["l5"]}
L6 = {st["id"]: st for st in RES["l6"]}
L7 = {st["id"]: st for st in RES["l7"]}
SMP = RES["samples"]
PR = RES["params"]
N_ODA, N_HON, N_ALL = PR["ODA"], PR["HONJIN"], PR["TOTAL"]


def pct_txt(rate):
    """画面の勝率の書き方: 0 →「0%」・1%未満 →「0.3%」（小数1桁）・それ以上 → 四捨五入の整数%"""
    if rate <= 0:
        return "0%"
    p = rate * 100
    if p < 1:
        return f"{p:.1f}%"
    return f"{ihalf(p)}%"


# ---- 戦場の並び（左ページ 45〜940）----
GEO_L = Geo(s=1.9, col_sp=50.0, row_y0=460.0, row_dy=70.0, depth=5)        # ch0・1: 織田4体 vs 今川50体（1体＝500人。足軽を大きく）
GEO_M = Geo(s=1.7, col_sp=52.0, row_y0=420.0, row_dy=52.0, depth=10)       # ch2〜: 織田8体 vs 本陣20体（足軽を大きく）
GEO_V = Geo(s=2.1, col_sp=50.0, row_y0=560.0, row_dy=52.0, depth=10)       # ch7: 谷（2列）
XO_F, XI_F = 330.0, 500.0


def reduce_path(path, n_rows):
    """人数の軌跡を、n_rows 行以内に間引く（最初と最後は残す）"""
    if len(path) <= n_rows:
        return [list(p) for p in path]
    idx = sorted(set(int(round(i)) for i in np.linspace(0, len(path) - 1, n_rows)))
    return [list(path[i]) for i in idx]


def groups_for(kind, n_hon=20):
    if kind == "field":
        return ({"O": dict(side="O", n=N_ODA // FIG_F, cols=2, rows=[2, 3], xf=250.0, poles=[2.5]),
                 "I": dict(side="I", n=N_ALL // FIG_F, cols=10, rows=list(range(5)), xf=430.0, poles=[1.5, 3.0])}, GEO_L)
    if kind == "hill":
        return ({"O": dict(side="O", n=N_ODA // FIG, cols=2, rows=[2, 3, 4, 5], xf=330.0, poles=[3.5]),
                 "I": dict(side="I", n=n_hon, cols=-(-n_hon // 4), rows=[2, 3, 4, 5], xf=520.0, poles=[2.0, 4.5])}, GEO_M)
    if kind == "valley":
        return ({"O": dict(side="O", n=N_ODA // FIG, cols=4, rows=[0, 1], xf=300.0, poles=[0.5]),
                 "I": dict(side="I", n=N_HON // FIG, cols=10, rows=[0, 1], xf=400.0, poles=[0.5])}, GEO_V)
    raise ValueError(kind)


class Sc:
    """1つの戦場の場面。kind: field（野原・今川全軍）/ hill（丘の上の本陣）/ valley（谷）。
    path: 人数の軌跡 [[織田, 今川], …]。times: 一斉射撃を始める時刻。quiet: 今川が撃ち返さない回数（雨）。
    rout: 本陣が崩れる時刻（旗が下がり、向きを変えて、右へ退く）"""

    def __init__(self, kind, path=None, times=None, quiet=0, rout=None, roll=0.5, seed=1, n_hon=20, tag="main",
                 n_vol=None, rout_dx=620.0, first_at=None, spacing=None, arc=0.07, march_dur=3.0):
        groups, geo = groups_for(kind, n_hon)
        self.kind, self.geo, self.tag = kind, geo, tag
        self.fig = FIG_F if kind == "field" else FIG
        fights, self.path = [], None
        if path is not None:
            p = path if n_vol is None else reduce_path(path, n_vol + 1)
            self.path = p
            rng = np.random.default_rng(seed)
            vols, self.alive_o, self.alive_i = make_vols(p, range(groups["O"]["n"]), range(groups["I"]["n"]), rng, quiet_b=quiet, fig=self.fig)
            if times is None:
                times = [first_at + spacing * i for i in range(len(vols))]
            self.times = list(times)
            fights = [dict(ga="O", gb="I", vols=vols, times=self.times, flight=(0.40, 0.42), roll=roll, arc=arc, dust=0.06)]
        self.rout = rout
        if rout is not None:
            groups["I"]["lower"] = (rout, rout + 0.9)
            groups["I"]["turn"] = rout + 0.9                      # 旗が下がりきってから、向きを変えて歩き出す
            groups["I"]["march"] = (rout + 0.9, rout + 0.9 + march_dur, rout_dx)
        self.groups = groups
        self.battle = Battle(groups, fights, geo, lambda t: VIEW_ID, seed=seed)
        self.battle.tag = tag
        self.t_end = max(self.battle.last_death("O"), self.battle.last_death("I")) if fights else 0.0
        self.land = sorted(self.battle.volley_land)
        self.dur = (rout + 0.9 + march_dur + 0.1) if rout is not None else ((self.t_end + 0.4) if fights else 3.0)     # 1回ぶんの見せる長さ（早回しの繰り返し用）

    def row_at(self, t):
        """いま（t）までに着弾した一斉射撃の回数 ＝ 人数の軌跡の行"""
        return min(bisect_right(self.land, t), len(self.path) - 1) if self.path else 0


# ---- 背景（世界座標）----
def draw_curtain(ctx, a=1.0):
    """小さな丘の上の白い陣幕（赤い2本線）。武将は描かない（旗と陣幕だけで本陣を表す）"""
    x0, x1, yt, yb = 808.0, 925.0, 416.0, 492.0
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(5)
    for xx in (x0, x1):
        ctx.move_to(xx, yt - 10)
        ctx.line_to(xx, yb + 6)
    ctx.stroke()
    ctx.move_to(x0, yt)
    ctx.line_to(x1, yt)
    n = 5
    for i in range(n):
        xa = x1 - (x1 - x0) * i / n
        xb = x1 - (x1 - x0) * (i + 1) / n
        ctx.line_to(xa, yb)
        ctx.curve_to(xa, yb + 10, xb, yb + 10, xb, yb)
    ctx.line_to(x0, yt)
    ctx.close_path()
    ctx.set_source_rgba(1, 0.99, 0.96, a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.set_line_width(8)
    for yy in (yt + 24, yt + 46):
        ctx.move_to(x0 + 4, yy)
        ctx.line_to(x1 - 4, yy)
    ctx.stroke()
    ctx.restore()


def draw_hill(ctx):
    pts = [(430, 760), (452, 650), (500, 568), (580, 520), (680, 497), (800, 488), (930, 492), (944, 500), (944, 760)]
    ctx.move_to(*pts[0])
    for (x, y) in pts[1:]:
        ctx.line_to(x, y)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#cfe0a6", 0.95))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.5))
    ctx.set_line_width(3)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    rng = np.random.default_rng(21)
    ctx.set_source_rgba(*hexrgb("#6f8f4a", 0.55))
    ctx.set_line_width(2.4)
    for _ in range(26):
        x = float(rng.uniform(520, 930))
        y = float(rng.uniform(530, 745))
        for dx, h in ((-5, 8), (0, 11), (5, 8)):
            ctx.move_to(x + dx * 0.4, y)
            ctx.line_to(x + dx, y - h)
    ctx.stroke()


def draw_valley(ctx):
    rng = np.random.default_rng(12)
    xs = np.linspace(40, 950, 34)
    ctx.set_source_rgba(*hexrgb("#e6d9b8", 0.9))             # 谷の道
    ctx.rectangle(40, 440, 910, 252)
    ctx.fill()
    for (ya, yb, sgn) in ((250, 446, 1), (880, 692, -1)):
        pts = [(x, yb + sgn * float(rng.uniform(-8, 8)) + sgn * 20 * math.sin(x / 90)) for x in xs]
        ctx.move_to(40, ya)
        for p in pts:
            ctx.line_to(*p)
        ctx.line_to(950, ya)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#b8ad9a", 0.92))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK, 0.35))
        ctx.set_line_width(2)
        for _ in range(30):
            x = float(rng.uniform(60, 930))
            y = float(rng.uniform(min(ya, yb) + 14, max(ya, yb) - 16))
            ctx.move_to(x, y)
            ctx.line_to(x + float(rng.uniform(-18, 18)), y + float(rng.uniform(8, 16)) * sgn)
        ctx.stroke()


def draw_bg(ctx, kind, curtain=True):
    if kind == "field":
        draw_field(ctx, 416.0, 780.0, GEO_L.s, WX0, WX1)
    elif kind == "hill":
        draw_field(ctx, 440.0, 790.0, 1.5, WX0, WX1)
        draw_hill(ctx)
        if curtain:
            draw_curtain(ctx)
    else:
        draw_valley(ctx)


def draw_sc(ctx, sc, t, a=1.0, view=None, shake=True, curtain=True):
    """場面を描く。view=(Zx, Zy, ox, oy) で世界を縮めて置ける（早回しの帯）"""
    if a <= 0.003:
        return
    view = view or VIEW_ID
    if a < 1:
        ctx.push_group()
    Zx, Zy, ox, oy = view
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(Zx, Zy)
    draw_bg(ctx, sc.kind, curtain)
    ctx.restore()
    sc.battle.draw(ctx, t, view=view, field=False, shake=shake and view == VIEW_ID)
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def fit_view(box, target):
    (bx0, by0, bx1, by1), (tx0, ty0, tx1, ty1) = box, target
    z = min((tx1 - tx0) / (bx1 - bx0), (ty1 - ty0) / (by1 - by0))
    ox = (tx0 + tx1) / 2 - z * (bx0 + bx1) / 2
    oy = (ty0 + ty1) / 2 - z * (by0 + by1) / 2
    return (z, z, ox, oy)


STRIP_T = (60, 595, 925, 920)
STRIP_VIEW = {"field": fit_view((100, 280, 940, 800), STRIP_T), "hill": fit_view((200, 270, 944, 770), STRIP_T),
              "valley": fit_view((120, 300, 944, 740), STRIP_T)}


# ---- 1万マス（1マス＝1回の合戦。織田の勝ち＝青・負け＝赤。勝った回数は data.json のとおり）----
GRID_N, GRID_C = 100, 4.4
GRID_PX = int(round(GRID_N * GRID_C))
GRID_X0, GRID_Y0 = LCX - GRID_PX / 2, 130.0
LOSS_C, WIN_C, EMPTY_C = "#eaaea6", "#2a63c8", "#e9e3d3"


class ResGrid:
    def __init__(self, wins, seed, n=10000):
        v = np.zeros(n, bool)
        v[:wins] = True
        self.win = np.random.default_rng(seed).permutation(v)
        self.wins, self.n = int(wins), n
        c, px = GRID_C, GRID_PX
        self.full = np.zeros((px, px, 4), np.uint8)
        self.idx = np.full((px, px), 10 ** 9, np.int64)
        self.win_xy = []
        lo, wi, em = hexrgb(LOSS_C), hexrgb(WIN_C), hexrgb(EMPTY_C)
        for i in range(n):
            r_, q_ = i // GRID_N, i % GRID_N
            y0, y1 = int(round(r_ * c)), int(round((r_ + 1) * c)) - 1
            x0, x1 = int(round(q_ * c)), int(round((q_ + 1) * c)) - 1
            col = wi if self.win[i] else lo
            self.full[y0:y1, x0:x1, 0] = int(col[2] * 255)
            self.full[y0:y1, x0:x1, 1] = int(col[1] * 255)
            self.full[y0:y1, x0:x1, 2] = int(col[0] * 255)
            self.full[y0:y1, x0:x1, 3] = 255
            self.idx[y0:y1, x0:x1] = i
            if self.win[i]:
                self.win_xy.append((i, GRID_X0 + (q_ + 0.5) * c, GRID_Y0 + (r_ + 0.5) * c))
        self.empty = np.zeros_like(self.full)
        m = self.full[..., 3] > 0
        self.empty[m] = (int(em[2] * 255), int(em[1] * 255), int(em[0] * 255), 255)
        self._buf = None

    def draw(self, ctx, n, a=1.0):
        mask = (self.idx < n)[..., None]
        self._buf = np.ascontiguousarray(np.where(mask, self.full, self.empty))
        s = cairo.ImageSurface.create_for_data(memoryview(self._buf), cairo.FORMAT_ARGB32, GRID_PX, GRID_PX, GRID_PX * 4)
        ctx.set_source_surface(s, GRID_X0, GRID_Y0)
        ctx.paint_with_alpha(a)
        if self.wins <= 200:                                    # まれな勝ちは、丸で囲んで見つけやすく
            ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
            ctx.set_line_width(2.2)
            for i, x, y in self.win_xy:
                if i < n:
                    ctx.new_sub_path()
                    ctx.arc(x, y, 7.5, 0, 2 * math.pi)
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(GRID_X0 - 4, GRID_Y0 - 4, GRID_PX + 6, GRID_PX + 6)
        ctx.stroke()


GRIDS = {k: ResGrid(LAD[k]["wins"], 30 + i) for i, k in enumerate(("L1", "L2", "L3", "L4", "L7"))}


def grid_n(t, t0, t1):
    return int(round(10000 * clamp01((t - t0) / (t1 - t0)) ** 1.7))


# ---- 見本の場面（時刻は台本の合図から）----
def sp_for(n_vol, total, lo=0.35, hi=0.9):
    return max(lo, min(hi, total / max(1, n_vol)))


# ch0: 冒頭。2千 vs 2万5千（見本 L1_loss）。0秒目にはもう矢が飛んでいて、左がみるみる減る。声は0.5秒から
_p0 = SMP["L1_loss"]["traj"]
_T_WIPE = Ek("c0_a") + 1.8                                           # 無音の始まりごろまでに、左が全滅する（織田は4体・0〜5秒のあいだに1体ずつ減る）
_ROLL0 = 2.6                                                       # 矢は一斉ではなく、1回ぶんを 2秒かけて次々に放つ（矢が途切れない）
_sp0 = (_T_WIPE + 0.7 - _ROLL0 - 0.5) / (len(_p0) - 2)
SC_OPEN = Sc("field", _p0, first_at=-0.7, spacing=_sp0, roll=_ROLL0, seed=3)
SC_FIELD = Sc("field", seed=4)                                    # 戦いの前の陣形（旗がゆれる）

# ch1: 「全員が一斉に矢を放ち、25本に1本が当たって、相手が1人倒れます」の見本（同じ見本 L1_loss を、ゆっくり）
_t10 = Sk("c1_25", 0.15)
SC_C1 = Sc("field", _p0, first_at=_t10, spacing=max(0.9, (Ek("c1_win") - _t10 - 1.6) / (len(_p0) - 2)), roll=0.9, seed=5)

# 早回しの帯（無音の区間）: 見本を速く繰り返す
STRIP = {}


def _mk_strip(kind, key_or_path, n_vol, quiet=0, seed=1, rout=False, n_hon=20):
    path = SMP[key_or_path]["traj"] if isinstance(key_or_path, str) else key_or_path
    n = len(path) - 1
    sp = sp_for(min(n, n_vol), 1.0, 0.2, 0.4)
    nv = min(n, n_vol)
    first = 0.2
    sc = Sc(kind, path, first_at=first, spacing=sp, quiet=quiet, roll=0.35, seed=seed, n_vol=nv, tag="strip", n_hon=n_hon)
    if rout and SMP[key_or_path]["result"] == "rout":
        sc = Sc(kind, path, first_at=first, spacing=sp, quiet=quiet, roll=0.35, seed=seed, n_vol=nv, tag="strip", n_hon=n_hon,
                rout=first + sp * (nv - 1) + 0.5, rout_dx=620.0, march_dur=1.0)
    return sc


STRIP["g1"] = [_mk_strip("field", "L1_loss", 4, seed=7)]
STRIP["g2"] = [_mk_strip("hill", "L2_loss", 6, seed=8)]
STRIP["g3"] = [_mk_strip("hill", "L3_loss", 6, seed=9)]
STRIP["g4"] = [_mk_strip("hill", "L4_loss", 6, quiet=SMP["L4_loss"]["s"], seed=10)]
STRIP["g7"] = [_mk_strip("valley", "L7_win", 4, seed=11, rout=True), _mk_strip("valley", "L7_loss", 4, seed=12),
               _mk_strip("valley", "L7-W50_win", 4, seed=13, rout=True), _mk_strip("valley", "L7-W200_win", 4, seed=14, rout=True)]
STRIP_ORDER = {"g1": [0], "g2": [0], "g3": [0], "g4": [0], "g7": [0, 1, 2, 3, 1]}      # 谷は勝ちの見本を多めに（1万回の7割ほどが勝ち）

# ch2: 本陣（8体 vs 20体）。戦いの前の陣形
SC_HILL = Sc("hill", seed=6)
# ch3: 「崩れる」の見せ方（旗が下がって右へ退く）。陣形のまま、台詞に合わせて崩れる
SC_CRUMBLE = Sc("hill", rout=Sk("c3_intro", 0.45), seed=6)
# ch3: 勝った1回（見本 L3_win）。旗が下がって退く
_pw = SMP["L3_win"]["traj"]
_T_W0 = Sk("c3_zero", 0.40)
_T_ROUT = Sk("c3_this", 0.40)
_nv = max(3, min(len(_pw) - 1, int((_T_ROUT - 1.5 - _T_W0) / 0.6) + 1))
SC_WIN = Sc("hill", _pw, first_at=_T_W0, spacing=(_T_ROUT - 1.5 - _T_W0) / max(1, _nv - 1), roll=0.5, seed=15, n_vol=_nv, rout=_T_ROUT, march_dur=5.5)       # 退く本陣は、旗を下げて右へゆっくり歩いて去る（しばらく絵に残る）
# ch4: 雨。織田だけが先に矢を放つ（見本 L4_win の最初の3回。今川は撃ち返さない回が2回）
_pr = SMP["L4_win"]["traj"][:4]
SC_RAIN = Sc("hill", _pr, first_at=Sk("c4_intro", 0.75), spacing=1.4, quiet=SMP["L4_win"]["s"], roll=0.6, seed=16)
# ch6: 本陣に勝ったあと（見本 L6_first_then_loss）。本陣は退き、次の今川5千が来る（見本の後ろの組の軌跡）
_p6a = SMP["L6_first_then_loss"]["traj"]
_p6b = SMP["L6_first_then_loss"]["later"][0]["traj"]


def _mk_ch6():
    groups, geo = groups_for("hill")
    rng = np.random.default_rng(17)
    t_r = Sk("c6_all", 0.25)
    nodes_a = reduce_path(_p6a, 10)
    v0, ao, ai = make_vols(nodes_a, range(8), range(20), rng, quiet_b=SMP["L6_first_then_loss"]["s"])
    t_in0, t_in1 = S("g6") - 2.0, S("g6") - 0.1
    groups["I"]["lower"] = (t_r, t_r + 0.9)
    groups["I"]["turn"] = t_r + 0.5
    groups["I"]["march"] = (t_r + 0.5, t_r + 3.5, 620.0)
    groups["G1"] = dict(side="I", n=20, cols=5, rows=[2, 3, 4, 5], xf=520.0 + 640.0, poles=[2.0, 4.5], march=(t_in0, t_in1, -640.0))
    nodes_b = reduce_path(_p6b, 4)
    v1, _ao, _ai = make_vols(nodes_b, ao, range(20), rng)
    t1 = [S("g6") + 0.6 + 0.6 * i for i in range(len(v1))]
    fights = [dict(ga="O", gb="I", vols=v0, times=[-60.0 + 1.0 * i for i in range(len(v0))], flight=(0.4, 0.42), roll=0.3, arc=0.07, dust=0.06),
              dict(ga="O", gb="G1", vols=v1, times=t1, flight=(0.40, 0.42), roll=0.6, arc=0.07, dust=0.06)]
    b = Battle(groups, fights, geo, lambda t: VIEW_ID, seed=18)
    return b, t1


SC6_BATTLE, SC6_T1 = _mk_ch6()

# ch7: 江戸時代の谷（見本 L7_win）
SC_VALLEY = Sc("valley", seed=19)


# ============================================================
# 左ページ（絵）。時刻つきの「層」を重ねる（出入りは 0.4秒のフェード）
# ============================================================
def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 910)
    ctx.clip()


def legend_fig(ctx, a=1.0, x=108, y=896, n=250):
    """絵の足軽1人＝250人（野原の場面は500人）（左ページの左下）"""
    if a <= 0.003:
        return
    s = sprite_soldier("O", False, 0.5)
    ctx.set_source_surface(s, x - s.get_width() / 2, y + 26 - s.get_height())
    ctx.paint_with_alpha(a)
    text(ctx, f"絵の足軽1人＝{n}人", x + 44, y - 4, 40, INK, align="left", alpha=a)


def labels_sc(ctx, kind, a, honjin=False):
    if a <= 0.003:
        return
    if kind == "field":
        tag(ctx, "織田", 235, 300, 52, FLAG_O, a)
        tag(ctx, "今川", 646, 300, 52, FLAG_I, a)
    elif kind == "hill":
        tag(ctx, "織田", 304, 235, 52, FLAG_O, a)
        tag(ctx, "今川の本陣", 640, 235, 52, FLAG_I, a)
    else:
        tag(ctx, "織田", 270, 330, 52, FLAG_O, a)
        tag(ctx, "今川の本陣", 700, 330, 52, FLAG_I, a)


def L_title(ctx, t, a=1.0):
    """0秒目から題字「桶狭間」（左上）"""
    text(ctx, "桶狭間", 85, 168, 140, INK, align="left", alpha=a)
    pen_line(ctx, 80, 252, 85 + text_width("桶狭間", 140) + 10, 246, RED, seed=3, width=9, progress=clamp01(t / 0.6), alpha=a)


def arrow_glyph(ctx, x, y, ln, col=INK, a=1.0, w=4.0):
    """右向きの矢（図の説明用）"""
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y)
    ctx.line_to(x + ln, y)
    ctx.stroke()
    ctx.move_to(x + ln, y)
    ctx.line_to(x + ln - 12, y - 8)
    ctx.line_to(x + ln - 12, y + 8)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(x, y)
    ctx.line_to(x - 9, y - 7)
    ctx.move_to(x, y)
    ctx.line_to(x - 9, y + 7)
    ctx.stroke()


def rain_draw(ctx, t, a, x0=45, x1=940, y0=200, y1=830):
    """雨の線。今川（右）の顔に向かって斜めに降る（左上から右下へ）"""
    if a <= 0.003:
        return
    rng = np.random.default_rng(31)
    n = 170
    xs = rng.uniform(x0 - 120, x1, n)
    ph = rng.uniform(0, 1, n)
    sp = rng.uniform(1.6, 2.4, n)
    heavy = (xs > 520) | (np.arange(n) % 3 == 0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(2.8)
    H_ = y1 - y0
    for i in range(n):
        if not heavy[i] and i % 2:
            continue
        u = (ph[i] + sp[i] * t * 0.6) % 1.0
        yy = y0 + u * H_
        xx = xs[i] + 0.42 * (yy - y0)
        if xx > x1 or xx < x0:
            continue
        ctx.set_source_rgba(*hexrgb("#6a8fc0", 0.6 * a))
        ctx.move_to(xx, yy)
        ctx.line_to(xx + 12, yy + 30)
        ctx.stroke()


# ---- ch0〜1: 戦いの絵 ----
def L_open0(ctx, t):
    draw_sc(ctx, SC_OPEN, t)
    labels_sc(ctx, "field", 1.0)                       # 0秒目から「織田」「今川」の札（どちらが全滅するか、最初から分かるように）
    legend_fig(ctx, fade(t, Sk("c0_b", 0.5), 0.4), n=FIG_F)


def L_field_c1(ctx, t):
    draw_sc(ctx, SC_C1, t)
    labels_sc(ctx, "field", 1.0)
    legend_fig(ctx, 1.0, n=FIG_F)


# ---- マス目＋早回しの帯 ----
def draw_strip(ctx, gid, t, a):
    if a <= 0.003:
        return
    t0 = S(gid) + 0.1
    seq = [STRIP[gid][i] for i in STRIP_ORDER[gid]]
    tot = sum(sc_.dur + 0.3 for sc_ in seq)
    tau = max(0.0, t - t0) % tot
    for sc in seq:
        if tau < sc.dur + 0.3:
            break
        tau -= sc.dur + 0.3
    ctx.save()
    ctx.rectangle(*STRIP_T[:2], STRIP_T[2] - STRIP_T[0], STRIP_T[3] - STRIP_T[1])
    ctx.clip()
    ctx.set_source_rgba(1, 1, 1, 0.45 * a)
    ctx.paint()
    draw_sc(ctx, sc, max(tau, 0.0), a, view=STRIP_VIEW[sc.kind], shake=False)
    ctx.restore()
    text(ctx, "▶▶ 早回し", STRIP_T[0] + 14, STRIP_T[1] + 24, 36, PENCIL_T, align="left", alpha=a)


def legend_sq(ctx, items, cx, y, size=36, gap=40, a=1.0):
    ws = [46 + text_width(lab, size, bold=False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.fill()
        text(ctx, lab, x + 42, y, size, INK, align="left", bold=False, alpha=a)
        x += w + gap


GRID_CAP = "青＝織田の勝ち　1マス＝1回"


def mk_grid_layer(gid, gkey):
    def fn(ctx, t):
        t0, t1 = S(gid) + 0.5, E(gid) - 0.4
        GRIDS[gkey].draw(ctx, grid_n(t, t0, t1))
        draw_strip(ctx, gid, t, out_fade(t, E(gid) - 0.05, 0.4))
        text(ctx, GRID_CAP, LCX, 86, 46, INK, alpha=fade(t, S(gid) + 0.1, 0.4))             # マス目の読み方を、グリッドの真上に大きく1行
        q = fade(t, E(gid) + 0.1, 0.4)
        if q > 0.003:
            text(ctx, f"1万回のうち {LAD[gkey]['wins']:,}回", LCX, 670, 66, RED if LAD[gkey]["wins"] else INK, alpha=q)
    return fn


# ---- ch1: 2倍→4倍の図 ----
def L_diag2x(ctx, t):
    t1, d1 = Sk("c1_2x"), Dk("c1_2x")
    t2, d2 = Sk("c1_2xb"), Dk("c1_2xb")
    ks = 0.5
    # ① 兵の数 2倍
    a1 = fade(t, t1 + 0.1, 0.4)
    if a1 > 0.003:
        text(ctx, "兵の数 2倍", LCX, 140, 48, INK, alpha=a1)
        for i in range(2):
            s_ = sprite_soldier("O", False, ks)
            ctx.set_source_surface(s_, 190 + 62 * i - s_.get_width() / 2, 250 - s_.get_height() + 6)
            ctx.paint_with_alpha(a1)
        arrow_glyph(ctx, 345, 218, 100, RED, a1, 6)
        for i in range(4):
            s_ = sprite_soldier("O", False, ks)
            ctx.set_source_surface(s_, 560 + 62 * i - s_.get_width() / 2, 250 - s_.get_height() + 6)
            ctx.paint_with_alpha(a1)
    # ② 矢の数 2倍
    a2 = fade(t, t2 + 0.1, 0.4)
    if a2 > 0.003:
        text(ctx, "矢の数 2倍", LCX, 330, 48, INK, alpha=a2)
        for i in range(2):
            arrow_glyph(ctx, 150, 385 + 34 * i, 100, INK, a2)
        arrow_glyph(ctx, 345, 402, 100, RED, a2, 6)
        for i in range(4):
            arrow_glyph(ctx, 560, 372 + 26 * i, 100, INK, a2)
    # ③ 相手の矢は2倍の人数に散らばる
    a3 = fade(t, t2 + 0.5 * d2, 0.4)
    if a3 > 0.003:
        text(ctx, "相手の矢は 2倍の人数に散らばる", LCX, 500, 42, INK, alpha=a3)
        for j, (n_t, lab) in enumerate(((2, "1人に 2本"), (4, "1人に 1本"))):
            x0 = 140 + 430 * j
            for i in range(4):
                arrow_glyph(ctx, x0 - 70, 548 + 28 * i, 62, FLAG_I, a3, 3.6)
            for i in range(n_t):
                s_ = sprite_soldier("O", False, ks)
                xx = x0 + 70 + 62 * i if n_t == 2 else x0 + 52 + 48 * i
                ctx.set_source_surface(s_, xx - s_.get_width() / 2, 660 - s_.get_height() + 6)
                ctx.paint_with_alpha(a3)
            text(ctx, lab, x0 + 100, 700, 38, INK, alpha=a3)
    # ④ 強さ 4倍
    a4 = fade(t, Ek("c1_2x") - 0.6, 0.5)
    if a4 > 0.003:
        sticky(ctx, "強さ 4倍", LCX, 820, 72, "pink", fg=RED, a=a4, tilt=-0.02)


# ---- ch2: 今川は分かれていた（手書きの配置図。地名は出さない）----
def draw_cluster(ctx, cx, cy, n, team, k=0.46, cols=4, px=46.0, py=40.0, a=1.0):
    rows = -(-n // cols)
    s_ = sprite_soldier(team, False, k)
    for i in range(n):
        r_, c_ = divmod(i, cols)
        x = cx + (c_ - (cols - 1) / 2) * px
        y = cy + (r_ - (rows - 1) / 2) * py
        ctx.set_source_surface(s_, x - s_.get_width() / 2, y + 22 - s_.get_height())
        ctx.paint_with_alpha(a)


def draw_fort(ctx, x, y, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgba(*hexrgb("#d9c7a0", a))
    ctx.rectangle(-60, -34, 120, 68)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3.5)
    ctx.stroke()
    for i in range(4):
        ctx.rectangle(-60 + i * 33, -52, 21, 20)
        ctx.set_source_rgba(*hexrgb("#d9c7a0", a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.stroke()
    ctx.restore()


def draw_castle(ctx, x, y, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    for (w, h, yy) in ((110, 42, 28), (80, 34, -12), (52, 28, -46)):
        ctx.rectangle(-w / 2, yy - h / 2, w, h)
        ctx.set_source_rgba(*hexrgb("#f3efe4", a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(3.5)
        ctx.stroke()
        ctx.move_to(-w / 2 - 12, yy - h / 2)
        ctx.line_to(0, yy - h / 2 - 20)
        ctx.line_to(w / 2 + 12, yy - h / 2)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#6b7285", a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.stroke()
    ctx.restore()


def L_map(ctx, t):
    tA, dA = Sk("c2_split"), Dk("c2_split")
    tE, dE = Sk("c2_split", 0.3), Dk("c2_split") * 0.6                  # 名札は「何か所にも分かれていました」の文のうちに順に書く
    tH = Sk("c2_hon")
    a = fade(t, tA, 0.3)
    f1 = fade(t, tA + 0.15 * dA, 0.4)
    f2 = fade(t, tA + 0.35 * dA, 0.4)
    f3 = fade(t, tA + 0.55 * dA, 0.4)
    f4 = fade(t, tA + 0.75 * dA, 0.4)
    # 砦と、砦を攻める兵（左上）
    if f1 > 0.003:
        draw_fort(ctx, 175, 255, f1)
        draw_cluster(ctx, 340, 270, 8, "I", a=f1)
    # 城と、城を守る兵（右上）
    if f2 > 0.003:
        draw_castle(ctx, 700, 235, f2)
        draw_cluster(ctx, 840, 275, 6, "I", cols=3, a=f2)
    # 後ろに控える兵（右下）
    if f3 > 0.003:
        draw_cluster(ctx, 765, 690, 10, "I", cols=5, a=f3)
    # 本陣（中央。小さな丘・陣幕・のぼり旗）
    if f4 > 0.003:
        ctx.save()
        ctx.translate(0, 0)
        ctx.push_group()
        ctx.move_to(250, 700)
        ctx.curve_to(300, 560, 400, 520, 470, 520)
        ctx.curve_to(560, 520, 640, 570, 690, 700)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#cfe0a6", 0.95))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.6))
        ctx.set_line_width(3)
        ctx.stroke()
        # 陣幕
        ctx.save()
        ctx.translate(470 - 808 + 70, 0)
        ctx.scale(1, 1)
        ctx.restore()
        x0, x1, yt, yb = 410, 530, 452, 520
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(4)
        for xx in (x0, x1):
            ctx.move_to(xx, yt - 8)
            ctx.line_to(xx, yb + 4)
        ctx.stroke()
        ctx.rectangle(x0, yt, x1 - x0, yb - yt)
        ctx.set_source_rgba(1, 0.99, 0.96, 1)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(RED, 0.95))
        ctx.set_line_width(7)
        for yy in (yt + 22, yt + 42):
            ctx.move_to(x0 + 3, yy)
            ctx.line_to(x1 - 3, yy)
        ctx.stroke()
        # のぼり旗
        for xx, ph in ((350, 0.0), (590, 1.3)):
            nobori(ctx, xx, 560, 0.9, 0.62, "I", t, ph)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(f4)
        draw_cluster(ctx, 470, 625, 10, "I", cols=5, k=0.46, px=52, py=38, a=f4)
        ctx.restore()
    # 織田（左下）
    f5 = fade(t, tH + 0.2, 0.4)
    if f5 > 0.003:
        draw_cluster(ctx, 160, 700, 6, "O", cols=3, a=f5)
        text(ctx, "織田", 160, 790, 48, FLAG_O, alpha=f5)
        p5 = clamp01((t - tH - 0.5) / 0.7)
        if p5 > 0:
            pen_line(ctx, 250, 690, 300 + 10, 640, RED, seed=41, width=8, progress=p5)
            if p5 >= 1:
                pen_line(ctx, 310, 640, 286, 643, RED, seed=42, width=8)
                pen_line(ctx, 310, 640, 303, 664, RED, seed=43, width=8)
    # 名札（書き進む）
    wr(ctx, "砦を攻める兵", 255, 380, 38, INK, tE + 0.0 * dE, t, align="center", alpha=1.0)
    wr(ctx, "城を守る兵", 765, 380, 38, INK, tE + 0.33 * dE, t, align="center")
    wr(ctx, "後ろに控える兵", 770, 785, 38, INK, tE + 0.66 * dE, t, align="center")
    q = fade(t, tH, 0.4)
    if q > 0.003:
        text(ctx, "本陣", 470, 408, 52, RED, alpha=q)
        pen_circle(ctx, 470, 585, 255, 130, RED, seed=51, width=6, progress=clamp01((t - tH - 0.3) / 0.8), alpha=q)


# ---- ch3: 崩れる・勝った1回 ----
def L_crumble(ctx, t):
    draw_sc(ctx, SC_CRUMBLE, t)
    labels_sc(ctx, "hill", out_fade(t, SC_CRUMBLE.rout - 0.1, 0.3))
    legend_fig(ctx)
    q = fade(t, SC_CRUMBLE.rout + 0.9, 0.4)
    if q > 0.003:
        pen_line(ctx, 560, 440, 820, 440, RED, seed=61, width=8, progress=clamp01((t - SC_CRUMBLE.rout - 0.9) / 0.6), alpha=q)
        text(ctx, "退く", 690, 395, 56, RED, alpha=q)


def L_hill(ctx, t):
    draw_sc(ctx, SC_HILL, t)
    labels_sc(ctx, "hill", 1.0)
    legend_fig(ctx)


def L_idle2(ctx, t):
    draw_sc(ctx, SC_FIELD, t)
    labels_sc(ctx, "field", 1.0)
    legend_fig(ctx, n=FIG_F)


def counters(ctx, sc, t, a, lab_r="本陣"):
    r_ = sc.row_at(t)
    o, i = sc.path[r_]
    text(ctx, f"織田 {o:,}人", 290, 830, 42, FLAG_O, alpha=a)
    text(ctx, f"{lab_r} {i:,}人", 690, 830, 42, FLAG_I, alpha=a)


def L_win3(ctx, t):
    draw_sc(ctx, SC_WIN, t)
    labels_sc(ctx, "hill", out_fade(t, SC_WIN.rout - 0.1, 0.3))
    legend_fig(ctx)
    counters(ctx, SC_WIN, t, fade(t, _T_W0 - 0.2, 0.3))


def L_rain4(ctx, t):
    draw_sc(ctx, SC_RAIN, t)
    labels_sc(ctx, "hill", 1.0)
    legend_fig(ctx)
    rain_draw(ctx, t, fade(t, Sk("c4_rain", 0.0), 0.5) * out_fade(t, Ek("c4_stop"), 0.6))


# ---- ch5: 置き方を変えたら（小さな絵が並ぶ）----
def var_cell(ctx, x0, y0, w, h, a):
    ctx.set_source_rgba(1, 1, 1, 0.55 * a)
    rrect(ctx, x0, y0, w, h, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, w, h, 14)
    ctx.stroke()


def icons_row(ctx, x0, y, n, team, per_row, k=0.30, pitch=29.0, a=1.0, rowh=40.0):
    s_ = sprite_soldier(team, False, k)
    for i in range(n):
        r_, c_ = divmod(i, per_row)
        ctx.set_source_surface(s_, x0 + c_ * pitch - s_.get_width() / 2, y + r_ * rowh - s_.get_height() + 8)
        ctx.paint_with_alpha(a)


VAR_STATES = [  # (手がかり, 本陣の体数, 織田の体数, 本陣の見出し, 織田の見出し, 変わった所)。1体＝250人
    ("c5_1", 20, 8, "本陣 5千", "織田 2千", None),
    ("c5_h6", 24, 8, "本陣 6千", "織田 2千", "hon"),
    ("c5_h4", 16, 8, "本陣 4千", "織田 2千", "hon"),
    ("c5_o3", 20, 12, "本陣 5千", "織田 3千", "oda"),
]


def L_var5(ctx, t):
    """置き方を変えたら: 1つの絵（本陣と織田の人数）が台詞に合わせて変わる ＋ 崩れる所の目盛り"""
    st = None
    for s_ in VAR_STATES:
        if t >= Sk(s_[0], 0.2):
            st = s_
    a = fade(t, Sk("c5_1", 0.2), 0.4)
    if st is not None and a > 0.003:
        _k, nh, no, lh, lo, ch_ = st
        var_cell(ctx, 60, 110, 860, 350, a)
        text(ctx, lh, 84, 150, 46, FLAG_I if ch_ == "hon" else PENCIL_T, align="left", alpha=a)
        icons_row(ctx, 108, 250, nh, "I", 12, k=0.5, pitch=62.0, rowh=56.0, a=a)
        text(ctx, lo, 84, 352, 46, FLAG_O if ch_ == "oda" else PENCIL_T, align="left", alpha=a)
        icons_row(ctx, 108, 440, no, "O", 12, k=0.5, pitch=62.0, a=a)
        tg = fade(t, Sk("c5_o3", 0.5), 0.4)
        if ch_ == "oda" and tg > 0.003:
            text(ctx, "いちばん勝てる", 330, 352, 44, RED, align="left", alpha=a * tg)
    b = fade(t, Sk("c5_r2", 0.1), 0.4)
    if b > 0.003:
        x0, y0, w, h = 60, 490, 860, 440
        var_cell(ctx, x0, y0, w, h, b)
        text(ctx, "本陣が崩れる所（失った兵の割合）", x0 + 20, y0 + 44, 42, INK, align="left", alpha=b)
        ax0, ax1 = 130.0, 850.0
        ux = (ax1 - ax0) / 5.0
        ctx.set_source_rgba(*hexrgb("#ffd84d", 0.85 * b))
        rrect(ctx, ax0 + ux, y0 + 90, 4 * ux, 52, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(RED, 0.92 * b))
        rrect(ctx, ax0 + 2 * ux, y0 + 156, 3 * ux, 52, 6)
        ctx.fill()
        text(ctx, "基本 1割〜5割", ax0 + ux * 3, y0 + 116, 42, INK, alpha=b)
        text(ctx, "2割〜5割", ax0 + ux * 3.5, y0 + 182, 42, "#ffffff", alpha=b)
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * b))
        ctx.set_line_width(3)
        ctx.move_to(ax0, y0 + 246)
        ctx.line_to(ax1, y0 + 246)
        ctx.stroke()
        for i in range(6):
            xx = ax0 + ux * i
            ctx.move_to(xx, y0 + 238)
            ctx.line_to(xx, y0 + 254)
            ctx.stroke()
            text(ctx, "0" if i == 0 else f"{i}割", xx, y0 + 292, 42, INK, alpha=b)
        text(ctx, "崩れにくい本陣 → 勝ちはゼロ", x0 + 20, y0 + 372, 46, RED, align="left", alpha=b * fade(t, Sk("c5_r2", 0.6), 0.4))


# ---- ch6: 後ろの今川 ----
Q6_X = [105 + 210 * i for i in range(4)]


def L_q6(ctx, t):
    ctx.save()
    draw_bg(ctx, "hill")
    ctx.restore()
    SC6_BATTLE.draw(ctx, t, view=VIEW_ID, field=False)
    a = fade(t, Sk("c6_all", 0.2), 0.4)
    if a > 0.003:
        text(ctx, "次々に来る今川（5千人ずつ）", LCX, 128, 40, INK, alpha=a)
        t_dead = SC6_T1[-1] + 1.3
        for i, x in enumerate(Q6_X):
            ai = a * fade(t, Sk("c6_all", 0.35 + 0.15 * i), 0.3)
            if ai <= 0.003:
                continue
            on = (i == 0 and S("g6") <= t < t_dead)
            ctx.set_source_rgba(*hexrgb("#ffd0da" if on else "#f1e6e4", 0.95 * ai))
            rrect(ctx, x, 160, 150, 74, 12)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(FLAG_I, 0.9 * ai))
            ctx.set_line_width(4 if on else 2.5)
            rrect(ctx, x, 160, 150, 74, 12)
            ctx.stroke()
            text(ctx, "5千", x + 75, 198, 48, FLAG_I, alpha=ai)
            if i < 3:
                arrow_glyph(ctx, x + 158, 198, 38, PENCIL, ai, 3.5)
        if t >= t_dead:
            q = fade(t, t_dead, 0.4)
            pen_line(ctx, Q6_X[0] + 12, 170, Q6_X[0] + 138, 224, RED, seed=71, width=8, progress=clamp01((t - t_dead) / 0.4), alpha=q)
            pen_line(ctx, Q6_X[0] + 138, 170, Q6_X[0] + 12, 224, RED, seed=72, width=8, progress=clamp01((t - t_dead - 0.3) / 0.4), alpha=q)
    legend_fig(ctx)


# ---- ch7: 江戸時代の谷 ----
def L_valley7(ctx, t):
    draw_sc(ctx, SC_VALLEY, t)
    labels_sc(ctx, "valley", fade(t, Sk("c7_valley", 0.3), 0.4))
    a = fade(t, Sk("c7_valley", 0.0), 0.4)
    if a > 0.003:
        mini_sticky(ctx, "江戸時代の話", 100, 150, 60, "pink", fg=RED, a=a, align="left", tilt=-0.02)
        text(ctx, "（史実ではないという見方が多い話）", 100, 232, 36, PENCIL_T, align="left", bold=False, alpha=a * fade(t, Sk("c7_edo", 0.5), 0.5))
    q = fade(t, Sk("c7_w", 0.2), 0.4)
    if q > 0.003:
        tag(ctx, f"いちばん前で矢を放てる人数 {PR['W_SET'][0]}〜{PR['W_SET'][-1]}人", LCX, 770, 38, INK, q)
    legend_fig(ctx, 1.0, y=900)


# ---- ch8: まとめ（ch0 の決着の絵に戻る）----
def L_end8(ctx, t):
    draw_sc(ctx, SC_OPEN, 40.0 + (t - S("ch8")), shake=False)
    labels_sc(ctx, "field", fade(t, S("ch8") + 0.5, 0.4))
    legend_fig(ctx, fade(t, S("ch8") + 0.5, 0.4), n=FIG_F)


LAYERS = []


def layer(name, t0, t1, fn, fi=0.4, fo=0.4):
    LAYERS.append((name, t0, t1, fn, fi, fo))


T_W0, T_W1 = _T_W0, S("ch4")
T_ES = Ek("c8_5") + 0.3                              # 終了画面の始まり（まとめの最後の説明を言い終わって 0.3秒後）
layer("title", 0.0, S("ch1") + 0.3, lambda ctx, t: L_title(ctx, t), fi=0.0)
layer("open0", 0.0, Sk("c0_b", 0.85), L_open0, fi=0.0)                  # 無音はなし。次の文「1560年…」のあいだも、戦いの絵は続く
layer("field_c1", Sk("c0_b", 0.85), S("g1"), L_field_c1)
layer("grid1", S("g1"), Sk("c1_2x"), mk_grid_layer("g1", "L1"))
layer("diag1", Sk("c1_2x"), S("ch2"), L_diag2x)
layer("idle2", S("ch2"), Sk("c2_split"), L_idle2)
layer("map2", Sk("c2_split"), Sk("c2_5k", 0.55), L_map)
layer("hill2", Sk("c2_5k", 0.55), S("g2"), L_hill)
layer("grid2", S("g2"), S("ch3"), mk_grid_layer("g2", "L2"))
layer("crumble3", S("ch3"), Ek("c3_intro") + 0.4, L_crumble)
layer("hill3", Ek("c3_intro") + 0.4, S("g3"), L_hill)
layer("grid3", S("g3"), T_W0 - 0.2, mk_grid_layer("g3", "L3"))
layer("win3", T_W0 - 0.2, S("ch4"), L_win3)
layer("rain4", S("ch4"), S("g4"), L_rain4)
layer("grid4", S("g4"), S("ch5"), mk_grid_layer("g4", "L4"))
layer("var5", S("ch5"), S("ch6"), L_var5)
layer("q6", S("ch6"), S("ch7"), L_q6)
layer("valley7", S("ch7"), S("g7"), L_valley7)
layer("grid7", S("g7"), S("ch8"), mk_grid_layer("g7", "L7"))
layer("end8", S("ch8"), T_ES + 0.8, L_end8)


def draw_left(ctx, t):
    ctx.save()
    clip_left(ctx)
    for name, t0, t1, fn, fi, fo in LAYERS:
        if t < t0 - 1e-6 or t > t1 + fo:
            continue
        a = (1.0 if fi <= 0 else ease_out(clamp01((t - t0) / fi))) * (1.0 if fo <= 0 else 1 - clamp01((t - t1) / fo))
        grp(ctx, a, fn, t)
    ctx.restore()


# ============================================================
# 右ページ（付せん・目盛り・帯）と、右下の「勝率」の棒の枠
# ============================================================
def stk(ctx, t, key, s, y, color="yellow", fg=INK, a=1.0, size=40, tilt=-0.012, off=0.3, x=RX, frac=0.0):
    """右ページの付せん。台本の文（手がかり key）から現れる"""
    t0 = Sk(key, frac) + off
    if t >= t0:
        return mini_sticky(ctx, s, x, y, size, color, fg=fg, a=a * fade(t, t0), align="left", tilt=tilt)
    return 0, 0


QLINES = ["もう一度", "戦ったら、", "2千人は勝てる？"]
QTXT = "\n".join(QLINES)                                 # サムネと同じ言葉（最初は 100px・3行。1560年の文から小さく2行にして、付せんの場所をあける）
QSMALL = "もう一度戦ったら、\n2千人は勝てる？"


def R_ch0(ctx, t):
    big = out_fade(t, Sk("c0_b", 0.0) - 0.2, 0.4)
    if big > 0.003:
        text(ctx, QTXT, RX, 285, 100, INK, align="left", alpha=big)
        pen_line(ctx, RX - 4, 478, RX + text_width("2千人は勝てる？", 100) + 4, 474, RED, seed=5, width=9, progress=clamp01(t / 0.6), alpha=big)
    small = 1 - big
    if small > 0.003:
        text(ctx, QSMALL, RX, 190, 66, INK, align="left", alpha=small)
        pen_line(ctx, RX - 4, 274, RX + text_width("2千人は勝てる？", 66) + 4, 270, RED, seed=5, width=7, alpha=small)
    if t >= Sk("c0_c", 0.3):
        sticky(ctx, "1万回", RX + 150, 372, 64, "pink", fg=RED, a=fade(t, Sk("c0_c", 0.3), 0.3), tilt=-0.02)
    t_f = Sk("c0_f", 0.4)
    if t >= t_f:
        w1, _h = mini_sticky(ctx, "今川 2万5千", RX, 470, 44, "pink", fg=FLAG_I, a=fade(t, t_f, 0.3), align="left", tilt=-0.015)
        mini_sticky(ctx, "織田 2千", RX + w1 + 24, 470, 44, "blue", fg=FLAG_O, a=fade(t, t_f + 0.5, 0.3), align="left", tilt=0.012)
        wr(ctx, "諸説あり", RX, 528, 40, PENCIL_T, t_f + 1.0, t, cps=8, alpha=1.0)


def R_ch1(ctx, t):
    k_ = ihalf(RES["k50"]["L1"]["theory"])
    stk(ctx, t, "c1_first", f"1人あたり {k_}倍強く", 138, "pink", fg=RED, size=62, tilt=-0.015, off=0.25)
    stk(ctx, t, "c1_bow", "弓だけ", 236, "yellow", size=48)
    stk(ctx, t, "c1_25", "25本に1本", 322, "pink", fg=RED, size=48, tilt=0.012)
    stk(ctx, t, "c1_win", "全滅させたら 勝ち", 408, "mint", size=44)
    stk(ctx, t, "c1_156", f"強さの差 約{k_}倍", 494, "pink", fg=RED, size=50, tilt=-0.015)


def R_ch2(ctx, t):
    stk(ctx, t, "c2_split", "今川は 何か所にも\n分かれていた", 172, "mint", size=42)
    stk(ctx, t, "c2_5k", f"本陣 {N_HON // 1000}千", 300, "pink", fg=RED, size=56, tilt=0.012)
    stk(ctx, t, "c2_5k", f"織田 {N_ODA // 1000}千 vs 本陣 {N_HON // 1000}千", 400, "blue", size=42, frac=0.6)


def scale_axis(ctx, x0, x1, y, a=1.0):
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(3.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y)
    ctx.line_to(x1, y)
    ctx.stroke()


def R_ch3(ctx, t):
    stk(ctx, t, "c3_last", "最後の1人まで", 134, "yellow", size=46)
    tl_ = Sk("c3_last", 0.3) + 0.5
    if t >= tl_:
        wlast = text_width("最後の1人まで", 46) + 44
        pen_line(ctx, RX - 6, 134, RX + wlast + 6, 132, RED, seed=81, width=8, progress=clamp01((t - tl_) / 0.5))
    stk(ctx, t, "c3_nobu", "信長公記", 214, "mint", size=46, tilt=0.012)
    stk(ctx, t, "c3_intro", "崩れる ＝ 戦うのをやめて退く", 292, "pink", fg=RED, size=40)
    # 目盛り: 本陣が崩れる所（失った兵の割合）。両はし「1割」「5割」だけ・太い帯
    a = fade(t, Sk("c3_r", 0.0), 0.4)
    x1, x5, y = 1220.0, 1740.0, 462.0
    if a > 0.003:
        text(ctx, "本陣が崩れる所（毎回ばらばら）", RX, 360, 40, INK, align="left", alpha=a)
        text(ctx, "1割〜5割", (x1 + x5) / 2, 410, 48, INK, alpha=a * fade(t, Sk("c3_r", 0.5), 0.4))
        pb = clamp01((t - Sk("c3_r", 0.35)) / 0.7)
        if pb > 0:
            ctx.set_source_rgba(*hexrgb("#ffd84d", 0.9 * a))
            rrect(ctx, x1, y - 24, (x5 - x1) * ease_out(pb), 48, 6)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
            ctx.set_line_width(3.5)
            rrect(ctx, x1, y - 24, (x5 - x1) * ease_out(pb), 48, 6)
            ctx.stroke()
        for xx, lab in ((x1, "1割"), (x5, "5割")):
            text(ctx, lab, xx, y + 52, 44, INK, alpha=a)
    b = fade(t, Sk("c3_usual", 0.3), 0.4)
    if b > 0.003:
        pen_line(ctx, x1, 424, x1, 506, RED, seed=83, width=10, progress=clamp01((t - Sk("c3_usual", 0.3)) / 0.5), alpha=b)
        text(ctx, "ここまでしか倒せない", x1 + 40, 548, 40, RED, align="left", alpha=b * fade(t, Sk("c3_usual", 0.5), 0.4))


def dots100(ctx, x0, y0, wins, a=1.0, size=22.0, t0=0.0, t=None):
    """100回のうち wins回（青）。残りは灰色"""
    for i in range(100):
        r_, c_ = divmod(i, 10)
        win = i < wins
        ctx.set_source_rgba(*hexrgb(WIN_C if win else "#cfc9bb", a))
        ctx.rectangle(x0 + c_ * size, y0 + r_ * size, size - 3, size - 3)
        ctx.fill()


def R_ch4(ctx, t):
    stk(ctx, t, "c4_face", "突然の雨\n今川の顔に打ちつけた", 182, "blue", size=40)
    stk(ctx, t, "c4_s", f"先に放てる 0〜{max(PR['S_SET'])}回", 296, "pink", fg=RED, size=44, tilt=0.012)
    r3 = LAD["L4"]["by_s"][str(max(PR["S_SET"]))]["rate"]
    stk(ctx, t, "c4_three", f"先に{max(PR['S_SET'])}回放てると {ihalf(r3 * 100)}%", 384, "mint", size=40)
    a = fade(t, Sk("c4_res", 0.6), 0.4)
    if a > 0.003:
        w6 = ihalf(LAD["L4"]["rate"] * 100)
        dots100(ctx, 1560, 140, w6, a)
        text(ctx, f"100回のうち\n{w6}回が勝ち", 1670, 400, 40, INK, alpha=a)


def R_ch5(ctx, t):
    stk(ctx, t, "c5_1", "決め方しだいで 変わる", 150, "yellow", size=44)
    a = fade(t, Sk("c5_band", 0.2), 0.4)
    if a > 0.003:
        lo = 0
        hi = ihalf(L5["L5-3"]["rate"] * 100)
        ax0, ax1, y = 1090.0, 1790.0, 372.0
        text(ctx, "勝てる割合の幅", RX, 300, 44, INK, align="left", alpha=a)
        scale_axis(ctx, ax0, ax1, y, a)
        pb = clamp01((t - Sk("c5_band", 0.4)) / 0.8)
        ctx.set_source_rgba(*hexrgb("#7ea6e6", 0.85 * a))
        rrect(ctx, ax0, y - 17, (ax1 - ax0) * hi / 100.0 * ease_out(pb), 34, 5)
        ctx.fill()
        for v in (0, 50, 100):
            xx = ax0 + (ax1 - ax0) * v / 100.0
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
            ctx.set_line_width(3)
            ctx.move_to(xx, y - 10)
            ctx.line_to(xx, y + 10)
            ctx.stroke()
            text(ctx, f"{v}%", xx, y + 46, 40, INK, alpha=a)
        text(ctx, f"{lo}%〜{hi}%", 1300, 470, 66, RED, alpha=a * fade(t, Sk("c5_band", 0.6), 0.4))


def R_ch6(ctx, t):
    stk(ctx, t, "c6_1", "全部の今川と 戦う", 150, "yellow", size=44)
    stk(ctx, t, "c6_700", "本陣に勝った回の\n織田の残り 700人足らず", 262, "mint", size=40, tilt=0.012)
    t_lo, t_hi = sorted((L6["L6-20000-1"]["cfg"]["H"] + sum(L6["L6-20000-1"]["cfg"]["groups"]), L6["L6-45000-1"]["cfg"]["H"] + sum(L6["L6-45000-1"]["cfg"]["groups"])))
    stk(ctx, t, "c6_tot", f"総勢 {t_lo // 10000}万〜{t_hi // 10000}万5千 でも 0回", 392, "pink", fg=RED, size=42, tilt=-0.012)


def R_ch7(ctx, t):
    stk(ctx, t, "c7_valley", "江戸時代の話", 150, "pink", fg=RED, size=48)
    stk(ctx, t, "c7_rec", "信長公記: おけはさま山", 238, "mint", size=42, tilt=0.012)
    wlo, whi = PR["W_SET"][0], PR["W_SET"][-1]
    a = fade(t, Sk("c7_w", 0.3), 0.4) * out_fade(t, S("g7") + 0.5, 0.4)
    if a > 0.003:
        ax0, ax1, y = 1090.0, 1790.0, 392.0
        text(ctx, "いちばん前で矢を放てる人数", RX, 322, 38, INK, align="left", alpha=a)
        scale_axis(ctx, ax0, ax1, y, a)
        xf = lambda v: ax0 + (ax1 - ax0) * v / 200.0
        ctx.set_source_rgba(*hexrgb("#ffd84d", 0.8 * a))
        rrect(ctx, xf(wlo), y - 15, (xf(whi) - xf(wlo)) * ease_out(clamp01((t - Sk("c7_w", 0.5)) / 0.8)), 30, 5)
        ctx.fill()
        for v in (0, wlo, 100, whi):
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
            ctx.set_line_width(3)
            ctx.move_to(xf(v), y - 10)
            ctx.line_to(xf(v), y + 10)
            ctx.stroke()
            text(ctx, f"{v}", xf(v), y + 44, 36, INK, alpha=a)
    # 勝つ割合の幅（谷）: 本陣が3割を失うまで崩れない … 45%〜100%
    lo = ihalf(min(L7["L7-r35"]["rate"], L7["L7-r25"]["rate"], L7["L7-r13"]["rate"]) * 100)
    hi = ihalf(max(L7["L7-r35"]["rate"], L7["L7-r25"]["rate"], L7["L7-r13"]["rate"]) * 100)
    b = fade(t, Sk("c7_r3", 0.4), 0.4) * out_fade(t, Sk("c7_edo2", 0.0), 0.4)
    if b > 0.003:
        ax0, ax1, y = 1090.0, 1790.0, 400.0
        text(ctx, "谷で勝てる割合の幅", RX, 322, 38, INK, align="left", alpha=b)
        scale_axis(ctx, ax0, ax1, y, b)
        xf = lambda v: ax0 + (ax1 - ax0) * v / 100.0
        ctx.set_source_rgba(*hexrgb("#7ea6e6", 0.85 * b))
        rrect(ctx, xf(lo), y - 17, (xf(hi) - xf(lo)) * ease_out(clamp01((t - Sk("c7_r3", 0.6)) / 0.8)), 34, 5)
        ctx.fill()
        for v in (0, 50, 100):
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * b))
            ctx.set_line_width(3)
            ctx.move_to(xf(v), y - 10)
            ctx.line_to(xf(v), y + 10)
            ctx.stroke()
            text(ctx, f"{v}%", xf(v), y + 46, 36, INK, alpha=b)
        text(ctx, f"{lo}%〜{hi}%", 1380, 505, 62, RED, alpha=b * fade(t, Sk("c7_r3", 0.8), 0.4))
    # 2本の棒を並べる: 江戸時代の谷 vs 記録に近い桶狭間
    c = fade(t, Sk("c7_edo2", 0.0), 0.4)
    if c > 0.003:
        base, hmax = 500.0, 190.0
        v_edo, v_rec = LAD["L7"]["rate"], LAD["L4"]["rate"]
        scale_axis(ctx, 1090, 1790, base, c)
        for xc, v, lab, col, t_k in ((1290.0, v_edo, "江戸時代の谷", ORANGE, Sk("c7_edo2", 0.4)), (1590.0, v_rec, "記録に近い", BLUE, Sk("c7_rec2", 0.4))):
            u = ease_out(clamp01((t - t_k) / 0.8))
            hh = max(3.0, hmax * v) * u if t >= t_k else 0.0
            ctx.set_source_rgba(*hexrgb(col, 0.9 * c))
            rrect(ctx, xc - 60, base - hh, 120, hh, 6)
            ctx.fill()
            if t >= t_k + 0.3:
                text(ctx, pct_txt(v), xc, base - hh - 36, 56, col, alpha=c * fade(t, t_k + 0.3, 0.3))
            text(ctx, lab, xc, base + 38, 36, INK, alpha=c)


R_CH = [R_ch0, R_ch1, R_ch2, R_ch3, R_ch4, R_ch5, R_ch6, R_ch7]


def draw_right(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    if idx >= len(R_CH):
        return
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, R_CH[idx - 1], t)
    R_CH[idx](ctx, t)


# ---- 勝率の棒の枠（右下。最初から出しっぱなし。ch8 で右ページいっぱいに並べる）----
GEO_PS = dict(box=(1030, 560, 1830, 920), cap=(1062, 594, 44), label_x=1062, label_size=44, track_x=1350, track_w=300, val_x=1662,
              val_size=52, bar_h=34, rows=[656, 716, 776, 836, 896])
GEO_PB = dict(box=(1030, 100, 1830, 920), cap=(1062, 150, 56), label_x=1062, label_size=56, track_x=1420, track_w=240, val_x=1676,
              val_size=60, bar_h=52, rows=[290, 420, 550, 680, 820])
VAL = {k: LAD[k]["rate"] for k in LAD}


def arrow_down(ctx, x, y, h, col, a=1.0):
    """小さな ↓（条件を足していく向き）"""
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(3.2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y - h)
    ctx.line_to(x, y + h)
    ctx.stroke()
    ctx.move_to(x - 7, y + h - 7)
    ctx.line_to(x, y + h)
    ctx.line_to(x + 7, y + h - 7)
    ctx.stroke()


def bar_row(ctx, G, i, label, la, col, frac, vtxt, bu, ta, vsz=None, lcol=INK, sub=None):
    """1本の棒。la=名札の濃さ、ta=枠の濃さ、bu=棒の伸び（0〜1）"""
    y = G["rows"][i]
    tx, tw, bh = G["track_x"], G["track_w"], G["bar_h"]
    if ta > 0.003:
        ctx.set_source_rgba(1, 1, 1, 0.7 * ta)
        rrect(ctx, tx, y - bh / 2, tw, bh, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * ta))
        ctx.set_line_width(2.5)
        rrect(ctx, tx, y - bh / 2, tw, bh, 6)
        ctx.stroke()
    if la > 0.003 and label:
        text(ctx, label, G["label_x"], y, G["label_size"], lcol, align="left", alpha=la)
        if sub:
            text(ctx, sub, G["label_x"], y + G["label_size"] * 0.95, 36, PENCIL_T, align="left", bold=False, alpha=la)
    if bu > 0.003 and ta > 0.003:
        wd = max(3.0, tw * frac) * bu if frac > 0 else 0.0
        if wd > 0:
            ctx.set_source_rgba(*hexrgb(col, 0.92 * ta))
            rrect(ctx, tx, y - bh / 2, wd, bh, 6)
            ctx.fill()
        if vtxt and bu > 0.15:
            text(ctx, vtxt, G["val_x"], y, vsz or G["val_size"], col, align="left", alpha=ta * clamp01((bu - 0.15) / 0.3))


def draw_box(ctx, G, a, y1=None):
    x0, y0, x1, y1_ = G["box"]
    y1 = y1_ if y1 is None else y1
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()


LADDER = [  # (行, 名札, id, 名札の時刻, 棒の時刻, 色)
    (0, "野原・全軍", "L1", lambda: S("ch1") + 0.9, lambda: Sk("c1_res", 0.55), BLUE),
    (1, "＋本陣だけ", "L2", lambda: S("ch2") + 0.9, lambda: Sk("c2_res", 0.5), BLUE),
    (2, "＋崩れ", "L3", lambda: S("ch3") + 0.9, lambda: Sk("c3_res", 0.5), BLUE),
    (3, "＋雨", "L4", lambda: S("ch4") + 0.9, lambda: Sk("c4_res", 0.5), BLUE),
]
GEO_PV = dict(GEO_PS, label_size=42, track_x=1440, track_w=210, val_x=1664, val_size=56, bar_h=40, rows=[690, 775, 860])
VARIANTS = [  # 5章の右の表は3行だけ（名札, 値, 画面の値, 棒の時刻）。いちばん勝てる＝織田3千 42%、いちばん負ける＝本陣が2割を失うまで崩れない 0%
    ("基本（＋雨まで）", VAL["L4"], pct_txt(VAL["L4"]), lambda: S("ch5") + 0.8),
    ("いちばん勝てる", L5["L5-3"]["rate"], pct_txt(L5["L5-3"]["rate"]), lambda: Sk("c5_o3", 0.55)),
    ("崩れにくい本陣", L5["L5-4"]["rate"], pct_txt(L5["L5-4"]["rate"]), lambda: Sk("c5_r2", 0.55)),
]


def bu_of(t, tb, d=0.9):
    return ease_out(clamp01((t - tb) / d))


def panel_small(ctx, t, a):
    G = GEO_PS
    t_fr = Sk("c0_d", 0.3)                                               # 「勝率の棒が5本並ぶ枠」が出る
    draw_box(ctx, G, a, lerp(704.0, G["box"][3], ease_out(clamp01((t - t_fr + 0.1) / 0.6))))      # 最初は1本ぶん。枠が出るときに5本ぶんへ広がる
    text(ctx, "勝率", G["cap"][0], G["cap"][1], G["cap"][2], INK, align="left", alpha=a)
    v_a = fade(t, S("ch5") + 0.2, 0.4) * out_fade(t, S("ch6") - 0.1, 0.4)       # ch5 だけ、置き方を変えた棒に差し替える
    l_a = 1 - v_a
    tz_a = out_fade(t, t_fr, 0.4)
    tr_a = lambda i: 1.0 if i == 0 else fade(t, t_fr + 0.12 * i, 0.4)
    if tz_a > 0.003:                                                     # ch0 の最初の棒（数字は伏せる）: 0% から少し伸びて止まる
        bar_row(ctx, G, 0, "", 0, BLUE, VAL["L4"], "？%", ease(clamp01(t / 4.0)), a * tz_a)
    for (i, lab, vid, tlf, tbf, col) in LADDER:
        ta = tr_a(i) * l_a * a * ((1 - tz_a) if i == 0 else 1.0)
        bar_row(ctx, G, i, lab, fade(t, tlf(), 0.4) * l_a * a, col, VAL[vid], pct_txt(VAL[vid]), bu_of(t, tbf()), ta)
    # 5行目: ch6 は「全部に勝つ」、ch7 からは「江戸時代の谷」
    ta5 = tr_a(4) * l_a * a
    bar_row(ctx, G, 4, "", 0, BLUE, 0.0, "", 0.0, ta5)
    m6 = fade(t, S("ch6") + 0.9, 0.4) * out_fade(t, S("ch7") + 0.3, 0.4)
    m7 = fade(t, S("ch7") + 0.9, 0.4)
    bar_row(ctx, G, 4, "全部に勝つ", m6 * ta5, BLUE, 0.0, "0%", bu_of(t, Sk("c6_res", 0.5)) * m6, ta5 * m6)
    sep = ta5 * max(m6, m7)                                              # 「全部に勝つ」「江戸時代の谷」は、積み上げの梯子とは別の枝（点線で分ける）
    if sep > 0.003:
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * sep))
        ctx.set_line_width(3)
        ctx.set_dash([10, 8])
        ctx.move_to(G["box"][0] + 24, (G["rows"][3] + G["rows"][4]) / 2)
        ctx.line_to(G["box"][2] - 24, (G["rows"][3] + G["rows"][4]) / 2)
        ctx.stroke()
        ctx.set_dash([])
    for i_ in range(3):                                                  # 行と行のあいだに ↓（条件を足していく）
        al = fade(t, LADDER[i_ + 1][3]() + 0.3, 0.4) * l_a * a
        if al > 0.003:
            arrow_down(ctx, G["track_x"] + 18, (G["rows"][i_] + G["rows"][i_ + 1]) / 2, 11, PENCIL_T, al)
    bar_row(ctx, G, 4, "江戸時代の谷", m7 * ta5, ORANGE, VAL["L7"], pct_txt(VAL["L7"]), bu_of(t, Sk("c7_res", 0.55)) * m7, ta5 * m7)
    if v_a > 0.003:                                                      # ch5: 置き方を変えた棒（基本の棒の横に並べる）
        for j, (lab, v, vt, tb_) in enumerate(VARIANTS):
            bar_row(ctx, GEO_PV, j, lab, v_a * a * fade(t, S("ch5") + 0.4 + 0.05 * j, 0.4), BLUE, v, vt, bu_of(t, tb_()), v_a * a, vsz=56)


def panel_big(ctx, t, a):
    """ch8: 勝率の棒を並べる（野原 0% → 本陣だけ 0% → 崩れ 0.3% → 雨 6% ／ 江戸時代の谷 73%）"""
    G = GEO_PB
    draw_box(ctx, G, a)
    text(ctx, "勝率（100回のうち 勝つ割合）", G["cap"][0], G["cap"][1], 44, INK, align="left", alpha=a)
    keys = ["c8_1", "c8_2", "c8_2", "c8_2", "c8_4"]
    fr = [0.2, 0.3, 0.55, 0.8]
    for j, (i, lab, vid, _tl, _tb, col) in enumerate(LADDER):
        tb = Sk("c8_1", 0.4) if j == 0 else Sk("c8_2", fr[j - 1] * 0.9)
        bar_row(ctx, G, j, lab, a * fade(t, tb - 0.2, 0.4), col, VAL[vid], pct_txt(VAL[vid]), bu_of(t, tb), a * fade(t, tb - 0.2, 0.4))
    tb = Sk("c8_4", 0.1)
    sepb = a * fade(t, tb - 0.2, 0.4)
    if sepb > 0.003:
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * sepb))
        ctx.set_line_width(3)
        ctx.set_dash([10, 8])
        ctx.move_to(G["box"][0] + 24, (G["rows"][3] + G["rows"][4]) / 2)
        ctx.line_to(G["box"][2] - 24, (G["rows"][3] + G["rows"][4]) / 2)
        ctx.stroke()
        ctx.set_dash([])
    bar_row(ctx, G, 4, "江戸時代の谷", a * fade(t, tb - 0.2, 0.4), ORANGE, VAL["L7"], pct_txt(VAL["L7"]), bu_of(t, tb), a * fade(t, tb - 0.2, 0.4),
            sub="（＋雨のうえで、谷の話。史実ではない）")
    # 矢印（0 → 0 → 0.3% → 6%）
    for j in range(3):
        y = (G["rows"][j] + G["rows"][j + 1]) / 2
        ar = a * fade(t, Sk("c8_2", 0.2 + 0.3 * j), 0.4)
        if ar > 0.003:
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.85 * ar))
            ctx.set_line_width(5)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            xx = G["track_x"] + 40
            ctx.move_to(xx, y - 22)
            ctx.line_to(xx, y + 22)
            ctx.stroke()
            ctx.move_to(xx - 10, y + 10)
            ctx.line_to(xx, y + 24)
            ctx.line_to(xx + 10, y + 10)
            ctx.stroke()


def draw_panel(ctx, t):
    a_all = out_fade(t, T_ES, 0.4)
    a_big_in = fade(t, S("ch8") + 0.3, 0.5)
    grp(ctx, a_all * (1 - a_big_in), panel_small, t, 1.0)
    grp(ctx, a_all * a_big_in, panel_big, t, 1.0)


# ============================================================
# 章カード・終了画面・全体
# ============================================================
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"
LCX_E, RCX_E = 490, 1430


def big_sticky(ctx, label, value, cx, cy, w, h, color, fg=INK, a=1.0, tilt=0.0, lsz=46, vsz=64, sub=None, ssz=38):
    """終了画面の答えの付せん。上に名前（lsz）、下に答え（vsz）。(cx, cy) は中心"""
    if a <= 0.003:
        return
    bg = STICKY.get(color, color)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, -w / 2 + 6, -h / 2 + 9, w, h, 8)
    ctx.fill()
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, -w / 2, -h / 2, w, h, 8)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(-w / 2, -h / 2, w, 12)
    ctx.fill()
    if sub:
        text(ctx, label, 0, -h * 0.31, lsz, INK, alpha=a)
        text(ctx, value, 0, -h * 0.01, vsz, fg, alpha=a)
        text(ctx, sub, 0, h * 0.31, ssz, PENCIL_T, bold=False, alpha=a)
    else:
        text(ctx, label, 0, -h * 0.22, lsz, INK, alpha=a)
        text(ctx, value, 0, h * 0.2, vsz, fg, alpha=a)
    ctx.restore()


def end_rows():
    r6 = ihalf(LAD["L4"]["rate"] * 100)
    return [("2千人で2万5千人に 野原で挑めば", "勝ち目は ない", "yellow", INK, -0.010, None),
            ("＋本陣だけ・＋崩れ・＋雨 と足して", f"100回に{r6}回", "pink", RED, 0.008, None),
            ("兵の数の決め方しだいで", "多くの場合 織田は負ける", "mint", INK, -0.008, None)]


def end_screen(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "桶狭間を、1万回 戦い直したら", LCX_E, 162, 38, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt, sub) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=62, sub=sub, ssz=40)
    tq, t9 = Sk("c8_q", 0.05), S(ID["c8_ch"])
    if t >= tq:
        q = fade(t, tq, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
        if q > 0.003:
            sticky(ctx, "あなたなら、\n勝ち目を上げるために、\nもう1つ何を足しますか？", RCX_E, 480, 52, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, ch[2], a, size=60)


def pages(ctx, t):
    draw_left(ctx, t)
    draw_right(ctx, t)
    draw_panel(ctx, t)
    overlays(ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    if t < T_ES + 0.6:
        grp(ctx, 1 - fade(t, T_ES, 0.5), pages, t)
    if t >= T_ES:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・早回し）
# ============================================================
def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 9):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for g in sorted(GAP_NOTE):
        if g != "g0":
            beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
            mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
    for k_, (tt, f_) in enumerate(BAR_BELLS()):
        mx.add(tt, bell(f_, 1.0), 0.3)
    mx.add(Sk("c8_q", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S(ID["c8_ch"]) + 0.2, bell(523.3, 1.6), 0.3)
    return mx


def BAR_BELLS():
    ts = [Sk("c1_res", 0.55), Sk("c2_res", 0.5), Sk("c3_res", 0.5), Sk("c4_res", 0.5), Sk("c6_res", 0.5), Sk("c7_res", 0.55)]
    return [(t_ + 0.3, 659.3 if i % 2 else 784.0) for i, t_ in enumerate(ts)]


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
STILL_NAMES = ["① 0.0秒: 題字・問い・矢が飛び交う・勝率の棒", "② 2.5秒: 左がみるみる減る", "③ 5.0秒: 棒が少し伸びた（数字は伏せる）",
               "④ 1章の頭: 弓だけ・25本に1本", "⑤ 1章の答え: マス目が全部負け・棒1", "⑥ 2章: 今川は分かれていた（配置図）",
               "⑦ 3章: 勝った1回・旗が下がって退く", "⑧ 4章: 雨・先に放てる0〜3回", "⑨ 5章: 置き方を変えたら（小さな棒）",
               "⑩ 7章: 江戸時代の谷・2本の棒", "⑪ まとめ: 棒が並ぶ", "⑫ 終了画面"]


def still_times():
    return [0.0, 2.5, 5.0, Sk("c1_25", 0.95), Ek("c1_res") + 0.5, Sk("c2_hon", 0.95), Sk("c3_this", 0.97), Sk("c4_s", 0.97),
            Sk("c5_band", 0.97), Sk("c7_rec2", 0.97) + 0.8, Ek("c8_2") + 0.3, S(ID["c8_ch"]) + 2.0]


def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_sheet(out_dir, names_times, thumb=(480, 270), cols=2, label=True):
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for nm, tt in names_times:
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}")
    W_, H_ = thumb
    lab_h, pad = (34 if label else 0), 10
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        if label:
            dr.text((x + 4, y + H_ + 3), f"{k + 1}  {_ts(names_times[k][1])}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")


def stills_preview(out_dir):
    names = [f"still_{i + 1:02d}" for i in range(len(STILL_NAMES))]
    stills_sheet(out_dir, list(zip(names, still_times())))


# ============================================================
# 文字起こし・読み・画面の文字
# ============================================================
def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字「桶狭間」と問い・矢の撃ち合い・勝率の棒）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE.get(it.id, '映像だけ')}）")
        else:
            nt = LINE_NOTE.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間（左ページに答えの付せん・右ページに問いかけ、亀と「チャンネル登録よろしく」）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    """読みの確認。read_aloud が AivisSpeech を起動するので、--fake-voice のときは読みを作らず、文だけ並べる"""
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            reading = "" if FAKE else "\n    → " + voice.read_aloud(spoken)
            rows.append(f"{it.id}: {shown_}{reading}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


def scan(step=0.25, scale=0.25, t_max=None):
    """0.25秒ごとに描いて、画面の文字（字幕を除く）の位置と、描いた兵の位置を集める"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int((t_max or DUR) / step)
    PEOPLE_ON[0] = True
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        PEOPLE_LOG.clear()
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale, e[6] / scale) for e in core._LOG]
        frames.append((t, ents, [tuple(p) for p in PEOPLE_LOG]))
        core._LOG = None
    PEOPLE_ON[0] = False
    return frames


def write_screen_text(path, frames, step=0.25):
    seen = {}
    for t, ents, *_r in frames:
        for e in ents:
            seen.setdefault(e[0], []).append(t)
    spans = []
    for s_, ts in seen.items():
        a = b = ts[0]
        for x in ts[1:] + [1e9]:
            if x - b > step * 1.5:
                spans.append((a, b + step, s_))
                a = x
            b = x
    spans.sort()
    rows = ["# 画面の文字（字幕を除く）と、見えている区間。0.25秒ごとに描いて調べた", ""]
    for a, b, s_ in spans:
        mark = "  ←短い" if b - a < 1.5 and not any(ch.isdigit() for ch in s_) else ""
        rows.append(f"{_ts(a)}〜{_ts(b)}（{b - a:4.1f}秒） {s_}{mark}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("画面の文字:", path)




# ============================================================
# 場面の照合（台本の合図・声の数字・画面の数字・早回し・絵の大きさ・文字の重なり・字幕・終了画面・長さ）
# ============================================================
NUM_RE = r"\d[\d,]*万\d*千?|\d[\d,]*千|\d+\.\d+|\d[\d,]*"
OVERLAY_OK = set(CH_TITLES)


def voice_nums(txt):
    return [x for x in _re.findall(NUM_RE, txt)]


def _allowed_nums():
    ok = set(range(0, 11)) | {12.5, 25, 50, 100, 200, 250, 500, 700}       # 700＝声「700人足らず」（本陣に勝った回の織田の残り。平均 600〜700 を別に照合）
    for key in ("L1_loss", "L3_win", "L3_loss", "L4_win", "L4_loss", "L6_first_then_loss"):
        for row in SMP[key]["traj"]:
            ok |= {float(v) for v in row}
    for row in SMP["L6_first_then_loss"]["later"][0]["traj"]:
        ok |= {float(v) for v in row}
    for st in list(LAD.values()) + list(L5.values()) + list(L6.values()) + list(L7.values()):
        ok.add(float(ihalf(st["rate"] * 100)))
    ok |= {float(ihalf(LAD["L4"]["by_s"][str(max(PR["S_SET"]))]["rate"] * 100)), 0.3, float(ihalf(RES["k50"]["L1"]["theory"])), float(ihalf(RES["k50"]["L2"]["theory"]))}
    ok |= {float(PR["W_SET"][0]), 100.0, float(PR["W_SET"][-1])}
    ok |= {float(LAD[k]["wins"]) for k in LAD}           # 「1万回のうち ◯回」
    return ok


def overlaps(frames, step=0.25, need=3, shrink=3.0):
    """文字どうしの重なり（同じ2つの文字が need 回続けて＝0.5秒以上重なったら）"""
    runs, bad = {}, {}
    for t, ents, *_r in frames:
        boxes = [(s_, x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink) for s_, x0, y0, x1, y1, *_q in ents if s_ not in OVERLAY_OK]
        hit = set()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] == b[0]:
                    continue
                w_ = min(a[3], b[3]) - max(a[1], b[1])
                h_ = min(a[4], b[4]) - max(a[2], b[2])
                if w_ > 0 and h_ > 0:
                    area = min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2]))
                    if w_ * h_ > 0.08 * area:
                        hit.add(tuple(sorted((a[0], b[0]))))
        for k in list(runs):
            if k not in hit:
                runs.pop(k)
        for k in hit:
            runs[k] = runs.get(k, 0) + 1
            if runs[k] >= need and k not in bad:
                bad[k] = t
    return bad


def _near(frames, t):
    return min(frames, key=lambda f: abs(f[0] - t))


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    has = lambda k, s_: s_ in txt(k)
    checks = []
    A = checks.append
    # ---- 台本の読み込み ----
    A((f"台本: 章は9つ（0〜8）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる",
       float(len(CHAPS) == 9 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS)), 1, 0))
    A(("台本: 「- 」の行の文言を一字も変えずに読んでいる（声の文を並べ直すと台本の行と同じ。長い文だけ「。」で分けた）",
       float("".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line")), 1, 0))
    A(("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_a"]), 0.5, 1e-6))
    A((f"台本: 無音（早回し）の区間は 1・2・3・4・6・7章の6つ（0章の無音はなし。{sorted(GAP_NOTE)}）", float(sorted(GAP_NOTE) == ["g1", "g2", "g3", "g4", "g6", "g7"]), 1, 0))
    # ---- 声の数字 = data.json ----
    r4 = LAD["L4"]["rate"]
    A(("声「1万回中、0回」（1章・2章）＝ L1・L2 の勝ち 0／l1_big（10万回でも0回）の数字 0/100,000",
       float(LAD["L1"]["wins"] == 0 and LAD["L2"]["wins"] == 0 and has("c1_res", "1万回中、0回") and has("c2_res", "1万回中、0回")
             and RES["l1_big"]["wins"] == 0 and RES["l1_big"]["n"] == 100000), 1, 0))
    A(("声「12.5倍」＝ 2万5千÷2千 ＝ 12.5 ／「約156倍」＝ 12.5² ＝ 156.25 の四捨五入 ／（データ）2.5² ＝ 6.25 → 6",
       float(N_ALL / N_ODA == 12.5 and ihalf(RES["k50"]["L1"]["theory"]) == 156 and abs(RES["k50"]["L1"]["theory"] - 12.5 ** 2) < 1e-9 and ihalf(RES["k50"]["L2"]["theory"]) == 6
             and has("c1_125", "12.5倍") and has("c1_156", "約156倍") and has("c1_first", "156倍強く")), 1, 0))
    A(("声「34回」＝ L3 の勝ち 34 ／「627回」「100回に6回ほど」＝ L4 627（6.27%）",
       float(LAD["L3"]["wins"] == 34 and LAD["L4"]["wins"] == 627 and ihalf(r4 * 100) == 6 and 100 - ihalf(r4 * 100) == 94 and has("c3_res", "1万回中、34回")
             and has("c4_res", "627回") and has("c4_res", "100回に6回ほど")), 1, 0))
    r3 = LAD["L4"]["by_s"][str(max(PR["S_SET"]))]["rate"]
    A((f"声「3回先に放てた回だけなら、10回に1回を少し超えます」＝ s=3 の勝率 {r3:.3f}（0.10〜0.15）", float(has("c4_three", "10回に1回を少し超えます") and 0.10 < r3 < 0.15), 1, 0))
    A(("声「本陣6千: 100回に1回もありません」＝ 0.68% ／「本陣4千: 5回に1回ほど」＝ 21.6% ／「織田3千: 5回に2回ほど」＝ 42.1% ／「2割を失うまでは崩れない: ゼロに戻る」＝ 0回",
       float(L5["L5-1"]["rate"] < 0.01 and has("c5_h6", "100回に1回もありません") and 0.18 < L5["L5-2"]["rate"] < 0.25 and has("c5_h4", "5回に1回ほど")
             and 0.38 < L5["L5-3"]["rate"] < 0.45 and has("c5_o3", "5回に2回ほど") and L5["L5-4"]["wins"] == 0 and has("c5_r2", "ゼロに戻ります")), 1, 0))
    hi5 = ihalf(L5["L5-3"]["rate"] * 100)
    A((f"5章の帯「0%〜{hi5}%」＝ 置き方を変えた棒の最小0%と最大{hi5}%（台本の画面の指示にも同じ文字）",
       float(min(L5[k]["rate"] for k in ("L5-1", "L5-2", "L5-3", "L5-4")) == 0.0 and hi5 == 42 and f"0%〜{hi5}%" in LINE_NOTE[ID["c5_band"]]), 1, 0))
    surv = [L6[k]["surv_first_mean"] for k in L6 if k.startswith("L6-20000") or k.startswith("L6-25000") or k.startswith("L6-45000")]
    A((f"声「700人足らず」＝ 本陣に勝った回の織田の残り（平均 {min(surv):.0f}〜{max(surv):.0f}人。600以上700未満）", float(has("c6_700", "700人足らず") and all(600 <= v < 700 for v in surv)), 1, 0))
    A(("声「全部に勝てた回は1万回中0回」「総勢2万人・4万5千人でも0回」＝ L6 の全勝 0",
       float(has("c6_res", "1万回中、0回") and L6["L6-20000-1"]["wins"] == 0 and L6["L6-20000-3"]["wins"] == 0 and L6["L6-45000-1"]["wins"] == 0 and L6["L6-45000-8"]["wins"] == 0
             and has("c6_tot", "2万人") and has("c6_tot", "4万5千人")), 1, 0))
    cl = [RES["mf_cliff"][i]["s0"] for i in (1, 2, 3)]
    r35, r25, r13 = L7["L7-r35"]["rate"], L7["L7-r25"]["rate"], L7["L7-r13"]["rate"]
    lo7, hi7 = ihalf(min(r35, r25, r13) * 100), ihalf(max(r35, r25, r13) * 100)
    A(("声「7,272回」「100回に70回を超えます」＝ L7 7,272（72.72%）／「100回に70回ほど」／（データ）谷で削れる割合 0.38〜0.40／「3割を失うまで崩れない→100回に50回を下回る」＝ 44.95%",
       float(LAD["L7"]["wins"] == 7272 and has("c7_res", "7,272回") and has("c7_res", "100回に70回を超えます") and LAD["L7"]["rate"] > 0.70 and has("c7_edo2", "100回に70回ほど")
             and all(0.37 <= v < 0.40 for v in cl) and has("c7_r3", "100回に50回を下回ります") and r35 < 0.5), 1, 0))
    A((f"7章の帯「{lo7}%〜{hi7}%」＝ 谷で崩れる所を変えた3本（3割〜5割 {r35 * 100:.1f}%・2割〜5割 {r25 * 100:.1f}%・1割〜3割 {r13 * 100:.1f}%）の最小〜最大（台本の画面の指示と同じ文字）",
       float(f"{lo7}%〜{hi7}%" in LINE_NOTE[ID["c7_r3"]] and (lo7, hi7) == (45, 100)), 1, 0))
    A(("声「記録に近い桶狭間なら100回に6回ほど」＝ L4 の 6.27%", float(has("c7_rec2", "100回に6回ほど") and ihalf(r4 * 100) == 6), 1, 0))
    A((f"まとめの棒: 野原・＋本陣だけ・＋崩れ・＋雨・江戸時代の谷 ＝ {[pct_txt(VAL[i]) for i in ('L1', 'L2', 'L3', 'L4', 'L7')]}（台本の画面の指示: 0% → 0% → 0.3% → 6% ／ 73%）",
       float([pct_txt(VAL[i]) for i in ("L1", "L2", "L3", "L4", "L7")] == ["0%", "0%", "0.3%", "6%", "73%"]), 1, 0))
    # ---- マス目 = data.json（勝った回数）----
    for gk in ("L1", "L2", "L3", "L4", "L7"):
        g_ = GRIDS[gk]
        A((f"マス目 {gk}: 1万マス・勝ちの青のマス ＝ data.json の勝ち {LAD[gk]['wins']:,}（数えなおす）", float(g_.n == 10000 and int(g_.win.sum()) == LAD[gk]["wins"] == g_.wins and LAD[gk]["n"] == 10000), 1, 0))
    # ---- 絵の数（1体＝250人）----
    A(("絵: 1体＝250人で割り切れる（織田2千＝8体・本陣5千＝20体・6千＝24体・4千＝16体・織田3千＝12体。野原だけ1体＝500人で織田4体・今川全軍50体）",
       float(all(n % FIG == 0 for n in (N_ODA, N_ALL, N_HON, 6000, 4000, 3000)) and (N_ODA // FIG_F, N_ALL // FIG_F) == (4, 50) and (N_ODA // FIG, N_HON // FIG) == (8, 20)
             and [(c[1], c[2]) for c in VAR_STATES] == [(20, 8), (24, 8), (16, 8), (20, 12)]), 1, 0))
    A(("絵: 織田＝左・青系（旗 #3a73c8）、今川＝右・赤系（旗 #d8434e）。織田の隊の x ＜ 今川の隊の x（野原・丘・谷）",
       float(TEAM["O"]["flag"] == "#3a73c8" and TEAM["I"]["flag"] == "#d8434e" and all(groups_for(k_)[0]["O"]["xf"] < groups_for(k_)[0]["I"]["xf"] for k_ in ("field", "hill", "valley"))), 1, 0))
    # ---- 冒頭 0〜5秒 ----
    b0 = SC_OPEN.battle
    ar = [b0.n_arrows(t_) for t_ in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0)]
    TW = Ek("c0_b")
    ao = [b0.alive("O", t_) for t_ in (0.0, 2.5, 5.0, TW)]
    A((f"冒頭: 0秒目からもう矢が飛んでいる（0・0.5・1・1.5・2・3・4・5秒の矢の数 {ar}。どれも1本以上）", float(all(x > 0 for x in ar)), 1, 0))
    A((f"冒頭: 左（織田・野原は1体＝500人で4体）の絵の足軽が 0秒 {ao[0]}体 → 2.5秒 {ao[1]}体 → 5秒 {ao[2]}体 → 「1560年…」の文の終わり {ao[3]}体 と減り、そこまでに全滅。今川は減らない（50体のまま）",
       float(ao[0] <= 4 and ao[0] > ao[1] > ao[2] > ao[3] and ao[3] == 0 and b0.alive("I", TW) == 50 and SC_OPEN.t_end <= Sk("c0_b", 0.85)), 1, 0))
    A(("冒頭: 見本は data.json の L1 負けの見本（織田 2000→1196→531→86→0・今川 25000 から）", float([r[0] for r in _p0] == [2000, 1196, 531, 86, 0] and _p0[0][1] == 25000), 1, 0))
    # ---- 声の数字の数（冒頭40秒）----
    first40 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            first40 |= {x for x in voice_nums(tl.clip(it.id).text) if x != "1560"}
    A((f"冒頭40秒で声に出す数字は、種類で3つまで（年号の1560をのぞく。同じ数字をくり返すのは数えない）: {sorted(first40)}", float(len(first40) <= 3), 1, 0))
    # ---- 早回し・時間割 ----
    for gid in ("g1", "g2", "g3", "g4", "g7"):
        seq = [STRIP[gid][i] for i in STRIP_ORDER[gid]]
        A((f"早回し {gid}: マス目が無音の区間のうちに1万まで埋まる・帯の見本が区間に 1回以上（見本1回 {seq[0].dur:.1f}秒 ≦ 区間 {dur(gid):.1f}秒）",
           float(S(gid) + 0.5 + (dur(gid) - 0.9) <= E(gid) and seq[0].dur <= dur(gid) - 0.5), 1, 0))
    A(("3章: 勝った1回の早回しは、一斉射撃が 0.45秒以上の間隔で並び、旗が下がる時刻の 1秒以上前に終わる・旗が下がる時刻は「この回は…」の文の中・無音のあとに始まる",
       float(len(SC_WIN.times) >= 3 and all(b - a >= 0.45 for a, b in zip(SC_WIN.times, SC_WIN.times[1:])) and SC_WIN.times[-1] + 1.0 <= SC_WIN.rout
             and S(ID["c3_this"]) <= SC_WIN.rout <= E(ID["c3_this"]) and T_W0 > E("g3")), 1, 0))
    A(("6章: 次の今川5千が来る動きは最初の一斉射撃の前に終わる・一斉射撃は無音の区間のうちに終わる・本陣は「では、ほかの場所にいた今川の兵が…」の文の中で退く",
       float(SC6_T1[0] > S("g6") and SC6_T1[-1] + 2.0 <= E("g6") and S(ID["c6_all"]) <= Sk("c6_all", 0.25) <= E(ID["c6_all"])), 1, 0))
    A(("4章: 織田だけが先に放つ見本（今川は撃ち返さない回あり）の一斉射撃は、「この章では、今川が射返す前に…」の文のあとに始まり、無音の前に終わる",
       float(SC_RAIN.times[0] >= S(ID["c4_intro"]) and SC_RAIN.times[-1] + 1.5 <= S("g4") + 0.5), 1, 0))
    # ---- 字幕 ----
    worst_cps, worst_vis, worst_lines = 0.0, 1e9, 0
    for s_, e_, pause, ln, clip in tl._lines:
        vis = e_ - s_ + min(pause, lf.SUB_HOLD)
        worst_cps = max(worst_cps, len(clip.text) / vis)
        worst_vis = min(worst_vis, vis)
        worst_lines = max(worst_lines, len(lf.wrap_subtitle(clip.text)))
    A((f"字幕: 1秒あたりの字数が12字以下（最大 {worst_cps:.1f}字）", float(worst_cps <= 12), 1, 0))
    A((f"字幕: どの行も1秒以上出る（最短 {worst_vis:.1f}秒）", float(worst_vis >= 1.0), 1, 0))
    A((f"字幕: 2行以内（最大 {worst_lines}行）", float(worst_lines <= 2), 1, 0))
    # ---- 章・長さ ----
    ch = tl.chapters
    ends = [c[0] for c in ch[1:]] + [DUR]
    A(("章は9つ・最初は0秒", float(len(ch) == 9 and ch[0][0] == 0), 1, 0))
    for (t0_, title), e_ in zip(ch, ends):
        A((f"章「{title}」が10秒以上", float(e_ - t0_ >= 10), 1, 0))
    A((f"長さ {lf._mmss(DUR)}（--fake-voice の見積もり。本番の声の長さで変わる。6分〜13分）", DUR, 570.0, 210.0))
    A(("終了画面は まとめ の章の中・まとめの最後の説明（歴史の桶狭間は…）は終了画面の前に言い終わる・問いかけは終了画面のあと",
       float(T_ES > S("ch8") + 3 and Ek("c8_5") <= T_ES and T_ES < Sk("c8_q")), 1, 0))
    all_voice = " ".join(tl.clip(i).text for i in LINES)
    bad_words = ("酒宴", "豪雨", "背後から", "鉄砲", "上洛", "血", "最期", "田楽狭間の谷底")
    A((f"声に出さない言葉: {[w for w in bad_words if w in all_voice]}", float(not [w for w in bad_words if w in all_voice]), 1, 0))
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]
        screen_txt = " ".join(e[0] for _t, e in allt)
        hit_w = [w for w in bad_words if w in screen_txt]
        A((f"画面に出さない言葉: {hit_w}", float(not hit_w), 1, 0))
        bad = overlaps(frames)
        for k, t in list(bad.items())[:12]:
            print(f"  重なり: {_ts(t)} 「{k[0]}」と「{k[1]}」")
        A((f"文字どうしの重なりなし（0.5秒以上続くもの。章カードは除く）: {len(bad)}組", float(len(bad) == 0), 1, 0))
        small = {}
        for f in frames:
            for e in f[1]:
                if e[5] < 35.5:
                    small.setdefault((e[0], round(e[5])), f[0])
        for (s_, sz), t_ in list(small.items())[:12]:
            print(f"  36px未満の文字: {_ts(t_)} 「{s_}」 {sz}px")
        A((f"画面の文字（字幕を除く）は すべて 36px 以上（幅480pxに縮めても読める）: 36px未満 {len(small)}種", float(not small), 1, 0))
        br = [(f[0], e[0]) for f in frames for e in f[1] if e[3] > 1660 and e[4] > 930]
        A((f"右下（x>1660・y>930）に文字を置かない: {len(br)}件", float(not br), 1, 0))
        low = [(f[0], e[0]) for f in frames for e in f[1] if e[4] > 938]
        for t, s_ in low[:5]:
            print(f"  字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        A((f"字幕の帯（y>938）に絵の文字を入れない: {len(low)}件", float(not low), 1, 0))
        stray = [(f[0], e[0]) for f in frames for e in f[1] if f[0] < T_ES and e[0] not in OVERLAY_OK and (945 < e[3] and e[1] < 1030)]
        for t, s_ in stray[:5]:
            print(f"  のどにかかる文字: {_ts(t)} 「{s_}」")
        A((f"見開きののど（x 945〜1030）に文字をまたがせない: {len(stray)}件", float(not stray), 1, 0))
        out_ = [(f[0], e[0]) for f in frames for e in f[1] if f[0] < T_ES and e[0] not in OVERLAY_OK and (e[1] < 40 or e[3] > 1880)]
        A((f"文字はページの左右の端（x<40・x>1880）にかからない: {len(out_)}件", float(not out_), 1, 0))
        f0 = frames[0]
        n0 = {e[0] for e in f0[1]}
        A(("0.0秒目: 題字「桶狭間」・右ページの問い（サムネと同じ言葉）・「勝率」の枠が出ている",
           float({"桶狭間", "もう一度", "戦ったら、", "2千人は勝てる？", "勝率"} <= n0 and "".join(QLINES) == "もう一度戦ったら、2千人は勝てる？"), 1, 0))
        T05 = [f for f in frames if f[0] <= 5.0]
        A(("0〜5秒: 絵の足軽（織田・今川）が描かれ続け（織田1体以上・今川45体以上）、棒が「？%」の形で数字を伏せている",
           float(all(sum(1 for p in f[2] if p[0] == "main" and p[5] == "I" and not p[4]) >= 45 for f in T05)
                 and all(sum(1 for p in f[2] if p[0] == "main" and p[5] == "O" and not p[4]) >= 1 for f in T05)
                 and any("？%" in e[0] for f in T05 for e in f[1])), 1, 0))
        pre = [(f[0], e[0]) for f in frames if f[0] < Sk("c0_d", 0.3) - 0.1 for e in f[1] if _re.search(r"\d+(\.\d+)?\s*%", e[0])]
        A((f"冒頭の棒は、勝率の数字を出さない（「勝率の棒が5本並ぶ枠」が出るまで%の数字なし）: {pre[:2]}", float(not pre), 1, 0))
        u4 = ease(clamp01(4.0 / 4.0)) * VAL["L4"]
        A((f"冒頭の棒は 0% から伸びて、4秒ごろには少し伸びたところで止まる（長さ {u4 * 100:.1f}% ぶん・0より大きく10%未満）", float(0 < u4 < 0.10 and ease(clamp01(0.0)) == 0.0), 1, 0))
        small_p, n_main = 0, 0
        for f in frames:
            for p in f[2]:
                if p[0] == "main" and p[5] in ("O", "I") and not p[4]:
                    n_main += 1
                    if 104.0 * p[3] < 50.0:
                        small_p += 1
        A((f"絵: 主役の足軽（早回しの帯をのぞく・延べ{n_main}体）の背の高さは 50px 以上（今川全軍の遠い列でも）: 小さい足軽 {small_p}", float(small_p == 0 and n_main > 0), 1, 0))
        f_r = _near(frames, SC_WIN.rout + 1.3)
        poles = [p for p in f_r[2] if p[0] == "main" and p[5] == "pole"]
        A((f"3章の勝った1回: 本陣の旗が下がっている（旗を倒す角度 {max([p[3] for p in poles] or [0]):.2f}rad ＞ 1.0）", float(len(poles) >= 1 and max(p[3] for p in poles) > 1.0), 1, 0))
        f_a = _near(frames, SC_WIN.rout + 6.5)
        alive_i = [p for p in f_a[2] if p[0] == "main" and p[5] == "I" and not p[4]]
        dead_i = [p for p in f_a[2] if p[0] == "main" and p[5] == "I" and p[4]]
        A((f"3章の勝った1回: 本陣が右へ退いたあと、生きている今川の絵は左ページに残らない（{len(alive_i)}体）・倒れた兵は {len(dead_i)}体（見本の本陣 5000→{SMP['L3_win']['traj'][-1][1]:,} ＝ 20→{figs(SMP['L3_win']['traj'][-1][1])}体）",
           float(len(alive_i) == 0 and len(dead_i) == 20 - figs(SMP["L3_win"]["traj"][-1][1])), 1, 0))
        f_b = _near(frames, SC_WIN.rout - 0.3)
        A(("3章の勝った1回: 退く前の絵に、織田の足軽がいる・今川の本陣の足軽が18体以上いる・旗が立っている",
           float(sum(1 for p in f_b[2] if p[0] == "main" and p[5] == "O" and not p[4]) >= 1 and sum(1 for p in f_b[2] if p[0] == "main" and p[5] == "I" and not p[4]) >= 18
                 and any(p[5] == "pole" and p[3] < 0.2 for p in f_b[2])), 1, 0))
        tokens = []
        for k_, nt in LINE_NOTE.items():
            for tk in _re.findall(r"「([^」]*)」", nt):
                tokens.append((k_, tk))
        shown = {e[0] for _t, e in allt}
        miss = sorted({tk for _k, tk in tokens if tk not in shown})
        A((f"台本の画面の指示〔 〕の「 」の言葉 {len(tokens)}個（{len(set(t_ for _k, t_ in tokens))}種）が、すべて画面に文字として出る: 出ていない {miss}", float(not miss), 1, 0))
        late = []
        for k_, tk in tokens:
            ts = [t_ for t_, e in allt if e[0] == tk]
            if ts and not (min(ts) <= E(k_) + 3.0):
                late.append((k_, tk, round(min(ts), 1)))
        A((f"台本の〔 〕の言葉は、その文が終わって3秒以内には画面に出ている（棒の名札は章の頭から先に出る）: 遅れ {late}", float(not late), 1, 0))
        ok_nums = _allowed_nums()
        extra = {}
        for t_, e in allt:
            if e[0] in OVERLAY_OK:
                continue
            for m in _re.findall(r"\d[\d,]*(?:\.\d+)?", e[0]):
                v = float(m.replace(",", ""))
                if v not in ok_nums:
                    extra.setdefault(v, e[0])
        for v, s_ in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」")
        A((f"画面に出る数字は、すべて data.json の値（の四捨五入・見本の人数）か、目盛りなどの閉じた値: 余分 {len(extra)}個", float(not extra), 1, 0))
        pct = {m for _t, e in allt for m in _re.findall(r"\d+(?:\.\d+)?%", e[0])}
        okp = ({f"{ihalf(st['rate'] * 100)}%" for st in list(LAD.values()) + list(L5.values()) + list(L6.values()) + list(L7.values())}
               | {"0.3%", "0%", "100%", "50%", f"{ihalf(r3 * 100)}%", f"{lo7}%", f"{hi7}%", f"{hi5}%"})
        A((f"画面に出る「N%」は、すべて data.json から作った値: 余分 {sorted(pct - okp)}", float(not (pct - okp)), 1, 0))

        def seen(tok, t_a, t_b):
            return any(e[0] == tok for t_, e in allt if t_a <= t_ <= t_b)
        A(("0章: 織田・今川の札・「1万回」の付せん・「今川 2万5千」「織田 2千」「諸説あり」・絵の足軽の凡例（1人＝500人）が出る",
           float(all(seen(x, 0, S("ch1")) for x in ("織田", "今川", "1万回", "今川 2万5千", "織田 2千", "諸説あり", "絵の足軽1人＝500人"))), 1, 0))
        A(("1章: 付せん「1人あたり 156倍強く」「弓だけ」「25本に1本」「強さの差 約156倍」・棒1「野原・全軍」0%・マス目のしくみ・2倍→4倍の図の文字（兵の数 2倍・矢の数 2倍・強さ 4倍）が出る",
           float(all(seen(x, S("ch1"), S("ch2")) for x in ("1人あたり 156倍強く", "弓だけ", "25本に1本", "強さの差 約156倍", "野原・全軍", "0%", "兵の数 2倍", "矢の数 2倍", "強さ 4倍", GRID_CAP))), 1, 0))
        A(("2章: 配置図の名札（砦を攻める兵・城を守る兵・後ろに控える兵・本陣・織田）・付せん「本陣 5千」・棒2「＋本陣だけ」0%が出る",
           float(all(seen(x, S("ch2"), S("ch3")) for x in ("砦を攻める兵", "城を守る兵", "後ろに控える兵", "本陣", "織田", "本陣 5千", "＋本陣だけ", "0%"))), 1, 0))
        A(("3章: 付せん「最後の1人まで」「信長公記」・目盛り（両はし「1割」「5割」）・棒3「＋崩れ」0.3%・勝った回の人数の表示（織田 ◯人・本陣 ◯人）が出る",
           float(all(seen(x, S("ch3"), S("ch4")) for x in ("最後の1人まで", "信長公記", "1割", "5割", "＋崩れ", "0.3%"))
                 and any(e[0].startswith("織田 ") and e[0].endswith("人") for t_, e in allt if S("ch3") <= t_ < S("ch4"))
                 and any(e[0].startswith("本陣 ") and e[0].endswith("人") for t_, e in allt if S("ch3") <= t_ < S("ch4"))), 1, 0))
        A(("4章: 雨の線・付せん「先に放てる 0〜3回」・棒4「＋雨」6%・100回のうち6回の図が出る",
           float(all(seen(x, S("ch4"), S("ch5")) for x in ("先に放てる 0〜3回", "＋雨", "6%")) and any(e[0].startswith("100回のうち") for t_, e in allt if S("ch4") <= t_ < S("ch5"))), 1, 0))
        A(("5章: 右の表は3行（基本（＋雨まで）6%・いちばん勝てる 42%・崩れにくい本陣 0%）・左は台詞に合わせて変わる1つの絵（本陣5千→6千→4千・織田2千→3千）と崩れる所の目盛り・帯「0%〜42%」が出る",
           float(all(seen(x, S("ch5"), S("ch6")) for x in ("基本（＋雨まで）", "いちばん勝てる", "崩れにくい本陣", "6%", "42%", "0%", "本陣 5千", "本陣 6千", "本陣 4千", "織田 2千", "織田 3千", "基本 1割〜5割", "2割〜5割", "0%〜42%"))), 1, 0))
        big156 = [e[5] for t_, e in allt if e[0] == "1人あたり 156倍強く"]
        A((f"1章の先頭の文（先に言います…）: 付せん「1人あたり 156倍強く」が 60px 以上で出る・その文が始まる時刻 {S(ID['c1_first']):.1f}秒（60秒以内）・声は「156倍強く」",
           float(bool(big156) and min(big156) >= 59.5 and S(ID["c1_first"]) <= 60.0 and has("c1_first", "156倍強く")), 1, 0))
        leg = [e[5] for _t, e in allt if e[0].startswith("絵の足軽1人＝")]
        gcap = [e[5] for _t, e in allt if e[0] == GRID_CAP]
        sc3 = [e[5] for t_, e in allt if S("ch3") <= t_ < S("ch4") and e[0] in ("1割", "5割", "1割〜5割", "ここまでしか倒せない")]
        sc5 = [e[5] for t_, e in allt if S("ch5") <= t_ < S("ch6") and not (e[0].startswith("決め方") or e[0] in ("勝率",))]
        A((f"文字の大きさ: 凡例「絵の足軽1人＝◯人」{min(leg):.0f}px（30px以上）・マス目の読み方 {min(gcap):.0f}px・3章の目盛りの文字 {min(sc3):.0f}px・5章の文字 {min(sc5):.0f}px（どれも40px以上）",
           float(min(leg) >= 39.5 and min(gcap) >= 39.5 and min(sc3) >= 39.5 and min(sc5) >= 39.5), 1, 0))
        A(("6章: 5千人ずつの組の箱が4つ・棒「全部に勝つ」0%・付せんが出る",
           float(all(seen(x, S("ch6"), S("ch7")) for x in ("全部に勝つ", "0%", "次々に来る今川（5千人ずつ）"))
                 and max(sum(1 for e in f[1] if e[0] == "5千") for f in frames if S("ch6") <= f[0] < S("ch7")) == 4), 1, 0))
        A(("7章: 谷の絵に「江戸時代の話」と添え書き・付せん「信長公記: おけはさま山」・谷の幅の目盛り（50・100・200）・棒「江戸時代の谷」73%・帯「45%〜100%」・2本の棒（73%・6%）が出る",
           float(all(seen(x, S("ch7"), S("ch8")) for x in ("江戸時代の話", "（史実ではないという見方が多い話）", "信長公記: おけはさま山", "50", "100", "200", "江戸時代の谷", "73%", "45%〜100%", "6%", "記録に近い"))), 1, 0))
        f8 = _near(frames, T_ES - 0.3)
        n8 = {e[0] for e in f8[1]}
        A(("8章（まとめ）: 勝率の棒が並ぶ（野原・全軍 0% → 本陣だけ 0% → 崩れ 0.3% → 雨 6% ／ 江戸時代の谷 73%）",
           float({"野原・全軍", "＋本陣だけ", "＋崩れ", "＋雨", "江戸時代の谷", "0%", "0.3%", "6%", "73%"} <= n8), 1, 0))
        A(("棒の長さ（枠の幅を 100% として）＝ data.json の勝率（0・0・0.34%・6.27%・72.72%）",
           float(abs(VAL["L3"] - 34 / 10000) < 1e-12 and abs(VAL["L4"] - 627 / 10000) < 1e-12 and abs(VAL["L7"] - 7272 / 10000) < 1e-12 and VAL["L1"] == 0 and VAL["L2"] == 0), 1, 0))
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936]
        for t, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        A((f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", float(not out_es), 1, 0))
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A((f"終了画面の文字は すべて 38px 以上: {es_small}", float(not es_small), 1, 0))
        es_ans = {e[0]: e[5] for f in frames if f[0] >= T_ES + 1.0 for e in f[1] if e[0] in ("勝ち目は ない", "100回に6回", "多くの場合 織田は負ける")}
        A((f"終了画面の答えの付せん（左ページ）の答えの文字は 60px 以上: {es_ans}", float(len(es_ans) == 3 and min(es_ans.values()) >= 59.5), 1, 0))
        es_last = [e for f in frames if f[0] >= S(ID["c8_ch"]) + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        A(("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", float(len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5), 1, 0))
        q_ = {e[0] for f in frames if f[0] >= Sk("c8_q", 0.3) for e in f[1]}
        A(("終了画面の問いかけ（あなたなら、勝ち目を上げるために、もう1つ何を足しますか？）が出る", float({"あなたなら、", "勝ち目を上げるために、", "もう1つ何を足しますか？"} <= q_), 1, 0))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--readings" in args:
        write_readings((WORK if FAKE else OUT) / "readings.log")
        return
    if "--wraps" in args:
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        return
    if "--scenecheck" in args:
        frames = scan()
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, WORK / f"at_{tt:06.1f}.png")
                print("  ", WORK / f"at_{tt:06.1f}.png")
        else:
            stills_preview(OUT / "stills_preview")
        return
    if "--preview" in args:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
        return
    if "--docs" in args:
        d = WORK if FAKE else OUT
        write_transcript(d / "transcript.long.txt")
        write_readings(d / "readings.log")
        (d / "chapters.txt").write_text(tl.chapter_text() + "\n", encoding="utf-8")
        print("チャプター:", d / "chapters.txt")
        return
    if FAKE:
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    # ---- 本番 ----
    frames = scan()
    scene_checks(frames)
    write_screen_text(OUT / "screen_text.txt", frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
