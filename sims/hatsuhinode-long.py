"""初日の出ロング「あなたは一生で何回、初日の出を見られる？」（横型ロング）— 2026-11-11 作成。
場面（描画・声の並び・照合・静止画）。作り・道具・点検は sims/penguin-long.py と同じ。

  python -X utf8 sims/hatsuhinode-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/hatsuhinode-long.py --fake-voice --contrast       文字のコントラスト（--scenecheck のあと）
  python -X utf8 sims/hatsuhinode-long.py --fake-voice --stills         要所の静止画と 480px の一覧（out/hatsuhinode-long/stills/・stills_key_480.png）
  python -X utf8 sims/hatsuhinode-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/hatsuhinode-long/scene_work/）
  python -X utf8 sims/hatsuhinode-long.py --fake-voice --sheet          本編の全場面の静止画一覧（out/hatsuhinode-long/body_stills_480*.png）
  python -X utf8 sims/hatsuhinode-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/hatsuhinode-long.py --readings                    声の読み（readings.log）
  python -X utf8 sims/hatsuhinode-long.py --docs                        文字起こし・読み・チャプター

台本: publish/hatsuhinode-long/narration_B.md（文は変えない）。
数字: research/hatsuhinode/H6.json を an6.py と同じ計算（乱数の種 20261111）で回した値。起動時に out/hatsuhinode-long/numbers.md と一致を assert する（手で書き写さない）。
絵: 地図は Natural Earth（out/hatsuhinode-long/src/japan_outline.json）。人は sims/hatsuhinode_sprites/person_blue.png だけ。
本番の mp4 の書き出しはここでは行わない（--fake-voice まで。--render は統括とユーザーのOKのあと）。
"""

import json
import math
import pickle
import random
import re as _re
import sys
from dataclasses import dataclass
from pathlib import Path

SLUG = "hatsuhinode-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
RES = ROOT / "research" / "hatsuhinode"

import cairo  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import core  # noqa: E402
from engine import longform as lf  # noqa: E402
from engine import longkit as lk  # noqa: E402
from engine.core import (bell, blip, check_answers, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, text, text_width,  # noqa: E402
                         whoosh)
from engine.voice import split_reading  # noqa: E402


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAKE = "--fake-voice" in sys.argv
# 場面の切りかえの前後の間（ツバメと同じ。第0章は 0.6＋0.4、ほかの章は 0.7＋0.6）
PACE_TRIAL = "--pace-old" not in sys.argv
TRIAL_LEAD = 0.7   # 場面が替わってから声まで
TRIAL_TAIL = 0.6   # 声が終わってから場面が替わるまで
TRIAL_CH = tuple(f"c{n}_" for n in range(0, 6))
TRIAL_PAIR = {"c0_": (0.6, 0.4), **{f"c{n}_": (TRIAL_LEAD, TRIAL_TAIL) for n in range(1, 8)}}
# 枠（グラフ・帯・地図・表）が出そろうのに時間がかかる図は 1.05秒前から出す
TRIAL_LEAD_KEY = {k_: 1.05 for k_ in (
    "c0_cond", "c0_stn", "c1_t36", "c1_box", "c1_graph", "c1_count", "c1_sr", "c2_cand", "c2_years", "c2_akmed", "c2_why", "c3_count", "c3_20", "c3_9370",
    "c3_chk", "c4_map", "c4_mae", "c4_tok", "c4_sap", "c4_cmp", "c4_tbl", "c5_sum")}
TRIAL_LEAD_KEY.update(c4_p2=0.95, c4_p3=0.95)       # 表のページは、その文の声の0.5秒前にそろう



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
# 台本の読み込み（tsubame-long.py と同じ）
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
            cur = None                     # 番号のない見出し（「守った決まり」「概要欄に書く前提」）から先は台本ではない
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


# ---- 読みの補正: 台本に {表記|よみ} が入っているので、ここは空 ----
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


VOICE_PAUSES = (0.0, 0.10)    # 読点は元の声の間のまま。文の間だけ少し足す
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
        # 数字（1,081・14.4 など）の途中で折らない: 前の行の終わりの数字を次の行へ送る
        while out[i - 1] and out[i] and (out[i - 1][-1].isdigit() or out[i - 1][-1] in ",.") and (out[i][0].isdigit() or out[i][0] in ",."):
            out[i] = out[i - 1][-1] + out[i]
            out[i - 1] = out[i - 1][:-1]
    return [x for x in out if x]


lf.wrap_subtitle = _wrap_kinsoku
# 字幕は 45px・行の間 54px（ツバメと同じ）
lf.SUB_SIZE = 45
lf.SUB_LINE_H = 54
# 文字は太いゴシック（メイリオの太字）
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

# ============================================================
# 場面の合図（文の一部で探す。見つからなければ止める）
# ============================================================
from long_bgm import bgm_track as _bgm  # noqa: E402  めでたしかめのロングの標準BGM（カスミソウ）

