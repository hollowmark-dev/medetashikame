"""チャンネル「めでたしかめ」の目印（亀）。

甲羅は、動画の「1万回モード」と同じマス目（当たり＝金、はずれ＝青）でできている。
アイコンにも動画の中にも同じ関数で描く。
"""
import math
import sys
from pathlib import Path

import cairo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import fill, hexrgb, rrect

NAVY = "#0e1120"
SHELL_A, SHELL_B, SHELL_EDGE = "#ffd166", "#4cc9f0", "#2b3566"
SKIN, SKIN_DARK = "#8fd694", "#5fae6b"


def turtle(ctx, cx, cy, s=1.0, blink=0.0):
    """亀を描く。(cx, cy) は甲羅の底辺の中央、s は倍率（s=1 で幅およそ360px）"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)

    # 足（甲羅の下から少し出る）
    fill(ctx, SKIN_DARK)
    for x in (-110, 70):
        rrect(ctx, x, -10, 50, 46, 18)
        ctx.fill()
    # しっぽ
    ctx.move_to(-150, -20)
    ctx.line_to(-190, -5)
    ctx.line_to(-150, 5)
    ctx.close_path()
    fill(ctx, SKIN_DARK)
    ctx.fill()

    # 頭（右に大きく出して、目を大きく。「目で確かめる」の目）
    fill(ctx, SKIN)
    ctx.arc(175, -70, 62, 0, 2 * math.pi)
    ctx.fill()
    rrect(ctx, 110, -60, 70, 55, 24)
    ctx.fill()
    # 目
    fill(ctx, "#ffffff")
    ctx.save()
    ctx.translate(192, -84)
    ctx.scale(1, max(0.08, 1 - blink))
    ctx.arc(0, 0, 30, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    if blink < 0.7:
        fill(ctx, NAVY)
        ctx.arc(200, -82, 16, 0, 2 * math.pi)
        ctx.fill()
        fill(ctx, "#ffffff")
        ctx.arc(206, -88, 5.5, 0, 2 * math.pi)
        ctx.fill()
    # 口
    ctx.set_line_width(5)
    ctx.set_source_rgba(*hexrgb(SKIN_DARK))
    ctx.arc(205, -50, 14, 0.2 * math.pi, 0.75 * math.pi)
    ctx.stroke()

    # 甲羅（半円のドーム。中はマス目）
    def dome():
        ctx.new_path()
        ctx.save()
        ctx.scale(1, 0.82)
        ctx.arc(0, 0, 160, math.pi, 2 * math.pi)
        ctx.restore()
        ctx.close_path()

    dome()
    fill(ctx, SHELL_EDGE)
    ctx.fill()
    ctx.save()
    dome()
    ctx.clip()
    cell = 26
    pattern = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    k = 0
    for row in range(6):
        for col in range(-7, 7):
            x = col * cell + 2
            y = -row * cell - cell + 2
            fill(ctx, SHELL_A if pattern[k % len(pattern)] else SHELL_B)
            rrect(ctx, x + 2, y + 2, cell - 6, cell - 6, 5)
            ctx.fill()
            k += 1
    ctx.restore()
    dome()
    ctx.set_line_width(10)
    ctx.set_source_rgba(*hexrgb(SHELL_EDGE))
    ctx.stroke()
    # 甲羅のふち
    fill(ctx, SHELL_EDGE)
    rrect(ctx, -172, -14, 344, 26, 13)
    ctx.fill()
    ctx.restore()


def make_icon(path, size=800):
    """チャンネルアイコン（YouTube は円で切り抜くので、中心に寄せる）"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surf)
    fill(ctx, NAVY)
    ctx.paint()
    k = size / 800
    # 円の中に収まる大きさ
    turtle(ctx, 364 * k, 473 * k, 1.55 * k)
    surf.write_to_png(str(path))


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "brand"
    out.mkdir(exist_ok=True)
    make_icon(out / "icon.png")
    print("アイコン:", out / "icon.png")


def mode_banner(ctx, label, x, y, a=1.0, t_rel=0.0, size=84):
    """「1万回モード」に入る合図。金の札の上に亀が乗って、まばたきする。
    シリーズ共通の目印なので、どの回もこの関数で出す（label は「1万人で引く」など）"""
    from engine.core import pill
    if a <= 0:
        return
    w, h = pill(ctx, label, x, y, size, "#ffd166", fg=NAVY, a=a)
    ctx.push_group()
    blink = 1.0 if 0.35 < t_rel < 0.45 else 0.0
    turtle(ctx, x - w / 2 + 95, y - h / 2 + 4, 0.42, blink=blink)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
