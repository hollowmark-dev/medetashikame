"""寒い朝、洗濯物は外干しと部屋干し、どっちが早く乾く？ 同じバスタオルを1枚ずつ干して1万回。— 2026-10-22 作成（公開予定 10/28・30秒前後）

くらべるのは「早く乾くか」だけ（お金・電気代は入れない。画面にも概要欄にも書かない）。

モデル（バスタオル1枚の「残りの水」。外と部屋で同じ式）
  蒸発の速さ E = h_m × (ρ_sat(Ts) − ρ_air)   [kg/(m²·s)]   ρ は空気 1m³ に含まれる水蒸気の量（絶対湿度）
      h_m（物質移動係数）= h_c ÷ (ρ_空気 × c_p × Le^(2/3))      … 熱と水蒸気の伝わり方の類似（Chilton–Colburn）。Le（ルイス数）= 0.85〜0.90、c_p = 1006 J/(kg·K)
      h_c（風による熱伝達）= a + b × 風速 [W/(m²K)]、a = 2.8〜5.7、b = 3.0〜3.8   … 平らな面のまわりの風の経験式（仮定。出典は確認できなかった）
  タオル表面の温度 Ts … 熱のつり合いで決める（毎回、二分法で解く）
      (h_c + h_r) × (気温 − Ts) + 日ざしの熱 = L × E        L = 蒸発の潜熱 2.501e6 − 2370×T [J/kg]
      h_r = 5 W/(m²K)（まわりの壁・空との放射。まわりの温度は気温と同じとした＝仮定）。
      日ざしの熱（晴れの日のみ）= 吸収率 α × 日射 I ÷ 2（鉛直に吊ったタオルの片面だけが日に当たるので、両面の面積あたりでは半分）。
          α = 0.5〜0.7、I = 300〜550 W/m²（冬の南向きベランダの鉛直面の日射・仮定）。くもりは 0 とした（仮定）。
      水蒸気の飽和量: ρ_sat = 216.7 × e_s ÷ (T + 273.15) [g/m³]、e_s = 6.112 × exp(17.62 T/(243.12+T)) [hPa]（Magnus の式・WMO）。
  水が減るにつれて遅くなる: 残りの水が最初の f_c = 20〜35% まではそのままの速さ、それより少なくなると 残りの水に比例して遅くなる（よくある乾燥の形・仮定）。
  「乾いた」＝ 残りの水が 最初の 1割 になった時刻。

  外（冬の朝9時〜昼過ぎ・条件は乾くまで一定）:
      気温 2〜12℃・湿度 40〜70%・風 1〜4 m/秒（一様）。晴れ 60%・くもり 40%。
      ・気象庁 東京の平年値（1991〜2020年）: 12月 平均気温 7.7℃・風速 2.6 m/s・湿度 56%、1月 5.4℃・2.7 m/s・51%、2月 6.1℃・3.0 m/s・52%。
        日照時間 12月 174.4 h・1月 192.6 h・2月 170.4 h（1月は 1日平均 6.2 時間 ＝ 日の出から日没まで約10時間の 6割 → 晴れ 60% とした＝仮定）。
        https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=44&block_no=47662
        気温は日中を見込んで平年値より高めの 2〜12℃。風は観測所（高さ約10m）よりベランダは弱くなりやすいので 1〜4 m/秒。
  部屋（閉め切り・扇風機なし）:
      室温 16〜22℃・湿度 40〜60%・風 0.1〜0.3 m/秒（一様）。部屋の広さ 20〜35 m³（6〜10畳 × 天井 2.4m・仮定）。
      乾くにつれて部屋の湿度が上がる: V × dρ/dt = 蒸発した水の量 − 換気で入れ替わる量。
      換気 = 0.3〜0.7 回/時（仮定。建築基準法の 24時間換気は 0.5 回/時以上の機械換気を住宅に求める → 国土交通省 住宅の換気の資料）。
      入ってくる空気は、外の空気（外と同じ気温・湿度）。壁・家具・カーテンが水蒸気を吸う分は入れていない。
  バスタオル: 脱水後の水の量 300〜500 g（仮定。洗濯機の脱水後の含水率は 乾いた重さの 50〜100% 前後、バスタオル 400〜600 g として）。
      水に触れる面積（両面）1.0〜1.4 m²（60×120cm 2枚ぶん 1.44m² から、重なりを引いた・仮定）。
  測るもの: 外と部屋、それぞれ「残りの水が 1割 になるまでの時間」。同じ回の中で比べる（水の量・面積は同じタオル）。
  1回ごとに すべて でたらめに変える。1回は 5分きざみ（60秒きざみ）で足し算。

問い: 「寒い朝、洗濯物は外干しと部屋干し、/ どっちが早く乾く？」（前提「冬の朝9時スタート・同じバスタオル1枚ずつ」）
      選択肢（記号の並びは LABELS の順。正解・TAG は 計算の結果で決める）: 外干し ／ ほぼ同じ ／ 部屋干し
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「外が先に乾いた回」の割合 p と、乾いた時刻の差（部屋 − 外）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 30分 なら「外干し」、p ≤ 40% かつ g ≤ −30分 なら「部屋干し」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「部屋干しに風 1.5 m/秒を当てたら？」（部屋の風だけを変えて同じ1万回を再計算）。
締め: 「あなたは、冬は 外干し？部屋干し？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（並んで乾く2枚）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "sentaku-hoshi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261028
DT = 60.0                                          # 足し算のきざみ（秒）
TMAX = 48 * 3600.0
DRY_AT = 0.10                                      # 残りの水がこの割合になったら「乾いた」
# 外
P_SUNNY = 0.60
TA_OUT, RH_OUT, V_OUT = (2.0, 12.0), (0.40, 0.70), (1.0, 4.0)
I_SUN, ALPHA = (300.0, 550.0), (0.5, 0.7)
# 部屋
TA_IN, RH_IN, V_IN = (16.0, 22.0), (0.40, 0.60), (0.1, 0.3)
VOL_ROOM, ACH = (20.0, 35.0), (0.3, 0.7)           # m³、回/時
V_FAN = 1.5                                        # ひねり（部屋に当てる風）m/秒
# タオル
M_WATER, AREA, F_CRIT = (0.30, 0.50), (1.0, 1.4), (0.20, 0.35)   # kg、m²、割合
HC_A, HC_B, LEWIS = (2.8, 5.7), (3.0, 3.8), (0.85, 0.90)
H_R = 5.0
RHO_AIR, CP_AIR = 1.2, 1006.0

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 30.0      # 分


def answer_by_rule(p_out, gap_med_min):
    """p_out = 外が先に乾いた回の割合、gap_med_min = (部屋 − 外) の乾いた時刻の差の真ん中の値（分）。'out' / 'same' / 'in'"""
    if p_out >= RULE_HI and gap_med_min >= RULE_GAP:
        return "out"
    if p_out <= RULE_LO and gap_med_min <= -RULE_GAP:
        return "in"
    return "same"


def es_hpa(T):
    return 6.112 * np.exp(17.62 * T / (243.12 + T))


def rho_sat(T):
    """飽和水蒸気量 kg/m³"""
    return 216.7 * es_hpa(T) / (np.asarray(T, float) + 273.15) * 1e-3


def latent(T):
    return 2.501e6 - 2370.0 * np.asarray(T, float)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    return dict(sunny=rng.uniform(0, 1, n) < P_SUNNY, Ta=u(TA_OUT), rh=u(RH_OUT), v=u(V_OUT), I=u(I_SUN), alpha=u(ALPHA),
                Tr=u(TA_IN), rhr=u(RH_IN), vr=u(V_IN), V=u(VOL_ROOM), ach=u(ACH),
                m0=u(M_WATER), A=u(AREA), fc=u(F_CRIT), a=u(HC_A), b=u(HC_B), Le=u(LEWIS))


def solve_Ts(Ta, hc, hr, qs, hm, rho_a):
    """熱のつり合い (hc+hr)(Ta−Ts) + qs = L·hm·(ρsat(Ts) − ρa) を満たす Ts（二分法）"""
    lo, hi = Ta - 30.0, Ta + 40.0
    for _ in range(40):
        mid = (lo + hi) / 2
        f = (hc + hr) * (Ta - mid) + qs - latent(mid) * hm * (rho_sat(mid) - rho_a)
        pos = f > 0
        lo = np.where(pos, mid, lo)
        hi = np.where(pos, hi, mid)
    return (lo + hi) / 2


def env(d, indoor, fan=False):
    """外 / 部屋の空気の条件"""
    n = len(d["Ta"])
    if indoor:
        Ta, v = d["Tr"], (np.full(n, V_FAN) if fan else d["vr"])
        qs = np.zeros(n)
        rho = d["rhr"] * rho_sat(Ta)
    else:
        Ta, v = d["Ta"], d["v"]
        qs = np.where(d["sunny"], d["alpha"] * d["I"] / 2.0, 0.0)
        rho = d["rh"] * rho_sat(Ta)
    hc = d["a"] + d["b"] * v
    hm = hc / (RHO_AIR * CP_AIR * d["Le"] ** (2.0 / 3.0))
    return Ta, qs, rho, hc, hm


def run(d, indoor, fan=False, hist=False):
    """残りの水が DRY_AT になる時刻（秒）を返す。hist=True（1回ぶんだけ）なら (時刻の配列[秒], 残りの割合, 絶対湿度[kg/m³]) も"""
    n = len(d["Ta"])
    Ta, qs, rho, hc, hm = env(d, indoor, fan)
    rho_out = d["rh"] * rho_sat(d["Ta"])
    m = d["m0"].copy()
    f = np.ones(n)
    tfin = np.full(n, np.inf)
    rh_max = np.zeros(n)
    t = 0.0
    H = [(0.0, 1.0, float(rho[0]))] if hist else None
    while t < TMAX and np.isinf(tfin).any():
        act = np.isinf(tfin)
        Ts = solve_Ts(Ta, hc, H_R, qs, hm, rho)
        Ec = hm * (rho_sat(Ts) - rho)
        E = Ec * np.minimum(1.0, f / d["fc"])
        dm = np.minimum(d["A"] * E * DT, m)
        mn = m - dm
        fn = mn / d["m0"]
        hit = act & (fn <= DRY_AT)
        frac = (f - DRY_AT) / np.maximum(f - fn, 1e-12)
        tfin = np.where(hit, t + frac * DT, tfin)
        if indoor:
            rho = rho + dm / d["V"] - d["ach"] / 3600.0 * DT * (rho - rho_out)
            rh_max = np.maximum(rh_max, np.where(act, rho / rho_sat(Ta), 0.0))
        m, f, t = mn, fn, t + DT
        if hist:
            H.append((t, float(f[0]), float(rho[0])))
    out = tfin
    if hist:
        return out, np.array(H)
    return out, rh_max


def evap0(d, indoor):
    """はじめの蒸発の速さ（kg/(m²·s)）"""
    Ta, qs, rho, hc, hm = env(d, indoor)
    Ts = solve_Ts(Ta, hc, H_R, qs, hm, rho)
    return hm * (rho_sat(Ts) - rho), Ts


def analytic_out(d):
    """外は空気の条件が変わらないので、式で解ける（数値の足し算の答え合わせ用）。秒"""
    Ec, _ = evap0(d, False)
    k = d["m0"] / (d["A"] * Ec)
    return k * (1 - d["fc"]) + k * d["fc"] * np.log(d["fc"] / DRY_AT) + 0 * k
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
        r = dict(t_out=z["t_out"], t_in=z["t_in"], t_fan=z["t_fan"], rhmax=z["rhmax"], e_out=z["e_out"], e_in=z["e_in"])
    else:
        t_out, _ = run(d, False)
        t_in, rhmax = run(d, True)
        t_fan, _ = run(d, True, fan=True)
        e_out, _ = evap0(d, False)
        e_in, _ = evap0(d, True)
        np.savez(fn, t_out=t_out, t_in=t_in, t_fan=t_fan, rhmax=rhmax, e_out=e_out, e_in=e_in)
        r = dict(t_out=t_out, t_in=t_in, t_fan=t_fan, rhmax=rhmax, e_out=e_out, e_in=e_in)
    r["p"] = d
    r["t_out"], r["t_in"], r["t_fan"] = r["t_out"] / 60.0, r["t_in"] / 60.0, r["t_fan"] / 60.0   # 分
    _RES["m"] = r
    return r


def shown():
    r = results()
    p = r["p"]
    to, ti, tf = r["t_out"], r["t_in"], r["t_fan"]
    gap = ti - to
    gapf = tf - to
    sun = p["sunny"]
    win = to < ti
    return dict(p_out=float(win.mean()), n_out=int(win.sum()), n_in=int((~win).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_out=float(np.median(to)), med_in=float(np.median(ti)),
                q_out=np.percentile(to, [10, 90]), q_in=np.percentile(ti, [10, 90]),
                p_sun=float(win[sun].mean()), p_cloud=float(win[~sun].mean()),
                gap_sun=float(np.median(gap[sun])), gap_cloud=float(np.median(gap[~sun])),
                med_out_sun=float(np.median(to[sun])), med_out_cloud=float(np.median(to[~sun])),
                ratio_e=float(np.median(r["e_out"] / r["e_in"])),
                p_fan=float((to < tf).mean()), gap_fan=float(np.median(gapf)), med_fan=float(np.median(tf)),
                n_unfinished=int(np.isinf(to).sum() + np.isinf(ti).sum()),
                out_late=float((to > 420).mean()),     # 9時スタートで16時（7時間）より遅い
                rh_max_q=np.percentile(r["rhmax"], [50, 90, 100]),
                n_sun=int(sun.sum()))


def hm_(minutes):
    """分 → '2時間54分' / '45分'"""
    mm = int(round(minutes))
    h, m = divmod(mm, 60)
    return f"{h}時間{m:02d}分" if h else f"{m}分"


def hm_about(minutes):
    """約 の付く短い言い方（5分きざみ）"""
    mm = int(round(minutes / 5.0)) * 5
    h, m = divmod(mm, 60)
    if h and m:
        return f"約{h}時間{m}分"
    if h:
        return f"約{h}時間"
    return f"約{m}分"


def report():
    sh = shown()
    print(f"外が先 {sh['p_out']:.4f}（{sh['n_out']}回 / 部屋が先 {sh['n_in']}回）  差(部屋−外)の中央値 {sh['gap_med']:+.1f}分 "
          f"平均 {sh['gap_mean']:+.1f}  10/25/75/90% {np.round(sh['gap_q'], 0)}")
    print(f"  答え {answer_by_rule(sh['p_out'], sh['gap_med'])}")
    print(f"  乾く時間の中央値 外 {sh['med_out']:.0f}分（{hm_(sh['med_out'])}）10/90% {np.round(sh['q_out'], 0)} / "
          f"部屋 {sh['med_in']:.0f}分（{hm_(sh['med_in'])}）10/90% {np.round(sh['q_in'], 0)}")
    print(f"  晴れ({sh['n_sun']}回): 外が先 {sh['p_sun']:.3f} 差 {sh['gap_sun']:+.0f}分 外の中央値 {sh['med_out_sun']:.0f}分 / "
          f"くもり: 外が先 {sh['p_cloud']:.3f} 差 {sh['gap_cloud']:+.0f}分 外の中央値 {sh['med_out_cloud']:.0f}分")
    print(f"  はじめの蒸発の速さ 外/部屋 の中央値 {sh['ratio_e']:.2f}倍  外が7時間より遅い割合 {sh['out_late']:.3f}  "
          f"未完了 {sh['n_unfinished']}  部屋の湿度の最大(50/90/100%点) {np.round(sh['rh_max_q'], 3)}")
    print(f"  ひねり 部屋に風{V_FAN}m/秒: 外が先 {sh['p_fan']:.3f} 差 {sh['gap_fan']:+.0f}分 部屋の中央値 {sh['med_fan']:.0f}分")


def tw_check():
    """湿球温度の確認: 風がとても強い・日ざし無しなら、表面の温度は湿球温度に近づく。20℃ 50% の湿球温度は約 13.7℃（気象庁の湿度表）"""
    one = lambda x: np.array([x], float)   # noqa: E731
    Ta = one(20.0)
    rho = 0.5 * rho_sat(Ta)
    hc = one(300.0)
    hm = hc / (RHO_AIR * CP_AIR * 0.875 ** (2.0 / 3.0))
    return float(solve_Ts(Ta, hc, H_R, one(0.0), hm, rho)[0])


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    print(f"  湿球温度の確認 20℃ 50%: {tw_check():.2f}℃（気象庁の湿度表 約13.7℃）")
    sys.exit(0)


# =====================================================================
# 見本（並んで乾く2枚）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 晴れの回（絵に日ざしが出る）、差が真ん中の値の近く（±8%）、外の時間・部屋の時間とも真ん中の近く（±12%）。
    その中で差が真ん中に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    to, ti = r["t_out"], r["t_in"]
    gap = ti - to
    cand = np.nonzero(p["sunny"] & (np.abs(gap / sh["gap_med"] - 1) < 0.08) & (np.abs(to / sh["med_out"] - 1) < 0.12)
                      & (np.abs(ti / sh["med_in"] - 1) < 0.12))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    d1 = {k: v[i:i + 1] for k, v in p.items()}
    t_o, ho = run(d1, False, hist=True)
    t_i, hi = run(d1, True, hist=True)
    q = {k: (v[i].item() if hasattr(v[i], "item") else v[i]) for k, v in p.items()}
    _SAMPLE = dict(i=i, p=q, t_out=float(to[i]), t_in=float(ti[i]), gap=float(gap[i]),
                   h_out=ho, h_in=hi, chk=(float(t_o[0]) / 60.0, float(t_i[0]) / 60.0))
    return _SAMPLE


def f_at(h, minutes):
    return float(np.interp(minutes * 60.0, h[:, 0], h[:, 1]))


def rh_in_at(minutes):
    s = sample()
    return float(np.interp(minutes * 60.0, s["h_in"][:, 0], s["h_in"][:, 2]) / rho_sat(s["p"]["Tr"]))


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    p = s["p"]
    print("見本", s["i"], "外: 気温", round(p["Ta"], 1), "湿度", round(p["rh"] * 100), "風", round(p["v"], 1), "晴れ" if p["sunny"] else "くもり",
          "| 部屋:", round(p["Tr"], 1), "℃", round(p["rhr"] * 100), "% 風", round(p["vr"], 2), "| 水", round(p["m0"] * 1000), "g",
          "面積", round(p["A"], 2), "| 外", hm_(s["t_out"]), "部屋", hm_(s["t_in"]), "差", round(s["gap"]), "分")
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
note.DATE = "10.28"                                # 日付欄（公開予定日）

COL_O, INK_O = "#8fbbe8", "#2f63a8"                # 外干し（水色）
COL_I, INK_I = "#f4ad6a", "#b8601a"                # 部屋干し（だいだい）
WATER = "#58a8e4"
TOWEL_DRY, TOWEL_WET = "#fbf3e2", "#7f9fcc"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["外干し", "ほぼ同じ", "部屋干し"]
TAG = {"out": "A", "in": "C"}
CORRECT = 0                                        # answer_by_rule の結果の位置
KEY_LABEL = {"out": "外干し", "same": "ほぼ同じ", "in": "部屋干し"}
NAME = {"out": "外干し", "in": "部屋干し"}
COLS = {"out": COL_O, "in": COL_I}
INKC = {"out": INK_O, "in": INK_I}

BIG_Q = ["寒い朝、洗濯物は外干しと部屋干し、", "どっちが早く乾く？"]           # 定位置（上）の2行
BIG_Q3 = ["寒い朝、洗濯物は", "外干しと部屋干し、", "どっちが早く乾く？"]     # 1コマ目の3行（同じ大きさ）
DETAIL = "冬の朝9時スタート・同じバスタオル1枚ずつ"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 7.4                                     # T_GO から2枚とも乾くまで
R0 = 0.9                                           # 冒頭の進み（シミュの分／動画の秒）。答えが見えないよう、ほとんど進めない

# 画面の置き場所
PN = {"out": dict(x0=80.0, x1=520.0, cx=300.0), "in": dict(x0=580.0, x1=1020.0, cx=800.0)}
# 問いが3行になったので、パネルは下へ（問いとパネルは真ん中の正方形 y420〜1500 に収める）。絵は旧い座標（AY0〜）で描いて DY だけずらす
AY0, AY1, ACARD = 745.0, 1445.0, 1192.0
PY0, PY1 = 830.0, 1480.0
DY = PY0 - AY0
POLE_Y, TOW_W, TOW_H = 935.0, 190.0, 228.0
CARD_Y = 1256.0


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_out"], s["t_in"]))
    T_FIN2 = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 60, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
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
    T_Q = 26.0
    DURATION = T_Q + 3.9


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


def fs(t):
    """その時刻の (外の残り, 部屋の残り)"""
    s = sample()
    tau = tau_of(t)
    return f_at(s["h_out"], tau), f_at(s["h_in"], tau)


def pcs(f):
    return f"{int(math.floor(f * 100 + 1e-9))}%"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def lerp_col(c0, c1, u):
    a, b = hexrgb(c0), hexrgb(c1)
    return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))


def clip_panel(ctx, k):
    pn = PN[k]
    core.rrect(ctx, pn["x0"], PY0, pn["x1"] - pn["x0"], PY1 - PY0, 22)
    ctx.clip()


def border_panel(ctx, k):
    pn = PN[k]
    core.rrect(ctx, pn["x0"], PY0, pn["x1"] - pn["x0"], PY1 - PY0, 22)
    _stroke(ctx, 3.5, INK, 0.75)


def cloud(ctx, x, y, s, col, a=1.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    for dx, dy, r in ((0, 0, 30), (34, -12, 38), (74, 0, 30), (36, 12, 34)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi)
        ctx.fill()


ZOOM0, ZOOM_T = 1.40, 1.25


def zoom_art(ctx, t, cx):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(cx, 1010.0)
    ctx.scale(z, z)
    ctx.translate(-cx, -1010.0)


def draw_sun(ctx, x, y, t):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(12):
        a = t * 0.5 + k * math.pi / 6
        r0, r1 = 40, 56 + 4 * math.sin(t * 3 + k)
        ctx.move_to(x + r0 * math.cos(a), y + r0 * math.sin(a))
        ctx.line_to(x + r1 * math.cos(a), y + r1 * math.sin(a))
        _stroke(ctx, 5.5, "#f2a21d", 0.95)
    fill(ctx, hexrgb("#ffd95a"))
    ctx.arc(x, y, 32, 0, 2 * math.pi)
    ctx.fill_preserve()
    _stroke(ctx, 3.0, "#e8901a", 0.9)


def towel_poly(ctx, cx, py, w, h, t, amp, phi, u0, u1, dx0=0.0, n=14):
    def off(u):
        return amp * (u ** 1.4) * (0.65 * math.sin(2 * math.pi * 0.85 * t + 2.0 * u + phi)
                                   + 0.35 * math.sin(2 * math.pi * 2.1 * t + 4.5 * u + 2 * phi))
    us = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
    for i, u in enumerate(us):
        x = cx - w / 2 + dx0 + off(u)
        (ctx.move_to if i == 0 else ctx.line_to)(x, py + u * h)
    for u in reversed(us):
        x = cx + w / 2 + dx0 + off(u) + 0.18 * amp * u * math.sin(2 * math.pi * 1.3 * t + 6 * u + phi)
        ctx.line_to(x, py + u * h)
    ctx.close_path()


def draw_towel(ctx, cx, py, t, amp, f, phi, drip=True):
    """バスタオルをバーに掛けた絵（前と後ろの2枚）。amp は風による揺れ(px)、f は残りの水(0〜1)"""
    wet = clamp01((f - DRY_AT) / (1 - DRY_AT)) ** 0.8
    col = lerp_col(TOWEL_DRY, TOWEL_WET, wet)
    back = tuple(c * 0.88 for c in col)
    towel_poly(ctx, cx, py - 4, TOW_W, TOW_H * 0.95, t, amp * 0.9, phi + 0.7, 0.0, 1.0, dx0=10)
    ctx.set_source_rgba(*back, 1.0)
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.7)
    towel_poly(ctx, cx, py - 4, TOW_W, TOW_H, t, amp, phi, 0.0, 1.0)
    ctx.set_source_rgba(*col, 1.0)
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    for (a, b) in ((0.76, 0.81), (0.85, 0.90)):                 # 端の縞
        towel_poly(ctx, cx, py - 4, TOW_W, TOW_H, t, amp, phi, a, b, n=3)
        ctx.set_source_rgba(*lerp_col("#a9dcc8", "#6f9fb6", wet), 0.9)
        ctx.fill()
    if drip and f > 0.55:
        al = clamp01((f - 0.55) / 0.2)
        u = 1.0
        ox = amp * (u ** 1.4) * (0.65 * math.sin(2 * math.pi * 0.85 * t + 2.0 * u + phi)
                                 + 0.35 * math.sin(2 * math.pi * 2.1 * t + 4.5 * u + 2 * phi))
        for k, fx in enumerate((-0.32, 0.05, 0.36)):
            ph = (t * 1.1 + k * 0.37) % 1.0
            x = cx + fx * TOW_W + ox
            y = py - 4 + TOW_H + ph * 62
            ctx.set_source_rgba(*hexrgb(WATER, 0.85 * al * (1 - ph ** 2)))
            ctx.arc(x, y, 5.5 - 2.5 * ph, 0, 2 * math.pi)
            ctx.fill()
    # バー
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - TOW_W / 2 - 24, py - 6)
    ctx.line_to(cx + TOW_W / 2 + 24, py - 6)
    _stroke(ctx, 9, INK, 0.85)
    ctx.move_to(cx - TOW_W / 2 - 24, py - 6)
    ctx.line_to(cx + TOW_W / 2 + 24, py - 6)
    _stroke(ctx, 5, "#c9d1da", 1.0)


# ---------- 絵: 外（ベランダ） ----------

def draw_out(ctx, t, f):
    s = sample()
    p = s["p"]
    pn = PN["out"]
    ctx.save()
    clip_panel(ctx, "out")
    ctx.translate(0, DY)
    zoom_art(ctx, t, pn["cx"])
    g = cairo.LinearGradient(0, AY0, 0, ACARD)
    if p["sunny"]:
        g.add_color_stop_rgb(0, *hexrgb("#aed8f3")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#e9f5fb")[:3])
    else:
        g.add_color_stop_rgb(0, *hexrgb("#b9c6d2")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#e3e8ec")[:3])
    ctx.set_source(g)
    ctx.rectangle(pn["x0"], AY0, pn["x1"] - pn["x0"], AY1 - AY0)
    ctx.fill()
    spd = 26 + 18 * p["v"]
    # 雲（風で流れる）
    span = pn["x1"] - pn["x0"] + 260
    if p["sunny"]:
        cl = ((0, 925, 0.7, "#ffffff", 0.9), (150, 1010, 0.55, "#ffffff", 0.8), (300, 960, 0.6, "#ffffff", 0.85))
        draw_sun(ctx, pn["x0"] + 70, 985, t)
    else:
        cl = ((0, 915, 1.1, "#8e9aa8", 0.95), (190, 985, 0.95, "#a3aeba", 0.95), (330, 940, 1.0, "#939fad", 0.95))
    for k, (ox, y, sc, col, al) in enumerate(cl):
        x = pn["x0"] - 130 + (ox + t * spd * (0.8 + 0.3 * k)) % span
        cloud(ctx, x, y, sc, col, al)
    # 町なみ（遠い建物。窓つき）
    for (x, w_, h_, col) in ((90, 90, 110, "#aebfd0"), (170, 70, 150, "#9fb2c5"), (260, 100, 100, "#b6c6d6"), (370, 80, 140, "#a3b6c9"),
                             (445, 90, 105, "#b2c3d3")):
        ctx.rectangle(x, 1112 - h_, w_, h_ + 8)
        ctx.set_source_rgba(*hexrgb(col, 1))
        ctx.fill()
        ctx.set_source_rgba(*hexrgb("#e9f2f8", 0.95))
        for wy in range(int(1112 - h_ + 14), 1100, 30):
            for wx in range(int(x + 10), int(x + w_ - 12), 24):
                ctx.rectangle(wx, wy, 11, 15)
                ctx.fill()
    # ベランダの手すり
    ctx.set_source_rgba(*hexrgb("#7d8895", 0.95))
    for x in range(int(pn["x0"]) + 10, int(pn["x1"]), 36):
        ctx.rectangle(x, 1120, 6, ACARD - 1120)
        ctx.fill()
    ctx.rectangle(pn["x0"], 1112, pn["x1"] - pn["x0"], 12)
    ctx.fill()
    # 風の筋
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(10):
        y = 895 + (k * 41) % 270
        sp = 120 * p["v"] * (0.8 + 0.4 * ((k * 7) % 5) / 4)
        L = 70 + 12 * (k % 4)
        x = pn["x0"] - L + ((t * sp + 53 * k) % (pn["x1"] - pn["x0"] + 2 * L))
        for i in range(9):
            xx = x - L + i * L / 8
            yy = y + 4 * math.sin(i * 0.9 + t * 4 + k)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        _stroke(ctx, 6, "#4f82b8", 0.7)
    # 物干しざお
    for x in (pn["x0"] + 40, pn["x1"] - 40):
        ctx.move_to(x, POLE_Y - 6)
        ctx.line_to(x, ACARD)
        _stroke(ctx, 7, INK, 0.8)
    draw_towel(ctx, pn["cx"], POLE_Y, t, (8 + 9 * p["v"]) * (1 + 0.9 * math.exp(-t / 0.7)), f, 0.3)
    ctx.restore()
    border_panel(ctx, "out")


# ---------- 絵: 部屋 ----------

def draw_in(ctx, t, f):
    s = sample()
    p = s["p"]
    pn = PN["in"]
    ctx.save()
    clip_panel(ctx, "in")
    ctx.translate(0, DY)
    zoom_art(ctx, t, pn["cx"])
    fill(ctx, hexrgb("#f4ead7"))
    ctx.rectangle(pn["x0"], AY0, pn["x1"] - pn["x0"], AY1 - AY0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#dcc9a4", 0.95))                  # 壁のしま
    for x in range(int(pn["x0"]) - 80, int(pn["x1"]) + 80, 32):
        ctx.rectangle(x, AY0 - 120, 14, ACARD - AY0 + 120)
        ctx.fill()
    fill(ctx, hexrgb("#d9b98a"))                                  # 床
    ctx.rectangle(pn["x0"], 1150, pn["x1"] - pn["x0"], AY1 - 1150)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#b8946a", 0.7))
    ctx.set_line_width(2.5)
    for i in range(0, 9):
        ctx.move_to(pn["x0"] + i * 60 - 20, 1150)
        ctx.line_to(pn["x0"] + i * 60 - 60, AY1)
    ctx.stroke()
    ctx.rectangle(pn["x0"], 1142, pn["x1"] - pn["x0"], 10)
    ctx.set_source_rgba(*hexrgb("#f7f1e6", 1))
    ctx.fill()
    # 窓（外は冬の空）
    wx0, wy0, ww, wh = 920.0, 935.0, 88.0, 170.0
    fill(ctx, hexrgb("#b8dcf0"))
    ctx.rectangle(wx0, wy0, ww, wh)
    ctx.fill()
    cloud(ctx, wx0 + 6 + (t * 6) % 70 - 20, wy0 + 40, 0.28, "#ffffff", 0.9)
    ctx.rectangle(wx0, wy0, ww, wh)
    _stroke(ctx, 5, INK, 0.85)
    ctx.move_to(wx0 + ww / 2, wy0)
    ctx.line_to(wx0 + ww / 2, wy0 + wh)
    ctx.move_to(wx0, wy0 + wh / 2)
    ctx.line_to(wx0 + ww, wy0 + wh / 2)
    _stroke(ctx, 3.5, INK, 0.8)
    # カーテン（ほとんど揺れない）
    sw = 3.5 * math.sin(2 * math.pi * 0.35 * t) + 1.6 * math.sin(2 * math.pi * 0.9 * t + 1)
    ctx.set_source_rgba(*hexrgb("#f1b7c4", 0.97))
    ctx.move_to(wx0 - 52, wy0 - 14)
    ctx.line_to(wx0 + 10, wy0 - 14)
    for i in range(11):
        u = i / 10
        ctx.line_to(wx0 + 10 + sw * u * u, wy0 - 14 + u * 215)
    for i in range(11):
        u = 1 - i / 10
        ctx.line_to(wx0 - 52 + sw * u * u * 0.7, wy0 - 14 + u * 215)
    ctx.close_path()
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.6)
    ctx.move_to(wx0 - 62, wy0 - 16)
    ctx.line_to(wx0 + 100, wy0 - 16)
    _stroke(ctx, 6, "#8a6a4a", 0.9)
    # 物干し（室内用の A 型ラック）
    cx = pn["cx"]
    for sgn in (-1, 1):
        ctx.move_to(cx + sgn * 124, POLE_Y - 6)
        ctx.line_to(cx + sgn * 150, 1175)
        _stroke(ctx, 7, INK, 0.8)
        ctx.move_to(cx + sgn * 150 - 22, 1175)
        ctx.line_to(cx + sgn * 150 + 22, 1175)
        _stroke(ctx, 7, INK, 0.8)
    draw_towel(ctx, cx, POLE_Y, t, 0.9 + 3.5 * p["vr"], f, 1.9)
    ctx.restore()
    border_panel(ctx, "in")


# ---------- メーター（しずく） ----------

def drop_path(ctx, cx, top, w, h):
    r = w / 2
    yb = top + h - r
    d = yb - top
    beta = math.acos(r / d)
    ctx.new_path()
    ctx.move_to(cx, top)
    a1 = math.atan2(-math.cos(beta), math.sin(beta))
    ctx.line_to(cx + r * math.sin(beta), yb - r * math.cos(beta))
    ctx.arc(cx, yb, r, a1, math.pi - a1)
    ctx.close_path()


def draw_drop(ctx, cx, top, w, h, f, t, done):
    ctx.save()
    drop_path(ctx, cx, top, w, h)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    ctx.clip()
    y = top + h - f * h
    ctx.set_source_rgba(*hexrgb(WATER, 0.95))
    ctx.move_to(cx - w, top + h + 4)
    for i in range(21):
        x = cx - w + i * (2 * w) / 20
        ctx.line_to(x, y + 2.5 * math.sin(x / 11 + t * 5))
    ctx.line_to(cx + w, top + h + 4)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    drop_path(ctx, cx, top, w, h)
    _stroke(ctx, 4.5, INK, 0.9)
    yd = top + h - DRY_AT * h                                      # 「1割」の印
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - w / 2 - 14, yd)
    ctx.line_to(cx + w / 2 + 14, yd)
    _stroke(ctx, 4, RED, 0.9)


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_card(ctx, t, k, f, t_fin, done_t):
    pn = PN[k]
    cx = pn["cx"]
    core.rrect(ctx, pn["x0"] + 10, CARD_Y - 6, pn["x1"] - pn["x0"] - 20, PY1 - CARD_Y - 4, 18)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.96))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    done = done_t is not None
    draw_drop(ctx, cx, CARD_Y + 2, 70, 88, f, t, done)
    if not done:
        text(ctx, "残りの水", cx, 1370, 28, PENCIL, bold=False)
        text(ctx, pcs(f), cx, 1418, 56, INKC[k])
    else:
        u = clamp01((t - done_t) / 0.35)
        text(ctx, "乾いた！", cx, 1368, 36, RED)
        lab = hm_(t_fin)
        sz = 40
        while core.text_width(lab, sz) > 215:
            sz -= 1
        text(ctx, lab, cx, 1418, sz, INKC[k])
        note.pen_circle(ctx, cx, 1418, 112, 34, RED, seed=70 + (k == "in"), width=4.5, progress=u)


def draw_header(ctx, t, k, rh_now):
    s = sample()
    p = s["p"]
    pn = PN[k]
    cx = pn["cx"]
    xd, yd = cx - 100, PY0 + 38
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 24, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 24, 24, INKC[k], seed=13 + (k == "in"), width=3.4)
    text(ctx, TAG[k], xd, yd, 32, INKC[k])
    text(ctx, NAME[k], cx - 62, yd, 42, INKC[k], align="left")
    if k == "out":
        text(ctx, f"気温{p['Ta']:.0f}℃", cx, PY0 + 89, 46, RED)
        text(ctx, f"湿度{p['rh'] * 100:.0f}%・風{p['v']:.0f}m/秒", cx, PY0 + 133, 28, INK, bold=False)
    else:
        text(ctx, f"室温{p['Tr']:.0f}℃", cx, PY0 + 89, 46, INK)
        text(ctx, f"湿度{rh_now * 100:.0f}%・風{p['vr']:.1f}m/秒", cx, PY0 + 133, 28, INK, bold=False)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = tau_of(t)
    fo, fi = fs(t)
    ctx.push_group()
    draw_out(ctx, t, fo)
    draw_in(ctx, t, fi)
    done_o = t_of(s["t_out"]) if tau >= s["t_out"] else None
    done_i = t_of(s["t_in"]) if tau >= s["t_in"] else None
    draw_card(ctx, t, "out", fo, s["t_out"], done_o)
    draw_card(ctx, t, "in", fi, s["t_in"], done_i)
    draw_header(ctx, t, "out", 0)
    draw_header(ctx, t, "in", rh_in_at(tau))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, f"経過 {hm_(tau_of(t))}", 580, 640, 40, "yellow", a=a, tilt=-0.02)
    text(ctx, "早送り（残りの水が1割で「乾いた」）", 580, 724, 26, PENCIL, bold=False, alpha=a)


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
    win_in = (r["t_in"] < r["t_out"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_O), bgra(COL_I)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_in[:m]]
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
    win_in = r["t_in"][:m] < r["t_out"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("out", int(m - win_in.sum())), ("in", int(win_in.sum())))):
            y = 1192 + i * 58
            fill(ctx, hexrgb(COLS[k], a * lg))
            ctx.rectangle(200, y - 17, 34, 34)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(200, y - 17, 34, 34)
            ctx.stroke()
            text(ctx, f"{TAG[k]} {NAME[k]}が先に乾いた", 250, y, 34, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 915, y, 34, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            sh = shown()
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            lead = "部屋" if sh["gap_med"] < 0 else "外"
            lead_p = sh["p_out"] if sh["gap_med"] >= 0 else 1 - sh["p_out"]
            note.sticky(ctx, f"外が先は 約{pct_i(sh['p_out'])}。\n差は 真ん中で {hm_about(abs(sh['gap_med']))}", 580, 1342, 34, "pink",
                        fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_out"], sh["gap_med"])


def reason_text():
    sh = shown()
    k = answer_key()
    r = sh["med_out"] / sh["med_in"] if sh["med_out"] <= sh["med_in"] else sh["med_in"] / sh["med_out"]
    part = "約半分" if 0.4 <= r <= 0.6 else f"約{r * 100:.0f}%"
    if k == "out":
        return f"外は風が吹き、部屋は湿気がこもるから。\n乾くまでの時間は 外が部屋の{part}"
    if k == "in":
        return f"部屋はあたたかく、外は寒くて湿っているから。\n乾くまでの時間は 部屋が外の{part}"
    return "寒くても風のある外と、風のない あたたかい部屋は\n乾くまでの時間が ほぼ互角"


def fan_line():
    sh = shown()
    return f"部屋に風を当てると 差は{hm_about(abs(sh['gap_fan']))}に縮む"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    sh = shown()
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1218, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        note.sticky(ctx, reason_text(), 580, 1338, 30, "blue", a=c, tilt=0.012)
    if FAN_LINE and t >= T_ANS2 + 1.8:
        d = ease_out((t - T_ANS2 - 1.8) / 0.3)
        text(ctx, fan_line(), 560, 1428, 30, INK, alpha=d)


FAN_LINE = True


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
    """この回だけの冒頭。上: 問い2行（横幅いっぱい）・前提・三択（横1列）。その下に2つの物干し（0秒目から揺れて、水が減り始める）"""
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
        note.sticky(ctx, "あなたは、冬は\n外干し？部屋干し？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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
    wind = noise_band(t_end, 60, 3, 1.0)                  # 外の風（ひゅう）
    tt = np.arange(len(wind)) / SR
    env_ = (0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, wind * env_, 0.45)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    tg, te = t_of(s["t_out"]), t_of(s["t_in"])
    mx.add(tg, bell(784.0, 1.2), 0.45)
    mx.add(te, bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    checks = []
    # (1) 外の数値の足し算が、外は空気が変わらないので式で解ける答えと合う（最大の食い違い・割合）
    k = 400
    d1 = {kk: v[:k] for kk, v in p.items()}
    num, _ = run(d1, False)
    ana = analytic_out(d1)
    checks.append(("外の乾く時刻: 足し算 − 式（最大・割合）", float(np.max(np.abs(num / ana - 1))), 0.0, 0.01))
    # (2) 熱のつり合いの残り（最大・W/m²）
    Ta, qs, rho, hc, hm = env(d1, False)
    Ts = solve_Ts(Ta, hc, H_R, qs, hm, rho)
    resid = (hc + H_R) * (Ta - Ts) + qs - latent(Ts) * hm * (rho_sat(Ts) - rho)
    checks.append(("表面の温度の熱のつり合いの残り（最大・W/m²）", float(np.max(np.abs(resid))), 0.0, 1e-3))
    # (3) 風がとても強く日ざしが無いとき、表面の温度は湿球温度（20℃ 50% で約 13.7℃）に近づく
    checks.append(("湿球温度（20℃・50%）に近づく（℃）", tw_check(), 13.7, 0.4))
    # (4) 部屋の湿度が100%を超えない
    checks.append(("部屋の湿度の最大が 100% 未満", float(np.max(r["rhmax"]) < 1.0), 1.0, 0.0))
    # (5) 見本の履歴の終わり（乾く時刻）が、1万回の中のその回と一致する
    s = sample()
    checks.append(("見本の外の時刻（分）が1万回の値と同じ", s["chk"][0], s["t_out"], 1e-6))
    checks.append(("見本の部屋の時刻（分）が1万回の値と同じ", s["chk"][1], s["t_in"], 1e-6))
    # (6) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key = answer_by_rule(sh["p_out"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（外干し・部屋干し）",
                   float(LABELS.index(NAME["out"]) * 10 + LABELS.index(NAME["in"])),
                   float("ABC".index(TAG["out"]) * 10 + "ABC".index(TAG["in"])), 0.0))
    # (7) 見本は1万回の中の1回で、差が真ん中の値の近く
    checks.append(("見本の差（分）が真ん中の値の近く", s["gap"], sh["gap_med"], 0.08 * abs(sh["gap_med"])))
    # (8) 画面の回数が足して1万・全部乾いている
    checks.append(("先に乾いた回の合計", float(sh["n_out"] + sh["n_in"]), float(N_TRIAL), 0.0))
    checks.append(("乾かなかった回（48時間）", float(sh["n_unfinished"]), 0.0, 0.0))
    # (9) 同じ回の中で、部屋の風を強くすると部屋の時刻は早まる
    checks.append(("部屋に風を当てると 部屋の中央値は短くなる", float(sh["med_fan"] < sh["med_in"]), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  乾く {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"締め {T_Q:.1f}  見本 {s['i']}（外 {hm_(s['t_out'])} / 部屋 {hm_(s['t_in'])}）")
    print("  理由:", reason_text().replace("\n", " / "), "|", fan_line())
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.2, 5.8, 8.0, 10.0, T_FIN1 + 0.4, T_FIN2 - 0.6, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_ANS2 + 2.6, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
