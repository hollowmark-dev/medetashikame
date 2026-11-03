"""カーテンを閉めると、窓の結露は増える？減る？ 同じ部屋の窓2つ（カーテンなし／あり）で、夜から朝まで1万回。— 2026-10-26 作成（公開予定 11/03・45秒前後）

結露の量だけをくらべる（お金・電気代・健康・カビは入れない。画面にも概要欄にも書かない）。

モデル（窓1m² あたり・夜のあいだ条件は一定＝定常）
  結露の量 = h_m × (ρ_空気 − ρ_sat(Tg))  を 夜の時間（8〜10時間）ぶん足す         ρ は空気 1m³ に含まれる水蒸気の量（絶対湿度）
      h_m（物質移動係数）= h_c ÷ (ρ_空気 × c_p × Le^(2/3))     … 熱と水蒸気の伝わり方の類似（Chilton–Colburn）。Le = 0.85〜0.90、c_p = 1006 J/(kg·K)
      h_c（ガラスの内側の、空気の動きによる熱伝達）= 2.5〜4.0 W/(m²K)   … 仮定（室内側の表面熱伝達率 α = 8.1〜9.3 のうち、放射を除いた分の見当）
      水蒸気の飽和量: ρ_sat = 216.7 × e_s ÷ (T + 273.15) [g/m³]、e_s = 6.112 × exp(17.62 T/(243.12+T)) [hPa]（Magnus の式・WMO）
  ガラス内側の温度 Tg（一枚ガラス）:
      Tg = T空気 − (T空気 − T外) × U / α        U = 5.8 W/(m²K)（透明単板ガラス）、α = 室内側の表面熱伝達率 8.1〜9.3（中央 8.7）
      U … 板硝子協会の表を引用した 中小機構ページ https://j-net21.smrj.go.jp/development/energyeff/Q1225.html （透明単板 5.8・透明複層 2.9）
      α と 式 … 北海道立総合研究機構 https://www.hro.or.jp/upload/50471/1041204.pdf （α = 8.7（8.1〜9.3）、θin = Tin − (Tin − Tout) × U / α）
      例: 室内 20℃・外 0℃・U 5.8・α 8.7 → 約 6.7℃（計算。露点は 20℃・60% で 約 12℃ なので 結露する）
  カーテンなし: T空気 = 部屋の温度、ρ空気 = 部屋の水蒸気量。
  カーテンあり（部屋 → カーテン → すき間の空気 → ガラス）:
      すき間の空気は、カーテンの布を通ってくる熱 と、上下のすき間で部屋の空気と入れかわる熱 を受け取り、ガラスへ熱を渡す。
        熱: (1/R_c + ρ_a c_p q) × (T部屋 − T_c) = U × (T_c − T外)       → T_c（すき間の空気の温度）
        R_c（部屋の空気 → すき間の空気 の熱抵抗。カーテンの布と、部屋側の空気の膜をふくむ）= 0.1〜0.4 m²K/W   … 仮定（出典なし。
            確認できたのは 雨戸・シャッターの補正値 0.10、障子 0.18、海外の断熱カーテン試作 0.38〜0.65。ふつうのカーテンは目安 0.1〜0.2＝推定）
        q（すき間の空気が部屋と入れかわる量）= 0.0005〜0.004 m³/(s·m²窓)   … 仮定（出典なし。すそ・上のすき間 1〜2cm、風 0.1m/秒ほどの見当）
        水蒸気: q × (ρ部屋 − ρ_c) = h_m × (ρ_c − ρ_sat(Tg))            → ρ_c（すき間の空気の水蒸気量）。ガラスに着くのは h_m(ρ_c − ρ_sat(Tg))
        ρ_c は すき間の空気の飽和量 ρ_sat(T_c) を超えない（超えた分の「すき間の空気やカーテンの裏での結露」はガラスの量に入れない＝仮定）。
      Tg = T_c − (T_c − T外) × U / α  。カーテンがあるとガラスは冷える向きだが、ガラスに着く水蒸気は すき間の入れかわりしだい。
  入れていないもの: 結露するときの熱でガラスが少し温まる分、カーテン生地が水蒸気を通す分・吸う分、窓の上下の温度差、
      夜の外気温の変化、人の呼吸や調理で部屋の湿気が増える分（部屋の温度・湿度は一晩ずっと同じ）。
  公的機関の資料でも「カーテンを閉めると結露が増える」とは言い切れず、カーテンの断熱性能と換気量しだい、とされている
      → 建材試験センター https://www.gbrc.or.jp/assets/documents/gbrc/GBRC189_12.pdf , https://www.gbrc.or.jp/assets/documents/gbrc/GBRC189_28.pdf
  だから答えは計算どおり。「ほぼ同じ」「減る」になってもそのまま出す。
  幅（1回ごとにすべてでたらめ）: 外 −5〜8℃、部屋 16〜22℃・湿度 40〜65%、夜の長さ 8〜10時間、窓の面積 1.0〜2.0 m²、R_c・q・h_c・α・Le は上のとおり。

問い: 「カーテンを閉めると、/ 窓の結露は / 増える？減る？」（前提「冬の夜、同じ部屋の同じ窓2つ（一枚ガラス）」）
      選択肢（記号の並びは LABELS の順。正解の記号は C になるように並べる）: 増える ／ ほぼ同じ ／ 減る
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      「結露が出た回」（どちらかが 5 g/m² 以上）のうち、カーテンありのほうが朝までの結露が多かった割合 p と、
      量の比（あり ÷ なし。分子・分母に 5 g/m² を足して0割りを避ける）の中央値 r で、
      p ≥ 60% かつ r ≥ 1.2 なら「増える」、p ≤ 40% かつ r ≤ 0.83 なら「減る」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、カーテンのすそを床までぴったりにしたら？」（q を 0.1〜0.3 倍にして同じ1万回を再計算）。
締め: 「あなたの家の窓、カーテンの裏を見てみますか？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（並んで結露する2つの窓）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "kaaten-ketsuro"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261103
T_OUT, T_ROOM, RH_ROOM = (-5.0, 8.0), (16.0, 22.0), (0.40, 0.65)
HOURS, A_WIN = (8.0, 10.0), (1.0, 2.0)            # 夜の長さ（時間）、窓の面積（m²）
U_GLASS = 5.8                                     # 透明単板ガラス（W/m²K）
ALPHA_I = (8.1, 9.3)                              # 室内側の表面熱伝達率
HC_IN = (2.5, 4.0)                                # ガラス内側の対流の熱伝達（仮定）
LEWIS = (0.85, 0.90)
R_C = (0.1, 0.4)                                  # 部屋の空気 → すき間の空気 の熱抵抗（仮定）
Q_EX = (0.0005, 0.004)                            # すき間の空気の入れかわり m³/(s·m²)（仮定）
Q_TWIST = (0.1, 0.3)                              # ひねり: すそを床までぴったり → q がこの倍に
RHO_AIR, CP_AIR = 1.2, 1006.0
EPS_G = 5.0                                       # 「結露が出た」の目安 g/m²

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_P_HI, RULE_P_LO, RULE_R_HI, RULE_R_LO = 0.60, 0.40, 1.2, 0.83


def answer_by_rule(p_more, r_med):
    """p_more = 結露が出た回のうち、カーテンありのほうが多かった割合、r_med = 量の比（あり÷なし）の中央値。'more' / 'same' / 'less'"""
    if p_more >= RULE_P_HI and r_med >= RULE_R_HI:
        return "more"
    if p_more <= RULE_P_LO and r_med <= RULE_R_LO:
        return "less"
    return "same"


def es_hpa(T):
    return 6.112 * np.exp(17.62 * T / (243.12 + T))


def rho_sat(T):
    """飽和水蒸気量 kg/m³"""
    return 216.7 * es_hpa(T) / (np.asarray(T, float) + 273.15) * 1e-3


def dew_point(T, rh):
    """露点（Magnus の式の逆）"""
    e = rh * es_hpa(T)
    g = np.log(e / 6.112)
    return 243.12 * g / (17.62 - g)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    return dict(To=u(T_OUT), Tr=u(T_ROOM), rh=u(RH_ROOM), hours=u(HOURS), A=u(A_WIN), ai=u(ALPHA_I), hc=u(HC_IN),
                Le=u(LEWIS), Rc=u(R_C), q=u(Q_EX), qm=u(Q_TWIST))


def mass_coef(d):
    return d["hc"] / (RHO_AIR * CP_AIR * d["Le"] ** (2.0 / 3.0))


def no_curtain(d):
    """カーテンなし。返り値 dict: flux（ガラスに着く水 kg/m²/s）、Tg"""
    Tg = d["Tr"] - (d["Tr"] - d["To"]) * U_GLASS / d["ai"]
    rr = d["rh"] * rho_sat(d["Tr"])
    flux = mass_coef(d) * np.maximum(rr - rho_sat(Tg), 0.0)
    return dict(flux=flux, Tg=Tg)


def with_curtain(d, qmult=1.0, Rc=None, q=None):
    """カーテンあり。flux はガラスに着く水、tot は部屋からすき間の空気に入った水（flux ＋ すき間・カーテンの裏の分）"""
    qq = (d["q"] * qmult) if q is None else q
    Rcc = d["Rc"] if Rc is None else Rc
    G = 1.0 / Rcc + RHO_AIR * CP_AIR * qq
    Tc = (G * d["Tr"] + U_GLASS * d["To"]) / (G + U_GLASS)
    Tg = Tc - (Tc - d["To"]) * U_GLASS / d["ai"]
    rs = rho_sat(Tg)
    rr = d["rh"] * rho_sat(d["Tr"])
    hm = mass_coef(d)
    rc_free = np.where(rr > rs, (qq * rr + hm * rs) / (qq + hm), rr)     # ガラスが露点より暖かければ 結露せず、すき間の空気は部屋と同じ
    rc = np.minimum(rc_free, rho_sat(Tc))
    flux = hm * np.maximum(rc - rs, 0.0)
    tot = qq * np.maximum(rr - rc, 0.0)
    return dict(flux=flux, Tg=Tg, Tc=Tc, rc=rc, rc_free=rc_free, tot=tot, G=G, qq=qq)
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
    d = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
    n0 = no_curtain(d)
    c1 = with_curtain(d)
    c2 = with_curtain(d, qmult=d["qm"])
    sec = d["hours"] * 3600.0
    g = lambda f: f["flux"] * sec * 1000.0                      # g/m² ひと晩   # noqa: E731
    r = dict(p=d, n0=n0, c1=c1, c2=c2, g_n=g(n0), g_c=g(c1), g_t=g(c2), sec=sec,
             g_c_tot=c1["tot"] * sec * 1000.0, g_t_tot=c2["tot"] * sec * 1000.0)
    _RES["m"] = r
    return r


def stats(gn, gc):
    """結露が出た回（どちらかが EPS_G 以上）での p, r ほか"""
    cond = (gn >= EPS_G) | (gc >= EPS_G)
    ratio = (gc + EPS_G) / (gn + EPS_G)
    n_cond = int(cond.sum())
    more = cond & (gc > gn)
    less = cond & (gc < gn)
    p = float(more.sum() / max(n_cond, 1))
    return dict(cond=cond, n_cond=n_cond, n_more=int(more.sum()), n_less=int(less.sum()), n_none=int((~cond).sum()),
                p=p, r=float(np.median(ratio[cond])), ratio=ratio, more=more, less=less)


def shown():
    r = results()
    p = r["p"]
    s1 = stats(r["g_n"], r["g_c"])
    s2 = stats(r["g_n"], r["g_t"])
    s3 = stats(r["g_n"], r["g_c_tot"])
    cond = s1["cond"]
    q_hi = p["q"] > np.median(p["q"])
    out = dict(s1=s1, s2=s2, s3=s3,
               med_n=float(np.median(r["g_n"][cond])), med_c=float(np.median(r["g_c"][cond])),
               Tg_n=float(np.median(r["n0"]["Tg"])), Tg_c=float(np.median(r["c1"]["Tg"])),
               dTg=np.percentile(r["n0"]["Tg"] - r["c1"]["Tg"], [0, 50, 100]),
               p_qhi=stats(r["g_n"][q_hi], r["g_c"][q_hi]), p_qlo=stats(r["g_n"][~q_hi], r["g_c"][~q_hi]),
               p_n_any=float((r["g_n"] >= EPS_G).mean()), p_c_any=float((r["g_c"] >= EPS_G).mean()),
               p_clamped=float((r["c1"]["rc_free"] > rho_sat(r["c1"]["Tc"])).mean()))
    return out


def report():
    sh = shown()
    s1, s2, s3 = sh["s1"], sh["s2"], sh["s3"]
    print(f"結露が出た回 {s1['n_cond']}回 / 出なかった {s1['n_none']}回（どちらも 5g/m² 未満）  なしで出る {sh['p_n_any']:.3f} ありで出る {sh['p_c_any']:.3f}")
    print(f"  あり が多い {s1['n_more']}回 / なし が多い {s1['n_less']}回  p = {s1['p']:.4f}  r(中央値) = {s1['r']:.3f}")
    print(f"  答え {answer_by_rule(s1['p'], s1['r'])}")
    print(f"  結露が出た回の 量の中央値 なし {sh['med_n']:.0f} g/m² / あり {sh['med_c']:.0f} g/m²   ガラス温度の中央値 なし {sh['Tg_n']:.1f}℃ / あり {sh['Tg_c']:.1f}℃"
          f"（差 最小/中央/最大 {np.round(sh['dTg'], 2)}）")
    print(f"  ひねり（すそぴったり）: p = {s2['p']:.4f}  r = {s2['r']:.3f}  あり多 {s2['n_more']} / なし多 {s2['n_less']} / 出ず {s2['n_none']}  → {answer_by_rule(s2['p'], s2['r'])}")
    print(f"  [感度] すき間やカーテンの裏の結露も数えると: p = {s3['p']:.4f} r = {s3['r']:.3f} → {answer_by_rule(s3['p'], s3['r'])}"
          f"   （すき間の空気が飽和に頭打ちになった回 {sh['p_clamped']:.3f}）")
    print(f"  [感度] q が大きい半分: p = {sh['p_qhi']['p']:.3f} r = {sh['p_qhi']['r']:.3f} / 小さい半分: p = {sh['p_qlo']['p']:.3f} r = {sh['p_qlo']['r']:.3f}")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで結露する2つの窓）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 結露が出た回で、どちらの量も「出た回の中央値」の近く（0.6〜1.5倍）、量の比が全体の中央値 r の近く（±6%）、外の気温が -3〜4℃（冬の夜らしい絵）。
    その中で、比と量が中央値にいちばん近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    s1 = sh["s1"]
    gn, gc = r["g_n"], r["g_c"]
    ratio = (gc + EPS_G) / (gn + EPS_G)
    ok = (s1["cond"] & (gn >= 0.6 * sh["med_n"]) & (gn <= 1.5 * sh["med_n"]) & (gc >= 0.6 * sh["med_c"]) & (gc <= 1.5 * sh["med_c"])
          & (np.abs(ratio / s1["r"] - 1) < 0.06) & (p["To"] >= -3.0) & (p["To"] <= 4.0))
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    score = np.abs(ratio[cand] / s1["r"] - 1) + 0.5 * np.abs(gn[cand] / sh["med_n"] - 1) + 0.5 * np.abs(gc[cand] / sh["med_c"] - 1)
    i = int(cand[np.argmin(score)])
    q = {k: float(v[i]) for k, v in p.items()}
    A = q["A"]
    _SAMPLE = dict(i=i, p=q, g_n=float(gn[i]), g_c=float(gc[i]), m_n=float(gn[i]) * A, m_c=float(gc[i]) * A, ratio=float(ratio[i]),
                   Tg_n=float(r["n0"]["Tg"][i]), Tg_c=float(r["c1"]["Tg"][i]), Tc=float(r["c1"]["Tc"][i]), hours=q["hours"])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    p = s["p"]
    print("見本", s["i"], "外", round(p["To"], 1), "℃ 部屋", round(p["Tr"], 1), "℃", round(p["rh"] * 100), "% 夜", round(p["hours"], 1), "時間 窓", round(p["A"], 2), "m²",
          "| ガラス なし", round(s["Tg_n"], 1), "あり", round(s["Tg_c"], 1), "(すき間の空気", round(s["Tc"], 1), ") | 量 なし", round(s["g_n"]), "あり", round(s["g_c"]),
          "g/m² → ", round(s["m_n"]), "/", round(s["m_c"]), "mL 比", round(s["ratio"], 3), "R_c", round(p["Rc"], 2), "q", round(p["q"], 4))
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
note.DATE = "11.3"                                # 日付欄（公開予定日）

COL_N, INK_N = "#8fbbe8", "#2f63a8"                # カーテンなし（水色）
COL_C, INK_C = "#f4ad6a", "#b8601a"                # カーテンあり（だいだい）
COL_0 = "#d3d1c8"                                  # どちらも出なかった（灰）
WATER = "#58a8e4"
CURT, CURT_D, CURT_L = "#f3a9bb", "#d4809a", "#fbd3dd"

# 並びと正解は ここ（と comment.txt）だけ。答えは「ほぼ同じ」なので 正解が C の位置になるよう 並べた。
# 答えが変わったら LABELS・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["増える", "減る", "ほぼ同じ"]
CORRECT = 2                                        # answer_by_rule の結果の位置（0始まり。2 = C）
KEY_LABEL = {"more": "増える", "same": "ほぼ同じ", "less": "減る"}
CATS = ("more", "less", "none")                    # マス目の分け方（あり が多い / なし が多い / どちらも出ない）
CAT_COL = {"more": COL_C, "less": COL_N, "none": COL_0}

BIG_Q = ["カーテンを閉めると、窓の結露は", "増える？減る？"]                # 定位置（上）の2行
BIG_Q3 = ["カーテンを閉めると、", "窓の結露は", "増える？減る？"]         # 1コマ目の3行（同じ大きさ）
DETAIL = "冬の夜、同じ部屋の同じ窓2つ（一枚ガラス）"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 16.0                                    # T_GO から朝まで
R0 = 0.9                                           # 冒頭の進み（シミュの分／動画の秒）
CURT_T0, CURT_T1 = 0.05, 1.0                       # カーテンが閉まる時刻
FLAP_T0, FLAP_T1 = 1.3, 2.2                        # すそをめくる時刻

# 画面の置き場所
PX0, PX1, PY0, PY1 = 80.0, 1020.0, 830.0, 1480.0
WCX = {"n": 280.0, "c": 820.0}                     # 窓の中心 x
WHW, WY0, WY1 = 110.0, 900.0, 1220.0               # 窓の半幅・上・下
GI = 10.0                                          # ガラスの内側の余白
CARD_Y0, CARD_Y1 = 1256.0, 1446.0
BED_X = 550.0
CD_X, CD_Y = 550.0, 1290.0


def setup():
    global TL, RX, T_FIN, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_TW_G, T_TW_RES, T_Q, DURATION, CUP_ML
    s = sample()
    dmin = s["hours"] * 60.0
    T_FIN = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 70, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 600.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN, ts, tau)) > dmin:
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
    T_TW = T_ANS2 + 3.2                            # ひねり（問い）
    T_TW_G = T_TW + 0.8                            # ひねりのマス目が埋まり始める
    T_TW_RES = T_TW_G + 2.4                        # ひねりの数字
    T_Q = T_TW_RES + 3.4
    DURATION = T_Q + 4.4
    CUP_ML = max(50.0, math.ceil(1.2 * max(s["m_n"], s["m_c"]) / 50.0) * 50.0)


def tau_of(t):
    """その時刻の「夜の経過（分）」"""
    return min(float(np.interp(t, TL["t"], TL["tau"])), sample()["hours"] * 60.0)      # 朝（夜の終わり）で止める


def frac_night(t):
    return clamp01(tau_of(t) / (sample()["hours"] * 60.0))


def amount_ml(t, k):
    s = sample()
    return (s["m_n"] if k == "n" else s["m_c"]) * frac_night(t)


def light_at(t):
    """0 = 夜 → 1 = 朝（夜の終わりの1.8時間前から明るくなり始める）"""
    h = tau_of(t) / 60.0
    return clamp01((h - (sample()["hours"] - 1.8)) / 1.5)


def clock_str(t):
    tau = tau_of(t)
    hh = int(22 + tau // 60) % 24
    mm = int(tau % 60)
    lab = "朝" if light_at(t) > 0.05 else "夜"
    return f"{lab} {hh:02d}:{mm:02d}"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def lerp_col(c0, c1, u):
    a = hexrgb(c0) if isinstance(c0, str) else c0
    b = hexrgb(c1) if isinstance(c1, str) else c1
    return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))


def clip_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    ctx.clip()


def border_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    _stroke(ctx, 3.5, INK, 0.75)


ZOOM0, ZOOM_T = 1.25, 1.25


def zoom_art(ctx, t):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(BED_X, 1100.0)
    ctx.scale(z, z)
    ctx.translate(-BED_X, -1100.0)


# ---------- 空 ----------
DUSK_T, DUSK_B = "#5a6ea8", "#e6b69d"
NIGHT_T, NIGHT_B = "#141d38", "#2d3f6e"
DAY_T, DAY_B = "#a8d2ee", "#f1e6cf"
_STARS = np.random.default_rng(5).random((16, 3))


def night_amt(t):
    return ease(t / 1.3) * (1 - light_at(t))


def draw_sky(ctx, x0, y0, w, h, t):
    u = ease(t / 1.3)
    L = light_at(t)
    top = lerp_col(lerp_col(DUSK_T, NIGHT_T, u), DAY_T, L)
    bot = lerp_col(lerp_col(DUSK_B, NIGHT_B, u), DAY_B, L)
    g = cairo.LinearGradient(0, y0, 0, y0 + h)
    g.add_color_stop_rgb(0, *top)
    g.add_color_stop_rgb(1, *bot)
    ctx.set_source(g)
    ctx.rectangle(x0, y0, w, h)
    ctx.fill()
    sa = u * (1 - L)
    if sa > 0.02:
        for k, (sx, sy, ph) in enumerate(_STARS):
            tw = 0.6 + 0.4 * math.sin(t * 2.2 + ph * 6)
            ctx.set_source_rgba(1, 0.97, 0.8, 0.9 * sa * tw)
            ctx.arc(x0 + 10 + sx * (w - 20), y0 + 8 + sy * h * 0.55, 1.8 + 1.2 * ph, 0, 2 * math.pi)
            ctx.fill()
        ctx.set_source_rgba(1, 0.96, 0.7, 0.95 * sa)               # 月
        ctx.arc(x0 + w * 0.72, y0 + 46, 17, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*top, 0.95 * sa)
        ctx.arc(x0 + w * 0.72 + 8, y0 + 41, 14, 0, 2 * math.pi)
        ctx.fill()
    # 向かいの家なみ（シルエット）
    hc = lerp_col(lerp_col("#27355c", "#1b2644", u), "#9db4c8", L)
    ctx.set_source_rgba(*hc, 1)
    for (bx, bw, bh) in ((0.0, 0.30, 60), (0.26, 0.26, 92), (0.50, 0.30, 70), (0.76, 0.26, 52)):
        ctx.rectangle(x0 + bx * w, y0 + h - bh, bw * w, bh)
        ctx.fill()
    wl = (1 - L) * u * 0.9                                             # 向かいの窓のあかり（夜）
    ctx.set_source_rgba(1, 0.88, 0.5, wl)
    for (bx, by) in ((0.33, 70), (0.60, 52), (0.44, 70), (0.83, 40)):
        ctx.rectangle(x0 + bx * w, y0 + h - by, 10, 12)
        ctx.fill()


# ---------- 結露の粒 ----------

def _make_beads(seed, n=170):
    rng = np.random.default_rng(seed)
    yf = 1 - rng.random(n) ** 1.5                                      # 下のほうに多い（下ほど冷える）
    return dict(x=0.04 + 0.92 * rng.random(n), y=yf, thr=0.02 + 0.9 * rng.random(n) ** 0.9,
                r=3.0 + 6.5 * rng.random(n) ** 1.5 + 3.0 * yf)


BEADS = {"n": _make_beads(31), "c": _make_beads(32)}
_rs = np.random.default_rng(77)
STREAKS = {k: dict(x=0.12 + 0.76 * _rs.random(7), y0=0.10 + 0.40 * _rs.random(7), thr=0.35 + 0.55 * _rs.random(7),
                   ln=0.18 + 0.30 * _rs.random(7)) for k in ("n", "c")}


def draw_condensation(ctx, gx, gy, gw, gh, frac, t, k):
    if frac <= 0.003:
        return
    # 白いくもり（下ほど濃い）
    a = frac ** 0.75
    g = cairo.LinearGradient(0, gy, 0, gy + gh)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.08 * a)
    g.add_color_stop_rgba(1, 0.92, 0.97, 1, 0.50 * a)
    ctx.set_source(g)
    ctx.rectangle(gx, gy, gw, gh)
    ctx.fill()
    st = STREAKS[k]
    for x, y0, thr, ln in zip(st["x"], st["y0"], st["thr"], st["ln"]):
        s = clamp01((frac - thr) / 0.25)
        if s <= 0:
            continue
        xx, ya = gx + x * gw, gy + y0 * gh
        yb = ya + ln * gh * ease(s)
        ctx.move_to(xx, ya)
        ctx.line_to(xx, yb)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        _stroke(ctx, 4.5, "#b9d9f2", 0.85 * min(1.0, s * 2))
        ctx.set_source_rgba(*hexrgb("#8cc0e6", 0.9))
        ctx.arc(xx, yb, 5.5, 0, 2 * math.pi)
        ctx.fill()
    b = BEADS[k]
    for x, y, th, rr in zip(b["x"], b["y"], b["thr"], b["r"]):
        s = clamp01((frac - th) / 0.12)
        if s <= 0:
            continue
        r_ = rr * (0.35 + 0.65 * ease(s))
        cx, cy = gx + x * gw, gy + y * gh
        ctx.set_source_rgba(0.86, 0.94, 1.0, 0.62)
        ctx.arc(cx, cy, r_, 0, 2 * math.pi)
        ctx.fill_preserve()
        _stroke(ctx, 1.5, "#5d93c4", 0.8)
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.arc(cx - r_ * 0.35, cy - r_ * 0.35, max(1.2, r_ * 0.28), 0, 2 * math.pi)
        ctx.fill()


# ---------- 窓・カーテン ----------

def _reflect(a, c, b):
    dx, dy = c[0] - a[0], c[1] - a[1]
    tt = ((b[0] - a[0]) * dx + (b[1] - a[1]) * dy) / (dx * dx + dy * dy)
    fx, fy = a[0] + tt * dx, a[1] + tt * dy
    return 2 * fx - b[0], 2 * fy - b[1]


def curtain_close(t):
    return 0.24 + 0.76 * ease((t - CURT_T0) / (CURT_T1 - CURT_T0))


def flap_prog(t):
    return ease((t - FLAP_T0) / (FLAP_T1 - FLAP_T0))


def draw_curtain(ctx, wx, t):
    c = curtain_close(t)
    pf = flap_prog(t)
    L, R = wx - 124.0, wx + 124.0
    top, bot = 892.0, 1252.0
    sw = 2.2 * math.sin(2 * math.pi * 0.3 * t) + 1.0 * math.sin(2 * math.pi * 0.8 * t + 1)
    # めくる三角
    A = (L, bot - 320.0 * pf)
    Cc = (L + 200.0 * pf, bot)
    B = (L, bot)
    ctx.save()
    if pf > 0.01:
        ctx.new_path()
        ctx.rectangle(L - 6, top - 4, R - L + 12, bot - top + 12)
        ctx.move_to(*A)
        ctx.line_to(*Cc)
        ctx.line_to(*B)
        ctx.close_path()
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.clip()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    half = (R - L) / 2
    for (xa, xb) in ((L, L + half * c), (R - half * c, R)):
        ctx.rectangle(xa, top, xb - xa, bot - top)
        ctx.set_source_rgba(*hexrgb(CURT, 0.98))
        ctx.fill()
        n = max(2, int((xb - xa) / (9 + 7 * (1 - c))))
        for i in range(1, n):
            xx = xa + (xb - xa) * i / n
            amp = 2.0 + 5.0 * (1 - c)
            ctx.move_to(xx, top)
            for j in range(1, 13):
                u = j / 12
                ctx.line_to(xx + amp * math.sin(u * 5 + i) + sw * u * u * 0.5, top + u * (bot - top))
            _stroke(ctx, 2.2, CURT_D, 0.55)
        ctx.rectangle(xa, top, xb - xa, bot - top)
        _stroke(ctx, 3.0, INK, 0.7)
    if c > 0.97:                                                       # 合わせ目
        ctx.move_to(wx, top)
        ctx.line_to(wx, bot)
        _stroke(ctx, 2.5, CURT_D, 0.8)
    ctx.restore()
    if pf > 0.01:                                                      # めくれた角（折り返し）
        D = _reflect(A, Cc, B)
        dx_, dy_ = Cc[0] - A[0], Cc[1] - A[1]                           # 折り返しの先は 少し手前で止める（まるまった角）
        tt_ = ((B[0] - A[0]) * dx_ + (B[1] - A[1]) * dy_) / (dx_ * dx_ + dy_ * dy_)
        F = (A[0] + tt_ * dx_, A[1] + tt_ * dy_)
        D = (F[0] + 0.42 * (D[0] - F[0]), F[1] + 0.42 * (D[1] - F[1]))
        ctx.move_to(*A)
        ctx.line_to(*Cc)
        ctx.line_to(*D)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(CURT_L, 1))
        ctx.fill_preserve()
        _stroke(ctx, 3.0, INK, 0.7)
        ctx.move_to(*A)
        ctx.line_to(*Cc)
        _stroke(ctx, 4.5, CURT_D, 0.9)
    # レール
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(wx - 138, 887)
    ctx.line_to(wx + 138, 887)
    _stroke(ctx, 9, INK, 0.85)
    ctx.move_to(wx - 138, 887)
    ctx.line_to(wx + 138, 887)
    _stroke(ctx, 5, "#b98f62", 1.0)


def draw_window(ctx, t, k):
    wx = WCX[k]
    x0, y0, x1, y1 = wx - WHW, WY0, wx + WHW, WY1
    core.rrect(ctx, x0, y0, x1 - x0, y1 - y0, 8)                       # 枠
    fill(ctx, hexrgb("#f7f1e6"))
    ctx.fill_preserve()
    _stroke(ctx, 5, INK, 0.9)
    gx, gy, gw, gh = x0 + GI, y0 + GI, x1 - x0 - 2 * GI, y1 - y0 - 2 * GI
    ctx.save()
    ctx.rectangle(gx, gy, gw, gh)
    ctx.clip()
    draw_sky(ctx, gx, gy, gw, gh, t)
    s = sample()
    mref = 1.15 * max(s["m_n"], s["m_c"])
    frac = clamp01(amount_ml(t, k) / mref)
    draw_condensation(ctx, gx, gy, gw, gh, frac, t, k)
    ctx.set_source_rgba(1, 1, 1, 0.18)                                 # ガラスの照り返し
    ctx.move_to(gx + 20, gy)
    ctx.line_to(gx + 70, gy)
    ctx.line_to(gx + 10, gy + 120)
    ctx.line_to(gx, gy + 120)
    ctx.line_to(gx, gy + 70)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    ctx.rectangle(gx, gy, gw, gh)
    _stroke(ctx, 2.5, INK, 0.6)
    # 窓台と、たまった水
    ctx.rectangle(wx - 126, y1, 252, 20)
    fill(ctx, hexrgb("#e7d7b9"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.8)
    if frac > 0.04:
        w_ = 200 * min(1.0, frac)
        ctx.set_source_rgba(*hexrgb(WATER, 0.85))
        core.rrect(ctx, wx - w_ / 2, y1 + 3, w_, 8, 4)
        ctx.fill()
    if k == "c":
        draw_curtain(ctx, wx, t)


# ---------- 部屋・ベッド・人 ----------

def draw_room(ctx, t):
    na = night_amt(t)
    fill(ctx, hexrgb("#f4ead7"))
    ctx.rectangle(PX0, PY0, PX1 - PX0, PY1 - PY0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#dcc9a4", 0.9))                       # 壁のしま
    for x in range(int(PX0) - 40, int(PX1) + 40, 34):
        ctx.rectangle(x, PY0 - 40, 14, 1350 - PY0 + 40)
        ctx.fill()
    fill(ctx, hexrgb("#d9b98a"))                                       # 床
    ctx.rectangle(PX0, 1350, PX1 - PX0, PY1 - 1350)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#b8946a", 0.7))
    ctx.set_line_width(2.5)
    for i in range(0, 16):
        ctx.move_to(PX0 + i * 70 - 10, 1360)
        ctx.line_to(PX0 + i * 70 - 50, PY1)
    ctx.stroke()
    ctx.rectangle(PX0, 1340, PX1 - PX0, 12)
    ctx.set_source_rgba(*hexrgb("#f7f1e6", 1))
    ctx.fill()
    ctx.set_source_rgba(0.12, 0.17, 0.38, 0.34 * na)                   # 夜は少し暗く
    ctx.rectangle(PX0, PY0, PX1 - PX0, PY1 - PY0)
    ctx.fill()


def draw_person(ctx, t):
    L = light_at(t)
    breath = 1 + 0.012 * math.sin(2 * math.pi * 0.35 * t)
    cx = BED_X
    # ベッドのあたま
    core.rrect(ctx, cx - 140, 925, 280, 215, 18)
    fill(ctx, hexrgb("#b98f62"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.8)
    core.rrect(ctx, cx - 112, 975, 224, 124, 42)                       # まくら
    fill(ctx, hexrgb("#fffdf8"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.7)
    hx, hy, hr = cx, 1032.0, 86.0                                      # あたま
    ctx.arc(hx, hy, hr, 0, 2 * math.pi)
    fill(ctx, hexrgb("#ffe2c9"))
    ctx.fill_preserve()
    _stroke(ctx, 4.0, INK, 0.9)
    ctx.new_path()                                                     # かみ
    ctx.arc(hx, hy, hr + 3, math.pi * 1.02, math.pi * 1.98)
    ctx.curve_to(hx + 70, hy - 52, hx + 40, hy - 40, hx + 22, hy - 44)
    ctx.curve_to(hx + 10, hy - 30, hx - 20, hy - 48, hx - 34, hy - 42)
    ctx.curve_to(hx - 48, hy - 38, hx - 66, hy - 46, hx - hr - 3, hy - 2)
    ctx.close_path()
    fill(ctx, hexrgb("#4d3526"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    ey = hy + 14
    for sx in (-1, 1):
        ex = hx + sx * 33
        if L < 0.55:                                                   # ねている（とじた目）
            ctx.new_path()
            ctx.arc(ex, ey - 6, 11, 0.15 * math.pi, 0.85 * math.pi)
            _stroke(ctx, 4.5, INK, 0.95)
        else:                                                          # あさ（ひらいた目）
            ctx.arc(ex, ey, 8, 0, 2 * math.pi)
            fill(ctx, hexrgb(INK))
            ctx.fill()
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.arc(ex - 2.5, ey - 3, 2.8, 0, 2 * math.pi)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb("#ff9f9a", 0.55))
        ctx.arc(hx + sx * 56, ey + 24, 12, 0, 2 * math.pi)
        ctx.fill()
    my = hy + 52
    if L < 0.55:
        ctx.set_source_rgba(*hexrgb("#c8665e", 0.9))
        ctx.save()
        ctx.translate(hx, my)
        ctx.scale(1, 0.8 + 0.4 * (0.5 + 0.5 * math.sin(2 * math.pi * 0.35 * t)))
        ctx.arc(0, 0, 6, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    else:
        ctx.new_path()
        ctx.arc(hx, my - 8, 12, 0.15 * math.pi, 0.85 * math.pi)
        _stroke(ctx, 4, "#c8665e", 0.95)
    # ふとん
    ctx.save()
    ctx.translate(cx, 1118)
    ctx.scale(1, breath)
    ctx.translate(-cx, -1118)
    ctx.new_path()
    ctx.move_to(cx - 140, 1114)
    for i in range(0, 29):
        u = i / 28
        ctx.line_to(cx - 140 + 280 * u, 1112 + 7 * math.sin(u * 9 + 0.6))
    ctx.line_to(cx + 140, 1338)
    ctx.line_to(cx - 140, 1338)
    ctx.close_path()
    fill(ctx, hexrgb("#79b6cc"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.8)
    ctx.set_source_rgba(1, 1, 1, 0.38)
    for yy in (1170, 1228, 1286):
        ctx.move_to(cx - 138, yy)
        for i in range(1, 29):
            u = i / 28
            ctx.line_to(cx - 138 + 276 * u, yy + 5 * math.sin(u * 8 + yy))
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.restore()
    core.rrect(ctx, cx - 148, 1334, 296, 22, 8)                        # ベッドの足もと
    fill(ctx, hexrgb("#b98f62"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.8)


def draw_zzz(ctx, t):
    L = light_at(t)
    a = (1 - L) * ease(t / 1.0)
    if a <= 0.02:
        return
    for i, (dx, dy, sz) in enumerate(((-70, -118, 30), (-15, -143, 36), (45, -168, 42))):
        ph = (t * 0.6 + i * 0.28) % 1.0
        text(ctx, "Z" if i else "z", BED_X + dx - 4 * ph, 1030 + dy - 10 * ph, sz, INK_N, alpha=a * (0.5 + 0.5 * math.sin(ph * math.pi)))


# ---------- メーター（コップ） ----------

def cup_path(ctx, cx, top, w1, w2, h):
    ctx.new_path()
    ctx.move_to(cx - w1 / 2, top)
    ctx.line_to(cx + w1 / 2, top)
    ctx.line_to(cx + w2 / 2, top + h)
    ctx.line_to(cx - w2 / 2, top + h)
    ctx.close_path()


def draw_cup(ctx, cx, top, f, t):
    w1, w2, h = 76.0, 56.0, 100.0
    ctx.save()
    cup_path(ctx, cx, top, w1, w2, h)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    ctx.clip()
    y = top + h - clamp01(f) * h
    ctx.set_source_rgba(*hexrgb(WATER, 0.95))
    ctx.move_to(cx - w1, top + h + 4)
    for i in range(21):
        x = cx - w1 + i * (2 * w1) / 20
        ctx.line_to(x, y + 2.2 * math.sin(x / 9 + t * 5))
    ctx.line_to(cx + w1, top + h + 4)
    ctx.close_path()
    ctx.fill()
    ctx.restore()
    cup_path(ctx, cx, top, w1, w2, h)
    _stroke(ctx, 4.5, INK, 0.9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for u in (1 / 3, 2 / 3):                                           # 目盛り
        yy = top + h - u * h
        xw = (w2 + (w1 - w2) * (h - (top + h - yy)) / h) / 2
        ctx.move_to(cx - xw, yy)
        ctx.line_to(cx - xw + 12, yy)
        _stroke(ctx, 2.5, INK, 0.6)


def draw_card(ctx, t, k):
    wx = WCX[k]
    core.rrect(ctx, wx - WHW - 4, CARD_Y0, 2 * WHW + 8, CARD_Y1 - CARD_Y0, 18)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    s = sample()
    m = amount_ml(t, k)
    draw_cup(ctx, wx - 58, CARD_Y0 + 14, m / CUP_ML, t)
    ink = INK_N if k == "n" else INK_C
    text(ctx, "たまった水", wx + 44, CARD_Y0 + 40, 24, PENCIL, bold=False)
    text(ctx, f"{int(round(m))}mL", wx + 44, CARD_Y0 + 84, 38, ink)
    Tg = s["Tg_n"] if k == "n" else s["Tg_c"]
    text(ctx, f"ガラス {Tg:.1f}℃", wx, CARD_Y0 + 158, 28, ink, bold=False)
    if frac_night(t) >= 0.999 and t >= T_FIN:
        u = clamp01((t - T_FIN) / 0.35)
        note.pen_circle(ctx, wx + 44, CARD_Y0 + 84, 70, 30, RED, seed=70 + (k == "c"), width=4.5, progress=u)


def draw_label(ctx, k):
    wx = WCX[k]
    lab = "カーテンなし" if k == "n" else "カーテンを閉める"
    w = core.text_width(lab, 36) + 30
    core.rrect(ctx, wx - w / 2, 838, w, 46, 12)                        # 札（レールや動く絵と重ならないように）
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    text(ctx, lab, wx, 862, 36, INK_N if k == "n" else INK_C)


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
    ctx.save()
    clip_panel(ctx)
    ctx.save()
    zoom_art(ctx, t)
    draw_room(ctx, t)
    draw_window(ctx, t, "n")
    draw_window(ctx, t, "c")
    draw_person(ctx, t)
    ctx.restore()
    draw_zzz(ctx, t)
    ctx.restore()
    border_panel(ctx)
    for k in ("n", "c"):
        draw_label(ctx, k)
        draw_card(ctx, t, k)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def caption_text():
    p = sample()["p"]
    return f"たとえば、この1回では　外 {p['To']:.0f}℃・室温 {p['Tr']:.0f}℃・湿度 {p['rh'] * 100:.0f}%"


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, clock_str(t), 580, 640, 40, "yellow", a=a, tilt=-0.02)
    cap = caption_text()
    sz = 30
    while core.text_width(cap, sz) > 860:
        sz -= 1
    text(ctx, cap, 560, 724, sz, PENCIL, bold=False, alpha=a)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 5
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}


def cat_array(s):
    """試行ごとの分類 0 = ありが多い / 1 = なしが多い / 2 = どちらも出ない（量が同じ回は なしが多い側にも入れない＝ 2）"""
    c = np.full(N_TRIAL, 2, int)
    c[s["more"]] = 0
    c[s["less"]] = 1
    return c


def grid_surface(n, n2):
    """先頭 n2 マスはひねり（すそぴったり）の分類、それ以降は ふつうの分類"""
    key = (int(n) // G_COLS, int(n2) // G_COLS)
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 4:
        _GRID.clear()
    sh = shown()
    c1, c2 = cat_array(sh["s1"]), cat_array(sh["s2"])
    pal = np.array([bgra(CAT_COL[c]) for c in CATS], np.uint8)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    flat = cols.reshape(-1, 4)
    m = min(N_TRIAL, key[0] * G_COLS)
    m2 = min(N_TRIAL, key[1] * G_COLS)
    flat[:m] = pal[c1[:m]]
    flat[:m2] = pal[c2[:m2]]
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


def x_(v, nd=2):
    return f"{v:.{nd}f}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    n2 = N_TRIAL * clamp01((t - T_TW_G) / 1.4) if t >= T_TW_G else 0
    surf, _ = grid_surface(n, n2)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    if t < T_TW:
        text(ctx, f"{fmt(n)} / 10,000回　1マス＝1回", 580, 616, 32, INK, alpha=a)
    else:
        text(ctx, f"すそぴったり　{fmt(max(n2, 0))} / 10,000回", 580, 616, 32, INK, alpha=a)
    c1 = cat_array(sh["s1"])
    m = (int(n) // G_COLS) * G_COLS
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0 and t < T_TW:
        for i, cat in enumerate(CATS):
            y = 1105 + i * 46
            cnt = int((c1[:m] == i).sum())
            fill(ctx, hexrgb(CAT_COL[cat], a * lg))
            ctx.rectangle(160, y - 15, 30, 30)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(160, y - 15, 30, 30)
            ctx.stroke()
            lab = {"more": "ありのほうが多かった", "less": "なしのほうが多かった", "none": "どちらも出なかった"}[cat]
            text(ctx, lab, 206, y, 32, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 915, y, 32, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            s1 = sh["s1"]
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            note.sticky(ctx, f"この置き方なら、出た回のうち\nありが多いのは 約{pct_i(s1['p'])}\n量は 中央値で なしの 約{x_(s1['r'])}倍", 540, 1335, 34,
                        "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    s1 = shown()["s1"]
    return answer_by_rule(s1["p"], s1["r"])


def reason_text():
    sh = shown()
    k = answer_key()
    head = f"この置き方なら、\nガラスは中央値で {sh['Tg_n']:.1f}→{sh['Tg_c']:.1f}℃に冷える\n"
    if k == "same":
        return head + "でも すき間に入る湿気が減って 量は互角"
    if k == "more":
        return head + "冷えたガラスに すき間の湿気が着いて 量が増える"
    return head + "でも すき間に入る湿気が減って 量が減る"


def twist_text():
    s2 = shown()["s2"]
    return f"この置き方なら、出た回のうち\nありが多いのは 約{pct_i(s2['p'])}\n量は 中央値で なしの 約{x_(s2['r'])}倍"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3) * (1 - ease((t - T_TW) / 0.3))
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1140, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3) * (1 - ease((t - T_TW) / 0.3))
        note.sticky(ctx, reason_text(), 540, 1335, 34, "blue", a=c, tilt=0.012)
    if t >= T_TW:                                                      # ひねり
        d = ease_out((t - T_TW) / 0.3)
        note.sticky(ctx, "では、カーテンのすそを\n床までぴったりにしたら？", 580, 1140, 38, "yellow", a=d, tilt=-0.02)
    if t >= T_TW_RES:
        e = ease_out((t - T_TW_RES) / 0.3)
        note.sticky(ctx, twist_text(), 540, 1335, 34, "pink", fg=RED, a=e, tilt=0.012)


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


def big3_size(max_w=860.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（同じ大きさ・横幅いっぱい）・前提・三択（横1列）。その下に2つの窓（0秒目から夜になり、カーテンが閉まる）"""
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
        sz = 47.0
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
        note.sticky(ctx, "あなたの家の窓、\nカーテンの裏を見てみますか？", 580, 860, 50, "yellow", a=q, tilt=-0.02)
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

