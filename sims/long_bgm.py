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
    # 2026-11-21 曲の頭（約0.5秒）と終わり（約2.8秒）の無音を切ってからつなぐ。切らないと、つなぎ目（約128秒ごと）で
    # 2秒の重ねが無音どうしになり、BGM が 0.1〜0.5秒 消えていた（ナポレオンの audio_check で見つかった）
    w = int(0.1 * sr)
    k = len(x) // w
    rms = 20 * np.log10(np.sqrt((x[:k * w].reshape(k, w) ** 2).mean(1)) + 1e-12)
    loud = np.where(rms > rms.max() - 30)[0]   # 曲の頭と終わりの小さい所（いちばん大きい所より30dB下）を切る
    if len(loud):
        x = x[loud[0] * w:(loud[-1] + 1) * w]
    n, xf = int(duration * sr) + sr, int(0.4 * sr)   # 重ねは0.4秒（2秒だと、曲の終わりの消えていく所と頭の小さい所が重なって音が落ちた）
    out = np.zeros(n)
    fade_in, fade_out = np.sqrt(np.linspace(0, 1, xf)), np.sqrt(np.linspace(1, 0, xf))   # 等パワーで重ねる（つなぎ目で音量が落ちない）
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
