"""一斉にじゃんけん。1回で決まりやすいのは何人まで？ 人数ごとに1万回。— 2026-10-29 作成（公開予定 11/10・ナレーションなし・45秒前後）

くらべるのは「n人が一斉に出して、1回で勝ち負けが決まる（あいこにならない）割合」だけ。

モデル（n人が、それぞれ別々に、グー・チョキ・パーのどれかを出す）
  ① 全員が グー・チョキ・パーを 同じ確率（1/3ずつ）で出す。人は別々に出し、前の回の影響はない（仮定。人の出す手は少しグーに偏る研究がある→ FACTCHECK と --model の感度）
  ② 「決まる」＝出た手がちょうど2種類。1種類だけ（全員同じ）・3種類そろった ときは「あいこ」。
  ③ n = 2〜40人のそれぞれで、1万回ずつ出して、決まった回の割合を数える。
  式（確かめ用）  p(n) = 3·(2^n − 2) ÷ 3^n   … 手の出し方は 3^n 通り。ちょうど2種類になるのは「どの2種類か 3通り」×「その2種類を両方使う 2^n − 2 通り」。
                  n=2・3 で 2/3、n=4 で 14/27（約52%）、n=5 で 10/27（約37%）、n=10 で 約5.2%、n=40 で 約 2.7×10⁻⁷（約370万回に1回）。

問い: 「一斉にじゃんけん。/ 1回で決まりやすいのは / 何人まで？」（小さい行: 「2回に1回以上 1回で決まる人数で比べる」「グー・チョキ・パーを同じ確率で出す、と置いた計算」）
      選択肢: 4人くらいまで ／ 10人くらいまで ／ 40人でも（この並び。正解の見込み A。2026-10-29 統括の直し: 6人・15人 → 4人・10人。しきい値は変えない）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      n=2 から順に、決まった割合が 50%以上（2回に1回は決まる）を保てる最大の人数を N とする（50%を下回ったら、それ以降は数えない）。
      N ≤ 6 → 4人くらいまで（A）／ 7 ≤ N ≤ 15 → 10人くらいまで（B）／ N ≥ 16 → 40人でも（C）
      見込み: p(4)≈52%・p(5)≈37% なので N = 4（→ 4人くらいまで）
見せ方: 見本の1回（教室の4人は決まる・10人はあいこ）→ 4人・10人・40人 それぞれ1万回のマス目 → 人数ごとの割合の棒（50%の線）→ 答え
ひねり: 「では、1回で決まりやすいのは何人？」→ 2人と3人が同じ 約67%（3回に2回）
締め: 「あなたのクラスなら、何人ずつに分けますか？」（答えは出さない）＋「コメントで教えてください」
言葉: 「中央値」は使わない（この題材は割合だけ）。見本の1回は「たとえば、この1回では」。画面に「…同じ確率で出す、と置いた計算で」と1回。
乱数の種は、画面に出す%（整数）が理論値と同じになるものを選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "janken-issei"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
N_MIN, N_MAX = 2, 40
SEED_MAIN = 20261110
EQUAL = (1 / 3, 1 / 3, 1 / 3)                        # （グー, チョキ, パー）を出す確率
ROCK_BIAS = (0.356, 0.322, 0.322)                    # グーがやや多い（Dyson ほか 2016 / Xu ほか 2013 の全体の割合に近い値）
ROCK_BIAS_STRONG = (0.50, 0.25, 0.25)                # もっと偏った場合（感度の確認用）
RULE_P = 0.5                                         # 「2回に1回は決まる」
RULE_SIX, RULE_FIFTEEN = 6, 15
SHOW_NS = (2, 3, 4, 5, 10, 40)


def answer_by_rule(p_by_n):
    """p_by_n: {人数: 1回で決まった割合}（2〜40人）。2人から順に見て、50%以上を保てる最大の人数 N。
    戻り値 (キー, N)。キーは 'six'（N ≤ 6）/ 'fifteen'（7 ≤ N ≤ 15）/ 'forty'（N ≥ 16）"""
    N = 1
    for n in sorted(p_by_n):
        if p_by_n[n] >= RULE_P:
            N = n
        else:
            break
    if N <= RULE_SIX:
        return "six", N
    if N <= RULE_FIFTEEN:
        return "fifteen", N
    return "forty", N


def exact_p(n, probs=EQUAL):
    """n人が（グー,チョキ,パー）を probs の確率で出したとき、ちょうど2種類になる確率。
    すべて同じ確率なら 3·(2^n − 2) ÷ 3^n"""
    a, b, c = probs
    return (a + b) ** n + (b + c) ** n + (a + c) ** n - 2.0 * (a ** n + b ** n + c ** n)


def exact_p_equal(n):
    return 3.0 * (2 ** n - 2) / 3.0 ** n


def kinds_of(hands):
    return sum((hands == k).any(axis=1).astype(np.int8) for k in range(3))


def simulate(probs, seed, n_trial=N_TRIAL, keep=(4, 10, 40)):
    """n = 2〜40 のそれぞれで n_trial 回。戻り値: kinds[n]（各回で出た手の種類の数）、hands[n]（keep の人数だけ）"""
    rng = np.random.default_rng(seed)
    kinds, hands = {}, {}
    for n in range(N_MIN, N_MAX + 1):
        h = rng.choice(3, size=(n_trial, n), p=list(probs)).astype(np.int8)
        kinds[n] = kinds_of(h)
        if n in keep:
            hands[n] = h
    return kinds, hands


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def _seed_ok(kinds):
    """画面に出す % が理論値と同じ整数になる種（表示のため。答えの統計は1万回すべてを使う）"""
    for n in (2, 3, 4, 5):
        if pct((kinds[n] == 2).mean()) != pct(exact_p_equal(n)):
            return False
    if pct((kinds[10] != 2).mean()) != pct(1 - exact_p_equal(10)):      # あいこ 95%
        return False
    return int((kinds[40] == 2).sum()) == 0


_RES = {}


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


def results():
    if _RES:
        return _RES["m"]
    for i in range(300):
        seed = SEED_MAIN + i
        kinds, hands = simulate(EQUAL, seed)
        if _seed_ok(kinds):
            break
    p = {n: float((kinds[n] == 2).mean()) for n in kinds}
    cnt = {n: int((kinds[n] == 2).sum()) for n in kinds}
    _RES["m"] = dict(seed=seed, kinds=kinds, hands=hands, p=p, cnt=cnt)
    return _RES["m"]


def sensitivity(n_trial=10000):
    """出し方を偏らせても 答え（N）が動くか。理論値（exact_p）と、別の乱数の1万回の両方"""
    rows = []
    for label, probs in (("同じ確率（基準）", EQUAL),
                         ("グーがやや多い（グー35.6%・チョキ32.2%・パー32.2%）", ROCK_BIAS),
                         ("グーが多い（グー50%・チョキ25%・パー25%）", ROCK_BIAS_STRONG),
                         ("グーとチョキだけ多い（グー40%・チョキ40%・パー20%）", (0.4, 0.4, 0.2))):
        ex = {n: exact_p(n, probs) for n in range(N_MIN, N_MAX + 1)}
        kinds, _ = simulate(probs, SEED_MAIN + 777, n_trial, keep=())
        sm = {n: float((kinds[n] == 2).mean()) for n in kinds}
        rows.append((label, probs, answer_by_rule(ex), answer_by_rule(sm), ex, sm))
    return rows


def report():
    r = results()
    key, N = answer_by_rule(r["p"])
    kex, Nex = answer_by_rule({n: exact_p_equal(n) for n in range(N_MIN, N_MAX + 1)})
    print(f"乱数の種 {r['seed']}  1万回ずつ  n = {N_MIN}〜{N_MAX}")
    print("  人数: 1万回の割合（決まった回数）/ 理論値 3(2^n−2)/3^n")
    for n in (2, 3, 4, 5, 6, 7, 8, 10, 15, 20, 30, 40):
        print(f"   {n:>2}人: {r['p'][n] * 100:6.2f}%（{r['cnt'][n]:>5}回）/ {exact_p_equal(n) * 100:10.6f}%  ≈ {1 / exact_p_equal(n):,.1f}回に1回")
    print(f"  答え: 1万回の割合 → N = {N} → {key}   理論値 → N = {Nex} → {kex}")
    print(f"  10人: あいこ {pct(1 - r['p'][10])}%（{1 - exact_p_equal(10):.4f}）  40人: 決まった {r['cnt'][40]}回  理論 約 {1 / exact_p_equal(40):,.0f} 回に1回")
    print(f"  ひねり: 2人 {pct(r['p'][2])}%  3人 {pct(r['p'][3])}%（理論どちらも 2/3 = {2 / 3:.4f}）")


def report_sensitivity():
    print("感度（人の出し方を偏らせても）:")
    for label, probs, (ke, Ne), (ks, Ns), ex, sm in sensitivity():
        print(f"  {label}: 理論 N={Ne}→{ke}  1万回 N={Ns}→{ks}  "
              f"p(2)={ex[2] * 100:.1f}% p(3)={ex[3] * 100:.1f}% p(4)={ex[4] * 100:.1f}% p(5)={ex[5] * 100:.1f}% p(10)={ex[10] * 100:.1f}% p(40)={ex[40]:.2e}")


# ---- MODEL END ----


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す1回ぶん）を、1万回の中から選ぶ
# =====================================================================
HAND_NAMES = ["グー", "チョキ", "パー"]
_SAMPLE = {}


def winner_hand(hs):
    """決まった回の、勝った手（0=グー 1=チョキ 2=パー。a は (a+1)%3 に勝つ）"""
    a, b = sorted(set(int(x) for x in hs))
    return a if (b - a) % 3 == 1 else b


def samples():
    """4人の見本（決まる回・グー3人対チョキ1人）と、10人の見本（3種類そろってあいこ・4-3-3）。どちらも 1万回の中の1回そのもの"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    h4, h10 = r["hands"][4], r["hands"][10]
    k4, k10 = r["kinds"][4], r["kinds"][10]
    i4 = None
    for i in range(len(h4)):
        hs = h4[i]
        if k4[i] == 2 and winner_hand(hs) == 0 and int((hs == 0).sum()) == 3 and hs[0] == 0 and hs[3] == 0:   # 端の2人は勝つほう。負けは真ん中
            i4 = i
            break
    if i4 is None:
        i4 = int(np.argmax((k4 == 2) & ((h4 == 0).sum(axis=1) == 3)))
    i10 = None
    for i in range(len(h10)):
        hs = h10[i]
        if k10[i] == 3 and sorted(int((hs == k).sum()) for k in range(3)) == [3, 3, 4] and int((hs == 0).sum()) == 4:
            if all(hs[j] != hs[(j + 1) % 10] for j in range(0, 10, 3)):
                i10 = i
                break
    if i10 is None:
        i10 = int(np.argmax(k10 == 3))
    _SAMPLE.update(i4=i4, i10=i10, h4=[int(x) for x in h4[i4]], h10=[int(x) for x in h10[i10]])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    S = samples()
    print("見本 4人: 回", S["i4"], [HAND_NAMES[x] for x in S["h4"]], " 10人: 回", S["i10"], [HAND_NAMES[x] for x in S["h10"]])
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER, MARKER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, shimmer, text, thump, tick, whoosh, _t)
from engine.parts import bgra, grid_image, loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.10"                                  # 日付欄（公開予定日）

