"""めでたしかめ 横型ロング（1920×1080・見開きノート）の共通部品集。2026-10-24 に 桶狭間・伊能忠敬・電車の空席 の3本から切り出した。

ロング1本ごとに sims/<名前>-long.py へコピーして直していた部品（勝率/ずれの棒の枠・冒頭の約束・1万マス・各種チェック）を、
どの題材でも使える形にまとめたもの。engine/longform.py（Timeline・Line・Chapter・Gap・spread・stills・render）の上に載せて使う。
既存の sims/*.py は import しない（公開済み・予約済みの動画を変えないため）。コピーして一般化してある。

使い方（sims/<名前>-long.py で）:
    from engine import longform as lf, longkit as lk
    lf.use()
    panel = lk.LadderPanel("勝率", [lk.Row("野原・全軍", 0.0, t_label=40.0, t_value=52.0, line="c1_res", color=lk.BLUE), ...],
                           t_frame=39.5, fmt=lk.pct)
    teaser = lk.OpeningTeaser(["もう一度", "戦ったら、", "2千人は勝てる？"], left=draw_battle, thumb_text="もう一度戦ったら、2千人は勝てる？")
    grid = lk.GridPanel(wins=627, caption="青＝織田の勝ち　1マス＝1回", t0=60, t1=68)
    # draw の中で panel.draw(ctx, t) / teaser.draw(ctx, t) / grid.draw(ctx, t)
    # 場面の照合で:
    frames = lk.scan_frames(draw, tl.duration, timeline=tl)           # 0.25秒ごとの文字の箱
    lk.text_box_overlaps(frames, exempt=CH_TITLES)                   # 文字の交わり
    rows, bad = lk.visual_lag(panel.cues(), tl)                       # 絵が声より遅いもの
    lk.min_text_size(frames, 40)                                      # スマホで読める大きさ
    lk.small(out/"x.mp4")                                             # 30MB 未満のプレビュー
デモと動作確認: sims/longkit-demo-long.py（python -X utf8 sims/longkit-demo-long.py）。

絵の座標・時刻の決まり（ロングの作り方 research/longform_plan.md より）:
  - 表・棒の「枠」（見出し・項目名）は、声がその話を始める 0.5 秒前には読める状態にする。答えの数字だけ声に合わせて出す
  - 画面の文字は 1920 幅で 40px 以上（幅 480px に縮めても読める）。冒頭の問いは 90px 以上でサムネと同じ言葉
"""
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cairo
import numpy as np

import engine.core as core
from engine import longform as lf
from engine.core import clamp01, ease, ease_out, fill, hexrgb, rrect, text, text_width
from engine.note import INK, PENCIL, RED, pen_line

# ---- 色（桶狭間・伊能忠敬と同じ） ----
BLUE = "#3a73c8"
ORANGE = "#e0892a"
GREEN = "#3f9a6a"
PENCIL_T = "#454d62"                  # 補足の文字
WIN_C, LOSS_C, EMPTY_C = "#2a63c8", "#eaaea6", "#e9e3d3"      # 1万マス（勝ち・負け・まだ埋まっていない）

MIN_PANEL_TEXT = 40                   # 棒の枠・マス目の文字の最小サイズ（1920 幅で）
MIN_QUESTION = 90                     # 冒頭の問いの最小サイズ
FRAME_LEAD = 0.5                      # 枠は声の文の頭の 0.5 秒前までにそろえる


# ============================================================
# 小さな道具
# ============================================================

def _fade(t, t0, d=0.3):
    """t0 から d 秒かけて 0→1"""
    return clamp01((t - t0) / d)


def _out_fade(t, t1, d=0.35):
    """t1 から d 秒かけて 1→0"""
    return clamp01((t1 + d - t) / d)


def pct(v, digits=None):
    """0〜1 の勝率を「6%」「0.3%」「73%」の形に。digits 省略時は 1% 未満だけ小数1桁（0.3%）、0 は「0%」"""
    x = v * 100
    if digits is not None:
        return f"{x:.{digits}f}%"
    if x == 0:
        return "0%"
    if x < 1:
        return f"{x:.1f}%"
    return f"{int(x + 0.5)}%"


def num1(v, unit="km"):
    """ずれなどの数値を「24.4km」の形に（小数1桁）"""
    return f"{v:.1f}{unit}"


def arrow_down(ctx, x, y, h, col, a=1.0, w=3.2):
    """小さな ↓（条件を1つ足していく向き）。(x, y) は中心、h は半分の長さ"""
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y - h)
    ctx.line_to(x, y + h)
    ctx.stroke()
    ctx.move_to(x - 7, y + h - 7)
    ctx.line_to(x, y + h)
    ctx.line_to(x + 7, y + h - 7)
    ctx.stroke()


# ============================================================
# 1. LadderPanel（棒の梯子：勝率・ずれ など）
# ============================================================

@dataclass
class Row:
    """梯子の1行。value は vmax に対する値（None なら枠だけ）。
    t_label=名札と棒の枠が出る時刻（None なら t_frame から 0.12 秒ずつ）、t_value=棒が伸びる時刻（声に合わせる）、
    line=この行を話す声の文の id（cues() と visual_lag 用）、branch=積み上げの梯子とは別の枝（前に点線）。
    plain=True なら '＋' を付けない。text=値の文字を直接指定。sub=名札の下の補足（40px 以上）"""
    label: str
    value: float = None
    t_label: float = None
    t_value: float = 0.0
    color: str = BLUE
    branch: bool = False
    plain: bool = False
    text: str = None
    sub: str = None
    line: str = None


@dataclass
class Cue:
    """絵の出る時刻の記録（visual_lag 用）。kind='frame'=声より前にそろえる枠、'value'=声に合わせて出す答え。
    start=現れはじめる時刻、ready=読めるようになる（描ききる）時刻、line=その絵を話す声の文の id"""
    name: str
    kind: str
    start: float
    ready: float
    line: str = None


