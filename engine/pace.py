"""テンポの点検: 画面の文字が「読み終わる前に消えていないか」を機械で測る。

ナレーションが無いので、情報はすべて文字で届く。スマホで初めて見る人が読むのに要る時間を
  0.5秒（目を向ける）＋ 文字数 ÷ 6（1秒に6文字）
として、実際に出ていた時間がそれより短い文字を並べる。
動画は書き出さず、draw を10fpsで呼んで文字の出入りを記録するだけなので速い。

使い方: python engine/pace.py sims/gacha-1pct-100.py [sims/...]
"""
import importlib.util
import re
import sys
from pathlib import Path

import cairo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine.core as core  # noqa: E402

STEP = 0.1
CPS = 6.0


def need(line):
    return 0.5 + len(line) / CPS


def measure(sim_path):
    spec = importlib.util.spec_from_file_location("sim", sim_path)
    mod = importlib.util.module_from_spec(spec)
    sys.argv = [str(sim_path)]
    spec.loader.exec_module(mod)
    dur = mod.DURATION
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, core.W, core.H)
    seen = {}      # 文字 → [出ていた区間]
    n = int(dur / STEP)
    for i in range(n):
        t = i * STEP
        core._LOG = []
        core._CUR_T = t
        mod.draw(cairo.Context(surf), t)
        # 小さい注記（30px未満）は対象外。数字だけが変わるカウンターは同じ表示として扱う
        lines = {re.sub(r"[0-9,.]+", "#", e[1]) for e in core._LOG if e[6] >= 30}
        for ln in lines:
            iv = seen.setdefault(ln, [])
            if iv and abs(iv[-1][1] - t) < STEP * 1.5:
                iv[-1][1] = t + STEP
            else:
                iv.append([t, t + STEP])
    core._LOG = None
    return dur, seen


def report(sim_path):
    dur, seen = measure(sim_path)
    short = []
    for ln, ivs in seen.items():
        if len(ln.strip()) < 2:
            continue
        longest = max(b - a for a, b in ivs)
        if longest < need(ln) and ln.strip("#% ") != "":
            short.append((ivs[0][0], ln, longest, need(ln)))
    short.sort()
    print(f"\n== {Path(sim_path).stem}（{dur:.1f}秒）: 読み切れない文字 {len(short)} 件")
    for t0, ln, have, want in short:
        print(f"  {t0:5.1f}秒〜 「{ln}」 出ている {have:.1f}秒 / 要る {want:.1f}秒")
    return len(short)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        report(p)
