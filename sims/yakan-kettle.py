"""やかん（ガス）と電気ケトル、500mLのお湯はどっちが早く沸く？ 同時にスタートして1万回。— 2026-10-19 作成（公開予定 10/24）

くらべるのは「早さ」だけ（お金のことはくらべない。画面にも概要欄にも書かない）。

モデル（どちらも「中の水と入れ物が同じ温度で上がる」かたまりのモデル）
      (水の熱容量 + 入れ物の熱容量) × dT/dt = 入る熱 − UA × (T − 部屋の温度)
  → 式で解ける: T(t) = Tr + P/UA − (P/UA − (T0 − Tr)) × exp(−UA t / C)。100℃になる時刻もこの式から出す。
  水: 500mL × 0.9〜1.1（目分量）。比熱 4.186 kJ/(kg·K)、1mL = 1g。沸点は 100℃。
  水道水の温度（季節）: 月を12か月から等確率で選び、その月の平均 + ばらつき（標準偏差 1.5℃）。
      月の平均は 東京都水道局「水質年報 令和5年度」第5 給水栓の水質 の水温（4月〜3月）
      15.8 / 18.6 / 21.9 / 26.7 / 28.6 / 27.5 / 22.0 / 17.6 / 12.8 / 10.0 / 9.9 / 10.7 ℃（年間 8.0〜29.1℃）。
  部屋の温度: 水道水 + 2〜8℃（12〜30℃で切る）。熱が逃げるぶんにしか効かない。
  やかん（ガス・強火）:
      バーナー（等確率）: 標準バーナーを全開 2.3〜3.0 kW ／ 強火力バーナーを、炎がやかんの底からはみ出ない強火で 2.8〜4.2 kW。
        ・杉山 2007（横浜国立大学 教育人間科学部紀要）表1: 家庭用ビルトインこんろの カタログ値 強火力 4.20〜4.24 kW、標準 2.45〜2.97 kW。
          同論文: ガスの強火は「炎が鍋底からはみ出ない最大火力」。
      炎の熱のうち、やかんに入る割合 η = (0.40〜0.52) − 0.04 × (Q − 2.5 kW)  （火が強いほど、はみ出す熱が増えて下がる）
        ・杉山 2007 表4・表5: ステンレスのやかん（810g・2.0L）で水1Lを沸かす。中くらいより強めの火で 5分25秒〜6分50秒、
          ガス 0.86〜0.93 MJ。水と入れ物が受け取った熱から割ると 40〜44%（室温の水と見た場合）。
        ・同論文: カタログの熱効率はガスこんろで最も良いもので56%（試験用のなべ・決まった条件。実際の使い方では下がる）。
        ・石谷ほか 1983（北見工業大学研究報告）: ステンレスの容器・水1.5L・約2.9kW で 31〜39%。
          「同じ容器なら、ガスを少なくするほど・水が多いほど効率が上がる」→ 火が強いほど η を下げる。水量による上がりは入れない（やかんに辛め）。
      やかんの重さ: ステンレス（60%）0.6〜1.1 kg・比熱 0.50 ／ アルミ（40%）0.35〜0.7 kg・比熱 0.90 kJ/(kg·K)。
      熱が逃げる UA: 0.6〜1.5 W/K。「沸いた」＝ 水が100℃になった時刻（ピーと鳴る・湯気が出る）。
  電気ケトル（100V）:
      消費電力 1,200〜1,300 W（一様）。ヒーターの熱のうち水と入れ物に入る割合 0.92〜0.98。
      入れ物（底の金属板など）の熱容量 200〜350 J/K。UA 0.4〜1.0 W/K（樹脂の胴）。
      100℃になってから、湯気で温度センサーが働いてスイッチが切れるまで 5〜20秒（その間も熱は入る）。「沸いた」＝スイッチが切れた時刻。
        ・名古屋市消費生活センター「電気ケトル」商品テスト（2007）: 1250W の2台で 0.5L・15℃ が 3分05秒・3分12秒、
          1.2L・15℃ が 6分32秒・6分43秒。「沸騰し始める時間には大差は無いが、電源が切れるまでの時間は若干ばらつき」。
          ほかに 1200W（3分21秒）・900W（3分57秒）・1450W（2分48秒）。この回は多い 1,200〜1,300 W だけにした。
        → 真ん中の値で、この2つの測定（0.5L と 1.2L）を ±5% で再現することを run_checks で確かめる。
  スタート: 同じ水を同時に、火をつける／スイッチを入れる（火がつくまでの時間・水を入れる時間は入れない）。

問い: 「やかんと電気ケトル、/ どっちが早く沸く？」（前提「水500mLずつ・ガスは強火・同時にスタート」）
      A やかん（ガス） ／ B ほぼ同じ ／ C 電気ケトル
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「やかんが先に沸いた回」の割合 p と、沸いた時刻の差（電気ケトル − やかん）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 15秒 なら A、p ≤ 40% かつ g ≤ −15秒 なら C、それ以外は B。
ひねり: 「では、1.5L沸かすなら？」 同じ1万回（同じ台所・同じ道具）で、水だけ 1.5L × 0.9〜1.1 に（ケトルは1.5L入るものとする）。
締め: 「あなたの家は、/ やかん？ケトル？」（答えは出さない）

乱数の種は見本（並んで沸く2つ）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "yakan-kettle"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
C_W = 4186.0                                      # 水の比熱 J/(kg·K)
T_BOIL = 100.0
VOL = 0.500                                       # L（= kg）
VOL_TW = 1.500                                    # ひねり
VOL_JIT = (0.9, 1.1)
TAP_MONTH = (15.8, 18.6, 21.9, 26.7, 28.6, 27.5, 22.0, 17.6, 12.8, 10.0, 9.9, 10.7)   # 4月〜3月（東京都水道局 R5 年報）
TAP_SD = 1.5
ROOM_ADD, ROOM_CLIP = (2.0, 8.0), (12.0, 30.0)
# やかん（ガス）
P_STD_BURNER = 0.5                                # 標準バーナーを使う割合
Q_STD, Q_HI = (2.3, 3.0), (2.8, 4.2)              # kW
ETA0, ETA_SLOPE, ETA_REF = (0.40, 0.52), 0.04, 2.5
P_STAINLESS = 0.6
M_SUS, M_AL = (0.6, 1.1), (0.35, 0.7)             # kg
C_SUS, C_AL = 500.0, 900.0                        # J/(kg·K)
UA_GAS = (0.6, 1.5)                               # W/K
# 電気ケトル
P_ELE = (1200.0, 1300.0)                          # W
ETA_ELE = (0.92, 0.98)
C_ELE = (200.0, 350.0)                            # J/K
UA_ELE = (0.4, 1.0)                               # W/K
OFF_DELAY = (5.0, 20.0)                           # 秒

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 15.0


def answer_by_rule(p_gas, gap_med):
    """p_gas = やかんが先に沸いた回の割合、gap_med = (電気ケトル − やかん) の沸いた時刻の差の真ん中の値（秒）"""
    if p_gas >= RULE_HI and gap_med >= RULE_GAP:
        return 0                                  # A やかん（ガス）
    if p_gas <= RULE_LO and gap_med <= -RULE_GAP:
        return 2                                  # C 電気ケトル
    return 1                                      # B ほぼ同じ


# ---------- 熱の式 ----------

def t_reach(P, C, UA, T0, Tr, Tt=T_BOIL):
    """一定の熱 P[W] が入り、UA[W/K] で部屋 Tr に逃げる。熱容量 C[J/K]。T0 から Tt になる時刻（秒）"""
    P, C, UA, T0, Tr = (np.asarray(x, float) for x in (P, C, UA, T0, Tr))
    Tinf = Tr + P / UA
    return -(C / UA) * np.log((Tinf - Tt) / (Tinf - T0))


def temp_at(t, P, C, UA, T0, Tr):
    Tinf = Tr + P / UA
    return Tinf - (Tinf - T0) * math.exp(-UA * t / C)


def draw_params(rng, n):
    u = lambda lo_hi, k=n: rng.uniform(lo_hi[0], lo_hi[1], k)   # noqa: E731
    month = rng.integers(0, 12, n)
    tap = np.clip(np.array(TAP_MONTH)[month] + rng.normal(0, TAP_SD, n), 3.0, 32.0)
    room = np.clip(tap + u(ROOM_ADD), *ROOM_CLIP)
    jit = u(VOL_JIT)
    std = rng.uniform(0, 1, n) < P_STD_BURNER
    q = np.where(std, u(Q_STD), u(Q_HI)) * 1000.0
    eta = u(ETA0) - ETA_SLOPE * (q / 1000.0 - ETA_REF)
    sus = rng.uniform(0, 1, n) < P_STAINLESS
    c_kettle = np.where(sus, u(M_SUS) * C_SUS, u(M_AL) * C_AL)
    return dict(month=month, tap=tap, room=room, jit=jit, std=std, q=q, eta=eta, sus=sus, c_gas=c_kettle,
                ua_gas=u(UA_GAS), p_ele=u(P_ELE), eta_ele=u(ETA_ELE), c_ele=u(C_ELE), ua_ele=u(UA_ELE),
                delay=u(OFF_DELAY))


def boil_times(p, vol):
    """沸いた時刻（秒）: やかん = 100℃になった時刻、電気ケトル = 100℃になってからスイッチが切れた時刻"""
    m = vol * p["jit"]
    t_gas = t_reach(p["q"] * p["eta"], m * C_W + p["c_gas"], p["ua_gas"], p["tap"], p["room"])
    t_e100 = t_reach(p["p_ele"] * p["eta_ele"], m * C_W + p["c_ele"], p["ua_ele"], p["tap"], p["room"])
    return t_gas, t_e100, t_e100 + p["delay"]


SEED_MAIN = 20261024
_RES = {}


def results():
    if not _RES:
        p = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
        g, e100, e = boil_times(p, VOL)
        g2, _, e2 = boil_times(p, VOL_TW)
        _RES["m"] = dict(p=p, gas=g, e100=e100, ele=e, gas_tw=g2, ele_tw=e2)
    return _RES["m"]


def shown():
    r = results()
    p = r["p"]
    gap = r["ele"] - r["gas"]
    gap2 = r["ele_tw"] - r["gas_tw"]
    win = r["gas"] < r["ele"]
    win2 = r["gas_tw"] < r["ele_tw"]
    std = p["std"]
    summer = np.isin(p["month"], (3, 4, 5))       # 7・8・9月
    winter = np.isin(p["month"], (9, 10, 11))     # 1・2・3月
    eff_gas = (VOL * p["jit"] * C_W + p["c_gas"]) * (T_BOIL - p["tap"]) / (p["q"] * r["gas"])
    return dict(p_gas=float(win.mean()), n_gas=int(win.sum()), n_ele=int((~win).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_gas=float(np.median(r["gas"])), med_ele=float(np.median(r["ele"])),
                within=float(np.mean(np.abs(gap) < RULE_GAP)),
                p_std=float(win[std].mean()), p_hi=float(win[~std].mean()),
                gap_std=float(np.median(gap[std])), gap_hi=float(np.median(gap[~std])),
                p_summer=float(win[summer].mean()), p_winter=float(win[winter].mean()),
                p_tw=float(win2.mean()), gap_tw=float(np.median(gap2)), gap_tw_q=np.percentile(gap2, [10, 90]),
                med_gas_tw=float(np.median(r["gas_tw"])), med_ele_tw=float(np.median(r["ele_tw"])),
                p_tw_std=float(win2[std].mean()), p_tw_hi=float(win2[~std].mean()),
                eff_gas_q=np.percentile(eff_gas, [10, 50, 90]),
                kw_gas_q=np.percentile(p["q"] * p["eta"], [10, 50, 90]),
                kw_ele_q=np.percentile(p["p_ele"] * p["eta_ele"], [10, 50, 90]),
                tap_q=np.percentile(p["tap"], [0, 50, 100]))


def mmss(s):
    s = int(round(s))
    return f"{s // 60}分{s % 60:02d}秒"


def report():
    sh = shown()
    print(f"500mL: やかんが先 {sh['p_gas']:.4f}（{sh['n_gas']}回 / ケトルが先 {sh['n_ele']}回）  差の中央値 {sh['gap_med']:+.1f}秒  "
          f"平均 {sh['gap_mean']:+.1f}  10/25/75/90% {np.round(sh['gap_q'], 1)}  差15秒以内 {sh['within']:.3f}")
    print(f"  答え {'ABC'[answer_by_rule(sh['p_gas'], sh['gap_med'])]}")
    print(f"  中央値 やかん {sh['med_gas']:.1f}秒（{mmss(sh['med_gas'])}）/ ケトル {sh['med_ele']:.1f}秒（{mmss(sh['med_ele'])}）")
    print(f"  標準バーナー: やかんが先 {sh['p_std']:.3f} 差 {sh['gap_std']:+.1f}  強火力: {sh['p_hi']:.3f} 差 {sh['gap_hi']:+.1f}")
    print(f"  夏(7-9月) やかんが先 {sh['p_summer']:.3f}  冬(1-3月) {sh['p_winter']:.3f}")
    print(f"  やかんの効率 10/50/90% {np.round(sh['eff_gas_q'], 3)}  入る熱 kW やかん {np.round(sh['kw_gas_q'] / 1000, 2)} "
          f"ケトル {np.round(sh['kw_ele_q'] / 1000, 2)}  水温 {np.round(sh['tap_q'], 1)}")
    print(f"1.5L: やかんが先 {sh['p_tw']:.4f}  差の中央値 {sh['gap_tw']:+.1f}秒 10/90% {np.round(sh['gap_tw_q'], 1)}  "
          f"中央値 やかん {mmss(sh['med_gas_tw'])} / ケトル {mmss(sh['med_ele_tw'])}  標準 {sh['p_tw_std']:.3f} 強火力 {sh['p_tw_hi']:.3f}")


def calib():
    """名古屋市のテスト（1250W・15℃）と杉山 2007（ガス・やかん810g・1L）を、真ん中の値で再現できるか"""
    mid = lambda a: (a[0] + a[1]) / 2   # noqa: E731
    out = {}
    for vol, meas in ((0.5, (185.0, 192.0)), (1.2, (392.0, 403.0))):
        t = float(t_reach(1250.0 * mid(ETA_ELE), vol * C_W + mid(C_ELE), mid(UA_ELE), 15.0, 20.0)) + mid(OFF_DELAY)
        out[f"ele{vol}"] = (t, meas)
    q = 2.5e3
    eta = mid(ETA0) - ETA_SLOPE * (q / 1000 - ETA_REF)
    t = float(t_reach(q * eta, 1.0 * C_W + 0.81 * C_SUS, mid(UA_GAS), 17.0, 20.0))
    out["gas1.0"] = (t, (325.0, 410.0))
    return out


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    for k, (t, meas) in calib().items():
        print(f"  照合 {k}: モデル {t:.0f}秒 / 測定 {meas}")
    sys.exit(0)


# =====================================================================
# 見本（並んで沸く2つ）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 差が真ん中の値の近く（±3秒）、水道水が真ん中あたり（15〜20℃）、水がほぼ500mL。その中で差が真ん中に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    gap = r["ele"] - r["gas"]
    cand = np.nonzero((np.abs(gap - sh["gap_med"]) < 3.0) & (p["tap"] > 15) & (p["tap"] < 20)
                      & (np.abs(p["jit"] - 1) < 0.03))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    q = {k: (v[i].item() if hasattr(v[i], "item") else v[i]) for k, v in p.items()}
    m = VOL * q["jit"]
    _SAMPLE = dict(i=i, p=q, t_gas=float(r["gas"][i]), t_e100=float(r["e100"][i]), t_ele=float(r["ele"][i]),
                   gap=float(gap[i]),
                   gas=(q["q"] * q["eta"], m * C_W + q["c_gas"], q["ua_gas"], q["tap"], q["room"]),
                   ele=(q["p_ele"] * q["eta_ele"], m * C_W + q["c_ele"], q["ua_ele"], q["tap"], q["room"]))
    return _SAMPLE


def T_gas(tau):
    s = sample()
    return T_BOIL if tau >= s["t_gas"] else temp_at(max(0.0, tau), *s["gas"])


def T_ele(tau):
    s = sample()
    return T_BOIL if tau >= s["t_e100"] else temp_at(max(0.0, tau), *s["ele"])


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    p = s["p"]
    print("見本", s["i"], "水", round(p["tap"], 1), "℃ 部屋", round(p["room"], 1), "量", round(VOL * p["jit"] * 1000), "mL",
          "バーナー", "標準" if p["std"] else "強火力", round(p["q"]), "W η", round(p["eta"], 3),
          "やかん", round(p["c_gas"]), "J/K", "ケトル", round(p["p_ele"]), "W", round(p["eta_ele"], 3),
          "やかん", mmss(s["t_gas"]), "ケトル", mmss(s["t_ele"]), "差", round(s["gap"], 1))
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
note.DATE = "10.24"                               # 日付欄（公開予定日）

COL_A, INK_A = "#8fbbe8", "#2f63a8"               # A やかん（ガス・青い炎）
COL_C, INK_C = "#f4ad6a", "#b8601a"               # C 電気ケトル（だいだいのランプ）
COL_TW = "#5f93cf"                                # ひねり（1.5L）の棒
FLAME_O, FLAME_I = "#4f86e0", "#a9d4ff"
STEEL, STEEL_D = "#d9dfe7", "#aab4c2"
KET_E = "#fbfaf6"                                 # 電気ケトルの胴（白い樹脂）
TILE, TILE_L = "#e4ebf2", "#b9c6d4"
WOOD, WOOD_D = "#e3c99f", "#c7a675"
STEAM = "#ffffff"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_X = 1.0                                     # 冒頭は実際の速さ
SLOW_X = 3.0                                      # 沸く前後はゆっくり
SLOW_PRE, SLOW_POST = 7.0, 1.5                    # 沸く何秒前（実際の秒）から何秒後までゆっくり
RACE_LEN = 11.5                                   # T_GO から2つとも沸くまで（動画の秒）
BIG_Q = ["やかんと電気ケトル、", "どっちが早く沸く？"]
DETAIL = "水500mLずつ・ガスは強火・同時にスタート"
LABELS = ["やかん（ガス）", "ほぼ同じ", "電気ケトル"]
CORRECT = 0                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
NAME = {"a": "やかん", "c": "電気ケトル"}
TAG = {"a": "A", "c": "C"}
COLS = {"a": COL_A, "c": COL_C}
INKC = {"a": INK_A, "c": INK_C}

# 場面（場面の座標: 幅1080・高さ SCENE_H。画面へは layout で縮めて置く）
SCENE_H = 760.0
CX = 580.0
COUNTER_Y = 560.0
GX = 330.0                                        # やかんの中心
EX = 790.0                                        # 電気ケトルの中心
TH_GX, TH_EX = 545.0, 990.0                       # 温度計（湯気のかからない右側）
TH_TOP, TH_BOT = 205.0, 470.0                     # 100℃ と 0℃ の高さ
LAY_INTRO = (1.0, 690.0)
LAY_RACE = (0.75, 572.0)
ZOOM0, ZOOM_T = 1.42, 1.6
ZOOM_F = (560.0, 470.0)


def setup():
    global TL, RACE_X, T_FIN1, T_FIN2, T_RACE_END, T_G0, T_G1, T_REV, T_WHY, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_gas"], s["t_ele"]))

    def build(rx):
        ts = np.arange(0, 90, 1 / 300)
        tau = np.zeros_like(ts)
        v, sp = 0.0, INTRO_X
        for k in range(1, len(ts)):
            t = ts[k]
            if t < T_GO:
                target = INTRO_X
            else:
                target = INTRO_X + (rx - INTRO_X) * ease((t - T_GO) / 0.8)
                if any(f - SLOW_PRE <= v <= f + SLOW_POST for f in fins):
                    target = min(target, SLOW_X)
            sp += (target - sp) * min(1.0, (1 / 300) / 0.25)     # 速さは 0.25秒かけて変える
            v += sp / 300
            tau[k] = v
        return ts, tau

    lo, hi = 2.0, 80.0
    for _ in range(30):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        t_end = float(np.interp(fins[1], tau, ts))
        if t_end > T_GO + RACE_LEN:
            lo = mid
        else:
            hi = mid
    RACE_X = hi
    ts, tau = build(RACE_X)
    TL = dict(t=ts, tau=tau)
    T_FIN1 = float(np.interp(fins[0], tau, ts))
    T_FIN2 = float(np.interp(fins[1], tau, ts))
    T_RACE_END = T_FIN2 + 2.2
    T_G0 = T_RACE_END
    T_G1 = T_G0 + 2.4
    T_REV = T_G1 + 0.8
    T_WHY = T_REV + 3.3
    T_TW = T_WHY + 4.2
    T_TW_RUN = T_TW + 2.5
    T_Q = T_TW_RUN + 5.6
    DURATION = T_Q + 3.8


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    return float(np.interp(tau, TL["tau"], TL["t"]))


def speed_now(t):
    return (tau_of(t + 0.02) - tau_of(t - 0.02)) / 0.04 if t > 0.03 else INTRO_X


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


# ---------- 絵: 台所 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def draw_kitchen(ctx):
    fill(ctx, hexrgb("#f7f4ec", 0.9))              # 壁
    ctx.rectangle(-200, -200, W + 400, COUNTER_Y + 200)
    ctx.fill()
    ctx.set_line_width(2)
    step = 76
    for i in range(-3, 18):                        # タイル
        for j in range(-3, 8):
            x, y = i * step + 10, COUNTER_Y - 6 - (j + 1) * step
            fill(ctx, hexrgb(TILE, 0.9))
            core.rrect(ctx, x + 3, y + 3, step - 6, step - 6, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(TILE_L, 0.8))
            ctx.stroke()
    fill(ctx, hexrgb(WOOD))                        # 台の天板と戸棚
    ctx.rectangle(-200, COUNTER_Y, W + 400, 26)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    fill(ctx, hexrgb(WOOD_D, 0.85))
    ctx.rectangle(-200, COUNTER_Y + 26, W + 400, SCENE_H)
    ctx.fill()
    for x in (40, 360, 690, 1010):
        ctx.rectangle(x, COUNTER_Y + 44, 300, 260)
        _stroke(ctx, 2.5, INK, 0.5)
        ctx.move_to(x + 130, COUNTER_Y + 70)
        ctx.line_to(x + 170, COUNTER_Y + 70)
        _stroke(ctx, 5, INK, 0.6)


def draw_stove(ctx):
    """ガスこんろ（天板・つまみ・バーナー・五徳）"""
    fill(ctx, hexrgb("#6b7280"))
    core.rrect(ctx, 150, 520, 360, 44, 8)
    ctx.fill_preserve()
    _stroke(ctx, 3.0)
    fill(ctx, hexrgb("#8b93a1"))
    ctx.rectangle(160, 562, 340, 22)
    ctx.fill_preserve()
    _stroke(ctx, 2.5)
    for kx in (215, 445):                          # つまみ
        fill(ctx, hexrgb("#e9edf2"))
        ctx.arc(kx, 573, 9, 0, 2 * math.pi)
        ctx.fill_preserve()
        _stroke(ctx, 2.0)
    fill(ctx, hexrgb("#3d434f"))                   # バーナー
    ctx.save()
    ctx.translate(GX, 516)
    ctx.scale(70, 10)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#2e333c"))        # 五徳
    ctx.set_line_width(7)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for dx in (-118, 118):
        ctx.move_to(GX + dx, 522)
        ctx.line_to(GX + dx * 0.92, 494)
        ctx.line_to(GX + dx * 0.62, 494)
    ctx.stroke()


def draw_flames(ctx, t, a=1.0):
    """青い炎（ゆらぐ）。強火なので底に当たって横に広がる"""
    if a <= 0:
        return
    for layer, (col, sc) in enumerate(((FLAME_O, 1.0), (FLAME_I, 0.55))):
        for k in range(11):
            x = GX - 95 + k * 19
            ph = t * (9.0 + 1.3 * k) + k * 1.7
            h = (32 + 7 * math.sin(ph) + 5 * math.sin(2.3 * ph + k)) * sc
            w = 9.5 * (1 if layer == 0 else 0.55)
            lean = 4 * math.sin(ph * 0.7 + k)
            y0 = 512
            ctx.move_to(x - w, y0)
            ctx.curve_to(x - w, y0 - h * 0.5, x + lean - 2, y0 - h * 0.8, x + lean, y0 - h)
            ctx.curve_to(x + lean + 2, y0 - h * 0.8, x + w, y0 - h * 0.5, x + w, y0)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(col, (0.85 if layer == 0 else 0.95) * a))
            ctx.fill()


# やかんの胴（場面の座標）: 底 y=492、肩 y=405、ふた y=372
def kettle_path(ctx):
    ctx.move_to(GX - 128, 492)
    ctx.curve_to(GX - 140, 455, GX - 120, 405, GX - 70, 392)
    ctx.curve_to(GX - 40, 368, GX + 40, 368, GX + 70, 392)
    ctx.curve_to(GX + 120, 405, GX + 140, 455, GX + 128, 492)
    ctx.close_path()


def ekettle_path(ctx):
    ctx.move_to(EX - 92, 536)
    ctx.line_to(EX - 80, 318)
    ctx.curve_to(EX - 60, 300, EX + 60, 300, EX + 80, 318)
    ctx.line_to(EX + 92, 536)
    ctx.close_path()


WATER_G = 450.0                                    # やかんの水面（500mL）
WATER_E = 470.0                                    # 電気ケトルの水面（500mL。細長いので高さは同じくらい）


def water_col(T):
    c0, c1 = hexrgb("#a9cff0"), hexrgb("#f3b48f")
    f = clamp01((T - 10) / 90)
    return tuple(c0[i] * (1 - f) + c1[i] * f for i in range(3))


def bubble_amt(T):
    return clamp01((T - 55) / 45) ** 1.6


def draw_water(ctx, t, path, x0, x1, y_top, y_bot, T, seed, calm=1.0):
    """断面の水（色は温度で青→だいだい）と泡（熱いほど多い）"""
    ctx.save()
    path(ctx)
    ctx.clip()
    c = water_col(T)
    ctx.set_source_rgba(c[0], c[1], c[2], 0.95)
    ctx.rectangle(x0 - 20, y_top, x1 - x0 + 40, y_bot - y_top + 20)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.6)              # 水面のゆれ
    ctx.set_line_width(3)
    wob = 1.5 + 4.5 * bubble_amt(T) * calm
    for i in range(30):
        x = x0 - 20 + i * (x1 - x0 + 40) / 29
        y = y_top + wob * math.sin(x / 23 + t * 5.0)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.stroke()
    amt = bubble_amt(T) * calm
    rng = np.random.default_rng(seed)
    n = 46
    for k in range(n):
        bx = rng.uniform(x0 + 14, x1 - 14)
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.7, 1.4)
        r = rng.uniform(3, 8)
        if k >= n * amt:
            continue
        u = (t * sp * (0.8 + 1.2 * amt) + ph) % 1.0
        y = y_bot - 6 - u * (y_bot - y_top - 8)
        ctx.set_source_rgba(1, 1, 1, 0.85 * (1 - 0.5 * u))
        ctx.set_line_width(2)
        ctx.arc(bx + 3 * math.sin(t * 6 + k), y, r * (0.6 + 0.6 * u), 0, 2 * math.pi)
        ctx.stroke()
    ctx.restore()


def draw_yakan(ctx, t, T):
    # 取っ手
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(13)
    ctx.move_to(GX - 82, 392)
    ctx.curve_to(GX - 90, 300, GX + 90, 300, GX + 82, 392)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#3a3f4a"))
    ctx.set_line_width(8)
    ctx.move_to(GX - 82, 392)
    ctx.curve_to(GX - 90, 300, GX + 90, 300, GX + 82, 392)
    ctx.stroke()
    # 注ぎ口（左）
    ctx.move_to(GX - 118, 452)
    ctx.curve_to(GX - 165, 440, GX - 185, 405, GX - 200, 372)
    ctx.line_to(GX - 182, 366)
    ctx.curve_to(GX - 170, 395, GX - 150, 420, GX - 112, 425)
    ctx.close_path()
    fill(ctx, hexrgb(STEEL))
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    # 胴
    kettle_path(ctx)
    fill(ctx, hexrgb("#eef2f6"))
    ctx.fill()
    draw_water(ctx, t, kettle_path, GX - 140, GX + 140, WATER_G, 492, T, 11)
    kettle_path(ctx)
    _stroke(ctx, 4.5)
    ctx.set_source_rgba(1, 1, 1, 0.55)             # 光
    ctx.set_line_width(7)
    ctx.move_to(GX + 70, 410)
    ctx.curve_to(GX + 100, 420, GX + 112, 445, GX + 114, 470)
    ctx.stroke()
    # ふたとつまみ
    fill(ctx, hexrgb(STEEL_D))
    ctx.save()
    ctx.translate(GX, 378)
    ctx.scale(52, 10)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill_preserve()
    _stroke(ctx, 3)
    fill(ctx, hexrgb("#3a3f4a"))
    core.rrect(ctx, GX - 13, 352, 26, 20, 7)
    ctx.fill()


def draw_ekettle(ctx, t, T, lamp, calm=1.0):
    """電気ケトル（白い樹脂の胴・取っ手は右・注ぎ口は左上）と、台（ランプつき）"""
    fill(ctx, hexrgb("#e9e4da"))                   # 台
    core.rrect(ctx, EX - 112, 536, 224, 24, 8)
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    # 取っ手
    ctx.move_to(EX + 84, 345)
    ctx.curve_to(EX + 150, 345, EX + 150, 500, EX + 90, 500)
    ctx.line_to(EX + 90, 474)
    ctx.curve_to(EX + 124, 474, EX + 124, 371, EX + 86, 371)
    ctx.close_path()
    fill(ctx, hexrgb(KET_E))
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    # 注ぎ口
    ctx.move_to(EX - 80, 322)
    ctx.line_to(EX - 118, 304)
    ctx.line_to(EX - 78, 346)
    ctx.close_path()
    fill(ctx, hexrgb(KET_E))
    ctx.fill_preserve()
    _stroke(ctx, 3.5)
    ekettle_path(ctx)
    fill(ctx, hexrgb(KET_E))
    ctx.fill()
    draw_water(ctx, t, ekettle_path, EX - 92, EX + 92, WATER_E, 532, T, 23, calm)
    ekettle_path(ctx)
    _stroke(ctx, 4.5)
    fill(ctx, hexrgb("#d9d3c8"))                   # ふた
    ctx.save()
    ctx.translate(EX, 312)
    ctx.scale(66, 11)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill_preserve()
    _stroke(ctx, 3)
    # スイッチ（取っ手の下）とランプ（台の前）
    if lamp > 0:
        for rr, al in ((34, 0.18), (22, 0.3)):
            ctx.set_source_rgba(*hexrgb("#ff9a3c", al * lamp))
            ctx.arc(EX, 548, rr, 0, 2 * math.pi)
            ctx.fill()
    fill(ctx, hexrgb("#ff8a24" if lamp > 0.5 else "#c9c2b6"))
    core.rrect(ctx, EX - 14, 543, 28, 10, 4)
    ctx.fill_preserve()
    _stroke(ctx, 2)


def draw_steam(ctx, t, x0, y0, amount, seed, lean=-1.0):
    """湯気。amount 0〜1"""
    if amount <= 0.02:
        return
    rng = np.random.default_rng(seed)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(7):
        ph = rng.uniform(0, 1)
        sp = rng.uniform(0.7, 1.0)
        u = (t * sp * 0.9 + ph) % 1.0
        vis = clamp01(amount * 7 - k)
        al = 0.95 * vis * math.sin(math.pi * u) ** 0.8
        if al < 0.02:
            continue
        L = 70 + 60 * amount
        yb = y0 - u * 120 * (0.6 + 0.6 * amount)
        ctx.set_source_rgba(*hexrgb(STEAM, al))
        ctx.set_line_width(9 + 5 * amount)
        for i in range(14):
            v = i / 13
            yy = yb - v * L
            xx = x0 + lean * 20 * v + (k - 3) * 6 + 12 * math.sin((yy + t * 140) / 60 + k) * (0.3 + v)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#8d9bb0", al * 0.8))
        ctx.set_line_width(2.5)
        for i in range(14):
            v = i / 13
            yy = yb - v * L
            xx = x0 + lean * 20 * v + (k - 3) * 6 + 12 * math.sin((yy + t * 140) / 60 + k) * (0.3 + v)
            (ctx.move_to if i == 0 else ctx.line_to)(xx + 6, yy)
        ctx.stroke()


def th_y(T):
    return TH_BOT + (clamp01(T / 100.0)) * (TH_TOP - TH_BOT)


def draw_thermo(ctx, x, T, col, a):
    """温度計（2本とも同じ目盛り。0℃〜100℃）"""
    if a <= 0:
        return
    ctx.save()
    core.rrect(ctx, x - 13, TH_TOP - 26, 26, TH_BOT - TH_TOP + 44, 13)
    ctx.set_source_rgba(1, 1, 1, 0.95 * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3.5)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.arc(x, TH_BOT + 30, 19, 0, 2 * math.pi)
    ctx.fill()
    y = th_y(T)
    core.rrect(ctx, x - 6, y, 12, TH_BOT + 22 - y, 6)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(2.5)
    for v in range(0, 101, 10):
        yy = th_y(v)
        ln = 14 if v % 50 == 0 else 8
        ctx.move_to(x + 13, yy)
        ctx.line_to(x + 13 + ln, yy)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))     # 100℃ の印
    ctx.set_line_width(4)
    ctx.move_to(x - 28, TH_TOP)
    ctx.line_to(x + 30, TH_TOP)
    ctx.stroke()
    ctx.restore()


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def thermo_alpha(t):
    return ease_out((t - T_GO + 0.1) / 0.4) if t >= T_GO - 0.1 else 0.0


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = tau_of(t)
    Tg, Te = T_gas(tau), T_ele(tau)
    lamp = 0.0 if tau >= s["t_ele"] else (0.8 + 0.2 * math.sin(t * 7.0))
    ctx.push_group()
    ctx.save()
    bx, by, bw, bh = scene_box(t)
    ctx.rectangle(bx, by, bw, bh)
    ctx.clip()
    ctx.save()
    apply_scene(ctx, t)
    draw_kitchen(ctx)
    draw_stove(ctx)
    draw_flames(ctx, t)
    draw_yakan(ctx, t, Tg)
    calm = 1.0 if tau < s["t_ele"] else math.exp(-(tau - s["t_ele"]) / 2.5)
    draw_ekettle(ctx, t, Te, lamp, calm)
    sg = clamp01((Tg - 82) / 18) ** 1.5           # 湯気（やかんは火がついたまま。ケトルは切れると弱まる）
    se = clamp01((Te - 82) / 18) ** 1.5
    if tau > s["t_ele"]:
        se *= math.exp(-(tau - s["t_ele"]) / 6.0)
    draw_steam(ctx, t, GX - 192, 360, sg, 5, lean=-1.0)
    draw_steam(ctx, t, EX - 112, 296, se, 6, lean=-0.6)
    ta = thermo_alpha(t)
    draw_thermo(ctx, TH_GX, Tg, COL_A, ta)
    draw_thermo(ctx, TH_EX, Te, COL_C, ta)
    ctx.restore()
    ctx.restore()
    ta = thermo_alpha(t)
    if ta > 0:
        for x in (TH_GX, TH_EX):
            stext(ctx, t, "100℃", x - 72, TH_TOP, 30, RED, alpha=ta)
    tags = [("a", GX, 300.0, 1.0), ("c", EX, 270.0, 1.0)]      # 上に A・C の丸（温度計にも）
    if ta > 0:
        tags += [("a", TH_GX, TH_TOP - 58, ta), ("c", TH_EX, TH_TOP - 58, ta)]
    for k, x, y, al in tags:
        xd, yd = to_dev(t, x, y)
        r = 22 * scene_scale(t)
        if yd - r < by + 2:
            continue
        fill(ctx, (1, 1, 1, 0.92 * al))
        ctx.arc(xd, yd, r, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, xd, yd, r, r, INKC[k], seed=13 + (k == "c"), width=3.2, alpha=al)
        text(ctx, TAG[k], xd, yd, max(24.0, 30 * scene_scale(t)), INKC[k], alpha=al)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    s = sample()
    sp = speed_now(t)
    text(ctx, f"再生 {sp:.1f}倍" if sp < 1.95 else f"再生 {sp:.0f}倍", 160, 1168, 24, PENCIL, bold=False,
         align="left", alpha=a)
    cols = (("a", 360.0, T_gas(tau), s["t_gas"]), ("c", 790.0, T_ele(tau), s["t_ele"]))
    for k, cx, T, t_fin in cols:
        done = tau >= t_fin
        text(ctx, f"{TAG[k]} {NAME[k]}", cx, 1205, 34, INKC[k], alpha=a)
        text(ctx, f"{math.floor(T + 1e-9):.0f}℃", cx, 1262, 54, INK, alpha=a)
        if k == "a":
            stat = "沸いた！" if done else "火にかけている"
        else:
            stat = "スイッチが切れた！" if done else ("ぐらぐら沸いている" if T >= T_BOIL else "あたためている")
        text(ctx, stat, cx, 1318, 30, RED if done else PENCIL, bold=done, alpha=a)
        if done:
            u = clamp01((t - t_of(t_fin)) / 0.35)
            text(ctx, mmss(t_fin), cx, 1385, 48, INKC[k], alpha=a)
            note.pen_circle(ctx, cx, 1385, 130, 38, RED, seed=70 + (k == "c"), width=5, progress=u, alpha=a)
        else:
            text(ctx, mmss(tau), cx, 1385, 48, INK, alpha=a)
    if t >= T_FIN2:
        b = a * ease_out((t - T_FIN2 - 0.2) / 0.3)
        w = "a" if s["t_gas"] < s["t_ele"] else "c"
        dd = abs(s["t_gas"] - s["t_ele"])
        note.sticky(ctx, f"{NAME[w]}が\n{dd:.0f}秒 早く沸いた", 580, 760, 44, "yellow", a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results()
    win_c = (r["ele"] < r["gas"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_A), bgra(COL_C)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_c[:m]]
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
    r = results()
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
    win_c = r["ele"][:m] < r["gas"][:m]
    for i, (lab, cnt, col) in enumerate(((f"A {NAME['a']}が先に沸いた", int(m - win_c.sum()), COL_A),
                                         (f"C {NAME['c']}が先に沸いた", int(win_c.sum()), COL_C))):
        y = 1180 + i * 58
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 250, y, 34, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 34, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。先に沸いたほうの色", 580, 1294, 26, PENCIL, bold=False, alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        lead = "やかん" if sh["gap_med"] >= 0 else "ケトル"
        note.sticky(ctx, f"やかんが先は 約{pct_i(sh['p_gas'])}。" + chr(10) + f"差は 真ん中で {lead}が{abs(sh['gap_med']):.0f}秒",
                    580, 1390, 32, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- なぜ: ガスの火の強さで分ける ----------
BAR_STEP = 0.45


def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def bars(ctx, t, t0, rows, ys, a, x0=300.0, ln=480.0):
    """横の棒（0〜100%・同じ目盛り）。rows = [(ラベル, 値, 色)]"""
    yt, yb = ys[0] - 26, ys[-1] + 40
    ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
    ctx.set_line_width(3)
    ctx.set_dash([9, 8])
    ctx.move_to(x0 + ln / 2, yt)
    ctx.line_to(x0 + ln / 2, yb)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "半々", x0 + ln / 2, yb + 26, 28, RED, alpha=a)
    for i, ((lab, val, col), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * BAR_STEP
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0, y - 52, 34, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 22, ln, 44)
        ctx.stroke()
        w = ln * val * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, pct_i(val), x0 + ln + 16, y, 38, INK, align="left", alpha=a * clamp01(g * 3 - 2))


WHY_NOTE = "ふつうのバーナーなら ほぼ互角。\n強火力バーナーなら やかん"


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "ガスの火の強さで 分けると", 580, 650, 40, INK, alpha=a)
    text(ctx, "棒は「やかんが先に沸いた」割合", 580, 704, 28, PENCIL, bold=False, alpha=a)
    rows = [("ふつうのバーナー（2.3〜3.0kW）", sh["p_std"], COL_A), ("強火力バーナー（2.8〜4.2kW）", sh["p_hi"], COL_A)]
    bars(ctx, t, T_WHY, rows, (850.0, 1000.0), a)
    tb = T_WHY + 0.3 + len(rows) * BAR_STEP + 0.5
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, WHY_NOTE, 580, 1200, 38, "yellow", a=b, tilt=-0.02)


# ---------- ひねり: 1.5L なら？ ----------
TW_STEP = BAR_STEP


def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


TW_ROWS = (("水 500mL", "gas", "med_gas", "med_ele"), ("水 1.5L", "tw", "med_gas_tw", "med_ele_tw"))
TW_MAX = 600.0                                    # 棒の目盛り（10分）。4本とも同じ目盛り


def tw_done_t():
    return T_TW_RUN + 0.3 + 4 * TW_STEP + 0.5


def draw_twist(ctx, t):
    """沸くまでの時間（1万回の真ん中の値）を、同じ目盛りの横棒で。500mL と 1.5L"""
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "沸くまでの時間（1万回の 真ん中の値）", 580, 650, 40, INK, alpha=a)
    text(ctx, "同じ台所・同じ道具で、水の量だけ変えた", 580, 704, 28, PENCIL, bold=False, alpha=a)
    x0, ln = 330.0, 480.0
    ys = ((800.0, 850.0, 905.0), (985.0, 1035.0, 1090.0))
    top, bot = 830.0, 1112.0
    ctx.set_line_width(1.5)                        # 1分ごとの目盛り線
    for mnt in range(0, 11):
        x = x0 + ln * mnt * 60 / TW_MAX
        ctx.set_source_rgba(*hexrgb(PENCIL, (0.45 if mnt % 5 == 0 else 0.2) * a))
        ctx.move_to(x, top)
        ctx.line_to(x, bot)
        ctx.stroke()
    for mnt in (0, 5, 10):
        text(ctx, f"{mnt}分", x0 + ln * mnt * 60 / TW_MAX, bot + 22, 24, PENCIL, bold=False, alpha=a)
    k = 0
    for (lab, _key, kg, ke), (yl, yg, ye) in zip(TW_ROWS, ys):
        text(ctx, lab, 150, yl, 34, INK, align="left", alpha=a * clamp01((t - T_TW_RUN - 0.1 - k * TW_STEP) / 0.3))
        for who, key, y in (("a", kg, yg), ("c", ke, ye)):
            tk = T_TW_RUN + 0.3 + k * TW_STEP
            k += 1
            if t < tk:
                continue
            g = ease_out((t - tk) / 0.45)
            text(ctx, NAME[who] if who == "a" else "ケトル", x0 - 14, y, 30, INKC[who], align="right", alpha=a)
            w = ln * min(1.0, sh[key] / TW_MAX) * g
            if w > 1:
                ctx.set_source_rgba(*hexrgb(COLS[who], 0.95 * a))
                core.rrect(ctx, x0, y - 20, w, 40, 6)
                ctx.fill_preserve()
                ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
                ctx.set_line_width(2.5)
                ctx.stroke()
            text(ctx, mmss(sh[key]), x0 + w + 12, y, 30, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"1回ごとの差（真ん中の値）\n{abs(sh['gap_med']):.0f}秒 → {abs(sh['gap_tw']):.0f}秒", 580, 1235, 36,
                    "pink", fg=RED, a=b, tilt=-0.02)
    if t >= tb + 1.0:
        b = ease_out((t - tb - 1.0) / 0.3) * a
        text(ctx, TW_NOTE, 580, 1365, 30, INK, bold=False, alpha=b)


TW_NOTE = "水が多いほど、火の強さの差が 時間の差になる"


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


CD_X, CD_Y = 580.0, 855.0


class YIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに台所（0秒目から炎がゆれ、ケトルのランプが光る）"""
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


