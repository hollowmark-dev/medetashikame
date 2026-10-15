"""車を飛ばしても、次の信号で追いつかれる？ 信号8つの道を、時速40kmの車と60kmの車で1万回ずつ走る。— 2026-10-13 作成（見本）

モデル（1本道・片側2車線。2台は別の車線を走り、同じ信号に従う。ほかの車はいない）
  道: スタート → 信号1 → … → 信号8 → ゴール。区間の長さ（9区間）はそれぞれ 200〜600m の一様乱数（合計 平均3.6km）。
  信号: 青（黄を含む）がサイクルの50%、そのうち最後の3秒が黄、残りが赤。
        つながっていない道（本編）: 信号ごとにサイクル 60〜120秒の一様乱数、青の始まり（オフセット）もでたらめ。
        つながった道（ひねり）: 8つとも同じサイクル（1回ごとに 60〜120秒）。青の始まりを「時速40kmで走ると
        ちょうど青が始まる」ように、距離÷時速40km ずつずらす（系統制御）。
  車: 時速40km（ふつう）と60km（速め。制限60kmの道なので、2台とも制限速度の内）。2台とも同じ時刻に、スタートで止まった状態から出る。出る時刻はでたらめ。
      加速は IDM（Treiber ら 2000）の自由走行の式 a = 1.5×(1−(v/v0)^4) m/s²。
      赤・黄の信号の手前では、ふつうのブレーキ 2.0 m/s² で止まりきれる所まで来たらブレーキを踏み、停止線の1.5m手前で止まる。
      黄に変わったとき、止まるのに 3.0 m/s² より強いブレーキが要るなら、止まらずに通る（ジレンマの決め方）。
      加速・ブレーキの強さは2台とも同じ（ちがうのは出す速さだけ）。
      加速 1.5・ブレーキ 2.0 は、信号交差点での乗用車の実測（平均の加速 1.44〜1.53 m/s²、減速 1.78 m/s²、
      最大の減速 3.09 m/s²。Ramireddy ら 2021）に合わせた。
  1回ぶん: 道の長さ・信号のサイクルとずれ・出る時刻を引き直して、2台を走らせる。1万回。

問い: 「車を飛ばしても、次の信号で追いつかれる？」（2行）
      A ほぼ同じ ／ B 少し早い ／ C 速さの分だけ早い
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1回ごとに「60kmの車が早く着いた時間 ÷ 信号がなかったら早く着くはずの時間（道のり÷40km − 道のり÷60km）」を出し、
      1万回の真ん中の値（中央値）が 1/3 未満なら A、2/3 未満なら B、それ以上なら C。
ひねり: 「信号がつながっていたら？」 時速40kmに合わせた系統制御の道で同じことをする。
締め: 「じゃあ、なんで『追いつかれる』気がするの？」→ 答え「見えない所で取り返している」（追いつかれた回数と、相手だけ赤で止まった回数）。
      概要欄用に、つながった道で速さを30〜70kmに変えた計算もする。
2026-10-13 v2: スピード違反をすすめる見え方を避ける（管理役経由のユーザー依頼）。前提を「制限60kmの道」にし、画面から「飛ばす」を外した

乱数の種は見本（並んで走る2台）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
照合（check_answers）は run_checks を参照。
"""
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "shingou-tobasu"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_SIG = 8                                         # 信号の数
GAP = (200.0, 600.0)                              # 区間の長さ（m）
CYC = (60.0, 120.0)                               # サイクル（秒）
GREEN = 0.5                                       # 青（黄を含む）の割合
YELLOW = 3.0                                      # 黄（秒）
V_A = 40 / 3.6                                    # ふつう（m/s）
V_B = 60 / 3.6                                    # 速め（制限60kmいっぱい）
ACC = 1.5                                         # 加速の強さ（m/s²）
BRAKE = 2.0                                       # ふつうのブレーキ（m/s²）
B_CRIT = 3.0                                      # これより強いブレーキが要るなら、黄でも止まらずに通る
S0 = 1.5                                          # 停止線の手前で止まる距離（m）
DT = 0.1                                          # 時間の刻み（秒）
N_TRIP = 10000
T_DEP = 1200.0                                    # 出る時刻は 0〜1200秒 のでたらめ
CATCH_S = 3.0                                     # 「追いつかれた」＝40kmの車が、60kmの車から3秒以内に同じ信号を通った

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_LO, RULE_HI = 1 / 3, 2 / 3


def answer_by_rule(f_median):
    """f_median = 1万回の「早く着いた時間 ÷ 信号がなければ早く着くはずの時間」の中央値"""
    if f_median < RULE_LO:
        return 0                                  # A ほぼ同じ（追いつかれる）
    if f_median < RULE_HI:
        return 1                                  # B 少し早い
    return 2                                      # C 速さの分だけ早い


# ---------- 道と信号を作る ----------

def make_roads(n, rng, coordinated=False):
    """n 回ぶんの道。sig: 停止線の位置 (n, 8)、L: ゴールまで、cyc/off: 信号のサイクルと青の始まり (n, 8)、t0: 出る時刻"""
    gaps = rng.uniform(*GAP, (n, N_SIG + 1))
    pos = np.cumsum(gaps, 1)
    sig, L = pos[:, :N_SIG], pos[:, N_SIG]
    if coordinated:
        c = rng.uniform(*CYC, n)
        cyc = np.repeat(c[:, None], N_SIG, 1)
        off = sig / V_A                            # 時速40kmで走ると、ちょうど青が始まる
    else:
        cyc = rng.uniform(*CYC, (n, N_SIG))
        off = rng.uniform(0, 1, (n, N_SIG)) * cyc
    t0 = rng.uniform(0, T_DEP, n)
    return dict(sig=sig, L=L, cyc=cyc, off=off, t0=t0)


def light_state(road, k, t_abs, rows=None):
    """信号 k の色（0=青, 1=黄, 2=赤）。t_abs は時刻（出る時刻を足したもの）"""
    rows = np.arange(len(t_abs)) if rows is None else rows
    c = road["cyc"][rows, k]
    ph = np.mod(t_abs - road["off"][rows, k], c)
    g = GREEN * c
    return np.where(ph < g - YELLOW, 0, np.where(ph < g, 1, 2))


