"""シミュレーション動画の共通エンジン。

映像: pycairo で1フレームずつ描き、生の BGRA を ffmpeg に流し込む。
音:   numpy で合成した効果音を Mixer に置き、WAV にしてから映像と合わせる。
素材ファイルを一切使わない（絵も音も全部ここで作る）ので、権利の確認が要らない。
"""
import math
import subprocess
import wave
from pathlib import Path

import cairo
import numpy as np

W, H, FPS = 1080, 1920, 30
SR = 48000
FONT = "Meiryo"

# ショートの画面で、UIに隠れる場所（下の約18%と右端のボタン列）。大事なものは置かない
SAFE_BOTTOM = 1580
SAFE_RIGHT = 930
SAFE_RIGHT_FROM_Y = 1000   # 右端のボタン列（高評価・コメント等）はこの高さから下
MIN_TEXT = 24              # これより小さい文字はスマホで読めない

_LOG = None     # render 中だけ、描いた文字の位置を記録する（公開前チェック用）
_CUR_T = 0.0


def check_answers(checks):
    """答えの照合。checks = [(名前, シミュレーションの値, 理論値, 許容誤差)]。
    1つでも外れたら書き出さずに止める（確率の動画で答えを間違えるのが最大の事故）"""
    bad = []
    for name, sim, exact, tol in checks:
        ok = abs(sim - exact) <= tol
        f = (lambda v: f"{v:.2e}") if max(abs(sim), abs(exact)) < 1e-3 and (sim or exact) else (lambda v: f"{v:.4f}")
        print(f"  答えの照合 {'OK' if ok else 'NG'}: {name} シミュ={f(sim)} 理論={f(exact)} (許容 ±{tol})")
        if not ok:
            bad.append(name)
    if bad:
        raise SystemExit(f"答えがシミュレーションと理論で食い違っています: {bad}")


# ---------- 色と図形 ----------

def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (a,)


def fill(ctx, color):
    ctx.set_source_rgba(*(hexrgb(color) if isinstance(color, str) else color))


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def text(ctx, s, x, y, size, color="#ffffff", align="center", bold=True, alpha=1.0):
    """y はベースラインではなく文字の縦中央。改行を含めてよい"""
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    lines = s.split("\n")
    lh = size * 1.25
    top = y - lh * (len(lines) - 1) / 2
    c = hexrgb(color) if isinstance(color, str) else color
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * alpha)
    for i, line in enumerate(lines):
        ext = ctx.text_extents(line)
        if align == "center":
            tx = x - ext.x_advance / 2
        elif align == "right":
            tx = x - ext.x_advance
        else:
            tx = x
        cy = top + i * lh
        ctx.move_to(tx, cy + size * 0.36)
        ctx.show_text(line)
        if _LOG is not None and c[3] * alpha > 0.1:
            # translate / scale の中で描いた文字も、画面上の位置で判定できるように変換して記録する
            xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in
                           ((tx, cy - size / 2), (tx + ext.x_advance, cy + size / 2))))
            dsize = abs(ctx.user_to_device_distance(0, size)[1])
            _LOG.append((_CUR_T, line, min(xs), min(ys), max(xs), max(ys), dsize))
    ctx.new_path()   # show_text は現在位置を残すので、次の arc などに線がつながらないよう切る


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def clamp01(t):
    return max(0.0, min(1.0, t))


# ---------- 音 ----------

class Mixer:
    def __init__(self, duration):
        self.buf = np.zeros(int(SR * duration) + SR, dtype=np.float64)

    def add(self, t, samples, vol=1.0):
        i = int(t * SR)
        if i >= len(self.buf):
            return
        n = min(len(samples), len(self.buf) - i)
        self.buf[i:i + n] += samples[:n] * vol

    def write(self, path, duration):
        x = self.buf[: int(SR * duration)]
        # 平均の音量をそろえてから、はみ出た山だけ tanh で丸める（スマホで小さく聞こえないように）
        rms = np.sqrt(np.mean(x ** 2)) or 1.0
        x = np.tanh(x * (0.11 / rms)) * 0.9
        pcm = (x * 32767).astype(np.int16)
        st = np.repeat(pcm[:, None], 2, axis=1)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(st.tobytes())


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def blip(freq, dur=0.12):
    """ポン。着地・カウント用"""
    t = _t(dur)
    env = np.exp(-t * 28) * np.minimum(1, t * 400)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)) * env


def tick(freq=2000, dur=0.03):
    t = _t(dur)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 180)


