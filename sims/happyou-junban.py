"""発表の順番を選べるなら、最初？最後？（歌の発表会・16人）— 2026-11-09 作成（ナレーションなし・60秒未満）

台本は research/shorts_junban_script_2026-11-09.md（ユーザーOK済み。文言・順番・数字は変えない。足したのは場面の絵だけ）。
計算の本体は sims/junban_model.py（置き方・seed 191・答えの決め方は、1万回を回す前に そのファイルの docstring に固定してある。ここでは変えない）。
この sim は「1万回の結果を読んで絵にする」ところ。

【置き方】（junban_model.py の docstring と同じ。結果を見て変えていない）
  ① 歌の発表会。出場者16人。実力は16人とも同じくらい（毎回くじで決まる正規分布）。
  ② 出番の効き目: 審査の点に「出番が後ろなほど少しずつ上がる分」を足す（最初0・最後 b・間は等分）。
     b は、1万回で「出番と順位の相関」が研究の値 0.188 になるように合わせた（Antipov & Pokryshevskaya 2017）。
  ③ 点の高い順に順位をつける。1回 = 発表会1回。1万回。変えるのは出番だけ（ほかの15人と出来のくじは同じ）。
【答えの決め方】（answer_by_rule。計算の前に固定）
  優勝する回の割合が2ポイント以上高いほうが正解。差がそれより小さければ「ほぼ同じ」。
【見本の1回】 1万回の最初の1回そのもの（最初の人4位・最後の人6位・優勝は3番目の人）。同じ乱数で数え直し（recount）、run_checks で照合する。
【言い方】 出番の効き目の形（1つ後ろごとに同じだけ）は置き方なので、画面に「計算での見立て」と小さく1回出す。中央値は出さない。
  答えは中立に「正解は『最後』。」。

問い: 「歌の発表会。16人。／出る順番を選べるなら、／最初？最後？」
選択肢: A 最初 ／ B ほぼ同じ ／ C 最後（正解の記号は C。run_checks で確かめる）
見せ方: 冒頭（問い・舞台と審査員・袖の16人）→ 研究の札3枚 → 比べ方（実力は同じ・ちがうのは出番だけ）→ 見本の1回 → 1万回の棒（優勝した回）・答え
        → 理由 → ひねり（3回に1回・効き目はその日の出来の差ほど大きくない）→ 締め
締め: 「あなたなら、何番目に出たいですか？」
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import junban_model as jm  # noqa: E402

SLUG = "happyou-junban"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
MODEL_JSON = Path(__file__).resolve().parents[1] / "out" / "models_1120" / "junban.json"

N_TRIAL = jm.R
N_SING = jm.N
CNT = 1.4                                            # 1万回の数え上げの秒数


def answer_by_rule(first_rate, last_rate):
    """答えの決め方（計算の前に固定）。優勝する割合が2ポイント以上高いほうが正解。差が小さければ ほぼ同じ"""
    d = last_rate - first_rate
    if abs(d) < 0.02 - 1e-9:
        return "ほぼ同じ", d
    return ("最後" if d > 0 else "最初"), d


_RES = {}


def _calib_b():
    """出番の効き目 b。calibrate は少し時間がかかるので out/<slug>/cache/ に置く"""
    p = OUT / "cache" / "b.json"
    if p.exists():
        return float(json.loads(p.read_text(encoding="utf-8"))["b"])
    b = jm.calibrate(jm.R_NEWWAVE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"b": b}), encoding="utf-8")
    return b


def results():
    """1万回の結果（junban_model.sim そのまま）。1回ごとの優勝を数え上げ用に持つ"""
    if _RES:
        return _RES["r"]
    b = _calib_b()
    skill, s, rank = jm.sim(b)
    first, last = rank[:, 0], rank[:, -1]
    wf, wl = (first == 1), (last == 1)
    summ = jm.summary(b)
    key, d = answer_by_rule(summ["win_first"] / N_TRIAL, summ["win_last"] / N_TRIAL)
    la = int((last < first).sum())
    _RES["r"] = dict(b=b, rank=rank, summ=summ, wf=int(wf.sum()), wl=int(wl.sum()), cum_f=np.cumsum(wf), cum_l=np.cumsum(wl),
                     key=key, d=d, last_above=la, first_above=N_TRIAL - la,
                     sample_rank=[int(x) for x in rank[0]])
    return _RES["r"]


def sample():
    """見本の1回 = 1万回の最初の1回"""
    r = results()
    rk = r["sample_rank"]
    return dict(first_rank=rk[0], last_rank=rk[-1], winner_pos=rk.index(1) + 1, ranks=rk)


def recount(seed=191, n=N_TRIAL):
    """junban_model.sim と同じ順で乱数を使い、点数から別の書き方（argmax・点の比較）で数え直す（照合用）"""
    b = results()["b"]
    rng = np.random.default_rng(seed)
    pos = np.arange(N_SING) / (N_SING - 1)
    skill = rng.normal(0, 1, (n, N_SING))
    sc = skill + b * pos
    win = sc.argmax(1)
    s0 = sc[0]
    order0 = list(np.argsort(-s0))
    return dict(win_first=int((win == 0).sum()), win_last=int((win == N_SING - 1).sum()),
                last_above=int((sc[:, -1] > sc[:, 0]).sum()),
                first_rank0=order0.index(0) + 1, last_rank0=order0.index(N_SING - 1) + 1, winner0=int(order0[0]) + 1)


# ---- --model / --pick（絵は読み込まない） ----
if __name__ == "__main__" and ("--model" in sys.argv or "--pick" in sys.argv):
    r = results()
    S = sample()
    print(f"{N_TRIAL}回  優勝: 最初に歌った人 {r['wf']:,}回（{r['wf'] / N_TRIAL:.1%}） 最後に歌った人 {r['wl']:,}回（{r['wl'] / N_TRIAL:.1%}）  答え: {r['key']}（差 {r['d']:+.3f}）")
    print(f"  最後の人が最初の人より上: {r['last_above']:,}回 / 最初の人が上: {r['first_above']:,}回（{r['first_above'] / N_TRIAL:.1%}）  b={r['b']:.3f}")
    print(f"見本: 1回目  最初の人{S['first_rank']}位  最後の人{S['last_rank']}位  優勝は{S['winner_pos']}番目の人  順位{S['ranks']}")
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
note.DATE = "11.25"                                  # 日付欄（公開予定日の仮置き）

FC, FC_D = "#e0801f", "#a85a0a"                      # 最初に歌った人（橙）
LC, LC_D = "#3f7fb5", "#2a5a85"                      # 最後に歌った人（青）
GOLD, GOLD_D = "#f4b400", "#b07d00"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は C（3番目）
LABELS = ["最初", "ほぼ同じ", "最後"]
KEY_LABEL = {"最初": "最初", "ほぼ同じ": "ほぼ同じ", "最後": "最後"}
CORRECT = 2

BIG_Q = ["歌の発表会。16人。", "出る順番を選べるなら、", "最初？最後？"]            # 1コマ目の3行（同じ大きさ）・上の定位置の3行

# ---------- 配置 ----------
CY_INTRO, CY_FINAL = 830.0, 655.0                    # 舞台の枠の上端 y（冒頭は問いのぶん下げる）
STAGE_H = 715.0
TABLE_Y = 142.0                                      # 審査員席の机の天板（cy から）
FLOOR_Y = 205.0                                      # 床の始まり
SING_X, SING_FY, SING_K = 330.0, 400.0, 2.1          # 歌う人（後ろ姿）の位置・足もと・大きさ
ROW_Y = (462.0, 562.0)                               # 袖の列（cy から）
ROW_DX, ROW_S = 98.0, 86.0

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.7, 0.9, 1.1)
T_CD = (1.2, 1.8, 2.4)                               # 3・2・1
T_MOVE, T_GO = 2.8, 3.2

CARD_TEXT = {
    "c1": "出番をくじで決める\n歌の大会がある。",
    "c2": "その12年分・576人の\n記録をもとに計算する。",
    "c4a": "16人とも、実力は同じくらい。",
    "c4b": "ちがうのは出番だけ。",
    "s0": "たとえば、この1回では",
    "s1": "この回は、最初の人のほうが上だった。",
    "ans": "正解は『最後』。",
    "a1": "優勝したのは、\n最初に歌った人が294回。\n最後に歌った人が1,095回。",
    "c3": "出番が後ろの人ほど、\n順位が少し上がっていた。",
    "rs": "審査員は、あとで聞いた歌ほど、\n少し高く点をつけていた。",
    "tw1": "それでも、最初の人が最後の人より\n上だった回は、約3回に1回。",
    "tw2": "出番の効き目は、\nその日の出来の差ほど大きくない。",
    "q": "あなたなら、\n何番目に出たいですか？",
}


def need(s_):
    """札が読み切れる最短の秒数（「1文字0.12秒＋1秒以上」と 公開前チェックの「0.5秒＋行の文字数÷6秒」の大きいほう）"""
    n_ = len(s_.replace("\n", ""))
    return max(0.12 * n_ + 1.0, 0.5 + max(len(x) for x in s_.split("\n")) / 6.0)


def hold(key):
    return need(CARD_TEXT[key]) + 0.1


def setup():
    global T_R1, T_R2, T_R3, T_R4, T_S0, T_H0, T_HC, T_REV, T_RS, T_TW, T_TWB, T_Q, DURATION
    global SCENES, CARDS, SAMPLE_T
    T_R1 = T_GO                                      # 研究① 出番をくじで決める歌の大会
    T_R2 = T_R1 + 0.2 + hold("c1") + 0.1             # 研究② 12年分・576人の記録をもとに計算（向きは言わない）
    T_R4 = T_R2 + 0.2 + hold("c2") + 0.1             # 比べ方
    T_S0 = T_R4 + 0.2 + hold("c4a") + 0.05 + hold("c4b") + 0.1      # 見本の1回
    SAMPLE_T = dict(names=0.45, r1=2.95, r2=4.25, r3=5.55, card=6.4)
    T_H0 = T_S0 + SAMPLE_T["card"] + hold("s1") + 0.1                # 1万回
    T_HC = T_H0 + 0.3                                # 数え上げ始め
    T_REV = T_H0 + 2.8                               # 答え
    T_R3 = T_REV + 0.2 + hold("ans") + 0.07 + hold("a1") + 0.1      # 研究の結果 後ろの人ほど順位が上（答えの後で初めて見せる）
    T_RS = T_R3 + 0.2 + hold("c3") + 0.1             # 理由
    T_TW = T_RS + 0.2 + hold("rs") + 0.1             # ひねり①
    T_TWB = T_TW + 0.2 + hold("tw1") + 0.1           # ひねり②
    T_Q = T_TWB + 0.2 + hold("tw2") + 0.1            # 締め
    DURATION = T_Q + 0.25 + hold("q") + 0.15
    SCENES = [("冒頭（問い・舞台と審査員・袖の16人）", 0.0, T_GO), ("研究① 出番をくじで決める歌の大会", T_R1, T_R2),
              ("研究② 12年分・576人の記録をもとに計算", T_R2, T_R4), ("比べ方 実力は同じ・ちがうのは出番", T_R4, T_S0),
              ("見本の1回", T_S0, T_H0), ("1万回の優勝の棒・答え・数字", T_H0, T_R3), ("研究の結果 後ろの人ほど順位が上（答えの後）", T_R3, T_RS), ("理由（審査員は後で聞いた歌ほど高く）", T_RS, T_TW),
              ("ひねり① 3回に1回は最初の人が上", T_TW, T_TWB), ("ひねり② 効き目はその日の出来の差ほど大きくない", T_TWB, T_Q), ("締め", T_Q, DURATION)]
    CARDS = {
        "c1": (CARD_TEXT["c1"], T_R1 + 0.2, T_R1 + 0.2 + hold("c1")),
        "c2": (CARD_TEXT["c2"], T_R2 + 0.2, T_R2 + 0.2 + hold("c2")),
        "c4a": (CARD_TEXT["c4a"], T_R4 + 0.2, T_R4 + 0.2 + hold("c4a")),
        "c4b": (CARD_TEXT["c4b"], T_R4 + 0.25 + hold("c4a"), T_R4 + 0.25 + hold("c4a") + hold("c4b")),
        "s0": (CARD_TEXT["s0"], T_S0 + 0.2, T_S0 + 0.2 + hold("s0")),
        "s1": (CARD_TEXT["s1"], T_S0 + SAMPLE_T["card"], T_S0 + SAMPLE_T["card"] + hold("s1")),
        "ans": (CARD_TEXT["ans"], T_REV + 0.2, T_REV + 0.2 + hold("ans")),
        "a1": (CARD_TEXT["a1"], T_REV + 0.27 + hold("ans"), T_REV + 0.27 + hold("ans") + hold("a1")),
        "c3": (CARD_TEXT["c3"], T_R3 + 0.2, T_R3 + 0.2 + hold("c3")),
        "rs": (CARD_TEXT["rs"], T_RS + 0.2, T_RS + 0.2 + hold("rs")),
        "tw1": (CARD_TEXT["tw1"], T_TW + 0.2, T_TW + 0.2 + hold("tw1")),
        "tw2": (CARD_TEXT["tw2"], T_TWB + 0.2, T_TWB + 0.2 + hold("tw2")),
        "q": (CARD_TEXT["q"], T_Q + 0.25, T_Q + 0.25 + hold("q")),
    }


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


def person(ctx, x, fy, k, kind, t, wl=None, wr=None, mouth=0.0, jk=None, hr=None, tie_col="#c4414b"):
    """立っている人。(x, fy) は足もとの中心、身長は 100·k px。kind = 'host'（正面）/ 'you'（後ろ姿）。
    wl・wr = 画面の左・右の手首の位置（k を単位に、足もと中心から (dx, dy)）。None なら体の横に下ろす"""
    host = kind == "host"
    P = lambda dx, dy: (x + dx * k, fy + dy * k)    # noqa: E731
    jacket, jacket_d, pants = jk or (("#2b2837", "#1f1c29", "#3a3a48") if host else ("#3f9a8f", "#2f7d73", "#46587a"))
    hair = hr or ("#a3a3b3" if host else "#4a3322")
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
        poly([(0, -77.5), (-6.5, -81.5), (-6.5, -73.5)], tie_col, lw * 0.7)      # 蝶ネクタイ
        poly([(0, -77.5), (6.5, -81.5), (6.5, -73.5)], tie_col, lw * 0.7)
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




# ---------- 絵: 人の半身（袖で出番を待つ人・研究の人たち） ----------
BUST_COL = ["#e9967a", "#7fb3d5", "#82c99a", "#c39bd3", "#f0c36b", "#e48aa8"]
BUST_HAIR = ["#4a3322", "#2c2c34", "#8a5a2b", "#b5651d"]


def bust(ctx, x, yc, s, label, i, a=1.0, hl=0.0, hlcol=RED, tint=0.0):
    """人の半身。(x, yc) は全体の中心、s = 高さの目安。label = 番号札（None なら無し）。hl = 赤い丸、tint = 白く薄める度合い"""
    if a <= 0:
        return
    col = BUST_COL[i % 6]
    hair = BUST_HAIR[(i * 5 + 2) % 4]
    lw = max(1.8, s * 0.03)
    ctx.save()
    if tint > 0:
        ctx.push_group()
    rrect(ctx, x - 0.40 * s, yc - 0.06 * s, 0.80 * s, 0.52 * s, 0.20 * s)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.9 * a)
    ctx.new_path()
    ctx.arc(x, yc - 0.28 * s, 0.22 * s, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN, a))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.9 * a)
    ctx.new_path()
    ctx.arc(x, yc - 0.29 * s, 0.226 * s, math.pi * 1.02, math.pi * 1.98)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair, a))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.8, INK, 0.9 * a)
    if s >= 40:
        for sg in (-1, 1):
            ctx.new_path()
            ctx.arc(x + sg * 0.08 * s, yc - 0.26 * s, max(1.4, 0.026 * s), 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(INK, a))
            ctx.fill()
        ctx.new_path()
        ctx.arc(x, yc - 0.235 * s, 0.05 * s, 0.15 * math.pi, 0.85 * math.pi)
        _stroke(ctx, lw * 0.7, INK, 0.85 * a)
    if label is not None:
        rrect(ctx, x - 0.30 * s, yc + 0.08 * s, 0.60 * s, 0.34 * s, 0.06 * s)
        ctx.set_source_rgba(1, 1, 1, 0.97 * a)
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.8, INK, 0.8 * a)
        text(ctx, str(label), x, yc + 0.25 * s, max(24, round(s * 0.31)), INK, alpha=a)
    if tint > 0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - 0.62 * tint)
    ctx.restore()
    if hl > 0:
        note.pen_circle(ctx, x, yc, 0.62 * s, 0.62 * s, hlcol, seed=70 + i, width=5, progress=hl, alpha=a)


def lineup(ctx, cy, labels, t, a=1.0, hl=None, hlprog=1.0, tints=None):
    """袖で出番を待つ16人（2列×8人）。labels = 番号札の数字16個"""
    for i in range(16):
        r_, c_ = divmod(i, 8)
        x = 540 + (c_ - 3.5) * ROW_DX
        yc = cy + ROW_Y[r_] + 2.0 * math.sin(t * 3.0 + i * 0.9)
        bust(ctx, x, yc, ROW_S, labels[i], i, a=a, hl=hlprog if hl == i else 0.0, tint=(tints[i] if tints else 0.0))


def note_icon(ctx, x, y, s, col, a):
    """八分音符"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.new_path()
    ctx.save()
    ctx.rotate(-0.35)
    ctx.scale(1.0, 0.72)
    ctx.arc(0, 0, 0.62 * s, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill()
    ctx.new_path()
    ctx.move_to(0.55 * s, -0.1 * s)
    ctx.line_to(0.55 * s, -2.1 * s)
    ctx.curve_to(0.55 * s, -1.5 * s, 1.6 * s, -1.5 * s, 1.5 * s, -0.7 * s)
    ctx.set_line_width(max(2.2, 0.2 * s))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.stroke()
    ctx.restore()


# ---------- 絵: 舞台（壁・幕・床・審査員席） ----------
JUDGES = [("#7b3f61", "#5a2c47", "#3a3a48", "#3a2a22", "#e6c35a"), ("#2f5d8a", "#22456a", "#3a3a48", "#a3a3b3", "#d8434e"),
          ("#3d7a5a", "#2c5a42", "#3a3a48", "#4a3322", "#e6c35a"), ("#8a6a2f", "#6a4f22", "#3a3a48", "#2c2c34", "#3f7fb5"),
          ("#5b4b8a", "#43366a", "#3a3a48", "#8a5a2b", "#d8434e")]
JUDGE_X = (170.0, 355.0, 540.0, 725.0, 910.0)


def draw_hall(ctx, cy, t):
    """壁・幕・床と、横に並んだ審査員席"""
    ctx.save()
    rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
    ctx.clip()
    fill(ctx, "#e6dff0")
    ctx.paint()
    for i in range(5):                                              # 壁のうすい縦じま
        xx = 150 + i * 190
        ctx.rectangle(xx, cy - 35, 60, FLOOR_Y + 35)
        ctx.set_source_rgba(1, 1, 1, 0.22)
        ctx.fill()
    ctx.rectangle(60, cy + FLOOR_Y, 960, STAGE_H)                    # 床
    ctx.set_source_rgba(*hexrgb("#d6b98d"))
    ctx.fill()
    for i in range(9):
        yy = cy + FLOOR_Y + 40 + i * 56
        ctx.move_to(60, yy)
        ctx.line_to(1020, yy)
        _stroke(ctx, 2.0, "#a98a5e", 0.35)
    for x0_, x1_, sg in ((60, 135, 1), (945, 1020, -1)):             # 幕
        ctx.rectangle(x0_, cy - 35, x1_ - x0_, STAGE_H)
        ctx.set_source_rgba(*hexrgb("#a63a4a"))
        ctx.fill()
        for j in range(5):
            xx = x0_ + (j + 0.5) * (x1_ - x0_) / 5
            ctx.move_to(xx, cy - 35)
            ctx.line_to(xx + sg * 6, cy + STAGE_H)
            _stroke(ctx, 5, "#7a2433", 0.55)
    ctx.move_to(60, cy + FLOOR_Y)
    ctx.line_to(1020, cy + FLOOR_Y)
    _stroke(ctx, 3.4, INK, 0.7)
    # 審査員（机の天板で切る）
    ctx.save()
    ctx.rectangle(60, cy - 35, 960, TABLE_Y + 35)
    ctx.clip()
    for j, x in enumerate(JUDGE_X):
        jk, jd, pn, hr, tc = JUDGES[j]
        person(ctx, x, cy + TABLE_Y + 45 * 1.7, 1.7, "host", t + j * 0.9, jk=(jk, jd, pn), hr=hr, tie_col=tc)
    ctx.restore()
    rrect(ctx, 85, cy + TABLE_Y, 910, 28, 6)                          # 机の天板
    ctx.set_source_rgba(*hexrgb("#b98f62"))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.85)
    ctx.rectangle(95, cy + TABLE_Y + 26, 890, FLOOR_Y - TABLE_Y - 26)  # 机の前板
    ctx.set_source_rgba(*hexrgb("#8b6a45"))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.85)
    for j, x in enumerate(JUDGE_X):                                   # 机の上の点数表
        ctx.save()
        ctx.translate(x, cy + TABLE_Y + 12)
        ctx.rotate(-0.06 + 0.03 * j)
        rrect(ctx, -22, -9, 44, 18, 3)
        ctx.set_source_rgba(1, 1, 1, 0.96)
        ctx.fill_preserve()
        _stroke(ctx, 1.8, INK, 0.7)
        ctx.restore()
    ctx.restore()
    rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
    _stroke(ctx, 3, PENCIL, 0.6)