class LadderPanel:
    """【いつ使う】条件を1つずつ足すと数字が変わっていくロング（勝率 0%→0%→0.3%→6%、ずれ 50→24→8…）の、棒の梯子。
    1行目の名札はそのまま、2行目から自動で「＋」を付ける（plus=False でやめる）。行と行の間に小さな ↓、
    branch=True の行の前には点線（梯子とは別の枝。例: 江戸時代の谷）。
    枠（箱・見出し・名札・棒のわく）と値（棒が伸びる・数字）の時刻を別々に持つので、
    「枠は声の0.5秒前・数字は声に合わせて」ができる。文字は全部 40px 以上（小さいと ValueError）。
    box は (x0, y0, x1, y1)。既定は右ページの下（桶狭間の panel_small と同じ位置）で、右ページいっぱいに使うなら box=(1030,100,1830,920)。
    fmt は値→文字（pct / num1 など）、vmax は棒の枠いっぱいの値"""

    def __init__(self, title, rows, box=(1030, 560, 1830, 920), t_frame=0.0, vmax=1.0, fmt=pct, plus=True, arrows=True,
                 title_size=44, label_size=42, val_size=52, sub_size=40, fade=0.4, grow=0.9, title_line=None, bar_h=None):
        for nm, sz in (("title_size", title_size), ("label_size", label_size), ("val_size", val_size), ("sub_size", sub_size)):
            if sz < MIN_PANEL_TEXT:
                raise ValueError(f"LadderPanel.{nm}={sz} は小さすぎる（{MIN_PANEL_TEXT}px 以上。幅480pxに縮めても読めるように）")
        self.title, self.rows, self.box = title, list(rows), box
        self.t_frame, self.vmax, self.fmt, self.plus, self.arrows = t_frame, vmax, fmt, plus, arrows
        self.title_size, self.label_size, self.val_size, self.sub_size = title_size, label_size, val_size, sub_size
        self.fade, self.grow, self.title_line, self._bar_h = fade, grow, title_line, bar_h
        self._geo = None
        for i, r in enumerate(self.rows):
            if r.t_label is None:
                r.t_label = t_frame + 0.12 * (i + 1)

    # ---- 表示する文字 ----
    def label_of(self, i):
        """i 行目の名札（1つ目の非 branch 行は素のまま、後ろは「＋」付き）"""
        r = self.rows[i]
        if (not self.plus) or r.branch or r.plain or r.label[:1] in "＋+":
            return r.label
        first = next(k for k, x in enumerate(self.rows) if not x.branch)
        return r.label if i == first else "＋" + r.label

    def value_text(self, r):
        if r.text is not None:
            return r.text
        return "" if r.value is None else self.fmt(r.value)

    # ---- 配置（フォントが決まってから最初の draw で計算） ----
    def layout(self):
        if self._geo is not None:
            return self._geo
        x0, y0, x1, y1 = self.box
        n = len(self.rows)
        title_cy = y0 + 34
        first = title_cy + self.title_size * 0.5 + self.label_size * 0.95
        last = y1 - max(24, self.label_size * 0.55)
        extra = [0.0] * n                                   # 行の前に足す間隔（枝の前は半分、補足つきの行の後ろも半分）
        for i, r in enumerate(self.rows):
            if i and r.branch:
                extra[i] += 0.5
            if i and self.rows[i - 1].sub:
                extra[i] += 0.5
        units = (n - 1) + sum(extra)
        pitch = (last - first) / max(units, 1.0)
        ys, cur = [], first
        for i in range(n):
            if i:
                cur += pitch * (1 + extra[i])
            ys.append(cur)
        lab_w = max([text_width(self.label_of(i), self.label_size) for i in range(n)] + [10])
        val_w = max([text_width(self.value_text(r), self.val_size) for r in self.rows] + [text_width("100%", self.val_size)]) + 12
        label_x = x0 + 32
        track_x = label_x + lab_w + 28
        track_w = max(60.0, (x1 - 28) - val_w - 14 - track_x)
        bar_h = self._bar_h or min(40.0, pitch * 0.62)
        self._geo = dict(title_cy=title_cy, ys=ys, pitch=pitch, label_x=label_x, track_x=track_x, track_w=track_w,
                         val_x=track_x + track_w + 14, bar_h=bar_h)
        return self._geo

    def layout_problems(self):
        """枠が小さすぎて行が詰まるときの注意（文字と文字の間が 1.15 倍の行間より狭い）"""
        g = self.layout()
        out = []
        if g["pitch"] < self.label_size * 1.15:
            out.append(f"{self.title}: 行間 {g['pitch']:.0f}px が名札 {self.label_size}px に対して詰まる（枠を広げるか行を減らす）")
        if g["track_w"] < 120:
            out.append(f"{self.title}: 棒の枠が {g['track_w']:.0f}px しかない（名札が長すぎる）")
        return out

    # ---- 描く ----
    def draw(self, ctx, t, a=1.0):
        g = self.layout()
        x0, y0, x1, y1 = self.box
        af = a * _fade(t, self.t_frame, self.fade)
        if af <= 0.003:
            return
        ctx.set_source_rgba(1, 1, 1, 0.6 * af)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * af))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        text(ctx, self.title, x0 + 32, g["title_cy"], self.title_size, INK, align="left", alpha=af)
        tx, tw, bh = g["track_x"], g["track_w"], g["bar_h"]
        # 点線（枝の前）と ↓（積み上げの間）
        for i, r in enumerate(self.rows):
            if i == 0:
                continue
            la = a * _fade(t, r.t_label, self.fade)
            mid = (g["ys"][i - 1] + g["ys"][i]) / 2
            if r.branch:
                if la > 0.003:
                    ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * la))
                    ctx.set_line_width(3)
                    ctx.set_dash([10, 8])
                    ctx.move_to(x0 + 24, mid)
                    ctx.line_to(x1 - 24, mid)
                    ctx.stroke()
                    ctx.set_dash([])
            elif self.arrows and not self.rows[i - 1].branch:
                al = a * _fade(t, r.t_label + 0.3, self.fade)
                if al > 0.003:
                    h = max(5.0, min(11.0, (g["pitch"] - bh) / 2 - 2))
                    arrow_down(ctx, tx + 18, mid, h, PENCIL_T, al)
        for i, r in enumerate(self.rows):
            y = g["ys"][i]
            la = a * _fade(t, r.t_label, self.fade)
            if la <= 0.003:
                continue
            ctx.set_source_rgba(1, 1, 1, 0.7 * la)                      # 棒のわく（枠の一部。値より先に出る）
            rrect(ctx, tx, y - bh / 2, tw, bh, 6)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * la))
            ctx.set_line_width(2.5)
            rrect(ctx, tx, y - bh / 2, tw, bh, 6)
            ctx.stroke()
            text(ctx, self.label_of(i), g["label_x"], y, self.label_size, INK, align="left", alpha=la)
            if r.sub:
                text(ctx, r.sub, g["label_x"], y + self.label_size * 0.95, self.sub_size, PENCIL_T, align="left", bold=False, alpha=la)
            if r.value is None and r.text is None:
                continue
            bu = ease_out(clamp01((t - r.t_value) / self.grow))
            if bu <= 0.003:
                continue
            frac = 0.0 if r.value is None else clamp01(r.value / self.vmax)
            wd = max(4.0, tw * frac) * bu if frac > 0 else 0.0
            if wd > 0:
                ctx.set_source_rgba(*hexrgb(r.color, 0.92 * la))
                rrect(ctx, tx, y - bh / 2, wd, bh, 6)
                ctx.fill()
            vt = self.value_text(r)
            if vt and bu > 0.15:
                text(ctx, vt, g["val_x"], y, self.val_size, r.color, align="left", alpha=la * clamp01((bu - 0.15) / 0.3))

    # ---- visual_lag 用の記録 ----
    def cues(self):
        """枠（箱・見出し・各行の名札と棒のわく）と値（棒・数字）の出る時刻の記録。visual_lag(panel.cues(), timeline) に渡す。
        line を持たない行は記録しない（title_line が無ければ枠の箱は最初の行の line を使う）"""
        out = []
        first_line = next((r.line for r in self.rows if r.line), None)
        tl_ = self.title_line or first_line
        if tl_:
            out.append(Cue(f"{self.title} 枠(箱・見出し)", "frame", self.t_frame, self.t_frame + self.fade, tl_))
        for i, r in enumerate(self.rows):
            if not r.line:
                continue
            out.append(Cue(f"{self.title} 名札「{self.label_of(i)}」", "frame", r.t_label, r.t_label + self.fade, r.line))
            if r.value is not None or r.text is not None:
                out.append(Cue(f"{self.title} 棒「{self.label_of(i)}」", "value", r.t_value, r.t_value + self.grow, r.line))
        return out


