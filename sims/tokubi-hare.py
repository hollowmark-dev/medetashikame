"""晴れてほしい予定、晴れの特異日？ふつうの日？ 1万回の天気で比べる。— 2026-11-08 作成（公開予定 11.22・ナレーションなし・50〜58秒）

計算の本体は sims/tokubi_model.py（晴れの決め方・比べる日・seed 131・答えの決め方は、計算の前にそのファイルの docstring に固定してある。ここでは変えない）。
この sim は「結果を読んで絵にする」ところ。

【データ】 気象庁 過去の気象データ（東京・日ごとの日照時間）10〜11月、1961〜2025年の65年（data/jma_tokyo/）。
  晴れ＝その日の日照時間が、昼の長さ（可照時間）の40%以上。11月3日は65年中42年（65%）、前後7日（10/27〜11/10のうち11/3以外の14日）の平均は56%。
【置き方】（tokubi_model.py の docstring と同じ。結果を見て変えていない）
  ・「どの日も、前後の日と同じ晴れやすさ（56%）」だったとして、65年のうち晴れる年の数を、くじで1万回作る（seed 131・二項分布）。
  ・1回 = 65年分の天気を1回作り直すこと。実際の42年が、たまたまでどれだけ出るかを数える。
【答えの決め方】（answer_by_rule。計算の前に固定）
  実際の晴れた年数が、たまたまの1万回のうち上位2.5%に入るほど多ければ「特異日を選ぶ」、下位2.5%に入るほど少なければ「ふつうの日を選ぶ」、どちらでもなければ「ほぼ同じ」。
【見本の1回】 1万回の中の最初の1回そのもの（seed 131 の1回目 = 晴れた年の数）。年ごとの並びはくじではなく、その数だけ晴れを散らして描く（run_checks で数を確かめる）。
【ひねり】 最近30年（1996〜2025年）は 11月3日 57%（17/30年）・前後の日 56%。tokubi_model.run(sun, 1996, 2025) で数え直す。
  「10〜11月の61日を同じ晴れやすさにすると、11月3日くらい晴れやすく見える日が、中央値で3日できる」は時間の都合で画面に入れていない（報告に書く）。
【言い方】 「中央値」は出さない。画面に「計算での見立て」は出さない（資料と確率のルールで決まるため）。代わりに出典の札を出す。

問い: 「晴れてほしい予定。/ 晴れの特異日を選ぶ？/ ふつうの日を選ぶ？」
選択肢: A 特異日（11月3日）／ B ほぼ同じ ／ C ふつうの日（正解の記号は B。run_checks で確かめる）
見せ方: 冒頭（問い・晴れの日に出かける2人）→ 特異日とは → データ（東京65年・晴れの数え方）→ 実際の記録（カレンダー）→ 問い → 見本の1回 → 1万回 → 答え → 理由 → ひねり（最近30年）→ 締め
締め: 「あなたの町にも、晴れの特異日の言い伝えはありますか？」
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tokubi_model as mm  # noqa: E402

SLUG = "tokubi-hare"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIAL = mm.R
CNT = 2.0                                           # 1万回の数え上げの秒数
SRC = "出典: 気象庁ホームページ（過去の気象データ）"
NEAR_COLS = [(10, 27), (10, 28), (10, 29), (10, 30), (10, 31)] + [(11, d) for d in range(1, 11)]   # 15日（11/3 は index 7）
COL3 = NEAR_COLS.index((11, 3))
YEARS = list(range(mm.Y0, mm.Y1 + 1))


def answer_by_rule(p_upper, p_lower):
    """答えの決め方（計算の前に固定）。上位2.5%に入れば 特異日／下位2.5%に入れば ふつうの日／どちらでもなければ ほぼ同じ"""
    if p_upper <= 0.025:
        return "特異日を選ぶ"
    if p_lower <= 0.025:
        return "ふつうの日を選ぶ"
    return "ほぼ同じ"


def pct0(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


_RES = {}


def results():
    """1万回の結果。記録（年×日の晴れ）・1万回のくじ・最近30年"""
    if _RES:
        return _RES["r"]
    sun, _summ = mm.load()
    res = mm.run(sun)
    res30 = mm.run(sun, 1996, 2025)
    k3, n3 = mm.rate(sun, (11, 3))
    near = [mm.rate(sun, md) for md in mm.NEAR]
    p0 = sum(a for a, _ in near) / sum(b for _, b in near)
    sims = np.random.default_rng(131).binomial(n3, p0, N_TRIAL)       # mm.run と同じ seed・同じ最初の呼び出し
    lo, hi = int(sims.min()), int(sims.max())
    ks = list(range(lo, hi + 1))
    onehot = np.stack([(sims == v) for v in ks]).astype(np.int32)
    cum = np.cumsum(onehot, axis=1)                                   # 各棒の、n回目までの回数
    cal = [[sun.get((y, m, d)) for (m, d) in NEAR_COLS] for y in YEARS]   # 年×日（True 晴れ / False / None 記録なし）
    y30 = list(range(1996, 2026))
    s3_30 = [bool(sun[(y, 11, 3)]) for y in y30]
    _RES["r"] = dict(sun=sun, res=res, res30=res30, k3=k3, n3=n3, p0=p0, sims=sims, ks=ks, cum=cum, cal=cal, y30=y30, s3_30=s3_30,
                     cnt_ge=int((sims >= k3).sum()), cnt_le=int((sims <= k3).sum()), dist={v: int((sims == v).sum()) for v in ks})
    r = _RES["r"]
    r["key"] = answer_by_rule(float((sims >= k3).mean()), float((sims <= k3).mean()))
    return r


def sample_tiles(k, n=65, seed=5):
    """見本の1回: 65年のうち k 年を晴れにして散らす（数 k は 1万回の最初の1回そのもの。並びは描くための散らし）"""
    idx = np.random.default_rng(seed).permutation(n)[:k]
    s = np.zeros(n, bool)
    s[idx] = True
    return s


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    print(f"{N_TRIAL}回  11月3日 {r['k3']}/{r['n3']}年 ({r['k3'] / r['n3']:.1%})  前後7日 {r['p0']:.3f}  答え: {r['key']}")
    print(f"  たまたま{r['k3']}年以上: {r['cnt_ge']:,}回 ({r['cnt_ge'] / N_TRIAL:.2%})  以下: {r['cnt_le']:,}回  晴れた年の数 {r['ks'][0]}〜{r['ks'][-1]}")
    print(f"  見本: 1回目 {int(r['sims'][0])}年  最初の10回 {[int(v) for v in r['sims'][:10]]}")
    print(f"  最近30年: {sum(r['s3_30'])}/30年 ({r['res30']['rate3']:.1%})  前後 {r['res30']['near_rate']:.3f}  たまたま以上 {r['res30']['p_upper']:.1%}")
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
note.DATE = "11.22"                                  # 日付欄（公開予定日）

SUN_Y, SUN_D = "#f6c945", "#b8860b"                  # 晴れ（黄）
CLD, CLD_D = "#cfd8e3", "#6b7a8f"                    # 晴れでない（灰青）
SKY, SKY_D = "#bfe3f5", "#3f7fb5"
ORG, ORG_D = "#e0801f", "#a85a0a"                    # 11月3日（橙）
BLU, BLU_D = "#3f7fb5", "#2a5a85"                    # 前後の日（青）
GRY, GRY_D = "#a9a395", "#6f695b"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は B（2番目）
LABELS = ["特異日（11月3日）", "ほぼ同じ", "ふつうの日"]
KEY_LABEL = {"特異日を選ぶ": "特異日（11月3日）", "ほぼ同じ": "ほぼ同じ", "ふつうの日を選ぶ": "ふつうの日"}
KEY_SAY = {"特異日を選ぶ": "特異日", "ほぼ同じ": "ほぼ同じ", "ふつうの日を選ぶ": "ふつうの日"}
CORRECT = 1

BIG_Q3 = ["晴れてほしい予定。", "晴れの特異日を選ぶ？", "ふつうの日を選ぶ？"]      # 1コマ目の3行（同じ大きさ）
BIG_Q = ["晴れてほしい予定。", "特異日を選ぶ？ふつうの日を選ぶ？"]                # 定位置（上）の2行
DETAIL_RULE = "比べるのは、11月3日と、前後の日"
DETAIL = "東京の65年分の記録で確かめる"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (1.8, 2.6, 3.4)                              # 3・2・1
T_MOVE, T_GO = 4.3, 4.7
CY_INTRO = 910.0                                    # 屋外の絵の上端 y
PX = (290.0, 730.0)                                 # 左（特異日）・右（ふつうの日）の人の中心 x
MID = 510.0
FYR, K_ST = 440.0, 4.4                              # 足もと y（cy から）・大きさ（身長 100×K_ST px）
SX = 570.0                                          # 付箋の中心 x（文字が x≤930 に収まる幅 720 まで）


def setup():
    global T_E, T_D, T_C, T_ASK, T_S, T_H0, T_HC, T_REV, T_RS, T_TW, T_Q, DURATION, SCENES
    T_E = T_GO                                      # 特異日とは
    T_D = T_E + 4.4                                 # データ（東京65年・晴れの数え方）
    T_C = T_D + 5.5                                 # 実際の記録（カレンダー）
    T_ASK = T_C + 6.5                               # 問い
    T_S = T_ASK + 4.4                               # 見本の1回
    T_H0 = T_S + 7.7                                # 1万回
    T_HC = T_H0 + 0.5                               # 数え上げ始め
    T_REV = T_H0 + 5.0                              # 答え
    T_RS = T_REV + 6.3                              # 理由
    T_TW = T_RS + 5.5                               # ひねり（最近30年）
    T_Q = T_TW + 5.0                                # 締め
    DURATION = T_Q + 3.5
    SCENES = [("冒頭（問い・晴れの日に出かける2人）", 0.0, T_GO), ("特異日とは", T_E, T_D), ("データ（東京65年・晴れの数え方）", T_D, T_C),
              ("実際の記録（カレンダー）", T_C, T_ASK), ("問い", T_ASK, T_S), ("見本の1回", T_S, T_H0),
              ("1万回", T_H0, T_REV), ("答え", T_REV, T_RS), ("理由", T_RS, T_TW), ("ひねり 最近30年", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()

# 見本の1回: 時間割（見本の秒 u = t − T_S）
U_A = (0.3, 4.6)                                    # 付箋A「どの日も同じ晴れやすさ（56%）だったら」
U_B = (1.6, 4.6)                                    # 付箋B「65年分の天気を、1万回作り直す」
U_FREEZE = 4.6                                      # 見本に落ち着く
U_C = (5.0, 7.5)                                   # 付箋C「たとえば、この1回では…」

STK_E1 = "特異日＝その日だけ、\nなぜか晴れやすいと言われる日"
STK_E2 = "11月3日は、\n晴れの特異日として有名"
STK_D1 = "東京の65年分の記録\n（1961〜2025年）"
STK_D2 = "晴れ＝日照時間が、\n昼の長さの4割以上"
STK_ASK1 = "この差は、本当に\n11月3日だから？"
STK_ASK2 = "たまたまでも、\nこのくらいの差は出る？"
STK_S1 = "どの日も同じ晴れやすさ\n（56%）だったら、"
STK_S2 = "65年分の天気を、\n1万回作り直す。"
STK_RS1 = "65年は、\n天気の比べっこには短い。"
STK_RS2 = "たまたまの差が、\n特別な日に見えてしまう。"
STK_TW1 = "最近30年（1996〜2025年）\nでは、11月3日は57%。"
STK_TW2 = "前後の日も56%で、\nほぼ同じ。"
STK_Q = "あなたの町にも、\n晴れの特異日の\n言い伝えはありますか？"


def stk_c():
    r = results()
    return f"たとえば、この1回では\nたまたま{int(r['sims'][0])}年晴れた。"


def stk_b():
    r = results()
    return f"どの日も同じ晴れやすさでも、\n{r['k3']}年以上晴れる回は\n1万回のうち{r['cnt_ge']:,}回。"


STK_B2 = "たまたまでも、\n10回に1回は出る差。\n特異日とまでは言えない。"


def cards():
    """札: (1行の文, 出る秒, 消える秒)。1行ごとに「1文字0.12秒＋1秒以上」と 公開前チェックの「0.5秒＋文字数÷6秒」の両方より長く映す"""
    out = []

    def add(s, ta, tb):
        for ln in s.split("\n"):
            out.append((ln, ta, tb))

    add(STK_E1, T_E + 0.2, T_E + 3.75)
    add(STK_E2, T_E + 1.6, T_E + 4.15)
    add(STK_D1, T_D + 0.3, T_D + 5.25)
    add(STK_D2, T_D + 2.0, T_D + 5.25)
    add(STK_ASK1, T_ASK + 0.2, T_S - 0.2)
    add(STK_ASK2, T_ASK + 1.6, T_S - 0.2)
    add(STK_S1, T_S + U_A[0], T_S + U_A[1])
    add(STK_S2, T_S + U_B[0], T_S + U_B[1])
    add(stk_c(), T_S + U_C[0], T_S + U_C[1])
    add(f"答えは『{KEY_SAY[results()['key']]}』。", T_REV + 0.2, T_RS - 0.1)
    add(stk_b(), T_REV + 0.6, T_REV + 3.5)
    add(STK_B2, T_REV + 3.6, T_RS - 0.1)
    add(STK_RS1, T_RS + 0.3, T_TW - 0.2)
    add(STK_RS2, T_RS + 2.7, T_TW - 0.2)
    add(STK_TW1, T_TW + 0.3, T_Q - 0.2)
    add(STK_TW2, T_TW + 2.5, T_Q - 0.2)
    add(STK_Q, T_Q + 0.3, DURATION - 0.2)
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




# ---------- 絵: 天気の小物 ----------
def glyph_sun(ctx, x, y, r, rot=0.0, a=1.0):
    """太陽（光線がまわる）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    for i in range(10):
        ang = i * math.pi / 5
        ctx.move_to(math.cos(ang) * r * 1.28, math.sin(ang) * r * 1.28)
        ctx.line_to(math.cos(ang) * r * 1.7, math.sin(ang) * r * 1.7)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    _stroke(ctx, max(3.0, r * 0.17), SUN_D, 0.95 * a)
    ctx.new_path()
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SUN_Y, a))
    ctx.fill_preserve()
    _stroke(ctx, max(2.5, r * 0.07), INK, 0.9 * a)
    ctx.restore()


