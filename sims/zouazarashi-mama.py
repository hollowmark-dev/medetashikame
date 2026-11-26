"""ゾウアザラシのメスの赤ちゃん。一生で子を10頭以上産むのは何頭に1頭？（めでたしかめ ショート）— 2026-11-09 作成（ナレーションなし・60秒未満）

台本は research/shorts_seal_turtle_scripts_2026-11-09.md の「A. ゾウアザラシ」（ユーザーOK済み。札の文言・順番・数字は変えない。足したのは絵と絵の中の短いラベルだけ）。
計算の本体はこのファイルの「計算（1万頭）」の節（置き方・seed 2611・答えの決め方は、1万頭を回す前に固定した docstring を、その節にそのまま残してある。ここでは変えない）。
この sim は「1万頭の結果を読んで絵にする」ところ。数字はすべてその節の計算から読み込む（手で打たない）。

【見本の1頭】 1万頭の最初の1頭そのもの（0歳で死亡・子0頭）。一人称の場面（赤ちゃんの目線）で描く。
【一人称の場面】 赤ちゃんの目の高さから見た景色。自分の体は画面の下の端に鼻先と前ひれが少し見えるだけ。視点は第三者に変わらない。
  生まれたては黒い毛、乳離れの頃は銀灰色に生え替わるので、1枚目は黒・2〜3枚目は銀灰色。死は「海の中で暗くなって見えなくなる」で表す。
【言い方】 答えは中立に「答えは『20頭に1頭』。」。高齢（16歳から）の生き残り方は置き方なので、画面に「計算での見立て」と小さく1回出す。
問い: 「ゾウアザラシのメスの赤ちゃん。／一生で、子を10頭以上産むのは／何頭に1頭？」
選択肢: A 2頭に1頭 ／ B 20頭に1頭 ／ C 200頭に1頭（正解の記号は B。run_checks で確かめる）
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# =====================================================================
# 計算（1万頭）— この1ファイルだけで、1万頭の結果と out/models_1128/zouazarashi.json を作り直せる（python sims/zouazarashi-mama.py --model）
# 計算の置き方・種・答えの決め方は、1万頭を回す前に固定した（結果を見て変えていない）。元の docstring:
#
# ゾウアザラシのメスの赤ちゃん1万頭。一生で何頭の子を産む？（slug: zouazarashi-mama 予定）の計算。
#
# 元にした研究（数字はすべてここから。計算の前に決めた）:
# - Le Boeuf, Condit & Reiter (2019) Canadian Journal of Zoology 97(12):1203-1217
#   「Lifetime reproductive success of northern elephant seals」。カリフォルニアの繁殖地で 7,735頭のメスを乳離れから一生追跡。
#   - 生き残り（標識の焼き印の調べ）: 1歳まで 57%、4歳まで 25%（初めて産む年齢でいちばん多いのが4歳）、10歳まで 9%、17歳まで 4%。
#   - 5〜16歳の年間生存率 86.3%、その後21歳まで下がる（Condit ほか 2014）。記録された最長は23歳・17頭。
#   - 1年に子を産む割合 87〜97.5%。
#   - 確かめに使う数字: 75%が一度も産まない、10頭以上産んだのは6%（468頭）で全体の子の54.7%、1頭あたり平均1.57頭。
# - Condit ほか (2024) Canadian Journal of Zoology「Inherent versus random variation in fitness of elephant seals」:
#   一生に産む子の数は母から娘へ受け継がれない（ほぼ運で決まる。主に何歳まで生きるか）。
#
# 1回 = メスの赤ちゃん1頭の一生。1万頭（1万回）。乱数の種は 2611（計算の前に決めた）。
# - 毎年、その年齢の生存率のくじで生き残るかを決める。
#   0→1歳 0.57、1→4歳は毎年 (0.25/0.57)^(1/3)、4→16歳 0.863、16歳から毎年同じだけ下げて 23歳で0（記録の最長23歳に合わせた置き方。上位の端だけに効く）。
# - 4歳から、生きている年は 92.5% のくじで子を1頭産む（研究の幅 87〜97.5% の真ん中。両端でも答えが変わらないことを確かめる）。
# 見本の1頭（2026-11-09 ユーザー指示で、結果を見る前に決めた選び方）: 1万頭の順で、最初に子を1頭以上産んだ1頭。
#   （ふだんの「見本は1万回の最初の1回」の例外。最初の1頭は1歳前に死ぬので「悲しい」とのこと）
# 数えるもの: 一生に産んだ子の数。0頭の割合、10頭以上の割合、10頭以上のメスが産んだ子の割合、死んだ年齢の中央値、最長。
#
# 答え（問い「10頭以上産むメスは何頭に1頭？」A 2頭に1頭 / B 20頭に1頭 / C 200頭に1頭）の決め方（計算の前に固定）:
# 10頭以上産んだメスの割合を、選択肢の 50%・5%・0.5% と比で比べ（対数で）、いちばん近いものを正解にする。
# =====================================================================
R, SEED = 10000, 2611
F_MID, F_LO, F_HI = 0.925, 0.87, 0.975
OPTIONS = [("2頭に1頭", 0.5), ("20頭に1頭", 0.05), ("200頭に1頭", 0.005)]


def surv(a):
    if a == 0:
        return 0.57
    if a < 4:
        return (0.25 / 0.57) ** (1 / 3)
    if a < 16:
        return 0.863
    return max(0.0, 0.863 * (23 - a) / (23 - 16))


def run(f=F_MID, seed=SEED, n=R):
    rng = np.random.default_rng(seed)
    alive = np.ones(n, bool)
    pups = np.zeros(n, int)
    death = np.zeros(n, int)
    births = np.zeros((n, 30), bool)
    surv_to = {}
    for a in range(30):
        surv_to[a] = float(alive.mean())
        if a >= 4:
            b = alive & (rng.random(n) < f)
            births[b, a] = True
            pups[b] += 1
        death[alive] = a
        alive &= rng.random(n) < surv(a)
    return pups, death, births, surv_to


def summary(f=F_MID, seed=SEED):
    pups, death, births, st = run(f, seed)
    ge10 = pups >= 10
    share = float(pups[ge10].sum() / pups.sum())
    frac = float(ge10.mean())
    ans = min(OPTIONS, key=lambda o: abs(np.log(frac) - np.log(o[1])))[0]
    hist = {str(k): int((pups == k).sum()) for k in range(int(pups.max()) + 1)}
    return dict(f=f, seed=seed,
                surv_to1=round(st[1], 4), surv_to4=round(st[4], 4), surv_to10=round(st[10], 4), surv_to17=round(st[17], 4),
                zero=int((pups == 0).sum()), ge10=int(ge10.sum()), share_ge10=round(share, 4),
                mean_pups=round(float(pups.mean()), 3), max_pups=int(pups.max()), max_age=int(death.max()),
                median_death_age=float(np.median(death)), median_pups_breeders=float(np.median(pups[pups > 0])),
                hist=hist, answer=ans,
                sample=dict(pups=int(pups[0]), death_age=int(death[0]),
                            birth_ages=[int(a) for a in np.nonzero(births[0])[0]]),
                sample_breeder=_first_breeder(pups, death, births))


def _first_breeder(pups, death, births):
    """1万頭の順で、最初に子を1頭以上産んだ1頭（選び方は計算の前に決めた）"""
    i = int(np.nonzero(pups > 0)[0][0])
    return dict(index=i, pups=int(pups[i]), death_age=int(death[i]),
                birth_ages=[int(a) for a in np.nonzero(births[i])[0]])


def build_model_json():
    """旧 main と同じ中身（mid・lo・hi・別の種10通り）"""
    return dict(mid=summary(F_MID), lo=summary(F_LO), hi=summary(F_HI),
                other_seeds=[summary(F_MID, s)["ge10"] for s in range(100, 110)])


def load_model_json():
    """out/models_1128/zouazarashi.json を読む。なければ上の計算を回して作る（公開側には out/ がない）"""
    if MODEL_JSON.exists():
        return json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    res = build_model_json()
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    try:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(txt, encoding="utf-8")
    except OSError:
        pass
    return json.loads(txt)


SLUG = "zouazarashi-mama"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
MODEL_JSON = Path(__file__).resolve().parents[1] / "out" / "models_1128" / "zouazarashi.json"

N = R
CNT = 1.0                                            # 1万頭の数え上げの秒数
_RES = {}


def results():
    """1万頭の結果（run そのまま）"""
    if _RES:
        return _RES["r"]
    pups, death, births, st = run(F_MID, SEED)
    summ = summary(F_MID, SEED)
    ge10 = pups >= 10
    _RES["r"] = dict(pups=pups, death=death, births=births, surv=st, summ=summ, zero=int((pups == 0).sum()),
                     ge10=int(ge10.sum()), total=int(pups.sum()), ge10_pups=int(pups[ge10].sum()),
                     hist=np.bincount(pups, minlength=21), key=summ["answer"])
    return _RES["r"]


def sample():
    """見本の1頭 = 1万頭の順で、最初に子を1頭以上産んだ1頭（選び方は結果を見る前に決めた。_first_breeder）"""
    r = results()
    sb = _first_breeder(r["pups"], r["death"], r["births"])
    return dict(index=sb["index"], pups=sb["pups"], death=sb["death_age"], births=sb["birth_ages"])


SB = sample()


if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    if "--model" in sys.argv:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(json.dumps(build_model_json(), ensure_ascii=False, indent=1), encoding="utf-8")
        print("書いた:", MODEL_JSON)
    r = results()
    S = sample()
    print(f"{N}頭  0頭 {r['zero']:,}  10頭以上 {r['ge10']:,}  答え: {r['key']}  子の合計 {r['total']:,}（10頭以上が {r['ge10_pups']:,}）")
    print(f"見本: {S['index'] + 1}頭目（index {S['index']}）  子{S['pups']}頭  産んだ年 {S['births']}  死んだ年齢 {S['death']}")
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
note.DATE = "11.26"

FC, FC_D = "#e0801f", "#a85a0a"
BLUE, BLUE_D = "#5f86b0", "#34567f"
SKY, SAND = "#dbe4ec", "#e6d9bf"
PANEL_BG = "#fbf8ef"

LABELS = [o[0] for o in OPTIONS]                  # 2頭に1頭 / 20頭に1頭 / 200頭に1頭
CORRECT = 1
BIG_Q = ["ゾウアザラシのメスの赤ちゃん。", "一生で、子を10頭以上産むのは", "何頭に1頭？"]

CY_INTRO, CY_FINAL = 830.0, 655.0
PW, PH = 960.0, 690.0                                # 絵の枠（横幅いっぱい近く）
PX = 60.0
T_CHO = (0.7, 0.9, 1.1)
T_CD = (1.2, 1.8, 2.4)
T_MOVE, T_GO = 2.8, 3.2

CARD_TEXT = {
    "c1": "メス7,735頭を、\n一生追いかけた研究がある。",
    "c2a": "生き残る割合は、\n研究の数字で決めた。",
    "c2b": "1万頭の一生を、\n1年ずつ進める。",
    "s0": "たとえば、この1頭では",
    "c4": f"{SB['births'][0]}歳で、初めて子を産んだ。",
    "s1": f"この1頭は、{SB['death']}歳まで生きた。\n子は{SB['pups']}頭。",
    "v1": "1歳まで生きたのは、約半分。",
    "v2": "子を産める4歳まで生きたのは、\n4頭に1頭。",
    "ans": "答えは『20頭に1頭』。",
    "a1": "10頭以上産んだのは、\n1万頭のうち594頭。",
    "sh": "この594頭が、\n群れの子の半分を産んだ。",
    "tw1": "たくさん産む力は、\n母から娘へ受け継がれなかった。",
    "tw2": "長く生きられるかの\n運で決まっていた。",
    "q": "あなたは、\n何頭に1頭だと思いましたか？",
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


POV_SHOTS = (3.4, 3.4)


def setup():
    global T_R1, T_R2, T_S0, T_P2, T_P3, T_P4, T_E0, T_H0, T_HC, T_REV, T_SH, T_TW, T_TWB, T_Q, DURATION
    global SCENES, CARDS, E_KEYS, E_MARK
    T_R1 = T_GO
    T_R2 = T_R1 + 0.1 + hold("c1") + 0.05
    T_S0 = T_R2 + 0.2 + hold("c2a") + 0.05 + hold("c2b") + 0.1
    T_P3 = T_S0 + POV_SHOTS[0]                               # 初めての海
    T_P2 = T_P3
    T_P4 = T_P3 + POV_SHOTS[1]                               # 大人になる（4歳）
    c4a = T_P4 + 0.1                                         # 大人になる（4歳）→ 初めての子
    c4b = c4a + hold("c4")
    s1a = c4b + 0.05
    s1b = s1a + hold("s1")
    T_E0 = s1b + 0.05
    # 1万頭が年ごとに減る: 年齢カウンターのキー (動画の秒, 年齢)
    t1 = T_E0 + 1.0                                          # 1歳に着く
    v1a = t1 + 0.1
    v1b = v1a + hold("v1")
    t4 = v1b + 0.7                                           # 4歳に着く
    v2a = t4 + 0.1
    v2b = v2a + hold("v2")
    t17 = v2b + 0.8
    T_H0 = t17 + 0.2
    E_KEYS = [(T_E0, 0.0), (T_E0 + 0.5, 0.0), (t1, 1.0), (v1b, 1.0), (t4, 4.0), (v2b, 4.0), (t17, 17.0)]
    E_MARK = (t1, t4, t17)
    T_HC = T_H0 + 0.1
    T_REV = T_HC + CNT + 0.6
    ans_a = T_REV + 0.1
    ans_b = ans_a + hold("ans")
    a1_a = ans_b + 0.05
    a1_b = a1_a + hold("a1")
    T_SH = a1_b + 0.05
    sh_a = T_SH + 0.1
    T_TW = sh_a + hold("sh") + 0.05
    tw1_a = T_TW + 0.1
    T_TWB = tw1_a + hold("tw1") + 0.05
    tw2_a = T_TWB + 0.1
    T_Q = tw2_a + hold("tw2") + 0.05
    DURATION = T_Q + 0.1 + hold("q") + 0.05
    SCENES = [("冒頭（問い・冬の浜の母と赤ちゃん）", 0.0, T_GO), ("研究の札 メス7,735頭", T_R1, T_R2), ("比べ方の札", T_R2, T_S0),
              ("見本の1頭（母と乳・浜に1頭・海へ・4歳・初めての子）", T_S0, T_E0), ("1万頭の点が年ごとに減る", T_E0, T_H0),
              ("産んだ子の数・答え", T_H0, T_SH), ("この594頭が子の半分を産んだ", T_SH, T_TW),
              ("ひねり① 母から娘へ受け継がれない", T_TW, T_TWB), ("ひねり② 長く生きられるかの運", T_TWB, T_Q), ("締め", T_Q, DURATION)]
    CARDS = {
        "c1": (CARD_TEXT["c1"], T_R1 + 0.1, T_R1 + 0.1 + hold("c1")),
        "c2a": (CARD_TEXT["c2a"], T_R2 + 0.2, T_R2 + 0.2 + hold("c2a")),
        "c2b": (CARD_TEXT["c2b"], T_R2 + 0.25 + hold("c2a"), T_R2 + 0.25 + hold("c2a") + hold("c2b")),
        "s0": (CARD_TEXT["s0"], T_S0 + 0.1, T_S0 + 0.1 + hold("s0")),
        "c4": (CARD_TEXT["c4"], c4a, c4b),
        "s1": (CARD_TEXT["s1"], s1a, s1b),
        "v1": (CARD_TEXT["v1"], v1a, v1b),
        "v2": (CARD_TEXT["v2"], v2a, v2b),
        "ans": (CARD_TEXT["ans"], ans_a, ans_b),
        "a1": (CARD_TEXT["a1"], a1_a, a1_b),
        "sh": (CARD_TEXT["sh"], sh_a, sh_a + hold("sh")),
        "tw1": (CARD_TEXT["tw1"], tw1_a, tw1_a + hold("tw1")),
        "tw2": (CARD_TEXT["tw2"], tw2_a, tw2_a + hold("tw2")),
        "q": (CARD_TEXT["q"], T_Q + 0.1, T_Q + 0.1 + hold("q")),
    }


setup()


def cards():
    return list(CARDS.values())


def age_at(t):
    """年齢カウンター（動画の秒 → 小数の年齢）。キーの間はなめらかに"""
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


SEAL_COL = {"mother": ("#9d8975", "#c6b6a2", "#6f5e51"),
            "pup": ("#37343c", "#4d4953", "#26232b"),
            "silver": ("#9ea5b1", "#c0c6cf", "#727985")}


def seal(ctx, x, gy, s, kind="mother", facing=1, t=0.0, a=1.0, blink=False, shadow=True):
    """ゾウアザラシ（メスと赤ちゃん）の横向き。(x, gy) は腹の接地点の中央、体の長さは約 560·s px。
    やわらかい手描き風。オスの長い鼻は描かない（メスの話）。facing = 1 で右向き"""
    if a <= 0:
        return
    body, belly, flip = SEAL_COL[kind]
    pupk = kind != "mother"
    ctx.save()
    if a < 1:
        ctx.push_group()
    ctx.translate(x, gy - 70 * s)
    ctx.scale(facing * s, s)
    lw = 3.4
    br = 1 + 0.014 * math.sin(t * 2.0 + x * 0.01)
    if shadow:
        ctx.save()
        ctx.translate(-20, 72)
        ctx.scale(1, 0.1)
        ctx.arc(0, 0, 300, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0.2, 0.18, 0.15, 0.16)
        ctx.fill()
    ctx.save()
    ctx.translate(0, 70)
    ctx.scale(1, br)
    ctx.translate(0, -70)
    # うしろひれ
    ctx.new_path()
    ctx.move_to(-250, 14)
    ctx.curve_to(-298, -20, -334, -8, -330, 24)
    ctx.curve_to(-304, 26, -284, 44, -246, 42)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(flip))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    # 体
    ctx.new_path()
    ctx.move_to(232, 28)
    ctx.curve_to(228, -4, 200, -34, 160, -40)
    ctx.curve_to(110, -62, 40, -82, -60, -78)
    ctx.curve_to(-160, -74, -230, -32, -262, 10)
    ctx.line_to(-250, 46)
    ctx.curve_to(-200, 64, -100, 72, 0, 70)
    ctx.curve_to(100, 72, 190, 64, 232, 28)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(body))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    # おなかの明るい部分
    ctx.new_path()
    ctx.move_to(-244, 48)
    ctx.curve_to(-150, 68, -30, 72, 60, 68)
    ctx.curve_to(150, 66, 205, 52, 226, 34)
    ctx.curve_to(190, 50, 100, 42, 0, 44)
    ctx.curve_to(-100, 46, -190, 40, -244, 48)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(belly, 0.85))
    ctx.fill()
    if not pupk:                                          # 首のしわ
        for dx, dy in ((125, -12), (95, -2), (65, 8)):
            ctx.new_path()
            ctx.move_to(dx, dy - 30)
            ctx.curve_to(dx - 12, dy - 6, dx - 12, dy + 22, dx, dy + 46)
            _stroke(ctx, 2.4, INK, 0.22)
    # 前ひれ
    ctx.new_path()
    ell(ctx, 98, 52, 52, 17, 0.5 + 0.04 * math.sin(t * 1.7))
    ctx.set_source_rgba(*hexrgb(flip))
    ctx.fill_preserve()
    _stroke(ctx, lw)
    # 顔
    ey = -6
    if blink:
        ctx.new_path()
        ctx.move_to(158, ey)
        ctx.line_to(182, ey)
        _stroke(ctx, 3.4, INK, 0.9)
    else:
        er = 13 if pupk else 11
        ctx.new_path()
        ctx.arc(170, ey, er, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#1c1a20"))
        ctx.fill()
        ctx.new_path()
        ctx.arc(170 + 4, ey - 4, 3.6, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.fill()
    ctx.new_path()
    ell(ctx, 216, 12, 7, 4, -0.5)
    ctx.set_source_rgba(*hexrgb("#1c1a20", 0.85))
    ctx.fill()
    ctx.new_path()
    ctx.move_to(230, 33)
    ctx.curve_to(206, 44, 186, 42, 166, 28)
    _stroke(ctx, 2.8, INK, 0.8)
    for dx, dy in ((204, 24), (194, 30), (184, 22)):
        ctx.new_path()
        ctx.arc(dx, dy, 2.2, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.fill()
    ctx.restore()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: 浜と海 ----------
def beach_bg(ctx, hz, t, sea_h=130.0, night=0.0):
    """冬の浜: 空・海・波打ちぎわ・砂（枠の中の座標 0..PW × 0..PH）"""
    grad(ctx, 0, hz, "#cdd8e3", "#e7edf1")
    grad(ctx, hz, hz + sea_h, "#8aa5bb", "#a8bfce")
    for k in range(5):                                        # 波のきらめき
        yy = hz + 16 + k * (sea_h - 20) / 5
        xo = (t * 18 * (1 + k * 0.2) + k * 140) % 300
        for j in range(-1, 5):
            xx = j * 300 + xo
            ctx.move_to(xx, yy)
            ctx.line_to(xx + 70, yy)
            _stroke(ctx, 3.0, "#ffffff", 0.45)
    grad(ctx, hz + sea_h, PH, "#ddd0b6", SAND)
    ctx.new_path()                                            # 波打ちぎわの泡
    for i in range(0, 41):
        x_ = i * 24.0
        y_ = hz + sea_h + 5 * math.sin(i * 0.9 + t * 1.2)
        (ctx.move_to if i == 0 else ctx.line_to)(x_, y_)
    _stroke(ctx, 11, "#ffffff", 0.85)
    ctx.rectangle(0, hz + sea_h + 8, PW, 44)                  # 濡れた砂
    ctx.set_source_rgba(0.62, 0.55, 0.42, 0.18)
    ctx.fill()
    rng = np.random.default_rng(7)
    for _ in range(26):                                       # 小石
        x_, y_ = rng.uniform(0, PW), rng.uniform(hz + sea_h + 60, PH)
        ell(ctx, x_, y_, rng.uniform(4, 9), rng.uniform(3, 5))
        ctx.set_source_rgba(0.55, 0.48, 0.38, 0.35)
        ctx.fill()


# ---------- 各場面 ----------
def panel_local(ctx, cy):
    ctx.translate(PX, cy - 35)


def content_a(ctx, cy, t, a, closing=False):
    """冒頭・締め: 冬の浜。母ゾウアザラシと黒い毛の赤ちゃん"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    beach_bg(ctx, 150, t)
    seal(ctx, 370, 590, 1.2, "mother", 1, t, blink=(t * 0.8) % 3.7 < 0.13)
    seal(ctx, 800, 612, 0.64, "pup", -1, t + 1.0, blink=(t * 0.9) % 4.1 < 0.13)
    if closing:
        u = t - T_Q
        text(ctx, "？", 640, 250 + 6 * math.sin(t * 4), 150, RED, alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_closing(ctx, cy, t, a):
    content_a(ctx, cy, t, a, closing=True)


def content_b(ctx, cy, t, a):
    """研究の札: メス7,735頭の点（91×85）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_R1
    n = int(7735 * ease(clamp01((u - 0.2) / 1.7)))
    cols, rows = 91, 85
    ctx.new_path()
    for k_ in range(n):
        r_, c_ = divmod(k_, cols)
        ctx.rectangle(40 + c_ * 9.55, 182 + r_ * 5.4, 5.4, 3.6)
    ctx.set_source_rgba(*hexrgb("#5a7ea6", 0.9))
    ctx.fill()
    text(ctx, f"{n:,}頭", 480, 84, 78, BLUE_D)
    text(ctx, "メスのゾウアザラシ", 480, 146, 34, INK, bold=False)
    text(ctx, "出典: Le Boeuf ほか（2019）", 480, 665, 28, PENCIL, bold=False, alpha=clamp01((u - 1.0) / 0.4))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def dots_layout():
    if "dots" in _RES:
        return _RES["dots"]
    rng = np.random.default_rng(5)
    perm = rng.permutation(N)
    mid = 40 * 125 + 62                                      # 見本の1頭（0番）は帯の真ん中に置く
    j = int(np.where(perm == mid)[0][0])
    k_ = SB["index"]
    perm[k_], perm[j] = perm[j], perm[k_]
    cx = (perm % 125) * 6.7 + 36.0
    cy_ = (perm // 125) * 5.2 + 192.0
    _RES["dots"] = (cx, cy_)
    return _RES["dots"]


def draw_dots(ctx, age, appear=1.0, show_alive=True):
    """1万頭の点。age = 小数の年齢（死んだ年の点は次の年へ進むあいだにうすくなって消える）"""
    r = results()
    cx, cy_ = dots_layout()
    death = r["death"]
    ai = int(math.floor(age + 1e-9))
    fr = age - ai
    lim = int(appear * N)
    idx = np.arange(N)
    full = (death > ai) & (idx < lim)
    dying = (death == ai) & (idx < lim)
    ctx.new_path()
    for i in np.nonzero(full)[0]:
        ctx.rectangle(cx[i], cy_[i], 4.8, 3.6)
    ctx.set_source_rgba(*hexrgb("#4a6f9b", 0.92))
    ctx.fill()
    al = 1 - ss(0.1, 0.9, fr)
    if al > 0.02:
        ctx.new_path()
        for i in np.nonzero(dying)[0]:
            ctx.rectangle(cx[i], cy_[i], 4.8, 3.6)
        ctx.set_source_rgba(*hexrgb("#4a6f9b", 0.92 * al))
        ctx.fill()
    return int((full | dying).sum()) if fr < 1e-6 else int(full.sum())


def content_c(ctx, cy, t, a):
    """比べ方: 研究の生き残る割合 → 1万頭を1年ずつ"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_R2
    tb = CARDS["c2b"][1] - T_R2
    r = results()
    pa = 1 - ss(tb - 0.1, tb + 0.3, u)
    if pa > 0:
        text(ctx, "研究の数字（生き残る割合）", 480, 90, 42, INK, alpha=pa)
        for yy, lab, v, seed in ((250, "1歳まで", 0.57, 1), (470, "4歳まで", 0.25, 2)):
            g = ease_out(clamp01((u - 0.4 - (yy - 250) / 700) / 0.8))
            rrect(ctx, 150, yy - 50, 700, 100, 14)
            ctx.set_source_rgba(1, 1, 1, 0.7 * pa)
            ctx.fill_preserve()
            _stroke(ctx, 2.4, PENCIL, 0.6 * pa)
            if v * 700 * g > 2:
                rrect(ctx, 150, yy - 50, 700 * v * g, 100, 14)
                ctx.set_source_rgba(*hexrgb(BLUE, 0.95 * pa))
                ctx.fill_preserve()
                _stroke(ctx, 3.4, INK, 0.9 * pa)
            text(ctx, lab, 150, yy - 80, 38, INK, align="left", alpha=pa)
            text(ctx, f"{int(round(v * 100))}%", 150 + 700 * v * g + 14, yy, 56, BLUE_D, align="left", alpha=pa * g)
    ga = ss(tb - 0.1, tb + 0.5, u)
    if ga > 0:
        n_ = clamp01((u - tb) / 0.9)
        draw_dots(ctx, 0.0, appear=n_)
        text(ctx, "1万頭", 480, 100, 78, BLUE_D, alpha=ga)
        text(ctx, "0歳 → 1歳 → 2歳 → …", 480, 660, 38, INK, alpha=ga)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 一人称の場面（赤ちゃんの目線） ----
def pov_self(ctx, t, kind):
    """赤ちゃんの体: 画面の下の端に、自分の鼻づらの上側だけが少し見える（目・鼻の穴は描かない。ひれも出さない）"""
    c0 = SEAL_COL[kind][0]
    bob = 5 * math.sin(t * 2.1)
    ctx.save()
    ctx.translate(480, 715 + bob)                             # 鼻づら（下半分は枠の外）
    ell(ctx, 0, 0, 150, 110)
    ctx.set_source_rgba(*hexrgb(c0))
    ctx.fill_preserve()
    _stroke(ctx, 4)
    ell(ctx, 0, -80, 60, 12)                                  # つや
    ctx.set_source_rgba(1, 1, 1, 0.2)
    ctx.fill()
    for sg in (-1, 1):                                        # ひげ（左右に3本ずつ）
        for j in range(3):
            ctx.new_path()
            ctx.move_to(sg * 120, -44 + j * 16)
            ctx.line_to(sg * (190 + j * 8), -66 + j * 22)
            _stroke(ctx, 3, "#f4f1ea", 0.75)
    ctx.restore()


def pov_vignette(ctx):
    g = cairo.RadialGradient(PW / 2, PH / 2, 260, PW / 2, PH / 2, 620)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0.05, 0.05, 0.1, 0.34)
    ctx.set_source(g)
    ctx.rectangle(0, 0, PW, PH)
    ctx.fill()


