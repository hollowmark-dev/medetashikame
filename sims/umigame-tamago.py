"""ウミガメの卵1万個。大人になって浜に戻るのは何匹？（めでたしかめ ショート）— 2026-11-09 作成（ナレーションなし・60秒未満）

台本は research/shorts_seal_turtle_scripts_2026-11-09.md の「B. ウミガメ」（ユーザーOK済み。札の文言・順番・数字は変えない。足したのは絵と絵の中の短いラベルだけ）。
計算の本体はこのファイルの「計算（1万個）」の節（置き方・seed 2612・答えの決め方は、1万個を回す前に固定した docstring を、その節にそのまま残してある。ここでは変えない）。
この sim は「1万個の結果を読んで絵にする」ところ。数字はすべてその節の計算から読み込む（手で打たない）。

【見本の1匹】 1万個の順で「最初に大人になった1匹」（結果を見る前に決めた。umigame.json の sample_adult.index = 2820）。2026-11-09 ユーザーの決まり「生き物の一生ものの見本は、すぐ死ぬ個体を避ける」。
  子ガメの目線（砂の中・波打ちぎわ・明るい海）→ 海で大きくなる → 22年後に浜へ戻る（横から）。
【一人称の場面】 子ガメの目の高さから見た景色。自分の体は画面の下の端に、甲羅の先と前ひれが少し見えるだけ。視点は第三者に変わらない。
  砂の中は暗い → 砂を押し上げると夜空と月 → 白く光る波打ちぎわへ走る → 海の中。死は「暗くなって見えなくなる」で表す。
【答えの前に答えの向きを見せない】 研究の札では結果を出さない。22年目の数（12匹）は、数え上げの終わりと答えの札で初めて見せる。
【ぶれ】 同じ1万個の浜を、モデルと同じ種（SEED+1）で1万回作り直した分布を、ここでも同じ呼び出しで再現して数える。
問い: 「ウミガメの卵、1万個。／大人になって浜に戻るのは／何匹？」
選択肢: A 約10匹 ／ B 約100匹 ／ C 約1,000匹（正解の記号は A。run_checks で確かめる）
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# =====================================================================
# 計算（1万個）— この1ファイルだけで、結果と out/models_1128/umigame.json を作り直せる（python sims/umigame-tamago.py --model）
# 計算の置き方・種・答えの決め方は、回す前に固定した（結果を見て変えていない）。元の docstring:
#
# ウミガメの卵1万個。大人になって浜に戻るのは何匹？（slug: umigame-tamago 予定）の計算。
#
# 元にした研究（数字はすべてここから。計算の前に決めた）:
# - Crouse, Crowder & Caswell (1987) Ecology 68(5):1412-1423、Crowder ほか (1994) Ecological Applications 4(3):437-445。
#   アカウミガメ（アメリカ南東部の個体群）の段階ごとの年間生存率と、段階の長さ:
#     卵〜1年目 0.6747（1年）／小さい子ども 0.75（7年）／大きい子ども 0.6758（8年）／若者 0.7425（6年）／大人 0.8091。
#   数字は Crowder ほか (1994) の5段階の表（mpmtools の再現データで確認）。著者は「一部は暫定の推定」と書いている。
# - 大人になる（初めて産卵に浜へ戻る）のは、1+7+8+6 = 22年を生き延びたとき。
#
# 1回 = 卵1個の一生。1万個（1万回）。乱数の種は 2612（計算の前に決めた）。
# - 毎年、その段階の生存率のくじで生き残るかを決める。
# 見本の1匹（2026-11-09 ユーザーの決まりで、結果を見る前に決めた選び方）: 1万個の順で、最初に大人になった1匹。
#   （ふだんの「見本は1万回の最初の1回」の例外。生き物の一生ものの見本は、すぐ死ぬ個体を避ける）
# 数えるもの: 大人になった数、各段階の終わりに残った数、死んだ年の中央値。
# ぶれ: 同じ1万個の浜を、乱数の種を変えて1万回作り直し、大人になる数の分布を見る。
#
# 答え（問い「大人になって浜に戻るのは？」A 約10匹 / B 約100匹 / C 約1,000匹）の決め方（計算の前に固定）:
# 大人になった数を、選択肢の 10・100・1,000 と比で比べ（対数で）、いちばん近いものを正解にする。
# 大人になってからの寿命は数えない（大人の生存率が年齢で変わらない置き方なので、最長の年齢は置き方で決まってしまうため）。
# =====================================================================
R, SEED = 10000, 2612
LIFE_STAGES = [("卵〜1年目", 0.6747, 1), ("小さい子ども", 0.75, 7), ("大きい子ども", 0.6758, 8), ("若者", 0.7425, 6)]
ADULT = 0.8091
OPTIONS = [("約10匹", 10), ("約100匹", 100), ("約1,000匹", 1000)]


def run(seed=SEED, n=R):
    rng = np.random.default_rng(seed)
    alive = np.ones(n, bool)
    death = np.full(n, -1)
    year = 0
    left = []
    for name, s, d in LIFE_STAGES:
        for _ in range(d):
            year += 1
            die = alive & (rng.random(n) >= s)
            death[die] = year
            alive &= ~die
        left.append((name, year, int(alive.sum())))
    return alive, death, left


def theory():
    p = 1.0
    for _, s, d in LIFE_STAGES:
        p *= s ** d
    return p


def build_model_json():
    """旧 main と同じ中身（1万個の結果・ぶれ・見本の番号）"""
    alive, death, left = run()
    adults = int(alive.sum())
    ans = min(OPTIONS, key=lambda o: abs(np.log(max(adults, 0.5)) - np.log(o[1])))[0]
    rng = np.random.default_rng(SEED + 1)
    reps = rng.binomial(R, theory(), size=10000)
    return dict(seed=SEED, adults=adults, theory_per_10000=round(theory() * R, 2), answer=ans,
                left_after_stage=left, median_death_year=float(np.median(np.where(alive, 99, death))),
                died_year1=int((death == 1).sum()), died_by_year2=int(((death >= 1) & (death <= 2)).sum()),
                years_to_adult=sum(d for _, _, d in LIFE_STAGES),
                reps=dict(zero=int((reps == 0).sum()), min=int(reps.min()), max=int(reps.max()),
                          median=float(np.median(reps)), ge10=int((reps >= 10).sum())),
                sample=dict(death_year=int(death[0]), adult=bool(alive[0])),
                sample_adult=dict(index=int(np.nonzero(alive)[0][0])),
                adult_annual_survival=ADULT)


def load_model_json():
    """out/models_1128/umigame.json を読む。なければ上の計算を回して作る（公開側には out/ がない）"""
    if MODEL_JSON.exists():
        return json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    txt = json.dumps(build_model_json(), ensure_ascii=False, indent=1)
    try:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(txt, encoding="utf-8")
    except OSError:
        pass
    return json.loads(txt)


SLUG = "umigame-tamago"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
MODEL_JSON = Path(__file__).resolve().parents[1] / "out" / "models_1128" / "umigame.json"

N = R
CNT = 1.4                                            # 16年目→22年目の数え上げの秒数
_RES = {}


def results():
    """1万個の結果（run そのまま）＋ 1万回作り直した浜ごとの数（モデルと同じ種・同じ呼び出し）"""
    if _RES.get("r"):
        return _RES["r"]
    alive, death, left = run()
    dd = np.where(alive, 99, death)                  # 生き残りは 99
    ad = int(alive.sum())
    key = min(OPTIONS, key=lambda o: abs(math.log(max(ad, 0.5)) - math.log(o[1])))[0]
    reps = np.random.default_rng(SEED + 1).binomial(N, theory(), size=10000)
    _RES["r"] = dict(alive=alive, dd=dd, left=left, adults=ad, key=key, reps=reps,
                     rh=np.bincount(reps, minlength=18), median=float(np.median(reps)),
                     surv=[int((dd > a_).sum()) for a_ in range(23)])
    return _RES["r"]


def sample():
    """見本の1匹 = 1万個の順で、最初に大人になった1匹（結果を見る前に決めた。umigame.json の sample_adult）"""
    r = results()
    i = int(np.nonzero(r["alive"])[0][0])
    return dict(idx=i, death=int(r["dd"][i]), adult=bool(r["alive"][i]))


if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    if "--model" in sys.argv:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(json.dumps(build_model_json(), ensure_ascii=False, indent=1), encoding="utf-8")
        print("書いた:", MODEL_JSON)
    r = results()
    S = sample()
    print(f"{N}個  大人 {r['adults']}匹  答え: {r['key']}  段階の終わり: {r['left']}")
    print(f"見本: {S['idx']}個目（0始まり）  大人={S['adult']}  ぶれ {int(r['reps'].min())}〜{int(r['reps'].max())}匹  中央値 {r['median']}  0匹 {int((r['reps'] == 0).sum())}回")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect,
                         text, thump, whoosh)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.27"

FC, FC_D = "#e0801f", "#a85a0a"
BLUE, BLUE_D = "#5f86b0", "#34567f"
PANEL_BG = "#fbf8ef"
NAVY_BG = "#1b2742"
WHITE = "#f6f1e3"
EGG = "#f3ecd8"
ORANGE = "#ffb347"

LABELS = [o[0] for o in OPTIONS]                  # 約10匹 / 約100匹 / 約1,000匹
CORRECT = 0
BIG_Q = ["ウミガメの卵、1万個。", "大人になって浜に戻るのは", "何匹？"]

CY_INTRO, CY_FINAL = 830.0, 655.0
PW, PH = 960.0, 690.0                                # 絵の枠（横幅いっぱい近く）
PX = 60.0
T_CHO = (0.7, 0.9, 1.1)
T_CD = (1.2, 1.8, 2.4)
T_MOVE, T_GO = 2.8, 3.2

_L = results()["left"]                               # [(段階, 年, 残り)]
_LS = {y_: n_ for _, y_, n_ in _L}                   # {1: 6790, 8: 866, 16: 39, 22: 12}
_RP = results()["reps"]

CARD_TEXT = {
    "c1": "年ごとに何割が生き残るか、\n調べた研究がある。",
    "c2a": "1万個の一生を、\n1年ずつ進める。",
    "c2b": "大人になるまで、\n22年。",
    "s0": "たとえば、この1匹では",
    "s1": "この1匹は、海で大きくなった。",
    "s2": "22年たって、浜に戻ってきた。",
    "v1": f"1年目が終わると、{_LS[1]:,}匹。",
    "v2": f"8年目、{_LS[8]:,}匹。",
    "v3": f"16年目、{_LS[16]:,}匹。",
    "ans": f"答えは『{results()['key']}』。",
    "a1": f"22年目に浜に戻ったのは、\n{_LS[22]}匹。",
    "bl": f"1万個の浜を、1万回作り直すと、\n戻るのは{int(_RP.min())}匹〜{int(_RP.max())}匹。中央値は{int(np.median(_RP))}匹。",
    "q": "あなたは、\n何匹だと思いましたか？",
}


def need(s_):
    n_ = len(s_.replace("\n", ""))
    return max(0.12 * n_ + 1.0, 0.5 + max(len(x) for x in s_.split("\n")) / 6.0)


def hold(key):
    return need(CARD_TEXT[key]) + 0.04


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ss(a, b, t):
    return smooth((t - a) / (b - a))


def lerp(a, b, u):
    return a + (b - a) * u


def win(t, a, b, fi=0.3, fo=0.3):
    return clamp01((t - a) / fi) * (1 - clamp01((t - (b - fo)) / fo))


POV_SHOTS = (3.0, 3.0, 3.0, 3.2, 3.4)      # 砂の中・波打ちぎわ・明るい海・海で大きくなる・浜に戻る


def setup():
    global T_R1, T_R2, T_S0, T_P2, T_P3, T_P4, T_P5, T_E0, T_HC, T_REV, T_BL, T_Q, DURATION
    global SCENES, CARDS, E_KEYS, E_MARK
    T_R1 = T_GO
    T_R2 = T_R1 + 0.2 + hold("c1") + 0.1
    T_S0 = T_R2 + 0.2 + hold("c2a") + 0.05 + hold("c2b") + 0.1
    T_P2 = T_S0 + POV_SHOTS[0]
    T_P3 = T_P2 + POV_SHOTS[1]
    T_P4 = T_P3 + POV_SHOTS[2]
    T_P5 = T_P4 + POV_SHOTS[3]
    T_E0 = T_P5 + POV_SHOTS[4]
    # 1万個が年ごとに減る: 年のカウンターのキー (動画の秒, 年)
    t1 = T_E0 + 1.3
    v1a = t1 + 0.1
    v1b = v1a + hold("v1")
    t8 = v1b + 0.9
    v2a = t8 + 0.1
    v2b = v2a + hold("v2")
    t16 = v2b + 0.9
    v3a = t16 + 0.1
    v3b = v3a + hold("v3")
    T_HC = v3b + 0.1
    E_KEYS = [(T_E0, 0.0), (T_E0 + 0.5, 0.0), (t1, 1.0), (v1b, 1.0), (t8, 8.0), (v2b, 8.0), (t16, 16.0), (v3b, 16.0), (T_HC + CNT, 22.0)]
    E_MARK = (t1, t8, t16)
    T_REV = T_HC + CNT + 0.6
    ans_a = T_REV + 0.2
    ans_b = ans_a + hold("ans")
    a1_a = ans_b + 0.07
    a1_b = a1_a + hold("a1")
    T_BL = a1_b + 0.1
    bl_a = T_BL + 0.2
    bl_b = bl_a + hold("bl")
    T_Q = bl_b + 0.1
    DURATION = T_Q + 0.2 + hold("q") + 0.05
    SCENES = [("冒頭（問い・夜の砂浜と卵の山）", 0.0, T_GO), ("研究の札", T_R1, T_R2), ("比べ方の札", T_R2, T_S0),
              ("見本の1匹（砂の中・波打ちぎわ・海・大きくなる・浜に戻る）", T_S0, T_E0), ("1万個の点が年ごとに減る", T_E0, T_REV),
              ("答え・22年目の12匹", T_REV, T_BL), ("ぶれ（1万回作り直した浜ごとの数）", T_BL, T_Q), ("締め", T_Q, DURATION)]
    CARDS = {
        "c1": (CARD_TEXT["c1"], T_R1 + 0.2, T_R1 + 0.2 + hold("c1")),
        "c2a": (CARD_TEXT["c2a"], T_R2 + 0.2, T_R2 + 0.2 + hold("c2a")),
        "c2b": (CARD_TEXT["c2b"], T_R2 + 0.25 + hold("c2a"), T_R2 + 0.25 + hold("c2a") + hold("c2b")),
        "s0": (CARD_TEXT["s0"], T_S0 + 0.2, T_S0 + 0.2 + hold("s0")),
        "s1": (CARD_TEXT["s1"], T_P4 + 0.2, T_P4 + 0.2 + hold("s1")),
        "s2": (CARD_TEXT["s2"], T_P5 + 0.2, T_P5 + 0.2 + hold("s2")),
        "v1": (CARD_TEXT["v1"], v1a, v1b),
        "v2": (CARD_TEXT["v2"], v2a, v2b),
        "v3": (CARD_TEXT["v3"], v3a, v3b),
        "ans": (CARD_TEXT["ans"], ans_a, ans_b),
        "a1": (CARD_TEXT["a1"], a1_a, a1_b),
        "bl": (CARD_TEXT["bl"], bl_a, bl_b),
        "q": (CARD_TEXT["q"], T_Q + 0.2, T_Q + 0.2 + hold("q")),
    }


setup()


def cards():
    return list(CARDS.values())


def year_at(t):
    """年のカウンター（動画の秒 → 小数の年）。キーの間はなめらかに"""
    ks = E_KEYS
    if t <= ks[0][0]:
        return 0.0
    for (ta, aa), (tb, ab) in zip(ks[:-1], ks[1:]):
        if t <= tb:
            return lerp(aa, ab, smooth((t - ta) / max(tb - ta, 1e-9)))
    return ks[-1][1]


# ---------- 絵: 共通 ----------
def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def ell(ctx, cx, cy, rx, ry, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def grad(ctx, y0, y1, c0, c1, x0=0.0, x1=PW):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *hexrgb(c0))
    g.add_color_stop_rgba(1, *hexrgb(c1))
    ctx.set_source(g)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.fill()


def specks(ctx, seed, n, x0, y0, x1, y1, col, a, r0=1.5, r1=4.0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ctx.new_path()
        ctx.arc(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(r0, r1), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(col, a * rng.uniform(0.5, 1.0)))
        ctx.fill()


def stars(ctx, seed, n, y1, t=0.0, a=1.0):
    rng = np.random.default_rng(seed)
    for k in range(n):
        x_, y_ = rng.uniform(10, PW - 10), rng.uniform(8, y1)
        tw = 0.6 + 0.4 * math.sin(t * 2.0 + k)
        ctx.new_path()
        ctx.arc(x_, y_, rng.uniform(1.6, 3.2), 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 0.92, 0.85 * tw * a)
        ctx.fill()


def moon(ctx, x, y, r, a=1.0):
    g = cairo.RadialGradient(x, y, r * 0.8, x, y, r * 3.2)
    g.add_color_stop_rgba(0, 1, 0.96, 0.78, 0.38 * a)
    g.add_color_stop_rgba(1, 1, 0.96, 0.78, 0.0)
    ctx.set_source(g)
    ctx.rectangle(x - r * 3.3, y - r * 3.3, r * 6.6, r * 6.6)
    ctx.fill()
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#f8f1d2", a))
    ctx.fill_preserve()
    _stroke(ctx, 3, "#c9bf94", 0.7 * a)
    for dx, dy, rr in ((-0.3, -0.25, 0.2), (0.28, 0.1, 0.15), (-0.05, 0.38, 0.12)):
        ctx.new_path()
        ctx.arc(x + dx * r, y + dy * r, rr * r, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#e2d8b0", 0.85 * a))
        ctx.fill()


def egg(ctx, x, y, r, a=1.0):
    g = cairo.RadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r * 1.05)
    g.add_color_stop_rgba(0, 1, 1, 0.97, a)
    g.add_color_stop_rgba(1, 0.86, 0.82, 0.7, a)
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill_preserve()
    _stroke(ctx, 2.6, "#6d6048", 0.85 * a)


def loggerhead(ctx, x, gy, s, facing=1, t=0.0, a=1.0):
    """アカウミガメ（横向き）。(x, gy) は腹の下の中央、甲羅の幅は約300·s px。やわらかい手描き風"""
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(facing * s, s)
    lw = 3.4
    fl = 0.12 * math.sin(t * 1.4)
    ctx.save()                                            # うしろひれ
    ctx.translate(-140, -14)
    ctx.rotate(-0.3 + fl)
    ell(ctx, 0, 0, 52, 17)
    ctx.set_source_rgba(*hexrgb("#b88a55"))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    ctx.restore()
    ctx.new_path()                                        # 首と頭
    ell(ctx, 168, -58, 64, 46, -0.1)
    ctx.set_source_rgba(*hexrgb("#c9a06a"))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    ctx.new_path()
    ctx.arc(188, -70, 9, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#1c1a20"))
    ctx.fill()
    ctx.new_path()
    ctx.arc(191, -73, 3, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(205, -42)
    ctx.curve_to(190, -34, 170, -36, 156, -44)
    _stroke(ctx, 2.8, INK, 0.75)
    ctx.new_path()                                        # おなかの板
    ell(ctx, 0, -20, 150, 24)
    ctx.set_source_rgba(*hexrgb("#e8cf93"))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    ctx.new_path()                                        # 甲羅
    ctx.move_to(-160, -26)
    ctx.curve_to(-165, -130, -80, -190, 10, -190)
    ctx.curve_to(100, -190, 165, -130, 160, -26)
    ctx.curve_to(80, -12, -80, -12, -160, -26)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#a8643a"))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    for (x0, y0, x1, y1) in ((-95, -165, -70, -30), (-5, -190, -5, -26), (85, -168, 62, -30)):   # 甲板の線
        ctx.new_path()
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        _stroke(ctx, 2.6, INK, 0.45)
    for yy in (-120, -75):
        ctx.new_path()
        ctx.move_to(-135 if yy == -75 else -112, yy)
        ctx.curve_to(-40, yy - 14, 40, yy - 14, 135 if yy == -75 else 112, yy)
        _stroke(ctx, 2.6, INK, 0.4)
    ctx.save()                                            # 前ひれ
    ctx.translate(104, -6)
    ctx.rotate(0.6 + fl)
    ell(ctx, 0, 0, 78, 20)
    ctx.set_source_rgba(*hexrgb("#c49a5f"))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    ctx.restore()
    ctx.restore()


# ---------- 絵: 夜の浜 ----------
def night_beach(ctx, t, closing=False, nest=True):
    grad(ctx, 0, 250, "#0f1b34", "#2c4468")
    stars(ctx, 3, 34, 220, t)
    moon(ctx, 770, 110, 58)
    grad(ctx, 250, 350, "#1b3556", "#2a4a70")
    for k in range(7):                                    # 月の光の波
        yy = 262 + k * 13
        w_ = 150 - k * 12
        xo = 8 * math.sin(t * 1.4 + k)
        ctx.move_to(770 - w_ / 2 + xo, yy)
        ctx.line_to(770 + w_ / 2 + xo, yy)
        _stroke(ctx, 4, "#fff6d0", 0.6)
    ctx.new_path()
    for i in range(0, 41):
        x_ = i * 24.0
        y_ = 350 + 4 * math.sin(i * 0.9 + t * 1.2)
        (ctx.move_to if i == 0 else ctx.line_to)(x_, y_)
    _stroke(ctx, 9, "#ffffff", 0.7)
    grad(ctx, 350, PH, "#6a6354", "#524b3f")
    specks(ctx, 11, 60, 0, 360, PW, PH, "#8c8370", 0.4, 1.5, 3.5)
    if not nest:
        return
    # 卵の山（砂を切った断面）
    rrect(ctx, 130, 395, 700, 255, 26)
    ctx.set_source_rgba(*hexrgb("#33291f"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)
    specks(ctx, 12, 70, 140, 405, 820, 640, "#5a4a37", 0.6, 1.5, 3.5)
    rows = [10, 9, 8, 7, 5, 3]
    for ri, n_ in enumerate(rows):
        yy = 622 - ri * 41
        for k in range(n_):
            xx = 480 + (k - (n_ - 1) / 2) * 56
            egg(ctx, xx, yy + 2 * math.sin(t * 1.3 + k + ri), 28)
    text(ctx, "卵（ピンポン玉くらい）", 480, 372, 28, WHITE, bold=False, alpha=0.95)
    if closing:
        u = t - T_Q
        text(ctx, "？", 330, 140 + 6 * math.sin(t * 4), 150, "#ffd166", alpha=ease_out(clamp01((u - 0.2) / 0.3)))


# ---------- 各場面 ----------
def panel_local(ctx, cy):
    ctx.translate(PX, cy - 35)


def content_a(ctx, cy, t, a, closing=False):
    """冒頭・締め: 夜の砂浜と卵の山"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    night_beach(ctx, t, closing)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_closing(ctx, cy, t, a):
    content_a(ctx, cy, t, a, closing=True)


