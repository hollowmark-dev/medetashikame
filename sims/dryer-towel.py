"""お風呂上がり、タオルで拭いてからドライヤー？ すぐドライヤー？ どっちが早く乾く？ 同じ人・同じ髪・同じドライヤーで1万回。— 2026-10-22 作成（公開予定 10/27・30秒前後）

くらべるのは「早く乾くか」だけ（お金・電気代・髪の傷みは入れない。画面にも概要欄にも書かない）。

モデル（髪の「残りの水」。お風呂を出たときの水の量を 1 とした割合 f）
  髪の長さ: ショート 30% / ミディアム 40% / ロング 30%（割合は仮定）。
  お風呂を出たときの髪の水の量 w0 = 乾いた髪の重さ × 1.0〜1.5（仮定）。
      乾いた髪の重さ（仮定）: ショート 30〜45 g / ミディアム 50〜70 g / ロング 80〜110 g。
      根拠: 髪の中に入る水は乾いた髪の約30〜35%（「健康毛は自重の30〜35%の水を吸う」「浸して1分未満で飽和」という文献の記述・
      Water Distribution Human Hair, J. Soc. Cosmet. Chem. など。本文は未確認、検索結果の要約）。そこに、髪と髪のあいだ・表面に付く水を足して、
      お風呂を出たときは乾いた髪の重さの 1.0〜1.5 倍と仮定した（浸した髪が約124%という特許の記述も参考。タオルドライ直後の測定値は見つからなかった）。
  「乾いた」＝ 髪の残りの水が、お風呂を出たときの 1割（f = 0.10）になった時点。
      1割は乾いた髪の重さの 10〜15% にあたり、部屋の湿度（65%前後）で髪が持っている水分（乾いた髪の14〜16%という解説）と同じくらい。
  タオルで拭く: 拭く時間 t_w = 30〜90秒（1回ごとにでたらめ）。取れる水は 上限 Q（40〜60%）に向かって だんだん減りにくくなる指数形
      取れた割合 = Q × (1 − exp(−t_w / τ))、τ = 30〜50秒（仮定）。
  ドライヤー: 乾く速さ（水が減る速さ）は、水が多いうち（f が f_c = 0.25〜0.40 より多い間）は一定（r_max）で、
      それより少なくなると 残りの水に比例して遅くなる（髪の芯に近い水は抜けにくい・よくある乾燥の形・仮定）。
      df/dt = −(1/c) × min(1, f / f_c)、c = w0 / r_max（秒。f=1 を最高の速さで飛ばしきる時間）。
      f から「乾いた」（0.10）までの時間 = c × g(f)、g(f) = (f − f_c) + f_c × ln(f_c / 0.10)（f ≥ f_c のとき）。
  ドライヤーの速さの大きさ: 「普通のタオルで軽く拭いたあと、ロング約6分半・ミディアム約5分・ボブ約4分」（マイベスト
      https://my-best.com/2797 。測定条件の細部は載っていない）に合わせる。
      → 標準の拭き方（60秒・Q=0.5・τ=40秒 → 拭いたあとの水は f=0.61）、f_c=0.325、ドライヤーの強さ 1.0 のとき、
        ショート（ボブ）240秒 / ミディアム300秒 / ロング390秒で「乾いた」になるよう r_max（g/秒）を長さごとに決めた（仮定の中心値）。
      1回ごとに ドライヤーの強さ（r_max の倍率）を 0.8〜1.25 倍でたらめ（機種・風量の違い・仮定）。左右の2人は同じ。
  測るもの: お風呂を出てから「乾いた」まで。拭く人は 拭く時間も含める。
      すぐドライヤー: T_dry = c × g(1)（最初の多い水を飛ばす時間が足される）。
      拭いてから: T_tw = t_w + c × g(f_w)、f_w = 1 − Q(1 − exp(−t_w/τ))。
  1回ごとに すべて でたらめに変える。左右は同じ人・同じ髪・同じ水の量・同じドライヤー。違うのは 拭くかどうかだけ。

問い: 「お風呂上がり、タオルで拭いてから／ドライヤー？すぐドライヤー？／どっちが早く乾く？」（前提「同じ人・同じ髪・同じドライヤー」）
      選択肢（記号の並びは LABELS の順。正解・TAG は 計算の結果で決める）: 拭いてから ／ ほぼ同じ ／ すぐドライヤー
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「拭いてからの人が先に乾いた回」の割合 p と、乾いた時刻の差（すぐ − 拭いてから）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 30秒 なら「拭いてから」、p ≤ 40% かつ g ≤ −30秒 なら「すぐドライヤー」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。拭く時間を 10〜240秒に変えて同じ1万回を計算し直し、差の真ん中の値が いちばん大きくなる拭く時間（それ以上は差が増えない）。
締め: 「あなたは、拭く派？すぐドライヤー派？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（並んで乾く2人）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "dryer-towel"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261027
DRY_AT = 0.10                                      # 残りの水がこの割合になったら「乾いた」
LENS = ("short", "mid", "long")
P_LEN = (0.30, 0.40, 0.30)
DRY_MASS = {"short": (30.0, 45.0), "mid": (50.0, 70.0), "long": (80.0, 110.0)}   # g（乾いた髪）
W_RATIO = (1.0, 1.5)
T_WIPE, Q_WIPE, TAU_WIPE = (30.0, 90.0), (0.40, 0.60), (30.0, 50.0)
FC = (0.25, 0.40)
POWER = (0.80, 1.25)
# 標準（マイベスト）: 軽く拭いたあとの乾く時間（秒）
T_STD = {"short": 240.0, "mid": 300.0, "long": 390.0}
STD_WIPE = (60.0, 0.5, 40.0)                       # 秒・Q・τ
FC0 = 0.325

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 30.0      # 秒


def answer_by_rule(p_tw, gap_med_sec):
    """p_tw = 拭いてからが先に乾いた回の割合、gap_med_sec = (すぐ − 拭いてから) の乾いた時刻の差の真ん中の値（秒）。'tw' / 'same' / 'dr'"""
    if p_tw >= RULE_HI and gap_med_sec >= RULE_GAP:
        return "tw"
    if p_tw <= RULE_LO and gap_med_sec <= -RULE_GAP:
        return "dr"
    return "same"


def g_fun(f, fc):
    """f から DRY_AT までの時間 ÷ c"""
    f = np.asarray(f, float)
    hi = (f - fc) + fc * np.log(fc / DRY_AT)
    lo = fc * np.log(np.maximum(f, 1e-9) / DRY_AT)
    return np.where(f >= fc, hi, lo)


def f_wipe(tw, Q, tau):
    return 1.0 - Q * (1.0 - np.exp(-np.asarray(tw, float) / tau))


def w0_center(L):
    lo, hi = DRY_MASS[L]
    return 0.5 * (lo + hi) * 0.5 * (W_RATIO[0] + W_RATIO[1])


def rmax_center(L):
    """標準の条件で T_STD になる r_max（g/秒）"""
    fstd = float(f_wipe(STD_WIPE[0], STD_WIPE[1], STD_WIPE[2]))
    c_std = T_STD[L] / float(g_fun(fstd, FC0))
    return w0_center(L) / c_std


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    li = rng.choice(3, size=n, p=P_LEN)
    dm = np.zeros(n)
    rc = np.zeros(n)
    for k, L in enumerate(LENS):
        lo, hi = DRY_MASS[L]
        dm[li == k] = rng.uniform(lo, hi, int((li == k).sum()))
        rc[li == k] = rmax_center(L)
    ratio = u(W_RATIO)
    return dict(li=li, dm=dm, w0=dm * ratio, rmax=rc * u(POWER), tw=u(T_WIPE), Q=u(Q_WIPE), tau=u(TAU_WIPE), fc=u(FC))


def times(d, tw=None):
    """(すぐドライヤーの乾く時刻, 拭いてからの乾く時刻, 拭いたあとの水 f_w)  秒"""
    c = d["w0"] / d["rmax"]
    t_w = d["tw"] if tw is None else tw
    fw = f_wipe(t_w, d["Q"], d["tau"])
    t_dr = c * g_fun(1.0, d["fc"])
    t_tw = t_w + c * g_fun(fw, d["fc"])
    return t_dr, t_tw, fw


def alt_exp_times(d):
    """べつの乾き方（検証用）: 速さが 残りの水に比例（指数形）。同じ標準の条件（60秒拭いたあとのミディアム等）に合わせ直す"""
    # f から DRY_AT まで c' × ln(f / DRY_AT)。標準で T_STD になる c'
    fstd = float(f_wipe(STD_WIPE[0], STD_WIPE[1], STD_WIPE[2]))
    cs = np.array([T_STD[L] / math.log(fstd / DRY_AT) for L in LENS])
    c = cs[d["li"]] * (d["w0"] / np.array([w0_center(L) for L in LENS])[d["li"]]) * (np.array([rmax_center(L) for L in LENS])[d["li"]] / d["rmax"])
    fw = f_wipe(d["tw"], d["Q"], d["tau"])
    return c * np.log(1.0 / DRY_AT), d["tw"] + c * np.log(fw / DRY_AT)


def f_dry(s, f0, c, fc):
    """ドライヤーを s 秒かけたあとの水 f（f0 から）"""
    s = np.asarray(s, float)
    s1 = np.maximum(f0 - fc, 0.0) * c                      # f_c まで一定の速さで下がる時間
    f_hi = f0 - s / c
    f_start_lo = np.minimum(f0, fc)
    f_lo = f_start_lo * np.exp(-(s - s1) / (fc * c))
    return np.where(s <= s1, f_hi, f_lo)
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
    t_dr, t_tw, fw = times(d)
    _RES["m"] = dict(p=d, t_dr=t_dr, t_tw=t_tw, fw=fw)
    return _RES["m"]


SWEEP = np.arange(10, 245, 5)


def sweep():
    """拭く時間だけを変えて、同じ1万回の差（すぐ − 拭いてから）の真ん中の値"""
    r = results()
    d = r["p"]
    out = []
    for t in SWEEP:
        t_dr, t_tw, _ = times(d, tw=float(t))
        out.append(float(np.median(t_dr - t_tw)))
    return np.array(out)


def shown():
    r = results()
    p = r["p"]
    tt, td = r["t_tw"], r["t_dr"]
    gap = td - tt
    win = tt < td
    sw = sweep()
    ipk = int(np.argmax(sw))
    out = dict(p_tw=float(win.mean()), n_tw=int(win.sum()), n_dr=int((~win).sum()),
               gap_med=float(np.median(gap)), gap_mean=float(gap.mean()), gap_q=np.percentile(gap, [10, 25, 75, 90]),
               med_tw=float(np.median(tt)), med_dr=float(np.median(td)),
               q_tw=np.percentile(tt, [10, 90]), q_dr=np.percentile(td, [10, 90]),
               sw=sw, t_peak=float(SWEEP[ipk]), g_peak=float(sw[ipk]), g_at_240=float(sw[-1]),
               med_wipe=float(np.median(p["tw"])), med_fw=float(np.median(r["fw"])),
               by_len=[(L, float((win[p["li"] == k]).mean()), float(np.median(gap[p["li"] == k])),
                        float(np.median(td[p["li"] == k])), float(np.median(tt[p["li"] == k]))) for k, L in enumerate(LENS)])
    ta, tb = alt_exp_times(p)
    out["alt"] = (float((tb < ta).mean()), float(np.median(ta - tb)))
    # 拭く時間で分けた差の真ん中の値
    bins = [(30, 45), (45, 60), (60, 75), (75, 90)]
    out["by_wipe"] = [(a, b, float(np.median(gap[(p["tw"] >= a) & (p["tw"] < b + (1 if b == 90 else 0))]))) for a, b in bins]
    return out


def mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def ms(sec):
    """秒 → '6分05秒' / '45秒'"""
    s = int(round(sec))
    m, r = divmod(s, 60)
    return f"{m}分{r:02d}秒" if m else f"{r}秒"


def about(sec):
    """約 の付く短い言い方（10秒きざみ。30秒は『半』）"""
    s = int(round(sec / 10.0)) * 10
    m, r = divmod(s, 60)
    if m and r == 30:
        return f"約{m}分半"
    if m and r:
        return f"約{m}分{r}秒"
    if m:
        return f"約{m}分"
    return f"約{r}秒"


def report():
    sh = shown()
    print(f"拭いてからが先 {sh['p_tw']:.4f}（{sh['n_tw']}回 / すぐが先 {sh['n_dr']}回）  差(すぐ−拭いてから)の中央値 {sh['gap_med']:+.1f}秒 "
          f"平均 {sh['gap_mean']:+.1f}  10/25/75/90% {np.round(sh['gap_q'], 0)}")
    print(f"  答え {answer_by_rule(sh['p_tw'], sh['gap_med'])}")
    print(f"  乾く時間の中央値 拭いてから {sh['med_tw']:.0f}秒（{ms(sh['med_tw'])}）10/90% {np.round(sh['q_tw'], 0)} / "
          f"すぐ {sh['med_dr']:.0f}秒（{ms(sh['med_dr'])}）10/90% {np.round(sh['q_dr'], 0)}")
    for L, pw, g, mdr, mtw in sh["by_len"]:
        print(f"  {L}: 拭いてからが先 {pw:.3f} 差 {g:+.0f}秒  すぐ {mdr:.0f}秒 / 拭いてから {mtw:.0f}秒")
    print("  拭く時間で分けた差:", [(a, b, round(g)) for a, b, g in sh["by_wipe"]])
    print(f"  拭く時間 {SWEEP[0]}〜{SWEEP[-1]}秒の差の中央値: ピーク {sh['t_peak']:.0f}秒で {sh['g_peak']:+.0f}秒 / 240秒で {sh['g_at_240']:+.0f}秒")
    print("   ", [(int(t), round(g)) for t, g in zip(SWEEP[::4], sh['sw'][::4])])
    print(f"  拭いたあとの水 f_w の中央値 {sh['med_fw']:.2f}  拭く時間の中央値 {sh['med_wipe']:.0f}秒")
    print(f"  乾き方を指数形に変えると: 拭いてからが先 {sh['alt'][0]:.3f} 差 {sh['alt'][1]:+.0f}秒")


def numeric_check(k=300):
    """足し算（1秒きざみ）で、式の乾く時刻を確かめる。最大の食い違い（割合）"""
    d = {kk: v[:k] for kk, v in results()["p"].items()}
    t_dr, t_tw, fw = times(d)
    c = d["w0"] / d["rmax"]
    worst = 0.0
    for i in range(k):
        for f0, t_off, ref in ((1.0, 0.0, t_dr[i]), (fw[i], d["tw"][i], t_tw[i])):
            f, t = f0, 0.0
            dt = 0.25
            while f > DRY_AT:
                f -= dt / c[i] * min(1.0, f / d["fc"][i])
                t += dt
            worst = max(worst, abs((t + t_off) / ref - 1))
    return worst


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    print(f"  足し算と式の最大の食い違い {numeric_check(60):.4f}")
    sys.exit(0)


# =====================================================================
# 見本（並んで乾く2人）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: ミディアム（マイベストの『約5分』に合わせた長さ）、拭く時間が 40〜52秒（冒頭の早送りの間に拭き終わる）、
    差が真ん中の値の近く（±10%）、すぐドライヤーの時間が その長さの中央値の近く（±8%）。その中で差が真ん中に最も近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    gap = r["t_dr"] - r["t_tw"]
    mid = p["li"] == 1
    med_dr_mid = float(np.median(r["t_dr"][mid]))
    cand = np.nonzero(mid & (p["tw"] > 40) & (p["tw"] < 52) & (np.abs(gap / sh["gap_med"] - 1) < 0.10)
                      & (np.abs(r["t_dr"] / med_dr_mid - 1) < 0.08))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    i = int(cand[np.argmin(np.abs(gap[cand] - sh["gap_med"]))])
    q = {k: (v[i].item() if hasattr(v[i], "item") else v[i]) for k, v in p.items()}
    c = q["w0"] / q["rmax"]
    fw = float(f_wipe(q["tw"], q["Q"], q["tau"]))
    _SAMPLE = dict(i=i, p=q, c=c, fw=fw, t_dr=float(r["t_dr"][i]), t_tw=float(r["t_tw"][i]), gap=float(gap[i]), n_cand=len(cand))
    return _SAMPLE


def f_dr_at(tau):
    """すぐドライヤーの人の、お風呂を出て tau 秒後の水 f"""
    s = sample()
    return float(f_dry(tau, 1.0, s["c"], s["p"]["fc"]))


def f_tw_at(tau):
    """拭いてからの人の、お風呂を出て tau 秒後の水 f"""
    s = sample()
    q = s["p"]
    if tau <= q["tw"]:
        return float(f_wipe(tau, q["Q"], q["tau"]))
    return float(f_dry(tau - q["tw"], s["fw"], s["c"], q["fc"]))


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    p = s["p"]
    print("見本", s["i"], "候補", s["n_cand"], "長さ", LENS[p["li"]], "乾いた髪", round(p["dm"]), "g 水", round(p["w0"]), "g 拭く", round(p["tw"]), "秒 Q", round(p["Q"], 2),
          "τ", round(p["tau"]), "f_c", round(p["fc"], 2), "強さ", round(p["rmax"] / rmax_center(LENS[p["li"]]), 2), "f_w", round(s["fw"], 2),
          "| すぐ", ms(s["t_dr"]), "拭いてから", ms(s["t_tw"]), "差", round(s["gap"]), "秒")
    print("確認: f_dr_at(t_dr) =", round(f_dr_at(s["t_dr"]), 4), " f_tw_at(t_tw) =", round(f_tw_at(s["t_tw"]), 4))
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
note.DATE = "10.27"                                # 日付欄（公開予定日）

COL_T, INK_T = "#8fbbe8", "#2f63a8"                # 拭いてから（水色）
COL_D, INK_D = "#f4ad6a", "#b8601a"                # すぐドライヤー（だいだい）
WATER = "#58a8e4"
SKIN, PJ, PJ_D = "#ffe0c4", "#a8d8c8", "#8cc4b0"   # 肌・パジャマ
HAIR_DRY, HAIR_WET = "#8a5a3c", "#3a3244"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["すぐドライヤー", "ほぼ同じ", "拭いてから"]
TAG = {"tw": "C", "dr": "A"}
CORRECT = 2                                        # answer_by_rule の結果の位置
KEY_LABEL = {"tw": "拭いてから", "same": "ほぼ同じ", "dr": "すぐドライヤー"}
NAME = {"tw": "拭いてから", "dr": "すぐドライヤー"}
COLS = {"tw": COL_T, "dr": COL_D}
INKC = {"tw": INK_T, "dr": INK_D}

BIG_PRE = "お風呂上がり、"                           # 小さめの1行（本体の6割ほど）
BIG_Q = ["拭いてからドライヤー？", "すぐドライヤー？", "どっちが早く乾く？"]
DETAIL = "同じ人・同じ髪・同じドライヤー"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 7.4                                     # T_GO から2人とも乾くまで
R0 = 8.0                                           # 冒頭の進み（シミュの秒／動画の秒）。拭く動きが見える速さ

# 画面の置き場所
PN = {"tw": dict(x0=80.0, x1=520.0, cx=300.0), "dr": dict(x0=580.0, x1=1020.0, cx=800.0)}
PY0, PY1 = 830.0, 1600.0
HYT, PK = 1245.0, 1.3                              # 人の頭の中心（画面）と拡大
HY, HR = 1008.0, 62.0                              # 頭の中心と半径
CARD_Y = 952.0                                     # メーターの帯（パネルの上のほう）
TORSO_B = 2400.0                                   # 体の下端（サムネは画面の下まで伸ばす）


def setup():
    global TL, RX, T_FIN1, T_FIN2, T_G0, T_G1, T_REV, T_ANS2, T_Q, DURATION
    s = sample()
    fins = sorted((s["t_dr"], s["t_tw"]))
    T_FIN2 = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 60, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 800.0
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
    """その時刻の (拭いてからの水, すぐの水)"""
    tau = tau_of(t)
    return f_tw_at(tau), f_dr_at(tau)


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


ZOOM0, ZOOM_T = 1.32, 1.25


def zoom_art(ctx, t, cx):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    ctx.translate(cx, 1300.0)
    ctx.scale(z, z)
    ctx.translate(-cx, -1300.0)


def _limb(ctx, pts, w, col, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(w + 5.0)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def star(ctx, x, y, r, col, a):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.move_to(x, y - r)
    ctx.curve_to(x + 0.12 * r, y - 0.12 * r, x + 0.12 * r, y - 0.12 * r, x + r, y)
    ctx.curve_to(x + 0.12 * r, y + 0.12 * r, x + 0.12 * r, y + 0.12 * r, x, y + r)
    ctx.curve_to(x - 0.12 * r, y + 0.12 * r, x - 0.12 * r, y + 0.12 * r, x - r, y)
    ctx.curve_to(x - 0.12 * r, y - 0.12 * r, x - 0.12 * r, y - 0.12 * r, x, y - r)
    ctx.fill()


# ---------- 絵: 人（正面・パジャマ） ----------
HAIR_BOTTOM = {0: -4.0, 1: HR + 12.0, 2: HR + 80.0}      # 髪の下端（頭の中心から）ショート・ミディアム・ロング


def hair_back(ctx, cx, hy, li, wet, t, blow):
    """うしろの髪。かわくほどふくらみ、かぜで揺れる"""
    dry = 1.0 - wet
    R = HR
    rw = R + 8 + 11 * dry
    rh = R + 9 + 7 * dry
    yb = hy + HAIR_BOTTOM[li]
    wob = (2.0 + 6.0 * dry) * (0.5 + blow)
    pts = []
    for i in range(0, 31):
        a = math.pi + math.pi * i / 30
        k = 1 + wob / 90.0 * math.sin(a * 6 + t * 7.0)
        pts.append((cx + rw * math.cos(a) * k, hy + rh * math.sin(a) * k + 2))
    side = rw * (1.0 + 0.03 * li)
    for j in range(1, 7):
        u = j / 6
        pts.append((cx + side + wob * 0.6 * math.sin(t * 6 + u * 4), hy + 2 + (yb - hy - 2) * u))
    for j in range(0, 9):
        u = j / 8
        pts.append((cx + side - 2 * side * u, yb + 6 * math.sin(math.pi * u) + wob * 0.3 * math.sin(t * 5 + u * 8)))
    for j in range(6, -1, -1):
        u = j / 6
        pts.append((cx - side + wob * 0.6 * math.sin(t * 6 + 2 + u * 4), hy + 2 + (yb - hy - 2) * u))
    col = lerp_col(HAIR_DRY, HAIR_WET, wet ** 0.7)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()
    ctx.set_source_rgba(*col, 1.0)
    ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    _stroke(ctx, 3.4, INK, 0.9)
    return yb, side


def hair_front(ctx, cx, hy, wet, t, blow):
    """前髪（ぬれているとすじに分かれる）"""
    R = HR + 4
    col = lerp_col(HAIR_DRY, HAIR_WET, wet ** 0.7)
    zig = 5 + 12 * wet
    pts = []
    for i in range(0, 25):
        a = math.pi * 1.04 + math.pi * 0.92 * i / 24
        pts.append((cx + R * math.cos(a), hy + 2 + (R + 1) * math.sin(a)))
    n = 10
    for j in range(n + 1):
        u = j / n
        x = cx + R * 0.95 - 2 * R * 0.95 * u
        base = hy - R * 0.50 + 0.52 * R * ((x - cx) / R) ** 2
        y = base + (zig if j % 2 else 0) + 3 * math.sin(t * 6 + j) * blow
        pts.append((x, y))
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()
    ctx.set_source_rgba(*col, 1.0)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)                       # つや
    ctx.arc(cx - 6, hy + 2, R - 10, math.pi * 1.12, math.pi * 1.38)
    _stroke(ctx, 5, "#ffffff", 0.25 + 0.3 * wet)


def draw_towel_head(ctx, cx, hy, dx, rot):
    ctx.save()
    ctx.translate(cx + dx, hy - 48)
    ctx.rotate(rot)
    core.rrect(ctx, -92, -34, 184, 66, 22)
    ctx.set_source_rgba(*hexrgb("#fbf6ee"))
    ctx.fill_preserve()
    _stroke(ctx, 3.6, INK, 0.9)
    ctx.set_source_rgba(*hexrgb("#8fc0e2", 0.95))
    for sx in (-52, 0, 52):
        ctx.rectangle(sx - 9, -30, 18, 58)
        ctx.fill()
    ctx.restore()


def draw_towel_neck(ctx, cx, hy):
    """首にかけたタオル（拭いたあと）"""
    sy = hy + HR + 22
    for sg in (-1, 1):
        ctx.move_to(cx + sg * 22, sy - 10)
        ctx.line_to(cx + sg * 62, sy - 2)
        ctx.line_to(cx + sg * 36, sy + 108)
        ctx.line_to(cx + sg * 4, sy + 94)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#fbf6ee"))
        ctx.fill_preserve()
        _stroke(ctx, 3.4, INK, 0.9)
        ctx.move_to(cx + sg * 14, sy + 52)
        ctx.line_to(cx + sg * 48, sy + 58)
        _stroke(ctx, 11, "#8fc0e2", 0.95)


DRY_S, DOFF = 0.82, 132.0                           # ドライヤーの大きさ・人の中心からの距離（拡大した人が枠に収まるように）


def draw_dryer(ctx, x, y, rot, sx, t_run, on):
    """ドライヤー。ノズルが +x 側（sx=-1 で左右反転）。on のとき風の線"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(sx * DRY_S, DRY_S)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-18, 20)                                          # 持ち手
    ctx.line_to(8, 20)
    ctx.line_to(2, 92)
    ctx.line_to(-26, 92)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#e0605f"))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    core.rrect(ctx, -58, -26, 104, 52, 22)                        # 本体
    ctx.set_source_rgba(*hexrgb("#ef7f7a"))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    ctx.move_to(44, -20)                                          # ノズル
    ctx.line_to(80, -27)
    ctx.line_to(80, 27)
    ctx.line_to(44, 20)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#6d7a8c"))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(3):                                            # 後ろの吸気口
        ctx.move_to(-48, -10 + k * 10)
        ctx.line_to(-36, -10 + k * 10)
        _stroke(ctx, 3, INK, 0.5)
    if on:
        for k, yy in enumerate((-22, -11, 0, 11, 22)):
            ctx.save()
            ctx.set_dash([20, 14], -t_run * 340.0 - k * 7)
            ctx.move_to(86, yy)
            ctx.line_to(86 + 92, yy * 1.5)
            _stroke(ctx, 5.5, "#7fb5de", 0.9)
            ctx.restore()
    ctx.restore()


