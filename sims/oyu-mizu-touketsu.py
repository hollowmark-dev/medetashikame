"""お湯と水、冷凍庫で先に凍るのは？ 同じコップを2つ並べて1万回。— 2026-10-28 作成（ナレーションなし・45秒前後）

くらべるのは「コップの水が、中まで全部凍るのに何分かかるか」だけ。

モデル（コップ1つを1つの塊として、時間を細かく刻んで計算。水の中はよく混ざっているとする。コップ2つは別々に計算し、同じ庫内の空気を使う）
  段階1（液体）  (m·c_w + C_コップ)·dT/dt = −q_上 − q_横 − q_底 − L·ṁ        T は水とコップの温度。水は蒸発で減る
  ① 上の水面  q_上 = A_上·[h_上·(T−Ta) + ε·σ·(T⁴−Ta⁴)]  ＋ 蒸発 L(T)·ṁ
       ṁ = A_上·h_m·max(ρv(T) − RH·ρv氷(Ta), 0)    h_m = h_上 ÷ (ρ_空気·c_p·Le^(2/3))
       ρv は飽和水蒸気の濃さ（Buck の式）。庫内の空気は「霜の上の飽和（氷に対する飽和）」の RH 倍とした。蒸発した分だけ水も減る。
  ② 横   q_横 = A_横·[h_横·(T−Ta) + ε·σ·(T⁴−Ta⁴)]    h は温度差の 1/4 乗に比例（自然対流。温度差30Kのときの値を h0 とした）
  ③ 底（棚）  q_底 = A_底·g_底·(T−T棚)      g_底 = g_霜 + 固着·(g_固着 − g_霜)
       霜の上に置いたあいだは g_霜（霜がすきまを作って伝わりにくい）。コップが 0℃ より温かいと底の下の霜が溶けて、棚に氷でくっつき（固着）、
       g_固着 になる。溶ける速さ  d固着/dt = g_溶·max(T,0) ÷ (霜の量[kg/m²]·溶ける熱 334 kJ/kg)。お湯のコップのほうが早く固着する。
  過冷却  水は 0℃ を下回っても、凍り始める温度 −Δ に下がるまで凍らない。Δ はコップごとにでたらめ（お湯と水で向きの差は仮定しない）。
  段階2（凍り始め）  −Δ に下がった瞬間に氷ができ、水の温度は 0℃ に戻る（氷の量 = C·Δ ÷ 334 kJ/kg）。そのあとは 0℃ のまま、
       逃げる熱 ÷ 334 kJ/kg ぶんだけ氷が増える。全部が氷になった時刻 ＝「凍った」（絵では 上から氷が増えていく）。
  段階3（全部凍った）  あとは氷の温度が下がっていくだけ（絵のためだけ。時刻の比較には使わない）。
  時間は 5 秒きざみの 2次のルンゲ＝クッタ。1回ごとに2つのコップの条件をでたらめに変える（同じコップ・同じ棚・同じ庫内。はじめの温度・過冷却・霜の量の細かいちがいだけコップごと）。
  ＊ 凍る熱が大きいので、凍るまでの時間の大半は「凍る熱を逃がす時間」。過冷却の深さは、「全部凍る時刻」にはほとんど効かない
     （過冷却を 0 にしても 14℃まで深くしても答えはほぼ動かない。--model で確かめた）。「凍り始め」を測るか「全部凍る」を測るかで結論が変わりうる、が実験が割れる理由のひとつ。

  値の出典（確認できたもの。ページを実際に開いた）
    冷凍庫 −18℃以下（3つ星＝食品温度 −18℃以下・保存の目安 約3か月。JIS C 9607:2015 の試験条件）  https://jp.sharp/support/advice/refrigerator/select_a3.html
    冷凍食品の品温 −18℃以下（日本冷凍食品協会が維持・Codex も同じ。法律の義務ではない）        https://www.logi-today.com/95719
    水の比熱 4.18 kJ/(kg·K)（20℃で 4.1844、70℃で 4.1902）                                  https://www.engineeringtoolbox.com/specific-heat-capacity-water-d_660.html
    水が凍る熱 334 kJ/kg                                                                    https://www.engineeringtoolbox.com/latent-heat-melting-solids-d_96.html
    氷の比熱 約 2.2 kJ/(kg·K)（0℃で 2.22）                                                  https://www.engineeringtoolbox.com/ice-thermal-properties-d_576.html
    氷の熱伝導率 2.18 W/(m·K)・雪 0.05〜0.25・ガラス 0.96・磁器 1.5・PP 0.1〜0.22            https://www.engineeringtoolbox.com/thermal-conductivity-d_429.html
    蒸発の熱 2.501e6 − 2370·T [J/kg]（0℃ 2500.9・20℃ 2453.5・70℃ 2333.0 kJ/kg）              https://www.engineeringtoolbox.com/water-properties-d_1573.html
    水・氷の飽和水蒸気圧（Buck の式）                                                        https://en.wikipedia.org/wiki/Arden_Buck_equation
    ガラス c 0.84 kJ/kgK・磁器 1.07・プラスチック 1.67／ガラス ρ 2400〜2800・磁器 2300〜2500・PP 910〜940
                                                                                            https://www.engineeringtoolbox.com/specific-heat-solids-d_154.html
                                                                                            https://www.engineeringtoolbox.com/density-solids-d_1265.html
    水面の蒸発の速さの式 (25+19v)·(x_s−x) kg/(h·m²) …… 桁の確認に使った                  https://www.engineeringtoolbox.com/evaporation-water-surface-d_690.html
    0℃までは熱いほうが遅い（400g・ガラスのビーカー・−18〜−15℃で 0℃に着くまで 21.8℃→6397秒・57.3℃→9504秒・84.7℃→10812秒）。水の最大密度は 4℃
                                                                                            Burridge & Linden 2016, Sci. Rep. 6:37665  https://pmc.ncbi.nlm.nih.gov/articles/PMC5121640
    棚の霜が溶けて、お湯のコップが棚にくっつくと早く冷える（銅のコップ・霜5mm）／静かな水はほぼ −1℃より下まで過冷却／加熱で凍る温度が上がる・下がる・変わらないが水ごとにちがう
                                                                                            Brownridge 2011, Am. J. Phys. 79:78（arXiv 版） https://arxiv.org/pdf/1003.3185
    霜（氷の粒）だらけの冷凍庫では過冷却が起きず、凍りかけの長さは お湯のほうが短い（凍り始めは お湯のほうが遅い）。※ 査読の有無は確かめていない
                                                                                            Brownridge ほか 2025（arXiv） https://arxiv.org/pdf/2503.18820
    冷凍庫が凍る温度に近いときだけ（−7℃より高いとき、約1/3の回で）お湯が先／−8℃より低いと起きない。※ 査読の有無は確かめていない
                                                                                            Klimov & Finkelstein（arXiv） https://arxiv.org/pdf/2508.05607
    ＊ 上の計算を実験と突き合わせた: Burridge & Linden の条件（5cmの発泡スチロールの上・h=5 W/(m²K)）で 0℃までの時間が 実測の 0.97・1.04・1.01倍（--model で表示）
  仮定（出典なし。幅を持たせて、1回ごとにでたらめに変える）
    コップ … 直径 6.5〜8cm・高さ 9.5〜11.5cm・水 150〜260mL。ガラス45%（厚さ2〜3.5mm）・磁器25%（3〜5mm）・プラスチック30%（0.8〜1.5mm）
    庫内 … 空気 −21〜−15℃・棚は空気より 0〜3℃ 低い・空気の湿り（氷に対する）60〜100%
    熱の逃げ方 … 横の自然対流 h0 = 3.5〜6.5、上 h_上 = 3〜8 W/(m²K)（蒸発の上昇気流ぶんを含めた幅。Burridge & Linden との照合で 5 前後）、ルイス数 0.85〜0.90、放射率 0.95（水）・0.9（コップ）
                 **蒸発の強さ・庫内の風（ファン式か直冷式か）は確かめられなかった**。計算の結果を「実測」と言わない。
    底 … 霜の上の g_霜 = 8〜30、固着後の g_固着 = 40〜150 W/(m²K)。霜の量 0.1〜2.4 kg/m²（厚さ1〜8mm × 密度100〜300）、溶かす熱の通り g_溶 = 20〜150。
         **霜の熱伝導率・厚さ・密度、コップの底が霜を溶かす速さは確かめられなかった**（雪の 0.05〜0.25 が目安）。
         ＊ この仮定に答えが敏感: 霜が厚く溶けにくい（0.5〜5 kg/m²・g_溶 10〜50）と お湯が先になる（--model の表）。
    過冷却の深さ Δ … 0〜Smax（Smax は 1回ごとに 2〜8℃ からでたらめ）。2つのコップは別々の値。
         **家庭用冷凍庫・水道水・200mL の過冷却の深さの分布は確かめられなかった**（小さな密封管では −11.8℃など深い／霜だらけなら起きない、という幅だけ）。
    はじめの温度 … お湯 65〜75℃、水 15〜25℃（コップも同じ温度から）
  乱数 … 1回ごとに すべて 一様乱数。

問い: 「お湯と水、/ 冷凍庫で / 先に凍るのは？」（前提「同じコップ・同じ量・同じ冷凍庫（−18℃前後）」）
      選択肢: お湯（約70℃） ／ 水（20℃） ／ ほぼ同じ（記号の並びは LABELS。結果が「水」だったので、正解を B に置いた）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「水のほうが先に全部凍った回」の割合 p と、凍るまでの時間の差（お湯 − 水）の中央値 g で、
      p ≥ 60% かつ g ≥ 5分 なら「水」、p ≤ 40% かつ g ≤ −5分 なら「お湯」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、お湯が先に凍るのは、どんなとき？」→ お湯が先になった回に多い条件
      （霜・蒸発・過冷却の3つのうち、「ぜんぶの回」との差が いちばん大きい1つを自動で選ぶ。今回は 霜）。
締め: 「あなたは、お湯が先だと思っていましたか？」（答えは出さない）＋「コメントで教えてください」
言葉: 1万回の結果の真ん中は「中央値」（初出で一度説明）。見本の1回は「たとえば、この1回では」、その数字は「この置き方なら」。
      実験の結論が割れている題材なので、画面にも「計算での見立て」と小さく1回（答えの理由の下）。

乱数の種は見本（並んで凍る2つ）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "oyu-mizu-touketsu"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261108
DT = 5.0                                           # 足し算のきざみ（秒）
TMAX = 14 * 3600.0
C_W, C_ICE, L_F = 4180.0, 2200.0, 334.0e3          # 水・氷の比熱 J/(kg·K)、水が凍る熱 J/kg
SIGMA, EPS_W, EPS_C = 5.670e-8, 0.95, 0.90
RHOCP_AIR = 1.30 * 1006.0                          # 冷たい空気（−18℃ ≒ 1.38 kg/m³）の ρ·c_p のおおよそ
H_REF = 30.0                                       # h0 を決める温度差（K）
# 材料（確率, 密度 kg/m³ の幅, 比熱 J/kgK, 厚さ m の幅）。 0 = ガラス・1 = 磁器・2 = プラスチック
MATS = [(0.45, (2400.0, 2800.0), 840.0, (0.0020, 0.0035)),
        (0.25, (2300.0, 2500.0), 1070.0, (0.0030, 0.0050)),
        (0.30, (910.0, 940.0), 1670.0, (0.0008, 0.0015))]
CUP = dict(D=(0.065, 0.080), Hc=(0.095, 0.115), V=(150.0, 260.0))   # 直径・高さ m、水 mL
T_AIR, D_TS, RH_I = (-21.0, -15.0), (0.0, 3.0), (0.60, 1.00)
T0_HOT, T0_COLD = (65.0, 75.0), (15.0, 25.0)
H_SIDE, H_TOP, LEWIS = (3.5, 6.5), (3.0, 8.0), (0.85, 0.90)
G_UNB, G_BOND, G_MELT = (8.0, 30.0), (40.0, 150.0), (20.0, 150.0)
FROST_MASS = (0.1, 2.4)                            # 霜の量 kg/m²（厚さ1〜8mm × 密度100〜300 のおおよそ）
SMAX = (2.0, 8.0)                                  # 過冷却の深さの上限の幅（℃）
G_FOAM = 0.8                                       # 検証用: 断熱材（発泡スチロール 5cm）の上。0.035 W/(m·K) ÷ 0.05 m ≒ 0.7

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 5.0       # 割合・割合・分


def answer_by_rule(p_water, gap_med_min):
    """p_water = 水のほうが先に全部凍った回の割合、gap_med_min = (お湯 − 水) の凍るまでの時間の中央値（分）。'water' / 'same' / 'hot'"""
    if p_water >= RULE_HI and gap_med_min >= RULE_GAP:
        return "water"
    if p_water <= RULE_LO and gap_med_min <= -RULE_GAP:
        return "hot"
    return "same"


def p_sat_w(T):
    """水の飽和水蒸気圧（Pa）。Buck (1996)"""
    return 611.21 * np.exp((18.678 - T / 234.5) * (T / (257.14 + T)))


def p_sat_i(T):
    """氷の飽和水蒸気圧（Pa）。Buck (1996)"""
    return 611.15 * np.exp((23.036 - T / 333.7) * (T / (279.82 + T)))


def rho_of(p, T):
    return p * 0.018015 / (8.314 * (np.asarray(T, float) + 273.15))


def latent_v(T):
    return 2.501e6 - 2370.0 * np.asarray(T, float)


def draw_params(rng, n):
    """1万回ぶんの条件。2つのコップ（h = お湯・c = 水）で共有するものと、別々のもの"""
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    pm = np.array([m[0] for m in MATS])
    kind = rng.choice(len(MATS), size=n, p=pm / pm.sum())
    rho, cc, dl = np.zeros(n), np.zeros(n), np.zeros(n)
    for k, (_, rr, c_, ddl) in enumerate(MATS):
        mk = kind == k
        rho[mk] = rng.uniform(rr[0], rr[1], int(mk.sum()))
        cc[mk] = c_
        dl[mk] = rng.uniform(ddl[0], ddl[1], int(mk.sum()))
    d = dict(kind=kind, rho=rho, cc=cc, dl=dl, D=u(CUP["D"]), Hc=u(CUP["Hc"]), V=u(CUP["V"]),
             Ta=u(T_AIR), dTs=u(D_TS), RHi=u(RH_I), hs=u(H_SIDE), ht=u(H_TOP), Le=u(LEWIS),
             g_unb=u(G_UNB), g_bond=u(G_BOND), g_melt=u(G_MELT), fm=u(FROST_MASS), Smax=u(SMAX))
    for k in ("h", "c"):
        d["T0" + k] = u(T0_HOT if k == "h" else T0_COLD)
        d["dn" + k] = rng.uniform(0.0, 1.0, n) * d["Smax"]        # 過冷却の深さ（℃）
        d["fm" + k] = d["fm"] * rng.uniform(0.8, 1.2, n)          # 霜の量は棚の場所で少しちがう
    return d


def vessel(d, k, V=None):
    """コップ1つの入力（配列）。k = 'h'（お湯）/ 'c'（水）"""
    n = len(d["D"])
    return dict(D=d["D"], Hc=d["Hc"], V=(d["V"] if V is None else np.full(n, float(V))),
                rho=d["rho"], cc=d["cc"], dl=d["dl"], Ta=d["Ta"], dTs=d["dTs"], RHi=d["RHi"], hs=d["hs"], ht=d["ht"], Le=d["Le"],
                g_unb=d["g_unb"], g_bond=d["g_bond"], g_melt=d["g_melt"], fm=d["fm" + k], T0=d["T0" + k], dn=d["dn" + k])


def cat(vs):
    return {k: np.concatenate([v[k] for v in vs]) for k in vs[0]}


def geometry(v):
    A_top = math.pi * v["D"] ** 2 / 4
    h0 = v["V"] * 1e-6 / A_top
    return A_top, h0, math.pi * v["D"] * h0


class Sim:
    """コップ n 個ぶんを同時に冷やす。
    状態: T（水とコップの温度 ℃）・m（水の量 kg）・fix（棚への固着 0〜1）・mi（氷の量 kg）・phase（0 液体 / 1 凍りかけ / 2 全部氷）"""

    def __init__(self, v, mode="shelf"):
        self.v = v
        self.mode = mode                                # "shelf" = 棚に置く / "foam" = 断熱材の上（検証用）
        self.n = len(v["D"])
        self.A_top, self.h0, self.A_side = geometry(v)
        self.m = v["V"] * 1e-6 * 1000.0
        self.T = v["T0"].astype(float).copy()
        self.fix = np.zeros(self.n)
        self.mi = np.zeros(self.n)
        self.phase = np.zeros(self.n, int)
        self.Ccup = v["rho"] * v["cc"] * v["dl"] * (self.A_side + self.A_top)
        self.Ts = v["Ta"] - v["dTs"]
        self.rv_air = v["RHi"] * rho_of(p_sat_i(v["Ta"]), v["Ta"])
        self.hm = v["ht"] / (RHOCP_AIR * v["Le"] ** (2.0 / 3.0))
        self.Q = np.zeros(self.n)                       # 外へ逃げた熱の合計（J）。エネルギー保存の照合用
        self.t = 0.0
        self.t_nuc = np.full(self.n, np.inf)
        self.t_frz = np.full(self.n, np.inf)
        self.t_zero = np.full(self.n, np.inf)           # 初めて 0℃ になった時刻
        self.t_fixed = np.full(self.n, np.inf)          # 固着が 0.9 を超えた時刻
        self.fix_zero = np.full(self.n, np.nan)         # 0℃になった時点での固着の割合
        self.evap = np.zeros(self.n)                    # 蒸発した水の量（kg）

    def _ho(self, T, h0):
        return h0 * (np.maximum(np.abs(T - self.v["Ta"]), 2.0) / H_REF) ** 0.25

    def rates(self, T, m, fix, mi, phase):
        v = self.v
        Ta = v["Ta"]
        Tw = np.where(phase == 1, 0.0, T)
        TK, TaK = Tw + 273.15, Ta + 273.15
        q_side = self.A_side * (self._ho(Tw, v["hs"]) * (Tw - Ta) + EPS_C * SIGMA * (TK ** 4 - TaK ** 4))
        q_top = self.A_top * (self._ho(Tw, v["ht"]) * (Tw - Ta) + EPS_W * SIGMA * (TK ** 4 - TaK ** 4))
        if self.mode == "foam":
            g_b = G_FOAM + 0 * Tw
            dfix = 0.0 * Tw
        else:
            g_b = v["g_unb"] + fix * (v["g_bond"] - v["g_unb"])
            dfix = v["g_melt"] * np.maximum(T, 0.0) / (v["fm"] * L_F) * (phase == 0) * (fix < 1.0)
        q_bot = self.A_top * g_b * (Tw - self.Ts)
        mdot = np.where(phase < 2, self.A_top * self.hm * np.maximum(rho_of(p_sat_w(Tw), Tw) - self.rv_air, 0.0), 0.0)
        Lv = latent_v(Tw)
        qtot = q_side + q_top + q_bot
        dT = np.where(phase == 0, -(qtot + Lv * mdot) / (m * C_W + self.Ccup),
                      np.where(phase == 2, -qtot / (m * C_ICE + self.Ccup), 0.0))
        dmi = np.where(phase == 1, (qtot + Lv * mdot) / L_F, 0.0)
        dQ = np.where(phase == 0, qtot + Lv * mdot + C_W * mdot * T, np.where(phase == 1, qtot + Lv * mdot, 0.0))
        return dT, -mdot, dfix, dmi, dQ, mdot

    def step(self, dt=DT):
        s = (self.T, self.m, self.fix, self.mi, self.Q)
        ph = self.phase
        k1 = self.rates(s[0], s[1], s[2], s[3], ph)
        k2 = self.rates(s[0] + dt / 2 * k1[0], s[1] + dt / 2 * k1[1], np.minimum(1.0, s[2] + dt / 2 * k1[2]), s[3] + dt / 2 * k1[3], ph)
        Tn, mn = s[0] + dt * k2[0], s[1] + dt * k2[1]
        fn, mi_n, Qn = np.minimum(1.0, s[2] + dt * k2[2]), s[3] + dt * k2[3], s[4] + dt * k2[4]
        self.evap += dt * k2[5]
        # 凍り始め（過冷却の深さまで下がった）
        hit = (ph == 0) & (Tn <= -self.v["dn"])
        if hit.any():
            fr = np.clip((s[0] + self.v["dn"]) / np.maximum(s[0] - Tn, 1e-12), 0, 1)
            self.t_nuc = np.where(hit & np.isinf(self.t_nuc), self.t + fr * dt, self.t_nuc)
            mi_new = np.minimum((mn * C_W + self.Ccup) * np.maximum(-Tn, 0.0) / L_F, mn)      # 過冷却ぶんが氷になる
            mi_n = np.where(hit, mi_new, mi_n)
            Tn = np.where(hit, 0.0, Tn)
            self.phase = np.where(hit, 1, ph)
        # 全部凍った
        done = (self.phase == 1) & (mi_n >= mn) & (ph == self.phase)
        if done.any():
            g0, g1 = s[1] - s[3], mn - mi_n
            fr = np.clip(g0 / np.maximum(g0 - g1, 1e-15), 0, 1)
            self.t_frz = np.where(done & np.isinf(self.t_frz), self.t + fr * dt, self.t_frz)
            self.phase = np.where(done, 2, self.phase)
            Tn = np.where(done, 0.0, Tn)
            mi_n = np.where(done, mn, mi_n)
        hz = np.isinf(self.t_zero) & (Tn <= 0.0) & (s[0] > 0.0)
        self.t_zero = np.where(hz, self.t + dt * np.clip(s[0] / np.maximum(s[0] - Tn, 1e-12), 0, 1), self.t_zero)
        self.fix_zero = np.where(hz, fn, self.fix_zero)
        self.t_fixed = np.where(np.isinf(self.t_fixed) & (fn >= 0.9), self.t + dt, self.t_fixed)
        self.T, self.m, self.fix, self.mi, self.Q = Tn, mn, fn, mi_n, Qn
        self.t += dt

    def enthalpy(self):
        """水とコップが持つ熱（0℃の水＋コップ を 0 として）。氷はその分だけ低い"""
        return (self.m * C_W + self.Ccup) * self.T - self.mi * L_F

    def mdot0(self):
        """配列の先頭の蒸発の速さ kg/s"""
        if self.phase[0] >= 2:
            return 0.0
        Tw = 0.0 if self.phase[0] == 1 else self.T[0]
        return float(self.A_top[0] * self.hm[0] * max(float(rho_of(p_sat_w(Tw), Tw)) - self.rv_air[0], 0.0))

    def run(self, dt=DT, hist=False):
        """全部凍った時刻（秒）を返す。hist=True なら記録（t, T, 氷の割合, 固着, 蒸発 ṁ, 水の量）も（凍ったあと30分まで）"""
        H = [(0.0, self.T[0], 0.0, self.fix[0], self.mdot0(), self.m[0])] if hist else None
        while self.t < TMAX:
            if hist:
                if not np.isinf(self.t_frz[0]) and self.t > self.t_frz[0] + 1800.0:
                    break
            elif not np.isinf(self.t_frz).any():
                break
            self.step(dt)
            if hist:
                H.append((self.t, self.T[0], float(self.mi[0] / self.m[0]) if self.phase[0] >= 1 else 0.0, self.fix[0],
                          self.mdot0(), self.m[0]))
        return (self.t_frz.copy(), np.array(H)) if hist else self.t_frz.copy()
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
    keys = ("t_frz", "t_nuc", "t_zero", "t_fixed", "evap", "fix_zero")
    if fn.exists():
        z = np.load(fn)
        r = {k: z[k] for k in keys}
    else:
        s = Sim(cat([vessel(d, "h"), vessel(d, "c")]))
        s.run()
        r = dict(t_frz=s.t_frz, t_nuc=s.t_nuc, t_zero=s.t_zero, t_fixed=s.t_fixed, evap=s.evap, fix_zero=s.fix_zero)
        np.savez(fn, **r)
    n = N_TRIAL
    for k in ("t_frz", "t_nuc", "t_zero", "t_fixed"):
        r[k] = r[k] / 60.0                          # 分
    out = dict(p=d)
    for i, k in enumerate(("h", "c")):
        for kk in keys:
            out[kk + "_" + k] = r[kk][i * n:(i + 1) * n]
    out["evap_h"], out["evap_c"] = out["evap_h"] * 1000.0, out["evap_c"] * 1000.0    # g
    _RES["m"] = out
    return out


def twist_factors():
    """お湯が先に凍った回に多い条件を、霜・蒸発・過冷却の3つで比べる。
    それぞれ「ぜんぶの回」と「お湯が先だった回」の平均の差を、ぜんぶの回のばらつきで割って（標準化して）くらべ、差がいちばん大きいものを選ぶ"""
    r = results()
    hot_first = r["t_frz_h"] < r["t_frz_c"]
    cand = {
        # 名前: (1回ごとの値, 単位, 表示の小数桁)
        "frost": (r["fix_zero_c"] * 100.0, "%", 0),                             # 水のコップが 0℃になるまでに、棚にくっついた割合
        "evap": (r["evap_h"], "g", 1),                                          # お湯のコップから蒸発した水
        "super": (r["p"]["dnc"] - r["p"]["dnh"], "℃", 1),                       # 水のコップの過冷却 − お湯のコップの過冷却
    }
    out = {}
    for k, (x, unit, nd) in cand.items():
        sd = float(np.std(x))
        out[k] = dict(all_med=float(np.median(x)), hf_med=float(np.median(x[hot_first])) if hot_first.any() else float("nan"),
                      z=(float(np.mean(x[hot_first]) - np.mean(x)) / sd) if (sd > 0 and hot_first.any()) else 0.0, unit=unit, nd=nd)
    best = max(out, key=lambda k: abs(out[k]["z"]))
    return best, out


def shown():
    r = results()
    th, tc = r["t_frz_h"], r["t_frz_c"]
    gap = th - tc
    best, fac = twist_factors()
    return dict(p_water=float((tc < th).mean()), n_water=int((tc < th).sum()), n_hot=int((tc >= th).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_h=float(np.median(th)), med_c=float(np.median(tc)), q_h=np.percentile(th, [10, 90]), q_c=np.percentile(tc, [10, 90]),
                n_unfinished=int(np.isinf(th).sum() + np.isinf(tc).sum()), best=best, fac=fac,
                zero_h=float(np.median(r["t_zero_h"])), zero_c=float(np.median(r["t_zero_c"])),
                fix_h=float(np.nanmedian(np.where(np.isinf(r["t_fixed_h"]), np.nan, r["t_fixed_h"]))), fix_c=float(np.nanmedian(np.where(np.isinf(r["t_fixed_c"]), np.nan, r["t_fixed_c"]))),
                evap_h=float(np.median(r["evap_h"])), evap_c=float(np.median(r["evap_c"])))


def hm_(minutes):
    """分 → '2時間54分' / '45分'"""
    mm = int(round(minutes))
    h, m = divmod(mm, 60)
    return f"{h}時間{m:02d}分" if h else f"{m}分"


def report():
    sh = shown()
    print(f"水が先 {sh['p_water']:.4f}（{sh['n_water']}回 / お湯が先 {sh['n_hot']}回）  差(お湯−水)の中央値 {sh['gap_med']:+.2f}分 "
          f"平均 {sh['gap_mean']:+.2f}  10/25/75/90% {np.round(sh['gap_q'], 1)}")
    print(f"  答え {answer_by_rule(sh['p_water'], sh['gap_med'])}")
    print(f"  全部凍るまでの中央値 お湯 {sh['med_h']:.1f}分（{hm_(sh['med_h'])}） 10/90% {np.round(sh['q_h'], 1)} / "
          f"水 {sh['med_c']:.1f}分（{hm_(sh['med_c'])}） 10/90% {np.round(sh['q_c'], 1)}  未完了 {sh['n_unfinished']}")
    print(f"  0℃になるまでの中央値 お湯 {sh['zero_h']:.1f}分 / 水 {sh['zero_c']:.1f}分  棚にくっつくまで お湯 {sh['fix_h']:.1f}分 / 水 {sh['fix_c']:.1f}分  "
          f"蒸発 お湯 {sh['evap_h']:.1f}g / 水 {sh['evap_c']:.1f}g")
    print("  ひねり（お湯が先だった回に多い条件）:", sh["best"])
    for k, v in sh["fac"].items():
        print(f"    {k:6s} ぜんぶ {v['all_med']:.2f}{v['unit']} → お湯が先 {v['hf_med']:.2f}{v['unit']}  標準化した差 {v['z']:+.2f}")


# 条件を変えて、答えがどれだけ動くか（言い切ってよい範囲を知るための確認）。各 3000回
def sensitivity(n=3000):
    rows = []
    cases = [("もとの置き方", {}),
             ("過冷却なし", dict(SMAX=(0.0, 0.0))),
             ("過冷却が深い 6〜14℃", dict(SMAX=(6.0, 14.0))),
             ("蒸発が強い（h_上 2倍・庫内が乾いている）", dict(H_TOP=(6.0, 16.0), RH_I=(0.3, 0.6))),
             ("棚に霜がない（固着しない）", dict(G_BOND=(8.0, 30.0))),
             ("霜が厚く溶けにくい（0.5〜5 kg/m²・g_溶 10〜50）", dict(FROST_MASS=(0.5, 5.0), G_MELT=(10.0, 50.0))),
             ("冷凍庫がゆるい −15〜−12℃", dict(T_AIR=(-15.0, -12.0)))]
    g = globals()
    for label, kw in cases:
        saved = {k: g[k] for k in kw}
        g.update(kw)
        d = draw_params(np.random.default_rng(1), n)
        s = Sim(cat([vessel(d, "h"), vessel(d, "c")]))
        t = s.run() / 60.0
        g.update(saved)
        th, tc = t[:n], t[n:]
        rows.append((label, float((tc < th).mean()), float(np.median(th - tc)), float(np.median(tc)), float(np.median(th))))
    return rows


def bl_check():
    """Burridge & Linden (2016) の実験: 400g・ガラスのビーカー（直径9.0cm・水深6.3cm）を 5cm の発泡スチロールの上に置き、
    冷凍庫（−18〜−15℃）で 0℃になるまで。21.8℃→6397秒・57.3℃→9504秒・84.7℃→10812秒。計算の側は h_横 = h_上 = 5 W/(m²K)（このモデルの幅の真ん中）"""
    obs = np.array([6397.0, 9504.0, 10812.0])
    n = 3
    v = dict(D=np.full(n, 0.09), Hc=np.full(n, 0.10), V=np.full(n, 400.7), rho=np.full(n, 2230.0), cc=np.full(n, 750.0), dl=np.full(n, 0.0025),
             Ta=np.full(n, -16.5), dTs=np.zeros(n), RHi=np.full(n, 0.8), hs=np.full(n, 5.0), ht=np.full(n, 5.0), Le=np.full(n, 0.875),
             g_unb=np.zeros(n), g_bond=np.zeros(n), g_melt=np.zeros(n), fm=np.ones(n), T0=np.array([21.8, 57.3, 84.7]), dn=np.zeros(n))
    s = Sim(v, mode="foam")
    while np.isinf(s.t_zero).any() and s.t < 40000:
        s.step(5.0)
    return s.t_zero, obs


def dt_check():
    d = {k: v[:200] for k, v in draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL).items()}
    v = cat([vessel(d, "h"), vessel(d, "c")])
    a = Sim(v).run(dt=5.0)
    b = Sim(v).run(dt=1.25)
    return float(np.max(np.abs(a - b)) / 60.0)


def energy_check():
    """熱の損失を足していくと、水とコップが持つ熱の減りと同じになる（相対誤差の最大。凍り始めの跳びも含む。3000秒のあいだ）"""
    d = {k: v[:300] for k, v in draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL).items()}
    s = Sim(cat([vessel(d, "h"), vessel(d, "c")]))
    e0 = s.enthalpy() + 0.0
    ref = (s.m * C_W + s.Ccup) * s.T
    for _ in range(int(3000 / DT)):
        s.step(DT)
    err = np.abs((e0 - s.enthalpy()) - s.Q) / ref
    return float(np.max(err))


def conserve_check():
    """水の量: 最初の水 − 蒸発 = 今の水"""
    d = {k: v[:100] for k, v in draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL).items()}
    s = Sim(cat([vessel(d, "h"), vessel(d, "c")]))
    m0 = s.m.copy()
    for _ in range(int(3000 / DT)):
        s.step(DT)
    return float(np.max(np.abs(m0 - s.evap - s.m)))


def diag():
    sh = shown()
    print("  条件を変えたときの答え（3000回ずつ。答えの規則は同じ）:")
    for label, p, g, mc, mh in sensitivity():
        print(f"    {label:38s} 水が先 {p * 100:5.1f}%  差(お湯−水)の中央値 {g:+6.1f}分  凍るまで 水 {mc:.0f}分 / お湯 {mh:.0f}分  → {answer_by_rule(p, g)}")
    z, obs = bl_check()
    print("  Burridge & Linden の実験との照合（0℃になるまで）:",
          "  ".join(f"{T}℃ 計算{x:.0f}秒/実測{o:.0f}秒（{x / o:.2f}倍）" for T, x, o in zip((21.8, 57.3, 84.7), z, obs)))


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    diag()
    print(f"  エネルギー保存の食い違い（最大・割合）: {energy_check():.2e}  水の量の食い違い（最大・kg）: {conserve_check():.2e}  "
          f"きざみ 5秒 と 1.25秒 の差（最大・分）: {dt_check():.4f}")
    sys.exit(0)


# =====================================================================
# 見本（並んで凍る2つ）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 差が中央値の近く（±15%）、お湯の時間・水の時間とも中央値の近く（±12%）、ガラスのコップ、直径 6.8〜7.6cm・水 190〜230mL
          （絵にしたときの形がそろう）、2つとも過冷却の深さが 0.5〜4℃。その中で差が中央値に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    th, tc = r["t_frz_h"], r["t_frz_c"]
    gap = th - tc
    ok = (np.abs(gap / sh["gap_med"] - 1) < 0.15) & (np.abs(th / sh["med_h"] - 1) < 0.12) & (np.abs(tc / sh["med_c"] - 1) < 0.12)
    ok &= (p["kind"] == 0) & (p["D"] >= 0.068) & (p["D"] <= 0.076) & (p["V"] >= 190) & (p["V"] <= 230)
    ok &= (p["dnh"] >= 0.5) & (p["dnh"] <= 4.0) & (p["dnc"] >= 0.5) & (p["dnc"] <= 4.0) & (gap > 0)
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    sh_, hh = Sim(vessel(d1, "h")).run(hist=True)
    sc_, hc = Sim(vessel(d1, "c")).run(hist=True)
    q = {k: float(v[i]) for k, v in p.items()}
    D, V = q["D"] * 100, q["V"]
    _SAMPLE = dict(i=i, p=q, t_h=float(th[i]), t_c=float(tc[i]), gap=float(gap[i]), h_h=hh, h_c=hc,
                   chk=(float(sh_[0]) / 60.0, float(sc_[0]) / 60.0), D=D, V=V, Hc=q["Hc"] * 100, dl=q["dl"] * 1000,
                   T0=dict(h=q["T0h"], c=q["T0c"]), Ta=q["Ta"])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    print("見本", s["i"], "コップ 口", round(s["D"], 2), "cm 高さ", round(s["Hc"], 2), "水", round(s["V"]), "mL 厚", round(s["dl"], 1), "mm",
          "はじめ お湯", round(s["T0"]["h"], 1), "水", round(s["T0"]["c"], 1), "庫内", round(s["Ta"], 1), "| お湯", round(s["t_h"], 1), "分 水",
          round(s["t_c"], 1), "分 差", round(s["gap"], 1), "分")
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
note.DATE = "11.8"                                 # 日付欄（公開予定日）

COL_H, INK_H = "#f4ad6a", "#b8601a"                # お湯（だいだい）
COL_C, INK_C = "#8fbbe8", "#2f63a8"                # 水（水色）
WATER_COLD, WATER_HOT = "#bfe3f5", "#f6d3b0"
ICE_COL = "#ffffff"
WALL_COLD, WALL_HOT = "#e8f3f8", "#f2a878"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["お湯（約70℃）", "水（20℃）", "ほぼ同じ"]
TAG = {"hot": "A", "water": "B"}
CORRECT = 1                                        # answer_by_rule の結果の位置（B）
KEY_LABEL = {"hot": "お湯（約70℃）", "same": "ほぼ同じ", "water": "水（20℃）"}
KEY_NAME = {"hot": "お湯", "same": "ほぼ同じ", "water": "水"}
NAME = {"h": "お湯", "c": "水"}
KIND_KEY = {"h": "hot", "c": "water"}
COLS = {"h": COL_H, "c": COL_C}
INKC = {"h": INK_H, "c": INK_C}

BIG_Q = ["お湯と水、冷凍庫で", "先に凍るのは？"]                  # 定位置（上）の2行
BIG_Q3 = ["お湯と水、", "冷凍庫で", "先に凍るのは？"]               # 1コマ目の3行（同じ大きさ）
DETAIL = "同じコップ・同じ量・同じ冷凍庫（−18℃前後）"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
T_P = 1.2                                          # 扉が開き終わる
RACE_LEN = 9.0                                     # T_GO から2つとも全部凍るまで
R0 = 0.9                                           # 扉が開いたあとの進み（シミュの分／動画の秒）

# ---------- 画面の置き場所 ----------
FR = (80.0, 830.0, 1020.0, 1480.0)                 # 絵の枠 x0, y0, x1, y1
S = 29.0                                           # 1cm = 29px
YB = 1290.0                                        # コップの底（棚の上）
CXH, CXW = 562.0, 830.0
CX = {"h": CXH, "c": CXW}
IX0, IX1, IY0, IY1 = 380.0, 1000.0, 852.0, 1478.0  # 冷凍庫の中（開口部）
Y_T0, Y_K = 1195.0, 4.0                            # 温度計: 0℃の高さ、1℃あたりのpx
PX = 203.0                                         # 人の中心 x


def th_y(T):
    return Y_T0 - T * Y_K


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_h"], s["t_c"]))
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
        MDOT_REF = max(float(s["h_h"][0, 4]), float(s["h_c"][0, 4]))
    return MDOT_REF


def kstate(t, kind):
    """その時刻の コップの状態: 温度計の読み・氷の割合・棚への固着・湯気の量"""
    s = sample()
    h = s["h_" + kind]
    sec = tau_of(t) * 60.0
    T = float(np.interp(sec, h[:, 0], h[:, 1]))
    ice = float(np.interp(sec, h[:, 0], h[:, 2]))
    fix = float(np.interp(sec, h[:, 0], h[:, 3]))
    md = float(np.interp(sec, h[:, 0], h[:, 4]))
    appear = ease(clamp01((t - 0.2) / 0.9))
    return dict(read=T, ice=ice, fix=fix, steam=md / mdot_ref() * appear)


def num_txt(x):
    return f"{x:.0f}℃".replace("-", "−")


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def lerp_col(c0, c1, u):
    a, b = hexrgb(c0), hexrgb(c1)
    return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))


def wall_col(T):
    return lerp_col(WALL_COLD, WALL_HOT, clamp01((T - 10.0) / 60.0))


def water_col(T):
    return lerp_col(WATER_COLD, WATER_HOT, clamp01((T - 10.0) / 60.0))


def clip_frame(ctx):
    core.rrect(ctx, FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1], 22)
    ctx.clip()


def border_frame(ctx):
    core.rrect(ctx, FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1], 22)
    _stroke(ctx, 3.5, INK, 0.75)


ZOOM0, ZOOM_T = 1.18, 1.25


def zoom_art(ctx, t, cx):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(cx, 1155.0)
    ctx.scale(z, z)
    ctx.translate(-cx, -1155.0)


def poly_path(ctx, pts):
    ctx.new_path()
    for i, (x, y) in enumerate(pts):
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()


def vessel_poly(cx, rim_y, top_half, bot_half, y_bot, ch=14.0):
    """コップの断面（左右対称）。底の角は面取り"""
    ch = min(ch, bot_half * 0.5)
    return [(cx - top_half, rim_y), (cx - bot_half, y_bot - ch), (cx - bot_half + ch, y_bot),
            (cx + bot_half - ch, y_bot), (cx + bot_half, y_bot - ch), (cx + top_half, rim_y)]


def geom(kind):
    s = sample()
    Dp, Hp = s["D"] * S, s["Hc"] * S
    dp = max(s["dl"] / 10.0 * S, 6.0)
    top_half = Dp / 2 + dp
    bot_half = top_half * 0.9
    h_cm = s["V"] / (math.pi * (s["D"] / 2) ** 2)                     # 水の高さ cm = V[cm³] ÷ 面積[cm²]
    return dict(Dp=Dp, Hp=Hp, dp=dp, top_half=top_half, bot_half=bot_half, rim_y=YB - Hp, h_px=h_cm * S, cx=CX[kind])


# ---------- 絵: 人 ----------
SKIN, HAIR_C, SWEATER, SWEATER_D, PANTS_C = "#f6dcc6", "#3a2f2a", "#e8806d", "#c85f4e", "#46557a"


def thick(ctx, pts, w, col, outline=3.5):
    """太い線（ふちどり付き）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.92), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


