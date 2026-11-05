"""冬の外でスマホの電池が急に減るのは、寒さのせい？ 使いすぎ？ 寒い外と暖かい部屋で「同じ使い方」を1万回。— 2026-10-27 作成（公開予定 11/5・45秒前後）

くらべるのは「同じ使い方をして、表示の％がどれだけ減るか」だけ。

モデル（スマホの電池1個。右のカッコは出典。【確認】【幅】【仮定】は FACTCHECK の判定）
  電池の中の電気の量（残量 SOC）は、使った電力を積み上げて減らす。表示の％は、電池の「電圧」から読む（画面に出すのはこれ）。
      SOC(t) = SOC0 − ∫ P dt ÷ 電池の容量（Wh）。容量 = 公称 11〜17 Wh（3,000〜4,500 mAh を 3.85 V で換算・仮定）× 傷み具合 0.80〜1.00（仮定）
      電圧（使っている最中）V = 開放電圧 OCV(SOC) − 内部抵抗 R × 電流 I、使う電力 P = V × I（一定の電力で使う）→ V = (OCV + √(OCV² − 4RP)) ÷ 2
      表示の％ = OCV の逆関数で V を読み直した値（電圧が高ければ高い％）
  開放電圧の形 OCV(SOC)（折れ線。0%:3.00 5%:3.45 10%:3.58 20%:3.70 50%:3.80 80%:4.00 100%:4.20 V）
      満充電 4.20 V（BU-409 https://batteryuniversity.com/article/bu-409-charging-lithium-ion 【確認】）、中ほど 3.7〜3.8 V、0%付近 3.0 V 以下、10% を切ると急に落ちる
      （形は【幅】。5% で約 3.45 V は掲示板の表で、公式の表は確認できなかった＝【仮定】。BU-903 https://batteryuniversity.com/article/bu-903-how-to-measure-state-of-charge にリチウムイオンの表は無い）
  内部抵抗 R = R25 × 傷み × 温度の倍率 f(T)
      向き: 寒いと内部抵抗が大きくなり、同じ使い方でも電圧が下がる。電池に電気が残っていても取り出せず機器が切れる
          （BU-802a https://batteryuniversity.com/article/bu-802a-how-does-rising-internal-resistance-affect-performance 、
           BU-502 https://batteryuniversity.com/article/bu-502-discharging-at-high-and-low-temperatures 、
           サンディア国立研究所 https://www.sandia.gov/research/publications/details/low-temperature-electrical-performance-characteristics-of-li-ion-cells-1999-01-01/ 【確認】）
      R25（25℃の内部抵抗）= 0.05〜0.12 Ω（FACTCHECK の概算「0.1 Ω前後」を見込んだ幅。出典なし＝【仮定】）
      温度の倍率 f(T) = m0^((25−T)/25)（0℃で m0 倍、25℃で 1 倍）。m0 = 1.5〜4.0（FACTCHECK の「0℃で 2〜3 倍・1.5〜数倍」を見込んだ幅。**倍率の出典は確認できなかった＝【仮定】**）
      傷み具合による抵抗の増え = 1 ＋ 4 ×（1 − 傷み具合）（仮定）
  電池の温度: スマホは温かい所（22〜28℃）から出発し、周りの気温＋使った熱 2〜6℃ に向けて、時定数 6〜18 分で近づく（すべて仮定）。外は −5〜5℃、部屋は 18〜24℃（仮定）
      電池の温度が 0〜35℃ の外だと性能が落ちる（メーカーの公式ページ https://www.apple.com/batteries/maximizing-performance/ 【確認】。温度が通常範囲に戻れば性能も戻る＝一時的）
  使い方（寒い外と部屋で同じ）: 画面 0.5〜1.4 W ＋ 地図・位置情報・通信 0.4〜1.4 W（旧機種の実測を見込んだ幅 【幅】。
      https://www.usenix.org/legacy/event/usenix10/tech/full_papers/Carroll.pdf 、https://www.itmedia.co.jp/mobile/spv/1403/18/news097.html ）
      ＋ カメラ 1.5〜3.0 W を 3〜5 分だけ（歩く途中に1回。カメラの電力は出典なし＝【仮定】）。歩く時間 40〜90 分
  電源が切れる電圧 3.25〜3.45 V（多くのリチウムイオンの切断電圧は 3.0 V/セル＝BU-501 https://batteryuniversity.com/article/bu-501-basics-about-discharging 【確認】。
      スマホはそれより高めで切るのが一般的だが公表値は確認できなかった＝【仮定】）。使っている最中に電圧がこれを下回ったら切れる（表示は 0%）
  はじめの残量 35〜90%、1回ごとにすべてでたらめ（一様）。1回のなかでは 寒い外と部屋で 使い方・電池・はじめの残量・出発の温度は同じ

問い: 「冬の外で、スマホの電池が／急に減るのは、／寒さ？使いすぎ？」
      選択肢: 使いすぎ ／ ほぼ同じ ／ 寒さのせい（記号の並びは LABELS の順。正解の記号は C）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      同じ使い方で、外のほうが表示の％の減りが大きかった割合を p、％の減り方の比（外 ÷ 中）の中央値を r とする。
      p ≥ 60% かつ r ≥ 1.2 → 寒さのせい、p ≤ 40% かつ r ≤ 0.83 → 使いすぎ、それ以外 → ほぼ同じ。
      ％の減り = はじめ（使い始め）の表示 − 歩き終わりの表示。電源が切れていたら歩き終わりは 0%。
ひねり: 「では、ポケットで温めたら？」→ 歩き終わりの電池を、ポケットの中で 15〜25℃ まで温めたとき（体温で。仮定）、
      同じ使い方での表示の％が戻った回（1ポイント以上）の割合と、戻った分の中央値。ポケットに入れることだけを言う。
      （ポケットの効果の出典は確認できなかった。「電池の温度が戻れば表示も戻る」という事実だけを根拠にする）
締め: 「あなたのスマホ、冬の外で急に減ったこと、ありますか？」（答えは出さない）＋「コメントで教えてください」

注意: 容量そのものが寒さで一時的に減る効果（BU-502: −18℃で約 50%）は入れていない（0℃前後の幅は出典が無い）。入れれば寒い側に倒れるので、結論は弱めに出る。
乱数の種は見本（2人の見た目）のために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "sumaho-samusa"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261105
SOC_T = np.array([0.0, 0.05, 0.10, 0.20, 0.50, 0.80, 1.00])      # 残量
V_T = np.array([3.00, 3.45, 3.58, 3.70, 3.80, 4.00, 4.20])       # 開放電圧 V
SOC0 = (0.35, 0.90)                                             # はじめの残量
CAP_NOM, HEALTH = (11.0, 17.0), (0.80, 1.00)                    # Wh、傷み具合（容量にかかる）
R25, M0 = (0.05, 0.12), (1.5, 4.0)                               # Ω、0℃での抵抗の倍率
P_SCREEN, P_MAP = (0.5, 1.4), (0.4, 1.4)                          # W
P_CAM, T_CAM = (1.5, 3.0), (3.0, 5.0)                            # W、分
WALK = (40.0, 90.0)                                              # 歩く時間（分）
TAU_COOL, SELF_HEAT, T_START = (6.0, 18.0), (2.0, 6.0), (22.0, 28.0)   # 分、℃、℃
T_OUT, T_ROOM, T_POCKET = (-5.0, 5.0), (18.0, 24.0), (15.0, 25.0)
V_CUT = (3.25, 3.45)                                             # 電源が切れる電圧

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_P_HI, RULE_R_HI = 0.60, 1.20
RULE_P_LO, RULE_R_LO = 0.40, 0.83
BACK_PT = 0.01                                                   # 「表示が戻った」＝1ポイント以上


def answer_by_rule(p, r):
    """p = 外のほうが減りが大きかった割合、r = 減り方の比（外÷中）の中央値。'cold' / 'same' / 'use'"""
    if p >= RULE_P_HI and r >= RULE_R_HI:
        return "cold"
    if p <= RULE_P_LO and r <= RULE_R_LO:
        return "use"
    return "same"


def ocv(s):
    return np.interp(s, SOC_T, V_T)


def ocv_inv(v):
    return np.interp(v, V_T, SOC_T)


def f_temp(m0, T):
    """温度の倍率。0℃で m0 倍、25℃で 1 倍（25℃より暖かい側は 1 倍より小さくなりうるが、そのまま使う）"""
    return np.power(m0, (25.0 - np.asarray(T, float)) / 25.0)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    q = dict(soc0=u(SOC0), cap=u(CAP_NOM), health=u(HEALTH), r25=u(R25), m0=u(M0),
             p_scr=u(P_SCREEN), p_map=u(P_MAP), p_cam=u(P_CAM), t_cam=u(T_CAM), walk=u(WALK),
             tau=u(TAU_COOL), heat=u(SELF_HEAT), t0=u(T_START), t_out=u(T_OUT), t_room=u(T_ROOM),
             t_pocket=u(T_POCKET), vcut=u(V_CUT))
    q["p_base"] = q["p_scr"] + q["p_map"]
    q["cam_at"] = 8.0 + (q["walk"] - q["t_cam"] - 14.0) * rng.uniform(0, 1, n)     # カメラを使い始める分
    return q


def batt_temp(q, t_amb, t):
    te = t_amb + q["heat"]
    return te + (q["t0"] - te) * np.exp(-t / q["tau"])


def state(q, t_amb, t, t_bat=None):
    """歩き始めから t 分後の (残量, 電圧, 電池の温度, 表示の割合 0〜1)。電圧が切断電圧を下回れば表示は 0。配列でも1回ぶんでも可"""
    t = np.asarray(t, float)
    tb = batt_temp(q, t_amb, t) if t_bat is None else t_bat
    cam_min = np.clip(t - q["cam_at"], 0.0, q["t_cam"])
    soc = q["soc0"] - (q["p_base"] * t + q["p_cam"] * cam_min) / 60.0 / (q["cap"] * q["health"])
    in_cam = (t >= q["cam_at"]) & (t < q["cam_at"] + q["t_cam"])
    p = q["p_base"] + q["p_cam"] * in_cam
    r = q["r25"] * (1.0 + 4.0 * (1.0 - q["health"])) * f_temp(q["m0"], tb)
    o = ocv(soc)
    disc = o * o - 4.0 * r * p
    v = (o + np.sqrt(np.maximum(disc, 0.0))) / 2.0
    off = (disc < 0) | (v < q["vcut"])
    return soc, v, tb, np.where(off, 0.0, ocv_inv(v))


def shut_down(q, t_amb):
    """歩いている間に一度でも電圧が切断電圧を下回ったか。電圧がいちばん下がるのは、カメラを使い終える時刻か歩き終わり（どちらも減る一方）"""
    _, v1, _, _ = state(q, t_amb, q["cam_at"] + q["t_cam"] - 1e-9)
    _, v2, _, _ = state(q, t_amb, q["walk"])
    return (v1 < q["vcut"]) | (v2 < q["vcut"])


def end_display(q, t_amb):
    d = state(q, t_amb, q["walk"])[3]
    return np.where(shut_down(q, t_amb), 0.0, d)
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
    q = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
    d0 = state(q, q["t_out"], 0.0)[3]                        # はじめの表示（出発の温度は同じなので 外も中も同じ）
    d0_room = state(q, q["t_room"], 0.0)[3]
    dc = d0 - end_display(q, q["t_out"])
    dw = d0_room - end_display(q, q["t_room"])
    # ひねり: 歩き終わりの電池を、ポケットで T_pocket まで温めたとき（同じ使い方 = 歩き終わりの電力）
    soc_e, _, _, d_end = state(q, q["t_out"], q["walk"])
    d_end = np.where(shut_down(q, q["t_out"]), 0.0, d_end)
    d_back = state(q, q["t_out"], q["walk"], t_bat=q["t_pocket"])[3]
    r = dict(q=q, d0=d0, d0_room=d0_room, dc=dc, dw=dw, d_end=d_end, d_back=d_back, soc_end=soc_e)
    _RES["m"] = r
    return r


def shown():
    r = results()
    dc, dw = r["dc"], r["dw"]
    p = float((dc > dw).mean())
    ratio = dc / np.maximum(dw, 0.01)                         # 室内の減りが 1 ポイント未満のときは 1 ポイントとして割る
    rm = float(np.median(ratio))
    rise = r["d_back"] - r["d_end"]
    q = r["q"]
    return dict(p=p, r=rm, key=answer_by_rule(p, rm),
                dc_med=float(np.median(dc)), dw_med=float(np.median(dw)),
                off_c=float(shut_down(q, q["t_out"]).mean()), off_w=float(shut_down(q, q["t_room"]).mean()),
                back_p=float((rise >= BACK_PT).mean()), back_med=float(np.median(rise)),
                back_med_up=float(np.median(rise[rise >= BACK_PT])) if (rise >= BACK_PT).any() else 0.0,
                gap_med=float(np.median(r["soc_end"] - r["d_end"])),
                soc_med=float(np.median(r["soc_end"])), d_med=float(np.median(r["d_end"])),
                rc_med=float(np.median(q["r25"] * f_temp(q["m0"], batt_temp(q, q["t_out"], q["walk"])))),
                rw_med=float(np.median(q["r25"] * f_temp(q["m0"], batt_temp(q, q["t_room"], q["walk"])))))


def report():
    sh = shown()
    print(f"p(外のほうが減りが大きい)={sh['p']:.4f}  r(減り方の比 外÷中・中央値)={sh['r']:.3f}  答え {sh['key']}"
          f"   減りの中央値 外 {sh['dc_med'] * 100:.1f}pt / 中 {sh['dw_med'] * 100:.1f}pt")
    print(f"  電源が切れた割合 外 {sh['off_c'] * 100:.1f}%  中 {sh['off_w'] * 100:.1f}%"
          f"   歩き終わり: 中の電気の量の中央値 {sh['soc_med'] * 100:.0f}%  表示の中央値 {sh['d_med'] * 100:.0f}%  差の中央値 {sh['gap_med'] * 100:.1f}pt")
    print(f"  ひねり: ポケットで温めて表示が戻った回 {sh['back_p'] * 100:.1f}%  戻った分の中央値 全体 {sh['back_med'] * 100:+.1f}pt / 戻った回だけ {sh['back_med_up'] * 100:+.1f}pt")
    print(f"  内部抵抗の中央値（歩き終わり）外 {sh['rc_med']:.3f}Ω  中 {sh['rw_med']:.3f}Ω")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)


# =====================================================================
# 見本（寒い外の1人と 暖かい部屋の1人。同じ1回の値）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中の1回（その回の値そのもの）。外・中とも電源が切れず、歩く時間は約60分、
    外のほうが大きく減り（比が 1.35〜1.9）、カメラを使うところで外は表示がガクッと下がり、ポケットで温めると戻る回。
    そのなかで 中央の値にいちばん近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    q = r["q"]
    n = len(q["soc0"])
    off = shut_down(q, q["t_out"]) | shut_down(q, q["t_room"])
    cam_mid = q["cam_at"] + q["t_cam"] / 2
    pre = np.maximum(q["cam_at"] - 1.0, 0.0)
    dip = state(q, q["t_out"], pre)[3] - state(q, q["t_out"], cam_mid)[3]
    dip_w = state(q, q["t_room"], pre)[3] - state(q, q["t_room"], cam_mid)[3]
    ratio = r["dc"] / np.maximum(r["dw"], 0.01)
    rise = r["d_back"] - r["d_end"]
    ok = (~off) & (np.abs(q["walk"] - 60.0) <= 4.0) & (q["t_out"] >= -3.0) & (q["t_out"] <= 2.0) & (q["t_room"] >= 19.0) & (q["t_room"] <= 22.0)
    ok &= (ratio >= 1.35) & (ratio <= 1.9) & (dip >= 0.05) & (dip > dip_w * 1.5) & (rise >= 0.04) & (r["dc"] >= 0.2) & (r["d0"] >= 0.5) & (r["d_end"] >= 0.1)
    idx = np.nonzero(ok)[0]
    if len(idx) == 0:
        raise SystemExit("見本の候補がない")
    keys = dict(soc0=0.2, p_base=0.5, r25=0.04, m0=1.0, cap=3.0, health=0.1)
    dist = np.zeros(len(idx))
    for k, w in keys.items():
        dist += np.abs(q[k][idx] - np.median(q[k])) / w
    i = int(idx[np.argmin(dist)])
    qi = {k: float(v[i]) for k, v in q.items()}
    _SAMPLE = dict(i=i, q=qi, t_amb={"cold": qi["t_out"], "warm": qi["t_room"]}, dip=float(dip[i]), dip_w=float(dip_w[i]),
                   d0=float(r["d0"][i]), dc=float(r["dc"][i]), dw=float(r["dw"][i]), d_end=float(r["d_end"][i]),
                   d_back=float(r["d_back"][i]), soc_end=float(r["soc_end"][i]))
    return _SAMPLE


def samp_state(k, tau):
    """見本の k（'cold' / 'warm'）の、歩き始めから tau 分後の (残量, 電圧, 電池の温度, 表示)"""
    S = sample()
    return [float(x) for x in state(S["q"], S["t_amb"][k], tau)]


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    S = sample()
    q = S["q"]
    print("見本 回", S["i"], "外", round(q["t_out"], 1), "℃ 部屋", round(q["t_room"], 1), "℃ 歩く", round(q["walk"]), "分 はじめ", round(S["d0"] * 100), "% 外の減り",
          round(S["dc"] * 100), "pt 中の減り", round(S["dw"] * 100), "pt 外の歩き終わり 表示", round(S["d_end"] * 100), "% 中の電気", round(S["soc_end"] * 100),
          "% ポケット後", round(S["d_back"] * 100), "% ガクッ", round(S["dip"] * 100), "pt（中", round(S["dip_w"] * 100), "pt）")
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
note.DATE = "11.5"                                  # 日付欄（公開予定日）

COL_C, INK_C = "#8fbbe8", "#2f63a8"                 # 寒い外（水色）
COL_P, INK_P = "#f4ad6a", "#b8601a"                 # 暖かい部屋（だいだい）
MORE_COL, LESS_COL = "#7fb0dc", "#ffe3a6"           # マス目: 外のほうが大きく減った / そうでない
SKIN = "#f7d9bd"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら CORRECT も合わせる（run_checks が確かめる）
# 規則の答えが「寒さのせい」なので、正解が C の位置に来るよう 使いすぎ／ほぼ同じ／寒さのせい の並びにした
LABELS = ["使いすぎ", "ほぼ同じ", "寒さのせい"]
CORRECT = 2                                         # answer_by_rule の結果の位置（C）
KEY_LABEL = {"cold": "寒さのせい", "same": "ほぼ同じ", "use": "使いすぎ"}
PANEL_TITLE = {"cold": "寒い外", "warm": "暖かい部屋"}
PCOL = {"cold": COL_C, "warm": COL_P}
PINK = {"cold": INK_C, "warm": INK_P}

BIG_Q = ["冬の外で、スマホの電池が急に減るのは、", "寒さ？使いすぎ？"]               # 定位置（上）の2行
BIG_Q3 = ["冬の外で、スマホの電池が", "急に減るのは、", "寒さ？使いすぎ？"]          # 1コマ目の3行（同じ大きさ）
DETAIL = "同じ使い方で、地図を見ながら歩く"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 10.0                                     # T_GO から 歩き終わり（見本の歩く時間）になるまで
R0 = 0.06                                           # 冒頭の進み（シミュの分／動画の秒）。ほとんど進めない（それでも雪・人・町は動く）

# 画面の置き場所（パネルは 局所座標 WC×HC で描いて、移動・拡大する）
WC, HC = 440.0, 720.0
CAR_CX = 520.0
S0, S1 = 0.82, 1.0
Y_INTRO, Y_FINAL = 830.0, 590.0
GAP = 16.0
BX, BY, BW, BH = 14.0, 62.0, 412.0, 322.0           # 場面の枠


def setup():
    global TL, TAU_END, T_FIN2, T_VERD, T_G0, T_G1, T_REV, T_ANS2, T_DOOR, T_DOOR2, T_Q, DURATION, GAKU
    TAU_END = float(sample()["q"]["walk"])
    T_FIN2 = T_GO + RACE_LEN
    T_VERD = T_FIN2 - 0.8

    def build(rx):
        ts = np.arange(0, 60, 1 / 200)
        fade = 1 - 0.6 * np.clip((ts - T_MOVE) / (T_FIN2 - T_MOVE), 0, 1)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.0) for t in ts]) * fade)
        sp = sp * np.array([1 - ease((t - (T_FIN2 - 1.2)) / 1.2) if t > T_FIN2 - 1.2 else 1.0 for t in ts])
        return ts, np.cumsum(sp) / 200

    lo, hi = 0.1, 60.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN2, ts, tau)) > TAU_END:
            hi = mid
        else:
            lo = mid
    ts, tau = build(hi)
    TL = dict(t=ts, tau=np.minimum(tau, TAU_END))
    T_G0 = T_FIN2 + 2.4
    T_G1 = T_G0 + 3.0
    T_REV = T_G1 + 3.0
    T_ANS2 = T_REV + 2.4
    T_DOOR = T_ANS2 + 6.2
    T_DOOR2 = T_DOOR + 2.4
    T_Q = T_DOOR2 + 5.4
    DURATION = T_Q + 6.0
    # 外のスマホの表示がガクッと下がる時刻（動画の秒）。約0.5秒で 3.5ポイント以上下がり始めた所。表示は一度出したら約1.6秒そのまま
    GAKU = []
    prev = None
    for i in range(int(T_FIN2 * 30)):
        t = i / 30
        d_now = samp_state("cold", tau_of(t))[3]
        d_old = samp_state("cold", tau_of(max(0.0, t - 0.5)))[3]
        if d_old - d_now >= 0.035 and (prev is None or t - prev > 3.0) and t > T_GO + 0.5:
            GAKU.append(t)
            prev = t


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def pcs(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


def pc1(x):
    return f"{x * 100:.1f}%"


def pt_i(x):
    return int(math.floor(abs(x) * 100 + 0.5))


def ival(x):
    v = int(round(x))
    return f"−{abs(v)}" if v < 0 else f"{v}"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, w, col, outline=3.0):
    """太い線（ふちどり付き）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


