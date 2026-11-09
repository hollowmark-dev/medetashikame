"""冬の夕焼けが赤いのは、太陽が低いから？ 空気が澄んでいるから？ 太陽の高さだけ変えた場合と、空気だけ変えた場合を1万回。— 2026-10-28 作成（公開予定 11/9・ナレーションなし・45秒前後）

くらべるのは「夕日の光（太陽から目まで一直線に届く光）が、どれだけ赤いか」だけ。空の雲や、空全体の色は入れない。

モデル（太陽の光が、大気の中を通って目に届くまでに、どの色がどれだけ残るか。T(λ) = exp(−τ_空気(λ)·m_空気 − τ_ちり(λ)·m_ちり)）
  赤さ R = T(650nm) ÷ T(450nm)  …「青い光に対して、赤い光が何倍残るか」。自然対数 ln R で測る（比どうしの掛け算を足し算にするため）。
  ① 空気そのものの散乱（レイリー散乱。λ の −4 乗にほぼ比例して青いほど強く散る）
       τ_R(λ)  = 0.0021520·(1.0455996 − 341.29061·λ⁻² − 0.90230850·λ²) ÷ (1 + 0.0027059889·λ⁻² − 85.968563·λ²)   [λ は µm。海面・標準大気・CO2 360ppm。Bodhaine ほか 1999 の式 30]
          （λ = 0.45 µm で 約0.22、0.65 µm で 約0.049。--model のあとの run_checks で別の近似式と照合）
  ② ちり・湿気の粒（エアロゾル）の散乱・吸収。色によりにくいが、少しだけ青に強い（オングストロームの式）
       τ_ちり(λ) = τ_0.5 × (λ ÷ 0.5µm)^(−α)      τ_0.5 は 0.5µm の光学的厚さ（真上から見たときの濃さ）、α はオングストローム指数
  ③ 光が空気の中を通る長さ（エアマス）… 太陽の高さ h（地平線から何度）で決まる。地球の丸みを入れる
       空気: Kasten & Young (1989) の近似式 m_R = 1 ÷ [cos z + 0.50572·(96.07995 − z)^(−1.6364)]   z = 90° − h（度）。屈折を含み、地平線で約38
       ちり: 地表近くに集まっている（指数分布・スケールハイト Hc = 1〜2 km の仮定）ので、丸い地球・指数分布の大気を光線に沿って数値積分した値
             （同じ積分を Hc = 8.4 km で行うと K&Y と 高さ5°で約2%・2°で約5% 以内で合う＝run_checks。屈折の分だけ積分のほうが小さい）。屈折は入れていない
  入れていないもの: オゾンの吸収（赤と青の比 650/450 には小さいと見込むが確かめていない）、雲、散乱光（空の色）、水蒸気そのものの吸収、
                   太陽光の元のスペクトルのかたより（650/450 で比べるときは、どの条件でも同じなので差には出ない）

  幅（1回ごとにすべてでたらめ・一様。出典は FACTCHECK）
    太陽の高さ  「高め」h_高 = 6〜10° ／「低い」h_低 = 1〜3°
        冬の東京（北緯35.7°・赤緯−23°）で 日没の約40〜50分前が 約6〜8°、日没の約10〜15分前が 約2〜3°（式から計算・--model で表示）。
        夕焼けを見ている時間のなかの「少し前」と「盛り」。冬と夏で日没時の高さそのものは変わらないので、季節の差ではなく「夕方の間の差」として取った。
    空気  くらべる2種類の空気は、関東の観測（スカイラジオメーター・Aoki & Fujiyoshi 2003 の表1）の季節平均から
        ちりの多い空気（夏型）: τ_0.5 = 0.365 × (0.7〜1.3)（つくば 夏0.36・東京 夏0.37）、α = 0.95〜1.25（つくば 夏1.04・東京 夏1.22）
        澄んだ空気（冬型）    : τ_0.5 = 0.19 × (0.7〜1.3)（つくば 冬0.18・東京 冬0.20）、α = 1.15〜1.40（つくば 冬1.21・東京 冬1.35）
        ＊ 札幌（冬0.26・夏0.28）・新潟（冬0.35・夏0.35）は冬と夏の差がほぼない。これは関東の値＝場所によって「澄ませる」幅は違う（--model で幅を狭めた場合も表示）。
    ちりのスケールハイト Hc = 1〜2 km（出典は FACTCHECK。衛星の研究で 1・2・3 km を試し 2 km が近かった例）  …1回ごとに 4つの条件で共通

  4つの条件を同じ回で計算する: （高め・ちり）（高め・澄）（低い・ちり）（低い・澄）
    ① 太陽だけ低くしたときの 赤さの増え方 g1 = ½[ ln R(低・ちり) − ln R(高・ちり) + ln R(低・澄) − ln R(高・澄) ]
        （空気を「ちりの多い」に固定した場合と「澄んだ」に固定した場合の平均。どちらに固定するかで有利不利が出ないようにした）
    ② 空気だけ澄ませたときの 赤さの増え方 g2 = ½[ ln R(高・澄) − ln R(高・ちり) + ln R(低・澄) − ln R(低・ちり) ]（太陽の高さを「高め」「低い」で平均）
    ＊ 増え方は「比の差」ではなく ln R の差（＝赤さが何倍になるか）で測る。赤さは掛け算で増えるので、比の差で測ると基準しだいで大きく変わるため（計算の前に決めた）。

問い: 「冬の夕焼けが赤いのは、/ 太陽が低いから？ / 空気が澄んでいるから？」
      選択肢: 太陽が低いから ／ ほぼ同じ ／ 空気が澄んでいるから（記号の並びは LABELS の順。計算のあと、正解が C に来るよう入れ替えた）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回の g1 の中央値 a1 と g2 の中央値 a2 を比べる。
      どちらも絶対値が 0.1 未満（赤さが1割も変わらない）→ ほぼ同じ
      a1 > 0 かつ a1 ≥ 1.5 × a2 → 太陽が低いから    （a2 が負＝澄ませると赤さが減る場合も、これに入る。赤さを減らす向きの理由は「赤い理由」にならない）
      a2 > 0 かつ a2 ≥ 1.5 × a1 → 空気が澄んでいるから
      それ以外 → ほぼ同じ
ひねり: 「では、空気が澄んでいると、夕日はどうなる？」→ 赤さ（比）が減る場合は、そのまま出す。
      同じ低い太陽のとき、赤い光（650nm）の残る量が 澄んだ空気ではちりの多い空気の何倍か（中央値）も出す＝「赤さ」と「明るさ」は別。
締め: 「今日の夕焼け、何色でしたか？」（答えは出さない）＋「コメントで教えてください」
言葉: 1万回の結果の真ん中は「中央値」（初出で一度説明）。見本の1回は「たとえば、この1回では」、その数字は「この置き方なら」。
      夕日の色を実測で確かめた例は見つからなかったので、画面にも「観測で確かめた例は見つからず、計算での見立て」と小さく1回。

乱数の種は見本（2枚の絵の見た目）のために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "yuuyake-akai"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261109
LAM_R, LAM_G, LAM_B = 0.65, 0.55, 0.45               # µm（赤・緑・青）
H_HIGH, H_LOW = (6.0, 10.0), (1.0, 3.0)              # 太陽の高さ（度）
AIR = {"dusty": dict(t05=0.365, spread=(0.7, 1.3), alpha=(0.95, 1.25)),
       "clean": dict(t05=0.19, spread=(0.7, 1.3), alpha=(1.15, 1.40))}
HC = (1.0, 2.0)                                      # ちりのスケールハイト km
H_AIR_KM = 8.4                                       # 空気（検算用）
R_EARTH = 6371.0                                     # km

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_RATIO, RULE_MIN = 1.5, 0.1


def answer_by_rule(a1, a2):
    """a1 = ① 太陽だけ低くしたときの ln R の増え方の中央値、a2 = ② 空気だけ澄ませたとき。'sun' / 'same' / 'air'"""
    if max(abs(a1), abs(a2)) < RULE_MIN:
        return "same"
    if a1 > 0 and a1 >= RULE_RATIO * a2:
        return "sun"
    if a2 > 0 and a2 >= RULE_RATIO * a1:
        return "air"
    return "same"


def tau_rayleigh(lam):
    """Bodhaine ほか (1999) 式30。海面・標準大気・CO2 360ppm。lam は µm"""
    lam = np.asarray(lam, float)
    return 0.0021520 * (1.0455996 - 341.29061 * lam ** -2 - 0.90230850 * lam ** 2) / (1.0 + 0.0027059889 * lam ** -2 - 85.968563 * lam ** 2)


def airmass_ky(h_deg):
    """Kasten & Young (1989)。h は太陽の高さ（度）"""
    z = 90.0 - np.asarray(h_deg, float)
    return 1.0 / (np.cos(np.radians(z)) + 0.50572 * (96.07995 - z) ** -1.6364)


def chapman(h_deg, H_km, n=3000):
    """丸い地球・指数分布の大気を、太陽の光線に沿って数値積分した「真上の何倍の量を通るか」（屈折なし）。h は配列でも可、H_km も配列でも可"""
    h = np.atleast_1d(np.asarray(h_deg, float))
    H = np.broadcast_to(np.asarray(H_km, float), h.shape)
    z = np.radians(90.0 - h)
    top = R_EARTH + 14.0 * H                                     # 密度が e^-14 に落ちる高さ
    smax = np.sqrt(top ** 2 - (R_EARTH * np.sin(z)) ** 2) - R_EARTH * np.cos(z)
    u = np.linspace(0.0, 1.0, n)[None, :] ** 2.2
    s = smax[:, None] * u
    r = np.sqrt(R_EARTH ** 2 + s ** 2 + 2.0 * R_EARTH * s * np.cos(z)[:, None])
    f = np.exp(-(r - R_EARTH) / H[:, None])
    integ = np.sum(0.5 * (f[:, 1:] + f[:, :-1]) * np.diff(s, axis=1), axis=1)
    return integ / H


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    d = dict(h_hi=u(H_HIGH), h_lo=u(H_LOW), Hc=u(HC))
    for k, a in AIR.items():
        d["t_" + k] = a["t05"] * u(a["spread"])
        d["a_" + k] = u(a["alpha"])
    return d


def ln_T(lam, h, air, d, same_mass=False):
    """ln T(λ)（光が残る割合の自然対数）。air は 'dusty' / 'clean'。same_mass=True はちりにも空気と同じエアマス（感度の確認用）"""
    mR = airmass_ky(h)
    mA = mR if same_mass else chapman(h, d["Hc"])
    tau_a = d["t_" + air] * (lam / 0.5) ** (-d["a_" + air])
    return -(tau_rayleigh(lam) * mR + tau_a * mA)


def physics(d, same_mass=False):
    """4つの条件の ln R と 赤い光の残り。戻り値は dict（配列）"""
    out = {}
    for hk in ("hi", "lo"):
        for air in ("dusty", "clean"):
            h = d["h_" + hk]
            lr, lg, lb = (ln_T(l, h, air, d, same_mass) for l in (LAM_R, LAM_G, LAM_B))
            out[(hk, air)] = dict(lnR=lr - lb, lnT_r=lr, lnT_g=lg, lnT_b=lb)
    g1 = 0.5 * ((out[("lo", "dusty")]["lnR"] - out[("hi", "dusty")]["lnR"]) + (out[("lo", "clean")]["lnR"] - out[("hi", "clean")]["lnR"]))
    g2 = 0.5 * ((out[("hi", "clean")]["lnR"] - out[("hi", "dusty")]["lnR"]) + (out[("lo", "clean")]["lnR"] - out[("lo", "dusty")]["lnR"]))
    return dict(c=out, g1=g1, g2=g2)


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
    ph = physics(d)
    _RES["m"] = dict(p=d, ph=ph)
    return _RES["m"]


def sun_set_height(minutes_before, lat=35.66, decl=-23.4):
    """日没の何分前の太陽の高さ（度）。上の縁が地平線に触れる＝高さ −0.83° を日没として、時角から逆算する（大気の屈折・太陽の半径を含む標準の値）"""
    la, de = math.radians(lat), math.radians(decl)
    h0 = math.radians(-0.833)
    ha_set = math.acos((math.sin(h0) - math.sin(la) * math.sin(de)) / (math.cos(la) * math.cos(de)))
    ha = ha_set - math.radians(15.0 * minutes_before / 60.0)
    return math.degrees(math.asin(math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(ha))), 12.0 * math.degrees(ha_set) / 180.0


def shown():
    r = results()
    g1, g2 = r["ph"]["g1"], r["ph"]["g2"]
    a1, a2 = float(np.median(g1)), float(np.median(g2))
    c = r["ph"]["c"]
    # ひねり: 低い太陽のとき、赤い光（650nm）の残りが 澄んだ空気ではちりの多い空気の何倍か（回ごとの比の中央値）
    red_gain = np.exp(c[("lo", "clean")]["lnT_r"] - c[("lo", "dusty")]["lnT_r"])
    red_gain_hi = np.exp(c[("hi", "clean")]["lnT_r"] - c[("hi", "dusty")]["lnT_r"])
    return dict(a1=a1, a2=a2, m1=math.exp(a1), m2=math.exp(a2),
                inc1=float(np.mean(g1 >= RULE_MIN)), inc2=float(np.mean(g2 >= RULE_MIN)),
                dec1=float(np.mean(g1 <= -RULE_MIN)), dec2=float(np.mean(g2 <= -RULE_MIN)), g1_q=np.percentile(g1, [10, 50, 90]), g2_q=np.percentile(g2, [10, 50, 90]),
                red_gain=float(np.median(red_gain)), red_gain_hi=float(np.median(red_gain_hi)),
                red_left_lo={k: float(np.median(np.exp(c[("lo", k)]["lnT_r"]))) for k in ("dusty", "clean")},
                red_left_hi={k: float(np.median(np.exp(c[("hi", k)]["lnT_r"]))) for k in ("dusty", "clean")},
                R={k: float(np.median(np.exp(c[k]["lnR"]))) for k in c})


def sensitivity(n=4000):
    """幅や置き方を変えても 答え（a1, a2）が動くか。_RES を汚さないよう別の乱数で"""
    global H_HIGH, H_LOW
    base_h = (H_HIGH, H_LOW)
    base_air = {k: dict(v) for k, v in AIR.items()}
    rows = []

    def run(label, same_mass=False):
        d = draw_params(np.random.default_rng(SEED_MAIN + 1), n)
        ph = physics(d, same_mass)
        a1, a2 = float(np.median(ph["g1"])), float(np.median(ph["g2"]))
        rows.append((label, a1, a2, answer_by_rule(a1, a2)))

    def reset():
        global H_HIGH, H_LOW
        H_HIGH, H_LOW = base_h
        for k in AIR:
            AIR[k].update(base_air[k])

    run("基準")
    run("ちりにも空気と同じエアマス（スケールハイトなし）", same_mass=True)
    H_HIGH, H_LOW = (4.0, 8.0), (2.0, 4.0)
    run("太陽の幅を狭く（高め4〜8°・低い2〜4°）")
    H_HIGH, H_LOW = (3.0, 5.0), (1.0, 3.0)
    run("太陽の幅をさらに狭く（高め3〜5°・低い1〜3°）")
    reset()
    AIR["clean"]["t05"] = 0.30
    run("澄んだ空気を夏の0.8倍だけ（札幌・新潟のように差が小さい）")
    reset()
    AIR["clean"]["t05"] = 0.10
    run("澄んだ空気をもっと澄ませる（τ0.5 = 0.10）")
    reset()
    AIR["dusty"]["t05"] = 0.60
    run("ちりの多い空気を濃く（τ0.5 = 0.60）")
    reset()
    AIR["clean"]["alpha"] = (0.95, 1.25)
    run("澄んだ空気の α を夏と同じにする（濃さだけの差）")
    reset()
    return rows


def report():
    sh = shown()
    key = answer_by_rule(sh["a1"], sh["a2"])
    print(f"① 太陽だけ低く: ln R の増え方の中央値 {sh['a1']:+.3f}（赤さ ×{sh['m1']:.2f}）  10/90% {np.round(sh['g1_q'][[0, 2]], 2)}")
    print(f"② 空気だけ澄ませる: ln R の増え方の中央値 {sh['a2']:+.3f}（赤さ ×{sh['m2']:.2f}）  10/90% {np.round(sh['g2_q'][[0, 2]], 2)}")
    print(f"  ①/② = {sh['a1'] / sh['a2'] if sh['a2'] else float('nan'):.2f}   答え {key}   赤さが1割以上増えた回: ① {sh['inc1'] * 100:.1f}%  ② {sh['inc2'] * 100:.1f}%（1割以上減った回 {sh['dec2'] * 100:.1f}%）")
    print("  中央値の赤さ R（赤÷青の残り）: " + "  ".join(f"{k[0]}・{k[1]} ×{v:.1f}" for k, v in sh["R"].items()))
    print(f"  ひねり: 低い太陽 赤い光の残り（650nm）ちり {sh['red_left_lo']['dusty'] * 100:.3g}% / 澄 {sh['red_left_lo']['clean'] * 100:.3g}%  澄/ちり ×{sh['red_gain']:.2f}"
          f"   高め太陽: ちり {sh['red_left_hi']['dusty'] * 100:.3g}% / 澄 {sh['red_left_hi']['clean'] * 100:.3g}%  ×{sh['red_gain_hi']:.2f}")
    for mb in (50, 40, 15, 10, 0):
        hh, ss = sun_set_height(mb)
        print(f"  冬の東京 日没の{mb}分前の太陽の高さ {hh:.1f}°（昼の長さの半分 {ss:.2f}時間）")


def report_sensitivity():
    print("感度（幅や置き方を変えても）:")
    for lab, a1, a2, k in sensitivity():
        print(f"  {lab}: ①{a1:+.2f}（×{math.exp(a1):.1f}）②{a2:+.2f}（×{math.exp(a2):.2f}） → {k}")


# ---- MODEL END ----


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す2枚の1回ぶん）を選ぶ
# =====================================================================
HT = np.linspace(0.5, 14.0, 217)                    # 見本の表を作る太陽の高さ（度）
_SAMPLE = None


def sample():
    """見本: 1万回の中の1回（その回の値そのもの）。中央値に近い回（太陽の高さ・ちりの濃さ・① ②の増え方）を選ぶ。
    上の絵（Ⓒ 太陽だけ低くする）: 空気は「ちりの多い」のまま、太陽が 高め h_高 → 低い h_低 へ下がる。
    下の絵（Ⓐ 空気だけ澄ませる）: 太陽は「低い」h_低 のまま、空気が ちりの多い → 澄んだ へ変わる（ちりの点が減る）。"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p, ph = r["p"], r["ph"]
    sh = shown()
    dist = (np.abs(p["h_lo"] - 2.0) / 1.0 + np.abs(p["h_hi"] - 8.0) / 2.0 + np.abs(p["t_dusty"] - 0.365) / 0.1
            + np.abs(p["t_clean"] - 0.19) / 0.05 + np.abs(p["Hc"] - 1.5) / 0.5
            + np.abs(ph["g1"] - sh["a1"]) / 1.0 + np.abs(ph["g2"] - sh["a2"]) / 0.3)
    i = int(np.argmin(dist))
    S = dict(i=i, g1=float(ph["g1"][i]), g2=float(ph["g2"][i]), h_hi=float(p["h_hi"][i]), h_lo=float(p["h_lo"][i]), Hc=float(p["Hc"][i]),
             dusty=dict(t05=float(p["t_dusty"][i]), alpha=float(p["a_dusty"][i])), clean=dict(t05=float(p["t_clean"][i]), alpha=float(p["a_clean"][i])))
    S["mR"] = airmass_ky(HT)
    S["mA"] = chapman(HT, np.full(HT.shape, S["Hc"]))
    _SAMPLE = S
    return S


