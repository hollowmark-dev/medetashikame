"""ノートの見た目（2026-09-27〜）。

初週の2本はフィードで「視聴を継続」が9〜15%しかなかった。紺の無地に光るボタンの三択は、
アプリやクイズゲームの広告と同じ見た目で、1コマ目で広告だと思われてスワイプされていた（ユーザーの指摘）。
そこで「方眼ノートに書いた自由研究」に寄せる:

- 背景は方眼紙、文字は手書き風の Klee One（Google Fonts・OFL。Windows に入れてあること）
- 三択はボタンではなく、ペンで丸をつけた選択肢。答えは赤ペンでぐるっと囲む
- 札（pill）の代わりに付箋（sticky）
- 冒頭は問題の画面（Intro）: 問題 → 三択を1つずつ → 亀「1万○○で確かめる」→ 予想して！3・2・1（1秒ずつ）→ 上へ移ってシミュ開始

使い方（sims/ の1本で）:
    from engine import note
    note.use()                       # 字を Klee One に
    INTRO = note.Intro(["1%のガチャを100回。", "当たる人は何%？"], ["100%", "63%", "50%"],
                       correct=1, msg="1万人で引いて確かめる", deco=draw_deco,
                       big=["1%のガチャを", "100回引いたら", "当たる人は何%？"], rule=["1回ごとに1%で当たり"])
    T_A0 = INTRO.T_GO                # シミュはここから
    def draw(ctx, t):
        note.paper(ctx)
        INTRO.draw(ctx, t, reveal_t=T_R20 + 0.8)
        if t < INTRO.T_GO: return    # 冒頭の間は Intro だけ（Intro.draw が亀とカウントも描く）
        ...
    INTRO.audio(mx)                  # build_audio の中で
"""
import math

import cairo
import numpy as np

import engine.core as core
from engine.core import W, H, blip, bell, clamp01, ease, ease_out, fill, hexrgb, rrect, text, whoosh

FONT = "Klee One"
PAPER = "#f6f2e7"
GRID = "#cfdcea"
INK = "#24324a"        # 本文（紺のインク）
PENCIL = "#6b7285"     # 補足（鉛筆）
RED = "#d8434e"        # 赤ペン（強調・答え）
MARKER = "#ffd84d"     # 蛍光ペン
STICKY = {"yellow": "#fff0a0", "pink": "#ffd0da", "mint": "#c9f0dc", "blue": "#d3e4ff"}


def use():
    """このあと描く文字を手書き風にする。Klee One はスマホでは細いので、太字の文字は縁取りで少し太らせる"""
    core.FONT = FONT
    core.STROKE = 0.045
    core.MIX_LEVEL = 0.075   # 効果音が少し大きいと言われた（2026-09-27）
    core.SFX_GAIN = 0.5      # 続けて「BGMはそのままでいい、ピコーンがまだ大きい」（同日）。pad と beat は bgm=True で足す


# ---------- 紙 ----------
_PAPER = None
DATE = None          # 日付欄に手書きで入れる文字（"9.28" など）。sim で公開日を入れる
DESK = "#b98f62"     # 穴から見える机（木）の色
MARGIN_X = 92        # 赤い余白線の位置
PAGE_DX = 40         # 中央そろえの物をずらす量。画面の中心(540)ではなく、穴と余白線を除いた紙の中心(約580)にそろえる
                     # （2026-09-28 ユーザー「左はリングの穴だから、そこを避けて中央ぞろいに」）。sim 側も本体を translate(PAGE_DX, 0) で描く


