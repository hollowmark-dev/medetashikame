"""サケの卵ロング「もしあなたがサケの卵だったら」（横型ロング）— 2026-11-05 作成。場面（描画・声の並び・照合・静止画）。

  python -X utf8 sims/salmon-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/salmon-long.py --fake-voice --stills         要所の静止画6枚と 480px の一覧（out/salmon-long/stills/・stills_480.png）
  python -X utf8 sims/salmon-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/salmon-long/scene_work/）
  python -X utf8 sims/salmon-long.py --fake-voice --sheet          本編の全場面の静止画一覧（out/salmon-long/body_stills_480*.png）
  python -X utf8 sims/salmon-long.py --fake-voice --readings       読みの一覧（scene_work/readings.log。--real-readings で AivisSpeech の読みも）
  python -X utf8 sims/salmon-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/salmon-long.py --scenecheck                  本番の声で照合（frames_real.pkl を保存。check-long が読む）
  python -X utf8 sims/salmon-long.py                               本番の書き出し（第2段階。AivisSpeech を起動してから）

台本: publish/salmon-long/narration_B.md（統括が決定。文は変えない）。「## 0」より後の「- 」の行をそのまま読む。{表記|よみ} は台本にある。
数字: out/salmon-long/data.json（sims/salmon_model.py が出したもの）。1万回の結果のばらつき（山）は salmon_model.chain を同じ種・同じ順で呼んで取り出す
      （data.json の中央値・最少・最多と同じになることを照合で確かめる。模型は作り直さない）。
絵: sims/salmon_art.py（平塗り・輪郭線なし。卵はうすい色の粒、あなたはオレンジ・顔つき。稚魚・成魚はうすい青の群れとオレンジのあなた）。
土台（台本の読み込み・声の時間割・--fake-voice・--scenecheck・--stills・--readings・場面の切りかえの間・frames_real.pkl）は sims/danchi-long.py と同じ。
区切り（ここまで／ここから）は engine/longkit.py の Eyecatch を平たい地に描き直したもの（カメの代わりに小さなサケが泳ぐ）。
"""
import json
import math
import random
import re as _re
import sys
from dataclasses import dataclass
from pathlib import Path

import cairo
import numpy as np

SLUG = "salmon-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import core  # noqa: E402
from engine import longform as lf  # noqa: E402
from engine import longkit as lk  # noqa: E402
from engine.core import (bell, blip, check_answers, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, text, text_width,  # noqa: E402
                         whoosh)
from engine.voice import split_reading  # noqa: E402

import salmon_model as sm  # noqa: E402  模型（作り直さない）
from salmon_map_data import HOKKAIDO as MAP_HOKKAIDO, OTHERS as MAP_OTHERS, xy as map_xy  # noqa: E402  Natural Earth の地図の形
from danchi_people import mix  # noqa: E402
from salmon_art import _clear, _grid, draw_egg, draw_fish, gravel_bed, north_sea, river_mouth, set_net  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAKE = "--fake-voice" in sys.argv
NARR_PATH = ROOT / "publish" / SLUG / "narration_B.md"
VOICE_DIR = OUT / "voice"
WORK = OUT / "scene_work"