ANCH = {
    # 0 あなたは一生で何回、初日の出を見られる？
    "c0_q": (0, "あなたは一生で何回、初日の出を見られるでしょうか"), "c0_32": (0, "36年のうち32回"), "c0_2": (0, "36年のうち2回しか"),
    "c0_diff": (0, "住む県によって"), "c0_near": (0, "どちらに近いでしょうか"), "c0_stn": (0, "県庁所在地にある気象台"), "c0_dou": (0, "2回しか見えなかった県は"), "c0_last": (0, "最後に、全国の地図で"), "c0_cond": (0, "条件をそろえます"), "c0_use": (0, "使うのは"),
    "c0_day": (0, "元日の朝に日が差した年"), "c0_life": (0, "一生は、80回"),
    # 1 東京
    "c1_q": (1, "最初の問いです"), "c1_guess": (1, "三つから、一つ選んでみてください"), "c1_t36": (1, "36回の元日のうち30回"),
    "c1_luck": (1, "運のよい人と"), "c1_tenk": (1, "その幅を見るために"), "c1_box": (1, "36本のうち30本"), "c1_draw": (1, "1本引きます"),
    "c1_hit": (1, "当たりなら"), "c1_sep": (1, "去年の天気が今年に関係しないかは"), "c1_rep": (1, "くり返します"), "c1_graph": (1, "グラフにします"), "c1_axes": (1, "横は見えた回数"),
    "c1_def": (1, "ちょうど真ん中の人の値"), "c1_med": (1, "中央値は、67回でした"), "c1_worst": (1, "いちばん少なかった人は、54回"),
    "c1_best": (1, "いちばん多かった人は、79回"), "c1_ans": (1, "答えです。東京に住むあなたは"), "c1_8": (1, "約8割は見られる"),
    "c1_most": (1, "ほとんどの年で見られるところ"), "c1_count": (1, "見えた年の数え方"), "c1_jma": (1, "見えた年の数え方です"),
    "c1_rule": (1, "合計30分以上差した年を"), "c1_cloud": (1, "昇る瞬間が雲に隠れても"), "c1_sr": (1, "県ごとに計算しています"), "c1_ex": (1, "県ごとに計算しています"), "c1_chg": (1, "住む県が変わると"),
    # 2 秋田
    "c2_q": (2, "二つ目の問いです"), "c2_cand": (2, "北海道、石川、秋田の三つ"), "c2_three": (2, "三つとも、冬に雪の多いところ"),
    "c2_guess": (2, "一つ選んでみてください"), "c2_same": (2, "東京と同じ決め方"), "c2_ans": (2, "答えです。36年で2回だけだったのは"),
    "c2_years": (2, "2011年と、2017年"), "c2_sap": (2, "北海道は、36年で10回"), "c2_kan": (2, "石川は、36年で7回"), "c2_orig": (2, "もとの記録は、36年で2回しか"), "c2_chg": (2, "もし3回だったら"),
    "c2_est": (2, "なので、秋田の数字は目安です"), "c2_akmed": (2, "中央値4回です"), "c2_akworst": (2, "人は、0回でした"), "c2_akbest": (2, "13回です"),
    "c2_zero": (2, "92人は"), "c2_imag": (2, "思い浮かべてください"), "c2_morn": (2, "窓の外を見ます"), "c2_gray": (2, "空は灰色"),
    "c2_next": (2, "次の年も"), "c2_why": (2, "どうして、こんなに見えない"), "c2_wind": (2, "理由は、冬の風にあります"),
    "c2_sea": (2, "水蒸気をもらって"), "c2_mt": (2, "山を越えられず"), "c2_pac": (2, "太平洋側には"), "c2_cant": (2, "この記録だけでは分かりません"),
    "c2_found": (2, "分かったことです"),
    # 3 続く年数
    "c3_q": (3, "の問いです。初日の出が見られない年は"), "c3_this": (3, "この章でも"), "c3_lost": (3, "外れた年です"), "c3_streak": (3, "続けて何年も出る人"),
    "c3_count": (3, "いちばん長く続いた年数を比べます"), "c3_guess": (3, "まず東京です"), "c3_ans": (3, "答えです。東京は"),
    "c3_ak": (3, "秋田は、中央値で33年"), "c3_age": (3, "33歳になるまで"), "c3_20": (3, "20年以上続けて見られない人を数えます"),
    "c3_q4": (3, "一生の4分の1"), "c3_9370": (3, "9,319人"), "c3_most": (3, "ほとんどの人が"), "c3_kan": (3, "石川では、1万人のうち"),
    "c3_tok": (3, "東京では、0人"), "c3_hit": (3, "たまたま初日の出を見られた年"), "c3_next": (3, "その翌年は"), "c3_g2": (3, "今年も見えやすい気がします"),
    "c3_chk": (3, "47都道府県の、36年の記録で"), "c3_dot": (3, "点1つが、1つの県です"), "c3_a4": (3, "今年にほとんど関係しません"), "c3_new": (3, "新しいくじとして"), "c3_found": (3, "何十年も続きます"),
    # 4 あなたの県
    "c4_q": (4, "四つ目の問いです"), "c4_this": (4, "地図の上で探します"), "c4_map": (4, "地図に色で塗りました"),
    "c4_mae": (4, "群馬と高知でした"), "c4_71": (4, "中央値は71回です"), "c4_mbest": (4, "群馬のいちばん多かった人は"), "c4_all80": (4, "元日のすべてで"),
    "c4_tok": (4, "東京は、中央値で67回"), "c4_mid": (4, "47都道府県の中央値は、44回"), "c4_mark": (4, "44回より多ければ"),
    "c4_sap": (4, "北海道は、中央値で22回"), "c4_aki": (4, "秋田は、中央値で4回"),
    "c4_cmp": (4, "いちばん多い県と"), "c4_x18": (4, "約18倍"), "c4_tbl": (4, "画面の表にあります"), "c4_p1": (4, "一枚目は"), "c4_p2": (4, "二枚目は"), "c4_p3": (4, "三枚目は"), "c4_near": (4, "記録は県庁所在地の1か所"),
    "c4_found": (4, "何倍もちがいます"),
    # 5 まとめ
    "c5_sum": (5, "中央値4回から71回"), "c5_long": (5, "何十年も続き"), "c5_you": (5, "あなたの県は、何回でしたか"),
    "c5_ch": (5, "このチャンネルでは"), "c5_sub": (5, "チャンネル登録してもらえると"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の並び（名前, 始まり, 描く関数の名前）。始まり: 合図のキー＝その文の頭の前 ／ "ch:N"＝章カードのあと ／ "z:キー"＝0章 ／ "gap:" ＝無音の途中 ----
SC_TABLE = [
    ("open", "zero", "sc_open"), ("c0_card", "z:c0_dou", "sc_c0_card"), ("c0_cond", "z:c0_cond", "sc_c0_cond"), ("c0_map", "z:c0_stn", "sc_c0_map"), ("c0_day", "z:c0_day", "sc_c0_day"),
    ("c0_life", "z:c0_life", "sc_c0_life"),
    ("c1_a", "ch:1", "sc_c1_a"), ("c1_t36", "c1_t36", "sc_c1_t36"), ("c1_luck", "c1_luck", "sc_c1_luck"), ("c1_tenk", "c1_tenk", "sc_c1_tenk"),
    ("c1_lot", "c1_box", "sc_c1_lot"), ("c1_graph", "c1_graph", "sc_c1_graph"), ("c1_hist", "c1_med", "sc_c1_hist"), ("c1_ans", "c1_ans", "sc_c1_ans"),
    ("c1_8", "c1_8", "sc_c1_8"), ("c1_most", "c1_most", "sc_c1_most"), ("c1_count", "c1_count", "sc_c1_count"), ("c1_sun", "c1_sr", "sc_c1_sun"),
    ("c1_chg", "c1_chg", "sc_c1_chg"),
    ("c2_a", "ch:2", "sc_c2_a"), ("c2_map", "c2_cand", "sc_c2_map"), ("c2_three", "c2_three", "sc_c2_three"), ("c2_ans", "c2_ans", "sc_c2_ans"),
    ("c2_years", "c2_years", "sc_c2_years"), ("c2_ak", "c2_akmed", "sc_c2_ak"), ("c2_win", "c2_imag", "sc_c2_win"),
    ("c2_diag", "c2_why", "sc_c2_diag"), ("c2_cant", "c2_cant", "sc_c2_cant"),
    ("c3_a", "ch:3", "sc_c3_a"), ("c3_lot", "c3_lost", "sc_c3_lot"), ("c3_count", "c3_count", "sc_c3_count"), ("c3_ans", "c3_ans", "sc_c3_ans"),
    ("c3_age", "c3_age", "sc_c3_age"), ("c3_20a", "c3_20", "sc_c3_20a"), ("c3_20b", "c3_9370", "sc_c3_20b"), ("c3_hit", "c3_hit", "sc_c3_hit"),
    ("c3_corr", "c3_chk", "sc_c3_corr"), ("c3_new", "c3_new", "sc_c3_new"),
    ("c4_a", "ch:4", "sc_c4_a"), ("c4_map", "c4_map", "sc_c4_map"), ("c4_mae", "c4_mae", "sc_c4_mae"), ("c4_best", "c4_mbest", "sc_c4_best"),
    ("c4_city", "c4_tok", "sc_c4_city"), ("c4_city2", "c4_sap", "sc_c4_city2"), ("c4_cmp", "c4_cmp", "sc_c4_cmp"), ("c4_tbl", "c4_tbl", "sc_c4_tbl"),
    ("c4_tbl2", "c4_p2", "sc_c4_tbl2"), ("c4_tbl3", "c4_p3", "sc_c4_tbl3"), ("c4_near", "c4_near", "sc_c4_near"),
    ("c5_map", "ch:5", "sc_c5_map"), ("c5_win", "c5_long", "sc_c5_win"), ("c5_close", "c5_ch", "sc_c5_close"), ("end", "end", "sc_end"),
]


# ---- 場面の切りかえの間: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c0_life": 2.4}


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


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


REST = [g_ for g_ in GAP_NOTE if "区切り" in GAP_NOTE[g_]]
T_RS0 = S(REST[0]) if len(REST) == 1 else 0.0
T_RS1 = E(REST[0]) if len(REST) == 1 else 0.0
LAST_KEY = "c5_sub"
T_ES = Ek(LAST_KEY) + 0.5


# ============================================================
# データ（research/hatsuhinode/an6.py と同じ計算。乱数の種 20261111。手で書き写さない）
# ============================================================
import statistics as _st  # noqa: E402
from collections import Counter as _Counter  # noqa: E402

# 県・気象台・緯度経度は an7.py の P（47都道府県。県庁所在地の気象台。埼玉=熊谷・滋賀=彦根）。並び順＝japan_outline.json の JP-01〜JP-47
P = [('北海道', 'sapporo', '札幌', 43.06, 141.33), ('青森', 'aomori', '青森', 40.82, 140.77), ('岩手', 'morioka', '盛岡', 39.70, 141.17), ('宮城', 'sendai', '仙台', 38.26, 140.90),
     ('秋田', 'akita', '秋田', 39.72, 140.10), ('山形', 'yamagata', '山形', 38.26, 140.35), ('福島', 'fukushima', '福島', 37.76, 140.47), ('茨城', 'mito', '水戸', 36.38, 140.47),
     ('栃木', 'utsunomiya', '宇都宮', 36.55, 139.87), ('群馬', 'maebashi', '前橋', 36.41, 139.06), ('埼玉', 'kumagaya', '熊谷', 36.15, 139.38), ('千葉', 'chiba', '千葉', 35.60, 140.10),
     ('東京', 'tokyo', '東京', 35.69, 139.75), ('神奈川', 'yokohama', '横浜', 35.44, 139.65), ('新潟', 'niigata', '新潟', 37.89, 139.02), ('富山', 'toyama', '富山', 36.71, 137.20),
     ('石川', 'kanazawa', '金沢', 36.59, 136.63), ('福井', 'fukui', '福井', 36.06, 136.22), ('山梨', 'kofu', '甲府', 35.67, 138.55), ('長野', 'nagano', '長野', 36.66, 138.19),
     ('岐阜', 'gifu', '岐阜', 35.40, 136.76), ('静岡', 'shizuoka', '静岡', 34.98, 138.40), ('愛知', 'nagoya', '名古屋', 35.17, 136.97), ('三重', 'tsu', '津', 34.73, 136.52),
     ('滋賀', 'hikone', '彦根', 35.28, 136.24), ('京都', 'kyoto', '京都', 35.01, 135.73), ('大阪', 'osaka', '大阪', 34.68, 135.52), ('兵庫', 'kobe', '神戸', 34.70, 135.21),
     ('奈良', 'nara', '奈良', 34.69, 135.83), ('和歌山', 'wakayama', '和歌山', 34.23, 135.16), ('鳥取', 'tottori', '鳥取', 35.49, 134.24), ('島根', 'matsue', '松江', 35.46, 133.07),
     ('岡山', 'okayama', '岡山', 34.66, 133.92), ('広島', 'hiroshima', '広島', 34.40, 132.46), ('山口', 'yamaguchi', '山口', 34.16, 131.46), ('徳島', 'tokushima', '徳島', 34.07, 134.57),
     ('香川', 'takamatsu', '高松', 34.32, 134.05), ('愛媛', 'matsuyama', '松山', 33.84, 132.78), ('高知', 'kochi', '高知', 33.57, 133.55), ('福岡', 'fukuoka', '福岡', 33.58, 130.38),
     ('佐賀', 'saga', '佐賀', 33.27, 130.31), ('長崎', 'nagasaki', '長崎', 32.73, 129.87), ('熊本', 'kumamoto', '熊本', 32.81, 130.71), ('大分', 'oita', '大分', 33.24, 131.62),
     ('宮崎', 'miyazaki', '宮崎', 31.94, 131.41), ('鹿児島', 'kagoshima', '鹿児島', 31.55, 130.55), ('沖縄', 'naha', '那覇', 26.21, 127.69)]
assert len(P) == 47
ISO = {p_[0]: f"JP-{i + 1:02d}" for i, p_ in enumerate(P)}
N_PEOPLE, N_LIFE = 10000, 80
SEED = 20261111


def _simulate():
    H = json.load(open(RES / "H7.json", encoding="utf-8"))
    st = (RES / "H7.json").stat()
    cache = OUT / "sim_cache7.pkl"
    key = (st.st_mtime_ns, st.st_size, SEED, N_PEOPLE, N_LIFE)
    if cache.exists():
        try:
            k_, res_ = pickle.loads(cache.read_bytes())
            if k_ == key:
                return res_
        except Exception:
            pass
    random.seed(SEED)
    res = {}
    for pref, _k, _st_, _la, _lo in P:                          # an7.py と同じ並び・同じ乱数の使い方
        yrs = sorted(H[pref])
        s = [H[pref][y] for y in yrs]
        cnt, stk = [], []
        for _ in range(N_PEOPLE):
            l = [random.choice(s) for _ in range(N_LIFE)]
            cnt.append(sum(l))
            m = k = 0
            for x in l:
                k = 0 if x else k + 1
                m = max(m, k)
            stk.append(m)
        cnt.sort()
        stk.sort()
        res[pref] = dict(years=[int(y) for y in yrs], s=s, cnt=cnt, stk=stk)
    OUT.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps((key, res)))
    return res


SIM = _simulate()


def _q(a, p):
    return a[int(p * (len(a) - 1))]


def _lag1(s):
    m = sum(s) / len(s)
    n = sum((a - m) * (b - m) for a, b in zip(s, s[1:]))
    d = sum((a - m) ** 2 for a in s)
    return n / d if d else 0.0


TOWN = {}                      # 県の名前 → 数字（名前の「TOWN」は旧版のまま。中身は47都道府県）
for _pref, _k, _stn, _la, _lo in P:
    _r = SIM[_pref]
    TOWN[_pref] = dict(station=_stn, years=_r["years"], s=_r["s"], seen=sum(_r["s"]), n=len(_r["s"]), med=_q(_r["cnt"], 0.5), worst=_r["cnt"][0],
                       best=_r["cnt"][-1], stk_med=_q(_r["stk"], 0.5), s20=sum(x >= 20 for x in _r["stk"]), zero=sum(x == 0 for x in _r["cnt"]),
                       hist=_Counter(_r["cnt"]), lag=_lag1(_r["s"]), lat=_la, lon=_lo)


def _load_numbers_md():
    """out/hatsuhinode-long/numbers.md の表（県ごとの数字）を読む"""
    rows = {}
    for ln in (OUT / "numbers.md").read_text(encoding="utf-8").splitlines():
        if "|" not in ln:
            continue
        p0, p1, p2, p3 = (x.split() for x in ln.split("|")[:4]) if ln.count("|") >= 3 else (None,) * 4
        if not p0 or p0[0] not in TOWN or len(p0) < 6:
            continue
        rows[p0[0]] = dict(sunrise=p0[2], seen=int(p0[3].split("/")[0]), n=int(p0[3].split("/")[1]), med=int(p1[0]), worst=int(p1[1]), best=int(p1[2]),
                           stk_med=int(p2[0]), zero=int(p3[0].replace(",", "")), s20=int(p3[1].replace(",", "")))
    return rows


_NM = _load_numbers_md()
assert len(_NM) == 47, f"numbers.md の表に 47 県が見つからない: {len(_NM)}"
for _n, _r in _NM.items():
    for _k in ("seen", "n", "med", "worst", "best", "stk_med", "s20", "zero"):
        assert TOWN[_n][_k] == _r[_k], f"numbers.md と計算が食い違う: {_n} {_k} 表 {_r[_k]} ／ 計算 {TOWN[_n][_k]}"
assert TOWN["大分"]["n"] == 35
AKITA_YEARS = [y for y, v in zip(TOWN["秋田"]["years"], TOWN["秋田"]["s"]) if v]
assert AKITA_YEARS == [2011, 2017]
T_TOK, T_AKI, T_MAE, T_KOC = TOWN["東京"], TOWN["秋田"], TOWN["群馬"], TOWN["高知"]      # T_MAE = 群馬
MED_MAX = max(t["med"] for t in TOWN.values())
MED_MIN = min(t["med"] for t in TOWN.values())
assert MED_MAX == T_MAE["med"] == T_KOC["med"] and MED_MIN == T_AKI["med"]
RATIO18 = ihalf(MED_MAX / MED_MIN)
_meds = sorted(t["med"] for t in TOWN.values())
MID47 = _meds[23]                                                    # 47県の中央値の中央値
MID47_PREFS = [n for n, t in TOWN.items() if t["med"] == MID47]
assert MID47 == 44 and sorted(MID47_PREFS) == sorted(["佐賀", "山口", "鹿児島"])


def example_life(town, target_streak, seed=20261112):
    """80回の元日の1人ぶんの例（見えた=1/見えない=0）。見られない年が続く最長が target_streak になる人を、別の乱数で探す"""
    s = TOWN[town]["s"]
    rnd = random.Random(seed)
    for _ in range(200000):
        l = [rnd.choice(s) for _ in range(N_LIFE)]
        m = k = 0
        for x in l:
            k = 0 if x else k + 1
            m = max(m, k)
        if m == target_streak:
            return l
    raise SystemExit("例の一生が見つからない")


def longest_run(l):
    """見えない年が続く最長の (長さ, 始まりの位置)"""
    best, bs, k, st_ = 0, 0, 0, 0
    for i, x in enumerate(l):
        if x:
            k = 0
        else:
            if k == 0:
                st_ = i
            k += 1
            if k > best:
                best, bs = k, st_
    return best, bs


LIFE_TOK = example_life("東京", T_TOK["stk_med"])
LIFE_AKI = example_life("秋田", T_AKI["stk_med"])

# ============================================================
# 見た目（共通の道具: tsubame-long.py と同じ札・線・場面の仕組み）
# ============================================================
W_, H_ = lf.W, lf.H
WHITE, YEL, PALE, REDC = "#ffffff", "#ffe14a", "#d6e2f5", "#e8505b"
PANEL = "#16204a"
BASE_BG = "#1d2650"


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
    _rec(ctx, "panel", rows[0][0], x0, y0, x0 + w, y0 + h, a=a)
    return (x0, y0, x0 + w, y0 + h)


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


# ============================================================
# 場面の仕組み（tsubame-long.py と同じ）: 前の場面が消えてから次が出る
# ============================================================
SCENES = []
SC_IN, SC_OUT, SC_DELAY = 0.25, 0.2, 0.2
SC_START = {}
SC_END = {}


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


# ---------- 札の出し入れ ----------
def pw(rows, pad=(28, 16), gap=1.22):
    ws = [text_width(s_, sz) for s_, sz, _c in rows]
    hs = [sz * gap for _s, sz, _c in rows]
    return max(ws) + 2 * pad[0], sum(hs) + 2 * pad[1] - rows[-1][1] * (gap - 1.0)


def R(*ss, sz=46, col=WHITE):
    return [(s_, sz, col) for s_ in ss]


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


def vrows(head, val, unit, hs=46, vs=90):
    """数の札: 見出し・数（黄色）・分母（小さく）"""
    rows = [(head, hs, WHITE), (val, vs, YEL)]
    if unit:
        rows.append((unit, 40, WHITE))
    return rows


def arows(n, *body):
    """答えの札: 「問いNの答え」＋本文"""
    return [(f"問い{n}の答え", 44, YEL)] + list(body)


# ---- 章カード（平たい板・問いの番号は黄色）----
CARD_BY_N = {1: ["問い1", "東京に住むあなたは、何回？"], 2: ["問い2", "36年で2回しか見えなかった県は？"], 3: ["問い3", "見られない年は、何年続く？"],
             4: ["問い4", "あなたの県は？"], 5: ["まとめ"]}
CARD_LINES = {s_ for v in CARD_BY_N.values() for s_ in v}
CARD_HOLD = {n: max(3.0, len("".join(v)) / 8 + 1 + 0.4) for n, v in CARD_BY_N.items()}
T_TITLE = {n: CARD_HOLD[n] + 0.2 for n in CARD_BY_N}


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        n = CHAPS[ch[0]]["n"]
        age = t - ch[1]
        hold = CARD_HOLD.get(n, 3.0)
        if 0 <= age <= hold:
            a = clamp01(age / 0.35) * clamp01((hold - age) / 0.4)
            rows = CARD_BY_N[n]
            rr = [(s_, 76, YEL if (s_.startswith("問い") or s_ in ("まとめ",)) else WHITE) for s_ in rows]
            sc = 0.92 + 0.08 * ease_out(clamp01(age / 0.35))      # 入りだけ大きくなる（消えるときは縮めない）
            ctx.save()
            ctx.translate(960, 440)
            ctx.scale(sc, sc)
            panel(ctx, rr, 0, 0, a=a, pad=(60, 34), border=YEL)
            ctx.restore()


def ch_start(n):
    return S(f"ch{n}")


# ============================================================
# 絵の道具（冬の朝: 空は夜明けの紺→桃色→うす水色。カードは無地の明るいカード）
# ============================================================
from PIL import Image  # noqa: E402

SUB_Y = 936           # 字幕の帯の上端（札・図の文字はこの下に置かない）
CARDC = "#f4ece4"     # グラフ・帯・地図・表を載せる無地のカード（背景の絵に直接のせない）
DARKTXT = "#2a2238"
UNITC = "#5a4a66"
GOLD = "#f3b72e"
AKANE = "#e0704f"
BLUEC = "#3a6fb0"
GREENC = "#3f9a6a"
GRIDC = "#c3cde3"
EDGEC = "#6f7ea3"


def tset(ctx, col, a=1.0):
    r, g, b, _a = hexrgb(col)
    ctx.set_source_rgba(r, g, b, a)


def lcol(c0, c1, u):
    a, b = hexrgb(c0), hexrgb(c1)
    u = clamp01(u)
    return "#%02x%02x%02x" % tuple(int(round((a[i] + (b[i] - a[i]) * u) * 255)) for i in range(3))


def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col, al in stops:
        r, gg, b, _a = hexrgb(col)
        g.add_color_stop_rgba(off, r, gg, b, al)
    return g


def rect(ctx, col, x0, y0, x1, y1, a=1.0):
    tset(ctx, col, a)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.fill()


def disc(ctx, x, y, r, col, a=1.0):
    tset(ctx, col, a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def whiten(ctx, a, col="#ffffff"):
    if a > 0.003:
        rect(ctx, col, 0, 0, W_, H_, a)


def tx(ctx, s, x, y, size, col=DARKTXT, align="center", a=1.0):
    """カードの上に直に置く文字（core.text のログに残る）"""
    if a > 0.003:
        text(ctx, s, x, y, size, col, align=align, alpha=a)


def unit_tag(ctx, s, x, y, a=1.0, align="center"):
    tx(ctx, s, x, y, 40, UNITC, align=align, a=a)


def chart_card(ctx, x0, y0, x1, y1, col=None, a=1.0):
    tset(ctx, col or CARDC, a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
    ctx.fill()


def snowfall(ctx, t, a=0.55, n=110, seed=8):
    """ゆっくり降る雪（カードの外の夜明けの空に）。10秒に1回は画面が動くように"""
    rnd = random.Random(seed)
    for i in range(n):
        x0, y0 = rnd.uniform(0, W_), rnd.uniform(0, H_ + 40)
        sp = rnd.uniform(35, 80)
        r = rnd.uniform(3.0, 7.0)
        x = (x0 + 14 * t + 22 * math.sin(t * 0.6 + i)) % W_
        y = (y0 + sp * t) % (H_ + 40) - 20
        disc(ctx, x, y, r, "#ffffff", a * rnd.uniform(0.45, 1.0))


def chart_bg(ctx, t):
    """グラフ・表・地図の場面の後ろ: 夜明けの空（紺→紫→あかね）と、ゆっくり降る雪（カードの外だけに見える）"""
    ctx.set_source(lin(0, 0, 0, H_, [(0, "#1a2250", 1), (0.55, "#4a3770", 1), (1, "#c8635c", 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    snowfall(ctx, t)


def card_scene(ctx, t, y0=40, y1=900, x0=110, x1=1810):
    chart_bg(ctx, t)
    chart_card(ctx, x0, y0, x1, y1)


def glow_box(ctx, t, x0, y0, x1, y1, a, col=GOLD, r=24):
    if a > 0.003:
        tset(ctx, col, a * (0.6 + 0.4 * math.sin(t * 5)))
        ctx.set_line_width(9)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, r)
        ctx.stroke()


def ring(ctx, x, y, r, col=REDC, a=1.0, w=9):
    _rec_circle(ctx, "赤丸", x, y, r + w / 2, a)
    if a > 0.003:
        tset(ctx, col, a)
        ctx.set_line_width(w)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.stroke()


def ring_box(ctx, x0, y0, x1, y1, col=REDC, a=1.0, w=9):
    if a > 0.003:
        tset(ctx, col, a)
        ctx.set_line_width(w)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, (y1 - y0) / 2)
        ctx.stroke()


def sun_mark(ctx, x, y, r, a=1.0):
    """日の印: 金色の丸と短い光の筋"""
    tset(ctx, "#f0a020", a)
    ctx.set_line_width(max(2.0, r * 0.22))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(8):
        an = k * math.pi / 4
        ctx.move_to(x + math.cos(an) * r * 1.25, y + math.sin(an) * r * 1.25)
        ctx.line_to(x + math.cos(an) * r * 1.7, y + math.sin(an) * r * 1.7)
    ctx.stroke()
    disc(ctx, x, y, r, "#ffcf3a", a)


def cross_mark(ctx, x, y, r, a=1.0, col="#b04a4a"):
    tset(ctx, col, a)
    ctx.set_line_width(max(2.5, r * 0.3))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x - r, y - r)
    ctx.line_to(x + r, y + r)
    ctx.move_to(x + r, y - r)
    ctx.line_to(x - r, y + r)
    ctx.stroke()


# ---- 人（紺のコート・赤いマフラー）: この画像だけで描く。小さく並べるときも同じ画像を縮小 ----
_PERSON_IM = Image.open(ROOT / "sims" / "hatsuhinode_sprites" / "person_blue.png").convert("RGBA")
_PBUF = {}


def _psurf(h):
    h = max(8, int(round(h)))
    if h not in _PBUF:
        w = max(4, int(round(_PERSON_IM.width * h / _PERSON_IM.height)))
        arr = np.array(_PERSON_IM.resize((w, h), Image.LANCZOS)).astype(np.float32)
        a_ = arr[..., 3:4] / 255.0
        bgra = np.empty((h, w, 4), np.uint8)
        bgra[..., 0] = np.round(arr[..., 2] * a_[..., 0])
        bgra[..., 1] = np.round(arr[..., 1] * a_[..., 0])
        bgra[..., 2] = np.round(arr[..., 0] * a_[..., 0])
        bgra[..., 3] = np.round(arr[..., 3])
        buf = bytearray(bgra.tobytes())
        _PBUF[h] = (cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, w * 4), buf, w, h)
    return _PBUF[h]


def person(ctx, x, y, h, a=1.0):
    """人。足もと中央が (x, y)、背の高さ h。a は不透明度"""
    if a <= 0.003:
        return
    surf, _b, w, hh = _psurf(h)
    _rec(ctx, "person", "人型", x - w / 2, y - hh, x + w / 2, y, a=a)
    ctx.save()
    ctx.set_source_surface(surf, x - w / 2, y - hh)
    ctx.paint_with_alpha(a)
    ctx.restore()


def person_w(h):
    return _PERSON_IM.width * h / _PERSON_IM.height


# ---- 一人称の窓（人の体は描かない。見えている景色だけ）----
_SKY = {   # (上, 中, 地平線)   u=0 → u=1
    "dark": (("#0d1330", "#141c44"), ("#2b2a5a", "#4a3d78"), ("#7a3f66", "#d0765e")),
    "clear": (("#1f2f6b", "#6a9bd8"), ("#c2688a", "#f0b3a8"), ("#f6a45f", "#fde0b0")),
    "cloud": (("#5d6573", "#5d6573"), ("#8b909b", "#8b909b"), ("#b4b3b6", "#b4b3b6")),
    "snow": (("#555d6d", "#555d6d"), ("#7a8292", "#7a8292"), ("#a0a5ae", "#a0a5ae")),
}


def _cloud(ctx, cx, cy, s, col, a=1.0):
    for dx, dy, r in ((-90, 10, 60), (0, -22, 82), (95, 8, 62), (10, 28, 72), (-40, 24, 60), (60, 30, 56)):
        disc(ctx, cx + dx * s, cy + dy * s, r * s, col, a)


def window(ctx, t, box, kind="clear", u=0.0, fw=46, curtain=True, seed=1, snow=None):
    """窓。box=(x0, y0, x1, y1)（枠の外側）。kind: dark（夜明け前）／clear（晴れ。u 0→1 で日が昇る）／cloud（曇り）／snow（雪）。"""
    x0, y0, x1, y1 = box
    ix0, iy0, ix1, iy1 = x0 + fw, y0 + fw, x1 - fw, y1 - fw * 1.6
    w, h = ix1 - ix0, iy1 - iy0
    hor = iy0 + h * 0.70
    u = clamp01(u)
    c_top, c_mid, c_hor = [lcol(p[0], p[1], u) for p in _SKY[kind]]
    _rec(ctx, "window", "窓", x0 - 14, y0, x1 + 14, y1, inner=None)
    if PARTS is not None:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((ix0, iy0), (ix1, iy1))))
        PARTS[-1]["inner"] = (min(xs), min(ys), max(xs), max(ys))
    ctx.save()
    ctx.rectangle(ix0, iy0, w, h)
    ctx.clip()
    ctx.set_source(lin(0, iy0, 0, hor, [(0, c_top, 1), (0.55, c_mid, 1), (1, c_hor, 1)]))
    ctx.rectangle(ix0, iy0, w, h)
    ctx.fill()
    rs = h * 0.085
    sx = ix0 + w * 0.62
    if kind in ("dark", "clear"):
        gl = cairo.RadialGradient(sx, hor, 0, sx, hor, w * (0.25 + 0.2 * u))
        r_, g_, b_, _a = hexrgb("#ffb070")
        gl.add_color_stop_rgba(0, r_, g_, b_, 0.25 + 0.55 * u if kind == "clear" else 0.18 + 0.3 * u)
        gl.add_color_stop_rgba(1, r_, g_, b_, 0.0)
        ctx.set_source(gl)
        ctx.rectangle(ix0, iy0, w, h)
        ctx.fill()
    if kind == "clear":
        sy = hor + rs * 0.9 - u * rs * 3.4
        disc(ctx, sx, sy, rs * 1.25, "#fff2b8", 0.45)
        disc(ctx, sx, sy, rs, "#fff8dc")
        if sy - rs * 1.25 < hor - 20:
            _rec_circle(ctx, "太陽", sx, sy, rs * 1.25, kind="sun")
    if kind in ("cloud", "snow"):
        rnd = random.Random(seed)
        cs = min(1.0, max(0.3, w / 900.0))
        for i in range(7 if cs >= 1.0 else 3):
            cx = ix0 + ((rnd.uniform(0, w) + 14 * t) % (w + 400 * cs)) - 200 * cs
            _cloud(ctx, cx, iy0 + h * rnd.uniform(0.08, 0.5), rnd.uniform(1.1, 1.9) * cs, "#c7c9cf" if kind == "cloud" else "#aeb3bd", 0.9)
    if kind == "dark":
        rnd = random.Random(seed + 5)
        for i in range(26):
            disc(ctx, ix0 + rnd.uniform(0, w), iy0 + rnd.uniform(0, h * 0.5), rnd.uniform(1.5, 3.0), "#ffffff", (0.5 + 0.5 * math.sin(t * 1.3 + i)) * (1 - u) * 0.9)
    # 町の屋根のシルエット（遠景）。雪の朝は少し明るい灰紫に白い雪の線
    rnd = random.Random(seed + 11)
    roofc = "#4d4466" if kind == "snow" else "#2a2238"
    sc_ = min(1.0, max(0.5, w / 1800.0))
    hm = (0.8, 1.0, 1.3)[seed % 3]
    tset(ctx, roofc)
    ctx.rectangle(ix0, hor + 6, w, iy1 - hor)
    ctx.fill()
    x = ix0 - 20
    while x < ix1 + 20:
        bw = rnd.uniform(70, 150) * sc_
        bh = rnd.uniform(18, 70) * hm
        pk = rnd.uniform(14, 34) * sc_ * 1.4 if rnd.random() < 0.8 else 0.0
        tset(ctx, roofc)
        ctx.move_to(x, hor + 8)
        ctx.line_to(x, hor - bh)
        if pk:
            ctx.line_to(x + bw / 2, hor - bh - pk)
        ctx.line_to(x + bw, hor - bh)
        ctx.line_to(x + bw, hor + 8)
        ctx.close_path()
        ctx.fill()
        if kind == "snow":
            tset(ctx, "#ffffff", 0.95)
            ctx.set_line_width(7)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            if pk:
                ctx.move_to(x - 2, hor - bh)
                ctx.line_to(x + bw / 2, hor - bh - pk)
                ctx.line_to(x + bw + 2, hor - bh)
            else:
                ctx.move_to(x - 2, hor - bh)
                ctx.line_to(x + bw + 2, hor - bh)
            ctx.stroke()
        x += bw * rnd.uniform(0.75, 1.0)
    if kind in ("snow", "cloud") or snow:
        sn = snow if snow is not None else (1.0 if kind == "snow" else 0.0)
        if sn > 0:
            rnd = random.Random(seed + 3)
            for i in range(int(160 * sn)):
                x_, y_ = rnd.uniform(0, w), rnd.uniform(0, h)
                sp = rnd.uniform(60, 130)
                px = ix0 + (x_ + 18 * t + 20 * math.sin(t * 0.8 + i)) % w
                py = iy0 + (y_ + sp * t) % h
                disc(ctx, px, py, rnd.uniform(3.5, 8), "#ffffff", rnd.uniform(0.55, 1.0))
    ctx.restore()
    # 窓枠（木）
    tset(ctx, "#6b4a2f")
    ctx.rectangle(x0, y0, x1 - x0, fw)
    ctx.rectangle(x0, y0, fw, y1 - y0)
    ctx.rectangle(x1 - fw, y0, fw, y1 - y0)
    ctx.rectangle(x0 - fw * 0.3, y1 - fw * 1.6, x1 - x0 + fw * 0.6, fw * 1.6)
    ctx.fill()
    tset(ctx, "#8a6340")
    ctx.set_line_width(4)
    ctx.rectangle(ix0 - 2, iy0 - 2, w + 4, h + 4)
    ctx.stroke()
    if curtain and w > 900:
        cw = 150
        dk = 0.5 * (1 - u) if kind == "dark" else 0.0
        ctx.set_source(lin(ix0, 0, ix0 + cw, 0, [(0, lcol("#d9c3a3", "#10142c", dk), 1), (0.5, lcol("#ecdcc2", "#10142c", dk), 1), (1, lcol("#cdb594", "#10142c", dk), 1)]))
        ctx.move_to(ix0, iy0)
        for k in range(0, 9):
            ctx.line_to(ix0 + cw + 16 * math.sin(k * 1.4 + 0.3), iy0 + h * k / 8)
        ctx.line_to(ix0, iy1)
        ctx.close_path()
        ctx.fill()
        tset(ctx, "#b79b78", 0.5)
        ctx.set_line_width(5)
        for k in range(1, 4):
            ctx.move_to(ix0 + cw * k / 4, iy0)
            ctx.line_to(ix0 + cw * k / 4 + 10 * math.sin(k), iy1)
        ctx.stroke()


def dim(ctx, box, a):
    if a > 0.003:
        rect(ctx, "#10142c", box[0], box[1], box[2], box[3], a)


# ---- 枠の列（1つの枠＝1回の元日）----
def slot_xy(x0, y, i, pitch, per_row=None, row_pitch=0.0):
    if per_row is None:
        return x0 + pitch * i + pitch / 2, y
    return x0 + pitch * (i % per_row) + pitch / 2, y + row_pitch * (i // per_row)


def slots(ctx, t, x0, y, n, pitch, size, state, t_fill=None, dt=0.0, a=1.0, cross=False, hl=None, per_row=None, row_pitch=0.0, times=None):
    """n 個の枠を並べる。state[i]=1 なら日の印、0 なら空（cross=True なら×）。t_fill が None なら最初から埋まっている。
    t_fill があれば i 番目は t_fill + dt*i（times があればその i 番目の時刻）から埋まる。hl は {i: 色} の枠の強調。per_row で折り返す"""
    for i in range(n):
        cx, cy = slot_xy(x0, y, i, pitch, per_row, row_pitch)
        tset(ctx, GRIDC, a)
        rrect(ctx, cx - size / 2, cy - size / 2, size, size, size * 0.2)
        ctx.fill()
        tset(ctx, EDGEC, a)
        ctx.set_line_width(2)
        rrect(ctx, cx - size / 2, cy - size / 2, size, size, size * 0.2)
        ctx.stroke()
        tf = times[i] if times is not None else (None if t_fill is None else t_fill + dt * i)
        if tf is not None and t < tf:
            continue
        e = 1.0 if tf is None else ease_out(clamp01((t - tf) / 0.25))
        if state[i]:
            tset(ctx, "#fff1c4", a * e)
            rrect(ctx, cx - size / 2, cy - size / 2, size, size, size * 0.2)
            ctx.fill()
            sun_mark(ctx, cx, cy, size * 0.26, a * e)
        elif cross:
            cross_mark(ctx, cx, cy, size * 0.24, a * e)
        if hl and i in hl:
            tset(ctx, hl[i], a)
            ctx.set_line_width(5)
            rrect(ctx, cx - size / 2 - 3, cy - size / 2 - 3, size + 6, size + 6, size * 0.25)
            ctx.stroke()


def run_bar(ctx, x0, y, pitch, i0, ln, size, col="#b04a4a", a=1.0, w=9, prog=1.0, per_row=None, row_pitch=0.0):
    """見られない年が続く区間の太い線（枠の下）。折り返す列では行ごとに引く"""
    if a <= 0.003 or ln <= 0:
        return
    tset(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    n_show = ln * prog
    i = i0
    while i < i0 + n_show - 1e-6:
        row_end = i0 + ln if per_row is None else min(i0 + ln, (i // per_row + 1) * per_row)
        j = min(row_end, i0 + n_show)
        xa, ya = slot_xy(x0, y, i, pitch, per_row, row_pitch)
        xb, _yb = slot_xy(x0, y, j - 1, pitch, per_row, row_pitch)
        ctx.move_to(xa - pitch * 0.4, ya + size * 0.78)
        ctx.line_to(xb + pitch * 0.4 + (j - n_show - 0 if False else 0), ya + size * 0.78)
        ctx.stroke()
        i = row_end


# ---- ヒストグラム（見えた回数の分布。1万人）----
def hist_plot(ctx, t, plot, hist, t0, col=AKANE, grow=1.2, vmax=None, xmax=N_LIFE, ticks=True, a=1.0):
    """plot=(x0, ytop, x1, ybase)。横が見えた回数 0〜xmax・縦が人の数（目盛りの数字なし）。t0 から棒が伸びる（t0=None なら枠だけ）"""
    x0, yt, x1, yb = plot
    bw = (x1 - x0) / (xmax + 1)
    tset(ctx, "#8a8499", a)
    ctx.set_line_width(4)
    ctx.move_to(x0 - 10, yb + 2)
    ctx.line_to(x1 + 10, yb + 2)
    ctx.stroke()
    if ticks:
        for k in range(0, xmax + 1, 20):
            cx = x0 + (k + 0.5) * bw
            tx(ctx, str(k), cx, yb + 40, 40, DARKTXT, a=a)
            tset(ctx, "#8a8499", a)
            ctx.move_to(cx, yb + 2)
            ctx.line_to(cx, yb + 12)
            ctx.stroke()
    if t0 is None or not hist:
        return
    vm = vmax or max(hist.values())
    e = ease_out(clamp01((t - t0) / grow))
    for k, v in hist.items():
        hh = max(5.0, (yb - yt) * v / vm) * e
        _rec(ctx, "bar", "グラフの棒", x0 + k * bw + 1, yb - hh, x0 + k * bw + max(2.0, bw - 2) + 1, yb, a=a)
        tset(ctx, col, a)
        ctx.rectangle(x0 + k * bw + 1, yb - hh, max(2.0, bw - 2), hh)
        ctx.fill()


def hist_x(plot, k, xmax=N_LIFE):
    x0, _yt, x1, _yb = plot
    return x0 + (k + 0.5) * (x1 - x0) / (xmax + 1)


def vline(ctx, x, y0, y1, col, a=1.0, w=7):
    if a > 0.003:
        tset(ctx, col, a)
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, y0)
        ctx.line_to(x, y1)
        ctx.stroke()


PARTS = None          # 点検中だけ list。絵の部品（人型・太陽・窓・地図の印・くじの箱・グラフの棒・札）を描くたびに記録する（device 座標）


def _rec(ctx, kind, label, x0, y0, x1, y1, a=1.0, **extra):
    if PARTS is None or a <= 0.1:
        return
    xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))))
    PARTS.append(dict(kind=kind, label=label, rect=(min(xs), min(ys), max(xs), max(ys)), **extra))


