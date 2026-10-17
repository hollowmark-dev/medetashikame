"""シャッフル再生、同じ歌手が続くのは偏ってる？ 1万回シャッフルして数える。— 2026-10-13 作成（公開予定 10/16）

モデル
  プレイリスト: 50曲（歌手10人×5曲ずつ）。歌手は色とひらがな1字だけ（あ・か・さ・た・な・は・ま・や・ら・わ）。
  本当のでたらめ: 50曲を一様にでたらめに並べる（どの並びも同じ確率。numpy の argsort で作る＝フィッシャー–イェーツと同じ分布）。
  でたらめっぽい並び（同じ歌手をばらす）: 歌手ごとに、5曲をリストの 1/5 おき（50曲なら10曲おき）に置く。
      はじめの位置は歌手ごとにでたらめ（0〜1/5 の一様）、1曲ずつ間隔の ±10% だけでたらめにずらし、位置の順に並べる。
      「同じ歌手の曲を間隔をあけて並べる」という考え方を、いちばん素直に式にしたもの（特定のアプリの実装ではない）。
  見るのは、再生する最初の20曲（となり合う組は19組）。

問い: 「シャッフル再生で同じ歌手が続く。これって偏ってる？」 A 偏ってる ／ B ときどき ／ C よくあること。
      答えは計算の前に決めた規則（answer_by_rule）: 本当のでたらめで「最初の20曲に同じ歌手が1回以上続く」割合 p が
      20% 未満なら A 偏ってる（でたらめならまず起きない＝よく続くなら偏っている）、20〜60% なら B ときどき、60% 以上なら C よくあること。
ひねり: でたらめっぽい並びは、11〜20曲目の歌手が「10曲前と同じ」になりやすい（2周目が読める）。
締め: 「歌手が何人いたら、続かないほうが多くなる？ → 答えは概要欄に」（1人5曲のまま。答えは厳密な計算で 23人）。

照合（check_answers）: run_checks を参照。理論値は、最初の20曲に続きが無い確率を厳密に数える動的計画法と、
  となり合う2曲が同じ歌手の確率 4/49 から出す。動的計画法そのものも、小さい例で全部の並びを数えた値と照らす。
"""
import functools
import math
import sys
from itertools import permutations
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, _t, SR)
from engine.parts import grid_image, bgra, loop_back, pct, stills, check_true  # noqa: E402

note.use()
note.DATE = "10.16"                               # 日付欄（公開予定日）

SLUG = "shuffle-saisei"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデル ----------
K_SINGER = 10
M_SONG = 5
N_SONG = K_SINGER * M_SONG
L_HEAD = 20                                       # 最初の20曲
N_RUN = 10000
JITTER = 0.10                                     # でたらめっぽい並びの、1曲ずつのずらし（間隔に対する割合）
SEED = 2                                          # 表示する%の丸めが理論値と同じになる種（下の照合で確かめる）
SEED_REF = 99                                     # 照合用（別の乱数で10万回）
ANS_LO, ANS_HI = 0.20, 0.60                       # 答えを決める規則のしきい値（計算する前に決めた）
LABELS = ["偏ってる", "ときどき", "よくあること"]
CORRECT = 2                                       # answer_by_rule で計算結果から決め、ずれたら止める

SINGER = np.repeat(np.arange(K_SINGER), M_SONG)   # 曲 → 歌手


def answer_by_rule(p):
    """p = 本当のでたらめで、最初の20曲に同じ歌手が1回以上続く割合"""
    if p < ANS_LO:
        return 0
    if p < ANS_HI:
        return 1
    return 2


def true_shuffle(rng, n, k=K_SINGER, m=M_SONG):
    singer = np.repeat(np.arange(k), m)
    return singer[np.argsort(rng.random((n, k * m)), axis=1)]


def spread_shuffle(rng, n, k=K_SINGER, m=M_SONG, jitter=JITTER):
    singer = np.repeat(np.arange(k), m)
    off = rng.random((n, k, 1))
    pos = (off + np.arange(m)[None, None, :]) / m + rng.uniform(-jitter, jitter, (n, k, m)) / m
    return singer[np.argsort(pos.reshape(n, k * m), axis=1)]


def measure(S):
    h = S[:, :L_HEAD]
    rep = (h[:, 1:] == h[:, :-1]).sum(1)                   # 最初の20曲で、となりが同じ歌手だった組の数
    m10 = (h[:, 10:20] == h[:, 0:10]).sum(1)               # 11〜20曲目のうち、10曲前と同じ歌手だった曲の数
    return rep, m10


