"""ツバメの一生ロング「ツバメの一生を1万回」（横型ロング）— 2026-11-08 作成。場面（描画・声の並び・照合・静止画）。

  python -X utf8 sims/tsubame-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/tsubame-long.py --fake-voice --stills         要所の静止画8枚と 480px の一覧（out/tsubame-long/stills/・stills_key_480.png）
  python -X utf8 sims/tsubame-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/tsubame-long/scene_work/）
  python -X utf8 sims/tsubame-long.py --fake-voice --sheet          本編の全場面の静止画一覧（out/tsubame-long/body_stills_480*.png）
  python -X utf8 sims/tsubame-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/tsubame-long.py --scenecheck                  本番の声で照合（frames_real.pkl を保存）
  python -X utf8 sims/tsubame-long.py --figcheck                    字幕の帯と鳥の足もとのかぶりを全コマで数える
  python -X utf8 sims/tsubame-long.py --readings                    声の読み（readings.log）

台本: publish/tsubame-long/narration_B.md（文は変えない）。数字: sims/tsubame_rough.py を同じ乱数の種（20261108）で回した値（手で書き写さない）。
絵: sims/tsubame_art.py（平塗り・輪郭線なし。地図は Natural Earth の実データ）。仕組みは sims/whaling-long.py と同じ。
本番の mp4 の書き出しはここでは行わない（--scenecheck と --stills・--sheet まで）。
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

SLUG = "tsubame-long"
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

from danchi_people import mix  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAKE = "--fake-voice" in sys.argv
# 場面の切りかえの前後の間（2026-11-08 ユーザー「その間でOK」で標準。--pace-old で前の間に戻せる）
PACE_TRIAL = "--pace-old" not in sys.argv
TRIAL_LEAD = 0.7   # 場面が替わってから声まで
TRIAL_TAIL = 0.6   # 声が終わってから場面が替わるまで
TRIAL_CH = tuple(f"c{n}_" for n in range(0, 7))
# 第0章は 0.6＋0.4。枠（グラフ・帯・地図）が出そろうのに時間がかかる図は 1.05秒前から出す
TRIAL_PAIR = {"c0_": (0.6, 0.4), **{f"c{n}_": (TRIAL_LEAD, TRIAL_TAIL) for n in range(1, 7)}}
TRIAL_LEAD_KEY = {k_: 1.05 for k_ in (
    "c0_med", "c1_pie", "c1_band1", "c1_nofl", "c2_band", "c2_x2", "c2_sort", "c3_aki", "c3_band", "c3_cmp", "c3_count",
    "c4_base", "c4_sorted", "c4_vary", "c4_20", "c4_long", "c5_sel", "c5_worst0")}


def trial_lead(k_):
    return TRIAL_LEAD_KEY.get(k_, TRIAL_PAIR[k_[:3]][0])


def trial_gap(k_):
    return trial_lead(k_) + TRIAL_PAIR[k_[:3]][1]


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
END_HOLD = 7.0
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
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, safe_pauses=True, tail_fix=True, **kw)


lf.use()

_wrap_orig = lf.wrap_subtitle


def _wrap_kinsoku(s_, limit=lf.SUB_MAX):
    """行頭に「。」「、」が来ないよう、前の行の終わりにぶら下げる（文言は変えない）"""
    out = [x for x in _wrap_orig(s_, limit)]
    for i in range(1, len(out)):
        while out[i] and out[i][0] in "。、，．":
            out[i - 1] += out[i][0]
            out[i] = out[i][1:]
    return [x for x in out if x]


lf.wrap_subtitle = _wrap_kinsoku
# 2026-11-08 ユーザー「字幕を気持ち大きく」: 40→45px（+12.5%）。行の間も同じ割合で
lf.SUB_SIZE = 45
lf.SUB_LINE_H = 54
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

from long_bgm import bgm_track as _bgm  # noqa: E402  めでたしかめのロングの標準BGM（カスミソウ）
import tsubame_art as wa  # noqa: E402
import tsubame_rough as tr  # noqa: E402  試算（乱数の種 20261108）。画面の数字はここから取る

# ---- 鳥の足もとの記録（字幕の帯とのかぶりを機械で測る・2026-11-08）----
FIG_LOG = None
FEET_MAX = 925   # とまった鳥・ヒナの足もとはここより下に置かない（字幕2行の帯の上端は 934）


def _lift(ctx, x, y):
    """足もとが FEET_MAX より下なら、その分だけ上げた y を返す（体を一緒に上げるため、描く関数の入口で使う）"""
    dyv = ctx.user_to_device(x, y)[1]
    if dyv > FEET_MAX:
        y -= ctx.device_to_user_distance(0, dyv - FEET_MAX)[1]
    return y


def _logged(fn):
    def wrapped(ctx, x, y, h, *a_, **k_):
        if k_.get("pose", "perch") == "perch":
            y = _lift(ctx, x, y)
            if FIG_LOG is not None:
                dx, dy = ctx.user_to_device(x, y)
                dh = abs(ctx.user_to_device_distance(0, h)[1])
                FIG_LOG.append((dx, dy, dh))
        return fn(ctx, x, y, h, *a_, **k_)
    return wrapped


draw_swallow = _logged(wa.draw_swallow)
draw_chick = _logged(wa.draw_chick)
from tsubame_art import (draw_swallow_front, draw_crow, draw_egg, draw_nest, draw_snake, draw_sparrow_icon, egg_slots, nest_back, nest_front,  # noqa: E402
                         pole, window, wire, wire_y, MapView)


ANCH = {
    # 0 来年の春、何羽？
    "c0_q": (0, "まだ生きているのは何羽でしょうか"), "c0_pick": (0, "一つ選んでみてください"), "c0_ans3": (0, "問いで出します"),
    "c0_egg": (0, "1万個用意しました"), "c0_one": (0, "最後に、その1万個の中央値"), "c0_med": (0, "ちょうど真ん中のことです"), "c0_prob": (0, "記録にある確率を使って"),
    # 1 巣立てる？
    "c1_q": (1, "最初の問いです"), "c1_spring": (1, "春に日本に来る鳥です"), "c1_eave": (1, "秋に東南アジアへ渡ります"), "c1_pie": (1, "ほとんどが建物にあります"),
    "c1_6": (1, "巣の約6割です"), "c1_clutch": (1, "1回に産む卵は"), "c1_brood": (1, "約2週間温めます"), "c1_chicks": (1, "約3週間で巣立ちます"),
    "c1_fail0": (1, "巣ごとうまくいかないことがあります"), "c1_enemy": (1, "天敵です"), "c1_other": (1, "スズメに巣を乗っ取られたり"), "c1_band1": (1, "巣ごと失敗したのは2,165個"), "c1_one": (1, "無事な巣でも"), "c1_nofl": (1, "巣立てなかった卵は"),
    "c1_ans": (1, "巣立ったのは6,855羽"),
    # 2 巣立ちの後の3週間
    "c2_q": (2, "二つ目の問いです"), "c2_safe": (2, "もうひと安心だと思いますよね"), "c2_3wari": (2, "生き残るのは約3割でした"),
    "c2_radio": (2, "小さな発信機をつけて"), "c2_band": (2, "3週間を越えたのは2,137羽でした"),
    "c2_dead": (2, "4,718羽が"), "c2_x2": (2, "2倍以上多い数です"), "c2_most": (2, "いちばん多くのツバメが一生を終える"), "c2_sort": (2, "生きた日数の順に並べてみます"), "c2_half": (2, "合わせて半分を超えます"),
    "c2_where": (2, "どこで一生を終えるかは、最後にお見せします"), "c2_ans": (2, "答えです。巣立ったヒナのうち"), "c2_ans2": (2, "半分以上が、この3週間までに"),
    # 3 渡りと翌年の春
    "c3_q": (3, "来年の春まで生きられるでしょうか"), "c3_aki": (3, "秋になると、ツバメは東南アジアへ渡ります"), "c3_first": (3, "初めての渡りです"),
    "c3_ashiwa": (3, "フィリピンやインドネシアで見つかっています"), "c3_malay": (3, "マレーシアや、ベトナムの南部"), "c3_winter": (3, "冬を東南アジアで過ごします"), "c3_51": (3, "約51%です"), "c3_band": (3, "春まで生きたのは1,075羽でした"),
    "c3_cmp": (3, "3週間と、渡りと冬を比べます"), "c3_guess": (3, "危なそうに見えますよね"), "c3_4718": (3, "一生を終えたのは、4,718羽でした"),
    "c3_1062": (3, "一生を終えたのは、1,062羽です"), "c3_ratio": (3, "生き残る割合で見ても"), "c3_big": (3, "いちばん大きく減るのは"), "c3_back": (3, "では、最初の問いに戻ります"),
    "c3_again": (3, "5羽が巣立ちました"), "c3_six": (3, "約6羽に1羽です"), "c3_count": (3, "5羽巣立った巣で"), "c3_zero": (3, "1羽も生きていない巣で、43%でした"),
    "c3_nochoice": (3, "選択肢にはなかった"), "c3_rest": (3, "1羽の巣が40%"), "c3_med": (3, "中央値は1羽です"), "c3_two": (3, "5つに1つもありません"),
    # 4 春まで生きたツバメ
    "c4_q": (4, "どんな一生を送るでしょうか"), "c4_base": (4, "数える基準を変えます"), "c4_pull": (4, "春まで生きた1,075羽を並べます"), "c4_tenth": (4, "約1割です"),
    "c4_age": (4, "ふつう1歳から子育てをします"), "c4_twice": (4, "1年に2回が約8割"), "c4_decay": (4, "同じ確率で減っていきます"),
    "c4_adult": (4, "毎年の渡りと冬を越えなければなりません"), "c4_49": (4, "約49%"), "c4_sorted": (4, "生きた日数の順に並べました"), "c4_life": (4, "寿命の中央値は、約2年でした"),
    "c4_brood": (4, "子育てをした回数の中央値は、2回です"), "c4_kids": (4, "巣立たせたヒナの数の中央値は"), "c4_pair": (4, "オスにもメスにも9羽と数えています"),
    "c4_vary": (4, "ヒナの数は、ツバメによって大きく違いました"), "c4_zero": (4, "59羽、5%でした"), "c4_empty": (4, "ヒナが1羽も巣立たないことがあるのです"),
    "c4_20": (4, "20羽以上を巣立たせたツバメは"), "c4_max": (4, "つがいで56羽を巣立たせました"), "c4_gap": (4, "0羽から56羽まで開きます"),
    "c4_tickets": (4, "この開きは、1羽ずつ一生を進めて"), "c4_long": (4, "いちばん長生きしたツバメは、10.7年"), "c4_uk": (4, "約11年で"),
    "c4_half": (4, "半分は、約2年までに"), "c4_ans": (4, "答えです。春まで生きたツバメは"), "c4_ans2": (4, "子育ては2回で"),
    # 5 中央値の1羽の一生
    "c5_q": (5, "最後に、約束した"), "c5_8d": (5, "巣立って約8日目"),
    "c5_42": (5, "産卵から42日でした"), "c5_4718": (5, "4,718羽の中の1羽です"), "c5_autumn": (5, "渡りの季節を迎える前に"), "c5_worst0": (5, "最悪と最良も並べます"),
    "c5_worst": (5, "2,165個ありました"), "c5_best": (5, "10.7年生きた1羽と"), "c5_base2": (5, "また1,075羽に替わります"),
    "c5_pick2": (5, "子育てが2回、ヒナが9羽で"), "c5_end2": (5, "その秋からの渡りと冬の間に"), "c5_708": (5, "産卵から708日"),
    # 6 まとめ
    "c6_8d": (6, "巣立って約8日で一生を終えます"), "c6_2y": (6, "中央値で約2年を生き"),
    "c6_tenth": (6, "たどり着けたのは約1割です"), "c6_last": (6, "親のツバメは、その約1割の1羽です"),
    "c0_you": (0, "巣で生まれたツバメのヒナです"), "c0_bro": (0, "あなたを入れて5羽です"), "c0_out": (0, "空へ飛び出します"),
    "c1_fail": (1, "約2割あります"), "c2_lost": (2, "見つからなくなったヒナは"),
    "c5_sel": (5, "中央値にいちばん近い卵を選びます"), "c5_you": (5, "ここからは、あなたがその卵です"), "c5_nest": (5, "5個のうち3番目の卵です"),
    "c5_warm": (5, "親に温められて約2週間"), "c5_sib": (5, "殻を割ると、すぐ横に兄弟"), "c5_male": (5, "あなたはオスです"), "c5_feed": (5, "口を開けて待つと"),
    "c5_grow": (5, "約34日。巣のふちから"), "c5_fly": (5, "空へ飛び立ちます"), "c5_wire": (5, "電線にとまると"),
    "c5_b2": (5, "の中央値の1羽にも、なってみます"), "c5_noeave2": (5, "ではない所の巣で産まれます"), "c5_3rd": (5, "3個のうち3番目の卵で、オスです"),
    "c5_travel": (5, "秋には海の上を南へ飛びます"), "c5_winter": (5, "東南アジアの暖かい国で"), "c5_spring": (5, "日本に戻って、子育てを始めます"),
    "c5_kids2": (5, "1回目は4羽、2回目は5羽"), "c5_pair9": (5, "つがいで9羽です"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in split_reading(txt)[0]]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の並び（名前, 始まり, 描く関数の名前）。始まり: 合図のキー＝その文の頭の前 ／ "ch:N"＝章カードのあと ／ "z:キー"＝0章 ----
SC_TABLE = [
    ("open", "zero", "sc_open"), ("c0_egg", "z:c0_egg", "sc_c0_egg"), ("c0_one", "z:c0_one", "sc_c0_one"), ("c0_med", "z:c0_med", "sc_c0_med"),
    ("c0_prob", "z:c0_prob", "sc_c0_prob"),
    ("c1_a", "ch:1", "sc_c1_a"), ("c1_spring", "c1_spring", "sc_c1_spring"), ("c1_eave", "c1_eave", "sc_c1_eave"), ("c1_pie", "c1_pie", "sc_c1_pie"),
    ("c1_clutch", "c1_clutch", "sc_c1_clutch"), ("c1_brood", "c1_brood", "sc_c1_brood"), ("c1_chicks", "c1_chicks", "sc_c1_chicks"),
    ("c1_fail", "c1_fail0", "sc_c1_fail"), ("c1_enemy", "c1_enemy", "sc_c1_enemy"), ("c1_other", "c1_other", "sc_c1_other"),
    ("c1_band1", "c1_band1", "sc_c1_band1"), ("c1_one", "c1_one", "sc_c1_one"), ("c1_band2", "c1_nofl", "sc_c1_band2"),
    ("c2_a", "ch:2", "sc_c2_a"), ("c2_safe", "c2_safe", "sc_c2_safe"), ("c2_three", "c2_3wari", "sc_c2_three"), ("c2_radio", "c2_radio", "sc_c2_radio"),
    ("c2_band", "c2_band", "sc_c2_band"), ("c2_bars", "c2_x2", "sc_c2_bars"),
    ("c2_sort", "c2_sort", "sc_c2_sort"), ("c2_ans", "c2_ans", "sc_c2_ans"),
    ("c3_a", "ch:3", "sc_c3_a"), ("c3_map", "c3_aki", "sc_c3_map"), ("c3_swiss", "c3_51", "sc_c3_swiss"), ("c3_band", "c3_band", "sc_c3_band"),
    ("c3_cmp", "c3_cmp", "sc_c3_cmp"), ("c3_back", "c3_back", "sc_c3_back"), ("c3_six", "c3_six", "sc_c3_six"), ("c3_dist", "c3_count", "sc_c3_dist"),
    ("c4_a", "ch:4", "sc_c4_a"), ("c4_base", "c4_base", "sc_c4_base"), ("c4_start", "c4_age", "sc_c4_start"), ("c4_decay", "c4_decay", "sc_c4_decay"),
    ("c4_adult", "c4_adult", "sc_c4_adult"), ("c4_band", "c4_sorted", "sc_c4_band"), ("c4_hist", "c4_vary", "sc_c4_hist"), ("c4_empty", "c4_empty", "sc_c4_empty"),
    ("c4_hist2", "c4_20", "sc_c4_hist2"), ("c4_long", "c4_long", "sc_c4_long"), ("c4_ans", "c4_ans", "sc_c4_ans"),
    ("c5_a", "ch:5", "sc_c5_a"), ("c5_band", "c5_sel", "sc_c5_band"), ("c5_shell", "c5_you", "sc_c5_shell"), ("c5_crack", "c5_warm", "sc_c5_crack"),
    ("c5_peek", "c5_sib", "sc_c5_peek"), ("c5_feed", "c5_feed", "sc_c5_feed"), ("c5_edge", "c5_grow", "sc_c5_edge"), ("c5_sky", "c5_fly", "sc_c5_sky"),
    ("c5_town", "c5_wire", "sc_c5_town"), ("c5_in4718", "c5_4718", "sc_c5_in4718"), ("c5_autumn", "c5_autumn", "sc_c5_autumn"),
    ("c5_worst", "c5_worst0", "sc_c5_worst"), ("c5_b2", "c5_b2", "sc_c5_b2"), ("c5_shell2", "c5_noeave2", "sc_c5_shell2"), ("c5_sib2", "c5_3rd", "sc_c5_sib2"),
    ("c5_sea", "c5_travel", "sc_c5_sea"), ("c5_south", "c5_winter", "sc_c5_south"), ("c5_spring", "c5_spring", "sc_c5_spring"),
    ("c5_nestview", "c5_kids2", "sc_c5_nestview"), ("c5_fadeend", "c5_end2", "sc_c5_fadeend"),
    ("c6_answers", "ch:6", "sc_c6_answers"), ("c6_close", "c6_last", "sc_c6_close"), ("end", "end", "sc_end"),
]

# ---- 場面の切りかえの間: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c5_kids2": 1.2, "c1_other": 1.6, "c5_pair9": 1.6}


def _pace(items):
    need = {}
    for k in SCENE_KEYS:
        need[ID[k]] = max(need.get(ID[k], 0.0), SCENE_GAP)
    after = {ID[k]: v for k, v in HOLD_AFTER.items()}
    trial = {}
    if PACE_TRIAL:
        for _n, sp_, _f in SC_TABLE:
            k_ = sp_[2:] if sp_.startswith("z:") else sp_
            if k_ in ANCH and k_.startswith(TRIAL_CH):
                trial[ID[k_]] = trial_gap(k_)
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
        if isinstance(nx, lf.Line) and nx.id in trial:
            p = max(p, trial[nx.id])
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
T_ES = Ek("c6_last") + 0.5

# ============================================================
# データ（sims/tsubame_rough.py を同じ乱数の種で回した値。手で書き写さない）
# ============================================================
_rng = random.Random(tr.SEED)
BIRDS = [tr.one(_rng) for _ in range(tr.N)]
NB = tr.N
DAYS = sorted(b["days"] for b in BIRDS)
MED_DAYS = (DAYS[NB // 2 - 1] + DAYS[NB // 2]) / 2
EGG_PERIOD = tr.INCUB + tr.NESTLING            # 産卵から巣立ちまで（34日）
T_3W = EGG_PERIOD + 21                           # 巣立ち後3週間まで（55日）
T_BACK = T_3W + 300                              # 翌春（355日）
N_FAIL = sum(1 for b in BIRDS if b["stage"].startswith("巣ごと失敗"))
N_NOFL = sum(1 for b in BIRDS if b["stage"].startswith("巣立てず"))
N_FLEDGED = sum(1 for b in BIRDS if b["days"] > EGG_PERIOD)
N_3W_OK = sum(1 for b in BIRDS if b["days"] > T_3W)
N_BACK = sum(1 for b in BIRDS if b["days"] > T_BACK)
N_3W_DEAD = N_FLEDGED - N_3W_OK
N_MIG_DEAD = N_3W_OK - N_BACK
BACK = [b for b in BIRDS if b["days"] > T_BACK]
BACK_DAYS = sorted(b["days"] for b in BACK)
BACK_MED = (BACK_DAYS[len(BACK_DAYS) // 2 - 1] + BACK_DAYS[len(BACK_DAYS) // 2]) / 2 if len(BACK_DAYS) % 2 == 0 else BACK_DAYS[len(BACK_DAYS) // 2]
KIDS = sorted(b["kids"] for b in BACK)
KIDS_MED = (KIDS[len(KIDS) // 2 - 1] + KIDS[len(KIDS) // 2]) / 2 if len(KIDS) % 2 == 0 else KIDS[len(KIDS) // 2]
BROODS_MED = sorted(b["broods"] for b in BACK)[len(BACK) // 2]
MAX_KIDS = max(KIDS)
MAX_YEARS = DAYS[-1] / tr.YEAR
N_KID0 = sum(1 for k in KIDS if k == 0)
N_KID20 = sum(1 for k in KIDS if k >= 20)
KID_BINS = [("0", 0, 0), ("1–4", 1, 4), ("5–8", 5, 8), ("9–12", 9, 12), ("13–16", 13, 16), ("17–19", 17, 19), ("20以上", 20, 10 ** 6)]
KID_COUNTS = [sum(1 for k in KIDS if lo <= k <= hi) for _l, lo, hi in KID_BINS]
# 中央値の1羽（選び方は sims/tsubame_rough.py と同じ）
_med_stage = min(BIRDS, key=lambda b: abs(b["days"] - MED_DAYS))["stage"]
_pool = [b for b in BIRDS if b["stage"] == _med_stage]


def _mode(key):
    from collections import Counter
    return Counter(b[key] for b in BIRDS).most_common(1)[0][0]


_want = {"place": _mode("place"), "eaves": _mode("eaves"), "sex": _mode("sex"), "clutch": _mode("clutch")}
_pool2 = [b for b in _pool if all(b[k] == v for k, v in _want.items())]
import statistics as _st  # noqa: E402
_med_order = _st.median_low([b["order"] for b in BIRDS])
_pool3 = [b for b in _pool2 if b["order"] == _med_order] or _pool2
MED1 = min(_pool3, key=lambda b: abs(b["days"] - MED_DAYS))
_cand = [b for b in BACK if b["broods"] == BROODS_MED and b["kids"] == KIDS_MED] or [b for b in BACK if b["broods"] == BROODS_MED]
MED2 = min(_cand, key=lambda b: abs(b["days"] - BACK_MED))
# 5羽巣立った巣で、春まで生きている数（二項分布）
P_SURV = N_BACK / N_FLEDGED
NEST5 = [math.comb(5, k) * P_SURV ** k * (1 - P_SURV) ** (5 - k) for k in range(6)]
NEST5_SHOW = [NEST5[0], NEST5[1], NEST5[2], sum(NEST5[3:])]

# ============================================================
# 見た目（共通の道具: danchi-long.py と同じ札・線・場面の仕組み）
# ============================================================
W_, H_ = lf.W, lf.H
WHITE, YEL, PALE, REDC = "#ffffff", "#ffe14a", "#d6e2f5", "#e8505b"
FISHC = "#9db7df"
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



def ramp(idxs, t0, t1):
    """idxs の各要素に t0〜t1 の等間隔の時刻をわりふる（{番号: 時刻}）"""
    n = len(idxs)
    return {i: t0 + (t1 - t0) * k / max(1, n - 1) for k, i in enumerate(idxs)}


def shuffled(n, seed, keep=()):
    r_ = [i for i in range(n) if i not in keep]
    random.Random(seed).shuffle(r_)
    return r_

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






# ---- 章カード（平たい板・問いの番号は黄色）----
CARD_BY_N = {1: ["問い1", "巣立てる？"], 2: ["問い2", "巣立ちの後の3週間"], 3: ["問い3", "渡りと翌年の春"], 4: ["問い4", "春まで生きたツバメ"],
             5: ["最後に", "中央値の1羽の一生"], 6: ["まとめ"]}
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
            rr = [(s_, 76, YEL if (s_.startswith("問い") or s_ in ("まとめ", "最後に")) else WHITE) for s_ in rows]
            sc = 0.92 + 0.08 * ease_out(a)
            ctx.save()
            ctx.translate(960, 440)
            ctx.scale(sc, sc)
            panel(ctx, rr, 0, 0, a=a, pad=(60, 34), border=YEL)
            ctx.restore()


def ch_start(n):
    return S(f"ch{n}")


def ch_start(n):
    return S(f"ch{n}")




# ============================================================
# 絵の道具（tsubame_art.py の部品を、動きと札に合わせて並べる）
# ============================================================
SUB_Y = 936           # 字幕の帯の上端（札・図の文字はこの下に置かない）
INKC = "#5a4630"
CARDC = "#d4e3f0"     # グラフ・帯・地図を載せる無地のカード（背景の絵に直接のせない）
DARKTXT = "#1f2d44"
CREAM = "#fbf7ea"
C_FAIL, C_NOFL, C_3W, C_MIG, C_LIVE, C_OLD = "#d9747c", "#e9a64e", "#8e6bbf", "#3fa7a3", "#4caf6d", "#7f8fb0"
C_PRE = "#c58f9a"    # 並べ替えの帯の「巣立つ前」
ORANGE_TXT = "#a63f10"
GOLD = "#f3b72e"


def band(ctx, col, y0, y1, a=1.0, x0=0, x1=None):
    wa._set(ctx, col, a)
    ctx.rectangle(x0, y0, (W_ if x1 is None else x1) - x0, y1 - y0)
    ctx.fill()


def disc(ctx, x, y, r, col, a=1.0):
    wa._set(ctx, col, a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def drift_cloud(ctx, t, x0, y, s, sp=14.0, a=0.9):
    wa.cloud(ctx, (x0 + t * sp) % (W_ + 500) - 250, y, s, a=a)


def bob(t, a=3.0, w=1.9, ph=0.0):
    return math.sin(t * w + ph) * a


TONE = {"day": dict(top="#cde8f4", low="#e8f4f6", sun="#fff0b8", g1="#a8d08a", g2="#92c277"),
        "autumn": dict(top="#f3d6bb", low="#f9e7d1", sun="#ffd39c", g1="#dcc07e", g2="#cbaa63"),
        "warm": dict(top="#f7ecd5", low="#fbf3e2", sun="#ffe6a8", g1="#e8d9b8", g2="#dccaa2")}


def sky(ctx, t, tone="day", hor=790, clouds=True):
    c = TONE[tone]
    band(ctx, c["top"], 0, hor)
    band(ctx, c["low"], hor - 230, hor)
    disc(ctx, 1730, 150, 66, c["sun"])
    if clouds:
        drift_cloud(ctx, t, 560, 150, 78, 12.0)
        drift_cloud(ctx, t, 1250, 100, 58, 9.0)
    band(ctx, c["g1"], hor, H_)
    band(ctx, c["g2"], hor, hor + 26)


def wire_pt(x0, y0, x1, y1, sag, x):
    u = (x - x0) / (x1 - x0)
    return y0 + (y1 - y0) * u + 4 * sag * u * (1 - u)


def wire_line(ctx, x0, y0, x1, y1, sag=16.0, w=4.5, a=1.0):
    wa._set(ctx, wa.WIREC, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    n = 48
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = wire_pt(x0, y0, x1, y1, sag, x)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)
    ctx.stroke()


WIRE = (0.0, 700.0, 1920.0, 676.0, 22.0)     # x0, y0, x1, y1, sag


def wire_y(x):
    return wire_pt(*WIRE, x)


def wires(ctx, gap=34):
    for i in range(2):
        x0, y0, x1, y1, sag = WIRE
        wire_line(ctx, x0, y0 + i * gap, x1, y1 + i * gap, sag)


# ---------- 札の出し入れ ----------
def pw(rows, pad=(28, 16), gap=1.22):
    ws = [text_width(s_, sz) for s_, sz, _c in rows]
    hs = [sz * gap for _s, sz, _c in rows]
    return max(ws) + 2 * pad[0], sum(hs) + 2 * pad[1] - rows[-1][1] * (gap - 1.0)


def tkw(**kw):
    return kw


def R(*ss, sz=46, col=WHITE, first=None):
    """札の行を作る。first=行1だけ別の大きさ・色"""
    rows = [(s_, sz, col) for s_ in ss]
    if first:
        rows[0] = (ss[0], first[0], first[1])
    return rows


def card(ctx, t, t0, t1, rows, x, y, **kw):
    """札 rows を t0 から t1 まで（前後に 0.3 秒のフェード）。t1 が None なら出しっぱなし"""
    if t < t0:
        return
    a = fade(t, t0, 0.3) * (1.0 if t1 is None else out_fade(t, t1, 0.3))
    if a > 0.003:
        panel(ctx, rows, x, y, a=a, **kw)


def Cd(ctx, t, key, f, rows, x, y, t1=None, lead=0.0, **kw):
    """合図 key の文の f 割のところから札を出す（lead 秒ずらせる。マイナスで先に出す）"""
    card(ctx, t, Sk(key, f) + lead, t1, rows, x, y, **kw)


def stack(ctx, t, x, ytop, items, gap=16):
    """札を上から積む。items=[(key, f, rows, kw)]。高さを先に取っておくので、あとから出る札で位置が動かない。kw: lead, t1, border, pad…"""
    y = ytop
    for key, f, rows, kw in items:
        kw = dict(kw)
        pad = kw.get("pad", (28, 16))
        w, h = pw(rows, pad)
        xx = min(max(x, 60 + w / 2), W_ - 60 - w / 2)
        lead = kw.pop("lead", 0.0)
        t1 = kw.pop("t1", None)
        Cd(ctx, t, key, f, rows, xx, y + h / 2, t1=t1, lead=lead, **kw)
        y += h + gap
    return y


def ctag(ctx, t, key, f, s, t1=None, lead=0.0):
    """国が替わる所の、画面の右下の小さな札（40px）"""
    rows = [(s, 40, WHITE)]
    w, h = pw(rows, (22, 12))
    card(ctx, t, Sk(key, f) + lead, t1, rows, W_ - 62 - w / 2, 893, pad=(22, 12), bg="#2c4a73", r=14)


def chart_card(ctx, x0, y0, x1, y1, col=None, a=1.0):
    """グラフ・表・絵を載せる無地のカード（背景の絵に直接のせない）"""
    wa._set(ctx, col or CARDC, a)
    wa.rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
    ctx.fill()


def tx(ctx, s, x, y, size, col=DARKTXT, align="center", a=1.0):
    """カードの上に直に置く文字（core.text のログに残る）"""
    if a > 0.003:
        text(ctx, s, x, y, size, col, align=align, alpha=a)


def ramp(idxs, t0, t1):
    n = len(idxs)
    return {i: t0 + (t1 - t0) * k / max(1, n - 1) for k, i in enumerate(idxs)}


def shuffled(n, seed, keep=()):
    r_ = [i for i in range(n) if i not in keep]
    random.Random(seed).shuffle(r_)
    return r_


# ---------- 卵・ツバメの帯（100列×4段。1つの絵＝100個ぶんの割合）----------
def egg_fast(ctx, x, y, rx, ry, col, a=1.0):
    wa._set(ctx, col, a)
    wa.ell(ctx, x, y, rx, ry)
    ctx.fill()
    wa._set(ctx, "#ffffff", 0.5 * a)
    wa.ell(ctx, x - rx * 0.28, y - ry * 0.3, rx * 0.35, ry * 0.3)
    ctx.fill()


def bird_fast(ctx, x, y, rx, ry, col, a=1.0):
    wa._set(ctx, col, a)
    wa.ell(ctx, x, y, rx, ry)
    ctx.fill()
    ctx.move_to(x - rx * 0.7, y - ry * 0.3)
    ctx.line_to(x - rx * 1.6, y - ry * 0.9)
    ctx.line_to(x - rx * 1.2, y + ry * 0.2)
    ctx.close_path()
    ctx.fill()
    wa._set(ctx, "#f8eed8", a)
    wa.ell(ctx, x + rx * 0.12, y + ry * 0.38, rx * 0.62, ry * 0.5)
    ctx.fill()


BAND_COLS, BAND_ROWS = 50, 4


def band_geom(x0, x1, yc, rows=BAND_ROWS):
    pitch = (x1 - x0) / BAND_COLS
    rp = pitch * 1.25
    return pitch, rp, yc - rp * (rows - 1) / 2


def egg_band(ctx, x0, x1, yc, colfn, kind="egg", rows=BAND_ROWS):
    """colfn(i, f) -> (色, 不透明度)。i=列（0〜99）・f=列の中心の割合"""
    pitch, rp, ytop = band_geom(x0, x1, yc, rows)
    rx, ry = (pitch * 0.40, pitch * 0.54) if kind == "egg" else (pitch * 0.40, pitch * 0.34)
    for i in range(BAND_COLS):
        col, a = colfn(i, (i + 0.5) / BAND_COLS)
        if a <= 0.01:
            continue
        cx = x0 + pitch * (i + 0.5)
        for r_ in range(rows):
            (egg_fast if kind == "egg" else bird_fast)(ctx, cx, ytop + rp * r_, rx, ry, col, a)


N_BIRDS = ihalf(N_BACK / 10)     # 1羽＝10羽 → 108羽
BIRD_ROWS, BIRD_COLS = 6, 18


def bird_band(ctx, x0, x1, yc, colfn, h=38, rp=46):
    """1羽＝10羽のツバメの帯（108羽・18列×6段）。左から右へ生きた日数の順。colfn(k, f) -> (色 or None, 不透明度)"""
    pitch = (x1 - x0) / BIRD_COLS
    top = yc - rp * (BIRD_ROWS - 1) / 2 - h / 2
    u = h / 64.0
    for k in range(N_BIRDS):
        c_, r_ = divmod(k, BIRD_ROWS)
        col, a = colfn(k, (c_ + 0.5) / BIRD_COLS)
        if a <= 0.01:
            continue
        draw_swallow(ctx, x0 + pitch * (c_ + 0.5) + 17 * u, top + rp * r_ + h, h, pose="perch", col=col, a=a)


def bird_mark(ctx, x0, x1, yc, f, col=GOLD, a=1.0, w=7, h=38, rp=46):
    x = x0 + (x1 - x0) * f
    half = rp * (BIRD_ROWS - 1) / 2 + h / 2 + 30
    wa._set(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, yc - half)
    ctx.line_to(x, yc + half)
    ctx.stroke()


def cover(i, f0, f1):
    """列 i が区間 [f0, f1]（割合）にどれだけかかるか（0〜1）"""
    a, b = i / BAND_COLS, (i + 1) / BAND_COLS
    return clamp01((min(b, f1) - max(a, f0)) / (b - a))


def band_mark(ctx, x0, x1, yc, f, col=GOLD, a=1.0, rows=BAND_ROWS, up=70, down=70, w=7):
    """帯の上に縦の印（割合 f の位置）"""
    pitch, rp, ytop = band_geom(x0, x1, yc, rows)
    x = x0 + (x1 - x0) * f
    wa._set(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, ytop - up)
    ctx.line_to(x, ytop + rp * (rows - 1) + down)
    ctx.stroke()
    return x


def bracket(ctx, x0, x1, y, col, a=1.0, w=8):
    wa._set(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0 + 3, y - 14)
    ctx.line_to(x0 + 3, y)
    ctx.line_to(x1 - 3, y)
    ctx.line_to(x1 - 3, y - 14)
    ctx.stroke()


F1 = N_FAIL / NB                       # 巣ごと失敗
F2 = (N_FAIL + N_NOFL) / NB            # 巣立てず まで
F3 = (N_FAIL + N_NOFL + N_3W_DEAD) / NB   # 巣立って3週間以内 まで
F4 = (NB - N_BACK) / NB                # 渡りと冬 まで（ここから先が春まで生きた）


def px_of(f, x0, x1):
    return x0 + (x1 - x0) * f


# ---------- 棒グラフ ----------
def hbar(ctx, x0, y, wmax, h, frac, col, a=1.0):
    wa._set(ctx, col, a)
    wa.rrect(ctx, x0, y - h / 2, max(h * 0.6, wmax * frac), h, h * 0.28)
    ctx.fill()


def flock(ctx, t, n, x0, x1, y0, y1, h, seed=3, spd=170.0, young=False, facing=1, a=1.0):
    """飛ぶツバメの群れ（右へ流れる）"""
    rnd = random.Random(seed)
    for k in range(n):
        bx = rnd.uniform(0, W_ + 400)
        by = rnd.uniform(y0, y1)
        ph = rnd.uniform(0, 6.28)
        sp = spd * rnd.uniform(0.85, 1.15)
        x = ((bx + t * sp * facing) % (W_ + 400)) - 200
        y = by + math.sin(t * 0.8 + ph) * 26
        draw_swallow(ctx, x, y, h * rnd.uniform(0.8, 1.15), facing=facing, pose="fly", phase=t * 11 + ph, young=young, a=a)


def perch_row(ctx, t, xs, h=110, young=True, facing=1, alphas=None, ph=0.0):
    for k, x in enumerate(xs):
        a = 1.0 if alphas is None else alphas[k]
        if a <= 0.003:
            continue
        dy = -abs(math.sin(t * 1.3 + k * 1.7 + ph)) * 7 if int(t * 0.5 + k) % 4 == 0 else 0
        draw_swallow(ctx, x, wire_y(x) + 2 + dy, h, facing=facing, pose="perch", young=young, a=a)


def house_scene(ctx, t, nest_rim=(330, 235), nest_w=240, tone="day", x1=640):
    """遠景の家と軒下の巣。戻り値 = 巣のふち（x, y）"""
    sky(ctx, t, tone)
    wa.house_far(ctx, 0, x1, 190)
    wa.window(ctx, 90, 330, 190, 250)
    wa.window(ctx, 360, 330, 190, 250)
    return nest_rim


def paper_sheet(ctx, x, y, w, h, lines=6, a=1.0):
    wa._set(ctx, CREAM, a)
    wa.rrect(ctx, x, y, w, h, 14)
    ctx.fill()
    wa._set(ctx, "#d3c9ae", a)
    for i in range(lines):
        wa.rrect(ctx, x + 36, y + 56 + i * (h - 100) / max(1, lines), w - 72, 12, 6)
        ctx.fill()


def mini_nest_chips(ctx, x, y, n_solid, n_total, w=70, dx=88, young=True, a=1.0):
    """小さなツバメを並べて、n_solid 羽だけ濃く（ほかはうすく）"""
    for k in range(n_total):
        draw_swallow(ctx, x + k * dx, y, w, young=young, a=a * (1.0 if k < n_solid else 0.28))


# ============================================================
# 0 来年の春、何羽？
# ============================================================
Q_TXT = "来年の春、まだ生きているのは何羽？"
OPTS = ("4羽", "2羽", "1羽")
OPT_X = (1100, 1380, 1660)
OPT_Y = 835
FLY_STAG, FLY_DUR = 0.55, 1.7


def nest_look_up(ctx, t, t0=0.0, dur=6.0):
    """一人称: 巣の中から見上げた景色。兄弟のヒナ4羽、正面から親鳥がエサを運んでくる（1回だけ近づいて、巣のふちで止まる）"""
    band(ctx, "#cfe8f4", 0, H_)
    band(ctx, "#e6f3f8", 300, H_)
    band(ctx, "#6a5b55", 0, 170)
    band(ctx, "#51443f", 170, 200)
    drift_cloud(ctx, t, 300, 330, 100, 20.0)
    drift_cloud(ctx, t, 1400, 400, 80, 16.0)
    for x, ph in ((560, 0.0), (1370, 1.7)):          # 奥の兄弟（頭だけ見える）
        draw_chick(ctx, x, 1000, 330, grow=0.7, beak=0.5 + 0.5 * math.sin(t * 4 + ph), facing=1 if x < 960 else -1)
    wa._set(ctx, wa.MUD)
    wa.ell(ctx, 960, 1130, 1100, 220)
    ctx.fill()
    draw_chick(ctx, 250, 1000, 460, grow=0.7, beak=0.5 + 0.5 * math.sin(t * 5), facing=1)
    draw_chick(ctx, 1670, 1000, 460, grow=0.7, beak=0.5 + 0.5 * math.sin(t * 5 + 2), facing=-1)
    u = ease(seg(t, t0, t0 + dur))
    sc = 0.3 + 0.7 * u
    px = 1250 - 290 * u + 10 * math.sin(t * 1.1) * u
    py = 300 + 230 * u + 6 * math.sin(t * 1.9)
    if u < 0.97:
        spread = clamp01(0.35 + 0.65 * u) * (1.0 + 0.1 * math.sin(t * (14 - 9 * u)))
    else:
        spread = 0.85 + 0.2 * math.sin(t * 2.2)          # 止まっている間はゆっくり上下
    draw_swallow_front(ctx, px, py, 470 * sc, spread=spread)


def nest_fly_out(ctx, t, u):
    """一人称: 巣のふちから外の空へ飛び出す（約1秒）。ふちが下へ遠ざかり、空が広がる"""
    e = ease(clamp01(u))
    band(ctx, "#9fd0ec", 0, H_)
    band(ctx, "#cde8f4", 380, H_)
    drift_cloud(ctx, t, 400, 300 + 260 * e, 120, -160.0)
    drift_cloud(ctx, t, 1300, 200 + 300 * e, 90, -120.0)
    y = 200 - 420 * e
    band(ctx, "#6a5b55", int(y - 200), int(y))
    wa._set(ctx, wa.MUD)
    wa.ell(ctx, 960, 1130 + 700 * e, 1100, 220)
    ctx.fill()
    wing_tips(ctx, t)


def sc_open(ctx, t):
    t_out = Sk("c0_out", 0.15)
    t_cut = t_out + 1.0
    t_land = t_cut + FLY_STAG * 4 + FLY_DUR
    t_big = Sk("c0_ans3", 0.0)
    xs = [980, 1160, 1340, 1520, 1700]
    nx, ny, nw = 330, 255, 250
    if t < t_out:
        nest_look_up(ctx, t)
        Cd(ctx, t, "c0_bro", 0.4, [("5羽", 90, YEL)], 1560, 250, pad=(36, 12), border=YEL, t1=t_out)
    elif t < t_cut:
        nest_fly_out(ctx, t, (t - t_out) / 1.0)
    else:
        sky(ctx, t, "day", hor=800)
        wa.house_far(ctx, 0, 640, 205)
        wa.window(ctx, 80, 345, 170, 230)
        wa.window(ctx, 360, 345, 170, 230)
        pole(ctx, 1840, 420)
        wires(ctx)
        wa.nest_back(ctx, nx, ny, nw)
        t_leave = [t_cut + FLY_STAG * k for k in range(5)]
        for k in range(5):
            if t < t_leave[k]:
                draw_chick(ctx, nx - 80 + k * 40, ny + 8 + (k % 2) * 4, 70, grow=1.0, beak=0.5 + 0.5 * math.sin(t * 6 + k))
        wa.nest_front(ctx, nx, ny, nw)
        for k in range(5):
            u = clamp01((t - t_leave[k]) / FLY_DUR)
            if u <= 0:
                continue
            tx_, ty_ = xs[k], wire_y(xs[k]) + 2
            if u >= 1.0:
                draw_swallow(ctx, tx_, ty_ + bob(t, 2, 2.0, k), 112, pose="perch", young=True)
            else:
                e = ease(u)
                x = nx + (tx_ - nx) * e
                y = ny - 30 + (ty_ - 40 - (ny - 30)) * e - 150 * math.sin(math.pi * u)
                draw_swallow(ctx, x, y, 137, pose="fly", phase=t * 15 + k, young=True)
        for k, s_ in enumerate(OPTS):
            card(ctx, t, t_land + 0.3 + 0.17 * k, t_big, [(s_, 70, WHITE)], OPT_X[k], OPT_Y, pad=(30, 14), bg="#27518a")
    qa = out_fade(t, t_big, 0.35)
    if qa > 0.003 and t >= 1.0:
        card(ctx, t, 1.0, t_big, [(Q_TXT, 44, WHITE)], 1100, 75, pad=(30, 12), border=YEL)



def corner_card(ctx, t):
    """答えは問い3で（選択肢の札が上の隅に小さく残る）。第0章の終わりまで"""
    t0 = Sk("c0_ans3", 0.0)
    card(ctx, t, t0, None, [("答えは問い3で", 44, YEL), ("4羽　2羽　1羽", 44, WHITE)], 300, 100, pad=(26, 14), bg="#27518a")


def sc_c0_egg(ctx, t):
    sky(ctx, t, "warm", hor=700, clouds=False)
    band(ctx, "#cfe3b8", 700, H_)
    rnd = random.Random(5)
    t0 = Sk("c0_egg", 0.0) - 0.3
    k = 0
    for r_ in range(9):
        n = 17 - 2 * r_
        for i in range(n):
            ta = t0 + 0.06 * k
            k += 1
            if t < ta:
                continue
            e = ease_out(clamp01((t - ta) / 0.3))
            x = 640 + (i - (n - 1) / 2) * 64 + rnd.uniform(-5, 5)
            y = 900 - r_ * 54 + rnd.uniform(-4, 4)
            draw_egg(ctx, x, y - 8 * (1 - e), 38 * (0.6 + 0.4 * e), a=e, seed=k, tilt=rnd.uniform(-0.4, 0.4))
    Cd(ctx, t, "c0_egg", 0.45, [("日本の家の軒下で産まれる卵", 50, WHITE), ("1万個", 110, YEL)], 1400, 330, pad=(44, 22), border=YEL)


def sc_c0_one(ctx, t):
    band(ctx, "#cfe0ee", 0, H_)
    disc(ctx, 560, 520, 340, "#eaf2f8", 1.0)
    tl_ = 0.06 * math.sin(t * 1.4)
    draw_egg(ctx, 560, 520, 250, tilt=tl_, seed=11, spots=True)
    Cd(ctx, t, "c0_one", 0.4, [("最後に", 56, YEL), ("中央値の1羽の一生を", 58, WHITE), ("通しで", 58, WHITE)], 1400, 440, pad=(44, 22), border=YEL)


def _mid_band_cols(t, tmark):
    def f(i, fr):
        return ("#fffaf0", 1.0)
    return f


def sc_c0_med(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 150, 1810, 800)
    x0, x1, yc = 190, 1730, 470
    tm = Sk("c0_med", 0.35)
    mid = fade(t, tm, 0.3)

    def colfn(i, f):
        if mid > 0.5 and abs(f - 0.5) < 0.011:
            return (GOLD, 1.0)
        return ("#fffaf0", 1.0)
    egg_band(ctx, x0, x1, yc, colfn)
    if mid > 0.003:
        band_mark(ctx, x0, x1, yc, 0.5, a=mid, up=80, down=80)
        tx(ctx, "ちょうど真ん中", 960, 330 - 10, 48, "#5c3b00", a=mid)
    tx(ctx, "短い", x0 + 60, 640, 44, DARKTXT)
    tx(ctx, "長い", x1 - 60, 640, 44, DARKTXT)
    tx(ctx, "生きた日数", 960, 640, 44, DARKTXT)
    arrow2(ctx, (x0 + 160, 640), (x0 + 300, 640), "#5b6f93", 7, 1.0, head=22)
    arrow2(ctx, (x1 - 300, 640), (x1 - 160, 640), "#5b6f93", 7, 1.0, head=22)
    Cd(ctx, t, "c0_med", 0.0, R("中央値＝生きた日数の順に並べた、ちょうど真ん中", sz=46), 960, 880, lead=-0.2)
    tx(ctx, "/1万個", 1640, 220, 44, "#41567c")


def sc_c0_prob(ctx, t):
    sky(ctx, t, "day", hor=840, clouds=True)
    band(ctx, "#c9b99a", 700, 760, x0=0)
    t0 = Sk("c0_prob", 0.0) - 0.3
    bx0, bx1 = 760, 1160
    # くじの箱
    wa._set(ctx, "#f3c25a")
    wa.rrect(ctx, bx0, 420, bx1 - bx0, 340, 30)
    ctx.fill()
    wa._set(ctx, "#d49a2e")
    wa.rrect(ctx, bx0 + 30, 560, bx1 - bx0 - 60, 40, 14)
    ctx.fill()
    tx(ctx, "確率", (bx0 + bx1) / 2, 490, 78, "#5a3a00")
    tx(ctx, "記録の確率", (bx0 + bx1) / 2, 680, 44, "#5a3a00")
    # 卵の流れ
    period, speed = 0.8, 340.0
    for k in range(30):
        ta = t0 + k * period
        if t < ta:
            break
        x = 120 + (t - ta) * speed
        if x > 1900:
            continue
        rnd = random.Random(k * 7 + 1)
        y = 620
        a = 1.0
        if x > bx1:
            if rnd.random() < 0.45:
                a = max(0.0, 1.0 - (x - bx1) / 220.0)
        a_in = 1.0 if x < bx0 else (0.0 if bx0 < x < bx1 else 1.0)
        if a_in > 0 and a > 0.01:
            draw_egg(ctx, x, y + 40 - 14 * math.sin((x - bx1) * 0.02) * (1 if x > bx1 else 0), 42, a=a, seed=k)
    Cd(ctx, t, "c0_prob", 0.3, R("卵ごとに一生を進める", sz=46), 960, 200, pad=(34, 16))


# ============================================================
# 1 巣立てる？
# ============================================================
def wall(ctx, t):
    wa.bg_wall(ctx)


def nest_scene(ctx, t, x, y, w, n_eggs=5, egg_a=None, wob=True, a=1.0, mid=None):
    """卵が入った巣。mid(ctx) を渡すと、卵と手前のおわんのあいだ（中に入る絵）に描く"""
    wa.nest_back(ctx, x, y, w, a)
    for i, (ex, ey, tl) in enumerate(egg_slots(x, y, w, n_eggs)):
        aa = 1.0 if egg_a is None else egg_a(i)
        draw_egg(ctx, ex, ey, w * 0.075, a=a * aa, seed=i, tilt=tl + (0.05 * math.sin(t * 1.6 + i) if wob else 0))
    if mid:
        mid(ctx)
    wa.nest_front(ctx, x, y, w, a)


def sc_c1_a(ctx, t):
    wall(ctx, t)
    nest_scene(ctx, t, 640, 470, 540)


def sc_c1_spring(ctx, t):
    sky(ctx, t, "day", hor=820)
    t0, t1 = SC_START["c1_spring"], SC_END["c1_spring"]
    u = clamp01((t - t0) / (t1 - t0))
    x = -200 + 2300 * u
    draw_swallow(ctx, x, 420 + 60 * math.sin(u * 7), 250, pose="fly", phase=t * 12)
    draw_swallow(ctx, x - 420, 300 + 40 * math.sin(u * 6 + 1), 130, pose="fly", phase=t * 12 + 2)
    draw_swallow(ctx, x - 650, 560 + 30 * math.sin(u * 5), 110, pose="fly", phase=t * 12 + 4)
    Cd(ctx, t, "c1_spring", 0.4, R("春に日本に来る", sz=64, col=WHITE), 1380, 190, pad=(40, 20), border=YEL)


def sc_c1_eave(ctx, t):
    sky(ctx, t, "day", hor=820)
    wa.house_far(ctx, 0, 980, 250)
    wa.window(ctx, 90, 400, 220, 280)
    wa.window(ctx, 650, 400, 220, 280)
    nx, ny, nw = 470, 345, 330
    nest_scene(ctx, t, nx, ny, nw, 4, mid=lambda c: draw_swallow(c, nx - 10, ny + 60, 190, pose="perch", facing=1))
    draw_swallow(ctx, 1500 + 160 * math.sin(t * 0.6), 330 + 40 * math.sin(t * 0.9), 130, pose="fly", phase=t * 12, facing=1 if math.cos(t * 0.6) > 0 else -1)
    Cd(ctx, t, "c1_eave", 0.6, R("秋に東南アジアへ", sz=64), 1420, 640, pad=(40, 20), border=YEL)


def pie(ctx, cx, cy, r, slices, p):
    """slices=[(割合, 色)]。12時から時計回り。p=0〜1 で描ききる"""
    ang = -math.pi / 2
    tot = 2 * math.pi * p
    used = 0.0
    for fr, col in slices:
        sweep = 2 * math.pi * fr
        s = max(0.0, min(sweep, tot - used))
        if s > 0:
            wa._set(ctx, col)
            ctx.move_to(cx, cy)
            ctx.arc(cx, cy, r, ang + used, ang + used + s)
            ctx.close_path()
            ctx.fill()
        used += sweep


def sc_c1_pie(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 100, 70, 1060, 905)
    cx, cy, r = 580, 487, 330
    p = ease(seg(t, SC_START["c1_pie"] + 0.2, Sk("c1_pie", 0.5)))
    pie(ctx, cx, cy, r, [(0.99, "#f2c47a"), (0.01, "#9aa9b8")], max(p, 0.0))
    a6 = fade(t, Sk("c1_6", 0.0), 0.5)
    if a6 > 0.003:
        wa._set(ctx, "#ef8a3b", a6)
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * 0.60)
        ctx.close_path()
        ctx.fill()
        panel(ctx, [("一戸建ての家・お店", 44, WHITE), ("約6割", 76, YEL)], cx + 130, cy + 40, a=a6, pad=(30, 16), bg="#7a3a12")
    Cd(ctx, t, "c1_pie", 0.5, [("建物", 64, WHITE), ("99%", 130, YEL)], 1480, 380, pad=(56, 24), border=YEL)
    ctag(ctx, t, "c1_pie", 0.3, "日本の記録（環境省 1997年度）")


def sc_c1_clutch(ctx, t):
    wall(ctx, t)
    t0 = Sk("c1_clutch", 0.15)
    nest_scene(ctx, t, 640, 470, 560, 5, egg_a=lambda i: fade(t, t0 + 0.4 * i, 0.3))
    Cd(ctx, t, "c1_clutch", 0.6, [("平均", 50, WHITE), ("4.55個", 120, YEL)], 1420, 360, pad=(50, 22), border=YEL)
    ctag(ctx, t, "c1_clutch", 0.45, "イギリスの記録")


def sc_c1_brood(ctx, t):
    wall(ctx, t)
    nx, ny, nw = 640, 470, 560
    nest_scene(ctx, t, nx, ny, nw, 5, wob=False, mid=lambda c: draw_swallow(c, nx + 10, ny + 105 + bob(t, 2, 1.3), 330, pose="perch", facing=1))
    Cd(ctx, t, "c1_brood", 0.45, [("温めて約2週間", 54, WHITE), ("（13〜14日）", 54, YEL)], 1420, 340, pad=(44, 22), border=YEL)
    ctag(ctx, t, "c1_brood", 0.4, "日本の記録（北海道）")


def sc_c1_chicks(ctx, t):
    wall(ctx, t)
    nx, ny, nw = 700, 470, 640
    g = ease(seg(t, Sk("c1_chicks", 0.05), Ek("c1_chicks") + 0.4))

    def chicks(c):
        for k in range(4):
            x = nx + (k - 1.5) * nw * 0.23
            draw_chick(c, x, ny + 34 - (k % 2) * 6, 80 + 110 * g, grow=g, beak=max(0.0, math.sin(t * 5 + k * 1.7)))
    wa.nest_back(ctx, nx, ny, nw)
    chicks(ctx)
    wa.nest_front(ctx, nx, ny, nw)
    Cd(ctx, t, "c1_chicks", 0.3, [("かえってから巣立ちまで", 46, WHITE), ("約3週間（17〜22日）", 56, YEL)], 1450, 340, pad=(44, 22), border=YEL)


def sc_c1_fail(ctx, t):
    wall(ctx, t)
    f0 = fade(t, Sk("c1_fail0", 0.45), 0.9)
    a_n = 1.0 - 0.58 * f0
    nest_scene(ctx, t, 640, 470, 560, 5, a=a_n, wob=False)
    Cd(ctx, t, "c1_fail", 0.15, [("巣の失敗 約2割", 60, YEL)], 1400, 340, pad=(40, 20), border=YEL)
    ctag(ctx, t, "c1_fail", 0.4, "日本の記録")


def sc_c1_enemy(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 100, 120, 1060, 880)
    a1 = fade(t, Sk("c1_enemy", 0.2), 0.4)
    a2 = fade(t, Sk("c1_enemy", 0.4), 0.4)
    draw_crow(ctx, 350, 700 + bob(t, 3, 1.5), 330, a=a1)
    draw_snake(ctx, 790, 770, 380, a=a2)
    tx(ctx, "カラス", 330, 780, 48, DARKTXT, a=a1)
    tx(ctx, "ヘビ", 790, 800, 48, DARKTXT, a=a2)
    wa.draw_nest(ctx, 580, 330, 300, eggs=3, a=0.9)
    Cd(ctx, t, "c1_enemy", 0.45, [("天敵", 64, WHITE), ("約36%", 130, YEL)], 1470, 420, pad=(56, 24), border=YEL)


def sc_c1_other(ctx, t):
    wall(ctx, t)
    nest_scene(ctx, t, 430, 480, 380, 3, wob=False)
    a = fade(t, Sk("c1_other", 0.15), 0.5)
    wa.draw_sparrow_icon(ctx, 760 + (1 - a) * 160, 560, 230, a=a)
    card(ctx, t, Sk("c1_other", 0.15) + 0.5, None, [("スズメ", 44, WHITE)], 800, 360, pad=(24, 10), bg="#27518a")
    stack(ctx, t, 1410, 90, [
        ("c1_other", 0.25, [("スズメの乗っ取り", 46, WHITE), ("14%", 90, YEL)], dict(pad=(36, 18), border=YEL)),
        ("c1_other", 0.5, [("人による撤去", 46, WHITE), ("12%", 90, YEL)], dict(pad=(36, 18), border=YEL)),
        ("c1_other", 0.65, [("推定をふくむ", 46, WHITE)], dict(pad=(36, 16))),
    ])


def stage_colfn(t, segs):
    def f(i, fr):
        col, a = "#fffaf0", 1.0
        for f0, f1, t0, dur, segcol, fa in segs:
            p = clamp01((t - t0) / dur)
            c = cover(i, f0, f0 + (f1 - f0) * p)
            if c > 0:
                col = mix(col, segcol, 0.75 * c)
                a *= 1 - (1 - fa) * c
        return (col, a)
    return f


BX0, BX1 = 190, 1730


def sc_c1_band1(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 170, 1810, 840)
    segs = [(0.0, F1, Sk("c1_band1", 0.2), 1.0, C_FAIL, 0.28)]
    egg_band(ctx, BX0, BX1, 380, stage_colfn(t, segs))
    tx(ctx, "/1万個", 1650, 250, 44, "#41567c")
    a = fade(t, Sk("c1_band1", 0.6), 0.4)
    bracket(ctx, BX0, px_of(F1, BX0, BX1), 480, C_FAIL, a)
    Cd(ctx, t, "c1_band1", 0.55, [("巣ごと失敗", 48, WHITE), ("2,165個", 96, YEL), ("/1万個", 40, WHITE)], 520, 650, pad=(40, 18), border=YEL)


def sc_c1_one(ctx, t):
    wall(ctx, t)
    t0 = Sk("c1_one", 0.35)
    nest_scene(ctx, t, 640, 470, 560, 5, egg_a=lambda i: (1.0 - 0.75 * fade(t, t0, 0.8)) if i == 4 else 1.0)
    Cd(ctx, t, "c1_one", 0.5, [("日本の巣立ち 平均約4羽", 46, WHITE), ("÷ イギリスの卵 平均4.55個", 46, WHITE)], 1390, 340, pad=(40, 20), border=YEL)


def sc_c1_band2(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 170, 1810, 840)
    segs = [(0.0, F1, -99.0, 1.0, C_FAIL, 0.28), (F1, F2, Sk("c1_nofl", 0.3), 1.0, C_NOFL, 0.28)]
    egg_band(ctx, BX0, BX1, 380, stage_colfn(t, segs))
    tx(ctx, "/1万個", 1650, 250, 44, "#41567c")
    bracket(ctx, BX0, px_of(F1, BX0, BX1), 480, C_FAIL, 1.0)
    tx(ctx, "巣ごと失敗", px_of(F1 / 2, BX0, BX1), 530, 40, "#8a3038")
    a = fade(t, Sk("c1_nofl", 0.55), 0.4)
    bracket(ctx, px_of(F1, BX0, BX1), px_of(F2, BX0, BX1), 480, C_NOFL, a)
    Cd(ctx, t, "c1_nofl", 0.55, [("巣立てず", 48, WHITE), ("980個", 96, YEL), ("/1万個", 40, WHITE)], 640, 700, pad=(40, 18), border=YEL)
    ab = fade(t, Sk("c1_ans", 0.15), 0.4)
    bracket(ctx, px_of(F2, BX0, BX1), BX1, 480, "#41567c", ab)
    Cd(ctx, t, "c1_ans", 0.55, [("巣立った", 48, WHITE), ("6,855羽", 110, YEL), ("/1万個", 40, WHITE)], 1340, 700, pad=(44, 20), border=YEL)


# ============================================================
# 2 巣立ちの後の3週間
# ============================================================
WIRE_XS6 = (330, 560, 790, 1020, 1250, 1480)


def wire_scene(ctx, t, tone="day", n=6, xs=None, h=122, alphas=None):
    sky(ctx, t, tone)
    pole(ctx, 90, 330)
    wires(ctx)
    perch_row(ctx, t, xs or WIRE_XS6[:n], h=h, alphas=alphas)


def sc_c2_a(ctx, t):
    wire_scene(ctx, t)


def sc_c2_safe(ctx, t):
    wire_scene(ctx, t)
    Cd(ctx, t, "c2_safe", 0.5, R("巣立てば、ひと安心？", sz=76), 960, 330, pad=(50, 24), border=YEL)


def chips_card(ctx, t, x0, y0, n_solid, t_fade, w=900, h=560, dx=170, sh=78):
    """小さなツバメ10羽（2段×5）を無地のカードに。n_solid 羽だけ濃く、ほかは t_fade から うすくなる"""
    chart_card(ctx, x0, y0, x0 + w, y0 + h)
    k = 0
    for r_ in range(2):
        for c_ in range(5):
            solid = k < n_solid
            a = 1.0 if solid else 1.0 - 0.72 * fade(t, t_fade + 0.12 * (k - n_solid), 0.6)
            draw_swallow(ctx, x0 + 130 + c_ * dx, y0 + 240 + r_ * 200, sh, pose="perch", young=True, a=a)
            k += 1


def sc_c2_three(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chips_card(ctx, t, 80, 160, 3, Sk("c2_3wari", 0.4))
    Cd(ctx, t, "c2_3wari", 0.45, [("巣立ち後3週間の生き残り", 46, WHITE), ("約3割", 130, YEL), ("（0.32）", 52, WHITE)], 1430, 380, pad=(50, 22), border=YEL)
    ctag(ctx, t, "c2_3wari", 0.5, "スイスの記録")


def sc_c2_radio(ctx, t):
    sky(ctx, t, "day", hor=820)
    bx, by, bh = 560, 640, 340
    wire_line(ctx, 0, 650, 1100, 636, 14)
    draw_swallow(ctx, bx, by + bob(t, 2, 1.4), bh, pose="perch", young=True)
    u = bh / 64.0
    gx, gy = bx - 2 * u, by - 46 * u
    wa.draw_tag(ctx, gx, gy, 16)
    for k in range(3):
        ph = (t * 1.2 + k * 0.33) % 1.0
        wa._set(ctx, "#e8505b", 0.75 * (1 - ph))
        ctx.set_line_width(5)
        ctx.arc(gx - 30, gy - 28, 28 + 70 * ph, math.pi * 1.05, math.pi * 1.55)
        ctx.stroke()
    Cd(ctx, t, "c2_radio", 0.5, R("発信機で追跡", sz=54), 1360, 220, pad=(40, 20), border=YEL)
    stack(ctx, t, 1330, 360, [("c2_lost", 0.35, [("見つからない＝一生を終えた", 46, WHITE)], dict(pad=(36, 18)))])


def sc_c2_band(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 170, 1810, 840)
    segs = [(0.0, F1, -99.0, 1.0, C_FAIL, 0.28), (F1, F2, -99.0, 1.0, C_NOFL, 0.28), (F2, F3, Sk("c2_dead", 0.25), 1.0, C_3W, 0.28)]
    egg_band(ctx, BX0, BX1, 380, stage_colfn(t, segs))
    tx(ctx, "/1万個", 1650, 250, 44, "#41567c")
    a1 = fade(t, Sk("c2_band", 0.55), 0.4)
    bracket(ctx, px_of(F3, BX0, BX1), BX1, 480, C_LIVE, a1)
    Cd(ctx, t, "c2_band", 0.55, [("3週間を越えた", 48, WHITE), ("2,137羽", 96, YEL), ("/1万個", 40, WHITE)], 1560, 690, pad=(40, 18), border=YEL)
    a2 = fade(t, Sk("c2_dead", 0.3), 0.4)
    bracket(ctx, px_of(F2, BX0, BX1), px_of(F3, BX0, BX1), 480, C_3W, a2)
    Cd(ctx, t, "c2_dead", 0.3, [("巣立って3週間以内", 48, WHITE), ("4,718羽", 96, YEL), ("/1万個", 40, WHITE)], 990, 690, pad=(40, 18), border=YEL)


BARS_X0, BARS_W = 720, 920


def sc_c2_bars(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 150, 1810, 740)
    rows = [("巣ごと失敗", N_FAIL, C_FAIL, "c2_x2", 0.1), ("巣立てず", N_NOFL, C_NOFL, "c2_most", 0.3), ("巣立って3週間以内", N_3W_DEAD, C_3W, "c2_x2", 0.35)]
    vmax = N_3W_DEAD
    for k, (lab, v, col, key, f) in enumerate(rows):
        y = 280 + k * 150
        tx(ctx, lab, 150, y, 46, DARKTXT, align="left")
        ta = Sk(key, f)
        p = ease(seg(t, ta, ta + 0.9))
        if p > 0:
            hbar(ctx, BARS_X0, y, BARS_W, 70, v / vmax * p, col)
            tx(ctx, f"{v:,}個" if k < 2 else f"{v:,}羽", BARS_X0 + BARS_W * v / vmax + 24, y, 46, DARKTXT, align="left", a=fade(t, ta + 0.9, 0.3))
    tx(ctx, "/1万個", 1650, 200, 44, "#41567c")
    Cd(ctx, t, "c2_most", 0.5, R("この3週間に何が起きたかは、記録に残っていない", sz=44), 960, 830, pad=(34, 14))
    g = fade(t, Sk("c2_most", 0.45), 0.4)
    if g > 0.003:
        wa._set(ctx, GOLD, g * (0.6 + 0.4 * math.sin(t * 5)))
        ctx.set_line_width(9)
        wa.rrect(ctx, BARS_X0 - 14, 580 - 52, BARS_W + 250, 104, 26)
        ctx.stroke()


def sc_c2_sort(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 130, 1810, 850)
    x0, x1, yc = BX0, BX1, 400
    tx(ctx, "短い", x0 + 40, 560, 44, DARKTXT)
    tx(ctx, "生きた日数", 960, 560, 44, DARKTXT)
    tx(ctx, "長い", x1 - 40, 560, 44, DARKTXT)
    arrow2(ctx, (x0 + 130, 560), (x0 + 300, 560), "#5b6f93", 7, 1.0, head=22)
    arrow2(ctx, (x1 - 300, 560), (x1 - 130, 560), "#5b6f93", 7, 1.0, head=22)
    tx(ctx, "/1万個", 1650, 220, 44, "#41567c")
    t_fill0, t_fill1 = Sk("c2_sort", 0.1), Sk("c2_sort", 1.0)
    tint0 = Sk("c2_half", 0.1)
    tint1 = Sk("c2_half", 0.9)

    # 色づけは「左から」伸びる
    def colfn2(i, f):
        a = clamp01((t - (t_fill0 + (t_fill1 - t_fill0) * f)) / 0.25)
        p = ease(clamp01((t - tint0) / max(0.1, tint1 - tint0)))
        reach = p * F3
        col = "#fffaf0"
        if f <= reach:
            col = mix("#fffaf0", C_PRE if f < F2 else C_3W, 0.85)
        return (col, a)
    egg_band(ctx, x0, x1, yc, colfn2)
    tm = fade(t, Sk("c2_sort", 0.7), 0.4)
    band_mark(ctx, x0, x1, yc, 0.5, a=tm, up=50, down=70)
    tx(ctx, "ちょうど真ん中", 960, 175, 44, "#5c3b00", a=tm)
    a_b = fade(t, tint1 - 0.5, 0.5)
    if a_b > 0.003:
        bracket(ctx, x0, px_of(F2, x0, x1), 650, C_PRE, a_b)
        tx(ctx, "巣立つ前", px_of(F2 / 2, x0, x1), 695, 40, "#7a4a58", a=a_b)
        bracket(ctx, px_of(F2, x0, x1), px_of(F3, x0, x1), 650, C_3W, a_b)
        tx(ctx, "巣立って3週間以内", px_of((F2 + F3) / 2, x0, x1), 695, 40, "#5b3a9e", a=a_b)
    q = fade(t, Sk("c2_where", 0.3), 0.4)
    if q > 0.003:
        tx(ctx, "？", 960, 262, 100, "#6b4e00", a=q)


def sc_c2_ans(ctx, t):
    sky(ctx, t, "day")
    wires(ctx)
    pole(ctx, 90, 330)
    xs = [330 + 150 * k for k in range(10)]
    t0 = Sk("c2_ans", 0.35)
    alphas = [1.0 if k < 3 else 1.0 - 0.8 * fade(t, t0 + 0.14 * (k - 3), 0.7) for k in range(10)]
    perch_row(ctx, t, xs, h=118, alphas=alphas)
    stack(ctx, t, 960, 60, [
        ("c2_ans", 0.45, [("巣立ったヒナのうち、", 46, WHITE), ("3週間後に残るのは", 46, WHITE), ("約3割", 110, YEL)], dict(pad=(46, 20), border=YEL)),
        ("c2_ans2", 0.3, [("1万個の卵の半分以上が、3週間までに一生を終える", 46, WHITE)], dict(pad=(36, 16))),
    ])


# ============================================================
# 3 渡りと翌年の春
# ============================================================
def sc_c3_a(ctx, t):
    sky(ctx, t, "autumn")
    flock(ctx, t, 8, 0, W_, 220, 640, 124, seed=4, spd=150.0)


MAP_RECT = (900, 40, 1830, 900)
MAP_RECT2 = (480, 25, 1440, 925)        # 画面の真ん中に大きく（北緯46度・南緯10度までに絞る）
MAP_BOX2 = (96.0, -10.0, 146.0, 46.0)
SEA_PAINT = "#f0914a"
JP_XY = (139.7, 36.0)


def map_labels(ctx, mv, t, items):
    """items=[(名前, 経度, 緯度, 出る時刻)]"""
    for nm, lo, la, ta in items:
        a = fade(t, ta, 0.4)
        if a > 0.003:
            x, y = mv.xy(lo, la)
            panel(ctx, [(nm, 40, WHITE)], x, y, a=a, bg="#7a3a12", pad=(16, 8), r=12)


def sc_c3_map(ctx, t):
    sky(ctx, t, "day", hor=900)
    for k in range(4):          # 秋の空を旋回する若いツバメ（左の空きに）
        ph = k * 1.6
        bx = 470 + 300 * math.cos(t * 0.55 + ph)
        by = 690 + 120 * math.sin(t * 0.8 + ph)
        draw_swallow(ctx, bx, by, 112, pose="fly", phase=t * 12 + ph, young=True, facing=1 if -math.sin(t * 0.55 + ph) >= 0 else -1)
    mv = MapView(*MAP_RECT)
    t_ph, t_my = Sk("c3_ashiwa", 0.35), Sk("c3_malay", 0.3)
    paint = {"PHL": SEA_PAINT, "IDN": SEA_PAINT, "MYS": SEA_PAINT, "VNM": SEA_PAINT}
    pal = {"PHL": fade(t, t_ph, 0.6), "IDN": fade(t, t_ph, 0.6), "MYS": fade(t, t_my, 0.6), "VNM": fade(t, t_my, 0.6)}
    paint = {k: v for k, v in paint.items() if pal[k] > 0.003}
    mv.draw(ctx, paint=paint, paint_alpha=pal)
    jx, jy = mv.xy(*JP_XY)
    disc(ctx, jx, jy, 13, "#e8505b")
    panel(ctx, [("日本", 40, WHITE)], jx - 78, jy + 8, a=1.0, bg="#7a1f2a", pad=(16, 8), r=12)
    # 飛び立つ若いツバメ（日本の上で小さく）
    tf = Sk("c3_first", 0.3)
    if t >= tf:
        u = clamp01((t - tf) / 3.0)
        draw_swallow(ctx, jx + 10 + 14 * u, jy - 40 - 50 * ease(u), 70, pose="fly", phase=t * 13, young=True, a=fade(t, tf, 0.3))
    tw = Sk("c3_winter", 0.25)
    if t >= tw:
        for k, (lo, la) in enumerate(((126.5, 8.0), (121.0, -6.5), (105.5, 6.5), (110.5, 10.0))):
            x, y = mv.xy(lo, la)
            draw_swallow(ctx, x, y - 24 + bob(t, 4, 2.0, k), 62, pose="fly", phase=t * 8 + k, a=fade(t, tw + 0.2 * k, 0.4))
    map_labels(ctx, mv, t, [("フィリピン", 122.0, 14.5, t_ph + 0.2), ("インドネシア", 108.0, -4.0, t_ph + 0.4),
                            ("マレーシア", 111.0, 5.2, t_my + 0.2), ("ベトナム南部", 101.0, 13.5, t_my + 0.4)])
    Cd(ctx, t, "c3_ashiwa", 0.35, R("足環＝鳥の足につける輪", sz=44), 450, 330, pad=(32, 16), border=YEL)
    ctag(ctx, t, "c3_ashiwa", 0.3, "日本の記録（山階鳥類研究所）")


def sc_c3_swiss(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chips_card(ctx, t, 80, 160, 5, Sk("c3_51", 0.4))
    stack(ctx, t, 1420, 150, [
        ("c3_51", 0.45, [("1年目の渡りと冬の生き残り", 46, WHITE), ("約51%", 120, YEL)], dict(pad=(44, 20), border=YEL)),
    ])
    ctag(ctx, t, "c3_51", 0.4, "スイスの記録")


def sc_c3_band(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 170, 1810, 840)
    segs = [(0.0, F1, -99.0, 1.0, C_FAIL, 0.28), (F1, F2, -99.0, 1.0, C_NOFL, 0.28), (F2, F3, -99.0, 1.0, C_3W, 0.28),
            (F3, F4, Sk("c3_band", 0.3), 1.0, C_MIG, 0.28)]
    egg_band(ctx, BX0, BX1, 380, stage_colfn(t, segs))
    tx(ctx, "/1万個", 1650, 250, 44, "#41567c")
    a1 = fade(t, Sk("c3_band", 0.55), 0.4)
    bracket(ctx, px_of(F4, BX0, BX1), BX1, 480, C_LIVE, a1)
    Cd(ctx, t, "c3_band", 0.55, [("春まで生きた", 48, WHITE), ("1,075羽", 96, YEL), ("/1万個", 40, WHITE)], 1560, 690, pad=(40, 18), border=YEL)


def sc_c3_cmp(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 90, 1810, 640)
    rows = [("巣立って3週間", N_3W_DEAD, C_3W, "c3_4718", "羽"), ("最初の渡りと冬", N_MIG_DEAD, C_MIG, "c3_1062", "羽")]
    x0, wmax = 650, 900
    for k, (lab, v, col, key, un) in enumerate(rows):
        y = 250 + k * 160
        tx(ctx, lab, 150, y, 48, DARKTXT, align="left")
        wa._set(ctx, "#cdd9e6")
        wa.rrect(ctx, x0, y - 38, wmax, 76, 20)
        ctx.fill()
        ta = Sk(key, 0.35)
        p = ease(seg(t, ta, ta + 0.9))
        if p > 0:
            hbar(ctx, x0, y, wmax, 76, v / N_3W_DEAD * p, col)
            tx(ctx, f"{v:,}羽", x0 + wmax * v / N_3W_DEAD + 22, y, 46, DARKTXT, align="left", a=fade(t, ta + 0.9, 0.3))
    tx(ctx, "/1万個", 1650, 160, 44, "#41567c")
    g = fade(t, Sk("c3_big", 0.35), 0.4)
    if g > 0.003:
        wa._set(ctx, GOLD, g * (0.6 + 0.4 * math.sin(t * 5)))
        ctx.set_line_width(9)
        wa.rrect(ctx, 130, 250 - 56, 1650, 112, 26)
        ctx.stroke()
    Cd(ctx, t, "c3_guess", 0.3, R("渡りのほうが危ない？", sz=68), 960, 790, t1=Sk("c3_4718", 0.35), pad=(48, 22), border=YEL)
    Cd(ctx, t, "c3_ratio", 0.3, [("生き残り", 46, WHITE), ("3週間 約3割（0.32）", 46, WHITE), ("渡りと冬 約5割（0.51・推定をふくむ）", 46, WHITE)], 960, 790, pad=(44, 18), border=YEL)


def sc_c3_back(ctx, t):
    sky(ctx, t, "day", hor=800)
    wa.house_far(ctx, 0, 640, 205)
    wa.window(ctx, 80, 345, 170, 230)
    wa.window(ctx, 360, 345, 170, 230)
    pole(ctx, 1840, 420)
    wires(ctx)
    wa.nest_back(ctx, 330, 255, 250)
    wa.nest_front(ctx, 330, 255, 250)
    perch_row(ctx, t, [980, 1160, 1340, 1520, 1700], h=112)
    for k, s_ in enumerate(OPTS):
        card(ctx, t, Sk("c3_again", 0.3 + 0.2 * k), None, [(s_, 70, WHITE)], OPT_X[k], OPT_Y, pad=(30, 14), bg="#27518a")


def sc_c3_six(ctx, t):
    sky(ctx, t, "day")
    wires(ctx)
    pole(ctx, 90, 330)
    t0 = Sk("c3_six", 0.35)
    xs = [300 + 290 * k for k in range(6)]
    for k, x in enumerate(xs):
        a = 1.0 if k == 0 else 1.0 - 0.72 * fade(t, t0, 0.8)
        draw_swallow(ctx, x, wire_y(x) + 2, 150, pose="perch", young=True, a=a)
    g = fade(t, t0, 0.8)
    if g > 0.003:
        wa._set(ctx, C_LIVE, g * 0.9)
        ctx.set_line_width(10)
        ctx.arc(xs[0] + 6, wire_y(xs[0]) - 76, 100, 0, 2 * math.pi)
        ctx.stroke()
    Cd(ctx, t, "c3_six", 0.1, R("1,075 / 6,855", sz=110, col=YEL), 960, 300, pad=(60, 26), border=YEL)


def sc_c3_dist(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 160, 1810, 880)
    base, hmax = 770, 430
    xs = (470, 770, 1070, 1370)
    labs = ("0羽", "1羽", "2羽", "3羽以上")
    pct = [ihalf(100 * v) for v in NEST5_SHOW]
    keys = ("c3_zero", "c3_rest", "c3_rest", "c3_rest")
    fr = (0.7, 0.2, 0.45, 0.78)
    cols = ("#8a6bc2", "#5b8bd0", "#5b8bd0", "#5b8bd0")
    wa._set(ctx, "#9fb2c8")
    ctx.rectangle(150, base, 1620, 6)
    ctx.fill()
    for k in range(4):
        tx(ctx, labs[k], xs[k], base + 56, 48, DARKTXT)
        ta = Sk(keys[k], fr[k])
        p = ease(seg(t, ta, ta + 0.8))
        h_ = hmax * NEST5_SHOW[k] / NEST5_SHOW[0] * p
        if p > 0:
            wa._set(ctx, cols[k])
            wa.rrect(ctx, xs[k] - 95, base - h_, 190, h_ + 8, 22)
            ctx.fill()
            tx(ctx, f"{pct[k]}%", xs[k], base - hmax * NEST5_SHOW[k] / NEST5_SHOW[0] - 40, 56, DARKTXT, a=fade(t, ta + 0.8, 0.3))
    g0 = fade(t, Sk("c3_zero", 0.7), 0.4)
    if g0 > 0.003:
        wa._set(ctx, GOLD, g0 * (0.6 + 0.4 * math.sin(t * 5)))
        ctx.set_line_width(9)
        wa.rrect(ctx, xs[0] - 125, base - hmax - 100, 250, hmax + 190, 26)
        ctx.stroke()
    tx(ctx, "/5羽の巣", 1640, 240, 44, "#41567c")
    # 選択肢の札
    tx(ctx, "選択肢", 190, 82, 42, DARKTXT)
    ox = (400, 600, 800)
    for k, s_ in enumerate(OPTS):
        panel(ctx, [(s_, 50, WHITE)], ox[k], 82, a=1.0, pad=(26, 10), bg="#27518a")
    card(ctx, t, Sk("c3_nochoice", 0.55), None, [("0羽", 50, YEL)], 1000, 82, pad=(26, 10), bg="#27518a", border=YEL)
    gm = fade(t, Sk("c3_med", 0.45), 0.4)
    if gm > 0.003:
        wa._set(ctx, GOLD, gm)
        ctx.set_line_width(8)
        wa.rrect(ctx, ox[2] - 70, 82 - 40, 140, 80, 22)
        ctx.stroke()
    Cd(ctx, t, "c3_med", 0.55, [("中央値", 46, WHITE), ("1羽", 110, YEL), ("/5羽の巣", 40, WHITE)], 1640, 420, pad=(40, 18), border=YEL)
    g2 = fade(t, Sk("c3_two", 0.25), 0.4)
    if g2 > 0.003:
        wa._set(ctx, "#e8505b", g2)
        ctx.set_line_width(8)
        ctx.set_dash([20, 14])
        wa.rrect(ctx, xs[2] - 125, base - 260, xs[3] - xs[2] + 250, 380, 24)
        ctx.stroke()
        ctx.set_dash([])
    Cd(ctx, t, "c3_two", 0.4, [("2羽以上", 46, WHITE), (f"{ihalf(100 * sum(NEST5[2:]))}%", 96, YEL), ("/5羽の巣", 40, WHITE)], 1640, 720, pad=(40, 16), border=YEL)


# ============================================================
# 4 春まで生きたツバメ
# ============================================================
def eave_parent(ctx, t, parent=True, tone="day"):
    """春の軒下の巣と親のツバメ（遠景の家）"""
    sky(ctx, t, tone, hor=820)
    wa.house_far(ctx, 0, 980, 250)
    wa.window(ctx, 90, 400, 220, 280)
    wa.window(ctx, 650, 400, 220, 280)
    nx, ny, nw = 470, 345, 330
    if parent:
        nest_scene(ctx, t, nx, ny, nw, 4, wob=False, mid=lambda c: draw_swallow(c, nx - 10, ny + 60, 190, pose="perch", facing=1))
    else:
        nest_scene(ctx, t, nx, ny, nw, 4, wob=False)
    draw_swallow(ctx, 1500 + 160 * math.sin(t * 0.6), 330 + 40 * math.sin(t * 0.9), 130, pose="fly", phase=t * 12, facing=1 if math.cos(t * 0.6) > 0 else -1)


def sc_c4_a(ctx, t):
    eave_parent(ctx, t)


def bird_colfn_stage(t, segs):
    return stage_colfn(t, segs)


def sc_c4_base(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 110, 1810, 900)
    segs = [(0.0, F1, -99.0, 1.0, C_FAIL, 0.28), (F1, F2, -99.0, 1.0, C_NOFL, 0.28), (F2, F3, -99.0, 1.0, C_3W, 0.28), (F3, F4, -99.0, 1.0, C_MIG, 0.28)]
    egg_band(ctx, BX0, BX1, 300, stage_colfn(t, segs))
    # 札「/1万個」→「/1,075羽」
    ts_ = Sk("c4_base", 0.3)
    a_old = out_fade(t, ts_, 0.2)
    a_new = fade(t, ts_ + 0.3, 0.3)
    tx(ctx, "/1万個", 1650, 190, 44, "#41567c", a=a_old)
    tx(ctx, "/1,075羽", 1650, 190, 44, "#145a2c", a=a_new)
    tp = Sk("c4_pull", 0.0)
    bracket(ctx, px_of(F4, BX0, BX1), BX1, 400, C_LIVE, fade(t, tp - 0.3, 0.4))
    if t >= tp - 0.2:
        a_ar = fade(t, tp, 0.4)
        arrow2(ctx, (px_of((F4 + 1) / 2, BX0, BX1), 420), (1300, 480), "#145a2c", 8, a_ar, head=26)
        tx(ctx, "1羽＝10羽", 330, 450, 46, "#145a2c", a=a_ar)

    def colfn(i, f):
        return (None, clamp01((t - (tp + 0.3 + 1.0 * f)) / 0.25))
    bird_band(ctx, BX0, BX1, 630, colfn)
    Cd(ctx, t, "c4_tenth", 0.3, [("1,075羽 /1万個 ＝ 約1割", 60, YEL)], 960, 830, pad=(48, 20), border=YEL)


def sc_c4_start(ctx, t):
    wall(ctx, t)
    nx, ny, nw = 640, 470, 560
    nest_scene(ctx, t, nx, ny, nw, 0, wob=False)
    draw_swallow(ctx, nx + 20, ny - 5 + bob(t, 3, 1.4), 330, pose="perch", facing=1)
    stack(ctx, t, 1440, 220, [
        ("c4_twice", 0.35, [("年に2回 約8割", 56, WHITE)], dict(pad=(40, 18), border=YEL)),
        ("c4_twice", 0.75, [("1回 約2割", 56, WHITE)], dict(pad=(40, 18), border=YEL)),
    ])
    ctag(ctx, t, "c4_age", 0.5, "イギリスの記録", t1=Sk("c4_twice", 0.0))
    ctag(ctx, t, "c4_twice", 0.2, "スイスの記録")


def sc_c4_decay(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 150, 1810, 800)
    xs = (330, 770, 1210, 1650)
    ns = (8, 5, 2, 1)
    ts_ = (SC_START["c4_decay"] + 0.3, Sk("c4_decay", 0.25), Sk("c4_decay", 0.55), Sk("c4_decay", 0.85))
    for k in range(4):
        a = fade(t, ts_[k], 0.4)
        if a <= 0.003:
            continue
        for j in range(ns[k]):
            ex = xs[k] + ((j % 4) - 1.5) * 76
            ey = 500 + (j // 4) * 96
            draw_egg(ctx, ex, ey, 40, a=a, seed=j + k * 9, col="#ffeec2")
    for k in range(3):
        a = fade(t, ts_[k + 1] - 0.2, 0.4)
        if a > 0.003:
            gx = (xs[k] + xs[k + 1]) / 2
            panel(ctx, [(f"問い{k + 1}", 70, YEL)], gx, 330, a=a, pad=(40, 18), border=YEL)
            arrow2(ctx, (gx - 80, 520), (gx + 80, 520), "#41567c", 10, a, head=28)
    tx(ctx, "同じ確率", 960, 730, 54, "#41567c", a=fade(t, ts_[1], 0.5))


def sc_c4_adult(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    mv = MapView(*MAP_RECT)
    paint = {"PHL": SEA_PAINT, "IDN": SEA_PAINT, "MYS": SEA_PAINT, "VNM": SEA_PAINT}
    mv.draw(ctx, paint=paint)
    jx, jy = mv.xy(*JP_XY)
    sx, sy = mv.xy(113.0, 2.0)
    for k in range(2):
        u = 0.5 - 0.5 * math.cos(t * 0.9 + k * math.pi)
        x = jx + (sx - jx) * ease(u)
        y = jy + (sy - jy) * ease(u) - 30 * math.sin(math.pi * u)
        draw_swallow(ctx, x, y, 90, pose="fly", phase=t * 11 + k, facing=-1 if math.sin(t * 0.9 + k * math.pi) > 0 else 1)
    disc(ctx, jx, jy, 13, "#e8505b")
    Cd(ctx, t, "c4_49", 0.4, [("大人の渡りと冬の生き残り", 46, WHITE), ("約49%", 120, YEL), ("（推定をふくむ）", 44, WHITE)], 450, 400, pad=(44, 20), border=YEL)
    ctag(ctx, t, "c4_49", 0.2, "スイスの記録")


def sc_c4_band(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 80, 1810, 530)
    t0 = SC_START["c4_band"] + 0.3
    bird_band(ctx, BX0, BX1, 275, lambda k, f: (None, 1.0))
    tx(ctx, "/1,075羽", 1650, 125, 44, "#145a2c")
    tx(ctx, "1羽＝10羽", 330, 125, 44, "#145a2c")
    tx(ctx, "短い", BX0 + 40, 485, 42, DARKTXT)
    tx(ctx, "長い", BX1 - 40, 485, 42, DARKTXT)
    tx(ctx, "生きた日数", 960, 485, 42, DARKTXT)
    a = fade(t, Sk("c4_life", 0.3), 0.4)
    bird_mark(ctx, BX0, BX1, 275, 0.5, a=a)
    xs = (330, 960, 1590)
    stack_y = 560
    Cd(ctx, t, "c4_life", 0.45, [("寿命の中央値", 44, WHITE), ("約2年（1.97年）", 58, YEL), ("/1,075羽", 40, WHITE)], xs[0], stack_y + 120, pad=(22, 16), border=YEL)
    Cd(ctx, t, "c4_brood", 0.45, [("子育ての回数の中央値", 44, WHITE), ("2回", 90, YEL), ("/1,075羽", 40, WHITE)], xs[1], stack_y + 120, pad=(22, 16), border=YEL)
    Cd(ctx, t, "c4_kids", 0.45, [("巣立たせたヒナの中央値", 44, WHITE), ("9羽", 90, YEL), ("/1,075羽", 40, WHITE)], xs[2], stack_y + 120, pad=(22, 16), border=YEL)
    Cd(ctx, t, "c4_pair", 0.35, R("親2羽とも9羽と数える（半分にしない）", sz=44), 960, 860, pad=(36, 14))


HX = [330 + 215 * k for k in range(7)]
HBASE, HMAX = 720, 340
HBAR_COL = ["#8a6bc2"] + ["#5b8bd0"] * 5 + ["#3fa7a3"]


def hist_frame(ctx):
    chart_card(ctx, 110, 130, 1810, 890)
    wa._set(ctx, "#9fb2c8")
    ctx.rectangle(150, HBASE, 1620, 6)
    ctx.fill()
    for k, (lab, lo, hi) in enumerate(KID_BINS):
        tx(ctx, {"0": "0羽", "20以上": "20羽以上"}.get(lab, lab), HX[k], HBASE + 52, 44, DARKTXT)
    tx(ctx, "巣立たせたヒナの数（親1羽ごとに数えたヒナ）", 960, HBASE + 130, 40, "#41567c")
    tx(ctx, "/1,075羽", 1650, 190, 44, "#145a2c")


def hist_bars(ctx, t, ks, t0, dt=0.0, dur=0.9, tickets=False):
    cmax = max(KID_COUNTS)
    for j, k in enumerate(ks):
        ta = t0 + dt * j
        p = ease(seg(t, ta, ta + dur))
        if p <= 0:
            continue
        h_ = HMAX * KID_COUNTS[k] / cmax * p
        wa._set(ctx, HBAR_COL[k])
        wa.rrect(ctx, HX[k] - 80, HBASE - h_, 160, h_ + 8, 20)
        ctx.fill()


def sc_c4_hist(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    hist_frame(ctx)
    hist_bars(ctx, t, [0], Sk("c4_zero", 0.2))
    a = fade(t, Sk("c4_zero", 0.45), 0.4)
    h0 = HMAX * KID_COUNTS[0] / max(KID_COUNTS)
    tx(ctx, f"{N_KID0}羽（{ihalf(100 * N_KID0 / N_BACK)}%）", HX[0], HBASE - h0 - 110, 46, DARKTXT, a=a)


def sc_c4_empty(ctx, t):
    wall(ctx, t)
    nx, ny, nw = 640, 470, 560
    nest_scene(ctx, t, nx, ny, nw, 0, wob=False)
    draw_swallow(ctx, nx + 250, ny - 20 + bob(t, 3, 1.3), 300, pose="perch", facing=-1)


def sc_c4_hist2(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    hist_frame(ctx)
    hist_bars(ctx, t, [0], -99.0)
    hist_bars(ctx, t, [1, 2, 3, 4, 5], SC_START["c4_hist2"] + 0.5, dt=0.18)
    t20 = Sk("c4_20", 0.35)
    hist_bars(ctx, t, [6], t20)
    h6 = HMAX * KID_COUNTS[6] / max(KID_COUNTS)
    a6 = fade(t, Sk("c4_20", 0.55), 0.4)
    tx(ctx, f"{N_KID20}羽（{ihalf(100 * N_KID20 / N_BACK)}%）", HX[6], HBASE - h6 - 62, 46, DARKTXT, a=a6)
    h0 = HMAX * KID_COUNTS[0] / max(KID_COUNTS)
    tx(ctx, f"{N_KID0}羽（{ihalf(100 * N_KID0 / N_BACK)}%）", HX[0], HBASE - h0 - 62, 46, DARKTXT)
    am = fade(t, Sk("c4_max", 0.5), 0.4)
    tx(ctx, f"最多 {MAX_KIDS}羽", HX[6] + 20, HBASE - h6 - 150, 46, "#8a3a0a", a=am)
    ag = fade(t, Sk("c4_gap", 0.35), 0.5)
    if ag > 0.003:
        arrow2(ctx, (HX[0] - 60, 330), (HX[6] + 60, 330), "#e8505b", 9, ag, head=28)
        tx(ctx, "0羽", HX[0] - 60, 275, 46, "#8a3038", a=ag)
        tx(ctx, f"{MAX_KIDS}羽", HX[6] + 60, 275, 46, "#8a3038", a=ag)
    tk = Sk("c4_tickets", 0.15)
    if tk <= t < Ek("c4_tickets"):
        rnd = random.Random(7)
        for q in range(50):
            ta = tk + rnd.uniform(0, 1.6)
            u = clamp01((t - ta) / 0.7)
            if 0 < u < 1:
                k = rnd.randrange(7)
                wa._set(ctx, "#ffffff", 0.9 * (1 - u * 0.4))
                wa.rrect(ctx, HX[k] - 12 + rnd.uniform(-60, 60), 250 + (HBASE - 330) * u * 0.9, 26, 34, 5)
                ctx.fill()


def sc_c4_long(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 80, 1810, 540)
    tint = fade(t, Sk("c4_half", 0.35), 0.6)

    def colfn(i, f):
        return (mix("#35538d", "#e9a64e", 0.65 * tint) if f < 0.5 else None, 1.0)
    bird_band(ctx, BX0, BX1, 300, colfn)
    tx(ctx, "/1,075羽", 1650, 125, 44, "#145a2c")
    tx(ctx, "1羽＝10羽", 330, 125, 44, "#145a2c")
    ax = fade(t, Sk("c4_long", 0.3), 0.4)
    bird_mark(ctx, BX0, BX1, 300, 0.995, a=ax)
    panel(ctx, [("最長", 44, WHITE), (f"{MAX_YEARS:.1f}年", 80, YEL)], 1560, 650, a=ax, pad=(36, 16), border=YEL)
    am = fade(t, Sk("c4_half", 0.4), 0.4)
    bird_mark(ctx, BX0, BX1, 300, 0.5, a=am)
    panel(ctx, [("約2年", 56, YEL)], 960, 600, a=am, pad=(36, 14), border=YEL)
    stack(ctx, t, 520, 590, [("c4_uk", 0.25, [("記録に残る最長", 46, WHITE), ("約11年", 100, YEL)], dict(pad=(40, 16), border=YEL))])
    ctag(ctx, t, "c4_uk", 0.2, "イギリスの記録")


def sc_c4_ans(ctx, t):
    eave_parent(ctx, t)
    stack(ctx, t, 1410, 90, [
        ("c4_ans", 0.3, [("答え", 52, YEL), ("春まで生きたツバメは", 46, WHITE), ("中央値で約2年", 90, YEL)], dict(pad=(44, 20), border=YEL)),
        ("c4_ans2", 0.3, [("子育て2回・ヒナ9羽（つがいで）", 50, WHITE), ("/1,075羽", 40, WHITE)], dict(pad=(40, 16), border=YEL)),
    ])


# ============================================================
# 5 中央値の1羽の一生（2026-11-08 一人称: あなた＝そのツバメ。ツバメ自身の体は描かず、見えている景色だけ）
# ============================================================
def sc_c5_a(ctx, t):
    band(ctx, "#cfe0ee", 0, H_)
    disc(ctx, 1450, 600, 340, "#eaf2f8", 1.0)
    draw_egg(ctx, 1450, 600, 240, tilt=0.05 * math.sin(t * 1.4), seed=11, spots=True)


def sorted_colfn(live=True):
    def f(i, fr):
        if fr < F2:
            return (C_PRE, 1.0)
        if fr < F3:
            return (C_3W, 1.0)
        if fr < F4:
            return (C_MIG, 1.0)
        return (C_LIVE, 1.0)
    return f


def sc_c5_band(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 110, 1810, 600)
    x0, x1, yc = BX0, BX1, 300
    tm = Sk("c5_sel", 0.5)
    mid = fade(t, tm, 0.3)

    def colfn(i, f):
        if mid > 0.5 and abs(f - 0.5) < 0.011:
            return (GOLD, 1.0)
        return mix("#fffaf0", sorted_colfn()(i, f)[0], 0.8), 1.0
    egg_band(ctx, x0, x1, yc, colfn)
    tx(ctx, "/1万個", 1650, 175, 44, "#41567c")
    tx(ctx, "短い", x0 + 40, 450, 42, DARKTXT)
    tx(ctx, "長い", x1 - 40, 450, 42, DARKTXT)
    tx(ctx, "生きた日数", 960, 450, 42, DARKTXT)
    if mid > 0.003:
        band_mark(ctx, x0, x1, yc, 0.5, a=mid, up=70, down=60)
    an = fade(t, Sk("c5_sel", 0.6), 0.5)
    if an > 0.003:
        ctx.push_group()
        draw_egg(ctx, 960, 770, 120, seed=11)
        wa._set(ctx, GOLD)
        ctx.set_line_width(10)
        wa.ell(ctx, 960, 770, 120 * 0.78 + 18, 120 + 18)
        ctx.stroke()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(an)
        arrow2(ctx, (960, 470), (960, 620), GOLD, 8, an, head=26)
    Cd(ctx, t, "c5_sel", 0.55, [("場所・卵の数は", 46, WHITE), ("1万個でいちばんよくある形", 46, WHITE)], 1400, 790, pad=(40, 18), border=YEL)


# ---------- 一人称の景色（体は描かない）----------
SHELL = "#33261a"
SHELL_D = "#7a5f3c"


def shell_inside(ctx, t, glow=0.3, drift=0.0, p=0.0):
    """殻の内側（暗いこげ茶〜暗いクリーム）。p=0 は外の光がうすく透ける程度、p>0 はひびから放射状に光が差す"""
    band(ctx, "#241a12", 0, H_)
    for rx, ry, col in ((1100, 700, "#33261a"), (900, 560, "#47341f"), (700, 430, "#5c4529"), (480, 290, "#6f5532")):
        wa._set(ctx, col)
        wa.ell(ctx, 960, 540, rx, ry)
        ctx.fill()
    gx = 1250 + 60 * math.sin(t * 0.5 + drift)
    gy = 330 + 30 * math.cos(t * 0.4)
    k = 0.5 + 0.5 * math.sin(t * 0.8)
    for r_, al in ((330, 0.10), (230, 0.16), (140, 0.22)):
        wa._set(ctx, "#ffe9a8", al * (0.6 + 0.4 * k) * (1 + 1.5 * p))
        wa.ell(ctx, gx, gy, r_ * 1.3, r_)
        ctx.fill()
    if p > 0.01:
        cx, cy = 1100, 420
        n = 16
        for i in range(n):
            ang = 2 * math.pi * i / n + 0.12 * math.sin(t * 0.7 + i)
            w = 0.05 + 0.03 * ((i * 7) % 3)
            for al, scl in ((0.10, 1.0), (0.16, 0.6)):
                wa._set(ctx, "#fffbd8", al * p * (0.7 + 0.3 * math.sin(t * 2 + i)))
                ctx.move_to(cx, cy)
                ctx.line_to(cx + math.cos(ang - w * scl) * 1900, cy + math.sin(ang - w * scl) * 1900)
                ctx.line_to(cx + math.cos(ang + w * scl) * 1900, cy + math.sin(ang + w * scl) * 1900)
                ctx.close_path()
                ctx.fill()
        for r_, al in ((420, 0.18), (260, 0.3), (140, 0.5)):
            wa._set(ctx, "#fffbe0", al * p)
            wa.ell(ctx, cx, cy, r_ * 0.7, r_)
            ctx.fill()
        crack_lines(ctx, p)


def crack_lines(ctx, p, cx=1100, cy=420):
    """殻のひび割れ。p=0〜1 で伸び、割れ目から光が差す"""
    pts = [(cx, cy - 260), (cx - 40, cy - 150), (cx + 30, cy - 60), (cx - 30, cy + 30), (cx + 40, cy + 130), (cx, cy + 240)]
    n = max(2, int(2 + (len(pts) - 2) * p))
    sub = pts[:n]
    if n < len(pts):                          # 伸びている先を途中まで
        f_ = (len(pts) - 2) * p - (n - 2)
        a_, b_ = pts[n - 1], pts[n]
        sub = sub + [(a_[0] + (b_[0] - a_[0]) * f_, a_[1] + (b_[1] - a_[1]) * f_)]
    if len(sub) < 2:
        return
    wa._set(ctx, "#fff3c4", 0.35 + 0.5 * p)
    ctx.set_line_width(70 * p + 8)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(*sub[0])
    for q in sub[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    wa._set(ctx, "#fffdf0", 0.8 * p)
    ctx.set_line_width(22 * p + 3)
    ctx.move_to(*sub[0])
    for q in sub[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    wa._set(ctx, "#7a6648", 0.8)
    ctx.set_line_width(5)
    for dx in (-1, 1):
        ctx.move_to(sub[0][0] + dx * (8 + 14 * p), sub[0][1])
        for q in sub[1:]:
            ctx.line_to(q[0] + dx * (8 + 14 * p), q[1])
        ctx.stroke()


def shell_frame(ctx, rx, ry, cx=960, cy=540):
    """割れた殻のふち（中央が開いている）。後ろに描いた景色が穴から見える"""
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(0, 0, W_, H_)
    n = 24
    for i in range(n + 1):            # ぎざぎざの穴
        a = 2 * math.pi * i / n
        k = 1.0 + (0.07 if i % 2 else -0.05)
        (ctx.move_to if i == 0 else ctx.line_to)(cx + rx * k * math.cos(a), cy + ry * k * math.sin(a))
    ctx.close_path()
    wa._set(ctx, SHELL)
    ctx.fill()
    ctx.restore()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    wa._set(ctx, SHELL_D, 0.9)
    ctx.set_line_width(10)
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        k = 1.0 + (0.07 if i % 2 else -0.05)
        (ctx.move_to if i == 0 else ctx.line_to)(cx + rx * k * math.cos(a), cy + ry * k * math.sin(a))
    ctx.stroke()


def sc_c5_shell(ctx, t):
    """ここからは、あなたがその卵です → 殻の内側"""
    tz = Sk("c5_you", 0.2)
    u = ease(seg(t, tz, tz + 1.6))
    if u < 1.0:                       # 印の卵に寄っていく
        band(ctx, "#cfe0ee", 0, H_)
        disc(ctx, 960, 540, 340 + 700 * u, "#eaf2f8")
        draw_egg(ctx, 960, 540, 120 + 700 * u, tilt=0.0, seed=11)
        wa._set(ctx, GOLD, 1 - u)
        ctx.set_line_width(10)
        wa.ell(ctx, 960, 540, (120 + 700 * u) * 0.78 + 18, 120 + 700 * u + 18)
        ctx.stroke()
    if u > 0.003:
        ctx.push_group()
        shell_inside(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp01((u - 0.5) * 2))
    stack(ctx, t, 1450, 120, [
        ("c5_nest", 0.3, [("5個のうち3番目", 60, YEL)], dict(pad=(40, 18), border=YEL)),
        ("c5_nest", 0.5, [("記録では家とお店をまとめて数える", 42, WHITE)], dict(pad=(34, 16))),
    ])


def sc_c5_crack(ctx, t):
    shell_inside(ctx, t, glow=0.3, p=ease(seg(t, Sk("c5_warm", 0.1), Sk("c5_warm", 0.8))))


def nest_wall_view(ctx, t, chicks=1, seed=2):
    """割れた殻の穴から見える、巣の中（泥の壁と、兄弟のヒナ）"""
    band(ctx, "#e9dcc0", 0, H_)
    band(ctx, "#a9795a", 560, H_)
    wa._set(ctx, "#8f6246")
    for i in range(14):
        wa.ell(ctx, 120 + i * 140, 640 + (i * 37) % 160, 36, 18)
        ctx.fill()
    wa._set(ctx, "#c4a47a")
    for i in range(10):
        ctx.rectangle(100 + i * 190, 560, 90, 8)
        ctx.fill()
    xs = {1: [1180], 2: [900, 1260]}[chicks]
    for k, x in enumerate(xs):
        draw_chick(ctx, x, 700 + 20 * k, 330, grow=0.6, beak=0.25 * max(0.0, math.sin(t * 2 + k * 2)), facing=-1 if k else 1, eye_closed=True)


def sc_c5_peek(ctx, t):
    nest_wall_view(ctx, t, 1)
    shell_frame(ctx, 680, 400)
    Cd(ctx, t, "c5_male", 0.2, R("オス", sz=80, col=YEL), 1500, 200, pad=(50, 22), border=YEL)


def sc_c5_feed(ctx, t):
    nest_look_up(ctx, t, SC_START["c5_feed"] + 0.2, 2.6)


def sc_c5_edge(ctx, t):
    """巣のふちから、はるか下の地面を見下ろす（庭と道。小さな人）"""
    band(ctx, "#8fbf72", 0, H_)
    rnd = random.Random(8)
    for k in range(40):                                  # 草むらのまだら
        wa._set(ctx, "#7db062" if k % 2 else "#a3cf86", 0.22)
        wa.ell(ctx, rnd.uniform(0, W_), rnd.uniform(0, 520), rnd.uniform(40, 120), rnd.uniform(20, 50))
        ctx.fill()
    band(ctx, "#8a8f98", 560, 650)                       # 道（細く）
    band(ctx, "#a0a5ad", 560, 568)
    wa._set(ctx, "#f2f2f2")
    for i in range(10):
        ctx.rectangle(40 + i * 200 - ((t * 20) % 200), 602, 60, 6)
        ctx.fill()
    for x in (420, 1500):                                # 植木鉢
        wa._set(ctx, "#c9683c")
        wa.rrect(ctx, x - 30, 360, 60, 50, 8)
        ctx.fill()
        wa._set(ctx, "#4f9a52")
        wa.ell(ctx, x, 352, 42, 26)
        ctx.fill()
    for x in (760, 1160):
        wa._set(ctx, "#6faa5a")
        wa.ell(ctx, x, 420, 90, 44)
        ctx.fill()
    px = 260 + (t - SC_START["c5_edge"]) * 60                    # 道ばたを歩く小さな人（上から: 影・肩・頭）
    py = 536
    wa._set(ctx, "#000000", 0.22)
    wa.ell(ctx, px + 8, py + 8, 20, 9)
    ctx.fill()
    wa._set(ctx, "#e26a4a")
    wa.ell(ctx, px, py, 19, 10)
    ctx.fill()
    wa._set(ctx, "#f0cfa8")
    ctx.arc(px, py, 10, 0, 2 * math.pi)
    ctx.fill()
    wa._set(ctx, "#4a3a2a")
    ctx.arc(px - 1, py - 1, 6, math.pi, 2 * math.pi)
    ctx.fill()
    cx_ = 700 + (t - SC_START["c5_edge"]) * 140                   # 道を走る車（上から）
    wa._set(ctx, "#000000", 0.22)
    wa.rrect(ctx, cx_ - 44, 622, 100, 38, 10)
    ctx.fill()
    wa._set(ctx, "#4a78b8")
    wa.rrect(ctx, cx_ - 48, 616, 100, 36, 10)
    ctx.fill()
    wa._set(ctx, "#cfe6f3")
    wa.rrect(ctx, cx_ - 14, 621, 36, 26, 6)
    ctx.fill()
    wa._set(ctx, wa.MUD)                                 # 手前のふち
    ctx.move_to(0, 760)
    ctx.curve_to(480, 650 + 14 * math.sin(t * 1.2), 1440, 650 + 14 * math.sin(t * 1.2), 1920, 760)
    ctx.line_to(1920, H_)
    ctx.line_to(0, H_)
    ctx.close_path()
    ctx.fill()
    wa._set(ctx, wa.MUD_L, 0.9)
    ctx.set_line_width(14)
    ctx.move_to(0, 760)
    ctx.curve_to(480, 650 + 14 * math.sin(t * 1.2), 1440, 650 + 14 * math.sin(t * 1.2), 1920, 760)
    ctx.stroke()


def wing_tips(ctx, t, a=1.0):
    """画面の端に入る翼の先（体は描かない）"""
    for sgn, x in ((1, 0), (-1, W_)):
        ctx.save()
        ctx.translate(x, 960)
        ctx.scale(sgn, 1)
        ctx.rotate(-0.25 + 0.18 * math.sin(t * 7))
        wa._set(ctx, wa.NAVY_D, a)
        ctx.move_to(-20, 0)
        ctx.curve_to(120, -80, 300, -90, 420, -40)
        ctx.curve_to(300, -10, 140, 30, -20, 80)
        ctx.close_path()
        ctx.fill()
        ctx.restore()


def sc_c5_sky(ctx, t):
    """視界が上がり、空が広がる"""
    u = ease(seg(t, SC_START["c5_sky"], Sk("c5_fly", 1.0)))
    band(ctx, "#9fd0ec", 0, H_)
    band(ctx, "#cde8f4", 380, H_)
    drift_cloud(ctx, t, 400, 300, 120, 24.0)
    drift_cloud(ctx, t, 1300, 200, 90, 18.0)
    drift_cloud(ctx, t, 900, 520, 70, 14.0)
    # 屋根が下へ遠ざかる
    y = 760 + 520 * u
    wa._set(ctx, "#6a5b55")
    ctx.move_to(0, y + 60)
    ctx.line_to(700, y - 120)
    ctx.line_to(1500, y - 40)
    ctx.line_to(1920, y + 100)
    ctx.line_to(1920, H_ + 400)
    ctx.line_to(0, H_ + 400)
    ctx.close_path()
    ctx.fill()
    wing_tips(ctx, t)


def town(ctx, t, whiten=0.0, y0=520):
    band(ctx, "#cde8f4", 0, y0)
    drift_cloud(ctx, t, 600, 150, 80, 12.0)
    drift_cloud(ctx, t, 1500, 110, 60, 9.0)
    band(ctx, "#a8d08a", y0, H_)
    band(ctx, "#8a8f98", y0 + 250, y0 + 330)
    cols = ("#c9683c", "#5b7fa8", "#8c6b9a", "#6aa58a", "#c98a3c")
    xs = (60, 380, 760, 1130, 1480, 1780)
    for k, x in enumerate(xs):
        w = 250 + (k * 37) % 80
        wa._set(ctx, "#f2e6cc")
        ctx.rectangle(x, y0 + 40, w, 150)
        ctx.fill()
        wa._set(ctx, cols[k % 5])
        ctx.move_to(x - 20, y0 + 40)
        ctx.line_to(x + w / 2, y0 - 60)
        ctx.line_to(x + w + 20, y0 + 40)
        ctx.close_path()
        ctx.fill()
    for x in (300, 1000, 1700):
        wa._set(ctx, "#5f9a4f")
        wa.ell(ctx, x, y0 + 200, 50, 60)
        ctx.fill()
    # 手前の電線
    wire_line(ctx, 0, 880, W_, 880, 46.0, w=30, a=1.0)
    wa._set(ctx, "#1f2430", 0.0)
    if whiten > 0.003:
        wa._set(ctx, "#ffffff", whiten)
        ctx.rectangle(0, 0, W_, H_)
        ctx.fill()


def sc_c5_town(ctx, t):
    wh = ease(seg(t, Sk("c5_8d", 0.25), Ek("c5_8d") + 0.8)) * 0.97
    town(ctx, t, wh)
    Cd(ctx, t, "c5_42", 0.3, [("中央値の1羽", 54, WHITE), ("産卵から42日", 100, YEL), ("/1万個", 44, WHITE)], 960, 330, pad=(46, 22), border=YEL)


def sc_c5_in4718(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 110, 1810, 600)
    x0, x1, yc = BX0, BX1, 300
    egg_band(ctx, x0, x1, yc, lambda i, f: (GOLD, 1.0) if abs(f - 0.5) < 0.011 else (mix("#fffaf0", sorted_colfn()(i, f)[0], 0.8), 1.0))
    band_mark(ctx, x0, x1, yc, 0.5, a=1.0, up=70, down=60)
    tx(ctx, "/1万個", 1650, 175, 44, "#41567c")
    a = fade(t, Sk("c5_4718", 0.2), 0.5)
    bracket(ctx, px_of(F2, x0, x1), px_of(F3, x0, x1), 440, C_3W, a)
    Cd(ctx, t, "c5_4718", 0.3, [("巣立って3週間以内", 48, WHITE), ("4,718羽の中の1羽", 70, YEL)], 1040, 740, pad=(44, 20), border=YEL)


def sc_c5_autumn(ctx, t):
    sky(ctx, t, "autumn")
    flock(ctx, t, 8, 0, W_, 230, 620, 126, seed=9, spd=140.0)


def sc_c5_worst(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    chart_card(ctx, 110, 90, 1810, 880)
    bx = ((150, 670), (700, 1220), (1250, 1770))
    heads = ("最悪", "中央値", "最良")
    for k in range(3):
        wa._set(ctx, CREAM)
        wa.rrect(ctx, bx[k][0], 150, bx[k][1] - bx[k][0], 690, 22)
        ctx.fill()
        tx(ctx, heads[k], (bx[k][0] + bx[k][1]) / 2, 220, 60, DARKTXT)
    cx = [(a + b) / 2 for a, b in bx]
    a1 = fade(t, Sk("c5_worst", 0.35), 0.4)
    tx(ctx, "巣立つ前に巣ごと失敗", cx[0], 360, 42, DARKTXT, a=a1)
    tx(ctx, f"{N_FAIL:,}個", cx[0], 480, 100, ORANGE_TXT, a=a1)
    tx(ctx, "/1万個", cx[0], 580, 44, "#41567c", a=a1)
    a2 = fade(t, Sk("c5_best", 0.3), 0.4)
    tx(ctx, "42日", cx[1], 440, 130, ORANGE_TXT, a=a2)
    tx(ctx, "/1万個", cx[1], 560, 44, "#41567c", a=a2)
    tx(ctx, "最長", cx[2], 330, 46, DARKTXT, a=a2)
    tx(ctx, f"{MAX_YEARS:.1f}年", cx[2], 430, 96, ORANGE_TXT, a=a2)
    a3 = fade(t, Sk("c5_best", 0.65), 0.4)
    tx(ctx, "最多", cx[2], 560, 46, DARKTXT, a=a3)
    tx(ctx, f"ヒナ{MAX_KIDS}羽", cx[2], 650, 80, ORANGE_TXT, a=a3)
    tx(ctx, "（つがいで）", cx[2], 740, 40, "#41567c", a=a3)


def sc_c5_b2(ctx, t):
    sky(ctx, t, "day")
    wires(ctx)
    pole(ctx, 90, 330)
    x = 620
    wa._set(ctx, C_LIVE, 0.85)
    ctx.set_line_width(10)
    ctx.arc(x + 6, wire_y(x) - 190, 235, 0, 2 * math.pi)
    ctx.stroke()
    draw_swallow(ctx, x, wire_y(x) + 2 + bob(t, 2, 1.3), 380, pose="perch")
    stack(ctx, t, 1400, 100, [
        ("c5_b2", 0.4, [("春まで生きた1,075羽の", 46, WHITE), ("中央値の1羽", 60, YEL), ("（試算の中の実在の1羽）", 42, WHITE)], dict(pad=(40, 18), border=YEL)),
        ("c5_pick2", 0.3, [("子育て2回・ヒナ9羽・", 46, WHITE), ("生きた日数が中央値に近い", 46, WHITE), ("/1,075羽", 40, WHITE)], dict(pad=(40, 18), border=YEL)),
    ])
    ta = Sk("c5_base2", 0.3)
    a_old, a_new = out_fade(t, ta, 0.2), fade(t, ta + 0.3, 0.3)
    if a_old > 0.003:
        panel(ctx, [("/1万個", 44, WHITE)], 1690, 860, a=a_old, pad=(24, 10), bg="#2c4a73", r=14)
    if a_new > 0.003:
        panel(ctx, [("/1,075羽", 44, WHITE)], 1690, 860, a=a_new, pad=(24, 10), bg="#2c4a73", r=14)


def beam_view(ctx, t):
    """梁の上の巣（殻の割れ目から見える）"""
    band(ctx, "#e9dcc0", 0, H_)
    band(ctx, "#cdbfa6", 0, H_, x0=1200)
    wa._set(ctx, "#6f5236")
    wa.rrect(ctx, 120, 620, 1700, 90, 12)
    ctx.fill()
    wa._set(ctx, "#a98763")
    wa.rrect(ctx, 120, 620, 1700, 28, 12)
    ctx.fill()
    wa._set(ctx, wa.MUD)
    wa.ell(ctx, 960, 560, 330, 110)
    ctx.fill()
    wa._set(ctx, wa.MUD_D)
    wa.ell(ctx, 960, 530, 270, 60)
    ctx.fill()


def sc_c5_shell2(ctx, t):
    shell_inside(ctx, t, glow=0.3, drift=1.0, p=ease(seg(t, SC_START["c5_shell2"] + 0.6, Sk("c5_noeave2", 0.7))) * 0.9)
    Cd(ctx, t, "c5_noeave2", 0.45, R("軒下以外の場所", sz=60, col=YEL), 1500, 170, pad=(44, 20), border=YEL)


def sc_c5_sib2(ctx, t):
    nest_wall_view(ctx, t, 2)
    shell_frame(ctx, 700, 410)
    Cd(ctx, t, "c5_3rd", 0.3, R("3個のうち3番目", sz=56, col=YEL), 1500, 170, pad=(44, 20), border=YEL)


def waves_view(ctx, t, hor=430, wing=True):
    band(ctx, "#bfe0f0", 0, hor)
    band(ctx, "#e6f3f8", hor - 160, hor)
    disc(ctx, 1300, hor - 40, 90, "#fff0b8", 0.9)
    band(ctx, "#3f86b5", hor, H_)
    rnd = random.Random(4)
    for k in range(40):
        z = ((k / 40.0) + t * 0.12) % 1.0           # 手前へ流れる波の線
        y = hor + 14 + (H_ - hor) * z * z
        w = 60 + 500 * z * z
        x = rnd.uniform(0, W_)
        wa._set(ctx, "#a8d6ee", 0.55)
        ctx.set_line_width(2 + 8 * z)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x - w / 2, y)
        ctx.line_to(x + w / 2, y)
        ctx.stroke()
    if wing:
        wing_tips(ctx, t)


def sc_c5_sea(ctx, t):
    waves_view(ctx, t)


def palm(ctx, x, y, h, sway=0.0):
    wa._set(ctx, "#7a5a3a")
    ctx.set_line_width(h * 0.07)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y)
    ctx.curve_to(x + h * 0.05, y - h * 0.4, x + h * 0.02 + sway, y - h * 0.7, x + sway, y - h)
    ctx.stroke()
    wa._set(ctx, "#2f8a4a")
    for ang in (-2.6, -2.1, -1.6, -1.0, -0.5, 0.0, -3.1):
        ex = x + sway + math.cos(ang) * h * 0.55
        ey = y - h + math.sin(ang) * h * 0.3 + h * 0.12
        ctx.move_to(x + sway, y - h)
        ctx.curve_to(x + sway + math.cos(ang) * h * 0.25, y - h - h * 0.2, ex, ey - h * 0.1, ex, ey + h * 0.1)
        ctx.curve_to(ex, ey, x + sway + math.cos(ang) * h * 0.25, y - h - h * 0.05, x + sway, y - h)
        ctx.fill()


def sc_c5_south(ctx, t):
    """南の国を上から見下ろす（田んぼ・川・小さなヤシ・強い日ざし）。翼の先が端に入る"""
    band(ctx, "#86c25e", 0, H_)
    rnd = random.Random(12)
    band(ctx, "#dce8bd", 0, H_)                          # あぜ道（細い薄い線になる地色）
    cols = ("#5fa84a", "#8fcb62", "#b2d86c")
    ctx.save()
    ctx.translate(960, 540)
    ctx.rotate(-0.175)                                   # 川の向きにそろえる
    for gi in range(-9, 10):
        for gj in range(-7, 8):
            wa._set(ctx, cols[(gi * 3 + gj * 5) % 3])
            wa.rrect(ctx, gi * 244, gj * 164, 232, 152, 6)
            ctx.fill()
            wa._set(ctx, "#3f7f3a", 0.9)
            ctx.set_line_width(4)
            wa.rrect(ctx, gi * 244 + 2, gj * 164 + 2, 228, 148, 6)
            ctx.stroke()
    ctx.restore()
    wa._set(ctx, "#6bb4d6")                              # 川
    ctx.set_line_width(70)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-50, 780)
    ctx.curve_to(500, 520, 900, 900, 1980, 420)
    ctx.stroke()
    for k in range(9):                                   # 小さなヤシ（上から見た星形）
        x, y = rnd.uniform(80, W_ - 80), rnd.uniform(80, 880)
        wa._set(ctx, "#2f8a4a")
        for q in range(7):
            ang = 2 * math.pi * q / 7 + 0.3 * math.sin(t * 0.8 + k)
            ctx.move_to(x, y)
            ctx.curve_to(x + math.cos(ang) * 22, y + math.sin(ang) * 22 - 8, x + math.cos(ang) * 40, y + math.sin(ang) * 40, x + math.cos(ang + 0.2) * 52, y + math.sin(ang + 0.2) * 52)
            ctx.curve_to(x + math.cos(ang - 0.2) * 30, y + math.sin(ang - 0.2) * 30, x, y, x, y)
            ctx.fill()
    for x, y in ((420, 250), (1250, 780), (1600, 560)):  # 小さな家
        wa._set(ctx, "#c98a3c")
        wa.rrect(ctx, x, y, 50, 36, 6)
        ctx.fill()
        wa._set(ctx, "#8a4a22")
        wa.rrect(ctx, x - 4, y - 8, 58, 16, 6)
        ctx.fill()
    for r_, al in ((700, 0.12), (450, 0.18), (260, 0.28)):   # 強い日ざし
        wa._set(ctx, "#fff2b0", al)
        wa.ell(ctx, 1600, 150, r_ * 1.3, r_)
        ctx.fill()
    wing_tips(ctx, t)
    Cd(ctx, t, "c5_winter", 0.5, [("東南アジア", 46, WHITE)], 300, 100, pad=(30, 12), bg="#27518a")


def sc_c5_spring(ctx, t):
    u = ease(seg(t, SC_START["c5_spring"], SC_END["c5_spring"]))
    band(ctx, "#cfe8f4", 0, 480)
    band(ctx, "#b6dc96", 480, H_)
    drift_cloud(ctx, t, 500, 140, 90, 14.0)
    band(ctx, "#8a8f98", 640, 700)
    for k in range(5):                                      # 遠い家々
        x = 100 + k * 380
        wa._set(ctx, "#f2e6cc")
        ctx.rectangle(x, 500, 180, 100)
        ctx.fill()
        wa._set(ctx, ("#c9683c", "#5b7fa8", "#8c6b9a")[k % 3])
        ctx.move_to(x - 15, 500)
        ctx.line_to(x + 90, 430)
        ctx.line_to(x + 195, 500)
        ctx.close_path()
        ctx.fill()
    for x, y in ((300, 400), (1500, 380), (1100, 430)):     # 桜
        wa._set(ctx, "#f6c6d2")
        wa.ell(ctx, x, y, 110, 70)
        ctx.fill()
    # 近づいてくる自分の家
    sc = 0.3 + 0.8 * u
    ctx.save()
    ctx.translate(960, 700)
    ctx.scale(sc, sc)
    wa.house_far(ctx, -300, 300, -200)
    wa.window(ctx, -220, -110, 140, 190)
    wa.window(ctx, 80, -110, 140, 190)
    ctx.restore()
    wing_tips(ctx, t, a=1.0 if u < 0.7 else 0.0)


def draw_chick_top(ctx, x, y, s, beak=0.0, a=1.0):
    """真上から見たヒナ（体は丸・頭・黄色い口）"""
    def body():
        wa._set(ctx, wa.NAVY_Y)
        wa.ell(ctx, x, y, s * 0.5, s * 0.62)
        ctx.fill()
        wa._set(ctx, "#c9b5a0")
        ctx.arc(x, y - s * 0.55, s * 0.3, 0, 2 * math.pi)
        ctx.fill()
        wa._set(ctx, "#d9573f")
        wa.ell(ctx, x, y - s * 0.86, s * (0.2 + 0.1 * beak), s * (0.1 + 0.12 * beak))
        ctx.fill()
        wa._set(ctx, "#f3c34e")
        wa.ell(ctx, x, y - s * 0.86, s * (0.3 + 0.1 * beak), s * (0.17 + 0.12 * beak))
        ctx.stroke()
        wa._set(ctx, "#2b2230")
        ctx.arc(x - s * 0.13, y - s * 0.6, s * 0.035, 0, 2 * math.pi)
        ctx.arc(x + s * 0.13, y - s * 0.6, s * 0.035, 0, 2 * math.pi)
        ctx.fill()
    wa._grp(ctx, a, body)


def sc_c5_nestview(ctx, t):
    """自分の巣の中のヒナを上から見下ろす（1回目4羽→2回目5羽）"""
    band(ctx, "#e9dcc0", 0, H_)
    wa._set(ctx, wa.MUD)
    wa.ell(ctx, 960, 560, 800, 480)
    ctx.fill()
    wa._set(ctx, wa.MUD_L, 0.9)
    ctx.set_line_width(16)
    wa.ell(ctx, 960, 560, 790, 470)
    ctx.stroke()
    wa._set(ctx, "#5e402f")
    wa.ell(ctx, 960, 560, 650, 380)
    ctx.fill()
    t2 = Sk("c5_kids2", 0.55)
    if t < t2:
        pos = [(420, 610), (780, 590), (1140, 610), (1500, 590)]   # 2026-11-08 真ん中の2羽の間を空ける
        a = 1.0 - ease(seg(t, t2 - 0.4, t2))
    else:
        pos = [(380, 610), (670, 590), (960, 610), (1250, 590), (1540, 610)]
        a = ease(seg(t, t2, t2 + 0.5))
    for k, (x, y) in enumerate(pos):
        draw_chick(ctx, x, y + 160, 500 if t < t2 else 440, grow=0.7, beak=0.7 + 0.3 * math.sin(t * 5 + k * 1.3), a=a, facing=1)   # みな同じ向き（向かい合うと重なって見える）
    stack(ctx, t, 330, 120, [("c5_kids2", 0.2, [("4羽", 90, YEL)], dict(pad=(36, 12), border=YEL))])
    stack(ctx, t, 1600, 120, [("c5_kids2", 0.55, [("5羽", 90, YEL)], dict(pad=(36, 12), border=YEL))])
    Cd(ctx, t, "c5_pair9", 0.05, R("合わせて9羽（つがいで）", sz=60), 960, 880, pad=(44, 20), border=YEL)


def sc_c5_fadeend(ctx, t):
    wh = ease(seg(t, Sk("c5_end2", 0.3), Ek("c5_end2") + 0.8)) * 0.97
    waves_view(ctx, t)
    if wh > 0.003:
        wa._set(ctx, "#ffffff", wh)
        ctx.rectangle(0, 0, W_, H_)
        ctx.fill()
    Cd(ctx, t, "c5_708", 0.3, [("産卵から708日", 56, WHITE), ("（約2年）", 100, YEL), ("/1,075羽の", 40, WHITE), ("中央値の1羽", 40, WHITE)], 960, 400, pad=(40, 20), border=YEL)


# ============================================================
# 6 まとめ
# ============================================================
C6_X = (255, 725, 1195, 1665)
C6_ROWS = [[("巣立つのは", 44, WHITE), ("6,855羽", 64, YEL), ("/1万個", 40, WHITE)],
           [("巣立ち後", 44, WHITE), ("3週間で", 44, WHITE), ("いちばん減る", 44, YEL)],
           [("5羽の巣の", 44, WHITE), ("中央値は", 44, WHITE), ("1羽", 70, YEL)],
           [("春まで生きたら", 44, WHITE), ("約2年・ヒナ9羽", 50, YEL), ("/1,075羽", 40, WHITE)]]


def sc_c6_answers(ctx, t):
    sky(ctx, t, "day", hor=820)
    wa.house_far(ctx, 0, 1000, 520)
    t0 = ch_start(6) + T_TITLE[6]
    for k, rows in enumerate(C6_ROWS):
        a = fade(t, t0 + 0.2 + 0.4 * k)
        if a <= 0.003:
            continue
        lit = (k == 1 and Sk("c6_8d", 0.0) <= t < Sk("c6_2y", 0.0)) or (k == 3 and t >= Sk("c6_2y", 0.0))
        panel(ctx, rows, C6_X[k], 250, a=a, pad=(28, 18), border=YEL if lit else None)
    Cd(ctx, t, "c6_8d", 0.3, [("中央値の1羽", 44, WHITE), ("42日", 90, YEL)], 1500, 650, t1=Sk("c6_tenth", 0.0), pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_tenth", 0.3, [("春までたどり着けたのは", 44, WHITE), ("1,075羽 /1万個", 64, YEL)], 1450, 650, pad=(40, 16), border=YEL)


def sc_c6_close(ctx, t):
    eave_parent(ctx, t)
    Cd(ctx, t, "c6_last", 0.4, [("春に軒下で見かける親のツバメ", 46, WHITE), ("約1割の1羽", 100, YEL)], 1400, 560, pad=(44, 20), border=YEL)


END_SUB = ["よければ", "チャンネル登録・高評価", "お願いします"]


def end_rows():
    return [("5羽の巣の中央値", "1羽"), ("中央値の1羽", "42日"), ("春まで生きた1羽", "約2年・ヒナ9羽")]


def sc_end(ctx, t):
    sky(ctx, t, "warm", hor=900, clouds=False)
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    panel(ctx, [("答え", 80, YEL)], 490, 95, a=b, pad=(44, 8), r=20)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 46, WHITE), (val, 70, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        a = fade(t, t9 + 0.1, 0.4)
        wire_line(ctx, 1000, 800, 1920, 780, 12, a=a)
        draw_swallow(ctx, 1300, 800 + 0, 420, pose="perch", a=a)
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1480, 300, a=fade(t, t9 + 0.3, 0.4))


# ============================================================
# 区切り（ここまで／ここから・小さなツバメが電線の上を歩く）。engine/longkit.py の Eyecatch を、平たい地・白と黄色の文字で描き直したもの
# ============================================================
EC_LEFT = ("巣立つのは6,855羽", "巣立ち後3週間でいちばん減る", "5羽の巣の中央値は1羽")
EC_RIGHT = ("春まで生きた1,075羽の一生", "中央値の1羽")
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
        wire_line(ctx, 0, 905, 1920, 905, 0.0, w=6)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:                                      # 足あと（電線の上の小さな点）
                ctx.set_source_rgba(1, 1, 1, 0.35 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, 905 + (10 if i % 2 else -10), 6, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        tr = t - self.t0
        hop = abs(math.sin(tr * 6.0)) * 9
        draw_swallow(ctx, x, 903 - hop, 150, pose="perch", facing=1)


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
    if PACE_TRIAL:
        k_ = spec[2:] if spec.startswith("z:") else spec
        if k_ in ANCH and k_.startswith(TRIAL_CH):
            return Sk(k_) - trial_lead(k_)
    if spec.startswith("z:"):
        return bz(spec[2:])
    return bd(spec)


def _end_of(j):
    name, spec, _f = SC_TABLE[j]
    if name == "end":
        return DUR + 2.0
    nname, nspec, _ = SC_TABLE[j + 1]
    if name == "c3_dist":
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
        if Sk("c0_ans3", 0.0) <= t < SC_END["c0_prob"]:
            corner_card(ctx, t)
    if ea > 0.003:
        EC.draw(ctx, t)
    if sub:
        lf.subtitle(ctx, t, tl)




# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・結果の数字・区切りの足音）
# ============================================================
def step_pop(seed=0, high=False):
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    return tone * env * 0.8


BELLS = [Sk("c1_ans", 0.62), Sk("c2_ans", 0.5), Sk("c3_med", 0.45), Sk("c4_life", 0.5), Sk("c5_42", 0.5)]


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, _bgm(DUR, lf.SR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for n in range(1, LAST_CH + 1):
        mx.add(S(f"ch{n}"), whoosh(0.6), 0.3)
    if EC:
        for i_, ts_ in enumerate(EC.step_times()):
            mx.add(ts_, step_pop(seed=i_, high=bool(i_ % 2)), 0.32)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(Sk("c6_last", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(T_ES + 0.3, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（要所8枚）
# ============================================================
def still_list():
    return [
        ("1_open", "0:02 問い（5羽・何羽）", 2.0),
        ("2_egg", "約束の卵", Sk("c0_one", 0.9)),
        ("3_c1_ans", "問い1の答え 6,855羽", Sk("c1_ans", 0.95)),
        ("4_c2_bars", "問い2 4,718羽の棒", Sk("c2_most", 0.9)),
        ("5_c3_cmp", "問い3 渡りのほうが危ない？", Sk("c3_guess", 0.95)),
        ("6_c3_dist", "冒頭の答え 0羽43%・中央値1羽", Sk("c3_med", 0.95)),
        ("7_c4_hist", "問い4 ヒナの数 0〜56羽", Sk("c4_gap", 0.95)),
        ("8_c5_42", "中央値の1羽 42日", Sk("c5_42", 0.95)),
        ("9_c5_708", "春まで生きた中央値の1羽 708日", Sk("c5_708", 0.95)),
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




WATCH = ["軒下", "巣立ち", "巣立って", "足環", "越冬", "中央値", "何羽", "1羽", "3羽", "6羽", "8羽", "10羽", "つがい", "渡り", "東南アジア", "山階鳥類研究所",
         "日本野鳥の会", "環境省", "一戸建て", "天敵", "発信機", "約6羽に1羽", "5羽"]


# ============================================================
# 絵の出る時刻の記録（visual_lag 用）: 枠は声の0.5秒前までに・答えは声に合わせる
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
    _fr("円グラフの枠(巣の場所)", "c1_pie", "c1_pie"), _fr("帯の枠(巣ごと失敗)", "c1_band1", "c1_band1"), _fr("帯の枠(巣立てず)", "c1_band2", "c1_nofl"),
    _fr("帯の枠(3週間を越えた)", "c2_band", "c2_band"), _fr("棒の枠(巣ごと失敗との比べ)", "c2_bars", "c2_x2"), _fr("並べた帯の枠(生きた日数の順)", "c2_sort", "c2_sort"),
    _fr("地図の枠(東南アジア)", "c3_map", "c3_aki"), _fr("帯の枠(春まで生きた)", "c3_band", "c3_band"), _fr("棒の枠(3週間と渡りの比べ)", "c3_cmp", "c3_cmp"),
    _fr("5羽の巣の棒グラフの枠", "c3_dist", "c3_count"), _fr("帯の枠(1,075羽を抜き出す)", "c4_base", "c4_base"), _fr("帯の枠(1,075羽の寿命)", "c4_band", "c4_sorted"),
    _fr("ヒナの数の棒グラフの枠", "c4_hist", "c4_vary"), _fr("ヒナの数の棒グラフの枠(2回目)", "c4_hist2", "c4_20"), _fr("帯の枠(最長)", "c4_long", "c4_long"),
    _fr("帯の枠(中央値の卵に印)", "c5_band", "c5_sel"), _fr("3つの枠(最悪・中央値・最良)", "c5_worst", "c5_worst0"),
    _val("札「2,165個」", "c1_band1", 0.55), _val("札「980個」", "c1_nofl", 0.55), _val("札「6,855羽」", "c1_ans", 0.55), _val("札「2,137羽」", "c2_band", 0.55),
    _val("札「4,718羽」", "c2_dead", 0.3), _val("札「約3割」", "c2_3wari", 0.45), _val("札「約51%」", "c3_51", 0.45), _val("札「1,075羽」", "c3_band", 0.55),
    _val("札「43%」", "c3_zero", 0.7), _val("札「中央値1羽」", "c3_med", 0.55), _val("札「約2年」", "c4_life", 0.45), _val("札「ヒナ9羽」", "c4_kids", 0.45),
    _val("札「産卵から42日」", "c5_42", 0.3), _val("札「産卵から708日」", "c5_708", 0.3),
]


NUM_RE = r"\d[\d,]*(?:\.\d+)?"
WARNS = []
SCENE_MIN = 3.0
STILL_MAX = 15.0
STILL_THR = 0.005


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




def _allowed_nums():
    md = NARR_PATH.read_text(encoding="utf-8")
    md = md[md.index("## 0"):]
    ok = {float(m.replace(",", "")) for m in _re.findall(NUM_RE, md)}
    ok |= set(float(x) for x in range(0, 61))                      # 問いの番号・目盛り・区間の端
    ok |= {float(NB), float(N_FAIL), float(N_NOFL), float(N_FLEDGED), float(N_3W_OK), float(N_3W_DEAD), float(N_BACK), float(N_MIG_DEAD)}
    return ok


def scene_checks(frames=None):
    txt = lambda k: split_reading(tl.clip(ID[k]).text)[0]
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本 ----
    A(f"台本: 章は{len(CHAPS)}つ（0〜{LAST_CH}）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 7 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない・読みの補正は空（台本の {表記|よみ} を使う）", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()) and not READ_FIX)
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S("c0_0"), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:])]
    okg = [0.3] + [trial_gap(k_) for k_ in ANCH if k_.startswith("c0_")] if PACE_TRIAL else [0.3]
    A(f"台本: 冒頭（第0章）の文と文の間は 0.3秒か場面の切りかえの間（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし",
      all(any(abs(g - o) < 0.011 for o in okg) for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch1"))
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
    A(f"区切り: 問い3（第3章）のあと・問い4（第4章）の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(last3) - 1e-6 and abs(T_RS1 - S("ch4")) < 1e-6 and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    pos = (T_RS0 + T_RS1) / 2 / DUR
    A(f"区切り: 動画の {pos:.1%} のところ（30〜75%）・声の行なし", 0.30 <= pos <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 小さなツバメは左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ進む・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    # ---- 冒頭 ----
    nums0 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and it.id.startswith("c0_"):
            nums0 |= set(_re.findall(r"\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭（第0章）の声の数字は2個以内（{sorted(nums0)}）", len(nums0) <= 2)
        # ---- 声の数字 = 試算（sims/tsubame_rough.py）----
    P = lambda x: ihalf(100 * x)
    exp = [("c1_band1", f"{N_FAIL:,}個"), ("c1_nofl", f"{N_NOFL}個"), ("c1_ans", f"{N_FLEDGED:,}羽"), ("c2_band", f"{N_3W_OK:,}羽"), ("c2_dead", f"{N_3W_DEAD:,}羽"),
           ("c2_3wari", "約3割"), ("c3_51", "約51%"), ("c3_band", f"{N_BACK:,}羽"), ("c3_4718", f"{N_3W_DEAD:,}羽"), ("c3_1062", f"{N_MIG_DEAD:,}羽"),
           ("c3_six", f"約{ihalf(N_FLEDGED / N_BACK)}羽に1羽"), ("c3_zero", f"{P(NEST5[0])}%"), ("c3_rest", f"1羽の巣が{P(NEST5[1])}%"), ("c3_rest", f"2羽の巣が{P(NEST5[2])}%"),
           ("c3_rest", f"以上の巣は{P(sum(NEST5[3:]))}%"), ("c4_tenth", "約1割"), ("c4_49", "約49%"), ("c4_life", f"約{ihalf(BACK_MED / tr.YEAR)}年"), ("c4_brood", f"{int(BROODS_MED)}回"),
           ("c4_kids", f"{int(KIDS_MED)}羽"), ("c4_zero", f"{N_KID0}羽、{P(N_KID0 / N_BACK)}%"), ("c4_20", f"{N_KID20}羽、{P(N_KID20 / N_BACK)}%"), ("c4_max", f"{MAX_KIDS}羽"),
           ("c4_long", f"{MAX_YEARS:.1f}年"), ("c5_grow", f"約{EGG_PERIOD}日"), ("c5_8d", f"約{ihalf(MED_DAYS - EGG_PERIOD)}日"), ("c5_42", f"{ihalf(MED_DAYS)}日"),
           ("c5_4718", f"{N_3W_DEAD:,}羽"), ("c5_worst", f"{N_FAIL:,}個"), ("c5_best", f"{MAX_YEARS:.1f}年"), ("c5_708", f"{ihalf(MED2['days'])}日"),
           ("c5_kids2", f"1回目は{MED2['log'][0][1][0]}羽、2回目は{MED2['log'][0][1][1]}羽"), ("c6_8d", f"約{ihalf(MED_DAYS - EGG_PERIOD)}日"), ("c6_tenth", "約1割")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が試算（tsubame_rough.py）の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A(f"試算: 卵 {NB} 個・巣ごと失敗 {N_FAIL}・巣立てず {N_NOFL}・巣立った {N_FLEDGED}・3週間を越えた {N_3W_OK}・春まで {N_BACK}・渡りと冬で {N_MIG_DEAD}",
      (NB, N_FAIL, N_NOFL, N_FLEDGED, N_3W_OK, N_BACK, N_MIG_DEAD, N_3W_DEAD) == (10000, 2165, 980, 6855, 2137, 1075, 1062, 4718))
    A(f"試算: 5羽の巣 {[P(v) for v in NEST5_SHOW]}%・2羽以上 {P(sum(NEST5[2:]))}%・中央値の1羽 {MED1['days']:.1f}日・春まで生きた1羽 {MED2['days']:.1f}日・ヒナの数の合計 {sum(KID_COUNTS)}",
      [P(v) for v in NEST5_SHOW] == [43, 40, 15, 3] and P(sum(NEST5[2:])) == 18 and ihalf(MED1["days"]) == 42 and ihalf(MED2["days"]) == 708 and sum(KID_COUNTS) == N_BACK)
    A(f"試算: 中央値の1羽は {MED1['stage']}・{MED1['place']}・軒下 {MED1['eaves']}・{MED1['sex']}・卵 {MED1['clutch']}個の{MED1['order']}番目／春まで生きた1羽は軒下 {MED2['eaves']}・{MED2['sex']}・卵 {MED2['clutch']}個の{MED2['order']}番目・子育て {MED2['log']}",
      MED1["stage"] == "巣立って3週間以内" and MED1["eaves"] and MED1["sex"] == "オス" and MED1["clutch"] == 5 and MED1["order"] == 3
      and (not MED2["eaves"]) and MED2["sex"] == "オス" and MED2["clutch"] == 3 and MED2["order"] == 3 and MED2["log"] == [(1, [4, 5])])
    A(f"試算: 確率の値は声の「約3割・約51%・約49%」と同じ（{tr.POST_FLEDGE_3W}・{tr.FIRST_NONBREED}・{tr.ADULT_NONBREED}）", P(tr.POST_FLEDGE_3W) == 32 and P(tr.FIRST_NONBREED) == 51 and P(tr.ADULT_NONBREED) == 49)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件 {[b[0] for b in bad[:4]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面の切りかえ: 文の途中で場面が替わらない（{mid_sc[:3]}）", not mid_sc)
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
        A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
        qf = [(t_, e) for t_, e in allt if e[0] == Q_TXT]
        q_first = min((t_ for t_, _e in qf), default=99.0)
        q_ok = bool(qf) and all(e[5] >= 40 and e[4] < 130 for _t, e in qf)
        A(f"冒頭: 上の小さな札「{Q_TXT}」が {q_first:.2f}秒から出る（40px 以上・画面の上 y<130 で飛ぶ道すじにかけない）", 0.9 <= q_first <= 1.3 and q_ok)
        A(f"冒頭: 声は0.5秒から「あなた」（{S('c0_0'):.1f}秒）・「5羽」（{S('c0_1'):.1f}秒）が5秒以内", S("c0_1") < 5.0 and "あなた" in txt("c0_you") and "5羽" in txt("c0_bro"))
        t_land_ = SC_START["open"] + 0
        o_first = min((t_ for t_, e in allt if e[0] in OPTS), default=0.0)
        fl_end = Sk("c0_out", 0.15) + 1.0 + FLY_STAG * 4 + FLY_DUR
        A(f"冒頭: 選択肢の札「4羽」「2羽」「1羽」は飛行が終わってから（{fl_end:.1f}秒）出る（初出 {o_first:.1f}秒）・声では言わない",
          o_first >= fl_end - 1e-6 and not any("4羽" in split_reading(LINES[i][1])[0] for i in LINES if LINES[i][0] == 0))
        big_ = [e[0] for t_, e in allt if t_ < fl_end and 1.0 <= t_ and e[5] > 60 and not e[0].startswith("字幕") and e[0] != "5羽" and t_ > Sk("c0_out", 0.15)]
        A(f"冒頭: 飛んでいる間（{Sk('c0_out', 0.15):.1f}〜{fl_end:.1f}秒）は大きな札（60px超）を出さない: {sorted(set(big_))}", not big_)
        tokens = [("2,165個", "c1_band1"), ("980個", "c1_nofl"), ("6,855羽", "c1_ans"), ("2,137羽", "c2_band"), ("4,718羽", "c2_dead"), ("約51%", "c3_51"),
                  ("1,075羽", "c3_band"), ("1,062羽", "c3_1062"), ("43%", "c3_zero"), ("40%", "c3_rest"), ("15%", "c3_rest"), ("3%", "c3_rest"), ("18%", "c3_two"),
                  ("約49%", "c4_49"), ("2回", "c4_brood"), ("9羽", "c4_kids"), (f"{N_KID0}羽（{ihalf(100 * N_KID0 / N_BACK)}%）", "c4_zero"),
                  (f"{N_KID20}羽（{ihalf(100 * N_KID20 / N_BACK)}%）", "c4_20"), (f"最多 {MAX_KIDS}羽", "c4_max"), ("産卵から42日", "c5_42"), ("産卵から708日", "c5_708")]
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
            print(f"  画面の数字 {v} が台本・試算の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて台本（札の指示を含む）か試算の値: 余分 {len(extra)}個 {list(extra)[:5]}", not extra)
        bad_words = sorted({e[0] for t_, e in allt if any(w in e[0] for w in ("襲", "食べ", "血", "殺", "倒れ", "死ぬ", "死んだ", "戻ってくる", "戻る"))})
        A(f"画面に「襲」「血」「殺」「倒れ」や言い切らない言い方（戻ってくる）の文字を出さない: {bad_words}", not bad_words)
        short_t = _check_long_mod().short_texts(frames)
        for a_, b_, s_, need_ in short_t[:16]:
            print(f"  札の表示時間 {_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒／要 {need_:.1f}秒 「{s_[:30]}」")
        A(f"札の表示時間: 画面の文字は「文字数÷8＋1秒」以上出る（字幕・カウンターは除く）: 足りない {len(short_t)} 件", not short_t)
        # 国が替わる所の右下の札（40px 以上・画面の右下）
        ct = sorted({(e[0], round(e[5])) for t_, e in allt if e[0].endswith("の記録") or "の記録（" in e[0]})
        ct_small = [c for c in ct if c[1] < 40]
        names3 = {n for n, _s in ct}
        A(f"国の札（日本・イギリス・スイスの記録）が出る: {sorted(names3)[:8]}・40px 未満 {ct_small}",
          any("日本の記録" in n for n in names3) and any("イギリスの記録" in n for n in names3) and any("スイスの記録" in n for n in names3) and not ct_small)
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、区切りの文字だけ: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        tes = T_ES + 0.6
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        A(f"終了画面: 最後の文のあと（{T_ES:.1f}秒〜）から最後まで（{DUR - T_ES:.1f}秒・6〜8秒）",
          6.0 <= DUR - T_ES <= 8.0 and T_ES > Ek("c6_last") - 1e-6)
        end_t = min(DUR - 0.2, T_ES + 2.0)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A(f"終了画面に 答え3つ・登録の札が出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
    flat_ = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat_)
    print(f"場面の照合 {len(flat_)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat_)


def contrast_audit_run(min_ratio=4.5):
    """文字と、そのすぐ後ろの色のコントラスト（sims/contrast_audit.py の測り方。mp4 を使わず draw から直接描く）。out/whaling-long/contrast_audit.md"""
    import importlib.util
    import pickle
    spec = importlib.util.spec_from_file_location("contrast_audit", Path(__file__).resolve().parent / "contrast_audit.py")
    ca = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ca)
    frames = pickle.loads((OUT / "frames_real.pkl").read_bytes())
    first = {}
    for t, ents in frames:
        for e in ents:
            if str(e[0]).startswith("字幕: "):
                continue
            first.setdefault((e[0], round(e[1] / 20), round(e[2] / 20)), (t, e))
    by_t = {}
    for (t, e) in first.values():
        by_t.setdefault(round(t + 0.6, 2), []).append(e)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, lf.W, lf.H)
    rows, n = [], 0
    for t in sorted(by_t):
        core._LOG = None
        core._CUR_T = t
        ctx = cairo.Context(surf)
        draw(ctx, t)
        surf.flush()
        img = np.frombuffer(bytes(surf.get_data()), np.uint8).reshape(lf.H, lf.W, 4)[:, :, [2, 1, 0]]
        for e in by_t[t]:
            r = ca.measure(img, e)
            if r is None:
                continue
            n += 1
            if r[0] < min_ratio:
                rows.append((t, e[0], r[0], r[1], r[2]))
    lines = [f"# 文字のコントラスト {SLUG}", "", f"測った文字 {n}・{min_ratio}:1 未満 {len(rows)}", ""]
    for t, s_, rr, fg, bg in rows:
        lines.append(f"- {int(t // 60)}:{t % 60:04.1f} 「{str(s_)[:24]}」 {rr:.1f}:1（文字 {tuple(int(v) for v in fg)}／後ろ {tuple(int(v) for v in bg)}）")
    (OUT / "contrast_audit.md").write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print(f"{SLUG}: 測った文字 {n}・{min_ratio}:1 未満 {len(rows)}")
    for ln in lines[4:34]:
        print(ln)
    return rows


# ============================================================
# 書き出し
# ============================================================
def fig_check(step=0.25):
    """字幕が出ているコマで、字幕の帯の上端より下に人物の足（左右は身長の±18%）が来ていないかを全コマで数える"""
    global FIG_LOG
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1920, 1080)
    hits = {}
    n_fig = 0
    n = int(DUR / step)
    for i in range(n):
        t = i * step
        FIG_LOG = []
        ctx = cairo.Context(surf)
        draw(ctx, t, sub=False)
        figs, FIG_LOG = FIG_LOG, None
        n_fig += len(figs)
        s_, a_ = tl.subtitle_at(t)
        if not s_ or a_ < 0.3 or not figs:
            continue
        lines = lf.wrap_subtitle(s_)
        w = max(text_width(l_, lf.SUB_SIZE) for l_ in lines) + 72
        top = lf.SUB_Y - (len(lines) * lf.SUB_LINE_H + 24) / 2
        x0, x1 = 960 - w / 2, 960 + w / 2
        nm = next((nm_ for nm_, t0_, t1_, *_r in SCENES if t0_ <= t < t1_), "?")
        for fx, fy, fh in figs:
            if fx + 0.18 * fh > x0 and fx - 0.18 * fh < x1 and fy > top - 4:
                key = (nm, round(fx / 20) * 20, round(fy))
                hits.setdefault(key, (t, top))
    rows = sorted(hits.items(), key=lambda kv: kv[1][0])
    out = OUT / "fig_subtitle_check.md"
    lines_ = ["# 字幕の帯と人物の足もと", "", f"かぶり {len(rows)} か所（場面・人物の位置ごと）", ""]
    for (nm, fx, fy), (t, top) in rows:
        lines_.append(f"- {_ts(t)} {nm} 人物 x≈{fx} 足 y={fy}（字幕の帯の上端 {top:.0f}）")
    out.write_text(chr(10).join(lines_) + chr(10), encoding="utf-8")
    print(f"字幕の帯と鳥の足もと: かぶり {len(rows)} か所（とまった鳥・ヒナを {n_fig} 羽ぶん測定） → {out}")
    for r_ in lines_[4:30]:
        print(" ", r_)


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
    print(f"  区切り {_ts(T_RS0)}〜{_ts(T_RS1)}（{(T_RS0 + T_RS1) / 2 / DUR:.1%}）・終了画面 {_ts(T_ES)}〜")
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
            stills_sheet(OUT / "stills", still_list(), cols=4, sheet_name="stills_key_480.png")
        return
    if "--figcheck" in args:
        fig_check()
        return
    if "--contrast" in args:
        contrast_audit_run()
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
    if "--pace-trial" in args:
        import pickle
        td = OUT / "pace_trial"
        td.mkdir(parents=True, exist_ok=True)
        t_end = SC_END["c1_ans"]
        print(f"お試しの範囲: 0:00〜{_ts(t_end)}（{t_end:.1f}秒）")
        if "--render" not in args:
            return
        frames = lk.scan_frames(draw, DUR, timeline=tl)
        (td / "frames_trial.pkl").write_bytes(pickle.dumps(frames))
        scene_checks(frames)
        lf.render(draw, t_end, td / f"{SLUG}.pace_trial.mp4", build_audio(), timeline=tl)
        print("お試し完成:", td / f"{SLUG}.pace_trial.mp4")
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
