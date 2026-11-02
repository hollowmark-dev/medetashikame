"""シャボン玉が長く割れないのは、夏？冬？ 夏の公園と冬の公園で同時に吹いて1万回。— 2026-10-26 作成（公開予定 11/2・45秒前後）

これは実験の結果ではなく、「計算の見立て」。夏と冬のシャボン玉の寿命をくらべた実験は見つからなかった（FACTCHECK 2026-10-26）。
蒸発と排液の研究の式に、気象庁の平年値をあてはめて、でたらめな条件を1万回ためした。

モデル（シャボン玉1つの膜の厚さ h [nm]。膜が薄くなる理由は2つ。ある厚さまで薄くなったら割れる）
  ① 蒸発による薄化   dh/dt = −C_E × e_s(T) × (1 − RH) × (1 + K_V × 風)    [nm/s]
      「蒸発の速さは 飽和水蒸気圧 × (1 − 相対湿度) に比例」… Gilet ほか（arXiv:0709.4412、式(2)）で確認。
      e_s(T) = 6.112 × exp(17.62 T / (243.12 + T)) [hPa]（Magnus の式・WMO）。
      C_E = 1.5 nm/s/hPa … 仮定。垂直の大きな石けん膜の薄化速度が「毎秒数十〜約百nm」という実測（Pasquet ほか、
        arXiv:2402.06950）の桁に、22℃・湿度54%（e_s×(1−RH) ≒ 12 hPa → 18 nm/s、風1で約25 nm/s）で合わせた。
      K_V = 0.4 /(m/秒) … そよ風で蒸発が速まる度合い。仮定（出典は確認できなかった）。
      「湿度が高いほど寿命が延びる」実測（Pasquet ほか: 63% → 約22秒、39% → 約12秒、垂直の膜）と向きが合うことを run_checks で確かめる。
  ② 排液による薄化   dh/dt = −D × h²,   D = D0 × (R / 2cm) × (μ(25℃) / μ(T)) / cf    [nm/s]
      液が重力で下へ流れる。粘度が大きいほど遅い → 水の粘度の温度依存を使う（0℃ 1.792、10℃ 1.307、20℃ 1.002、
        25℃ 0.890、30℃ 0.797、40℃ 0.653 mPa·s。https://chem-casts.com/data-tables/water-viscosity-data-table 。純水の値）。
      「h² に比例」「玉の半径 R に比例」の形は仮定（比例の形は出典なし）。D0 = 2.5e-5 /(nm·s)（h=1000nm・R=2cm・cf=1・25℃で 25 nm/s）も仮定。
      cf = 液の濃さ（石けん液は水より粘る）。粘度が水の cf 倍。1〜4（仮定）。同じ回の夏と冬で同じ液（同じボトルを持っていく）。
      Pasquet ほかは「排液の影響は蒸発に比べ無視できる」。この計算でも、蒸発が主役で排液はおまけの大きさにしてある。
  割れる厚さ h_c … 30〜150 nm（仮定の幅）。「数十nmまで薄くなって自発的に破れる」（Roux ほか、Phys. Rev. Fluids 7, L011601, 2022）。
      破裂の厚さそのものは未決着。
  はじめの膜の厚さ h0 … 400〜1500 nm（仮定）。吹き出し直後の厚さの実測は確認できなかった（垂直膜の線形薄化の最大が約1μm）。
  玉の半径 R … 1〜3 cm（仮定）。そよ風 … 0〜1.5 m/秒（仮定）。
  「割れるまでの時間」… 吹いてから h が h_c になるまで。1回は 0.25 秒きざみで足し算。ほこりなどの核による穴・風で割れる・凍る は入れていない。

  条件の幅（気象庁 東京の平年値 1991〜2020: 1月 5.4℃・湿度51%、8月 26.9℃・74%
      https://www.data.jma.go.jp/obd/stats/etrn/view/nml_sfc_ym.php?prec_no=44&block_no=47662 を中心にとった）
      夏: 気温 25〜33℃・湿度 55〜85%、冬: 気温 0〜10℃・湿度 35〜65%（昼の公園を見込んで、平年値の日平均の前後にとった幅）。
  1回ごとにすべてでたらめ（夏と冬で、気温・湿度・風・玉の大きさ・はじめの厚さ・割れる厚さは別々。液の濃さだけ同じ）。

問い: 「シャボン玉が／長く割れないのは、／冬？夏？」（10/26 統括: 左右と記号の並び A冬・B夏 にそろえて「冬？夏？」に）（夏の公園と冬の公園で、同時に1つずつ吹く）
      選択肢: 夏 ／ ほぼ同じ ／ 冬。**正解の記号は A**。結果がどれでも LABELS の並びを入れ替えて、正解を A の位置に置く（TAG・CORRECT が追う）。
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「冬のほうが長く割れなかった回」の割合 p と、割れるまでの時間の比（冬÷夏）の中央値 r で、
      p ≥ 60% かつ r ≥ 1.2 なら「冬」、p ≤ 40% かつ r ≤ 0.83 なら「夏」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、夏でも雨上がり（湿度90%）なら？」（夏の湿度だけ 90% にして同じ1万回を再計算）。
締め: 「冬の公園で、ためしてみますか？」（答えは出さない）＋「コメントで教えてください」

言葉: 1万回の結果の真ん中は「中央値」（初出で一度説明）。見本の1回には「たとえば、この1回では」、数字には「この置き方なら」。
商品名・ブランドは出さない。
乱数の種は見本（並んで吹く2つ）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "shabon-kisetsu"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261102
DT = 0.25                                          # 足し算のきざみ（秒）
TMAX = 3600.0
# 夏・冬の条件
T_SUM, RH_SUM = (25.0, 33.0), (0.55, 0.85)
T_WIN, RH_WIN = (0.0, 10.0), (0.35, 0.65)
RH_RAIN = 0.90                                     # ひねり（夏の雨上がり）
V_WIND = (0.0, 1.5)                                # そよ風 m/秒
# 液と玉
H0 = (400.0, 1500.0)                               # はじめの膜の厚さ nm
HC = (30.0, 150.0)                                 # 割れる厚さ nm
R_CM = (1.0, 3.0)                                  # 玉の半径 cm
CF = (1.0, 4.0)                                    # 液の濃さ（粘度が水の何倍か）
# 薄くなる速さ
C_E, K_V = 1.5, 0.4                                # nm/s/hPa、1/(m/秒)
D0 = 2.5e-5                                        # 1/(nm·s)
MU_T = [0.0, 10.0, 20.0, 25.0, 30.0, 40.0]
MU_V = [1.792, 1.307, 1.002, 0.890, 0.797, 0.653]  # mPa·s（純水）
MU25 = 0.890

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_R_HI, RULE_R_LO = 0.60, 0.40, 1.2, 0.83


def answer_by_rule(p_win, r_med):
    """p_win = 冬のほうが長く割れなかった割合、r_med = 割れるまでの時間の比（冬÷夏）の中央値。'win' / 'same' / 'sum'"""
    if p_win >= RULE_HI and r_med >= RULE_R_HI:
        return "win"
    if p_win <= RULE_LO and r_med <= RULE_R_LO:
        return "sum"
    return "same"


def es_hpa(T):
    return 6.112 * np.exp(17.62 * np.asarray(T, float) / (243.12 + np.asarray(T, float)))


def mu_w(T):
    return np.interp(T, MU_T, MU_V)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    return dict(T_s=u(T_SUM), RH_s=u(RH_SUM), v_s=u(V_WIND), h0_s=u(H0), R_s=u(R_CM), hc_s=u(HC),
                T_w=u(T_WIN), RH_w=u(RH_WIN), v_w=u(V_WIND), h0_w=u(H0), R_w=u(R_CM), hc_w=u(HC),
                cf=u(CF))


def coef(d, side, rh=None):
    """薄くなる速さ: 蒸発 E [nm/s]、排液の係数 Dc [1/(nm·s)]"""
    T = d["T_" + side]
    RH = d["RH_" + side] if rh is None else np.full(len(T), rh)
    E = C_E * es_hpa(T) * (1.0 - RH) * (1.0 + K_V * d["v_" + side])
    Dc = D0 * (d["R_" + side] / 2.0) * (MU25 / mu_w(T)) / d["cf"]
    return E, Dc


def run(d, side, rh=None, evap=True, drain=True, hist=False):
    """割れるまでの時間（秒）。hist=True（1回ぶんだけ）なら (時刻[秒], 膜の厚さ[nm]) の配列も返す"""
    E, Dc = coef(d, side, rh)
    if not evap:
        E = np.zeros_like(E)
    if not drain:
        Dc = np.zeros_like(Dc)
    n = len(E)
    h = d["h0_" + side].astype(float).copy()
    hc = d["hc_" + side]
    tpop = np.full(n, np.inf)
    t = 0.0
    H = [(0.0, float(h[0]))] if hist else None
    while t < TMAX and np.isinf(tpop).any():
        act = np.isinf(tpop)
        h1 = h / (1.0 + Dc * h * DT)               # 排液（この1ステップ分は式で解ける）
        h2 = h1 - E * DT                           # 蒸発
        hit = act & (h2 <= hc)
        frac = (h - hc) / np.maximum(h - h2, 1e-12)
        tpop = np.where(hit, t + frac * DT, tpop)
        h = np.where(act, h2, h)
        t += DT
        if hist and act[0]:
            H.append((t if not hit[0] else float(tpop[0]), float(max(h2[0], hc[0])) if not hit[0] else float(hc[0])))
    if hist:
        return tpop, np.array(H)
    return tpop
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
    keys = ("t_s", "t_w", "t_s90", "t_s_ev", "t_w_ev", "t_s_dr", "t_w_dr")
    if fn.exists():
        z = np.load(fn)
        r = {k: z[k] for k in keys}
    else:
        r = dict(t_s=run(d, "s"), t_w=run(d, "w"), t_s90=run(d, "s", rh=RH_RAIN),
                 t_s_ev=run(d, "s", drain=False), t_w_ev=run(d, "w", drain=False),
                 t_s_dr=run(d, "s", evap=False), t_w_dr=run(d, "w", evap=False))
        np.savez(fn, **r)
    r["p"] = d
    _RES["m"] = r
    return r


def shown():
    r = results()
    p = r["p"]
    ts, tw, ts90 = r["t_s"], r["t_w"], r["t_s90"]
    ratio = tw / ts
    ratio90 = tw / ts90
    Es, _ = coef(p, "s")
    Ew, _ = coef(p, "w")
    Es0 = C_E * es_hpa(p["T_s"]) * (1 - p["RH_s"])
    Ew0 = C_E * es_hpa(p["T_w"]) * (1 - p["RH_w"])
    return dict(p_win=float((tw > ts).mean()), n_win=int((tw > ts).sum()), n_sum=int((tw <= ts).sum()),
                r_med=float(np.median(ratio)), r_q=np.percentile(ratio, [10, 25, 75, 90]),
                med_s=float(np.median(ts)), med_w=float(np.median(tw)),
                q_s=np.percentile(ts, [10, 90]), q_w=np.percentile(tw, [10, 90]),
                p90=float((tw > ts90).mean()), r90=float(np.median(ratio90)), med_s90=float(np.median(ts90)),
                p_ev=float((r["t_w_ev"] > r["t_s_ev"]).mean()), r_ev=float(np.median(r["t_w_ev"] / r["t_s_ev"])),
                p_dr=float((r["t_w_dr"] > r["t_s_dr"]).mean()),
                r_dr=float(np.median(np.minimum(r["t_w_dr"], TMAX) / np.minimum(r["t_s_dr"], TMAX))),   # 排液だけだと1時間で割れない回もある（上限で打ち切り）
                e_ratio=float(np.median(Es0 / Ew0)), e_ratio_w=float(np.median(Es / Ew)),
                mu_ratio=float(np.median(mu_w(p["T_w"]) / mu_w(p["T_s"]))),
                n_unfinished=int(np.isinf(ts).sum() + np.isinf(tw).sum() + np.isinf(ts90).sum()))


def sec_s(t):
    """秒 → '38秒' / '1分05秒'"""
    t = int(math.floor(t + 1e-9))
    return f"{t // 60}分{t % 60:02d}秒" if t >= 60 else f"{t}秒"


def sec_about(t):
    """約 の付く短い言い方"""
    if t < 90:
        return f"約{int(round(t / 5.0)) * 5}秒"
    return f"約{t / 60:.1f}分"


def report():
    sh = shown()
    print(f"冬が長持ち p={sh['p_win']:.4f}（冬 {sh['n_win']}回 / 夏 {sh['n_sum']}回）  時間の比(冬÷夏) 中央値 r={sh['r_med']:.3f}  "
          f"10/25/75/90% {np.round(sh['r_q'], 2)}")
    print(f"  答え {answer_by_rule(sh['p_win'], sh['r_med'])}")
    print(f"  割れるまでの時間の中央値 夏 {sh['med_s']:.1f}秒 10/90% {np.round(sh['q_s'], 1)} / "
          f"冬 {sh['med_w']:.1f}秒 10/90% {np.round(sh['q_w'], 1)}")
    print(f"  蒸発の勢い 夏÷冬（風なし）の中央値 {sh['e_ratio']:.2f}倍 / 風こみ {sh['e_ratio_w']:.2f}倍  粘度 冬÷夏 {sh['mu_ratio']:.2f}倍")
    print(f"  蒸発だけ: p={sh['p_ev']:.3f} r={sh['r_ev']:.2f} / 排液だけ: p={sh['p_dr']:.3f} r={sh['r_dr']:.2f}  未完了 {sh['n_unfinished']}")
    print(f"  ひねり 夏の湿度90%: 冬が長持ち p={sh['p90']:.3f}  r={sh['r90']:.3f}  夏の中央値 {sh['med_s90']:.1f}秒")


def pasquet_ratio():
    """蒸発だけのモデルで、同じ気温・風なしの 湿度63% と 39% の寿命の比。Pasquet ほか(2024)の実測は 約22秒÷約12秒"""
    one = lambda x: np.array([x], float)   # noqa: E731
    d = dict(T_s=one(22.0), RH_s=one(0.63), v_s=one(0.0), h0_s=one(1000.0), R_s=one(2.0), hc_s=one(50.0), cf=one(1.0))
    a = run(d, "s", rh=0.63, drain=False)[0]
    b = run(d, "s", rh=0.39, drain=False)[0]
    return float(a / b)


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    print(f"  湿度63%と39%の寿命の比（モデル・蒸発のみ）{pasquet_ratio():.2f}（Pasquet ほかの実測 22÷12 = {22 / 12:.2f}）")
    sys.exit(0)


# =====================================================================
# 見本（並んで吹く2つ）を選ぶ
# =====================================================================
_SAMPLE = None


def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_win"], sh["r_med"])


def sample():
    """見本: 1万回の中の1回（その回の値そのもの）。
    条件: 割れるまでの時間が 夏・冬とも 中央値の近く（±15%）、比が中央値の近く（±8%）、答えと同じ向き（冬が長い、など）。
    その中で比が中央値に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    ts, tw = r["t_s"], r["t_w"]
    ratio = tw / ts
    cand = np.nonzero((np.abs(ts / sh["med_s"] - 1) < 0.15) & (np.abs(tw / sh["med_w"] - 1) < 0.15)
                      & (np.abs(ratio / sh["r_med"] - 1) < 0.08))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(ratio[cand] - sh["r_med"]))])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    t_s, hs = run(d1, "s", hist=True)
    t_w, hw = run(d1, "w", hist=True)
    q = {k: (v[i].item() if hasattr(v[i], "item") else v[i]) for k, v in p.items()}
    _SAMPLE = dict(i=i, p=q, t_s=float(ts[i]), t_w=float(tw[i]), ratio=float(ratio[i]),
                   h_s=hs, h_w=hw, chk=(float(t_s[0]), float(t_w[0])))
    return _SAMPLE


