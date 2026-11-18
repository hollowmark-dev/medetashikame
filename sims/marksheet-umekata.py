"""分からない20問、同じ番号で埋める？ばらばら？ マークシートの埋め方を1万回。— 2026-11-04 作成（公開予定 11.18・ナレーションなし・45秒前後）

計算の本体は sims/marksheet_model.py（置き方と答えの決め方は、1万回を回す前に そのファイルの docstring に固定してある。ここでは変えない）。
この sim は「1万回の結果を読んで絵にする」ところ。

【置き方】（marksheet_model.py の docstring と同じ。結果を見て変えていない）
  ・テストは40問・4択。正解の番号は 1〜4 が10問ずつ（作る人が番号をならす、という見立て。並びはでたらめ）。
  ・分からない問題は 40問からでたらめに20問（どの番号が正解かとは関係なく選ばれる）。そのほか20問は分かる。
  ・同じ番号: 分からない20問すべてに同じ番号（③）をマークする。 ばらばら: 1問ごとに 1〜4 をでたらめにマークする。
  ・1回ごとに 同じテスト・同じ分からない問題へ 両方の埋め方を当てる（変える条件は埋め方だけ）。1万回。
  ・点は「分からない20問のうち、あたった数」（1問1点。分かる20問は2人とも同じなので数えない）。
【答えの決め方】（answer_by_rule。計算の前に固定）
  1万回の平均点の差 d（同じ番号 − ばらばら）。 |d| < 0.25点 → ほぼ同じ / d >= 0.25 → 同じ番号 / d <= -0.25 → ばらばら
【あわせて出す数字】 平均・中央値・最低・最高、2点以下・8点以上になる回の割合（山の形）、「1問分かれば+0.75点」（4択で分からない1問の期待 0.25点 → 分かる1問 1点）。
【見本の1回】 1万回の中の1回そのもの。乱数の順で最初に「同じ番号が4〜6点、かつ、ばらばらが4〜6点でない」回
  （0番目は 6点と12点で極端なので使わず、1番目から数える。結果を見て選んでいない）。同じ乱数で取り出し直し、1万回の記録と一致するかを run_checks で照合する。
【言い方】 「分からない問題の埋め方」の話。点を取るコツ・どの番号が当たりやすいかの話はしない。
  「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。画面に「計算での見立て」を小さく1回。実在の試験の名前は出さない。

問い: 「分からない20問、/ 同じ番号で埋める？ / ばらばら？」
選択肢: A 同じ番号 ／ B ほぼ同じ ／ C ばらばら（正解の記号は B。run_checks で確かめる）
見せ方: 教室で同じ服の2人が同じテストを埋める → 見本の1回の答え合わせ → 1万回の点数の山 → 答え → ひねり（山の形）→ 短い札（+0.75点）→ 締め
締め: 「あなたなら、どちらで埋めますか？」
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import marksheet_model as mm  # noqa: E402

SLUG = "marksheet-umekata"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIAL = mm.N
N_Q, N_UNK = 40, 20
PICK = mm.run.__defaults__[3]                        # 「同じ番号」で塗る番号（0始まりの2 = ③）。run() の既定と同じ
KMAX = 14                                            # 点の山の横軸 0〜13


def pct1(x):
    return f"{math.floor(x * 1000 + 0.5) / 10:.1f}%"


def f2(x):
    return f"{math.floor(x * 100 + 0.5) / 100:.2f}"


def once_in(f):
    """割合 f → 約N回に1回（整数）"""
    return f"約{int(round(1.0 / f))}回に1回"


def pts(x):
    """点（整数なら小数なし）"""
    return f"{int(round(x))}点" if abs(x - round(x)) < 1e-9 else f"{x:g}点"


_RES = {}


def _model_hash():
    return hashlib.md5(Path(mm.__file__).read_bytes()).hexdigest()[:10]


def results():
    """1万回の点数（同じ番号・ばらばら）。marksheet_model.run を同じ乱数で回し、out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"trials_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        s, m = z["s"], z["m"]
    else:
        s, m = mm.run(np.random.default_rng(mm.SEED))
        np.savez_compressed(f, s=s, m=m)
    key, d = mm.answer_by_rule(s, m)
    hs = np.bincount(s, minlength=KMAX)
    hm = np.bincount(m, minlength=KMAX)
    cs = np.zeros((KMAX, len(s) + 1), np.int32)         # 最初の n 回までの度数（山が積み上がる絵用）
    cm = np.zeros((KMAX, len(s) + 1), np.int32)
    for k in range(KMAX):
        cs[k, 1:] = np.cumsum(s == k)
        cm[k, 1:] = np.cumsum(m == k)

    def st(x):
        return dict(mean=float(x.mean()), median=float(np.median(x)), mn=int(x.min()), mx=int(x.max()),
                    le2=float((x <= 2).mean()), ge8=float((x >= 8).mean()))
    _RES["m"] = dict(s=s, m=m, key=key, d=d, hs=hs, hm=hm, cs=cs, cm=cm, S=st(s), M=st(m))
    return _RES["m"]


_SAMPLE = {}