def p_norep_exact(k, m, L):
    """k人×m曲を一様にでたらめに並べたとき、最初の L 曲に同じ歌手が続かない確率（厳密）。
    状態＝（直前の歌手以外の残り曲数の並び（順不同）, 直前の歌手の残り曲数）。次に歌手 j を引く確率は 残り_j / 残り全部"""
    @functools.lru_cache(None)
    def f(prof, last, steps):
        if steps == 0:
            return 1.0
        tot = sum(prof) + last
        r = 0.0
        prof_l = list(prof)
        for c in sorted(set(prof_l)):
            if c == 0:
                continue
            i = prof_l.index(c)
            nxt = prof_l.copy()
            nxt[i] = last
            r += prof_l.count(c) * c / tot * f(tuple(sorted(nxt)), c - 1, steps - 1)
        return r
    return f(tuple([m] * (k - 1)), m - 1, L - 1)


def p_norep_brute(k, m, L):
    """全部の並びを数える（小さい例だけ）"""
    s = list(np.repeat(np.arange(k), m))
    perms = set(permutations(s))
    ok = sum(1 for p in perms if all(p[i] != p[i + 1] for i in range(L - 1)))
    return ok / len(perms)


def singers_for_half():
    """1人5曲のまま歌手を増やして、最初の20曲に続きが無い確率が50%以上になる最小の人数"""
    k = K_SINGER
    while p_norep_exact(k, M_SONG, L_HEAD) < 0.5:
        k += 1
    return k


_D = None


def data():
    global _D
    if _D is not None:
        return _D
    rng = np.random.default_rng(SEED)
    TR = true_shuffle(rng, N_RUN)
    SP = spread_shuffle(rng, N_RUN)
    rep_t, m10_t = measure(TR)
    rep_s, m10_s = measure(SP)
    # 見本（見栄えのために選ぶ。統計は1万回すべてから）: 1回目は2回続く、2回目は続かない、3回目は1回
    def pick(cond, used):
        for i in np.nonzero(cond)[0]:
            if i not in used:
                return int(i)
        raise SystemExit("見本が見つからない")
    h = TR[:, :L_HEAD]
    cross_ok = h[:, 9] != h[:, 10]                         # 行の変わり目（10→11曲目）で続く見本は避ける（見やすさ）
    used = []
    for want in (2, 0, 1):
        used.append(pick((rep_t == want) & cross_ok, used))
    # ひねりの見本: でたらめは10曲前と同じが1曲、でたらめっぽいは5曲（平均に近いもの）
    tw = pick((m10_t == 1) & (m10_s == 5), used)
    # 1万回のマス目の並び: 見本の3回を先頭に（集計は並べ替えても変わらない）
    order = np.array(used + [i for i in range(N_RUN) if i not in used])
    k = singers_for_half()
    _D = dict(TR=TR, SP=SP, rep_t=rep_t, rep_s=rep_s, m10_t=m10_t, m10_s=m10_s, samples=used, tw=tw, order=order,
              p_t=float((rep_t > 0).mean()), p_s=float((rep_s > 0).mean()),
              mean_t=float(rep_t.mean()), mean_s=float(rep_s.mean()),
              m10_t_mean=float(m10_t.mean()), m10_s_mean=float(m10_s.mean()),
              exact_p=1 - p_norep_exact(K_SINGER, M_SONG, L_HEAD), exact_mean=(L_HEAD - 1) * (M_SONG - 1) / (N_SONG - 1),
              exact_m10=10 * (M_SONG - 1) / (N_SONG - 1), k_half=k,
              p_half_k=p_norep_exact(k, M_SONG, L_HEAD), p_half_km1=p_norep_exact(k - 1, M_SONG, L_HEAD))
    return _D


# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）。砂時計の回と同じ
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
BIG_Q = ["シャッフル再生で、同じ歌手が続く。", "これって偏ってる？"]
DETAIL = "50曲（歌手10人×5曲）。最初の20曲で数える"
DEAL1 = 0.10                                      # 見本1回目: 1曲ずつ配る間隔
DEAL2 = 0.045
T_S1 = T_GO + 0.35
T_S2 = T_S1 + L_HEAD * DEAL1 + 0.7
T_S3 = T_S2 + L_HEAD * DEAL2 + 0.35
T_BAN = T_S3 + L_HEAD * DEAL2 + 0.35              # 1万回の合図
T_K0 = T_BAN + 1.7                                # マス目が埋まりはじめる
T_K1 = T_K0 + 5.0
T_REV = T_K1 + 0.7                                # 答え
T_ST = T_REV + 0.4
T_TW = T_ST + 3.4                                 # ひねりの合図
T_TWC = T_TW + 0.3                                # ひねりの見本を配る
T_TWL = T_TW + 3.0                                # 10曲前と同じ列を囲む
T_TWB = T_TWL + 1.9                               # 1万回の平均の棒
T_TWS = T_TWB + 0.9                               # 付箋
T_Q = T_TWS + 2.9                                 # 締め
DURATION = T_Q + 4.2

