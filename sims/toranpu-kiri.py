"""トランプ7回、リフルとヒンズー、どっちが混ざる？ 同じ52枚・同じ7回で、切り方だけ変えて1万回。— 2026-11-04 作成（公開予定 11.17・ナレーションなし・45秒前後）

くらべるのは「7回切ったあとの並びが、ほんとうに混ぜた並びとどれだけ近いか」。変える条件は切り方だけ（同じ52枚・同じ7回）。

計算（置き方・答えの決め方・乱数の順）は sims/shuffle_model.py に計算の前に固定してある。この絵のファイルはそれを読むだけで、変えていない。
  置き方  : 52枚をマークごと・数字順にそろえた所から始める。
            リフル  = 山を半分くらいに分け、左右の残りの枚数に比例して1枚ずつ落とす（Gilbert-Shannon-Reeds）。
            ヒンズー = 上から数枚ずつ抜いて手前に重ねる。1枚ごとに確率 p で区切る（p は回ごとに 0.15〜0.35 から。1回に抜くのは平均3〜7枚。仮定・実測ではない）。
  ものさし: ① 元の並びで隣どうしだったカードが、まだ隣にいる組の数 ② 同じマークが隣に並んだ組の数。どちらも「ほんとうに混ぜた1万回」と比べる。
  答えの決め方: ものさし①の中央値。ほんとうに混ぜた時の99%点を L とする。
            リフルが L 以下でヒンズーが L を超える → リフル ／ ヒンズーが L 以下でリフルが L を超える → ヒンズー
            どちらも L 以下、またはどちらも L を超える → 中央値の差が1組以内なら ほぼ同じ、それ以外は少ないほう
  結果    : 隣の組（中央値）リフル2・ヒンズー10・ほんとうに混ぜた時2 ／ 同じマークの組 リフル12・ヒンズー26・混ぜた時12 → リフル。

この動画で足した処理（shuffle_model.py の末尾。既存の結果は変わらない）:
  ・replay: 同じ乱数の順で1万回を数え直し、1回ごとの数（グラフ用）と見本の1回を取り出す。見本は「中央値と同じ値の回のうち、乱数の順で最初の1回」（極端な回は選ばない）。
  ・show_counts: ヒンズー7・10・20・30・100回を1万回ずつ数え直す（別の乱数。100回は説明欄用）。

問い: 「トランプを7回。/ どっちの切り方が / 混ざる？」  選択肢: A ヒンズー ／ B ほぼ同じ ／ C リフル（正解の記号 C）
見せ方: 手の絵（ヒンズー＝上から抜いて重ねる／リフル＝2つに分けて交互に落とす）→ 52枚を色の帯にして7回（見本の1回）→ 1万回のグラフ → 答え
ひねり: 「ヒンズーは何回で追いつく？」→ 元の隣の組が 7・10・20・30回で どう減るか（画面のものさしは「元の隣のまま残った組」1つだけ）。数えた回数ほどで追いつく。ただし本当に混ざるまでの回数は資料によって幅がある。リフル7回は「きれいに切ったときの研究結果」。
同じマークの組は 画面に出さず、説明欄だけに書く。
締め: 「あなたは、いつも何回切っていますか？」
言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」。見本は「たとえば、この1回では」。画面に「計算での見立て」を小さく1回。実在の会社・商品は出さない。
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sims"))
import shuffle_model as sm  # noqa: E402

SLUG = "toranpu-kiri"
OUT = ROOT / "out" / SLUG
CACHE = OUT / "cache"
N_TRIAL = sm.N
TW_TIMES = (7, 10, 20, 30)                           # ひねりの棒グラフ（ヒンズーを切る回数）
SHOW_TIMES = TW_TIMES + (100,)                       # 100回は説明欄の数字用（画面には出さない）
NB = 28                                              # グラフの目盛り 0〜27


def answer_by_rule(x, y, L):
    """x=リフル7回の中央値、y=ヒンズー7回の中央値（ものさし① 隣の組）、L=ほんとうに混ぜた時の99%点。
    戻り値 'riffle' / 'hindu' / 'same'。shuffle_model.main の規則と同じ（その結果は model.json の answer と照合する）"""
    if x <= L < y:
        return "riffle"
    if y <= L < x:
        return "hindu"
    if abs(x - y) <= 1:
        return "same"
    return "riffle" if x < y else "hindu"


def pct(x):
    return int(math.floor(x * 100 + 0.5))


_RES = {}


def _hash():
    return hashlib.md5((ROOT / "sims" / "shuffle_model.py").read_text(encoding="utf-8").encode("utf-8")).hexdigest()[:10]


def results():
    """1万回の数え直し（replay）と ヒンズー30・100回。時間がかかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    CACHE.mkdir(parents=True, exist_ok=True)
    model = json.loads((CACHE / "model.json").read_text(encoding="utf-8"))
    f = CACHE / ("show_%s_%s.json" % (_hash(), "-".join(str(x) for x in SHOW_TIMES)))
    if f.exists():
        z = json.loads(f.read_text(encoding="utf-8"))
    else:
        import time
        t0 = time.time()
        want = {"riffle": (int(model["riffle7"]["adj"]["median"]), int(model["riffle7"]["suit"]["median"])),
                "hindu": (int(model["hindu7"]["adj"]["median"]), int(model["hindu7"]["suit"]["median"]))}
        arrs, sample = sm.replay(want)
        print(f"  1万回の数え直し {time.time() - t0:.0f}秒")
        t0 = time.time()
        cnt = sm.show_counts(SHOW_TIMES, N_TRIAL)
        for v_ in cnt.values():
            v_['n'] = N_TRIAL
        print(f"  ヒンズー7・30・100回を1万回ずつ {time.time() - t0:.0f}秒")
        for v in sample.values():
            v["state"] = [v["state"][0], list(v["state"][1]), v["state"][2]]
        z = dict(arrs=arrs, sample=sample, counts={str(k): v for k, v in cnt.items()}, want=want)
        f.write_text(json.dumps(z, ensure_ascii=False), encoding="utf-8")
    arr = {k: {m: np.array(v[m], np.int16) for m in ("adj", "suit")} for k, v in z["arrs"].items()}
    sample = z["sample"]
    for v in sample.values():
        v["state"] = (v["state"][0], tuple(v["state"][1]), v["state"][2])
    cnt = {int(k): v for k, v in z["counts"].items()}
    _RES["m"] = dict(model=model, arr=arr, sample=sample, cnt=cnt, want=z["want"])
    return _RES["m"]


def med(a):
    return float(np.median(a))