def _rec_circle(ctx, label, x, y, r, a=1.0, kind="circle"):
    if PARTS is None or a <= 0.1:
        return
    cx, cy = ctx.user_to_device(x, y)
    PARTS.append(dict(kind=kind, label=label, circle=(cx, cy, abs(ctx.user_to_device_distance(r, 0)[0]))))


# ---- 地図（Natural Earth の実データ・47都道府県の輪郭）----
JP = json.load(open(OUT / "src" / "japan_outline.json", encoding="utf-8"))
_MAIN_BOX = (128.6, 146.0, 30.8, 45.6)       # lon0, lon1, lat0, lat1
_INSET_BOX = (126.6, 128.4, 25.9, 27.0)
_MAP_CACHE = {}


class JMap:
    """box=(x0, y0, x1, y1) に日本地図（47都道府県の県境）を置く（本州などは右・沖縄は左下の枠）。幅は 1040 以上ほしい。xy(県) で県庁所在地の気象台の画面の位置"""
    INSET_W, INSET_H = 230, 150

    def __init__(self, box):
        self.box = box
        x0, y0, x1, y1 = box
        mx0 = x0 + self.INSET_W + 20
        lo0, lo1, la0, la1 = _MAIN_BOX
        cs = math.cos(math.radians(37))
        self.k = min((x1 - mx0) / ((lo1 - lo0) * cs), (y1 - y0) / (la1 - la0))
        self.mx0 = mx0 + ((x1 - mx0) - (lo1 - lo0) * cs * self.k) / 2
        self.my1 = y1 - ((y1 - y0) - (la1 - la0) * self.k) / 2
        self.inset = (x0, y1 - self.INSET_H, x0 + self.INSET_W, y1)
        ilo0, ilo1, ila0, ila1 = _INSET_BOX
        ics = math.cos(math.radians(26.5))
        self.ik = min(self.INSET_W / ((ilo1 - ilo0) * ics), self.INSET_H / (ila1 - ila0))

    def _proj(self, lon, lat, ins):
        if ins:
            ilo0, _a, ila0, _b = _INSET_BOX
            ics = math.cos(math.radians(26.5))
            return self.inset[0] + (lon - ilo0) * ics * self.ik, self.inset[3] - (lat - ila0) * self.ik
        lo0, _a, la0, _b = _MAIN_BOX
        cs = math.cos(math.radians(37))
        return self.mx0 + (lon - lo0) * cs * self.k, self.my1 - (lat - la0) * self.k

    def xy(self, pref):
        t = TOWN[pref]
        return self._proj(t["lon"], t["lat"], pref == "沖縄")

    def _pref_path(self, ctx, pref):
        ins = pref == "沖縄"
        box = _INSET_BOX if ins else _MAIN_BOX
        for r in JP[ISO[pref]]:
            if not any(box[0] <= x <= box[1] and box[2] <= y <= box[3] for x, y in r[::5] or r):
                continue
            for i, (x, y) in enumerate(r):
                X, Y = self._proj(x, y, ins)
                (ctx.move_to if i == 0 else ctx.line_to)(X, Y)
            ctx.close_path()

    def draw(self, ctx, a=1.0, colors=None):
        """県境つきの地図。colors={県: 色} なら県ごとに塗る（なければ無地）"""
        key = (self.box, tuple(sorted(colors.items())) if colors else None)
        if key not in _MAP_CACHE:
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_, H_)
            c = cairo.Context(surf)
            tset(c, "#cfdbe6")
            x0, y0, x1, y1 = self.box
            rrect(c, x0, y0, x1 - x0, y1 - y0, 22)
            c.fill()
            edge = "#565b6e" if colors else "#8d97a6"   # 2026-11-13 色分けでは県境・海岸を濃く（クリーム色の県が海に溶けないように）
            for pref in ISO:
                if pref == "沖縄":
                    continue
                self._pref_path(c, pref)
                tset(c, (colors or {}).get(pref, "#f8f4ea"))
                c.fill_preserve()
                tset(c, edge)
                c.set_line_width(1.2)
                c.stroke()
            ix0, iy0, ix1, iy1 = self.inset
            tset(c, "#e2eaf1")
            c.rectangle(ix0, iy0, ix1 - ix0, iy1 - iy0)
            c.fill()
            c.save()
            c.rectangle(ix0, iy0, ix1 - ix0, iy1 - iy0)
            c.clip()
            self._pref_path(c, "沖縄")
            tset(c, (colors or {}).get("沖縄", "#f8f4ea"))
            c.fill_preserve()
            tset(c, edge)
            c.set_line_width(1.2)
            c.stroke()
            c.restore()
            tset(c, "#8d97a6")
            c.set_line_width(2)
            c.rectangle(ix0, iy0, ix1 - ix0, iy1 - iy0)
            c.stroke()
            _MAP_CACHE[key] = surf
        _rec(ctx, "inset", "沖縄の枠", *self.inset, a=a)   # 2026-11-13 名札が沖縄の枠にかかったのを点検で拾うため
        ctx.save()
        ctx.set_source_surface(_MAP_CACHE[key], 0, 0)
        ctx.paint_with_alpha(a)
        ctx.restore()

    def glow(self, ctx, t, prefs, col=GOLD, a=1.0):
        """県の形を光らせる（金色の縁と半透明の塗り）"""
        if a <= 0.003:
            return
        for pref in prefs:
            ctx.save()
            if pref == "沖縄":
                ctx.rectangle(self.inset[0], self.inset[1], self.inset[2] - self.inset[0], self.inset[3] - self.inset[1])
                ctx.clip()
            self._pref_path(ctx, pref)
            tset(ctx, col, a * (0.35 + 0.15 * math.sin(t * 5)))
            ctx.fill_preserve()
            tset(ctx, col, a)
            ctx.set_line_width(5)
            ctx.stroke()
            ctx.restore()

    def dots(self, ctx, towns, r=11, a=1.0, col_fn=None):
        for n in towns:
            x, y = self.xy(n)
            c = col_fn(n) if col_fn else med_color(n)
            disc(ctx, x, y, r + 3, "#ffffff", a)
            disc(ctx, x, y, r, c, a)
            _rec_circle(ctx, "県庁所在地の点", x, y, r + 3, a)


RAMP = ((0.0, "#7f8fab"), (0.35, "#e6e0cf"), (0.7, "#f7d04a"), (1.0, "#ef8a2a"))   # 2026-11-13 統括: 少ない＝曇りの灰青 → 黄 → 橙（多い）。灰青と黄の間はくすむので明るいクリームをはさむ


def ramp(u):
    u = max(0.0, min(1.0, u))
    for (u0, c0), (u1, c1) in zip(RAMP, RAMP[1:]):
        if u <= u1:
            return lcol(c0, c1, (u - u0) / (u1 - u0))
    return RAMP[-1][1]


def med_color(pref):
    """県の中央値の色: 少ない＝灰青 → 黄 → 橙（多い）"""
    return ramp((TOWN[pref]["med"] - MED_MIN) / (MED_MAX - MED_MIN))


COLORS47 = {p_: med_color(p_) for p_ in ISO}


def med_legend(ctx, t, a=1.0, show44=False, x0=900, x1=1130, y=830):
    """凡例「見られる回数（中央値）」: 色の帯・4回〜71回・44回の線"""
    if a <= 0.003:
        return
    tx(ctx, "見られる回数（中央値）", (x0 + x1) / 2 + 10, y - 40, 40, DARKTXT, a=a)
    n = 37
    for i in range(n):
        u = i / (n - 1)
        col = ramp(u)
        rect(ctx, col, x0 + (x1 - x0) * i / n, y - 12, x0 + (x1 - x0) * (i + 1) / n + 1, y + 14, a)
    tx(ctx, f"{MED_MIN}回", x0 - 15, y + 46, 40, DARKTXT, a=a)
    tx(ctx, f"{MED_MAX}回", x1 + 20, y + 46, 40, DARKTXT, a=a)
    if show44:
        xm = x0 + (x1 - x0) * (MID47 - MED_MIN) / (MED_MAX - MED_MIN)
        vline(ctx, xm, y - 22, y + 24, REDC, a=a, w=6)
        tx(ctx, f"{MID47}回", xm, y + 46, 40, DARKTXT, a=a)