def air_at(w):
    """空気の混ぜ具合 w（0 = ちりの多い、1 = 澄んだ）での ちりの濃さ τ0.5 と α"""
    S = sample()
    return (S["dusty"]["t05"] + (S["clean"]["t05"] - S["dusty"]["t05"]) * w,
            S["dusty"]["alpha"] + (S["clean"]["alpha"] - S["dusty"]["alpha"]) * w)


def state(h, w=0.0):
    """太陽の高さ h・空気 w での 光の通る長さ・ln T(赤/緑/青)・赤÷青"""
    S = sample()
    mr = float(np.interp(h, HT, S["mR"]))
    ma = float(np.interp(h, HT, S["mA"]))
    t05, al = air_at(w)
    ls = [-(float(tau_rayleigh(lam)) * mr + t05 * (lam / 0.5) ** (-al) * ma) for lam in (LAM_R, LAM_G, LAM_B)]
    return dict(mR=mr, mA=ma, lr=ls[0], lg=ls[1], lb=ls[2], R=math.exp(ls[0] - ls[2]), lnR=ls[0] - ls[2])


def cond_pair(k):
    """絵の1枚の 前と後の条件 ((h, w), (h, w))。'top' = 太陽だけ低く、'bot' = 空気だけ澄ませる"""
    S = sample()
    if k == "top":
        return (S["h_hi"], 0.0), (S["h_lo"], 0.0)
    return (S["h_lo"], 0.0), (S["h_lo"], 1.0)


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    S = sample()
    print("見本 回", S["i"], " g1", round(S["g1"], 2), " g2", round(S["g2"], 2), " 高め", round(S["h_hi"], 2), "° 低い", round(S["h_lo"], 2), "° Hc", round(S["Hc"], 2),
          " ちり τ0.5", round(S["dusty"]["t05"], 3), "α", round(S["dusty"]["alpha"], 2), " 澄 τ0.5", round(S["clean"]["t05"], 3), "α", round(S["clean"]["alpha"], 2))
    for k in ("top", "bot"):
        b, a = cond_pair(k)
        print(" ", k, "前 赤÷青 ×", round(state(*b)["R"], 1), " 後 ×", round(state(*a)["R"], 1))
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
note.DATE = "11.9"                                  # 日付欄（公開予定日）