def paper(ctx, step=45):
    """ルーズリーフの方眼紙。左に穴と赤い余白線、紙のざらつき、右上に日付欄。毎コマ描かず、1枚作って貼る。
    2026-09-27 ユーザー「まだ広告っぽい。手作りっぽい要素を1コマに」→ 真っ平らな紙をやめて、机の上のノートに寄せた"""
    global _PAPER
    if _PAPER is None:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        fill(c, PAPER)
        c.paint()
        c.set_line_width(1.5)
        for x in range(0, W + 1, step):
            c.set_source_rgba(*hexrgb(GRID, 1 if x % (step * 5) == 0 else 0.55))
            c.move_to(x + 0.5, 0)
            c.line_to(x + 0.5, H)
            c.stroke()
        for y in range(0, H + 1, step):
            c.set_source_rgba(*hexrgb(GRID, 1 if y % (step * 5) == 0 else 0.55))
            c.move_to(0, y + 0.5)
            c.line_to(W, y + 0.5)
            c.stroke()
        # 赤い余白線（2本）
        for dx, al in ((0, 0.55), (7, 0.35)):
            c.set_source_rgba(*hexrgb(RED, al))
            c.set_line_width(2.5)
            c.move_to(MARGIN_X + dx, 0)
            c.line_to(MARGIN_X + dx, H)
            c.stroke()
        # 紙のざらつき（うっすら）
        rng = np.random.default_rng(3)
        buf = np.ndarray((H, W, 4), np.uint8, s.get_data())
        noise = rng.normal(0, 3.2, (H, W, 1))
        from PIL import Image
        low = Image.fromarray(np.uint8(np.clip(128 + rng.normal(0, 40, (H // 80 + 2, W // 80 + 2)), 0, 255)))
        blot = (np.asarray(low.resize((W, H), Image.BICUBIC), np.float32)[:, :, None] - 128) / 40 * 2.0
        buf[:, :, :3] = np.clip(buf[:, :, :3].astype(np.float32) + noise + blot, 0, 255).astype(np.uint8)
        s.mark_dirty()
        # 穴（机が見える）
        for y in range(150, H, 190):
            c.set_source_rgba(*hexrgb(DESK))
            c.arc(40, y, 17, 0, 2 * math.pi)
            c.fill()
            c.set_source_rgba(0, 0, 0, 0.18)
            c.set_line_width(3)
            c.arc(40, y, 17, math.pi * 1.1, math.pi * 1.9)
            c.stroke()
        # 日付欄
        text(c, "No.", 610, 66, 26, PENCIL, align="left", bold=False)
        text(c, "Date", 790, 66, 26, PENCIL, align="left", bold=False)
        c.set_source_rgba(*hexrgb(PENCIL, 0.6))
        c.set_line_width(1.5)
        for x0, x1 in ((652, 770), (852, 1030)):
            c.move_to(x0, 82)
            c.line_to(x1, 82)
            c.stroke()
        if DATE:
            text(c, DATE, 930, 62, 34, INK, bold=False)
        _PAPER = s
    ctx.set_source_surface(_PAPER, 0, 0)
    ctx.paint()


# ---------- ペン ----------

def pen_circle(ctx, cx, cy, rx, ry, color=INK, seed=0, width=5, progress=1.0, alpha=1.0):
    """ペンでぐるっと囲んだ丸（少しゆがんで1周ちょっと）。progress で書いている途中も描ける"""
    if progress <= 0 or alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    a0 = rng.uniform(0, 2 * math.pi)
    n = max(2, int(64 * progress))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(color, alpha))
    for i in range(n):
        a = a0 + i / 60 * 2.15 * math.pi
        wob = 1 + 0.04 * math.sin(3 * a + seed) + 0.03 * i / 60
        x, y = cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.stroke()


def pen_line(ctx, x0, y0, x1, y1, color=RED, seed=1, width=6, progress=1.0, alpha=1.0):
    """手で引いた線（少したわむ）。下線・取り消し線に"""
    if progress <= 0 or alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    b1, b2 = rng.uniform(-6, 6), rng.uniform(-6, 6)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(color, 0.9 * alpha))
    n = max(2, int(24 * progress))
    for i in range(n):
        u = i / 23
        x = x0 + (x1 - x0) * u
        y = y0 + (y1 - y0) * u + (b1 * 3 * u * (1 - u) ** 2 + b2 * 3 * u * u * (1 - u)) * 2
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.stroke()


# ---------- 手書きの字 ----------

def hand_text(ctx, s, x, y, size, color=INK, seed=0, alpha=1.0, align="left", jitter=1.0):
    """1字ずつ、ほんの少し傾けて・上下にずらして書く（機械でそろえた行に見せない）。
    冒頭の大きな問題など、1コマ目の目立つ字に使う。公開前チェックのため字は core.text で描く"""
    rng = np.random.default_rng(seed)
    ctx.select_font_face(core.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    ws = [ctx.text_extents(ch).x_advance for ch in s]
    tot = sum(ws)
    cx = x - tot / 2 if align == "center" else (x - tot if align == "right" else x)
    for ch, w in zip(s, ws):
        ang = rng.normal(0, 0.035) * jitter
        dy = rng.normal(0, size * 0.035) * jitter
        sc = 1 + rng.normal(0, 0.03) * jitter
        ctx.save()
        ctx.translate(cx + w / 2, y + dy)
        ctx.rotate(ang)
        ctx.scale(sc, sc)
        text(ctx, ch, 0, 0, size, color, alpha=alpha)
        ctx.restore()
        cx += w * (1 + rng.normal(0, 0.02) * jitter)
    return tot


def tape(ctx, cx, cy, w, h, ang, a=1.0):
    """マスキングテープ（半透明のクリーム色、端はギザギザ）"""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang)
    ctx.move_to(-w / 2, -h / 2)
    ctx.line_to(w / 2, -h / 2)
    for i in range(7):
        ctx.line_to(w / 2 + (4 if i % 2 == 0 else -2), -h / 2 + h * (i + 1) / 7)
    ctx.line_to(-w / 2, h / 2)
    for i in range(7):
        ctx.line_to(-w / 2 + (-4 if i % 2 == 0 else 2), h / 2 - h * (i + 1) / 7)
    ctx.close_path()
    ctx.set_source_rgba(0.93, 0.88, 0.74, 0.78 * a)
    ctx.fill()
    ctx.restore()


# ---------- 付箋 ----------

def sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.025):
    """付箋に文字を書く（札 pill の代わり）。(x, y) は中心。s は改行を含めてよい"""
    if a <= 0:
        return 0, 0
    ctx.select_font_face(core.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    lines = s.split("\n")
    w = max(ctx.text_extents(l).x_advance for l in lines) + 90
    h = size * 1.25 * len(lines) + 56
    bg = STICKY.get(color, color)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)          # 影
    rrect(ctx, -w / 2 + 6, -h / 2 + 10, w, h, 6)
    ctx.fill()
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, -w / 2, -h / 2, w, h, 6)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)                    # のりの部分
    ctx.rectangle(-w / 2, -h / 2, w, 22)
    ctx.fill()
    text(ctx, s, 0, 6, size, fg, alpha=a)
    ctx.restore()
    return w, h