# この回の差し色: グー＝コーラル、チョキ＝すみれ、パー＝青緑（janken-10nin と同じ）
HANDS = ["#f26b4f", "#9b72e8", "#1fb3a2"]
SKIN = "#f7d9bd"
AIKO = "#6f7fb3"
COL_DEC, COL_AIKO, COL_NOT = "#f2a33a", "#cdd6e8", "#ece7d8"       # マス目: 決まった／あいこ／まだ
COL_BAR_HI, COL_BAR_LO = "#e0801f", "#f4c987"                       # 棒: 50%以上／未満
INK_DEC = "#b8601a"

# 記号の並び・正解は ここ（と comment.txt）だけ
LABELS = ["4人くらいまで", "10人くらいまで", "40人でも"]
KEY_LABEL = {"six": LABELS[0], "fifteen": LABELS[1], "forty": LABELS[2]}
CORRECT = 0                                         # answer_by_rule の結果の位置（A）

BIG_Q3 = ["一斉にじゃんけん。", "1回で決まりやすいのは", "何人まで？"]      # 1コマ目の3行（同じ大きさ）
BIG_Q = ["一斉にじゃんけん。", "1回で決まりやすいのは何人まで？"]           # 定位置（上）の2行
DETAIL_RULE = "2回に1回以上 1回で決まる人数で比べる"
DETAIL = "グー・チョキ・パーを同じ確率で出す、と置いた計算"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 860.0, 620.0
CARD_X = 140.0
CARD_Y_INTRO, CARD_Y_FINAL = 840.0, 640.0
CD_X, CD_Y = 790.0, 970.0

N_ROWS, N_COLS_G, G_CELL = 125, 80, 3                # 1万回 = 80列 × 125行
G_PANELS = (4, 10, 40)
G_X = {4: 110.0, 10: 400.0, 40: 690.0}               # 左端
G_Y0 = 760.0
CH_X0, CH_SLOT, CH_BASE, CH_H = 170.0, 19.2, 965.0, 300.0     # 棒グラフ


def setup():
    global T_A_REV, T_A_STK, T_B0, T_B_REV, T_B_STK, T_B_STK2, T_G0, T_G1, T_GN, T_H0, T_H_BARS
    global T_REV, T_ANS2, T_TW, T_TW2, T_Q, DURATION, SCENES
    T_A_REV = T_GO + 1.5                            # 4人が「ぽん」
    T_A_STK = T_A_REV + 0.4
    T_B0 = T_A_REV + 3.4
    T_B_REV = T_B0 + 1.8
    T_B_STK = T_B_REV + 0.4
    T_B_STK2 = T_B_REV + 2.5
    T_G0 = T_B_REV + 5.6
    T_G1 = T_G0 + 4.0                               # 1万回ぶんのマスが埋まり終わる
    T_GN = T_G1 + 0.1                               # 数字
    T_H0 = T_G1 + 3.4                               # 棒グラフ
    T_H_BARS = T_H0 + 0.4
    T_REV = T_H0 + 3.6
    T_ANS2 = T_REV + 2.4
    T_TW = T_ANS2 + 3.6
    T_TW2 = T_TW + 2.2
    T_Q = T_TW2 + 3.6
    DURATION = T_Q + 4.8
    SCENES = [("4人の見本", T_GO, T_B0), ("10人の見本", T_B0, T_G0), ("1万回のマス目", T_G0, T_H0),
              ("棒グラフ（答え・理由）", T_H0, T_TW), ("ひねり", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def pcs(x):
    return f"{pct(x)}%"


def fmt(n):
    return f"{int(round(n)):,}"


def once_in(p):
    """割合 p を「約N回に1回」にする（N は整数）"""
    return f"約{int(round(1.0 / p))}回に1回"


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


def ik_out(sx, sy, wx, wy, l1, l2, side):
    """肩 (sx, sy) と手首 (wx, wy) から、ひじの位置（2つの解のうち 体の外側 side=±1 のほう）"""
    dx, dy = wx - sx, wy - sy
    dd = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 2.0, math.hypot(dx, dy)))
    a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd)
    hh = math.sqrt(max(l1 * l1 - a * a, 0.0))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    bx, by = sx + a * ux, sy + a * uy
    c1 = (bx - hh * uy, by + hh * ux)
    c2 = (bx + hh * uy, by - hh * ux)
    return c1 if side * c1[0] >= side * c2[0] else c2