def bell(freq, dur=1.6):
    """チーン。発見・正解用"""
    t = _t(dur)
    env = np.exp(-t * 3.2) * np.minimum(1, t * 300)
    partials = [(1, 1), (2.01, 0.5), (3.0, 0.25), (4.2, 0.12)]
    return sum(a * np.sin(2 * np.pi * freq * m * t) for m, a in partials) * env


def thump(dur=0.35):
    t = _t(dur)
    f = 110 * np.exp(-t * 8) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def whoosh(dur=0.6, rng=None):
    rng = rng or np.random.default_rng(0)
    t = _t(dur)
    n = rng.standard_normal(len(t))
    # 簡易ローパス（移動平均）で風っぽく
    k = 40
    n = np.convolve(n, np.ones(k) / k, mode="same")
    env = np.sin(np.pi * t / dur) ** 2
    return n * env * 3


def chord(freqs, dur=1.2):
    t = _t(dur)
    env = np.minimum(1, t * 20) * np.exp(-t * 1.8)
    return sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs) * env


def kick(dur=0.25):
    t = _t(dur)
    f = 150 * np.exp(-t * 25) + 48
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)


def hat(dur=0.05, seed=1):
    t = _t(dur)
    n = np.random.default_rng(seed).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(6) / 6, mode="same")   # 高い成分だけ残す
    return n * np.exp(-t * 90) * 0.6


def riser(dur=0.9):
    """上がっていく音。1万回モードに入る合図"""
    t = _t(dur)
    f = 200 * (8 ** (t / dur))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    x += whoosh(dur) * 0.4
    return x * (t / dur) ** 1.5


def beat(mixer, t0, t1, bpm=128, vol=0.5, accel=False):
    """1万回モードのリズム（シリーズ共通の目印）。accel=True で後半ほど刻みが細かくなる"""
    step = 60 / bpm / 2
    t, k = t0, 0
    while t < t1:
        if k % 2 == 0:
            mixer.add(t, kick(), vol)
        mixer.add(t, hat(seed=k), vol * (0.5 if k % 2 else 0.3))
        p = (t - t0) / max(1e-6, t1 - t0)
        t += step / (2 if accel and p > 0.5 else 1)
        k += 1


def shimmer(n_hits, dur=0.25, seed=0):
    """たくさんの当たりが同時に光るときの、きらきらした音（数に応じて厚くなる）"""
    rng = np.random.default_rng(seed)
    t = _t(dur)
    x = np.zeros(len(t))
    for _ in range(int(min(12, 2 + n_hits / 15))):
        f = rng.uniform(2200, 4200)
        d = rng.uniform(0, dur * 0.4)
        x += np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - d) * 40) * (t > d)
    return x * 0.15


def pad(duration, freqs=(110, 164.8, 220, 277.2), vol=0.05):
    """全体に薄く敷く持続音。無音の間を作らないため"""
    t = _t(duration)
    x = sum(np.sin(2 * np.pi * f * t + i) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * (i + 1) * t))
            for i, f in enumerate(freqs)) / len(freqs)
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (duration - t) / 1.5)
    return x * fade * vol


# ---------- 書き出し ----------

MAX_MB = 9.5   # Claude in Chrome の file_upload は 10MB まで


def shrink(path, duration, max_mb=MAX_MB):
    """max_mb を超えていたら、2パスのビットレート指定で縮め直す（粒子の多い回は crf 18 だと大きくなる）"""
    path = Path(path)
    mb = path.stat().st_size / 1024 / 1024
    if mb <= max_mb:
        return mb
    kbps = int(max_mb * 0.93 * 8 * 1024 / duration) - 160
    tmp = path.with_name(path.stem + "_small.mp4")
    log = str(path.with_name("ffmpeg2pass"))
    base = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-c:v", "libx264", "-preset", "slow",
            "-b:v", f"{kbps}k", "-passlogfile", log]
    subprocess.run(base + ["-pass", "1", "-an", "-f", "null", "-"], check=True)
    subprocess.run(base + ["-pass", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(tmp)],
                   check=True)
    for f in path.parent.glob("ffmpeg2pass*"):
        f.unlink()
    tmp.replace(path)
    new = path.stat().st_size / 1024 / 1024
    print(f"大きさ: {mb:.1f}MB → {new:.1f}MB に縮めた（映像 {kbps}kbps）")
    return new