def samples():
    """見本の1回（1万回の中の1回そのもの）。表示用に 分からない20問を 問題番号の小さい順に並べる"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    i = mm.pick_sample(r["s"], r["m"])
    rp = mm.replay(i)
    order = np.argsort(rp["idx"])
    _SAMPLE.update(i=i, rp=rp, qno=rp["idx"][order] + 1, key=rp["k"][order], same=np.full(N_UNK, PICK),
                   mix=rp["marks"][order])
    return _SAMPLE


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    S = samples()
    s, m = r["s"], r["m"]
    if "--model" in sys.argv:
        jd = json.loads((OUT / "cache" / "model.json").read_text(encoding="utf-8"))
        main_ = jd[list(jd)[0]]
        print(f"乱数の種 {mm.SEED}  {N_TRIAL}回  40問4択・番号は10問ずつ・分からない問題は20問")
        print(f"  同じ番号 : 平均 {r['S']['mean']:.3f}  中央値 {r['S']['median']:g}  最低/最高 {r['S']['mn']}/{r['S']['mx']}  2点以下 {pct1(r['S']['le2'])}（{once_in(r['S']['le2'])}）  8点以上 {pct1(r['S']['ge8'])}（{once_in(r['S']['ge8'])}）")
        print(f"  ばらばら : 平均 {r['M']['mean']:.3f}  中央値 {r['M']['median']:g}  最低/最高 {r['M']['mn']}/{r['M']['mx']}  2点以下 {pct1(r['M']['le2'])}（{once_in(r['M']['le2'])}）  8点以上 {pct1(r['M']['ge8'])}（{once_in(r['M']['ge8'])}）")
        print(f"  平均の差 d = {r['d']:.3f} → 答え: {r['key']}（|d|<0.25 でほぼ同じ）")
        same_json = {int(k): v for k, v in main_["same"]["hist"].items()}
        print("  model.json の山と同じ:", all(int(r["hs"][k]) == same_json.get(k, 0) for k in range(KMAX)))
        print("  山 同じ番号:", " ".join(f"{k}:{int(r['hs'][k])}" for k in range(KMAX)))
        print("  山 ばらばら:", " ".join(f"{k}:{int(r['hm'][k])}" for k in range(KMAX)))
        for k_ in list(jd)[2:]:
            a, b = jd[k_]["same"], jd[k_]["mix"]
            print(f"  {k_}: 平均 {a['mean']}/{b['mean']}  2点以下 {a['le2']:.1%}/{b['le2']:.1%}  8点以上 {a['ge8']:.1%}/{b['ge8']:.1%}  最低/最高 {a['min']}-{a['max']}/{b['min']}-{b['max']}")
    print(f"見本: {S['i']}番目の回  同じ番号 {S['rp']['same']}点  ばらばら {S['rp']['mix']}点  （山の値 {int(s[S['i']])} / {int(m[S['i']])}）")
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
note.DATE = "11.18"                                  # 日付欄（公開予定日）

ORG, ORG_D = "#e0801f", "#a85a0a"                    # 同じ番号（橙）
BLU, BLU_D = "#3f7fb5", "#2a5a85"                    # ばらばら（青）
HIT = RED
WALL, WALL_D = "#dbe8dd", "#c8dacd"
DESK_T, DESK_F, DESK_E = "#c99d68", "#a97c4a", "#8e6636"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は B（2番目）
LABELS = ["同じ番号", "ほぼ同じ", "ばらばら"]
KEY_LABEL = {"同じ番号": "同じ番号", "ほぼ同じ": "ほぼ同じ", "ばらばら": "ばらばら"}
CORRECT = 1

BIG_Q3 = ["分からない20問、", "同じ番号で埋める？", "ばらばら？"]                  # 1コマ目の3行（同じ大きさ）
BIG_Q = ["分からない20問、", "同じ番号で埋める？ばらばら？"]                      # 定位置（上）の2行
DETAIL_RULE = "40問・4択。2人とも、同じ20問が分からない"
DETAIL = "違うのは、分からない問題の埋め方だけ"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 960.0, 870.0
CARD_X = 60.0
CARD_Y_INTRO, CARD_Y_FINAL = 840.0, 610.0
CD_X, CD_Y = 790.0, 970.0
ROW_DT, GRADE_DT = 0.18, 0.20                       # 1問を塗る間隔・答え合わせの間隔（秒）
MARK_LAG = 0.45 * ROW_DT                            # 鉛筆が着いて 印が付くまで

# 教室の絵（カード内の座標）
COL_X = (250.0, 700.0)                              # 左（同じ番号）・右（ばらばら）の生徒の中心 x
FY, K_ST = 526.0, 3.0                               # 生徒の足もと y・大きさ（身長 100×K_ST px）
DESK_Y = 392.0                                      # 机のふち（これより下は机）
BAND_H = 42.0                                       # 机の前板（名札）
SHW, SHH = 400.0, 340.0                             # 答案用紙
SHEET_Y = 440.0
BLK_X = (18.0, 208.0)                               # 答案の2ブロック（1〜10問・11〜20問）の左端
BUB_DX, BUB_R = 41.0, 12.0
ROW_Y0, ROW_DY = 64.0, 27.5
CLOCK = (475.0, 226.0, 50.0)

# 山のグラフ
BX0, BPITCH, BW = 105.0, 56.0, 46.0
HB1, HB2 = 985.0, 1275.0                            # 上（同じ番号）・下（ばらばら）の底
HL1, HL2 = 708.0, 1050.0                            # 上・下のグラフの名前の y
HSCALE = 260.0 / 2830.0                             # 1回あたりの高さ（2830回で260px）


def setup():
    global T_F0, T_F1, T_G0, T_G1, T_H0, T_H1, T_N, T_REV, T_TW, T_TW2, T_TW3, T_P, T_Q, DURATION, SCENES
    T_F0 = T_GO + 1.0                               # 塗り始め
    T_F1 = T_F0 + N_UNK * ROW_DT                    # 20問を塗り終わる
    T_G0 = T_F1 + 1.4                               # 答え合わせ
    T_G1 = T_G0 + N_UNK * GRADE_DT
    T_H0 = T_G1 + 3.4                               # 1万回の山へ
    T_H1 = T_H0 + 3.8                               # 山が積み上がり終わる
    T_N = T_H1 + 0.1                                # 平均・中央値
    T_REV = T_N + 3.4                               # 答え
    T_TW = T_REV + 4.4                              # ひねり（山の形）
    T_TW2 = T_TW + 1.0                              # 2点以下・8点以上
    T_TW3 = T_TW + 3.6                              # いちばん高い回
    T_P = T_TW + 7.0                                # +0.75点の札
    T_Q = T_P + 3.6                                 # 締め
    DURATION = T_Q + 4.4
    SCENES = [("教室・見本の1回（塗る・答え合わせ）", T_GO, T_H0), ("1万回の点数の山（答え）", T_H0, T_TW),
              ("ひねり（山の形）", T_TW, T_P), ("短い札（+0.75点）", T_P, T_Q), ("締め", T_Q, DURATION)]


setup()


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


# ---------- 絵: 答案用紙・鉛筆 ----------

def bub_xy(r, j):
    """r 問目（0〜19）の 番号 j（0〜3）の丸の中心（答案内）"""
    return BLK_X[r // 10] + 21.0 + BUB_DX * j, ROW_Y0 + ROW_DY * (r % 10)


def mark_time(r):
    return T_F0 + r * ROW_DT + MARK_LAG


def grade_time(r):
    return T_G0 + r * GRADE_DT


def draw_sheet(ctx, ox, oy, marks, keys, t, digits=True, scale=1.0, col=INK):
    """答案用紙。marks=マークした番号（0〜3）20個、keys=正解の番号 20個。t より前に塗られた印・答え合わせ済みの正解を描く"""
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(scale, scale)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.22)
    rrect(ctx, 6, 9, SHW, SHH, 10)
    ctx.fill()
    rrect(ctx, 0, 0, SHW, SHH, 10)
    ctx.set_source_rgba(*hexrgb("#fffdf4"))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.85)
    ctx.move_to(SHW / 2, 12)
    ctx.line_to(SHW / 2, SHH - 12)
    _stroke(ctx, 1.6, PENCIL, 0.35)
    for b in range(2):
        for j in range(4):
            if digits and t >= 1.25:                                              # 冒頭の拡大のあいだは 番号の字を出さない（右が切れるため）
                text(ctx, str(j + 1), BLK_X[b] + 21.0 + BUB_DX * j, 30, 25, PENCIL, bold=False,
                     alpha=clamp01((t - 1.25) / 0.3))
    for r in range(N_UNK):
        age_m = t - mark_time(r)
        age_g = t - grade_time(r)
        hit = int(marks[r]) == int(keys[r])
        for j in range(4):
            cx, cy = bub_xy(r, j)
            ctx.arc(cx, cy, BUB_R, 0, 2 * math.pi)
            _stroke(ctx, 1.9, PENCIL, 0.55)
        if age_m >= 0:
            cx, cy = bub_xy(r, int(marks[r]))
            pop = 1 + 0.35 * (1 - ease_out(age_m / 0.12))
            graded_hit = age_g >= 0 and hit
            ctx.arc(cx, cy, (BUB_R - 1.0) * pop, 0, 2 * math.pi)
            if graded_hit:
                ctx.set_source_rgba(*hexrgb(HIT, 0.95))
            else:
                ctx.set_source_rgba(*hexrgb("#343a48", 0.92))
            ctx.fill()
            ctx.arc(cx - 3, cy - 3, 2.6, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.25)
            ctx.fill()
        if age_g >= 0:
            kx, ky = bub_xy(r, int(keys[r]))
            pr = 1 + 0.55 * (1 - ease_out(age_g / 0.15))
            ctx.arc(kx, ky, (BUB_R + 3.2) * pr, 0, 2 * math.pi)
            _stroke(ctx, 3.0 if hit else 2.2, HIT, 0.95 if hit else 0.75)
            if hit:                                                          # あたり: ✓
                ctx.move_to(kx - 5.0, ky + 0.5)
                ctx.line_to(kx - 1.5, ky + 4.5)
                ctx.line_to(kx + 5.5, ky - 4.5)
                _stroke(ctx, 3.0, "#ffffff", min(1.0, age_g / 0.1))
    ctx.restore()


def draw_pencil(ctx, x, y, a=1.0):
    """先が (x, y)。右上へ向かって伸びる鉛筆"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.95)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.push_group()
    ctx.move_to(0, 0)
    ctx.line_to(26, -8)
    ctx.line_to(26, 8)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#f1d3a4"))
    ctx.fill_preserve()
    _stroke(ctx, 2, INK, 0.9)
    ctx.move_to(0, 0)
    ctx.line_to(7, -2.4)
    ctx.line_to(7, 2.4)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#343a48"))
    ctx.fill()
    ctx.rectangle(26, -8, 92, 16)
    ctx.set_source_rgba(*hexrgb("#f4c430"))
    ctx.fill_preserve()
    _stroke(ctx, 2, INK, 0.9)
    ctx.rectangle(118, -8, 14, 16)
    ctx.set_source_rgba(*hexrgb("#b9c2cf"))
    ctx.fill_preserve()
    _stroke(ctx, 2, INK, 0.9)
    rrect(ctx, 132, -8, 20, 16, 5)
    ctx.set_source_rgba(*hexrgb("#f08a9b"))
    ctx.fill_preserve()
    _stroke(ctx, 2, INK, 0.9)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def pencil_pos(side, marks, t):
    """鉛筆の先の位置（答案内）と不透明度。側 0=左（同じ番号）・1=右（ばらばら）"""
    u = (t - T_F0) / ROW_DT
    if u >= N_UNK:
        return None
    r = int(max(0, math.floor(u)))
    fr = u - r if u >= 0 else 0.0
    cur = np.array(bub_xy(r, int(marks[r])))
    prev = np.array(bub_xy(r - 1, int(marks[r - 1]))) if r > 0 else cur + np.array([-30.0, -50.0])
    q = smooth(fr / 0.45)
    p = prev + (cur - prev) * q
    wob = 0.0 if fr < 0.45 else 1.6 * math.sin((fr - 0.45) * 60)
    a = 1.0 if u >= 0 else clamp01((t - (T_F0 - 0.4)) / 0.4)
    return float(p[0] + wob), float(p[1] - wob), a