# ---------- 手の絵（janken-10nin と同じ） ----------

def _finger(ctx, bx, by, ang, w, length):
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(ang)
    rrect(ctx, -w / 2, -length, w, length + w, w / 2)
    ctx.restore()


def _part(ctx, col, edge, lw=4):
    c = hexrgb(col) if isinstance(col, str) else col
    ctx.set_source_rgba(c[0], c[1], c[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(*edge)
    ctx.set_line_width(lw)
    ctx.stroke()


def hand(ctx, kind, cx, cy, s, col, a=1.0):
    """グー(0)・チョキ(1)・パー(2) を図形で描く。s は大きさ（手のひらの半幅くらい）"""
    if a < 1.0:
        ctx.push_group()
        hand(ctx, kind, cx, cy, s, col, 1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        return
    edge = hexrgb(INK)
    lw = max(2.5, 4 * s / 50)
    ctx.save()
    ctx.translate(cx, cy + 0.2 * s)
    if kind == 0:
        rrect(ctx, -0.85 * s, -0.55 * s, 1.7 * s, 1.25 * s, 0.4 * s)
        _part(ctx, col, edge, lw)
        for i in range(4):
            ctx.new_path()
            ctx.arc(-0.63 * s + i * 0.42 * s, -0.55 * s, 0.24 * s, 0, 2 * math.pi)
            _part(ctx, col, edge, lw)
        rrect(ctx, -0.95 * s, 0.0, 1.05 * s, 0.36 * s, 0.18 * s)
        _part(ctx, col, edge, lw)
    elif kind == 1:
        _finger(ctx, -0.2 * s, -0.2 * s, -0.3, 0.36 * s, 1.15 * s)
        _part(ctx, col, edge, lw)
        _finger(ctx, 0.22 * s, -0.2 * s, 0.3, 0.36 * s, 1.15 * s)
        _part(ctx, col, edge, lw)
        rrect(ctx, -0.75 * s, -0.25 * s, 1.5 * s, 1.0 * s, 0.4 * s)
        _part(ctx, col, edge, lw)
        rrect(ctx, -0.9 * s, 0.2 * s, 0.95 * s, 0.34 * s, 0.17 * s)
        _part(ctx, col, edge, lw)
    else:
        for i, (ang, ln) in enumerate([(-0.28, 0.85), (-0.09, 1.0), (0.09, 0.98), (0.28, 0.82)]):
            _finger(ctx, (-0.45 + i * 0.3) * s, -0.2 * s, ang, 0.27 * s, ln * s)
            _part(ctx, col, edge, lw)
        _finger(ctx, -0.55 * s, 0.35 * s, -1.05, 0.3 * s, 0.7 * s)
        _part(ctx, col, edge, lw)
        rrect(ctx, -0.7 * s, -0.3 * s, 1.4 * s, 1.05 * s, 0.4 * s)
        _part(ctx, col, edge, lw)
    ctx.restore()


# ---------- 絵: 生徒（制服・正面。目と頭は内側＝円の中心のほうを向く） ----------
BLAZER, BLAZER_D, SHIRT, SKIRT, PANTS, TIE, SHOE = "#34456a", "#283657", "#f6f3ea", "#4a5373", "#3d4560", "#c4414b", "#2a2f3d"
STU = [dict(girl=False, hair="#2b2b33", style="short"),
       dict(girl=True, hair="#5a3d2b", style="bob"),
       dict(girl=True, hair="#1f2430", style="long"),
       dict(girl=False, hair="#6a4a33", style="spiky")]


def student(ctx, x, fy, k, ci, t, look, hand_spec=None, bob=0.0, mouth=0.0, hl=0.0, wait_blink=True):
    """正面向きの生徒。(x, fy) は足もとの中心、身長は 100·k px。look = +1 なら右、−1 なら左（内側）を見て、その側の手を前に出す。
    hand_spec = (kind, 色, 不透明度, 大きさの倍率) か None。bob = 手の上下（単位は身長の1/100）。mouth = 口の開き（0〜1）。hl = 勝った手の強調（0〜1）"""
    S = STU[ci % len(STU)]
    hs = look if look else 1
    P = lambda dx, dy: (x + dx * k, fy + dy * k)    # noqa: E731
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    lw = max(2.2, 0.75 * k)

    def poly(pts, col, w=None):
        ctx.new_path()
        for i, (px, py) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(*P(px, py))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, w or lw, INK, 0.9)

    # 長い髪（うしろ）
    if S["style"] == "long":
        ctx.new_path()
        ctx.move_to(*P(-10.5, -93))
        ctx.curve_to(*P(-15, -82), *P(-14.5, -70), *P(-11.5, -64))
        ctx.line_to(*P(11.5, -64))
        ctx.curve_to(*P(14.5, -70), *P(15, -82), *P(10.5, -93))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(S["hair"]))
        ctx.fill_preserve()
        _stroke(ctx, lw, INK, 0.9)
    # 脚と くつ
    for dx in (-7.2, 7.2):
        if S["girl"]:
            thick(ctx, [P(dx, -34), P(dx, -7)], 7.6 * k, SKIN, 2.2)
            thick(ctx, [P(dx, -14), P(dx, -6.5)], 8.2 * k, SHIRT, 2.2)
        else:
            thick(ctx, [P(dx, -46), P(dx, -6)], 13.0 * k, PANTS, 2.4)
        sx, sy = P(dx + look * 1.4, -2.6)
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1.0, 0.52)
        ctx.arc(0, 0, 6.8 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(SHOE))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    # 手を出さないほうのうで（体の横に下ろす）
    sx0, sy0 = P(-hs * 16.0, -73.0)
    thick(ctx, [(sx0, sy0), P(-hs * 19.5, -62), P(-hs * 19.0, -50.5)], 7.6 * k, BLAZER, 2.4)
    ctx.new_path()
    ctx.arc(*P(-hs * 19.5, -46.5), 3.9 * k, 0, 2 * math.pi)
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
    poly([(-5.8, -80.5), (0, -63), (5.8, -80.5)], SHIRT, lw * 0.8)            # シャツ（V の襟もと）
    poly([(-5.8, -80.5), (-10.2, -68), (-3.6, -60.5), (0, -63)], BLAZER_D, lw * 0.8)      # 襟（折り返し）
    poly([(5.8, -80.5), (10.2, -68), (3.6, -60.5), (0, -63)], BLAZER_D, lw * 0.8)
    if S["girl"]:                                                              # リボン
        poly([(0, -72), (-5.4, -76), (-5.4, -68)], TIE, lw * 0.7)
        poly([(0, -72), (5.4, -76), (5.4, -68)], TIE, lw * 0.7)
        ctx.new_path()
        ctx.arc(*P(0, -72), 1.8 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(TIE))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.7, INK, 0.9)
    else:                                                                      # ネクタイ
        poly([(-1.6, -73), (1.6, -73), (2.1, -57), (0, -54.5), (-2.1, -57)], TIE, lw * 0.7)
    for by_ in (-52.5, -47.0):
        ctx.new_path()
        ctx.arc(*P(0, by_), 0.95 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#e6c35a"))
        ctx.fill()
    if S["girl"]:                                                              # スカート
        poly([(-15.6, -46), (15.6, -46), (20.5, -29), (-20.5, -29)], SKIRT, lw)
        for dx in (-9, -3, 3, 9):
            ctx.move_to(*P(dx * 0.8, -45))
            ctx.line_to(*P(dx * 1.25, -29.5))
            _stroke(ctx, lw * 0.5, INK, 0.35)
    # 手を出すほうのうで（胸の前）
    shx, shy = P(hs * 15.5, -73.0)
    wx, wy = P(hs * 13.0, -54.0 + bob)
    elx, ely = ik_out(shx, shy, wx, wy, 14.0 * k, 14.0 * k, hs)
    thick(ctx, [(shx, shy), (elx, ely), (wx, wy)], 7.6 * k, BLAZER, 2.4)
    ctx.new_path()
    ctx.arc(wx, wy, 4.7 * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SHIRT))                                         # そで口
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.8, INK, 0.9)
    hcx, hcy = wx + hs * 1.0 * k, wy - 7.0 * k
    if hand_spec is not None:
        kind, col, al, scl = hand_spec
        hsz = 8.6 * k * scl
        if hl > 0:
            ctx.set_source_rgba(*hexrgb("#ffe98a", hl))
            ctx.arc(hcx, hcy, hsz * 1.5, 0, 2 * math.pi)
            ctx.fill()
        hand(ctx, kind, hcx, hcy, hsz, col, al)
        if hl > 0:
            note.pen_circle(ctx, hcx, hcy, hsz * 1.55, hsz * 1.55, RED, seed=3 + ci, width=max(3.0, 0.9 * k), progress=hl)
    # 首・頭（内側へ少し傾ける）
    core.rrect(ctx, *P(-3.6, -82), 7.2 * k, 6.5 * k, 2 * k)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    ctx.save()
    nx, ny = P(0, -80)
    ctx.translate(nx, ny)
    ctx.rotate(look * 0.06)
    ctx.translate(-nx, -ny)
    for sg in (-1, 1):                                                          # 耳
        ctx.new_path()
        ctx.arc(*P(sg * 9.1, -89), 2.2 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.save()                                                                  # 顔
    ctx.translate(*P(0, -89.5))
    ctx.scale(1.0, 1.08)
    ctx.arc(0, 0, 9.1 * k, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    # 髪
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
    if S["style"] in ("bob", "long"):
        ln = 14.5 if S["style"] == "bob" else 17.0
        for sg in (-1, 1):
            core.rrect(ctx, *P(sg * 10.4 - 2.1, -96), 4.2 * k, ln * k, 2.0 * k)
            ctx.set_source_rgba(*hexrgb(hair))
            ctx.fill_preserve()
            _stroke(ctx, lw * 0.9, INK, 0.9)
    # 目・まゆ・ほお・口
    blink = wait_blink and ((t * 0.9 + ci * 0.7) % 3.4 < 0.12)
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
    return hcx, hcy


# ---------- 絵: 輪になった生徒（真上から。手の絵が主役） ----------

def person_top(ctx, x, y, th, ci):
    """真上から見た生徒。th は、局所の「上」を 中心のほうへ向ける回転。肩（ブレザー）・頭（髪）・耳・鼻"""
    S = STU[ci % len(STU)]
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(th)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if S["style"] == "long":                                                    # 長い髪（うしろ）
        ctx.save()
        ctx.translate(0, 18)
        ctx.scale(1.0, 0.95)
        ctx.arc(0, 0, 23, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(S["hair"]))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
    for sg in (-1, 1):                                                          # うで（前へ）
        thick(ctx, [(sg * 33, 6), (sg * 24, -16), (sg * 14, -34)], 14, BLAZER, 2.4)
    ctx.save()                                                                  # 肩
    ctx.translate(0, 10)
    ctx.scale(1.0, 0.46)
    ctx.arc(0, 0, 42, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(BLAZER))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.92)
    for sg in (-1, 1):                                                          # 耳・鼻
        ctx.new_path()
        ctx.arc(sg * 21, 6, 5.2, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.9)
    ctx.new_path()
    ctx.arc(0, -22, 5.2, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.4, INK, 0.9)
    ctx.new_path()                                                              # 頭（髪）
    ctx.arc(0, 6, 22, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(S["hair"]))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.92)
    ctx.save()                                                                  # おでこ（髪の生えぎわ）
    ctx.new_path()
    ctx.translate(0, -4)
    ctx.scale(1.0, 0.72)
    ctx.arc(0, 0, 13.5, math.pi * 1.02, math.pi * 1.98)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 2.2, INK, 0.8)
    ctx.move_to(0, -12)
    ctx.line_to(0, 8)
    _stroke(ctx, 2.0, INK, 0.4)
    ctx.restore()


