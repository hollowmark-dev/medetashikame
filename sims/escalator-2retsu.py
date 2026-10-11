"""エスカレーター、片側あける？2列で立つ？ 電車が着いて100人が下に来る。「1人あたりの平均」で早いのは？ — 2026-10-08 作成（公開予定 10/10）
（v2: 比べる指標を「全員が上り終える時間（最後の人）」から「1人あたりの平均」に変えた。v1 は out/escalator-2retsu/ に .v1 で残してある）

モデル（上から見た1基。幅は2人が並べる＝左右2列。人は1列にならんで乗る）
  エスカレーター : 秒速0.5m（分速30m。日本エレベーター協会の言う「通常」の速さ）。傾斜30度、高さ17.5m → 長さ35m（地下鉄の深い駅の長いもの）。
                   踏段1段の奥行き 0.4m（ロンドン地下鉄の報告書の値 0.41m に近い値）。
  人             : 100人。電車が着いて、少しずつばらつきながら（20〜50秒かけて）下に着く。着いた順に列に並び、前の人が乗れる間隔をあけたら乗る。
  立つ人         : エスカレーターと同じ速さ（秒速0.5m）で上る。前の人との間隔は「1段あけ」= 2段おき（0.8m）が基準。
                   1人ごとに1〜3段おき（平均2段）、その回の平均も 1.6〜2.4段 でゆらす。
  歩く人         : エスカレーターの上でさらに秒速0.5m（平均。標準偏差0.1）で上る → 地面から見て約1.0m/s。前の人との間隔は 2段あけ = 3段おき（1.2m）が基準
                   （ロンドン地下鉄の報告書は、立つ人 2段おき・歩く人 3段おきで計算している）。1人ごとに 平均2.8段おき、標準偏差0.4段。
                   歩く列では前の人を追い越せない。速い人は前の人の速さまで落ちる（間隔より近づけない）。
  歩きたい人の割合: 平均25%（その回ごとに 5〜55%くらいでゆらす。Beta(9.25, 27.75)）。
  片側あける      : 立つ人は立つ列だけ、歩きたい人は歩く列だけを使う（片方の列を歩く人のために空けておく）。
  2列で立つ      : 全員が立つ。空いたほうの列に乗る。
  判定（v2）     : 1人あたりの平均 = 全員の「列に着いてから上り終えるまで」の平均（下の行列で待つ時間も含む）。参考として最後の人（全員が上り終える時間）も出す。
  ラッシュ       : 電車が T 秒おきに100人ずつ15本。各電車は make_trial で別々に作り、到着時刻に k×T を足して連結。1人あたりの平均は1500人ぶん。
  1万回          : 到着の順番・タイミング・歩きたい人の割合と顔ぶれ・間隔・歩く速さをゆらして1万回（ラッシュも1万回）。数字は全試行から。
  ※ 上り終えたあとの出口の混雑、乗る前のためらい、荷物のある人、立つ列を歩いて抜ける人は入れていない。

照合（check_answers）:
 (1) 閉じた式: 全員が同時に着いて全員が立つ2列 → 全員が上り終える時間 = 49 × 1.6秒 + 長さ ÷ 0.5
 (2) 閉じた式: 歩く25人が同じ速さ・同じ間隔で同時に着く → 最後の人が上り終える時間 = 24 × 間隔 ÷ 速さ + 長さ ÷ 速さ
 (3) 別の実装（0.02秒刻みで1人ずつ動かす）と、全員が上り終える時間が一致（片側あける・2列）
 (3b) 閉じた式: 全員が同時に着いて全員が立つ2列 → 1人あたりの平均 = (2 × Σ_{j<50} j × 1.6秒) / 100 + 長さ ÷ 0.5
 (4) 別の乱数で1万回やり直して、「平均の差」「2列が早い割合」「ラッシュの平均」が同じ
 (5) 画面に出す数字（秒数）が別の乱数のやり直しと同じ丸め
 (6) 答えは C（1人あたりの平均はほぼ同じ）、ひねりは「ラッシュでは片側あけの行列が伸び続ける」
乱数の種は、冒頭〜答え合わせ1・ひねりの見本（1回ぶん）を「ふつうの結果」にするために選んでよい。
画面の統計は1万回すべてから正直に出している。
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
from engine.parts import bgra, grid_image, loop_back, stills

note.use()
note.DATE = "10.11"                               # 日付欄（公開予定日）

SLUG = "escalator-2retsu"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
VE = 0.5                                          # エスカレーターの速さ（m/s）
PITCH = 0.4                                       # 踏段1段の奥行き（m）
HEIGHT = 17.5                                     # 高さ（m）。傾斜30度なので長さ = 2 × 高さ
L_BASE = 2 * HEIGHT                               # 35m
N = 100                                           # 1回に着く人数
P_MEAN, P_SD = 0.25, 0.07                         # 歩きたい人の割合（平均・標準偏差）
BETA_A = P_MEAN * (P_MEAN * (1 - P_MEAN) / P_SD ** 2 - 1)
BETA_B = (1 - P_MEAN) * (P_MEAN * (1 - P_MEAN) / P_SD ** 2 - 1)
W_LO, W_HI = 20.0, 50.0                           # 100人が着き終わるまでの時間の範囲（秒）
GS_MEAN, GS_SD = 2.0, 0.15                        # 立つ人の間隔（段おき）: その回の平均
GW_MEAN, GW_SD = 2.8, 0.2                         # 歩く人の間隔（段おき）: その回の平均
WALK_REL, WALK_SD = 0.5, 0.1                      # 歩く人の上乗せの速さ（m/s）
N_TRIALS = 10000
HEIGHTS = [5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 25.0]   # 長さを変える（高さ。長さは2倍）
I_BASE = HEIGHTS.index(HEIGHT)


def make_trial(seed):
    r = np.random.default_rng(seed)
    p = r.beta(BETA_A, BETA_B)
    Wd = r.uniform(W_LO, W_HI)
    a = np.sort(Wd * r.beta(2, 3, N))
    a -= a[0]
    walker = r.random(N) < p
    ms = float(np.clip(r.normal(GS_MEAN, GS_SD), 1.6, 2.4))
    gs = (1 + r.binomial(2, (ms - 1) / 2, N)) * PITCH
    mw = float(np.clip(r.normal(GW_MEAN, GW_SD), 2.2, 3.4))
    gw = np.clip(r.normal(mw, 0.4, N), 1.5, 4.5) * PITCH
    w = np.clip(r.normal(WALK_REL, WALK_SD, N), 0.25, 0.8)
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


N_TRAIN = 15                                      # ラッシュの電車の本数
RUSH_TS = [90.0, 100.0, 120.0, 150.0, 180.0]      # 電車が来る間隔（秒）
I_T100 = RUSH_TS.index(100.0)
N_RUSH = 10000
RUSH_BASE = 20000000


def rush_trial(seed, T, ntrain=N_TRAIN):
    """電車が T 秒おきに100人ずつ ntrain 本。1本ずつ make_trial で作り、到着に k×T を足して連結"""
    trs = [make_trial(seed * 20 + k) for k in range(ntrain)]
    tr = {k: np.concatenate([t[k] for t in trs]) for k in ("walker", "gs", "gw", "w")}
    tr["a"] = np.concatenate([t["a"] + k * T for k, t in enumerate(trs)])
    tr["p"] = float(np.mean([t["p"] for t in trs]))
    tr["ntrain"] = ntrain
    return tr


def _chunk(args):
    seeds, Ls = args
    rows = []
    for sd in seeds:
        tr = make_trial(int(sd))
        A, B = metrics(tr, "A", Ls), metrics(tr, "B", Ls)
        rows.append(np.stack([A["make"], B["make"], A["mean"], B["mean"], A["mean_w"], B["mean_w"], A["mean_s"], B["mean_s"]]
                             + [np.full(len(Ls), tr["walker"].sum(), float)]))
    return np.array(rows)                              # (試行, 9, 長さ）


def _rush_chunk(args):
    seeds, Ts = args
    rows = []
    for sd in seeds:
        row = []
        trs = [make_trial(int(sd) * 20 + k) for k in range(N_TRAIN)]
        for T in Ts:
            tr = {k: np.concatenate([t[k] for t in trs]) for k in ("walker", "gs", "gw", "w")}
            tr["a"] = np.concatenate([t["a"] + k * T for k, t in enumerate(trs)])
            out = []
            for mode in ("A", "B"):
                m = metrics(tr, mode, L_BASE)
                dur = (m["ex"][0] - tr["a"])
                out += [float(dur.mean()), float(dur[-N:].mean())]
            row.append([out[0], out[2], out[1], out[3]])   # A平均, B平均, A最後の電車の人の平均, B最後の電車の人の平均
        rows.append(row)
    return np.array(rows)                              # (試行, T, 4)


def many(seed0, n, Ls, chunk=250):
    jobs = [(np.arange(seed0 + i, seed0 + min(n, i + chunk)), Ls) for i in range(0, n, chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        return np.concatenate(list(ex.map(_chunk, jobs)))


def many_rush(seed0, n, Ts, chunk=100):
    jobs = [(np.arange(seed0 + i, seed0 + min(n, i + chunk)), Ts) for i in range(0, n, chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        return np.concatenate(list(ex.map(_rush_chunk, jobs)))


def compute(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    Ls = 2 * np.array(HEIGHTS)
    f = OUT / "data.npz"
    if force or not f.exists():
        main = many(0, N_TRIALS, Ls)
        again = many(500000, N_TRIALS, Ls)
        np.savez(f, main=main, again=again)
    f2 = OUT / "rush.npz"
    if force or not f2.exists():
        np.savez(f2, main=many_rush(0, N_RUSH, RUSH_TS), again=many_rush(RUSH_BASE, N_RUSH, RUSH_TS))


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        if not (OUT / "data.npz").exists() or not (OUT / "rush.npz").exists():
            compute()
        z = np.load(OUT / "data.npz")
        r = np.load(OUT / "rush.npz")
        _DATA = {k: z[k] for k in z.files}
        _DATA.update({"rush_" + k: r[k] for k in r.files})
    return _DATA


# ---------- 別の実装（0.02秒刻み）と閉じた式 ----------

def timestep(tr, mode, L, dt=0.02):
    """全員が上り終える時刻。1人ずつ 0.02秒ごとに動かす別の実装（式を使わない）。
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