def draw_singer(ctx, cy, t, a=1.0):
    """歌う人（後ろ姿）。審査員のほうを向き、右手のマイクを口もとへ。音符が上がる"""
    ctx.save()
    ctx.push_group()
    sx = SING_X + 4 * math.sin(t * 2.2)
    ctx.new_path()                                                    # 足もとの明かり
    ctx.save()
    ctx.translate(SING_X, cy + SING_FY - 4)
    ctx.scale(1.0, 0.18)
    ctx.arc(0, 0, 150, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(1.0, 0.98, 0.82, 0.6)
    ctx.fill()
    wr = (27.0, -101.0 + 3 * math.sin(t * 5.0))
    person(ctx, sx, cy + SING_FY, SING_K, "you", t, wr=wr)
    wx, wy = sx + wr[0] * SING_K, cy + SING_FY + wr[1] * SING_K            # マイク
    ctx.new_path()
    ctx.move_to(wx + 2, wy + 4)
    ctx.line_to(wx + 8, wy - 18)
    _stroke(ctx, 7, "#444a5a", 1.0)
    ctx.new_path()
    ctx.arc(wx + 9, wy - 24, 9, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#8d95a8"))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.9)
    for j in range(4):                                               # 音符
        ph = (t * 0.55 + j * 0.25) % 1.0
        nx = sx + 110 + j * 38 + 12 * math.sin(t * 3 + j * 2)
        ny = cy + 300 - ph * 170
        note_icon(ctx, nx, ny, 17, (RED, FC, LC, "#3d7a5a")[j], math.sin(math.pi * ph) * 0.95)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def shuffled_nums(t):
    """くじ引きの間は番号札が入れ替わり、決まると 1〜16 の順に並ぶ"""
    u = t - (T_R1 + 0.35)
    if 0 <= u < 1.4:
        step = int(u / 0.14)
        return [int(v) + 1 for v in np.random.default_rng(100 + step).permutation(16)]
    return list(range(1, 17))


# ---------- 各場面の中身（舞台の床の部分） ----------
def content_a(ctx, cy, t, a):
    """冒頭〜研究①: 歌う人と、袖で出番を待つ16人"""
    ctx.push_group()
    draw_singer(ctx, cy, t)
    lineup(ctx, cy, shuffled_nums(t), t)
    text(ctx, "出番待ち", 770, cy + 400, 28, INK, alpha=0.9)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_b(ctx, cy, t, a):
    """研究②: 12年分・576人（3日×16人×12年）の点"""
    ctx.push_group()
    u = t - T_R2
    text(ctx, "出典: Antipov & Pokryshevskaya（2017）", 540, cy + 223, 26, PENCIL, bold=False, alpha=clamp01((u - 0.9) / 0.4))
    n = int(576 * ease(clamp01((u - 0.3) / 1.7)))
    cols, rows = 36, 16
    for k_ in range(n):
        r_, c_ = divmod(k_, cols)
        bust(ctx, 540 + (c_ - (cols - 1) / 2) * 21.0, cy + 306 + r_ * 20.0, 19, None, k_ * 7 + r_)
    p = ease_out(clamp01((u - 1.2) / 0.4))
    text(ctx, "12年分", 330, cy + 262, 46, FC_D, alpha=p)
    text(ctx, "576人", 750, cy + 262, 46, LC_D, alpha=p)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_c(ctx, cy, t, a):
    """研究の結果: 出番が後ろの人ほど順位が少し上（階段）"""
    ctx.push_group()
    u = t - T_R3
    for i in range(16):
        p = ease_out(clamp01((u - 0.2 - 0.07 * i) / 0.25))
        if p <= 0:
            continue
        yc = cy + 560 - i * 15.5 + 14 * (1 - p)
        bust(ctx, 540 + (i - 7.5) * 57.0, yc, 70, (1 if i == 0 else None), i, a=p)
    p2 = ease_out(clamp01((u - 1.4) / 0.9))
    note.pen_line(ctx, 130, cy + 495, 940, cy + 262, RED, seed=33, width=8, progress=p2, alpha=0.9)
    text(ctx, "順位が上がる", 640, cy + 255, 40, RED, alpha=p2)
    text(ctx, "出番が前", 250, cy + 618, 34, INK, alpha=clamp01((u - 0.5) / 0.3))
    text(ctx, "出番が後ろ", 820, cy + 618, 34, INK, alpha=clamp01((u - 0.5) / 0.3))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_d(ctx, cy, t, a):
    """比べ方: 実力は全員同じ（同じ高さの棒）・ちがうのは出番（番号）だけ"""
    ctx.push_group()
    u = t - T_R4
    tb = CARDS["c4b"][1] - T_R4
    dim = 0.65 * ss(tb, tb + 0.3, u)                                  # 後半は番号に注目
    nums = list(range(1, 17))
    for i in range(16):
        x = 556 + (i - 7.5) * 44.0
        g = ease_out(clamp01((u - 0.3 - 0.03 * i) / 0.3))
        bust(ctx, x, cy + 318, 46, None, i, a=g, tint=dim)
        h_ = 118.0 * g
        rrect(ctx, x - 14, cy + 372 + 118 - h_, 28, max(h_, 1), 5)
        ctx.set_source_rgba(*hexrgb("#f4c242", 0.95 * (1 - 0.6 * dim)))
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.85 * (1 - 0.6 * dim))
        rrect(ctx, x - 17, cy + 528, 34, 32, 5)
        ctx.set_source_rgba(1, 1, 1, 0.97)
        ctx.fill_preserve()
        _stroke(ctx, 2.0, RED if dim > 0 else INK, 0.9)
        text(ctx, str(nums[i]), x, cy + 545, 24, RED if dim > 0.3 else INK, alpha=g)
    pl = clamp01((u - 1.2) / 0.5)
    if pl > 0:
        note.pen_line(ctx, 190, cy + 372, 925, cy + 372, RED, seed=12, width=5, progress=pl, alpha=0.85 * (1 - dim))
    text(ctx, "実力", 172, cy + 440, 30, FC_D, alpha=ease_out(clamp01((u - 0.6) / 0.3)))
    text(ctx, "出番", 172, cy + 545, 30, RED, alpha=ease_out(clamp01((u - 0.6) / 0.3)))
    if dim > 0:
        note.pen_circle(ctx, 556, cy + 545, 400, 32, RED, seed=88, width=6, progress=clamp01((u - tb - 0.1) / 0.5), alpha=1.0)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


SAMPLE_PEOPLE = (("最初に歌った人", 260.0, ("#e0801f", "#a85a0a", "#3a3a48"), "#4a3322", FC),
                 ("3番目に歌った人", 540.0, ("#7a4fa0", "#5a3a7a", "#3a3a48"), "#2c2c34", GOLD_D),
                 ("最後に歌った人", 800.0, ("#3f7fb5", "#2a5a85", "#3a3a48"), "#8a5a2b", LC))


def content_e(ctx, cy, t, a):
    """見本の1回: 最初の人4位・最後の人6位・優勝は3番目の人"""
    ctx.push_group()
    u = t - T_S0
    S = sample()
    ranks = (S["first_rank"], S["winner_pos"] and 1, S["last_rank"])
    reveal = (SAMPLE_T["r1"], SAMPLE_T["r3"], SAMPLE_T["r2"])
    for (nm, x, jk, hr, col), rk, rv in zip(SAMPLE_PEOPLE, ranks, reveal):
        g = ease_out(clamp01((u - 0.1) / 0.4))
        person(ctx, x, cy + 535, 2.3, "host", t, jk=jk, hr=hr, tie_col=col)
        text(ctx, nm, x, cy + 592, 32, col if col != GOLD_D else INK, alpha=ease_out(clamp01((u - SAMPLE_T["names"]) / 0.3)))
        if u >= rv:
            pr = ease_out(clamp01((u - rv) / 0.3))
            by = cy + 245 - 14 * (1 - pr)
            if rk == 1:
                trophy(ctx, x - 60, by + 4, 118, t)
                text(ctx, "優勝", x + 62, by, 58, RED, alpha=pr)
            else:
                ctx.new_path()
                ctx.arc(x, by, 46, 0, 2 * math.pi)
                ctx.set_source_rgba(*hexrgb(col, 0.97 * pr))
                ctx.fill_preserve()
                _stroke(ctx, 4, INK, 0.9 * pr)
                text(ctx, f"{rk}位", x, by, 52, "#ffffff", alpha=pr)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_g(ctx, cy, t, a):
    """理由: あとで聞いた歌ほど、審査の点に少し上乗せ（計算での見立て）"""
    ctx.push_group()
    u = t - T_RS
    ramp = [i / (N_SING - 1) for i in range(N_SING)]
    base = cy + 572.0
    hmax = 255.0
    prog = clamp01((u - 0.3) / 2.6) * N_SING
    for i in range(N_SING):
        x = 195 + i * 46.0
        f = clamp01(prog - i)
        h_ = max(6.0, hmax * ramp[i]) * f
        c0, c1 = hexrgb(FC), hexrgb(LC)
        cc = tuple(c0[k_] + (c1[k_] - c0[k_]) * ramp[i] for k_ in range(3))
        rrect(ctx, x - 17, base - h_, 34, h_ + 0.01, 5)
        ctx.set_source_rgba(cc[0], cc[1], cc[2], 0.95 * f)
        ctx.fill_preserve()
        _stroke(ctx, 2.6, INK, 0.85 * f)
    k_ = min(N_SING - 1, int(prog))
    if prog < N_SING:
        note_icon(ctx, 195 + k_ * 46.0, base - max(6.0, hmax * ramp[k_]) - 32, 19, RED, 0.95)
    text(ctx, "最初", 195, base + 34, 32, FC_D)
    text(ctx, "最後", 885, base + 34, 32, LC_D)
    text(ctx, "点に足される分", 540, cy + 250, 44, INK, alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    text(ctx, "計算での見立て（1つ後ろごとに同じだけ上がる）", 540, cy + 292, 26, PENCIL, bold=False, alpha=ease_out(clamp01((u - 1.0) / 0.4)))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def content_i(ctx, cy, t, a):
    """締め: 袖の16人と、どこに入るか考えるあなた"""
    ctx.push_group()
    u = t - T_Q
    draw_singer(ctx, cy, t)
    seq = [0, 15, 7, 3, 11, 5, 12, 1]
    k_ = int(max(0.0, u - 0.5) / 0.6) % len(seq)
    pr = clamp01(((max(0.0, u - 0.5)) % 0.6) / 0.25)
    lineup(ctx, cy, list(range(1, 17)), t, hl=seq[k_] if u >= 0.5 else None, hlprog=pr)
    text(ctx, "？", 700, cy + 320 + 6 * math.sin(t * 4), 130, RED, alpha=ease_out(clamp01((u - 0.2) / 0.3)))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def win_alpha(t, s0, s1):
    return ss(s0 - 0.05, s0 + 0.3, t) * (1 - ss(s1, s1 + 0.3, t))


def panel_alpha(t):
    a = 0.0
    for s0, s1 in ((-1.0, T_H0), (T_R3, T_TW), (T_Q, DURATION + 1)):
        a = max(a, win_alpha(t, s0, s1))
    return a


def cy_of(t):
    return lerp(CY_INTRO, CY_FINAL, INTRO.moved(t))


def draw_panel_scene(ctx, t):
    a = panel_alpha(t)
    if a <= 0:
        return
    cy = cy_of(t)
    ctx.push_group()
    ctx.save()
    z = 1.0 + 0.05 * (1 - ease(clamp01(t / 1.1)))                    # 冒頭だけ、場面が寄ったところから引く（文字は拡大しない）
    if z > 1.0:
        ctx.translate(540, cy + 330)
        ctx.scale(z, z)
        ctx.translate(-540, -(cy + 330))
    draw_hall(ctx, cy, t)
    ctx.save()
    rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
    ctx.clip()
    for fn, s0, s1 in ((content_a, -1.0, T_R2), (content_b, T_R2, T_R4), (content_d, T_R4, T_S0),
                       (content_e, T_S0, T_H0), (content_c, T_R3, T_RS), (content_g, T_RS, T_TW), (content_i, T_Q, DURATION + 1)):
        ca = win_alpha(t, s0, s1)
        if ca > 0:
            fn(ctx, cy, t, ca)
    ctx.restore()
    d_ = 0.55 * (1 - ss(0.0, 0.9, t))                                # 冒頭: 暗い舞台に明かりがつく
    if d_ > 0:
        ctx.save()
        rrect(ctx, 60, cy - 35, 960, STAGE_H, 24)
        ctx.set_source_rgba(0.08, 0.07, 0.16, d_)
        ctx.fill()
        ctx.restore()
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def bottom_card(ctx, t, key, size=40, color="yellow", fg=INK, y=1385.0, x=565.0):
    s_, ta, tb = CARDS[key]
    al = win(t, ta, tb, 0.25, 0.25)
    if al > 0:
        note.sticky(ctx, s_, x, y, size, color, fg=fg, a=al, tilt=-0.015)


# ---------- 絵: 1万回の優勝の棒・答え ----------
HBASE = 1180.0
HSC = 0.33


def draw_hist_scene(ctx, t):
    a = clamp01((t - T_H0) / 0.4) * (1 - clamp01((t - T_R3) / 0.3))
    if a <= 0:
        return
    r = results()
    ctx.push_group()
    text(ctx, "1万回やって、優勝した回数", 580, 688, 46, INK)
    p = ease(clamp01((t - T_HC) / CNT))
    n = int(p * N_TRIAL)
    vf = int(r["cum_f"][n - 1]) if n > 0 else 0
    vl = int(r["cum_l"][n - 1]) if n > 0 else 0
    if t < T_REV - 0.2:
        text(ctx, f"{n:,}回目", 580, HBASE + 112, 36, PENCIL, bold=False)
    for cx, v, col, dcol, lab in ((290.0, vf, FC, FC_D, "最初に歌った人"), (700.0, vl, LC, LC_D, "最後に歌った人")):
        hgt = v * HSC
        rrect(ctx, cx - 120, HBASE - 420, 240, 420, 14)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.fill_preserve()
        _stroke(ctx, 2.2, PENCIL, 0.5)
        if hgt > 1:
            rrect(ctx, cx - 120, HBASE - hgt, 240, hgt, 14)
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.fill_preserve()
            _stroke(ctx, 3.4, INK, 0.9)
        text(ctx, f"{v:,}回", cx, HBASE - max(hgt, 0) - 48, 72, dcol)
        text(ctx, lab, cx, HBASE + 48, 40, dcol)
    if t >= T_REV:
        pr = ease_out(clamp01((t - T_REV) / 0.5))
        note.pen_circle(ctx, 700, HBASE - r["wl"] * HSC - 48, 190, 62, RED, seed=61, width=7, progress=pr)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 絵: ひねり ----------
def draw_twist(ctx, t):
    a = clamp01((t - T_TW) / 0.3) * (1 - clamp01((t - T_Q) / 0.35))
    if a <= 0:
        return
    r = results()
    u = t - T_TW
    ctx.push_group()
    text(ctx, "1万回で、最初の人と最後の人を比べると", 580, 688, 36, INK)
    bx0, bw, by, bh = 130.0, 810.0, 810.0, 112.0
    fa = r["first_above"] / N_TRIAL
    seg1 = bw * fa                                                    # 最初の人が上だった回
    seg2 = bw - seg1
    f = ease_out(clamp01((u - 0.2) / 0.6))
    for (x0_, wd, col, dcol, num, lab) in ((bx0, seg1, FC, FC_D, r["first_above"], "最初の人が上"),
                                           (bx0 + seg1, seg2, LC, LC_D, r["last_above"], "最後の人が上")):
        rrect(ctx, x0_, by, wd * f, bh, 10)
        ctx.set_source_rgba(*hexrgb(col, 0.95))
        ctx.fill_preserve()
        _stroke(ctx, 3.4, INK, 0.9)
        text(ctx, f"{num:,}回", x0_ + wd / 2, by + bh / 2, 46, "#ffffff", alpha=f)
        text(ctx, lab, x0_ + wd / 2, by + bh + 52, 34, dcol, alpha=ease_out(clamp01((u - 0.7) / 0.35)))
    pb = ease_out(clamp01((u - 1.4) / 0.5))
    if pb > 0:
        note.pen_circle(ctx, bx0 + seg1 / 2, by + bh / 2, seg1 / 2 + 22, bh / 2 + 24, RED, seed=93, width=7, progress=pb)
        text(ctx, "約3回に1回", bx0 + seg1 / 2 + 40, by - 64, 54, RED, alpha=pb)
    # 2枚目: 出番の効き目 と その日の出来の差（棒の長さ）
    u2 = t - T_TWB
    if u2 > -0.1:
        g = ease_out(clamp01((u2 + 0.1) / 0.5))
        b_ = r["b"]
        L = 600.0
        text(ctx, "出番の効き目", 150, 1040, 40, RED, align="left", alpha=g)
        text(ctx, "その日の出来の差", 150, 1160, 40, INK, align="left", alpha=g)
        for yy, ln, col, seed in ((1092.0, b_ * L, RED, 51), (1212.0, 1.0 * L, "#3d7a5a", 52)):
            ww = ln * ease_out(clamp01((u2 - 0.3) / 0.8))
            rrect(ctx, 150, yy - 22, max(ww, 1), 44, 8)
            ctx.set_source_rgba(*hexrgb(col, 0.92 * g))
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, 0.85 * g)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


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
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q)


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
        for line, y in zip(BIG_Q, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q[-1], sz)
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
        if t >= self.T_CD[0]:                                           # 予想して！と 3・2・1（舞台の床の右）
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = 790.0, CY_INTRO + 300.0
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
    draw_hist_scene(ctx, t)
    draw_twist(ctx, t)
    for key in CARDS:
        if key == "ans":
            bottom_card(ctx, t, key, 52, fg=RED)
        elif key == "q":
            bottom_card(ctx, t, key, 48)
        elif key == "a1":
            bottom_card(ctx, t, key, 40, y=1360.0)
        else:
            bottom_card(ctx, t, key, 40, color="pink" if key == "tw2" else "yellow", fg=RED if key == "tw2" else INK)


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
    mx.add(T_R1 + 0.4, blip(520, 0.06), 0.3)                           # くじ
    mx.add(T_R1 + 1.8, bell(659.3, 0.8), 0.3)
    mx.add(T_R2 + 0.4, riser(0.8), 0.3)                                # 576人
    mx.add(T_R2 + 2.0, bell(784.0, 0.8), 0.3)
    mx.add(T_R3 + 0.3, bell(698.5, 0.8), 0.35)                         # 後ろほど上
    mx.add(T_R3 + 1.5, blip(660, 0.08), 0.35)
    mx.add(T_R4 + 0.4, bell(659.3, 0.8), 0.3)                          # 実力は同じ
    mx.add(CARDS["c4b"][1] + 0.1, blip(880, 0.08), 0.35)               # ちがうのは出番
    mx.add(T_S0 + 0.4, bell(784.0, 0.6), 0.25)
    for k_ in ("r1", "r2"):
        mx.add(T_S0 + SAMPLE_T[k_], blip(660, 0.08), 0.35)
    mx.add(T_S0 + SAMPLE_T["r3"], bell(1046.5, 1.0), 0.45)
    mx.add(T_H0 - 0.5, riser(0.8), 0.4)                                # 1万回
    beat(mx, T_HC, T_HC + CNT, bpm=132, vol=0.5, accel=True)
    mx.add(T_HC + CNT, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(CARDS["a1"][1] + 0.1, bell(698.5, 0.8), 0.3)
    mx.add(T_RS + 0.4, bell(698.5, 0.8), 0.35)
    mx.add(T_TW, riser(0.6), 0.35)                                     # ひねり
    mx.add(T_TW + 1.5, thump(), 0.4)
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


def run_checks():
    r = results()
    S = sample()
    rc = recount()
    mj = json.loads(MODEL_JSON.read_text(encoding="utf-8"))["newwave"]
    checks = []
    # (1) 条件・数え直し
    checks.append(("回数 = 1万", float(len(r["rank"])), float(N_TRIAL), 0.0))
    checks.append(("1回の出場者 = 16人", float(r["rank"].shape[1]), 16.0, 0.0))
    checks.append(("優勝: 最初の人 数え直し(argmax) = junban_model.sim", float(rc["win_first"]), float(r["wf"]), 0.0))
    checks.append(("優勝: 最後の人 数え直し(argmax) = junban_model.sim", float(rc["win_last"]), float(r["wl"]), 0.0))
    checks.append(("最後の人が上の回 数え直し(点の比較) = junban_model.sim", float(rc["last_above"]), float(r["last_above"]), 0.0))
    checks.append(("優勝: 最初の人 = out/models_1120/junban.json（294回）", float(r["wf"]), float(mj["win_first"]), 0.0))
    checks.append(("優勝: 最後の人 = out/models_1120/junban.json（1,095回）", float(r["wl"]), float(mj["win_last"]), 0.0))
    checks.append(("最後の人が上の回 = out/models_1120/junban.json（6,766回）", float(r["last_above"]), float(mj["last_above_first"]), 0.0))
    checks.append(("画面: 294回・1,095回・6,766回・3,234回", float((r["wf"], r["wl"], r["last_above"], r["first_above"]) == (294, 1095, 6766, 3234)), 1.0, 0.0))
    checks.append(("札の数字 294・1,095 が結果と同じ", float(f"{r['wf']}回" in CARD_TEXT["a1"] and f"{r['wl']:,}回" in CARD_TEXT["a1"]), 1.0, 0.0))
    checks.append(("研究の相関に合わせた効き目 b で、相関 ≒ 0.188（許容 0.01）", float(r["summ"]["corr"]), 0.188, 0.01))
    checks.append(("効き目 b < 実力のばらつき 1（標準偏差）= 「その日の出来の差ほど大きくない」の棒の根拠", float(r["b"] < 1.0), 1.0, 0.0))
    checks.append(("ひねり: 最初の人が上の回 ≒ 3回に1回（許容 2ポイント）", r["first_above"] / N_TRIAL, 1 / 3, 0.02))
    checks.append(("576人 = 36×16（点の数）= 12年×3日×16人", float(36 * 16 == 576 == 12 * 3 * 16), 1.0, 0.0))
    # (2) 答え
    key, d = answer_by_rule(r["wf"] / N_TRIAL, r["wl"] / N_TRIAL)
    checks.append(("規則の答え = 最後", float(key == "最後"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号の並び: 最初・ほぼ同じ・最後 の順", float(LABELS == ["最初", "ほぼ同じ", "最後"]), 1.0, 0.0))
    checks.append(("答えの札は 中立（正解は『最後』。）", float(CARD_TEXT["ans"] == "正解は『最後』。"), 1.0, 0.0))
    for dd, k_ in ((0.0, "ほぼ同じ"), (0.019, "ほぼ同じ"), (0.021, "最後"), (-0.021, "最初")):
        checks.append((f"規則の道具: 差 {dd:+.3f} → {k_}", float(answer_by_rule(0.1, 0.1 + dd)[0] == k_), 1.0, 0.0))
    # (3) 見本は1万回の最初の1回そのもの
    checks.append(("見本: 最初の人4位・最後の人6位・優勝は3番目（junban.json の sample）",
                   float((S["first_rank"], S["last_rank"], S["winner_pos"]) == (mj["sample"]["first_rank"], mj["sample"]["last_rank"], mj["sample"]["winner_pos"]) == (4, 6, 3)), 1.0, 0.0))
    checks.append(("見本: 数え直し(点から順位) の1回目と 同じ", float((rc["first_rank0"], rc["last_rank0"], rc["winner0"]) == (S["first_rank"], S["last_rank"], S["winner_pos"])), 1.0, 0.0))
    checks.append(("見本: 16人の順位が 1〜16 を1回ずつ", float(sorted(S["ranks"]) == list(range(1, 17))), 1.0, 0.0))
    checks.append(("見本: 最初の人のほうが上（4位 < 6位）= 札「この回は、最初の人のほうが上だった」", float(S["first_rank"] < S["last_rank"]), 1.0, 0.0))
    # (4) 問い（3行）が収まる
    s3 = min(big3_size(840.0), 108.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 840px 以内", float(max(core.text_width(l, s3) for l in BIG_Q) <= 840.5), 1.0, 0.0))
    checks.append(("問い3行: 横幅いっぱい近く（いちばん長い行 700px 以上）", float(max(core.text_width(l, s3) for l in BIG_Q) >= 700), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(450 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行の文: 「歌の発表会。16人。／出る順番を選べるなら、／最初？最後？」",
                   float(BIG_Q == ["歌の発表会。16人。", "出る順番を選べるなら、", "最初？最後？"]), 1.0, 0.0))
    # (5) 札の読める長さ・場面の長さ
    for s_, ta, tb in cards():
        n_ = len(s_.replace("\n", ""))
        nd = max(0.12 * n_ + 1.0, 0.5 + max(len(x) for x in s_.split("\n")) / 6.0)
        checks.append((f"札「{s_.replace(chr(10), '')}」が読み切れる（{tb - ta:.2f}秒 / 要る {nd:.2f}秒）", float(tb - ta >= nd - 1e-9), 1.0, 0.0))
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    ordered = sorted(CARDS.values(), key=lambda c: c[1])
    checks.append(("札どうしが重ならない（同じ場所に2枚出ない）", float(all(ordered[i][2] <= ordered[i + 1][1] + 1e-9 for i in range(len(ordered) - 1))), 1.0, 0.0))
    checks.append(("台本の順: 札の出る順が 台本どおり", float([k_ for k_, _ in sorted(CARDS.items(), key=lambda kv: kv[1][1])]
                                                   == ["c1", "c2", "c4a", "c4b", "s0", "s1", "ans", "a1", "c3", "rs", "tw1", "tw2", "q"]), 1.0, 0.0))
    checks.append(("結果が見える時間: 1万回の数え上げのあと 答えまで 1.0秒以上", float(T_REV - (T_HC + CNT) >= 1.0), 1.0, 0.0))
    checks.append(("長さ 50〜58.9秒（lint は60秒未満）", float(50.0 <= DURATION <= 58.9), 1.0, 0.0))
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
    S = sample()
    print(f"長さ {DURATION:.1f}秒  研究 {T_R1:.1f}/{T_R2:.1f}/{T_R3:.1f}  比べ方 {T_R4:.1f}  見本 {T_S0:.1f}-{T_H0:.1f}  1万回 {T_H0:.1f}  答え {T_REV:.1f}  理由 {T_RS:.1f}  ひねり {T_TW:.1f}/{T_TWB:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  優勝: 最初の人 {r['wf']:,}回・最後の人 {r['wl']:,}回  答え: {r['key']}（差 {r['d']:+.3f}）  最後が上 {r['last_above']:,}回 / 最初が上 {r['first_above']:,}回")
    print(f"  見本: 最初の人{S['first_rank']}位  最後の人{S['last_rank']}位  優勝は{S['winner_pos']}番目の人")
    print(f"  問い3行の文字 {min(big3_size(840.0), 108.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(840.0), 108.0)) for l in BIG_Q):.0f}px")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


def stills_all():
    from PIL import Image
    ts = [0.0, 0.4, 1.0, 2.2,
          T_R1 + 1.0, T_R1 + 2.6, T_R2 + 2.5, T_R3 + 2.6, T_R4 + 1.8, T_R4 + 4.6,
          T_S0 + 1.5, T_S0 + SAMPLE_T["r1"] + 0.8, T_S0 + SAMPLE_T["r2"] + 0.8, T_S0 + SAMPLE_T["r3"] + 0.9, T_S0 + SAMPLE_T["card"] + 1.5,
          T_HC + 1.0, T_REV + 1.2, T_REV + 4.5,
          T_RS + 1.2, T_RS + 3.6, T_TW + 2.4, T_TWB + 2.0, T_Q + 1.8]
    stills(draw, ts, OUT)
    for old in OUT.glob("w480_*.png"):
        old.unlink()
    paths = sorted(OUT.glob("still_*.png"))
    for p in paths:
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