def ik2(sx, sy, wx, wy, l1, l2):
    """肩 (sx, sy) と手首 (wx, wy) から、ひじの位置（2つの解のうち下のほう）"""
    dx, dy = wx - sx, wy - sy
    d = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 2.0, math.hypot(dx, dy)))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    bx, by = sx + a * ux, sy + a * uy
    c1 = (bx - h * uy, by + h * ux)
    c2 = (bx + h * uy, by - h * ux)
    return c1 if (c1[1] + 0.6 * c1[0]) > (c2[1] + 0.6 * c2[0]) else c2     # 下・外向きのほう


def draw_hand(ctx, x, y, ang, kind):
    """手。ang = 前腕の向き（指の向き）。kind: 'fist'（にぎる）/ 'open'（ひらく）"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def capsule(x0, y0, x1, y1, w):
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.set_source_rgba(*hexrgb(INK, 0.92))
        ctx.set_line_width(w + 6.5)
        ctx.stroke()
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.set_line_width(w)
        ctx.stroke()

    if kind == "open":
        for k, yy in enumerate((-14, -5, 4, 13)):                       # 4本の指
            capsule(24, yy, 24 + 22 - 3 * abs(k - 1.5), yy * 1.05, 9.0)
        capsule(8, -19, 24, -33, 10.0)                                    # 親指
    else:
        for yy in (-12, -4, 4, 12):                                       # 曲げた指
            capsule(26, yy, 31, yy, 9.5)
        capsule(14, -18, 30, -9, 10.0)                                    # 親指をかぶせる
    ctx.save()                                                            # 手のひら
    ctx.translate(14, 0)
    ctx.scale(1.0, 0.92)
    ctx.arc(0, 0, 19, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.92)
    ctx.restore()


def draw_person(ctx, t, mood, hold_x, hold_w=1.0):
    """冷凍庫の前に立つ人（腰から上を大きく、ひざから下は枠の外）。mood 0 = 考え中（あごに手）、1 = にっこり（手をあげる）。
    hold_x = 扉の取っ手の x（扉を引いているあいだだけ手をそえる。None なら離す）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx = PX
    K, AX, AY = 1.10, PX + 10.0, 1480.0                                   # 絵全体を少し大きく（足もとの高さを基準に）
    ctx.save()
    ctx.translate(AX, AY)
    ctx.scale(K, K)
    ctx.translate(-AX, -AY)
    bob = 2.5 * math.sin(t * 1.7)
    hx, hy = cx + 8, 962.0 + bob
    sh_y = 1078.0 + bob
    # 足（ズボン）
    for sg in (-1, 1):
        core.rrect(ctx, cx + sg * 44 - 40, 1300, 80, 260, 26)
        ctx.set_source_rgba(*hexrgb(PANTS_C))
        ctx.fill_preserve()
        _stroke(ctx, 4, INK, 0.92)
    ctx.move_to(cx, 1322)
    ctx.line_to(cx, 1480)
    _stroke(ctx, 3.5, INK, 0.7)
    # 奥のうで（人から見て左・まっすぐ下ろす）
    thick(ctx, [(cx - 88, sh_y + 20), (cx - 102, sh_y + 130), (cx - 98, sh_y + 214)], 36, SWEATER, 3.5)
    thick(ctx, [(cx - 98, sh_y + 196), (cx - 98, sh_y + 214)], 36, SWEATER_D, 3.5)
    draw_hand(ctx, cx - 98, sh_y + 222, math.pi / 2, "fist")
    # 胴（セーター）
    ctx.new_path()
    ctx.move_to(cx - 30, sh_y - 30)
    ctx.curve_to(cx - 70, sh_y - 22, cx - 112, sh_y - 6, cx - 104, sh_y + 52)
    ctx.line_to(cx - 90, 1322)
    ctx.line_to(cx + 90, 1322)
    ctx.line_to(cx + 104, sh_y + 52)
    ctx.curve_to(cx + 112, sh_y - 6, cx + 70, sh_y - 22, cx + 30, sh_y - 30)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(SWEATER))
    ctx.fill_preserve()
    _stroke(ctx, 4.5, INK, 0.95)
    core.rrect(ctx, cx - 91, 1296, 182, 28, 12)                          # すその編み目
    ctx.set_source_rgba(*hexrgb(SWEATER_D))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    for k in range(-4, 5):
        ctx.move_to(cx + k * 20, 1300)
        ctx.line_to(cx + k * 20, 1320)
    _stroke(ctx, 2.0, INK, 0.35)
    # えり（丸首）と首
    core.rrect(ctx, cx - 21, hy + 50, 42, 52, 12)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.92)
    ctx.save()
    ctx.translate(cx, sh_y - 26)
    ctx.scale(1.0, 0.42)
    ctx.arc(0, 0, 42, 0, math.pi)
    ctx.restore()
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(SWEATER_D))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.92)
    # 頭
    ctx.new_path()                                                       # 後ろ髪
    ctx.arc(hx - 12, hy + 2, 70, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(HAIR_C))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    ctx.save()                                                           # 顔
    ctx.translate(hx, hy + 6)
    ctx.scale(1.0, 1.06)
    ctx.arc(0, 0, 60, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    ctx.arc(hx - 58, hy + 10, 13, 0, 2 * math.pi)                        # 耳
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.new_path()                                                       # 前髪（右へ流す）
    ctx.move_to(hx - 62, hy - 6)
    ctx.curve_to(hx - 66, hy - 62, hx + 2, hy - 80, hx + 46, hy - 58)
    ctx.curve_to(hx + 62, hy - 48, hx + 64, hy - 26, hx + 58, hy - 14)
    ctx.curve_to(hx + 36, hy - 40, hx + 8, hy - 44, hx - 30, hy - 30)
    ctx.curve_to(hx - 44, hy - 24, hx - 54, hy - 14, hx - 62, hy - 6)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(HAIR_C))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.95)
    # 目（右の冷凍庫のほうを見る）・まゆ・鼻・口
    gaze = 5.0 + 3.0 * math.sin(t * 1.15)
    blink = (t % 3.1) < 0.12
    for sg, (ex_, rr) in enumerate(((hx - 20, 13.0), (hx + 30, 11.0))):
        ey_ = hy + 6
        if blink or mood > 0.5:
            ctx.new_path()
            if mood > 0.5 and not blink:
                ctx.arc(ex_, ey_ + 4, rr * 0.85, 1.15 * math.pi, 1.85 * math.pi)       # にこにこ目
            else:
                ctx.move_to(ex_ - rr * 0.8, ey_)
                ctx.line_to(ex_ + rr * 0.8, ey_)
            _stroke(ctx, 4, INK, 0.95)
        else:
            ctx.save()
            ctx.translate(ex_, ey_)
            ctx.scale(0.82, 1.05)
            ctx.arc(0, 0, rr, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, 0.9)
            ctx.arc(ex_ + gaze * rr / 13.0, ey_ + 1, rr * 0.5, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()
            ctx.arc(ex_ + gaze * rr / 13.0 - 2.5, ey_ - 3, rr * 0.16, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 1)
            ctx.fill()
        brow_up = 4.0 * (1 - mood)
        ctx.move_to(ex_ - rr, ey_ - rr * 1.5 - brow_up * (sg == 0))
        ctx.curve_to(ex_ - rr * 0.3, ey_ - rr * 1.9, ex_ + rr * 0.6, ey_ - rr * 1.8, ex_ + rr, ey_ - rr * 1.45 + 3 * (1 - mood) * (sg == 1))
        _stroke(ctx, 4.5, HAIR_C, 0.95)
    ctx.move_to(hx + 40, hy + 14)                                        # 鼻
    ctx.curve_to(hx + 52, hy + 24, hx + 48, hy + 30, hx + 38, hy + 31)
    _stroke(ctx, 3.5, INK, 0.85)
    for sx_ in (hx - 34, hx + 46):                                       # ほっぺ
        ctx.arc(sx_, hy + 34, 11, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f4a79b", 0.55))
        ctx.fill()
    ctx.new_path()
    if mood > 0.5:
        ctx.arc(hx + 12, hy + 38, 17, 0.1 * math.pi, 0.9 * math.pi)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#c0645c"))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.95)
    else:
        ctx.move_to(hx + 2, hy + 48)
        ctx.curve_to(hx + 10, hy + 43, hx + 22, hy + 43, hx + 30, hy + 47)
        _stroke(ctx, 4, INK, 0.95)
    # 手前のうで（人から見て右）: 扉を引く → あごに手 → 手をあげる
    sx0, sy0 = cx + 86, sh_y + 20
    w_chin = (cx + 74, sh_y + 206)                                       # 手を腰に（ひじを外に張る）
    w_up = (cx + 138, 985.0 + 14 * math.sin(t * 7.5))
    if hold_x is not None and hold_w > 0:
        w_hold = ((hold_x + 2 - AX) / K + AX, (1152.0 - AY) / K + AY)      # 絵全体の拡大の前の座標へもどす
        base = (w_chin[0] + (w_hold[0] - w_chin[0]) * hold_w, w_chin[1] + (w_hold[1] - w_chin[1]) * hold_w)
    else:
        base = w_chin
    wx = base[0] + (w_up[0] - base[0]) * mood
    wy = base[1] + (w_up[1] - base[1]) * mood
    elx, ely = ik2(sx0, sy0, wx, wy, 128.0, 118.0)
    thick(ctx, [(sx0, sy0), (elx, ely), (wx, wy)], 36, SWEATER, 3.5)
    ang = math.atan2(wy - ely, wx - elx)
    thick(ctx, [(wx - 18 * math.cos(ang), wy - 18 * math.sin(ang)), (wx - 4 * math.cos(ang), wy - 4 * math.sin(ang))], 36, SWEATER_D, 3.5)   # そでぐち
    draw_hand(ctx, wx + 4 * math.cos(ang), wy + 4 * math.sin(ang), ang, "open" if mood > 0.5 else "fist")
    ctx.restore()


# ---------- 絵: 冷凍庫 ----------
_FROST = None


def frost_dots():
    global _FROST
    if _FROST is None:
        rng = np.random.default_rng(7)
        _FROST = [(rng.uniform(IX0, IX1), rng.uniform(IY0, YB - 6), rng.uniform(5, 22), rng.uniform(0, 3.14)) for _ in range(70)]
    return _FROST


def draw_room(ctx):
    fill(ctx, hexrgb("#f7efe0"))
    ctx.rectangle(FR[0], FR[1], FR[2] - FR[0], FR[3] - FR[1])
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#eadfc8", 0.9))
    for x in range(int(FR[0]) - 40, int(IX0) - 20, 44):
        ctx.rectangle(x, FR[1], 16, FR[3] - FR[1])
        ctx.fill()


def draw_cabinet(ctx):
    """冷凍庫の本体（外側）と、中（奥の壁・棚・引き出し）。開口部は IX0〜IX1・IY0〜IY1"""
    ctx.rectangle(IX0 - 22, FR[1] - 4, IX1 - IX0 + 44 + 30, FR[3] - FR[1] + 8)
    ctx.set_source_rgba(*hexrgb("#e6edf1"))
    ctx.fill()
    ctx.rectangle(IX0 - 22, FR[1] - 4, IX1 - IX0 + 44 + 30, IY0 - FR[1] + 4)
    _stroke(ctx, 3.5, INK, 0.8)
    # 中の奥の壁
    ctx.rectangle(IX0, IY0, IX1 - IX0, IY1 - IY0)
    ctx.set_source_rgba(*hexrgb("#d3e6f0"))
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.55)                                   # 霜
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for (fx, fy, fr_, fa) in frost_dots():
        ctx.set_line_width(2.4)
        ctx.move_to(fx - fr_ * math.cos(fa), fy - fr_ * math.sin(fa))
        ctx.line_to(fx + fr_ * math.cos(fa), fy + fr_ * math.sin(fa))
        ctx.stroke()
        ctx.move_to(fx - fr_ * 0.6 * math.sin(fa), fy + fr_ * 0.6 * math.cos(fa))
        ctx.line_to(fx + fr_ * 0.6 * math.sin(fa), fy - fr_ * 0.6 * math.cos(fa))
        ctx.stroke()
    ctx.rectangle(IX0, IY0, IX1 - IX0, IY1 - IY0)
    _stroke(ctx, 4, INK, 0.85)
    ctx.rectangle(IX0, IY0, 18, IY1 - IY0)                                # 左の側面の影
    ctx.set_source_rgba(0.2, 0.3, 0.4, 0.16)
    ctx.fill()
    # 棚（コップが乗る）
    ctx.rectangle(IX0, YB, IX1 - IX0, 22)
    ctx.set_source_rgba(*hexrgb("#b8cad6"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    # 棚の上の霜
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.move_to(IX0, YB)
    n = 46
    for k in range(n + 1):
        x = IX0 + (IX1 - IX0) * k / n
        ctx.line_to(x, YB - 5 - 4 * math.sin(k * 1.9) - 2 * math.sin(k * 0.7))
    ctx.line_to(IX1, YB)
    ctx.close_path()
    ctx.fill()
    # 引き出し（ラベルを貼る）
    ctx.rectangle(IX0, YB + 22, IX1 - IX0, IY1 - YB - 22)
    ctx.set_source_rgba(*hexrgb("#e8f1f6"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    core.rrect(ctx, 590, YB + 34, 200, 14, 7)                             # 取っ手
    ctx.set_source_rgba(*hexrgb("#9db2c0"))
    ctx.fill()


def draw_scale(ctx):
    """左の壁に 温度の目盛り（温度計と同じ高さ）。0℃の線は赤い点線で全体にわたす"""
    for v in (60, 40, 20, 0):
        y = th_y(v)
        big = v == 0
        ctx.set_dash([10, 8] if big else [3, 9])
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.move_to(IX0 + 66, y)
        ctx.line_to(IX1 - 6, y)
        _stroke(ctx, 4.0 if big else 1.8, RED if big else PENCIL, 0.85 if big else 0.55)
        ctx.set_dash([])
        text(ctx, num_txt(v), IX0 + 44, y, 30 if big else 26, RED if big else PENCIL, bold=big)


def draw_steam(ctx, cx, rim_y, wid, amount, t, seed, a):
    """湯気。amount（いちばん多いほう＝1）が大きいほど、本数が多く・濃く・高く上がる"""
    if a <= 0 or amount <= 0.02:
        return
    amount = min(1.0, amount) ** 0.6
    rng = np.random.default_rng(seed)
    n = 11
    ctx.save()
    ctx.rectangle(IX0 + 4, IY0 + 4, IX1 - IX0 - 8, rim_y - IY0 - 4)
    ctx.clip()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.55, 0.85)
        x0 = cx + (k / (n - 1) - 0.5) * wid * 0.9 + rng.uniform(-8, 8)
        amp = rng.uniform(12, 22)
        wl = rng.uniform(100, 150)
        u = (t * sp + ph) % 1.0
        vis = clamp01(amount * n * 1.1 - k)
        al = 0.9 * a * vis * min(1.0, 0.4 + 0.6 * amount) * math.sin(math.pi * u) ** 0.8
        if al <= 0.02:
            continue
        rise = 210 * min(1.2, 0.5 + 0.7 * amount)
        y_bot = rim_y - 4 - u * rise
        L = 110 + 50 * amount
        for (col, aa, lw) in (("#9fb4c8", 0.75 * al, 13 + 5 * amount), ("#ffffff", al, 8 + 4 * amount)):
            ctx.set_source_rgba(*hexrgb(col, aa))
            ctx.set_line_width(lw)
            for i in range(16):
                v = i / 15
                yy = y_bot - v * L
                xx = x0 + amp * math.sin((yy + t * 120) / wl * 2 * math.pi + k) * (0.4 + v)
                (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
            ctx.stroke()
    ctx.restore()


def draw_thermo(ctx, x, T, g):
    """料理用の棒の温度計（コップに差してある）。赤い柱の高さ＝温度。2本とも同じ目盛り・同じ高さ"""
    top, bot = th_y(80) - 22, YB - g["dp"] - 10
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    core.rrect(ctx, x - 13, top, 26, bot - top, 13)
    ctx.set_source_rgba(1, 1, 1, 0.93)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    y = th_y(max(-21.0, min(79.0, T)))
    ctx.set_source_rgba(*hexrgb(RED, 0.95))
    core.rrect(ctx, x - 5.5, y, 11, bot - y - 4, 5.5)
    ctx.fill()
    ctx.set_line_width(2.5)
    for v in range(-20, 80, 20):
        yy = th_y(v)
        if yy > g["rim_y"] - 4 or v >= -20:
            ctx.set_source_rgba(*hexrgb(INK, 0.8))
            ctx.move_to(x - 13, yy)
            ctx.line_to(x - 23 if v % 20 == 0 else x - 19, yy)
            ctx.stroke()


def draw_cup(ctx, t, kind, done_t):
    s = sample()
    st = kstate(t, kind)
    g = geom(kind)
    cx, rim_y, dp = g["cx"], g["rim_y"], g["dp"]
    th, bh = g["top_half"], g["bot_half"]
    T = st["read"]
    # 棚の上: 霜が溶けて、コップの底が氷で棚にくっつく
    fx = st["fix"]
    if fx > 0.02:
        ctx.save()
        ctx.rectangle(IX0, YB - 14, IX1 - IX0, 14)
        ctx.clip()
        ctx.set_source_rgba(*hexrgb("#bfe3f5", min(0.95, 0.4 + 0.6 * fx)))
        ctx.rectangle(cx - bh - 12 * fx, YB - 9, 2 * (bh + 12 * fx), 11)
        ctx.fill()
        ctx.restore()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    outer = vessel_poly(cx, rim_y, th, bh, YB)
    layer = vessel_poly(cx, rim_y, th - dp / 2, bh - dp / 2, YB - dp / 2, 10.0)
    cav = vessel_poly(cx, rim_y, th - dp, bh - dp, YB - dp, 9.0)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    poly_path(ctx, outer)
    for i, (x, y) in enumerate(cav):
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.close_path()
    ctx.set_source_rgba(*wall_col(T), 0.97)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    # 中（空気・水・氷）
    poly_path(ctx, cav)
    ctx.set_source_rgba(1, 1, 1, 0.16)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    y_w = YB - dp - g["h_px"]
    ctx.set_source_rgba(*water_col(T), 0.94)
    ctx.rectangle(cx - th, y_w, 2 * th, YB - y_w)
    ctx.fill()
    ice = st["ice"]
    if ice > 0.002:                                                         # 上から白く凍っていく
        y_i = y_w + g["h_px"] * ice
        ctx.set_source_rgba(*hexrgb(ICE_COL, 1.0))
        ctx.rectangle(cx - th, y_w - 4, 2 * th, y_i - y_w + 4)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb("#b9dcee", 0.9))                        # 氷のすじ
        ctx.set_line_width(3.0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(-3, 4):
            ctx.move_to(cx + k * 26 + 6, y_w + 4)
            ctx.line_to(cx + k * 26 - 4, max(y_w + 4, y_i - 6))
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#5f9fc4", 0.95))                       # 氷の先（下の面）
        ctx.set_line_width(4.0)
        ctx.move_to(cx - th, y_i)
        ctx.line_to(cx + th, y_i)
        ctx.stroke()
    elif T < 0.0:                                                           # 過冷却: 0℃より下でもまだ水
        ctx.set_source_rgba(*hexrgb("#ffffff", 0.35))
        for k in range(5):
            ctx.arc(cx - th + 26 + k * (2 * th - 52) / 4, y_w + 10 + 8 * math.sin(t * 5 + k), 3, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()
    for pts, w_ in ((outer, 5.0), (cav, 3.5)):
        ctx.new_path()
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        _stroke(ctx, w_, INK, 0.95)
    # 湯気
    draw_steam(ctx, cx, rim_y, 2 * (th - dp), st["steam"], t, 11 if kind == "h" else 29, 1.0)
    # 温度計（コップの右よりに差す）
    draw_thermo(ctx, cx + th - dp - 50, T, g)
    # 器の中の数字
    nx, ny = cx - 30, YB - dp - 54
    done = done_t is not None
    text(ctx, num_txt(T), nx, ny, 50, RED if done else INK)
    if done:
        note.pen_circle(ctx, nx, ny, 66, 34, RED, seed=70 + (kind == "c"), width=5, progress=clamp01((t - done_t) / 0.35))


def draw_labels(ctx, t, kind, done_t, tmin, a, show_detail):
    g = geom(kind)
    cx = g["cx"]
    s = sample()
    name = NAME[kind]
    y1, y2, y3 = 1348.0, 1392.0, 1432.0
    wn = core.text_width(name, 38)
    xd = cx - wn / 2 - 30
    fill(ctx, (1, 1, 1, 0.92 * a))
    ctx.arc(xd, y1, 22, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, y1, 22, 22, INKC[kind], seed=13 + (kind == "c"), width=3.4, alpha=a)
    text(ctx, TAG[KIND_KEY[kind]], xd, y1, 30, INKC[kind], alpha=a)
    text(ctx, name, cx + 8, y1, 38, INKC[kind], alpha=a)
    if done_t is None:
        text(ctx, f"はじめ {s['T0'][kind]:.0f}℃", cx, y2, 28, INK, bold=False, alpha=a)
        if show_detail and kind == "h":
            lab = f"どちらも 口{s['D']:.1f}cm・水{s['V']:.0f}mL・ガラス"
            text(ctx, lab, 696.0, y3, 26, PENCIL, bold=False, alpha=a)
    else:
        u = clamp01((t - done_t) / 0.35)
        text(ctx, "この置き方なら", cx, y2, 26, INK, bold=False, alpha=a)
        lab = hm_(tmin)
        text(ctx, lab, cx, y3, 34, RED, alpha=a)
        note.pen_circle(ctx, cx, y3, core.text_width(lab, 34) / 2 + 16, 24, RED, seed=80 + (kind == "c"), width=4, progress=u, alpha=a)


def draw_fog(ctx, t):
    """扉が開いたときに こぼれる白い冷気"""
    u = clamp01((t - 0.15) / 3.2)
    if u <= 0 or u >= 1:
        return
    a = math.sin(math.pi * u) ** 0.7 * 0.8
    rng = np.random.default_rng(3)
    for k in range(10):
        x0 = IX0 + 30 + rng.uniform(0, IX1 - IX0 - 60)
        yy = 1420 - 30 * u + rng.uniform(-40, 40)
        r = rng.uniform(70, 130) * (0.6 + 0.6 * u)
        gr = cairo.RadialGradient(x0 + 40 * u * (k % 3 - 1), yy, 4, x0 + 40 * u * (k % 3 - 1), yy, r)
        gr.add_color_stop_rgba(0, 1, 1, 1, 0.75 * a)
        gr.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(gr)
        ctx.rectangle(x0 - r + 40 * u * (k % 3 - 1), yy - r, 2 * r, 2 * r)
        ctx.fill()


def door_theta(t):
    return math.radians(104.0) * ease_out(t / 0.95)


def door_free_x(t):
    return IX1 + 20 - (IX1 - IX0 + 42) * math.cos(door_theta(t))


def draw_door(ctx, t):
    th = door_theta(t)
    if th >= math.pi / 2:
        return
    x_h = IX1 + 20
    x_f = door_free_x(t)
    sc = 1 + 0.10 * math.sin(th)
    yt, yb_ = FR[1] - 6 - 30 * math.sin(th), FR[3] + 6 + 30 * math.sin(th)
    ctx.new_path()
    ctx.move_to(x_h, FR[1] - 6)
    ctx.line_to(x_f, yt)
    ctx.line_to(x_f, yb_)
    ctx.line_to(x_h, FR[3] + 6)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#f4f7f9"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)
    w = abs(x_h - x_f)
    if w > 60:
        core.rrect(ctx, x_f + 20, 1010, 16, 200, 8)                         # 取っ手
        ctx.set_source_rgba(*hexrgb("#9db2c0"))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.85)
        ctx.set_source_rgba(1, 1, 1, 0.6)                                    # つや
        ctx.move_to(x_f + 60, yt + 60)
        ctx.line_to(x_f + 60, yb_ - 60)
        ctx.set_line_width(10)
        ctx.stroke()


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
    done_h = t_of(s["t_h"]) if tau >= s["t_h"] else None
    done_c = t_of(s["t_c"]) if tau >= s["t_c"] else None
    mood = 1.0 if (done_h is not None and done_c is not None) else 0.0
    mood = ease(clamp01((t - max(done_h, done_c)) / 0.5)) if mood else 0.0
    xf = door_free_x(t)
    hold = min(xf + 28, 520.0)
    hold_w = 1 - ease(clamp01((math.degrees(door_theta(t)) - 24.0) / 14.0))
    ctx.push_group()
    ctx.save()
    clip_frame(ctx)
    ctx.save()
    zoom_art(ctx, t, 550.0)
    draw_room(ctx)
    draw_cabinet(ctx)
    draw_scale(ctx)
    draw_cup(ctx, t, "h", done_h)
    draw_cup(ctx, t, "c", done_c)
    la = ease((t - 1.0) / 0.4)
    if la > 0:
        any_done = (done_h is not None) or (done_c is not None)
        draw_labels(ctx, t, "h", done_h, s["t_h"], la, not any_done)
        draw_labels(ctx, t, "c", done_c, s["t_c"], la, not any_done)
    draw_door(ctx, t)
    draw_fog(ctx, t)
    draw_person(ctx, t, mood, hold, hold_w)
    ctx.restore()
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
    win_c = (r["t_frz_c"] < r["t_frz_h"]).astype(int)           # 1 = 水のほうが先に凍った
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_H), bgra(COL_C)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_c[:m]]
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


def pct_s(p):
    """表示用の割合。1%未満は小数1桁（0.7%）"""
    v = p * 100
    return f"{v:.1f}%" if v < 1.0 else f"{int(math.floor(v + 0.5))}%"


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
    win_c = r["t_frz_c"][:m] < r["t_frz_h"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("h", int(m - win_c.sum())), ("c", int(win_c.sum())))):
            y = 1185 + i * 54
            fill(ctx, hexrgb(COLS[k], a * lg))
            ctx.rectangle(150, y - 17, 34, 34)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(150, y - 17, 34, 34)
            ctx.stroke()
            text(ctx, f"{TAG[KIND_KEY[k]]} {NAME[k]}のほうが先に凍る", 200, y, 34, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 925, y, 34, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            sh = shown()
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            lead = "水" if sh["gap_med"] >= 0 else "お湯"
            lead_p = sh["p_water"] if sh["gap_med"] >= 0 else 1 - sh["p_water"]
            note.sticky(ctx, f"{lead}が先に凍る回は 約{pct_i(lead_p)}。\n凍るまでの差は 中央値で {hm_about(abs(sh['gap_med']))}\n（中央値＝1万回の ちょうど真ん中の値）",
                        580, 1352, 30, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_water"], sh["gap_med"])


def reason_text():
    sh = shown()
    k = answer_key()
    a, b = hm_(sh["med_h"]), hm_(sh["med_c"])
    if k == "water":
        return f"お湯は まず水の温度まで冷める。\nその分、お湯は遅れて凍る。\n凍るまでの中央値は 水{b}・お湯{a}"
    if k == "hot":
        return f"お湯は 棚と蒸発の分だけ早く冷める。\nその分、お湯が先に凍る。\n凍るまでの中央値は お湯{a}・水{b}"
    return f"凍るまでの時間は ほぼ互角。\n中央値は 水{b}・お湯{a}"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 580, 1192, 52, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        note.sticky(ctx, reason_text(), 580, 1336, 30, "blue", a=c, tilt=0.012)
        text(ctx, "実験の結論は割れています。これは計算での見立て", 560, 1436, 26, PENCIL, bold=False, alpha=c)


# ---------- ひねり（お湯が先に凍るのは、どんなとき？） ----------
BAR_X0, BAR_W = 300.0, 500.0                       # 棒の左端、最大の長さ


def twist_info():
    """お湯が先に凍った回に多い条件（霜・蒸発・過冷却のうち、いちばん差が大きい1つ）。棒グラフの中身と一行"""
    sh = shown()
    f = sh["fac"][sh["best"]]
    if sh["best"] == "frost":
        return dict(title="0℃になるまでに、水のコップが\n棚にくっついた割合", unit="%", all=f["all_med"], hf=f["hf_med"], nd=0, vmax=100.0,
                    line="棚の霜が厚いと、水のコップは\nなかなか棚にくっつかない。\nこのとき、お湯が先に凍る。")
    if sh["best"] == "evap":
        return dict(title="お湯のコップから 蒸発した水", unit="g", all=f["all_med"], hf=f["hf_med"], nd=1, vmax=max(f["all_med"], f["hf_med"]) * 1.25,
                    line="お湯がよく蒸発すると、お湯の量が減る。\nこのとき、お湯が先に凍る。")
    return dict(title="水のコップの過冷却 − お湯のコップの過冷却", unit="℃", all=f["all_med"], hf=f["hf_med"], nd=1, vmax=max(abs(f["all_med"]), abs(f["hf_med"]), 1.0) * 1.25,
                line="水のコップだけ、過冷却が深くなる。\nこのとき、お湯が先に凍る。")


def draw_bar(ctx, y, v, vmax, label, col, ink, a, grow, unit, nd):
    wbar = BAR_W * max(v, 0.0) / vmax * grow
    text(ctx, label, 140, y - 26, 30, ink, align="left", alpha=a)
    fill(ctx, hexrgb(col, a))
    core.rrect(ctx, 140, y, max(wbar, 1.0), 42, 8)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    core.rrect(ctx, 140, y, max(wbar, 1.0), 42, 8)
    ctx.stroke()
    if grow > 0.98:
        text(ctx, f"{v:.{nd}f}{unit}", 140 + wbar + 14, y + 21, 34, INK, align="left", alpha=a)


def draw_twist(ctx, t):
    if t < T_TW:
        return
    sh = shown()
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo <= 0:
        return
    u = t - T_TW
    info = twist_info()
    ctx.push_group()
    a0 = ease_out(u / 0.3)
    note.sticky(ctx, "では、お湯が先に凍るのは、\nどんなとき？", 580, 700, 46, "yellow", fg=RED, a=a0, tilt=-0.02)
    if u > 0.8:
        text(ctx, f"お湯が先だった {sh['n_hot']}回（約{pct_s(sh['n_hot'] / N_TRIAL)}）の条件を調べた", 580, 840, 28, INK, bold=False,
             alpha=ease_out((u - 0.8) / 0.3))
    ua = u - 2.0
    if ua > 0:
        a = ease_out(ua / 0.3)
        text(ctx, f"{info['title']}（中央値）", 140, 925, 30, INK, align="left", bold=False, alpha=a)
        g = ease(clamp01((ua - 0.2) / 0.8))
        draw_bar(ctx, 1010, info["all"], info["vmax"], "ぜんぶの1万回", COL_C, INK_C, a, g, info["unit"], info["nd"])
        ub = ua - 1.6
        if ub > 0:
            b = ease_out(ub / 0.3)
            g2 = ease(clamp01((ub - 0.2) / 0.8))
            draw_bar(ctx, 1140, info["hf"], info["vmax"], "お湯が先だった回", COL_H, INK_H, b, g2, info["unit"], info["nd"])
    uc = u - 6.0
    if uc > 0:
        note.sticky(ctx, info["line"], 580, 1330, 32, "pink", fg=RED, a=ease_out(uc / 0.3), tilt=-0.012)
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


def big3_size(max_w=860.0, cap=112.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ（行の間に収まるよう cap まで）"""
    return min(cap, 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3))


CD_X, CD_Y = 205.0, 1190.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下で、冷凍庫の扉が開く（0秒目から動く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = big3_size(860.0)
        ys = (440, 552, 664)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.03 * (1 - ease_out(t / 0.4))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q3[2], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, 716, 565 + w2 / 2 + 6, 712, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, 754, 30, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 800
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
        note.sticky(ctx, "あなたは、\nお湯が先だと思っていましたか？", 580, 860, 48, "yellow", a=q, tilt=-0.02)
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
    mx.add(0.0, thump(), 0.55)                                 # 扉の「ガチャ」
    door = noise_band(1.5, 24, 5, 1.0)                         # 扉が開く・冷気が出る音（ふわっ）
    tt = np.arange(len(door)) / SR
    door = door * np.minimum(1, tt / 0.04) * np.minimum(1, (1.5 - tt) / 0.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 5 * tt))
    mx.add(0.05, door, 0.5)
    hiss_len = T_G0
    hiss = noise_band(hiss_len, 6, 9, 1.0)                    # 冷気のしゅー（だんだん小さく）
    th = np.arange(len(hiss)) / SR
    hiss = hiss * np.minimum(1, th / 0.5) * np.minimum(1, (hiss_len - th) / 0.5) * np.clip(1.0 - th / 18.0, 0.3, 1.0)
    mx.add(0.3, hiss, 0.09)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    tg, te = t_of(s["t_h"]), t_of(s["t_c"])
    mx.add(min(tg, te), bell(784.0, 1.2), 0.45)
    mx.add(max(tg, te), bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                       # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                            # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    mx.add(T_TW + 2.2, blip(659.3, 0.12), 0.3)
    mx.add(T_TW + 3.8, blip(659.3, 0.12), 0.3)
    mx.add(T_TW + 6.2, blip(784.0, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def change_fraction(t0, t1):
    """画面全体のうち、2つの時刻でちがう画素の割合（preflight と同じ測り方）"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    arrs = []
    for t in (t0, t1):
        core._CUR_T = t
        ctx = cairo.Context(surf)
        draw(ctx, t)
        surf.flush()
        arrs.append(np.frombuffer(bytes(surf.get_data()), np.uint8).astype(np.int16))
    core._CUR_T = 0.0
    return float(np.mean(np.abs(arrs[0] - arrs[1]) > 8))


def run_checks():
    sh = shown()
    r = results()
    checks = []
    checks.append(("エネルギー保存（最大の食い違い・割合）", energy_check(), 0.0, 1e-4))
    checks.append(("水の量の保存（最大の食い違い・kg）", conserve_check(), 0.0, 1e-9))
    checks.append(("きざみ 5秒 と 1.25秒 の差（最大・分）", dt_check(), 0.0, 0.1))
    z, obs = bl_check()
    checks.append(("Burridge & Linden の実験（0℃まで）との比 21.8℃", float(z[0] / obs[0]), 1.0, 0.10))
    checks.append(("Burridge & Linden の実験（0℃まで）との比 57.3℃", float(z[1] / obs[1]), 1.0, 0.10))
    checks.append(("Burridge & Linden の実験（0℃まで）との比 84.7℃", float(z[2] / obs[2]), 1.0, 0.10))
    s = sample()
    checks.append(("見本のお湯の時刻（分）が1万回の値と同じ", s["chk"][0], s["t_h"], 1e-6))
    checks.append(("見本の水の時刻（分）が1万回の値と同じ", s["chk"][1], s["t_c"], 1e-6))
    key = answer_by_rule(sh["p_water"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（お湯・水）",
                   float(LABELS.index(KEY_LABEL["hot"]) * 10 + LABELS.index(KEY_LABEL["water"])),
                   float("ABC".index(TAG["hot"]) * 10 + "ABC".index(TAG["water"])), 0.0))
    checks.append(("見本の差（分）が中央値の近く", s["gap"], sh["gap_med"], 0.15 * abs(sh["gap_med"])))
    checks.append(("水が先＋お湯が先", float(sh["n_water"] + sh["n_hot"]), float(N_TRIAL), 0.0))
    checks.append(("14時間たっても凍らなかった回", float(sh["n_unfinished"]), 0.0, 0.0))
    d = r["p"]
    free = (d["Hc"] - d["dl"] - d["V"] * 1e-6 / (math.pi * d["D"] ** 2 / 4))
    fmin = float(np.min(free))
    print(f"  水面からコップの口までの高さの最小: {fmin * 100:.2f}cm")
    checks.append(("すべての回で 水があふれない（水面が口より1cm以上下）", float(fmin >= 0.01), 1.0, 0.0))
    checks.append(("凍るまでの中央値が 1〜6時間に収まる（お湯・水）", float(all(60 <= x <= 360 for x in (sh["med_h"], sh["med_c"]))), 1.0, 0.0))
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(change_fraction(0.0, 1.0) >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {change_fraction(0.0, 1.0):.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


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
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  全部凍る {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（お湯 {hm_(s['t_h'])} / 水 {hm_(s['t_c'])}）")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", twist_info()["line"].replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.6, 1.0, 2.5, 4.4, 5.2, 6.5, 8.0, 10.0, T_FIN1 - 0.6, T_FIN1 + 0.4, T_FIN2 - 0.6, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 2.0, T_TW + 4.8, T_TW + 8.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