# ============================================================
# 2. OpeningTeaser（0〜5秒：サムネと同じ問い＋答えのちら見せ）
# ============================================================

class OpeningTeaser:
    """【いつ使う】ロングの 0〜5 秒。合戦で言えば 0 秒目から 2 つがぶつかり合っていて（left=左ページの動く絵）、
    右ページには「サムネと同じ言葉の問い」が大きく（90px 以上）出ていて、答えの箱の数字が 0 から上がっていき、
    あるところで「？」に伏せられる——という形。数字そのものは言わなくてよい（ちら見せ）。
    left は callable(ctx, t)（左ページの動き。省略可）。thumb_text を渡すと、問いの行をつなげた文字がそれと同じか確かめる。
    value_fn(t) を渡すと数字の動きを自分で決められる（省略時は t_up0〜t_up1 で 0→peak へ ease）。
    hide_at 以降は数字を「？」にする（hide_at=None なら最初から「？」で、棒だけ伸びる）。
    t_out 以降は答えの箱を消す（その後は LadderPanel の枠に引きつぐ）。
    shrink=(時刻, 小さい文字サイズ, y) で問いを小さくして場所をあける（桶狭間は 1560年の文から 66px の2行に）。
    大きい問いは時刻の0.05秒前までに消え、小さい問いはその時刻から出る（入れかえで箱が重ならない）。"""

    def __init__(self, question, left=None, thumb_text=None, q_pos=(1050, 285), q_size=100, underline=None,
                 box=(1030, 560, 1830, 704), box_title="勝率", unit="%", fmt=None, peak=0.06, vmax=1.0,
                 t_up0=0.15, t_up1=3.2, hide_at=3.2, t_out=None, value_fn=None, shrink=None, color=BLUE, val_size=84, title_size=64):
        self.q_lines = [question] if isinstance(question, str) else list(question)
        self.q_size = q_size
        if q_size < MIN_QUESTION:
            raise ValueError(f"OpeningTeaser: 問いの文字 {q_size}px は小さい（{MIN_QUESTION}px 以上）")
        if thumb_text is not None and "".join(self.q_lines).replace("\n", "") != thumb_text:
            raise ValueError(f"OpeningTeaser: 問い「{''.join(self.q_lines)}」がサムネの言葉「{thumb_text}」と違う（同じ言葉にする）")
        for nm, sz in (("val_size", val_size), ("title_size", title_size)):
            if sz < MIN_PANEL_TEXT:
                raise ValueError(f"OpeningTeaser.{nm}={sz} は小さすぎる（{MIN_PANEL_TEXT}px 以上）")
        self.left, self.q_pos, self.underline = left, q_pos, underline
        self.box, self.box_title, self.unit, self.fmt = box, box_title, unit, fmt
        self.peak, self.vmax, self.t_up0, self.t_up1 = peak, vmax, t_up0, t_up1
        self.hide_at, self.t_out, self.value_fn, self.shrink = hide_at, t_out, value_fn, shrink
        self.color, self.val_size, self.title_size = color, val_size, title_size

    def value_at(self, t):
        """いまの数字（0〜peak）。hide_at より前だけ意味がある"""
        if self.value_fn:
            return self.value_fn(t)
        return self.peak * ease(clamp01((t - self.t_up0) / max(self.t_up1 - self.t_up0, 1e-6)))

    def hidden_at(self, t):
        return self.hide_at is None or t >= self.hide_at

    def _fmt(self, v):
        if self.fmt:
            return self.fmt(v)
        return f"{int(v * 100 + 0.5)}" if self.unit == "%" else f"{v:.0f}"

    def draw(self, ctx, t, a=1.0):
        if self.left:
            self.left(ctx, t)
        self.draw_question(ctx, t, a)
        self.draw_box(ctx, t, a)

    def draw_question(self, ctx, t, a=1.0):
        x, y = self.q_pos
        txt = "\n".join(self.q_lines)
        big = 1.0
        if self.shrink:
            ts, sz, ys = self.shrink
            big = _out_fade(t, ts - 0.25, 0.2)             # 大きい問いが消えきってから（ts）小さい問いが出る＝同時には重ならない
            small = _fade(t, ts, 0.25)
            if small > 0.003:
                text(ctx, txt, x, ys, sz, INK, align="left", alpha=a * small)
        if big > 0.003:
            text(ctx, txt, x, y, self.q_size, INK, align="left", alpha=a * big)
            if self.underline:
                last = self.q_lines[-1]
                w = text_width(last, self.q_size)
                lh = self.q_size * 1.25
                yb = y + lh * (len(self.q_lines) - 1) / 2 + self.q_size * 0.62
                pen_line(ctx, x - 4, yb, x + w + 4, yb - 4, RED, seed=5, width=9, progress=clamp01(t / 0.6), alpha=a * big)

    def draw_box(self, ctx, t, a=1.0):
        al = a * (_out_fade(t, self.t_out, 0.4) if self.t_out is not None else 1.0)
        if al <= 0.003:
            return
        x0, y0, x1, y1 = self.box
        ctx.set_source_rgba(1, 1, 1, 0.6 * al)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * al))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        cy = (y0 + y1) / 2
        text(ctx, self.box_title, x0 + 32, cy, self.title_size, INK, align="left", alpha=al)
        hidden = self.hidden_at(t)
        v = self.value_at(t) if not hidden else self.peak
        # 棒（数字を伏せたあとも、止まったところの長さで残す）
        tx = x0 + 32 + text_width(self.box_title, self.title_size) + 28
        tw = max(80.0, x1 - 32 - (text_width("？" + self.unit, self.val_size) + 20) - tx)
        bh = 36
        ctx.set_source_rgba(1, 1, 1, 0.7 * al)
        rrect(ctx, tx, cy - bh / 2, tw, bh, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * al))
        ctx.set_line_width(2.5)
        rrect(ctx, tx, cy - bh / 2, tw, bh, 6)
        ctx.stroke()
        wd = tw * clamp01(v / self.vmax)
        if wd > 1:
            ctx.set_source_rgba(*hexrgb(self.color, 0.92 * al))
            rrect(ctx, tx, cy - bh / 2, max(4.0, wd), bh, 6)
            ctx.fill()
        vx = tx + tw + 14
        label = "？" if hidden else self._fmt(v)
        text(ctx, label + self.unit, vx, cy, self.val_size, RED if hidden else self.color, align="left", alpha=al)

    def check(self, frames, step=0.25):
        """冒頭 0〜5 秒の機械チェック。frames=scan_frames の結果。問題の文字列のリストを返す（空なら OK）。
        ・0.0 秒目に問いの全行が出ている（サイズ q_size）  ・hide_at 以降は答えの数字（数字+単位）が画面に無い（「？」のみ）"""
        probs = []
        f0 = next((f for f in frames if abs(f[0]) < 1e-6), None)
        if f0 is None:
            return ["0.0秒のコマがない"]
        labels0 = {e[0] for e in f0[1]}
        for ln in self.q_lines:
            if ln not in labels0:
                probs.append(f"0.0秒目に問いの行「{ln}」が出ていない")
        if self.hide_at is not None:
            pat = re.compile(r"^\d+(\.\d+)?\s*" + re.escape(self.unit) + r"$")
            for t, boxes in frames:
                if self.hide_at <= t <= 5.0 and (self.t_out is None or t < self.t_out):
                    bad = [e[0] for e in boxes if pat.match(e[0])]
                    if bad:
                        probs.append(f"{t:.2f}秒: 伏せたはずの数字が出ている {bad}")
                        break
        return probs


