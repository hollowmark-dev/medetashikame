"""テストで迷った答え、最初のまま？書き換える？ 1万回のテストで比べる。— 2026-11-08 作成（公開予定 11.21・ナレーションなし・45〜55秒）

計算の本体は sims/minaoshi_model.py（割合・平均2.1問・seed 91・答えの決め方は、1万回を回す前にそのファイルの docstring に固定してある。ここでは変えない）。
この sim は「1万回の結果を読んで絵にする」ところ。

【元にした研究】 Kruger, Wirtz & Miller (2005) J. Pers. Soc. Psychol. 88(5), 725-735。大学のテストで、書き換えた答え3,291件（学生1,561人）。
  書き換えた答えは 誤→正 51%・正→誤 25%・誤→誤 23%（合計99%は端数。計算では100%に割り戻す）。迷う問題は 1回のテストで平均2.1問（3,291÷1,561）。
【置き方】（minaoshi_model.py の docstring と同じ。結果を見て変えていない）
  ・迷う問題の数は毎回くじ（ポアソン分布・平均2.1問）。迷った問題ごとに、書き換えるとどうなるかをくじで決める。
  ・変えるのは「書き換えるかどうか」だけ。迷う問題の数・中身は同じ（同じ乱数）。1回 = 1人が1回のテストを受けること。1万回。
【答えの決め方】（answer_by_rule。計算の前に固定）
  点の差（書き換えた点 − 最初のままの点）の平均がプラスなら「書き換える」、マイナスなら「最初のまま」。±0.1点以内なら「ほぼ同じ」。
【見本の1回】 1万回の中の最初の1回そのもの（minaoshi_model.run の seed 91 の1回目）。
  同じ乱数で数え直し（このファイルの sample_cats）、迷った問題ごとの行き先を取り出す。run_checks で model と一致を確かめる。
【ひねり】 学生の予想（誤→正33%・正→誤42%）と実際（誤→正51%・正→誤25%）を比べる。
  予想の数字は Kruger ほか(2005) を紹介した解説スライドの数字（EXPECT_WR / EXPECT_RW）:
  https://www.sambuz.com/doc/a-review-of-counterfactual-thinking-and-the-first-ppt-presentation-469977
  「10回に4回」は 1万回のうち、書き換えて損した問題が1問以上あったテストの割合（41%）。
【言い方】 「中央値」は出さない。画面に「計算での見立て」は出さない（研究の割合で決まるため）。代わりに出典の札を出す。

問い: 「テストで迷った答え。/ 最初のまま？/ 書き換える？」
選択肢: A 最初のまま ／ B ほぼ同じ ／ C 書き換える（正解の記号は C。run_checks で確かめる）
見せ方: 冒頭（問い・2人が机で消しゴム）→ 研究の札3つ（出典つき）→ 比べる条件（書き換えるかどうかだけ）→ 見本の1回 → 1万回の点の差 → 答え → 理由 → ひねり（予想と実際／10回に4回）→ 締め
締め: 「あなたは、最初の直感を信じるほうですか？」
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import minaoshi_model as mm  # noqa: E402

SLUG = "minaoshi-kakikae"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIAL = mm.R
CNT = 2.0                                          # 1万回の数え上げの秒数
STUDY_N = 3291                                      # 研究で調べた書き換えの件数
PCT = (51, 25, 23)                                  # 誤→正・正→誤・誤→誤（研究）
EXPECT_WR, EXPECT_RW = 33, 42                       # 学生の予想（Kruger ほか2005 を紹介した解説スライドの数字。上の URL）
SRC1 = "出典: Kruger, Wirtz & Miller (2005)"
SRC2 = "J. Pers. Soc. Psychol. 88(5), 725–735"
DIFFS = list(range(-4, 7))                          # 点の差の棒（−4〜+6）


def answer_by_rule(mean):
    """答えの決め方（計算の前に固定）。点の差の平均が ±0.1点以内なら ほぼ同じ"""
    if abs(mean) <= 0.1 + 1e-9:
        return "ほぼ同じ"
    return "書き換える" if mean > 0 else "最初のまま"


def pct0(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


_RES = {}


def _model_hash():
    return hashlib.md5(Path(mm.__file__).read_bytes()).hexdigest()[:10]


def sample_cats():
    """1万回の最初の1回で、迷った問題ごとの行き先（0 誤→正・1 正→誤・2 誤→誤）。minaoshi_model.run と同じ順で乱数を使う"""
    rng = np.random.default_rng(91)
    k = rng.poisson(mm.MEAN_K, mm.R)
    c = rng.choice(3, size=int(k[0]), p=mm.P)
    return [int(v) for v in c]


def results():
    """1万回の結果。out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["r"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"minaoshi_{_model_hash()}.json"
    if f.exists():
        z = json.loads(f.read_text(encoding="utf-8"))
        k, diff, wr, rw = (np.array(z[n], np.int32) for n in ("k", "diff", "wr", "rw"))
    else:
        k, diff, wr, rw = mm.run()
        f.write_text(json.dumps(dict(k=k.tolist(), diff=diff.tolist(), wr=wr.tolist(), rw=rw.tolist())), encoding="utf-8")
    s = mm.summ(k, diff, wr, rw)
    onehot = np.stack([(diff == v) for v in DIFFS]).astype(np.int32)
    cum = np.cumsum(onehot, axis=1)                                   # 各棒の、n回目までの回数
    flag = rw > 0                                                     # 書き換えて損した問題が1問以上あった回
    win10 = next(i for i in range(0, N_TRIAL - 9) if int(flag[i:i + 10].sum()) == 4)   # 見せる10回（4回が該当する並び）
    mean = float(diff.mean())
    _RES["r"] = dict(k=k, diff=diff, wr=wr, rw=rw, s=s, cum=cum, flag=flag, win10=win10, mean=mean, key=answer_by_rule(mean),
                     gain=int((diff > 0).sum()), loss=int((diff < 0).sum()), same=int((diff == 0).sum()),
                     dist={v: int((diff == v).sum()) for v in DIFFS}, cats=sample_cats())
    return _RES["r"]


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    print(f"{N_TRIAL}回  点の差の平均 {r['mean']:+.3f}  答え: {r['key']}  上がった {r['gain']:,}回 下がった {r['loss']:,}回 同じ {r['same']:,}回")
    print("  分布:", " ".join(f"{v:+d}:{c:,}" for v, c in r["dist"].items()))
    print(f"  書き換えて損した問題が1問以上あった回: {r['s']['had_rw']:.1%}   迷う問題が0問の回: {r['s']['no_doubt']:.1%}")
    print(f"  見本: 1回目  迷った問題 {len(r['cats'])}問  行き先 {[('誤→正', '正→誤', '誤→誤')[c] for c in r['cats']]}  差 {int(r['diff'][0]):+d}")
    print(f"  10回の並び: {r['win10']}回目から  損した問題がある回 {[int(v) for v in r['flag'][r['win10']:r['win10'] + 10]]}")
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
note.DATE = "11.21"                                  # 日付欄（公開予定日）

ORG, ORG_D = "#e0801f", "#a85a0a"                    # 最初のまま（橙）
BLU, BLU_D = "#3f7fb5", "#2a5a85"                    # 書き換える（青）
GRY, GRY_D = "#a9a395", "#6f695b"                    # 変わらない（灰）
DESK_T, DESK_F, DESK_E = "#c99d68", "#a97c4a", "#8e6636"
CAT_COL = (BLU, ORG, GRY)                            # 誤→正・正→誤・誤→誤

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は C（3番目）
LABELS = ["最初のまま", "ほぼ同じ", "書き換える"]
KEY_LABEL = {"最初のまま": "最初のまま", "ほぼ同じ": "ほぼ同じ", "書き換える": "書き換える"}
CORRECT = 2

BIG_Q3 = ["テストで迷った答え。", "最初のまま？", "書き換える？"]      # 1コマ目の3行（同じ大きさ）
BIG_Q = ["テストで迷った答え。", "最初のまま？書き換える？"]            # 定位置（上）の2行
DETAIL_RULE = "違うのは、書き換えるかどうかだけ"
DETAIL = "同じ答案・同じ迷い（同じ乱数）"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (1.8, 2.6, 3.4)                              # 3・2・1
T_MOVE, T_GO = 4.3, 4.7
CY_INTRO, CY_FINAL = 910.0, 610.0                   # 教室（机の絵）の上端 y
PX = (290.0, 730.0)                                 # 左（最初のまま）・右（書き換える）の人の中心 x
MID = 510.0                                         # 机の中央 x
FYR, K_ST = 440.0, 4.4                              # 足もと y（cy から）・大きさ（身長 100×K_ST px）
SX = 570.0                                          # 付箋の中心 x（文字が x≤930 に収まる幅 720 まで）
LET = "アイウエ"


def setup():
    global T_R1, T_R2, T_R3, T_SET, T_S0, T_H0, T_HC, T_REV, T_RS, T_TW, T_TW2, T_Q, DURATION, SCENES, RT
    T_R1 = T_GO                                     # 研究1 大学のテストで3,291件
    T_R2 = T_R1 + 3.6                               # 研究2 割合
    T_R3 = T_R2 + 4.2                               # 研究3 平均2.1問
    T_SET = T_R3 + 4.2                              # 比べる条件
    T_S0 = T_SET + 4.0                              # 見本
    T_H0 = T_S0 + 8.0                               # 1万回
    T_HC = T_H0 + 0.5                               # 数え上げ始め
    T_REV = T_H0 + 3.5                              # 答え
    T_RS = T_REV + 4.6                              # 理由
    T_TW = T_RS + 5.0                               # ひねり1（予想と実際）
    T_TW2 = T_TW + 4.6                              # ひねり2（10回に4回）
    T_Q = T_TW2 + 5.2                               # 締め
    DURATION = T_Q + 3.6
    RT = [(T_R1, T_R2), (T_R2, T_R3), (T_R3, T_SET)]
    SCENES = [("冒頭（問い・2人が机で消しゴム）", 0.0, T_GO), ("研究1 3,291件", T_R1, T_R2), ("研究2 割合", T_R2, T_R3),
              ("研究3 平均2.1問", T_R3, T_SET), ("比べる条件", T_SET, T_S0), ("見本の1回", T_S0, T_H0),
              ("1万回の点の差", T_H0, T_REV), ("答え", T_REV, T_RS), ("理由", T_RS, T_TW), ("ひねり1 予想と実際", T_TW, T_TW2),
              ("ひねり2 10回に4回", T_TW2, T_Q), ("締め", T_Q, DURATION)]


setup()

# 見本の1回: 時間割（見本の秒 u = t − T_S0）
U_ERASE0, U_ERASE_STEP = 1.6, 0.7                   # 右の人が消しゴムで書き換える（問ごと）
U_MARK0, U_MARK_STEP = 4.3, 0.22                    # 答え合わせの○×
U_SCORE = 5.3                                       # 正解の数
U_STK_A = (0.3, 3.9)                                # 付箋A「たとえば、この1回では…」
U_STK_B = (4.2, 7.8)                                # 付箋B「書き換えると、…」

STK_A = "たとえば、この1回では\n迷った問題は3問あった。"
STK_B = "書き換えると、2問が正解に変わった。\n1問は、不正解に変わった。\n差し引きで、1点の得。"
STK_TW1 = "学生の予想は、誤→正33%・正→誤42%。\n実際は、誤→正51%・正→誤25%。"
STK_TW2A = "それでも、10回に4回のテストで、\n書き換えて損した問題が1問はある。"
STK_TW2B = "損した1問は悔しいので、\nよく覚えている。"
STK_RS1 = "迷ったとき、最初の答えは\nまちがっていることが多い。"
STK_RS2 = "書き換えた答えの2つに1つは、\n正解に変わる。"


def cards():
    """札: (1行の文, 出る秒, 消える秒)。1行ごとに「1文字0.12秒＋1秒以上」と 公開前チェックの「0.5秒＋文字数÷6秒」の両方より長く映す"""
    out = []

    def add(s, ta, tb):
        for ln in s.split("\n"):
            out.append((ln, ta, tb))

    add("大学のテストで、書き換えた答え\n3,291件を調べた研究", T_R1 + 0.25, T_R2 - 0.25)
    add("書き換えた答えは", T_R2 + 0.25, T_R3 - 0.25)
    add("迷う問題は、1回のテストで平均2.1問", T_R3 + 0.25, T_SET - 0.25)
    add("違うのは、書き換えるかどうかだけ。\n答案も、迷う問題も同じ。", T_SET + 0.3, T_S0 - 0.25)
    add(STK_A, T_S0 + U_STK_A[0], T_S0 + U_STK_A[1])
    add(STK_B, T_S0 + U_STK_B[0], T_S0 + U_STK_B[1])
    add("正解は『書き換える』。", T_REV + 0.2, T_RS - 0.1)
    add("書き換えて点が上がった回は4,916回、\n下がった回は1,778回。", T_REV + 0.6, T_RS - 0.1)
    add(STK_RS1, T_RS + 0.3, T_TW - 0.25)
    add(STK_RS2, T_RS + 1.6, T_TW - 0.25)
    add(STK_TW1, T_TW + 0.3, T_TW2 - 0.2)
    add(STK_TW2A, T_TW2 + 0.3, T_Q - 0.2)
    add(STK_TW2B, T_TW2 + 1.8, T_Q - 0.2)
    add("あなたは、最初の直感を\n信じるほうですか？", T_Q + 0.3, DURATION - 0.2)
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


def eraser(ctx, x, y, rot=0.0, a=1.0, s=1.0):
    """消しゴム（白い本体と青い紙のさや）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.25 * a)
    rrect(ctx, -34 + 4, -16 + 6, 68, 32, 6)
    ctx.fill()
    rrect(ctx, -34, -16, 68, 32, 6)
    ctx.set_source_rgba(*hexrgb("#f7f3ea", a))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.9 * a)
    rrect(ctx, -34, -16, 38, 32, 6)
    ctx.set_source_rgba(*hexrgb(BLU, a))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.9 * a)
    ctx.restore()


def pencil_icon(ctx, x, y, rot=0.0, a=1.0, s=1.0):
    """えんぴつ（右がとがった先）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    rrect(ctx, -62, -9, 100, 18, 3)
    ctx.set_source_rgba(*hexrgb("#f2c94c", a))
    ctx.fill_preserve()
    _stroke(ctx, 2.8, INK, 0.9 * a)
    rrect(ctx, -76, -9, 16, 18, 3)
    ctx.set_source_rgba(*hexrgb("#e88f9a", a))
    ctx.fill_preserve()
    _stroke(ctx, 2.8, INK, 0.9 * a)
    ctx.move_to(38, -9)
    ctx.line_to(66, 0)
    ctx.line_to(38, 9)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#f1d9b0", a))
    ctx.fill_preserve()
    _stroke(ctx, 2.8, INK, 0.9 * a)
    ctx.move_to(58, -3)
    ctx.line_to(66, 0)
    ctx.line_to(58, 3)
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.fill()
    ctx.restore()


def mini_sheet(ctx, cx, cy, w, h, a=1.0, flag=False, qmark=False):
    """小さな答案用紙（3行）。flag = 書き換えて損した問題がある回（赤い×）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.2 * a)
    rrect(ctx, -w / 2 + 4, -h / 2 + 6, w, h, 5)
    ctx.fill()
    rrect(ctx, -w / 2, -h / 2, w, h, 5)
    ctx.set_source_rgba(1, 1, 1, 0.96 * a)
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.85 * a)
    for r in range(3):
        yy = -h / 2 + h * (0.28 + 0.26 * r)
        ctx.move_to(-w / 2 + w * 0.14, yy)
        ctx.line_to(w / 2 - w * (0.34 if r != 1 else 0.5), yy)
        _stroke(ctx, max(2.0, w * 0.035), PENCIL, 0.55 * a)
    if flag:
        bx, by = w / 2 - w * 0.22, -h / 2 + h * 0.54
        ctx.move_to(bx - w * 0.11, by - w * 0.11)
        ctx.line_to(bx + w * 0.11, by + w * 0.11)
        ctx.move_to(bx + w * 0.11, by - w * 0.11)
        ctx.line_to(bx - w * 0.11, by + w * 0.11)
        _stroke(ctx, max(4.0, w * 0.07), RED, 0.95 * a)
    ctx.restore()


# ---------- 絵: 教室（2人と机） ----------
def cy_of(t):
    return lerp(CY_INTRO, CY_FINAL, INTRO.moved(t))


def desk_props(ctx, cy, t):
    """机の上の答案と、迷っている手もとの道具（左: えんぴつ、右: 消しゴムでこする）"""
    py = cy + 338
    for i in range(2):
        ctx.save()
        ctx.translate(PX[i], py)
        ctx.rotate(0.03 if i == 0 else -0.03)
        ctx.set_source_rgba(0.15, 0.1, 0.05, 0.2)
        rrect(ctx, -120 + 5, -46 + 7, 240, 92, 6)
        ctx.fill()
        rrect(ctx, -120, -46, 240, 92, 6)
        ctx.set_source_rgba(1, 1, 1, 0.97)
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        for r, ln in zip((-24, 0, 24), (130, 100, 150)):
            ctx.move_to(-98, r)
            ctx.line_to(-98 + ln, r)
            _stroke(ctx, 4, PENCIL, 0.5)
        text(ctx, "？", 82, 2, 52, RED, alpha=0.95)
        ctx.restore()
    pa = 0.5 + 0.5 * math.sin(t * 6.0)
    pencil_icon(ctx, PX[0] + 36 + 14 * math.sin(t * 4.0), py - 8 + 5 * math.sin(t * 8.0), -0.55, 1.0, 1.0)
    ex = PX[1] - 40 + 52 * math.sin(t * 5.2)
    eraser(ctx, ex, py + 10 + 4 * pa, -0.25 + 0.15 * math.sin(t * 5.2), 1.0, 1.15)


def draw_room_gfx(ctx, cy, t):
    wp = ease(clamp01(t / 0.8))                                     # 壁が左から右へ塗られていく（冒頭の動き）
    ctx.save()
    ctx.rectangle(60, cy - 35, 960 * wp, 580)
    ctx.clip()
    rrect(ctx, 60, cy - 35, 960, 580, 24)
    ctx.set_source_rgba(*hexrgb("#cfe3d5"))
    ctx.fill_preserve()
    _stroke(ctx, 3, PENCIL, 0.6)
    ctx.restore()
    for ci, x in enumerate(PX):
        student(ctx, x, cy + FYR, K_ST, ci, t, 1 if ci == 0 else -1, 0.0)
    top = cy + 262
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22)
    rrect(ctx, 76, top + 10, 880, 192, 16)
    ctx.fill()
    rrect(ctx, 70, top, 880, 160, 16)
    ctx.set_source_rgba(*hexrgb(DESK_T))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    for i in range(6):                                              # 木目
        yy = top + 24 + i * 26
        ctx.move_to(96, yy)
        ctx.curve_to(300, yy - 6, 600, yy + 7, 924, yy - 2)
        _stroke(ctx, 2.0, DESK_E, 0.22)
    rrect(ctx, 70, top + 146, 880, 44, 12)
    ctx.set_source_rgba(*hexrgb(DESK_F))
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9)
    desk_props(ctx, cy, t)


def draw_placards(ctx, cy, a=1.0):
    for s, (lab, col, dcol, lt) in enumerate((("最初のまま", ORG, ORG_D, "#fbe7cf"), ("書き換える", BLU, BLU_D, "#d9e8f5"))):
        x, y = PX[s], cy + 500
        rrect(ctx, x - 160, y - 35, 320, 70, 16)
        ctx.set_source_rgba(*hexrgb(lt, 0.97 * a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.set_line_width(5)
        ctx.stroke()
        text(ctx, lab, x, y, 44, dcol, alpha=a)


# ---------- 見本の1回: 答案用紙 ----------
SH_W, SH_H = 430.0, 345.0
SH_CX = (285.0, 735.0)
SH_Y0 = 890.0
SH_R0, SH_RS = 120.0, 94.0


def sample_rows():
    """迷った問題ごとの（正解の字, 最初の答え, 書き換えた答え）。行き先 0 誤→正・1 正→誤・2 誤→誤"""
    out = []
    for j, c in enumerate(results()["cats"]):
        tj = (1, 2, 0, 3)[j % 4]
        if c == 0:
            f, n = (tj + 1) % 4, tj
        elif c == 1:
            f, n = tj, (tj + 2) % 4
        else:
            f, n = (tj + 1) % 4, (tj + 2) % 4
        out.append((tj, f, n))
    return out


def sheet_scores():
    rows = sample_rows()
    return sum(1 for tj, f, n in rows if f == tj), sum(1 for tj, f, n in rows if n == tj)


def erase_t(j):
    return U_ERASE0 + U_ERASE_STEP * j


def mark_t(j):
    return U_MARK0 + U_MARK_STEP * j


def draw_mark(ctx, x, y, ok, p):
    if p <= 0:
        return
    sc = 1 + 0.5 * (1 - ease_out(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    if ok:
        note.pen_circle(ctx, 0, 0, 40, 40, RED, seed=3, width=10, progress=min(1.0, p * 1.5))
    else:
        ctx.move_to(-32, -32)
        ctx.line_to(32, 32)
        ctx.move_to(32, -32)
        ctx.line_to(-32, 32)
        _stroke(ctx, 10, INK, 0.9)
    ctx.restore()


def draw_sheets(ctx, cy, u, a):
    """見本: 左（最初のまま）と右（書き換える）の答案用紙。迷った問題だけ 3行。u = 見本の秒。机の上いっぱいに大きく置く"""
    rows = sample_rows()
    sc = sheet_scores()
    y0 = SH_Y0 - 24 * (1 - ease_out(clamp01(u / 0.5)))
    for side in range(2):
        x0 = SH_CX[side] - SH_W / 2
        col, dcol = (ORG, ORG_D) if side == 0 else (BLU, BLU_D)
        ctx.save()
        ctx.translate(x0, y0)
        ctx.rotate(0.006 if side == 0 else -0.006)
        ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22 * a)
        rrect(ctx, 6, 9, SH_W, SH_H, 12)
        ctx.fill()
        rrect(ctx, 0, 0, SH_W, SH_H, 12)
        ctx.set_source_rgba(1, 1, 1, 0.98 * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.set_line_width(8)
        ctx.stroke()
        text(ctx, ("最初のまま", "書き換える")[side], 20, 40, 36, dcol, align="left", alpha=a)
        if u >= U_SCORE:
            p = ease_out((u - U_SCORE) / 0.3)
            text(ctx, f"正解 {sc[side]}問", SH_W - 18, 40, max(42.0, 44 + 6 * (1 - p)), dcol, align="right", alpha=a * p)
        ctx.move_to(14, 76)
        ctx.line_to(SH_W - 14, 76)
        _stroke(ctx, 3, PENCIL, 0.5 * a)
        for j, (tj, f, n) in enumerate(rows):
            ry = SH_R0 + SH_RS * j
            text(ctx, f"問{j + 1}", 20, ry, 40, INK, align="left", alpha=a)
            if side == 0:
                text(ctx, LET[f], 200, ry, 80, INK, alpha=a)
                ok = f == tj
            else:
                e0 = erase_t(j)
                old_a = 1 - clamp01((u - e0) / 0.35)
                new_a = clamp01((u - e0 - 0.35) / 0.3)
                if old_a > 0:
                    text(ctx, LET[f], 200, ry, 80, INK, alpha=a * old_a)
                if new_a > 0:
                    text(ctx, LET[n], 200, ry, 80 + 10 * (1 - new_a), BLU_D, alpha=a * new_a)
                ok = n == tj
            mu = (u - mark_t(j)) / 0.25
            draw_mark(ctx, SH_W - 70, ry, ok, mu)
        if side == 1:                                                   # 消しゴムがこする
            for j in range(len(rows)):
                e0 = erase_t(j)
                if e0 <= u <= e0 + 0.5:
                    f_ = (u - e0) / 0.5
                    ex = 200 + 44 * math.sin(f_ * 14.0)
                    eraser(ctx, ex, SH_R0 + SH_RS * j + 8, -0.3, a, 1.4)
        ctx.restore()
    if u >= U_SCORE + 0.5:                                              # 正解が多いほうに赤い丸
        p = ease_out((u - U_SCORE - 0.5) / 0.4)
        note.pen_circle(ctx, SH_CX[1] + SH_W / 2 - 112, y0 + 40, 112, 38, RED, seed=71, width=7, progress=p, alpha=a)


def draw_room_scene(ctx, t):
    if t < T_SET - 0.01:
        a = 1 - ease(clamp01((t - T_GO) / 0.3)) if t >= T_GO else 1.0
    else:
        a = ease(clamp01((t - T_SET) / 0.3)) * (1 - ease(clamp01((t - T_H0) / 0.4)))
    if a <= 0:
        return
    cy = cy_of(t)
    ctx.push_group()
    # 人と机（冒頭だけ、場面が寄ったところから引く。文字は拡大しない）
    ctx.save()
    z = 1.0 + 0.14 * (1 - ease(clamp01(t / 1.1)))
    if z > 1.0:
        ctx.translate(540, cy + 400)
        ctx.scale(z, z)
        ctx.translate(-540, -(cy + 400))
    draw_room_gfx(ctx, cy, t)
    ctx.restore()
    draw_placards(ctx, cy, 1.0)
    if t >= T_S0 - 0.01:
        u = t - T_S0
        draw_sheets(ctx, cy, u, ease_out(clamp01(u / 0.4)))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    # 札
    if T_SET <= t < T_S0:
        sa = win(t, T_SET + 0.3, T_S0 - 0.25, 0.3, 0.25)
        stk(ctx, "違うのは、書き換えるかどうかだけ。\n答案も、迷う問題も同じ。", 1290, 50, a=sa)
    if T_S0 <= t < T_H0:
        u = t - T_S0
        stk(ctx, STK_A, 1352, 42, a=win(u, *U_STK_A, 0.3, 0.25))
        stk(ctx, STK_B, 1350, 36, a=win(u, *U_STK_B, 0.3, 0.25), fg=INK)


# ---------- 絵: 研究の札 ----------
def research_source(ctx, a):
    text(ctx, SRC1, SX, 1408, 26, PENCIL, bold=False, alpha=a)
    text(ctx, SRC2, SX, 1436, 26, PENCIL, bold=False, alpha=a)


def res1(ctx, t, a):
    u = t - T_R1
    stk(ctx, "大学のテストで、書き換えた答え\n3,291件を調べた研究", 700, 48, a=a * ease_out(clamp01((u - 0.2) / 0.3)))
    order = np.random.default_rng(7).permutation(45)
    rank = {int(v): i for i, v in enumerate(order)}
    cols = 9
    for idx in range(45):
        r_, c_ = divmod(idx, cols)
        tt = 0.5 + 1.5 * (rank[idx] / 45)
        p = ease_out(clamp01((u - tt) / 0.25))
        if p <= 0:
            continue
        x = 570 + (c_ - 4) * 88.0
        y = 860 + r_ * 112.0
        mini_sheet(ctx, x, y + 10 * (1 - p), 72, 92, a * p)
    if u >= 1.5:
        p = ease_out((u - 1.5) / 0.35)
        ctx.save()
        ctx.translate(SX, 1100)
        ctx.scale(0.85 + 0.15 * p, 0.85 + 0.15 * p)
        rrect(ctx, -380, -135, 760, 270, 36)
        ctx.set_source_rgba(1, 1, 1, 0.95 * p * a)
        ctx.fill_preserve()
        _stroke(ctx, 6, INK, 0.9 * p * a)
        text(ctx, "3,291", -70, 0, 190, BLU_D, alpha=p * a)
        text(ctx, "件", 290, 30, 100, INK, alpha=p * a)
        ctx.restore()


def res2(ctx, t, a):
    u = t - T_R2
    stk(ctx, "書き換えた答えは", 675, 50, a=a * ease_out(clamp01((u - 0.2) / 0.3)))
    base = 1230.0
    sc_ = 8.8
    caps = (("誤→正", "まちがいが\n正解に"), ("正→誤", "正解が\nまちがいに"), ("誤→誤", "まちがいの\nままだった"))
    for i, (cx, v) in enumerate(zip((210.0, 520.0, 830.0), PCT)):
        t0 = 0.5 + 0.6 * i
        f = ease_out(clamp01((u - t0) / 0.6))
        hgt = v * sc_ * f
        rrect(ctx, cx - 100, base - v * sc_, 200, v * sc_, 14)
        ctx.set_source_rgba(1, 1, 1, 0.5 * a)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.5 * a)
        if hgt > 1:
            rrect(ctx, cx - 100, base - hgt, 200, hgt, 14)
            ctx.set_source_rgba(*hexrgb(CAT_COL[i], 0.95 * a))
            ctx.fill_preserve()
            _stroke(ctx, 4, INK, 0.9 * a)
        if f > 0.4:
            text(ctx, f"{v}%", cx, base - hgt - 46, 92, (BLU_D, ORG_D, GRY_D)[i], alpha=a * min(1.0, (f - 0.4) * 2))
        text(ctx, caps[i][0], cx, base + 40, 56, INK, alpha=a)
        text(ctx, caps[i][1], cx, base + 118, 32, PENCIL, bold=False, alpha=a)


def res3(ctx, t, a):
    u = t - T_R3
    stk(ctx, "迷う問題は、1回のテストで平均2.1問", 700, 46, a=a * ease_out(clamp01((u - 0.2) / 0.3)))
    p = ease_out(clamp01((u - 0.5) / 0.4))
    text(ctx, "2.1", 410, 960, 330, BLU_D, alpha=a * p)
    text(ctx, "問", 800, 1000, 170, INK, alpha=a * p)
    for i in range(3):                                                 # 迷った問題 2問と、0.1問ぶん
        q = ease_out(clamp01((u - 1.0 - 0.3 * i) / 0.3))
        cx = 250 + i * 250
        ctx.save()
        if i == 2:
            ctx.rectangle(cx - 100, 1100, 100 + 0.1 * 200 + 6, 300)
            ctx.clip()
        mini_sheet(ctx, cx, 1250, 200, 240, a * q, False)
        text(ctx, "？", cx, 1252, 130, RED, alpha=a * q)
        ctx.restore()


def draw_research(ctx, t):
    fns = (res1, res2, res3)
    for k, (ta, tb) in enumerate(RT):
        a = clamp01((t - ta) / 0.25) * (1 - clamp01((t - tb) / 0.25))
        if a <= 0:
            continue
        ctx.push_group()
        fns[k](ctx, t, a)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    sa = win(t, T_R1 + 0.2, T_SET - 0.2, 0.3, 0.3)
    if sa > 0:
        research_source(ctx, sa)


# ---------- 絵: 1万回の点の差・答え ----------
def sign_str(v):
    return f"+{v}" if v > 0 else ("0" if v == 0 else f"−{abs(v)}")


H_X0, H_STEP, H_BW = 105.0, 76.0, 62.0
H_Y0, H_Y1 = 1290.0, 1105.0                      # 棒の下端: 結果を数えるあいだ / 答えの付箋が出るあと
H_S0, H_S1 = 0.16, 0.105                          # 1回あたりの棒の高さ（px）


def draw_hist_scene(ctx, t):
    a = clamp01((t - T_H0) / 0.4) * (1 - clamp01((t - T_RS) / 0.3))
    if a <= 0:
        return
    r = results()
    m = ease(clamp01((t - T_REV) / 0.6))              # 答えでグラフが縮み、下に付箋の場所ができる
    base = lerp(H_Y0, H_Y1, m)
    hsc = lerp(H_S0, H_S1, m)
    ctx.push_group()
    text(ctx, "1万回のテスト、点の差", SX, 645, 48, INK)
    text(ctx, "（書き換えた点 − 最初のままの点）", SX, 690, 30, PENCIL, bold=False)
    p = ease(clamp01((t - T_HC) / CNT))
    n = max(0, min(N_TRIAL, int(p * N_TRIAL)))
    text(ctx, f"{n:,}回目", 100, 745, 34, PENCIL, bold=False, align="left")
    for i, v in enumerate(DIFFS):
        cnt = int(r["cum"][i][n - 1]) if n > 0 else 0
        hgt = cnt * hsc
        x = H_X0 + i * H_STEP
        col = BLU if v > 0 else (ORG if v < 0 else GRY)
        dcol = BLU_D if v > 0 else (ORG_D if v < 0 else GRY_D)
        if hgt > 1:
            rrect(ctx, x, base - hgt, H_BW, hgt, 8)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, 0.9)
        if cnt > 0:
            text(ctx, f"{cnt:,}", x + H_BW / 2, base - hgt - 20, 30, dcol)
        text(ctx, sign_str(v), x + H_BW / 2, base + 36, 36, INK)
    ctx.move_to(H_X0 - 12, base)
    ctx.line_to(H_X0 + 11 * H_STEP, base)
    _stroke(ctx, 3, INK, 0.8)
    if p >= 1.0:
        text(ctx, "書き換えて下がった回", 235, base + 92, 32, ORG_D)
        text(ctx, "同じ", H_X0 + 4 * H_STEP + H_BW / 2, base + 92, 32, GRY_D)
        text(ctx, "書き換えて上がった回", 745, base + 92, 32, BLU_D)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.2) / 0.3) * (1 - ease((t - T_RS + 0.1) / 0.3))
        stk(ctx, f"正解は『{KEY_LABEL[r['key']]}』。", 1285, 50, fg=RED, a=b, tilt=-0.02)
        c = ease_out((t - T_REV - 0.6) / 0.3) * (1 - ease((t - T_RS + 0.1) / 0.3))
        stk(ctx, f"書き換えて点が上がった回は{r['gain']:,}回、\n下がった回は{r['loss']:,}回。", 1395, 38, a=c)


# ---------- 絵: 理由 ----------
def donut(ctx, cx, cy, rad, vals, cols, prog, labels, a=1.0):
    tot = float(sum(vals))
    a0 = -math.pi / 2
    for v, col, lab in zip(vals, cols, labels):
        sweep = 2 * math.pi * v / tot
        use = max(0.0, min(sweep, 2 * math.pi * prog - (a0 + math.pi / 2)))
        if use > 0.001:
            ctx.new_path()
            ctx.move_to(cx, cy)
            ctx.arc(cx, cy, rad, a0, a0 + use)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            ctx.fill_preserve()
            _stroke(ctx, 4, INK, 0.9 * a)
            if use >= sweep - 0.001:
                am = a0 + sweep / 2
                lx, ly = cx + math.cos(am) * rad * 0.62, cy + math.sin(am) * rad * 0.62
                text(ctx, lab, lx, ly, 54, "#ffffff", alpha=a)
        a0 += sweep


def draw_reasons(ctx, t):
    a = clamp01((t - T_RS) / 0.3) * (1 - clamp01((t - T_TW) / 0.3))
    if a <= 0:
        return
    u = t - T_RS
    ctx.push_group()
    text(ctx, "書き換えた答えの行き先", SX, 640, 42, INK)
    prog = ease(clamp01((u - 0.2) / 1.2))
    donut(ctx, SX, 905, 235, PCT, CAT_COL, prog, ("誤→正\n51%", "正→誤\n25%", "誤→誤\n23%"))
    if u >= 1.5:
        p = ease_out((u - 1.5) / 0.4)
        note.pen_circle(ctx, SX + 146, 905, 118, 88, RED, seed=33, width=7, progress=p)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    stk(ctx, STK_RS1, 1218, 40, a=win(t, T_RS + 0.3, T_TW - 0.25, 0.3, 0.25))
    stk(ctx, STK_RS2, 1372, 40, a=win(t, T_RS + 1.6, T_TW - 0.25, 0.3, 0.25))


# ---------- 絵: ひねり ----------
def draw_twist1(ctx, t):
    a = clamp01((t - T_TW) / 0.3) * (1 - clamp01((t - T_TW2) / 0.3))
    if a <= 0:
        return
    u = t - T_TW
    ctx.push_group()
    text(ctx, "学生の予想と、実際", SX, 645, 48, INK)
    sc_ = 10.0
    x0 = 210.0
    groups = (("誤→正", EXPECT_WR, PCT[0], BLU, BLU_D, 740), ("正→誤", EXPECT_RW, PCT[1], ORG, ORG_D, 1030))
    for gi, (lab, ex, ac, col, dcol, y0) in enumerate(groups):
        text(ctx, lab, 92, y0, 54, dcol, align="left")
        for k, (nm, v, yy) in enumerate((("予想", ex, y0 + 36), ("実際", ac, y0 + 148))):
            f = ease_out(clamp01((u - 0.4 - 0.9 * k - 0.2 * gi) / 0.5))
            hgt = 96
            wv = v * sc_ * f
            if wv > 1:
                rrect(ctx, x0, yy, wv, hgt, 12)
                if k == 0:
                    ctx.set_source_rgba(*hexrgb(col, 0.28 * a))
                    ctx.fill_preserve()
                    ctx.set_dash([14, 9])
                    _stroke(ctx, 4, dcol, 0.95)
                    ctx.set_dash([])
                else:
                    ctx.set_source_rgba(*hexrgb(col, 0.95))
                    ctx.fill_preserve()
                    _stroke(ctx, 4, INK, 0.9)
            text(ctx, nm, x0 - 12, yy + hgt / 2, 34, PENCIL, align="right", bold=False)
            if f > 0.5:
                text(ctx, f"{v}%", x0 + wv + 16, yy + hgt / 2, 66, dcol, align="left", alpha=min(1.0, (f - 0.5) * 2))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    stk(ctx, STK_TW1, 1355, 42, a=win(t, T_TW + 0.3, T_TW2 - 0.2, 0.3, 0.25), maxw=690.0)


def draw_twist2(ctx, t):
    a = clamp01((t - T_TW2) / 0.3) * (1 - clamp01((t - T_Q) / 0.35))
    if a <= 0:
        return
    r = results()
    u = t - T_TW2
    ctx.push_group()
    text(ctx, "10回のテストを受けると", SX, 645, 46, INK)
    w0 = r["win10"]
    for i in range(10):
        rr_, cc = divmod(i, 5)
        cx = 570 + (cc - 2) * 170.0
        cy = 810 + rr_ * 215.0
        p = ease_out(clamp01((u - 0.2 - 0.09 * i) / 0.25))
        fl = bool(r["flag"][w0 + i])
        fa = ease_out(clamp01((u - 1.2 - 0.1 * i) / 0.25)) if fl else 0.0
        mini_sheet(ctx, cx, cy + 10 * (1 - p), 150, 180, a * p, flag=False)
        if fl and fa > 0:
            mini_sheet(ctx, cx, cy, 150, 180, a * fa, flag=True)
    text(ctx, "赤い×＝書き換えて損した問題がある", SX, 1150, 34, RED, bold=False, alpha=ease_out(clamp01((u - 1.5) / 0.3)))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    stk(ctx, STK_TW2A, 1245, 40, a=win(t, T_TW2 + 0.3, T_Q - 0.2, 0.3, 0.25))
    stk(ctx, STK_TW2B, 1385, 40, a=win(t, T_TW2 + 1.8, T_Q - 0.2, 0.3, 0.25), color="pink")


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


# ---------- 締め ----------
def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    stk(ctx, "あなたは、最初の直感を\n信じるほうですか？", 800, 56, a=q, tilt=-0.02, cx=580)
    r_ = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 985, 40, INK, bold=False, alpha=r_)
    ctx.push_group()
    for i in range(3):
        x = 270 + i * 300
        bob = math.sin((t - T_Q) * 3.0 + i) * 8
        if i == 1:
            eraser(ctx, x, 1230 + bob, -0.2 + 0.1 * math.sin((t - T_Q) * 4.0), 1.0, 2.0)
        else:
            mini_sheet(ctx, x, 1230 + bob, 130, 150, 1.0, flag=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)


# ---------- 本体 ----------
def body(ctx, t):
    draw_room_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_research(ctx, t)
        draw_hist_scene(ctx, t)
        draw_reasons(ctx, t)
        draw_twist1(ctx, t)
        draw_twist2(ctx, t)
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
def scrub(mx, t0, vol=0.2):
    """消しゴムでこする音"""
    for i in range(5):
        mx.add(t0 + i * 0.07, blip(330 + 50 * (i % 2), 0.03), vol)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 164.8, 196.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(3):                                      # 冒頭: 消しゴムでこする
        scrub(mx, 0.1 + 1.4 * i, vol=0.22)
    mx.add(T_R1 + 1.5, thump(), 0.4)                        # 研究1: 3,291
    for i in range(3):                                      # 研究2: 棒
        mx.add(T_R2 + 0.5 + 0.6 * i, bell(659.3 + 90 * i, 0.6), 0.3)
    mx.add(T_R3 + 0.5, bell(784.0, 0.8), 0.35)
    for j in range(3):                                      # 見本: 書き換え・答え合わせ
        scrub(mx, T_S0 + erase_t(j), vol=0.22)
        mx.add(T_S0 + mark_t(j), blip(988.0, 0.1), 0.3)
    mx.add(T_S0 + U_SCORE, bell(1046.5, 0.9), 0.4)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                     # 1万回
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_RS + 0.5, bell(698.5, 0.8), 0.35)
    mx.add(T_RS + 1.7, bell(784.0, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 1.3, bell(659.3, 0.8), 0.4)
    mx.add(T_TW2, riser(0.5), 0.35)
    mx.add(T_TW2 + 1.2, thump(), 0.4)
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
    cats = r["cats"]
    checks = []
    # (1) 条件・数え直し
    k2, d2, wr2, rw2 = mm.run()                              # minaoshi_model.run をもう一度（同じ seed 91）
    checks.append(("回数 = 1万", float(len(r["diff"])), float(N_TRIAL), 0.0))
    checks.append(("数え直し: 点の差が minaoshi_model.run と全回一致", float(np.array_equal(r["diff"], d2)), 1.0, 0.0))
    checks.append(("分布の合計 = 1万", float(sum(r["dist"].values())), float(N_TRIAL), 0.0))
    alt = np.bincount(d2 + 4, minlength=11)                  # 別の数え方（bincount）
    checks.append(("分布: 別の数え方（bincount）と同じ", float([int(v) for v in alt] == [r["dist"][v] for v in DIFFS]), 1.0, 0.0))
    checks.append(("点の差 = 誤→正の数 − 正→誤の数（全回）", float(np.array_equal(r["diff"], r["wr"] - r["rw"])), 1.0, 0.0))
    checks.append(("点の差の範囲 −4〜+6（資料）", float((int(r["diff"].min()), int(r["diff"].max())) == (-4, 6)), 1.0, 0.0))
    checks.append(("点の差の平均 +0.56", r["mean"], 0.56, 0.005))
    checks.append(("研究の割合 51・25・23（model の P×99）", float(tuple(int(round(v * 99)) for v in mm.P) == PCT), 1.0, 0.0))
    checks.append(("研究: 3,291件 ÷ 1,561人 = 平均2.1問", float(f"{mm.MEAN_K:.1f}" == "2.1" and STUDY_N == 3291), 1.0, 0.0))
    checks.append(("画面: 迷う問題の数の平均がおよそ2.1問（1万回）", float(r["k"].mean()), 2.1, 0.06))
    # (2) 画面の数字
    checks.append(("画面: 上がった回 4,916", float(r["gain"]), 4916.0, 0.0))
    checks.append(("画面: 下がった回 1,778", float(r["loss"]), 1778.0, 0.0))
    checks.append(("画面: 上がった回の数 = 分布の合計（+1以上）", float(sum(r["dist"][v] for v in DIFFS if v > 0)), float(r["gain"]), 0.0))
    checks.append(("画面: 10回に4回（書き換えて損した問題が1問以上の回 41%）", float(int(round(r["s"]["had_rw"] * 10))), 4.0, 0.0))
    checks.append(("画面: 損した問題がある回 = rw>0 の数え直し", float((r["rw"] > 0).mean()), r["s"]["had_rw"], 0.0))
    checks.append(("画面: 見せる10回のうち 損した問題がある回 = 4", float(int(r["flag"][r["win10"]:r["win10"] + 10].sum())), 4.0, 0.0))
    checks.append(("ひねり: 予想 誤→正33%・正→誤42% / 実際 51%・25%", float((EXPECT_WR, EXPECT_RW, PCT[0], PCT[1]) == (33, 42, 51, 25)), 1.0, 0.0))
    checks.append(("ひねり: 実際は 誤→正が多く 正→誤が少ない（予想と逆）", float(PCT[0] > EXPECT_WR and PCT[1] < EXPECT_RW), 1.0, 0.0))
    # (3) 答え
    key = answer_by_rule(r["mean"])
    checks.append(("規則の答え = 書き換える", float(key == "書き換える"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号の並び: 最初のまま・ほぼ同じ・書き換える の順", float(LABELS == ["最初のまま", "ほぼ同じ", "書き換える"]), 1.0, 0.0))
    for m_, k_ in ((0.0, "ほぼ同じ"), (0.1, "ほぼ同じ"), (0.11, "書き換える"), (-0.11, "最初のまま")):
        checks.append((f"規則の道具: 平均 {m_:+.2f} → {k_}", float(answer_by_rule(m_) == k_), 1.0, 0.0))
    # (4) 見本は1万回の中の最初の1回そのもの
    sm = mm.summ(k2, d2, wr2, rw2)
    rng = np.random.default_rng(91)
    kk = rng.poisson(mm.MEAN_K, mm.R)
    cc = [int(v) for v in rng.choice(3, size=int(kk[0]), p=mm.P)]
    checks.append(("見本: 迷った問題の数 = 1万回の1回目", float(len(cats)), float(k2[0]), 0.0))
    checks.append(("見本: 数え直した行き先が一致（同じ乱数）", float(cats == cc), 1.0, 0.0))
    checks.append(("見本: 誤→正の数 = 2（model の sample.wr と1回目）", float(sum(1 for c in cats if c == 0)), float(wr2[0]), 0.0))
    checks.append(("見本: 正→誤の数 = 1（model の sample.rw と1回目）", float(sum(1 for c in cats if c == 1)), float(rw2[0]), 0.0))
    checks.append(("見本: 迷った問題は3問・2問が正解に・1問が不正解に・差し引き +1", float((len(cats), sum(1 for c in cats if c == 0), sum(1 for c in cats if c == 1), int(d2[0])) == (3, 2, 1, 1)), 1.0, 0.0))
    s0, s1 = sheet_scores()
    checks.append(("見本: 答案の○の数 最初のまま1問・書き換え2問", float((s0, s1) == (1, 2)), 1.0, 0.0))
    checks.append(("見本: 答案の○の数の差 = 点の差 +1", float(s1 - s0), float(d2[0]), 0.0))
    checks.append(("見本: 迷った問題は3問（札の文と一致）", float(len(sample_rows()) == 3 and "3問" in STK_A), 1.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q3) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(440 - s3 / 2 >= 370), 1.0, 0.0))
    # 出典の札
    checks.append(("出典の札: 文字24px以上・1行が x=930 以内（28px）", float(max(core.text_width(SRC1, 28), core.text_width(SRC2, 28)) / 2 + SX <= 930), 1.0, 0.0))
    checks.append(("出典の札: 研究の場面のあいだ 8秒以上映す", float((T_SET - 0.2) - (T_R1 + 0.2) - 0.3 >= 8.0), 1.0, 0.0))
    checks.append(("出典の札: 論文の名前と年・巻号ページが入っている",
                   float(all(w_ in SRC1 + SRC2 for w_ in ("Kruger, Wirtz & Miller", "2005", "88(5)", "725"))), 1.0, 0.0))
    # (6) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_)
        need = max(0.12 * n_ + 1.0, 0.5 + n_ / 6.0)
        checks.append((f"札「{s_}」が読み切れる（{tb - ta:.1f}秒 / 要る {need:.1f}秒）", float(tb - ta >= need), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("研究の札は1つずつ（場面が重ならない）", float(RT[0][1] <= RT[1][0] and RT[1][1] <= RT[2][0]), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万回の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("見本の付箋が 見本の場面に収まる", float(U_STK_B[1] <= (T_H0 - T_S0) and U_STK_A[1] <= U_STK_B[0] + 0.5), 1.0, 0.0))
    checks.append(("長さ 45〜59秒（目安45〜55秒）", float(45.0 <= DURATION < 59.0), 1.0, 0.0))
    # (7) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）  [model.summ 一致: {sm['gain'] == r['s']['gain']}]")


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
    print(f"長さ {DURATION:.1f}秒  研究 {T_R1:.1f}/{T_R2:.1f}/{T_R3:.1f}  比べる条件 {T_SET:.1f}  見本 {T_S0:.1f}-{T_H0:.1f}  1万回 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  点の差の平均 {r['mean']:+.3f}  答え: {r['key']}  上がった {r['gain']:,}回・下がった {r['loss']:,}回・同じ {r['same']:,}回  損した問題がある回 {r['s']['had_rw']:.0%}")
    print(f"  見本: 1回目  迷った{len(r['cats'])}問  行き先 {[('誤→正', '正→誤', '誤→誤')[c] for c in r['cats']]}  差 {int(r['diff'][0]):+d}  答案の○ {sheet_scores()}")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 3.0, 4.6,
          T_R1 + 2.2, T_R2 + 3.0, T_R3 + 2.4,
          T_SET + 2.0,
          T_S0 + 0.9, T_S0 + 3.0, T_S0 + 5.0, T_S0 + 7.0,
          T_HC + 1.0, T_REV - 0.3, T_REV + 3.2,
          T_RS + 4.0, T_TW + 3.4, T_TW2 + 4.2,
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