# ---------- 絵: 教室のカード ----------

def card_pos(m):
    return CARD_X, CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m


A_HANDS = None            # 4人の見本の手（samples で決まる）
RING_C, RING_R, RING_HR = (305.0, 345.0), 200.0, 140.0       # 輪の中心・人の半径・手の半径（カード内）


def seq_a():
    return samples()["h4"]


def seq_b():
    return samples()["h10"]


def draw_room(ctx, t):
    """教室（壁・黒板・窓・床）と、横一列に並んだ4人。冒頭から じゃんけんの前の手がはずむ"""
    # 壁と床
    fill(ctx, "#dbe8dd")
    ctx.rectangle(0, 0, CARD_W, 520)
    ctx.fill()
    fill(ctx, "#c8dacd")
    ctx.rectangle(0, 400, CARD_W, 120)
    ctx.fill()
    for i in range(12):                                                         # 壁の縦じま
        fill(ctx, (1, 1, 1, 0.38))
        ctx.rectangle(30 + i * 74, 0, 30, 400)
        ctx.fill()
    # 窓からの光（床と壁を ゆっくり横切る）
    sh = (t * 90.0) % 400.0
    ctx.save()
    ctx.move_to(560 - sh * 1.2, 160)
    ctx.line_to(640 - sh * 1.2, 160)
    ctx.line_to(360 - sh * 1.2, 520)
    ctx.line_to(280 - sh * 1.2, 520)
    ctx.close_path()
    ctx.set_source_rgba(1.0, 0.97, 0.8, 0.30)
    ctx.fill()
    ctx.restore()
    # 黒板
    rrect(ctx, 370, 36, 290, 124, 6)
    ctx.set_source_rgba(*hexrgb("#a8825a"))
    ctx.fill()
    rrect(ctx, 378, 44, 274, 108, 4)
    ctx.set_source_rgba(*hexrgb("#35564c"))
    ctx.fill()
    for (x0, y0, x1, y1) in ((400, 70, 500, 66), (400, 96, 600, 98), (400, 122, 470, 120)):      # チョークの線
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        _stroke(ctx, 4, "#f3f1e6", 0.55)
    ctx.rectangle(384, 154, 262, 6)
    ctx.set_source_rgba(*hexrgb("#8e6c46"))
    ctx.fill()
    # 窓
    rrect(ctx, 690, 36, 130, 134, 6)
    ctx.set_source_rgba(*hexrgb("#f4f1e8"))
    ctx.fill()
    rrect(ctx, 698, 44, 114, 118, 3)
    ctx.set_source_rgba(*hexrgb("#bfe0f5"))
    ctx.fill()
    ctx.move_to(755, 44)
    ctx.line_to(755, 162)
    ctx.move_to(698, 103)
    ctx.line_to(812, 103)
    _stroke(ctx, 4, "#f4f1e8", 1.0)
    ctx.arc(728, 76, 13, 0, 2 * math.pi)
    ctx.arc(742, 80, 11, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 1, 1, 0.8)
    ctx.fill()
    # 床
    fill(ctx, "#b08b5f")
    ctx.rectangle(0, 506, CARD_W, 14)
    ctx.fill()
    fill(ctx, "#d9b98c")
    ctx.rectangle(0, 520, CARD_W, 110)
    ctx.fill()
    for yy in (548, 578, 608):
        ctx.move_to(0, yy)
        ctx.line_to(CARD_W, yy)
        _stroke(ctx, 2, "#b08b5f", 0.55)
    # 4人
    seq = seq_a()
    revealed = t >= T_A_REV
    for i in range(4):
        inner = i in (1, 2)
        k = 3.8 * (0.97 if inner else 1.0)
        fy = 594.0 - (12.0 if inner else 0.0)
        x = CARD_W / 2 + (i - 1.5) * 216.0
        look = 1 if i < 2 else -1
        if not revealed:
            ph = t / 0.62 + i * 0.35
            bob = 6.5 * math.sin(2 * math.pi * ph)
            hsp = (0, SKIN, 1.0, 1.0)
            mouth = 0.9 if (t >= T_GO and math.sin(2 * math.pi * ph) > 0.2) else 0.0
            hl = 0.0
        else:
            age = t - T_A_REV
            kind = seq[i]
            win = winner_hand(seq)
            al = 1.0
            pop = 1 + 0.25 * (1 - ease_out(age / 0.15))
            hsp = (kind, HANDS[kind], al, pop)
            bob = 0.0
            mouth = 0.55 if (kind == win and age > 0.4) else 0.0
            hl = clamp01((age - 0.3) / 0.35) if kind == win else 0.0
        student(ctx, x, fy, k, i, t, look, hsp, bob=bob, mouth=mouth, hl=hl)