def glyph_cloud(ctx, x, y, r, a=1.0, col=CLD):
    """くも"""
    if a <= 0:
        return
    parts = ((-0.9, 0.2, 0.62), (-0.2, -0.28, 0.82), (0.55, 0.0, 0.7), (1.05, 0.28, 0.5))
    for phase in (0, 1):
        for dx, dy, rr in parts:
            ctx.new_path()
            ctx.arc(x + dx * r, y + dy * r, rr * r, 0, 2 * math.pi)
            if phase == 0:
                ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
                ctx.set_line_width(max(3.0, r * 0.1) * 2)
                ctx.stroke()
            else:
                ctx.set_source_rgba(*hexrgb(col, a))
                ctx.fill()
        if phase == 0:
            continue
    core.rrect(ctx, x - 1.5 * r, y + 0.2 * r, 3.1 * r, 0.6 * r, 0.3 * r)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill()


def tile(ctx, x, y, s, sunny, a=1.0):
    """年ごとの天気の升（大きいときは絵、小さいときは色だけ）。(x, y) は左上"""
    if a <= 0:
        return
    if s < 34:
        rrect(ctx, x, y, s, s, min(4, s / 4))
        ctx.set_source_rgba(*hexrgb(SUN_Y if sunny else CLD, a))
        ctx.fill()
        return
    rrect(ctx, x, y, s, s, 8)
    ctx.set_source_rgba(*hexrgb("#fff3b0" if sunny else "#e3e9f0", a))
    ctx.fill_preserve()
    _stroke(ctx, 2.4, PENCIL, 0.8 * a)
    if sunny:
        glyph_sun(ctx, x + s / 2, y + s / 2, s * 0.22, 0.0, a)
    else:
        glyph_cloud(ctx, x + s / 2 - s * 0.02, y + s / 2 + s * 0.02, s * 0.2, a)


