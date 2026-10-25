"""冷える夜、毛布は羽毛布団の上？下？ 同じ部屋の2つのベッドで1万回。— 2026-10-19 作成（公開予定 10/25）

くらべるのは「体から上へ逃げる熱」（少ないほうが暖かい）。敷きふとん側（下へ逃げる熱）は2つとも同じなので入れない。

モデル（1次元・体の上側 1m² あたり。肌 → パジャマ → 掛けもの2枚 → 部屋）
  逃げる熱 q = (肌の温度 − 部屋の温度) ÷ (R_パジャマ + R_羽毛 + R_毛布 + R_表面)      [W/m²]
  ※ 熱の通りにくさ（熱抵抗 R）を足し算するだけなら、重ねる順番を変えても q は1ミリも変わらない。
    この回で差を生むのは「重さで羽毛がつぶれる」ことだけ（それ以外の差はモデルに入れていない）:
      A 毛布が上 … 毛布の重さが羽毛布団に乗り、羽毛がつぶれて薄くなる（羽毛の R が下がる）
      B 毛布が下 … 羽毛は自分と側生地の重さだけでふくらむ。毛布は羽毛布団の重さでほんの少しだけ押される
  肌の温度 33.0〜34.0℃、部屋 5〜15℃（一様）。
  パジャマ: 0.42〜0.57 clo（半袖〜厚手の長袖パジャマ。ASHRAE 55 の衣服の表 → 0.065〜0.088 m²K/W）。
  表面の空気の層: 0.10〜0.12 m²K/W（ISO 9920 の静かな空気 0.7 clo = 0.109）。
  羽毛布団（ふくらんだ状態の熱抵抗 R0）: 0.8〜1.3 m²K/W。
      ・岐阜県産業技術センター研究報告 No.10 (2016)「軽量・高保温性繊維素材の開発（第1報）」:
        市販の羽毛布団から採った羽毛（ダウン50%）を厚さ4cmに詰めて 約1.03 m²K/W。
        目付250 g/m²（シングル150×210cmで羽毛0.8kg＝合掛けの多い量）なら 厚さ約3.8cm・約0.88 m²K/W。
      ・香港消費者委員会の掛け布団テスト（20点）: 4.8〜11.1 tog（0.48〜1.11 m²K/W）。
      → 冬用（合掛けより羽毛が多い）を見込んで 0.8〜1.3 にした（上のほうは仮定）。
      厚み 1cm あたりの熱抵抗 0.22〜0.26 m²K/W（上の岐阜の値から）。羽毛の量は 250 g/m² × R0/0.88。
      側生地（片面）0.10〜0.14 kg/m²（仮定）。
  羽毛のつぶれ方: 羽毛の密度 ∝ 押す圧力^n、n = 0.30〜0.50。
      ・Fuller 2015（リーズ大学 博士論文）7.1: ばらの羽毛を 2.08 Pa から押すと、羽毛量の試験と同じ 14.8 Pa までに
        45±8 mm 縮み、1.5mm まで押しきるのに 約80mm。→ 高さは 約83mm → 約38mm（圧力 約7倍で 約0.46倍）。
        羽毛の自重（約0.6Pa）を足すと n ≈ 0.45、ばらつき（±8mm）で 0.30〜0.52。同論文は van Wyk の式（n=1/3）にも触れる。
      ・羽毛の中の深さごとに、上に乗っている重さ（側生地＋上の羽毛＋毛布）で圧力を出し、厚みを足し合わせる。
      ・同論文 7.2: 生地で包んだ羽毛は、生地の重さと仕切り（バッフル）で「いつも少し押された状態」になる。
        → キルトの仕切りが、羽毛が本来ふくらむ高さの c = 70〜100% に厚みを抑えている、とした（仮定）。
          軽い重さなら、つぶれはまず仕切りの「余裕」で吸収される（厚みが変わらない）。
      ・熱抵抗は厚みにほぼ比例する（同論文 7.3 が引く Rees 1941）。ただし同論文の測定では、同じ仕切りに羽毛を詰めるほど
        熱抵抗が上がった（密度が上がると熱が通りにくくなる分がある）。→ R ∝ 厚み^(1−β)、β = 0〜0.5（0.5は同論文から見た上限）。
  毛布: 重さ 1.8〜4.0 kg、大きさ 155×195 cm（日本大百科全書「毛布」）。重さはそのまま羽毛布団に乗るとした。
      厚み ＝ 1m²あたりの重さ ÷ かさ密度 80〜130 kg/m³（仮定）。熱伝導率 0.040〜0.050 W/(m·K)
      （岐阜の報告で、わたを4cmに詰めた熱抵抗 0.85〜1.03 → 0.039〜0.047）。
      毛布が下のとき、羽毛布団の重さで毛布の厚みが 0〜5% 減る（仮定。毛布は羽毛より約20倍詰まっていて、ほとんどつぶれない）。
  見本の動き（寝てからの時間）: 布団に入った瞬間は、パジャマと掛けものが部屋の温度。それぞれの層を細かく分け、
      熱容量（パジャマ 0.2 kg/m²・羽毛と側生地・毛布、比熱 1.3〜1.4 kJ/(kg·K)。仮定）で温まっていく様子を足し算で出す。
      答えには使わない（答えは温まりきったあとの q）。

問い: 「冷える夜、毛布は / 羽毛布団の上？下？」（前提「1枚ずつ掛ける。下＝体と羽毛布団のあいだ」）
      A 毛布が上 ／ B 毛布が下 ／ C ほぼ同じ
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1回ごとに d = (A の逃げる熱 − B の逃げる熱) ÷ A の逃げる熱（毛布を下にして減った熱の割合）。
      d の真ん中の値が +5% 以上で、しかも d ≥ +5% の回が 60% 以上なら B（毛布が下）。
      d の真ん中の値が −5% 以下で、しかも d ≤ −5% の回が 60% 以上なら A（毛布が上）。それ以外は C（ほぼ同じ）。
ひねり: 「では、毛布が重いと？」 同じ1万回を、毛布の重さで分ける（軽い 1.8〜2.5kg ／ 重い 3.3〜4.0kg）。
締め: 「あなたの家は、/ 上？下？」（答えは出さない）

乱数の種は見本（並んで眠る2人）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "moufu-kasane"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
G = 9.81
ROOM = (5.0, 15.0)                                # ℃
SKIN = (33.0, 34.0)                               # ℃
R_PJ = (0.42 * 0.155, 0.57 * 0.155)               # パジャマ m²K/W
R_SURF = (0.10, 0.12)                             # 表面の空気の層
R_DOWN0 = (0.8, 1.3)                              # 羽毛布団（ふくらんだ状態）
R_PER_CM = (0.22, 0.26)                           # 羽毛の厚み1cmあたり
DOWN_REF = (0.250, 0.88)                          # 250 g/m² で 0.88 m²K/W（岐阜）
SHELL = (0.10, 0.14)                              # 側生地 片面 kg/m²
N_COMP = (0.30, 0.50)                             # 密度 ∝ 圧力^n
CAP = (0.70, 1.00)                                # 仕切りが抑えている厚み（本来の高さに対する割合）
BETA = (0.0, 0.5)                                 # R ∝ 厚み^(1−β)
BLK_KG = (1.8, 4.0)                               # 毛布の重さ
BLK_AREA = 1.55 * 1.95                            # m²
BLK_RHO = (80.0, 130.0)                           # kg/m³
BLK_K = (0.040, 0.050)                            # W/(m·K)
BLK_SQUEEZE = (0.0, 0.05)                         # 下にしたとき、羽毛布団の重さで減る厚み
LIGHT, HEAVY = (1.8, 2.5), (3.3, 4.0)             # ひねり
TOP_AREA = 0.9                                    # 体の上側の面積 m²（体表面 約1.8m² の半分。画面の W 表示だけに使う）

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_D, RULE_P = 0.05, 0.60


def answer_by_rule(d_med, p_b, p_a):
    """d_med = 「毛布を下にして減った熱の割合」の真ん中の値、p_b = d ≥ 5% の回の割合、p_a = d ≤ −5% の回の割合"""
    if d_med >= RULE_D and p_b >= RULE_P:
        return 1                                  # B 毛布が下
    if d_med <= -RULE_D and p_a >= RULE_P:
        return 0                                  # A 毛布が上
    return 2                                      # C ほぼ同じ


# ---------- 羽毛のつぶれ方 ----------
_U = (np.arange(64) + 0.5) / 64                   # 羽毛の深さ（0 上 → 1 下）


def loft_ratio(p_top, m_down, dp, n):
    """上に dp [Pa] 足したとき、羽毛が本来ふくらむ高さが何倍になるか。
    p_top = 羽毛の上に乗っている重さの圧力（側生地）、m_down = 羽毛 kg/m²。深さごとに 密度 ∝ 圧力^n で足し合わせる"""
    p_top, m_down, dp, n = (np.asarray(x, float)[..., None] for x in (p_top, m_down, dp, n))
    p = p_top + G * m_down * _U
    return (np.mean((p + dp) ** (-n), -1) / np.mean(p ** (-n), -1))


def draw_params(rng, n):
    u = lambda lo_hi, k=n: rng.uniform(lo_hi[0], lo_hi[1], k)   # noqa: E731
    r0 = u(R_DOWN0)
    return dict(room=u(ROOM), skin=u(SKIN), r_pj=u(R_PJ), r_surf=u(R_SURF), r_down0=r0, r_cm=u(R_PER_CM),
                m_down=DOWN_REF[0] * r0 / DOWN_REF[1], shell=u(SHELL), n=u(N_COMP), cap=u(CAP), beta=u(BETA),
                blk_kg=u(BLK_KG), blk_rho=u(BLK_RHO), blk_k=u(BLK_K), squeeze=u(BLK_SQUEEZE))


def layers(p):
    """A（毛布が上）と B（毛布が下）の、羽毛と毛布の熱抵抗と厚み"""
    m_blk = p["blk_kg"] / BLK_AREA                                 # kg/m²
    t_blk = m_blk / p["blk_rho"]                                   # m
    r_blk = t_blk / p["blk_k"]
    f_nat = loft_ratio(G * p["shell"], p["m_down"], G * m_blk, p["n"])
    ratio = np.minimum(1.0, f_nat / p["cap"])                      # 仕切りの余裕を超えた分だけ薄くなる
    r_down_a = p["r_down0"] * ratio ** (1 - p["beta"])
    h0 = p["r_down0"] / p["r_cm"]                                  # cm
    return dict(r_blk_a=r_blk, r_blk_b=r_blk * (1 - p["squeeze"]), r_down_a=r_down_a, r_down_b=p["r_down0"],
                h_b=h0, h_a=h0 * ratio, t_blk=t_blk, ratio=ratio, f_nat=f_nat)


def heat(p, L):
    """逃げる熱 W/m²（温まりきったあと）と、寝床内（パジャマと掛けもののあいだ）の温度"""
    dT = p["skin"] - p["room"]
    ra = p["r_pj"] + L["r_down_a"] + L["r_blk_a"] + p["r_surf"]
    rb = p["r_pj"] + L["r_down_b"] + L["r_blk_b"] + p["r_surf"]
    qa, qb = dT / ra, dT / rb
    return qa, qb, p["skin"] - qa * p["r_pj"], p["skin"] - qb * p["r_pj"]


SEED_MAIN = 20261025
_RES = {}


def results():
    if not _RES:
        p = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
        L = layers(p)
        qa, qb, ta, tb = heat(p, L)
        _RES["m"] = dict(p=p, L=L, qa=qa, qb=qb, ta=ta, tb=tb, d=(qa - qb) / qa)
    return _RES["m"]


def shown():
    r = results()
    p, L, d = r["p"], r["L"], r["d"]
    light = (p["blk_kg"] >= LIGHT[0]) & (p["blk_kg"] <= LIGHT[1])
    heavy = (p["blk_kg"] >= HEAVY[0]) & (p["blk_kg"] <= HEAVY[1])
    return dict(d_med=float(np.median(d)), d_q=np.percentile(d, [1, 10, 25, 75, 90, 99]),
                p_b=float(np.mean(d >= RULE_D)), p_a=float(np.mean(d <= -RULE_D)),
                n_b=int(np.sum(d >= RULE_D)), n_a=int(np.sum(d <= -RULE_D)), n_c=int(np.sum(np.abs(d) < RULE_D)),
                p_bwarm=float(np.mean(d > 0)),
                qa_med=float(np.median(r["qa"])), qb_med=float(np.median(r["qb"])),
                ta_med=float(np.median(r["ta"])), tb_med=float(np.median(r["tb"])),
                dt_med=float(np.median(r["tb"] - r["ta"])),
                h_b=float(np.median(L["h_b"])), h_a=float(np.median(L["h_a"])),
                ratio_med=float(np.median(L["ratio"])), ratio_q=np.percentile(L["ratio"], [10, 90]),
                t_blk_q=np.percentile(L["t_blk"] * 1000, [0, 50, 100]), r_blk_q=np.percentile(L["r_blk_a"], [0, 50, 100]),
                d_light=float(np.median(d[light])), d_heavy=float(np.median(d[heavy])),
                n_light=int(light.sum()), n_heavy=int(heavy.sum()),
                pb_light=float(np.mean(d[light] >= RULE_D)), pb_heavy=float(np.mean(d[heavy] >= RULE_D)),
                h_a_light=float(np.median(L["h_a"][light])), h_a_heavy=float(np.median(L["h_a"][heavy])),
                cold=float(np.median((r["qa"] - r["qb"])[p["room"] < 8])),
                warm=float(np.median((r["qa"] - r["qb"])[p["room"] > 12])))


def report():
    sh = shown()
    print(f"d（毛布を下にして減った熱の割合）: 真ん中 {sh['d_med']:+.4f}  1/10/25/75/90/99% {np.round(sh['d_q'], 3)}")
    print(f"  d≥5%: {sh['p_b']:.4f}（{sh['n_b']}回）  d≤−5%: {sh['p_a']:.4f}（{sh['n_a']}）  5%未満: {sh['n_c']}  B が少しでも暖かい: {sh['p_bwarm']:.4f}")
    print(f"  答え {'ABC'[answer_by_rule(sh['d_med'], sh['p_b'], sh['p_a'])]}")
    print(f"  逃げる熱（真ん中）A {sh['qa_med']:.1f} / B {sh['qb_med']:.1f} W/m²   寝床内 A {sh['ta_med']:.2f} / B {sh['tb_med']:.2f}℃  差 {sh['dt_med']:.2f}")
    print(f"  羽毛の厚み（真ん中）B {sh['h_b']:.2f}cm → A {sh['h_a']:.2f}cm  比 {sh['ratio_med']:.3f}  10/90% {np.round(sh['ratio_q'], 3)}")
    print(f"  毛布 厚み mm {np.round(sh['t_blk_q'], 1)}  R {np.round(sh['r_blk_q'], 3)}")
    print(f"  軽い毛布 d {sh['d_light']:+.3f}（{sh['n_light']}回, ≥5% {sh['pb_light']:.3f}, 羽毛 {sh['h_a_light']:.2f}cm） "
          f"重い毛布 d {sh['d_heavy']:+.3f}（{sh['n_heavy']}回, ≥5% {sh['pb_heavy']:.3f}, 羽毛 {sh['h_a_heavy']:.2f}cm）")
    print(f"  部屋 8℃未満の熱の差 {sh['cold']:.2f} W/m²  12℃超 {sh['warm']:.2f}")


def seeds_check(k=10):
    """乱数を変えて k 回やり直したときの d の真ん中の値と d≥5% の割合（概要欄用）"""
    out = []
    for j in range(k):
        p = draw_params(np.random.default_rng(1000 + j), N_TRIAL)
        qa, qb, _, _ = heat(p, layers(p))
        d = (qa - qb) / qa
        out.append((float(np.median(d)), float(np.mean(d >= RULE_D))))
    return np.array(out)


# ---------- 見本の動き（寝てからの時間） ----------
C_SPEC = 1340.0                                   # J/(kg·K) 繊維（羽毛・綿・アクリル）の比熱（仮定 1.3〜1.4 の真ん中）
M_PJ = 0.2                                        # パジャマ kg/m²（仮定）
N_SLAB = 6


class Stack:
    """肌（一定）→ 層 → 表面 → 部屋。層は (R, C) のリスト（肌側から）。温度は固有値で式のまま解く"""

    def __init__(self, layers_rc, r_surf, t_skin, t_room, t0_layers):
        rs, cs, li = [], [], []
        for k, (R, C) in enumerate(layers_rc):
            rs += [R / N_SLAB] * N_SLAB
            cs += [C / N_SLAB] * N_SLAB
            li += [k] * N_SLAB
        n = len(rs)
        self.rs, self.li = np.array(rs), np.array(li)
        K = np.zeros((n, n))
        b = np.zeros(n)
        for i in range(n):
            rl = rs[i] / 2 + (rs[i - 1] / 2 if i > 0 else 0.0)
            rr = rs[i] / 2 + (rs[i + 1] / 2 if i < n - 1 else r_surf)
            K[i, i] -= 1 / rl + 1 / rr
            if i > 0:
                K[i, i - 1] += 1 / rl
            else:
                b[i] += t_skin / rl
            if i < n - 1:
                K[i, i + 1] += 1 / rr
            else:
                b[i] += t_room / rr
        cinv = 1 / np.array(cs)
        A = K * cinv[:, None]
        self.ss = np.linalg.solve(K, -b)
        lam, V = np.linalg.eig(A)
        self.lam, self.V = lam.real, V.real
        self.c0 = np.linalg.solve(self.V, np.array([t0_layers[k] for k in li]) - self.ss)
        self.t_skin, self.t_room, self.r_surf = t_skin, t_room, r_surf

    def nodes(self, t):
        return self.ss + self.V @ (self.c0 * np.exp(self.lam * t))

    def t_bed(self, t):
        """寝床内（1枚目の層＝パジャマ と 2枚目のあいだ）の温度"""
        T = self.nodes(t)
        i = N_SLAB - 1
        ra, rb = self.rs[i] / 2, self.rs[i + 1] / 2
        return T[i] + (T[i + 1] - T[i]) * ra / (ra + rb)

    def q_out(self, t):
        """いちばん外の表面から部屋へ逃げる熱 W/m²"""
        T = self.nodes(t)
        return (T[-1] - self.t_room) / (self.rs[-1] / 2 + self.r_surf)

    def q_skin(self, t):
        T = self.nodes(t)
        return (self.t_skin - T[0]) / (self.rs[0] / 2)


def stacks(i):
    """1万回のうち i 回目の A・B の Stack"""
    r = results()
    p, L = r["p"], r["L"]
    g = lambda k: float(p[k][i])   # noqa: E731
    m_blk = g("blk_kg") / BLK_AREA
    c_pj, c_down, c_blk = M_PJ * C_SPEC, (g("m_down") + 2 * g("shell")) * C_SPEC, m_blk * C_SPEC
    pj = (g("r_pj"), c_pj)
    a = [pj, (float(L["r_down_a"][i]), c_down), (float(L["r_blk_a"][i]), c_blk)]
    b = [pj, (float(L["r_blk_b"][i]), c_blk), (float(L["r_down_b"][i]), c_down)]
    t0 = [g("skin") * 0.5 + g("room") * 0.5, g("room"), g("room")]   # パジャマは着ていた分だけ温かい（肌と部屋の中間）
    return (Stack(a, g("r_surf"), g("skin"), g("room"), t0), Stack(b, g("r_surf"), g("skin"), g("room"), t0))


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sc = seeds_check()
    print(f"乱数を変えて10回: d の真ん中 {sc[:, 0].min():.4f}〜{sc[:, 0].max():.4f}  d≥5% {sc[:, 1].min():.4f}〜{sc[:, 1].max():.4f}")
    sys.exit(0)


# =====================================================================
# 見本（並んで眠る2人）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: d が真ん中の値の近く（±1%）、部屋 7.5〜10℃、毛布 2.3〜3.0kg、羽毛のつぶれ方が真ん中の近く。その中で d が真ん中に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p, L, d = r["p"], r["L"], r["d"]
    sh = shown()
    cand = np.nonzero((np.abs(d - sh["d_med"]) < 0.01) & (p["room"] > 7.5) & (p["room"] < 10) & (p["blk_kg"] > 2.3)
                      & (p["blk_kg"] < 3.0) & (np.abs(L["ratio"] - sh["ratio_med"]) < 0.05))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(d[cand] - sh["d_med"]))])
    A, B = stacks(i)
    _SAMPLE = dict(i=i, A=A, B=B, room=float(p["room"][i]), skin=float(p["skin"][i]), kg=float(p["blk_kg"][i]),
                   h_b=float(L["h_b"][i]), h_a=float(L["h_a"][i]), t_blk=float(L["t_blk"][i]),
                   qa=float(r["qa"][i]), qb=float(r["qb"][i]), ta=float(r["ta"][i]), tb=float(r["tb"][i]), d=float(d[i]))
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    print("見本", s["i"], "部屋", round(s["room"], 1), "肌", round(s["skin"], 2), "毛布", round(s["kg"], 2), "kg",
          "羽毛", round(s["h_b"], 2), "→", round(s["h_a"], 2), "cm  d", round(s["d"], 3),
          "逃げる熱", round(s["qa"] * TOP_AREA, 1), round(s["qb"] * TOP_AREA, 1), "W  寝床内", round(s["ta"], 2), round(s["tb"], 2))
    for mins in (0, 1, 2, 5, 10, 15, 20, 30, 45, 60):
        print(f"  {mins:3d}分 A {s['A'].t_bed(mins * 60):.2f} B {s['B'].t_bed(mins * 60):.2f}  "
              f"熱 A {s['A'].q_skin(mins * 60) * TOP_AREA:.1f} B {s['B'].q_skin(mins * 60) * TOP_AREA:.1f} W")
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
note.DATE = "10.25"                               # 日付欄（公開予定日）

COL_A, INK_A = "#f4ad6a", "#b8601a"               # A 毛布が上（毛布の色）
COL_B, INK_B = "#8fbbe8", "#2f63a8"               # B 毛布が下（羽毛布団の色）
COL_C = "#cfd3da"                                 # ほぼ同じ
BLANKET, BLANKET_D = "#eca66c", "#c27a42"
DOWN, DOWN_L = "#f7f9fd", "#b7c6dc"
WALL, WALL_L = "#eceef5", "#dfe3ee"
NIGHT0, NIGHT1 = "#1f2b4f", "#3b4d7c"
WOOD, WOOD_D = "#d9b98c", "#b8935f"
SKIN_C, HAIR = "#f6d7bd", "#4a3a33"
HEAT = "#e8574a"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_SPREAD = T_GO - 0.05                             # 毛布を広げる（1.0秒）
T_CLOCK0 = T_GO + 1.0                              # 寝てから0分
RACE_LEN = 10.0                                    # 0〜60分を何秒で見せるか
RACE_MIN = 60.0
BIG_Q = ["冷える夜、毛布は", "羽毛布団の上？下？"]
DETAIL = "1枚ずつ掛ける。下＝体と羽毛布団のあいだ"
LABELS = ["毛布が上", "毛布が下", "ほぼ同じ"]
CORRECT = 1                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
NAME = {"a": "毛布が上", "b": "毛布が下"}
TAG = {"a": "A", "b": "B"}
COLS = {"a": COL_A, "b": COL_B}
INKC = {"a": INK_A, "b": INK_B}

# 場面（場面の座標: 幅1080・高さ SCENE_H。画面へは layout で縮めて置く）
# 同じ部屋が上下に2つ（上が A、下が B）。ベッドは横から見た断面
SCENE_H = 760.0
CX = 580.0
ROOM_H, SLAB = 375.0, 10.0
ROOM_Y = {"a": 0.0, "b": ROOM_H + SLAB}
FLOOR_Y = 360.0                                    # 床（部屋の中の座標）
BED_X0, BED_X1 = 110.0, 960.0                      # ベッドの頭側・足側
MAT_Y = 300.0                                      # マットレスの上
PX_CM = 14.0                                       # 羽毛の厚み 1cm を何 px で描くか
BLK_PX = 18.0                                      # 毛布の厚み（絵。実物は約1cm）
TH_XR = 400.0                                      # 温度計（胸の上）
TH_TOP, TH_BOT = 70.0, 220.0                       # 35℃ と 15℃ の高さ
TH_LO, TH_HI = 15.0, 35.0
TAG_X, TAG_Y = 150.0, 52.0
LAY_INTRO = (1.0, 690.0)
LAY_RACE = (0.75, 572.0)
ZOOM0, ZOOM_T = 1.42, 1.6
ZOOM_F = (560.0, 330.0)


def setup():
    global T_RACE_END, T_G0, T_G1, T_REV, T_WHY, T_TW, T_TW_RUN, T_Q, DURATION
    T_RACE_END = T_CLOCK0 + RACE_LEN
    T_G0 = T_RACE_END + 2.8
    T_G1 = T_G0 + 2.4
    T_REV = T_G1 + 0.8
    T_WHY = T_REV + 3.3
    T_TW = T_WHY + 4.4
    T_TW_RUN = T_TW + 2.5
    T_Q = T_TW_RUN + 5.6
    DURATION = T_Q + 3.8


def minutes(t):
    """寝てからの分（動画の秒 → 分）。はじめはゆっくり（温まり始めを見せる）"""
    if t < T_CLOCK0:
        return 0.0
    u = clamp01((t - T_CLOCK0) / RACE_LEN)
    return RACE_MIN * u ** 1.6


def speed_now(t):
    return (minutes(t + 0.02) - minutes(t - 0.02)) * 60 / 0.04


# ---------- 場面の置き場所 ----------

def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def zoom(t):
    return 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))


def to_dev(t, x, y):
    sc, y0 = layout(t)
    z = zoom(t)
    fx, fy = ZOOM_F
    x2, y2 = fx + (x - fx) * z, fy + (y - fy) * z
    return CX + (x2 - CX) * sc, y0 + y2 * sc


def scene_scale(t):
    return layout(t)[0] * zoom(t)


def apply_scene(ctx, t):
    sc, y0 = layout(t)
    z = zoom(t)
    fx, fy = ZOOM_F
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)
    ctx.translate(fx * (1 - z), fy * (1 - z))
    ctx.scale(z, z)


def scene_box(t):
    sc, y0 = layout(t)
    return CX * (1 - sc), y0, W * sc, SCENE_H * sc


def stext(ctx, t, s, x, y, size, color=INK, align="center", alpha=1.0, bold=True):
    """場面の中の字（画面の座標に直して描く。iPhone で切れる所・場面の外では出さない）"""
    xd, yd = to_dev(t, x, y)
    sz = max(24.0, size * scene_scale(t))
    w = core.text_width(s, sz)
    x0 = xd - w / 2 if align == "center" else (xd if align == "left" else xd - w)
    bx, by, bw, bh = scene_box(t)
    if x0 < 76 or x0 + w > 1004 or yd - sz / 2 < max(by, 372) or yd + sz / 2 > min(by + bh, 1448):
        return
    if yd + sz / 2 > 1000 and x0 + w > 928:
        return
    text(ctx, s, xd, yd, sz, color, align=align, alpha=alpha, bold=bold)


def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


# ---------- 絵: 部屋（同じ部屋が上下に2つ。A が上の部屋、B が下の部屋） ----------
_FLAKES = np.random.default_rng(7).uniform(0, 1, (46, 4))


def draw_rooms(ctx, t):
    for k in ("a", "b"):
        oy = ROOM_Y[k]
        fill(ctx, hexrgb(WALL))                     # 壁（夜）
        ctx.rectangle(-300, oy, W + 600, FLOOR_Y)
        ctx.fill()
        ctx.set_line_width(2)
        for x in range(-300, W + 300, 54):          # 壁紙のたて縞
            ctx.set_source_rgba(*hexrgb(WALL_L, 0.9))
            ctx.move_to(x, oy)
            ctx.line_to(x, oy + FLOOR_Y)
            ctx.stroke()
        fill(ctx, hexrgb(WOOD))                     # 床
        ctx.rectangle(-300, oy + FLOOR_Y, W + 600, ROOM_H - FLOOR_Y)
        ctx.fill()
        ctx.move_to(-300, oy + FLOOR_Y)
        ctx.line_to(W + 300, oy + FLOOR_Y)
        _stroke(ctx, 3.0)
        draw_window(ctx, t, oy, seed=0 if k == "a" else 0.5)
    fill(ctx, hexrgb("#c9c3b8"))                    # 上の部屋の床と下の部屋の天井（壁の断面）
    ctx.rectangle(-300, ROOM_Y["b"] - SLAB, W + 600, SLAB)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    draw_clock(ctx, t, ROOM_Y["a"])
    draw_room_card(ctx, ROOM_Y["b"])


WIN = (740.0, 22.0, 960.0, 140.0)                   # 窓（左・上・右・下。部屋の中の座標）


def draw_window(ctx, t, oy, seed=0.0):
    x0, y0, x1, y1 = WIN
    y0 += oy
    y1 += oy
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.clip()
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgb(0, *hexrgb(NIGHT0)[:3])
    g.add_color_stop_rgb(1, *hexrgb(NIGHT1)[:3])
    ctx.set_source(g)
    ctx.paint()
    fill(ctx, hexrgb("#fff6c9"))                    # 月
    ctx.arc(x1 - 46, y0 + 36, 17, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, hexrgb(NIGHT0))
    ctx.arc(x1 - 39, y0 + 30, 16, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, hexrgb("#e9eef7"))                    # 外の雪の屋根
    ctx.move_to(x0, y1 - 18)
    ctx.curve_to(x0 + 80, y1 - 36, x0 + 170, y1 - 24, x1, y1 - 32)
    ctx.line_to(x1, y1)
    ctx.line_to(x0, y1)
    ctx.close_path()
    ctx.fill()
    for fx, fy, sp, sz in _FLAKES:                  # 降る雪
        y = y0 - 14 + ((fy + seed + t * (0.16 + 0.12 * sp)) % 1.0) * (y1 - y0 + 28)
        x = x0 + fx * (x1 - x0) + 10 * math.sin(t * 1.3 + fy * 9) + (y - y0) * 0.15
        x = x0 + (x - x0) % (x1 - x0)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.arc(x, y, 2.2 + 3.0 * sz, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.7)               # 窓の霜
    ctx.set_line_width(3)
    for (ax, ay) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        for j in range(3):
            ctx.arc(ax, ay, 12 + j * 10, 0, 2 * math.pi)
            ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(WOOD))             # 窓わく
    ctx.set_line_width(10)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.stroke()
    ctx.move_to((x0 + x1) / 2, y0)
    ctx.line_to((x0 + x1) / 2, y1)
    ctx.stroke()
    ctx.rectangle(x0 - 5, y0 - 5, x1 - x0 + 10, y1 - y0 + 10)
    _stroke(ctx, 3.0)
    ctx.rectangle(x0 + 5, y0 + 5, x1 - x0 - 10, y1 - y0 - 10)
    _stroke(ctx, 2.0, INK, 0.6)


CLK = (600.0, 76.0, 50.0)


def clock_minutes(t):
    """壁の時計: 23時ちょうどに寝る"""
    return 23 * 60 + minutes(t)


def draw_clock(ctx, t, oy):
    cx, cy, r = CLK
    cy += oy
    fill(ctx, hexrgb("#fffdf6"))
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill_preserve()
    _stroke(ctx, 4.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(12):
        a = k * math.pi / 6
        ln = 10 if k % 3 == 0 else 5
        ctx.move_to(cx + (r - 7) * math.sin(a), cy - (r - 7) * math.cos(a))
        ctx.line_to(cx + (r - 7 - ln) * math.sin(a), cy - (r - 7 - ln) * math.cos(a))
        _stroke(ctx, 2.5)
    m = clock_minutes(t)
    for ang, ln, w in ((m / 720 * 2 * math.pi, r * 0.5, 6.0), ((m % 60) / 60 * 2 * math.pi, r * 0.75, 4.5)):
        ctx.move_to(cx, cy)
        ctx.line_to(cx + ln * math.sin(ang), cy - ln * math.cos(ang))
        _stroke(ctx, w)
    sec = math.floor(t) % 60 if t < T_CLOCK0 else math.floor(t * 8) % 60
    a = sec / 60 * 2 * math.pi
    ctx.move_to(cx, cy)
    ctx.line_to(cx + r * 0.8 * math.sin(a), cy - r * 0.8 * math.cos(a))
    _stroke(ctx, 2.0, RED, 0.9)
    fill(ctx, hexrgb(INK))
    ctx.arc(cx, cy, 5, 0, 2 * math.pi)
    ctx.fill()


def draw_room_card(ctx, oy):
    """下の部屋の壁に貼った紙（「部屋 8℃」。字は draw_scene で書く）。2つの部屋は同じ温度"""
    cx, cy = CLK[0], oy + CLK[1]
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-0.03)
    fill(ctx, hexrgb("#fffdf6"))
    core.rrect(ctx, -86, -34, 172, 68, 8)
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.7)
    ctx.restore()
    note.tape(ctx, cx, cy - 34, 70, 20, 0.04)


# ---------- 絵: ベッドと2人（部屋の中の座標） ----------
_BODY_X = np.array([226, 244, 272, 330, 400, 470, 540, 640, 740, 830, 880, 905, 930, 952])
_BODY_Y = np.array([290, 270, 258, 248, 250, 254, 256, 264, 262, 268, 266, 250, 262, 296])


def body_top(xr):
    return float(np.interp(xr, _BODY_X, _BODY_Y))


COV_X0, COV_X1 = 236.0, 958.0                       # 掛けものの頭側・足側の端


def spread(t):
    return ease(clamp01((t - T_SPREAD) / 1.0))


def cover_profile(k, t, n=90):
    """掛けもの2枚の境目（肌側から）を、x ごとに返す。k = "a"（毛布が上）／"b"（毛布が下）"""
    s = sample()
    p = spread(t)
    xs = np.linspace(COV_X0, COV_X1, n)
    if p <= 0:
        cov = np.zeros(n)
    elif p >= 1:
        cov = np.ones(n)
    else:
        front = COV_X1 - p * (COV_X1 - COV_X0 + 80)
        cov = np.clip((xs - front) / 80.0, 0, 1)
    base = np.array([body_top(x) - 2 for x in xs])
    ends = np.clip(np.minimum(xs - COV_X0, COV_X1 - xs) / 22.0, 0, 1) ** 0.6      # 端は丸く薄く
    hd = PX_CM * s["h_b"]
    if k == "a":
        squash = cov * ease(clamp01((t - T_SPREAD - 0.15) / 0.8))
        th_down = (hd - (hd - PX_CM * s["h_a"]) * squash) * ends
        th_blk = BLK_PX * cov * ends
        y1 = base - th_down
        y2 = y1 - th_blk
        return xs, [("down", base, y1), ("blk", y1, y2)]
    th_blk = BLK_PX * cov * ends
    th_down = hd * ends
    y1 = base - th_blk
    y2 = y1 - th_down
    return xs, [("blk", base, y1), ("down", y1, y2)]


def _poly(ctx, oy, xs, lo, hi):
    ctx.move_to(xs[0], oy + lo[0])
    for x, y in zip(xs, hi):
        ctx.line_to(x, oy + y)
    for x, y in zip(xs[::-1], lo[::-1]):
        ctx.line_to(x, oy + y)
    ctx.close_path()


def draw_layer(ctx, oy, xs, lo, hi, kind, seed):
    if np.max(lo - hi) < 0.6:
        return
    _poly(ctx, oy, xs, lo, hi)
    if kind == "down":
        fill(ctx, hexrgb(DOWN))
        ctx.fill_preserve()
        _stroke(ctx, 3.2)
        ctx.save()                                   # キルトの縫い目と、中の羽毛
        _poly(ctx, oy, xs, lo, hi)
        ctx.clip()
        for xq in np.arange(xs[0] + 60, xs[-1], 72):
            yl, yh = float(np.interp(xq, xs, lo)), float(np.interp(xq, xs, hi))
            ctx.move_to(xq, oy + yl)
            ctx.line_to(xq, oy + yh)
            _stroke(ctx, 2.0, DOWN_L, 0.9)
        rng = np.random.default_rng(seed)
        for _ in range(70):
            xq = rng.uniform(xs[0] + 10, xs[-1] - 10)
            v = rng.uniform(0.15, 0.85)
            yl, yh = float(np.interp(xq, xs, lo)), float(np.interp(xq, xs, hi))
            y = yl + (yh - yl) * v
            r = max(2.0, min(7.0, (yl - yh) * 0.11))
            ctx.set_source_rgba(*hexrgb(DOWN_L, 0.95))
            ctx.set_line_width(1.8)
            for dx, dy in ((-r * 0.7, 0), (r * 0.7, 0), (0, -r * 0.6)):   # 羽毛のかたまり（ふわっとした3つの丸）
                ctx.arc(xq + dx, oy + y + dy, r * 0.7, 0, 2 * math.pi)
                ctx.stroke()
        ctx.restore()
    else:
        fill(ctx, hexrgb(BLANKET))
        ctx.fill_preserve()
        _stroke(ctx, 2.8)
        ctx.save()
        _poly(ctx, oy, xs, lo, hi)
        ctx.clip()
        ctx.set_source_rgba(*hexrgb(BLANKET_D, 0.75))
        ctx.set_line_width(1.8)
        for xq in np.arange(xs[0], xs[-1], 10):
            yl = float(np.interp(xq, xs, lo))
            ctx.move_to(xq, oy + yl)
            ctx.line_to(xq + 7, oy + yl - 20)
            ctx.stroke()
        ctx.restore()


def draw_folded(ctx, oy, base_y, amount):
    """たたんだ毛布（足もと）。amount 1 → 0 で広げられて小さくなる"""
    if amount <= 0.02:
        return
    w = 40 + 90 * amount
    xr = COV_X1 - 40 - w
    h = 16 * (0.4 + 0.6 * amount)
    for k in range(3):
        y = oy + base_y - (k + 1) * h
        core.rrect(ctx, xr - k * 4, y, w, h, 7)
        fill(ctx, hexrgb(BLANKET))
        ctx.fill_preserve()
        _stroke(ctx, 2.4)


def draw_bed(ctx, t, k):
    oy = ROOM_Y[k]
    x0, x1 = BED_X0, BED_X1
    fill(ctx, hexrgb(WOOD_D))                       # 頭の板・枠・脚
    core.rrect(ctx, x0, oy + 168, 24, FLOOR_Y - 168, 7)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    fill(ctx, hexrgb(WOOD))
    ctx.rectangle(x0 + 24, oy + MAT_Y + 40, x1 - x0 - 24, 20)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    for lx in (x0 + 34, x1 - 26):
        ctx.rectangle(lx, oy + MAT_Y + 60, 12, FLOOR_Y - MAT_Y - 60)
        fill(ctx, hexrgb(WOOD_D))
        ctx.fill_preserve()
        _stroke(ctx, 2.5)
    fill(ctx, hexrgb("#ffffff"))                    # マットレス
    core.rrect(ctx, x0 + 24, oy + MAT_Y - 4, x1 - x0 - 24, 46, 12)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    ctx.set_source_rgba(*hexrgb(DOWN_L, 0.8))
    ctx.set_line_width(2)
    ctx.move_to(x0 + 30, oy + MAT_Y + 20)
    ctx.line_to(x1 - 8, oy + MAT_Y + 20)
    ctx.stroke()
    fill(ctx, hexrgb("#ffffff"))                    # まくら
    ctx.save()
    ctx.translate(x0 + 86, oy + MAT_Y - 19)
    ctx.scale(86, 25)                               # 2026-10-19 頭を大きくしたのに合わせて枕も大きく
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    draw_sleeper(ctx, t, oy, k)
    xs, lay = cover_profile(k, t)
    for j, (kind, lo, hi) in enumerate(lay):
        draw_layer(ctx, oy, xs, lo, hi, kind, 31 + j + (k == "b") * 5)
    top = lay[-1][2]
    draw_folded(ctx, oy, float(np.interp(COV_X1 - 100, xs, top)) + 3, 1 - spread(t))
    return xs, top


HEAD_S = 1.7                                        # 寝ている人の頭の大きさ（最初の版の何倍か）
SHOW_BREATH = False                                 # 白い息（初版はあり）


def draw_sleeper(ctx, t, oy, k):
    """寝ている人の顔（横から・あお向け）。冷えた部屋なので、息が白い"""
    hx, hy = BED_X0 + 92, oy + MAT_Y - 46
    ax, ay = hx, hy + 33                            # 2026-10-19 頭を大きく（ユーザー指摘）。枕に触れる点を中心に拡大
    ctx.save()
    ctx.translate(ax, ay)
    ctx.scale(HEAD_S, HEAD_S)
    ctx.translate(-ax, -ay)
    # 2026-10-19 あお向けの横顔に（ユーザー指摘「寝ているように見えない」）。
    # 後頭部が下で枕に沈み、顔は天井を向く。頭頂は左（ベッドの頭板側）、あごは右（体の側）
    R = 33.0
    fill(ctx, hexrgb(SKIN_C))
    ctx.arc(hx, hy, R, 0, 2 * math.pi)
    ctx.fill_preserve()
    _stroke(ctx, 3.2)
    ctx.save()                                      # 髪: 頭頂（左）と後頭部（下）
    ctx.arc(hx, hy, R, 0, 2 * math.pi)
    ctx.clip()
    fill(ctx, hexrgb(HAIR))
    ctx.move_to(hx - 2, hy + R + 2)
    ctx.curve_to(hx - 12, hy + 10, hx - 22, hy - 8, hx - 20, hy - R + 2)
    ctx.line_to(hx - R - 4, hy - R - 4)
    ctx.line_to(hx - R - 4, hy + R + 4)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    ctx.arc(hx, hy, R, 0, 2 * math.pi)              # 輪郭をもう一度（髪の上から）
    _stroke(ctx, 3.2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(hx + 6, hy - R + 2)                 # 鼻（上へ出る）
    ctx.curve_to(hx + 8, hy - R - 9, hx + 15, hy - R - 9, hx + 16, hy - R + 3)
    _stroke(ctx, 2.8)
    ctx.arc(hx + 4, hy - 19, 6.0, 0.15 * math.pi, 0.85 * math.pi)   # 閉じた目（上を向いた弧）
    _stroke(ctx, 2.8)
    ctx.move_to(hx + 22, hy - 24)                   # 口（小さく閉じている）
    ctx.line_to(hx + 26, hy - 21)
    _stroke(ctx, 2.4)
    ctx.set_source_rgba(*hexrgb("#f2a3a0", 0.7))   # ほお
    ctx.arc(hx + 14, hy - 8, 6.0, 0, 2 * math.pi)
    ctx.fill()
    ph = t / 2.6 + (0.45 if k == "b" else 0.0)     # 白い息（2026-10-19 頭の後ろの薄い丸に見えると言われたので出さない）
    u = ph % 1.0
    if SHOW_BREATH and u < 0.8:
        v = u / 0.8
        for j in range(3):
            vv = v - j * 0.12
            if vv <= 0:
                continue
            a = (1 - vv) * 0.9
            r = 4 + 9 * vv - j * 1.5
            ctx.arc(hx + 14 + 6 * vv, hy - R - 16 - 46 * vv, max(2, r), 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, a)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb("#8d9bb0", a * 0.8))
            ctx.set_line_width(1.6)
            ctx.stroke()
    ctx.restore()


def th_y(T):
    return TH_BOT + clamp01((T - TH_LO) / (TH_HI - TH_LO)) * (TH_TOP - TH_BOT)


def draw_bed_thermo(ctx, oy, x, y_bulb, T, a):
    """布団に差した温度計（2本とも同じ目盛り 15〜35℃）。玉は体のすぐ上（寝床内）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(0, oy)
    core.rrect(ctx, x - 11, TH_TOP - 20, 22, y_bulb - TH_TOP + 10, 11)
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3.0)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.arc(x, y_bulb, 14, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3)
    ctx.stroke()
    y = th_y(T)
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.rectangle(x - 4.5, y, 9, y_bulb - y)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(2.0)
    for v in range(int(TH_LO), int(TH_HI) + 1):
        yy = th_y(v)
        ln = 14 if v % 5 == 0 else 6
        ctx.move_to(x + 11, yy)
        ctx.line_to(x + 11 + ln, yy)
        ctx.stroke()
    ctx.restore()


