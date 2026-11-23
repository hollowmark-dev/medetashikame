"""麻雀の配牌、対子が4つ。七対子を狙う？ふつうの手を狙う？ 1万局で比べる。— 2026-11-08 作成（公開予定 11.23・ナレーションなし・60秒未満）

計算の本体は sims/chiitoi_model.py（配牌の条件・捨て方・18巡・seed 161・答えの決め方は、計算の前にそのファイルの docstring に固定してある。ここでは変えない）。
この sim は「結果を読んで絵にする」ところ。1万局の配列は out/chiitoi-nerau/cache/ に置く（再実行を速くする）。結果は out/models_1120/chiitoi{3,4,5}.json と照合する。

【置き方】（chiitoi_model.py の docstring と同じ。結果を見て変えていない）
  配牌13枚: 対子がちょうど4組（3枚同じ牌なし）。1人で18巡まで 引いて捨てる。鳴きなし。
  七対子の人は七対子の向聴数、ふつうの手の人はふつうの手の向聴数が いちばん少なくなる牌を捨てる（同じなら くじ）。配牌と山は両者で同じ。
【答えの決め方】（answer_by_rule。計算の前に固定）
  18巡までにテンパイする回の割合が 2ポイント以上高いほうが正解。差がそれより小さければ「ほぼ同じ」。
【見本の1局】 1万局の最初の1局そのもの（seed 161 の1局目。同じ乱数で引き直し、毎巡の「引いた牌・捨てた牌・向聴数」を取り出す）。run_checks で chiitoi_model.play と一致を確かめる。
【ひねり】 対子3つ・5つの配牌も、同じ計算（chiitoi_model.run 相当）。数字は out/models_1120/chiitoi3.json・chiitoi5.json と一致を確かめる。
【言い方】 「中央値」「計算での見立て」は出さない（牌のルールで決まるため）。

問い: 「麻雀の配牌。対子が4つ。/ 七対子を狙う？/ ふつうの手を狙う？」
選択肢: A 七対子 ／ B ほぼ同じ ／ C ふつうの手（正解の記号は A。run_checks で確かめる）
見せ方: 冒頭（配牌が並ぶ・対子が4つ）→ 対子・七対子 → ふつうの手 → テンパイ・向聴 → 比べ方（同じ配牌の2人）→ 見本の1局 → 1万局 → 答え → 理由 → ひねり → 締め
締め: 「対子が4つの配牌、あなたはどちらを狙いますか？」
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import chiitoi_model as mm  # noqa: E402

SLUG = "chiitoi-nerau"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
CACHE = OUT / "cache"
JSON_DIR = ROOT / "out" / "models_1120"
N_TRIAL = mm.R
MAXD = mm.MAXD
SEED = 161
NONE = 99                                           # テンパイしなかった回の印（配列の中）
CNT = 2.0                                           # 1万局の数え上げの秒数
BAR_MAX = 5000.0                                    # 棒の高さの目盛り（0〜5,000回。ゼロから始める）


def answer_by_rule(c_rate, n_rate):
    """答えの決め方（計算の前に固定）。18巡までにテンパイする割合が 2ポイント以上高いほう／差が小さければ ほぼ同じ"""
    d = c_rate - n_rate
    if d >= 0.02:
        return "七対子"
    if d <= -0.02:
        return "ふつうの手"
    return "ほぼ同じ"


def pct0(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


def trace_play(hand, wall, f, rng):
    """chiitoi_model.play と同じ手順・同じ乱数の使い方で、毎巡の (引いた牌, 捨てた牌, 捨てたあとの向聴数, 捨てたあとの手) を記録する"""
    hand = list(hand)
    tr = []
    if f(hand) == 0:
        return 0, tr
    for d in range(1, MAXD + 1):
        dr = wall[d - 1]
        hand[dr] += 1
        best = None
        cands = []
        for i in range(34):
            if hand[i]:
                hand[i] -= 1
                s = f(hand)
                hand[i] += 1
                if best is None or s < best:
                    best, cands = s, [i]
                elif s == best:
                    cands.append(i)
        dis = cands[rng.integers(len(cands))]
        hand[dis] -= 1
        tr.append((int(dr), int(dis), int(best), [k for k in range(34) for _ in range(hand[k])]))
        if best == 0:
            return d, tr
    return None, tr


def run_arrays(n_pairs, seed=SEED, n=N_TRIAL):
    """chiitoi_model.run と同じ手順で 1万局を回し、局ごとのテンパイ巡目（なければ 99）を配列で返す。cache に置く"""
    p = CACHE / f"arr{n_pairs}.npz"
    if p.exists():
        z = np.load(p)
        return z["a"], z["b"]
    rng = np.random.default_rng(seed)
    a = []
    b = []
    for _ in range(n):
        hand, wall = mm.deal(rng, n_pairs)
        s = int(rng.integers(1 << 30))
        x = mm.play(hand, wall, mm.chiitoi_sh, np.random.default_rng(s))
        y = mm.play(hand, wall, mm.normal_sh, np.random.default_rng(s))
        a.append(NONE if x is None else x)
        b.append(NONE if y is None else y)
    a = np.array(a, np.int16)
    b = np.array(b, np.int16)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(p, a=a, b=b)
    return a, b


def summarize(a, b):
    n = len(a)
    ok_a, ok_b = a <= MAXD, b <= MAXD
    return dict(c_n=int(ok_a.sum()), n_n=int(ok_b.sum()), c_rate=float(ok_a.mean()), n_rate=float(ok_b.mean()),
                c_med=float(np.median(a[ok_a])) if ok_a.any() else None, n_med=float(np.median(b[ok_b])) if ok_b.any() else None,
                c_faster=float((a < b).mean()), n_faster=float((b < a).mean()), n=n)


_RES = {}


def results():
    """1万局の結果（対子4つ=今回／3つ・5つ=ひねり）・見本の1局"""
    if _RES:
        return _RES["r"]
    arr = {k: run_arrays(k) for k in (3, 4, 5)}
    sm = {k: summarize(*arr[k]) for k in arr}
    js = {k: json.loads((JSON_DIR / f"chiitoi{k}.json").read_text(encoding="utf-8"))[f"pairs{k}"] for k in (3, 4, 5)}
    a4, b4 = arr[4]
    # 見本の1局: 1万局の最初の1局（seed 161）
    rng = np.random.default_rng(SEED)
    hand, wall = mm.deal(rng, 4)
    s = int(rng.integers(1 << 30))
    ra, tra = trace_play(hand, wall, mm.chiitoi_sh, np.random.default_rng(s))
    rb, trb = trace_play(hand, wall, mm.normal_sh, np.random.default_rng(s))
    hand_sorted = [k for k in range(34) for _ in range(hand[k])]
    cum_a = np.cumsum(a4 <= MAXD)
    cum_b = np.cumsum(b4 <= MAXD)
    r = dict(arr=arr, sm=sm, js=js, hand=hand, wall=wall, hand_sorted=hand_sorted, ra=ra, rb=rb, tra=tra, trb=trb,
             sh0=(mm.chiitoi_sh(hand), mm.normal_sh(hand)), first=(int(a4[0]), int(b4[0])), cum_a=cum_a, cum_b=cum_b)
    r["key"] = answer_by_rule(sm[4]["c_rate"], sm[4]["n_rate"])
    _RES["r"] = r
    return r


# ---- 言葉の札の例（牌のルールに合う形。run_checks で model の関数で確かめる） ----
EX_PAIR = [13, 13]                                                    # 五筒の対子
EX_CHII = [1, 1, 6, 6, 11, 11, 16, 16, 21, 21, 27, 27, 33, 33]       # 七対子: 7種類のちがう対子（二萬・七萬・三筒・八筒・四索・東・中）
EX_NORM_SETS = [[0, 1, 2], [12, 13, 14], [24, 25, 26], [33, 33, 33]]  # 順子3つ（一二三萬・四五六筒・七八九索）と刻子（中中中）
EX_NORM_HEAD = [27, 27]                                               # 雀頭（東東）
EX_TENPAI = [0, 1, 2, 12, 13, 14, 24, 25, 26, 27, 33, 33, 33]         # 13枚。東を引けば上がり（東東が雀頭になる）
EX_TENPAI_WAIT = 27
EX_SHANTEN = [0, 1, 2, 12, 13, 14, 24, 25, 26, 27, 31, 33, 33]        # 13枚。1向聴: 白を捨てて東を引けば 東東・中中でテンパイ
EX_SHANTEN_DROP = 31                                                  # 白
EX_SHANTEN_DRAW = 27                                                  # 東

# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    OUT.mkdir(parents=True, exist_ok=True)
    r = results()
    for k in (3, 4, 5):
        s_ = r["sm"][k]
        print(f"対子{k}つ: 七対子 {s_['c_n']:,}回({s_['c_rate']:.1%}) ふつうの手 {s_['n_n']:,}回({s_['n_rate']:.1%})  巡目の中央値(テンパイした局) {s_['c_med']}/{s_['n_med']}"
              f"  七対子が早い {s_['c_faster']:.1%} ふつうが早い {s_['n_faster']:.1%}")
    print(f"答え: {r['key']}")
    print(f"見本の1局: 配牌 {r['hand_sorted']}  向聴(七対子/ふつう) {r['sh0']}  テンパイ巡目 {r['ra']}/{r['rb']}  毎巡の向聴 七対子{[t[2] for t in r['tra']]} ふつう{[t[2] for t in r['trb']]}")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, whoosh)
from engine.parts import loop_back, stills  # noqa: E402
import mj_tiles as mj  # noqa: E402
from mj_tiles import draw_tile  # noqa: E402

note.use()
note.DATE = "11.23"                                  # 日付欄（公開予定日）

ORG, ORG_D = "#e0801f", "#a85a0a"                    # 七対子（橙）
BLU, BLU_D = "#3f7fb5", "#2a5a85"                    # ふつうの手（青）
FELT, FELT_D = "#2f7a5c", "#1f5a42"                  # 卓の緑
GOLD = "#ffd54a"
GRY, GRY_D = "#a9a395", "#6f695b"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は A（1番目）
LABELS = ["七対子", "ほぼ同じ", "ふつうの手"]
KEY_LABEL = {"七対子": "七対子", "ほぼ同じ": "ほぼ同じ", "ふつうの手": "ふつうの手"}
CORRECT = 0

BIG_Q3 = ["麻雀の配牌。対子が4つ。", "七対子を狙う？", "ふつうの手を狙う？"]      # 1コマ目の3行（同じ大きさ）
BIG_Q = ["麻雀の配牌。対子が4つ。", "七対子を狙う？ふつうの手を狙う？"]            # 定位置（上）の2行
DETAIL_RULE = "配牌は同じ。目指す手だけがちがう"
DETAIL = "コンピューターで1万局くり返して確かめる"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (1.8, 2.6, 3.4)                              # 3・2・1
T_MOVE, T_GO = 4.3, 4.7
SX = 570.0                                          # 付箋の中心 x
HX = 555.0                                          # 牌の列の中心 x


def setup():
    global T_W1, T_W2, T_W3, T_CMP, T_S, T_H0, T_HC, T_REV, T_RS, T_TW, T_Q, DURATION, SCENES
    T_W1 = T_GO                                     # 対子・七対子
    T_W2 = T_W1 + 5.8                               # ふつうの手
    T_W3 = T_W2 + 4.2                               # テンパイ・向聴
    T_CMP = T_W3 + 6.2                              # 比べ方（同じ配牌の2人）
    T_S = T_CMP + 5.8                               # 見本の1局
    T_H0 = T_S + 8.3                                # 1万局
    T_HC = T_H0 + 0.5                               # 数え上げ始め
    T_REV = T_H0 + 5.0                              # 答え
    T_RS = T_REV + 4.2                              # 理由
    T_TW = T_RS + 4.8                               # ひねり（対子3つ・5つ）
    T_Q = T_TW + 6.2                                # 締め
    DURATION = T_Q + 3.3
    SCENES = [("冒頭（配牌が並ぶ・対子が4つ）", 0.0, T_GO), ("対子・七対子", T_W1, T_W2), ("ふつうの手", T_W2, T_W3), ("テンパイ・向聴", T_W3, T_CMP),
              ("比べ方（同じ配牌の2人）", T_CMP, T_S), ("見本の1局", T_S, T_H0), ("1万局", T_H0, T_REV), ("答え", T_REV, T_RS),
              ("理由", T_RS, T_TW), ("ひねり（対子3つ・5つ）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()

DT = 0.22                                           # 見本: 1巡の秒数
U_STEP0 = 0.7                                       # 見本: 巡が始まる秒


def twist_texts():
    r = results()
    s3, s5 = r["sm"][3], r["sm"][5]
    return (f"対子が3つだと逆になる。\nふつうの手{pct0(s3['n_rate'])}・七対子{pct0(s3['c_rate'])}。",
            f"対子が5つなら、\n七対子{pct0(s5['c_rate'])}・ふつうの手{pct0(s5['n_rate'])}。")


def answer_sub():
    s4 = results()["sm"][4]
    return f"18巡までにテンパイしたのは\n七対子{pct0(s4['c_rate'])}、ふつうの手{pct0(s4['n_rate'])}。"


# 付箋: (文, 場面の始まり, 出る秒, 消える秒, y, 色, 大きさ)
def card_defs():
    tw1, tw2 = twist_texts()
    return [
        ("対子（トイツ）\n＝同じ牌が2枚", T_W1, 0.2, 2.6, 1330, "yellow", 40),
        ("七対子（チートイツ）\n＝対子を7つ集める手", T_W1, 2.7, 5.6, 1330, "pink", 40),
        ("ふつうの手＝\n3枚の組を4つと、\n対子を1つ集める手", T_W2, 0.3, 4.0, 1330, "mint", 38),
        ("テンパイ\n＝あと1枚で上がれる形", T_W3, 0.2, 3.2, 1330, "yellow", 40),
        ("向聴（シャンテン）\n＝テンパイまで、\nあと何枚入れ替えるか", T_W3, 3.3, 6.0, 1330, "pink", 38),
        ("1枚引いて、1枚捨てる。\n18回まで。", T_CMP, 0.3, 5.5, 1215, "yellow", 38),
        ("捨てるのは、テンパイまでの残り\n（向聴）がいちばん少なくなる牌。", T_CMP, 1.7, 5.5, 1370, "pink", 38),
        ("たとえば、この1回では\n同じ山から、同じ牌を引く。", T_S, 0.2, 2.9, 1330, "yellow", 40),
        ("どちらも18巡までに\nテンパイできなかった。", T_S, 4.9, 8.2, 1245, "pink", 42),
        ("1局だけでは決まらない。\nだから1万局で比べる。", T_S, 5.6, 8.2, 1392, "mint", 38),
        ("対子が4つあれば、\n七対子はあと3組でいい。", T_RS, 0.3, 4.6, 1215, "yellow", 42),
        ("ふつうの手は、\n3枚の組をいくつも作る。", T_RS, 2.0, 4.6, 1375, "pink", 42),
        (tw1, T_TW, 0.3, 6.0, 1245, "yellow", 42),
        (tw2, T_TW, 2.5, 6.0, 1385, "mint", 42),
        (answer_sub(), T_REV, 0.7, 4.1, 1370, "yellow", 36),
        ("対子が4つの配牌、\nあなたはどちらを\n狙いますか？", T_Q, 0.3, None, 790, "yellow", 52),
    ]


def cards():
    """札: (1行の文, 出る秒, 消える秒)。1行ごとに「1文字0.12秒＋1秒以上」と 公開前チェックの「0.5秒＋文字数÷6秒」の両方より長く映す"""
    out = []
    for s, t0, a, b, _y, _c, _z in card_defs():
        for ln in s.split("\n"):
            out.append((ln, t0 + a, t0 + (b if b is not None else DURATION - t0 - 0.2)))
    out.append(("正解は『七対子』。", T_REV + 0.2, T_RS - 0.1))
    return out


# ---------- 絵: 共通 ----------
def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def thick(ctx, pts_, w, col, outline=2.6):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts_):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


def ik_out(sx, sy, wx, wy, l1, l2, side):
    dx, dy = wx - sx, wy - sy
    dd = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 2.0, math.hypot(dx, dy)))
    a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd)
    hh = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    bx, by = sx + a * ux, sy + a * uy
    c1 = (bx - hh * uy, by + hh * ux)
    c2 = (bx + hh * uy, by - hh * ux)
    return c1 if side * c1[0] >= side * c2[0] else c2


# ---------- 絵: 生徒（制服の男子・正面。janken-issei の描き方。同じ服で、髪だけ違う） ----------
BLAZER, BLAZER_D, SHIRT, PANTS, TIE, SHOE, SKIN = "#34456a", "#283657", "#f6f3ea", "#3d4560", "#c4414b", "#2a2f3d", "#f7d9bd"
STU = [dict(hair="#2b2b33", style="short"), dict(hair="#6a4a33", style="spiky")]


def student(ctx, x, fy, k, ci, t, look, mouth=0.0):
    """机にむかう生徒。(x, fy) は足もとの中心（机に隠れる）、身長は 100·k px。look = +1 なら右、−1 なら左（内側）を見る"""
    S = STU[ci % len(STU)]
    hs = look
    P = lambda dx, dy: (x + dx * k, fy + dy * k)    # noqa: E731
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    lw = max(2.2, 0.75 * k)

    def poly(pts_, col, w=None):
        ctx.new_path()
        for i, (px, py) in enumerate(pts_):
            (ctx.move_to if i == 0 else ctx.line_to)(*P(px, py))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, w or lw, INK, 0.9)

    for dx in (-7.2, 7.2):                                                     # 脚（机の下。ふちから少し見える）
        thick(ctx, [P(dx, -46), P(dx, -6)], 13.0 * k, PANTS, 2.4)
    # 手を出さないほうのうで（体の横に下ろす→机の上）
    sx0, sy0 = P(-hs * 16.0, -73.0)
    wx0, wy0 = P(-hs * 17.0, -43.0)
    thick(ctx, [(sx0, sy0), P(-hs * 19.5, -58), (wx0, wy0)], 7.6 * k, BLAZER, 2.4)
    ctx.new_path()
    ctx.arc(wx0, wy0 + 1.5 * k, 3.9 * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    # ブレザー
    ctx.new_path()
    ctx.move_to(*P(-9, -80.5))
    ctx.curve_to(*P(-14, -79.5), *P(-18.5, -78.5), *P(-18.3, -71))
    ctx.line_to(*P(-15.6, -43))
    ctx.line_to(*P(15.6, -43))
    ctx.line_to(*P(18.3, -71))
    ctx.curve_to(*P(18.5, -78.5), *P(14, -79.5), *P(9, -80.5))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(BLAZER))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    poly([(-5.8, -80.5), (0, -63), (5.8, -80.5)], SHIRT, lw * 0.8)
    poly([(-5.8, -80.5), (-10.2, -68), (-3.6, -60.5), (0, -63)], BLAZER_D, lw * 0.8)
    poly([(5.8, -80.5), (10.2, -68), (3.6, -60.5), (0, -63)], BLAZER_D, lw * 0.8)
    poly([(-1.6, -73), (1.6, -73), (2.1, -57), (0, -54.5), (-2.1, -57)], TIE, lw * 0.7)
    for by_ in (-52.5, -47.0):
        ctx.new_path()
        ctx.arc(*P(0, by_), 0.95 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#e6c35a"))
        ctx.fill()
    # 手を出すほうのうで（机の上におく）
    shx, shy = P(hs * 15.5, -73.0)
    wx, wy = P(hs * 14.0, -43.0)
    elx, ely = ik_out(shx, shy, wx, wy, 14.0 * k, 14.0 * k, hs)
    thick(ctx, [(shx, shy), (elx, ely), (wx, wy)], 7.6 * k, BLAZER, 2.4)
    ctx.new_path()
    ctx.arc(wx, wy + 1.5 * k, 3.9 * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    # 首・頭
    core.rrect(ctx, *P(-3.6, -82), 7.2 * k, 6.5 * k, 2 * k)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    ctx.save()
    nx, ny = P(0, -80)
    ctx.translate(nx, ny)
    ctx.rotate(look * 0.06)
    ctx.translate(-nx, -ny)
    for sg in (-1, 1):
        ctx.new_path()
        ctx.arc(*P(sg * 9.1, -89), 2.2 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.save()
    ctx.translate(*P(0, -89.5))
    ctx.scale(1.0, 1.08)
    ctx.arc(0, 0, 9.1 * k, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    hair = S["hair"]
    ctx.new_path()
    ctx.move_to(*P(-9.6, -88))
    ctx.curve_to(*P(-11.5, -104), *P(11.5, -104), *P(9.6, -88))
    ctx.line_to(*P(9.0, -94))
    ctx.line_to(*P(6.0, -95.8))
    ctx.line_to(*P(2.2, -93.6))
    ctx.line_to(*P(-1.8, -95.8))
    ctx.line_to(*P(-5.4, -93.6))
    ctx.line_to(*P(-8.6, -95.2))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    if S["style"] == "spiky":
        for dx, h_ in ((-5.5, 5.0), (0.0, 6.5), (5.5, 5.0)):
            poly([(dx - 3.2, -99.4), (dx, -99.4 - h_), (dx + 3.2, -99.4)], hair, lw * 0.8)
    blink = (t * 0.9 + ci * 0.7) % 3.4 < 0.12
    for sg in (-1, 1):
        ex, ey = P(sg * 3.5 + look * 1.5, -89.2)
        if blink:
            ctx.move_to(ex - 1.8 * k, ey)
            ctx.line_to(ex + 1.8 * k, ey)
            _stroke(ctx, lw * 0.9, INK, 0.95)
        else:
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(0.78, 1.0)
            ctx.arc(0, 0, 1.9 * k, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()
            ctx.new_path()
            ctx.arc(ex + look * 0.5 * k + 0.45 * k, ey - 0.55 * k, 0.55 * k, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.fill()
        bx, by = P(sg * 3.6 + look * 1.5, -92.3)
        ctx.move_to(bx - 2.0 * k, by + 0.25 * k)
        ctx.line_to(bx + 2.0 * k, by - 0.25 * k)
        _stroke(ctx, lw * 0.8, INK, 0.8)
        ctx.new_path()
        ctx.arc(*P(sg * 6.0 + look * 1.2, -86.1), 1.5 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(1.0, 0.55, 0.55, 0.32)
        ctx.fill()
    mx_, my_ = P(look * 1.3, -84.3)
    if mouth > 0.05:
        ctx.save()
        ctx.translate(mx_, my_)
        ctx.scale(1.0, 0.5 + 0.8 * mouth)
        ctx.arc(0, 0, 1.7 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#b5434b"))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.7, INK, 0.9)
    else:
        ctx.new_path()
        ctx.arc(mx_, my_ - 0.4 * k, 2.2 * k, 0.2 * math.pi, 0.8 * math.pi)
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.restore()
    ctx.restore()



# ---------- 絵: 共通の小道具 ----------
def lerp(a, b, u):
    return a + (b - a) * u


def win(t, a, b, fi=0.3, fo=0.3):
    return clamp01((t - a) / fi) * (1 - clamp01((t - (b - fo)) / fo))


def fit_size(lines, size, maxw=720.0):
    w = max(core.text_width(l, size) for l in lines)
    return size if w <= maxw else size * maxw / w


def stk(ctx, s, cy, size, color="yellow", fg=INK, a=1.0, tilt=-0.015, cx=SX, maxw=720.0):
    """付箋。文字が横に長いときは 幅 maxw に収まる大きさに縮める"""
    if a <= 0:
        return
    sz = fit_size(s.split("\n"), size, maxw)
    note.sticky(ctx, s, cx, cy, sz, color, fg=fg, a=a, tilt=tilt)



def fade(t, ta, tb, f=0.25):
    return clamp01((t - ta) / f) * (1 - clamp01((t - tb) / f))


def grouped(ctx, a, fn, *args):
    if a <= 0:
        return
    ctx.push_group()
    fn(ctx, *args)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)



# ---------- 絵: 牌 ----------
RED_RGB = (0.82, 0.15, 0.18)
ORG_RGB = (0.88, 0.50, 0.12)


def tile_back(ctx, x, y, w):
    s = w / 40.0
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    mj._rrect(ctx, 0.75, 2.6, 38.5, 54.5, 5)
    mj._fill(ctx, (0.62, 0.60, 0.53), 0.55)
    mj._rrect(ctx, 0.75, 0.75, 38.5, 54.5, 5)
    mj._fill(ctx, (0.13, 0.46, 0.40))
    mj._rrect(ctx, 0.75, 0.75, 38.5, 54.5, 5)
    ctx.set_source_rgb(*mj.EDGE)
    ctx.set_line_width(1.3)
    ctx.stroke()
    mj._rrect(ctx, 3.4, 3.4, 33.2, 49.2, 3.6)
    ctx.set_source_rgba(1, 1, 1, 0.35)
    ctx.set_line_width(1.2)
    ctx.stroke()
    ctx.restore()


def flip_tile(ctx, kind, x, y, w, p, alpha=1.0):
    """p=0 で裏、p=1 で表。横にひっくり返る"""
    if alpha <= 0:
        return
    if alpha < 1.0:
        ctx.push_group()
    cx = x + w / 2
    sx = abs(1 - 2 * p) if p < 0.5 else (2 * p - 1)
    ctx.save()
    ctx.translate(cx, 0)
    ctx.scale(max(sx, 0.03), 1.0)
    ctx.translate(-cx, 0)
    if p < 0.5:
        tile_back(ctx, x, y, w)
    else:
        draw_tile(ctx, kind, x, y, w)
    ctx.restore()
    if alpha < 1.0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)


def tile_row(ctx, kinds, x0, y, w, step=None, alpha=1.0, hl=None):
    step = step or (w + 2)
    for i, k in enumerate(kinds):
        draw_tile(ctx, k, x0 + i * step, y, w, alpha=alpha, highlight=(hl or {}).get(i))


def dashed_rrect(ctx, x, y, w, h, rad, col=PENCIL, a=0.8, lw=3.0):
    rrect(ctx, x, y, w, h, rad)
    ctx.set_dash([9, 7])
    _stroke(ctx, lw, col, a)
    ctx.set_dash([])


def felt_panel(ctx, x, y, w, h):
    rrect(ctx, x, y, w, h, 26)
    ctx.set_source_rgba(*hexrgb(FELT))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)


def hand_pairs(hs):
    out = []
    i = 0
    while i < len(hs) - 1:
        if hs[i] == hs[i + 1]:
            out.append(i)
            i += 2
        else:
            i += 1
    return out


def draw_cards(ctx, t, t0):
    """その場面の付箋"""
    for s, ts, a, b, y, col, sz in card_defs():
        if ts != t0 or b is None:
            continue
        stk(ctx, s, y, sz, a=win(t, ts + a, ts + b, 0.3, 0.25), color=col)


# ---------- 絵: 冒頭（配牌が並ぶ・対子が4つ） ----------
DEAL_W, DEAL_STEP, DEAL_Y = 68.0, 70.0, 1170.0


def draw_deal(ctx, t):
    a = 1 - ease(clamp01((t - T_GO) / 0.3)) if t >= T_GO else 1.0
    if a <= 0:
        return
    hs = results()["hand_sorted"]
    wp = ease(clamp01(t / 0.8))                                       # 卓の緑が左から右へ広がる（冒頭の動き）
    ctx.push_group()
    ctx.save()
    ctx.rectangle(0, 1080, 1080 * wp, 390)
    ctx.clip()
    felt_panel(ctx, 12, 1090, 1056, 368)
    ctx.restore()
    x0 = HX - ((len(hs) - 1) * DEAL_STEP + DEAL_W) / 2
    text(ctx, "最初に配られた13枚", HX, 1136, 32, "#ffffff", alpha=ease_out(clamp01((t - 0.3) / 0.3)))
    for i, k in enumerate(hs):
        p = ease_out(clamp01((t - 0.03 * i) / 0.25))
        if p <= 0:
            continue
        fl = clamp01((t - 0.45 - 0.03 * i) / 0.3)
        flip_tile(ctx, k, x0 + i * DEAL_STEP, DEAL_Y - 40 * (1 - p), DEAL_W, fl, alpha=p)
    for j, i in enumerate(hand_pairs(hs)):                            # 対子に金色のかっこ
        q = ease_out(clamp01((t - 1.15 - 0.18 * j) / 0.25))
        if q <= 0:
            continue
        xa, xb = x0 + i * DEAL_STEP, x0 + (i + 1) * DEAL_STEP + DEAL_W
        yb = 1292.0
        ctx.move_to(xa, yb - 12)
        ctx.line_to(xa, yb)
        ctx.line_to(xb, yb)
        ctx.line_to(xb, yb - 12)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        _stroke(ctx, 6, GOLD, q)
        text(ctx, "対子", min((xa + xb) / 2, 890.0), 1330, 34, GOLD, alpha=q)
    q = ease_out(clamp01((t - 2.2) / 0.3))
    text(ctx, "対子が4つ", HX, 1402, 60, "#ffffff", alpha=q)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 絵: 対子・七対子 ----------
def scene_w1(ctx, t):
    u = t - T_W1
    a1 = ease_out(clamp01((u - 0.1) / 0.3)) * (1 - ease(clamp01((u - 2.45) / 0.25)))
    if a1 > 0:
        text(ctx, "対子", HX, 650, 64, INK, alpha=a1)
        for i, k in enumerate(EX_PAIR):
            draw_tile(ctx, k, HX - 153 + i * 156, 720 + 24 * (1 - a1), 150, alpha=a1)
        yb = 975.0
        ctx.move_to(HX - 153, yb - 14)
        ctx.line_to(HX - 153, yb)
        ctx.line_to(HX + 153, yb)
        ctx.line_to(HX + 153, yb - 14)
        _stroke(ctx, 7, RED, a1)
    if u >= 2.7:
        q0 = ease_out(clamp01((u - 2.7) / 0.3))
        text(ctx, "七対子", HX, 650, 64, ORG_D, alpha=q0)
        for n in range(7):
            p = ease_out(clamp01((u - 2.85 - 0.14 * n) / 0.25))
            if p <= 0:
                continue
            row, c = (0, n) if n < 4 else (1, n - 4)
            nrow = 4 if row == 0 else 3
            x0 = HX - (nrow * 162 + (nrow - 1) * 16) / 2
            x = x0 + c * 178
            y = 720 + row * 140 + 20 * (1 - p)
            tile_row(ctx, EX_CHII[2 * n:2 * n + 2], x, y, 80, 82, alpha=p)
        q = ease_out(clamp01((u - 3.5) / 0.3))
        text(ctx, "2枚 × 7組", HX, 1035, 46, INK, alpha=q)
    draw_cards(ctx, t, T_W1)


# ---------- 絵: ふつうの手 ----------
def scene_w2(ctx, t):
    u = t - T_W2
    text(ctx, "ふつうの手", HX, 650, 64, BLU_D, alpha=ease_out(clamp01(u / 0.3)))
    w, st = 72.0, 74.0
    groups = [(EX_NORM_SETS[0], 0, 0), (EX_NORM_SETS[1], 1, 0), (EX_NORM_SETS[2], 2, 0), (EX_NORM_SETS[3], 0, 1), (EX_NORM_HEAD, 1, 1)]
    for n, (g, c, row) in enumerate(groups):
        p = ease_out(clamp01((u - 0.3 - 0.28 * n) / 0.25))
        if p <= 0:
            continue
        head = len(g) == 2
        if row == 0:
            x = HX - 348 + c * (220 + 18)
        else:
            x = HX - 203 + (0 if c == 0 else 220 + 40)
        y = 720 + row * 140 + 20 * (1 - p)
        wid = (len(g) - 1) * st + w
        ctx.save()
        rrect(ctx, x - 9, y - 9, wid + 18, w * 1.4 + 18, 14)
        ctx.set_source_rgba(1, 1, 1, 0.6 * p)
        ctx.fill_preserve()
        _stroke(ctx, 3, "#c4414b" if head else PENCIL, 0.85 * p)
        ctx.restore()
        tile_row(ctx, g, x, y, w, st, alpha=p)
    q = ease_out(clamp01((u - 0.9) / 0.3))
    text(ctx, "3枚の組×4 ＋ 対子×1", HX, 1035, 46, INK, alpha=q)
    draw_cards(ctx, t, T_W2)


# ---------- 絵: テンパイ・向聴 ----------
def scene_w3(ctx, t):
    u = t - T_W3
    w, st = 60.0, 62.0
    x0 = HX - 446
    gx = x0 + 13 * st + 28
    text(ctx, "テンパイ", HX, 640, 48, INK, alpha=ease_out(clamp01(u / 0.3)))
    for i, k in enumerate(EX_TENPAI):
        p = ease_out(clamp01((u - 0.1 - 0.04 * i) / 0.2))
        if p > 0:
            draw_tile(ctx, k, x0 + i * st, 685 + 16 * (1 - p), w, alpha=p)
    g = ease_out(clamp01((u - 0.9) / 0.3))
    if g > 0:
        dashed_rrect(ctx, gx - 3, 682, w + 6, w * 1.4 + 6, 8, RED, g, 4)
        draw_tile(ctx, EX_TENPAI_WAIT, gx, 685, w, alpha=0.4 * g)
        text(ctx, "あと1枚（東）で上がり", HX, 815, 36, RED, alpha=g)
    if u >= 3.2:
        p0 = ease_out(clamp01((u - 3.2) / 0.3))
        text(ctx, "1向聴", HX, 890, 48, INK, alpha=p0)
        for i, k in enumerate(EX_SHANTEN):
            p = ease_out(clamp01((u - 3.3 - 0.04 * i) / 0.2))
            if p > 0:
                draw_tile(ctx, k, x0 + i * st, 935 + 16 * (1 - p), w, alpha=p, highlight=RED_RGB if k == EX_SHANTEN_DROP else None)
        g2 = ease_out(clamp01((u - 4.2) / 0.3))
        if g2 > 0:
            dashed_rrect(ctx, gx - 3, 932, w + 6, w * 1.4 + 6, 8, RED, g2, 4)
            draw_tile(ctx, EX_SHANTEN_DRAW, gx, 935, w, alpha=0.4 * g2)
            text(ctx, "白を捨てて東を引けば、テンパイ", HX, 1060, 36, RED, alpha=g2)
    draw_cards(ctx, t, T_W3)


# ---------- 絵: 比べ方（同じ配牌の2人） ----------
def scene_cmp(ctx, t):
    u = t - T_CMP
    hs = results()["hand_sorted"]
    p0 = ease_out(clamp01(u / 0.4))
    for ci, (x, look) in enumerate(((300, 1), (780, -1))):
        ctx.push_group()
        student(ctx, x, 940.0, 2.6, ci, t, look, 0.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(p0)
    ctx.push_group()
    felt_panel(ctx, 60, 836, 960, 285)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(p0)
    text(ctx, "どちらも同じ配牌13枚", HX, 868, 32, "#ffffff", alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    w, st = 66.0, 69.0
    x0 = HX - (12 * st + w) / 2
    for i, k in enumerate(hs):
        p = ease_out(clamp01((u - 0.25 - 0.04 * i) / 0.25))
        if p > 0:
            draw_tile(ctx, k, x0 + i * st, 895 + 18 * (1 - p), w, alpha=p)
    text(ctx, "鳴き（ポン・チー）はなし", HX, 1055, 32, "#ffffff", alpha=ease_out(clamp01((u - 1.0) / 0.3)))
    for (x, lab, lt, col, dcol) in ((300, "七対子を狙う", "#fbe7cf", ORG, ORG_D), (780, "ふつうの手を狙う", "#d9e8f5", BLU, BLU_D)):
        q = ease_out(clamp01((u - 0.5) / 0.3))
        ww = core.text_width(lab, 34) + 44
        rrect(ctx, x - ww / 2, 598, ww, 56, 16)
        ctx.set_source_rgba(*hexrgb(lt, 0.97 * q))
        ctx.fill_preserve()
        _stroke(ctx, 5, col, q)
        text(ctx, lab, x, 626, 34, dcol, alpha=q)
    draw_cards(ctx, t, T_CMP)


# ---------- 絵: 見本の1局 ----------
def sample_view(tr, hand0, sh0, v):
    if v < 0:
        return dict(base=hand0, drawn=None, dis=None, f=0.0, sh=sh0, k=-1, done=False)
    k = int(v / DT)
    if k >= len(tr):
        if not tr:
            return dict(base=hand0, drawn=None, dis=None, f=1.0, sh=sh0, k=-1, done=True)
        return dict(base=tr[-1][3], drawn=None, dis=None, f=1.0, sh=tr[-1][2], k=len(tr) - 1, done=True)
    f = (v - k * DT) / DT
    base = hand0 if k == 0 else tr[k - 1][3]
    prev = sh0 if k == 0 else tr[k - 1][2]
    dr, dis, sh, _after = tr[k]
    return dict(base=base, drawn=dr, dis=dis, f=f, sh=sh if f >= 0.5 else prev, k=k, done=False)


def sh_text(sh):
    return "テンパイ" if sh == 0 else f"{sh}向聴"


def draw_row(ctx, view, y, label, dcol, alpha, ok):
    x0, w, st = 112.0, 60.0, 62.0
    text(ctx, label, x0, y - 46, 36, dcol, align="left", alpha=alpha)
    shown = sh_text(view["sh"])
    if view["done"]:
        shown = "テンパイ！" if view["sh"] == 0 else f"{view['sh']}向聴で終わり"
    text(ctx, shown, 930, y - 46, 36, RED if view["done"] else dcol, align="right", alpha=alpha)
    base = view["base"]
    dis, f = view["dis"], view["f"]
    idx = base.index(dis) if (view["drawn"] is not None and f >= 0.5 and dis in base) else None
    if alpha < 1.0:
        ctx.push_group()
    for i, k in enumerate(base):
        yy = y + (10 * ease(clamp01((f - 0.5) / 0.5)) if idx == i else 0)
        draw_tile(ctx, k, x0 + i * st, yy, w, highlight=RED_RGB if idx == i else None)
    if view["drawn"] is not None:
        p = ease_out(clamp01(f / 0.3))
        drop = view["drawn"] == dis and dis not in base and f >= 0.5
        draw_tile(ctx, view["drawn"], x0 + 13 * st + 22, y - 30 * (1 - p) + (10 * ease(clamp01((f - 0.5) / 0.5)) if drop else 0), w,
                  alpha=p, highlight=RED_RGB if drop else None)
    if alpha < 1.0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)


def scene_s(ctx, t):
    r = results()
    u = t - T_S
    p0 = ease_out(clamp01(u / 0.4))
    v = u - U_STEP0
    va = sample_view(r["tra"], r["hand_sorted"], r["sh0"][0], v)
    vb = sample_view(r["trb"], r["hand_sorted"], r["sh0"][1], v)
    draw_row(ctx, va, 705.0, "七対子を狙う人", ORG_D, p0, r["ra"])
    draw_row(ctx, vb, 905.0, "ふつうの手を狙う人", BLU_D, p0, r["rb"])
    if v < 0:
        label = ""
    else:
        label = f"{max(va['k'], vb['k']) + 1}巡目"
    text(ctx, label, HX, 1100, 64, INK, alpha=p0)
    draw_cards(ctx, t, T_S)


# ---------- 絵: 1万局・答え ----------
def scene_h(ctx, t):
    r = results()
    a = fade(t, T_H0, T_RS, 0.4) if t < T_RS else 0.0
    if a <= 0:
        return
    m = ease(clamp01((t - T_REV) / 0.6))
    base = lerp(1130.0, 1010.0, m)
    hsc = lerp(400.0, 280.0, m) / BAR_MAX
    p = ease(clamp01((t - T_HC) / CNT))
    n = max(0, min(N_TRIAL, int(p * N_TRIAL)))
    ca = int(r["cum_a"][n - 1]) if n > 0 else 0
    cb = int(r["cum_b"][n - 1]) if n > 0 else 0
    ctx.push_group()
    text(ctx, "1万局のうち、18巡までにテンパイした回", SX, 640, 34, INK)
    for cx, cnt, col, dcol, lab in ((330, ca, ORG, ORG_D, "七対子"), (810, cb, BLU, BLU_D, "ふつうの手")):
        hgt = cnt * hsc
        if hgt > 1:
            rrect(ctx, cx - 105, base - hgt, 210, hgt, 10)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3.2, INK, 0.9)
        text(ctx, f"{cnt:,}回", cx, base - hgt - 42, 60, dcol)
        text(ctx, lab, cx, base + 50, 46, dcol)
    ctx.move_to(150, base)
    ctx.line_to(990, base)
    _stroke(ctx, 3, INK, 0.8)
    if t < T_REV + 0.3:
        text(ctx, f"{n:,}局目", SX, base + 108, 30, PENCIL, bold=False, alpha=1 - ease(clamp01((t - T_REV) / 0.3)))
    if t >= T_REV + 0.2:
        q = ease_out(clamp01((t - T_REV - 0.2) / 0.4))
        ytop = base - r["sm"][4]["c_n"] * hsc - 42
        note.pen_circle(ctx, 330, ytop, 185, 46, RED, seed=8, width=7, progress=q)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if t >= T_REV:
        ex = 1 - ease((t - T_RS + 0.1) / 0.3)
        b = ease_out((t - T_REV - 0.2) / 0.3) * ex
        stk(ctx, "正解は『七対子』。", 1190, 54, fg=RED, a=b, tilt=-0.02)
        draw_cards(ctx, t, T_REV)


# ---------- 絵: 理由 ----------
def scene_r(ctx, t):
    r = results()
    u = t - T_RS
    hs = r["hand_sorted"]
    prs = [hs[i] for i in hand_pairs(hs)]
    text(ctx, "七対子", HX, 625, 52, ORG_D, alpha=ease_out(clamp01(u / 0.3)))
    pw, pst = 70.0, 72.0
    x0 = HX - (4 * 142 + 3 * 14) / 2
    for n, k in enumerate(prs):
        p = ease_out(clamp01((u - 0.2 - 0.18 * n) / 0.25))
        if p > 0:
            tile_row(ctx, [k, k], x0 + n * 156, 660 + 16 * (1 - p), pw, pst, alpha=p)
    x1 = HX - (3 * 142 + 2 * 14) / 2
    for n in range(3):
        q = ease_out(clamp01((u - 1.1 - 0.15 * n) / 0.25))
        if q > 0:
            dashed_rrect(ctx, x1 + n * 156, 785, 142, 98, 12, ORG_D, q)
    q = ease_out(clamp01((u - 1.4) / 0.3))
    text(ctx, "あと3組", 800, 835, 40, ORG_D, align="left", alpha=q)
    q2 = ease_out(clamp01((u - 2.0) / 0.3))
    text(ctx, "ふつうの手", HX, 930, 52, BLU_D, alpha=q2)
    bx0 = HX - 355
    for n in range(4):
        q = ease_out(clamp01((u - 2.2 - 0.15 * n) / 0.25))
        if q <= 0:
            continue
        x = bx0 + n * 150
        dashed_rrect(ctx, x, 965, 140, 82, 12, BLU_D, q)
        for j in range(3):
            dashed_rrect(ctx, x + 10 + j * 42, 975, 36, 62, 6, BLU_D, 0.6 * q, 2.4)
    q = ease_out(clamp01((u - 2.9) / 0.3))
    dashed_rrect(ctx, bx0 + 4 * 150 + 14, 965, 96, 82, 12, BLU_D, q)
    for j in range(2):
        dashed_rrect(ctx, bx0 + 4 * 150 + 24 + j * 38, 975, 32, 62, 6, BLU_D, 0.6 * q, 2.4)
    text(ctx, "3枚の組 ×4", bx0 + 295, 1085, 30, BLU_D, bold=False, alpha=q)
    text(ctx, "対子×1", bx0 + 4 * 150 + 62, 1085, 28, BLU_D, bold=False, alpha=q)
    draw_cards(ctx, t, T_RS)


# ---------- 絵: ひねり（対子3つ・5つ） ----------
def scene_tw(ctx, t):
    r = results()
    u = t - T_TW
    base, hmax = 1100.0, 420.0
    note.legend(ctx, [(ORG, "七対子"), (BLU, "ふつうの手")], 645, 34)
    text(ctx, "18巡までにテンパイした割合", HX, 702, 30, PENCIL, bold=False, alpha=ease_out(clamp01(u / 0.3)))
    for gi, (k, cx, ua, alp) in enumerate(((3, 270.0, 0.3, 1.0), (4, 540.0, 0.1, 0.45), (5, 810.0, 2.5, 1.0))):
        s_ = r["sm"][k]
        gp = clamp01((u - ua) / 0.3)
        if gp <= 0:
            continue
        for bi, (val, col, dcol) in enumerate(((s_["c_rate"], ORG, ORG_D), (s_["n_rate"], BLU, BLU_D))):
            h = val * hmax * ease_out(clamp01((u - ua) / 0.7))
            x = cx - 104 + bi * 108
            if h > 1:
                rrect(ctx, x, base - h, 100, h, 8)
                ctx.set_source_rgba(*hexrgb(col, 0.95 * alp))
                ctx.fill_preserve()
                _stroke(ctx, 3, INK, 0.9 * alp)
            text(ctx, pct0(val), x + 50, base - h - 32, 46, dcol, alpha=alp * gp)
        text(ctx, f"対子{k}つ", cx, base + 48, 40, INK, alpha=alp * gp)
    ctx.move_to(HX - 450, base)
    ctx.line_to(HX + 450, base)
    _stroke(ctx, 3, INK, 0.8)
    draw_cards(ctx, t, T_TW)


# ---------- 絵: 締め ----------
def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    hs = results()["hand_sorted"]
    s, t0, a, b, y, col, sz = card_defs()[-1]
    stk(ctx, s, y, sz, a=q, tilt=-0.02, cx=580, color=col)
    ctx.push_group()
    prs = set()
    for i in hand_pairs(hs):
        prs.update((i, i + 1))
    tile_row(ctx, hs, HX - (12 * 69 + 66) / 2, 985, 66, 69, hl={i: ORG_RGB for i in prs})
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    r_ = ease_out((t - T_Q - 0.7) / 0.3)
    text(ctx, "コメントで教えてください", 580, 1170, 40, INK, bold=False, alpha=r_)
    for (x, lab, lt, col2, dcol) in ((290, "七対子", "#fbe7cf", ORG, ORG_D), (770, "ふつうの手", "#d9e8f5", BLU, BLU_D)):
        bob = math.sin((t - T_Q) * 3.0 + x) * 6
        ww = core.text_width(lab, 54) + 50
        rrect(ctx, x - ww / 2, 1270 + bob, ww, 90, 20)
        ctx.set_source_rgba(*hexrgb(lt, 0.97 * q))
        ctx.fill_preserve()
        _stroke(ctx, 6, col2, q)
        text(ctx, lab, x, 1315 + bob, 54, dcol, alpha=q)
    text(ctx, "？", 530, 1315, 60, RED, alpha=q)


# ---------- 本体 ----------
def body(ctx, t):
    draw_deal(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        grouped(ctx, fade(t, T_W1, T_W2), scene_w1, t)
        grouped(ctx, fade(t, T_W2, T_W3), scene_w2, t)
        grouped(ctx, fade(t, T_W3, T_CMP), scene_w3, t)
        grouped(ctx, fade(t, T_CMP, T_S), scene_cmp, t)
        grouped(ctx, fade(t, T_S, T_H0), scene_s, t)
        scene_h(ctx, t)
        grouped(ctx, fade(t, T_RS, T_TW), scene_r, t)
        grouped(ctx, fade(t, T_TW, T_Q), scene_tw, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_closing(ctx, t)


# ---------- 絵: 冒頭・上のブロック ----------
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
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に配牌13枚（0秒目から並ぶ・めくれる）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(840.0), 108.0)
        ys = (440, 548, 656)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q3[-1], sz)
        note.pen_line(ctx, 565 - w3 / 2 - 6, 712, 565 + w3 / 2 + 6, 708, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL_RULE, 565, 756, 34, INK, bold=False, alpha=a1)
            text(ctx, DETAIL, 565, 795, 28, PENCIL, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 852
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = 510.0, 1015.0
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
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 464, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 498, 540 + w2 / 2 + 6, 495, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 548
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


INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


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
    for i in range(4):                                      # 冒頭: 牌が並ぶ音
        mx.add(0.1 + 0.3 * i, blip(520.0 + 70 * i, 0.05), 0.25)
    mx.add(T_W1 + 0.2, bell(784.0, 0.8), 0.3)
    mx.add(T_W1 + 2.8, bell(880.0, 0.8), 0.3)
    mx.add(T_W2 + 0.3, bell(659.3, 0.8), 0.3)
    mx.add(T_W3 + 0.3, bell(698.5, 0.8), 0.3)
    mx.add(T_W3 + 3.4, bell(784.0, 0.8), 0.3)
    mx.add(T_CMP + 0.3, whoosh(0.5), 0.2)
    mx.add(T_CMP + 1.7, bell(587.3, 0.8), 0.3)
    for i in range(10):                                     # 見本: 引いて捨てる音
        mx.add(T_S + U_STEP0 + 0.4 * i, blip(440 + 60 * (i % 2), 0.04), 0.18)
    mx.add(T_S + 4.9, thump(), 0.35)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                     # 1万局
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_HC + CNT + 0.5, bell(659.3, 0.8), 0.35)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_RS + 0.5, bell(698.5, 0.8), 0.35)
    mx.add(T_RS + 2.1, bell(784.0, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 0.4, bell(659.3, 0.8), 0.35)
    mx.add(T_TW + 2.6, bell(880.0, 0.8), 0.4)
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


def legal(kinds):
    """牌のルール: 同じ牌は4枚まで"""
    return all(kinds.count(k) <= 4 for k in set(kinds)) and all(0 <= k < 34 for k in kinds)


def run_checks():
    r = results()
    sm, js = r["sm"], r["js"]
    checks = []
    # (1) 1万局の数え直し（chiitoi_model の json と一致）
    checks.append(("回数 = 1万（3つ・4つ・5つ）", float(all(sm[k]["n"] == N_TRIAL for k in (3, 4, 5))), 1.0, 0.0))
    for k in (3, 4, 5):
        j = js[k]
        checks.append((f"対子{k}つ: 七対子 18巡までのテンパイ率が json と一致", float(round(sm[k]["c_rate"], 4) == j["chiitoi"]["tenpai18"]), 1.0, 0.0))
        checks.append((f"対子{k}つ: ふつうの手 18巡までのテンパイ率が json と一致", float(round(sm[k]["n_rate"], 4) == j["normal"]["tenpai18"]), 1.0, 0.0))
        checks.append((f"対子{k}つ: テンパイした局の巡目の中央値が json と一致", float((sm[k]["c_med"], sm[k]["n_med"]) == (j["chiitoi"]["median_turn_if_tenpai"], j["normal"]["median_turn_if_tenpai"])), 1.0, 0.0))
        checks.append((f"対子{k}つ: 早い局の割合が json と一致", float((round(sm[k]["c_faster"], 4), round(sm[k]["n_faster"], 4)) == (j["chiitoi_faster"], j["normal_faster"])), 1.0, 0.0))
    checks.append(("画面: 対子4つ 七対子 4,836回・ふつうの手 4,044回", float((f"{sm[4]['c_n']:,}", f"{sm[4]['n_n']:,}") == ("4,836", "4,044")), 1.0, 0.0))
    checks.append(("棒の目盛り(5,000)より 結果が小さい", float(max(sm[4]["c_n"], sm[4]["n_n"]) < BAR_MAX), 1.0, 0.0))
    checks.append(("数え上げの最後の値 = 全体の回数", float((int(r["cum_a"][-1]), int(r["cum_b"][-1])) == (sm[4]["c_n"], sm[4]["n_n"])), 1.0, 0.0))
    # (2) 答え
    key = answer_by_rule(sm[4]["c_rate"], sm[4]["n_rate"])
    checks.append(("規則の答え = 七対子", float(key == "七対子"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 七対子・ほぼ同じ・ふつうの手 の順", float(LABELS == ["七対子", "ほぼ同じ", "ふつうの手"]), 1.0, 0.0))
    for cr, nr, k_ in ((0.484, 0.404, "七対子"), (0.40, 0.484, "ふつうの手"), (0.45, 0.44, "ほぼ同じ"), (0.43, 0.40, "七対子"), (0.419, 0.40, "ほぼ同じ")):
        checks.append((f"規則の道具: {cr}・{nr} → {k_}", float(answer_by_rule(cr, nr) == k_), 1.0, 0.0))
    checks.append(("差は2ポイント以上（48.4% - 40.4%）", float(sm[4]["c_rate"] - sm[4]["n_rate"] >= 0.02), 1.0, 0.0))
    # (3) 見本は1万局の最初の1局そのもの
    checks.append(("見本: 1局目の配牌 = mm.deal(seed 161)", float(r["hand"] == mm.deal(np.random.default_rng(SEED), 4)[0]), 1.0, 0.0))
    checks.append(("見本: 配牌は対子ちょうど4組・3枚同じなし", float(sum(1 for c in r["hand"] if c == 2) == 4 and max(r["hand"]) <= 2), 1.0, 0.0))
    checks.append(("見本: 絵の配牌13枚が並び順（萬→筒→索→字）", float(r["hand_sorted"] == sorted(r["hand_sorted"]) and len(r["hand_sorted"]) == 13), 1.0, 0.0))
    ra0 = NONE if r["ra"] is None else r["ra"]
    rb0 = NONE if r["rb"] is None else r["rb"]
    checks.append(("見本: 引き直しのテンパイ巡目 = 1万局の1局目の記録", float((ra0, rb0) == r["first"]), 1.0, 0.0))
    rng = np.random.default_rng(SEED)
    h_, w_ = mm.deal(rng, 4)
    s_ = int(rng.integers(1 << 30))
    checks.append(("見本: chiitoi_model.play と一致（七対子）", float(mm.play(h_, w_, mm.chiitoi_sh, np.random.default_rng(s_)) == r["ra"]), 1.0, 0.0))
    checks.append(("見本: chiitoi_model.play と一致（ふつうの手）", float(mm.play(h_, w_, mm.normal_sh, np.random.default_rng(s_)) == r["rb"]), 1.0, 0.0))
    checks.append(("見本: 毎巡の引いた牌 = 山の先頭から順", float(all(tr[0] == r["wall"][i] for tr_ in (r["tra"], r["trb"]) for i, tr in enumerate(tr_))), 1.0, 0.0))
    ok_tr = True
    for tr_, f_ in ((r["tra"], mm.chiitoi_sh), (r["trb"], mm.normal_sh)):
        for dr, dis, sh, after in tr_:
            ok_tr &= len(after) == 13 and f_([after.count(k) for k in range(34)]) == sh and after == sorted(after)
    checks.append(("見本: 毎巡 捨てたあとの手は13枚・向聴数が記録どおり・並び順", float(ok_tr), 1.0, 0.0))
    checks.append(("見本: 18巡ぶん記録（どちらもテンパイせず）", float((len(r["tra"]), len(r["trb"]), r["ra"], r["rb"]) == (18, 18, None, None)), 1.0, 0.0))
    checks.append(("見本: 付箋「どちらも18巡までにテンパイできなかった」と結果が同じ", float(r["ra"] is None and r["rb"] is None), 1.0, 0.0))
    # (4) 言葉の札の例が牌のルールに合う
    checks.append(("例: 対子 = 同じ牌2枚", float(len(EX_PAIR) == 2 and EX_PAIR[0] == EX_PAIR[1]), 1.0, 0.0))
    checks.append(("例: 七対子 14枚・7種類のちがう対子・上がり形(七対子の向聴数 -1)",
                   float(len(EX_CHII) == 14 and len(set(EX_CHII)) == 7 and all(EX_CHII.count(k) == 2 for k in set(EX_CHII)) and legal(EX_CHII)
                         and mm.chiitoi_sh([EX_CHII.count(k) for k in range(34)]) == -1 and EX_CHII == sorted(EX_CHII)), 1.0, 0.0))
    ex_norm = [k for g in EX_NORM_SETS for k in g] + EX_NORM_HEAD
    c14 = [ex_norm.count(k) for k in range(34)]
    checks.append(("例: ふつうの手 14枚・順子/刻子4つ＋雀頭1つ・上がり形(向聴数 -1)",
                   float(len(ex_norm) == 14 and legal(ex_norm) and mm.normal_sh(c14) == -1
                         and all(g == sorted(g) and (g[0] == g[1] == g[2] or (g[1] == g[0] + 1 and g[2] == g[0] + 2 and g[0] // 9 == g[2] // 9 and g[0] < 27)) for g in EX_NORM_SETS)
                         and EX_NORM_HEAD[0] == EX_NORM_HEAD[1]), 1.0, 0.0))
    t13 = [EX_TENPAI.count(k) for k in range(34)]
    t14 = list(t13)
    t14[EX_TENPAI_WAIT] += 1
    checks.append(("例: テンパイ 13枚・向聴数0・東を足すと上がり形", float(len(EX_TENPAI) == 13 and legal(EX_TENPAI) and mm.normal_sh(t13) == 0 and mm.normal_sh(t14) == -1 and EX_TENPAI == sorted(EX_TENPAI)), 1.0, 0.0))
    s13 = [EX_SHANTEN.count(k) for k in range(34)]
    s_after = list(s13)
    s_after[EX_SHANTEN_DROP] -= 1
    s_after[EX_SHANTEN_DRAW] += 1
    checks.append(("例: 1向聴 13枚・向聴数1・白を捨て東を引くとテンパイ", float(len(EX_SHANTEN) == 13 and legal(EX_SHANTEN) and mm.normal_sh(s13) == 1 and mm.normal_sh(s_after) == 0 and EX_SHANTEN == sorted(EX_SHANTEN)), 1.0, 0.0))
    # (5) ひねり
    s3, s5 = sm[3], sm[5]
    tw1, tw2 = twist_texts()
    checks.append(("ひねり: 対子3つ ふつうの手43%・七対子31%（付箋と計算が同じ）", float(pct0(s3["n_rate"]) == "43%" and pct0(s3["c_rate"]) == "31%" and "ふつうの手43%・七対子31%" in tw1), 1.0, 0.0))
    checks.append(("ひねり: 対子5つ 七対子73%・ふつうの手39%（付箋と計算が同じ）", float(pct0(s5["c_rate"]) == "73%" and pct0(s5["n_rate"]) == "39%" and "七対子73%・ふつうの手39%" in tw2), 1.0, 0.0))
    checks.append(("ひねり: 対子3つは逆（ふつうの手が上）・5つは七対子が上", float(s3["n_rate"] > s3["c_rate"] and s5["c_rate"] > s5["n_rate"]), 1.0, 0.0))
    checks.append(("答えの付箋: 48%・40%（計算と同じ）", float(pct0(sm[4]["c_rate"]) == "48%" and pct0(sm[4]["n_rate"]) == "40%" and "七対子48%、ふつうの手40%" in answer_sub()), 1.0, 0.0))
    # (6) 言葉の札
    allcards = "".join(s for s, *_ in card_defs())
    for term in ("対子（トイツ）\n＝同じ牌が2枚", "七対子（チートイツ）\n＝対子を7つ集める手", "ふつうの手＝\n3枚の組を4つと、\n対子を1つ集める手", "テンパイ\n＝あと1枚で上がれる形",
                 "向聴（シャンテン）\n＝テンパイまで、\nあと何枚入れ替えるか", "1枚引いて、1枚捨てる。\n18回まで。", "捨てるのは、テンパイまでの残り\n（向聴）がいちばん少なくなる牌。"):
        checks.append((f"言葉の札「{term.splitlines()[0]}…」がある", float(term in allcards), 1.0, 0.0))
    checks.append(("鳴きなしの文が画面にある", float("鳴き（ポン・チー）はなし" in open(__file__, encoding="utf-8").read()), 1.0, 0.0))
    checks.append(("使わない言い方（残念・やっぱり・中央値・計算での見立て）が札にない",
                   float(not any(w_ in allcards for w_ in ("残念", "やっぱり", "中央値", "計算での見立て"))), 1.0, 0.0))
    # (7) 問い（3行）が収まる
    s3_ = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3_ >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3_) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3_) for l in BIG_Q3) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(440 - s3_ / 2 >= 370), 1.0, 0.0))
    checks.append(("冒頭の配牌 13枚: 1枚の幅 60px 以上・横幅いっぱい近く（850px以上）", float(DEAL_W >= 60 and (12 * DEAL_STEP + DEAL_W) >= 850), 1.0, 0.0))
    # (8) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_)
        need = max(0.12 * n_ + 1.0, 0.5 + n_ / 6.0)
        checks.append((f"札「{s_}」が読み切れる（{tb - ta:.1f}秒 / 要る {need:.1f}秒）", float(tb - ta >= need), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万局の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("見本の巡が 見本の場面に収まる（結果の付箋の前に18巡が終わる）", float(U_STEP0 + 18 * DT + 0.2 <= 4.9 and 7.3 <= (T_H0 - T_S)), 1.0, 0.0))
    checks.append(("長さ 60秒未満（50〜58.5秒）", float(50.0 <= DURATION <= 58.5), 1.0, 0.0))
    # (9) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く（拡大なし）", float(cf >= 0.15), 1.0, 0.0))
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
    r = results()
    sm = r["sm"]
    print(f"長さ {DURATION:.1f}秒  対子 {T_W1:.1f}  ふつうの手 {T_W2:.1f}  テンパイ {T_W3:.1f}  比べ方 {T_CMP:.1f}  見本 {T_S:.1f}  1万局 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  対子4つ: 七対子 {sm[4]['c_n']:,}回({pct0(sm[4]['c_rate'])}) ふつうの手 {sm[4]['n_n']:,}回({pct0(sm[4]['n_rate'])})  答え: {r['key']}")
    print(f"  対子3つ: 七対子 {pct0(sm[3]['c_rate'])} ふつうの手 {pct0(sm[3]['n_rate'])} / 対子5つ: 七対子 {pct0(sm[5]['c_rate'])} ふつうの手 {pct0(sm[5]['n_rate'])}")
    print(f"  見本: 配牌 {r['hand_sorted']}  向聴 {r['sh0']}  テンパイ巡目 七対子{r['ra']}・ふつう{r['rb']}  最後の向聴 {r['tra'][-1][2]}/{r['trb'][-1][2]}")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.4, 4.6,
          T_W1 + 1.4, T_W1 + 4.6, T_W2 + 3.0, T_W3 + 2.2, T_W3 + 5.4,
          T_CMP + 3.0, T_CMP + 5.2,
          T_S + 1.2, T_S + 3.0, T_S + 4.6, T_S + 6.4,
          T_HC + 1.0, T_REV - 0.3, T_REV + 3.0,
          T_RS + 1.8, T_RS + 4.3, T_TW + 1.2, T_TW + 5.0,
          T_Q + 2.4, DURATION - 0.2]
    stills(draw, ts, OUT)
    for old in OUT.glob("w480_*.png"):
        old.unlink()
    for p in sorted(OUT.glob("still_*.png")):
        im = Image.open(p).convert("RGB")
        im.resize((480, int(round(im.height * 480 / im.width)))).save(OUT / f"w480_{p.name[6:]}")
    print("原寸: still_*.png / 480px幅: w480_*.png / 一覧: sheet.png ->", OUT)


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
