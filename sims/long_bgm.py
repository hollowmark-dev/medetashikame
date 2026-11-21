"""めでたしかめのロングの BGM（2026-11-06 ユーザーが決定: 甘茶の音楽工房「カスミソウ」）。

曲は assets/bgm/kasumisou.mp3（二次配布禁止のためリポジトリに入れない）。
声の間は mixer が -10dB 下げるので、声より約18dB下になる。曲をくり返し、つなぎ目は2秒重ねる。
"""
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BGM_FILE = ROOT / "assets" / "bgm" / "kasumisou.mp3"
BGM_RMS = 0.045


def bgm_track(duration, sr):
    if not BGM_FILE.exists():  # 公開側の作業コピーには曲が無い。無音（0 の配列）で動かす
        print(f"[long_bgm] 曲 {BGM_FILE.name} が無いので無音の BGM で動かします")
        return np.zeros(int(duration * sr) + sr)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(BGM_FILE), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    n, xf = int(duration * sr) + sr, 2 * sr
    out = np.zeros(n)
    fade_in, fade_out = np.linspace(0, 1, xf), np.linspace(1, 0, xf)
    i = 0
    while i < n:
        y = x.copy()
        if i > 0:
            y[:xf] *= fade_in
        y[-xf:] *= fade_out
        m = min(len(y), n - i)
        out[i:i + m] += y[:m]
        i += len(x) - xf
    out *= BGM_RMS / float(np.sqrt(np.mean(out ** 2)))
    t = np.arange(n) / sr
    out *= np.clip(t / 1.0, 0, 1) * np.clip((duration - t) / 2.5, 0, 1)
    return out