def banner(ctx, label, x, y, a=1.0, t_rel=0.0, size=80):
    """「1万回モード」に入る合図（ノート版）。黄色い付箋に亀が乗って、まばたきする"""
    from engine.brand import turtle
    if a <= 0:
        return
    w, h = sticky(ctx, label, x, y, size, "yellow", a=a, tilt=-0.02)
    ctx.push_group()
    blink = 1.0 if 0.35 < t_rel < 0.45 else 0.0
    turtle(ctx, x - w / 2 + 70, y - h / 2 + 8, 0.42, blink=blink)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def legend(ctx, items, y, size=34, gap=64):
    """色の見本と説明を中央にそろえて並べる。items = [(色 or [色,...], 説明)]。色が複数なら縞で"""
    ctx.select_font_face(core.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ws = [48 + ctx.text_extents(lab).x_advance for _, lab in items]
    x = 540 - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        cols = col if isinstance(col, (list, tuple)) and isinstance(col[0], str) else [col]
        k = len(cols)
        for j, c in enumerate(cols):
            fill(ctx, c)
            ctx.rectangle(x + j * 34 / k, y - 17, 34 / k, 34)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7))
        ctx.set_line_width(2)
        ctx.rectangle(x, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, x + 48, y, size, INK, align="left", bold=False)
        x += w + gap


