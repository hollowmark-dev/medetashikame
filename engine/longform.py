"""横型ロング（1920×1080・8〜9分・合成音声のナレーション付き）の共通部品。

ショート用の engine/core.py・note.py・parts.py には手を入れず、ここに足す（仕様: research/longform_engine_spec.md）。
文字の描画は core.text（手書き体・ログ記録）、色とペンは note をそのまま使うので、ショートと同じ見た目になる。
core.W/H は縦（1080×1920）のまま。ここでは longform の W, H（1920×1080）を使う。

使い方（sims/ の1本で）:
    from engine import longform as lf
    lf.use()
    tl = lf.Timeline([lf.Chapter("はじめに"), lf.Line("a1", "バス停に、1人の人がやってきました。"), ...], cache_dir)
    def draw(ctx, t):
        lf.spread(ctx)                                 # 見開きのノート
        lf.write_on(ctx, "平均10分おき", 1415, 300, 56, INK, clamp01((t - tl.start("a1")) / lf.write_dur("平均10分おき")))
        lf.chapter_card_at(ctx, t, tl)                  # 章の始まりに付箋
        lf.subtitle(ctx, t, tl)                         # 下の帯に今の台詞
    mx = lf.LongMixer(tl.duration); tl.add_voice(mx); mx.add(0, core.pad(tl.duration), 1.0, bgm=True)
    lf.render(draw, tl.duration, out / "x.mp4", mx, timeline=tl)       # preview=True で 960×540・15fps
    lf.stills(draw, [10, 30, 60], out / "stills")
"""
import bisect
import math
import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import cairo
import numpy as np

import engine.core as core
from engine.core import SR, clamp01, ease, ease_out, fill, hexrgb, rrect, text
from engine import note
from engine.note import GRID, INK, MARKER, PAPER, PENCIL, RED, STICKY, hand_text, legend, pen_circle, pen_line, sticky

W, H, FPS = 1920, 1080, 30

# 紙（見開き）。毎コマは描かず1枚作って貼る
GUTTER = 960                          # のど（中央の綴じ目）
LEFT = (110, 90, 900, 940)            # 左ページの中身を置く箱（x0, y0, x1, y1）
RIGHT = (1020, 90, 1810, 940)         # 右ページ
SUB_Y = 1000                          # 字幕の中心の高さ（下の帯 940〜1060 は字幕専用）
GRID_STEP = 45                        # note.paper と同じ方眼

# 字幕
SUB_SIZE = 40
SUB_LINE_H = 48
SUB_MAX = 28                          # 1行の最大字数
SUB_FADE = 0.12                       # 行と行の切り替えのフェード（秒）
SUB_HOLD = 0.2                        # 言い終わってから字幕を残す長さ（秒。間より長くしない）

# 書き進む文字
WRITE_CPS = 9.0                       # 1秒に書く字数の目安
WRITE_FADE = 0.08                     # 現れる字のフェード（秒）

# 音
VOICE_RMS = 0.12                      # 声の平均の大きさ（1行ごとにそろえる）
SFX_GAIN = 0.5                        # 効果音の音量（note.use() と同じ 0.5）
BGM_GAIN = 1.0
DUCK_DB = -10.0                       # 声が出ている間の BGM
DUCK_DOWN = 0.3                       # 下げるのにかける秒数
DUCK_UP = 0.6                         # 戻すのにかける秒数
DUCK_HOLD = 0.5                       # 声が切れてもこの間は下げたまま（行の間の短い間でBGMが跳ねない）

# 公開前チェック（ロング用。縦用の SAFE_* は使わない）
PF_X = (48, 1872)
PF_Y = (36, 1044)
PF_MIN_TEXT = 26
PF_MIN_LEN = 8 * 60                   # これより短いと注意（止めない）

_PAPERS = {}


def use():
    """このあと描く文字を手書き風（Klee One をファイルから・縁取り）にする。core.W/H は書き換えない"""
    note.use()


# ---------- 紙（見開き） ----------

