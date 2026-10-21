"""エスカレーター、片側あけが得になるのは歩く人が何割のとき？（横型ロング）— 2026-10-13 作成（モデル部分のみ。描画・場面は後で足す）

構成案: research/escalator_long_storyboard.md ／ 元のショート: sims/escalator-2retsu.py（触らない。make_trial・enter・exit_times・metrics・timestep は
そこからコピーした。ショートの乱数と同じ流れなので、同じ種ならショートと同じ数字になる）

問い: 片側あけが得になるのは、歩く人が何割のとき？
  （ショートの答え: 電車1本ならほぼ同じ・電車が続くと片側あけが不利 → では、何割なら片側あけが得か）

モデル（上から見た1基。幅は2人が並べる＝左右2列。人は1列にならんで乗る）
  エスカレーター : 秒速0.5m（斜面に沿った速さ）。勾配30度。高さ17.5m・斜面35m → 立って乗ると 35÷0.5 = 70秒（高さ方向の速さは 0.25m/秒）。
                   コードの HEIGHT=17.5 は「高さ」で、斜面の長さ L = 高さ×2。高さを変える章（4章）は L = 2×高さ。踏段1段の奥行き 0.4m。
                   階段との比較（5章）は高さ同士: 階段は高さ方向の速さ 0.2 / 0.25 m/秒 → 17.5m で 87.5 / 70秒（立って乗る 70秒＝高さ方向0.25m/秒と同じ）。
  人             : 電車1本100人。20〜50秒かけて少しずつ下に着く。着いた順に列に並び、前の人が乗れる間隔をあけたら乗る。
  立つ人         : エスカレーターと同じ速さ（斜面に沿って秒速0.5m）。「2段に1人」（1段あける＝前の人との間隔2段分＝0.8m）が基準。
                   1人ごとに 1〜3段に1人（平均2.0段に1人）。
  歩く人         : エスカレーターの上でさらに斜面に沿って秒速0.5m（平均。標準偏差0.1）→ 地面から見て約1.0m/s。間隔は 平均2.8段に1人（1.12m。標準偏差0.4段）。
                   資料（立つ人は2段に1人・歩く人は3段に1人）に対して、立つ人は同じ、歩く人は 2.8 と 3 で少し詰めてある（値はショートのまま。ずれは numbers.md に書いた）。
                   歩く列では前の人を追い越せない（速い人は前の人の速さまで落ちる）。
  片側あける     : 立つ人は立つ列だけ、歩く人は歩く列だけを使う（片方の列を歩く人のために空けておく）。
  2列で立つ      : 全員が立つ。空いたほうの列に乗る。
  歩く人の割合   : ショートはその回ごとに平均25%（Beta）でゆらしていた。このロングは割合そのものを動かす章が多いので、
                   各人が確率 p で「歩きたい人」になる形に固定する（同じ種なら p を上げると歩く人が増えるだけ＝入れ子。曲線がなめらかに出る）。
                   ただし 0章の再現と5章（階段）は、ショートと同じ Beta のゆらぎ（make_trial の walker）のまま使う。
  指標           : 1人あたりの平均（列に着いてから上り終えるまで。下の行列で待つ時間を含む）。ショートv2と同じ。
  混雑（ラッシュ）: 電車が 100秒おきに100人ずつ、15本（1,500人）。各電車は別々の乱数で作って到着時刻に k×100 を足してつなぐ。
                   平均は1,500人ぶん（ショートの 206秒｜100秒 と同じ数え方）。「十分な本数」は numbers.md の 40本の試算で確かめた。

章ごとに出す数字（out/escalator-long/numbers.md、data.json）
  1章: 歩く人の割合 0〜50%（5%刻み）で「片側あけ − 2列」の平均秒（電車1本・17.5m）と、互角の割合（0を横切る所）
  2章: 朝の混雑（100秒おき）の同じ曲線と互角の割合、20/30/40%の秒。電車の間隔 90/120秒の互角（閉じた式との照合）
  2章（なぜ）: 運べる量（立つ列・歩く列・2列）。閉じた式「速さ÷間隔」とシミュの実測（十分長い行列の流出率）
  3章: 歩く列の2人目だけ上乗せ秒速0.1m（割合25%）で、歩く人の平均・全体の平均 vs 2列
  4章: 高さ 3, 10, 17.5, 25, 40m の互角の割合（電車1本）
  5章: 階段（高さ方向 秒速0.2m と 0.25m）で「前に何人いたら階段が早いか」と、電車1本100人で階段が早い人の割合

使い方（モデル）
  python -X utf8 sims/escalator-long.py --compute    計算だけ（--force でやり直し。--only=capacity,pile のように絞れる）
  python -X utf8 sims/escalator-long.py --check      照合だけ
  python -X utf8 sims/escalator-long.py --numbers    照合 → 数字の書き出し（numbers.md・data.json）
使い方（場面。2026-10-13 追加。引数なしで動画を書き出す。詳しくはファイル後半の「場面」の頭）
  python -X utf8 sims/escalator-long.py              照合 → 場面の照合 → mp4・chapters.txt・transcript.long.txt・readings.log・stills/
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers

SLUG = "escalator-long"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
CACHE = OUT / "cache"
SHORT_OUT = Path(__file__).resolve().parents[1] / "out" / "escalator-2retsu"   # ショートの1万回の結果（読むだけ）

# ============================================================
# モデルの値（ショート sims/escalator-2retsu.py と同じ）
# ============================================================
VE = 0.5                                          # エスカレーターの速さ（m/s）
PITCH = 0.4                                       # 踏段1段の奥行き（m）
HEIGHT = 17.5                                     # 高さ（m）。傾斜30度なので長さ = 2 × 高さ
L_BASE = 2 * HEIGHT                               # 35m
N = 100                                           # 1回に着く人数
P_MEAN, P_SD = 0.25, 0.07                         # （ショートの）歩きたい人の割合: 平均・標準偏差
BETA_A = P_MEAN * (P_MEAN * (1 - P_MEAN) / P_SD ** 2 - 1)
BETA_B = (1 - P_MEAN) * (P_MEAN * (1 - P_MEAN) / P_SD ** 2 - 1)
W_LO, W_HI = 20.0, 50.0                           # 100人が着き終わるまでの時間の範囲（秒）
GS_MEAN, GS_SD = 2.0, 0.15                        # 立つ人の間隔（「◯段に1人」の◯）: その回の平均
GW_MEAN, GW_SD = 2.8, 0.2                         # 歩く人の間隔（「◯段に1人」の◯）: その回の平均（資料は3）
WALK_REL, WALK_SD = 0.5, 0.1                      # 歩く人の上乗せの速さ（m/s）
N_TRAIN = 15                                      # 混雑の電車の本数
T_RUSH = 100.0                                    # 電車の間隔（秒）
N_TRIALS = 10000
AGAIN = 500000                                    # 「別の乱数でやり直し」の種の始まり

# ここから先は、このロングで足した値
HEIGHTS_LONG = [3.0, 10.0, 17.5, 25.0, 40.0]      # 4章
Ls_LONG = [2 * h for h in HEIGHTS_LONG]
SLOW_W = 0.1                                      # 3章: 歩く列の2人目の上乗せ速さ（m/s）
SLOW_P = 0.25                                     # 3章: 歩く人の割合
STAIR_VS = [0.2, 0.25]                            # 5章: 階段を上る速さ（高さ方向 m/s）
P_GRID = [round(float(x), 2) for x in np.arange(0, 0.5001, 0.01)]        # 1・4章の割合の刻み（1%）
P_TABLE = [round(float(x), 2) for x in np.arange(0, 0.5001, 0.05)]       # 表に出す刻み（5%）
P_RUSH = sorted({round(float(x), 2) for x in list(np.arange(0, 0.5001, 0.05)) + list(np.arange(0.30, 0.5001, 0.01))})
P_RUSH_AGAIN = [0.2, 0.3, 0.35, 0.37, 0.38, 0.39, 0.4, 0.45]
P_RUSH_T = [round(float(x), 2) for x in np.arange(0.20, 0.5001, 0.02)]   # 電車の間隔 90/120秒
TR_RUSH_T = 10000                                 # 電車の間隔 90/120秒の試行数
N_RUSH_LONG, P_RUSH_LONG, TR_RUSH_LONG = 40, [0.2, 0.3, 0.35, 0.4], 2000
SENS_N, SENS_N_RUSH = 4000, 2000                  # 歩く人の間隔を資料の値（3段に1人）にした感度: 試行数
P_SENS = [round(float(x), 2) for x in np.arange(0.15, 0.4001, 0.01)]
P_SENS_RUSH = [round(float(x), 2) for x in np.arange(0.34, 0.4601, 0.01)]
PILE_N = 1500                                     # 運べる量の測定: 同時に着く人数


# ============================================================
# ショートのモデル（sims/escalator-2retsu.py からコピー。make_trial だけ人数 n と歩く人の間隔の平均 gw_mean を引数にした。既定値なら乱数の流れは同じ）
# ============================================================
def make_trial(seed, n=N, gw_mean=GW_MEAN):
    r = np.random.default_rng(seed)
    p = r.beta(BETA_A, BETA_B)
    Wd = r.uniform(W_LO, W_HI)
    a = np.sort(Wd * r.beta(2, 3, n))
    a -= a[0]
    walker = r.random(n) < p
    ms = float(np.clip(r.normal(GS_MEAN, GS_SD), 1.6, 2.4))
    gs = (1 + r.binomial(2, (ms - 1) / 2, n)) * PITCH
    mw = float(np.clip(r.normal(gw_mean, GW_SD), gw_mean - 0.6, gw_mean + 0.6))   # gw_mean=2.8 ならショートと同じ（2.2〜3.4）
    gw = np.clip(r.normal(mw, 0.4, n), 1.5, 4.5) * PITCH
    w = np.clip(r.normal(WALK_REL, WALK_SD, n), 0.25, 0.8)
    return dict(a=a, walker=walker, gs=gs, gw=gw, w=w, p=p, W=Wd)


def enter(tr, mode):
    """全員が列に乗る時刻 e、地面から見た速さ s、乗る列（0=上の列, 1=下の列）、立つか。
    mode 'A'=片側あける（立つ列＝0、歩く列＝1）、'B'=2列で立つ"""
    a, walker = tr["a"], tr["walker"]
    n = len(a)
    lane = np.zeros(n, int)
    e = np.zeros(n)
    s = np.full(n, VE)
    if mode == "B":
        last = [None, None]
        prev_e = 0.0                                  # 行列は順番どおり（前の人より先には乗れない）
        for i in range(n):
            cand = [max(prev_e, a[i] if last[l] is None else max(a[i], e[last[l]] + tr["gs"][i] / VE)) for l in (0, 1)]
            l = 0 if cand[0] <= cand[1] else 1
            lane[i], e[i], last[l] = l, cand[l], i
            prev_e = e[i]
        return dict(lane=lane, e=e, s=s, stand=np.ones(n, bool), C=None, idx_w=np.array([], int))
    last = None
    for i in range(n):
        if not walker[i]:
            e[i] = a[i] if last is None else max(a[i], e[last] + tr["gs"][i] / VE)
            last = i
    idx = np.where(walker)[0]
    lane[idx] = 1
    s[idx] = VE + tr["w"][idx]
    sw = s[idx]
    C = np.cumsum(tr["gw"][idx])                       # C[m] = m番目の人までの間隔の合計
    ew = np.zeros(len(idx))
    for m, i in enumerate(idx):
        t = a[i]
        if m > 0:
            k = np.arange(m)
            # 前の人たちの線 s_k (t − e_k) − (C[m−1] − C[k]) が、自分との間隔 g 以上になる時刻
            t = max(t, float((ew[k] + (tr["gw"][i] + C[m - 1] - C[k]) / sw[k]).max()))
        ew[m] = t
    e[idx] = ew
    return dict(lane=lane, e=e, s=s, stand=~walker, C=C, idx_w=idx)


def exit_times(res, Ls):
    """各長さで、全員が上の端に着く時刻（len(Ls) × n）。
    歩く列の位置: x_m(t) = min_k≤m [ s_k (t − e_k) − (C_m − C_k) ]（前の人に間隔 g より近づけない。追い越せない）"""
    Ls = np.atleast_1d(np.asarray(Ls, float))
    n = len(res["e"])
    out = np.zeros((len(Ls), n))
    st = res["stand"]
    out[:, st] = res["e"][st][None, :] + Ls[:, None] / VE
    idx = res["idx_w"]
    if len(idx):
        ew, sw, C = res["e"][idx], res["s"][idx], res["C"]
        for m in range(len(idx)):
            k = np.arange(m + 1)
            t = ew[k][None, :] + (Ls[:, None] + C[m] - C[k][None, :]) / sw[k][None, :]
            out[:, idx[m]] = t.max(1)
    return out


def metrics(tr, mode, Ls):
    res = enter(tr, mode)
    ex = exit_times(res, Ls)
    dur = ex - tr["a"][None, :]
    wk = tr["walker"]
    return dict(make=ex.max(1), mean=dur.mean(1),
                mean_w=dur[:, wk].mean(1) if wk.any() else np.full(len(ex), np.nan),
                mean_s=dur[:, ~wk].mean(1), res=res, ex=ex)


def timestep(tr, mode, L, dt=0.02):
    """全員が上り終える時刻。1人ずつ 0.02秒ごとに動かす別の実装（式を使わない）。（ショートからコピー）
    乗る条件: 先に乗った人が g（自分の間隔）以上進んだら。動き: 自分の速さ、ただし前の人から g より近づかない"""
    n = len(tr["a"])
    a, walker = tr["a"], tr["walker"]
    if mode == "B":
        queues = [list(range(n))]
        qlanes = [[0, 1]]
    else:
        queues = [[i for i in range(n) if not walker[i]], [i for i in range(n) if walker[i]]]
        qlanes = [[0], [1]]
    lanes = [[], []]                                   # 各列: [[人, 位置], ...] 前の人が先頭
    t, done, last_exit = 0.0, 0, 0.0
    total = n
    while done < total and t < 2000:
        for ln in lanes:
            prev = None
            for p in ln:
                i = p[0]
                sp = VE if (mode == "B" or not walker[i]) else VE + tr["w"][i]
                nx = p[1] + sp * dt
                if prev is not None:
                    gap = tr["gs"][i] if (mode == "B" or not walker[i]) else tr["gw"][i]
                    nx = min(nx, prev[1] - gap)
                p[1] = nx
                prev = p
        for ln in lanes:
            while ln and ln[0][1] >= L:
                ln.pop(0)
                done += 1
                last_exit = t
        for q, ls in zip(queues, qlanes):
            if not q or a[q[0]] > t:
                continue
            i = q[0]
            gap = tr["gs"][i] if (mode == "B" or not walker[i]) else tr["gw"][i]
            ok = [l for l in ls if (not lanes[l]) or lanes[l][-1][1] >= gap]
            if ok:
                l = max(ok, key=lambda l: lanes[l][-1][1] if lanes[l] else 1e9)
                lanes[l].append([i, 0.0])
                q.pop(0)
        t += dt
    return last_exit


# ============================================================
# 割合を固定する部品（このロングで足した）
# ============================================================
def fixed_walker(seed, p, n=N):
    """各人が確率 p で歩きたい人。同じ種なら p を上げると歩く人が増えるだけ（入れ子）"""
    return np.random.default_rng(seed + 777).random(n) < p


def with_p(tr, seed, p):
    return dict(tr, walker=fixed_walker(seed, p))


def rush_trial(seed, T, p=None, ntrain=N_TRAIN):
    """電車が T 秒おきに100人ずつ ntrain 本。p=None ならショートと同じ（make_trial の walker）"""
    trs = [make_trial(seed * 20 + k) for k in range(ntrain)]
    if p is not None:
        for k, t in enumerate(trs):
            t["walker"] = fixed_walker(seed * 20 + k, p)
    tr = {k: np.concatenate([t[k] for t in trs]) for k in ("walker", "gs", "gw", "w")}
    tr["a"] = np.concatenate([t["a"] + k * T for k, t in enumerate(trs)])
    return tr


# ============================================================
# 並列で回す部品
# ============================================================
def _workers():
    return max(1, min(14, (os.cpu_count() or 4) - 2))


def _pmap(fn, jobs):
    with ProcessPoolExecutor(max_workers=_workers()) as ex:
        return list(ex.map(fn, jobs))


def _chunks(seed0, n, chunk):
    return [np.arange(seed0 + i, seed0 + min(n, i + chunk)) for i in range(0, n, chunk)]


# ---- 1・4章: 割合 p を動かす（電車1本。長さは複数まとめて） ----
def _share_chunk(args):
    seeds, ps, Ls = args[:3]
    gwm = args[3] if len(args) > 3 else GW_MEAN
    iL = list(Ls).index(L_BASE) if L_BASE in Ls else 0
    S, nP, nL = len(seeds), len(ps), len(Ls)
    A = np.zeros((S, nP, nL), np.float32)
    B = np.zeros((S, nL), np.float32)
    Aw = np.full((S, nP), np.nan, np.float32)          # 歩く人だけの平均（長さ L_BASE）
    As = np.full((S, nP), np.nan, np.float32)          # 立つ人だけの平均（長さ L_BASE、片側あけ）
    nw = np.zeros((S, nP), np.int16)
    for si, sd in enumerate(seeds):
        tr = make_trial(int(sd), N, gwm)
        a = tr["a"]
        B[si] = (exit_times(enter(tr, "B"), Ls) - a).mean(1)      # 2列は割合に関係しない
        u = np.random.default_rng(int(sd) + 777).random(N)
        for pi, p in enumerate(ps):
            t2 = dict(tr, walker=u < p)
            dur = exit_times(enter(t2, "A"), Ls) - a
            wk = t2["walker"]
            A[si, pi] = dur.mean(1)
            nw[si, pi] = wk.sum()
            if wk.any():
                Aw[si, pi] = dur[iL, wk].mean()
            if (~wk).any():
                As[si, pi] = dur[iL, ~wk].mean()
    return A, B, Aw, As, nw


def run_share(seed0, n=N_TRIALS, ps=P_GRID, Ls=Ls_LONG, chunk=250, gw_mean=GW_MEAN):
    parts = _pmap(_share_chunk, [(s, ps, Ls, gw_mean) for s in _chunks(seed0, n, chunk)])
    return [np.concatenate([p[i] for p in parts]) for i in range(5)]


# ---- 2章: 混雑 ----
def _rush_chunk(args):
    seeds, ps, T, ntrain = args[:4]                    # ps の要素 None = ショートと同じ（Beta）の歩きたい人
    gwm = args[4] if len(args) > 4 else GW_MEAN
    S, nP = len(seeds), len(ps)
    A = np.zeros((S, nP, ntrain), np.float32)          # 電車ごとの1人あたり平均
    B = np.zeros((S, ntrain), np.float32)
    for si, sd in enumerate(seeds):
        sd = int(sd)
        trs = [make_trial(sd * 20 + k, N, gwm) for k in range(ntrain)]
        us = [np.random.default_rng(sd * 20 + k + 777).random(N) for k in range(ntrain)]
        base = {k: np.concatenate([t[k] for t in trs]) for k in ("walker", "gs", "gw", "w")}
        base["a"] = np.concatenate([t["a"] + k * T for k, t in enumerate(trs)])
        dB = exit_times(enter(base, "B"), L_BASE)[0] - base["a"]
        B[si] = dB.reshape(ntrain, N).mean(1)
        for pi, p in enumerate(ps):
            tr = dict(base)
            if p is not None:
                tr["walker"] = np.concatenate([u < p for u in us])
            dA = exit_times(enter(tr, "A"), L_BASE)[0] - tr["a"]
            A[si, pi] = dA.reshape(ntrain, N).mean(1)
    return A, B


def run_rush(seed0, n, ps, T=T_RUSH, ntrain=N_TRAIN, chunk=50, gw_mean=GW_MEAN):
    parts = _pmap(_rush_chunk, [(s, ps, T, ntrain, gw_mean) for s in _chunks(seed0, n, chunk)])
    return np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])


# ---- 3章: 歩く列の2人目だけゆっくり ----
def _slow_chunk(args):
    seeds, p, wslow, wall = args
    rows = []
    for sd in seeds:
        sd = int(sd)
        tr = with_p(make_trial(sd), sd, p)
        mB = metrics(tr, "B", L_BASE)
        mA = metrics(tr, "A", L_BASE)
        idx = np.where(tr["walker"])[0]
        t2 = dict(tr, w=tr["w"].copy())
        t2["w"][idx[1]] = wslow                        # 歩く列の2人目だけ
        mS = metrics(t2, "A", L_BASE)
        t3 = dict(tr, w=np.clip(np.random.default_rng(sd + 99).normal(wall, 0.1 * wall / 0.5, N), 0.03, 1.2))
        mW = metrics(t3, "A", L_BASE)                  # 参考: 歩く人ぜんぶの上乗せを wall にする
        rows.append([float(mA["mean"][0]), float(mA["mean_w"][0]), float(mA["mean_s"][0]),
                     float(mS["mean"][0]), float(mS["mean_w"][0]), float(mS["mean_s"][0]),
                     float(mB["mean"][0]), float(mW["mean"][0]), float(mW["mean_w"][0]), float(len(idx))])
    return np.array(rows)


def run_slow(seed0, n=N_TRIALS, chunk=250, p=SLOW_P, wslow=SLOW_W, wall=0.2):
    return np.concatenate(_pmap(_slow_chunk, [(s, p, wslow, wall) for s in _chunks(seed0, n, chunk)]))


# ---- 5章: 階段 ----
def stair_time(vs, H=HEIGHT):
    return H / vs


def _stairs_chunk(args):
    seeds, vss = args
    rows = []
    for sd in seeds:
        tr = make_trial(int(sd))
        row = []
        for mode in ("A", "B"):
            m = metrics(tr, mode, L_BASE)
            dur = m["ex"][0] - tr["a"]
            for vs in vss:
                faster = dur > stair_time(vs) + 1e-9
                row += [float(faster.sum()), float((faster & ~tr["walker"]).sum())]
        rows.append(row + [float(tr["walker"].sum())])
    return np.array(rows)                               # 列: [A:vs1 全員,立つ人, A:vs2 全員,立つ人, B:vs1 全員,立つ人, B:vs2 ..., 歩く人数]


def run_stairs(seed0, n=N_TRIALS, chunk=250, vss=STAIR_VS):
    return np.concatenate(_pmap(_stairs_chunk, [(s, vss) for s in _chunks(seed0, n, chunk)]))


def _pile_threshold_chunk(args):
    """100人が同時に着いた行列で、前に j 人いる人の「並んで乗って上り終えるまで」が階段より長くなる最初の j"""
    seeds, vss = args
    rows = []
    for sd in seeds:
        tr = make_trial(int(sd))
        tr["a"] = np.zeros(N)
        tr["walker"] = np.zeros(N, bool)
        row = []
        for mode in ("B", "A"):                         # 2列 / 片側あけの立つ列
            dur = exit_times(enter(tr, mode), L_BASE)[0]
            for vs in vss:
                over = np.where(dur > stair_time(vs) + 1e-9)[0]
                row.append(float(over[0]) if len(over) else float("nan"))
        rows.append(row)
    return np.array(rows)                               # 列: [2列:vs1, 2列:vs2, 立つ列:vs1, 立つ列:vs2]


def run_pile_threshold(n=400, vss=STAIR_VS):
    return np.concatenate(_pmap(_pile_threshold_chunk, [(s, vss) for s in _chunks(900000, n, 100)]))


# ---- 2章（なぜ）: 運べる量の実測 ----
def _capacity_one(args):
    """同時に着いた n 人の行列から出てくる流れ（人/秒）と、同じ人たちの「速さ ÷ 間隔」。
    trim=True: 先頭と最後の20%を除いて、まん中の流れで測る（十分長い行列の流出率）。False: 行列全体（短い行列）。"""
    seed, kind, n, trim = args
    tr = make_trial(int(seed), n)
    tr["a"] = np.zeros(n)
    if kind == "stand":                                  # 立つ人だけ → 片側あけの立つ列1つ
        tr["walker"] = np.zeros(n, bool)
        mode = "A"
    elif kind in ("walk", "walk_equal"):                 # 歩く人だけ → 歩く列1つ（walk_equal は全員の速さを同じ 1.0m/s に）
        tr["walker"] = np.ones(n, bool)
        if kind == "walk_equal":
            tr["w"] = np.full(n, WALK_REL)
        mode = "A"
    else:                                                # 全員立つ・2列
        tr["walker"] = np.zeros(n, bool)
        mode = "B"
    ex = np.sort(exit_times(enter(tr, mode), L_BASE)[0])
    lo, hi = (n // 5, n * 4 // 5) if trim else (0, n - 1)
    rate = (hi - lo) / (ex[hi] - ex[lo])
    g = tr["gw"] if kind in ("walk", "walk_equal") else tr["gs"]
    spd = float(np.mean(VE + tr["w"])) if kind in ("walk", "walk_equal") else VE
    closed = spd * (hi - lo) / float(np.sum(g[lo + 1:hi + 1])) * (2 if kind == "both" else 1)   # 速さ ÷ 間隔（2列は立つ列2つぶん）
    return rate, closed


CAP_CASES = [("stand", PILE_N, True), ("walk_equal", PILE_N, True), ("walk", PILE_N, True), ("both", PILE_N, True)] +             [("walk", m, False) for m in (10, 25, 50, 100, 200, 500)]


def run_capacity(n_seeds=300):
    out = {}
    with ProcessPoolExecutor(max_workers=_workers()) as ex:
        for kind, n, trim in CAP_CASES:
            ns = n_seeds if n >= 500 else 200
            key = f"{kind}_{n}" + ("" if trim else "_all")
            out[key] = np.array(list(ex.map(_capacity_one, [(910000 + s, kind, n, trim) for s in range(ns)])))
    return out


# ============================================================
# 計算（キャッシュ）
# ============================================================
def _save(name, **arrs):
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / f"{name}.npz", **arrs)


def _load(name):
    z = np.load(CACHE / f"{name}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def _have(name, force):
    return (CACHE / f"{name}.npz").exists() and not force


def compute(force=False, only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    t00 = time.time()

    def step(name, fn):
        if only and name not in only:
            return
        if _have(name, force):
            print(f"  [{name}] キャッシュを使う")
            return
        t0 = time.time()
        _save(name, **fn())
        print(f"  [{name}] {time.time() - t0:.0f}秒", flush=True)

    # 1・4章: 割合 × 高さ（電車1本）
    for nm, s0 in (("share_main", 0), ("share_again", AGAIN)):
        def f(s0=s0):
            A, B, Aw, As, nw = run_share(s0)
            return dict(A=A, B=B, Aw=Aw, As=As, nw=nw)
        step(nm, f)
    # 2章: 混雑（100秒おき）
    def f():
        A, B = run_rush(0, N_TRIALS, [None] + P_RUSH)
        return dict(A=A, B=B)
    step("rush_main", f)
    def f():
        A, B = run_rush(AGAIN, N_TRIALS, [None] + P_RUSH_AGAIN)
        return dict(A=A, B=B)
    step("rush_again", f)
    for T in (90.0, 120.0):
        def f(T=T):
            A, B = run_rush(0, TR_RUSH_T, P_RUSH_T, T=T)
            return dict(A=A, B=B)
        step(f"rush_T{int(T)}", f)
    def f():
        A, B = run_rush(0, TR_RUSH_LONG, P_RUSH_LONG, ntrain=N_RUSH_LONG, chunk=25)
        return dict(A=A, B=B)
    step("rush_long", f)
    # 資料の間隔（歩く人は3段に1人）にしたらどう動くか（感度。1章と2章の互角だけ）
    def f():
        out = {}
        for tag, g in (("g28", 2.8), ("g30", 3.0)):
            A, B, _, _, _ = run_share(0, SENS_N, ps=P_SENS, Ls=[L_BASE], gw_mean=g)
            out[f"share_A_{tag}"], out[f"share_B_{tag}"] = A, B
            A, B = run_rush(0, SENS_N_RUSH, P_SENS_RUSH, gw_mean=g)
            out[f"rush_A_{tag}"], out[f"rush_B_{tag}"] = A, B
        return out
    step("sens_gw", f)
    # 2章（なぜ）
    step("capacity", lambda: {k: v for k, v in run_capacity().items()})
    # 3章
    step("slow_main", lambda: dict(R=run_slow(0)))
    step("slow_again", lambda: dict(R=run_slow(AGAIN)))
    # 5章
    step("stairs_main", lambda: dict(R=run_stairs(0)))
    step("stairs_again", lambda: dict(R=run_stairs(AGAIN)))
    step("pile", lambda: dict(R=run_pile_threshold()))
    print(f"計算 合計 {time.time() - t00:.0f}秒")


def load_all():
    names = ["share_main", "share_again", "rush_main", "rush_again", "rush_T90", "rush_T120", "rush_long",
             "capacity", "sens_gw", "slow_main", "slow_again", "stairs_main", "stairs_again", "pile"]
    for nm in names:
        if not (CACHE / f"{nm}.npz").exists():
            raise SystemExit(f"キャッシュがありません: {nm}（--compute で作る）")
    return {nm: _load(nm) for nm in names}


# ============================================================
# 数字のまとめ（画面に出す数字は全部ここから）
# ============================================================
RATE_STAND = VE / (2 * PITCH)                      # 立つ列の運べる量 = 速さ ÷ 間隔 = 0.5 ÷ 0.8 = 0.625 人/秒
RATE_WALK = (VE + WALK_REL) / (GW_MEAN * PITCH)    # 歩く列 = 1.0 ÷ 1.12 = 0.893 人/秒
RATE_BOTH = 2 * RATE_STAND                         # 2列 = 1.25 人/秒


def pstar_formula(T):
    """混雑のとき、立つ人が毎秒 RATE_STAND 以下に収まる歩く人の割合（100人が T 秒おき → 毎秒 100/T 人が来る）"""
    return 1 - RATE_STAND * T / N


def crossing(ps, d):
    """d（片側あけ − 2列）が正から0以下に変わる最初の所を線形補間（割合）。なければ nan"""
    ps = np.asarray(ps, float)
    d = np.asarray(d, float)
    for i in range(len(d) - 1):
        if d[i] > 0 >= d[i + 1]:
            return float(ps[i] + (ps[i + 1] - ps[i]) * d[i] / (d[i] - d[i + 1]))
    return float("nan")


def boot_cross(ps, DA, DB, nb=200, seed=1):
    """互角の割合の誤差（試行を取り直して nb 回求めた標準偏差）。DA: (試行, 割合)、DB: (試行,)"""
    r = np.random.default_rng(seed)
    S = len(DA)
    out = []
    for _ in range(nb):
        i = r.integers(0, S, S)
        out.append(crossing(ps, DA[i].mean(0) - DB[i].mean()))
    return float(np.nanstd(out))


def _nanmean(x):
    x = np.asarray(x, float)
    return float(np.nanmean(x)) if np.any(~np.isnan(x)) else float("nan")


def _se(x):
    x = np.asarray(x, float)
    return float(np.nanstd(x) / math.sqrt(np.sum(~np.isnan(x))))


def shown(D):
    S = {}
    sm, sa = D["share_main"], D["share_again"]
    pg = P_GRID
    iL = Ls_LONG.index(L_BASE)
    # ---------- 1章 ----------
    A, B = sm["A"][:, :, iL], sm["B"][:, iL]
    d_all = A - B[:, None]
    dmean = d_all.mean(0)
    rows = []
    for p in P_TABLE:
        k = pg.index(p)
        rows.append(dict(p=p, A=float(A[:, k].mean()), B=float(B.mean()), diff=float(dmean[k]), diff_se=_se(d_all[:, k]),
                         A_walk=_nanmean(sm["Aw"][:, k]), A_stand=_nanmean(sm["As"][:, k]),
                         nwalk=float(sm["nw"][:, k].mean()), A_wins=float((A[:, k] < B).mean())))
    cr = crossing(pg, dmean)
    cr_again = crossing(pg, (sa["A"][:, :, iL] - sa["B"][:, iL][:, None]).mean(0))
    S["ch1"] = dict(rows=rows, cross=cr, cross_se=boot_cross(pg, A, B), cross_again=cr_again,
                    curve=[dict(p=p, diff=float(v)) for p, v in zip(pg, dmean)], B_mean=float(B.mean()),
                    B_mean_again=float(sa["B"][:, iL].mean()))
    # ---------- 4章 ----------
    ch4 = []
    for j, h in enumerate(HEIGHTS_LONG):
        Aj, Bj = sm["A"][:, :, j], sm["B"][:, j]
        c = crossing(pg, (Aj - Bj[:, None]).mean(0))
        ca = crossing(pg, (sa["A"][:, :, j] - sa["B"][:, j][:, None]).mean(0))
        k25 = pg.index(0.25)
        ch4.append(dict(h=h, L=2 * h, cross=c, cross_se=boot_cross(pg, Aj, Bj), cross_again=ca, B_mean=float(Bj.mean()),
                        diff25=float((Aj[:, k25] - Bj).mean()), ride=2 * h / VE))
    S["ch4"] = ch4
    # ---------- 2章 ----------
    rm, ra = D["rush_main"], D["rush_again"]

    def rush_curve(R, last=None):
        sl = slice(None) if last is None else slice(last, None)
        return R["A"][:, :, sl].mean(2), R["B"][:, sl].mean(1)
    Aall, Ball = rush_curve(rm)
    Al5, Bl5 = rush_curve(rm, 10)
    pr = P_RUSH
    d_r = Aall[:, 1:] - Ball[:, None]
    cr2 = crossing(pr, d_r.mean(0))
    cr2_l5 = crossing(pr, (Al5[:, 1:] - Bl5[:, None]).mean(0))
    pa = P_RUSH_AGAIN                                   # やり直しと同じ割合だけで補間して比べる（同じ刻み同士）
    idx_a = [pr.index(p) for p in pa]
    Aa, Ba = rush_curve(ra)
    cr2_sub = crossing(pa, (Aall[:, 1:][:, idx_a] - Ball[:, None]).mean(0))
    cr2_again = crossing(pa, (Aa[:, 1:] - Ba[:, None]).mean(0))
    rrows = []
    for p in sorted(set(P_TABLE) | {0.2, 0.3, 0.4}):
        k = pr.index(p)
        rrows.append(dict(p=p, A=float(Aall[:, k + 1].mean()), B=float(Ball.mean()), diff=float(d_r[:, k].mean()), diff_se=_se(d_r[:, k]),
                          A_last5=float(Al5[:, k + 1].mean()), B_last5=float(Bl5.mean())))
    dflt = dict(A=float(Aall[:, 0].mean()), B=float(Ball.mean()), A_sd=float(Aall[:, 0].std()),
                A_p5=float(np.percentile(Aall[:, 0], 5)), A_p95=float(np.percentile(Aall[:, 0], 95)))
    Tr = {}
    for T in (90, 120):                                  # 電車の間隔 90/120秒
        Rt = D[f"rush_T{T}"]
        At, Bt = Rt["A"].mean(2), Rt["B"].mean(1)
        c = crossing(P_RUSH_T, (At - Bt[:, None]).mean(0))
        Tr[T] = dict(cross=c, cross_se=boot_cross(P_RUSH_T, At, Bt), formula=pstar_formula(T),
                     rows=[dict(p=p, A=float(At[:, i].mean()), B=float(Bt.mean())) for i, p in enumerate(P_RUSH_T)])
    rl = D["rush_long"]                                  # 40本の試算（定常状態になるか）
    longrows = []
    for i, p in enumerate(P_RUSH_LONG):
        a = rl["A"][:, i, :]
        longrows.append(dict(p=p, A15=float(a[:, :15].mean()), A40=float(a.mean()), A_last20=float(a[:, 20:].mean()),
                             A_last5of15=float(a[:, 10:15].mean()),
                             per_train=[float(a[:, k].mean()) for k in range(0, 40, 5)] + [float(a[:, 39].mean())]))
    blong = dict(B15=float(rl["B"][:, :15].mean()), B40=float(rl["B"].mean()), B_last20=float(rl["B"][:, 20:].mean()))
    S["ch2"] = dict(rows=rrows, cross=cr2, cross_se=boot_cross(pr, Aall[:, 1:], Ball), cross_last5=cr2_l5,
                    cross_sub=cr2_sub, cross_again=cr2_again, default=dflt, T=Tr, long=longrows, blong=blong,
                    curve=[dict(p=p, A=float(Aall[:, i + 1].mean()), diff=float(d_r[:, i].mean())) for i, p in enumerate(pr)],
                    B_mean=float(Ball.mean()), B_mean_again=float(Ba.mean()),
                    again_rows=[dict(p=p, A=float(Aa[:, i + 1].mean()), A_main=float(Aall[:, pr.index(p) + 1].mean())) for i, p in enumerate(pa)],
                    default_again=dict(A=float(Aa[:, 0].mean()), B=float(Ba.mean())),
                    pstar_formula=pstar_formula(T_RUSH))
    # ---------- 2章（なぜ） ----------
    cap = {}
    for k, v in D["capacity"].items():
        cap[k] = dict(sim=float(v[:, 0].mean()), sim_se=_se(v[:, 0]), closed=float(v[:, 1].mean()), n=int(len(v)),
                      worst=float(np.abs(v[:, 0] - v[:, 1]).max()))
    S["capacity"] = cap
    sg = D["sens_gw"]
    sens = {}
    for tag in ("g28", "g30"):
        sens[tag] = dict(
            cross1=crossing(P_SENS, (sg[f"share_A_{tag}"][:, :, 0] - sg[f"share_B_{tag}"][:, 0][:, None]).mean(0)),
            cross2=crossing(P_SENS_RUSH, (sg[f"rush_A_{tag}"].mean(2) - sg[f"rush_B_{tag}"].mean(1)[:, None]).mean(0)),
            walk_rate=RATE_WALK if tag == "g28" else (VE + WALK_REL) / (3.0 * PITCH))
    S["sens"] = sens
    # ---------- 3章 ----------
    def slow_sum(R):
        return dict(base_all=float(R[:, 0].mean()), base_walk=float(R[:, 1].mean()), base_stand=float(R[:, 2].mean()),
                    slow_all=float(R[:, 3].mean()), slow_walk=float(R[:, 4].mean()), slow_stand=float(R[:, 5].mean()),
                    B=float(R[:, 6].mean()), allslow_all=float(R[:, 7].mean()), allslow_walk=float(R[:, 8].mean()),
                    nwalk=float(R[:, 9].mean()), slow_all_se=_se(R[:, 3]), slow_minus_B=float((R[:, 3] - R[:, 6]).mean()),
                    slow_minus_B_se=_se(R[:, 3] - R[:, 6]), slow_loses=float((R[:, 3] > R[:, 6]).mean()),
                    base_minus_B=float((R[:, 0] - R[:, 6]).mean()))
    S["ch3"] = dict(main=slow_sum(D["slow_main"]["R"]), again=slow_sum(D["slow_again"]["R"]))
    # ---------- 5章 ----------
    def st_sum(R):
        names = ["A_v20_all", "A_v20_stand", "A_v25_all", "A_v25_stand", "B_v20_all", "B_v20_stand", "B_v25_all", "B_v25_stand"]
        d = {n: float(R[:, i].mean()) for i, n in enumerate(names)}
        d["nwalk"] = float(R[:, 8].mean())
        return d
    pile = D["pile"]["R"]
    pc = lambda col, q: float(np.nanpercentile(pile[:, col], q))
    S["ch5"] = dict(main=st_sum(D["stairs_main"]["R"]), again=st_sum(D["stairs_again"]["R"]),
                    ts=[stair_time(v) for v in STAIR_VS], ride=L_BASE / VE,
                    extra=[stair_time(v) - L_BASE / VE for v in STAIR_VS],
                    pile=dict(B_v20=float(np.nanmedian(pile[:, 0])), B_v25=float(np.nanmedian(pile[:, 1])),
                              A_v20=float(np.nanmedian(pile[:, 2])), A_v25=float(np.nanmedian(pile[:, 3])),
                              B_v20_mean=float(np.nanmean(pile[:, 0])), A_v20_mean=float(np.nanmean(pile[:, 2])),
                              B_v25_mean=float(np.nanmean(pile[:, 1])), A_v25_mean=float(np.nanmean(pile[:, 3])),
                              B_v20_p10=pc(0, 10), B_v20_p90=pc(0, 90), A_v20_p10=pc(2, 10), A_v20_p90=pc(2, 90)),
                    closed=dict(B_v20=(stair_time(0.2) - L_BASE / VE) * RATE_BOTH, A_v20=(stair_time(0.2) - L_BASE / VE) * RATE_STAND))
    return S


# ============================================================
# 照合（check_answers で全部通す。1つでも外れたら止まる）
# ============================================================
def closed_form_checks():
    """ショートと同じ閉じた式（コピー）。ここを通らなければモデルのコピーが壊れている"""
    out = []
    # (1) 全員が t=0 に着いて全員が立つ2列、間隔は一定（2段 = 0.8m）
    tr = dict(a=np.zeros(N), walker=np.zeros(N, bool), gs=np.full(N, 2 * PITCH), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    for L in (10.0, 35.0, 50.0):
        sim = float(metrics(tr, "B", L)["make"][0])
        out.append((f"閉じた式 全員同時・2列・長さ{L:.0f}m: 全員が上り終える時間（秒）", sim, 49 * 2 * PITCH / VE + L / VE, 1e-6))
    for L in (10.0, 35.0):
        sim = float(metrics(tr, "B", L)["mean"][0])
        out.append((f"閉じた式 全員同時・2列・長さ{L:.0f}m: 1人あたりの平均（秒）", sim, 1.6 * 24.5 + L / VE, 1e-6))
    # (2) 歩く25人が同時に着く、同じ速さ・同じ間隔
    wk = np.zeros(N, bool)
    wk[:25] = True
    tr2 = dict(a=np.zeros(N), walker=wk, gs=np.full(N, 0.8), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    for L in (10.0, 35.0):
        ex = exit_times(enter(tr2, "A"), L)[0]
        out.append((f"閉じた式 歩く25人が同時・長さ{L:.0f}m: 歩く最後の人（秒）", float(ex[wk].max()), 24 * 1.2 / 1.0 + L / 1.0, 1e-6))
    # (3c) 立つ人だけが100人ずつ同時に100秒おき15本 → 片側あけ（立つ列1つ）。n番目の人は 1.6×n 秒に乗る
    n = N * N_TRAIN
    tr3 = dict(a=np.repeat(np.arange(N_TRAIN) * 100.0, N), walker=np.zeros(n, bool), gs=np.full(n, 0.8), gw=np.full(n, 1.2), w=np.full(n, 0.5))
    theory = 1.6 * (n - 1) / 2 - 100 * np.mean(np.arange(n) // 100) + L_BASE / VE
    out.append(("閉じた式 ラッシュ（全員立つ・片側あけ・100人ずつ同時・100秒おき）: 1人あたりの平均（秒）", float(metrics(tr3, "A", L_BASE)["mean"][0]), float(theory), 1e-6))
    # (3d) 連結の確認: 電車の間隔が十分あいていれば、15本ぶんの平均 = 1本ずつの平均の平均
    trs = [make_trial(777 * 20 + k) for k in range(N_TRAIN)]
    big = rush_trial(777, 5000.0)
    for mode in ("A", "B"):
        one = float(np.mean([metrics(t, mode, L_BASE)["mean"][0] for t in trs]))
        out.append((f"ラッシュの連結（間隔5000秒）= 1本ずつの平均の平均 mode={mode}", float(metrics(big, mode, L_BASE)["mean"][0]), one, 1e-6))
    # (new) 歩く人の割合が0%・全員が同時に着く: 片側あけ（立つ列1つ）は 2列より 1.6×(49.5−24.5)= 40秒遅い（1章の「誰も歩かないのに片側をあける損」の上限）
    tr4 = dict(a=np.zeros(N), walker=np.zeros(N, bool), gs=np.full(N, 0.8), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    out.append(("閉じた式 割合0%・全員同時: 片側あけ − 2列 の平均（秒）= 1.6×(49.5−24.5)",
                float(metrics(tr4, "A", L_BASE)["mean"][0] - metrics(tr4, "B", L_BASE)["mean"][0]), 1.6 * (49.5 - 24.5), 1e-6))
    return out


def run_checks(D, S):
    checks = list(closed_form_checks())
    c1, c2, c3, c4, c5, cap = S["ch1"], S["ch2"], S["ch3"], S["ch4"], S["ch5"], S["capacity"]
    r = lambda x: float(int(round(x)))
    # ---------- 別の実装（0.02秒刻み） ----------
    rng = np.random.default_rng(3)
    for p in (0.15, 0.4):
        for mode in ("A", "B"):
            for L in (20.0, 35.0):
                worst = 0.0
                for sd in rng.integers(0, 100000, 4):
                    tr = with_p(make_trial(int(sd)), int(sd), p)
                    worst = max(worst, abs(float(metrics(tr, mode, L)["make"][0]) - timestep(tr, mode, L)))
                checks.append((f"別の実装（0.02秒刻み）との差 最大（秒） 割合{p:.0%} mode={mode} 長さ{L:.0f}m", worst, 0.0, 1.2))
    worst = 0.0                                          # 3章: 歩く列の2人目だけゆっくり
    for sd in rng.integers(0, 100000, 6):
        tr = with_p(make_trial(int(sd)), int(sd), SLOW_P)
        idx = np.where(tr["walker"])[0]
        tr = dict(tr, w=tr["w"].copy())
        tr["w"][idx[1]] = SLOW_W
        worst = max(worst, abs(float(metrics(tr, "A", L_BASE)["make"][0]) - timestep(tr, "A", L_BASE)))
    checks.append(("別の実装（0.02秒刻み）との差 最大（秒） 3章: 歩く列の2人目だけ上乗せ0.1m/s", worst, 0.0, 1.2))
    # ---------- ショートの再現 ----------
    z = SHORT_OUT / "data.npz"
    if z.exists():
        zz = np.load(z)["main"]
        worst = 0.0
        for sd in range(300):
            tr = make_trial(sd)
            worst = max(worst, abs(float(metrics(tr, "A", L_BASE)["mean"][0]) - zz[sd, 2, 5]), abs(float(metrics(tr, "B", L_BASE)["mean"][0]) - zz[sd, 3, 5]))
        checks.append(("ショートの1万回（保存した数字）と同じ種で一致 300回: 1人あたり平均の差 最大（秒）", worst, 0.0, 1e-6))
    zr = SHORT_OUT / "rush.npz"
    d0 = c2["default"]
    if zr.exists():
        zm = np.load(zr)["main"][:, 1, :]                # T=100秒
        checks.append(("ショートの1万回（保存した数字）と一致: ラッシュ T=100 片側あけの平均（秒）", d0["A"], float(zm[:, 0].mean()), 0.01))
        checks.append(("ショートの1万回（保存した数字）と一致: ラッシュ T=100 2列の平均（秒）", d0["B"], float(zm[:, 1].mean()), 0.01))
    checks += [
        ("ショートの画面の数字「ラッシュ 206秒｜100秒」の再現（片側あけ）", r(d0["A"]), 206.0, 0.0),
        ("ショートの画面の数字「ラッシュ 206秒｜100秒」の再現（2列）", r(d0["B"]), 100.0, 0.0),
    ]
    # 電車1本（ショートと同じ Beta のゆらぎ）100秒｜100秒 は 5章の元データ（stairs）の前に、1章の曲線の25%付近で見る
    # ---------- 運べる量の閉じた式 ----------
    checks += [
        ("運べる量 立つ列: シミュ（十分長い行列の流出率）と同じ人たちの 速さ÷間隔 の差 最大（人/秒）", cap["stand_1500"]["worst"], 0.0, 1e-9),
        ("運べる量 歩く列（全員の速さが同じ）: シミュと 速さ÷間隔 の差 最大（人/秒）", cap["walk_equal_1500"]["worst"], 0.0, 1e-9),
        ("運べる量 立つ列: 0.5 ÷ 0.8 = 0.625 人/秒（間隔のゆらぎ込みで ±0.01）", cap["stand_1500"]["sim"], RATE_STAND, 0.01),
        ("運べる量 歩く列（全員の速さが同じ）: 1.0 ÷ (2.8段×0.4m) = 0.893 人/秒（±0.015）", cap["walk_equal_1500"]["sim"], RATE_WALK, 0.015),
        ("運べる量 2列: 立つ列2つぶん 1.25 人/秒 より少ない（順番どおりに乗るので、間隔の大きい人が後ろを待たせる）", float(cap["both_1500"]["sim"] < RATE_BOTH), 1.0, 0.0),
        ("運べる量 2列: ただし 1.25 の 9割以上", float(cap["both_1500"]["sim"] >= 0.9 * RATE_BOTH), 1.0, 0.0),
        ("運べる量 歩く列（速さがばらつく）: 長い行列では 速さ÷間隔 より少ない（遅い人に全員が合わせる）", float(cap["walk_1500"]["sim"] < 0.9 * cap["walk_1500"]["closed"]), 1.0, 0.0),
        ("運べる量 歩く列（速さがばらつく）: 10人の行列より100人の行列のほうが流れが大きい（先頭の遅い人の遅れが薄まる）",
         float(cap["walk_10_all"]["sim"] < cap["walk_100_all"]["sim"]), 1.0, 0.0),
        ("運べる量 歩く列（速さがばらつく）: 立つ列より多く運ぶが、1.4倍には届かない（1.0〜1.25倍）",
         float(1.0 < cap["walk_1500"]["sim"] / cap["stand_1500"]["sim"] < 1.25), 1.0, 0.0),
    ]
    # ---------- 混雑時の互角 ≒ 1 − 0.625×T/100 ----------
    # 閉じた式は「立つ列が詰まらなくなる境目」。互角は「平均が2列の100秒と並ぶ所」なので、ぴったりは重ならない。T=100 は ±3pt、90/120 は ±5pt で見る
    for T, cr, tol in ((100, c2["cross"], 0.03), (90, c2["T"][90]["cross"], 0.05), (120, c2["T"][120]["cross"], 0.05)):
        checks.append((f"混雑の互角の割合 T={T}秒: シミュ vs 閉じた式 1 − 0.625×{T}/100（±{tol * 100:.0f}pt）", cr, pstar_formula(T), tol))
    # ---------- 別の乱数で1万回やり直し ----------
    checks += [
        ("別の乱数の1万回: 1章 互角の割合（±0.5pt）", c1["cross_again"], c1["cross"], 0.005),
        ("別の乱数の1万回: 1章 2列の平均（±0.5秒）", c1["B_mean_again"], c1["B_mean"], 0.5),
        ("別の乱数の1万回: 2章 混雑の互角の割合（同じ割合の刻みで補間・±1pt）", c2["cross_again"], c2["cross_sub"], 0.01),
        ("別の乱数の1万回: 2章 ショート設定の混雑 片側あけの平均（±1.5秒）", c2["default_again"]["A"], c2["default"]["A"], 1.5),
        ("別の乱数の1万回: 2章 2列の平均（±0.5秒）", c2["B_mean_again"], c2["B_mean"], 0.5),
    ]
    for x in c2["again_rows"]:
        if x["p"] in (0.2, 0.3, 0.4):
            checks.append((f"別の乱数の1万回: 2章 混雑 割合{x['p']:.0%} 片側あけの平均（±{max(1.5, 0.02 * x['A_main']):.1f}秒）", x["A"], x["A_main"], max(1.5, 0.02 * x["A_main"])))
    for h_main, h_again in zip(c4, c4):
        checks.append((f"別の乱数の1万回: 4章 高さ{h_main['h']:g}m 互角の割合（±0.7pt）", h_again["cross_again"], h_main["cross"], 0.007))
    m3, a3 = c3["main"], c3["again"]
    checks += [
        ("別の乱数の1万回: 3章 歩く人の平均（2人目がゆっくり・±1秒）", a3["slow_walk"], m3["slow_walk"], 1.0),
        ("別の乱数の1万回: 3章 全体の平均（2人目がゆっくり・±0.7秒）", a3["slow_all"], m3["slow_all"], 0.7),
        ("別の乱数の1万回: 3章 2列の平均（±0.5秒）", a3["B"], m3["B"], 0.5),
        ("別の乱数の1万回: 5章 階段0.2m/s 2列で階段が早い人（人・±0.5）", c5["again"]["B_v20_all"], c5["main"]["B_v20_all"], 0.5),
        ("別の乱数の1万回: 5章 階段0.25m/s 2列で階段が早い人（人・±0.5）", c5["again"]["B_v25_all"], c5["main"]["B_v25_all"], 0.5),
    ]
    # ---------- 答えの形 ----------
    cr = [x["cross"] for x in c4]
    d0_ = c1["rows"][0]["diff"]
    checks += [
        ("1章: 割合0%では片側あけが遅い（20〜40秒・全員が同時に着く40秒より小さい）", float(20 < d0_ < 40), 1.0, 0.0),
        ("1章: 割合が増えるほど 片側−2列 は小さくなる（5%刻みの表で単調）", float(all(a["diff"] > b["diff"] for a, b in zip(c1["rows"], c1["rows"][1:]))), 1.0, 0.0),
        ("1章: 互角は 20〜30% の間", float(0.20 < c1["cross"] < 0.30), 1.0, 0.0),
        ("2章: 混雑の互角は電車1本の互角より大きい（右へずれる）", float(c2["cross"] > c1["cross"]), 1.0, 0.0),
        ("2章: 電車の間隔が短いほど互角の割合は大きい（90 > 100 > 120秒）", float(c2["T"][90]["cross"] > c2["cross"] > c2["T"][120]["cross"]), 1.0, 0.0),
        ("感度: 歩く人の間隔を資料の値（3段に1人）にしても 1章の互角は 1.5pt 以内で動かない", S["sens"]["g30"]["cross1"], S["sens"]["g28"]["cross1"], 0.015),
        ("感度: 同じく 2章（混雑）の互角も 1.5pt 以内で動かない", S["sens"]["g30"]["cross2"], S["sens"]["g28"]["cross2"], 0.015),
        ("2章: 2列は混雑でも 100秒前後（電車1本の 99.8 と 2秒以内）", float(abs(c2["B_mean"] - c1["B_mean"]) < 2), 1.0, 0.0),
        ("4章: 高さが高いほど互角の割合は小さい（3 > 10 > 17.5 > 25 > 40m）", float(all(a > b for a, b in zip(cr, cr[1:]))), 1.0, 0.0),
        ("4章: 17.5m の互角は 1章と同じ値", c4[2]["cross"], c1["cross"], 1e-9),
        ("3章: 2人目がゆっくりだと 歩く人の平均が10秒以上遅くなる", float(m3["slow_walk"] - m3["base_walk"] > 10), 1.0, 0.0),
        ("3章: 2人目がゆっくりだと 全体の平均で片側あけが2列に負ける", float(m3["slow_all"] > m3["B"]), 1.0, 0.0),
        ("3章: ゆっくりな人がいなければ 片側あけは2列と互角（±3秒）", float(abs(m3["base_minus_B"]) < 3), 1.0, 0.0),
        ("5章: 階段0.25m/s は立って乗る70秒と同じ → 2列の先頭2人の後ろから階段が早い（2列 2〜3人目）",
         c5["pile"]["B_v25"], 2.0, 1.0),
        ("5章: 階段0.25m/s は 立つ列なら 前に1人いれば階段が早い", c5["pile"]["A_v25"], 1.0, 0.0),
        ("5章: 階段0.2m/s 2列の人数が『運べる量 × 差17.5秒』と一致（実測の流出率で・±2人）", c5["pile"]["B_v20"], cap["both_1500"]["sim"] * c5["extra"][0], 2.0),
        ("5章: 階段0.2m/s 立つ列の人数が『運べる量 × 差17.5秒』と一致（±1.5人）", c5["pile"]["A_v20"], cap["stand_1500"]["sim"] * c5["extra"][0], 1.5),
        ("5章: 立つ列の人数は2列の約半分（立つ列 × 2 ≒ 2列・±3人）", 2 * c5["pile"]["A_v20"], c5["pile"]["B_v20"], 3.0),
        ("5章: 階段0.25m/s のほうが階段0.2m/s より階段が早い人が多い（2列）", float(c5["main"]["B_v25_all"] > c5["main"]["B_v20_all"]), 1.0, 0.0),
    ]
    check_answers(checks)
    print(f"  照合 {len(checks)} 件 すべて OK")
    return len(checks)



# ============================================================
# 数字の書き出し（out/escalator-long/numbers.md と data.json）
# ============================================================
def _row(S, key, p):
    return next(x for x in S[key]["rows"] if abs(x["p"] - p) < 1e-9)


def story_table(S):
    """構成案の試算表の数字 → 1万回の数字。互角の割合が5pt以上・秒が10%以上ずれたら「要説明」"""
    c1, c2, c3, c4, c5, cap = S["ch1"], S["ch2"], S["ch3"], S["ch4"], S["ch5"], S["capacity"]
    m3 = c3["main"]
    items = [
        ("1章 割合0%の 片側−2列（秒）", 37, _row(S, "ch1", 0.0)["diff"], "sec"),
        ("1章 互角の割合（%）", 25, c1["cross"] * 100, "pt"),
        ("1章 割合40%の 片側−2列（秒）", -14, _row(S, "ch1", 0.4)["diff"], "sec"),
        ("2章 混雑の互角の割合（%）（構成案は約37〜38）", 37.5, c2["cross"] * 100, "pt"),
        ("2章 割合30% 片側あけ（秒）", 153, _row(S, "ch2", 0.3)["A"], "sec"),
        ("2章 割合40% 片側あけ（秒）", 89, _row(S, "ch2", 0.4)["A"], "sec"),
        ("2章 割合20% 片側あけ（秒）", 263, _row(S, "ch2", 0.2)["A"], "sec"),
        ("2章 2列（秒）", 100, c2["B_mean"], "sec"),
        ("なぜ 立つ列（人/秒）", 0.63, cap["stand_1500"]["sim"], "sec"),
        ("なぜ 歩く列（人/秒）", 0.89, cap["walk_1500"]["sim"], "sec"),
        ("なぜ 2列（人/秒）", 1.25, cap["both_1500"]["sim"], "sec"),
        ("3章 歩く人の平均 基準（秒）", 46, m3["base_walk"], "sec"),
        ("3章 歩く人の平均 2人目がゆっくり（秒）", 68, m3["slow_walk"], "sec"),
        ("3章 全体の平均 基準（秒）", 99, m3["base_all"], "sec"),
        ("3章 全体の平均 2人目がゆっくり（秒）", 105, m3["slow_all"], "sec"),
        ("3章 2列（秒）", 100, m3["B"], "sec"),
    ]
    for h, v in zip(c4, (32, 28, 25, 23, 19)):
        items.append((f"4章 高さ{h['h']:g}mの互角の割合（%）", v, h["cross"] * 100, "pt"))
    items += [
        ("5章 階段0.2m/s 2列の人数（人）", 22, c5["pile"]["B_v20"], "sec"),
        ("5章 階段0.2m/s 立つ列の人数（人）", 11, c5["pile"]["A_v20"], "sec"),
        ("5章 階段0.2m/s 電車1本100人で階段が早い人 2列（人）（構成案は「約7割」＝69人）", 69, c5["main"]["B_v20_all"], "sec"),
        ("5章 階段0.2m/s 同 片側あけの立つ人（人）", 60, c5["main"]["A_v20_stand"], "sec"),
        ("5章 階段0.25m/s 同 2列（人）", 97, c5["main"]["B_v25_all"], "sec"),
        ("5章 階段0.25m/s 同 片側あけの立つ人（人）", 74, c5["main"]["A_v25_stand"], "sec"),
    ]
    out = []
    for name, story, now, kind in items:
        d = now - story
        flag = (abs(d) >= 5) if kind == "pt" else (abs(d) >= 0.10 * abs(story))
        out.append(dict(name=name, story=story, now=now, diff=d, flag=bool(flag), kind=kind))
    return out


def write_numbers(S, n_checks):
    c1, c2, c3, c4, c5, cap = S["ch1"], S["ch2"], S["ch3"], S["ch4"], S["ch5"], S["capacity"]
    L = []
    a = L.append
    f1 = lambda x: f"{x:.1f}"
    a("# エスカレーター（ロング）シミュレーションの数字")
    a("")
    a(f"`sims/escalator-long.py` が出した数字（2026-10-13）。構成案 `research/escalator_long_storyboard.md` の「試算」表を1万回で出し直したもの。照合 {n_checks} 件すべて pass。")
    a("電車1本・割合を動かす章（1・3・4・5章）は 1万回、混雑（2章）は 1万回×電車15本（電車の間隔 90/120秒も1万回）、運べる量の実測は 300回×1,500人の行列。乱数は種固定（別の乱数 500000〜 でもやり直して一致を確認）。")
    a("")
    a("## 設定（モデルはショート `sims/escalator-2retsu.py` と同じ。値は変えていない）")
    a("")
    a("| 項目 | 値 |")
    a("|---|---|")
    a("| エスカレーター | **高さ17.5m・斜面35m・勾配30度**。速さ 秒速0.5m（**斜面に沿って**。高さ方向は 0.25m/秒）。立って乗ると 35÷0.5 = **70秒**（＝17.5÷0.25） |")
    a("| 階段 | 高さ方向の速さ 0.2 / 0.25 m/秒 → 高さ17.5m で **87.5秒 / 70秒**。エスカレーターも階段も **高さ同士** で比べている（ショートの「17.5m」は高さ。コード上の `HEIGHT`、斜面は `L_BASE = 2×HEIGHT`） |")
    a("| 立つ人の間隔 | **2段に1人**（前の人との間隔2段分＝0.8m。「1段あける」）。1人ごとに 1〜3段に1人、その回の平均は 1.6〜2.4 段に1人でゆらす |")
    a("| 歩く人の間隔 | 平均 **2.8段に1人**（1.12m）、標準偏差0.4段。資料の「歩く人は3段に1人（2段あける）」より 0.2段だけ詰めてある |")
    a("| 歩く人の速さ | 地面から見て 約1.0m/s（エスカレーターの上で秒速0.5m 上乗せ。標準偏差0.1。追い越しなし） |")
    a("| 電車 | 1本100人、20〜50秒かけて着く。混雑は 100秒おき×15本（1,500人） |")
    a("| 歩く人の割合 | 1・2・3・4章は各人が確率 p で歩く（p を動かす）。0章の再現・5章はショートと同じ Beta のゆらぎ（平均25%） |")
    a("| 指標 | 1人あたりの平均（列に着いてから上り終えるまで。下の行列で待つ時間込み） |")
    a("")
    # ---- 1章 ----
    a("## 1章 歩く人が何割なら？（電車1本・高さ17.5m・1万回）")
    a("")
    a("| 歩く人の割合 | 片側あける（秒） | 2列で立つ（秒） | 片側 − 2列（秒）（± は標準誤差） | 片側が早い回 | 歩く人の平均 | 立つ人の平均 |")
    a("|---|---|---|---|---|---|---|")
    for x in c1["rows"]:
        a(f"| {x['p']:.0%} | {f1(x['A'])} | {f1(x['B'])} | {x['diff']:+.1f} (±{x['diff_se']:.2f}) | {x['A_wins']:.0%} | {f1(x['A_walk']) if not math.isnan(x['A_walk']) else '—'} | {f1(x['A_stand'])} |")
    a("")
    a(f"- **互角の割合（0を横切る所・1%刻みの曲線を補間）: {c1['cross'] * 100:.1f}%**（誤差 ±{c1['cross_se'] * 100:.2f}pt、別の乱数 {c1['cross_again'] * 100:.1f}%）。画面は「約25%」。")
    a(f"- 0%（誰も歩かない）: 片側あけが **{_row(S, 'ch1', 0.0)['diff']:+.0f}秒** 損。全員が同時に着く最悪の場合の閉じた式は +40秒（照合に使用）。")
    a("")
    # ---- 2章 ----
    a("## 2章 朝の混雑（100秒おきに100人×15本）")
    a("")
    a("| 歩く人の割合 | 片側あける（秒） | 2列で立つ（秒） | 片側 − 2列（秒） | 後半5本の片側（秒） | 後半5本の2列（秒） |")
    a("|---|---|---|---|---|---|")
    for x in c2["rows"]:
        a(f"| {x['p']:.0%} | {f1(x['A'])} | {f1(x['B'])} | {x['diff']:+.1f} (±{x['diff_se']:.2f}) | {f1(x['A_last5'])} | {f1(x['B_last5'])} |")
    a("")
    a(f"- **互角の割合: {c2['cross'] * 100:.1f}%**（誤差 ±{c2['cross_se'] * 100:.2f}pt。後半5本だけの平均で見ると {c2['cross_last5'] * 100:.1f}%。別の乱数 {c2['cross_again'] * 100:.1f}%＝同じ刻みで補間した本番 {c2['cross_sub'] * 100:.1f}% と比較）。")
    for p in (0.2, 0.3, 0.4):
        x = _row(S, "ch2", p)
        a(f"- 割合{p:.0%}: 片側あけ **{x['A']:.0f}秒** ｜ 2列 **{x['B']:.0f}秒**")
    d = c2["default"]
    a(f"- ショートと同じ設定（割合は平均25%でゆらす）の混雑: 片側 {d['A']:.1f}秒（5〜95% {d['A_p5']:.0f}〜{d['A_p95']:.0f}）｜2列 {d['B']:.1f}秒 → ショートの「206秒｜100秒」を再現。")
    a(f"- 閉じた式 1 − 0.625 × T ÷ 100: T=100秒 → {c2['pstar_formula'] * 100:.1f}%。")
    a("")
    a("電車の間隔を変えたときの互角の割合（1万回×15本）:")
    a("")
    a("| 電車の間隔 | シミュの互角 | 閉じた式 1−0.625×T/100 | 差 |")
    a("|---|---|---|---|")
    a(f"| 90秒 | {c2['T'][90]['cross'] * 100:.1f}% (±{c2['T'][90]['cross_se'] * 100:.2f}) | {c2['T'][90]['formula'] * 100:.1f}% | {(c2['T'][90]['cross'] - c2['T'][90]['formula']) * 100:+.1f}pt |")
    a(f"| 100秒 | {c2['cross'] * 100:.1f}% (±{c2['cross_se'] * 100:.2f}) | {c2['pstar_formula'] * 100:.1f}% | {(c2['cross'] - c2['pstar_formula']) * 100:+.1f}pt |")
    a(f"| 120秒 | {c2['T'][120]['cross'] * 100:.1f}% (±{c2['T'][120]['cross_se'] * 100:.2f}) | {c2['T'][120]['formula'] * 100:.1f}% | {(c2['T'][120]['cross'] - c2['T'][120]['formula']) * 100:+.1f}pt |")
    a("")
    a("**「十分な本数」について（40本の試算・2,000回）。** 片側あけの立つ列が詰まる割合（立つ人が毎秒0.625人を超える）では、行列が伸び続けて定常状態にならない。本数を増やすほど平均は大きくなる。")
    a("")
    a("| 割合 | 15本の平均 | 15本のうち後半5本 | 40本の平均 | 40本のうち後半20本 | 電車ごとの平均（1,6,11,…,36本目と40本目） |")
    a("|---|---|---|---|---|---|")
    for x in c2["long"]:
        a(f"| {x['p']:.0%} | {f1(x['A15'])} | {f1(x['A_last5of15'])} | {f1(x['A40'])} | {f1(x['A_last20'])} | {' / '.join(f'{v:.0f}' for v in x['per_train'])} |")
    bl = c2["blong"]
    a(f"| 2列 | {f1(bl['B15'])} | — | {f1(bl['B40'])} | {f1(bl['B_last20'])} | — |")
    a("")
    a("→ 割合35%以下は「15本の平均」でも本数に依存する（詰まったまま伸びる）ので、画面に出すときは「15本流したとき」と添えること。40%では15本でも40本でも同じ（定常）。互角の割合は、詰まりが消える境目に決まるので本数に依存しない。")
    a("")
    # ---- なぜ ----
    a("## 2章（なぜ）運べる量（人/秒）")
    a("")
    a("同時に着いた1,500人の行列の、まん中60%の流出率（300回の平均）。閉じた式は「速さ ÷ 間隔」（同じ人たちの実際の間隔・速さの平均で作る）。")
    a("")
    a("| 列 | 閉じた式（速さ÷間隔） | シミュの実測 | 実測/式 |")
    a("|---|---|---|---|")
    names = [("stand_1500", "立つ列（0.5 ÷ 0.8）"), ("walk_equal_1500", "歩く列（全員が同じ速さ1.0m/s）"), ("walk_1500", "歩く列（速さがばらつく・1,500人の行列）"),
             ("both_1500", "2列（立つ列2つぶん）")]
    for k, nm in names:
        v = cap[k]
        a(f"| {nm} | {v['closed']:.3f} | {v['sim']:.3f} (±{v['sim_se']:.3f}) | {v['sim'] / v['closed']:.0%} |")
    a("")
    a("歩く列の行列の長さ別（速さがばらつく。歩く列は追い越せないので、遅い人に後ろ全員が合わせる）:")
    a("")
    a("| 行列の人数 | 閉じた式 | 実測 | 実測/式 | 立つ列(0.625)の何倍 |")
    a("|---|---|---|---|---|")
    for m in (10, 25, 50, 100, 200, 500):
        v = cap[f"walk_{m}_all"]
        a(f"| {m}人 | {v['closed']:.3f} | {v['sim']:.3f} | {v['sim'] / v['closed']:.0%} | {v['sim'] / cap['stand_1500']['sim']:.2f}倍 |")
    v = cap["walk_1500"]
    a(f"| 1,500人 | {v['closed']:.3f} | {v['sim']:.3f} | {v['sim'] / v['closed']:.0%} | {v['sim'] / cap['stand_1500']['sim']:.2f}倍 |")
    a("")
    sn = S["sens"]
    a("## 感度: 歩く人の間隔を資料の値（3段に1人）にしたら")
    a("")
    a("モデルは歩く人の間隔を平均2.8段に1人にしている（ショートのまま）。資料の3段に1人に変えて同じ手順でやり直した（1章 4,000回・2章 2,000回×15本。他の値は同じ）。")
    a("")
    a("| 歩く人の間隔 | 歩く列の 速さ÷間隔（理想） | 1章の互角（電車1本） | 2章の互角（混雑） |")
    a("|---|---|---|---|")
    a(f"| 平均2.8段に1人（本編） | {sn['g28']['walk_rate']:.3f} 人/秒 | {sn['g28']['cross1'] * 100:.1f}% | {sn['g28']['cross2'] * 100:.1f}% |")
    a(f"| 3段に1人（資料） | {sn['g30']['walk_rate']:.3f} 人/秒 | {sn['g30']['cross1'] * 100:.1f}% | {sn['g30']['cross2'] * 100:.1f}% |")
    a("")
    a("→ 互角の割合は 0.3pt も動かない。画面の「約25%」「約4割弱」はどちらの値でも同じ。")
    a("")
    # ---- 3章 ----
    m3, a3 = c3["main"], c3["again"]
    a("## 3章 歩く人がゆっくりなら？（電車1本・割合25%・歩く列の2人目だけ上乗せ秒速0.1m）")
    a("")
    a("| | 基準（全員 秒速0.5m 上乗せ） | 2人目だけ 0.1m/s | 2列 |")
    a("|---|---|---|---|")
    a(f"| 歩く人の平均（秒） | {f1(m3['base_walk'])} | **{f1(m3['slow_walk'])}** | — |")
    a(f"| 立つ人の平均（秒） | {f1(m3['base_stand'])} | {f1(m3['slow_stand'])} | — |")
    a(f"| 全体の平均（秒） | {f1(m3['base_all'])} | **{f1(m3['slow_all'])}** | **{f1(m3['B'])}** |")
    a("")
    a(f"- 片側 − 2列: 基準 {m3['base_minus_B']:+.1f}秒 → 2人目がゆっくり {m3['slow_minus_B']:+.1f}秒（±{m3['slow_minus_B_se']:.2f}）。片側あけが負ける回 {m3['slow_loses']:.0%}。歩く人は平均 {m3['nwalk']:.1f}人。")
    a(f"- 参考: 歩く人ぜんぶの上乗せを 0.2m/s に落とすと 片側あけの全体平均 {f1(m3['allslow_all'])}秒（歩く人 {f1(m3['allslow_walk'])}秒） vs 2列 {f1(m3['B'])}秒。")
    a(f"- 別の乱数: 歩く人 {f1(a3['slow_walk'])}秒、全体 {f1(a3['slow_all'])}秒、2列 {f1(a3['B'])}秒。")
    a("")
    # ---- 4章 ----
    a("## 4章 深い駅なら？（電車1本・互角の歩く割合）")
    a("")
    a("| 高さ | 斜面の長さ | 立って乗る時間 | 互角の割合 | 誤差 | 別の乱数 | 割合25%の 片側−2列（秒） | 2列の平均（秒） |")
    a("|---|---|---|---|---|---|---|---|")
    for x in c4:
        a(f"| {x['h']:g}m | {x['L']:g}m | {x['ride']:.0f}秒 | **{x['cross'] * 100:.1f}%** | ±{x['cross_se'] * 100:.2f}pt | {x['cross_again'] * 100:.1f}% | {x['diff25']:+.1f} | {f1(x['B_mean'])} |")
    a("")
    # ---- 5章 ----
    a("## 5章 横に階段があったら？（高さ17.5m）")
    a("")
    a(f"- 立って乗る: 斜面35m ÷ 0.5 = **{c5['ride']:.0f}秒**（待ちなしのとき）。階段（高さ方向）: 0.2m/秒 → **{c5['ts'][0]:.1f}秒**、0.25m/秒 → **{c5['ts'][1]:.0f}秒**。")
    a(f"- 差（待てる時間）: 0.2m/秒なら **{c5['extra'][0]:.1f}秒**、0.25m/秒なら 0秒（待ちなしで同じ）。")
    p = c5["pile"]
    a("")
    a("**「前に何人いたら階段が早いか」** — 100人が同時に並んだ行列で、並んで乗って上り終えるまでが階段の時間を超える最初の人の「前の人数」（400回の中央値）:")
    a("")
    a("| | 階段 0.2m/秒（87.5秒） | 階段 0.25m/秒（70秒） |")
    a("|---|---|---|")
    a(f"| 2列 | **{p['B_v20']:.0f}人**（10〜90%: {p['B_v20_p10']:.0f}〜{p['B_v20_p90']:.0f}人。閉じた式 17.5秒×1.25人/秒 = {c5['closed']['B_v20']:.1f}人） | **{p['B_v25']:.0f}人**（待ちなしで同じ時間なので、2人目の後ろから） |")
    a(f"| 片側あけの立つ列 | **{p['A_v20']:.0f}人**（10〜90%: {p['A_v20_p10']:.0f}〜{p['A_v20_p90']:.0f}人。閉じた式 17.5秒×0.625人/秒 = {c5['closed']['A_v20']:.1f}人） | **{p['A_v25']:.0f}人** |")
    a("")
    a("**電車1本100人（歩く人は平均25%）で、階段のほうが早い人**（1万回の平均。「早い」＝上り終えるまでの時間が階段より長い）:")
    a("")
    a("| | 階段 0.2m/秒 | 階段 0.25m/秒 |")
    a("|---|---|---|")
    m5, a5 = c5["main"], c5["again"]
    a(f"| 2列 | {m5['B_v20_all']:.1f}人 ({m5['B_v20_all']:.0f}%) | {m5['B_v25_all']:.1f}人 ({m5['B_v25_all']:.0f}%) |")
    a(f"| 片側あけ（全員） | {m5['A_v20_all']:.1f}人 | {m5['A_v25_all']:.1f}人 |")
    a(f"| 片側あけ（立つ人のうち） | {m5['A_v20_stand']:.1f}人（立つ人 {100 - m5['nwalk']:.0f}人中 {m5['A_v20_stand'] / (100 - m5['nwalk']):.0%}） | {m5['A_v25_stand']:.1f}人（{m5['A_v25_stand'] / (100 - m5['nwalk']):.0%}） |")
    a(f"| （別の乱数）2列 | {a5['B_v20_all']:.1f}人 | {a5['B_v25_all']:.1f}人 |")
    a("")
    return L


def write_all(D, S, n_checks):
    OUT.mkdir(parents=True, exist_ok=True)
    L = write_numbers(S, n_checks)
    st = story_table(S)
    L.append("## 構成案の試算からのずれ（互角の割合が5pt以上・秒が10%以上ずれたものに ★）")
    L.append("")
    L.append("| 項目 | 構成案 | 1万回 | 差 | |")
    L.append("|---|---|---|---|---|")
    for x in st:
        fmt = (lambda v: f"{v:.2f}") if abs(x["story"]) < 2 else (lambda v: f"{v:.1f}")
        L.append(f"| {x['name']} | {fmt(x['story'])} | {fmt(x['now'])} | {x['diff']:+.1f} | {'★' if x['flag'] else ''} |")
    L.append("")
    L.append(NOTES)
    (OUT / "numbers.md").write_text("\n".join(L), encoding="utf-8")
    S2 = dict(S)
    S2["story_diff"] = st
    S2["n_checks"] = n_checks
    S2["meta"] = dict(date="2026-10-13", n_trials=N_TRIALS, height=HEIGHT, slope=L_BASE, ve=VE, n_train=N_TRAIN, T=T_RUSH,
                      rate_stand=RATE_STAND, rate_walk_free=RATE_WALK, rate_both_ideal=RATE_BOTH,
                      seeds="main=0.., again=500000..", rush_trials=dict(T100=N_TRIALS, T90_120=TR_RUSH_T, long40=TR_RUSH_LONG))
    (OUT / "data.json").write_text(json.dumps(S2, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")


NOTES = """### ずれの説明

