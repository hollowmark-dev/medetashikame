"""焼き芋、レンジとじっくり焼く、どっちが甘い？ 同じさつまいも2本で1万回。— 2026-10-19 作成（公開予定 10/23）

しくみ（甘さのもと＝麦芽糖）
  さつまいもの β-アミラーゼは、生のデンプンには働けない。加熱で糊化したデンプンを麦芽糖に切る。
  ただし酵素は熱で壊れる（失活）。だから「糊化した・まだ酵素が生きている」温度にいる時間だけ、麦芽糖ができる。

モデル（いもを長い円柱とみなし、半径方向1次元の熱伝導。中心から皮まで20層）
  大きさ    : 重さ 200〜350g、半径 2.2〜3.0cm（一様）。長さは 重さ÷(πR²×密度)（先の細りは入れない）
  熱の性質  : 比熱 3.70〜3.78 kJ/kgK（Fasina ほか 2003 のピューレ 5〜80℃）、
              熱伝導率 20℃で 0.50〜0.60 W/mK（同論文が引く Stewart の生のいも 0.54）。温度による伸びは Fasina の式(4)の比で
              （80℃で約1.5倍。ピューレでは 0.52〜0.78）。密度 1,000〜1,100 kg/m³（仮定）
  100℃より上がらない: 100℃を超えたぶんの熱は水が蒸発して出ていくとする（各層を100℃で止める）
  じっくり焼く: オーブン 160〜200℃（ウェザーニュースの家庭のやり方 160℃・Allan ほか 2023 は 188℃）、
              予定 60〜100分（Allan ほか 60〜75分・ウェザーニュース 中くらいの芋 90〜100分）。
              表面へ 対流 6〜18 W/m²K（家庭のオーブン。Isleroglu & Kaymak-Ertekin 2016 は 17〜18）＋放射（放射率 0.1〜0.9。
              アルミホイルで包む〜皮のまま）
  レンジ    : 出力 500〜700W、いもが吸うのは その 50〜75%（仮定。小さい物ほど吸う割合が下がる Houšová & Hoke 2002）。
              予定 4〜5分×(重さ÷200g)×(600W÷出力)（約200gで600W 4〜5分の目安）。濡らした紙とラップで包む（表面の逃げ 5〜10 W/m²K）。
              熱のでき方: 皮から入って弱まる（電力の浸透深さ Dp は Fasina ほかの誘電率の式(7)(8)から 2450MHz・50℃で計算 ≒ 0.94cm）。
              q(r) ∝ exp(−(R−r)/Dp) + exp(−(R+r)/Dp)（向かい側から入った分も足す）
  できあがり: 予定の時間で 芯が85℃以上（竹串が通る）。届かなければ レンジは30秒ずつ・オーブンは5分ずつ足す。そのあと3分おいて食べる
              （室温 20〜25℃、表面 8 W/m²K）
  はじめの温度: 10〜25℃

  酵素（1層ごと）
  糊化      : g = これまでの最高温度での シグモイド((T − Tp) / 2℃)。Tp は 64〜73℃（Nakamura ほか 2014・2018 のでんぷんの
              糊化開始温度。紅あずま・紅はるか 64.4〜73.2℃。農家の説明「65℃以上で糊化」とも合う）
  失活      : 生きている酵素 E は dE/dt = −kd(T)·E。80℃での半減期 1〜5分、温度の効き Ed 250〜350 kJ/mol（仮定）。
              → 70℃で半減期 約10〜160分、75℃で 約3〜30分、85℃で 約10〜90秒。
              資料の「75℃以上で働きが悪くなる」「75〜85℃を超えると止まる」「紅あずまは80℃でひどく落ちる（Nakamura 2018）」に合わせた幅
  切る速さ  : 糊化したデンプンを、生きた酵素が k·a(T)·E·g の速さで切る。a(T) は 60℃を1とした温度の効き（Q10 = 2、仮定）。
              切れるのは デンプンの 57.5〜60%まで（β-アミラーゼは枝分かれの手前で止まる。Zhang 1999: アミロース15.6%・
              分解の限界 アミロース98%・アミロペクチン50% → でんぷん全体で57.5%。上は 蒸し芋で切れた割合 51±8%（Nakamura 2018）の上の方）
  k の決め方: 1回ごとに、同じ酵素で「ふつうの芋（半径2.6cm）を40分蒸す（表面は100℃の湯気）」と、デンプンの 41〜51% が
              麦芽糖になるよう合わせる（Nakamura ほか 2017/2018 の蒸し芋: 中くらいの品種 41%・多い品種 51%）。
              ＝ 酵素の量は 蒸し芋の実測に合わせ、レンジとオーブンの差は熱の入り方だけから出る
  デンプン  : 生の重さの 18〜23%（Nakamura 2014 の表）。麦芽糖 = 切れたデンプン × 342/324

問い: 「焼き芋、レンジとじっくり焼く、/ どっちが甘い？」 A レンジ ／ B ほぼ同じ ／ C じっくり焼く
      （2026-10-19 計算のあと、前後の回と正解の記号が続かないよう並びだけ入れ替えた。規則と計算は変えていない）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1回ごとに、同じ芋（同じ大きさ・同じ酵素）の 麦芽糖の量を くらべる。
      じっくり ≥ レンジ×1.2 の回が 60%以上なら A、レンジ ≥ じっくり×1.2 の回が 60%以上なら C、それ以外は B。
ひねり: 「レンジでも、弱で10分なら？」 出力200W（いもが吸うのは同じ割合）で10分。芯が85℃に届かなければ30秒ずつ足す。
締め: 「あなたは、レンジ派？じっくり派？」（答えは出さない）

結果（SEED_MAIN、2026-10-19）: 麦芽糖の真ん中 じっくり 10.1 / レンジ 3.9 g/100g、じっくり÷レンジ 真ん中 2.6倍（10〜90% 2.1〜3.3）。
      1万回すべてで じっくり ≥ レンジ×1.2 → A。種を変えても（11〜13、各2,000回）100%・2.6倍で A。
      ひねり（弱200Wで10分）: 6.7 g/100g。ふつうのレンジの 1.7倍、じっくりはその 1.5倍（97%の回で1.2倍以上）。
      65〜75℃にいた時間（芋ぜんたいの平均・真ん中）: じっくり 4.6分 / レンジ 0.4分 / 弱 1.4分。

乱数の種は見本（並べた2本）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "yakiimo-amasa"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
NR = 20                                           # 半径方向の層の数
DT = 1.0                                          # 秒
MASS = (0.200, 0.350)                             # kg
RAD = (0.022, 0.030)                              # m
RHO = (1000.0, 1100.0)                            # kg/m³（仮定）
CP = (3700.0, 3780.0)                             # J/kgK（Fasina 2003）
K20 = (0.50, 0.60)                                # W/mK、20℃（Stewart の 0.54 の前後）
T0 = (10.0, 25.0)                                 # はじめの温度
T_ROOM = (20.0, 25.0)
OVEN_T = (160.0, 200.0)
OVEN_MIN = (60.0, 100.0)
H_OVEN = (6.0, 18.0)                              # 対流 W/m²K
EMIS = (0.1, 0.9)                                 # 放射率（ホイル〜皮のまま）
MW_P = (500.0, 700.0)                             # W（表示の出力）
MW_ETA = (0.50, 0.75)                             # いもが吸う割合（仮定）
MW_MIN200 = (4.0, 5.0)                            # 200g・600W あたりの分
H_WRAP = (5.0, 10.0)                              # 包んだ表面の逃げ
LOW_P, LOW_MIN = 200.0, 10.0                      # ひねり: 弱で10分
DONE_T = 85.0                                     # 芯がこれ以上で できあがり
REST_S = 180.0                                    # 食べるまで3分
H_REST = 8.0
TP = (64.0, 73.0)                                 # 糊化の温度（Nakamura）
G_W = 2.0                                         # 糊化のなだらかさ（℃）
THALF80 = (60.0, 300.0)                           # 80℃での酵素の半減期（秒）
ED = (250e3, 350e3)                               # J/mol
Q10 = 2.0
LIMIT = (0.575, 0.60)                             # 切れる上限（デンプンに対する割合。Zhang 1999 から 57.5%、蒸し芋の実測の上の方 約60%）
X_REF = (0.41, 0.51)                              # 蒸し芋で切れた割合（Nakamura）
STEAM_R, STEAM_MIN, STEAM_H = 0.026, 40.0, 200.0  # 合わせに使う蒸し芋
STARCH = (0.18, 0.23)
MALT_PER_STARCH = 342.3 / 324.3
F_MW = 2.45e9
SIGMA = 5.670e-8
RGAS = 8.314

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_X, RULE_SHARE = 1.2, 0.60


def answer_by_rule(m_slow, m_mw):
    """m_slow, m_mw = 1回ごとの麦芽糖の量（じっくり焼く・レンジ）。A=0 レンジ / B=1 ほぼ同じ / C=2 じっくり（並びは計算のあとに入れ替え）"""
    m_slow, m_mw = np.asarray(m_slow), np.asarray(m_mw)
    if np.mean(m_slow >= RULE_X * m_mw) >= RULE_SHARE:
        return 2
    if np.mean(m_mw >= RULE_X * m_slow) >= RULE_SHARE:
        return 0
    return 1


# ---------- 物の値 ----------

def k_factor(T):
    """熱伝導率の温度による伸び（Fasina 2003 式(4) を 20℃で1にした比）"""
    f = lambda x: 0.544 - 3.29e-3 * x + 7.70e-5 * x * x   # noqa: E731
    return f(T) / f(20.0)


def penetration_depth(T=50.0, f_hz=F_MW):
    """電力の浸透深さ（m）。Fasina 2003 の誘電率の式(7)(8)（f は MHz）と式(9)"""
    f = f_hz / 1e6
    e1 = 74.84 - 0.113 * T - 0.00214 * f
    e2 = 29.76 + 0.125 * T - 0.0144 * f - 8.60e-5 * f * T + 4.11e-6 * f * f + 7.64e-4 * T * T
    lam = 2.998e8 / f_hz
    return lam / (2 * math.pi * math.sqrt(2 * e1)) * (math.sqrt(1 + (e2 / e1) ** 2) - 1) ** -0.5


DP = penetration_depth()


def draw_params(rng, n):
    u = lambda lo_hi: rng.uniform(lo_hi[0], lo_hi[1], n)   # noqa: E731
    p = dict(m=u(MASS), R=u(RAD), rho=u(RHO), cp=u(CP), k20=u(K20), T0=u(T0), Troom=u(T_ROOM),
             Tov=u(OVEN_T), ov_min=u(OVEN_MIN), hov=u(H_OVEN), eps=u(EMIS),
             P=u(MW_P), eta=u(MW_ETA), mw200=u(MW_MIN200), hwrap=u(H_WRAP),
             Tp=u(TP), th80=u(THALF80), Ed=u(ED), lim=u(LIMIT), xref=u(X_REF), starch=u(STARCH))
    p["L"] = p["m"] / (math.pi * p["R"] ** 2 * p["rho"])
    p["mw_min"] = p["mw200"] * (p["m"] / 0.2) * (600.0 / p["P"])
    return p


def a_rate(T):
    return Q10 ** ((T - 60.0) / 10.0)


def kd(T, th80, Ed):
    return math.log(2) / th80 * np.exp(Ed / RGAS * (1 / 353.15 - 1 / (T + 273.15)))


def sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))


class Potato:
    """n 本のいもを同時に計算する。T[n, NR]（中心→皮）"""

    def __init__(self, p, R=None):
        self.p = p
        n = len(p["m"])
        self.n = n
        self.R = p["R"] if R is None else np.full(n, R)
        dr = self.R / NR
        self.dr = dr
        i = np.arange(NR)
        self.r = (i[None, :] + 0.5) * dr[:, None]                     # 層の中心
        self.rf = (i[None, :] + 1.0) * dr[:, None]                    # 外側の面
        self.vol = math.pi * (2 * i[None, :] + 1) * dr[:, None] ** 2  # 長さ1mあたりの体積
        self.w = self.vol / self.vol.sum(1, keepdims=True)            # 平均をとる重み
        self.C = p["rho"][:, None] * p["cp"][:, None] * self.vol      # 熱容量（J/K/m）
        self.T = np.repeat(p["T0"][:, None], NR, 1).astype(float)
        self.E = np.ones((n, NR))
        self.G = np.zeros((n, NR))
        self.J = np.zeros((n, NR))
        self.win = np.zeros(n)                                        # 芯が 65〜75℃にいた時間（表示用）
        self.winv = np.zeros(n)                                       # 芋全体で平均した 65〜75℃にいた時間（表示用）
        shape = np.exp(-(self.R[:, None] - self.r) / DP) + np.exp(-(self.R[:, None] + self.r) / DP)
        self.qshape = shape / (shape * self.w).sum(1, keepdims=True)  # 平均1

    def step(self, dt, T_env, h, eps=None, P_abs=None):
        """dt 秒すすめる。T_env, h, eps, P_abs は (n,) の配列（0 なら無し）"""
        p, T = self.p, self.T
        k = p["k20"][:, None] * k_factor(T)
        kf = 2 * k[:, :-1] * k[:, 1:] / (k[:, :-1] + k[:, 1:])
        g = kf * 2 * math.pi * self.rf[:, :-1] / self.dr[:, None]
        flow = g * (T[:, 1:] - T[:, :-1])                              # 内側の層へ入る熱（W/m）
        Q = np.zeros_like(T)
        Q[:, :-1] += flow
        Q[:, 1:] -= flow
        Ts = T[:, -1]
        hh = h.copy()
        if eps is not None:
            Ta, Tb = T_env + 273.15, Ts + 273.15
            hh = hh + eps * SIGMA * (Ta * Ta + Tb * Tb) * (Ta + Tb)
        U = 1.0 / (1.0 / np.maximum(hh, 1e-9) + 0.5 * self.dr / k[:, -1])
        Q[:, -1] += U * 2 * math.pi * self.R * (T_env - Ts)
        if P_abs is not None:
            q_mean = P_abs / self.p["L"] / (math.pi * self.R ** 2)    # W/m³
            Q += q_mean[:, None] * self.qshape * self.vol
        T += Q * dt / self.C
        np.minimum(T, 100.0, out=T)                                    # 100℃を超えたぶんは蒸発
        self.enzyme(dt)

    def enzyme(self, dt):
        p, T = self.p, self.T
        np.maximum(self.G, sig((T - p["Tp"][:, None]) / G_W), out=self.G)
        self.J += a_rate(T) * self.E * self.G * dt
        self.E *= np.exp(-kd(T, p["th80"][:, None], p["Ed"][:, None]) * dt)
        c = T[:, 0]
        self.win += ((c >= 65.0) & (c <= 75.0)) * dt
        self.winv += (((T >= 65.0) & (T <= 75.0)) * self.w).sum(1) * dt

    def maltose(self, kcat):
        """麦芽糖（生の重さに対する割合）"""
        p = self.p
        X = p["lim"][:, None] * (1 - np.exp(-kcat[:, None] * self.J))
        return p["starch"] * MALT_PER_STARCH * (X * self.w).sum(1)

    def conv(self, kcat):
        X = self.p["lim"][:, None] * (1 - np.exp(-kcat[:, None] * self.J))
        return (X * self.w).sum(1)


def cook(p, method, record=None, rec_dt=5.0):
    """method: 'oven' / 'mw' / 'low' / 'steam'。返り値: Potato（J まで入った状態）と 加熱の終わり・食べる時刻（秒）"""
    n = len(p["m"])
    pot = Potato(p, R=STEAM_R if method == "steam" else None)
    if method == "oven":
        plan, check = p["ov_min"] * 60, 300.0
    elif method == "mw":
        plan, check = p["mw_min"] * 60, 30.0
    elif method == "low":
        plan, check = np.full(n, LOW_MIN * 60), 30.0
    else:
        plan, check = np.full(n, STEAM_MIN * 60), 1e9
    plan = np.round(plan)
    heating = np.ones(n, bool)
    t_end = np.full(n, np.nan)
    t = 0.0
    zeros = np.zeros(n)
    while True:
        # できあがりの判定（予定の時間を過ぎて、check 秒ごと）
        due = heating & (t >= plan - 1e-9) & (((t - plan) % check) < DT * 0.5)
        if method == "steam":
            due = heating & (t >= plan - 1e-9)
            done = due
        else:
            done = due & (pot.T[:, 0] >= DONE_T)
        t_end[done] = t
        heating &= ~done
        resting = ~heating & (t < t_end + REST_S)
        if not heating.any() and not resting.any():
            break
        if method == "oven":
            T_env = np.where(heating, p["Tov"], p["Troom"])
            h = np.where(heating, p["hov"], H_REST)
            eps = np.where(heating, p["eps"], 0.0)
            P_abs = None
        elif method in ("mw", "low"):
            P = p["P"] if method == "mw" else np.full(n, LOW_P)
            T_env = np.where(heating, 25.0, p["Troom"])
            h = np.where(heating, p["hwrap"], H_REST)
            eps = None
            P_abs = np.where(heating, P * p["eta"], 0.0)
        else:
            T_env = np.where(heating, 100.0, p["Troom"])
            h = np.where(heating, STEAM_H, H_REST)
            eps, P_abs = None, None
        active = heating | resting
        if record is not None and abs(t / rec_dt - round(t / rec_dt)) < 1e-6:
            record.append((t, pot.T[0].copy(), pot.J[0].copy(), pot.E[0].copy(), pot.G[0].copy(), bool(heating[0])))
        idle = ~active
        if idle.any():
            keep = [a[idle].copy() for a in (pot.T, pot.J, pot.E, pot.G, pot.win, pot.winv)]
        pot.step(DT, T_env, h, eps, P_abs)
        # 食べ終わった（休ませ終わった）芋は止める
        if idle.any():
            pot.T[idle], pot.J[idle], pot.E[idle], pot.G[idle], pot.win[idle], pot.winv[idle] = keep
        t += DT
    return pot, t_end


def solve_kcat(pot_ref, p):
    """蒸し芋の切れた割合が xref になる k（1回ごと）。切れる割合は k について単調に増えるので二分法"""
    lo = np.full(len(p["m"]), 1e-8)
    hi = np.full(len(p["m"]), 1.0)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        x = pot_ref.conv(mid)
        big = x > p["xref"]
        hi = np.where(big, mid, hi)
        lo = np.where(big, lo, mid)
    return np.sqrt(lo * hi)


def run(seed, n=N_TRIAL):
    rng = np.random.default_rng(seed)
    p = draw_params(rng, n)
    out = dict(p)
    ref, _ = cook(p, "steam")
    kcat = solve_kcat(ref, p)
    out["kcat"] = kcat
    out["x_steam"] = ref.conv(kcat)
    for m in ("oven", "mw", "low"):
        pot, t_end = cook(p, m)
        out[f"malt_{m}"] = pot.maltose(kcat) * 100          # g / 100g
        out[f"t_{m}"] = t_end
        out[f"win_{m}"] = pot.win
        out[f"winv_{m}"] = pot.winv
    return out


SEED_MAIN = 20261023
_RES = {}


def results():
    if not _RES:
        cache = OUT / "cache" / f"model_{SEED_MAIN}_v3.npz"
        if cache.exists():
            _RES["m"] = dict(np.load(cache))
        else:
            r = run(SEED_MAIN)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **r)
            _RES["m"] = r
    return _RES["m"]


def shown():
    r = results()
    mo, mm, ml = r["malt_oven"], r["malt_mw"], r["malt_low"]
    ratio = mo / mm
    return dict(p_A=float(np.mean(mo >= RULE_X * mm)), p_C=float(np.mean(mm >= RULE_X * mo)),
                n_A=int(np.sum(mo >= RULE_X * mm)), n_C=int(np.sum(mm >= RULE_X * mo)),
                ratio_med=float(np.median(ratio)), ratio_q=np.percentile(ratio, [10, 25, 75, 90]),
                med_oven=float(np.median(mo)), med_mw=float(np.median(mm)), med_low=float(np.median(ml)),
                win_oven=float(np.median(r["win_oven"])) / 60, win_mw=float(np.median(r["win_mw"])) / 60,
                win_low=float(np.median(r["win_low"])) / 60,
                winv_oven=float(np.median(r["winv_oven"])) / 60, winv_mw=float(np.median(r["winv_mw"])) / 60,
                winv_low=float(np.median(r["winv_low"])) / 60,
                low_vs_oven_A=float(np.mean(mo >= RULE_X * ml)), low_vs_oven_C=float(np.mean(ml >= RULE_X * mo)),
                low_vs_mw=float(np.median(ml / mm)), oven_vs_low=float(np.median(mo / ml)),
                t_oven=float(np.median(r["t_oven"])) / 60, t_mw=float(np.median(r["t_mw"])) / 60,
                t_low=float(np.median(r["t_low"])) / 60,
                ext_oven=float(np.mean(r["t_oven"] > r["ov_min"] * 60 + 1)),
                ext_mw=float(np.mean(r["t_mw"] > r["mw_min"] * 60 + 1)),
                ext_low=float(np.mean(r["t_low"] > LOW_MIN * 60 + 1)))


def report():
    sh = shown()
    r = results()
    print(f"浸透深さ Dp = {DP * 100:.2f} cm")
    print(f"麦芽糖（g/100g・真ん中）: じっくり {sh['med_oven']:.2f} / レンジ {sh['med_mw']:.2f} / 弱10分 {sh['med_low']:.2f}")
    print(f"じっくり÷レンジ 真ん中 {sh['ratio_med']:.2f}  10/25/75/90% {np.round(sh['ratio_q'], 2)}")
    print(f"じっくりが1.2倍以上 {sh['p_A']:.4f}（{sh['n_A']}回）  レンジが1.2倍以上 {sh['p_C']:.4f}（{sh['n_C']}回）")
    print(f"  答え {'ABC'[answer_by_rule(r['malt_oven'], r['malt_mw'])]}")
    print(f"芯が65〜75℃にいた時間（真ん中・分）: じっくり {sh['win_oven']:.1f} / レンジ {sh['win_mw']:.2f} / 弱 {sh['win_low']:.1f}")
    print(f"加熱の時間（真ん中・分）: じっくり {sh['t_oven']:.0f} / レンジ {sh['t_mw']:.1f} / 弱 {sh['t_low']:.1f}  "
          f"延長した割合 {sh['ext_oven']:.2f} / {sh['ext_mw']:.2f} / {sh['ext_low']:.2f}")
    print(f"ひねり: 弱10分÷レンジ 真ん中 {sh['low_vs_mw']:.2f}  じっくり÷弱 真ん中 {sh['oven_vs_low']:.2f}  "
          f"じっくりが弱の1.2倍以上 {sh['low_vs_oven_A']:.3f}  弱がじっくりの1.2倍以上 {sh['low_vs_oven_C']:.3f}  "
          f"規則で {'ABC'[answer_by_rule(r['malt_oven'], r['malt_low'])]}")
    print(f"芋全体の平均で65〜75℃にいた時間（真ん中・分）: じっくり {sh['winv_oven']:.1f} / レンジ {sh['winv_mw']:.2f} / "
          f"弱 {sh['winv_low']:.1f}")
    print(f"蒸し芋の切れた割合 {np.percentile(r['x_steam'], [0, 50, 100]).round(3)}")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並べた2本）を選ぶ
# =====================================================================
_SAMPLE = None


def pick_params(seed, i):
    """1万回のうち i 回目の値（run と同じ乱数の順で引いて、i 番目だけ取り出す）"""
    rng = np.random.default_rng(seed)
    p = draw_params(rng, N_TRIAL)
    return {k: v[i:i + 1].copy() for k, v in p.items()}


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: じっくり÷レンジ が真ん中の値の ±0.1、芋は半径 2.5〜2.7cm・重さ 230〜290g、オーブンの予定 70〜85分・
    レンジは予定どおりで延長なし。その中で、はじめの温度が真ん中に近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    sh = shown()
    ratio = r["malt_oven"] / r["malt_mw"]
    cand = np.nonzero((np.abs(ratio - sh["ratio_med"]) < 0.1) & (r["R"] > 0.025) & (r["R"] < 0.027)
                      & (r["m"] > 0.23) & (r["m"] < 0.29) & (r["ov_min"] > 70) & (r["ov_min"] < 85)
                      & (np.abs(r["t_mw"] - np.round(r["mw_min"] * 60)) < 0.5))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    sc = np.abs(r["T0"][cand] - 17.5) / 7.5 + np.abs(ratio[cand] - sh["ratio_med"]) / 0.1
    i = int(cand[np.argmin(sc)])
    cache = OUT / "cache" / f"sample_{SEED_MAIN}_{i}.npz"
    p = pick_params(SEED_MAIN, i)
    if cache.exists():
        d = dict(np.load(cache))
    else:
        d = {}
        ref, _ = cook(p, "steam")
        kc = solve_kcat(ref, p)
        d["kcat"] = kc
        for m in ("oven", "mw", "low"):
            rec = []
            pot, t_end = cook(p, m, record=rec)
            d[f"t_{m}"] = np.array([x[0] for x in rec])
            d[f"T_{m}"] = np.array([x[1] for x in rec])
            d[f"J_{m}"] = np.array([x[2] for x in rec])
            d[f"E_{m}"] = np.array([x[3] for x in rec])
            d[f"G_{m}"] = np.array([x[4] for x in rec])
            d[f"heat_{m}"] = np.array([x[5] for x in rec])
            d[f"end_{m}"] = t_end
            d[f"malt_{m}"] = pot.maltose(kc) * 100
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez(cache, **d)
    pot0 = Potato(p)
    w = pot0.w[0]
    s = dict(i=i, p=p, w=w, d=d)
    kc = float(d["kcat"][0])
    for m in ("oven", "mw", "low"):
        X = p["lim"][0] * (1 - np.exp(-kc * d[f"J_{m}"]))
        s[f"M_{m}"] = p["starch"][0] * MALT_PER_STARCH * (X * w).sum(1) * 100       # 時刻ごとの 麦芽糖 g/100g
        inwin = ((d[f"T_{m}"] >= 65) & (d[f"T_{m}"] <= 75)) * w
        s[f"W_{m}"] = np.concatenate([[0.0], np.cumsum(inwin.sum(1)[:-1] * np.diff(d[f"t_{m}"]))]) / 60  # 分
        s[f"done_{m}"] = float(d[f"end_{m}"][0])
        s[f"eat_{m}"] = float(d[f"end_{m}"][0]) + REST_S
    _SAMPLE = s
    return s


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    p = s["p"]
    print("見本", s["i"], "重さ", round(float(p["m"][0]) * 1000), "g 半径", round(float(p["R"][0]) * 100, 2), "cm",
          "オーブン", round(float(p["Tov"][0])), "℃", round(float(p["ov_min"][0])), "分 レンジ", round(float(p["P"][0])), "W",
          round(float(p["mw_min"][0]), 1), "分  はじめ", round(float(p["T0"][0]), 1), "℃")
    for m in ("oven", "mw", "low"):
        print(m, "できあがり", round(s[f"done_{m}"] / 60, 1), "分  麦芽糖", round(float(s[f"M_{m}"][-1]), 2),
              "（1万回の値", round(float(results()[f"malt_{m}"][s["i"]]), 2), "）  65〜75℃", round(float(s[f"W_{m}"][-1]), 1), "分")
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
note.DATE = "10.23"                               # 日付欄（公開予定日）

COL_A, INK_A = "#f4ad6a", "#b8601a"               # A じっくり焼く（橙）
COL_C, INK_C = "#8fbbe8", "#2f63a8"               # C レンジ（青）
COL_B = "#cfc8b8"                                 # B ほぼ同じ
COL_L = "#c3a8e6"                                 # 弱で10分（ひねり）
SKIN = "#9b4f8c"                                  # 皮（紫）
METAL = "#e8e4da"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
SEG1, SEG2 = 4.0, 6.0                             # レンジが食べごろになるまで / じっくりが食べごろになるまで（動画の秒）
BIG_Q = ["焼き芋、レンジとじっくり焼く、", "どっちが甘い？"]
DETAIL = "同じ芋を2本。オーブンで約1時間／レンジで数分"
LABELS = ["レンジ", "ほぼ同じ", "じっくり焼く"]
CORRECT = 2                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
COLX = {"oven": 370.0, "mw": 790.0}
TAG = {"oven": "C", "mw": "A"}
NAME = {"oven": "じっくり焼く", "mw": "レンジ"}
COL = {"oven": COL_A, "mw": COL_C}
INKC = {"oven": INK_A, "mw": INK_C}


def setup():
    global TL, T_FIN1, T_FIN2, T_RACE_END, T_G0, T_G1, T_REV, T_WHY, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    tau1, tau2 = s["eat_mw"], s["eat_oven"]
    ts = np.arange(0, 120, 1 / 120)

    def build(s1, s2):
        sp = np.ones_like(ts)
        k1 = (ts >= T_GO) & (ts < T_GO + SEG1)
        sp[k1] = 1.0 + (s1 - 1.0) * np.array([ease((t - T_GO) / 0.8) for t in ts[k1]])
        k2 = ts >= T_GO + SEG1
        sp[k2] = s1 + (s2 - s1) * np.array([ease((t - T_GO - SEG1) / 0.8) for t in ts[k2]])
        return np.concatenate([[0.0], np.cumsum(sp[1:] / 120)])

    def solve(target, t_at, fn):
        lo, hi = 1.0, 5000.0
        for _ in range(40):
            mid = math.sqrt(lo * hi)
            if np.interp(t_at, ts, fn(mid)) > target:
                hi = mid
            else:
                lo = mid
        return math.sqrt(lo * hi)

    s1 = solve(tau1, T_GO + SEG1, lambda x: build(x, x))
    s2 = solve(tau2, T_GO + SEG1 + SEG2, lambda x: build(s1, x))
    TL = dict(t=ts, tau=build(s1, s2), s1=s1, s2=s2)
    T_FIN1 = t_of(tau1)
    T_FIN2 = t_of(tau2)
    T_RACE_END = T_FIN2 + 2.4
    T_G0 = T_RACE_END
    T_G1 = T_G0 + 2.4
    T_REV = T_G1 + 0.8
    T_WHY = T_REV + 3.4
    T_TW = T_WHY + 4.2
    T_TW_RUN = T_TW + 2.2
    T_Q = T_TW_RUN + 5.6
    DURATION = T_Q + 4.2


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


def speed_now(t):
    return (tau_of(t + 0.02) - tau_of(t - 0.02)) / 0.04 if t > 0.03 else 1.0


def state(m, tau):
    """見本の芋の、実際の時刻 τ（秒）での様子。食べごろを過ぎたら止める"""
    s = sample()
    d = s["d"]
    tt = d[f"t_{m}"]
    tau = min(tau, s[f"eat_{m}"])
    j = int(np.clip(np.searchsorted(tt, tau) - 1, 0, len(tt) - 2))
    f = clamp01((tau - tt[j]) / (tt[j + 1] - tt[j]))
    T = d[f"T_{m}"][j] * (1 - f) + d[f"T_{m}"][j + 1] * f
    rate = (d[f"J_{m}"][j + 1] - d[f"J_{m}"][j]) / max(1e-9, tt[j + 1] - tt[j])
    M = float(np.interp(tau, tt, s[f"M_{m}"]))
    Wm = float(np.interp(tau, tt, s[f"W_{m}"]))
    heat = tau < s[f"done_{m}"]
    return dict(T=T, rate=rate, M=M, W=Wm, heat=heat, eaten=tau >= s[f"eat_{m}"] - 1e-6)


# ---------- 色 ----------
CMAP = [(10, "#4f7fd1"), (35, "#9fd0ee"), (55, "#f6ec9a"), (68, "#f7c25a"), (80, "#ef8a45"), (100, "#cf3b3b")]
CM_STOPS = [(v, hexrgb(c)) for v, c in CMAP]


def tcolor(T):
    if T <= CM_STOPS[0][0]:
        return CM_STOPS[0][1]
    for (v0, c0), (v1, c1) in zip(CM_STOPS, CM_STOPS[1:]):
        if T <= v1:
            f = (T - v0) / (v1 - v0)
            return tuple(c0[i] * (1 - f) + c1[i] * f for i in range(3)) + (1.0,)
    return CM_STOPS[-1][1]


# ---------- 場面（冒頭の台所）。場面の座標: 幅1080・高さ SCENE_H ----------
SCENE_H = 760.0
CX = 580.0
LAY_INTRO = (1.0, 690.0)
ZOOM0, ZOOM_T = 1.32, 1.5
ZOOM_F = (580.0, 330.0)
OV = (115.0, 70.0, 535.0, 520.0)                  # オーブンの外形 x0,y0,x1,y1
OVW = (145.0, 160.0, 425.0, 470.0)                # オーブンの窓
MW = (610.0, 215.0, 1010.0, 520.0)                # レンジの外形
MWW = (635.0, 250.0, 890.0, 485.0)                # レンジの窓
COUNTER = 535.0


def scene_alpha(t):
    if t < T_MOVE:
        return 1.0
    return 1 - ease((t - T_MOVE) / 0.45)


def zoom(t):
    return 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))


def apply_scene(ctx, t):
    sc, y0 = LAY_INTRO
    z = zoom(t)
    fx, fy = ZOOM_F
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)
    ctx.translate(fx * (1 - z), fy * (1 - z))
    ctx.scale(z, z)


def to_dev(t, x, y):
    sc, y0 = LAY_INTRO
    z = zoom(t)
    fx, fy = ZOOM_F
    x2, y2 = fx + (x - fx) * z, fy + (y - fy) * z
    return CX + (x2 - CX) * sc, y0 + y2 * sc


def _stroke(ctx, w=3.0, a=0.95, col=INK):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def potato_side(ctx, cx, cy, L, R, ang=0.0, a=1.0, roast=0.0):
    """横から見たさつまいも（両端が細い）"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang)
    ctx.move_to(-L / 2, 4)
    ctx.curve_to(-L / 2 + L * 0.18, -R * 1.25, L / 2 - L * 0.22, -R * 1.15, L / 2, -2)
    ctx.curve_to(L / 2 - L * 0.2, R * 1.2, -L / 2 + L * 0.2, R * 1.1, -L / 2, 4)
    ctx.close_path()
    c = hexrgb(SKIN)
    k = 1 - 0.25 * roast
    ctx.set_source_rgba(c[0] * k, c[1] * k, c[2] * k, a)
    ctx.fill_preserve()
    _stroke(ctx, 3.0, 0.9 * a)
    ctx.set_source_rgba(1, 1, 1, 0.25 * a)          # つや
    ctx.set_line_width(5)
    ctx.move_to(-L * 0.25, -R * 0.55)
    ctx.curve_to(-L * 0.1, -R * 0.75, L * 0.1, -R * 0.75, L * 0.2, -R * 0.6)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))    # 根の筋
    ctx.set_line_width(2)
    for u in (-0.2, 0.05, 0.28):
        ctx.move_to(L * u, -R * 0.7)
        ctx.curve_to(L * u + 6, -R * 0.2, L * u + 6, R * 0.3, L * u, R * 0.7)
    ctx.stroke()
    ctx.move_to(L / 2, -2)                          # しっぽ
    ctx.line_to(L / 2 + 26, -10)
    _stroke(ctx, 3.0, 0.8 * a)
    ctx.restore()