def _make_spread():
    saved_log, core._LOG = core._LOG, None     # 日付欄は飾り。公開前チェックに入れない
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    fill(c, PAPER)
    c.paint()
    # 方眼（のどから左右対称に引く。のどから5本ごとに濃い線）
    c.set_line_width(1.5)
    for k in range(0, 22):
        for sgn in (-1, 1):
            x = GUTTER + sgn * k * GRID_STEP
            if k == 0 or not 0 <= x <= W:
                continue
            c.set_source_rgba(*hexrgb(GRID, 1 if k % 5 == 0 else 0.55))
            c.move_to(x + 0.5, 0)
            c.line_to(x + 0.5, H)
            c.stroke()
    for y in range(0, H + 1, GRID_STEP):
        c.set_source_rgba(*hexrgb(GRID, 1 if y % (GRID_STEP * 5) == 0 else 0.55))
        c.move_to(0, y + 0.5)
        c.line_to(W, y + 0.5)
        c.stroke()
    # 紙のざらつき（note.paper と同じ）
    rng = np.random.default_rng(3)
    buf = np.ndarray((H, W, 4), np.uint8, s.get_data())
    noise = rng.normal(0, 3.2, (H, W, 1))
    from PIL import Image
    low = Image.fromarray(np.uint8(np.clip(128 + rng.normal(0, 40, (H // 80 + 2, W // 80 + 2)), 0, 255)))
    blot = (np.asarray(low.resize((W, H), Image.BICUBIC), np.float32)[:, :, None] - 128) / 40 * 2.0
    buf[:, :, :3] = np.clip(buf[:, :, :3].astype(np.float32) + noise + blot, 0, 255).astype(np.uint8)
    s.mark_dirty()
    # のどの影（綴じ目のくぼみ）: 中央が一番濃く、左右へなめらかに消える
    g = cairo.LinearGradient(GUTTER - 70, 0, GUTTER + 70, 0)
    for u, al in ((0.0, 0.0), (0.25, 0.07), (0.42, 0.22), (0.5, 0.34), (0.58, 0.22), (0.75, 0.07), (1.0, 0.0)):
        g.add_color_stop_rgba(u, 0.22, 0.17, 0.08, al)
    c.set_source(g)
    c.rectangle(GUTTER - 70, 0, 140, H)
    c.fill()
    c.set_source_rgba(0.2, 0.15, 0.06, 0.28)                    # 綴じ目の筋
    c.set_line_width(2)
    c.move_to(GUTTER + 0.5, 0)
    c.line_to(GUTTER + 0.5, H)
    c.stroke()
    # 左右のページの端にうっすら影（外側ほど暗く）。端の数本は重なったページ
    for x0, sgn in ((0, 1), (W, -1)):
        g = cairo.LinearGradient(x0, 0, x0 + sgn * 46, 0)
        g.add_color_stop_rgba(0, 0.2, 0.15, 0.06, 0.2)
        g.add_color_stop_rgba(1, 0.2, 0.15, 0.06, 0.0)
        c.set_source(g)
        c.rectangle(min(x0, x0 + sgn * 46), 0, 46, H)
        c.fill()
        for i, al in enumerate((0.16, 0.1, 0.06)):
            c.set_source_rgba(0.25, 0.2, 0.1, al)
            c.set_line_width(1.5)
            c.move_to(x0 + sgn * (6 + i * 5), 0)
            c.line_to(x0 + sgn * (6 + i * 5), H)
            c.stroke()
    for y0, sgn in ((0, 1), (H, -1)):
        g = cairo.LinearGradient(0, y0, 0, y0 + sgn * 26)
        g.add_color_stop_rgba(0, 0.2, 0.15, 0.06, 0.12)
        g.add_color_stop_rgba(1, 0.2, 0.15, 0.06, 0.0)
        c.set_source(g)
        c.rectangle(0, min(y0, y0 + sgn * 26), W, 26)
        c.fill()
    core._LOG = saved_log
    return s


def spread(ctx):
    """方眼の見開き（のどの影・ページ端の影・紙のざらつき）。日付欄は無い（2026-10-04 ユーザー指示）。1枚作って貼る。
    ctx が 0.5 倍（preview）なら半分の大きさに縮めたものを貼る（毎コマの縮小を避ける）"""
    sc = ctx.get_matrix().xx
    half = abs(sc - 0.5) < 0.01
    key = half
    surf = _PAPERS.get(key)
    if surf is None:
        full = _PAPERS.get(False)
        if full is None:
            full = _PAPERS[False] = _make_spread()
        if half:
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // 2, H // 2)
            c = cairo.Context(surf)
            c.scale(0.5, 0.5)
            c.set_source_surface(full, 0, 0)
            c.get_source().set_filter(cairo.FILTER_BEST)
            c.get_source().set_extend(cairo.EXTEND_PAD)    # 縁が半透明になって、1コマ目だけ縁が違う色になるのを防ぐ
            c.paint()
        else:
            surf = full
        _PAPERS[key] = surf
    ctx.save()
    if half:
        ctx.scale(2, 2)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()
    ctx.restore()


# ---------- 台本 → 時間割 ----------

@dataclass
class Line:
    """ナレーション1文。pause は言い終わってからの間（秒）。speed は None なら voice の既定"""
    id: str
    text: str
    pause: float = 0.35
    speed: float = None


@dataclass
class Gap:
    """声のない区間（1万人モードなど）"""
    id: str
    seconds: float


@dataclass
class Chapter:
    """章の始まり（YouTube のチャプターと章カード）。gap は章カードだけが出ている間（次の声までの無音）"""
    title: str
    id: str = None
    gap: float = 0.8


class Timeline:
    """台本から時刻を確定する。コンストラクタ内で voice.synth して（キャッシュがあれば合成せず）長さを得る。
    synth= は差し替え用（テストで無音の偽物を渡す）。省略時は engine.voice.synth（先に ensure_engine する）"""

    def __init__(self, items, cache_dir, lead=1.0, synth=None, tail=0.0):
        self.items = list(items)
        self.cache_dir = Path(cache_dir)
        self.lead = lead
        if synth is None:
            from engine import voice
            voice.ensure_engine()
            synth = voice.synth
        self._t = {}            # id -> (start, end)
        self._clips = {}        # Line.id -> Clip
        self._lines = []        # (start, end, pause, Line, Clip) 時刻順
        self.chapters = []      # [(t, title)]
        cur = 0.0
        first_line = True
        for it in self.items:
            if isinstance(it, Chapter):
                self.chapters.append((cur, it.title))
                if it.id:
                    self._reg(it.id, cur, cur)
                cur += it.gap
            elif isinstance(it, Gap):
                self._reg(it.id, cur, cur + it.seconds)
                cur += it.seconds
            elif isinstance(it, Line):
                clip = synth(it.text, self.cache_dir) if it.speed is None else \
                    synth(it.text, self.cache_dir, speed=it.speed)
                if first_line:
                    cur = max(cur, lead)
                    first_line = False
                s, e = cur, cur + clip.duration
                self._reg(it.id, s, e)
                self._clips[it.id] = clip
                self._lines.append((s, e, it.pause, it, clip))
                cur = e + it.pause
            else:
                raise TypeError(f"Line / Gap / Chapter 以外が入っています: {it!r}")
        self.duration = cur + tail
        self._starts = [x[0] for x in self._lines]
        for s, _e, _p, ln, clip in self._lines:
            n = len(clip.text)
            if n > SUB_MAX * 2:
                print(f"  注意: 字幕が{n}字で2行に収まらない（{ln.id}）。文を分けてください")

    def _reg(self, id_, s, e):
        if id_ in self._t:
            raise ValueError(f"id が重複しています: {id_}")
        self._t[id_] = (s, e)

    def start(self, id_):
        return self._t[id_][0]

    def end(self, id_):
        return self._t[id_][1]

    def clip(self, id_):
        return self._clips[id_]

    def line_at(self, t):
        """今しゃべっている Line（声の区間 start ≤ t < end）。いなければ None"""
        i = bisect.bisect_right(self._starts, t) - 1
        if i >= 0 and t < self._lines[i][1]:
            return self._lines[i][3]
        return None

    def subtitle_at(self, t):
        """字幕用: (表示する文字, 0〜1 の濃さ)。言い終わって SUB_HOLD 秒まで残し、前後 SUB_FADE 秒でフェード"""
        i = bisect.bisect_right(self._starts, t) - 1
        if i < 0:
            return None, 0.0
        s, e, pause, _ln, clip = self._lines[i]
        e_vis = e + min(pause, SUB_HOLD)
        if t >= e_vis:
            return None, 0.0
        a = clamp01((t - s) / SUB_FADE) * clamp01((e_vis - t) / SUB_FADE)
        return clip.text, a

    def chapter_at(self, t):
        """いまの章 (index, 開始時刻, タイトル)。始まる前なら None"""
        i = bisect.bisect_right([c[0] for c in self.chapters], t) - 1
        if i < 0:
            return None
        return i, self.chapters[i][0], self.chapters[i][1]

    def add_voice(self, mixer):
        """全 Line の音を mixer.voice に置く"""
        for s, _e, _p, _ln, clip in self._lines:
            mixer.add_voice(s, clip.samples())

    def _chapter_rows(self):
        rows = [(t, title) for t, title in self.chapters]
        if rows and rows[0][0] > 0.01:
            # YouTube の決まり: 最初のチャプターは 0:00。すぐ始まるなら 0:00 に寄せ、遠いなら「はじめに」を足す
            rows = [(0.0, rows[0][1])] + rows[1:] if rows[0][0] < 5 else [(0.0, "はじめに")] + rows
        return rows

    def chapter_text(self):
        """概要欄用 "0:00 タイトル\\n1:12 …"（最初は 0:00・3つ以上・各10秒以上が YouTube の決まり。外れたら注意を出す）"""
        rows = self._chapter_rows()
        if len(rows) < 3:
            print(f"  注意: チャプターが{len(rows)}つ（YouTube は3つ以上で有効）")
        ends = [r[0] for r in rows[1:]] + [self.duration]
        for (t, title), e in zip(rows, ends):
            if e - t < 10:
                print(f"  注意: チャプター「{title}」が{e - t:.1f}秒（YouTube は各10秒以上）")
        return "\n".join(f"{_mmss(t)} {title}" for t, title in rows)


def _mmss(t):
    t = int(t)
    if t >= 3600:
        return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"
    return f"{t // 60}:{t % 60:02d}"


# ---------- 字幕 ----------

_NOBREAK_BEFORE = set("、。，．，！？!?）」』】〕ゃゅょっャュョッーぁぃぅぇぉ%％")
_BREAK_AFTER_STRONG = set("、。，！？!?")
_BREAK_AFTER_WEAK = set("はがをにでとのもへやよねか")
_WRAP_CACHE = {}


def wrap_subtitle(s, limit=SUB_MAX):
    """1行 limit 字まで。超えたら読点や助詞の後ろで、なるべく均等に折る（2行が基本、収まらなければ行を増やす）"""
    s = s.replace("\n", "")
    hit = _WRAP_CACHE.get((s, limit))
    if hit is not None:
        return hit
    out = _wrap(s, limit)
    _WRAP_CACHE[(s, limit)] = out
    return out


def _wrap(s, limit):
    n = len(s)
    if n <= limit:
        return [s]
    k = math.ceil(n / limit)
    ideal = n / k
    lo, hi = max(1, n - limit * (k - 1)), min(limit, n - 1)
    best, bs = None, 1e9
    for p in range(lo, hi + 1):
        sc = abs(p - ideal)
        prev, nxt = s[p - 1], s[p]
        if prev in _BREAK_AFTER_STRONG:
            sc -= 6
        elif prev in _BREAK_AFTER_WEAK:
            sc -= 3
        if nxt in _NOBREAK_BEFORE:
            sc += 20
        if prev.isascii() and nxt.isascii() and prev.isalnum() and nxt.isalnum():
            sc += 20                                   # 英数字の途中では折らない
        if sc < bs:
            best, bs = p, sc
    if best is None:
        best = min(limit, n - 1)
    return [s[:best]] + _wrap(s[best:], limit)


def subtitle(ctx, t, timeline):
    """今の行を下の帯（y 940〜1060）に。白い半透明（0.85）の角丸の帯＋INK の文字、40px。公開前チェックの対象外"""
    s, a = timeline.subtitle_at(t)
    if not s or a <= 0.01:
        return
    lines = wrap_subtitle(s)
    saved_log, core._LOG = core._LOG, None
    n = len(lines)
    w = max(core.text_width(l, SUB_SIZE) for l in lines) + 72
    h = n * SUB_LINE_H + 24
    fill(ctx, (1, 1, 1, 0.85 * a))
    rrect(ctx, W / 2 - w / 2, SUB_Y - h / 2, w, h, 22)
    ctx.fill()
    top = SUB_Y - SUB_LINE_H * (n - 1) / 2
    for i, l in enumerate(lines):
        text(ctx, l, W / 2, top + i * SUB_LINE_H, SUB_SIZE, INK, alpha=a)
    core._LOG = saved_log


# ---------- 章カード・書き進む文字 ----------

def chapter_card(ctx, title, a, x=GUTTER, y=470, size=64, color="yellow"):
    """章の始まりの付箋（既定は見開きの中央）。a は 0〜1 の濃さ（出入りは呼び出し側。ふわっと膨らんで出る）"""
    if a <= 0:
        return
    sc = 0.9 + 0.1 * ease_out(a)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    sticky(ctx, title, 0, 0, size, color, a=a, tilt=-0.025)
    ctx.restore()


def chapter_card_at(ctx, t, timeline, hold=2.6, fade_in=0.35, fade_out=0.4, **kw):
    """章が始まってから hold 秒だけ、その章の付箋を出す（出入りのフェード付き）。draw から毎コマ呼ぶだけ"""
    ch = timeline.chapter_at(t)
    if ch is None:
        return
    _i, t0, title = ch
    age = t - t0
    if age < 0 or age > hold:
        return
    a = clamp01(age / fade_in) * clamp01((hold - age) / fade_out)
    chapter_card(ctx, title, a, **kw)


def write_dur(s, cps=WRITE_CPS):
    """書き進むのにかける秒数の目安（改行は数えない）"""
    return max(0.2, len(s.replace("\n", "")) / cps)


def write_on(ctx, s, x, y, size, color=INK, progress=1.0, align="left", bold=True, alpha=1.0):
    """手書きで書き進む文字。progress 0→1 で1字ずつ現れる（現れる字は WRITE_FADE 秒でフェード）。
    文字列全体を core.text で描き（画像はキャッシュが効く）、見えている幅の右端だけグラデーションで消す。
    位置は書き終わりの位置に固定（書いている途中で行が動かない）。改行は1行ずつ順に書く"""
    p = clamp01(progress)
    if p <= 0 or not s:
        return
    if p >= 1:
        text(ctx, s, x, y, size, color, align=align, bold=bold, alpha=alpha)
        return
    lines = s.split("\n")
    n = sum(len(l) for l in lines)
    f = WRITE_FADE * WRITE_CPS                  # フェードの幅（字数換算）
    pos = p * (n + f)
    lh = size * 1.25
    top = y - lh * (len(lines) - 1) / 2
    base = 0
    for i, line in enumerate(lines):
        c = len(line)
        local = pos - base
        base += c
        if c == 0:
            continue
        if local <= 0:
            break
        cy = top + i * lh
        adv = core.text_width(line, size, bold)
        tx = x - adv / 2 if align == "center" else (x - adv if align == "right" else x)
        if local - f >= c:
            text(ctx, line, tx, cy, size, color, align="left", bold=bold, alpha=alpha)
            continue

        def xat(u):
            u = max(0.0, min(float(c), u))
            k = min(int(u), c - 1)
            w0 = core.text_width(line[:k], size, bold) if k else 0.0
            w1 = core.text_width(line[:k + 1], size, bold)
            return w0 + (w1 - w0) * (u - k)

        xa, xb = tx + xat(local - f), tx + xat(local)
        ctx.save()
        ctx.rectangle(tx - size * 0.3, cy - size * 0.95, adv + size * 0.6, size * 1.9)
        ctx.clip()
        ctx.push_group()
        text(ctx, line, tx, cy, size, color, align="left", bold=bold, alpha=alpha)
        ctx.pop_group_to_source()
        g = cairo.LinearGradient(xa, 0, max(xb, xa + 1), 0)
        g.add_color_stop_rgba(0, 0, 0, 0, 1)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.mask(g)
        ctx.restore()


# ---------- 音 ----------

class LongMixer:
    """声のバス・効果音・BGM。声は1行ごとに平均の大きさ（RMS）をそろえ、BGM は声が出ている間 約 -10dB に下げ、
    最後に軽いリミッター（tanh）をかけてステレオ 48kHz 16bit の WAV にする"""

    def __init__(self, duration):
        n = int(SR * duration) + SR
        self.buf = np.zeros(n, dtype=np.float64)           # 効果音
        self.bgm_buf = np.zeros(n, dtype=np.float64)       # BGM
        self.voice_buf = np.zeros(n, dtype=np.float64)     # 声
        self._spans = []                                   # 声が出ている区間（秒）

    def add(self, t, samples, vol=1.0, bgm=False):
        buf = self.bgm_buf if bgm else self.buf
        i = int(t * SR)
        if i < 0 or i >= len(buf):
            return
        n = min(len(samples), len(buf) - i)
        buf[i:i + n] += np.asarray(samples[:n], np.float64) * vol

    def add_voice(self, t, samples):
        x = np.asarray(samples, np.float64)
        i = int(t * SR)
        if i < 0 or i >= len(self.voice_buf) or len(x) == 0:
            return
        peak = np.max(np.abs(x))
        if peak < 1e-6:
            return                                          # 無音（テスト用の偽物など）
        act = np.abs(x) > 0.02 * peak
        rms = float(np.sqrt(np.mean(x[act] ** 2)))
        x = x * float(np.clip(VOICE_RMS / rms, 0.25, 4.0))
        n = min(len(x), len(self.voice_buf) - i)
        self.voice_buf[i:i + n] += x[:n]
        idx = np.flatnonzero(act)
        self._spans.append((t + idx[0] / SR, t + idx[-1] / SR))

    def duck_gain(self, n):
        """BGM に掛ける倍率（n サンプル分）。声の区間で 1 → -10dB へ DUCK_DOWN 秒、戻りは DUCK_UP 秒"""
        step = 0.01
        m = int(n / SR / step) + 2
        talk = np.zeros(m, bool)
        for a, b in self._spans:
            talk[int(a / step):int(b / step) + 1] = True
        low = 10 ** (DUCK_DB / 20)
        down = (1 - low) * step / DUCK_DOWN
        up = (1 - low) * step / DUCK_UP
        hold = int(DUCK_HOLD / step)
        g = np.empty(m)
        cur, since = 1.0, hold + 1
        for k in range(m):
            since = 0 if talk[k] else since + 1
            if since <= hold:
                cur = max(low, cur - down)
            else:
                cur = min(1.0, cur + up)
            g[k] = cur
        return np.interp(np.arange(n) / SR, np.arange(m) * step, g)

    def level_in(self, a, b):
        """a〜b 秒の音の大きさ（公開前チェックの「最初の0.5秒に音がある」用）"""
        i, j = int(a * SR), int(b * SR)
        x = self.voice_buf[i:j] + self.buf[i:j] + self.bgm_buf[i:j]
        return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0

    def write(self, path, duration):
        n = int(SR * duration)
        mix = (self.voice_buf[:n] + self.buf[:n] * SFX_GAIN
               + self.bgm_buf[:n] * BGM_GAIN * self.duck_gain(n))
        x = np.tanh(mix / 0.9) * 0.9                        # 軽いリミッター（小さい音はほぼそのまま）
        pcm = (x * 32767).astype(np.int16)
        st = np.repeat(pcm[:, None], 2, axis=1)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(st.tobytes())


# ---------- 書き出し ----------

def _dedupe(log):
    """文字のログを (字・位置・大きさ) で畳む（1万5千コマぶん溜めない）。最初に出た時刻を残す"""
    seen, out = set(), []
    for e in log:
        key = (e[1], round(e[2]), round(e[3]), round(e[6]))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def preflight(log, first, probe, duration, mixer, scale=1.0):
    """人が見る前に機械で落とせるものを落とす（ロング用）。scale は preview の縮小率（ログの座標を元の大きさに戻す）"""
    problems, notes = [], []
    if first is not None and probe is not None:
        changed = np.mean(np.abs(first.astype(np.int16) - probe.astype(np.int16)) > 8)
        if changed < 0.0015:
            problems.append(f"0〜0.3秒で画面がほとんど動いていない（変化 {changed:.4%}）")
    seen = set()
    for t, line, x0, y0, x1, y1, size in log:
        x0, y0, x1, y1, size = x0 / scale, y0 / scale, x1 / scale, y1 / scale, size / scale
        key = (line, round(x0), round(y0))
        if key in seen:
            continue
        seen.add(key)
        if size < PF_MIN_TEXT - 0.5:
            problems.append(f"{t:.1f}秒「{line}」の文字が小さい（{size:.0f}px < {PF_MIN_TEXT}）")
        if x0 < PF_X[0] or x1 > PF_X[1] or y0 < PF_Y[0] or y1 > PF_Y[1]:
            problems.append(f"{t:.1f}秒「{line}」が画面の端に近い（x={x0:.0f}〜{x1:.0f}、y={y0:.0f}〜{y1:.0f}。"
                            f"x {PF_X[0]}〜{PF_X[1]}・y {PF_Y[0]}〜{PF_Y[1]} に収める）")
    if mixer is not None and mixer.level_in(0, 0.5) < 1e-4:
        problems.append("最初の0.5秒に音が無い（BGM か声を 0 秒から入れる）")
    if duration < PF_MIN_LEN:
        notes.append(f"長さ {_mmss(duration)}（{_mmss(PF_MIN_LEN)} 未満。ミッドロール広告が入れられない長さ）")
    return problems, notes


def render(draw, duration, out_path, mixer, timeline=None, preview=False):
    """1920×1080・30fps・libx264 crf 20・yuv420p・aac 192k。preview=True は 960×540・15fps（同じ draw を ctx.scale(0.5) で）。
    書き出し後に timeline があれば chapters.txt も出す。10MB には縮めない"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fps = 15 if preview else FPS
    sc = 0.5 if preview else 1.0
    w, h = int(W * sc), int(H * sc)
    n = int(round(duration * fps))
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
    wav = None
    if mixer is not None:
        wav = out_path.with_suffix(".wav")
        mixer.write(wav, duration)
        cmd += ["-i", str(wav)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "28" if preview else "20", "-preset", "veryfast" if preview else "medium"]
    if wav:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-movflags", "+faststart", str(out_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    first = probe = None
    core._LOG = []
    try:
        for i in range(n):
            core._CUR_T = i / fps
            ctx = cairo.Context(surf)
            if preview:
                ctx.scale(sc, sc)
            draw(ctx, i / fps)
            surf.flush()
            if i == 0:
                first = np.frombuffer(bytes(surf.get_data()), np.uint8)
            elif i == int(0.3 * fps):
                probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
            p.stdin.write(memoryview(surf.get_data()))
            if i % 300 == 299:
                core._LOG = _dedupe(core._LOG)
            if i % (fps * 60) == fps * 60 - 1:
                print(f"  {i / fps / 60:.0f}分ぶん描いた（{i + 1}/{n}コマ）", flush=True)
        p.stdin.close()
    except (BrokenPipeError, OSError):
        p.wait()
        core._LOG = None
        raise SystemExit("ffmpeg が途中で止まりました")
    finally:
        log, core._LOG = core._LOG, None
    if p.wait() != 0:
        raise SystemExit("ffmpeg が失敗しました")
    problems, notes = preflight(_dedupe(log), first, probe, duration, mixer, scale=sc)
    for s in notes:
        print("  注意:", s)
    if problems:
        print("公開前チェック: 要対応")
        for s in problems:
            print("  -", s)
        raise SystemExit(1)
    print("公開前チェック: OK（0秒目の動き・文字の大きさと画面の端・冒頭の音。字幕は対象外）")
    if timeline is not None:
        txt = out_path.with_name("chapters.txt")
        txt.write_text(timeline.chapter_text() + "\n", encoding="utf-8")
        print("チャプター:", txt)
    mb = out_path.stat().st_size / 1024 / 1024
    print(f"書き出し: {out_path}（{mb:.1f}MB・{_mmss(duration)}）")
    return out_path


def still(draw, t, png_path):
    """確認用に1コマだけ PNG（1920×1080）で書き出す"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    core._CUR_T = t
    draw(cairo.Context(surf), t)
    surf.write_to_png(str(png_path))


def stills(draw, times, out_dir, cols=4, thumb=(480, 270)):
    """指定秒の静止画（still_<秒>.png）と一覧 sheet.png を書き出す。目で確かめるのは sheet.png から"""
    from PIL import Image
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("still_*.png"):
        old.unlink()
    paths = []
    for tt in times:
        pth = out_dir / f"still_{tt:06.1f}.png"
        still(draw, tt, pth)
        paths.append(pth)
    ims = [Image.open(q).convert("RGB").resize(thumb, Image.LANCZOS) for q in paths]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (thumb[0] + 8), (i // cols) * (thumb[1] + 8)))
    sheet.save(out_dir / "sheet.png")
    print("一覧:", out_dir / "sheet.png")
    return paths