def xf(x, y, rot, sx, lx, ly):
    px = sx * DRY_S * lx
    ly = ly * DRY_S
    c, s = math.cos(rot), math.sin(rot)
    return x + px * c - ly * s, y + px * s + ly * c


def draw_person(ctx, cx, t, li, f, mode, side, done_u, towel_neck):
    """正面の人。mode = 'towel'（タオルで拭く）/ 'dryer'（ドライヤー）。side = 'tw'（ドライヤーは左から）/ 'dr'（右から）。
    f = 残りの水。done_u = 乾いたあとの進み（0〜1）"""
    wet = clamp01((f - DRY_AT) / (1 - DRY_AT)) ** 0.8
    hy = HY
    ds = -1 if side == "tw" else 1                                  # ドライヤーを持つ側（画面の左 = -1）
    blow = 1.0 if (mode == "dryer" and done_u <= 0) else (0.0 if mode == "dryer" else 0.6)
    yb, side_w = hair_back(ctx, cx, hy, li, wet, t, blow)
    # 首・体
    sy = hy + HR + 30
    ctx.rectangle(cx - 22, hy + HR - 14, 44, 52)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.move_to(cx - 32, sy - 8)
    ctx.curve_to(cx - 90, sy - 4, cx - 118, sy + 6, cx - 124, sy + 46)
    ctx.line_to(cx - 128, TORSO_B)
    ctx.line_to(cx + 128, TORSO_B)
    ctx.line_to(cx + 124, sy + 46)
    ctx.curve_to(cx + 118, sy + 6, cx + 90, sy - 4, cx + 32, sy - 8)
    ctx.curve_to(cx + 14, sy + 26, cx - 14, sy + 26, cx - 32, sy - 8)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(PJ))
    ctx.fill_preserve()
    ctx.save()
    ctx.clip_preserve()
    ctx.set_source_rgba(*hexrgb(PJ_D, 0.9))
    for x in range(-130, 140, 34):
        ctx.rectangle(cx + x, sy - 10, 12, 400)
        ctx.fill()
    ctx.restore()
    _stroke(ctx, 3.6, INK, 0.9)
    if towel_neck:
        draw_towel_neck(ctx, cx, hy)
    # 顔
    ctx.arc(cx, hy + 4, HR, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.6, INK, 0.9)
    ctx.set_source_rgba(*hexrgb("#f2a3a0", 0.55))                    # ほお
    for sg in (-1, 1):
        ctx.arc(cx + sg * 36, hy + 30, 11, 0, 2 * math.pi)
        ctx.fill()
    blink = 0.12 if (t % 3.1) < 0.12 else 1.0
    happy = clamp01(done_u)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for sg in (-1, 1):                                                # 目・まゆ
        ex, ey = cx + sg * 23, hy + 12
        if happy > 0.5:
            ctx.arc(ex, ey + 4, 8, math.pi * 1.1, math.pi * 1.9)
            _stroke(ctx, 3.6, INK, 0.95)
        else:
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(1, blink)
            ctx.arc(0, 0, 6.5, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*hexrgb(INK, 0.95))
            ctx.fill()
        ctx.move_to(ex - 11, ey - 20 + (3 if sg < 0 else 0) * (1 - happy))
        ctx.line_to(ex + 11, ey - 20 - (3 if sg < 0 else 0) * (1 - happy))
        _stroke(ctx, 3.2, INK, 0.75)
    if happy > 0.5:                                                   # 口（にっこり）
        ctx.arc(cx, hy + 28, 17, math.pi * 0.1, math.pi * 0.9)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#c24d4d"))
        ctx.fill_preserve()
        _stroke(ctx, 3.2, INK, 0.95)
    else:
        ctx.arc(cx, hy + 33, 10, math.pi * 0.15, math.pi * 0.85)
        _stroke(ctx, 3.4, INK, 0.9)
    if mode != "towel":
        hair_front(ctx, cx, hy, wet, t, blow)
    # 腕・道具
    sh_y = sy + 24
    if mode == "towel":
        dx = 17 * math.sin(2 * math.pi * 2.3 * t)
        rot = 0.07 * math.sin(2 * math.pi * 2.3 * t + 1.2)
        draw_towel_head(ctx, cx, hy, dx, rot)
        for sg in (-1, 1):
            hand = (cx + sg * 86 + dx, hy - 44 + sg * 4 * math.sin(2 * math.pi * 2.3 * t))
            elb = (cx + sg * 140, sh_y - 52)
            _limb(ctx, [(cx + sg * 100, sh_y), elb, hand], 25, PJ)
            ctx.arc(hand[0], hand[1], 15, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(SKIN))
            ctx.fill_preserve()
            _stroke(ctx, 3.2, INK, 0.9)
    else:
        u = ease(clamp01(done_u * 1.6))
        sweep = (1 - u) * 15 * math.sin(2 * math.pi * 0.85 * t + (0.0 if side == "tw" else 1.7))
        px = cx + ds * (DOFF - 6 * u)
        py = hy + 6 + sweep + u * 120
        rot = (1 - u) * 0.07 * math.sin(2 * math.pi * 0.85 * t + 0.5) + u * ds * 1.05
        sx = -ds                                                       # 左の人: ノズルは右(+x)、右の人: 左
        on = done_u <= 0
        hx, hy2 = xf(px, py, rot, sx, -12, 58)
        draw_dryer(ctx, px, py, rot, sx, t, on)
        elb = ((cx + ds * 100 + hx) / 2 + ds * 14, (sh_y + hy2) / 2 + 26)
        _limb(ctx, [(cx + ds * 100, sh_y), elb, (hx, hy2)], 25, PJ)
        ctx.arc(hx, hy2, 15, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 3.2, INK, 0.9)
        # もう片方の腕は下ろす
        _limb(ctx, [(cx - ds * 100, sh_y), (cx - ds * 124, sh_y + 52), (cx - ds * 112, sh_y + 104)], 25, PJ)
    # しずく
    al = clamp01((f - 0.30) / 0.3)
    if al > 0:
        for k in range(4):
            ph = (t * 1.0 + k * 0.27) % 1.0
            x = cx + (-1 if k % 2 else 1) * (side_w - 10 - 14 * (k // 2))
            y = yb - 4 + ph * 62
            ctx.arc(x, y, 6.5 - 2.8 * ph, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(WATER, 0.9 * al * (1 - ph ** 2)))
            ctx.fill()
    # かわいた！ きらきら
    if done_u > 0:
        for k, (ox, oy, r) in enumerate(((-96, -54, 15), (98, -40, 12), (-84, 40, 11), (104, 30, 16))):
            tw_ = 0.5 + 0.5 * math.sin(t * 6 + k * 1.7)
            star(ctx, cx + ox, hy + oy, r * (0.7 + 0.5 * tw_), "#ffd95a", clamp01(done_u * 2) * 0.95)


def draw_bg(ctx, k, t, y0=None, y1=None):
    pn = PN[k]
    y0 = PY0 if y0 is None else y0
    y1 = PY1 if y1 is None else y1
    base = "#dbe9f8" if k == "tw" else "#fbe7d3"
    line = "#a9c4e2" if k == "tw" else "#e4bf97"
    fill(ctx, hexrgb(base))
    ctx.rectangle(pn["x0"], y0, pn["x1"] - pn["x0"], y1 - y0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(line, 0.7))                          # タイル
    ctx.set_line_width(2.5)
    for x in range(int(pn["x0"]) - 60, int(pn["x1"]) + 60, 56):
        ctx.move_to(x, y0)
        ctx.line_to(x, y1)
    for y in range(int(y0) - 20, int(y1), 56):
        ctx.move_to(pn["x0"], y)
        ctx.line_to(pn["x1"], y)
    ctx.stroke()
    for i in range(9):                                               # ゆげのあわ（上へ昇る）
        ph = (t * (0.16 + 0.03 * (i % 3)) + i * 0.173) % 1.0
        x = pn["x0"] + 30 + ((i * 97) % 380) + 12 * math.sin(t * 2 + i)
        y = y1 - ph * (y1 - y0 + 60)
        r = 9 + (i % 4) * 6
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, "#ffffff", 0.9)


def draw_panel(ctx, k, t, f, mode, done_t):
    s = sample()
    pn = PN[k]
    ctx.save()
    clip_panel(ctx, k)
    zoom_art(ctx, t, pn["cx"])
    draw_bg(ctx, k, t)
    done_u = 0.0 if done_t is None else clamp01((t - done_t) / 0.6) + 1e-6
    ctx.save()
    ctx.translate(pn["cx"], HYT)
    ctx.scale(PK, PK)
    ctx.translate(-pn["cx"], -HY)
    draw_person(ctx, pn["cx"], t, s["p"]["li"], f, mode, k, done_u, towel_neck=(k == "tw" and mode == "dryer"))
    ctx.restore()
    ctx.restore()
    border_panel(ctx, k)


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
    """メーターの帯（人の上）。しずくは左、文字は右（右のパネルでも x≤930）"""
    pn = PN[k]
    cx = pn["cx"]
    core.rrect(ctx, pn["x0"] + 10, CARD_Y - 4, pn["x1"] - pn["x0"] - 20, 142, 18)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.96))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    done = done_t is not None
    draw_drop(ctx, cx - 112, CARD_Y + 8, 80, 118, f, t, done)
    tx = cx + 36
    if not done:
        text(ctx, "髪の水", tx, CARD_Y + 32, 28, PENCIL, bold=False)
        text(ctx, pcs(f), tx, CARD_Y + 90, 72, INKC[k])
    else:
        u = clamp01((t - done_t) / 0.35)
        text(ctx, "乾いた！", tx, CARD_Y + 32, 38, RED)
        lab = ms(t_fin)
        sz = 44
        while core.text_width(lab, sz) > 168:
            sz -= 1
        text(ctx, lab, tx, CARD_Y + 90, sz, INKC[k])
        note.pen_circle(ctx, tx, CARD_Y + 90, 98, 36, RED, seed=70 + (k == "dr"), width=4.5, progress=u)