INTRO = YIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "沸くまで", 580, 690, 34, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、1.5L沸かすなら？", 580, 860, a=ba, t_rel=t - T_TW, size=56)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたの家は、\nやかん？ケトル？", 580, 860, 58, "yellow", a=q, tilt=-0.02)
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
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    # ガスの炎の音（ゴー）とケトルのうなり。沸いている間は泡の音（ぷつぷつ）が増える
    hiss = noise_band(t_end, 6, 3, 1.0)
    env = np.minimum(1, np.arange(len(hiss)) / (SR * 0.3)) * np.minimum(1, (len(hiss) - np.arange(len(hiss))) / (SR * 0.4))
    mx.add(0.0, hiss * env, 0.06)
    tt = 0.0
    rng = np.random.default_rng(9)
    while tt < t_end:
        tau = tau_of(tt)
        amt = max(bubble_amt(T_gas(tau)), bubble_amt(T_ele(tau)) * (1.0 if tau < s["t_ele"] else 0.0))
        if amt > 0.05 and rng.uniform() < amt:
            mx.add(tt, tick(rng.uniform(500, 1400), 0.03), 0.12)
        tt += 0.05
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_FIN1 - 1.2, bpm=124, vol=0.32)
    tg, te = t_of(s["t_gas"]), t_of(s["t_ele"])
    whistle = np.sin(2 * np.pi * 1760 * np.arange(int(SR * 1.2)) / SR) * np.minimum(1, np.arange(int(SR * 1.2)) / (SR * 0.3)) \
        * np.minimum(1, (int(SR * 1.2) - np.arange(int(SR * 1.2))) / (SR * 0.3))
    mx.add(tg, whistle, 0.10)                         # やかんの笛
    mx.add(tg, bell(784.0, 1.2), 0.4)
    mx.add(te, tick(1800, 0.04), 0.6)                 # カチッ（スイッチが切れる）
    mx.add(te + 0.05, bell(659.3, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(2):                                 # なぜ
        mx.add(T_WHY + 0.3 + i * BAR_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(4):
        mx.add(T_TW_RUN + 0.3 + i * TW_STEP, blip(523.3 + 60 * i, 0.12), 0.3)
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
    # (1) 式で出した「100℃になる時刻」が、細かいきざみで足し算した結果と一致する（いくつかの回で）
    worst = 0.0
    for i in range(0, 400, 40):
        P = p["q"][i] * p["eta"][i]
        C = VOL * p["jit"][i] * C_W + p["c_gas"][i]
        T, tt, dt = p["tap"][i], 0.0, 0.01
        while T < T_BOIL:
            T += (P - p["ua_gas"][i] * (T - p["room"][i])) / C * dt
            tt += dt
        worst = max(worst, abs(tt - r["gas"][i]))
    checks.append(("やかんの沸く時刻: 式 − きざみの足し算（最大・秒）", worst, 0.0, 0.05))
    # (2) 熱が逃げないとき（UA→0）は 熱容量×温度差÷熱 に近づく
    tq = float(t_reach(1200.0, 2400.0, 1e-6, 15.0, 20.0))
    checks.append(("熱が逃げないときの時刻（秒）", tq, 2400.0 * 85.0 / 1200.0, 0.01))
    # (3) 実測との照合（モデルの真ん中の値で）: 名古屋市のテスト 1250W・15℃、杉山 2007 のやかん 1L
    cal = calib()
    t5, m5 = cal["ele0.5"]
    t12, m12 = cal["ele1.2"]
    tg, mg = cal["gas1.0"]
    checks.append(("電気ケトル 0.5L・15℃ のモデル（秒）が 測定 185〜192秒の ±5% に入る", float(m5[0] * 0.95 <= t5 <= m5[1] * 1.05),
                   1.0, 0.0))
    checks.append(("電気ケトル 1.2L・15℃ のモデル（秒）が 測定 392〜403秒の ±5% に入る", float(m12[0] * 0.95 <= t12 <= m12[1] * 1.05),
                   1.0, 0.0))
    checks.append(("やかん 1L・2.5kW のモデル（秒）が 測定 325〜410秒 に入る", float(mg[0] <= tg <= mg[1]), 1.0, 0.0))
    # (4) やかんの実際の効率（水とやかんが受け取った熱 ÷ ガス）が 30〜56% の中（石谷 1983 の 31% 〜 カタログ最良 56%）
    checks.append(("やかんの効率の10%点が30%以上", float(sh["eff_gas_q"][0] >= 0.30), 1.0, 0.0))
    checks.append(("やかんの効率の90%点が56%以下", float(sh["eff_gas_q"][2] <= 0.56), 1.0, 0.0))
    # (5) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["p_gas"], sh["gap_med"])),
                   float(INTRO.correct), 0.0))
    # (6) 見本は1万回の中の1回で、差が真ん中の値の近く
    smp = sample()
    checks.append(("見本の差（秒）が真ん中の値の近く", smp["gap"], sh["gap_med"], 3.0))
    # (7) 画面の回数が足して1万（同時は無い）
    checks.append(("先に沸いた回の合計", float(sh["n_gas"] + sh["n_ele"]), float(N_TRIAL), 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.1f}倍  沸く {T_FIN1:.2f} / {T_FIN2:.2f}秒  答え {T_REV:.1f}  なぜ {T_WHY:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（やかん {mmss(s['t_gas'])} / ケトル {mmss(s['t_ele'])}）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 16.0, 18.0, T_FIN1 - 0.3, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 2.5, T_TW + 1.0, T_TW_RUN + 1.5, tw_done_t() + 1.5,
              T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