def chip(ctx, x, y, w, h, label, size=30, bg="#ffffff", fg=INK, a=1.0, edge=PENCIL):
    rrect(ctx, x - w / 2, y - h / 2, w, h, 14)
    ctx.set_source_rgba(*hexrgb(bg, a))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, edge, 0.85 * a)
    text(ctx, label, x, y + 2, size, fg, alpha=a)


def content_b(ctx, cy, t, a):
    """研究の札: 一生の段階（結果は出さない）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_R1
    ctx.save()
    ctx.translate(0, 8 * math.sin(t * 1.6))
    loggerhead(ctx, 330, 260, 1.15, 1, t)
    ctx.restore()
    text(ctx, "アカウミガメ", 760, 130, 40, INK)
    text(ctx, "一生の段階", 480, 330, 36, INK)
    st = ["卵〜1年目", "小さい子ども", "大きい子ども", "若者", "大人"]
    pos = [(200, 410, 250), (480, 410, 270), (760, 410, 270), (330, 500, 200), (610, 500, 200)]
    for k, ((x_, y_, w_), lab) in enumerate(zip(pos, st)):
        sh = ease_out(clamp01((u - 0.3 - 0.18 * k) / 0.35))
        chip(ctx, x_, y_, w_, 64, lab, 32, a=sh)
    text(ctx, "出典: Crouse ほか（1987）・Crowder ほか（1994）", 480, 640, 28, PENCIL, bold=False, alpha=clamp01((u - 1.2) / 0.4))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def dots_layout():
    if "dots" in _RES:
        return _RES["dots"]
    rng = np.random.default_rng(5)
    perm = rng.permutation(N)
    mid = 40 * 125 + 62                                      # 見本の1匹は帯の真ん中に置く
    j = int(np.where(perm == mid)[0][0])
    si = sample()["idx"]
    perm[si], perm[j] = perm[j], perm[si]
    cx = (perm % 125) * 6.7 + 36.0
    cy_ = (perm // 125) * 5.2 + 192.0
    _RES["dots"] = (cx, cy_)
    return _RES["dots"]


def draw_dots(ctx, yr, appear=1.0):
    """1万個の点。yr = 小数の年（その年に死ぬ点は、次の年へ進むあいだにうすくなって消える）。返り値 = 生きている数（なめらか）"""
    r = results()
    cx, cy_ = dots_layout()
    dd = r["dd"]
    ai = int(math.floor(yr + 1e-9))
    fr = yr - ai
    lim = int(appear * N)
    idx = np.arange(N)
    if fr < 1e-6:
        full = (dd > ai) & (idx < lim)
        dying = np.zeros(N, bool)
        n_alive = int(full.sum())
        al = 0.0
    else:
        full = (dd > ai + 1) & (idx < lim)
        dying = (dd == ai + 1) & (idx < lim)
        al = 1 - ss(0.1, 0.9, fr)
        n_alive = int(round(int(full.sum()) + int(dying.sum()) * al))
    nf = max(int(full.sum()) + int(dying.sum() * al), 1)
    big = nf < 1200
    rr = 4 + (1200 - nf) / 1200 * 7.0 if big else 0.0
    col = ORANGE if big else EGG
    for sel, aa in ((full, 0.95), (dying, 0.95 * al)):
        if aa <= 0.02:
            continue
        ctx.new_path()
        for i in np.nonzero(sel)[0]:
            if big:
                ctx.new_sub_path()
                ctx.arc(cx[i] + 2.4, cy_[i] + 1.8, rr, 0, 2 * math.pi)
            else:
                ctx.rectangle(cx[i], cy_[i], 4.8, 3.6)
        ctx.set_source_rgba(*hexrgb(col, aa))
        ctx.fill()
    return n_alive


def content_c(ctx, cy, t, a):
    """比べ方: 1万個を1年ずつ → 大人になるまで22年（段階の長さの帯）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    u = t - T_R2
    tb = CARDS["c2b"][1] - T_R2
    n_ = clamp01(u / 0.9)
    pa = 1 - ss(tb - 0.1, tb + 0.4, u)
    if pa > 0:
        draw_dots(ctx, 0.0, appear=n_)
        text(ctx, "卵 1万個", 480, 100, 80, WHITE, alpha=pa * ss(0, 0.3, u))
        text(ctx, "0年 → 1年 → 2年 → …", 480, 660, 40, WHITE, alpha=pa)
    ga = ss(tb, tb + 0.5, u)
    if ga > 0:
        text(ctx, "大人になるまでの年", 480, 90, 46, WHITE, alpha=ga)
        X0, X1 = 50.0, 830.0
        xs = lambda yv: X0 + (X1 - X0) * yv / 22.0       # noqa: E731
        seg = [("1年目", 0, 1, "#7fc4d9"), ("小さい子ども", 1, 8, "#5f86b0"), ("大きい子ども", 8, 16, "#7a6fb0"), ("若者", 16, 22, "#d89a4a")]
        for k, (nm, a0, a1, cc) in enumerate(seg):
            g = ease_out(clamp01((u - tb - 0.2 - 0.18 * k) / 0.5))
            if g <= 0:
                continue
            x0, x1 = xs(a0), xs(a0 + (a1 - a0) * g)
            rrect(ctx, x0, 300, max(x1 - x0, 2), 100, 10)
            ctx.set_source_rgba(*hexrgb(cc, 0.95 * ga))
            ctx.fill_preserve()
            _stroke(ctx, 3, WHITE, 0.8 * ga)
            if k >= 1:
                text(ctx, nm, 0.5 * (xs(a0) + xs(a1)), 262, 30, WHITE, alpha=g * ga)
                text(ctx, f"{a1 - a0}年", 0.5 * (xs(a0) + xs(a1)), 350, 44, WHITE, alpha=g * ga)
        text(ctx, "1年目", xs(0.5) + 12, 440, 28, WHITE, alpha=ga)
        text(ctx, "0年", xs(0), 478, 32, WHITE, alpha=ga)
        text(ctx, "22年", xs(22) - 10, 478, 32, WHITE, alpha=ga)
        d_ = ease_out(clamp01((u - tb - 0.9) / 0.4))
        text(ctx, "22年で 大人", 640, 580, 44, ORANGE, alpha=d_ * ga)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 一人称の場面（子ガメの目線） ----
