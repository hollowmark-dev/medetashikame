"""やかんの湯気、白く見えるのは 口のすぐそば？ 少し離れたところ？ 1万回ためす。— 2026-10-23 作成（公開予定 10/31・45秒前後）

くらべるのは「注ぎ口から、白く見えはじめるまでの距離（cm）」だけ。人は湯気に近づけない（やけどの危険）ので、人は描かない。

モデル（注ぎ口から出る水蒸気の噴流（ジェット）。中心の軸の上だけを見る）
  噴き出し: 注ぎ口から出るのは、ほぼ100℃の水蒸気だけ（沸騰中のやかんの中の気体。水の粒は無い＝見えない）。
        口の内径 d = 0.8〜1.5 cm（仮定。家庭用やかんの注ぎ口の口を 1cm 前後と見た）。
        火の強さ（水に入る熱）0.5〜1.5 kW（仮定）、そのうち注ぎ口から出る割合 0.6〜1.0（残りはふたのすき間・仮定）
        → 水蒸気の量 = 熱 ÷ 蒸発の熱（2.26 MJ/kg）、出る速さ = 量 ÷（水蒸気の密度 × 口の面積）。
        （速さは絵の動きの速さにだけ使う。噴流の混ざり方の「かたち」は速さによらないので、距離は変えない。そのことも結果で確かめる）
  巻き込み・うすまり（教科書の円形噴流）: 軸の上の、噴き出した気体の割合 φ（質量の割合）は
        φ(x) = 1（x < x_c）、φ(x) = x_c / x（x ≥ x_c）、  x_c = K × d_eff、  d_eff = d × √(ρ_噴き出し ÷ ρ_まわり)。
        K は 4.5〜6.5（仮定。円形噴流の中心の速さ・濃さの減り方の定数は 5〜6 前後と言われる。例: 速さの定数 5.5〜6.1 という報告
        （arXiv:2602.09759 の紹介。検索の要約で確認しただけで、表の原文は未確認）。濃さ（水蒸気の割合）の定数の原典は確認できていない）。
        軽い水蒸気（100℃で 0.59 kg/m³）は、まわりの空気（約1.2 kg/m³）より軽いので、有効な口の大きさは √(密度比) 倍で小さくなる（教科書の補正）。
  混ざった気体の状態（その場所の温度・水蒸気の量）: 噴き出した水蒸気 φ とまわりの空気（気温 Ta・湿度 RH）が混ざったとき、
        熱（エンタルピー）と水の量の保存から、つり合いの温度 T を求める（水蒸気が飽和量を超えたぶんは水の粒になる。
        水の粒になるときに出る熱も入れる）。飽和水蒸気圧は 水の Antoine の式（Wikipedia「Antoine equation」の水の定数:
        log10 P[mmHg] = 8.07131 − 1730.63 / (233.426 + T[℃])、1〜100℃。20℃で 2.333 kPa（実測値 2.339）、100℃で 1気圧）。
  白く見えはじめる距離: 水の粒の量（空気 1m³ あたりのグラム数）が LWC_min を超える最初の距離。
        LWC_min = 0.5〜5 g/m³（仮定。粒の大きさ 1〜3μm・見える筋の太さ 数cm でうすい霧がはっきり白く見える程度）。
        白く見えなくなる距離（まわりの乾いた空気で粒がまた蒸発して見えない）は LWC が LWC_min をふたたび下回る距離。
  条件のでたらめ: 部屋の気温 5〜20℃、湿度 30〜70%（冬の台所）、口の内径・K・火の強さ・口から出る割合・LWC_min は上の幅。
  測るもの: 白く見えはじめる距離（cm）。1万回。
  入れていないこと: 口のふちの混ざりの層（ふちでは中心より先に薄く白くなる）、粒ができるまでの時間、注ぎ口の中で先に冷えること、
        浮力（軽い水蒸気は上へそる）、部屋の気流、粒が育つ時間。

答えの決め方（計算の前に決めた規則。answer_by_rule）:
      「口のすぐそば」＝白くなり始める距離が 1cm 未満、「少し離れたところ」＝ 1cm 以上。
      1万回のうち 1cm 以上だった割合 p、距離の真ん中の値 d。
      p ≥ 60% かつ d ≥ 1.5cm なら「少し離れたところ」、p ≤ 40% かつ d ≤ 0.7cm なら「口のすぐそば」、それ以外は「ほぼ同じ」。
      結果がどれでも、そのまま出す。
ひねり: 1行。「では、暖かい部屋（25℃）なら？」 同じ1万回（湿度などは同じ値）で、気温だけ 25℃ に。
締め: 「あなたの家のやかん、白い湯気は口から何cm？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "yakan-yuge"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261031
P_ATM = 1.01325                                    # bar
T_JET = 100.0                                      # 噴き出す水蒸気（℃）
LV = 2.26e6                                        # 蒸発の熱 J/kg
R_AIR, R_VAP = 287.05, 461.5                       # J/(kg K)
TA, RH = (5.0, 20.0), (0.30, 0.70)
D_MM = (8.0, 15.0)                                 # 口の内径（mm）
K_RANGE = (4.5, 6.5)
PBOIL = (500.0, 1500.0)                            # 水に入る熱（W）
F_SPOUT = (0.6, 1.0)
LWC_MIN = (0.5, 5.0)                               # g/m³
T_TWIST = 25.0
PHI = np.concatenate([1.0 - np.logspace(-3, np.log10(0.5), 160), np.logspace(np.log10(0.5), -3, 220)[1:]])   # 1 → 0.001
X_NEAR = 1.0                                       # cm。これ未満が「口のすぐそば」

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_D_HI, RULE_D_LO = 0.60, 0.40, 1.5, 0.7


def answer_by_rule(p_far, d_med_cm):
    """p_far = 1cm 以上だった回の割合、d_med_cm = 距離の真ん中の値（cm）。'far' / 'same' / 'near'"""
    if p_far >= RULE_HI and d_med_cm >= RULE_D_HI:
        return "far"
    if p_far <= RULE_LO and d_med_cm <= RULE_D_LO:
        return "near"
    return "same"


def psat(T):
    """水の飽和水蒸気圧（bar）。T は℃（1〜100）。Antoine の式 log10 P[mmHg] = 8.07131 − 1730.63 / (233.426 + T)
    （1〜100℃で広く載っている定数）。沸点 100℃ で 1気圧をわずかに超えるので、1気圧の 99.99% で頭打ちにする"""
    p = 10.0 ** (8.07131 - 1730.63 / (233.426 + T)) / 760.0 * 1.01325
    return np.minimum(p, 0.9999 * P_ATM)


def wsat(T):
    p = psat(T)
    return 0.622 * p / (P_ATM - p)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    d = dict(Ta=u(TA), RH=u(RH), d=u(D_MM) / 10.0, K=u(K_RANGE), Pb=u(PBOIL), fs=u(F_SPOUT), Lmin=u(LWC_MIN))
    return d


def ambient(Ta, RH):
    pv = RH * psat(Ta)
    wa = 0.622 * pv / (P_ATM - pv)
    TK = Ta + 273.15
    rho = (P_ATM - pv) * 1e5 / (R_AIR * TK) + pv * 1e5 / (R_VAP * TK)
    return wa, rho


def jet_speed(d):
    """出る速さ（m/s）"""
    mdot = d["Pb"] * d["fs"] / LV
    rho_j = P_ATM * 1e5 / (R_VAP * (T_JET + 273.15))
    A = math.pi * (d["d"] / 100.0 / 2.0) ** 2
    return mdot / (rho_j * A)


def lwc_profile(Ta, wa, phi):
    """気温 Ta・湿度比 wa のまわりの空気に、噴き出した気体の割合 phi（質量）で混ざった状態の、水の粒の量（g/m³）と温度。
    Ta, wa は (n,)、phi は (G,) → (n, G)"""
    Ta, wa = Ta[:, None], wa[:, None]
    r = phi[None, :] * (1.0 + wa) / (1.0 - phi[None, :])          # 噴き出した水蒸気 / 乾いた空気（kg/kg）
    wt = wa + r
    H = 1.006 * Ta + wa * (2501.0 + 1.86 * Ta) + r * (2501.0 + 1.86 * T_JET)
    lo = np.broadcast_to(Ta, wt.shape).copy()
    hi = np.full(wt.shape, T_JET)
    for _ in range(45):
        T = 0.5 * (lo + hi)
        wv = np.minimum(wt, wsat(T))
        g = 1.006 * T + wv * (2501.0 + 1.86 * T) + (wt - wv) * 4.186 * T - H
        up = g > 0
        hi = np.where(up, T, hi)
        lo = np.where(up, lo, T)
    T = 0.5 * (lo + hi)
    wv = np.minimum(wt, wsat(T))
    wl = np.maximum(wt - wv, 0.0)
    pv = wv / (0.622 + wv) * P_ATM
    rho_dry = (P_ATM - pv) * 1e5 / (R_AIR * (T + 273.15))
    return wl * rho_dry * 1000.0, T


def visible_range(d, Ta=None):
    """白く見えはじめる距離・見えなくなる距離（cm）。見えなくなる距離は、グリッドの端（φ=0.001）まで見えていたら inf"""
    Ta = d["Ta"] if Ta is None else np.full(len(d["Ta"]), Ta)
    wa, rho_a = ambient(Ta, d["RH"])
    rho_j = P_ATM * 1e5 / (R_VAP * (T_JET + 273.15))
    deff = d["d"] * np.sqrt(rho_j / rho_a)
    xc = d["K"] * deff                                             # cm
    lwc, _ = lwc_profile(Ta, wa, PHI)
    vis = lwc >= d["Lmin"][:, None]
    anyv = vis.any(1)
    i_s = np.argmax(vis, 1)
    i_e = vis.shape[1] - 1 - np.argmax(vis[:, ::-1], 1)
    xs = np.where(anyv, xc / PHI[i_s], np.inf)
    xe = np.where(anyv, np.where(i_e >= len(PHI) - 1, np.inf, xc / PHI[i_e]), np.nan)
    return xs, xe, xc
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
        xs, xe, xc = visible_range(d)
        xs25, xe25, _ = visible_range(d, T_TWIST)
        r = dict(xs=xs, xe=xe, xc=xc, xs25=xs25, xe25=xe25)
        np.savez(fn, **r)
    r["p"] = d
    r["v"] = jet_speed(d)
    _RES["m"] = r
    return r


def shown():
    r = results()
    xs, xe = r["xs"], r["xe"]
    far = xs >= X_NEAR
    q = np.percentile(xs, [10, 25, 75, 90])
    big = lambda a: np.where(np.isfinite(a), a, 1e9)    # noqa: E731
    return dict(p_far=float(far.mean()), n_far=int(far.sum()), n_near=int((~far).sum()), xs_med=float(np.median(xs)), xs_q=q,
                xs_min=float(xs.min()), xs_max=float(xs.max()),
                xe_med=float(np.median(big(xe))), xe_fin=float(np.isfinite(xe).mean()),
                xe_q=np.percentile(big(xe), [10, 90]),
                xs25_med=float(np.median(r["xs25"])), xe25_med=float(np.median(big(r["xe25"]))),
                n_novis=int((~np.isfinite(xs)).sum()),
                v_med=float(np.median(r["v"])), v_q=np.percentile(r["v"], [10, 90]),
                corr_v=float(np.corrcoef(r["v"], xs)[0, 1]), corr_d=float(np.corrcoef(r["p"]["d"], xs)[0, 1]),
                corr_K=float(np.corrcoef(r["p"]["K"], xs)[0, 1]), corr_Ta=float(np.corrcoef(r["p"]["Ta"], xs)[0, 1]),
                corr_Ta_e=float(np.corrcoef(r["p"]["Ta"], np.minimum(big(xe), 1e3))[0, 1]))


def report():
    sh = shown()
    print(f"1cm以上 {sh['p_far']:.4f}（{sh['n_far']}回 / 未満 {sh['n_near']}回）  距離の真ん中 {sh['xs_med']:.2f}cm  10/25/75/90% {np.round(sh['xs_q'], 2)}  "
          f"最小 {sh['xs_min']:.2f} 最大 {sh['xs_max']:.2f}  見えない回 {sh['n_novis']}")
    print(f"  答え {answer_by_rule(sh['p_far'], sh['xs_med'])}")
    print(f"  見えなくなる距離 真ん中 {sh['xe_med']:.1f}cm（10/90% {np.round(sh['xe_q'], 1)}）  有限の割合 {sh['xe_fin']:.3f}")
    print(f"  25℃の部屋: 見えはじめ {sh['xs25_med']:.2f}cm  見えなくなる {sh['xe25_med']:.1f}cm")
    print(f"  出る速さ 真ん中 {sh['v_med']:.1f}m/s（10/90% {np.round(sh['v_q'], 1)}）  相関 速さ {sh['corr_v']:+.2f} 口 {sh['corr_d']:+.2f} K {sh['corr_K']:+.2f} 気温 {sh['corr_Ta']:+.2f}（見えなくなる距離と気温 {sh['corr_Ta_e']:+.2f}）")


if __name__ == "__main__" and "--model" in sys.argv:
    import time
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    report()
    print(f"  計算 {time.time() - t0:.0f}秒")
    sys.exit(0)


# =====================================================================
# 見本（1回ぶん）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。条件: 距離が真ん中の値の近く（±4%）で、冬の台所らしい気温・湿度、
    口の内径が 1.0〜1.35cm。その中で距離が真ん中にいちばん近い回。"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    xs = r["xs"]
    med = float(np.median(xs))
    ok = ((np.abs(xs / med - 1) < 0.04) & (p["Ta"] > 8) & (p["Ta"] < 14) & (p["RH"] > 0.40) & (p["RH"] < 0.65)
          & (p["d"] > 1.0) & (p["d"] < 1.35))
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    sc = np.abs(xs[cand] / med - 1) + 0.01 * np.abs(p["Ta"][cand] - 11.0)
    i = int(cand[np.argmin(sc)])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    q = {k: float(v[i]) for k, v in p.items()}
    xs1, xe1, xc1 = visible_range(d1)
    wa, rho_a = ambient(d1["Ta"], d1["RH"])
    lwc, Tm = lwc_profile(d1["Ta"], wa, PHI)
    xarr = float(xc1[0]) / PHI
    _SAMPLE = dict(i=i, p=q, xs=float(xs[i]), chk=float(xs1[0]), xc=float(xc1[0]), xarr=xarr, lwc=lwc[0], Tm=Tm[0],
                   v=float(jet_speed(d1)[0]), med=med)
    return _SAMPLE


def lwc_at(s_cm):
    sm = sample()
    return np.interp(s_cm, sm["xarr"], sm["lwc"], left=0.0)


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    q = s["p"]
    print("見本", s["i"], "気温", round(q["Ta"], 1), "湿度", round(q["RH"] * 100), "% 口", round(q["d"], 2), "cm K", round(q["K"], 2), "火", round(q["Pb"]),
          "W 割合", round(q["fs"], 2), "LWC_min", round(q["Lmin"], 2), "| 芯の長さ", round(s["xc"], 2), "cm 白くなる", round(s["xs"], 2), "cm 速さ", round(s["v"], 1), "m/s")
    for x in (s["xs"], s["xs"] + 0.3, s["xs"] + 1, s["xs"] + 3, s["xs"] + 8):
        print("  x", round(x, 2), "LWC", round(float(lwc_at(x)), 2), "g/m3")
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
note.DATE = "10.31"                                # 日付欄（公開予定日）

COL_NEAR = "#f2a65a"                               # 1cm未満（口のすぐそば）
COL_F = ["#bfe3c4", "#7cc796", "#3f9d68"]          # 1〜3 / 3〜5 / 5cm以上（少し離れたところ）
KEY_LABEL = {"near": "口のすぐそば", "same": "ほぼ同じ", "far": "少し離れたところ"}

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["口のすぐそば", "ほぼ同じ", "少し離れたところ"]
TAG = {"near": "A", "far": "C"}
CORRECT = 2                                        # answer_by_rule の結果の位置

BIG_Q = ["やかんの湯気、白く見えるのは", "口のすぐそば？少し離れたところ？"]                      # 定位置（上）の2行
BIG_Q4 = ["やかんの湯気、", "白く見えるのは", "口のすぐそば？", "少し離れたところ？"]             # 1コマ目の4行（同じ大きさ）
DETAIL = "冬の台所・火にかけたやかん"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
T_RULER, T_SW0, T_SW1 = 5.8, 6.8, 8.6              # 定規 → すき間をはかる
T_RES = 8.9                                        # 「口から ○cm」
T_LAB1, T_LAB2 = 10.0, 11.3                        # 見えない水蒸気 → 白い水の粒
T_MANY = 12.4                                     # 「条件を変えて1万回」
T_G0 = 15.0
T_G1 = T_G0 + 2.9
T_REV = T_G1 + 2.6
T_ANS2 = T_REV + 1.7
T_ANS3 = T_ANS2 + 2.4
T_TW = T_ANS3 + 4.4                                # ひねり
T_TWB = T_TW + 2.6
T_Q = T_TWB + 5.0
DURATION = T_Q + 6.6

# ---------- 画面の置き場所 ----------
PX0, PX1, PY0, PY1 = 60.0, 1020.0, 905.0, 1600.0   # 絵のパネル（画面の下まで）
TIPX, TIPY = 510.0, 1250.0                         # 注ぎ口の先
ANG = math.radians(32.0)                           # 注ぎ口の向き（水平から上へ）
EXV = (math.cos(ANG), -math.sin(ANG))              # 軸の向き（画面の座標）
NXV = (math.sin(ANG), math.cos(ANG))               # 軸に直角（右下向き）
SC = 38.0                                          # 1cm あたりの画面の px
S_VIEW = 15.0                                      # 湯気を描く長さ（cm）
ZOOM0, ZOOM_T = 1.8, 1.25
WALL, WALL_L = "#55708a", "#6786a1"


def axp(s_cm, off=0.0):
    """軸の上 s cm の点から、軸に直角に off px ずらした点（画面の座標）"""
    return (TIPX + EXV[0] * s_cm * SC + NXV[0] * off, TIPY + EXV[1] * s_cm * SC + NXV[1] * off)


def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def clip_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    ctx.clip()


def border_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    _stroke(ctx, 3.5, INK, 0.75)


def zoom_art(ctx, t):
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(TIPX, TIPY)
    ctx.scale(z, z)
    ctx.translate(-TIPX, -TIPY)


# ---------- 絵: 台所・やかん・コンロ ----------

def draw_wall(ctx):
    fill(ctx, hexrgb(WALL))
    ctx.rectangle(PX0 - 300, PY0 - 300, PX1 - PX0 + 600, 1480 - PY0 + 300)
    ctx.fill()
    ctx.set_line_width(3)
    step = 84
    for i in range(-3, 16):
        for j in range(-4, 8):
            x, y = PX0 + i * step - 20, 1440 - (j + 1) * step
            core.rrect(ctx, x + 3, y + 3, step - 6, step - 6, 6)
            ctx.set_source_rgba(*hexrgb(WALL_L, 0.55))
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb("#7b99b3", 0.8))
            ctx.stroke()


def draw_stove(ctx, t):
    fill(ctx, hexrgb("#8b93a1"))                                   # コンロの天板
    ctx.rectangle(PX0 - 300, 1436, PX1 - PX0 + 600, 96)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    fill(ctx, hexrgb("#4a4f5a"))                                   # バーナー
    ctx.save()
    ctx.translate(290, 1452)
    ctx.scale(150, 14)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    for k in range(13):                                            # 炎（ゆらぐ）
        x = 290 - 126 + k * 21
        ph = t * (9.0 + 1.1 * k) + k * 1.7
        h = 34 + 8 * math.sin(ph) + 5 * math.sin(2.3 * ph + k)
        lean = 4 * math.sin(ph * 0.7 + k)
        for col, sc_, al in (("#4a86e8", 1.0, 0.9), ("#bfe0ff", 0.55, 0.95)):
            hh, w = h * sc_, 9.5 * sc_
            ctx.move_to(x - w, 1448)
            ctx.curve_to(x - w, 1448 - hh * 0.5, x + lean - 2, 1448 - hh * 0.8, x + lean, 1448 - hh)
            ctx.curve_to(x + lean + 2, 1448 - hh * 0.8, x + w, 1448 - hh * 0.5, x + w, 1448)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(col, al))
            ctx.fill()
    ctx.set_source_rgba(*hexrgb("#2e333c"))                        # 五徳
    ctx.set_line_width(9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for dx in (-130, -43, 43, 130):
        ctx.move_to(290 + dx, 1444)
        ctx.line_to(290 + dx * 0.95, 1420)
    ctx.stroke()
    fill(ctx, hexrgb("#5b6170"))                                   # 前のパネルとつまみ
    ctx.rectangle(PX0 - 300, 1532, PX1 - PX0 + 600, 120)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    for kx in (180, 400, 620, 840):
        fill(ctx, hexrgb("#e9edf2"))
        ctx.arc(kx, 1572, 26, 0, 2 * math.pi)
        ctx.fill_preserve()
        _stroke(ctx, 3)
        ctx.move_to(kx, 1572)
        ctx.line_to(kx, 1550)
        _stroke(ctx, 4)


def body_path(ctx):
    ctx.move_to(112, 1418)
    ctx.curve_to(92, 1330, 138, 1238, 220, 1208)
    ctx.curve_to(262, 1192, 330, 1192, 372, 1208)
    ctx.curve_to(444, 1238, 490, 1330, 468, 1418)
    ctx.close_path()


def draw_kettle(ctx, t):
    sm = sample()
    wtip = sm["p"]["d"] * SC + 16.0
    L = 215.0
    bx, by = TIPX - EXV[0] * L, TIPY - EXV[1] * L
    # 取っ手（上の弓）
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for (w_, col) in ((17, INK), (10, "#3a3f4a")):
        ctx.move_to(158, 1232)
        ctx.curve_to(170, 1085, 335, 1085, 352, 1212)
        _stroke(ctx, w_, col, 0.97)
    # 注ぎ口（先は、はかる口の太さ）
    ctx.move_to(bx - NXV[0] * 62, by - NXV[1] * 62)
    ctx.line_to(TIPX - NXV[0] * wtip / 2, TIPY - NXV[1] * wtip / 2)
    ctx.line_to(TIPX + NXV[0] * wtip / 2, TIPY + NXV[1] * wtip / 2)
    ctx.line_to(bx + NXV[0] * 62, by + NXV[1] * 62)
    ctx.close_path()
    fill(ctx, hexrgb("#d5dce4"))
    ctx.fill_preserve()
    _stroke(ctx, 4.5)
    # 胴
    body_path(ctx)
    fill(ctx, hexrgb("#eef2f6"))
    ctx.fill_preserve()
    _stroke(ctx, 5)
    body_path(ctx)
    ctx.save()
    ctx.clip()
    ctx.set_source_rgba(1, 1, 1, 0.6)
    ctx.set_line_width(10)
    ctx.move_to(150, 1300)
    ctx.curve_to(148, 1350, 152, 1380, 160, 1400)
    ctx.stroke()
    ctx.restore()
    # ふたとつまみ
    ctx.save()
    ctx.translate(246, 1200)
    ctx.scale(64, 13)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    fill(ctx, hexrgb("#c3ccd6"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    core.rrect(ctx, 232, 1170, 28, 26, 8)
    fill(ctx, hexrgb("#3a3f4a"))
    ctx.fill()


# ---------- 絵: 湯気 ----------
NP = 300
_RNG = np.random.default_rng(5)
P_PH = _RNG.random(NP)
P_SF = 0.88 + 0.24 * _RNG.random(NP)
P_ZE = np.clip(_RNG.normal(0.0, 0.55, NP), -1.0, 1.0)
P_WB = _RNG.random(NP) * 6.28
RATE = 0.6


def plume_b(s):
    """湯気の半径（cm）"""
    return sample()["p"]["d"] / 2 + 0.11 * s


def vis_target(s):
    """その距離で水の粒がどれだけ見えるか（0〜1）"""
    sm = sample()
    v = float(lwc_at(s))
    lm = sm["p"]["Lmin"]
    if v < lm:
        return 0.25 * v / lm
    return 0.3 + 0.7 * min(1.0, (v - lm) / (10 * lm))


def draw_plume(ctx, t, a=1.0):
    sm = sample()
    xs = sm["xs"]
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # 見えない水蒸気がある範囲（うすい点線）
    ctx.set_dash([9, 11])
    for sg in (-1, 1):
        for i in range(24):
            s0, s1 = S_VIEW * i / 24, S_VIEW * (i + 1) / 24
            p0, p1 = axp(s0, sg * plume_b(s0) * SC), axp(s1, sg * plume_b(s1) * SC)
            if i == 0:
                ctx.move_to(*p0)
            ctx.line_to(*p1)
    ctx.set_source_rgba(1, 1, 1, 0.45 * a)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_dash([])
    u = (t * RATE * P_SF + P_PH) % 1.0
    s = u * S_VIEW
    order = np.argsort(s)[::-1]
    lwc = lwc_at(s)
    lm = sm["p"]["Lmin"]
    for k in order:
        sk = float(s[k])
        b = plume_b(sk)
        wob = 0.18 * math.sin(t * 3.1 + P_WB[k] * 3.0) + 0.1 * math.sin(t * 7.3 + P_WB[k])
        off = (P_ZE[k] * 0.85 + wob) * b * SC
        x, y = axp(sk, off)
        w = clamp01((sk - (xs - 0.3)) / 0.6)                       # 気体 → 水の粒
        if w < 1.0:
            ctx.arc(x, y, 5.0, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.75 * (1 - w) * a)
            ctx.set_line_width(2.6)
            ctx.stroke()
        if w > 0.0:
            v = float(lwc[k])
            al = (0.25 * v / lm if v < lm else 0.3 + 0.7 * min(1.0, (v - lm) / (10 * lm))) if sk > 0 else 0.0
            rad = (0.30 + 0.12 * sk) * SC
            al = al * w * 0.34 * a
            if al > 0.004:
                g = cairo.RadialGradient(x, y, 0, x, y, rad)
                g.add_color_stop_rgba(0, 1, 1, 1, al)
                g.add_color_stop_rgba(0.55, 1, 1, 1, al * 0.7)
                g.add_color_stop_rgba(1, 1, 1, 1, 0)
                ctx.set_source(g)
                ctx.arc(x, y, rad, 0, 2 * math.pi)
                ctx.fill()


# ---------- 絵: 温度計・定規・はかる ----------
TH_X, TH_TOP, TH_BOT = 104.0, 940.0, 1090.0


def th_y(T):
    return TH_BOT + clamp01(T / 25.0) * (TH_TOP - TH_BOT)


def draw_thermo(ctx):
    Ta = sample()["p"]["Ta"]
    core.rrect(ctx, TH_X - 13, TH_TOP - 24, 26, TH_BOT - TH_TOP + 46, 13)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.set_source_rgba(*hexrgb(RED, 0.95))
    ctx.arc(TH_X, TH_BOT + 30, 19, 0, 2 * math.pi)
    ctx.fill()
    y = th_y(Ta)
    core.rrect(ctx, TH_X - 6, y, 12, TH_BOT + 22 - y, 6)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(2.5)
    for v in range(0, 26, 5):
        yy = th_y(v)
        ctx.move_to(TH_X - 13, yy)
        ctx.line_to(TH_X - 13 - (16 if v % 10 == 0 else 9), yy)
        ctx.stroke()


def draw_readouts(ctx):
    q = sample()["p"]
    text(ctx, f"室温 {q['Ta']:.0f}℃", 160, 985, 38, PAPER, align="left")
    text(ctx, f"湿度 {q['RH'] * 100:.0f}%", 160, 1040, 38, PAPER, align="left")


RULER_OFF = 104.0


def draw_ruler(ctx, t):
    p = ease_out((t - T_RULER) / 0.6)
    if p <= 0:
        return
    OFF, HW = RULER_OFF, 24.0
    s0, s1 = -0.6, 12.6 * p + (-0.6) * (1 - p)
    quad = [axp(s0, OFF - HW), axp(s1, OFF - HW), axp(s1, OFF + HW), axp(s0, OFF + HW)]
    ctx.move_to(*quad[0])
    for q in quad[1:]:
        ctx.line_to(*q)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#f2e6b8", 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.9)
    for k in range(0, 13):
        if k > s1:
            break
        ln = 16 if k % 5 else 24
        a_, b_ = axp(k, OFF - HW), axp(k, OFF - HW + ln)
        ctx.move_to(*a_)
        ctx.line_to(*b_)
        _stroke(ctx, 2.5 if k % 5 else 3.5, INK, 0.9)
        if k + 0.5 <= s1:
            ctx.move_to(*axp(k + 0.5, OFF - HW))
            ctx.line_to(*axp(k + 0.5, OFF - HW + 9))
            _stroke(ctx, 2, INK, 0.8)
    for k in range(0, 11, 2):
        if k <= s1:
            x, y = axp(k, OFF + 6)
            text(ctx, str(k), x, y, 26, INK)


def draw_measure(ctx, t):
    sm = sample()
    xs = sm["xs"]
    if t < T_SW0:
        return
    f = ease((t - T_SW0) / (T_SW1 - T_SW0))
    s = xs * f
    OFF = -62.0
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(*axp(0, OFF))
    ctx.line_to(*axp(s, OFF))
    _stroke(ctx, 7, "#ffd84d", 1.0)
    for ss in (0.0, s):
        ctx.move_to(*axp(ss, OFF - 18))
        ctx.line_to(*axp(ss, OFF + 18))
        _stroke(ctx, 6, "#ffd84d", 1.0)
    if t >= T_SW1:
        x, y = axp(xs, 0)
        ctx.set_source_rgba(*hexrgb(RED, 1.0))
        ctx.arc(x, y, 13, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 1.0)
        ctx.arc(x, y, 13, 0, 2 * math.pi)
        ctx.set_line_width(3.5)
        ctx.stroke()
        ctx.set_dash([8, 8])
        ctx.move_to(x, y)
        ctx.line_to(*axp(xs, RULER_OFF - 24))
        _stroke(ctx, 3.5, RED, 0.95)
        ctx.set_dash([])


def arrow(ctx, x0, y0, x1, y1, col="#ffd84d", a=1.0, w=5.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    _stroke(ctx, w, col, a)
    ang = math.atan2(y1 - y0, x1 - x0)
    ctx.move_to(x1 + 4 * math.cos(ang), y1 + 4 * math.sin(ang))
    ctx.line_to(x1 - 20 * math.cos(ang - 0.45), y1 - 20 * math.sin(ang - 0.45))
    ctx.line_to(x1 - 20 * math.cos(ang + 0.45), y1 - 20 * math.sin(ang + 0.45))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill()


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def fmt_cm(x):
    return f"{x:.1f}cm"


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    sm = sample()
    ctx.push_group()
    ctx.save()
    clip_panel(ctx)
    ctx.save()
    ctx.rectangle(PX0, PY0, PX1 - PX0, PY1 - PY0)
    ctx.clip()
    zoom_art(ctx, t)
    draw_wall(ctx)
    draw_plume(ctx, t)
    draw_kettle(ctx, t)
    draw_stove(ctx, t)
    ctx.restore()
    draw_thermo(ctx)
    draw_readouts(ctx)
    draw_ruler(ctx, t)
    draw_measure(ctx, t)
    # 札（見えない水蒸気・白い水の粒）
    if t >= T_LAB1:
        b = ease_out((t - T_LAB1) / 0.3)
        note.sticky(ctx, "見えない水蒸気（気体）", 715, 1372, 28, "blue", a=b, tilt=-0.02)
        xg, yg = axp(max(0.6, sm["xs"] * 0.45), 0)
        arrow(ctx, 640, 1334, xg + 12, yg + 16, a=b)
    if t >= T_LAB2:
        b = ease_out((t - T_LAB2) / 0.3)
        note.sticky(ctx, "白く見える水の粒", 665, 962, 28, "mint", a=b, tilt=0.02)
        xw, yw = axp(8.0, -6)
        arrow(ctx, 730, 1004, xw - 8, yw - 30, a=b)
    ctx.restore()
    border_panel(ctx)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_result(ctx, t):
    """「口から ○cm」の札（上のあき）"""
    if t < T_RES:
        return
    sm = sample()
    a = ease_out((t - T_RES) / 0.3) * (1 - ease((t - T_MANY + 0.1) / 0.3))
    if a <= 0:
        return
    note.sticky(ctx, f"この1回は、口から {fmt_cm(sm['xs'])} の\nところから白く見えた", 580, 715, 44, "yellow", fg=RED, a=a, tilt=-0.02)


def draw_many(ctx, t):
    if t < T_MANY:
        return
    a = ease_out((t - T_MANY) / 0.3) * (1 - ease((t - T_G0 + 0.1) / 0.3))
    if a <= 0:
        return
    note.sticky(ctx, "気温・湿度・口の太さ・\n火の強さを変えて 1万回", 580, 715, 42, "pink", a=a, tilt=0.015)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}
BINS = (X_NEAR, 3.0, 5.0)


def bin_code():
    """1回ごと: 0 = 1cm未満、1 = 1〜3cm、2 = 3〜5cm、3 = 5cm以上"""
    xs = results()["xs"]
    return np.digitize(xs, BINS)


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    code = bin_code()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_NEAR)] + [bgra(c) for c in COL_F], np.uint8)
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


def fit_size(lines, size, maxw):
    w = max(core.text_width(l, size) for l in lines)
    return size * min(1.0, maxw / w)


def sticky_fit(ctx, s, x, y, size, color, fg=INK, a=1.0, tilt=-0.02, maxw=700.0):
    sz = fit_size(s.split("\n"), size, maxw)
    return note.sticky(ctx, s, x, y, sz, color, fg=fg, a=a, tilt=tilt)


def cap_text():
    sh = shown()
    p = sh["p_far"]
    ptxt = "ほぼ100%" if p >= 0.995 else (f"約{int(math.floor(p * 100 + 0.5))}%")
    return f"1cm以上は {ptxt}"


def draw_grid(ctx, t):
    a = grid_alpha(t) * (1 - 0.8 * ease((t - T_REV) / 0.4))      # 答えの札を読ませるので、答えのあとはうすく
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
    code = bin_code()[:m]
    cnt = [int((code == k).sum()) for k in range(4)]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        tn, tf = TAG["near"], TAG["far"]
        rows = [(COL_NEAR, f"{tn} 1cm未満（口のすぐそば）", cnt[0]), (COL_F[0], f"{tf} 1〜3cm（少し離れた）", cnt[1]),
                (COL_F[1], f"{tf} 3〜5cm（少し離れた）", cnt[2]), (COL_F[2], f"{tf} 5cm以上（少し離れた）", cnt[3])]
        for i, (col, lab, c) in enumerate(rows):
            y = 1172 + i * 46
            fill(ctx, hexrgb(col, a * lg))
            ctx.rectangle(150, y - 15, 30, 30)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(150, y - 15, 30, 30)
            ctx.stroke()
            text(ctx, lab, 196, y, 30, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(c)}回", 915, y, 30, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            sticky_fit(ctx, cap_text(), 580, 1392, 40, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_far"], sh["xs_med"])


def head_text():
    key = answer_key()
    if key == "far":
        return "やっぱり、\n少し離れたところが正解。"
    if key == "near":
        return "残念、\n口のすぐそばが正解。"
    return "ほぼ同じ、\nが正解。"


def num_text():
    sh = shown()
    p = sh["p_far"]
    ptxt = "ほぼ100%" if p >= 0.995 else f"{int(math.floor(p * 100 + 0.5))}%"
    return f"この置き方なら、真ん中で約{int(round(sh['xs_med']))}cm\n1cm以上は {ptxt}"


def why_text():
    key = answer_key()
    if key == "far":
        return "口のすぐそばは、見えない水蒸気（気体）。\nまわりの空気で冷やされて 小さな水の粒に\nなると、光を散らして白く見える"
    return "白く見えるのは、冷やされてできた小さな水の粒。\n水蒸気そのものは見えない気体"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    b = ease_out((t - T_REV - 0.15) / 0.3)
    sticky_fit(ctx, head_text(), 580, 900, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        sticky_fit(ctx, num_text(), 580, 1090, 36, "blue", a=c, tilt=0.012, maxw=690.0)
    if t >= T_ANS3:
        c = ease_out((t - T_ANS3) / 0.3)
        sticky_fit(ctx, why_text(), 580, 1290, 34, "pink", a=c, tilt=-0.012, maxw=690.0)


# ---------- ひねり: 暖かい部屋（25℃）なら？ ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease_out((t - T_TW) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TWB + 0.3 + 2 * 0.45 + 0.5


def twist_text():
    sh = shown()
    d = sh["xs25_med"] - sh["xs_med"]
    if abs(d) < 0.3:
        return f"白く見えはじめる距離は ほぼ同じ。\n暖かい部屋は 約{int(round(sh['xs25_med']))}cm"
    return f"白く見えはじめる距離は {'少しのびる' if d > 0 else '少しちぢむ'}。\n暖かい部屋は 約{int(round(sh['xs25_med']))}cm"


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    if t < T_TWB:
        ba = ease_out((t - T_TW) / 0.25) * a * (1 - ease((t - T_TWB + 0.25) / 0.25))
        note.banner(ctx, "では、暖かい部屋\n（25℃）なら？", 560, 900, a=ba, t_rel=t - T_TW, size=56)
        return
    text(ctx, "白く見えはじめる距離（口から）", 580, 660, 38, INK, alpha=a)
    text(ctx, "1万回の 真ん中の値", 580, 718, 30, PENCIL, bold=False, alpha=a)
    x0, ln, v0, v1 = 330.0, 400.0, 0.0, 8.0
    rows = [("冬の台所\n（5〜20℃）", sh["xs_med"], "#7cc796"), ("暖かい部屋\n（25℃）", sh["xs25_med"], "#f2a65a")]
    for i, (lab, v, col) in enumerate(rows):
        y = 900 + i * 190
        tk = T_TWB + 0.3 + i * 0.45
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0 - 20, y, 30, INK, align="right", alpha=a)
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
        text(ctx, f"約{int(round(v))}cm", x0 + ln + 16, y, 46, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    text(ctx, "0cm", x0, 1235, 26, PENCIL, bold=False, alpha=a)
    text(ctx, "8cm", x0 + ln, 1235, 26, PENCIL, bold=False, alpha=a)
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


def big4_size(max_w=800.0):
    """4行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q4)