def steam(ctx, x0, y0, t, n, spread, rise, seed, a=1.0, width=7.0):
    rng = np.random.default_rng(seed)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.45, 0.7)
        xx0 = x0 + (k / max(1, n - 1) - 0.5) * spread
        u = (t * sp + ph) % 1.0
        al = 0.8 * a * math.sin(math.pi * u) ** 0.8
        if al < 0.02:
            continue
        yb = y0 - u * rise
        for col, wd, dx in (((1, 1, 1), width, 0.0), (hexrgb(PENCIL)[:3], 1.5, width / 2)):
            ctx.set_source_rgba(col[0], col[1], col[2], al if wd > 2 else 0.4 * al)
            ctx.set_line_width(wd)
            for i in range(14):
                v = i / 13
                yy = yb - v * 80
                xx = xx0 + 12 * math.sin((yy + t * 90) / 60 + k) * (0.3 + v) + dx
                (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
            ctx.stroke()


def draw_oven(ctx, t):
    x0, y0, x1, y1 = OV
    core.rrect(ctx, x0, y0, x1 - x0, y1 - y0, 22)    # 本体
    fill(ctx, METAL)
    ctx.fill_preserve()
    _stroke(ctx, 4)
    wx0, wy0, wx1, wy1 = OVW
    glow = 0.55 + 0.25 * math.sin(2 * math.pi * 0.9 * t) + 0.1 * math.sin(2 * math.pi * 2.3 * t)
    core.rrect(ctx, wx0, wy0, wx1 - wx0, wy1 - wy0, 14)
    g = cairo.LinearGradient(0, wy0, 0, wy1)
    g.add_color_stop_rgba(0, 0.99, 0.62, 0.25, 0.55 + 0.35 * glow)
    g.add_color_stop_rgba(0.5, 0.98, 0.83, 0.45, 0.35 + 0.3 * glow)
    g.add_color_stop_rgba(1, 0.99, 0.55, 0.22, 0.55 + 0.35 * glow)
    ctx.set_source(g)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    for yy, ph in ((wy0 + 26, 0.0), (wy1 - 26, 1.3)):    # 上下のヒーター（赤く光る）
        ctx.move_to(wx0 + 18, yy)
        for i in range(12):
            ctx.line_to(wx0 + 18 + (i + 0.5) * (wx1 - wx0 - 36) / 12, yy + (9 if i % 2 == 0 else -9))
        ctx.line_to(wx1 - 18, yy)
        a = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * t + ph))
        ctx.set_source_rgba(0.85, 0.15, 0.1, a)
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.move_to(wx0 + 14, wy1 - 70)                   # 網
    ctx.line_to(wx1 - 14, wy1 - 70)
    _stroke(ctx, 2.5, 0.7)
    potato_side(ctx, (wx0 + wx1) / 2, wy1 - 98, 200, 34, -0.04, roast=0.3)
    for k in range(4):                                # ゆらゆら（熱）
        xx = wx0 + 50 + k * 60
        ph = t * 1.6 + k * 0.7
        ctx.move_to(xx, wy1 - 150)
        for i in range(10):
            ctx.line_to(xx + 6 * math.sin(ph * 3 + i * 0.9), wy1 - 150 - i * 8)
        _stroke(ctx, 2.5, 0.35, "#b8401a")
    core.rrect(ctx, wx1 + 22, wy0, x1 - wx1 - 44, wy1 - wy0, 10)   # つまみの板
    fill(ctx, "#d9d3c5")
    ctx.fill_preserve()
    _stroke(ctx, 2.5)
    for k, yy in enumerate((wy0 + 60, wy0 + 160)):
        cxk = (wx1 + x1) / 2
        ctx.arc(cxk, yy, 26, 0, 2 * math.pi)
        fill(ctx, (1, 1, 1, 0.95))
        ctx.fill_preserve()
        _stroke(ctx, 3)
        ang = -0.6 + 0.12 * k + (0.05 * math.sin(t * 2) if k == 1 else 0)
        ctx.move_to(cxk, yy)
        ctx.line_to(cxk + 20 * math.cos(ang - math.pi / 2), yy + 20 * math.sin(ang - math.pi / 2))
        _stroke(ctx, 4)
    lamp = 0.5 + 0.5 * math.sin(2 * math.pi * 1.5 * t)
    ctx.arc((wx1 + x1) / 2, wy0 + 245, 9, 0, 2 * math.pi)
    ctx.set_source_rgba(0.95, 0.3, 0.15, 0.4 + 0.6 * lamp)
    ctx.fill()
    ctx.move_to(wx0 + 20, y0 + 40)                    # 取っ手
    ctx.line_to(wx1 - 20, y0 + 40)
    _stroke(ctx, 9, 0.85, "#9a927f")
    for fx in (x0 + 40, x1 - 40):                     # 足
        ctx.rectangle(fx - 14, y1, 28, COUNTER - y1)
        fill(ctx, "#9a927f")
        ctx.fill()


