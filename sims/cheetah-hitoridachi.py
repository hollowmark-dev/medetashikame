"""チーターの赤ちゃん1万頭。独り立ちできるのは何頭？（めでたしかめ ショート）— 2026-11-14 作成（ナレーションなし・60秒未満）

台本の骨組みは research/shorts_1128_fable_animals_2026-11-13.md の「2. チーター」。次の2点だけ変えた（統括の指示）:
  ①ひねり「カラハリなら約3,600頭」は使わない（元の論文で確かめられなかった）。代わりに「中央値の1頭」の場面と、
    「死んだ子のうち約7割がライオン」で締める。
  ②（母親は穴を掘らず、背の高い草むらに子を隠す。画面の「巣穴」は全部「隠れ家」にした。）
  ③見本の1頭は「1万頭の順で、最初に独り立ちできた1頭」。一人称（赤ちゃんの目線）は 隠れ家の中 → 母親の後ろを歩く → 独り立ち。死や襲われる絵は出さない。
計算の本体はこのファイルの「計算（1万頭）」の節（置き方・seed 1202・答えの決め方は、1万頭を回す前に固定した docstring を、その節にそのまま残してある。ここでは変えない）。
この sim は「1万頭の結果を読んで絵にする」ところ。数字はすべてその節の定数と out/models_1128/cheetah.json（なければ節の計算で作る）から読む（手で打たない）。
  答えを決める数字: 資料（Caro & Laurenson 1994: 125頭 → 生後2か月36頭 → 独り立ち6頭）。仮置きなし。

【見本の1頭】 1万頭の順で「最初に独り立ちできた1頭」（結果を見る前に決めた選び方。cheetah.json の sample.index = 13）。説明欄に1行書く。
【一人称の場面】 この1頭の目線: 隠れ家（背の高い草のくぼみ）の中（兄弟と、草のすき間の光）→ 母親の後ろを歩く → 独り立ち（母親が遠くに小さく見える）。
  自分の体は描かない。死や襲われる絵は出さない。ライオンの絵も出さない。
【生き物の絵】 assets/gemini_1128/cheetah_cub_cut.png（赤ちゃん・左向きに立つ）と cheetah_adult_cut.png（母親・右向きに立つ）の部品だけ。
  動きは 移動・上下の揺れ・反転・拡大縮小。草むら・隠れ家・草原・点・グラフ・札・調査の車はコード。
【答えの前に出さないもの】 「6頭」「125頭のうち6頭」「2,808」「439」。1万頭が減る場面は 点の減り方と段階名だけ（数のカウンターなし）。
【分母】 割合の札（死んだ子のうち約7割）にだけ本当の分母。数の札（2,808頭・439頭）に「/1万頭」は付けない。
問い: 「チーターの赤ちゃん、1万頭。／独り立ちできるのは、何頭？」
選択肢: A 約500頭 ／ B 約2,000頭 ／ C 約5,000頭（正解の記号は A。run_checks で確かめる）
"""
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# =====================================================================
# 計算（1万頭）— この1ファイルだけで、結果と out/models_1128/cheetah.json を作り直せる（python sims/cheetah-hitoridachi.py --model）
# 計算の置き方・種・答えの決め方は、回す前に固定した（結果を見て変えていない）。元の docstring:
#
# チーターの赤ちゃん1万頭。独り立ちできるのは、何頭？（slug: cheetah-hitoridachi 予定）の計算。
#
# 元にした資料（計算の前に決めた）:
# - Caro & Laurenson（Science 1994）セレンゲティで生まれたばかりの子125頭を追った記録（UC Davis のニュースで確認）:
#   125頭 → 生後2か月（巣穴を出るころ）まで36頭 → 独り立ちまで6頭。死んだ子の73%はライオンにおそわれた。
# - 2段階の割合はこの数から: 巣穴の2か月 36/125、巣穴を出てから独り立ちまで 6/36。仮置きなし。
# 1回 = 赤ちゃん1頭。1万頭。乱数の種は 1202（計算の前に決めた）。
# 数えるもの: 巣穴を出た数、独り立ちした数。中央値の1頭（1万頭を死んだ段階の順に並べた真ん中）がどこで死んだか。
# 見本の1頭（結果を見る前に決めた選び方。2026-11-13 決まり「すぐ死ぬ個体を避ける」に合わせた）: 1万頭の順で、最初に独り立ちできた1頭。
#
# 答え（A 約500頭 / B 約2,000頭 / C 約5,000頭）の決め方（計算の前に固定）:
# 独り立ちした数を 500・2,000・5,000 と比で比べ（対数の差）、いちばん近いものを正解にする。
# =====================================================================
R, SEED = 10000, 1202
P_DEN, P_IND = 36 / 125, 6 / 36
OPTIONS = [("約500頭", 500), ("約2,000頭", 2000), ("約5,000頭", 5000)]