CD_X, CD_Y = 655.0, 1168.0                         # 予想して！3・2・1 の札（すき間のあたりをかくす）


class YIntro(note.Intro):
    """この回だけの冒頭。上: 問い4行（同じ大きさ・横幅いっぱい）・前提・三択（横1列）。その下に台所（0秒目から湯気が出ている）。
    注ぎ口のすぐ先は札でかくしておく（すき間が見えると答えがわかる）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = big4_size(800.0)
        lh = sz * 1.0
        ys = [436 + i * lh for i in range(4)]
        for line, y in zip(BIG_Q4, ys):
            pop = 1 + 0.07 * (1 - ease_out(t / 0.7))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w4 = core.text_width(BIG_Q4[3], sz)
        note.pen_line(ctx, 565 - w4 / 2 - 6, ys[3] + sz * 0.6, 565 + w4 / 2 + 6, ys[3] + sz * 0.57, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, ys[3] + sz * 0.62 + 30, 30, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = ys[3] + sz * 0.62 + 88
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        # かくす札（0秒目から。3・2・1 は 2.3 秒から）
        a2 = a
        cx, cy = CD_X, CD_Y
        fill(ctx, (*hexrgb(PAPER)[:3], 0.97 * a2))
        core.rrect(ctx, cx - 150, cy - 125, 300, 250, 18)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
        ctx.set_line_width(2.5)
        ctx.stroke()
        note.tape(ctx, cx, cy - 125, 120, 30, -0.04, a=a2)
        note.hand_text(ctx, "予想して！", cx, cy - 78, 44, RED, seed=41, alpha=a2, align="center")
        if t >= self.T_CD[0]:
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, cx, cy + 36, 54, 52, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy + 36)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) + 1 - n), 0, 0, 84, INK, alpha=a)
            ctx.restore()
        else:
            text(ctx, "？", cx, cy + 36, 96, INK, alpha=a2)

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


INTRO = YIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_result(ctx, t)
    draw_many(ctx, t)
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
        sticky_fit(ctx, "あなたの家のやかん、\n白い湯気は口から何cm？", 580, 800, 54, "yellow", a=q, tilt=-0.02, maxw=760.0)
        r1 = ease_out((t - T_Q - 1.8) / 0.3)
        if r1 > 0:
            note.sticky(ctx, "遠くから見たとき、\nすき間は見えましたか？", 580, 1040, 44, "pink", a=r1, tilt=0.015)
        r = ease_out((t - T_Q - 3.4) / 0.3)
        text(ctx, "コメントで教えてください", 580, 1230, 36, INK, bold=False, alpha=r)


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
    hi = n - np.convolve(n, np.ones(k * 6) / (k * 6), mode="same")
    return (0.5 * lo + 0.5 * hi) * amp


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    air = noise_band(t_end, 12, 4, 0.9)                    # 湯気の しゅーっ
    tt = np.arange(len(air)) / SR
    env_ = (0.75 + 0.25 * np.sin(2 * np.pi * 0.31 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, air * env_, 0.3)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    mx.add(T_RULER, whoosh(0.4), 0.25)
    mx.add(T_SW1, bell(784.0, 1.2), 0.45)                  # 白く見えはじめた所
    mx.add(T_RES, blip(587.3, 0.14), 0.3)
    mx.add(T_LAB1, blip(523.3, 0.12), 0.3)
    mx.add(T_LAB2, blip(659.3, 0.12), 0.3)
    mx.add(T_MANY, blip(587.3, 0.14), 0.3)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                    # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_ANS3, blip(659.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.8), 0.4)                          # ひねり
    for i in range(2):
        mx.add(T_TWB + 0.3 + i * 0.45, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    mx.add(T_Q + 1.8, blip(659.3, 0.14), 0.3)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    checks = []
    # (1) 水の飽和水蒸気圧（Antoine）が、よく知られた値と合う: 20℃で 2.339 kPa、100℃で 101.325 kPa に近い
    checks.append(("飽和水蒸気圧 20℃（kPa）", float(psat(20.0)) * 100.0, 2.339, 0.01 * 2.339))
    checks.append(("飽和水蒸気圧 5℃（kPa）", float(psat(5.0)) * 100.0, 0.8726, 0.01 * 0.8726))
    checks.append(("飽和水蒸気圧 60℃（kPa）", float(psat(60.0)) * 100.0, 19.946, 0.01 * 19.946))
    checks.append(("飽和水蒸気圧 100℃（kPa）", float(psat(100.0)) * 100.0, 101.325, 0.001 * 101.325))
    # (2) 熱と水の保存: 解いた温度・水の粒の量から、混ぜる前のエンタルピーを組み直して合う（最大の食い違い・割合）
    k = 300
    d1 = {kk: v[:k] for kk, v in p.items()}
    wa, _ = ambient(d1["Ta"], d1["RH"])
    lwc_, T_ = lwc_profile(d1["Ta"], wa, PHI)
    ph = PHI[None, :]
    rr = ph * (1.0 + wa[:, None]) / (1.0 - ph)
    wt = wa[:, None] + rr
    Htar = 1.006 * d1["Ta"][:, None] + wa[:, None] * (2501.0 + 1.86 * d1["Ta"][:, None]) + rr * (2501.0 + 1.86 * T_JET)
    wv = np.minimum(wt, wsat(T_))
    Hnow = 1.006 * T_ + wv * (2501.0 + 1.86 * T_) + (wt - wv) * 4.186 * T_
    checks.append(("エンタルピーの保存（最大の食い違い・割合）", float(np.max(np.abs(Hnow - Htar) / np.abs(Htar))), 0.0, 1e-6))
    # (3) 見本は1万回の中の1回。1回だけ計算した距離が、1万回の中のその回と同じ
    s = sample()
    checks.append(("見本の距離（cm）が1万回の値と同じ", s["chk"], s["xs"], 1e-9))
    # (4) 白く見えはじめるのは、混ざらない芯（x_c）より先
    checks.append(("白く見えはじめる距離 ≧ 芯の長さ（最小の差・cm）が 0 以上", float(np.min(r["xs"] - r["xc"]) >= 0), 1.0, 0.0))
    # (5) 噴き出す速さは距離を変えない（火の強さ・口から出る割合と距離の相関が小さい）
    checks.append(("火の強さと距離の相関が小さい", float(abs(np.corrcoef(p["Pb"], r["xs"])[0, 1]) < 0.03), 1.0, 0.0))
    checks.append(("口から出る割合と距離の相関が小さい", float(abs(np.corrcoef(p["fs"], r["xs"])[0, 1]) < 0.03), 1.0, 0.0))
    # (6) 答え: 決めておいた規則の答えが、画面の正解の位置と同じ。正解の記号は直前（10/29 が C）と同じにしない運用は統括が決める
    key = answer_by_rule(sh["p_far"], sh["xs_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（口のすぐそば・少し離れたところ）",
                   float(LABELS.index(KEY_LABEL["near"]) * 10 + LABELS.index(KEY_LABEL["far"])),
                   float("ABC".index(TAG["near"]) * 10 + "ABC".index(TAG["far"])), 0.0))
    # (7) 画面の回数が足して1万
    checks.append(("距離の区分の合計", float(sum(int((bin_code() == i).sum()) for i in range(4))), float(N_TRIAL), 0.0))
    checks.append(("見えない回（水の粒が1度もできない）は 0", float(sh["n_novis"]), 0.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  見本 {s['i']}（距離 {s['xs']:.2f}cm）  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}/{T_ANS3:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}")
    print("  上:", cap_text(), "|", num_text(), "|", why_text().replace("\n", " / "), "|", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.4, T_SW0 + 0.9, T_SW1 + 0.3, T_RES + 0.6, T_LAB2 + 0.8, T_MANY + 0.8, T_G0 + 1.5,
              T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_ANS3 + 0.8, T_TW + 0.8, T_TWB + 3.6, T_Q + 0.8, T_Q + 3.0, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