def drive(road, v0, acc=ACC, brake=BRAKE, b_crit=B_CRIT, dt=DT, record=False, t_max=2400.0):
    """road の各回を、最高速度 v0（m/s。配列か数）の車で走る。返り値: 着いた時間・止まった回数・信号を通った時刻"""
    n = len(road["L"])
    v0 = np.broadcast_to(np.asarray(v0, float), (n,)).copy()
    sig = np.concatenate([road["sig"], np.full((n, 1), np.inf)], 1)
    x = np.zeros(n)
    v = np.zeros(n)
    k = np.zeros(n, int)
    commit = np.zeros(n, bool)
    done = np.zeros(n, bool)
    T = np.full(n, np.nan)
    stops = np.zeros(n, int)
    stops_at = np.zeros((n, N_SIG), bool)
    stopped = np.ones(n, bool)
    cross = np.full((n, N_SIG), np.nan)
    rows = np.arange(n)
    hist = [] if record else None
    t = 0.0
    while t < t_max and not done.all():
        kk = np.minimum(k, N_SIG - 1)
        has = k < N_SIG
        st = light_state(road, kk, road["t0"] + t)
        d_eff = sig[rows, k] - S0 - x
        obst = has & (st > 0) & ~commit
        need = v * v / (2 * np.maximum(d_eff, 0.01))
        newc = obst & (st == 1) & (need > b_crit) & (d_eff > 0)
        commit |= newc
        obst &= ~newc
        # 赤のまま止まりきれない所まで来ていたら（赤に変わる前に黄で決めたはず）、止まる
        a_free = acc * (1 - (v / v0) ** 4)
        a = np.where(obst & (need >= brake), -need, a_free)
        hold = obst & (d_eff <= 0.05)
        a = np.where(hold, 0.0, a)
        vn = np.maximum(0.0, v + a * dt)
        xn = x + (v + vn) / 2 * dt
        clip = obst & (xn > sig[rows, k] - S0)
        xn = np.where(clip, sig[rows, k] - S0, xn)
        vn = np.where(clip | hold, 0.0, vn)
        vn = np.where(done, 0.0, vn)
        xn = np.where(done, x, xn)
        # 信号を通った
        passed = has & (xn > sig[rows, k])
        if passed.any():
            r = rows[passed]
            frac = (sig[r, k[r]] - x[r]) / np.maximum(xn[r] - x[r], 1e-9)
            cross[r, k[r]] = t + frac * dt
            k[passed] += 1
            commit[passed] = False
        # 止まった回数（スタートの停止は数えない）
        now_stop = (vn < 0.3) & ~done
        new_stop = now_stop & ~stopped & (t > 1.0)
        if new_stop.any():
            stops += new_stop
            ks = np.minimum(k, N_SIG - 1)
            stops_at[rows[new_stop], ks[new_stop]] = True
        stopped = now_stop | (stopped & (vn < 1.0))
        # ゴール
        arr = ~done & (xn >= road["L"])
        if arr.any():
            frac = (road["L"][arr] - x[arr]) / np.maximum(xn[arr] - x[arr], 1e-9)
            T[arr] = t + frac * dt
            done |= arr
            xn = np.where(arr, road["L"], xn)
        x, v = xn, vn
        t += dt
        if record:
            hist.append(np.stack([x, v]))
    out = dict(T=T, stops=stops, stops_at=stops_at, cross=cross)
    if record:
        out["hist"] = np.array(hist)              # (刻み, 2, n)
    return out


def subset(road, idx):
    return {k: v[idx] for k, v in road.items()}


def race(road, record=False, dt=DT):
    """同じ道を 40km と 60km で走る（2台ぶんを1度に計算する）"""
    n = len(road["L"])
    both = {k: np.concatenate([v, v]) for k, v in road.items()}
    r = drive(both, np.concatenate([np.full(n, V_A), np.full(n, V_B)]), record=record, dt=dt)
    A = {k: (v[:n] if k != "hist" else v[:, :, :n]) for k, v in r.items()}
    B = {k: (v[n:] if k != "hist" else v[:, :, n:]) for k, v in r.items()}
    naive = road["L"] / V_A - road["L"] / V_B
    saved = A["T"] - B["T"]
    catch = ((A["cross"] - B["cross"]) < CATCH_S).any(1)
    return dict(A=A, B=B, naive=naive, saved=saved, f=saved / naive, catch=catch)


# ---------- 計算 ----------
SEED_MAIN, SEED_WAVE, SEED_SWEEP = 20261015, 20261016, 20261017
SWEEP_KMH = np.arange(30, 75, 5)


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    road = make_roads(N_TRIP, np.random.default_rng(SEED_MAIN))
    m = race(road)
    wroad = make_roads(N_TRIP, np.random.default_rng(SEED_WAVE), coordinated=True)
    w = race(wroad)
    # 締めの問い: つながった道で、出す速さを変える（道は同じものを使う）
    sw = make_roads(N_TRIP, np.random.default_rng(SEED_SWEEP), coordinated=True)
    sweep = []
    for kmh in SWEEP_KMH:
        r = drive(sw, kmh / 3.6)
        sweep.append(r["T"])
    np.savez_compressed(OUT / "data.npz",
                        **{f"m_{k}": v for k, v in road.items()}, **{f"w_{k}": v for k, v in wroad.items()},
                        mA_T=m["A"]["T"], mB_T=m["B"]["T"], mA_st=m["A"]["stops"], mB_st=m["B"]["stops"],
                        m_catch=m["catch"], m_naive=m["naive"],
                        mA_cross=m["A"]["cross"], mB_cross=m["B"]["cross"], mA_sa=m["A"]["stops_at"], mB_sa=m["B"]["stops_at"],
                        wA_T=w["A"]["T"], wB_T=w["B"]["T"], wA_st=w["A"]["stops"], wB_st=w["B"]["stops"],
                        w_catch=w["catch"], w_naive=w["naive"],
                        wA_sa=w["A"]["stops_at"], wB_sa=w["B"]["stops_at"], sweep=np.array(sweep), sweep_kmh=SWEEP_KMH)
    print(f"計算 {time.time() - t0:.0f}秒")


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


def road_of(prefix, idx=None):
    d = data()
    r = {k: d[f"{prefix}_{k}"] for k in ("sig", "L", "cyc", "off", "t0")}
    return r if idx is None else subset(r, np.atleast_1d(idx))


def shown():
    d = data()
    out = {}
    for p in ("m", "w"):
        saved = d[f"{p}A_T"] - d[f"{p}B_T"]
        naive = d[f"{p}_naive"]
        f = saved / naive
        out[p] = dict(
            f_med=float(np.median(f)), saved_med=float(np.median(saved)), naive_med=float(np.median(naive)),
            saved_mean=float(np.mean(saved)), naive_mean=float(np.mean(naive)),
            zone=np.array([np.mean(f < RULE_LO), np.mean((f >= RULE_LO) & (f < RULE_HI)), np.mean(f >= RULE_HI)]),
            later=float(np.mean(saved < 0)), catch=float(np.mean(d[f"{p}_catch"])),
            stA=float(np.mean(d[f"{p}A_st"])), stB=float(np.mean(d[f"{p}B_st"])),
            TA_med=float(np.median(d[f"{p}A_T"])), TB_med=float(np.median(d[f"{p}B_T"])),
            f=f, saved=saved)
    # 追いつかれた回数と、その逆（60kmが青で通った信号で、40kmが赤で止まった回数）。1回あたりの平均
    out["m"]["n_catch"] = float(((d["mA_cross"] - d["mB_cross"]) < CATCH_S).sum(1).mean())
    out["m"]["n_pull"] = float((d["mA_sa"] & ~d["mB_sa"]).sum(1).mean())
    out["m"]["any_pull"] = float((d["mA_sa"] & ~d["mB_sa"]).any(1).mean())
    T = d["sweep"]
    out["sweep_med"] = np.median(T, 1)
    out["sweep_mean"] = T.mean(1)
    out["best_kmh"] = int(d["sweep_kmh"][int(np.argmin(out["sweep_med"]))])
    return out