COL_S, INK_S = "#f4ad6a", "#b8601a"                 # 太陽が低いから（だいだい）
COL_A, INK_A = "#8fbbe8", "#2f63a8"                 # 空気が澄んでいるから（水色）
UP_COL, NO_COL = "#f08a5d", "#cfd9e6"               # マス目: 赤さが増えた / 増えなかった
SKIN = "#f7d9bd"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
# 規則の答えが「太陽が低いから」なので、正解が C の位置に来るよう 空気が澄んでいるから／ほぼ同じ／太陽が低いから の並びにした
LABELS = ["空気が澄んでいるから", "ほぼ同じ", "太陽が低いから"]
TAG = {"air": "A", "sun": "C"}
CORRECT = 2                                         # answer_by_rule の結果の位置（C）
KEY_LABEL = {"sun": "太陽が低いから", "same": "ほぼ同じ", "air": "空気が澄んでいるから"}
NAME = {"sun": "太陽が低いから", "air": "空気が澄んでいるから"}
COLS = {"sun": COL_S, "air": COL_A}
INKC = {"sun": INK_S, "air": INK_A}
PANEL_KEY = {"top": "sun", "bot": "air"}            # キーの名前は作った順のまま。置き場所は Y_INTRO / Y_FINAL で 上＝Ⓐ 空気だけ澄ませる（"bot"）、下＝Ⓒ 太陽だけ低くする（"top"）。問い・記号の順（A空気→C太陽）とそろえる
PANEL_TITLE = {"top": ("太陽だけ 低くする", "（空気は同じ）"), "bot": ("空気だけ 澄ませる", "（太陽の高さは同じ）")}

Q_LINE1 = "冬の夕焼けが赤いと言われるのは、"                 # 問いの1行目（ここだけ。変えたら report_full / run_checks が 3行の収まりを確かめる）
BIG_Q = [Q_LINE1, "空気が澄んでいるから？ 太陽が低いから？"]                  # 定位置（上）の2行
BIG_Q3 = ["冬の夕焼けが", "赤いと言われるのは、", "空気が澄んでいるから？", "太陽が低いから？"]   # 1コマ目の4行（同じ大きさ。1行目が長いので4行に割って字を大きく）
DETAIL = "夕日の光の色を計算・空気は観測の平均値をもとに"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 10.0                                     # T_GO から 太陽が見本の高さに着くまで