def h_at(hist, tau):
    return float(np.interp(tau, hist[:, 0], hist[:, 1]))


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    p = s["p"]
    print("見本", s["i"], "夏:", round(p["T_s"], 1), "℃", round(p["RH_s"] * 100), "% 風", round(p["v_s"], 2), "R", round(p["R_s"], 2),
          "h0", round(p["h0_s"]), "hc", round(p["hc_s"]), "|冬:", round(p["T_w"], 1), "℃", round(p["RH_w"] * 100), "% 風", round(p["v_w"], 2),
          "R", round(p["R_w"], 2), "h0", round(p["h0_w"]), "hc", round(p["hc_w"]), "| cf", round(p["cf"], 2),
          "| 夏", sec_s(s["t_s"]), "冬", sec_s(s["t_w"]), "比", round(s["ratio"], 2))
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
note.DATE = "11.2"                                 # 日付欄（公開予定日）

COL_S, INK_S = "#f4ad6a", "#b8601a"                # 夏（だいだい）
COL_W, INK_W = "#8fbbe8", "#2f63a8"                # 冬（水色）

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は A（結果しだいで並びを入れ替える。run_checks が確かめる）
KEY_LABEL = {"win": "冬", "same": "ほぼ同じ", "sum": "夏"}
_AK = answer_key()
LABELS = [KEY_LABEL[_AK]] + [v for k, v in (("sum", "夏"), ("same", "ほぼ同じ"), ("win", "冬")) if k != _AK]
CORRECT = 0                                        # 正解は A（0番目）
TAG = {"sum": "ABC"[LABELS.index("夏")], "win": "ABC"[LABELS.index("冬")]}
NAME = {"sum": "夏", "win": "冬"}
COLS = {"sum": COL_S, "win": COL_W}
INKC = {"sum": INK_S, "win": INK_W}

