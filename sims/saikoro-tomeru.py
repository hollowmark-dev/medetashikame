"""サイコロ、3回で止める？6回まで振る？ 50点先取の勝負を1万回。— 2026-11-08 作成（公開予定 11.20・ナレーションなし・55〜65秒）

計算の本体は sims/saikoro_model.py（ルールと答えの決め方は、1万回を回す前に そのファイルの docstring に固定してある。ここでは変えない）。
この sim は「1万回の結果を読んで絵にする」ところ。

【置き方】（saikoro_model.py の docstring と同じ。結果を見て変えていない）
  ・自分の番では、決めた回数までサイコロを振って、出た目を足していく。途中で1が出たら、その番は0点（番は終わる）。
  ・決めた回数を振り終えたら、その番の点を持ち点に足す。先に50点に届いたほうの勝ち。どちらが先に振るかは毎回くじ（半々）。
  ・サイコロの目は1〜6が同じ確率。A は3回で止める、B は6回まで振る。変えるのは止める回数だけ。1回 = 勝負1回。1万回。
【答えの決め方】（answer_by_rule。計算の前に固定）
  勝つ回が多いほうが正解。勝率の差が2ポイント以内なら「ほぼ同じ」。
【見本の1回】 1万回の中の最初の1回そのもの（saikoro_model.game を seed 21 で1回目に回したもの）。
  同じ乱数で、サイコロの目まで取り出し直し（このファイルの play_all）、1万回の勝ち数が saikoro_model.match(3, 6) と一致するかを run_checks で照合する。
【言い方】 「中央値」は出さない（1番の点は平均だけ）。画面に「計算での見立て」は出さない（確率のルールだけで決まるため）。

問い: 「サイコロ勝負。/ 3回で止める？/ 6回まで振る？」
選択肢: A 3回で止める ／ B ほぼ同じ ／ C 6回まで振る（正解の記号は C。run_checks で確かめる）
見せ方: 冒頭（問い・2人が机でサイコロ）→ ルール1・2・3（札を1つずつ・見本の動き）→ 比べる条件（止める回数だけ）→ 見本の1回 → 1万回の勝ち数 → 答え → 理由（0点の割合・1番の平均）→ ひねり（9回まで）→ 締め
締め: 「あなたなら、何回で止めますか？」
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import saikoro_model as mm  # noqa: E402

SLUG = "saikoro-tomeru"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIAL = mm.R
CNT = 1.5                                          # 1万回の数え上げの秒数
GOAL = mm.GOAL
NA, NB = 3, 6                                         # A = 3回で止める（左）、B = 6回まで振る（右）


def answer_by_rule(win_b, win_a):
    """答えの決め方（計算の前に固定）。勝つ割合の差が2ポイント以内なら ほぼ同じ"""
    d = win_b - win_a
    if abs(d) <= 0.02 + 1e-9:
        return "ほぼ同じ", d
    return ("6回まで振る" if d > 0 else "3回で止める"), d


def pct0(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


_RES = {}


def _model_hash():
    return hashlib.md5(Path(mm.__file__).read_bytes()).hexdigest()[:10]


def play_all(n_games=N_TRIAL, seed=21):
    """saikoro_model.game と同じ順で乱数を使い、1万回を回し直す。1回目だけ、サイコロの目と各番の記録を残す"""
    rng = np.random.default_rng(seed)
    wins_a = np.zeros(n_games, bool)
    turns = np.zeros(n_games, np.int32)
    first = None
    for i in range(n_games):
        first_a = bool(rng.random() < 0.5)
        order = ("a", "b") if first_a else ("b", "a")
        a = b = 0
        rounds = 0
        hist = []
        winner = None
        while winner is None:
            rounds += 1
            for who in order:
                n = NA if who == "a" else NB
                d = rng.integers(1, 7, n)
                t = 0 if (d == 1).any() else int(d.sum())
                if who == "a":
                    a += t
                else:
                    b += t
                if i == 0:
                    hist.append(dict(who=who, pts=t, a=a, b=b, dice=[int(v) for v in d]))
                if a >= GOAL:
                    winner = "a"
                    break
                if b >= GOAL:
                    winner = "b"
                    break
        wins_a[i] = winner == "a"
        turns[i] = rounds
        if i == 0:
            first = dict(winner=winner, rounds=rounds, first_a=first_a, hist=hist)
    return wins_a, turns, first


def results():
    """1万回の結果。out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["r"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"saikoro_{_model_hash()}.json"
    if f.exists():
        z = json.loads(f.read_text(encoding="utf-8"))
        wins_a = np.array(z["wins_a"], bool)
        turns = np.array(z["turns"], np.int32)
        first = z["first"]
        turn_stats = z["turn"]
        vs3 = {int(k): v for k, v in z["vs3"].items()}
        p3 = z["p3"]
        rmed, rmax, rmin = z["rounds"]
    else:
        wins_a, turns, first = play_all()
        p3, tt = mm.match(NA, NB)                      # saikoro_model.match(3, 6)（既定の seed 21）
        rmed, rmax, rmin = float(np.median(tt)), int(tt.max()), int(tt.min())
        rng = np.random.default_rng(5)
        turn_stats = {}
        for n in (NA, NB):
            pts_ = np.array([mm.turn(rng, n) for _ in range(N_TRIAL)])
            turn_stats[str(n)] = dict(zero=float((pts_ == 0).mean()), mean=float(pts_.mean()))
        vs3 = {n: float(mm.match(n, NA, seed=31 + n)[0]) for n in range(1, 11)}
        f.write_text(json.dumps(dict(wins_a=wins_a.astype(int).tolist(), turns=turns.tolist(), first=first, turn=turn_stats,
                                     vs3=vs3, p3=float(p3), rounds=[rmed, rmax, rmin]), ensure_ascii=False), encoding="utf-8")
    win3 = int(wins_a.sum())
    win6 = N_TRIAL - win3
    key, d = answer_by_rule(win6 / N_TRIAL, win3 / N_TRIAL)
    _RES["r"] = dict(wins_a=wins_a, turns=turns, first=first, cum_a=np.cumsum(wins_a), win3=win3, win6=win6, key=key, d=d,
                     z3=turn_stats["3"]["zero"], z6=turn_stats["6"]["zero"], m3=turn_stats["3"]["mean"], m6=turn_stats["6"]["mean"],
                     vs3=vs3, p3=p3, rmed=rmed, rmax=rmax, rmin=rmin)
    return _RES["r"]


def sample():
    return results()["first"]


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    S = sample()
    if "--model" in sys.argv:
        print(f"{N_TRIAL}回  勝ち: 6回 {r['win6']}（{r['win6'] / N_TRIAL:.1%}） 3回 {r['win3']}（{r['win3'] / N_TRIAL:.1%}）  答え: {r['key']}（差 {r['d']:+.3f}）")
        print(f"  saikoro_model.match(3,6) の3回の勝ち率 {r['p3']:.4f} → {round(r['p3'] * N_TRIAL)}回  / このファイルで数え直し {r['win3']}回")
        print(f"  勝負の長さ: 中央値 {r['rmed']:g}  最短 {r['rmin']}  最長 {r['rmax']}")
        print(f"  1番: 0点 3回 {pct0(r['z3'])} / 6回 {pct0(r['z6'])}   平均 3回 {r['m3']:.2f} / 6回 {r['m6']:.2f}")
        print("  相手が3回のとき、こちらの止め方ごとの勝つ割合:", " ".join(f"{n}回:{pct0(v)}" for n, v in sorted(r["vs3"].items())))
    print(f"見本: 1回目  先に振る: {'3回の人' if S['first_a'] else '6回の人'}  勝ち: {'3回の人' if S['winner'] == 'a' else '6回の人'}  番の数 {S['rounds']}")
    for h in S["hist"]:
        print(f"  {'3回' if h['who'] == 'a' else '6回'}の人 目 {h['dice']} → {h['pts']}点   持ち点 3回 {h['a']} / 6回 {h['b']}")
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
note.DATE = "11.20"                                  # 日付欄（公開予定日）

ORG, ORG_D = "#e0801f", "#a85a0a"                    # 3回で止める（橙）
BLU, BLU_D = "#3f7fb5", "#2a5a85"                    # 6回まで振る（青）
DESK_T, DESK_F, DESK_E = "#c99d68", "#a97c4a", "#8e6636"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は C（3番目）
LABELS = ["3回で止める", "ほぼ同じ", "6回まで振る"]
KEY_LABEL = {"3回で止める": "3回で止める", "ほぼ同じ": "ほぼ同じ", "6回まで振る": "6回まで振る"}
CORRECT = 2

BIG_Q3 = ["サイコロ勝負。", "3回で止める？", "6回まで振る？"]            # 1コマ目の3行（同じ大きさ）
BIG_Q = ["サイコロ勝負。", "3回で止める？6回まで振る？"]                  # 定位置（上）の2行
DETAIL_RULE = "違うのは、止める回数だけ"
DETAIL = "サイコロ・ルール・50点・先に振る人（くじ）は同じ"

RULE0 = [("自分の番では、サイコロを", "続けて何回か振れる"), ("止めると、その番に足した", "点が自分の点になる"),
         ("1が出たら、その番の点は", "0になり、相手の番になる")]
RULES = [("ルール1", "自分の番では、サイコロを続けて何回か振れる\n止めると、その番に足した点が自分の点になる\n1が出たら、その番の点は0になり、相手の番になる"),
         ("ルール2", "出た目を足していく"), ("ルール3", "1が出たら、その番に足した点は0点"), ("ルール4", "先に50点に届いたほうが勝ち")]
RULE_SZ = 48

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (1.4, 2.0, 2.6)                              # 3・2・1
T_MOVE, T_GO = 3.2, 3.6
CY_INTRO, CY_FINAL = 910.0, 610.0                   # 教室（机の絵）の上端 y
PX = (290.0, 730.0)                                 # 左（3回）・右（6回）の人の中心 x
MID = 510.0                                         # 机の中央 x
FYR, K_ST = 440.0, 4.4                              # 足もと y（cy から）・大きさ（身長 100×K_ST px）
TURN = 1.15                                         # 見本: 1番の長さ
BAR_PX = 7.0                                        # 見本: 1点あたりの棒の長さ（50点 = 310px）
BAR_X0 = (100.0, 540.0)                             # 左右の棒の左端 x
EVENTS3 = [("a", 0.5, 10), ("b", 0.8, 28), ("a", 1.1, 27), ("a", 1.5, 41), ("b", 2.0, 51)]   # ルール3の棒（見本と同じ点）


def setup():
    global T_R0, T_R1, T_R2, T_R3, T_SET, T_S0, T_S1, T_WIN, T_H0, T_HC, T_REV, T_RS, T_TW, T_TW2, T_Q, DURATION, SCENES, RT
    T_R0 = T_GO                                     # ルール1（番と止める）5.7秒
    T_R1 = T_R0 + 5.85                               # ルール2（足していく）4.2秒
    T_R2 = T_R1 + 4.2                               # ルール3（1が出たら0点）5.0秒
    T_R3 = T_R2 + 5.0                               # ルール4（先に50点）4.2秒
    T_SET = T_R3 + 4.0                              # 比べる条件 4.0秒
    T_S0 = T_SET + 4.0                              # 見本
    T_S1 = T_S0 + 0.3
    T_WIN = T_S1 + 6 * TURN + 1.1                   # 最後の番が終わる
    T_H0 = T_WIN + 2.4                              # 1万回
    T_HC = T_H0 + 0.4                               # 数え上げ始め
    T_REV = T_H0 + 3.0                              # 答え
    T_RS = T_REV + 2.9                              # 理由
    T_TW = T_RS + 4.9                               # ひねり
    T_TW2 = T_TW + 3.1                              # ひねり2枚目
    T_Q = T_TW2 + 3.9                               # 締め
    DURATION = T_Q + 3.5
    RT = [(T_R0, T_R1), (T_R1, T_R2), (T_R2, T_R3), (T_R3, T_SET)]
    SCENES = [("冒頭（問い・2人が机でサイコロ）", 0.0, T_GO), ("ルール1 番と止める", T_R0, T_R1),
              ("ルール2 出た目を足していく", T_R1, T_R2), ("ルール3 1が出たら0点", T_R2, T_R3), ("ルール4 先に50点", T_R3, T_SET),
              ("比べる条件", T_SET, T_S0), ("見本の1回", T_S0, T_H0), ("1万回の勝ち数・答え", T_H0, T_RS),
              ("理由（0点の割合・1回の番の平均）", T_RS, T_TW), ("ひねり（9回まで）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def cards():
    """札: (文, 出る秒, 消える秒)。「1文字0.12秒＋1秒以上」と 公開前チェックの「0.5秒＋文字数÷6秒」の両方より長く映す"""
    out = []
    for i, (a_, b_) in enumerate(RULE0):                                  # ルール1: 1行ずつ出る（全部 場面の終わりまで残る）
        out.append((a_ + b_, T_R0 + R0_T[i] + 0.2, T_R1 - 0.1))
    for k in (1, 2, 3):
        a, b = RT[k]
        out.append((RULES[k][1], a + 0.25, b - 0.25))
    for s_ in ("違うのは、止める回数だけ。", "サイコロ・ルール・50点は同じ。", "先に振る人は、毎回くじで決める。",
               "3回の人は、3回振るか1が出るまで。", "6回の人は、6回振るか1が出るまで。"):
        out.append((s_, T_SET + 0.25, T_S0 - 0.2))
    out.append(("たとえば、この1回では", T_S0 + 0.3, T_H0 - 0.3))
    out.append(("6回の人の勝ち。", T_WIN + 0.3, T_H0 - 0.1))
    out.append(("正解は『6回まで振る』。", T_REV + 0.2, T_RS))
    out.append(("6回振る人は、3回に2回が0点になる。", T_RS + 0.95, T_TW - 0.15))
    out.append(("それでも、1回の番に入る点が大きい。", T_RS + 0.95, T_TW - 0.15))
    out.append(("もっと振れば もっと強い？", T_TW + 0.3, T_TW2))
    out.append(("9回まで振ると、3回の人に負ける。", T_TW2 + 0.3, T_Q - 0.2))
    out.append(("あなたなら、何回で止めますか？", T_Q + 0.3, DURATION - 0.2))
    return out


R0_T = (0.25, 0.9, 1.55)                            # ルール1の3行が出る秒（場面の頭から）


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



# ---------- 絵: サイコロ ----------
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


def lerp(a, b, u):
    return a + (b - a) * u


def rnd6(n):
    return ((int(n) * 1103515245 + 12345) >> 8) % 6 + 1


def die(ctx, cx, cy, s, v, rot=0.0, a=1.0, dim=False, glow=0.0):
    """サイコロ。s = 1辺の長さ。1の目は赤くて大きい（見分けやすい）。dim = 目を灰色にして沈ませる、glow = 赤い輪"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.28 * a)
    rrect(ctx, -s / 2 + s * 0.05, -s / 2 + s * 0.09, s, s, s * 0.18)
    ctx.fill()
    rrect(ctx, -s / 2, -s / 2, s, s, s * 0.18)
    ctx.set_source_rgba(*hexrgb("#e4e0d4" if dim else "#fffdf6", a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.92 * a))
    ctx.set_line_width(max(3.0, s * 0.03))
    ctx.stroke()
    for px, py in PIPS[int(v)]:
        ctx.new_path()
        if v == 1:
            ctx.arc(0, 0, s * 0.17, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(RED, a))
        else:
            ctx.arc(px * s * 0.27, py * s * 0.27, s * 0.095, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#9aa0ad" if dim else INK, a))
        ctx.fill()
    if glow > 0:
        rrect(ctx, -s * 0.62, -s * 0.62, s * 1.24, s * 1.24, s * 0.26)
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * glow * a))
        ctx.set_line_width(7)
        ctx.stroke()
    ctx.restore()


def throw(t, t0, dur, v, seed, p0, p1, h=150.0):
    """投げたサイコロの位置・向き・見えている目。t0 より前は None。dur 秒で p0 から p1 へ、はずんで止まる"""
    u = (t - t0) / dur
    if u < 0:
        return None
    rf = ((seed * 37) % 11 - 5) * 0.03
    if u >= 1.0:
        return dict(x=p1[0], y=p1[1], rot=rf, v=v, landed=True)
    e = ease_out(u)
    x = lerp(p0[0], p1[0], e)
    y = lerp(p0[1], p1[1], e) - h * (1 - u) ** 1.3 * abs(math.sin(math.pi * 2.5 * u))
    rot = rf + (1 - u) * (7 + seed % 3) * (1 if seed % 2 else -1)
    vv = v if u > 0.82 else rnd6(int(t * 16) + seed * 5)
    if vv == 1 and v != 1:                                   # 止まる目が1でないときは、転がる途中に1の面を見せない
        vv = 2 + (int(t * 16) + seed) % 5
    return dict(x=x, y=y, rot=rot, v=vv, landed=False)


def win(t, a, b, fi=0.3, fo=0.3):
    return clamp01((t - a) / fi) * (1 - clamp01((t - (b - fo)) / fo))


# ---------- 絵: 教室（2人と机） ----------
def cy_of(t):
    return lerp(CY_INTRO, CY_FINAL, INTRO.moved(t))


def draw_room_gfx(ctx, cy, t, mouth=(0.0, 0.0)):
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
        student(ctx, x, cy + FYR, K_ST, ci, t, 1 if ci == 0 else -1, mouth[ci])
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


def draw_placards(ctx, cy, a=1.0, active=None):
    for s, (lab, col, dcol, lt) in enumerate((("3回で止める", ORG, ORG_D, "#fbe7cf"), ("6回まで振る", BLU, BLU_D, "#d9e8f5"))):
        x, y = PX[s], cy + 500
        rrect(ctx, x - 160, y - 35, 320, 70, 16)
        ctx.set_source_rgba(*hexrgb(lt, 0.97 * a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.set_line_width(8 if active == s else 4.5)
        ctx.stroke()
        text(ctx, lab, x, y, 44, dcol, alpha=a)


def table_dice(ctx, cy, ds, s=130.0):
    """机の上のサイコロ。ds = throw() の結果のリスト"""
    for d in ds:
        if d:
            die(ctx, d["x"], d["y"], s, d["v"], d["rot"], d.get("a", 1.0), d.get("dim", False), d.get("glow", 0.0))


def intro_dice(t, cy):
    ds = []
    for s in range(2):
        P = 1.5
        ph = (t + 0.35 * s) % P
        k = int((t + 0.35 * s) // P)
        d = throw(ph, 0.0, 0.8, rnd6(k * 2 + s + 2), 3 + s + 2 * k, (PX[s] + (40 if s == 0 else -40), cy + 250), (MID + (-85 if s == 0 else 85), cy + 340))
        ds.append(d)
    return ds


# 見本の1回
def sample_turns():
    """各番のサイコロ（最初の1が出るまで。1が出たらそこで止める）"""
    out = []
    for h in sample()["hist"]:
        dd = []
        for v in h["dice"]:
            dd.append(v)
            if v == 1:
                break
        out.append(dd)
    return out


def sample_state(t):
    S = sample()
    H_ = S["hist"]
    sc = [0.0, 0.0]
    cur = None
    for k, h in enumerate(H_):
        Ts = T_S1 + k * TURN
        if t >= Ts + 1.1:
            sc = [float(h["a"]), float(h["b"])]
            continue
        if t >= Ts:
            prev = (H_[k - 1]["a"], H_[k - 1]["b"]) if k else (0, 0)
            new = (h["a"], h["b"])
            si = 0 if h["who"] == "a" else 1
            th = t - Ts
            f = ease(clamp01((th - 0.8) / 0.3))
            sc = [float(prev[0]), float(prev[1])]
            sc[si] = prev[si] + (new[si] - prev[si]) * f
            cur = dict(k=k, th=th, si=si, h=h, f=f, Ts=Ts)
        break
    return sc, cur


def draw_bar(ctx, x0, y, sc, pend, col, a=1.0, zero=False):
    h = 60.0
    wbox = 54 * BAR_PX
    rrect(ctx, x0, y, wbox, h, 10)
    ctx.set_source_rgba(1, 1, 1, 0.9 * a)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9 * a)
    if sc > 0.05:
        ctx.save()
        rrect(ctx, x0, y, wbox, h, 10)
        ctx.clip()
        ctx.rectangle(x0, y, sc * BAR_PX, h)
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.fill()
        if pend > 0:
            ctx.rectangle(x0 + sc * BAR_PX, y, pend * BAR_PX, h)
            ctx.set_source_rgba(*hexrgb(col, 0.45 * a))
            ctx.fill()
        ctx.restore()
    xl = x0 + 50 * BAR_PX
    ctx.move_to(xl, y - 12)
    ctx.line_to(xl, y + h + 12)
    _stroke(ctx, 5, RED, 0.95 * a)
    text(ctx, "50", xl, y + h + 34, 30, RED, alpha=a)


def draw_sample_layer(ctx, cy, t, a):
    """見本の1回: 持ち点の棒・数字・サイコロ・今の番の点"""
    sc, cur = sample_state(t)
    S = sample()
    ds = []
    mouth = [0.0, 0.0]
    pend = [0.0, 0.0]
    tags = []
    if cur:
        h = cur["h"]
        th = cur["th"]
        si = cur["si"]
        dd = sample_turns()[cur["k"]]
        n = len(dd)
        for i, v in enumerate(dd):
            xi = MID + (i - (n - 1) / 2) * 140
            d = throw(t, cur["Ts"] + i * 0.03, 0.4, v, cur["k"] * 7 + i + 1, (PX[si] + (50 if si == 0 else -50), cy + 250), (xi, cy + 340), h=130.0)
            if d:
                d["a"] = 1 - clamp01((th - 0.9) / 0.2)
                if h["pts"] == 0 and th >= 0.6:
                    d["dim"] = v != 1
                    d["glow"] = 1.0 if v == 1 else 0.0
                ds.append(d)
        if th < 0.5:
            mouth[si] = 0.7
        if th >= 0.45:
            if h["pts"] > 0:
                shown = int(round(h["pts"] * ease(clamp01((th - 0.45) / 0.25))))
                if th < 0.8:
                    pend[si] = shown
                tags.append((si, f"+{shown}", None, 1 - clamp01((th - 0.95) / 0.15)))
            else:
                tags.append((si, "0点", RED, 1 - clamp01((th - 0.95) / 0.15)))
    table_dice(ctx, cy, ds)
    for si in range(2):
        col, dcol = (ORG, ORG_D) if si == 0 else (BLU, BLU_D)
        draw_bar(ctx, BAR_X0[si], cy + 650, sc[si], pend[si], col, a)
        text(ctx, str(int(round(sc[si]))), PX[si], cy + 598, 100, dcol, alpha=a)
    for si, s_, colr, al in tags:
        dcol = ORG_D if si == 0 else BLU_D
        jit = math.sin(t * 60) * 6 if colr == RED else 0.0
        text(ctx, s_, PX[si] + 135 + jit, cy + 598, 62, colr or dcol, alpha=a * al)
    if t >= T_WIN:                                                      # 6回の人が51点で勝ち
        wa = ease_out((t - T_WIN) / 0.4)
        note.pen_circle(ctx, PX[1], cy + 598, 82, 64, RED, seed=77, width=7, progress=wa, alpha=a)
    return mouth


def draw_room_scene(ctx, t):
    if t < T_SET - 0.01:
        a = 1 - ease(clamp01((t - T_GO) / 0.3)) if t >= T_GO else 1.0
    else:
        a = ease(clamp01((t - T_SET) / 0.3)) * (1 - ease(clamp01((t - T_H0) / 0.4)))
    if a <= 0:
        return
    cy = cy_of(t)
    active = None
    mouth = [0.0, 0.0]
    ctx.push_group()
    # 人と机（冒頭だけ、場面が寄ったところから引く。文字は拡大しない）
    ctx.save()
    z = 1.0 + 0.10 * (1 - ease(clamp01(t / 1.1)))
    if z > 1.0:
        ctx.translate(540, cy + 400)
        ctx.scale(z, z)
        ctx.translate(-540, -(cy + 400))
    if T_S1 <= t < T_WIN:
        sc_, cur = sample_state(t)
        if cur:
            active = cur["si"]
            if cur["th"] < 0.5:
                mouth[cur["si"]] = 0.7
    draw_room_gfx(ctx, cy, t, tuple(mouth))
    if t < T_GO + 0.5:
        table_dice(ctx, cy, intro_dice(t, cy))
    ctx.restore()
    draw_placards(ctx, cy, 1.0, active)
    if t >= T_S0 - 0.01:
        ba = ease_out(clamp01((t - T_S0) / 0.4))
        draw_sample_layer(ctx, cy, t, ba)
        if t < T_S1 + TURN:                                             # 先に振るのは くじで決まる
            fa = win(t, T_S0 + 0.6, T_S1 + TURN, 0.3, 0.3)
            note.pen_circle(ctx, PX[1] - 205, cy + 500, 26, 26, RED, seed=61, width=5, alpha=fa)
            text(ctx, "先", PX[1] - 205, cy + 500, 34, RED, alpha=fa)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    # 札
    if T_SET <= t < T_S0:
        sa = win(t, T_SET + 0.25, T_S0 - 0.2, 0.2, 0.15)
        lines = "違うのは、止める回数だけ。\nサイコロ・ルール・50点は同じ。\n先に振る人は、毎回くじで決める。\n3回の人は、3回振るか1が出るまで。\n6回の人は、6回振るか1が出るまで。"
        note.sticky(ctx, lines, 540, 1298, 40, "yellow", fg=INK, a=sa, tilt=-0.015)
    if T_S0 <= t < T_WIN:
        sa = win(t, T_S0 + 0.3, T_WIN, 0.3, 0.25)
        note.sticky(ctx, "たとえば、この1回では", 565, 1424, 44, "yellow", fg=INK, a=sa, tilt=-0.015)
    if T_WIN <= t < T_H0:
        sa = win(t, T_WIN + 0.2, T_H0 - 0.05, 0.15, 0.12)
        note.sticky(ctx, "6回の人の勝ち。", 565, 1422, 48, "yellow", fg=RED, a=sa, tilt=-0.015)


# ---------- 絵: ルールの札と見本 ----------
STRIP_Y = 1300.0
STRIP_X = (235.0, 505.0, 775.0)
TW, TH = 262.0, 212.0


def token(ctx, cx, cy, s, col, a=1.0, sc=1.0, shake=0.0):
    if a <= 0:
        return
    ctx.save()
    ctx.translate(cx + shake, cy)
    ctx.scale(sc, sc)
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.2 * a)
    rrect(ctx, -TW / 2 + 7, -TH / 2 + 10, TW, TH, 26)
    ctx.fill()
    rrect(ctx, -TW / 2, -TH / 2, TW, TH, 26)
    ctx.set_source_rgba(1, 1, 1, 0.97 * a)
    ctx.fill_preserve()
    _stroke(ctx, 4.6, INK, 0.9 * a)
    text(ctx, s, 0, 8, 140 if len(s) <= 2 else 110, col, alpha=a)
    ctx.restore()


def token_crumble(ctx, cx, cy, s, col, p):
    """札が6つのかけらになって崩れ落ちる（p: 0〜1）"""
    i = 0
    pw, ph = TW / 3, TH / 2
    for r in range(2):
        for c in range(3):
            px0, py0 = -TW / 2 + c * pw, -TH / 2 + r * ph
            vx = ((i * 37) % 7 - 3) * 12
            fall = 20 * p ** 1.6 + (i % 3) * 3 * p
            rot = ((i % 5) - 2) * 0.28 * p
            al = 1 - clamp01((p - 0.35) / 0.65)
            ctx.save()
            ctx.translate(cx + vx * p, cy + fall)
            ctx.translate(px0 + pw / 2, py0 + ph / 2)
            ctx.rotate(rot)
            ctx.translate(-(px0 + pw / 2), -(py0 + ph / 2))
            ctx.rectangle(px0, py0, pw, ph)
            ctx.clip()
            token(ctx, 0, 0, s, col, al)
            ctx.restore()
            i += 1


def rule_header(ctx, k, a, t0, u):
    tag, s = RULES[k]
    text(ctx, tag, 170, 598, 30, RED, alpha=a)
    note.sticky(ctx, s, 540, 668, RULE_SZ, "yellow", fg=INK, a=a * ease_out(clamp01((u - 0.25) / 0.3)), tilt=-0.015)


def rule_mat(ctx):
    ctx.set_source_rgba(0.15, 0.1, 0.05, 0.2)
    rrect(ctx, 86, 790, 850, 420, 34)
    ctx.fill()
    rrect(ctx, 80, 780, 850, 420, 34)
    ctx.set_source_rgba(*hexrgb(DESK_T))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)
    for i in range(7):
        yy = 815 + i * 55
        ctx.move_to(110, yy)
        ctx.curve_to(400, yy - 8, 650, yy + 9, 900, yy - 2)
        _stroke(ctx, 2.2, DESK_E, 0.2)


BIGD = 345.0
DIE_END = (505.0, 990.0)
DIE_START = (230.0, 1000.0)


def rule_dice(ctx, t, t0, thr, slides, labels):
    """ルール1・2の大きなサイコロ。thr = [(投げはじめ, 着地, 目)]、slides = [(滑りはじめ, 終わり)]、labels = 札の文字"""
    u = t - t0
    for i, (ta, tb, v) in enumerate(thr):
        d = throw(u, ta, tb - ta, v, 11 + i * 3, DIE_START, DIE_END, h=50.0)
        if not d:
            continue
        al = 1.0
        if i < len(slides):
            sa, sb = slides[i]
            al = 1 - clamp01((u - sa) / (sb - sa)) if u >= sa else 1.0
        if u > (slides[i][1] if i < len(slides) else 1e9):
            continue
        glow = 0.0
        if v == 1 and d["landed"]:
            glow = 0.5 + 0.5 * math.sin((u - tb) * 14)
        die(ctx, d["x"], d["y"], BIGD, d["v"], d["rot"], al, False, glow)


def meter_row(ctx, y, label, lcol, sc, pend, col, a, active):
    """ルール1のメーター1本（上下に2本並べる）。active = 番の人（橙の枠が光る）"""
    rrect(ctx, 70, y - 42, 870, 84, 18)
    if active:
        ctx.set_source_rgba(*hexrgb("#fbe7cf", 0.7 * a))
        ctx.fill_preserve()
        glow = 0.6 + 0.4 * math.sin(core._CUR_T * 7)
        ctx.set_source_rgba(*hexrgb(ORG, glow * a))
        ctx.set_line_width(7)
    else:
        ctx.set_source_rgba(1, 1, 1, 0.35 * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(3)
    ctx.stroke()
    text(ctx, label, 165, y, 32, lcol, bold=active, alpha=a)
    x0, scl = 290.0, 10.0
    rrect(ctx, x0, y - 26, 54 * scl, 52, 12)
    ctx.set_source_rgba(1, 1, 1, 0.92 * a)
    ctx.fill_preserve()
    _stroke(ctx, 3.4, INK, 0.9 * a)
    if sc > 0.05 or pend > 0.05:
        ctx.save()
        rrect(ctx, x0, y - 26, 54 * scl, 52, 12)
        ctx.clip()
        if sc > 0.05:
            ctx.rectangle(x0, y - 26, sc * scl, 52)
            ctx.set_source_rgba(*hexrgb(col, a))
            ctx.fill()
        if pend > 0.05:
            ctx.rectangle(x0 + sc * scl, y - 26, pend * scl, 52)
            ctx.set_source_rgba(*hexrgb(col, 0.4 * a))
            ctx.fill()
        ctx.restore()
    xl = x0 + 50 * scl
    ctx.move_to(xl, y - 34)
    ctx.line_to(xl, y + 34)
    _stroke(ctx, 5, RED, 0.9 * a)
    text(ctx, str(int(round(sc))), 885, y, 60, lcol if active else PENCIL, alpha=a)


def rule0(ctx, t, a):
    """ルール1: 番と止める。3行を1つずつ出し、下で「3回振って止める → 足した点が、その人のメーターに入る」を見せる"""
    t0 = T_R0
    u = t - t0
    tag = RULES[0][0]
    text(ctx, tag, 170, 598, 30, RED, alpha=a)
    for i, (l1, l2) in enumerate(RULE0):
        al = ease_out(clamp01((u - R0_T[i]) / 0.3))
        if al <= 0:
            continue
        y0 = 648 + i * 144
        note.pen_circle(ctx, 98, y0 + 32, 30, 30, RED, seed=30 + i, width=5, alpha=al)
        text(ctx, str(i + 1), 98, y0 + 32, 40, RED, alpha=al)
        text(ctx, l1, 150, y0, 60, INK, align="left", alpha=al)
        text(ctx, l2, 150, y0 + 64, 60, INK, align="left", alpha=al)
    # 見本の動き: 3回振る（4・+3・+5 = 12）→ 止める → 足した点がメーターに入る
    thr = [(1.0, 4), (1.6, 3), (2.2, 5)]
    sums = [4, 7, 12]
    lab = ["4", "+3", "+5"]
    DY = 1140.0
    pend = 0
    tok = None
    for i, (ta, v) in enumerate(thr):
        x = 150 + i * 175
        d = throw(u, ta, 0.4, v, 5 + i * 3, (60.0, DY - 20), (x, DY), h=30.0)
        if not d:
            continue
        fade = 1 - clamp01((u - 3.3) / 0.3)
        die(ctx, d["x"], d["y"], 150.0, d["v"], d["rot"], fade * a)
        if u >= ta + 0.4:
            pend = sums[i]
            tok = i
            text(ctx, lab[i], x, DY + 100, 46, INK, alpha=a * fade)
    f = ease(clamp01((u - 3.5) / 0.8))                      # 足した点が メーターへ飛び込む
    score = 12 * f
    meter_row(ctx, 1302, "この人の番", RED, score, pend * (1 - f), ORG, a, True)
    meter_row(ctx, 1392, "相手", PENCIL, 0.0, 0.0, BLU, a * 0.8, False)
    if tok is not None:
        s_ = ("4", "=7", "=12")[tok]
        if u < 3.5:
            pop = ease_out(clamp01((u - (thr[tok][0] + 0.4)) / 0.2))
            token(ctx, 760, DY, s_, RED if tok == 2 else INK, a * pop, 0.78 + 0.1 * pop)
        elif f < 1.0:
            tx = lerp(760, 290 + 12 * 10, f)
            ty = lerp(DY, 1302, f)
            token(ctx, tx, ty, "=12", RED, a * (1 - ease(clamp01((f - 0.7) / 0.3))), lerp(0.88, 0.3, f))
    if 3.0 <= u < 4.6:                                       # 止める！
        sp = ease_out(clamp01((u - 3.0) / 0.2)) * (1 - clamp01((u - 4.3) / 0.3))
        text(ctx, "止める！", 400, DY, 84, RED, alpha=a * sp)


def rule1(ctx, t, a):
    t0 = T_R1
    u = t - t0
    rule_header(ctx, 1, a, t0, u)
    rule_mat(ctx)
    thr = [(0.4, 1.0, 4), (1.6, 2.2, 3)]
    slides = [(1.2, 1.5), (2.4, 2.7)]
    rule_dice(ctx, t, t0, thr, slides, None)
    toks = [("4", INK), ("+3", INK)]
    for i, (s, col) in enumerate(toks):
        sa, sb = slides[i]
        if u < sa:
            continue
        f = ease(clamp01((u - sa) / (sb - sa)))
        x = lerp(DIE_END[0], STRIP_X[i], f)
        y = lerp(DIE_END[1], STRIP_Y, f)
        token(ctx, x, y, s, col, 1.0, lerp(0.55, 1.0, f))
    if u >= 3.0:
        p = ease_out(clamp01((u - 3.0) / 0.3))
        token(ctx, STRIP_X[2], STRIP_Y, "=7", RED, p, 0.8 + 0.2 * p)
        ctx.save()
        ctx.move_to(STRIP_X[0] + 105 + 8, STRIP_Y + 150)
        ctx.restore()


def rule2(ctx, t, a):
    t0 = T_R2
    u = t - t0
    rule_header(ctx, 2, a, t0, u)
    rule_mat(ctx)
    thr = [(0.4, 1.0, 5), (1.4, 2.0, 6), (2.7, 3.3, 1)]
    slides = [(1.1, 1.4), (2.1, 2.4)]
    rule_dice(ctx, t, t0, thr, slides, None)
    toks = [("5", INK), ("+6", INK)]
    crash = clamp01((u - 3.7) / 0.6)
    shake = math.sin(u * 55) * 7 * win(u, 3.3, 3.7, 0.05, 0.1) if 3.3 <= u < 3.7 else 0.0
    for i, (s, col) in enumerate(toks):
        sa, sb = slides[i]
        if u < sa:
            continue
        f = ease(clamp01((u - sa) / (sb - sa)))
        x = lerp(DIE_END[0], STRIP_X[i], f)
        y = lerp(DIE_END[1], STRIP_Y, f)
        if u >= 3.7:
            token_crumble(ctx, x, y, s, col, crash)
        else:
            token(ctx, x + shake, y, s, col, 1.0, lerp(0.55, 1.0, f))
    if u >= 2.5:
        p = ease_out(clamp01((u - 2.5) / 0.3))
        if u >= 3.7:
            token_crumble(ctx, STRIP_X[2], STRIP_Y, "=11", RED, crash)
        else:
            token(ctx, STRIP_X[2] + shake, STRIP_Y, "=11", RED, p, 0.8 + 0.2 * p)
    if u >= 4.2:
        p = ease_out(clamp01((u - 4.2) / 0.3))
        text(ctx, "0点", STRIP_X[2] - 20, STRIP_Y + 4, 170 * (0.8 + 0.2 * p), RED, alpha=p)
        text(ctx, "×", STRIP_X[1] - 20, STRIP_Y + 6, 160, RED, alpha=p * 0.9)


def meter_bars(ctx, vals, a, with_stamp, u):
    sc = 12.5
    x0 = 250.0
    ys = (960.0, 1190.0)
    bh = 110.0
    xl = x0 + 50 * sc
    names = (("3回の人", ORG, ORG_D), ("6回の人", BLU, BLU_D))
    for i in range(2):
        y = ys[i]
        text(ctx, names[i][0], x0 + 80, y - 34, 40, names[i][2], alpha=a)
        rrect(ctx, x0, y, 54 * sc, bh, 18)
        ctx.set_source_rgba(1, 1, 1, 0.92 * a)
        ctx.fill_preserve()
        _stroke(ctx, 4, INK, 0.9 * a)
        if vals[i] > 0.05:
            ctx.save()
            rrect(ctx, x0, y, 54 * sc, bh, 18)
            ctx.clip()
            ctx.rectangle(x0, y, vals[i] * sc, bh)
            ctx.set_source_rgba(*hexrgb(names[i][1], a))
            ctx.fill()
            ctx.restore()
        text(ctx, str(int(round(vals[i]))), 150, y + bh / 2, 110, names[i][2], alpha=a)
    ctx.move_to(xl, 900)
    ctx.line_to(xl, 1340)
    _stroke(ctx, 7, RED, 0.95 * a)
    text(ctx, "50点", xl, 876, 34, RED, alpha=a)


def rule3(ctx, t, a):
    t0 = T_R3
    u = t - t0
    rule_header(ctx, 3, a, t0, u)
    vals = [0.0, 0.0]
    prev = [0.0, 0.0]
    for who, te, pts in EVENTS3:
        i = 0 if who == "a" else 1
        f = ease(clamp01((u - te) / 0.35))
        if u >= te:
            vals[i] = prev[i] + (pts - prev[i]) * f
        prev[i] = pts if u >= te + 0.35 else prev[i]
    meter_bars(ctx, vals, a, False, u)
    ts = EVENTS3[-1][1] + 0.55
    if u >= ts:
        p = ease_out(clamp01((u - ts) / 0.25))
        ctx.save()
        ctx.translate(620, 1130)
        ctx.rotate(-0.12)
        sc_ = 1 + 0.4 * (1 - p)
        ctx.scale(sc_, sc_)
        text(ctx, "勝ち", 0, 0, 120, RED, alpha=p)
        ctx.restore()
        note.pen_circle(ctx, 620, 1130, 150, 80, RED, seed=88, width=7, progress=p, alpha=a)


def draw_rules(ctx, t):
    fns = (rule0, rule1, rule2, rule3)
    for k, (ta, tb) in enumerate(RT):
        a = clamp01((t - ta) / 0.25) * (1 - clamp01((t - tb) / 0.25))
        if a <= 0:
            continue
        ctx.push_group()
        fns[k](ctx, t, a)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


# ---------- 絵: 1万回の勝ち数・答え ----------
def draw_hist_scene(ctx, t):
    a = clamp01((t - T_H0) / 0.4) * (1 - clamp01((t - T_RS) / 0.3))
    if a <= 0:
        return
    r = results()
    ctx.push_group()
    text(ctx, "1万回の勝負、勝った回", 580, 650, 46, INK, alpha=1.0)
    p = ease(clamp01((t - T_HC) / CNT))
    n = int(p * N_TRIAL)
    wa = int(r["cum_a"][n - 1]) if n > 0 else 0
    wb = n - wa
    text(ctx, f"{n:,}回目", 110, 700, 36, PENCIL, bold=False, align="left")
    base = 1215.0
    sc_ = 0.08
    for i, (cx, v, col, dcol, lab) in enumerate(((300.0, wa, ORG, ORG_D, "3回で止める"), (745.0, wb, BLU, BLU_D, "6回まで振る"))):
        hgt = v * sc_
        rrect(ctx, cx - 125, base - 470, 250, 470, 14)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.5)
        if hgt > 1:
            rrect(ctx, cx - 125, base - hgt, 250, hgt, 14)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3.4, INK, 0.9)
        text(ctx, f"{v:,}", cx, base - max(hgt, 0) - 55, 96, dcol)
        text(ctx, lab, cx, base + 48, 40, dcol)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.2) / 0.3) * (1 - ease((t - T_RS + 0.1) / 0.3))
        note.sticky(ctx, f"正解は『{KEY_LABEL[r['key']]}』。", 570, 1385, 52, "yellow", fg=RED, a=b, tilt=-0.02)


def draw_reasons(ctx, t):
    a = clamp01((t - T_RS) / 0.3) * (1 - clamp01((t - T_TW) / 0.3))
    if a <= 0:
        return
    r = results()
    u = t - T_RS
    ctx.push_group()
    cols = ((290.0, "3回で止める", ORG_D), (745.0, "6回まで振る", BLU_D))
    for cx, lab, col in cols:
        text(ctx, lab, cx, 655, 46, col)
    ctx.move_to(90, 710)
    ctx.line_to(930, 710)
    _stroke(ctx, 2.5, PENCIL, 0.5)
    rows = (("1回の番で 0点になる割合", (pct0(r["z3"]), pct0(r["z6"])), 775, 885, 0.15),
            ("1回の番の平均", (f"{r['m3']:.1f}点", f"{r['m6']:.1f}点"), 1030, 1140, 0.5))
    for lab, (v3, v6), yl, yn, ts in rows:
        al = ease_out(clamp01((u - ts) / 0.35))
        text(ctx, lab, 520, yl, 42, INK, alpha=al)
        text(ctx, v3, 290, yn, 150, ORG_D, alpha=al)
        text(ctx, v6, 735, yn, 150, BLU_D, alpha=al)
    s = ease_out(clamp01((u - 0.8) / 0.3))
    note.sticky(ctx, "6回振る人は、3回に2回が0点になる。\nそれでも、1回の番に入る点が大きい。", 540, 1370, 40, "yellow", fg=INK, a=s, tilt=-0.015)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_twist(ctx, t):
    a = clamp01((t - T_TW) / 0.3) * (1 - clamp01((t - T_Q) / 0.35))
    if a <= 0:
        return
    r = results()
    u = t - T_TW
    ctx.push_group()
    text(ctx, "3回で止める人と勝負したとき、", 560, 650, 36, INK)
    text(ctx, "こちらが ○回で止めると、勝つ回は？", 560, 698, 36, INK)
    base, sc_ = 1215.0, 5.6
    x0, step, bw = 118.0, 82.0, 62.0
    for n in range(1, 11):
        v = r["vs3"][n]
        f = ease_out(clamp01((u - 0.3 - 0.12 * n) / 0.35))
        hgt = v * 100 * sc_ * f
        x = x0 + (n - 1) * step
        low = v < 0.5
        col = RED if (low and n >= 9) else BLU
        rrect(ctx, x, base - hgt, bw, max(hgt, 1), 8)
        ctx.set_source_rgba(*hexrgb(col, 0.95 if n in (3, 6, 9) or True else 0.8))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
        big = n == 9 and u >= (T_TW2 - T_TW)
        if f > 0.5:
            text(ctx, pct0(v), x + bw / 2, base - hgt - (30 if big else 22), 44 if big else 28, RED if big else INK, alpha=min(1.0, (f - 0.5) * 2))
        text(ctx, str(n), x + bw / 2, base + 30, 30, INK)
    yl = base - 50 * sc_
    ctx.set_dash([14, 10])
    ctx.move_to(100, yl)
    ctx.line_to(930, yl)
    _stroke(ctx, 3.4, RED, 0.8)
    ctx.set_dash([])
    text(ctx, "50%", 890, yl - 22, 30, RED)
    text(ctx, "こちらが止める回数", 520, base + 78, 32, PENCIL, bold=False)
    if u >= T_TW2 - T_TW:
        p = ease_out(clamp01((u - (T_TW2 - T_TW) - 0.1) / 0.3))
        note.pen_circle(ctx, x0 + 8 * step + bw / 2, base - r["vs3"][9] * 100 * sc_ - 28, 56, 50, RED, seed=93, width=6, progress=p)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    if u < T_TW2 - T_TW:
        b = win(t, T_TW + 0.3, T_TW2, 0.3, 0.25)
        note.sticky(ctx, "もっと振れば もっと強い？", 570, 1385, 42, "yellow", fg=INK, a=b, tilt=-0.015)
    else:
        b = win(t, T_TW2 + 0.3, T_Q, 0.3, 0.3)
        note.sticky(ctx, f"9回まで振ると、3回の人に負ける。\n（勝つ回 {pct0(r['vs3'][9])}）", 570, 1375, 40, "pink", fg=RED, a=b, tilt=-0.015)


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
    note.sticky(ctx, "あなたなら、\n何回で止めますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r_ = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 960, 40, INK, bold=False, alpha=r_)
    for i in range(6):
        x = 170 + i * 148
        bob = math.sin((t - T_Q) * 3.0 + i) * 8
        die(ctx, x, 1240 + bob, 130, i + 1, 0.06 * math.sin((t - T_Q) * 2 + i * 1.7), a=q)


# ---------- 本体 ----------
def body(ctx, t):
    draw_room_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_rules(ctx, t)
        draw_hist_scene(ctx, t)
        draw_reasons(ctx, t)
        draw_twist(ctx, t)
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
def rattle(mx, t0, n=1, vol=0.2):
    for i in range(4):
        mx.add(t0 + i * 0.07, blip(280 + 40 * ((i * 3) % 4), 0.03), vol)
    mx.add(t0 + 0.5, blip(210, 0.06), vol * 1.2)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 164.8, 196.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(4):                                      # 冒頭: サイコロ ころころ
        rattle(mx, 0.1 + 1.5 * i, vol=0.22)
    for ta in (1.0, 1.7, 2.4):                              # ルール1（番と止める）
        rattle(mx, T_R0 + ta)
    mx.add(T_R0 + 3.0, bell(784.0, 0.6), 0.3)
    for ta in (0.4, 1.6):                                   # ルール2（足していく）
        rattle(mx, T_R1 + ta)
    mx.add(T_R1 + 3.0, bell(880.0, 0.9), 0.4)
    for ta in (0.4, 1.4, 2.7):                              # ルール3（1が出たら0点）
        rattle(mx, T_R2 + ta)
    mx.add(T_R2 + 2.5, bell(784.0, 0.6), 0.3)
    mx.add(T_R2 + 3.7, riser(0.5), 0.3)
    mx.add(T_R2 + 4.2, thump(), 0.45)
    for _w, te, _p in EVENTS3:                              # ルール4
        mx.add(T_R3 + te, blip(520, 0.06), 0.25)
    mx.add(T_R3 + EVENTS3[-1][1] + 0.55, bell(1046.5, 0.8), 0.45)
    S = sample()
    for k, h in enumerate(S["hist"]):                       # 見本
        Ts = T_S1 + k * TURN
        rattle(mx, Ts, vol=0.2)
        if h["pts"] == 0:
            mx.add(Ts + 0.6, blip(220, 0.12), 0.3)
        else:
            mx.add(Ts + 0.65, bell(988.0, 0.5), 0.25)
    mx.add(T_WIN, bell(1046.5, 1.0), 0.45)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                     # 1万回
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_RS + 0.4, bell(698.5, 0.8), 0.35)
    mx.add(T_RS + 0.9, bell(784.0, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW2, bell(659.3, 0.8), 0.4)
    mx.add(T_TW2 + 0.1, thump(), 0.4)
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
    S = sample()
    H_ = S["hist"]
    checks = []
    # (1) 条件・数え直し
    checks.append(("回数 = 1万", float(len(r["wins_a"])), float(N_TRIAL), 0.0))
    checks.append(("勝ち数の合計 = 1万", float(r["win3"] + r["win6"]), float(N_TRIAL), 0.0))
    checks.append(("3回の勝ち数: 数え直し = saikoro_model.match(3, 6) の勝ち率×1万", float(r["win3"]), round(r["p3"] * N_TRIAL), 0.0))
    # 勝負の長さも同じ乱数で数え直した結果と saikoro_model の match が同じ
    p3b, tt = mm.match(NA, NB)
    checks.append(("勝負の長さ（最短）: 数え直し = match", float(r["turns"].min()), float(tt.min()), 0.0))
    checks.append(("勝負の長さ（最長）: 数え直し = match", float(r["turns"].max()), float(tt.max()), 0.0))
    checks.append(("勝負の長さ（中央値）: 数え直し = match", float(np.median(r["turns"])), float(np.median(tt)), 0.0))
    checks.append(("勝負の長さ: 最短2番・最長18番・中央値6番（資料）", float((int(r["rmin"]), int(r["rmax"]), r["rmed"]) == (2, 18, 6.0)), 1.0, 0.0))
    # (2) 画面の数字
    checks.append(("画面: 勝ち 6回5,591回・3回4,409回", float((r["win6"], r["win3"]) == (5591, 4409)), 1.0, 0.0))
    checks.append(("画面: 1番で0点 43%と66%", float((pct0(r["z3"]), pct0(r["z6"])) == ("43%", "66%")), 1.0, 0.0))
    checks.append(("画面: 1番の平均 6.9点と8.0点（8.0495。資料の8.1は 8.05 を二重に丸めた値）", float((f"{r['m3']:.1f}", f"{r['m6']:.1f}") == ("6.9", "8.0")), 1.0, 0.0))
    # 確率のルールだけから出る値で 別の数え方（1番の0点 = 1−(5/6)^n、平均 = n×4×(5/6)^n）
    for n_, z, m in ((NA, r["z3"], r["m3"]), (NB, r["z6"], r["m6"])):
        checks.append((f"{n_}回: 0点の割合 = 1−(5/6)^{n_}（確率のルール）", z, 1 - (5 / 6) ** n_, 0.012))
        checks.append((f"{n_}回: 1番の平均 = {n_}×4×(5/6)^{n_}（確率のルール）", m, n_ * 4 * (5 / 6) ** n_, 0.2))
    checks.append(("画面: 6回の人は3回に2回が0点（66% ≒ 2/3）", r["z6"], 2 / 3, 0.02))
    checks.append(("画面: 9回まで振ると勝つ回43%", float(pct0(r["vs3"][9]) == "43%"), 1.0, 0.0))
    checks.append(("ひねり: 9回・10回は 3回の人に負ける（50%未満）", float(r["vs3"][9] < 0.5 and r["vs3"][10] < 0.5), 1.0, 0.0))
    checks.append(("ひねり: 4〜7回は 3回の人に勝ち越す（50%超）", float(all(r["vs3"][n] > 0.5 for n in (4, 5, 6, 7))), 1.0, 0.0))
    checks.append(("ひねりのグラフ: 1回2%・2回30%・3回51%（資料の表）", float([pct0(r["vs3"][n]) for n in (1, 2, 3)] == ["2%", "30%", "51%"]), 1.0, 0.0))
    # (3) 答え
    key, d = answer_by_rule(r["win6"] / N_TRIAL, r["win3"] / N_TRIAL)
    checks.append(("規則の答え = 6回まで振る", float(key == "6回まで振る"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号の並び: 3回で止める・ほぼ同じ・6回まで振る の順", float(LABELS == ["3回で止める", "ほぼ同じ", "6回まで振る"]), 1.0, 0.0))
    for dd, k_ in ((0.0, "ほぼ同じ"), (0.02, "ほぼ同じ"), (0.021, "6回まで振る"), (-0.021, "3回で止める")):
        checks.append((f"規則の道具: 差 {dd:+.3f} → {k_}", float(answer_by_rule(0.5 + dd, 0.5)[0] == k_), 1.0, 0.0))
    # (4) 見本は1万回の中の最初の1回そのもの
    rng = np.random.default_rng(21)
    g = mm.game(rng, NA, NB, log=True)                      # saikoro_model.game そのまま（既定の seed 21 の1回目）
    checks.append(("見本: saikoro_model.game の1回目と勝者が同じ", float(g[0] == S["winner"]), 1.0, 0.0))
    checks.append(("見本: 番の数が同じ", float(g[1] == S["rounds"]), 1.0, 0.0))
    checks.append(("見本: 先に振る人が同じ（くじ）", float(g[3] == S["first_a"]), 1.0, 0.0))
    checks.append(("見本: 各番の（誰・点・持ち点）が saikoro_model.game と同じ",
                   float([(h["who"], h["pts"], h["a"], h["b"]) for h in H_] == [tuple(x) for x in g[2]]), 1.0, 0.0))
    checks.append(("見本: サイコロの目から数えた各番の点 = 記録", float(all((0 if 1 in h["dice"] else sum(h["dice"])) == h["pts"] for h in H_)), 1.0, 0.0))
    checks.append(("見本: 3回の人は毎番3つ・6回の人は毎番6つの目", float(all(len(h["dice"]) == (NA if h["who"] == "a" else NB) for h in H_)), 1.0, 0.0))
    checks.append(("見本: 1万回の記録の1回目と勝者が同じ（6回の人の勝ち）", float(bool(r["wins_a"][0]) == (S["winner"] == "a") and S["winner"] == "b"), 1.0, 0.0))
    checks.append(("見本: 6回の人は0点を2回出して51点で勝つ", float(sum(1 for h in H_ if h["who"] == "b" and h["pts"] == 0) == 2 and H_[-1]["b"] == 51), 1.0, 0.0))
    checks.append(("見本: 3回の人は10・17・14点を積んで41点", float([h["pts"] for h in H_ if h["who"] == "a"] == [10, 17, 14] and H_[-1]["a"] == 41), 1.0, 0.0))
    checks.append(("見本: 画面の番の数 7（棒の動きと札）", float(len(H_) == 7 and len(sample_turns()) == 7), 1.0, 0.0))
    sc_end, _ = sample_state(T_WIN + 0.1)
    checks.append(("見本: 画面の最後の持ち点 = 記録（41点・51点）", float((int(round(sc_end[0])), int(round(sc_end[1]))) == (H_[-1]["a"], H_[-1]["b"])), 1.0, 0.0))
    checks.append(("見本: ルール3の棒の点 = 見本の点（10・27・41 と 28・51）",
                   float([p for w, _t, p in EVENTS3 if w == "a"] == [10, 27, 41] and [p for w, _t, p in EVENTS3 if w == "b"] == [28, 51]), 1.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: 同じ大きさ（1つの大きさで3行とも描く）", float(len(set(core.text_width(l, s3) > 0 for l in BIG_Q3)) == 1), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q3) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(440 - s3 / 2 >= 370), 1.0, 0.0))
    # (6) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_.replace("\n", ""))
        wrap = {a_ + b_: max(len(a_), len(b_)) for a_, b_ in RULE0}      # ルール1の文は2行に折って描く（公開前チェックは 描いた1行ごと）
        need = max(0.12 * n_ + 1.0, 0.5 + wrap.get(s_, n_) / 6.0)
        checks.append((f"札「{s_}」が読み切れる（{tb - ta:.1f}秒 / 要る {need:.1f}秒）", float(tb - ta >= need), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("札は1つずつ（ルール1〜4の場面が重ならない）", float(all(RT[i][1] <= RT[i + 1][0] for i in range(3))), 1.0, 0.0))
    checks.append(("ルール1の3行は 1行ずつ（0.3秒以上あけて）出る", float(all(R0_T[i + 1] - R0_T[i] >= 0.3 for i in range(2))), 1.0, 0.0))
    checks.append(("ルールは4枚（番と止める・足す・1が出たら0点・先に50点）", float(len(RULES) == 4 and len(RT) == 4), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万回の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("長さ 55〜59秒（lint は60秒未満）", float(55.0 <= DURATION <= 59.0), 1.0, 0.0))
    # (7) 冒頭の動き
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
    S = sample()
    print(f"長さ {DURATION:.1f}秒  ルール {T_R0:.1f}/{T_R1:.1f}/{T_R2:.1f}/{T_R3:.1f}  比べる条件 {T_SET:.1f}  見本 {T_S0:.1f}-{T_H0:.1f}  1万回 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  勝ち: 6回 {r['win6']:,}回・3回 {r['win3']:,}回  答え: {r['key']}（差 {r['d']:+.3f}）")
    print(f"  1番: 0点 {pct0(r['z3'])}/{pct0(r['z6'])}  平均 {r['m3']:.1f}点/{r['m6']:.1f}点  9回まで振ると勝つ回 {pct0(r['vs3'][9])}")
    print(f"  見本: 1回目  {len(S['hist'])}番  3回 {S['hist'][-1]['a']}点 / 6回 {S['hist'][-1]['b']}点  勝ち: {'3回' if S['winner'] == 'a' else '6回'}の人")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q3):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2, 3.4,
          T_R0 + 0.8, T_R0 + 1.7, T_R0 + 2.9, T_R0 + 5.0,
          T_R1 + 0.9, T_R1 + 3.6,
          T_R2 + 1.7, T_R2 + 3.5, T_R2 + 4.6,
          T_R3 + 1.5, T_R3 + 3.6,
          T_SET + 2.2,
          T_S0 + 0.8, T_S1 + 0.8, T_S1 + 2 * TURN + 0.7, T_S1 + 4 * TURN + 0.7, T_S1 + 6 * TURN + 0.7, T_WIN + 1.2,
          T_HC + 1.2, T_REV - 0.3, T_REV + 1.5,
          T_RS + 2.5, T_TW + 2.2, T_TW2 + 1.8,
          T_Q + 1.8, DURATION - 0.2]
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
