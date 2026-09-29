"""30人で席替え。誰も元の席に戻らない確率は？

直感の外れ: 「30人もいれば誰か戻る → 1%くらい」（A）。正解は完全順列 D30/30! ≈ 1/e ≈ 37%（B）。
1クラス目は2人が元の席に戻る、2クラス目は全員が新しい席 → 1万クラスが一斉に席替え
（1番の席から順に確かめ、誰かが戻ったクラスから消えていく）→ 37%が残る
→ 追い打ち: 戻る人は平均ちょうど1人（1人あたり 1/30 × 30人）。

2026-09-28 ノートの見た目に変更（engine/note.py。janken-10nin で視聴を継続が 9〜15% → 25% に上がった形）。
冒頭8秒は問題の画面。右上では机3つで席替えが動いている（ユーザー「1コマ目に席替えしている感じを動かして見せたい」）。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.parts import loop_back, stills
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, shimmer,
                         still, text, thump, tick, whoosh, _t)

note.use()
note.DATE = "9.29"                                # 日付欄（公開予定日）

SLUG = "sekigae-30nin"
N, M = 10000, 30
SUB = PENCIL
# この回の差し色: 黒板の緑・机の木・緑（全員移動）・赤（元の席に戻った）
BOARD, BOARD_EDGE, CHALK = "#2e5e4e", "#6b4f35", "#e6efe6"
DESK, DESK_NUM, KID, KID_NUM = "#c9a06a", "#3a2a1a", "#ffffff", INK
MINT, CORAL = "#2fae78", "#e5484d"
PEND, FAILC = "#7d93c8", "#e2dccd"     # 1万クラス: 確かめ中＝青、誰かが戻った＝紙に近い灰色で消える
K1, K2 = "#3a9fd6", "#9b72e8"          # 2段目: 1人戻った / 2人戻った


def derange(n):
    """n人の完全順列の確率 D_n / n! = Σ_{k=0}^{n} (-1)^k / k!"""
    return sum((-1) ** k / math.factorial(k) for k in range(n + 1))


def p_fixed(k):
    """ちょうど k 人が元の席に戻る確率"""
    return derange(M - k) / math.factorial(k)


EXACT0, EXACT1, EXACT2 = p_fixed(0), p_fixed(1), p_fixed(2)
EXACT3P = 1 - EXACT0 - EXACT1 - EXACT2
EXACT_MEAN = 1.0                      # 1人あたり 1/30 × 30人（線形性。何人のクラスでも1）


def pct(x):
    return int(math.floor(x * 100 + 0.5))


# 乱数の種: 表示する%（四捨五入）と平均（小数2桁）が理論値と一致するものを選ぶ。統計は1万クラス全部から出す
IDX = np.arange(M)
for SEED in range(1, 5000):
    rng = np.random.default_rng(SEED)
    PERM = np.argsort(rng.random((N, M)), axis=1)     # PERM[c, 席] = その席に座った人の番号
    FIX = PERM == IDX
    F = FIX.sum(1)
    S = [(F == 0).mean(), (F == 1).mean(), (F == 2).mean(), (F >= 3).mean()]
    MEAN = F.mean()
    if all(pct(a) == pct(b) for a, b in zip(S, (EXACT0, EXACT1, EXACT2, EXACT3P))) \
            and pct(1 - S[0]) == pct(1 - EXACT0) and f"{MEAN:.2f}" == f"{EXACT_MEAN:.2f}":
        break
SIM0, SIM1, SIM2, SIM3P = S
FIRST = np.where(FIX.any(1), FIX.argmax(1) + 1, M + 1)    # 何番の席で初めて「戻った人」が出たか


def _spread(c):
    s = np.flatnonzero(FIX[c])
    return len(s) == 2 and s[0] // 6 != s[1] // 6 and abs(s[0] % 6 - s[1] % 6) >= 2


CLASS_A = next(c for c in range(N) if _spread(c))      # 見本1: 2人が戻る
CLASS_B = next(c for c in range(N) if F[c] == 0)       # 見本2: 全員が新しい席

# ---------- 時間割 ----------
# 2026-09-26 テンポの直し（ユーザー指摘「最初の2回で企画を理解できるか」「冒頭の1人目にもう少し時間を」）:
#   ・1クラス目は問題を読む時間を兼ねる。最初の0.9秒は全員が自分の番号の机でソワソワ（0秒目から動いている）、
#     そこから約3秒かけてゆっくり席を移る。ルールを1行出す
#   ・2クラス目は対比なので速いまま。札と合図は「0.5秒＋文字数÷6秒」以上出す（engine/pace.py で測る）
SH_DUR, SH_SPREAD = 1.1, 0.35
_drng = np.random.default_rng(7)
DELAY = _drng.uniform(0, SH_SPREAD, M)
DELAY[[0, 7, 14, 21, 28]] = 0.0
SH_DUR_A, SH_SPREAD_A = 1.8, 1.2       # 1クラス目はゆっくり、ばらばらに立って移る
DELAY_A = DELAY * (SH_SPREAD_A / SH_SPREAD)
T_A0 = note.Intro.T_GO                # 冒頭の問題画面（約8秒）のあと
T_A_SH = T_A0 + 0.9
T_A_GLOW = T_A_SH + SH_DUR_A + SH_SPREAD_A + 0.1
T_B0 = T_A_GLOW + 2.3
T_B_SH = T_B0 + 0.3
T_B_GLOW = T_B_SH + SH_DUR + SH_SPREAD + 0.1
T_BANNER = T_B_GLOW + 2.4
T_M0 = T_BANNER + 2.1                  # 1万クラスモード開始（合図は9文字なので2.1秒）
STEP = 60 / 128 / 2                    # 1席ずつ、ハイハットの刻みに合わせて確かめる
T_DONE = T_M0 + M * STEP               # 30番の席まで確かめ終わる
T_REV = T_DONE + 0.8
T_P2 = T_DONE + 3.9                    # 追い打ち「戻る人は平均何人？」
T_SW = T_P2 + 1.9
T_SW_END = T_SW + 1.4
T_MEAN = T_SW_END + 0.4
DURATION = T_MEAN + 4.2


def step_at(t):
    if t < T_M0:
        return 0
    return min(M, 1 + int((t - T_M0) / STEP))


# ---------- 描画 ----------
GX, GY, CS = 190, 470, 7               # 1万クラスのマス（100×100、1マス7px）。下の文字を 1,450px より上に収めるため8→7
ROW_Y = [590 + 150 * r for r in range(5)]


def seat_xy(j):
    return 540 + (j % 6 - 2.5) * 126, ROW_Y[j // 6]    # 126: 右端の列が右のボタン列（x>930）にかからない幅


# 冒頭の右上: 机3つで席替えがずっと続いている（1コマ目から「席替えの話だ」と分かるように）
MINI_X, MINI_Y = [615, 785, 955], 300
MINI_PERMS = [(1, 2, 0), (2, 0, 1), (1, 0, 2), (0, 2, 1), (2, 1, 0), (1, 2, 0)]   # 席 → 座る人
MINI_IV, MINI_HOP = 1.3, 0.6


def mini_state(t):
    """その時刻に各人がどこにいるか（x, y）と、自分の番号の机にいるか"""
    tt = t + 0.35                                   # 0秒目は跳んでいる途中
    k = int(tt // MINI_IV)
    u = clamp01((tt - k * MINI_IV) / MINI_HOP)
    prev = MINI_PERMS[k % len(MINI_PERMS)]
    nxt = MINI_PERMS[(k + 1) % len(MINI_PERMS)]
    where_prev = {kid: seat for seat, kid in enumerate(prev)}
    where_next = {kid: seat for seat, kid in enumerate(nxt)}
    out = []
    for kid in range(3):
        a, b = where_prev[kid], where_next[kid]
        p = ease(u)
        x = MINI_X[a] + (MINI_X[b] - MINI_X[a]) * p
        y = MINI_Y - 60 * math.sin(math.pi * p) * (a != b)
        out.append((x, y, u >= 1 and b == kid))
    return out


def draw_deco(ctx, t, a):
    for j, x in enumerate(MINI_X):
        fill(ctx, (*hexrgb(DESK)[:3], a))
        rrect(ctx, x - 62, MINI_Y + 26, 124, 58, 10)
        ctx.fill()
        text(ctx, str(j + 1), x, MINI_Y + 55, 32, DESK_NUM, alpha=a)
    for kid, (x, y, home) in enumerate(mini_state(t)):
        if home:                                    # 自分の番号の机に戻ったら赤く光る
            fill(ctx, (*hexrgb(CORAL)[:3], 0.8 * a))
            ctx.arc(x, y - 12, 52, 0, 2 * math.pi)
            ctx.fill()
        fill(ctx, (*hexrgb(KID)[:3], a))
        ctx.arc(x, y - 12, 43, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(3)
        ctx.stroke()
        text(ctx, str(kid + 1), x, y - 12, 40, KID_NUM, alpha=a)


INTRO = note.Intro(["30人で席替え。", "誰も元の席に戻らない確率は？"], ["1%", f"{pct(EXACT0)}%", "50%"],
                   correct=1, msg="1万クラスで確かめる", deco=draw_deco,
                   big=["30人で席替え。", "誰も元の席に", "戻らない確率は？"],
                   rule=["机の番号 ＝ その人の元の席", "同じ番号に座ったら → 戻った"])


def draw_board(ctx, label, a=1.0):
    fill(ctx, (*hexrgb(BOARD_EDGE)[:3], a))
    rrect(ctx, 200, 426, 680, 74, 12)
    ctx.fill()
    fill(ctx, (*hexrgb(BOARD)[:3], a))
    rrect(ctx, 208, 432, 664, 62, 8)
    ctx.fill()
    text(ctx, label, 540, 463, 34, CHALK, alpha=a)


def draw_class(ctx, t, c, t_sh, t_glow, label, fade=1.0, dur=SH_DUR, delay=DELAY, rule_a=None):
    """教室。t_sh から席替えが始まり、t_glow で「元の席に戻った人」の席が光る。
    dur・delay は1人が移る時間と立ち上がりのずれ。rule_a はルールの1行の明るさ（1＝白）"""
    draw_board(ctx, label, fade)
    inv = np.argsort(PERM[c])                       # inv[人] = その人の新しい席
    glow = ease_out((t - t_glow) / 0.3) if t >= t_glow else 0.0
    n_fix = int(F[c])
    # 机
    for j in range(M):
        x, y = seat_xy(j)
        fixed = FIX[c, j]
        col = CORAL if (fixed and glow > 0) else DESK
        fill(ctx, (*hexrgb(col)[:3], fade))
        rrect(ctx, x - 56, y + 22, 112, 54, 10)
        ctx.fill()
        text(ctx, str(j + 1), x, y + 49, 28, DESK_NUM, alpha=fade)
    # 人（動いている子を上に描く）
    order = sorted(range(M), key=lambda s: 0 < clamp01((t - t_sh - delay[s]) / dur) < 1)
    for s in order:
        p = ease(clamp01((t - t_sh - delay[s]) / dur))
        x0, y0 = seat_xy(s)
        x1, y1 = seat_xy(int(inv[s]))
        x = x0 + (x1 - x0) * p
        y = y0 + (y1 - y0) * p - 70 * math.sin(math.pi * p)
        if t < t_sh + delay[s]:                     # 立つ前はその場でソワソワ（止まった画面にしない）
            y -= 9 * abs(math.sin(math.pi * (t * 2.2 + s * 0.37)))
        fixed = int(inv[s]) == s
        if glow > 0 and (fixed or n_fix == 0):
            ring = CORAL if fixed else MINT
            fill(ctx, (*hexrgb(ring)[:3], 0.35 * glow * fade))
            ctx.arc(x, y - 12, 62, 0, 2 * math.pi)
            ctx.fill()
            fill(ctx, (*hexrgb(ring)[:3], glow * fade))
            ctx.arc(x, y - 12, 52, 0, 2 * math.pi)
            ctx.fill()
        fill(ctx, (*hexrgb(KID)[:3], fade))
        ctx.arc(x, y - 12, 44, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.75 * fade))
        ctx.set_line_width(3)
        ctx.stroke()
        text(ctx, str(s + 1), x, y - 12, 38, KID_NUM, alpha=fade)
    # 結果
    if t < t_glow:
        if t >= t_sh:
            text(ctx, "席替え中…", 540, 1320, 48, SUB, alpha=fade)
    else:
        a = ease_out((t - t_glow) / 0.25) * fade
        if n_fix:
            note.sticky(ctx, f"{n_fix}人が元の席に…", 540, 1320, 56, "pink", fg=RED, a=a)
        else:
            note.sticky(ctx, "全員 新しい席！", 540, 1320, 56, "mint", a=a, tilt=0.02)
    if rule_a is not None:
        if rule_a >= 1:
            text(ctx, RULE, 540, 1415, 38, INK, alpha=fade)
        else:
            text(ctx, RULE, 540, 1415, 38, SUB, bold=False, alpha=fade)


RULE = "机の番号＝元の席　同じ番号に戻ると赤"


def _bgra(h):
    c = hexrgb(h)
    return [int(c[2] * 255), int(c[1] * 255), int(c[0] * 255), 255]


def grid_surface(t):
    """1万クラスのマスを numpy で塗って cairo の画像にする"""
    k, kp = step_at(t), step_at(t - 1 / FPS)
    col = np.empty((N, 4), np.uint8)
    col[:] = _bgra(PEND)
    failed = FIRST <= k
    col[failed] = _bgra(FAILC)
    col[failed & (FIRST > kp)] = _bgra(CORAL)             # 戻った瞬間だけ赤く光る
    if t >= T_DONE:
        surv = FIRST > M
        col[surv] = _bgra(MARKER) if t < T_DONE + 0.1 else _bgra(MINT)
    if t >= T_SW:
        rows = int(100 * ease(clamp01((t - T_SW) / (T_SW_END - T_SW))))
        sel = np.arange(N) < rows * 100
        for val, h in ((1, K1), (2, K2)):
            col[sel & (F == val)] = _bgra(h)
        col[sel & (F >= 3)] = _bgra(CORAL)
        edge = sel & (np.arange(N) >= max(0, rows - 3) * 100)
        col[edge & (F > 0)] = _bgra(MARKER)
    col = col.reshape(100, 100, 4)
    big = np.repeat(np.repeat(col, CS, 0), CS, 1)
    big[CS - 1::CS, :, :] = _bgra(PAPER)
    big[:, CS - 1::CS, :] = _bgra(PAPER)
    big = np.ascontiguousarray(big)
    surf = cairo.ImageSurface.create_for_data(memoryview(big), cairo.FORMAT_ARGB32,
                                              100 * CS, 100 * CS, 100 * CS * 4)
    return surf, big


def draw_legend(ctx, a):
    items = [("0人", SIM0, MINT), ("1人", SIM1, K1), ("2人", SIM2, K2), ("3人〜", SIM3P, CORAL)]
    for i, (lab, v, colr) in enumerate(items):
        x = 140 + i * 200
        fill(ctx, (1, 1, 1, 0.75 * a))
        rrect(ctx, x, 1205, 180, 110, 12)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.5 * a))
        ctx.set_line_width(2)
        ctx.stroke()
        fill(ctx, (*hexrgb(colr)[:3], a))
        rrect(ctx, x + 18, 1222, 26, 26, 6)
        ctx.fill()
        text(ctx, lab, x + 56, 1235, 36, INK, align="left", alpha=a)
        text(ctx, f"{pct(v)}%", x + 90, 1282, 42, colr, alpha=a)
    text(ctx, "元の席に戻った人数（1マス＝1クラス）", 540, 1370, 38, INK, alpha=a)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）

    if t < T_A0:
        pass
    elif t < T_B0:
        fo = ease_out((t - T_A0) / 0.25) * (1 - ease((t - (T_B0 - 0.25)) / 0.25))
        draw_class(ctx, t, CLASS_A, T_A_SH, T_A_GLOW, "1クラス目", fade=fo, dur=SH_DUR_A,
                   delay=DELAY_A, rule_a=1)
    elif t < T_BANNER:
        fi = ease((t - T_B0) / 0.25) * (1 - ease((t - (T_BANNER - 0.2)) / 0.2))
        draw_class(ctx, t, CLASS_B, T_B_SH, T_B_GLOW, "2クラス目", fade=fi, rule_a=0)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        note.banner(ctx, "1万クラスで席替え", 540, 820, a=a, t_rel=t - T_BANNER)
    else:
        surf, _keep = grid_surface(t)
        ctx.set_source_surface(surf, GX, GY)
        ctx.paint()
        k = step_at(t)
        lg = ease((t - T_SW_END) / 0.4)
        if lg < 1:
            n_ok = int((FIRST > k).sum())
            text(ctx, f"{k}番の席まで確かめた", 540, 1230, 52, INK, alpha=1 - lg)
            text(ctx, f"誰も戻っていないクラス {n_ok / N * 100:.0f}%", 540, 1305, 42, MINT,
                 alpha=1 - lg)
            text(ctx, "1マス＝1クラス　消えたら誰かが戻った", 540, 1375, 38, INK,
                 alpha=1 - lg)
        if lg > 0:
            draw_legend(ctx, lg)
        if T_DONE <= t < T_P2 + 0.3:
            a = ease_out((t - T_DONE - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
            note.sticky(ctx, f"誰も元の席に\n戻らない {pct(SIM0)}%", 540, 820, 70, "yellow", a=a)
        if T_P2 <= t < T_SW + 0.3:
            a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_SW) / 0.3))
            note.banner(ctx, "戻る人は平均何人？", 540, 820, a=a, t_rel=t - T_P2)
        if t >= T_MEAN:
            a = ease_out((t - T_MEAN) / 0.3)
            note.sticky(ctx, f"戻る人は\n平均 {MEAN:.2f}人", 540, 770, 72, "yellow", fg=RED, a=a)
            b = ease_out((t - T_MEAN - 0.9) / 0.3)
            note.sticky(ctx, "1人あたり 1/30 × 30人", 540, 980, 40, "blue", a=b, tilt=0.02)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)    # 最後の0.5秒で冒頭の画面に戻す（ループ）


# ---------- 音 ----------

def boing(dur=0.5):
    """元の席に戻っちゃった音（下がる2音）"""
    t = _t(dur)
    f = np.where(t < dur / 2, 520, 390)
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * np.exp(-(t % (dur / 2)) * 9) * 0.8


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    for k in range(10):                       # 冒頭の机3つ: 着地ごとに小さくトン
        tl = k * MINI_IV - 0.35 + MINI_HOP
        if 0 <= tl < INTRO.T_MOVE:
            mx.add(tl, tick(900, 0.04), 0.35)
    for t_sh, t_glow, c, dur, dl in ((T_A_SH, T_A_GLOW, CLASS_A, SH_DUR_A, DELAY_A),
                                     (T_B_SH, T_B_GLOW, CLASS_B, SH_DUR, DELAY)):
        mx.add(t_sh, whoosh(1.3), 0.5)
        for s in range(M):
            mx.add(t_sh + dl[s] + dur, tick(700 + s * 25, 0.04), 0.35)
        if F[c]:
            mx.add(t_glow, boing(), 0.8)
            mx.add(t_glow + 0.25, boing(), 0.5)
        else:
            mx.add(t_glow, bell(1046.5), 0.7)
            mx.add(t_glow, shimmer(60), 0.8)
            mx.add(t_glow, chord([523.3, 659.3, 784], 1.2), 0.4)
    for i in range(3):                    # 立つ前のソワソワ
        mx.add(T_A0 + i * 0.3, tick(900 + i * 60, 0.05), 0.4)
    mx.add(T_BANNER, riser(0.9), 0.6)
    beat(mx, T_M0, T_DONE, bpm=128, vol=0.55)
    for k in range(1, M + 1):
        tt = T_M0 + (k - 1) * STEP
        new = int((FIRST == k).sum())
        mx.add(tt, blip(330 - k * 4, 0.1), min(0.6, new / 400))
    mx.add(T_DONE, shimmer(300, 0.5), 1.0)
    mx.add(T_DONE + 0.2, thump(), 0.8)
    mx.add(T_DONE + 0.2, bell(784), 0.6)
    mx.add(T_DONE + 0.2, chord([261.6, 329.6, 392], 1.8), 0.6)
    mx.add(T_P2, riser(0.8), 0.5)
    beat(mx, T_SW, T_SW_END, bpm=150, vol=0.45)
    for i in range(int((T_SW_END - T_SW) * FPS)):
        mx.add(T_SW + i / FPS, shimmer(40, seed=i), 0.4)
    mx.add(T_MEAN, thump(), 0.8)
    mx.add(T_MEAN, bell(1046.5), 0.6)
    mx.add(T_MEAN, chord([261.6, 329.6, 392, 523.3], 2.0), 0.6)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 1クラス目={CLASS_A}（{F[CLASS_A]}人戻る） 2クラス目={CLASS_B} "
          f"長さ={DURATION:.1f}秒")
    check_answers([
        ("誰も戻らない", SIM0, EXACT0, 0.015),
        ("ちょうど1人戻る", SIM1, EXACT1, 0.015),
        ("ちょうど2人戻る", SIM2, EXACT2, 0.015),
        ("3人以上戻る", SIM3P, EXACT3P, 0.015),
        ("戻る人数の平均", MEAN, EXACT_MEAN, 0.03),
    ])
    if "--stills" in sys.argv:
        stills(draw, [0.0, 0.3, 1.4, 3.2, 5.0, 7.95, T_A0 + 0.5, T_A_SH + 1.2, T_A_SH + 2.4, T_A_GLOW + 0.6, T_B_SH + 0.7,
                      T_B_GLOW + 0.6, T_BANNER + 0.5, T_M0 + 3.0, T_REV + 0.6, T_P2 + 0.8,
                      T_SW + 0.7, T_MEAN + 1.5, DURATION - 0.25], out)
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