def report():
    sh = shown()
    for p, name in (("m", "つながっていない道"), ("w", "つながった道（40km用）")):
        s = sh[p]
        print(f"[{name}] 中央値 f={s['f_med']:.3f}  早く着いた時間 中央値 {s['saved_med']:.1f}秒（平均 {s['saved_mean']:.1f}）"
              f"  信号なしの計算 中央値 {s['naive_med']:.1f}秒（平均 {s['naive_mean']:.1f}）")
        print(f"   区分 A/B/C = {s['zone'][0]:.3f}/{s['zone'][1]:.3f}/{s['zone'][2]:.3f}  60kmが遅く着いた {s['later']:.3f}"
              f"  追いつかれた {s['catch']:.3f}  赤で止まった平均 40km {s['stA']:.2f}回 / 60km {s['stB']:.2f}回"
              f"  所要 中央値 40km {s['TA_med']:.0f}秒 / 60km {s['TB_med']:.0f}秒")
        print(f"   答え（規則）: {'ABC'[answer_by_rule(s['f_med'])]}")
    print("速さ別（つながった道）中央値:", {int(k): round(float(v), 1) for k, v in zip(data()["sweep_kmh"], sh["sweep_med"])},
          "いちばん早い", sh["best_kmh"], "km/h")


if __name__ == "__main__" and "--compute" in sys.argv:
    compute()
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで走る2台）を選ぶ
# =====================================================================
# 道の絵: 1本道を4段に折りたたんで紙に置く（すごろくの道）。下の座標は「道の絵」の座標（px）
XL, XR, RR = 215.0, 905.0, 95.0                   # 段の左端・右端、折り返しの半径
ROW = 2 * RR                                      # 段の間隔
SL = XR - XL                                      # 1段のまっすぐな長さ
AL = math.pi * RR                                 # 折り返しの長さ
SEG = SL + AL
P_TOT = 4 * SL + 3 * AL                           # スタートからゴールまで（px）
ROAD_W = 76.0                                     # 道の幅
LANE = 19.0                                       # 車線の中心のずれ
CAR_K = 1.3                                       # くらべる2台は、ほかの車より大きく描く
CAR_L, CAR_W = 48.0, 25.0                         # 車の絵の大きさ