def label_at(ctx, jm, town, s, dx, dy, a=1.0, size=40, col=DARKTXT, leader=True, align="center"):
    """県の名前を (dx, dy) ずらして置く（県庁所在地の点から引き出し線）"""
    x, y = jm.xy(town)
    if a <= 0.003:
        return
    if leader:
        tset(ctx, "#6b6478", a)
        ctx.set_line_width(3)
        ctx.move_to(x, y)
        ctx.line_to(x + dx * 0.8, y + dy * 0.8)
        ctx.stroke()
    wl = text_width(s, size) + 18
    tset(ctx, "#f4ece4", 0.92 * a)
    rrect(ctx, x + dx - wl / 2, y + dy - size * 0.68, wl, size * 1.36, 10)
    ctx.fill()
    tx(ctx, s, x + dx, y + dy, size, col, align=align, a=a)


# ---- 予想の札・赤丸 ----
def pred_cards(ctx, t, t0, t1, labels, xs, y, size=64, hl=None, hl_t=None, bg="#2d3f7a"):
    for k, s_ in enumerate(labels):
        card(ctx, t, t0 + 0.14 * k, t1, [(s_, size, WHITE)], xs[k], y, pad=(34, 14), bg=bg, border=YEL)
    if hl is not None and hl_t is not None and t >= hl_t:
        w_, h_ = pw([(labels[hl], size, WHITE)], pad=(34, 14))
        ring_box(ctx, xs[hl] - w_ / 2 - 12, y - h_ / 2 - 12, xs[hl] + w_ / 2 + 12, y + h_ / 2 + 12, a=fade(t, hl_t, 0.3))



# ============================================================
# 場面で使う部品と数字
# ============================================================
ctx_t = [0.0]
FULL = (0, 0, W_, H_)
SLOT_X80 = 160                 # 80個の枠（2段×40）の左端
ST67 = None
_r67 = random.Random(3)
_pick = {0} | set(_r67.sample(range(1, N_LIFE), T_TOK["med"] - 1))
ST67 = [1 if i in _pick else 0 for i in range(N_LIFE)]
assert sum(ST67) == T_TOK["med"] == 67
LIFE_DEMO = example_life("東京", 4, seed=20261114)       # 冒頭の「太い線」の例（答えの2年とは別の人）
LAGS = [TOWN[n]["lag"] for n in TOWN]
assert all(-0.6 < v < 0.6 for v in LAGS)
SUBTXT = "#ffffff"


def su(name, t, u0, u1, dur):
    return u0 + (u1 - u0) * seg(t, SC_START[name], SC_START[name] + dur)


def full_window(ctx, t, kind, u=0.0, seed=1, snow=None):
    window(ctx, t, (0, 0, W_, H_ + 74), kind, u, fw=46, curtain=True, seed=seed, snow=snow)


def person_row(ctx, x0, pitch, y, h, n, a_fn):
    for i in range(n):
        person(ctx, x0 + pitch * i, y, h, a_fn(i))


def tag_year_ticks(ctx, x0, pitch, y, n=36, a=1.0):
    tx(ctx, "1991", x0 + pitch * 0.5, y, 48, DARKTXT, a=a)
    tx(ctx, "2026", x0 + pitch * (n - 0.5), y, 48, DARKTXT, a=a)


# ============================================================
# 0 あなたは一生で何回、初日の出を見られる？
# ============================================================
Q1, Q2 = "あなたは一生で何回、", "初日の出を見られる？"
WIN_L, WIN_R = (40, 170, 940, 880), (980, 170, 1880, 880)


def sc_open(ctx, t):
    t_w = Sk("c0_32", 0.0) - 0.3
    b = fade(t, t_w, 0.5)
    if b < 0.999:
        grp(ctx, 1.0 - b, lambda c, tt: full_window(c, tt, "dark", 0.55 * (1 - math.exp(-tt / 1.5)), seed=2, snow=0.35), t)
    if b > 0.003:
        def split(c, tt):
            paint_bg(c, "#1d2650")
            window(c, tt, WIN_L, "clear", min(1.0, 0.25 + 0.04 * max(0.0, tt - t_w)), fw=30, curtain=False, seed=5)
            window(c, tt, WIN_R, "snow", 0.0, fw=30, curtain=False, seed=7)
            tdf = Sk("c0_diff", 0.0)
            if Sk("c0_2") <= tt:
                dim(c, WIN_L, 0.45 * ease_out(clamp01((tt - Sk("c0_2")) / 0.4)) * (1 - fade(tt, tdf, 0.3)))
            elif tt >= Sk("c0_32"):
                dim(c, WIN_R, 0.45 * ease_out(clamp01((tt - Sk("c0_32")) / 0.4)))
            tn_, en_ = Sk("c0_near"), Ek("c0_near")
            if tn_ <= tt <= en_:
                sw = math.sin(2 * math.pi * (tt - tn_) / 1.6)
                rect(c, "#ffffff", WIN_L[0] + 30, WIN_L[1] + 30, WIN_L[2] - 30, WIN_L[3] - 48, 0.18 * max(0.0, sw))
                rect(c, "#ffffff", WIN_R[0] + 30, WIN_R[1] + 30, WIN_R[2] - 30, WIN_R[3] - 48, 0.18 * max(0.0, -sw))
            focus = WIN_L if Sk("c0_32") <= tt < Sk("c0_2") else (WIN_R if Sk("c0_2") <= tt < Sk("c0_diff") else None)
            if focus:
                tset(c, GOLD, 0.9)
                c.set_line_width(10)
                rrect(c, focus[0] + 4, focus[1] + 4, focus[2] - focus[0] - 8, focus[3] - focus[1] - 8, 6)
                c.stroke()
        grp(ctx, b, split, t)
        Cd(ctx, t, "c0_32", 0.1, [("36年のうち", 46, WHITE), ("32回", 100, YEL)], 490, 310, pad=(40, 18), border=YEL)
        Cd(ctx, t, "c0_2", 0.1, [("36年のうち", 46, WHITE), ("2回", 100, YEL)], 1430, 310, pad=(40, 18), border=YEL)
        Cd(ctx, t, "c0_diff", 0.1, [("住む県で、ちがう", 60, WHITE)], 960, 105, pad=(36, 16), border=YEL)
    ap = 1.0 - clamp01((t - (t_w - 0.45)) / 0.4)
    if ap > 0.003:
        panel(ctx, [(Q1, 100, WHITE), (Q2, 100, YEL)], 960, 430, a=ap, pad=(56, 28), border=YEL)


def sc_c0_card(ctx, t):
    card_scene(ctx, t)
    tx(ctx, "一生で何回？", 960, 330, 120, DARKTXT)
    person(ctx, 330, 880, 480)
    person(ctx, 1590, 880, 480)
    Cd(ctx, t, "c0_dou", 0.3, [("2回の県は", 52, WHITE), ("問い2で", 84, YEL)], 960, 640, t1=Sk("c0_last", 0.0) - 0.2, pad=(48, 22), border=YEL)
    Cd(ctx, t, "c0_last", 0.1, [("最後に 全国の地図で", 52, WHITE), ("32回の県と", 66, YEL), ("あなたの県も", 66, YEL)], 960, 650, pad=(48, 22), border=YEL)   # 2026-11-13 後半の約束（条件を0:30より後へ）


def sc_c0_cond(ctx, t):
    card_scene(ctx, t)
    card(ctx, t, SC_START["c0_cond"] + 0.1, None, [("条件をそろえます", 84, YEL)], 960, 170, pad=(48, 20), border=YEL)
    tb = Sk("c0_use") - 1.2
    a = fade(t, tb, 0.4)
    if a > 0.003:
        x0 = 960 - 18 * 44
        slots(ctx, t, x0, 480, 36, 44, 36, [0] * 36, a=a)
        tag_year_ticks(ctx, x0, 44, 560, a=a)
    Cd(ctx, t, "c0_use", 0.2, [("気象庁の記録", 52, WHITE), ("1991〜2026年　36回の元日", 60, YEL)], 960, 720, pad=(44, 20), border=YEL)


def sc_c0_map(ctx, t):
    card_scene(ctx, t)
    jm = JMap(MAP_BOX)
    jm.draw(ctx)
    t0 = SC_START["c0_map"] + 0.6
    for k, p_ in enumerate(P):
        a = fade(t, t0 + 0.05 * k, 0.25)
        x, y = jm.xy(p_[0])
        if a > 0.003:
            disc(ctx, x, y, 11, "#ffffff", a)
            disc(ctx, x, y, 8, "#3a2f55", a)
            _rec_circle(ctx, "県庁所在地の点", x, y, 11, a)
    Cd(ctx, t, "c0_stn", 0.2, [("県庁所在地の", 54, WHITE), ("気象台の記録", 70, YEL)], 1500, 420, pad=(48, 22), border=YEL)


def sc_c0_day(ctx, t):
    full_window(ctx, t, "clear", su("c0_day", t, 0.1, 0.95, 3.8), seed=5)
    Cd(ctx, t, "c0_day", 0.45, [("朝に日が差した＝見えた", 66, YEL)], 960, 800, pad=(44, 18), border=YEL)


def sc_c0_life(ctx, t):
    card_scene(ctx, t)
    Cd(ctx, t, "c0_life", 0.1, [("一生＝80回の元日", 84, YEL)], 960, 260, pad=(52, 22), border=YEL)
    slots(ctx, t, SLOT_X80, 450, N_LIFE, 40, 32, [0] * N_LIFE, a=fade(t, SC_START["c0_life"] + 0.2, 0.4), per_row=40, row_pitch=52)
    a = fade(t, SC_START["c0_life"] + 0.6, 0.4)
    tx(ctx, "平均寿命は80歳をこえる（厚労省 令和7年）", 960, 680, 52, DARKTXT, a=a)


# ============================================================
# 1 東京に住むあなたは、何回見られる？
# ============================================================
PRED1 = ("約35回", "約50回", "約65回")
PRED1_X = (560, 960, 1360)


def sc_c1_a(ctx, t):
    full_window(ctx, t, "clear", su("c1_a", t, 0.05, 0.55, 9.0), seed=9)
    pred_cards(ctx, t, Sk("c1_guess", 0.2), None, PRED1, PRED1_X, 200, size=70)


def sc_c1_t36(ctx, t):
    card_scene(ctx, t)
    x0 = 960 - 18 * 44
    slots(ctx, t, x0, 430, 36, 44, 36, S_TOK36, t_fill=Sk("c1_t36", 0.3), dt=0.06)
    tag_year_ticks(ctx, x0, 44, 510)
    tx(ctx, "県庁所在地の気象台の記録", 960, 568, 44, DARKTXT, a=fade(t, Sk("c1_t36", 0.35), 0.3))
    Cd(ctx, t, "c1_t36", 0.35, [("東京", 46, WHITE), ("30回", 90, YEL), ("/36回の元日", 40, WHITE)], 960, 730, pad=(48, 18), border=YEL)


S_TOK36 = TOWN["東京"]["s"]


def sc_c1_luck(ctx, t):
    card_scene(ctx, t)
    window(ctx, t, (170, 110, 560, 500), "clear", 0.9, fw=22, curtain=False, seed=12)
    window(ctx, t, (1090, 110, 1480, 500), "cloud", 0.0, fw=22, curtain=False, seed=13)
    tx(ctx, "晴れた朝", 365, 560, 44)
    tx(ctx, "曇りの朝", 1285, 560, 44)
    a = fade(t, Sk("c1_luck", 0.1), 0.4)
    person(ctx, 700, 880, 560, a)
    person(ctx, 1620, 880, 560, a)


def sc_c1_tenk(ctx, t):
    card_scene(ctx, t)
    t0 = Sk("c1_tenk", 0.15)
    for r_, n_ in enumerate((17, 17, 16)):
        x0 = 960 - (n_ - 1) * 92 / 2
        for i in range(n_):
            k = r_ * 17 + i
            person(ctx, x0 + 92 * i, 395 + 195 * r_, 170, fade(t, t0 + 0.04 * k, 0.25))
    Cd(ctx, t, "c1_tenk", 0.1, [("東京に住む　1万人", 60, YEL)], 960, 112, pad=(44, 16), border=YEL)
    tx(ctx, "人型1つ＝200人", 960, 860, 48, DARKTXT, a=fade(t, t0 + 1.0, 0.4))


def _stick_x(i, x0=890, p=20):
    return x0 + i * p + p / 2


def draw_box(ctx, t, x0, ytop, wbox, hbox, marks, pull=None, n=36, stick_len=140, pull_t=None, hide_marks=False):
    """くじ引きの箱（2026-11-13 統括: 棒が並ぶとケーキに見える→ 前面に「くじ」の紙・上に丸い穴・引いた札を1枚だけ出す）。
    marks[i]=1 なら当たり（札に日の印）、0 なら外れ（札に×）。pull=引く札の番号（pull_t から穴から持ち上がる）。n・stick_len は互換のため残す"""
    tw, th = wbox * 0.20, hbox * 0.62            # 引いた札の大きさ
    _rec(ctx, "lot", "くじの箱", x0, ytop - th * 0.9, x0 + wbox, ytop + hbox)
    cx = x0 + wbox / 2
    # 箱の本体と上の面
    tset(ctx, "#c98b4a")
    rrect(ctx, x0, ytop, wbox, hbox, 22)
    ctx.fill()
    tset(ctx, "#a96f33")
    rrect(ctx, x0, ytop, wbox, hbox * 0.16, 14)
    ctx.fill()
    tset(ctx, "#5a3a1c")
    ctx.set_line_width(5)
    rrect(ctx, x0, ytop, wbox, hbox, 22)
    ctx.stroke()
    # 上の丸い穴
    tset(ctx, "#2a1a0e")
    ctx.save()
    ctx.translate(cx, ytop + hbox * 0.08)
    ctx.scale(wbox * 0.16, hbox * 0.055)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    # 前面の「くじ」の紙
    lw, lh = wbox * 0.42, hbox * 0.48
    tset(ctx, "#f6ead2")
    rrect(ctx, cx - lw / 2, ytop + hbox * 0.30, lw, lh, 12)
    ctx.fill()
    tx(ctx, "くじ", cx, ytop + hbox * 0.30 + lh / 2, max(40, int(lh * 0.62)), "#2b2140")
    # 引いた札（穴から1枚だけ）
    if pull is not None and pull_t is not None and t >= pull_t:
        up = ease_out(clamp01((t - pull_t) / 1.0))
        yb = ytop + hbox * 0.08
        ytk = yb - th * 0.9 * up
        ctx.save()
        ctx.rectangle(x0 - 50, ytop - th * 2, wbox + 100, (yb - (ytop - th * 2)))
        ctx.clip()
        tset(ctx, "#fffaf0")
        rrect(ctx, cx - tw / 2, ytk, tw, th, 8)
        ctx.fill()
        tset(ctx, "#8a6a4a")
        ctx.set_line_width(3)
        rrect(ctx, cx - tw / 2, ytk, tw, th, 8)
        ctx.stroke()
        ctx.restore()
        if up > 0.6 and not hide_marks:
            ym = ytk + th * 0.32
            if marks[pull]:
                sun_mark(ctx, cx, ym, tw * 0.26)
            else:
                tx(ctx, "×", cx, ym, max(40, int(tw * 0.5)), "#8a3b3b")


def sc_c1_lot(ctx, t):
    card_scene(ctx, t)
    kpull = next(i for i, v in enumerate(S_TOK36) if v)
    t_pull = Sk("c1_draw", 0.3)
    times = [Sk("c1_hit", 0.5)] + [Sk("c1_rep", 0.1) + 0.04 * i for i in range(1, N_LIFE)]
    slots(ctx, t, SLOT_X80, 120, N_LIFE, 40, 32, ST67, times=times, per_row=40, row_pitch=52)
    person(ctx, 330, 880, 600, fade(t, SC_START["c1_lot"] + 0.2, 0.4))
    draw_box(ctx, t, 870, 540, 760, 300, S_TOK36, pull=kpull, pull_t=t_pull)
    Cd(ctx, t, "c1_box", 0.3, [("当たり30本", 60, YEL), ("/36本", 40, WHITE)], 1500, 300, t1=Sk("c1_sep", 0.0) - 0.2, pad=(40, 14), border=YEL)
    card(ctx, t, Sk("c1_rep", 0.0), None, [("当たり30本", 60, YEL), ("/36本", 40, WHITE)], 1500, 300, pad=(40, 14), border=YEL)
    Cd(ctx, t, "c1_sep", 0.1, [("去年と今年は関係ない？", 46, WHITE), ("→ 問い3で確かめる", 46, YEL)], 1500, 300, t1=Sk("c1_rep", 0.0) - 0.2, pad=(36, 12), border=YEL)   # 2026-11-13 初見チェック: 去年と今年の関係の予告（当たり30本の札と入れ替え）
    Cd(ctx, t, "c1_rep", 0.0, [("80回の元日", 60, YEL)], 640, 330, pad=(40, 14), border=YEL)


def person_strip(ctx, t, t0, a=1.0):
    """少ない順に並んだ人の帯（中央値の人に印）"""
    n, pitch, h = 31, 52, 95
    x0 = 960 - (n - 1) * pitch / 2
    mid = n // 2
    for i in range(n):
        if i == mid:
            disc(ctx, x0 + pitch * i, 880 - h * 0.5, h * 0.62, GOLD, 0.55 * a * fade(t, t0 + 0.8, 0.3))
        person(ctx, x0 + pitch * i, 880, h, a * fade(t, t0 + 0.02 * i, 0.25))
    ta = a * fade(t, t0 + 0.8, 0.3)
    if ta > 0.003:
        tset(ctx, REDC, ta)
        xm = x0 + pitch * mid
        ctx.move_to(xm, 800)
        ctx.line_to(xm - 18, 770)
        ctx.line_to(xm + 18, 770)
        ctx.close_path()
        ctx.fill()
    tx(ctx, "少ない", 215, 760, 40, UNITC, a=a * fade(t, t0, 0.3))
    tx(ctx, "多い", 1705, 760, 40, UNITC, a=a * fade(t, t0, 0.3))


PLOT1 = (260, 190, 1660, 590)


def graph_base(ctx, t, key_axes, show_strip=True, t_strip=None):
    card_scene(ctx, t)
    hist_plot(ctx, t, PLOT1, None, None)
    a = fade(t, Sk(key_axes) - 1.0, 0.4)
    tx(ctx, "横：見えた回数", 960, 690, 44, DARKTXT, a=a)
    tx(ctx, "縦：人の数", 230, 140, 44, DARKTXT, align="left", a=a)
    unit_tag(ctx, "/1万人", 1650, 140, a=a, align="right")
    if show_strip:
        person_strip(ctx, t, t_strip if t_strip is not None else Sk("c1_def") - 1.6)