def draw_micro(ctx, t):
    x0, y0, x1, y1 = MW
    core.rrect(ctx, x0, y0, x1 - x0, y1 - y0, 20)
    fill(ctx, "#f2efe6")
    ctx.fill_preserve()
    _stroke(ctx, 4)
    wx0, wy0, wx1, wy1 = MWW
    core.rrect(ctx, wx0, wy0, wx1 - wx0, wy1 - wy0, 12)
    light = 0.85 + 0.1 * math.sin(2 * math.pi * 3.0 * t)
    ctx.set_source_rgba(1.0, 0.93, 0.6, light)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    ctx.save()                                        # 窓の中
    core.rrect(ctx, wx0, wy0, wx1 - wx0, wy1 - wy0, 12)
    ctx.clip()
    pcx, pcy = (wx0 + wx1) / 2, wy1 - 52
    ang = 2 * math.pi * t / 6.0                       # ターンテーブル（6秒で1周）
    ctx.save()
    ctx.translate(pcx, pcy)
    ctx.scale(1, 0.28)
    ctx.arc(0, 0, 112, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.fill_preserve()
    _stroke(ctx, 3, 0.8)
    for k in range(6):                                # 皿の目印（回って見える）
        a = ang + k * math.pi / 3
        ctx.save()
        ctx.translate(pcx + 96 * math.cos(a), pcy + 27 * math.sin(a))
        ctx.arc(0, 0, 4, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 if math.sin(a) > 0 else 0.2))
        ctx.fill()
    L = 200 * (0.55 + 0.45 * abs(math.cos(ang)))      # 回ると短く見える
    potato_side(ctx, pcx, pcy - 22, L, 32, 0.0)
    for k in range(3):                                # 電波（波線）
        ph = (t * 1.2 + k / 3) % 1.0
        yy = wy0 + 30 + ph * 80
        ctx.move_to(wx0 + 20, yy)
        for i in range(30):
            ctx.line_to(wx0 + 20 + i * (wx1 - wx0 - 40) / 29, yy + 7 * math.sin(i * 1.2 + t * 8))
        _stroke(ctx, 3, 0.5 * math.sin(math.pi * ph), "#7a5cc4")
    ctx.restore()
    core.rrect(ctx, wx1 + 16, wy0, x1 - wx1 - 34, wy1 - wy0, 10)   # 操作パネル
    fill(ctx, "#e2ddd0")
    ctx.fill_preserve()
    _stroke(ctx, 2.5)
    px = (wx1 + 16 + x1 - 18) / 2
    core.rrect(ctx, px - 30, wy0 + 18, 60, 34, 6)     # 表示（数字は出さない）
    fill(ctx, "#2f3a33")
    ctx.fill()
    for i in range(3):
        on = int(t * 2) % 3 == i
        ctx.rectangle(px - 20 + i * 15, wy0 + 30, 9, 10)
        ctx.set_source_rgba(0.5, 1.0, 0.6, 0.9 if on else 0.3)
        ctx.fill()
    for k in range(3):
        core.rrect(ctx, px - 26, wy0 + 80 + k * 46, 52, 30, 8)
        fill(ctx, (1, 1, 1, 0.95))
        ctx.fill_preserve()
        _stroke(ctx, 2.2)
    ctx.move_to(wx0 + 10, y1 - 14)
    ctx.line_to(wx1 - 10, y1 - 14)
    _stroke(ctx, 2, 0.4)