def pov_self(ctx, t, mode, low=0.0):
    """子ガメの体: 画面の下の端に、左右の前ひれだけが少し見える（FPS の手のように。甲羅は見せない）"""
    ph = {"dig": 3.2, "run": 8.0, "swim": 3.6}[mode]
    amp = {"dig": 0.3, "run": 0.34, "swim": 0.4}[mode]
    bob = 5 * math.sin(t * ph * 0.6)
    for sg in (-1, 1):
        sph = (math.pi if (mode == "run" and sg > 0) else 0)
        ang = amp * math.sin(t * ph + sph)
        ctx.save()
        ctx.translate(480 + sg * 330, 700 + low - abs(ang) * 25 + bob * 0.4)
        ctx.rotate(sg * (-0.55 + ang))
        ell(ctx, 0, 0, 170, 52)
        ctx.set_source_rgba(*hexrgb("#c49a5f"))
        ctx.fill_preserve()
        _stroke(ctx, 6, INK, 1.0)
        ell(ctx, -sg * 8, -18, 124, 9)
        ctx.set_source_rgba(*hexrgb("#e3c08a", 0.7))
        ctx.fill()
        ctx.restore()


def pov_vignette(ctx, k=0.4):
    g = cairo.RadialGradient(PW / 2, PH / 2, 260, PW / 2, PH / 2, 640)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0.03, 0.03, 0.08, k)
    ctx.set_source(g)
    ctx.rectangle(0, 0, PW, PH)
    ctx.fill()