def closed_form_checks():
    out = []
    # (1) 全員が t=0 に着いて全員が立つ2列、間隔は一定（2段 = 0.8m）
    tr = dict(a=np.zeros(N), walker=np.zeros(N, bool), gs=np.full(N, 2 * PITCH), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    for L in (10.0, 35.0, 50.0):
        sim = float(metrics(tr, "B", L)["make"][0])
        out.append((f"閉じた式 全員同時・2列・長さ{L:.0f}m: 全員が上り終える時間（秒）", sim, 49 * 2 * PITCH / VE + L / VE, 1e-6))
    # (2) 歩く25人が同時に着く、同じ速さ・同じ間隔
    wk = np.zeros(N, bool)
    wk[:25] = True
    tr = dict(a=np.zeros(N), walker=wk, gs=np.full(N, 0.8), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    for L in (10.0, 35.0):
        res = enter(tr, "A")
        ex = exit_times(res, L)[0]
        out.append((f"閉じた式 歩く25人が同時・長さ{L:.0f}m: 歩く最後の人（秒）", float(ex[wk].max()), 24 * 1.2 / 1.0 + L / 1.0, 1e-6))
    return out


# ---------- 画面に出す数字（1万回すべて） ----------

def shown():
    d = data()
    m, ag = d["main"], d["again"]
    r, ra = d["rush_main"], d["rush_again"]
    i = I_BASE
    dm = m[:, 2, i] - m[:, 3, i]                      # 1人あたり平均の差（片側あける − 2列）。正なら2列が早い
    dm2 = ag[:, 2, i] - ag[:, 3, i]
    dk = m[:, 0, i] - m[:, 1, i]                      # 最後の人の差
    dk2 = ag[:, 0, i] - ag[:, 1, i]
    sw = lambda arr, k, j: float(arr[:, k, j].mean())
    S = dict(dm=dm, win=int((dm > 0).sum()), win_again=int((dm2 > 0).sum()),
             mean_diff=float(dm.mean()), mean_diff_again=float(dm2.mean()),
             dm_sd=float(dm.std()), dm_p5=float(np.percentile(dm, 5)), dm_p95=float(np.percentile(dm, 95)),
             dk=dk, mk_diff=float(dk.mean()), mk_diff_again=float(dk2.mean()),
             mk_win=int((dk > 0).sum()), mk_win_again=int((dk2 > 0).sum()),
             A_make=sw(m, 0, i), B_make=sw(m, 1, i), A_make_again=sw(ag, 0, i), B_make_again=sw(ag, 1, i),
             A_mean=sw(m, 2, i), B_mean=sw(m, 3, i), A_mean_again=sw(ag, 2, i), B_mean_again=sw(ag, 3, i),
             A_walk=sw(m, 4, i), B_walk=sw(m, 5, i), A_stand=sw(m, 6, i), B_stand=sw(m, 7, i),
             A_walk_again=sw(ag, 4, i), B_walk_again=sw(ag, 5, i), A_stand_again=sw(ag, 6, i), B_stand_again=sw(ag, 7, i),
             n_walk=float(m[:, 8, i].mean()))
    # 長さごと
    S["sweep"] = []
    for j, h in enumerate(HEIGHTS):
        dj = m[:, 2, j] - m[:, 3, j]
        S["sweep"].append(dict(h=h, L=2 * h, win=float((dj > 0).mean()), dmean=float(dj.mean()),
                               dmake=float((m[:, 0, j] - m[:, 1, j]).mean()),
                               A_mean=float(m[:, 2, j].mean()), B_mean=float(m[:, 3, j].mean())))
    # ラッシュ（T ごと）
    S["rush"] = [dict(T=T, A=float(r[:, k, 0].mean()), B=float(r[:, k, 1].mean()),
                      A_last=float(r[:, k, 2].mean()), B_last=float(r[:, k, 3].mean()),
                      A_again=float(ra[:, k, 0].mean()), B_again=float(ra[:, k, 1].mean()),
                      A_sd=float(r[:, k, 0].std()), A_p5=float(np.percentile(r[:, k, 0], 5)), A_p95=float(np.percentile(r[:, k, 0], 95)),
                      A_win=float((r[:, k, 0] > r[:, k, 1]).mean()))
                 for k, T in enumerate(RUSH_TS)]
    # 歩きたい人の割合ごと（1人あたり平均で2列が早い割合）
    nw = m[:, 8, i]
    S["by_walkers"] = [(lo, hi, float((dm[(nw >= lo) & (nw < hi)] > 0).mean()), int(((nw >= lo) & (nw < hi)).sum()))
                       for lo, hi in ((0, 20), (20, 30), (30, 40), (40, 50), (50, 101))]
    return S


def find_seed():
    """見本にする1回: 歩きたい人25人で、1人あたり平均が両方100秒に丸まり、最後の人の差が1万回の中央値付近"""
    d = data()["main"]
    i = I_BASE
    dm = d[:, 2, i] - d[:, 3, i]
    dk = d[:, 0, i] - d[:, 1, i]
    med = float(np.median(dk))
    nw = d[:, 8, i]
    cand = [(abs(dk[k] - med) + abs(dm[k]), k) for k in range(len(dm))
            if nw[k] == 25 and round(d[k, 2, i]) == 100 and round(d[k, 3, i]) == 100 and abs(dm[k]) < 0.8]
    cand.sort()
    return cand[:10], med


def find_rush_seed():
    """ラッシュの見本にする1回: T=100 で、片側あけの平均が1万回の中央値に近く、2列は100秒"""
    r = data()["rush_main"][:, I_T100]
    med = float(np.median(r[:, 0]))
    cand = [(abs(r[k, 0] - med) + abs(r[k, 1] - 99.5), k) for k in range(len(r))]
    cand.sort()
    return cand[:10], med


def fmt_n(n):
    return f"{int(n):,}"


if __name__ == "__main__" and "--compute" in sys.argv:
    import time
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    compute(force="--force" in sys.argv)
    print(f"計算 {time.time() - t0:.0f}秒")
    S = shown()
    print(f"1人あたり平均: 片側 {S['A_mean']:.2f} 2列 {S['B_mean']:.2f}（やり直し {S['A_mean_again']:.2f} / {S['B_mean_again']:.2f}）")
    print(f"平均の差（片側−2列） {S['mean_diff']:.2f}秒（やり直し {S['mean_diff_again']:.2f}） sd {S['dm_sd']:.1f} 5〜95% [{S['dm_p5']:.1f}, {S['dm_p95']:.1f}]  2列が早い {S['win']}/{N_TRIALS}（やり直し {S['win_again']}）")
    print(f"最後の人: 片側 {S['A_make']:.1f} 2列 {S['B_make']:.1f} 差 {S['mk_diff']:.1f}（やり直し {S['mk_diff_again']:.1f}） 2列が早い {S['mk_win']}/{N_TRIALS}")
    print(f"歩きたい人 片側 {S['A_walk']:.1f} 2列 {S['B_walk']:.1f} / 立つ人 片側 {S['A_stand']:.1f} 2列 {S['B_stand']:.1f}")
    print("長さごと:")
    for r in S["sweep"]:
        print("  高さ%.1fm 長さ%.0fm: 平均 片側 %.1f 2列 %.1f 差 %.2f 2列が早い %.1f%% / 最後の人の差 %.1f" %
              (r["h"], r["L"], r["A_mean"], r["B_mean"], r["dmean"], r["win"] * 100, r["dmake"]))
    print("歩きたい人の人数ごとの「平均で2列が早い」割合:", S["by_walkers"])
    print("ラッシュ（%d本、%d回）:" % (N_TRAIN, N_RUSH))
    for r in S["rush"]:
        print("  T=%3.0f秒: 片側 %.1f 2列 %.1f（やり直し %.1f / %.1f） 最後の電車の人 片側 %.1f 2列 %.1f  片側のばらつき sd %.1f 5〜95%% [%.0f, %.0f]  2列が早い %.1f%%" %
              (r["T"], r["A"], r["B"], r["A_again"], r["B_again"], r["A_last"], r["B_last"], r["A_sd"], r["A_p5"], r["A_p95"], r["A_win"] * 100))
    print("見本の候補:", find_seed())
    print("ラッシュ見本の候補:", find_rush_seed())


# ---------- 見本の1回（冒頭〜答え合わせ1）と、ラッシュの見本 ----------
DEMO_SEED = 7583                                  # 歩きたい人25人で、1人あたり平均が両方100秒・最後の人の差が中央値付近の回（--compute で探した）
RUSH_SEED = 5964                                  # ラッシュ（T=100秒）で、片側あけの平均が1万回の中央値に最も近い回
TR = make_trial(DEMO_SEED)


class Run:
    """1回ぶんの動き。時刻 tau（秒）での位置・待っている人の順番・上り終えた人数を返す"""

    def __init__(self, tr, mode, L):
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

    def pos(self, tau):
        """列の上の位置（m）。まだ乗っていない人は nan"""
        x = np.full(len(self.e), np.nan)
        m = self.stand & (self.e <= tau)
        x[m] = VE * (tau - self.e[m])
        idx = self.idx_w
        if len(idx):
            ew, sw, C = self.e[idx], self.s[idx], self.C
            val = sw[None, :] * (tau - ew[None, :]) - (C[:, None] - C[None, :])
            tri = np.tril(np.ones((len(idx), len(idx)), bool))
            val = np.where(tri, val, np.inf).min(1)
            ent = ew <= tau
            x[idx[ent]] = np.maximum(0.0, val[ent])
        return x

    def waiting(self, tau, sm=0.0):
        """待っている人と、その順番（先頭が0）。sm>0 なら過去の数時刻の平均で滑らかに"""
        wait = (self.a <= tau) & (self.e > tau)
        taus = [tau] if sm <= 0 else [tau - sm * u for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
        rk = np.mean([(self.before & (self.e[None, :] > tt)).sum(1) for tt in taus], axis=0)
        return wait, rk

    def done(self, tau):
        return int((self.ex <= tau).sum())


_RUNS = {}


def run_of(mode, L=L_BASE):
    k = (mode, L)
    if k not in _RUNS:
        _RUNS[k] = Run(TR, mode, L)
    return _RUNS[k]


# ---------- 絵: 上から見た人・エスカレーター（ペン描き風） ----------
STAND_COL, WALK_COL = "#a9d0f2", "#c5e37a"        # 水色（立つ人）／黄緑（歩く人）
SKY, ORANGE = "#3a8fd9", "#f29a2e"                # 2列が早い／片側あけが早い
SKIN = "#fff3df"
STRIP_FILL = "#e8e2d2"


def person_icon(ctx, x, y, col, w, a=1.0):
    """上から見た頭と肩（右向き＝上りの向き）。w は肩幅（px）。肩は色つき、頭は髪の色（上から見ると髪が見える）"""
    if a <= 0:
        return
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


_JIT = np.random.default_rng(4).uniform(-1, 1, (N, 2))
_STR = np.random.default_rng(8).uniform(-0.28, 0.28, 12)
STRIPE_OFFS = [k * PITCH + _STR[k] * PITCH for k in range(12)]    # 踏段の線（わざとふぞろいにして、早送りでも逆回りに見えない）
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
    for base in (range(-1, int(min(L, G.vis_m) / STRIPE_PERIOD) + 2) if moving else ()):   # 早送りが速いときは踏段の線を描かない（ちらつくので）
        for off in STRIPE_OFFS:
            px = G.x0 + (base * STRIPE_PERIOD + off + shift) * G.pxm
            if G.x0 <= px <= xr:
                ctx.move_to(px, y0 + 3)
                ctx.line_to(px, y1 - 3)
    ctx.stroke()
    ctx.restore()
    # ふち（ペンで引いた線）と、まん中の仕切り
    for (xa, ya, xb, yb, sd, wd) in ((G.x0, y0, xr, y0, 11, 4), (G.x0, y1, xr, y1, 12, 4),
                                     (G.x0, G.yu + G.lw / 2, xr, G.yu + G.lw / 2, 13, 3)):
        note.pen_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=wd, alpha=0.8 * a)
    note.pen_line(ctx, G.x0, y0, G.x0, y1, INK, seed=14, width=4, alpha=0.8 * a)
    if L <= G.vis_m + 1e-9:
        note.pen_line(ctx, xr, y0, xr, y1, INK, seed=15, width=4, alpha=0.8 * a)
        for yc in (G.yu, G.yd):                            # 上りの向きを示す三角
            ctx.set_source_rgba(*hexrgb(INK, 0.55 * a))
            ctx.move_to(xr + 10, yc - 9)
            ctx.line_to(xr + 24, yc)
            ctx.line_to(xr + 10, yc + 9)
            ctx.close_path()
            ctx.fill()


def draw_people(ctx, G, run, tau, L, F, a=1.0):
    """待っている人（行列）と、列の上の人。F = 動画1秒あたりの世界の秒数"""
    n = len(run.e)
    mode = run.mode
    colors = [STAND_COL if run.stand[i] else WALK_COL for i in range(n)]
    ctx.save()
    ctx.rectangle(40, G.yu - G.lw * 4, G.vis_right + 30 - 40, G.lw * 9)
    ctx.clip()
    wait, rk = run.waiting(tau, sm=0.25 * F)
    for i in np.where(wait)[0]:
        r = rk[i]
        if mode == "B":
            R, yc = G.rows_one, (G.yu + G.yd) / 2
        elif run.stand[i]:
            R, yc = G.rows_u, G.yq_u
        else:
            R, yc = G.rows_d, G.yq_d
        row = int(r + 0.5) % R
        jx, jy = _JIT[i]
        px = G.x0 - 14 - G.qsp * (r / R) + jx * G.qsp * 0.28
        py = yc + (row - (R - 1) / 2) * G.qsp + jy * G.qsp * 0.28
        k = (tau - run.a[i]) / (0.4 * F)
        slide = 90 * (1 - ease_out(k))
        person_icon(ctx, px - slide, py, colors[i], G.qw, a=a * clamp01(k * 1.5))
    x = run.pos(tau)
    for i in np.where(~np.isnan(x))[0]:
        xm = x[i]
        lim = min(G.vis_m, L)
        if xm > lim + 1.3:
            continue
        fade = clamp01((lim + 1.2 - xm) / 1.2)
        py = G.yu + G.lw * run.lane[i]
        person_icon(ctx, G.x0 + xm * G.pxm, py, colors[i], G.iw, a=a * fade)
    ctx.restore()


def draw_block(ctx, G, run, tau, F, a=1.0, L=L_BASE):
    if a <= 0:
        return
    if a < 1:
        ctx.push_group()
    draw_strip(ctx, G, tau, L)
    draw_people(ctx, G, run, tau, L, F)
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


# 見せ方の配置
G_INTRO = Geo(x0=330, pxm=62, lw=100, yu=640, vis_right=1010, qsp=26, qw=24, rows_u=5, rows_d=2, yq_u=640, yq_d=740)
G_A = Geo(x0=285, pxm=19.5, lw=60, yu=730, vis_right=285 + 19.5 * L_BASE, qsp=14, qw=13, rows_u=6, rows_d=3)
G_B = Geo(x0=285, pxm=19.5, lw=60, yu=1050, vis_right=285 + 19.5 * L_BASE, qsp=14, qw=13, rows_u=6, rows_d=3, single=True, rows_one=8)
RX0, RPXM, RLW, RQSP = 690, 8.8, 32, 12              # ラッシュ: 短い1基（右）。左に行列（点）、列の上の人も点
G_RA = Geo(x0=RX0, pxm=RPXM, lw=RLW, yu=860, vis_right=RX0 + RPXM * L_BASE, qsp=RQSP, qw=8, rows_u=5, rows_d=2)
G_RB = Geo(x0=RX0, pxm=RPXM, lw=RLW, yu=1030, vis_right=RX0 + RPXM * L_BASE, qsp=RQSP, qw=8, rows_u=5, rows_d=2, single=True, rows_one=6)

# ---------- 時間割（表示の秒） ----------
RUN_A, RUN_B = run_of("A"), run_of("B")
A_MAKE, B_MAKE = float(RUN_A.ex.max()), float(RUN_B.ex.max())
A_AVG, B_AVG = float((RUN_A.ex - TR["a"]).mean()), float((RUN_B.ex - TR["a"]).mean())
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
TAU0_I, F_INTRO = 12.0, 6.0                        # 冒頭: 世界の12秒目から、動画1秒＝世界6秒
T_R0 = T_GO + 0.3                                  # 答え合わせ1: 2基を同時に動かす
RB_DUR = 3.6                                       # 2列が全員上り終えるまでの動画の秒（世界の約150秒を3.9秒で）
F1 = B_MAKE / RB_DUR                               # 動画1秒 = 世界の約40秒
F2 = 20.0                                          # 2列が終わったあと、片側あけの残りはゆっくり
T_RB = T_R0 + RB_DUR
T_RA = T_RB + (A_MAKE - B_MAKE) / F2
T_G0 = T_RA + 2.9                                  # 1万回へ
T_D0 = T_G0 + 0.45
D_DUR = 3.0
T_D1 = T_D0 + D_DUR
T_REV = T_D1 + 0.4
T_ST2 = T_REV + 0.3
T_TW = T_ST2 + 2.4                                 # ひねり: 電車が次々来たら？
T_RU0 = T_TW + 1.3                                 # ラッシュの動き
RU_DUR = 6.0
TAU_MAX = 1560.0                                   # 世界の秒（15本め到着のあとまで）
T_RES = T_RU0 + 4.1                                # 「1人あたり 片側○秒／2列○秒」
T_TWS = T_RU0 + 3.0                                # 付箋
T_Q = T_RU0 + RU_DUR + 1.7                         # 締め
DURATION = T_Q + 3.9

BIG_Q = "片側あける？2列で立つ？"
DETAIL = "100人の平均、早いのは？"
LABELS = ["片側あける", "2列で立つ", "ほぼ同じ"]
C_ORANGE, C_BLUE = "#c8741c", "#2f62c9"


# ---------- 冒頭 ----------

class EIntro(note.Intro):
    """この回だけの冒頭。上半分に上から見たエスカレーター（0秒目から人が流れ込み、片側だけ歩く人が上がる）、下に大きな問い"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        # 上半分: 片側あけのエスカレーター（拡大。長い1基の下のほう）
        if a > 0:
            tau = TAU0_I + F_INTRO * t
            # 2026-10-08 ユーザー「冒頭からエスカレーターって文字がないからなんだかわからない」→ 0秒目から大きく題材名
            note.hand_text(ctx, "エスカレーター", 110, 470, 64, INK, seed=77, alpha=a)
            text(ctx, "上から見たところ・右へ上る", 112, 530, 30, note.PENCIL, align="left", bold=False, alpha=a)
            draw_block(ctx, G_INTRO, RUN_A, tau, F_INTRO, a=a)
            note.legend(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], 860, 30)
        sz = 64
        w = core.text_width(BIG_Q, sz)
        if w > 860:
            sz *= 860 / w
            w = 860
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
                note.pen_circle(ctx, cx, y, (64 + vw) / 2 + 30, 42, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 72 + vw, y - 2, note.PENCIL, seed=i + 40, width=4,
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


INTRO = EIntro(["片側あける？", "2列で立つ？"], LABELS, correct=2, msg="", rule=None)


# ---------- 本体 ----------

def number_row(ctx, parts, y, a, size=44, cx=540):
    ws = [core.text_width(s, size) for s, _ in parts]
    x = cx - sum(ws) / 2
    for (s, col), w in zip(parts, ws):
        text(ctx, s, x, y, size, col, align="left", alpha=a)
        x += w


def tau1(t):
    """答え合わせ1: 動画の時刻 → 世界の秒（2列が終わるまでは速く、そのあとはゆっくり）"""
    if t < T_RB:
        return max(0.0, F1 * (t - T_R0))
    return min(A_MAKE, B_MAKE + F2 * (t - T_RB))


def video_of_tau(tau):
    if tau <= B_MAKE:
        return T_R0 + tau / F1
    return T_RB + (tau - B_MAKE) / F2


def block_label(ctx, label, y, a):
    text(ctx, label, 120, y, 40, INK, align="left", alpha=a)


def draw_answer1(ctx, t, a):
    """答え合わせ1: 上＝片側あける、下＝2列で立つ。同時に動かす。上り終えた人数と、1人あたりの平均"""
    if a <= 0:
        return
    tau = tau1(t)
    ctx.push_group()
    text(ctx, f"経過 {int(min(tau, A_MAKE))}秒", 470, 612, 40, INK, alpha=1.0)
    text(ctx, "早送り", 700, 614, 28, note.PENCIL, bold=False)
    nA, nB = RUN_A.done(tau), RUN_B.done(tau)
    Fn = F1 if t < T_RB else F2
    # 片側あける
    block_label(ctx, "片側あける", 672, 1.0)
    draw_block(ctx, G_A, RUN_A, tau, Fn)
    number_row(ctx, [("上り終えた人 ", INK), (f"{nA}", C_ORANGE), (" / 100", INK)], 868, 1.0, size=38, cx=470)
    # 2列で立つ
    block_label(ctx, "2列で立つ", 985, 1.0)
    draw_block(ctx, G_B, RUN_B, tau, Fn)
    number_row(ctx, [("上り終えた人 ", INK), (f"{nB}", C_BLUE), (" / 100", INK)], 1188, 1.0, size=38, cx=470)
    # 1人あたりの平均: 全員が上り終えたら数字が出る（途中は ？）
    for (tdone, avg, col, yy) in ((T_RA, A_AVG, C_ORANGE, 916), (T_RB, B_AVG, C_BLUE, 1236)):
        if t >= tdone:
            k = ease_out((t - tdone) / 0.25)
            ctx.save()
            ctx.translate(470, yy)
            sc = 1 + 0.25 * (1 - k)
            ctx.scale(sc, sc)
            number_row(ctx, [("1人あたり 平均 ", INK), (f"{int(round(avg))}", col), ("秒", INK)], 0, k, size=42, cx=0)
            ctx.restore()
        else:
            number_row(ctx, [("1人あたり 平均 ", INK), ("？", note.PENCIL), ("秒", INK)], yy, 0.8, size=42, cx=470)
    # 最後の人（小さく）
    if t >= T_RB:
        k = ease_out((t - T_RB) / 0.25)
        text(ctx, f"最後の人 {int(round(B_MAKE))}秒", 930, 985, 28, note.PENCIL, align="right", alpha=k, bold=False)
        if t < T_RA:
            number_row(ctx, [("片側あけの最後の人は あと ", note.PENCIL), (f"{int(math.ceil(A_MAKE - tau))}", INK), ("秒", note.PENCIL)], 1318, k, size=32)
    if t >= T_RA:
        k = ease_out((t - T_RA) / 0.25)
        text(ctx, f"最後の人 {int(round(A_MAKE))}秒", 930, 672, 28, note.PENCIL, align="right", alpha=k, bold=False)
        k2 = ease_out((t - T_RA - 0.25) / 0.3)
        text(ctx, "1人あたりの平均は、ほぼ同じ", 540, 1330, 52, RED, alpha=k2)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 答え合わせ2: 1万回（マス目 ＋ 平均の差のヒストグラム） ----------
GRID_CELL = 4
GRID_X, GRID_Y = 60, 640                           # 本体の座標（紙の中心にそろえるため draw 側で translate(PAGE_DX) する）
HX0, HX1 = 500, 880                                # ヒストグラムの横の範囲（本体の座標）
H_BASE, H_MAXH = GRID_Y + 100 * GRID_CELL, 330
H_EDGES = np.arange(-30.0, 30.01, 3.0)             # 平均の差（片側あけ − 2列）の階級。正＝2列が早い


def ease_out_lin(x):
    return clamp01(x)


_HIST = {}


def hist_bins():
    if "b" not in _HIST:
        dm = shown()["dm"]
        b = np.clip(np.digitize(dm, H_EDGES) - 1, 0, len(H_EDGES) - 2)
        _HIST["b"] = b
        _HIST["max"] = int(np.bincount(b, minlength=len(H_EDGES) - 1).max())
    return _HIST["b"], _HIST["max"]


def draw_grid(ctx, t, a):
    if a <= 0:
        return
    S = shown()
    win = (S["dm"] > 0)
    k = int(round(N_TRIALS * ease_out_lin((t - T_D0) / D_DUR)))
    cols = np.zeros((N_TRIALS, 4), np.uint8)
    cols[:] = bgra("#e6e0cf")
    cols[:k][win[:k]] = bgra(SKY)
    cols[:k][~win[:k]] = bgra(ORANGE)
    surf, _keep = grid_image(cols.reshape(100, 100, 4), cell=GRID_CELL, gap_color=PAPER, gap=1)
    ctx.push_group()
    ctx.set_source_surface(surf, GRID_X, GRID_Y)
    ctx.paint()
    gw = 100 * GRID_CELL
    note.pen_line(ctx, GRID_X - 4, GRID_Y - 4, GRID_X + gw + 4, GRID_Y - 4, INK, seed=21, width=3, alpha=0.7)
    note.pen_line(ctx, GRID_X - 4, GRID_Y + gw + 4, GRID_X + gw + 4, GRID_Y + gw + 4, INK, seed=22, width=3, alpha=0.7)
    # ヒストグラム
    b, hmax = hist_bins()
    cnt = np.bincount(b[:k], minlength=len(H_EDGES) - 1)
    nb = len(cnt)
    bw = (HX1 - HX0) / nb
    for j in range(nb):
        h = H_MAXH * cnt[j] / hmax
        if h < 1:
            continue
        col = SKY if j >= nb // 2 else ORANGE
        ctx.set_source_rgba(*hexrgb(col, 0.85))
        ctx.rectangle(HX0 + j * bw + 1, H_BASE - h, bw - 2, h)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(2)
        ctx.stroke()
    note.pen_line(ctx, HX0 - 6, H_BASE, HX1 + 6, H_BASE, INK, seed=23, width=3, alpha=0.8)
    xm = (HX0 + HX1) / 2
    note.pen_line(ctx, xm, H_BASE - H_MAXH - 14, xm, H_BASE + 8, note.PENCIL, seed=24, width=2.5, alpha=0.8)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    text(ctx, "1マス = 1回", GRID_X + gw / 2, 612, 28, INK, bold=False, alpha=a)
    text(ctx, "1回ごとの平均の差（秒）", (HX0 + HX1) / 2, 612, 28, INK, bold=False, alpha=a)
    for v in (-20, 0, 20):
        text(ctx, ("+%d" % v) if v > 0 else str(v).replace("-", "−"), HX0 + (v + 30) / 60 * (HX1 - HX0), H_BASE + 30, 26, INK, bold=False, alpha=a)
    text(ctx, "← 片側あけ", HX0 - 4, H_BASE + 74, 24, C_ORANGE, align="left", bold=False, alpha=a)
    text(ctx, "2列 →", HX1 + 4, H_BASE + 74, 24, C_BLUE, align="right", bold=False, alpha=a)
    nb_win = int(win[:k].sum())
    number_row(ctx, [("2列が早い ", INK), (fmt_n(nb_win), C_BLUE), ("　片側あけが早い ", INK), (fmt_n(k - nb_win), C_ORANGE)], 1170, a, size=34)


# ---------- ひねり: 電車が次々来たら？ ----------
_RR = None


def rush_runs():
    global _RR
    if _RR is None:
        tr = rush_trial(RUSH_SEED, 100.0)
        _RR = (Run(tr, "A", L_BASE), Run(tr, "B", L_BASE))
    return _RR


def _dots(ctx, pts, col, r):
    if not pts:
        return
    ctx.new_path()
    for (x, y) in pts:
        ctx.new_sub_path()
        ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(col))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.75))
    ctx.set_line_width(1.0)
    ctx.stroke()


def draw_rush_block(ctx, G, run, tau):
    draw_strip(ctx, G, tau, L_BASE, moving=False)
    ctx.save()
    ctx.rectangle(50, G.yu - 70, G.vis_right + 40 - 50, 190)
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
    _dots(ctx, pts[True], STAND_COL, G.qsp * 0.40)
    _dots(ctx, pts[False], WALK_COL, G.qsp * 0.40)
    x = run.pos(tau)
    on = {True: [], False: []}
    for i in np.where(~np.isnan(x))[0]:
        if x[i] > L_BASE:
            continue
        on[bool(run.stand[i])].append((G.x0 + x[i] * G.pxm, G.yu + G.lw * run.lane[i]))
    _dots(ctx, on[True], STAND_COL, 5.0)
    _dots(ctx, on[False], WALK_COL, 5.0)
    ctx.restore()
    return int(wait.sum())


def draw_rush(ctx, t, a, dim=1.0):
    """ひねり: 電車が100秒おきに100人ずつ。片側あけは立つ列の行列が伸び続け、2列は伸びない"""
    if a <= 0:
        return
    S = shown()
    R100 = S["rush"][I_T100]
    RA, RB = rush_runs()
    tau = TAU_MAX * clamp01((t - T_RU0) / RU_DUR)
    tt = t - T_TW
    ctx.push_group()
    ctx.push_group()
    note.banner(ctx, "電車が次々来たら？", 560, 665, a=ease_out(tt / 0.25), t_rel=tt, size=50)
    ctx.pop_group_to_source()
    ctx.paint()
    k = ease_out((t - T_TW - 0.5) / 0.3)
    if k > 0:
        ctx.push_group()
        text(ctx, f"100秒おきに100人　経過 {int(tau // 60)}分", 580, 752, 30, INK, bold=False)
        text(ctx, "片側あける", 120, 808, 38, INK, align="left")
        nA = draw_rush_block(ctx, G_RA, RA, tau)
        number_row(ctx, [("待つ人 ", INK), (f"{nA}", C_ORANGE), ("人", INK)], 808, 1.0, size=38, cx=830)
        text(ctx, "2列で立つ", 120, 978, 38, INK, align="left")
        nB = draw_rush_block(ctx, G_RB, RB, tau)
        number_row(ctx, [("待つ人 ", INK), (f"{nB}", C_BLUE), ("人", INK)], 978, 1.0, size=38, cx=830)
        note.legend(ctx, [(STAND_COL, "立つ人"), (WALK_COL, "歩く人")], 1150, 26)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k)
    if t >= T_RES:
        kr = ease_out((t - T_RES) / 0.3)
        text(ctx, "15本ぶんの平均（1万回）", 580, 1215, 28, note.PENCIL, bold=False, alpha=kr)
        number_row(ctx, [("1人あたり ", INK), ("片側 ", INK), (f"{int(round(R100['A']))}", C_ORANGE), ("秒", INK),
                         (" ／ 2列 ", INK), (f"{int(round(R100['B']))}", C_BLUE), ("秒", INK)], 1268, kr, size=42, cx=545)
    if t >= T_TWS and t < T_Q + 0.35:
        ks = ease_out((t - T_TWS) / 0.3) * (1 - ease_out((t - T_Q) / 0.35))
        note.sticky(ctx, "片側あけは、行列が伸び続ける", 560, 1385, 44, "pink", fg=RED, a=ks, tilt=-0.015)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a * dim)


def body(ctx, t):
    # --- 答え合わせ2: 1万回のマス目とヒストグラム
    if T_G0 <= t < T_TW + 0.3:
        ga = ease((t - T_G0 - 0.2) / 0.3) * (1 - ease((t - T_TW) / 0.3))
        draw_grid(ctx, t, ga)
        if t >= T_ST2:
            b = ease_out((t - T_ST2) / 0.3) * ga
            note.sticky(ctx, "平均の差 1秒もない\nほぼ同じ", 560, 1320, 44, "pink", fg=RED, a=b, tilt=-0.015)
    # --- 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで電車が続くと、\n差が開くの？", 520, 715, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 520, 905, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    # 答え合わせ1（紙の座標のまま）
    if T_GO - 0.1 <= t < T_G0 + 0.25:
        a = ease((t - (T_GO - 0.1)) / 0.4) * (1 - ease((t - T_G0) / 0.2))
        draw_answer1(ctx, t, a)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    # ひねり（紙の座標のまま）
    if t >= T_TW:
        draw_rush(ctx, t, ease((t - T_TW) / 0.3), dim=1 - 0.85 * ease_out((t - T_Q) / 0.35))
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def band_noise(dur, lo, hi, seed, rms, edge_lo=40.0, edge_hi=200.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def esc_hum(dur):
    """エスカレーターの低い動作音: 80〜400Hz のゆるいノイズ＋ごく小さな55Hzのうなり。うるさくない"""
    x = band_noise(dur, 80.0, 420.0, 3, 0.030, 60.0, 250.0)
    tt = np.arange(len(x)) / SR
    x += 0.010 * np.sin(2 * np.pi * 55 * tt) * (1 + 0.3 * np.sin(2 * np.pi * 0.4 * tt))
    return x * np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.6)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    hum = esc_hum(DURATION)
    tt = np.arange(len(hum)) / SR
    gain = np.where((tt >= T_G0) & (tt < T_TW), 0.35, 1.0)
    mx.add(0, hum * gain, 1.0, bgm=True)
    INTRO.audio(mx)
    # 答え合わせ1: 上り終えるたびに小さな音
    rng = np.random.default_rng(6)
    for run, f0 in ((RUN_A, 1500.0), (RUN_B, 2100.0)):
        for ex in np.sort(run.ex):
            tv = video_of_tau(float(ex))
            mx.add(tv, tick(float(rng.uniform(f0, f0 * 1.6)), 0.03), 0.035)
    mx.add(T_GO + 0.1, blip(880.0, 0.2), 0.25)
    mx.add(T_RB, blip(1046.5, 0.25), 0.45)
    mx.add(T_RA, blip(784.0, 0.25), 0.45)
    mx.add(T_RA + 0.3, chord([261.6, 329.6, 392.0], 1.2), 0.3)
    # 1万回
    mx.add(T_G0 - 0.5, riser(0.9), 0.5)
    beat(mx, T_D0, T_D1, bpm=124, vol=0.5, accel=True)
    for b in range(int(D_DUR * 8)):
        mx.add(T_D0 + b / 8, tick(float(rng.uniform(1700, 3300)), 0.03), 0.05 + 0.04 * (b / (D_DUR * 8)))
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST2, blip(659.3, 0.15), 0.35)
    # ひねり: 電車が着くたびに小さな音（15本）
    mx.add(T_TW, riser(0.8), 0.45)
    for k in range(N_TRAIN):
        mx.add(T_RU0 + RU_DUR * (k * 100.0) / TAU_MAX, tick(float(rng.uniform(900, 1300)), 0.05), 0.07)
    mx.add(T_RU0, blip(523.3, 0.2), 0.35)
    mx.add(T_TWS, bell(880.0, 1.2), 0.4)
    mx.add(T_RES, blip(659.3, 0.2), 0.35)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    S = shown()
    checks = list(closed_form_checks())
    # (3b) 閉じた式: 全員が同時に着いて全員が立つ2列 → 1人あたりの平均 = 1.6 × (0,0,1,1,…,49,49 の平均) + 長さ ÷ 0.5
    tr = dict(a=np.zeros(N), walker=np.zeros(N, bool), gs=np.full(N, 2 * PITCH), gw=np.full(N, 1.2), w=np.full(N, 0.5))
    for L in (10.0, 35.0):
        sim = float(metrics(tr, "B", L)["mean"][0])
        checks.append((f"閉じた式 全員同時・2列・長さ{L:.0f}m: 1人あたりの平均（秒）", sim, 1.6 * 24.5 + L / VE, 1e-6))
    # (3c) 閉じた式: 立つ人だけが100人ずつ同時に T=100秒おき15本 → 片側あけ（立つ列1つ）。n番目の人は 1.6×n 秒に乗る → 平均 = 1.6×(1500−1)/2 − 100×mean(⌊n/100⌋) + 長さ÷0.5
    n = N * N_TRAIN
    tr = dict(a=np.repeat(np.arange(N_TRAIN) * 100.0, N), walker=np.zeros(n, bool), gs=np.full(n, 0.8), gw=np.full(n, 1.2), w=np.full(n, 0.5))
    sim = float(metrics(tr, "A", L_BASE)["mean"][0])
    theory = 1.6 * (n - 1) / 2 - 100 * np.mean(np.arange(n) // 100) + L_BASE / VE
    checks.append(("閉じた式 ラッシュ（全員立つ・片側あけ・100人ずつ同時・100秒おき）: 1人あたりの平均（秒）", sim, float(theory), 1e-6))
    # (3d) 連結の確認: 電車の間隔が十分あいていれば、15本ぶんの平均 = 1本ずつの平均の平均
    trs = [make_trial(777 * 20 + k) for k in range(N_TRAIN)]
    big = rush_trial(777, 5000.0)
    for mode in ("A", "B"):
        one = float(np.mean([metrics(t, mode, L_BASE)["mean"][0] for t in trs]))
        checks.append((f"ラッシュの連結（間隔5000秒）= 1本ずつの平均の平均 mode={mode}", float(metrics(big, mode, L_BASE)["mean"][0]), one, 1e-6))
    # (3) 別の実装（0.02秒刻み）
    rng = np.random.default_rng(2)
    for mode in ("A", "B"):
        for L in (20.0, 35.0):
            worst = 0.0
            for sd in rng.integers(0, 100000, 6):
                tr = make_trial(int(sd))
                ev = float(metrics(tr, mode, L)["make"][0])
                ts = timestep(tr, mode, L)
                worst = max(worst, abs(ev - ts))
            checks.append((f"別の実装（0.02秒刻み）との差 最大（秒） mode={mode} 長さ{L:.0f}m", worst, 0.0, 1.2))
    # (4) 別の乱数で1万回やり直し
    R = S["rush"][I_T100]
    checks += [
        ("別の乱数の1万回: 1人あたり平均の差（秒）", S["mean_diff_again"], S["mean_diff"], 0.6),
        ("別の乱数の1万回: 平均で2列が早い割合", S["win_again"] / N_TRIALS, S["win"] / N_TRIALS, 0.03),
        ("別の乱数の1万回: 1人あたり平均（片側あける）", S["A_mean_again"], S["A_mean"], 0.8),
        ("別の乱数の1万回: 1人あたり平均（2列）", S["B_mean_again"], S["B_mean"], 0.8),
        ("別の乱数の1万回: 最後の人の差（秒）", S["mk_diff_again"], S["mk_diff"], 0.8),
        ("別の乱数の1万回: 歩きたい人の平均（片側あける）", S["A_walk_again"], S["A_walk"], 0.8),
        ("別の乱数の1万回: ラッシュ T=100 片側あけの平均", R["A_again"], R["A"], 1.5),
        ("別の乱数の1万回: ラッシュ T=100 2列の平均", R["B_again"], R["B"], 0.5),
    ]
    # (5) 画面の数字の丸め
    r = lambda x: float(int(round(x)))
    checks += [
        ("画面「平均の差 1秒もない」: どちらの1万回でも |平均の差| < 1秒", float(abs(S["mean_diff"]) < 1 and abs(S["mean_diff_again"]) < 1), 1.0, 0.0),
        ("画面「ラッシュ 片側 ○秒」の整数が別の乱数と同じ", r(R["A"]), r(R["A_again"]), 0.0),
        ("画面「ラッシュ 2列 ○秒」の整数が別の乱数と同じ", r(R["B"]), r(R["B_again"]), 0.0),
        ("見本: 画面の「1人あたり 平均」片側が1万回の平均と1秒以内", r(A_AVG), r(S["A_mean"]), 1.0),
        ("見本: 画面の「1人あたり 平均」2列が1万回の平均と1秒以内", r(B_AVG), r(S["B_mean"]), 1.0),
        ("見本: 画面の「最後の人」の差が1万回の平均付近（±5秒）", float(abs((A_MAKE - B_MAKE) - S["mk_diff"]) <= 5), 1.0, 0.0),
    ]
    for rr in S["rush"]:
        checks.append((f"ラッシュ T={rr['T']:.0f}秒 片側の平均（説明文の表）が別の乱数と整数で1秒以内", r(rr["A"]), r(rr["A_again"]), 1.0))
    # (6) 答えは C、ひねりはラッシュ
    nw = int(TR["walker"].sum())
    ra = rush_runs()[0]
    checks += [
        ("答えは C: 1人あたり平均の差が1秒未満", float(abs(S["mean_diff"]) < 1), 1.0, 0.0),
        ("答えは C: 2列が早い回が45〜55%", float(0.45 <= S["win"] / N_TRIALS <= 0.55), 1.0, 0.0),
        ("最後の人は2列が早い（20秒以上・95%以上の回）", float(S["mk_diff"] >= 20 and S["mk_win"] / N_TRIALS >= 0.95), 1.0, 0.0),
        ("ひねり: ラッシュ T=100 で片側あけの平均が2列の1.5倍以上", float(R["A"] >= 1.5 * R["B"]), 1.0, 0.0),
        ("ひねり: ラッシュ T=180 では差が2%以内", float(abs(S["rush"][-1]["A"] - S["rush"][-1]["B"]) <= 2.0), 1.0, 0.0),
        ("見本の歩きたい人は25人", float(nw), 25.0, 0.0),
        ("ラッシュ見本: 片側あけの平均が1万回の平均付近（±5%）", float(abs(float((ra.ex - rush_runs()[0].tr["a"]).mean()) - R["A"]) <= 0.05 * R["A"]), 1.0, 0.0),
        ("ラッシュ見本: 画面の最大の行列が x≥100 に収まる（点の列数）", float(max_queue_cols() * RQSP + 14 <= RX0 - 100), 1.0, 0.0),
    ]
    check_answers(checks)


def max_queue_cols():
    """ラッシュ見本で、片側あけの立つ列の行列がいちばん長くなるときの点の列数"""
    ra = rush_runs()[0]
    mx = 0
    for tau in np.arange(0, TAU_MAX + 1, 10.0):
        wait, rk = ra.waiting(tau)
        sel = wait & ra.stand
        if sel.any():
            mx = max(mx, int(rk[sel].max()) // G_RA.rows_u + 1)
    return mx


if __name__ == "__main__" and "--compute" not in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    S = shown()
    R = S["rush"][I_T100]
    print(f"見本の種 {DEMO_SEED}（歩きたい人 {int(TR['walker'].sum())}人）/ 長さ={DURATION:.1f}秒")
    print(f"見本: 1人あたり平均 片側 {A_AVG:.1f} 2列 {B_AVG:.1f} ／ 最後の人 片側 {A_MAKE:.1f} 2列 {B_MAKE:.1f}")
    print(f"1万回: 平均の差 {S['mean_diff']:.2f}秒 2列が早い {S['win']}回 / 最後の人の差 {S['mk_diff']:.1f}秒 / ラッシュ T=100: 片側 {R['A']:.1f} 2列 {R['B']:.1f}")
    print(f"時間割: T_GO={T_GO:.2f} T_RB={T_RB:.2f} T_RA={T_RA:.2f} T_G0={T_G0:.2f} T_REV={T_REV:.2f} T_TW={T_TW:.2f} T_RU0={T_RU0:.2f} T_Q={T_Q:.2f}")
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0]
        ts = [x for x in ts if x < DURATION]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
