"""1週目の7本で、どの回もコピーしていた部品をまとめたもの（2026-09-26、制作役の要望から）。

- choices    … 三択の札。答えの発表で正解が金色に光り、ほかは暗くなる
- loop_back  … 最後の0.5秒で、冒頭のコマそのものにクロスフェードする（ループの継ぎ目）
- grid_image … 1万回モードのマス目。色の配列を渡すと cairo の画像を返す（1万個の四角を毎フレーム描かない）
- legend     … 色の見本と説明を中央にそろえて並べる
- pct / r1   … 表示用の四捨五入（%の整数、小数1桁）。種を選ぶときの照合にも使う
- check_true … 「A>Bである」のような真偽の照合
- stills     … 要所の静止画と、その一覧画像（sheet.png）をまとめて書き出す
- cache_dir  … 重い計算の置き場（out/<slug>/cache/。git には入らない）
"""
import math
from pathlib import Path

import cairo
import numpy as np

from engine.core import FONT, W, clamp01, fill, hexrgb, rrect, still, text

NAVY = "#0e1120"
GOLD = "#ffd166"


def pct(x):
    """0.634 → 63（%の整数。四捨五入は0.5を切り上げ）"""
    return int(math.floor(x * 100 + 0.5))


def r1(x):
    """11.42 → 11.4（小数1桁。0.05を切り上げ）"""
    return math.floor(x * 10 + 0.5) / 10


def choices(ctx, t, labels, correct, reveal_t, y=350, size=44, key_size=34,
            widths=None, gap=30, reveal_dur=0.4, colors=None):
    """三択（2択・4択も可）の札を描く。

    labels   … ["100%", "63%", "50%"] のような中身。A/B/C は自動で付く
    correct  … 正解の番号（0始まり）
    reveal_t … 発表の時刻。これ以降、正解が金色に光り、ほかは暗くなる
    widths   … 札の幅のリスト（文言が長い回用）。省略時は画面幅に均等
    colors   … (札の地の色, 記号の色)。省略時は紺と金
    """
    n = len(labels)
    if widths is None:
        widths = [(W - 2 * 105 - gap * (n - 1)) / n] * n
    total = sum(widths) + gap * (n - 1)
    x = (W - total) / 2
    base, keyc = colors or ((0.17, 0.2, 0.36), GOLD)
    rev = clamp01((t - reveal_t) / reveal_dur) if reveal_t is not None else 0.0
    h = size + 28
    for i, (lab, w) in enumerate(zip(labels, widths)):
        ok = i == correct
        if rev > 0 and ok:
            fill(ctx, (1, 0.82, 0.4, 0.3 + 0.7 * rev))
        else:
            fill(ctx, (*base, 1 - 0.5 * rev))
        rrect(ctx, x, y - h / 2, w, h, 16)
        ctx.fill()
        dark = rev > 0.5 and ok
        a = 1 - 0.6 * rev * (not ok)
        text(ctx, "ABCD"[i], x + 40, y, key_size, NAVY if dark else keyc, alpha=a)
        text(ctx, lab, x + 40 + (w - 40) / 2, y, size, NAVY if dark else "#ffffff", alpha=a)
        x += w + gap


def loop_back(ctx, t, duration, draw_first, fade=0.5):
    """最後の fade 秒で、冒頭のコマ（draw_first(ctx, 0)）へクロスフェードする。draw の最後で呼ぶ"""
    if t <= duration - fade:
        return
    a = clamp01((t - (duration - fade)) / fade)
    a = a * a * (3 - 2 * a)
    ctx.push_group()
    draw_first(ctx, 0.0)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def bgra(color):
    c = hexrgb(color) if isinstance(color, str) else color
    a = c[3] if len(c) > 3 else 1.0
    return [int(c[2] * 255 * a), int(c[1] * 255 * a), int(c[0] * 255 * a), int(255 * a)]


def grid_image(colors, cell=8, gap_color=NAVY, gap=1, round_cells=False):
    """1万回モードのマス目を numpy で塗って cairo の画像にする。

    colors … (行, 列, 4) の uint8 BGRA 配列（`bgra("#ffd166")` で1色ぶんが作れる）
    返り値 … (surface, 配列)。配列は surface が生きている間は捨てないこと
    使い方: surf, _keep = grid_image(c); ctx.set_source_surface(surf, x, y); ctx.paint()
    """
    rows, cols = colors.shape[:2]
    big = np.repeat(np.repeat(colors, cell, 0), cell, 1)
    if gap:
        g = bgra(gap_color)
        big[cell - gap::cell, :, :] = g
        big[:, cell - gap::cell, :] = g
    if round_cells and cell >= 5:
        g = bgra(gap_color)
        for dy, dx in ((0, 0), (0, cell - gap - 1), (cell - gap - 1, 0), (cell - gap - 1, cell - gap - 1)):
            big[dy::cell, dx::cell, :] = g
    big = np.ascontiguousarray(big)
    surf = cairo.ImageSurface.create_for_data(memoryview(big), cairo.FORMAT_ARGB32,
                                              cols * cell, rows * cell, cols * cell * 4)
    return surf, big


def legend(ctx, items, y, size=30, color="#8d99c9", gap=60, cx=W / 2):
    """items = [(色, "説明"), ...] を中央にそろえて1行に並べる"""
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ws = [size + 12 + ctx.text_extents(lab).x_advance for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        fill(ctx, col)
        rrect(ctx, x, y - size * 0.45, size * 0.9, size * 0.9, 5)
        ctx.fill()
        text(ctx, lab, x + size + 12, y, size, color, align="left", bold=False)
        x += w + gap


def check_true(name, cond, detail=""):
    """真偽の照合を check_answers に渡す形にする: check_answers([... , check_true(...)])"""
    print(f"  条件の照合 {'OK' if cond else 'NG'}: {name} {detail}")
    return (name, 1.0 if cond else 0.0, 1.0, 0.0)


def stills(draw, times, out_dir, cols=6, thumb=(270, 480)):
    """要所の静止画を書き出し、一覧（sheet.png）も作る。目で確かめるのは sheet.png から"""
    from PIL import Image
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("still_*.png"):   # 時刻を変えたときに古い静止画が残らないように
        old.unlink()
    paths = []
    for tt in times:
        p = out_dir / f"still_{tt:05.1f}.png"
        still(draw, tt, p)
        paths.append(p)
    ims = [Image.open(p).convert("RGB").resize(thumb) for p in paths]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (thumb[0] + 8), (i // cols) * (thumb[1] + 8)))
    sheet.save(out_dir / "sheet.png")
    print("一覧:", out_dir / "sheet.png")
    return paths


def cache_dir(slug):
    """重い計算（数値積分など）の置き場。out/ の下なので公開されない"""
    p = Path(__file__).resolve().parents[1] / "out" / slug / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p
