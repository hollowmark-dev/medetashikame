"""寒い朝、エアコン暖房の風向きは 上向き と 下向き、足もとが早く暖まるのは？ 同じ部屋2つで1万回くらべる。— 2026-10-23 作成（公開予定 10/29・45秒前後）

くらべるのは「足もとが早く暖まるか」だけ（お金・電気代は入れない。画面にも概要欄にも書かない）。

モデル（部屋を高さ方向の12層に分けた1次元の温度モデル。床の面積 A・天井の高さ H。部屋のかたちは同じで、風向きだけが違う2部屋）
  空気: 12層（1層の厚さ dz = H/12 ≒ 0.2m）。いちばん下の層の真ん中が「床から約10cm」＝足もと。顔の高さ 1.5m は 2層のあいだを補間する。
  エアコン: 壁の上（床から H−0.3m）にあり、吸い込み口の層の温度 T_s をはかる（吸い込み口の温度で運転する機種が多い。仮定）。
        出す熱 P = 最大能力 Q_max × clip((設定温度 + 0.5 − T_s) ÷ 2.0, 0.25, 1)   … 設定温度の1.5℃手前までは全力、届くと 25%（仮定）。
        吹き出す風の温度 = T_s + P ÷ (ρ·c_p·G)（G は風量。ρ·c_p = 1207 J/(m³K)）。
  温風の行き先（吹き出した向きで決まる）:
        風は吹き出し口から斜めに進み、まわりの空気を引き込んで（引き込む量 = 風量の 2〜6倍・仮定。自由噴流の
        流量は距離とともに増える）、届いた高さ z_arr で部屋に入る。引き込むのは、吹き出し口から z_arr までの層の空気。
        z_arr = 吹き出し口の高さ − 届く距離 × sin(角度) + 浮き上がり。届く距離 = 2〜4m × √(風量 ÷ 0.1m³/s)（仮定）、
        浮き上がり = 0.3〜1.0m（温風は軽いので上へ反る・仮定）。
        上向き = 水平〜やや上〜少し下（角度 −10°〜+15°・下が正）、下向き = 斜め下（50°〜80°）。
        天井の近くに入った温風は、下の空気よりも軽いので混ざりにくい。床の近くに入った温風は、上の空気よりも軽いので
        浮き上がって混ざる。
  空気どうしの混ざり方（成層）:
        上の層のほうが暖かい（安定）ときは混ざりにくい。上下の層の熱の伝わり（乱流拡散）は 0.008〜0.030 m²/s（仮定。
        下の「天井と床の温度差」の値に合うよう幅を決めた）。
        下の層のほうが暖かい（不安定）ときは、隣り合う2層を完全に混ぜる（毎回、下から上・上から下の順に1往復）。
        温風が部屋の中を回る流れ（吹き出しと吸い込みの流量のつり合い）は、層のあいだの上下の流れとして足している（風上差分）。
  壁・窓・床・天井・家具（熱をためる所）: 各層に1つずつの温度 T_m。空気とのあいだの熱の伝わり 20〜45 W/(m²K) × 床の面積、
        熱容量 40〜100 kJ/(m²K) × 床の面積（軽い〜ふつうのつくりの、短い時間で温まる表面の分・仮定）。
        壁などから外へは 2.0〜4.5 W/(m²K) × 床の面積（平成11年基準の熱損失係数 2.7 前後〜古い家を仮定）。
  すきま風・換気: 0.3〜0.8 回/時。冷たい外の空気が下の層から入り、いちばん上の層から出ていく（煙突効果）。
  1回ごとの条件（でたらめ）: 部屋の広さ 6〜12畳（1畳 = 1.62 m²）、天井の高さ 2.4〜2.7 m、外の気温 0〜10℃、
        最初の室温 8〜15℃（冬の朝。外より2℃以上高い）、設定温度 20〜24℃、
        暖房の最大の強さ 150〜260 W/m²（床1m²あたり・仮定）、運転を始めてから熱が出きるまでの時定数 90〜240秒（仮定）、
        風量 7〜13 m³/分（暖房の強風・仮定）。
  測るもの: 足もと（床から約10cm）が 18℃ に届くまでの時間（分）。18℃ は、WHO が寒い季節の室温の下限として示した値
        （WHO「Housing and Health Guidelines」2018）。90分たっても届かないときは 90分とする（打ち切り）。
        同じ回の中で、上向きと下向きを同じ部屋・同じ条件で比べる。時間の刻みは 1秒の足し算。

天井付近と床付近の温度むら（暖房時）。調べられた値（原典は確認できていない・要約で確認）:
  ・エアコン暖房の特許（US 5,477,698）の記載: 壁掛けのヒートポンプ、設定 24℃、外気 10℃、部屋 25 m²で、1時間後に
    床から10cmと230cmで 8.6℃の差（床が寒いまま）。
  ・環境省の資料の紹介（原典は未確認）: 床と天井で「最大 5〜10℃」の温度差が出ることがある。
  ・メーカーの家庭向けの解説（会社名は出さない決まりなので、出典としては使わない）: 暖房の吹き出しが下向き（60度以上）でないと、温風は天井にたまりやすい。
  これらにあわせて、「上向き」の 1万回の、60分後の（天井近く − 足もと）の温度差の真ん中の値が 3〜9℃に入る幅にした（run_checks で確かめる）。

問い: 「エアコン暖房、風向きは上？下？/ 足もとが早く暖まるのは？」（前提「冬の朝・同じ部屋ふたつ」）
      選択肢（記号の並びは LABELS の順。正解・TAG は 計算の結果で決める）: 上向き ／ ほぼ同じ ／ 下向き
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「下向きのほうが先に 18℃に届いた回」の割合 p と、時間の差（上向き − 下向き）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 3分 なら「下向き」、p ≤ 40% かつ g ≤ −3分 なら「上向き」、それ以外は「ほぼ同じ」。
      結果がどれでも、そのまま出す。
ひねり: 1行だけ。「では、15分たったら顔の高さは？」（同じ1万回の、15分後の顔の高さ 1.5m の温度の真ん中の値）。
締め: 「あなたのエアコン、いま風向きはどっち？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（並んだ2部屋）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "aircon-kazamuki"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261029
N_LAY = 12
DT = 1.0                                           # 時間の刻み（秒）
TMAX = 90 * 60.0                                   # 打ち切り（秒）
T_FOOT = 18.0                                      # 足もとがここに届いたら「暖まった」
TATAMI, TATAMI_M2 = (6.0, 12.0), 1.62
H_RANGE = (2.4, 2.7)
T_OUT, T_IN0, T_SET = (0.0, 10.0), (8.0, 15.0), (20.0, 24.0)
QC = (150.0, 260.0)                                # 最大能力（W/m²）
RAMP = (90.0, 240.0)                               # 運転を始めてから、熱が出きるまでの時定数（秒）
G_RANGE = (7.0, 13.0)                              # 風量（m³/分）
CM, HA, QUA = (40.0, 100.0), (20.0, 45.0), (2.0, 4.5)   # kJ/(m²K)、W/(m²K)、W/(m²K)
ACH = (0.3, 0.8)
DS = (0.008, 0.030)                                # 上の層が暖かいとき（安定）の上下の混ざり（m²/s）
RE = (2.0, 6.0)                                    # 引き込む量 ÷ 風量
L0, BZ = (2.0, 4.0), (0.3, 1.0)                    # 届く距離（m）、浮き上がり（m）
TH_UP, TH_DN = (-10.0, 15.0), (50.0, 80.0)         # 吹き出しの角度（度。下が正）
UNIT_DROP = 0.3                                    # 吹き出し口は天井から 0.3m 下
SIGMA_ARR = 0.2                                    # 届いた高さのまわりの広がり（m）
RHOCP = 1207.0                                     # ρ·c_p（J/(m³K)）
P_MIN, P_BAND = 0.25, 2.0

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 3.0       # 割合・分


def answer_by_rule(p_down, gap_med_min):
    """p_down = 下向きが先に届いた回の割合、gap_med_min = (上向き − 下向き) の時間の差の真ん中の値（分）。'down' / 'same' / 'up'"""
    if p_down >= RULE_HI and gap_med_min >= RULE_GAP:
        return "down"
    if p_down <= RULE_LO and gap_med_min <= -RULE_GAP:
        return "up"
    return "same"


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    d = dict(tat=u(TATAMI), H=u(H_RANGE), Tout=u(T_OUT), T0=u(T_IN0), Tset=u(T_SET), qc=u(QC), G=u(G_RANGE) / 60.0,
             cm=u(CM) * 1000.0, hA=u(HA), qua=u(QUA), ach=u(ACH), Ds=u(DS), re=u(RE), L0=u(L0), Bz=u(BZ),
             th_up=np.radians(u(TH_UP)), th_dn=np.radians(u(TH_DN)), ramp=u(RAMP))
    d["T0"] = np.maximum(d["T0"], d["Tout"] + 2.0)
    d["A"] = d["tat"] * TATAMI_M2
    return d


def z_arrival(d, mode):
    """温風が部屋に入る高さ（m）= 吹き出し口の高さ − 届く距離 × sin(角度) + 浮き上がり。層の真ん中より外には出さない"""
    H = d["H"]
    th = d["th_up"] if mode == "up" else d["th_dn"]
    Lt = d["L0"] * np.sqrt(d["G"] / 0.1)
    dz = H / N_LAY
    return np.clip(H - UNIT_DROP - Lt * np.sin(th) + d["Bz"], 0.5 * dz, H - 0.5 * dz)


def simulate(d, mode, hist=False, snaps=(900.0, 3600.0), tmax=TMAX, closed=False):
    """mode = 'up' / 'down'。足もとが T_FOOT に届く時刻（秒。届かなければ inf）と、snaps の時刻の層の温度などを返す。
    hist=True（1回ぶんだけ）なら 10秒ごとの全層の温度の履歴も返す。closed=True は照合用（外へ逃げる熱・すきま風を0にする）。
    snap["Pint"] = 出した熱の合計（J）、snap["end"] = (最後の空気の温度, 最後のかたまりの温度)"""
    n = len(d["H"])
    N = N_LAY
    H, A = d["H"], d["A"]
    dz = H / N
    V = A * dz
    ar = np.arange(n)
    zc = (np.arange(N)[:, None] + 0.5) * dz[None, :]
    zu = H - UNIT_DROP
    s_idx = np.minimum(np.floor(zu / dz).astype(int), N - 1)
    z_arr = z_arrival(d, mode)
    g = np.exp(-((zc - z_arr[None, :]) ** 2) / (2 * SIGMA_ARR ** 2))
    g += 1e-12
    g /= g.sum(0)
    lo, hi = np.minimum(z_arr, zu), np.maximum(z_arr, zu)
    w = ((zc >= (lo - dz / 2)[None, :]) & (zc <= (hi + dz / 2)[None, :])).astype(float)
    w += 1e-12 * (np.abs(zc - z_arr[None, :]) < dz)
    w /= w.sum(0)
    delta = (np.arange(N)[:, None] == s_idx[None, :]).astype(float)
    G, E = d["G"], d["re"] * d["G"]
    F = G + E
    Qmax = d["qc"] * A
    Qinf = (0.0 if closed else d["ach"] / 3600.0) * A * H
    hAi = d["hA"] * A / N
    UAi = (0.0 if closed else d["qua"]) * A / N
    Cmi = d["cm"] * A / N
    Dz = d["Ds"] / dz ** 2
    Tset, Tout = d["Tset"], d["Tout"]
    T = np.tile(d["T0"], (N, 1)).astype(float)
    Tm = T.copy()
    tfin = np.full(n, np.inf)
    snap = {}
    Hh = [(0.0, T[:, 0].copy())] if hist else None
    nstep = int(tmax / DT)
    t = 0.0
    Pint = np.zeros(n)
    for step in range(nstep):
        Ts = T[s_idx, ar]
        P = Qmax * np.clip((Tset + 0.5 - Ts) / P_BAND, P_MIN, 1.0)
        P = P * (1.0 - np.exp(-t / d["ramp"]))
        Pint += P * DT
        Tsup = Ts + P / (RHOCP * G)
        Tjet = (G * Tsup + E * (w * T).sum(0)) / F
        inflow = F * g
        out = G * delta + E * w
        sv = inflow - out
        sv[0] += Qinf
        sv[-1] -= Qinf
        q = np.cumsum(sv, axis=0)[:-1]
        flux = q * np.where(q > 0, T[:-1], T[1:])
        dE = inflow * Tjet - out * T
        dE[0] += Qinf * Tout
        dE[-1] -= Qinf * T[-1]
        dE[:-1] -= flux
        dE[1:] += flux
        dT = dE / V + hAi * (Tm - T) / (RHOCP * V)
        lap = np.zeros_like(T)
        lap[1:-1] = T[2:] - 2 * T[1:-1] + T[:-2]
        lap[0] = T[1] - T[0]
        lap[-1] = T[-2] - T[-1]
        dT += Dz * lap
        Tm += DT * (hAi * (T - Tm) - UAi * (Tm - Tout)) / Cmi
        T = T + DT * dT
        for i in range(N - 1):                      # 下が暖かければ混ぜる（下から上へ）
            m = T[i] > T[i + 1]
            av = 0.5 * (T[i] + T[i + 1])
            T[i] = np.where(m, av, T[i])
            T[i + 1] = np.where(m, av, T[i + 1])
        for i in range(N - 2, -1, -1):              # （上から下へ）
            m = T[i] > T[i + 1]
            av = 0.5 * (T[i] + T[i + 1])
            T[i] = np.where(m, av, T[i])
            T[i + 1] = np.where(m, av, T[i + 1])
        t += DT
        hit = np.isinf(tfin) & (T[0] >= T_FOOT)
        if hit.any():
            tfin = np.where(hit, t, tfin)
        for sn in snaps:
            if abs(t - sn) < DT / 2:
                snap[sn] = T.copy()
        if hist and (step + 1) % 10 == 0:
            Hh.append((t, T[:, 0].copy()))
        if t >= max(snaps) and not np.isinf(tfin).any():
            break
    snap["Pint"] = Pint
    snap["end"] = (T.copy(), Tm.copy())
    if hist:
        return tfin, snap, Hh, dz[0]
    return tfin, snap, None, dz


def face_temp(T, d, z=1.5):
    """顔の高さ z（m）の温度。層の真ん中どうしを補間"""
    n = T.shape[1]
    dz = d["H"] / N_LAY
    x = np.clip(z / dz - 0.5, 0, N_LAY - 1.000001)
    i0 = np.floor(x).astype(int)
    f = x - i0
    ar = np.arange(n)
    return T[i0, ar] * (1 - f) + T[i0 + 1, ar] * f
# ---- MODEL END ----

_RES = {}


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


def results():
    if _RES:
        return _RES["m"]
    cache = OUT / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    fn = cache / f"res_{_model_hash()}.npz"
    d = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
    if fn.exists():
        z = np.load(fn)
        r = {k: z[k] for k in z.files}
    else:
        r = {}
        for mode in ("up", "down"):
            tf, sn, _, _ = simulate(d, mode)
            r[f"t_{mode}"] = tf
            r[f"foot15_{mode}"] = sn[900.0][0]
            r[f"face15_{mode}"] = face_temp(sn[900.0], d)
            r[f"mean15_{mode}"] = sn[900.0].mean(0)
            r[f"ceil60_{mode}"] = sn[3600.0][-1]
            r[f"foot60_{mode}"] = sn[3600.0][0]
            r[f"face60_{mode}"] = face_temp(sn[3600.0], d)
        np.savez(fn, **r)
    r["p"] = d
    for k in ("t_up", "t_down"):
        r[k + "_raw"] = r[k] / 60.0                 # 分（届かなければ inf）
        r[k] = np.where(np.isinf(r[k]), TMAX, r[k]) / 60.0   # 打ち切りは 90分
    _RES["m"] = r
    return r


def shown():
    r = results()
    tu, td = r["t_up"], r["t_down"]
    gap = tu - td
    win = td < tu
    tie = td == tu
    sun = np.isinf(r["t_up_raw"]) | np.isinf(r["t_down_raw"])
    return dict(p_down=float(win.mean()), n_down=int(win.sum()), n_up=int((tu < td).sum()), n_tie=int(tie.sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_up=float(np.median(tu)), med_down=float(np.median(td)),
                q_up=np.percentile(tu, [10, 90]), q_down=np.percentile(td, [10, 90]),
                n_unfin_up=int(np.isinf(r["t_up_raw"]).sum()), n_unfin_down=int(np.isinf(r["t_down_raw"]).sum()),
                dT60_up=float(np.median(r["ceil60_up"] - r["foot60_up"])), dT60_down=float(np.median(r["ceil60_down"] - r["foot60_down"])),
                dT60_up_q=np.percentile(r["ceil60_up"] - r["foot60_up"], [10, 90]),
                face15_up=float(np.median(r["face15_up"])), face15_down=float(np.median(r["face15_down"])),
                foot15_up=float(np.median(r["foot15_up"])), foot15_down=float(np.median(r["foot15_down"])),
                p_face_up_warmer=float((r["face15_up"] > r["face15_down"]).mean()),
                face_gap_med=float(np.median(r["face15_down"] - r["face15_up"])),
                mean15_up=float(np.median(r["mean15_up"])), mean15_down=float(np.median(r["mean15_down"])),
                n_any_unfin=int(sun.sum()))


def hm_(minutes):
    return f"{int(round(minutes))}分"


def report():
    sh = shown()
    print(f"下向きが先 {sh['p_down']:.4f}（{sh['n_down']}回 / 上向きが先 {sh['n_up']}回 / 同時 {sh['n_tie']}）  差(上向き−下向き)の中央値 "
          f"{sh['gap_med']:+.2f}分 平均 {sh['gap_mean']:+.1f} 10/25/75/90% {np.round(sh['gap_q'], 1)}")
    print(f"  答え {answer_by_rule(sh['p_down'], sh['gap_med'])}")
    print(f"  18℃に届く時間の中央値 上向き {sh['med_up']:.1f}分（10/90% {np.round(sh['q_up'], 1)}）/ 下向き {sh['med_down']:.1f}分（{np.round(sh['q_down'], 1)}）"
          f" 届かず(90分) 上向き {sh['n_unfin_up']} 下向き {sh['n_unfin_down']}")
    print(f"  60分後の（天井近く−足もと）の中央値 上向き {sh['dT60_up']:.2f}℃（10/90% {np.round(sh['dT60_up_q'], 1)}）/ 下向き {sh['dT60_down']:.2f}℃")
    print(f"  15分後 足もと 上向き {sh['foot15_up']:.1f} / 下向き {sh['foot15_down']:.1f}℃  顔(1.5m) 上向き {sh['face15_up']:.1f} / 下向き {sh['face15_down']:.1f}℃"
          f"  上向きの顔が暖かい回 {sh['p_face_up_warmer']:.3f}  部屋の平均 上向き {sh['mean15_up']:.1f} / 下向き {sh['mean15_down']:.1f}")


if __name__ == "__main__" and "--model" in sys.argv:
    import time
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    report()
    print(f"  計算 {time.time() - t0:.0f}秒")
    sys.exit(0)


# =====================================================================
# 見本（並んだ2部屋）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 2部屋とも 90分以内に 18℃に届いた回の中で、上向きの時間・下向きの時間・その差が、それぞれ（届いた回の）真ん中の値の近く
    （±15〜20%）。その中でいちばん真ん中に近い回。"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    tu, td = r["t_up_raw"], r["t_down_raw"]
    fin = np.isfinite(tu) & np.isfinite(td)
    gap = tu - td
    mu, md, mg = np.median(tu[fin]), np.median(td[fin]), np.median(gap[fin])
    sc = np.abs(tu / mu - 1) + np.abs(td / md - 1) + np.abs(gap / mg - 1)
    ok = fin & (np.abs(tu / mu - 1) < 0.15) & (np.abs(td / md - 1) < 0.20) & (np.abs(gap / mg - 1) < 0.15)
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(sc[cand])])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    q = {k: float(v[i]) for k, v in p.items()}
    q["z_up"] = float(z_arrival(d1, "up")[0])
    q["z_down"] = float(z_arrival(d1, "down")[0])
    hs = {}
    chk = {}
    for mode in ("up", "down"):
        tf, _, Hh, dz = simulate(d1, mode, hist=True)
        hs[mode] = (np.array([h[0] for h in Hh]), np.array([h[1] for h in Hh]))   # 秒、(時刻, 層)
        chk[mode] = float(tf[0]) / 60.0
    _SAMPLE = dict(i=i, p=q, t_up=float(tu[i]), t_down=float(td[i]), gap=float(gap[i]), h=hs, chk=chk, med=(mu, md, mg))
    return _SAMPLE


def layers_at(mode, minutes):
    """見本の、その時刻の全層の温度（下から上）"""
    ts, T = sample()["h"][mode]
    sec = minutes * 60.0
    j = int(np.clip(np.searchsorted(ts, sec) - 1, 0, len(ts) - 2))
    f = float(np.clip((sec - ts[j]) / (ts[j + 1] - ts[j]), 0, 1))
    return T[j] * (1 - f) + T[j + 1] * f


def temp_at(mode, minutes, z):
    """見本の、その時刻・高さ z(m) の温度"""
    q = sample()["p"]
    dz = q["H"] / N_LAY
    L = layers_at(mode, minutes)
    return float(np.interp(z, (np.arange(N_LAY) + 0.5) * dz, L))


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    q = s["p"]
    print("見本", s["i"], "広さ", round(q["tat"], 1), "畳 天井", round(q["H"], 2), "m 外", round(q["Tout"], 1), "室温", round(q["T0"], 1), "設定", round(q["Tset"], 1),
          "風量", round(q["G"] * 60, 1), "上向きの入る高さ", round(q["z_up"], 2), "下向き", round(q["z_down"], 2), "| 上向き", hm_(s["t_up"]), "下向き", hm_(s["t_down"]),
          "差", round(s["gap"], 1), "分")
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
note.DATE = "10.29"                                # 日付欄（公開予定日）

COL_U, INK_U = "#c3aeea", "#6a4aa8"                # 上向き（むらさき。温度の色と混ざらない色）
COL_D, INK_D = "#86d3a1", "#2b7d4a"                # 下向き（みどり）
COL_T = "#cfc8b4"                                  # 同時
KEY_LABEL = {"up": "上向き", "same": "ほぼ同じ", "down": "下向き"}
NAME = {"up": "上向き", "down": "下向き"}
COLS = {"up": COL_U, "down": COL_D}
INKC = {"up": INK_U, "down": INK_D}

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["上向き", "ほぼ同じ", "下向き"]
TAG = {"up": "A", "down": "C"}
CORRECT = 2                                        # answer_by_rule の結果の位置

BIG_Q = ["エアコン暖房、風向きは上？下？", "足もとが早く暖まるのは？"]                    # 定位置（上）の2行
BIG_Q3 = ["エアコン暖房、", "風向きは上？下？", "足もとが早く暖まるのは？"]               # 1コマ目の3行（同じ大きさ）
DETAIL = "冬の朝・同じ部屋ふたつ"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 15.5                                    # T_GO から2部屋とも暖まるまで
R0 = 0.35                                          # 冒頭の進み（シミュの分／動画の秒）。答えが見えないよう、ほとんど進めない

# 画面の置き場所
PN = {"up": dict(x0=80.0, x1=520.0, cx=300.0), "down": dict(x0=580.0, x1=1020.0, cx=800.0)}
PY0, PY1 = 800.0, 1600.0                           # パネル（画面の下まで）
YC, YF = 900.0, 1440.0                             # 天井・床の y（文字は 1450 まで）
UNIT_X0, UNIT_X1 = 12.0, 176.0                     # エアコン（パネルの左端から）


def kpx():
    return (YF - YC) / sample()["p"]["H"]


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_TWB, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_up"], s["t_down"]))
    T_FIN2 = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 80, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
        return ts, np.cumsum(sp) / 200

    lo, hi = 0.5, 80.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN2, ts, tau)) > fins[1]:
            hi = mid
        else:
            lo = mid
    RX = hi
    ts, tau = build(RX)
    TL = dict(t=ts, tau=tau)
    T_FIN1 = float(np.interp(fins[0], tau, ts))
    T_G0 = T_FIN2 + 1.7
    T_G1 = T_G0 + 2.9
    T_REV = T_G1 + 2.6
    T_ANS2 = T_REV + 1.7
    T_TW = T_ANS2 + 4.4                            # ひねり
    T_TWB = T_TW + 2.6                             # ひねりの棒
    T_Q = T_TWB + 5.0
    DURATION = T_Q + 4.0


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


# ---------- 色 ----------
STOPS = [(8.0, "#6f9fd6"), (13.0, "#a9c9ea"), (17.0, "#eef1e6"), (20.0, "#f9dca6"), (23.0, "#f5ae72"), (27.0, "#ea7a50")]
_STOP_RGB = [(v, hexrgb(c)[:3]) for v, c in STOPS]


def tcol(T):
    """温度 → 色（寒い青 → 暖かい赤）。2つの部屋で同じ尺度"""
    if T <= _STOP_RGB[0][0]:
        return _STOP_RGB[0][1]
    for (a, ca), (b, cb) in zip(_STOP_RGB[:-1], _STOP_RGB[1:]):
        if T <= b:
            u = (T - a) / (b - a)
            return tuple(ca[i] * (1 - u) + cb[i] * u for i in range(3))
    return _STOP_RGB[-1][1]


def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def clip_panel(ctx, k):
    pn = PN[k]
    core.rrect(ctx, pn["x0"], PY0, pn["x1"] - pn["x0"], PY1 - PY0, 22)
    ctx.clip()


def border_panel(ctx, k):
    pn = PN[k]
    core.rrect(ctx, pn["x0"], PY0, pn["x1"] - pn["x0"], PY1 - PY0, 22)
    _stroke(ctx, 3.5, INK, 0.75)


ZOOM0, ZOOM_T = 1.40, 1.25


def zoom_art(ctx, t, ax, ay):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）。(ax, ay) はエアコンの近く（最初から見えるように）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(ax, ay)
    ctx.scale(z, z)
    ctx.translate(-ax, -ay)


# ---------- 絵: 人 ----------

def draw_person(ctx, cx, yf, h, shirt, warm, t):
    """立っている人（床 yf・背の高さ h px）。warm = 足もとが暖まったか"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    sh = 0.0 if warm else 2.2 * math.sin(t * 38)            # 寒いと ぶるぶる
    ctx.save()
    ctx.translate(cx + sh, 0)
    ctx.scale(0.84, 1.0)                                    # 横ははば 0.84 倍（部屋の幅が狭いので）
    ctx.translate(-cx, 0)
    leg_w, leg_h = 0.115 * h, 0.47 * h
    for sgn in (-1, 1):                                    # 脚と くつ
        x = cx + sgn * 0.085 * h
        ctx.rectangle(x - leg_w / 2, yf - leg_h, leg_w, leg_h - 0.03 * h)
        ctx.set_source_rgba(*hexrgb("#4a5878"))
        ctx.fill_preserve()
        _stroke(ctx, 3.2, INK, 0.9)
        core.rrect(ctx, x - leg_w * 0.62 + sgn * 0.02 * h, yf - 0.04 * h, leg_w * 1.35, 0.04 * h, 6)
        ctx.set_source_rgba(*hexrgb("#3a3330"))
        ctx.fill()
    for sgn in (-1, 1):                                    # 腕（体の横）
        ctx.move_to(cx + sgn * 0.165 * h, yf - 0.80 * h)
        ctx.line_to(cx + sgn * 0.195 * h, yf - 0.50 * h)
        _stroke(ctx, 0.07 * h, shirt, 1.0)
        ctx.arc(cx + sgn * 0.197 * h, yf - 0.47 * h, 0.032 * h, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f6dcc6"))
        ctx.fill_preserve()
        _stroke(ctx, 2.8, INK, 0.9)
    core.rrect(ctx, cx - 0.155 * h, yf - 0.83 * h, 0.31 * h, 0.40 * h, 16)   # 体
    ctx.set_source_rgba(*hexrgb(shirt))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    ctx.arc(cx, yf - 0.895 * h, 0.077 * h, 0, 2 * math.pi)  # 頭（顔の高さ ≒ 1.5m）
    ctx.set_source_rgba(*hexrgb("#f6dcc6"))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    ctx.arc(cx, yf - 0.915 * h, 0.082 * h, math.pi * 1.04, math.pi * 1.96)    # かみ
    ctx.set_source_rgba(*hexrgb("#3a2f2a"))
    ctx.fill()
    for sgn in (-1, 1):                                    # 目
        ctx.arc(cx + sgn * 0.03 * h, yf - 0.895 * h, 0.0085 * h, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
    if warm:                                               # 口: にっこり / 寒いと へ
        ctx.arc(cx, yf - 0.89 * h, 0.032 * h, 0.15 * math.pi, 0.85 * math.pi)
    else:
        ctx.move_to(cx - 0.026 * h, yf - 0.867 * h)
        ctx.line_to(cx + 0.026 * h, yf - 0.867 * h)
    _stroke(ctx, 2.8, INK, 0.9)
    ctx.restore()


# ---------- 絵: 部屋 ----------

def draw_ac(ctx, x0, mode, k_):
    ux0, ux1 = x0 + UNIT_X0, x0 + UNIT_X1
    uy0, uy1 = YC + 0.05 * k_, YC + 0.34 * k_
    core.rrect(ctx, ux0, uy0, ux1 - ux0, uy1 - uy0, 12)
    ctx.set_source_rgba(*hexrgb("#fbfbf8"))
    ctx.fill_preserve()
    _stroke(ctx, 3.6, INK, 0.95)
    ctx.move_to(ux0 + 16, uy0 + 0.09 * k_)                 # 吸い込み口
    ctx.line_to(ux1 - 16, uy0 + 0.09 * k_)
    _stroke(ctx, 2.2, INK, 0.7)
    ctx.set_source_rgba(*hexrgb("#47c27a"))
    ctx.arc(ux1 - 20, uy0 + 17, 5.5, 0, 2 * math.pi)
    ctx.fill()
    th = sample()["p"]["th_up" if mode == "up" else "th_dn"]
    ox, oy = x0 + 118.0, uy1 - 4                           # 吹き出し口と風向きの板（羽）
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for (w_, col) in ((8, INK), (3.6, "#e9edf0")):
        ctx.move_to(ox - 20, oy)
        ctx.line_to(ox - 20 + 52 * math.cos(th), oy + 52 * math.sin(th))
        _stroke(ctx, w_, col, 0.95)


def jet_path(mode):
    """温風の通り道（絵の点列）。見本の入る高さ z_arr と角度から決める。(x, y) の配列"""
    s = sample()
    q = s["p"]
    k_ = kpx()
    x1 = PN[mode]["x1"]
    x0 = PN[mode]["x0"]
    th = q["th_up" if mode == "up" else "th_dn"]
    xo, yo = x0 + 118.0 + 30 * math.cos(th), YC + 0.34 * k_ + 26 * math.sin(th)
    ya = YF - q["z_up" if mode == "up" else "z_down"] * k_
    if th > 0.25:
        xa = xo + (ya - yo) / math.tan(th)
    else:
        xa = x1 - 190
    xa = float(np.clip(xa, xo + 40, x1 - 190))
    xe = x1 - 150
    ye = max(YC + 24, ya - 22)
    pts = []
    for u in np.linspace(0, 1, 30):
        pts.append((xo + (xa - xo) * u, yo + (ya - yo) * (u ** 0.85 if th > 0.25 else u * u * (3 - 2 * u))))
    for u in np.linspace(0, 1, 20)[1:]:
        pts.append((xa + (xe - xa) * u, ya + (ye - ya) * (u * u)))
    return np.array(pts)


_JP = {}


def jet_cache(mode):
    if mode not in _JP:
        P = jet_path(mode)
        seg = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
        _JP[mode] = (P, np.concatenate([[0], np.cumsum(seg)]))
    return _JP[mode]


def pt_on(mode, s):
    P, L = jet_cache(mode)
    s = min(max(s, 0.0), 1.0) * L[-1]
    return float(np.interp(s, L, P[:, 0])), float(np.interp(s, L, P[:, 1]))


def pt_off(mode, s_, off):
    """通り道の上の点から、横へ off px ずらした点（流れを太い帯に見せる）"""
    x, y = pt_on(mode, s_)
    xa, ya = pt_on(mode, s_ - 0.01)
    xb, yb = pt_on(mode, s_ + 0.01)
    dx, dy = xb - xa, yb - ya
    n_ = math.hypot(dx, dy) or 1.0
    return x - dy / n_ * off, y + dx / n_ * off


def draw_jet(ctx, t, mode):
    """温風の流れ。真ん中は太い矢（矢じりつき）、そのまわりに細い筋が流れる。0秒目から流れている"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    lanes = (-48.0, -32.0, -16.0, 0.0, 16.0, 32.0, 48.0)
    for lane, off in enumerate(lanes):
        main = off == 0.0
        n = 8 if main else 6
        for i in range(n):
            ph = (t * (0.55 if main else 0.62) + (i + 0.41 * lane) / n) % 1.0
            a0 = ph
            a1 = min(1.0, ph + (0.06 if main else 0.05))
            al = math.sin(math.pi * ph) ** 0.5 * (1.0 if main else 0.8)
            pts = [pt_off(mode, a0 + (a1 - a0) * j / 5, off * (0.3 + 0.7 * ph)) for j in range(6)]
            for (col, w, aa) in (("#ffffff", 20 if main else 12, 0.6), ("#e8572a", 14 if main else 7, 0.95 if main else 0.85)):
                ctx.move_to(*pts[0])
                for p_ in pts[1:]:
                    ctx.line_to(*p_)
                ctx.set_source_rgba(*hexrgb(col, aa * al))
                ctx.set_line_width(w)
                ctx.stroke()
            if main:
                hx, hy = pts[-1]
                gx, gy = pts[-2]
                ang = math.atan2(hy - gy, hx - gx)
                ctx.move_to(hx + 20 * math.cos(ang), hy + 20 * math.sin(ang))
                ctx.line_to(hx + 17 * math.cos(ang + 2.4), hy + 17 * math.sin(ang + 2.4))
                ctx.line_to(hx + 17 * math.cos(ang - 2.4), hy + 17 * math.sin(ang - 2.4))
                ctx.close_path()
                ctx.set_source_rgba(*hexrgb("#e8572a", 0.95 * al))
                ctx.fill()


def draw_room(ctx, t, mode, minutes):
    s = sample()
    q = s["p"]
    k_ = kpx()
    pn = PN[mode]
    x0, x1 = pn["x0"], pn["x1"]
    ctx.save()
    clip_panel(ctx, mode)
    fill(ctx, hexrgb("#e9e2d2"))                                       # 外の壁（見出しの帯）
    ctx.rectangle(x0 - 10, PY0, x1 - x0 + 20, PY1 - PY0)
    ctx.fill()
    ctx.rectangle(x0 + 8, YC - 14, x1 - x0 - 16, 14)                   # 天井
    ctx.set_source_rgba(*hexrgb("#c9bfa9"))
    ctx.fill()
    ctx.save()
    ctx.rectangle(x0 - 10, YC, x1 - x0 + 20, PY1 - YC + 20)            # 絵は部屋と床の中だけで動かす（見出しにはみ出さない）
    ctx.clip()
    zoom_art(ctx, t, x0 + 120.0, YC + 130.0)
    dz = q["H"] / N_LAY
    L = layers_at(mode, minutes)
    zc = (np.arange(N_LAY) + 0.5) * dz
    y = YC
    while y < YF - 0.1:                                                # 部屋の空気（高さごとの温度の色）
        y1 = min(YF, y + 6.0)
        z = (YF - (y + y1) / 2) / k_
        ctx.rectangle(x0 + 8, y, x1 - x0 - 16, y1 - y + 0.6)
        ctx.set_source_rgba(*tcol(float(np.interp(z, zc, L))), 1)
        ctx.fill()
        y = y1
    # 床
    ctx.rectangle(x0 - 10, YF, x1 - x0 + 20, PY1 - YF + 20)
    ctx.set_source_rgba(*hexrgb("#d9b98a"))
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#b8946a", 0.7))
    ctx.set_line_width(2.5)
    for i in range(0, 9):
        ctx.move_to(x0 + i * 62 - 10, YF)
        ctx.line_to(x0 + i * 62 - 60, PY1 + 10)
    ctx.stroke()
    ctx.rectangle(x0 + 8, YF - 9, x1 - x0 - 16, 9)
    ctx.set_source_rgba(*hexrgb("#f7f1e6"))
    ctx.fill()
    # 窓（右の壁）
    wx0, wy0, ww, wh = x1 - 104, YF - 2.05 * k_, 80, 1.15 * k_
    ctx.rectangle(wx0, wy0, ww, wh)
    ctx.set_source_rgba(*hexrgb("#bfe0f2"))
    ctx.fill()
    ctx.rectangle(wx0, wy0, ww, wh)
    _stroke(ctx, 5, INK, 0.85)
    ctx.move_to(wx0 + ww / 2, wy0)
    ctx.line_to(wx0 + ww / 2, wy0 + wh)
    ctx.move_to(wx0, wy0 + wh / 2)
    ctx.line_to(wx0 + ww, wy0 + wh / 2)
    _stroke(ctx, 3.5, INK, 0.8)
    # エアコン・温風・人
    draw_jet(ctx, t, mode)
    draw_ac(ctx, x0, mode, k_)
    warm = temp_at(mode, minutes, 0.1) >= T_FOOT
    draw_person(ctx, x1 - 82, YF - 2, 1.65 * k_, COLS[mode], warm, t)
    # 室内の枠
    ctx.rectangle(x0 + 8, YC, x1 - x0 - 16, YF - YC)
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.restore()
    ctx.restore()
    border_panel(ctx, mode)


def draw_header(ctx, t, mode):
    pn = PN[mode]
    cx = pn["cx"]
    xd, yd = cx - 100, PY0 + 34
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 24, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 24, 24, INKC[mode], seed=13 + (mode == "down"), width=3.4)
    text(ctx, TAG[mode], xd, yd, 32, INKC[mode])
    text(ctx, NAME[mode], cx - 62, yd, 42, INKC[mode], align="left")
    q = sample()["p"]
    text(ctx, f"室温{q['T0']:.0f}℃ → 設定{q['Tset']:.0f}℃", cx, PY0 + 68, 28, INK, bold=False)


def draw_cards(ctx, t, mode, minutes, done_t, t_fin):
    """顔の高さと足もとの温度のカード（人のとなり）。足もとが18℃に届いたら「届いた！」と時間"""
    pn = PN[mode]
    x1 = pn["x1"]
    k_ = kpx()
    cx = x1 - 238
    yf_face = YF - 1.5 * k_
    yf_foot = YF - 56
    for (yy, lab, z) in ((yf_face, "顔の高さ", 1.5), (yf_foot, "足もと", 0.1)):
        done = (z < 1.0) and done_t is not None
        h = 112 if done else 92
        ctx.set_source_rgba(*hexrgb(INK, 0.55))
        ctx.set_line_width(2.5)
        ctx.set_dash([6, 7])
        ctx.move_to(cx + 80, yy)
        ctx.line_to(x1 - 82 - 62, yy)
        ctx.stroke()
        ctx.set_dash([])
        ctx.arc(x1 - 82 - 62, yy, 7, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(RED, 0.95))
        ctx.fill()
        core.rrect(ctx, cx - 80, yy - h / 2, 160, h, 16)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.95))
        ctx.fill_preserve()
        _stroke(ctx, 2.5, PENCIL, 0.8)
        if done:
            text(ctx, "届いた！", cx, yy - 28, 34, RED)
            text(ctx, hm_(t_fin), cx, yy + 22, 44, INKC[mode])
            note.pen_circle(ctx, cx, yy + 22, 58, 30, RED, seed=70 + (mode == "down"), width=4.5, progress=clamp01((t - done_t) / 0.35))
        else:
            text(ctx, lab, cx, yy - 22, 28, PENCIL, bold=False)
            text(ctx, f"{temp_at(mode, minutes, z):.1f}℃", cx, yy + 16, 42, INKC[mode] if z < 1 else INK)


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = tau_of(t)
    ctx.push_group()
    for mode in ("up", "down"):
        draw_room(ctx, t, mode, tau)
    for mode in ("up", "down"):
        tf = s["t_" + mode]
        done_t = t_of(tf) if tau >= tf else None
        draw_cards(ctx, t, mode, tau, done_t, tf)
        draw_header(ctx, t, mode)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, f"経過 {hm_(tau_of(t))}", 580, 640, 40, "yellow", a=a, tilt=-0.02)
    fade = 1 - ease((t - (T_GO + 4.5)) / 0.4)                       # はじめの数秒は「例の1回」の字幕
    if fade > 0:
        text(ctx, "たとえば、この1回では（上向きも届いた回）", 580, 724, 30, INK, bold=False, alpha=a * fade)
    if fade < 1:
        text(ctx, "早送り（足もとが18℃で「届いた」）", 580, 724, 26, PENCIL, bold=False, alpha=a * (1 - fade))


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}


def first_code():
    """1回ごと: 0 = 下向きが先に届いた、1 = 上向きが先、2 = 同時（どちらも届かなかった）"""
    r = results()
    return np.where(r["t_down"] < r["t_up"], 0, np.where(r["t_up"] < r["t_down"], 1, 2))


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    code = first_code()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_D), bgra(COL_U), bgra(COL_T)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[code[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def fit_size(lines, size, maxw):
    """文字の大きさ。いちばん長い行が maxw に収まるまで小さくする"""
    w = max(core.text_width(l, size) for l in lines)
    return size * min(1.0, maxw / w)


def sticky_fit(ctx, s, x, y, size, color, fg=INK, a=1.0, tilt=-0.02, maxw=700.0):
    """付せん。文字は 画面の右のボタン列（x>930）に入らないよう、中心 x から maxw/2 までに収める"""
    sz = fit_size(s.split("\n"), size, maxw)
    return note.sticky(ctx, s, x, y, sz, color, fg=fg, a=a, tilt=tilt)


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
    text(ctx, f"{fmt(n)} / 10,000回　1マス＝1回", 580, 616, 32, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    code = first_code()[:m]
    cnt = {"down": int((code == 0).sum()), "up": int((code == 1).sum()), "tie": int((code == 2).sum())}
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        rows = sorted(("up", "down"), key=lambda k: TAG[k])
        items = [(k, COLS[k], f"{TAG[k]} {NAME[k]}が先に届いた", cnt[k]) for k in rows]
        if sh["n_tie"] > 0:
            items.append(("tie", COL_T, "同時（どちらも届かず）", cnt["tie"]))
        for i, (k, col, lab, c) in enumerate(items):
            y = 1192 + i * 52
            fill(ctx, hexrgb(col, a * lg))
            ctx.rectangle(200, y - 17, 34, 34)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(200, y - 17, 34, 34)
            ctx.stroke()
            text(ctx, lab, 250, y, 34, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(c)}回", 915, y, 34, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            sticky_fit(ctx, cap_text(), 580, 1370 if sh["n_tie"] > 0 else 1352, 32, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_down"], sh["gap_med"])


def censored_up(sh):
    """上向きの半分以上が 90分で打ち切り（届かなかった）か"""
    return sh["n_unfin_up"] >= 0.5 * N_TRIAL


def cap_text():
    """1万回のマス目の下の付せん: 下向きが先の割合と、時間の差（打ち切りの回は 90分として数えているので「以上」）"""
    sh = shown()
    p = sh["p_down"]
    lead = "下向き" if p >= 0.5 else "上向き"
    q = p if p >= 0.5 else 1 - p
    ptxt = "ほぼ100%" if q >= 0.995 else f"約{pct_i(q)}"
    g = abs(sh["gap_med"])
    gtxt = f"{int(g // 10 * 10)}分以上" if sh["n_unfin_up"] >= 0.25 * N_TRIAL else f"約{g:.0f}分"
    return f"{lead}が先は {ptxt}。\n差は 真ん中で {gtxt}"


def reason_text():
    """答えの理由（数字）。時間は 足もとが 18℃に届くまでの、1万回の真ん中の値"""
    sh = shown()
    key = answer_key()
    md = f"{sh['med_down']:.0f}分"
    fr = sh["n_unfin_up"] / N_TRIAL
    if sh["n_unfin_up"] >= 0.25 * N_TRIAL:
        frs = "約半分" if 0.45 <= fr <= 0.55 else f"約{int(round(fr * 100))}%"
        up = f"この部屋の置き方なら、上向きは\n{frs}の回で 90分たっても届かない"
    else:
        up = f"上向きは {sh['med_up']:.0f}分"
    if key == "down":
        return f"足もとが18℃に届くまで 真ん中で 下向き{md}。\n{up}"
    return f"足もとが18℃に届くまで 真ん中で 下向き{md}・上向き{sh['med_up']:.0f}分"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    head = "やっぱり、下向きが正解。" if key == "down" else f"残念、{KEY_LABEL[key]}が正解。"
    sticky_fit(ctx, head, 580, 1218, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        sticky_fit(ctx, reason_text(), 580, 1368, 30, "blue", a=c, tilt=0.012)


# ---------- ひねり: 15分たったら顔の高さは？ ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease_out((t - T_TW) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TWB + 0.3 + 2 * 0.45 + 0.5


def twist_text():
    d = shown()["face_gap_med"]                    # 下向き − 上向き（℃）
    if abs(d) < 0.3:
        return f"顔の高さは ほとんど同じ。\n差は 約{abs(d):.1f}℃"
    if d > 0:
        return f"顔の高さも 下向きのほうが 暖かい。\n差は 真ん中で 約{d:.1f}℃"
    return f"顔の高さは 上向きのほうが 暖かい。\n差は 真ん中で 約{-d:.1f}℃"


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    if t < T_TWB:
        ba = ease_out((t - T_TW) / 0.25) * a * (1 - ease((t - T_TWB + 0.25) / 0.25))
        note.banner(ctx, "では、15分たったら\n顔の高さは？", 560, 900, a=ba, t_rel=t - T_TW, size=56)
        return
    text(ctx, "15分たったときの 顔の高さ（1.5m）", 580, 660, 38, INK, alpha=a)
    text(ctx, "1万回の 真ん中の値", 580, 718, 30, PENCIL, bold=False, alpha=a)
    x0, ln, v0, v1 = 230.0, 430.0, 10.0, 24.0
    rows = [("上向き", sh["face15_up"], COL_U, "up"), ("下向き", sh["face15_down"], COL_D, "down")]
    rows.sort(key=lambda z: TAG[z[3]])
    for i, (lab, v, col, k) in enumerate(rows):
        y = 900 + i * 190
        tk = T_TWB + 0.3 + i * 0.45
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0, y - 66, 40, INKC[k], align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 34, ln, 68)
        ctx.stroke()
        w_ = ln * clamp01((v - v0) / (v1 - v0)) * g
        if w_ > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - 34, w_, 68, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, f"{v:.1f}℃", x0 + ln + 16, y, 46, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    text(ctx, "10℃", x0, 1235, 26, PENCIL, bold=False, alpha=a)
    text(ctx, "24℃", x0 + ln, 1235, 26, PENCIL, bold=False, alpha=a)
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        sticky_fit(ctx, twist_text(), 580, 1345, 42, "pink", fg=RED, a=b, tilt=-0.02)


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


def big_sizes(max_w):
    s1 = 100.0 * max_w / core.text_width(BIG_Q[0], 100.0)
    s2 = min(100.0 * max_w / core.text_width(BIG_Q[1], 100.0), s1 * 1.6)
    return s1, s2


def big3_size(max_w=860.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


CD_X, CD_Y = 580.0, 1135.0


class KIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（同じ大きさ・横幅いっぱい）・前提・三択（横1列）。その下に2つの部屋（0秒目から温風が流れている）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = big3_size(820.0)
        ys = (440, 530, 620)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.07 * (1 - ease_out(t / 0.7))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q3[2], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, ys[2] + sz * 0.62, 565 + w2 / 2 + 6, ys[2] + sz * 0.59, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, 706, 30, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 757
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
        s1, s2 = big_sizes(850.0)
        sz = min(s1, 47.0)
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 456, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 488, 540 + w2 / 2 + 6, 485, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 540
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840)):
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


INTRO = KIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_clock(ctx, t)
    fo = 1 - ease((t - T_TW + 0.1) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたのエアコン、\nいま風向きはどっち？", 580, 860, 54, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 580, 1050, 36, INK, bold=False, alpha=r)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def noise_band(dur, k, seed, amp=1.0):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(int(SR * dur))
    lo = np.convolve(n, np.ones(k) / k, mode="same")
    return lo * amp


def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    air = noise_band(t_end, 90, 4, 1.0)                    # 温風の ふぉー
    tt = np.arange(len(air)) / SR
    env_ = (0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, air * env_, 0.5)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    tg, te = t_of(s["t_down"]), t_of(s["t_up"])
    mx.add(tg, bell(784.0, 1.2), 0.45)
    mx.add(te, bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.8), 0.4)                         # ひねり
    for i in range(2):
        mx.add(T_TWB + 0.3 + i * 0.45, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    checks = []
    # (1) 熱の保存: 外へ逃げる熱・すきま風を 0 にした閉じた部屋で、出した熱 = 空気とかたまりが増えた熱（最大の食い違い・割合）
    k = 40
    d1 = {kk: v[:k] for kk, v in p.items()}
    for mode in ("up", "down"):
        _, sn, _, dz = simulate(d1, mode, snaps=(1e9,), tmax=1200.0, closed=True)
        T_end, Tm_end = sn["end"]
        V = d1["A"] * d1["H"] / N_LAY
        dE_air = (RHOCP * V[None, :] * (T_end - d1["T0"][None, :])).sum(0)
        dE_m = (d1["cm"] * d1["A"] / N_LAY * (Tm_end - d1["T0"][None, :])).sum(0)
        err = np.max(np.abs(dE_air + dE_m - sn["Pint"]) / sn["Pint"])
        checks.append((f"熱の保存（{NAME[mode]}・閉じた部屋）最大の食い違い（割合）", float(err), 0.0, 1e-9))
    # (2) 上向きの60分後の（天井近く−足もと）の温度差の真ん中の値が、調べられた値（数℃〜約9℃）の幅に入る
    checks.append(("上向き60分後の 天井近く−足もと の真ん中の値（℃）が 3〜9", float(3.0 <= sh["dT60_up"] <= 9.0), 1.0, 0.0))
    # (3) 見本は1万回の中の1回。1回ずつ計算した時刻が、1万回の中のその回と同じ
    s = sample()
    checks.append(("見本の上向きの時刻（分）が1万回の値と同じ", s["chk"]["up"], s["t_up"], 1e-6))
    checks.append(("見本の下向きの時刻（分）が1万回の値と同じ", s["chk"]["down"], s["t_down"], 1e-6))
    # (4) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ。正解の記号は A にしない（10/28 の正解が A）
    key = answer_by_rule(sh["p_down"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（上向き・下向き）",
                   float(LABELS.index(NAME["up"]) * 10 + LABELS.index(NAME["down"])),
                   float("ABC".index(TAG["up"]) * 10 + "ABC".index(TAG["down"])), 0.0))
    checks.append(("正解の記号が A ではない", float(INTRO.correct != 0), 1.0, 0.0))
    # (5) 画面の回数が足して1万
    checks.append(("先に届いた回の合計（同時を含む）", float(sh["n_down"] + sh["n_up"] + sh["n_tie"]), float(N_TRIAL), 0.0))
    # (6) 見本の差が真ん中の値の近く
    checks.append(("見本の差（分）が（届いた回の）真ん中の値の近く", s["gap"], s["med"][2], 0.15 * abs(s["med"][2])))
    # (7) 下向きが90分で届かなかった回は 1%未満（打ち切りの影響は主に上向き）
    checks.append(("下向きが90分で届かなかった回の割合が 1%未満", float(sh["n_unfin_down"] / N_TRIAL < 0.01), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  届く {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（上向き {hm_(s['t_up'])} / 下向き {hm_(s['t_down'])}）")
    print("  上:", cap_text().replace("\n", " / "), "|", reason_text().replace("\n", " / "), "|", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.2, 5.8, 8.0, 10.0, T_FIN1 + 0.4, T_FIN2 - 0.6, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 0.8, T_TWB + 2.6, T_TWB + 3.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, sorted(ts), OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