Q_REF = 20.0                                       # 矢印の目盛り（W/m²）。2つとも同じ
HEAT_X = (527.0, 700.0)


def draw_heat(ctx, t, oy, xs, top, q, a):
    """布団の表面から部屋へ逃げる熱（ゆらゆら上る赤い矢印）。太さと濃さは逃げる熱に比例（2つ同じ目盛り）"""
    if a <= 0 or q <= 0.2:
        return
    f = clamp01(q / Q_REF)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for j, xr in enumerate(HEAT_X):
        y0 = oy + float(np.interp(xr, xs, top)) - 8
        u = (t * 0.55 + j * 0.33) % 1.0
        al = a * f * math.sin(math.pi * u) * 0.95
        L = 62
        yb = y0 - u * 40
        ctx.set_source_rgba(*hexrgb(HEAT, al))
        ctx.set_line_width(2 + 7 * f)
        pts = []
        for i in range(12):
            v = i / 11
            yy = yb - v * L
            xx = xr + 9 * math.sin(v * 2 * math.pi + t * 4 + j)
            pts.append((xx, yy))
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
        (xa, ya), (xb, yb2) = pts[-2], pts[-1]
        ang = math.atan2(yb2 - ya, xb - xa)
        for sg in (-1, 1):
            ctx.move_to(xb, yb2)
            ctx.line_to(xb - 14 * math.cos(ang + sg * 0.6), yb2 - 14 * math.sin(ang + sg * 0.6))
        ctx.stroke()


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def live_alpha(t):
    return ease_out((t - T_CLOCK0 + 0.3) / 0.4) if t >= T_CLOCK0 - 0.3 else 0.0


