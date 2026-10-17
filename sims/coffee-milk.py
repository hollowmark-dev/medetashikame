"""コーヒーにミルク、先に入れると冷めにくい？ 冷蔵庫のミルクで1万杯ためす。— 2026-10-13 作成（公開予定 10/17）

問い: 「コーヒーにミルク、先に入れると冷めにくい？」（2行）。前提「10分後に飲む。冷たいミルクを今入れる？飲む直前？」
      A 先が温かい ／ B あとが温かい ／ C どっちも同じ

答えの決め方（計算の前に決めた規則。answer_by_rule。コードに書いてから1万杯を流した）:
      1杯ごとに「飲むときの温度の差 = 先に入れた杯 − 飲む直前に入れた杯」を出す。
      温度計の表示の細かさ（0.1℃）より差が小さい杯は「同じ」と数える。
      先のほうが 0.1℃以上 温かい杯が 60%以上なら A、あとのほうが 0.1℃以上 温かい杯が 60%以上なら B、どちらでもなければ C。

モデル（カップ1つを、中身の温度が1つの「かたまり」として扱う。よく混ざっているとする）
  中身の熱容量 C = 比熱×重さ（コーヒー 4.18 J/gK・1.00 g/ml、牛乳 3.93 J/gK・1.03 g/ml）
  C dT/dt = −[ 壁と底から逃げる熱 + 水面から逃げる熱（対流＋放射） + 湯気（蒸発）で逃げる熱 ]
    壁と底:   g_wall × (ぬれている壁の面積 + 底の面積) × (T − 室温)              … 温度の差に比例（ニュートンの冷却の法則）
    水面:     h_top × 水面の面積 × (T − 室温) + 0.95σ(T⁴ − 室温⁴) × 水面の面積  … 対流は差に比例、放射は少し強めに効く
    蒸発:     潜熱 L(T) × 水面の面積 × h_m × (飽和水蒸気の濃さ(T) − 湿度×飽和水蒸気の濃さ(室温))
              h_m = h_top ÷ (空気の密度×比熱×ルイス数^(2/3))（熱と湯気の運ばれ方の相似。チルトン＝コルバーン）
              飽和水蒸気圧は Buck の式。温度が高いほど急に増える（80℃は60℃の約2.4倍）。蒸発した分だけ中身も減る
  カップ: 内径 D の円柱（取っ手・カップ自体の熱容量は入れない＝温めておいたカップ）。ミルクを足すと液面が上がり、ぬれた壁が増える
  ミルク: 冷蔵庫の温度のまま、入れた瞬間に混ざる（熱容量で重みをつけた平均）。冷蔵庫に入れていた間は温まらない
  1杯ごとにでたらめに変えるもの（一様乱数）:
    コーヒー 150〜220ml、注いだときの温度 80〜92℃、ミルク 10〜40ml、冷蔵庫 3〜7℃、室温 18〜28℃、湿度 30〜70%、
    カップの内径 7.0〜8.5cm、g_wall 7〜12 W/m²K、h_top 5〜9 W/m²K、待つ時間 5〜15分
  時間は1秒きざみのルンゲ＝クッタ（4次）。

ひねり: 「待つのが30分なら？」 同じ1万杯で、待つ時間だけ30分にする。
締め:   「なんで 先に入れると冷めにくいの？」→ 画面に1行「熱いほど 湯気で冷めるから」（蒸発なしだと差が4分の1になることで照合）。
概要欄用: 蒸発を入れない計算（ニュートンの冷却の法則だけ）と、ミルクが常温（＝室温）の計算も出す。
結果（2026-10-13）: 1万杯すべてで先が温かい（差 平均3.2℃）→ A。30分なら平均4.2℃。蒸発なしだと0.8℃、常温のミルクで2.3℃。

照合（check_answers）は run_checks を参照。見本（並ぶ2杯）は1万杯とは別に、真ん中くらいの条件で1杯つくる。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "coffee-milk"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_EPS = 0.1                                    # ℃。温度計の表示の細かさ。これより小さい差は「同じ」
RULE_SHARE = 0.6                                  # 6割以上の杯で同じ側が温かければ、その側の勝ち


def answer_by_rule(diff):
    """diff = 1杯ごとの（先に入れた杯 − 飲む直前に入れた杯）の、飲むときの温度の差（℃）"""
    diff = np.asarray(diff)
    if np.mean(diff >= RULE_EPS) >= RULE_SHARE:
        return 0                                  # A 先が温かい
    if np.mean(diff <= -RULE_EPS) >= RULE_SHARE:
        return 1                                  # B あとが温かい
    return 2                                      # C どっちも同じ


# ---------- 物の値 ----------
C_COF, RHO_COF = 4180.0, 1.00                     # J/kgK, g/ml
C_MILK, RHO_MILK = 3930.0, 1.03
SIGMA, EPS_R = 5.670e-8, 0.95
RHOCP_AIR = 1.18 * 1006.0                         # 空気の密度×比熱（J/m³K）
LE23 = 0.85 ** (2 / 3)                            # ルイス数（空気中の水蒸気）^(2/3)
DT = 1.0                                          # 秒
N_CUP = 10000

RANGES = dict(vc=(150.0, 220.0), t0=(80.0, 92.0), vm=(10.0, 40.0), tm=(3.0, 7.0), tr=(18.0, 28.0),
              rh=(0.30, 0.70), d=(0.070, 0.085), g_wall=(7.0, 12.0), h_top=(5.0, 9.0), wait=(5.0, 15.0))
TYPICAL = {k: 0.5 * (a + b) for k, (a, b) in RANGES.items()}   # 見本の1杯（真ん中の条件）
TYPICAL.update(vc=180.0, t0=86.0, vm=25.0, tm=5.0, tr=23.0, wait=10.0)


def draw_params(n, seed=20261017):
    rng = np.random.default_rng(seed)
    return {k: rng.uniform(a, b, n) for k, (a, b) in RANGES.items()}


def p_sat(T):
    """飽和水蒸気圧（Pa）。Buck (1996) の式"""
    return 611.21 * np.exp((18.678 - T / 234.5) * (T / (257.14 + T)))


def rho_v(T):
    """飽和水蒸気の濃さ（kg/m³）"""
    return p_sat(T) * 0.018015 / (8.314 * (T + 273.15))


def latent(T):
    return 2.501e6 - 2370.0 * T                   # J/kg


class Cups:
    """カップ n 杯ぶんを同時に冷ます。状態は温度 T（℃）・熱容量 C（J/K）・体積 V（m³）"""

    def __init__(self, p, T, C, V, evap=True, k_fixed=None):
        self.p = p
        self.T, self.C, self.V = T.astype(float), C.astype(float), V.astype(float)
        self.A_top = math.pi * p["d"] ** 2 / 4
        self.evap = evap
        self.k_fixed = k_fixed                    # 照合用: dT/dt = −k(T−室温) だけ（1/秒）
        self.rv_room = p["rh"] * rho_v(p["tr"])

    def losses(self, T, V):
        """逃げる熱（W）: (壁と底＋水面の対流＋放射, 蒸発) と、蒸発する水の量（kg/s）"""
        p = self.p
        A = self.A_top
        h = V / A
        side = math.pi * p["d"] * h
        sens = p["g_wall"] * (side + A) * (T - p["tr"]) + p["h_top"] * A * (T - p["tr"]) \
            + EPS_R * SIGMA * A * ((T + 273.15) ** 4 - (p["tr"] + 273.15) ** 4)
        if not self.evap:
            return sens, 0.0 * T, 0.0 * T
        hm = p["h_top"] / (RHOCP_AIR * LE23)
        mdot = A * hm * np.maximum(rho_v(T) - self.rv_room, 0.0)
        return sens, latent(T) * mdot, mdot

    def rate(self, T, C, V):
        if self.k_fixed is not None:
            return -self.k_fixed * (T - self.p["tr"]), 0.0 * T, 0.0 * T
        sens, ev, mdot = self.losses(T, V)
        return -(sens + ev) / C, -C_COF * mdot, -mdot / 1000.0

    def step(self, dt=DT, mask=None):
        """4次のルンゲ＝クッタで dt 秒すすめる。mask が False の杯は止めておく"""
        T, C, V = self.T, self.C, self.V
        k1 = self.rate(T, C, V)
        k2 = self.rate(T + dt / 2 * k1[0], C + dt / 2 * k1[1], V + dt / 2 * k1[2])
        k3 = self.rate(T + dt / 2 * k2[0], C + dt / 2 * k2[1], V + dt / 2 * k2[2])
        k4 = self.rate(T + dt * k3[0], C + dt * k3[1], V + dt * k3[2])
        d = [dt / 6 * (a + 2 * b + 2 * c + e) for a, b, c, e in zip(k1, k2, k3, k4)]
        if mask is None:
            mask = np.ones_like(T, bool)
        self.T = np.where(mask, T + d[0], T)
        self.C = np.where(mask, C + d[1], C)
        self.V = np.where(mask, V + d[2], V)

    def add_milk(self, mask, vm, tm):
        """ミルクを入れて、すぐ混ざる"""
        cm = C_MILK * vm * RHO_MILK / 1000.0
        T_new = (self.C * self.T + cm * tm) / (self.C + cm)
        self.T = np.where(mask, T_new, self.T)
        self.C = np.where(mask, self.C + cm, self.C)
        self.V = np.where(mask, self.V + vm * 1e-6, self.V)


def black(p):
    """注いだばかりのブラック（温度・熱容量・体積）"""
    return p["t0"].copy(), C_COF * p["vc"] * RHO_COF / 1000.0, p["vc"] * 1e-6


def race(p, wait_min=None, milk_t=None, evap=True, k_fixed=None, dt=DT, record=False, rec_dt=5.0):
    """先に入れる杯（a）と、飲む直前に入れる杯（b）。飲むとき（待つ時間ちょうど）の温度を返す。
    wait_min: 待つ時間（分）。None なら1杯ごとのでたらめ。milk_t: ミルクの温度（None なら冷蔵庫の温度）"""
    n = len(p["vc"])
    wait = (p["wait"] if wait_min is None else np.full(n, float(wait_min))) * 60.0
    tm = p["tm"] if milk_t is None else milk_t
    T0, C0, V0 = black(p)
    a = Cups(p, T0, C0, V0, evap, k_fixed)
    b = Cups(p, T0, C0, V0, evap, k_fixed)
    a.add_milk(np.ones(n, bool), p["vm"], tm)
    t = 0.0
    rec = {"t": [0.0], "a": [a.T.copy()], "b": [b.T.copy()], "ea": [], "eb": []}
    next_rec = rec_dt
    while True:
        h = np.clip(wait - t, 0.0, dt)            # 最後の1歩は、待つ時間ちょうどで止まるように短くする
        go = h > 1e-9
        if not go.any():
            break
        if record:
            for key, cup in (("ea", a), ("eb", b)):
                _, ev, _ = cup.losses(cup.T, cup.V)
                rec[key].append(ev)
        a.step(h, go)
        b.step(h, go)
        t += dt
        if record and t >= next_rec - 1e-9:
            rec["t"].append(t)
            rec["a"].append(a.T.copy())
            rec["b"].append(b.T.copy())
            next_rec += rec_dt
    b_before = b.T.copy()
    b.add_milk(np.ones(n, bool), p["vm"], tm)
    out = dict(Ta=a.T, Tb=b.T, Tb_before=b_before, diff=a.T - b.T, wait=wait)
    if record:
        out["rec"] = {k: np.array(v) for k, v in rec.items()}
    return out


def black_k(p, minutes=20.0):
    """ブラックのまま20分冷ましたときの、見かけの冷却定数（1/分）。ln((T0−室温)/(T20−室温))÷20"""
    T0, C0, V0 = black(p)
    c = Cups(p, T0, C0, V0)
    for _ in range(int(minutes * 60 / DT)):
        c.step()
    return np.log((p["t0"] - p["tr"]) / (c.T - p["tr"])) / minutes


def evap_share(p):
    """注いだ直後の、逃げる熱のうち湯気（蒸発）の割合"""
    T0, C0, V0 = black(p)
    c = Cups(p, T0, C0, V0)
    sens, ev, _ = c.losses(c.T, c.V)
    return ev / (sens + ev)


def george(p, wait_s, k):
    """George の閉じた式（ニュートンの冷却だけ・ミルクを入れても冷却定数が同じとき）:
    飲むときの差（先 − あと）= Vm/(Vc+Vm)·(室温 − ミルク)·(1 − e^{−k·待つ時間})。体積で重みをつける形"""
    return p["vm"] / (p["vc"] + p["vm"]) * (p["tr"] - p["tm"]) * (1 - np.exp(-k * wait_s))


# ---------- 1万杯の計算（数秒） ----------
_DATA = None


def data():
    global _DATA
    if _DATA is None:
        cache = OUT / "data.npz"
        if cache.exists():
            z = np.load(cache)
            _DATA = {k: z[k] for k in z.files}
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            p = draw_params(N_CUP)
            m = race(p)
            w30 = race(p, wait_min=30.0)
            room = race(p, milk_t=p["tr"])
            noev = race(p, evap=False)
            k20 = black_k(p)
            es = evap_share(p)
            _DATA = dict(m_diff=m["diff"], m_Ta=m["Ta"], m_Tb=m["Tb"], m_Tbb=m["Tb_before"],
                         w_diff=w30["diff"], w_Ta=w30["Ta"], w_Tb=w30["Tb"],
                         r_diff=room["diff"], n_diff=noev["diff"], k20=k20, evs=es,
                         **{"p_" + k: v for k, v in p.items()})
            np.savez_compressed(cache, **_DATA)
    return _DATA


def params():
    d = data()
    return {k[2:]: v for k, v in d.items() if k.startswith("p_")}


def shown():
    d = data()
    s = {}
    for key in ("m", "w", "r", "n"):
        x = d[key + "_diff"]
        s[key] = dict(mean=float(x.mean()), med=float(np.median(x)), lo=float(np.percentile(x, 5)),
                      hi=float(np.percentile(x, 95)), mx=float(x.max()), mn=float(x.min()),
                      share_a=float(np.mean(x >= RULE_EPS)), share_b=float(np.mean(x <= -RULE_EPS)),
                      share_same=float(np.mean(np.abs(x) < RULE_EPS)), n_a=int(np.sum(x >= RULE_EPS)),
                      n_b=int(np.sum(x <= -RULE_EPS)), n_same=int(np.sum(np.abs(x) < RULE_EPS)))
    s["m"].update(Ta=float(d["m_Ta"].mean()), Tb=float(d["m_Tb"].mean()), Tbb=float(d["m_Tbb"].mean()))
    s["w"].update(Ta=float(d["w_Ta"].mean()), Tb=float(d["w_Tb"].mean()))
    s["k20"] = (float(np.percentile(d["k20"], 5)), float(np.median(d["k20"])), float(np.percentile(d["k20"], 95)))
    s["evs"] = (float(np.percentile(d["evs"], 5)), float(np.median(d["evs"])), float(np.percentile(d["evs"], 95)))
    return s


def report():
    s = shown()
    for key, name in (("m", "本編（冷蔵庫のミルク・待つ5〜15分）"), ("w", "ひねり（待つ30分）"), ("r", "締め（常温のミルク）"),
                      ("n", "蒸発なし（ニュートンだけ）")):
        x = s[key]
        print(f"{name}: 差 平均 {x['mean']:+.2f}℃ 中央 {x['med']:+.2f} 5〜95% {x['lo']:+.2f}〜{x['hi']:+.2f} "
              f"最小 {x['mn']:+.2f} 最大 {x['mx']:+.2f}  先が0.1℃以上 {x['share_a']:.4f} あと {x['share_b']:.4f} 同じ {x['share_same']:.4f}"
              f" → 規則の答え {'ABC'[answer_by_rule(data()[key + '_diff'])]}")
    print(f"飲むときの平均: 先 {s['m']['Ta']:.1f}℃ あと {s['m']['Tb']:.1f}℃（入れる前 {s['m']['Tbb']:.1f}℃）  30分: 先 {s['w']['Ta']:.1f} あと {s['w']['Tb']:.1f}")
    print(f"ブラックの見かけの冷却定数（1/分）5%/中央/95%: {s['k20']}  注いだ直後の蒸発の割合: {s['evs']}")


if __name__ == "__main__" and "--compute" in sys.argv:
    data()
    report()
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, SR, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh)
from engine.parts import bgra, check_true, grid_image, loop_back, pct, stills  # noqa: E402

note.use()
note.DATE = "10.17"                               # 日付欄（公開予定日）

BIG_Q = ["コーヒーにミルク、", "先に入れると冷めにくい？"]
DETAIL = "10分ほどで飲むなら。冷たいミルクで1万杯"
LABELS = ["先が温かい", "あとが温かい", "どっちも同じ"]
CORRECT = 0                                       # answer_by_rule で1万杯の結果から決めた答え。ずれたら run_checks が止める

COL_A, INK_A = "#f2a46f", "#c4581f"               # 先にミルク（だいだい）
COL_B, INK_B = "#8fbbe3", "#2f6fae"               # あとでミルク（青）
COL_SAME = "#c9c6bd"
COFFEE = "#3b2416"
LATTE = "#a87a52"
MILK = "#fbf8f1"
STEAM = "#a3b2c6"
STEAM_TOP = 672.0
MUG = "#fdfcf8"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_X = 5.0                                     # 冒頭（カウントの間）の時計の速さ（実際の5秒＝動画の1秒）
RACE_X = 62.0                                     # くらべる間（実際の62秒＝動画の1秒）
TW_X = 450.0                                      # ひねり（30分）
POUR_A = 1.25                                     # 0秒目からの、先の杯にミルクを注ぐ長さ（動画の秒）
POUR_B = 0.9                                      # 飲む直前に注ぐ長さ（時計は止める）
TW_POUR_A = 0.5


def setup():
    global T_R1, T_DRINK, T_G0, T_G1, T_REV, T_TW, T_TW_RUN, T_TW_R1, T_TW_DRINK, T_WB, T_Q, DURATION
    S0 = T_GO * INTRO_X
    T_R1 = T_GO + (600.0 - S0) / RACE_X + 0.25    # 立ち上がりの0.5秒は加速するので少し長い
    T_DRINK = T_R1 + POUR_B
    T_G0 = T_DRINK + 2.6                          # 1万杯
    T_G1 = T_G0 + 2.6
    T_REV = T_G1 + 0.3                            # 答え
    T_TW = T_REV + 3.0                            # ひねり
    T_TW_RUN = T_TW + 2.4
    T_TW_R1 = T_TW_RUN + TW_POUR_A + 1800.0 / TW_X
    T_TW_DRINK = T_TW_R1 + 0.6
    T_WB = T_TW_DRINK + 1.9                       # 差の棒
    T_Q = T_WB + 3.4                              # 締め
    DURATION = T_Q + 4.4


def S_main(t):
    """本編の見本の時計（実際の秒）。0〜600秒"""
    if t < T_GO:
        return max(0.0, t) * INTRO_X
    u = t - T_GO
    s = T_GO * INTRO_X + INTRO_X * u + (RACE_X - INTRO_X) * (max(0.0, u - 0.25) if u > 0.5 else u * u)
    return min(600.0, s)


def S_tw(t):
    return min(1800.0, max(0.0, t - T_TW_RUN - TW_POUR_A) * TW_X)


# ---------- 見本の2杯（真ん中の条件） ----------
_SAMPLE = {}


def sample(wait):
    if wait not in _SAMPLE:
        p = {k: np.array([float(v)]) for k, v in TYPICAL.items()}
        r = race(p, wait_min=wait, record=True, rec_dt=1.0)
        rec = r["rec"]
        e0 = float(rec["eb"][0][0])
        _SAMPLE[wait] = dict(t=rec["t"], a=rec["a"][:, 0], b=rec["b"][:, 0],
                             ea=np.concatenate([rec["ea"][:, 0], rec["ea"][-1:, 0]]) / e0,
                             eb=np.concatenate([rec["eb"][:, 0], rec["eb"][-1:, 0]]) / e0,
                             Ta=float(r["Ta"][0]), Tb=float(r["Tb"][0]), Tbb=float(r["Tb_before"][0]),
                             T0=float(p["t0"][0]))
    return _SAMPLE[wait]


def samp_at(sm, s, key):
    return float(np.interp(s, sm["t"], sm[key]))


# ---------- 置き場所 ----------
XA, XB = 320.0, 840.0                             # 2つのカップの中心
RIM_Y = 1020.0                                    # 口（だ円の中心）
MUG_W, MUG_H, RIM_RY = 262.0, 232.0, 36.0
TH_DX = 52.0                                      # 温度計はカップの中心から内側へ
TH_LO, TH_HI = 40.0, 90.0                         # 温度計の目盛り（2本とも同じ）
TH_Y_LO, TH_Y_HI = 975.0, 705.0                   # 40℃・90℃ の高さ


def th_y(T):
    return TH_Y_LO + (T - TH_LO) / (TH_HI - TH_LO) * (TH_Y_HI - TH_Y_LO)


def mix(c1, c2, f):
    a, b = hexrgb(c1), hexrgb(c2)
    return tuple(a[i] * (1 - f) + b[i] * f for i in range(3)) + (1.0,)


def draw_mug_back(ctx, cx, a):
    """カップの口の奥側（中の壁）"""
    ctx.save()
    ctx.translate(cx, RIM_Y)
    ctx.scale(MUG_W / 2, RIM_RY)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb("#e9e4d8", a))
    ctx.fill()


def draw_liquid(ctx, cx, milk_f, a, swirl=0.0, swirl_t=0.0):
    """液面（口より少し下）。milk_f は 0（ブラック）〜1（ミルクが混ざりきった色）"""
    ctx.save()
    ctx.translate(cx, RIM_Y + 9)
    ctx.scale(MUG_W / 2 - 12, RIM_RY - 8)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    c = mix(COFFEE, LATTE, milk_f)
    ctx.set_source_rgba(c[0], c[1], c[2], a)
    ctx.fill()
    if swirl > 0:                                 # 注いだミルクのうず（混ざると消える）
        ctx.save()
        ctx.translate(cx, RIM_Y + 9)
        ctx.scale(1.0, (RIM_RY - 8) / (MUG_W / 2 - 12))
        ctx.set_source_rgba(*hexrgb(MILK, 0.9 * swirl * a))
        ctx.set_line_width(9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(2):
            ph = swirl_t * 4.0 + k * math.pi
            for i in range(40):
                u = i / 39
                r = 12 + u * (MUG_W / 2 - 34)
                ang = ph + u * 3.6
                (ctx.move_to if i == 0 else ctx.line_to)(r * math.cos(ang), r * math.sin(ang))
            ctx.stroke()
        ctx.restore()


def draw_mug_front(ctx, cx, band, side, a):
    """カップの胴（手前）と取っ手。side = −1 なら取っ手は左、+1 なら右"""
    x0, x1 = cx - MUG_W / 2, cx + MUG_W / 2
    yb = RIM_Y + MUG_H
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # 取っ手
    hx = x1 if side > 0 else x0
    ctx.new_path()
    ctx.save()
    ctx.translate(hx + side * 6, RIM_Y + 105)
    ctx.scale(side, 1)
    ctx.move_to(0, -62)
    ctx.curve_to(78, -70, 88, 52, 0, 56)
    ctx.line_to(0, 30)
    ctx.curve_to(52, 28, 50, -40, 0, -36)
    ctx.close_path()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(MUG, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95 * a))
    ctx.set_line_width(4)
    ctx.stroke()
    # 胴（下が少し丸い）
    ctx.new_path()
    ctx.move_to(x0, RIM_Y)
    ctx.line_to(x0 + 8, yb - 34)
    ctx.curve_to(x0 + 12, yb + 2, x1 - 12, yb + 2, x1 - 8, yb - 34)
    ctx.line_to(x1, RIM_Y)
    ctx.save()
    ctx.translate(cx, RIM_Y)
    ctx.scale(MUG_W / 2, RIM_RY)
    ctx.arc(1, 0, 1e-6, 0, 0)
    ctx.arc(0, 0, 1, 0, math.pi)
    ctx.restore()
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(MUG, a))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    ctx.set_source_rgba(*hexrgb(band, 0.9 * a))       # 色の帯（だいだい＝先・青＝あと）
    ctx.rectangle(x0 - 10, RIM_Y + 118, MUG_W + 20, 44)
    ctx.fill()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.95 * a))
    ctx.set_line_width(4.5)
    ctx.stroke()
    # 口の縁（だ円）
    ctx.save()
    ctx.translate(cx, RIM_Y)
    ctx.scale(MUG_W / 2, RIM_RY)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_line_width(4.5)
    ctx.stroke()


def draw_thermo(ctx, x, T, a, labels_side):
    """料理用の棒の温度計（カップに差してある）。赤い柱の高さ＝温度。2本とも同じ目盛り"""
    if a <= 0:
        return
    top, bot = TH_Y_HI - 24, RIM_Y + 40
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    core.rrect(ctx, x - 14, top, 28, bot - top, 14)
    ctx.set_source_rgba(1, 1, 1, 0.92 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3.5)
    ctx.stroke()
    y = th_y(max(TH_LO - 2, min(TH_HI + 1, T)))
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    core.rrect(ctx, x - 6, y, 12, bot - y, 6)
    ctx.fill()
    ctx.set_line_width(2.5)
    for v in range(int(TH_LO), int(TH_HI) + 1, 5):
        yy = th_y(v)
        big = v % 10 == 0
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ln = 16 if big else 9
        ctx.move_to(x + labels_side * 14, yy)
        ctx.line_to(x + labels_side * (14 + ln), yy)
        ctx.stroke()
        if big:
            text(ctx, f"{v}", x + labels_side * 36, yy, 26, PENCIL, align="left" if labels_side > 0 else "right",
                 bold=False, alpha=a)


def draw_steam(ctx, cx, amount, t, seed, a):
    """湯気。amount（注いだばかりのブラック＝1）が大きいほど、本数が多く・濃く・高く上がる"""
    if a <= 0 or amount <= 0.02:
        return
    rng = np.random.default_rng(seed)
    n = 13
    ctx.save()
    ctx.rectangle(0, STEAM_TOP, W, RIM_Y - STEAM_TOP)      # 問いと三択にかからないように
    ctx.clip()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(n):
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.6, 0.9)
        x0 = cx + (k / (n - 1) - 0.5) * MUG_W * 0.86 + rng.uniform(-10, 10)
        if abs(x0 - (cx + (TH_DX if cx < 580 else -TH_DX))) < 18:
            x0 += 36
        amp = rng.uniform(14, 26)
        wl = rng.uniform(110, 160)
        u = (t * sp + ph) % 1.0
        vis = clamp01(amount * n - k)              # 湯気が少ないと本数が減る
        al = 0.85 * a * vis * min(1.0, 0.35 + 0.65 * amount) * math.sin(math.pi * u) ** 0.8
        if al <= 0.02:
            continue
        rise = 190 * min(1.2, 0.55 + 0.6 * amount)
        y_bot = RIM_Y - 4 - u * rise
        L = 120 + 50 * amount
        ctx.set_source_rgba(*hexrgb(STEAM, al))
        ctx.set_line_width(7 + 4 * amount)
        for i in range(18):
            v = i / 17
            yy = y_bot - v * L
            xx = x0 + amp * math.sin((yy + t * 120) / wl * 2 * math.pi + k) * (0.4 + v)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
    ctx.restore()


def draw_carton(ctx, x, y, ang, a):
    """ミルクの紙パック（だれのものでもない絵）。(x, y) は注ぎ口のあたり、ang は傾き"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    # 注ぎ口が (0, 0)、パックは +y 側に伸びる
    w, h = 96, 170
    ctx.move_to(-w / 2, 34)
    ctx.line_to(0, 0)
    ctx.line_to(w / 2, 34)
    ctx.line_to(w / 2, 34 + h)
    ctx.line_to(-w / 2, 34 + h)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95 * a))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#9cc3e6", 0.95 * a))
    ctx.rectangle(-w / 2 + 2, 34 + h * 0.55, w - 4, h * 0.22)
    ctx.fill()
    # 冷たい印（雪の結晶を手描きで）
    ctx.set_source_rgba(*hexrgb(INK_B, 0.9 * a))
    ctx.set_line_width(3)
    cx0, cy0 = 0, 34 + h * 0.3
    for k in range(3):
        an = k * math.pi / 3
        ctx.move_to(cx0 - 17 * math.cos(an), cy0 - 17 * math.sin(an))
        ctx.line_to(cx0 + 17 * math.cos(an), cy0 + 17 * math.sin(an))
    ctx.stroke()
    ctx.restore()