# ---------- 歌手の色 ----------
KANA = "あかさたなはまやらわ"
COLS = ["#e9a87c", "#f4c36a", "#efe07a", "#b5dc7a", "#7fcf9b", "#79cdd0", "#8fbcec", "#a3a6e8", "#cda4e6", "#f1a9c8"]
HIT = "#e5646e"                                   # 1万回のマス目: 続いた
MISS = "#9cc3ea"                                  # 続かなかった

# ---------- 置き場所 ----------
CARD_W, CARD_H = 68, 80
PX0, PDX = 165.0, 80.0                            # 1枚目の中心・間隔（右端 919 ≦ 930）
PANELS = (615.0, 1000.0)                          # パネルの上端
ROW_DY = (85.0, 175.0)
GRID_COLS, GRID_ROWS, CELL = 200, 50, 4
GX0 = 120


def card(ctx, x, y, s, a=1.0, w=CARD_W, h=CARD_H, rot=0.0, lift=0.0):
    """曲のカード: 歌手の色の角丸に、ひらがな1字。lift は持ち上げた影"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    if rot:
        ctx.rotate(rot)
    if lift > 0:
        ctx.set_source_rgba(0.1, 0.1, 0.1, 0.13 * a * lift)
        core.rrect(ctx, -w / 2 + 5, -h / 2 + 8, w, h, 10)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(COLS[s], a))
    core.rrect(ctx, -w / 2, -h / 2, w, h, 10)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(2.6)
    ctx.stroke()
    # 小さな音符（ペン描き）
    ctx.set_source_rgba(*hexrgb(INK, 0.55 * a))
    nx, ny = w / 2 - 15, -h / 2 + 18
    ctx.arc(nx - 3, ny + 6, 3.2, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_line_width(1.6)
    ctx.move_to(nx, ny + 6)
    ctx.line_to(nx, ny - 6)
    ctx.line_to(nx + 5, ny - 3)
    ctx.stroke()
    text(ctx, KANA[s], 0, 4, h * 0.5, INK, alpha=a)
    ctx.restore()


# ---------- 冒頭: 50曲がずっとシャッフルされている ----------
CL_COLS, CL_ROWS = 10, 5
CL_X0, CL_X1 = 150.0, 872.0
CL_Y0, CL_Y1 = 760.0, 1360.0
CL_W, CL_H = 76, 96
HOP = 0.50                                        # 入れかえの周期
_CL = None


def cloud_plan():
    """冒頭のカードの動き: HOP 秒ごとに、となり合う2枚（左右・上下・ななめ）をでたらめに入れかえる。
    遠くへ飛ばすと全部のカードが真ん中を通って画面の端が空くので、近くどうしで入れかえて、画面いっぱいに散らばったまま動かす"""
    global _CL
    if _CL is None:
        rng = np.random.default_rng(5)
        n = CL_COLS * CL_ROWS
        slots = np.array([(CL_X0 + (CL_X1 - CL_X0) * (i % CL_COLS) / (CL_COLS - 1),
                           CL_Y0 + (CL_Y1 - CL_Y0) * (i // CL_COLS) / (CL_ROWS - 1)) for i in range(n)])
        steps = int(T_GO / HOP) + 4
        where = [rng.permutation(n)]                       # where[k][card] = 場所
        for k in range(steps):
            w = where[-1].copy()
            at = np.empty(n, int)
            at[w] = np.arange(n)                           # 場所 → カード
            dx, dy = [(1, 0), (0, 1), (1, 1), (1, -1)][rng.integers(4)]
            used = set()
            for s1 in rng.permutation(n):                  # でたらめな順に、まだ動かしていない隣と組む
                r, c = divmod(int(s1), CL_COLS)
                r2, c2 = r + dy, c + dx
                if not (0 <= r2 < CL_ROWS and 0 <= c2 < CL_COLS):
                    continue
                s2 = r2 * CL_COLS + c2
                if s1 in used or s2 in used or rng.random() < 0.1:
                    continue
                used |= {int(s1), s2}
                ca, cb = at[s1], at[s2]
                w[ca], w[cb] = s2, s1
            where.append(w)
        delay = rng.uniform(0, 0.16, n)
        sing = rng.permutation(SINGER)
        _CL = dict(slots=slots, where=where, delay=delay, sing=sing, bend=rng.choice([-1.0, 1.0], n) *
                   rng.uniform(0.6, 1.0, n), ph=rng.uniform(0, 2 * math.pi, n))
    return _CL


def cloud_pos(t):
    """各カードの (x, y, 回転, 持ち上げ)。t=0 は飛んでいる途中（0秒目から動く）"""
    c = cloud_plan()
    tt = t + HOP * 0.3
    k = int(tt // HOP)
    out = []
    for i in range(len(c["sing"])):
        u = clamp01((tt - k * HOP - c["delay"][i]) / 0.40)
        e = ease(u)
        a = c["slots"][c["where"][k][i]]
        b = c["slots"][c["where"][k + 1][i]]
        x = a[0] + (b[0] - a[0]) * e
        y = a[1] + (b[1] - a[1]) * e
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if d > 1:                                          # 弧を描いて入れかわる（ぶつからないよう横にふくらむ）
            bulge = math.sin(math.pi * e) * 0.45 * d * c["bend"][i]
            x += -(b[1] - a[1]) / d * bulge
            y += (b[0] - a[0]) / d * bulge
        x += 5 * math.sin(2 * math.pi * 0.9 * t + c["ph"][i])     # 止まっている間も少しゆれる
        y += 5 * math.cos(2 * math.pi * 0.7 * t + c["ph"][i])
        x = min(max(x, CL_X0 - 5), CL_X1)              # 右のボタン列（x>930）に字がかからないように
        y = min(max(y, CL_Y0 - 30), CL_Y1 + 20)
        lift = math.sin(math.pi * u) if d > 1 else 0.0
        out.append((x, y, 0.3 * lift * c["bend"][i] + 0.05 * math.sin(2 * math.pi * 0.6 * t + c["ph"][i]), lift))
    return out


def draw_cloud(ctx, t, a):
    if a <= 0:
        return
    c = cloud_plan()
    pos = cloud_pos(t)
    order = sorted(range(len(pos)), key=lambda i: pos[i][3])   # 飛んでいるカードを上に
    for i in order:
        x, y, rot, lift = pos[i]
        sc = 1 + 0.12 * lift
        card(ctx, x, y, int(c["sing"][i]), a, w=CL_W * sc, h=CL_H * sc, rot=rot, lift=lift)


def choice_row(labels, size, cx, max_w, gap=72):
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


CD_X, CD_Y = 580.0, 1060.0


class ShIntro(note.Intro):
    """問い2行・前提・三択（横1列）。その下いっぱいに、50曲のカードが0秒目からずっと入れかわる"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_cloud(ctx, t, a)
        sz = 60
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (408, 482)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 524, 575 + w2 / 2 + 6, 518, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 566, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 790, gap=40)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            fill(ctx, (*hexrgb(PAPER)[:3], 0.85 * a * show))
            core.rrect(ctx, x0 - 6, 594, 70 + core.text_width(v, vs), 66, 14)
            ctx.fill()
            note.pen_circle(ctx, x0 + 27, 628, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 628, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 628, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.93 * a2))
            core.rrect(ctx, cx - 140, cy - 166, 280, 76, 20)
            ctx.fill()
            note.hand_text(ctx, "予想して！", cx, cy - 128, 46, RED, seed=41, alpha=a2, align="center")
            fill(ctx, (*hexrgb(PAPER)[:3], 0.95 * a2))
            ctx.arc(cx, cy, 70, 0, 2 * math.pi)
            ctx.fill()
            note.pen_circle(ctx, cx, cy, 64, 62, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 96, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        sz = 44
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 850:
            sz *= 850 / w
        text(ctx, BIG_Q[0], 540, 400, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 452, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 483, 540 + w2 / 2 + 6, 480, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 536
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840, gap=48)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7, progress=rev)
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