def on_straight(s, margin=55.0):
    i = int(s // SEG)
    u = s - i * SEG
    return i < 4 and margin <= u <= SL - margin


SEED_PICK = 20261018


def pick_main():
    """見本: 1万回とは別に、同じ作り方で道を引き直して選ぶ（信号が絵のまっすぐな所に来る道は少ないので）。
    条件: 途中（信号3〜6）で1度は追いつかれる（60kmが赤で待つ横に40kmが来る）、40kmが赤で止まった信号を
    60kmが青で通る場面もある、着いた差（÷信号なしの計算）が1万回の中央値に近い"""
    med = shown()["m"]["f_med"]
    pool = make_roads(300000, np.random.default_rng(SEED_PICK))
    s_px = pool["sig"] * (P_TOT / pool["L"])[:, None]
    i = s_px // SEG
    u = s_px - i * SEG
    ok = np.nonzero(((i < 4) & (u >= 55) & (u <= SL - 55)).all(1))[0]
    cand = subset(pool, ok)
    r = race(cand)
    catch_mid = (((r["A"]["cross"] - r["B"]["cross"]) < CATCH_S) & r["B"]["stops_at"])[:, 2:6].any(1)
    pull = (r["A"]["stops_at"] & ~r["B"]["stops_at"]).any(1)
    n_catch = ((r["A"]["cross"] - r["B"]["cross"]) < CATCH_S).sum(1)
    good = np.nonzero(catch_mid & pull & (n_catch >= 2) & (n_catch <= 3) & (np.abs(r["f"] - med) < 0.05)
                      & (r["A"]["T"] < 480) & (r["B"]["stops"] >= 2))[0]
    if not len(good):
        raise SystemExit("見本の候補がない")
    best = good[np.argmin(np.abs(r["naive"][good] - shown()["m"]["naive_med"]))]   # 道の長さも真ん中くらい
    return subset(cand, np.array([best])), len(ok)


def pick_wave(base):
    """ひねりの見本: 見本と同じ道（信号の場所）で、信号をつなげる。サイクルと出る時刻は、
    40kmが一度も止まらず、60kmの早く着いた時間が1万回の真ん中くらいになるものを選ぶ"""
    med = shown()["w"]["saved_med"]
    best = None
    for c in (80.0, 90.0, 100.0):
        for t0 in np.arange(0, c, 2.0):
            r = dict(sig=base["sig"], L=base["L"], cyc=np.full((1, N_SIG), c), off=base["sig"] / V_A,
                     t0=np.array([t0]))
            res = race(r)
            if res["A"]["stops"][0] != 0 or res["B"]["stops"][0] < 4:
                continue
            score = abs(res["saved"][0] - med)
            if best is None or score < best[0]:
                best = (score, c, float(t0))
    if best is None:
        raise SystemExit("ひねりの見本の候補がない")
    _, c, t0 = best
    return dict(sig=base["sig"], L=base["L"], cyc=np.full((1, N_SIG), c), off=base["sig"] / V_A, t0=np.array([t0]))


_SAMPLE = {}


def sample():
    if not _SAMPLE:
        cache = OUT / "sample.npz"                # 選ぶのに30秒ほどかかるので、選んだ道を残す（data.npz より新しいときだけ使う）
        if cache.exists() and cache.stat().st_mtime > (OUT / "data.npz").stat().st_mtime:
            z = np.load(cache)
            road = {k: z["m_" + k] for k in ("sig", "L", "cyc", "off", "t0")}
            wroad = {k: z["w_" + k] for k in ("sig", "L", "cyc", "off", "t0")}
            n_ok = int(z["n_ok"])
        else:
            road, n_ok = pick_main()
            wroad = pick_wave(road)
            np.savez(cache, n_ok=n_ok, **{"m_" + k: v for k, v in road.items()}, **{"w_" + k: v for k, v in wroad.items()})
        i = 0
        for key, rd in (("m", road), ("w", wroad)):
            res = race(rd, record=True)
            _SAMPLE[key] = dict(road=rd, res=res, ppm=P_TOT / float(rd["L"][0]),
                                A=car_track(res["A"]), B=car_track(res["B"]))
        _SAMPLE["i"] = i
        _SAMPLE["n_ok"] = n_ok
        sm = _SAMPLE["m"]
        # 追いつかれた場面: 60kmが止まって待っている信号に、40kmが来た
        cr = sm["res"]["A"]["cross"][0] - sm["res"]["B"]["cross"][0]
        ks = [k for k in range(N_SIG) if cr[k] < CATCH_S and sm["res"]["B"]["stops_at"][0, k] and k >= 1]
        ev = []
        for k in ks:
            xa = sm["A"]["x"]
            j = int(np.argmax(xa >= sm["road"]["sig"][0, k] - S0 - 40.0))
            ev.append((k, j * DT))
        sm["catch"] = ev
    return _SAMPLE


def car_track(r):
    """記録した位置と速さから、止まった時刻の一覧も作る（drive と同じ数え方）"""
    h = r["hist"][:, :, 0]
    x, v = h[:, 0], h[:, 1]
    T = float(r["T"][0])
    t_stop = []
    stopped = True
    for j in range(len(v)):
        if j * DT >= T:                            # ゴールのあとは数えない
            break
        now = v[j] < 0.3
        if now and not stopped and j * DT > 1.0:
            t_stop.append((j + 1) * DT)
        stopped = now or (stopped and v[j] < 1.0)
    if len(t_stop) != int(r["stops"][0]):
        raise SystemExit(f"止まった回数が合わない: 絵 {len(t_stop)} / 計算 {int(r['stops'][0])}")
    return dict(x=x, v=v, T=T, stops=int(r["stops"][0]), t_stop=np.array(t_stop))


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    print("見本", s["i"], "（絵に収まる回", s["n_ok"], "）")
    for key in ("m", "w"):
        sm = s[key]
        print(key, "40km", round(sm["A"]["T"], 1), "秒", sm["A"]["stops"], "回 / 60km", round(sm["B"]["T"], 1), "秒",
              sm["B"]["stops"], "回  差", round(sm["A"]["T"] - sm["B"]["T"], 1), "cyc", sm["road"]["cyc"][0, 0].round(1),
              "t0", sm["road"]["t0"][0].round(1))
    print("追いつかれた", s["m"]["catch"])
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, pct, stills  # noqa: E402

note.use()
note.DATE = "10.15"                               # 日付欄

COL_A, INK_A = "#5b8fd6", "#2f63a8"               # ふつう（40km）
COL_B, INK_B = "#e4573d", "#b8331d"               # 速め（60km）
AMB_COLS = ["#bba57c", "#8fae9f", "#c79e86", "#a2a6c0", "#c8b66e"]   # ほかの車（2台とは違う、くすんだ色）
ROAD = "#dedad0"
LAMP = {0: "#1fa77a", 1: "#f0b12a", 2: "#e0414b"}   # 青・黄・赤
LAMP_OFF = "#c9c6bd"
ZONE_COLS = ["#9fb0c8", "#f2c94c", COL_B]          # A ほぼ同じ / B 少し早い / C 速さの分だけ早い

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_X = 36.0                                    # 冒頭の早送り（実際の36秒＝動画の1秒）
RACE_LEN = 10.0                                   # 40kmの車が着くまで（動画の秒）
WAVE_LEN = 5.6
BIG_Q = ["車を飛ばしても、", "次の信号で追いつかれる？"]
DETAIL = "制限60kmの道を、40kmと60kmで。信号8つ・1万回"
LABELS = ["ほぼ同じ", "少し早い", "速さの分だけ早い"]
CORRECT = 2                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める

# 冒頭と本編での道の絵の置き場所: (縮める倍率, 1段目の y)
LAY_INTRO = (1.0, 790.0)
LAY_SIM = (0.8, 650.0)
CX_SCENE = 0.5 * (XL + XR)


def setup():
    global RACE_X, WAVE_X, T_RACE_END, T_G0, T_G1, T_BAR, T_REV, T_TW, T_TW_RUN, T_TW_END, T_WB, T_Q, DURATION
    s = sample()
    RACE_X = s["m"]["A"]["T"] / RACE_LEN
    WAVE_X = s["w"]["A"]["T"] / WAVE_LEN
    T_RACE_END = T_GO + RACE_LEN + 2.6
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.6
    T_BAR = T_G1 + 1.0                            # 棒（早く着いた時間）
    T_REV = T_BAR + 1.4                           # 答え
    T_TW = T_REV + 2.4                            # ひねり
    T_TW_RUN = T_TW + 2.7
    T_TW_END = T_TW_RUN + WAVE_LEN + 1.0
    T_WB = T_TW_END                               # ひねりの棒
    T_Q = T_WB + 3.2                              # 締め
    DURATION = T_Q + 4.0


# ---------- 道の絵 ----------

def path_pt(s):
    """道の上の位置 s（px）→ 道の絵の座標 (x, y, 向き)。s<0 はスタートの手前、s>P_TOT はゴールの先"""
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


def lane_pt(s, lane):
    """lane = +1（左の車線＝ふつうの車）/ −1（右の車線＝速めの車）"""
    x, y, a = path_pt(s)
    return x + lane * LANE * math.sin(a), y - lane * LANE * math.cos(a), a


def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_SIM[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_SIM[1] - LAY_INTRO[1]) * m)


def apply_layout(ctx, lay):
    sc, y0 = lay
    ctx.translate(CX_SCENE * (1 - sc), y0)
    ctx.scale(sc, sc)


def to_dev(lay, x, y):
    sc, y0 = lay
    return CX_SCENE + (x - CX_SCENE) * sc, y0 + y * sc


_ROAD_CACHE = {}


def _wobble_path(ctx, ss, off, seed, amp=0.9):
    rng = np.random.default_rng(seed)
    noise = np.convolve(rng.normal(0, amp, len(ss) + 8), np.ones(9) / 9, mode="same")[4:-4] * 3
    for j, s in enumerate(ss):
        x, y, a = path_pt(s)
        o = off + noise[j]
        px, py = x + o * math.sin(a), y - o * math.cos(a)
        (ctx.move_to if j == 0 else ctx.line_to)(px, py)