def draw_kitchen(ctx, t):
    fill(ctx, hexrgb("#efe6d2", 0.85))               # 壁のタイル（うすく）
    ctx.rectangle(100, -40, 980, COUNTER + 40)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.18))
    ctx.set_line_width(1.5)
    for yy in range(-30, int(COUNTER), 60):
        ctx.move_to(100, yy)
        ctx.line_to(1080, yy)
    ctx.stroke()
    fill(ctx, hexrgb("#d9b98f"))                      # 調理台
    ctx.rectangle(100, COUNTER, 980, 26)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    fill(ctx, hexrgb("#f3ead8"))                      # 戸棚
    ctx.rectangle(110, COUNTER + 26, 950, SCENE_H - COUNTER - 26)
    ctx.fill_preserve()
    _stroke(ctx, 3)
    for xa in (110, 427, 744):
        ctx.rectangle(xa + 18, COUNTER + 46, 280, SCENE_H - COUNTER - 60)
        _stroke(ctx, 2.2, 0.6)
        ctx.move_to(xa + 150, COUNTER + 70)
        ctx.line_to(xa + 185, COUNTER + 70)
        _stroke(ctx, 6, 0.6, "#9a927f")


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    ctx.push_group()
    ctx.save()
    ctx.rectangle(0, 680, W, 1450 - 680 + 10)
    ctx.clip()
    ctx.save()
    apply_scene(ctx, t)
    draw_kitchen(ctx, t)
    draw_oven(ctx, t)
    draw_micro(ctx, t)
    ctx.restore()
    ctx.restore()
    la = ease_out((t - 1.0) / 0.4)                    # 寄りから引ききったころに、どっちがどっちかを書く
    for k, (x, y) in (("oven", ((OV[0] + OV[2]) / 2, OV[1] - 34)), ("mw", ((MW[0] + MW[2]) / 2, MW[1] - 40))):
        if la > 0:
            note.hand_text(ctx, f"{TAG[k]} {NAME[k]}", x, LAY_INTRO[1] + y, 38, INKC[k], seed=90 + len(k),
                           align="center", alpha=la)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- シミュの画面: 断面・読み取り ----------