def sc_c1_graph(ctx, t):
    graph_base(ctx, t, "c1_axes")
    card(ctx, t, Sk("c1_def", 0.05), Sk("c1_med", 0.0) - 0.9, [("中央値＝少ない順に並べた、", 46, WHITE), ("ちょうど真ん中の値", 46, YEL)], 960, 400, pad=(40, 18), border=YEL)


def sc_c1_hist(ctx, t):
    graph_base(ctx, t, "c1_axes", t_strip=SC_START["c1_hist"] - 10)
    hist_plot(ctx, t, PLOT1, T_TOK["hist"], Sk("c1_med", 0.1))
    yt, yb = PLOT1[1], PLOT1[3]
    for key, k, col, lab in (("c1_med", T_TOK["med"], GOLD, "中央値 67回"), ("c1_worst", T_TOK["worst"], BLUEC, "最悪 54回"),
                             ("c1_best", T_TOK["best"], GREENC, "最良 79回")):
        vline(ctx, hist_x(PLOT1, k), yt - 30, yb, col, a=fade(t, Sk(key, 0.3), 0.3))
    Cd(ctx, t, "c1_med", 0.3, [("中央値 67回", 64, YEL)], 640, 250, pad=(40, 14), border=GOLD)
    Cd(ctx, t, "c1_worst", 0.3, [("最悪 54回", 64, WHITE)], 640, 380, pad=(40, 14), border=BLUEC)
    Cd(ctx, t, "c1_best", 0.3, [("最良 79回", 64, WHITE)], 640, 510, pad=(40, 14), border=GREENC)


def sc_c1_ans(ctx, t):
    card_scene(ctx, t)
    Cd(ctx, t, "c1_ans", 0.3, arows(1, ("東京 中央値 67回", 84, WHITE), ("（最悪54回・最良79回）", 46, WHITE), ("/1万人", 40, WHITE)), 960, 290, pad=(56, 22), border=YEL)
    pred_cards(ctx, t, SC_START["c1_ans"] + 0.3, None, PRED1, PRED1_X, 700, size=70, hl=2, hl_t=Sk("c1_ans", 0.35))


def sc_c1_8(ctx, t):
    card_scene(ctx, t)
    slots(ctx, t, SLOT_X80, 330, N_LIFE, 40, 32, ST67, t_fill=Sk("c1_8", 0.15), dt=0.03, per_row=40, row_pitch=52)
    Cd(ctx, t, "c1_8", 0.2, [("80回のうち", 46, WHITE), ("約8割", 110, YEL)], 960, 640, pad=(52, 20), border=YEL)


def sc_c1_most(ctx, t):
    full_window(ctx, t, "clear", su("c1_most", t, 0.1, 1.0, 3.6), seed=9)


# ---- 日の出から2時間の数え方 ----
def tband_x(h):
    return 200 + (h - 6.0) * 500


def sc_c1_count(ctx, t):
    card_scene(ctx, t)
    a0 = fade(t, SC_START["c1_count"] + 0.05, 0.4)
    card(ctx, t, SC_START["c1_count"] + 0.1, None, [("見えた年の数え方", 56, YEL)], 960, 130, pad=(40, 14), border=YEL)
    rect(ctx, "#e5eaf4", tband_x(6), 330, tband_x(9), 450, a0)
    for h in range(6, 10):
        x = tband_x(h)
        tset(ctx, "#8a8499", a0)
        ctx.set_line_width(4)
        ctx.move_to(x, 330)
        ctx.line_to(x, 470)
        ctx.stroke()
        tx(ctx, f"{h}時", x, 510, 40, DARKTXT, a=a0)
    tj = Sk("c1_jma", 0.0)
    a_hide = 1 - fade(t, Sk("c1_rule", 0.0), 0.3)   # 帯が出たら「○時台」を消す（帯の下で透けないように）
    for k in range(3):
        a = fade(t, tj + 0.25 * k, 0.3) * a_hide
        if a > 0.003:
            tx(ctx, f"{6 + k}時台", tband_x(6.5 + k), 390, 44, UNITC, a=a)
    card(ctx, t, SC_START["c1_count"] + 0.3, Sk("c1_rule", 0.0) - 0.2, [("日が差した時間", 52, WHITE), ("1時間ごと", 60, YEL)], 960, 760, pad=(44, 18), border=YEL)
    tr = Sk("c1_rule", 0.0)
    ar = fade(t, tr + 0.1, 0.4)
    if ar > 0.003:
        rect(ctx, "#fde9b8", tband_x(6 + 51 / 60), 330, tband_x(8 + 51 / 60), 450, 0.8 * ar)
        for h0, h1 in ((7.05, 7.40), (7.75, 8.0)):
            rect(ctx, GOLD, tband_x(h0), 345, tband_x(h1), 435, ar)
        sun_mark(ctx, tband_x(6 + 51 / 60), 300, 18, ar)
        tx(ctx, "日の出 6:51", tband_x(6 + 51 / 60) + 30, 240, 40, DARKTXT, align="left", a=ar)
        tx(ctx, "8:51", tband_x(8 + 51 / 60), 260, 40, DARKTXT, a=ar)
        tset(ctx, REDC, ar)
        ctx.set_line_width(7)
        ctx.move_to(tband_x(6 + 51 / 60), 575)
        ctx.line_to(tband_x(8 + 51 / 60), 575)
        ctx.stroke()
        tx(ctx, "日の出から2時間", 1125, 622, 44, DARKTXT, a=ar)
    Cd(ctx, t, "c1_rule", 0.1, [("日の出から2時間で", 52, WHITE), ("日が合計30分以上", 60, YEL)], 960, 770, pad=(44, 18), border=YEL)
    tcl = Sk("c1_cloud", 0.0)
    acl = fade(t, tcl + 0.1, 0.4)
    if acl > 0.003:
        _cloud(ctx, tband_x(6 + 51 / 60), 305, 0.28, "#8d97a8", acl)
        for hh_, dd_ in ((7.2, 1.3), (7.88, 1.9)):
            sun_mark(ctx, tband_x(hh_), 300, 18, fade(t, tcl + dd_, 0.4))


def sc_c1_sun(ctx, t):
    card_scene(ctx, t)
    chart_card(ctx, 500, 120, 1420, 600, "#ece3da")
    tx(ctx, "県", 700, 180, 46, UNITC)
    tx(ctx, "日の出（元日）", 1180, 180, 46, UNITC)
    for k, n in enumerate(("東京", "福岡")):
        tx(ctx, n, 700, 300 + 130 * k, 70, DARKTXT)
    te = Sk("c1_ex", 0.3)
    tx(ctx, "6:51", 1180, 300, 70, DARKTXT, a=fade(t, te, 0.3))
    tx(ctx, "7:23", 1180, 430, 70, DARKTXT, a=fade(t, te + 0.5, 0.3))
    Cd(ctx, t, "c1_ex", 0.4, [("どの県も", 52, WHITE), ("日の出から2時間", 60, YEL)], 960, 740, pad=(44, 18), border=YEL)


def sc_c1_chg(ctx, t):
    card_scene(ctx, t)
    jm = JMap((130, 70, 1180, 880))
    jm.draw(ctx)
    t0 = Sk("c1_chg", 0.1)
    for k, p_ in enumerate(P):
        a = fade(t, t0 + 0.05 * k, 0.25)
        if a > 0.003:
            x, y = jm.xy(p_[0])
            disc(ctx, x, y, 11, "#ffffff", a)
            disc(ctx, x, y, 8, BLUEC, a)
            _rec_circle(ctx, "県庁所在地の点", x, y, 11, a)
    Cd(ctx, t, "c1_chg", 0.1, [("では、", 70, WHITE), ("ほかの県は？", 76, YEL)], 1500, 420, pad=(50, 22), border=YEL)


# ============================================================
# 2 36年で2回しか見えなかった町は、どこ？
# ============================================================
def sc_c2_a(ctx, t):
    full_window(ctx, t, "snow", 0.0, seed=21)


def town_labels(ctx, jm, towns, a=1.0):
    D = {"北海道": (-170, -20), "石川": (-150, -30), "秋田": (-140, 0), "東京": (130, 40), "群馬": (-150, -60), "高知": (-80, 80),
         "佐賀": (-95, -75), "山口": (-110, -115), "鹿児島": (125, 35)}   # 2026-11-13 左下は沖縄の枠なので、九州の名札は上と右へ
    for n in towns:
        dx, dy = D[n]
        label_at(ctx, jm, n, n, dx, dy, a=a)


MAP_BOX = (130, 70, 1180, 880)
CAND = ("北海道", "石川", "秋田")
CAND_COLORS = {n: "#4f86c6" for n in CAND}


def sc_c2_map(ctx, t):
    card_scene(ctx, t)
    jm = JMap(MAP_BOX)
    jm.draw(ctx, colors=CAND_COLORS)
    jm.dots(ctx, CAND, 11, col_fn=lambda n: "#1d2650")
    town_labels(ctx, jm, CAND)
    panel(ctx, [("東京 中央値67回", 44, WHITE)], 400, 125, a=1.0, pad=(26, 12))
    for k, n in enumerate(CAND):
        card(ctx, t, Sk("c2_cand", 0.15) + 0.2 * k, None, [(n, 76, WHITE)], 1500, 280 + 160 * k, pad=(50, 18), bg="#2d3f7a", border=YEL)


def sc_c2_three(ctx, t):
    boxes = ((30, 80, 640, 880), (655, 80, 1265, 880), (1280, 80, 1890, 880))
    paint_bg(ctx, "#1d2650")
    for k, b in enumerate(boxes):
        window(ctx, t, b, "snow", 0.0, fw=24, curtain=False, seed=31 + 17 * k)
    for k, n in enumerate(CAND):
        card(ctx, t, Sk("c2_three", 0.2) + 0.2 * k, None, [(n, 76, WHITE)], 335 + 625 * k, 190, pad=(50, 16), bg="#2d3f7a", border=YEL)
    Cd(ctx, t, "c2_same", 0.1, [("同じ決め方", 56, WHITE), ("36回の元日", 56, YEL)], 960, 690, pad=(46, 18), border=YEL)


def sc_c2_ans(ctx, t):
    card_scene(ctx, t)
    jm = JMap(MAP_BOX)
    jm.draw(ctx, colors=CAND_COLORS)
    jm.dots(ctx, CAND, 11, col_fn=lambda n: "#1d2650")
    town_labels(ctx, jm, CAND)
    x, y = jm.xy("秋田")
    ring(ctx, x, y, 34, a=fade(t, Sk("c2_ans", 0.3), 0.3))
    Cd(ctx, t, "c2_ans", 0.3, arows(2, ("秋田 2回", 96, WHITE), ("/36回の元日", 40, WHITE)), 1500, 430, pad=(52, 22), border=YEL)


ROW_X0, ROW_P, ROW_S = 420, 38, 30


def year_row(ctx, t, y, states, t_fill, label, val, t_label, hl=None):
    slots(ctx, t, ROW_X0, y, 36, ROW_P, ROW_S, states, t_fill=t_fill, dt=0.0 if t_fill is None else 0.03, hl=hl)
    card(ctx, t, t_label, None, [(label, 44, WHITE), (val, 64, YEL)], 250, y, pad=(28, 12), border=YEL)


def sc_c2_years(ctx, t):
    card_scene(ctx, t)
    S_AKI = TOWN["秋田"]["s"]
    S_SAP, S_KAN = TOWN["北海道"]["s"], TOWN["石川"]["s"]
    unit_tag(ctx, "/36回の元日", 1650, 120, align="right")
    year_row(ctx, t, 300, S_AKI, Sk("c2_years", 0.3), "秋田", "2回", Sk("c2_years", 0.25))
    for yy in AKITA_YEARS:
        i = yy - 1991
        tx(ctx, str(yy), ROW_X0 + ROW_P * i + ROW_P / 2, 370, 40, DARKTXT, a=fade(t, Sk("c2_years", 0.3) + 0.03 * i, 0.3))
    if t >= Sk("c2_sap") - 0.5:
        year_row(ctx, t, 540, S_SAP, Sk("c2_sap", 0.3), "北海道", "10回", Sk("c2_sap", 0.25))
    if t >= Sk("c2_kan") - 0.5:
        year_row(ctx, t, 760, S_KAN, Sk("c2_kan", 0.3), "石川", "7回", Sk("c2_kan", 0.25))


def sc_c2_chg(ctx, t):
    card_scene(ctx, t)
    S2 = TOWN["秋田"]["s"]
    S3 = list(S2)
    S3[10] = 1
    unit_tag(ctx, "/36回の元日", 1650, 100, align="right")
    year_row(ctx, t, 250, S2, None, "秋田", "2回", SC_START["c2_chg"])
    t3 = Sk("c2_chg", 0.4)
    arrow2(ctx, (960, 310), (960, 400), GOLD, 10, fade(t, t3 - 0.2, 0.3), head=28)
    S3v = [S3[i] if (i != 10 or t >= t3) else 0 for i in range(36)]
    year_row(ctx, t, 470, S3v, None, "もし", "3回", t3 - 0.2)
    Cd(ctx, t, "c2_chg", 0.3, [("2回 → 3回なら", 76, YEL), ("一生の回数は1.5倍", 56, WHITE)], 960, 730, pad=(50, 20), border=YEL)


PLOT2 = (260, 260, 1660, 600)


def sc_c2_ak(ctx, t):
    card_scene(ctx, t)
    tx(ctx, "見えた回数", 960, 700, 44, DARKTXT)
    hist_plot(ctx, t, PLOT2, T_AKI["hist"], Sk("c2_akmed", 0.1))
    yt, yb = PLOT2[1], PLOT2[3]
    unit_tag(ctx, "/1万人", 1650, 140, align="right")
    tx(ctx, "目安", 1650, 190, 40, UNITC, align="right", a=fade(t, Sk("c2_est", 0.1), 0.3))
    card(ctx, t, Sk("c2_orig", 0.1), Sk("c2_chg", 0.0) - 0.1, [("もとの記録 36年で2回", 56, YEL)], 960, 135, pad=(44, 14), border=YEL)
    card(ctx, t, Sk("c2_chg", 0.1), Sk("c2_est", 0.0) - 0.1, [("2回 → 3回なら", 60, YEL), ("一生の回数は1.5倍", 46, WHITE)], 960, 135, pad=(44, 14), border=YEL)
    card(ctx, t, Sk("c2_est", 0.1), None, [("秋田の数字は目安", 52, WHITE), ("（36年で2回から計算）", 40, PALE)], 960, 135, pad=(44, 14), border=YEL)
    for key, k, col in (("c2_akmed", T_AKI["med"], GOLD), ("c2_akworst", T_AKI["worst"], BLUEC), ("c2_akbest", T_AKI["best"], GREENC)):
        vline(ctx, hist_x(PLOT2, k), yt - 20, yb, col, a=fade(t, Sk(key, 0.3), 0.3))
    Cd(ctx, t, "c2_akmed", 0.3, [("中央値 4回", 64, YEL)], 1000, 300, pad=(40, 14), border=GOLD)
    Cd(ctx, t, "c2_akworst", 0.3, [("最悪 0回", 64, WHITE)], 1000, 420, pad=(40, 14), border=BLUEC)
    Cd(ctx, t, "c2_akbest", 0.3, [("最良 13回", 64, WHITE)], 1000, 540, pad=(40, 14), border=GREENC)
    tz = Sk("c2_zero", 0.2)
    x0 = hist_x(PLOT2, 0)
    glow_box(ctx, t, x0 - 24, yb - 60, x0 + 24, yb + 8, fade(t, tz, 0.3))
    Cd(ctx, t, "c2_zero", 0.2, [("一生0回", 46, WHITE), ("92人", 84, YEL), ("/1万人", 40, WHITE)], 1450, 420, pad=(44, 16), border=YEL)


def sc_c2_win(ctx, t):
    full_window(ctx, t, "snow", 0.0, seed=21)
    tn = Sk("c2_next", 0.0)
    if t >= tn:
        panel(ctx, [(f"{min(5, 1 + int((t - tn) / 0.8))}年目", 66, WHITE)], 1620, 170, a=fade(t, tn, 0.3), pad=(36, 14), border=YEL)


def arrow_dash(ctx, p, q, col, t, w=14, a=1.0):
    """流れる点線の矢印（折れ線にしない）"""
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_dash([26, 26], -t * 60)
    ctx.move_to(*p)
    ctx.line_to(*q)
    ctx.stroke()
    ctx.set_dash([])
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    ctx.move_to(q[0] + 14 * math.cos(ang), q[1] + 14 * math.sin(ang))
    ctx.line_to(q[0] - 34 * math.cos(ang - 0.5), q[1] - 34 * math.sin(ang - 0.5))
    ctx.line_to(q[0] - 34 * math.cos(ang + 0.5), q[1] - 34 * math.sin(ang + 0.5))
    ctx.close_path()
    ctx.fill()


def sc_c2_diag(ctx, t):
    card_scene(ctx, t)
    ctx.save()
    ctx.rectangle(110, 40, 1700, 860)
    ctx.clip()
    tset(ctx, "#e6f0fa")
    ctx.rectangle(110, 40, 1700, 580)
    ctx.fill()
    tset(ctx, "#9ec4e8")
    ctx.rectangle(110, 620, 1700, 280)
    ctx.fill()
    pts = [(640, 620), (760, 580), (880, 450), (1000, 310), (1120, 400), (1230, 500), (1340, 590), (1430, 620)]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.line_to(1430, 900)
    ctx.line_to(640, 900)
    ctx.close_path()
    tset(ctx, "#8fb07a")
    ctx.fill()
    tset(ctx, "#ffffff")
    ctx.move_to(930, 400)
    ctx.line_to(1000, 310)
    ctx.line_to(1070, 370)
    ctx.line_to(1000, 380)
    ctx.close_path()
    ctx.fill()
    tx(ctx, "日本海側", 380, 780, 44, DARKTXT)
    tx(ctx, "太平洋側", 1600, 780, 44, DARKTXT)
    tx(ctx, "山", 1000, 720, 44, DARKTXT)
    tw = Sk("c2_wind", 0.0)
    aw = fade(t, tw + 0.2, 0.4)
    if aw > 0.003:
        arrow_dash(ctx, (160, 500), (600, 440), "#3a6fb0", t, a=aw)
    ts = Sk("c2_sea", 0.0)
    ac = fade(t, ts + 0.3, 0.6) * (1 - fade(t, Sk("c2_mt", 0.0) + 0.5, 0.6))
    if ac > 0.003:
        for k in range(4):
            x = 300 + 90 * k
            tset(ctx, "#5b9bd5", ac)
            ctx.set_line_width(6)
            ctx.move_to(x, 610)
            ctx.curve_to(x - 14, 580, x + 14, 560, x, 530)
            ctx.stroke()
        _cloud(ctx, 520, 440, 0.9, "#9aa3b3", ac)
    tm = Sk("c2_mt", 0.0)
    am = fade(t, tm + 0.3, 0.6)
    if am > 0.003:
        _cloud(ctx, 800, 390, 1.0, "#8d97a8", am * (1 - fade(t, Sk("c2_pac", 0.0) + 0.6, 0.8)))
        rnd = random.Random(4)
        for i in range(40):
            px = 700 + rnd.uniform(0, 260)
            py = 450 + (rnd.uniform(0, 200) + 90 * t) % 200
            disc(ctx, px, py, rnd.uniform(4, 7), "#ffffff", am)
        tx(ctx, "雪", 700, 380, 44, DARKTXT, a=am)
    tp = Sk("c2_pac", 0.0)
    ap = fade(t, tp + 0.3, 0.6)
    if ap > 0.003:
        arrow_dash(ctx, (1120, 330), (1420, 330), "#e0892a", t, a=ap)
        sun_mark(ctx, 1560, 230, 36, ap)
    ctx.restore()
    card(ctx, t, SC_START["c2_diag"] + 0.1, Sk("c2_wind", 0.0) - 0.2, [("なぜ、見えない？", 66, YEL)], 960, 140, pad=(44, 16), border=YEL)
    Cd(ctx, t, "c2_wind", 0.2, [("冬の北西の季節風", 54, WHITE)], 560, 170, pad=(36, 14), border=YEL)
    Cd(ctx, t, "c2_pac", 0.3, [("太平洋側は晴れやすい", 54, WHITE)], 1450, 450, pad=(36, 14), border=YEL)