# ---------- 絵: 教室のカード ----------

def clock_state(t):
    """のこり時間（赤い扇の割合）: 塗り始めから答え合わせまでに 0.85 → 0.12 へ"""
    return 0.85 - 0.73 * clamp01(t / T_G0)


def draw_clock(ctx, t):
    cx, cy, r = CLOCK
    ctx.arc(cx, cy, r + 5, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#8e6636"))
    ctx.fill()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#fffdf4"))
    ctx.fill()
    f = clock_state(t)
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r - 5, -math.pi / 2, -math.pi / 2 + 2 * math.pi * f)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(RED, 0.55))
    ctx.fill()
    for i in range(12):
        a_ = i * math.pi / 6
        ctx.move_to(cx + math.cos(a_) * (r - 8), cy + math.sin(a_) * (r - 8))
        ctx.line_to(cx + math.cos(a_) * (r - 2), cy + math.sin(a_) * (r - 2))
    _stroke(ctx, 2.6, INK, 0.85)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    _stroke(ctx, 3, INK, 0.9)
    am = -math.pi / 2 + 2 * math.pi * (t / 6.0)
    ah = -math.pi / 2 + 2 * math.pi * (t / 72.0) + 0.6
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(ah) * (r * 0.5), cy + math.sin(ah) * (r * 0.5))
    _stroke(ctx, 5, INK, 0.95)
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(am) * (r * 0.78), cy + math.sin(am) * (r * 0.78))
    _stroke(ctx, 3.6, INK, 0.95)
    ctx.arc(cx, cy, 5, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(RED))
    ctx.fill()
    text(ctx, "のこり時間", cx, cy + r + 24, 24, PENCIL, bold=False)