def pov_shot1(ctx, t, u):
    """母の大きな体（赤ちゃんの目の高さ。母は浜の場面と同じ横顔で、画面いっぱい）"""
    grad(ctx, 0, PH, "#ccd7e2", "#e6edf1")
    grad(ctx, 470, PH, "#ddd0b4", "#d3c3a3")                  # 砂
    seal(ctx, 905, 560, 2.45, "mother", -1, t, blink=(int(t * 0.7) % 5 == 4))


def pov_shot2(ctx, t, u):
    """母が海へ帰り、浜に1頭だけ残る（もう銀灰色）"""
    beach_bg(ctx, 120, t, 140.0)
    m = ss(0.08, 0.86, u)                                     # 母が遠ざかる
    sx, sy, ssc = lerp(300, 690, m), lerp(560, 300, m), lerp(1.0, 0.5, m)
    ctx.new_path()                                            # 母が通ったあとの砂のすじ
    ctx.move_to(300, 560)
    for k in range(1, 13):
        f = k / 12 * m
        ctx.line_to(lerp(300, 690, f), lerp(560, 300, f))
    ctx.set_source_rgba(0.5, 0.42, 0.3, 0.11)
    ctx.set_line_width(16)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    al = 1 - ss(0.80, 0.97, u)
    if al > 0:
        seal(ctx, sx, sy, ssc, "mother", 1, t * (1 + 2 * (1 - m)), a=al)
    pov_self(ctx, t, "pup")