def sc_c2_cant(ctx, t):
    card_scene(ctx, t)
    for k, (n, v) in enumerate((("北海道", "10回"), ("石川", "7回"), ("秋田", "2回"))):
        Cd(ctx, t, "c2_cant", 0.05 + 0.15 * k, [(n, 46, WHITE), (v, 80, YEL)], 560 + 400 * k, 300, pad=(44, 16), border=YEL)
    unit_tag(ctx, "/36回の元日", 960, 470, a=fade(t, Sk("c2_cant", 0.3), 0.3))
    Cd(ctx, t, "c2_found", 0.3, [("日本海側は", 56, WHITE), ("見られない年のほうが多い", 64, YEL)], 960, 700, pad=(52, 22), border=YEL)


# ============================================================
# 3 見られない年は、何年続く？
# ============================================================
def sc_c3_a(ctx, t):
    full_window(ctx, t, "snow", 0.0, seed=21)
    Cd(ctx, t, "c3_this", 0.1, [("この章では", 52, WHITE), ("続く年数", 84, YEL)], 960, 740, pad=(48, 18), border=YEL)
    Cd(ctx, t, "c3_this", 0.1, [("秋田 36年で2回", 44, WHITE)], 420, 120, pad=(30, 12))


GRID3 = dict(x0=560, pitch=40, size=34, per_row=27, row_pitch=70)


def sc_c3_lot(ctx, t):
    card_scene(ctx, t)
    person(ctx, 330, 880, 600, fade(t, SC_START["c3_lot"] + 0.2, 0.4))
    st = LIFE_AKI
    t0 = Sk("c3_lost", 0.1)
    slots(ctx, t, GRID3["x0"], 300, N_LIFE, GRID3["pitch"], GRID3["size"], st, t_fill=t0, dt=0.05, cross=True, per_row=GRID3["per_row"], row_pitch=GRID3["row_pitch"])
    ln, i0 = longest_run(st)
    ts = Sk("c3_streak", 0.2)
    run_bar(ctx, GRID3["x0"], 300, GRID3["pitch"], i0, ln, GRID3["size"], a=fade(t, ts, 0.3), prog=ease_out(clamp01((t - ts) / 1.2)),
            per_row=GRID3["per_row"], row_pitch=GRID3["row_pitch"])
    Cd(ctx, t, "c3_streak", 0.3, [("続けて外れる", 64, YEL)], 1100, 640, pad=(44, 16), border=YEL)


def sc_c3_count(ctx, t):
    card_scene(ctx, t)
    slots(ctx, t, SLOT_X80, 250, N_LIFE, 40, 32, LIFE_DEMO, cross=True, per_row=40, row_pitch=70)
    ln, i0 = longest_run(LIFE_DEMO)
    run_bar(ctx, SLOT_X80, 250, 40, i0, ln, 32, per_row=40, row_pitch=70)
    unit_tag(ctx, "/1万人", 1650, 130, align="right")
    Cd(ctx, t, "c3_count", 0.05, [("いちばん長く続いた年数", 56, WHITE), ("/1万人", 40, WHITE)], 960, 600, pad=(44, 16), border=YEL)
    card(ctx, t, Sk("c3_guess", 0.1), None, [("東京は、何年続く？", 64, WHITE)], 960, 790, pad=(44, 14), bg="#2d3f7a", border=YEL)


def sc_c3_ans(ctx, t):
    card_scene(ctx, t)
    G = dict(pitch=40, size=32, per_row=40, row_pitch=54)
    for tw_, key, y0, life, lab in (("東京", "c3_ans", 280, LIFE_TOK, [("問い3の答え", 40, YEL), ("東京 中央値 2年 /1万人", 60, WHITE)]),
                                  ("秋田", "c3_ak", 600, LIFE_AKI, [("秋田 中央値 33年 /1万人", 60, WHITE)])):
        t0 = Sk(key, 0.15)
        slots(ctx, t, SLOT_X80, y0, N_LIFE, G["pitch"], G["size"], life, t_fill=t0, dt=0.012, cross=True, per_row=G["per_row"], row_pitch=G["row_pitch"])
        ln, i0 = longest_run(life)
        run_bar(ctx, SLOT_X80, y0, G["pitch"], i0, ln, G["size"], a=fade(t, t0 + 1.2, 0.3), prog=ease_out(clamp01((t - t0 - 1.2) / 1.2)),
                per_row=G["per_row"], row_pitch=G["row_pitch"])
        Cd(ctx, t, key, 0.0, lab, 960, y0 - 125 if tw_ == "東京" else y0 - 90, lead=-0.25, pad=(48, 14), border=YEL)


def sc_c3_age(ctx, t):
    full_window(ctx, t, "snow", 0.0, seed=21)
    t0 = Sk("c3_age", 0.0)
    n = min(33, int(33 * seg(t, t0, t0 + 3.0)))
    if t >= t0:
        panel(ctx, [(f"{n}歳", 90, WHITE)], 1560, 800, a=fade(t, t0, 0.3), pad=(44, 14), border=YEL)


def sc_c3_20a(ctx, t):
    card_scene(ctx, t)
    slots(ctx, t, SLOT_X80, 280, N_LIFE, 40, 32, [0] * N_LIFE, per_row=40, row_pitch=54)
    ta = Sk("c3_20", 0.2)
    run_bar(ctx, SLOT_X80, 280, 40, 0, 20, 32, a=fade(t, ta, 0.3), prog=ease_out(clamp01((t - ta) / 1.0)), per_row=40, row_pitch=54)
    Cd(ctx, t, "c3_20", 0.2, [("20年以上", 64, YEL), ("続けて見られない", 52, WHITE)], 960, 560, pad=(48, 18), border=YEL)
    x0, y0 = slot_xy(SLOT_X80, 280, 0, 40)
    x1, _y1 = slot_xy(SLOT_X80, 280, 19, 40)
    glow_box(ctx, t, x0 - 28, y0 - 28, x1 + 28, y0 + 28 + 54 * 0, fade(t, Sk("c3_q4", 0.2), 0.3))
    Cd(ctx, t, "c3_q4", 0.2, [("20年＝80回の4分の1", 60, YEL)], 960, 740, pad=(48, 16), border=YEL)


def sc_c3_20b(ctx, t):
    card_scene(ctx, t)
    unit_tag(ctx, "/1万人", 1650, 110, align="right")
    rows = (("秋田", T_AKI["s20"], "c3_9370", 190), ("石川", TOWN["石川"]["s20"], "c3_kan", 320), ("東京", T_TOK["s20"], "c3_tok", 450))
    for n, v, key, y in rows:
        tx(ctx, n, 330, y, 60, DARKTXT, align="right", a=fade(t, SC_START["c3_20b"] + 0.3, 0.3))
        a = fade(t, Sk(key, 0.1), 0.3)
        ln = 1000 * v / 10000
        if v:
            tset(ctx, AKANE, a)
            rrect(ctx, 360, y - 40, max(30.0, ln * ease_out(clamp01((t - Sk(key, 0.1)) / 1.0))), 80, 14)
            ctx.fill()
        Cd(ctx, t, key, 0.3, [(f"{v:,}人", 60, YEL)], 360 + max(30.0, ln) + 130, y, pad=(30, 10), border=YEL)
    tm = Sk("c3_most", 0.1)
    for i in range(20):
        lit = i < 19
        x = 160 + 80 * i + 40
        if lit:
            disc(ctx, x, 870 - 75, 62, GOLD, 0.6 * fade(t, tm + 0.04 * i, 0.3))
        person(ctx, x, 870, 150, fade(t, tm - 0.2, 0.3))


def sc_c3_hit(ctx, t):
    th, tn, tg = Sk("c3_hit", 0.45), Sk("c3_next", 0.15), Sk("c3_g2", 0.0)
    full_window(ctx, t, "snow", 0.0, seed=21)
    ca = ease_out(clamp01((t - th) / 0.8)) * (1 - ease_out(clamp01((t - tn) / 0.6)))
    if ca > 0.003:
        grp(ctx, ca, lambda c, tt: full_window(c, tt, "clear", 0.7, seed=21), t)
    ta = fade(t, tg - 0.2, 0.6)
    if ta > 0.003:
        grp(ctx, ta, lambda c, tt: full_window(c, tt, "dark", 0.6, seed=22), t)
    Cd(ctx, t, "c3_next", 0.1, [("次の年", 66, WHITE)], 1620, 170, t1=Sk("c3_g2", 0.0) - 0.3, pad=(36, 14), border=YEL)
    Cd(ctx, t, "c3_g2", 0.1, [("去年見えたら、今年は？", 60, WHITE)], 960, 800, pad=(44, 16), bg="#2d3f7a", border=YEL)


AX3 = (300, 1620, 520)


def sc_c3_corr(ctx, t):
    card_scene(ctx, t)
    tx(ctx, "47都道府県　36年の記録で調べる", 960, 130, 52, DARKTXT)
    tx(ctx, "去年と今年の関係の強さ", 960, 215, 44, UNITC)
    x0, x1, y = AX3
    xc = (x0 + x1) / 2
    xs = lambda v: xc + v * (x1 - xc)
    rect(ctx, "#e8dfe8", xs(-0.3), 400, xs(0.3), 560)
    tset(ctx, "#8a8499")
    ctx.set_line_width(5)
    ctx.move_to(x0 - 20, y + 60)
    ctx.line_to(x1 + 20, y + 60)
    ctx.stroke()
    for (xx, l1, l2) in ((x0 + 150, "去年見えたら", "今年は見えにくい"), (x1 - 150, "去年見えたら", "今年も見えやすい")):   # 2026-11-13 初見チェック: 県ごとの見えやすさの図と読み違えない軸の言葉
        tx(ctx, l1, xx, y + 110, 40, DARKTXT)
        tx(ctx, l2, xx, y + 160, 40, DARKTXT)
    tx(ctx, "関係なし", xc, y + 120, 44, DARKTXT)
    rnd = random.Random(6)
    ta = Sk("c3_dot", 0.15)
    for k, v in enumerate(LAGS):
        yy = 440 + rnd.uniform(0, 100)
        a = fade(t, ta + 0.055 * k, 0.2)
        if a > 0.003:
            disc(ctx, xs(v), yy, 15, "#ffffff", a)
            disc(ctx, xs(v), yy, 12, BLUEC, a)
    vline(ctx, xc, 385, 585, GOLD, a=fade(t, Sk("c3_dot", 0.3), 0.3) * out_fade(t, Sk("c3_a4", 0.0), 0.3) * (0.75 + 0.25 * math.sin(t * 6)), w=10)
    Cd(ctx, t, "c3_a4", 0.3, [("去年と今年の関係は、ほぼなし", 56, YEL)], 960, 840, pad=(44, 14), border=YEL)


NEW_PULLS = ([i for i, v in enumerate(S_TOK36) if v][0], [i for i, v in enumerate(S_TOK36) if not v][0], [i for i, v in enumerate(S_TOK36) if v][1])   # 当たり・外れ・当たり（毎年が新しいくじ）


def sc_c3_new(ctx, t):
    card_scene(ctx, t)
    t0 = Sk("c3_new", 0.0)
    for k in range(3):
        a = fade(t, t0 + 1.1 * k, 0.4)
        if a > 0.003:
            x = 420 + 540 * k
            grp(ctx, a, lambda c, tt, x=x, k=k: (draw_box(c, tt, x - 190, 450, 380, 190, S_TOK36, pull=NEW_PULLS[k], pull_t=t0 + 1.1 * k + 0.5, n=12, stick_len=100)
                                                    , tx(c, f"{k + 1}年目", x, 700, 44, DARKTXT)), t)
    Cd(ctx, t, "c3_found", 0.3, [("何十年も続くことがある", 64, YEL)], 960, 830, pad=(48, 14), border=YEL)


# ============================================================
# 4 あなたの町は？
# ============================================================
def sc_c4_a(ctx, t):
    full_window(ctx, t, "clear", su("c4_a", t, 0.1, 0.6, 9.0), seed=41)
    Cd(ctx, t, "c4_this", 0.1, [("この章では", 52, WHITE), ("あなたの県", 84, YEL)], 480, 300, pad=(48, 18), border=YEL)
    Cd(ctx, t, "c4_this", 0.1, [("何十年も続く県がある", 44, WHITE)], 480, 120, pad=(30, 12))


MAP4 = (130, 70, 1180, 880)


def map47(ctx, t, legend=True, show44=False, a_leg=1.0):
    """47都道府県の色分け地図（中央値の色）と凡例"""
    jm = JMap(MAP4)
    jm.draw(ctx, colors=COLORS47)
    if legend:
        med_legend(ctx, t, a=a_leg, show44=show44)
    return jm


def sc_c4_map(ctx, t):
    card_scene(ctx, t)
    map47(ctx, t, a_leg=fade(t, Sk("c4_map", 0.3), 0.4))
    Cd(ctx, t, "c4_map", 0.3, [("47都道府県", 80, YEL)], 1500, 330, pad=(60, 22), border=YEL)


def sc_c4_mae(ctx, t):
    card_scene(ctx, t)
    jm = map47(ctx, t)
    jm.glow(ctx, t, ("群馬", "高知"), a=1.0)
    jm.dots(ctx, ("群馬", "高知"), 9, col_fn=lambda n: "#1d2650")
    town_labels(ctx, jm, ("群馬", "高知"))
    Cd(ctx, t, "c4_mae", 0.3, [("群馬・高知", 56, WHITE), ("32回", 90, YEL), ("/36回の元日", 40, WHITE)], 1500, 270, pad=(44, 16), border=YEL)
    Cd(ctx, t, "c4_71", 0.3, [("群馬・高知", 56, WHITE), ("中央値 71回", 76, YEL), ("/1万人", 40, WHITE)], 1500, 570, pad=(44, 16), border=YEL)


def sc_c4_best(ctx, t):
    card_scene(ctx, t)
    Cd(ctx, t, "c4_mbest", 0.2, [("群馬 最良 80回", 64, YEL), ("/1万人", 40, WHITE)], 960, 130, pad=(48, 14), border=YEL)
    person(ctx, 960, 640, 420, fade(t, Sk("c4_mbest", 0.2), 0.4))
    slots(ctx, t, SLOT_X80, 720, N_LIFE, 40, 32, [1] * N_LIFE, t_fill=Sk("c4_all80", 0.1), dt=0.03, per_row=40, row_pitch=54)
    Cd(ctx, t, "c4_all80", 0.2, [("80回すべて", 56, YEL)], 1500, 420, pad=(44, 14), border=YEL)


def sc_c4_city(ctx, t):
    card_scene(ctx, t)
    t44 = Sk("c4_mark", 0.1)
    jm = map47(ctx, t, show44=t >= t44)
    jm.glow(ctx, t, ("東京",), a=fade(t, Sk("c4_tok", 0.2), 0.3))
    tm = Sk("c4_mid", 0.3)
    jm.glow(ctx, t, MID47_PREFS, col="#ffffff", a=fade(t, tm, 0.3))
    jm.dots(ctx, ["東京"] + MID47_PREFS, 9, col_fn=lambda n: "#1d2650", a=fade(t, Sk("c4_tok", 0.2), 0.3))
    town_labels(ctx, jm, ["東京"] + MID47_PREFS, a=fade(t, Sk("c4_tok", 0.2), 0.3))
    Cd(ctx, t, "c4_tok", 0.3, [("東京 67回", 64, YEL), ("/1万人", 40, WHITE)], 1500, 230, pad=(44, 14), border=YEL)
    Cd(ctx, t, "c4_mid", 0.3, [("47都道府県の", 46, WHITE), ("中央値 44回", 72, YEL), ("44回の県:", 40, WHITE), ("佐賀・山口・鹿児島", 40, WHITE)], 1500, 560, pad=(44, 14), border=YEL)


def sc_c4_city2(ctx, t):
    card_scene(ctx, t)
    jm = map47(ctx, t, show44=True)
    jm.glow(ctx, t, ("北海道",), a=fade(t, Sk("c4_sap", 0.2), 0.3))
    jm.glow(ctx, t, ("秋田",), a=fade(t, Sk("c4_aki", 0.2), 0.3))
    jm.dots(ctx, ("北海道",), 9, col_fn=lambda n: "#1d2650", a=fade(t, Sk("c4_sap", 0.2), 0.3))
    jm.dots(ctx, ("秋田",), 9, col_fn=lambda n: "#1d2650", a=fade(t, Sk("c4_aki", 0.2), 0.3))
    town_labels(ctx, jm, ("北海道",), a=fade(t, Sk("c4_sap", 0.2), 0.3))
    town_labels(ctx, jm, ("秋田",), a=fade(t, Sk("c4_aki", 0.2), 0.3))
    Cd(ctx, t, "c4_sap", 0.3, [("北海道 22回", 64, YEL), ("/1万人", 40, WHITE)], 1500, 230, pad=(44, 14), border=YEL)
    Cd(ctx, t, "c4_aki", 0.3, [("秋田 4回", 64, YEL), ("/1万人", 40, WHITE), ("目安", 40, WHITE)], 1500, 470, pad=(44, 14), border=YEL)