DISK_Y, DISK_R = 815.0, 118.0


def race_alpha(t):
    if T_GO - 0.25 <= t < T_G0:
        return ease_out((t - T_GO + 0.25) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


_SPARK = np.random.default_rng(11).uniform(0, 1, (NR, 6, 2))


def draw_disk(ctx, m, cx, cy, R, st, t, a):
    """断面（同心の輪を温度の色で塗る）。麦芽糖ができている輪には小さな光の粒"""
    T = st["T"]
    ctx.arc(cx, cy, R + 9, 0, 2 * math.pi)            # 皮
    fill(ctx, hexrgb(SKIN, a))
    ctx.fill()
    for i in range(NR - 1, -1, -1):
        ctx.arc(cx, cy, R * (i + 1) / NR, 0, 2 * math.pi)
        c = tcolor(T[i])
        ctx.set_source_rgba(c[0], c[1], c[2], a)
        ctx.fill()
    ctx.arc(cx, cy, R + 9, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3.5)
    ctx.stroke()
    rate = st["rate"]
    ref = 0.02                                        # 光る粒の物差し（a·E·g の 1秒あたり）
    for i in range(NR):
        v = clamp01(rate[i] / ref)
        if v < 0.05 or st["eaten"]:
            continue
        for k in range(6):
            u, ph = _SPARK[i, k]
            ang = 2 * math.pi * (u + 0.03 * t * (1 if k % 2 else -1))
            rr = R * (i + 0.5) / NR
            tw = 0.5 + 0.5 * math.sin(2 * math.pi * (1.7 * t + ph))
            ctx.arc(cx + rr * math.cos(ang), cy + rr * math.sin(ang), 3.2 + 2.0 * tw, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 0.85, a * v * (0.45 + 0.55 * tw))
            ctx.fill()
    if st["heat"]:                                    # 熱の入り方
        if m == "oven":
            for k in range(10):
                ang = 2 * math.pi * k / 10 + 0.2
                ph = (t * 0.9 + k * 0.13) % 1.0
                r0 = R + 48 - 22 * ph
                x0, y0 = cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)
                x1, y1 = cx + (r0 - 22) * math.cos(ang), cy + (r0 - 22) * math.sin(ang)
                al = a * math.sin(math.pi * ph)
                ctx.move_to(x0, y0)
                ctx.line_to(x1, y1)
                _stroke(ctx, 4, 0.9 * al, "#d9532e")
                for s_ in (-1, 1):
                    ctx.move_to(x1, y1)
                    ctx.line_to(x1 + 9 * math.cos(ang + s_ * 0.6), y1 + 9 * math.sin(ang + s_ * 0.6))
                    _stroke(ctx, 4, 0.9 * al, "#d9532e")
        else:
            for k in range(8):
                ang = 2 * math.pi * k / 8
                ph = (t * 1.3 + k * 0.17) % 1.0
                r0 = R + 50 - 30 * ph
                al = a * math.sin(math.pi * ph)
                ctx.save()
                ctx.translate(cx, cy)
                ctx.rotate(ang)
                ctx.move_to(r0, -14)
                for j in range(9):
                    ctx.line_to(r0 + 7 * math.sin(j * 1.4 + t * 9), -14 + j * 3.5)
                ctx.restore()
                _stroke(ctx, 3, 0.85 * al, "#7a5cc4")