def draw_die(ctx, x, y, s, n, rot=0.0, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22 * a)
    rrect(ctx, -s / 2 + 4, -s / 2 + 7, s, s, s * 0.18)
    ctx.fill()
    rrect(ctx, -s / 2, -s / 2, s, s, s * 0.18)
    ctx.set_source_rgba(1, 1, 1, 0.98 * a)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9 * a)
    pips = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
            5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[n]
    for px, py in pips:
        ctx.new_path()
        ctx.arc(px * s * 0.26, py * s * 0.26, s * 0.075, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(RED if n == 1 else INK, a))
        ctx.fill()
    ctx.restore()


def calendar_prop(ctx, cx, cy, w, h, label, a=1.0, size=52):
    """日めくり"""
    ctx.save()
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22 * a)
    rrect(ctx, cx - w / 2 + 5, cy - h / 2 + 8, w, h, 10)
    ctx.fill()
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, 10)
    ctx.set_source_rgba(1, 1, 1, 0.98 * a)
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9 * a)
    ctx.rectangle(cx - w / 2 + 2, cy - h / 2 + 2, w - 4, 26)
    ctx.set_source_rgba(*hexrgb("#d9534f", a))
    ctx.fill()
    text(ctx, label, cx, cy + 12, size, INK, alpha=a)
    ctx.restore()