def shard(ctx, x, y, r, rot):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.new_path()
    ctx.arc(0, 0, r, math.pi * 0.95, math.pi * 2.05)
    ctx.curve_to(r * 0.6, -r * 0.15, -r * 0.2, r * 0.05, -r, 0)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#efe6cd"))
    ctx.fill_preserve()
    _stroke(ctx, 3, "#5b4c36", 0.8)
    ctx.restore()


def pov_shot1(ctx, t, u):
    """卵の山の中。卵がぎっしり、手前の卵にヒビ。砂の色で暗い"""
    grad(ctx, 0, PH, "#4a3828", "#5c4630")
    specks(ctx, 21, 420, 0, 0, PW, PH, "#8a7048", 0.6, 1.5, 4.5)
    R = 80.0
    for row in range(-1, 8):
        for col in range(-1, 9):
            x_ = col * 2 * R * 0.97 + (R if row % 2 else 0) + 20
            y_ = row * R * 1.72 + 40
            if abs(x_ - 480) < 140 and abs(y_ - 330) < 130:
                continue
            egg(ctx, x_, y_ + 3 * math.sin(t * 1.3 + row + col), R * 1.02, 1.0)
    egg(ctx, 480, 330, 120, 1.0)                              # 手前の大きな卵
    ctx.rectangle(0, 0, PW, PH)                               # 砂の中の暗さ
    ctx.set_source_rgba(0.12, 0.08, 0.04, 0.2)
    ctx.fill()
    g = cairo.RadialGradient(PW / 2, -40, 20, PW / 2, -40, 420)
    g.add_color_stop_rgba(0, 0.75, 0.75, 0.8, 0.18 * ss(0.3, 1.0, u))
    g.add_color_stop_rgba(1, 0.75, 0.75, 0.8, 0.0)
    ctx.set_source(g)
    ctx.rectangle(0, 0, PW, PH)
    ctx.fill()
    for k in range(34):                                       # 落ちてくる砂つぶ
        x_ = (k * 131) % 960
        y_ = (t * 55 + k * 47) % 760 - 30
        ctx.new_path()
        ctx.arc(x_, y_, 2.5 + (k % 3), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#c9b184", 0.6))
        ctx.fill()
    pov_self(ctx, t, "dig")


def rough_ellipse(ctx, cx, cy, rx, ry, seed=3, amp=0.07):
    ctx.new_path()
    for i in range(0, 73):
        a_ = i / 72 * 2 * math.pi
        k = 1 + amp * math.sin(a_ * 5 + seed) + amp * 0.6 * math.sin(a_ * 11 + seed * 2) + 0.022 * ((i % 2) * 2 - 1) + 0.02 * math.sin(i * 2.3)
        x_, y_ = cx + rx * k * math.cos(a_), cy + ry * k * math.sin(a_)
        (ctx.move_to if i == 0 else ctx.line_to)(x_, y_)
    ctx.close_path()


def pov_shot2(ctx, t, u):
    """砂を押し上げると、夜空と月"""
    g = ss(0.0, 0.55, u)
    rx, ry = lerp(170, 400, g), lerp(125, 300, g)
    grad(ctx, 0, PH, "#3a2d20", "#241b13")                    # 砂（まず全面）
    specks(ctx, 31, 150, 0, 0, PW, PH, "#6a563c", 0.5, 1.5, 4.0)
    ctx.save()                                                # 穴の中は夜空
    rough_ellipse(ctx, 480, 270, rx, ry)
    ctx.clip()
    grad(ctx, 0, PH, "#0e1932", "#2b4268")
    stars(ctx, 8, 60, 500, t)
    moon(ctx, 585, 205, 105)
    ctx.restore()
    rough_ellipse(ctx, 480, 270, rx, ry)
    _stroke(ctx, 8, "#9b8460", 0.95)
    for k in range(40):                                       # ふちから落ちる砂つぶ
        x_ = 480 + (rx * 0.92) * math.cos(k * 0.9 + 1.0)
        y_ = 270 + ry * 0.85 * math.sin(k * 0.9 + 1.0) + ((t * 70 + k * 31) % 200)
        ctx.new_path()
        ctx.arc(x_, y_, 3 + (k % 3), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#c2a97c", 0.7))
        ctx.fill()
    pov_self(ctx, t, "dig", low=22)


def pov_shot3(ctx, t, u):
    """白く光る波打ちぎわへ走る（子ガメの低い目線。砂は下の細い帯だけ）"""
    hz = 330
    grad(ctx, 0, hz, "#0f1b34", "#2d4a72")
    stars(ctx, 5, 50, 300, t)
    moon(ctx, 330, 215, 100)
    grad(ctx, hz, 585, "#1a3556", "#27496e")
    rng = np.random.default_rng(17)                           # 月の光の反射（幅と間隔をばらす）
    yy = hz + 14
    while yy < 565:
        w_ = float(rng.uniform(60, 200)) * (1 - (yy - hz) / 420)
        xo = float(rng.uniform(-30, 30)) + 8 * math.sin(t * 1.4 + yy)
        ctx.move_to(330 - w_ / 2 + xo, yy)
        ctx.line_to(330 + w_ / 2 + xo, yy)
        _stroke(ctx, float(rng.uniform(3, 7)), "#fff6d0", 0.5)
        yy += float(rng.uniform(9, 30))
    wl = lerp(585.0, 600.0, ss(0, 1, u))                      # 波打ちぎわ
    g = cairo.LinearGradient(0, wl, 0, PH)
    g.add_color_stop_rgba(0, *hexrgb("#8f7f60"))
    g.add_color_stop_rgba(1, *hexrgb("#6e6048"))
    ctx.set_source(g)
    ctx.rectangle(0, wl, PW, PH - wl)
    ctx.fill()
    for k in range(18):                                       # 流れてくる砂のつぶ（走っている動き）
        f = ((k * 0.0731) + t * 0.45) % 1.0
        y_ = wl + 6 + (PH - wl) * f
        x_ = (k * 197) % 960
        ctx.new_path()
        ctx.arc(480 + (x_ - 480) * (0.5 + f), y_, 1.5 + 3 * f, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#b8a67f", 0.55))
        ctx.fill()
    for wd, al in ((34, 0.28), (14, 0.95)):                   # 白く光る波打ちぎわ
        ctx.new_path()
        for i in range(0, 41):
            x_ = i * 24.0
            y_ = wl + 5 * math.sin(i * 0.8 + t * 2.0)
            (ctx.move_to if i == 0 else ctx.line_to)(x_, y_)
        _stroke(ctx, wd, "#fffbe6" if wd > 20 else "#ffffff", al)
    pov_self(ctx, t, "run", low=20)


def pov_shot4(ctx, t, u):
    """明るい海の中を泳いでいく"""
    gb = 1 - ss(0.0, 0.3, u)                                  # 波をかぶる白
    grad(ctx, 0, PH, "#1f4f7c", "#081c38")
    for j in range(6):                                        # 水面からの光
        x0 = 60 + j * 170 + 25 * math.sin(t * 0.8 + j)
        ctx.move_to(x0, 0)
        ctx.line_to(x0 + 70, 0)
        ctx.line_to(x0 + 220, PH)
        ctx.line_to(x0 + 60, PH)
        ctx.close_path()
        ctx.set_source_rgba(0.85, 0.92, 1, 0.07)
        ctx.fill()
    ell(ctx, 480 + 30 * math.sin(t * 1.5), 12, 430, 11)         # 水面ごしの月
    ctx.set_source_rgba(0.95, 0.95, 0.85, 0.25)
    ctx.fill()
    for j in range(11):   # あわ（だんだん減る）
        ph = (t * 0.33 + j * 0.173) % 1.0
        bx = 120 + (j * 163) % 720 + 14 * math.sin(t * 2 + j)
        by = 650 - ph * 600
        ctx.new_path()
        ctx.arc(bx, by, 6 + (j % 3) * 4, 0, 2 * math.pi)
        _stroke(ctx, 3, "#ffffff", 0.55)
    pov_self(ctx, t, "swim")
    if gb > 0:                                                # 白い泡がひいていく
        ctx.rectangle(0, 0, PW, PH)
        ctx.set_source_rgba(0.75, 0.82, 0.92, 0.7 * gb)
        ctx.fill()
        pov_self(ctx, t, "swim")


def pov_grow(ctx, t, u):
    """海で大きくなる（横から）: 同じ1匹が 1年・8年・16年と大きくなって泳ぐ"""
    grad(ctx, 0, PH, "#2a6a92", "#0a2c50")
    for j in range(6):
        x0 = 60 + j * 170 + 25 * math.sin(t * 0.8 + j)
        ctx.move_to(x0, 0)
        ctx.line_to(x0 + 70, 0)
        ctx.line_to(x0 + 220, PH)
        ctx.line_to(x0 + 60, PH)
        ctx.close_path()
        ctx.set_source_rgba(0.9, 0.95, 1, 0.08)
        ctx.fill()
    for j in range(9):
        ph = (t * 0.3 + j * 0.19) % 1.0
        ctx.new_path()
        ctx.arc(100 + (j * 211) % 800 + 12 * math.sin(t * 2 + j), 660 - ph * 620, 5 + (j % 3) * 4, 0, 2 * math.pi)
        _stroke(ctx, 3, "#ffffff", 0.5)
    for k, (xa, ya, xb, yb) in enumerate(((265, 485, 375, 445), (600, 375, 675, 340))):
        g = ease_out(clamp01((u - 0.3 - 0.28 * k) / 0.3))
        if g > 0:
            ctx.new_path()
            ctx.move_to(xa, ya)
            ctx.line_to(xa + (xb - xa) * g, ya + (yb - ya) * g)
            ctx.set_source_rgba(1, 1, 1, 0.85)
            ctx.set_line_width(4)
            ctx.set_dash([10, 9])
            ctx.stroke()
            ctx.set_dash([])
            ang = math.atan2(yb - ya, xb - xa)
            ctx.new_path()
            for da in (2.6, -2.6):
                ctx.move_to(xb, yb)
                ctx.line_to(xb + 18 * math.cos(ang + da), yb + 18 * math.sin(ang + da))
            ctx.set_source_rgba(1, 1, 1, 0.85 * g)
            ctx.set_line_width(4)
            ctx.stroke()
    spots = ((190, 520, 0.28, "1年"), (480, 400, 0.5, "8年"), (770, 270, 0.78, "16年"))
    for k, (x_, y_, sc, lab) in enumerate(spots):
        g = ease_out(clamp01((u - 0.12 - 0.28 * k) / 0.3))
        if g <= 0:
            continue
        loggerhead(ctx, x_ + 8 * math.sin(t * 1.6 + k), y_ + 7 * math.sin(t * 1.9 + k), sc, 1, t * 2.0, g)
        text(ctx, lab, x_, y_ + 62 * (0.5 + sc), 40, WHITE, alpha=g)


def pov_back(ctx, t, u):
    """22年たって、浜に戻ってきた（横から。大人のアカウミガメが夜の浜に上がる）"""
    night_beach(ctx, t, nest=False)
    m = ss(0.0, 1.0, u)
    x_ = lerp(200.0, 560.0, m)
    y_ = lerp(560.0, 600.0, m)
    ell(ctx, x_ + 10, y_ + 44, 190, 16)                       # 甲羅の真下の短い影
    ctx.set_source_rgba(0.08, 0.06, 0.04, 0.22)
    ctx.fill()
    loggerhead(ctx, x_, y_ + 40, 1.0, 1, t * 0.8)
    text(ctx, "22年後", 170, 150, 56, WHITE, alpha=ease_out(clamp01((u - 0.2) / 0.3)))


def content_d(ctx, cy, t, a):
    """見本の1匹の一生: 子ガメの目の高さ（砂の中・波打ちぎわ・海）→ 海で大きくなる → 浜に戻る"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    ctx.rectangle(0, 0, PW, PH)
    ctx.clip()
    shots = ((pov_shot1, T_S0, T_P2), (pov_shot3, T_P2, T_P3), (pov_shot4, T_P3, T_P4), (pov_grow, T_P4, T_P5), (pov_back, T_P5, T_E0))
    for k, (fn, s0, s1) in enumerate(shots):
        fi = ss(s0 - 0.2, s0 + 0.2, t) if k > 0 else 1.0
        fo = 1 - ss(s1 - 0.2, s1 + 0.2, t) if k < len(shots) - 1 else 1.0
        al = fi * fo
        if al <= 0:
            continue
        ctx.push_group()
        fn(ctx, t, clamp01((t - s0) / (s1 - s0)))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)
    pa = 1 - ss(T_P4 - 0.2, T_P4 + 0.2, t)                   # 一人称のあいだだけ
    if pa > 0:
        pov_vignette(ctx, 0.4 * pa)
    ctx.restore()
    if pa > 0:
        ctx.save()
        panel_local(ctx, cy)
        rrect(ctx, 14, 14, 390, 76, 16)                       # 「子ガメの目線」の札
        ctx.set_source_rgba(1, 1, 1, 0.9 * pa)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.7 * pa)
        text(ctx, "子ガメの目線", 209, 53, 50, INK, alpha=pa)
        ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


STAGES = [("1年目", 0.0, 1.0), ("小さい子ども", 1.0, 8.0), ("大きい子ども", 8.0, 16.0), ("若者", 16.0, 22.0)]


def content_e(ctx, cy, t, a):
    """1万個の点が年ごとに減る（年のカウンターと段階の名前）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    yr = year_at(t)
    n_alive = draw_dots(ctx, yr)
    ai = int(round(yr)) if abs(yr - round(yr)) < 1e-6 else int(math.floor(yr))
    text(ctx, f"{ai}年", 190, 80, 84, WHITE)
    text(ctx, "生きている", 590, 56, 32, WHITE, bold=False)
    text(ctx, f"{n_alive:,}匹", 600, 118, 66, ORANGE if n_alive < 1200 else WHITE)
    cx, cy_ = dots_layout()
    u = t - T_E0
    si_ = sample()["idx"]
    ring = ease_out(clamp01(u / 0.4))
    lab_a = 1 - ss(2.2, 2.8, u)
    if ring > 0:
        note.pen_circle(ctx, cx[si_] + 2.4, cy_[si_] + 1.8, 24, 24, "#ff8a7a", seed=9, width=6, progress=clamp01(u / 0.4), alpha=ring)
        rrect(ctx, cx[si_] - 72, cy_[si_] - 66, 148, 40, 8)
        ctx.set_source_rgba(1, 1, 1, 0.95 * ring * lab_a)
        ctx.fill()
        text(ctx, "見本の1匹", cx[si_] + 2, cy_[si_] - 46, 30, RED, alpha=ring * lab_a)
    cur = 0
    for k, (nm, a0, a1) in enumerate(STAGES):
        if yr > a0 + 1e-6:
            cur = k
    for k, (nm, a0, a1) in enumerate(STAGES):
        xc = (110, 330, 620, 830)[k]
        wd = (130, 250, 250, 130)[k]
        chip(ctx, xc, 652, wd, 44, nm, 28, bg="#ffb347" if k == cur else "#2d3b5c", fg=INK if k == cur else "#c9d0e0",
             edge="#f6f1e3" if k == cur else "#6c7a99")
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_f(ctx, cy, t, a):
    """答え: 22年目に生き残った点（12匹）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    n_ = draw_dots(ctx, 22.0)
    text(ctx, "22年", 190, 80, 84, WHITE)
    text(ctx, "生きている", 590, 56, 32, WHITE, bold=False)
    text(ctx, f"{n_:,}匹", 600, 118, 66, ORANGE)
    r = results()
    cx, cy_ = dots_layout()
    u = t - T_REV
    pr = ease_out(clamp01((u - 0.1) / 0.5))
    pulse = 0.5 + 0.5 * math.sin(u * 5.0)
    for i in np.nonzero(r["alive"])[0]:
        ctx.new_path()
        ctx.arc(cx[i] + 2.4, cy_[i] + 1.8, 17 + 2 * pulse, 0, 2 * math.pi)
        _stroke(ctx, 3.4, "#ff8a7a", 0.9 * pr)
    text(ctx, "大人になって 浜に戻る", 480, 652, 34, ORANGE, alpha=pr)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- ぶれ: 1万回作り直した浜ごとの、大人になった数 ----
BASE_Y, BAR_PITCH, BAR_W2, BAR_X0 = 480.0, 44.0, 36.0, 40.0


def content_g(ctx, cy, t, a):
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    r = results()
    rh = r["rh"]
    mxv = float(rh.max())
    u = t - T_BL
    gr = ease_out(clamp01((u - 0.2) / 1.3))
    text(ctx, "1万個の浜を 1万回 作り直した", 480, 56, 42, INK)
    text(ctx, "浜ごとの、大人になった数", 480, 108, 36, INK, bold=False)
    med = int(r["median"])
    for i in range(18):
        v = float(rh[i]) if i < len(rh) else 0.0
        hgt = v / mxv * 250 * gr
        if v > 0:
            hgt = max(hgt, 3.0 * gr)
        x_ = BAR_X0 + i * BAR_PITCH + BAR_PITCH / 2
        isr = i == med
        if hgt > 0:
            rrect(ctx, x_ - BAR_W2 / 2, BASE_Y - hgt, BAR_W2, hgt + 0.01, 5)
            ctx.set_source_rgba(*hexrgb(FC if isr else BLUE, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 2.6, INK, 0.85)
        text(ctx, str(i), x_, BASE_Y + 24, 26, FC_D if isr else INK)
    ctx.move_to(BAR_X0, BASE_Y + 1)
    ctx.line_to(BAR_X0 + 18 * BAR_PITCH, BASE_Y + 1)
    _stroke(ctx, 3, INK, 0.8)
    text(ctx, "大人になった数（匹）", 480, BASE_Y + 66, 30, PENCIL, bold=False)
    z = ease_out(clamp01((u - 1.4) / 0.4))
    if z > 0:
        x0 = BAR_X0 + BAR_PITCH / 2
        text(ctx, "0匹の浜は", 30, 300, 32, BLUE_D, align="left", alpha=z)
        text(ctx, f"{int(rh[0])}回", 30, 342, 40, BLUE_D, align="left", alpha=z)
        note.pen_line(ctx, x0, 372, x0, BASE_Y - 8, BLUE_D, seed=4, width=4, progress=z, alpha=0.9)
    m_ = ease_out(clamp01((u - 2.0) / 0.5))
    if m_ > 0:
        xm = BAR_X0 + med * BAR_PITCH + BAR_PITCH / 2
        hh = float(rh[med]) / mxv * 250
        note.pen_circle(ctx, xm, BASE_Y - hh / 2, 36, hh / 2 + 22, RED, seed=7, width=6, progress=m_)
        text(ctx, f"中央値 {med}匹", xm, BASE_Y - hh - 48, 40, RED, alpha=m_)
        text(ctx, "（中央値＝1万回の ちょうど真ん中の値）", 480, 635, 28, PENCIL, bold=False, alpha=m_)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def win_alpha(t, s0, s1):
    return ss(s0 - 0.05, s0 + 0.3, t) * (1 - ss(s1, s1 + 0.3, t))


def cy_of(t):
    return lerp(CY_INTRO, CY_FINAL, INTRO.moved(t))


def draw_panel_scene(ctx, t):
    cy = cy_of(t)
    ctx.push_group()
    ctx.save()
    z = 1.0 + 0.05 * (1 - ease(clamp01(t / 1.1)))
    if z > 1.0:
        ctx.translate(540, cy + 330)
        ctx.scale(z, z)
        ctx.translate(-540, -(cy + 330))
    rrect(ctx, PX, cy - 35, PW, PH, 24)
    fill(ctx, PANEL_BG)
    ctx.fill()
    ctx.save()
    rrect(ctx, PX, cy - 35, PW, PH, 24)
    ctx.clip()
    for fn, s0, s1 in ((content_a, -1.0, T_R1), (content_b, T_R1, T_R2), (content_c, T_R2, T_S0), (content_d, T_S0, T_E0),
                       (content_e, T_E0, T_REV), (content_f, T_REV, T_BL), (content_g, T_BL, T_Q),
                       (content_closing, T_Q, DURATION + 1)):
        ca = win_alpha(t, s0, s1)
        if ca > 0:
            fn(ctx, cy, t, ca)
    ctx.restore()
    d_ = 0.35 * (1 - ss(0.0, 0.9, t))                         # 冒頭: 暗い浜に月の光がさす
    if d_ > 0:
        rrect(ctx, PX, cy - 35, PW, PH, 24)
        ctx.set_source_rgba(0.04, 0.06, 0.14, d_)
        ctx.fill()
    rrect(ctx, PX, cy - 35, PW, PH, 24)
    _stroke(ctx, 3, PENCIL, 0.6)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint()


def bottom_card(ctx, t, key, size=40, color="yellow", fg=INK, y=1385.0, x=565.0):
    s_, ta, tb = CARDS[key]
    al = win(t, ta, tb, 0.25, 0.25)
    if al > 0:
        note.sticky(ctx, s_, x, y, size, color, fg=fg, a=al, tilt=-0.015)


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


def big3_size(max_w=840.0):
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・三択（横1列）。その下に冬の浜（0秒目から動く）"""
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(840.0), 108.0)
        ys = (450, 450 + sz * 1.5, 450 + sz * 3.0)
        for line, y in zip(BIG_Q, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q[-1], sz)
        note.pen_line(ctx, 565 - w3 / 2 - 6, ys[2] + sz * 0.62, 565 + w3 / 2 + 6, ys[2] - 4 + sz * 0.62, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = ys[2] + 100
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = 800.0, CY_INTRO + 130.0
            fill(ctx, (*hexrgb(PAPER)[:3], 0.96 * a2))
            core.rrect(ctx, cx - 120, cy - 120, 240, 190, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 120, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 72, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy + 4, 50, 48, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy + 4)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) + 1 - n), 0, 0, 78, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
        sz = min(56.0, 100.0 * 850.0 / wmax)
        for k_, y_ in enumerate((398, 456, 514)):
            text(ctx, BIG_Q[k_], 540, y_, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[-1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 548, 540 + w2 / 2 + 6, 545, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 590
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 860)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 66 + vw, y - 2, PENCIL, seed=i + 40, width=4, progress=rev, alpha=0.8)

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
    draw_panel_scene(ctx, t)
    for key in CARDS:
        if key == "ans":
            bottom_card(ctx, t, key, 52, fg=RED)
        elif key == "q":
            bottom_card(ctx, t, key, 48)
        elif key in ("s1", "s2"):
            bottom_card(ctx, t, key, 40)
        else:
            bottom_card(ctx, t, key, 40)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------
def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 164.8, 196.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    mx.add(0.3, bell(784.0, 0.6), 0.25)
    mx.add(T_R1 + 0.4, riser(0.8), 0.3)
    mx.add(T_R1 + 2.0, bell(784.0, 0.8), 0.3)
    mx.add(T_R2 + 0.4, bell(659.3, 0.8), 0.3)
    mx.add(CARDS["c2b"][1] + 0.1, blip(880, 0.08), 0.35)
    mx.add(T_S0 + 0.3, bell(784.0, 0.8), 0.25)
    mx.add(T_P2, blip(660, 0.08), 0.3)
    mx.add(T_P3, whoosh(1.0), 0.25)
    mx.add(T_P4, blip(520, 0.08), 0.3)
    mx.add(T_P5, blip(440, 0.08), 0.3)
    mx.add(CARDS["s1"][1], bell(523.3, 1.2), 0.3)
    mx.add(CARDS["s2"][1], bell(659.3, 1.2), 0.3)
    for k_ in E_MARK:
        mx.add(k_, blip(740, 0.1), 0.35)
    mx.add(T_HC - 0.3, riser(0.8), 0.4)
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(CARDS["a1"][1] + 0.1, bell(698.5, 0.8), 0.3)
    mx.add(T_BL + 0.3, bell(659.3, 0.8), 0.35)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------
def change_fraction(t0, t1):
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


def recount():
    """run とは別の書き方（年ごとの生存率の表で、1個ずつ年を進める）で数え直す"""
    yr_s = [0.6747] + [0.75] * 7 + [0.6758] * 8 + [0.7425] * 6          # 22年分
    rng = np.random.default_rng(SEED)
    alive = np.ones(N, bool)
    dth = np.full(N, 99)
    cnt = []
    for y_, s_ in enumerate(yr_s, 1):
        d_ = alive & (rng.random(N) >= s_)
        dth[d_] = y_
        alive &= ~d_
        cnt.append(int(alive.sum()))
    p = 1.0
    for s_ in yr_s:
        p *= s_
    reps = np.random.default_rng(SEED + 1).binomial(N, p, size=10000)
    return dict(adults=int(alive.sum()), cnt=cnt, first_adult=int(np.argmax(dth == 99)), reps=reps, dth=dth)


def run_checks():
    r = results()
    S = sample()
    rc = recount()
    mj = load_model_json()
    rp = r["reps"]
    checks = []
    checks.append(("1万個", float(len(r["dd"])), float(N), 0.0))
    checks.append(("大人になった数 = umigame.json（12匹）", float(r["adults"]), float(mj["adults"]), 0.0))
    checks.append(("大人になった数 数え直し（別の書き方）= 結果", float(rc["adults"]), float(r["adults"]), 0.0))
    checks.append(("段階の終わりの残り（1・8・16・22年）= umigame.json", float([(a, b, c) for a, b, c in r["left"]] == [(a, b, c) for a, b, c in mj["left_after_stage"]]), 1.0, 0.0))
    checks.append(("年ごとの生存数 数え直し = 点の数え（1・8・16・22年）",
                   float([rc["cnt"][y_ - 1] for y_ in (1, 8, 16, 22)] == [r["surv"][y_] for y_ in (1, 8, 16, 22)]), 1.0, 0.0))
    checks.append(("札の数字 6,790・866・39・12 が結果と同じ", float([_LS[1], _LS[8], _LS[16], _LS[22]] == [6790, 866, 39, 12]
                                                              and "6,790" in CARD_TEXT["v1"] and "866" in CARD_TEXT["v2"] and "39" in CARD_TEXT["v3"]
                                                              and "12匹" in CARD_TEXT["a1"]), 1.0, 0.0))
    checks.append(("大人になるまで = 22年（札と段階の長さ 1+7+8+6）", float(sum(d for _, _, d in LIFE_STAGES) == 22 and "22年" in CARD_TEXT["c2b"]), 1.0, 0.0))
    checks.append(("1年目に死んだ数 = umigame.json（3,210）", float(int((r["dd"] == 1).sum())), float(mj["died_year1"]), 0.0))
    checks.append(("死んだ年の中央値 = umigame.json（3年目）", float(np.median(r["dd"])), float(mj["median_death_year"]), 0.0))
    checks.append(("ぶれ 最小〜最大 = umigame.json（0〜17）と札", float((int(rp.min()), int(rp.max())) == (mj["reps"]["min"], mj["reps"]["max"])
                                                          and "0匹〜17匹" in CARD_TEXT["bl"]), 1.0, 0.0))
    checks.append(("ぶれ 中央値 = umigame.json（6匹）と札", float(float(np.median(rp)) == mj["reps"]["median"] and "中央値は6匹" in CARD_TEXT["bl"]), 1.0, 0.0))
    checks.append(("ぶれ 0匹の浜 = umigame.json（14回）", float((rp == 0).sum()), float(mj["reps"]["zero"]), 0.0))
    checks.append(("ぶれ 10匹以上の浜 = umigame.json（1,266回）", float((rp >= 10).sum()), float(mj["reps"]["ge10"]), 0.0))
    checks.append(("ぶれ 数え直し（別の書き方）= 同じ分布", float(np.array_equal(rc["reps"], rp)), 1.0, 0.0))
    checks.append(("棒グラフの合計 = 1万回", float(int(r["rh"].sum())), 10000.0, 0.0))
    checks.append(("棒グラフ 0〜17匹ですべて（18本で足りる）", float(int(rp.max()) <= 17), 1.0, 0.0))
    key = r["key"]
    checks.append(("規則の答え = 約10匹（計算の節・umigame.json）", float(key == "約10匹" and key == mj["answer"]), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(key)), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 約10匹・約100匹・約1,000匹 の順", float(LABELS == ["約10匹", "約100匹", "約1,000匹"]), 1.0, 0.0))
    checks.append(("答えの札は 中立（答えは『約10匹』。）", float(CARD_TEXT["ans"] == "答えは『約10匹』。"), 1.0, 0.0))
    checks.append(("見本: 最初に大人になった1匹 = umigame.json の sample_adult（2820）", float(S["idx"] == mj["sample_adult"]["index"] == 2820), 1.0, 0.0))
    checks.append(("見本: 数え直し（別の書き方）の最初に大人になった1匹も同じ", float(rc["first_adult"] == S["idx"]), 1.0, 0.0))
    checks.append(("見本: 手前の個体はすべて大人になっていない", float(not r["alive"][:S["idx"]].any() and bool(r["alive"][S["idx"]])), 1.0, 0.0))
    checks.append(("見本: 点の見本が 最後まで残る（dd=99）", float(int(r["dd"][S["idx"]]) == 99), 1.0, 0.0))
    checks.append(("見本: 点の配置で見本の点が帯の真ん中", float(abs(dots_layout()[0][S["idx"]] - (62 * 6.7 + 36.0)) < 1e-6), 1.0, 0.0))
    checks.append(("見本の札: 大人になった見本（札に 死 を含まない）", float(all("死" not in CARD_TEXT[k_] for k_ in ("s0", "s1", "s2"))), 1.0, 0.0))
    # 答えの向きを見せない: 22年目の数（12匹）が出るのは 数え上げの終わり以降
    t_first12 = min(t_ for t_ in (CARDS["a1"][1], T_HC + CNT - 0.05))
    checks.append(("答えの前に 12匹を出さない: 札 c1・c2・v1〜v3 に「12」「22年目」を含まない",
                   float(all("12" not in CARD_TEXT[k_] and "22年目" not in CARD_TEXT[k_] for k_ in ("c1", "c2a", "c2b", "s0", "s1", "s2", "v1", "v2", "v3"))), 1.0, 0.0))
    checks.append(("カウンターが 22年に着くのは 数え上げの終わり（T_HC+CNT）", float(abs(year_at(T_HC + CNT) - 22.0) < 1e-9 and year_at(T_HC + CNT - 0.2) < 22.0), 1.0, 0.0))
    checks.append(("16年目の札の間は 16年のまま（22年の数を先に見せない）", float(abs(year_at(CARDS["v3"][2] - 0.05) - 16.0) < 1e-9), 1.0, 0.0))
    checks.append(("答えの札は 数え上げの終わり（12匹）のあと", float(CARDS["ans"][1] >= T_HC + CNT), 1.0, 0.0))
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(450 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行の文（台本どおり）", float(BIG_Q == ["ウミガメの卵、1万個。", "大人になって浜に戻るのは", "何匹？"]), 1.0, 0.0))
    for s_, ta, tb in cards():
        checks.append((f"札「{s_.replace(chr(10), '')}」が読み切れる（{tb - ta:.2f}秒 / 要る {need(s_):.2f}秒）", float(tb - ta >= need(s_) - 1e-9), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本の5つの絵が それぞれ 3秒以上", float(min(POV_SHOTS) >= 3.0), 1.0, 0.0))
    ordered = sorted(CARDS.values(), key=lambda c: c[1])
    checks.append(("札どうしが重ならない", float(all(ordered[i][2] <= ordered[i + 1][1] + 1e-9 for i in range(len(ordered) - 1))), 1.0, 0.0))
    checks.append(("台本の順: 札の出る順が 台本どおり", float([k_ for k_, _ in sorted(CARDS.items(), key=lambda kv: kv[1][1])]
                                                   == ["c1", "c2a", "c2b", "s0", "s1", "s2", "v1", "v2", "v3", "ans", "a1", "bl", "q"]), 1.0, 0.0))
    checks.append(("結果が見える時間: 数え上げのあと 答えまで 0.6秒以上", float(T_REV - (T_HC + CNT) >= 0.6 - 1e-9), 1.0, 0.0))
    checks.append(("札 s2 は 見本の場面のうち（カウンターより前）", float(CARDS["s2"][2] <= T_E0 + 0.01), 1.0, 0.0))
    checks.append(("札 v1 のとき 1年", float(abs(year_at(CARDS["v1"][1] + 0.2) - 1.0) < 1e-9), 1.0, 0.0))
    checks.append(("札 v2 のとき 8年", float(abs(year_at(CARDS["v2"][1] + 0.2) - 8.0) < 1e-9), 1.0, 0.0))
    checks.append(("札 v3 のとき 16年", float(abs(year_at(CARDS["v3"][1] + 0.2) - 16.0) < 1e-9), 1.0, 0.0))
    checks.append(("長さ 45〜58.9秒（lint は60秒未満）", float(45.0 <= DURATION <= 58.9), 1.0, 0.0))
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


def lint():
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
            first = np.frombuffer(bytes(surf.get_data()), np.uint8).copy()
        elif i == int(0.3 * FPS):
            surf.flush()
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8).copy()
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
    r = results()
    S = sample()
    print(f"長さ {DURATION:.1f}秒  研究 {T_R1:.1f}  比べ方 {T_R2:.1f}  一人称 {T_S0:.1f}/{T_P2:.1f}/{T_P3:.1f}/{T_P4:.1f}/{T_P5:.1f}  点 {T_E0:.1f}  答え {T_REV:.1f}  ぶれ {T_BL:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  大人 {r['adults']}匹  答え: {r['key']}  見本: {S['idx']}個目（大人）")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2,
          T_R1 + 1.5, T_R2 + 1.0, CARDS["c2b"][1] + 1.6,
          T_S0 + 1.5, T_P2 + 1.5, T_P3 + 1.5, T_P4 + 1.6, T_P5 + 1.8,
          T_E0 + 0.35, CARDS["v1"][1] + 1.2, CARDS["v2"][1] + 1.2, CARDS["v3"][1] + 1.2, T_HC + 0.8,
          T_REV + 0.3, CARDS["a1"][1] + 1.5, T_BL + 1.0, T_BL + 3.6, T_Q + 1.8]
    stills(draw, ts, OUT)
    for old in OUT.glob("w480_*.png"):
        old.unlink()
    paths = sorted(OUT.glob("still_*.png"))
    ims = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        im = im.resize((480, int(round(im.height * 480 / im.width))))
        im.save(OUT / f"w480_{p.name[6:]}")
        ims.append(im)
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((480 + 8) * cols, (ims[0].height + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 488, (i // cols) * (ims[0].height + 8)))
    sheet.save(OUT / "contact_480.png")
    # 一人称の場面は 原寸で4枚（砂の中／夜空と月／波打ちぎわ／海の中）
    for old in OUT.glob("pov_*.png"):
        old.unlink()
    for k_, tt in enumerate((T_S0 + 1.5, T_P2 + 1.6, T_P3 + 1.6, T_P4 + 2.7, T_P5 + 2.4), 1):
        core.still(draw, tt, OUT / f"pov_{k_}.png")
    print("原寸: still_*.png / 480px幅: w480_*.png / 一覧: contact_480.png・sheet.png / 一人称: pov_1〜4.png ->", OUT)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        stills_all()
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