# ============================================================
# 3. GridPanel（1万マス）
# ============================================================

class GridPanel:
    """【いつ使う】「1万回やった結果」を 100×100 のマス目で見せるとき。1マス＝1回。勝ち（青）と負け（赤）がばらけて埋まっていく。
    上に大きな1行の読み方（caption。例「青＝織田の勝ち　1マス＝1回」）、下に大きな数の行（count_fmt。例「1万回のうち {wins:,}回」）。
    勝ちが 200 以下なら、まれな勝ちを丸で囲んで見つけやすくする。t0〜t1 で埋まる（^1.7 で後半ほど速い）、t_count で下の行が出る。
    中心 cx・上端 y0・1マスの大きさ cell で位置が決まる（既定は桶狭間の左ページ中央 492・130・4.4px＝440px四方）。
    caption と count の文字は 40px 以上（既定 46 / 66）"""

    def __init__(self, wins, caption="", n=10000, side=100, seed=30, cx=492, y0=130.0, cell=4.4, t0=0.0, t1=8.0, t_cap=None,
                 t_count=None, count_fmt="1万回のうち {wins:,}回", cap_size=46, count_size=66, cap_y=None, count_y=None,
                 win_color=WIN_C, loss_color=LOSS_C, count_color=None, power=1.7, circle_rare=True):
        for nm, sz in (("cap_size", cap_size), ("count_size", count_size)):
            if sz < MIN_PANEL_TEXT:
                raise ValueError(f"GridPanel.{nm}={sz} は小さすぎる（{MIN_PANEL_TEXT}px 以上）")
        if wins < 0 or wins > n:
            raise ValueError("wins が 0〜n の外")
        self.wins, self.n, self.side, self.cell, self.cx, self.y0 = int(wins), n, side, cell, cx, y0
        self.px = int(round(side * cell))
        self.x0 = cx - self.px / 2
        self.t0, self.t1 = t0, t1
        self.t_cap = t0 - 0.4 if t_cap is None else t_cap
        self.t_count = t1 + 0.1 if t_count is None else t_count
        self.caption, self.count_fmt = caption, count_fmt
        self.cap_size, self.count_size = cap_size, count_size
        self.cap_y = y0 - 44 if cap_y is None else cap_y
        self.count_y = y0 + self.px + 100 if count_y is None else count_y
        self.count_color = count_color
        self.power, self.circle_rare = power, circle_rare
        v = np.zeros(n, bool)
        v[:self.wins] = True
        self.win = np.random.default_rng(seed).permutation(v)
        c, px = cell, self.px
        self.full = np.zeros((px, px, 4), np.uint8)
        self.idx = np.full((px, px), 10 ** 9, np.int64)
        self.win_xy = []
        lo, wi, em = hexrgb(loss_color), hexrgb(win_color), hexrgb(EMPTY_C)
        for i in range(n):
            r_, q_ = i // side, i % side
            ya, yb = int(round(r_ * c)), int(round((r_ + 1) * c)) - 1
            xa, xb = int(round(q_ * c)), int(round((q_ + 1) * c)) - 1
            col = wi if self.win[i] else lo
            self.full[ya:yb, xa:xb, 0] = int(col[2] * 255)             # cairo は BGRA
            self.full[ya:yb, xa:xb, 1] = int(col[1] * 255)
            self.full[ya:yb, xa:xb, 2] = int(col[0] * 255)
            self.full[ya:yb, xa:xb, 3] = 255
            self.idx[ya:yb, xa:xb] = i
            if self.win[i]:
                self.win_xy.append((i, self.x0 + (q_ + 0.5) * c, y0 + (r_ + 0.5) * c))
        self.empty = np.zeros_like(self.full)
        m = self.full[..., 3] > 0
        self.empty[m] = (int(em[2] * 255), int(em[1] * 255), int(em[0] * 255), 255)
        self._buf = None

    def filled(self, t):
        """時刻 t までに埋まったマスの数"""
        return int(round(self.n * clamp01((t - self.t0) / max(self.t1 - self.t0, 1e-6)) ** self.power))

    def draw(self, ctx, t, a=1.0):
        ac = a * _fade(t, self.t_cap, 0.4)
        if ac > 0.003 and self.caption:
            text(ctx, self.caption, self.cx, self.cap_y, self.cap_size, INK, alpha=ac)
        if t >= self.t0 - 0.4:
            n = self.filled(t)
            mask = (self.idx < n)[..., None]
            self._buf = np.ascontiguousarray(np.where(mask, self.full, self.empty))
            s = cairo.ImageSurface.create_for_data(memoryview(self._buf), cairo.FORMAT_ARGB32, self.px, self.px, self.px * 4)
            ctx.set_source_surface(s, self.x0, self.y0)
            ctx.paint_with_alpha(a * _fade(t, self.t0 - 0.4, 0.4))
            if self.circle_rare and self.wins <= 200:
                ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
                ctx.set_line_width(2.2)
                for i, x, y in self.win_xy:
                    if i < n:
                        ctx.new_sub_path()
                        ctx.arc(x, y, 7.5, 0, 2 * math.pi)
                ctx.stroke()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.rectangle(self.x0 - 4, self.y0 - 4, self.px + 6, self.px + 6)
            ctx.stroke()
        q = a * _fade(t, self.t_count, 0.4)
        if q > 0.003:
            col = self.count_color or (RED if self.wins else INK)
            text(ctx, self.count_fmt.format(wins=self.wins, n=self.n), self.cx, self.count_y, self.count_size, col, alpha=q)

    def cues(self, line_cap=None, line_count=None):
        """読み方(frame)と下の数の行(value)の記録。line_cap=その話を始める声の文 id"""
        out = []
        if line_cap:
            out.append(Cue("マス目 読み方の1行", "frame", self.t_cap, self.t_cap + 0.4, line_cap))
        if line_count:
            out.append(Cue("マス目 下の数の行", "value", self.t_count, self.t_count + 0.4, line_count))
        return out

    def check(self):
        """マス目の数と勝ちの数が合っているか（数えなおし）。問題の文字列のリスト"""
        probs = []
        if int(self.win.sum()) != self.wins:
            probs.append(f"勝ちのマス {int(self.win.sum())} ≠ {self.wins}")
        if self.side * self.side != self.n:
            probs.append(f"{self.side}×{self.side} ≠ {self.n}")
        return probs