BIG_Q = ["シャボン玉が長く割れないのは、", "冬？夏？"]                    # 定位置（上）の2行
BIG_Q3 = ["シャボン玉が", "長く割れないのは、", "冬？夏？"]               # 1コマ目の3行（同じ大きさ）
DETAIL = "冬と夏の公園で、同じ液を同時に吹く"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 10.5                                    # T_GO から2つとも割れるまで
R0 = 0.9                                           # 冒頭の進み（シミュの秒／動画の秒）。答えが見えないよう、ほとんど進めない

# 画面の置き場所（左＝夏、右＝冬）
PN = {"win": dict(x0=80.0, x1=520.0, cx=300.0), "sum": dict(x0=580.0, x1=1020.0, cx=800.0)}   # 左＝冬（A）・右＝夏（B）。記号の並びと左右をそろえる（統括 10/26）
PY0, PY1 = 830.0, 1485.0
GY = 1246.0                                        # 地面の上端
FY = 1298.0                                        # 人の足もと
CARD_Y = 1308.0                                    # ストップウォッチの札


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_TW1, T_TW2, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_s"], s["t_w"]))
    T_FIN2 = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 80, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 2000.0
    for _ in range(50):
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
    T_G0 = T_FIN2 + 1.8
    T_G1 = T_G0 + 3.2
    T_REV = T_G1 + 3.4
    T_ANS2 = T_REV + 2.0
    T_TW1 = T_ANS2 + 3.4
    T_TW2 = T_TW1 + 3.2
    T_Q = T_TW2 + 4.6
    DURATION = T_Q + 6.5


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