def render(draw, duration, out_path, mixer=None):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(duration * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    wav = None
    if mixer is not None:
        wav = out_path.with_suffix(".wav")
        mixer.write(wav, duration)
        cmd += ["-i", str(wav)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium"]
    if wav:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [str(out_path)]
    global _LOG, _CUR_T
    _LOG = []
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    first = probe = None
    for i in range(n):
        _CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        surf.flush()
        data = bytes(surf.get_data())
        if i == 0:
            first = np.frombuffer(data, np.uint8)
        elif i == int(0.3 * FPS):
            probe = np.frombuffer(data, np.uint8)
        p.stdin.write(data)
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg が失敗しました")
    log, _LOG = _LOG, None
    problems = preflight(log, first, probe, duration, mixer)
    if problems:
        print("公開前チェック: 要対応")
        for s in problems:
            print("  -", s)
        raise SystemExit(1)
    print("公開前チェック: OK（0秒目の動き・文字の位置と大きさ・読み切れる長さ・長さ・冒頭の音）")
    shrink(out_path, duration)
    return out_path


def preflight(log, first, probe, duration, mixer):
    """人が見る前に機械で落とせるものを落とす"""
    problems = []
    # 0秒目から動いているか（1コマ目が止まった問題文だとスワイプされる）
    if first is not None and probe is not None:
        changed = np.mean(np.abs(first.astype(np.int16) - probe.astype(np.int16)) > 8)
        if changed < 0.0015:
            problems.append(f"0〜0.3秒で画面がほとんど動いていない（変化 {changed:.4%}）")
    seen = set()
    for t, line, x0, y0, x1, y1, size in log:
        key = (line, round(x0), round(y0))
        if key in seen:
            continue
        seen.add(key)
        if y1 > SAFE_BOTTOM:
            problems.append(f"{t:.1f}秒「{line}」が下のUIに隠れる（下端 y={y1:.0f} > {SAFE_BOTTOM}）")
        elif x1 > SAFE_RIGHT and y1 > SAFE_RIGHT_FROM_Y:
            problems.append(f"{t:.1f}秒「{line}」が右のボタン列に隠れる（右端 x={x1:.0f}）")
        if size < MIN_TEXT:
            problems.append(f"{t:.1f}秒「{line}」の文字が小さい（{size}px < {MIN_TEXT}）")
    problems += reading_gaps(log)
    if duration > 59:
        problems.append(f"長さ {duration:.1f}秒（ショートは60秒未満）")
    if mixer is not None:
        head = mixer.buf[: int(SR * 0.5)]
        if np.sqrt(np.mean(head ** 2)) < 1e-4:
            problems.append("最初の0.5秒に音が無い")
    return problems


READ_CPS = 6.0        # 1秒に読める文字数（スマホで初めて見る人の目安）
READ_MIN_SIZE = 40    # この大きさ以上の文字（見出し・札・合図）を読み切れるかの対象にする


def reading_gaps(log):
    """大きな文字が「0.5秒＋文字数÷6秒」より早く消えていないか。
    ナレーションが無いので、読み切れない札はそのまま「分からない」になる（2026-09-26 ユーザー指摘）。
    数字だけが変わるカウンターは同じ表示として扱う"""
    import re
    frames = {}
    for t, line, *_rest, size in log:
        if size >= READ_MIN_SIZE:
            frames.setdefault(round(t * FPS), set()).add(re.sub(r"[0-9,.]+", "#", line))
    runs = {}
    for f in sorted(frames):
        for key in frames[f]:
            iv = runs.setdefault(key, [])
            if iv and f - iv[-1][1] <= 1:
                iv[-1][1] = f
            else:
                iv.append([f, f])
    out = []
    for key, iv in runs.items():
        body = key.replace("#", "").strip(" %%！？!?。、")
        if len(body) < 2:
            continue
        have = max(b - a + 1 for a, b in iv) / FPS
        need = 0.5 + len(key) / READ_CPS
        if have < need:
            out.append(f"{iv[0][0] / FPS:.1f}秒「{key}」が読み切れない（{have:.1f}秒 / 要る {need:.1f}秒）")
    return out


def still(draw, t, png_path):
    """確認用に1コマだけPNGで書き出す"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    draw(cairo.Context(surf), t)
    surf.write_to_png(str(png_path))


def pill(ctx, s, x, y, size, bg, fg="#ffffff", a=1.0):
    """角丸の札に文字を載せる。s は改行を含めてよい。(x, y) は札の中心"""
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    lines = s.split("\n")
    w = max(ctx.text_extents(l).x_advance for l in lines) + 70
    h = size * 1.25 * len(lines) + 40
    c = hexrgb(bg) if isinstance(bg, str) else bg
    fill(ctx, (c[0], c[1], c[2], c[3] * a))
    rrect(ctx, x - w / 2, y - h / 2, w, h, 24)
    ctx.fill()
    text(ctx, s, x, y, size, fg, alpha=a)
    return w, h