def summary():
    r = results()
    m, a = r["model"], r["arr"]
    L = m["L"]
    x, y = m["riffle7"]["adj"]["median"], m["hindu7"]["adj"]["median"]
    return dict(L=L, x=x, y=y, key=answer_by_rule(x, y, L),
                rf_a=m["riffle7"]["adj"]["median"], hi_a=m["hindu7"]["adj"]["median"], rn_a=m["random"]["adj"]["median"],
                rf_s=m["riffle7"]["suit"]["median"], hi_s=m["hindu7"]["suit"]["median"], rn_s=m["random"]["suit"]["median"])


def report():
    r = results()
    S = summary()
    a = r["arr"]
    print(f"乱数の種 {sm.SEED}  {N_TRIAL}回ずつ  52枚  同じ7回")
    print(f"  答え: {S['key']}（model.json は {r['model']['answer']}）  L（ほんとうに混ぜた時の隣の組の99%点）= {S['L']}")
    print(f"  隣の組の中央値   リフル {S['rf_a']:.0f}  ヒンズー {S['hi_a']:.0f}  ほんとうに混ぜた時 {S['rn_a']:.0f}")
    print(f"  同じマークの組   リフル {S['rf_s']:.0f}  ヒンズー {S['hi_s']:.0f}  ほんとうに混ぜた時 {S['rn_s']:.0f}")
    for nm in ("riffle", "hindu", "rnd"):
        for k in ("adj", "suit"):
            x = a[nm][k]
            print(f"   {nm:7s} {k:4s}: 中央値 {med(x):.1f} 平均 {x.mean():.2f} 最小 {x.min()} 最大 {x.max()} 99%点 {np.sort(x)[N_TRIAL * 99 // 100]}")
    print("  ヒンズーを増やすと（各1万回・別の乱数）:")
    for t, v in sorted(r["cnt"].items()):
        print(f"    {t:>3}回: 隣の組 {v['adj']['median']:.0f}（99%点 {v['adj']['p99']}）  同じマーク {v['suit']['median']:.0f}（99%点 {v['suit']['p99']}）")
    for nm, sp in r["sample"].items():
        print(f"  見本 {nm}: 回 {sp['trial']}  隣 {sp['adj']}  同じマーク {sp['suit']}  p={sp['p']:.3f}")
    print("  リフル7回の隣の組が L 以下の割合 %.1f%%  ヒンズー7回 %.1f%%" % ((a["riffle"]["adj"] <= S["L"]).mean() * 100, (a["hindu"]["adj"] <= S["L"]).mean() * 100))


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)

if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    for nm, sp in results()["sample"].items():
        print(f"見本 {nm}: 1万回の中の {sp['trial']} 回目  隣 {sp['adj']}  同じマーク {sp['suit']}")
        print("   最後の並び:", sp["decks"][-1])
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, tick, whoosh)
from engine.parts import loop_back, stills  # noqa: E402
import toranpu_hands  # noqa: E402  2026-11-08 冒頭の手の絵を作り直し（白い札・裏の柄・腕までつながった手）

note.use()
note.DATE = "11.17"                                  # 日付欄（公開予定日）

SKIN, SKIN_D = "#f7d9bd", "#d9a679"
SLEEVE, CUFF = "#5b8fd6", "#f4f1e8"
COL_H, COL_R = "#e0801f", "#1fa593"                  # ヒンズー・リフルの差し色
TINT_H = "#fdebd3"
TINT_R = "#d9f3ef"
SUIT_COL = ["#3f7fb5", "#d8434e", "#f2a33a", "#3aa57a"]   # ♠ ♥ ♦ ♣
GRAY = "#9aa0ac"
GOLD, GOLD_D = "#f7b61f", "#a56d00"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は C（3番目）
LABELS = ["ヒンズー", "ほぼ同じ", "リフル"]
KEY_LABEL = {"hindu": "ヒンズー", "same": "ほぼ同じ", "riffle": "リフル"}
CORRECT = 2

BIG_Q3 = ["トランプを7回。", "どっちの切り方が", "混ざる？"]          # 1コマ目の3行（同じ大きさ）
BIG_Q = ["トランプを7回。", "どっちの切り方が混ざる？"]                # 定位置（上）の2行
DETAIL_RULE = "同じ52枚を同じ7回。ちがうのは切り方だけ"
DETAIL = "計算での見立て（ヒンズーの抜く枚数は仮定）"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 960.0, 840.0
CARD_X = 60.0
CARD_Y_INTRO, CARD_Y_FINAL = 878.0, 610.0
M_DUR, M_HOLD = 0.8, 0.3                            # 1回切る動き（途中で切らない）・次までの間
HAND_P = 4.4                                        # 手の絵の1周（秒）