INTRO = ShIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- シミュの間: 2つの並びを上下に並べてくらべる ----------

def slot_xy(p, k):
    """パネル p の k 曲目（0始まり）の位置。1〜10曲目が上の行、11〜20曲目が下の行"""
    return PX0 + (k % 10) * PDX, PANELS[p] + ROW_DY[k // 10]


def seq_of(p, idx):
    d = data()
    return (d["TR"] if p == 0 else d["SP"])[idx, :L_HEAD]


def deal_state(t):
    """いま配っている見本: (見本の番号 0..2, 配り始め, 間隔) か None"""
    if t < T_S1:
        return None
    if t < T_S2:
        return 0, T_S1, DEAL1
    if t < T_S3:
        return 1, T_S2, DEAL2
    return 2, T_S3, DEAL2


def draw_queue(ctx, p, seq, t0, step, t, a, mark_rep=True):
    """20曲を配る。となりが同じ歌手なら、2枚目が置かれたときに赤ペンで囲む。返り値: 置いた枚数・続いた数"""
    placed = 0
    reps = 0
    for k in range(L_HEAD):
        tk = t0 + k * step
        if t < tk:
            break
        g = ease_out((t - tk) / 0.16)
        x, y = slot_xy(p, k)
        card(ctx, x, y - 26 * (1 - g), int(seq[k]), a * g)
        placed += 1
    if mark_rep:
        for k in range(1, placed):
            if seq[k] == seq[k - 1]:
                reps += 1
                tk = t0 + k * step
                x0, y0 = slot_xy(p, k - 1)
                x1, y1 = slot_xy(p, k)
                prog = clamp01((t - tk - 0.05) / 0.25)
                note.pen_circle(ctx, (x0 + x1) / 2, (y0 + y1) / 2, 84, 50, RED, seed=60 + k, width=6,
                                progress=prog, alpha=a)
    return placed, reps


def readout(ctx, p, lab_l, val_l, lab_r, val_r, a, col_l=INK, col_r=INK):
    y0 = PANELS[p]
    text(ctx, lab_l, 120, y0 + 262, 28, PENCIL, align="left", bold=False, alpha=a)
    text(ctx, val_l, 120, y0 + 306, 42, col_l, align="left", alpha=a)
    if lab_r:
        text(ctx, lab_r, 470, y0 + 262, 28, PENCIL, align="left", bold=False, alpha=a)
        sz = 42
        w = core.text_width(val_r, sz)
        if w > 450:
            sz *= 450 / w
        text(ctx, val_r, 470, y0 + 306, sz, col_r, align="left", alpha=a)


def heading(ctx, p, a, sub_a=1.0):
    y0 = PANELS[p]
    head, sub = ("本当のでたらめ", "ふつうのシャッフル") if p == 0 else ("でたらめっぽい並び", "同じ歌手を ばらして並べる")
    w = core.text_width(head, 40)
    text(ctx, head, 120, y0 + 18, 40, INK, align="left", alpha=a)
    text(ctx, sub, 120 + w + 22, y0 + 22, 28, PENCIL, align="left", bold=False, alpha=a * sub_a)


_GRID = {}


def grid_surface(p, n):
    """1万回のマス目（n 回ぶんまで塗る）。左上から右へ。続いた＝赤、続かなかった＝水色"""
    key = (p, n)
    if key in _GRID:
        return _GRID[key]
    d = data()
    rep = (d["rep_t"] if p == 0 else d["rep_s"])[d["order"]]
    col = np.zeros((GRID_ROWS, GRID_COLS, 4), np.uint8)
    flat = col.reshape(-1, 4)
    flat[:] = bgra((0.93, 0.91, 0.86, 1.0))
    hit = rep[:n] > 0
    flat[:n][hit] = bgra(HIT)
    flat[:n][~hit] = bgra(MISS)
    if len(_GRID) > 8:
        _GRID.clear()
    _GRID[key] = grid_image(col, cell=CELL, gap_color=(0.97, 0.95, 0.9, 1.0), gap=1)
    return _GRID[key]


def n_done(t):
    """1万回モードで、t までにシャッフルし終えた回数（はじめはゆっくり、だんだん速く）"""
    if t < T_K0:
        return 3
    u = clamp01((t - T_K0) / (T_K1 - T_K0))
    return int(round(3 + (N_RUN - 3) * (0.25 * u + 0.75 * u ** 2.2)))


def draw_grid(ctx, p, n, a):
    surf, _keep = grid_surface(p, n)
    y = PANELS[p] + 40
    ctx.save()
    ctx.set_source_surface(surf, GX0, y)
    ctx.paint_with_alpha(a)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(GX0 - 2, y - 2, GRID_COLS * CELL + 4, GRID_ROWS * CELL + 4)
    ctx.stroke()


def fmt(n):
    return f"{int(n):,}"


def draw_sim(ctx, t):
    """T_GO から答えまで"""
    d = data()
    if t < T_GO - 0.1 or t >= T_TW + 0.35:
        return
    fade = 1 - ease((t - T_TW) / 0.35) if t >= T_TW else 1.0
    a = ease_out((t - T_GO + 0.1) / 0.4) * fade
    ds = deal_state(t)
    in_grid = t >= T_K0 - 0.3
    ga = ease((t - T_K0 + 0.3) / 0.3) if in_grid else 0.0
    for p in (0, 1):
        heading(ctx, p, a, 1 - ga)
        if ds is not None and ga < 1:
            si, t0, step = ds
            seq = seq_of(p, d["samples"][si])
            placed, reps = draw_queue(ctx, p, seq, t0, step, t, a * (1 - ga))
        else:
            placed, reps = 0, 0
        if ga > 0:
            draw_grid(ctx, p, n_done(t), a * ga)
        # 読み取り
        rep = d["rep_t"] if p == 0 else d["rep_s"]
        rep_o = rep[d["order"]]
        if not in_grid:
            done = (ds[0] + (1 if placed == L_HEAD else 0)) if ds is not None else 0
            k_hit = int((rep_o[:done] > 0).sum())
            v_l = f"この20曲で {reps}回"
            v_r = f"{done}回中 {k_hit}回" if done > 0 else "—"
        else:
            n = n_done(t)
            k_hit = int((rep_o[:n] > 0).sum())
            v_l = f"平均 {rep_o[:n].mean():.2f}回"
            v_r = f"{fmt(n)}回中 {fmt(k_hit)}回"
        readout(ctx, p, "同じ歌手が続いた", v_l, "1回以上続いた", v_r, a, col_l=RED if p == 0 else INK,
                col_r=RED if p == 0 else INK)
        if ga > 0:
            # マス目の色の見本（パネルの見出しの右）
            y = PANELS[p] + 18
            if p == 0:
                lx = 640
                for c, lab in ((HIT, "続いた"), (MISS, "続かない")):
                    fill(ctx, hexrgb(c, ga * a))
                    ctx.rectangle(lx, y - 13, 26, 26)
                    ctx.fill()
                    text(ctx, lab, lx + 34, y, 26, INK, align="left", bold=False, alpha=ga * a)
                    lx += 34 + core.text_width(lab, 26, bold=False) + 22
    # 1万回の合図
    if T_BAN <= t < T_K0 + 0.3:
        b = ease_out((t - T_BAN) / 0.25) * (1 - ease((t - T_K0) / 0.3))
        note.sticky(ctx, "1万回シャッフル", 580, 1395, 48, "yellow", a=b, tilt=-0.02)
    # 答えの付箋
    if t >= T_ST:
        b = ease_out((t - T_ST) / 0.3) * fade
        note.sticky(ctx, f"でたらめでも {pct(d['p_t'])}%は続く", 580, 1395, 44, "pink", fg=RED, a=b, tilt=-0.02)


# ---------- ひねり: 2周目が読める ----------

def draw_twist(ctx, t):
    if t < T_TW:
        return
    d = data()
    end = 1 - 0.75 * ease_out((t - T_Q) / 0.35) if t >= T_Q else 1.0
    a = ease_out((t - T_TW) / 0.35) * end
    idx = d["tw"]
    for p in (0, 1):
        heading(ctx, p, a)
        seq = seq_of(p, idx)
        draw_queue(ctx, p, seq, T_TWC, 0.03, t, a, mark_rep=False)
        # 10曲前と同じ歌手の列を、上下まとめて赤ペンで囲む
        hits = [k for k in range(10) if seq[k] == seq[k + 10]]
        for j, k in enumerate(hits):
            tk = T_TWL + j * 0.22
            if t < tk:
                break
            x, _ = slot_xy(p, k)
            yc = PANELS[p] + (ROW_DY[0] + ROW_DY[1]) / 2
            note.pen_circle(ctx, x, yc, 40, 98, RED, seed=80 + k + 10 * p, width=5,
                            progress=clamp01((t - tk) / 0.25), alpha=a)
        n_shown = sum(1 for j in range(len(hits)) if t >= T_TWL + j * 0.22)
        if t >= T_TWL:
            b = ease_out((t - T_TWL) / 0.3) * a
            y0 = PANELS[p]
            text(ctx, "11〜20曲目で、10曲前と同じ歌手", 120, y0 + 262, 30, PENCIL, align="left", bold=False, alpha=b)
            text(ctx, f"この回 {n_shown}曲", 120, y0 + 306, 42, RED, align="left", alpha=b)
        if t >= T_TWB:
            b = ease_out((t - T_TWB) / 0.3) * a
            mean = d["m10_t_mean"] if p == 0 else d["m10_s_mean"]
            y = PANELS[p] + 306
            x0, full = 430.0, 400.0                   # 10曲ぶんの長さ（2つのパネルで同じ目盛り）
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * b))
            ctx.set_line_width(2)
            ctx.set_dash([6, 6])
            ctx.rectangle(x0, y - 20, full, 40)
            ctx.stroke()
            ctx.set_dash([])
            text(ctx, "10曲", x0 + full, y - 36, 26, PENCIL, align="right", bold=False, alpha=b)
            grow = ease_out((t - T_TWB) / 0.6)
            wbar = full * mean / 10 * grow
            ctx.set_source_rgba(*hexrgb(HIT, 0.95 * b))
            core.rrect(ctx, x0, y - 20, max(wbar, 2), 40, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * b))
            ctx.set_line_width(2.5)
            ctx.stroke()
            text(ctx, f"1万回の平均 {mean * grow:.1f}曲", x0 + max(wbar, 2) + 12, y, 30, INK, align="left", alpha=b)
    if t >= T_TW and t < T_TWL + 0.2:
        b = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TWL) / 0.2))
        note.banner(ctx, "続かない並びは、でたらめ？", 580, 1395, a=b, t_rel=t - T_TW, size=46)
    if T_TWS <= t < T_Q + 0.35:
        b = ease_out((t - T_TWS) / 0.3) * (1 - ease_out((t - T_Q) / 0.35) if t >= T_Q else 1.0)
        note.sticky(ctx, "2周目が 読めてしまう", 580, 1395, 44, "yellow", fg=RED, a=b, tilt=0.02)