def pov_shot3(ctx, t, u):
    """初めて海へ入る。波が近づき、海の中が暗くなっていく"""
    hz = 150
    grad(ctx, 0, hz, "#cbd8e4", "#e6edf1")
    grad(ctx, hz, PH, "#8aa5bb", "#d9ccb2")
    wl = lerp(300.0, 700.0, ss(0.1, 0.62, u))                 # 水ぎわ（砂の側）
    grad(ctx, hz, 300, "#8aa5bb", "#97b0c4")
    # 砂
    ctx.new_path()
    ctx.move_to(0, 300)
    for i in range(0, 41):
        (ctx.line_to)(i * 24.0, wl + 10 * math.sin(i * 0.7 + t * 1.6) - (i % 2) * 2)
    ctx.line_to(PW, PH)
    ctx.line_to(0, PH)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#dccfb3"))
    ctx.fill()
    ctx.new_path()                                            # 海
    ctx.move_to(0, hz)
    ctx.line_to(PW, hz)
    for i in range(40, -1, -1):
        ctx.line_to(i * 24.0, wl + 10 * math.sin(i * 0.7 + t * 1.6))
    ctx.close_path()
    g = cairo.LinearGradient(0, hz, 0, 700)
    g.add_color_stop_rgba(0, *hexrgb("#8aa5bb"))
    g.add_color_stop_rgba(1, *hexrgb("#4f7f9e"))
    ctx.set_source(g)
    ctx.fill()
    for k in range(6):                                        # 近づく波
        f = ((k / 6) + t * 0.18) % 1.0
        yy = hz + (wl - hz) * f ** 1.7
        ctx.new_path()
        for i in range(0, 41):
            (ctx.move_to if i == 0 else ctx.line_to)(i * 24.0, yy + 5 * math.sin(i * 0.8 + k + t * 2))
        _stroke(ctx, 2 + 3.5 * f, "#ffffff", 0.3 + 0.35 * f)
    ctx.new_path()                                            # 先頭の泡
    for i in range(0, 41):
        (ctx.move_to if i == 0 else ctx.line_to)(i * 24.0, wl + 10 * math.sin(i * 0.7 + t * 1.6))
    _stroke(ctx, 14, "#ffffff", 0.9)
    uw = ss(0.5, 0.92, u)                                     # 海の中（だんだん暗く）
    if uw > 0:
        g = cairo.LinearGradient(0, 0, 0, PH)
        g.add_color_stop_rgba(0, *hexrgb("#4a97b5", 0.6 * uw))
        g.add_color_stop_rgba(1, *hexrgb("#1b4766", 0.7 * uw))
        ctx.set_source(g)
        ctx.rectangle(0, 0, PW, PH)
        ctx.fill()
        for j in range(5):                                    # 水面からの光
            x0 = 140 + j * 190 + 20 * math.sin(t * 0.8 + j)
            ctx.move_to(x0, 0)
            ctx.line_to(x0 + 60, 0)
            ctx.line_to(x0 + 190 + 40 * j * 0.2, PH)
            ctx.line_to(x0 + 70, PH)
            ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 0.12 * uw * (1 - 0.6 * ss(0.7, 1.0, u)))
            ctx.fill()
        for j in range(9):                                    # あわ
            ph = (t * 0.35 + j * 0.173) % 1.0
            bx = 330 + (j * 97) % 330 + 14 * math.sin(t * 2 + j)
            by = 640 - ph * 560
            ctx.new_path()
            ctx.arc(bx, by, 6 + (j % 3) * 4, 0, 2 * math.pi)
            _stroke(ctx, 3, "#ffffff", 0.6 * uw)
    la = 1 - ss(0.45, 0.6, u)                                 # 何の場面か（はじめだけ）
    if la > 0:
        rrect(ctx, PW / 2 - 130, 30, 260, 62, 14)
        ctx.set_source_rgba(1, 1, 1, 0.9 * la)
        ctx.fill()
        text(ctx, "初めての海", PW / 2, 61, 40, INK, alpha=la)