def draw_header(ctx, t, k):
    s = sample()
    p = s["p"]
    pn = PN[k]
    cx = pn["cx"]
    xd, yd = cx - 108, 870
    core.rrect(ctx, pn["x0"] + 8, PY0 + 8, pn["x1"] - pn["x0"] - 16, 104, 16)   # 字の下地（冒頭に絵がせり上がっても読める）
    ctx.set_source_rgba(*hexrgb(PAPER, 0.92))
    ctx.fill()
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 24, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 24, 24, INKC[k], seed=13 + (k == "dr"), width=3.4)
    text(ctx, TAG[k], xd, yd, 32, INKC[k])
    text(ctx, NAME[k], cx - 70, yd, 38, INKC[k], align="left")
    if k == "tw":
        text(ctx, f"拭く時間 {int(round(p['tw']))}秒", cx, 916, 36, RED)
    else:
        text(ctx, "拭かずに すぐ", cx, 916, 36, INK)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    s = sample()
    tau = tau_of(t)
    ft, fd = fs(t)
    q = s["p"]
    ctx.push_group()
    done_t = t_of(s["t_tw"]) if tau >= s["t_tw"] else None
    done_d = t_of(s["t_dr"]) if tau >= s["t_dr"] else None
    draw_panel(ctx, "tw", t, ft, "towel" if tau < q["tw"] else "dryer", done_t)
    draw_panel(ctx, "dr", t, fd, "dryer", done_d)
    draw_card(ctx, t, "tw", ft, s["t_tw"], done_t)
    draw_card(ctx, t, "dr", fd, s["t_dr"], done_d)
    draw_header(ctx, t, "tw")
    draw_header(ctx, t, "dr")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, f"お風呂を出て {mmss(tau_of(t))}", 580, 702, 42, "yellow", a=a, tilt=-0.02)
    text(ctx, "早送り（髪の水が1割で「乾いた」）", 580, 778, 26, PENCIL, bold=False, alpha=a)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 7
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 714.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results()
    win_dr = (r["t_dr"] < r["t_tw"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_T), bgra(COL_D)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_dr[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results()
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    sg = 1 - 0.20 * ease((t - T_REV) / 0.4)                  # 答えの画面では、すこし縮めて下に答えの場所をあける
    ctx.save()
    ctx.translate(580, G_Y0)
    ctx.scale(sg, sg)
    ctx.translate(-580, -G_Y0)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    ctx.restore()
    text(ctx, f"{fmt(n)} / 10,000回　1マス＝1回", 580, 678, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    win_dr = r["t_dr"][:m] < r["t_tw"][:m]
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0:
        for i, (k, cnt) in enumerate((("tw", int(m - win_dr.sum())), ("dr", int(win_dr.sum())))):
            y = 1298 + i * 36
            fill(ctx, hexrgb(COLS[k], a * lg))
            ctx.rectangle(160, y - 16, 32, 32)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(160, y - 16, 32, 32)
            ctx.stroke()
            text(ctx, f"{TAG[k]} {NAME[k]}が先に乾いた", 210, y, 32, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 915, y, 32, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            sh = shown()
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            note.sticky(ctx, f"拭く時間を入れても、\n差は 真ん中で {about(abs(sh['gap_med']))}", 580, 1410, 28, "pink",
                        fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["p_tw"], sh["gap_med"])


def reason_text():
    sh = shown()
    k = answer_key()
    g = about(abs(sh["gap_med"]))
    if k == "tw":
        return f"先に水を取るぶん、ドライヤーが短くなるから。\n拭く時間を足しても、真ん中で{g}早い"
    if k == "dr":
        return f"拭く時間のほうが、ドライヤーが減る時間より長いから。\nすぐドライヤーが、真ん中で{g}早い"
    return "拭く時間と、減るドライヤーの時間が ほぼ同じ。\nどちらも 真ん中で数十秒の差もない"


def twist_line():
    sh = shown()
    return f"拭くのは{about(sh['t_peak'])}まで。それより長いと差は増えない"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1244, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3)
        note.sticky(ctx, reason_text(), 580, 1352, 30, "blue", a=c, tilt=0.012)
    if TWIST and t >= T_ANS2 + 1.8:
        d = ease_out((t - T_ANS2 - 1.8) / 0.3)
        text(ctx, twist_line(), 560, 1428, 32, INK, alpha=d)


TWIST = True


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
    """3行とも同じ大きさ（いちばん長い行が max_w になる）。小さい1行（お風呂上がり、）は6割"""
    s = min(100.0 * max_w / core.text_width(q, 100.0) for q in BIG_Q)
    return s, s * 0.6


CD_X, CD_Y = 580.0, 1330.0


class DIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい）・前提・三択（横1列）。その下に2人（0秒目からタオルとドライヤーが動き、髪の水が減り始める）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        s, sp = big_sizes(850.0)
        for line, y, sz, pk in ((BIG_PRE, 414, sp, 0.03), (BIG_Q[0], 497, s, 0.03), (BIG_Q[1], 581, s, 0.03), (BIG_Q[2], 665, s, 0.03)):
            pop = 1 + pk * (1 - ease_out(t / 0.4))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q[2], s)
        note.pen_line(ctx, 565 - w3 / 2 - 6, 716, 565 + w3 / 2 + 6, 711, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, 810, 28, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 762
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
        s, sp = big_sizes(850.0)
        sz = min(s, 48.0)
        text(ctx, BIG_PRE, 540, 390, min(sp, 28.0), INK, alpha=m)
        for i, y in enumerate((436, 488, 540)):
            text(ctx, BIG_Q[i], 540, y, sz, INK, alpha=m)
        w3 = core.text_width(BIG_Q[2], sz)
        note.pen_line(ctx, 540 - w3 / 2 - 6, 572, 540 + w3 / 2 + 6, 569, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 622
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 860)):
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


INTRO = DIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


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
        note.sticky(ctx, "あなたは、\n拭く派？すぐドライヤー派？", 580, 770, 62, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 580, 960, 46, INK, bold=False, alpha=r)
        draw_closing_people(ctx, t - T_Q, q)


CLOSE_Y0 = 1060.0


def draw_closing_people(ctx, t, a):
    """締めの画面の下半分: 拭く人とドライヤーの人（どちらが乾いているかは出さない。ぬれ具合は同じ）"""
    s = sample()
    ctx.push_group()
    for k, mode in (("tw", "towel"), ("dr", "dryer")):
        pn = PN[k]
        ctx.save()
        core.rrect(ctx, pn["x0"], CLOSE_Y0, pn["x1"] - pn["x0"], PY1 - CLOSE_Y0, 22)
        ctx.clip()
        draw_bg(ctx, k, t, CLOSE_Y0, PY1)
        ctx.save()
        ctx.translate(pn["cx"], HYT + 20)
        ctx.scale(PK, PK)
        ctx.translate(-pn["cx"], -HY)
        draw_person(ctx, pn["cx"], t + 0.3, s["p"]["li"], 0.55, mode, k, 0.0, towel_neck=False)
        ctx.restore()
        ctx.restore()
        core.rrect(ctx, pn["x0"], CLOSE_Y0, pn["x1"] - pn["x0"], PY1 - CLOSE_Y0, 22)
        _stroke(ctx, 3.5, INK, 0.75)
        core.rrect(ctx, pn["x0"] + 8, CLOSE_Y0 + 8, pn["x1"] - pn["x0"] - 16, 60, 16)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.92))
        ctx.fill()
        text(ctx, NAME[k] + "派", pn["cx"], CLOSE_Y0 + 40, 32, INKC[k])
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


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
    hum = noise_band(t_end, 9, 3, 1.0)                     # ドライヤー（ゴー）
    tt = np.arange(len(hum)) / SR
    env_ = (0.85 + 0.15 * np.sin(2 * np.pi * 0.9 * tt)) * np.minimum(1, tt / 0.15) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, (hum * 1.6 + 0.25 * np.sin(2 * np.pi * 118 * tt)) * env_, 0.34)
    t_rub = t_of(s["p"]["tw"])                              # タオルでこする音（ざっざっ）
    rub = noise_band(t_rub, 40, 8, 1.0)
    tr = np.arange(len(rub)) / SR
    mx.add(0.0, rub * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 2.3 * tr))) * 3.0, 0.5)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    tg, te = t_of(s["t_tw"]), t_of(s["t_dr"])
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
    # (1) 式の乾く時刻が、1/4秒きざみの足し算と合う（最大の食い違い・割合）
    checks.append(("乾く時刻: 足し算 − 式（最大・割合）", numeric_check(120), 0.0, 0.01))
    # (2) 標準の条件（60秒・Q=0.5・τ=40秒、f_c=0.325）で、長さごとの乾く時間がマイベストの値（秒）と合う
    fstd = float(f_wipe(*STD_WIPE))
    for L in LENS:
        c = w0_center(L) / rmax_center(L)
        checks.append((f"標準の乾く時間（{L}・秒）", float(c * g_fun(fstd, FC0)), T_STD[L], 0.5))
    # (3) 拭いたあとの水は、いつも f_c より多い（式 g の前提）
    checks.append(("拭いたあとの水が f_c より多い", float(np.min(r["fw"] - p["fc"]) > 0), 1.0, 0.0))
    # (4) 見本の履歴の終わり（水が1割）が、1万回の中のその回の時刻と一致する
    s = sample()
    checks.append(("見本のすぐの時刻で水が1割", f_dr_at(s["t_dr"]), DRY_AT, 1e-6))
    checks.append(("見本の拭いてからの時刻で水が1割", f_tw_at(s["t_tw"]), DRY_AT, 1e-6))
    checks.append(("見本の拭く時間が 30〜90秒", float(30.0 <= s["p"]["tw"] <= 90.0), 1.0, 0.0))
    # (5) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key = answer_by_rule(sh["p_tw"], sh["gap_med"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（拭いてから・すぐドライヤー）",
                   float(LABELS.index(NAME["tw"]) * 10 + LABELS.index(NAME["dr"])),
                   float("ABC".index(TAG["tw"]) * 10 + "ABC".index(TAG["dr"])), 0.0))
    # (6) 見本は1万回の中の1回で、差が真ん中の値の近く
    checks.append(("見本の差（秒）が真ん中の値の近く", s["gap"], sh["gap_med"], 0.10 * abs(sh["gap_med"])))
    # (7) 回数が足して1万
    checks.append(("先に乾いた回の合計", float(sh["n_tw"] + sh["n_dr"]), float(N_TRIAL), 0.0))
    # (8) ひねり: 拭く時間をピークの2倍にした差は、ピークの差より小さい
    i2 = int(np.argmin(np.abs(SWEEP - 2 * sh["t_peak"])))
    checks.append(("拭く時間を2倍にすると差はピークより小さい", float(sh["sw"][i2] < sh["g_peak"]), 1.0, 0.0))
    checks.append(("拭く時間10秒の差はピークより小さい", float(sh["sw"][0] < sh["g_peak"]), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX:.1f}秒/秒  乾く {T_FIN1:.2f} / {T_FIN2:.2f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  "
          f"締め {T_Q:.1f}  見本 {s['i']}（拭いてから {ms(s['t_tw'])} / すぐ {ms(s['t_dr'])}）  拭き終わり 動画{t_of(s['p']['tw']):.2f}秒")
    print("  理由:", reason_text().replace("\n", " / "), "|", twist_line())
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 4.4, 5.2, 5.8, 8.0, 10.0, T_FIN1 + 0.4, T_FIN2 - 0.6, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_ANS2 + 2.6, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