# ---------- 絵: 冒頭（晴れの日に出かける2人） ----------
def draw_outdoor(ctx, t):
    a = 1 - ease(clamp01((t - T_GO) / 0.3)) if t >= T_GO else 1.0
    if a <= 0:
        return
    cy = CY_INTRO
    wp = ease(clamp01(t / 0.8))                                       # 空が左から右へ広がる（冒頭の動き）
    rise = 1 - ease(clamp01(t / 0.9))                                 # 2人が塀の陰から立ち上がる
    ctx.push_group()
    ctx.save()
    ctx.rectangle(60, cy - 35, 960 * wp, 600)
    ctx.clip()
    rrect(ctx, 60, cy - 35, 960, 580, 24)
    ctx.set_source_rgba(*hexrgb(SKY))
    ctx.fill_preserve()
    _stroke(ctx, 3, PENCIL, 0.6)
    # 太陽（光線がまわる）とくも（右へ流れる）
    glyph_sun(ctx, 510, cy + 128, 66, t * 0.6)
    for i, (bx, by, rr, sp) in enumerate(((160, 40, 46, 38.0), (610, 20, 40, 26.0), (860, 120, 54, 32.0), (330, 205, 38, 22.0))):
        cx_ = 60 + ((bx - 60 + t * sp) % 1060) - 40
        glyph_cloud(ctx, cx_, cy + by + 40, rr, 0.95, "#ffffff")
    # 丘
    ctx.new_path()
    ctx.move_to(60, cy + 330)
    ctx.curve_to(300, cy + 270, 600, cy + 340, 1020, cy + 290)
    ctx.line_to(1020, cy + 545)
    ctx.line_to(60, cy + 545)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#a7d49a"))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.6)
    for ci, x in enumerate(PX):
        student(ctx, x, cy + FYR + 150 * rise, K_ST, ci, t, 1 if ci == 0 else -1, 0.0)
    # 塀
    top = cy + 262
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22)
    rrect(ctx, 76, top + 10, 880, 290, 14)
    ctx.fill()
    rrect(ctx, 70, top, 880, 283, 14)
    ctx.set_source_rgba(*hexrgb("#dcb98f"))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    for r_ in range(1, 5):                                            # れんがの線
        yy = top + r_ * 56
        ctx.move_to(72, yy)
        ctx.line_to(948, yy)
        _stroke(ctx, 2.0, "#8e6636", 0.35)
        for k in range(0, 9):
            xx = 70 + k * 110 + (55 if r_ % 2 else 0)
            ctx.move_to(xx, yy - 56)
            ctx.line_to(xx, yy)
        _stroke(ctx, 2.0, "#8e6636", 0.3)
    calendar_prop(ctx, PX[0], cy + 380, 190, 120, "11/3", 1.0)
    calendar_prop(ctx, PX[1] - 58, cy + 380, 108, 120, "11/2", 1.0, 36)
    calendar_prop(ctx, PX[1] + 58, cy + 380, 108, 120, "11/4", 1.0, 36)
    for s, (lab, col, dcol, lt) in enumerate((("特異日", ORG, ORG_D, "#fbe7cf"), ("ふつうの日", BLU, BLU_D, "#d9e8f5"))):
        x, y = PX[s], cy + 500
        rrect(ctx, x - 160, y - 33, 320, 66, 16)
        ctx.set_source_rgba(*hexrgb(lt, 0.97))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.set_line_width(5)
        ctx.stroke()
        text(ctx, lab, x, y, 44, dcol)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 絵: 場面の共通 ----------
def fade(t, ta, tb, f=0.25):
    return clamp01((t - ta) / f) * (1 - clamp01((t - tb) / f))


def grouped(ctx, a, fn, *args):
    if a <= 0:
        return
    ctx.push_group()
    fn(ctx, *args)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def number_block(ctx, cx, label, big, small, dcol, ys, bsize=100, a=1.0):
    yl, yb, ys_ = ys
    text(ctx, label, cx, yl, 32, dcol, alpha=a)
    text(ctx, big, cx, yb, bsize, dcol, alpha=a)
    if small:
        text(ctx, small, cx, ys_, 30, INK, bold=False, alpha=a)


# ---------- 絵: 特異日とは ----------
def scene_e(ctx, t):
    u = t - T_E
    cx, top = SX, 625.0
    p = ease_out(clamp01(u / 0.45))
    ctx.save()
    ctx.translate(cx, top + 220)
    ctx.scale(0.8 + 0.2 * p, 0.8 + 0.2 * p)
    ctx.translate(-cx, -(top + 220))
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22)
    rrect(ctx, cx - 240 + 8, top + 12, 480, 430, 14)
    ctx.fill()
    rrect(ctx, cx - 240, top, 480, 430, 14)
    ctx.set_source_rgba(1, 1, 1, 0.98)
    ctx.fill_preserve()
    _stroke(ctx, 5, INK, 0.9)
    ctx.rectangle(cx - 238, top + 2, 476, 92)
    ctx.set_source_rgba(*hexrgb("#d9534f"))
    ctx.fill()
    text(ctx, "11月", cx, top + 48, 64, "#ffffff")
    text(ctx, "3日", cx, top + 262, 250, INK)
    ctx.restore()
    glyph_sun(ctx, cx + 215, top + 40, 62, u * 0.7)                        # 太陽が角でまわる
    if u >= 0.9:                                                           # 「特異日」の赤い判
        q = ease_out(clamp01((u - 0.9) / 0.3))
        ctx.save()
        ctx.translate(cx + 120, top + 385)
        ctx.rotate(-0.13)
        text(ctx, "特異日", 0, 0, 72, RED, alpha=q)
        note.pen_circle(ctx, 0, 0, 142, 54, RED, seed=9, width=7, progress=clamp01((u - 1.0) / 0.5), alpha=q)
        ctx.restore()
    stk(ctx, STK_E1, 1190, 40, a=win(t, T_E + 0.2, T_E + 3.75, 0.3, 0.25))
    stk(ctx, STK_E2, 1365, 40, a=win(t, T_E + 1.6, T_E + 4.15, 0.3, 0.25), color="pink")