def sc_c4_cmp(ctx, t):
    card_scene(ctx, t)
    jm = map47(ctx, t, show44=True)
    jm.glow(ctx, t, ("群馬", "高知", "秋田"), a=1.0)
    jm.dots(ctx, ("群馬", "秋田"), 9, col_fn=lambda n: "#1d2650")
    town_labels(ctx, jm, ("群馬", "秋田"))
    xa, ya = jm.xy("群馬")
    xb, yb = jm.xy("秋田")
    tl_ = Sk("c4_x18", 0.4)
    a = fade(t, tl_, 0.4)
    if a > 0.003:
        line2(ctx, (xa, ya), (lerp(xa, xb, ease_out(clamp01((t - tl_) / 0.8))), lerp(ya, yb, ease_out(clamp01((t - tl_) / 0.8)))), REDC, 7, a)
    Cd(ctx, t, "c4_cmp", 0.3, [("71回 ÷ 4回", 84, YEL)], 1500, 300, pad=(48, 20), border=YEL)
    Cd(ctx, t, "c4_x18", 0.3, [("約18倍", 130, YEL), ("秋田の4回は目安", 40, WHITE)], 1500, 600, pad=(56, 22), border=YEL)


TBL_PAGES = (
    ("北海道・東北・関東", ("北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川")),
    ("中部・近畿", ("新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山")),
    ("中国・四国・九州・沖縄", ("鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄")))
assert sorted(n for _t, ns in TBL_PAGES for n in ns) == sorted(TOWN) and len(TOWN) == 47


def table_page(ctx, t, title, towns):
    card_scene(ctx, t)
    tx(ctx, title, 960, 85, 48, DARKTXT)
    unit_tag(ctx, "/1万人", 1700, 85, align="right")
    half = (len(towns) + 1) // 2
    for b, blk in enumerate((towns[:half], towns[half:])):
        bx = 150 + 840 * b
        cols = (bx + 110, bx + 370, bx + 540, bx + 700)
        for x, s_ in zip(cols, ("都道府県", "最悪", "中央値", "最良")):
            tx(ctx, s_, x, 165, 44, UNITC)
        for k, n in enumerate(blk):
            y = 235 + 56 * k
            if k % 2 == 0:
                rect(ctx, "#ebe2d8", bx, y - 28, bx + 790, y + 28)
            if k == int(t / 0.9) % len(blk):                      # 見ている行を示す光の帯（表の場面は長く止まるので、動きをつける）
                rect(ctx, "#f7e3a0", bx, y - 28, bx + 790, y + 28)
            r = TOWN[n]
            tx(ctx, n, cols[0], y, 44, DARKTXT)
            for x, v in zip(cols[1:], (r["worst"], r["med"], r["best"])):
                tx(ctx, str(v), x, y, 44, DARKTXT)


def sc_c4_tbl(ctx, t):
    table_page(ctx, t, *TBL_PAGES[0])


def sc_c4_tbl2(ctx, t):
    table_page(ctx, t, *TBL_PAGES[1])


def sc_c4_tbl3(ctx, t):
    table_page(ctx, t, *TBL_PAGES[2])


def sc_c4_near(ctx, t):
    card_scene(ctx, t)
    jm = map47(ctx, t)
    t0 = SC_START["c4_near"] + 0.4
    for k, p_ in enumerate(P):
        a = fade(t, t0 + 0.05 * k, 0.25)
        x, y = jm.xy(p_[0])
        if a > 0.003:
            disc(ctx, x, y, 9, "#ffffff", a)
            disc(ctx, x, y, 6, "#1d2650", a)
            _rec_circle(ctx, "県庁所在地の点", x, y, 9, a)
    Cd(ctx, t, "c4_near", 0.2, [("県庁所在地の", 54, WHITE), ("気象台の記録", 70, YEL)], 1500, 230, pad=(48, 22), border=YEL)
    Cd(ctx, t, "c4_found", 0.3, [("住む県で、", 64, WHITE), ("何倍もちがう", 76, YEL)], 1500, 520, pad=(50, 22), border=YEL)


# ============================================================
# 5 まとめ
# ============================================================
def sc_c5_map(ctx, t):
    card_scene(ctx, t)
    jm = map47(ctx, t)
    al = fade(t, ch_start(5) + T_TITLE[5] + 0.1, 0.4)
    label_at(ctx, jm, "群馬", "群馬 71回", -170, -60, a=al)
    label_at(ctx, jm, "秋田", "秋田 4回", -150, 0, a=al)
    Cd(ctx, t, "c5_sum", 0.3, [("中央値 4回〜71回", 64, YEL), ("/1万人", 40, WHITE)], 1500, 420, pad=(48, 18), border=YEL)


def sc_c5_win(ctx, t):
    full_window(ctx, t, "snow", 0.0, seed=21)
    ta = Sk("c5_you", 0.0)
    ca = fade(t, ta, 0.8)
    if ca > 0.003:
        grp(ctx, ca, lambda c, tt: full_window(c, tt, "clear", 0.15 + 0.7 * seg(tt, ta, ta + 3.0), seed=21), t)
    Cd(ctx, t, "c5_you", 0.2, [("あなたの県は、何回？", 76, WHITE)], 960, 220, pad=(52, 18), border=YEL)


def sc_c5_close(ctx, t):
    chart_bg(ctx, t)
    person(ctx, 330, 900, 560)
    Cd(ctx, t, "c5_ch", 0.1, [("めでたしかめ", 110, YEL), ("身近な疑問を", 54, WHITE), ("シミュレーションで確かめる", 54, WHITE)], 1100, 300, pad=(60, 24), border=YEL)
    Cd(ctx, t, "c5_sub", 0.25, [("チャンネル登録", 90, WHITE)], 1400, 800, pad=(50, 22), bg="#c8372d")


END_SUB = ["よければ", "チャンネル登録・高評価", "お願いします"]


def end_rows():
    return [("東京", "中央値 67回"), ("秋田", "中央値 4回"), ("秋田は続けて見られない", "中央値 33年")]


def sc_end(ctx, t):
    chart_bg(ctx, t)
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    panel(ctx, [("答え", 80, YEL)], 490, 95, a=b, pad=(44, 8), r=20)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 46, WHITE), (val, 70, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        person(ctx, 1500, 905, 470, a=fade(t, t9 + 0.1, 0.4))
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1480, 270, a=fade(t, t9 + 0.3, 0.4))