def draw_road_static(ctx):
    """道（灰色の地・ペンの縁・まん中の点線）・スタートとゴールの線。字は書かない（公開前チェックのため別に描く）"""
    ss = np.arange(-70.0, P_TOT + 50.0, 6.0)
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    _wobble_path(ctx, ss, 0.0, 1, amp=0.0)
    ctx.set_source_rgba(*hexrgb(ROAD))
    ctx.set_line_width(ROAD_W)
    ctx.stroke()
    for off, sd in ((ROAD_W / 2, 2), (-ROAD_W / 2, 3)):
        _wobble_path(ctx, ss, off, sd)
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(3.0)
        ctx.stroke()
    _wobble_path(ctx, ss, 0.0, 4, amp=0.3)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.set_line_width(3.0)
    ctx.set_dash([14, 12])
    ctx.stroke()
    ctx.set_dash([])
    # スタートとゴール（市松の線）
    for s in (0.0, P_TOT):
        x, y, a = path_pt(s)
        nx, ny = math.sin(a), -math.cos(a)
        tx, ty = math.cos(a), math.sin(a)
        for j in range(8):
            for q in range(2):
                o = -ROAD_W / 2 + (j + 0.5) * ROAD_W / 8
                cx_ = x + nx * o + tx * (q * 8 - 4)
                cy_ = y + ny * o + ty * (q * 8 - 4)
                if (j + q) % 2 == 0:
                    ctx.set_source_rgba(*hexrgb(INK, 0.85))
                    ctx.rectangle(cx_ - 4, cy_ - 4, 8, 8)
                    ctx.fill()


def road_surface(lay):
    key = (round(lay[0], 4), round(lay[1], 2))
    if key not in _ROAD_CACHE:
        if len(_ROAD_CACHE) > 4:
            _ROAD_CACHE.clear()
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        apply_layout(c, lay)
        draw_road_static(c)
        _ROAD_CACHE[key] = s
    return _ROAD_CACHE[key]


def sig_px(sm):
    return sm["road"]["sig"][0] * sm["ppm"]


def light_states(sm, t_abs):
    r = sm["road"]
    out = []
    for k in range(N_SIG):
        c = r["cyc"][0, k]
        ph = (t_abs - r["off"][0, k]) % c
        g = GREEN * c
        out.append(0 if ph < g - YELLOW else (1 if ph < g else 2))
    return out


def draw_signals(ctx, sm, t_abs, a=1.0):
    st = light_states(sm, t_abs)
    for k, s in enumerate(sig_px(sm)):
        x, y, ang = path_pt(s)
        col = LAMP[st[k]]
        # 停止線（信号の色）
        nx, ny = math.sin(ang), -math.cos(ang)
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        ctx.set_line_width(6.0)
        ctx.move_to(x + nx * ROAD_W / 2, y + ny * ROAD_W / 2)
        ctx.line_to(x - nx * ROAD_W / 2, y - ny * ROAD_W / 2)
        ctx.stroke()
        # 信号機（横に3つ: 青・黄・赤）。道の上側に置く
        hx, hy = x, y - ROAD_W / 2 - 34
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(3)
        ctx.move_to(hx, hy + 14)
        ctx.line_to(hx, y - ROAD_W / 2 - 2)
        ctx.stroke()
        fill(ctx, hexrgb("#4a4f5c", a))
        core.rrect(ctx, hx - 44, hy - 16, 88, 32, 10)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(2.5)
        ctx.stroke()
        for j in range(3):
            lx = hx - 27 + 27 * j
            on = st[k] == j
            if on:
                ctx.set_source_rgba(*hexrgb(LAMP[j], 0.35 * a))
                ctx.arc(lx, hy, 17, 0, 2 * math.pi)
                ctx.fill()
            fill(ctx, hexrgb(LAMP[j] if on else LAMP_OFF, a))
            ctx.arc(lx, hy, 10.5, 0, 2 * math.pi)
            ctx.fill()


def draw_car(ctx, s, lane, col, a=1.0, at=None, k=1.0):
    """上から見た車（前の端が s）。lane は車線。at=(x, y, 向き) を渡すとその場所に描く。k は大きさ"""
    if a <= 0:
        return
    xm, ym, ang = at if at is not None else lane_pt(s - CAR_L * k / 2, lane)
    ctx.save()
    ctx.translate(xm, ym)
    ctx.rotate(ang)
    ctx.scale(k, k)
    fill(ctx, hexrgb("#3b3f4a", a))
    for wx in (-CAR_L * 0.3, CAR_L * 0.3):
        for wy in (-CAR_W / 2 - 1.5, CAR_W / 2 - 3.5):
            ctx.rectangle(wx - 5, wy, 10, 5)
    ctx.fill()
    fill(ctx, hexrgb(col, a))
    core.rrect(ctx, -CAR_L / 2, -CAR_W / 2, CAR_L, CAR_W, 7)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(2.4)
    ctx.stroke()
    fill(ctx, (1, 1, 1, 0.75 * a))                # 前と後ろの窓
    core.rrect(ctx, CAR_L * 0.08, -CAR_W / 2 + 4, CAR_L * 0.2, CAR_W - 8, 3)
    ctx.fill()
    core.rrect(ctx, -CAR_L * 0.36, -CAR_W / 2 + 5, CAR_L * 0.12, CAR_W - 10, 2)
    ctx.fill()
    ctx.restore()


# ---------- 冒頭のほかの車（IDM で信号に従って流れる） ----------
_AMB = None


def ambient():
    """冒頭（0〜T_GO秒）に流れるほかの車。見本と同じ道・同じ信号で、2車線に車を流す（IDM: Treiber ら 2000）。
    答えが見えないよう、ほかの車の速さは時速38〜50kmのばらばら。返り値: 動画のコマごとの [(位置 m, 車線, 色の番号)]"""
    global _AMB
    if _AMB is not None:
        return _AMB
    sm = sample()["m"]
    rd = sm["road"]
    L = float(rd["L"][0])
    sig = list(rd["sig"][0]) + [np.inf]
    carl = (CAR_L * 1.12 + 8) / sm["ppm"]                # 絵の車の長さ（m に直す）。絵が重ならないように
    rng = np.random.default_rng(5)
    t_end = float(rd["t0"][0])
    frames = [t_end + (j / FPS - T_GO) * INTRO_X for j in range(int(T_GO * FPS) + 2)]
    t = frames[0] - 400.0
    cars = []
    next_sp = [t, t + 4.0]
    rec = []
    fi = 0
    while fi < len(frames):
        st_all = light_states(sm, t)
        for ln in (0, 1):
            if t >= next_sp[ln] and all(not (c["lane"] == ln and c["x"] < carl + 25) for c in cars):
                v0 = rng.uniform(38, 50) / 3.6
                cars.append(dict(x=0.0, v=v0, v0=v0, lane=ln, k=0, commit=False, col=int(rng.integers(5))))
                next_sp[ln] = t + rng.uniform(9, 18)
        for ln in (0, 1):
            cs = sorted([c for c in cars if c["lane"] == ln], key=lambda c: -c["x"])
            lead = None
            for c in cs:
                st = st_all[c["k"]] if c["k"] < N_SIG else 0
                d_eff = sig[c["k"]] - S0 - c["x"]
                obst = c["k"] < N_SIG and st > 0 and not c["commit"]
                need = c["v"] ** 2 / (2 * max(d_eff, 0.01))
                if obst and st == 1 and need > B_CRIT and d_eff > 0:
                    c["commit"] = True
                    obst = False
                a = ACC * (1 - (c["v"] / c["v0"]) ** 4)
                if lead is not None:
                    gap = max(0.5, lead["x"] - c["x"] - carl)
                    ss = 2.0 + c["v"] * 1.2 + c["v"] * (c["v"] - lead["v"]) / (2 * math.sqrt(ACC * BRAKE))
                    a = ACC * (1 - (c["v"] / c["v0"]) ** 4 - (max(ss, 0) / gap) ** 2)
                if obst and need >= BRAKE:
                    a = min(a, -need)
                if obst and d_eff <= 0.05:
                    a = 0.0
                    c["v"] = 0.0
                vn = max(0.0, c["v"] + max(a, -9.0) * DT)
                xn = c["x"] + (c["v"] + vn) / 2 * DT
                if obst and xn > sig[c["k"]] - S0:
                    xn, vn = sig[c["k"]] - S0, 0.0
                if lead is not None and xn > lead["new"][0] - carl + 0.3:
                    xn, vn = max(c["x"], lead["new"][0] - carl + 0.3), min(vn, lead["new"][1])
                c["new"] = (xn, vn)
                lead = c
        for c in cars:
            c["x"], c["v"] = c.pop("new")
            if c["k"] < N_SIG and c["x"] > sig[c["k"]]:
                c["k"] += 1
                c["commit"] = False
        cars = [c for c in cars if c["x"] < L + 80]
        t += DT
        while fi < len(frames) and t >= frames[fi]:
            rec.append([(c["x"], c["lane"], c["col"]) for c in cars])
            fi += 1
    _AMB = rec
    return rec