def setup():
    global T_S0, T_SH0, T_M, T_ME, T_H0, T_H1, T_HN, T_REV, T_ANS2, T_TW, T_TW2, T_TW3, T_Q, DURATION, SCENES
    T_S0 = T_GO + 2.8                               # 手の絵 → 色の帯
    T_SH0 = T_S0 + 2.4                              # 1回目を切り始める
    T_M = [T_SH0 + i * (M_DUR + M_HOLD) for i in range(7)]
    T_ME = T_M[-1] + M_DUR                          # 7回目が終わる
    T_H0 = T_ME + 2.8                               # グラフへ
    T_H1 = T_H0 + 0.8 + 2.8                         # 1万回ぶんが積み終わる
    T_HN = T_H1 + 0.1                               # 数字
    T_REV = T_HN + 3.0                              # 答え
    T_ANS2 = T_REV + 2.2                            # 理由
    T_TW = T_ANS2 + 3.0                             # ひねり
    T_TW2 = T_TW + 2.8
    T_TW3 = T_TW2 + 2.0
    T_Q = T_TW3 + 4.0                               # 締め
    DURATION = T_Q + 4.0
    SCENES = [("手の絵（切り方）", 0.0, T_S0), ("色の帯・見本の1回", T_S0, T_H0), ("1万回のグラフ（答え・理由）", T_H0, T_TW),
              ("ひねり（ヒンズーを増やすと）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, w, col, outline=2.6, a=1.0):
    """太い線（ふちどり付き）。指・そで"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9 * a), (w, col, a)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


def mix(col, k):
    """色 col を 白と混ぜる（k=0 で col、k=1 で白）"""
    r, g, b, _ = hexrgb(col)
    return "#%02x%02x%02x" % tuple(int(round((v + (1 - v) * k) * 255)) for v in (r, g, b))


def suit_glyph(ctx, kind, cx, cy, s, col, a=1.0):
    """♠♥♦♣ を図形で描く（0=♠ 1=♥ 2=♦ 3=♣）。s は半分の大きさ"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)

    def heart(flip):
        ctx.move_to(0, 0.95 * flip)
        ctx.curve_to(-1.25, 0.2 * flip, -0.95, -0.9 * flip, 0, -0.4 * flip)
        ctx.curve_to(0.95, -0.9 * flip, 1.25, 0.2 * flip, 0, 0.95 * flip)
        ctx.close_path()

    ctx.set_source_rgba(*hexrgb(col, a))
    if kind == 1:
        heart(1)
        ctx.fill()
    elif kind == 0:
        heart(-1)
        ctx.fill()
        ctx.move_to(0, 0.1)
        ctx.line_to(0.4, 1.0)
        ctx.line_to(-0.4, 1.0)
        ctx.close_path()
        ctx.fill()
    elif kind == 2:
        ctx.move_to(0, -1.05)
        ctx.line_to(0.72, 0)
        ctx.line_to(0, 1.05)
        ctx.line_to(-0.72, 0)
        ctx.close_path()
        ctx.fill()
    else:
        for (x, y) in ((0, -0.5), (-0.55, 0.12), (0.55, 0.12)):
            ctx.arc(x, y, 0.48, 0, 2 * math.pi)
            ctx.fill()
        ctx.move_to(0, 0.0)
        ctx.line_to(0.34, 1.0)
        ctx.line_to(-0.34, 1.0)
        ctx.close_path()
        ctx.fill()
    ctx.restore()


# ---------- 絵: 手と山 ----------

def layer(ctx, x, y, w, h, tint, a=1.0):
    rrect(ctx, x, y, w, h, 3)
    ctx.set_source_rgba(*hexrgb(tint, a))
    ctx.fill_preserve()
    _stroke(ctx, 2.2, INK, 0.85 * a)


def sleeve(ctx, x0, y0, x1, y1, w):
    """そで。(x0,y0) が体のほう、(x1,y1) が手首（白いカフス付き）"""
    thick(ctx, [(x0, y0), (x1, y1)], w, SLEEVE)
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    thick(ctx, [(x1 - ux * 22, y1 - uy * 22), (x1, y1)], w + 6, CUFF)


def palm(ctx, x, y, w, h, r=16):
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)


def finger(ctx, pts, w=22):
    thick(ctx, pts, w, SKIN, 2.6)


HIN_TINT = ["#ffb3a7", "#ffd98a", "#b8e6a8", "#a6d4ff", "#d9b8ff", "#ffc2e0", "#b8f0e6"]
H_W, H_LH = 170.0, 13.0                              # ヒンズーの山の幅・1パックの厚さ
H_X = 115.0
H_DECK_BOT, H_PILE_BOT = 150.0, 335.0


def hindu_art(ctx, ox, oy, t):
    """ヒンズー: 上の手が持つ山の上から 数枚ずつ抜いて、下の手の上へ重ねていく（1周 HAND_P 秒でくり返す）"""
    n = int(t // HAND_P)
    u = (t % HAND_P) / HAND_P
    K = 7
    slot = 1 / 8
    ctx.save()
    ctx.translate(ox, oy)
    # うしろ側: 下の手のそで・手のひら、上の手のそで・手の甲
    sleeve(ctx, -30, 392, 105, 362, 56)
    palm(ctx, 95, 332, 215, 46)
    sleeve(ctx, 440, 26, 330, 30, 54)
    palm(ctx, 120, 6, 222, 50)
    pile_n = sum(1 for j in range(K) if u >= j * slot + slot * 0.9)
    packets = [(j, (u - j * slot) / (slot * 0.9)) for j in range(K) if j * slot < u < j * slot + slot * 0.9]
    deck_n = K - pile_n - len(packets)

    def tint(j, cyc):                                   # j 番目に抜くパックの色（周ごとに順番が反転する）
        return HIN_TINT[K - 1 - j] if cyc % 2 == 0 else HIN_TINT[j]

    if u <= 7 / 8:
        for L in range(deck_n):                         # 上の手の山（下から L 番目 = j=K-1-L のパック）
            layer(ctx, H_X, H_DECK_BOT - (L + 1) * H_LH, H_W, H_LH, tint(K - 1 - L, n))
        for j in range(pile_n):
            layer(ctx, H_X, H_PILE_BOT - (j + 1) * H_LH, H_W, H_LH, tint(j, n))
    else:                                               # 周の終わり: 重ねた山が 次の周の「上の手の山」へ入れ替わる
        e = ease((u - 7 / 8) / (1 / 8))
        for j in range(K):
            layer(ctx, H_X, H_PILE_BOT - (j + 1) * H_LH, H_W, H_LH, tint(j, n), 1 - e)
        for L in range(K):
            layer(ctx, H_X, H_DECK_BOT - (L + 1) * H_LH, H_W, H_LH, tint(K - 1 - L, n + 1), e)
    for j, v in packets:                                # 抜いたパックが 左へふくらんで 下の山へ
        vv = ease(v)
        x = H_X - 78 * math.sin(math.pi * vv)
        y0 = H_DECK_BOT - (K - j) * H_LH
        y1 = H_PILE_BOT - (j + 1) * H_LH
        y = y0 + (y1 - y0) * vv - 22 * math.sin(math.pi * vv)
        layer(ctx, x, y, H_W, H_LH, tint(j, n))
    # 手前側: 下の手の指（山の手前に回る）と、上の手の指（親指は左の端・4本は右の端）
    finger(ctx, [(112, 372), (104, 352), (100, 322)], 24)
    for i in range(4):
        finger(ctx, [(268 + i * 15, 374), (276 + i * 15, 352), (280 + i * 15, 326 + 3 * abs(i - 1.5))], 20)
    finger(ctx, [(150, 44), (126, 96), (121, 146)], 26)
    for i in range(3):
        finger(ctx, [(300 + i * 14, 48), (298 + i * 15, 100), (290 + i * 14, 148)], 20)
    ctx.restore()


R_TINT_L, R_TINT_R = "#bcd9ff", "#ffd2a8"
R_W, R_LH = 118.0, 12.0
R_BOT = 205.0
R_PILE_BOT = 345.0


def riffle_art(ctx, ox, oy, t):
    """リフル: 山を2つに分け、左右から交互に 1枚ずつ落として 1つに重ねる（1周 HAND_P 秒でくり返す）"""
    u = (t % HAND_P) / HAND_P
    K = 7
    slot = 1 / 17
    pile_w = R_W + 30
    px = 200 - pile_w / 2
    lx, rx = 40.0, 400.0 - 40.0 - R_W
    ctx.save()
    ctx.translate(ox, oy)
    sleeve(ctx, -30, 262, 40, 236, 54)
    sleeve(ctx, 430, 262, 360, 236, 54)
    palm(ctx, 28, 205, 150, 40)
    palm(ctx, 222, 205, 150, 40)
    done = sum(1 for i in range(2 * K) if u >= i * slot + 2 * slot)
    flying = [(i, (u - i * slot) / (2 * slot)) for i in range(2 * K) if i * slot < u < i * slot + 2 * slot]
    if u <= 15 / 17:
        gone_l = sum(1 for i in range(2 * K) if i % 2 == 0 and u > i * slot)
        gone_r = sum(1 for i in range(2 * K) if i % 2 == 1 and u > i * slot)
        for L in range(K - gone_l):
            layer(ctx, lx, R_BOT - (L + 1) * R_LH, R_W, R_LH, R_TINT_L)
        for L in range(K - gone_r):
            layer(ctx, rx, R_BOT - (L + 1) * R_LH, R_W, R_LH, R_TINT_R)
        for i in range(done):
            layer(ctx, px, R_PILE_BOT - (i + 1) * R_LH, pile_w, R_LH, R_TINT_L if i % 2 == 0 else R_TINT_R)
    else:                                               # 周の終わり: 重ねた山が 左右2つの山へ入れ替わる
        e = ease((u - 15 / 17) / (2 / 17))
        for i in range(2 * K):
            layer(ctx, px, R_PILE_BOT - (i + 1) * R_LH, pile_w, R_LH, R_TINT_L if i % 2 == 0 else R_TINT_R, 1 - e)
        for L in range(K):
            layer(ctx, lx, R_BOT - (L + 1) * R_LH, R_W, R_LH, R_TINT_L, e)
            layer(ctx, rx, R_BOT - (L + 1) * R_LH, R_W, R_LH, R_TINT_R, e)
    for i, v in flying:
        vv = ease(v)
        left = i % 2 == 0
        xs = lx + (R_W - pile_w) / 2 if left else rx + (R_W - pile_w) / 2
        y = (R_BOT - 4) + ((R_PILE_BOT - (i + 1) * R_LH) - (R_BOT - 4)) * vv
        layer(ctx, xs + (px - xs) * vv, y, pile_w, R_LH, R_TINT_L if left else R_TINT_R)
    # 親指（内側の上から 1枚ずつはなす）と指（外側）
    finger(ctx, [(160, 232), (168, 190), (152, 148 + 10 * math.sin(2 * math.pi * u * 7))], 26)
    finger(ctx, [(240, 232), (232, 190), (248, 148 + 10 * math.sin(2 * math.pi * u * 7 + math.pi))], 26)
    for i in range(3):
        finger(ctx, [(52 + i * 15, 244), (46 + i * 15, 214), (40 + i * 15, 186)], 20)
        finger(ctx, [(300 + i * 15, 244), (306 + i * 15, 214), (312 + i * 15, 186)], 20)
    ctx.restore()


# ---------- 絵: 色の帯 ----------
SX0, SW_ = 30.0, 900.0 / 52
PANEL_TOP = {"hindu": 48.0, "riffle": 440.0}
STR_DY0, STR_H = 80.0, 260.0
_POS = {}


def deck_pos(name):
    """見本の回の、切る前・1回ごとのあとの 並び → カードごとの位置（8本の配列）"""
    if name not in _POS:
        decks = results()["sample"][name]["decks"]
        arr = []
        for d in decks:
            p = np.zeros(52)
            for i, c in enumerate(d):
                p[c] = i
            arr.append(p)
        _POS[name] = arr
    return _POS[name]


def strip_col(c):
    return mix(SUIT_COL[c // 13], 0.42 * (1 - (c % 13) / 12.0))


def adj_pairs(deck):
    return [i for i in range(51) if abs(deck[i + 1] - deck[i]) == 1 and deck[i] // 13 == deck[i + 1] // 13]


def strip_state(t):
    """時刻 t の帯の様子: (位置の配列, いま動いているか, 静止している並びの番号 k, 静止してからの秒, 次に動くまでの秒, 切った回数)"""
    i = -1
    for j in range(7):
        if T_M[j] <= t:
            i = j
    if i < 0:
        return 0, None, t - (T_S0 + 0.5), T_M[0] - t, 0
    u = (t - T_M[i]) / M_DUR
    if u < 1.0:
        return i, u, -1.0, 0.0, i + 1
    k = i + 1
    return k, None, t - (T_M[i] + M_DUR), (T_M[k] - t) if k < 7 else 99.0, k


def swap_parts(j, u):
    """切る動き（u=0〜1）の途中の、場所 j の 古い帯（持ち上がる）と 新しい帯（降りてくる）の（ずれ・濃さ）"""
    d = 0.50 * (j // 4) / 12.0
    av = ease(clamp01((u - d) / 0.40))
    bv = ease(clamp01((u - d - 0.04) / 0.36))
    return -26.0 * av, 1.0 - ease(clamp01((av - 0.5) / 0.5)), -26.0 * (1 - bv), ease(clamp01(bv / 0.5))


def draw_strip_panel(ctx, name, t):
    S = results()["sample"][name]
    pos = deck_pos(name)
    k, u, since, until, nmove = strip_state(t)
    top = PANEL_TOP[name]
    col = COL_H if name == "hindu" else COL_R
    rrect(ctx, 12, top, CARD_W - 24, 388, 14)                       # パネル
    ctx.set_source_rgba(*hexrgb(TINT_H if name == "hindu" else TINT_R, 0.75))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, col, 0.8)
    nm = "ヒンズー" if name == "hindu" else "リフル"
    text(ctx, nm, 40, top + 30, 42, INK, align="left")
    text(ctx, "はじめ" if nmove == 0 else f"{nmove}回目", 262, top + 30, 34, INK, align="left", bold=False)
    # 元の隣のまま（●）の数: 動いている間は前の数、止まったら新しい数
    kk = k if u is None else k
    cnt = len(adj_pairs(S["decks"][kk]))
    ctx.arc(468, top + 31, 9, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(GOLD))
    ctx.fill_preserve()
    _stroke(ctx, 2.2, GOLD_D, 0.95)
    text(ctx, "元の隣のまま", 486, top + 30, 30, INK, align="left", bold=False)
    final = t >= T_ME + 0.2
    text(ctx, f"{cnt}", 666, top + 30, 46, RED if final else INK, align="left")
    text(ctx, "組", 666 + core.text_width(f"{cnt}", 46) + 6, top + 33, 30, INK, align="left", bold=False)
    # 帯: 切るときは 左から順に（4本ずつのかたまりで）古い帯が持ち上がって消え、新しい帯が上から降りてくる。
    # どの瞬間も 52本ぶんの幅が埋まっている（古い帯か新しい帯のどちらかが、その場所にいる）
    y0 = top + STR_DY0
    decks = S["decks"]

    def one(card, slot, dy, al):
        if al <= 0:
            return
        rrect(ctx, SX0 + slot * SW_ + 1, y0 + dy, SW_ - 2, STR_H, 3)
        ctx.set_source_rgba(*hexrgb(strip_col(card), al))
        ctx.fill_preserve()
        _stroke(ctx, 1.6, INK, 0.55 * al)

    if u is None:
        for j in range(52):
            one(decks[k][j], j, 0.0, 1.0)
    else:
        for j in range(52):
            dy0, a0, dy1, a1 = swap_parts(j, u)
            one(decks[k][j], j, dy0, a0)
            one(decks[k + 1][j], j, dy1, a1)
    # ●（元の隣のまま）
    if u is None:
        al = clamp01(since / 0.25) * clamp01(until / 0.2)
        if al > 0:
            for j in adj_pairs(S["decks"][k]):
                ctx.arc(SX0 + (j + 1) * SW_, top + 63, 7.5, 0, 2 * math.pi)
                ctx.set_source_rgba(*hexrgb(GOLD, al))
                ctx.fill_preserve()
                _stroke(ctx, 2.0, GOLD_D, 0.95 * al)


def draw_strips_content(ctx, t):
    text(ctx, "たとえば、この1回では", 30, 24, 34, PENCIL, align="left", bold=False)
    for i in range(4):                                              # 色の見本（マーク）
        x = 560 + i * 44
        rrect(ctx, x, 6, 34, 34, 7)
        ctx.set_source_rgba(*hexrgb(SUIT_COL[i]))
        ctx.fill_preserve()
        _stroke(ctx, 2, INK, 0.8)
        suit_glyph(ctx, i, x + 17, 23, 9.5, "#ffffff")
    text(ctx, "色＝マーク", 744, 24, 32, PENCIL, align="left", bold=False)
    draw_strip_panel(ctx, "hindu", t)
    draw_strip_panel(ctx, "riffle", t)


# ---------- 絵: 手の絵の場面 ----------
PN_X = {"hindu": 24.0, "riffle": 486.0}
PN_W, PN_H = 450.0, 548.0
ART_X = {"hindu": 22.0, "riffle": 484.0}
ART_Y = {"hindu": 123.0, "riffle": 113.0}
ART_S = {"hindu": 1.08, "riffle": 1.08}


def draw_hands_content(ctx, t, m):
    for name, nm, l1, l2, tint, col in (("hindu", "ヒンズー", "上から抜いて", "重ねる", TINT_H, COL_H),
                                         ("riffle", "リフル", "2つに分けて", "交互に落とす", TINT_R, COL_R)):
        x = PN_X[name]
        rrect(ctx, x, 14, PN_W, PN_H, 16)
        k0 = ease(clamp01(t / 0.9))                                  # 冒頭: 濃い色から うすい色へ（0秒目から動かす）
        c0, c1 = hexrgb(mix(col, 0.55)), hexrgb(tint)
        ctx.set_source_rgba(*(c0[i] + (c1[i] - c0[i]) * k0 for i in range(3)), 0.9)
        ctx.fill_preserve()
        _stroke(ctx, 3, col, 0.85)
        cx = x + PN_W / 2
        text(ctx, nm, cx, 50, 50, INK)
        note.pen_line(ctx, cx - core.text_width(nm, 50) / 2 - 4, 78, cx + core.text_width(nm, 50) / 2 + 4, 76, col, seed=3, width=6)
        text(ctx, l1, cx, 108, 30, INK, bold=False)
        text(ctx, l2, cx, 142, 30, INK, bold=False)
        ctx.save()                                                  # 手は パネルの外へはみ出さない（そでは 枠から入ってくる）
        rrect(ctx, x + 2, 14, PN_W - 4, PN_H - 2, 16)
        ctx.clip()
        ctx.translate(ART_X[name], ART_Y[name])
        ctx.scale(ART_S[name], ART_S[name])
        if name == "hindu":
            toranpu_hands.hindu_art(ctx, 0, 0, t, HAND_P)
        else:
            toranpu_hands.riffle_art(ctx, 0, 0, t, HAND_P)
        ctx.restore()
    if m >= 0.999:                                                  # 下の帯は 場面が定位置に着いてから（下端が y=1450 を超えないため）
        a = ease_out((t - T_GO) / 0.3)
        if a > 0:
            text(ctx, "ちがうのは、切り方だけ", CARD_W / 2, 650, 52, INK, alpha=a)
            note.pen_line(ctx, 130, 686, 830, 683, RED, seed=9, width=7, progress=clamp01((t - T_GO) / 0.5), alpha=a)
            text(ctx, "52枚を 色の帯にして、7回切ってみる", CARD_W / 2, 750, 36, INK, bold=False, alpha=a)


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, PN_H + 34 + (CARD_H - PN_H - 34) * m, 24)   # 冒頭は 手のパネルぶんの高さ（下に空の枠を残さない）
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ah = 1 - ease((t - T_S0) / 0.5)
    ast = ease((t - T_S0) / 0.5)
    if ah > 0:
        ctx.push_group()
        draw_hands_content(ctx, t, m)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ah)
    if ast > 0:
        ctx.push_group()
        draw_strips_content(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ast)
    # カウントダウンの合図（冒頭だけ。2枚の絵のあいだ）
    if t >= T_CD[0] and t < T_MOVE + 0.2:
        a2 = ease_out((t - T_CD[0]) / 0.2) * (1 - clamp01((t - T_MOVE) / 0.2))
        n = sum(1 for c in T_CD if c <= t)
        age = t - T_CD[n - 1]
        text(ctx, "予想して！", CARD_W / 2, 44, 28, RED, alpha=a2)
        cx, cy = CARD_W / 2, 124.0
        ctx.arc(cx, cy, 44, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.97 * a2))
        ctx.fill()
        note.pen_circle(ctx, cx, cy, 44, 42, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a2)
        sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
        ctx.save()
        ctx.translate(cx, cy + 2)
        ctx.scale(sc, sc)
        text(ctx, str(len(T_CD) + 1 - n), 0, 0, 62, INK, alpha=a2)
        ctx.restore()
    ctx.restore()


def scene_alpha(t):
    if t < T_H0:
        return 1.0
    return 1 - ease((t - T_H0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.06 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: ほんの少し寄ったところから引く（パネル全体が いつも画面に収まる弱さ）
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


# ---------- グラフ（1万回のぶんの隣の組の数） ----------
HX0, BW, HH = 100.0, 30.0, 185.0
SCALE = 0.30                                         # 縦軸: 1万回のうち 30% で上端
PAN_A, PAN_B = 704.0, 972.0                          # 各パネルの見出しの y
PAN_BASE = {"hindu": 910.0, "riffle": 1178.0}


def hist_alpha(t):
    if t < T_H0:
        return 0.0
    return ease((t - T_H0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    S = summary()
    text(ctx, "元の隣のまま残った組の数　少ないほどよく混ざる", 565, 628, 36, INK, alpha=a)
    text(ctx, "色＝切り方7回　灰色の線＝ほんとうに混ぜた時", 565, 668, 32, PENCIL, bold=False, alpha=a)
    pr = clamp01((t - T_H0 - 0.8) / (T_H1 - T_H0 - 0.8))
    m_rev = N_TRIAL if pr >= 1 else int(N_TRIAL * ease(pr))
    rnd = np.bincount(r["arr"]["rnd"]["adj"], minlength=NB)[:NB] / N_TRIAL
    for name, hy, nm, col, key_a in (("hindu", PAN_A, "ヒンズー7回", COL_H, "hi_a"), ("riffle", PAN_B, "リフル7回", COL_R, "rf_a")):
        base = PAN_BASE[name]
        text(ctx, nm, 100, hy, 36, INK, align="left", alpha=a)
        if name == "hindu":
            text(ctx, "中央値＝1万回の ちょうど真ん中の値", 925, hy, 30, PENCIL, align="right", bold=False, alpha=a)
        else:
            text(ctx, f"{m_rev:,} / 10,000 回目", 925, hy, 30, PENCIL, align="right", bold=False, alpha=a)
        ctx.move_to(HX0 - 4, base)
        ctx.line_to(HX0 + NB * BW + 4, base)
        _stroke(ctx, 3, INK, 0.7 * a)
        h_now = np.bincount(r["arr"][name]["adj"][:m_rev], minlength=NB)[:NB] / N_TRIAL
        for b in range(NB):                                          # 色の棒（積み上がる）
            hg = min(1.0, h_now[b] / SCALE) * HH
            if hg > 0.5:
                rrect(ctx, HX0 + b * BW + 1.5, base - hg, BW - 3, hg, 3)
                ctx.set_source_rgba(*hexrgb(col, 0.85 * a))
                ctx.fill_preserve()
                _stroke(ctx, 1.4, INK, 0.5 * a)
        for b in range(NB):                                          # 灰色の線（ほんとうに混ぜた時）を 上に重ねる
            hg = min(1.0, rnd[b] / SCALE) * HH
            if hg > 0.5:
                rrect(ctx, HX0 + b * BW + 1.5, base - hg, BW - 3, hg, 3)
                ctx.set_source_rgba(*hexrgb(GRAY, 0.22 * a))
                ctx.fill_preserve()
                _stroke(ctx, 2.6, "#5d6472", 0.9 * a)
        for tk in range(0, NB, 5):
            text(ctx, str(tk), HX0 + tk * BW + BW / 2, base + 22, 24, PENCIL, alpha=a, bold=False)
        if t >= T_HN:
            u = ease_out((t - T_HN) / 0.3) * a
            text(ctx, f"中央値 {S[key_a]:.0f}組", 765, base - HH + 36, 56, RED, alpha=u)
            xl = 268.0                                               # 灰色の山のそばに 1つだけ
            text(ctx, f"ほんとうに混ぜた時 {S['rn_a']:.0f}組", xl, base - HH + 24, 28, "#5d6472", align="left", bold=False, alpha=u)


# ---------- ひねり（ヒンズーを増やすと） ----------
TW_X = (180.0, 360.0, 540.0, 720.0)
TW_BASE, TW_H, TW_MAX = 960.0, 250.0, 11.0


def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


def twist_vals():
    """ヒンズーを切る回数ごとの（回数, 隣の組の中央値, 同じマークの組の中央値）。1万回ずつ数えた値"""
    r = results()
    return [(tt, r["cnt"][tt]["adj"]["median"], r["cnt"][tt]["suit"]["median"]) for tt in TW_TIMES]


def catch_up_n():
    """隣の組の中央値が ほんとうに混ぜた時の中央値に 初めて届く（以下になる）回数。届かなければ None"""
    base = summary()["rn_a"]
    for tt, va, _vs in twist_vals():
        if va <= base:
            return tt
    return None


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    S = summary()
    text(ctx, TW_Q, 565, 628, 40, INK, alpha=a)
    text(ctx, "元の隣のまま残った組の数（1万回ずつ・中央値）", 565, 668, 30, PENCIL, bold=False, alpha=a)
    ctx.move_to(100, TW_BASE)
    ctx.line_to(800, TW_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    pr = ease(clamp01((t - T_TW - 0.6) / 1.6))
    ly = TW_BASE - S["rn_a"] / TW_MAX * TW_H
    ctx.move_to(100, ly)
    ctx.line_to(812, ly)
    ctx.set_dash([10, 8])
    _stroke(ctx, 3, RED, 0.85 * a)
    ctx.set_dash([])
    text(ctx, f"ほんとうに\n混ぜた時\n{S['rn_a']:.0f}組", 890, ly - 18, 28, RED, bold=False, alpha=a)
    for i, (tt, va, vs) in enumerate(twist_vals()):
        x = TW_X[i]
        hg = va / TW_MAX * TW_H * pr
        rrect(ctx, x - 62, TW_BASE - hg, 124, max(hg, 1.0), 8)
        ctx.set_source_rgba(*hexrgb(COL_H, 0.88 * a))
        ctx.fill_preserve()
        _stroke(ctx, 2.0, INK, 0.6 * a)
        text(ctx, f"{va:.0f}組", x, TW_BASE - hg - 30, 44, RED, alpha=a * pr)
        text(ctx, f"{tt}回", x, TW_BASE + 38, 40, INK, alpha=a)


# ---------- 答え ----------

def answer_key():
    return summary()["key"]


TW_Q = "ヒンズーは何回で追いつく？"
READ_NOTE = "残った組が少ないほど よく混ざる"


def tw_a():
    n = catch_up_n()
    return f"ヒンズーは{n}回ほどで\nリフル7回に追いつく" if n else f"ヒンズーは{TW_TIMES[-1]}回でも\nリフル7回に追いつかない"


TW_B = "本当に混ざるまでの回数は\n資料によって幅がある"
TW_C = "7回で混ざるのは、リフルをきれいに切った場合"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 570, 1262, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, READ_NOTE, 570, 1380, 40, "mint", a=c, tilt=0.01)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        note.sticky(ctx, tw_a(), 570, 1105, 36, "pink", fg=RED, a=e, tilt=-0.012)
    if t >= T_TW3:
        f_ = ease_out((t - T_TW3) / 0.3)
        note.sticky(ctx, TW_B, 570, 1268, 36, "mint", a=f_, tilt=0.01)
        text(ctx, TW_C, 570, 1384, 32, INK, bold=False, alpha=f_)


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
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行・前提・三択（横1列）。その下に 2つの切り方の手の絵（0秒目から動き、場面が寄ったところから引く）"""
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
            text(ctx, DETAIL_RULE, 565, 716, 36, INK, bold=False, alpha=a1)
            text(ctx, DETAIL, 565, 758, 34, PENCIL, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 812
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)

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


# ---------- 締め（トランプの扇） ----------

def draw_card_face(ctx, cx, cy, w, h, ang, kind, num):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang)
    rrect(ctx, -w / 2, -h / 2, w, h, 14)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    suit_glyph(ctx, kind, 0, 0, w * 0.26, SUIT_COL[kind])
    suit_glyph(ctx, kind, -w / 2 + 28, -h / 2 + 52, 12, SUIT_COL[kind])
    text(ctx, num, -w / 2 + 28, -h / 2 + 24, 30, SUIT_COL[kind])
    ctx.restore()


def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたは、いつも\n何回切っていますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 950, 36, INK, bold=False, alpha=r)
    ctx.save()
    ctx.push_group()
    rrect(ctx, 90, 1010, 900, 430, 24)
    ctx.set_source_rgba(*hexrgb("#e9f3ee", 0.97))
    ctx.fill()
    sw = 0.06 * math.sin(1.6 * (t - T_Q))
    for i, (k, nmb) in enumerate(((0, "A"), (1, "7"), (2, "K"), (3, "3"))):
        draw_card_face(ctx, 270 + i * 150, 1250 + 8 * math.sin(1.3 * t + i), 190, 290, -0.42 + i * 0.28 + sw, k, nmb)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    rrect(ctx, 90, 1010, 900, 430, 24)
    _stroke(ctx, 3.5, INK, 0.75 * q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_hist(ctx, t)
        draw_twist(ctx, t)
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

def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 164.8, 196.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for tt in np.arange(0.1, T_S0 - 0.3, HAND_P / 16):          # 手の絵: パタパタ
        mx.add(float(tt), tick(1700 if int(tt / (HAND_P / 16)) % 2 else 2100, 0.03), 0.20)
    mx.add(T_S0 - 0.3, riser(0.6), 0.3)
    for i, tm in enumerate(T_M):                                 # 1回切るごと
        mx.add(tm, whoosh(M_DUR), 0.28)
        mx.add(tm + M_DUR, blip(520 + 40 * i, 0.08), 0.28)
    mx.add(T_ME + 0.2, bell(784.0, 0.9), 0.4)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)
    beat(mx, T_H0 + 0.8, T_H1, bpm=132, vol=0.5, accel=True)
    mx.add(T_HN, bell(784.0, 0.9), 0.45)
    mx.add(T_H1, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    for i in range(3):
        mx.add(T_TW + 0.6 + 0.5 * i, bell([784.0, 880.0, 988.0][i], 0.8), 0.35)
    mx.add(T_TW2, blip(659.3, 0.14), 0.3)
    mx.add(T_TW3, blip(740.0, 0.14), 0.3)
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


def run_checks():
    r = results()
    S = summary()
    a = r["arr"]
    m = r["model"]
    checks = []
    n = N_TRIAL
    # (1) 計算の整合（replay は shuffle_model.main と同じ乱数の順 → 同じ数になるか）
    checks.append(("1万回ずつ（ほんとうに混ぜた・リフル・ヒンズー）", float(len(a["rnd"]["adj"]) + len(a["riffle"]["adj"]) + len(a["hindu"]["adj"])), 3.0 * n, 0.0))
    for nm, mk in (("rnd", "random"), ("riffle", "riffle7"), ("hindu", "hindu7")):
        for k in ("adj", "suit"):
            x = a[nm][k]
            checks.append((f"数え直した中央値 = model.json（{nm}・{k}）", med(x), float(m[mk][k]["median"]), 1e-9))
            checks.append((f"数え直した平均 = model.json（{nm}・{k}）", round(float(x.mean()), 2), float(m[mk][k]["mean"]), 1e-9))
            checks.append((f"数え直した最大 = model.json（{nm}・{k}）", float(x.max()), float(m[mk][k]["max"]), 0.0))
    checks.append(("L（混ぜた時の隣の組の99%点）を数え直しても同じ", float(np.sort(a["rnd"]["adj"])[n * 99 // 100]), float(m["L"]), 0.0))
    # (2) 答えの規則
    key = answer_key()
    checks.append(("規則の答え = model.json の answer（リフル）", float(KEY_LABEL[key] == m["answer"]), 1.0, 0.0))
    checks.append(("規則の答え = riffle", float(key == "riffle"), 1.0, 0.0))
    checks.append(("リフル7回の中央値は L 以下・ヒンズー7回は L を超える", float(S["rf_a"] <= S["L"] < S["hi_a"]), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号の並び: ヒンズー・ほぼ同じ・リフル の順", float(LABELS == ["ヒンズー", "ほぼ同じ", "リフル"]), 1.0, 0.0))
    for args, k_ in (((2, 10, 6), "riffle"), ((10, 2, 6), "hindu"), ((3, 4, 6), "same"), ((8, 9, 6), "same"), ((8, 12, 6), "riffle"), ((12, 8, 6), "hindu")):
        checks.append((f"規則の道具: リフル{args[0]}・ヒンズー{args[1]}・L={args[2]} → {k_}", float(answer_by_rule(*args) == k_), 1.0, 0.0))
    # (3) 見本の1回は 1万回の中の1回そのもの
    for nm in ("riffle", "hindu"):
        sp = r["sample"][nm]
        i = sp["trial"]
        decks = sp["decks"]
        checks.append((f"見本（{nm}）: 1万回の中の {i} 回目（0〜9999）", float(0 <= i < n), 1.0, 0.0))
        checks.append((f"見本（{nm}）: 隣の組 = 1万回の記録の {i} 回目", float(len(adj_pairs(decks[-1]))), float(a[nm]["adj"][i]), 0.0))
        checks.append((f"見本（{nm}）: 同じマークの組 = 1万回の記録の {i} 回目", float(sm.suit(decks[-1])), float(a[nm]["suit"][i]), 0.0))
        checks.append((f"見本（{nm}）: 隣の組は 中央値と同じ", float(len(adj_pairs(decks[-1]))), float(m["riffle7" if nm == "riffle" else "hindu7"]["adj"]["median"]), 0.0))
        checks.append((f"見本（{nm}）: 同じマークの組は 中央値と同じ", float(sm.suit(decks[-1])), float(m["riffle7" if nm == "riffle" else "hindu7"]["suit"]["median"]), 0.0))
        checks.append((f"見本（{nm}）: 乱数の順で最初に条件に合う回（それより前に同じ値の回なし）",
                       float(not any((a[nm]["adj"][j], a[nm]["suit"][j]) == (sp["adj"], sp["suit"]) for j in range(i))), 1.0, 0.0))
        checks.append((f"見本（{nm}）: 8つの並びはどれも52枚（切る前＋7回）", float(len(decks) == 8 and all(sorted(d) == list(range(52)) for d in decks)), 1.0, 0.0))
        checks.append((f"見本（{nm}）: 切る前は マークごと・数字順", float(decks[0] == list(range(52))), 1.0, 0.0))
        d2, p2 = sm.redo_trial(nm, sp["state"])                    # 頭の乱数の状態から 別に数え直す
        checks.append((f"見本（{nm}）: 同じ乱数で数え直しても 7回ぶんの並びが全部同じ", float(d2 == decks), 1.0, 0.0))
        checks.append((f"見本（{nm}）: 数え直した p が同じ", float(p2), float(sp["p"]), 1e-12))
        checks.append((f"見本（{nm}）: 切るたびに並びが変わる", float(all(decks[k_] != decks[k_ + 1] for k_ in range(7))), 1.0, 0.0))
    # 画面に出す数字 = 並びから数え直した数
    for nm, key_a, key_s in (("hindu", "hi_a", "hi_s"), ("riffle", "rf_a", "rf_s")):
        sp = r["sample"][nm]
        checks.append((f"画面: 見本の最後の隣の組（{nm}）= 帯の ● の数", float(len(adj_pairs(sp["decks"][7]))), float(sp["adj"]), 0.0))
    # (4) ひねり（ヒンズーを増やすと）。画面は「元の隣のまま残った組」だけ。同じマークの組は説明欄の数字
    tv = twist_vals()
    cn = r["cnt"]
    checks.append(("ひねりの回数は 7・10・20・30", float(tuple(v[0] for v in tv) == (7, 10, 20, 30)), 1.0, 0.0))
    checks.append(("ヒンズー7回（数え直し）の隣の組 ≈ 本番（±1）", abs(tv[0][1] - S["hi_a"]), 0.0, 1.0))
    checks.append(("ヒンズー7回（数え直し）の同じマークの組 ≈ 本番（±1）", abs(cn[7]["suit"]["median"] - S["hi_s"]), 0.0, 1.0))
    checks.append(("回数を増やすほど 隣の組は減る（7 > 10 > 20 > 30）", float(tv[0][1] > tv[1][1] > tv[2][1] > tv[3][1]), 1.0, 0.0))
    checks.append(("画面の数字は 1万回ずつ数えた値（回数別に1万回）", float(all(cn[t_]["n"] == N_TRIAL for t_ in TW_TIMES)), 1.0, 0.0))
    checks.append(("追いつく回数が 数えた値から決まる（隣の組が混ぜた時の中央値以下になる最初の回数）", float(catch_up_n() is not None), 1.0, 0.0))
    nn = catch_up_n()
    checks.append(("画面の文の回数 = 数えた値（追いつく回数）", float(str(nn) + "回ほど" in tw_a()), 1.0, 0.0))
    checks.append(("追いつく回数より前の回数では まだ届かない", float(all(v[1] > S["rn_a"] for v in tv if v[0] < nn)), 1.0, 0.0))
    checks.append(("画面の文に 100回 を出さない", float("100" not in tw_a() + TW_B + TW_C + TW_Q), 1.0, 0.0))
    checks.append(("画面に「同じマーク」の数字を出さない（札・ひねり）", float("同じマーク" not in READ_NOTE + tw_a() + TW_B + TW_C + TW_Q), 1.0, 0.0))
    checks.append(("説明欄用: ヒンズー100回の同じマークの組 = 混ぜた時の中央値（±0.5）", abs(cn[100]["suit"]["median"] - S["rn_s"]), 0.0, 0.5))
    checks.append(("説明欄用: ヒンズー100回の隣の組 = 混ぜた時の中央値（±0.5）", abs(cn[100]["adj"]["median"] - S["rn_a"]), 0.0, 0.5))
    checks.append(("リフル7回の同じマークの組 = 混ぜた時（説明欄）", float(S["rf_s"] == S["rn_s"]), 1.0, 0.0))
    checks.append(("リフル7回の隣の組 = 混ぜた時（画面）", float(S["rf_a"] == S["rn_a"]), 1.0, 0.0))
    checks.append(("グラフの目盛りに 全部入る（隣の組の最大 < 28）", float(max(a[k]["adj"].max() for k in a) < NB), 1.0, 0.0))
    checks.append(("グラフの縦軸 30% を超える棒がない（混ぜた時・リフル・ヒンズー）",
                   float(all(np.bincount(a[k]["adj"], minlength=NB).max() / n <= SCALE for k in a)), 1.0, 0.0))
    checks.append(("ひねりの棒グラフ: 最大の棒が 縦軸の上端以内", float(max(v[1] for v in tv) <= TW_MAX), 1.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (6) 場面の長さ・動き
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("1回切る動きは 0.7秒以上（途中で切らない）", float(M_DUR >= 0.7), 1.0, 0.0))
    checks.append(("切る前の並びが見える時間 2秒以上（4色がきれいに分かれている）", float(T_SH0 - T_S0 - 0.5 >= 1.8), 1.0, 0.0))
    checks.append(("結果が見える時間: 見本の7回目のあと 次の場面まで 2.7秒以上", float(T_H0 - T_ME >= 2.7), 1.0, 0.0))
    cov = min(1 - (1 - a0) * (1 - a1) for j in range(52) for u_ in np.linspace(0, 0.999, 200) for (_d0, a0, _d1, a1) in [swap_parts(j, u_)])
    checks.append(("切っている間も 52本ぶんの幅が埋まる（どの場所も 古い帯か新しい帯が 70%以上の濃さ）", float(cov >= 0.70), 1.0, 0.0))
    checks.append(("切る前と切ったあとは 52本ぶんが全部ならぶ", float(len(S_decks_check()) == 8), 1.0, 0.0))
    checks.append(("数字が見える時間: グラフの数字 3秒以上", float(T_REV - T_HN >= 3.0), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (7) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


def S_decks_check():
    return results()["sample"]["hindu"]["decks"]


def lint():
    """mp4 は書かずに、全コマの文字を記録して 公開前チェックと同じ点検をする"""
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
    S = summary()
    print(f"長さ {DURATION:.1f}秒  帯 {T_S0:.1f}〜  切る {T_SH0:.1f}〜{T_ME:.1f}  グラフ {T_H0:.1f}-{T_H1:.1f}  数字 {T_HN:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}/{T_TW3:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  問い3行の文字 {min(big3_size(820.0), 92.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(820.0), 92.0)) for l in BIG_Q3):.0f}px")
    print("  読み方:", READ_NOTE, " ひねりの4本:", [(v[0], v[1]) for v in twist_vals()], " 追いつく回数:", catch_up_n())
    print("  ひねり:", TW_Q, "|", tw_a(), "|", TW_B, "|", TW_C)
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_GO + 0.8, T_GO + 2.0, T_S0 + 0.3, T_S0 + 1.5, T_M[0] + 0.4, T_M[1] + 0.4, T_M[2] + 0.4,
              T_M[6] + 0.9, T_ME + 1.5, T_H0 + 1.5, T_H1 - 0.2, T_HN + 1.2, T_REV + 0.9, T_ANS2 + 0.6, T_TW + 0.8, T_TW + 2.4,
              T_TW2 + 0.8, T_TW3 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