def hs_at(t):
    """その時刻の (夏の膜の厚さ, 冬の膜の厚さ)"""
    s = sample()
    tau = tau_of(t)
    return h_at(s["h_s"], tau), h_at(s["h_w"], tau)


# ---------- 絵: 共通 ----------

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


def circ(ctx, x, y, r, col, a=1.0, line=None, lw=3.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.arc(x, y, r, 0, 2 * math.pi)
    if line:
        ctx.fill_preserve()
        _stroke(ctx, lw, line, 0.9)
    else:
        ctx.fill()


def ell(ctx, x, y, rx, ry, col, a=1.0, line=None, lw=3.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(col, a))
    if line:
        ctx.fill_preserve()
        _stroke(ctx, lw, line, 0.9)
    else:
        ctx.fill()


def cloud(ctx, x, y, s, col, a=1.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    for dx, dy, r in ((0, 0, 30), (34, -12, 38), (74, 0, 30), (36, 12, 34)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi)
        ctx.fill()


def draw_sun(ctx, x, y, t):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(12):
        a = t * 0.5 + k * math.pi / 6
        r0, r1 = 36, 50 + 4 * math.sin(t * 3 + k)
        ctx.move_to(x + r0 * math.cos(a), y + r0 * math.sin(a))
        ctx.line_to(x + r1 * math.cos(a), y + r1 * math.sin(a))
        _stroke(ctx, 5.0, "#f2a21d", 0.95)
    circ(ctx, x, y, 29, "#ffd95a", 1.0, "#e8901a")


# ---------- 絵: 公園 ----------

BARE = [  # 冬の木の枝 (x0,y0,x1,y1,太さ) 幹の根もとが (0,0)、上が −y
    (0, 0, 0, -95, 15), (0, -60, -34, -108, 9), (0, -80, 36, -128, 9), (0, -95, -14, -150, 8), (0, -95, 22, -160, 8),
    (-34, -108, -62, -128, 5), (-34, -108, -40, -146, 5), (36, -128, 64, -144, 5), (36, -128, 40, -166, 5),
    (-14, -150, -30, -178, 4), (22, -160, 16, -190, 4), (22, -160, 44, -184, 4)]


def draw_tree(ctx, x, gy, t, summer, s=1.0):
    sw = 3.0 * math.sin(t * 1.1 + x)
    if summer:
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, gy + 6)
        ctx.line_to(x + 2, gy - 112 * s)
        _stroke(ctx, 20 * s, "#7a5232", 1.0)
        for dx, dy, r, c in ((0, -150, 62, "#4f9a52"), (-46, -118, 44, "#5aa85a"), (48, -122, 46, "#5aa85a"), (6, -178, 40, "#6bb866")):
            circ(ctx, x + (dx + sw * (1 + dy / -150.0)) * s, gy + dy * s, r * s, c, 1.0, "#2d6a3a", 3.0)
    else:
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for (a, b, c_, d_, w) in BARE:
            k0 = max(0.0, -b / 190.0)
            k1 = max(0.0, -d_ / 190.0)
            ctx.move_to(x + (a + sw * k0 * 0.5) * s, gy + 6 + b * s)
            ctx.line_to(x + (c_ + sw * k1 * 0.5) * s, gy + 6 + d_ * s)
            _stroke(ctx, w * s, "#5b4636", 1.0)


def draw_park(ctx, t, k):
    pn = PN[k]
    p = sample()["p"]
    summer = k == "sum"
    x0, x1, cx = pn["x0"], pn["x1"], pn["cx"]
    g = cairo.LinearGradient(0, PY0, 0, GY)
    if summer:
        g.add_color_stop_rgb(0, *hexrgb("#8ccbf2")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#d9f0fb")[:3])
    else:
        g.add_color_stop_rgb(0, *hexrgb("#c3cfdb")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#e9eef2")[:3])
    ctx.set_source(g)
    ctx.rectangle(x0, PY0, x1 - x0, GY - PY0 + 4)
    ctx.fill()
    # 遠くの丘
    ell(ctx, cx - 90, GY + 10, 210, 62, "#9bd08a" if summer else "#dfe7ee")
    ell(ctx, cx + 150, GY + 14, 190, 48, "#86c277" if summer else "#d2dce5")
    if summer:
        draw_sun(ctx, x1 - 36, PY0 + 202, t)
        for ox, y, sc in ((0, PY0 + 175, 0.55), (150, PY0 + 215, 0.45)):
            cloud(ctx, x0 - 90 + (ox + t * 14) % (x1 - x0 + 200), y, sc, "#ffffff", 0.9)
    else:
        for ox, y, sc in ((0, PY0 + 178, 0.7), (190, PY0 + 215, 0.6)):
            cloud(ctx, x0 - 120 + (ox + t * 9) % (x1 - x0 + 240), y, sc, "#aab6c3", 0.95)
    draw_tree(ctx, x1 - 66, GY, t, summer)
    # 地面
    fill(ctx, hexrgb("#8fcf6a" if summer else "#f7fafd"))
    ctx.rectangle(x0, GY, x1 - x0, PY1 - GY)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#5da24a" if summer else "#c4d3e0", 0.9))
    ctx.set_line_width(3.5)
    ctx.move_to(x0, GY)
    ctx.line_to(x1, GY)
    ctx.stroke()
    if summer:
        for i in range(14):                                    # 草
            gx = x0 + 20 + i * 31 + (i * 7) % 11
            ctx.move_to(gx, GY + 30 + (i * 13) % 22)
            ctx.line_to(gx + 6, GY + 14 + (i * 13) % 22)
            _stroke(ctx, 3, "#4c8f3a", 0.85)
        ell(ctx, x0 + 56, GY + 2, 50, 26, "#4f9a52", 1.0, "#2d6a3a")             # 植え込み
    else:
        for i in range(5):                                     # 雪だまり
            ell(ctx, x0 + 30 + i * 100, GY + 38 + (i * 9) % 14, 60, 14, "#e6eef6", 0.9)
        for i in range(16):                                    # 降る雪
            sx = x0 + (i * 53 + 20 * math.sin(t * 0.8 + i)) % (x1 - x0)
            sy = PY0 + 150 + ((i * 97 + t * (34 + 3 * (i % 5))) % (GY - PY0 - 150))
            circ(ctx, sx, sy, 3.2 + (i % 3), "#ffffff", 0.9)
        ell(ctx, x0 + 56, GY + 6, 52, 22, "#eef3f8", 1.0, "#9fb2c4")             # 雪をかぶった植え込み


PERSON_S = 1.08


def draw_person(ctx, px, fy, t, k, ring_on):
    """人は公園の右側に立ち、左（中央）へ向けて吹く。絵は右向きで描いて左右を反転する。戻り値は輪の位置（反転後）"""
    ctx.save()
    ctx.translate(px, fy)
    ctx.scale(-PERSON_S, PERSON_S)
    ctx.translate(-px, -fy)
    ring = _person(ctx, px, fy, t, k, ring_on)
    ctx.restore()
    return (px - PERSON_S * (ring[0] - px), fy + PERSON_S * (ring[1] - fy))


def _person(ctx, px, fy, t, k, ring_on):
    summer = k == "sum"
    skin = "#f6d3b0"
    hip = fy - 105
    sh_y = hip - 100
    hc_y = sh_y - 40
    sway = 2.0 * math.sin(t * 1.6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for dx in (-15, 15):                                       # 脚
        ctx.move_to(px + dx, hip - 6)
        ctx.line_to(px + dx, fy - 14)
        _stroke(ctx, 21, skin if summer else "#35405a", 1.0)
        ell(ctx, px + dx + 7, fy - 7, 19, 9, "#f4f4f0" if summer else "#5a3b2a", 1.0, INK, 2.5)
    if summer:
        core.rrect(ctx, px - 31, hip - 14, 62, 44, 8)
        ctx.set_source_rgba(*hexrgb("#3f78c4", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.8)
    # 腕（あとろ側）
    ctx.move_to(px - 24, sh_y + 12)
    ctx.line_to(px - 36, hip - 20)
    _stroke(ctx, 17, skin if summer else "#2f6b4f", 1.0)
    # 胴
    core.rrect(ctx, px - 40, sh_y, 80, 112, 24)
    ctx.set_source_rgba(*hexrgb("#ffc24a" if summer else "#2f6b4f", 1))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    if not summer:
        ctx.move_to(px + 6, sh_y + 8)
        ctx.line_to(px + 6, sh_y + 108)
        _stroke(ctx, 2.5, INK, 0.5)
        for yy in (36, 66, 96):
            circ(ctx, px + 14, sh_y + yy, 3.4, "#e8d9a8", 1.0, INK, 1.5)
    # 頭
    circ(ctx, px, hc_y, 40, skin, 1.0, INK, 3.4)
    if summer:                                                 # 半そで・髪
        ctx.arc(px, hc_y - 4, 41, math.pi * 1.0, math.pi * 2.0)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#4a3626", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
    else:                                                      # ニット帽
        ctx.arc(px, hc_y - 4, 42, math.pi * 1.02, math.pi * 1.98)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#d8434e", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        core.rrect(ctx, px - 44, hc_y - 16, 88, 18, 8)
        ctx.set_source_rgba(*hexrgb("#f1f1f1", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        circ(ctx, px, hc_y - 44, 9, "#ffffff", 1.0, INK, 2.5)
    # 顔（右向き）
    circ(ctx, px + 12, hc_y + 2, 3.8, INK, 1.0)
    circ(ctx, px + 28, hc_y + 2, 3.8, INK, 1.0)
    circ(ctx, px + 6, hc_y + 14, 6, "#f4a9a0", 0.6)
    mouth_r = 4.8 + (1.2 * math.sin(t * 7.0) if ring_on else 0)
    ell(ctx, px + 32, hc_y + 16, mouth_r * 0.8, mouth_r, "#b5483f", 1.0, INK, 2)
    if not summer:                                             # マフラー
        core.rrect(ctx, px - 32, sh_y - 14, 64, 20, 9)
        ctx.set_source_rgba(*hexrgb("#e8584f", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        ctx.move_to(px - 22, sh_y + 4)
        ctx.line_to(px - 28 + sway, sh_y + 52)
        ctx.line_to(px - 10 + sway, sh_y + 54)
        ctx.line_to(px - 8, sh_y + 4)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#e8584f", 1))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        for i in range(3):                                     # 白い息
            ph = (t * 0.9 + i * 0.34) % 1.0
            circ(ctx, px + 48 + ph * 36, hc_y + 12 - ph * 22, 5 + 7 * ph, "#ffffff", 0.8 * (1 - ph))
    # 腕（吹く側）と輪
    hand = (px + 66, hc_y + 30)
    ctx.move_to(px + 26, sh_y + 14)
    ctx.line_to(*hand)
    _stroke(ctx, 17, skin if summer else "#2f6b4f", 1.0)
    circ(ctx, hand[0], hand[1], 9, skin, 1.0, INK, 2.5)
    ring = (px + 84, hc_y + 4)
    ctx.move_to(*hand)
    ctx.line_to(ring[0] - 4, ring[1] + 14)
    _stroke(ctx, 4.5, "#8f8f94", 1.0)
    circ(ctx, ring[0], ring[1], 15, "#ffffff", 0.25, "#8f8f94", 3.5)
    return ring


# ---------- シャボン玉 ----------

def film_color(h):
    """膜の厚さ h [nm] の干渉色。反射は sin²(2π n h / λ)（n=1.33、表と裏の反射の干渉）。薄いほど暗く、厚いと白っぽい"""
    base = [0.08 + 0.92 * math.sin(2 * math.pi * 1.33 * h / lam) ** 2 for lam in (630.0, 540.0, 460.0)]
    m = clamp01((h - 500.0) / 700.0)
    rgb = tuple(base[j] * (1 - m) + (0.80, 0.92, 1.0)[j] * m for j in range(3))
    return rgb, 0.64 - 0.32 * m


def draw_bubble(ctx, cx, cy, r, h_top, alpha=1.0):
    g = cairo.LinearGradient(0, cy - r, 0, cy + r)
    n = 28
    for i in range(n + 1):
        u = i / n
        hu = h_top * (1.0 + 1.3 * u ** 1.6)                    # 下ほど厚い（排液でたまる）
        rgb, a = film_color(hu)
        g.add_color_stop_rgba(u, rgb[0], rgb[1], rgb[2], a * alpha)
    ctx.set_source(g)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill_preserve()
    _stroke(ctx, 2.8, "#5d8fc4", 0.8 * alpha)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.arc(cx, cy, r * 0.8, math.pi * 1.08, math.pi * 1.42)
    _stroke(ctx, max(3.0, r * 0.07), "#ffffff", 0.85 * alpha)
    ctx.arc(cx, cy, r * 0.8, math.pi * 1.5, math.pi * 1.58)
    _stroke(ctx, max(3.0, r * 0.07), "#ffffff", 0.6 * alpha)


def draw_burst(ctx, cx, cy, r, u, col):
    """割れた瞬間（u: 0→1）"""
    a = 1 - u
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(14):
        ang = i * 2 * math.pi / 14 + 0.2
        r0, r1 = r * (0.9 + 0.5 * u), r * (1.15 + 1.0 * u)
        ctx.move_to(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang))
        ctx.line_to(cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))
        _stroke(ctx, 4.5, "#5d8fc4", 0.8 * a)
    for i in range(9):
        ang = i * 2 * math.pi / 9 + 0.6
        rr = r * (0.7 + 1.1 * u)
        circ(ctx, cx + rr * math.cos(ang), cy + rr * math.sin(ang) + 18 * u * u * r / 50, 4.5 * (1 - 0.5 * u), "#a9cdee", 0.9 * a)
    text(ctx, "ぱん！", cx, cy - r * 1.05 - 18 * u, 38, col, alpha=a)


def r_px(R):
    return 34.0 + 15.0 * R                                      # 玉の半径 1〜3cm → 49〜79 px


def draw_side(ctx, t, k):
    """1つの公園: 背景・人・シャボン玉"""
    s = sample()
    p = s["p"]
    suf = "s" if k == "sum" else "w"
    pn = PN[k]
    cx = pn["cx"]
    tau = tau_of(t)
    t_pop = s["t_" + suf]
    popped = tau >= t_pop
    ctx.save()
    clip_panel(ctx, k)
    draw_park(ctx, t, k)
    ring = draw_person(ctx, cx + 112, FY, t, k, t < 3.0)
    rp = r_px(p["R_" + suf])
    v = p["v_" + suf]
    hover = (cx - 70, 1086.0)
    ph = 1.0 if k == "sum" else 2.3
    if t < 2.8:                                                 # 吹き始めの小さな玉（絵だけ。冒頭1秒の動きのため。計算の玉は下の1つ）
        h0 = h_at(s["h_" + suf], 0.0)
        for j in range(18):
            age = t - j * 0.08
            if 0 <= age < 1.9:
                fade = (1 - age / 1.9) * (1 - clamp01((t - 2.2) / 0.6))
                bx = ring[0] - 30 - age * (130 + 30 * (j % 5))
                by = ring[1] - 20 - age * (90 + 45 * (j % 4)) + 16 * math.sin(age * 6 + j + ph)
                rr = (22 + (j * 7) % 22) * min(1.0, age / 0.12)
                circ(ctx, bx, by, rr, "#ffffff", 0.35 * fade)
                draw_bubble(ctx, bx, by, rr, h0, alpha=fade)
    if not popped:
        grow = ease(t / 0.9)
        u = ease((t - 0.8) / 1.8)
        gx, gy = ring[0] - rp * grow * 0.55, ring[1] - rp * grow * 0.35
        sx = (9 + 13 * v) * math.sin(t * 1.25 + ph) * u
        sy = 7 * math.sin(t * 1.7 + ph) * u
        bx = gx + (hover[0] + sx - gx) * u
        by = gy + (hover[1] + sy - gy) * u
        h_now = h_at(s["h_" + suf], tau)
        draw_bubble(ctx, bx, by, rp * grow * (1 + 0.012 * math.sin(t * 5 + ph)), h_now)
    else:
        tp = t_of(t_pop)
        u = clamp01((t - tp) / 0.45)
        if u < 1:
            sx = (9 + 13 * v) * math.sin(tp * 1.25 + ph)
            sy = 7 * math.sin(tp * 1.7 + ph)
            draw_burst(ctx, hover[0] + sx, hover[1] + sy, rp, u, RED)
    ctx.restore()
    border_panel(ctx, k)


# ---------- ストップウォッチ・見出し ----------

def draw_dial(ctx, cx, cy, r, tau, done, col):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    core.rrect(ctx, cx - 7, cy - r - 17, 14, 14, 3)
    fill(ctx, hexrgb("#9aa3b0"))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.9)
    circ(ctx, cx, cy, r, "#ffffff", 1.0, INK, 4.0)
    for i in range(12):
        a = i * math.pi / 6
        ctx.move_to(cx + (r - 8) * math.sin(a), cy - (r - 8) * math.cos(a))
        ctx.line_to(cx + (r - 3) * math.sin(a), cy - (r - 3) * math.cos(a))
        _stroke(ctx, 2.5, INK, 0.8)
    a = (tau / 60.0) * 2 * math.pi
    ctx.move_to(cx, cy)
    ctx.line_to(cx + (r - 12) * math.sin(a), cy - (r - 12) * math.cos(a))
    _stroke(ctx, 4.5, RED if done else col, 1.0)
    circ(ctx, cx, cy, 4.5, INK, 1.0)


def draw_card(ctx, t, k):
    s = sample()
    suf = "s" if k == "sum" else "w"
    pn = PN[k]
    cx = pn["cx"]
    core.rrect(ctx, pn["x0"] + 10, CARD_Y, pn["x1"] - pn["x0"] - 20, PY1 - CARD_Y - 10, 18)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.96))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    tau = tau_of(t)
    t_pop = s["t_" + suf]
    done = tau >= t_pop
    show_tau = t_pop if done else tau
    draw_dial(ctx, cx - 112, CARD_Y + 92, 50, show_tau, done, INKC[k])
    if not done:
        text(ctx, "経過", cx + 52, CARD_Y + 54, 26, PENCIL, bold=False)
        text(ctx, sec_s(show_tau), cx + 52, CARD_Y + 106, 50, INKC[k])
    else:
        tp = t_of(t_pop)
        u = clamp01((t - tp) / 0.35)
        text(ctx, "割れた！", cx + 52, CARD_Y + 52, 34, RED)
        lab = sec_s(t_pop)
        text(ctx, lab, cx + 52, CARD_Y + 106, 46, INKC[k])
        note.pen_circle(ctx, cx + 52, CARD_Y + 106, core.text_width(lab, 46) / 2 + 26, 33, RED, seed=70 + (k == "win"), width=4.5, progress=u)


def draw_header(ctx, t, k):
    p = sample()["p"]
    suf = "s" if k == "sum" else "w"
    pn = PN[k]
    cx = pn["cx"]
    xd, yd = cx - 62, PY0 + 38
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 24, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 24, 24, INKC[k], seed=13 + (k == "win"), width=3.4)
    text(ctx, TAG[k], xd, yd, 32, INKC[k])
    text(ctx, NAME[k] + "の公園", cx - 24, yd, 40, INKC[k], align="left")
    text(ctx, f"気温{p['T_' + suf]:.0f}℃", cx, PY0 + 89, 46, RED if k == "sum" else INK_W)
    text(ctx, f"湿度{p['RH_' + suf] * 100:.0f}%・風{p['v_' + suf]:.1f}m/秒", cx, PY0 + 133, 28, INK, bold=False)


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    ctx.push_group()
    z = 1.0 + 0.07 * (1 - ease(clamp01(t / 1.1)))           # 冒頭1秒: 2つの公園が少し寄った所から引いていく（動きのため）
    if z > 1.0:
        ctx.translate(550, 1440)
        ctx.scale(z, z)
        ctx.translate(-550, -1440)
    draw_side(ctx, t, "sum")
    draw_side(ctx, t, "win")
    draw_card(ctx, t, "sum")
    draw_card(ctx, t, "win")
    draw_header(ctx, t, "sum")
    draw_header(ctx, t, "win")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, "早送り", 580, 650, 40, "yellow", a=a, tilt=-0.02)
    text(ctx, "たとえば、この1回では", 580, 732, 28, PENCIL, bold=False, alpha=a)
    text(ctx, "膜が薄くなると割れる", 580, 774, 26, PENCIL, bold=False, alpha=a)


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
    win = (r["t_w"] > r["t_s"]).astype(int)          # 1 = 冬が長持ち
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_S), bgra(COL_W)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win[:m]]
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


