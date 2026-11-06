"""おにぎり、アルミホイルとラップ、冷めにくいのは？ 同じ炊きたてを同時に包んで1時間後の中心の温度を1万回くらべる。— 2026-10-27 作成（ナレーションなし・45秒前後）

くらべるのは「包んで1時間後の、おにぎりの中心の温度」だけ（温度の差だけで比べる。「食べごろ」の線は根拠がないので出さない）。

モデル（球に近い形のおにぎりの中の熱の伝わりと、包みの外へ逃げる熱を、時間を刻んで一緒に計算）
  ごはん … 同じ厚さの球殻 6 層。層ごとの熱容量 C_j = ρ·c·V_j、層のあいだは熱伝導 G_j = k·4π r_j² ÷ Δr。
           表面の温度 Ts は いちばん外の層の温度とした（層の半分の厚さの温度差は無視＝仮定）。
           表面積 A = 形の係数 f × 4πR²（三角に握ると球より広い。f = 1.15〜1.4 ＝仮定）。
  ごはん表面 → 包み（すき間の厚さ δ）
      熱伝導 + 放射   q_cd = A·[ k_空気/δ·(Ts−Tw) + ε_eff·σ·(Ts⁴−Tw⁴) ]    ε_eff = 1/(1/ε_ごはん + 1/ε_包み − 1)
      水蒸気          ごはんの表面で蒸発 → すき間を拡散 → 包みの内側で凝縮（熱を包みに渡す）。一部はすき間から外へ逃げる。
                      m_e = A·ぬれ·h_m·(ρv(Ts) − ρ_g)   m_c = A·h_m·(ρ_g − ρv(Tw))   m_l = G·(ρ_g − ρ_部屋)
                      ρ_g（すき間の水蒸気の濃さ）は m_e = m_c + m_l で決まる。h_m = 2·D_v/δ。ごはんから出ていく熱 = q_cd + m_e·L。
  包み（熱容量なしとして、毎ステップ熱のつりあいで温度 Tw を決める）
      包みに入る熱 q_cd + m_c·L ＝ 外へ出す熱 A·[ h·(Tw−Tr) + ε_外·σ·(Tw⁴−Tr⁴) ]
      すき間から逃げた水蒸気 m_l·L は そのぶん部屋へ持ち去られる熱（L = 2.40e6 J/kg 一定）。
  タオル（ひねり）… 包みの外に厚さ δ_t・熱伝導率 k_t のタオル1枚ぶんの断熱（熱抵抗 δ_t/k_t）を足す。
           すき間から逃げた水蒸気はタオルの中で凝縮して、タオルの外面から出ていくとする（＝仮定）。
           タオルの熱容量は入れていない（準定常＝仮定）。タオルの外面は h と放射率 0.9 で逃がす。
  時間は 10秒きざみのルンゲ＝クッタ（4次）。包んだ瞬間のごはんは どの層も同じ温度（60〜70℃）、包みは部屋の温度。

  値の出典（確認できたもの）
    アルミホイルの放射率 0.04（0.03〜0.1）  https://www.engineeringtoolbox.com/emissivity-coefficients-d_447.html
    PE・PVC（ラップの素材に近いもの）の放射率 0.90〜0.97 → ラップは 0.80〜0.95 と置く（ポリ塩化ビニリデンの値は見つからなかった）
                                            同上
    アルミの熱伝導率 約215〜237 W/(m·K)、PE 0.33〜0.51、PVC 0.19（膜が薄く、結果に効かない）
                                            https://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    炊いた米の比熱 2.93 kJ/(kg·K)（5〜90℃で測定）  https://www.spkx.net.cn/CN/Y2011/V32/I3/103
    自然対流の熱伝達率（気体）2〜25 W/(m²·K)、小さな物体・温度差30K程度で 約5〜10
                                            https://pages.mtu.edu/~fmorriso/cm3120/typical_values_heat_transfer_coefficient.pdf
    空気の熱伝導率 0.0262 W/(m·K)（25℃）  https://www.engineeringtoolbox.com/air-properties-d_156.html
    水の蒸発の潜熱・水蒸気の飽和（Buck の式）は一般の物性値
  仮定（出典なし。幅を持たせて、1回ごとにでたらめに変える）
    **ラップの厚さ・炊いた米の熱伝導率と密度・包みのすき間の厚さ・すき間から逃げる水蒸気の量は、出典を確認できなかった。**
    おにぎり 90〜115g、ごはんの密度 800〜1000 kg/m³、熱伝導率 0.3〜0.6 W/(m·K)、表面積の係数 1.15〜1.4、ごはんの放射率 0.95、表面のぬれ具合 0.3〜1.0
    包んだ瞬間の温度 60〜70℃、部屋 12〜24℃・湿度 40〜70%
    置き場所 … 台の上（h = 3〜8 W/m²K）か バッグの中＝風なし（h = 1.5〜3.5）を半々
    アルミ … 放射率 0.03〜0.10、ゆるく巻いたすき間 0.5〜3mm、合わせ目から出入りする空気 0〜4e-6 m³/s
    ラップ … 放射率 0.80〜0.95、密着に近いすき間 0.05〜0.5mm、合わせ目から出入りする空気 0〜1e-6 m³/s
    タオル … 厚さ 3〜6mm、熱伝導率 0.04〜0.07 W/(m·K)、放射率 0.9
    **実際におにぎりの温度を測った実験は見つからなかった。計算の結果を「実測」と言わない。**
    机との接触・ごはんが乾くことで質量が減ること・包みの大きさの違いは入れていない（2つとも同じ扱い）。
  1回ごとに、上の値をすべてでたらめに変える（一様乱数）。2つの包みは「同じおにぎり・同じ部屋・同じ置き場所」で、包みの値だけが違う。

問い: 「おにぎり、/ アルミホイルとラップ、/ 冷めにくいのは？」（前提「炊きたて（60〜70℃）を同時に包む・1時間後に比べる」）
      選択肢: アルミホイル ／ ほぼ同じ ／ ラップ（記号の並びは LABELS。正解を B の位置に置く）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「アルミのほうが1時間後に温かかった回」の割合 p と、中心の温度の差（アルミ − ラップ）の中央値 g（℃）で、
      p ≥ 60% かつ g ≥ 1℃ なら「アルミホイル」、p ≤ 40% かつ g ≤ −1℃ なら「ラップ」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、両方をタオルで包んだら？」（タオル1枚ぶんの断熱を足して、同じ1万回をもう一度）。
締め: 「あなたは、アルミ派？ラップ派？」（答えは出さない）＋「コメントで教えてください」
言葉: 1万回の結果の真ん中は「中央値」（初出で一度説明）。見本の1回は「たとえば、この1回では」、その数字は「この置き方なら」。

乱数の種は見本（並んで冷める2つ）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "onigiri-tsutsumi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261106
DT = 10.0                                          # 足し算のきざみ（秒）
T_END = 3600.0                                     # 1時間
NSH = 6                                            # ごはんの層の数
LAT = 2.40e6                                       # 水の蒸発の潜熱 J/kg（一定とした）
SIGMA = 5.670e-8
K_AIR, D_V = 0.027, 2.6e-5                         # 空気の熱伝導率 W/(m·K)・水蒸気の拡散係数 m²/s
C_RICE, EPS_RICE, EPS_TOWEL = 2930.0, 0.95, 0.90
# 幅（仮定）。(下限, 上限)
RANGES = dict(
    m=(0.090, 0.115), rho=(800.0, 1000.0), k=(0.30, 0.60), f=(1.15, 1.40), T0=(60.0, 70.0), Tr=(12.0, 24.0), rh=(0.40, 0.70),
    h_table=(3.0, 8.0), h_bag=(1.5, 3.5), wet=(0.30, 1.00),
    eps_f=(0.03, 0.10), gap_f=(0.5e-3, 3.0e-3), G_f=(0.0, 4.0e-6),
    eps_w=(0.80, 0.95), gap_w=(0.05e-3, 0.5e-3), G_w=(0.0, 1.0e-6),
    td=(3.0e-3, 6.0e-3), kt=(0.04, 0.07))

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 1.0       # 割合・割合・℃


def answer_by_rule(p_foil, gap_med):
    """p_foil = アルミのほうが1時間後に温かかった回の割合、gap_med = (アルミ − ラップ) の中央値（℃）。'foil' / 'same' / 'wrap'"""
    if p_foil >= RULE_HI and gap_med >= RULE_GAP:
        return "foil"
    if p_foil <= RULE_LO and gap_med <= -RULE_GAP:
        return "wrap"
    return "same"


def p_sat(T):
    """飽和水蒸気圧（Pa）。Buck (1996) の式"""
    return 611.21 * np.exp((18.678 - T / 234.5) * (T / (257.14 + T)))


def rho_v(T):
    """飽和水蒸気の濃さ（kg/m³）"""
    return p_sat(T) * 0.018015 / (8.314 * (np.asarray(T, float) + 273.15))


def draw_params(rng, n):
    """1万回ぶんの条件（おにぎり・部屋・置き場所は2つの包みで共通。包みの値は別）"""
    u = lambda key: rng.uniform(RANGES[key][0], RANGES[key][1], n)    # noqa: E731
    d = {k: u(k) for k in ("m", "rho", "k", "f", "T0", "Tr", "rh", "wet", "eps_f", "gap_f", "G_f", "eps_w", "gap_w", "G_w", "td", "kt")}
    bag = rng.random(n) < 0.5
    d["bag"] = bag
    d["h"] = np.where(bag, u("h_bag"), u("h_table"))
    return d


def batch(d, kinds):
    """kinds = 'f'（アルミ）/ 'w'（ラップ）のリスト。それぞれ n 個ぶんをつなげた入力（配列）にする"""
    out = {}
    for key in ("m", "rho", "k", "f", "T0", "Tr", "rh", "wet", "h", "td", "kt"):
        out[key] = np.concatenate([d[key] for _ in kinds])
    out["eps"] = np.concatenate([d["eps_" + kd] for kd in kinds])
    out["gap"] = np.concatenate([d["gap_" + kd] for kd in kinds])
    out["G"] = np.concatenate([d["G_" + kd] for kd in kinds])
    return out


class Sim:
    """おにぎり n 個ぶんを同時に冷ます。状態: ごはんの層ごとの温度 T[n, NSH]（℃）"""

    def __init__(self, P, towel=False, lossless=False, T_init=None):
        self.P = P
        self.towel, self.lossless = towel, lossless
        n = len(P["m"])
        self.n = n
        V = P["m"] / P["rho"]
        R = (3 * V / (4 * math.pi)) ** (1.0 / 3.0)
        self.R = R
        j = np.arange(NSH + 1)
        edges = R[:, None] * j[None, :] / NSH
        vol = 4.0 / 3.0 * math.pi * (edges[:, 1:] ** 3 - edges[:, :-1] ** 3)
        self.C = P["rho"][:, None] * C_RICE * vol
        dr = (R / NSH)[:, None]
        self.Gc = P["k"][:, None] * 4 * math.pi * edges[:, 1:NSH] ** 2 / dr      # 層のあいだの熱コンダクタンス W/K
        self.A = P["f"] * 4 * math.pi * R ** 2
        self.hm = 2 * D_V / P["gap"]
        self.a = self.A * P["wet"] * self.hm
        self.b = self.A * self.hm
        self.eeff = 1.0 / (1.0 / EPS_RICE + 1.0 / P["eps"] - 1.0)
        self.rho_room = P["rh"] * rho_v(P["Tr"])
        self.Rt = P["td"] / P["kt"]
        self.At = self.A * (1 + P["td"] / R) ** 2
        if lossless:
            self.h = 0.0 * P["h"]
            self.eps_o = 0.0 * P["eps"]
            self.G = 0.0 * P["G"]
        else:
            self.h, self.eps_o, self.G = P["h"], P["eps"], P["G"]
        T0 = P["T0"][:, None] * np.ones((n, NSH)) if T_init is None else T_init.copy()
        self.T = T0
        self.Q = np.zeros(n)

    def _wrapper(self, Ts, Tw):
        """包みの温度が Tw のときの各量。g = 包みに入る熱 − 外へ出す熱（Tw が高いほど小さくなる）"""
        Tr = self.P["Tr"]
        rs, rw = rho_v(Ts), rho_v(Tw)
        a, b, c = self.a, self.b, self.G
        rg = (a * rs + b * rw + c * self.rho_room) / (a + b + c)
        me, mc, ml = a * (rs - rg), b * (rg - rw), c * (rg - self.rho_room)
        K = lambda T: T + 273.15                                    # noqa: E731
        qcd = self.A * (K_AIR / self.P["gap"] * (Ts - Tw) + self.eeff * SIGMA * (K(Ts) ** 4 - K(Tw) ** 4))
        qin = qcd + mc * LAT
        if self.towel:
            Tt = 0.5 * (Tw + Tr)
            for _ in range(8):
                heff = self.h + EPS_TOWEL * SIGMA * (K(Tt) ** 2 + K(Tr) ** 2) * (K(Tt) + K(Tr))
                Tt = (self.A * Tw / self.Rt + ml * LAT + self.At * heff * Tr) / (self.A / self.Rt + self.At * heff)
            q_to = self.A * (Tw - Tt) / self.Rt
            q_loss = self.At * (self.h * (Tt - Tr) + EPS_TOWEL * SIGMA * (K(Tt) ** 4 - K(Tr) ** 4))   # 外へ逃げた熱の合計
        else:
            q_to = self.A * (self.h * (Tw - Tr) + self.eps_o * SIGMA * (K(Tw) ** 4 - K(Tr) ** 4))
            q_loss = q_to + ml * LAT
        return dict(g=qin - q_to, qcd=qcd, me=me, mc=mc, ml=ml, q_loss=q_loss)

    def rates(self, T):
        Ts = T[:, -1]
        lo, hi = np.minimum(self.P["Tr"], Ts), Ts.copy()
        for _ in range(22):
            mid = 0.5 * (lo + hi)
            pos = self._wrapper(Ts, mid)["g"] > 0
            lo = np.where(pos, mid, lo)
            hi = np.where(pos, hi, mid)
        Tw = 0.5 * (lo + hi)
        w = self._wrapper(Ts, Tw)
        flow = self.Gc * (T[:, :-1] - T[:, 1:])                       # 内側→外側の熱
        dT = np.zeros_like(T)
        dT[:, :-1] -= flow
        dT[:, 1:] += flow
        dT[:, -1] -= w["qcd"] + w["me"] * LAT
        dT = dT / self.C
        w["Tw"] = Tw
        return dT, w

    def step(self, dt=DT):
        T = self.T
        k1, w1 = self.rates(T)
        k2, w2 = self.rates(T + dt / 2 * k1)
        k3, w3 = self.rates(T + dt / 2 * k2)
        k4, w4 = self.rates(T + dt * k3)
        # 逃げた熱の合計は、ルンゲ＝クッタの4つの段の逃げ方を同じ重みで足す
        self.Q = self.Q + dt / 6 * (w1["q_loss"] + 2 * w2["q_loss"] + 2 * w3["q_loss"] + w4["q_loss"])
        self.T = T + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    def energy(self):
        return (self.C * self.T).sum(axis=1)

    def run(self, dt=DT, t_end=T_END, hist=False):
        """t_end 秒後の中心の温度（℃）を返す。hist=True なら記録（t, 中心, 表面, 包み, 蒸発 m_e, 逃げる m_l, 凝縮 m_c）も"""
        H = []
        t = 0.0
        if hist:
            _, w = self.rates(self.T)
            H.append((0.0, self.T[0, 0], self.T[0, -1], w["Tw"][0], w["me"][0], w["ml"][0], w["mc"][0]))
        while t < t_end - 1e-9:
            self.step(dt)
            t += dt
            if hist:
                _, w = self.rates(self.T)
                H.append((t, self.T[0, 0], self.T[0, -1], w["Tw"][0], w["me"][0], w["ml"][0], w["mc"][0]))
        return (self.T[:, 0].copy(), np.array(H)) if hist else self.T[:, 0].copy()
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
        r = dict(c_f=z["c_f"], c_w=z["c_w"], c_ft=z["c_ft"], c_wt=z["c_wt"])
    else:
        n = N_TRIAL
        t = Sim(batch(d, ["f", "w"])).run()
        tt = Sim(batch(d, ["f", "w"]), towel=True).run()
        r = dict(c_f=t[:n], c_w=t[n:], c_ft=tt[:n], c_wt=tt[n:])
        np.savez(fn, **r)
    r["p"] = d
    _RES["m"] = r
    return r


def shown():
    r = results()
    cf, cw, cft, cwt = r["c_f"], r["c_w"], r["c_ft"], r["c_wt"]
    gap, gapt = cf - cw, cft - cwt
    return dict(p_foil=float((cf > cw).mean()), n_foil=int((cf > cw).sum()), n_wrap=int((cf <= cw).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_f=float(np.median(cf)), med_w=float(np.median(cw)), q_f=np.percentile(cf, [10, 90]), q_w=np.percentile(cw, [10, 90]),
                p_foilt=float((cft > cwt).mean()), gap_medt=float(np.median(gapt)), gap_qt=np.percentile(gapt, [10, 25, 75, 90]),
                med_ft=float(np.median(cft)), med_wt=float(np.median(cwt)),
                n_bad=int((~np.isfinite(cf)).sum() + (~np.isfinite(cw)).sum() + (~np.isfinite(cft)).sum() + (~np.isfinite(cwt)).sum()))


def report():
    sh = shown()
    print(f"アルミが温かい {sh['p_foil']:.4f}（{sh['n_foil']}回 / ラップが温かい {sh['n_wrap']}回）  差(アルミ−ラップ)の中央値 {sh['gap_med']:+.2f}℃ "
          f"平均 {sh['gap_mean']:+.2f}  10/25/75/90% {np.round(sh['gap_q'], 2)}")
    print(f"  答え {answer_by_rule(sh['p_foil'], sh['gap_med'])}")
    print(f"  1時間後の中心の中央値 アルミ {sh['med_f']:.1f}℃ 10/90% {np.round(sh['q_f'], 1)} / ラップ {sh['med_w']:.1f}℃ 10/90% {np.round(sh['q_w'], 1)}")
    print(f"  ひねり（タオル）: アルミが温かい {sh['p_foilt']:.4f}  差の中央値 {sh['gap_medt']:+.2f}℃ 10/25/75/90% {np.round(sh['gap_qt'], 2)}  "
          f"答え {answer_by_rule(sh['p_foilt'], sh['gap_medt'])}  アルミ {sh['med_ft']:.1f}℃ ラップ {sh['med_wt']:.1f}℃  計算できなかった {sh['n_bad']}")


def _sub(d, n):
    return {k: v[:n] for k, v in d.items()}


def diag():
    """どの仮定が効いているか（感度）。1万回のうち先頭 3000 回で見る（答えの統計ではない）"""
    r = results()
    n = 3000
    base = _sub(r["p"], n)

    def run(dd, towel=False):
        t = Sim(batch(dd, ["f", "w"]), towel=towel).run()
        gap = t[:n] - t[n:]
        return float((gap > 0).mean()), float(np.median(gap)), float(np.median(t[:n])), float(np.median(t[n:]))

    print(f"  感度（先頭 {n} 回）  [アルミが温かい割合, 差の中央値℃, アルミ中央値, ラップ中央値]")
    print("   ふつう                                 ", np.round(run(base), 3))
    d1 = dict(base)
    d1["G_f"] = np.zeros(n)
    d1["G_w"] = np.zeros(n)
    print("   水蒸気がすき間から全く逃げない（両方）  ", np.round(run(d1), 3))
    d2 = dict(base)
    d2["eps_f"] = d2["eps_w"].copy()
    print("   アルミの放射率をラップと同じにした      ", np.round(run(d2), 3))
    d3 = dict(base)
    d3["G_f"] = d3["G_w"].copy()
    print("   アルミの出入りをラップと同じにした      ", np.round(run(d3), 3))
    d4 = dict(base)
    d4["gap_f"] = d4["gap_w"].copy()
    print("   アルミのすき間をラップと同じにした      ", np.round(run(d4), 3))
    d5 = dict(base)
    d5["G_f"] = d5["G_f"] * 2
    print("   アルミの出入りを2倍                     ", np.round(run(d5), 3))
    for nm, sel in (("台の上", ~base["bag"]), ("バッグの中", base["bag"])):
        dd = {k: v[sel] for k, v in base.items()}
        t = Sim(batch(dd, ["f", "w"])).run()
        m = int(sel.sum())
        gap = t[:m] - t[m:]
        print(f"   {nm}だけ: アルミが温かい {float((gap > 0).mean()):.3f} 差の中央値 {float(np.median(gap)):+.2f}℃ アルミ {np.median(t[:m]):.1f} ラップ {np.median(t[m:]):.1f}")
    # 1つの真ん中の条件で、時間ごとの内訳
    sh = shown()
    sel = int(np.argmin(np.abs(r["c_f"] - sh["med_f"]) + np.abs(r["c_w"] - sh["med_w"])))
    d1_ = {k: v[sel:sel + 1] for k, v in r["p"].items()}
    for nm, kd in (("アルミ", "f"), ("ラップ", "w")):
        s = Sim(batch(d1_, [kd]))
        c, H = s.run(hist=True)
        i = [0, 30, 120, 360]
        print(f"   中央値に近い1回（試行{sel}・{'バッグ' if d1_['bag'][0] else '台の上'}・室温{d1_['Tr'][0]:.0f}℃・{d1_['m'][0] * 1000:.0f}g）{nm}: "
              + " ".join(f"{int(H[k, 0] / 60)}分 中心{H[k, 1]:.1f}/表面{H[k, 2]:.1f}/包み{H[k, 3]:.1f}" for k in i)
              + f"  蒸発{H[1, 4] * LAT:.2f}W 逃げる{H[1, 5] * LAT:.2f}W 凝縮{H[1, 6] * LAT:.2f}W(開始10秒後)")


def lump_check():
    """損失なし・初期に温度むらがあるとき、層が全部同じ温度になり、その値が熱容量の重みつき平均と同じか"""
    r = results()
    P = batch(_sub(r["p"], 100), ["f"])
    s = Sim(P, lossless=True)
    rng = np.random.default_rng(3)
    s.T = 20.0 + 50.0 * rng.random((s.n, NSH))
    eq = (s.C * s.T).sum(axis=1) / s.C.sum(axis=1)
    for _ in range(int(40000 / DT)):
        s.step(DT)
    return float(np.max(np.abs(s.T - eq[:, None])))


def energy_check():
    """逃げた熱の合計（包みの外側で数えたもの）が、ごはんが持つ熱の減りと同じになる（相対誤差の最大。アルミ・ラップ・タオルあり）"""
    r = results()
    out = 0.0
    for towel in (False, True):
        P = batch(_sub(r["p"], 150), ["f", "w"])
        s = Sim(P, towel=towel)
        e0 = s.energy()
        for _ in range(int(1800 / DT)):
            s.step(DT)
        err = np.abs((e0 - s.energy()) - s.Q) / (e0 - s.energy())
        out = max(out, float(np.max(err)))
    return out


def dt_check():
    r = results()
    P = batch(_sub(r["p"], 200), ["f", "w"])
    a = Sim(P).run(dt=10.0)
    b = Sim(P).run(dt=2.5)
    return float(np.max(np.abs(a - b)))


def same_check():
    """アルミとラップの値を同じにしたら、差が出ない（入れ替わりのまちがいの点検）"""
    r = results()
    d = _sub(r["p"], 200)
    for k in ("eps", "gap", "G"):
        d[k + "_f"] = d[k + "_w"].copy()
    P = batch(d, ["f", "w"])
    t = Sim(P).run()
    return float(np.max(np.abs(t[:200] - t[200:])))


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    diag()
    print(f"  損失なしで層がそろう温度の食い違い（最大・℃）: {lump_check():.4f}  エネルギー保存の食い違い（最大・割合）: {energy_check():.2e}  "
          f"きざみ 10秒 と 2.5秒 の差（最大・℃）: {dt_check():.5f}  同じ値にしたときの差（℃）: {same_check():.2e}")
    sys.exit(0)


# =====================================================================
# 見本（並んで冷める2つ）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 差が中央値の近く（±12%または±0.35℃）、アルミ・ラップとも1時間後の温度が中央値の近く（±8%）、置き場所は台の上、
    アルミの合わせ目から空気が出入りする量が 1e-6 m³/s 以上（絵で湯気が出るのが見える回）。その中で差が中央値に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    cf, cw = r["c_f"], r["c_w"]
    gap = cf - cw
    tol = max(0.12 * abs(sh["gap_med"]), 0.35)
    ok = (np.abs(gap - sh["gap_med"]) <= tol) & (np.abs(cf / sh["med_f"] - 1) < 0.08) & (np.abs(cw / sh["med_w"] - 1) < 0.08)
    cand = np.nonzero(ok & (~p["bag"]) & (p["G_f"] >= 1.0e-6))[0]
    if len(cand) == 0:
        cand = np.nonzero(ok & (~p["bag"]))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    sf, hf = Sim(batch(d1, ["f"])).run(hist=True)
    sw, hw = Sim(batch(d1, ["w"])).run(hist=True)
    q = {k: float(v[i]) for k, v in p.items()}
    _SAMPLE = dict(i=i, p=q, c_f=float(cf[i]), c_w=float(cw[i]), gap=float(gap[i]), h_f=hf, h_w=hw,
                   chk=(float(sf[0]), float(sw[0])), Tr=q["Tr"], T0=q["T0"], mass=q["m"] * 1000.0)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    print("見本", s["i"], "アルミ", round(s["c_f"], 2), "℃ ラップ", round(s["c_w"], 2), "℃ 差", round(s["gap"], 2), "℃ 室温", round(s["Tr"], 1),
          "初め", round(s["T0"], 1), "質量", round(s["mass"]), "g  アルミ G", s["p"]["G_f"], "すき間", s["p"]["gap_f"])
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
note.DATE = "11.6"                                 # 日付欄（公開予定日）

COL_F, INK_F = "#9db7d8", "#2f5f9e"                # アルミホイル（水色）
COL_W, INK_W = "#f0a95f", "#b05a14"                # ラップ（だいだい）

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["ほぼ同じ", "アルミホイル", "ラップ"]
TAG = {"foil": "B", "wrap": "C"}
CORRECT = 1                                        # answer_by_rule の結果の位置（B）
KEY_LABEL = {"foil": "アルミホイル", "same": "ほぼ同じ", "wrap": "ラップ"}
NAME = {"f": "アルミホイル", "w": "ラップ"}
KIND_KEY = {"f": "foil", "w": "wrap"}
COLS = {"f": COL_F, "w": COL_W}
INKC = {"f": INK_F, "w": INK_W}

BIG_Q = ["おにぎり、アルミホイルとラップ、", "冷めにくいのは？"]                # 定位置（上）の2行
BIG_Q3 = ["おにぎり、", "アルミホイルとラップ、", "冷めにくいのは？"]            # 1コマ目の3行（同じ大きさ）
DETAIL = "炊きたて（60〜70℃）を同時に包む・1時間後に比べる"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
T_P = 1.3                                          # 包み終わり
T_WRAP_DONE = 1.2                                  # 包みが形になる
RACE_LEN = 9.0                                     # T_GO から1時間たつまで
R0 = 0.9                                           # 包んだあとの進み（シミュの分／動画の秒）
TOTAL_MIN = T_END / 60.0

# ---------- 画面の置き場所 ----------
FR = (80.0, 830.0, 1020.0, 1480.0)                 # 絵の枠 x0, y0, x1, y1
YB = 1318.0                                        # おにぎりの底（机の上）
CXP = 548.0
CXF, CXW = 288.0, 802.0
CX = {"f": CXF, "w": CXW}
HALF, HGT = 165.0, 280.0                           # おにぎりの底の半分の幅・高さ
TABLE_BACK, TABLE_FRONT = 1215.0, 1345.0
APEX = YB - HGT


def setup():
    global TL, RX, T_FIN, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_Q, DURATION
    sample()
    T_FIN = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 80, 1 / 200)
        sp = np.where(ts < T_P, 0.0, np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts])))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN, ts, tau)) > TOTAL_MIN:
            hi = mid
        else:
            lo = mid
    RX = hi
    ts, tau = build(RX)
    TL = dict(t=ts, tau=tau)
    T_G0 = T_FIN + 1.7
    T_G1 = T_G0 + 2.6
    T_REV = T_G1 + 2.6
    T_ANS2 = T_REV + 1.7
    T_TW = T_ANS2 + 4.4
    T_Q = T_TW + 12.6
    DURATION = T_Q + 4.6


def tau_of(t):
    return min(float(np.interp(t, TL["t"], TL["tau"])), TOTAL_MIN)


_REF = {}


def refs():
    """湯気・くもりの絵の大きさをそろえる基準（2つの包みの最大値）"""
    if not _REF:
        s = sample()
        _REF["ml"] = max(float(s["h_f"][:, 5].max()), float(s["h_w"][:, 5].max()), 1e-30)
        _REF["mc"] = max(float(s["h_w"][:, 6].max()), 1e-30)
    return _REF


def kstate(t, kind):
    """その時刻の 温度計の読み（中心）・表面・包み・湯気（すき間から逃げる）・くもり（包みの内側で凝縮）・包みの進み"""
    s = sample()
    h = s["h_" + kind]
    sec = tau_of(t) * 60.0
    Tc = float(np.interp(sec, h[:, 0], h[:, 1]))
    Ts = float(np.interp(sec, h[:, 0], h[:, 2]))
    Tw = float(np.interp(sec, h[:, 0], h[:, 3]))
    ml = float(np.interp(sec, h[:, 0], h[:, 5]))
    mc = float(np.interp(sec, h[:, 0], h[:, 6]))
    u = ease(clamp01((t - 0.15) / (T_WRAP_DONE - 0.15)))
    leak = (ml / refs()["ml"]) ** 0.7
    bare = 1.0 - ease(clamp01((t - 0.5) / 0.9))
    steam = max(bare, leak * 0.9 * ease(clamp01((t - 0.9) / 0.6)))
    fog = (mc / refs()["mc"]) ** 0.5 if kind == "w" else 0.0
    return dict(read=Tc, Ts=Ts, Tw=Tw, steam=steam, fog=fog * ease(clamp01((t - 0.9) / 0.8)), wrap=u)


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


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


def rounded_poly(ctx, pts, radii):
    """角を丸めた多角形の経路"""
    n = len(pts)
    ctx.new_path()
    for i in range(n):
        v, p, q = np.array(pts[i], float), np.array(pts[i - 1], float), np.array(pts[(i + 1) % n], float)
        d1, d2 = (p - v) / np.linalg.norm(p - v), (q - v) / np.linalg.norm(q - v)
        a, b = v + d1 * radii[i], v + d2 * radii[i]
        c1, c2 = a + (v - a) * 0.66, b + (v - b) * 0.66
        (ctx.move_to if i == 0 else ctx.line_to)(*a)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], b[0], b[1])
    ctx.close_path()


def body_path(ctx, cx, infl=0.0, dy=0.0, sx=1.0, sy=1.0, rot=0.0):
    """おにぎりの形（角を丸めた三角）。infl だけ外へふくらませる"""
    hw, hg = (HALF + infl) * sx, (HGT + infl * 1.1) * sy
    ymid = YB - HGT * 0.4 + dy
    pts = [(cx - hw, YB + dy + infl * 0.0), (cx + hw, YB + dy), (cx, YB - hg + dy)]
    if rot:
        c, s_ = math.cos(rot), math.sin(rot)
        pts = [(cx + (x - cx) * c - (y - ymid) * s_, ymid + (x - cx) * s_ + (y - ymid) * c) for x, y in pts]
    rounded_poly(ctx, pts, [70 + infl * 0.4, 70 + infl * 0.4, 96 + infl * 0.4])


# ---------- 絵: 人 ----------

def draw_person(ctx, cx, t, mood):
    """テーブルの奥に座る人（頭と胴）。mood 0 = 考え中、1 = にっこり"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    bob = 3.0 * math.sin(t * 1.7)
    hy = 916.0 + bob
    sweater, skin, hair = "#8fc9a3", "#f6dcc6", "#3a2f2a"
    ctx.new_path()                                  # 胴
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
    ctx.arc(cx, 990 + bob, 38, 0.05 * math.pi, 0.95 * math.pi)     # えり
    ctx.set_source_rgba(*hexrgb("#6fae88"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    core.rrect(ctx, cx - 22, hy + 52, 44, 46, 10)                  # 首
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.arc(cx, hy, 68, 0, 2 * math.pi)                            # 頭
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    for sg in (-1, 1):                                             # 耳
        ctx.arc(cx + sg * 68, hy + 6, 13, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(skin))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
    ctx.new_path()                                                 # かみ
    ctx.arc(cx, hy - 6, 74, math.pi * 1.02, math.pi * 1.98)
    ctx.curve_to(cx + 52, hy - 40, cx - 20, hy - 44, cx - 74, hy - 14)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill()
    gaze = math.sin(t * 1.15)                                      # 目（2つを交互に見る）
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
    for sg in (-1, 1):                                             # ほっぺ・口
        ctx.arc(cx + sg * 44, hy + 30, 11, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f4a79b", 0.55))
        ctx.fill()
    if mood > 0.5:
        ctx.arc(cx, hy + 28, 20, 0.12 * math.pi, 0.88 * math.pi)
    else:
        ctx.move_to(cx - 12, hy + 40)
        ctx.curve_to(cx - 4, hy + 36, cx + 4, hy + 36, cx + 12, hy + 41)
    _stroke(ctx, 4, INK, 0.95)


def hand_pos(sg, t):
    """手の位置。0〜0.9秒は おにぎり（のホイル・ラップ）を包む動き、そのあと机の上へ戻る。sg = -1 は画面の左の手"""
    cxo = CXF if sg < 0 else CXW
    rest = (CXP + sg * 92.0, 1268.0)
    work = (cxo - sg * 98.0 + 14 * math.sin(t * 15.0), 1150.0 + 16 * math.cos(t * 12.0) + 20 * (1 - ease(clamp01(t / 0.7))) * -1)
    k = ease(clamp01((t - 0.85) / 0.7))
    return (work[0] * (1 - k) + rest[0] * k, work[1] * (1 - k) + rest[1] * k)


def draw_arms(ctx, cx, t):
    """机の上に出ている腕と手（おにぎりより手前）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    sweater, skin = "#8fc9a3", "#f6dcc6"
    bob = 3.0 * math.sin(t * 1.7)
    for sg in (-1, 1):
        x0, y0 = cx + sg * 132, 1040 + bob
        x1, y1 = hand_pos(sg, t)
        for w_, col in ((56, INK), (49, sweater)):
            ctx.move_to(x0, y0)
            ctx.curve_to(x0 + sg * 10, y0 + 100, x1 + sg * 20, y1 - 80, x1, y1)
            _stroke(ctx, w_, col, 0.95 if col == INK else 1.0)
        ctx.arc(x1 - sg * 6, y1 + 14, 25, 0, 2 * math.pi)
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


# ---------- 絵: 湯気 ----------

def draw_steam(ctx, cx, rim_y, wid, amount, t, seed, a):
    """湯気。amount（1 = いちばん多い）が大きいほど、本数が多く・濃く・高く上がる"""
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
        rise = 200 * min(1.2, 0.5 + 0.7 * amount)
        y_bot = rim_y - 4 - u * rise
        L = 120 + 50 * amount
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


# ---------- 絵: おにぎりと包み ----------

def draw_rice(ctx, cx, kind):
    """中身（ごはんと のり）。ホイルのときは上から隠れる"""
    body_path(ctx, cx)
    ctx.set_source_rgba(*hexrgb("#fcf9ef"))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    rng = np.random.default_rng(5 + (kind == "w"))
    ctx.set_source_rgba(*hexrgb("#e6dcc0", 0.9))
    ctx.set_line_width(3.2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(70):                                              # 米つぶ
        x = cx + rng.uniform(-HALF, HALF)
        y = YB - rng.uniform(100, HGT - 20)
        a_ = rng.uniform(0, math.pi)
        ctx.move_to(x, y)
        ctx.line_to(x + 9 * math.cos(a_), y + 6 * math.sin(a_))
        ctx.stroke()
    ctx.rectangle(cx - HALF - 10, YB - 100, 2 * HALF + 20, 120)      # のり
    ctx.set_source_rgba(*hexrgb("#2b3a31"))
    ctx.fill()
    ctx.move_to(cx - HALF, YB - 82)
    ctx.line_to(cx + HALF, YB - 82)
    _stroke(ctx, 3, "#5d7566", 0.8)
    ctx.restore()
    body_path(ctx, cx)
    _stroke(ctx, 4.5, INK, 0.95)


def _crinkles(ctx, cx, seed, n, a_dark, a_light, spread):
    rng = np.random.default_rng(seed)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for _ in range(n):
        x = cx + rng.uniform(-spread, spread)
        y = YB - rng.uniform(10, HGT - 10)
        ang = rng.uniform(-1.0, 1.0) + rng.choice([0.0, math.pi / 2])
        L = rng.uniform(26, 78)
        pts = [(x, y)]
        for k in range(1, 4):
            pts.append((x + math.cos(ang + rng.uniform(-0.5, 0.5)) * L * k / 3, y + math.sin(ang + rng.uniform(-0.5, 0.5)) * L * k / 3))
        for dx, col, aa, lw in ((0, "#6b7886", a_dark, 2.2), (2.5, "#ffffff", a_light, 2.6)):
            ctx.new_path()
            for i, (px, py) in enumerate(pts):
                (ctx.move_to if i == 0 else ctx.line_to)(px + dx, py + dx)
            _stroke(ctx, lw, col, aa)


def draw_foil_pkg(ctx, cx, a, t, steam_amt):
    """ホイルでくるんだ形（銀色・しわ・合わせ目・上のねじり）"""
    ctx.save()
    body_path(ctx, cx, infl=8)
    g = cairo.LinearGradient(cx - HALF, 0, cx + HALF, 0)
    for off, col in ((0.0, "#8d99a8"), (0.22, "#e7edf3"), (0.45, "#ffffff"), (0.62, "#c5ced9"), (0.82, "#eef2f6"), (1.0, "#8793a3")):
        g.add_color_stop_rgba(off, *hexrgb(col, a))
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    _crinkles(ctx, cx, 31, 44, 0.55 * a, 0.9 * a, HALF * 0.9)
    ctx.move_to(cx + 6, YB - HGT + 20)                               # 合わせ目
    ctx.curve_to(cx + 26, YB - HGT * 0.6, cx - 14, YB - HGT * 0.3, cx + 8, YB)
    _stroke(ctx, 3.2, "#5f6c7b", 0.75 * a)
    ctx.move_to(cx + 12, YB - HGT + 24)
    ctx.curve_to(cx + 32, YB - HGT * 0.6, cx - 8, YB - HGT * 0.3, cx + 14, YB)
    _stroke(ctx, 2.4, "#ffffff", 0.9 * a)
    ctx.restore()
    body_path(ctx, cx, infl=8)
    _stroke(ctx, 4.5, INK, 0.95 * a)
    # 上のつまみ（ねじって閉じたところ）
    ax = cx
    ay = YB - HGT - 8 * 1.1
    ctx.new_path()
    ctx.move_to(ax - 30, ay + 22)
    for i in range(7):
        ctx.line_to(ax - 26 + i * 8.7, ay - 12 - (8 if i % 2 else 0))
    ctx.line_to(ax + 30, ay + 22)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#dfe6ee", a))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.95 * a)
    ctx.restore()


def draw_wrap_pkg(ctx, cx, a, t, fog, seed=7):
    """ラップでくるんだ形（ごはんとのりが透ける・つや・くもりと水滴・上のひだ）"""
    ctx.save()
    body_path(ctx, cx, infl=7)
    ctx.set_source_rgba(*hexrgb("#e7f2fb", 0.26 * a))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    if fog > 0.02:                                                   # くもり（包みの内側で水蒸気が凝縮）
        g = cairo.RadialGradient(cx, YB - HGT * 0.45, 20, cx, YB - HGT * 0.45, HGT * 0.75)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.62 * fog * a)
        g.add_color_stop_rgba(1, 1, 1, 1, 0.22 * fog * a)
        ctx.set_source(g)
        ctx.paint()
        rng = np.random.default_rng(seed)
        for _ in range(70):
            x = cx + rng.uniform(-HALF * 0.9, HALF * 0.9)
            y = YB - rng.uniform(20, HGT - 10)
            rr = rng.uniform(3, 7.5)
            if rng.random() < fog + 0.15:
                ctx.arc(x, y, rr, 0, 2 * math.pi)
                ctx.set_source_rgba(1, 1, 1, 0.8 * a)
                ctx.fill_preserve()
                _stroke(ctx, 1.4, "#7f9db8", 0.7 * a)
    for (x0, y0, x1, y1, lw) in ((-0.55, -0.30, -0.30, -0.82, 9), (-0.70, -0.05, -0.62, -0.20, 6)):   # つや
        ctx.move_to(cx + x0 * HALF, YB + y0 * HGT + 0.1 * HGT)
        ctx.curve_to(cx + x0 * HALF - 8, YB + y0 * HGT - 30, cx + x1 * HALF - 14, YB + y1 * HGT + 30, cx + x1 * HALF, YB + y1 * HGT)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        _stroke(ctx, lw, "#ffffff", 0.85 * a)
    rng = np.random.default_rng(seed + 3)
    for _ in range(12):                                              # ラップの細いしわ
        x = cx + rng.uniform(-HALF * 0.8, HALF * 0.8)
        y = YB - rng.uniform(40, HGT - 30)
        ang = rng.uniform(-0.6, 0.6)
        L = rng.uniform(20, 46)
        ctx.move_to(x, y)
        ctx.line_to(x + L * math.cos(ang), y + L * math.sin(ang))
        _stroke(ctx, 2, "#ffffff", 0.7 * a)
    ctx.restore()
    body_path(ctx, cx, infl=7)
    _stroke(ctx, 4.2, "#6f95b8", 0.95 * a)
    ax, ay = cx, YB - HGT - 7 * 1.1                                 # 上のひだ
    ctx.new_path()
    ctx.move_to(ax - 24, ay + 20)
    for i in range(5):
        ctx.curve_to(ax - 26 + i * 12.5, ay - 18, ax - 20 + i * 12.5, ay - 18, ax - 14 + i * 12.5, ay + 4)
    ctx.line_to(ax + 24, ay + 20)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.55 * a)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, "#6f95b8", 0.95 * a)
    ctx.restore()


def draw_sheet(ctx, cx, kind, u, t):
    """包む前の1枚の板（上から落ちてきて、おにぎりにかぶさる）。u = 0 → 1"""
    a = 1 - ease(clamp01((u - 0.78) / 0.22))
    if a <= 0:
        return
    e = ease(clamp01(u / 0.78))
    dy = -(1 - e) * 470.0
    rot = (1 - e) * (-0.22 if kind == "f" else 0.2)
    ctx.save()
    ctx.translate(cx, YB - HGT * 0.42 + dy)
    ctx.rotate(rot)
    w_, h_ = 2 * HALF + 70, HGT + 90
    core.rrect(ctx, -w_ / 2, -h_ / 2, w_, h_, 26)
    if kind == "f":
        g = cairo.LinearGradient(-w_ / 2, -h_ / 2, w_ / 2, h_ / 2)
        for off, col in ((0.0, "#9aa6b4"), (0.3, "#eef2f6"), (0.55, "#ffffff"), (0.8, "#c3ccd7"), (1.0, "#8d99a8")):
            g.add_color_stop_rgba(off, *hexrgb(col, a))
        ctx.set_source(g)
        ctx.fill_preserve()
        _stroke(ctx, 4, INK, 0.9 * a)
        ctx.save()
        core.rrect(ctx, -w_ / 2, -h_ / 2, w_, h_, 26)
        ctx.clip()
        ctx.translate(-cx, -(YB - HGT * 0.42))
        _crinkles(ctx, cx, 14, 30, 0.5 * a, 0.9 * a, HALF * 1.1)
        ctx.restore()
    else:
        ctx.set_source_rgba(*hexrgb("#e7f2fb", 0.32 * a))
        ctx.fill_preserve()
        _stroke(ctx, 3.6, "#6f95b8", 0.9 * a)
        ctx.move_to(-w_ / 2 + 30, -h_ / 2 + 36)
        ctx.line_to(-w_ / 2 + 30, -h_ / 2 + 140)
        _stroke(ctx, 8, "#ffffff", 0.8 * a)
    ctx.restore()


def draw_probe(ctx, cx, kind, T, done_t, t, a):
    """料理用の温度計（中心にさしてある）。上の表示は中心の温度。下の細い棒は 20〜70℃ のめもり"""
    if a <= 0:
        return
    top, bw, bh = APEX - 28 - 104, 184.0, 104.0
    # 棒（ごはんの中心まで）
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx, APEX - 28)
    ctx.line_to(cx, YB - 150)
    _stroke(ctx, 11, INK, 0.95 * a)
    ctx.move_to(cx, APEX - 28)
    ctx.line_to(cx, YB - 150)
    _stroke(ctx, 6, "#dfe4ea", a)
    ctx.move_to(cx - 1.5, APEX - 20)
    ctx.line_to(cx - 1.5, YB - 160)
    _stroke(ctx, 2, "#ffffff", 0.9 * a)
    # 表示
    core.rrect(ctx, cx - bw / 2, top, bw, bh, 16)
    ctx.set_source_rgba(1, 1, 1, 0.97 * a)
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95 * a)
    done = done_t is not None
    ny = top + 40
    text(ctx, f"{T:.0f}℃", cx, ny, 58, RED if done else INK, alpha=a)
    if done:
        note.pen_circle(ctx, cx, ny, 86, 40, RED, seed=70 + (kind == "w"), width=5, progress=clamp01((t - done_t) / 0.35), alpha=a)
    gx0, gw, gy = cx - 70, 140.0, top + 84
    core.rrect(ctx, gx0, gy - 8, gw, 16, 8)
    ctx.set_source_rgba(*hexrgb("#e4e8ee", a))
    ctx.fill()
    ww = max(gw * clamp01((T - 20.0) / 50.0), 12.0)
    core.rrect(ctx, gx0, gy - 8, ww, 16, 8)
    ctx.set_source_rgba(*hexrgb(COLS[kind], a))
    ctx.fill()
    core.rrect(ctx, gx0, gy - 8, gw, 16, 8)
    _stroke(ctx, 2.2, INK, 0.8 * a)


def draw_oni(ctx, t, kind, done_t):
    s = sample()
    st = kstate(t, kind)
    cx = CX[kind]
    ctx.save()                                                         # 影
    ctx.translate(cx, YB + 6)
    ctx.scale(HALF + 30, 15)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.3, 0.2, 0.1, 0.22)
    ctx.fill()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    u = clamp01((t - 0.0) / T_WRAP_DONE)
    pk = ease(clamp01((u - 0.6) / 0.4))                               # 包みが形になる（0〜1）
    draw_rice(ctx, cx, kind)
    if kind == "f":
        if pk > 0:
            draw_foil_pkg(ctx, cx, pk, t, st["steam"])
    else:
        if pk > 0:
            draw_wrap_pkg(ctx, cx, pk, t, st["fog"])
    if pk < 1:
        draw_sheet(ctx, cx, kind, u, t)
    draw_steam(ctx, cx, APEX + 14, 150, st["steam"], t, 11 if kind == "f" else 29, 1.0)
    draw_probe(ctx, cx, kind, st["read"], done_t, t, ease(clamp01((t - 1.0) / 0.3)))


def draw_labels(ctx, t, kind, done_t, a):
    s = sample()
    cx = CX[kind]
    cx_l = min(cx, 790.0) if kind == "w" else cx
    name = NAME[kind]
    y1, y2 = 1376.0, 1418.0
    wn = core.text_width(name, 38)
    xd = cx_l - wn / 2 - 34
    fill(ctx, (1, 1, 1, 0.92 * a))
    ctx.arc(xd, y1, 22, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, y1, 22, 22, INKC[kind], seed=13 + (kind == "w"), width=3.4, alpha=a)
    text(ctx, TAG[KIND_KEY[kind]], xd, y1, 30, INKC[kind], alpha=a)
    text(ctx, name, cx_l, y1, 38, INKC[kind], alpha=a)
    if done_t is None:
        lab = f"約{s['mass']:.0f}g・{s['T0']:.0f}℃から"
        text(ctx, lab, min(cx_l, 925.0 - core.text_width(lab, 26, False) / 2), y2, 26, INK, bold=False, alpha=a)
    else:
        u = clamp01((t - done_t) / 0.35)
        tc = s["c_" + kind]
        lab_a, lab_b = "この置き方なら ", f"{tc:.1f}℃"
        sz = 30.0
        while core.text_width(lab_a + lab_b, sz) > 270 and sz > 25:
            sz -= 1
        wa, wb = core.text_width(lab_a, sz), core.text_width(lab_b, sz)
        x0 = cx_l - (wa + wb) / 2
        x0 = min(x0, 925.0 - (wa + wb))
        text(ctx, lab_a, x0, y2, sz, INK, align="left", bold=False, alpha=a)
        text(ctx, lab_b, x0 + wa, y2, sz, RED, align="left", alpha=a)
        note.pen_circle(ctx, x0 + wa + wb / 2, y2, wb / 2 + 14, 22, RED, seed=80 + (kind == "w"), width=4, progress=u, alpha=a)


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    done = t_fin_done(t)
    mood = 1.0 if done is not None else 0.0
    ctx.push_group()
    ctx.save()
    clip_frame(ctx)
    ctx.save()
    zoom_art(ctx, t, CXP)
    draw_room(ctx)
    draw_person(ctx, CXP, t, mood)
    draw_table(ctx)
    draw_oni(ctx, t, "w", done)
    draw_oni(ctx, t, "f", done)
    draw_arms(ctx, CXP, t)
    ctx.restore()
    la = ease((t - 1.0) / 0.4)
    if la > 0:
        draw_labels(ctx, t, "f", done, la)
        draw_labels(ctx, t, "w", done, la)
    ctx.restore()
    border_frame(ctx)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def t_fin_done(t):
    return T_FIN if t >= T_FIN else None


def min_txt(minutes):
    mm = int(round(minutes))
    h, m = divmod(mm, 60)
    if h:
        return f"{h}時間" + (f"{m}分" if m else "")
    return f"{m}分"


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    s = sample()
    note.sticky(ctx, f"経過 {min_txt(tau_of(t))}", 580, 640, 40, "yellow", a=a, tilt=-0.02)
    if t < T_FIN:
        text(ctx, f"たとえば、この1回では（早送り）室温{s['Tr']:.0f}℃・台の上", 580, 726, 28, PENCIL, bold=False, alpha=a)
    else:
        text(ctx, f"たとえば、この1回では 差（アルミ−ラップ）{s['gap']:+.1f}℃", 580, 726, 28, PENCIL, bold=False, alpha=a)


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
    win_f = (r["c_f"] > r["c_w"]).astype(int)           # 1 = アルミのほうが冷めにくい（1時間後に温かい）
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_W), bgra(COL_F)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_f[:m]]
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


def deg_about(x):
    return f"約{abs(x):.1f}℃"


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
    text(ctx, "実験ではなく、計算での見立てです", 580, G_Y0 + G_ROWS * G_CELL + 26, 26, PENCIL, bold=False, alpha=a)   # 統括 10/27: 画面にも1回
    m = (int(n) // G_COLS) * G_COLS
    win_f = r["c_f"][:m] > r["c_w"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("f", int(win_f.sum())), ("w", int(m - win_f.sum())))):
            y = 1203 + i * 52
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
            lead = "アルミ" if sh["gap_med"] >= 0 else "ラップ"
            lead_p = sh["p_foil"] if sh["gap_med"] >= 0 else 1 - sh["p_foil"]
            note.sticky(ctx, f"{lead}が冷めにくい回は 約{pct_i(lead_p)}。\n差は 中央値で {deg_about(sh['gap_med'])}\n（中央値＝1万回の ちょうど真ん中の値）",
                        580, 1368, 30, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_foil"], sh["gap_med"])


def reason_text():
    sh = shown()
    k = answer_key()
    a, b = f"{sh['med_f']:.1f}", f"{sh['med_w']:.1f}"
    if k == "foil":
        return f"アルミの表面は 熱を出しにくい。\n1時間後の中央値は アルミ{a}℃・ラップ{b}℃"
    if k == "wrap":
        return f"ラップのほうが 冷めにくかった。\n1時間後の中央値は ラップ{b}℃・アルミ{a}℃"
    return f"1時間後の温度は ほぼ互角。\n中央値は アルミ{a}℃・ラップ{b}℃"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1218, 52, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        note.sticky(ctx, reason_text(), 580, 1348, 30, "blue", a=c, tilt=0.012)


# ---------- ひねり（タオルで包んだら） ----------
BAR_X0, BAR_W70 = 340.0, 520.0                     # 棒の左端、70℃ぶんの長さ


def twist_text():
    sh = shown()
    key = answer_by_rule(sh["p_foilt"], sh["gap_medt"])
    g, g0 = deg_about(sh["gap_medt"]), deg_about(sh["gap_med"])
    if key == "same":
        return f"タオルを足すと ほぼ同じ。\n差は 中央値で{g}（さっきは{g0}）\n外側がタオルになり 包みの差が消えた"
    lead = "アルミ" if key == "foil" else "ラップ"
    pr = sh["p_foilt"] if key == "foil" else 1 - sh["p_foilt"]
    return f"タオルがあっても {lead}が冷めにくい回が 約{pct_i(pr)}。\n差は 中央値で{g}（さっきは{g0}）"


def draw_bar(ctx, y, tc, kind, a, grow):
    wbar = BAR_W70 * tc / 70.0 * grow
    text(ctx, NAME[kind], 140, y, 34, INKC[kind], align="left", alpha=a)
    fill(ctx, hexrgb(COLS[kind], a))
    core.rrect(ctx, BAR_X0 + 40, y - 21, max(wbar, 1.0), 42, 8)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    core.rrect(ctx, BAR_X0 + 40, y - 21, max(wbar, 1.0), 42, 8)
    ctx.stroke()
    if grow > 0.98:
        text(ctx, f"{tc:.1f}℃", BAR_X0 + 40 + wbar + 14, y, 34, INK, align="left", alpha=a)


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
    note.sticky(ctx, "では、両方をタオルで包んだら？", 580, 690, 46, "yellow", fg=RED, a=a0, tilt=-0.02)
    if u > 0.6:
        text(ctx, "タオル1枚ぶんの断熱を足して、同じ1万回", 580, 772, 30, INK, bold=False, alpha=ease_out((u - 0.6) / 0.3))
    ua = u - 1.4
    if ua > 0:
        a = ease_out(ua / 0.3)
        text(ctx, "さっきの1万回（1時間後の中心の温度の中央値）", 140, 850, 30, INK, align="left", bold=False, alpha=a)
        g = ease(clamp01((ua - 0.2) / 0.8))
        draw_bar(ctx, 910, sh["med_f"], "f", a, g)
        draw_bar(ctx, 972, sh["med_w"], "w", a, g)
    ub = u - 3.6
    if ub > 0:
        a = ease_out(ub / 0.3)
        text(ctx, "どちらもタオルで包むと", 140, 1056, 30, INK, align="left", bold=False, alpha=a)
        g = ease(clamp01((ub - 0.2) / 0.8))
        draw_bar(ctx, 1116, sh["med_ft"], "f", a, g)
        draw_bar(ctx, 1178, sh["med_wt"], "w", a, g)
    uc = u - 6.4
    if uc > 0:
        note.sticky(ctx, twist_text(), 580, 1330, 30, "pink", fg=RED, a=ease_out(uc / 0.3), tilt=-0.012)
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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下で、おにぎりを包む（0秒目から動く）"""
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
        note.sticky(ctx, "あなたは、\nアルミ派？ラップ派？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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
    rng = np.random.default_rng(4)                                # ホイル・ラップを包むしゃかしゃかした音
    for k in range(9):
        t0 = 0.02 + k * 0.1 + rng.uniform(0, 0.04)
        dur = 0.12
        x = noise_band(dur, 2, 100 + k, 1.0)
        env = np.minimum(1, np.arange(len(x)) / SR / 0.01) * np.exp(-np.arange(len(x)) / SR / 0.05)
        mx.add(t0, x * env, 0.5)
    hiss_len = T_G0
    hiss = noise_band(hiss_len, 6, 9, 1.0)                        # 湯気のしゅー（だんだん小さく）
    th = np.arange(len(hiss)) / SR
    hiss = hiss * np.minimum(1, th / 0.5) * np.minimum(1, (hiss_len - th) / 0.5) * np.clip(1.0 - th / 22.0, 0.3, 1.0)
    mx.add(0.3, hiss, 0.08)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    mx.add(T_FIN, bell(784.0, 1.2), 0.45)                         # 1時間たった
    mx.add(T_FIN + 0.25, bell(659.3, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                           # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                                # ひねり
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
    checks = []
    checks.append(("損失なしで層がそろう温度（最大の食い違い・℃）", lump_check(), 0.0, 0.01))
    checks.append(("エネルギー保存（最大の食い違い・割合）", energy_check(), 0.0, 1e-4))
    checks.append(("きざみ 10秒 と 2.5秒 の差（最大・℃）", dt_check(), 0.0, 0.02))
    checks.append(("アルミとラップの値を同じにしたら差が出ない（最大・℃）", same_check(), 0.0, 1e-6))
    s = sample()
    checks.append(("見本のアルミの温度が1万回の値と同じ", s["chk"][0], s["c_f"], 1e-6))
    checks.append(("見本のラップの温度が1万回の値と同じ", s["chk"][1], s["c_w"], 1e-6))
    key = answer_by_rule(sh["p_foil"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（アルミ・ラップ）",
                   float(LABELS.index(NAME["f"]) * 10 + LABELS.index(NAME["w"])),
                   float("ABC".index(TAG["foil"]) * 10 + "ABC".index(TAG["wrap"])), 0.0))
    checks.append(("見本の差（℃）が中央値の近く", s["gap"], sh["gap_med"], max(0.12 * abs(sh["gap_med"]), 0.35)))
    checks.append(("アルミが温かい回＋ラップが温かい回", float(sh["n_foil"] + sh["n_wrap"]), float(N_TRIAL), 0.0))
    checks.append(("計算できなかった回（4つの合計）", float(sh["n_bad"]), 0.0, 0.0))
    meds = (sh["med_f"], sh["med_w"], sh["med_ft"], sh["med_wt"])
    checks.append(("1時間後の中心の温度の中央値が 室温〜70℃ に収まる（4つ）", float(all(12.0 <= x <= 70.0 for x in meds)), 1.0, 0.0))
    r = results()
    checks.append(("1時間後はどの回も初めの温度より下がっている", float(np.all(r["c_f"] < r["p"]["T0"]) and np.all(r["c_w"] < r["p"]["T0"])), 1.0, 0.0))
    checks.append(("ラップは、タオルを足すとどの回も冷めにくくなる", float(np.all(r["c_wt"] >= r["c_w"] - 1e-9)), 1.0, 0.0))
    print(f"  参考: アルミにタオルを足すと冷めやすくなった回 {float((r['c_ft'] < r['c_f']).mean()) * 100:.0f}%"
          f"（中央値で {float(np.median(r['c_ft'] - r['c_f'])):+.1f}℃）。外側の面が 光るアルミ から タオル（放射率0.9）に変わるため")
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
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  1時間 {T_FIN:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（アルミ {s['c_f']:.1f}℃ / ラップ {s['c_w']:.1f}℃）")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.7, 1.2, 2.5, 4.4, 5.2, 6.5, 8.0, 10.0, 12.0, T_FIN - 0.3, T_FIN + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 2.0, T_TW + 4.8, T_TW + 8.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
