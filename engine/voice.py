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


_KANA_D = {1: "いち", 2: "に", 3: "さん", 4: "よん", 5: "ご", 6: "ろく", 7: "なな", 8: "はち", 9: "きゅう"}
_KANA_100 = {1: "ひゃく", 3: "さんびゃく", 6: "ろっぴゃく", 8: "はっぴゃく"}
_KANA_1000 = {1: "せん", 3: "さんぜん", 8: "はっせん"}


def _num_kana(n):
    """1〜9999 の整数をひらがなに（分数の読み用）。範囲外は数字のまま"""
    if not 1 <= n <= 9999:
        return str(n)
    out = ""
    th, n = divmod(n, 1000)
    if th:
        out += _KANA_1000.get(th, _KANA_D[th] + "せん")
    hu, n = divmod(n, 100)
    if hu:
        out += _KANA_100.get(hu, _KANA_D[hu] + "ひゃく")
    te, n = divmod(n, 10)
    if te:
        out += ("" if te == 1 else _KANA_D[te]) + "じゅう"
    if n:
        out += _KANA_D[n]
    return out


_FRACTION = re.compile(r"(\d+|何)分の(\d+)")


def _fraction_reading(s):
    """「50分の1」「何分の1」を「ごじゅうぶんのいち」「なんぶんのいち」と読ませる（2026-10-25 ユーザー指摘:
    「ごじゅっぷん」と時間の読みになっていた）。表示用の文字は変えない"""
    def rep(m):
        a = "なん" if m.group(1) == "何" else _num_kana(int(m.group(1)))
        return f"{a}ぶんの{_num_kana(int(m.group(2)))}"
    return _FRACTION.sub(rep, s)


def split_reading(s):
    """「{表記|よみ}」記法を (表示用, 合成用) に分ける。記法が無ければ両方そのまま。
    合成用では「数字＋分の＋数字」を必ず「○ぶんの○」と読ませる"""
    return _READING.sub(lambda m: m.group(1), s), _fraction_reading(_READING.sub(lambda m: m.group(2), s))


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


def tail_cut(path, ms=8.0, th=0.03):
    """文末が切れているか（2026-11-08 ユーザー「『せん』が途切れて聞こえる」）。
    最後の音（0 でない最後の標本）の直前 ms ミリ秒の大きさが、ピークの th 倍より大きければ、声の途中で急に止まっている。
    返り値: (切れているか, 直前の大きさ/ピーク)"""
    x, sr = _wav_samples(path)
    x = np.abs(x.astype(np.float64))
    nz = np.flatnonzero(x > 0)
    if not nz.size:
        return False, 0.0
    win = max(1, int(0.005 * sr))
    env = np.convolve(x, np.ones(win) / win, "same")
    pk = max(1.0, env.max())
    v = float(env[max(0, nz[-1] - int(ms / 1000 * sr))]) / pk
    return v > th, v


def _tail_fixed(clip, cache_dir):
    """文末が切れている声に、なめらかに消える尻尾を足した wav を返す（切れていなければそのまま）。
    最後の 40ms を時間の逆向きに写して 70ms に伸ばし、余弦で 0 まで下げる。つなぎ目の値は同じなので「ぷつっ」とならない。
    そのあとの無音（元の post の長さ）はそのまま残す"""
    cut, _v = tail_cut(clip.path)
    if not cut:
        return clip
    path = Path(cache_dir) / (clip.path.stem + "_tail1.wav")
    if not path.exists():
        x, sr = _wav_samples(clip.path)
        y = x.astype(np.float64)
        nz = np.flatnonzero(np.abs(y) > 0)
        end = int(nz[-1]) + 1
        seg = y[max(0, end - int(0.04 * sr)):end]
        n = int(0.07 * sr)
        ext = np.resize(seg[::-1], n)
        ext *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, n)))
        z = np.concatenate([y[:end], ext, y[end:]])
        tmp = path.with_suffix(".tmp")
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(np.round(np.clip(z, -32768, 32767)).astype("<i2").tobytes())
        tmp.replace(path)
    with wave.open(str(path), "rb") as w:
        duration = w.getnframes() / w.getframerate()
    return Clip(clip.text, clip.spoken, path, duration)