# ---------- 絵: データ ----------
def scene_d(ctx, t):
    u = t - T_D
    # 65年分のカレンダー（13×5）
    s_, st = 58.0, 64.0
    x0, y0 = SX - (13 * st - 6) / 2, 625.0
    for i in range(65):
        r_, c_ = divmod(i, 13)
        p = ease_out(clamp01((u - 0.3 - 1.6 * i / 65) / 0.2))
        if p <= 0:
            continue
        x, y = x0 + c_ * st, y0 + r_ * st + 8 * (1 - p)
        ctx.save()
        rrect(ctx, x, y, s_, s_, 6)
        ctx.set_source_rgba(1, 1, 1, 0.97 * p)
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.85 * p)
        ctx.rectangle(x + 1.5, y + 1.5, s_ - 3, 16)
        ctx.set_source_rgba(*hexrgb("#d9534f", p))
        ctx.fill()
        glyph_sun(ctx, x + s_ / 2, y + 37, 10.0, 0.0, p)
        ctx.restore()
    # 晴れの数え方: 昼の長さの帯に、4割
    bx0, bx1, by0, by1 = 100.0, 900.0, 995.0, 1045.0
    pa = ease_out(clamp01((u - 2.0) / 0.4))
    text(ctx, "昼の長さ", bx0, 968, 30, INK, align="left", alpha=pa)
    if pa > 0:
        rrect(ctx, bx0, by0, bx1 - bx0, by1 - by0, 10)
        ctx.set_source_rgba(1, 1, 1, 0.9 * pa)
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.85 * pa)
        text(ctx, "日の出", bx0, 1078, 28, PENCIL, align="left", bold=False, alpha=pa)
        text(ctx, "日の入り", bx1, 1078, 28, PENCIL, align="right", bold=False, alpha=pa)
    pf = ease_out(clamp01((u - 2.5) / 0.8))
    if pf > 0:
        wfill = 0.4 * (bx1 - bx0) * pf
        rrect(ctx, bx0, by0, wfill, by1 - by0, 10)
        ctx.set_source_rgba(*hexrgb(SUN_Y, 0.98))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        xe = bx0 + 0.4 * (bx1 - bx0)
        if pf > 0.95:
            text(ctx, "ここまで＝昼の4割", xe + 12, 1078, 30, SUN_D, align="left")
            note.pen_line(ctx, xe, by0 - 10, xe, by1 + 12, RED, seed=4, width=6, progress=1.0)
    stk(ctx, STK_D1, 1192, 40, a=win(t, T_D + 0.3, T_D + 5.25, 0.3, 0.25))
    stk(ctx, STK_D2, 1340, 40, a=win(t, T_D + 2.0, T_D + 5.25, 0.3, 0.25), color="mint")


def source_tag(ctx, t):
    a = win(t, T_D + 0.2, T_ASK - 0.2, 0.3, 0.3)
    if a > 0:
        text(ctx, SRC, SX, 1430, 26, PENCIL, bold=False, alpha=a)


# ---------- 絵: 実際の記録（カレンダー） ----------
G_CW, G_CH = 52.0, 9.4
G_X0, G_Y0 = 150.0, 635.0