def adult_scene(ctx, t):
    """大人になる（4歳）→ 初めての子 → 5歳まで。浜の横から（一人称ではない）。最後は静かに暗くなる"""
    u = t - T_P4
    beach_bg(ctx, 150, t)
    mx_ = 330 + 40 * (1 - ease_out(clamp01(u / 1.0)))
    s1a_ = CARDS["s1"][1]
    sleep_ = t >= s1a_ + 0.6                                  # 終わりの場面: 目を閉じて静かに
    seal(ctx, mx_, 590, 1.2, "mother", 1, t * (0.3 if sleep_ else 1.0), blink=sleep_ or (t * 0.8) % 3.7 < 0.13)
    pa = ease_out(clamp01((t - CARDS["c4"][1] + 0.15) / 0.4))      # 子は「初めて子を産んだ」の札と同時に出る
    if pa > 0:
        seal(ctx, 800, 612 + 14 * (1 - pa), 0.64, "pup", -1, t + 1.0, a=pa)
    d_ = 0.62 * ss(s1a_ + 0.3, s1a_ + 2.6, t)
    age_ = SB["death"] if t >= s1a_ else SB["births"][0]
    text(ctx, f"{age_}歳", 130, 70, 56, BLUE_D)
    if d_ > 0:
        ctx.rectangle(0, 0, PW, PH)
        ctx.set_source_rgba(0.06, 0.09, 0.2, d_)
        ctx.fill()