**★は1つだけ: 「なぜ」の歩く列の運べる量。** 構成案の 0.89人/秒（歩く列は立つ列の約1.4倍）は「速さ÷間隔」の閉じた式の値で、全員が同じ速さ1.0m/sのときはシミュと完全に一致する（照合済み）。
ところが歩く速さがばらつく（標準偏差0.1）と、歩く列は追い越せないので後ろ全員が前のいちばん遅い人に合わせてしまい、長い行列の流れは **0.68人/秒（立つ列の約1.08倍、閉じた式の75%）** まで落ちる。
行列が短いときも、先頭の遅い人の遅れが全体にのるので0.54〜0.65（10〜50人）と低い。**台本・画面で「歩く列は立つ列の1.4倍運ぶ」と言うのは、速さがそろった理想の値**であり、シミュの実測には当てはまらない。
言うなら「歩く列は立つ列より少し多く運ぶ（約1.1倍）。ただし追い越せないので、遅い人1人で後ろ全員が遅くなる」（3章の伏線にもなる）。
互角の割合（約25%・約4割弱）はこの影響を受けない。混雑時の互角は立つ列の運べる量（0.625人/秒）だけで決まり、歩く列はそこまで詰まらないため。2列も 1.25 でなく **1.17人/秒**（順番どおりに乗るので、間隔の大きい人が後ろを待たせる。理想の93%）。