def scores(t):
    """答え合わせの途中経過 (左, 右)"""
    S = samples()
    a = sum(1 for r in range(N_UNK) if grade_time(r) <= t and int(S["same"][r]) == int(S["key"][r]))
    b = sum(1 for r in range(N_UNK) if grade_time(r) <= t and int(S["mix"][r]) == int(S["key"][r]))
    return a, b


def draw_room(ctx, t):
    S = samples()
    # 壁と床
    fill(ctx, WALL)
    ctx.rectangle(0, 0, CARD_W, CARD_H)
    ctx.fill()
    for i in range(12):
        fill(ctx, (1, 1, 1, 0.38))
        ctx.rectangle(30 + i * 74, 0, 30, 380)
        ctx.fill()
    fill(ctx, WALL_D)
    ctx.rectangle(0, 330, CARD_W, 60)
    ctx.fill()
    sh = (t * 70.0) % 400.0                                                     # 窓の光
    ctx.move_to(700 - sh * 1.2, 100)
    ctx.line_to(780 - sh * 1.2, 100)
    ctx.line_to(520 - sh * 1.2, 390)
    ctx.line_to(440 - sh * 1.2, 390)
    ctx.close_path()
    ctx.set_source_rgba(1.0, 0.97, 0.8, 0.22)
    ctx.fill()
    if t < T_G1 + 0.3:
        ctx.push_group()
        draw_clock(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - ease((t - T_G1) / 0.3))
    if t >= T_G1:
        note.sticky(ctx, "この1回だけなら、\n差が出る", CLOCK[0], 244, 30, "yellow", fg=RED,
                    a=ease_out((t - T_G1 - 0.15) / 0.3), tilt=-0.02)
    # 生徒と机
    for side in range(2):
        cx = COL_X[side]
        sway = 2.2 * math.sin(t * 1.7 + side * 1.3)
        student(ctx, cx + sway * 0.4, FY + 1.2 * math.sin(t * 2.0 + side), K_ST, side, t, 1 if side == 0 else -1)
        dx0 = cx - 218
        fill(ctx, DESK_T)                                                       # 机の上（上から見た面）
        rrect(ctx, dx0, DESK_Y + BAND_H, 436, CARD_H - DESK_Y - BAND_H + 10, 10)
        ctx.fill()
        fill(ctx, DESK_F)                                                       # 机の前板
        rrect(ctx, dx0, DESK_Y, 436, BAND_H, 8)
        ctx.fill_preserve()
        _stroke(ctx, 3, DESK_E, 0.9)
        col = ORG_D if side == 0 else BLU_D
        lab = "同じ番号で埋める" if side == 0 else "ばらばらに埋める"
        wlab = core.text_width(lab, 30) + 36
        fill(ctx, (*hexrgb(PAPER)[:3], 0.97))
        rrect(ctx, cx - wlab / 2, DESK_Y + 4, wlab, BAND_H - 8, 9)
        ctx.fill()
        text(ctx, lab, cx, DESK_Y + BAND_H / 2 + 0.5, 30, col)
        # 答案用紙（すこし傾けて机の上へ）
        ctx.save()
        ctx.translate(cx, SHEET_Y + SHH / 2)
        ctx.rotate(0.012 if side == 0 else -0.012)
        ctx.translate(-cx, -(SHEET_Y + SHH / 2))
        marks = S["same"] if side == 0 else S["mix"]
        draw_sheet(ctx, cx - SHW / 2, SHEET_Y, marks, S["key"], t)
        pp = pencil_pos(side, marks, t)
        if pp is not None:
            draw_pencil(ctx, cx - SHW / 2 + pp[0], SHEET_Y + pp[1], pp[2])
        elif t < T_F1 + 0.6:
            pass
        ctx.restore()
    # 答え合わせの途中経過
    if t >= T_G0:
        sc = scores(t)
        for side in range(2):
            n = sc[side]
            last = max([grade_time(r) for r in range(N_UNK) if grade_time(r) <= t and
                        int((S["same"] if side == 0 else S["mix"])[r]) == int(S["key"][r])] or [-9])
            pop = 1 + 0.3 * (1 - ease_out((t - last) / 0.15))
            cx = 104.0 if side == 0 else 856.0
            a_ = ease_out((t - T_G0) / 0.3)
            col = ORG_D if side == 0 else BLU_D
            text(ctx, "あたり", cx, 268, 28, PENCIL, bold=False, alpha=a_)
            ctx.save()
            ctx.translate(cx, 330)
            ctx.scale(pop, pop)
            text(ctx, f"{n}点", 0, 0, 74, col, alpha=a_)
            ctx.restore()