def draw_colorbar(ctx, a):
    x0, x1, y = 330.0, 830.0, 985.0
    n = 90
    for i in range(n):
        T = 10 + 90 * (i + 0.5) / n
        c = tcolor(T)
        ctx.rectangle(x0 + (x1 - x0) * i / n, y - 13, (x1 - x0) / n + 0.6, 26)
        ctx.set_source_rgba(c[0], c[1], c[2], a)
        ctx.fill()
    ctx.rectangle(x0, y - 13, x1 - x0, 26)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2)
    ctx.stroke()
    text(ctx, "10℃", x0 - 12, y, 26, PENCIL, align="right", bold=False, alpha=a)
    text(ctx, "100℃", x1 + 12, y, 26, PENCIL, align="left", bold=False, alpha=a)
    xa, xb = x0 + (x1 - x0) * (65 - 10) / 90, x0 + (x1 - x0) * (75 - 10) / 90
    ctx.rectangle(xa, y - 17, xb - xa, 34)
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.set_line_width(4)
    ctx.stroke()
    text(ctx, "甘くなる 65〜75℃", (xa + xb) / 2, y + 40, 28, RED, alpha=a)


def meter(ctx, x, y, w, h, val, vmax, col, a):
    ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
    ctx.set_line_width(2.5)
    core.rrect(ctx, x, y - h / 2, w, h, 6)
    ctx.stroke()
    ww = (w - 6) * clamp01(val / vmax)
    if ww > 1:
        fill(ctx, hexrgb(col, 0.95 * a))
        core.rrect(ctx, x + 3, y - h / 2 + 3, ww, h - 6, 4)
        ctx.fill()