**★ではないが言い方に注意**
- 混雑の互角と閉じた式 1−0.625×T/100: T=100秒は 37.3% 対 37.5% で一致。T=90秒は 42.0%（式44%）、T=120秒は 28.6%（式25%）。
  式は「立つ列が詰まらなくなる境目」で、互角は「平均が2列の100秒と並ぶ所」なので、ぴったりは重ならない（ずれ 2〜4pt）。構成案の「120秒おきなら25%、90秒おきなら約44%」は「約29%」「約42%」に直すこと。「電車が詰まるほど、もっと多くの人が歩かないと追いつかない」という向きは変わらない。
- 「十分な本数」: 割合35%以下では片側あけの行列が伸び続けて定常状態にならない（40本流すと30%で 154秒→258秒、後半20本だけなら 341秒）。画面の「153秒」「154秒」は **15本流したときの平均**。40%以上は定常で、15本でも40本でも約90〜92秒。互角の割合は本数に依存しない（15本全体 37.3%、後半5本だけ 38.2%）。
- 5章: 2列で並ぶ人数は構成案22人 → 21人（中央値。10〜90%で18〜24人）。「運べる量1.25」でなく実測1.17人/秒を掛けると20.6人で、シミュと合う。立つ列は 11人で変わらず。階段0.25m/sは「待ちなしで立って乗るのと同じ70秒」なので、**2列なら前に2人、立つ列なら前に1人いれば階段が早い**。「電車1本100人」で階段が早い人は階段0.25m/sで 2列 97人（97%）— 待ちなしの人を数えない決まり（同じ70秒は「早い」に入れない）で数えた値。0.2m/sでは 2列 69人（約7割）、片側あけの立つ人は75人中 59.6人。
- 構成案の「歩くのが遅い人1人」(3章) は 46→68秒(68.5)、99→105秒(105.0) で一致。片側あけが2列に負ける回は 91%。
- 構成案の試算「高さ5m・30mでも混雑時の互角は36〜39%」は今回の指示範囲外なので出し直していない（混雑の高さ違いは未計算）。