def draw_ambient(ctx, t, a):
    if a <= 0:
        return
    rec = ambient()
    j = min(len(rec) - 1, int(round(t * FPS)))
    sm = sample()["m"]
    for x, ln, ci in rec[j]:
        s = x * sm["ppm"]
        fa = clamp01((s - 60) / 50) * clamp01((P_TOT + 40 - s) / 60)
        draw_car(ctx, s, 1 if ln == 0 else -1, AMB_COLS[ci], a * fa, k=1.12)


# ---------- 2台 ----------

def tau_race(t):
    return max(0.0, (t - T_GO) * RACE_X)


def tau_wave(t):
    return max(0.0, (t - T_TW_RUN) * WAVE_X)


def car_x(track, tau):
    j = tau / DT
    n = len(track["x"])
    if j >= n - 1:
        return float(track["x"][-1])
    i = int(j)
    f = j - i
    return float(track["x"][i] * (1 - f) + track["x"][i + 1] * f)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    if t < T_TW:
        return 1 - ease((t - T_G0) / 0.4)
    if t < T_WB:
        return ease((t - T_TW) / 0.4)
    return 1 - ease((t - T_WB) / 0.4)


def scene_mode(t):
    return "m" if t < T_TW else "w"


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    lay = layout(t)
    mode = scene_mode(t)
    s = sample()
    sm = s[mode]
    ctx.push_group()
    ctx.set_source_surface(road_surface(lay), 0, 0)
    ctx.paint()
    ctx.save()
    apply_layout(ctx, lay)
    if mode == "m":
        if t < T_GO:
            t_abs = float(sm["road"]["t0"][0]) + (t - T_GO) * INTRO_X
        else:
            t_abs = float(sm["road"]["t0"][0]) + tau_race(t)
        tau = tau_race(t)
    else:
        t_abs = float(sm["road"]["t0"][0]) + (t - T_TW_RUN) * WAVE_X
        tau = tau_wave(t)
    draw_signals(ctx, sm, t_abs)
    if t < T_GO:
        draw_ambient(ctx, t, 1 - ease((t - T_CD[-1] + 0.3) / 0.6))
    for key, lane, col in (("A", 1, COL_A), ("B", -1, COL_B)):
        draw_car(ctx, car_x(sm[key], tau) * sm["ppm"], lane, col, k=CAR_K)
    # 追いつかれた（赤ペンで2台を囲む）
    if mode == "m":
        for n, (k, te) in enumerate(sm["catch"]):
            tv = T_GO + te / RACE_X
            if tv - 0.05 <= t < tv + 1.6:
                xk, yk, _ = path_pt(sig_px(sm)[k] - CAR_L * CAR_K / 2)
                note.pen_circle(ctx, xk, yk, 56, 46, RED, seed=60 + n, width=5, progress=clamp01((t - tv) / 0.3))
    ctx.restore()
    # 字（道の絵の座標から画面の座標に直して描く）
    sc = lay[0]
    xs, ys = to_dev(lay, XL + 40, -ROAD_W / 2 - 28)
    if t >= T_GO:
        text(ctx, "スタート", xs, ys, 30 * sc, INK, bold=False)
    xg, yg = to_dev(lay, XL + 30, 3 * ROW + ROAD_W / 2 + 24)
    text(ctx, "ゴール", xg, yg, 30 * sc, INK, bold=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    # 冒頭: 2台の名札
    if t < T_GO:
        la = 1 - ease((t - T_MOVE + 0.15) / 0.3)
        xa, ya = to_dev(lay, 0, -LANE - 42)
        xb, yb = to_dev(lay, 0, LANE + 44)
        text(ctx, "ふつう 時速40km", 118, ya, 30, INK_A, align="left", alpha=la)
        text(ctx, "速め 時速60km", 118, yb, 30, INK_B, align="left", alpha=la)
    # 追いつかれた！
    if mode == "m" and a > 0.5:
        for n, (k, te) in enumerate(sm["catch"]):
            tv = T_GO + te / RACE_X
            if tv <= t < tv + 1.6:
                b = ease_out((t - tv) / 0.2) * (1 - ease((t - tv - 1.3) / 0.3))
                xk, yk, _ = path_pt(sig_px(sm)[k])
                dx, dy = to_dev(lay, xk, yk)
                note.sticky(ctx, "追いつかれた！", min(max(dx - 230, 260), 760), dy - 78, 32, "pink", fg=RED, a=b, tilt=-0.03)


# ---------- 読み取り（2台の経過時間・赤で止まった回数・到着） ----------

def mmss(sec):
    sec = max(0, int(round(sec)))
    return f"{sec // 60}分{sec % 60:02d}秒"


def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    if T_TW_RUN - 0.4 <= t < T_WB + 0.4:
        return ease_out((t - T_TW_RUN + 0.4) / 0.4) * (1 - ease((t - T_WB) / 0.35))
    return 0.0


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    mode = "m" if t < T_TW else "w"
    sm = sample()[mode]
    tau = tau_race(t) if mode == "m" else tau_wave(t)
    X = RACE_X if mode == "m" else WAVE_X
    for key, cx, lab, ink, col in (("A", 330.0, "ふつう 40km", INK_A, COL_A), ("B", 790.0, "速め 60km", INK_B, COL_B)):
        tr = sm[key]
        lw = core.text_width(lab, 32)
        draw_car(ctx, 0, 0, col, a, at=(cx - lw / 2 - 10, 1222, 0.0))
        text(ctx, lab, cx + 24, 1222, 32, ink, alpha=a)
        arrived = tau >= tr["T"]
        text(ctx, "到着" if arrived else "経過", cx, 1270, 28, RED if arrived else PENCIL, bold=arrived, alpha=a)
        text(ctx, mmss(min(tau, tr["T"])), cx, 1318, 50, ink if arrived else INK, alpha=a)
        if arrived:
            pa = clamp01((tau - tr["T"]) / X / 0.3)
            note.pen_circle(ctx, cx, 1318, 145, 40, RED, seed=70 + (key == "B"), width=5, progress=pa, alpha=a)
        n = int(np.sum(tr["t_stop"] <= tau))
        text(ctx, f"赤で停止 {n}回", cx, 1378, 34, INK, alpha=a)
    text(ctx, f"再生 {X:.0f}倍", 580, 1425, 24, PENCIL, bold=False, alpha=a)
    # 2台とも着いたら、差
    tA, tB = sm["A"]["T"], sm["B"]["T"]
    if tau >= tA:
        b = a * ease_out((tau - tA) / X / 0.3)
        note.sticky(ctx, f"60kmが {mmss(tA - tB)} 早い", 580, 880, 42, "yellow", fg=INK, a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def zone_of(f):
    return np.where(f < RULE_LO, 0, np.where(f < RULE_HI, 1, 2))


def grid_surface(n):
    """はじめの n 回ぶんを塗ったマス目（1行＝125回ずつ）"""
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    z = zone_of(shown()["m"]["f"])
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(c) for c in ZONE_COLS], np.uint8)
    m = min(N_TRIP, key * G_COLS)
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
    sh = shown()["m"]
    n = N_TRIP * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000回", 580, 612, 34, INK, alpha=a)
    z = zone_of(sh["f"][:int(n)])
    cnt = np.bincount(z, minlength=3)
    for i, lab in enumerate(LABELS):
        y = 1190 + i * 58
        fill(ctx, hexrgb(ZONE_COLS[i], a))
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, f"{'ABC'[i]} {lab}", 282, y, 36, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt[i])}回", 900, y, 36, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。信号なしの計算とくらべて色分け", 580, 1380, 26, PENCIL, bold=False, alpha=a)