def scene_c(ctx, t):
    r = results()
    u = t - T_C
    gx, gy = G_X0, G_Y0
    nrow = len(YEARS)
    for ci in (0, COL3, len(NEAR_COLS) - 1):
        m_, d_ = NEAR_COLS[ci]
        text(ctx, f"{m_}/{d_}", gx + ci * G_CW + G_CW / 2, 615, 26, RED if ci == COL3 else INK, alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    pr = ease_out(clamp01((u - 0.2) / 0.3))
    text(ctx, str(YEARS[0]), gx - 10, gy + 8, 24, PENCIL, align="right", bold=False, alpha=pr)
    text(ctx, str(YEARS[-1]), gx - 10, gy + nrow * G_CH - 8, 24, PENCIL, align="right", bold=False, alpha=pr)
    for yi in range(nrow):
        tr = 0.2 + 2.2 * yi / nrow
        if u < tr:
            break
        for ci in range(len(NEAR_COLS)):
            v = r["cal"][yi][ci]
            if v is None:
                continue
            ctx.rectangle(gx + ci * G_CW + 1, gy + yi * G_CH + 0.6, G_CW - 2, G_CH - 1.2)
            ctx.set_source_rgba(*hexrgb(SUN_Y if v else "#dfe5ec"))
            ctx.fill()
    gb = gy + nrow * G_CH
    if u >= 2.9:                                                           # 11月3日の列に赤い枠
        q = ease_out(clamp01((u - 2.9) / 0.4))
        rrect(ctx, gx + COL3 * G_CW - 3, gy - 7, G_CW + 6, nrow * G_CH + 14, 6)
        _stroke(ctx, 6, RED, 0.95 * q)
    # 凡例
    la = ease_out(clamp01((u - 2.4) / 0.3))
    rrect(ctx, 330, 1262, 30, 30, 5)
    ctx.set_source_rgba(*hexrgb(SUN_Y, la))
    ctx.fill()
    text(ctx, "晴れ", 372, 1277, 30, INK, align="left", alpha=la)
    rrect(ctx, 520, 1262, 30, 30, 5)
    ctx.set_source_rgba(*hexrgb("#dfe5ec", la))
    ctx.fill_preserve()
    _stroke(ctx, 2, PENCIL, 0.7 * la)
    text(ctx, "晴れでない", 562, 1277, 30, INK, align="left", alpha=la)
    ys = (1318, 1380, 0)
    if u >= 3.2:
        q = ease_out(clamp01((u - 3.2) / 0.4))
        number_block(ctx, 350, f"11月3日（{r['k3']}年／{r['n3']}年）", pct0(r["k3"] / r["n3"]), "", ORG_D, ys, 84, q)
    if u >= 4.6:
        q = ease_out(clamp01((u - 4.6) / 0.4))
        number_block(ctx, 780, "前後7日の平均", pct0(r["p0"]), "", BLU_D, ys, 84, q)


# ---------- 絵: 問い ----------
def scene_ask(ctx, t):
    r = results()
    u = t - T_ASK
    ys = (700, 810, 880)
    number_block(ctx, 350, "11月3日", pct0(r["k3"] / r["n3"]), f"{r['k3']}年／{r['n3']}年", ORG_D, ys, 130, 1.0)
    number_block(ctx, 790, "前後7日の平均", pct0(r["p0"]), "前後の14日", BLU_D, ys, 130, 1.0)
    bob = math.sin(u * 4.0) * 8
    text(ctx, "？", 570, 800 + bob, 150, RED, alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    for i, x in enumerate((470, 670)):                                      # さいころ
        draw_die(ctx, x, 1030 + 6 * math.sin(u * 5.0 + i * 2), 96, 1 + int((u * 6 + i * 3) % 6), 0.3 * math.sin(u * 4 + i), 1.0)
    stk(ctx, STK_ASK1, 1190, 44, a=win(t, T_ASK + 0.2, T_S - 0.2, 0.3, 0.25))
    stk(ctx, STK_ASK2, 1362, 44, a=win(t, T_ASK + 1.6, T_S - 0.2, 0.3, 0.25), color="pink")


# ---------- 絵: 見本の1回 ----------
_FLICK = {}


def flick(step):
    if step not in _FLICK:
        _FLICK[step] = np.random.default_rng(1000 + step).random(65) < 0.56
    return _FLICK[step]


def scene_s(ctx, t):
    r = results()
    u = t - T_S
    k = int(r["sims"][0])
    s_, st = 66.0, 70.0
    x0, y0 = SX - (13 * st - 4) / 2, 655.0
    fz = u >= U_FREEZE
    sample = sample_tiles(k)
    state = sample if fz else flick(int(u / 0.28))
    for i in range(65):
        r_, c_ = divmod(i, 13)
        p = ease_out(clamp01((u - 0.15 - 0.6 * i / 65) / 0.2))
        if p <= 0:
            continue
        tile(ctx, x0 + c_ * st, y0 + r_ * st + 8 * (1 - p), s_, bool(state[i]), p)
    if not fz:
        for i, x in enumerate((480, 660)):
            draw_die(ctx, x, 1092 + 6 * math.sin(u * 5.0 + i * 2), 120, 1 + int((u * 6 + i * 3) % 6), 0.3 * math.sin(u * 4 + i), 1.0)
    else:
        q = ease_out(clamp01((u - U_FREEZE) / 0.3))
        text(ctx, "1万回の、1回目", SX, 618, 30, PENCIL, bold=False, alpha=q)
        text(ctx, "65年のうち", SX, 1050, 34, INK, alpha=q)
        text(ctx, f"{k}年", SX, 1140, 120, SUN_D, alpha=q)
    stk(ctx, STK_S1, 1240, 42, a=win(t, T_S + U_A[0], T_S + U_A[1], 0.3, 0.25))
    stk(ctx, STK_S2, 1385, 42, a=win(t, T_S + U_B[0], T_S + U_B[1], 0.3, 0.25), color="mint")
    stk(ctx, stk_c(), 1310, 46, a=win(t, T_S + U_C[0], T_S + U_C[1], 0.3, 0.25))


# ---------- 絵: 1万回・答え ----------
def scene_h(ctx, t):
    r = results()
    a = fade(t, T_H0, T_RS, 0.6)
    if a <= 0:
        return
    m = ease(clamp01((t - T_REV) / 0.6))
    ks = r["ks"]
    nb = len(ks)
    step, bw = 24.0, 21.0
    x0 = SX - nb * step / 2
    base = lerp(1330.0, 1080.0, m)
    peak = max(r["dist"].values())
    hsc = lerp(560.0, 340.0, m) / peak
    ctx.push_group()
    text(ctx, "65年分の天気を、1万回作り直した", SX, 645, 40, INK)
    p = ease(clamp01((t - T_HC) / CNT))
    n = max(0, min(N_TRIAL, int(p * N_TRIAL)))
    if t < T_REV + 0.3:
        text(ctx, f"{n:,}回目", 100, 705, 30, PENCIL, bold=False, align="left", alpha=1 - ease(clamp01((t - T_REV) / 0.3)))
    k3 = r["k3"]
    for i, v in enumerate(ks):
        cnt = int(r["cum"][i][n - 1]) if n > 0 else 0
        hgt = cnt * hsc
        x = x0 + i * step
        if hgt > 1:
            rrect(ctx, x, base - hgt, bw, hgt, 5)
            col = ORG if v >= k3 else BLU
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3.2 if v >= k3 else 2.4, INK, 0.9)
        if v % 5 == 0 and v <= 50:
            text(ctx, str(v), x + bw / 2, base + 30, 26, INK)
    ctx.move_to(x0 - 8, base)
    ctx.line_to(x0 + nb * step, base)
    _stroke(ctx, 3, INK, 0.8)
    text(ctx, "晴れた年の数（65年のうち）", SX, base + 75, 28, PENCIL, bold=False)
    u = t - (T_HC + CNT)
    if u >= 0.3:                                                            # 実際の42年に赤い線
        q = ease_out(clamp01((u - 0.3) / 0.4))
        xl = x0 + ks.index(k3) * step + bw / 2
        ytop = base - lerp(430.0, 270.0, m)
        note.pen_line(ctx, xl, base + 4, xl, ytop, RED, seed=8, width=11, progress=q)
        text(ctx, f"実際は{k3}年", xl + 16, ytop - 22, 38, RED, align="left", alpha=q)
        text(ctx, str(k3), xl, base + 30, 34, RED, alpha=q)
    if u >= 1.1:
        q = ease_out(clamp01((u - 1.1) / 0.4))
        text(ctx, f"{k3}年以上は、{r['cnt_ge']:,}回", 740, 705, 48, ORG_D, alpha=q)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if t >= T_REV:
        ex = 1 - ease((t - T_RS + 0.1) / 0.3)
        b = ease_out((t - T_REV - 0.2) / 0.3) * ex
        stk(ctx, f"答えは『{KEY_SAY[r['key']]}』。", 1232, 50, fg=RED, a=b, tilt=-0.02)
        stk(ctx, stk_b(), 1372, 34, a=win(t, T_REV + 0.6, T_REV + 3.5, 0.3, 0.25))
        stk(ctx, STK_B2, 1364, 35, a=win(t, T_REV + 3.6, T_RS - 0.1, 0.3, 0.2), color="pink")


# ---------- 絵: 理由 ----------
def scene_r(ctx, t):
    r = results()
    u = t - T_RS
    text(ctx, "同じ晴れやすさ（56%）で作り直した5回", SX, 628, 34, INK, alpha=ease_out(clamp01(u / 0.3)))
    sx0, cw = 190.0, 11.0
    for row in range(5):
        k = int(r["sims"][row])
        p = ease_out(clamp01((u - 0.3 - 0.35 * row) / 0.3))
        if p <= 0:
            continue
        y = 690 + row * 80.0
        st = sample_tiles(k, seed=11 + row)
        for i in range(65):
            ctx.rectangle(sx0 + i * cw + 0.8, y - 27, cw - 1.6, 54)
            ctx.set_source_rgba(*hexrgb(SUN_Y if st[i] else CLD, p))
            ctx.fill()
        big = k >= r["k3"]
        text(ctx, f"{k}年", 80, y, 46, ORG_D if big else INK, align="left", alpha=p)
        if big and p > 0.9:
            note.pen_circle(ctx, 125, y, 66, 34, RED, seed=15, width=5, progress=1.0)
    text(ctx, "晴れた年の数は、回ごとにちがう。", SX, 1092, 38, INK, alpha=ease_out(clamp01((u - 2.0) / 0.4)))
    stk(ctx, STK_RS1, 1210, 42, a=win(t, T_RS + 0.3, T_TW - 0.2, 0.3, 0.25))
    stk(ctx, STK_RS2, 1365, 42, a=win(t, T_RS + 2.7, T_TW - 0.2, 0.3, 0.25), color="pink")


# ---------- 絵: ひねり（最近30年） ----------
def scene_tw(ctx, t):
    r = results()
    u = t - T_TW
    s_, st = 80.0, 88.0
    x0, y0 = SX - (10 * st - 8) / 2, 660.0
    text(ctx, "11月3日の天気（1996〜2025年）", SX, 622, 28, PENCIL, bold=False, alpha=ease_out(clamp01(u / 0.3)))
    for i, v in enumerate(r["s3_30"]):
        r_, c_ = divmod(i, 10)
        p = ease_out(clamp01((u - 0.2 - 1.0 * i / 30) / 0.2))
        if p > 0:
            tile(ctx, x0 + c_ * st, y0 + r_ * st + 8 * (1 - p), s_, v, p)
    k30 = sum(r["s3_30"])
    ys = (968, 1062, 1138)
    if u >= 1.4:
        q = ease_out(clamp01((u - 1.4) / 0.4))
        number_block(ctx, 340, "11月3日", pct0(k30 / 30), f"{k30}年／30年", ORG_D, ys, 130, q)
    if u >= 2.2:
        q = ease_out(clamp01((u - 2.2) / 0.4))
        number_block(ctx, 800, "前後7日の平均", pct0(r["res30"]["near_rate"]), "前後の14日", BLU_D, ys, 130, q)
        text(ctx, "≒", 570, 1062, 110, INK, alpha=q)
    stk(ctx, STK_TW1, 1245, 42, a=win(t, T_TW + 0.3, T_Q - 0.2, 0.3, 0.25))
    stk(ctx, STK_TW2, 1385, 42, a=win(t, T_TW + 2.5, T_Q - 0.2, 0.3, 0.25), color="mint")


# ---------- 絵: 締め ----------
def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    stk(ctx, STK_Q, 830, 52, a=q, tilt=-0.02, cx=580)
    r_ = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 1030, 40, INK, bold=False, alpha=r_)
    ctx.push_group()
    for i in range(3):
        x = 270 + i * 300
        bob = math.sin((t - T_Q) * 3.0 + i) * 8
        if i == 1:
            glyph_cloud(ctx, x, 1250 + bob, 80, 1.0)
        else:
            glyph_sun(ctx, x, 1250 + bob, 62, (t - T_Q) * (1.2 if i == 0 else -1.0))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)