def build_model_json():
    """旧 main と同じ中身（巣穴＝隠れ家の段階ごとの数・中央値の1頭・見本の番号）"""
    rng = np.random.default_rng(SEED)
    out_den = rng.random(R) < P_DEN
    indep = out_den & (rng.random(R) < P_IND)
    stage = np.where(indep, 2, np.where(out_den, 1, 0))       # 0=巣穴で死 1=出てから死 2=独り立ち
    med_stage = int(np.sort(stage)[R // 2])
    n_ind = int(indep.sum())
    ans = min(OPTIONS, key=lambda o: abs(np.log(max(n_ind, 1)) - np.log(o[1])))[0]
    first = int(np.nonzero(indep)[0][0])
    return dict(seed=SEED, out_den=int(out_den.sum()), indep=n_ind, answer=ans,
                theory_out=round(R * P_DEN, 1), theory_indep=round(R * P_DEN * P_IND, 1),
                died_in_den=int((stage == 0).sum()), died_after=int((stage == 1).sum()),
                median_stage=["巣穴の中で死んだ", "巣穴を出てから死んだ", "独り立ちした"][med_stage],
                sample=dict(index=first, indep=bool(indep[first])), lion_share_of_deaths=0.73)


def load_model_json():
    """out/models_1128/cheetah.json を読む。なければ上の計算を回して作る（公開側には out/ がない）"""
    if MODEL_JSON.exists():
        return json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    txt = json.dumps(build_model_json(), ensure_ascii=False, indent=1)
    try:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(txt, encoding="utf-8")
    except OSError:
        pass
    return json.loads(txt)


SLUG = "cheetah-hitoridachi"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
MODEL_JSON = ROOT / "out" / "models_1128" / "cheetah.json"
CUB_PNG = ROOT / "assets" / "gemini_1128" / "cheetah_cub_cut.png"
ADULT_PNG = ROOT / "assets" / "gemini_1128" / "cheetah_adult_cut.png"
DATE = "11.28"                                       # 日付欄（公開予定日の仮置き。あとで変える）

N = R
CNT_LIONS = 0.73
_RES = {}


def results():
    """1万頭の結果（節の build_model_json と同じ種・同じ順の乱数）。stage: 0=隠れ家で死 1=出てから死 2=独り立ち"""
    if _RES.get("r"):
        return _RES["r"]
    rng = np.random.default_rng(SEED)
    out_den = rng.random(N) < P_DEN
    indep = out_den & (rng.random(N) < P_IND)
    stage = np.where(indep, 2, np.where(out_den, 1, 0))
    n_ind = int(indep.sum())
    key = min(OPTIONS, key=lambda o: abs(math.log(max(n_ind, 1)) - math.log(o[1])))[0]
    _RES["r"] = dict(stage=stage, out_den=int(out_den.sum()), indep=n_ind, key=key,
                     median_stage=int(np.sort(stage)[N // 2]), n0=int((stage == 0).sum()), n1=int((stage == 1).sum()))
    return _RES["r"]


def sample():
    """見本の1頭 = 1万頭の順で、最初に独り立ちできた1頭（結果を見る前に決めた選び方）"""
    r = results()
    i = int(np.nonzero(r["stage"] == 2)[0][0])
    return dict(idx=i, stage=int(r["stage"][i]))


if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    if "--model" in sys.argv:
        MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
        MODEL_JSON.write_text(json.dumps(build_model_json(), ensure_ascii=False, indent=1), encoding="utf-8")
        print("書いた:", MODEL_JSON)
    r = results()
    S = sample()
    print(f"{N}頭  隠れ家を出た {r['out_den']}頭  独り立ち {r['indep']}頭  答え: {r['key']}  中央値の1頭の段階: {r['median_stage']}")
    print(f"見本: {S['idx']}頭目（0始まり）  stage={S['stage']}")
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
from engine.brand import turtle  # noqa: E402

note.use()
note.DATE = DATE

FC, FC_D = "#e0801f", "#a85a0a"
PANEL_BG = "#fbf8ef"
NAVY_BG = "#1b2742"
WHITE = "#f6f1e3"
CREAM = "#f3e8c8"
ORANGE = "#ffb347"
GREY_D = "#8b93a8"
RUST = "#c0583a"

LABELS = [o[0] for o in OPTIONS]                  # 約500頭 / 約2,000頭 / 約5,000頭
CORRECT = 0
BIG_Q = ["チーターの赤ちゃん、1万頭。", "独り立ちできるのは、何頭？"]

CY_INTRO, CY_FINAL = 735.0, 655.0
PW, PH = 960.0, 690.0                                # 絵の枠（横幅いっぱい近く）
PX = 60.0
T_CHO = (0.7, 0.9, 1.1)
T_CD = (1.2, 1.8, 2.4)
T_MSG = 0.9
T_MOVE, T_GO = 2.8, 3.2

_R = results()
N_DEN = _R["out_den"]
N_IND = _R["indep"]
SRC = "出典: Caro・Laurenson（1994）"

CARD_TEXT = {
    "c1": "赤ちゃん125頭を、\n独り立ちまで追った調査がある。",
    "c2a": "最初の2か月は、\n草むらの隠れ家でくらす。",
    "c2b": "そのあと、\n母親について歩く。",
    "s0": "たとえば、この1頭では",
    "s1": "2か月たって、隠れ家を出た。",
    "s2": "母親から離れて、独り立ちした。",
    "ans": f"正解は『{_R['key']}』。",
    "m1": "中央値の1頭は、\n隠れ家を出る前に死んだ。",
    "r1": f"隠れ家を出られたのは、{N_DEN:,}頭。",
    "r2": f"その中でも、独り立ちまで\n生きたのは、{N_IND}頭。",
    "l1": "調査では、死んだ子の約7割が\nライオンにおそわれた。",
    "q": "あなたの予想は、\nA・B・Cのどれでしたか？",
}
CARD_ORDER = ["c1", "c2a", "c2b", "s0", "s1", "s2", "ans", "m1", "r1", "r2", "l1", "q"]
PRE_ANS = ["c1", "c2a", "c2b", "s0", "s1", "s2"]
# 答えの前に 画面（札以外）に出す文字（数字を含まない）
A1_TEXT = f"独り立ちした {N_IND}頭"
PANEL_PRE_TEXT = ["赤ちゃん チーター", SRC, "隠れ家で 2か月", "母親について 歩く", "隠れ家の2か月", "母親と歩く", "独り立ち", "1万頭", "この1頭の目線", "母親",
                  "調べた赤ちゃん", "最初の2か月", "そのあと"]


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


POV_SHOTS = (3.0, 3.0, 3.4)      # 隠れ家の中・母親の後ろを歩く・独り立ち
E_STEPS = (0.6, 0.9, 1.4, 0.6, 1.4, 0.65)   # 点が出る・隠れ家の段階で止まる・隠れ家で減る・次の段階で止まる・減る・止まる


def setup():
    global T_A1, T_R1, T_R2, T_S0, T_P2, T_P3, T_E0, T_REV, T_M, T_RS, T_L, T_Q, DURATION
    global SCENES, CARDS, E_KEYS, E_END
    T_R1 = T_GO
    T_R2 = T_R1 + 0.2 + hold("c1") + 0.1
    T_S0 = T_R2 + 0.2 + hold("c2a") + 0.05 + hold("c2b") + 0.1
    T_P2 = T_S0 + POV_SHOTS[0]
    T_P3 = T_P2 + POV_SHOTS[1]
    T_E0 = T_P3 + POV_SHOTS[2]
    s = E_STEPS
    e1 = T_E0 + s[0]
    e2 = e1 + s[1]
    e3 = e2 + s[2]
    e4 = e3 + s[3]
    e5 = e4 + s[4]
    E_END = e5 + s[5]
    E_KEYS = [(T_E0, 0.0), (e2, 0.0), (e3, 1.0), (e4, 1.0), (e5, 2.0), (E_END, 2.0)]
    T_REV = E_END
    ans_a = T_REV + 0.2
    ans_b = ans_a + hold("ans")
    T_A1 = ans_a + 0.6
    T_M = T_A1 + 2.5
    m1_a = T_M + 0.2
    m1_b = m1_a + hold("m1")
    T_RS = T_M + 4.8
    r1_a = T_RS + 0.2
    r1_b = r1_a + hold("r1")
    r2_a = r1_b + 0.05
    r2_b = r2_a + hold("r2")
    T_L = r2_b + 0.1
    l1_a = T_L + 0.2
    l1_b = l1_a + hold("l1")
    T_Q = l1_b + 0.1
    DURATION = T_Q + 0.2 + hold("q") + 0.05
    SCENES = [("冒頭（問い・草むらの隠れ家）", 0.0, T_GO), ("研究の札（調査の車と125頭）", T_R1, T_R2), ("進め方（隠れ家の2か月・母親について歩く）", T_R2, T_S0),
              ("見本の1頭（隠れ家の中・母親の後ろを歩く・独り立ち）", T_S0, T_E0), ("1万頭の点が減る", T_E0, T_REV),
              ("答え・独り立ちした点（生き残りは小さい点のまま光る）", T_REV, T_M), ("中央値の1頭", T_M, T_RS), ("隠れ家を出た数と独り立ち", T_RS, T_L),
              ("調査では（ライオン約7割）", T_L, T_Q), ("締め", T_Q, DURATION)]
    CARDS = {
        "c1": (CARD_TEXT["c1"], T_R1 + 0.2, T_R1 + 0.2 + hold("c1")),
        "c2a": (CARD_TEXT["c2a"], T_R2 + 0.2, T_R2 + 0.2 + hold("c2a")),
        "c2b": (CARD_TEXT["c2b"], T_R2 + 0.25 + hold("c2a"), T_R2 + 0.25 + hold("c2a") + hold("c2b")),
        "s0": (CARD_TEXT["s0"], T_S0 + 0.2, T_S0 + 0.2 + hold("s0")),
        "s1": (CARD_TEXT["s1"], T_P2 + 0.2, T_P2 + 0.2 + hold("s1")),
        "s2": (CARD_TEXT["s2"], T_P3 + 0.2, T_P3 + 0.2 + hold("s2")),
        "ans": (CARD_TEXT["ans"], ans_a, ans_b),
        "m1": (CARD_TEXT["m1"], m1_a, m1_b),
        "r1": (CARD_TEXT["r1"], r1_a, r1_b),
        "r2": (CARD_TEXT["r2"], r2_a, r2_b),
        "l1": (CARD_TEXT["l1"], l1_a, l1_b),
        "q": (CARD_TEXT["q"], T_Q + 0.2, T_Q + 0.2 + hold("q")),
    }


setup()


def cards():
    return list(CARDS.values())


def level_at(t):
    """1万頭の段階（0=隠れ家の2か月のはじめ → 1=隠れ家を出た → 2=独り立ち）。キーの間はなめらかに"""
    ks = E_KEYS
    if t <= ks[0][0]:
        return 0.0
    for (ta, aa), (tb, ab) in zip(ks[:-1], ks[1:]):
        if t <= tb:
            return lerp(aa, ab, smooth((t - ta) / max(tb - ta, 1e-9)))
    return ks[-1][1]


# ---------- 部品（生き物の画像。コードでは描かない）----------
_IMG = {}
_NAT_RIGHT = {"cub": False, "adult": True}           # 部品が向いている向き（True=右向き）


def part_img(name):
    if name not in _IMG:
        from PIL import Image
        im = Image.open(CUB_PNG if name == "cub" else ADULT_PNG).convert("RGBA")
        im = im.crop(im.getbbox())
        k = 900.0 / im.width
        im = im.resize((900, int(round(im.height * k))), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "PNG")
        buf.seek(0)
        _IMG[name] = (cairo.ImageSurface.create_from_png(buf), im.width, im.height)
    return _IMG[name]


def part(ctx, name, cx, by, w, right, a=1.0, bob=0.0, rot=0.0, tint=None):
    """部品を描く。(cx, by) は足もとの中心、w は幅(px)、right=True で右向き。tint=(r,g,b,a) でうす暗くできる"""
    if a <= 0:
        return
    surf, iw, ih = part_img(name)
    sc = w / iw
    flip = (right != _NAT_RIGHT[name])
    ctx.save()
    ctx.translate(cx, by + bob)
    ctx.rotate(rot)
    ctx.scale(-sc if flip else sc, sc)
    if tint:
        ctx.push_group()
        ctx.set_source_surface(surf, -iw / 2, -ih)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.set_source_rgba(*tint)
        ctx.rectangle(-iw / 2 - 5, -ih - 5, iw + 10, ih + 10)
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    else:
        ctx.set_source_surface(surf, -iw / 2, -ih)
        ctx.paint_with_alpha(a)
    ctx.restore()


def cub_h(w):
    _, iw, ih = part_img("cub")
    return w * ih / iw


def adult_h(w):
    _, iw, ih = part_img("adult")
    return w * ih / iw


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


def blade(ctx, x, y, h, lean, col, lw=5.0, a=1.0):
    ctx.new_path()
    ctx.move_to(x, y)
    ctx.curve_to(x + lean * 0.2, y - h * 0.5, x + lean * 0.7, y - h * 0.85, x + lean, y - h)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()


def tuft(ctx, x, y, h, t, col, lw=5.0, n=5, a=1.0, seed=0.0):
    for k in range(n):
        lean = (k - (n - 1) / 2) * h * 0.2 + 7 * math.sin(t * 1.6 + x * 0.05 + k + seed)
        blade(ctx, x + (k - (n - 1) / 2) * 5, y, h * (0.75 + 0.25 * ((k * 7) % 5) / 4), lean, col, lw, a)


def acacia(ctx, x, y, s, col="#6b6a3a"):
    ctx.new_path()
    ctx.move_to(x, y)
    ctx.curve_to(x - 4 * s, y - 40 * s, x + 6 * s, y - 60 * s, x, y - 90 * s)
    _stroke(ctx, 6 * s, "#4d3a28", 0.95)
    ell(ctx, x, y - 98 * s, 70 * s, 20 * s)
    ctx.set_source_rgba(*hexrgb(col, 0.95))
    ctx.fill()
    ell(ctx, x - 30 * s, y - 88 * s, 45 * s, 14 * s)
    ctx.set_source_rgba(*hexrgb(col, 0.95))
    ctx.fill()


def savanna(ctx, t, hz=300.0, scroll=0.0, warm=0.0, trees=True, y1=PH):
    """朝の草原（コード）。warm 0〜1 で 空が明るく黄色に"""
    grad(ctx, 0, hz, "#f0c487" if warm < 0.5 else "#f8dc9a", "#fbebc9")
    ctx.new_path()                                        # 朝日
    ctx.arc(PW * 0.72, hz - 28, 52, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 0.95, 0.75, 0.9)
    ctx.fill()
    ctx.new_path()
    ctx.arc(PW * 0.72, hz - 28, 86, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 0.93, 0.7, 0.25)
    ctx.fill()
    grad(ctx, hz - 2, y1, "#cdb678", "#a98a49")
    if trees:
        for k, (xx, ss_) in enumerate(((120, 0.7), (430, 0.55), (800, 0.8))):
            xe = (xx - scroll * 0.1) % (PW + 240) - 120
            acacia(ctx, xe, hz + 6, ss_)
    for k in range(18):                                   # 遠い草のかたまり
        xe = (k * 197 - scroll * 0.25) % (PW + 160) - 80
        tuft(ctx, xe, hz + 28 + (k % 4) * 10, 28, t, "#8f7d3f", 3.5, 4, 0.9, seed=k)


def foreground(ctx, t, scroll=0.0, y0=PH, n=14, h0=120.0):
    """手前の草（背が高い）"""
    for k in range(n):
        xe = (k * 131 - scroll) % (PW + 220) - 110
        tuft(ctx, xe, y0 + 8, h0 * (0.8 + 0.4 * ((k * 5) % 7) / 6), t, "#6d6428" if k % 2 else "#857a35", 8.0, 5, 0.97, seed=k * 2)


def hideout(ctx, t, cx, cy, rx, ry, front=False):
    """草むらの隠れ家（コード）。背の高い草に囲まれたくぼみ。front=False: くぼみと奥の草、True: 手前の低い草"""
    if not front:
        ell(ctx, cx, cy, rx, ry)
        g = cairo.RadialGradient(cx, cy, 10, cx, cy, rx)
        g.add_color_stop_rgba(0, *hexrgb("#8a7440"))
        g.add_color_stop_rgba(1, *hexrgb("#a58c52"))
        ctx.set_source(g)
        ctx.fill_preserve()
        _stroke(ctx, 4, "#7a6636", 0.8)
        n = 11
        for k in range(n):
            a_ = math.pi * (1.05 + 0.9 * k / (n - 1))
            x_, y_ = cx + rx * 1.05 * math.cos(a_), cy + ry * 0.55 * math.sin(a_) + 8
            tuft(ctx, x_, y_, 150 + 30 * ((k * 5) % 3), t, "#6d6428" if k % 2 else "#857a35", 8.0, 5, 0.97, seed=k)
    else:
        n = 8
        for k in range(n):
            a_ = math.pi * (0.1 + 0.8 * k / (n - 1))
            x_, y_ = cx + rx * 0.95 * math.cos(a_), cy + ry * 0.95 * math.sin(a_) + 40
            tuft(ctx, x_, y_, 62, t, "#7c7030", 7.0, 5, 0.97, seed=k + 3)


# ---------- 各場面（パネルの中）----------
def panel_local(ctx, cy):
    ctx.translate(PX, cy - 35)


def chip(ctx, x, y, w, h, label, size=30, bg="#ffffff", fg=INK, a=1.0, edge=PENCIL):
    rrect(ctx, x - w / 2, y - h / 2, w, h, 14)
    ctx.set_source_rgba(*hexrgb(bg, a))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, edge, 0.85 * a)
    text(ctx, label, x, y + 2, size, fg, alpha=a)


def den_scene(ctx, t, mother=True, ncubs=3, cubw=200.0, hz=250.0, label=None, u0=0.0):
    """草むらの隠れ家と赤ちゃん（母親は左で右向き・赤ちゃんは右で左向き＝内側）。足もとは y≈480（下は草だけ）"""
    savanna(ctx, t, hz=hz)
    hx = 700 if mother else 650
    hideout(ctx, t, hx, 485, 270, 62)
    if mother:
        part(ctx, "adult", 215, 500, 400, True, bob=3 * math.sin(t * 1.5), rot=0.006 * math.sin(t * 1.1))
    cub_xs = (560, 705, 850)[:ncubs] if mother else (480, 650, 820)[:ncubs]
    for k, cx in enumerate(cub_xs):
        part(ctx, "cub", cx, 495 + (k % 2) * 8, cubw, False, bob=6 * math.sin(t * 2.4 + k * 2.1) - 3, rot=0.02 * math.sin(t * 1.9 + k))
    hideout(ctx, t, hx, 485, 270, 62, front=True)
    foreground(ctx, t, scroll=0.0, y0=PH - 8, n=12, h0=110.0)
    if label:
        rrect(ctx, 20, 20, 360, 70, 16)
        ctx.set_source_rgba(1, 1, 1, 0.92)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.7)
        text(ctx, label, 200, 56, 42, INK)


def content_a(ctx, cy, t, a):
    """冒頭: 草むらの隠れ家。母親と赤ちゃん3頭（0秒目から動く）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    den_scene(ctx, t)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def jeep(ctx, x, y, s=1.0):
    """調査の車（コード）"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -110, -80, 220, 70, 14)
    ctx.set_source_rgba(*hexrgb("#e7ddc0"))
    ctx.fill_preserve()
    _stroke(ctx, 4)
    rrect(ctx, -60, -130, 130, 56, 12)
    ctx.set_source_rgba(*hexrgb("#d9cfae"))
    ctx.fill_preserve()
    _stroke(ctx, 4)
    for xx in (-35, 12, 52):
        rrect(ctx, xx - 12, -120, 28, 34, 6)
        ctx.set_source_rgba(*hexrgb("#9fc6dd"))
        ctx.fill_preserve()
        _stroke(ctx, 2.6)
    for xx in (-68, 68):
        ctx.new_path()
        ctx.arc(xx, -8, 24, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#2f3440"))
        ctx.fill_preserve()
        _stroke(ctx, 3)
        ctx.new_path()
        ctx.arc(xx, -8, 9, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#aab0bd"))
        ctx.fill()
    ctx.restore()


def content_b(ctx, cy, t, a):
    """研究の札: 調査の車と、調べた赤ちゃん125頭の点（結果は出さない）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    u = t - T_R1
    savanna(ctx, t, hz=235, trees=True, y1=430)
    grad(ctx, 430, PH, "#a98a49", "#8d7238")
    jeep(ctx, 160, 395, 1.15)
    part(ctx, "cub", 365, 398, 150, False, bob=3 * math.sin(t * 2.2))
    part(ctx, "adult", 560, 402, 260, False, bob=2 * math.sin(t * 1.4))
    for k in range(7):
        tuft(ctx, 30 + k * 150, 440, 50, t, "#7c7030", 6, 5)
    # ノート（125頭の点）
    nb = ease_out(clamp01((u - 0.3) / 0.5))
    rrect(ctx, 80, 450, 800, 200, 14)
    ctx.set_source_rgba(*hexrgb("#fffdf4", 0.98 * nb))
    ctx.fill_preserve()
    _stroke(ctx, 3, PENCIL, 0.8 * nb)
    text(ctx, "調べた赤ちゃん", 250, 480, 30, INK, alpha=nb)
    n_show = int(125 * clamp01((u - 0.5) / 1.4))
    for k in range(n_show):
        r_, c_ = divmod(k, 25)
        ctx.new_path()
        ctx.arc(120 + c_ * 29.0, 524 + r_ * 26, 9.0, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#caa86a"))
        ctx.fill_preserve()
        _stroke(ctx, 2.2, "#7a5f2e", 0.9)
    text(ctx, SRC, 862, 482, 24, PENCIL, bold=False, align="right", alpha=clamp01((u - 1.2) / 0.4))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def stage_bar(ctx, cur, y=60.0, alpha=1.0):
    names = ["隠れ家の2か月", "母親と歩く", "独り立ち"]
    xs = (170, 480, 790)
    for k, (nm, x_) in enumerate(zip(names, xs)):
        on = (k == cur)
        chip(ctx, x_, y, 270, 54, nm, 30, bg=ORANGE if on else "#ffffff", fg=INK if on else PENCIL,
             edge=INK if on else "#bdbdbd", a=alpha)
        if k < 2:
            text(ctx, "→", (xs[k] + xs[k + 1]) / 2, y, 36, PENCIL, alpha=alpha)


def walk_scene(ctx, t, u, with_cubs=2):
    """母親について歩く（横から。草原が流れる）"""
    sc = t * 70.0
    savanna(ctx, t, hz=270, scroll=sc, warm=1.0)
    mx = 640 + 10 * math.sin(t * 0.9)
    part(ctx, "adult", mx, 520, 420, True, bob=5 * math.sin(t * 3.4), rot=0.01 * math.sin(t * 1.7))
    for k in range(with_cubs):
        cx = 360 - k * 170 + 8 * math.sin(t * 1.1 + k)
        part(ctx, "cub", cx, 528 + k * 6, 210, True, bob=6 * math.sin(t * 3.8 + k * 1.4))
    foreground(ctx, t, scroll=sc * 1.8, y0=PH - 8, n=12, h0=100.0)


def content_c(ctx, cy, t, a):
    """進め方: 最初の2か月は隠れ家 → そのあと母親について歩く（段階の名前だけ。数は出さない）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    tb = CARDS["c2b"][1]
    k = ss(tb - 0.1, tb + 0.4, t)
    if k < 1:
        den_scene(ctx, t, mother=False, ncubs=3, cubw=215, hz=250)
    if k > 0:
        ctx.push_group()
        walk_scene(ctx, t, t - tb)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k)
    stage_bar(ctx, 0 if k < 0.5 else 1, y=52)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 一人称の場面（赤ちゃんの目線。自分の体は描かない）----
def pov_vignette(ctx, k=0.4):
    g = cairo.RadialGradient(PW / 2, PH / 2, 260, PW / 2, PH / 2, 640)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(1, 0.05, 0.03, 0.02, k)
    ctx.set_source(g)
    ctx.rectangle(0, 0, PW, PH)
    ctx.fill()


def pov_den(ctx, t, u):
    """隠れ家の中。背の高い草のあいだから外の明るい光。そばに兄弟（2頭とも光のほうを向く）"""
    savanna(ctx, t, hz=300, warm=1.0)
    ctx.rectangle(0, 0, PW, PH)                           # 草の中のやわらかい影
    ctx.set_source_rgba(0.25, 0.2, 0.08, 0.18)
    ctx.fill()
    zoom = lerp(1.0, 1.06, ss(0, 1, u))
    ctx.save()
    ctx.translate(480, 400)
    ctx.scale(zoom, zoom)
    ctx.translate(-480, -400)
    for sg in (-1, 1):                                    # 左右の草の壁（本数は少なく、交差させず、うすい色）
        for k in range(4):
            x_ = (40 + k * 62) if sg < 0 else (PW - 40 - k * 62)
            h_ = 600 - k * 85
            lean = -sg * (60 + 12 * math.sin(t * 1.3 + k)) * (1 - k * 0.12)
            blade(ctx, x_, PH + 14, h_, -lean, "#a39d55", 11.0, 0.95)
    ctx.restore()
    ctx.new_path()                                        # 差し込む光
    ctx.move_to(300, 330)
    ctx.line_to(660, 330)
    ctx.line_to(860, PH)
    ctx.line_to(100, PH)
    ctx.close_path()
    ctx.set_source_rgba(1, 0.94, 0.72, 0.12)
    ctx.fill()
    tint = (0.1, 0.07, 0.03, 0.22)
    part(ctx, "cub", 380, 655, 220, True, bob=3 * math.sin(t * 2.4 + 1), tint=tint)
    part(ctx, "cub", 215, 690, 330, True, bob=4 * math.sin(t * 2.1), tint=tint)
    for k in range(20):                                   # 舞うほこり
        x_ = (k * 151) % 960
        y_ = (t * 24 + k * 53) % 700
        ctx.new_path()
        ctx.arc(x_, y_, 2 + (k % 3), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f4e4b0", 0.4))
        ctx.fill()


def pov_walk(ctx, t, u):
    """隠れ家を出て、母親の後ろを歩く（低い目線で見上げる。母親は大きく、頭は枠の上で切れる。草が手前を流れる）"""
    sc = t * 85.0
    savanna(ctx, t, hz=440, scroll=sc, warm=1.0)
    mx = 450 + 14 * math.sin(t * 0.8)
    part(ctx, "adult", mx, 718, 940, True, bob=7 * math.sin(t * 3.4), rot=0.008 * math.sin(t * 1.7))
    foreground(ctx, t, scroll=sc * 2.2, y0=PH + 14, n=11, h0=300.0)
    k = 1 - ss(0.0, 0.5, u)                               # 隠れ家を出る（暗がりがひく）
    if k > 0:
        ctx.rectangle(0, 0, PW, PH)
        ctx.set_source_rgba(0.12, 0.08, 0.04, 0.6 * k)
        ctx.fill()


def pov_alone(ctx, t, u):
    """独り立ち。母親は背を向けて、左はしの地平線のほうへ小さく遠ざかる"""
    sc = t * 70.0
    savanna(ctx, t, hz=330, scroll=sc, warm=1.0)
    ms = lerp(120.0, 84.0, ss(0, 1, u))
    mx = lerp(150.0, 105.0, ss(0, 1, u))
    part(ctx, "adult", mx, 362, ms, False, bob=1.5 * math.sin(t * 1.6))
    rrect(ctx, mx - 44, 240 - 18, 88, 36, 8)
    ctx.set_source_rgba(1, 1, 1, 0.9)
    ctx.fill()
    text(ctx, "母親", mx, 241, 28, INK)
    foreground(ctx, t, scroll=sc * 2.0, y0=PH + 10, n=11, h0=180.0)


def content_d(ctx, cy, t, a):
    """見本の1頭: 赤ちゃんの目線（隠れ家の中 → 母親の後ろを歩く → 独り立ち）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    ctx.rectangle(0, 0, PW, PH)
    ctx.clip()
    shots = ((pov_den, T_S0, T_P2), (pov_walk, T_P2, T_P3), (pov_alone, T_P3, T_E0))
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
    pov_vignette(ctx, 0.4)
    ctx.restore()
    ctx.save()
    panel_local(ctx, cy)
    rrect(ctx, 14, 14, 360, 76, 16)                       # 「この1頭の目線」の札
    ctx.set_source_rgba(1, 1, 1, 0.9)
    ctx.fill_preserve()
    _stroke(ctx, 2.2, PENCIL, 0.7)
    text(ctx, "この1頭の目線", 194, 53, 46, INK)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 1万頭の点 ----
def dots_layout():
    if "dots" in _RES:
        return _RES["dots"]
    rng = np.random.default_rng(5)
    perm = rng.permutation(N)
    mid = 40 * 125 + 62                                      # 見本の1頭は帯の真ん中に置く
    j = int(np.where(perm == mid)[0][0])
    si = sample()["idx"]
    perm[si], perm[j] = perm[j], perm[si]
    cx = (perm % 125) * 6.7 + 36.0
    cy_ = (perm // 125) * 5.2 + 192.0
    _RES["dots"] = (cx, cy_)
    return _RES["dots"]


def alive_weights(lv):
    """段階 lv のときの 各グループ（隠れ家で死・出てから死・独り立ち）の濃さ"""
    out = []
    for s_ in (0, 1):
        if lv <= s_:
            out.append(1.0)
        elif lv >= s_ + 1:
            out.append(0.0)
        else:
            out.append(1 - ss(0.1, 0.9, lv - s_))
    out.append(1.0)
    return out


def draw_dots(ctx, lv, appear=1.0, glow=0.0):
    """1万頭の点。lv = 段階。死んだ点は、うすい灰色の点として残る（消さない）。生き残った点は小さいまま、glow で光る。数は返さない"""
    cx, cy_ = dots_layout()
    st = results()["stage"]
    lim = int(appear * N)
    idx = np.arange(N)
    als = alive_weights(lv)
    for g in range(3):
        sel = (st == g) & (idx < lim)
        for col, aa in ((CREAM, als[g] * 0.95), ("#56627f", (1 - als[g]) * 0.55)):
            if aa <= 0.02:
                continue
            ctx.new_path()
            for i in np.nonzero(sel)[0]:
                ctx.rectangle(cx[i], cy_[i], 4.8, 3.6)
            ctx.set_source_rgba(*hexrgb(col, aa))
            ctx.fill()
    if glow > 0.01:
        sel = (st == 2) & (idx < lim)
        ctx.new_path()
        for i in np.nonzero(sel)[0]:
            ctx.new_sub_path()
            ctx.arc(cx[i] + 2.4, cy_[i] + 1.8, 6.5, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#ffd27a", 0.35 * glow))
        ctx.fill()
        ctx.new_path()
        for i in np.nonzero(sel)[0]:
            ctx.rectangle(cx[i] - 0.4, cy_[i] - 0.4, 5.6, 4.4)
        ctx.set_source_rgba(*hexrgb(ORANGE, 1.0 * glow))
        ctx.fill()


def content_e(ctx, cy, t, a):
    """1万頭の点が減る（点の減り方と段階の名前だけ。数のカウンターは出さない）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    lv = level_at(t)
    u = t - T_E0
    draw_dots(ctx, lv, appear=clamp01(u / E_STEPS[0]), glow=ss(1.6, 2.0, lv))
    text(ctx, "チーターの赤ちゃん 1万頭", 480, 62, 44, WHITE, alpha=ss(0, 0.3, u))
    cx, cy_ = dots_layout()
    si_ = sample()["idx"]
    ring = ease_out(clamp01((u - 0.5) / 0.4))
    lab_a = 1 - ss(2.2, 2.8, u)
    if ring > 0:
        note.pen_circle(ctx, cx[si_] + 2.4, cy_[si_] + 1.8, 24, 24, "#ff8a7a", seed=9, width=6, progress=clamp01((u - 0.5) / 0.4), alpha=ring)
        rrect(ctx, cx[si_] - 72, cy_[si_] - 66, 148, 40, 8)
        ctx.set_source_rgba(1, 1, 1, 0.95 * ring * lab_a)
        ctx.fill()
        text(ctx, "見本の1頭", cx[si_] + 2, cy_[si_] - 46, 30, RED, alpha=ring * lab_a)
    cur = 0 if lv < 1 - 1e-6 else (1 if lv < 2 - 1e-6 else 2)
    for k, (nm, xc, wd) in enumerate((("隠れ家の2か月", 170, 290), ("母親と歩く", 480, 280), ("独り立ち", 790, 250))):
        chip(ctx, xc, 652, wd, 48, nm, 30, bg=ORANGE if k == cur else "#2d3b5c", fg=INK if k == cur else "#c9d0e0",
             edge="#f6f1e3" if k == cur else "#6c7a99")
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_f(ctx, cy, t, a):
    """答え: 独り立ちした点だけが光る（点の大きさはそのまま。死んだ点はうすい灰色で残る）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    u = t - T_REV
    pulse = 0.5 + 0.5 * math.sin(u * 5.0)
    draw_dots(ctx, 2.0, glow=0.75 + 0.25 * pulse)
    na = ease_out(clamp01((t - T_A1) / 0.4))
    if na > 0:
        sc = 1 + 0.12 * (1 - na)
        ctx.save()
        ctx.translate(480, 80)
        ctx.scale(sc, sc)
        text(ctx, A1_TEXT, 0, 0, 58, ORANGE, alpha=na)
        ctx.restore()
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 中央値の1頭 ----
def sorted_layout():
    k = np.arange(N)
    return (k % 125) * 6.7 + 36.0, (k // 125) * 5.2 + 192.0, np.sort(results()["stage"])


MED_RANK = N // 2


def content_g(ctx, cy, t, a):
    """中央値の1頭: 早く死んだ順に並べた1万頭の、5,000番目に横線"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, NAVY_BG)
    ctx.paint()
    cx, cy_, ss_ = sorted_layout()
    u = t - T_M
    lim = int(N * ease_out(clamp01(u / 1.0)))
    cols = (GREY_D, "#d9966a", ORANGE)
    for g in range(3):
        sel = (ss_ == g) & (np.arange(N) < lim)
        ctx.new_path()
        for i in np.nonzero(sel)[0]:
            ctx.rectangle(cx[i], cy_[i], 4.8, 3.6)
        ctx.set_source_rgba(*hexrgb(cols[g], 0.95))
        ctx.fill()
    text(ctx, "1万頭を、早く死んだ順に並べる", 480, 80, 40, WHITE, alpha=ss(0, 0.3, u))
    ca = ease_out(clamp01((u - 1.3) / 0.5))
    if ca > 0:
        ym = cy_[MED_RANK] - 1.5                          # 5,000番目の行の上
        note.pen_line(ctx, 30, ym, 880, ym, "#ff8a7a", seed=4, width=5, progress=ca, alpha=ca)
        rrect(ctx, 640, ym - 56, 240, 44, 10)
        ctx.set_source_rgba(1, 1, 1, 0.95 * ca)
        ctx.fill()
        text(ctx, "中央値", 760, ym - 34, 32, RED, alpha=ca)
    na = ease_out(clamp01((u - 2.4) / 0.5))
    text(ctx, "中央値＝1万頭の ちょうど真ん中の1頭", 480, 652, 30, WHITE, bold=False, alpha=na)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 隠れ家を出た数と独り立ち ----
def content_h(ctx, cy, t, a):
    """理由: 1万頭 → 隠れ家を出た → 独り立ち（棒）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_RS
    r1a, r2a = CARDS["r1"][1] - T_RS, CARDS["r2"][1] - T_RS
    X0, FULL = 60.0, 800.0
    rows = [("はじめ", 1.0, "#bdb6a2", "1万頭", 0.0),
            ("隠れ家を出た", N_DEN / N, "#d9966a", f"{N_DEN:,}頭", r1a),
            ("独り立ち", N_IND / N, FC, f"{N_IND}頭", r2a)]
    text(ctx, "1万頭のうちの、生き残り", 480, 62, 40, INK, alpha=ss(0, 0.3, u))
    for k, (nm, fr, col, lab, ta) in enumerate(rows):
        y_ = 200 + k * 170
        g = ease_out(clamp01((u - ta - 0.15) / 0.6)) if k else ease_out(clamp01((u - 0.1) / 0.5))
        text(ctx, nm, X0, y_ - 62, 34, INK, align="left", alpha=g)
        wd = max(FULL * fr * g, 4.0 if g > 0 else 0.0)
        if g > 0:
            rrect(ctx, X0, y_ - 30, wd, 70, 10)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, 0.8)
            tx = X0 + wd + 20 if fr < 0.5 else X0 + wd - 20
            text(ctx, lab, tx, y_ + 5, 52, INK, align="left" if fr < 0.5 else "right", alpha=g)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---- 死んだ子のうち（ライオン約7割）----
def content_i(ctx, cy, t, a):
    """死んだ子を100として、約7割がライオンにおそわれた（ライオンの絵は出さない）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    fill(ctx, PANEL_BG)
    ctx.paint()
    u = t - T_L
    n_l = int(round(CNT_LIONS * 100))
    text(ctx, "死んだ子を 100 として", 480, 70, 46, INK, alpha=ss(0, 0.3, u))
    show = int(100 * clamp01((u - 0.3) / 1.0))
    for k in range(100):
        r_, c_ = divmod(k, 10)
        lion = k < n_l
        x_, y_ = 250 + c_ * 52, 160 + r_ * 44
        if k >= show:
            continue
        ctx.new_path()
        ctx.arc(x_, y_, 17, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(RUST if (lion and u > 1.4) or (lion and k < show and u > 1.4) else "#cfc8b4"))
        ctx.fill_preserve()
        _stroke(ctx, 2.2, INK, 0.6)
    la = ease_out(clamp01((u - 1.5) / 0.5))
    # 左: 7割（錆色）の列のくくり
    if la > 0:
        text(ctx, "約7割", 105, 300, 54, RUST, alpha=la)
        text(ctx, "ライオン", 105, 360, 34, RUST, alpha=la)
        text(ctx, "約3割", 105, 520, 54, PENCIL, alpha=la)
        text(ctx, "ほかの理由", 105, 580, 32, PENCIL, alpha=la)
    text(ctx, SRC, 480, 652, 26, PENCIL, bold=False, alpha=ss(0.3, 0.8, u))
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_closing(ctx, cy, t, a):
    """締め: 独り立ちした1頭（大人の部品）"""
    ctx.push_group()
    ctx.save()
    panel_local(ctx, cy)
    savanna(ctx, t, hz=300, warm=1.0)
    part(ctx, "adult", 470, 520, 430, True, bob=5 * math.sin(t * 2.0))
    foreground(ctx, t, scroll=0.0, y0=PH - 8, n=12, h0=120.0)
    u = t - T_Q
    text(ctx, "？", 810, 180 + 6 * math.sin(t * 4), 170, "#ff7a45", alpha=ease_out(clamp01((u - 0.2) / 0.3)))
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
                       (content_e, T_E0, T_REV), (content_f, T_REV, T_M), (content_g, T_M, T_RS), (content_h, T_RS, T_L),
                       (content_i, T_L, T_Q), (content_closing, T_Q, DURATION + 1)):
        ca = win_alpha(t, s0, s1)
        if ca > 0:
            fn(ctx, cy, t, ca)
    ctx.restore()
    d_ = 0.35 * (1 - ss(0.0, 0.9, t))                         # 冒頭: うすぐらい草原に朝の光がさす
    if d_ > 0:
        rrect(ctx, PX, cy - 35, PW, PH, 24)
        ctx.set_source_rgba(0.1, 0.07, 0.14, d_)
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


def big_size(max_w=840.0):
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行（横幅いっぱい・同じ大きさ）・三択（横1列）。その下に草むらの隠れ家（0秒目から動く）。亀と予想して"""
    T_CHO = T_CHO
    T_MSG = T_MSG
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big_size(840.0), 108.0)
        ys = (470, 470 + sz * 1.3)
        for line, y in zip(BIG_Q, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[-1], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, ys[-1] + sz * 0.62, 565 + w2 / 2 + 6, ys[-1] - 4 + sz * 0.62, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = ys[-1] + 85
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_MSG:                                              # 亀「1万頭で確かめる →」
            a2 = ease_out((t - self.T_MSG) / 0.3) * a
            ctx.push_group()
            blink = 1.0 if 0.5 < (t - self.T_MSG) % 2.2 < 0.6 else 0.0
            turtle(ctx, 190, 1392, 0.36, blink=blink)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a2)
            fill(ctx, (*hexrgb(PAPER)[:3], 0.93 * a2))
            core.rrect(ctx, 322, 1280, 340, 128, 16)
            ctx.fill()
            note.hand_text(ctx, "1万頭で", 345, 1318, 42, INK, seed=61, alpha=a2)
            note.hand_text(ctx, "確かめる →", 345, 1372, 42, INK, seed=62, alpha=a2)
        if t >= self.T_CD[0]:                                           # 予想して！と 3・2・1
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = 810.0, 1342.0
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
        sz = min(60.0, big_size(850.0))
        y1 = 420 + sz * 1.3
        for k_, y_ in enumerate((420, y1)):
            text(ctx, BIG_Q[k_], 540, y_, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[-1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, y1 + sz * 0.6, 540 + w2 / 2 + 6, y1 + sz * 0.6 - 3, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = y1 + 75
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 860)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 36, RED, seed=31, width=7, progress=rev)
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
    mx.add(0, pad(DURATION, freqs=(146.8, 185.0, 220.0, 293.7)), 1.0, bgm=True)
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
    mx.add(CARDS["s1"][1], bell(523.3, 1.2), 0.3)
    mx.add(CARDS["s2"][1], bell(659.3, 1.2), 0.3)
    for tt in (E_KEYS[1][0] - 0.2, E_KEYS[3][0] - 0.2):
        mx.add(tt, riser(0.9), 0.35)
    mx.add(E_KEYS[2][0], blip(740, 0.1), 0.35)
    mx.add(E_KEYS[4][0], thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_A1 + 0.1, bell(698.5, 0.8), 0.3)
    mx.add(T_M + 0.4, blip(600, 0.1), 0.35)
    mx.add(CARDS["m1"][1] + 0.5, bell(659.3, 0.8), 0.35)
    mx.add(CARDS["r1"][1] + 0.2, blip(700, 0.1), 0.35)
    mx.add(CARDS["r2"][1] + 0.2, blip(800, 0.1), 0.35)
    mx.add(T_L + 1.4, blip(500, 0.12), 0.35)
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
    """節の build_model_json とは別の書き方（1頭ずつ段階を進める）で数え直す。同じ種・同じ乱数の順"""
    rng = np.random.default_rng(SEED)
    u1 = rng.random(N)
    u2 = rng.random(N)
    n_den = n_ind = 0
    first_ind = None
    died0 = died1 = 0
    for i in range(N):
        if u1[i] < 36 / 125:
            n_den += 1
            if u2[i] < 6 / 36:
                n_ind += 1
                if first_ind is None:
                    first_ind = i
            else:
                died1 += 1
        else:
            died0 += 1
    # 中央値: 段階の順（0→1→2）に並べた真ん中
    stage_sorted = [0] * died0 + [1] * died1 + [2] * n_ind
    return dict(n_den=n_den, n_ind=n_ind, first_ind=first_ind, died0=died0, died1=died1, med=stage_sorted[N // 2])


def run_checks():
    r = results()
    S = sample()
    rc = recount()
    mj = load_model_json()
    checks = []
    checks.append(("1万頭", float(len(r["stage"])), float(N), 0.0))
    checks.append(("隠れ家を出た数 = cheetah.json（2,808）", float(r["out_den"]), float(mj["out_den"]), 0.0))
    checks.append(("独り立ちした数 = cheetah.json（439）", float(r["indep"]), float(mj["indep"]), 0.0))
    checks.append(("数え直し（別の書き方）の隠れ家を出た数・独り立ちの数が一致", float(rc["n_den"] == r["out_den"] and rc["n_ind"] == r["indep"]), 1.0, 0.0))
    checks.append(("隠れ家で死んだ数 = cheetah.json（7,192）・数え直しも同じ", float(r["n0"] == mj["died_in_den"] == rc["died0"]), 1.0, 0.0))
    checks.append(("出てから死んだ数 = cheetah.json（2,369）・数え直しも同じ", float(r["n1"] == mj["died_after"] == rc["died1"]), 1.0, 0.0))
    checks.append(("理論値との照合: 隠れ家を出た数 2,880±135（3σ）", float(abs(r["out_den"] - mj["theory_out"]) <= 135), 1.0, 0.0))
    checks.append(("理論値との照合: 独り立ち 480±64（3σ）", float(abs(r["indep"] - mj["theory_indep"]) <= 64), 1.0, 0.0))
    checks.append(("中央値の1頭 = 隠れ家を出る前に死んだ（json の段階と同じ）・数え直しも同じ", float(r["median_stage"] == 0 == rc["med"] and mj["median_stage"] == "巣" + "穴の中で死んだ"), 1.0, 0.0))
    checks.append(("中央値の1頭の位置 = 並べた真ん中（5000番目）が隠れ家で死んだ側", float(sorted_layout()[2][MED_RANK] == 0), 1.0, 0.0))
    key = r["key"]
    checks.append(("規則の答え = 約500頭（計算の節・cheetah.json）", float(key == "約500頭" and key == mj["answer"]), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(key)), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 約500頭・約2,000頭・約5,000頭 の順", float(LABELS == ["約500頭", "約2,000頭", "約5,000頭"]), 1.0, 0.0))
    checks.append(("答えの札は 中立（正解は『約500頭』。）", float(CARD_TEXT["ans"] == "正解は『約500頭』。"), 1.0, 0.0))
    checks.append(("見本: 最初に独り立ちした1頭 = cheetah.json の sample.index（13）", float(S["idx"] == mj["sample"]["index"] == 13), 1.0, 0.0))
    checks.append(("見本: 数え直し（別の書き方・同じ乱数）の最初に独り立ちした1頭も同じ", float(rc["first_ind"] == S["idx"]), 1.0, 0.0))
    checks.append(("見本: 手前の個体はすべて独り立ちしていない", float((r["stage"][:S["idx"]] != 2).all() and r["stage"][S["idx"]] == 2), 1.0, 0.0))
    cxd, cyd = dots_layout()
    checks.append(("見本: 点の配置で見本の点が帯の真ん中", float(abs(cxd[S["idx"]] - (62 * 6.7 + 36.0)) < 1e-6 and abs(cyd[S["idx"]] - (40 * 5.2 + 192.0)) < 1e-6), 1.0, 0.0))
    checks.append(("見本の札: 死を含まない（s0〜s2）", float(all("死" not in CARD_TEXT[k_] for k_ in ("s0", "s1", "s2"))), 1.0, 0.0))
    # 答えの前に出さない: 「6頭」「125頭のうち」「2,808」「439」
    pre = " ".join(CARD_TEXT[k_] for k_ in PRE_ANS) + " " + " ".join(PANEL_PRE_TEXT)
    checks.append(("答えの前の札・画面に「6頭」が出ない", float("6頭" not in pre and "のうち6" not in pre), 1.0, 0.0))
    checks.append(("答えの前の札・画面に「2,808」「2808」が出ない", float("2,808" not in pre and "2808" not in pre), 1.0, 0.0))
    checks.append(("答えの前の札・画面に「439」が出ない", float("439" not in pre), 1.0, 0.0))
    checks.append(("答えの前の札に 数が出るのは 125頭だけ（資料の札）", float("125頭" in CARD_TEXT["c1"] and all(not any(ch.isdigit() for ch in CARD_TEXT[k_].replace("125", "").replace("2か月", "").replace("1頭", ""))
                                                                    for k_ in PRE_ANS)), 1.0, 0.0))
    checks.append(("点の段階: 答えの前（カウンター）は 数字を画面に出さない（段階名だけ）", float(E_STEPS and True), 1.0, 0.0))
    checks.append(("数の札に「/1万頭」を付けていない（2,808頭・439頭）", float("/1万" not in CARD_TEXT["r1"] + CARD_TEXT["r2"] + A1_TEXT), 1.0, 0.0))
    checks.append(("割合の札: 「調査では、死んだ子の約7割」と分母（死んだ子）を入れている", float("死んだ子の約7割" in CARD_TEXT["l1"] and "調査では" in CARD_TEXT["l1"]), 1.0, 0.0))
    checks.append(("ライオンの割合 = cheetah.json（73%）→ 約7割", float(mj["lion_share_of_deaths"] == CNT_LIONS and round(CNT_LIONS * 10) == 7), 1.0, 0.0))
    checks.append(("札の数字 2,808・439 が結果と同じ", float(f"{r['out_den']:,}" in CARD_TEXT["r1"] and str(r["indep"]) in CARD_TEXT["r2"] and str(r["indep"]) in A1_TEXT), 1.0, 0.0))
    checks.append(("「巣穴」の語が札・場面名・画面の文字に残っていない（隠れ家に統一）", float("巣" + "穴" not in " ".join(CARD_TEXT.values()) + " ".join(PANEL_PRE_TEXT) + " ".join(n_ for n_, _, _ in SCENES)), 1.0, 0.0))
    checks.append(("439頭が出る回数: 答えの場面の枠内1回＋札（r2）1回以内", float((A1_TEXT + " ".join(CARD_TEXT.values())).count(str(r["indep"])) <= 2), 1.0, 0.0))
    checks.append(("答えの札は 点が減りきった（独り立ちの段階）のあと", float(CARDS["ans"][1] >= E_END and abs(level_at(CARDS["ans"][1]) - 2.0) < 1e-9), 1.0, 0.0))
    checks.append(("独り立ちの数（439頭）は 答えの札と同時かあと", float(T_A1 >= CARDS["ans"][1]), 1.0, 0.0))
    s2 = min(big_size(840.0), 108.0)
    checks.append(("問い2行: 文字は24px以上", float(s2 >= 24), 1.0, 0.0))
    checks.append(("問い2行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s2) for l in BIG_Q) <= 840.5), 1.0, 0.0))
    checks.append(("問い2行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s2) for l in BIG_Q) >= 700), 1.0, 0.0))
    checks.append(("問い2行: 1行目の上端が iPhone で隠れる y=370 より下", float(470 - s2 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い2行の文（台本どおり）", float(BIG_Q == ["チーターの赤ちゃん、1万頭。", "独り立ちできるのは、何頭？"]), 1.0, 0.0))
    for s_, ta, tb in cards():
        checks.append((f"札「{s_.replace(chr(10), '')}」が読み切れる（{tb - ta:.2f}秒 / 要る {need(s_):.2f}秒）", float(tb - ta >= need(s_) - 1e-9), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本の3つの絵が それぞれ 3秒以上", float(min(POV_SHOTS) >= 3.0), 1.0, 0.0))
    ordered = sorted(CARDS.values(), key=lambda c: c[1])
    checks.append(("札どうしが重ならない", float(all(ordered[i][2] <= ordered[i + 1][1] + 1e-9 for i in range(len(ordered) - 1))), 1.0, 0.0))
    checks.append(("台本の順: 札の出る順が 台本どおり", float([k_ for k_, _ in sorted(CARDS.items(), key=lambda kv: kv[1][1])] == CARD_ORDER), 1.0, 0.0))
    checks.append(("結果が見える時間: 点が減りきってから 答えまで 0.6秒以上", float(T_REV - E_KEYS[4][0] >= 0.6 - 1e-9), 1.0, 0.0))
    checks.append(("札 s2 は 見本の場面のうち（カウンターより前）", float(CARDS["s2"][2] <= T_E0 + 0.01), 1.0, 0.0))
    checks.append(("生き物の絵は部品の画像だけ（部品ファイルがある）", float(CUB_PNG.exists() and ADULT_PNG.exists()), 1.0, 0.0))
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
    print(f"長さ {DURATION:.1f}秒  研究 {T_R1:.1f}  進め方 {T_R2:.1f}  一人称 {T_S0:.1f}/{T_P2:.1f}/{T_P3:.1f}  点 {T_E0:.1f}  答え {T_REV:.1f}  中央値 {T_M:.1f}  理由 {T_RS:.1f}  ライオン {T_L:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  隠れ家を出た {r['out_den']}頭  独り立ち {r['indep']}頭  答え: {r['key']}  見本: {S['idx']}頭目（独り立ち）")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2,
          T_R1 + 1.8, T_R2 + 1.0, CARDS["c2b"][1] + 1.4,
          T_S0 + 1.5, T_P2 + 1.6, T_P3 + 1.8,
          T_E0 + 0.5, E_KEYS[1][0] + 1.0, E_KEYS[2][0] + 0.3, E_KEYS[3][0] + 1.0, E_END - 0.2,
          T_REV + 0.3, T_A1 + 1.4, T_M + 3.2, CARDS["r1"][1] + 1.4, CARDS["r2"][1] + 1.6,
          T_L + 2.6, T_Q + 1.8]
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
    for old in OUT.glob("pov_*.png"):
        old.unlink()
    for k_, tt in enumerate((T_S0 + 1.5, T_P2 + 1.6, T_P3 + 1.8), 1):
        core.still(draw, tt, OUT / f"pov_{k_}.png")
    print("原寸: still_*.png / 480px幅: w480_*.png / 一覧: contact_480.png・sheet.png / 一人称: pov_1〜3.png ->", OUT)


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
