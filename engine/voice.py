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


def _wav_samples(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").copy(), w.getframerate()


def synth(text, cache_dir, speed=1.05, pitch=0.0, intonation=1.0, volume=1.0, pre=0.05, post=0.12, pauses=None):
    """1文を合成して Clip を返す。cache_dir に同じ設定の wav があれば合成しない。
    AivisSpeech の intonation は「全体の抑揚」ではなく感情表現の強さ。pitch は ±0.15 で、0 から動かすと音質が落ちる。
    pauses=(読点の間, 句点の間)（秒）を渡すと、文中の読点・句点の所に無音を差し込む（文は1回で合成するので抑揚と速さは同じ）。
    AivisSpeech は文中の句読点でほとんど間を取らず、AudioQuery の pauseLength / pauseLengthScale もほぼ効かないため（2026-10-12 実測）。
    既定の None は今までと同じ（1回で合成。キャッシュのキーも今までと同じ）"""
    if _VERSION is None:
        ensure_engine()
    shown, spoken = split_reading(text)
    if pauses is not None:
        return _synth_paused(shown, spoken, cache_dir, pauses,
                             dict(speed=speed, pitch=pitch, intonation=intonation, volume=volume, pre=pre, post=post))
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


def _synth_paused(shown, spoken, cache_dir, pauses, params):
    """synth(pauses=...) の中身。元の1文の wav（間なし）も cache_dir にキャッシュされる"""
    comma, period = float(pauses[0]), float(pauses[1])
    key = json.dumps([spoken, SPEAKER, params, _VERSION, "pauses-insert", [comma, period]], ensure_ascii=False, sort_keys=True)
    cache_dir = Path(cache_dir)
    path = cache_dir / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not path.exists():
        # 文は1回で合成する（塊ごとに合成すると早口になり、文の抑揚も切れる。2026-10-12 実測で約1割速くなった）。
        # 句読点（AudioQuery の pau モーラ）の位置を、モーラ数の比で音声の上に置き、その前後 ±0.25秒で一番静かな所に無音を差し込む
        whole = synth(spoken, cache_dir, **params)
        x, sr = _wav_samples(whole.path)
        q = _query(spoken, SPEAKER)
        marks, n = [], 0                       # (句読点の前までのモーラ数, 種類)
        for ap in q["accent_phrases"]:
            for m in ap["moras"]:
                if m.get("vowel") == "pau":
                    marks.append((n, m["text"]))
                else:
                    n += 1
        total = max(1, n)
        xf = np.abs(x.astype(np.float64))
        win = max(1, int(0.02 * sr))
        env = np.convolve(xf, np.ones(win) / win, "same")
        act = np.flatnonzero(env > 0.02 * max(1.0, env.max()))
        s0, s1 = (act[0], act[-1]) if act.size else (0, len(x))
        cuts, last = [], -10
        for k, mark in marks:
            if k >= total or k - last < 4:     # 文末と、前の間から4モーラ未満のところは入れない
                continue
            guess = s0 + (s1 - s0) * k / total
            lo, hi = int(max(s0, guess - 0.25 * sr)), int(min(s1, guess + 0.25 * sr))
            if hi - lo < win:
                continue
            i = lo + int(np.argmin(env[lo:hi]))
            cuts.append((i, comma if mark in (",", "、") else period))
            last = k
        pieces, prev = [], 0
        for i, gap in sorted(cuts):
            pieces += [x[prev:i], np.zeros(int(round(gap * sr)), np.int16)]
            prev = i
        pieces.append(x[prev:])
        y = np.concatenate(pieces)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(y.astype("<i2").tobytes())
        tmp.replace(path)
    with wave.open(str(path), "rb") as w:
        duration = w.getnframes() / w.getframerate()
    return Clip(shown, spoken, path, duration)