def card_y(m):
    return CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m


def draw_card(ctx, t, m):
    y0 = card_y(m)
    ctx.save()
    ctx.translate(CARD_X, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 24)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 16)
    ctx.clip()
    draw_room(ctx, t)
    ctx.restore()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 16)
    _stroke(ctx, 3.2, INK, 0.85)
    rrect(ctx, 76, 22, 440, 96, 12)                     # 題（左上）。冒頭の拡大で左が切れないよう x=88 から
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    text(ctx, "同じ40問のテスト（4択）", 96, 46, 32, INK, align="left")
    if t >= T_G0:
        text(ctx, "たとえば、この1回では", 96, 90, 34, INK, align="left")
    else:
        text(ctx, "分からない20問も 同じ", 96, 86, 26, PENCIL, align="left", bold=False)
    if m >= 0.999:                                       # 下の札は 場面が定位置に着いてから（カードの下端が y=1450 を超えないため）
        a2 = clamp01((t - T_GO) / 0.3)
        if a2 > 0:
            rrect(ctx, 24, CARD_H - 106, 912, 88, 12)
            ctx.set_source_rgba(*hexrgb(PAPER, 0.96 * a2))
            ctx.fill()
            if t < T_G0:
                text(ctx, "正解の番号は 1〜4が10問ずつ", CARD_W / 2, CARD_H - 82, 38, INK, alpha=a2)
                text(ctx, "（計算での見立て）", CARD_W / 2, CARD_H - 46, 28, PENCIL, bold=False, alpha=a2)
            else:
                b2 = ease_out((t - T_G0) / 0.3)
                text(ctx, "赤い丸＝あたり", CARD_W / 2, CARD_H - 82, 38, INK, alpha=b2)
                text(ctx, "点＝分からない20問のあたった数", CARD_W / 2, CARD_H - 46, 28, INK, bold=False, alpha=b2)
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
    z = 1.0 + 0.12 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: 場面が寄ったところから引く（下端を基準に）
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


# ---------- 点の山（1万回） ----------

def hist_alpha(t):
    if t < T_H0:
        return 0.0
    return ease((t - T_H0) / 0.35) * (1 - ease((t - T_P + 0.1) / 0.3))


def bar_x(k):
    return BX0 + (k + 0.5) * BPITCH