def draw_close(ctx, t):
    if t < T_Q:
        return
    q = ease_out((t - T_Q) / 0.35)
    note.sticky(ctx, "歌手が何人いたら、\n続かないほうが多くなる？", 580, 830, 48, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 1.3) / 0.3)
    note.sticky(ctx, "答えは概要欄に", 580, 1060, 48, "pink", fg=RED, a=r, tilt=0.025)
    if t >= T_Q + 1.9:
        text(ctx, "（いまは 10人×5曲）", 580, 1180, 32, PENCIL, bold=False, alpha=ease_out((t - T_Q - 1.9) / 0.3))


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    draw_sim(ctx, t)
    draw_twist(ctx, t)
    draw_close(ctx, t)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def flick(seed, dur=0.05):
    """カードをはじく音（短い紙の音）"""
    t = _t(dur)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(4) / 4, mode="same")
    return n * np.exp(-t * 120) * 0.5


def build_audio():
    d = data()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    # 冒頭: カードを切る音（入れかえのたびに、ぱらぱら）
    mx.add(0.0, whoosh(0.5), 0.25)
    k = 0
    t = -HOP * 0.55
    while t < T_MOVE:
        for j in range(5):
            tt = t + 0.03 + j * 0.035
            if 0 <= tt < T_MOVE:
                mx.add(tt, flick(k * 7 + j), 0.22)
        t += HOP
        k += 1
    INTRO.audio(mx)
    # 見本: 1枚配るごとにぱちっ、続いたらポン
    for si, (t0, step) in enumerate(((T_S1, DEAL1), (T_S2, DEAL2), (T_S3, DEAL2))):
        seq = seq_of(0, d["samples"][si])
        for kk in range(L_HEAD):
            mx.add(t0 + kk * step, flick(500 + si * 40 + kk), 0.35 if si == 0 else 0.2)
            if kk > 0 and seq[kk] == seq[kk - 1]:
                mx.add(t0 + kk * step + 0.05, blip(1046.5, 0.15), 0.5)
    # 1万回
    mx.add(T_BAN, riser(0.9), 0.45)
    beat(mx, T_K0, T_K1, bpm=128, vol=0.45, accel=True)
    mx.add(T_K1, bell(784.0, 1.2), 0.45)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST, blip(659.3, 0.15), 0.35)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.4)
    for kk in range(L_HEAD):
        mx.add(T_TWC + kk * 0.03, flick(900 + kk), 0.15)
    for p in (0, 1):
        seq = seq_of(p, d["tw"])
        hits = [k for k in range(10) if seq[k] == seq[k + 10]]
        for j in range(len(hits)):
            mx.add(T_TWL + j * 0.22, blip(880.0 + 60 * j if p else 660.0, 0.12), 0.35)
    mx.add(T_TWB, thump(), 0.5)
    mx.add(T_TWS, bell(1046.5, 1.3), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.3, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    d = data()
    checks = []
    # (1) 動的計画法の確かめ: 小さい例で、全部の並びを数えた値と一致する
    for k, m, L in ((3, 2, 6), (3, 2, 4), (2, 3, 5), (4, 2, 5)):
        checks.append((f"厳密計算と全数えが一致（{k}人×{m}曲・最初の{L}曲）", p_norep_exact(k, m, L), p_norep_brute(k, m, L), 1e-12))
    # (2) 本当のでたらめ: 1回以上続いた割合・続いた回数の平均・10曲前と同じ数の平均が理論値と合う
    checks.append(("でたらめ: 最初の20曲で1回以上続いた割合", d["p_t"], d["exact_p"], 0.012))
    checks.append(("でたらめ: 続いた回数の平均（理論 19×4/49）", d["mean_t"], d["exact_mean"], 0.04))
    checks.append(("でたらめ: 11〜20曲目で10曲前と同じ歌手の数（理論 10×4/49）", d["m10_t_mean"], d["exact_m10"], 0.03))
    checks.append(("でたらめ: 画面の%（四捨五入）が理論値と同じ", float(pct(d["p_t"])), float(pct(d["exact_p"])), 0.0))
    # (3) でたらめっぽい並び: 別の乱数で10万回と同じ（理論の閉じた式が無いので）
    ref = np.random.default_rng(SEED_REF)
    rep_r, m10_r = measure(spread_shuffle(ref, 100000))
    checks.append(("でたらめっぽい: 1回以上続いた割合（別の乱数10万回）", d["p_s"], float((rep_r > 0).mean()), 0.003))
    checks.append(("でたらめっぽい: 10曲前と同じ歌手の数（別の乱数10万回）", d["m10_s_mean"], float(m10_r.mean()), 0.06))
    checks.append(("でたらめっぽい: 画面の小数1桁が別の乱数と同じ", round(d["m10_s_mean"], 1), round(float(m10_r.mean()), 1), 0.0))
    checks.append(("でたらめ: 画面の小数1桁が理論値と同じ", round(d["m10_t_mean"], 1), round(d["exact_m10"], 1), 0.0))
    # (4) 締めの答え: 23人で50%を超え、22人では超えない（シミュでも確かめる）
    checks.append(check_true(f"締め: {d['k_half']}人で初めて続かない確率が50%以上",
                             d["p_half_k"] >= 0.5 > d["p_half_km1"], f"({d['p_half_km1']:.4f} → {d['p_half_k']:.4f})"))
    rep_k, _ = measure(true_shuffle(np.random.default_rng(7), 100000, k=d["k_half"]))
    checks.append((f"締め: {d['k_half']}人のときの続かない割合（シミュ10万回）", float((rep_k == 0).mean()), d["p_half_k"], 0.005))
    # (5) 答えは、決めておいた規則で計算結果から出したものと同じ
    checks.append(("画面の答え（三択の番号）が、決めておいた規則で計算結果から出した答えと同じ",
                   float(answer_by_rule(d["p_t"])), float(INTRO.correct), 0.0))
    checks.append(check_true("理論値でも同じ答え", answer_by_rule(d["exact_p"]) == INTRO.correct))
    check_answers(checks)


def report():
    d = data()
    print(f"長さ={DURATION:.1f}秒  見本 {d['samples']} ひねり {d['tw']}")
    print(f"でたらめ: 1回以上続く {d['p_t']:.4f}（理論 {d['exact_p']:.4f}）  平均 {d['mean_t']:.3f}回（理論 {d['exact_mean']:.4f}）"
          f"  10曲前と同じ {d['m10_t_mean']:.3f}（理論 {d['exact_m10']:.4f}）")
    print(f"でたらめっぽい: 1回以上続く {d['p_s']:.4f}  平均 {d['mean_s']:.4f}回  10曲前と同じ {d['m10_s_mean']:.3f}")
    print(f"締め: {d['k_half']}人で続かない確率 {d['p_half_k']:.4f}（{d['k_half'] - 1}人で {d['p_half_km1']:.4f}）")
    hist = np.bincount(d["rep_t"], minlength=8)[:8] / N_RUN
    print("でたらめの続いた回数の分布 0..7:", " ".join(f"{h:.3f}" for h in hist))
    print("10曲前と同じ（でたらめっぽい）の分布 0..10:", np.bincount(d["m10_s"], minlength=11) / N_RUN)
    for j in (0.2, 0.3, 0.5):
        r, m = measure(spread_shuffle(np.random.default_rng(11), 100000, jitter=j))
        print(f"  ずらし ±{j:.0%}: 1回以上続く {(r > 0).mean():.4f}  10曲前と同じ {m.mean():.3f}")
    for k in (10, 15, 20, 23):
        print(f"  歌手{k}人: 1回以上続く {1 - p_norep_exact(k, M_SONG, L_HEAD):.4f}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 1.0, 2.5, 5.0, 8.0, 8.6, T_S1 + 1.0, T_S1 + 2.3, T_S2 + 0.8, T_S3 + 0.9, T_BAN + 0.8,
              T_K0 + 1.5, T_K0 + 3.5, T_K1 + 0.3, T_REV + 0.6, T_ST + 1.5, T_TW + 1.0, T_TWL + 1.2, T_TWB + 0.8,
              T_TWS + 1.0, T_Q + 0.6, T_Q + 2.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