# ---------- 冒頭の問題画面 ----------

class Intro:
    """冒頭の問題画面（約6秒）→ 上の定位置の問題と三択に入れ替わってシミュ開始。

    2026-09-27 2回作り直した結果の形:
    - 中央そろえ・左右対称は広告の文法。**左寄せで、字を1字ずつ少し傾けた手書き**にする
    - 三択は縦に並べたメモ書き（Ⓐ 100% / Ⓑ 63% / Ⓒ 50%）
    - 右に「予想して！」と、赤ペンの丸の中の 5・4・3・2・1（実際の秒数どおり1秒ずつ）
    - 亀はマスキングテープで貼ったシール、その横に「1万人で引いて確かめる →」
    - 三択の下にルールのメモ（2026-09-27 ユーザー「理解する前に始まる」→ 待つ時間を読む時間にする）

    title   … 定位置（y=150・235）の問題の2行
    big     … 冒頭の大きな問題（3行ほど）
    labels  … 三択の中身。A/B/C は自動で付く
    correct … 正解の番号（0始まり）。draw(reveal_t=) の時刻から赤ペンで囲む
    msg     … 亀の横の一言
    rule    … ルールのメモ（1〜2行）。カウントダウンの間に読めるよう、枠で囲んで三択の下に出す
    deco    … deco(ctx, t, a) 冒頭の右上に置く題材の小物。0秒目から動かすこと
    """
    T_CHO = (0.7, 0.95, 1.2)
    T_MSG = 1.7
    T_RULE = 2.2
    # カウントは 5 から、実際の秒数どおり1秒ずつ（2026-09-27 ユーザー「理解する前に始まってしまう。しっかりためを」）
    T_CD = (2.75, 3.75, 4.75, 5.75, 6.75)
    T_MOVE = 7.75
    T_GO = 8.15
    LX = 135                       # 冒頭の字の左端（余白線の右）

    def __init__(self, title, labels, correct, msg, deco=None, title_sizes=(62, 66), big=None,
                 big_sizes=(64, 88, 88), rule=None):
        self.title, self.labels, self.correct, self.msg, self.deco = title, labels, correct, msg, deco
        self.rule = rule or []
        self.title_sizes = title_sizes
        self.big, self.big_sizes = big or title, big_sizes

    def moved(self, t):
        return ease(clamp01((t - self.T_MOVE) / (self.T_GO - self.T_MOVE)))

    # 冒頭（左寄せの手書き）
    def _intro(self, ctx, t, a):
        from engine.brand import turtle
        if self.deco:
            self.deco(ctx, t, a)
        ys = [440, 545, 650][:len(self.big)]
        for k, (line, y, sz) in enumerate(zip(self.big, ys, self.big_sizes)):
            w = hand_text(ctx, line, self.LX, y, sz, INK, seed=11 + k, alpha=a)
        # 最後の行（聞きたいこと）にだけ赤い下線を、書くように引く
        pen_line(ctx, self.LX - 5, ys[-1] + 62, self.LX + w + 10, ys[-1] + 56, RED, seed=5, width=7,
                 progress=clamp01(t / 0.5), alpha=a)
        # 三択（縦のメモ書き）
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 800 + i * 95
            x = self.LX + 38 + 14 * (1 - show)
            pen_circle(ctx, x, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x, y, 44, INK, alpha=a * show)
            hand_text(ctx, v, x + 62, y, 66, INK, seed=21 + i, alpha=a * show)
        # 予想して！ と 3・2・1（右側、赤ペンの丸の中）
        if t >= self.T_CD[0]:
            a1 = ease_out((t - self.T_CD[0]) / 0.2) * a
            hand_text(ctx, "予想して！", 800, 790, 60, RED, seed=41, alpha=a1, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            pen_circle(ctx, 800, 915, 82, 78, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(800, 915)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) + 1 - n), 0, 0, 118, INK, alpha=a)
            ctx.restore()
        # 亀のシール（テープで貼る）と一言
        if t >= self.T_MSG:
            a2 = ease_out((t - self.T_MSG) / 0.3) * a
            ctx.push_group()
            blink = 1.0 if 0.5 < (t - self.T_MSG) % 2.2 < 0.6 else 0.0
            ctx.save()
            ctx.translate(850, 1380)
            ctx.rotate(0.07)
            fill(ctx, (1, 1, 1, 0.92))
            rrect(ctx, -140, -150, 300, 190, 22)
            ctx.fill()
            turtle(ctx, 0, 0, 0.5, blink=blink)
            ctx.restore()
            tape(ctx, 975, 1245, 110, 34, 0.5)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a2)
            hand_text(ctx, self.msg + " →", self.LX + 10, 1320, 50, INK, seed=61, alpha=a2)
        # ルールのメモ（手で引いた枠の中に）
        if self.rule and t >= self.T_RULE:
            a3 = ease_out((t - self.T_RULE) / 0.3) * a
            y0 = 1115
            w = 0
            for k, line in enumerate(self.rule):
                w = max(w, hand_text(ctx, line, self.LX + 20, y0 + k * 68, 46, INK, seed=71 + k, alpha=a3))
            top, bot, x0, x1 = y0 - 62, y0 + 68 * (len(self.rule) - 1) + 42, self.LX - 8, self.LX + w + 44
            text(ctx, "ルール", x0 + 60, top, 30, RED, alpha=a3)
            for (xa, ya, xb, yb, sd) in ((x0 + 110, top, x1, top + 2, 81), (x1, top, x1 + 3, bot, 82),
                                         (x1, bot, x0, bot + 3, 83), (x0, bot, x0 - 2, top, 84)):
                pen_line(ctx, xa, ya, xb, yb, PENCIL, seed=sd, width=3, progress=clamp01((t - self.T_RULE) / 0.4),
                         alpha=a3)

    # 定位置（上に小さく）
    def _top(self, ctx, t, m, reveal_t):
        text(ctx, self.title[0], 540, 150, self.title_sizes[0], INK, alpha=m)
        text(ctx, self.title[1], 540, 235, self.title_sizes[1], INK, alpha=m)
        pen_line(ctx, 130, 290, 950, 286, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        for i, v in enumerate(self.labels):
            cx, y = 540 + (i - 1) * 320, 370
            ok = i == self.correct
            a = m * (1 - 0.55 * rev * (not ok))
            pen_circle(ctx, cx - 70, y, 30, 30, INK, seed=i + 7, width=4, alpha=a)
            text(ctx, "ABC"[i], cx - 70, y, 40, INK, alpha=a)
            text(ctx, v, cx + 28, y, 52, RED if (ok and rev > 0.5) else INK, alpha=a)
            if ok:
                pen_circle(ctx, cx - 10, y, 140, 52, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                pen_line(ctx, cx - 110, y + 4, cx + 95, y - 2, PENCIL, seed=i + 40, width=4,
                         progress=rev, alpha=0.8)

    def draw(self, ctx, t, reveal_t=None):
        m = self.moved(t)
        if m < 1:
            self._intro(ctx, t, 1 - clamp01(m * 2.2))
        if m > 0:
            ctx.save()
            ctx.translate(PAGE_DX, 0)
            self._top(ctx, t, m, reveal_t)
            ctx.restore()

    def audio(self, mx):
        for c in self.T_CHO:
            mx.add(c, blip(1046.5, 0.1), 0.45)
        mx.add(self.T_MSG, bell(784.0, 1.0), 0.3)
        for j, c in enumerate(self.T_CD):
            mx.add(c, blip(1318.5 if j == len(self.T_CD) - 1 else 659.3, 0.2), 0.55)
        mx.add(self.T_MOVE - 0.1, whoosh(0.6), 0.2)