M_MAX = 12.0


def mins(sec):
    return f"{int(sec // 60)}分" if sec >= 60 else f"{int(sec)}秒"


def draw_race(ctx, t):
    a = race_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = tau_of(t)
    sp = speed_now(t)
    text(ctx, f"はじめてから {int(tau // 60)}分", 580, 612, 40, INK, alpha=a)
    text(ctx, f"再生 {sp:.0f}倍", 130, 664, 24, PENCIL, bold=False, align="left", alpha=a)
    text(ctx, "断面の温度", 580, 664, 28, PENCIL, bold=False, alpha=a)
    draw_colorbar(ctx, a)
    for m in ("oven", "mw"):
        st = state(m, tau)
        cx = COLX[m]
        draw_disk(ctx, m, cx, DISK_Y, DISK_R, st, t, a)
        y0 = 1080
        text(ctx, f"{TAG[m]} {NAME[m]}", cx, y0, 36, INKC[m], alpha=a)
        if st["heat"]:
            stat = "オーブンで焼いている" if m == "oven" else "レンジで温めている"
            sc = PENCIL
        elif not st["eaten"]:
            stat, sc = "できた。3分おく", INK
        else:
            stat, sc = "食べごろ！", RED
        text(ctx, stat, cx, y0 + 48, 30, sc, bold=sc == RED, alpha=a)
        text(ctx, f"芯 {st['T'][0]:.0f}℃", cx, y0 + 102, 42, INK, alpha=a)
        text(ctx, "甘さ", cx - 160, y0 + 162, 30, INK, alpha=a)
        meter(ctx, cx - 118, y0 + 162, 250, 34, st["M"], M_MAX, COL[m], a)
        text(ctx, f"100gに 麦芽糖 {st['M']:.1f}g", cx, y0 + 214, 30, INK, alpha=a)
        text(ctx, "65〜75℃に いた時間", cx, y0 + 256, 26, PENCIL, bold=False, alpha=a)
        text(ctx, f"{st['W']:.1f}分", cx, y0 + 298, 36, RED if st["eaten"] else INK, alpha=a)
    if t >= T_FIN2:
        b = a * ease_out((t - T_FIN2 - 0.2) / 0.3)
        k = s["M_oven"][-1] / s["M_mw"][-1]
        note.sticky(ctx, f"じっくりのほうが\n麦芽糖が {k:.1f}倍", 580, 815, 46, "yellow", a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def cats():
    r = results()
    mo, mm = r["malt_oven"], r["malt_mw"]
    return np.where(mo >= RULE_X * mm, 0, np.where(mm >= RULE_X * mo, 2, 1))


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    c = cats()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_A), bgra(COL_B), bgra(COL_C)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[c[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_WHY) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
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
    c = cats()[:m]
    rows = (("A レンジが 1.2倍以上 甘い", int((c == 2).sum()), COL_C),
            ("B ほぼ同じ", int((c == 1).sum()), COL_B),
            ("C じっくりが 1.2倍以上 甘い", int((c == 0).sum()), COL_A))
    for i, (lab, cnt, col) in enumerate(rows):
        y = 1160 + i * 52
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(200, y - 16, 32, 32)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(200, y - 16, 32, 32)
        ctx.stroke()
        text(ctx, lab, 248, y, 32, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 32, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回（同じ芋2本）。甘さ＝できた麦芽糖の量", 580, 1322, 26, PENCIL, bold=False, alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"じっくりは 真ん中で 約{sh['ratio_med']:.1f}倍 甘い", 580, 1396, 34, "pink", fg=RED, a=b,
                    tilt=-0.015)


# ---------- 横の棒（同じ目盛り） ----------
BAR_STEP = 0.5


def hbars(ctx, t, t0, rows, ys, a, vmax, unit, x0=270.0, ln=500.0):
    """rows = [(ラベル, 値, 色)]。0 から vmax までの同じ目盛り"""
    for i, ((lab, val, col), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * BAR_STEP
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0, y - 50, 32, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 22, ln, 44)
        ctx.stroke()
        w = ln * clamp01(val / vmax) * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, f"{val:.1f}{unit}", x0 + ln + 14, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


# ---------- なぜ ----------

def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "甘くなる温度（65〜75℃）に いた時間", 580, 650, 38, INK, alpha=a)
    text(ctx, "芋ぜんたいの平均。1万回の真ん中の値", 580, 702, 28, PENCIL, bold=False, alpha=a)
    vmax = max(sh["winv_oven"], sh["winv_mw"]) * 1.1
    rows = [("A レンジ", sh["winv_mw"], COL_C), ("C じっくり焼く", sh["winv_oven"], COL_A)]
    hbars(ctx, t, T_WHY, rows, (850.0, 1000.0), a, vmax, "分")
    tb = T_WHY + 0.3 + 2 * BAR_STEP + 0.5
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, "レンジは 甘くなる温度を\nあっという間に 通りすぎる", 580, 1200, 38, "yellow", a=b, tilt=-0.02)


