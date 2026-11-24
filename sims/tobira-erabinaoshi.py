"""扉が3つ。1つだけ当たり。選び直す？そのまま？（モンティ・ホール問題）— 2026-11-09 作成（公開予定 11.24・ナレーションなし・60秒未満）

計算の本体は sims/monty_model.py（ルール・seed 171・答えの決め方は、1万回を回す前に そのファイルの docstring に固定してある。ここでは変えない）。
この sim は「1万回の結果を読んで絵にする」ところ。

【置き方】（monty_model.py の docstring と同じ。結果を見て変えていない）
  ① 扉は3つ。当たりは1つ、はずれは2つ。当たりの扉は毎回くじ（どれも3分の1）。
  ② あなたが扉を1つ選ぶ（まだ開けない）。どれを選ぶかもくじ。
  ③ 司会者は当たりの扉を知っていて、残り2つから はずれを必ず1つ開ける。残り2つが両方はずれのときは、どちらを開けるかをくじで決める。
  ④ 選び直すか、そのままにするか。変えるのは④の選び方だけ（①〜③の乱数は同じ）。1回 = ゲーム1回。1万回。
【答えの決め方】（answer_by_rule。計算の前に固定）
  当たる回の割合が2ポイント以上高いほうが正解。差がそれより小さければ「ほぼ同じ」。
【ひねり】 ③だけを「司会者は当たりを知らず、でたらめに1つ開ける」に変え、当たりが開いてしまった回は数えず、はずれが開いた回だけで比べる。
【見本の1回】 monty_model.run の1万回の最初の1回そのもの（当たり=扉3・あなた=扉1・司会者が開けた=扉2）。
  同じ乱数で数え直し（このファイルの recount）、1万回の当たり数が monty_model.run と一致するかを run_checks で照合する。
【言い方】 「計算での見立て」は出さない（確率のルールだけで決まるため）。中央値は出さない。
  理論上は 10,000×2/3 ≒ 6,667回。この1万回（seed 171）は 6,526回で、たまたま少なめ（概要欄に1行書く。種は計算の前に決めたまま変えない）。

問い: 「扉が3つ。1つだけ当たり。／司会者がはずれを1つ開けた。／選び直す？そのまま？」
選択肢: A 選び直す ／ B ほぼ同じ ／ C そのまま（正解の記号は A。run_checks で確かめる）
見せ方: 冒頭（問い・舞台に扉3つ・司会者・あなた）→ ルール①②③（札2枚）④（札と動きで1つずつ）→ 見本の1回 → 1万回の当たり数・答え → 理由（付箋2枚）→ ひねり → 締め
締め: 「あなたは、選び直しますか？」
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import monty_model as mm  # noqa: E402

SLUG = "tobira-erabinaoshi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIAL = mm.R
CNT = 1.4                                            # 1万回の数え上げの秒数


def answer_by_rule(switch_rate, stay_rate):
    """答えの決め方（計算の前に固定）。当たる割合の差が2ポイント以上高いほうが正解。差が小さければ ほぼ同じ"""
    d = switch_rate - stay_rate
    if abs(d) < 0.02 - 1e-9:
        return "ほぼ同じ", d
    return ("選び直す" if d > 0 else "そのまま"), d


def pct0(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


_RES = {}


def results():
    """1万回の結果（monty_model.run そのまま）。1回ごとの当たりを数え上げ用に持つ"""
    if _RES:
        return _RES["r"]
    a = mm.run(True)
    b = mm.run(False)
    sw, st = a["switch_win_arr"], a["stay_win_arr"]
    key, d = answer_by_rule(a["switch_rate"], a["stay_rate"])
    _RES["r"] = dict(a=a, b=b, sw=int(a["switch"]), st=int(a["stay"]), cum_sw=np.cumsum(sw), key=key, d=d,
                     first=a["first"], rh_n=int(b["n_valid"]), rh_sw=int(b["switch"]), rh_st=int(b["stay"]),
                     rh_sw_rate=float(b["switch_rate"]), rh_st_rate=float(b["stay_rate"]))
    return _RES["r"]


def sample():
    return results()["first"]


def recount(seed=171, n=N_TRIAL):
    """monty_model.run と同じ順で乱数を使い、1万回を別の書き方で数え直す（照合用）"""
    rng = np.random.default_rng(seed)
    car = rng.integers(0, 3, n)
    pick = rng.integers(0, 3, n)
    coin = rng.random(n)
    opened = np.empty(n, int)
    for i in range(n):
        rest = [d for d in range(3) if d != pick[i]]
        goats = [d for d in rest if d != car[i]]
        opened[i] = goats[0] if len(goats) == 1 else goats[int(coin[i] < 0.5)]
    stay = int((pick == car).sum())
    switch_to = 3 - pick - opened
    switch = int((switch_to == car).sum())
    # ひねり（司会者がでたらめ）
    ok = 0
    rs = rr = 0
    for i in range(n):
        rest = [d for d in range(3) if d != pick[i]]
        o = rest[int(coin[i] < 0.5)]
        if o == car[i]:
            continue
        ok += 1
        rs += int(pick[i] == car[i])
        rr += int((3 - pick[i] - o) == car[i])
    return dict(car0=int(car[0]), pick0=int(pick[0]), opened0=int(opened[0]), stay=stay, switch=switch, rh_n=ok, rh_stay=rs, rh_switch=rr)


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    S = sample()
    print(f"{N_TRIAL}回  当たり: 選び直す {r['sw']:,}回（{r['sw'] / N_TRIAL:.1%}） そのまま {r['st']:,}回（{r['st'] / N_TRIAL:.1%}）  答え: {r['key']}（差 {r['d']:+.3f}）")
    print(f"  ひねり: はずれが開いた {r['rh_n']:,}回のうち 選び直す {r['rh_sw']:,}回（{pct0(r['rh_sw_rate'])}）・そのまま {r['rh_st']:,}回（{pct0(r['rh_st_rate'])}）")
    print(f"見本: 1回目  当たり=扉{S['car'] + 1}  あなた=扉{S['pick'] + 1}  司会者が開けた=扉{S['opened'] + 1}  選び直す先=扉{S['switch_to'] + 1}")
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

note.use()
note.DATE = "11.24"                                  # 日付欄（公開予定日）

SWC, SWC_D = "#3f7fb5", "#2a5a85"                    # 選び直す（青）
STC, STC_D = "#e0801f", "#a85a0a"                    # そのまま（橙）
GOLD, GOLD_D = "#f4b400", "#b07d00"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は A（1番目）
LABELS = ["選び直す", "ほぼ同じ", "そのまま"]
KEY_LABEL = {"選び直す": "選び直す", "ほぼ同じ": "ほぼ同じ", "そのまま": "そのまま"}
CORRECT = 0

BIG_Q3 = ["扉が3つ。1つだけ当たり。", "司会者がはずれを1つ開けた。", "選び直す？そのまま？"]      # 1コマ目の3行（同じ大きさ）
BIG_Q = ["司会者が、はずれを1つ開けた。", "選び直す？そのまま？"]                                       # 定位置（上）の2行

# ---------- 配置 ----------
CY_INTRO, CY_FINAL = 830.0, 620.0                    # 舞台の上端 y（冒頭は問いのぶん下げる）
DOORX = (235.0, 538.0, 840.0)                        # 扉1・2・3 の中心 x
DW, DH = 268.0, 280.0                                # 扉の幅・高さ
YOU_X, HOST_X = 240.0, 840.0                         # あなた（後ろ姿）・司会者
FEET, K_P = 665.0, 2.75                               # 足もと y（cy から）・人の大きさ（身長 100×K_P px）
STAGE_H = 715.0                                      # 舞台の枠の高さ（cy-35 から）
DEMO = dict(car=1, pick=0, opened=2)                 # ルール説明用の並び（見本とは別。当たり=扉2・あなた=扉1・司会者=扉3）

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.7, 0.9, 1.1)
T_CD = (1.2, 1.8, 2.4)                               # 3・2・1
T_MOVE, T_GO = 2.8, 3.2


def setup():
    global T_R1, T_R2, T_R3A, T_R3B, T_R4, T_S0, T_H0, T_HC, T_REV, T_RS, T_TW, T_TWB, T_Q, DURATION, SCENES, CARDS, DLABELS
    T_R1 = T_GO                                      # ルール① 当たりは1つ・はずれは2つ（3.3秒）
    T_R2 = T_R1 + 3.2                                # ルール② あなたが1つ選ぶ（3.5秒）
    T_R3A = T_R2 + 3.5                               # ルール③-1 司会者は当たりを知っている（3.9秒・いちばんゆっくり）
    T_R3B = T_R3A + 3.9                              # ルール③-2 はずれを必ず1つ開ける（4.5秒）
    T_R4 = T_R3B + 4.5                               # ルール④ 選び直す？そのまま？（3.7秒）
    T_S0 = T_R4 + 3.7                                # 見本の1回（7.7秒）
    T_H0 = T_S0 + 7.7                                # 1万回
    T_HC = T_H0 + 0.3                                # 数え上げ始め
    T_REV = T_H0 + 2.8                               # 答え
    T_RS = T_H0 + 5.4                                # 理由（7.6秒）
    T_TW = T_RS + 7.8                                # ひねり①（司会者が当たりを知らなかったら）3.5秒
    T_TWB = T_TW + 3.7                               # ひねり②③（49%と51%・答えを決めていたこと）8.4秒
    T_Q = T_TWB + 8.6                                # 締め
    DURATION = T_Q + 3.2
    SCENES = [("冒頭（問い・舞台）", 0.0, T_GO), ("ルール① 当たり1・はずれ2", T_R1, T_R2), ("ルール② あなたが選ぶ", T_R2, T_R3A),
              ("ルール③-1 司会者は知っている", T_R3A, T_R3B), ("ルール③-2 はずれを必ず開ける", T_R3B, T_R4), ("ルール④ 選び直す？そのまま？", T_R4, T_S0),
              ("見本の1回", T_S0, T_H0), ("1万回の当たり数・答え", T_H0, T_RS), ("理由（付箋2枚）", T_RS, T_TW),
              ("ひねり① 司会者が知らなかったら", T_TW, T_TWB), ("ひねり②③ 49%と51%・答えを決めていたこと", T_TWB, T_Q), ("締め", T_Q, DURATION)]
    # 下の付箋（文, 出る秒, 消える秒）。「1文字0.12秒＋1秒以上」と公開前チェックの「0.5秒＋行の文字数÷6秒」の両方より長く映す
    CARDS = {
        "r1": ("当たりは1つ。はずれは2つ。", T_R1 + 0.2, T_R2 - 0.1),
        "r2": ("あなたが1つ選ぶ。まだ開けない。", T_R2 + 0.2, T_R3A - 0.1),
        "r3a": ("司会者は、当たりの扉を知っている。", T_R3A + 0.2, T_R3B - 0.1),
        "r3b": ("残り2つから、\nはずれを必ず1つ開ける。", T_R3B + 0.2, T_R4 - 0.1),
        "r3c": ("当たりの扉は、\n司会者は開けない。", T_R3B + 1.2, T_R4 + 0.4),           # 補足の付箋（小さめ・舞台の床に貼る）
        "r4": ("残った扉に選び直す？そのまま？", T_R4 + 0.2, T_S0 - 0.1),
        "s0": ("たとえば、この1回では", T_S0 + 0.2, T_S0 + 2.7),
        "ans": ("正解は『選び直す』。", T_REV + 0.2, T_RS - 0.05),
        "rs1": ("最初に当たりを選べるのは、\n3回に1回だけ。", T_RS + 0.2, T_RS + 3.8),
        "rs2": ("残りの3回に2回は、\n閉じたままの扉が当たり。", T_RS + 3.95, T_TW),
        "tw1": ("司会者が、当たりを知らなかったら？", T_TW + 0.2, T_TWB - 0.1),
        "tw2": ("でたらめに開けて、\nはずれだった回だけ数えた。", T_TWB + 0.2, T_TWB + 3.85),
        "tw3": ("司会者が『必ずはずれを開ける』\nことが、答えを決めていた。", T_TWB + 3.95, T_Q - 0.05),
        "q": ("あなたは、選び直しますか？", T_Q + 0.25, DURATION - 0.15),
    }
    # 扉の下の言葉（文, 扉の番号0〜2, 段, 色, 出る秒, 消える秒）。段1 = 扉のすぐ下、段2 = その下
    S = T_S0
    DLABELS = [
        ("はずれ", 0, 1, PENCIL, T_R1 + 0.5, T_R1 + 2.7), ("当たり", 1, 1, RED, T_R1 + 0.5, T_R1 + 2.7), ("はずれ", 2, 1, PENCIL, T_R1 + 0.5, T_R1 + 2.7),
        ("あなた", 0, 1, STC_D, T_R2 + 1.2, T_R4 + 0.3),
        ("はずれ", 2, 1, PENCIL, T_R3B + 1.7, T_S0 + 0.1),
        ("そのまま", 0, 1, STC_D, T_R4 + 0.45, T_S0 + 0.1), ("選び直す", 1, 1, SWC_D, T_R4 + 0.45, T_S0 + 0.1),
        ("当たりは扉3", 2, 1, RED, S + 0.4, S + 2.6),
        ("あなたは扉1", 0, 1, STC_D, S + 2.9, S + 4.8),
        ("司会者が開けた", 1, 1, INK, S + 4.0, S + 6.1),
        ("そのまま", 0, 1, STC_D, S + 5.0, S + 7.6), ("選び直す", 2, 1, SWC_D, S + 5.0, S + 7.6),
        ("はずれ", 0, 2, PENCIL, S + 6.1, S + 7.6), ("当たり！", 2, 2, RED, S + 6.1, S + 7.6),
        ("数えない", 1, 1, RED, T_TW + 2.0, T_TWB),
        ("そのまま", 0, 1, STC_D, T_Q + 0.45, DURATION - 0.2), ("選び直す", 1, 1, SWC_D, T_Q + 0.45, DURATION - 0.2), ("はずれ", 2, 1, PENCIL, T_Q + 0.45, DURATION - 0.2),
    ]


setup()


def cards():
    """札: (文, 出る秒, 消える秒)"""
    return list(CARDS.values())


# ---------- 絵: 共通 ----------
def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ss(a, b, t):
    return smooth((t - a) / (b - a))


def lerp(a, b, u):
    return a + (b - a) * u


def win(t, a, b, fi=0.3, fo=0.3):
    return clamp01((t - a) / fi) * (1 - clamp01((t - (b - fo)) / fo))


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


# ---------- 絵: 人（司会者は正面・あなたは後ろ姿。janken-issei の生徒と同じ頭身・線） ----------
SKIN, SHOE = "#f7d9bd", "#2a2f3d"


def person(ctx, x, fy, k, kind, t, wl=None, wr=None, mouth=0.0):
    """立っている人。(x, fy) は足もとの中心、身長は 100·k px。kind = 'host'（正面）/ 'you'（後ろ姿）。
    wl・wr = 画面の左・右の手首の位置（k を単位に、足もと中心から (dx, dy)）。None なら体の横に下ろす"""
    host = kind == "host"
    P = lambda dx, dy: (x + dx * k, fy + dy * k)    # noqa: E731
    jacket, jacket_d, pants = ("#2b2837", "#1f1c29", "#3a3a48") if host else ("#3f9a8f", "#2f7d73", "#46587a")
    hair = "#a3a3b3" if host else "#4a3322"
    lw = max(2.4, 0.78 * k)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def poly(pts_, col, w=None):
        ctx.new_path()
        for i, (px, py) in enumerate(pts_):
            (ctx.move_to if i == 0 else ctx.line_to)(*P(px, py))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, w or lw, INK, 0.9)

    for dx in (-7.2, 7.2):                                                     # 脚と靴
        thick(ctx, [P(dx, -48), P(dx, -7)], 13.0 * k, pants, 2.4)
        core.rrect(ctx, *P(dx - 8.5, -6.5), 17 * k, 7 * k, 3.2 * k)
        ctx.set_source_rgba(*hexrgb(SHOE))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    if not host:                                                               # フード（首のうしろ）
        ctx.new_path()
        ctx.arc(*P(0, -80), 11.5 * k, 0, math.pi)
        ctx.set_source_rgba(*hexrgb(jacket_d))
        ctx.fill_preserve()
        _stroke(ctx, lw, INK, 0.9)
    ctx.new_path()                                                             # 上着
    ctx.move_to(*P(-9, -80.5))
    ctx.curve_to(*P(-14, -79.5), *P(-18.5, -78.5), *P(-18.3, -71))
    ctx.line_to(*P(-15.6, -43))
    ctx.line_to(*P(15.6, -43))
    ctx.line_to(*P(18.3, -71))
    ctx.curve_to(*P(18.5, -78.5), *P(14, -79.5), *P(9, -80.5))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(jacket))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    if host:
        poly([(-5.8, -80.5), (0, -63), (5.8, -80.5)], "#f6f3ea", lw * 0.8)
        poly([(-5.8, -80.5), (-10.2, -68), (-3.6, -60.5), (0, -63)], jacket_d, lw * 0.8)
        poly([(5.8, -80.5), (10.2, -68), (3.6, -60.5), (0, -63)], jacket_d, lw * 0.8)
        poly([(0, -77.5), (-6.5, -81.5), (-6.5, -73.5)], "#c4414b", lw * 0.7)      # 蝶ネクタイ
        poly([(0, -77.5), (6.5, -81.5), (6.5, -73.5)], "#c4414b", lw * 0.7)
        ctx.new_path()
        ctx.arc(*P(0, -77.5), 1.7 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#a02f39"))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.6, INK, 0.9)
        for by_ in (-55.0, -49.0):
            ctx.new_path()
            ctx.arc(*P(0, by_), 1.0 * k, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#e6c35a"))
            ctx.fill()
    else:
        ctx.move_to(*P(0, -78))                                                # 背中の中心の縫い目
        ctx.line_to(*P(0, -45))
        _stroke(ctx, lw * 0.6, INK, 0.45)
        ctx.new_path()
        core.rrect(ctx, *P(-9, -56), 18 * k, 9 * k, 2.5 * k)                    # 腰のポケット
        _stroke(ctx, lw * 0.6, INK, 0.35)
    # うで
    for side, wr_ in ((-1, wl), (1, wr)):
        shx, shy = P(side * 17.0, -75.5)
        wp = wr_ if wr_ is not None else (side * 18.5, -46.0)
        wx, wy = P(*wp)
        elx, ely = ik_out(shx, shy, wx, wy, 14.0 * k, 14.0 * k, side)
        thick(ctx, [(shx, shy), (elx, ely), (wx, wy)], 7.6 * k, jacket, 2.4)
        ctx.new_path()
        ctx.arc(wx, wy + 1.0 * k, 4.0 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    # 首・頭
    core.rrect(ctx, *P(-3.6, -82), 7.2 * k, 6.5 * k, 2 * k)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    for sg in (-1, 1):                                                          # 耳
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
    ctx.set_source_rgba(*hexrgb(hair if not host else SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    if host:
        ctx.new_path()                                                          # 前髪
        ctx.move_to(*P(-9.6, -88))
        ctx.curve_to(*P(-11.5, -104), *P(11.5, -104), *P(9.6, -88))
        ctx.line_to(*P(9.0, -94))
        ctx.line_to(*P(5.0, -96.4))
        ctx.line_to(*P(0.5, -94.0))
        ctx.line_to(*P(-4.5, -96.0))
        ctx.line_to(*P(-8.6, -94.5))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(hair))
        ctx.fill_preserve()
        _stroke(ctx, lw, INK, 0.92)
        blink = (t * 0.9) % 3.4 < 0.12
        for sg in (-1, 1):
            ex, ey = P(sg * 3.5, -89.2)
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
                ctx.arc(ex + 0.45 * k, ey - 0.55 * k, 0.55 * k, 0, 2 * math.pi)
                ctx.set_source_rgba(1, 1, 1, 0.95)
                ctx.fill()
            bx, by = P(sg * 3.6, -92.3)
            ctx.move_to(bx - 2.0 * k, by + 0.25 * k)
            ctx.line_to(bx + 2.0 * k, by - 0.25 * k)
            _stroke(ctx, lw * 0.8, INK, 0.8)
            ctx.new_path()
            ctx.arc(*P(sg * 6.0, -86.1), 1.5 * k, 0, 2 * math.pi)
            ctx.set_source_rgba(1.0, 0.55, 0.55, 0.32)
            ctx.fill()
        mx_, my_ = P(0, -84.3)
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
    else:
        for dx, hh in ((-4.5, 4.0), (0.5, 5.4), (5.0, 3.8)):                    # 後ろ髪の毛先
            poly([(dx - 3.0, -98.8), (dx, -98.8 - hh), (dx + 3.0, -98.8)], hair, lw * 0.8)
        ctx.new_path()
        ctx.arc(*P(0, -85.5), 6.6 * k, 0.15 * math.pi, 0.85 * math.pi)          # えり足の線
        _stroke(ctx, lw * 0.7, INK, 0.35)
    ctx.restore()


# ---------- 絵: 景品（トロフィー） ----------
def trophy(ctx, cx, cy, s, t=0.0, rays=True):
    """金色のトロフィー（cx, cy = 全体の中心、s = 高さの目安）。rays = 後ろで回る光"""
    u = s / 100.0
    if rays:
        ctx.save()
        ctx.translate(cx, cy - 2 * u)
        ctx.rotate(t * 0.5)
        for i in range(10):
            a0 = i * 2 * math.pi / 10
            ctx.move_to(0, 0)
            ctx.line_to(math.cos(a0) * 95 * u, math.sin(a0) * 95 * u)
            ctx.line_to(math.cos(a0 + 0.2) * 95 * u, math.sin(a0 + 0.2) * 95 * u)
            ctx.close_path()
            ctx.set_source_rgba(1.0, 0.9, 0.4, 0.42)
            ctx.fill()
        ctx.restore()
    ctx.save()
    ctx.translate(cx, cy)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for sg in (-1, 1):                                                          # 持ち手
        ctx.new_path()
        ctx.arc(sg * 37 * u, -26 * u, 15 * u, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(9.5 * u)
        ctx.stroke_preserve()
        ctx.set_source_rgba(*hexrgb(GOLD))
        ctx.set_line_width(5.5 * u)
        ctx.stroke()
    ctx.new_path()                                                              # 土台
    core.rrect(ctx, -26 * u, 28 * u, 52 * u, 13 * u, 3 * u)
    ctx.set_source_rgba(*hexrgb(GOLD_D))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.new_path()                                                              # 脚
    core.rrect(ctx, -6 * u, 6 * u, 12 * u, 24 * u, 2 * u)
    ctx.set_source_rgba(*hexrgb(GOLD))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.new_path()                                                              # 杯
    ctx.move_to(-38 * u, -50 * u)
    ctx.line_to(38 * u, -50 * u)
    ctx.curve_to(38 * u, -8 * u, 20 * u, 8 * u, 0, 9 * u)
    ctx.curve_to(-20 * u, 8 * u, -38 * u, -8 * u, -38 * u, -50 * u)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(GOLD))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.92)
    ctx.new_path()                                                              # つや
    ctx.move_to(-27 * u, -44 * u)
    ctx.curve_to(-27 * u, -22 * u, -20 * u, -10 * u, -12 * u, -2 * u)
    ctx.set_source_rgba(1, 0.96, 0.7, 0.85)
    ctx.set_line_width(5 * u)
    ctx.stroke()
    ctx.new_path()                                                              # 星
    for i in range(10):
        r_ = 13 * u if i % 2 == 0 else 5.5 * u
        a_ = -math.pi / 2 + i * math.pi / 5
        (ctx.move_to if i == 0 else ctx.line_to)(math.cos(a_) * r_ + 6 * u, math.sin(a_) * r_ - 28 * u)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    _stroke(ctx, 2.2, GOLD_D, 0.9)
    ctx.restore()


# ---------- 絵: 扉 ----------
DOOR_BLUE, DOOR_BLUE_D = "#5b86c7", "#3f66a3"


def door(ctx, cx, y, w, h, num, op, xr, has_car, glow=0.0, frame=0.0, t=0.0, a=1.0):
    """扉1枚。op = 開き（0〜1）、xr = 裏が透ける度合い、has_car = 中が当たり（トロフィー）か（False は からっぽ）、
    glow = 黄色く光る、frame = 橙の太い枠（あなたが選んだ印）"""
    x0 = cx - w / 2
    cs = max(4.0, w * 0.048)
    rrect(ctx, x0 - cs, y - cs, w + 2 * cs, h + cs, max(3, cs * 0.8))
    ctx.set_source_rgba(*hexrgb("#8b6a45", a))
    ctx.fill_preserve()
    _stroke(ctx, max(2.4, w * 0.014), INK, 0.9 * a)
    ctx.save()
    ctx.rectangle(x0, y, w, h)
    ctx.clip()
    if op > 0.01 or xr > 0.01:
        ctx.set_source_rgba(*hexrgb("#f1e6cf", a))
        ctx.paint()
        ctx.rectangle(x0, y + h * 0.84, w, h * 0.16)
        ctx.set_source_rgba(*hexrgb("#d6c39b", a))
        ctx.fill()
        if has_car:
            trophy(ctx, cx, y + h * 0.5, h * 0.56, t)
        else:
            if w > 120:
                text(ctx, "からっぽ", cx, y + h * 0.5, 36, PENCIL, alpha=a)
                for i in range(5):                                           # ほこり
                    ctx.new_path()
                    ctx.arc(cx - 60 + i * 30 + 6 * math.sin(t * 2 + i), y + h * 0.7 + 8 * math.cos(t * 1.7 + i * 2), 3.2, 0, 2 * math.pi)
                    ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
                    ctx.fill()
                ctx.move_to(x0, y)                                           # くもの巣
                ctx.line_to(x0 + w * 0.2, y + w * 0.14)
                ctx.move_to(x0, y + w * 0.1)
                ctx.line_to(x0 + w * 0.12, y + w * 0.1)
                ctx.move_to(x0 + w * 0.1, y)
                ctx.line_to(x0 + w * 0.12, y + w * 0.1)
                _stroke(ctx, 2.0, PENCIL, 0.5 * a)
            else:
                text(ctx, "から", cx, y + h * 0.5, 26, PENCIL, alpha=a)
    else:
        ctx.paint_with_alpha(0.0)
        ctx.set_source_rgba(*hexrgb("#3a3550", a))
        ctx.paint()
    ctx.restore()
    pw = w * (1 - 0.83 * op)
    ins = op * h * 0.06
    pa = a * (1 - 0.86 * xr)
    ctx.new_path()
    ctx.move_to(x0, y)
    ctx.line_to(x0 + pw, y + ins)
    ctx.line_to(x0 + pw, y + h - ins)
    ctx.line_to(x0, y + h)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(DOOR_BLUE, pa))
    ctx.fill_preserve()
    _stroke(ctx, max(2.4, w * 0.014), INK, 0.9 * pa)
    if op < 0.5:
        ctx.save()
        ctx.translate(x0, y)
        ctx.scale(pw / w, 1.0)
        for (ry, rh) in ((h * 0.1, h * 0.38), (h * 0.55, h * 0.34)):
            core.rrect(ctx, w * 0.12, ry, w * 0.76, rh, w * 0.03)
            ctx.set_source_rgba(*hexrgb(DOOR_BLUE_D, 0.28 * pa))
            ctx.fill_preserve()
            _stroke(ctx, max(1.6, w * 0.008), DOOR_BLUE_D, 0.7 * pa)
        ctx.restore()
        ctx.new_path()
        ctx.arc(x0 + pw * 0.9, y + h * 0.58, max(3, w * 0.03), 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#e6c35a", pa))
        ctx.fill_preserve()
        _stroke(ctx, 2.0, INK, 0.8 * pa)
        if num is not None:
            na = pa * (1 - clamp01(op * 2.5))
            ctx.new_path()
            ctx.arc(x0 + pw / 2, y + h * 0.3, w * 0.17, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.95 * na)
            ctx.fill_preserve()
            _stroke(ctx, 3.0, INK, 0.9 * na)
            text(ctx, str(num), x0 + pw / 2, y + h * 0.3, w * 0.24, INK, alpha=na)
    if glow > 0:
        rrect(ctx, x0 - cs - 8, y - cs - 8, w + 2 * cs + 16, h + cs + 16, 14)
        ctx.set_source_rgba(*hexrgb("#ffcf33", 0.95 * glow * a))
        ctx.set_line_width(10)
        ctx.stroke()
    if frame > 0:
        rrect(ctx, x0 - cs - 10, y - cs - 10, w + 2 * cs + 20, h + cs + 20, 16)
        ctx.set_source_rgba(*hexrgb(STC, 0.95 * frame * a))
        ctx.set_line_width(9)
        ctx.stroke()


def bubble(ctx, cx, cy, a, t, qmark=False):
    """司会者の頭のそばに浮かぶ考えごとの雲。中は当たりの扉の小さな絵（qmark のときは「？」）"""
    if a <= 0:
        return
    ctx.push_group()
    blobs = [(cx, cy, 70), (cx - 52, cy + 12, 40), (cx + 52, cy + 12, 40), (cx - 30, cy - 48, 38), (cx + 30, cy - 48, 38)]
    for bx, by, br in blobs:
        ctx.new_path()
        ctx.arc(bx, by, br + 3.5, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.fill()
    for bx, by, br in blobs:
        ctx.new_path()
        ctx.arc(bx, by, br, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
    for bx, by, br in ((cx + 88, cy + 58, 11), (cx + 106, cy + 78, 7)):          # 頭へつづく小さな丸
        ctx.new_path()
        ctx.arc(bx, by, br + 3, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.fill()
        ctx.new_path()
        ctx.arc(bx, by, br, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
    if qmark:
        text(ctx, "？", cx, cy, 84, RED)
    else:
        door(ctx, cx, cy - 46, 66, 86, None, 1.0, 0.0, True, t=t)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 舞台の状態（時間の関数） ----------
def new_state():
    return dict(open=[0.0, 0.0, 0.0], xray=[0.0, 0.0, 0.0], car=1, frame=[0.0, 0.0, 0.0], glow=[0.0, 0.0, 0.0],
                you=0.0, host=0.0, talk=0.0, bubble=0.0, qmark=0.0, dark=0.0, tag=None)


def stage_state(t):
    S = new_state()
    if t < T_GO:                                                     # 冒頭: 司会者がはずれの扉（2）を開けたところ
        S["car"] = 2
        o = 1 - ss(T_MOVE, T_GO, t)
        S["open"][1] = ss(0.15, 0.9, t) * o
        S["frame"][0] = ss(0.6, 1.0, t) * o
        S["you"] = ss(0.3, 0.8, t) * o
        S["host"] = ss(0.0, 0.5, t) * o
        S["talk"] = o * ss(0.2, 0.4, t) * (0.5 + 0.5 * math.sin(t * 13))
        S["dark"] = 0.55 * (1 - ss(0.0, 0.9, t))
        return S
    if t < T_S0 + 0.4:                                               # ルール①〜④（当たり=扉2・あなた=扉1・司会者が開ける=扉3）
        S["car"] = DEMO["car"]
        fd = 1 - ss(T_S0, T_S0 + 0.35, t)
        xr = ss(T_R1 + 0.3, T_R1 + 0.9, t) * (1 - ss(T_R1 + 2.3, T_R1 + 2.9, t)) if t < T_R2 else 0.0
        S["xray"] = [xr] * 3
        S["you"] = ss(T_R2 + 0.4, T_R2 + 0.9, t) * (1 - ss(T_R2 + 2.4, T_R2 + 3.0, t))
        S["frame"][DEMO["pick"]] = ss(T_R2 + 1.0, T_R2 + 1.4, t) * fd
        S["bubble"] = ss(T_R3A + 0.4, T_R3A + 0.9, t) * (1 - ss(T_R4, T_R4 + 0.4, t))
        if T_R3A <= t < T_R3B:
            S["talk"] = ss(T_R3A + 0.3, T_R3A + 0.5, t) * (0.5 + 0.5 * math.sin(t * 12))
        S["host"] = ss(T_R3B + 0.5, T_R3B + 0.9, t) * (1 - ss(T_R3B + 1.9, T_R3B + 2.3, t))
        S["open"][DEMO["opened"]] = ss(T_R3B + 0.9, T_R3B + 1.6, t) * fd
        gl = ss(T_R4 + 0.3, T_R4 + 0.7, t) * fd * (0.6 + 0.4 * math.sin(t * 7))
        S["glow"][DEMO["pick"]] = gl
        S["glow"][3 - DEMO["pick"] - DEMO["opened"]] = gl
        return S
    if t < T_TW - 0.4:                                               # 見本の1回（1万回の最初の1回）
        F = sample()
        S["car"] = F["car"]
        u = t - T_S0
        S["xray"][F["car"]] = ss(0.3, 0.8, u) * (1 - ss(2.1, 2.6, u))
        S["you"] = ss(2.6, 3.1, u) * (1 - ss(4.6, 5.0, u))
        S["frame"][F["pick"]] = ss(2.9, 3.3, u)
        S["host"] = ss(3.3, 3.7, u) * (1 - ss(4.3, 4.7, u))
        S["open"][F["opened"]] = ss(3.7, 4.3, u)
        S["open"][F["switch_to"]] = ss(5.5, 6.1, u)
        S["open"][F["pick"]] = ss(5.5, 6.1, u)
        return S
    if t < T_Q - 0.4:                                                # ひねり①: 司会者が当たりを知らない（でたらめに開けて、当たりが開いてしまった）
        S["car"] = 1
        u = t - T_TW
        S["frame"][0] = 1.0
        S["qmark"] = ss(0.3, 0.7, u)
        S["host"] = ss(0.8, 1.2, u) * (1 - ss(2.4, 2.8, u))
        S["open"][1] = ss(1.3, 2.0, u)
        return S
    S["car"] = 1                                                     # 締め: 残った2つの扉が光る
    u = t - T_Q
    S["open"][2] = 1.0
    S["frame"][0] = 1.0
    gl = ss(0.3, 0.7, u) * (0.6 + 0.4 * math.sin(t * 7))
    S["glow"][0] = gl
    S["glow"][1] = gl
    S["you"] = 0.0
    return S


def stage_alpha(t):
    if t < T_H0:
        return 1.0 - ss(T_H0 - 0.3, T_H0, t) if False else 1.0
    segs = ((T_TW, T_TWB), (T_Q, DURATION + 1))
    a = 0.0
    for (s0, s1) in segs:
        if s0 <= t < s1 + 0.3:
            a = max(a, ss(s0 - 0.05, s0 + 0.3, t) * (1 - ss(s1, s1 + 0.3, t)))
    if T_H0 <= t < T_H0 + 0.3:
        a = max(a, 1 - ss(T_H0, T_H0 + 0.3, t))
    return a


# ---------- 絵: 舞台 ----------
def cy_of(t):
    return lerp(CY_INTRO, CY_FINAL, INTRO.moved(t))


def draw_stage(ctx, cy, t, S):
    # 壁と床
    ctx.save()
    rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
    ctx.clip()
    fill(ctx, "#e6dff0")
    ctx.paint()
    ctx.rectangle(60, cy + 280, 960, 440)
    ctx.set_source_rgba(*hexrgb("#d6b98d"))
    ctx.fill()
    for i in range(7):                                              # 床の板
        yy = cy + 304 + i * 52
        ctx.move_to(60, yy)
        ctx.line_to(1020, yy)
        _stroke(ctx, 2.0, "#a98a5e", 0.35)
    ctx.move_to(60, cy + 280)
    ctx.line_to(1020, cy + 280)
    _stroke(ctx, 3.4, INK, 0.7)
    for i in range(5):                                              # 壁の模様（うすい縦じま）
        xx = 150 + i * 190
        ctx.rectangle(xx, cy - 35, 60, 315)
        ctx.set_source_rgba(1, 1, 1, 0.22)
        ctx.fill()
    ctx.restore()
    rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
    _stroke(ctx, 3, PENCIL, 0.6)
    # 扉
    for i in range(3):
        door(ctx, DOORX[i], cy, DW, DH, i + 1, S["open"][i], S["xray"][i], i == S["car"], S["glow"][i], S["frame"][i], t)
    # 人
    pu = S["you"]
    wl = (lerp(-18.5, -27.0, pu), lerp(-46.0, -106.0, pu)) if pu > 0.001 else None      # あなた: 扉1を指さす
    person(ctx, YOU_X, cy + FEET, K_P, "you", t, wl=wl)
    ph = S["host"]
    wl2 = (lerp(-18.5, -42.0, ph), lerp(-46.0, -96.0, ph)) if ph > 0.001 else None       # 司会者: 扉のほうを指す
    person(ctx, HOST_X, cy + FEET, K_P, "host", t, wl=wl2, mouth=S["talk"])
    bubble(ctx, 700.0, cy + 368, S["bubble"], t)
    if S["qmark"] > 0:
        bubble(ctx, 700.0, cy + 368, S["qmark"], t, qmark=True)
    # 扉の下の言葉
    for (s_, di, row, col, ta, tb) in DLABELS:
        al = win(t, ta, tb, 0.2, 0.2)
        if al > 0:
            text(ctx, s_, DOORX[di], cy + (306 if row == 1 else 354), 40 if row == 1 else 42, col, alpha=al)
    # 照明（冒頭: 暗い舞台に明かりがつく）
    if S["dark"] > 0:
        ctx.save()
        rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
        ctx.set_source_rgba(0.08, 0.07, 0.16, S["dark"])
        ctx.fill()
        ctx.restore()


def rule_tag(ctx, t):
    """ルールの番号（舞台の左上）"""
    cy = CY_FINAL
    for s_, a, b in (("ルール1", T_R1, T_R2), ("ルール2", T_R2, T_R3A), ("ルール3", T_R3A, T_R4), ("ルール4", T_R4, T_S0)):
        al = win(t, a + 0.1, b - 0.05, 0.2, 0.15)
        if al > 0:
            text(ctx, s_, 150, cy - 56, 30, RED, alpha=al)


def bottom_card(ctx, t, key, size=40, color="yellow", fg=INK, y=1385.0, x=565.0):
    s_, ta, tb = CARDS[key]
    al = win(t, ta, tb, 0.25, 0.25)
    if al > 0:
        note.sticky(ctx, s_, x, y, size, color, fg=fg, a=al, tilt=-0.015)


def draw_stage_scene(ctx, t):
    a = stage_alpha(t)
    if a <= 0:
        return
    cy = cy_of(t)
    S = stage_state(t)
    ctx.push_group()
    ctx.save()
    z = 1.0 + 0.10 * (1 - ease(clamp01(t / 1.1)))                  # 冒頭だけ、場面が寄ったところから引く（文字は拡大しない）
    if z > 1.0:
        ctx.translate(540, cy + 330)
        ctx.scale(z, z)
        ctx.translate(-540, -(cy + 330))
    draw_stage(ctx, cy, t, S)
    ctx.restore()
    rule_tag(ctx, t)
    # 札
    for key in ("r1", "r2", "r3a", "r3b", "r4", "s0", "tw1", "q"):
        bottom_card(ctx, t, key, 48 if key == "q" else 40)
    s_, ta, tb = CARDS["r3c"]                                        # 補足の付箋（舞台の床・小さめ）
    al = win(t, ta, tb, 0.25, 0.25)
    if al > 0:
        note.sticky(ctx, s_, 560, CY_FINAL + 520, 32, "pink", fg=RED, a=al, tilt=-0.02)
    # 冒頭のカウントダウン（床の中央）は SIntro で描く
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 絵: 1万回の当たり数・答え ----------
def draw_hist_scene(ctx, t):
    a = clamp01((t - T_H0) / 0.4) * (1 - clamp01((t - T_RS) / 0.3))
    if a <= 0:
        return
    r = results()
    ctx.push_group()
    text(ctx, "1万回やって、当たった回数", 580, 650, 46, INK)
    base = 1215.0
    p = ease(clamp01((t - T_HC) / CNT))
    n = int(p * N_TRIAL)
    sw = int(r["cum_sw"][n - 1]) if n > 0 else 0
    st = n - sw
    if t < T_REV - 0.2:
        text(ctx, f"{n:,}回目", 540, base + 112, 36, PENCIL, bold=False)
    base = 1215.0
    sc_ = 0.065
    for cx, v, col, dcol, lab in ((290.0, sw, SWC, SWC_D, "選び直す"), (700.0, st, STC, STC_D, "そのまま")):
        hgt = v * sc_
        rrect(ctx, cx - 120, base - 480, 240, 480, 14)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.5)
        if hgt > 1:
            rrect(ctx, cx - 120, base - hgt, 240, hgt, 14)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3.4, INK, 0.9)
        text(ctx, f"{v:,}回", cx, base - max(hgt, 0) - 48, 72, dcol)
        text(ctx, lab, cx, base + 48, 44, dcol)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if t >= T_REV:
        bottom_card(ctx, t, "ans", 52, fg=RED, y=1385.0)


def mini_door_row(ctx, t, u):
    """理由の2枚目の絵: あなたの扉（はずれ）・司会者が開けた扉（はずれ）・残った扉（当たり）"""
    y, w, h = 1020.0, 150.0, 190.0
    xs = (250.0, 540.0, 830.0)
    specs = (("あなたの扉\n（はずれ）", False, 0.0, 1.0), ("司会者が開けた扉\n（はずれ）", False, 1.0, 0.0), ("残った扉\n（当たり）", True, 1.0, 0.0))
    for i, (lab, car, op, fr) in enumerate(specs):
        al = ease_out(clamp01((u - 0.15 - 0.25 * i) / 0.3))
        if al <= 0:
            continue
        door(ctx, xs[i], y, w, h, None, op, 0.0, car, 0.0, fr, t, a=al)
        text(ctx, lab, xs[i], y + h + 58, 30, RED if car else INK, alpha=al)
    return


def draw_reasons(ctx, t):
    a = clamp01((t - T_RS) / 0.3) * (1 - clamp01((t - T_TW) / 0.3))
    if a <= 0:
        return
    r = results()
    u = t - T_RS
    ctx.push_group()
    bx0, bw, by, bh = 100.0, 830.0, 690.0, 104.0
    seg1 = bw * r["st"] / N_TRIAL                                       # 最初に当たりを選んだ回（選び直すとはずれ）
    seg2 = bw - seg1
    text(ctx, "1万回を、最初に選んだ扉で分ける", 580, 640, 38, INK, alpha=ease_out(clamp01(u / 0.3)))
    for (x0_, wd, col, dcol, num, lab1, lab2) in (
            (bx0, seg1, STC, STC_D, r["st"], "最初に当たりを\n選んだ回", "選び直すと、はずれ"),
            (bx0 + seg1, seg2, SWC, SWC_D, r["sw"], "最初にはずれを\n選んだ回", "選び直すと、当たり")):
        f = ease_out(clamp01((u - 0.2) / 0.5))
        dim = 1.0
        if u >= 3.7:                                                    # 2枚目の間は 右（はずれを選んだ回）に注目
            dim = 0.4 if col == STC else 1.0
        rrect(ctx, x0_, by, wd * f, bh, 10)
        ctx.set_source_rgba(*hexrgb(col, 0.95 * dim))
        ctx.fill_preserve()
        _stroke(ctx, 3.4, INK, 0.9 * dim)
        ncol = "#ffffff"
        text(ctx, f"{num:,}回", x0_ + wd / 2, by + bh / 2, 42, ncol, alpha=f * dim)
        al = ease_out(clamp01((u - 0.7) / 0.35)) * dim
        text(ctx, lab1, x0_ + wd / 2, by + bh + 62, 34, dcol, alpha=al)
        text(ctx, lab2, x0_ + wd / 2, by + bh + 150, 34, RED if col == SWC else INK, alpha=al)
    if u >= 3.9:
        mini_door_row(ctx, t, u - 3.9)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    bottom_card(ctx, t, "rs1")
    bottom_card(ctx, t, "rs2")


def draw_twist_bars(ctx, t):
    a = clamp01((t - T_TWB) / 0.3) * (1 - clamp01((t - T_Q) / 0.35))
    if a <= 0:
        return
    r = results()
    u = t - T_TWB
    ctx.push_group()
    text(ctx, f"はずれが開いた{r['rh_n']:,}回で比べると", 580, 640, 40, INK)
    text(ctx, "（当たりが開いた回は数えない）", 580, 690, 32, PENCIL, bold=False)
    base = 1215.0
    sc_ = 4.8
    for cx, v, col, dcol, lab in ((290.0, r["rh_sw_rate"], SWC, SWC_D, "選び直す"), (700.0, r["rh_st_rate"], STC, STC_D, "そのまま")):
        f = ease_out(clamp01((u - 0.3) / 0.7))
        hgt = v * 100 * sc_ * f
        rrect(ctx, cx - 120, base - hgt, 240, max(hgt, 1), 12)
        ctx.set_source_rgba(*hexrgb(col, 0.95))
        ctx.fill_preserve()
        _stroke(ctx, 3.4, INK, 0.9)
        if f > 0.5:
            text(ctx, pct0(v), cx, base - hgt - 56, 110, dcol, alpha=min(1.0, (f - 0.5) * 2))
        text(ctx, lab, cx, base + 48, 44, dcol)
    yl = base - 50 * sc_
    ctx.set_dash([14, 10])
    ctx.move_to(110, yl)
    ctx.line_to(900, yl)
    _stroke(ctx, 3.4, RED, 0.8)
    ctx.set_dash([])
    text(ctx, "50%", 960, yl, 30, RED)
    if u >= 1.3:
        p = ease_out(clamp01((u - 1.3) / 0.4))
        text(ctx, "ほぼ同じ", 495, 800, 64, RED, alpha=p)
        note.pen_circle(ctx, 495, 800, 170, 54, RED, seed=93, width=6, progress=p)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    bottom_card(ctx, t, "tw2", 40)
    bottom_card(ctx, t, "tw3", 40, color="pink", fg=RED)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・三択（横1列）。その下に舞台（0秒目から動く）"""
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(840.0), 108.0)
        ys = (450, 546, 642)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q3[-1], sz)
        note.pen_line(ctx, 565 - w3 / 2 - 6, 642 + sz * 0.62, 565 + w3 / 2 + 6, 638 + sz * 0.62, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 740
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:                                           # 予想して！と 3・2・1（舞台の床の中央）
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = 540.0, 1325.0
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
    draw_stage_scene(ctx, t)
    draw_hist_scene(ctx, t)
    draw_reasons(ctx, t)
    draw_twist_bars(ctx, t)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------
def creak(mx, t0, vol=0.25):
    mx.add(t0, whoosh(0.35), vol * 0.7)
    mx.add(t0 + 0.3, blip(180, 0.1), vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 164.8, 196.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    creak(mx, 0.3)
    mx.add(T_R1 + 0.4, bell(784.0, 0.6), 0.3)                          # ルール①
    mx.add(T_R2 + 1.0, blip(660, 0.08), 0.35)                          # ②
    mx.add(T_R3A + 0.5, bell(659.3, 0.8), 0.3)                         # ③-1
    creak(mx, T_R3B + 0.9)                                             # ③-2
    mx.add(T_R3B + 1.7, blip(330, 0.12), 0.3)
    mx.add(T_R4 + 0.4, bell(880.0, 0.8), 0.35)                         # ④
    F = sample()
    mx.add(T_S0 + 0.4, bell(784.0, 0.6), 0.25)
    mx.add(T_S0 + 3.0, blip(660, 0.08), 0.35)
    creak(mx, T_S0 + 3.7)
    creak(mx, T_S0 + 5.5)
    mx.add(T_S0 + 6.1, bell(1046.5, 1.0), 0.45)
    mx.add(T_S0 + 6.2, blip(220, 0.12), 0.3)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                                # 1万回
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_RS + 0.4, bell(698.5, 0.8), 0.35)
    mx.add(T_RS + 4.2, bell(784.0, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                                     # ひねり
    creak(mx, T_TW + 1.3)
    mx.add(T_TW + 2.0, thump(), 0.35)
    mx.add(T_TWB + 1.3, bell(659.3, 0.8), 0.4)
    mx.add(T_TWB + 4.0, thump(), 0.4)
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


def run_checks():
    r = results()
    F = sample()
    rc = recount()
    checks = []
    # (1) 条件・数え直し
    checks.append(("回数 = 1万", float(r["a"]["n_valid"]), float(N_TRIAL), 0.0))
    checks.append(("当たりの合計: 選び直す＋そのまま = 1万（毎回どちらか片方だけ当たる）", float(r["sw"] + r["st"]), float(N_TRIAL), 0.0))
    checks.append(("そのままの当たり: 数え直し = monty_model.run", float(rc["stay"]), float(r["st"]), 0.0))
    checks.append(("選び直すの当たり: 数え直し = monty_model.run", float(rc["switch"]), float(r["sw"]), 0.0))
    checks.append(("ひねり: はずれが開いた回数 数え直し = monty_model.run", float(rc["rh_n"]), float(r["rh_n"]), 0.0))
    checks.append(("ひねり: そのままの当たり 数え直し = monty_model.run", float(rc["rh_stay"]), float(r["rh_st"]), 0.0))
    checks.append(("ひねり: 選び直すの当たり 数え直し = monty_model.run", float(rc["rh_switch"]), float(r["rh_sw"]), 0.0))
    checks.append(("画面: 選び直す 6,526回・そのまま 3,474回", float((r["sw"], r["st"]) == (6526, 3474)), 1.0, 0.0))
    checks.append(("画面: ひねり 49%と51%（6,815回）", float((pct0(r["rh_sw_rate"]), pct0(r["rh_st_rate"]), r["rh_n"]) == ("49%", "51%", 6815)), 1.0, 0.0))
    # 確率のルールだけから出る値（選び直す = 3分の2）。この1万回は たまたま少なめ（約3σ）なので、広めの許容で照合する
    checks.append(("選び直すの当たる割合 ≒ 3分の2（確率のルール。許容 2ポイント）", r["a"]["switch_rate"], 2 / 3, 0.02))
    checks.append(("そのままの当たる割合 ≒ 3分の1（確率のルール。許容 2ポイント）", r["a"]["stay_rate"], 1 / 3, 0.02))
    checks.append(("ひねり: でたらめに開けて はずれだった回の割合 ≒ 3分の2", r["rh_n"] / N_TRIAL, 2 / 3, 0.02))
    checks.append(("ひねり: 選び直す・そのまま とも ≒ 2分の1（許容 2ポイント）", float(abs(r["rh_sw_rate"] - 0.5) < 0.02 and abs(r["rh_st_rate"] - 0.5) < 0.02), 1.0, 0.0))
    # (2) 答え
    key, d = answer_by_rule(r["a"]["switch_rate"], r["a"]["stay_rate"])
    checks.append(("規則の答え = 選び直す", float(key == "選び直す"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 選び直す・ほぼ同じ・そのまま の順", float(LABELS == ["選び直す", "ほぼ同じ", "そのまま"]), 1.0, 0.0))
    for dd, k_ in ((0.0, "ほぼ同じ"), (0.019, "ほぼ同じ"), (0.021, "選び直す"), (-0.021, "そのまま")):
        checks.append((f"規則の道具: 差 {dd:+.3f} → {k_}", float(answer_by_rule(0.5 + dd, 0.5)[0] == k_), 1.0, 0.0))
    # (3) 見本は1万回の最初の1回そのもの
    checks.append(("見本: 当たり=扉3・あなた=扉1・司会者が開けた=扉2（monty_model.run の1回目）",
                   float((F["car"], F["pick"], F["opened"]) == (2, 0, 1)), 1.0, 0.0))
    checks.append(("見本: 数え直しの1回目と 当たり・あなた・司会者が同じ", float((rc["car0"], rc["pick0"], rc["opened0"]) == (F["car"], F["pick"], F["opened"])), 1.0, 0.0))
    checks.append(("見本: 選び直す先 = 扉3 で当たり（3 − あなた − 開けた）", float(F["switch_to"] == F["car"] == 2), 1.0, 0.0))
    checks.append(("見本: そのまま = 扉1 ではずれ", float(F["pick"] != F["car"]), 1.0, 0.0))
    checks.append(("見本: 司会者が開けた扉は はずれで、あなたの扉でもない", float(F["opened"] != F["car"] and F["opened"] != F["pick"]), 1.0, 0.0))
    checks.append(("見本: 1万回の数え上げの1回目 = 選び直すで当たり", float(bool(r["a"]["switch_win_arr"][0]) and not bool(r["a"]["stay_win_arr"][0])), 1.0, 0.0))
    checks.append(("見本の絵の状態: 当たりの扉=3・あなたの枠=扉1・開く扉=扉2・選び直す先=扉3",
                   float(stage_state(T_S0 + 7.0)["car"] == 2 and stage_state(T_S0 + 7.0)["frame"][0] > 0.9 and stage_state(T_S0 + 4.8)["open"][1] > 0.9
                         and stage_state(T_S0 + 7.0)["open"][2] > 0.9), 1.0, 0.0))
    checks.append(("ルール説明の並び: 司会者が開ける扉は 当たりでもあなたの扉でもない（当たり=扉2・あなた=扉1・開ける=扉3）",
                   float(DEMO["opened"] != DEMO["car"] and DEMO["opened"] != DEMO["pick"] and DEMO["car"] != DEMO["pick"]), 1.0, 0.0))
    # (4) 問い（3行）が収まる
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q3) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(450 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行の文: 「扉が3つ。1つだけ当たり。／司会者がはずれを1つ開けた。／選び直す？そのまま？」",
                   float(BIG_Q3 == ["扉が3つ。1つだけ当たり。", "司会者がはずれを1つ開けた。", "選び直す？そのまま？"]), 1.0, 0.0))
    # (5) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_.replace("\n", ""))
        need = max(0.12 * n_ + 1.0, 0.5 + max(len(x) for x in s_.split("\n")) / 6.0)
        checks.append((f"札「{s_.replace(chr(10), '')}」が読み切れる（{tb - ta:.2f}秒 / 要る {need:.2f}秒）", float(tb - ta >= need - 1e-9), 1.0, 0.0))
    for (s_, di, row, col, ta, tb) in DLABELS:
        need = 0.5 + len(s_) / 6.0
        checks.append((f"扉の下の言葉「{s_}」（扉{di + 1}・{ta:.1f}秒〜）が読み切れる（{tb - ta:.1f}秒 / 要る {need:.1f}秒）", float(tb - ta >= need + 0.3), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("ルールの札は4つ（①②③④）。③は札2枚（司会者は知っている／はずれを必ず1つ開ける）＋補足の付箋",
                   float(all(k in CARDS for k in ("r1", "r2", "r3a", "r3b", "r3c", "r4"))), 1.0, 0.0))
    checks.append(("ルール③-1 がいちばんゆっくり（札の秒数が、①②③-2④より 短くない → ③-1 の場面が ①②④ より長い）",
                   float((T_R3B - T_R3A) > max(T_R2 - T_R1, T_R3A - T_R2, T_S0 - T_R4)), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万回の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("長さ 55〜59秒（lint は60秒未満）", float(55.0 <= DURATION <= 59.0), 1.0, 0.0))
    # (6) 冒頭の動き
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
    F = sample()
    print(f"長さ {DURATION:.1f}秒  ルール {T_R1:.1f}/{T_R2:.1f}/{T_R3A:.1f}/{T_R3B:.1f}/{T_R4:.1f}  見本 {T_S0:.1f}-{T_H0:.1f}  1万回 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}/{T_TWB:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  当たり: 選び直す {r['sw']:,}回・そのまま {r['st']:,}回  答え: {r['key']}（差 {r['d']:+.3f}）")
    print(f"  ひねり: はずれが開いた {r['rh_n']:,}回のうち 選び直す {pct0(r['rh_sw_rate'])}・そのまま {pct0(r['rh_st_rate'])}")
    print(f"  見本: 1回目  当たり=扉{F['car'] + 1}  あなた=扉{F['pick'] + 1}  司会者=扉{F['opened'] + 1}")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2,
          T_R1 + 1.5, T_R2 + 1.9, T_R3A + 2.2, T_R3B + 1.2, T_R3B + 3.3, T_R4 + 2.0,
          T_S0 + 1.5, T_S0 + 3.4, T_S0 + 4.8, T_S0 + 7.2,
          T_HC + 1.0, T_REV + 1.8,
          T_RS + 2.5, T_RS + 5.8,
          T_TW + 2.4, T_TWB + 3.0, T_TWB + 6.5,
          T_Q + 1.8]
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