# 画面の置き場所（絵のカードは 局所座標 900×420 で描いて、移動・拡大する）
WC, HC_ = 900.0, 420.0
CAR_CX = 520.0
S0, S1 = 0.86, 1.0
Y_INTRO = {"bot": 830.0, "top": 830.0 + HC_ * S0 + 16.0}       # 上＝空気（A）、下＝太陽（C）
Y_FINAL = {"bot": 588.0, "top": 588.0 + HC_ + 8.0}
SKY = (22.0, 54.0, 856.0, 318.0)                    # 絵の中の窓（x, y, 幅, 高さ）
EYE = (682.0, 155.0)                                # 光が目に入る点
SUN_X = 170.0
PEOPLE = ((790.0, 334.0, 1.05, "pocket", 4), (700.0, 334.0, 1.0, "shade", 1))      # 奥から（x, 足もとy, 大きさ, 姿勢, 服の色）


def setup():
    global T_FIN2, T_VERD, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_TW2, T_Q, DURATION
    T_FIN2 = T_GO + RACE_LEN
    T_VERD = T_FIN2 - 0.8
    T_G0 = T_FIN2 + 2.4
    T_G1 = T_G0 + 3.0
    T_REV = T_G1 + 3.0
    T_ANS2 = T_REV + 2.4
    T_TW = T_ANS2 + 5.0
    T_TW2 = T_TW + 2.4
    T_Q = T_TW2 + 4.4
    DURATION = T_Q + 6.0


def prog(t):
    """太陽が沈む進み（0〜1）"""
    return ease(clamp01((t - T_GO) / (T_VERD - T_GO)))


def cond(k, t):
    """時刻 t の 絵の1枚の条件 (太陽の高さ h, 空気 w)。前の条件から後の条件へ prog(t) で動く"""
    b, a = cond_pair(k)
    u = prog(t)
    return b[0] + (a[0] - b[0]) * u, b[1] + (a[1] - b[1]) * u


