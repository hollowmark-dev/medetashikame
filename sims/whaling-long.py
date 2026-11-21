"""捕鯨船ロング「もしあなたが捕鯨船の新米なら」（横型ロング）— 2026-11-08 作成。場面（描画・声の並び・照合・静止画）。

  python -X utf8 sims/whaling-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/whaling-long.py --fake-voice --stills         要所の静止画8枚と 480px の一覧（out/whaling-long/stills/・stills_key_480.png）
  python -X utf8 sims/whaling-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/whaling-long/scene_work/）
  python -X utf8 sims/whaling-long.py --fake-voice --sheet          本編の全場面の静止画一覧（out/whaling-long/body_stills_480*.png）
  python -X utf8 sims/whaling-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/whaling-long.py --scenecheck                  本番の声で照合（frames_real.pkl を保存）

台本: publish/whaling-long/narration_B.md（文は変えない）。数字: out/whaling-long/data.json と numbers.md。
絵: sims/whaling_art.py（平塗り・輪郭線なし。あなた＝オレンジ、ほかの新米＝うすい青）。土台は sims/salmon-long.py。
本番の mp4 の書き出しはここでは行わない（--scenecheck と --stills まで）。
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

SLUG = "whaling-long"
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
# 場面の切りかえの前後の間のお試し（2026-11-08 ユーザー「切り替わりが早い」）。第0章・第1章だけ
# 2026-11-08 ユーザーOK: 全編に広げた（--pace-old で前の間に戻せる）
PACE_TRIAL = "--pace-old" not in sys.argv   # 2026-11-08 ユーザー「その間でOK」で標準に（--pace-old で前の間）
TRIAL_LEAD = 0.7   # 場面が替わってから声まで（ユーザー「後ろ側をもう少し」で 0.5→0.7）
TRIAL_TAIL = 0.6   # 声が終わってから場面が替わるまで
TRIAL_CH = ("c0_", "c1_", "c2_", "c3_", "c4_", "c5_")
# 第0章は「284ドル」を30秒以内に言う決まりがあるので 0.4＋0.4。帯の図は枠が出そろうのに時間がかかるので先に出す
TRIAL_PAIR = {"c0_": (0.6, 0.4), **{f"c{n}_": (TRIAL_LEAD, TRIAL_TAIL) for n in range(1, 6)}}
TRIAL_LEAD_KEY = {"c1_sort": 1.05, "c2_sort": 1.05, "c4_diff": 1.05, "c4_many": 1.05}   # 枠が出そろうのに時間がかかる図


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
from whaling_art import (CREW, YOU, cloud, draw_barrel, draw_boat, draw_calendar, draw_factory, draw_family,  # noqa: E402
                         draw_sailor, draw_ship, draw_spout, draw_stamp, gray_lines, paper, pay_envelope, seal, smoke, waves)
from whaling_art import _set as _wset, rrect as _wrr, text as _wtext  # noqa: E402
import whaling_art as wa  # noqa: E402

# ---- 人物の足もとの記録（字幕の帯とのかぶりを機械で測る・2026-11-08）----
FIG_LOG = None
_draw_person_orig = wa.draw_person


FEET_MAX = 925   # 人物の足もとはここより下に置かない（字幕2行の帯の上端は 934・2026-11-08 統括「人物を少し上に」）


def _lift(ctx, x, y):
    """足もとが FEET_MAX より下なら、その分だけ上げた y を返す（体と帽子を一緒に上げるため、人物を描く関数の入口で使う）"""
    dyv = ctx.user_to_device(x, y)[1]
    if dyv > FEET_MAX:
        y -= ctx.device_to_user_distance(0, dyv - FEET_MAX)[1]
    return y


def _draw_person_logged(ctx, x, y, h, *a_, **k_):
    y = _lift(ctx, x, y)
    if FIG_LOG is not None:
        dx, dy = ctx.user_to_device(x, y)
        dh = abs(ctx.user_to_device_distance(0, h)[1])
        FIG_LOG.append((dx, dy, dh))
    return _draw_person_orig(ctx, x, y, h, *a_, **k_)


wa.draw_person = _draw_person_logged
_draw_sailor_orig, _draw_family_orig = wa.draw_sailor, wa.draw_family


def draw_sailor(ctx, x, y, h, *a_, **k_):
    return _draw_sailor_orig(ctx, x, _lift(ctx, x, y), h, *a_, **k_)


def draw_family(ctx, x, y, h, *a_, **k_):
    return _draw_family_orig(ctx, x, _lift(ctx, x, y), h, *a_, **k_)


wa.draw_sailor, wa.draw_family = draw_sailor, draw_family

ANCH = {
    # 0 いくら稼げますか
    "c0_new": (0, "初めて船に乗る"), "c0_nopay": (0, "給料はありません"), "c0_lay": (0, "だいたい190分の1"), "c0_back": (0, "帰ってきたとき"),
    "c0_10k": (0, "くじで1万回引きました"), "c0_res": (0, "中央値は、284ドル"), "c0_med": (0, "ちょうど真ん中"), "c0_call": (0, "多いのか少ないのか"),
    # 1 何年で帰れる？
    "c1_yoso": (1, "1年くらいで"), "c1_day": (1, "出港のときには"), "c1_sort": (1, "短い順に並べます"), "c1_med": (1, "中央値は、約2年11か月"),
    "c1_p10": (1, "約1年9か月以内"), "c1_p90": (1, "4年以上かかりました"), "c1_follow": (1, "ちょうど真ん中のあなたを追いかけます"),
    "c1_out": (1, "あなたは港を出ます"), "c1_far": (1, "航海が長いのは"), "c1_pac": (1, "太平洋や北の海まで"), "c1_lookout": (1, "マストの上から"),
    "c1_port": (1, "途中の港で"), "c1_oil": (1, "ランプの明かり"), "c1_baleen": (1, "上あごに何百枚も"), "c1_filter": (1, "水だけを外へ出します"), "c1_use": (1, "傘の骨"), "c1_cargo": (1, "持ち帰る荷物です"), "c1_cal": (1, "カレンダーは3枚目"), "c1_ans": (1, "答えです"),
    # 2 取り分はいくら？
    "c2_yoso": (2, "陸の仕事より多いと思いませんか"), "c2_def": (2, "取り分とは、"), "c2_split": (2, "分け方の割合は"), "c2_lay": (2, "中央値で190分の1でした"),
    "c2_val1": (2, "まず、船が持ち帰った"), "c2_val2": (2, "次に、その値打ちを"), "c2_sort": (2, "小さい順に並べます"), "c2_med": (2, "中央値は、284ドルでした"),
    "c2_p10": (2, "146ドルに届きませんでした"), "c2_p90": (2, "478ドルを超えました"), "c2_month": (2, "1か月あたりに直すと"), "c2_doc": (2, "資料には、"), "c2_job": (2, "新米の仕事は"), "c2_boat": (2, "ボートをこいで"), "c2_bed": (2, "寝る所は"), "c2_food": (2, "塩漬けの肉"),
    "c2_facday": (2, "働いた日の分の給料"), "c2_ship": (2, "航海が終わるまで"),
    "c2_fac": (2, "町の工場で働いた場合と比べます"), "c2_facpay": (2, "工場の給料は"), "c2_600": (2, "約600ドルです"), "c2_half": (2, "工場の半分に届きませんでした"),
    "c2_168": (2, "168人でした"), "c2_meal": (2, "船の上では食事が出ます"), "c2_pay": (2, "食費を自分で払います"), "c2_add": (2, "足してみます"),
    "c2_noreach": (2, "食事の値打ちを足しても"), "c2_5in1": (2, "約5人に1人は"), "c2_ledger": (2, "ちょうど真ん中のあなたの帳簿を見ます"),
    "c2_left": (2, "帳簿の左には"), "c2_row": (2, "あなたの取り分の行に書かれます"), "c2_more": (2, "船が多く持ち帰るほど"), "c2_vary": (2, "乗った船で大きく変わります"),
    "c2_one": (2, "帳簿のこの1行です"), "c2_office": (2, "船に乗る前の話に戻ります"), "c2_adv": (2, "前借りをします"), "c2_advdef": (2, "前借りとは"),
    "c2_third": (2, "見込みの4分の1から3分の1"), "c2_int": (2, "利子もつきました"), "c2_fam": (2, "家族がいれば"), "c2_shop": (2, "服や道具を船から買います"),
    "c2_sub": (2, "服や道具の代金など"), "c2_before": (2, "引く前の額です"), "c2_ans": (2, "答えです"),
    # 3 最後まで乗っていられる？
    "c3_yoso": (3, "ほとんどの船は帰ってくる"), "c3_count": (3, "船の数で数えます"), "c3_log": (3, "最後にどうなったか"), "c3_1666": (3, "全部で1,666回"),
    "c3_129": (3, "129航海の船は"), "c3_13": (3, "帰らなかった船は、約13回"), "c3_why": (3, "沈没だけではありません"), "c3_82": (3, "82航海でした"),
    "c3_rest": (3, "残りは、船がこわれて"), "c3_notall": (3, "全員がいなくなったとは"), "c3_rev": (3, "逆に、船が帰っても"), "c3_reason": (3, "死亡だけではありません"),
    "c3_leave": (3, "船を降りる人や"), "c3_63": (3, "63%にあたる人"), "c3_hire": (3, "新しい乗組員を雇いました"), "c3_one": (3, "1隻の例です"), "c3_noshin": (3, "新米だけで数えた割合"),
    "c3_search": (3, "隣にいた人を探します"), "c3_sink": (3, "船が沈んだ場合を考えます"), "c3_norec": (3, "港に戻った記録を残していません"), "c3_mark": (3, "印だけが残ります"),
    "c3_nodate": (3, "帰った日のない記録"), "c3_empty": (3, "港に届きません"), "c3_row": (3, "行は空のままです"), "c3_adv": (3, "前借りしたお金を"),
    "c3_ans": (3, "答えです"), "c3_next": (3, "では、船を選べば"),
    # 4 船を選べるなら、どれに乗る？
    "c4_year": (4, "年をそろえて比べます"), "c4_ground": (4, "漁場と呼びます"), "c4_three": (4, "三つの漁場の船を比べます"), "c4_diff": (4, "漁場で違いました"),
    "c4_ind": (4, "181分の1"), "c4_pac": (4, "188分の1"), "c4_north": (4, "193分の1"), "c4_promise": (4, "大きめの取り分を約束します"),
    "c4_want": (4, "乗りたいと思いませんか"), "c4_notonly": (4, "割合だけでは"), "c4_len": (4, "持ち帰る量も"), "c4_wage": (4, "月給と呼んで"),
    "c4_answer1": (4, "答えから言います"), "c4_avg": (4, "平均で見ても"), "c4_order": (4, "この順番は同じでした"), "c4_follow": (4, "北の海の船に乗ったあなた"),
    "c4_many": (4, "油も鯨ひげも多く持ち帰りました"), "c4_barrel": (4, "バレルは"), "c4_n": (4, "2,265バレルでした"), "c4_p": (4, "1,798バレルでした"),
    "c4_i": (4, "さらに少ない量でした"), "c4_bone": (4, "鯨ひげも、"), "c4_more": (4, "多くの樽が積まれて帰ります"), "c4_win": (4, "稼げるのでしょうか"), "c4_vs": (4, "船の数がいちばん多い太平洋"),
    "c4_draw": (4, "くじで引いて比べます"), "c4_yr": (4, "港を出た年をそろえた船の中"), "c4_cmp": (4, "高いほうを勝ちとします"), "c4_10k": (4, "1万回くり返しました"),
    "c4_6": (4, "勝ったのは、約6割"), "c4_4": (4, "残りの約4割"), "c4_hit": (4, "当たりと外れがありました"), "c4_slight": (4, "少し得をします"),
    "c4_luck": (4, "運のほうが大きかった"), "c4_danger": (4, "危ない海だった"), "c4_loss": (4, "漁場ごとに比べます"), "c4_ten": (4, "10回に1回ほど"),
    "c4_small": (4, "船の数が少なくなる"), "c4_ans": (4, "答えです"),
    # 5 まとめ
    "c5_a": (5, "約3年海にいて"), "c5_b": (5, "月給はいちばん高く"), "c5_q": (5, "どの船に乗りますか"), "c5_note": (5, "記録から計算した値"), "c5_sub": (5, "チャンネル登録"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in split_reading(txt)[0]]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の並び（名前, 始まり, 描く関数の名前）。始まり: 合図のキー＝その文の頭の1.05秒前 ／ "ch:N"＝章カードのあと ／ "z:キー"＝0章（前の文の終わり）----
SC_TABLE = [
    ("open", "zero", "sc_open"), ("c0_new", "z:c0_new", "sc_c0_new"), ("c0_lay", "z:c0_lay", "sc_c0_lay"), ("c0_back", "z:c0_back", "sc_c0_back"),
    ("c0_10k", "z:c0_10k", "sc_c0_10k"), ("c0_med", "z:c0_med", "sc_c0_med"), ("c0_call", "z:c0_call", "sc_c0_call"),
    ("c1_a", "ch:1", "sc_c1_a"), ("c1_yoso", "c1_yoso", "sc_c1_yoso"), ("c1_band", "c1_sort", "sc_c1_band"), ("c1_far", "c1_far", "sc_c1_far"), ("c1_follow", "c1_follow", "sc_c1_follow"), ("c1_out", "c1_out", "sc_c1_out"),
    ("c1_lookout", "c1_lookout", "sc_c1_lookout"), ("c1_port", "c1_port", "sc_c1_port"), ("c1_sea", "c1_cargo", "sc_c1_sea"), ("c1_oil", "c1_oil", "sc_c1_oil"),
    ("c1_baleen", "c1_baleen", "sc_c1_baleen"), ("c1_filter", "c1_filter", "sc_c1_filter"), ("c1_use", "c1_use", "sc_c1_use"), ("c1_cal", "c1_cal", "sc_c1_cal"), ("c1_ans", "c1_ans", "sc_c1_ans"),
    ("c2_a", "ch:2", "sc_c2_a"), ("c2_yoso", "c2_yoso", "sc_c2_yoso"), ("c2_def", "c2_def", "sc_c2_def"), ("c2_split", "c2_split", "sc_c2_split"),
    ("c2_val", "c2_val1", "sc_c2_val"), ("c2_sort", "c2_sort", "sc_c2_sort"), ("c2_month", "c2_month", "sc_c2_month"), ("c2_job", "c2_job", "sc_c2_job"), ("c2_boat", "c2_boat", "sc_c2_boat"),
    ("c2_bed", "c2_bed", "sc_c2_bed"), ("c2_food", "c2_food", "sc_c2_food"),
    ("c2_fac", "c2_fac", "sc_c2_fac"), ("c2_facday", "c2_facday", "sc_c2_facday"), ("c2_ship", "c2_ship", "sc_c2_ship"), ("c2_facpay", "c2_facpay", "sc_c2_facpay"), ("c2_600", "c2_600", "sc_c2_600"), ("c2_168", "c2_168", "sc_c2_168"), ("c2_meal", "c2_meal", "sc_c2_meal"),
    ("c2_noreach", "c2_noreach", "sc_c2_noreach"), ("c2_5in1", "c2_5in1", "sc_c2_5in1"), ("c2_ledger", "c2_ledger", "sc_c2_ledger"),
    ("c2_more", "c2_more", "sc_c2_more"), ("c2_one", "c2_one", "sc_c2_one"), ("c2_office", "c2_office", "sc_c2_office"), ("c2_adv", "c2_advdef", "sc_c2_adv"),
    ("c2_int", "c2_int", "sc_c2_int"), ("c2_shop", "c2_shop", "sc_c2_shop"), ("c2_before", "c2_before", "sc_c2_before"), ("c2_ans", "c2_ans", "sc_c2_ans"),
    ("c3_a", "ch:3", "sc_c3_a"), ("c3_yoso", "c3_yoso", "sc_c3_yoso"), ("c3_log", "c3_log", "sc_c3_log"), ("c3_1666", "c3_1666", "sc_c3_1666"),
    ("c3_129", "c3_129", "sc_c3_129"), ("c3_why", "c3_why", "sc_c3_why"), ("c3_notall", "c3_notall", "sc_c3_notall"), ("c3_reason", "c3_reason", "sc_c3_reason"),
    ("c3_63", "c3_63", "sc_c3_63"), ("c3_hire", "c3_hire", "sc_c3_hire"), ("c3_one", "c3_one", "sc_c3_one"), ("c3_noshin", "c3_noshin", "sc_c3_noshin"), ("c3_search", "c3_search", "sc_c3_search"), ("c3_sink", "c3_sink", "sc_c3_sink"),
    ("c3_mark", "c3_mark", "sc_c3_mark"), ("c3_empty", "c3_empty", "sc_c3_empty"), ("c3_adv", "c3_adv", "sc_c3_adv"), ("c3_ans", "c3_ans", "sc_c3_ans"),
    ("c3_next", "c3_next", "sc_c3_next"),
    ("c4_a", "ch:4", "sc_c4_a"), ("c4_year", "c4_year", "sc_c4_year"), ("c4_map", "c4_three", "sc_c4_map"), ("c4_tbl", "c4_diff", "sc_c4_tbl"),
    ("c4_want", "c4_promise", "sc_c4_want"), ("c4_len", "c4_notonly", "sc_c4_len"), ("c4_wage", "c4_wage", "sc_c4_wage"), ("c4_ans1", "c4_answer1", "sc_c4_ans1"),
    ("c4_ans2", "c4_avg", "sc_c4_ans2"), ("c4_follow", "c4_follow", "sc_c4_follow"), ("c4_many", "c4_many", "sc_c4_many"), ("c4_n", "c4_n", "sc_c4_n"),
    ("c4_i", "c4_i", "sc_c4_i"), ("c4_bone", "c4_bone", "sc_c4_bone"), ("c4_win", "c4_win", "sc_c4_win"), ("c4_vs", "c4_vs", "sc_c4_vs"), ("c4_draw", "c4_draw", "sc_c4_draw"),
    ("c4_cmp", "c4_cmp", "sc_c4_cmp"), ("c4_10k", "c4_10k", "sc_c4_10k"), ("c4_hit", "c4_hit", "sc_c4_hit"), ("c4_luck", "c4_slight", "sc_c4_luck"),
    ("c4_danger", "c4_danger", "sc_c4_danger"), ("c4_loss", "c4_loss", "sc_c4_loss"), ("c4_ten", "c4_ten", "sc_c4_ten"), ("c4_small", "c4_small", "sc_c4_small"),
    ("c4_ans", "c4_ans", "sc_c4_ans"),
    ("c5_answers", "ch:5", "sc_c5_answers"), ("c5_close", "c5_q", "sc_c5_close"), ("end", "end", "sc_end"),
]

# ---- 場面の切りかえの間: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c1_p10": 1.0, "c1_p90": 1.5, "c2_p10": 0.8, "c2_p90": 1.4, "c2_noreach": 2.0, "c2_5in1": 1.8, "c4_10k": 0.8, "c4_6": 0.8, "c3_13": 0.8,
              "c2_lay": 2.2, "c2_val2": 1.6, "c3_count": 1.5, "c3_one": 1.2, "c2_pay": 0.6, "c2_fam": 1.0,
              "c4_three": 2.0, "c4_north": 1.5, "c4_wage": 1.0, "c1_out": 1.4, "c4_i": 1.5, "c4_bone": 1.6, "c4_notonly": 0.8}


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
T_ES = Sk("c5_sub") - 0.3

# ============================================================
# データ（out/whaling-long/data.json と numbers.md）
# ============================================================
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
HM, HT = RES["hist_months"], RES["hist_take"]

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
CARD_BY_N = {1: ["問い1", "何年で帰れる？"], 2: ["問い2", "取り分はいくら？"], 3: ["問い3", "最後まで乗っていられる？"],
             4: ["問い4", "船を選べるなら、", "どれに乗る？"], 5: ["まとめ"]}
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


def ch_start(n):
    return S(f"ch{n}")




# ============================================================
# 絵の道具（whaling_art.py の部品を、動きと札に合わせて並べる）
# ============================================================
YOU_H = 440           # あなた（主役）の高さ。画面の高さの約41%
GY = 960              # 人物の足もと
SUB_Y = 936           # 字幕の帯の上端（札・図の文字はこの下に置かない）
INKC = "#5a4630"


def band(ctx, col, y0, y1, a=1.0, x0=0, x1=None):
    wa._set(ctx, col, a)
    ctx.rectangle(x0, y0, (W_ if x1 is None else x1) - x0, y1 - y0)
    ctx.fill()


def disc(ctx, x, y, r, col, a=1.0):
    wa._set(ctx, col, a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def wave_scroll(ctx, t, y0, y1, n=36, size=64, seed=3, speed=-24.0, col="#8cc3dc", a=0.7):
    rnd = random.Random(seed)
    wa._set(ctx, col, a)
    ctx.set_line_width(max(3, size * 0.07))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(n):
        x0 = rnd.uniform(0, W_ + 200)
        y = rnd.uniform(y0, y1)
        s = size * rnd.uniform(0.6, 1.2)
        sp = speed * rnd.uniform(0.6, 1.4)
        x = (x0 + t * sp) % (W_ + 200) - 100
        ctx.arc(x, y + s * 0.3, s * 0.5, math.pi * 1.15, math.pi * 1.85)
        ctx.stroke()


def drift_cloud(ctx, t, x0, y, s, sp=14.0, a=0.9):
    wa.cloud(ctx, (x0 + t * sp) % (W_ + 500) - 250, y, s, a=a)


def bg_sky_sea(ctx, t, hor=560, sky="#bfe0f0", sea="#4a8fb8", wspeed=-24.0, clouds=True):
    band(ctx, sky, 0, hor)
    band(ctx, "#d8ecf4", hor - 150, hor)
    disc(ctx, 250, 190, 75, "#fff3c4")
    if clouds:
        drift_cloud(ctx, t, 700, 150, 90, 14.0)
        drift_cloud(ctx, t, 1500, 120, 70, 10.0)
    band(ctx, sea, hor, H_)
    band(ctx, "#5aa0c4", hor, hor + 70)
    wave_scroll(ctx, t, hor + 80, 900, 40, 70, 3, wspeed)


def bob(t, a=6.0, w=1.2, ph=0.0):
    return math.sin(t * w + ph) * a


def bg_harbor(ctx, t, ship=(1400, 830, 500), boat=True, barrels=True):
    bg_sky_sea(ctx, t, 560)
    if ship:
        x, y, L = ship
        draw_ship(ctx, x, y + bob(t), L)
        wave_scroll(ctx, t, y - 30, y + 20, 10, 70, 5, -30.0, a=0.9)
    if boat:
        draw_boat(ctx, 820, 810 + bob(t, 4, 1.5, 1), 210)
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    wa._set(ctx, "#8a6945", 0.6)
    ctx.set_line_width(4)
    for i in range(0, W_, 140):
        ctx.move_to(i, 898)
        ctx.line_to(i - 40, H_)
        ctx.stroke()
    if barrels:
        for bx in (1010, 1180, 1350, 1520, 1690):
            draw_barrel(ctx, bx, 975, 105, 150)


def you(ctx, t, x, y=GY, h=YOU_H, facing=1, sway=True):
    dy = math.sin(t * 1.7) * 3.0 if sway else 0.0
    draw_sailor(ctx, x, y + dy, h, you=True, facing=facing)


def crew(ctx, t, x, y=GY, h=330, facing=1, ph=0.0):
    draw_sailor(ctx, x, y + math.sin(t * 1.5 + ph) * 3.0, h, you=False, facing=facing)


def bg_deck(ctx, t, spouts=True):
    """船の上（手前に甲板、奥に海と遠くの潮吹き）"""
    band(ctx, "#cfe6f2", 0, 380)
    drift_cloud(ctx, t, 1000, 120, 85, 12.0)
    drift_cloud(ctx, t, 1650, 190, 60, 9.0)
    band(ctx, "#4d93bb", 380, 600)
    wave_scroll(ctx, t, 400, 570, 30, 60, 2, -60.0)
    if spouts:
        k = 0.5 + 0.5 * math.sin(t * 0.9)
        draw_spout(ctx, 1260, 382, 120 + 50 * k, a=0.6 + 0.35 * k)
        draw_spout(ctx, 1560, 384, 80 + 30 * (1 - k), a=0.5 + 0.4 * (1 - k))
    wa._set(ctx, "#f6f0e0")
    ctx.move_to(30, 0)
    ctx.line_to(560, 0)
    ctx.line_to(560, 380)
    ctx.curve_to(420, 420, 160, 420, 30, 380)
    ctx.close_path()
    ctx.fill()
    wa._set(ctx, "#c8d0dc")
    ctx.rectangle(30, 0, 150, 390)
    ctx.fill()
    band(ctx, "#6b4a35", 0, 700, x0=250, x1=310)
    band(ctx, "#563a29", 0, 700, x0=250, x1=268)
    band(ctx, "#6b4a35", 560, 588)
    band(ctx, "#563a29", 588, 602)
    for px in range(40, W_, 160):
        band(ctx, "#6b4a35", 560, 650, x0=px, x1=px + 22)
    band(ctx, "#a67c52", 650, H_)
    wa._set(ctx, "#8d6542")
    ctx.set_line_width(5)
    for yy in (730, 820, 910, 1000):
        ctx.move_to(0, yy)
        ctx.line_to(W_, yy)
        ctx.stroke()
    for i, yy in enumerate((650, 730, 820, 910)):
        for xx in range(i * 90 % 300, W_, 300):
            ctx.move_to(xx, yy)
            ctx.line_to(xx, yy + 80)
            ctx.stroke()


def bg_room(ctx, wall="#e8d7bd", floor="#a98763"):
    band(ctx, wall, 0, 900)
    band(ctx, "#dcc8a8", 770, 900)
    band(ctx, floor, 900, H_)
    band(ctx, "#8f6e4c", 900, 912)


def bg_office(ctx):
    band(ctx, "#efe3cc", 0, 870)
    band(ctx, "#e3d4b6", 740, 870)
    band(ctx, "#8a5e3b", 860, H_)
    band(ctx, "#74502f", 860, 874)


def mini_block(ctx, x, y, w, h, col, a=1.0, head=True):
    """人のしるし（1つで100人など）: 角丸の札に小さな頭。(x, y) = 下の真ん中"""
    wa._set(ctx, col, a)
    wa.rrect(ctx, x - w / 2, y - h, w, h, min(w, h) * 0.22)
    ctx.fill()
    if head:
        wa._set(ctx, "#ffffff", 0.55 * a)
        ctx.arc(x, y - h * 0.62, h * 0.2, 0, 2 * math.pi)
        ctx.fill()


def mini_ship(ctx, x, y, L, col="#9db7df", a=1.0):
    """船のしるし（1隻で10航海など）。(x, y) = 水面の真ん中"""
    wa._set(ctx, col, a)
    ctx.move_to(x - L * 0.5, y - L * 0.12)
    ctx.line_to(x + L * 0.5, y - L * 0.12)
    ctx.line_to(x + L * 0.32, y)
    ctx.line_to(x - L * 0.32, y)
    ctx.close_path()
    ctx.fill()
    wa._set(ctx, "#ffffff", 0.85 * a)
    ctx.move_to(x - L * 0.06, y - L * 0.16)
    ctx.line_to(x - L * 0.06, y - L * 0.6)
    ctx.line_to(x - L * 0.38, y - L * 0.16)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(x + L * 0.06, y - L * 0.16)
    ctx.line_to(x + L * 0.06, y - L * 0.5)
    ctx.line_to(x + L * 0.34, y - L * 0.16)
    ctx.close_path()
    ctx.fill()


def tkw(**kw):
    return kw


def R(*ss, sz=46, col=WHITE, first=None):
    """札の行を作る。first=行1だけ別の大きさ・色（問いの番号など）"""
    rows = [(s_, sz, col) for s_ in ss]
    if first:
        rows[0] = (ss[0], first[0], first[1])
    return rows


def Cd(ctx, t, key, f, rows, x, y, t1=None, lead=0.0, **kw):
    """合図 key の文の f 割のところから札を出す（lead 秒ずらせる。マイナスで先に出す）"""
    card(ctx, t, Sk(key, f) + lead, t1, rows, x, y, **kw)


def sc_end_t(name):
    return SC_END[name]


def X(ctx, x, y, s, col="#c8402f", w=14, a=1.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x - s, y - s)
    ctx.line_to(x + s, y + s)
    ctx.move_to(x + s, y - s)
    ctx.line_to(x - s, y + s)
    ctx.stroke()


def pay_pile(ctx, t, x, y, n, w=200, t0=0.0, dt=0.25, spread=4):
    """給料袋の山（下から n 個。t0 から dt ごとに1つずつ）。(x, y) = 山の底の真ん中"""
    k = 0
    row = 0
    while k < n:
        cnt = max(1, spread - row)
        for i in range(cnt):
            if k >= n:
                break
            ta = t0 + k * dt
            if t >= ta:
                a = fade(t, ta, 0.2)
                pxx = x + (i - (cnt - 1) / 2) * (w * 1.05)
                pyy = y - row * w * 0.5
                ctx.push_group()
                wa.pay_envelope(ctx, pxx, pyy, w, ((k * 37) % 7 - 3) * 0.012)
                ctx.pop_group_to_source()
                ctx.paint_with_alpha(a)
            k += 1
        row += 1


# ---------- ヒストグラム（人・給料袋を「1つ＝100人」で積む）----------
def pile_hist(ctx, t, counts, x0, x1, yb, unit, ih, t0, dt, colfn, a=1.0):
    n = len(counts)
    bw = (x1 - x0) / n
    for i, c in enumerate(counts):
        ta = t0 + i * dt
        if t < ta or c <= 0:
            continue
        al = a * fade(t, ta, 0.25)
        k = c / unit
        full, fr = int(k), k - int(k)
        cx = x0 + bw * (i + 0.5)
        for j in range(full + (1 if fr > 0.04 else 0)):
            last = j == full
            mini_block(ctx, cx, yb - j * ih, bw * 0.82, ih * 0.86 * (fr if (last and fr < 0.999) else 1.0) if last else ih * 0.86, colfn(i), al * (0.55 if last else 1.0), head=not last)


def months_x(v, x0, x1):
    return x0 + (x1 - x0) * v / (HM["step"] * len(HM["counts"]))


def take_x(v, x0, x1):
    return x0 + (x1 - x0) * v / (HT["step"] * len(HT["counts"]))


# ============================================================
# 0 いくら稼げますか
# ============================================================
QROWS = ["いくら", "稼げますか？"]
OPEN_YOU_H = YOU_H


def sc_open(ctx, t):
    bg_harbor(ctx, t)
    for k in range(3):
        x = 560 + ((k * 230 + t * 48) % 700)
        crew(ctx, t, x, 900 + 12 * k, 250 + 20 * k, ph=k)
    you(ctx, t, 330, GY, OPEN_YOU_H)
    panel(ctx, [(QROWS[0], 110, WHITE), (QROWS[1], 110, YEL)], 640, 175, a=1.0, pad=(40, 20), border=YEL)
    card(ctx, t, 0.4, None, R("ニューベッドフォード", "1840〜58年に出た船", sz=40), 1560, 130)


def sc_c0_new(ctx, t):
    bg_harbor(ctx, t, ship=(1250, 840, 640), boat=False, barrels=False)
    u = seg(t, Sk("c0_new", 0.0), Sk("c0_new", 1.0) + 0.8)
    for k in range(3):
        x = 560 + 90 * k + (t - Sk("c0_new")) * 40
        crew(ctx, t, min(x, 780), 905, 260, ph=k)
    you(ctx, t, 330 + 470 * ease(u), GY)
    Cd(ctx, t, "c0_new", 0.55, R("新米＝初めて船に乗る", "見習いの船員"), 1560, 190, t1=None, lead=-0.2)
    a = fade(t, Sk("c0_nopay", 0.0), 0.35)
    if a > 0.003:
        ctx.push_group()
        wa.pay_envelope(ctx, 1560, 520, 340, -0.05, mark="給料")
        X(ctx, 1560, 520, 120, a=1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def sc_c0_lay(ctx, t):
    bg_office(ctx)
    wa.paper(ctx, 790, 80, 960, 800, rot=0.0)
    text(ctx, "契約書", 480, 100, 76, INKC)
    text(ctx, "190分の1", 480, 370, 150, ORANGE_TXT)
    text(ctx, "あなたの取り分", 480, 590, 70, INKC)
    gray_lines(ctx, 130, 690, 700, 3, 52)
    seal(ctx, 760, 715, 52)
    ctx.restore()
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c0_lay", 0.55, R("取り分＝給料の代わりに", "あなたに分けられる額"), 480, 190, lead=-0.1)
    Cd(ctx, t, "c0_lay", 0.55, R("最後まで乗っていた場合", "前借りと費用を引く前", sz=40), 480, 372, lead=0.2)


def sc_c0_back(ctx, t):
    bg_deck(ctx, t)
    e = SC_END["c0_back"]
    d = seg(t, e - 2.0, e - 0.2)
    if d > 0:
        band(ctx, "#a07d57", 560, 660, x0=int(W_ - 900 * ease(d)), x1=W_)
    you(ctx, t, 760, GY, YOU_H)
    crew(ctx, t, 1180, 985, 300, facing=-1)
    crew(ctx, t, 1500, 1030, 330, facing=-1, ph=1.0)


def sc_c0_10k(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    x0, y0, dx, dy = 770, 150, 100, 52
    t_in = Sk("c0_10k", 0.0) - 0.2
    for k in range(100):
        ta = t_in + (k / 99.0) * 1.6
        if t < ta:
            continue
        a = fade(t, ta, 0.2) * (1.0 if t < Sk("c0_res", 0.0) else 0.35)
        mini_block(ctx, x0 + (k % 10) * dx + 40, y0 + (k // 10) * dy + 44, 56, 44, CREW, a)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c0_10k", 0.1, R("実際の新米の契約から", "1万人ぶん"), 1300, 110, t1=None, lead=-0.1)
    Cd(ctx, t, "c0_10k", 0.1, R("/1万人", sz=40), 1700, 110, lead=0.2)
    Cd(ctx, t, "c0_res", 0.35, [("取り分の中央値", 56, WHITE), ("284ドル", 130, YEL)], 1300, 640, pad=(50, 24), border=YEL)
    a = fade(t, Sk("c0_res", 0.5), 0.4)
    if a > 0.003:
        ctx.push_group()
        wa.pay_envelope(ctx, 1640, 770, 280, 0.05, mark="284ドル")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def _sorted_strip(ctx, t, x0, x1, ybase, hmax, t0, dt, mid_t=None, a=1.0):
    """1万人を取り分の小さい順に並べた帯（100本＝100人ずつ）。ヒストグラム hist_take の分位で高さを決める"""
    cs = np.cumsum(HT["counts"])
    step = HT["step"]
    n = 100
    bw = (x1 - x0) / n
    for i in range(n):
        ta = t0 + i * dt
        if t < ta:
            continue
        q = (i + 0.5) / n * 10000.0
        j = int(np.searchsorted(cs, q))
        j = min(j, len(cs) - 1)
        lo = cs[j - 1] if j else 0
        v = (j + (q - lo) / max(1, HT["counts"][j])) * step
        h = hmax * v / (step * len(HT["counts"])) * 1.5
        mid = i == 50
        wa._set(ctx, YOU if (mid and mid_t is not None and t >= mid_t) else CREW, a * fade(t, ta, 0.2))
        wa.rrect(ctx, x0 + bw * i + 1.5, ybase - h, bw - 3, h, 4)
        ctx.fill()


def sc_c0_med(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    t0 = Sk("c0_med", 0.0) - 0.9
    _sorted_strip(ctx, t, 220, 1700, 800, 560, t0, 0.03, mid_t=Sk("c0_med", 0.35))
    tm = Sk("c0_med", 0.35)
    a = fade(t, tm, 0.3)
    if a > 0.003:
        xm = 220 + 1480 * 0.505
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.set_line_width(8)
        ctx.move_to(xm, 800)
        ctx.line_to(xm, 250)
        ctx.stroke()
    Cd(ctx, t, "c0_med", 0.35, R("ちょうど真ん中＝中央値"), 960, 190, lead=0.0)
    Cd(ctx, t, "c0_med", 0.0, R("小さい順に並べた1万人", sz=44), 960, 870, lead=-0.5)


def sc_c0_call(ctx, t):
    bg_harbor(ctx, t, ship=(1450, 840, 420), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    q = [("問い1", "何年で帰れる？"), ("問い2", "取り分はいくら？"), ("問い3", "最後まで乗っていられる？"), ("問い4", "どの船に乗る？")]
    for k, (a_, b_) in enumerate(q):
        tt = Sk("c0_call", 0.0) + 0.5 + 0.55 * k
        card(ctx, t, tt, None, [(f"{a_}　{b_}", 52, WHITE)], 1150, 150 + 170 * k, pad=(40, 22), border=YEL if k == 0 else None, align="center")



# ============================================================
# 1 何年で帰れる？
# ============================================================
def dock_leaving(ctx, t, t0, speed=170.0):
    x1 = max(0.0, 900 - speed * (t - t0))
    if x1 > 0:
        band(ctx, "#a07d57", 560, 660, x0=0, x1=int(x1))
        band(ctx, "#b8946a", 560, 575, x0=0, x1=int(x1))


def sc_c1_a(ctx, t):
    bg_deck(ctx, t)
    dock_leaving(ctx, t, SC_START["c1_a"] + 0.2)
    you(ctx, t, 760, GY)
    crew(ctx, t, 1250, 985, 300, facing=-1)
    crew(ctx, t, 1560, 1030, 330, facing=-1, ph=1.0)


def sc_c1_yoso(ctx, t):
    bg_room(ctx)
    wa._set(ctx, "#7a5a3a")
    wa.rrect(ctx, 90, 150, 380, 460, 10)
    ctx.fill()
    band(ctx, "#27406b", 170, 590, x0=110, x1=450)
    disc(ctx, 330, 300, 52, "#fff3c4")
    disc(ctx, 352, 288, 46, "#27406b")
    band(ctx, "#7a5a3a", 170, 590, x0=270, x1=290)
    band(ctx, "#7a5a3a", 370, 390, x0=110, x1=450)
    wa.draw_calendar(ctx, 1190, 160, 560, 640, "1月", crossed=0, first_dow=2)
    you(ctx, t, 760, GY)
    Cd(ctx, t, "c1_yoso", 0.35, R("1年くらい？", sz=60, col=YEL), 700, 330, pad=(40, 20), border=YEL)
    card(ctx, t, SC_START["c1_yoso"] + 0.7, None, R("航海の記録と乗組員の名簿", "（whalinghistory.org）", sz=40), 1470, 865)


BX0, BX1, BYB, BIH = 300, 1800, 860, 36


def sc_c1_band(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    chart_card(ctx, 180, 110, 1860, 930)
    cnt = HM["counts"]
    t0 = Sk("c1_sort", 0.0) - 0.5
    wa._set(ctx, INKC)
    ctx.rectangle(BX0 - 10, BYB + 6, BX1 - BX0 + 20, 6)
    ctx.fill()
    pile_hist(ctx, t, cnt, BX0, BX1, BYB, 100, BIH, t0, 0.26, lambda i: CREW)
    for k in range(1, 7):
        tag_x = months_x(12 * k, BX0, BX1)
        label(ctx, f"{k}年", tag_x, BYB + 52, 40, INKC, a=fade(t, t0, 0.3))
    card(ctx, t, t0, None, R("1マス＝100人", "/1万人", sz=40), 260, 140)
    # 中央値
    tm = Sk("c1_med", 0.4)
    am = fade(t, tm, 0.3)
    if am > 0.003:
        xm = months_x(34.7, BX0, BX1)
        line2(ctx, (xm, BYB), (xm, 330), YOU, 8, am)
    Cd(ctx, t, "c1_med", 0.4, [("中央値", 44, WHITE), ("約2年11か月", 64, YEL), ("（34.7か月）", 40, WHITE), ("/1万人", 40, WHITE)], 1070, 150, pad=(40, 16))
    # 10%点（短いほう）
    tp = Sk("c1_p10", 0.35)
    ap = fade(t, tp, 0.3)
    if ap > 0.003:
        line2(ctx, (months_x(21.3, BX0, BX1), BYB), (months_x(21.3, BX0, BX1), 340), YEL, 6, ap, dash=[14, 12])
    Cd(ctx, t, "c1_p10", 0.35, [("10%点", 44, WHITE), ("21.3か月", 56, YEL)], 640, 150, pad=(30, 16))
    Cd(ctx, t, "c1_p10", 0.35, R("最短 約半年（6.4か月）", sz=40), 480, 570, lead=0.3)
    # 4年以上（長いほう）
    tq = Sk("c1_p90", 0.4)
    aq = fade(t, tq, 0.3)
    if aq > 0.003:
        line2(ctx, (months_x(48, BX0, BX1), BYB), (months_x(48, BX0, BX1), 340), YEL, 6, aq, dash=[14, 12])
    Cd(ctx, t, "c1_p90", 0.4, [("4年以上", 56, YEL), ("1,054人", 52, WHITE), ("/1万人", 40, WHITE)], 1620, 150, pad=(36, 16))
    Cd(ctx, t, "c1_p90", 0.4, R("最長 約6年（73か月）", sz=40), 1560, 570, lead=0.3)


def sc_c1_follow(ctx, t):
    bg_harbor(ctx, t, ship=(1350, 840, 560), boat=False, barrels=False)
    u = seg(t, Sk("c1_follow", 0.0), Sk("c1_follow", 0.0) + 2.0)
    you(ctx, t, 380 + 80 * ease(u), GY, 500)
    for k in range(3):
        crew(ctx, t, 700 + 140 * k, 930, 250, ph=k)


def sc_c1_out(ctx, t):
    bg_deck(ctx, t)
    dock_leaving(ctx, t, SC_START["c1_out"] + 0.3)
    you(ctx, t, 760, GY)
    crew(ctx, t, 1250, 985, 300, facing=-1)
    crew(ctx, t, 1560, 1030, 330, facing=-1, ph=1.0)


def sc_c1_sea(ctx, t):
    bg_deck(ctx, t)
    you(ctx, t, 760, GY)
    crew(ctx, t, 1180, 990, 300, facing=-1)
    n = 0
    for k in range(9):
        ta = Sk("c1_cargo", 0.0) + 0.5 + 0.45 * k
        if t >= ta:
            a = fade(t, ta, 0.25)
            ctx.push_group()
            draw_barrel(ctx, 1450 + (k % 3) * 120, 880 + (k // 3) * 62, 110, 140)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
    Cd(ctx, t, "c1_cargo", 0.2, R("船の荷物＝鯨の油と鯨ひげ", sz=44), 1000, 210)


def sc_c1_cal(ctx, t):
    bg_room(ctx)
    t0, d = Sk("c1_cal", 0.0), Dk("c1_cal")
    cur = 2.0 * ease(clamp01((t - t0) / max(1.0, d - 0.8)))
    for k in range(3):
        px = 760 + (k - cur) * 1000
        if -400 < px < 2300:
            wa.draw_calendar(ctx, px, 150, 560, 640, f"{k + 1}年目", crossed=(0 if k < 2 else 12), first_dow=(2 + k) % 7)
    wa.draw_family(ctx, 1560, 1000, 440, "woman", facing=-1)
    wa.draw_family(ctx, 1790, 1000, 320, "kid", facing=-1)
    page = int(min(2, round(cur - 0.2)))
    label_t = Sk("c1_cal", 0.0) + 0.4
    for k in range(3):
        ts_ = SC_START["c1_cal"] + 0.2           # 場面の頭から（札「1枚目」を読める長さに）
        span = (t0 + d - 0.7) - ts_
        ta = ts_ + k * span / 3.0
        tb = ta + span / 3.0
        if k == 2:
            tb = SC_END["c1_cal"]
        card(ctx, t, ta, (tb - 0.25) if k < 2 else tb, R(f"{k + 1}枚目", sz=64, col=YEL), 1000, 90)


def sc_c1_ans(ctx, t):
    bg_harbor(ctx, t, ship=(1600, 880, 330), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c1_ans", 0.2, [("答え", 48, WHITE), ("約2年11か月", 120, YEL)], 1120, 190, pad=(46, 22), border=YEL, lead=0.3)
    Cd(ctx, t, "c1_ans", 0.6, [("10人に1人は", 48, WHITE), ("4年以上かかる", 72, WHITE)], 1180, 470, pad=(40, 20))



# ============================================================
# 2 取り分はいくら？
# ============================================================
def bg_town(ctx, t, factory=True, fx=1000):
    band(ctx, "#d9e6ee", 0, 880)
    drift_cloud(ctx, t, 1500, 160, 80, 11.0, 0.8)
    drift_cloud(ctx, t, 500, 110, 60, 8.0, 0.8)
    if factory:
        draw_factory(ctx, fx, 470, 820, 410)
        for k in range(5):
            u = ((t * 0.35 + k * 0.2) % 1.0)
            wa._set(ctx, "#f0f2f5" if k % 2 else "#e1e6ec", 0.8 * (1 - u))
            ctx.arc(fx + 180 + u * 90, 150 - u * 120, 28 + u * 30, 0, 2 * math.pi)
            ctx.fill()
            ctx.arc(fx + 620 + u * 90, 150 - u * 120, 28 + u * 30, 0, 2 * math.pi)
            ctx.fill()
    band(ctx, "#8b8f93", 880, H_)
    band(ctx, "#777b80", 880, 894)


def ledger(ctx, t, you_txt=None, rows=("blank", "blank", "you"), bar=0.0, left_title="樽の値打ち", extra=(), you_a=1.0, amt_col="#2b1d10"):
    x, top = 690, 70
    wa._set(ctx, "#2f5d4a")
    wa.rrect(ctx, x, top, 1170, 810, 22)
    ctx.fill()
    wa._set(ctx, "#000000", 0.18)
    wa.rrect(ctx, x + 26, top + 40, 560, 740, 8)
    ctx.fill()
    wa._set(ctx, "#fbf7ea")
    wa.rrect(ctx, x + 26, top + 26, 560, 740, 8)
    ctx.fill()
    wa.rrect(ctx, x + 594, top + 26, 552, 740, 8)
    ctx.fill()
    wa._set(ctx, "#e8dfc6")
    ctx.rectangle(x + 574, top + 26, 30, 740)
    ctx.fill()
    text(ctx, left_title, x + 306, top + 90, 54, INKC)
    text(ctx, "名前と取り分", x + 870, top + 90, 54, INKC)
    for i in range(5):
        yy = 290 + i * 112
        wa._set(ctx, "#d9cfb5")
        ctx.rectangle(x + 66, yy + 44, 480, 4)
        ctx.fill()
    if bar > 0:
        wa._set(ctx, "#6aa07a")
        wa.rrect(ctx, x + 66, 290 + 6, 480 * bar, 40, 8)
        ctx.fill()
    allrows = list(rows) + list(extra)
    for i, kind in enumerate(allrows):
        yy = 290 + i * 112
        if kind == "you":
            if you_a > 0.003:
                wa._set(ctx, YOU, you_a)
                wa.rrect(ctx, x + 626, yy - 40, 490, 88, 14)
                ctx.fill()
                text(ctx, "あなた", x + 650, yy + 4, 46, "#2b1d10", align="left", alpha=you_a)
                if you_txt:
                    text(ctx, you_txt, x + 1100, yy + 4, 50, amt_col, align="right", alpha=you_a)
        elif kind in ("前借り", "費用"):
            wa._set(ctx, "#e9d9b0")
            wa.rrect(ctx, x + 626, yy - 40, 490, 88, 14)
            ctx.fill()
            text(ctx, kind, x + 650, yy + 4, 46, INKC, align="left")
            wa._set(ctx, "#b9ad8e")
            ctx.rectangle(x + 930, yy + 2, 160, 6)
            ctx.fill()
        else:
            wa._set(ctx, "#d9cfb5")
            ctx.rectangle(x + 626, yy + 44, 490, 4)
            ctx.fill()


def sc_c2_a(ctx, t):
    bg_harbor(ctx, t, ship=(1420, 830, 480), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    k = bob(t, 8, 1.4)
    ctx.push_group()
    wa.pay_envelope(ctx, 1000, 700 + k, 300, -0.04, mark="給料")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.9)


def sc_c2_yoso(ctx, t):
    bg_town(ctx, t)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c2_yoso", 0.4, R("陸の仕事より多い？", sz=60, col=YEL), 760, 330, pad=(40, 20), border=YEL)


def sc_c2_def(ctx, t):
    bg_office(ctx)
    for r, n in enumerate((3, 2)):
        for i in range(n):
            draw_barrel(ctx, 220 + i * 170 + r * 85, 960 - r * 175, 150, 190)
    k = seg(t, Sk("c2_def", 0.35), Sk("c2_def", 1.0))
    ledger(ctx, t, bar=ease(k), you_txt=None, rows=("blank", "blank", "blank"))
    if k > 0.6:
        s = ease(seg(k, 0.6, 1.0))
        wa._set(ctx, YOU)
        wa.rrect(ctx, 690 + 66 + 480 * 0.94 - 30 * s, 296 - 120 * s, 44, 40, 8)
        ctx.fill()


def sc_c2_split(ctx, t):
    bg_office(ctx)
    wa.paper(ctx, 760, 90, 1000, 780, rot=0.0)
    text(ctx, "契約書", 500, 100, 70, INKC)
    text(ctx, "190分の1", 500, 340, 150, "#d4622b")
    text(ctx, "あなたの取り分", 500, 560, 64, INKC)
    gray_lines(ctx, 140, 650, 720, 3, 52)
    seal(ctx, 790, 690, 52)
    ctx.restore()
    you(ctx, t, 330, GY)


def sc_c2_lay(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    wa.paper(ctx, 1000, 120, 760, 700, rot=0.0)
    gray_lines(ctx, 80, 120, 600, 6, 80)
    seal(ctx, 560, 600, 50)
    ctx.restore()
    Cd(ctx, t, "c2_lay", 0.1, [("新米の取り分　中央値", 48, WHITE), ("190分の1", 110, YEL)], 1130, 270, pad=(46, 22), border=YEL, lead=0.0)
    Cd(ctx, t, "c2_lay", 0.3, R("10〜90%は 160分の1〜200分の1", sz=40), 1130, 520, lead=0.0)
    Cd(ctx, t, "c2_lay", 0.5, R("実際の新米14,649人の記録", sz=40), 1130, 620, lead=0.0)


def sc_c2_val(ctx, t):
    bg_office(ctx)
    for i in range(7):
        ta = SC_START["c2_val"] + 0.5 + 0.2 * i
        if t >= ta:
            ctx.push_group()
            draw_barrel(ctx, 330 + i * 190, 520, 140, 180)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(fade(t, ta, 0.25))
    Cd(ctx, t, "c2_val1", 0.5, R("値段は帰港した年の相場", sz=44), 960, 110)
    Cd(ctx, t, "c2_val1", 0.7, R("金額はすべて当時の金額", sz=44), 960, 200, lead=0.5)
    tb = Sk("c2_val1", 0.85)
    wa._set(ctx, "#6aa07a", fade(t, tb, 0.4))
    wa.rrect(ctx, 300, 640, 1320, 80, 12)
    ctx.fill()
    ts = Sk("c2_val2", 0.3)
    s = ease(seg(t, ts, ts + 1.2))
    if t >= ts:
        wa._set(ctx, YOU)
        wa.rrect(ctx, 1560 - 80 * s, 640 + 130 * s, 60 + 80 * s, 80, 10)
        ctx.fill()
    Cd(ctx, t, "c2_val2", 0.0, R("値打ち全体のうち、あなたの一切れ", sz=44), 1000, 830, lead=0.2)


def sc_c2_sort(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    chart_card(ctx, 180, 110, 1860, 930)
    cnt = HT["counts"]
    t0 = Sk("c2_sort", 0.0) - 0.5
    wa._set(ctx, INKC)
    ctx.rectangle(BX0 - 10, BYB + 6, BX1 - BX0 + 20, 6)
    ctx.fill()
    pile_hist(ctx, t, cnt, BX0, BX1, BYB, 100, 24, t0, 0.26, lambda i: "#f3e9cf")
    for v in (200, 400, 600, 800):
        label(ctx, f"{v}ドル", take_x(v, BX0, BX1), BYB + 52, 40, INKC, a=fade(t, t0, 0.3))
    card(ctx, t, t0, None, R("1つ＝100人ぶんの取り分", "/1万人", sz=40), 400, 100)
    tm = Sk("c2_med", 0.5)
    am = fade(t, tm, 0.3)
    if am > 0.003:
        line2(ctx, (take_x(284, BX0, BX1), BYB), (take_x(284, BX0, BX1), 300), YOU, 8, am)
    Cd(ctx, t, "c2_med", 0.5, [("中央値", 44, WHITE), ("284ドル", 84, YEL), ("/1万人", 40, WHITE)], 1000, 150, pad=(40, 16))
    Cd(ctx, t, "c2_med", 0.5, R("最後まで乗っていた場合", "前借りと費用を引く前", sz=40), 1560, 430, lead=0.4)
    ap = fade(t, Sk("c2_p10", 0.4), 0.3)
    if ap > 0.003:
        line2(ctx, (take_x(146, BX0, BX1), BYB), (take_x(146, BX0, BX1), 330), YEL, 6, ap, dash=[14, 12])
    Cd(ctx, t, "c2_p10", 0.4, [("10%点", 44, WHITE), ("146ドル", 56, YEL)], 560, 330, pad=(36, 16), lead=0.0)
    Cd(ctx, t, "c2_p10", 0.6, R("最少 9ドル", sz=40), 520, 600)
    aq = fade(t, Sk("c2_p90", 0.4), 0.3)
    if aq > 0.003:
        line2(ctx, (take_x(478, BX0, BX1), BYB), (take_x(478, BX0, BX1), 330), YEL, 6, aq, dash=[14, 12])
    Cd(ctx, t, "c2_p90", 0.4, [("90%点", 44, WHITE), ("478ドル", 56, YEL)], 1560, 270, pad=(36, 16))
    Cd(ctx, t, "c2_p90", 0.4, R("最多 841ドル", sz=40), 1560, 600, lead=0.2)


def sc_c2_month(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    you(ctx, t, 330, GY)
    wa._set(ctx, "#2f5d4a")
    wa.rrect(ctx, 1240, 520, 520, 330, 18)
    ctx.fill()
    wa._set(ctx, "#fbf7ea")
    wa.rrect(ctx, 1262, 540, 476, 290, 10)
    ctx.fill()
    gray_lines(ctx, 1290, 580, 420, 4, 56)
    Cd(ctx, t, "c2_month", 0.35, [("月給に直すと", 44, WHITE), ("中央値 約8ドル", 70, YEL)], 1000, 140, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c2_month", 0.5, R("（10〜90% 約4〜14ドル）", "/1万人", sz=40), 1000, 340, lead=0.5)
    Cd(ctx, t, "c2_doc", 0.2, [("資料の平均", 44, WHITE), ("8.22ドル", 64, YEL)], 1500, 340, pad=(40, 16))


def sc_c2_fac(ctx, t):
    bg_town(ctx, t)
    you(ctx, t, 330, GY)
    pay_pile(ctx, t, 1400, 860, 8, 190, SC_START["c2_fac"] + 1.0, 0.45, 4)
    Cd(ctx, t, "c2_facpay", 0.1, R("未熟練の工場・1か月25日働いた場合", sz=44), 960, 100, lead=-0.2)
    Cd(ctx, t, "c2_facpay", 0.4, R("同じ月数・同じ年", sz=44), 960, 190)


def _bar(ctx, x0, y, w, h, col, label_, a=1.0, size=46, tcol="#2b1d10", frac=1.0):
    wa._set(ctx, col, a)
    wa.rrect(ctx, x0, y - h / 2, w * frac, h, 12)
    ctx.fill()
    if label_ and frac > 0.55:
        text(ctx, label_, x0 + 24, y + 2, size, tcol, align="left", alpha=a)


def sc_c2_600(ctx, t):
    bg_town(ctx, t, fx=40)
    tp = Sk("c2_600", 0.0)
    pay_pile(ctx, t, 450, 890, 12, 130, tp - 0.3, 0.22, 6)
    Cd(ctx, t, "c2_600", 0.5, [("同じ月数の工場", 44, WHITE), ("約600ドル", 90, YEL)], 1400, 230, pad=(46, 20), border=YEL)
    tb = Sk("c2_half", 0.0) - 1.0
    a = fade(t, tb, 0.4)
    if a > 0.003:
        box(ctx, 980, 400, 1850, 830, "#10284a", 0.94 * a, r=24)
        s = 700 / 650.0
        _bar(ctx, 1010, 520, 600 * s, 100, "#c9b27a", "工場 約600ドル", a, size=42)
        f = ease(seg(t, tb + 0.2, tb + 0.9))
        _bar(ctx, 1010, 690, 284 * s, 100, YOU, "新米 284ドル", a * fade(t, tb + 0.2, 0.3), size=40, frac=f)


def sc_c2_168(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    t0 = SC_START["c2_168"]
    _sorted_strip(ctx, t, 220, 1700, 820, 560, t0 - 5, 0.0)
    ta = Sk("c2_168", 0.4)
    a = fade(t, ta, 0.3)
    if a > 0.003:
        wa._set(ctx, YEL, a)
        wa.rrect(ctx, 1700 - 26, 820 - 520, 26, 520, 4)
        ctx.fill()
    Cd(ctx, t, "c2_168", 0.4, [("工場を上回った", 48, WHITE), ("168人", 110, YEL), ("/1万人", 40, WHITE)], 960, 230, pad=(50, 20), border=YEL)
    Cd(ctx, t, "c2_168", 0.1, R("1万人を小さい順に並べた帯", sz=40), 960, 880, lead=-0.4)


def sc_c2_meal(ctx, t):
    bg_room(ctx, "#e6d2b4", "#8a6945")
    t0 = SC_START["c2_meal"]
    tp, ta_ = Sk("c2_pay", 0.0), Sk("c2_add", 0.0)
    if t < tp:
        # 船の食卓
        wa._set(ctx, "#7a5436")
        wa.rrect(ctx, 300, 560, 1320, 60, 14)
        ctx.fill()
        wa._set(ctx, "#5b3a2a")
        ctx.rectangle(380, 620, 60, 280)
        ctx.rectangle(1480, 620, 60, 280)
        ctx.fill()
        for k in range(5):
            wa._set(ctx, "#f6f0e0")
            ctx.arc(520 + k * 220, 548, 62, 0, 2 * math.pi)
            ctx.fill()
            wa._set(ctx, "#e1b04a")
            ctx.arc(520 + k * 220, 548, 34, 0, 2 * math.pi)
            ctx.fill()
        you(ctx, t, 560, 905, 300)
        crew(ctx, t, 1040, 905, 300)
        crew(ctx, t, 1380, 905, 300, facing=-1, ph=1)
    elif t < ta_:
        u = ease(seg(t, tp, tp + 1.4))
        ctx.push_group()
        wa.pay_envelope(ctx, 760, 520, 380, 0.0, mark="工場の給料")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1.0)
        wa.pay_envelope(ctx, 1240 + 380 * u, 540 + 60 * u, 200, 0.1 * u, mark="食費")
        Cd(ctx, t, "c2_pay", 0.0, R("陸では、食費を自分で払う", sz=44), 960, 190, lead=0.1)
    else:
        s = 1250 / 650.0
        _bar(ctx, 300, 520, 284 * s, 100, YOU, "新米 284ドル")
        f = ease(seg(t, ta_ + 0.2, ta_ + 1.2))
        if f > 0:
            wa._set(ctx, "#6aa07a")
            wa.rrect(ctx, 300 + 284 * s, 520 - 50, 145 * s * f, 100, 12)
            ctx.fill()
        Cd(ctx, t, "c2_add", 0.4, R("船の食事の値打ちを足す", sz=44), 960, 190)


def sc_c2_noreach(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    s = 1250 / 650.0
    _bar(ctx, 300, 330, 600 * s, 100, "#c9b27a", "工場 約600ドル")
    _bar(ctx, 300, 520, 284 * s, 100, YOU, "新米 284ドル")
    wa._set(ctx, "#6aa07a")
    wa.rrect(ctx, 300 + 284 * s, 470, 145 * s, 100, 12)
    ctx.fill()
    wa._set(ctx, "#6aa07a", 0.5)
    wa.rrect(ctx, 300 + (284 + 145) * s, 470, (248 - 145) * s, 100, 12)
    ctx.fill()
    Cd(ctx, t, "c2_noreach", 0.1, R("食事の値打ち 中央値で約145〜250ドル", sz=44), 960, 700, lead=0.0)
    Cd(ctx, t, "c2_noreach", 0.3, R("足した中央値 約445〜550ドル", sz=44, col=YEL), 960, 790, lead=0.0)
    Cd(ctx, t, "c2_noreach", 0.5, R("住む場所の値打ちは入れていない", sz=40), 960, 875, lead=0.0)


def sc_c2_5in1(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    ts = Sk("c2_5in1", 0.0) - 0.5
    for k in range(5):
        a = fade(t, ts + 0.2 * k, 0.3)
        mini_block(ctx, 360 + k * 130, 660, 100, 130, "#4a6fb0" if k == 4 else CREW, a)
    Cd(ctx, t, "c2_5in1", 0.4, [("高く見た場合　工場を上回った", 44, WHITE), ("1,948人", 100, YEL), ("/1万人", 40, WHITE)], 1180, 250, pad=(46, 20), border=YEL)
    Cd(ctx, t, "c2_5in1", 0.6, [("低く見た場合", 44, WHITE), ("685人", 72, WHITE), ("/1万人", 40, WHITE)], 1450, 600, pad=(40, 16))
    Cd(ctx, t, "c2_5in1", 0.0, R("5人に1人", sz=48), 560, 800, lead=0.3)


def sc_c2_ledger(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    a = fade(t, Sk("c2_ledger", 0.0) - 0.3, 0.4)
    ctx.push_group()
    ledger(ctx, t, you_txt="284ドル" if t >= Sk("c2_row", 0.55) else None, you_a=1.0 if t >= Sk("c2_row", 0.0) - 0.3 else 0.0,
           bar=ease(seg(t, Sk("c2_left", 0.2), Sk("c2_left", 0.9))))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def sc_c2_more(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    k = ease(seg(t, Sk("c2_more", 0.2), Sk("c2_more", 1.0)))
    ledger(ctx, t, you_txt="284ドル", bar=0.4 + 0.5 * k)
    Cd(ctx, t, "c2_vary", 0.3, R("取り分の額は、", "乗った船で大きく変わる", sz=44), 340, 330, pad=(36, 18))


def sc_c2_one(ctx, t):
    bg_office(ctx)
    wa._set(ctx, "#2f5d4a")
    wa.rrect(ctx, 260, 160, 1400, 640, 24)
    ctx.fill()
    wa._set(ctx, "#fbf7ea")
    wa.rrect(ctx, 296, 196, 1328, 568, 14)
    ctx.fill()
    wa._set(ctx, YOU)
    wa.rrect(ctx, 340, 400, 1240, 170, 22)
    ctx.fill()
    text(ctx, "あなた", 400, 485, 90, "#2b1d10", align="left")
    text(ctx, "284ドル", 1540, 485, 110, "#2b1d10", align="right")
    wa._set(ctx, "#d9cfb5")
    ctx.rectangle(340, 330, 1240, 6)
    ctx.rectangle(340, 650, 1240, 6)
    ctx.fill()
    Cd(ctx, t, "c2_one", 0.3, R("約3年を海の上で過ごした結果", sz=46), 960, 100)


def sc_c2_office(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    ledger(ctx, t, you_txt="284ドル", rows=("blank", "blank", "you"), extra=("前借り",), you_a=1.0)
    Cd(ctx, t, "c2_adv", 0.3, R("出航前に「前借り」", sz=44), 330, 330, lead=0.0)


def sc_c2_adv(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c2_advdef", 0.2, R("前借り＝取り分の見込みを、", "出航前に借りる", sz=44), 1130, 150, pad=(36, 18))
    tb = Sk("c2_third", 0.2)
    a = fade(t, tb - 0.2, 0.4)
    if a > 0.003:
        wa._set(ctx, "#c9b27a", a)
        wa.rrect(ctx, 760, 470, 960, 90, 12)
        ctx.fill()
        f = ease(seg(t, tb, tb + 1.0))
        wa._set(ctx, "#6aa07a", a)
        wa.rrect(ctx, 760, 470, 960 / 4 * f, 90, 12)
        ctx.fill()
        wa._set(ctx, "#6aa07a", 0.5 * a)
        wa.rrect(ctx, 760 + 960 / 4, 470, (960 / 3 - 960 / 4) * f, 90, 12)
        ctx.fill()
    card(ctx, t, tb - 0.2, None, R("取り分の見込み", sz=44), 1240, 395, pad=(26, 12))
    card(ctx, t, tb - 0.2, None, R("前借り（1/4〜1/3）", sz=44, col=YEL), 1000, 585, pad=(26, 12))
    Cd(ctx, t, "c2_third", 0.3, [("借りる額は見込みの", 44, WHITE), ("1/4〜1/3", 90, YEL)], 1230, 750, pad=(44, 18), border=YEL)


def sc_c2_int(ctx, t):
    bg_room(ctx)
    wa._set(ctx, "#7a5436")
    wa.rrect(ctx, 760, 700, 700, 50, 12)
    ctx.fill()
    ctx.rectangle(820, 750, 50, 150)
    ctx.rectangle(1340, 750, 50, 150)
    ctx.fill()
    wa._set(ctx, "#f6f0e0")
    ctx.arc(1000, 690, 50, 0, 2 * math.pi)
    ctx.arc(1220, 690, 50, 0, 2 * math.pi)
    ctx.fill()
    wa.draw_family(ctx, 880, 900, 380, "woman", facing=1)
    wa.draw_family(ctx, 1340, 900, 290, "kid", facing=-1)
    Cd(ctx, t, "c2_int", 0.3, R("利子は通常6%", sz=64, col=YEL), 960, 160, pad=(44, 20), border=YEL)
    Cd(ctx, t, "c2_fam", 0.0, R("家族がいれば、このお金で暮らした", sz=44), 960, 290, lead=-0.3)


def sc_c2_shop(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    ledger(ctx, t, you_txt="284ドル", rows=("blank", "blank", "you"), extra=("前借り", "費用"), you_a=1.0)
    wa._set(ctx, "#7a5436")
    wa.rrect(ctx, 80, 330, 520, 40, 8)
    ctx.fill()
    for k in range(4):
        wa._set(ctx, ("#6b8cc2", "#c8d0dc", "#b5573e", "#4a8f6a")[k])
        wa.rrect(ctx, 100 + k * 125, 250, 100, 80, 10)
        ctx.fill()
    Cd(ctx, t, "c2_shop", 0.3, R("船の売店（服・道具）", sz=44), 340, 190)
    Cd(ctx, t, "c2_sub", 0.0, R("284ドルから前借りと", "費用が引かれる", sz=40), 340, 440, pad=(30, 16), lead=0.3)


def sc_c2_before(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    wa._set(ctx, "#2f5d4a")
    wa.rrect(ctx, 740, 200, 1000, 560, 24)
    ctx.fill()
    wa._set(ctx, "#fbf7ea")
    wa.rrect(ctx, 770, 230, 940, 500, 12)
    ctx.fill()
    wa._set(ctx, YOU)
    wa.rrect(ctx, 800, 300, 880, 130, 18)
    ctx.fill()
    text(ctx, "284ドル", 1240, 366, 90, "#2b1d10")
    Cd(ctx, t, "c2_before", 0.2, R("284ドルは前借りと費用を", "引く前の額", sz=46, first=(46, WHITE)), 1240, 560, pad=(36, 18), border=YEL)


def sc_c2_ans(ctx, t):
    bg_harbor(ctx, t, ship=(1600, 880, 330), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c2_ans", 0.15, [("答え", 48, WHITE), ("取り分の中央値　284ドル", 80, YEL)], 1080, 190, pad=(46, 22), border=YEL, lead=0.3)
    Cd(ctx, t, "c2_ans", 0.55, R("同じ月数の工場の半分に届かない", sz=56), 1180, 440, pad=(40, 20))



# ============================================================
# 3 最後まで乗っていられる？
# ============================================================
NAVY = "#17365f"


def log_panel(ctx, t, mark_t=None, hi_t=None, ghosts=True, ghost_t=None, third="帰港"):
    """船の記録（欄は空欄か線だけ。仮の船名・数字は書かない）"""
    band(ctx, "#1d3b5c", 0, H_)
    band(ctx, "#18324f", 560, H_)
    wave_scroll(ctx, t, 100, 900, 18, 60, 8, -14.0, col="#2f5a86", a=0.6)
    wa._set(ctx, "#000000", 0.2)
    wa.rrect(ctx, 90, 90, 1190, 800, 12)
    ctx.fill()
    wa._set(ctx, "#f1e7cc")
    wa.rrect(ctx, 70, 70, 1190, 800, 12)
    ctx.fill()
    text(ctx, "船の記録", 665, 125, 64, INKC)
    heads = (("船の名前", 150), ("出港", 700), (third, 960))
    wa._set(ctx, INKC)
    ctx.rectangle(100, 210, 1130, 6)
    ctx.fill()
    for s_, x in heads:
        text(ctx, s_, x, 180, 40, INKC, align="left")
    for i in range(4):
        yy = 300 + i * 140
        wa._set(ctx, "#d9cfb5")
        ctx.rectangle(100, yy + 62, 1130, 4)
        ctx.fill()
        wa._set(ctx, "#b9ad8e")
        ctx.rectangle(150, yy + 4, 360, 6)
        ctx.rectangle(700, yy + 4, 190, 6)
        if i < 3:
            ctx.rectangle(960, yy + 4, 220, 6)
        ctx.fill()
    if mark_t is not None and t >= mark_t:
        a = fade(t, mark_t, 0.4)
        seal(ctx, 1120 - 0, 300 + 3 * 140 + 8, 40 * a + 0.1)
    if hi_t is not None and t >= hi_t:
        a = fade(t, hi_t, 0.4)
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.set_line_width(8)
        rrect(ctx, 940, 300 + 3 * 140 - 30, 300, 90, 14)
        ctx.stroke()
    if ghosts:
        gt = ghost_t if ghost_t is not None else 0.0
        g0 = ghost_t if ghost_t is not None else 0.0
        al = 0.95 * (1 - clamp01((t - g0) / 4.0))
        if al > 0.02:
            draw_ship(ctx, 1570, 560 + bob(t, 4, 1.2), 300, a=al)


def sc_c3_a(ctx, t):
    bg_deck(ctx, t)
    you(ctx, t, 760, GY)
    crew(ctx, t, 1250, 985, 300, facing=-1)


def sc_c3_yoso(ctx, t):
    bg_sky_sea(ctx, t, 520)
    for k, (x, y, L) in enumerate(((760, 800, 280), (1200, 800, 280), (1640, 800, 280))):
        draw_ship(ctx, x, y + bob(t, 5, 1.1, k), L, hull=hull3(k))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    you(ctx, t, 300, GY)
    Cd(ctx, t, "c3_yoso", 0.45, R("ほとんど帰ってくる？", sz=60, col=YEL), 1100, 160, pad=(40, 20), border=YEL)
    Cd(ctx, t, "c3_count", 0.0, R("ここからは船の数で数える", "/1,666航海", sz=44), 1330, 340, lead=0.1)


SHIP_COLS, SHIP_ROWS, N_SHIPS = 14, 12, 167          # 1隻＝10航海（1,666航海 ≒ 167隻）
SHIP_X0, SHIP_DX, SHIP_Y0, SHIP_DY = 120, 86, 215, 58
_rl = random.Random(7)
LOST = sorted(int(b * N_SHIPS / 13) + _rl.randrange(0, int(N_SHIPS / 13)) for b in range(13))   # 129航海 ≒ 13隻。13の区画に1つずつ（ばらばらの位置）
LOST_COL = "#e8505b"


def mini_ship_rot(ctx, x, y, L, col, a, rot=0.0):
    ctx.save()
    ctx.translate(x, y - L * 0.2)
    ctx.rotate(rot)
    mini_ship(ctx, 0, L * 0.2, L, col, a)
    ctx.restore()


def ship_grid(ctx, t, t_in, dt, fade_t=None, fade_dt=0.12):
    for k in range(N_SHIPS):
        ta = t_in + k * dt
        if t < ta:
            continue
        a = fade(t, ta, 0.2)
        col, rot = "#9db7df", 0.0
        if fade_t is not None and k in LOST:
            j = LOST.index(k)
            f = clamp01((t - fade_t - j * fade_dt) / 0.4)
            col, rot = mix("#9db7df", LOST_COL, f), 0.55 * f
        x = SHIP_X0 + (k % SHIP_COLS) * SHIP_DX
        y = SHIP_Y0 + (k // SHIP_COLS) * SHIP_DY
        mini_ship_rot(ctx, x, y + math.sin(t * 1.3 + k) * 1.5, 70, col, a, rot)


def sc_c3_log(ctx, t):
    log_panel(ctx, t, mark_t=Sk("c3_log", 0.6), ghost_t=SC_START["c3_log"] + 0.8)


def sc_c3_1666(ctx, t):
    band(ctx, NAVY, 0, H_)
    t0 = Sk("c3_1666", 0.0) - 0.4
    ship_grid(ctx, t, t0, 0.012)
    card(ctx, t, t0, None, R("ニューベッドフォード 1840〜58年", sz=40), 700, 90)
    card(ctx, t, t0 + 0.4, None, R("1隻＝10航海", "/1,666航海", sz=40), 1560, 330)


def sc_c3_129(ctx, t):
    band(ctx, NAVY, 0, H_)
    ship_grid(ctx, t, -10, 0.0, fade_t=Sk("c3_129", 0.45))
    card(ctx, t, -1, None, R("1隻＝10航海", sz=40), 1560, 130)
    Cd(ctx, t, "c3_129", 0.5, [("帰らなかった船", 44, WHITE), ("129航海", 90, YEL), ("/1,666航海", 40, WHITE)], 1560, 360, pad=(40, 18), border=YEL)
    Cd(ctx, t, "c3_13", 0.35, [("7.7%", 90, YEL), ("約13回に1回", 56, WHITE)], 1560, 690, pad=(40, 18))


def sc_c3_why(ctx, t):
    band(ctx, NAVY, 0, H_)
    al = 0.95 * (1 - clamp01((t - SC_START["c3_why"] - 0.8) / 5.0))
    if al > 0.02:
        draw_ship(ctx, 1560, 560 + bob(t, 4, 1.2), 320, a=al)
    Cd(ctx, t, "c3_why", 0.3, R("帰らなかった理由", "沈没・行方不明・廃船・焼失・放棄・拿捕", sz=40), 560, 160)
    Cd(ctx, t, "c3_82", 0.4, [("沈没・行方不明", 44, WHITE), ("82航海（4.9%）", 76, YEL), ("/1,666航海", 40, WHITE)], 560, 440, pad=(40, 18), border=YEL)
    Cd(ctx, t, "c3_rest", 0.3, R("残りは", "廃船・焼失・放棄・拿捕", sz=44), 560, 740)


def deck_figs(ctx, t, n, x0, dx, y, h, alive):
    for k in range(n):
        a = alive(k)
        if a > 0.02:
            mini_block(ctx, x0 + dx * k, y, h * 0.55, h, CREW, a)


def sc_c3_notall(ctx, t):
    bg_harbor(ctx, t, ship=(1350, 840, 520), boat=False, barrels=False)
    ts = Sk("c3_rev", 0.0)
    deck_figs(ctx, t, 8, 1210, 38, 722, 56, lambda k: 1.0 if t < ts + 1.0 else (1.0 if k % 4 else 1 - clamp01((t - ts - 1.0 - 0.4 * k) / 0.5)))
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c3_notall", 0.4, R("船が帰らない＝", "全員が死んだ、ではない", sz=44), 880, 200, lead=0.0)
    Cd(ctx, t, "c3_rev", 0.5, R("船が帰る＝", "全員帰った、とは限らない", sz=44), 880, 400, lead=0.0)


def sc_c3_reason(ctx, t):
    bg_harbor(ctx, t, ship=(1500, 840, 520), boat=False, barrels=False)
    ts = Sk("c3_leave", 0.0)
    for k in range(3):
        u = ease(seg(t, ts + 0.3 * k, ts + 0.3 * k + 2.4))
        crew(ctx, t, 1180 - 380 * u - 20 * k, 905, 280, facing=-1, ph=k)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c3_reason", 0.4, R("死亡・下船・逃亡", sz=64, col=YEL), 960, 190, pad=(40, 20), border=YEL)


def sc_c3_63(ctx, t):
    band(ctx, NAVY, 0, H_)
    band(ctx, "#a67c52", 700, H_)
    ts = Sk("c3_63", 0.15)
    for k in range(10):
        if k < 6:
            a = 1 - clamp01((t - ts - 0.45 * k) / 0.5)
        elif k == 6:
            a = 1 - 0.7 * clamp01((t - ts - 0.45 * 6) / 0.5)
        else:
            a = 1.0
        px = 1050 + k * 80 - (60 * (1 - a) if k < 7 else 0)
        mini_block(ctx, px, 680, 66, 130, CREW, a)
    Cd(ctx, t, "c3_63", 0.2, R("ジョージ・ハウランド号", "1隻の例", sz=44), 560, 190)
    Cd(ctx, t, "c3_63", 0.45, [("出港のときの乗組員のうち", 44, WHITE), ("63%", 110, YEL)], 1300, 330, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c3_63", 0.5, R("死亡・下船・逃亡を合わせた数", "6回の航海の平均", sz=40), 560, 400, lead=0.4)
    Cd(ctx, t, "c3_one", 0.0, R("1隻の例。全体の割合ではない", sz=44, col=YEL), 960, 800, pad=(36, 16), border=YEL, lead=0.1)


def sc_c3_noshin(ctx, t):
    log_panel(ctx, t, ghosts=False)
    Cd(ctx, t, "c3_noshin", 0.0, R("全体の割合は言えない", "（記録の備考は", "当たり外れがある）", sz=44), 1560, 380, pad=(34, 18), lead=0.2)


def sc_c3_search(ctx, t):
    bg_harbor(ctx, t, ship=(1550, 840, 440), boat=False, barrels=False)
    ts = Sk("c3_search", 0.0)
    tn = Sk("c3_search", 0.0) + 3.4
    for k in range(4):
        a = 1.0 if k < 1 else 1 - clamp01((t - tn - 0.3 * k) / 0.6)
        if a > 0.02:
            ctx.push_group()
            crew(ctx, t, 800 + 150 * k, 905, 260, ph=k)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
    you(ctx, t, 330, GY, facing=-1)


def sc_c3_sink(ctx, t):
    bg_sky_sea(ctx, t, 560)
    s = clamp01((t - Sk("c3_sink", 0.35)) / 3.0)
    draw_ship(ctx, 1350, 830 + bob(t, 6), 560, a=max(0.12, 1 - s))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    you(ctx, t, 330, GY)


def sc_c3_mark(ctx, t):
    log_panel(ctx, t, mark_t=Sk("c3_mark", 0.3), hi_t=Sk("c3_nodate", 0.2), ghost_t=SC_START["c3_mark"] + 0.8)
    Cd(ctx, t, "c3_nodate", 0.35, R("帰港日が空のまま", sz=44, col=YEL), 1560, 90, pad=(30, 14))


def sc_c3_empty(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    ledger(ctx, t, you_txt=None, bar=0.0, rows=("blank", "blank", "you"))
    Cd(ctx, t, "c3_row", 0.4, R("取り分の元になる油も", "鯨ひげも届かない", sz=44), 340, 330, pad=(34, 18))


def sc_c3_adv(ctx, t):
    bg_room(ctx)
    wa.draw_family(ctx, 1380, 1000, 440, "woman", facing=-1)
    wa.draw_family(ctx, 1640, 1000, 320, "kid", facing=-1)
    you(ctx, t, 420, GY)
    Cd(ctx, t, "c3_adv", 0.4, R("船が沈んだ場合、", "前借りはほとんど返されなかった", sz=48), 1000, 220, pad=(40, 20), border=YEL)


def sc_c3_ans(ctx, t):
    bg_harbor(ctx, t, ship=(1600, 880, 330), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c3_ans", 0.2, [("答え", 48, WHITE), ("約13回に1回の船は", 70, YEL), ("帰ってこなかった", 70, WHITE)], 1100, 210, pad=(46, 20), border=YEL, lead=0.3)
    Cd(ctx, t, "c3_ans", 0.6, R("船が帰っても、乗っていた人が", "全員帰ったとは限らない", sz=48), 1160, 440, pad=(40, 18))


def sc_c3_next(ctx, t):
    bg_sky_sea(ctx, t, 520)
    for k, (x, hull) in enumerate(((470, "#5b3a2a"), (960, "#3f5f7a"), (1450, "#6b4a35"))):
        draw_ship(ctx, x, 800 + bob(t, 5, 1.1, k), 380, hull=hull)
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    Cd(ctx, t, "c3_next", 0.15, R("船を選べば、稼ぎは変えられる？", sz=56, col=YEL), 960, 190, pad=(40, 20), border=YEL)



# ============================================================
# 4 船を選べるなら、どれに乗る？
# ============================================================
C_N, C_P, C_I = "#f2542d", "#1fb8b0", "#9a63e0"       # 北の海・太平洋・インド洋（地図・表・棒で同じ色）


def hull3(k):
    return ("#5b3a2a", "#3f5f7a", "#6b4a35")[k % 3]


def sc_c4_a(ctx, t):
    bg_sky_sea(ctx, t, 520)
    for k, x in enumerate((770, 1180, 1590)):     # 船どうしが触れないように（長さ約350・間隔410）
        draw_ship(ctx, x, 850 + bob(t, 5, 1.1, k), 280, hull=hull3(k))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    you(ctx, t, 300, GY)


def log_panel_fish(ctx, t, hi_t=None):
    log_panel(ctx, t, ghosts=False, third="漁場")
    if hi_t is not None and t >= hi_t:
        a = fade(t, hi_t, 0.4)
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.set_line_width(8)
        rrect(ctx, 930, 140, 310, 700, 12)
        ctx.stroke()


def sc_c4_year(ctx, t):
    log_panel_fish(ctx, t, hi_t=Sk("c4_ground", 0.15))
    Cd(ctx, t, "c4_year", 0.25, R("1848〜58年に出た船", sz=52, col=YEL), 1560, 230, pad=(34, 18), border=YEL)
    Cd(ctx, t, "c4_ground", 0.3, R("漁場＝鯨を探す海", sz=48), 1560, 440, pad=(34, 18))


def map_regions(a_i=1.0, a_p=1.0, a_n=1.0):
    return [(wa.SEA_INDIAN, C_I, a_i), (wa.SEA_PACIFIC, C_P, a_p), (wa.SEA_NORTH, C_N, a_n)]


def map_labels(ctx, t, ti, tp, tn):
    from whaling_map_data import xy
    for (lo, la), nm, ta, col in (((78, -24), "インド洋", ti, C_I), ((205, 20), "太平洋", tp, C_P), ((184, 59.5), "北の海", tn, C_N)):
        a = fade(t, ta, 0.4)
        if a > 0.003:
            x, y = xy(lo, la)
            panel(ctx, [(nm, 50, WHITE)], x, y, a=a, bg=mix(col, "#000000", 0.55), pad=(26, 12))


def sc_c4_map(ctx, t):
    ti, tp, tn = Sk("c4_three", 0.3), Sk("c4_three", 0.48), Sk("c4_three", 0.66)
    wa.draw_map_seas(ctx, map_regions(fade(t, ti, 0.6), fade(t, tp, 0.6), fade(t, tn, 0.6)))
    map_labels(ctx, t, ti, tp, tn)
    Cd(ctx, t, "c4_three", 0.45, R("北の海＝北太平洋〜ベーリング海など", sz=40), 640, 100, lead=0.0)
    sh = 0.5 + 0.5 * math.sin(t * 1.1)


def wage_table(ctx, t, t_frame, t_cols, t_vals, hi_n=False, show_wage_t=None, dim=1.0):
    """表: 漁場 | 新米の取り分の平均 | 月給の中央値。枠は t_frame、行の中身は t_cols[i]、月給は show_wage_t"""
    a = fade(t, t_frame, 0.4)
    if a <= 0.003:
        return
    names = ("インド洋", "太平洋", "北の海")
    cols = (C_I, C_P, C_N)
    lays = ("181分の1", "188分の1", "193分の1")
    wages = ("約7ドル", "約7〜9ドル", "約8〜11ドル")
    X0, X1 = 260, 1660
    box(ctx, X0, 150, X1, 700, "#10284a", 0.95 * a, r=24)
    text(ctx, "漁場", 480, 215, 46, YEL, alpha=a)
    text(ctx, "新米の取り分の平均", 960, 215, 46, YEL, alpha=a)
    if show_wage_t is not None:
        text(ctx, "月給の中央値", 1400, 215, 46, YEL, alpha=fade(t, show_wage_t, 0.4) * a)
    wa._set(ctx, "#ffffff", 0.3 * a)
    ctx.rectangle(X0 + 20, 255, X1 - X0 - 40, 4)
    ctx.fill()
    order = (2, 1, 0) if show_wage_t is not None and False else (0, 1, 2)
    for r_i, k in enumerate(order):
        y = 345 + r_i * 140
        hi = hi_n and names[k] == "北の海"
        if hi:
            ctx.set_source_rgba(*hexrgb(YEL, a))
            ctx.set_line_width(8)
            rrect(ctx, X0 + 16, y - 56, X1 - X0 - 32, 112, 16)
            ctx.stroke()
        wa._set(ctx, cols[k], a)
        wa.rrect(ctx, X0 + 40, y - 36, 24, 72, 8)
        ctx.fill()
        text(ctx, names[k], 480, y, 56, WHITE, alpha=a)
        text(ctx, lays[k], 960, y, 72, YEL, alpha=a * fade(t, t_cols[k], 0.3))
        if show_wage_t is not None:
            text(ctx, wages[k], 1400, y, 62, YEL if hi or names[k] == "北の海" else WHITE, alpha=a * fade(t, t_vals, 0.4))


def sc_c4_tbl(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    wage_table(ctx, t, Sk("c4_diff", 0.0) - 0.5, (Sk("c4_ind", 0.4), Sk("c4_pac", 0.4), Sk("c4_north", 0.4)), None, hi_n=t >= Sk("c4_north", 0.45))
    Cd(ctx, t, "c4_north", 0.45, R("いちばん小さい取り分", sz=48, col=YEL), 960, 800, pad=(34, 16), border=YEL)


def sc_c4_want(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    wa.paper(ctx, 1010, 100, 760, 700, rot=0.0)
    text(ctx, "インド洋の船の契約書", 380, 90, 52, INKC)
    text(ctx, "181分の1", 380, 330, 120, PURPLE_TXT)
    gray_lines(ctx, 80, 450, 600, 3, 60)
    seal(ctx, 560, 600, 46)
    ctx.restore()
    Cd(ctx, t, "c4_want", 0.1, R("取り分が大きい　インド洋？", sz=56, col=YEL), 760, 300, pad=(40, 20), border=YEL)


def sc_c4_len(ctx, t):
    bg_sky_sea(ctx, t, 400, clouds=True)
    chart_card(ctx, 60, 480, 1860, 880)
    ts = Sk("c4_len", 0.1)
    for k, (w, col, nm) in enumerate(((900, C_N, "北の海"), (640, C_P, "太平洋"), (1150, C_I, "インド洋"))):
        y = 560 + k * 130
        f = ease(seg(t, ts + 0.3 * k, ts + 0.3 * k + 1.6))
        wa._set(ctx, col, 0.9)
        wa.rrect(ctx, 360, y - 36, w * f, 72, 14)
        ctx.fill()
        mini_ship(ctx, 360 + w * f + 60, y + 24, 90, hull3(k))
        text(ctx, nm, 190, y, 46, INKC)
    Cd(ctx, t, "c4_notonly", 0.35, R("割合だけでは船を比べられない", sz=48), 960, 150, pad=(34, 16))
    Cd(ctx, t, "c4_len", 0.0, R("航海の長さは船ごとに違う", sz=52, col=YEL), 960, 280, pad=(36, 18), border=YEL)


def sc_c4_wage(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    ctx.push_group()
    wa.pay_envelope(ctx, 880, 520, 360, -0.04, mark="取り分")
    ctx.pop_group_to_source()
    ctx.paint()
    text(ctx, "÷", 1130, 520, 120, INKC)
    wa.draw_calendar(ctx, 1300, 270, 380, 420, "月数", crossed=0)
    Cd(ctx, t, "c4_wage", 0.0, R("月給＝取り分の額 ÷ 航海の月数", sz=52, col=YEL), 1040, 140, pad=(36, 18), border=YEL)


def sc_c4_ans1(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    wage_table(ctx, t, -1, (-1, -1, -1), Sk("c4_answer1", 0.55), hi_n=True, show_wage_t=Sk("c4_answer1", 0.45) - 0.0)
    Cd(ctx, t, "c4_answer1", 0.4, R("数え方（油の値段の年・月数）で幅がある", sz=40), 960, 780, lead=0.3)
    Cd(ctx, t, "c4_answer1", 0.3, R("取り分はいちばん小さいのに、月給はいちばん高い", sz=48, col=YEL), 960, 850, pad=(34, 14), lead=0.2)


def sc_c4_ans2(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    wage_table(ctx, t, -1, (-1, -1, -1), -1, hi_n=True, show_wage_t=-1)
    Cd(ctx, t, "c4_avg", 0.5, R("平均でも中央値でも同じ向き", sz=48), 960, 780, pad=(34, 14))
    Cd(ctx, t, "c4_order", 0.4, R("数え方を4通り変えても同じ向き", sz=48, col=YEL), 960, 860, pad=(34, 14), border=YEL)


def map_ship(ctx, t, pos, col=YOU):
    x, y = pos
    disc(ctx, x, y - 50, 82, col, 0.85)
    draw_ship(ctx, x, y + 10, 120)


def sc_c4_follow(ctx, t):
    from whaling_map_data import xy
    wa.draw_map_seas(ctx, map_regions())
    p0, p1 = xy(205, 22), xy(187, 55)
    u = ease(seg(t, Sk("c4_follow", 0.1), Sk("c4_follow", 0.1) + 3.2))
    map_ship(ctx, t, (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u))
    map_labels(ctx, t, 0, 0, 0)
    card(ctx, t, SC_START["c4_follow"], None, R("北の海＝北太平洋〜ベーリング海など", sz=40), 640, 100)


BAR_X = (480, 960, 1440)


def barrel_chart(ctx, t, ta, tvals, hi_line=False, ghost=False):
    """1航海あたりの油（1樽＝100バレル）。ta/tvals は (北, 太平洋, インド洋) の出る時刻"""
    names = ("北の海", "太平洋", "インド洋")
    cols = (C_N, C_P, C_I)
    nb = (22.65, 17.98, 13.29)
    vals = ("2,265バレル", "1,798バレル", "1,329バレル")
    base = 760
    wa._set(ctx, INKC)
    ctx.rectangle(240, base + 8, 1440, 6)
    ctx.fill()
    for k in range(3):
        label(ctx, names[k], BAR_X[k], base + 56, 46, INKC, a=1.0)
        if t < ta[k]:
            continue
        n = nb[k]
        full = int(n)
        for i in range(full + 1):
            tt = ta[k] + 0.06 * i
            if t < tt:
                continue
            a = fade(t, tt, 0.2)
            sc = 1.0 if i < full else (n - full)
            if sc < 0.05:
                continue
            bx = BAR_X[k] + ((i % 5) - 2) * 62
            by = base - (i // 5) * 66
            ctx.push_group()
            draw_barrel(ctx, bx, by, 56 * (0.6 + 0.4 * sc), 64 * sc)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
        if t >= tvals[k]:
            card(ctx, t, tvals[k], None, [(vals[k], 56, YEL if k == 0 else WHITE)], BAR_X[k], base - 5 * 66 - 70 + (0 if k == 0 else 70 * k * 0.0), pad=(26, 12))


def sc_c4_many(ctx, t):
    band(ctx, NAVY, 0, H_)
    chart_card(ctx, 200, 150, 1720, 880)
    ta = (Sk("c4_many", 0.55), Sk("c4_n", 0.1), Sk("c4_p", 0.1))
    tv = (Sk("c4_n", 0.55), Sk("c4_p", 0.3), Sk("c4_i", 0.25))
    barrel_chart(ctx, t, ta, tv)
    card(ctx, t, SC_START["c4_many"] + 0.3, None, R("1航海あたりの油　1樽＝100バレル", sz=44), 960, 100)
    Cd(ctx, t, "c4_barrel", 0.3, R("1バレル＝31.5ガロン", sz=40), 1500, 190, lead=0.0)


def sc_c4_n(ctx, t):
    sc_c4_many(ctx, t)


def sc_c4_i(ctx, t):
    sc_c4_many(ctx, t)


def sc_c4_bone(ctx, t):
    band(ctx, NAVY, 0, H_)
    tm = Sk("c4_more", 0.0) - 0.3
    if t < tm:
        vals = (29270, 13998, 3672)
        texts = ("29,270ポンド", "13,998ポンド", "3,672ポンド")
        names = ("北の海", "太平洋", "インド洋")
        cols = (C_N, C_P, C_I)
        tb0 = SC_START["c4_bone"] + 0.6
        card(ctx, t, tb0, None, R("1航海あたりの鯨ひげ", sz=44), 960, 100)
        for k in range(3):
            y = 330 + k * 150
            ts_k = tb0 + 0.3 + 0.35 * k
            f = ease(seg(t, ts_k, ts_k + 1.0))
            wa._set(ctx, cols[k])
            wa.rrect(ctx, 420, y - 44, max(1.0, 1000 * vals[k] / 29270.0 * f), 88, 12)
            ctx.fill()
            text(ctx, names[k], 330, y, 46, "#ffffff", align="right")
            xx = 420 + 1000 * vals[k] / 29270.0 + 200
            card(ctx, t, ts_k + 1.0, None, R(texts[k], sz=46), min(xx, 1560) if k else 1160, y, pad=(24, 12))
    else:
        chart_card(ctx, 200, 150, 1720, 880)
        ta = (-5, -5, -5)
        tv = (-5, -5, -5)
        barrel_chart(ctx, t, ta, tv)
        ya = 760 - 5 * 66 - 40
        a = fade(t, tm, 0.4)
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.set_line_width(6)
        ctx.set_dash([16, 12])
        ctx.move_to(BAR_X[1] - 180, 760 - 4 * 66 - 66 * 1)
        ctx.line_to(BAR_X[0] + 180, 760 - 4 * 66 - 66 * 1)
        ctx.stroke()
        ctx.set_dash([])
        Cd(ctx, t, "c4_more", 0.4, R("北の海の船のほうが樽が多い", sz=48, col=YEL), 960, 110, pad=(34, 14), border=YEL)


def sc_c4_win(ctx, t):
    bg_sky_sea(ctx, t, 520)
    draw_ship(ctx, 640, 800 + bob(t, 5, 1.1, 0), 420, hull="#5b3a2a")
    draw_ship(ctx, 1280, 800 + bob(t, 5, 1.1, 1), 420, hull="#3f5f7a")
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    disc(ctx, 640, 360, 24, C_N)
    disc(ctx, 1280, 360, 24, C_P)
    Cd(ctx, t, "c4_win", 0.4, R("北の海を選べば、勝てる？", sz=58, col=YEL), 960, 180, pad=(40, 20), border=YEL)


def sc_c4_draw(ctx, t):
    bg_sky_sea(ctx, t, 520)
    draw_ship(ctx, 560, 800 + bob(t, 5, 1.1, 0), 420, hull="#5b3a2a")
    draw_ship(ctx, 1260, 800 + bob(t, 5, 1.1, 1), 420, hull="#3f5f7a")
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    disc(ctx, 560, 330, 24, C_N)
    disc(ctx, 1260, 330, 24, C_P)
    Cd(ctx, t, "c4_draw", 0.4, R("北の海1隻　対　太平洋1隻", sz=52), 910, 150, pad=(36, 16))
    Cd(ctx, t, "c4_draw", 0.7, R("/1万回", sz=40), 1700, 150, lead=0.0)
    Cd(ctx, t, "c4_yr", 0.4, R("1848〜58年に出た船", sz=48, col=YEL), 910, 250, pad=(34, 14))


def sc_c4_cmp(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    ts = Sk("c4_cmp", 0.2)
    for k, (w, col, nm) in enumerate(((1100, C_N, "北の海の1隻"), (760, C_P, "太平洋の1隻"))):
        y = 430 + k * 190
        f = ease(seg(t, ts + 0.4 * k, ts + 0.4 * k + 1.4))
        wa._set(ctx, col)
        wa.rrect(ctx, 480, y - 50, w * f, 100, 14)
        ctx.fill()
        text(ctx, nm, 450, y, 46, INKC, align="right")
    Cd(ctx, t, "c4_cmp", 0.3, R("月給の高いほうが勝ち", sz=56, col=YEL), 960, 190, pad=(40, 18), border=YEL)


def sc_c4_10k(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    order = list(range(100))
    random.Random(11).shuffle(order)
    t0 = Sk("c4_10k", 0.35)
    for j, idx in enumerate(order):
        ta = t0 + j * 0.03
        is_n = idx < 60
        a = fade(t, ta, 0.2) if t >= ta else 0.0
        if a > 0.003:
            x = 240 + (j % 10) * 62
            y = 250 + (j // 10) * 62
            wa._set(ctx, C_N if is_n else C_P, a)
            wa.rrect(ctx, x - 24, y - 24, 48, 48, 10)
            ctx.fill()
    card(ctx, t, Sk("c4_10k", 0.0) - 0.4, None, R("1つ＝100回", sz=40), 520, 130)
    Cd(ctx, t, "c4_6", 0.5, [("北の海が勝った", 44, WHITE), ("5,723〜6,687回", 64, "#ff9a78"), ("/1万回", 40, WHITE)], 1340, 300, pad=(40, 16))
    Cd(ctx, t, "c4_6", 0.5, R("数え方を4通り変えても約6割", sz=44), 1340, 470, lead=0.5)
    Cd(ctx, t, "c4_4", 0.4, [("太平洋が勝った", 44, WHITE), ("約4割", 80, C_P)], 1340, 660, pad=(40, 16))


def sc_c4_hit(ctx, t):
    bg_sky_sea(ctx, t, 520)
    chart_card(ctx, 160, 290, 1760, 870, CREAM)
    wa._set(ctx, "#6b4a35")
    ctx.rectangle(220, 742, 1480, 6)
    ctx.fill()
    for k, (x, hh) in enumerate(((360, 3), (660, 7), (960, 2), (1260, 5), (1560, 9))):
        mini_ship(ctx, x, 830, 150, C_N)
        for i in range(hh):
            ta = SC_START["c4_hit"] + 0.5 + 0.2 * (i + k)
            if t >= ta:
                ctx.push_group()
                draw_barrel(ctx, x - 40 + (i % 2) * 80, 740 - (i // 2) * 72, 66, 70)
                ctx.pop_group_to_source()
                ctx.paint_with_alpha(fade(t, ta, 0.2))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    Cd(ctx, t, "c4_hit", 0.4, R("同じ北の海の船でも、", "当たりと外れがある", sz=52), 960, 160, pad=(40, 18))


def sc_c4_luck(ctx, t):
    bg_sky_sea(ctx, t, 520)
    for k, x in enumerate((470, 960, 1450)):
        draw_ship(ctx, x, 800 + bob(t, 5, 1.1, k), 380, hull=hull3(k))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    Cd(ctx, t, "c4_slight", 0.4, [("船を選ぶ効果", 44, WHITE), ("約6割", 90, YEL)], 700, 170, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c4_luck", 0.35, R("当たった船の運のほうが大きい", sz=52), 1150, 400, pad=(36, 18))


def sc_c4_ans(ctx, t):
    bg_harbor(ctx, t, ship=(1600, 880, 330), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c4_ans", 0.15, [("答え", 48, WHITE), ("取り分がいちばん小さい北の海が", 52, WHITE), ("月給はいちばん高い", 70, YEL)], 1090, 200, pad=(44, 20), border=YEL, lead=0.3)
    Cd(ctx, t, "c4_ans", 0.55, R("それでも太平洋に勝つのは　約6割", sz=52), 1190, 420, pad=(36, 18), lead=0.3)


# ============================================================
# 5 まとめ・終了画面
# ============================================================
C5_X = (255, 725, 1195, 1665)
C5_ROWS = [[("問い1", 44, YEL), ("約2年11か月", 54, WHITE), ("で帰る", 44, WHITE)],
           [("問い2", 44, YEL), ("取り分は", 44, WHITE), ("284ドル", 64, YEL), ("工場の半分に", 42, WHITE), ("届かない", 42, WHITE)],
           [("問い3", 44, YEL), ("約13回に1回の", 44, WHITE), ("船は帰らない", 44, WHITE)],
           [("問い4", 44, YEL), ("北の海が勝つのは", 44, WHITE), ("約6割", 64, YEL)]]


def sc_c5_answers(ctx, t):
    bg_harbor(ctx, t, ship=(1560, 890, 330), boat=False, barrels=False)
    you(ctx, t, 330, GY)
    t0 = ch_start(5) + T_TITLE[5]
    for k, rows in enumerate(C5_ROWS):
        a = fade(t, t0 + 0.2 + 0.4 * k)
        if a <= 0.003:
            continue
        lit = (k in (0, 1) and Sk("c5_a", 0.0) <= t < Sk("c5_b", 0.0)) or (k in (2, 3) and t >= Sk("c5_b", 0.0))
        panel(ctx, rows, C5_X[k], 250, a=a, pad=(28, 18), border=YEL if lit else None)


def sc_c5_close(ctx, t):
    bg_sky_sea(ctx, t, 520)
    for k, x in enumerate((770, 1180, 1590)):     # 船どうしが触れないように（長さ約350・間隔410）
        draw_ship(ctx, x, 850 + bob(t, 5, 1.1, k), 280, hull=hull3(k))
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    you(ctx, t, 300, GY)
    Cd(ctx, t, "c5_q", 0.1, R("あなたなら、", "どの船に乗りますか？", sz=64, col=YEL), 700, 190, pad=(44, 20), border=YEL)
    Cd(ctx, t, "c5_note", 0.1, R("記録から計算した値", "最後まで乗っていた場合", "前借りと費用を引く前", sz=44), 1500, 280, pad=(32, 16))


END_SUB = ["よければ", "チャンネル登録・高評価", "お願いします"]


def end_rows():
    return [("新米の取り分の中央値", "284ドル"), ("帰らない船は", "約13回に1回"), ("北の海が太平洋に勝つのは", "約6割")]


def sc_end(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    label(ctx, "答え", 490, 90, 80, YEL, a=b)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 46, WHITE), (val, 70, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        a = fade(t, t9 + 0.1, 0.4)
        ctx.push_group()
        you(ctx, t, 1000, 900, 500)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1500, 740, a=fade(t, t9 + 0.3, 0.4))


# ============================================================
# 2026-11-08 追加: 新しく足した台本の行の場面・見やすさ（関所5）の部品
# ============================================================
CREAM = "#fbf7ea"
DARKTXT = "#2b1d10"
ORANGE_TXT = "#a63f10"        # 札・紙の上のオレンジ系の文字（コントラスト 4.5:1 以上）
PURPLE_TXT = "#5b3a9e"


def chart_card(ctx, x0, y0, x1, y1, col=CREAM, a=1.0):
    """グラフ・表・絵を載せる無地のカード（背景の絵に直接のせない）"""
    wa._set(ctx, col, a)
    wa.rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
    ctx.fill()


def path_progress(ctx, pts, u, col, w=10, outline="#10284a", head=34):
    """点列 pts を先頭から割合 u だけ、矢印つきで描く"""
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = L[-1] * clamp01(u)
    path = [pts[0]]
    for i in range(1, len(pts)):
        if L[i] <= tot:
            path.append(pts[i])
        else:
            f = (tot - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
            path.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f))
            break
    if len(path) < 2:
        return
    for c, ww in ((outline, w + 8), (col, w)):
        ctx.set_source_rgba(*hexrgb(c, 1.0))
        ctx.set_line_width(ww)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(*path[0])
        for q in path[1:]:
            ctx.line_to(*q)
        ctx.stroke()
    a, b = path[-2], path[-1]
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for c, hh in ((outline, head + 8), (col, head)):
        ctx.set_source_rgba(*hexrgb(c, 1.0))
        ctx.move_to(b[0] + hh * 0.5 * math.cos(ang), b[1] + hh * 0.5 * math.sin(ang))
        ctx.line_to(b[0] - hh * math.cos(ang - 0.5), b[1] - hh * math.sin(ang - 0.5))
        ctx.line_to(b[0] - hh * math.cos(ang + 0.5), b[1] - hh * math.sin(ang + 0.5))
        ctx.close_path()
        ctx.fill()


ARROW_PTS = [(22, -30), (50, -44), (100, -47), (140, -42), (175, -28), (200, -2), (206, 22), (196, 42), (187, 55)]


def sc_c1_far(ctx, t):
    from whaling_map_data import xy
    wa.draw_map_seas(ctx, map_regions())
    pts = [xy(*p) for p in ARROW_PTS]
    u = ease(seg(t, SC_START["c1_far"] + 0.5, Sk("c1_pac", 0.0) + 2.4))
    path_progress(ctx, pts, u, "#ffffff", 10)
    map_labels(ctx, t, 1e9, SC_START["c1_far"] + 0.5, SC_START["c1_far"] + 0.5)
    card(ctx, t, SC_START["c1_far"] + 0.3, None, R("ニューベッドフォードから", "アフリカの南を回って", sz=40), 330, 780)
    Cd(ctx, t, "c1_pac", 0.0, R("この頃の船は太平洋や北の海まで", sz=40), 700, 100, lead=0.0)


def sc_c1_lookout(ctx, t):
    bg_sky_sea(ctx, t, 640)
    k = 0.5 + 0.5 * math.sin(t * 0.9)
    draw_spout(ctx, 1500, 642, 100 + 40 * k, a=0.6 + 0.35 * k)
    draw_spout(ctx, 1280, 644, 70 + 30 * (1 - k), a=0.5 + 0.4 * (1 - k))
    band(ctx, "#a67c52", 860, H_)
    band(ctx, "#563a29", 860, 880)
    band(ctx, "#6b4a35", 60, 880, x0=700, x1=770)
    band(ctx, "#563a29", 60, 880, x0=700, x1=718)
    wa._set(ctx, "#563a29")
    wa.rrect(ctx, 620, 262, 230, 26, 8)
    ctx.fill()
    for px in (630, 835):
        band(ctx, "#6b4a35", 180, 262, x0=px, x1=px + 12)
    band(ctx, "#6b4a35", 180, 192, x0=630, x1=847)
    draw_sailor(ctx, 735 + 20 * math.sin(t * 0.7), 262, 200, you=False, facing=1)
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c1_lookout", 0.3, R("日の出から日没まで、", "交代で見張る", sz=44), 1300, 220, lead=0.0)


def sc_c1_port(ctx, t):
    bg_harbor(ctx, t, ship=(760, 830, 560), boat=False, barrels=False)
    ts = SC_START["c1_port"] + 0.8
    for i in range(4):
        ta = ts + 0.9 * i
        u = clamp01((t - ta) / 1.8)
        x0 = 1450 + 110 * i
        x = lerp(x0, 840 + 70 * i, ease(u))
        y = lerp(975, 718, ease(u)) - 90 * math.sin(math.pi * u)
        ctx.push_group()
        draw_barrel(ctx, x, y, 90 - 20 * u, 115 - 30 * u)
        ctx.pop_group_to_source()
        ctx.paint()
    crew(ctx, t, 1380, GY, 320, facing=-1)
    Cd(ctx, t, "c1_port", 0.3, R("途中の港で食べ物を積む", sz=44), 1350, 200, lead=0.0)


def lamp(ctx, x, y, s, t):
    """石油ランプのような明かり。(x, y) = 台の底の真ん中"""
    wa._set(ctx, "#7a5436")
    wa.rrect(ctx, x - s * 0.42, y - s * 0.12, s * 0.84, s * 0.12, s * 0.04)
    ctx.fill()
    wa._set(ctx, "#b07a48")
    wa.rrect(ctx, x - s * 0.24, y - s * 0.5, s * 0.48, s * 0.4, s * 0.1)
    ctx.fill()
    wa._set(ctx, "#cfe6f2", 0.8)
    ctx.arc(x, y - s * 0.78, s * 0.3, 0, 2 * math.pi)
    ctx.fill()
    fl = 1 + 0.12 * math.sin(t * 9) + 0.06 * math.sin(t * 15)
    wa._set(ctx, "#ffd84a")
    ctx.move_to(x, y - s * 1.0 * fl)
    ctx.curve_to(x + s * 0.16, y - s * 0.8, x + s * 0.12, y - s * 0.62, x, y - s * 0.62)
    ctx.curve_to(x - s * 0.12, y - s * 0.62, x - s * 0.16, y - s * 0.8, x, y - s * 1.0 * fl)
    ctx.fill()
    wa._set(ctx, "#ff9a3d")
    ctx.arc(x, y - s * 0.7, s * 0.07, 0, 2 * math.pi)
    ctx.fill()


def gear(ctx, cx, cy, r, teeth, rot, col="#7d8794"):
    wa._set(ctx, col)
    n = teeth * 2
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.8
        px, py = cx + rr * math.cos(a), cy + rr * math.sin(a)
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    ctx.close_path()
    ctx.fill()
    wa._set(ctx, CREAM)
    ctx.arc(cx, cy, r * 0.3, 0, 2 * math.pi)
    ctx.fill()


def sc_c1_oil(ctx, t):
    bg_room(ctx)
    chart_card(ctx, 380, 190, 1540, 830)
    lamp(ctx, 700, 700, 380, t)
    gear(ctx, 1180, 480, 170, 10, t * 0.5)
    gear(ctx, 1380, 640, 100, 7, -t * 0.5 * 10 / 7)
    Cd(ctx, t, "c1_oil", 0.1, R("鯨の油＝明かり・機械の油", sz=48, col=YEL), 960, 100, pad=(36, 16), border=YEL)


def baleen_plate(ctx, x, y, w, h, t, k):
    """鯨ひげの板（くしのような板）。(x, y) = 上の真ん中。内側の縁に細い毛"""
    wa._set(ctx, "#8a6a4a")
    ctx.move_to(x - w / 2, y)
    ctx.line_to(x + w / 2, y)
    ctx.line_to(x + w * 0.28, y + h)
    ctx.line_to(x - w * 0.28, y + h)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#d8c9a6", 1.0))
    ctx.set_line_width(3)
    for i in range(14):
        yy = y + 30 + (h - 40) * i / 13
        xx = x - w / 2 + (w / 2 - w * 0.28) * (yy - y) / h
        ctx.move_to(xx, yy)
        ctx.line_to(xx - 46 - 6 * math.sin(t * 1.5 + i + k), yy + 8)
        ctx.stroke()


def whale_head(ctx):
    """鯨の頭を横から見た図（しくみの図。右が口の先）。上あごの内側から鯨ひげが並んで垂れ下がる"""
    def bez(p0, p1, p2, u):
        return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
                (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])
    # 頭
    wa._set(ctx, "#4a5d73")
    ctx.move_to(250, 430)
    ctx.curve_to(420, 230, 1050, 200, 1520, 440)
    ctx.line_to(1530, 500)
    ctx.curve_to(1300, 720, 700, 860, 250, 720)
    ctx.close_path()
    ctx.fill()
    # 口の中
    wa._set(ctx, "#c98287")
    ctx.move_to(380, 520)
    ctx.curve_to(600, 340, 1100, 330, 1470, 485)
    ctx.curve_to(1250, 640, 750, 740, 380, 650)
    ctx.close_path()
    ctx.fill()
    # 鯨ひげ（上あごの内側の線から垂れ下がる板）
    A0, A1, A2 = (400, 515), (900, 300), (1450, 490)
    for i in range(44):
        u = 0.04 + 0.92 * i / 43
        x, y = bez(A0, A1, A2, u)
        ln = 70 + 230 * math.sin(math.pi * u) ** 1.3
        ctx.set_source_rgba(*hexrgb("#3b2f2a", 1.0))
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, y)
        ctx.line_to(x - 6, y + ln)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#d8c9a6", 1.0))
        ctx.set_line_width(6)
        ctx.move_to(x - 5, y + ln - 22)
        ctx.line_to(x - 7, y + ln + 4)
        ctx.stroke()
    # 目
    disc(ctx, 330, 610, 16, "#1b2430")


def sc_c1_baleen(ctx, t):
    bg_room(ctx)
    chart_card(ctx, 170, 175, 1750, 900)
    whale_head(ctx)
    tag(ctx, t, SC_START["c1_baleen"] + 0.5, None, "上あご", 900, 235, size=40)
    tag(ctx, t, Sk("c1_baleen", 0.45), None, "鯨ひげ（何百枚も並ぶ）", 1430, 800, size=40)
    Cd(ctx, t, "c1_baleen", 0.2, R("鯨ひげ＝上あごから並ぶ板", "（髪の毛や爪と同じ物質）", sz=44), 960, 90, pad=(36, 16), border=YEL)


def sc_c1_filter(ctx, t):
    bg_room(ctx)
    chart_card(ctx, 170, 175, 1750, 900)
    wa._set(ctx, "#6b4a35")
    wa.rrect(ctx, 470, 230, 1000, 40, 14)
    ctx.fill()
    for i in range(6):
        baleen_plate(ctx, 560 + i * 165, 270, 110, 430, t, i)
    t0 = Sk("c1_filter", 0.15)
    # 水の矢印（口の中 → 外）
    for j, yy in enumerate((380, 500, 620)):
        u = clamp01((t - t0 - 0.3 * j) / 1.6)
        if u > 0:
            arrow2(ctx, (260, yy), (260 + (1440 - 260) * ease(u), yy), "#2f86d0", 12, 0.9, head=34)
    # エサの粒（板の毛に残る）
    rng = random.Random(3)
    for k in range(26):
        sx, sy = 240 + rng.uniform(0, 60), 320 + rng.uniform(0, 360)
        stop = 400 + rng.uniform(0, 70)
        u = clamp01((t - t0 - 0.05 * k) / 1.4)
        disc(ctx, sx + (stop - sx) * ease(u), sy, 11, "#e8743b")
    tag(ctx, t, t0 + 0.6, None, "口の中", 330, 805, size=40)
    tag(ctx, t, t0 + 0.6, None, "外", 1600, 805, size=40)
    tag(ctx, t, SC_START["c1_filter"] + 0.3, None, "鯨ひげを大きく見た図", 960, 805, size=40)
    Cd(ctx, t, "c1_filter", 0.1, R("水だけ外へ。エサは残る", sz=48, col=YEL), 960, 90, pad=(36, 16), border=YEL)


def sc_c1_use(ctx, t):
    bg_room(ctx)
    chart_card(ctx, 380, 190, 1540, 830)
    # 服の芯（ひげの細い板が布の中に入っている）
    wa._set(ctx, "#9db7df")
    wa.rrect(ctx, 480, 300, 380, 440, 30)
    ctx.fill()
    for i in range(4):
        wa._set(ctx, "#d8c9a6")
        wa.rrect(ctx, 540 + i * 85, 320, 30, 400, 15)
        ctx.fill()
    # 傘の骨
    cx, cy = 1180, 400
    ctx.set_source_rgba(*hexrgb("#5a4630", 1.0))
    ctx.set_line_width(7)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(9):
        a = math.pi * (0.08 + 0.84 * i / 8)
        ctx.move_to(cx, cy - 90)
        ctx.curve_to(cx + 120 * math.cos(a) * 1.0, cy - 90 - 110 * math.sin(a), cx + 220 * math.cos(a), cy - 40 - 60 * math.sin(a) * 0.2, cx + 270 * math.cos(a), cy + 70 - 40 * math.sin(a))
        ctx.stroke()
    ctx.move_to(cx, cy - 90)
    ctx.line_to(cx, cy + 300)
    ctx.curve_to(cx, cy + 360, cx - 60, cy + 360, cx - 60, cy + 310)
    ctx.stroke()
    Cd(ctx, t, "c1_use", 0.2, R("服の芯・傘の骨", sz=48, col=YEL), 960, 100, pad=(36, 16), border=YEL)


def sc_c2_job(ctx, t):
    bg_deck(ctx, t)
    sw = math.sin(t * 2.2) * 40
    you(ctx, t, 760, GY)
    ctx.set_source_rgba(*hexrgb("#8a6945", 1.0))
    ctx.set_line_width(14)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(860, 700)
    ctx.line_to(960 + sw, 930)
    ctx.stroke()
    wa._set(ctx, "#d9c79a")
    wa.rrect(ctx, 920 + sw, 915, 100, 36, 10)
    ctx.fill()
    draw_sailor(ctx, 330, 430, 170, you=False, facing=1)
    crew(ctx, t, 1250, 990, 300, facing=-1)


def sc_c2_boat(ctx, t):
    bg_sky_sea(ctx, t, 520)
    k = 0.5 + 0.5 * math.sin(t * 0.9)
    draw_spout(ctx, 1500, 524, 90 + 30 * k, a=0.55 + 0.4 * k)
    by = 760 + bob(t, 6, 1.3)
    for i in range(4):
        draw_sailor(ctx, 520 + i * 150, by - 6, 210, you=False, facing=1)
    draw_boat(ctx, 760, by, 640)
    ctx.set_source_rgba(*hexrgb("#8a6945", 1.0))
    ctx.set_line_width(10)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(4):
        x = 520 + i * 150
        sw = math.sin(t * 2.0 + i * 0.4) * 30
        ctx.move_to(x + 10, by - 70)
        ctx.line_to(x + 80 + sw, by + 70)
        ctx.stroke()


def sc_c2_bed(ctx, t):
    band(ctx, "#3a281d", 0, H_)
    A, B, Cc = (330, 180), (330, 840), (1580, 510)
    wa._set(ctx, "#a67c52")
    ctx.move_to(*A)
    ctx.line_to(*B)
    ctx.line_to(*Cc)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#6b4a35", 1.0))
    ctx.set_line_width(26)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*A)
    ctx.line_to(*Cc)
    ctx.line_to(*B)
    ctx.stroke()
    for (P, Q, sgn) in ((A, Cc, 1), (B, Cc, -1)):
        ang = math.atan2(Q[1] - P[1], Q[0] - P[0])
        for i in range(3):
            f = 0.1 + 0.22 * i
            px, py = P[0] + (Q[0] - P[0]) * f, P[1] + (Q[1] - P[1]) * f
            ctx.save()
            ctx.translate(px, py)
            ctx.rotate(ang)
            wa._set(ctx, "#e6dcc3")
            wa.rrect(ctx, 0, 14 * sgn if sgn > 0 else -78, 200, 64, 10)
            ctx.fill()
            wa._set(ctx, "#8aa6cf")
            wa.rrect(ctx, 50, 18 * sgn if sgn > 0 else -74, 150, 56, 10)
            ctx.fill()
            ctx.restore()
    fl = 1 + 0.1 * math.sin(t * 7)
    disc(ctx, 1480, 510, 70 * fl, "#ffd84a", 0.35)
    disc(ctx, 1480, 510, 26, "#ffd84a")
    # 何の図かを示す: 船の絵の小窓で、船の先（へさき）に印
    chart_card(ctx, 1520, 40, 1895, 420, CREAM)
    wa.draw_ship(ctx, 1690, 330, 220, facing=1)
    ctx.set_source_rgba(*hexrgb("#e0a400", 1.0))
    ctx.set_line_width(8)
    ctx.arc(1830, 318, 44, 0, 2 * math.pi)
    ctx.stroke()
    tag(ctx, t, SC_START["c2_bed"] + 0.2, None, "船の先", 1640, 385, size=40)
    card(ctx, t, SC_START["c2_bed"] + 0.2, None, R("船の先の部屋を", "上から見た図", sz=40), 700, 95)


def sc_c2_food(ctx, t):
    bg_room(ctx, "#cdb48b", "#7a5436")
    wa._set(ctx, "#8a6945")
    wa.rrect(ctx, 220, 640, 1480, 70, 20)
    ctx.fill()
    disc(ctx, 960, 480, 270, "#f6f0e0")
    disc(ctx, 960, 480, 220, "#e8e2d2")
    ctx.save()
    ctx.translate(850, 470)
    ctx.rotate(-0.25)
    wa._set(ctx, "#b5573e")
    wa.rrect(ctx, -110, -60, 220, 120, 26)
    ctx.fill()
    wa._set(ctx, "#e6c6b8")
    ctx.rectangle(-110, -10, 220, 14)
    ctx.fill()
    ctx.restore()
    ctx.save()
    ctx.translate(1060, 430)
    ctx.rotate(0.2)
    wa._set(ctx, "#cfa763")
    wa.rrect(ctx, -80, -60, 160, 120, 14)
    ctx.fill()
    wa._set(ctx, "#a07d3e")
    for i in range(6):
        ctx.arc(-50 + (i % 3) * 50, -25 + (i // 3) * 50, 6, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()
    for i in range(14):
        a = 2 * math.pi * i / 14
        disc(ctx, 960 + 70 * math.cos(a) * (0.5 + 0.5 * (i % 2)) + 10, 580 + 28 * math.sin(a), 15, "#8a5a3a")


def sc_c2_facday(ctx, t):
    bg_town(ctx, t, fx=1000)
    u = ease(seg(t, Sk("c2_facday", 0.2), Sk("c2_facday", 0.2) + 2.0))
    draw_sailor(ctx, 380, GY, 400, you=False, facing=1, cap=False)
    draw_sailor(ctx, 760, GY, 400, you=False, facing=-1, cap=False)
    ctx.push_group()
    wa.pay_envelope(ctx, lerp(500, 640, u), 650 - 40 * math.sin(math.pi * u), 150, 0.0, mark="給料")
    ctx.pop_group_to_source()
    ctx.paint()


def sc_c2_ship(ctx, t):
    bg_office(ctx)
    you(ctx, t, 330, GY)
    ledger(ctx, t, you_txt=None, rows=("blank", "blank", "you"))
    Cd(ctx, t, "c2_ship", 0.3, R("航海が終わってから", "決まる", sz=44), 340, 330, pad=(34, 18))


def sc_c2_facpay(ctx, t):
    bg_town(ctx, t)
    you(ctx, t, 330, GY)
    pay_pile(ctx, t, 1400, 860, 8, 190, SC_START["c2_facpay"] + 0.5, 0.45, 4)
    Cd(ctx, t, "c2_facpay", 0.1, R("未熟練の工場・1か月25日働いた場合", sz=44), 960, 100, lead=-0.2)
    Cd(ctx, t, "c2_facpay", 0.4, R("同じ月数・同じ年", sz=44), 960, 190)


def sc_c2_fac(ctx, t):
    bg_town(ctx, t)
    you(ctx, t, 330, GY)
    pay_pile(ctx, t, 1400, 860, 4, 190, SC_START["c2_fac"] + 1.0, 0.6, 4)


def sc_c2_split(ctx, t):
    bg_office(ctx)
    wa.paper(ctx, 790, 80, 960, 800, rot=0.0)
    text(ctx, "契約書", 480, 100, 76, INKC)
    text(ctx, "190分の1", 480, 370, 150, ORANGE_TXT)
    text(ctx, "あなたの取り分", 480, 590, 70, INKC)
    gray_lines(ctx, 130, 690, 700, 3, 52)
    seal(ctx, 760, 715, 52)
    ctx.restore()
    you(ctx, t, 330, GY)
    Cd(ctx, t, "c2_lay", 0.5, [("新米の取り分　中央値", 44, WHITE), ("190分の1", 90, YEL)], 440, 150, pad=(36, 16), border=YEL, lead=0.0)
    Cd(ctx, t, "c2_lay", 0.5, R("10〜90%は", "160分の1〜200分の1", sz=40), 440, 330, lead=0.0)
    Cd(ctx, t, "c2_lay", 0.6, R("実際の新米14,649人の記録", sz=40), 440, 460, lead=0.0)


HIRE_COL = "#7bb36a"   # 途中の港で雇った船員（緑の服）


def fig_hire(ctx, t, ts, hire_t=None):
    """乗組員10人（1人＝出港のときの1割）。6人と少しが船を離れ、途中の港で雇った緑の船員が空いた所に入る"""
    bg_sky_sea(ctx, t, 600)
    band(ctx, "#a67c52", 760, H_)
    band(ctx, "#8c6440", 760, 776)
    for k in range(10):
        x = 250 + k * 158
        if k < 6:
            a = 1 - clamp01((t - ts - 0.45 * k) / 0.5)
        elif k == 6:
            a = 1 - 0.7 * clamp01((t - ts - 0.45 * 6) / 0.5)
        else:
            a = 1.0
        u = 0.0
        if hire_t is not None and k < 7 and t >= hire_t + 0.5 * k:
            u = fade(t, hire_t + 0.5 * k, 0.6)
        if k == 6:
            a *= (1 - u)
        gone = (1 - a) * (1 - u) if k < 7 else 0.0
        if gone > 0.02:   # 船を離れた人の空いた場所（白い点線の人形）
            ctx.save()
            ctx.set_source_rgba(1, 1, 1, 0.75 * gone)
            ctx.set_line_width(5)
            ctx.set_dash([14, 10])
            ctx.arc(x, 930 - 290 * 0.86, 34, 0, 2 * math.pi)
            ctx.stroke()
            wa.rrect(ctx, x - 52, 930 - 290 * 0.72, 104, 290 * 0.72, 30)
            ctx.stroke()
            ctx.restore()
        if a > 0.02:
            ctx.push_group()
            crew(ctx, t, x - (90 * (1 - a) if k < 6 else 0), 930, 290, ph=k)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
        if u > 0.02:
            ctx.push_group()
            wa.draw_sailor(ctx, x + 160 * (1 - u), 930 + math.sin(t * 1.5 + k) * 3.0, 290, color=HIRE_COL)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(u)


def sc_c3_63(ctx, t):
    ts = Sk("c3_63", 0.15)
    fig_hire(ctx, t, ts)
    Cd(ctx, t, "c3_63", 0.2, R("ジョージ・ハウランド号", "1隻の例", sz=44), 560, 190)
    Cd(ctx, t, "c3_63", 0.45, [("出港のときの乗組員のうち", 44, WHITE), ("63%", 110, YEL)], 1300, 330, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c3_63", 0.5, R("死亡・下船・逃亡を合わせた数", "6回の航海の平均", sz=40), 560, 400, lead=0.4)


def sc_c3_hire(ctx, t):
    fig_hire(ctx, t, Sk("c3_63", 0.15), hire_t=Sk("c3_hire", 0.3))
    Cd(ctx, t, "c3_hire", 0.1, R("途中の港で新しい乗組員を雇う", sz=48), 960, 190, pad=(36, 16))


def sc_c3_one(ctx, t):
    fig_hire(ctx, t, Sk("c3_63", 0.15), hire_t=Sk("c3_hire", 0.3))
    Cd(ctx, t, "c3_one", 0.0, R("1隻の例。全体の割合ではない", sz=44, col=YEL), 960, 190, pad=(36, 16), border=YEL, lead=0.1)


def sc_c4_vs(ctx, t):
    bg_sky_sea(ctx, t, 520)
    draw_ship(ctx, 640, 800 + bob(t, 5, 1.1, 0), 420, hull="#5b3a2a")
    draw_ship(ctx, 1280, 800 + bob(t, 5, 1.1, 1), 420, hull="#3f5f7a")
    band(ctx, "#a07d57", 880, H_)
    band(ctx, "#b8946a", 880, 898)
    disc(ctx, 640, 360, 24, C_N)
    disc(ctx, 1280, 360, 24, C_P)
    Cd(ctx, t, "c4_vs", 0.4, R("北の海　対　太平洋", sz=64, col=YEL), 960, 180, pad=(40, 20), border=YEL)


def loss_table(ctx, t, t_frame, t_rows, hi_t=None):
    a = fade(t, t_frame, 0.4)
    if a <= 0.003:
        return
    names = ("北の海", "太平洋", "インド洋")
    cols = (C_N, C_P, C_I)
    nums = ("11/160航海", "32/366航海", "6/56航海")
    rates = ("約15回に1回", "約11回に1回", "約9回に1回")
    X0, X1 = 200, 1720
    box(ctx, X0, 130, X1, 720, "#10284a", a, r=24)
    text(ctx, "漁場", 400, 200, 46, YEL, alpha=a)
    text(ctx, "帰らなかった船", 900, 200, 46, YEL, alpha=a)
    text(ctx, "割合", 1430, 200, 46, YEL, alpha=a)
    wa._set(ctx, "#ffffff", 0.3 * a)
    ctx.rectangle(X0 + 20, 240, X1 - X0 - 40, 4)
    ctx.fill()
    for k in range(3):
        y = 340 + k * 120
        wa._set(ctx, cols[k], a)
        wa.rrect(ctx, X0 + 40, y - 36, 24, 72, 8)
        ctx.fill()
        text(ctx, names[k], 400, y, 56, WHITE, alpha=a)
        ar = a * fade(t, t_rows[k], 0.3)
        text(ctx, nums[k], 900, y, 56, YEL, alpha=ar)
        text(ctx, rates[k], 1430, y, 56, WHITE, alpha=ar)
    if hi_t is not None and t >= hi_t:
        ah = fade(t, hi_t, 0.4) * a
        ctx.set_source_rgba(*hexrgb(YEL, ah))
        ctx.set_line_width(8)
        rrect(ctx, X0 + 16, 280, X1 - X0 - 32, 380, 16)
        ctx.stroke()


def sc_c4_danger(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    loss_table(ctx, t, SC_START["c4_danger"] + 0.3, (1e9, 1e9, 1e9))
    Cd(ctx, t, "c4_danger", 0.3, R("北の海は危ない海だった？", sz=52, col=YEL), 960, 800, pad=(36, 16), border=YEL)


def _loss_rows():
    return (Sk("c4_loss", 0.4), Sk("c4_loss", 0.6), Sk("c4_loss", 0.8))


def sc_c4_loss(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    loss_table(ctx, t, -1, _loss_rows())
    Cd(ctx, t, "c4_loss", 0.2, R("1848〜58年に出た船", sz=44), 960, 800, pad=(36, 16))


def sc_c4_ten(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    loss_table(ctx, t, -1, _loss_rows(), hi_t=Sk("c4_ten", 0.2))
    Cd(ctx, t, "c4_ten", 0.2, R("どの漁場も10回に1回ほど", sz=52, col=YEL), 960, 800, pad=(36, 16), border=YEL)


def sc_c4_small(ctx, t):
    bg_room(ctx, "#cfdff0", "#7e9bb8")
    loss_table(ctx, t, -1, _loss_rows())
    Cd(ctx, t, "c4_small", 0.2, R("偶然でもこれくらいの差は出る", sz=52, col=YEL), 960, 800, pad=(36, 16), border=YEL)

# ============================================================
# 区切り（ここまで／ここから・小さな船が進む）
# ============================================================

# ============================================================
# 区切り（ここまで／ここから・小さな船が進む）。engine/longkit.py の Eyecatch を、平たい地・白と黄色の文字で描き直したもの
# ============================================================
EC_LEFT = ("約2年11か月で帰る", "取り分は284ドル", "工場の半分に届かない")
EC_RIGHT = ("帰らない船は何隻？", "どの船に乗る？")
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
        draw_ship(ctx, x, 912 - bob, 170)


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
    if name == "c2_ans":
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


BELLS = [Sk("c0_res", 0.62), Sk("c1_med", 0.45), Sk("c2_med", 0.5), Sk("c3_13", 0.4), Sk("c4_6", 0.5)]


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, _bgm(DUR, lf.SR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for n in range(1, LAST_CH + 1):
        mx.add(S(f"ch{n}"), whoosh(0.6), 0.3)
    if EC:
        for i_, ts_ in enumerate(EC.step_times()):
            mx.add(ts_, bubble_pop(seed=i_, high=bool(i_ % 2)), 0.32)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(Sk("c5_q", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(Sk("c5_sub", 0.0) + 0.2, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（要所8枚）
# ============================================================
def still_list():
    return [
        ("1_open", "冒頭 いくら稼げますか", 1.6),
        ("2_c1", "問い1 何年で帰れる？", Sk("c1_med", 0.9)),
        ("3_c2_fac", "問い2 工場との比べ", Sk("c2_half", 0.9)),
        ("4_c2_adv", "問い2 前借り", Sk("c2_third", 0.9)),
        ("5_rest", "区切り", T_RS0 + 1.9),
        ("6_c3", "問い3 帰らない船", Sk("c3_129", 0.95)),
        ("7_c4_map", "問い4 地図", Sk("c4_three", 0.95)),
        ("8_c5", "まとめ", Sk("c5_b", 0.9)),
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




WATCH = ["捕鯨船", "新米", "取り分", "前借り", "中央値", "ベーリング", "ニューベッドフォード", "漁場", "バレル", "鯨ひげ", "北の海", "拿捕", "ジョージ・ハウランド", "1,666航海", "190分の1"]


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
    _val("札「284ドル」(冒頭)", "c0_res", 0.5),
    _fr("1万人の帯の枠(問い1)", "c1_band", "c1_sort"), _val("札「約2年11か月」", "c1_med", 0.4), _val("札「21.3か月」", "c1_p10", 0.35),
    _fr("取り分の山の枠", "c2_sort", "c2_sort"), _val("札「284ドル」", "c2_med", 0.5), _val("札「146ドル」", "c2_p10", 0.4), _val("札「478ドル」", "c2_p90", 0.4),
    _val("札「約600ドル」", "c2_600", 0.5), _val("札「168人」", "c2_168", 0.4), _val("札「1,948人」", "c2_5in1", 0.4),
    _val("札「129航海」", "c3_129", 0.5), _val("札「約13回に1回」", "c3_13", 0.35), _val("札「63%」", "c3_63", 0.45),
    _fr("表の枠(取り分の割合)", "c4_tbl", "c4_diff"), _val("表「1/181」", "c4_ind", 0.4), _val("表「1/193」", "c4_north", 0.4),
    _fr("樽の棒グラフの枠", "c4_many", "c4_many"), _val("札「2,265バレル」", "c4_n", 0.55), _val("札「5,723〜6,687回」", "c4_6", 0.5),
]
ALL_CUES.append(lk.Cue("2本の棒の枠(工場)", "frame", Sk("c2_half", 0.0) - 1.0, Sk("c2_half", 0.0) - 0.6, ID["c2_half"]))
ALL_CUES.append(lk.Cue("月給の列", "frame", Sk("c4_answer1", 0.0) - 1.0, Sk("c4_answer1", 0.0) - 0.6, ID["c4_answer1"]))



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




def _allowed_nums():
    md = NARR_PATH.read_text(encoding="utf-8")
    md = md[md.index("## 0"):]
    ok = {float(m.replace(",", "")) for m in _re.findall(NUM_RE, md)}
    ok |= set(float(x) for x in range(0, 61))                      # 問いの番号・目盛り
    ok |= {100.0, 200.0, 400.0, 600.0, 800.0, 160.0, 8.22, 31.5}   # 軸の目盛り・凡例
    nm = (ROOT / "out" / SLUG / "numbers.md").read_text(encoding="utf-8")                # numbers.md にある数字は画面に出してよい
    ok |= {float(m.replace(",", "")) for m in _re.findall(NUM_RE, nm)}
    return ok


def _ym(months):
    m = int(math.floor(months + 0.5))
    y, r = divmod(m, 12)
    return f"約{y}年{r}か月"


def _bbox_h(kind, L):
    return L


def scene_checks(frames=None):
    txt = lambda k: split_reading(tl.clip(ID[k]).text)[0]
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本 ----
    A(f"台本: 章は6つ（0〜5）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 6 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない・読みの補正は空（台本の {表記|よみ} を使う）", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()) and not READ_FIX)
    A(f"題字「{''.join(QROWS)}」は第0章の題名「{CH_TITLES[0]}」と同じ言葉", "".join(QROWS).replace("？", "") == CH_TITLES[0])
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S("c0_0"), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:])]
    A(f"台本: 冒頭（第0章）の文と文の間は 0.3秒（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし", all(abs(g - 0.3) < 0.011 or (PACE_TRIAL and abs(g - 1.0) < 0.011) for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch1"))
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
    last2 = [i for i in LINES if LINES[i][0] == 2][-1]
    A(f"区切り: 問い2（第2章）のあと・問い3（第3章）の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(last2) - 1e-6 and abs(T_RS1 - S("ch3")) < 1e-6 and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    pos = (T_RS0 + T_RS1) / 2 / DUR
    A(f"区切り: 動画の {pos:.1%} のところ（30〜75%）・声の行なし", 0.30 <= pos <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 小さな船は左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ進む・泡の音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    # ---- 冒頭 ----
    nums0 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and it.id.startswith("c0_"):
            s0 = _re.sub(r"\d+年", "", split_reading(it.text)[0])
            nums0 |= set(_re.findall(r"\d[\d,]*", s0))
    A(f"台本: 冒頭（第0章）の声の数字は3個以内・年の名前は数えない（{sorted(nums0)}）", len(nums0) <= 3)
    t284 = Sk("c0_res", 0.62)
    A(f"冒頭の結果の数字（284ドル）を言うのは約 {t284:.1f}秒（文の頭 {Sk('c0_res'):.1f}秒。本番の声は30秒以内。2026-11-08 場面の間をユーザーの指示で広げたので31秒まで）", t284 <= (29.5 if FAKE else (31.0 if PACE_TRIAL else 30.0)))
    # ---- 声の数字 = data.json ----
    D = RES
    wins = [r["wins"] for r in D["readings"]]
    exp = [("c0_lay", "190分の1"), ("c0_res", f"{ihalf(D['take'][2])}ドル"), ("c1_med", _ym(D["months"][2])), ("c1_p10", _ym(D["months"][1]).replace("約", "約")),
           ("c1_p90", "4年以上"), ("c2_lay", f"{ihalf(D['lay'][1])}分の1"), ("c2_med", f"{ihalf(D['take'][2])}ドル"), ("c2_p10", f"{ihalf(D['take'][1])}ドル"),
           ("c2_p90", f"{ihalf(D['take'][3])}ドル"), ("c2_month", f"約{ihalf(D['wage'][2])}ドル"), ("c2_600", "約600ドル"), ("c2_168", f"{D['over_factory']}人"),
           ("c2_5in1", "約5人に1人"), ("c3_1666", f"{D['mid']:,}回"), ("c3_129", f"{D['lost']}航海"), ("c3_13", f"約{ihalf(D['mid'] / D['lost'])}回に1回"),
           ("c3_82", f"{D['lost_lm']}航海"), ("c3_63", "63%"), ("c4_ind", f"{ihalf(D['lays']['インド洋'])}分の1"), ("c4_pac", f"{ihalf(D['lays']['太平洋'])}分の1"),
           ("c4_north", f"{ihalf(D['lays']['北の海'])}分の1"), ("c4_n", f"{D['catch']['北の海']['barrels']:,}バレル"), ("c4_p", f"{D['catch']['太平洋']['barrels']:,}バレル"),
           ("c4_6", "約6割")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A(f"data.json: 取り分 {D['take']}・帰るまで {D['months']}・工場 {D['land_median']}（声は約600ドル）・上回る {D['over_factory']}/{D['over_low']}/{D['over_high']}・帰らない {D['lost']}/{D['mid']}・1隻ずつ {min(wins)}〜{max(wins)}回",
      D["use"] == 1850 and D["n"] == 10000 and 580 <= D["land_median"] <= 650 and (D["over_factory"], D["over_low"], D["over_high"]) == (168, 685, 1948)
      and (D["lost"], D["lost_lm"], D["mid"]) == (129, 82, 1666) and (min(wins), max(wins)) == (5723, 6687) and D["catch"]["北の海"]["bone"] == 29270
      and D["catch"]["太平洋"]["bone"] == 13998 and D["catch"]["インド洋"]["bone"] == 3672 and D["catch"]["インド洋"]["barrels"] == 1329)
    A(f"帯・山: 帰るまでの月数の山 {sum(HM['counts'])}人・取り分の山 {sum(HT['counts'])}人 が 1万人", sum(HM["counts"]) == 10000 and sum(HT["counts"]) == 10000)
    A(f"帯・山: 10%点より短い {sum(HM['counts'][:7])}・4年以上 {sum(HM['counts'][16:])} ≈ data.json（4年以上 {D['months_share']['ge48']}）",
      sum(HM["counts"][16:]) == D["months_share"]["ge48"])
    A(f"絵の数: 船の格子 {N_SHIPS}（1隻＝10航海→167隻≈1,666）・赤く傾く {len(LOST)}（129航海≈12.9隻）・樽 22.65/17.98/13.29（1樽＝100バレル）",
      N_SHIPS == 167 and len(LOST) == 13 and len(set(LOST)) == 13 and round(D["catch"]["北の海"]["barrels"] / 100, 2) == 22.65
      and round(D["catch"]["太平洋"]["barrels"] / 100, 2) == 17.98 and round(D["catch"]["インド洋"]["barrels"] / 100, 2) == 13.29)
    A(f"主役の大きさ: あなた {YOU_H}px・冒頭 {OPEN_YOU_H}px は 画面の高さ {lf.H}px の 36〜46%（{YOU_H / lf.H:.0%}）", 0.36 <= YOU_H / lf.H <= 0.46 and 0.36 <= OPEN_YOU_H / lf.H <= 0.46)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件 {[b[0] for b in bad[:4]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面の切りかえ: 文の途中で場面が替わらない（{mid_sc[:3]}）", not mid_sc)
    A("グラフ: 帯・山・点は 0.26秒・0.03秒おき… 積み上げは 1本 0.26秒（0.25秒以上）", 0.26 >= 0.25)
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
        tokens = [("284ドル", "c0_res"), ("約2年11か月", "c1_med"), ("146ドル", "c2_p10"), ("478ドル", "c2_p90"), ("約600ドル", "c2_600"), ("168人", "c2_168"),
                  ("1,948人", "c2_5in1"), ("129航海", "c3_129"), ("約13回に1回", "c3_13"), ("63%", "c3_63"), ("181分の1", "c4_ind"), ("188分の1", "c4_pac"),
                  ("193分の1", "c4_north"), ("2,265バレル", "c4_n"), ("1,798バレル", "c4_p"), ("5,723〜6,687回", "c4_6"), ("約4割", "c4_4")]
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
        bad_words = sorted({e[0] for t_, e in allt if any(w in e[0] for w in ("銛", "血", "解体", "殺", "手にする", "受け取る", "持って帰る"))})
        A(f"画面に「銛」「血」「解体」「殺」や言い切らない言い方（手にする・受け取る・持って帰る）の文字を出さない: {bad_words}", not bad_words)
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
        A(f"終了画面: 登録のお願い（{Sk('c5_sub'):.1f}秒〜）の{Sk('c5_sub') - T_ES:.1f}秒前から最後まで（{DUR - T_ES:.1f}秒・6〜8秒）",
          0.2 <= Sk("c5_sub") - T_ES <= 1.0 and 6.0 <= DUR - T_ES <= 8.0 and T_ES > Ek("c5_note") - 1e-6)
        end_t = min(DUR - 0.2, Sk("c5_sub") + 1.5)
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
    if not (Path(__file__).resolve().parent / "contrast_audit.py").exists():
        print("  （sims/contrast_audit.py が無いので、コントラストの点検は飛ばします）")
        return
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
    n = int(DUR / step)
    for i in range(n):
        t = i * step
        FIG_LOG = []
        ctx = cairo.Context(surf)
        draw(ctx, t, sub=False)
        figs, FIG_LOG = FIG_LOG, None
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
    print(f"字幕の帯と人物の足もと: かぶり {len(rows)} か所 → {out}")
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
    print(f"  284ドルを言う: {Sk('c0_res', 0.62):.1f}秒（文 {Sk('c0_res'):.1f}〜{Ek('c0_res'):.1f}秒）・区切り {_ts(T_RS0)}〜{_ts(T_RS1)}（{(T_RS0 + T_RS1) / 2 / DUR:.1%}）")
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