def synth(text, cache_dir, speed=1.05, pitch=0.0, intonation=1.0, volume=1.0, pre=0.05, post=0.12, pauses=None, safe_pauses=False, tail_fix=False):
    """tail_fix=True で、文末が切れた声に消える尻尾を足す（2026-11-08。既定は今までと同じ）"""
    if tail_fix:
        return _tail_fixed(synth(text, cache_dir, speed, pitch, intonation, volume, pre, post, pauses, safe_pauses), cache_dir)
    return _synth_core(text, cache_dir, speed, pitch, intonation, volume, pre, post, pauses, safe_pauses)


def _synth_core(text, cache_dir, speed=1.05, pitch=0.0, intonation=1.0, volume=1.0, pre=0.05, post=0.12, pauses=None, safe_pauses=False):
    """1文を合成して Clip を返す。cache_dir に同じ設定の wav があれば合成しない。
    AivisSpeech の intonation は「全体の抑揚」ではなく感情表現の強さ。pitch は ±0.15 で、0 から動かすと音質が落ちる。
    pauses=(読点の間, 句点の間)（秒）を渡すと、文中の読点・句点の所に無音を差し込む（文は1回で合成するので抑揚と速さは同じ）。
    AivisSpeech は文中の句読点でほとんど間を取らず、AudioQuery の pauseLength / pauseLengthScale もほぼ効かないため（2026-10-12 実測）。
    既定の None は今までと同じ（1回で合成。キャッシュのキーも今までと同じ）"""
    if _VERSION is None:
        ensure_engine()
    shown, spoken = split_reading(text)
    if pauses is not None and safe_pauses:
        return _synth_paused_safe(shown, spoken, cache_dir, pauses,
                                  dict(speed=speed, pitch=pitch, intonation=intonation, volume=volume, pre=pre, post=post))
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


def _synth_paused_safe(shown, spoken, cache_dir, pauses, params):
    """語の途中に入らない間の差し込み（2026-11-06 ユーザー「読みが途切れる」）。
    元の声はすでに句読点で約0.33秒の間を取っている。旧版（v2）はその上に足し、探す範囲が広いので次の語の中の無音にも入っていた。
    ここでは「句読点の前までの声の終わり」と「句読点の後ろの声の始まり」の間（元の声の間）の中だけに入れる。
    元の間が 80ms 未満なら入れない。読点の値が 0 なら読点には入れない。切り口は 6ms でフェードして音のつなぎ目を消す"""
    comma, period = float(pauses[0]), float(pauses[1])
    key = json.dumps([spoken, SPEAKER, params, _VERSION, "pauses-safe-v3", [comma, period]], ensure_ascii=False, sort_keys=True)
    cache_dir = Path(cache_dir)
    path = cache_dir / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not path.exists():
        whole = synth(spoken, cache_dir, **params)
        x, sr = _wav_samples(whole.path)
        win = max(1, int(0.01 * sr))

        def voiced(a):
            e = np.convolve(np.abs(a.astype(np.float64)), np.ones(win) / win, "same")
            return e, np.flatnonzero(e > 0.02 * max(1.0, e.max()))
        env, act = voiced(x)
        cuts = []
        for m in re.finditer(r"[、。,，．]", spoken):
            pos = m.end()
            gap = comma if m.group() in "、,，" else period
            if gap <= 0 or not spoken[pos:].strip("、。,，．！？!?」』）) ") or not act.size:
                continue
            hx, _ = _wav_samples(synth(spoken[:pos], cache_dir, **params).path)
            tx, _ = _wav_samples(synth(spoken[pos:], cache_dir, **params).path)
            _, ha = voiced(hx)
            _, ta = voiced(tx)
            if not ha.size or not ta.size:
                continue
            a0, a1 = int(ha[-1]), int(act[-1] - (ta[-1] - ta[0]))    # 元の声の間（句読点の前の終わり〜後ろの始まり）
            if a1 - a0 < 0.08 * sr:
                continue
            lo, hi = a0 + int(0.02 * sr), a1 - int(0.02 * sr)
            cuts.append((lo + int(np.argmin(env[lo:hi])), gap))
        pieces, prev, fade_n = [], 0, int(0.006 * sr)
        ramp = np.linspace(1.0, 0.0, fade_n)
        y0 = x.astype(np.float64)
        for i, gap in sorted(cuts):
            seg = y0[prev:i].copy()
            seg[-fade_n:] *= ramp
            if prev > 0:
                seg[:fade_n] *= ramp[::-1]
            pieces += [seg, np.zeros(int(round(gap * sr)))]
            prev = i
        last = y0[prev:].copy()
        if prev > 0:
            last[:fade_n] *= ramp[::-1]
        pieces.append(last)
        y = np.concatenate(pieces)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(np.round(y).astype("<i2").tobytes())
        tmp.replace(path)
    with wave.open(str(path), "rb") as w:
        duration = w.getnframes() / w.getframerate()
    return Clip(shown, spoken, path, duration)