def draw_ring(ctx, t):
    """10人が輪になって（真上から）一斉に出す。手の絵が主役"""
    # 床と敷物
    fill(ctx, "#d9b98c")
    ctx.rectangle(0, 0, CARD_W, CARD_H)
    ctx.fill()
    for yy in range(30, int(CARD_H), 44):
        ctx.move_to(0, yy)
        ctx.line_to(CARD_W, yy)
        _stroke(ctx, 2, "#b08b5f", 0.5)
    for j, yy in enumerate(range(30, int(CARD_H), 44)):
        for xx in range(40 + (j % 2) * 120, int(CARD_W), 240):
            ctx.move_to(xx, yy)
            ctx.line_to(xx, yy + 44)
            _stroke(ctx, 2, "#b08b5f", 0.45)
    ctx.arc(RING_C[0], RING_C[1], RING_R + 50, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#f0e6cd", 0.8))
    ctx.fill_preserve()
    _stroke(ctx, 3, "#b08b5f", 0.7)
    seq = seq_b()
    rt = t - T_B0
    revealed = t >= T_B_REV
    for i in range(10):
        ang = -math.pi / 2 + i * 2 * math.pi / 10
        px, py = RING_C[0] + RING_R * math.cos(ang), RING_C[1] + RING_R * math.sin(ang)
        dx, dy = RING_C[0] - px, RING_C[1] - py
        th = math.atan2(dx, -dy)
        person_top(ctx, px, py, th, i)
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        if not revealed:
            bobv = 7.0 * math.sin(2 * math.pi * (rt / 0.6 + i * 0.1))
            hx, hy = px + ux * (RING_R - RING_HR + bobv), py + uy * (RING_R - RING_HR + bobv)
            hand(ctx, 0, hx, hy, 29, SKIN)
        else:
            age = t - T_B_REV
            pop = 1 + 0.25 * (1 - ease_out(age / 0.15))
            hx, hy = px + ux * (RING_R - RING_HR), py + uy * (RING_R - RING_HR)
            hand(ctx, seq[i], hx, hy, 29 * pop, HANDS[seq[i]])
    # 輪の真ん中
    cx, cy = RING_C
    if not revealed:
        text(ctx, "じゃんけん…", cx, cy, 36, PENCIL, bold=False)
    else:
        a = ease_out((t - T_B_REV - 0.1) / 0.25)
        text(ctx, "あいこ", cx, cy - 8, 52, AIKO, alpha=a)
        text(ctx, "3種類 そろった", cx, cy + 40, 26, PENCIL, bold=False, alpha=a)
        # 右の集計（グー・チョキ・パーの人数）
        for j in range(3):
            n = sum(1 for h in seq if h == j)
            yy = 220 + j * 90
            hand(ctx, j, 588, yy, 24, HANDS[j], a)
            text(ctx, f"{HAND_NAMES[j]} {n}人", 630, yy, 34, INK, align="left", alpha=a)


def draw_card(ctx, t, m):
    x0, y0 = card_pos(m)
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    ctx.clip()
    sw = ease((t - T_B0) / 0.35)                                  # 4人 → 10人 の切り替え
    if sw < 1.0:
        ctx.push_group()
        draw_room(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - sw)
    if sw > 0.0:
        ctx.push_group()
        draw_ring(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(sw)
    ctx.restore()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    _stroke(ctx, 3.2, INK, 0.85)
    # 題（左上）
    plate_w = 330
    rrect(ctx, 24, 22, plate_w, 82, 12)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    title = "4人で一斉に" if sw < 0.5 else "10人で一斉に"
    text(ctx, title, 42, 46, 40, INK, align="left")
    text(ctx, "たとえば、この1回では", 42, 86, 26, PENCIL, align="left", bold=False)
    ctx.restore()


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.16 * (1 - ease(clamp01(t / 1.1)))               # 冒頭: 場面が寄ったところから引く（下端を基準に）
    ctx.save()
    if z > 1.0:
        ctx.translate(540, 1440)
        ctx.scale(z, z)
        ctx.translate(-540, -1440)
    ctx.push_group()
    draw_card(ctx, t, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()
    # 見本の結果の付箋（カードの下）
    if t >= T_A_STK and t < T_B0 + 0.1:
        s = ease_out((t - T_A_STK) / 0.25) * (1 - ease((t - T_B0) / 0.25))
        note.sticky(ctx, f"決まった！\n{HAND_NAMES[winner_hand(seq_a())]}の{sum(1 for h in seq_a() if h == winner_hand(seq_a()))}人の勝ち", 570, 1362, 50, "mint", a=s, tilt=0.02)
    if t >= T_B_STK and t < T_G0 + 0.1:
        s = ease_out((t - T_B_STK) / 0.25) * (1 - ease((t - T_G0) / 0.25))
        note.sticky(ctx, "あいこ", 570, 1337, 56, "blue", fg=AIKO, a=s * (1 - ease_out((t - T_B_STK2) / 0.25)), tilt=-0.02)
    if t >= T_B_STK2 and t < T_G0 + 0.1:
        s = ease_out((t - T_B_STK2) / 0.25) * (1 - ease((t - T_G0) / 0.25))
        note.sticky(ctx, f"10人だと 20回に19回が\nあいこ（約{pct(1 - results()['p'][10])}%）", 570, 1352, 44, "pink", fg=RED, a=s, tilt=-0.02)


# ---------- 1万回のマス目（4人・10人・40人） ----------
_GRID = {}


def flags(n):
    return (results()["kinds"][n] == 2).astype(int)


def grid_surface(n, m):
    """m 回ぶんまで埋めたマス目（決まった／あいこ／まだ）"""
    kk = (n, int(m) // N_COLS_G)
    if kk in _GRID:
        return _GRID[kk]
    if len(_GRID) > 400:
        _GRID.clear()
    fl = flags(n)
    cols = np.zeros((N_ROWS, N_COLS_G, 4), np.uint8)
    cols[:] = bgra(COL_NOT)
    pal = np.array([bgra(COL_AIKO), bgra(COL_DEC)], np.uint8)
    mm = len(fl) if m >= len(fl) else (int(m) // N_COLS_G) * N_COLS_G
    flat = cols.reshape(-1, 4)
    flat[:mm] = pal[fl[:mm]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=0)
    _GRID[kk] = (surf, keep)
    return _GRID[kk]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_H0 + 0.2) / 0.3))


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results()
    text(ctx, "それぞれ 1万回 やってみる", 520, 660, 46, INK, alpha=a)
    pr = clamp01((t - T_G0 - 0.5) / (T_G1 - T_G0 - 0.5))
    for n in G_PANELS:
        gx = G_X[n]
        cx = gx + N_COLS_G * G_CELL / 2
        surf, _ = grid_surface(n, N_TRIAL * pr)
        ctx.set_source_surface(surf, gx, G_Y0)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(gx - 3, G_Y0 - 3, N_COLS_G * G_CELL + 6, N_ROWS * G_CELL + 6)
        ctx.stroke()
        text(ctx, f"{n}人", cx, 722, 46, INK_DEC, alpha=a)
        if t >= T_GN:
            u = ease_out((t - T_GN) / 0.3) * a
            c = r["cnt"][n]
            if c == 0:
                text(ctx, "決まった回", cx, 1166, 30, INK, bold=False, alpha=u)
                text(ctx, "0回", cx, 1222, 60, RED, alpha=u)
                text(ctx, "計算では\n約370万回に1回", cx, 1296, 28, PENCIL, bold=False, alpha=u)
            else:
                text(ctx, "決まった回", cx, 1166, 30, INK, bold=False, alpha=u)
                text(ctx, f"{fmt(c)}回", cx, 1222, 52, INK, alpha=u)
                text(ctx, once_in(r["p"][n]), cx, 1284, 38, RED, alpha=u)
    note.legend(ctx, [(COL_DEC, "決まった回"), (COL_AIKO, "あいこの回"), (COL_NOT, "まだ")] if pr < 1.0 else
                [(COL_DEC, "決まった回"), (COL_AIKO, "あいこの回")], 1380, 30)
    text(ctx, "1マス＝1回", 520, 1424, 30, INK, bold=False, alpha=a)


# ---------- 人数ごとの割合（棒グラフ） ----------

def bar_x(n):
    return CH_X0 + (n - N_MIN) * CH_SLOT


def y_of(p):
    return CH_BASE - p * CH_H


def chart_alpha(t):
    if t < T_H0:
        return 0.0
    return ease((t - T_H0) / 0.35)


def draw_chart(ctx, t):
    a = chart_alpha(t)
    if a <= 0:
        return
    r = results()
    xr = CH_X0 + (N_MAX - N_MIN + 1) * CH_SLOT
    text(ctx, "人数ごとに 1万回やって 決まった割合", (CH_X0 + xr) / 2, 628, 36, INK, alpha=a)
    # 目盛り
    ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
    ctx.set_line_width(2)
    for p in (0.0, 1.0):
        ctx.move_to(CH_X0 - 10, y_of(p))
        ctx.line_to(xr, y_of(p))
        ctx.stroke()
    for p, lab in ((0.0, "0%"), (1.0, "100%")):
        text(ctx, lab, CH_X0 - 14, y_of(p), 26, PENCIL, align="right", bold=False, alpha=a)
    for n in (2, 10, 20, 30, 40):
        text(ctx, str(n), bar_x(n) + 7, CH_BASE + 30, 26, PENCIL, bold=False, alpha=a)
    text(ctx, "（人数）", 800, CH_BASE + 30, 26, PENCIL, bold=False, alpha=a)
    # 棒（左から順にのびる）
    for idx, n in enumerate(range(N_MIN, N_MAX + 1)):
        st = T_H_BARS + 0.06 * idx
        u = ease_out((t - st) / 0.35)
        if u <= 0:
            continue
        p = r["p"][n]
        fill(ctx, COL_BAR_HI if p >= RULE_P else COL_BAR_LO)
        ctx.rectangle(bar_x(n), CH_BASE - p * CH_H * u, CH_SLOT - 4, max(p * CH_H * u, 1.5))
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.55 * a))
        ctx.set_line_width(1.5)
        ctx.rectangle(bar_x(n), CH_BASE - p * CH_H * u, CH_SLOT - 4, max(p * CH_H * u, 1.5))
        ctx.stroke()
    # 50% の線（2回に1回）
    u50 = clamp01((t - T_H0 - 0.5) / 0.6)
    if u50 > 0:
        note.pen_line(ctx, CH_X0 - 10, y_of(RULE_P), xr, y_of(RULE_P) - 2, RED, seed=4, width=5, progress=u50, alpha=a)
        text(ctx, "50%（2回に1回）", xr - 2, y_of(RULE_P) - 22, 28, RED, align="right", alpha=a * u50)
    # 答え: 50%を保てるのは 4人まで
    if t >= T_REV:
        _, N = answer_by_rule(r["p"])
        s = ease_out((t - T_REV - 0.4) / 0.4)
        cxb = bar_x(2) + (bar_x(N) - bar_x(2)) / 2 + (CH_SLOT - 4) / 2
        note.pen_circle(ctx, cxb, y_of(0.62), (bar_x(N) - bar_x(2)) / 2 + 34, 78, RED, seed=9, width=6, progress=s, alpha=a)
        tw = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
        if tw > 0:
            text(ctx, f"50%以上で決まるのは {N}人まで", 640, y_of(0.9), 34, RED, alpha=ease_out((t - T_REV - 0.6) / 0.3) * tw)
    # ひねり: 2人と3人
    if t >= T_TW2:
        s = ease_out((t - T_TW2) / 0.4)
        cxb = bar_x(2) + (bar_x(3) - bar_x(2)) / 2 + (CH_SLOT - 4) / 2
        note.pen_circle(ctx, cxb, y_of(0.62), 46, 62, MARKER, seed=21, width=9, progress=s, alpha=a)
        note.pen_circle(ctx, cxb, y_of(0.62), 46, 62, RED, seed=22, width=5, progress=s, alpha=a)


