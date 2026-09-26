"""1%のガチャを100回引いたら、当たる人は何%？

直感の外れ: 1% × 100回 = 100%（A）。正解は 1 - 0.99^100 ≈ 63%（B）。
1人目は当たる、2人目は100回ぜんぶ外れる → 1万人が一斉に引く（100×100のマス）
→ 100回で37%が残る → 追い打ち: 200回でも13%は当たらない。
"""
import math
import sys
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.brand import mode_banner
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, pill, render, riser, rrect, shimmer,
                         still, text, thump, tick, _t)

SLUG = "gacha-1pct-100"
N, R = 10000, 200
P = 0.01
BG, OFF, MISS, HIT, LOSE, ACC, SUB = ("#0e1120", "#1c2342", "#39406a", "#ffd166", "#ff4d6d",
                                      "#ffd166", "#8d99c9")

EXACT100 = 1 - (1 - P) ** 100
EXACT200 = 1 - (1 - P) ** 200


def pct(x):
    return int(math.floor(x * 100 + 0.5))


# 乱数の種: 表示する%（四捨五入）が理論値の四捨五入と一致するものを選ぶ。答えの統計は全員ぶんで正直に出す
for SEED in range(1, 1000):
    rng = np.random.default_rng(SEED)
    FIRST = rng.geometric(P, size=N)          # 何回目で初めて当たったか
    s100, s200 = (FIRST <= 100).mean(), (FIRST <= 200).mean()
    if pct(s100) == pct(EXACT100) and pct(1 - s100) == pct(1 - EXACT100) \
            and pct(1 - s200) == pct(1 - EXACT200):
        break
SIM100, SIM200 = s100, s200
PERSON_A = int(np.argmax((FIRST >= 28) & (FIRST <= 42)))   # 見本1: 途中で当たる人
PERSON_B = int(np.argmax(FIRST > 150))                     # 見本2: 100回ぜんぶ外れる人

# ---------- 時間割 ----------
A_IV, B_IV = 0.075, 0.03
A_HIT = int(FIRST[PERSON_A])
T_A0 = 0.0
T_A_HIT = T_A0 + A_HIT * A_IV
T_B0 = T_A_HIT + 1.2
T_B_END = T_B0 + 100 * B_IV
T_BANNER = T_B_END + 1.4
T_M0 = T_BANNER + 0.9                 # 1万人モード開始
T_R100 = T_M0 + 7.0                   # 100回目
T_P2 = T_R100 + 3.4                   # 追い打ち「200回なら？」
T_P2_RUN = T_P2 + 0.8
T_R200 = T_P2_RUN + 2.6
DURATION = T_R200 + 3.2


def round_at(t):
    if t < T_M0:
        return 0
    if t < T_R100:
        p = (t - T_M0) / (T_R100 - T_M0)
        return int(100 * p ** 1.15)
    if t < T_P2_RUN:
        return 100
    return min(200, 100 + int(100 * clamp01((t - T_P2_RUN) / (T_R200 - T_P2_RUN))))


# ---------- 描画 ----------
BX, BY, TS = 190, 470, 70            # 1人ぶんの盤（10×10）
GX, GY, CS = 120, 470, 8             # 1万人のマス（100×100、1マス8px）


def star(ctx, cx, cy, r):
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        (ctx.move_to if i == 0 else ctx.line_to)(cx + rr * math.cos(a), cy + rr * math.sin(a))
    ctx.close_path()


def draw_title(ctx):
    text(ctx, "1%のガチャを100回。", 540, 150, 62)
    text(ctx, "当たる人は何%？", 540, 235, 76)


def draw_choices(ctx, t):
    labels = [("A", "100%"), ("B", f"{pct(EXACT100)}%"), ("C", "50%")]
    rev = clamp01((t - T_R100 - 0.8) / 0.4)
    for i, (k, v) in enumerate(labels):
        x, y, w, h = 105 + i * 300, 350, 270, 72
        correct = k == "B"
        if rev > 0 and correct:
            fill(ctx, (1, 0.82, 0.4, 0.3 + 0.7 * rev))
        else:
            fill(ctx, (0.17, 0.2, 0.36, 1 - 0.5 * rev))
        rrect(ctx, x, y - h / 2, w, h, 16)
        ctx.fill()
        dark = rev > 0.5 and correct
        a = 1 - 0.6 * rev * (not correct)
        text(ctx, k, x + 42, y, 34, BG if dark else ACC, alpha=a)
        text(ctx, v, x + 165, y, 44, BG if dark else "#ffffff", alpha=a)