def draw_stream(ctx, x0, y0, x1, y1, a, wob_t):
    if a <= 0:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for wdt, col, al in ((16, INK, 0.75), (11, MILK, 1.0)):
        ctx.set_source_rgba(*hexrgb(col, al * a))
        ctx.set_line_width(wdt)
        for i in range(16):
            u = i / 15
            xx = x0 + (x1 - x0) * u ** 0.6 + 2.5 * math.sin(wob_t * 30 + u * 9)
            yy = y0 + (y1 - y0) * u
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
    # しぶき
    ctx.set_source_rgba(*hexrgb(MILK, a))
    for k in range(5):
        an = math.pi + (k + 0.5) / 5 * math.pi
        r = 12 + 8 * ((wob_t * 7 + k * 0.37) % 1)
        ctx.arc(x1 + r * math.cos(an) * 1.8, y1 + 6 + r * math.sin(an), 4, 0, 2 * math.pi)
        ctx.fill()


# ---------- 場面（2杯） ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    if t < T_TW:
        return 1 - ease((t - T_G0) / 0.4)
    if t < T_WB:
        return ease((t - T_TW - 1.4) / 0.5)
    return 1 - ease((t - T_WB) / 0.4)


def scene_state(t):
    """いま見せている見本・時計・各杯の表示温度・ミルクの混ざり・注ぐ様子"""
    if t < T_TW:
        sm, s = sample(10.0), S_main(t)
        pa = clamp01(t / POUR_A)                  # 先の杯: 0秒目から注いでいる
        pb = clamp01((t - T_R1) / POUR_B)
        pour_a = (0.0 <= t < POUR_A + 0.5, t)
        pour_b_t = t - T_R1
        x = RACE_X
    else:
        sm, s = sample(30.0), S_tw(t)
        pa = clamp01((t - T_TW_RUN) / TW_POUR_A)
        pb = clamp01((t - T_TW_R1) / 0.6)
        pour_a = (T_TW_RUN - 0.2 <= t < T_TW_RUN + TW_POUR_A + 0.3, t - T_TW_RUN + (POUR_A - TW_POUR_A))
        pour_b_t = (t - T_TW_R1) * POUR_B / 0.6
        x = TW_X
    black_now = samp_at(sm, s, "b")
    Ta = samp_at(sm, s, "a")
    # 注いでいる間は、ブラックから混ざった温度へなめらかに
    Ta_show = black_now + (Ta - black_now) * ease(pa)
    Tb_show = black_now if pb <= 0 else sm["Tbb"] + (sm["Tb"] - sm["Tbb"]) * ease(pb)
    ea = samp_at(sm, s, "ea") if pa >= 1 else (samp_at(sm, s, "eb") * (1 - pa) + samp_at(sm, s, "ea") * pa)
    eb = samp_at(sm, s, "eb") if pb <= 0 else samp_at(sm, s, "eb") * (1 - 0.35 * pb)
    return dict(sm=sm, s=s, Ta=Ta_show, Tb=Tb_show, ma=ease(pa), mb=ease(pb), ea=ea, eb=eb, pour_a=pour_a,
                pour_b_t=pour_b_t, pb=pb, X=x)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    st = scene_state(t)
    ctx.push_group()
    if t < 0.5:                                    # 0秒目に、場面がポンと置かれる
        sc = 1 + 0.035 * (1 - ease_out(t / 0.5))
        ctx.translate(580, 1100)
        ctx.scale(sc, sc)
        ctx.translate(-580, -1100)
    for cx in (XA, XB):
        draw_mug_back(ctx, cx, 1.0)
    sw_a = clamp01(1 - (t - (POUR_A if t < T_TW else T_TW_RUN + TW_POUR_A)) / 1.6) if st["ma"] > 0 else 0.0
    draw_liquid(ctx, XA, st["ma"], 1.0, swirl=sw_a * st["ma"], swirl_t=t)
    sw_b = clamp01(1 - (st["pour_b_t"] - POUR_B) / 1.4) if st["pb"] > 0 else 0.0
    draw_liquid(ctx, XB, st["mb"], 1.0, swirl=sw_b * st["mb"], swirl_t=t)
    draw_steam(ctx, XA, st["ea"], t, 3, 1.0)
    draw_steam(ctx, XB, st["eb"], t, 4, 1.0)
    rise = ease_out(t / 0.7) if t < 0.7 else 1.0       # 0秒目に温度計を差したところ（室温から上がる）
    tr = TYPICAL["tr"]
    draw_thermo(ctx, XA + TH_DX, tr + (st["Ta"] - tr) * rise, 1.0, -1)
    draw_thermo(ctx, XB - TH_DX, tr + (st["Tb"] - tr) * rise, 1.0, +1)
    draw_mug_front(ctx, XA, COL_A, -1, 1.0)
    draw_mug_front(ctx, XB, COL_B, +1, 1.0)
    # 先の杯に注ぐ（0秒目から）
    on, tp = st["pour_a"]
    if on:
        lift = ease_out((tp - POUR_A) / 0.5)      # 注ぎ終わったら上へ引く
        ca = 1 - lift
        px, py = XA - 80 - 60 * lift, RIM_Y - 250 - 160 * lift
        draw_carton(ctx, px, py, -2.05 + 0.5 * lift, ca)
        if tp < POUR_A:
            draw_stream(ctx, px + 6, py + 4, XA - 30, RIM_Y + 6, 1.0, tp)
    # あとの杯: 待っているパック（あいだ）→ 飲む直前に飛んで注ぐ
    tb = st["pour_b_t"]
    rest = (580.0, RIM_Y + 40)
    over = (XB + 92, RIM_Y - 250)
    if tb < -0.35:
        draw_carton(ctx, rest[0], rest[1], 0.0, 1.0)
    elif tb < POUR_B + 0.5:
        m = ease((tb + 0.35) / 0.35)
        lift = ease_out((tb - POUR_B) / 0.5)
        px = rest[0] + (over[0] - rest[0]) * m + 50 * lift
        py = rest[1] + (over[1] - rest[1]) * m - 160 * lift
        draw_carton(ctx, px, py, 2.05 * m - 0.5 * lift, 1 - lift)
        if 0 <= tb < POUR_B:
            draw_stream(ctx, px - 6, py + 4, XB + 30, RIM_Y + 6, 1.0, tb)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    draw_labels(ctx, t, st, a)