### モデルと資料の対応（値は変えていない）
- **高さと斜面**: ショートの「17.5m」は高さ。勾配30度なので斜面は35m、秒速0.5mは斜面に沿った速さ（高さ方向は 0.25m/秒）。立って乗る 35÷0.5 = 70秒 は 17.5÷0.25 と同じ。階段（高さ方向 0.2 / 0.25 m/秒）との比較は高さ17.5m同士で、ずれはない。4章の「高さ3〜40m」は 斜面6〜80m。
- **間隔**: 立つ人はモデルも資料も「2段に1人」（1段あける）で同じ。歩く人は資料が「3段に1人（2段あける）」、モデルは平均「2.8段に1人」で **0.2段だけ詰めて**ある（ショートのまま）。資料の値にしても互角は 0.3pt 動かない（上の感度の表）。
- 乱数は種固定。「別の乱数」は種 500000〜 で同じ試行数をやり直した値（互角の割合・平均が ±1pt／±1秒以内で一致）。
"""


def main():
    args = sys.argv[1:]
    if "--compute" in args:
        only = None
        for x in args:
            if x.startswith("--only="):
                only = set(x[7:].split(","))
        compute(force="--force" in args, only=only)
        return
    D = load_all()
    S = shown(D)
    n = run_checks(D, S)
    if "--check" in args and "--numbers" not in args:
        return
    write_all(D, S, n)
    print("書き出し:", OUT / "numbers.md", OUT / "data.json")


# ============================================================
# モデルの CLI（--compute / --check / --numbers）。引数なし（や --stills など）は場面（動画の書き出し）。
#   2026-10-13 場面を足すときに、ここを「モデルの引数があるときだけ」にした（main の中身は元のまま）
# ============================================================
_MODEL_CLI = any(a in sys.argv for a in ("--compute", "--check", "--numbers"))
if __name__ == "__main__" and _MODEL_CLI:
    main()
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・音・書き出し）。2026-10-13 追加。台本: publish/escalator-long/script.md v1 ／ 絵コンテ: research/escalator_long_storyboard.md
# 上のモデル部分は変えていない。上から見たエスカレーター・人（頭と肩）・行列の描き方は、ショート sims/escalator-2retsu.py の
# person_icon / Geo / draw_strip / draw_people / _dots / draw_rush_block / Run をコピーして、横型の見開きの左ページに合わせて直した
# （ショート側は触らない）。グラフ・ダイヤル・運べる量の図・断面・階段の行列は、ここで新しく描いた。
#
# 使い方
#   python -X utf8 sims/escalator-long.py                照合 → 本番（mp4・chapters.txt・transcript.long.txt・readings.log・stills/・screen_text.txt）
#   python -X utf8 sims/escalator-long.py --scenecheck   場面の照合だけ（画面・声の数字・見本の回・文字の重なり・字幕・終了画面）
#   python -X utf8 sims/escalator-long.py --stills       要所の静止画と sheet.png（out/escalator-long/stills/）。--at 12.3,40.5 なら指定した秒だけ
#   python -X utf8 sims/escalator-long.py --preview-intro  冒頭の静止画4枚（0・5・15・30秒）を out/escalator-long/preview/ へ
#   python -X utf8 sims/escalator-long.py --readings     合成エンジンが読むカナ（readings.log にも書く）
#   python -X utf8 sims/escalator-long.py --wraps        字幕の折り返しを全部表示
#   python -X utf8 sims/escalator-long.py --preview      960×540・15fps の確認用
#   --fake-voice をつけると、AivisSpeech なしで長さを見積もる（無音。静止画の確認用。本番では使えない）
# ####################################################################################################
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (beat, bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh, SR, _t)
from engine.note import INK, PENCIL, RED, PAPER, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

_WORKER = __name__ != "__main__"                     # 並列計算の子プロセス（__mp_main__）。場面の準備はしない
VOICE_DIR = OUT / "voice"
LX0_, LY0_, LX1_, LY1_ = lf.LEFT
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
FAKE = "--fake-voice" in sys.argv


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本 → 時間割（2026-10-14 台本 v4 に合わせて作り直し。元の注記: ナレーションは publish/escalator-long/script.md v1 のまま。読みの指定 {表記|よみ} を足した。
#   変えた所: 3章「69秒」→「68秒」（data.json の 68.49 を四捨五入すると 68。台本は numbers.md の表示 68.5 を切り上げていた）
# ============================================================
CH_TITLES = ["片側あけが得になるのは？", "では、歩く人が何割なら？", "では、朝の混雑なら？", "では、歩く人がゆっくりなら？",
             "では、エスカレーターが長い駅なら？", "では、横に階段があったら？", "まとめ"]
SPEED = 1.0


def _items():
    """読み上げ台本 v6（publish/escalator-long/narration_v6.md）。「- 」の行を1行ずつ1文として、そのまま読む。
    id は場面の時刻に使うので、v5 の id を同じ役目の文に付け直した（新しい文は c?_?x などの id）"""
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED)
        k.setdefault("pause", 0.35)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        # 0. はじめに（v6.4 2026-10-15 統括の判断: 朝の2駅のちら見せを先に。説明の順番を入れ替え）
        L("c0_1", "地下の駅のホームに、電車が着きました。"),
        L("c0_1b", "電車から降りた人たちは、上りのエスカレーターに向かいます。"),
        L("c0_6", "電車が次々に着く朝は、エスカレーターを歩いて上る人の割合が少し違うだけで、エスカレーターの前の行列が、まったく違ってきます。"),
        L("c0_6c", "最初の駅では、歩く人が{3割|さんわり}です。"),
        L("c0_6d", "次の駅では、歩く人が{4割|よんわり}です。", pause=0.1),
        G("g0", 4.0),
        L("c0_7", "{3割|さんわり}の駅では、エスカレーターの前の行列が、どんどん長くなります。"),
        L("c0_8", "{4割|よんわり}の駅では、行列が長くなりません。"),
        L("c0_9", "何が起きたのか、順番に確かめます。", pause=0.6),
        L("c0_2", "エスカレーターの乗り方には、ふたつあります。", pause=0.4),
        L("c0_3", "ひとつ目の乗り方は、「片側あけ」です。"),
        L("c0_3b", "片側あけでは、立つ人が片側に並びます。"),
        L("c0_3c", "もう片側は、歩く人のためにあけておきます。"),
        L("c0_3d", "いま見たふたつの駅は、どちらも片側あけでした。", pause=0.4),
        L("c0_4", "ふたつ目の乗り方は、「{2列|にれつ}で立つ乗り方」です。"),
        L("c0_4b", "{2列|にれつ}で立つ乗り方では、全員が左右に並んで立ちます。"),
        L("c0_4c", "この乗り方では、歩く人はいません。", pause=0.4),
        L("c0_4d", "この動画では、ふたつの乗り方のどちらのほうが、みんなが早く上に着くかを比べます。"),
        L("c0_5", "片側あけのほうが早くなるのは、歩く人が{何割|なんわり}いるときでしょうか。", pause=0.6),
        L("c0_5b", "この動画の駅は、どれもコンピューターの中で人を動かして試したものです。"),
        L("c0_9b", "歩く人が{何割|なんわり}のところで、どちらが早いかが入れ替わるのかを、確かめていきます。", pause=0.8),
        C(CH_TITLES[1], id="ch1", gap=1.2),
        # 1. では、歩く人が何割なら？
        L("c1_0", "いま見た駅では、電車が次々に着いていました。"),
        L("c1_0b", "この章では、まず、電車が{1本|いっぽん}だけ着いたときを確かめます。"),
        L("c1_1", "電車から降りるのは、{100人|ひゃくにん}です。"),
        L("c1_2", "エスカレーターは、ビルの{何階|なんがい}ぶんもの高さまで上ります。"),
        L("c1_2b", "立ったまま乗っても、上に着くまでには、しばらくかかります。", pause=0.8),   # 付箋「立つ人 1段あける」「歩く人 2段あける」を読む間
        L("c1_4", "比べるのは、それぞれの人が上に着くまでの時間です。"),
        L("c1_4b", "時間は、その人がエスカレーターの下に着いたときから数えます。"),
        L("c1_4c", "そのため、下で並んで待つ時間も、時間に入ります。"),
        L("c1_4d", "最後に、全員の時間を平均して、片側あけと{2列|にれつ}で立つ乗り方を比べます。", pause=0.4),
        L("c1_5", "なお、駅や鉄道会社は、エスカレーターでは歩かずに立ち止まって乗るよう呼びかけています。"),
        L("c1_5b", "この動画が比べるのは、上に着くまでの時間だけです。", pause=0.4),
        L("c1_6", "では、片側あけが早くなるのは、歩く人が{何割|なんわり}のときか、予想してみましょう。"),
        L("c1_6b", "多くの人は、歩く人が半分くらいいて、やっと片側あけが早くなると考えるかもしれません。", pause=0.5),
        L("c1_7", "まず、歩く人がひとりもいない場合を試します。"),
        L("c1_7b", "片側あけでは、立つ人は片側にしか並べません。"),
        L("c1_7c", "歩く人がいないので、もう片側はあいたままになります。"),
        L("c1_7d", "立つ人の行列が、長くなります。", pause=0.1),
        G("g1a", 3.0),
        L("c1_8", "片側あけでは、平均で{137秒|ひゃくさんじゅうななびょう}かかりました。"),
        L("c1_8b", "{2列|にれつ}で立つ乗り方では、平均で{100秒|ひゃくびょう}でした。"),
        L("c1_9", "歩く人がいなければ、片側あけのほうが遅くなります。", pause=0.5),
        L("c1_10", "次に、歩く人の割合を、少しずつ増やしていきます。"),
        L("c1_10b", "歩く人の割合ごとに、{1万回|いちまんかい}ずつ試しました。"),
        L("c1_10c", "人が来る順番と、誰が歩くかは、毎回変えています。", pause=0.1),
        G("g1b", 4.0),
        L("c1_10d", "歩く人が増えるほど、片側あけは早くなっていきます。"),
        L("c1_11", "歩く人が{4人|よにん}に{1人|ひとり}のとき、片側あけは、{2列|にれつ}で立つ乗り方と同じ時間になりました。", pause=0.8),
        L("c1_12", "歩く人は、半分も必要ありませんでした。"),
        L("c1_13", "歩く人は、あいている側をすぐに上れます。"),
        L("c1_13b", "歩く人が早く着くぶん、{100人|ひゃくにん}の平均の時間が短くなるのです。", pause=0.5),
        L("c1_14", "この章で分かったことを、まとめます。"),
        L("c1_14b", "この章では、電車は{1本|いっぽん}だけでした。"),
        L("c1_14c", "この場合、歩く人が{4人|よにん}に{1人|ひとり}いれば、片側あけは{2列|にれつ}で立つ乗り方と同じ早さです。"),
        L("c1_14x", "歩く人がそれより多ければ、片側あけのほうが早くなります。"),
        L("c1_14d", "冒頭のふたつの駅は、どちらも、この答えより歩く人が多い駅でした。"),
        L("c1_14e", "それなのに、{3割|さんわり}の駅では、なぜ行列が長くなったのでしょう。"),
        L("c1_14f", "次の章で、朝の混雑を確かめます。", pause=0.8),
        C(CH_TITLES[2], id="ch2", gap=1.2),
        # 2. では、朝の混雑なら？
        L("c2_0", "この章では、冒頭の朝の駅のように、電車が次々に着くときを確かめます。"),
        L("c2_1", "電車が着くたびに、{100人|ひゃくにん}が降りてきます。"),
        L("c2_1b", "歩く人の割合は、まず、さっきの章と同じ、{4人|よにん}に{1人|ひとり}にします。"),
        L("c2_2", "電車が続けて着いたとして、試します。", pause=0.1),
        G("g2a", 4.0),
        L("c2_3", "片側あけでは、平均で{206秒|にひゃくろくびょう}かかりました。"),
        L("c2_3b", "{2列|にれつ}で立つ乗り方では、来た人をすぐ乗せられるので、混んでいても、平均で{100秒|ひゃくびょう}のままでした。"),
        L("c2_4", "電車が{1本|いっぽん}のときは、片側あけと{2列|にれつ}で立つ乗り方は、同じ時間でした。"),
        L("c2_4b", "朝の混雑では、片側あけのほうが、ずっと遅くなります。", pause=0.4),
        L("c2_5", "では、歩く人の割合を変えると、どうなるでしょう。", pause=0.1),
        G("g2b", 4.0),
        L("c2_6", "片側あけと{2列|にれつ}で立つ乗り方が同じ時間になったのは、歩く人が{4割|よんわり}より{少し|すこし}少ないときでした。", pause=0.8),
        L("c2_7", "歩く人が{3割|さんわり}の駅では、片側あけの行列が伸び続けます。"),
        L("c2_7b", "{3割|さんわり}の駅では、片側あけは、{2列|にれつ}で立つ乗り方より、ずっと遅くなりました。"),
        L("c2_8", "歩く人が{4割|よんわり}の駅では、片側あけの行列は伸びません。"),
        L("c2_8b", "{4割|よんわり}の駅では、片側あけは、{2列|にれつ}で立つ乗り方より早くなりました。"),
        L("c2_9", "冒頭のふたつの駅は、ちょうど、どちらが早いかが入れ替わる所をはさんでいたのです。", pause=0.6),
        L("c2_10", "では、なぜ{4割|よんわり}くらいで入れ替わるのでしょう。", pause=0.5),
        L("c2_10b", "片側あけでは、立つ人は片側にしか並べません。"),
        L("c2_10c", "立つ人は、前の人とのあいだをあけて乗ります。"),
        L("c2_11", "そのため、立つ側から上に運べる人数には、限りがあります。"),
        L("c2_12", "立つ側が運べるのは、下に来る人の{6割|ろくわり}くらいまでです。"),
        L("c2_13", "立つ人が{6割|ろくわり}を超えると、立つ側は運び切れません。"),
        L("c2_13a", "運び切れない人は、下に残ります。"),
        L("c2_13c", "下に残る人が増えて、行列が伸び続けます。"),
        L("c2_14", "つまり、歩く人が{4割|よんわり}くらいいれば、立つ側は運び切れます。"),
        L("c2_14b", "電車が{1本|いっぽん}だけなら、運び切れない人が残っても、新しく人は来ません。"),
        L("c2_14c", "そのため、行列は、いつか無くなります。"),
        L("c2_14d", "朝は、電車が来るたびに行列が増えて、行列が無くなりません。"),
        L("c2_13b", "{2列|にれつ}で立つ乗り方は、両側で人を運べます。"),
        L("c2_13e", "{2列|にれつ}で立つ乗り方なら、下に来る人を、全員運び切れます。", pause=0.2),
        G("c2_15", 2.5),                              # 声なし: 小さな付箋「電車が90秒おきなら 約42%」
        L("c2_16", "この章で分かったことを、まとめます。"),
        L("c2_16b", "電車が次々に着く朝は、歩く人が{4割|よんわり}くらいいて、やっと片側あけが早くなります。", pause=0.5),
        L("c2_17", "ただし、歩く人がゆっくりだったら、話が変わります。", pause=0.8),
        G("g_ec", 4.0),                               # 区切り（アイキャッチ「ここまで／ここから」。声なし・章ではない）
        C(CH_TITLES[3], id="ch3", gap=1.2),
        # 3. では、歩く人がゆっくりなら？
        L("c3_0", "この章では、歩く人の中に、ゆっくり歩く人がいたらどうなるかを確かめます。"),
        L("c3_0q1", "歩く側に、ゆっくり歩く人がいることもありますよね。"),
        L("c3_0q2", "あなたも、後ろで足が止まったことはありませんか？", pause=0.6),
        L("c3_1", "電車が{1本|いっぽん}だけ着く駅に戻ります。"),
        L("c3_1x", "歩く人は、{4人|よにん}に{1人|ひとり}です。"),
        L("c3_1y", "この駅では、片側あけと{2列|にれつ}で立つ乗り方が、同じ時間でした。"),
        L("c3_1b", "歩く人だけを見ると、平均で{47秒|よんじゅうななびょう}で上に着いていました。"),
        L("c3_1c", "この時間には、下で並ぶ時間も入っています。", pause=0.4),
        L("c3_2", "ここで、歩く側の{2番目|にばんめ}の人だけが、とてもゆっくり歩くとします。"),
        L("c3_2b", "ゆっくり歩く人は、立って乗るのと、ほとんど変わらない速さで歩きます。"),
        L("c3_3", "エスカレーターの上では、前の人を追い越せません。", pause=0.1),
        G("g3", 4.0),
        L("c3_4", "歩く人の平均は、{68秒|ろくじゅうはちびょう}に延びました。"),
        L("c3_4b", "ゆっくり歩く人の後ろで、{後|あと}から来た歩く人が、全員待たされたからです。"),
        L("c3_5", "{100人|ひゃくにん}全体でも、片側あけのほうが、{2列|にれつ}で立つ乗り方より遅くなりました。", pause=0.8),
        L("c3_6x", "この章で分かったことを、まとめます。"),
        L("c3_6", "歩く側にゆっくり歩く人がいると、後ろの全員が遅れて、片側あけは不利になります。", pause=0.8),
        C(CH_TITLES[4], id="ch4", gap=1.2),
        # 4. では、エスカレーターが長い駅なら？
        L("c4_1", "この章では、エスカレーターの長さを変えて確かめます。"),
        L("c4_1z", "これまでの駅のエスカレーターは、ビルの{6階|ろっかい}ぶんくらいの高さでした。"),
        L("c4_1a", "ホームが地下深くにある駅ほど、エスカレーターは長くなります。"),
        L("c4_1b", "電車は、{1本|いっぽん}だけ着くことにします。"),
        L("c4_2", "まず、ビルの{1階|いっかい}ぶんくらいの、短いエスカレーターです。"),
        L("c4_2b", "短いエスカレーターでは、歩く人が{3割|さんわり}くらいいて、やっと片側あけが、{2列|にれつ}で立つ乗り方と同じ時間になります。", pause=0.6),
        L("c4_3", "次に、ビルの{13階|じゅうさんがい}ぶんくらいの、長いエスカレーターです。"),
        L("c4_3b", "長いエスカレーターでは、歩く人が{2割|にわり}くらいで、片側あけが、{2列|にれつ}で立つ乗り方と同じ時間になります。", pause=0.6),
        L("c4_5", "エスカレーターが長いほど、歩く人が少なくても、片側あけが早くなるのです。"),
        L("c4_4", "エスカレーターが長いほど、歩いて縮まる時間が、大きいからです。", pause=0.4),
        L("c4_6", "ところが、本物の駅では、長いエスカレーターほど、歩く人は減る、という報告もあります。"),
        L("c4_6q1", "長いエスカレーターを歩いて上ると、疲れますよね。"),
        L("c4_6q2", "あなたなら、歩きますか？", pause=0.6),
        L("c4_7", "海外の、とても長いエスカレーターで、全員に{2列|にれつ}で立って乗ってもらう試験が行われました。"),
        L("c4_7a", "試験の結果、{2列|にれつ}で立って乗ったほうが、片側あけのときより、多くの人を上に運べました。"),
        L("c4_7b", "多くの人を運べるほど、下で並ぶ時間は短くなります。"),
        L("c4_8b", "試験をしたエスカレーターでも、ふだん歩く人が少なかったのでしょう。"),
        L("c4_8", "だから、歩く人の割合が、片側あけが早くなる所まで届かなかったと考えられます。", pause=0.5),
        L("c4_9", "この章で分かったことを、まとめます。"),
        L("c4_9b", "エスカレーターが長いほど、歩く人が少なくても、片側あけが早くなります。"),
        L("c4_9c", "ただし、長いエスカレーターほど、歩く人は少なくなりがちです。", pause=0.8),
        C(CH_TITLES[5], id="ch5", gap=1.2),
        # 5. では、横に階段があったら？
        L("c5_1", "この章では、エスカレーターの横に階段がある駅を考えます。"),
        L("c5_1z", "電車は{1本|いっぽん}で、エスカレーターはこれまでと同じ長さです。"),
        L("c5_1b", "行列が長いときは、階段で上ったほうが早いかもしれません。"),
        L("c5_1c", "階段を上る速さは、人によって違います。"),
        L("c5_2", "ここでは、階段だと、立って乗るより少し時間がかかる人を考えます。", pause=0.5),
        L("c5_3", "階段で上る人は、行列に並ばなくてすみます。"),
        L("c5_3b", "行列が長いほど、階段のほうが有利になります。"),
        L("c5_4", "{2列|にれつ}で立つ乗り方の行列では、前に{20人|にじゅうにん}くらいいたら、階段のほうが早く上に着きます。"),
        L("c5_5", "片側あけの立つ側の行列では、前に{10人|じゅうにん}くらいいたら、階段のほうが早く上に着きます。", pause=0.8),
        L("c5_5b", "片側あけの立つ側は、上に運べる人数が少ないからです。"),
        L("c5_6", "階段を速く上れる人なら、もっと短い行列でも、階段のほうが早くなります。", pause=0.4),
        L("c5_7", "この章で分かったことを、まとめます。"),
        L("c5_7b", "前に並ぶ人が多いときは、階段を使うほうが、早く上に着くことがあります。", pause=0.8),
        C(CH_TITLES[6], id="ch6", gap=1.2),
        # 6. まとめ
        L("c6_0", "最後に、この動画で分かったことを、まとめます。"),
        L("c6_1", "まず、電車が{1本|いっぽん}だけのときです。"),
        L("c6_1b", "歩く人が{4人|よにん}に{1人|ひとり}いれば、片側あけと{2列|にれつ}で立つ乗り方は同じ時間です。"),
        L("c6_1c", "歩く人がそれより多ければ、片側あけのほうが早くなります。"),
        L("c6_2", "電車が次々に着く朝は、歩く人が{4割|よんわり}くらいいて、やっと片側あけが早くなります。"),
        L("c6_3", "エスカレーターが長いほど、歩く人が少なくても、片側あけが早くなります。", pause=0.5),
        L("c6_4", "なお、駅や鉄道会社は、エスカレーターでは立ち止まって乗るよう呼びかけています。"),
        L("c6_4b", "この動画で比べたのは、上に着くまでの時間だけです。", pause=0.6),
        L("c6_5", "あなたの駅のエスカレーターでは、{10人|じゅうにん}のうち、何人が歩いていますか？", pause=1.0),
        L("c6_6", "このチャンネルでは、身近な疑問を、シミュレーションで確かめる動画をあげています。"),
        L("c6_6b", "チャンネル登録してもらえると、うれしいです。", pause=0),
        G("g_end", 2.0),
    ]


@dataclass
class _FakeClip:
    text: str
    spoken: str
    duration: float

    def samples(self):
        return np.zeros(16, np.float32)


def _fake_synth(text_, cache_dir, speed=SPEED, **kw):
    import re as _re
    shown_, spoken = split_reading(text_)
    n = len(shown_) + sum(max(0, len(m.group(2)) * 0.55 - len(m.group(1)))
                          for m in _re.finditer(r"\{([^{}|]*)\|([^{}]*)\}", text_))
    return _FakeClip(shown_, spoken, 0.25 + n * 0.158 / speed)


# 字幕の折り返しを指定する文（自動だと語の途中で折れるもの）
_SUB_BREAK = {
    "電車が次々に着く朝は、エスカレーターを歩いて上る人の割合が少し違うだけで、エスカレーターの前の行列が、まったく違ってきます。":
        ["電車が次々に着く朝は、エスカレーターを歩いて上る人の割合が", "少し違うだけで、エスカレーターの前の行列が、まったく違ってきます。"],
    "短いエスカレーターでは、歩く人が3割くらいいて、やっと片側あけが、2列で立つ乗り方と同じ時間になります。":
        ["短いエスカレーターでは、歩く人が3割くらいいて、", "やっと片側あけが、2列で立つ乗り方と同じ時間になります。"],
    "長いエスカレーターでは、歩く人が2割くらいで、片側あけが、2列で立つ乗り方と同じ時間になります。":
        ["長いエスカレーターでは、歩く人が2割くらいで、", "片側あけが、2列で立つ乗り方と同じ時間になります。"],
    "海外の、とても長いエスカレーターでは、2列で立ったほうが、同じ時間で約3割多くの人が通れた試験もあります。":
        ["海外の、とても長いエスカレーターでは、2列で立ったほうが、", "同じ時間で約3割多くの人が通れた試験もあります。"],
    "2列で立つエスカレーターは、1秒に約1.2人を上に送るので、前に21人いたら、階段のほうが早い。":
        ["2列で立つエスカレーターは、1秒に約1.2人を上に送るので、", "前に21人いたら、階段のほうが早い。"],
}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)

# 一呼吸（雨ロングと同じ値）
VOICE_PAUSES = (0.10, 0.22)
NUM_BREATH = 0.5                     # 2026-10-15 ユーザー指示: 数字を言った文のあとは 0.5秒
CH_BREATH = 0.35


def voice_numbers(shown_):
    """声に出す数字（「2列」は乗り方の名前なので数えない。「4人に1人」「10人のうち何人」は1つ）"""
    import re as _re
    x = shown_.replace("2列", "").replace("4人に1人", "#").replace("10人のうち", "#")
    return _re.findall(r"#|\d+(?:\.\d+)?[^\d、。？]?", x)


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and voice_numbers(split_reading(it.text)[0]):
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# ============================================================
# 小さな道具（雨ロングと同じ）
# ============================================================
def lerp(a, b, u):
    return a + (b - a) * u


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


def kf(t, pts):
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t < t1:
            if t1 - t0 < 1e-9:
                return v1
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
    return pts[-1][1]


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


def pen_arrow(ctx, x0, y0, x1, y1, color, seed, width=6, alpha=1.0, head=22):
    pen_line(ctx, x0, y0, x1, y1, color, seed=seed, width=width, alpha=alpha)
    ang = math.atan2(y1 - y0, x1 - x0)
    for sgn in (-1, 1):
        a2 = ang + math.pi + sgn * 0.5
        pen_line(ctx, x1, y1, x1 + head * math.cos(a2), y1 + head * math.sin(a2), color, seed=seed + 3 * sgn,
                 width=width, alpha=alpha)


def legend_at(ctx, items, cx, y, size=30, gap=48, a=1.0):
    ws = [44 + text_width(lab, size, bold=False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.arc(x + 15, y, 14, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.stroke()
        text(ctx, lab, x + 44, y, size, INK, align="left", bold=False, alpha=a)
        x += w + gap


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """余白の小さい付箋（note.sticky は上下の余白が大きく、左ページの間に入らないので）。(x, y) は中心（align='left' なら左端）"""
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


def hand_title(ctx, s, x, y, size, seed, alpha=1.0, color=INK):
    """1字ずつ少し傾けた手書きの見出し。公開前チェック・重なりの検査には1行として記録する（1字ずつだと字どうしが重なって見える）"""
    saved = core._LOG
    core._LOG = None
    w = note.hand_text(ctx, s, x, y, size, color, seed=seed, alpha=alpha)
    core._LOG = saved
    if saved is not None and alpha > 0.1:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((x, y - size / 2), (x + w, y + size / 2))))
        saved.append((core._CUR_T, s, min(xs), min(ys), max(xs), max(ys), abs(ctx.user_to_device_distance(0, size)[1])))
    return w


def nolog(fn, *args, **kw):
    """飾りの字（重なりの検査に入れない）"""
    saved = core._LOG
    core._LOG = None
    try:
        return fn(*args, **kw)
    finally:
        core._LOG = saved


# ============================================================
# 絵: 上から見た人・エスカレーター（ショート escalator-2retsu.py からコピーして直した）
# ============================================================
STAND_COL, WALK_COL = "#a9d0f2", "#c5e37a"           # 立つ人＝水色、歩く人＝黄緑（最後まで入れ替えない）
C_ORANGE, C_BLUE = "#c8741c", "#2f62c9"              # 片側あける＝橙、2列で立つ＝青（数字の欄と同じ）
STRIP_FILL = "#e8e2d2"
DRAWN = [0]                                          # 描いた人の数（検査用）


def person_icon(ctx, x, y, col, w, a=1.0):
    """上から見た頭と肩（右向き＝上りの向き）。w は肩幅（px）。（ショートと同じ）"""
    if a <= 0:
        return
    DRAWN[0] += 1
    along = 0.5 * w
    lwid = max(1.0, w * 0.05)
    ctx.save()
    ctx.translate(x, y)
    if a < 1:
        ctx.push_group()
    ctx.save()
    ctx.scale(along / 2, w / 2)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(col))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(lwid)
    ctx.stroke()
    ctx.arc(0.07 * w, 0, 0.21 * w, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#6a5445"))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(lwid)
    ctx.stroke()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


_JIT = np.random.default_rng(4).uniform(-1, 1, (N * N_TRAIN, 2))
_STR = np.random.default_rng(8).uniform(-0.28, 0.28, 12)
STRIPE_OFFS = [k * PITCH + _STR[k] * PITCH for k in range(12)]
STRIPE_PERIOD = 12 * PITCH


class Geo:
    def __init__(self, x0, pxm, lw, yu, vis_right, qsp, qw, rows_u, rows_d, yq_u=None, yq_d=None, single=False, rows_one=8):
        self.x0, self.pxm, self.lw, self.yu, self.vis_right = x0, pxm, lw, yu, vis_right
        self.yd = yu + lw
        self.qsp, self.qw = qsp, qw
        self.rows_u, self.rows_d = rows_u, rows_d
        self.yq_u = yu if yq_u is None else yq_u
        self.yq_d = self.yd if yq_d is None else yq_d
        self.single, self.rows_one = single, rows_one
        self.iw = 0.64 * lw
        self.vis_m = (vis_right - x0) / pxm


def draw_strip(ctx, G, tau, L, a=1.0, moving=True):
    y0, y1 = G.yu - G.lw / 2, G.yu + G.lw * 1.5
    xr = G.x0 + min(L, G.vis_m) * G.pxm
    ctx.save()
    ctx.rectangle(G.x0 - 2, y0 - 6, xr - G.x0 + 14, y1 - y0 + 12)
    ctx.clip()
    fill(ctx, hexrgb(STRIP_FILL, a))
    ctx.rectangle(G.x0, y0, xr - G.x0, y1 - y0)
    ctx.fill()
    shift = (VE * tau) % STRIPE_PERIOD
    ctx.set_source_rgba(*hexrgb(INK, 0.20 * a))
    ctx.set_line_width(1.5)
    for base in (range(-1, int(min(L, G.vis_m) / STRIPE_PERIOD) + 2) if moving else ()):
        for off in STRIPE_OFFS:
            px = G.x0 + (base * STRIPE_PERIOD + off + shift) * G.pxm
            if G.x0 <= px <= xr:
                ctx.move_to(px, y0 + 3)
                ctx.line_to(px, y1 - 3)
    ctx.stroke()
    ctx.restore()
    for (xa, ya, xb, yb, sd, wd) in ((G.x0, y0, xr, y0, 11, 4), (G.x0, y1, xr, y1, 12, 4),
                                     (G.x0, G.yu + G.lw / 2, xr, G.yu + G.lw / 2, 13, 3)):
        pen_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=wd, alpha=0.8 * a)
    pen_line(ctx, G.x0, y0, G.x0, y1, INK, seed=14, width=4, alpha=0.8 * a)
    if L <= G.vis_m + 1e-9:
        pen_line(ctx, xr, y0, xr, y1, INK, seed=15, width=4, alpha=0.8 * a)
        for yc in (G.yu, G.yd):
            ctx.set_source_rgba(*hexrgb(INK, 0.55 * a))
            ctx.move_to(xr + 8, yc - 8)
            ctx.line_to(xr + 20, yc)
            ctx.line_to(xr + 8, yc + 8)
            ctx.close_path()
            ctx.fill()


class Run:
    """1回ぶんの動き（ショートと同じ）。時刻 tau（秒）での位置・待っている人の順番・上り終えた人数"""

    def __init__(self, tr, mode, L=L_BASE):
        self.tr, self.mode, self.L = tr, mode, L
        self.res = enter(tr, mode)
        self.ex = exit_times(self.res, L)[0]
        self.e, self.a, self.s = self.res["e"], tr["a"], self.res["s"]
        self.idx_w, self.C = self.res["idx_w"], self.res["C"]
        n = len(self.e)
        j = np.arange(n)
        lower = j[None, :] < j[:, None]
        if mode == "B":
            self.before = lower
        else:
            same = tr["walker"][:, None] == tr["walker"][None, :]
            self.before = lower & same
        self.stand = self.res["stand"]
        self.lane = self.res["lane"]
        self.mean = float((self.ex - self.a).mean())
        self.make = float(self.ex.max())

    def pos(self, tau):
        x = np.full(len(self.e), np.nan)
        m = self.stand & (self.e <= tau)
        x[m] = VE * (tau - self.e[m])
        idx = self.idx_w
        if len(idx):
            ew, sw, C = self.e[idx], self.s[idx], self.C
            ent = ew <= tau
            if ent.any():
                k = int(ent.sum())                     # 歩く列は乗った順（前の人ほど先）
                val = sw[None, :k] * (tau - ew[None, :k]) - (C[:k, None] - C[None, :k])
                tri = np.tril(np.ones((k, k), bool))
                val = np.where(tri, val, np.inf).min(1)
                x[idx[:k]] = np.maximum(0.0, val)
        return x

    def waiting(self, tau, sm=0.0):
        wait = (self.a <= tau) & (self.e > tau)
        if not wait.any():
            return wait, np.zeros(len(self.e))
        taus = [tau] if sm <= 0 else [tau - sm * u for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
        rk = np.zeros(len(self.e))
        wi = np.where(wait)[0]
        sub = self.before[wi]
        rk[wi] = np.mean([(sub & (self.e[None, :] > tt)).sum(1) for tt in taus], axis=0)
        return wait, rk

    def done(self, tau):
        return int((self.ex <= tau).sum())


def draw_people(ctx, G, run, tau, L, F, a=1.0, ring=None):
    """待っている人（行列）と、列の上の人（頭と肩）。F = 動画1秒あたりの世界の秒数。描いた人の位置を返す"""
    n = len(run.e)
    pos_out = {}
    ctx.save()
    ctx.rectangle(LX0_ + 2, G.yu - G.lw * 4, G.vis_right + 30 - LX0_, G.lw * 9)
    ctx.clip()
    wait, rk = run.waiting(tau, sm=0.25 * F)
    for i in np.where(wait)[0]:
        r = rk[i]
        if run.mode == "B":
            R, yc = G.rows_one, (G.yu + G.yd) / 2
        elif run.stand[i]:
            R, yc = G.rows_u, G.yq_u
        else:
            R, yc = G.rows_d, G.yq_d
        row = int(r + 0.5) % R
        jx, jy = _JIT[i]
        px = G.x0 - 14 - G.qsp * (r / R) + jx * G.qsp * 0.28
        py = yc + (row - (R - 1) / 2) * G.qsp + jy * G.qsp * 0.28
        k = (tau - run.a[i]) / (0.4 * max(F, 1e-6))
        slide = 90 * (1 - ease_out(k))
        col = STAND_COL if run.stand[i] else WALK_COL
        person_icon(ctx, px - slide, py, col, G.qw, a=a * clamp01(k * 1.5))
        pos_out[i] = (px - slide, py, G.qw)
    x = run.pos(tau)
    for i in np.where(~np.isnan(x))[0]:
        xm = x[i]
        lim = min(G.vis_m, L)
        if xm > lim + 1.3:
            continue
        fd = clamp01((lim + 1.2 - xm) / 1.2)
        py = G.yu + G.lw * run.lane[i]
        col = STAND_COL if run.stand[i] else WALK_COL
        person_icon(ctx, G.x0 + xm * G.pxm, py, col, G.iw, a=a * fd)
        pos_out[i] = (G.x0 + xm * G.pxm, py, G.iw)
    ctx.restore()
    return pos_out


def _dots(ctx, pts, col, r, a=1.0):
    if not pts:
        return
    DRAWN[0] += len(pts)
    ctx.new_path()
    for (x, y) in pts:
        ctx.new_sub_path()
        ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
    ctx.set_line_width(1.0)
    ctx.stroke()


def draw_rush_block(ctx, G, run, tau, a=1.0):
    """早回し用: 人を丸い点で（ショートのラッシュと同じ）。待っている人数を返す"""
    draw_strip(ctx, G, tau, L_BASE, a=a, moving=False)
    ctx.save()
    ctx.rectangle(LX0_ + 6, G.yu - 70, G.vis_right + 40 - LX0_ - 6, 200)
    ctx.clip()
    wait, rk = run.waiting(tau)
    pts = {True: [], False: []}
    for i in np.where(wait)[0]:
        if run.mode == "B":
            R, yc = G.rows_one, (G.yu + G.yd) / 2
        elif run.stand[i]:
            R, yc = G.rows_u, G.yu - 12
        else:
            R, yc = G.rows_d, G.yd + 8
        col, row = divmod(int(round(rk[i])), R)
        pts[bool(run.stand[i])].append((G.x0 - 14 - col * G.qsp, yc + (row - (R - 1) / 2) * G.qsp))
    _dots(ctx, pts[True], STAND_COL, G.qsp * 0.40, a)
    _dots(ctx, pts[False], WALK_COL, G.qsp * 0.40, a)
    x = run.pos(tau)
    on = {True: [], False: []}
    for i in np.where(~np.isnan(x))[0]:
        if x[i] > L_BASE:
            continue
        on[bool(run.stand[i])].append((G.x0 + x[i] * G.pxm, G.yu + G.lw * run.lane[i]))
    _dots(ctx, on[True], STAND_COL, 6.0, a)
    _dots(ctx, on[False], WALK_COL, 6.0, a)
    ctx.restore()
    return int(wait.sum())


def draw_train(ctx, x, y, a=1.0):
    """横から見た電車（小さく）。(x, y) は中心"""
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.set_source_rgba(*hexrgb("#e9eef6", a))
    rrect(ctx, -46, -17, 92, 32, 9)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(C_BLUE, 0.85 * a))
    ctx.rectangle(-46, 5, 92, 4)
    ctx.fill()
    for k in range(4):
        ctx.set_source_rgba(*hexrgb("#9fc3e8", a))
        rrect(ctx, -38 + k * 20, -11, 14, 11, 2)
        ctx.fill()
    for xx in (-28, 28):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(xx, 17, 4, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()


# ============================================================
# 見本の回（1万回の中央値に近い回）。キャッシュ（--compute の結果）から選び、out/escalator-long/scene_seeds.json に書く
# ============================================================
SEEDS_JSON = OUT / "scene_seeds.json"


def _z(x):
    med = np.median(x)
    iqr = np.subtract(*np.percentile(x, [75, 25]))
    return np.abs(x - med) / iqr, float(med), float(iqr)


def pick_seeds():
    if SEEDS_JSON.exists():
        return json.loads(SEEDS_JSON.read_text(encoding="utf-8"))
    sm = np.load(CACHE / "share_main.npz")
    iL = Ls_LONG.index(L_BASE)
    A_, B_ = sm["A"][:, :, iL], sm["B"][:, iL]
    sl = np.load(CACHE / "slow_main.npz")["R"]
    sc = np.zeros(len(B_))
    med = {}
    for key, arr in [("B1", B_)] + [(f"A1_{p}", A_[:, P_GRID.index(p)]) for p in (0.0, 0.1, 0.25, 0.4)] + \
                    [("slow_all", sl[:, 3]), ("slow_walk", sl[:, 4])]:
        zz, m, q = _z(arr)
        sc += zz
        med[key] = dict(median=m, iqr=q)
    s1 = int(np.argmin(sc))
    rm = np.load(CACHE / "rush_main.npz")
    RA, RB = rm["A"].mean(2), rm["B"].mean(1)
    cols = {"R_def": 0, "R_30": P_RUSH.index(0.3) + 1, "R_40": P_RUSH.index(0.4) + 1}
    sc = np.zeros(len(RB))
    for key, ci in cols.items():
        zz, m, q = _z(RA[:, ci])
        sc += zz
        med[key] = dict(median=m, iqr=q)
    zz, m, q = _z(RB)
    sc += zz
    med["R_B"] = dict(median=m, iqr=q)
    sr = int(np.argmin(sc))
    vals = {"B1": float(B_[s1]), "slow_all": float(sl[s1, 3]), "slow_walk": float(sl[s1, 4]), "R_B": float(RB[sr])}
    for p in (0.0, 0.1, 0.25, 0.4):
        vals[f"A1_{p}"] = float(A_[s1, P_GRID.index(p)])
    for key, ci in cols.items():
        vals[key] = float(RA[sr, ci])
    out = dict(seed1=s1, seed_rush=sr, sample=vals, median=med,
               note="1万回の中央値からのずれ（四分位範囲で割った値）の合計が最小の回。seed1=電車1本（1・3章）、seed_rush=混雑（冒頭・2章・まとめ）")
    SEEDS_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def rush_tr(sd, p):
    """混雑の1回（_rush_chunk と同じ作り）。p=None ならショートと同じ（Beta）の歩く人"""
    trs = [make_trial(sd * 20 + k) for k in range(N_TRAIN)]
    tr = {k: np.concatenate([t[k] for t in trs]) for k in ("walker", "gs", "gw", "w")}
    tr["a"] = np.concatenate([t["a"] + k * T_RUSH for k, t in enumerate(trs)])
    if p is not None:
        tr["walker"] = np.concatenate([np.random.default_rng(sd * 20 + k + 777).random(N) < p for k in range(N_TRAIN)])
    return tr


# ============================================================
# 準備（データ・時間割・見本の回）。子プロセスではしない
# ============================================================
if not _WORKER:
    lf.use()
    RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
    tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=2.0, synth=_fake_synth if FAKE else _voice_synth)
    S, E = tl.start, tl.end
    DUR = tl.duration
    SEEDS = pick_seeds()
    SEED1, SEED_R = SEEDS["seed1"], SEEDS["seed_rush"]
    # 電車1本（1・3章）
    TR25 = with_p(make_trial(SEED1), SEED1, 0.25)
    TR0 = with_p(make_trial(SEED1), SEED1, 0.0)
    RUN25 = (Run(TR25, "A"), Run(TR25, "B"))
    RUN0 = (Run(TR0, "A"), Run(TR0, "B"))
    _iw = np.where(TR25["walker"])[0]
    SLOW_I = int(_iw[1])                                 # 歩く列の2人目
    TRS = dict(TR25, w=TR25["w"].copy())
    TRS["w"][SLOW_I] = SLOW_W
    RUNS3 = (Run(TRS, "A"), RUN25[1])
    # 混雑（冒頭・2章・まとめ）
    TRD = rush_tr(SEED_R, None)
    TR30 = rush_tr(SEED_R, 0.3)
    TR40 = rush_tr(SEED_R, 0.4)
    RUNR = dict(d=Run(TRD, "A"), B=Run(TRD, "B"), p30=Run(TR30, "A"), p40=Run(TR40, "A"))

    # ---------- 画面と声に出す数字（すべて data.json から） ----------
    _c1, _c2, _c3, _c4, _c5, _cap = RES["ch1"], RES["ch2"], RES["ch3"]["main"], RES["ch4"], RES["ch5"], RES["capacity"]
    _r1 = {round(r["p"], 2): r for r in _c1["rows"]}
    _r2 = {round(r["p"], 2): r for r in _c2["rows"]}
    _h = {r["h"]: r for r in _c4}
    SH = dict(
        A0=ihalf(_r1[0.0]["A"]), B1=ihalf(_c1["B_mean"]), LOSS0=ihalf(_r1[0.0]["diff"]),
        X1=ihalf(_c1["cross"] * 100),
        AD=ihalf(_c2["default"]["A"]), BR=ihalf(_c2["B_mean"]), X2_10=ihalf(_c2["cross"] * 10), X2=_c2["cross"], X2P=ihalf(_c2["cross"] * 100),
        A30=ihalf(_r2[0.3]["A"]), A40=ihalf(_r2[0.4]["A"]),
        CAP=ihalf(_cap["stand_1500"]["sim"] * 10) / 10, CAP2=ihalf(_cap["both_1500"]["sim"] * 10) / 10, CAP6=ihalf(RATE_STAND * 10), X90=ihalf(_c2["T"]["90"]["cross"] * 100),
        W0=ihalf(_c3["base_walk"]), W1=ihalf(_c3["slow_walk"]), AS=ihalf(_c3["slow_all"]), B3=ihalf(_c3["B"]),
        X3=ihalf(_h[3.0]["cross"] * 100), X40=ihalf(_h[40.0]["cross"] * 100), X17=ihalf(_h[17.5]["cross"] * 100),
        X3_10=ihalf(_h[3.0]["cross"] * 10), X40_10=ihalf(_h[40.0]["cross"] * 10),
        AH3=ihalf(_h[3.0]["B_mean"] + _h[3.0]["diff25"]), BH3=ihalf(_h[3.0]["B_mean"]),
        AH40=ihalf(_h[40.0]["B_mean"] + _h[40.0]["diff25"]), BH40=ihalf(_h[40.0]["B_mean"]),
        STAIR=ihalf(_c5["ts"][0]), RIDE=ihalf(_c5["ride"]), EXTRA=ihalf(_c5["extra"][0]),
        Q2=ihalf(_c5["pile"]["B_v20"]), Q1=ihalf(_c5["pile"]["A_v20"]),
        F3=ihalf(3.0 / 3.0), F17=ihalf(HEIGHT / 3.0), F40=ihalf(40.0 / 3.0),   # 1階＝約3m
    )


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ============================================================
# 配置
# ============================================================
# 冒頭・2章後半・まとめ: 上から 片側あけ（3割が歩く）／片側あけ（4割が歩く）／2列で立つ（うすく）。人は丸い点（早回し）
G_I3 = Geo(x0=420, pxm=13, lw=40, yu=430, vis_right=420 + 13 * L_BASE, qsp=14, qw=8, rows_u=5, rows_d=2)
G_I4 = Geo(x0=420, pxm=13, lw=40, yu=630, vis_right=420 + 13 * L_BASE, qsp=14, qw=8, rows_u=5, rows_d=2)
G_I2 = Geo(x0=420, pxm=13, lw=40, yu=815, vis_right=420 + 13 * L_BASE, qsp=14, qw=8, rows_u=5, rows_d=2, single=True, rows_one=6)
# 1・3章: 上＝片側あける、下＝2列で立つ。人は頭と肩
G1A = Geo(x0=300, pxm=16.5, lw=66, yu=350, vis_right=300 + 16.5 * L_BASE, qsp=16, qw=16, rows_u=6, rows_d=3)
G1B = Geo(x0=300, pxm=16.5, lw=66, yu=665, vis_right=300 + 16.5 * L_BASE, qsp=16, qw=16, rows_u=6, rows_d=3, single=True, rows_one=8)
G1A.iw = G1B.iw = 24.0                               # 列の上の人の肩幅（0.8m おき＝13px に、前後の長さ 11px が収まる大きさ）
# 2章（混雑）: 上＝片側あける、下＝2列で立つ。人は丸い点
G2A = Geo(x0=420, pxm=13, lw=40, yu=440, vis_right=420 + 13 * L_BASE, qsp=12, qw=8, rows_u=7, rows_d=2)
G2B = Geo(x0=420, pxm=13, lw=40, yu=740, vis_right=420 + 13 * L_BASE, qsp=12, qw=8, rows_u=7, rows_d=2, single=True, rows_one=7)

T_LAY = (S("c0_6") - 0.3) if not _WORKER else 0.0   # 冒頭: 朝の2駅（片側あけの2基）のちら見せを始める時刻
T_PEEK = T_LAY + 0.4 if not _WORKER else 0.0         # 冒頭: 早回しを始める時刻（ちら見せと同時に人が流れ始める）
TAU_MAX_I = 1490.0                                   # 15本め（1,400秒）が着き終わったところ（4割の駅は行列が消え、3割の駅は伸びたまま）


def T_FF1():
    """冒頭の早回しが終わる時刻（「伸びていきます」を言い終わるところ）"""
    return E("c0_7") - 0.2


def F_I():
    return TAU_MAX_I / (T_FF1() - T_PEEK)


def tau_intro(t):
    return float(np.clip((t - T_PEEK) * F_I(), 0.0, TAU_MAX_I))


def tau_demo(t):
    """冒頭の「乗り方は2つ」: 電車1本・歩く人25% をゆっくり（人が流れているところから）"""
    return 12.0 + (t - S("c0_2") + 0.3) * 4.0


def tau_replay(t):
    t0 = S("c2_7") + 0.1
    F = TAU_MAX_I / (mid("c2_8", 0.4) - t0)
    return float(np.clip((t - t0) * F, 0.0, TAU_MAX_I))


F25 = 3.0                                            # 1章前半: 電車1本・歩く人25% をゆっくり


def tau25(t):
    return (t - S("c1_1") - 0.3) * F25


def F0():
    return (RUN0[0].make + 4.0) / (E("g1a") - S("c1_7") - 0.4)


def tau0(t):
    return (t - S("c1_7") - 0.1) * F0()


F3 = 6.0


def tau3(t):
    return (t - S("c3_2") - 0.2) * F3


def F2():
    return TAU_MAX_I / (E("g2a") - S("c2_2") - 0.6)


def tau2(t):
    return float(np.clip((t - S("c2_2") - 0.2) * F2(), 0.0, TAU_MAX_I))


def train_no(tau):
    return int(min(N_TRAIN, math.floor(tau / T_RUSH) + 1)) if tau >= 0 else 0


def train_marker(ctx, x, y, tau, F, a=1.0):
    """電車が着くたびに左から滑り込む小さな電車"""
    if a <= 0.003:
        return
    k = train_no(tau)
    if k <= 0:
        return
    age = (tau - (k - 1) * T_RUSH) / max(F, 1e-6)     # 動画の秒
    dx = -50 * (1 - ease_out(clamp01(age / 0.25)))
    draw_train(ctx, x + dx, y, a * clamp01(age / 0.25 + 0.3))


# ============================================================
# 左ページ
# ============================================================
def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 905)
    ctx.clip()


def intro_blocks(ctx, t, tau, a=1.0, two=0.0, arrows=None, arrows2=None, moving_t=None, label_a=1.0, lab=(1.0, 1.0)):
    """冒頭の3基（上: 3割が歩く・中: 4割が歩く・下: 2列で立つ（two の濃さ））"""
    if a <= 0.003:
        return
    if moving_t is not None:                         # 人が来る前: 踏段だけゆっくり動く
        for G in (G_I3, G_I4):
            draw_strip(ctx, G, moving_t, L_BASE, a=a, moving=True)
    else:
        draw_rush_block(ctx, G_I3, RUNR["p30"], tau, a)
        draw_rush_block(ctx, G_I4, RUNR["p40"], tau, a)
    tag(ctx, "片側あけ・3割が歩く", 660, G_I3.yu - 64, 30, INK, a * label_a * lab[0])
    tag(ctx, "片側あけ・4割が歩く", 660, G_I4.yu - 64, 30, INK, a * label_a * lab[1])
    if two > 0.003:
        draw_rush_block(ctx, G_I2, RUNR["B"], tau, a * two)
        tag(ctx, "2列で立つ", 660, G_I2.yu - 58, 30, INK, a * min(1.0, two * 1.6))
    if arrows is not None and t >= arrows:
        u = clamp01((t - arrows) / 0.5)
        y = G_I3.yu - 40
        pen_arrow(ctx, 450, y, lerp(450, 150, u), y, RED, seed=31, width=5, alpha=a * fade(t, arrows, 0.2), head=18)
        wr(ctx, "伸び続ける", 160, G_I3.yu - 72, 34, RED, arrows + 0.2, t, alpha=a)
    t2 = (arrows + 0.8) if arrows2 is None and arrows is not None else arrows2
    if t2 is not None and t >= t2:
        pen_circle(ctx, 300, G_I4.yu - 10, 150, 38, RED, seed=33, width=5, progress=clamp01((t - t2) / 0.5), alpha=a)
        wr(ctx, "消える", 160, G_I4.yu - 72, 34, RED, t2 + 0.2, t, alpha=a)


SIDE_GROUND, SIDE_PLAT = 380.0, 800.0                 # 横から見た駅: 地上・地下のホームの高さ（px）
SIDE_E0, SIDE_E1 = (400.0, SIDE_PLAT), (885.0, SIDE_GROUND)   # 上りエスカレーターの下の端・上の端（絵なので傾きは強め）
_SIDE_RNG = np.random.default_rng(12)
SIDE_N = 22
SIDE_T0 = 1.6 + np.cumsum(_SIDE_RNG.uniform(0.18, 0.42, SIDE_N))   # 電車を降りる時刻（動画の秒）
SIDE_X0 = _SIDE_RNG.uniform(160, 360, SIDE_N)                        # 降りる位置
SIDE_WALK = _SIDE_RNG.random(SIDE_N) < 0.3                          # 歩く人（3割ほど）


def side_person(ctx, x, y, col, a=1.0):
    """横から見た人（小さく）。(x, y) は足もと"""
    if a <= 0.003:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    rrect(ctx, x - 8, y - 34, 16, 26, 6)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#fff3df", a))
    ctx.arc(x, y - 42, 8, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.stroke()
    ctx.set_line_width(3)
    ctx.move_to(x - 4, y - 8)
    ctx.line_to(x - 4, y)
    ctx.move_to(x + 4, y - 8)
    ctx.line_to(x + 4, y)
    ctx.stroke()


def side_view(ctx, t, a=1.0):
    """冒頭: 横から見た駅。地下のホームに電車が着き、降りた人が上りのエスカレーターで地上へ"""
    if a <= 0.003:
        return
    # 地面（地上）と、地下の壁
    pen_line(ctx, 115, SIDE_GROUND, 900, SIDE_GROUND, INK, seed=201, width=5, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, 0.25 * a))
    ctx.set_line_width(2)
    for k in range(46):
        x = 120 + k * 17
        ctx.move_to(x, SIDE_GROUND + 2)
        ctx.line_to(x - 12, SIDE_GROUND - 12)
    ctx.stroke()
    fill(ctx, hexrgb("#e9e1cf", 0.55 * a))
    ctx.move_to(115, SIDE_GROUND + 4)
    ctx.line_to(SIDE_E1[0] - 10, SIDE_GROUND + 4)
    ctx.line_to(SIDE_E0[0] + 10, SIDE_PLAT - 120)
    ctx.line_to(115, SIDE_PLAT - 120)
    ctx.close_path()
    ctx.fill()
    text(ctx, "地上", 130, SIDE_GROUND - 34, 30, INK, align="left", alpha=a)
    # ホーム
    fill(ctx, hexrgb("#d9cfb8", a))
    ctx.rectangle(115, SIDE_PLAT, SIDE_E0[0] - 115 + 20, 18)
    ctx.fill()
    pen_line(ctx, 115, SIDE_PLAT, SIDE_E0[0] + 20, SIDE_PLAT, INK, seed=202, width=4, alpha=a)
    text(ctx, "地下のホーム", 130, SIDE_PLAT + 50, 30, INK, align="left", alpha=a)
    # 電車（左から入って止まる）
    u = ease_out(clamp01((t - 0.2) / 1.2))
    tx = lerp(-260, 130, u)
    ctx.save()
    ctx.rectangle(115, SIDE_PLAT - 120, 800, 120)
    ctx.clip()
    ctx.set_source_rgba(*hexrgb("#e9eef6", a))
    rrect(ctx, tx, SIDE_PLAT - 96, 250, 84, 14)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(C_BLUE, 0.85 * a))
    ctx.rectangle(tx, SIDE_PLAT - 40, 250, 7)
    ctx.fill()
    for k in range(5):
        ctx.set_source_rgba(*hexrgb("#9fc3e8", a))
        rrect(ctx, tx + 16 + k * 46, SIDE_PLAT - 84, 32, 26, 4)
        ctx.fill()
    for xx in (tx + 40, tx + 210):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(xx, SIDE_PLAT - 10, 8, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    # 上りのエスカレーター（横から: 斜めの帯と踏段）
    (x0, y0), (x1, y1) = SIDE_E0, SIDE_E1
    L_ = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L_, (y1 - y0) / L_
    nx, ny = uy, -ux
    fill(ctx, hexrgb(STRIP_FILL, a))
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.line_to(x1 - nx * 22, y1 - ny * 22)
    ctx.line_to(x0 - nx * 22, y0 - ny * 22)
    ctx.close_path()
    ctx.fill()
    pen_line(ctx, x0, y0, x1, y1, INK, seed=203, width=4, alpha=a)
    pen_line(ctx, x0 - nx * 22, y0 - ny * 22, x1 - nx * 22, y1 - ny * 22, INK, seed=204, width=3, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, 0.3 * a))
    ctx.set_line_width(1.5)
    off = (t * 18) % 16
    d = off
    while d < L_:
        px, py = x0 + ux * d, y0 + uy * d
        ctx.move_to(px, py)
        ctx.line_to(px - nx * 22, py - ny * 22)
        d += 16
    ctx.stroke()
    tag(ctx, "上りのエスカレーター →", 330, 600, 30, INK, a * fade(t, 0.8, 0.4))
    # 人: 電車を降りて右へ歩き、エスカレーターを上る（歩く人は速い）
    for i in range(SIDE_N):
        age = t - SIDE_T0[i]
        if age < 0:
            continue
        xh = SIDE_X0[i] + 150 * age
        col = WALK_COL if SIDE_WALK[i] else STAND_COL
        if xh < x0:
            side_person(ctx, xh, SIDE_PLAT - 2, col, a * clamp01(age / 0.3))
            continue
        t_on = (x0 - SIDE_X0[i]) / 150
        dd = (age - t_on) * (95 if SIDE_WALK[i] else 48)
        if dd > L_ + 30:
            continue
        px, py = x0 + ux * dd - nx * 4, y0 + uy * dd - ny * 4
        side_person(ctx, px, py, col, a * clamp01((L_ + 30 - dd) / 30))


def demo_blocks(ctx, t, a=1.0):
    """冒頭の「乗り方は2つ」: 上から見た2基（上＝片側あけ、下＝2列で立つ）"""
    if a <= 0.003:
        return
    tau = tau_demo(t)
    for G, run in ((G1A, RUN25[0]), (G1B, RUN25[1])):
        draw_strip(ctx, G, tau, L_BASE, a=a, moving=True)
        draw_people(ctx, G, run, tau, L_BASE, 4.0, a=a)
    t3, t4 = S("c0_3") + 0.2, S("c0_4") + 0.2
    if t >= t3:
        b = a * fade(t, t3, 0.3)
        mini_sticky(ctx, "片側あけ", 120, G1A.yu - 82, 36, "pink", fg=C_ORANGE, a=b, align="left")
        text(ctx, "片側に立つ・もう片側を歩く", 330, G1A.yu - 82, 28, INK, align="left", bold=False, alpha=b)
    if t >= t4:
        b = a * fade(t, t4, 0.3)
        mini_sticky(ctx, "2列で立つ", 120, G1B.yu - 82, 36, "blue", fg=C_BLUE, a=b, align="left")
        text(ctx, "両側に立つ", 350, G1B.yu - 82, 28, INK, align="left", bold=False, alpha=b)
    legend_at(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], 330, 865, size=28, a=a)
    text(ctx, "上から見たところ・右へ上る", 885, 865, 26, PENCIL, align="right", bold=False, alpha=a)


def L_open(ctx, t):
    # 0秒目から: 題字＋赤い下線（書くように引く）。0秒目から電車が入ってくる
    w = hand_title(ctx, "エスカレーター", 130, 150, 80, seed=77)
    pen_line(ctx, 124, 206, 124 + (w + 14) * 1.0, 200, RED, seed=5, width=8, progress=clamp01((t + 0.08) / 0.45))
    t_b = S("c0_2") - 0.3                             # 上から見た2基（乗り方の説明）に切り替える時刻
    grp(ctx, out_fade(t, T_LAY, 0.4), side_view, t, 1.0)
    if t >= t_b:
        grp(ctx, fade(t, t_b, 0.4), demo_blocks, t, 1.0)
    ma = fade(t, T_LAY, 0.35) * out_fade(t, t_b, 0.35)
    if ma > 0.003:
        mini_sticky(ctx, "朝の混雑（電車が次々に着く）", 560, 278, 34, "yellow", a=ma, tilt=-0.02)
        tau = tau_intro(t)
        train_marker(ctx, 180, 280, tau, F_I(), a=ma)
        lab = (fade(t, S("c0_6c"), 0.3), fade(t, S("c0_6d"), 0.3))
        grp(ctx, ma, intro_blocks, t, tau, 1.0, 0.0, S("c0_7") + 0.5, S("c0_8") + 0.3, None, 1.0, lab)



def spacing_pair(run, tau, lane, target):
    """列の上で、間隔が target（m）に近い隣どうしの2人（真ん中に近い組）"""
    x = run.pos(tau)
    on = np.where(~np.isnan(x) & (x > 3) & (x < L_BASE - 3) & (run.lane == lane))[0]
    if len(on) < 2:
        return None
    o = on[np.argsort(x[on])]
    best, bs = None, 1e9
    for i, j in zip(o[:-1], o[1:]):
        g = x[j] - x[i]
        sc = abs(g - target) * 10 + abs((x[i] + x[j]) / 2 - L_BASE * 0.55) * 0.05
        if sc < bs:
            best, bs = (int(i), int(j)), sc
    return best


_PAIRS = {}


def spacing_marks(ctx, t, a):
    """1章「2段に1人」「3段に1人」: 決めた2人の間に寸法線（2人に付いて動く）"""
    if a <= 0.003:
        return
    run = RUN25[0]
    tau = tau25(t)
    if not _PAIRS:
        tp = tau25(mid("c1_2b", 0.7) + 0.4)
        _PAIRS["s"] = spacing_pair(run, tp, 0, 2 * PITCH)
        _PAIRS["w"] = spacing_pair(run, tp, 1, 3 * PITCH)
    x = run.pos(tau)
    for key, lane, lab, y, dy in (("s", 0, "1段あける", G1A.yu - G1A.lw / 2 - 10, -26), ("w", 1, "2段あける", G1A.yu + G1A.lw * 1.5 + 10, 26)):
        pr = _PAIRS.get(key)
        if not pr or np.isnan(x[pr[0]]) or np.isnan(x[pr[1]]) or max(x[pr[0]], x[pr[1]]) > L_BASE - 1:
            continue
        xa, xb = G1A.x0 + x[pr[0]] * G1A.pxm, G1A.x0 + x[pr[1]] * G1A.pxm
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))
        ctx.set_line_width(2.5)
        ctx.move_to(xa, y)
        ctx.line_to(xb, y)
        for xx in (xa, xb):
            ctx.move_to(xx, y - 7)
            ctx.line_to(xx, y + 7)
        ctx.stroke()
        text(ctx, lab, (xa + xb) / 2, y + dy, 28, RED, alpha=a)


def done_mark(ctx, run, tau, G, a, y):
    if run.done(tau) >= len(run.e) and a > 0.003:
        tag(ctx, "全員 上り終えた", 880 - text_width("全員 上り終えた", 28) / 2 - 13, y, 28, INK, a)


def dial_p(t):
    return kf(t, [(S("c1_10") + 0.2, 0.0), (mid("c1_10c", 0.95), 0.10), (S("g1b") + 1.3, 0.25), (S("g1b") + 2.6, 0.40),
                  (E("g1b") - 0.5, 0.50), (S("c1_11") + 0.3, 0.50), (S("c1_11") + 1.3, 0.25)])


_GRID_ORDER = np.argsort(np.random.default_rng(5).permutation(100))


def draw_dial(ctx, t, a):
    if a <= 0.003:
        return
    p = dial_p(t)
    cx, cy, r = 505.0, 300.0, 130.0
    text(ctx, "歩く人の割合", cx, 128, 36, INK, alpha=a)
    ctx.set_line_width(5)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.arc(cx, cy, r, math.pi, 2 * math.pi)
    ctx.stroke()
    for k in range(6):
        ang = math.pi + k / 5 * math.pi
        ctx.move_to(cx + (r - 14) * math.cos(ang), cy + (r - 14) * math.sin(ang))
        ctx.line_to(cx + (r + 6) * math.cos(ang), cy + (r + 6) * math.sin(ang))
        ctx.stroke()
    text(ctx, "0%", cx - r - 40, cy, 28, INK, bold=False, alpha=a)
    text(ctx, "50%", cx + r + 46, cy, 28, INK, bold=False, alpha=a)
    ang = math.pi + p / 0.5 * math.pi
    pen_line(ctx, cx, cy, cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang), RED, seed=9, width=7, alpha=a)
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.arc(cx, cy, 9, 0, 2 * math.pi)
    ctx.fill()
    n = ihalf(p * 100)
    text(ctx, f"{n}%", cx, cy + 52, 56, RED, alpha=a)
    text(ctx, f"100人のうち {n}人が歩く", cx, cy + 108, 30, INK, bold=False, alpha=a)
    for k in range(100):
        row, col = divmod(k, 10)
        walk = _GRID_ORDER[k] < n
        DRAWN[0] += 1
        ctx.set_source_rgba(*hexrgb(WALK_COL if walk else STAND_COL, a))
        ctx.arc(cx - 4.5 * 46 + col * 46, 470 + row * 44, 15, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
        ctx.set_line_width(2)
        ctx.stroke()


def L_share(ctx, t):
    tb = S("c1_10")
    ab = out_fade(t, tb - 0.2, 0.4)
    if ab > 0.003:
        a1 = out_fade(t, S("c1_7") - 0.3, 0.3)
        a2 = fade(t, S("c1_7") - 0.3, 0.3)
        lab_a = fade(t, S("ch1") + 0.3, 0.4) * ab
        tag(ctx, "片側あけ", 130, G1A.yu - 78, 32, C_ORANGE, lab_a, align="left")
        tag(ctx, "2列で立つ", 130, G1B.yu - 78, 32, C_BLUE, lab_a, align="left")
        legend_at(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], 505, 160, size=30, a=lab_a)

        def phase(ctx, runs, tau, F, marks):
            for G, run in ((G1A, runs[0]), (G1B, runs[1])):
                draw_strip(ctx, G, tau, L_BASE, moving=F < 10)
                draw_people(ctx, G, run, tau, L_BASE, F)
            if marks:
                spacing_marks(ctx, t, fade(t, mid("c1_2b", 0.7), 0.3) * out_fade(t, S("c1_5"), 0.4))
        grp(ctx, a1 * ab, phase, RUN25, tau25(t), F25, True)
        if a2 > 0.003:
            grp(ctx, a2 * ab, phase, RUN0, tau0(t), F0(), False)
            for G, run in ((G1A, RUN0[0]), (G1B, RUN0[1])):
                done_mark(ctx, run, tau0(t), G, a2 * ab, G.yu - 78)
    grp(ctx, fade(t, tb - 0.1, 0.4), draw_dial, t, 1.0)


def why_left(ctx, t, a):
    """2章（なぜ）: 立つ列だけを引き伸ばした絵と、1秒に来る人の帯"""
    if a <= 0.003:
        return
    t0 = S("c2_10")
    # 立つ列（実際の速さ）
    PXM = 110.0
    y0, y1 = 300.0, 372.0
    xa, xb = 150.0, 860.0
    xe = 790.0                                        # 上の端
    text(ctx, "立つ側だけ（実際の速さ）", 150, 215, 32, INK, align="left", alpha=a)
    fill(ctx, hexrgb(STRIP_FILL, a))
    ctx.rectangle(xa, y0, xe - xa, y1 - y0)
    ctx.fill()
    tt = max(0.0, t - t0)
    shift = (VE * tt * PXM) % (PITCH * PXM)
    ctx.set_source_rgba(*hexrgb(INK, 0.22 * a))
    ctx.set_line_width(1.5)
    x = xa + shift
    while x < xe:
        ctx.move_to(x, y0 + 3)
        ctx.line_to(x, y1 - 3)
        x += PITCH * PXM
    ctx.stroke()
    for (p0, q0, p1, q1, sd) in ((xa, y0, xe, y0, 41), (xa, y1, xe, y1, 42)):
        pen_line(ctx, p0, q0, p1, q1, INK, seed=sd, width=4, alpha=0.8 * a)
    pen_line(ctx, xe, y0 - 22, xe, y1 + 22, RED, seed=43, width=5, alpha=a)
    text(ctx, "上の端", xe + 8, y0 - 36, 28, RED, align="left", bold=False, alpha=a)
    sp = 2 * PITCH * PXM                              # 2段に1人
    off = (VE * tt * PXM) % sp
    ctx.save()
    ctx.rectangle(xa, y0 - 30, xe - xa + 2, y1 - y0 + 60)
    ctx.clip()
    x = xa + off - sp
    while x < xe + sp:
        person_icon(ctx, x, (y0 + y1) / 2, STAND_COL, 48, a=a)
        x += sp
    ctx.restore()
    # ものさし（止まっている）
    ry = y1 + 34
    for xx in (330.0, 330.0 + sp):
        pen_line(ctx, xx, ry - 8, xx, ry + 8, INK, seed=int(xx), width=3, alpha=a)
    pen_line(ctx, 330, ry, 330 + sp, ry, INK, seed=44, width=3, alpha=a)
    text(ctx, "2段に1人＝0.8m", 330 + sp + 16, ry, 28, INK, align="left", bold=False, alpha=a)
    pen_arrow(ctx, 560, y0 - 30, 680, y0 - 30, INK, seed=45, width=4, alpha=a, head=14)
    text(ctx, "秒速0.5m", 545, y0 - 30, 28, INK, align="right", bold=False, alpha=a)
    n = int((VE * tt) / (2 * PITCH))
    text(ctx, f"上の端を通った人 {n}人 ／ {tt:.0f}秒", 505, 470, 32, INK, alpha=a * fade(t, t0 + 0.6, 0.3))
    # 1秒に来る人の帯
    tb = S("c2_12")
    b = a * fade(t, tb, 0.4)
    if b <= 0.003:
        return
    bx0, bx1, by0, by1 = 170.0, 830.0, 640.0, 700.0
    s = kf(t, [(S("c2_14") + 0.3, 0.75), (S("c2_14") + 1.8, 0.60)])
    text(ctx, "下に来る人 1秒に1人", 170, 595, 32, INK, align="left", alpha=b)
    xs = bx0 + s * (bx1 - bx0)
    fill(ctx, hexrgb(STAND_COL, b))
    ctx.rectangle(bx0, by0, xs - bx0, by1 - by0)
    ctx.fill()
    fill(ctx, hexrgb(WALK_COL, b))
    ctx.rectangle(xs, by0, bx1 - xs, by1 - by0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * b))
    ctx.set_line_width(3)
    ctx.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
    ctx.stroke()
    xc = bx0 + RATE_STAND * (bx1 - bx0)
    over = b * fade(t, S("c2_13") + 0.3, 0.4)
    if s > RATE_STAND and over > 0.003:
        ctx.save()
        ctx.rectangle(xc, by0, xs - xc, by1 - by0)
        ctx.clip()
        ctx.set_source_rgba(*hexrgb(RED, 0.75 * over))
        ctx.set_line_width(3)
        for k in range(-10, 40):
            ctx.move_to(xc + k * 14, by1)
            ctx.line_to(xc + k * 14 + 60, by0)
        ctx.stroke()
        ctx.restore()
    text(ctx, f"立つ人 {ihalf(s * 100)}%", (bx0 + xs) / 2, by0 + 30, 30, INK, alpha=b)
    text(ctx, f"歩く人 {ihalf((1 - s) * 100)}%", (xs + bx1) / 2 + (8 if s > 0.72 else 0), by1 + 30, 28, INK, bold=False, alpha=b)
    for yy in range(int(by0 - 26), int(by1 + 26), 14):
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * b))
        ctx.set_line_width(3)
        ctx.move_to(xc, yy)
        ctx.line_to(xc, yy + 8)
        ctx.stroke()
    wr(ctx, "立つ側が上に運べるのは ここまで", xc, 785, 30, RED, S("c2_12") + 0.6, t, align="center", alpha=b)
    if over > 0.003:
        q = over * out_fade(t, S("c2_14") + 1.4, 0.3)
        wr(ctx, "あふれる → 行列が伸びる", (bx0 + bx1) / 2, 840, 34, RED, S("c2_13") + 0.5, t, align="center", alpha=q)
        wr(ctx, "4割を超えたら → 伸びなくなる", (bx0 + bx1) / 2, 840, 34, INK, S("c2_14") + 1.6, t, align="center", alpha=b)


def L_rush(ctx, t):
    a1 = out_fade(t, S("c2_7") - 0.3, 0.35)
    if a1 > 0.003:
        tau = tau2(t)
        ma = fade(t, S("ch2") + 0.3, 0.4) * a1
        mini_sticky(ctx, "朝の混雑（電車が次々に着く）", 560, 200, 34, "yellow", a=ma, tilt=-0.02)
        train_marker(ctx, 180, 202, tau, F2(), a=ma)
        tag(ctx, "片側あけ", 130, G2A.yu - 74, 32, C_ORANGE, ma, align="left")
        tag(ctx, "2列で立つ", 130, G2B.yu - 74, 32, C_BLUE, ma, align="left")
        nA = draw_rush_block(ctx, G2A, RUNR["d"], tau, a1)
        nB = draw_rush_block(ctx, G2B, RUNR["B"], tau, a1)
        if t >= S("c2_2"):
            for nn, G in ((nA, G2A), (nB, G2B)):
                s_ = f"待っている人 {nn}人"
                text(ctx, s_, 880, G.yu - 74, 30, INK, align="right", bold=False, alpha=a1 * fade(t, S("c2_2"), 0.3))
    a2 = fade(t, S("c2_7") - 0.3, 0.35) * out_fade(t, S("c2_10") - 0.2, 0.35)
    if a2 > 0.003:
        mini_sticky(ctx, "朝の混雑（電車が次々に着く）", 560, 278, 34, "yellow", a=a2, tilt=-0.02)
        tau = tau_replay(t)
        train_marker(ctx, 180, 280, tau, TAU_MAX_I / (mid("c2_8", 0.4) - S("c2_7") - 0.1), a=a2)
        grp(ctx, a2, intro_blocks, t, tau, 1.0, 0.45, mid("c2_7", 0.6), mid("c2_8", 0.45))
    why_left(ctx, t, fade(t, S("c2_10") - 0.1, 0.4))


def L_slow(ctx, t):
    a = fade(t, S("ch3") + 0.2, 0.4)
    tag(ctx, "片側あけ", 130, G1A.yu - 78, 32, C_ORANGE, a, align="left")
    tag(ctx, "2列で立つ", 130, G1B.yu - 78, 32, C_BLUE, a, align="left")
    legend_at(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], 505, 160, size=30, a=a)
    tau = tau3(t)
    pos = {}
    for G, run in ((G1A, RUNS3[0]), (G1B, RUNS3[1])):
        draw_strip(ctx, G, tau if tau > 0 else (t - S("ch3")) * 2.0, L_BASE, a=a)
        if tau > 0:
            p_ = draw_people(ctx, G, run, tau, L_BASE, F3)
            if G is G1A:
                pos = p_
    if SLOW_I in pos and t >= S("c3_2") + 0.4:
        x, y, w = pos[SLOW_I]
        r = max(w, 16) * 0.95
        pen_circle(ctx, x, y, r + 6, r + 6, RED, seed=51, width=4, progress=clamp01((t - S("c3_2") - 0.4) / 0.4))
        tq = S("c3_3") + 0.2
        if t >= tq and x > G1A.x0 + 40:
            b = fade(t, tq, 0.3)
            yy = G1A.yu + G1A.lw * 1.5 + 22
            pen_arrow(ctx, x - 90, yy + 10, x + 40, yy + 10, RED, seed=52, width=4, alpha=b, head=14)
            nolog(text, ctx, "×", x - 25, yy + 8, 44, RED, alpha=b)
            text(ctx, "追い越せない", x - 25, yy + 52, 28, RED, alpha=b)
    if tau > 0:
        done_mark(ctx, RUNS3[0], tau, G1A, a, G1A.yu - 78)
        done_mark(ctx, RUNS3[1], tau, G1B, a, G1B.yu - 78)


# ---------- 4章: 横から見た断面 ----------
DEEP_PX = 9.0                                        # 1m あたりの px（縦横同じ）
DEEP_TOP = 250.0
DEEP = [(3.0, 660.0), (HEIGHT, 760.0), (40.0, 860.0)]  # (高さ, 地上の入口の x)


def L_deep(ctx, t):
    a = fade(t, S("ch4") + 0.2, 0.4)
    if a <= 0.003:
        return
    pen_line(ctx, 120, DEEP_TOP, 890, DEEP_TOP, INK, seed=61, width=5, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, 0.25 * a))
    ctx.set_line_width(2)
    for k in range(0, 46):
        x = 125 + k * 17
        ctx.move_to(x, DEEP_TOP - 2)
        ctx.line_to(x - 12, DEEP_TOP - 14)
    ctx.stroke()
    text(ctx, "地上", 130, DEEP_TOP - 40, 30, INK, align="left", bold=False, alpha=a)
    text(ctx, "横から見たところ", 880, DEEP_TOP - 40, 30, PENCIL, align="right", bold=False, alpha=a)
    tk = {3.0: S("c4_2"), HEIGHT: S("c4_1b") + 0.4, 40.0: S("c4_3")}
    labs = {3.0: (f"ビル{SH['F3']}階ぶん", f"同じ時間 約{SH['X3']}%"), HEIGHT: (f"ビル{SH['F17']}階ぶん", f"同じ時間 約{SH['X17']}%"),
            40.0: (f"ビル{SH['F40']}階ぶん", f"同じ時間 約{SH['X40']}%")}
    for h, xt in DEEP:
        t0 = tk[h]
        u = clamp01((t - t0) / 0.8)
        if u <= 0:
            continue
        dx, dy = h * math.sqrt(3) * DEEP_PX, h * DEEP_PX
        xb, yb = xt - dx * u, DEEP_TOP + dy * u
        pen_line(ctx, xt, DEEP_TOP, xb, yb, C_ORANGE if h == HEIGHT else INK, seed=int(h * 3), width=7, alpha=a)
        if u >= 1:
            pen_line(ctx, xb - 70, yb, xb + 10, yb, INK, seed=int(h * 5), width=4, alpha=a)
            ctx.set_source_rgba(*hexrgb(INK, 0.6 * a))
            ctx.set_line_width(2)
            ctx.move_to(xb - 70, yb + 14)
            ctx.line_to(xb + 10, yb + 14)
            ctx.stroke()
            l1, l2 = labs[h]
            b = fade(t, t0 + 0.8, 0.3) * a
            if h == 40.0:
                text(ctx, l1, xb - 20, yb + 46, 32, INK, alpha=b)
                text(ctx, l2, xb - 20, yb + 88, 30, RED, alpha=b)
            else:
                text(ctx, l1, xb - 84, yb - 2, 32, INK, align="right", alpha=b)
                text(ctx, l2, xb - 84, yb + 38, 30, RED, align="right", alpha=b)


# ---------- 5章: 横に階段（行列を1列に並べる） ----------
Q_FRONT = 760.0
Q_SP = 26.0
Q_N = 25
Q_Y = {"A": 300.0, "B": 690.0}
STAIR_Y = (470.0, 540.0)


def queue_row(ctx, y, cut, t_count, t_cut, t, a, lab):
    """前から並んだ行列（1列）。t_count から「前に○人」の札が後ろへ数えていき、t_cut で cut 人目と次の人の間に赤い線"""
    for k in range(Q_N):
        x = Q_FRONT - k * Q_SP
        behind = k >= cut and t >= t_cut + 0.6
        person_icon(ctx, x, y, STAND_COL, 24, a=a * (0.55 if behind else 1.0))
    # 入口（エスカレーターの下の端）
    fill(ctx, hexrgb(STRIP_FILL, a))
    ctx.rectangle(790, y - 34, 100, 68)
    ctx.fill()
    pen_line(ctx, 790, y - 34, 890, y - 34, INK, seed=71, width=3, alpha=0.8 * a)
    pen_line(ctx, 790, y + 34, 890, y + 34, INK, seed=72, width=3, alpha=0.8 * a)
    pen_line(ctx, 790, y - 34, 790, y + 34, INK, seed=73, width=3, alpha=0.8 * a)
    text(ctx, lab, 880, y + 58, 30, INK, align="right", alpha=a)
    if t >= t_count:
        u = clamp01((t - t_count) / 1.6)
        k = int(round(u * cut))
        x = Q_FRONT - k * Q_SP
        b = a * out_fade(t, t_cut + 0.5, 0.3)
        tag(ctx, f"前に {k}人", x, y - 50, 28, RED, b)
    if t >= t_cut:
        xc = Q_FRONT - (cut - 0.5) * Q_SP
        pen_line(ctx, xc, y - 30, xc, y + 30, RED, seed=74, width=6, progress=clamp01((t - t_cut) / 0.3), alpha=a)


def L_stairs(ctx, t):
    a = fade(t, S("ch5") + 0.2, 0.4)
    if a <= 0.003:
        return
    # 階段（横から並べた、上から見た段）
    sy0, sy1 = STAIR_Y
    fill(ctx, hexrgb("#efe6d2", a))
    ctx.rectangle(300, sy0, 590, sy1 - sy0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
    ctx.set_line_width(2)
    for k in range(0, 42):
        x = 300 + k * 14
        ctx.move_to(x, sy0 + 2)
        ctx.line_to(x, sy1 - 2)
    ctx.stroke()
    pen_line(ctx, 300, sy0, 890, sy0, INK, seed=81, width=3, alpha=0.8 * a)
    pen_line(ctx, 300, sy1, 890, sy1, INK, seed=82, width=3, alpha=0.8 * a)
    text(ctx, "階段", 280, (sy0 + sy1) / 2, 34, INK, align="right", alpha=a)
    tb = S("c5_2") + 0.4
    if t >= tb:
        text(ctx, f"約{SH['STAIR']}秒", 595, (sy0 + sy1) / 2, 30, INK, alpha=a * fade(t, tb, 0.3))
    queue_row(ctx, Q_Y["A"], SH["Q1"], S("c5_5") + 0.1, S("c5_5") + 1.8, t, a, "片側あけ（立つ側）")
    queue_row(ctx, Q_Y["B"], SH["Q2"], S("c5_4") + 0.2, S("c5_4") + 1.9, t, a, "2列で立つ")
    for key, cut, tc in (("B", SH["Q2"], S("c5_4") + 1.9), ("A", SH["Q1"], S("c5_5") + 1.8)):
        if t >= tc + 0.6:
            y = Q_Y[key]
            xm = Q_FRONT - (cut + 4) * Q_SP
            yt = sy1 + 14 if key == "B" else sy0 - 14
            pen_arrow(ctx, xm, y + (-30 if key == "B" else 30), xm + 120, yt, RED, seed=83 + len(key), width=4,
                      alpha=a * fade(t, tc + 0.6, 0.3), head=14)
            if key == "B":
                text(ctx, "階段へ", xm + 40, (y + yt) / 2 + 6, 28, RED, align="right", alpha=a * fade(t, tc + 0.8, 0.3))
            else:
                text(ctx, "階段へ", xm + 130, (y + yt) / 2 + 34, 28, RED, align="left", alpha=a * fade(t, tc + 0.8, 0.3))


def L_end(ctx, t):
    a = fade(t, S("ch6") + 0.2, 0.4)
    mini_sticky(ctx, "朝の混雑（電車が次々に着く）", 560, 278, 34, "yellow", a=a, tilt=-0.02)
    draw_train(ctx, 180, 280, a)
    grp(ctx, a, intro_blocks, t, TAU_MAX_I, 1.0, 1.0, S("ch6") - 10.0, S("ch6") - 10.0)


LEFTS = [L_open, L_share, L_rush, L_slow, L_deep, L_stairs, L_end]


# ============================================================
# 右ページ
# ============================================================
def R_open(ctx, t):
    text(ctx, "片側あけが得になるのは、", RX, 175, 54, INK, align="left")
    text(ctx, "歩く人が何割のとき？", RX, 255, 64, INK, align="left")
    t5 = S("c0_5") + 0.3
    if t >= t5:
        pen_line(ctx, RX - 4, 296, RX + text_width("歩く人が何割のとき？", 64) + 6, 292, RED, seed=7, width=7,
                 progress=clamp01((t - t5) / 0.5))
    d = fade(t, S("c0_2") - 0.3, 0.35)
    if d > 0.003:
        wr(ctx, "片側あけ: 片側に立ち、もう片側を歩く", RX, 380, 34, C_ORANGE, S("c0_3b") + 0.2, t, alpha=d, cps=12)
        wr(ctx, "2列で立つ: 全員が左右に並んで立つ", RX, 445, 34, C_BLUE, S("c0_4b") + 0.2, t, alpha=d, cps=12)
        wr(ctx, "どちらが早く上に着く？", RX, 530, 40, INK, S("c0_4d") + 0.3, t, alpha=d, cps=11)
    text(ctx, "コンピューターの中で試した駅", RX, 690, 30, PENCIL, align="left", bold=False, alpha=fade(t, S("c0_5b") + 0.5, 0.4))
    a = fade(t, T_LAY, 0.35) * out_fade(t, S("c0_2") - 0.3, 0.35)
    if a > 0.003:
        legend_at(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], RCX, 360, size=32, a=a)
        tau = tau_intro(t)
        k = train_no(tau)
        if t >= T_PEEK:
            text(ctx, f"電車 {k}本目" if tau < TAU_MAX_I - 1 else f"電車 {N_TRAIN}本が着いた", RX, 440, 36, INK, align="left", alpha=a)
            text(ctx, "▶▶ 早回し", 1790, 440, 32, PENCIL, align="right", bold=False, alpha=a * out_fade(t, T_FF1(), 0.3))
    wr(ctx, "どこで入れ替わる？", RX, 605, 46, INK, S("c0_9b") + 0.3, t)


def R_share(ctx, t):
    tb = S("c1_10")
    a = out_fade(t, tb - 0.2, 0.4)
    if a > 0.003:
        wr(ctx, "呼びかけ: 立ち止まって乗る", RX, 135, 30, PENCIL, S("c1_5") + 0.8, t, alpha=a, bold=False)
        for tk, s_, x, y, col, tilt in ((S("c1_1") + 0.3, "電車1本・100人", RX, 205, "yellow", -0.02),
                                        (S("c1_2") + 0.4, f"高さ ビル{SH['F17']}階ぶん", RX, 280, "yellow", 0.01),
                                        (S("c1_2b") + 0.4, f"立って{SH['RIDE']}秒", RX + 400, 280, "yellow", -0.02),
                                        (mid("c1_2b", 0.7), "立つ人 1段あける", RX, 360, "blue", 0.015),
                                        (E("c1_2b") + 0.2, "歩く人 2段あける", RX + 350, 360, "mint", -0.02)):
            if t >= tk:
                mini_sticky(ctx, s_, x, y, 34, col, a=a * fade(t, tk), align="left", tilt=tilt)
        wr(ctx, "比べる: 上に着くまでの時間（全員の平均）", RX, 440, 34, INK, S("c1_4") + 0.3, t, alpha=a, cps=12)
        wr(ctx, "（下に着いた時から数える。並んで待つ時間も入る）", RX, 490, 28, PENCIL, S("c1_4b") + 0.3, t, alpha=a, bold=False, cps=13)
        b = a * out_fade(t, S("c1_7") - 0.2, 0.3)
        wr(ctx, "予想", RX, 570, 34, RED, S("c1_6") + 0.1, t, alpha=b)
        wr(ctx, "歩く人が半分くらいいて、", RX + 90, 570, 34, INK, S("c1_6b") + 0.3, t, alpha=b, cps=12)
        wr(ctx, "やっと片側あけが早くなる？", RX + 90, 620, 34, INK, mid("c1_6b", 0.45), t, alpha=b, cps=12)
        c = a * fade(t, S("c1_7") - 0.1, 0.3)
        wr(ctx, "歩く人がひとりもいない駅（0%）", RX, 570, 36, INK, S("c1_7") + 0.1, t, alpha=c, cps=12)
        wr(ctx, f"→ 片側あけが {SH['LOSS0']}秒遅い", RX, 630, 40, RED, S("c1_9") + 0.3, t, alpha=c)
    draw_graph(ctx, t, fade(t, tb - 0.1, 0.4))


def R_rush(ctx, t):
    a = out_fade(t, S("c2_5") - 0.2, 0.4)
    if a > 0.003:
        wr(ctx, "朝の混雑", RX, 165, 56, INK, S("ch2") + 0.4, t, cps=8, alpha=a)
        if t >= S("c2_1") + 0.3:
            mini_sticky(ctx, "100秒おきに100人", RX, 250, 36, "yellow", a=a * fade(t, S("c2_1") + 0.3), align="left")
        if t >= S("c2_2") + 0.2:
            mini_sticky(ctx, "電車15本", RX + 380, 250, 36, "yellow", a=a * fade(t, S("c2_2") + 0.2), align="left", tilt=0.015)
        wr(ctx, "歩く人 4人に1人", RX, 335, 38, INK, S("c2_1b") + 0.3, t, alpha=a)
        wr(ctx, "電車1本なら 同じ時間だった", RX, 420, 38, INK, S("c2_4") + 0.2, t, alpha=a)
        wr(ctx, "→ 朝の混雑では ずっと遅い", RX, 480, 42, RED, S("c2_4b") + 0.2, t, alpha=a)
    g = fade(t, S("c2_5") - 0.1, 0.4) * out_fade(t, S("c2_10") - 0.2, 0.4)
    draw_graph(ctx, t, g)
    w = fade(t, S("c2_10") - 0.1, 0.4)
    if w > 0.003:
        wr(ctx, "なぜ？", RX, 165, 60, INK, S("c2_10") + 0.1, t, cps=8, alpha=w)
        if t >= S("c2_12") + 0.3:
            mini_sticky(ctx, f"立つ側が運べるのは 1秒に約{SH['CAP']}人", RX, 260, 34, "blue", a=w * fade(t, S("c2_12") + 0.3), align="left")
        wr(ctx, "（1段あける＝0.8mおき・秒速0.5m）", RX, 318, 28, PENCIL, S("c2_11") + 0.3, t, alpha=w, bold=False, cps=12)
        if t >= mid("c2_12", 0.6):
            mini_sticky(ctx, "来るのは 1秒に1人", RX, 385, 34, "yellow", a=w * fade(t, mid("c2_12", 0.6)), align="left", tilt=0.015)
        wr(ctx, f"立つ人が{SH['CAP6']}割を超える", RX, 460, 40, RED, S("c2_13") + 0.2, t, alpha=w, cps=12)
        wr(ctx, "→ 行列が伸び続ける", RX + 40, 512, 40, RED, S("c2_13c") + 0.2, t, alpha=w, cps=12)
        s_ = f"1 − {SH['CAP']} ≒ {ihalf((1 - RATE_STAND) * 10)}割"
        wr(ctx, s_, RX + 40, 600, 52, INK, S("c2_14") + 0.3, t, alpha=w, cps=10)
        if t >= mid("c2_14", 0.6):
            ww = text_width(s_, 52)
            pen_circle(ctx, RX + 40 + ww / 2, 600, ww / 2 + 30, 40, RED, seed=91, width=6,
                       progress=clamp01((t - mid("c2_14", 0.6)) / 0.5), alpha=w)
        if t >= S("c2_13b") + 0.3:
            mini_sticky(ctx, f"2列 1秒に約{SH['CAP2']}人", RX + 560, 600, 30, "blue", a=w * fade(t, S("c2_13b") + 0.3), tilt=-0.02)
        if t >= S("c2_15") + 0.2:
            mini_sticky(ctx, f"電車が90秒おきなら 約{SH['X90']}%", 1610, 680, 28, "yellow", a=w * fade(t, S("c2_15") + 0.2), tilt=-0.015)


def R_slow(ctx, t):
    wr(ctx, "電車1本・歩く人 4人に1人（同じ時間だった駅）", RX, 165, 34, INK, S("c3_1") + 0.2, t, cps=12)
    wr(ctx, "歩く人の平均（並ぶ時間も入れて）", RX, 250, 36, INK, S("c3_1b") + 0.2, t, cps=12)
    wr(ctx, f"{SH['W0']}秒", RX + 40, 320, 56, INK, mid("c3_1b", 0.7), t, cps=8)
    wr(ctx, f"→ {SH['W1']}秒", RX + 200, 320, 56, RED, S("c3_4") + 0.3, t, cps=8)
    wr(ctx, "歩く側の2番目の人だけ ゆっくり", RX, 420, 40, INK, S("c3_2") + 0.2, t, cps=11)
    wr(ctx, "前の人を 追い越せない", RX, 490, 40, INK, S("c3_3") + 0.2, t, cps=11)
    if t >= S("c3_6") + 0.2:
        mini_sticky(ctx, "1人で、後ろ全員", RX + 380, 610, 44, "pink", fg=RED, a=fade(t, S("c3_6") + 0.2), tilt=-0.02)


def R_deep(ctx, t):
    wr(ctx, "長さを変える（電車1本）", RX, 165, 42, INK, S("c4_1b") + 0.2, t, cps=11)
    a = fade(t, S("c4_1b") + 0.6, 0.3)
    text(ctx, "高さ", RX + 10, 240, 30, PENCIL, align="left", bold=False, alpha=a)
    text(ctx, "同じ時間になる歩く人の割合", RX + 260, 240, 30, PENCIL, align="left", bold=False, alpha=a)
    pen_line(ctx, RX, 268, RX + 720, 268, PENCIL, seed=93, width=2.5, alpha=a)
    rows = ((f"ビル{SH['F3']}階ぶん", f"約{SH['X3']}%", S("c4_2b") + 0.4, 315), (f"ビル{SH['F17']}階ぶん", f"約{SH['X17']}%", S("c4_1b") + 0.8, 375),
            (f"ビル{SH['F40']}階ぶん", f"約{SH['X40']}%", S("c4_3b") + 0.4, 435))
    for lab, v, t0, y in rows:
        wr(ctx, lab, RX + 10, y, 36, INK, t0, t)
        wr(ctx, v, RX + 290, y, 40, RED if lab.endswith(f"{SH['F40']}階ぶん") else INK, t0 + 0.3, t)
    wr(ctx, "長いほど、少ない人数で早くなる", RX, 515, 38, INK, S("c4_5") + 0.3, t, cps=11)
    wr(ctx, "でも、長いほど歩く人は減る", RX, 580, 38, RED, S("c4_6") + 0.3, t, cps=11)
    if t >= mid("c4_6", 0.8):
        b = fade(t, mid("c4_6", 0.8), 0.3)
        pen_arrow(ctx, RX + 590, 505, RX + 660, 545, INK, seed=95, width=4, alpha=b, head=14)
        pen_arrow(ctx, RX + 560, 600, RX + 660, 562, RED, seed=96, width=4, alpha=b, head=14)
        text(ctx, "？", RX + 700, 548, 56, RED, alpha=b)
    wr(ctx, "海外の試験: とても長いエスカレーターで", RX, 645, 28, PENCIL, S("c4_7") + 0.3, t, bold=False, cps=13)
    wr(ctx, "2列で立つ → 約3割多く通れた", RX + 40, 680, 28, PENCIL, S("c4_7a") + 0.3, t, bold=False, cps=13)


def R_stairs(ctx, t):
    wr(ctx, "横に階段がある駅", RX, 165, 44, INK, S("c5_1") + 0.2, t, cps=10)
    if t >= S("c5_2") + 0.3:
        mini_sticky(ctx, f"階段 約{SH['STAIR']}秒（仮に決めた値）", RX, 250, 34, "yellow", a=fade(t, S("c5_2") + 0.3), align="left")
    if t >= mid("c5_2", 0.6):
        mini_sticky(ctx, f"立って乗る {SH['RIDE']}秒", RX + 480, 250, 34, "blue", a=fade(t, mid("c5_2", 0.6)), align="left", tilt=0.015)
    wr(ctx, "階段は 行列に並ばなくてすむ", RX, 340, 38, INK, S("c5_3") + 0.2, t, cps=11)
    wr(ctx, "→ 行列が長いほど 階段が有利", RX + 40, 395, 38, INK, S("c5_3b") + 0.2, t, cps=11)
    wr(ctx, f"2列の行列: 前に{SH['Q2']}人 → 階段が早い", RX, 460, 36, INK, S("c5_4") + 0.4, t, cps=12)
    if t >= S("c5_5") + 0.4:
        mini_sticky(ctx, f"2列なら前に約{SH['Q2']}人・片側あけなら前に約{SH['Q1']}人", RX + 370, 550, 32, "pink", fg=RED,
                    a=fade(t, S("c5_5") + 0.4), tilt=-0.02)
    wr(ctx, "速く上れる人は、もっと短い行列でも階段", RX, 640, 32, PENCIL, S("c5_6") + 0.3, t, bold=False, cps=12)


def R_end(ctx, t):
    a = fade(t, S("ch6") + 0.3, 0.4)
    s_ = "片側あけが得になるのは、歩く人が何割のとき？"
    text(ctx, s_, RX, 150, 34, INK, align="left", alpha=a)
    if t >= mid("c6_2", 0.3):
        pen_line(ctx, RX - 4, 178, RX + text_width(s_, 34) + 4, 174, RED, seed=97, width=5, progress=clamp01((t - mid("c6_2", 0.3)) / 0.5))
    wr(ctx, "① 電車1本 → 4人に1人で同じ時間", RX, 250, 38, INK, S("c6_1b") + 0.2, t, cps=11)
    wr(ctx, "② 次々に着く朝 → 4割くらいで片側あけが早い", RX, 330, 36, RED, S("c6_2") + 0.3, t, cps=12)
    wr(ctx, "③ 長いほど 少ない人数で片側あけが早い", RX, 410, 36, INK, S("c6_3") + 0.2, t, cps=12)


RIGHTS = [R_open, R_share, R_rush, R_slow, R_deep, R_stairs, R_end]


# ============================================================
# グラフ（右ページ）: 横＝歩く人の割合、縦＝片側あける − 2列で立つ（秒）。1章で点と線、2章で混雑の線を重ねる
# ============================================================
PX0, PX1, PY0, PY1 = 1150.0, 1760.0, 190.0, 600.0
YLO, YHI = -40.0, 80.0


def gx(p):
    return PX0 + np.asarray(p, float) / 0.5 * (PX1 - PX0)


def gy(d):
    return PY1 - (np.asarray(d, float) - YLO) / (YHI - YLO) * (PY1 - PY0)


_COLS = {}
_TCOL = {}
_SHARE = {}
DOT_COL = "#5b6378"


def col_surface(p):
    """割合 p の1万回（電車1本）の 片側−2列 を、細い帯の画像に点で打つ"""
    if p in _COLS:
        return _COLS[p]
    if not _SHARE:
        sm = np.load(CACHE / "share_main.npz")
        _SHARE["A"], _SHARE["B"] = sm["A"][:, :, Ls_LONG.index(L_BASE)], sm["B"][:, Ls_LONG.index(L_BASE)]
    d = _SHARE["A"][:, P_GRID.index(p)] - _SHARE["B"]
    rng = np.random.default_rng(int(p * 1000) + 3)
    W_, H_ = 40, int(PY1 - PY0) + 40
    xs = 20 + rng.uniform(-12, 12, len(d))
    ys = gy(d) - PY0 + 20
    ix, iy = np.round(xs).astype(int), np.round(ys).astype(int)
    cov = np.zeros(W_ * H_)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x2, y2 = ix + dx, iy + dy
            ok = (x2 >= 0) & (x2 < W_) & (y2 >= 0) & (y2 < H_)
            cov += np.bincount((y2 * W_ + x2)[ok], minlength=W_ * H_)
    al = 1 - (1 - 0.05) ** cov
    c = hexrgb(DOT_COL)
    out = np.zeros((H_, W_, 4), np.uint8)
    for ch, kk in ((2, 0), (1, 1), (0, 2)):
        out[:, :, kk] = (c[ch] * al * 255).reshape(H_, W_).astype(np.uint8)
    out[:, :, 3] = (al * 255).reshape(H_, W_).astype(np.uint8)
    out = np.ascontiguousarray(out)
    surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, W_, H_, W_ * 4)
    _COLS[p] = (surf, out)
    return _COLS[p]


def t_col(p):
    """ダイヤルが p に届いた時刻"""
    if p not in _TCOL:
        ts = np.arange(S("c1_10"), E("g1b"), 1 / 60)
        _TCOL[p] = next((float(tt) for tt in ts if dial_p(tt) >= p - 1e-6), float(ts[-1]))
    return _TCOL[p]


def pen_poly(ctx, pts, col, width, a):
    if len(pts) < 2 or a <= 0.003:
        return
    ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def draw_graph(ctx, t, a):
    if a <= 0.003:
        return
    # 軸
    pen_line(ctx, PX0 - 6, PY0 - 10, PX0 - 6, PY1 + 3, INK, seed=3, width=4.5, alpha=0.85 * a)
    pen_line(ctx, PX0 - 6, PY1 + 3, PX1 + 10, PY1 + 3, INK, seed=4, width=4.5, alpha=0.85 * a)
    y0 = float(gy(0))
    ctx.set_source_rgba(*hexrgb(INK, 0.55 * a))
    ctx.set_line_width(2)
    ctx.set_dash([8, 6])
    ctx.move_to(PX0, y0)
    ctx.line_to(PX1 + 6, y0)
    ctx.stroke()
    ctx.set_dash([])
    for v in (-20, 0, 20, 40, 60):
        yy = float(gy(v))
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(PX0 - 14, yy)
        ctx.line_to(PX0 - 6, yy)
        ctx.stroke()
        text(ctx, f"{v:+d}" if v else "0", PX0 - 20, yy, 28, INK, align="right", bold=False, alpha=a)
    for k in range(0, 6):
        xx = float(gx(k / 10))
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, PY1 + 3)
        ctx.line_to(xx, PY1 + 12)
        ctx.stroke()
        text(ctx, f"{k * 10}%", xx, PY1 + 34, 28, INK, bold=False, alpha=a)
    text(ctx, "歩く人の割合", (PX0 + PX1) / 2, PY1 + 72, 30, INK, bold=False, alpha=a)
    text(ctx, "片側あけ − 2列で立つ（秒）", PX0 - 70, PY0 - 40, 28, INK, align="left", bold=False, alpha=a)
    text(ctx, "↑ 2列が早い", PX0 + 16, float(gy(72)), 28, C_BLUE, align="left", alpha=a)
    text(ctx, "↓ 片側あけが早い", PX1, float(gy(-32)), 28, C_ORANGE, align="right", alpha=a)
    # 1万回の点（ダイヤルが届いた割合から）
    ctx.save()
    ctx.rectangle(PX0 - 4, PY0 - 6, PX1 - PX0 + 20, PY1 - PY0 + 8)
    ctx.clip()
    for p in P_TABLE:
        tc = t_col(p)
        if t < tc:
            continue
        surf, _ = col_surface(p)
        ctx.set_source_surface(surf, float(gx(p)) - 20, PY0 - 20)
        ctx.paint_with_alpha(a * clamp01((t - tc) / 0.35))
    # 電車1本の平均の線（ダイヤルに合わせて伸びる）
    pmax = max(dial_p(min(t, E("g1b"))), 0.5 if t >= E("g1b") else 0.0)
    pts = [(float(gx(c["p"])), float(gy(c["diff"]))) for c in RES["ch1"]["curve"] if c["p"] <= pmax + 1e-9]
    pen_poly(ctx, pts, INK, 5, a)
    # 混雑の線（2章）
    tr_ = S("g2b") + 0.3
    if t >= tr_:
        u = clamp01((t - tr_) / 2.4)
        cv = [c for c in RES["ch2"]["curve"]]
        pts2 = [(float(gx(c["p"])), float(gy(c["diff"]))) for c in cv if c["p"] <= 0.5 * u + 1e-9]
        pen_poly(ctx, pts2, RED, 5, a)
    ctx.restore()
    if t >= E("g1b") - 0.3:
        text(ctx, "電車1本", float(gx(0.16)), float(gy(31)), 30, INK, alpha=a * fade(t, E("g1b") - 0.3, 0.3))
    if t >= tr_ + 1.0:
        text(ctx, "混雑 ↑", float(gx(0.27)) - 14, PY0 + 22, 30, RED, align="right", alpha=a * fade(t, tr_ + 1.0, 0.3))
    # 互角の所
    tx1 = S("c1_11") + 0.2
    if t >= tx1:
        cx_ = float(gx(RES["ch1"]["cross"]))
        pen_circle(ctx, cx_, y0, 26, 26, RED, seed=101, width=5, progress=clamp01((t - tx1) / 0.5), alpha=a)
        text(ctx, f"4人に1人（約{SH['X1']}%）", cx_, y0 - 56, 32, RED, alpha=a * fade(t, tx1 + 0.2, 0.3))
    if S("c1_14c") <= t < S("ch2"):
        text(ctx, "4人に1人で同じ時間", PX1, float(gy(60)), 32, INK, align="right", alpha=a * fade(t, S("c1_12") + 0.3, 0.3))
    tx2 = S("c2_6") + 0.2
    if t >= tx2:
        cx_ = float(gx(RES["ch2"]["cross"]))
        pen_circle(ctx, cx_, y0, 26, 26, RED, seed=102, width=5, progress=clamp01((t - tx2) / 0.5), alpha=a)
        text(ctx, f"{SH['X2_10']}割の少し手前\n（約{SH['X2P']}%）", 1690, float(gy(22)), 30, RED, alpha=a * fade(t, tx2 + 0.2, 0.3))
    for key, p, tq, dxl in (("A30", 0.3, S("c2_7") + 0.3, -1), ("A40", 0.4, S("c2_8") + 0.2, -1)):
        if t >= tq:
            d = next(c["diff"] for c in RES["ch2"]["curve"] if abs(c["p"] - p) < 1e-9)
            b = a * fade(t, tq, 0.3)
            xx, yy = float(gx(p)), float(gy(d))
            ctx.set_source_rgba(*hexrgb(RED, b))
            ctx.arc(xx, yy, 9, 0, 2 * math.pi)
            ctx.fill()
            text(ctx, f"{ihalf(p * 10)}割", xx - 16, yy + (0 if p < 0.35 else 30), 30, RED, align="right", alpha=b)
    if t >= S("c2_9") + 0.3:
        mini_sticky(ctx, "3割と4割の間で入れ替わる", 1555, 330, 34, "pink", fg=RED, a=a * fade(t, S("c2_9") + 0.3), tilt=-0.02)


# ============================================================
# 右ページ下の「2つの数字」（1章で出して、終了画面まで出しっぱなし）
# ============================================================
NB = (1030, 712, 1800, 905)
CELLX = (1222, 1608)


def box_keys():
    sec = lambda v: f"{v}秒"
    c1, cm, c0 = "電車1本・4人に1人が歩く", "朝の混雑・4人に1人が歩く", "電車1本・誰も歩かない"
    return [
        (S("c1_4") + 0.3, "上に着くまでの時間の平均", "?秒", "?秒"),
        (S("c1_8") + 0.2, c0, sec(SH["A0"]), "?秒"),
        (S("c1_8b") + 0.2, c0, sec(SH["A0"]), sec(SH["B1"])),
        (S("c1_11") + 0.3, c1, sec(SH["B1"]), sec(SH["B1"])),
        (S("c2_3") + 0.2, cm, sec(SH["AD"]), "?秒"),
        (S("c2_3b") + 0.2, cm, sec(SH["AD"]), sec(SH["BR"])),
        (S("c2_7") + 0.4, "朝の混雑・3割が歩く", sec(SH["A30"]), sec(SH["BR"])),
        (S("c2_8") + 0.3, "朝の混雑・4割が歩く", sec(SH["A40"]), sec(SH["BR"])),
        (S("ch3") + 0.6, c1, sec(SH["B1"]), sec(SH["B1"])),
        (S("c3_5") + 0.2, "歩く側の2番目の人がゆっくり", sec(SH["AS"]), sec(SH["B3"])),
        (S("ch4") + 0.6, "", "—", "—"),   # 4・5章は声で言わない数字を出さない（薄くして中身は「—」）
        (S("c6_1b") + 0.2, c1, sec(SH["B1"]), sec(SH["B1"])),
        (S("c6_2") + 0.2, "朝の混雑・4割が歩く", sec(SH["A40"]), sec(SH["BR"])),
    ]


BOX_DIM = 0.4


def draw_box(ctx, t):
    keys = box_keys()
    t0 = keys[0][0]
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3)
    i = max([k for k, kk in enumerate(keys) if kk[0] <= t + 0.1] or [0])
    tk, cap, va, vb = keys[i]
    prev = keys[i - 1] if i > 0 else None
    u = fade(t, tk, 0.35)
    dim = lambda k: BOX_DIM if k[2] == "—" else 1.0
    a *= dim(keys[i]) * u + (dim(prev) if prev else 1.0) * (1 - u)
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to((x0 + x1) / 2, y0 + 62)
    ctx.line_to((x0 + x1) / 2, y1 - 18)
    ctx.stroke()
    cy_cap = y0 + 34
    if prev is None or prev[1] == cap:
        text(ctx, cap, (x0 + x1) / 2, cy_cap, 28, PENCIL, bold=False, alpha=a)
    else:
        text(ctx, cap, (x0 + x1) / 2, cy_cap, 28, PENCIL, bold=False, alpha=a * u)
        text(ctx, prev[1], (x0 + x1) / 2, cy_cap, 28, PENCIL, bold=False, alpha=a * (1 - u))
    lf.write_on(ctx, "片側あけ", CELLX[0], y0 + 86, 34, C_ORANGE, clamp01((t - t0) / 0.5), align="center", alpha=a)
    lf.write_on(ctx, "2列で立つ", CELLX[1], y0 + 86, 34, C_BLUE, clamp01((t - t0 - 0.2) / 0.5), align="center", alpha=a)
    for cx_, v_new, v_old, col in ((CELLX[0], va, prev[2] if prev else va, C_ORANGE), (CELLX[1], vb, prev[3] if prev else vb, C_BLUE)):
        if prev is None or v_new == v_old:
            text(ctx, v_new, cx_, y0 + 150, 64, col, alpha=a)
        else:
            text(ctx, v_old, cx_, y0 + 150, 64, col, alpha=a * (1 - u))
            sc = 1 + 0.25 * (1 - ease_out(clamp01((t - tk) / 0.3)))
            ctx.save()
            ctx.translate(cx_, y0 + 150)
            ctx.scale(sc, sc)
            text(ctx, v_new, 0, 0, 64, col, alpha=a * u)
            ctx.restore()


# ============================================================
# 章の付箋・1万回の合図・終了画面・全体
# ============================================================
def T_ES():
    """終了画面の始まり（最後の20秒）。ここからは左右を空け、中央だけに置く"""
    return DUR - 20.0


def end_screen(ctx, t):
    t0 = T_ES()
    b = fade(t, t0 + 0.3, 0.4)
    c4 = S("c6_4")
    text(ctx, "答え", 960, 140, 44, INK, alpha=b)
    rows = [("電車1本 → 4人に1人で同じ時間", 38, INK, S("c6_1b")), (f"次々に着く朝 → {SH['X2_10']}割くらいで片側あけが早い", 36, RED, S("c6_2")),
            ("長いほど 少ない人数で片側あけが早い", 34, INK, S("c6_3"))]
    for k, (s_, sz, col, ts) in enumerate(rows):
        text(ctx, s_, 960, 210 + k * 58, sz, col, alpha=b * fade(t, max(ts, t0 + 0.3), 0.3))
    text(ctx, "呼びかけ: 立ち止まって乗る", 960, 450, 28, PENCIL, bold=False, alpha=b * fade(t, max(c4, t0 + 0.3) + 0.3, 0.4))
    text(ctx, "比べたのは 上に着くまでの時間だけ", 960, 492, 28, PENCIL, bold=False,
         alpha=b * fade(t, max(S("c6_4b"), t0 + 0.3) + 0.3, 0.4))
    tq, t5 = S("c6_5") + 0.05, S("c6_6")
    if t >= tq:
        q = fade(t, tq, 0.35) * (1 - fade(t, t5 - 0.1, 0.3))
        if q > 0.003:
            sticky(ctx, "あなたの駅の\nエスカレーター、10人のうち\n何人が歩いていますか？", 960, 650, 44, "yellow", a=q, tilt=-0.02)
    if t >= t5:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t5) % 3.2 < 0.45 else 0.0
        turtle(ctx, 955, 690, 0.62, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t5 + 0.1, 0.4))
        sticky(ctx, "チャンネル登録\nお願いします", 960, 805, 40, "pink", fg=INK, a=fade(t, t5 + 0.3, 0.4), tilt=-0.015)


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, ch[2], a, size=60)
    tb = S("g1b")
    a = fade(t, tb - 0.1, 0.25) * out_fade(t, tb + 1.5, 0.35)
    if a > 0.003:
        note.banner(ctx, "1万回ずつためす", lf.GUTTER, 470, a=a, t_rel=t - tb)


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def pages(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    ctx.save()
    clip_left(ctx)
    page(ctx, t, LEFTS, idx, t0)
    ctx.restore()
    page(ctx, t, RIGHTS, idx, t0)
    draw_box(ctx, t)
    overlays(ctx, t)


# ============================================================
# 区切り（アイキャッチ・約4秒・声なし）。2026-10-14 ユーザー「『ひと休み』は安っぽい。見開きの左に←ここまで、右に→ここから」
# 見本 out/escalator-long/eyecatch/make_eyecatch_v2.py の形をコピーして、亀を歩かせ・足あとを順に出す
# ============================================================
EC_LEFT = ("混んだ朝は、歩く人が", "{X}割いないと 2列が早い")
EC_RIGHT = ("ゆっくり歩く人や、", "階段があったら？")
EC_PX = (480, 1440)                                   # 左右のページの中央
EC_Y = 860                                            # 亀の高さ
EC_X0, EC_X1 = 330.0, 1590.0                          # 亀が歩く範囲（左ページから右ページへ）
EC_STEP0, EC_STEP = 260.0, 64.0                       # 足あとの点の位置


def T_EC0():
    return S("g_ec")


def T_EC1():
    return S("ch3")


def ec_x(t):
    return lerp(EC_X0, EC_X1, clamp01((t - T_EC0()) / (T_EC1() - T_EC0())))


def ec_step_times():
    """足あとの点 i が出る時刻（亀の位置が 260 + (i+1)×64 を越えたとき）"""
    out = []
    i = 0
    while True:
        need = EC_STEP0 + (i + 1) * EC_STEP
        if need > EC_X1:
            return out
        u = (need - EC_X0) / (EC_X1 - EC_X0)
        if u >= 0:
            out.append(T_EC0() + u * (T_EC1() - T_EC0()))
        i += 1


def ec_arrow(ctx, x0, x1, y, color, seed, a):
    pen_line(ctx, x0, y, x1, y, color, seed=seed, width=7, alpha=a)
    d = 1 if x1 > x0 else -1
    pen_line(ctx, x1, y, x1 - d * 34, y - 24, color, seed=seed + 1, width=7, alpha=a)
    pen_line(ctx, x1, y, x1 - d * 34, y + 24, color, seed=seed + 2, width=7, alpha=a)


def ec_page(ctx, cx, head, lines, back, a):
    hand_title(ctx, head, cx - text_width(head, 104) / 2, 250, 104, seed=4 if back else 6, alpha=a)
    if back:
        ec_arrow(ctx, cx + 210, cx - 230, 345, RED, 11, a)
    else:
        ec_arrow(ctx, cx - 210, cx + 230, 345, RED, 21, a)
    for i, s_ in enumerate(lines):
        hand_title(ctx, s_, cx - text_width(s_, 66) / 2, 520 + i * 96, 66, seed=30 + i + (0 if back else 10), alpha=a)


def eyecatch(ctx, t):
    from engine.brand import turtle
    t0 = T_EC0()
    a = fade(t, t0, 0.5)                              # 左右の文字は最初の0.5秒で出して、最後まで
    left = (EC_LEFT[0], EC_LEFT[1].replace("{X}", str(SH["X2_10"])))
    ec_page(ctx, EC_PX[0], "ここまで", left, True, a)
    ec_page(ctx, EC_PX[1], "ここから", EC_RIGHT, False, a)
    x = ec_x(t)
    n = int(max(0.0, x - EC_STEP0) // EC_STEP)
    for i in range(n):
        px = EC_STEP0 + i * EC_STEP
        ctx.set_source_rgba(0.25, 0.25, 0.3, 0.30)
        ctx.arc(px, EC_Y + 18 + (7 if i % 2 else -7), 6, 0, 2 * math.pi)
        ctx.fill()
    bob = 3 * abs(math.sin((t - t0) * 2 * math.pi * 0.5 * (EC_X1 - EC_X0) / EC_STEP / (T_EC1() - t0) / 2))
    blink = 1.0 if 0.55 < (t - t0) % 1.7 < 0.67 else 0.0
    turtle(ctx, x, EC_Y - bob, 0.5, blink=blink)


def footstep(freq, dur_=0.11):
    """亀の足音（ぽてっ）: 少し下がる短い音＋やわらかい当たり。core.blip と同じ作り方"""
    t_ = _t(dur_)
    f = freq * (1 + 0.5 * np.exp(-t_ * 55))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t_ * 38) * np.minimum(1, t_ * 900)
    rng = np.random.default_rng(int(freq))
    tap = np.convolve(rng.standard_normal(len(t_)), np.ones(12) / 12, mode="same") * np.exp(-t_ * 160) * 0.6
    return body + tap


def draw(ctx, t):
    lf.spread(ctx)
    tes = T_ES()
    e0, e1 = T_EC0(), T_EC1()
    ec = fade(t, e0, 0.35) * out_fade(t, e1 - 0.15, 0.35)
    if ec > 0.997:
        grp(ctx, 1.0, eyecatch, t)
        lf.subtitle(ctx, t, tl)
        return
    if t < tes + 0.6:
        grp(ctx, (1 - fade(t, tes, 0.5)) * (1 - ec), pages, t)
    if ec > 0.003:
        grp(ctx, ec, eyecatch, t)
    if t >= tes:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM・エスカレーターの低い音は 0秒から。効果音はショートの作り方をコピー）
# ============================================================
def band_noise(dur_, lo, hi, seed, rms, edge_lo=40.0, edge_hi=200.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur_)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def esc_hum(dur_):
    """エスカレーターの低い動作音（ショートと同じ）"""
    x = band_noise(dur_, 80.0, 420.0, 3, 0.030, 60.0, 250.0)
    tt = np.arange(len(x)) / SR
    x += 0.010 * np.sin(2 * np.pi * 55 * tt) * (1 + 0.3 * np.sin(2 * np.pi * 0.4 * tt))
    return x * np.minimum(1, tt / 0.3) * np.minimum(1, (dur_ - tt) / 0.6)


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    padw = core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13)
    hum = esc_hum(DUR)
    tt = np.arange(len(hum)) / SR
    e0, e1 = T_EC0(), T_EC1()                           # 区切りの4秒は BGM を少し下げる（入り・出は0.3秒）
    duck = 1 - 0.4 * np.clip(np.minimum((tt - e0 + 0.3) / 0.3, (e1 + 0.3 - tt) / 0.3), 0, 1)
    mx.add(0, padw * duck[:len(padw)], 1.0, bgm=True)
    mx.add(0, hum * np.where(tt < T_ES(), 0.9, 0.3) * duck, 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 7):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    # 電車が着くたび（冒頭・2章・2章の見直し）
    rng = np.random.default_rng(6)
    for t0, F in ((T_PEEK, F_I()), (S("c2_2") + 0.2, F2()),
                  (S("c2_7") + 0.1, TAU_MAX_I / (mid("c2_8", 0.4) - S("c2_7") - 0.1))):
        for k in range(N_TRAIN):
            mx.add(t0 + k * T_RUSH / F, tick(float(rng.uniform(900, 1300)), 0.05), 0.08)
        mx.add(t0, blip(523.3, 0.2), 0.3)
    mx.add(S("c0_8") + 0.3, chord([261.6, 329.6, 392.0], 1.2), 0.3)
    mx.add(0.3, whoosh(1.2), 0.25)                                   # 電車が入ってくる
    for cid in ("c0_3", "c0_4", "c0_6c", "c0_6d"):
        mx.add(S(cid) + 0.2, blip(659.3, 0.12), 0.3)
    mx.add(S("c0_5") + 0.3, blip(784.0, 0.15), 0.3)
    mx.add(T_LAY, whoosh(0.6), 0.2)
    # 1章: 人が上り終えるたびに小さな音（ゆっくりの区間だけ）
    for run, f0 in ((RUN25[0], 1500.0), (RUN25[1], 2100.0)):
        for ex in np.sort(run.ex):
            tv = S("c1_1") + 0.3 + float(ex) / F25
            if tv < S("c1_7") - 0.3:
                mx.add(tv, tick(float(rng.uniform(f0, f0 * 1.6)), 0.03), 0.03)
    for run in RUN0:
        mx.add(S("c1_7") + 0.1 + run.make / F0(), blip(1046.5 if run.mode == "B" else 784.0, 0.25), 0.4)
    # 数字の欄が変わるたび
    for k, (tk, *_r) in enumerate(box_keys()):
        if k > 0 and _r[1] != "—":
            mx.add(tk, bell(659.3 if k % 2 else 784.0, 1.0), 0.3)
    # 1万回
    mx.add(S("g1b") - 0.4, riser(0.9), 0.5)
    beat(mx, S("c1_10") + 0.3, E("g1b") - 0.3, bpm=124, vol=0.22, accel=True)
    mx.add(S("g1b"), shimmer(400, E("g1b") - S("g1b"), seed=2), 0.3)
    mx.add(S("c1_11") + 0.2, bell(880.0, 1.4), 0.45)
    mx.add(S("c2_6") + 0.2, bell(880.0, 1.4), 0.45)
    mx.add(S("g2b") + 0.3, whoosh(0.6), 0.2)
    mx.add(S("c2_9") + 0.3, chord([261.6, 329.6, 392.0], 1.4), 0.35)
    mx.add(S("c2_13") + 0.5, thump(), 0.4)
    mx.add(mid("c2_14", 0.6), bell(784.0, 1.2), 0.4)
    mx.add(S("c3_2") + 0.4, blip(523.3, 0.15), 0.3)
    rng_f = np.random.default_rng(21)                   # 区切り: 足あとの点が出るたびに、亀の足音（高さを少しずつ変える）
    for k, ts_ in enumerate(ec_step_times()):
        f0 = (420.0 if k % 2 else 520.0) * float(rng_f.uniform(0.9, 1.12))
        mx.add(ts_, footstep(f0), 0.32)
    mx.add(S("c3_6") + 0.2, chord([392.0, 493.9, 587.3], 1.2), 0.35)
    for cid in ("c4_2", "c4_3"):
        mx.add(S(cid) + 0.4, blip(659.3, 0.15), 0.3)
    mx.add(mid("c4_6", 0.8), whoosh(0.5), 0.2)
    mx.add(S("c5_4") + 1.9, blip(784.0, 0.2), 0.35)
    mx.add(S("c5_5") + 1.8, blip(784.0, 0.2), 0.35)
    mx.add(S("c6_2") + 0.3, chord([261.6, 329.6, 392.0], 1.4), 0.35)
    mx.add(S("c6_5") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S("c6_6") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻（章ごとに要所を2枚以上）
# ============================================================
def still_times():
    ts = [0.0, 3.0, mid("c0_1b", 0.9), mid("c0_3", 0.9), mid("c0_4", 0.9), mid("c0_5", 0.9), mid("c0_6d", 0.9), T_PEEK + 1.0, E("g0") - 0.5,
          mid("c0_7", 0.9), mid("c0_8", 0.95), mid("c0_9b", 0.9),
          S("ch1") + 0.8, E("c1_2b") + 0.5, mid("c1_4", 0.9), mid("c1_6", 0.9), E("g1a") - 0.3, mid("c1_9", 0.9),
          S("g1b") + 0.8, S("g1b") + 3.0, mid("c1_11", 0.95), mid("c1_13", 0.9),
          S("ch2") + 0.8, S("g2a") + 2.0, mid("c2_3", 0.9), mid("c2_4", 0.9), E("g2b") - 0.3, mid("c2_6", 0.95),
          mid("c2_7", 0.9), mid("c2_8", 0.95), mid("c2_9", 0.9), mid("c2_11", 0.95), mid("c2_13", 0.95), mid("c2_14", 0.95),
          mid("c2_15", 0.9),
          S("ch3") + 0.8, T_EC0() + 2.0, mid("c3_1b", 0.9), mid("c3_2", 0.9), E("g3") - 0.5, mid("c3_4", 0.95), mid("c3_6", 0.9),
          S("ch4") + 0.8, mid("c4_2", 0.95), mid("c4_3", 0.95), mid("c4_6", 0.95), mid("c4_7", 0.95),
          S("ch5") + 0.8, mid("c5_2", 0.95), mid("c5_4", 0.95), mid("c5_5", 0.95), mid("c5_6", 0.9),
          S("ch6") + 0.8, mid("c6_2", 0.95), T_ES() + 1.0, mid("c6_5", 0.9), S("c6_6") + 1.5, DUR - 0.1]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


# ============================================================
# 文字起こし（雨ロングと同じ形）・読み・画面の文字
# ============================================================
def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字「エスカレーター」と問い）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・映像だけ）")
        else:
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}")
    rows.append("")
    rows.append(f"{_ts(T_ES())}〜{_ts(DUR)} 終了画面の区間（左右を空け、中央に答え・問いかけ・亀）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            rows.append(f"{it.id}: {shown_}\n    → {voice.read_aloud(spoken)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


def scan(step=0.25, scale=0.25):
    """0.25秒ごとに描いて、画面の文字（字幕を除く）の位置と、描いた人の数を集める"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int(DUR / step)
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        DRAWN[0] = 0
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale) for e in core._LOG]
        frames.append((t, ents, DRAWN[0]))
        core._LOG = None
    return frames