# ---------- 棒: 早く着いた時間（同じものさし） ----------
BAR_X0, BAR_LEN = 250.0, 560.0                    # 120秒 → 560px


def bx(sec):
    return BAR_X0 + sec / 120.0 * BAR_LEN


def draw_hbar(ctx, y, sec, col, lab, val, a, g=1.0):
    text(ctx, lab, BAR_X0, y - 46, 32, INK, align="left", alpha=a)
    w = (bx(sec) - BAR_X0) * g
    if w > 1:
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        core.rrect(ctx, BAR_X0, y - 20, w, 40, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.stroke()
    tw = core.text_width(val, 36)
    vx = BAR_X0 + w + 14
    if vx + tw > 925:
        vx = BAR_X0 + w - tw - 12
    text(ctx, val, vx, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def bars_alpha(t):
    if t < T_BAR:
        return 0.0
    if t < T_TW:
        return ease_out((t - T_BAR) / 0.3) * (1 - ease((t - T_TW) / 0.3))
    if t < T_WB:
        return 0.0
    return ease_out((t - T_WB) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def draw_bars(ctx, t):
    a = bars_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "60kmの車が 早く着いた時間", 580, 640, 40, INK, alpha=a)
    text(ctx, "（1万回の真ん中の値）", 580, 690, 30, PENCIL, bold=False, alpha=a)
    t0 = T_BAR if t < T_TW else T_WB
    g1 = ease_out((t - t0 - 0.15) / 0.4) if t < T_TW else 1.0
    g2 = ease_out((t - t0 - 0.55) / 0.5) if t < T_TW else 1.0
    draw_hbar(ctx, 810, sh["m"]["naive_med"], "#d6d1c4", "信号がなかったら（計算）", mmss(sh["m"]["naive_med"]), a, g1)
    draw_hbar(ctx, 945, sh["m"]["saved_med"], COL_B, "つながっていない信号", mmss(sh["m"]["saved_med"]), a, g2)
    if t >= T_WB:
        g3 = ease_out((t - T_WB - 0.7) / 0.5)
        draw_hbar(ctx, 1080, sh["w"]["saved_med"], "#7bc6a4", "つながった信号（40kmに合わせた）", mmss(sh["w"]["saved_med"]), a, g3)
        if t >= T_WB + 1.4:
            b = ease_out((t - T_WB - 1.4) / 0.3) * a
            note.sticky(ctx, f"60kmの車は 信号8つで 平均{sh['w']['stB']:.1f}回 赤で止まる\n（40kmの車は {sh['w']['stA']:.1f}回）", 580, 1270, 32,
                        "mint", a=b, tilt=-0.02)
    elif t >= T_REV:
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, "速く走った分、ほぼ計算どおり早く着く", 580, 1110, 38, "pink", fg=RED, a=b, tilt=-0.02)
        b2 = ease_out((t - T_REV - 1.0) / 0.3) * a
        text(ctx, f"{pct(sh['m']['catch'])}%の回は、途中で追いつかれていた", 580, 1240, 32, INK, bold=False, alpha=b2)


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


CD_X, CD_Y = 580.0, 1075.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、信号8つの道を0秒目から車が流れる"""
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
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 38, 575, 860, gap=48)):
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
            core.rrect(ctx, cx - 150, cy - 175, 300, 255, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 175, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 115, 42, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 62, 60, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 92, INK, alpha=a)
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
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840, gap=48)):
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
        note.sticky(ctx, "スタート", 580, 880, 36, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_bars(ctx, t)
    # ひねり
    if T_TW <= t < T_TW_RUN:
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "信号がつながっていたら？", 580, 860, a=ba, t_rel=t - T_TW, size=50)
        b2 = ba * ease_out((t - T_TW - 0.5) / 0.3)
        note.sticky(ctx, "時速40kmで走ると、青が順に続く道", 580, 1040, 32, "mint", a=b2, tilt=0.02)
    # 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "じゃあ、なんで\n「追いつかれる」気がするの？", 580, 800, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.0) / 0.3)
        note.sticky(ctx, "見えない所で 取り返している", 580, 1010, 44, "pink", fg=RED, a=r, tilt=0.025)
        sh = shown()["m"]
        r2 = ease_out((t - T_Q - 1.3) / 0.3)
        text(ctx, f"追いつかれる … 1回の道のりで平均 {sh['n_catch']:.1f}回", 580, 1140, 30, INK, bold=False, alpha=r2)
        text(ctx, f"相手だけ赤で止まる … 平均 {sh['n_pull']:.1f}回", 580, 1190, 30, INK, bold=False, alpha=r2)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)          # 道の絵の上に（カウントダウンの札が道に隠れないように）


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
    tt = np.arange(int(SR * DURATION)) / SR
    # 車の走る音（低いうなり）。冒頭はほかの車、本編は2台の速さに合わせる
    hum = band_noise(DURATION, 60.0, 320.0, 3, 0.03)
    env = np.zeros_like(tt)
    env[tt < T_GO] = 0.8
    for X, t0, sm in ((RACE_X, T_GO, s["m"]), (WAVE_X, T_TW_RUN, s["w"])):
        sel = (tt >= t0) & (tt < t0 + max(sm["A"]["T"], sm["B"]["T"]) / X)
        for c in ("A", "B"):
            vv = np.interp((tt[sel] - t0) * X / DT, np.arange(len(sm[c]["v"])), sm[c]["v"])
            env[sel] += 0.5 * vv / V_B
    env = np.convolve(env, np.ones(2400) / 2400, mode="same")
    mx.add(0, hum * env, 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    # 本編
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    for key, X, t0 in (("m", RACE_X, T_GO), ("w", WAVE_X, T_TW_RUN)):
        sm = s[key]
        for c, f0 in (("A", 523.3), ("B", 659.3)):
            for ts in sm[c]["t_stop"]:
                mx.add(t0 + ts / X, blip(f0, 0.12), 0.3)             # 赤で止まった
            mx.add(t0 + sm[c]["T"] / X, bell(784.0 if c == "B" else 659.3, 1.2), 0.4)
    for k, te in s["m"]["catch"]:
        mx.add(T_GO + te / RACE_X, bell(523.3, 0.8), 0.35)
    # 1万回
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_BAR + 0.15, blip(587.3, 0.15), 0.35)
    mx.add(T_BAR + 0.55, blip(784.0, 0.15), 0.35)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.45)
    mx.add(T_WB + 0.7, blip(698.5, 0.15), 0.35)
    mx.add(T_WB + 1.4, bell(1046.5, 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.0, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    d = data()
    checks = []
    # (1) 信号がない（いつも青）道: 着く時間 = 道のり÷速さ ＋ 加速の遅れ（IDM の自由走行の式を積分した閉じた式）
    #     遅れ = ∫0^v0 (1−v/v0)/a(v) dv = (v0/a)·(ln2/4 + π/8)
    for v0 in (V_A, V_B):
        L = 3000.0
        rd = dict(sig=np.full((1, N_SIG), 1e9), L=np.array([L]), cyc=np.full((1, N_SIG), 90.0),
                  off=np.zeros((1, N_SIG)), t0=np.zeros(1))
        T = drive(rd, v0)["T"][0]
        exact = L / v0 + v0 / ACC * (math.log(2) / 4 + math.pi / 8)
        checks.append((f"信号なし {v0 * 3.6:.0f}km/h の所要（秒）が閉じた式と一致", float(T), exact, 0.15))
    # (2) 信号1つ・ブレーキと加速がとても強い車: 待ち時間の平均 = 赤（黄を含む）の長さ² ÷ (2×サイクル)
    rng = np.random.default_rng(1)
    n = 20000
    C = 90.0
    rd = dict(sig=np.concatenate([np.full((n, 1), 1500.0), np.full((n, N_SIG - 1), 1e9)], 1), L=np.full(n, 3000.0),
              cyc=np.full((n, N_SIG), C), off=rng.uniform(0, C, (n, N_SIG)), t0=np.zeros(n))
    free = dict(rd, sig=np.full((n, N_SIG), 1e9))
    Tl = drive(rd, V_A, acc=60.0, brake=60.0, b_crit=1e9, dt=0.02)["T"]
    Tf = drive(free, V_A, acc=60.0, brake=60.0, b_crit=1e9, dt=0.02)["T"]
    r = (1 - GREEN) * C + YELLOW
    checks.append(("信号1つの待ち時間の平均（秒）が r²/(2C) と一致", float(np.mean(Tl - Tf)), r * r / (2 * C), 0.4))
    # (3) つながった道: 時速40kmの車は、2つ目より先の信号でほとんど止まらない
    checks.append(("つながった道: 40kmの車が信号2〜8で止まった回の割合 < 2%", float(np.mean(d["wA_sa"][:, 1:].any(1)) < 0.02),
                   1.0, 0.0))
    # (4) 時間の刻みを半分にしても、答えの値（中央値）が変わらない（2,000回で）
    rd = road_of("m", np.arange(2000))
    f1 = race(rd)["f"]
    f2 = race(rd, dt=DT / 2)["f"]
    checks.append(("刻み 0.1秒と0.05秒で中央値 f の差", float(np.median(f1) - np.median(f2)), 0.0, 0.03))
    # (5) 平均で見ると、待ち時間は2台とも同じ（青の割合が同じなので）→ 早く着いた時間の平均 ÷ 信号なしの計算 ≈ 1
    checks.append(("つながっていない道: 早く着いた時間の平均 ÷ 信号なしの計算の平均", sh["m"]["saved_mean"] / sh["m"]["naive_mean"], 1.0, 0.1))
    # (6) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ。棒（秒の中央値どうし）で見ても同じ区分
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["m"]["f_med"])), float(INTRO.correct), 0.0))
    checks.append(("棒の比（中央値どうし）でも同じ区分", float(answer_by_rule(sh["m"]["saved_med"] / sh["m"]["naive_med"])),
                   float(INTRO.correct), 0.0))
    checks.append(("ひねり: つながった道では A（ほぼ同じ）になる", float(answer_by_rule(sh["w"]["f_med"])), 0.0, 0.0))
    checks.append(("全員ゴールした", float(np.isfinite(d["mA_T"]).sum() + np.isfinite(d["mB_T"]).sum()
                                     + np.isfinite(d["wA_T"]).sum() + np.isfinite(d["wB_T"]).sum()), 4.0 * N_TRIP, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    sh = shown()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.1f}倍 / ひねり {WAVE_X:.1f}倍  追いつかれた回数の平均 {sh['m']['n_catch']:.2f}"
          f"  40kmだけ赤で止まった信号の平均 {sh['m']['n_pull']:.2f}（そういう信号があった回 {sh['m']['any_pull']:.3f}）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 16.0, 18.0, 19.5, T_G0 + 1.5, T_G1 + 0.5,
              T_BAR + 1.0, T_REV + 1.5, T_TW + 1.0, T_TW_RUN + 2.0, T_TW_RUN + 5.0, T_WB + 2.5, T_Q + 2.0, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