def content_d(ctx, cy, t, a):
    """一人称の場面: 赤ちゃんの目の高さから見た景色"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    ctx.rectangle(0, 0, PW, PH)
    ctx.clip()
    if t < T_P3 + 0.2:
        pov_shot1(ctx, t, (t - T_S0) / POV_SHOTS[0])
    if T_P3 - 0.2 <= t < T_P4 + 0.2:
        al = ss(T_P3 - 0.2, T_P3 + 0.2, t) * (1 - ss(T_P4 - 0.2, T_P4 + 0.2, t))
        ctx.push_group()
        pov_shot3(ctx, t, (t - T_P3) / POV_SHOTS[1])
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)
    if t >= T_P4 - 0.2:
        al = ss(T_P4 - 0.2, T_P4 + 0.2, t)
        ctx.push_group()
        adult_scene(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)
    if t < T_P4 + 0.2:
        pov_vignette(ctx)
    ctx.restore()
    ctx.save()
    panel_local(ctx, cy)
    ctx.push_group()
    rrect(ctx, 14, 14, 330, 50, 12)                           # 「赤ちゃんの目線」の札
    ctx.set_source_rgba(1, 1, 1, 0.9)
    ctx.fill_preserve()
    _stroke(ctx, 2.2, PENCIL, 0.7)
    text(ctx, "赤ちゃんの目線", 179, 39, 32, INK)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(1 - ss(T_P4 - 0.2, T_P4 + 0.1, t))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_e(ctx, cy, t, a):
    """1万頭の点が年ごとに減る（年齢カウンター）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    ag = age_at(t)
    n_alive = draw_dots(ctx, ag)
    ai = int(math.floor(ag + 1e-9))
    text(ctx, f"{ai}歳", 200, 90, 84, BLUE_D)
    text(ctx, "生きている", 560, 70, 32, INK, bold=False, align="center")
    text(ctx, f"{results()['surv'][ai] * N:,.0f}頭", 620, 128, 62, INK)   # 数はその歳の生存数（次の歳になるまで変えない）
    ctx.set_source_rgba(*hexrgb(INK, 0.0))
    # 見本の1頭に赤い丸
    cx, cy_ = dots_layout()
    u = t - T_E0
    k_ = SB["index"]
    ring = ease_out(clamp01(u / 0.4)) * (1 - ss(SB["death"], SB["death"] + 0.9, ag))   # 見本の1頭が消えるまで丸が付いている
    if ring > 0:
        note.pen_circle(ctx, cx[k_] + 2.4, cy_[k_] + 1.8, 22, 22, RED, seed=9, width=5, progress=clamp01(u / 0.4), alpha=ring)
        lab = ring * (1 - ss(0.9, 1.4, u))
        if lab > 0:
            rrect(ctx, cx[k_] - 62, cy_[k_] - 66, 128, 40, 8)
            ctx.set_source_rgba(1, 1, 1, 0.95 * lab)
            ctx.fill()
            text(ctx, "見本の1頭", cx[k_] + 2, cy_[k_] - 46, 30, RED, alpha=lab)
    if ag >= 15.5:
        text(ctx, "16歳から先は、計算での見立て", 480, 660, 28, PENCIL, bold=False, alpha=ss(15.5, 16.5, ag))
    if abs(ag - 4.0) < 1e-6 and t < CARDS["v2"][2]:
        text(ctx, "ここから子を産める", 480, 660, 34, FC_D)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 産んだ子の数の棒グラフ ----