# ============================================================
# 区切り（ここまで／ここから・小さな亀が歩く）
# ============================================================
EC_LEFT = ("東京は 中央値67回", "秋田は 中央値4回")
EC_RIGHT = ("見られない年は何年続く？", "あなたの県は？")
EC_FADE = 0.35
EC_BG = "#2b2f5a"


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
        pr_ = clamp01((t - self.t0 - 0.1) / 0.4)
        x0, x1 = (cx + 210, cx - 230) if back else (cx - 210, cx + 230)
        if pr_ > 0:
            arrow2(ctx, (x0, 340), (lerp(x0, x1, pr_), 340), REDC, 9, a, head=26)
        for i, s_ in enumerate(lines):
            text(ctx, s_, cx, 470 + i * 92, self._sizes[s_], WHITE, alpha=a)

    def _scene(self, ctx, t):
        from engine.brand import turtle
        paint_bg(ctx, EC_BG)
        fill(ctx, hexrgb("#ffffff", 0.18))
        ctx.rectangle(958, 60, 4, 760)
        ctx.fill()
        self._page(ctx, t, self.lx, "ここまで", self.left, True)
        self._page(ctx, t, self.rx, "ここから", self.right, False)
        rect(ctx, "#e9c9b8", 0, 905, W_, 918)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:                                      # 足あと（小さな点）
                ctx.set_source_rgba(1, 1, 1, 0.35 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, 895 + (6 if i % 2 else -6), 6, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        tr = t - self.t0
        blink = 1.0 if 0.35 < tr % 1.8 < 0.47 else 0.0
        turtle(ctx, x, self.Y - 3 * abs(math.sin(tr * 6.0)), self.TURTLE_S, blink=blink)


EC = FlatEyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None

# ============================================================
# 場面を並べる
# ============================================================
LAST_BEFORE_REST = "c2_cant"


def _start_of(spec):
    if spec == "zero":
        return 0.0
    if spec == "end":
        return T_ES
    if spec.startswith("ch:"):
        n = int(spec[3:])
        return ch_start(n) - 0.3 if n == LAST_CH else ch_start(n) + 0.5
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
    if name == LAST_BEFORE_REST:
        return T_RS0 - 0.3
    if nspec.startswith("ch:"):
        return ch_start(int(nspec[3:])) - 0.3
    return _start_of(nspec)


for _j, (_nm, _spec, _fn) in enumerate(SC_TABLE):
    SC_END[_nm] = _end_of(_j)
for _j, (_nm, _spec, _fn) in enumerate(SC_TABLE):
    scene(_nm, _start_of(_spec), _end_of(_j), globals()[_fn], first=(_nm == "open"))


def draw(ctx, t, sub=True):
    ctx_t[0] = t
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
# 音（BGM は 0秒から。効果音は章の始まり・答え・区切りの足音）
# ============================================================
def step_pop(seed=0, high=False):
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    return tone * env * 0.8


BELLS = [Sk("c1_ans", 0.3), Sk("c2_ans", 0.3), Sk("c3_ans", 0.3), Sk("c4_x18", 0.3)]


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
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)
    mx.add(Sk(LAST_KEY, 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(T_ES + 0.3, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（要所）
# ============================================================
def still_list():
    return [
        ("1_open", "0:02 問い（暗い東の空）", 2.0),
        ("2_split", "二つの窓（晴れ／雪）", Sk("c0_diff", 0.9)),
        ("3_c1_lot", "くじの箱と80個の枠", Sk("c1_rep", 0.9)),
        ("4_c1_ans", "問い1の答え 東京67回", Sk("c1_ans", 0.95)),
        ("5_c2_ak", "秋田 92人", Ek("c2_zero") - 0.2),
        ("6_c2_diag", "断面図 太平洋側", Ek("c2_pac") - 0.2),
        ("7_rest", "区切り", T_RS0 + 2.0),
        ("8_c3_ans", "問い3の答え 33年", Ek("c3_ak") + 0.3),
        ("9_c4_tbl", "47都道府県の表", Sk("c4_tbl", 0.9)),
    ]


def _ts(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_sheet(out_dir, items, thumb=(480, 270), cols=3, sheet_name="stills_480.png"):
    """静止画を 1920×1080 で書き出し、480px 幅の一覧を作る（古い静止画は消さずに上書き）"""
    from PIL import ImageDraw, ImageFont
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
    fnt = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", 17)
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W2, H2), Image.LANCZOS)
        x, y = pad + (k % cols) * (W2 + pad), pad + (k // cols) * (H2 + lab_h + pad)
        dr.text((x + 4, y + 4), f"{_ts(items[k][2])}  {items[k][1]}", fill=(255, 225, 120), font=fnt)
        sheet.paste(im, (x, y + lab_h))
    sheet.save(out_dir.parent / sheet_name)
    print("一覧:", out_dir.parent / sheet_name)


def body_sheet():
    """本編の静止画一覧: 全場面（8秒ごとに途中のコマも）を 480px 幅で並べる。body_stills_480.png と12枚割りの p1〜"""
    from PIL import ImageDraw, ImageFont
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
    if EC:
        items.append(("区切り", T_RS0 + 2.0))
        items.sort(key=lambda x: x[1])
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
    rows = ["## 0 声に渡した文（読みの補正つき。sims/hatsuhinode-long.py --voicemd が出力）"]
    for it in tl.items:
        if isinstance(it, lf.Line):
            rows.append("- " + it.text)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("声に渡した文:", path)


def _screen_texts():
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


WATCH = ["初日の出", "中央値", "気象庁", "日照", "元日", "日の出", "見えた", "日本海側", "太平洋側", "季節風", "水蒸気", "雪雲", "群馬", "高知", "石川", "秋田",
         "北海道", "福岡", "東京", "約18倍", "一生", "何倍", "最悪", "最良", "目安"]


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


def tail_check():
    """文末切れの機械確認: 声の最後の 0.15秒がほぼ無音になっているか（tail_fix のあと）。本番の声のときだけ"""
    bad = []
    if FAKE:
        return bad
    for s, e, _p, ln, clip in tl._lines:
        x = np.asarray(clip.samples(), dtype=np.float64)
        n = int(0.15 * core.SR)
        if len(x) < n * 2:
            continue
        tail = float(np.sqrt(np.mean(x[-n:] ** 2)))
        body = float(np.sqrt(np.mean(x ** 2))) + 1e-9
        if tail / body > 0.35:
            bad.append((ln.id, round(tail / body, 2)))
    return bad


# ============================================================
# 絵の出る時刻の記録（visual_lag 用）: 枠は声の0.5秒前までに・答えは声に合わせる
# ============================================================
def rd(scene_name, own_t, d):
    return max(SC_START[scene_name] + SC_DELAY + SC_IN, own_t + d)


def _fr(name, scene_nm, key, d=0.0):
    t0 = SC_START[scene_nm]
    return lk.Cue(name, "frame", t0, rd(scene_nm, t0, d), ID[key])


def _fc(name, key, t_start, fade_=0.4):
    """場面の途中で出す枠（出はじめと、そろう時刻を直接書く）"""
    return lk.Cue(name, "frame", t_start, t_start + fade_, ID[key])


def _val(name, key, frac, off=0.0):
    t0 = Sk(key, frac) + off
    return lk.Cue(name, "value", t0, t0 + 0.3, ID[key])


ALL_CUES = [
    _fc("年表の枠(36回の元日)", "c0_use", Sk("c0_use") - 1.2),
    _fr("36個の枠の列(東京)", "c1_t36", "c1_t36"), _fr("くじの箱", "c1_lot", "c1_box"), _fr("グラフの枠", "c1_graph", "c1_graph"),
    _fc("軸の札(横・縦)", "c1_axes", Sk("c1_axes") - 1.0), _fc("人の帯(少ない順)", "c1_def", Sk("c1_def") - 1.6, 0.9),
    _fr("時間の帯の枠", "c1_count", "c1_count", 0.05), _fr("日の出の表の枠", "c1_sun", "c1_sr"),
    _fr("地図の枠(三つの道県)", "c2_map", "c2_cand"), _fr("36個の枠の列(秋田)", "c2_years", "c2_years"), _fr("グラフの枠(秋田)", "c2_ak", "c2_akmed"),
    _fr("断面図の枠", "c2_diag", "c2_wind"), _fr("80個の枠の列(続く年数)", "c3_count", "c3_count"), _fr("80個の枠の列(20年)", "c3_20a", "c3_20"),
    _fr("点の図の枠", "c3_corr", "c3_chk"), _fr("地図の枠(47都道府県)", "c4_map", "c4_map"), _fr("地図の枠(県庁所在地)", "c0_map", "c0_stn"), _fr("地図の枠(群馬・高知)", "c4_mae", "c4_mae"),
    _fr("地図の枠(東京・中央値44回)", "c4_city", "c4_tok"), _fr("地図の枠(比べる)", "c4_cmp", "c4_cmp"), _fr("表の枠(北海道〜関東)", "c4_tbl", "c4_tbl"),
    _fr("表の枠(中部・近畿)", "c4_tbl2", "c4_p2"), _fr("表の枠(中国〜沖縄)", "c4_tbl3", "c4_p3"), _fr("地図の枠(47都道府県まとめ)", "c5_map", "c5_sum"),
    _val("札「30回」", "c1_t36", 0.35), _val("札「中央値 67回」", "c1_med", 0.3), _val("札「最悪 54回」", "c1_worst", 0.3), _val("札「最良 79回」", "c1_best", 0.3),
    _val("札「東京 中央値 67回」", "c1_ans", 0.3), _val("札「秋田 2回」", "c2_ans", 0.3), _val("札「中央値 4回」", "c2_akmed", 0.3),
    _val("札「92人」", "c2_zero", 0.2), _val("札「東京 中央値 2年」", "c3_ans", 0.3), _val("札「秋田 中央値 33年」", "c3_ak", 0.3),
    _val("札「9,319人」", "c3_9370", 0.3), _val("札「約18倍」", "c4_x18", 0.3),
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
    ok |= set(float(x) for x in range(0, 61))                      # 問いの番号・目盛り・月・年齢
    ok |= {200.0}                                                  # 「人型1つ＝200人」（統括の指示 2026-11-11）
    for r_ in TOWN.values():                                       # 26町の表・数字（試算の値）
        ok |= {float(r_[k]) for k in ("worst", "med", "best", "stk_med", "seen")}
    ok |= {float(T_AKI["zero"]), float(T_AKI["s20"]), float(TOWN["石川"]["s20"]), float(T_TOK["s20"])}
    return ok


# ============================================================
# 絵の部品と札・文字の重なりの点検（overlap_parts.md）
# ============================================================
# 意図した重ね: (部品の種類, 札・文字の正規表現, 理由)
OVERLAP_OK = [("lot", r"^(くじ|×)$", "くじの箱の前面の「くじ」の紙と、引いた札の×は箱そのものの一部（2026-11-13 統括: くじ引きの箱だと一目で分かるように）")]   # (部品の kind, 札・文字の正規表現, 理由)
_MASKS = {}


def _person_mask(w, h):
    k = (int(round(w)), int(round(h)))
    if k not in _MASKS:
        al = np.array(_PERSON_IM.resize(k, Image.LANCZOS))[..., 3]
        _MASKS[k] = al > 20
    return _MASKS[k]


def _rect_inter(a, b):
    w_ = min(a[2], b[2]) - max(a[0], b[0])
    h_ = min(a[3], b[3]) - max(a[1], b[1])
    return (w_ * h_) if (w_ > 0 and h_ > 0) else 0.0


def _hit(card, part):
    """札・文字の四角 card=(x0,y0,x1,y1) と部品の重なり（画素数。0 なら重ならない）"""
    k = part["kind"]
    if "circle" in part:
        cx, cy, r = part["circle"]
        nx, ny = min(max(cx, card[0]), card[2]), min(max(cy, card[1]), card[3])
        if (nx - cx) ** 2 + (ny - cy) ** 2 < r * r:
            return max(1.0, _rect_inter(card, (cx - r, cy - r, cx + r, cy + r)))
        return 0.0
    rx = part["rect"]
    if k == "person":
        x0, y0 = int(round(rx[0])), int(round(rx[1]))
        m = _person_mask(rx[2] - rx[0], rx[3] - rx[1])
        h_, w_ = m.shape
        ax0, ay0 = max(int(card[0]), x0), max(int(card[1]), y0)
        ax1, ay1 = min(int(card[2]), x0 + w_), min(int(card[3]), y0 + h_)
        if ax1 <= ax0 or ay1 <= ay0:
            return 0.0
        return float(m[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0].sum())
    if k == "window":
        return max(0.0, _rect_inter(card, rx) - _rect_inter(card, part["inner"]))
    return _rect_inter(card, rx)


def _scene_at(t):
    return next((nm for nm, t0, t1, *_r in SCENES if t0 <= t < t1), "区切り")


def parts_check(step=0.25, scale=0.25):
    """全コマで、札・文字の四角と絵の部品（人型・太陽・窓・地図の印・くじの箱・棒）の重なりを調べる。字幕の箱が画面からはみ出さないかも。
    戻り値 (意図しない重なり一覧, 意図した重なり一覧, 字幕のはみ出し一覧)。out/hatsuhinode-long/overlap_parts.md に書く"""
    global PARTS
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    saved = core._LOG, core._CUR_T, PARTS
    groups, subs = {}, []
    try:
        for i in range(int(DUR / step) + 1):
            t = i * step
            if T_ES <= t < T_ES + 0.6:
                continue
            core._LOG = []
            core._CUR_T = t
            PARTS = []
            ctx = cairo.Context(surf)
            ctx.scale(scale, scale)
            draw(ctx, t, sub=False)
            cards = []
            for e in core._LOG:
                cards.append((e[1], (e[2] / scale + 2, e[3] / scale + 2, e[4] / scale - 2, e[5] / scale - 2)))
            parts = []
            for p_ in PARTS:
                q = dict(p_)
                if "rect" in q:
                    q["rect"] = tuple(v / scale for v in q["rect"])
                if "inner" in q and q["inner"]:
                    q["inner"] = tuple(v / scale for v in q["inner"])
                if "circle" in q:
                    q["circle"] = tuple(v / scale for v in q["circle"])
                if q["kind"] == "panel":
                    cards.append((q["label"], (q["rect"][0] + 2, q["rect"][1] + 2, q["rect"][2] - 2, q["rect"][3] - 2)))
                else:
                    parts.append(q)
            ents = subtitle_boxes_pill(t)
            for lab, bx in ents:
                cards.append((lab, bx))
                if bx[0] < 0 or bx[2] > lf.W or bx[1] < 0 or bx[3] > lf.H:
                    subs.append((t, lab, bx))
            for lab, bx in cards:
                for p_ in parts:
                    n = _hit(bx, p_)
                    if n > 0:
                        key = (_scene_at(t), lab, p_["kind"], p_["label"])
                        g = groups.setdefault(key, [t, t, 0.0, 0])
                        g[1] = t
                        g[2] = max(g[2], n)
                        g[3] += 1
    finally:
        core._LOG, core._CUR_T, PARTS = saved
    bad, ok = [], []
    for (sc, lab, kind, plab), (t0, t1, n, cnt) in sorted(groups.items(), key=lambda kv: kv[1][0]):
        reason = next((r_ for k_, pat, r_ in OVERLAP_OK if k_ == kind and _re.search(pat, lab)), None)
        row = (sc, t0, t1, lab, plab, int(n), reason)
        (ok if reason else bad).append(row)
    md = ["# 絵の部品と札・文字の重なり（全コマ・0.25秒ごと）", "",
          "部品: 人型（透明でない画素）・太陽（円）・窓（枠の木の部分）・県庁所在地の点と赤丸（円）・くじの箱・グラフの棒。札（板）・図の文字・字幕の箱と比べる。", "",
          f"- 意図しない重なり: **{len(bad)} 件**", f"- 意図した重なり: {len(ok)} 件", f"- 字幕の箱が画面からはみ出す: {len(subs)} 件", "",
          "## 意図しない重なり", "", "| 場面 | 時刻 | 札・文字 | 部品 | 重なった画素数 |", "|---|---|---|---|---|"]
    for sc, t0, t1, lab, plab, n, _r in bad:
        md.append(f"| {sc} | {_ts(t0)}〜{_ts(t1)} | {lab[:30]} | {plab} | {n} |")
    md += ["", "## 意図した重なり（許可リスト）", "", "| 場面 | 時刻 | 札・文字 | 部品 | 重なった画素数 | 理由 |", "|---|---|---|---|---|---|"]
    for sc, t0, t1, lab, plab, n, r_ in ok:
        md.append(f"| {sc} | {_ts(t0)}〜{_ts(t1)} | {lab[:30]} | {plab} | {n} | {r_} |")
    md += ["", "## 字幕の箱のはみ出し", ""] + [f"- {_ts(t)} {lab[:40]} {tuple(int(v) for v in bx)}" for t, lab, bx in subs]
    (OUT / "overlap_parts.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return bad, ok, subs


def subtitle_boxes_pill(t):
    """字幕の板（文字＋左右36px・上下12px）。画面からはみ出さないかの点検にも使う"""
    s_, a_ = tl.subtitle_at(t)
    out = []
    if s_ and a_ > 0.3:
        lines = lf.wrap_subtitle(s_)
        n = len(lines)
        wmax = max(text_width(l_, lf.SUB_SIZE) for l_ in lines)
        top = lf.SUB_Y - (n * lf.SUB_LINE_H + 24) / 2
        out.append(("字幕: " + lines[0], (lf.W / 2 - wmax / 2 - 36, top, lf.W / 2 + wmax / 2 + 36, top + n * lf.SUB_LINE_H + 24)))
    return out


def overlap_stills(bad, d=OUT / "overlap_960"):
    """引っかかった図と、引っかかりやすい図（人型・太陽・窓・地図・くじの箱・棒のある場面）の静止画を 960px で1枚ずつ"""
    d.mkdir(parents=True, exist_ok=True)
    for p_ in d.glob("*.png"):
        p_.unlink()
    todo = [(f"NG_{k:02d}_{sc}", t0) for k, (sc, t0, *_r) in enumerate(bad)]
    for nm_, t0_, t1_, *_r in SCENES:
        if nm_ == "end":
            continue
        todo.append((f"{nm_}_a", t0_ + (t1_ - t0_) * 0.45))
        todo.append((f"{nm_}_b", t1_ - 0.5))
    tmp = WORK / "ov_tmp.png"
    for nm, t in todo:
        lf.still(draw, t, tmp)
        Image.open(tmp).convert("RGB").resize((960, 540), Image.LANCZOS).save(d / f"{nm}.png")
    print(f"重なり点検の静止画（960px）: {len(todo)} 枚 → {d}")


def scene_checks(frames=None):
    txt = lambda k: split_reading(tl.clip(ID[k]).text)[0]
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本 ----
    A(f"台本: 章は{len(CHAPS)}つ（0〜{LAST_CH}）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる",
      len(CHAPS) == 6 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕（ ）が1つも混ざらない・読みの補正は空（台本の {表記|よみ} を使う）",
      not any(any(ch_ in v[1] for ch_ in "〔〕（）") for v in LINES.values()) and not READ_FIX)
    A("台本: 「守った決まり」「概要欄に書く前提」は声にしない", not any(("前提" in v[1] and v[0] == 5) for v in LINES.values()))
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
    last2 = [i for i in LINES if LINES[i][0] == 2][-1]
    A(f"区切り: 問い2（第2章）のあと・問い3（第3章）の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(last2) - 1e-6 and abs(T_RS1 - S("ch3")) < 1e-6 and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    pos = (T_RS0 + T_RS1) / 2 / DUR
    A(f"区切り: 動画の {pos:.1%} のところ（30〜75%）・声の行なし", 0.30 <= pos <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 亀は左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ歩く・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    # ---- 冒頭・数字 ----
    nums0 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and it.id.startswith("c0_") and S(it.id) < S(ID["c0_cond"]):
            nums0 |= set(_re.findall(r"\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭（「条件をそろえます」の前）の声の数字は「36」「32」「2」だけ（{sorted(nums0)}）", nums0 == {"36", "32", "2"})
    print(f"  参考: 「条件をそろえます」は {S(ID['c0_cond']):.1f}秒（偽の声）")
    exp = [("c0_32", f"{T_MAE['seen']}回"), ("c0_2", f"{T_AKI['seen']}回"), ("c1_t36", f"{T_TOK['seen']}回"), ("c1_med", f"{T_TOK['med']}回"),
           ("c1_worst", f"{T_TOK['worst']}回"), ("c1_best", f"{T_TOK['best']}回"), ("c1_ans", f"{T_TOK['med']}回"), ("c1_8", f"約{ihalf(10 * T_TOK['med'] / N_LIFE)}割"),
           ("c2_sap", f"{TOWN['北海道']['seen']}回"), ("c2_kan", f"{TOWN['石川']['seen']}回"), ("c2_akmed", f"{T_AKI['med']}回"),
           ("c2_akworst", f"{T_AKI['worst']}回"), ("c2_akbest", f"{T_AKI['best']}回"), ("c2_zero", f"{T_AKI['zero']}人"), ("c3_ans", f"{T_TOK['stk_med']}年"),
           ("c3_ak", f"{T_AKI['stk_med']}年"), ("c3_age", f"{T_AKI['stk_med']}歳"), ("c3_9370", f"{T_AKI['s20']:,}人"), ("c3_kan", f"{TOWN['石川']['s20']:,}人"),
           ("c3_tok", f"{T_TOK['s20']}人"), ("c4_mae", f"{T_MAE['seen']}回"), ("c4_71", f"{T_MAE['med']}回"), ("c4_mbest", f"{T_MAE['best']}回"),
           ("c4_tok", f"{TOWN['東京']['med']}回"), ("c4_mid", f"{MID47}回"), ("c4_sap", f"{TOWN['北海道']['med']}回"), ("c4_aki", f"{T_AKI['med']}回"),
           ("c4_x18", f"約{RATIO18}倍"), ("c5_sum", f"中央値{T_AKI['med']}回から{T_MAE['med']}回")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が試算（an6.py の計算・numbers.md と一致を確認済み）の値と同じ: 食い違い {bad_}", not bad_)
    A(f"試算: numbers.md の 47 県×8項目が計算と一致（起動時に assert 済み）・東京 中央値{T_TOK['med']}・秋田 中央値{T_AKI['med']}・群馬＝高知 中央値{T_MAE['med']}・47県の中央値{MID47}・約{RATIO18}倍",
      len(_NM) == 47 and (T_TOK["med"], T_AKI["med"], T_MAE["med"], RATIO18, MID47) == (67, 4, 71, 18, 44))
    A(f"試算: 秋田の見えた年は {AKITA_YEARS}・東京の見えた年は {T_TOK['seen']}/{T_TOK['n']}・秋田 一生0回 {T_AKI['zero']}人・20年以上 {T_AKI['s20']:,}人",
      AKITA_YEARS == [2011, 2017] and (T_TOK["seen"], T_TOK["n"], T_AKI["zero"], T_AKI["s20"]) == (30, 36, 92, 9319))
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
    splits = []
    for lid in LINES:
        ls_ = lf.wrap_subtitle(tl.clip(lid).text)
        if len(ls_) > 2:
            splits.append((lid, "3行"))
        for a_, b_ in zip(ls_, ls_[1:]):
            if (a_[-1].isdigit() or a_[-1] in ",.") and (b_[0].isdigit() or b_[0] in ",."):
                splits.append((lid, a_[-4:] + "／" + b_[:4]))
    A(f"字幕: 2行以内・数字の途中で行を折らない: {splits[:4]}", not splits)
    tb = tail_check()
    A(f"文末切れ: 声の最後の0.15秒が無音に落ちていない文 {len(tb)} 件 {tb[:4]}", not tb)
    if frames is not None:
        sp_ = still_spans()
        long_ = [f"{_ts(a_)}〜{_ts(b_)}（{b_ - a_:.1f}秒）" for a_, b_ in sp_ if b_ - a_ > STILL_MAX + 1e-6]
        print("  同じ絵の長い区間: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:6]))
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
        f0 = next(f for f in frames if abs(f[0]) < 1e-6)
        qs = [e for e in f0[1] if e[0] in (Q1, Q2)]
        A(f"冒頭: 0.0秒の画面に問い「{Q1}{Q2}」が出ている（{[round(e[5]) for e in qs]}px・90px 以上）", len(qs) == 2 and all(e[5] >= 90 for e in qs))
        A(f"冒頭: 声は0.5秒から「あなた」（{S('c0_0'):.1f}秒）・最初の文は5秒以内に終わる（{E('c0_0'):.1f}秒）",
          txt("c0_q").startswith("あなた") and ID["c0_q"] == "c0_0" and E("c0_0") < 5.0)
        tokens = [("30回", "c1_t36"), ("中央値 67回", "c1_med"), ("最悪 54回", "c1_worst"), ("最良 79回", "c1_best"), ("東京 中央値 67回", "c1_ans"), ("約8割", "c1_8"),
                  ("秋田 2回", "c2_ans"), ("10回", "c2_sap"), ("7回", "c2_kan"), ("中央値 4回", "c2_akmed"), ("最悪 0回", "c2_akworst"), ("最良 13回", "c2_akbest"),
                  ("92人", "c2_zero"), ("東京 中央値 2年 /1万人", "c3_ans"), ("秋田 中央値 33年 /1万人", "c3_ak"), ("9,319人", "c3_9370"), ("1,607人", "c3_kan"),
                  ("0人", "c3_tok"), ("32回", "c4_mae"), ("中央値 71回", "c4_71"), ("東京 67回", "c4_tok"), ("中央値 44回", "c4_mid"), ("北海道 22回", "c4_sap"),
                  ("秋田 4回", "c4_aki"), ("約18倍", "c4_x18"), ("中央値 4回〜71回", "c5_sum")]
        for tok, key in tokens:
            n_ = LINES[ID[key]][0]
            fr_ch = [f for f in frames if S(f"ch{n_}") <= f[0]]
            ft = first_seen(fr_ch, lambda s_, e, tok=tok: s_ == tok)
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        # 答えの前に、答えの向き（何回・何年）を出さない
        for n_, key, toks in ((1, "c1_med", ("67回", "54回", "79回")), (2, "c2_ans", ("秋田 2回",)), (3, "c3_ans", ("2年", "33年", "9,319")),
                              (4, "c4_x18", ("約18倍",))):
            early = sorted({e[0] for t_, e in allt if S(f"ch{n_}") <= t_ < S(ID[key]) - 0.3 and any(tk in e[0] for tk in toks)})
            A(f"答えの前（問い{n_}の {_ts(S(ID[key]))} より前）に、答えの数の札を出さない: {early}", not early)
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
        bad_words = sorted({e[0] for t_, e in allt if not e[0].startswith("字幕: ") and any(w in e[0] for w in ("襲", "血", "殺", "倒れ", "死"))})
        A(f"画面の札・図に「襲」「血」「殺」「倒れ」「死」の文字を出さない（字幕は台本のまま）: {bad_words}", not bad_words)
        _cl = _check_long_mod()
        short_t = _cl.short_texts(frames) if _cl else []
        for a_, b_, s_, need_ in short_t[:16]:
            print(f"  札の表示時間 {_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒／要 {need_:.1f}秒 「{s_[:30]}」")
        A(f"札の表示時間: 画面の文字は「文字数÷8＋1秒」以上出る（字幕・カウンターは除く）: 足りない {len(short_t)} 件", not short_t)
        units = sorted({e[0] for t_, e in allt if e[0] in ("/1万人", "/36回の元日")})
        A(f"分母の札（/1万人・/36回の元日）が出る: {units}", units == ["/1万人", "/36回の元日"])
        akt = sorted({(round(t_, 1)) for t_, e in allt if e[0] == "目安"})
        A("秋田の数字の札に小さく「目安」が出る（秋田の1万人・問い4の秋田）", bool(akt))
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、区切りの文字だけ: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        tes = T_ES + 0.6
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        A(f"終了画面: 最後の文のあと（{T_ES:.1f}秒〜）から最後まで（{DUR - T_ES:.1f}秒・6〜8秒）", 6.0 <= DUR - T_ES <= 8.0 and T_ES > Ek(LAST_KEY) - 1e-6)
        end_t = min(DUR - 0.2, T_ES + 2.0)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A("終了画面に 答え3つ・登録の札が出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
    if frames is not None:
        bad_p, ok_p, subs_p = parts_check()
        for sc, t0, t1, lab, plab, n, _r in bad_p[:12]:
            print(f"  部品の重なり {sc} {_ts(t0)}〜{_ts(t1)} 「{lab[:20]}」×{plab} {n}画素")
        A(f"絵の部品と札・文字の重なり: 意図しない重なり {len(bad_p)} 件（意図した重ね {len(ok_p)} 件は overlap_parts.md に理由つき）", not bad_p)
        A(f"字幕の箱が画面（x 0〜1920・y 〜1080）からはみ出さない: {len(subs_p)} 件", not subs_p)
        if "--no-ovstills" not in sys.argv:
            overlap_stills(bad_p)
    flat_ = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat_)
    print(f"場面の照合 {len(flat_)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat_)


def contrast_audit_run(min_ratio=4.5):
    """文字と、そのすぐ後ろの色のコントラスト（sims/contrast_audit.py の測り方。mp4 を使わず draw から直接描く）。out/hatsuhinode-long/contrast_audit.md"""
    import importlib.util
    if not (Path(__file__).resolve().parent / "contrast_audit.py").exists():
        print("  （sims/contrast_audit.py が無いので、コントラストの点検は飛ばします）")
        return
    spec = importlib.util.spec_from_file_location("contrast_audit", Path(__file__).resolve().parent / "contrast_audit.py")
    ca = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ca)
    frames = pickle.loads(((WORK / "frames.pkl") if FAKE else (OUT / "frames_real.pkl")).read_bytes())
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


def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if "--motion" in args:
        sp_ = still_spans()
        print("同じ絵の長い区間: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:14]))
        return
    if not any(a in args for a in ("--anchors", "--readings", "--scenecheck", "--stills", "--sheet", "--voicemd", "--contrast", "--docs", "--render")):
        print(__doc__)
        return
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    print(f"  区切り {_ts(T_RS0)}〜{_ts(T_RS1)}（{(T_RS0 + T_RS1) / 2 / DUR:.1%}）・終了画面 {_ts(T_ES)}〜")
    if "--anchors" in args:
        for k_ in ID:
            print(k_, ID[k_], f"{Sk(k_):.1f}-{Ek(k_):.1f}")
        for nm_, t0_, t1_, *_r in SCENES:
            print(f"場面 {nm_}: {t0_:.1f}-{t1_:.1f}（{t1_ - t0_:.1f}秒）")
        return
    if "--readings" in args:
        write_readings((WORK if FAKE else OUT) / "readings.log")
        return
    if "--scenecheck" in args:
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
            stills_sheet(OUT / "stills", still_list(), cols=3, sheet_name="stills_key_480.png")
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
    if "--docs" in args:
        d = WORK if FAKE else OUT
        write_transcript(d / "transcript.long.txt")
        write_readings(d / "readings.log")
        (d / "chapters.txt").write_text(tl.chapter_text() + "\n", encoding="utf-8")
        print("チャプター:", d / "chapters.txt")
        return
    if "--render" in args:
        if FAKE:
            raise SystemExit("--fake-voice では書き出さない")
        frames = lk.scan_frames(draw, DUR, timeline=tl)
        (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))
        scene_checks(frames)
        lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
        write_transcript(OUT / "transcript.long.txt")
        write_readings(OUT / "readings.log")
        print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
