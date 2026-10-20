"""渋滞で車線を変える車は、早く着く？ 2車線の渋滞5kmを、すぐ車線を変える車と変えない車で1万回ずつ走る。— 2026-10-17 作成（公開予定 10/20）

モデル（自作。2車線のセル・オートマトン。Nagel & Schreckenberg 1992 の1車線のモデルを2車線にしたもの）
  道: 2車線・1マス7.5m（車1台ぶん）・1歩＝1秒。長さ667マス（5,002.5m）の輪にして、車の数を一定に保つ（渋滞の5kmがずっと続く道と同じ）。
  車: 1車線あたり 200台（1kmあたり約40台）。両車線とも同じ台数・同じ決まりで走る（2つの車線は統計的に同じ）。
      1秒ごとに Nagel–Schreckenberg の4つの決まり: ①最高速度3マス/秒（時速81km）まで1つ加速 ②前の車との
      すき間より速ければ、すき間まで落とす ③でたらめに1つ減速（走っていれば確率0.2、止まっていれば確率0.5＝
      「止まった車は出だしが遅れる」slow-to-start。これで止まっては進む渋滞の波ができる）④進む。
  ほかの車の車線変更: 前がつかえていて（すき間が「速度＋1」未満）、隣の車線の前のすき間のほうが広く、
      隣の真横が空いていて、隣の後ろの車がブレーキを踏まずにすむとき、1秒あたり確率0.2で隣へ移る
      （Rickert ら 1996 の2車線の決まりと同じ形）。
  くらべる2台（スタートのとき隣どうしの車線に並んだ2台。どちらの車線から出るかはでたらめ）:
      「変えない車」… 一度も車線を変えない。
      「変える車」  … 前方90m（12マス）の隣の車線の車の平均速度が、自分の車線の前方90mの平均より
                      時速13.5km（0.5マス/秒）以上速いと「隣のほうが流れている」と判断して、ウインカーを出す。
                      合図は3秒（道路交通法施行令21条「進路を変えようとするときの3秒前」）。3秒たってから、
                      隣の真横が空き、隣の後ろの車がブレーキを踏まずにすむ・前に1マス以上のすき間がある
                      ときに移る。それまでに隣のほうが流れていなくなったら合図をやめる。
                      移った秒と次の秒は加速しない（合流してなじむまでの時間）。
  1回ぶん: 車をでたらめに置き、400秒ならしてから、2台を並べてスタート。それぞれが5,002.5m（1周）進むまでの時間を測る。1万回。

問い: 「渋滞で車線を変える車は、早く着く？」（2行）
      A 変える ／ B 変えない ／ C ほぼ同じ
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1回ごとに「変えない車の時間 − 変える車の時間」÷「変えない車の時間」を出し、1万回の真ん中の値（中央値）が
      ±3%未満なら C、+3%以上なら A（変える車が早い）、−3%以下なら B（変えない車が早い）。
ひねり: 「変えない車」から見た隣の車線。Redelmeier & Tibshirani（1999・2000）と同じ数え方で、1秒ごとに
      隣の車線の車に「抜かれた秒」と「抜いた秒」を数える（台数も数える）。
締め: 「あなたは、変える派？」（答えは出さない）

乱数の種は見本（並んで走る2台）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
照合（check_answers）は run_checks を参照。
"""
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "shasen-henkou"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
CELL = 7.5                                        # 1マス（m）
R = 667                                           # 輪の長さ（マス）= 5,002.5m
TRIP = R                                          # 1周 = 約5km 走る
VMAX = 3                                          # 最高速度（マス/秒）= 時速81km
P_SLOW = 0.2                                      # 走っている車が、でたらめに1つ減速する確率
P_START = 0.5                                     # 止まっている車が、出だしで遅れる確率（slow-to-start）
RHO = 0.30                                        # 1マスあたりの車の数（1車線）
N_LANE = int(round(RHO * R))                      # 1車線の台数
N = 2 * N_LANE
P_BG = 0.2                                        # ほかの車が、条件がそろったとき1秒で隣へ移る確率
LOOK = 12                                         # 前方を見る範囲（マス）= 90m
BACK_LOOK = 2                                     # 隣の車線は、少し後ろ（真横あたり）から見る
THRESH = 0.5                                      # 「隣のほうが流れている」とする速度の差（マス/秒）= 時速13.5km
SIGNAL = 3                                        # 合図の秒数
MERGE = 2                                         # 移った秒から、加速しない秒数
WARM = 400                                        # ならしの秒数
T_MAX = 6000
N_TRIAL = 10000
KMH = CELL * 3.6                                  # 1マス/秒 = 時速27km

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_REL = 0.03


def answer_by_rule(m):
    """m = 1万回の「(変えない車の時間 − 変える車の時間) ÷ 変えない車の時間」の中央値"""
    if abs(m) < RULE_REL:
        return 2                                  # C ほぼ同じ
    if m > 0:
        return 0                                  # A 変える（変える車が早い）
    return 1                                      # B 変えない


# ---------- 2車線のセル・オートマトン ----------
BIG = 1 << 30


def _grids(x, lane, v):
    n = x.shape[0]
    rows = np.arange(n)[:, None]
    occ = np.zeros((n, 2, R), bool)
    vg = np.zeros((n, 2, R), np.int16)
    occ[rows, lane, x] = True
    vg[rows, lane, x] = v
    ar = np.arange(R)
    pos = np.where(occ, ar, BIG)
    d = np.concatenate([pos, pos + R], -1)
    nxt = np.minimum.accumulate(d[..., ::-1], axis=-1)[..., ::-1]          # nxt[p] = p 以上で最初に車がいるマス
    neg = np.where(occ, ar, -BIG)
    prv = np.maximum.accumulate(np.concatenate([neg - R, neg], -1), axis=-1)   # prv[p+R] = p 以下で最後に車がいるマス
    return occ, vg, nxt, prv


def _win_mean(vg, occ, b, l, a, length):
    """車線 l のマス a〜a+length−1（輪）の車の平均速度。車がいなければ VMAX"""
    n = len(b)
    idx = (a[:, None] + np.arange(length)[None, :]) % R
    o = occ[b[:, None], l[:, None], idx]
    s = vg[b[:, None], l[:, None], idx]
    cnt = o.sum(1)
    return np.where(cnt > 0, (s * o).sum(1) / np.maximum(cnt, 1), float(VMAX)), cnt