# ---------- 本体 ----------
def body(ctx, t):
    draw_outdoor(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        grouped(ctx, fade(t, T_E, T_D), scene_e, t)
        grouped(ctx, fade(t, T_D, T_C), scene_d, t)
        grouped(ctx, fade(t, T_C, T_ASK), scene_c, t)
        grouped(ctx, fade(t, T_ASK, T_S), scene_ask, t)
        grouped(ctx, fade(t, T_S, T_H0), scene_s, t)
        scene_h(ctx, t)
        grouped(ctx, fade(t, T_RS, T_TW), scene_r, t)
        grouped(ctx, fade(t, T_TW, T_Q), scene_tw, t)
        source_tag(ctx, t)
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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に2人と机（0秒目から動く）"""
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
            cx, cy = MID, 1015.0
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
    for i in range(3):                                      # 冒頭: 雲が流れる音
        mx.add(0.2 + 1.3 * i, bell(880.0 + 110 * i, 0.5), 0.2)
    mx.add(T_E + 0.9, thump(), 0.35)                        # 特異日の判
    mx.add(T_D + 0.3, riser(0.8), 0.3)
    mx.add(T_D + 2.5, bell(784.0, 0.8), 0.35)
    mx.add(T_C + 0.2, riser(1.6), 0.3)                      # カレンダーが埋まる
    mx.add(T_C + 2.9, thump(), 0.4)
    mx.add(T_C + 3.2, bell(659.3, 0.8), 0.35)
    mx.add(T_C + 4.6, bell(587.3, 0.8), 0.35)
    mx.add(T_ASK + 0.3, bell(523.3, 1.0), 0.35)
    for i in range(4):
        mx.add(T_S + 0.5 + 1.0 * i, blip(440 + 60 * (i % 2), 0.05), 0.2)
    mx.add(T_S + U_FREEZE, thump(), 0.4)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                     # 1万回
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_HC + CNT + 0.5, bell(659.3, 0.8), 0.35)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_RS + 0.5, bell(698.5, 0.8), 0.35)
    mx.add(T_RS + 2.8, bell(784.0, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 1.5, bell(659.3, 0.8), 0.4)
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
    res, res30 = r["res"], r["res30"]
    sims, k3, n3 = r["sims"], r["k3"], r["n3"]
    checks = []
    # (1) 条件・数え直し
    checks.append(("回数 = 1万", float(len(sims)), float(N_TRIAL), 0.0))
    checks.append(("11月3日 = 42年/65年", float((k3, n3) == (42, 65)), 1.0, 0.0))
    checks.append(("画面: 11月3日 65%", float(pct0(k3 / n3) == "65%"), 1.0, 0.0))
    checks.append(("画面: 前後7日 56%（model と一致）", float(pct0(r["p0"]) == "56%" and abs(r["p0"] - res["near_rate"]) < 0.0006), 1.0, 0.0))
    checks.append(("数え直し: たまたま42年以上の割合が tokubi_model.run と一致", float(round(float((sims >= k3).mean()), 4) == res["p_upper"]), 1.0, 0.0))
    checks.append(("数え直し: 1万回の中央・最小・最大が model と一致",
                   float((float(np.median(sims)), int(sims.min()), int(sims.max())) == (res["chance_k"]["median"], res["chance_k"]["min"], res["chance_k"]["max"])), 1.0, 0.0))
    checks.append(("分布の合計 = 1万", float(sum(r["dist"].values())), float(N_TRIAL), 0.0))
    alt = np.bincount(sims - r["ks"][0], minlength=len(r["ks"]))
    checks.append(("分布: 別の数え方（bincount）と同じ", float([int(v) for v in alt] == [r["dist"][v] for v in r["ks"]]), 1.0, 0.0))
    checks.append(("画面: 42年以上の回 1,075", float(r["cnt_ge"]), 1075.0, 0.0))
    checks.append(("画面: 「10回に1回」（1,075回 = 10.8%）", float(round(r["cnt_ge"] / N_TRIAL * 10) == 1), 1.0, 0.0))
    # カレンダーが model と一致
    ok_cal = all(sum(1 for row in r["cal"] if row[ci] is True) == mm.rate(r["sun"], md)[0] and
                 sum(1 for row in r["cal"] if row[ci] is not None) == mm.rate(r["sun"], md)[1] for ci, md in enumerate(NEAR_COLS))
    checks.append(("カレンダー: 15日ぶんの晴れた年数・記録のある年数が model.rate と一致", float(ok_cal), 1.0, 0.0))
    checks.append(("カレンダー: 11月3日の列 = 42年", float(sum(1 for row in r["cal"] if row[COL3] is True)), 42.0, 0.0))
    near_s = sum(1 for row in r["cal"] for ci in range(len(NEAR_COLS)) if ci != COL3 and row[ci] is True)
    near_n = sum(1 for row in r["cal"] for ci in range(len(NEAR_COLS)) if ci != COL3 and row[ci] is not None)
    checks.append(("カレンダー: 前後14日の平均 = 56%（model の near_rate）", float(abs(near_s / near_n - r["p0"]) < 1e-9), 1.0, 0.0))
    checks.append(("カレンダー: 65年 × 15日", float((len(r["cal"]), len(r["cal"][0])) == (65, 15)), 1.0, 0.0))
    # (2) 答え
    key = answer_by_rule(float((sims >= k3).mean()), float((sims <= k3).mean()))
    checks.append(("規則の答え = ほぼ同じ", float(key == "ほぼ同じ"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号の並び: 特異日・ほぼ同じ・ふつうの日 の順", float(LABELS == ["特異日（11月3日）", "ほぼ同じ", "ふつうの日"]), 1.0, 0.0))
    for pu, pl, k_ in ((0.01, 0.99, "特異日を選ぶ"), (0.99, 0.01, "ふつうの日を選ぶ"), (0.1075, 0.9, "ほぼ同じ"), (0.025, 0.9, "特異日を選ぶ"), (0.026, 0.9, "ほぼ同じ")):
        checks.append((f"規則の道具: 上位{pu:.3f}・下位{pl:.2f} → {k_}", float(answer_by_rule(pu, pl) == k_), 1.0, 0.0))
    # (3) 見本は1万回の中の最初の1回そのもの
    k0 = int(sims[0])
    one = int(np.random.default_rng(131).binomial(n3, r["p0"], N_TRIAL)[0])
    checks.append(("見本: 晴れた年の数 = 1万回の1回目（数え直し）", float(k0 == one), 1.0, 0.0))
    checks.append(("見本: 絵の升の晴れの数 = 1回目の年数", float(int(sample_tiles(k0).sum())), float(k0), 0.0))
    checks.append(("見本: 付箋の年数 = 1回目", float(f"{k0}年" in stk_c()), 1.0, 0.0))
    checks.append(("理由: 5回の行 = 1万回の最初の5回、絵の升の数が一致",
                   float(all(int(sample_tiles(int(sims[i]), seed=11 + i).sum()) == int(sims[i]) for i in range(5))), 1.0, 0.0))
    # (4) ひねり（最近30年）
    k30 = sum(r["s3_30"])
    checks.append(("ひねり: 最近30年の11月3日 = 17/30年 = 57%（model と一致）", float(k30 == res30["k3"] == 17 and pct0(k30 / 30) == "57%"), 1.0, 0.0))
    checks.append(("ひねり: 最近30年の前後7日 = 56%", float(pct0(res30["near_rate"]) == "56%"), 1.0, 0.0))
    checks.append(("ひねり: 付箋の数字 57%・56% が計算と同じ", float("57%" in STK_TW1 and "56%" in STK_TW2), 1.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q3) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(440 - s3 / 2 >= 370), 1.0, 0.0))
    # 出典の札
    checks.append(("出典の札: 文字24px以上・1行が x=930 以内（26px）", float(core.text_width(SRC, 26) / 2 + SX <= 930), 1.0, 0.0))
    checks.append(("出典の札: 気象庁ホームページ（過去の気象データ）", float("気象庁ホームページ（過去の気象データ）" in SRC), 1.0, 0.0))
    checks.append(("出典の札: 映す時間 8秒以上", float((T_ASK - 0.2) - (T_D + 0.2) - 0.6 >= 8.0), 1.0, 0.0))
    # (6) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_)
        need = max(0.12 * n_ + 1.0, 0.5 + n_ / 6.0)
        checks.append((f"札「{s_}」が読み切れる（{tb - ta:.1f}秒 / 要る {need:.1f}秒）", float(tb - ta >= need), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万回の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("見本の付箋が 見本の場面に収まる", float(U_C[1] <= (T_H0 - T_S) and U_B[1] <= U_FREEZE), 1.0, 0.0))
    checks.append(("長さ 50〜58秒（60秒未満）", float(50.0 <= DURATION <= 58.5), 1.0, 0.0))
    # (7) 冒頭の動き
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
    print(f"長さ {DURATION:.1f}秒  特異日 {T_E:.1f}  データ {T_D:.1f}  記録 {T_C:.1f}  問い {T_ASK:.1f}  見本 {T_S:.1f}  1万回 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  11月3日 {r['k3']}/{r['n3']}年 ({pct0(r['k3'] / r['n3'])})  前後7日 {pct0(r['p0'])}  答え: {r['key']}  42年以上 {r['cnt_ge']:,}回/1万回")
    print(f"  見本: 1回目 {int(r['sims'][0])}年  最近30年: {sum(r['s3_30'])}/30年 ({pct0(sum(r['s3_30']) / 30)})  前後 {pct0(r['res30']['near_rate'])}")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 3.0, 4.6,
          T_E + 2.0, T_D + 1.2, T_D + 4.2,
          T_C + 1.4, T_C + 3.4, T_C + 5.6,
          T_ASK + 2.4,
          T_S + 2.0, T_S + 4.2, T_S + 6.0,
          T_HC + 1.0, T_REV - 0.3, T_REV + 3.2, T_REV + 5.0,
          T_RS + 2.0, T_RS + 4.3, T_TW + 1.0, T_TW + 4.0,
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