def ratio_txt(r):
    """時間の比（冬÷夏）→ '冬が夏の約2.6倍' / '夏が冬の約1.3倍' / 'ほぼ同じ'"""
    if abs(r - 1) < 0.05:
        return "ほぼ同じ"
    return f"冬が夏の約{r:.1f}倍" if r >= 1 else f"夏が冬の約{1 / r:.1f}倍"


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
    text(ctx, "実験ではなく、計算での見立てです", 580, 1166, 24, PENCIL, bold=False, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    win = r["t_w"][:m] > r["t_s"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("win", int(win.sum())), ("sum", int(m - win.sum())))):
            y = 1208 + i * 50
            fill(ctx, hexrgb(COLS[k], a * lg))
            ctx.rectangle(190, y - 16, 32, 32)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(190, y - 16, 32, 32)
            ctx.stroke()
            text(ctx, f"{TAG[k]} {NAME[k]}のほうが長持ち", 240, y, 33, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 925, y, 33, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            sh = shown()
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            note.sticky(ctx, f"この置き方なら 冬が長持ちは 約{pct_i(sh['p_win'])}\n中央値で{ratio_txt(sh['r_med'])}", 580, 1352, 32,
                        "pink", fg=RED, a=b, tilt=-0.015)
            text(ctx, "中央値＝小さい順に並べた真ん中の値", 580, 1436, 28, PENCIL, bold=False, alpha=b)


# ---------- 答え ----------

def reason_text():
    sh = shown()
    k = answer_key()
    if k == "win":
        return (f"この置き方なら 蒸発の勢いは\n中央値で夏が冬の約{sh['e_ratio']:.1f}倍。\n"
                f"冬は水が逃げにくく、液も流れ落ちにくい")
    if k == "sum":
        return "夏は湿度が高く、冬は乾いて水が逃げやすいから"
    return "夏は暑く湿気も多く、冬は寒く乾いている。\n打ち消し合って 時間は ほぼ同じ"


def twist_q():
    return "では、夏でも雨上がり\n（湿度90%）なら？"


def twist_a():
    sh = shown()
    return f"この置き方なら 冬が長持ちは 約{pct_i(sh['p90'])}\n中央値で{ratio_txt(sh['r90'])}"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    go = 1 - ease((t - T_TW1) / 0.3)                           # ひねりの前に、答えと理由は消す
    b = ease_out((t - T_REV - 0.15) / 0.3) * go
    note.sticky(ctx, f"残念、{TAG[key]}が正解。" if key != "same" else "残念、ほぼ同じが正解。", 580, 1252, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if key != "same" and go > 0:
        text(ctx, f"（{KEY_LABEL[key]}のほうが長く割れない）", 580, 1304, 28, INK, bold=False, alpha=b)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3) * go
        note.sticky(ctx, reason_text(), 580, 1384, 28, "blue", a=c, tilt=0.012)
    if t >= T_TW1:
        d = ease_out((t - T_TW1) / 0.3)
        note.sticky(ctx, twist_q(), 580, 1258, 34, "mint", a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        note.sticky(ctx, twist_a(), 580, 1388, 30, "pink", fg=RED, a=e, tilt=0.012)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に夏と冬の公園（0秒目から玉を吹く）"""
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
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "冬の公園で、\nためしてみますか？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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
    mx.add(0.0, whoosh(0.7), 0.3)                          # ふーっと吹く
    mx.add(0.05, whoosh(0.7), 0.2)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    for key, f0 in (("t_s", 784.0), ("t_w", 659.3)):
        tg = t_of(s[key])
        mx.add(tg, tick(700, 0.05), 0.6)                   # ぱん
        mx.add(tg, bell(f0, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                    # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW1, blip(659.3, 0.14), 0.3)
    mx.add(T_TW2, blip(784.0, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    checks = []
    k = 500
    d1 = {kk: v[:k] for kk, v in p.items()}
    # (1) 蒸発だけ: 数値の足し算が、一定の速さで薄くなる式 (h0−hc)/E と合う（最大の食い違い・割合）
    for side in ("s", "w"):
        E, _ = coef(d1, side)
        ana = (d1["h0_" + side] - d1["hc_" + side]) / E
        num = run(d1, side, drain=False)
        checks.append((f"蒸発だけの割れる時刻: 足し算 − 式（最大・割合・{side}）", float(np.max(np.abs(num / ana - 1))), 0.0, 1e-3))
        # (2) 排液だけ: 1/h が時間に比例して増える式 (1/hc − 1/h0)/D と合う
        _, Dc = coef(d1, side)
        ana2 = (1 / d1["hc_" + side] - 1 / d1["h0_" + side]) / Dc
        num2 = run(d1, side, evap=False)
        ok = ana2 < TMAX - 10                        # 排液だけだと1時間で割れない回もある（その回は比べない）
        checks.append((f"排液だけの割れる時刻: 足し算 − 式（最大・割合・{side}）", float(np.max(np.abs(num2[ok] / ana2[ok] - 1))), 0.0, 1e-3))
    # (3) 飽和水蒸気圧と水の粘度の値
    checks.append(("飽和水蒸気圧 25℃（hPa・水の表の値 31.7）", float(es_hpa(25.0)), 31.7, 0.3))
    checks.append(("飽和水蒸気圧 0℃（hPa・6.11）", float(es_hpa(0.0)), 6.11, 0.05))
    checks.append(("水の粘度 0℃（mPa·s）", float(mu_w(0.0)), 1.792, 1e-9))
    checks.append(("水の粘度 25℃（mPa·s）", float(mu_w(25.0)), 0.890, 1e-9))
    # (4) 蒸発の式が、湿度の実測（Pasquet ほか: 63% → 22秒、39% → 12秒）と向き・大きさが近い
    checks.append(("湿度63%と39%の寿命の比（蒸発のみ）が 実測 22÷12 に近い", pasquet_ratio(), 22.0 / 12.0, 0.25))
    # (5) 夏の湿度を上げる（90%）と 夏の寿命は長くなる
    checks.append(("夏の湿度を90%にすると 夏の寿命の中央値は長くなる", float(sh["med_s90"] > sh["med_s"]), 1.0, 0.0))
    # (6) 見本の履歴の終わり（割れる時刻）が、1万回の中のその回と一致する
    s = sample()
    checks.append(("見本の夏の時刻（秒）が1万回の値と同じ", s["chk"][0], s["t_s"], 1e-6))
    checks.append(("見本の冬の時刻（秒）が1万回の値と同じ", s["chk"][1], s["t_w"], 1e-6))
    checks.append(("見本の時間の比が中央値の近く", s["ratio"], sh["r_med"], 0.08 * sh["r_med"]))
    # (7) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ。正解の記号は A
    key = answer_by_rule(sh["p_win"], sh["r_med"])
    checks.append(("画面の正解の位置が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号は A", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（夏・冬）",
                   float(LABELS.index("夏") * 10 + LABELS.index("冬")),
                   float("ABC".index(TAG["sum"]) * 10 + "ABC".index(TAG["win"])), 0.0))
    # (8) 画面の回数が足して1万・全部割れている
    checks.append(("長持ちの回数の合計", float(sh["n_win"] + sh["n_sum"]), float(N_TRIAL), 0.0))
    checks.append(("割れなかった回（1時間）", float(sh["n_unfinished"]), 0.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}倍  割れる {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"ひねり {T_TW1:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}  見本 {s['i']}（夏 {sec_s(s['t_s'])} / 冬 {sec_s(s['t_w'])}）")
    print("  理由:", reason_text().replace("\n", " / "), "|", twist_q().replace("\n", ""), twist_a().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.2, 5.8, 8.0, 10.0, T_FIN1 - 0.3, T_FIN1 + 0.2, T_FIN1 + 0.8, T_FIN2 - 0.6, T_FIN2 + 0.3,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW1 + 0.6, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
