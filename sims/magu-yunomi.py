"""温かい飲み物、マグカップと湯のみ、冷めにくいのは？ 同時に90℃のお湯を注いで1万回。— 2026-10-26 作成（ナレーションなし・45秒前後）

くらべるのは「飲みごろの60℃まで下がるのに何分かかるか」だけ。

モデル（お湯と器の温度を、時間を細かく刻んで一緒に計算。お湯はよく混ざっているとする）
  お湯 Tw ……… m·c_w·dTw/dt = −q_水面 − L·ṁ − q_壁           （q_壁 = お湯から器の内側へ入る熱）
  器の内側 Ti … C_i·dTi/dt = q_壁 − q_貫通                       （器の熱容量 ＝ ③ 器が最初に熱を吸うぶん）
  器の外側 To … C_o·dTo/dt = q_貫通 − q_外                       （器の厚さの半分ずつの2枚の層）
  ① 水面（口） q_水面 = A_口·[h_上·(Tw−Tr) + ε·σ·(Tw⁴−Tr⁴)] ＋ 蒸発 L(T)·ṁ
       ṁ = A_口·h_m·max(ρv(Tw) − RH·ρv(Tr), 0)       h_m = h_上 ÷ (ρ_空気·c_p·Le^(2/3))   … 熱と水蒸気の伝わり方の類似（Chilton–Colburn）
       ρv は飽和水蒸気の濃さ（Buck の式）、L(T) = 2.501e6 − 2370·T [J/kg]。蒸発した分だけお湯の量も減る。
  ② 側面と底 q_壁 = g_壁·A·(Tw−Ti)、q_貫通 = (k ÷ (δ/2))·A·(Ti−To)、q_外 = A·[h_自然·(To−Tr) + ε·σ·(To⁴−Tr⁴)]
       g_壁 = 1 ÷ (1/h_内 + δ/(4k))（お湯の中の自然対流 h_内 と、器の厚さの1/4の伝導）。外側の面の温度は To とした。
  A（水に触れる壁と底の面積）= π·D·h + π·D²/4、h = 注いだ量 ÷ (π·D²/4)。器は円柱で計算する（絵だけ湯のみは少し丸くした）。
  器の熱容量 C_i = C_o = ½·ρ_器·c_器·δ·A（水に触れる部分だけ。取っ手と、水より上の壁は入れていない＝仮定）。
  時間は2秒きざみのルンゲ＝クッタ（4次）。注いだ瞬間のお湯は90℃、器は部屋の温度。

  値の出典（確認できたもの）
    磁器の密度 2,300〜2,500 kg/m³       https://www.engineeringtoolbox.com/density-solids-d_1265.html
    磁器の比熱 1.07 kJ/(kg·K)（実験例では 1.09） https://www.engineeringtoolbox.com/specific-heat-solids-d_154.html
                                        https://www.glewengineering.com/thermal-analysis-of-covered-ceramic-espresso-cup/
    磁器の熱伝導率 1.5 W/(m·K)          https://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
        ※ 湯のみに多い陶器の値は確認できなかった（推定 0.5〜1.5 で磁器より低い側）。ここでは両方とも磁器の値で計算する。
    飲みごろ 60℃前後（推奨の提供温度は約54〜71℃の範囲、嗜好の上位は62.8〜68.3℃）
                                        https://foodsci.oregonstate.edu/sites/agscid7/files/foodsci/attachments/hot-bev-temp.pdf
    水の比熱 4.18 kJ/(kg·K)、水の蒸発の潜熱 2.501e6 − 2370·T（一般の物性値）
  仮定（出典なし。幅を持たせて、1回ごとにでたらめに変える）
    器の寸法の幅 … マグ: 口の直径 7.5〜9cm・高さ 9〜10cm・厚さ 4〜6mm・注ぐ量 200〜300mL
                   湯のみ: 口の直径 6.5〜8.5cm・高さ 7〜9cm・厚さ 3〜6mm・注ぐ量 120〜180mL
                   （どちらも特定の商品の寸法ではない。口の直径は内側の直径として計算した）
    部屋 … 15〜22℃、湿度 40〜70%（2つの器は同じ部屋・同じ机の上）
    熱の逃げ方 … 水面の対流 h_上 = 3〜7、器の外側の自然対流 h_自然 = 3〜6 W/(m²K)、お湯の中の対流 h_内 = 200〜500 W/(m²K)、
                 ルイス数 0.85〜0.90、放射率 0.95（水）・0.9（器）。底も側面と同じ逃げ方とした（机との接触は入れていない）。
                 **熱の逃げ方の割合（蒸発・対流・放射・壁の伝導）を比べた出典は見つからなかった。**
                 計算の結果を「実測」と言わない。軸にしたのは、水面から逃げる熱は水面の面積に比例する、という定性的な関係。
  1回ごとに、器の寸法・注ぐ量・厚さ・部屋の温度と湿度・熱の逃げ方の値を すべて でたらめに変える（一様乱数）。

問い: 「温かい飲み物、/ マグカップと湯のみ、/ 冷めにくいのは？」（前提「同時に90℃のお湯を注ぐ・器は部屋の温度」）
      選択肢: マグカップ ／ ほぼ同じ ／ 湯のみ（記号の並びは LABELS。正解を A の位置に置く）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「マグが60℃になるのが遅かった回」の割合 p と、60℃までの時間の差（マグ − 湯のみ）の中央値 g で、
      p ≥ 60% かつ g ≥ 2分 なら「マグカップ」、p ≤ 40% かつ g ≤ −2分 なら「湯のみ」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、同じ量を注いだら？」（両方とも 150mL にして、同じ1万回をもう一度）。
      量の差と形の差のどちらが効いたかが分かる。
締め: 「あなたは、マグ派？湯のみ派？」（答えは出さない）＋「コメントで教えてください」
言葉: 1万回の結果の真ん中は「中央値」（初出で一度説明）。見本の1回は「たとえば、この1回では」、その数字は「この置き方なら」。

乱数の種は見本（並んで冷める2つ）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "magu-yunomi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261101
DT = 2.0                                           # 足し算のきざみ（秒）
TMAX = 4 * 3600.0
T_POUR, T_DRINK = 90.0, 60.0                       # 注ぐ温度・飲みごろ（℃）
V_SAME = 150.0                                     # ひねり（両方に注ぐ量 mL）
# 器の寸法の幅（仮定）: 口の直径 m、高さ m、厚さ m、注ぐ量 mL
MUG = dict(D=(0.075, 0.090), H=(0.090, 0.100), dl=(0.004, 0.006), V=(200.0, 300.0))
YUN = dict(D=(0.065, 0.085), H=(0.070, 0.090), dl=(0.003, 0.006), V=(120.0, 180.0))
ROOM_T, ROOM_RH = (15.0, 22.0), (0.40, 0.70)
H_TOP, H_NAT, H_IN, LEWIS = (3.0, 7.0), (3.0, 6.0), (200.0, 500.0), (0.85, 0.90)
RHO_C = (2300.0, 2500.0)                           # 磁器の密度 kg/m³
C_C, K_C = 1070.0, 1.5                             # 磁器の比熱 J/(kg·K)・熱伝導率 W/(m·K)
C_W = 4180.0
SIGMA, EPS_W, EPS_C = 5.670e-8, 0.95, 0.90
RHOCP_AIR = 1.18 * 1006.0

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 2.0       # 割合・割合・分


def answer_by_rule(p_mug, gap_med_min):
    """p_mug = マグが60℃になるのが遅かった回（＝マグのほうが冷めにくかった回）の割合、gap_med_min = (マグ − 湯のみ) の中央値（分）。'mug' / 'same' / 'yun'"""
    if p_mug >= RULE_HI and gap_med_min >= RULE_GAP:
        return "mug"
    if p_mug <= RULE_LO and gap_med_min <= -RULE_GAP:
        return "yun"
    return "same"


def p_sat(T):
    """飽和水蒸気圧（Pa）。Buck (1996) の式"""
    return 611.21 * np.exp((18.678 - T / 234.5) * (T / (257.14 + T)))


def rho_v(T):
    """飽和水蒸気の濃さ（kg/m³）"""
    return p_sat(T) * 0.018015 / (8.314 * (np.asarray(T, float) + 273.15))


def latent(T):
    return 2.501e6 - 2370.0 * np.asarray(T, float)


def draw_params(rng, n):
    """1万回ぶんの条件。マグ・湯のみの寸法と、2つが共有する部屋・熱の逃げ方"""
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    d = dict(
        mD=u(MUG["D"]), mH=u(MUG["H"]), mdl=u(MUG["dl"]), mV=u(MUG["V"]),
        yD=u(YUN["D"]), yH=u(YUN["H"]), ydl=u(YUN["dl"]), yV=u(YUN["V"]),
        Tr=u(ROOM_T), rh=u(ROOM_RH), htop=u(H_TOP), hnat=u(H_NAT), hin=u(H_IN), Le=u(LEWIS),
        rho_m=u(RHO_C), rho_y=u(RHO_C))
    return d


def vessel(d, kind, V=None):
    """1つの器の入力（配列）。kind = 'm'（マグ）/ 'y'（湯のみ）。V を渡すとその量（mL）で上書き"""
    pre = kind
    v = dict(D=d[pre + "D"], H=d[pre + "H"], dl=d[pre + "dl"], V=(d[pre + "V"] if V is None else np.full_like(d[pre + "D"], V)),
             rho=d["rho_" + pre])
    for k in ("Tr", "rh", "htop", "hnat", "hin", "Le"):
        v[k] = d[k]
    return v


def cat(vs):
    return {k: np.concatenate([v[k] for v in vs]) for k in vs[0]}


def geometry(v):
    A_top = math.pi * v["D"] ** 2 / 4
    h0 = v["V"] * 1e-6 / A_top
    A_w = A_top + math.pi * v["D"] * h0            # 水に触れる壁＋底
    return A_top, h0, A_w


class Sim:
    """器 n 個ぶんを同時に冷ます。状態: お湯の温度 Tw・器の内側 Ti・外側 To（℃）と お湯の量 m（kg）"""

    def __init__(self, v, lossless=False):
        self.v = v
        self.n = len(v["D"])
        self.A_top, self.h0, self.A_w = geometry(v)
        self.m = v["V"] * 1e-6 * 1000.0
        self.Tw = np.full(self.n, T_POUR)
        self.Ti = v["Tr"].copy()
        self.To = v["Tr"].copy()
        self.C_half = 0.5 * v["rho"] * C_C * v["dl"] * self.A_w
        self.g_wall = 1.0 / (1.0 / v["hin"] + v["dl"] / (4 * K_C))
        self.g_thru = K_C / (v["dl"] / 2)
        self.rv_room = v["rh"] * rho_v(v["Tr"])
        self.hm = v["htop"] / (RHOCP_AIR * v["Le"] ** (2.0 / 3.0))
        self.lossless = lossless
        self.Q = np.zeros(self.n)                  # 外へ逃げた熱の合計（J）。エネルギー保存の照合用

    def rates(self, Tw, Ti, To, m, Q=None):
        v = self.v
        Tr = v["Tr"]
        q_wall = self.g_wall * self.A_w * (Tw - Ti)
        q_thru = self.g_thru * self.A_w * (Ti - To)
        if self.lossless:
            q_out = 0.0 * To
            q_top = 0.0 * Tw
            mdot = 0.0 * Tw
        else:
            q_out = self.A_w * (v["hnat"] * (To - Tr) + EPS_C * SIGMA * ((To + 273.15) ** 4 - (Tr + 273.15) ** 4))
            q_top = self.A_top * (v["htop"] * (Tw - Tr) + EPS_W * SIGMA * ((Tw + 273.15) ** 4 - (Tr + 273.15) ** 4))
            mdot = self.A_top * self.hm * np.maximum(rho_v(Tw) - self.rv_room, 0.0)
        ev = latent(Tw) * mdot
        dTw = -(q_top + ev + q_wall) / (m * C_W)
        dTi = (q_wall - q_thru) / self.C_half
        dTo = (q_thru - q_out) / self.C_half
        dm = -mdot
        dQ = q_top + ev + q_out + C_W * mdot * Tw       # 逃げる熱（水蒸気になって出ていく水が持ち去る分も入れる）
        return dTw, dTi, dTo, dm, dQ

    def step(self, dt=DT):
        s = (self.Tw, self.Ti, self.To, self.m, self.Q)
        k1 = self.rates(*s[:4])
        k2 = self.rates(*(s[i] + dt / 2 * k1[i] for i in range(4)))
        k3 = self.rates(*(s[i] + dt / 2 * k2[i] for i in range(4)))
        k4 = self.rates(*(s[i] + dt * k3[i] for i in range(4)))
        d = [dt / 6 * (a + 2 * b + 2 * c + e) for a, b, c, e in zip(k1, k2, k3, k4)]
        self.Tw, self.Ti, self.To, self.m, self.Q = (s[i] + d[i] for i in range(5))

    def energy(self):
        return self.m * C_W * self.Tw + self.C_half * (self.Ti + self.To)

    def run(self, dt=DT, hist=False):
        """Tw が T_DRINK になる時刻（秒）を返す。hist=True なら記録（t, Tw, Ti, To, 蒸発 ṁ）も"""
        tfin = np.full(self.n, np.inf)
        t = 0.0
        H = [(0.0, self.Tw[0], self.Ti[0], self.To[0], self._mdot0())] if hist else None
        while t < TMAX and np.isinf(tfin).any():
            Tprev = self.Tw.copy()
            self.step(dt)
            hit = np.isinf(tfin) & (self.Tw <= T_DRINK)
            fr = (Tprev - T_DRINK) / np.maximum(Tprev - self.Tw, 1e-12)
            tfin = np.where(hit, t + fr * dt, tfin)
            t += dt
            if hist:
                H.append((t, self.Tw[0], self.Ti[0], self.To[0], self._mdot0()))
        return (tfin, np.array(H)) if hist else tfin

    def _mdot0(self):
        return float(self.A_top[0] * self.hm[0] * max(rho_v(self.Tw[0]) - self.rv_room[0], 0.0))


# 熱の逃げ道ごとの内訳（1つの器・冷めるまで足し合わせる）。出典のある割合ではなく、このモデルの中の内訳
def budget(v1, dt=2.0):
    s = Sim(v1)
    tot = dict(top=0.0, evap=0.0, wall_out=0.0, vessel=0.0)
    t = 0.0
    while s.Tw[0] > T_DRINK and t < TMAX:
        Tw, To, Tr = s.Tw[0], s.To[0], v1["Tr"][0]
        tot["top"] += s.A_top[0] * (v1["htop"][0] * (Tw - Tr) + EPS_W * SIGMA * ((Tw + 273.15) ** 4 - (Tr + 273.15) ** 4)) * dt
        tot["evap"] += float(latent(Tw) * s.A_top[0] * s.hm[0] * max(rho_v(Tw) - s.rv_room[0], 0.0)) * dt
        tot["wall_out"] += s.A_w[0] * (v1["hnat"][0] * (To - Tr) + EPS_C * SIGMA * ((To + 273.15) ** 4 - (Tr + 273.15) ** 4)) * dt
        s.step(dt)
        t += dt
    tot["vessel"] = float(s.C_half[0] * ((s.Ti[0] - v1["Tr"][0]) + (s.To[0] - v1["Tr"][0])))   # その時点で器が持っている熱
    return tot, t
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
        r = dict(t_m=z["t_m"], t_y=z["t_y"], t_m150=z["t_m150"], t_y150=z["t_y150"])
    else:
        vs = [vessel(d, "m"), vessel(d, "y"), vessel(d, "m", V_SAME), vessel(d, "y", V_SAME)]
        t = Sim(cat(vs)).run()
        n = N_TRIAL
        r = dict(t_m=t[:n], t_y=t[n:2 * n], t_m150=t[2 * n:3 * n], t_y150=t[3 * n:])
        np.savez(fn, **r)
    r["p"] = d
    for k in ("t_m", "t_y", "t_m150", "t_y150"):
        r[k] = r[k] / 60.0                          # 分
    _RES["m"] = r
    return r


def shown():
    r = results()
    tm, ty, tm1, ty1 = r["t_m"], r["t_y"], r["t_m150"], r["t_y150"]
    gap, gap1 = tm - ty, tm1 - ty1
    return dict(p_mug=float((tm > ty).mean()), n_mug=int((tm > ty).sum()), n_yun=int((tm <= ty).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_m=float(np.median(tm)), med_y=float(np.median(ty)),
                q_m=np.percentile(tm, [10, 90]), q_y=np.percentile(ty, [10, 90]),
                p_mug1=float((tm1 > ty1).mean()), gap_med1=float(np.median(gap1)), gap_q1=np.percentile(gap1, [10, 25, 75, 90]),
                med_m1=float(np.median(tm1)), med_y1=float(np.median(ty1)),
                n_unfinished=int(np.isinf(tm).sum() + np.isinf(ty).sum() + np.isinf(tm1).sum() + np.isinf(ty1).sum()))


def hm_(minutes):
    """分 → '2時間54分' / '45分'"""
    mm = int(round(minutes))
    h, m = divmod(mm, 60)
    return f"{h}時間{m:02d}分" if h else f"{m}分"


def report():
    sh = shown()
    print(f"マグが長い {sh['p_mug']:.4f}（{sh['n_mug']}回 / 湯のみが長い {sh['n_yun']}回）  差(マグ−湯のみ)の中央値 {sh['gap_med']:+.2f}分 "
          f"平均 {sh['gap_mean']:+.2f}  10/25/75/90% {np.round(sh['gap_q'], 1)}")
    print(f"  答え {answer_by_rule(sh['p_mug'], sh['gap_med'])}")
    print(f"  60℃までの中央値 マグ {sh['med_m']:.1f}分 10/90% {np.round(sh['q_m'], 1)} / 湯のみ {sh['med_y']:.1f}分 10/90% {np.round(sh['q_y'], 1)}")
    print(f"  ひねり（どちらも{V_SAME:.0f}mL）: マグが長い {sh['p_mug1']:.4f}  差の中央値 {sh['gap_med1']:+.2f}分 10/25/75/90% {np.round(sh['gap_q1'], 1)}  "
          f"答え {answer_by_rule(sh['p_mug1'], sh['gap_med1'])}  マグ {sh['med_m1']:.1f}分 湯のみ {sh['med_y1']:.1f}分  未完了 {sh['n_unfinished']}")


def diag():
    """量と形の効き方、熱の逃げ道の内訳（真ん中くらいの条件で）"""
    r = results()
    d = r["p"]
    sh = shown()
    sel = int(np.argmin(np.abs(r["t_m"] - sh["med_m"]) / sh["med_m"] + np.abs(r["t_y"] - sh["med_y"]) / sh["med_y"]))
    d1 = {k: v[sel:sel + 1] for k, v in d.items()}
    print(f"  内訳の条件（試行{sel}）: マグ D={d1['mD'][0] * 100:.1f}cm H={d1['mH'][0] * 100:.1f}cm δ={d1['mdl'][0] * 1000:.1f}mm V={d1['mV'][0]:.0f}mL "
          f"| 湯のみ D={d1['yD'][0] * 100:.1f}cm H={d1['yH'][0] * 100:.1f}cm δ={d1['ydl'][0] * 1000:.1f}mm V={d1['yV'][0]:.0f}mL | 室温 {d1['Tr'][0]:.1f}℃ 湿度 {d1['rh'][0] * 100:.0f}%")
    for nm, kind, V in (("マグ", "m", None), ("湯のみ", "y", None), ("マグ150", "m", V_SAME), ("湯のみ150", "y", V_SAME)):
        b, tt = budget(vessel(d1, kind, V))
        tot = b["top"] + b["evap"] + b["wall_out"] + b["vessel"]
        print(f"   {nm}: 60℃まで {tt / 60:.1f}分  逃げた熱の内訳（器に溜まった分を含む）水面の対流・放射 {b['top'] / tot * 100:.0f}% 蒸発 {b['evap'] / tot * 100:.0f}% "
              f"器の外側から {b['wall_out'] / tot * 100:.0f}% 器が持っている {b['vessel'] / tot * 100:.0f}%")
    # 量を入れ替える: マグに湯のみの量、湯のみにマグの量
    v_a = vessel(d, "m")
    v_a["V"] = d["yV"].copy()
    v_b = vessel(d, "y")
    v_b["V"] = d["mV"].copy()
    ok = []
    for v in (v_a, v_b):
        A, h0, _ = geometry(v)
        ok.append(bool(np.all(h0 < v["H"] - 0.015)))
    s = Sim(cat([v_a, v_b])).run() / 60.0
    ta, tb = s[:N_TRIAL], s[N_TRIAL:]
    print(f"  量だけ入れ替え: マグ(湯のみの量) 中央値 {np.median(ta):.1f}分（元 {sh['med_m']:.1f}） 湯のみ(マグの量) {np.median(tb):.1f}分（元 {sh['med_y']:.1f}） 溢れない={ok}")


def tw_check():
    """損失なし・器とお湯が同じ温度になったときの温度が、熱容量の重みつき平均と同じか（器の熱容量 ＝ 最初に熱を吸うぶん）"""
    r = results()
    d = {k: v[:200] for k, v in r["p"].items()}
    out = []
    for kind in ("m", "y"):
        v = vessel(d, kind)
        s = Sim(v, lossless=True)
        for _ in range(int(3000 / DT)):
            s.step(DT)
        Cw = s.m * C_W
        Cv = 2 * s.C_half
        eq = (Cw * T_POUR + Cv * v["Tr"]) / (Cw + Cv)
        out.append(float(np.max(np.abs(np.stack([s.Tw, s.Ti, s.To]) - eq))))
    return max(out)


def energy_check():
    """熱の損失を足していくと、お湯と器が持つ熱の減りと同じになる（相対誤差の最大）"""
    r = results()
    d = {k: v[:300] for k, v in r["p"].items()}
    v = cat([vessel(d, "m"), vessel(d, "y")])
    s = Sim(v)
    e0 = s.energy() - 0.0
    # エネルギーの基準は 0℃。逃げる熱 dQ は 水蒸気になって出ていく水の持ち去る分を含む
    for _ in range(int(1500 / DT)):
        s.step(DT)
    err = np.abs((e0 - s.energy()) - s.Q) / e0
    return float(np.max(err))


def dt_check():
    r = results()
    d = {k: v[:200] for k, v in r["p"].items()}
    v = cat([vessel(d, "m"), vessel(d, "y")])
    a = Sim(v).run(dt=2.0)
    b = Sim(v).run(dt=0.5)
    return float(np.max(np.abs(a - b)) / 60.0)


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    diag()
    print(f"  損失なしの平衡温度の食い違い（最大・℃）: {tw_check():.4f}  エネルギー保存の食い違い（最大・割合）: {energy_check():.2e}  "
          f"きざみ 2秒 と 0.5秒 の差（最大・分）: {dt_check():.5f}")
    sys.exit(0)


# =====================================================================
# 見本（並んで冷める2つ）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 差が中央値の近く（±12%）、マグの時間・湯のみの時間とも中央値の近く（±10%）、湯のみの口がマグより0.6cm以上細い。その中で差が中央値に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    tm, ty = r["t_m"], r["t_y"]
    gap = tm - ty
    ok = (np.abs(gap / sh["gap_med"] - 1) < 0.12) & (np.abs(tm / sh["med_m"] - 1) < 0.10) & (np.abs(ty / sh["med_y"] - 1) < 0.10)
    cand = np.nonzero(ok & (p["yD"] <= p["mD"] - 0.006))[0]       # 絵で「湯のみは少し細い」と分かるよう、口が0.6cm以上細い回から
    if len(cand) == 0:
        cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    sm, hm_hist = Sim(vessel(d1, "m")).run(hist=True)
    sy, hy_hist = Sim(vessel(d1, "y")).run(hist=True)
    q = {k: float(v[i]) for k, v in p.items()}
    _SAMPLE = dict(i=i, p=q, t_m=float(tm[i]), t_y=float(ty[i]), gap=float(gap[i]), h_m=hm_hist, h_y=hy_hist,
                   chk=(float(sm[0]) / 60.0, float(sy[0]) / 60.0),
                   m=dict(D=q["mD"] * 100, H=q["mH"] * 100, dl=q["mdl"] * 1000, V=q["mV"]),
                   y=dict(D=q["yD"] * 100, H=q["yH"] * 100, dl=q["ydl"] * 1000, V=q["yV"]), Tr=q["Tr"])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    print("見本", s["i"], "マグ", {k: round(v, 2) for k, v in s["m"].items()}, "湯のみ", {k: round(v, 2) for k, v in s["y"].items()},
          "室温", round(s["Tr"], 1), "| マグ", round(s["t_m"], 1), "分 湯のみ", round(s["t_y"], 1), "分 差", round(s["gap"], 1), "分")
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
note.DATE = "11.4"                                 # 日付欄（公開予定日）

COL_M, INK_M = "#f4ad6a", "#b8601a"                # マグカップ（だいだい）
COL_Y, INK_Y = "#8fbbe8", "#2f63a8"                # 湯のみ（水色）
TEA = "#e0b25a"
WALL_COOL, WALL_HOT = "#f7f3ea", "#ee9a5b"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["マグカップ", "ほぼ同じ", "湯のみ"]
TAG = {"mug": "A", "yun": "C"}
CORRECT = 0                                        # answer_by_rule の結果の位置
KEY_LABEL = {"mug": "マグカップ", "same": "ほぼ同じ", "yun": "湯のみ"}
NAME = {"m": "マグカップ", "y": "湯のみ"}
KIND_KEY = {"m": "mug", "y": "yun"}
COLS = {"m": COL_M, "y": COL_Y}
INKC = {"m": INK_M, "y": INK_Y}

BIG_Q = ["温かい飲み物、マグカップと湯のみ、", "冷めにくいのは？"]            # 定位置（上）の2行
BIG_Q3 = ["温かい飲み物、", "マグカップと湯のみ、", "冷めにくいのは？"]        # 1コマ目の3行（同じ大きさ）
DETAIL = "同時に90℃のお湯を注ぐ・器は部屋の温度"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
T_P = 1.3                                          # 注ぎ終わり
RACE_LEN = 9.0                                     # T_GO から2つとも60℃になるまで
R0 = 0.9                                           # 注いだあとの進み（シミュの分／動画の秒）

# ---------- 画面の置き場所 ----------
FR = (80.0, 830.0, 1020.0, 1480.0)                 # 絵の枠 x0, y0, x1, y1
S = 29.0                                           # 1cm = 29px
YB = 1318.0                                        # 器の底（机の上）
CXM, CXP, CXY = 288.0, 548.0, 802.0
CX = {"m": CXM, "y": CXY}
Y_T0, Y_K = 1062.0, 3.4                            # 温度計: 40℃の高さ、1℃あたりのpx
TABLE_BACK, TABLE_FRONT = 1215.0, 1345.0


def th_y(T):
    return Y_T0 - (T - 40.0) * Y_K


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_m"], s["t_y"]))
    T_FIN2 = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 80, 1 / 200)
        sp = np.where(ts < T_P, 0.0, np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts])))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 400.0
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
    T_G1 = T_G0 + 2.6
    T_REV = T_G1 + 2.6
    T_ANS2 = T_REV + 1.7
    T_TW = T_ANS2 + 4.4
    T_Q = T_TW + 12.6
    DURATION = T_Q + 4.6


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


MDOT_REF = None


def mdot_ref():
    global MDOT_REF
    if MDOT_REF is None:
        s = sample()
        MDOT_REF = max(float(s["h_m"][0, 4]), float(s["h_y"][0, 4]))
    return MDOT_REF


def kstate(t, kind):
    """その時刻の 器の状態: 温度計の読み・器の内側/外側の温度・湯気の量・注いだ高さの割合"""
    s = sample()
    h = s["h_" + kind]
    sec = tau_of(t) * 60.0
    Tw = float(np.interp(sec, h[:, 0], h[:, 1]))
    Ti = float(np.interp(sec, h[:, 0], h[:, 2]))
    To = float(np.interp(sec, h[:, 0], h[:, 3]))
    md = float(np.interp(sec, h[:, 0], h[:, 4]))
    pour = ease(clamp01(t / (T_P - 0.2)))
    read = s["Tr"] + (Tw - s["Tr"]) * ease(clamp01(t / 1.0))
    return dict(read=read, Tw=Tw, Ti=Ti, To=To, steam=md / mdot_ref() * ease(clamp01(t / 0.9)), lvl=pour)


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def lerp_col(c0, c1, u):
    a, b = hexrgb(c0), hexrgb(c1)
    return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))


def wall_col(T):
    u = clamp01((T - sample()["Tr"]) / (82.0 - sample()["Tr"]))
    return lerp_col(WALL_COOL, WALL_HOT, u)


def clip_frame(ctx):
    core.rrect(ctx, FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1], 22)
    ctx.clip()


def border_frame(ctx):
    core.rrect(ctx, FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1], 22)
    _stroke(ctx, 3.5, INK, 0.75)


ZOOM0, ZOOM_T = 1.16, 1.25


def zoom_art(ctx, t, cx):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(cx, 1130.0)
    ctx.scale(z, z)
    ctx.translate(-cx, -1130.0)


def poly_path(ctx, pts):
    ctx.new_path()
    for i, (x, y) in enumerate(pts):
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()


def vessel_poly(cx, rim_y, top_half, bot_half, y_bot, ch=16.0):
    """器の断面（左右対称）。底の角は面取り"""
    ch = min(ch, bot_half * 0.5)
    return [(cx - top_half, rim_y), (cx - bot_half, y_bot - ch), (cx - bot_half + ch, y_bot),
            (cx + bot_half - ch, y_bot), (cx + bot_half, y_bot - ch), (cx + top_half, rim_y)]


def geom(kind):
    s = sample()
    q = s[kind]
    Dp, Hp = q["D"] * S, q["H"] * S
    dp = max(q["dl"] / 10.0 * S, 7.0)
    top_half = Dp / 2 + dp
    bot_half = top_half * (1.0 if kind == "m" else 0.86)
    A_top = math.pi * (q["D"] / 100) ** 2 / 4
    h_cm = q["V"] * 1e-6 / A_top * 100
    return dict(Dp=Dp, Hp=Hp, dp=dp, top_half=top_half, bot_half=bot_half, rim_y=YB - Hp, h_px=h_cm * S, cx=CX[kind],
                sgn=1 if kind == "m" else -1)


# ---------- 絵: 人 ----------

def draw_person(ctx, cx, t, mood):
    """テーブルの奥に座る人（頭と胴と腕）。mood 0 = 考え中、1 = にっこり"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    bob = 3.0 * math.sin(t * 1.7)
    hy = 916.0 + bob
    sweater, skin, hair = "#8fc9a3", "#f6dcc6", "#3a2f2a"
    # 胴
    ctx.new_path()
    ctx.move_to(cx - 142, 1232)
    ctx.line_to(cx - 150, 1040 + bob)
    ctx.curve_to(cx - 150, 996 + bob, cx - 100, 990 + bob, cx - 52, 988 + bob)
    ctx.line_to(cx + 52, 988 + bob)
    ctx.curve_to(cx + 100, 990 + bob, cx + 150, 996 + bob, cx + 150, 1040 + bob)
    ctx.line_to(cx + 142, 1232)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(sweater))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)
    # えり
    ctx.arc(cx, 990 + bob, 38, 0.05 * math.pi, 0.95 * math.pi)
    ctx.set_source_rgba(*hexrgb("#6fae88"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    # 首
    core.rrect(ctx, cx - 22, hy + 52, 44, 46, 10)
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    # 頭
    ctx.arc(cx, hy, 68, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    for sg in (-1, 1):                              # 耳
        ctx.arc(cx + sg * 68, hy + 6, 13, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(skin))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
    ctx.new_path()                                  # かみ
    ctx.arc(cx, hy - 6, 74, math.pi * 1.02, math.pi * 1.98)
    ctx.curve_to(cx + 52, hy - 40, cx - 20, hy - 44, cx - 74, hy - 14)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill()
    # 目（2つの器を交互に見る）
    gaze = math.sin(t * 1.15)
    blink = 1.0 if (t % 3.1) < 0.12 else 0.0
    for sg in (-1, 1):
        ex, ey = cx + sg * 27 + 7 * gaze, hy + 6
        if blink:
            ctx.move_to(ex - 9, ey)
            ctx.line_to(ex + 9, ey)
            _stroke(ctx, 3.5, INK, 0.95)
        else:
            ctx.arc(ex, ey, 8.5, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()
        ctx.move_to(ex - 13, ey - 21 - 3 * (1 - mood))
        ctx.line_to(ex + 13, ey - 24 + 3 * (1 - mood) * sg)
        _stroke(ctx, 4, hair, 0.95)
    # ほっぺ・口
    for sg in (-1, 1):
        ctx.arc(cx + sg * 44, hy + 30, 11, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f4a79b", 0.55))
        ctx.fill()
    if mood > 0.5:
        ctx.arc(cx, hy + 28, 20, 0.12 * math.pi, 0.88 * math.pi)
    else:
        ctx.move_to(cx - 12, hy + 40)
        ctx.curve_to(cx - 4, hy + 36, cx + 4, hy + 36, cx + 12, hy + 41)
    _stroke(ctx, 4, INK, 0.95)


def draw_arms(ctx, cx, t, mood):
    """机の上に出ている腕と手（机より手前）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    sweater, skin = "#8fc9a3", "#f6dcc6"
    bob = 3.0 * math.sin(t * 1.7)
    for sg in (-1, 1):
        x0, y0 = cx + sg * 132, 1040 + bob
        x1, y1 = cx + sg * 92, 1268
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 + sg * 26, y0 + 90, x1 + sg * 30, y1 - 70, x1, y1)
        _stroke(ctx, 56, INK, 0.95)
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 + sg * 26, y0 + 90, x1 + sg * 30, y1 - 70, x1, y1)
        _stroke(ctx, 49, sweater, 1.0)
        ctx.arc(x1 - sg * 6, y1 + 18, 25, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(skin))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)


# ---------- 絵: 背景と机 ----------

def draw_room(ctx):
    fill(ctx, hexrgb("#f7efe0"))
    ctx.rectangle(FR[0], FR[1], FR[2] - FR[0], TABLE_BACK - FR[1])
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#eadfc8", 0.9))
    for x in range(int(FR[0]) - 40, int(FR[2]) + 40, 44):
        ctx.rectangle(x, FR[1], 16, TABLE_BACK - FR[1])
        ctx.fill()


def draw_table(ctx):
    ctx.rectangle(FR[0] - 10, TABLE_BACK, FR[2] - FR[0] + 20, TABLE_FRONT - TABLE_BACK)
    ctx.set_source_rgba(*hexrgb("#e2b87c"))
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#c9985c", 0.55))
    ctx.set_line_width(2.5)
    for k in range(7):
        y = TABLE_BACK + 14 + k * 18
        ctx.move_to(FR[0] - 10, y)
        ctx.curve_to(300, y - 5, 700, y + 6, FR[2] + 10, y - 2)
        ctx.stroke()
    ctx.rectangle(FR[0] - 10, TABLE_FRONT, FR[2] - FR[0] + 20, FR[3] - TABLE_FRONT + 10)
    ctx.set_source_rgba(*hexrgb("#d4a56e"))
    ctx.fill()
    ctx.move_to(FR[0] - 10, TABLE_FRONT)
    ctx.line_to(FR[2] + 10, TABLE_FRONT)
    _stroke(ctx, 5, INK, 0.8)
    ctx.move_to(FR[0] - 10, TABLE_BACK)
    ctx.line_to(FR[2] + 10, TABLE_BACK)
    _stroke(ctx, 3, INK, 0.5)


def draw_line60(ctx):
    """飲みごろ 60℃ の線（2つの温度計をつなぐ）"""
    y = th_y(T_DRINK)
    ctx.set_dash([18, 12])
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    ctx.move_to(FR[0] + 8, y)
    ctx.line_to(FR[2] - 8, y)
    _stroke(ctx, 4.5, RED, 0.85)
    ctx.set_dash([])


def draw_line60_label(ctx, a):
    if a <= 0:
        return
    y = th_y(T_DRINK)
    w = core.text_width("飲みごろ 60℃", 30)
    cx = 902.0
    ctx.set_source_rgba(*hexrgb("#f7efe0", 0.92 * a))
    core.rrect(ctx, cx - w / 2 - 12, y - 56, w + 24, 42, 12)
    ctx.fill()
    text(ctx, "飲みごろ 60℃", cx, y - 35, 30, RED, alpha=a)


# ---------- 絵: 器 ----------

def draw_steam(ctx, cx, rim_y, wid, amount, t, seed, a):
    """湯気。amount（注いだ直後のいちばん多いほう＝1）が大きいほど、本数が多く・濃く・高く上がる"""
    if a <= 0 or amount <= 0.02:
        return
    amount = amount ** 0.6                          # 見た目: 量が減っても消えてしまわないように（量の順序は変えない）
    rng = np.random.default_rng(seed)
    n = 12
    ctx.save()
    ctx.rectangle(FR[0], FR[1] + 4, FR[2] - FR[0], rim_y - FR[1] - 4)
    ctx.clip()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.55, 0.85)
        x0 = cx + (k / (n - 1) - 0.5) * wid * 0.9 + rng.uniform(-8, 8)
        amp = rng.uniform(14, 26)
        wl = rng.uniform(110, 160)
        u = (t * sp + ph) % 1.0
        vis = clamp01(amount * n * 1.1 - k)
        al = 0.9 * a * vis * min(1.0, 0.4 + 0.6 * amount) * math.sin(math.pi * u) ** 0.8
        if al <= 0.02:
            continue
        rise = 230 * min(1.2, 0.5 + 0.7 * amount)
        y_bot = rim_y - 4 - u * rise
        L = 130 + 60 * amount
        for (col, aa, lw) in (("#a3b1c4", 0.75 * al, 14 + 5 * amount), ("#ffffff", al, 9 + 4 * amount)):
            ctx.set_source_rgba(*hexrgb(col, aa))
            ctx.set_line_width(lw)
            for i in range(18):
                v = i / 17
                yy = y_bot - v * L
                xx = x0 + amp * math.sin((yy + t * 120) / wl * 2 * math.pi + k) * (0.4 + v)
                (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
            ctx.stroke()
    ctx.restore()


def draw_thermo(ctx, x, T, g, side):
    """料理用の棒の温度計（器に差してある）。赤い柱の高さ＝温度。2本とも同じ目盛り・同じ高さ"""
    top, bot = th_y(90) - 24, YB - g["dp"] - 10
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    core.rrect(ctx, x - 13, top, 26, bot - top, 13)
    ctx.set_source_rgba(1, 1, 1, 0.93)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    y = th_y(max(36.0, min(92.0, T)))
    ctx.set_source_rgba(*hexrgb(RED, 0.95))
    core.rrect(ctx, x - 5.5, y, 11, bot - y - 4, 5.5)
    ctx.fill()
    ctx.set_line_width(2.5)
    for v in range(50, 91, 5):
        yy = th_y(v)
        if yy > g["rim_y"] - 8:
            continue
        big = v % 10 == 0
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ln = 15 if big else 8
        ctx.move_to(x + side * 13, yy)
        ctx.line_to(x + side * (13 + ln), yy)
        ctx.stroke()
        if big and v >= 70:
            text(ctx, f"{v}", x + side * 36, yy, 26, PENCIL, align="left" if side > 0 else "right", bold=False)


def draw_vessel(ctx, t, kind, done_t):
    s = sample()
    st = kstate(t, kind)
    g = geom(kind)
    cx, rim_y, dp = g["cx"], g["rim_y"], g["dp"]
    th, bh = g["top_half"], g["bot_half"]
    sgn = g["sgn"]
    # 影
    ctx.save()
    ctx.translate(cx, YB + 4)
    ctx.scale(bh + 18, 14)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.3, 0.2, 0.1, 0.22)
    ctx.fill()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    col_o, col_i = wall_col(st["To"]), wall_col(st["Ti"])
    # 取っ手（マグ）
    if kind == "m":
        hx = cx - th
        ctx.new_path()
        ctx.move_to(hx + 8, rim_y + 34)
        ctx.curve_to(hx - 92, rim_y + 14, hx - 96, rim_y + 188, hx + 8, rim_y + 176)
        ctx.line_to(hx + 8, rim_y + 146)
        ctx.curve_to(hx - 52, rim_y + 156, hx - 52, rim_y + 62, hx + 8, rim_y + 66)
        ctx.close_path()
        ctx.set_source_rgba(*col_o, 1.0)
        ctx.fill_preserve()
        _stroke(ctx, 4.5, INK, 0.95)
    outer = vessel_poly(cx, rim_y, th, bh, YB)
    layer = vessel_poly(cx, rim_y, th - dp / 2, bh - dp / 2, YB - dp / 2, 12.0)
    cav = vessel_poly(cx, rim_y, th - dp, bh - dp, YB - dp, 10.0)
    # 壁（外側の半分 To・内側の半分 Ti）
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    poly_path(ctx, outer)
    for i, (x, y) in enumerate(cav):
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()
    ctx.set_source_rgba(*col_o, 1.0)
    ctx.fill()
    poly_path(ctx, layer)
    for i, (x, y) in enumerate(cav):
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()
    ctx.set_source_rgba(*col_i, 1.0)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    # 中（空気とお湯）
    poly_path(ctx, cav)
    ctx.set_source_rgba(1, 1, 1, 0.34)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    y_w = YB - dp - g["h_px"] * st["lvl"]
    ctx.set_source_rgba(*hexrgb(TEA, 0.93))
    ctx.move_to(cx - th, y_w)
    for i in range(21):
        x = cx - th + i * (2 * th) / 20
        ctx.line_to(x, y_w + 2.5 * math.sin(x / 11 + t * 5))
    ctx.line_to(cx + th, YB)
    ctx.line_to(cx - th, YB)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    # ふちの線
    for pts, w_ in ((outer, 5.0), (cav, 3.5)):
        ctx.new_path()
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        _stroke(ctx, w_, INK, 0.95)
    # 湯気
    draw_steam(ctx, cx, rim_y, 2 * (th - dp), st["steam"], t, 11 if kind == "m" else 29, 1.0)
    # 注ぐお湯
    if t < T_P + 0.15:
        sx = cx - sgn * 36
        top_y = FR[1] + 4 + (clamp01((t - (T_P - 0.15)) / 0.3) ** 1.3) * max(0.0, y_w - FR[1] - 4)
        if top_y < y_w:
            ctx.save()
            ctx.rectangle(FR[0], FR[1] + 4, FR[2] - FR[0], y_w - FR[1] - 4 + 6)
            ctx.clip()
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(sx, top_y)
            ctx.line_to(sx + 2.5 * math.sin(t * 40), y_w)
            _stroke(ctx, 15, TEA, 0.9)
            ctx.move_to(sx - 3, top_y)
            ctx.line_to(sx - 2, y_w)
            _stroke(ctx, 4, "#ffffff", 0.55)
            ctx.restore()
    # 温度計
    tx = cx + sgn * (th - dp - 40)
    draw_thermo(ctx, tx, st["read"], g, -1)
    # 器の中の数字
    nx = cx - sgn * 30
    ny = (min(y_w, YB - dp - 70) + YB - dp) / 2 + 2
    if st["lvl"] > 0.6:
        done = done_t is not None
        col = RED if done else INK
        text(ctx, f"{st['read']:.0f}℃", nx, ny, 54, col)
        if done:
            note.pen_circle(ctx, nx, ny, 86, 40, RED, seed=70 + (kind == "y"), width=5, progress=clamp01((t - done_t) / 0.35))


def draw_labels(ctx, t, kind, done_t, tmin, a):
    g = geom(kind)
    cx = g["cx"]
    cx_l = min(cx, 790.0) if kind == "y" else cx
    q = sample()[kind]
    name = NAME[kind]
    y1, y2 = 1376.0, 1418.0
    wn = core.text_width(name, 38)
    xd = cx_l - wn / 2 - 34
    fill(ctx, (1, 1, 1, 0.92 * a))
    ctx.arc(xd, y1, 22, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, y1, 22, 22, INKC[kind], seed=13 + (kind == "y"), width=3.4, alpha=a)
    text(ctx, TAG[KIND_KEY[kind]], xd, y1, 30, INKC[kind], alpha=a)
    text(ctx, name, cx_l, y1, 38, INKC[kind], alpha=a)
    if done_t is None:
        lab = f"口{q['D']:.1f}cm・{q['V']:.0f}mL・厚{q['dl']:.0f}mm"
        text(ctx, lab, min(cx_l, 925.0 - core.text_width(lab, 26, False) / 2), y2, 26, INK, bold=False, alpha=a)
    else:
        u = clamp01((t - done_t) / 0.35)
        lab_a, lab_b = "この置き方なら ", f"{tmin:.0f}分"
        sz = 30.0
        while core.text_width(lab_a + lab_b, sz) > 270 and sz > 25:
            sz -= 1
        wa, wb = core.text_width(lab_a, sz), core.text_width(lab_b, sz)
        x0 = cx_l - (wa + wb) / 2
        x0 = min(x0, 925.0 - (wa + wb))
        text(ctx, lab_a, x0, y2, sz, INK, align="left", bold=False, alpha=a)
        text(ctx, lab_b, x0 + wa, y2, sz, RED, align="left", alpha=a)
        note.pen_circle(ctx, x0 + wa + wb / 2, y2, wb / 2 + 14, 22, RED, seed=80 + (kind == "y"), width=4, progress=u, alpha=a)


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
    done_m = t_of(s["t_m"]) if tau >= s["t_m"] else None
    done_y = t_of(s["t_y"]) if tau >= s["t_y"] else None
    mood = 1.0 if (done_m is not None and done_y is not None) else 0.0
    ctx.push_group()
    ctx.save()
    clip_frame(ctx)
    ctx.save()
    zoom_art(ctx, t, CXP)
    draw_room(ctx)
    draw_line60(ctx)
    draw_person(ctx, CXP, t, mood)
    draw_table(ctx)
    draw_arms(ctx, CXP, t, mood)
    draw_vessel(ctx, t, "y", done_y)
    draw_vessel(ctx, t, "m", done_m)
    ctx.restore()
    draw_line60_label(ctx, ease((t - 1.1) / 0.3))
    la = ease((t - 1.0) / 0.4)
    if la > 0:
        draw_labels(ctx, t, "m", done_m, s["t_m"], la)
        draw_labels(ctx, t, "y", done_y, s["t_y"], la)
    ctx.restore()
    border_frame(ctx)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, f"経過 {hm_(tau_of(t))}", 580, 640, 40, "yellow", a=a, tilt=-0.02)
    text(ctx, "たとえば、この1回では（早送り）", 580, 726, 28, PENCIL, bold=False, alpha=a)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results()
    win_m = (r["t_m"] > r["t_y"]).astype(int)           # 1 = マグのほうが冷めにくい（60℃になるのが遅い）
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_Y), bgra(COL_M)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_m[:m]]
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


def hm_about(minutes):
    mm = int(round(minutes))
    h, m = divmod(mm, 60)
    if h and m:
        return f"約{h}時間{m}分"
    if h:
        return f"約{h}時間"
    return f"約{m}分"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results()
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
    win_m = r["t_m"][:m] > r["t_y"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("m", int(win_m.sum())), ("y", int(m - win_m.sum())))):
            y = 1185 + i * 54
            fill(ctx, hexrgb(COLS[k], a * lg))
            ctx.rectangle(150, y - 17, 34, 34)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(150, y - 17, 34, 34)
            ctx.stroke()
            text(ctx, f"{TAG[KIND_KEY[k]]} {NAME[k]}のほうが冷めにくい", 200, y, 34, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 925, y, 34, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            sh = shown()
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            lead = "マグ" if sh["gap_med"] >= 0 else "湯のみ"
            lead_p = sh["p_mug"] if sh["gap_med"] >= 0 else 1 - sh["p_mug"]
            note.sticky(ctx, f"{lead}が冷めにくい回は 約{pct_i(lead_p)}。\n差は 中央値で {hm_about(abs(sh['gap_med']))}\n（中央値＝1万回の ちょうど真ん中の値）",
                        580, 1352, 30, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_mug"], sh["gap_med"])


def reason_text():
    sh = shown()
    k = answer_key()
    a, b = f"{sh['med_m']:.1f}", f"{sh['med_y']:.1f}"
    if k == "mug":
        return f"マグは注ぐ量が多い（約250mL対約150mL）。\n60℃までの中央値は マグ{a}分・湯のみ{b}分"
    if k == "yun":
        return f"湯のみのほうが 長く温かい。\n60℃までの中央値は 湯のみ{b}分・マグ{a}分"
    return f"60℃までの時間は ほぼ互角。\n中央値は マグ{a}分・湯のみ{b}分"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1218, 52, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        note.sticky(ctx, reason_text(), 580, 1348, 30, "blue", a=c, tilt=0.012)


# ---------- ひねり（同じ量を注いだら） ----------
BAR_X0, BAR_W20 = 300.0, 560.0                     # 棒の左端、20分ぶんの長さ


def twist_lead():
    sh = shown()
    p1 = sh["p_mug1"]
    if p1 <= 0.40 and sh["gap_med1"] < 0:
        return "湯のみ", 1 - p1
    if p1 >= 0.60 and sh["gap_med1"] > 0:
        return "マグ", p1
    return "ほぼ同じ", max(p1, 1 - p1)


def twist_text():
    sh = shown()
    lead, pr = twist_lead()
    gap = hm_about(abs(sh["gap_med1"]))
    if lead == "湯のみ":
        return f"同じ量なら 湯のみが冷めにくい回が 約{pct_i(pr)}。\n差は 中央値で{gap}。\nマグが冷めにくかったのは 量のおかげ"
    if lead == "マグ":
        return f"同じ量でも マグが冷めにくい回が 約{pct_i(pr)}。\n差は 中央値で{gap}。\n量だけでなく 形も効いていた"
    return f"同じ量だと ほぼ同じ。\n差は 中央値で{gap}。\n差をつくっていたのは 量だった"


def draw_bar(ctx, y, minutes, kind, a, grow):
    wbar = BAR_W20 * minutes / 20.0 * grow
    text(ctx, NAME[kind], 140, y, 34, INKC[kind], align="left", alpha=a)
    fill(ctx, hexrgb(COLS[kind], a))
    core.rrect(ctx, BAR_X0 + 40, y - 21, max(wbar, 1.0), 42, 8)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    core.rrect(ctx, BAR_X0 + 40, y - 21, max(wbar, 1.0), 42, 8)
    ctx.stroke()
    if grow > 0.98:
        text(ctx, f"{minutes:.1f}分", BAR_X0 + 40 + wbar + 14, y, 34, INK, align="left", alpha=a)


def draw_twist(ctx, t):
    if t < T_TW:
        return
    sh = shown()
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo <= 0:
        return
    u = t - T_TW
    ctx.push_group()
    a0 = ease_out(u / 0.3)
    note.sticky(ctx, "では、同じ量を注いだら？", 580, 690, 50, "yellow", fg=RED, a=a0, tilt=-0.02)
    if u > 0.6:
        text(ctx, f"どちらも{V_SAME:.0f}mLにして、同じ1万回", 580, 772, 30, INK, bold=False, alpha=ease_out((u - 0.6) / 0.3))
    ua = u - 1.4
    if ua > 0:
        a = ease_out(ua / 0.3)
        text(ctx, "さっきの1万回（60℃までの中央値）", 140, 850, 30, INK, align="left", bold=False, alpha=a)
        g = ease(clamp01((ua - 0.2) / 0.8))
        draw_bar(ctx, 910, sh["med_m"], "m", a, g)
        draw_bar(ctx, 972, sh["med_y"], "y", a, g)
    ub = u - 3.6
    if ub > 0:
        a = ease_out(ub / 0.3)
        text(ctx, f"どちらも{V_SAME:.0f}mLなら", 140, 1056, 30, INK, align="left", bold=False, alpha=a)
        g = ease(clamp01((ub - 0.2) / 0.8))
        draw_bar(ctx, 1116, sh["med_m1"], "m", a, g)
        draw_bar(ctx, 1178, sh["med_y1"], "y", a, g)
    uc = u - 6.4
    if uc > 0:
        note.sticky(ctx, twist_text(), 580, 1330, 32, "pink", fg=RED, a=ease_out(uc / 0.3), tilt=-0.012)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(fo)


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


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下で、お湯を注ぐ（0秒目から動く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = big3_size(860.0)
        ys = (450, 552, 654)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.03 * (1 - ease_out(t / 0.4))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q3[2], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, 702, 565 + w2 / 2 + 6, 698, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, 740, 30, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 792
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


INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_clock(ctx, t)
    fo = 1 - ease((t - T_TW) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\nマグ派？湯のみ派？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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
    pour = noise_band(T_P + 0.2, 14, 5, 1.0)                  # お湯を注ぐ音（さー）
    tt = np.arange(len(pour)) / SR
    pour = pour * np.minimum(1, tt / 0.05) * np.minimum(1, (T_P + 0.2 - tt) / 0.25) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * tt))
    mx.add(0.0, pour, 0.55)
    hiss_len = T_G0
    hiss = noise_band(hiss_len, 6, 9, 1.0)                    # 湯気のしゅー（だんだん小さく）
    th = np.arange(len(hiss)) / SR
    hiss = hiss * np.minimum(1, th / 0.5) * np.minimum(1, (hiss_len - th) / 0.5) * np.clip(1.0 - th / 22.0, 0.3, 1.0)
    mx.add(0.3, hiss, 0.10)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    tg, te = t_of(s["t_m"]), t_of(s["t_y"])
    mx.add(min(tg, te), bell(784.0, 1.2), 0.45)
    mx.add(max(tg, te), bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                       # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                            # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    mx.add(T_TW + 1.8, blip(659.3, 0.12), 0.3)
    mx.add(T_TW + 4.0, blip(659.3, 0.12), 0.3)
    mx.add(T_TW + 6.8, blip(784.0, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    checks = []
    checks.append(("損失なしの平衡温度（最大の食い違い・℃）", tw_check(), 0.0, 0.01))
    checks.append(("エネルギー保存（最大の食い違い・割合）", energy_check(), 0.0, 1e-6))
    checks.append(("きざみ 2秒 と 0.5秒 の差（最大・分）", dt_check(), 0.0, 0.01))
    s = sample()
    checks.append(("見本のマグの時刻（分）が1万回の値と同じ", s["chk"][0], s["t_m"], 1e-6))
    checks.append(("見本の湯のみの時刻（分）が1万回の値と同じ", s["chk"][1], s["t_y"], 1e-6))
    key = answer_by_rule(sh["p_mug"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（先頭）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（マグ・湯のみ）",
                   float(LABELS.index(NAME["m"]) * 10 + LABELS.index(NAME["y"])),
                   float("ABC".index(TAG["mug"]) * 10 + "ABC".index(TAG["yun"])), 0.0))
    checks.append(("見本の差（分）が中央値の近く", s["gap"], sh["gap_med"], 0.12 * abs(sh["gap_med"])))
    checks.append(("マグが長い回＋湯のみが長い回", float(sh["n_mug"] + sh["n_yun"]), float(N_TRIAL), 0.0))
    checks.append(("60℃まで下がらなかった回（4時間）", float(sh["n_unfinished"]), 0.0, 0.0))
    d = r["p"]
    free = []
    for kind in ("m", "y"):
        for V in (None, V_SAME):
            v = vessel(d, kind, V)
            _, h0, _ = geometry(v)
            free.append(v["H"] - v["dl"] - h0)           # 水面から口までの高さ（m）
    fmin = float(min(np.min(f) for f in free))
    print(f"  水面から口までの高さの最小: {fmin * 100:.2f}cm（湯のみに 180mL をいちばん細い 6.5cm の口へ注ぐ回など）")
    checks.append(("すべての回で お湯があふれない（水面が口より0.5cm以上下）", float(fmin >= 0.005), 1.0, 0.0))
    v1, v2 = vessel(d, "m", V_SAME), vessel(d, "y", V_SAME)
    checks.append(("ひねりの注ぐ量が両方 150mL", float(np.all(v1["V"] == V_SAME) and np.all(v2["V"] == V_SAME)), 1.0, 0.0))
    checks.append(("60℃までの中央値が 5〜30分に収まる（マグ・湯のみ・ひねり4つ）",
                   float(all(5 <= x <= 30 for x in (sh["med_m"], sh["med_y"], sh["med_m1"], sh["med_y1"]))), 1.0, 0.0))
    check_answers(checks)


def lint():
    """mp4 は書かずに、全コマの文字を記録して 公開前チェックと同じ点検（位置・大きさ・読み切れる長さ・0秒目の動き・長さ・冒頭の音）をする"""
    n = int(round(DURATION * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    core._LOG = []
    first = probe = None
    for i in range(n):
        core._CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        if i == 0:
            surf.flush()
            first = np.frombuffer(bytes(surf.get_data()), np.uint8)
        elif i == int(0.3 * FPS):
            surf.flush()
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
    log, core._LOG = core._LOG, None
    problems = core.preflight(log, first, probe, DURATION, build_audio())
    if problems:
        print("公開前チェック相当: 要対応")
        for p_ in problems:
            print("  -", p_)
    else:
        print("公開前チェック相当: OK")
    return problems


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  60℃ {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（マグ {hm_(s['t_m'])} / 湯のみ {hm_(s['t_y'])}）")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.2, 5.8, 8.0, 10.0, T_FIN1 + 0.4, T_FIN2 - 0.6, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 2.0, T_TW + 4.8, T_TW + 8.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