def draw_labels(ctx, t, st, a):
    """下の名札（0秒目から）と、温度の数字（シミュが始まってから）"""
    for cx, name, sub, ink in ((330.0, "先にミルク", "すぐ入れる", INK_A), (805.0, "あとでミルク", "飲む直前に入れる", INK_B)):
        text(ctx, name, cx, 1312, 38, ink, alpha=a)
        text(ctx, sub, cx, 1354, 27, INK, bold=False, alpha=a)
    if t < T_GO - 0.1:
        return
    b = a * ease_out((t - T_GO + 0.1) / 0.4)
    done = (t >= T_DRINK) if t < T_TW else (t >= T_TW_DRINK)
    for cx, T, key in ((330.0, st["Ta"], "a"), (805.0, st["Tb"], "b")):
        text(ctx, f"{T:.1f}℃", cx, 1406, 58, INK, alpha=b)
    # 真ん中: 経過時間
    s = st["s"]
    mm, ss = int(s // 60), int(s % 60)
    clock = f"{mm}分{ss:02d}秒"
    if not done:
        text(ctx, "経過", 580, 760, 30, PENCIL, bold=False, alpha=b)
        text(ctx, clock, 580, 808, 46, INK, alpha=b)
        text(ctx, f"再生 {st['X']:.0f}倍", 580, 856, 26, PENCIL, bold=False, alpha=b)
        if st["pb"] > 0 or (st["pour_b_t"] > -0.35):
            text(ctx, "飲む直前", 580, 900, 30, RED, alpha=b)
    if done:
        t0 = T_DRINK if t < T_TW else T_TW_DRINK
        g = ease_out((t - t0) / 0.3) * a
        sm = st["sm"]
        note.sticky(ctx, f"{int(round(sm['t'][-1] / 60))}分後に飲む", 580, 760, 34, "yellow", a=g, tilt=-0.03)
        note.pen_circle(ctx, 330, 1406, 120, 40, RED, seed=71, width=6, progress=clamp01((t - t0 - 0.3) / 0.35), alpha=a)
        g2 = ease_out((t - t0 - 0.6) / 0.3) * a
        note.sticky(ctx, f"先が {sm['Ta'] - sm['Tb']:.1f}℃ 温かい", 580, 890, 38, "pink", fg=RED, a=g2, tilt=0.02)


# ---------- 1万杯のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}
DIFF_LO, DIFF_HI = 0.5, 6.0                       # 色の濃さの範囲（℃）


def cell_colors():
    d = data()["m_diff"]
    f = np.clip((d - DIFF_LO) / (DIFF_HI - DIFF_LO), 0, 1)
    lo, hi = np.array(hexrgb("#fbd9bd")[:3]), np.array(hexrgb("#c9531c")[:3])
    rgb = lo[None] * (1 - f[:, None]) + hi[None] * f[:, None]
    out = np.zeros((len(d), 4), np.uint8)
    out[:, 0], out[:, 1], out[:, 2], out[:, 3] = rgb[:, 2] * 255, rgb[:, 1] * 255, rgb[:, 0] * 255, 255
    same = np.abs(d) < RULE_EPS
    neg = d <= -RULE_EPS
    out[same] = bgra(COL_SAME)
    out[neg] = bgra(COL_B)
    return out


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    m = min(N_CUP, key * G_COLS)
    cols.reshape(-1, 4)[:m] = cell_colors()[:m]
    _GRID[key] = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_TW) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    d = data()["m_diff"]
    n = N_CUP * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000杯", 580, 622, 34, INK, alpha=a)
    x = d[:int(n)]
    cnt = (int(np.sum(x >= RULE_EPS)), int(np.sum(x <= -RULE_EPS)), int(np.sum(np.abs(x) < RULE_EPS)))
    for i, (lab, col) in enumerate(zip(LABELS, ("#e07a3f", COL_B, COL_SAME))):
        y = 1205 + i * 58
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, f"{'ABC'[i]} {lab}", 282, y, 36, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt[i])}杯", 905, y, 36, INK, align="right", alpha=a)
    text(ctx, "1マス＝1杯。色がこいほど 先のほうが温かい", 580, 1392, 26, PENCIL, bold=False, alpha=a)
    # 答え
    if t >= T_REV:
        sh = shown()["m"]
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, "1万杯すべて 先が温かい", 580, 790, 46, "pink", fg=RED, a=b, tilt=-0.02)
        b2 = ease_out((t - T_REV - 1.1) / 0.3) * a
        note.sticky(ctx, f"差は 平均 {sh['mean']:.1f}℃", 580, 990, 44, "yellow", a=b2, tilt=0.02)