# ---------- 答え ----------

def answer_key():
    return answer_by_rule(results()["p"])[0]


def reason_text():
    r = results()
    _, N = answer_by_rule(r["p"])
    return f"{N}人なら、1回で決まるのは {pcs(r['p'][N])}。\n{N + 1}人なら、{pcs(r['p'][N + 1])}に下がる。\n2回に1回以上 決まるのは {N}人まで。"


TW_Q = "では、いちばん決まりやすいのは\n何人？"


def tw_a():
    r = results()
    return f"2人と3人が いちばん決まりやすい。\nどちらも 約{pcs(r['p'][2])}（3回に2回）で決まる。"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"答えは『{KEY_LABEL[key]}』。", 570, 1100, 44, "yellow", fg=RED, a=b, tilt=-0.02)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 570, 1252, 32, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 570, 1252, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        for k_, ln_ in enumerate(tw_a().split("\n")):
            text(ctx, ln_, 570, 1370 + 42 * k_, 34, RED, alpha=e)


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


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に教室の4人（0秒目から手がはずみ、場面が寄った所から引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(820.0), 92.0)
        ys = (432, 530, 628)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q3[-1], sz)
        note.pen_line(ctx, 565 - w3 / 2 - 6, 682, 565 + w3 / 2 + 6, 678, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL_RULE, 565, 720, 30, INK, bold=False, alpha=a1)
            text(ctx, DETAIL, 565, 756, 28, PENCIL, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 806
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
        sz = min(56.0, 100.0 * 850.0 / wmax)
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 464, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 498, 540 + w2 / 2 + 6, 495, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 548
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


# ---------- 締め（3人の生徒） ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたのクラスなら、\n何人ずつに分けますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 972, 36, INK, bold=False, alpha=r)
    for i, (x, look) in enumerate(((330, 1), (580, 1), (830, -1))):        # 3人（まん中は右向き）。手は はずむ
        ph = (t - T_Q) / 0.62 + i * 0.3
        student(ctx, x, 1420.0, 3.1, i + 1, t, look, (0, SKIN, 1.0, 1.0), bob=4.0 * math.sin(2 * math.pi * ph),
                mouth=0.8 if math.sin(2 * math.pi * ph) > 0.2 else 0.0)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_chart(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_closing(ctx, t)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def clack(dur=0.09, seed=3):
    """みんなが一斉に手を出す「ぽん」"""
    t = _t(dur)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(4) / 4, mode="same")
    return (n * 0.5 + np.sin(2 * np.pi * 620 * t)) * np.exp(-t * 60)


def boo(dur=0.22):
    """あいこの「ぶっ」"""
    t = _t(dur)
    x = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.3 + np.sin(2 * np.pi * 150 * t)
    return x * np.exp(-t * 14) * 0.6


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(3):                                      # 冒頭: 手がはずむ ぽん・ぽん・ぽん
        mx.add(0.1 + 0.62 * i, clack(seed=20 + i), 0.3)
    # 4人: じゃん・けん・ぽん → 決まった
    mx.add(T_GO + 0.3, tick(1300, 0.04), 0.4)
    mx.add(T_GO + 0.9, tick(1500, 0.04), 0.4)
    mx.add(T_A_REV, clack(seed=1), 0.6)
    mx.add(T_A_REV + 0.05, bell(1046.5), 0.7)
    mx.add(T_A_REV + 0.05, chord([523.3, 659.3, 784.0], 1.2), 0.45)
    # 10人
    mx.add(T_B0 + 0.4, tick(1300, 0.04), 0.4)
    mx.add(T_B0 + 1.1, tick(1500, 0.04), 0.4)
    mx.add(T_B_REV, clack(seed=2), 0.6)
    mx.add(T_B_REV + 0.04, boo(), 0.55)
    # 1万回
    mx.add(T_G0 - 0.6, riser(0.8), 0.4)
    beat(mx, T_G0 + 0.4, T_G1, bpm=132, vol=0.5, accel=True)
    for i, n in enumerate(G_PANELS):
        mx.add(T_GN + 0.12 * i, bell([784.0, 880.0, 988.0][i], 0.8), 0.4)
    mx.add(T_G1, thump(), 0.5)
    # 棒グラフ
    for idx in range(0, N_MAX - N_MIN + 1, 2):
        mx.add(T_H_BARS + 0.06 * idx, tick(900 + 22 * idx, 0.02), 0.16)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)
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