def _synth_paused(shown, spoken, cache_dir, pauses, params):
    """synth(pauses=...) の中身。元の1文の wav（間なし）も cache_dir にキャッシュされる"""
    comma, period = float(pauses[0]), float(pauses[1])
    key = json.dumps([spoken, SPEAKER, params, _VERSION, "pauses-insert-v2", [comma, period]], ensure_ascii=False, sort_keys=True)
    cache_dir = Path(cache_dir)
    path = cache_dir / (hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not path.exists():
        # 文は1回で合成する（塊ごとに合成すると早口になり、文の抑揚も切れる。2026-10-12 実測で約1割速くなった）。
        # 句読点の位置は「句読点までの頭の部分だけを合成した長さ」で決める（v2・2026-10-24）。
        # 旧版はモーラ数の比で置いていたが、AivisSpeech の AudioQuery には長さが入っておらず、0.2〜0.5秒ずれて
        # 語の途中に無音が入り「声が詰まる」と言われた（桶狭間ロング 4:41 ほか）。頭だけの合成の終わりの近く
        # （-0.10〜+0.30秒）で一番長い静かな所に差し込み、見つからなければその句読点には入れない
        whole = synth(spoken, cache_dir, **params)
        x, sr = _wav_samples(whole.path)
        xf = np.abs(x.astype(np.float64))
        win = max(1, int(0.01 * sr))
        env = np.convolve(xf, np.ones(win) / win, "same")
        mx = max(1.0, env.max())
        act = np.flatnonzero(env > 0.02 * mx)
        s0, s1 = (act[0], act[-1]) if act.size else (0, len(x))
        quiet = env < 0.03 * mx
        cuts, last = [], -10
        for m in re.finditer(r"[、。,，．]", spoken):
            pos = m.end()
            if not spoken[pos:].strip("、。,，．！？!?」』）) "):
                continue                        # 文末
            if pos - last < 4:                  # 前の間から4文字未満のところは入れない
                continue
            head = synth(spoken[:pos], cache_dir, **params)
            hx, _ = _wav_samples(head.path)
            he = np.convolve(np.abs(hx.astype(np.float64)), np.ones(win) / win, "same")
            ha = np.flatnonzero(he > 0.02 * max(1.0, he.max()))
            if not ha.size:
                continue
            anchor = ha[-1]
            lo, hi = int(max(s0, anchor - 0.10 * sr)), int(min(s1, anchor + 0.30 * sr))
            if hi - lo < win:
                continue
            best, j = None, lo
            while j < hi:                       # 静かな区間（15ms 以上）のうち一番長いもの
                if quiet[j]:
                    k = j
                    while k < hi and quiet[k]:
                        k += 1
                    if (k - j) >= 0.015 * sr and (best is None or k - j > best[1] - best[0]):
                        best = (j, k)
                    j = k
                else:
                    j += 1
            if best is None:
                continue
            cuts.append(((best[0] + best[1]) // 2, comma if m.group() in "、,，" else period))
            last = pos
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