def draw_board(ctx, t, first_hit, t0, iv, label, dim=1.0):
    k = min(100, 1 + int((t - t0) / iv)) if t >= t0 else 0   # 0秒目から1回目が出ている
    k = min(k, first_hit) if first_hit <= 100 else k
    text(ctx, label, 540, BY - 40, 34, SUB, bold=False, alpha=dim)
    for j in range(100):
        x = BX + (j % 10) * TS
        y = BY + (j // 10) * TS
        if j < k:
            is_hit = (j + 1) == first_hit
            fill(ctx, (*hexrgb(HIT)[:3], dim) if is_hit else (*hexrgb(MISS)[:3], dim))
            if not is_hit and first_hit > 100 and k >= 100:
                fill(ctx, (0.55, 0.2, 0.3, dim))
        else:
            fill(ctx, (*hexrgb(OFF)[:3], dim))
        rrect(ctx, x + 4, y + 4, TS - 8, TS - 8, 10)
        ctx.fill()
        if j < k and (j + 1) == first_hit:
            fill(ctx, (0.05, 0.07, 0.12, dim))
            star(ctx, x + TS / 2, y + TS / 2, 22)
            ctx.fill()
    return k


def grid_surface(r, flash_r):
    """1万人のマスを numpy で塗って cairo の画像にする（1万個の四角を毎フレーム描くと遅い）"""
    col = np.empty((100, 100, 4), np.uint8)
    hit = (FIRST <= r).reshape(100, 100)
    new = ((FIRST <= r) & (FIRST > flash_r)).reshape(100, 100)
    def bgra(h):
        c = hexrgb(h)
        return [int(c[2] * 255), int(c[1] * 255), int(c[0] * 255), 255]
    col[:] = bgra(MISS if r < 100 else LOSE)
    col[hit] = bgra(HIT)
    col[new] = [255, 255, 255, 255]
    big = np.repeat(np.repeat(col, CS, 0), CS, 1)
    big[CS - 1::CS, :, :] = bgra(BG)
    big[:, CS - 1::CS, :] = bgra(BG)
    big = np.ascontiguousarray(big)
    surf = cairo.ImageSurface.create_for_data(memoryview(big), cairo.FORMAT_ARGB32,
                                              100 * CS, 100 * CS, 100 * CS * 4)
    return surf, big


def draw(ctx, t):
    fill(ctx, BG)
    ctx.paint()
    draw_title(ctx)
    draw_choices(ctx, t)

    if t < T_B0:
        k = draw_board(ctx, t, A_HIT, T_A0, A_IV, "1人目")
        text(ctx, f"{k}回目", 540, 1250, 64)
        if t >= T_A_HIT:
            a = ease_out((t - T_A_HIT) / 0.25)
            pill(ctx, f"当たり！ {A_HIT}回目", 540, BY + 350, 60, HIT, fg=BG, a=a)
    elif t < T_BANNER:
        k = draw_board(ctx, t, int(FIRST[PERSON_B]), T_B0, B_IV, "2人目")
        text(ctx, f"{k}回目", 540, 1250, 64)
        if t >= T_B_END:
            a = ease_out((t - T_B_END) / 0.25)
            pill(ctx, "100回ぜんぶハズレ", 540, BY + 350, 60, LOSE, a=a)
    elif t < T_M0:
        a = ease_out((t - T_BANNER) / 0.25)
        mode_banner(ctx, "1万人で引く", 540, BY + 400, a=a, t_rel=t - T_BANNER)
    else:
        r = round_at(t)
        prev = round_at(t - 1 / FPS)
        surf, _keep = grid_surface(r, prev)
        ctx.set_source_surface(surf, GX, GY)
        ctx.paint()
        n_hit = int((FIRST <= r).sum())
        text(ctx, f"{r}回目", 330, 1345, 64)
        text(ctx, f"当たった人 {n_hit / N * 100:.0f}%", 700, 1345, 44, ACC)
        text(ctx, "1マス＝1人（1万人）", 540, 1435, 30, SUB, bold=False)
        if T_R100 <= t < T_P2 + 0.3:
            a = ease_out((t - T_R100 - 0.2) / 0.3) * (1 - ease((t - T_P2) / 0.3))
            pill(ctx, f"100回引いても\n{pct(1 - SIM100)}%は当たらない", 540, GY + 400, 66,
                 (0.08, 0.1, 0.2, 0.94), fg=LOSE, a=a)
        if T_P2 <= t < T_P2_RUN + 0.3:
            a = ease_out((t - T_P2) / 0.25) * (1 - ease((t - T_P2_RUN) / 0.3))
            mode_banner(ctx, "200回なら？", 540, GY + 400, a=a, t_rel=t - T_P2)
        if t >= T_R200:
            a = ease_out((t - T_R200 - 0.1) / 0.3)
            pill(ctx, f"200回でも\n{pct(1 - SIM200)}%は当たらない", 540, GY + 400, 66,
                 (0.08, 0.1, 0.2, 0.94), fg=LOSE, a=a)

    if t > DURATION - 0.5:
        a = ease((t - (DURATION - 0.5)) / 0.5)
        ctx.set_source_rgba(0.055, 0.067, 0.125, a)
        ctx.rectangle(0, 400, W, H - 400)
        ctx.fill()


# ---------- 音 ----------

def sad(dur=0.7):
    t = _t(dur)
    f = 440 * 2 ** (-t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / 48000) * np.exp(-t * 3) * 0.8


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION), 1.0)
    for j in range(A_HIT):
        mx.add(T_A0 + j * A_IV, tick(900 + j * 12, 0.05), 0.5)
    mx.add(T_A_HIT, bell(1046.5), 0.7)
    mx.add(T_A_HIT, shimmer(60), 0.8)
    mx.add(T_A_HIT, thump(), 0.5)
    for j in range(100):
        mx.add(T_B0 + j * B_IV, tick(900 + j * 6, 0.03), 0.35)
    mx.add(T_B_END, sad(), 0.7)
    mx.add(T_BANNER, riser(0.9), 0.6)
    beat(mx, T_M0, T_R100, bpm=128, vol=0.55, accel=True)
    prev = 0
    for i in range(int((T_R200 - T_M0) * FPS) + 1):
        tt = T_M0 + i / FPS
        r = round_at(tt)
        if r > prev:
            new = int(((FIRST <= r) & (FIRST > prev)).sum())
            mx.add(tt, shimmer(new, seed=i), 0.7)
            prev = r
    mx.add(T_R100 + 0.2, thump(), 0.8)
    mx.add(T_R100 + 0.2, chord([220, 261.6, 329.6], 1.6), 0.6)
    mx.add(T_P2, riser(0.8), 0.5)
    beat(mx, T_P2_RUN, T_R200, bpm=150, vol=0.45)
    mx.add(T_R200 + 0.1, thump(), 0.8)
    mx.add(T_R200 + 0.1, chord([220, 261.6, 329.6], 1.8), 0.6)
    return mx


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / SLUG
    out.mkdir(parents=True, exist_ok=True)
    print(f"seed={SEED} 1人目={A_HIT}回目で当たり 2人目={FIRST[PERSON_B]}回目 長さ={DURATION:.1f}秒")
    check_answers([
        ("100回で当たる割合", SIM100, EXACT100, 0.015),
        ("200回で当たる割合", SIM200, EXACT200, 0.015),
    ])
    if "--stills" in sys.argv:
        for tt in (0.0, T_A_HIT + 0.6, T_B_END + 0.7, T_M0 + 3.5, T_R100 + 1.5, T_R200 + 1.5):
            still(draw, tt, out / f"still_{tt:05.1f}.png")
    else:
        render(draw, DURATION, out / f"{SLUG}.mp4", build_audio())
        print("完成:", out / f"{SLUG}.mp4")