def _st(k):
    s = sample()
    return s["A"] if k == "a" else s["B"]


def bed_T(k, t):
    return float(_st(k).t_bed(minutes(t) * 60))


def bed_q(k, t):
    return float(_st(k).q_out(minutes(t) * 60))


def bed_q_skin(k, t):
    return float(_st(k).q_skin(minutes(t) * 60))


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    ctx.push_group()
    ctx.save()
    bx, by, bw, bh = scene_box(t)
    ctx.rectangle(bx, by, bw, bh)
    ctx.clip()
    ctx.save()
    apply_scene(ctx, t)
    draw_rooms(ctx, t)
    la = live_alpha(t)
    tops = {}
    for k in ("a", "b"):
        tops[k] = draw_bed(ctx, t, k)
    for k in ("a", "b"):
        xs, top = tops[k]
        draw_heat(ctx, t, ROOM_Y[k], xs, top, bed_q(k, t), la)
        draw_bed_thermo(ctx, ROOM_Y[k], TH_XR, body_top(TH_XR) - 6, bed_T(k, t), la)
    ctx.restore()
    ctx.restore()
    if la > 0:
        for k in ("a", "b"):
            stext(ctx, t, "35℃", TH_XR + 32, ROOM_Y[k] + TH_TOP, 26, RED, align="left", alpha=la)
    stext(ctx, t, f"部屋 {sample()['room']:.0f}℃", CLK[0], ROOM_Y["b"] + CLK[1], 28, INK)
    for k in ("a", "b"):                            # A・B の丸と名前
        xd, yd = to_dev(t, TAG_X, ROOM_Y[k] + TAG_Y)
        r = 28 * scene_scale(t)
        if yd - r < by + 2 or xd - r < 76:
            continue
        fill(ctx, (1, 1, 1, 0.92))
        ctx.arc(xd, yd, r, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, xd, yd, r, r, INKC[k], seed=13 + (k == "b"), width=3.2)
        text(ctx, TAG[k], xd, yd, max(24.0, 36 * scene_scale(t)), INKC[k])
        if t >= T_SPREAD + 0.6:
            b = ease_out((t - T_SPREAD - 0.6) / 0.3)
            stext(ctx, t, NAME[k], TAG_X + 44, ROOM_Y[k] + TAG_Y, 38, INKC[k], align="left", alpha=b)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def readout_alpha(t):
    if T_CLOCK0 - 0.3 <= t < T_G0:
        return ease_out((t - T_CLOCK0 + 0.3) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def hm(mins):
    m = int(math.floor(mins + 1e-6))
    return f"{m}分" if m < 60 else f"{m // 60}時間{m % 60:02d}分"


Q_SHOW_MIN = 5.0                                   # 逃げる熱は寝てから5分後から出す（入った直後は冷たい布団に熱をとられて大きい）


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    s = sample()
    text(ctx, f"寝てから {hm(minutes(t))}", 580, 1166, 36, INK, alpha=a)
    if T_CLOCK0 + 0.2 < t < T_RACE_END:
        text(ctx, f"再生 {speed_now(t):.0f}倍", 150, 1166, 24, PENCIL, bold=False, align="left", alpha=a)
    mins = minutes(t)
    for k, cx in (("a", 360.0), ("b", 800.0)):
        text(ctx, f"{TAG[k]} {NAME[k]}", cx, 1222, 34, INKC[k], alpha=a)
        text(ctx, f"{bed_T(k, t):.1f}℃", cx, 1280, 54, INK, alpha=a)
        text(ctx, "布団の中の温度", cx, 1330, 26, PENCIL, bold=False, alpha=a)
        if mins >= Q_SHOW_MIN:
            q = bed_q_skin(k, t) * TOP_AREA
            text(ctx, f"逃げる熱 {q:.0f}W", cx, 1392, 40, INK, alpha=a * clamp01((mins - Q_SHOW_MIN) / 2))
    if t >= T_RACE_END:
        u = clamp01((t - T_RACE_END - 0.1) / 0.35)
        k = "a" if s["qa"] < s["qb"] else "b"
        note.pen_circle(ctx, 360.0 if k == "a" else 800.0, 1392, 150, 38, RED, seed=70, width=5, progress=u, alpha=a)
        b = a * ease_out((t - T_RACE_END - 0.3) / 0.3)
        less = 1 - min(s["qa"], s["qb"]) / max(s["qa"], s["qb"])
        note.sticky(ctx, f"{NAME[k]}のほうが\n逃げる熱が {less * 100:.0f}%少ない", 580, 760, 44, "yellow", a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def trial_class():
    d = results()["d"]
    return np.where(d >= RULE_D, 1, np.where(d <= -RULE_D, 0, 2))     # 1=B 0=A 2=ほぼ同じ


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    cls = trial_class()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_A), bgra(COL_B), bgra(COL_C)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[cls[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_WHY) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


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
    cls = trial_class()[:m]
    rows = ((f"B {NAME['b']}が 5%以上 暖かい", int(np.sum(cls == 1)), COL_B),
            (f"A {NAME['a']}が 5%以上 暖かい", int(np.sum(cls == 0)), COL_A),
            ("差が 5%より小さい", int(np.sum(cls == 2)), COL_C))
    for i, (lab, cnt, col) in enumerate(rows):
        y = 1160 + i * 46
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(190, y - 16, 32, 32)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(190, y - 16, 32, 32)
        ctx.stroke()
        text(ctx, lab, 238, y, 32, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 32, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。暖かい＝体から逃げる熱が少ない", 580, 1296, 26, PENCIL, bold=False, alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"毛布が下で 5%以上暖かい回は {pct_i(sh['p_b'])}。\n逃げる熱は 真ん中で {pct_i(sh['d_med'])}少ない",
                    580, 1380, 30, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- なぜ: 羽毛の厚み ----------
BAR_STEP = 0.45


def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def hbars(ctx, t, t0, rows, ys, a, vmax, fmt_v, ticks, tick_lab, x0=330.0, ln=480.0, step=BAR_STEP):
    """横の棒（同じ目盛り）。rows = [(ラベル, 値, 色)]"""
    top, bot = ys[0] - 34, ys[-1] + 34
    ctx.set_line_width(1.5)
    for v in ticks:
        x = x0 + ln * v / vmax
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
        ctx.move_to(x, top)
        ctx.line_to(x, bot)
        ctx.stroke()
    for v in tick_lab:
        text(ctx, fmt_v(v, True), x0 + ln * v / vmax, bot + 22, 24, PENCIL, bold=False, alpha=a)
    for i, ((lab, val, col), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * step
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0 - 14, y, 32, INK, align="right", alpha=a)
        w = ln * min(1.0, val / vmax) * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, fmt_v(val, False), x0 + w + 14, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


WHY_NOTE = "重ねる順番だけなら 差は0。\n羽毛がつぶれた分だけ 熱が逃げる"


def why_done_t():
    return T_WHY + 0.3 + 2 * BAR_STEP + 0.5


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "羽毛布団の厚み（1万回の 真ん中の値）", 580, 650, 40, INK, alpha=a)
    text(ctx, "毛布の重みで、羽毛がつぶれる", 580, 704, 28, PENCIL, bold=False, alpha=a)
    rows = [(f"B {NAME['b']}", sh["h_b"], COL_B), (f"A {NAME['a']}", sh["h_a"], COL_A)]
    hbars(ctx, t, T_WHY, rows, (830.0, 930.0), a, 6.0, lambda v, tk: f"{v:.0f}cm" if tk else f"{v:.1f}cm",
          range(0, 7), (0, 2, 4, 6))
    tb = why_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, WHY_NOTE, 580, 1170, 38, "yellow", a=b, tilt=-0.02)


# ---------- ひねり: 毛布が重いと？ ----------

def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + 2 * BAR_STEP + 0.5


def tw_note():
    sh = shown()
    return f"重いほど 差が広がる。\nでも軽くても 約{pct_i(sh['d_light'])}"


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "毛布を下にして 減った熱（真ん中の値）", 580, 650, 40, INK, alpha=a)
    text(ctx, "同じ1万回を、毛布の重さで分けた", 580, 704, 28, PENCIL, bold=False, alpha=a)
    rows = [(f"軽い毛布 {LIGHT[0]:.1f}〜{LIGHT[1]:.1f}kg", sh["d_light"], COL_B),
            (f"重い毛布 {HEAVY[0]:.1f}〜{HEAVY[1]:.1f}kg", sh["d_heavy"], COL_B)]
    hbars(ctx, t, T_TW_RUN, rows, (830.0, 930.0), a, 0.30, lambda v, tk: pct_i(v), (0, 0.1, 0.2, 0.3), (0, 0.1, 0.2, 0.3),
          x0=410.0, ln=410.0)
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, tw_note(), 580, 1170, 38, "pink", fg=RED, a=b, tilt=-0.02)


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


