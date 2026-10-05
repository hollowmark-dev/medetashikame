"""ナレーションの音声合成（AivisSpeech Engine。VOICEVOX 互換 API）。

台本の1文ずつを wav にして、長さ（秒）を返す。同じ文・同じ設定ならキャッシュを使い回し、合成しない。
依存は標準ライブラリと numpy だけ（requests は使わない）。
読みの指定は「{表記|よみ}」記法: 字幕には表記、合成にはよみを渡す。例 "{MU|ミュー}を変えると"
"""
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ENGINE_URL = "http://127.0.0.1:10101"   # AivisSpeech Engine（VOICEVOX 互換 API）
SPEAKER = 606865152                      # fumifumi（ノーマル）
EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/AivisSpeech/AivisSpeech-Engine/run.exe"
SR = 48000

_READING = re.compile(r"\{([^{}|]*)\|([^{}]*)\}")
_VERSION = None    # エンジンの版（キャッシュの鍵に入れる。実行中は変わらないので1回だけ取る）


def _open(req, timeout):
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def version(timeout=3):
    """エンジンの版。返らなければ None"""
    try:
        return json.loads(_open(ENGINE_URL + "/version", timeout))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def ensure_engine(timeout=180):
    """エンジンが動いていなければ裏で起動し、/version が返るまで待つ"""
    global _VERSION
    if version() is None:
        if not EXE.exists():
            raise SystemExit(f"AivisSpeech Engine が見つかりません: {EXE}")
        print("AivisSpeech Engine を起動します…")
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen([str(EXE), "--host", "127.0.0.1", "--port", "10101", "--use_gpu", "--disable_sentry"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags, close_fds=True)
        t0 = time.time()
        while version() is None:
            if time.time() - t0 > timeout:
                raise SystemExit(f"AivisSpeech Engine が {timeout} 秒たっても起動しません")
            time.sleep(1.0)
    _VERSION = str(version())


def split_reading(s):
    """「{表記|よみ}」記法を (表示用, 合成用) に分ける。記法が無ければ両方そのまま"""
    return _READING.sub(lambda m: m.group(1), s), _READING.sub(lambda m: m.group(2), s)


@dataclass
class Clip:
    text: str        # 字幕に出す文字（表記）
    spoken: str      # 合成に渡した文字
    path: Path       # wav（48kHz・モノラル）
    duration: float  # 秒（前後の無音を含む）

    def samples(self):
        """float32、-1〜1、48kHz モノラル"""
        with wave.open(str(self.path), "rb") as w:
            ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(n)
        if sw != 2:
            raise ValueError(f"16bit の wav だけ扱えます: {self.path} ({sw * 8}bit)")
        a = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
        if ch > 1:
            a = a.reshape(-1, ch).mean(1)
        if sr != SR:   # エンジンが指定を守らなかったときの保険（線形補間）
            a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
        return a


def _query(spoken, speaker):
    q = urllib.parse.urlencode({"text": spoken, "speaker": speaker})
    return json.loads(_open(urllib.request.Request(f"{ENGINE_URL}/audio_query?{q}", data=b"", method="POST"), 120))


def read_aloud(spoken, speaker=SPEAKER):
    """エンジンが実際に読もうとしているカナ（アクセント句ごとに「/」で区切る）。誤読の確認用"""
    ensure_engine()
    return "/".join("".join(m["text"] for m in ap["moras"]) + (ap.get("pause_mora") and "、" or "")
                    for ap in _query(spoken, speaker)["accent_phrases"])


def synth(text, cache_dir, speed=1.05, pitch=0.0, intonation=1.0, volume=1.0, pre=0.05, post=0.12):
    """1文を合成して Clip を返す。cache_dir に同じ設定の wav があれば合成しない。
    AivisSpeech の intonation は「全体の抑揚」ではなく感情表現の強さ。pitch は ±0.15 で、0 から動かすと音質が落ちる"""
    if _VERSION is None:
        ensure_engine()
    shown, spoken = split_reading(text)
    params = dict(speed=speed, pitch=pitch, intonation=intonation, volume=volume, pre=pre, post=post)
    key = json.dumps([spoken, SPEAKER, params, _VERSION], ensure_ascii=False, sort_keys=True)
    cache_dir = Path(cache_dir)
    path = cache_dir / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not path.exists():
        q = _query(spoken, SPEAKER)
        want = dict(speedScale=speed, pitchScale=pitch, intonationScale=intonation, volumeScale=volume,
                    prePhonemeLength=pre, postPhonemeLength=post, outputSamplingRate=SR, outputStereo=False)
        for k, v in want.items():
            if k in q:   # エンジンに無いキーは足さない
                q[k] = v
        req = urllib.request.Request(f"{ENGINE_URL}/synthesis?speaker={SPEAKER}", data=json.dumps(q).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        wav = _open(req, 300)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(wav)
        tmp.replace(path)    # 書きかけを残さない
    with wave.open(str(path), "rb") as w:
        duration = w.getnframes() / w.getframerate()
    return Clip(shown, spoken, path, duration)