def pcs(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


def xtxt(x):
    """倍率の表示。10未満は小数1桁、それ以上は整数"""
    if x < 0.995:
        return f"{x:.2f}"
    if x < 9.95:
        return f"{x:.1f}"
    return f"{int(round(x))}"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, w, col, outline=2.6):
    """太い線（ふちどり付き）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


def mixc(c0, c1, u):
    a, b = hexrgb(c0), hexrgb(c1)
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def ik2(sx, sy, wx, wy, l1, l2):
    """肩 (sx, sy) と手首 (wx, wy) から、ひじの位置（2つの解のうち 下・手前向き）"""
    dx, dy = wx - sx, wy - sy
    dd = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 2.0, math.hypot(dx, dy)))
    a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd)
    hh = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    bx, by = sx + a * ux, sy + a * uy
    c1 = (bx - hh * uy, by + hh * ux)
    c2 = (bx + hh * uy, by - hh * ux)
    return c1 if (c1[1] - 0.6 * c1[0]) > (c2[1] - 0.6 * c2[0]) else c2


COATS = ["#7c8fb5", "#c9786b", "#6d9a86", "#a98fc4", "#d6b25a", "#5f6b80", "#b07d54", "#d98fa0"]
SCARF = ["#e8e0d0", "#b84a4a", "#3f6fa8", "#e4b84a", "#4f8a6a"]
HAIR = ["#2b2b33", "#4a3526", "#1f2430", "#6a4a33", "#3a3a44"]
PANTS = "#3b4358"


def person_side(ctx, x, fy, sc, ci, t, pose):
    """横向きの人（左を向く＝絵の中の太陽のほうを見る）。(x, fy) は足もとの中心。sc=1 で身長 約190px。
    pose: 'shade'（手をひたいにかざす）/ 'pocket'（ポケットに手）"""
    coat, scarf, hair = COATS[ci % len(COATS)], SCARF[ci % len(SCARF)], HAIR[(ci * 3 + 1) % len(HAIR)]
    bob = 1.2 * math.sin(t * 1.6 + ci)
    fy = fy - bob * 0.0
    P = lambda dx, dy: (x + dx * sc, fy + dy * sc)   # noqa: E731
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    # 脚（奥→手前）と くつ
    for dx0, dx1, col in ((6, 9, "#323a4e"), (-3, -9, PANTS)):
        thick(ctx, [P(dx0, -84), P(dx1, -9)], 17 * sc, col, 2.4)
        sx, sy = P(dx1 - 6, -4)
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1.0, 0.45)
        ctx.arc(0, 0, 17 * sc, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#2a2f3d"))
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.9)
    # 奥のうで（背中がわ・コートの色）
    thick(ctx, [P(8, -146), P(14, -112), P(8, -84)], 13 * sc, coat, 2.4)
    # コート
    ctx.new_path()
    ctx.move_to(*P(-13, -154))
    ctx.curve_to(*P(-22, -146), *P(-24, -112), *P(-23, -76))
    ctx.line_to(*P(25, -76))
    ctx.curve_to(*P(24, -112), *P(24, -146), *P(15, -154))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(coat))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.9)
    ctx.move_to(*P(-23, -88))
    ctx.line_to(*P(25, -88))
    _stroke(ctx, 2.0, INK, 0.35)
    # マフラー（首に巻いて、うしろに垂らす）
    thick(ctx, [P(10, -150), P(20, -132), P(18, -112)], 9 * sc, scarf, 2.2)
    core.rrect(ctx, *P(-17, -166), 33 * sc, 15 * sc, 7 * sc)
    ctx.set_source_rgba(*hexrgb(scarf))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.9)
    # 頭
    hx, hy = P(-1, -178)
    hr = 15.5 * sc
    ctx.arc(hx, hy, hr, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.8, INK, 0.9)
    ctx.new_path()                                                   # 髪（うしろと上）
    ctx.arc(hx, hy, hr + 1.8 * sc, math.pi * 1.08, math.pi * 2.36)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.9)
    ctx.new_path()                                                   # 鼻
    ctx.move_to(hx - hr + 1.0 * sc, hy - 3 * sc)
    ctx.line_to(hx - hr - 5.5 * sc, hy + 3 * sc)
    ctx.line_to(hx - hr + 1.5 * sc, hy + 5 * sc)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.2, INK, 0.85)
    blink = (t * 0.9 + ci * 0.7) % 3.4 < 0.12
    ex, ey = hx - 8 * sc, hy - 1.5 * sc                               # 目
    if blink or pose == "shade":
        ctx.move_to(ex - 3.4 * sc, ey)
        ctx.line_to(ex + 3.2 * sc, ey - 0.4 * sc)
        _stroke(ctx, 2.4, INK, 0.95)
    else:
        ctx.arc(ex, ey, 2.3 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
    ctx.move_to(hx - 12 * sc, hy + 8.5 * sc)                          # 口
    ctx.line_to(hx - 6 * sc, hy + 9 * sc)
    _stroke(ctx, 2.2, INK, 0.85)
    # 手前のうで
    shx, shy = P(-4, -146)
    if pose == "shade":
        wx, wy = P(-17, -183)
        elx, ely = ik2(shx, shy, wx, wy, 36 * sc, 36 * sc)
        thick(ctx, [(shx, shy), (elx, ely), (wx, wy)], 13 * sc, coat, 2.4)
        ctx.new_path()
        core.rrect(ctx, wx - 9 * sc, wy - 5.5 * sc, 20 * sc, 10 * sc, 5 * sc)                 # ひたいにかざした手
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.9)
    else:
        wx, wy = P(-6, -98)
        elx, ely = ik2(shx, shy, wx, wy, 34 * sc, 30 * sc)
        thick(ctx, [(shx, shy), (elx + 10 * sc, ely), (wx, wy)], 13 * sc, coat, 2.4)
        ctx.arc(wx, wy + 2 * sc, 6 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 2.2, INK, 0.9)
    # 息（白いもや。左上へ）
    for j in range(2):
        u = (t * 0.45 + ci * 0.31 + j * 0.5) % 1.0
        bx, by = P(-21 - 16 * u, -170 - 12 * u)
        ctx.arc(bx, by, (4 + 8 * u) * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.8 * (1 - u))
        ctx.fill_preserve()
        _stroke(ctx, 1.5, PENCIL, 0.4 * (1 - u))
    ctx.restore()


# ---------- 絵: 空・町・光の線 ----------
_DECOR = {}


def decor():
    if _DECOR:
        return _DECOR
    rng = np.random.default_rng(11)
    hills = [(22 + i * 18.0, 193 + 9 * math.sin(i * 0.55) + 6 * math.sin(i * 1.7 + 1.0)) for i in range(48)]
    rows = []
    for yb, hl, wl, n_ in ((248, (16, 28), (22, 34), 0), (292, (26, 44), (30, 46), 1), (338, (38, 60), (40, 62), 2)):
        x = 26.0 + rng.uniform(0, 20)
        while x < 500:
            w = rng.uniform(*wl)
            h = rng.uniform(*hl)
            rows.append((x, yb, w, h, int(rng.integers(0, 6)), n_, rng.uniform(0.2, 1.0)))
            x += w + rng.uniform(4, 14)
    specks = [(rng.uniform(SKY[0], SKY[0] + SKY[2]), rng.uniform(SKY[1] + 6, 330), rng.uniform(1.5, 3.4), rng.uniform(0, 1), rng.uniform(4, 12)) for _ in range(90)]
    dots = [((i * 0.6180339 + 0.13) % 1.0, rng.uniform(0, 1), (-1) ** i, rng.uniform(0.7, 1.3)) for i in range(48)]
    _DECOR.update(hills=hills, blds=rows, specks=specks, dots=dots)
    return _DECOR


BLD_COL = ["#d9c9b0", "#c9d4dc", "#e0d2bf", "#bfcad6", "#d6c0b4", "#cfd8c4"]
ROOF_COL = ["#a86a5a", "#7d8ea6", "#9a7d6a", "#6f7f93", "#b07d54", "#7b8f86"]


def sun_color(h, w):
    """目に届く光の色（赤・緑・青の残りの比から。いちばん多く残る色を 1 に）"""
    st = state(h, w)
    mx = max(st["lr"], st["lg"], st["lb"])
    ch = [math.exp(0.42 * (st[c] - mx)) for c in ("lr", "lg", "lb")]
    return tuple(ch)


def ray_color(h, w, f):
    st = state(h, w)
    ls = [f * st[c] for c in ("lr", "lg", "lb")]
    mx = max(ls)
    return tuple(math.exp(0.42 * (v - mx)) for v in ls)


def draw_sky(ctx, t, h, aw, dusk):
    x, y, w, hh = SKY
    st = state(h, aw)
    red = clamp01(st["lnR"] / 6.5)
    sc = sun_color(h, aw)
    ctx.push_group()
    g = cairo.LinearGradient(0, y, 0, y + 200)
    g.add_color_stop_rgb(0, *mixc("#86b9ea", "#6f9ed4", dusk))
    g.add_color_stop_rgb(1, *mixc("#e3eef6", "#f2b98a", red * 0.9))
    ctx.set_source(g)
    ctx.rectangle(x, y, w, 230)
    ctx.fill()
    # 太陽のまわりのにじみ
    sy_ = EYE[1] - math.tan(math.radians(h)) * (EYE[0] - 10 - SUN_X)
    rg = cairo.RadialGradient(SUN_X, sy_, 6, SUN_X, sy_, 230)
    rg.add_color_stop_rgba(0, sc[0], sc[1], sc[2], 0.55 * (0.35 + 0.65 * red))
    rg.add_color_stop_rgba(1, sc[0], sc[1], sc[2], 0.0)
    ctx.set_source(rg)
    ctx.rectangle(x, y, w, 230)
    ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.3 + 0.7 * ease(clamp01(t / 1.0)))                    # 冒頭: 空が、うすい色から色づく


def draw_town(ctx, t, h, dusk, dust):
    D = decor()
    # 遠い丘
    hc = mixc("#a9bdd3", "#c7b79c", clamp01(dust))
    ctx.move_to(22, 250)
    for hx, hy in D["hills"]:
        ctx.line_to(hx, hy)
    ctx.line_to(878, 250)
    ctx.close_path()
    ctx.set_source_rgba(*hc, 0.95)
    ctx.fill()
    # 地面
    gc = mixc("#cfdab8", "#c3ccae", dusk)
    ctx.rectangle(22, 214, 856, 160)
    ctx.set_source_rgba(*gc, 1.0)
    ctx.fill()
    for (bx, yb, bw, bh, ci, rown, lt) in D["blds"]:
        col = BLD_COL[ci % len(BLD_COL)]
        ctx.rectangle(bx, yb - bh, bw, bh)
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, 2.0, INK, 0.55)
        ctx.move_to(bx - 2, yb - bh)
        ctx.line_to(bx + bw / 2, yb - bh - bw * 0.28)
        ctx.line_to(bx + bw + 2, yb - bh)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(ROOF_COL[ci % len(ROOF_COL)]))
        ctx.fill_preserve()
        _stroke(ctx, 2.0, INK, 0.55)
        n_win = max(1, int(bw // 14))
        for wi in range(n_win):
            wx = bx + 5 + wi * (bw - 10) / n_win
            lit = lt < dusk * 0.9
            ctx.rectangle(wx, yb - bh + 8, 6 + rown, 7 + rown)
            ctx.set_source_rgba(*hexrgb("#ffe08a" if lit else "#8fa0b4", 0.95 if lit else 0.6))
            ctx.fill()
    # 地平線のもや（ちりが多いほど濃い）
    hz = cairo.LinearGradient(0, 160, 0, 300)
    hz.add_color_stop_rgba(0, 0.93, 0.86, 0.74, 0.0)
    hz.add_color_stop_rgba(0.45, 0.93, 0.86, 0.74, 0.55 * clamp01(dust))
    hz.add_color_stop_rgba(1, 0.93, 0.86, 0.74, 0.0)
    ctx.set_source(hz)
    ctx.rectangle(22, 160, 856, 140)
    ctx.fill()


def draw_specks(ctx, t, dust):
    D = decor()
    n = int(18 + 70 * clamp01(dust))
    for (sx, sy, sr, ph, spd) in D["specks"][:n]:
        x = SKY[0] + ((sx - SKY[0] + t * spd) % SKY[2])
        y = sy + 3.0 * math.sin(t * 0.8 + ph * 6.28)
        ctx.arc(x, y, sr, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#b08c5a", 0.5))
        ctx.fill()


def draw_ray(ctx, t, h, aw, ga):
    D = decor()
    st = state(h, aw)
    sy_ = EYE[1] - math.tan(math.radians(h)) * (EYE[0] - 10 - SUN_X)
    ex, ey = EYE[0] - 10, EYE[1]
    # 水平の目安と角度
    if ga > 0:
        ctx.set_dash([8, 7])
        ctx.move_to(ex, ey)
        ctx.line_to(ex - 190, ey)
        _stroke(ctx, 2.2, PENCIL, 0.8 * ga)
        ctx.set_dash([])
    # 光の線（ふちどり → 色つき。太陽から目まで、残る色が変わっていく）
    nseg = 48
    for ww, outl in ((13.0, True), (8.0, False)):
        for i in range(nseg):
            f0, f1 = i / nseg, (i + 1) / nseg
            ctx.move_to(SUN_X + (ex - SUN_X) * f0, sy_ + (ey - sy_) * f0)
            ctx.line_to(SUN_X + (ex - SUN_X) * f1, sy_ + (ey - sy_) * f1)
            if outl:
                ctx.set_source_rgba(*hexrgb(INK, 0.42))
            else:
                c = ray_color(h, aw, (f0 + f1) / 2)
                ctx.set_source_rgba(c[0], c[1], c[2], 0.98)
            ctx.set_line_width(ww)
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            ctx.stroke()
    # 青い光が横へ散っていく
    tb = max(0.5, -st["lb"])
    n = int(min(46, 5 + 2.6 * tb))
    te = min(tb, 3.5)
    dx, dy = ex - SUN_X, ey - sy_
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    for (u0, ph, sg, spd) in D["dots"][:n]:
        f = -math.log(1 - u0 * (1 - math.exp(-te))) / te
        a = (t * 0.55 * spd + ph) % 1.0
        off = sg * (8 + 62 * a)
        px = SUN_X + dx * f + nx * off + dx / ln * 14 * a
        py = sy_ + dy * f + ny * off + dy / ln * 14 * a
        ctx.arc(px, py, 4.6 * (1 - 0.3 * a), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#4a90e2", 0.92 * (1 - a) ** 0.7))
        ctx.fill_preserve()
        _stroke(ctx, 1.4, "#1f4f99", 0.55 * (1 - a))
    # 太陽
    sc = sun_color(h, aw)
    ctx.arc(SUN_X, sy_, 24, 0, 2 * math.pi)
    ctx.set_source_rgba(1.0, 0.97, 0.82, 1.0)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.85)
    ctx.arc(SUN_X, sy_, 15, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, 0.9)
    ctx.fill()
    if ga > 0:
        ang = math.radians(h)
        r_ = 84.0
        ctx.arc(ex, ey, r_, math.pi, math.pi + ang)
        _stroke(ctx, 3.0, INK_S, 0.9 * ga)
        text(ctx, f"高さ {h:.1f}°".replace(".0°", "°"), ex - 150, ey + 30, 28, INK_S, alpha=ga)


def draw_dike(ctx):
    ctx.move_to(452, 372)
    ctx.curve_to(500, 366, 520, 340, 570, 334)
    ctx.line_to(878, 334)
    ctx.line_to(878, 372)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#8fb36e"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.85)
    ctx.move_to(572, 340)
    ctx.line_to(878, 340)
    _stroke(ctx, 2.2, "#6f9254", 0.9)
    for gx in range(580, 870, 34):                                    # 草
        ctx.move_to(gx, 358)
        ctx.line_to(gx + 4, 349)
        ctx.move_to(gx + 8, 358)
        ctx.line_to(gx + 9, 351)
    _stroke(ctx, 2.0, "#5f8a45", 0.8)


# ---------- 絵: カード ----------

def card_xf(k, m):
    s = S0 + (S1 - S0) * m
    y0 = Y_INTRO[k] + (Y_FINAL[k] - Y_INTRO[k]) * m
    return CAR_CX - WC * s / 2, y0, s


def draw_card(ctx, k, t, m):
    h, aw = cond(k, t)
    st = state(h, aw)
    bef, aft = cond_pair(k)
    x0, y0, s = card_xf(k, m)
    ga = clamp01((m - 0.85) / 0.15)                                  # 数字は、問いが上に移ったあとで出す
    key = PANEL_KEY[k]
    dusk = clamp01((10.0 - h) / 9.0)
    dust = clamp01((air_at(aw)[0] - 0.1) / 0.35)
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(s, s)
    core.rrect(ctx, 0, 0, WC, HC_, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    # --- 題 ---
    xd, yd = 40, 28
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 22, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 22, 22, INKC[key], seed=13 + (k == "bot"), width=3.4)
    text(ctx, TAG[key], xd, yd, 30, INKC[key])
    t1, t2 = PANEL_TITLE[k]
    text(ctx, t1, 76, yd, 40, INKC[key], align="left")
    text(ctx, t2, 76 + core.text_width(t1, 40) + 8, yd, 30, INK, align="left", bold=False)
    # --- 窓（空・町・光・人）---
    x, y, w, hh = SKY
    ctx.save()
    core.rrect(ctx, x, y, w, hh, 10)
    ctx.clip()
    fill(ctx, hexrgb("#e3eef6"))
    ctx.rectangle(x, y, w, hh)
    ctx.fill()
    draw_sky(ctx, t, h, aw, dusk)
    draw_town(ctx, t, h, dusk, dust)
    draw_specks(ctx, t, dust)
    draw_ray(ctx, t, h, aw, ga)
    draw_dike(ctx)
    for (px, pfy, psc, pose, ci) in PEOPLE:
        person_side(ctx, px, pfy, psc, ci, t, pose)
    if k == "top" and ga > 0 and t < T_G0 - 0.5:
        a_ = ga * ease_out((t - T_GO - 0.3) / 0.4)
        if a_ > 0:
            core.rrect(ctx, 30, 236, 296, 80, 10)
            ctx.set_source_rgba(*hexrgb(PAPER, 0.88 * a_))
            ctx.fill()
            ctx.arc(52, 260, 6, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#4a90e2", a_))
            ctx.fill()
            text(ctx, "青い光は 横へ散る", 70, 260, 27, INK_A, align="left", alpha=a_)
            ctx.move_to(44, 292)
            ctx.line_to(60, 292)
            _stroke(ctx, 6, RED, 0.9 * a_)
            text(ctx, "赤い光は 目に届く", 70, 292, 27, RED, align="left", alpha=a_)
    ctx.restore()
    core.rrect(ctx, x, y, w, hh, 10)
    _stroke(ctx, 3.2, INK, 0.85)
    # --- 下の帯: 前と後の赤さ（見本の1回の値）---
    if ga > 0:
        text(ctx, "たとえば、この1回では", 28, 398, 26, PENCIL, align="left", bold=False, alpha=ga)
        sc = sun_color(h, aw)
        ctx.arc(352, 398, 15, 0, 2 * math.pi)
        ctx.set_source_rgba(sc[0], sc[1], sc[2], ga)
        ctx.fill_preserve()
        _stroke(ctx, 2.6, INK, 0.9 * ga)
        col = RED if k == "top" else INK_A
        r_b = state(*bef)["R"]
        p1 = f"赤÷青 前 ×{xtxt(r_b)} → "
        p2 = f"後 ×{xtxt(st['R'])}"
        text(ctx, p1, 378, 398, 32, INK, align="left", alpha=ga)
        x2 = 378 + core.text_width(p1, 32)
        text(ctx, p2, x2, 398, 32, col, align="left", alpha=ga)
        if t >= T_VERD:
            u = clamp01((t - T_VERD) / 0.35)
            wl = core.text_width(p2, 32)
            note.pen_circle(ctx, x2 + wl / 2, 398, wl / 2 + 16, 25, col, seed=70 + (k == "bot"), width=4.5, progress=u)
    ctx.restore()

# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.08 * (1 - ease(clamp01(t / 1.1)))               # 冒頭: 場面が少し寄ったところから引く（下端を基準に）
    ctx.save()
    if z > 1.0:
        ctx.translate(540, 1440)
        ctx.scale(z, z)
        ctx.translate(-540, -1440)
    ctx.push_group()
    for k in ("top", "bot"):
        draw_card(ctx, k, t, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 1万回のマス目（2つ） ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 3
G_Y0 = 640.0
G_X = {"air": 100.0, "sun": 565.0}                 # 左＝空気（A）、右＝太陽（C）
_GRID = {}


def flags(key):
    """各回の 赤さが1割以上増えたか（1/0）。key: 'sun' = ① 太陽だけ低く、'air' = ② 空気だけ澄ませる"""
    r = results()
    g = r["ph"]["g1"] if key == "sun" else r["ph"]["g2"]
    return (g >= RULE_MIN).astype(int)


def grid_surface(key, n):
    kk = (key, int(n) // G_COLS)
    if kk in _GRID:
        return _GRID[kk]
    if len(_GRID) > 6:
        _GRID.clear()
    fl = flags(key)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(NO_COL), bgra(UP_COL)], np.uint8)
    m = len(fl) if n >= len(fl) else (int(n) // G_COLS) * G_COLS
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[fl[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[kk] = (surf, keep)
    return _GRID[kk]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def dec_text(p):
    """減った回の割合（1割以上減った回）"""
    if p < 0.005:
        return "（減った回は なし）"
    return f"（{pcs(p)}は 減った）"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    pr = clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    titles = {"sun": "太陽だけ 低くする", "air": "空気だけ 澄ませる"}
    for key in ("sun", "air"):
        n = N_TRIAL * pr
        surf, _ = grid_surface(key, n)
        gx = G_X[key]
        cx = gx + G_COLS * G_CELL / 2
        ctx.set_source_surface(surf, gx, G_Y0)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(gx - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
        ctx.stroke()
        text(ctx, titles[key], cx, 604, 34, INKC[key], alpha=a)
        if t >= T_G1 + 0.1:
            u = ease_out((t - T_G1 - 0.1) / 0.3) * a
            p = sh["inc1"] if key == "sun" else sh["inc2"]
            dd = sh["dec1"] if key == "sun" else sh["dec2"]
            text(ctx, f"増えた {pcs(p)}", cx, 922, 50, RED if key == "sun" else INK_A, alpha=u)
            text(ctx, dec_text(dd), cx, 968, 30, INK, bold=False, alpha=u)
    # 凡例（色の見本）と 1マス＝1回
    lg = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    fill(ctx, hexrgb(UP_COL, a * lg))
    ctx.rectangle(100, 1012, 28, 28)
    ctx.fill()
    fill(ctx, hexrgb(NO_COL, a * lg))
    ctx.rectangle(460, 1012, 28, 28)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
    ctx.set_line_width(2)
    for xx in (100, 460):
        ctx.rectangle(xx, 1012, 28, 28)
        ctx.stroke()
    text(ctx, "赤さが1割以上 増えた回", 138, 1026, 28, INK, align="left", bold=False, alpha=a * lg)
    text(ctx, "増えなかった回", 498, 1026, 28, INK, align="left", bold=False, alpha=a * lg)
    text(ctx, "1マス＝1回", 740, 1026, 28, INK, align="left", bold=False, alpha=a * lg)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["a1"], sh["a2"])


def reason_text():
    sh = shown()
    k = answer_key()
    l1 = f"太陽だけを低くすると、赤さは ×{xtxt(sh['m1'])}になる。"
    if sh["m2"] < 1.0:
        l2 = f"空気だけを澄ませると、赤さは ×{xtxt(sh['m2'])}に減る。"
    else:
        l2 = f"空気だけを澄ませると、赤さは ×{xtxt(sh['m2'])}になる。"
    return f"赤さ＝赤い光÷青い光\n{l1}\n{l2}\n（×は中央値＝1万回の ちょうど真ん中の値）"


TW_Q = "では、空気が澄んでいると\n夕日はどうなる？"


def tw_a():
    sh = shown()
    g = sh["red_gain"]
    return f"同じ低い太陽で、空気だけをくらべる。\n澄んだ空気だと、赤い光そのものは約{xtxt(g)}倍明るい。\n青い光も多く残るので、赤さの比は下がる。"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 520, 1120, 44, "yellow", fg=RED, a=b, tilt=-0.02)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 520, 1282, 30, "blue", a=c, tilt=0.012)
        text(ctx, "観測で確かめた例は見つからず、計算での見立て", 520, 1428, 26, PENCIL, bold=False, alpha=c)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 520, 1250, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        for k_, (ln_, col_) in enumerate(zip(tw_a().split("\n"), (INK, RED, INK))):
            text(ctx, ln_, 520, 1356 + 36 * k_, 30, col_, alpha=e)


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


def big3_size(max_w=820.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


CD_X, CD_Y = 590.0, 1015.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に2枚の絵（0秒目から光が流れ、場面が寄った所から引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(820.0), 64.0)                         # 4行を iPhone で隠れる上端（y370）より下に収める
        ys = (410, 488, 566, 644)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q3[-1], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, 694, 565 + w2 / 2 + 6, 690, RED, seed=5, width=8,
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
        wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
        sz = min(47.0, 100.0 * 850.0 / wmax)
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
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "今日の夕焼け、\n何色でしたか？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    wind = noise_band(t_end, 120, 3, 2.2)                  # 土手を抜ける風（ふわー）
    tt = np.arange(len(wind)) / SR
    env_ = (0.7 + 0.3 * np.sin(2 * np.pi * 0.17 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, wind * env_, 0.5)
    k = 0.0
    while k < t_end - 0.5:                                # 光が散るきらっ
        mx.add(k, tick(2600, 0.02), 0.12)
        k += 0.9 if k < T_GO else 0.6
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.30)
    mx.add(T_VERD + 0.2, bell(523.3, 1.2), 0.45)
    mx.add(T_VERD + 0.5, bell(784.0, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                        # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    mx.add(T_TW2, blip(659.3, 0.14), 0.3)
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


def _chapman_ref(h_deg, H_km, n=400000):
    """chapman() の答え合わせ。別の刻み方（等間隔の細かい足し算・math だけ）"""
    z = math.radians(90.0 - h_deg)
    top = R_EARTH + 14.0 * H_km
    smax = math.sqrt(top ** 2 - (R_EARTH * math.sin(z)) ** 2) - R_EARTH * math.cos(z)
    ds = smax / n
    tot = 0.0
    for j in range(n):
        s_ = (j + 0.5) * ds
        r_ = math.sqrt(R_EARTH ** 2 + s_ ** 2 + 2.0 * R_EARTH * s_ * math.cos(z))
        tot += math.exp(-(r_ - R_EARTH) / H_km) * ds
    return tot / H_km


def run_checks():
    sh = shown()
    r = results()
    p, ph = r["p"], r["ph"]
    checks = []
    # (1) 式の照合
    for z, ref in ((80, 5.59), (85, 10.31), (88, 19.43), (90, 37.92)):
        checks.append((f"エアマス K&Y 天頂角{z}°（Wikipedia の表の値）", float(airmass_ky(90 - z)), ref, 0.02 * ref))
    checks.append(("エアマス 真上（高さ90°）= 1", float(airmass_ky(90.0)), 1.0, 0.002))
    for lam_ in (0.45, 0.65):                      # 別の式（Hansen & Travis 型の近似・係数は記憶による＝FACTCHECK に書いた）との一致
        ht = 0.008569 * lam_ ** -4 * (1 + 0.0113 * lam_ ** -2 + 0.00013 * lam_ ** -4)
        checks.append((f"レイリー光学的厚さ {lam_}µm: 式30 と 別の近似式が合う（割合）", float(tau_rayleigh(lam_)) / ht, 1.0, 0.01))
    checks.append(("レイリー光学的厚さ 0.5µm（AMS 用語集の約0.145）", float(tau_rayleigh(0.5)), 0.145, 0.004))
    ex_ = np.log(tau_rayleigh(0.45) / tau_rayleigh(0.65)) / np.log(0.65 / 0.45)
    checks.append(("レイリー散乱の波長の指数（0.45〜0.65µm）→ 約4.1（λ⁻⁴ より少し大きい）", float(ex_), 4.1, 0.15))
    for hh_, tol in ((5.0, 0.12), (2.0, 0.12)):
        c1 = float(chapman(hh_, H_AIR_KM)[0])
        k1 = float(airmass_ky(hh_))
        checks.append((f"丸い地球の積分（H=8.4km）と K&Y が合う 高さ{hh_:.0f}°（割合）", c1 / k1, 1.0, tol))
    checks.append(("丸い地球の積分 真上（高さ90°）= 1", float(chapman(90.0, 1.5)[0]), 1.0, 0.002))
    for hh_, HH in ((3.0, 1.5), (8.0, 1.0), (1.0, 2.0)):
        c1 = float(chapman(hh_, HH)[0])
        c2 = _chapman_ref(hh_, HH)
        checks.append((f"積分の答え合わせ（別の刻み）高さ{hh_:.0f}°・H={HH}km（割合）", c1 / c2, 1.0, 0.003))
    # (2) 配列版の物理と、math だけで1回ぶんを計算し直した値が合う
    mx = 0.0
    for i in (0, 7, 123, 4567):
        for hk, air in (("lo", "dusty"), ("hi", "clean")):
            hh_ = float(p["h_" + hk][i])
            zz = 90.0 - hh_
            mR = 1.0 / (math.cos(math.radians(zz)) + 0.50572 * (96.07995 - zz) ** -1.6364)
            mA = _chapman_ref(hh_, float(p["Hc"][i]), 200000)
            vals = []
            for lam in (LAM_R, LAM_B):
                tr = 0.0021520 * (1.0455996 - 341.29061 * lam ** -2 - 0.90230850 * lam ** 2) / (1.0 + 0.0027059889 * lam ** -2 - 85.968563 * lam ** 2)
                ta = float(p["t_" + air][i]) * (lam / 0.5) ** (-float(p["a_" + air][i]))
                vals.append(-(tr * mR + ta * mA))
            ref = vals[0] - vals[1]
            mx = max(mx, abs(ref - float(ph["c"][(hk, air)]["lnR"][i])))
    checks.append(("ln R: 配列版 − 計算し直し（4回×2条件の最大）", mx, 0.0, 5e-3))
    # (3) 太陽の高さの幅（冬の東京）
    h40, _ = sun_set_height(40)
    h15, _ = sun_set_height(15)
    checks.append(("日没の40分前の高さが「高め」の幅（6〜10°）の中", float(H_HIGH[0] <= h40 <= H_HIGH[1] + 1), 1.0, 0.0))
    checks.append(("日没の15分前の高さが「低い」の幅（1〜3°）の中", float(H_LOW[0] <= h15 <= H_LOW[1]), 1.0, 0.0))
    checks.append(("日没（上の縁が地平線）の高さ = −0.83°", sun_set_height(0)[0], -0.833, 0.01))
    # (4) 向き: 太陽を低くすると赤くなる・赤い光の残りは減る（全回）
    c = ph["c"]
    checks.append(("太陽を低くすると 赤÷青は増える（全回・4条件のうち2つ）",
                   float(np.all(c[("lo", "dusty")]["lnR"] > c[("hi", "dusty")]["lnR"]) and np.all(c[("lo", "clean")]["lnR"] > c[("hi", "clean")]["lnR"])), 1.0, 0.0))
    checks.append(("太陽を低くすると 赤い光の残りは減る（全回）", float(np.all(c[("lo", "dusty")]["lnT_r"] < c[("hi", "dusty")]["lnT_r"])), 1.0, 0.0))
    checks.append(("澄んだ空気のほうが 赤い光の残りは多い（全回・低い太陽）", float(np.all(c[("lo", "clean")]["lnT_r"] > c[("lo", "dusty")]["lnT_r"])), 1.0, 0.0))
    checks.append(("澄んだ空気は 青い光も多く残る（全回・低い太陽）", float(np.all(c[("lo", "clean")]["lnT_b"] > c[("lo", "dusty")]["lnT_b"])), 1.0, 0.0))
    # (5) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key = answer_by_rule(sh["a1"], sh["a2"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（太陽が低いから・空気が澄んでいるから）",
                   float(LABELS.index(NAME["sun"]) * 10 + LABELS.index(NAME["air"])),
                   float("ABC".index(TAG["sun"]) * 10 + "ABC".index(TAG["air"])), 0.0))
    checks.append(("規則の道具: ①が大きく②が負 → 太陽", float(answer_by_rule(2.0, -0.5) == "sun"), 1.0, 0.0))
    checks.append(("規則の道具: ②が大きく①が小さい → 空気", float(answer_by_rule(0.3, 1.0) == "air"), 1.0, 0.0))
    checks.append(("規則の道具: どちらも小さい → ほぼ同じ", float(answer_by_rule(0.05, -0.05) == "same"), 1.0, 0.0))
    checks.append(("規則の道具: 近い → ほぼ同じ", float(answer_by_rule(1.0, 0.8) == "same"), 1.0, 0.0))
    # (6) マス目が1万回のぜんぶで、割合が同じ
    checks.append(("マス目に収まる（回数 ≦ 125×80）", float(N_TRIAL <= G_COLS * G_ROWS), 1.0, 0.0))
    checks.append(("マス目の増えた割合 ①", float(flags("sun").mean()), sh["inc1"], 1e-12))
    checks.append(("マス目の増えた割合 ②", float(flags("air").mean()), sh["inc2"], 1e-12))
    checks.append(("マス目の回数 = 1万", float(len(flags("sun"))), float(N_TRIAL), 0.0))
    # (7) 見本は1万回の中の1回で、絵の値が1万回の値と同じ
    S = sample()
    i = S["i"]
    for nm, (hh_, ww_), key_ in (("上の前（高め・ちり）", (S["h_hi"], 0.0), ("hi", "dusty")), ("上の後・下の前（低い・ちり）", (S["h_lo"], 0.0), ("lo", "dusty")),
                                 ("下の後（低い・澄）", (S["h_lo"], 1.0), ("lo", "clean"))):
        checks.append((f"見本 {nm} の赤÷青（絵）が 1万回の値と同じ", math.log(state(hh_, ww_)["R"]), float(c[key_]["lnR"][i]), 0.02))
    checks.append(("見本の ① が中央値の近く", S["g1"], sh["a1"], 0.15 * abs(sh["a1"])))
    checks.append(("見本の ② が中央値の近く", S["g2"], sh["a2"], 0.2 * abs(sh["a2"])))
    checks.append(("見本の低い太陽の高さが「低い」の幅", float(H_LOW[0] <= S["h_lo"] <= H_LOW[1]), 1.0, 0.0))
    checks.append(("見本の高めの太陽の高さが「高め」の幅", float(H_HIGH[0] <= S["h_hi"] <= H_HIGH[1]), 1.0, 0.0))
    b_, a_ = cond_pair("top")
    checks.append(("上の絵（太陽だけ低く）: 空気は同じ・赤÷青は増える", float(b_[1] == a_[1] and state(*a_)["R"] > state(*b_)["R"]), 1.0, 0.0))
    b_, a_ = cond_pair("bot")
    checks.append(("下の絵（空気だけ澄ませる）: 太陽の高さは同じ・赤÷青は変わる（減る）", float(b_[0] == a_[0] and state(*a_)["R"] < state(*b_)["R"]), 1.0, 0.0))
    checks.append(("上の絵のタグ = 太陽が低いから の記号、下の絵のタグ = 空気が澄んでいるから の記号",
                   float("ABC".index(TAG[PANEL_KEY["top"]]) * 10 + "ABC".index(TAG[PANEL_KEY["bot"]])),
                   float(LABELS.index(NAME["sun"]) * 10 + LABELS.index(NAME["air"])), 0.0))
    checks.append(("マス目の減った割合 ①②（表示の数字がモデルと同じ）", float(flags("sun").size and (ph["g1"] <= -RULE_MIN).mean() == sh["dec1"] and (ph["g2"] <= -RULE_MIN).mean() == sh["dec2"]), 1.0, 0.0))
    # 問い（1行目の定数）が 3行同じ大きさで収まる
    s3 = big3_size(820.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    s_top = min(47.0, 100.0 * 850.0 / max(core.text_width(l, 100.0) for l in BIG_Q))
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))    # (8) ひねりの数字
    checks.append(("ひねり: 澄んだ空気のほうが 赤い光は明るい（中央値の倍率 > 1）", float(sh["red_gain"] > 1.0), 1.0, 0.0))
    # (9) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


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


def report_full():
    sh = shown()
    S = sample()
    print(f"長さ {DURATION:.1f}秒  沈み終わり {T_VERD:.1f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print(f"  見本: 回{S['i']} 高め{S['h_hi']:.1f}° 低い{S['h_lo']:.1f}° ちり τ0.5={S['dusty']['t05']:.2f} α={S['dusty']['alpha']:.2f} 澄 τ0.5={S['clean']['t05']:.2f} α={S['clean']['alpha']:.2f}")
    for k in ("top", "bot"):
        b_, a_ = cond_pair(k)
        print(f"  {k}（{PANEL_TITLE[k][0]}）: 前 赤÷青 ×{state(*b_)['R']:.1f} → 後 ×{state(*a_)['R']:.1f}")
    print(f"  問い1行目「{Q_LINE1}」{len(Q_LINE1)}字  3行の文字 {big3_size(820.0):.0f}px  上の2行 {min(47.0, 100.0 * 850.0 / max(core.text_width(l, 100.0) for l in BIG_Q)):.0f}px")
    print(f"  減った回: ① {dec_text(sh['dec1'])}  ② {dec_text(sh['dec2'])}")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a().replace("\n", " "))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, 6.5, 8.5, 11.0, 13.5, T_VERD + 0.3, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.6, T_TW + 0.8, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