def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)                          # カーテンが閉まる
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    rng = np.random.default_rng(9)
    for k, m_end in (("n", s["m_n"]), ("c", s["m_c"])):     # しずくの音（水が たまるごと）
        for lv in np.arange(15.0, m_end, 15.0):
            tt = float(np.interp(lv / max(m_end, 1e-9), TL["tau"] / (s["hours"] * 60.0), TL["t"]))
            if T_GO <= tt <= T_FIN:
                mx.add(tt, blip(1500 + 600 * rng.random() + (200 if k == "c" else 0), 0.04), 0.10)
    mx.add(T_FIN - 0.4, bell(784.0, 1.4), 0.45)             # 朝
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                     # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, blip(659.3, 0.14), 0.3)                    # ひねり
    mx.add(T_TW_G - 0.3, riser(0.5), 0.35)
    mx.add(T_TW_RES, blip(784.0, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    s1, s2 = sh["s1"], sh["s2"]
    checks = []
    one = lambda **kw: {k: np.array([v], float) for k, v in kw.items()}   # noqa: E731
    # (1) 出典の数値例: 室内 20℃・外 0℃・U 5.8・α 8.7 → ガラスの内側 約 6.7℃（北海道立総合研究機構の式）、露点 20℃・60% → 約 12℃（Magnus の式）
    d0 = one(Tr=20.0, To=0.0, ai=8.7, rh=0.6, hc=3.0, Le=0.875)
    checks.append(("ガラス内側の温度（20℃・外0℃・α8.7）", float(no_curtain(d0)["Tg"][0]), 20 - 20 * 5.8 / 8.7, 1e-9))
    checks.append(("露点（20℃・60%）が約12℃", float(dew_point(20.0, 0.6)), 12.0, 0.1))
    # (2) カーテンあり: すき間の空気の熱のつり合いの残り（最大・W/m²）
    c = r["c1"]
    resid = (1.0 / p["Rc"] + RHO_AIR * CP_AIR * p["q"]) * (p["Tr"] - c["Tc"]) - U_GLASS * (c["Tc"] - p["To"])
    checks.append(("すき間の空気の熱のつり合いの残り（最大・W/m²）", float(np.max(np.abs(resid))), 0.0, 1e-9))
    # (3) すき間の水蒸気のつり合い: q(ρ部屋 − ρ_c) = h_m(ρ_c − ρ_sat(Tg))（頭打ちにならなかった回の最大の残り・kg/m²/s）
    rr = p["rh"] * rho_sat(p["Tr"])
    hm = mass_coef(p)
    res2 = c["qq"] * (rr - c["rc_free"]) - hm * (c["rc_free"] - rho_sat(c["Tg"]))
    mk = rr > rho_sat(c["Tg"])
    checks.append(("すき間の水蒸気のつり合いの残り（結露する回の最大）", float(np.max(np.abs(res2[mk]))), 0.0, 1e-12))
    # (4) 入れかわりがとても大きく・熱抵抗がとても小さいカーテンは「ないのと同じ」になる（先頭400回・量の最大の食い違い・割合）
    d1 = {k: v[:400] for k, v in p.items()}
    lim = with_curtain(d1, Rc=np.full(400, 1e-9), q=np.full(400, 1e5))["flux"]
    base = no_curtain(d1)["flux"]
    m_ = base > 1e-12
    checks.append(("カーテンが無いのと同じ極限（量の比の最大のずれ）", float(np.max(np.abs(lim[m_] / base[m_] - 1))), 0.0, 1e-3))
    # (5) 物理の向き: カーテンありのガラスは、なしより冷たい（全回）・すき間の空気は部屋より冷たく外より暖かい
    checks.append(("カーテンありのガラスは なし以下の温度（全回）", float(np.all(c["Tg"] <= r["n0"]["Tg"] + 1e-9)), 1.0, 0.0))
    checks.append(("すき間の空気の温度が 外〜部屋のあいだ（全回）",
                   float(np.all((c["Tc"] >= p["To"] - 1e-9) & (c["Tc"] <= p["Tr"] + 1e-9))), 1.0, 0.0))
    # (6) すき間の空気の水蒸気量は 部屋以下、ガラスの飽和量以上（結露する回）・ガラスに着く量 ≤ 部屋から入る量
    cond_c = c["flux"] > 0
    checks.append(("すき間の水蒸気量が 部屋以下（全回）", float(np.all(c["rc"] <= rr + 1e-12)), 1.0, 0.0))
    checks.append(("ガラスに着く量が 部屋から入る量以下（全回）", float(np.all(c["flux"] <= c["tot"] + 1e-15)), 1.0, 0.0))
    checks.append(("結露する回は すき間の水蒸気量 ≥ ガラスの飽和量", float(np.all(c["rc"][cond_c] >= rho_sat(c["Tg"])[cond_c] - 1e-12)), 1.0, 0.0))
    # (7) 見本は1万回の中の1回で、量の比が全体の中央値の近く・結露が出た回
    s = sample()
    checks.append(("見本の量の比が 中央値 r の近く（±6%）", s["ratio"], s1["r"], 0.06 * s1["r"]))
    checks.append(("見本は結露が出た回（なし・あり とも 5g/m² 以上）", float(s["g_n"] >= EPS_G and s["g_c"] >= EPS_G), 1.0, 0.0))
    checks.append(("見本の量が 1万回の値と同じ（なし・mL）", s["m_n"], float(r["g_n"][s["i"]] * p["A"][s["i"]]), 1e-9))
    checks.append(("見本の量が 1万回の値と同じ（あり・mL）", s["m_c"], float(r["g_c"][s["i"]] * p["A"][s["i"]]), 1e-9))
    # (8) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ（正解は C の位置）
    key = answer_by_rule(s1["p"], s1["r"])
    checks.append(("画面の正解の位置が 規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C", float(INTRO.correct), 2.0, 0.0))
    checks.append(("LABELS が 増える・ほぼ同じ・減る の3つ", float(sorted(LABELS) == sorted(KEY_LABEL.values())), 1.0, 0.0))
    # (9) 回数が足して1万（ふつう・ひねり。量がまったく同じ回は 0 のはず）
    tie1 = int((s1["cond"] & (r["g_c"] == r["g_n"])).sum())
    tie2 = int((s2["cond"] & (r["g_t"] == r["g_n"])).sum())
    checks.append(("分類の合計（ふつう）", float(s1["n_more"] + s1["n_less"] + s1["n_none"] + tie1), float(N_TRIAL), 0.0))
    checks.append(("分類の合計（ひねり）", float(s2["n_more"] + s2["n_less"] + s2["n_none"] + tie2), float(N_TRIAL), 0.0))
    checks.append(("量がまったく同じ回の数", float(tie1 + tie2), 0.0, 0.0))
    # (10) 画面の数字: マス目の数と分類の数が合う
    ca = cat_array(s1)
    checks.append(("マス目の「あり が多い」の数", float((ca == 0).sum()), float(s1["n_more"]), 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}分/秒  朝 {T_FIN:.2f}  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW_G:.1f}/{T_TW_RES:.1f}  "
          f"締め {T_Q:.1f}  見本 {s['i']}  コップ {CUP_ML:.0f}mL")
    print("  理由:", reason_text().replace("\n", " / "), "|", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 0.8, 1.2, 2.5, 4.4, 5.2, 6.5, 9.0, 12.0, 15.0, 18.0, T_FIN - 0.4, T_FIN + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 0.5, T_TW_G + 1.8, T_TW_RES + 0.6, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