def write_screen_text(path, frames, step=0.25):
    seen = {}
    for t, ents, _n in frames:
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


OVERLAY_OK = set(CH_TITLES) | {"1万回ずつためす"}   # 章の付箋・1万回の合図は、わざと上に重ねている（不透明の付箋）


def overlaps(frames, step=0.25, need=3, shrink=3.0):
    """文字どうしの重なり（同じ2つの文字が need 回続けて＝0.5秒以上重なったら）"""
    runs, bad = {}, {}
    for t, ents, _n in frames:
        boxes = [(s_, x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink) for s_, x0, y0, x1, y1 in ents if s_ not in OVERLAY_OK]
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


# ============================================================
# 場面の照合（画面と声の数字が data.json と合っているか・見本の回・文字の重なり・字幕・終了画面・長さ）
# ============================================================
def scene_checks(frames=None):
    import re as _re
    sd = SEEDS
    c1, c2, c3m, c5 = RES["ch1"], RES["ch2"], RES["ch3"]["main"], RES["ch5"]
    txt = lambda i: tl.clip(i).text
    has = lambda i, s_: float(s_ in txt(i))
    checks = [
        # ---- 声と画面の数字 = data.json（四捨五入）。v6 では声の数字を減らし、細かい数字は付箋・札・欄だけ ----
        ("1章「137秒」＝ 割合0%・片側あけの平均", SH["A0"], 137, 0), ("1章 声「137秒」", has("c1_8", f"{SH['A0']}秒"), 1, 0),
        ("1章「100秒」＝ 2列の平均", SH["B1"], 100, 0), ("1章 声「100秒」", has("c1_8b", f"{SH['B1']}秒"), 1, 0),
        ("1章 付箋「37秒遅い」", SH["LOSS0"], 37, 0),
        ("1章「4人に1人」＝ 同じ時間になる割合 約25%", SH["X1"], 25, 0),
        ("1章 声「4人に1人」", has("c1_11", "4人に1人") * has("c1_14c", "4人に1人"), 1, 0),
        ("1章 数字の欄「100秒｜100秒」（同じ時間の所で 片側＝2列。25%の差 |−0.4| < 0.5秒）", abs(_r1[0.25]["diff"]), 0, 0.5),
        ("1章 声「100人」＝ 電車1本の人数", float(N == 100 and has("c1_1", "100人") and has("c1_13b", "100人")), 1, 0),
        ("1章 付箋「高さ ビル6階ぶん」（1階＝約3m で 17.5m）", SH["F17"], 6, 0),
        ("1章 付箋「立って70秒」", SH["RIDE"], 70, 0),
        ("1章 付箋「立つ人 1段あける」（2段に1人＝モデルの平均）", GS_MEAN - 1, 1, 0),
        ("1章 付箋「歩く人 2段あける」（モデル 2.8段に1人＝1.8段あける・±0.25）", GW_MEAN - 1, 2, 0.25),
        ("1章 声「1万回」", float(N_TRIALS == 10000 and has("c1_10b", "1万回")), 1, 0),
        ("4章 声「6階」（これまでのエスカレーターの高さ 17.5m）", has("c4_1z", f"{SH['F17']}階"), 1, 0),
        ("1章「冒頭の2つの駅は、どちらもこの答え（4人に1人）より歩く人が多い」", float(0.3 > _c1["cross"] and 0.4 > _c1["cross"]), 1, 0),
        ("2章「206秒」（ショートと同じ設定の混雑）", SH["AD"], 206, 0), ("2章 声「206秒」", has("c2_3", f"{SH['AD']}秒"), 1, 0),
        ("2章「2列は100秒」", SH["BR"], 100, 0), ("2章 声「100秒」", has("c2_3b", f"{SH['BR']}秒"), 1, 0),
        ("2章 声「100人」（電車が着くたび）", has("c2_1", "100人"), 1, 0),
        ("2章「ずっと遅くなる」（2倍以上）", float(c2["default"]["A"] / c2["B_mean"] >= 2), 1, 0),
        ("2章「4割より少し少ない」（混雑の同じ時間 37.3%：四捨五入で4割・4割未満）", float(SH["X2_10"] == 4 and _c2["cross"] < 0.4), 1, 0),
        ("2章 声「4割より少し少ない」", has("c2_6", f"{SH['X2_10']}割より少し少ない"), 1, 0), ("2章 札「約37%」", SH["X2P"], 37, 0),
        ("2章 欄「3割なら154秒」", SH["A30"], 154, 0), ("2章 欄「4割なら90秒」", SH["A40"], 90, 0),
        ("2章「3割の駅は2列よりずっと遅い」", float(_r2[0.3]["A"] > _r2[0.3]["B"] + 30), 1, 0),
        ("2章「4割の駅は2列より早い」", float(_r2[0.4]["A"] < _r2[0.4]["B"]), 1, 0),
        ("2章 付箋「立つ側が運べるのは1秒に約0.6人」（実測）", SH["CAP"], 0.6, 0),
        ("2章「来るのは1秒に1人」（100秒おきに100人）", N / T_RUSH, 1.0, 0),
        ("2章 声「6割」（0.625 の一の位）", SH["CAP6"], 6, 0), ("2章 声「6割」", has("c2_12", f"{SH['CAP6']}割") * has("c2_13", f"{SH['CAP6']}割"), 1, 0),
        ("2章 声「4割くらいいれば運び切れる」（1 − 0.625 の一の位）", ihalf((1 - RATE_STAND) * 10), 4, 0),
        ("2章 付箋「2列 1秒に約1.2人」（2列の実測 1.17）", SH["CAP2"], 1.2, 0),
        ("2章「2列なら全員運び切れる」（2列の実測 > 1人/秒）", float(_cap["both_1500"]["sim"] > N / T_RUSH), 1, 0),
        ("2章 付箋「90秒おきなら約42%」", SH["X90"], 42, 0),
        ("3章「47秒」（歩く人の平均・基準）", SH["W0"], 47, 0), ("3章 声「47秒」", has("c3_1b", f"{SH['W0']}秒"), 1, 0),
        ("3章「68秒」（2番目の人がゆっくり。68.49 の四捨五入）", SH["W1"], 68, 0), ("3章 声「68秒」", has("c3_4", f"{SH['W1']}秒"), 1, 0),
        ("3章 欄「105秒」", SH["AS"], 105, 0),
        ("3章「100人全体でも片側あけが遅い」", float(c3m["slow_all"] > c3m["B"] and SH["B3"] == 100), 1, 0),
        ("4章「1階ぶん」＝ 3m", SH["F3"], 1, 0), ("4章「13階ぶん」＝ 40m", SH["F40"], 13, 0),
        ("4章 声「1階」「13階」", has("c4_2", f"{SH['F3']}階") * has("c4_3", f"{SH['F40']}階"), 1, 0),
        ("4章「3割くらい」（3m の同じ時間 31.9%）", SH["X3_10"], 3, 0), ("4章 声「3割」", has("c4_2b", f"{SH['X3_10']}割"), 1, 0),
        ("4章「2割くらい」（40m の同じ時間 18.9%）", SH["X40_10"], 2, 0), ("4章 声「2割」", has("c4_3b", f"{SH['X40_10']}割"), 1, 0),
        ("4章 札「約32%」「約19%」", (SH["X3"], SH["X40"]) == (32, 19), 1, 0),
        ("4・5章 数字の欄は「—」（声で言わない数字を出さない）", float(any(k[2] == "—" and S("ch4") < k[0] < S("c4_1") for k in box_keys())
                                                      and not any(S("c4_1") <= k[0] < S("ch6") for k in box_keys())), 1, 0),
        ("5章 付箋「階段 約88秒」（階段 0.2m/秒）", SH["STAIR"], 88, 0),
        ("5章「立って乗るより少し長くかかる」（88 > 70）", float(SH["STAIR"] > SH["RIDE"]), 1, 0),
        ("5章「21人」（2列）", SH["Q2"], 21, 0), ("5章 声「20人くらい」（21 を十の位で丸めた値）", has("c5_4", f"{ihalf(SH['Q2'] / 10) * 10}人くらい"), 1, 0),
        ("5章「21人」＝ 差17.5秒 × 2列の実測（±1.5人）", SH["Q2"], _c5["extra"][0] * _cap["both_1500"]["sim"], 1.5),
        ("5章「11人」＝ 差17.5秒 × 立つ側の実測（±1人）", SH["Q1"], _c5["extra"][0] * _cap["stand_1500"]["sim"], 1.0),
        ("5章「11人」（立つ側）", SH["Q1"], 11, 0), ("5章 声「10人くらい」（11 を十の位で丸めた値）", has("c5_5", f"{ihalf(SH['Q1'] / 10) * 10}人くらい"), 1, 0),
        ("まとめ 声「4人に1人」「4割」", has("c6_1b", "4人に1人") * has("c6_2", f"{SH['X2_10']}割"), 1, 0),
        ("冒頭 声「3割」「4割」＝ 見本の回の割合", has("c0_6c", "3割") * has("c0_6d", "4割"), 1, 0),
        # ---- 見本の回（1万回の中央値の近く） ----
    ]
    for key, v in sd["sample"].items():
        m = sd["median"][key]
        checks.append((f"見本の回 {key}: 1万回の中央値 {m['median']:.1f} から 四分位範囲の半分以内", v, m["median"], 0.5 * m["iqr"]))
    checks += [
        ("見本の回 電車1本25%: 動かす絵の平均＝キャッシュの値（片側あけ）", RUN25[0].mean, sd["sample"]["A1_0.25"], 0.01),
        ("見本の回 電車1本0%: 動かす絵の平均＝キャッシュの値（片側あけ）", RUN0[0].mean, sd["sample"]["A1_0.0"], 0.01),
        ("見本の回 電車1本: 動かす絵の平均＝キャッシュの値（2列）", RUN25[1].mean, sd["sample"]["B1"], 0.01),
        ("見本の回 3章: 動かす絵の平均＝キャッシュの値（2人目がゆっくり）", RUNS3[0].mean, sd["sample"]["slow_all"], 0.01),
        ("見本の回 混雑: 動かす絵の平均＝キャッシュの値（ショートの設定）", RUNR["d"].mean, sd["sample"]["R_def"], 0.01),
        ("見本の回 混雑3割: 動かす絵の平均＝キャッシュの値", RUNR["p30"].mean, sd["sample"]["R_30"], 0.01),
        ("見本の回 混雑4割: 動かす絵の平均＝キャッシュの値", RUNR["p40"].mean, sd["sample"]["R_40"], 0.01),
        ("見本の回 混雑: 動かす絵の平均＝キャッシュの値（2列）", RUNR["B"].mean, sd["sample"]["R_B"], 0.01),
        ("絵 冒頭: 3割の駅は行列が伸び続ける（15本め到着後 > 7本め到着後）",
         float(RUNR["p30"].waiting(TAU_MAX_I)[0].sum() > RUNR["p30"].waiting(700.0)[0].sum() + 20), 1, 0),
        ("絵 冒頭: 4割の駅は行列が消える（15本め到着後に待つ人 10人未満）", float(RUNR["p40"].waiting(TAU_MAX_I)[0].sum() < 10), 1, 0),
        ("絵 冒頭: 早回しは「伸びていきます」を言い終わるまでに終わる", float(tau_intro(E("c0_7")) >= TAU_MAX_I), 1, 0),
        ("絵 冒頭: 朝の2駅のちら見せは最初の20秒以内に始まる（統括の判断。ふだんの間で 0:10〜0:12 ごろ）", T_LAY, 14.0, 6.0),
        ("絵 冒頭: ちら見せのあとに乗り方の説明（上から見た2基）", float(T_LAY < S("g0") < S("c0_2")), 1, 0),
        ("絵 1章: 誰も歩かない回は「137秒」の前に全員上り終える", float(tau0(S("c1_8")) >= RUN0[0].make), 1, 0),
        ("絵 2章: 15本の早回しは「206秒」の前に終わる", float(tau2(S("c2_3")) >= TAU_MAX_I), 1, 0),
        ("絵 3章: 2人目は歩く人", float(TR25["walker"][SLOW_I]), 1, 0),
        ("絵 4章: 断面は左ページに収まる（40m の下の端 x > 110）", float(DEEP[2][1] - 40 * math.sqrt(3) * DEEP_PX > LX0_), 1, 0),
    ]
    # ---- 時間割 ----
    ch = tl.chapters
    ends = [c[0] for c in ch[1:]] + [DUR]
    checks.append(("章は7つ・最初は0秒（ひと休みは章に入れない）", float(len(ch) == 7 and ch[0][0] == 0), 1, 0))
    checks += [
        ("区切り: 2章の最後の文と3章の付箋の間", float(E("c2_15") <= T_EC0() and T_EC1() == S("ch3")), 1, 0),
        ("区切り: 長さ約4秒（3.5〜5秒）", T_EC1() - T_EC0(), 4.25, 0.75),
        ("区切り: 声なし（区切りの間にナレーションの行がない）", float(not any(T_EC0() <= s_ < T_EC1() for s_, *_r in tl._lines)), 1, 0),
        ("区切り: 足あとの音は点の数と同じで、区切りの中", float(len(ec_step_times()) >= 10 and all(T_EC0() <= x <= T_EC1() for x in ec_step_times())), 1, 0),
        ("区切り: 動画の真ん中に一番近い章の切れ目（真ん中との差が他の切れ目より小さい）",
         float(abs(T_EC0() - DUR / 2) <= min(abs(c[0] - DUR / 2) for c in ch[1:])), 1, 0),
        ("区切りの「4割」＝ 混雑の入れ替わり（四捨五入で4割）", SH["X2_10"], 4, 0),
    ]
    for (t0_, title), e_ in zip(ch, ends):
        checks.append((f"章「{title}」が10秒以上", float(e_ - t0_ >= 10), 1, 0))
    checks.append(("長さ 10分〜14分（台本 v6 を1文ずつ読んだ長さ。v6 から目安なし）", DUR, 720.0, 120.0))
    many = [(it.id, voice_numbers(txt(it.id))) for it in tl.items if isinstance(it, lf.Line) and len(voice_numbers(txt(it.id))) > 1]
    for i_, v_ in many:
        print(f"  1文に数字が2つ以上: {i_} {v_}")
    checks.append((f"1文の声の数字は1つまで（「4人に1人」「10人のうち」「2列」は1つ扱い）: {len(many)}文", float(not many), 1, 0))
    nb = [it.id for it in tl.items if isinstance(it, lf.Line) and voice_numbers(txt(it.id)) and
          next(x for x in tl._lines if x[3].id == it.id)[2] < 0.5 - 1e-9 and it.id != "c6_6b"]
    checks.append((f"数字を言った文のあとは0.5秒以上の間: 足りない文 {nb}", float(not nb), 1, 0))
    first45 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 45:
            first45 |= set(_re.findall(r"\d+[^\d、。]?", txt(it.id)))
    checks.append((f"冒頭45秒で声に出す数字は「2つ」「3割」「4割」の3つまで（「2列」は名前）: {sorted(first45)}",
                   float(first45 - {"2列"} <= {"2つ", "3割", "4割"}), 1, 0))
    keys = box_keys()
    gaps = [b[0] - a[0] for a, b in zip(keys, keys[1:])]
    checks.append((f"数字の欄: 答えの数字は3秒以上見せる（変わるまでの最短 {min(gaps):.1f}秒）", float(min(gaps) >= 3.0), 1, 0))
    checks += [
        ("約25% の赤丸は3秒以上", float(S("ch2") - (S("c1_11") + 0.2) >= 3), 1, 0),
        ("約4割 の赤丸は3秒以上", float(S("c2_10") - 0.2 - (S("c2_6") + 0.2) >= 3), 1, 0),
        ("68秒 は3秒以上", float(S("ch4") - mid("c3_4", 0.5) >= 3), 1, 0),
        ("21人・11人 の付箋は3秒以上", float(S("ch6") - (S("c5_5") + 0.4) >= 3), 1, 0),
        ("終了画面（最後の20秒）は まとめ の章の中", float(T_ES() > S("ch6") + 3), 1, 0),
    ]
    # ---- 字幕 ----
    worst_cps, worst_vis, worst_lines = 0.0, 1e9, 0
    for s_, e_, pause, ln, clip in tl._lines:
        vis = e_ - s_ + min(pause, lf.SUB_HOLD)
        worst_cps = max(worst_cps, len(clip.text) / vis)
        worst_vis = min(worst_vis, vis)
        worst_lines = max(worst_lines, len(lf.wrap_subtitle(clip.text)))
    checks += [
        (f"字幕: 1秒あたりの字数が12字以下（最大 {worst_cps:.1f}字）", float(worst_cps <= 12), 1, 0),
        (f"字幕: どの行も1秒以上出る（最短 {worst_vis:.1f}秒）", float(worst_vis >= 1.0), 1, 0),
        (f"字幕: 2行以内（最大 {worst_lines}行）", float(worst_lines <= 2), 1, 0),
    ]
    # ---- 画面の文字（0.25秒ごとに描いて調べる） ----
    if frames is not None:
        bad = overlaps(frames)
        for k, t in list(bad.items())[:10]:
            print(f"  重なり: {_ts(t)} 「{k[0]}」と「{k[1]}」")
        checks.append((f"文字どうしの重なりなし（0.5秒以上続くもの。章の付箋・1万回の合図は除く）: {len(bad)}組", float(len(bad) == 0), 1, 0))
        f0 = next(f for f in frames if f[0] == 0.0)
        names0 = {e[0] for e in f0[1]}
        checks.append(("0秒目に 題字「エスカレーター」と問いが出ている",
                       float({"エスカレーター", "片側あけが得になるのは、", "歩く人が何割のとき？"} <= names0), 1, 0))
        checks.append(("冒頭: 上から見た2基に人が流れている（乗り方は2つ）・朝の駅の比べに人が出ている",
                       float(min(f[2] for f in frames if S("c0_3") <= f[0] <= S("c0_4")) > 0
                             and min(f[2] for f in frames if T_PEEK + 0.75 <= f[0] <= T_PEEK + 3) > 0), 1, 0))
        tes = T_ES() + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if e[1] < 580 or e[3] > 1340]
        for t, s_ in out_es[:5]:
            print(f"  終了画面の左右に文字: {_ts(t)} 「{s_}」")
        checks.append((f"終了画面（最後の20秒）は左右を空ける（文字は x 580〜1340 だけ）: {len(out_es)}件", float(not out_es), 1, 0))
        br = [(f[0], e[0]) for f in frames for e in f[1] if e[3] > 1660 and e[4] > 930]
        for t, s_ in br[:5]:
            print(f"  右下に文字: {_ts(t)} 「{s_}」")
        checks.append((f"右下（x>1660・y>930）に文字を置かない: {len(br)}件", float(not br), 1, 0))
        ec_in = [f for f in frames if T_EC0() + 0.4 <= f[0] <= T_EC1() - 0.6]
        checks.append(("区切りの間は 2つの数字の欄を出さない", float(bool(ec_in) and all(
            not ({"片側あけ", "2列で立つ"} <= {e[0] for e in f[1] if 1030 < e[1] < 1800 and e[2] > 712}) for f in ec_in)), 1, 0))
        checks.append(("区切り: 左「ここまで」・右「ここから」と2行ずつが出ている", float(all(
            {"ここまで", "ここから", "混んだ朝は、歩く人が", "ゆっくり歩く人や、", "階段があったら？"} <= {e[0] for e in f[1]} for f in ec_in)), 1, 0))
        ec_nums = set()
        for f_ in ec_in:
            for e in f_[1]:
                ec_nums |= set(_re.findall(r"\d+[^\d、。 ]?", e[0]))
        checks.append((f"区切り: 画面の数字は「4割」の1つだけ（「2列」は名前）: {sorted(ec_nums)}", float(ec_nums - {"2列"} == {"4割"}), 1, 0))
        ec_mid = [f for f in frames if T_EC0() + 0.6 <= f[0] <= T_EC1() - 0.3]
        checks.append(("区切り: 左右の文字は最初の0.5秒で出て最後まで表示", float(bool(ec_mid) and all("ここまで" in {e[0] for e in f[1]} for f in ec_mid)), 1, 0))
        miss = [f[0] for f in frames if S("c1_5") + 0.8 <= f[0] < T_ES() - 0.1 and not (T_EC0() - 0.1 <= f[0] <= T_EC1() + 0.4)
                and not ({"片側あけ", "2列で立つ"} <= {e[0] for e in f[1] if 1030 < e[1] < 1800 and e[2] > 712})]
        checks.append((f"2つの数字の欄は1章から終了画面まで出しっぱなし（欠けたコマ {len(miss)}）", float(not miss), 1, 0))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--readings" in args:
        write_readings(OUT / "readings.log")
        return
    if "--wraps" in args:
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        return
    if "--preview-intro" in args:
        d = OUT / "preview"
        d.mkdir(parents=True, exist_ok=True)
        for tt in (0.0, 5.0, 15.0, 30.0):
            lf.still(draw, tt, d / f"intro_{tt:04.1f}.png")
        print("冒頭の静止画:", d)
        return
    if "--scenecheck" in args:
        frames = scan()
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, OUT / f"at_{tt:06.1f}.png")
        else:
            lf.stills(draw, still_times(), OUT / "stills")
        return
    if "--preview" in args:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
        return
    if FAKE:
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    D = load_all()
    run_checks(D, shown(D))                            # モデルの照合（74件）
    frames = scan()
    scene_checks(frames)
    write_screen_text(OUT / "screen_text.txt", frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    lf.stills(draw, still_times(), OUT / "stills")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