# ---------- ひねり: 弱で10分なら？ ----------

def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + 3 * BAR_STEP + 0.5


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "100gにできた 麦芽糖（1万回の真ん中）", 580, 650, 38, INK, alpha=a)
    text(ctx, "弱＝200W。芯が85℃になるまで 30秒ずつ足す", 580, 702, 28, PENCIL, bold=False, alpha=a)
    rows = [("A レンジ（ふつう）", sh["med_mw"], COL_C), ("レンジ 弱で10分", sh["med_low"], COL_L),
            ("C じっくり焼く", sh["med_oven"], COL_A)]
    hbars(ctx, t, T_TW_RUN, rows, (840.0, 970.0, 1100.0), a, M_MAX, "g")
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"弱なら ふつうの 約{sh['low_vs_mw']:.1f}倍。\nでも じっくりには 届かない", 580, 1290, 36, "pink",
                    fg=RED, a=b, tilt=-0.02)


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


CD_X, CD_Y = 580.0, 1335.0


class YIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに台所（0秒目からオーブンとレンジが動いている）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 62
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 790:
            sz *= 790 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (410, 484)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 526, 575 + w2 / 2 + 6, 520, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 568, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 820)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 632, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 632, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 632, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.95 * a2))
            core.rrect(ctx, cx - 125, cy - 105, 250, 210, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 105, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 58, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy + 32, 50, 48, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy + 32)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 78, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        sz = 46
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 850:
            sz *= 850 / w
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


INTRO = YIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_race(ctx, t)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "レンジでも、\n弱で10分なら？", 580, 860, a=ba, t_rel=t - T_TW, size=60)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\nレンジ派？じっくり派？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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

def hum(dur, f=120.0, vol=0.5):
    tt = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, tt / 0.2) * np.minimum(1, (dur - tt) / 0.2)
    return (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * 2 * f * tt) + 0.2 * np.sin(2 * np.pi * 3 * f * tt)) \
        * env * vol


def crackle(dur, seed=4):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = np.zeros(n)
    for i in rng.integers(0, max(1, n - 400), int(dur * 9)):
        k = np.arange(300)
        x[i:i + 300] += rng.normal(0, 1, 300) * np.exp(-k / 40) * rng.uniform(0.2, 1.0)
    return x * 0.3


def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    mx.add(0.0, hum(t_of(s["done_mw"])), 0.10)       # レンジのうなり
    mx.add(0.0, crackle(t_of(s["done_oven"])), 0.12)  # オーブンのぱちぱち
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_FIN2 - 1.2, bpm=124, vol=0.32)
    mx.add(t_of(s["done_mw"]), bell(1568.0, 0.9), 0.5)   # チン
    mx.add(t_of(s["done_oven"]), bell(1318.5, 0.9), 0.4)
    mx.add(T_FIN1, blip(880.0, 0.12), 0.3)
    mx.add(T_FIN2, bell(784.0, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(2):                                 # なぜ
        mx.add(T_WHY + 0.3 + i * BAR_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(3):
        mx.add(T_TW_RUN + 0.3 + i * BAR_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    r = results()
    checks = []
    # (1) 熱の出入りがない（表面を断熱）レンジの加熱: たまった熱 = 吸った電力×時間（100℃に届く前）
    rng = np.random.default_rng(3)
    p = draw_params(rng, 50)
    pot = Potato(p)
    E0 = (pot.C * pot.T).sum(1)
    P_abs = np.full(50, 150.0)
    for _ in range(60):
        pot.step(1.0, np.zeros(50), np.zeros(50), None, P_abs)
    gain = ((pot.C * pot.T).sum(1) - E0) * p["L"]
    checks.append(("断熱のレンジ: たまった熱 ÷ 入れた熱（60秒）", float(np.mean(gain / (150.0 * 60))), 1.0, 1e-6))
    # (2) 外から温めると、十分に時間がたてば全体が外の温度にそろう（60℃の湯に3時間）
    pot = Potato(p)
    for _ in range(3 * 3600):
        pot.step(1.0, np.full(50, 60.0), np.full(50, 500.0))
    checks.append(("60℃の湯に3時間: 芯の温度", float(pot.T[:, 0].mean()), 60.0, 0.05))
    # (3) 蒸し芋の合わせ: 切れた割合が狙いどおり
    checks.append(("蒸し芋で切れた割合 − 狙い（最大のずれ）", float(np.max(np.abs(r["x_steam"] - r["xref"]))), 0.0, 1e-4))
    # (4) 浸透深さ（2450MHz・50℃）が 1cm 前後（Fasina ほかの誘電率から）
    checks.append(("電力の浸透深さ（cm）", DP * 100, 0.94, 0.02))
    # (5) 見本は1万回の中の1回で、まとめて計算した値と同じ
    smp = sample()
    i = smp["i"]
    for m in ("oven", "mw", "low"):
        checks.append((f"見本の麦芽糖（{m}）− 1万回の計算", float(smp["d"][f"malt_{m}"][0]), float(r[f"malt_{m}"][i]), 1e-6))
    # (6) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(r["malt_oven"], r["malt_mw"])),
                   float(INTRO.correct), 0.0))
    # (7) 画面の回数が足して1万
    checks.append(("A・B・C の合計", float(len(cats())), float(N_TRIAL), 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  再生 {TL['s1']:.0f}倍 / {TL['s2']:.0f}倍  食べごろ {T_FIN1:.2f} / {T_FIN2:.2f}秒  "
          f"答え {T_REV:.1f}  なぜ {T_WHY:.1f}  ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 9.5, 10.5, 11.5, 12.5, 14.5, 16.5, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 2.5, T_TW + 1.0, tw_done_t() + 1.5, T_Q + 1.5,
              DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