# ---------- 棒: 差の平均（同じものさし） ----------
BAR_X0, BAR_LEN, BAR_MAX = 250.0, 560.0, 5.0


def draw_hbar(ctx, y, val, col, lab, a, g=1.0):
    text(ctx, lab, BAR_X0, y - 46, 32, INK, align="left", alpha=a)
    w = val / BAR_MAX * BAR_LEN * g
    if w > 1:
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        core.rrect(ctx, BAR_X0, y - 20, w, 40, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.stroke()
    text(ctx, f"{val:.1f}℃", BAR_X0 + w + 14, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def bars_alpha(t):
    if t < T_WB:
        return 0.0
    return ease_out((t - T_WB) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def draw_bars(ctx, t):
    a = bars_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "飲むときの温度の差（先 − あと）", 580, 650, 40, INK, alpha=a)
    text(ctx, "（1万杯の平均）", 580, 700, 30, PENCIL, bold=False, alpha=a)
    g1 = 1.0
    g2 = ease_out((t - T_WB - 0.4) / 0.6)
    draw_hbar(ctx, 830, sh["m"]["mean"], "#f2a46f", "5〜15分待つ（さっきの1万杯）", a, g1)
    draw_hbar(ctx, 965, sh["w"]["mean"], "#d9743b", "30分待つ", a, g2)
    # ものさし（0〜5℃）
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(2)
    for v in range(0, 6):
        x = BAR_X0 + v / BAR_MAX * BAR_LEN
        ctx.move_to(x, 1010)
        ctx.line_to(x, 1022)
        ctx.stroke()
        text(ctx, f"{v}℃", x, 1046, 24, PENCIL, bold=False, alpha=a)
    if t >= T_WB + 0.9:
        b = ease_out((t - T_WB - 0.9) / 0.3) * a
        note.sticky(ctx, "待つほど 差は広がる", 580, 1190, 44, "mint", a=b, tilt=-0.02)
        b2 = ease_out((t - T_WB - 1.4) / 0.3) * a
        text(ctx, f"30分後の平均: 先 {sh['w']['Ta']:.0f}℃・あと {sh['w']['Tb']:.0f}℃", 580, 1310, 28,
             INK, bold=False, alpha=b2)


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


CD_X, CD_Y = 580.0, 820.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに2つのカップ（0秒目から湯気・ミルクを注ぐ）"""
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
            core.rrect(ctx, cx - 130, cy - 165, 260, 245, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 165, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 108, 42, RED, seed=41, alpha=a2, align="center")
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
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "スタート", 580, 660, 34, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    # ひねり
    if T_TW <= t < T_TW_RUN:
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "待つのが30分なら？", 580, 760, a=ba, t_rel=t - T_TW, size=52)
    draw_bars(ctx, t)
    # 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで 先に入れると\n冷めにくいの？", 580, 800, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.1) / 0.3)
        note.sticky(ctx, "熱いほど 湯気で冷めるから", 580, 1010, 44, "pink", fg=RED, a=r, tilt=0.025)
        r2 = ease_out((t - T_Q - 1.6) / 0.3)
        text(ctx, "（くわしくは概要欄に）", 580, 1130, 30, PENCIL, bold=False, alpha=r2)


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
    band = np.clip((f - lo) / 150, 0, 1) * np.clip((hi - f) / 600, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 277.2, 329.6)), 1.0, bgm=True)
    tt = np.arange(int(SR * DURATION)) / SR
    # 注ぐ音（とぽとぽ）: 0秒目と、飲む直前
    pour = band_noise(DURATION, 300.0, 1600.0, 5, 0.03)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 9.0 * tt) * np.sin(2 * np.pi * 2.7 * tt)
    env = np.zeros_like(tt)
    for t0, d in ((0.0, POUR_A), (T_R1, POUR_B), (T_TW_RUN, TW_POUR_A), (T_TW_R1, 0.6)):
        env += ((tt >= t0) & (tt < t0 + d)).astype(float)
    env = np.convolve(env, np.ones(1200) / 1200, mode="same")
    mx.add(0, pour * mod * env, 1.0, bgm=True)
    # 湯気のしゅー（ごく小さく）: 場面が出ている間
    hiss = band_noise(DURATION, 3000.0, 9000.0, 6, 0.008)
    sa = np.array([scene_alpha(x) for x in tt[::480]])
    mx.add(0, hiss * np.interp(tt, tt[::480], sa), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.2)
    # 本編: 1分ごとに時計
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    for m in range(1, 10):
        ts = np.interp(m * 60.0, [S_main(x) for x in np.arange(T_GO, T_R1 + 0.01, 0.02)], np.arange(T_GO, T_R1 + 0.01, 0.02))
        mx.add(float(ts), tick(2400.0, 0.03), 0.12)
    mx.add(T_R1, blip(659.3, 0.15), 0.35)
    mx.add(T_DRINK, bell(784.0, 1.4), 0.5)
    mx.add(T_DRINK + 0.6, blip(880.0, 0.15), 0.35)
    # 1万杯
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_REV + 1.1, blip(659.3, 0.15), 0.35)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.45)
    beat(mx, T_TW_RUN + TW_POUR_A, T_TW_R1, bpm=140, vol=0.4)
    mx.add(T_TW_DRINK, bell(784.0, 1.2), 0.45)
    mx.add(T_WB + 0.4, blip(698.5, 0.15), 0.35)
    mx.add(T_WB + 1.3, bell(1046.5, 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.1, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    d = data()
    p = params()
    checks = []
    # (1) ニュートンの冷却だけ・冷却定数が一定のとき、George の閉じた式と一致（熱容量で重みをつけた形）
    sub = {k: v[:2000] for k, v in p.items()}
    k = 0.04 / 60
    r = race(sub, k_fixed=k)
    cc = C_COF * sub["vc"] * RHO_COF / 1000
    cm_ = C_MILK * sub["vm"] * RHO_MILK / 1000
    exact = cm_ / (cc + cm_) * (sub["tr"] - sub["tm"]) * (1 - np.exp(-k * sub["wait"] * 60))
    checks.append(("ニュートンだけ: 差が George の閉じた式と一致（最大のずれ・℃）", float(np.max(np.abs(r["diff"] - exact))), 0.0, 1e-3))
    # 体積で重みをつけた George の式そのもの（比熱・密度を同じにしたとき）とも一致
    checks.append(("George の式（体積の重み）と熱容量の重みの差は小さい（℃）",
                   float(np.max(np.abs(exact - george(sub, sub["wait"] * 60, k)))), 0.0, 0.1))
    # (2) 時間の刻み 1秒 と 0.5秒 で結果が変わらない
    sub2 = {k: v[:1000] for k, v in p.items()}
    r1 = race(sub2)["diff"]
    r2 = race(sub2, dt=0.5)["diff"]
    checks.append(("刻み1秒と0.5秒の差（最大・℃）", float(np.max(np.abs(r1 - r2))), 0.0, 0.005))
    # (3) Buck の式: 100℃の飽和水蒸気圧 ≈ 101.3kPa
    checks.append(("飽和水蒸気圧 100℃（kPa）", float(p_sat(100.0) / 1000), 101.325, 0.5))
    # (4) ブラックの見かけの冷却定数（20分）が、実測（Kurzweg 2017: コーヒー 0.036/分・お湯 0.045/分）の幅に入る
    checks.append(check_true("ブラックの冷却定数の中央値が 0.030〜0.050/分", 0.030 <= sh["k20"][1] <= 0.050, f"{sh['k20'][1]:.4f}"))
    # (5) 答え: 計算の前に決めた規則で出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(d["m_diff"])), float(INTRO.correct), 0.0))
    # (6) ひねり: 30分でも A、差は本編より大きい
    checks.append(("ひねり: 30分でも規則の答えは A", float(answer_by_rule(d["w_diff"])), 0.0, 0.0))
    checks.append(check_true("ひねり: 30分の差の平均 > 本編の差の平均", sh["w"]["mean"] > sh["m"]["mean"]))
    # (7) 締め「熱いほど湯気で冷めるから」: 蒸発を入れないと差は半分より小さい（差の大半は湯気から）
    checks.append(check_true("蒸発なしの差の平均 < 本編の差の平均の半分", sh["n"]["mean"] < 0.5 * sh["m"]["mean"],
                             f"{sh['n']['mean']:.2f} / {sh['m']['mean']:.2f}"))
    # (8) 見本の2杯（真ん中の条件）も先が温かい。画面の「先が○℃温かい」
    sm = sample(10.0)
    checks.append(check_true("見本: 先の杯が温かい", sm["Ta"] > sm["Tb"], f"{sm['Ta']:.2f} > {sm['Tb']:.2f}"))
    sw = sample(30.0)
    checks.append(check_true("ひねりの見本: 先の杯が温かい", sw["Ta"] > sw["Tb"], f"{sw['Ta']:.2f} > {sw['Tb']:.2f}"))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    sm, sw = sample(10.0), sample(30.0)
    print(f"長さ {DURATION:.1f}秒  見本10分: 先 {sm['Ta']:.2f} あと {sm['Tb']:.2f}（入れる前 {sm['Tbb']:.2f}）  "
          f"30分: 先 {sw['Ta']:.2f} あと {sw['Tb']:.2f}")
    print(f"T_R1={T_R1:.2f} T_DRINK={T_DRINK:.2f} T_G0={T_G0:.2f} T_REV={T_REV:.2f} T_TW={T_TW:.2f} T_TW_RUN={T_TW_RUN:.2f} "
          f"T_TW_DRINK={T_TW_DRINK:.2f} T_WB={T_WB:.2f} T_Q={T_Q:.2f}")
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.6, 1.0, 1.5, 2.5, 5.0, 8.0, 8.6, 10.0, 13.0, 16.0, T_R1 - 0.3, T_R1 + 0.5, T_DRINK + 1.2,
              T_G0 + 1.5, T_G1 + 0.2, T_REV + 1.6, T_TW + 1.0, T_TW_RUN + 2.0, T_TW_DRINK + 0.8, T_WB + 2.2, T_Q + 2.5,
              DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