# ============================================================
# 出典（クレジット）の置き場
# ============================================================

def draw_credit(ctx, lines, box, a=1.0, size=32):
    """出典の小さな白い箱（左ページの左下など）。28px 以上（スマホで読める下限）。何度も出さず、1回だけ出して消す。
    box=(x0, y0, x1, y1)。lines は短く折った行（各行の幅が箱に入ること）"""
    if size < 28:
        raise ValueError("出典は 28px 以上")
    if a <= 0.003:
        return
    ctx.set_source_rgba(1, 1, 1, 0.92 * a)
    rrect(ctx, box[0], box[1], box[2] - box[0], box[3] - box[1], 10)
    ctx.fill()
    step = (box[3] - box[1] - 20) / max(len(lines), 1)
    for k, ln in enumerate(lines):
        text(ctx, ln, box[0] + 14, box[1] + 18 + step * (k + 0.5), size, INK, align="left", alpha=a)


# ============================================================
# 4. チェック（題材に依存しない。箱の一覧・手がかりの一覧だけを受け取る）
# ============================================================
# frames = [(t, [(文字, x0, y0, x1, y1, 大きさ), ...]), ...]  ← scan_frames が作る形（core._LOG と同じ並び）

def scan_frames(draw, duration, step=0.25, scale=0.25, t_max=None, timeline=None):
    """0.25 秒ごとに draw を縮小して描き、画面の文字の箱を集める（1920×1080 の座標に戻す）。
    timeline を渡すと字幕の行の箱（「字幕: …」）も足す。戻り値は [(t, [(文字, x0, y0, x1, y1, size), …]), …]"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int((t_max or duration) / step)
    saved_log, saved_t = core._LOG, core._CUR_T
    try:
        for i in range(n + 1):
            t = i * step
            core._LOG = []
            core._CUR_T = t
            ctx = cairo.Context(surf)
            ctx.scale(scale, scale)
            draw(ctx, t)
            ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale, e[6] / scale) for e in core._LOG]
            if timeline is not None:
                ents += subtitle_boxes(timeline, t)
            frames.append((t, ents))
    finally:
        core._LOG, core._CUR_T = saved_log, saved_t
    return frames


def subtitle_boxes(timeline, t):
    """字幕の各行の箱（字幕は文字のログに入らないのでここで計算する。大きさは lf.SUB_SIZE）"""
    s_, a_ = timeline.subtitle_at(t)
    out = []
    if s_ and a_ > 0.3:
        lines = lf.wrap_subtitle(s_)
        n = len(lines)
        for i, l_ in enumerate(lines):
            w = text_width(l_, lf.SUB_SIZE)
            y = lf.SUB_Y - lf.SUB_LINE_H * (n - 1) / 2 + i * lf.SUB_LINE_H
            out.append(("字幕: " + l_, lf.W / 2 - w / 2, y - lf.SUB_SIZE * 0.55, lf.W / 2 + w / 2, y + lf.SUB_SIZE * 0.55, lf.SUB_SIZE))
    return out


def _is_exempt(label, exempt):
    if not exempt:
        return False
    if callable(exempt):
        return bool(exempt(label))
    return label in exempt


def text_box_overlaps(frames, exempt=(), shrink=2.0, skip=(), need=1, min_ratio=0.0):
    """(a) 文字の箱どうしの交わり。各コマで全ての組を調べ、面積が重なるものを [(t, 文字A, 文字B), …] で返す（空なら OK）。
    exempt=調べない文字（章カードなど。集合か関数）、skip=[(t0, t1), …] 調べない時間帯（終了画面への切りかえなど）、
    shrink=箱を縮めてから判定（px）、need=同じ組が何コマ続いたら数えるか（1=厳しい。okehazama は 3＝0.5秒以上）、
    min_ratio=重なり面積が小さいほうの箱の何割以上で数えるか（0=少しでも）。
    「前の絵が消えてから次が出る」の入れかえもこれで見張れる（0.25 秒ごとに全部調べる）。同じ文字どうしは数えない"""
    pairs, runs, seen = [], {}, set()
    for f in frames:
        t, ents = f[0], f[1]
        if any(a <= t < b for a, b in skip):
            runs = {}
            continue
        boxes = [(e[0], e[1] + shrink, e[2] + shrink, e[3] - shrink, e[4] - shrink) for e in ents if not _is_exempt(e[0], exempt)]
        hit = set()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] == b[0]:
                    continue
                w_ = min(a[3], b[3]) - max(a[1], b[1])
                h_ = min(a[4], b[4]) - max(a[2], b[2])
                if w_ > 0 and h_ > 0:
                    area = min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2]))
                    if area > 0 and w_ * h_ >= min_ratio * area:
                        hit.add(tuple(sorted((a[0], b[0]))))
        runs = {k: runs.get(k, 0) + 1 for k in hit}
        for k, c in runs.items():
            if need <= 1:
                pairs.append((t, k[0], k[1]))
            elif c >= need and k not in seen:
                seen.add(k)
                pairs.append((t, k[0], k[1]))
    return pairs


def collapse_overlaps(pairs, step=0.25):
    """text_box_overlaps の結果を、同じ組の続いた区間にまとめる → [(最初の時刻, 最後の時刻, 文字A, 文字B), …]"""
    spans = {}
    for t, a, b in pairs:
        spans.setdefault((a, b), []).append(t)
    out = []
    for (a, b), ts in spans.items():
        ts.sort()
        s = p = ts[0]
        for x in ts[1:]:
            if x - p > step * 1.5:
                out.append((s, p, a, b))
                s = x
            p = x
        out.append((s, p, a, b))
    return sorted(out)


def write_overlap_report(path, frames, pairs, notes=(), step=0.25):
    """overlap_report.md を書く（伊能忠敬と同じ形）。notes=数えなかったものの説明"""
    n_txt = sum(len(f[1]) for f in frames)
    t_end = frames[-1][0] if frames else 0
    rows = ["# 文字の箱の交わりの機械検査（engine/longkit.py text_box_overlaps）", "",
            f"- 調べたコマ: {len(frames)}（{step}秒ごと・0〜{t_end:.1f}秒）／文字の箱（字幕の行を含む）のべ {n_txt} 個",
            "- 各コマで、すべての文字の箱の組を調べ、面積が重なるものを数えた", *[f"- {s}" for s in notes], "",
            f"## 結果: 交わり {len(pairs)} 件（期待は 0）", ""]
    if pairs:
        rows += ["| 時刻 | 文字A | 文字B |", "|---|---|---|"] + [f"| {_ts(t)} | {a} | {b} |" for t, a, b in pairs[:200]]
    Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")


def _ts(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def min_text_size(frames, min_px=MIN_PANEL_TEXT, exempt=(), overrides=None):
    """(c) スマホで読める大きさの確認。min_px 未満の文字を [(t, 文字, 大きさ), …]（同じ文字・大きさは最初の1回）で返す。
    1920 幅で 40px は、幅 480px に縮めると 10px。字幕は含めない（subtitle_boxes は frames に入れない／exempt に「字幕: 」で始まるものを入れる）。
    overrides={文字: そのまま許す最小px}（出典の 28px など）"""
    overrides = overrides or {}
    out, seen = [], set()
    for t, ents in ((f[0], f[1]) for f in frames):
        for e in ents:
            lab, size = e[0], e[5]
            if _is_exempt(lab, exempt) or lab.startswith("字幕: "):
                continue
            lim = overrides.get(lab, min_px)
            if size < lim - 0.5 and (lab, round(size)) not in seen:
                seen.add((lab, round(size)))
                out.append((t, lab, size))
    return out


def outside_area(frames, x=(48, 1872), y=(36, 1044), exempt=(), skip=()):
    """画面の端に近い文字（公開前チェックと同じ範囲 x 48〜1872・y 36〜1044）。[(t, 文字, 箱), …]"""
    out, seen = [], set()
    for t, ents in ((f[0], f[1]) for f in frames):
        if any(a <= t < b for a, b in skip):
            continue
        for e in ents:
            if _is_exempt(e[0], exempt) or e[0].startswith("字幕: "):
                continue
            if e[1] < x[0] or e[3] > x[1] or e[2] < y[0] or e[4] > y[1]:
                if (e[0], round(e[1]), round(e[2])) not in seen:
                    seen.add((e[0], round(e[1]), round(e[2])))
                    out.append((t, e[0], tuple(round(v) for v in e[1:5])))
    return out


def credit_check(frames, credit_lines, min_px=28, page_right=945, max_span=20.0):
    """出典の行が「1回だけ・左ページ内・28px以上・max_span 秒以内」で出ているか。問題の文字列のリスト"""
    cr = [(t, e) for t, ents in ((f[0], f[1]) for f in frames) for e in ents if e[0] in set(credit_lines)]
    if not cr:
        return ["出典が画面にない"]
    ts = sorted({t for t, _e in cr})
    probs = []
    if ts[-1] - ts[0] > max_span:
        probs.append(f"出典が {ts[-1] - ts[0]:.1f} 秒も出ている（{max_span:.0f}秒以内）")
    if min(e[5] for _t, e in cr) < min_px - 0.5:
        probs.append(f"出典が {min_px}px 未満")
    if any(e[3] > page_right for _t, e in cr):
        probs.append("出典が左ページからはみ出す")
    return probs


# ---- visual_lag（絵は声より先に）----

def _line_start(lines, lid):
    if hasattr(lines, "start"):
        return lines.start(lid)
    v = lines[lid]
    return v[0] if isinstance(v, (tuple, list)) else v


def _line_text(lines, lid):
    try:
        if hasattr(lines, "clip"):
            return lines.clip(lid).text
        v = lines[lid]
        return v[1] if isinstance(v, (tuple, list)) and len(v) > 1 else ""
    except Exception:
        return ""


def visual_lag(cues, lines, lead=FRAME_LEAD, frame_kinds=("frame",)):
    """(b) 絵が声より遅れていないか。cues=Cue の一覧（panel.cues() など。name・kind・ready・line を持つもの）、
    lines=lf.Timeline、または {文の id: 頭の時刻 or (頭の時刻, 文)} の辞書。
    戻り値 (rows, violations): rows=[(絵, 絵がそろう時刻, 声の文の頭, 遅れ), …]（遅れ＝ready − 文の頭。大きい順。マイナスなら絵が先）。
    violations=rows のうち、frame 型の絵が文の頭の lead 秒前（既定0.5）までにそろわないもの（遅れ > −lead）。
    'value' 型（答えの数字）は声に合わせてよいので violations には入れない → 声より先に出すぎは value_spoilers で見る。
    line を持たない cue は飛ばす"""
    rows, bad = [], []
    for c in cues:
        if not getattr(c, "line", None):
            continue
        ls = _line_start(lines, c.line)
        lag = c.ready - ls
        row = (c.name, c.ready, ls, lag)
        rows.append(row)
        if c.kind in frame_kinds and lag > -lead + 1e-9:
            bad.append(row)
    rows.sort(key=lambda r: -r[3])
    bad.sort(key=lambda r: -r[3])
    return rows, bad


def value_spoilers(cues, lines, tol=0.3):
    """答えの数字（kind='value'）が、声の文の頭より tol 秒以上早く出始めていないか（答えが先に見えると驚きが減る）。
    [(絵, 出はじめ, 声の文の頭, 早さ), …]"""
    out = []
    for c in cues:
        if c.kind == "value" and c.line:
            ls = _line_start(lines, c.line)
            if c.start < ls - tol:
                out.append((c.name, c.start, ls, ls - c.start))
    return out


def write_visual_lag_md(path, rows, violations, lead=FRAME_LEAD):
    """visual_lag.md を書く（伊能忠敬と同じ表）。rows・violations は visual_lag の戻り値"""
    md = ["# 絵が出そろう時刻 − その絵を言う声の文の頭（visual_lag）", "",
          "- 遅れ ＝ 絵が読める（描ききった）時刻 − その絵のことを言う声の文が始まる時刻。プラスなら、声が言い始めてから絵がそろう",
          f"- 枠（frame）は遅れ ≦ −{lead} 秒（声の{lead}秒前までにそろう）が条件。答えの数字（value）は声に合わせてよい",
          f"- 調べた合図 {len(rows)} 件のうち、条件を外れる frame 型: **{len(violations)} 件**", "",
          "| 遅れ(秒) | 絵 | 声の文の頭 | 絵がそろう |", "|---|---|---|---|"]
    bad = {v[0] for v in violations}
    for name, ready, ls, lag in rows:
        md.append(f"| {lag:+.1f}{' ✗' if name in bad else ''} | {name} | {_ts(ls)} | {_ts(ready)} |")
    Path(path).write_text("\n".join(md) + "\n", encoding="utf-8")


# ============================================================
# 5. small（30MB未満のプレビュー）
# ============================================================

def small(src, dst=None, max_mb=30.0, crf=28, audio_k=96):
    """ffmpeg でプレビュー用に縮める（幅1280・crf28・aac 96k）。max_mb（既定30MB）を超えたら crf を上げてやり直す（最大 36）。
    dst 省略時は <src>.small.mp4。戻り値は書き出したパス。本番の mp4 は縮めない（これは確認用）"""
    src = Path(src)
    dst = Path(dst) if dst else src.with_name(src.stem + ".small.mp4")
    c = crf
    while True:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", "scale=1280:-2", "-c:v", "libx264",
               "-crf", str(c), "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", f"{audio_k}k",
               "-movflags", "+faststart", str(dst)]
        subprocess.run(cmd, check=True)
        mb = dst.stat().st_size / 1024 / 1024
        if mb <= max_mb or c >= 36:
            break
        c += 2
    print(f"プレビュー: {dst}（{mb:.1f}MB・crf {c}）" + ("" if mb <= max_mb else f"  ← {max_mb:.0f}MB を超えている"))
    return dst


# ============================================================
# 区切り（アイキャッチ）— 2026-10-25 追加。kaidan-long / reji-long / densha-long の「ここまで／ここから」を部品にしたもの
# ============================================================

class Eyecatch:
    """章と章のあいだの区切り（声なし・既定 4 秒）。見開きの左ページに「ここまで」＋左向きの赤い矢印＋ここまでのまとめ2行、
    右ページに「ここから」＋右向きの赤い矢印＋これから確かめること2行。亀（engine/brand.py の turtle）が左ページから右ページへ歩き、
    足あとの点が順に出る（点が出る時刻に足音を鳴らす → step_times()）。見た目は kaidan-long.py の eyecatch と同じ。

    前提（呼び出し側の責任）: 区切りの間は **この部品だけが見える**。draw は自前で見開きの紙（lf.spread）を敷いて描くが、
    前の章の付せん・表・字幕以外の動く絵は、[t0, t1] の間は呼び出し側で描かないこと（紙の上に重なって見える）。
    章には数えず（chapters.txt に入れない）、早回しの照合・声の照合からも外す。台本には
    「- （無音 4秒・区切り。左ページにここまで、右ページにここから。カメが歩く）」を次の章の見出しの直前に置く。
    入りは 0.3秒で現れ、t1 から 0.35秒で消える（draw は t0 〜 t1+0.35 の間だけ描く。次の章は t1 から始める）。

    left / right: (1行目, 2行目)。文字は幅 820px に収まるよう 66px から縮める（40px 未満になる長さは ValueError）。
    pause: None なら止まらずに歩く。(0.5, 0.7) のように (歩く道のりの割合, 止まる秒) を渡すと、そこで止まって1回まばたきする（付せんは出さない）。
    """
    TURTLE_S = 0.5            # 亀の倍率（kaidan と同じ）
    Y = 860                   # 亀の高さ
    X0, X1 = 330.0, 1590.0    # 亀が歩く範囲（左ページ → 右ページ）
    FOOT_X0, FOOT_DX, FOOT_BEHIND = 260.0, 64.0, 70.0
    MIN_TEXT = 40

    def __init__(self, t0, left, right, dur=4.0, lx=480, rx=1440, pause=None):
        self.t0, self.dur = float(t0), float(dur)
        self.t1 = self.t0 + self.dur
        self.left, self.right = tuple(left), tuple(right)
        self.lx, self.rx = lx, rx
        self.pause = pause
        if len(self.left) != 2 or len(self.right) != 2:
            raise ValueError("左右とも2行（文字列2つ）で渡す")
        if self.dur < 2.5:
            raise ValueError("区切りは 2.5秒以上（亀が歩ききれない）")
        self._sizes = {}
        for s in self.left + self.right:
            sz = min(66, int(66 * 820 / text_width(s, 66)))
            if sz < self.MIN_TEXT:
                raise ValueError(f"区切りの文字が{sz}px になる（{self.MIN_TEXT}px 未満）: {s!r} — 短くする")
            self._sizes[s] = sz

    # ---- 時刻 ----
    def _u(self, t):
        """亀の道のり 0→1（止まる間は一定）"""
        tr = clamp01((t - self.t0) / self.dur) * self.dur
        if not self.pause:
            return tr / self.dur
        pu, pd = self.pause
        walk = self.dur - pd
        tp = pu * walk
        if tr < tp:
            return tr / walk
        if tr < tp + pd:
            return pu
        return (tr - pd) / walk

    def _t_at_u(self, u):
        """道のり u に亀が着く時刻"""
        if not self.pause:
            return self.t0 + u * self.dur
        pu, pd = self.pause
        walk = self.dur - pd
        return self.t0 + u * walk + (pd if u > pu else 0.0)

    def alpha(self, t):
        return ease_out(clamp01((t - self.t0) / 0.3)) * (1 - clamp01((t - self.t1) / 0.35))

    def _foots(self):
        out, i = [], 0
        while True:
            px = self.FOOT_X0 + i * self.FOOT_DX
            u = (px + self.FOOT_BEHIND - self.X0) / (self.X1 - self.X0)
            if u > 1.0:
                break
            out.append((px, self._t_at_u(max(0.0, u))))
            i += 1
        return out

    def step_times(self):
        """足あとの点が出る時刻の一覧（足音を鳴らす所）。例: for i, ts in enumerate(ey.step_times()): mx.add(ts, turtle_step(seed=i, high=bool(i % 2)), 0.32)"""
        return [tf for _px, tf in self._foots()]

    def still_times(self):
        """静止画で確かめる時刻（始め・途中・終わり）。始め＝0.5秒後、途中＝半分、終わり＝t1 の 0.5秒前"""
        return [self.t0 + 0.5, self.t0 + self.dur * 0.5, self.t1 - 0.5]

    def texts(self):
        """区切りの間に出る文字の集合（照合用）。{'ここまで', 'ここから', 左の2行, 右の2行}"""
        return {"ここまで", "ここから", *self.left, *self.right}

    # ---- 描画 ----
    def _page(self, ctx, t, cx, head, lines, back):
        a = ease_out(clamp01((t - self.t0) / 0.5))
        w = text_width(head, 104)
        _hand_title(ctx, head, cx - w / 2, 250, 104, seed=4 if back else 6, alpha=a)
        pr = clamp01((t - self.t0 - 0.1) / 0.4)
        if back:
            self._arrow(ctx, cx + 210, cx - 230, 345, 11, pr)
        else:
            self._arrow(ctx, cx - 210, cx + 230, 345, 21, pr)
        for i, s_ in enumerate(lines):
            text(ctx, s_, cx, 520 + i * 96, self._sizes[s_], INK, alpha=a)

    @staticmethod
    def _arrow(ctx, x0, x1, y, seed, progress):
        pen_line(ctx, x0, y, x1, y, RED, seed=seed, width=7, progress=progress)
        if progress >= 1:
            d = 1 if x1 > x0 else -1
            pen_line(ctx, x1, y, x1 - d * 34, y - 24, RED, seed=seed + 1, width=7)
            pen_line(ctx, x1, y, x1 - d * 34, y + 24, RED, seed=seed + 2, width=7)

    def _scene(self, ctx, t):
        from engine.brand import turtle
        lf.spread(ctx)
        self._page(ctx, t, self.lx, "ここまで", self.left, True)
        self._page(ctx, t, self.rx, "ここから", self.right, False)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:
                ctx.set_source_rgba(0.25, 0.25, 0.3, 0.30 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, self.Y + 18 + (7 if i % 2 else -7), 6, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        tr = t - self.t0
        resting = bool(self.pause) and self.pause[0] - 1e-6 <= u <= self.pause[0] + 1e-6 and \
            self._t_at_u(self.pause[0]) <= t < self._t_at_u(self.pause[0]) + self.pause[1]
        if resting:
            tp = t - self._t_at_u(self.pause[0])
            blink = 1.0 if self.pause[1] * 0.35 < tp < self.pause[1] * 0.35 + 0.14 else 0.0
            bob = 0.0
        else:
            blink = 1.0 if 0.35 < tr % 1.8 < 0.47 else 0.0
            bob = 3 * abs(math.sin(tr * 6.0))
        turtle(ctx, x, self.Y - bob, self.TURTLE_S, blink=blink)

    def draw(self, ctx, t):
        """t0 〜 t1+0.35 の間だけ描く（それ以外は何もしない）。見開きの紙ごと描く。"""
        a = self.alpha(t)
        if a <= 0.003:
            return
        if a >= 0.997:
            self._scene(ctx, t)
            return
        ctx.push_group()
        self._scene(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def _hand_title(ctx, s, x, y, size, seed, alpha=1.0, color=INK):
    """1字ずつ少し傾けた手書きの見出し（kaidan-long.py の hand_title と同じ）。重なりの検査には1行として記録する"""
    from engine import note
    saved = core._LOG
    core._LOG = None
    w = note.hand_text(ctx, s, x, y, size, color, seed=seed, alpha=alpha)
    core._LOG = saved
    if saved is not None and alpha > 0.1:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((x, y - size / 2), (x + w, y + size / 2))))
        saved.append((core._CUR_T, s, min(xs), min(ys), max(xs), max(ys), abs(ctx.user_to_device_distance(0, size)[1])))
    return w