def simulate(seed, n, hop=True, bg=True, record=False, p_bg=P_BG, thresh=THRESH, signal=SIGNAL, merge=MERGE,
             vmax=VMAX, p_slow=P_SLOW, p_start=P_START, speeds=False):
    """n 回ぶん。car 0 = 変える車（hop=False なら変えない）、car 1 = 変えない車。
    返り値: 2台の着いた時間・変える車の車線変更の回数・変えない車の「抜かれた秒/抜いた秒/抜かれた台数/抜いた台数」"""
    rng = np.random.default_rng(seed)
    rows = np.arange(n)
    # 車をでたらめに置く（各車線 N_LANE 台）
    x = np.zeros((n, N), np.int64)
    for l in range(2):
        cells = np.argsort(rng.random((n, R)), 1)[:, :N_LANE]
        x[:, l * N_LANE:(l + 1) * N_LANE] = np.sort(cells, 1)
    lane = np.repeat(np.array([0] * N_LANE + [1] * N_LANE)[None, :], n, 0)
    v = np.zeros((n, N), np.int64)
    tracked = np.zeros(N, bool)
    tracked[:2] = True
    sig = np.zeros(n, np.int64)                   # 合図を出してからの秒（−1 は出していない）
    sig[:] = -1
    mcd = np.zeros(n, np.int64)                   # 加速しない残りの秒
    started = False
    prog = np.zeros((n, 2), np.int64)
    T = np.full((n, 2), np.nan)
    n_chg = np.zeros(n, np.int64)
    ep_over = np.zeros(n, np.int64)
    ep_pass = np.zeros(n, np.int64)
    c_over = np.zeros(n, np.int64)
    c_pass = np.zeros(n, np.int64)
    rec = [] if record else None
    rec_sig = [] if record else None
    v_sum = np.zeros(n)
    n_sum = 0
    bg_cnt = np.zeros(n)
    bg_dist = np.zeros(n)
    vn_prev_sum = np.zeros(n)
    t = -WARM
    while t < T_MAX:
        if t == 0 and not started:
            # 2台を選ぶ: 変える車＝でたらめな車線のでたらめな1台、変えない車＝隣の車線でいちばん近い1台。並べ替えて car 0, 1 に
            started = True
            l0 = rng.integers(0, 2, n)
            perm = np.tile(np.arange(N), (n, 1))
            for i in range(n):
                c0 = np.nonzero(lane[i] == l0[i])[0]
                j0 = c0[rng.integers(len(c0))]
                c1 = np.nonzero(lane[i] != l0[i])[0]
                dd = (x[i, c1] - x[i, j0] + R // 2) % R - R // 2
                best = np.nonzero(np.abs(dd) == np.abs(dd).min())[0]
                j1 = c1[best[rng.integers(len(best))]]
                p = perm[i]
                k0 = int(np.nonzero(p == j0)[0][0])
                p[0], p[k0] = p[k0], p[0]
                k1 = int(np.nonzero(p == j1)[0][0])
                p[1], p[k1] = p[k1], p[1]
            x = np.take_along_axis(x, perm, 1)
            lane = np.take_along_axis(lane, perm, 1)
            v = np.take_along_axis(v, perm, 1)
            if record:                                          # ならしの記録も、選んだ2台が car 0, 1 になるように並べ替える
                rec = [np.stack([np.take_along_axis(fr[j], perm.astype(np.int64), 1) for j in range(3)]) for fr in rec]
        occ, vg, nxt, prv = _grids(x, lane, v)
        gap = np.take_along_axis(nxt.reshape(n, -1), (lane * 2 * R + x + 1), 1) - x - 1
        ol = 1 - lane
        beside = occ[rows[:, None], ol, x]
        gap_o = np.take_along_axis(nxt.reshape(n, -1), (ol * 2 * R + x + 1), 1) - x - 1
        q = np.take_along_axis(prv.reshape(n, -1), (ol * 2 * R + x - 1 + R), 1)
        gap_b = (x - 1) - q
        v_f = vg[rows[:, None], ol, q % R]
        safe = ~beside & (gap_b >= v_f) & (gap_o >= 1)
        move_lane = np.zeros((n, N), bool)
        if bg:
            want = (gap < np.minimum(v + 1, vmax)) & (gap_o > gap) & safe
            if started:
                want[:, :2] = False
            move_lane |= want & (rng.random((n, N)) < p_bg)
        if not started:
            # ならしの間は、car 0/1 もほかの車と同じ
            pass
        if started and hop:
            h = 0
            xh, lh = x[:, h], lane[:, h]
            own, _ = _win_mean(vg, occ, rows, lh, xh + 1, LOOK)
            oth, _ = _win_mean(vg, occ, rows, 1 - lh, (xh - BACK_LOOK) % R, LOOK + BACK_LOOK)
            fin = ~np.isnan(T[:, 0])
            better = oth >= own + thresh
            still = oth > own
            idle = (sig < 0) & (mcd == 0) & better & ~fin
            sig = np.where(idle, 0, sig)
            going = sig >= 0
            sig = np.where(going & ~still, -1, sig)                # 隣が流れなくなったら合図をやめる
            go = (sig >= signal) & safe[:, h] & ~fin
            move_lane[:, 0] = go
            n_chg += go
            sig = np.where(go, -1, np.where(sig >= 0, sig + 1, sig))
            mcd = np.where(go, merge, np.maximum(mcd - 1, 0))
            if record:
                rec_sig.append(sig.copy())
        elif record:
            rec_sig.append(np.full(n, -1))
        if started:
            bg_cnt += move_lane[:, 2:].sum(1)
            bg_dist += vn_prev_sum
        nolc = mcd > 0                                              # この秒に加速しない（移った秒を含む）
        lane = np.where(move_lane, ol, lane)
        # 速さの更新（Nagel–Schreckenberg ＋ slow-to-start）
        occ, vg, nxt, prv = _grids(x, lane, v)
        gap = np.take_along_axis(nxt.reshape(n, -1), (lane * 2 * R + x + 1), 1) - x - 1
        acc = np.minimum(v + 1, vmax)
        if started and hop:
            acc[:, 0] = np.where(nolc, v[:, 0], acc[:, 0])
        vn = np.minimum(acc, gap)
        p = np.where(v == 0, p_start, p_slow)
        vn = np.where((rng.random((n, N)) < p) & (vn > 0), vn - 1, vn)
        # 変えない車から見た、隣の車線の車（抜かれた・抜いた）
        if started:
            s = 1
            xs, ls = x[:, s:s + 1], lane[:, s:s + 1]
            r0 = (x - xs + R // 2) % R - R // 2
            r1 = r0 + vn - vn[:, s:s + 1]
            other = (lane != ls) & (np.abs(r0) < 60)
            over = other & (r0 <= 0) & (r1 > 0)
            pas = other & (r0 >= 0) & (r1 < 0)
            live = np.isnan(T[:, 1])
            ep_over += (over.any(1) & live)
            ep_pass += (pas.any(1) & live)
            c_over += over.sum(1) * live
            c_pass += pas.sum(1) * live
        if record:
            rec.append(np.stack([x, lane, vn]).astype(np.int16))
        if speeds and started:
            v_sum += vn.mean(1)
            n_sum += 1
        x = (x + vn) % R
        if started:
            for k in (0, 1):
                pn = prog[:, k] + vn[:, k]
                arr = np.isnan(T[:, k]) & (pn >= TRIP)
                frac = (TRIP - prog[:, k]) / np.maximum(vn[:, k], 1)
                T[:, k] = np.where(arr, t + frac, T[:, k])
                prog[:, k] = pn
        v = vn
        vn_prev_sum = vn[:, 2:].sum(1)
        t += 1
        if started and not np.isnan(T).any() and not record:
            break
        if record and started and not np.isnan(T).any() and t > np.nanmax(T) + 40:
            break
    out = dict(bg_per_km=bg_cnt / np.maximum(bg_dist * CELL / 1000, 1e-9), T=T, n_chg=n_chg, ep_over=ep_over, ep_pass=ep_pass, c_over=c_over, c_pass=c_pass)
    if speeds:
        out["v_all"] = float(np.mean(v_sum)) / max(1, n_sum)
    if record:
        out["rec"] = np.array(rec)                 # (秒, 3, n, N): 位置・車線・その秒の速さ（−WARM 秒から）
        out["sig"] = np.array(rec_sig)
    return out


# ---------- 計算 ----------
SEED_MAIN = 20261020
CHUNK = 250


def _job(args):
    seed, n, kw = args
    r = simulate(seed, n, **kw)
    return {k: v for k, v in r.items()}


def run_many(seed0, n_total, workers=None, **kw):
    jobs = [(seed0 * 1000 + i, min(CHUNK, n_total - i * CHUNK), kw) for i in range((n_total + CHUNK - 1) // CHUNK)]
    with ProcessPoolExecutor(workers or max(1, (os.cpu_count() or 4) - 2)) as ex:
        res = list(ex.map(_job, jobs))
    return {k: np.concatenate([r[k] for r in res]) for k in res[0] if k != "v_all"}


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    m = run_many(SEED_MAIN, N_TRIAL)
    print(f"本編 {time.time() - t0:.0f}秒")
    ctl = run_many(SEED_MAIN + 1, 2000, hop=False)            # 照合: 2台とも変えない → 差はほぼ0
    nobg = run_many(SEED_MAIN + 2, 2000, bg=False)            # 概要欄: ほかの車が車線を変えない道
    free = run_many(SEED_MAIN + 3, 2000, signal=0, merge=0)   # 概要欄: 合図も合流の遅れもない（手間ゼロ）
    eager = run_many(SEED_MAIN + 4, 2000, thresh=0.01)        # 概要欄: 少しでも隣が速ければ変える
    np.savez_compressed(OUT / "data.npz", **{f"m_{k}": v for k, v in m.items()}, **{f"c_{k}": v for k, v in ctl.items()},
                        **{f"n_{k}": v for k, v in nobg.items()}, **{f"f_{k}": v for k, v in free.items()},
                        **{f"e_{k}": v for k, v in eager.items()})
    print(f"計算 {time.time() - t0:.0f}秒")


if __name__ == "__main__" and "--compute" in sys.argv:
    compute()
    sys.exit(0)


# ---------- 結果 ----------
_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = OUT / "data.npz"
        if not f.exists():
            raise SystemExit(f"{f} がありません。先に python sims/{SLUG}.py --compute を実行してください")
        z = np.load(f)
        _DATA = {k: z[k] for k in z.files}
    return _DATA


def rel_of(T):
    """(変えない車の時間 − 変える車の時間) ÷ 変えない車の時間。＋なら変える車が早い"""
    return (T[:, 1] - T[:, 0]) / T[:, 1]


def zone_of(rel):
    """0: 変える車が3%以上早い / 1: 変えない車が3%以上早い / 2: 差が3%未満"""
    return np.where(rel >= RULE_REL, 0, np.where(rel <= -RULE_REL, 1, 2))


_SHOWN = None


def shown():
    global _SHOWN
    if _SHOWN is not None:
        return _SHOWN
    d = data()
    T = d["m_T"]
    rel = rel_of(T)
    diff = T[:, 1] - T[:, 0]
    z = zone_of(rel)
    out = dict(rel=rel, diff=diff, zone=z, cnt=np.bincount(z, minlength=3),
               rel_med=float(np.median(rel)), rel_mean=float(np.mean(rel)), diff_med=float(np.median(diff)),
               diff_mean=float(np.mean(diff)), Th_med=float(np.median(T[:, 0])), Ts_med=float(np.median(T[:, 1])),
               win_h=float(np.mean(diff > 0)), chg_mean=float(np.mean(d["m_n_chg"])), chg_med=float(np.median(d["m_n_chg"])),
               ep_over=float(np.mean(d["m_ep_over"])), ep_pass=float(np.mean(d["m_ep_pass"])),
               c_over=float(np.mean(d["m_c_over"])), c_pass=float(np.mean(d["m_c_pass"])),
               share_over=float(np.mean(d["m_ep_over"] > d["m_ep_pass"])),
               kmh_s=float(TRIP * CELL / np.median(T[:, 1]) * 3.6), kmh_h=float(TRIP * CELL / np.median(T[:, 0]) * 3.6))
    for p in ("c", "n", "f", "e"):
        Tp = d[f"{p}_T"]
        out[f"{p}_rel_med"] = float(np.median(rel_of(Tp)))
        out[f"{p}_diff_med"] = float(np.median(Tp[:, 1] - Tp[:, 0]))
        out[f"{p}_chg"] = float(np.mean(d[f"{p}_n_chg"]))
        out[f"{p}_ep_over"] = float(np.mean(d[f"{p}_ep_over"]))
        out[f"{p}_ep_pass"] = float(np.mean(d[f"{p}_ep_pass"]))
        out[f"{p}_c_over"] = float(np.mean(d[f"{p}_c_over"]))
        out[f"{p}_c_pass"] = float(np.mean(d[f"{p}_c_pass"]))
    _SHOWN = out
    return out


def report():
    sh = shown()
    print(f"中央値 rel {sh['rel_med']:+.4f}（平均 {sh['rel_mean']:+.4f}）  差の中央値 {sh['diff_med']:+.1f}秒（平均 {sh['diff_mean']:+.1f}）"
          f"  時間の中央値 変える {sh['Th_med']:.0f}秒 / 変えない {sh['Ts_med']:.0f}秒（時速 {sh['kmh_h']:.1f} / {sh['kmh_s']:.1f}km）")
    print(f"  区分 変える早い/変えない早い/ほぼ同じ = {sh['cnt']}  変える車が早かった回 {sh['win_h']:.3f}  車線変更 平均 {sh['chg_mean']:.2f}回（中央値 {sh['chg_med']:.0f}）")
    print(f"  答え（規則）: {'ABC'[answer_by_rule(sh['rel_med'])]}")
    print(f"  変えない車: 抜かれた秒 {sh['ep_over']:.1f} / 抜いた秒 {sh['ep_pass']:.1f}  抜かれた台数 {sh['c_over']:.1f} / 抜いた台数 {sh['c_pass']:.1f}"
          f"  抜かれた秒のほうが長い回 {sh['share_over']:.3f}")
    for p, name in (("c", "照合: 2台とも変えない"), ("n", "ほかの車が車線を変えない"), ("f", "合図・合流の遅れなし"), ("e", "少しでも速ければ変える")):
        print(f"  [{name}] rel 中央値 {sh[p + '_rel_med']:+.4f}  差 {sh[p + '_diff_med']:+.1f}秒  車線変更 {sh[p + '_chg']:.2f}回"
              f"  抜かれた秒 {sh[p + '_ep_over']:.1f} / 抜いた秒 {sh[p + '_ep_pass']:.1f}  台数 {sh[p + '_c_over']:.1f} / {sh[p + '_c_pass']:.1f}")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで走る2台）を選ぶ
# =====================================================================
INTRO_X = 3.0                                     # 冒頭の早送り（実際の3秒＝動画の1秒）
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_SIM = int(math.ceil(T_GO * INTRO_X)) + 2    # 冒頭に見せる、スタート前の秒数
SEED_PICK = 20261022
PICK_N = 16


def pair_u(rec):
    """2台の、スタートからの進んだマス（スタート前は負）。rec は (秒, 3, N)"""
    v = rec[:, 2, :2].astype(float)
    u = np.zeros((len(rec) + 1, 2))
    for k in range(WARM, len(rec)):
        u[k + 1] = u[k] + v[k]
    for k in range(WARM - 1, -1, -1):
        u[k] = u[k + 1] - v[k]
    return u


def pick():
    """見本: 1万回とは別に引いた回から選ぶ。条件: 2台の差（÷変えない車の時間）が1万回の中央値から±0.6%以内、
    車線変更の回数が中央値±1、スタートで真横に並び、冒頭に見せる間は2台とも車線を変えず30m以内に並んでいる、
    途中で前後が2回以上入れ替わる（冒頭の間は2台の前後のずれが2マス＝15m以内）"""
    sh = shown()
    for k in range(200):
        seed = SEED_PICK + k
        r = simulate(seed, PICK_N, record=True)
        rec = r["rec"]
        for i in range(PICK_N):
            T = r["T"][i]
            rel = (T[1] - T[0]) / T[1]
            if abs(rel - sh["rel_med"]) > 0.006 or abs(r["n_chg"][i] - sh["chg_med"]) > 1:
                continue
            ri = rec[:, :, i, :]
            x, ln = ri[:, 0, :2].astype(int), ri[:, 1, :2]
            if x[WARM, 0] != x[WARM, 1]:
                continue
            pre = slice(WARM - INTRO_SIM, WARM + 1)
            if (ln[pre, 0] != ln[WARM, 0]).any() or (ln[pre, 1] != ln[WARM, 1]).any():
                continue
            dx = (x[pre, 0] - x[pre, 1] + R // 2) % R - R // 2
            if np.abs(dx).max() > 2:
                continue
            if ri[WARM - INTRO_SIM:WARM - INTRO_SIM + 3, 2, :2].max() == 0:
                continue                           # 0秒目に2台が止まっている絵は避ける
            u = pair_u(ri)
            kend = WARM + int(min(T)) + 1
            lead = np.sign(u[WARM + 1:kend, 0] - u[WARM + 1:kend, 1])
            lead = lead[lead != 0]
            if len(lead) < 2 or np.sum(lead[1:] != lead[:-1]) < 2:
                continue
            return seed, i
    raise SystemExit("見本の候補がない")


_SAMPLE = {}


def sample():
    if not _SAMPLE:
        cache = OUT / "sample.npz"
        if cache.exists() and cache.stat().st_mtime > (OUT / "data.npz").stat().st_mtime:
            z = np.load(cache)
            seed, i = int(z["seed"]), int(z["i"])
        else:
            seed, i = pick()
            np.savez(cache, seed=seed, i=i)
        r = simulate(seed, PICK_N, record=True)
        rec = r["rec"][:, :, i, :].astype(np.int64)
        _SAMPLE.update(seed=seed, i=i, rec=rec, T=r["T"][i].copy(), n_chg=int(r["n_chg"][i]),
                       u=pair_u(rec), x0=int(rec[WARM, 0, 0]))
        # 変える車の車線変更の時刻（スタートからの秒）
        ln = rec[:, 1, 0]
        _SAMPLE["chg_t"] = np.array([k - WARM for k in range(WARM + 1, len(rec)) if ln[k] != ln[k - 1]], float)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    T = s["T"]
    print("見本 seed", s["seed"], "i", s["i"], "時間 変える", round(T[0], 1), "変えない", round(T[1], 1),
          "差", round(T[1] - T[0], 1), "車線変更", s["n_chg"], "変更の時刻", s["chg_t"])
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, pct, stills, check_true  # noqa: E402

note.use()
note.DATE = "10.20"                               # 日付欄（公開予定日）

COL_H, INK_H = "#e8913a", "#b8601a"               # 変える車
COL_S, INK_S = "#5b8fd6", "#2f63a8"               # 変えない車
AMB_COLS = ["#c9bfa6", "#a9c2b6", "#d0b3a4", "#b5b8cf", "#d3c79a", "#bcc9cf"]   # ほかの車（くすんだ色）
ROAD = "#dedad0"
BRAKE = "#e0414b"
ZONE_COLS = [COL_H, COL_S, "#cdc8b8"]              # 変える車が早い / 変えない車が早い / ほぼ同じ
COL_OVER, COL_PASS = "#e46b6b", "#62b58f"           # 抜かれている / 抜いている

RACE_LEN = 10.0                                   # 遅いほうの車が着くまで（動画の秒）
BIG_Q = ["渋滞で 車線を変える車は、", "早く着く？"]
DETAIL = "隣が流れたら移る車 と 移らない車。5km"
LABELS = ["変える車が早い", "変えない車が早い", "ほぼ同じ"]
CORRECT = 2                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める

# ---------- 道の絵（1本道を4段に折りたたむ） ----------
XL, XR, RR = 200.0, 940.0, 95.0
ROW = 2 * RR
SL = XR - XL
AL = math.pi * RR
SEG = SL + AL
P_TOT = 4 * SL + 3 * AL                           # 道の絵の長さ（px）
ROAD_W = 66.0
LANE = 16.5                                       # 車線の中心のずれ
PPC_CLOSE = 52.0                                  # 冒頭: 1マス(7.5m)＝52px
PPC_MAP = P_TOT / R                               # 本編: 5km 全体が道の絵に入る
PAIR_PX = SL + AL + SL * 0.5                      # 冒頭: 2台を置く場所（2段目のまん中）
LAY_INTRO = (1.0, 790.0)                          # (縮める倍率, 1段目の y)
LAY_RACE = (0.78, 695.0)
CX_SCENE = 0.5 * (XL + XR) + 0.0


def setup():
    global RACE_X, TL, T_ENDB, T_RACE_END, T_G0, T_G1, T_BAR, T_REV, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    T_last = float(max(s["T"]))
    tau_go = 0.0
    RACE_X = (T_last - 0.3 * INTRO_X) / (RACE_LEN - 0.3)
    ts = np.arange(0, 80, 1 / 600)
    tau = np.zeros_like(ts)
    v = 0.0
    for k in range(len(ts)):
        t = ts[k]
        if t < T_GO:
            v = (t - T_GO) * INTRO_X
        else:
            sp = INTRO_X + (RACE_X - INTRO_X) * ease((t - T_GO) / 0.6)
            v += sp / 600
        tau[k] = v
    TL = dict(t=ts, tau=tau)
    T_ENDB = float(np.interp(T_last, tau, ts))
    T_RACE_END = T_ENDB + 2.4
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.6
    T_BAR = T_G1 + 0.9                            # 棒（5kmの時間）
    T_REV = T_BAR + 1.4                           # 答え
    T_TW = T_REV + 3.2                            # ひねり
    T_TW_RUN = T_TW + 3.2
    T_Q = T_TW_RUN + 6.2                          # 締め
    DURATION = T_Q + 4.6


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of_tau(x):
    return float(np.interp(x, TL["tau"], TL["t"]))


def path_pt(s):
    """道の絵の上の位置 s（px）→ (x, y, 向き)"""
    if s < 0:
        return XL + s, 0.0, 0.0
    if s >= P_TOT:
        return XL - (s - P_TOT), 3 * ROW, math.pi
    i = int(s // SEG)
    u = s - i * SEG
    if u < SL or i >= 3:
        x = XL + u if i % 2 == 0 else XR - u
        return x, i * ROW, (0.0 if i % 2 == 0 else math.pi)
    w = (u - SL) / RR
    if i % 2 == 0:
        return XR + RR * math.sin(w), i * ROW + RR - RR * math.cos(w), w
    return XL - RR * math.sin(w), i * ROW + RR - RR * math.cos(w), math.pi - w


def lane_pt(s, off):
    """off: +1 = 左の車線（車線0）、−1 = 右の車線（車線1）。間の値は車線変更の途中"""
    x, y, a = path_pt(s)
    return x + off * LANE * math.sin(a), y - off * LANE * math.cos(a), a


def zoom(t):
    """0 = 冒頭の寄り、1 = 5km 全体"""
    return ease(clamp01((t - T_MOVE) / (T_GO + 0.9 - T_MOVE)))


def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO + 0.9 - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def apply_layout(ctx, lay):
    sc, y0 = lay
    ctx.translate(CX_SCENE * (1 - sc), y0)
    ctx.scale(sc, sc)


def to_dev(lay, x, y):
    sc, y0 = lay
    return CX_SCENE + (x - CX_SCENE) * sc, y0 + y * sc


def _wobble_path(ctx, ss, off, seed, amp=0.9):
    rng = np.random.default_rng(seed)
    noise = np.convolve(rng.normal(0, amp, len(ss) + 8), np.ones(9) / 9, mode="same")[4:-4] * 3
    for j, s in enumerate(ss):
        x, y, a = path_pt(s)
        o = off + noise[j]
        (ctx.move_to if j == 0 else ctx.line_to)(x + o * math.sin(a), y - o * math.cos(a))


_ROAD_CACHE = {}


def road_surface(lay):
    key = (round(lay[0], 4), round(lay[1], 2))
    if key not in _ROAD_CACHE:
        if len(_ROAD_CACHE) > 4:
            _ROAD_CACHE.clear()
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        apply_layout(c, lay)
        ss = np.arange(-30.0, P_TOT + 30.0, 6.0)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        _wobble_path(c, ss, 0.0, 1, amp=0.0)
        c.set_source_rgba(*hexrgb(ROAD))
        c.set_line_width(ROAD_W)
        c.stroke()
        for off, sd in ((ROAD_W / 2, 2), (-ROAD_W / 2, 3)):
            _wobble_path(c, ss, off, sd)
            c.set_source_rgba(*hexrgb(INK, 0.9))
            c.set_line_width(3.0)
            c.stroke()
        _ROAD_CACHE[key] = s
    return _ROAD_CACHE[key]


# ---------- 車の状態（コマごと） ----------

def state(tau):
    """スタートからの秒 tau（小数）での、全車の位置（マス・小数）・車線（0〜1の小数）・速さ・ブレーキ"""
    s = sample()
    rec = s["rec"]
    k = WARM + int(math.floor(tau))
    k = max(1, min(k, len(rec) - 2))
    f = clamp01(tau - (k - WARM))
    x = rec[k, 0] + f * rec[k, 2]
    lane_now, lane_prev = rec[k, 1], rec[k - 1, 1]
    lat = lane_prev + (lane_now - lane_prev) * ease(clamp01(f * 1.6))
    v = rec[k, 2]
    brake = (v == 0) | (v < rec[k - 1, 2])
    u = s["u"][k] + f * (s["u"][k + 1] - s["u"][k])
    return x, lat, v, brake, u


def camera(t, tau, u_pair):
    """(道の絵の始まりにあたる位置 s0（マス）, 1マスの px)"""
    m = zoom(t)
    ppc = math.exp(math.log(PPC_CLOSE) + (math.log(PPC_MAP) - math.log(PPC_CLOSE)) * m)
    u_mid = 0.5 * (u_pair[0] + u_pair[1])
    p = PAIR_PX + (u_mid * PPC_MAP - PAIR_PX) * m if m < 1 else u_mid * PPC_MAP
    s0 = u_mid - p / ppc
    if m >= 1:
        s0 = 0.0
    return s0, ppc


def draw_car(ctx, xm, ym, ang, col, length, width, a=1.0, brake=False, outline=2.2):
    if a <= 0:
        return
    ctx.save()
    ctx.translate(xm, ym)
    ctx.rotate(ang)
    fill(ctx, hexrgb(col, a))
    core.rrect(ctx, -length / 2, -width / 2, length, width, min(6, length * 0.3))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(outline)
    ctx.stroke()
    if length > 24:                                # 窓
        fill(ctx, (1, 1, 1, 0.7 * a))
        core.rrect(ctx, length * 0.06, -width / 2 + 4, length * 0.2, width - 8, 3)
        ctx.fill()
        core.rrect(ctx, -length * 0.36, -width / 2 + 5, length * 0.12, width - 10, 2)
        ctx.fill()
    if brake:                                      # ブレーキランプ（後ろの両端）
        for sy in (-1, 1):
            if length > 24:
                ctx.set_source_rgba(*hexrgb(BRAKE, 0.35 * a))
                ctx.arc(-length / 2, sy * (width / 2 - 4), 8, 0, 2 * math.pi)
                ctx.fill()
            fill(ctx, hexrgb(BRAKE, a))
            r = 3.6 if length > 24 else 2.2
            ctx.arc(-length / 2 + 1, sy * (width / 2 - 3.5), r, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    s = sample()
    lay = layout(t)
    tau = tau_of(t)
    x, lat, v, brake, u_pair = state(tau)
    T = s["T"]
    u_show = np.minimum(u_pair, TRIP)              # 着いたらゴールで止めて描く
    s0, ppc = camera(t, tau, u_show)
    m = zoom(t)
    ctx.push_group()
    ctx.set_source_surface(road_surface(lay), 0, 0)
    ctx.paint()
    ctx.save()
    apply_layout(ctx, lay)
    # まん中の点線（カメラが進むと流れる）
    ss = np.arange(-30.0, P_TOT + 30.0, 8.0)
    _wobble_path(ctx, ss, 0.0, 4, amp=0.0)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.set_line_width(3.0)
    per = 26.0 * (1 - m) + 16.0 * m
    ctx.set_dash([per * 0.55, per * 0.45], (s0 * ppc) % per)
    ctx.stroke()
    ctx.set_dash([])
    # スタートとゴールの線
    for uline in (0.0, float(TRIP)):
        sp = (uline - s0) * ppc
        if -40 < sp < P_TOT + 40:
            xx, yy, ang = path_pt(min(max(sp, 0.0), P_TOT))
            nx, ny = math.sin(ang), -math.cos(ang)
            tx, ty = math.cos(ang), math.sin(ang)
            for j in range(8):
                for q in range(2):
                    o = -ROAD_W / 2 + (j + 0.5) * ROAD_W / 8
                    if (j + q) % 2 == 0:
                        ctx.set_source_rgba(*hexrgb(INK, 0.85))
                        ctx.rectangle(xx + nx * o + tx * (q * 8 - 4) - 4, yy + ny * o + ty * (q * 8 - 4) - 4, 8, 8)
                        ctx.fill()
    # ほかの車
    span = P_TOT / ppc
    c = s0 + span / 2
    xc = (s["x0"] + c) % R
    uu = c + ((x - xc + R / 2) % R - R / 2)
    length = max(0.78 * ppc, 4.5)
    width = 24.0 * (1 - m) + 12.0 * m
    for j in range(2, N):
        sp = (uu[j] - s0) * ppc
        if sp < -length or sp > P_TOT + length:
            continue
        fa = clamp01((sp + length / 2) / max(4.0, length)) * clamp01((P_TOT + length / 2 - sp) / max(4.0, length))
        off = 1 - 2 * lat[j]
        xm, ym, ang = lane_pt(sp - length / 2, off)
        col = AMB_COLS[j % len(AMB_COLS)]
        if m > 0.5 and brake[j]:                     # 全体図では、止まっている車を赤くする（渋滞の波が見える）
            col = "#e88a8a"
        draw_car(ctx, xm, ym, ang, col, length, width, a=fa, brake=bool(brake[j]),
                 outline=2.2 * (1 - m) + 1.0 * m)
    # くらべる2台（上に大きめに）
    kl = max(length, 30.0 + 14.0 * m)
    kw = max(width, 18.0 + 6.0 * m)
    for j, col in ((1, COL_S), (0, COL_H)):
        sp = (u_show[j] - s0) * ppc
        off = 1 - 2 * lat[j]
        xm, ym, ang = lane_pt(sp - kl / 2, off)
        if m > 0.3:                                # 全体図では白いふちで目立たせる
            ctx.save()
            ctx.translate(xm, ym)
            ctx.rotate(ang)
            fill(ctx, (1, 1, 1, 0.95))
            core.rrect(ctx, -kl / 2 - 4, -kw / 2 - 4, kl + 8, kw + 8, 8)
            ctx.fill()
            ctx.restore()
        draw_car(ctx, xm, ym, ang, col, kl, kw, brake=bool(brake[j]) and u_pair[j] < TRIP, outline=2.6)
    ctx.restore()
    # 字
    if t < T_GO + 0.3:                             # 冒頭: 2台の名札
        la = 1 - ease((t - T_MOVE + 0.2) / 0.3)
        for j, lab, ink in ((0, "変える車", INK_H), (1, "変えない車", INK_S)):
            sp = (u_show[j] - s0) * ppc
            off = 1 - 2 * lat[j]
            xm, ym, ang = lane_pt(sp - kl / 2, off * 3.4)
            dx, dy = to_dev(lay, xm, ym)
            text(ctx, lab, dx, dy, 32 * lay[0], ink, alpha=la)
    if m > 0.6:
        b = clamp01((m - 0.6) / 0.4)
        xs, ys = to_dev(lay, XL - 14, 0.0)
        text(ctx, "スタート", xs, ys, 28, INK, align="right", bold=False, alpha=b)
        xg, yg = to_dev(lay, XL - 14, 3 * ROW)
        text(ctx, "ゴール", xg, yg - 16, 28, INK, align="right", bold=False, alpha=b)
        text(ctx, "（5km）", xg, yg + 18, 24, PENCIL, align="right", bold=False, alpha=b)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def mmss(sec):
    sec = max(0, int(round(sec)))
    return f"{sec // 60}分{sec % 60:02d}秒"


def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = max(0.0, tau_of(t))
    T = s["T"]
    for j, cx, lab, ink, col in ((0, 330.0, "A 変える車", INK_H, COL_H), (1, 790.0, "B 変えない車", INK_S, COL_S)):
        lw = core.text_width(lab, 32)
        draw_car(ctx, cx - lw / 2 - 18, 1222, 0.0, col, 34, 18, a=a)
        text(ctx, lab, cx + 16, 1222, 32, ink, alpha=a)
        arrived = tau >= T[j]
        text(ctx, "到着" if arrived else "経過", cx, 1270, 28, RED if arrived else PENCIL, bold=arrived, alpha=a)
        text(ctx, mmss(min(tau, T[j])), cx, 1318, 50, ink if arrived else INK, alpha=a)
        if arrived:
            pa = clamp01((t - t_of_tau(T[j])) / 0.3)
            note.pen_circle(ctx, cx, 1318, 145, 40, RED, seed=70 + j, width=5, progress=pa, alpha=a)
        n = int(np.sum(s["chg_t"] <= min(tau, T[j]))) if j == 0 else 0
        text(ctx, f"車線変更 {n}回", cx, 1378, 34, INK, alpha=a)
    text(ctx, f"再生 {RACE_X:.0f}倍", 580, 1425, 24, PENCIL, bold=False, alpha=a)
    tl = float(max(T))
    if tau >= tl:
        b = a * ease_out((t - t_of_tau(tl)) / 0.3)
        d = T[1] - T[0]
        who = "変える車" if d > 0 else "変えない車"
        note.sticky(ctx, f"{who}が {mmss(abs(d))} 早い", 580, 920, 40, "yellow", fg=INK, a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    z = shown()["zone"]
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(c) for c in ZONE_COLS], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[z[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_BAR) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000回", 580, 612, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    cnt = np.bincount(sh["zone"][:m], minlength=3)
    labs = ["A 変える車が 3%以上早い", "B 変えない車が 3%以上早い", "C 差が3%未満（ほぼ同じ）"]
    for i, lab in enumerate(labs):
        y = 1190 + i * 58
        fill(ctx, hexrgb(ZONE_COLS[i], a))
        ctx.rectangle(222, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(222, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 272, y, 34, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt[i])}回", 915, y, 34, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。5kmにかかった時間の差で色分け", 580, 1380, 26, PENCIL, bold=False, alpha=a)


# ---------- 棒（同じものさし） ----------
BAR_X0, BAR_LEN = 250.0, 560.0


def draw_hbar(ctx, y, val, full, col, lab, txt, a, g=1.0):
    text(ctx, lab, BAR_X0, y - 46, 32, INK, align="left", alpha=a)
    w = BAR_LEN * val / full * g
    if w > 1:
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        core.rrect(ctx, BAR_X0, y - 20, w, 40, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.stroke()
    tw = core.text_width(txt, 36)
    vx = BAR_X0 + w + 14
    if vx + tw > 925:
        vx = BAR_X0 + w - tw - 12
    text(ctx, txt, vx, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def bars_alpha(t):
    if t < T_BAR:
        return 0.0
    return ease_out((t - T_BAR) / 0.3) * (1 - ease((t - T_TW) / 0.3))


def draw_bars(ctx, t):
    a = bars_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "5kmにかかった時間", 580, 640, 42, INK, alpha=a)
    text(ctx, "（1万回の真ん中の値）", 580, 692, 30, PENCIL, bold=False, alpha=a)
    g1 = ease_out((t - T_BAR - 0.15) / 0.4)
    g2 = ease_out((t - T_BAR - 0.55) / 0.5)
    full = 15 * 60.0
    draw_hbar(ctx, 810, sh["Th_med"], full, COL_H, "A 変える車", mmss(sh["Th_med"]), a, g1)
    draw_hbar(ctx, 945, sh["Ts_med"], full, COL_S, "B 変えない車", mmss(sh["Ts_med"]), a, g2)
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        d = sh["diff_med"]
        who = "変える車" if d > 0 else "変えない車"
        note.sticky(ctx, f"差は 約{abs(d):.0f}秒（{abs(sh['rel_med']) * 100:.1f}%）", 580, 1110, 40, "pink", fg=RED, a=b, tilt=-0.02)
        b2 = ease_out((t - T_REV - 1.0) / 0.3) * a
        text(ctx, f"{who}が 少しだけ早い（平均{sh['chg_mean']:.0f}回 車線変更して）", 580, 1235, 30, INK, bold=False, alpha=b2)
        text(ctx, "隣が流れると、ほかの車も移ってきて すぐ詰まる", 580, 1290, 30, INK, bold=False, alpha=b2)


# ---------- ひねり: 変えない車から見た隣の車線 ----------

def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "変えない車から見た、隣の車線", 580, 640, 40, INK, alpha=a)
    text(ctx, "（5kmを走るあいだ・1万回の平均）", 580, 692, 30, PENCIL, bold=False, alpha=a)
    g1 = ease_out((t - T_TW_RUN - 0.2) / 0.4)
    g2 = ease_out((t - T_TW_RUN - 0.7) / 0.5)
    full = 80.0
    draw_hbar(ctx, 810, sh["ep_over"], full, COL_OVER, "隣に 抜かれている時間", f"{sh['ep_over']:.0f}秒", a, g1)
    draw_hbar(ctx, 945, sh["ep_pass"], full, COL_PASS, "隣を 抜いている時間", f"{sh['ep_pass']:.0f}秒", a, g2)
    tb = T_TW_RUN + 1.6
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, "抜かれている時間のほうが長い", 580, 1105, 40, "pink", fg=RED, a=b, tilt=-0.02)
    if t >= tb + 1.0:
        b = ease_out((t - tb - 1.0) / 0.3) * a
        text(ctx, "どちらの車線も、平均の速さは同じなのに", 580, 1230, 30, INK, bold=False, alpha=b)
        text(ctx, "隣のほうが 速く見えてしまう", 580, 1285, 30, INK, bold=False, alpha=b)
        text(ctx, f"（抜かれている時間のほうが長かった回 {pct(sh['share_over'])}%）", 580, 1345, 26, PENCIL, bold=False, alpha=b)


# ---------- 冒頭・上のブロック ----------

def choice_row(labels, size, cx, max_w, gap=72):
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


CD_X, CD_Y = 790.0, 1205.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、渋滞の2車線を0秒目から車が流れる"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 60
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (408, 480)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 522, 575 + w2 / 2 + 6, 516, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 562, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 38, 575, 860, gap=40)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 626, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 626, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 626, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.94 * a2))
            core.rrect(ctx, cx - 140, cy - 165, 280, 240, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 165, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 108, 42, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 58, 56, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 88, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        sz = 44
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 850:
            sz *= 850 / w
        text(ctx, BIG_Q[0], 540, 400, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 452, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 483, 540 + w2 / 2 + 6, 480, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 534
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840, gap=40)):
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


INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "スタート", 760, 655, 36, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_bars(ctx, t)
    if T_TW <= t < T_TW_RUN:                       # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "でも、隣の車線って速く見えない？", 580, 860, a=ba, t_rel=t - T_TW, size=44)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\n変える派？ 変えない派？", 580, 860, 54, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.0) / 0.3)
        text(ctx, "コメントで教えてください", 580, 1090, 34, INK, bold=False, alpha=r)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def band_noise(dur, lo, hi, seed, rms):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / 60, 0, 1) * np.clip((hi - f) / 200, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    # 車の低いうなり（2台の速さに合わせて強くなる）
    tt = np.arange(int(SR * DURATION)) / SR
    hum = band_noise(DURATION, 60.0, 300.0, 3, 0.03)
    taus = np.interp(tt, TL["t"], TL["tau"])
    k = np.clip(WARM + np.floor(taus).astype(int), 0, len(s["rec"]) - 1)
    vv = s["rec"][k, 2, 0] + s["rec"][k, 2, 1]
    env = np.where(tt < T_G0, 0.35 + 0.25 * vv / VMAX, 0.0)
    env = np.convolve(env, np.ones(4800) / 4800, mode="same")
    mx.add(0, hum * env, 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    for tc in s["chg_t"]:                          # 変える車の車線変更（カチッ）
        if tc <= s["T"][0]:
            tv = t_of_tau(tc)
            mx.add(tv, tick(1800.0, 0.04), 0.35)
            mx.add(tv + 0.06, tick(1500.0, 0.04), 0.3)
    for j, f0 in ((0, 784.0), (1, 659.3)):
        mx.add(t_of_tau(s["T"][j]), bell(f0, 1.2), 0.45)
    beat(mx, T_GO + 0.4, T_ENDB, bpm=120, vol=0.3)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_BAR + 0.15, blip(587.3, 0.15), 0.35)
    mx.add(T_BAR + 0.55, blip(784.0, 0.15), 0.35)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    mx.add(T_TW_RUN + 0.2, blip(523.3, 0.15), 0.35)
    mx.add(T_TW_RUN + 0.7, blip(659.3, 0.15), 0.35)
    mx.add(T_TW_RUN + 1.6, thump(), 0.5)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    d = data()
    checks = []
    # (1) 作りの照合: 1車線・最高速度1・確率 p の Nagel–Schreckenberg は、流量に閉じた式がある
    #     J = (1 − √(1 − 4(1−p)ρ(1−ρ))) / 2（輪が長ければ）。平均の速さ = J/ρ
    for p in (0.2, 0.5):
        r = simulate(7, 200, hop=False, bg=False, vmax=1, p_slow=p, p_start=p, speeds=True)
        exact = (1 - math.sqrt(1 - 4 * (1 - p) * RHO * (1 - RHO))) / 2 / RHO
        checks.append((f"最高速度1・p={p} の平均の速さ（マス/秒）が閉じた式と一致", r["v_all"], exact, 0.01))
    # (2) 2台とも変えない（照合用 2,000回）: 差の中央値はほぼ0（2つの車線・2台の扱いが公平）
    checks.append(("2台とも変えない: 差の中央値（÷時間）", sh["c_rel_med"], 0.0, 0.004))
    checks.append(("2台とも変えない: 車線変更は0回", sh["c_chg"], 0.0, 0.0))
    # (3) 全員が着いた
    checks.append(("全員ゴールした", float(np.isfinite(d["m_T"]).sum()), 2.0 * N_TRIAL, 0.0))
    # (4) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["rel_med"])), float(INTRO.correct), 0.0))
    # (5) 見本の差が1万回の中央値の近く
    s = sample()
    checks.append(("見本の差（÷時間）が中央値の近く", float((s["T"][1] - s["T"][0]) / s["T"][1]), sh["rel_med"], 0.006))
    # (6) ひねり: 抜かれた秒 > 抜いた秒（画面の言い方と同じ向き）
    checks.append(check_true("ひねり: 抜かれている時間 > 抜いている時間", sh["ep_over"] > sh["ep_pass"],
                             f"{sh['ep_over']:.1f} / {sh['ep_pass']:.1f}"))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.1f}倍  遅いほうの到着 {T_ENDB:.2f}秒  見本 {sample()['T']}  車線変更 {sample()['n_chg']}")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.6, 1.0, 2.5, 5.0, 8.0, 8.6, 9.5, 11.0, 13.0, 15.0, 17.0, T_ENDB + 0.6, T_G0 + 1.5, T_G1 + 0.5,
              T_BAR + 1.0, T_REV + 1.5, T_TW + 1.0, T_TW_RUN + 1.0, T_TW_RUN + 3.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