BASE_Y, HS, CAPH = 470.0, 0.72, 280.0
BAR_X0, PITCH, BAR_W = 30.0, 42.0, 34.0


def bar_x(i):
    return BAR_X0 + i * PITCH + PITCH / 2


def content_f(ctx, cy, t, a):
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    r = results()
    p = ease(clamp01((t - T_HC) / CNT))
    n = int(p * N)
    h = np.bincount(r["pups"][:n], minlength=21) if n > 0 else np.zeros(21, int)
    rev = clamp01((t - T_REV) / 0.5)
    text(ctx, "1万頭が一生に産んだ子の数", 480, 52, 42, INK)
    if t < T_REV - 0.2:
        text(ctx, f"{n:,}頭目", 480, 106, 34, PENCIL, bold=False)
    sh = ss(T_SH - 0.05, T_SH + 0.35, t)
    if rev > 0.2 and sh < 1:                                  # 10頭以上の見出し
        text(ctx, "10頭以上", 0.5 * (bar_x(10) + bar_x(19)), 104, 40, FC_D, alpha=ease_out(rev))
    if sh > 0:                                                # 子の半分を産んだ右側が光る
        pulse = 0.5 + 0.5 * math.sin((t - T_SH) * 5.0)
        rrect(ctx, bar_x(10) - 24, 170, bar_x(19) - bar_x(10) + 48, 320, 16)
        ctx.set_source_rgba(1.0, 0.86, 0.3, (0.28 + 0.2 * pulse) * sh)
        ctx.fill()
    for i in range(20):
        v = int(h[i])
        hgt = min(v * HS, CAPH)
        if v > 0:
            hgt = max(hgt, 3.0)
        ok = i >= 10 and rev > 0.3
        col = FC if ok else BLUE
        if hgt > 0:
            rrect(ctx, bar_x(i) - BAR_W / 2, BASE_Y - hgt, BAR_W, hgt + 0.01, 5)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 2.6, INK, 0.85)
        if i == 0 and v * HS > CAPH:                          # 0頭の棒は高すぎるので途中を省略（波線）
            yb = BASE_Y - CAPH * 0.5
            ctx.new_path()
            ctx.move_to(bar_x(0) - 28, yb - 10)
            for k_ in range(0, 9):
                ctx.line_to(bar_x(0) - 28 + k_ * 7.0, yb - 10 + (6 if k_ % 2 else -6))
            for k_ in range(8, -1, -1):
                ctx.line_to(bar_x(0) - 28 + k_ * 7.0, yb + 10 + (6 if k_ % 2 else -6))
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(PANEL_BG))
            ctx.fill_preserve()
            _stroke(ctx, 2.4, INK, 0.75)
        text(ctx, str(i), bar_x(i), BASE_Y + 23, 24, INK if i < 10 else FC_D, alpha=0.95)
    ctx.move_to(BAR_X0, BASE_Y + 1)
    ctx.line_to(BAR_X0 + 20 * PITCH, BASE_Y + 1)
    _stroke(ctx, 3, INK, 0.8)
    text(ctx, "産んだ子の数（頭）", 450, 528, 30, PENCIL, bold=False)
    v0 = int(h[0])
    if v0 * HS > CAPH * 0.9:
        text(ctx, f"0頭は {v0:,}頭", bar_x(0) - 14, BASE_Y - CAPH - 28, 46, BLUE_D, align="left")
    if rev > 0:
        x0_, x1_ = bar_x(10) - 24, bar_x(19) + 24
        note.pen_circle(ctx, 0.5 * (x0_ + x1_), 395, 0.5 * (x1_ - x0_) + 12, 90, RED, seed=61, width=7, progress=rev)
        if sh < 0.5:
            text(ctx, f"{r['ge10']}頭", 0.5 * (x0_ + x1_), 285, 64, RED, alpha=ease_out(rev))
    if sh > 0:                                                # 子の合計のうち、594頭が産んだ分
        tot, g10 = r["total"], r["ge10_pups"]
        f = g10 / tot
        by_, bh_ = 612.0, 62.0
        text(ctx, f"産んだ子は 全部で {tot:,}頭", 450, 568, 32, INK, alpha=sh)
        bw = 840.0
        for x0_, wd, col, lab in ((30.0, bw * f, FC, f"594頭 → {g10:,}頭"), (30.0 + bw * f, bw * (1 - f), BLUE, f"のこり{N - r['ge10']:,}頭 → {tot - g10:,}頭")):
            ww = wd * ease_out(clamp01((t - T_SH - 0.3) / 0.7))
            rrect(ctx, x0_, by_, max(ww, 1), bh_, 10)
            ctx.set_source_rgba(*hexrgb(col, 0.95 * sh))
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, 0.85 * sh)
            if ww > wd * 0.9:
                text(ctx, lab, x0_ + wd / 2, by_ + bh_ / 2 + 2, 30, "#ffffff", alpha=sh)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- ひねり ----