CD_X, CD_Y = 600.0, 905.0


class MIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに寝室（0秒目から雪が降り、白い息が出て、時計が動く）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 62
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
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
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 840)):
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
            fill(ctx, (*hexrgb(PAPER)[:3], 0.94 * a2))
            core.rrect(ctx, cx - 125, cy - 150, 250, 220, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 150, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 98, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 54, 52, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 84, INK, alpha=a)
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


INTRO = MIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_CLOCK0 - 0.1 <= t < T_CLOCK0 + 1.6:
        b = ease_out((t - T_CLOCK0 + 0.1) / 0.3) * (1 - ease((t - T_CLOCK0 - 1.2) / 0.4))
        note.sticky(ctx, "寝てから1時間", 580, 690, 34, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、毛布が重いと？", 580, 860, a=ba, t_rel=t - T_TW, size=56)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたの家は、\n上？下？", 580, 860, 58, "yellow", a=q, tilt=-0.02)
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
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(110.0, 164.8, 220.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    wind = noise_band(t_end, 60, 3, 1.0)               # 外の風（ひゅう）
    tt = np.arange(len(wind)) / SR
    env = (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, wind * env, 0.5)
    for k in range(int(T_CLOCK0)):                      # 時計の秒（冒頭）
        mx.add(float(k), tick(2400, 0.02), 0.25)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    mx.add(T_SPREAD, whoosh(0.8), 0.35)               # 毛布を広げる
    mx.add(T_SPREAD + 0.5, thump(0.25), 0.25)
    beat(mx, T_CLOCK0, T_RACE_END - 0.8, bpm=118, vol=0.30)
    mx.add(T_RACE_END, bell(784.0, 1.4), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(2):                                 # なぜ
        mx.add(T_WHY + 0.3 + i * BAR_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(why_done_t(), thump(), 0.35)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(2):
        mx.add(T_TW_RUN + 0.3 + i * BAR_STEP, blip(523.3 + 60 * i, 0.12), 0.3)
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
    # (1) 見本の「寝てからの温まり方」の行きつく先が、温まりきったあとの式と一致する
    s = sample()
    checks.append(("見本A 2時間後の逃げる熱（W/m²）が式と同じ", float(s["A"].q_skin(7200.0)), s["qa"], 1e-3))
    checks.append(("見本B 2時間後の逃げる熱（W/m²）が式と同じ", float(s["B"].q_skin(7200.0)), s["qb"], 1e-3))
    checks.append(("見本B 2時間後の寝床内（℃）が式と同じ", float(s["B"].t_bed(7200.0)), s["tb"], 1e-3))
    checks.append(("見本 1時間後の逃げる熱が、行きつく先の1%以内（画面の60分）",
                   float(abs(s["A"].q_skin(3600.0) / s["qa"] - 1)), 0.0, 0.01))
    # (2) つぶれなければ（n→0）、順番を変えても逃げる熱はまったく同じ（熱抵抗の足し算）
    p0 = dict(p)
    p0["n"] = np.full(N_TRIAL, 1e-12)
    p0["squeeze"] = np.zeros(N_TRIAL)
    qa0, qb0, _, _ = heat(p0, layers(p0))
    checks.append(("つぶれないときの A と B の差（最大・W/m²）", float(np.max(np.abs(qa0 - qb0))), 0.0, 1e-9))
    # (3) つぶれ方の式が、Fuller 2015 の測定（2.08 Pa → 14.8 Pa で高さ 約83mm → 約38mm、比 0.46）を n の幅で挟む
    lo = float(loft_ratio(2.08, 0.119, 14.8 - 2.08, N_COMP[0]))
    hi = float(loft_ratio(2.08, 0.119, 14.8 - 2.08, N_COMP[1]))
    print(f"  つぶれ方: 2.08→14.8 Pa の高さの比 n=0.30 で {lo:.3f}、n=0.50 で {hi:.3f}（測定 0.46、±8mm で 0.36〜0.55）")
    checks.append(("n=0.30 の高さの比が 測定の真ん中(0.46)以上", float(lo >= 0.46), 1.0, 0.0))
    checks.append(("n=0.50 の高さの比が 測定の真ん中(0.46)以下", float(hi <= 0.46), 1.0, 0.0))
    # (4) 羽毛の熱抵抗 1cm あたりの幅に、岐阜の2つの値（4cm で1.03、3.8cm で0.88）が入る
    checks.append(("岐阜 1.03/4cm が幅に入る", float(R_PER_CM[0] <= 1.03 / 4 <= R_PER_CM[1]), 1.0, 0.0))
    checks.append(("岐阜 0.88/3.8cm が幅に入る", float(R_PER_CM[0] <= 0.88 / 3.8 <= R_PER_CM[1]), 1.0, 0.0))
    # (5) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["d_med"], sh["p_b"], sh["p_a"])),
                   float(INTRO.correct), 0.0))
    # (6) 見本は1万回の中の1回で、d が真ん中の値の近く
    checks.append(("見本の d が真ん中の値の近く", s["d"], sh["d_med"], 0.01))
    # (7) 画面の回数が足して1万
    checks.append(("3つの色の回数の合計", float(sh["n_a"] + sh["n_b"] + sh["n_c"]), float(N_TRIAL), 0.0))
    # (8) 画面の「重いほど差が広がる」が結果と合っている
    checks.append(("重い毛布の差 > 軽い毛布の差", float(sh["d_heavy"] > sh["d_light"]), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  寝る {T_CLOCK0:.2f}〜{T_RACE_END:.2f}  1万回 {T_G0:.1f}  答え {T_REV:.1f}  なぜ {T_WHY:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（d {s['d']:.3f}）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 9.0, 9.5, 10.5, 12.0, 14.0, 16.0, 18.0, T_RACE_END + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 2.5, T_TW + 1.0, T_TW_RUN + 1.5, tw_done_t() + 1.5,
              T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