def tail_mix(t):
    """ひねりで 2点以下・8点以上 の棒が橙色に変わる割合"""
    return ease((t - T_TW) / 0.5) * (1 - ease((t - T_P + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    pr = clamp01((t - T_H0 - 0.8) / (T_H1 - T_H0 - 0.8))
    n = N_TRIAL if pr >= 1 else int(N_TRIAL * ease(pr))
    text(ctx, "分からない20問の点数を、1万回", 570, 622, 40, INK, alpha=a)
    sub_a = "（1問1点・分からない20問のうち あたった数）"
    sub_b = "中央値＝1万回の ちょうど真ん中の値"
    if t < T_N:
        text(ctx, sub_a, 570, 664, 26, PENCIL, bold=False, alpha=a)
    elif t < T_TW:
        text(ctx, sub_b, 570, 664, 28, PENCIL, bold=False, alpha=a * ease_out((t - T_N) / 0.3))
    else:
        text(ctx, "色のついた山 ＝ 2点以下・8点以上", 570, 664, 28, PENCIL, bold=False, alpha=a * ease_out((t - T_TW) / 0.3))
    tm = tail_mix(t)
    for pi, (base, cs_, hist_final, colr, name) in enumerate(((HB1, r["cs"], r["hs"], ORG, "同じ番号で埋めた"),
                                                              (HB2, r["cm"], r["hm"], BLU, "ばらばらに埋めた"))):
        text(ctx, name, 112, HL1 if pi == 0 else HL2, 34, ORG_D if pi == 0 else BLU_D, align="left", alpha=a)
        ctx.move_to(BX0 - 8, base)
        ctx.line_to(BX0 + KMAX * BPITCH + 6, base)
        _stroke(ctx, 3, INK, 0.75 * a)
        for k in range(KMAX):
            cnt = float(cs_[k, n])
            hgt = cnt * HSCALE
            tail = (k <= 2 or k >= 8)
            if hgt >= 0.5:
                rrect(ctx, bar_x(k) - BW / 2, base - hgt, BW, hgt, 5)
                c1 = hexrgb(colr)
                c2 = hexrgb("#e5484d")
                mix_ = tm if tail else 0.0
                col = tuple(c1[i] * (1 - mix_) + c2[i] * mix_ for i in range(3))
                ctx.set_source_rgba(col[0], col[1], col[2], 0.92 * a)
                ctx.fill()
            if k in (0, 2, 4, 6, 8, 10, 12) or True:
                text(ctx, str(k), bar_x(k), base + 26, 26, INK, bold=False, alpha=a)
        text(ctx, "点", BX0 + KMAX * BPITCH + 28, base + 26, 24, PENCIL, bold=False, alpha=a)
    text(ctx, f"{n:,} / 10,000 回", 760, 1335, 26, PENCIL, bold=False, alpha=a * (1 - ease((t - T_REV) / 0.3)))
    # 平均・中央値
    if T_N <= t:
        u = ease_out((t - T_N) / 0.3) * a * (1 - ease((t - T_TW) / 0.3))
        for pi, (base, st_, colr) in enumerate(((HB1, r["S"], ORG_D), (HB2, r["M"], BLU_D))):
            yy = base - 235 if pi == 0 else base - 175
            text(ctx, f"平均 {f2(st_['mean'])}点", 755, yy, 52, colr, alpha=u)
            text(ctx, f"中央値 {pts(st_['median'])}", 755, yy + 64, 52, colr, alpha=u)
        x_ = bar_x(0) - BPITCH / 2 + (r["S"]["mean"] + 0.5) * BPITCH
        for base in (HB1, HB2):
            ctx.move_to(x_, base - (275 if base == HB1 else 205))
            ctx.line_to(x_, base)
            ctx.set_dash([8, 6])
            _stroke(ctx, 3, RED, 0.85 * u)
            ctx.set_dash([])
    # 2点以下・8点以上
    if t >= T_TW2:
        for pi, (base, st_, colr) in enumerate(((HB1, r["S"], ORG_D), (HB2, r["M"], BLU_D))):
            u = ease_out((t - T_TW2 - 0.15 * pi) / 0.3) * a * (1 - ease((t - T_P + 0.1) / 0.3))
            yy = base - 205 if pi == 0 else base - 178
            for xc, nm, f in ((bar_x(1) + 6, "2点以下", st_["le2"]), (760.0, "8点以上", st_["ge8"])):
                text(ctx, nm, xc, yy, 36, colr, alpha=u)
                text(ctx, once_in(f), xc, yy + 40, 34, RED, alpha=u)


# ---------- 答え ----------

def answer_key():
    return results()["key"]


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"答えは『{KEY_LABEL[key]}』。", 570, 1392, 52, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_TW:
        r = results()
        d = ease_out((t - T_TW - 0.15) / 0.3) * (1 - ease((t - T_P + 0.1) / 0.3))
        note.sticky(ctx, "平均は同じで、違うのは山の形。\nばらばらだと、高い点も低い点も出やすい。", 565, 1396, 35, "pink", fg=RED, a=d, tilt=-0.012)


# ---------- 短い札（+0.75点） ----------

def draw_plus(ctx, t):
    a = ease((t - T_P) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3)) if t >= T_P else 0.0
    if a <= 0:
        return
    note.sticky(ctx, "埋め方を変えても、平均は増えない。\n1問分かれば、平均は0.75点増える。", 570, 760, 42, "yellow", a=a, tilt=-0.015)
    base, per = 1390.0, 360.0
    ctx.move_to(130, base)
    ctx.line_to(930, base)
    _stroke(ctx, 3, INK, 0.75 * a)
    u = ease_out((t - T_P - 0.5) / 0.6)
    for xc, v, nm, colr in ((290.0, 0.25, "分からない1問", BLU_D), (710.0, 1.0, "分かる1問", ORG_D)):
        hgt = per * v * u
        rrect(ctx, xc - 80, base - hgt, 160, max(hgt, 1.0), 8)
        ctx.set_source_rgba(*hexrgb(colr if v < 1 else ORG, 0.9 * a))
        ctx.fill()
        text(ctx, nm, xc, base + 36, 32, INK, alpha=a)
        text(ctx, f"{v:g}点", xc, base - hgt - 34, 44, RED, alpha=a * u)
    if t >= T_P + 1.4:
        w = ease_out((t - T_P - 1.4) / 0.4) * a
        yt = base - per * 0.25
        yb = base - per
        ctx.move_to(400, yt)
        ctx.line_to(400, yb + 8)
        ctx.line_to(390, yb + 22)
        ctx.move_to(400, yb + 8)
        ctx.line_to(410, yb + 22)
        _stroke(ctx, 4, RED, 0.9 * w)
        text(ctx, "+0.75点", 515, (yt + yb) / 2 + 4, 40, RED, alpha=w)
        ctx.move_to(400, yb)
        ctx.line_to(626, yb)
        ctx.set_dash([8, 6])
        _stroke(ctx, 2.5, RED, 0.6 * w)
        ctx.set_dash([])


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に教室（0秒目から動き、場面が寄った所から引く）"""
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
            text(ctx, DETAIL, 565, 756, 26, PENCIL, bold=False, alpha=a1)
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
    S = samples()
    note.sticky(ctx, "あなたなら、\nどちらで埋めますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 950, 36, INK, bold=False, alpha=r)
    sc = 1.0
    for side in range(2):
        cx = 285.0 if side == 0 else 715.0
        marks = S["same"] if side == 0 else S["mix"]
        ctx.save()
        ctx.push_group()
        draw_sheet(ctx, cx - SHW * sc / 2, 1010, marks, S["key"], 1e9, digits=True, scale=sc)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(q)
        ctx.restore()
        text(ctx, "同じ番号" if side == 0 else "ばらばら", cx, 1010 + SHH * sc + 50, 38, ORG_D if side == 0 else BLU_D, alpha=q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_hist(ctx, t)
        draw_plus(ctx, t)
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
    for i in range(4):                                      # 冒頭: 時計 カチ・カチ
        mx.add(0.1 + 0.5 * i, blip(900 if i % 2 else 760, 0.04), 0.25)
    S = samples()
    for r in range(N_UNK):                                  # 鉛筆で塗る音
        mx.add(mark_time(r), blip(420 + 18 * (r % 5), 0.05), 0.22)
    for r in range(N_UNK):                                  # 答え合わせ: あたりは ちん
        hit_a = int(S["same"][r]) == int(S["key"][r])
        hit_b = int(S["mix"][r]) == int(S["key"][r])
        if hit_a or hit_b:
            mx.add(grade_time(r), bell(1318.5 if hit_a and hit_b else (1046.5 if hit_a else 1174.7), 0.5), 0.30)
        else:
            mx.add(grade_time(r), blip(330, 0.04), 0.12)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                     # 山
    beat(mx, T_H0 + 0.8, T_H1, bpm=132, vol=0.5, accel=True)
    mx.add(T_H1, thump(), 0.5)
    mx.add(T_N, bell(784.0, 0.9), 0.45)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    mx.add(T_TW2, bell(880.0, 0.9), 0.4)
    mx.add(T_TW3, blip(659.3, 0.14), 0.3)
    mx.add(T_P, bell(988.0, 1.0), 0.4)
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
    s, m = r["s"], r["m"]
    S = samples()
    rp = S["rp"]
    jd = json.loads((OUT / "cache" / "model.json").read_text(encoding="utf-8"))
    mj = jd[list(jd)[0]]
    checks = []
    # (1) 条件
    checks.append(("回数 = 1万", float(len(s)), float(N_TRIAL), 0.0))
    checks.append(("点の範囲（0〜40問中の分からない20問なので 0〜20）", float(s.min() >= 0 and s.max() <= N_UNK and m.min() >= 0 and m.max() <= N_UNK), 1.0, 0.0))
    checks.append(("山の合計 = 1万（同じ番号）", float(r["hs"].sum()), float(N_TRIAL), 0.0))
    checks.append(("山の合計 = 1万（ばらばら）", float(r["hm"].sum()), float(N_TRIAL), 0.0))
    checks.append(("山の横軸 0〜13 に全部入る", float(s.max() < KMAX and m.max() < KMAX), 1.0, 0.0))
    # (2) 計算の本体（marksheet_model）と同じ結果か
    checks.append(("山（同じ番号）が model.json と同じ", float(all(int(r["hs"][k]) == int(mj["same"]["hist"].get(str(k), 0)) for k in range(KMAX))), 1.0, 0.0))
    checks.append(("山（ばらばら）が model.json と同じ", float(all(int(r["hm"][k]) == int(mj["mix"]["hist"].get(str(k), 0)) for k in range(KMAX))), 1.0, 0.0))
    checks.append(("平均（同じ番号）が model.json と同じ", r["S"]["mean"], float(mj["same"]["mean"]), 5e-4))
    checks.append(("平均（ばらばら）が model.json と同じ", r["M"]["mean"], float(mj["mix"]["mean"]), 5e-4))
    checks.append(("2点以下の割合（同じ番号）が model.json と同じ", r["S"]["le2"], float(mj["same"]["le2"]), 5e-5))
    checks.append(("8点以上の割合（ばらばら）が model.json と同じ", r["M"]["ge8"], float(mj["mix"]["ge8"]), 5e-5))
    checks.append(("平均の差 d が model.json の答えと同じ", r["d"], float(mj["answer"][1]), 5e-4))
    # (3) 1問ごとに 当たる見込みは 4分の1（ばらばら）。1問分かれば +0.75点
    checks.append(("ばらばら: 1問あたりの平均 = 0.25（4択）", float(m.mean() / N_UNK), 0.25, 0.004))
    checks.append(("同じ番号: 1問あたりの平均 = 0.25（番号が10問ずつ）", float(s.mean() / N_UNK), 0.25, 0.004))
    checks.append(("分かる1問 1点 − 分からない1問 0.25点 = +0.75点", 1.0 - 0.25, 0.75, 0.0))
    # (4) 答え
    key, d = mm.answer_by_rule(s, m)
    checks.append(("規則の答え = ほぼ同じ", float(key == "ほぼ同じ"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号の並び: 同じ番号・ほぼ同じ・ばらばら の順", float(LABELS == ["同じ番号", "ほぼ同じ", "ばらばら"]), 1.0, 0.0))
    for dd, k_ in ((0.0, "ほぼ同じ"), (0.24, "ほぼ同じ"), (0.25, "同じ番号"), (-0.25, "ばらばら")):
        a_ = np.full(100, 5.0 + dd)
        b_ = np.full(100, 5.0)
        checks.append((f"規則の道具: d={dd:+.2f} → {k_}", float(mm.answer_by_rule(a_, b_)[0] == k_), 1.0, 0.0))
    # (5) 見本は1万回の中の1回そのもの
    i = S["i"]
    checks.append(("見本: 取り出し直した同じ番号の点 = 1万回の記録", float(rp["same"]), float(s[i]), 0.0))
    checks.append(("見本: 取り出し直したばらばらの点 = 1万回の記録", float(rp["mix"]), float(m[i]), 0.0))
    checks.append(("見本: 画面の答案から数えた点（同じ番号）= 1万回の記録", float(sum(int(S["same"][q]) == int(S["key"][q]) for q in range(N_UNK))), float(s[i]), 0.0))
    checks.append(("見本: 画面の答案から数えた点（ばらばら）= 1万回の記録", float(sum(int(S["mix"][q]) == int(S["key"][q]) for q in range(N_UNK))), float(m[i]), 0.0))
    checks.append(("見本: 画面の途中経過の最後 = 1万回の記録（同じ番号・ばらばら）", float(scores(T_G1 + 0.1) == (int(s[i]), int(m[i]))), 1.0, 0.0))
    checks.append(("見本: 乱数の順で最初に条件に合う回（0番目は除く）", float(i == next(j for j in range(1, N_TRIAL) if 4 <= s[j] <= 6 and not (4 <= m[j] <= 6))), 1.0, 0.0))
    checks.append(("見本: 同じ番号は 4〜6点、ばらばらは 4〜6点でない", float(4 <= s[i] <= 6 and not (4 <= m[i] <= 6)), 1.0, 0.0))
    checks.append(("見本: 取り出した回のテストは 1〜4 が10問ずつ", float(np.array_equal(np.bincount(rp["key"], minlength=4), [10, 10, 10, 10])), 1.0, 0.0))
    checks.append(("見本: 分からない問題は 40問のうち20問（重ならない）", float(len(set(rp["idx"].tolist())) == N_UNK and rp["idx"].max() < N_Q), 1.0, 0.0))
    checks.append(("見本: 同じ番号は 20問すべて同じ番号（③）", float(len(set(int(v) for v in S["same"])) == 1 and int(S["same"][0]) == PICK == 2), 1.0, 0.0))
    checks.append(("見本: 画面の正解の番号 = テストの正解の番号（分からない20問ぶん）", float(np.array_equal(S["key"], rp["key"][np.sort(rp["idx"])])), 1.0, 0.0))
    # (6) 画面に出す数字を、別の数え方で数え直す
    for nm, x, st_ in (("同じ番号", s, r["S"]), ("ばらばら", m, r["M"])):
        checks.append((f"{nm}: 2点以下の割合 数え直し", float(np.count_nonzero(x <= 2) / N_TRIAL), st_["le2"], 0.0))
        checks.append((f"{nm}: 8点以上の割合 数え直し", float(np.count_nonzero(x >= 8) / N_TRIAL), st_["ge8"], 0.0))
        checks.append((f"{nm}: 中央値 数え直し（並べた真ん中）", float(np.sort(x)[N_TRIAL // 2 - 1: N_TRIAL // 2 + 1].mean()), st_["median"], 0.0))
    checks.append(("画面: 平均が同じ（4.99点と4.98点）", float((f2(r["S"]["mean"]), f2(r["M"]["mean"])) == ("4.99", "4.98")), 1.0, 0.0))
    checks.append(("画面: 中央値はどちらも5点", float(r["S"]["median"] == 5 and r["M"]["median"] == 5), 1.0, 0.0))
    checks.append(("ひねり: ばらばらの2点以下は同じ番号の2倍以上（山の形の文）", float(r["M"]["le2"] >= 2 * r["S"]["le2"]), 1.0, 0.0))
    checks.append(("ひねり: ばらばらの8点以上は同じ番号の2倍以上（山の形の文）", float(r["M"]["ge8"] >= 2 * r["S"]["ge8"]), 1.0, 0.0))
    checks.append(("画面: いちばん高い回 10点と13点", float((r["S"]["mx"], r["M"]["mx"]) == (10, 13)), 1.0, 0.0))
    checks.append(("画面: 約30回に1回 / 約11回に1回 / 約32回に1回 / 約10回に1回",
                   float((once_in(r["S"]["le2"]), once_in(r["M"]["le2"]), once_in(r["S"]["ge8"]), once_in(r["M"]["ge8"])) ==
                         ("約30回に1回", "約11回に1回", "約32回に1回", "約10回に1回")), 1.0, 0.0))
    # 番号をならさないテストでは差が消える（description に書く）
    nb = jd["番号をならさない"]
    checks.append(("番号をならさない: 2点以下の割合の差 1ポイント以内（description の文）", abs(nb["same"]["le2"] - nb["mix"]["le2"]), 0.0, 0.01))
    checks.append(("番号をならさない: 8点以上の割合の差 1ポイント以内（description の文）", abs(nb["same"]["ge8"] - nb["mix"]["ge8"]), 0.0, 0.01))
    # (7) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (8) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("塗る時間 3秒以上", float(T_F1 - T_F0 >= 3.0), 1.0, 0.0))
    checks.append(("答え合わせ 3秒以上", float(T_G1 - T_G0 >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 答え合わせのあと 次の場面まで 3秒以上", float(T_H0 - T_G1 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 平均・中央値 3秒以上", float(T_REV - T_N >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 2点以下・8点以上 3秒以上", float(T_P - T_TW2 >= 3.0), 1.0, 0.0))
    checks.append(("鉛筆: 1問の間隔は 0.15秒以上", float(ROW_DT >= 0.15), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (9) 冒頭の動き
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
    S = samples()
    r = results()
    print(f"長さ {DURATION:.1f}秒  塗る {T_F0:.1f}-{T_F1:.1f}  答え合わせ {T_G0:.1f}-{T_G1:.1f}  山 {T_H0:.1f}-{T_H1:.1f}  平均・中央値 {T_N:.1f}  答え {T_REV:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}/{T_TW3:.1f}  札 {T_P:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: {S['i']}番目の回  同じ番号 {S['rp']['same']}点  ばらばら {S['rp']['mix']}点")
    print(f"  平均 {f2(r['S']['mean'])} / {f2(r['M']['mean'])}  中央値 {r['S']['median']:g} / {r['M']['median']:g}  答え: {r['key']}（差 {r['d']:.3f}）")
    print(f"  2点以下 {once_in(r['S']['le2'])} / {once_in(r['M']['le2'])}  8点以上 {once_in(r['S']['ge8'])} / {once_in(r['M']['ge8'])}  最高 {r['S']['mx']} / {r['M']['mx']}")
    print(f"  問い3行の文字 {min(big3_size(820.0), 92.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(820.0), 92.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_F0 + 0.5, T_F0 + 1.8, T_F1 - 0.4, T_F1 + 0.6, T_G0 + 0.5, T_G0 + 2.2, T_G1 - 0.2,
              T_G1 + 1.5, T_H0 + 1.5, T_H1 - 0.2, T_N + 1.2, T_REV + 0.9, T_TW + 0.8, T_TW2 + 1.6, T_TW3 + 1.2,
              T_P + 0.6, T_P + 2.2, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