def _enumerate_p(n):
    """手の出し方 3^n 通りを全部数える（n ≤ 8）"""
    import itertools
    ok = 0
    for hs in itertools.product(range(3), repeat=n):
        if len(set(hs)) == 2:
            ok += 1
    return ok / 3 ** n


def run_checks():
    r = results()
    p, cnt, kinds = r["p"], r["cnt"], r["kinds"]
    checks = []
    # (1) 式の照合
    for n in range(2, 9):
        checks.append((f"式 3(2^n−2)/3^n と 全部数え上げ（3^n 通り）が合う n={n}", exact_p_equal(n), _enumerate_p(n), 1e-12))
    checks.append(("Wikipedia（じゃんけん）: 4人のあいこ 13/27", 1 - exact_p_equal(4), 13 / 27, 1e-12))
    checks.append(("式: 2人・3人はどちらも 2/3", exact_p_equal(2), 2 / 3, 1e-12))
    checks.append(("式: 3人は 2/3", exact_p_equal(3), 2 / 3, 1e-12))
    checks.append(("式: 5人 10/27", exact_p_equal(5), 10 / 27, 1e-12))
    checks.append(("別の書き方（2つの手の確率の和）と同じ n=10", exact_p(10), exact_p_equal(10), 1e-12))
    checks.append(("Wikipedia（じゃんけん）: 1回2秒なら 30人で 約35.5時間（1/p(30) から）", 1 / exact_p_equal(30) * 2 / 3600, 35.5, 0.3))
    checks.append(("Wikipedia（じゃんけん）: 1回2秒なら 40人で 約85日（1/p(40) から）", 1 / exact_p_equal(40) * 2 / 86400, 85.0, 0.6))
    checks.append(("式: 40人は 約370万回に1回（理論値の逆数 3.65〜3.75百万）", float(3.65e6 <= 1 / exact_p_equal(40) <= 3.75e6), 1.0, 0.0))
    # (2) 1万回の割合が、式の値と合う（全人数。標準誤差の4.5倍まで）
    worst, worst_n = 0.0, 0
    for n in range(N_MIN, N_MAX + 1):
        e = exact_p_equal(n)
        se = max(math.sqrt(e * (1 - e) / N_TRIAL), 1e-4)
        z = abs(p[n] - e) / se
        if z > worst:
            worst, worst_n = z, n
    checks.append((f"1万回の割合と式の値（2〜40人のすべて）: ずれが標準誤差の何倍か（最大は {worst_n}人）", worst, 0.0, 4.5))
    for n in SHOW_NS:
        e = exact_p_equal(n)
        checks.append((f"1万回の割合 n={n}", p[n], e, max(4.5 * math.sqrt(e * (1 - e) / N_TRIAL), 2e-4)))
    checks.append(("40人: 1万回で決まった回 = 0", float(cnt[40]), 0.0, 0.0))
    checks.append(("画面の%（整数）が理論値と同じ 2人", float(pct(p[2])), float(pct(exact_p_equal(2))), 0.0))
    checks.append(("画面の%（整数）が理論値と同じ 3人", float(pct(p[3])), float(pct(exact_p_equal(3))), 0.0))
    checks.append(("画面の%（整数）が理論値と同じ 4人", float(pct(p[4])), float(pct(exact_p_equal(4))), 0.0))
    checks.append(("画面の%（整数）が理論値と同じ 5人", float(pct(p[5])), float(pct(exact_p_equal(5))), 0.0))
    checks.append(("10人のあいこ: 20回に19回（95%）= 画面の数字（理論と1万回）", float(pct(1 - p[10])), float(pct(1 - exact_p_equal(10))), 0.0))
    checks.append(("10人のあいこ 20回に19回 = 0.95 の近く（1万回）", 1 - p[10], 0.95, 0.01))
    checks.append(("10人のあいこ 20回に19回 = 0.95 の近く（理論）", 1 - exact_p_equal(10), 0.95, 0.01))
    # (3) 向き: 2人と3人が同じ、3人以降は減る
    checks.append(("理論: 3人以降は 人数が増えるほど 決まる割合が減る", float(all(exact_p_equal(n + 1) < exact_p_equal(n) for n in range(3, N_MAX))), 1.0, 0.0))
    checks.append(("1万回: 2人と3人が 同じ約67%（画面の整数が同じ）", float(pct(p[2]) == pct(p[3]) == 67), 1.0, 0.0))
    # (4) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key, N = answer_by_rule(p)
    kex, Nex = answer_by_rule({n: exact_p_equal(n) for n in range(N_MIN, N_MAX + 1)})
    checks.append(("N（1万回）= 理論値の N", float(N), float(Nex), 0.0))
    checks.append(("N = 4（p(4)≈52% ≥ 50% > p(5)≈37%）", float(N), 4.0, 0.0))
    checks.append(("規則の答え（1万回）= 規則の答え（理論）", float(key == kex), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 4人くらいまで・10人くらいまで・40人でも の順", float(LABELS == ["4人くらいまで", "10人くらいまで", "40人でも"]), 1.0, 0.0))
    checks.append(("規則の道具: 4人まで50%以上 → six", float(answer_by_rule({2: .67, 3: .67, 4: .52, 5: .37, 6: .25})[0] == "six"), 1.0, 0.0))
    checks.append(("規則の道具: 10人まで50%以上 → fifteen", float(answer_by_rule({n: (0.6 if n <= 10 else 0.3) for n in range(2, 41)})[0] == "fifteen"), 1.0, 0.0))
    checks.append(("規則の道具: 20人まで50%以上 → forty", float(answer_by_rule({n: (0.6 if n <= 20 else 0.3) for n in range(2, 41)})[0] == "forty"), 1.0, 0.0))
    checks.append(("規則の道具: 途中で一度50%を割ったら、そのあとは数えない", float(answer_by_rule({2: .6, 3: .4, 4: .6, 5: .6})[1] == 2), 1.0, 0.0))
    # (5) マス目: 3つの人数、どれも1万マス・数字が1万回の数と同じ
    checks.append(("マス目 = 80列×125行 = 1万", float(N_COLS_G * N_ROWS), float(N_TRIAL), 0.0))
    for n in G_PANELS:
        checks.append((f"マス目の決まった回数 n={n}（表示の数字と同じ）", float(flags(n).sum()), float(cnt[n]), 0.0))
        checks.append((f"マス目の回数 = 1万 n={n}", float(len(flags(n))), float(N_TRIAL), 0.0))
    # (6) 見本は1万回の中の1回
    S = samples()
    h4, h10 = r["hands"][4][S["i4"]], r["hands"][10][S["i10"]]
    checks.append(("見本 4人: 1万回の中の1回そのもの（手が一致）", float(list(map(int, h4)) == S["h4"]), 1.0, 0.0))
    checks.append(("見本 4人: ちょうど2種類 = 決まる", float(len(set(S["h4"])) == 2), 1.0, 0.0))
    checks.append(("見本 4人: 勝ったのは グー・3人", float(winner_hand(S["h4"]) == 0 and S["h4"].count(0) == 3), 1.0, 0.0))
    checks.append(("見本 10人: 1万回の中の1回そのもの（手が一致）", float(list(map(int, h10)) == S["h10"]), 1.0, 0.0))
    checks.append(("見本 10人: 3種類そろった = あいこ", float(len(set(S["h10"])) == 3), 1.0, 0.0))
    checks.append(("見本 10人: グー4・チョキ3・パー3（画面の集計）", float([S["h10"].count(k) for k in range(3)] == [4, 3, 3]), 1.0, 0.0))
    # (7) 感度: 出し方を偏らせても 答えは変わるか（情報。基準のほかは参考として表示し、N の違いは報告する）
    ex_bias = answer_by_rule({n: exact_p(n, ROCK_BIAS) for n in range(N_MIN, N_MAX + 1)})
    checks.append(("グーがやや多くても（35.6%）N は同じ（理論値）", float(ex_bias[1]), float(Nex), 0.0))
    # (8) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行: 3行の文字の大きさが同じ（同じ s3 で描く）", float(len(set([s3] * 3)) == 1), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (9) 場面の長さ（新しい場面・グラフは3秒以上）
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 4人（ぽん から 次の場面まで）3秒以上", float(T_B0 - T_A_REV >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 10人 3秒以上", float(T_G0 - T_B_REV >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: マス目の数字 3秒以上", float(T_H0 - T_GN >= 3.0), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (10) 冒頭の動き
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
    r = results()
    S = samples()
    print(f"長さ {DURATION:.1f}秒  4人ぽん {T_A_REV:.1f}  10人 {T_B0:.1f}/{T_B_REV:.1f}  マス目 {T_G0:.1f}-{T_G1:.1f}  数字 {T_GN:.1f}  棒 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本 4人: {[HAND_NAMES[x] for x in S['h4']]}（回 {S['i4']}）  10人: グー{S['h10'].count(0)}・チョキ{S['h10'].count(1)}・パー{S['h10'].count(2)}（回 {S['i10']}）")
    print(f"  問い3行の文字 {min(big3_size(820.0), 92.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(820.0), 92.0)) for l in BIG_Q3):.0f}px")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a())
    print("  マス目の数字: " + "  ".join(f"{n}人 {r['cnt'][n]}回({once_in(r['p'][n]) if r['cnt'][n] else '0回'})" for n in G_PANELS))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_GO + 0.8, T_A_REV + 0.6, T_A_REV + 2.0, T_B0 + 0.3, T_B0 + 1.4, T_B_REV + 0.6,
              T_B_STK2 + 0.8, T_G0 + 1.5, T_G1 - 0.2, T_GN + 1.2, T_H0 + 1.5, T_H0 + 3.2, T_REV + 0.9, T_ANS2 + 0.6,
              T_TW + 0.8, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