def ihalf(x):
    """画面・声に出す丸め（四捨五入）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本の読み込み（danchi-long.py と同じ）
# ============================================================
GAP_FAST = 3.0


def parse_narration(path=NARR_PATH):
    chaps, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _re.match(r"##\s*(\d+)\s+(.+)$", raw)
        if m:
            cur = dict(n=int(m.group(1)), title=m.group(2).strip(), items=[])
            chaps.append(cur)
            continue
        if raw.startswith("## ") or raw.strip() == "---":
            cur = None                     # 番号のない見出し（「守った決まり」など）から先は台本ではない
            continue
        if cur is None or not raw.startswith("- "):
            continue
        body = raw[2:].strip()
        if body.startswith("（無音"):
            ms = _re.match(r"（無音\s*(\d+(?:\.\d+)?)\s*秒", body)
            cur["items"].append(("gap", float(ms.group(1)) if ms else None, body))
        elif body.startswith("（") or body.startswith("〔"):
            cur["items"].append(("note", None, body))
        else:
            mt = _re.search(r"(〔[^〕]*〕\s*)+$", body)
            txt = (body[:mt.start()] if mt else body).strip()
            notes_ = _re.findall(r"〔([^〕]*)〕", mt.group(0)) if mt else []
            cur["items"].append(("line", txt, "／".join(notes_)))
    return chaps


CHAPS = parse_narration()
LAST_CH = max(c["n"] for c in CHAPS)
LINES = {}
LINE_NOTE = {}
GAP_NOTE = {}
GAP_SEC = {}
CH_NOTE0 = {}
SPEED_V = 1.0
END_HOLD = 2.7
SUB_MAX2 = 2 * lf.SUB_MAX


def split_long(txt):
    """2行（56字）に収まらない文だけ、「。」の切れ目で分ける（文言は変えない）"""
    if len(split_reading(txt)[0]) <= SUB_MAX2:
        return [txt]
    sents = [x + "。" for x in txt.split("。") if x]
    out, cur = [], ""
    for x in sents:
        if cur and len(split_reading(cur + x)[0]) > SUB_MAX2:
            out.append(cur)
            cur = x
        else:
            cur += x
    if cur:
        out.append(cur)
    res = []
    for p in out:
        if len(split_reading(p)[0]) <= SUB_MAX2:
            res.append(p)
            continue
        cuts = [i + 1 for i, ch in enumerate(p) if ch == "、"]
        k = min(cuts, key=lambda i: abs(i - len(p) / 2))
        res += [p[:k], p[k:]]
    return res


# ---- 読みの補正: 台本に {表記|よみ} が入っているので、ここは空（--real-readings で AivisSpeech の読みを確かめて、必要なら足す）----
READ_FIX = []
READ_HITS = {}


def fix_reading(txt):
    for a, b, _n in READ_FIX:
        if a in txt:
            READ_HITS[a] = READ_HITS.get(a, 0) + txt.count(a)
            txt = txt.replace(a, b)
    return txt


def _items():
    C, G = lf.Chapter, lf.Gap
    out = []
    for ch in CHAPS:
        n = ch["n"]
        out.append(C(ch["title"], id=f"ch{n}", gap=0.0 if n == 0 else 1.0))
        lines = [it for it in ch["items"] if it[0] == "line"]
        k, li, gk = 0, 0, 0
        for kind, val, note_ in ch["items"]:
            if kind == "line":
                li += 1
                parts = split_long(val)
                for j, part in enumerate(parts):
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and j == len(parts) - 1
                    out.append(lf.Line(lid, fix_reading(part), pause=0.3 if n == 0 else ((END_HOLD if n == LAST_CH else 0.6) if last else 0.35), speed=SPEED_V))
            elif kind == "gap":
                gk += 1
                gid = f"g{n}_{gk}"
                GAP_NOTE[gid] = note_
                GAP_SEC[gid] = val if val else GAP_FAST
                out.append(G(gid, GAP_SEC[gid]))
            elif n not in CH_NOTE0:
                CH_NOTE0[n] = note_
    return out


@dataclass
class _FakeClip:
    text: str
    spoken: str
    duration: float

    def samples(self):
        return np.zeros(16, np.float32)


def _fake_synth(text_, cache_dir, speed=SPEED_V, **kw):
    shown_, spoken = split_reading(text_)
    n = len(shown_) + sum(max(0, len(m.group(2)) * 0.55 - len(m.group(1)))
                          for m in _re.finditer(r"\{([^{}|]*)\|([^{}]*)\}", text_))
    return _FakeClip(shown_, spoken, 0.25 + n * 0.158 / speed)


VOICE_PAUSES = (0.0, 0.10)    # 読点は元の声の間（中央値約0.33秒）のまま。文の間だけ少し足す。v3 で語の途中には入らない
NUM_BREATH = 0.35
CH_BREATH = 0.35


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and not it.id.startswith("c0_") and any(ch.isdigit() for ch in split_reading(it.text)[0]):
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, safe_pauses=True, **kw)


lf.use()
# 文字は太いゴシック（メイリオの太字）。手書き体（Klee One）は使わない
core.FONT = "Meiryo"
core.FONT_FILE = Path("C:/Windows/Fonts/meiryob.ttc")
core.STROKE = 0.0

_syn = _fake_synth if FAKE else _voice_synth
_ITEMS = _breathe(_items())
tl = lf.Timeline(_ITEMS, VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


# ============================================================
# 場面の合図（文の一部で探す。見つからなければ止める）
# ============================================================
ANCH = {
    # 0 帰ってこられますか
    "c0_q": (0, "サケの卵だったら"),
    "c0_10k": (0, "卵1万粒で計算すると"), "c0_res": (0, "約80匹でした"), "c0_med": (0, "何度もくり返し"), "c0_call": (0, "中央値です"),
    # 1 サケの一生
    "c1_aki": (1, "親のサケが川へ"), "c1_haru": (1, "春に、卵から"), "c1_winter": (1, "海で最初の冬を越します"), "c1_ocean": (1, "北の海を何年も泳ぎ"),
    "c1_4th": (1, "多くは4年目"), "c1_net": (1, "この3つの関門"), "c1_four": (1, "この3つの関門"),
    # 2 運だけなら、あなたはどこまで行ける？
    "c2_intro": (2, "最初の問いです"), "c2_yoso": (2, "いちばん危ないのは"), "c2_g1": (2, "最初の関門は"), "c2_def": (2, "この動画では、卵が"),
    "c2_chitose": (2, "千歳川で調べた"), "c2_medyou": (2, "どこまで進めたか"), "c2_nb": (2, "生まれることもできません"), "c2_worstyou": (2, "いちばん運の悪い1粒"),
    "c2_g2": (2, "川を下り始めた2,000匹"), "c2_9": (2, "最初の冬を越せるのは"), "c2_g3": (2, "三つ目の関門"), "c2_calc": (2, "133匹のうち、帰ってきて"),
    "c2_med82": (2, "82匹がちょうど真ん中"), "c2_worst": (2, "いちばん少ない回"), "c2_best": (2, "いちばん多い回"), "c2_bestyou": (2, "いちばん運の良かった1粒"),
    "c2_spring": (2, "あなたは春に"), "c2_win": (2, "最初の冬を越すころ"), "c2_circ": (2, "何年も泳ぎ回ります"), "c2_stay": (2, "いなくなる仲間は"),
    "c2_home": (2, "帰ってきました"), "c2_netis": (2, "川の手前には"), "c2_3way": (2, "行き先は、3つ"), "c2_85": (2, "1つ目は"), "c2_trap": (2, "2つ目は"), "c2_third": (2, "3つ目は、捕まらずに"), "c2_sum": (2, "1つ目と2つ目の合計"), "c2_more": (2, "82匹より多いはず"), "c2_70": (2, "70匹あまりは"),
    "c2_gap": (2, "誰も数えていません"), "c2_10": (2, "中央値で10匹でした"), "c2_upyou": (2, "いちばん運の良いあなたは"), "c2_table": (2, "私たちの食卓"), "c2_where": (2, "どこでいなくなる"),
    "c2_b1": (2, "卵1万粒のうち8,000粒は"), "c2_b2": (2, "残った2,000匹のうち"), "c2_b3": (2, "133匹のうち51匹"), "c2_hon": (2, "ふるい落とされる"), "c2_ans": (2, "答えです"),
    # 3 川か放流か、生まれ方で変わる？
    "c3_intro": (3, "二つ目の問いです"), "c3_hatch": (3, "人が卵を育てて"), "c3_yoso": (3, "ほとんど帰ってくる"), "c3_only1": (3, "川生まれと違うのは"),
    "c3_tank": (3, "水槽の中で守られて"), "c3_875": (3, "8,750粒ほど"), "c3_chit": (3, "千歳川という1本の川"),
    "c3_other": (3, "ほかの川では"), "c3_move": (3, "ふ化場の卵1万粒で"), "c3_4x": (3, "川生まれの4倍"), "c3_589": (3, "589匹でした"),
    "c3_more": (3, "ずっと多いです"), "c3_9": (3, "最初の冬は厳しい"), "c3_364": (3, "中央値で364匹"), "c3_cmp": (3, "川生まれの82匹と"), "c3_low": (3, "500匹と低く見ると"),
    "c3_zoom": (3, "ふ化場で生まれた真ん中の1粒"), "c3_spring": (3, "水槽の中で春を"), "c3_nogravel": (3, "もう砂利の中で"),
    "c3_endwin": (3, "最初の冬までに終わります"), "c3_8of10": (3, "8,000匹あまり"), "c3_same2": (3, "最初の冬は越えにくい"), "c3_moved": (3, "1つ先に進みました"),
    "c3_ans": (3, "答えです"),
    # 4 大きく育つと、有利？
    "c4_intro": (4, "三つ目の問いです"), "c4_1g": (4, "体重1グラム"), "c4_dir": (4, "資料でも報告"), "c4_01": (4, "どれくらい有利かは"), "c4_kaiki": (4, "回帰率という言葉"),
    "c4_def": (4, "人に捕まったサケの割合"), "c4_notenough": (4, "左右するのは"), "c4_years": (4, "生まれた年によって"), "c4_high": (4, "いちばん高く"),
    "c4_7": (4, "7匹あまり"), "c4_low": (4, "いちばん低く"), "c4_1": (4, "1匹ほどです"), "c4_64": (4, "約6.4倍です"), "c4_143": (4, "143匹"),
    "c4_22": (4, "22匹です"), "c4_choose": (4, "あなたは選べません"), "c4_ans": (4, "答えです"),
    # 5 お母さん1匹の卵から、何匹帰ってくる？
    "c5_intro": (5, "最後の問いです"), "c5_3000": (5, "3,000粒とします"), "c5_once": (5, "1度産卵すると"), "c5_two": (5, "オスとメスが1匹ずつ"), "c5_yoso": (5, "楽に残ると"),
    "c5_10k": (5, "お母さん1万匹ぶん"), "c5_gates": (5, "3つの関門を進みます"), "c5_lot": (5, "29年分の実際の回帰率"), "c5_riv": (5, "千歳川の推定を使います"),
    "c5_24": (5, "平均で約24匹"), "c5_enough": (5, "楽に残りそうに見えます"), "c5_split": (5, "生まれた年で分けて"), "c5_oldnew": (5, "昔の年、"),
    "c5_table": (5, "昔の年は約29匹でした"), "c5_need": (5, "捕られる分とは別に"),
    "c5_19": (5, "約3分の1に減ったことに"), "c5_dir": (5, "生き残りをどう見ても"), "c5_why": (5, "捕られるほど、サケが帰ってきました"), "c5_notsay": (5, "別に必要な2匹が"),
    "c5_zoom": (5, "今度は、あなたがお母さんです"), "c5_egg": (5, "砂利の中へ卵を産み"), "c5_most": (5, "卵のほとんどは"),
    "c5_10": (5, "約10匹の計算"), "c5_2of10": (5, "その10匹とは別に"), "c5_old": (5, "昔なら"), "c5_ans": (5, "答えです"),
    # 6 まとめ
    "c6_0": (6, "卵1万粒のうち"), "c6_0b": (6, "いちばん減るのは"), "c6_1": (6, "昔の約3分の1に減りました"), "c6_2": (6, "2匹が残れているかは"), "c6_3": (6, "どこまで行けたと思いますか"),
    "c6_4": (6, "仮定を置いた"), "c6_sub": (6, "チャンネル登録"),
}
def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in split_reading(txt)[0]]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の並び（名前, 始まり, 描く関数の名前）。始まり: 合図のキー＝その文の頭の1.05秒前 ／ "ch:N"＝章カードのあと ／ "z:キー"＝0章（前の文の終わり）----
SC_TABLE = [
    ("open", "zero", "sc_open"), ("c0_10k", "z:c0_10k", "sc_c0_10k"),
    ("c1_map", "ch:1", "sc_c1_map"),
    ("c2_a", "ch:2", "sc_c2_a"), ("c2_b", "c2_g1", "sc_c2_b"), ("c2_c", "c2_medyou", "sc_c2_c"), ("c2_d", "c2_g2", "sc_c2_d"), ("c2_e", "c2_g3", "sc_c2_e"),
    ("c2_f", "c2_med82", "sc_c2_f"), ("c2_h1", "c2_bestyou", "sc_c2_h1"), ("c2_h2", "c2_win", "sc_c2_h2"), ("c2_h3", "c2_circ", "sc_c2_h3"),
    ("c2_h4", "c2_home", "sc_c2_h4"), ("c2_i1", "c2_netis", "sc_c2_i1"), ("c2_i2", "c2_gap", "sc_c2_i2"), ("c2_i3", "c2_table", "sc_c2_i3"),
    ("c2_j", "c2_where", "sc_c2_j"), ("c2_ans", "c2_ans", "sc_c2_ans"),
    ("c3_a", "ch:3", "sc_c3_a"), ("c3_b", "c3_only1", "sc_c3_b"), ("c3_c", "c3_move", "sc_c3_c"), ("c3_d", "c3_589", "sc_c3_d"), ("c3_e", "c3_364", "sc_c3_e"),
    ("c3_f", "c3_cmp", "sc_c3_f"), ("c3_g", "c3_zoom", "sc_c3_g"), ("c3_h", "c3_endwin", "sc_c3_h"), ("c3_i", "c3_same2", "sc_c3_i"),
    ("c3_ans", "c3_ans", "sc_c3_ans"),
    ("c4_a", "ch:4", "sc_c4_a"), ("c4_b", "c4_kaiki", "sc_c4_b"), ("c4_bars", "c4_notenough", "sc_c4_bars"), ("c4_ans", "c4_ans", "sc_c4_ans"),
    ("c5_a", "ch:5", "sc_c5_a"), ("c5_b", "c5_once", "sc_c5_b"), ("c5_c", "c5_yoso", "sc_c5_c"), ("c5_d", "c5_10k", "sc_c5_d"), ("c5_e", "c5_lot", "sc_c5_e"),
    ("c5_f", "c5_24", "sc_c5_f"), ("c5_table", "c5_split", "sc_c5_table"), ("c5_bars", "c5_why", "sc_c5_bars"), ("c5_net", "c5_notsay", "sc_c5_net"),
    ("c5_g1", "c5_zoom", "sc_c5_g1"), ("c5_g2", "c5_most", "sc_c5_g2"), ("c5_g3", "c5_2of10", "sc_c5_g3"), ("c5_ans", "c5_ans", "sc_c5_ans"),
    ("c6_answers", "ch:6", "sc_c6_answers"), ("c6_close", "c6_3", "sc_c6_close"), ("end", "end", "sc_end"),
]

# ---- 場面の切りかえの間: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c2_chitose": 3.0, "c2_9": 2.5, "c3_4x": 2.0, "c3_364": 3.0, "c5_dir": 1.7}


def _pace(items):
    need = {}
    for k in SCENE_KEYS:
        need[ID[k]] = max(need.get(ID[k], 0.0), SCENE_GAP)
    after = {ID[k]: v for k, v in HOLD_AFTER.items()}
    out = list(items)
    for j, it in enumerate(out):
        if not isinstance(it, lf.Line):
            continue
        p = it.pause
        nx = out[j + 1] if j + 1 < len(out) else None
        if isinstance(nx, lf.Line) and nx.id in need and not nx.id.startswith("c0_"):
            p = max(p, need[nx.id])
        if it.id in after:
            p = max(p, after[it.id])
        if p != it.pause:
            out[j] = lf.Line(it.id, it.text, pause=p, speed=it.speed)
    return out


def rebuild_timeline():
    global tl, S, E, DUR, _ITEMS
    _ITEMS = _pace(_ITEMS)
    tl = lf.Timeline(_ITEMS, VOICE_DIR, lead=0.5, synth=_syn)
    S, E = tl.start, tl.end
    DUR = tl.duration


rebuild_timeline()


def fix_reading_shown(lid):
    """声に渡す字（読みの補正つき）から、画面に出る字を取り出す（照合用）"""
    it = next(x for x in _ITEMS if isinstance(x, lf.Line) and x.id == lid)
    return it.text


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


REST = [g_ for g_ in GAP_NOTE if "区切り" in GAP_NOTE[g_]]
T_RS0 = S(REST[0]) if len(REST) == 1 else 0.0
T_RS1 = E(REST[0]) if len(REST) == 1 else 0.0
T_ES = Sk("c6_sub") - 0.3

# ============================================================
# データ（data.json と、模型と同じ関数・同じ種で取り出した1万回の結果）
# ============================================================
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
_rng = np.random.default_rng(sm.SEED)                   # salmon_model.main と同じ順に chain を呼ぶ（問い1の20%・10%・5%、そのあと問い2）
CH_R = sm.chain(_rng, sm.P_RIVER)
sm.chain(_rng, sm.P_RIVER_LOW[1])
sm.chain(_rng, sm.P_RIVER_LOW[0])
CH_H = sm.chain(_rng, sm.P_HATCH)
BACK_R, BACK_H = CH_R[2], CH_H[2]                       # 帰ってくる数の1万回
Q1, Q2, Q3, Q4 = RES["q1"], RES["q2"], RES["q3"], RES["q4"]
YEARS = {int(k): v for k, v in RES["years"].items()}
TAB = RES["table"]

# ============================================================
# 見た目（共通の道具: danchi-long.py と同じ札・線・場面の仕組み）
# ============================================================
W_, H_ = lf.W, lf.H
WHITE, YEL, PALE, REDC = "#ffffff", "#ffe14a", "#d6e2f5", "#e8505b"
YOU, EGGC, FISHC = "#f39a4a", "#dbe6f5", "#9db7df"
PANEL = "#10284a"
BASE_BG = "#17365f"


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


def seg(t, a, b):
    return clamp01((t - a) / max(1e-6, b - a))


def lerp(a, b, u):
    return a + (b - a) * u


def grp(ctx, a, fn, *args):
    if a <= 0.003:
        return
    if a >= 0.997:
        fn(ctx, *args)
        return
    ctx.push_group()
    fn(ctx, *args)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def nolog(fn, *args, **kw):
    saved = core._LOG
    core._LOG = None
    try:
        return fn(*args, **kw)
    finally:
        core._LOG = saved



def paint_bg(ctx, col):
    fill(ctx, col)
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()


def panel(ctx, rows, x, y, a=1.0, align="center", bg=PANEL, pad=(28, 16), r=16, border=None, gap=1.22):
    """札（文字の板）。rows = [(文字, 大きさ, 色), …] または 文字列（白・48px）。板は不透明（下の文字を消す）。
    (x, y) は align='center' なら中心、'left' なら左端・中心の高さ。戻り値 (x0, y0, x1, y1)"""
    if isinstance(rows, str):
        rows = [(s_, 48, WHITE) for s_ in rows.split("\n")]
    if a <= 0.003:
        return (x, y, x, y)
    ws = [text_width(s_, sz) for s_, sz, _c in rows]
    hs = [sz * gap for _s, sz, _c in rows]
    w = max(ws) + 2 * pad[0]
    h = sum(hs) + 2 * pad[1] - (rows[-1][1] * (gap - 1.0))
    x0 = x - w / 2 if align == "center" else x
    y0 = y - h / 2
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, x0, y0, w, h, r)
    ctx.fill()
    if border:
        ctx.set_source_rgba(*hexrgb(border, a))
        ctx.set_line_width(4)
        rrect(ctx, x0 + 2, y0 + 2, w - 4, h - 4, r - 2)
        ctx.stroke()
    cy = y0 + pad[1]
    for (s_, sz, col), hh in zip(rows, hs):
        cy_c = cy + sz / 2
        if align == "center":
            text(ctx, s_, x, cy_c, sz, col, alpha=a)
        else:
            text(ctx, s_, x0 + pad[0], cy_c, sz, col, align="left", alpha=a)
        cy += hh
    return (x0, y0, x0 + w, y0 + h)


def label(ctx, s, x, y, size=48, col=WHITE, a=1.0, align="center"):
    if a > 0.003:
        text(ctx, s, x, y, size, col, align=align, alpha=a)



def line2(ctx, p, q, col, w, a=1.0, dash=None):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_dash(dash or [])
    ctx.move_to(*p)
    ctx.line_to(*q)
    ctx.stroke()
    ctx.set_dash([])


def arrow2(ctx, p, q, col, w=10.0, a=1.0, head=30.0):
    line2(ctx, p, q, col, w, a)
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.move_to(q[0] + 8 * math.cos(ang), q[1] + 8 * math.sin(ang))
    ctx.line_to(q[0] - head * math.cos(ang - 0.5), q[1] - head * math.sin(ang - 0.5))
    ctx.line_to(q[0] - head * math.cos(ang + 0.5), q[1] - head * math.sin(ang + 0.5))
    ctx.close_path()
    ctx.fill()


def box(ctx, x0, y0, x1, y1, col, a=1.0, r=10):
    fill(ctx, hexrgb(col, a))
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, r)
    ctx.fill()



# ============================================================
# 場面の仕組み（hikyaku-long.py と同じ）: 前の場面が消えてから次が出る
# ============================================================
SCENES = []
SC_IN, SC_OUT, SC_DELAY = 0.25, 0.2, 0.2
SC_START = {}


def scene(name, t0, t1, fn, first=False):
    SCENES.append((name, t0, t1, fn, first))
    SC_START[name] = t0


def draw_scenes(ctx, t):
    for name, t0, t1, fn, first in SCENES:
        if t < t0 - 1e-6 or t > t1 + SC_OUT:
            continue
        a_in = 1.0 if first else ease_out(clamp01((t - t0 - SC_DELAY) / SC_IN))
        a = a_in * (1.0 - clamp01((t - t1) / SC_OUT))
        grp(ctx, a, fn, t)


def bd(key, lead=1.05):
    return Sk(key) - lead


def bz(key):
    return Sk(key) - 0.3


def T(key, f=0.0, off=0.0):
    return Sk(key, f) + off



# ---------- 魚・卵・群れ（sims/salmon_art.py の絵を使う。小さい魚は絵にして使い回す）----------
_FS = {}


def fish(ctx, x, y, L, color=FISHC, kind="fry", phase=0.0, facing=1, a=1.0, face=True):
    """魚を1匹（x, y は体の中心・L は鼻先から尾の先まで）。小さい魚は画像にして貼る（見た目は draw_fish と同じ）"""
    if a <= 0.003:
        return
    if L >= 240:
        draw_fish(ctx, x, y, L, color, kind, phase, facing, a, face)
        return
    Lq = max(16, int(round(L / 8.0)) * 8)
    ph = int(round((phase % 1.0) * 8)) % 8
    key = (color, kind, Lq, facing, ph, face)
    sp = _FS.get(key)
    if sp is None:
        w, h = int(Lq * 1.3) + 8, int(Lq * 0.8) + 8
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(surf)
        draw_fish(c, w / 2, h / 2, Lq, color, kind, ph / 8, facing, 1.0, face)
        if len(_FS) > 3000:
            _FS.clear()
        _FS[key] = sp = (surf, w / 2, h / 2)
    surf, ox, oy = sp
    sc = L / Lq
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    ctx.set_source_surface(surf, -ox, -oy)
    ctx.paint_with_alpha(a)
    ctx.restore()


def fish_dir(ctx, x, y, L, color, kind, ang, phase=0.0, a=1.0):
    """進む向き ang（ラジアン）に頭を向けた魚（左へ進むときは裏返して、背中が上のまま）"""
    ctx.save()
    ctx.translate(x, y)
    if math.cos(ang) >= 0:
        ctx.rotate(ang)
        fc = 1
    else:
        ctx.rotate(ang - math.pi)
        fc = -1
    fish(ctx, 0, 0, L, color, kind, phase, fc, a)
    ctx.restore()


def glow(ctx, x, y, r, a=0.28):
    fill(ctx, hexrgb("#ffffff", a))
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def you_egg(ctx, t, x, y, r, a=1.0, pulse=1.0, sway=3.0):
    g = (0.22 + 0.10 * math.sin(t * 3.0)) * pulse
    dy = math.sin(t * 1.3) * sway
    glow(ctx, x, y + dy, r * 1.28, g * a)
    draw_egg(ctx, x, y + dy, r, YOU, True, a)


def you_fish(ctx, t, x, y, L, kind="fry", a=1.0, ang=0.0, glow_r=None):
    if glow_r:
        glow(ctx, x, y, glow_r, (0.22 + 0.08 * math.sin(t * 3.0)) * a)
    fish_dir(ctx, x, y, L, YOU, kind, ang, t * 1.6, a)


def ramp(idxs, t0, t1):
    """idxs の各要素に t0〜t1 の等間隔の時刻をわりふる（{番号: 時刻}）"""
    n = len(idxs)
    return {i: t0 + (t1 - t0) * k / max(1, n - 1) for k, i in enumerate(idxs)}


def shuffled(n, seed, keep=()):
    r_ = [i for i in range(n) if i not in keep]
    random.Random(seed).shuffle(r_)
    return r_


def _grid_cols(x0, y0, x1, y1, n, cols, rnd, jitter):
    """列の数を決めて並べる（_grid と同じ半分ずらし）。行 = ceil(n / cols)"""
    rows = max(1, math.ceil(n / cols))
    pts = []
    for j in range(rows):
        for i in range(cols):
            cx = (i + (0.25 if j % 2 else 0.75) + rnd.uniform(-jitter, jitter)) / cols
            cy = (j + 0.5 + rnd.uniform(-jitter, jitter)) / rows
            pts.append((x0 + (x1 - x0) * cx, y0 + (y1 - y0) * cy, rnd.random()))
    return sorted(pts, key=lambda p: p[1])


def _exact(pts, n, rnd):
    """_grid が返した点が n 個より多ければ、ランダムに間引いて n 個にする（1匹＝○匹の絵の数をそろえる）"""
    if len(pts) > n:
        drop = set(rnd.sample(range(len(pts)), len(pts) - n))
        pts = [p for i, p in enumerate(pts) if i not in drop]
    return pts


class Bed:
    """卵の粒（うすい色）。box いっぱいに n 粒ほど。fade={番号: 消え始める時刻}・appear={番号: 出る時刻}。keepout=(x, y, 半径) の中は描かない"""

    def __init__(self, box, n, r, seed=1, keepout=None, color=EGGC, cols=None):
        rnd = random.Random(seed)
        pts = _grid_cols(box[0], box[1], box[2], box[3], n, cols, rnd, 0.28) if cols else _grid(box[0], box[1], box[2], box[3], n, rnd, 0.28)
        pts = _exact(pts, n, rnd)
        self.pts = [(x, y, ph) for x, y, ph in pts if _clear(x, y, keepout)]
        self.n = len(self.pts)
        self.color = color
        self.rr = [r * (0.92 + 0.13 * p[2]) for p in self.pts]

    def draw(self, ctx, t, fade=None, fd=0.9, appear=None, a=1.0, sway=3.0, hide=(), upto=None):
        for i, (x, y, ph) in enumerate(self.pts):
            if i in hide or (upto is not None and i >= upto):
                continue
            al = a
            if fade and i in fade:
                al *= 1 - clamp01((t - fade[i]) / fd)
            if appear and i in appear:
                al *= clamp01((t - appear[i]) / 0.35)
            if al <= 0.02:
                continue
            draw_egg(ctx, x + math.cos(t * 1.0 + ph * 5) * sway * 0.6, y + math.sin(t * 1.3 + ph * 6.28) * sway, self.rr[i], self.color, False, al)


class Swarm:
    """魚の群れ。ex={番号: 泳ぎ去り始める時刻}（右へ1匹ずつ画面の外へ）・fade・appear は Bed と同じ"""

    def __init__(self, box, n, L, kind="fry", color=FISHC, seed=1, facing=1, keepout=None, cols=None):
        rnd = random.Random(seed)
        pts = _grid_cols(box[0], box[1], box[2], box[3], n, cols, rnd, 0.2) if cols else _grid(box[0], box[1], box[2], box[3], n, rnd, 0.2)
        pts = _exact(pts, n, rnd)
        self.pts = [(x, y, ph) for x, y, ph in pts if _clear(x, y, keepout)]
        self.n = len(self.pts)
        self.L, self.kind, self.color, self.facing = L, kind, color, facing
        self.dep = [0.9 + 0.18 * (p[1] - box[1]) / max(1, box[3] - box[1]) for p in self.pts]

    def pos(self, i, t, ex=None, vx=520.0, swim=True, dx=0.0, dy=0.0, cruise=0.0, ct0=0.0):
        x, y, ph = self.pts[i]
        xx, yy = x + dx, y + dy
        if cruise:
            xx = ((xx + (t - ct0) * cruise * (0.8 + 0.4 * ph) * self.facing + 220) % (W_ + 440)) - 220
        if swim:
            xx += math.cos(t * 0.9 + ph * 6.28) * 9
            yy += math.sin(t * 1.2 + ph * 5) * 6
        if ex and i in ex and t > ex[i]:
            u = t - ex[i]
            xx += self.facing * (u * vx * (0.8 + 0.5 * ph) + 60 * u * u)
        return xx, yy

    def draw(self, ctx, t, ex=None, fade=None, fd=0.7, appear=None, a=1.0, vx=520.0, swim=True, hide=(), dx=0.0, dy=0.0, color=None, scale=1.0, cruise=0.0, ct0=0.0):
        for i in range(self.n):
            if i in hide:
                continue
            xx, yy = self.pos(i, t, ex, vx, swim, dx, dy, cruise, ct0)
            if xx - self.L > W_ + 40 or xx + self.L < -40:
                continue
            al = a
            if fade and i in fade:
                al *= 1 - clamp01((t - fade[i]) / fd)
            if appear and i in appear:
                al *= clamp01((t - appear[i]) / fd)
            if al <= 0.02:
                continue
            fish(ctx, xx, yy, self.L * self.dep[i] * scale, color or self.color, self.kind, t * 1.6 + self.pts[i][2], self.facing, al)


# ---------- 背景 ----------
def bg_gravel(ctx, top=330):
    gravel_bed(ctx, W_, H_, top)


def bg_mouth(ctx):
    river_mouth(ctx, W_, H_)


def bg_sea(ctx):
    north_sea(ctx, W_, H_)


def snow(ctx, t, a=1.0, y1=H_ * 0.92):
    """冬の雪（白い点がゆっくり落ちる）"""
    if a <= 0.003:
        return
    for k in range(46):
        x = (k * 197 + 40 * math.sin(t * 0.5 + k)) % W_
        y = (k * 83 + t * 55) % y1
        fill(ctx, hexrgb("#ffffff", 0.7 * a))
        ctx.arc(x, y, 4 + (k % 3) * 2, 0, 2 * math.pi)
        ctx.fill()


def winter_sky(ctx, u):
    """河口の空が冬の色になる（u 0〜1）"""
    if u <= 0.003:
        return
    fill(ctx, hexrgb("#cfd8e6", u))
    ctx.rectangle(0, 0, W_, H_ * 0.3)
    ctx.fill()
    fill(ctx, hexrgb("#b7c8e0", 0.35 * u))
    ctx.rectangle(0, H_ * 0.3, W_, H_)
    ctx.fill()


def flat(ctx, col=BASE_BG):
    fill(ctx, col)
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()


def layers(ctx, t, specs, xf=0.35):
    """specs = [(t0, t1, fn), …]。t0〜t1 の間だけ fn(ctx, t) を描く。前後 xf 秒で重ねて切りかえる"""
    for t0, t1, fn in specs:
        if t < t0 - 1e-6 or t > t1 + xf:
            continue
        a = (1.0 if t0 <= 0 else clamp01((t - t0) / xf)) * (1 - clamp01((t - t1) / xf))
        grp(ctx, a, fn, t)


# ---------- 札の出し入れ ----------
def card(ctx, t, t0, t1, rows, x, y, **kw):
    """札 rows を t0 から t1 まで（前後に 0.3 秒のフェード）。t1 が None なら出しっぱなし"""
    if t < t0:
        return
    a = fade(t, t0, 0.3) * (1.0 if t1 is None else out_fade(t, t1, 0.3))
    if a > 0.003:
        panel(ctx, rows, x, y, a=a, **kw)


def tag(ctx, t, t0, t1, s, x, y, size=46, col=WHITE, **kw):
    card(ctx, t, t0, t1, [(s, size, col)], x, y, **kw)


# ---------- 関門の札（4枚）----------
G_ROWS = [["関門1", "生まれられるか"], ["関門2", "最初の冬を", "越えられるか"], ["関門3", "海から", "帰ってこられるか"], ["そのあと", "沿岸の網"]]
GX, GW = [255, 725, 1195, 1665], 430


def gate_row(ctx, t, y=520, h=250, lit=None, a=1.0, t_in=None, size=46, hi=()):
    """4つの関門の札を横に並べる。lit=光らせる番号（黄色い縁）・t_in=各札が出る時刻・hi=薄く沈める番号"""
    for k, rows in enumerate(G_ROWS):
        ak = a
        if t_in is not None:
            ak *= fade(t, t_in[k], 0.35)
        if ak <= 0.003:
            continue
        x = GX[k]
        on = (lit == k) or (isinstance(lit, (list, tuple)) and k in lit)
        box(ctx, x - GW / 2, y - h / 2, x + GW / 2, y + h / 2, "#1f4a82" if on else PANEL, ak, r=22)
        if on:
            ctx.set_source_rgba(*hexrgb(YEL, ak))
            ctx.set_line_width(7)
            rrect(ctx, x - GW / 2 + 4, y - h / 2 + 4, GW - 8, h - 8, 20)
            ctx.stroke()
        n = len(rows)
        step = 62
        y0 = y - step * (n - 1) / 2
        for j, s_ in enumerate(rows):
            label(ctx, s_, x, y0 + j * step, 54 if j == 0 else size, YEL if j == 0 else WHITE, a=ak * (0.55 if k in hi else 1.0))


# ---------- 地図（北海道・オホーツク海・北の海）----------
def _catmull(pts, n=22):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            u = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u * u
                                     + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u ** 3) for j in (0, 1)))
    out.append(pts[-1])
    return out


MAP_KEY = [map_xy(*p) for p in (
    (143.0, 43.30), (143.3, 43.55), (143.65, 43.8), (143.95, 43.95), (144.3, 44.05),     # 川（北海道の中）→ 河口（オホーツク海の岸）
    (145.2, 45.0), (147.2, 47.3), (149.5, 49.8), (152.0, 50.8),                           # オホーツク海
    (154.5, 48.6), (156.5, 46.0), (160.0, 44.5), (166.0, 46.5), (171.5, 50.5), (170.5, 55.0),   # 千島の外へ出て、北の海をぐるりと回る
    (165.5, 54.0), (162.5, 50.0), (158.0, 46.5), (152.0, 45.2), (148.0, 44.9), (145.6, 44.6),   # 戻る
    (144.35, 44.12), (143.95, 43.95), (143.3, 43.55), (143.0, 43.30))]   # 河口 → 川
MAP_PTS = _catmull(MAP_KEY)
MAP_CUM = [0.0]
for _i in range(1, len(MAP_PTS)):
    MAP_CUM.append(MAP_CUM[-1] + math.hypot(MAP_PTS[_i][0] - MAP_PTS[_i - 1][0], MAP_PTS[_i][1] - MAP_PTS[_i - 1][1]))
MAP_LEN = MAP_CUM[-1]


def _map_idx_u(pt):
    i = min(range(len(MAP_PTS)), key=lambda k: math.hypot(MAP_PTS[k][0] - pt[0], MAP_PTS[k][1] - pt[1]))
    return MAP_CUM[i] / MAP_LEN


U_MOUTH = _map_idx_u(MAP_KEY[4])        # 河口を出る
U_OKH = _map_idx_u(MAP_KEY[8])          # オホーツク海を出る
U_LOOP1 = _map_idx_u(MAP_KEY[14])       # 北の海を回り終える
U_BACK = _map_idx_u(MAP_KEY[21])        # 河口にもどる


def map_pos(u):
    d = clamp01(u) * MAP_LEN
    lo, hi = 0, len(MAP_CUM) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if MAP_CUM[mid] <= d:
            lo = mid
        else:
            hi = mid
    a, b = MAP_PTS[lo], MAP_PTS[hi]
    f = (d - MAP_CUM[lo]) / max(1e-6, MAP_CUM[hi] - MAP_CUM[lo])
    x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
    return x, y, math.atan2(b[1] - a[1], b[0] - a[0])


def _poly(ctx, pts, col, smooth=True):
    fill(ctx, hexrgb(col))
    ctx.move_to(*pts[0])
    if smooth:
        sm_ = _catmull(pts + [pts[0], pts[1]], 8)
        for p in sm_:
            ctx.line_to(*p)
    else:
        for p in pts[1:]:
            ctx.line_to(*p)
    ctx.close_path()
    ctx.fill()


def _land(ctx, pts, col):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(col))
    ctx.fill_preserve()
    ctx.set_line_width(1.5)
    ctx.stroke()


def draw_map(ctx, t, u_trail=0.0, labels=(), a_lab=1.0):
    """平塗りの簡単な地図。u_trail=通ってきた道（0〜1）を白い点線で。labels=出す名札の名前の一覧"""
    fill(ctx, hexrgb("#2a6a9c"))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    fill(ctx, hexrgb("#235f90"))                                    # 北の海（北太平洋とベーリング海）を少し濃く
    cx_, cy_ = map_xy(165.5, 49.5)
    ctx.arc(cx_, cy_, 380, 0, 2 * math.pi)
    ctx.fill()
    # 陸の形は Natural Earth（salmon_make_map.py）。国境の継ぎ目が出ないように同じ色の線でふちどる
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for pts in MAP_OTHERS:
        _land(ctx, pts, "#9ec47f")
    _land(ctx, [(x + 4, y + 5) for x, y in MAP_HOKKAIDO], "#86ac6c")
    _land(ctx, MAP_HOKKAIDO, "#a9cf8a")
    # 川（北海道の中を河口へ）
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(9)
    ctx.set_source_rgba(*hexrgb("#9fd4f2"))
    ks = MAP_PTS[:next(i for i, c in enumerate(MAP_CUM) if c / MAP_LEN >= U_MOUTH)]
    ctx.move_to(*ks[0])
    for p in ks[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    if u_trail > 0.002:
        ctx.set_source_rgba(1, 1, 1, 0.7)
        ctx.set_line_width(7)
        ctx.set_dash([4, 16])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        n = max(2, int(len(MAP_PTS) * clamp01(u_trail)))
        ctx.move_to(*MAP_PTS[0])
        for p in MAP_PTS[1:n]:
            ctx.line_to(*p)
        ctx.stroke()
        ctx.set_dash([])
    pos = {"北海道": map_xy(146.0, 41.3), "川": map_xy(141.2, 44.6), "河口": map_xy(147.0, 43.6), "オホーツク海": map_xy(149.5, 53.6), "北の海": map_xy(166.0, 44.6)}
    for nm in labels:
        x, y = pos[nm]
        panel(ctx, [(nm, 46, WHITE)], x, y, a=a_lab, pad=(22, 8), r=12)


# ---------- 山（1万回の結果を1マス＝100回で積む）----------
def pile(ctx, t, counts, binw, vmax, x0, x1, ybase, t0, step, unit=100, th=26, hi_bin=None, t_hi=0.0, a=1.0, col=FISHC):
    """counts[k] = 区間 [k*binw, (k+1)*binw) に入った回数。柱が左から1本ずつ、step 秒おきに立つ。値 v の位置は pile_x"""
    bw = (x1 - x0) / (vmax / binw)
    for k, c in enumerate(counts):
        tk = t0 + k * step
        if t < tk or c <= 0:
            continue
        g = ease_out(clamp01((t - tk) / 0.3))
        n = c / unit
        cc = YOU if (hi_bin == k and t >= t_hi) else col
        full = int(n)
        xk = x0 + k * bw + 3
        for j in range(full + 1):
            frac = 1.0 if j < full else n - full
            if frac < 0.08:
                continue
            h = th * frac
            y = ybase - (j + 1) * (th + 2) + (th - h)
            box(ctx, xk, y, xk + bw - 6, y + h, cc, a * g, r=3)


def pile_x(v, binw, vmax, x0, x1):
    return x0 + v / vmax * (x1 - x0)


# ---------- 答えの場面 ----------
def answer_scene(ctx, t, key, rows, you_kind="egg", y=330):
    tc = T(key, 0.1)
    label(ctx, "答え", 960, 130, 72, YEL)
    panel(ctx, rows, 960, y, a=fade(t, tc), border=YEL, pad=(60, 30))
    a = fade(t, bd(key) + 0.5)
    if you_kind == "egg":
        you_egg(ctx, t, 960, 710, 150, a=a)
    elif you_kind == "fry":
        you_fish(ctx, t, 960, 700, 520, "fry", a=a, glow_r=300)
    elif you_kind == "adult":
        you_fish(ctx, t, 960, 700, 640, "adult", a=a, glow_r=330)


# ---- 章カード（平たい板・問いの番号は黄色）----
CARD_BY_N = {1: ["サケの一生"], 2: ["問い1", "運だけなら、あなたは、", "どこまで行ける？"], 3: ["問い2", "川か放流か、", "生まれ方で変わる？"],
             4: ["問い3", "大きく育つと、有利？"], 5: ["問い4", "お母さん1匹の卵から、", "何匹帰ってくる？"], 6: ["まとめ"]}
CARD_LINES = {s_ for v in CARD_BY_N.values() for s_ in v}
CARD_HOLD = {n: max(3.0, len("".join(v)) / 8 + 1 + 0.4) for n, v in CARD_BY_N.items()}
T_TITLE = {n: CARD_HOLD[n] + 0.2 for n in CARD_BY_N}
CH_TITLES = [c["title"] for c in CHAPS]


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        n = CHAPS[ch[0]]["n"]
        age = t - ch[1]
        hold = CARD_HOLD.get(n, 3.0)
        if 0 <= age <= hold:
            a = clamp01(age / 0.35) * clamp01((hold - age) / 0.4)
            rows = CARD_BY_N[n]
            rr = [(s_, 76, YEL if (s_.startswith("問い") or s_ == "まとめ") else WHITE) for s_ in rows]
            sc = 0.92 + 0.08 * ease_out(a)
            ctx.save()
            ctx.translate(960, 440)
            ctx.scale(sc, sc)
            panel(ctx, rr, 0, 0, a=a, pad=(60, 34), border=YEL)
            ctx.restore()


def ch_start(n):
    return S(f"ch{n}")


def tri_down2(ctx, x, y, s, col, a=1.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.move_to(x - s, y - s * 1.1)
    ctx.line_to(x + s, y - s * 1.1)
    ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill()


def bubbles(ctx, t, n=8, y0=380, y1=40, x0=80, x1=980):
    for k in range(n):
        x = x0 + (x1 - x0) * ((k * 0.618) % 1.0)
        yy = y0 - ((t * 50 + k * 71) % (y0 - y1))
        fill(ctx, hexrgb("#ffffff", 0.45))
        ctx.arc(x + math.sin(t + k) * 8, yy, 7 + (k % 3) * 3, 0, 2 * math.pi)
        ctx.fill()


# ============================================================
# 0 帰ってこられますか
# ============================================================
QROWS = ["帰って", "こられますか？"]
OPEN_YOU = (520, 690)
OPEN_R = 190
OPEN_BED = Bed((50, 470, 1000, 915), 92, 27, seed=3, keepout=(OPEN_YOU[0], OPEN_YOU[1], 275))


def sc_open(ctx, t):
    bg_gravel(ctx, 400)
    bubbles(ctx, t)
    OPEN_BED.draw(ctx, t)
    you_egg(ctx, t, OPEN_YOU[0], OPEN_YOU[1], OPEN_R)
    panel(ctx, [("もしあなたが、", 60, WHITE), ("サケの卵だったら", 60, WHITE), (QROWS[0], 120, YEL), (QROWS[1], 110, YEL)], 1430, 470, pad=(36, 24), border=YEL)


RUN_BED = Bed((50, 450, 1870, 915), 120, 26, seed=5, keepout=(660, 690, 190))


def _run_split():
    return Sk("c0_run", 0.30), Sk("c0_run", 0.56)


def _egg_to_fry_gravel(ctx, t):
    t0, t1 = bz("c0_run"), _run_split()[0]
    bg_gravel(ctx, 380)
    RUN_BED.draw(ctx, t, sway=2.0)
    u = seg(t, t0 + 0.2, t1)
    cx, cy = lerp(660, 1520, ease(u)), lerp(690, 215, ease(u))
    a_egg = 1 - clamp01((t - t0) / 0.5)
    if a_egg > 0.02:
        you_egg(ctx, t, 660, 690, 120, a=a_egg)
    a_f = clamp01((t - t0 - 0.15) / 0.4)
    ang = -math.atan2(690 - 215, 860) * 0.9
    you_fish(ctx, t, cx, cy, 380, "fry", a=a_f, ang=ang, glow_r=140)


def _fry_mouth(ctx, t):
    t0, t1 = _run_split()
    bg_mouth(ctx)
    u = seg(t, t0 + 0.1, t1)
    winter_sky(ctx, seg(t, t0 + 0.3, t1 - 0.2))
    snow(ctx, t, seg(t, t0 + 0.4, t1))
    you_fish(ctx, t, lerp(-220, 2150, ease(u)), 600 + 30 * math.sin(t * 2), 420, "fry", ang=0.0, glow_r=150)


def _fry_map(ctx, t):
    t0 = _run_split()[1]
    u = ease(seg(t, t0 + 0.1, Ek("c0_run") + 0.1)) * U_BACK
    draw_map(ctx, t, u_trail=u)
    x, y, ang = map_pos(u)
    you_fish(ctx, t, x, y, 120, "adult", ang=ang, glow_r=62)


def sc_c0_run(ctx, t):
    a, b = _run_split()
    layers(ctx, t, [(0.0, a, _egg_to_fry_gravel), (a, b, _fry_mouth), (b, 1e9, _fry_map)], xf=0.3)


T_CARD0 = Sk("c0_res", 0.58)
T_C3 = Sk("c0_med", 0.0)
BED10 = Bed((60, 440, 1860, 910), 100, 30, seed=7)
YOU10 = min(range(BED10.n), key=lambda i: math.hypot(BED10.pts[i][0] - 1300, BED10.pts[i][1] - 740))
FISH80 = Swarm((70, 400, 960, 800), 80, 76, "adult", FISHC, seed=9, cols=10)
VAN10 = ramp(shuffled(BED10.n, 4, keep=(YOU10,)), Sk("c0_10k", 0.3), Sk("c0_10k", 0.62))
APP80 = ramp(list(range(FISH80.n)), Sk("c0_10k", 0.5), Sk("c0_10k", 0.92))
COND_ROWS = ["北海道の数字", "生まれた年は、実際の29年分からくじ"]
COND_Y = [100, 188, 276, 364, 452, 540]
T_COND = [T_C3 + 0.45 + 0.45 * k for k in range(6)]


def sc_c0_10k(ctx, t):
    # 卵は砂利の中、帰ってきた魚は海の中（魚が土の中に見えないように、魚が出る前に海へ替える）
    ts = Sk("c0_10k", 0.42)
    if t < ts + 0.5:
        bg_gravel(ctx, 300)
        BED10.draw(ctx, t, fade=VAN10, fd=0.7, hide=(YOU10,))
        x, y, _ph = BED10.pts[YOU10]
        you_egg(ctx, t, x, y, 44)
    grp(ctx, fade(t, ts, 0.5), bg_mouth)
    grp(ctx, out_fade(t, T_COND[0], 0.4), lambda c: FISH80.draw(c, t, appear=APP80, fd=0.3))
    card(ctx, t, Sk("c0_10k", 0.0) + 0.3, Sk("c0_10k", 0.0) + 3.1, [("1万粒", 64, YEL), ("（絵の1粒＝卵100粒）", 44, WHITE)], 70, 130, align="left", pad=(30, 12))
    card(ctx, t, T_CARD0, None, [("帰ってこられた（/1万粒）", 54, WHITE), ("中央値 約80匹", 96, YEL), ("網か川の捕獲場で、人が捕って数えたサケ", 40, WHITE)], 1400, 310, pad=(44, 20), border=YEL)
    card(ctx, t, T_CARD0 + 0.8, None, [("卵の生き残りを低く見ると、約20匹", 48, WHITE)], 1400, 560, pad=(30, 16))
    # 1万回の結果を小さい順に並べた帯
    tm = T_C3 + 0.2
    if t >= tm:
        a = fade(t, tm, 0.4)
        box(ctx, 80, 650, 1840, 895, PANEL, 0.96 * a, r=24)
        label(ctx, "くり返した結果を、小さい順に", 140, 688, 46, WHITE, a=a, align="left")
        n = 100
        for k in range(n):
            if t < tm + 0.2 + k * 0.012:
                continue
            c = mix("#bcd2ee", YOU, k / (n - 1))
            box(ctx, 140 + k * 16.4, 720, 140 + k * 16.4 + 15, 780, c, a, r=2)
        label(ctx, "小さい", 190, 835, 44, PALE, a=a)
        label(ctx, "大きい", 1750, 835, 44, PALE, a=a)
        tmk = Sk("c0_call", 0.0)
        if t >= tmk:
            ak = fade(t, tmk, 0.3)
            tri_down2(ctx, 960, 715, 20, YEL, ak)
            label(ctx, "真ん中の値＝中央値", 960, 835, 48, YEL, a=ak)
    for k, s_ in enumerate(COND_ROWS):
        if t >= T_COND[k]:
            panel(ctx, [(s_, 46, WHITE if k else YEL)], 100, COND_Y[k], align="left", a=fade(t, T_COND[k]))


# ============================================================
# 1 サケの一生（1枚の地図の上で進める）
# ============================================================
G_SHORT = [[("関門1", 48, YEL), ("生まれられるか", 44, WHITE)], [("関門2", 48, YEL), ("最初の冬を越えられるか", 44, WHITE)],
           [("関門3", 48, YEL), ("海から帰ってこられるか", 44, WHITE)], [("そのあと", 48, YEL), ("沿岸の網", 44, WHITE)]]
G_Y = [130, 300, 470, 640]
RIVER_HEAD = map_xy(143.0, 43.30)
MOUTH = map_xy(144.3, 44.05)


def sc_c1_map(ctx, t):
    t0, t_end = SC_START["c1_map"], SC_END["c1_map"]
    t_lab = ch_start(1) + CARD_HOLD[1] + 0.05
    tA, tB, tC = Sk("c1_haru", 0.0), Sk("c1_ocean", 0.0), Sk("c1_net", 0.0)
    winter = seg(t, Sk("c1_winter", 0.0), Sk("c1_winter", 0.0) + 1.6) * (1 - seg(t, tB, tB + 0.8))
    u = 0.0
    if t >= tA:
        if t < tB:
            u = lerp(0.0, U_OKH, ease(seg(t, tA + 0.1, tB - 0.2)))
        elif t < Sk("c1_4th", 0.0):
            u = lerp(U_OKH, U_LOOP1, ease(seg(t, tB, Sk("c1_4th", 0.0))))
        else:
            u = lerp(U_LOOP1, U_BACK, ease(seg(t, Sk("c1_4th", 0.0), tC + 0.6)))
    labs = ["北海道", "オホーツク海", "北の海"] + (["川", "河口"] if t >= t_lab else [])
    draw_map(ctx, t, u_trail=u, labels=labs, a_lab=fade(t, t0 + 0.3, 0.4) if t < t_lab else 1.0)
    if winter > 0.003:
        fill(ctx, hexrgb("#dfe8f3", 0.42 * winter))
        ctx.rectangle(0, 0, W_, H_)
        ctx.fill()
        snow(ctx, t, winter)
    # 親の魚が川に戻り、卵を産む（秋）
    ta0 = ch_start(1) + CARD_HOLD[1] + 0.1
    ua = ease(seg(t, ta0, Ek("c1_aki") - 0.1))
    if t < tA + 0.1:
        px, py = lerp(MOUTH[0], RIVER_HEAD[0], ua), lerp(MOUTH[1] + 20, RIVER_HEAD[1] - 20, ua)
        fish_dir(ctx, px, py, 90, FISHC, "adult", math.atan2(RIVER_HEAD[1] - MOUTH[1], RIVER_HEAD[0] - MOUTH[0]), t * 1.6, a=1 - fade(t, tA, 0.3))
    for k in range(9):
        tk = Ek("c1_aki") - 0.5 + 0.1 * k
        if t >= tk and t < tA + 0.4:
            draw_egg(ctx, RIVER_HEAD[0] - 50 + 25 * (k % 5) + 12 * (k // 5), RIVER_HEAD[1] + 12 + 22 * (k // 5), 11, EGGC, False, fade(t, tk, 0.3) * (1 - fade(t, tA + 0.1, 0.3)))
    if t >= tA:
        x, y, ang = map_pos(u)
        you_fish(ctx, t, x, y, 110, "fry" if u < U_OKH else "adult", ang=ang, glow_r=58)
    # 関門の札（左の列・出るたびに増える）
    ts = [tA + 0.1, Sk("c1_winter", 0.0), tB + 0.1, tC + 0.3]
    for k in range(3):
        lit = (t >= Sk("c1_four", 0.0))
        card(ctx, t, ts[k], None, G_SHORT[k], 70, G_Y[k], align="left", pad=(28, 14), border=YEL if lit else None)
    # 網（河口の前の海に白い線）


# ============================================================
# 2 運だけなら、あなたはどこまで行ける？
# ============================================================
def rising_fry(ctx, t, t0, n=14, you_k=6, you_L=210, hold=3.2):
    """砂利から稚魚が1匹ずつ水へ上がり、右へ川を下る（you_k 番目がオレンジのあなた）"""
    for k in range(n):
        tk = t0 + 0.2 + 0.18 * k
        if t < tk:
            continue
        x0, y0 = 150 + (110 * k) % 1500 + 40, 480 + (k * 53) % 360
        u = ease(seg(t, tk, tk + hold))
        x1, y1 = x0 + 800, 190 + (k * 37) % 90
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        ang = math.atan2(y1 - y0, x1 - x0)
        if k == you_k:
            you_fish(ctx, t, x, y, you_L, "fry", ang=ang, glow_r=you_L * 0.55)
        else:
            fish_dir(ctx, x, y, 120, FISHC, "fry", ang, t * 1.6 + k * 0.3)


def exits_at(n, keep, t_a, t_b, seed):
    """n 匹のうち keep を残して、ほかを t_a〜t_b に1匹ずつ泳ぎ去らせる時刻の表"""
    return ramp(shuffled(n, seed, keep=keep), t_a, t_b)


# ---- 問い1: 川で生まれた卵 ----
A_BED = Bed((50, 440, 1870, 910), 110, 26, seed=23, keepout=(960, 690, 170))


def sc_c2_a(ctx, t):
    bg_gravel(ctx, 330)
    A_BED.draw(ctx, t)
    you_egg(ctx, t, 960, 690, 115)
    card(ctx, t, Sk("c2_intro", 0.5), Sk("c2_yoso") - 0.2, [("川で生まれた卵", 56, YEL)], 150, 125, align="left", pad=(30, 12))
    card(ctx, t, Sk("c2_yoso", 0.0) + 0.3, None, [("あなたの予想", 46, PALE), ("いちばん危ないのは 海の旅", 62, YEL)], 960, 150, pad=(44, 16), border=YEL)


B_BED = Bed((60, 450, 1860, 910), 100, 30, seed=31)
B_YOU = min(range(B_BED.n), key=lambda i: math.hypot(B_BED.pts[i][0] - 960, B_BED.pts[i][1] - 700))
B_VAN = ramp(shuffled(B_BED.n, 8, keep=(B_YOU,))[:80], Sk("c2_chitose", 0.35), Sk("c2_chitose", 0.8))
FRY200 = Swarm((60, 450, 1860, 910), 200, 100, "fry", FISHC, seed=41, cols=25)
FRY133 = Swarm((60, 340, 1860, 900), 133, 112, "fry", FISHC, seed=43, cols=19)
T_FRY0 = Sk("c2_chitose", 0.85)


def sc_c2_b(ctx, t):
    if t < T_FRY0 + 0.5:
        bg_gravel(ctx, 330)
        gone = {i: T_FRY0 + 0.05 for i in range(B_BED.n) if i not in B_VAN and i != B_YOU}
        fd = dict(B_VAN)
        fd.update(gone)
        B_BED.draw(ctx, t, fade=fd, fd=0.6, hide=(B_YOU,))
        x, y, _ph = B_BED.pts[B_YOU]
        you_egg(ctx, t, x, y, 46)
    grp(ctx, fade(t, T_FRY0 - 0.1, 0.5), bg_mouth)      # 魚は水の中に置く（土の中に見えないように）
    app = ramp(list(range(FRY200.n)), T_FRY0, T_FRY0 + 0.9)
    FRY200.draw(ctx, t, appear=app, fd=0.4, cruise=0.0, hide=())
    card(ctx, t, Sk("c2_g1", 0.0) + 0.3, T_FRY0 - 0.15, [("1万粒", 56, YEL), ("絵の1粒＝卵100粒", 44, WHITE)], 70, 135, align="left", pad=(30, 12))
    card(ctx, t, T_FRY0 + 0.2, None, [("2,000匹 /1万粒", 58, YEL), ("絵の1匹＝10匹", 44, WHITE)], 70, 135, align="left", pad=(30, 12))
    card(ctx, t, Sk("c2_g1", 0.0) + 0.1, Sk("c2_def") - 0.3, [("関門1", 56, YEL), ("生まれられるか", 50, WHITE)], 1180, 150, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c2_def", 0.0) + 0.1, Sk("c2_chitose") - 0.3, [("ここでの「生まれる」は、", 46, WHITE), ("砂利を出て、川を下り始めること", 46, YEL)], 1180, 150, pad=(36, 14))
    card(ctx, t, Sk("c2_chitose", 0.0) + 0.1, None, [("千歳川の推定", 46, YEL), ("8,000粒/1万粒が、川を下り始める前に残れない", 44, WHITE), ("（残るのは5〜20%。この動画は20%で計算）", 44, PALE)], 1180, 165, pad=(36, 12))


# ---- あなた1粒に寄る（中央値のあなた・最悪のあなた）----
G_BED = Bed((40, 440, 1000, 912), 60, 26, seed=61, keepout=(480, 690, 250))


def sc_c2_c(ctx, t):
    tz = SC_START["c2_c"] + 0.25
    r = lerp(46, 190, ease(seg(t, tz, tz + 1.6)))
    al = 1 - 0.65 * ease(seg(t, Sk("c2_medyou", 0.15), Ek("c2_medyou")))
    bg_gravel(ctx, 330)
    G_BED.draw(ctx, t, a=0.8)
    you_egg(ctx, t, 480, 700, r, a=al)
    t7 = Sk("c2_worstyou", 0.0)
    card(ctx, t, Sk("c2_medyou", 0.0) + 0.1, t7 - 0.15, [("ちょうど真ん中の1粒", 56, YEL)], 1390, 150, pad=(40, 14), border=YEL)
    card(ctx, t, t7 + 0.1, None, [("いちばん運の悪い1粒", 52, YEL)], 1390, 150, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c2_medyou", 0.0) + 0.3, Sk("c2_nb") - 0.15, [("生き残り5〜20%のどれでも、", 44, WHITE), ("真ん中の1粒は関門1で終わる", 44, YEL)], 1390, 355, pad=(30, 14))
    card(ctx, t, Sk("c2_nb", 0.0) + 0.1, None, [("あなたは、たぶん、", 66, WHITE), ("生まれることもできません。", 66, YEL)], 1390, 355, pad=(40, 20), border=YEL)
    card(ctx, t, Sk("c2_nb", 0.25), None, [("ここでの「生まれる」は、", 44, WHITE), ("砂利を出て、川を下り始めること", 44, WHITE)], 1390, 585, pad=(30, 14))
    card(ctx, t, Sk("c2_nb", 0.55), None, [("ここで終わる数（/1万粒）", 44, WHITE), ("関門1で 8,000粒", 66, YEL)], 1390, 775, pad=(34, 14))


# ---- 関門2・関門3 ----
def sc_c2_d(ctx, t):
    bg_mouth(ctx)
    t0c = SC_START["c2_d"]
    winter_sky(ctx, seg(t, t0c + 0.3, t0c + 3.0))
    snow(ctx, t, seg(t, t0c + 0.8, t0c + 3.0))
    ex = exits_at(FRY200.n, set(range(13)), Sk("c2_9", 0.1), Sk("c2_9", 0.5), 51)
    t_new = Sk("c2_9", 0.62)
    FRY200.draw(ctx, t, ex=ex, vx=900.0, cruise=60.0, ct0=t0c, a=1 - clamp01((t - t_new) / 0.4))
    app = ramp(list(range(FRY133.n)), t_new, t_new + 0.5)
    FRY133.draw(ctx, t, appear=app, fd=0.4, cruise=20.0, ct0=t_new)
    card(ctx, t, t0c + 0.4, t_new - 0.15, [("絵の1匹＝10匹", 48, WHITE)], 70, 150, align="left", pad=(28, 12))
    card(ctx, t, t_new + 0.2, None, [("絵の1匹＝1匹", 48, WHITE)], 70, 150, align="left", pad=(28, 12))
    card(ctx, t, Sk("c2_g2", 0.0) + 0.2, Sk("c2_9") + 0.1, [("関門2", 56, YEL), ("最初の冬を越えられるか", 50, WHITE)], 800, 150, pad=(36, 14), border=YEL)
    card(ctx, t, Sk("c2_9", 0.0) + 0.2, None, [("どう見ても9割以上がいなくなる", 44, YEL)], 1500, 150, pad=(30, 12))
    card(ctx, t, Sk("c2_9", 0.72), None, [("最初の冬を越えた稚魚（/1万粒）", 46, WHITE), ("133匹", 96, YEL)], 1250, 330, pad=(40, 14), border=YEL)


SEA133 = Swarm((60, 330, 1860, 880), 133, 100, "adult", FISHC, seed=47, cols=19)


def sc_c2_e(ctx, t):
    bg_sea(ctx)
    t0 = SC_START["c2_e"]
    ex = exits_at(SEA133.n, set(range(80)), Sk("c2_calc", 0.55), Sk("c2_calc", 0.72), 53)
    SEA133.draw(ctx, t, ex=ex, vx=900.0, cruise=40.0, ct0=t0)
    card(ctx, t, Sk("c2_g3", 0.0) + 0.1, Sk("c2_calc", 0.45) - 0.1, [("関門3", 56, YEL), ("海から帰ってこられるか", 50, WHITE)], 960, 150, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c2_calc", 0.47), None, [("資料の推定値からの計算", 48, WHITE), ("（5〜7割）", 56, YEL)], 960, 150, pad=(40, 14))
    card(ctx, t, t0 + 0.4, None, [("絵の1匹＝1匹", 48, WHITE)], 70, 150, align="left", pad=(28, 12))


# ---- 1万回の結果の山（帰ってこられた数）----
BIN_R = np.bincount(BACK_R // 10).tolist()
PX0, PX1, PY0 = 150, 1770, 850
PVMAX = 180


def _pile_frame(ctx, t, title, vmax, ticks, a=1.0):
    label(ctx, title, 90, 62, 46, WHITE, a=a, align="left")
    line2(ctx, (PX0 - 10, PY0 + 2), (PX1 + 10, PY0 + 2), WHITE, 5, a)
    for v in ticks:
        x = pile_x(v, 0, vmax, PX0, PX1)
        line2(ctx, (x, PY0 + 2), (x, PY0 + 16), WHITE, 4, a)
        label(ctx, str(v), x, PY0 + 48, 42, PALE, a=a)
    label(ctx, "匹", PX1 + 50, PY0 + 48, 42, PALE, a=a)


def sc_c2_f(ctx, t):
    flat(ctx)
    _pile_frame(ctx, t, "1万回のうち、何回か（1マス＝100回）", PVMAX, (0, 50, 100, 150))
    t0 = Sk("c2_med82", 0.0) + 0.2
    xm = pile_x(82, 0, PVMAX, PX0, PX1)
    xa, xb = pile_x(34, 0, PVMAX, PX0, PX1), pile_x(116, 0, PVMAX, PX0, PX1)
    tb = Sk("c2_med82", 0.8)
    if t >= tb:
        ab = fade(t, tb, 0.4)
        fill(ctx, hexrgb("#ffffff", 0.10 * ab))
        ctx.rectangle(xa, 350, xb - xa, PY0 - 350)
        ctx.fill()
        line2(ctx, (xa, 348), (xb, 348), YEL, 8, ab)
        line2(ctx, (xa, 336), (xa, 360), YEL, 8, ab)
        line2(ctx, (xb, 336), (xb, 360), YEL, 8, ab)
        panel(ctx, [("34〜116匹", 56, YEL), ("（1万回のうち8割）", 44, WHITE)], 1520, 360, a=ab, pad=(36, 12))
    pile(ctx, t, BIN_R, 10, PVMAX, PX0, PX1, PY0, t0, 0.28, hi_bin=82 // 10, t_hi=Sk("c2_med82", 0.55))
    tm = Sk("c2_med82", 0.55)
    if t >= tm:
        am = fade(t, tm, 0.3)
        line2(ctx, (xm, 330), (xm, PY0), YEL, 4, am * 0.8, dash=[10, 8])
        panel(ctx, [("帰ってこられた数の 中央値（/1万粒）", 44, WHITE), ("82匹", 110, YEL)], xm, 215, a=am, border=YEL, pad=(40, 14))
    tw = Sk("c2_worst", 0.0) + 0.1
    if t >= tw:
        a = fade(t, tw)
        x = pile_x(10, 0, PVMAX, PX0, PX1)
        panel(ctx, [("最少 10匹", 50, YEL)], x + 60, 690, a=a)
        tri_down2(ctx, x + 40, 782, 16, YEL, a)
    tb2 = Sk("c2_best", 0.0) + 0.1
    if t >= tb2:
        a = fade(t, tb2)
        x = pile_x(177, 0, PVMAX, PX0, PX1)
        panel(ctx, [("最多 177匹", 50, YEL)], x - 100, 770, a=a)
        tri_down2(ctx, x - 12, 842, 16, YEL, a)


# ---- いちばん良かった場合のあなた ----
H_BED = Bed((50, 480, 1870, 915), 110, 25, seed=71, keepout=(700, 700, 160))
H1_SCHOOL = Swarm((60, 330, 1500, 880), 16, 120, "fry", FISHC, seed=73, keepout=(900, 600, 200))


def _h1_gravel(ctx, t):
    bg_gravel(ctx, 330)
    H_BED.draw(ctx, t, sway=2.0)
    t2 = Sk("c2_spring", 0.0)
    if t < t2:
        pulse = 1.0 + 1.2 * max(0.0, math.sin((t - Sk("c2_bestyou", 0.3)) * 6.0))
        you_egg(ctx, t, 700, 700, 120, pulse=pulse)
    else:
        a = 1 - clamp01((t - t2) / 0.4)
        if a > 0.02:
            you_egg(ctx, t, 700, 700, 120, a=a)
        rising_fry(ctx, t, t2 - 0.1, you_k=5, you_L=230)


def _h1_mouth(ctx, t):
    bg_mouth(ctx)
    t0 = Sk("c2_spring", 0.55)
    H1_SCHOOL.draw(ctx, t, cruise=140.0, ct0=t0)
    you_fish(ctx, t, lerp(-200, 1100, ease(seg(t, t0, Ek("c2_spring")))), 620 + 8 * math.sin(t * 1.5), 260, "fry", ang=0.0, glow_r=150)


def sc_c2_h1(ctx, t):
    t0 = Sk("c2_spring", 0.55)
    layers(ctx, t, [(0.0, t0, _h1_gravel), (t0, 1e9, _h1_mouth)], xf=0.35)
    card(ctx, t, Sk("c2_bestyou", 0.0) + 0.1, None, [("いちばん運の良かった1粒", 50, YEL)], 960, 150, pad=(34, 14), border=YEL)


H2_SCHOOL = Swarm((60, 330, 1860, 880), 30, 110, "fry", FISHC, seed=81, keepout=(900, 620, 190))


def sc_c2_h2(ctx, t):
    bg_mouth(ctx)
    t_w = Sk("c2_win", 0.0)
    winter_sky(ctx, seg(t, t_w, t_w + 1.6))
    snow(ctx, t, seg(t, t_w + 0.3, t_w + 1.6))
    ex = exits_at(H2_SCHOOL.n, set(range(5)), Sk("c2_win", 0.35), Sk("c2_win", 0.6), 83)
    H2_SCHOOL.draw(ctx, t, ex=ex, vx=900.0, cruise=40.0, ct0=SC_START["c2_h2"])
    you_fish(ctx, t, 900, 620 + 8 * math.sin(t * 1.5), 260, "fry", ang=0.0, glow_r=150)
    card(ctx, t, t_w + 0.1, None, [("最初の冬", 56, WHITE)], 190, 125, pad=(30, 12))


ORB_C, ORB_R = map_xy(166.0, 49.5), 190


def _orbit(th):
    return ORB_C[0] + ORB_R * math.cos(th), ORB_C[1] + ORB_R * 1.05 * math.sin(th), th + math.pi / 2


def sc_c2_h3(ctx, t):
    t0 = SC_START["c2_h3"]
    draw_map(ctx, t, labels=["北海道", "オホーツク海", "北の海"])
    th = -1.2 + (t - t0) * 0.55
    for k in range(5):
        x, y, ang = _orbit(th - 0.28 * (k + 1))
        fish_dir(ctx, x, y, 96, FISHC, "adult", ang, t * 1.6 + k * 0.4)
    x, y, ang = _orbit(th)
    you_fish(ctx, t, x, y, 124, "adult", ang=ang, glow_r=66)


def sc_c2_h4(ctx, t):
    bg_mouth(ctx)
    t0 = Sk("c2_home", 0.0)
    u = ease(seg(t, SC_START["c2_h4"] + 0.2, t0 + Dk("c2_home") * 0.9))
    you_fish(ctx, t, lerp(2000, 820, u), 620 + 10 * math.sin(t * 1.4), 430, "adult", ang=math.pi, glow_r=230)
    card(ctx, t, t0 + 0.9, None, [("帰ってこられた", 52, WHITE), ("1万粒のうち 約80匹", 66, YEL)], 960, 165, pad=(40, 14), border=YEL)


# ---- 網 ----
NET2 = (1180, 480, 1660, 880)
NET2_SCHOOL = Swarm((60, 500, 1060, 880), 8, 200, "adult", FISHC, seed=91, keepout=(560, 700, 230))


def _river_strip(ctx):
    """右に陸、その中を川が河口へ流れる（柱に見えないように）"""
    fill(ctx, hexrgb("#7fb56a"))
    ctx.rectangle(1690, 0, 230, 1080)
    ctx.fill()
    fill(ctx, hexrgb("#7fc3e6"))
    ctx.move_to(1730, 0)
    ctx.line_to(1880, 0)
    ctx.line_to(1880, 900)
    ctx.curve_to(1860, 950, 1760, 960, 1690, 965)
    ctx.line_to(1690, 840)
    ctx.curve_to(1715, 830, 1730, 810, 1730, 780)
    ctx.close_path()
    ctx.fill()
    label(ctx, "川", 1805, 100, 56, WHITE)


def _path_pos(pts, u):
    ls = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    d = clamp01(u) * sum(ls)
    for i, l_ in enumerate(ls):
        if d <= l_ or i == len(ls) - 1:
            f = clamp01(d / max(1e-6, l_))
            x, y = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
            return x, y, math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
        d -= l_
    return pts[-1][0], pts[-1][1], 0.0


def net_scene(ctx, t, t_net, you_col=None, school=True, up=(), up_col=FISHC, up_a=0.5, up_L=150, you_x=560):
    """海と網（白い線）と川。up=(出発の時刻, …) の魚が、網の下をくぐって川を上る"""
    bg_sea(ctx)
    _river_strip(ctx)
    if t >= t_net:
        set_net(ctx, *NET2, a=fade(t, t_net, 0.5), cell=60)
    if school:
        NET2_SCHOOL.draw(ctx, t)
    if you_col:
        you_fish(ctx, t, you_x, 700, 360, "adult", ang=0.0, glow_r=190)
    for k, tk in enumerate(up):
        u = seg(t, tk, tk + 3.0)
        if u <= 0:
            continue
        path = [(880, 560 + 14 * k), (1100, 910 + 14 * k), (1700, 905), (1795, 800), (1795, 300)]
        x, y, ang = _path_pos(path, u)
        col = up_col[k] if isinstance(up_col, (list, tuple)) else up_col
        fish_dir(ctx, x, y, up_L, col, "adult", ang, t * 1.6 + k, a=up_a)


def _badge(ctx, x, y, s_, a=1.0):
    fill(ctx, hexrgb(PANEL, a))
    ctx.arc(x, y, 36, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(YEL, a))
    ctx.set_line_width(4)
    ctx.arc(x, y, 36, 0, 2 * math.pi)
    ctx.stroke()
    label(ctx, s_, x, y, 48, YEL, a=a)


def three_ways(ctx, t):
    """海から帰ってきたサケの行き先は3つ（2026-11-06 ユーザー「網のところがわからない」）。①沿岸の網 ②川の捕獲場 ③捕まらずに川を上る"""
    tn, t1, t2, t3, tg = Sk("c2_netis", 0.0) + 0.4, Sk("c2_85", 0.0), Sk("c2_trap", 0.0), Sk("c2_third", 0.0), Sk("c2_gap", 0.0)
    tu = Sk("c2_upyou", 0.0)
    bg_sea(ctx)
    _river_strip(ctx)
    if t >= tn:
        set_net(ctx, *NET2, a=fade(t, tn, 0.5), cell=60)
    if t >= t2:          # 川の捕獲場の柵
        a = fade(t, t2, 0.4)
        box(ctx, 1730, 612, 1880, 630, "#f4f4f4", a, r=4)
        for k in range(6):
            box(ctx, 1742 + k * 26, 590, 1750 + k * 26, 652, "#f4f4f4", a, r=3)
    NET2_SCHOOL.draw(ctx, t)
    if t < tu:
        you_fish(ctx, t, 560, 700, 360, "adult", ang=0.0, glow_r=190)
    else:                # 網の下をくぐって、あなたが川へ上る
        xu, yu, ang_u = _path_pos([(560, 700), (1100, 910), (1700, 905), (1795, 800), (1795, 300)], seg(t, tu, tu + 3.2))
        fish_dir(ctx, xu, yu, 220, YOU, "adult", ang_u, t * 1.6, a=1.0)
    for k in range(6):   # ① 網に入る
        tk = t1 + 0.3 + 0.35 * k
        u = seg(t, tk, tk + 1.5)
        if u > 0:
            x, y, ang = _path_pos([(1000, 540 + 55 * k), (1280 + 130 * (k % 3), 570 + 130 * (k // 3))], u)
            fish_dir(ctx, x + (6 * math.sin(t * 1.4 + k) if u >= 1 else 0), y, 120, FISHC, "adult", ang if u < 1 else 0.0, t * 1.6 + k)
    for k in range(2):   # ② 川の捕獲場で止まる
        tk = t2 + 0.3 + 0.7 * k
        u = seg(t, tk, tk + 3.0)
        if u > 0:
            x, y, ang = _path_pos([(900, 800), (1100, 915 + 12 * k), (1700, 905), (1775 + 40 * k, 800), (1775 + 40 * k, 690)], u)
            fish_dir(ctx, x, y, 110, FISHC, "adult", ang, t * 1.6 + k)
    for k in range(12):  # ③ 捕まらずに川を上る（うすい魚が1匹ずつ）
        tk = t3 + 0.2 + 2.2 * k
        u = seg(t, tk, tk + 4.0)
        if 0 < u < 1:
            x, y, ang = _path_pos([(880, 560), (1100, 915), (1700, 905), (1805, 800), (1805, -60)], u)
            fish_dir(ctx, x, y, 110, FISHC, "adult", ang, t * 1.6 + k, a=0.5)
    if t >= t1:
        _badge(ctx, 1420, 462, "①", fade(t, t1, 0.3))
    if t >= t2:
        _badge(ctx, 1805, 540, "②", fade(t, t2, 0.3))
    if t >= t3:
        _badge(ctx, 1805, 210, "③", fade(t, t3, 0.3))
    # 左上の一覧
    tag(ctx, t, t1, None, "① 沿岸の網", 70, 140, size=54, align="left", pad=(24, 10))
    tag(ctx, t, t1 + 0.4, None, "人が数えた", 720, 140, size=48, col=YEL, align="left", pad=(24, 12))
    tag(ctx, t, t2, None, "② 川の捕獲場", 70, 255, size=54, align="left", pad=(24, 10))
    tag(ctx, t, t2 + 0.4, None, "人が数えた", 720, 255, size=48, col=YEL, align="left", pad=(24, 12))
    tag(ctx, t, t3, None, "③ 川を上って卵を産む", 70, 370, size=54, align="left", pad=(24, 10))
    tag(ctx, t, tg + 0.1, None, "誰も数えていない", 720, 370, size=48, col="#ff8c8c", align="left", pad=(24, 12))
    # 右上の数
    ts, tm, t70, t10 = Sk("c2_sum", 0.0), Sk("c2_more", 0.0), Sk("c2_70", 0.0), Sk("c2_10", 0.0)
    card(ctx, t, ts + 0.1, t70 - 0.3, [("① ＋ ② ＝ 82匹", 62, YEL), ("/1万粒", 40, WHITE)], 1400, 110, pad=(30, 10), border=YEL)
    card(ctx, t, tm + 0.1, t70 - 0.3, [("本当に帰ってきたサケは", 42, WHITE), ("82匹より多いはず", 54, YEL)], 1400, 300, pad=(26, 10))
    card(ctx, t, t70 + 0.1, None, [("① 沿岸の網", 42, WHITE), ("70匹あまり", 60, YEL)], 1400, 110, pad=(30, 10))
    card(ctx, t, t10 + 0.1, None, [("② 川の捕獲場（/1万粒）", 40, WHITE), ("中央値 10匹", 60, YEL)], 1400, 300, pad=(26, 10), border=YEL)


def sc_c2_i1(ctx, t):
    three_ways(ctx, t)


def sc_c2_i2(ctx, t):
    three_ways(ctx, t)


def _fillet(ctx, x, y, w, h):
    fill(ctx, hexrgb("#f08e6a"))
    rrect(ctx, x - w / 2, y - h / 2, w, h, h * 0.5)
    ctx.fill()
    fill(ctx, hexrgb("#f7b49a"))
    for k in range(4):
        rrect(ctx, x - w * 0.34 + k * w * 0.17, y - h * 0.33, w * 0.035, h * 0.66, 6)
        ctx.fill()


def sc_c2_i3(ctx, t):
    flat(ctx, "#2a2f45")
    fill(ctx, hexrgb("#8a5a2e"))
    ctx.rectangle(0, 560, W_, 400)
    ctx.fill()
    fill(ctx, hexrgb("#a06c3a"))
    ctx.rectangle(0, 560, W_, 30)
    ctx.fill()
    a = fade(t, SC_START["c2_i3"] + 0.3, 0.6)
    for (yy, rx, col, al) in ((770, 360, "#000000", 0.18), (740, 350, "#ffffff", 1.0), (740, 270, "#ece7df", 1.0)):
        fill(ctx, hexrgb(col, al * a))
        ctx.save()
        ctx.translate(960, yy)
        ctx.scale(1.0, 0.27)
        ctx.arc(0, 0, rx, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if a > 0.02:
        ctx.push_group()
        _fillet(ctx, 960, 715, 330, 120)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    for k in range(3):                       # ゆげ
        yy = 560 - ((t * 40 + k * 60) % 180)
        fill(ctx, hexrgb("#ffffff", 0.25 * a * (1 - (560 - yy) / 200)))
        ctx.arc(900 + 60 * k + 10 * math.sin(t * 2 + k), yy, 18, 0, 2 * math.pi)
        ctx.fill()


# ---- 1粒の終点（4つの関門の棒）----
BAR_ROWS = [("関門1 生まれられるか", 80.0, "8,000粒"), ("関門2 最初の冬を越えられるか", 18.72, "約1,870匹"), ("関門3 北の海の旅", 0.48, "約50匹"), ("帰ってくる", 0.791, "約80匹")]
BAR_Y = [215, 345, 475, 605]
BX0, BX1 = 780, 1640


def sc_c2_j(ctx, t):
    flat(ctx)
    label(ctx, "どこで終わるか（/1万粒）", 90, 90, 46, WHITE, align="left")
    fish(ctx, 200 + ((t * 70) % 1500), 690, 190, FISHC, "adult", t * 1.6, 1)   # 棒だけで長く止まらないように
    for k, (nm, v, vt) in enumerate(BAR_ROWS):
        y = BAR_Y[k]
        label(ctx, nm, 90, y, 44, WHITE, align="left")
        box(ctx, BX0, y - 30, BX1, y + 30, "#22436f", r=6)
    tks = [Sk("c2_b1", 0.2), Sk("c2_b2", 0.2), Sk("c2_b3", 0.1), Sk("c2_b3", 0.1) + 0.3]
    tvs = [Sk("c2_b1", 0.65), Sk("c2_b2", 0.7), Sk("c2_b3", 0.5), Sk("c2_b3", 0.5) + 0.3]
    for k, (nm, v, vt) in enumerate(BAR_ROWS):
        if t < tks[k]:
            continue
        y = BAR_Y[k]
        u = ease(seg(t, tks[k], tks[k] + 0.7))
        w = max(5.0, (BX1 - BX0) * v / 100.0) * u
        box(ctx, BX0, y - 30, BX0 + w, y + 30, YOU if k < 2 else "#7fb0e6", r=6)
        if t >= tvs[k]:
            label(ctx, vt, BX0 + max(5.0, (BX1 - BX0) * v / 100.0) + 20, y, 54, YEL, a=fade(t, tvs[k], 0.3), align="left")
    tb3 = Sk("c2_b3", 0.0)
    if tb3 <= t < Sk("c2_hon"):
        ctx.set_source_rgba(*hexrgb(YEL, 0.9 * fade(t, tb3, 0.4)))
        ctx.set_line_width(5)
        rrect(ctx, 70, BAR_Y[2] - 52, 1780, 104, 14)
        ctx.stroke()
    th = Sk("c2_hon", 0.0) + 0.1
    if t >= th:
        a = fade(t, th, 0.4)
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.set_line_width(8)
        rrect(ctx, 70, BAR_Y[0] - 56, 1780, BAR_Y[1] - BAR_Y[0] + 112, 18)
        ctx.stroke()
        panel(ctx, [("いちばん減るのは、最初の冬まで", 64, YEL)], 960, 800, a=a, border=YEL, pad=(50, 18))


def sc_c2_ans(ctx, t):
    tc = T("c2_ans", 0.1)
    label(ctx, "答え", 960, 95, 72, YEL)
    panel(ctx, [("ふつうの運なら、あなたはたぶん", 52, WHITE), ("砂利の中で終わる", 80, YEL), ("いちばん減るのは、海の旅ではなく", 48, WHITE), ("最初の冬まで", 72, YEL)], 960, 390, a=fade(t, tc), border=YEL, pad=(60, 26))
    you_egg(ctx, t, 960, 790, 105, a=fade(t, bd("c2_ans") + 0.5))


# ============================================================
# 3 川か放流か、生まれ方で変わる？
# ============================================================
ROOM = "#2c4a6b"
YOU_EGG_R, YOU_ADULT_L, YOU_FRY_L = 190, 840, 640       # 画面の高さの3分の1（360px）以上になる大きさ（魚は ひれまで入れた高さ）


def tank(ctx, x0, y0, x1, y1, a=1.0, glow_a=0.0):
    """ふ化場の水槽（ガラスの枠・水・光）"""
    box(ctx, x0 - 14, y0 - 14, x1 + 14, y1 + 14, "#9fb3cc", a, r=24)
    box(ctx, x0, y0, x1, y1, "#4f9fd2", a, r=14)
    box(ctx, x0, y0, x1, y0 + (y1 - y0) * 0.14, "#6fb5df", a, r=14)
    fill(ctx, hexrgb("#ffffff", 0.16 * a))
    ctx.rectangle(x0 + 18, y0 + 18, 20, (y1 - y0) - 60)
    ctx.fill()
    if glow_a > 0.003:
        ctx.set_source_rgba(*hexrgb("#ffe14a", glow_a * a))
        ctx.set_line_width(10)
        rrect(ctx, x0 - 20, y0 - 20, x1 - x0 + 40, y1 - y0 + 40, 28)
        ctx.stroke()


TANK_BED_A = Bed((240, 380, 960, 790), 36, 22, seed=101)
TANK_FRY_A = Swarm((240, 380, 960, 790), 14, 90, "fry", FISHC, seed=103)


def sc_c3_a(ctx, t):
    flat(ctx, ROOM)
    # 右: 川
    box(ctx, 1500, 380, 1920, 860, "#3e8fc4", r=0)
    fill(ctx, hexrgb("#ffffff", 0.3))
    for k in range(3):
        ctx.rectangle(1560 + 80 * k, 470 + 90 * k, 70, 6)
        ctx.fill()
    box(ctx, 1000, 560, 1560, 640, "#8a9bb0", r=6)
    box(ctx, 1000, 560, 1560, 575, "#aab8ca", r=6)
    tank(ctx, 200, 330, 1000, 830)
    th = Sk("c3_hatch", 0.45)
    TANK_BED_A.draw(ctx, t, fade={i: th + 0.04 * i for i in range(TANK_BED_A.n)}, fd=0.5)
    app = {i: th + 0.04 * i for i in range(TANK_FRY_A.n)}
    # 稚魚が1匹ずつ、管を通って川へ（放流）
    for i in range(TANK_FRY_A.n):
        tk = th + 0.7 + 0.35 * i
        x, y = TANK_FRY_A.pos(i, t)
        al = clamp01((t - app[i]) / 0.4)
        if t >= tk:
            u = seg(t, tk, tk + 3.4)
            x, y, ang = _path_pos([(x, y), (1020, 600), (1560, 600), (1900, 640)], u)
            fish_dir(ctx, x, y, 90, FISHC, "fry", ang, t * 1.6 + i * 0.3)
        elif al > 0.02:
            fish(ctx, x, y, 90, FISHC, "fry", t * 1.6 + i * 0.3, 1, al)
    card(ctx, t, Sk("c3_hatch", 0.0) + 0.1, None, [("ふ化場", 56, YEL)], 600, 282, pad=(36, 12))
    card(ctx, t, th + 1.2, None, [("放流", 56, YEL)], 1700, 300, pad=(36, 12))
    card(ctx, t, Sk("c3_yoso", 0.0) + 0.3, None, [("あなたの予想", 46, PALE), ("ふ化場なら ほとんど帰ってくる", 58, YEL)], 960, 140, pad=(44, 16), border=YEL)


TANK_B = (120, 400, 1020, 900)
TANK_EGGS = Bed((150, 430, 990, 870), 100, 22, seed=111, cols=14)
TANK_YOU = min(range(TANK_EGGS.n), key=lambda i: math.hypot(TANK_EGGS.pts[i][0] - 570, TANK_EGGS.pts[i][1] - 650))


def sc_c3_b(ctx, t):
    flat(ctx, ROOM)
    gate_row(ctx, t, y=165, h=200, lit=0)
    tg = Sk("c3_tank", 0.0)
    tank(ctx, *TANK_B, glow_a=0.6 * fade(t, tg, 0.5))
    TANK_EGGS.draw(ctx, t, hide=(TANK_YOU,), sway=7.0)
    x, y, _ph = TANK_EGGS.pts[TANK_YOU]
    you_egg(ctx, t, x, y, 36)
    card(ctx, t, Sk("c3_875", 0.0) + 0.2, None, [("ふ化場", 50, YEL), ("8,750粒", 96, YEL), ("/1万粒（死亡率 約10〜15%）", 44, WHITE)], 1455, 560, pad=(36, 14), border=YEL)
    card(ctx, t, Sk("c3_chit", 0.0) + 0.1, Sk("c3_other") - 0.4, [("千歳川", 46, YEL), ("2006〜2011年級で同程度", 44, WHITE)], 1455, 790, pad=(34, 14))
    card(ctx, t, Sk("c3_other", 0.0) + 0.1, None, [("ほかの川は分からない", 46, WHITE), ("だから 同じと仮定", 52, YEL)], 1455, 790, pad=(34, 14))


TANK_C = (110, 380, 690, 860)
TANK_C_EGGS = Bed((130, 400, 670, 840), 100, 17, seed=113, cols=10)
TC_YOU = min(range(TANK_C_EGGS.n), key=lambda i: math.hypot(TANK_C_EGGS.pts[i][0] - 400, TANK_C_EGGS.pts[i][1] - 620))
HATCH88 = Swarm((780, 400, 1860, 880), 88, 80, "fry", FISHC, seed=117, cols=11)
T_H88 = Sk("c3_4x", 0.15)


def sc_c3_c(ctx, t):
    flat(ctx, ROOM)
    box(ctx, 700, 600, 780, 660, "#8a9bb0", r=4)
    tank(ctx, *TANK_C)
    van = {i: T_H88 + 0.03 * k for k, i in enumerate(shuffled(TANK_C_EGGS.n, 7, keep=(TC_YOU,))[:12])}
    gone = {i: T_H88 + 0.15 for i in range(TANK_C_EGGS.n) if i not in van and i != TC_YOU}
    fd = dict(van)
    fd.update(gone)
    TANK_C_EGGS.draw(ctx, t, fade=fd, fd=0.6, hide=(TC_YOU,), sway=2.0)
    x, y, _ph = TANK_C_EGGS.pts[TC_YOU]
    you_egg(ctx, t, x, y, 30, a=1 - 0.0)
    # 稚魚が管から出て右の川（群れ）へ
    for i in range(HATCH88.n):
        tk = T_H88 + 0.15 + 0.012 * i
        if t < tk:
            continue
        u = ease(seg(t, tk, tk + 1.3))
        x1, y1 = HATCH88.pos(i, t)
        xx, yy = lerp(740, x1, u), lerp(630, y1, u)
        fish(ctx, xx, yy, 80 * HATCH88.dep[i], FISHC, "fry", t * 1.6 + HATCH88.pts[i][2], 1, clamp01((t - tk) / 0.2))
    tt = Sk("c3_move", 0.0) + 0.2
    card(ctx, t, tt, T_H88, [("ふ化場の卵", 44, WHITE), ("1万粒", 64, YEL)], 400, 270, pad=(34, 12))
    card(ctx, t, tt, T_H88, [("絵の1粒＝卵100粒", 44, WHITE)], 70, 130, align="left", pad=(26, 10))
    card(ctx, t, T_H88 + 0.3, None, [("絵の1匹＝100匹", 44, WHITE)], 70, 130, align="left", pad=(26, 10))
    card(ctx, t, Sk("c3_4x", 0.55), None, [("川を下り始めた稚魚（/1万粒）", 46, WHITE), ("8,751匹", 96, YEL), ("（川生まれは2,000匹）", 44, PALE)], 1320, 240, pad=(36, 14), border=YEL)


DEF_H88 = Swarm((200, 400, 1860, 880), 88, 90, "fry", FISHC, seed=119, cols=12)
RIV13 = Swarm((80, 440, 720, 880), 13, 100, "fry", FISHC, seed=121, cols=4)
HAT59 = Swarm((860, 440, 1840, 880), 59, 100, "fry", FISHC, seed=123, cols=10)


def sc_c3_d(ctx, t):
    bg_mouth(ctx)
    t_589 = Sk("c3_589", 0.0)
    ex = exits_at(DEF_H88.n, set(range(6)), t_589 + 0.1, t_589 + 0.55, 131)
    t_cmp = Sk("c3_more", 0.0) - 0.1
    DEF_H88.draw(ctx, t, ex=ex, vx=900.0, cruise=30.0, ct0=SC_START["c3_d"], a=1 - clamp01((t - t_cmp) / 0.4))
    RIV13.draw(ctx, t, appear=ramp(list(range(RIV13.n)), t_cmp, t_cmp + 0.4), fd=0.4)
    HAT59.draw(ctx, t, appear=ramp(list(range(HAT59.n)), t_cmp, t_cmp + 0.5), fd=0.4)
    card(ctx, t, SC_START["c3_d"] + 0.3, t_cmp - 0.15, [("絵の1匹＝100匹", 44, WHITE)], 70, 130, align="left", pad=(26, 10))
    card(ctx, t, t_cmp + 0.2, None, [("絵の1匹＝10匹", 44, WHITE)], 70, 130, align="left", pad=(26, 10))
    card(ctx, t, Sk("c3_589", 0.55), Sk("c3_9") - 0.1, [("最初の冬を越えた稚魚（/1万粒）", 46, WHITE), ("589匹", 96, YEL)], 1450, 190, pad=(36, 14), border=YEL)
    tl_ = Sk("c3_more", 0.15)
    card(ctx, t, tl_, None, [("川生まれ 133匹", 50, WHITE)], 400, 360, pad=(30, 12))
    card(ctx, t, tl_ + 0.3, None, [("ふ化場 589匹", 50, YEL)], 1350, 360, pad=(30, 12))
    card(ctx, t, Sk("c3_9", 0.0) + 0.1, None, [("ふ化場でも", 46, WHITE), ("関門2で9割以上がいなくなる", 52, YEL)], 960, 190, pad=(36, 14))


BIN_H = np.bincount(BACK_H // 50).tolist()
HVMAX = 700


def sc_c3_e(ctx, t):
    flat(ctx)
    _pile_frame(ctx, t, "ふ化場: 1万回のうち、何回か（1マス＝200回）", HVMAX, (0, 200, 400, 600))
    t0 = Sk("c3_364", 0.0) + 0.2
    xm = pile_x(364, 0, HVMAX, PX0, PX1)
    xa, xb = pile_x(153, 0, HVMAX, PX0, PX1), pile_x(504, 0, HVMAX, PX0, PX1)
    pile(ctx, t, BIN_H, 50, HVMAX, PX0, PX1, PY0, t0, 0.28, unit=200, th=36, hi_bin=364 // 50, t_hi=Sk("c3_364", 0.55))
    tm = Sk("c3_364", 0.55)
    if t >= tm:
        am = fade(t, tm, 0.3)
        line2(ctx, (xm, 330), (xm, PY0), YEL, 4, am * 0.8, dash=[10, 8])
        panel(ctx, [("帰ってこられた数の 中央値（/1万粒）", 44, WHITE), ("364匹", 110, YEL)], xm, 215, a=am, border=YEL, pad=(40, 14))
    tb = Sk("c3_364", 0.8)
    if t >= tb:
        ab = fade(t, tb, 0.4)
        fill(ctx, hexrgb("#ffffff", 0.10 * ab))
        ctx.rectangle(xa, 372, xb - xa, PY0 - 372)
        ctx.fill()
        line2(ctx, (xa, 370), (xb, 370), YEL, 8, ab)
        line2(ctx, (xa, 358), (xa, 382), YEL, 8, ab)
        line2(ctx, (xb, 358), (xb, 382), YEL, 8, ab)
        panel(ctx, [("10%点〜90%点", 44, WHITE), ("153〜504匹", 56, YEL)], 1560, 400, a=ab, pad=(36, 12))


def sc_c3_f(ctx, t):
    flat(ctx)
    base = 830
    tb = SC_START["c3_f"] + 0.4
    for x, nm, v, col, tv in ((600, "川生まれ", 82, "#7fb0e6", tb), (1050, "ふ化場", 364, YOU, tb + 0.35)):
        if t < tv:
            continue
        u = ease(seg(t, tv, tv + 0.8))
        h = v * 1.15 * u
        box(ctx, x - 120, base - h, x + 120, base, col, r=8)
        label(ctx, nm, x, base + 48, 46, WHITE)
        if u > 0.95:
            label(ctx, f"{v}匹", x, base - h - 48, 60, YEL)
    # 「低く見ると」の3本目（声と一緒に出す）
    tl_ = Sk("c3_low", 0.3)
    if t >= tl_:
        u = ease(seg(t, tl_, tl_ + 0.8))
        v = ihalf(Q1["5"]["back"]["median"])
        h = v * 1.15 * u
        box(ctx, 1500 - 120, base - h, 1500 + 120, base, "#7fb0e6", fade(t, tl_, 0.3), r=8)
        label(ctx, "川生まれ（低く見ると）", 1500, base + 48, 46, WHITE, a=fade(t, tl_, 0.3))
        if u > 0.95:
            label(ctx, f"{v}匹", 1500, base - h - 48, 60, YEL)
    line2(ctx, (380, base + 2), (1270 if t < tl_ else lerp(1270, 1720, ease(seg(t, tl_, tl_ + 0.6))), base + 2), WHITE, 5)
    card(ctx, t, Sk("c3_cmp", 0.3), None, [("差は 約4〜18倍", 76, YEL), ("（川の卵の生き残り20〜5%で）", 44, PALE)], 1500, 190, pad=(40, 16), border=YEL)


def _egg_tank_bg(ctx, t):
    flat(ctx, ROOM)
    tank(ctx, 40, 300, 960, 900)
    box(ctx, 1000, 150, 1920, 900, "#3e8fc4", r=0)
    fill(ctx, hexrgb("#ffffff", 0.3))
    for k in range(3):
        ctx.rectangle(1100 + 140 * k, 300 + 150 * k, 80, 6)
        ctx.fill()


TANK_G_EGGS = Bed((70, 700, 930, 880), 14, 20, seed=131)


def sc_c3_g(ctx, t):
    _egg_tank_bg(ctx, t)
    TANK_G_EGGS.draw(ctx, t, sway=2.0)
    tz = SC_START["c3_g"] + 0.25
    r = lerp(46, YOU_EGG_R, ease(seg(t, tz, tz + 1.8)))
    t17 = Sk("c3_spring", 0.0)
    if t < t17:
        you_egg(ctx, t, 500, 600, r)
    else:
        a = 1 - clamp01((t - t17) / 0.5)
        if a > 0.02:
            you_egg(ctx, t, 500, 600, YOU_EGG_R, a=a)
        u = ease(seg(t, t17 + 0.2, Ek("c3_nogravel") - 0.2))
        you_fish(ctx, t, lerp(500, 1400, u), 600 + 6 * math.sin(t * 2), YOU_FRY_L, "fry", a=clamp01((t - t17) / 0.5), ang=0.0, glow_r=YOU_FRY_L * 0.5)
    card(ctx, t, Sk("c3_nogravel", 0.0) + 0.5, None, [("ここで終わる数（/1万粒）", 44, WHITE), ("関門1で 1,250粒", 66, YEL)], 1450, 190, pad=(36, 14), border=YEL)


H3_SCHOOL = Swarm((60, 330, 1860, 880), 30, 110, "fry", FISHC, seed=137, keepout=(900, 620, 220))


def sc_c3_h(ctx, t):
    bg_mouth(ctx)
    t0 = SC_START["c3_h"]
    winter_sky(ctx, seg(t, t0 + 0.2, t0 + 1.8))
    snow(ctx, t, seg(t, t0 + 0.4, t0 + 1.8))
    ex = exits_at(H3_SCHOOL.n, set(), Sk("c3_endwin", 0.25), Sk("c3_endwin", 0.7), 139)
    H3_SCHOOL.draw(ctx, t, ex=ex, vx=900.0, cruise=40.0, ct0=t0)
    al = 1 - 0.65 * ease(seg(t, Sk("c3_endwin", 0.4), Ek("c3_endwin")))
    you_fish(ctx, t, 900, 620 + 8 * math.sin(t * 1.5), 280, "fry", a=al, ang=0.0, glow_r=160)
    card(ctx, t, Sk("c3_endwin", 0.0) + 0.1, None, [("最初の冬", 56, WHITE)], 190, 125, pad=(30, 12))
    card(ctx, t, Sk("c3_8of10", 0.0) + 0.2, None, [("ここで終わる数（/1万粒）", 44, WHITE), ("関門2で 約8,160匹", 66, YEL)], 1450, 190, pad=(36, 14), border=YEL)


def sc_c3_i(ctx, t):
    flat(ctx)
    label(ctx, "真ん中の1粒が行ける所", 960, 120, 52, YEL)
    t1 = SC_START["c3_i"] + 0.3
    gate_row(ctx, t, y=520, h=270, lit=1 if t >= Sk("c3_same2", 0.0) + 0.1 else None)
    u = ease(seg(t, Sk("c3_moved", 0.4), Sk("c3_moved", 0.85)))
    you_egg(ctx, t, lerp(GX[0], GX[1], u), 280, 62, a=fade(t, t1))


GRAV_J = Bed((50, 480, 1870, 915), 110, 25, seed=141, keepout=(960, 720, 160))


def sc_c3_j(ctx, t):
    bg_gravel(ctx, 330)
    GRAV_J.draw(ctx, t)
    you_egg(ctx, t, 960, 720, 100)
    t24 = Sk("c3_30", 0.0)
    card(ctx, t, t24 + 0.15, Sk("c3_nat") + 0.0, [("川で捕獲されたサケのうち", 44, WHITE), ("川や年によっては", 44, WHITE), ("約30%超（推定）", 76, YEL)], 960, 200, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c3_nat", 0.0) + 0.4, None, [("全国の割合は 不明", 64, YEL)], 960, 200, pad=(40, 14), border=YEL)


def sc_c3_ans(ctx, t):
    tc = T("c3_ans", 0.1)
    label(ctx, "答え", 960, 95, 72, YEL)
    panel(ctx, [("ふ化場で生まれると、", 50, WHITE), ("1つ先まで行ける", 76, YEL), ("でも、最初の冬という関門は", 48, WHITE), ("変わらない", 64, YEL)], 960, 380, a=fade(t, tc), border=YEL, pad=(60, 24))
    you_fish(ctx, t, 960, 765, 440, "fry", a=fade(t, bd("c3_ans") + 0.5), glow_r=190)


# ============================================================
# 4 大きく育つと、有利？
# ============================================================
def sc_c4_a(ctx, t):
    flat(ctx)
    fish(ctx, 620 + 70 * math.sin(t * 0.7), 480 + 18 * math.sin(t * 1.1), 560, FISHC, "fry", t * 1.2, 1)
    t1 = Sk("c4_1g", 0.0) + 0.2
    if t >= t1:
        a = fade(t, t1, 0.5)
        box(ctx, 340, 760, 900, 800, "#f0e6c8", a, r=6)
        for k in range(6):
            line2(ctx, (340 + k * 112, 760), (340 + k * 112, 782 - (0 if k in (0, 5) else 8)), "#4a4a4a", 4, a)
        label(ctx, "5cm", 900, 850, 46, WHITE, a=a)
        label(ctx, "体長", 340, 850, 46, PALE, a=a)
    card(ctx, t, t1, None, [("目安", 44, PALE), ("体重1g・体長5cm", 58, YEL)], 1440, 240, pad=(34, 14))
    card(ctx, t, Sk("c4_dir", 0.0) + 0.1, None, [("大きいほうが帰ってきやすい", 46, WHITE), ("資料でも報告されている", 58, YEL)], 1440, 470, pad=(34, 14))
    card(ctx, t, Sk("c4_01", 0.3), None, [("大きさと、放す時期や水温は", 44, WHITE), ("切り離せない", 56, YEL)], 1440, 710, pad=(34, 14))


KAI_L = Swarm((120, 640, 760, 900), 24, 64, "fry", FISHC, seed=151)


def sc_c4_b(ctx, t):
    flat(ctx)
    card(ctx, t, Sk("c4_kaiki", 0.0) + 0.3, None, [("回帰率", 110, YEL)], 960, 170, pad=(50, 16), border=YEL)
    KAI_L.draw(ctx, t, cruise=0.0)
    arrow2(ctx, (860, 770), (1130, 770), WHITE, 10, 0.8)
    for k in range(4):
        fish(ctx, 1300 + 110 * (k % 3), 720 + 90 * (k // 3), 100, YOU, "adult", t * 1.6 + k, 1)
    card(ctx, t, Sk("c4_def", 0.0) + 0.1, None, [("帰ってきて捕まったサケ", 56, WHITE), ("÷", 56, YEL), ("放流した稚魚", 56, WHITE)], 960, 440, pad=(44, 16))


YEARS_L = sorted(YEARS)
BARX0, BSTEP, BW, BBASE, BSC = 140, 56, 44, 790, 520 / 7.15
BAR_DT = 0.26


def _bar_x(y):
    return BARX0 + (y - 1989) * BSTEP


def _small_school(ctx, t, n_on, a=1.0, x0=1210, y0=330):
    """100匹放流の絵（20列×5段）。n_on 匹がオレンジ（帰ってきた）"""
    for k in range(100):
        if k == 0:
            box(ctx, x0 - 34, y0 - 96, x0 + 19 * 31 + 34, y0 + 4 * 38 + 34, PANEL, a, r=14)   # 棒の上でも読めるように
        r_, c_ = divmod(k, 20)
        col = YOU if k in ON_IDX[:n_on] else FISHC
        fish(ctx, x0 + c_ * 31, y0 + r_ * 38, 42, col, "fry", t * 1.6 + k * 0.1, 1, a)


ON_IDX = random.Random(5).sample(range(100), 7)


def sc_c4_bars(ctx, t):
    flat(ctx)
    label(ctx, "北海道の回帰率（生まれた年ごと）", 90, 70, 46, WHITE, align="left")
    for g in (2, 4, 6):
        yy = BBASE - g * BSC
        line2(ctx, (BARX0 - 10, yy), (BARX0 + 29 * BSTEP, yy), "#3b5f8f", 3)
        label(ctx, f"{g}%", BARX0 - 42, yy, 42, PALE)
    line2(ctx, (BARX0 - 10, BBASE + 2), (BARX0 + 29 * BSTEP, BBASE + 2), WHITE, 5)
    for y in (1989, 1999, 2005, 2013, 2017):
        label(ctx, str(y), _bar_x(y) + BW / 2, BBASE + 50, 42, PALE)
    tb0 = Sk("c4_notenough", 0.0) + 0.6
    t99, t13 = Sk("c4_high", 0.0) + 0.1, Sk("c4_low", 0.0) + 0.1
    for k, y in enumerate(YEARS_L):
        tk = tb0 + k * BAR_DT
        if t < tk:
            continue
        h = YEARS[y] * BSC * ease_out(clamp01((t - tk) / 0.3))
        col = YOU if ((y == 1999 and t >= t99) or (y == 2013 and t >= t13)) else FISHC
        box(ctx, _bar_x(y), BBASE - h, _bar_x(y) + BW, BBASE, col, r=3)
    card(ctx, t, Sk("c4_years", 0.0) + 0.5, Sk("c4_high") - 0.5, [("公式の図から読み取り", 44, PALE)], 1380, 100, pad=(30, 10))
    # 1999年級
    card(ctx, t, t99, Sk("c4_low") - 0.45, [("1999年級", 46, WHITE), ("7.15%", 80, YEL)], 1200, 150, pad=(36, 12), border=YEL)
    t7 = Sk("c4_7", 0.0) + 0.1
    if t7 <= t < Sk("c4_low") - 0.1:
        a = fade(t, t7, 0.3) * out_fade(t, Sk("c4_low") - 0.2, 0.2)
        _small_school(ctx, t, 7, a)
        label(ctx, "7匹あまり /100匹", 1560, 282, 42, WHITE, a=a)
    # 2013年級
    card(ctx, t, t13, Sk("c4_64") - 0.1, [("2013年級", 46, WHITE), ("1.12%", 80, YEL)], 1200, 150, pad=(36, 12), border=YEL)
    t1 = Sk("c4_1", 0.0) + 0.1
    if t1 <= t < Sk("c4_64") - 0.1:
        a = fade(t, t1, 0.3) * out_fade(t, Sk("c4_64") - 0.2, 0.2)
        _small_school(ctx, t, 1, a)
        label(ctx, "1匹ほど /100匹", 1560, 282, 42, WHITE, a=a)
    # 差
    t64 = Sk("c4_64", 0.0) + 0.1
    if t64 <= t < Sk("c4_143") - 0.1:
        a = fade(t, t64, 0.3)
        y99, y13 = BBASE - 7.15 * BSC, BBASE - 1.12 * BSC
        line2(ctx, (_bar_x(1999), y99), (1840, y99), WHITE, 3, a * 0.8, dash=[10, 8])
        line2(ctx, (_bar_x(2013), y13), (1840, y13), WHITE, 3, a * 0.8, dash=[10, 8])
        arrow2(ctx, (1840, y99 + 6), (1840, y13 - 6), YEL, 6, a, head=22)
        arrow2(ctx, (1840, y13 - 6), (1840, y99 + 6), YEL, 6, a, head=22)
        panel(ctx, [("約6.4倍", 100, YEL)], 1560, 410, a=a, border=YEL, pad=(40, 14))
    # 1万粒なら
    t143 = Sk("c4_143", 0.0) + 0.15
    card(ctx, t, t143, Sk("c4_choose") - 0.1, [("1999年級", 46, WHITE), ("143匹", 80, YEL)], 1310, 200, pad=(36, 12), border=YEL)
    card(ctx, t, Sk("c4_22", 0.0) + 0.1, Sk("c4_choose") - 0.1, [("2013年級", 46, WHITE), ("22匹", 80, YEL)], 1660, 200, pad=(36, 12), border=YEL)
    card(ctx, t, t143, Sk("c4_choose") - 0.1, [("/1万粒（川生まれ・生き残り20%）", 42, PALE)], 1480, 360, pad=(26, 10))
    # あなたは年を選べない
    tc = Sk("c4_choose", 0.0)
    if t >= tc:
        you_egg(ctx, t, 330, 245, 85, a=fade(t, tc, 0.4))
        pass


def sc_c4_ans(ctx, t):
    tc = T("c4_ans", 0.1)
    label(ctx, "答え", 960, 95, 72, YEL)
    panel(ctx, [("大きく育つと、帰りやすくなる", 52, WHITE), ("でも、生まれた年だけで", 52, WHITE), ("回帰率は 約6.4倍 違った", 76, YEL)], 960, 390, a=fade(t, tc), border=YEL, pad=(60, 26))
    you_egg(ctx, t, 960, 790, 105, a=fade(t, bd("c4_ans") + 0.5))


# ============================================================
# 5 3,000粒から、何匹帰れば足りる？
# ============================================================
WATER_TOP = 640      # 問い4の川の断面: 魚が泳ぐ水を広く、砂利は下に
MOM_BED = Bed((40, 720, 640, 950), 40, 22, seed=161)


def sc_c5_a(ctx, t):
    bg_gravel(ctx, WATER_TOP)
    t1 = Sk("c5_3000", 0.0)
    MOM_BED.draw(ctx, t, appear=ramp(list(range(MOM_BED.n)), t1 - 0.5, t1 + 2.5))
    fish(ctx, 1100, 430, 560, FISHC, "adult", t * 1.4, 1)
    card(ctx, t, t1 + 0.4, None, [("卵の数 約2,000〜3,000粒（メス4年魚）", 44, WHITE), ("→ 多めに 3,000粒とする", 64, YEL)], 960, 150, pad=(40, 14), border=YEL)


def sc_c5_b(ctx, t):
    flat(ctx)
    fish(ctx, 560, 560, 520, FISHC, "adult", t * 1.4, 1)
    fish(ctx, 1360, 560, 520, mix(FISHC, "#6f8fd0", 0.5), "adult", t * 1.4 + 0.4, -1)
    label(ctx, "メス", 560, 780, 52, WHITE)
    label(ctx, "オス", 1360, 780, 52, WHITE)
    card(ctx, t, Sk("c5_once", 0.0) + 0.2, Sk("c5_two") - 0.4, [("産卵は 1度だけ", 64, YEL)], 960, 150, pad=(44, 14), border=YEL)
    card(ctx, t, Sk("c5_two", 0.0) + 0.1, None, [("オス1匹＋メス1匹＝2匹", 64, YEL), ("（雌雄1対1は仮定）", 44, PALE)], 960, 160, pad=(44, 14), border=YEL)


C_BED = Bed((60, 720, 1860, 950), 120, 22, seed=171)


def sc_c5_c(ctx, t):
    bg_gravel(ctx, WATER_TOP)
    C_BED.draw(ctx, t)
    fish(ctx, 1300, 370, 240, YOU, "adult", t * 1.6, 1)
    fish(ctx, 1300, 530, 240, YOU, "adult", t * 1.6 + 0.5, 1)
    card(ctx, t, Sk("c5_yoso", 0.0) + 0.3, None, [("あなたの予想", 46, PALE), ("昔も今も 2匹くらい 楽に残る", 56, YEL)], 960, 150, pad=(44, 16), border=YEL)


NEST_BED = Bed((60, 450, 1860, 900), 100, 30, seed=181, cols=20)


def sc_c5_d(ctx, t):
    bg_gravel(ctx, 330)
    for k, (x, y, ph) in enumerate(NEST_BED.pts):
        fill(ctx, hexrgb("#7a6652"))
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(1.0, 0.45)
        ctx.arc(0, 0, 38, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
        fill(ctx, hexrgb("#a28d74"))
        ctx.save()
        ctx.translate(x, y - 2)
        ctx.scale(1.0, 0.4)
        ctx.arc(0, 0, 26, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
        for j in range(3):
            draw_egg(ctx, x - 10 + 10 * j, y - 4, 6, EGGC, False, 1.0)
    card(ctx, t, Sk("c5_10k", 0.0) + 0.3, Sk("c5_gates") - 0.7, [("お母さん 1万匹", 64, YEL), ("1つ＝100匹", 44, WHITE)], 70, 150, align="left", pad=(30, 12), border=YEL)
    # 1匹のお母さんの卵が、4つの関門を進む
    tg = Sk("c5_gates", 0.0)
    if t >= tg - 0.4:
        a = fade(t, tg - 0.4, 0.4)
        box(ctx, 0, 0, W_, 560, ROOM, a, r=0)
        gate_row(ctx, t, y=170, h=200, a=a)
        alive = [30, 6, 1, 1]
        gx = [255, 725, 1195, 1665]
        for j in range(30):
            tj = tg + 0.1 + 0.05 * j
            if t < tj:
                continue
            u = seg(t, tj, tj + 3.2)
            x = lerp(80, 1860, u)
            stage = sum(1 for g in gx if x > g)
            if j >= alive[min(3, stage - 1) if stage > 0 else 0] and stage > 0:
                continue
            draw_egg(ctx, x, 430 + 8 * math.sin(j + t * 3), 22 if j else 30, EGGC if j else YOU, j == 0, a)


def sc_c5_e(ctx, t):
    flat(ctx)
    label(ctx, "29年分の回帰率", 90, 100, 46, WHITE, align="left")
    x0, st, bw, base, sc = 140, 44, 34, 760, 60.0
    ys = sorted(YEARS)
    t0 = SC_START["c5_e"] + 0.3
    hi = None
    ts = Sk("c5_lot", 0.0) + 0.4
    seq = [3, 17, 8, 22, 5, 14, 26, 11, 19, 7]
    fin = 12
    k_ = int(max(0.0, (t - ts)) / 0.3)
    if t >= ts:
        hi = seq[k_] if k_ < len(seq) else fin
    for k, y in enumerate(ys):
        h = YEARS[y] * sc * ease_out(clamp01((t - t0 - 0.02 * k) / 0.3))
        box(ctx, x0 + k * st, base - h, x0 + k * st + bw, base, YOU if hi == k else FISHC, r=3)
    line2(ctx, (x0 - 10, base + 2), (x0 + 29 * st, base + 2), WHITE, 5)
    label(ctx, "1989", x0 + bw / 2, base + 46, 42, PALE)
    label(ctx, "2017", x0 + 28 * st + bw / 2, base + 46, 42, PALE)
    kuji_x = 1570
    box(ctx, kuji_x - 150, 330, kuji_x + 150, 570, "#b8473f", r=18)
    box(ctx, kuji_x - 150, 330, kuji_x + 150, 352, "#d9655a", r=12)
    fill(ctx, hexrgb("#5a1f1b"))
    ctx.arc(kuji_x, 450, 48, 0, 2 * math.pi)
    ctx.fill()
    card(ctx, t, ts - 0.1, None, [("くじで 年を選ぶ", 56, YEL)], kuji_x, 260, pad=(30, 12))
    card(ctx, t, Sk("c5_riv", 0.0) + 0.1, None, [("川生まれ", 50, WHITE), ("生き残り20%", 64, YEL)], kuji_x, 700, pad=(34, 14), border=YEL)


MOM24 = Swarm((100, 440, 1000, 880), 24, 120, "adult", FISHC, seed=191, cols=6)


def sc_c5_f(ctx, t):
    flat(ctx)
    MOM24.draw(ctx, t, appear=ramp(list(range(MOM24.n)), SC_START["c5_f"] + 0.5, SC_START["c5_f"] + 1.5), fd=0.3)
    card(ctx, t, Sk("c5_24", 0.7), None, [("帰ってきて捕られるサケ（/3,000粒）", 44, WHITE), ("平均 約24匹", 90, YEL), ("中央値 24匹", 72, WHITE)], 960, 190, pad=(40, 16), border=YEL)
    t2 = Sk("c5_enough", 0.0) + 0.1
    if t >= t2:
        a = fade(t, t2, 0.4)
        fish(ctx, 1380, 680, 190, YOU, "adult", t * 1.6, 1, a)
        fish(ctx, 1600, 760, 190, YOU, "adult", t * 1.6 + 0.4, 1, a)
        label(ctx, "必要な2匹", 1490, 560, 56, YEL, a=a)


# ---- 表（卵の生き残り × 昔の年・近年の年）----
def _tbl_rows():
    rows = []
    for k in ("20", "10", "5"):
        v = Q4[k]
        rows.append((f"{k}%", f"{v['old']['mean']}匹", f"{v['new']['mean']}匹", f"約{ihalf(v['need_pct']['old'])}%", f"約{ihalf(v['need_pct']['new'])}%"))
    return rows


TBL = _tbl_rows()
TC = [230, 620, 1030]                       # 列の真ん中（卵の生き残り・昔・近年）
TY = [400, 540, 680]
RED2 = "#ff8c8c"


def sc_c5_table(ctx, t):
    flat(ctx)
    label(ctx, "お母さん1匹の卵から、人に捕られるサケ（/3,000粒）", 90, 70, 46, WHITE, align="left")
    label(ctx, "卵の生き残り", TC[0], 200, 46, PALE)
    for k in range(3):
        label(ctx, TBL[k][0], TC[0], TY[k], 64, YEL)
        line2(ctx, (90, TY[k] + 66), (1850, TY[k] + 66), "#3b5f8f", 3)
    t12 = Sk("c5_oldnew", 0.0) + 0.1
    if t >= t12:
        a = fade(t, t12, 0.35)
        label(ctx, "昔の年", TC[1], 160, 50, WHITE, a=a)
        label(ctx, "1989〜2005年級", TC[1], 222, 42, PALE, a=a)
        label(ctx, "近年の年", TC[2], 160, 50, WHITE, a=a)
        label(ctx, "2013〜2017年級", TC[2], 222, 42, PALE, a=a)
    t13 = Sk("c5_table", 0.0) + 0.2
    red = t >= Sk("c5_table", 0.55)
    for k in range(3):
        tk = t13 + 0.3 * k
        if t >= tk:
            a = fade(t, tk, 0.3)
            label(ctx, TBL[k][1], TC[1], TY[k], 60, WHITE, a=a)
            label(ctx, TBL[k][2], TC[2], TY[k], 60, RED2 if red else WHITE, a=a)
    if red:
        a = fade(t, Sk("c5_table", 0.55), 0.4)
        ctx.set_source_rgba(*hexrgb(RED2, a))
        ctx.set_line_width(6)
        rrect(ctx, TC[2] - 190, 140, 380, 600, 16)
        ctx.stroke()
    # 「これとは別の2匹」が、空いている右の列で泳ぐ（表が10秒以上止まらないように）
    t2f, t2e = Sk("c5_oldnew", 0.0), SC_START["c5_bars"] + 0.3
    if t2f <= t < t2e:
        for k in range(2):
            fish(ctx, 1420 + ((t - t2f) * 34 + k * 70) % 330, 575 + k * 125, 190, YOU, "adult", t * 1.6 + k, 1, fade(t, t2f, 0.3))
    card(ctx, t, Sk("c5_need", 0.0) + 0.2, None, [("捕られる分とは別に", 44, WHITE), ("2匹", 84, YEL), ("網をくぐって川を上る", 40, WHITE)], 1560, 280, pad=(30, 12), border=YEL)


def sc_c5_bars(ctx, t):
    flat(ctx)
    base = 830
    tb = SC_START["c5_bars"] + 0.3
    gx = 200
    label(ctx, "人に捕られるサケ（/3,000粒）", gx + 300, 250, 50, YEL)
    tvs = (tb, Sk("c5_why", 0.0) + 2.0)
    for j, (nm, v, vt, col) in enumerate((("昔の年", 28.8, "28.8匹", FISHC), ("近年の年", 10.4, "10.4匹", RED2))):
        x = gx + 40 + j * 320
        if t < tvs[j]:
            continue
        u = ease(seg(t, tvs[j], tvs[j] + 0.7))
        h = v * 15.0 * u
        box(ctx, x, base - h, x + 220, base, col, r=8)
        label(ctx, nm, x + 110, base + 46, 44, WHITE)
        if u > 0.95:
            label(ctx, vt, x + 110, base - h - 40, 54, YEL)
    line2(ctx, (gx, base + 2), (gx + 640, base + 2), WHITE, 4)
    t3 = Sk("c5_19", 0.0) + 0.2
    card(ctx, t, t3, None, [("捕り方が同じなら、帰ってくるサケも", 46, WHITE), ("約3分の1に", 92, YEL)], 1370, 270, pad=(44, 18), border=YEL)
    td = Sk("c5_dir", 0.0) + 0.2
    if t >= td:
        a = fade(t, td, 0.35)
        label(ctx, "卵の生き残りを変えても（/3,000粒）", 1370, 480, 42, PALE, a=a)
        for k in range(3):
            tk = td + 0.3 * k
            if t >= tk:
                ak = fade(t, tk, 0.3)
                label(ctx, TBL[k][0], 1090, 570 + k * 82, 54, YEL, a=ak)
                label(ctx, TBL[k][1], 1300, 570 + k * 82, 54, WHITE, a=ak)
                arrow2(ctx, (1400, 570 + k * 82), (1480, 570 + k * 82), WHITE, 7, ak, head=20)
                label(ctx, TBL[k][2], 1590, 570 + k * 82, 54, RED2, a=ak)
        card(ctx, t, td + 1.0, None, [("どれも 約3分の1", 54, YEL)], 1370, 850, pad=(30, 10))


def sc_c5_net(ctx, t):
    t0 = SC_START["c5_net"]
    net_scene(ctx, t, t0, school=True, up=[t0 + 0.4 + 1.5 * k for k in range(14)])   # 間があいても止まって見えないように、1匹ずつ川を上る
    card(ctx, t, Sk("c5_notsay", 0.0) + 0.1, None, [("2匹が川を上れているかは 分からない", 56, YEL), ("川を上ったサケは 誰も数えていない", 46, WHITE)], 960, 170, pad=(40, 14), border=YEL)


MOTH_BED = Bed((40, 720, 620, 950), 30, 22, seed=201)


def sc_c5_g1(ctx, t):
    bg_gravel(ctx, WATER_TOP)
    t1 = Sk("c5_egg", 0.0)
    MOTH_BED.draw(ctx, t, appear=ramp(list(range(MOTH_BED.n)), t1 + 0.2, Ek("c5_egg") - 0.3))
    you_fish(ctx, t, 1150, 340 + 6 * math.sin(t * 1.5), YOU_ADULT_L, "adult", glow_r=300)


G2_BED = Bed((60, 720, 1860, 950), 100, 26, seed=211, cols=20)
TEN10 = Swarm((120, 300, 980, 590), 10, 130, "adult", FISHC, seed=213, cols=5)


def sc_c5_g2(ctx, t):
    bg_gravel(ctx, WATER_TOP)
    t0 = Sk("c5_most", 0.0) + 0.2
    G2_BED.draw(ctx, t, fade={i: t0 + 3.0 * i / max(1, G2_BED.n) for i in range(G2_BED.n)}, fd=0.7)
    t10 = Sk("c5_10", 0.0)
    TEN10.draw(ctx, t, appear=ramp(list(range(TEN10.n)), t10 + 0.2, t10 + 1.0), fd=0.3)
    card(ctx, t, t10 + 0.2, None, [("2013〜2017年級（/3,000粒）", 44, WHITE), ("10.4匹", 96, YEL)], 1450, 300, pad=(36, 14), border=YEL)
    card(ctx, t, t10 + 0.3, None, [("絵の1匹＝1匹", 44, WHITE)], 70, 150, align="left", pad=(26, 10))


def sc_c5_g3(ctx, t):
    t0 = SC_START["c5_g3"]
    bg_sea(ctx)
    _river_strip(ctx)
    set_net(ctx, *NET2, cell=60)
    for k in range(12):     # k<2 は、数えられる10匹とは別の2匹
        x, y = (140 + k * 130, 440) if k < 2 else (140 + ((k - 2) % 5) * 130, 560 + ((k - 2) // 5) * 120)
        if k < 2:
            tk = Sk("c5_2of10", 0.3) + 0.6 * k
            u = seg(t, tk, tk + 3.0)
            if u > 0:
                path = [(x, y), (1100, 910), (1700, 905), (1795, 800), (1795, 300)]
                px, py, ang = _path_pos(path, u)
                fish_dir(ctx, px, py, 130, YOU, "adult", ang, t * 1.6 + k)
                continue
            fish(ctx, x, y, 130, YOU, "adult", t * 1.6 + k, 1)
        else:
            fish(ctx, x + 30 * math.sin(t * 0.9 + k), y + 10 * math.sin(t * 1.3 + k), 130, FISHC, "adult", t * 1.6 + k * 0.3, 1)
    card(ctx, t, Sk("c5_2of10", 0.0) + 0.1, Sk("c5_old") - 0.4, [("網をくぐって川を上る", 44, WHITE), ("2匹", 96, YEL)], 960, 170, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c5_old", 0.0) + 0.1, None, [("昔なら、捕られるサケは", 44, WHITE), ("約29匹", 96, YEL)], 960, 170, pad=(40, 14), border=YEL)


def sc_c5_ans(ctx, t):
    tc = T("c5_ans", 0.1)
    label(ctx, "答え", 960, 95, 72, YEL)
    panel(ctx, [("お母さん1匹の卵から帰ってきて、人に捕られるサケは", 46, WHITE), ("昔の約3分の1", 84, YEL), ("2匹が残れているかは、数えられていないので分からない", 42, WHITE)], 960, 380, a=fade(t, tc), border=YEL, pad=(60, 26))
    you_fish(ctx, t, 960, 765, 460, "adult", a=fade(t, bd("c5_ans") + 0.5), glow_r=180)


# ============================================================
# 6 まとめ・終了画面
# ============================================================
C6_X, C6_W, C6_TOP, C6_BOT = (255, 725, 1195, 1665), 430, 40, 500
C6_ROWS = [[("砂利の中で", 66, WHITE, 140), ("終わる", 96, YEL, 270)],
           [("ふ化場なら", 62, WHITE, 120), ("1つ先へ", 62, WHITE, 205), ("進む", 88, YEL, 330)],
           [("生まれた年で", 62, WHITE, 150), ("約6.4倍", 100, YEL, 300)],
           [("捕られる", 62, WHITE, 115), ("サケは昔の", 62, WHITE, 205), ("約3分の1", 80, YEL, 335)]]


def window(ctx, x, y, w, h, fn, t, a=1.0):
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rectangle(0, 0, w, h)
    ctx.clip()
    grp(ctx, a, fn, t)
    ctx.restore()


WIN_W, WIN_H, WIN_Y = 560, 340, 545
WIN_X = [60, 680, 1300]
W_EGGS = Bed((20, 200, 540, 330), 14, 14, seed=221)
W_SCH = Swarm((20, 150, 540, 310), 8, 70, "fry", FISHC, seed=223)
W_SEA = Swarm((20, 90, 540, 300), 8, 70, "adult", FISHC, seed=225)


def _w_gravel(ctx, t):
    gravel_bed(ctx, WIN_W, WIN_H, top=110)
    W_EGGS.draw(ctx, t, sway=1.5)
    you_egg(ctx, t, 280, 250, 46)


def _w_mouth(ctx, t):
    river_mouth(ctx, WIN_W, WIN_H)
    W_SCH.draw(ctx, t, cruise=60.0, ct0=0.0)
    you_fish(ctx, t, 280, 220, 120, "fry", glow_r=60)


def _w_sea(ctx, t):
    north_sea(ctx, WIN_W, WIN_H)
    ex = exits_at(W_SEA.n, set(range(2)), Sk("c6_0b", 0.2), Sk("c6_0b", 0.6), 231)
    W_SEA.draw(ctx, t, ex=ex, vx=500.0)
    you_fish(ctx, t, 280, 220, 140, "adult", glow_r=70)


def _w_bars(ctx, t):
    t1 = Sk("c6_1", 0.0) + 0.2
    label(ctx, "人に捕られるサケ", 330, 740, 56, WHITE)
    for k in range(4):   # 止まって見えないように、右で小さな群れを泳がせる
        fish(ctx, 1380 + ((t * 45 + k * 110) % 420), 660 + k * 58, 150, FISHC, "adult", t * 1.6 + k, 1)
    for j, (nm, h, vt, col) in enumerate((("昔の年", 135, "約29匹", FISHC), ("近年の年", 49, "約10匹", RED2))):
        x = 650 + j * 400
        u = ease(seg(t, t1 + 0.3 * j, t1 + 0.3 * j + 0.7))
        box(ctx, x, 835 - h * u, x + 220, 835, col, r=8)
        label(ctx, nm, x + 110, 872, 44, WHITE)
        if u > 0.95:
            label(ctx, vt, x + 110, 835 - h * u - 40, 54, YEL)


def _w_net(ctx, t):
    north_sea(ctx, 1800, WIN_H)
    set_net(ctx, 760, 70, 1240, 330, cell=60)
    t2 = Sk("c6_2", 0.0)
    for k in range(4):
        u = seg(t, t2 + 0.2 + 0.6 * k, t2 + 3.2 + 0.6 * k)
        if u > 0:
            x, y, ang = _path_pos([(220, 160 + 14 * k), (700, 300), (1350, 320), (1700, 200)], u)
            fish_dir(ctx, x, y, 110, FISHC, "adult", ang, t * 1.6 + k, a=0.5)


def sc_c6_answers(ctx, t):
    t0 = ch_start(6) + T_TITLE[6]
    for k, rows in enumerate(C6_ROWS):
        x = C6_X[k]
        a = fade(t, t0 + 0.2 + 0.4 * k)
        if a <= 0.003:
            continue
        hl = (k in (0, 1) and Sk("c6_0", 0.0) <= t < Sk("c6_1", 0.0)) or (k == 3 and t >= Sk("c6_1", 0.0) and t < Sk("c6_3", 0.0))
        box(ctx, x - C6_W / 2, C6_TOP, x + C6_W / 2, C6_BOT, PANEL, a, r=26)
        if hl:
            ctx.set_source_rgba(*hexrgb(YEL, a))
            ctx.set_line_width(7)
            rrect(ctx, x - C6_W / 2 + 4, C6_TOP + 4, C6_W - 8, C6_BOT - C6_TOP - 8, 22)
            ctx.stroke()
        for s_, sz, col, yy in rows:
            label(ctx, s_, x, yy, sz, col, a=a)
    # 下の絵: 砂利 → 河口 → 冬の海 が順に出る → 約29匹→約10匹の棒 → 網のすきまを上る魚
    tA, tB, tC = Sk("c6_0", 0.1), Sk("c6_0", 0.55), Sk("c6_0b", 0.0)
    t1, t2 = Sk("c6_1", 0.0) - 0.2, Sk("c6_2", 0.0) - 0.2
    ff = 1 - clamp01((t - t1) / 0.4)
    for x, fn, tt in zip(WIN_X, (_w_gravel, _w_mouth, _w_sea), (tA, tB, tC)):
        if t >= tt:
            window(ctx, x, WIN_Y, WIN_W, WIN_H, fn, t, a=fade(t, tt, 0.4) * ff)
    if t1 <= t < t2 + 0.4:
        box(ctx, 60, WIN_Y, 1860, WIN_Y + WIN_H, PANEL, 0.9 * fade(t, t1 + 0.3, 0.4) * out_fade(t, t2, 0.3), r=18)
        grp(ctx, fade(t, t1 + 0.3, 0.4) * out_fade(t, t2, 0.3), _w_bars, t)
    if t >= t2:
        window(ctx, 60, WIN_Y, 1800, WIN_H, _w_net, t, a=fade(t, t2 + 0.1, 0.4))


def sc_c6_close(ctx, t):
    bg_gravel(ctx, 330)
    GRAV_J.draw(ctx, t)
    you_egg(ctx, t, 1250, 720, 150)
    tq = Sk("c6_3", 0.0)
    card(ctx, t, tq, None, [("あなたの1粒は、", 56, WHITE), ("どこまで行けたと思いますか？", 64, YEL)], 80, 175, align="left", pad=(36, 18), border=YEL)
    tn = Sk("c6_4", 0.05)
    card(ctx, t, tn, None, [("数字は、この動画の仮定を置いた", 44, WHITE), ("計算の結果。実際のサケの数を", 44, WHITE), ("言い当てるものではない", 44, WHITE)], 80, 420, align="left", pad=(30, 14))


END_SUB = ["よければ", "チャンネル登録・高評価", "お願いします"]


def end_rows():
    return [("中央値で帰ってこられたのは", "約80匹"), ("いちばん多くいなくなるのは", "最初の冬まで"), ("帰ってきて捕られるサケ（お母さん1匹）", "昔の約3分の1")]


def sc_end(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    label(ctx, "答え", 490, 90, 80, YEL, a=b)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 46, WHITE), (val, 70 if len(val) <= 10 else 60, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        a = fade(t, t9 + 0.1, 0.4)
        you_fish(ctx, t, 1400, 420 + 10 * math.sin(t * 1.8), 460, "adult", a=a, glow_r=250)
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1430, 760, a=fade(t, t9 + 0.3, 0.4))


# ============================================================
# 区切り（ここまで／ここから・小さなサケが泳ぐ）。engine/longkit.py の Eyecatch を、平たい地・白と黄色の文字で描き直したもの
# ============================================================
EC_LEFT = ("真ん中の1粒は砂利の中で終わる", "いちばん減るのは最初の冬まで", "ふ化場なら1つ先へ進む")
EC_RIGHT = ("大きく育つと有利？", "2匹を残すのは、昔より難しい？")
EC_FADE = 0.35
EC_BG = "#2b3f63"


class FlatEyecatch(lk.Eyecatch):
    def __init__(self, t0, left, right, dur=4.0, lx=480, rx=1440):
        self.t0, self.dur = float(t0), float(dur)
        self.t1 = self.t0 + self.dur
        self.left, self.right = tuple(left), tuple(right)
        self.lx, self.rx = lx, rx
        self.pause = None
        self._sizes = {}
        for s in self.left + self.right:
            sz = min(60, int(60 * 820 / text_width(s, 60)))
            if sz < self.MIN_TEXT:
                raise ValueError(f"区切りの文字が{sz}px になる: {s!r}")
            self._sizes[s] = sz

    def _page(self, ctx, t, cx, head, lines, back):
        a = ease_out(clamp01((t - self.t0) / 0.5))
        text(ctx, head, cx, 230, 100, YEL, alpha=a)
        pr = clamp01((t - self.t0 - 0.1) / 0.4)
        x0, x1 = (cx + 210, cx - 230) if back else (cx - 210, cx + 230)
        if pr > 0:
            arrow2(ctx, (x0, 340), (lerp(x0, x1, pr), 340), REDC, 9, a, head=26)
        for i, s_ in enumerate(lines):
            text(ctx, s_, cx, 470 + i * 92, self._sizes[s_], WHITE, alpha=a)

    def _scene(self, ctx, t):
        paint_bg(ctx, EC_BG)
        fill(ctx, hexrgb("#ffffff", 0.18))
        ctx.rectangle(958, 60, 4, 820)
        ctx.fill()
        self._page(ctx, t, self.lx, "ここまで", self.left, True)
        self._page(ctx, t, self.rx, "ここから", self.right, False)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:                                      # 泡（小さなサケの後ろにできる）
                ctx.set_source_rgba(1, 1, 1, 0.35 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, self.Y + 8 + (14 if i % 2 else -14), 7, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        tr = t - self.t0
        bob = 6 * math.sin(tr * 4.0)
        fish(ctx, x, self.Y - bob + 6, 230, FISHC, "adult", tr * 2.2, 1)


EC = FlatEyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None


# ============================================================
# 場面を並べる
# ============================================================
SC_END = {}


def _start_of(spec):
    if spec == "zero":
        return 0.0
    if spec == "end":
        return T_ES
    if spec.startswith("ch:"):
        n = int(spec[3:])
        return ch_start(n) + (0.5 if n < LAST_CH else T_TITLE[n])
    if spec.startswith("z:"):
        return bz(spec[2:])
    return bd(spec)


def _end_of(j):
    name, spec, _f = SC_TABLE[j]
    if name == "end":
        return DUR + 2.0
    nname, nspec, _ = SC_TABLE[j + 1]
    if name == "c3_ans":
        return T_RS0 - 0.3
    if nspec.startswith("ch:"):
        return ch_start(int(nspec[3:])) - 0.3
    return _start_of(nspec)


for _j, (_nm, _spec, _fn) in enumerate(SC_TABLE):
    SC_END[_nm] = _end_of(_j)
for _j, (_nm, _spec, _fn) in enumerate(SC_TABLE):
    scene(_nm, _start_of(_spec), _end_of(_j), globals().get(_fn, lambda c, t: None), first=(_nm == "open"))


def draw(ctx, t, sub=True):
    paint_bg(ctx, BASE_BG)
    ea = EC.alpha(t) if (EC and T_RS0 <= t < T_RS1) else 0.0
    if ea < 0.5:
        draw_scenes(ctx, t)
        overlays(ctx, t)
    if ea > 0.003:
        EC.draw(ctx, t)
    if sub:
        lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・結果の数字・区切りの泡）
# ============================================================
def bubble_pop(seed=0, high=False):
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    return tone * env * 0.8


BELLS = [Sk("c0_res", 0.58), Sk("c2_med82", 0.55), Sk("c3_364", 0.55), Sk("c4_64", 0.5), Sk("c5_19", 0.5)]


BGM_FILE = ROOT / "assets" / "bgm" / "kasumisou.mp3"    # 2026-11-06 ユーザーが決定。めでたしかめのロングの標準（甘茶の音楽工房・リポジトリに入れない）
BGM_RMS = 0.045         # 声が止まっている所の BGM の大きさ。声の間は mixer が -10dB 下げる（声 0.12 より約18dB下）


def bgm_track(duration):
    """曲をくり返して duration 秒にする。つなぎ目は2秒重ね、大きさをそろえる"""
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(BGM_FILE), "-ac", "1", "-ar", str(lf.SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    n, xf = int(duration * lf.SR) + lf.SR, 2 * lf.SR
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
    t = np.arange(n) / lf.SR
    out *= np.clip(t / 1.0, 0, 1) * np.clip((duration - t) / 2.5, 0, 1)
    return out


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, bgm_track(DUR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for n in range(1, LAST_CH + 1):
        mx.add(S(f"ch{n}"), whoosh(0.6), 0.3)
    if EC:
        for i_, ts_ in enumerate(EC.step_times()):
            mx.add(ts_, bubble_pop(seed=i_, high=bool(i_ % 2)), 0.32)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(Sk("c6_3", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(Sk("c6_sub", 0.0) + 0.2, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（要所6枚）
# ============================================================
def still_list():
    return [
        ("1_c0_res", "① 冒頭: 中央値 約80匹", T_CARD0 + 2.0),
        ("2_c2_nb", "② 問い1: あなたは、たぶん", Sk("c2_nb", 0.7)),
        ("3_c2_bars", "③ 問い1: 関門ごとの棒", Sk("c2_hon", 0.7)),
        ("4_c4_bars", "④ 問い3: 29年分の棒", Sk("c4_64", 0.9)),
        ("5_c5_table", "⑤ 問い4: 約3分の1", Sk("c5_dir", 0.9)),
        ("6_c2_net", "⑥ 網の場面: 3つの行き先", Sk("c2_sum", 0.8)),
    ]


def _ts(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_sheet(out_dir, items, thumb=(480, 270), cols=3, sheet_name="stills_480.png"):
    """静止画を 1920×1080 で書き出し、480px 幅の一覧を作る（古い静止画は消さずに上書き）"""
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for nm, _lab, tt in items:
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}  {_lab}")
    W2, H2 = thumb
    lab_h, pad = 34, 10
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W2 + pad), pad + rows * (H2 + lab_h + pad)), (40, 40, 40))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", 17)
    except Exception:
        fnt = ImageFont.load_default()
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W2, H2), Image.LANCZOS)
        x, y = pad + (k % cols) * (W2 + pad), pad + (k // cols) * (H2 + lab_h + pad)
        dr.text((x + 4, y + 4), f"{_ts(items[k][2])}  {items[k][1]}", fill=(255, 225, 120), font=fnt)
        sheet.paste(im, (x, y + lab_h))
    sheet.save(out_dir.parent / sheet_name)
    print("一覧:", out_dir.parent / sheet_name)


def body_sheet():
    """本編の静止画一覧: 全場面（20秒を超える場面は途中のコマも）を 480px 幅で並べる。out/salmon-long/body_stills_480.png と16枚割りの p1〜"""
    from PIL import Image, ImageDraw, ImageFont
    d = WORK / "body"
    d.mkdir(parents=True, exist_ok=True)
    items = []
    for nm, t0, t1, *_r in SCENES:
        if nm == "end":
            items.append((nm, DUR - 1.0))
            continue
        n_mid = int((t1 - t0) // 8)
        for q in range(1, n_mid + 1):
            items.append((f"{nm}・{q}", t0 + (t1 - t0) * q / (n_mid + 1)))
        items.append((nm, t1 - 0.4))
    fnt = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", 17)
    cols, tw, th, lab = 4, 480, 270, 26
    cells = []
    for k, (nm, tt) in enumerate(items):
        p_ = d / f"{k:03d}_{nm}.png"
        lf.still(draw, tt, p_)
        cells.append((f"{_ts(tt)} {nm}", Image.open(p_).convert("RGB").resize((tw, th), Image.LANCZOS)))

    def sheet(sub, path):
        rows = (len(sub) + cols - 1) // cols
        sh = Image.new("RGB", (8 + cols * (tw + 8), 8 + rows * (th + lab + 8)), (40, 40, 40))
        dr = ImageDraw.Draw(sh)
        for k, (cap, im) in enumerate(sub):
            x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + lab + 8)
            dr.text((x + 4, y + 2), cap, fill=(255, 225, 120), font=fnt)
            sh.paste(im, (x, y + lab))
        sh.save(path)
        print("一覧:", path)
    sheet(cells, OUT / "body_stills_480.png")
    for p_i, i0 in enumerate(range(0, len(cells), 12)):
        sheet(cells[i0:i0 + 12], OUT / f"body_stills_480_p{p_i + 1}.png")


def write_voice_md(path):
    rows = ["## 0 声に渡した文（読みの補正つき。sims/salmon-long.py --voicemd が出力）"]
    for it in tl.items:
        if isinstance(it, lf.Line):
            rows.append("- " + it.text)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("声に渡した文:", path)


def _screen_texts():
    import pickle
    pk = (WORK / "frames.pkl") if FAKE else (OUT / "frames_real.pkl")
    if not pk.exists():
        return {}
    frames = pickle.loads(pk.read_bytes())
    ids = [it.id for it in tl.items if isinstance(it, (lf.Line, lf.Gap))]
    starts = [S(i) for i in ids]
    out, seen = {}, set()
    for t, ents in frames:
        cur = set()
        for e in ents:
            s_ = e[0]
            if s_.startswith("字幕: ") or s_ == "":
                continue
            cur.add(s_)
            if s_ not in seen:
                seen.add(s_)
                k = max(0, np.searchsorted(starts, t, side="right") - 1)
                if t > E(ids[k]) and k + 1 < len(ids):
                    k += 1
                out.setdefault(ids[k], []).append(s_)
        seen &= cur
    return out


def write_transcript(path):
    scr = _screen_texts()
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            rows.append(f"[章「{it.title}」]" if it.id == "ch0" else f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            txts = scr.get(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE.get(it.id, '映像だけ')}）" + (f"  〔画面の文字: {'／'.join(txts)}〕" if txts else ""))
        else:
            nt = LINE_NOTE.get(it.id)
            txts = scr.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else "")
                        + (f"  〔画面の文字: {'／'.join(txts)}〕" if txts else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


WATCH = ["砂利", "稚魚", "千歳川", "回帰率", "放流", "沿岸", "中央値", "産卵", "1万粒", "3,000粒", "北の海", "1999年", "2013年", "2,000匹", "8,751匹"]


def write_readings(path):
    from engine import voice
    real = (not FAKE) or ("--real-readings" in sys.argv)
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    rows.append("")
    rows.append("■ 読みが割れそうな語（{表記|よみ} があるか・声の文のどこに出るか）")
    for w in WATCH:
        hits = []
        for it in tl.items:
            if isinstance(it, lf.Line) and w in split_reading(it.text)[0]:
                m = _re.search(r"\{" + _re.escape(w) + r"\|([^{}]*)\}", it.text)
                hits.append(f"{it.id}({'よみ: ' + m.group(1) if m else 'よみ指定なし'})")
        rows.append(f"  {w}: " + ("、".join(hits) if hits else "声には出ない（画面の札だけ）"))
    rows.append("")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            reading = "\n    → " + voice.read_aloud(spoken) if real else ""
            rows.append(f"{it.id}: {shown_}" + (f"\n    （声に渡す字: {spoken}）" if spoken != shown_ else "") + reading)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


# ============================================================
# 絵の出る時刻の記録（visual_lag 用）: 枠は声の0.5秒前までに・答えの数字は声に合わせる
# ============================================================
def rd(scene_name, own_t, d):
    return max(SC_START[scene_name] + SC_DELAY + SC_IN, own_t + d)


def _fr(name, scene_nm, key, d=0.0):
    t0 = SC_START[scene_nm]
    return lk.Cue(name, "frame", t0, rd(scene_nm, t0, d), ID[key])


def _val(name, key, frac, off=0.0):
    t0 = Sk(key, frac) + off
    return lk.Cue(name, "value", t0, t0 + 0.3, ID[key])


ALL_CUES = [
    _val("札「中央値 約80匹」", "c0_res", 0.58),
    _val("札「34〜116匹」", "c2_med82", 0.8), _val("箱「中央値 82匹」", "c2_med82", 0.55),
    _fr("1万回の山の枠", "c2_f", "c2_med82"), _val("印「最少 10匹」", "c2_worst", 0.1), _val("印「最多 177匹」", "c2_best", 0.1),
    _fr("4つの関門の棒の枠", "c2_j", "c2_where"), _val("棒「80%」", "c2_b1", 0.65), _val("棒「約19%」", "c2_b2", 0.7),
    _fr("ふ化場の山の枠", "c3_e", "c3_364"), _val("箱「中央値 364匹」", "c3_364", 0.55),
    _fr("29年分の棒グラフの枠", "c4_bars", "c4_notenough"), _val("札「1999年級 7.15%」", "c4_high", 0.1), _val("札「約6.4倍」", "c4_64", 0.1),
    _fr("表の枠（卵の生き残り）", "c5_table", "c5_split"), _val("札「約3分の1に」", "c5_19", 0.2),
]


# ============================================================
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
WARNS = []
SCENE_MIN = 3.0
STILL_MAX = 15.0
STILL_THR = 0.005


def _allowed_nums():
    md = NARR_PATH.read_text(encoding="utf-8")
    md = md[md.index("## 0"):]
    ok = {float(m.replace(",", "")) for m in _re.findall(NUM_RE, md)}
    ok |= set(float(x) for x in range(0, 61))                      # 関門の番号・年ごとの棒の目盛り
    ok |= {100.0, 150.0, 200.0, 400.0, 600.0, 5.0, 87.5, 12.5, 2000.0, 8751.0, 4.7, 29.8}   # 軸の目盛り・凡例
    ok |= {float(y) for y in YEARS}
    ok |= {float(v) for v in YEARS.values()}
    ok |= {float(Q4[k][g]["mean"]) for k in ("20", "10", "5") for g in ("old", "new")}
    return ok


def first_seen(frames, pred):
    for f in frames:
        if any(pred(e[0], e) for e in f[1]):
            return f[0]
    return None


def motion_first_03():
    out = []
    for tt in (0.0, 0.3):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 960, 540)
        core._CUR_T = tt
        ctx = cairo.Context(surf)
        ctx.scale(0.5, 0.5)
        core._LOG = None
        draw(ctx, tt)
        surf.flush()
        out.append(np.frombuffer(bytes(surf.get_data()), np.uint8).astype(np.int16))
    return float(np.mean(np.abs(out[0] - out[1]) > 8))


def _check_long_mod():
    import importlib.util
    if not (Path(__file__).resolve().parent / "check-long.py").exists():
        print("  （sims/check-long.py が無いので、札の表示時間の点検だけ飛ばします）")
        return None
    spec = importlib.util.spec_from_file_location("check_long", Path(__file__).resolve().parent / "check-long.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pace_problems():
    short, mid_ = [], []
    lines_ = [(S(i), E(i), i) for i in LINES]
    for nm_, t0_, t1_, *_r in SCENES:
        if t1_ - t0_ < SCENE_MIN - 1e-6:
            short.append(f"{nm_} {_ts(t0_)} {t1_ - t0_:.1f}秒")
        if t1_ >= DUR:
            continue
        for a_, b_, i_ in lines_:
            if a_ < t1_ < b_ - 0.01:
                mid_.append(f"{nm_}→ {_ts(t1_)}（文 {i_} は {_ts(b_)} まで）")
    return short, mid_


def still_spans(step=0.5, scale=0.25, thr=STILL_THR):
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    saved = core._LOG, core._CUR_T
    spans, ref, t_ref = [], None, 0.0
    try:
        for i in range(int(DUR / step) + 1):
            t = i * step
            core._LOG = None
            core._CUR_T = t
            ctx = cairo.Context(surf)
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
            ctx.scale(scale, scale)
            draw(ctx, t, sub=False)
            surf.flush()
            img = np.frombuffer(bytes(surf.get_data()), np.uint8).reshape(h, -1, 4)[:, :w, :3].astype(np.int16)
            if ref is None:
                ref, t_ref = img, t
                continue
            if np.mean(np.abs(img - ref).max(axis=2) > 8) >= thr:
                spans.append((t_ref, t))
                ref, t_ref = img, t
        spans.append((t_ref, DUR))
    finally:
        core._LOG, core._CUR_T = saved
    return sorted(spans, key=lambda s_: s_[0] - s_[1])


def _bbox_h(kind, L):
    """draw_fish の体の高さ（背びれの先から胸びれの先まで）の目安"""
    return L * (0.40 if kind == "fry" else 0.30) * 1.46


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本 ----
    A(f"台本: 章は7つ（0〜6）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 7 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない・読みの補正は空（台本の {表記|よみ} を使う）", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()) and not READ_FIX)
    A(f"題字「{''.join(QROWS)}」は第0章の題名「{CH_TITLES[0]}」と同じ言葉", "".join(QROWS).replace("？", "") == CH_TITLES[0])
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S("c0_0"), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:])]
    A(f"台本: 冒頭（第0章）の文と文の間は 0.3秒（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし", all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch1"))
    sil = [(g, GAP_SEC[g]) for g in GAP_NOTE]
    A(f"台本: 無音はどこも10秒以内（{sil}）", all(v <= 10 for _g, v in sil))
    gaps_all = []
    its = [it for it in tl.items if isinstance(it, lf.Line)]
    for a_, b_ in zip(its, its[1:]):
        gaps_all.append((S(b_.id) - E(a_.id), a_.id))
    A(f"台本: 声と声の間（章の切りかえ・区切りを含む）は最長 {max(gaps_all)[0]:.1f}秒（10秒以内）", max(gaps_all)[0] <= 10.0)
    # ---- 区切り ----
    n_rest = len(REST)
    A(f"区切り: 「（無音 4秒・区切り。…）」は {n_rest} か所・長さ {T_RS1 - T_RS0:.1f}秒", n_rest == 1 and abs((T_RS1 - T_RS0) - 4.0) < 0.01)
    last3 = [i for i in LINES if LINES[i][0] == 3][-1]
    A(f"区切り: 問い2（第3章）のあと・問い3（第4章）の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(last3) - 1e-6 and abs(T_RS1 - S("ch4")) < 1e-6 and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    pos = (T_RS0 + T_RS1) / 2 / DUR
    A(f"区切り: 動画の {pos:.1%} のところ（35〜75%）・声の行なし", 0.35 <= pos <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 小さなサケは左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ泳ぐ・泡の音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    # ---- 冒頭 ----
    nums0 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and it.id.startswith("c0_"):
            s0 = _re.sub(r"\d+年", "", split_reading(it.text)[0])
            nums0 |= set(_re.findall(r"\d[\d,]*", s0))
    A(f"台本: 冒頭（第0章）の声の数字は3個以内・年の名前は数えない（{sorted(nums0)}）", len(nums0) <= 3)
    t80 = Sk("c0_res", 0.58)
    A(f"冒頭の結果の数字（約80匹）を言うのは約 {t80:.1f}秒（文の頭 {Sk('c0_res'):.1f}秒。本番の声は30秒以内）", t80 <= (29.5 if FAKE else 30.0))
    # ---- 声の数字 = data.json ----
    q20, q5 = Q1["20"], Q1["5"]
    exp = [("c0_res", "約80匹"), ("c2_chitose", "8,000粒"), ("c2_med82", f"{ihalf(q20['back']['median'])}匹"), ("c2_worst", f"{ihalf(q20['back']['min'])}匹"),
           ("c2_best", f"{ihalf(q20['back']['max'])}匹"), ("c2_10", f"{ihalf(q20['trap']['median'])}匹"), ("c3_875", "8,750粒"), ("c3_589", f"{ihalf(Q2['winter']['median'])}匹"),
           ("c3_364", f"{ihalf(Q2['back']['median'])}匹"), ("c3_cmp", f"{ihalf(Q2['x_low'])}倍以上"),
           ("c4_7", f"{ihalf(YEARS[1999])}匹あまり"), ("c4_1", f"{ihalf(YEARS[2013])}匹ほど"), ("c4_64", f"約{TAB['ratio']}倍"),
           ("c4_143", f"{Q3['per_year']['1999']['river']}匹"), ("c4_22", f"{Q3['per_year']['2013']['river']}匹"),
           ("c5_24", f"約{ihalf(Q4['20']['all']['mean'])}匹"), ("c5_table", f"約{ihalf(Q4['20']['old']['mean'])}匹"),
           ("c5_10", f"約{ihalf(Q4['20']['new']['mean'])}匹")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in split_reading(txt(k))[0]]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A(f"data.json: 約80匹は 平均 {q20['back']['mean']}・中央値 {q20['back']['median']}（幅 約{ihalf(q5['back']['median'])}〜{ihalf(q20['back']['median'])}匹）・ふ化場の差 {Q2['x_low']}〜{Q2['x_high']}倍・回帰率の差 {TAB['ratio']}倍",
      abs(q20["back"]["mean"] - 80) < 2.5 and q5["back"]["median"] == 20.0 and Q2["x_low"] == 4.4 and Q2["x_high"] == 17.5 and TAB["ratio"] == 6.4)
    A(f"data.json: 1粒の終点 {q20['ends']}（合計 {round(q20['ends']['関門1で'] + q20['ends']['関門2で'] + q20['ends']['関門3で'] + q20['ends']['帰ってくる'], 2)}）が棒の値と同じ",
      [v for _n, v, _t in BAR_ROWS] == [q20["ends"]["関門1で"], q20["ends"]["関門2で"], q20["ends"]["関門3で"], q20["ends"]["帰ってくる"]]
      and abs(q20["ends"]["関門1で"] + q20["ends"]["関門2で"] + q20["ends"]["関門3で"] + q20["ends"]["帰ってくる"] - 100) < 0.02)
    # ---- 場面のデータ（模型と同じ関数・同じ種）----
    A(f"1万回の再現（川生まれ）: 中央値 {np.median(BACK_R):.0f}・最少 {BACK_R.min()}・最多 {BACK_R.max()}・10%点 {np.percentile(BACK_R, 10):.0f}・90%点 {np.percentile(BACK_R, 90):.0f} が data.json と同じ",
      np.median(BACK_R) == q20["back"]["median"] and BACK_R.min() == q20["back"]["min"] and BACK_R.max() == q20["back"]["max"]
      and np.percentile(BACK_R, 10) == q20["back"]["p10"] and np.percentile(BACK_R, 90) == q20["back"]["p90"])
    A(f"1万回の再現（ふ化場）: 中央値 {np.median(BACK_H):.0f}・10%点 {np.percentile(BACK_H, 10):.0f}・90%点 {np.percentile(BACK_H, 90):.0f} が data.json と同じ",
      np.median(BACK_H) == Q2["back"]["median"] and np.percentile(BACK_H, 10) == Q2["back"]["p10"] and np.percentile(BACK_H, 90) == Q2["back"]["p90"])
    A(f"絵の数: 1粒＝100粒の卵 {BED10.n}・{B_BED.n}・{BED10.n} ／ 1匹＝10匹の稚魚 {FRY200.n}（2000匹）・1匹＝1匹 {FRY133.n}（133匹）・{SEA133.n}・{FISH80.n}（約80匹）・{TEN10.n}（10匹）",
      BED10.n == 100 and B_BED.n == 100 and FRY200.n == 200 and FRY133.n == 133 and SEA133.n == 133 and FISH80.n == 80 and TEN10.n == 10 and HATCH88.n == 88 and HAT59.n == 59 and RIV13.n == 13 and MOM24.n == 24)
    A(f"年ごとの棒: 29年分（{YEARS_L[0]}〜{YEARS_L[-1]}）・最高 {max(YEARS.values())}%（{TAB['best_year']}）・最低 {min(YEARS.values())}%（{TAB['worst_year']}）・差 {max(YEARS.values()) / min(YEARS.values()):.1f}倍",
      len(YEARS_L) == 29 and max(YEARS, key=YEARS.get) == TAB["best_year"] and min(YEARS, key=YEARS.get) == TAB["worst_year"] and round(max(YEARS.values()) / min(YEARS.values()), 1) == 6.4)
    r3 = [round(Q4[k]["new"]["mean"] / Q4[k]["old"]["mean"], 2) for k in ("20", "10", "5")]
    A(f"近年 ÷ 昔 は 卵の生き残りを変えても同じで 約3分の1: {r3}", all(0.33 <= x <= 0.38 for x in r3) and max(r3) - min(r3) < 0.01)
    A(f"表の数字: {TBL} が data.json（昔の年・近年の年・必要な割合）", TBL[0] == ("20%", "28.8匹", "10.4匹", "約7%", "約19%") and TBL[1][1:] == ("14.4匹", "5.2匹", "約14%", "約39%") and TBL[2][1:] == ("7.2匹", "2.6匹", "約28%", "約77%"))
    A(f"主役の大きさ: あなたの卵 直径 {2 * YOU_EGG_R}px・稚魚 高さ {_bbox_h('fry', YOU_FRY_L):.0f}px・成魚 高さ {_bbox_h('adult', YOU_ADULT_L):.0f}px・冒頭の卵 {2 * OPEN_R}px は 画面の高さの3分の1（{lf.H / 3:.0f}px）以上",
      min(2 * YOU_EGG_R, _bbox_h("fry", YOU_FRY_L), _bbox_h("adult", YOU_ADULT_L), 2 * OPEN_R) >= lf.H / 3)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件 {[b[0] for b in bad[:4]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面の切りかえ: 文の途中で場面が替わらない（{mid_sc[:3]}）", not mid_sc)
    A(f"グラフ: 棒・柱は 1本ずつ 0.28秒・0.26秒おき（0.25秒以上）", 0.28 >= 0.25 and BAR_DT >= 0.25)
    A(f"章カード: 文字数÷8＋1秒 以上出る（{[(n, round(len(''.join(v)) / 8 + 1, 1), round(CARD_HOLD[n], 1)) for n, v in CARD_BY_N.items()]}）",
      all(CARD_HOLD[n] - 0.4 >= len("".join(v)) / 8 + 1 for n, v in CARD_BY_N.items()))
    if frames is not None:
        sp_ = still_spans()
        long_ = [f"{_ts(a_)}〜{_ts(b_)}（{b_ - a_:.1f}秒）" for a_, b_ in sp_ if b_ - a_ > STILL_MAX + 1e-6]
        print(f"  同じ絵の長い区間: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:6]))
        A(f"同じ絵は{STILL_MAX:.0f}秒まで（最長 {sp_[0][1] - sp_[0][0]:.1f}秒）: 超える区間 {long_}", not long_)
        long10 = [f"{_ts(a_)}〜{_ts(b_)}（{b_ - a_:.1f}秒）" for a_, b_ in sp_ if b_ - a_ > 10.0 + 1e-6]
        A(f"10秒に1回は何かが動く（画面の{STILL_THR:.1%}以上が変わる）: 10秒を超えて止まる区間 {long10}", not long10)
        allt = [(f[0], e) for f in frames for e in f[1]]

        def _pad_card(fr_):
            cd_ = [e for e in fr_[1] if e[0] in CARD_LINES and e[5] >= 70]
            if not cd_:
                return fr_
            box_ = ("章カード", min(e[1] for e in cd_) - 60, min(e[2] for e in cd_) - 34, max(e[3] for e in cd_) + 60, max(e[4] for e in cd_) + 34, cd_[0][5])
            return (fr_[0], [e for e in fr_[1] if e not in cd_] + [box_], *fr_[2:])
        pairs = lk.text_box_overlaps([_pad_card(f_) for f_ in frames], skip=[(T_ES, T_ES + 0.6)])
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）。章カードも板ごと数えた"])
        for a_, b_, x, y in spans[:16]:
            print(f"  文字の交わり {_ts(a_)}〜{_ts(b_)} 「{x}」と「{y}」")
        A(f"文字の箱の交わり（章カード・字幕・札・図の文字・全コマ）: {len(spans)} 組・{len(pairs)} コマ（期待 0）", not spans)
        small = lk.min_text_size(frames, 40, exempt=lambda s_: s_ in CARD_LINES or s_.startswith("字幕: "))
        for t_, lab, sz in small[:8]:
            print(f"  40px未満 {_ts(t_)} 「{lab}」 {sz:.0f}px")
        A(f"文字の大きさ: 40px 未満 {len(small)} 種（幅480pxに縮めても約10px）", not small)
        edge = lk.outside_area(frames, skip=[(T_ES, T_ES + 0.6)])
        for t_, lab, bx in edge[:8]:
            print(f"  画面の端 {_ts(t_)} 「{lab}」 {bx}")
        A(f"画面の端（x 48〜1872・y 36〜1044）に近い文字: {len(edge)} 件", not edge)
        onsub = sorted({(e[0], round(f[0], 1)) for f in frames if any(x[0].startswith("字幕: ") for x in f[1]) for e in f[1]
                        if not e[0].startswith("字幕: ") and e[4] > 936 and e[0] not in EC.texts()})
        for lab, t_ in onsub[:6]:
            print(f"  字幕の帯に重なる札 {_ts(t_)} 「{lab}」")
        A(f"字幕の帯（画面下 y 936〜）に札・図の文字を重ねない: {len(onsub)} 件", not onsub)
        f0 = next(f for f in frames if abs(f[0]) < 1e-6)
        q0 = [e for e in f0[1] if e[0] in QROWS]
        A(f"冒頭: 0秒目に問い「{' '.join(QROWS)}」が {min((e[5] for e in q0), default=0):.0f}px（90px 以上）で出ている", len(q0) == 2 and min(e[5] for e in q0) >= 90)
        A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
        tokens = [("中央値 約80匹", "c0_res"), ("82匹", "c2_med82"), ("最少 10匹", "c2_worst"), ("最多 177匹", "c2_best"), ("中央値 10匹", "c2_10"), ("589匹", "c3_589"),
                  ("364匹", "c3_364"), ("約6.4倍", "c4_64"), ("143匹", "c4_143"), ("22匹", "c4_22"), ("10.4匹", "c5_table"), ("平均 約24匹", "c5_24"), ("約3分の1に", "c5_19")]
        for tok, key in tokens:
            n_ = LINES[ID[key]][0]
            fr_ch = [f for f in frames if S(f"ch{n_}") <= f[0]]
            ft = first_seen(fr_ch, lambda s_, e, tok=tok: s_ == tok)
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        ok_ = _allowed_nums()
        extra = {}
        for t_, e in allt:
            lab = e[0]
            if lab.startswith("字幕: ") or lab in CARD_LINES:
                continue
            for m in _re.finditer(NUM_RE, lab):
                v = float(m.group(0).replace(",", ""))
                if v not in ok_:
                    extra.setdefault(m.group(0), (lab, t_))
        for v, (s_, t_) in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が台本・data.json の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて台本（札の指示を含む）か data.json の値: 余分 {len(extra)}個 {list(extra)[:5]}", not extra)
        bad_words = sorted({e[0] for t_, e in allt if any(w in e[0] for w in ("円", "死骸", "食べられ", "もがく"))})
        A(f"画面に「死骸」「食べられる」「もがく」などの文字を出さない（食べられる場面・死骸・もがく絵は描かない）: {bad_words}", not bad_words)
        _cl = _check_long_mod()
        short_t = _cl.short_texts(frames) if _cl else []
        for a_, b_, s_, need_ in short_t[:16]:
            print(f"  札の表示時間 {_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒／要 {need_:.1f}秒 「{s_[:30]}」")
        A(f"札の表示時間: 画面の文字は「文字数÷8＋1秒」以上出る（字幕・カウンターは除く）: 足りない {len(short_t)} 件", not short_t)
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、区切りの文字だけ: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        tes = T_ES + 0.6
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        A(f"終了画面: 登録のお願い（{Sk('c6_sub'):.1f}秒〜）の{Sk('c6_sub') - T_ES:.1f}秒前から最後まで（{DUR - T_ES:.1f}秒・6〜8秒）",
          0.2 <= Sk("c6_sub") - T_ES <= 1.0 and 6.0 <= DUR - T_ES <= 8.0 and T_ES > Ek("c6_4") - 1e-6)
        end_t = min(DUR - 0.2, Sk("c6_sub") + 1.5)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A(f"終了画面に 答え3つ・登録の札が出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
    flat_ = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat_)
    print(f"場面の照合 {len(flat_)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat_)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if "--motion" in args:
        sp_ = still_spans()
        print("同じ絵の長い区間: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:14]))
        return
    if not any(a in args for a in ("--anchors", "--readings", "--scenecheck", "--stills", "--preview", "--docs", "--lines", "--sheet", "--voicemd")) and FAKE:
        print(__doc__)
        return
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    print(f"  約80匹を言う: {Sk('c0_res', 0.58):.1f}秒（文 {Sk('c0_res'):.1f}〜{Ek('c0_res'):.1f}秒）・区切り {_ts(T_RS0)}〜{_ts(T_RS1)}（{(T_RS0 + T_RS1) / 2 / DUR:.1%}）")
    if "--anchors" in args or "--lines" in args:
        for k_ in ID:
            print(k_, ID[k_], f"{Sk(k_):.1f}-{Ek(k_):.1f}")
        for nm_, t0_, t1_, *_r in SCENES:
            print(f"場面 {nm_}: {t0_:.1f}-{t1_:.1f}（{t1_ - t0_:.1f}秒）")
        return
    if "--readings" in args:
        write_readings((WORK if FAKE else OUT) / "readings.log")
        return
    if "--scenecheck" in args:
        import pickle
        pk = WORK / "frames.pkl"
        if "--cached" in args and pk.exists():
            frames = pickle.loads(pk.read_bytes())
        else:
            frames = lk.scan_frames(draw, DUR, timeline=tl)
            pk.write_bytes(pickle.dumps(frames))
            if not FAKE:
                (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, WORK / f"at_{tt:06.1f}.png")
                print("  ", WORK / f"at_{tt:06.1f}.png")
        else:
            stills_sheet(OUT / "stills", still_list())
        return
    if "--sheet" in args:
        body_sheet()
        return
    if "--voicemd" in args:
        write_voice_md((WORK if FAKE else OUT) / "narration_voice.md")
        return
    if "--preview" in args:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
        return
    if "--docs" in args:
        d = WORK if FAKE else OUT
        write_transcript(d / "transcript.long.txt")
        write_readings(d / "readings.log")
        (d / "chapters.txt").write_text(tl.chapter_text() + "\n", encoding="utf-8")
        print("チャプター:", d / "chapters.txt")
        return
    if FAKE:
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから（この段階ではまだしない）")
    import pickle
    frames = lk.scan_frames(draw, DUR, timeline=tl)
    (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))
    scene_checks(frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