def content_g1(ctx, cy, t, a):
    """たくさん産む力は、母から娘へ受け継がれなかった"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    grad(ctx, 0, PH, "#e3eaf0", "#efe6d0")
    u = t - T_TW
    seal(ctx, 280, 560, 0.85, "mother", 1, t)
    seal(ctx, 760, 585, 0.56, "silver", -1, t + 1)
    text(ctx, "母", 280, 625, 44, INK)
    text(ctx, "娘", 760, 640, 44, INK)
    g = ease_out(clamp01((u - 0.3) / 0.7))
    ctx.new_path()                                            # 母から娘へ渡る矢印
    ctx.move_to(250, 300)
    ctx.curve_to(380, 150, 640, 150, 780, 330)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * g))
    ctx.set_line_width(7)
    ctx.set_dash([18, 14])
    ctx.stroke()
    ctx.set_dash([])
    ctx.new_path()
    ctx.move_to(742, 308)
    ctx.line_to(782, 338)
    ctx.line_to(790, 288)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * g))
    ctx.set_line_width(7)
    ctx.stroke()
    x_ = ease_out(clamp01((u - 1.0) / 0.4))
    if x_ > 0:
        note.pen_line(ctx, 470, 130, 570, 230, RED, seed=3, width=12, progress=x_)
        note.pen_line(ctx, 570, 130, 470, 230, RED, seed=4, width=12, progress=x_)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def three_lives():
    """1万頭の中から3頭（0歳で死んだ見本の1頭・5頭産んだ1頭・最多の1頭）"""
    r = results()
    pu, de, bi = r["pups"], r["death"], r["births"]
    mx = int(pu.max())
    idx = [0, int(np.where(pu == 5)[0][0]), int(np.where(pu == mx)[0][0])]
    return [dict(i=i, pups=int(pu[i]), death=int(de[i]), births=[int(a_) for a_ in np.nonzero(bi[i])[0]]) for i in idx]


def content_g2(ctx, cy, t, a):
    """長く生きられるかの運で決まっていた: 3頭の一生（年齢の線と、子を産んだ年）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_TWB
    X0, X1, AMAX = 70.0, 850.0, 24.0
    xa = lambda ag: X0 + (X1 - X0) * ag / AMAX               # noqa: E731
    text(ctx, "1万頭の中の3頭の一生", 480, 60, 42, INK)
    lives = three_lives()
    labs = ("1歳になる前に死んだ", "10歳くらいまで生きた", "いちばん長く生きた")
    for k, (lv, lab) in enumerate(zip(lives, labs)):
        yy = 210 + k * 170
        end = lv["death"] + 1
        pr = ease_out(clamp01((u - 0.3 - 0.3 * k) / 1.0))
        text(ctx, lab, X0, yy - 58, 32, INK, align="left")
        rrect(ctx, X0, yy - 18, X1 - X0, 36, 10)
        ctx.set_source_rgba(1, 1, 1, 0.6)
        ctx.fill_preserve()
        _stroke(ctx, 2, PENCIL, 0.5)
        ww = (xa(end) - X0) * pr
        rrect(ctx, X0, yy - 18, max(ww, 1), 36, 10)
        ctx.set_source_rgba(*hexrgb(BLUE, 0.92))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.85)
        for ba in lv["births"]:
            if xa(ba + 0.5) <= X0 + ww:
                ctx.new_path()
                ctx.arc(xa(ba + 0.5), yy, 8.5, 0, 2 * math.pi)
                ctx.set_source_rgba(*hexrgb(FC))
                ctx.fill_preserve()
                _stroke(ctx, 2, INK, 0.9)
        text(ctx, f"子 {lv['pups']}頭", X1 - 6, yy - 58, 38, FC_D, align="right", alpha=clamp01((pr - 0.6) / 0.4))
    text(ctx, "○ = 子を産んだ年", 480, 640, 30, PENCIL, bold=False)
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
                       (content_e, T_E0, T_H0), (content_f, T_H0, T_TW), (content_g1, T_TW, T_TWB),
                       (content_g2, T_TWB, T_Q), (content_closing, T_Q, DURATION + 1)):
        ca = win_alpha(t, s0, s1)
        if ca > 0:
            fn(ctx, cy, t, ca)
    ctx.restore()
    d_ = 0.55 * (1 - ss(0.0, 0.9, t))                         # 冒頭: 暗い朝の浜に光がさす
    if d_ > 0:
        rrect(ctx, PX, cy - 35, PW, PH, 24)
        ctx.set_source_rgba(0.08, 0.1, 0.2, d_)
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
        elif key == "tw2":
            bottom_card(ctx, t, key, 40, color="pink", fg=RED)
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
    mx.add(T_P3, blip(520, 0.08), 0.3)
    mx.add(T_P3 + 1.2, whoosh(1.0), 0.25)
    mx.add(CARDS["s1"][1], bell(523.3, 1.2), 0.3)
    for k_ in E_MARK[:2]:
        mx.add(k_, blip(740, 0.1), 0.35)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(CARDS["a1"][1] + 0.1, bell(698.5, 0.8), 0.3)
    mx.add(T_SH + 0.3, bell(698.5, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)
    mx.add(T_TW + 1.1, thump(), 0.4)
    mx.add(T_TWB + 0.3, bell(659.3, 0.8), 0.35)
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
    """run とは別の書き方（年ごとのくじを手で回す）で、件数・最初に子を産んだ1頭を数え直す"""
    rng = np.random.default_rng(SEED)
    alive = np.ones(N, bool)
    cnt = np.zeros(N, int)
    last = np.zeros(N, int)
    bys = []
    for a_ in range(30):
        b = np.zeros(N, bool)
        if a_ >= 4:
            b = alive & (rng.random(N) < F_MID)
            cnt[b] += 1
        bys.append(b)
        last[alive] = a_
        alive &= rng.random(N) < surv(a_)
    i = next(k for k in range(N) if cnt[k] > 0)
    return dict(zero=int((cnt == 0).sum()), ge10=int((cnt >= 10).sum()), idx=i, pups=int(cnt[i]), death=int(last[i]),
                births=[a_ for a_ in range(30) if bys[a_][i]], before_zero=bool((cnt[:i] == 0).all()), hist=np.bincount(cnt))


def run_checks():
    r = results()
    S = sample()
    rc = recount()
    mj = load_model_json()["mid"]
    checks = []
    checks.append(("頭数 = 1万", float(len(r["pups"])), float(N), 0.0))
    checks.append(("0頭 = out/models_1128/zouazarashi.json（7,546頭）", float(r["zero"]), float(mj["zero"]), 0.0))
    checks.append(("10頭以上 = zouazarashi.json（594頭）", float(r["ge10"]), float(mj["ge10"]), 0.0))
    checks.append(("0頭 数え直し = run", float(rc["zero"]), float(r["zero"]), 0.0))
    checks.append(("10頭以上 数え直し = run", float(rc["ge10"]), float(r["ge10"]), 0.0))
    checks.append(("棒グラフ 0〜19頭の頭数が zouazarashi.json の hist と全部同じ",
                   float(all(int(r["hist"][k]) == mj["hist"][str(k)] for k in range(20)) and int(r["hist"][20:].sum()) == 0), 1.0, 0.0))
    checks.append(("棒グラフ 数え直しの hist も同じ", float(list(rc["hist"][:20]) == [int(x) for x in r["hist"][:20]]), 1.0, 0.0))
    checks.append(("札の数字 594 が結果と同じ", float(f"{r['ge10']}頭" in CARD_TEXT["a1"]), 1.0, 0.0))
    checks.append(("札の数字 7,735 が 研究の数字（点 91×85 = 7,735）", float(91 * 85 == 7735 and "7,735" in CARD_TEXT["c1"]), 1.0, 0.0))
    checks.append(("1歳まで生きた割合 = 約半分（0.5〜0.6）", r["summ"]["surv_to1"], 0.57, 0.03))
    checks.append(("4歳まで生きた割合 = 4頭に1頭（0.25 ± 0.02）", r["summ"]["surv_to4"], 0.25, 0.02))
    checks.append(("点の数え: 1歳の生存数 = surv_to[1]×1万", float(int((r["death"] >= 1).sum())), r["surv"][1] * N, 0.5))
    checks.append(("点の数え: 4歳の生存数 = surv_to[4]×1万", float(int((r["death"] >= 4).sum())), r["surv"][4] * N, 0.5))
    checks.append(("子の合計の半分: 594頭が産んだ割合 ≒ 0.5（0.45〜0.55）", r["ge10_pups"] / r["total"], 0.5, 0.05))
    checks.append(("子の合計 = json の mean_pups×1万", float(r["total"]), mj["mean_pups"] * N, 1.0))
    key = r["key"]
    checks.append(("規則の答え = 20頭に1頭（計算の節）", float(key == "20頭に1頭"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(key)), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号の並び: 2頭に1頭・20頭に1頭・200頭に1頭 の順", float(LABELS == ["2頭に1頭", "20頭に1頭", "200頭に1頭"]), 1.0, 0.0))
    checks.append(("答えの札は 中立（答えは『20頭に1頭』。）", float(CARD_TEXT["ans"] == "答えは『20頭に1頭』。"), 1.0, 0.0))
    sbj = mj["sample_breeder"]
    checks.append(("見本: 1万頭の順で最初に子を産んだ1頭 = zouazarashi.json の sample_breeder（index 6・子2頭・4歳と5歳・5歳で死亡）",
                   float((S["index"], S["pups"], S["death"], S["births"]) == (sbj["index"], sbj["pups"], sbj["death_age"], sbj["birth_ages"]) == (6, 2, 5, [4, 5])), 1.0, 0.0))
    checks.append(("見本: 別の書き方の数え直しでも 同じ1頭（index・子の数・産んだ年・死んだ年）",
                   float((rc["idx"], rc["pups"], rc["births"], rc["death"]) == (S["index"], S["pups"], S["births"], S["death"])), 1.0, 0.0))
    checks.append(("見本: それより前の1頭ずつは 全員 子0頭", float(rc["before_zero"] and bool((r["pups"][:S["index"]] == 0).all())), 1.0, 0.0))
    checks.append(("見本: 子の数 = 産んだ年の数", float(S["pups"] == len(S["births"])), 1.0, 0.0))
    checks.append(("見本の札の数字（4歳・5歳・子2頭）が 結果と同じ",
                   float(CARD_TEXT["c4"] == f"{S['births'][0]}歳で、初めて子を産んだ。" and f"{S['death']}歳まで" in CARD_TEXT["s1"] and f"子は{S['pups']}頭" in CARD_TEXT["s1"]), 1.0, 0.0))
    checks.append(("見本の点: 5歳のカウンターでは まだ残り、6歳では消える", float(int(r["death"][S["index"]]) >= 5 and int(r["death"][S["index"]]) < 6), 1.0, 0.0))
    checks.append(("見本の絵: 一人称の2枚は それぞれ 3.3秒以上", float(min(POV_SHOTS) >= 3.3), 1.0, 0.0))
    lv = three_lives()
    checks.append(("ひねり②の3頭: 子の数 0・5・最多", float([x["pups"] for x in lv] == [0, 5, int(r["pups"].max())]), 1.0, 0.0))
    checks.append(("ひねり②の3頭: 子の数 = 産んだ年の数", float(all(len(x["births"]) == x["pups"] for x in lv)), 1.0, 0.0))
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(450 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行の文（台本どおり）", float(BIG_Q == ["ゾウアザラシのメスの赤ちゃん。", "一生で、子を10頭以上産むのは", "何頭に1頭？"]), 1.0, 0.0))
    for s_, ta, tb in cards():
        n_ = len(s_.replace("\n", ""))
        nd = max(0.12 * n_ + 1.0, 0.5 + max(len(x) for x in s_.split("\n")) / 6.0)
        checks.append((f"札「{s_.replace(chr(10), '')}」が読み切れる（{tb - ta:.2f}秒 / 要る {nd:.2f}秒）", float(tb - ta >= nd - 1e-9), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    
    ordered = sorted(CARDS.values(), key=lambda c: c[1])
    checks.append(("札どうしが重ならない", float(all(ordered[i][2] <= ordered[i + 1][1] + 1e-9 for i in range(len(ordered) - 1))), 1.0, 0.0))
    checks.append(("台本の順: 札の出る順が 台本どおり", float([k_ for k_, _ in sorted(CARDS.items(), key=lambda kv: kv[1][1])]
                                                   == ["c1", "c2a", "c2b", "s0", "c4", "s1", "v1", "v2", "ans", "a1", "sh", "tw1", "tw2", "q"]), 1.0, 0.0))
    checks.append(("結果が見える時間: 数え上げのあと 答えまで 0.6秒以上（棒が止まって見える）", float(T_REV - (T_HC + CNT) >= 0.6 - 1e-9), 1.0, 0.0))
    checks.append(("札 s1 は 1歳のカウンターより前（見本の場面のあと）", float(CARDS["s1"][2] <= T_E0 + 0.01), 1.0, 0.0))
    checks.append(("札 v1 のとき年齢カウンター = 1歳", float(abs(age_at(CARDS["v1"][1] + 0.2) - 1.0) < 1e-9), 1.0, 0.0))
    checks.append(("札 v2 のとき年齢カウンター = 4歳", float(abs(age_at(CARDS["v2"][1] + 0.2) - 4.0) < 1e-9), 1.0, 0.0))
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
    print(f"長さ {DURATION:.1f}秒  研究 {T_R1:.1f}  比べ方 {T_R2:.1f}  一人称 {T_S0:.1f}/{T_P3:.1f}/{T_P4:.1f}  点 {T_E0:.1f}  棒 {T_H0:.1f}  答え {T_REV:.1f}  子の半分 {T_SH:.1f}  ひねり {T_TW:.1f}/{T_TWB:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  0頭 {r['zero']:,}  10頭以上 {r['ge10']:,}  答え: {r['key']}  見本: 子{S['pups']}頭・死亡{S['death']}歳")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2,
          T_R1 + 1.2, T_R1 + 2.6, T_R2 + 1.6, CARDS["c2b"][1] + 1.6,
          T_S0 + 1.8, T_P3 + 1.7, T_P4 + 0.9, CARDS["c4"][1] + 2.1, CARDS["s1"][1] + 2.7,
          T_E0 + 0.35, CARDS["v1"][1] + 1.2, CARDS["v2"][1] + 1.5, E_MARK[2] + 0.2,
          T_HC + 1.0, T_REV + 1.2, CARDS["a1"][1] + 1.5, T_SH + 1.6,
          T_TW + 2.4, T_TWB + 2.4, T_Q + 1.8]
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
    # 見本の1頭の場面は 原寸で保存（1 = 母、2 = 初めての海、3 = 大人になる、4 = 初めての子、5 = 静かに暗くなる）
    for k_, tt in enumerate((T_S0 + 1.8, T_P3 + 1.7, T_P4 + 0.9, CARDS["c4"][1] + 2.1, CARDS["s1"][1] + 2.7), 1):
        core.still(draw, tt, OUT / f"pov_{k_}.png")
    print("原寸: still_*.png / 480px幅: w480_*.png / 一覧: contact_480.png・sheet.png / 見本の1頭: pov_1〜5.png ->", OUT)


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