COATS = ["#7c8fb5", "#c9786b", "#6d9a86", "#a98fc4"]
SCARF = ["#e8e0d0", "#b84a4a", "#3f6fa8", "#e4b84a"]
HAIR = ["#2b2b33", "#4a3526", "#1f2430", "#6a4a33"]
PANTS = "#3b4358"


def phone_icon(ctx, x, y, sc, ang):
    """手に持ったスマホ（画面に地図と赤いピン）。(x, y) は中心"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    core.rrect(ctx, -13 * sc, -22 * sc, 26 * sc, 44 * sc, 5 * sc)
    ctx.set_source_rgba(*hexrgb("#2d3340"))
    ctx.fill_preserve()
    _stroke(ctx, 2.4, INK, 0.95)
    core.rrect(ctx, -10.5 * sc, -18.5 * sc, 21 * sc, 36 * sc, 3 * sc)
    ctx.set_source_rgba(*hexrgb("#dff2ff"))
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#7fb98f"))
    ctx.rectangle(-10.5 * sc, 2 * sc, 21 * sc, 8 * sc)
    ctx.fill()
    ctx.move_to(-10.5 * sc, -8 * sc)
    ctx.line_to(10.5 * sc, 0)
    ctx.move_to(-4 * sc, -18.5 * sc)
    ctx.line_to(2 * sc, 18.5 * sc)
    ctx.set_source_rgba(*hexrgb("#ffffff"))
    ctx.set_line_width(3 * sc)
    ctx.stroke()
    ctx.arc(2 * sc, -4 * sc, 3.4 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(RED))
    ctx.fill()
    ctx.restore()


def walker(ctx, x, fy, sc, ci, t, walk, puff=1.0, scarf=True, phase=0.0):
    """スマホを見ながら歩く（立つ）人。(x, fy) は足もとの中心。walk=True で足を振る"""
    coat, scf, hair = COATS[ci % len(COATS)], SCARF[ci % len(SCARF)], HAIR[(ci * 3 + 1) % len(HAIR)]
    sc = sc * 1.08
    w8 = t * 8.0 + phase
    bob = 4.0 * abs(math.sin(w8)) * sc if walk else 1.2 * math.sin(t * 1.8 + phase) * sc
    hip, sh_y, hd = fy - 62 * sc, fy - 130 * sc - bob, fy - 150 * sc - bob
    ctx.save()
    for sgn in (-1, 1):
        sw = math.sin(w8) * sgn if walk else 0.0
        lift = max(0.0, math.cos(w8) * sgn) * 8 * sc if walk else 0.0
        fx = x + sgn * 7 * sc + sw * 20 * sc
        thick(ctx, [(x + sgn * 7 * sc, hip - bob), (fx, fy - 6 * sc - lift)], 17 * sc, PANTS, 2.5)
        ctx.save()
        ctx.translate(fx + 5 * sc, fy - 3 * sc - lift)
        ctx.scale(1.5, 0.8)
        ctx.arc(0, 0, 9 * sc, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#2a2f3d"))
        ctx.fill()
    # うで（奥）
    asw = math.sin(w8 + 0.5) if walk else 0.0
    thick(ctx, [(x - 26 * sc, sh_y + 12 * sc), (x - 32 * sc - asw * 8 * sc, sh_y + 62 * sc)], 14 * sc, coat, 2.5)
    # 胴
    core.rrect(ctx, x - 29 * sc, sh_y, 58 * sc, 80 * sc, 15 * sc)
    ctx.set_source_rgba(*hexrgb(coat))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    if scarf:
        core.rrect(ctx, x - 24 * sc, sh_y - 8 * sc, 48 * sc, 16 * sc, 8 * sc)
        ctx.set_source_rgba(*hexrgb(scf))
        ctx.fill_preserve()
        _stroke(ctx, 2.6, INK, 0.85)
    # 手前のうで（スマホを持つ）
    hx, hy = x + 46 * sc, sh_y + 44 * sc
    thick(ctx, [(x + 26 * sc, sh_y + 14 * sc), (x + 40 * sc, sh_y + 52 * sc), (hx, hy)], 14 * sc, coat, 2.5)
    phone_icon(ctx, hx + 10 * sc, hy - 20 * sc, 1.45 * sc, 0.18)
    ctx.arc(hx + 1 * sc, hy + 2 * sc, 7 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.2, INK, 0.9)
    # 頭
    ctx.arc(x, hd, 26 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.arc(x, hd, 27.5 * sc, math.pi * 0.98, math.pi * 2.02)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.9)
    for dx in (-8, 11):
        ctx.arc(x + dx * sc + 3 * sc, hd + 4 * sc, 2.9 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
    ctx.arc(x + 6 * sc, hd + 14 * sc, 3.4 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#c0645c"))
    ctx.fill()
    if puff > 0:                                                    # 白い息
        for j in range(2):
            u = (t * 0.55 + phase + j * 0.5) % 1.0
            ctx.arc(x + (26 + 20 * u) * sc, hd + 12 * sc - 30 * u * sc, (5 + 11 * u) * sc, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.85 * (1 - u) * puff)
            ctx.fill_preserve()
            _stroke(ctx, 1.6, PENCIL, 0.5 * (1 - u) * puff)
    ctx.restore()


def scene_out(ctx, x, y, w, h, t):
    """寒い外: 雪の町なみが流れ、雪が降る"""
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *hexrgb("#a9bacd")[:3])
    g.add_color_stop_rgb(1, *hexrgb("#e0e8ef")[:3])
    ctx.set_source(g)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    scroll = t * 70.0
    for blds, per, spd, col in (
            (((0, 60, 80), (95, 48, 110), (165, 80, 66), (260, 52, 120), (330, 70, 88)), 410.0, 0.45, "#9aabbd"),
            (((30, 72, 74), (140, 56, 96), (230, 90, 60), (340, 60, 84)), 440.0, 0.9, "#7f93a8")):
        off = (scroll * spd) % per
        for rep in (-1, 0, 1, 2):
            for bx, bw, bh in blds:
                X = x + bx + rep * per - off
                if X > x + w or X + bw < x:
                    continue
                ctx.rectangle(X, y + h - 44 - bh, bw, bh)
                ctx.set_source_rgba(*hexrgb(col))
                ctx.fill()
                ctx.rectangle(X - 2, y + h - 44 - bh - 6, bw + 4, 8)          # 屋根の雪
                ctx.set_source_rgba(*hexrgb("#f4f8fb"))
                ctx.fill()
    ctx.rectangle(x, y + h - 44, w, 44)                                          # 雪の道
    ctx.set_source_rgba(*hexrgb("#f4f8fb"))
    ctx.fill()
    ctx.move_to(x, y + h - 44)
    ctx.line_to(x + w, y + h - 44)
    _stroke(ctx, 2.6, INK, 0.6)
    for i in range(7):                                                            # 道のすじ（足もとが流れる）
        px = x + ((i * 72.0 - scroll * 1.4) % (w + 72.0)) - 36
        ctx.move_to(px, y + h - 26)
        ctx.line_to(px + 34, y + h - 26)
    _stroke(ctx, 3.2, "#c9d6e2", 0.9)
    for i in range(46):                                                           # 雪
        sp = 55.0 + (i % 5) * 20.0
        fx = (i * 37.3 + 14.0 * math.sin(t * 1.3 + i)) % (w + 20) - 10
        fy = (t * sp + i * 53.7) % (h + 20) - 10
        rr = 2.4 + (i % 4) * 0.9
        ctx.arc(x + fx, y + fy, rr, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.96)
        ctx.fill_preserve()
        _stroke(ctx, 1.1, PENCIL, 0.35)
    ctx.restore()


def scene_in(ctx, x, y, w, h, t):
    """暖かい部屋: 窓・ソファ・時計・ランプ"""
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.set_source_rgba(*hexrgb("#f7e8cb"))
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#d9b48a"))
    ctx.rectangle(x, y + h - 52, w, 52)                                          # ゆか
    ctx.fill()
    ctx.move_to(x, y + h - 52)
    ctx.line_to(x + w, y + h - 52)
    _stroke(ctx, 2.6, INK, 0.6)
    # 窓
    wx, wy, ww, wh = x + 24, y + 26, 110, 128
    ctx.rectangle(wx, wy, ww, wh)
    ctx.set_source_rgba(*hexrgb("#bfe2f6"))
    ctx.fill()
    ctx.arc(wx + 80, wy + 34, 16, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#ffe27a"))
    ctx.fill()
    ctx.rectangle(wx, wy, ww, wh)
    _stroke(ctx, 4.0, INK, 0.85)
    ctx.move_to(wx + ww / 2, wy)
    ctx.line_to(wx + ww / 2, wy + wh)
    ctx.move_to(wx, wy + wh / 2)
    ctx.line_to(wx + ww, wy + wh / 2)
    _stroke(ctx, 3.0, INK, 0.8)
    # 時計（秒針が動く）
    cx, cy = x + w - 66, y + 56
    ctx.arc(cx, cy, 30, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.85)
    for ang, ln, wd in ((t * 0.09, 17, 4.0), (t * 1.2, 24, 2.6)):
        ctx.move_to(cx, cy)
        ctx.line_to(cx + ln * math.sin(ang), cy - ln * math.cos(ang))
        _stroke(ctx, wd, RED if wd < 3 else INK, 0.95)
    # ソファ
    sx0 = x + w - 150
    core.rrect(ctx, sx0, y + h - 112, 140, 66, 12)
    ctx.set_source_rgba(*hexrgb("#e59a64"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.8)
    core.rrect(ctx, sx0 - 6, y + h - 82, 152, 38, 10)
    ctx.set_source_rgba(*hexrgb("#d9854f"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.8)
    # ランプ（ゆらぎ）
    lx = x + 168
    ctx.move_to(lx, y + h - 52)
    ctx.line_to(lx, y + h - 150)
    _stroke(ctx, 4.0, INK, 0.8)
    ctx.move_to(lx - 20, y + h - 150)
    ctx.line_to(lx + 20, y + h - 150)
    ctx.line_to(lx + 14, y + h - 182)
    ctx.line_to(lx - 14, y + h - 182)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#ffe9a3", 0.95))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.85)
    ctx.arc(lx, y + h - 140, 40 + 3 * math.sin(t * 2.0), 0, 2 * math.pi)
    ctx.set_source_rgba(1, 0.92, 0.6, 0.18)
    ctx.fill()
    ctx.restore()


# ---------- 絵: 電池の目盛り ----------

def level_color(d):
    if d >= 0.5:
        return "#6cbf78"
    if d >= 0.25:
        return "#f0c24b"
    return "#e0615a"


def draw_gauge(ctx, d, off, cx, y_num, y_bar):
    """スマホの電池の表示（％）。大きな数字と、目盛りの棒"""
    if off:
        text(ctx, "電源が切れた", cx, y_num, 64, RED)
    else:
        text(ctx, pcs(d), cx, y_num, 104, INK)
    bx, bw, bh = 34.0, 366.0, 50.0
    core.rrect(ctx, bx, y_bar, bw, bh, 12)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    _stroke(ctx, 4.0, INK, 0.9)
    core.rrect(ctx, bx + bw + 2, y_bar + 14, 12, bh - 28, 4)                      # 電池の出っぱり
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.fill()
    if d > 0.004:
        core.rrect(ctx, bx + 5, y_bar + 5, (bw - 10) * clamp01(d), bh - 10, 8)
        ctx.set_source_rgba(*hexrgb(level_color(d)))
        ctx.fill()
    for i in range(1, 5):                                                        # 目盛り
        ctx.move_to(bx + bw * i / 5, y_bar + bh - 14)
        ctx.line_to(bx + bw * i / 5, y_bar + bh - 5)
    _stroke(ctx, 2.2, INK, 0.55)


# ---------- 絵: パネル ----------

def panel_xf(k, m):
    s = S0 + (S1 - S0) * m
    y0 = Y_INTRO + (Y_FINAL - Y_INTRO) * m
    xl = CAR_CX - (WC + GAP / 2) * s
    xr = CAR_CX + (GAP / 2) * s
    return (xl if k == "cold" else xr), y0, s


def draw_panel(ctx, k, t, tau, m):
    S = sample()
    q = S["q"]
    x0, y0, s = panel_xf(k, m)
    soc, volt, tb, d = samp_state(k, tau)
    walking = k == "cold"
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(s, s)
    core.rrect(ctx, 0, 0, WC, HC, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    # --- 題・気温 ---
    text(ctx, PANEL_TITLE[k], 22, 32, 42, PINK[k], align="left")
    t_amb = S["t_amb"][k]
    text(ctx, f"{ival(t_amb)}℃", 402, 32, 50, RED, align="right")
    # --- 場面 ---
    ctx.save()
    core.rrect(ctx, BX, BY, BW, BH, 12)
    ctx.clip()
    if walking:
        scene_out(ctx, BX, BY, BW, BH, t)
        walker(ctx, BX + BW / 2 - 20, BY + BH - 14, 1.5, 0, t, True, puff=1.0, scarf=True, phase=0.0)
    else:
        scene_in(ctx, BX, BY, BW, BH, t)
        walker(ctx, BX + BW / 2 - 20, BY + BH - 14, 1.5, 2, t, False, puff=0.0, scarf=False, phase=1.3)
    ctx.restore()
    core.rrect(ctx, BX, BY, BW, BH, 12)
    _stroke(ctx, 3.6, INK, 0.85)
    # --- 電池の表示 ---
    off = d <= 0.0 and tau > 0.0
    draw_gauge(ctx, d, off, WC / 2, 442, 500)
    if k == "cold" and any(tg <= t <= tg + 1.6 for tg in GAKU):                 # ガクッ
        tg = max(x for x in GAKU if x <= t)
        u = clamp01((t - tg) / 0.15) * (1 - clamp01((t - tg - 1.3) / 0.3))
        sc = 1 + 0.25 * (1 - ease_out((t - tg) / 0.2))
        ctx.save()
        ctx.translate(374, 416)
        ctx.scale(sc, sc)
        text(ctx, "ガクッ", 0, 0, 44, RED, alpha=u)
        ctx.restore()
    # --- 下の帯 ---
    text(ctx, "たとえば、この1回では", WC / 2, 584, 30, PENCIL, bold=False)
    text(ctx, f"歩いて {int(tau)}分後", 24, 624, 34, INK, align="left")
    if t >= T_VERD:
        u = clamp01((t - T_VERD) / 0.35)
        lab = f"−{pt_i(S['d0'] - samp_state(k, TAU_END)[3])}ポイント"
        colr = RED if k == "cold" else INK
        text(ctx, lab, WC / 2, 682, 42, colr, alpha=u)
        note.pen_circle(ctx, WC / 2, 682, core.text_width(lab, 42) / 2 + 16, 27, colr, seed=70 + (k == "warm"), width=4.5, progress=u)
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
    tau = tau_of(t)
    m = INTRO.moved(t)
    ctx.push_group()
    z = 1.0 + 0.08 * (1 - ease(clamp01(t / 1.1)))           # 冒頭1秒: 2つの場面が少し寄った所から引く（動きのため・下端を固定）
    if z > 1.0:
        ctx.translate(540, 1440)
        ctx.scale(z, z)
        ctx.translate(-540, -1440)
    for k in ("cold", "warm"):
        draw_panel(ctx, k, t, tau, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 1万回のマス目（1つ） ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_Y0 = 614.0
_GRID = {}
_FLAGS = {}


def cell_flags():
    """1万回の 外のほうが大きく減った(1)/そうでない(0)。試行番号の順"""
    if "f" not in _FLAGS:
        r = results()
        _FLAGS["f"] = (r["dc"] > r["dw"]).astype(int)
    return _FLAGS["f"]


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 6:
        _GRID.clear()
    fl = cell_flags()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(LESS_COL), bgra(MORE_COL)], np.uint8)
    m = len(fl) if n >= len(fl) else (int(n) // G_COLS) * G_COLS
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[fl[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    if t >= T_ANS2:
        return 1 - ease((t - T_ANS2) / 0.35)
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    prog = clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    fl = cell_flags()
    n = len(fl) * prog
    surf, _ = grid_surface(n)
    gw, gh = G_COLS * G_CELL, G_ROWS * G_CELL
    gx = CAR_CX - gw / 2
    ctx.set_source_surface(surf, gx, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(gx - 4, G_Y0 - 4, gw + 7, gh + 7)
    ctx.stroke()
    # 凡例（色の見本）
    sz = 28
    w1, w2 = core.text_width("外のほうが大きく減った", sz, False), core.text_width("そうでない", sz, False)
    tot = 28 + 10 + w1 + 36 + 28 + 10 + w2
    x = CAR_CX - tot / 2
    yl = G_Y0 + gh + 36
    for col, lab, ww in ((MORE_COL, "外のほうが大きく減った", w1), (LESS_COL, "そうでない", w2)):
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(x, yl - 14, 28, 28)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x, yl - 14, 28, 28)
        ctx.stroke()
        text(ctx, lab, x + 38, yl, sz, INK, align="left", bold=False, alpha=a)
        x += 38 + ww + 36
    text(ctx, f"1マス＝1回（{fmt(round(len(fl) * prog / 100.0) * 100)}回）", CAR_CX, yl + 38, 28, INK, bold=False, alpha=a)
    if t >= T_G1 + 0.1:
        u = ease_out((t - T_G1 - 0.1) / 0.3) * a
        text(ctx, f"外のほうが大きく減った  {pc1(sh['p'])}", CAR_CX, yl + 92, 46, RED, alpha=u)
    if t >= T_G1 + 0.9:
        u = ease_out((t - T_G1 - 0.9) / 0.3) * a
        text(ctx, f"減り方は 外が中の {sh['r']:.1f}倍（中央値）", CAR_CX, yl + 142, 36, INK_C, alpha=u)


# ---------- 答え・理由・ひねり ----------

def answer_key():
    sh = shown()
    return sh["key"]


def draw_bar_pair(ctx, y_top, rows, a, bar_x=110.0, bar_w=600.0, bar_h=50.0):
    """横の棒を縦に並べる。rows = [(ラベル, 割合, 色)]。棒の右にその％"""
    y = y_top
    ends = []
    for lab, frac, col in rows:
        text(ctx, lab, bar_x, y, 36, INK, align="left", alpha=a)
        by = y + 24
        core.rrect(ctx, bar_x, by, bar_w, bar_h, 10)
        ctx.set_source_rgba(1, 1, 1, 0.95 * a)
        ctx.fill_preserve()
        _stroke(ctx, 3.6, INK, 0.9 * a)
        if frac > 0.004:
            core.rrect(ctx, bar_x + 4, by + 4, (bar_w - 8) * clamp01(frac), bar_h - 8, 7)
            ctx.set_source_rgba(*hexrgb(col, a))
            ctx.fill()
        text(ctx, pcs(frac), bar_x + bar_w + 18, by + bar_h / 2, 48, INK, align="left", alpha=a)
        ends.append((bar_x + 4 + (bar_w - 8) * clamp01(frac), by, by + bar_h))
        y += 112
    return ends


def reason_text():
    sh = shown()
    k = answer_key()
    l1 = f"外のほうが大きく減った回は {pc1(sh['p'])}"
    l2 = f"減り方は 外が中の {sh['r']:.1f}倍（中央値）"
    l3 = "寒さで電池の中が電気を通しにくくなり"
    l4 = "電圧が下がると 表示の％が下がる" if k == "cold" else "どちらも 同じくらい効く"
    return f"この置き方なら\n{l1}\n{l2}\n{l3}\n{l4}"


TWIST_Q = "では、ポケットで\n温めたら？"


def twist_text():
    sh = shown()
    return f"この置き方なら 表示の％が戻った回は {pcs(sh['back_p'])}\n戻った分の中央値は +{pt_i(sh['back_med_up'])}ポイント"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    S = sample()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"正解は {'ABC'[CORRECT]}、{KEY_LABEL[key]}。", 520, 1378, 50, "yellow", fg=RED, a=b, tilt=-0.02)
    r_a = 1 - ease((t - T_DOOR) / 0.3) if t >= T_DOOR else 1.0
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2 - 0.1) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 520, 735, 32, "blue", a=c, tilt=0.012)
        e = ease_out((t - T_ANS2 - 1.6) / 0.3) * r_a
        if e > 0:
            text(ctx, "たとえば、この1回では（寒い外・歩き終わり）", 520, 940, 28, INK, bold=False, alpha=e)
            ends = draw_bar_pair(ctx, 985, [("中の電気の量", S["soc_end"], "#7ec08a"), ("表示の％", S["d_end"], COL_C)], e)
            xt = ends[0][0]
            ctx.set_source_rgba(*hexrgb(RED, 0.85 * e))
            ctx.set_line_width(3.4)
            ctx.set_dash([8, 6])
            ctx.move_to(xt, ends[0][1] - 4)
            ctx.line_to(xt, ends[1][2] + 6)
            ctx.stroke()
            ctx.set_dash([])
            gap = pt_i(S["soc_end"] - S["d_end"])
            text(ctx, f"表示のほうが {gap}ポイント低い", 520, 1215, 38, RED, alpha=e)
    if t >= T_DOOR:
        d = ease_out((t - T_DOOR - 0.15) / 0.3)
        note.sticky(ctx, TWIST_Q, 520, 700, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_DOOR2:
        e = ease_out((t - T_DOOR2) / 0.3)
        text(ctx, "歩き終わりの表示", 520, 850, 30, INK, bold=False, alpha=e)
        ends = draw_bar_pair(ctx, 925, [("ポケットに入れる前", S["d_end"], COL_C), ("ポケットで温めたあと", S["d_back"], "#7ec08a")], e)
        text(ctx, twist_text(), 520, 1225, 32, INK, alpha=e)


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


CD_X, CD_Y = 590.0, 1015.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい）・前提・三択（横1列）。その下に 寒い外と暖かい部屋（0秒目から雪が降り、人が歩く）"""
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
            text(ctx, DETAIL, 565, 742, 30, INK, bold=False, alpha=a1)
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
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたのスマホ、\n冬の外で急に減ったこと、\nありますか？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 580, 1090, 36, INK, bold=False, alpha=r)


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
    wind = noise_band(t_end, 300, 3, 2.6)                 # 冬の風（ひゅー）
    tt = np.arange(len(wind)) / SR
    env_ = (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, wind * env_, 0.45)
    k = 0.0
    while k < T_FIN2 - 0.3:                               # 雪を踏む足音（ざくっ）
        mx.add(k, tick(520, 0.05), 0.2)
        k += 0.48 if k < T_GO else 0.34
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.30)
    for tg in GAKU:
        mx.add(tg - 0.1, blip(311.1, 0.22), 0.45)         # ガクッ（低い音）
        mx.add(tg + 0.12, blip(233.1, 0.28), 0.4)
    mx.add(T_VERD + 0.2, bell(523.3, 1.2), 0.45)
    mx.add(T_VERD + 0.5, bell(784.0, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_DOOR, blip(1318.5, 0.18), 0.45)
    mx.add(T_DOOR + 0.28, blip(987.8, 0.3), 0.45)
    mx.add(T_DOOR2, blip(659.3, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def _scalar_state(q, i, t_amb, t):
    """1回ぶんを math だけで計算し直す。(残量, 電圧, 電池の温度, 表示)。電源が切れるなら表示は 0"""
    g = lambda k: float(q[k][i])    # noqa: E731
    te = t_amb + g("heat")
    tb = te + (g("t0") - te) * math.exp(-t / g("tau"))
    cam = min(max(t - g("cam_at"), 0.0), g("t_cam"))
    soc = g("soc0") - (g("p_base") * t + g("p_cam") * cam) / 60.0 / (g("cap") * g("health"))
    p = g("p_base") + (g("p_cam") if g("cam_at") <= t < g("cam_at") + g("t_cam") else 0.0)
    r = g("r25") * (1 + 4 * (1 - g("health"))) * g("m0") ** ((25.0 - tb) / 25.0)
    xs, ys = list(SOC_T), list(V_T)

    def interp(x, X, Y):
        if x <= X[0]:
            return Y[0]
        for j in range(1, len(X)):
            if x <= X[j]:
                return Y[j - 1] + (Y[j] - Y[j - 1]) * (x - X[j - 1]) / (X[j] - X[j - 1])
        return Y[-1]
    o = interp(soc, xs, ys)
    disc = o * o - 4 * r * p
    if disc < 0:
        return soc, o / 2, tb, 0.0
    v = (o + math.sqrt(disc)) / 2
    return soc, v, tb, 0.0 if v < g("vcut") else interp(v, ys, xs)


def run_checks():
    sh = shown()
    r = results()
    q = r["q"]
    checks = []
    # (1) 配列版の計算と、math だけで計算し直した値が合う（外・中・歩き始め・歩き終わり・カメラの最中）
    mx = dict(soc=0.0, v=0.0, tb=0.0, d=0.0)
    for i in range(300):
        for t_amb, t in ((q["t_out"][i], 0.0), (q["t_out"][i], q["walk"][i]), (q["t_room"][i], q["walk"][i]),
                         (q["t_out"][i], q["cam_at"][i] + 0.5 * q["t_cam"][i])):
            a = [float(x) for x in state({k: float(v[i]) for k, v in q.items()}, float(t_amb), float(t))]
            b = _scalar_state(q, i, float(t_amb), float(t))
            for name, x, y in zip(("soc", "v", "tb", "d"), a, b):
                mx[name] = max(mx[name], abs(x - y))
    checks.append(("残量: 配列版 − 計算し直し（最大）", mx["soc"], 0.0, 1e-9))
    checks.append(("電圧: 配列版 − 計算し直し（最大・V）", mx["v"], 0.0, 1e-9))
    checks.append(("電池の温度: 配列版 − 計算し直し（最大・℃）", mx["tb"], 0.0, 1e-9))
    checks.append(("表示の％: 配列版 − 計算し直し（最大）", mx["d"], 0.0, 1e-9))
    # (2) 使った電力（足し算 0.05分刻み）と、残量の減り（式）が合う
    mx_e = 0.0
    for i in range(40):
        i_q = {k: float(v[i]) for k, v in q.items()}
        e = 0.0
        dt = 0.05
        for s in range(int(round(i_q["walk"] / dt))):
            tm = (s + 0.5) * dt
            e += (i_q["p_base"] + (i_q["p_cam"] if i_q["cam_at"] <= tm < i_q["cam_at"] + i_q["t_cam"] else 0.0)) * dt / 60.0
        soc_sum = i_q["soc0"] - e / (i_q["cap"] * i_q["health"])
        mx_e = max(mx_e, abs(soc_sum - float(state(i_q, i_q["t_out"], i_q["walk"])[0])))
    checks.append(("使った電力の足し算 − 残量の式（最大）", mx_e, 0.0, 2e-3))
    # (3) 電圧の式: 使う電力 P = V × I、I = (OCV − V) ÷ R が両方成り立つ（V = OCV − R×P÷V の残差）
    res_v = 0.0
    for i in range(300):
        i_q = {k: float(v[i]) for k, v in q.items()}
        soc, v, tb, _ = state(i_q, i_q["t_out"], i_q["walk"])
        rr = i_q["r25"] * (1 + 4 * (1 - i_q["health"])) * i_q["m0"] ** ((25.0 - float(tb)) / 25.0)
        if float(ocv(soc)) ** 2 >= 4 * rr * i_q["p_base"]:
            res_v = max(res_v, abs(float(v) - (float(ocv(soc)) - rr * i_q["p_base"] / float(v))))
    checks.append(("電圧の式 V = OCV − R×P÷V の残差（最大・V）", res_v, 0.0, 1e-9))
    # (4) 開放電圧の表: 増える一方（逆関数が使える）。逆にして戻る
    checks.append(("開放電圧の表が 残量とともに増える", float(np.all(np.diff(V_T) > 0)), 1.0, 0.0))
    xs = np.linspace(0.0, 1.0, 101)
    checks.append(("OCV の逆関数 → 元に戻る（最大）", float(np.max(np.abs(ocv_inv(ocv(xs)) - xs))), 0.0, 1e-12))
    # (5) 温度の倍率: 25℃で1倍、0℃で m0 倍、寒いほど大きい。外の抵抗 ≧ 部屋の抵抗（全回・歩き終わり）
    checks.append(("温度の倍率 25℃ → 1", float(f_temp(2.5, 25.0)), 1.0, 1e-12))
    checks.append(("温度の倍率 0℃ → m0", float(f_temp(2.5, 0.0)), 2.5, 1e-12))
    r_c = q["r25"] * f_temp(q["m0"], batt_temp(q, q["t_out"], q["walk"]))
    r_w = q["r25"] * f_temp(q["m0"], batt_temp(q, q["t_room"], q["walk"]))
    checks.append(("外の内部抵抗 ≧ 部屋の内部抵抗（全回）", float(np.all(r_c >= r_w)), 1.0, 0.0))
    # (6) 同じ使い方: はじめの表示は 外も中も同じ（出発の温度が同じ）。電池の中の電気の減りも同じ
    checks.append(("はじめの表示 外 − 中（最大）", float(np.max(np.abs(r["d0"] - r["d0_room"]))), 0.0, 1e-12))
    checks.append(("はじめの温度は 外も中も同じ（歩き始め・最大・℃）",
                   float(np.max(np.abs(batt_temp(q, q["t_out"], 0.0) - batt_temp(q, q["t_room"], 0.0)))), 0.0, 1e-12))
    checks.append(("歩き終わりの中の電気の量は 外も中も同じ（最大）",
                   float(np.max(np.abs(state(q, q["t_out"], q["walk"])[0] - state(q, q["t_room"], q["walk"])[0]))), 0.0, 1e-12))
    # (7) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key = answer_by_rule(sh["p"], sh["r"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号は C", float(INTRO.correct), 2.0, 0.0))
    checks.append(("規則の境目（p≥60% かつ r≥1.2 / p≤40% かつ r≤0.83）の例: 0.7,1.3→cold 0.3,0.8→use 0.5,1.0→same",
                   float(answer_by_rule(0.7, 1.3) == "cold" and answer_by_rule(0.3, 0.8) == "use" and answer_by_rule(0.5, 1.0) == "same"), 1.0, 0.0))
    # (8) マス目: 1万回すべて。外のほうが大きく減った回数が、画面の割合と同じ
    checks.append(("マス目の数 = 1万回", float(G_COLS * G_ROWS), float(N_TRIAL), 0.0))
    checks.append(("マス目の「外のほうが大きく減った」割合 = p", float(cell_flags().mean()), sh["p"], 1e-12))
    # (9) 見本: 1万回の中の1回で、外・中とも電源が切れず、結果が多数派と同じ、ポケットで戻る。歩く時間が早送りの終わりと同じ
    S = sample()
    i = S["i"]
    checks.append(("見本は外のほうが大きく減った（多数派と同じ）", float(S["dc"] > S["dw"]), float(sh["p"] >= 0.5), 0.0))
    checks.append(("見本は外・中とも電源が切れない", float(not (shut_down(q, q["t_out"])[i] or shut_down(q, q["t_room"])[i])), 1.0, 0.0))
    checks.append(("見本の歩く時間 = 早送りの終わり（分）", TAU_END, float(q["walk"][i]), 1e-9))
    checks.append(("見本は ポケットで温めると表示が戻る", float(S["d_back"] > S["d_end"]), 1.0, 0.0))
    s0c, s0w = samp_state("cold", 0.0), samp_state("warm", 0.0)
    checks.append(("見本のはじめの表示 外 − 中", s0c[3] - s0w[3], 0.0, 1e-12))
    sec = samp_state("cold", TAU_END)
    checks.append(("見本 歩き終わりの表示（画面）= 1万回の値", sec[3], float(r["d_end"][i]), 1e-12))
    checks.append(("見本 歩き終わりの中の電気の量（画面）= 1万回の値", sec[0], float(r["soc_end"][i]), 1e-12))
    checks.append(("見本の外の減り − 画面の差", S["d0"] - sec[3], float(r["dc"][i]), 1e-12))
    checks.append(("画面の「ガクッ」が1回出る", float(len(GAKU)), 1.0, 0.0))
    # (10) 大きく見て: 外が寒いほど、減りの差（外 − 中）が大きい（三分位）
    d = r["dc"] - r["dw"]
    o = q["t_out"]
    q1, q2 = np.quantile(o, [1 / 3, 2 / 3])
    checks.append(("外が寒い三分位ほど 減りの差が大きい", float(d[o <= q1].mean() > d[(o > q1) & (o < q2)].mean() > d[o >= q2].mean()), 1.0, 0.0))
    checks.append(("戻った割合は 0〜1", float(0.0 <= sh["back_p"] <= 1.0), 1.0, 0.0))
    check_answers(checks)


def lint():
    """書き出さずに、公開前チェック（文字の位置・大きさ・読み切れる長さ・0.3秒の動き）だけを回す"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    n = int(round(DURATION * FPS))
    core._LOG = []
    first = probe = None
    for i in range(n):
        core._CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        surf.flush()
        if i == 0:
            first = np.frombuffer(bytes(surf.get_data()), np.uint8)
        elif i == int(0.3 * FPS):
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
    log, core._LOG = core._LOG, None
    problems = core.preflight(log, first, probe, DURATION, build_audio())
    if problems:
        print("公開前チェック: 要対応")
        for s in problems:
            print("  -", s)
    else:
        print("公開前チェック: OK")
    return problems


def report_full():
    sm = sample()
    q = sm["q"]
    print(f"長さ {DURATION:.1f}秒  早送り終わり {T_FIN2:.1f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_DOOR:.1f}/{T_DOOR2:.1f}  締め {T_Q:.1f}  ガクッ {[round(x, 1) for x in GAKU]}")
    print(f"  見本: 回{sm['i']} 外{q['t_out']:.1f}℃ 部屋{q['t_room']:.1f}℃ 歩く{q['walk']:.0f}分 はじめ{sm['d0'] * 100:.0f}% 外の減り{sm['dc'] * 100:.0f}pt 中の減り{sm['dw'] * 100:.0f}pt "
          f"外の歩き終わり 表示{sm['d_end'] * 100:.0f}% 中の電気{sm['soc_end'] * 100:.0f}% ポケット後{sm['d_back'] * 100:.0f}%")
    print("  理由:", reason_text().replace("\n", " / "), "|", TWIST_Q.replace("\n", ""), "|", twist_text().replace("\n", " / "))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--lint" in sys.argv:
        lint()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, 5.8, 7.0, 9.0, 11.0, T_VERD - 0.3, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.6, T_ANS2 + 2.6, T_DOOR + 0.7, T_DOOR2 + 0.7, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" not in sys.argv and "--model" not in sys.argv:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
