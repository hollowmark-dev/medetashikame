"""コウテイペンギンの一生ロング「もしあなたがコウテイペンギンのヒナに生まれたら、何年生きられる？」（横型ロング）— 2026-11-09 作成。
場面（描画・声の並び・照合・静止画）。作り・道具・点検は sims/tsubame-long.py と同じ。

  python -X utf8 sims/penguin-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/penguin-long.py --fake-voice --stills         要所の静止画と 480px の一覧（out/penguin-long/stills/・stills_key_480.png）
  python -X utf8 sims/penguin-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/penguin-long/scene_work/）
  python -X utf8 sims/penguin-long.py --fake-voice --sheet          本編の全場面の静止画一覧（out/penguin-long/body_stills_480*.png）
  python -X utf8 sims/penguin-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/penguin-long.py --scenecheck                  本番の声で照合（frames_real.pkl を保存）
  python -X utf8 sims/penguin-long.py --figcheck                    字幕の帯とペンギンの足もとのかぶりを全コマで数える
  python -X utf8 sims/penguin-long.py --contrast                    文字と後ろの色のコントラスト（--scenecheck のあと）
  python -X utf8 sims/penguin-long.py --readings                    声の読み（readings.log）
  python -X utf8 sims/penguin-long.py --docs                        文字起こし・読み・チャプター（transcript.long.txt・readings.log・chapters.txt）
  python -X utf8 sims/penguin-long.py --makemap                     南極まわりの地図の形（Natural Earth）→ sims/penguin_map_data.py

台本: publish/penguin-long/narration_B.md（文は変えない）。数字: sims/penguin_rough.py を同じ乱数の種（20261109）で回した値（手で書き写さない）。
絵: sims/penguin_art.py（平塗り・輪郭線なし）。ここでは読んで使うだけ。足りない部品はこのファイルの中に書く。
地図は Natural Earth の実データ（南極点を中心にした正距方位図法）。
本番の mp4 の書き出しはここでは行わない（--scenecheck と --stills・--sheet まで。書き出しは --render をつけたときだけ）。
"""

import json
import math
import random
import re as _re
import sys
from dataclasses import dataclass
from pathlib import Path

SLUG = "penguin-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
SRC_WORLD = ROOT.parent / "kaisetsu_movie" / "long" / "shuhasu" / "map" / "world.json"
MAP_LON0 = 140.0          # 画面の上（北）に向ける経度（ポワント・ジェオロジーの群れ 東経140度）
MAP_RMAX = 62.0           # 南極点からの角度（度）。62度＝南緯28度まで


def polar_xy(lon, lat, lon0=MAP_LON0):
    """南極点を中心にした正距方位図法（度の単位）。上が lon0、右が東"""
    r = 90.0 + lat
    a = math.radians(lon - lon0)
    return (r * math.sin(a), -r * math.cos(a))


def make_map():
    """sims/penguin_map_data.py を作る（world.json は読むだけ）"""
    world = json.load(open(SRC_WORLD, encoding="utf-8"))

    def polys(g):
        return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]

    def simp(pts, tol):
        if len(pts) < 4:
            return pts
        keep = [False] * len(pts)
        keep[0] = keep[-1] = True
        st = [(0, len(pts) - 1)]
        while st:
            a, b = st.pop()
            ax, ay = pts[a]
            bx, by = pts[b]
            dx, dy = bx - ax, by - ay
            n = math.hypot(dx, dy) or 1e-9
            best, bi = 0.0, -1
            for i in range(a + 1, b):
                d = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / n
                if d > best:
                    best, bi = d, i
            if best > tol and bi > 0:
                keep[bi] = True
                st += [(a, bi), (bi, b)]
        return [p for p, k in zip(pts, keep) if k]

    def ring(c):
        q = [polar_xy(lon, lat) for lon, lat in c]
        m = len(q) // 2
        p = simp(q[:m + 1], 0.06)[:-1] + simp(q[m:], 0.06)
        return [(round(x, 3), round(y, 3)) for x, y in p]

    ant, land = [], []
    for code, g in world.items():
        for poly in polys(g):
            c = poly[0]
            if min(p[1] for p in c) > -90 + MAP_RMAX + 4:
                continue
            r = ring(c)
            if len(r) < 3:
                continue
            (ant if code == "ATA" else land).append(r)
    out = ['"""sims/penguin-long.py --makemap が作った地図の形（Natural Earth・パブリックドメイン）。手で編集しない。',
           f'南極点を中心にした正距方位図法。単位は度（南極点からの角度）。上＝東経{MAP_LON0:.0f}度、右＝東。"""',
           f"LON0 = {MAP_LON0}", f"RMAX = {MAP_RMAX}", f"ANT = {ant!r}", f"LAND = {land!r}"]
    p = Path(__file__).resolve().parent / "penguin_map_data.py"
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("地図の形:", p, "南極", len(ant), "ほかの陸", len(land), "点", sum(len(r) for r in ant + land))


if __name__ == "__main__" and "--makemap" in sys.argv:
    make_map()
    raise SystemExit(0)

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

from danchi_people import mix  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAKE = "--fake-voice" in sys.argv
# 場面の切りかえの前後の間（ツバメと同じ。第0章は 0.6＋0.4、ほかの章は 0.7＋0.6）
PACE_TRIAL = "--pace-old" not in sys.argv
TRIAL_LEAD = 0.7   # 場面が替わってから声まで
TRIAL_TAIL = 0.6   # 声が終わってから場面が替わるまで
TRIAL_CH = tuple(f"c{n}_" for n in range(0, 8))
TRIAL_PAIR = {"c0_": (0.6, 0.4), **{f"c{n}_": (TRIAL_LEAD, TRIAL_TAIL) for n in range(1, 8)}}
# 枠（グラフ・帯・地図）が出そろうのに時間がかかる図は 1.05秒前から出す
TRIAL_LEAD_KEY = {k_: 1.05 for k_ in (
    "c0_egg", "c0_med", "c1_map", "c1_rec", "c1_band", "c1_snow", "c1_unk", "c1_ans", "c2_base", "c2_months", "c2_years", "c2_far",
    "c2_band", "c2_sum", "c3_base", "c3_north", "c3_data", "c3_band", "c3_cmp", "c4_base", "c4_sea", "c4_4y", "c4_same", "c4_band",
    "c4_cmp", "c5_pull", "c5_ages", "c5_sort", "c5_vary", "c6_sel", "c6_avg", "c6_ending", "c6_worst0", "c6_two")}


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
from long_bgm import bgm_track as _bgm  # noqa: E402  めでたしかめのロングの標準BGM（カスミソウ）
import penguin_art as pa  # noqa: E402
import penguin_rough as pr  # noqa: E402  試算（乱数の種 20261109）。画面の数字はここから取る
from tsubame_art import _set as tset, ell  # noqa: E402

# ---- ペンギンの足もとの記録（字幕の帯とのかぶりを機械で測る）----
FIG_LOG = None
FEET_MAX = 925   # 立っているペンギン・ヒナの足もとはここより下に置かない（字幕2行の帯の上端は 934）


def _lift(ctx, x, y):
    """足もとが FEET_MAX より下なら、その分だけ上げた y を返す（体を一緒に上げるため、描く関数の入口で使う）"""
    dyv = ctx.user_to_device(x, y)[1]
    if dyv > FEET_MAX:
        y -= ctx.device_to_user_distance(0, dyv - FEET_MAX)[1]
    return y


def _log(ctx, x, y, h):
    if FIG_LOG is not None:
        dx, dy = ctx.user_to_device(x, y)
        dh = abs(ctx.user_to_device_distance(0, h)[1])
        FIG_LOG.append((dx, dy, dh))


def _logged(fn):
    def wrapped(ctx, x, y, h, *a_, **k_):
        if k_.get("pose", "stand") != "swim":
            y = _lift(ctx, x, y)
            _log(ctx, x, y, h)
        return fn(ctx, x, y, h, *a_, **k_)
    return wrapped


def _logged_group(fn):
    """群れ（huddle・creche）: 手前の足もと y を記録。幅 w の左右いっぱいを数えるよう h = w / 0.36 で記録する"""
    def wrapped(ctx, x, y, w, n, **k_):
        y = _lift(ctx, x, y)
        _log(ctx, x, y, w / 0.36)
        return fn(ctx, x, y, w, n, **k_)
    return wrapped


draw_emperor = _logged(pa.draw_emperor)
draw_emperor_front = _logged(pa.draw_emperor_front)
draw_emperor_back = _logged(pa.draw_emperor_back)
draw_emperor_chick = _logged(pa.draw_emperor_chick)
draw_father_with_egg = _logged(pa.draw_father_with_egg)
huddle = _logged_group(pa.huddle)
_creche_raw = _logged_group(pa.creche)
CHICK_AGE_MAX = 0.55      # ヒナの群れは斑の出ない年ごろで描く


class chick_age_cap:
    """この中で描くヒナ（penguin_art の群れの部品の中も）は age を CHICK_AGE_MAX 以下にする"""
    def __enter__(self):
        self._orig = pa.draw_emperor_chick

        def capped(ctx, x, y, h, facing=1, age=0.0, a=1.0):
            return self._orig(ctx, x, y, h, facing=facing, age=min(age, CHICK_AGE_MAX), a=a)
        pa.draw_emperor_chick = capped
        return self

    def __exit__(self, *exc):
        pa.draw_emperor_chick = self._orig
        return False


def creche(ctx, x, y, w, n, **k_):
    with chick_age_cap():
        return _creche_raw(ctx, x, y, w, n, **k_)

ANCH = {
    # 0 あなたは何年生きられる？
    "c0_you": (0, "コウテイペンギンの卵です"), "c0_q": (0, "何年生きられるでしょうか"), "c0_pick": (0, "一つ選んでみてください"),
    "c0_ans": (0, "いちばん最後にお見せします"), "c0_egg": (0, "1万個用意しました"), "c0_prob": (0, "記録にある確率で"),
    "c0_one": (0, "最後に、1万個の中央値"), "c0_med": (0, "ちょうど真ん中の1羽の値"),
    # 1 ふ化できる？
    "c1_q": (1, "最初の問いです"), "c1_big": (1, "いちばん大きなペンギンです"), "c1_map": (1, "約3,000つがい"),
    "c1_gather": (1, "毎年、ペンギンが集まります"), "c1_rec": (1, "何十年もかけて"), "c1_one": (1, "1つのつがいに1個だけ"),
    "c1_may": (1, "5月から6月ごろです"), "c1_female": (1, "産んだメスは"), "c1_warm": (1, "残ったオスが"), "c1_fast": (1, "何も食べません"),
    "c1_guess": (1, "どれくらいかえるでしょうか"), "c1_band": (1, "ふ化したのは8,226羽"), "c1_nohatch": (1, "1,774個です"),
    "c1_2wari": (1, "約2割にあたります"), "c1_gate": (1, "最初の関門"), "c1_snow": (1, "雪が多い年は"), "c1_unk": (1, "1個ずつは分かっていません"),
    "c1_ans": (1, "卵の約8割が"), "c1_ans2": (1, "ヒナにならないまま"),
    # 2 ヒナの冬
    "c2_q": (2, "二つ目の問いです"), "c2_base": (2, "8,226羽のヒナで数えます"), "c2_july": (2, "7月ごろにかえります"), "c2_50": (2, "最初の約50日"),
    "c2_creche": (2, "ヒナどうしで群れます"), "c2_parents": (2, "ヒナのところへ戻ります"), "c2_months": (2, "ふ化から巣立ちまで、約5か月です"),
    "c2_edge": (2, "12月の終わりに"), "c2_years": (2, "年ごとに大きく違います"), "c2_far": (2, "海氷が遠い年は"), "c2_bird": (2, "ヒナを襲う鳥の記録"),
    "c2_guess": (2, "どれくらい巣立つでしょうか"), "c2_band": (2, "巣立って海へ出たのは5,321羽"), "c2_5m": (2, "巣立つまでに、約5か月"),
    "c2_dead": (2, "2,905羽です"), "c2_ans": (2, "巣立つのは約3分の2"), "c2_winter": (2, "冬を越えて巣立てるのは"), "c2_sum": (2, "合わせて4,679個"),
    # 3 初めての海
    "c3_q": (3, "海に出たヒナは、1歳になれるでしょうか"), "c3_base": (3, "5,321羽の若い鳥で数えます"), "c3_sea": (3, "ヒナが初めて入る場所"),
    "c3_stand": (3, "氷の{縁|ふち}に立ちます"), "c3_north": (3, "北へ向かいます"), "c3_far": (3, "どんどん遠くへ"), "c3_ryu": (3, "流氷へ戻ってきます"),
    "c3_under": (3, "氷が空のように明るく"), "c3_data": (3, "数える材料は"), "c3_guess": (3, "1歳になれるのは何羽"), "c3_band": (3, "1年を越えたのは、2,088羽"),
    "c3_dead": (3, "3,233羽です"), "c3_cmp": (3, "同じ1万個の卵で比べると"), "c3_ans": (3, "答えです。海に出て最初の1年"), "c3_again": (3, "最初の問いに戻ります"),
    "c3_last": (3, "最後の章で出します"),
    # 4 誰も見ていない数年
    "c4_q": (4, "四つ目の問いです"), "c4_base": (4, "2,088羽で数えます"), "c4_sea": (4, "海の上で暮らします"), "c4_noreturn": (4, "氷には戻りません"),
    "c4_4y": (4, "誰も数えられていません"), "c4_nobody": (4, "この数年は、誰も見ていません"), "c4_same": (4, "大人と同じと置いています"),
    "c4_9": (4, "毎年約9割"), "c4_guess": (4, "何羽が残るでしょうか"), "c4_band": (4, "5歳まで生きたのは、1,368羽"), "c4_age5": (4, "初めての子育てを始める年ごろ"),
    "c4_23": (4, "約3分の2が、5歳まで"), "c4_cmp": (4, "割合で比べると"), "c4_ans": (4, "答えです。5歳まで"),
    # 5 大人になったペンギン
    "c5_q": (5, "五つ目の問いです"), "c5_first5": (5, "5歳か6歳ごろです"), "c5_pair": (5, "大人と呼びます"), "c5_pull": (5, "大人になったのは、1,081羽"),
    "c5_base": (5, "1,081羽で数えます"), "c5_ages": (5, "5歳が308羽"), "c5_7": (5, "7歳で初めて子育てをした鳥"), "c5_medage": (5, "年齢の中央値は、6歳"),
    "c5_sort": (5, "生きた日数の順に並べます"), "c5_life": (5, "約15年です"), "c5_brood": (5, "回数の中央値は、7回"), "c5_return": (5, "毎年氷の上へ戻ってきた"),
    "c5_kids": (5, "ヒナの数の中央値は"), "c5_vary": (5, "鳥によって大きく違います"), "c5_zero": (5, "99羽います"), "c5_five": (5, "507羽"),
    "c5_ten": (5, "208羽"), "c5_gap": (5, "大きく開きます"), "c5_20": (5, "20年以上生きた鳥は"), "c5_nomax": (5, "最高齢の記録は"),
    "c5_ans": (5, "答えです。大人になった鳥は"), "c5_tenth": (5, "1万羽のうち約1割"),
    # 6 中央値の1羽の一生
    "c6_q": (6, "約束した中央値の1羽"), "c6_base1": (6, "また1万個の卵に戻ります"), "c6_sel": (6, "中央値にいちばん近い卵を選びます"), "c6_avg": (6, "平均ではなく"),
    "c6_you": (6, "ここからは、あなたがその卵です"), "c6_father": (6, "父親の足の上にいます"), "c6_mother": (6, "母親は"), "c6_crack": (6, "殻に、ひびが入ります"),
    "c6_open": (6, "殻を割ると"), "c6_chick": (6, "あなたはヒナになりました"), "c6_out": (6, "初めて見る外は"), "c6_50": (6, "約50日、あなたは"),
    "c6_fast": (6, "何も食べずに立ち続けています"), "c6_creche": (6, "まわりはヒナだらけです"), "c6_feed": (6, "えさを運んできます"), "c6_huddle": (6, "体を寄せ合って"),
    "c6_dec": (6, "12月の終わり。"), "c6_dive": (6, "海へ飛びこみます"), "c6_look": (6, "水の中から見上げると"), "c6_north": (6, "北へ向かって泳ぎます"),
    "c6_turn": (6, "振り向くと"), "c6_end": (6, "ここで終わります"), "c6_8m": (6, "産卵から約8か月。冒頭"), "c6_ansopt": (6, "一つ目、1年未満です"),
    "c6_luck": (6, "特別な不運"), "c6_3233": (6, "3,233羽もいるからです"), "c6_ending": (6, "ちょうど海に出るころに一生を終えます"),
    "c6_6044": (6, "6,044羽でした"), "c6_6wari": (6, "約6割が一生を終えます"), "c6_half": (6, "半分以上は、1歳になれません"), "c6_in3233": (6, "3,233羽の中の1羽です"),
    "c6_worst0": (6, "最悪と最良も並べます"), "c6_worst": (6, "最悪は"), "c6_best": (6, "最良は"), "c6_b2": (6, "中央値の1羽にも、なってみます"),
    "c6_base2": (6, "また1,081羽に替わります"), "c6_7y": (6, "7歳で初めて子育て"), "c6_may": (6, "毎年5月から6月ごろ"), "c6_kids": (6, "7回の子育てで"),
    "c6_end2": (6, "14.4年で、あなたの一生"), "c6_cmp": (6, "14.4年は"), "c6_two": (6, "2つの一生を見ました"), "c6_both": (6, "どちらも"),
    # 7 まとめ
    "c7_half": (7, "1歳になれず"), "c7_15": (7, "約15年を生きます"), "c7_last": (7, "当たっていましたか"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の並び（名前, 始まり, 描く関数の名前）。始まり: 合図のキー＝その文の頭の前 ／ "ch:N"＝章カードのあと ／ "z:キー"＝0章 ----
SC_TABLE = [
    ("open", "zero", "sc_open"), ("c0_egg", "z:c0_egg", "sc_c0_egg"), ("c0_prob", "z:c0_prob", "sc_c0_prob"), ("c0_one", "z:c0_one", "sc_c0_one"),
    ("c0_med", "z:c0_med", "sc_c0_med"),
    ("c1_a", "ch:1", "sc_c1_a"), ("c1_big", "c1_big", "sc_c1_big"), ("c1_map", "c1_map", "sc_c1_map"), ("c1_gather", "c1_gather", "sc_c1_gather"),
    ("c1_rec", "c1_rec", "sc_c1_rec"), ("c1_lay", "c1_one", "sc_c1_lay"), ("c1_female", "c1_female", "sc_c1_female"), ("c1_fp", "c1_warm", "sc_c1_fp"),
    ("c1_guess", "c1_guess", "sc_c1_guess"), ("c1_band", "c1_band", "sc_c1_band"), ("c1_snow", "c1_snow", "sc_c1_snow"), ("c1_unk", "c1_unk", "sc_c1_unk"),
    ("c1_ans", "c1_ans", "sc_c1_ans"),
    ("c2_a", "ch:2", "sc_c2_a"), ("c2_base", "c2_base", "sc_c2_base"), ("c2_pouch", "c2_july", "sc_c2_pouch"), ("c2_creche", "c2_creche", "sc_c2_creche"),
    ("c2_parents", "c2_parents", "sc_c2_parents"), ("c2_months", "c2_months", "sc_c2_months"), ("c2_edge", "c2_edge", "sc_c2_edge"),
    ("c2_years", "c2_years", "sc_c2_years"), ("c2_far", "c2_far", "sc_c2_far"), ("c2_bird", "c2_bird", "sc_c2_bird"), ("c2_guess", "c2_guess", "sc_c2_guess"),
    ("c2_band", "c2_band", "sc_c2_band"), ("c2_ans", "c2_ans", "sc_c2_ans"), ("c2_sum", "c2_sum", "sc_c2_sum"),
    ("c3_a", "ch:3", "sc_c3_a"), ("c3_base", "c3_base", "sc_c3_base"), ("c3_edge", "c3_sea", "sc_c3_edge"), ("c3_map", "c3_north", "sc_c3_map"),
    ("c3_under", "c3_under", "sc_c3_under"), ("c3_data", "c3_data", "sc_c3_data"), ("c3_guess", "c3_guess", "sc_c3_guess"), ("c3_band", "c3_band", "sc_c3_band"),
    ("c3_bars", "c3_cmp", "sc_c3_bars"), ("c3_opts", "c3_again", "sc_c3_opts"),
    ("c4_a", "ch:4", "sc_c4_a"), ("c4_base", "c4_base", "sc_c4_base"), ("c4_map", "c4_sea", "sc_c4_map"), ("c4_colony", "c4_noreturn", "sc_c4_colony"),
    ("c4_dark", "c4_4y", "sc_c4_dark"), ("c4_same", "c4_same", "sc_c4_same"), ("c4_guess", "c4_guess", "sc_c4_guess"), ("c4_band", "c4_band", "sc_c4_band"),
    ("c4_cmp", "c4_cmp", "sc_c4_cmp"),
    ("c5_a", "ch:5", "sc_c5_a"), ("c5_pair", "c5_pair", "sc_c5_pair"), ("c5_pull", "c5_pull", "sc_c5_pull"), ("c5_first", "c5_ages", "sc_c5_first"),
    ("c5_sorted", "c5_sort", "sc_c5_sorted"), ("c5_return", "c5_return", "sc_c5_return"), ("c5_hist", "c5_vary", "sc_c5_hist"), ("c5_old", "c5_20", "sc_c5_old"),
    ("c5_ans", "c5_ans", "sc_c5_ans"),
    ("c6_a", "ch:6", "sc_c6_a"), ("c6_sel", "c6_sel", "sc_c6_sel"), ("c6_avg", "c6_avg", "sc_c6_avg"), ("c6_you", "c6_you", "sc_c6_you"),
    ("c6_crack", "c6_crack", "sc_c6_crack"), ("c6_gap", "c6_open", "sc_c6_gap"), ("c6_pouch", "c6_50", "sc_c6_pouch"), ("c6_creche", "c6_creche", "sc_c6_creche"),
    ("c6_edge", "c6_dec", "sc_c6_edge"), ("c6_under", "c6_look", "sc_c6_under"), ("c6_sea", "c6_north", "sc_c6_sea"), ("c6_answer", "c6_luck", "sc_c6_answer"),
    ("c6_band2", "c6_ending", "sc_c6_band2"), ("c6_three", "c6_worst0", "sc_c6_three"), ("c6_b2", "c6_b2", "sc_c6_b2"), ("c6_brood", "c6_7y", "sc_c6_brood"),
    ("c6_end2", "c6_end2", "sc_c6_end2"), ("c6_two", "c6_two", "sc_c6_two"),
    ("c7_answers", "ch:7", "sc_c7_answers"), ("c7_close", "c7_last", "sc_c7_close"), ("end", "end", "sc_end"),
]

# ---- 場面の切りかえの間: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {}


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
LAST_KEY = "c7_last"
T_ES = Ek(LAST_KEY) + 0.5

# ============================================================
# データ（sims/penguin_rough.py を同じ乱数の種で回した値。手で書き写さない）
# ============================================================
import statistics as _st  # noqa: E402
from collections import Counter as _Counter  # noqa: E402

_rng = random.Random(pr.SEED)
BIRDS = [pr.life(_rng) for _ in range(pr.N)]          # (生きた日数, 段階, 子育て回数, 巣立たせたヒナ, 初めての子育ての歳)
NB = pr.N
YEAR = 365.0
DAYS = sorted(b[0] for b in BIRDS)
MED_DAYS = _st.median(DAYS)
N_HATCH = sum(1 for b in BIRDS if b[1] != "卵")
N_FLEDGE = sum(1 for b in BIRDS if b[1] not in ("卵", "ヒナ"))
N_1Y = sum(1 for b in BIRDS if b[0] >= pr.D_SEA + 365)
N_5Y = sum(1 for b in BIRDS if b[0] >= pr.D_SEA + 365 * 5)
N_EGGD = NB - N_HATCH
N_CHD = N_HATCH - N_FLEDGE
N_SEAD = N_FLEDGE - N_1Y
N_PRESEA = NB - N_FLEDGE
N_NOT1 = sum(1 for b in BIRDS if b[0] < YEAR)                  # 産卵から1年（1歳）になれない
ADULTS = [b for b in BIRDS if b[2] > 0]
N_AD = len(ADULTS)
AD_LIFE = _st.median([b[0] for b in ADULTS]) / YEAR
AD_BROODS = _st.median([b[2] for b in ADULTS])
AD_KIDS = _st.median([b[3] for b in ADULTS])
FIRST_AGE = _Counter(b[4] for b in ADULTS)
FIRST_MED = _st.median([b[4] for b in ADULTS])
N_KID0 = sum(1 for b in ADULTS if b[3] == 0)
N_KID5 = sum(1 for b in ADULTS if b[3] >= 5)
N_KID10 = sum(1 for b in ADULTS if b[3] >= 10)
KID_BINS = [("0羽", 0, 0), ("1〜4羽", 1, 4), ("5〜9羽", 5, 9), ("10羽以上", 10, 10 ** 6)]
KID_COUNTS = [sum(1 for b in ADULTS if lo <= b[3] <= hi) for _l, lo, hi in KID_BINS]
N_20Y = sum(1 for b in BIRDS if b[0] / YEAR >= 20)
# 中央値の1羽（選び方は sims/penguin_rough.py と同じ）
MED1_I = min(range(NB), key=lambda k: (abs(BIRDS[k][0] - MED_DAYS), k))
MED1 = BIRDS[MED1_I]
MED1_SEA_DAYS = MED1[0] - pr.D_SEA
# 大人の中央値の1羽（penguin_rough.picks() と同じ選び方）
_ad = [(k, b) for k, b in enumerate(BIRDS) if b[2] > 0]
_cand = [(k, b) for k, b in _ad if b[2] == AD_BROODS and b[3] == AD_KIDS] or [(k, b) for k, b in _ad if b[2] == AD_BROODS]
MED2_I, MED2 = min(_cand, key=lambda kb: (abs(kb[1][0] - AD_LIFE * YEAR), kb[0]))
MED2_YEARS = MED2[0] / YEAR
AD_SORTED = sorted(ADULTS, key=lambda b: b[0])

# 帯の割合（1万個を生きた日数の順に並べたとき、左からどこまでが何か）
FE = N_EGGD / NB                      # 卵のうち
FC = (N_EGGD + N_CHD) / NB            # ヒナのうち まで
FS = (NB - N_1Y) / NB                 # 海に出て1年以内 まで
F5 = (NB - N_5Y) / NB                 # 5歳になる前 まで
FN1 = N_NOT1 / NB                     # 1歳になれず
FA = N_AD / NB                        # 大人になった（右端から）

# ============================================================
# 見た目（共通の道具: tsubame-long.py と同じ札・線・場面の仕組み）
# ============================================================
W_, H_ = lf.W, lf.H
WHITE, YEL, PALE, REDC = "#ffffff", "#ffe14a", "#d6e2f5", "#e8505b"
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
CARD_BY_N = {1: ["問い1", "ふ化できる？"], 2: ["問い2", "ヒナの冬"], 3: ["問い3", "初めての海"], 4: ["問い4", "誰も見ていない数年"],
             5: ["問い5", "大人になったペンギン"], 6: ["最後に", "中央値の1羽の一生"], 7: ["まとめ"]}
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
            rr = [(s_, 76, YEL if (s_.startswith("問い") or s_ in ("まとめ", "最後に")) else WHITE) for s_ in rows]
            sc = 0.92 + 0.08 * ease_out(clamp01(age / 0.35))      # 入りだけ大きくなる（消えるときは縮めない）
            ctx.save()
            ctx.translate(960, 440)
            ctx.scale(sc, sc)
            panel(ctx, rr, 0, 0, a=a, pad=(60, 34), border=YEL)
            ctx.restore()


def ch_start(n):
    return S(f"ch{n}")


# ============================================================
# 絵の道具（penguin_art.py の部品を、動きと札に合わせて並べる）
# ============================================================
SUB_Y = 936           # 字幕の帯の上端（札・図の文字はこの下に置かない）
CARDC = "#d4e3f0"     # グラフ・帯・地図を載せる無地のカード（背景の絵に直接のせない）
DARKTXT = "#1f2d44"
UNITC = "#41567c"
GOLD = "#f3b72e"
C_E, C_C, C_S, C_L, C_A = "#c9772a", "#7a55b0", "#2a8a86", "#3d8f57", "#3b6fb0"
STAGE_TXT = {C_E: "#7a4410", C_C: "#4d2f80", C_S: "#1b5e5b", C_L: "#285e3a"}


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


def bob(t, a=3.0, w=1.9, ph=0.0):
    return math.sin(t * w + ph) * a


def whiten(ctx, a, col="#ffffff"):
    if a > 0.003:
        rect(ctx, col, 0, 0, W_, H_, a)


def snowfall(ctx, t, a=0.55, n=150, seed=8):
    """ゆっくり降る雪（グラフの後ろの夜の空に）。10秒に1回は画面が動くように"""
    rnd = random.Random(seed)
    for i in range(n):
        x0, y0 = rnd.uniform(0, W_), rnd.uniform(0, H_ + 40)
        sp = rnd.uniform(35, 80)
        r = rnd.uniform(3.0, 7.0)
        x = (x0 + 14 * t + 22 * math.sin(t * 0.6 + i)) % W_
        y = (y0 + sp * t) % (H_ + 40) - 20
        disc(ctx, x, y, r, "#ffffff", a * rnd.uniform(0.45, 1.0))


def chart_bg(ctx, t):
    """グラフ・帯・地図の場面の後ろ: 南極の夜の空と、ゆっくり降る雪（カードの外だけに見える）"""
    ctx.set_source(lin(0, 0, 0, H_, [(0, "#16294a", 1), (0.7, "#25426b", 1), (1, "#3a5a82", 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    snowfall(ctx, t)


def chart_card(ctx, x0, y0, x1, y1, col=None, a=1.0):
    """グラフ・表・絵を載せる無地のカード（背景の絵に直接のせない）"""
    tset(ctx, col or CARDC, a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 26)
    ctx.fill()


def tx(ctx, s, x, y, size, col=DARKTXT, align="center", a=1.0):
    """カードの上に直に置く文字（core.text のログに残る）"""
    if a > 0.003:
        text(ctx, s, x, y, size, col, align=align, alpha=a)


def unit_tag(ctx, s, x, y, a=1.0):
    tx(ctx, s, x, y, 44, UNITC, a=a)


def light_snow(ctx, t, a=0.55, seed=3):
    pa.blizzard(ctx, t, a=a, n=150, seed=seed, speed=0.45, size=0.8, veil=0.0)


def ice_bg(ctx, t, hor=560, snow=0.55):
    """南極の氷原（夕方の低い空）"""
    pa.sky(ctx, 0, hor + 40)
    pa.ice_shelf(ctx, hor, H_)
    light_snow(ctx, t, snow)


def walker(ctx, t, x, y, h, facing=1, ph=0.0, a=1.0):
    """歩くペンギン（足を交互に・小さく上下）"""
    pose = "walk" if int(t * 3.2 + ph) % 2 else "stand"
    draw_emperor(ctx, x, y - abs(math.sin(t * 10 + ph)) * h * 0.012, h, facing=facing, pose=pose, a=a)


def parent_with_chick(ctx, x, y, h, facing=1, t=0.0):
    """足もとにヒナを連れた親（横向き）。2026-11-10 大人を画像に替えたので、白い垂れの手描きはやめ、ヒナを親のおなかの前・足もとに置く"""
    y = _lift(ctx, x, y)
    draw_emperor(ctx, x, y, h, facing=facing)
    s = h / 100.0
    pa.draw_emperor_chick(ctx, x + facing * 9 * s, y - 5 * s, 19 * s, facing=facing, age=0.0)   # ふ化したてを足の上（おなかの下）に


def edge_scene(ctx, t, n=4, age=1.0):
    """氷の縁と、その先の海（横から）。縁の近くにヒナが立つ"""
    pa.sky(ctx, 0, 480)
    pa.sea(ctx, 470, H_, t=t)
    for k in range(3):                         # 遠くの流氷のかけら
        fx = (300 + 520 * k + 10 * t) % (W_ + 200) - 100
        tset(ctx, "#b7d2e4", 0.9)
        ell(ctx, fx + 900, 520 + 30 * k, 90 - 20 * k, 10)
        ctx.fill()
    ice_tongue(ctx, 64, "#8fb3cc")          # 氷の厚み（下にずらした影の形）
    ice_tongue(ctx, 0, None)                 # 氷の上面
    xs = [620, 760, 880, 980][:n]
    for k, x in enumerate(xs):
        draw_emperor_chick(ctx, x, 700 + 8 * (k % 2) + bob(t, 1.5, 1.7, k), 190 + 12 * (k % 2), facing=1, age=age)
    light_snow(ctx, t, 0.4)


# 氷の上面の縁（右へ張り出し、縁は不ぞろい・角は丸い）。(x, y) の点を曲線でつなぐ
ICE_RIM = [(-20, 652), (300, 636), (560, 648), (760, 632), (930, 646), (1040, 638), (1110, 664), (1150, 702), (1132, 748),
           (1168, 800), (1140, 860), (1176, 930), (1150, 1000), (1170, H_ + 20)]


def ice_tongue(ctx, dy, col):
    """横から見た氷の張り出し。dy で下にずらすと厚み（側面）になる"""
    pts = [(x - (14 if dy else 0), y + dy) for x, y in ICE_RIM]
    ctx.move_to(-20, H_ + 20)
    ctx.line_to(*pts[0])
    for i in range(1, len(pts)):
        x0, y0 = pts[i - 1]
        x1, y1 = pts[i]
        ctx.curve_to(x0 + (x1 - x0) * 0.5, y0, x1 - (x1 - x0) * 0.2, y1 - (y1 - y0) * 0.5, x1, y1)
    ctx.close_path()
    if col:
        tset(ctx, col)
    else:
        ctx.set_source(lin(0, 630, 0, H_, [(0, pa.ICE_L, 1), (0.5, "#e3eef6", 1), (1, "#cfe0ec", 1)]))
    ctx.fill()
    if not col:                                # 縁のすぐ内側に、うすい青の段（1段だけ）
        tset(ctx, "#c3d8e8", 0.55)
        ctx.set_line_width(10)
        ctx.move_to(*pts[5])
        for i in range(6, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            ctx.curve_to(x0 + (x1 - x0) * 0.5 - 18, y0, x1 - (x1 - x0) * 0.2 - 18, y1 - (y1 - y0) * 0.5, x1 - 18, y1)
        ctx.stroke()


FLOES = [(260, 520, 150), (760, 600, 230), (1320, 540, 170), (1700, 690, 260), (520, 800, 300), (1150, 860, 280)]


def floe_scene(ctx, t, dark=0.0):
    """海の上の流氷（遠くまで）"""
    pa.sky(ctx, 0, 430)
    pa.sea(ctx, 420, H_, t=t)
    for k, (x, y, w) in enumerate(FLOES):
        xx = (x + 9 * t * (1 + 0.2 * k)) % (W_ + 400) - 200
        yy = y + bob(t, 3, 0.7, k)
        tset(ctx, "#8fb4cf", 0.95)
        ell(ctx, xx, yy + 8, w * 0.5, w * 0.09)
        ctx.fill()
        tset(ctx, "#eef5fa")
        ell(ctx, xx, yy, w * 0.5, w * 0.08)
        ctx.fill()
    light_snow(ctx, t, 0.35)
    whiten(ctx, dark, "#0a1426")


def blurred(ctx, fn, k=40):
    """fn(ctx) を 1/k に縮めて描き、なめらかに引きのばす（輪郭が分からないくらいの強いぼかし）"""
    w, h = int(W_ / k) + 2, int(H_ / k) + 2
    small = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c2 = cairo.Context(small)
    c2.scale(1.0 / k, 1.0 / k)
    saved = core._LOG
    core._LOG = None
    try:
        fn(c2)
    finally:
        core._LOG = saved
    ctx.save()
    ctx.scale(k, k)
    ctx.set_source_surface(small, 0, 0)
    pat = ctx.get_source()
    pat.set_filter(cairo.FILTER_BILINEAR)
    pat.set_extend(cairo.EXTEND_PAD)
    ctx.paint()
    ctx.restore()


def fp_shell_view(ctx, t, extra=None, cream=0.52):
    """一人称: 殻の内側。殻ごしなので外（羽毛のカーテン・父親の足・吹雪）は輪郭が分からないほどぼけ、光と影の気配だけが透ける"""
    def outside(c):
        pa.fp_from_pouch(c, t)
        if extra:
            c.save()
            c.rectangle(420, 400, 1080, 330)
            c.clip()
            extra(c)
            c.restore()
    blurred(ctx, outside)
    whiten(ctx, cream, "#f2e7c9")                    # 殻の膜（明るいクリーム色）
    rnd = random.Random(12)                          # 殻ごしに透ける、吹雪のぼんやりした影（斜めに流れる）
    for i in range(22):
        x0, y0 = rnd.uniform(0, W_ + 600), rnd.uniform(-200, H_ + 200)
        sp = rnd.uniform(380, 700)
        x = (x0 - 0.93 * sp * t) % (W_ + 600) - 300
        y = (y0 + 0.37 * sp * t) % (H_ + 400) - 200
        r = rnd.uniform(60, 130)
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, 0.45, 0.40, 0.33, 0.16)
        g.add_color_stop_rgba(1, 0.45, 0.40, 0.33, 0.0)
        ctx.set_source(g)
        ctx.rectangle(x - r, y - r, 2 * r, 2 * r)
        ctx.fill()
    g = cairo.RadialGradient(960, 470, 40, 960, 470, 620)    # 殻を通ってくる光
    g.add_color_stop_rgba(0, 1.0, 0.98, 0.9, 0.35 + 0.05 * math.sin(t * 0.8))
    g.add_color_stop_rgba(1, 1.0, 0.98, 0.9, 0.0)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    ctx.save()
    ctx.translate(960, 540)
    ctx.scale(1.0, 1.15)
    g = cairo.RadialGradient(0, 0, 360, 0, 0, 820)
    for off, col, al in ((0, "#4a3a28", 0.0), (0.6, "#4a3a28", 0.30), (1, "#1f160d", 0.90)):
        r, gg, b, _a = hexrgb(col)
        g.add_color_stop_rgba(off, r, gg, b, al)
    ctx.set_source(g)
    ctx.rectangle(-2000, -2000, 4000, 4000)
    ctx.fill()
    ctx.restore()


def fp_adult_view(ctx, t, egg=False, white=0.0):
    """一人称: 大人になって氷の上に立つ。まわりに群れ、吹雪。egg=True で、つがいの父親が足の上に卵をのせている（自分の体は描かない）"""
    pa.sky(ctx, 0, 600)
    pa.ice_shelf(ctx, 560, H_)
    huddle(ctx, 960, 700, 1500, 22, seed=7)
    draw_emperor(ctx, 250, 905 + bob(t, 2, 0.9), 560, facing=1)
    if egg:
        draw_father_with_egg(ctx, 1560, 905 + bob(t, 2, 1.1, 1.0), 640, facing=-1)
    else:
        draw_emperor(ctx, 1680, 905 + bob(t, 2, 1.1, 1.0), 600, facing=-1)
    pa.blizzard(ctx, t, a=0.6, n=180, seed=9, speed=0.8, size=1.0, veil=0.10)
    whiten(ctx, white)


def big_egg(ctx, t, x, y, r, ring=0.0):
    """白い卵1個（やさしく揺れる）。ring>0 で金の輪"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(0.05 * math.sin(t * 1.4))
    ctx.translate(-x, -y)
    pa.draw_penguin_egg(ctx, x, y, r)
    ctx.restore()
    if ring > 0.003:
        tset(ctx, GOLD, ring)
        ctx.set_line_width(10)
        ell(ctx, x, y - r * 1.3, r * 1.25, r * 1.62)
        ctx.stroke()


# ---------- 卵・ヒナ・鳥の帯（50列×4段。1つの絵＝200個ぶんの割合）----------
BAND_COLS, BAND_ROWS = 50, 4
BX0, BX1 = 190, 1730


def icon(ctx, kind, x, y, p, a=1.0):
    """帯の小さな絵（p＝列の幅）。egg＝卵、chick＝灰色のヒナ、bird＝紺と白の鳥"""
    if a <= 0.01:
        return
    if kind == "egg":
        tset(ctx, "#b9a67a", a)
        ell(ctx, x, y, p * 0.36, p * 0.47)
        ctx.fill()
        tset(ctx, "#fbf6e2", a)
        ell(ctx, x - p * 0.03, y - p * 0.04, p * 0.30, p * 0.41)
        ctx.fill()
    elif kind == "chick":
        tset(ctx, "#8d9097", a)
        ell(ctx, x, y + p * 0.12, p * 0.35, p * 0.36)
        ctx.fill()
        tset(ctx, "#1d1e25", a)
        ctx.arc(x, y - p * 0.24, p * 0.22, 0, 2 * math.pi)
        ctx.fill()
        tset(ctx, "#f6f3ea", a)
        ell(ctx, x + p * 0.04, y - p * 0.22, p * 0.14, p * 0.15)
        ctx.fill()
    else:
        tset(ctx, "#222944", a)
        ell(ctx, x, y + p * 0.12, p * 0.30, p * 0.37)            # 体
        ctx.fill()
        ctx.arc(x + p * 0.03, y - p * 0.27, p * 0.19, 0, 2 * math.pi)   # 頭
        ctx.fill()
        ctx.move_to(x + p * 0.18, y - p * 0.31)                    # くちばし
        ctx.line_to(x + p * 0.40, y - p * 0.22)
        ctx.line_to(x + p * 0.17, y - p * 0.20)
        ctx.close_path()
        ctx.fill()
        tset(ctx, "#f8f6ee", a)
        ell(ctx, x + p * 0.08, y + p * 0.16, p * 0.19, p * 0.29)    # おなか
        ctx.fill()
        tset(ctx, "#f5b92e", a)
        ell(ctx, x + p * 0.01, y - p * 0.17, p * 0.09, p * 0.10)    # 耳の斑
        ctx.fill()


def band_geom(x0, x1, yc, rows=BAND_ROWS, cols=BAND_COLS):
    pitch = (x1 - x0) / cols
    rp = pitch * 1.25
    return pitch, rp, yc - rp * (rows - 1) / 2


def eband(ctx, x0, x1, yc, fn, rows=BAND_ROWS, cols=BAND_COLS):
    """fn(i, f) -> (種類, 不透明度)。i＝列・f＝列の中心の割合（左から生きた日数の短い順）"""
    pitch, rp, ytop = band_geom(x0, x1, yc, rows, cols)
    for i in range(cols):
        kind, a = fn(i, (i + 0.5) / cols)
        cx = x0 + pitch * (i + 0.5)
        for r_ in range(rows):
            icon(ctx, kind, cx, ytop + rp * r_, pitch, a)


def stage_kind(f, upto):
    """f の位置の鳥が、どこまで育った姿で描かれるか（upto: 'egg'|'chick'|'bird'）"""
    if upto == "egg" or f < FE:
        return "egg"
    if upto == "chick" or f < FC:
        return "chick"
    return "bird"


def faded(t, f, segs, base=1.0):
    """segs=[(f0, f1, t0)]: t0 から 0.8秒かけて、f0〜f1 の列をうすくする（-99 なら最初から）"""
    a = base
    for f0, f1, t0 in segs:
        if f0 <= f < f1:
            a = min(a, 1.0 - 0.72 * fade(t, t0, 0.8))
    return a


def band_mark(ctx, x0, x1, yc, f, col=GOLD, a=1.0, rows=BAND_ROWS, up=60, down=60, w=7):
    pitch, rp, ytop = band_geom(x0, x1, yc, rows)
    x = x0 + (x1 - x0) * f
    tset(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, ytop - up)
    ctx.line_to(x, ytop + rp * (rows - 1) + down)
    ctx.stroke()
    return x


def bracket(ctx, x0, x1, y, col, a=1.0, w=8):
    if a <= 0.003:
        return
    tset(ctx, col, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0 + 3, y - 14)
    ctx.line_to(x0 + 3, y)
    ctx.line_to(x1 - 3, y)
    ctx.line_to(x1 - 3, y - 14)
    ctx.stroke()


def px_of(f, x0=BX0, x1=BX1):
    return x0 + (x1 - x0) * f


def glow_box(ctx, t, x0, y0, x1, y1, a, col=GOLD, r=24):
    if a > 0.003:
        tset(ctx, col, a * (0.6 + 0.4 * math.sin(t * 5)))
        ctx.set_line_width(9)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, r)
        ctx.stroke()


def hbar(ctx, x0, y, wmax, h, frac, col, a=1.0):
    tset(ctx, col, a)
    rrect(ctx, x0, y - h / 2, max(h * 0.6, wmax * frac), h, h * 0.28)
    ctx.fill()


def band_card(ctx, t, y0=170, y1=860):
    chart_bg(ctx, t)
    chart_card(ctx, 110, y0, 1810, y1)


BAND_Y = 340


# ---------- 地図（Natural Earth の実データ・南極点を中心に）----------
COLONY = (140.0, -66.66)       # ポワント・ジェオロジー


class PMap:
    """南極まわりの地図を、中心 (cx, cy)・半径 rad の円に収める（南極点から rview 度まで）"""
    def __init__(self, cx, cy, rad, rview=50.0):
        self.cx, self.cy, self.rad = cx, cy, rad
        self.k = rad / rview

    def xy(self, lon, lat):
        px, py = polar_xy(lon, lat)
        return self.cx + px * self.k, self.cy + py * self.k

    def pr_xy(self, r_deg, dlon):
        """南極点からの角度 r_deg・東経140度からのずれ dlon の点"""
        a = math.radians(dlon)
        return self.cx + r_deg * math.sin(a) * self.k, self.cy - r_deg * math.cos(a) * self.k

    def _path(self, ctx, r):
        ctx.move_to(self.cx + r[0][0] * self.k, self.cy + r[0][1] * self.k)
        for x, y in r[1:]:
            ctx.line_to(self.cx + x * self.k, self.cy + y * self.k)
        ctx.close_path()

    def draw(self, ctx, packice=0.0):
        from penguin_map_data import ANT, LAND
        tset(ctx, "#9ccbe3")
        ctx.arc(self.cx, self.cy, self.rad, 0, 2 * math.pi)
        ctx.fill()
        ctx.save()
        ctx.arc(self.cx, self.cy, self.rad, 0, 2 * math.pi)
        ctx.clip()
        if packice > 0.003:                      # 流氷の帯（南緯60度前後まで）
            tset(ctx, "#e4f1f8", 0.85 * packice)
            ctx.arc(self.cx, self.cy, 30 * self.k, 0, 2 * math.pi)
            ctx.fill()
        for r in LAND:
            self._path(ctx, r)
        tset(ctx, "#e6dcc0")
        ctx.fill()
        for r in ANT:
            self._path(ctx, r)
        tset(ctx, "#ffffff")
        ctx.fill()
        ctx.restore()
        tset(ctx, "#5f86a6")
        ctx.set_line_width(4)
        ctx.arc(self.cx, self.cy, self.rad, 0, 2 * math.pi)
        ctx.stroke()


def map_label(ctx, s, x, y, a=1.0, bg="#7a3a12"):
    if a > 0.003:
        panel(ctx, [(s, 40, WHITE)], x, y, a=a, bg=bg, pad=(16, 8), r=12)


def colony_mark(ctx, mv, t, a=1.0):
    x, y = mv.xy(*COLONY)
    disc(ctx, x, y, 15 + 3 * math.sin(t * 4), REDC, a)
    disc(ctx, x, y, 6, "#ffffff", a)
    return x, y


# ============================================================
# 0 あなたは何年生きられる？
# ============================================================
Q_TXT = "何年生きられる？"
OPTS = ("1年未満", "5年", "15年")
OPT_X = (620, 960, 1300)
OPT_Y = 580
CORNER = [("答えは最後に", 44, YEL), ("1年未満　5年　15年", 44, WHITE)]
CORNER_XY = (300, 100)


def _mother_leaving(t0):
    def f(ctx):
        u = ease(clamp01((ctx_t[0] - t0) / 5.0))
        pa.draw_emperor(ctx, 1000 + 360 * u, 712 - 80 * u, 290 - 200 * u, facing=1, pose="walk" if int(ctx_t[0] * 3) % 2 else "stand", a=1.0 - 0.5 * u)
    return f


ctx_t = [0.0]


def sc_open(ctx, t):
    fp_shell_view(ctx, t)
    t_q = Sk("c0_q", 0.5)
    t_c = Sk("c0_ans", 0.0)
    for k, s_ in enumerate(OPTS):
        card(ctx, t, t_q + 0.17 * k, t_c, [(s_, 70, WHITE)], OPT_X[k], OPT_Y, pad=(34, 14), bg="#27518a", border=YEL)
    if t >= 1.0:
        card(ctx, t, 1.0, t_c, [(Q_TXT, 46, WHITE)], 960, 75, pad=(30, 12), border=YEL)


def corner_card(ctx, t, t0, t1=None):
    card(ctx, t, t0, t1, CORNER, *CORNER_XY, pad=(26, 14), bg="#27518a")


def sc_c0_egg(ctx, t):
    band_card(ctx, t, 180, 860)
    rect(ctx, "#eef5fa", 140, 640, 1780, 830)
    rect(ctx, "#cfe0ec", 140, 640, 1780, 652)
    rnd = random.Random(5)
    t0 = Sk("c0_egg", 0.0) - 0.4
    k = 0
    for r_ in range(8):
        n = 15 - 2 * r_
        for i in range(n):
            ta = t0 + 0.05 * k
            k += 1
            if t < ta:
                continue
            e = ease_out(clamp01((t - ta) / 0.3))
            x = 640 + (i - (n - 1) / 2) * 58 + rnd.uniform(-5, 5)
            y = 760 - r_ * 52 + rnd.uniform(-4, 4)
            pa.draw_penguin_egg(ctx, x, y - 8 * (1 - e), 19 * (0.6 + 0.4 * e), a=e)
    Cd(ctx, t, "c0_egg", 0.3, [("南極の氷の上で産まれる卵", 50, WHITE), ("1万個", 110, YEL)], 1400, 400, pad=(44, 22), border=YEL)


def sc_c0_prob(ctx, t):
    ice_bg(ctx, t, hor=520)
    t0 = Sk("c0_prob", 0.0) - 0.6
    bx0, bx1 = 760, 1160
    tset(ctx, "#f3c25a")
    rrect(ctx, bx0, 440, bx1 - bx0, 330, 30)
    ctx.fill()
    tset(ctx, "#d49a2e")
    rrect(ctx, bx0 + 30, 580, bx1 - bx0 - 60, 40, 14)
    ctx.fill()
    tx(ctx, "記録の確率", (bx0 + bx1) / 2, 510, 54, "#5a3a00")
    period, speed = 0.75, 360.0
    for k in range(40):
        ta = t0 + k * period
        if t < ta:
            break
        x = 80 + (t - ta) * speed
        if x > 1900 or bx0 - 20 < x < bx1 + 20:
            continue
        pa.draw_penguin_egg(ctx, x, 760 - 8 * abs(math.sin((t - ta) * 4)), 26)
    Cd(ctx, t, "c0_prob", 0.2, R("卵ごとに一生を進める", sz=50), 1100, 230, pad=(36, 16), border=YEL)


def sc_c0_one(ctx, t):
    ctx.set_source(lin(0, 0, 0, H_, [(0, "#d7e5f1", 1), (1, "#eef4f9", 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    disc(ctx, 600, 520, 330, "#f6f9fc")
    light_snow(ctx, t, 0.4)
    big_egg(ctx, t, 600, 760, 150)
    Cd(ctx, t, "c0_one", 0.25, [("最後に", 56, YEL), ("中央値の1羽の一生を", 58, WHITE)], 1380, 440, pad=(44, 22), border=YEL)


def sc_c0_med(ctx, t):
    band_card(ctx, t, 180, 860)
    tm = Sk("c0_med", 0.3)
    mid = fade(t, tm, 0.3)

    def fn(i, f):
        return ("egg", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    if mid > 0.003:
        band_mark(ctx, BX0, BX1, BAND_Y, 0.5, a=mid, up=40, down=50)
        tx(ctx, "中央値", 960, 230, 46, "#5c3b00", a=mid)
    tx(ctx, "短い", BX0 + 60, 520, 44)
    tx(ctx, "長い", BX1 - 60, 520, 44)
    tx(ctx, "生きた日数", 960, 520, 44)
    arrow2(ctx, (BX0 + 160, 520), (BX0 + 300, 520), "#5b6f93", 7, 1.0, head=22)
    arrow2(ctx, (BX1 - 300, 520), (BX1 - 160, 520), "#5b6f93", 7, 1.0, head=22)
    unit_tag(ctx, "/1万個", 1640, 230)
    Cd(ctx, t, "c0_med", 0.1, [("中央値＝生きた日数の順に並べた、", 46, WHITE), ("ちょうど真ん中の値", 46, YEL)], 960, 715, pad=(34, 16), border=YEL)


# ============================================================
# 1 ふ化できる？
# ============================================================
def sc_c1_a(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1450, 640, 700, 12, seed=2)
    draw_father_with_egg(ctx, 760, 905 + bob(t, 2, 1.1), 640, facing=1)


def sc_c1_big(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 640, 650, 900, 16, seed=4)
    draw_emperor(ctx, 1380, 905 + bob(t, 2, 1.0), 680, facing=-1)
    Cd(ctx, t, "c1_big", 0.35, R("いちばん大きなペンギン", sz=60), 620, 230, pad=(40, 20), border=YEL)


def sc_c1_map(ctx, t):
    chart_bg(ctx, t)
    chart_card(ctx, 110, 40, 1080, 900)
    mv = PMap(595, 470, 400)
    mv.draw(ctx)
    x, y = colony_mark(ctx, mv, t)
    map_label(ctx, "南極", *mv.xy(110.0, -85.0))
    a = fade(t, Sk("c1_map", 0.25), 0.4)
    map_label(ctx, "フランスの基地の近く", x, y - 62, a=a)
    Cd(ctx, t, "c1_map", 0.45, [("この群れで数えた", 46, WHITE), ("約3,000つがい", 80, YEL)], 1450, 430, pad=(44, 22), border=YEL)


def sc_c1_gather(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 960, 690, 900, 18, seed=6)
    t0 = SC_START["c1_gather"]
    for k, (x0_, dx, y, h, fc) in enumerate(((-150, 260, 860, 330, 1), (2050, -300, 880, 360, -1), (-300, 330, 760, 220, 1))):
        u = clamp01((t - t0) / 6.0)
        walker(ctx, t, x0_ + dx * u * 2.2, y, h, facing=fc, ph=k)


def sc_c1_rec(ctx, t):
    band_card(ctx, t, 170, 860)
    tx(ctx, "何十年", 960, 300, 80)
    t0 = SC_START["c1_rec"] + 0.3
    arrow2(ctx, (260, 480), (1660, 480), "#5b6f93", 9, 1.0, head=34)
    for k in range(12):
        x = 300 + k * 112
        line2(ctx, (x, 455), (x, 505), "#5b6f93", 6)
        a = fade(t, t0 + 0.25 * k, 0.3)
        if a > 0.003:                               # 記録の帳面
            tset(ctx, "#fbf7ea", a)
            rrect(ctx, x - 28, 540, 56, 72, 8)
            ctx.fill()
            tset(ctx, "#b9ad8c", a)
            for j in range(3):
                ctx.rectangle(x - 18, 556 + j * 16, 36, 5)
                ctx.fill()
    Cd(ctx, t, "c1_rec", 0.3, R("何十年分の記録", sz=56), 960, 740, pad=(40, 18), border=YEL)


def sc_c1_lay(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1500, 640, 600, 10, seed=8)
    draw_father_with_egg(ctx, 620, 905 + bob(t, 2, 1.0), 600, facing=1)
    draw_emperor(ctx, 1000, 905 + bob(t, 2, 1.2, 1.0), 590, facing=-1)
    Cd(ctx, t, "c1_one", 0.25, [("1つがいに", 50, WHITE), ("卵1個", 90, YEL)], 1450, 260, t1=Sk("c1_may", 0.0) - 0.3, pad=(44, 20), border=YEL)
    Cd(ctx, t, "c1_may", 0.2, [("5〜6月ごろ", 70, YEL), ("卵を産む", 50, WHITE)], 1450, 260, pad=(44, 20), border=YEL)


def sc_c1_female(ctx, t):
    pa.sky(ctx, 0, 600)
    pa.ice_shelf(ctx, 560, H_)
    rect(ctx, pa.SEA_T, 1250, 548, 1920, 566)
    light_snow(ctx, t, 0.5)
    draw_father_with_egg(ctx, 380, 905 + bob(t, 2, 1.0), 560, facing=1)
    t0 = SC_START["c1_female"] + 0.3
    u = clamp01((t - t0) / max(1.0, SC_END["c1_female"] - t0))
    x = lerp(760, 1500, u)
    y = lerp(880, 690, u)
    h = lerp(470, 110, u)
    walker(ctx, t, x, y, h, facing=1)
    Cd(ctx, t, "c1_female", 0.3, R("メスは海へ", sz=56), 1500, 250, pad=(40, 18), border=YEL)


def sc_c1_fp(ctx, t):
    fp_shell_view(ctx, t)
    Cd(ctx, t, "c1_warm", 0.25, [("オスが足の上で", 50, WHITE), ("約2か月", 80, YEL)], 960, 140, t1=Sk("c1_fast", 0.0) - 0.3, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c1_fast", 0.15, [("繁殖地に来てから ヒナがかえるまで", 46, WHITE), ("約4か月食べない", 80, YEL)], 960, 140, pad=(40, 16), border=YEL)


def sc_c1_guess(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1500, 640, 600, 10, seed=8)
    draw_father_with_egg(ctx, 600, 905 + bob(t, 2, 1.0), 600, facing=1)
    Cd(ctx, t, "c1_guess", 0.1, R("卵は、かえる？", sz=80), 1300, 330, pad=(50, 24), border=YEL)


BAND_Q = (960, 95)      # 帯の場面で、上の小さな札の位置


def sc_c1_band(ctx, t):
    band_card(ctx, t, 170, 880)
    t_fe = Sk("c1_nohatch", 0.2)

    def fn(i, f):
        return ("egg", faded(t, f, [(0.0, FE, t_fe)]))
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    a1 = fade(t, Sk("c1_band", 0.45), 0.4)
    bracket(ctx, px_of(FE), BX1, 460, C_L, a1)
    Cd(ctx, t, "c1_band", 0.45, vrows("ふ化", "8,226", ""), 1300, 650, pad=(44, 18), border=YEL)
    a2 = fade(t, t_fe, 0.4)
    bracket(ctx, BX0, px_of(FE), 460, C_E, a2)
    Cd(ctx, t, "c1_nohatch", 0.2, vrows("ふ化せず", "1,774個", ""), 420, 650, pad=(40, 18), border=YEL)
    Cd(ctx, t, "c1_2wari", 0.2, [("約2割", 72, YEL)], 830, 650, pad=(34, 14), border=YEL)
    g = fade(t, Sk("c1_gate", 0.1), 0.3)
    if g > 0.003:
        x0, y0, x1, y1 = panel(ctx, [("問い1　ふ化できる？", 46, WHITE)], *BAND_Q, a=g, pad=(34, 12))
        glow_box(ctx, t, x0 - 6, y0 - 6, x1 + 6, y1 + 6, g)


def sc_c1_snow(ctx, t):
    band_card(ctx, t, 150, 860)
    rect(ctx, "#eef5fa", 300, 520, 1620, 620)
    for k in range(5):                    # 氷の上の卵
        pa.draw_penguin_egg(ctx, 560 + k * 200, 600, 26)
    for cx, cy, s in ((700, 260, 1.0), (1150, 240, 1.2)):         # 雪雲
        for dx, dy, r in ((-90, 10, 60), (0, -20, 80), (90, 10, 60), (0, 30, 70)):
            disc(ctx, cx + dx * s, cy + dy * s, r * s, "#9fb1c6")
    rnd = random.Random(2)
    ctx.save()
    ctx.rectangle(300, 300, 1320, 300)
    ctx.clip()
    for i in range(90):
        x0, y0 = rnd.uniform(420, 1500), rnd.uniform(0, 300)
        y = 300 + (y0 + 70 * t) % 300
        disc(ctx, x0 + 10 * math.sin(t + i), y, rnd.uniform(4, 8), "#ffffff")
    ctx.restore()
    tx(ctx, "5月の雪", 330, 260, 46)
    Cd(ctx, t, "c1_snow", 0.3, R("雪の多い年は、ふ化が減る研究あり", sz=50), 960, 760, pad=(40, 18), border=YEL)


def sc_c1_unk(ctx, t):
    band_card(ctx, t, 170, 860)

    def fn(i, f):
        return ("egg", 0.28 if f < FE else 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    for k, x in enumerate((px_of(FE * 0.2), px_of(FE * 0.55), px_of(FE * 0.9))):
        tx(ctx, "？", x, 225, 64, "#7a4410", a=fade(t, Sk("c1_unk", 0.2) + 0.2 * k, 0.3))
    Cd(ctx, t, "c1_unk", 0.35, R("1個ずつの理由は、分かっていない", sz=52), 960, 650, pad=(40, 18), border=YEL)


def sc_c1_ans(ctx, t):
    band_card(ctx, t, 170, 880)
    t_go = Sk("c1_ans2", 0.3)

    def fn(i, f):
        if f < FE:
            return ("egg", 0.28 * (1.0 - ease(seg(t, t_go, t_go + 2.5))))
        return ("egg", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FE), BX1, 460, C_L, 1.0)
    Cd(ctx, t, "c1_ans", 0.3, arows(1, ("ふ化 約8割", 80, WHITE), ("1万個のうち 8,226羽", 44, WHITE)), 1250, 660, pad=(48, 20), border=YEL)
    bracket(ctx, BX0, px_of(FE), 460, C_E, fade(t, Sk("c1_ans2", 0.1), 0.4))
    Cd(ctx, t, "c1_ans2", 0.15, vrows("ふ化せず", "約2割", "1万個のうち"), 470, 660, pad=(40, 18), border=YEL)


# ============================================================
# 2 ヒナの冬
# ============================================================
def sc_c2_a(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1500, 640, 600, 10, seed=12)
    parent_with_chick(ctx, 760, 905 + bob(t, 2, 1.0), 640, facing=1, t=t)


def sc_c2_base(ctx, t):
    band_card(ctx, t, 170, 860)
    t0 = Sk("c2_base", 0.25)

    def fn(i, f):
        if f < FE:
            return ("egg", 0.28)
        return ("chick" if t >= t0 + 1.2 * (f - FE) / (1 - FE) else "egg", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FE), BX1, 460, C_L, fade(t, t0, 0.4))
    Cd(ctx, t, "c2_base", 0.2, vrows("ふ化した", "8,226羽", ""), 1250, 650, pad=(44, 18), border=YEL)


def sc_c2_pouch(ctx, t):
    pa.fp_from_pouch(ctx, t)
    Cd(ctx, t, "c2_july", 0.25, R("7月ごろ ふ化", sz=56), 960, 120, t1=Sk("c2_50", 0.0) - 0.3, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c2_50", 0.2, [("親のおなかの袋の中で", 48, WHITE), ("約50日", 76, YEL)], 960, 150, pad=(40, 16), border=YEL)


def sc_c2_creche(ctx, t):
    with chick_age_cap():
        pa.fp_in_creche(ctx, t)
    Cd(ctx, t, "c2_creche", 0.3, R("ヒナどうしで群れる", sz=54), 960, 90, pad=(40, 14), border=YEL)


def sc_c2_parents(ctx, t):
    pa.sky(ctx, 0, 600)
    pa.ice_shelf(ctx, 560, H_)
    rect(ctx, pa.SEA_T, 1300, 548, 1920, 566)
    light_snow(ctx, t, 0.5)
    creche(ctx, 520, 760, 620, 12, seed=3)
    t0 = SC_START["c2_parents"]
    for k in range(4):
        u = ((t - t0) / 7.0 + k * 0.25) % 1.0
        out_ = k % 2 == 0
        x = lerp(900, 1650, u if out_ else 1 - u)
        y = lerp(860, 700, u if out_ else 1 - u) - 20 * (k // 2)
        h = lerp(380, 150, u if out_ else 1 - u)
        walker(ctx, t, x, y, h, facing=1 if out_ else -1, ph=k)
    Cd(ctx, t, "c2_parents", 0.3, R("親は、海と行き来する", sz=50), 1400, 230, pad=(40, 16), border=YEL)


MONTHS = ("7月", "8月", "9月", "10月", "11月", "12月")


def sc_c2_months(ctx, t):
    band_card(ctx, t, 170, 860)
    x0, dx, y = 260, 240, 420
    t0 = Sk("c2_months", 0.1)
    for k, m in enumerate(MONTHS):
        tset(ctx, "#eef4fa")
        rrect(ctx, x0 + k * dx, y - 60, dx - 16, 120, 18)
        ctx.fill()
        tx(ctx, m, x0 + k * dx + (dx - 16) / 2, y, 50)
    p = ease(seg(t, t0, t0 + 2.4))
    if p > 0:
        tset(ctx, C_C, 0.9)
        rrect(ctx, x0, y + 90, (6 * dx - 16) * p, 34, 14)
        ctx.fill()
    Cd(ctx, t, "c2_months", 0.3, [("ふ化から巣立ちまで", 48, WHITE), ("約5か月", 86, YEL)], 960, 700, pad=(44, 18), border=YEL)


def sc_c2_edge(ctx, t):
    edge_scene(ctx, t, n=4, age=1.0)
    Cd(ctx, t, "c2_edge", 0.3, [("12月末", 76, YEL), ("海へ", 56, WHITE)], 1550, 250, pad=(44, 20), border=YEL)


YEAR_BARS = [0.62, 0.35, 0.80, 0.55, 0.20, 0.72, 0.48, 0.90, 0.30, 0.66, 0.44, 0.78, 0.25, 0.58]


def sc_c2_years(ctx, t):
    band_card(ctx, t, 150, 880)
    tx(ctx, "年ごとの記録", 960, 230, 52)
    base, hmax = 690, 360
    t0 = SC_START["c2_years"] + 0.2
    for k, v in enumerate(YEAR_BARS):
        p = ease(seg(t, t0 + 0.03 * k, t0 + 0.03 * k + 0.4))
        if p <= 0:
            continue
        x = 300 + k * 94
        tset(ctx, "#7f98bb")
        rrect(ctx, x, base - hmax * v * p, 66, hmax * v * p + 6, 12)
        ctx.fill()
    rect(ctx, "#5b6f93", 270, base, 1650, base + 6)
    Cd(ctx, t, "c2_years", 0.35, R("年によって大きく違う", sz=56), 960, 790, pad=(40, 16), border=YEL)


def sc_c2_far(ctx, t):
    band_card(ctx, t, 150, 880)
    for k, (lab, xs) in enumerate((("海氷が近い年", 960), ("海氷が遠い年", 1640))):
        y = 330 + k * 230
        tx(ctx, lab, 160, y - 70, 46, align="left")
        for j in range(3):
            icon(ctx, "bird", 400 + j * 34, y, 54)
        line2(ctx, (480, y), (xs - 60, y), "#5b6f93", 8, dash=[22, 16])
        tset(ctx, pa.SEA_T)
        rrect(ctx, xs - 60, y - 50, 140, 100, 20)
        ctx.fill()
        tx(ctx, "海", xs + 10, y, 46, "#ffffff")
        u = 0.5 + 0.5 * math.sin(t * 1.2 + k)
        icon(ctx, "bird", lerp(500, xs - 90, u), y - 4, 54)
    Cd(ctx, t, "c2_far", 0.35, R("海氷が遠い年は、減る", sz=56), 960, 790, pad=(40, 16), border=YEL)


def creche_scene(ctx, t, n=12):
    ice_bg(ctx, t)
    huddle(ctx, 1550, 630, 500, 8, seed=14)
    creche(ctx, 900, 900, 1100, n, seed=5)


def sc_c2_bird(ctx, t):
    creche_scene(ctx, t)
    Cd(ctx, t, "c2_bird", 0.3, R("オオフルマカモメの記録あり・数は不明", sz=46), 960, 200, pad=(36, 16))


def sc_c2_guess(ctx, t):
    creche_scene(ctx, t)
    Cd(ctx, t, "c2_guess", 0.1, R("ヒナは、巣立てる？", sz=80), 960, 300, pad=(50, 24), border=YEL)


def sc_c2_band(ctx, t):
    band_card(ctx, t, 170, 880)
    t_c = Sk("c2_dead", 0.2)

    def fn(i, f):
        if f < FE:
            return ("egg", 0.28)
        return ("chick", faded(t, f, [(FE, FC, t_c)]))
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FC), BX1, 460, C_L, fade(t, Sk("c2_band", 0.5), 0.4))
    Cd(ctx, t, "c2_band", 0.5, vrows("巣立ち", "5,321", ""), 1330, 660, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c2_5m", 0.2, R("巣立つまで 約5か月", sz=48), *BAND_Q, pad=(34, 12))
    bracket(ctx, px_of(FE), px_of(FC), 460, C_C, fade(t, t_c, 0.4))
    Cd(ctx, t, "c2_dead", 0.2, vrows("ヒナのうちに一生を終えた", "2,905", ""), 690, 660, pad=(40, 18), border=YEL)


def sc_c2_ans(ctx, t):
    creche_scene(ctx, t, n=10)
    Cd(ctx, t, "c2_ans", 0.3, arows(2, ("巣立ち 約3分の2", 76, WHITE), ("ふ化した8,226羽のうち", 44, WHITE)), 960, 250, pad=(48, 20), border=YEL)
    Cd(ctx, t, "c2_winter", 0.2, R("冬を越えて巣立つ 約3分の2", sz=50), 960, 560, pad=(40, 16), border=YEL)


def sc_c2_sum(ctx, t):
    band_card(ctx, t, 170, 880)

    def fn(i, f):
        return ("egg" if f < FE else "chick", 0.28 if f < FC else 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, BX0, px_of(FC), 460, C_C, fade(t, Sk("c2_sum", 0.4), 0.4))
    Cd(ctx, t, "c2_sum", 0.4, vrows("海に出る前に一生を終えた", "4,679", ""), 560, 660, pad=(44, 18), border=YEL)


# ============================================================
# 3 初めての海
# ============================================================
def sc_c3_a(ctx, t):
    edge_scene(ctx, t, n=3, age=1.0)


def sc_c3_base(ctx, t):
    band_card(ctx, t, 170, 860)
    t0 = Sk("c3_base", 0.25)

    def fn(i, f):
        if f < FC:
            return ("egg" if f < FE else "chick", 0.28)
        return ("bird" if t >= t0 + 1.2 * (f - FC) / (1 - FC) else "chick", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FC), BX1, 460, C_L, fade(t, t0, 0.4))
    Cd(ctx, t, "c3_base", 0.2, vrows("巣立った", "5,321羽", ""), 1330, 650, pad=(44, 18), border=YEL)


def sc_c3_edge(ctx, t):
    pa.fp_ice_edge(ctx, t)
    Cd(ctx, t, "c3_stand", 0.2, R("12月の終わり　氷の縁", sz=52), 960, 110, pad=(40, 16), border=YEL)


def sc_c3_map(ctx, t):
    chart_bg(ctx, t)
    chart_card(ctx, 110, 40, 1080, 900)
    pk = fade(t, Sk("c3_ryu", 0.1), 0.8)
    mv = PMap(595, 470, 400)
    mv.draw(ctx, packice=pk)
    t1, t2, t3 = Sk("c3_north", 0.15), Sk("c3_far", 0.9), Sk("c3_ryu", 0.15)
    rnd = random.Random(4)
    r0 = 90 + COLONY[1]
    for j in range(14):
        dl = rnd.uniform(-22, 22)
        rf = rnd.uniform(36, 44)
        rb = rnd.uniform(27, 31)
        if t < t3:
            r = lerp(r0, rf, ease(seg(t, t1 + 0.08 * j, t2)))
        else:
            r = lerp(rf, rb, ease(seg(t, t3, t3 + 3.0)))
        x, y = mv.pr_xy(r, dl + 3 * math.sin(t * 0.7 + j))
        disc(ctx, x, y, 11, "#ffffff")
        disc(ctx, x, y, 7.5, "#1f2d44")
    colony_mark(ctx, mv, t)
    map_label(ctx, "南極", *mv.xy(110.0, -85.0))
    map_label(ctx, "流氷", *mv.pr_xy(29, -95), a=pk, bg="#2c4a73")
    Cd(ctx, t, "c3_north", 0.25, [("最初の数か月は", 48, WHITE), ("北へ", 86, YEL)], 1450, 300, pad=(44, 20), border=YEL)
    Cd(ctx, t, "c3_ryu", 0.2, [("秋・冬は", 48, WHITE), ("流氷へ", 86, YEL)], 1450, 620, pad=(44, 20), border=YEL)


def sc_c3_under(ctx, t):
    pa.fp_underwater(ctx, t)
    Cd(ctx, t, "c3_under", 0.3, R("1年目の海", sz=60), 460, 800, pad=(40, 16), border=YEL)


def sc_c3_data(ctx, t):
    band_card(ctx, t, 150, 880)
    rect(ctx, "#2e5d84", 300, 330, 1620, 520)
    for k in range(4):
        x = (420 + k * 330 + 60 * t) % 1320 + 300
        pa.draw_emperor(ctx, x, 470 + 10 * math.sin(t * 2 + k), 160, facing=1, pose="swim")
    rect(ctx, CARDC, 1620, 300, 1800, 560)
    rect(ctx, CARDC, 120, 300, 300, 560)
    tx(ctx, "数える材料", 960, 240, 50)
    Cd(ctx, t, "c3_data", 0.3, [("材料：", 48, WHITE), ("海に出て1年間の生き残り", 56, YEL)], 960, 700, pad=(44, 18), border=YEL)


def sc_c3_guess(ctx, t):
    floe_scene(ctx, t)
    Cd(ctx, t, "c3_guess", 0.1, R("海に出て1年、どれくらい？", sz=72), 960, 260, pad=(50, 24), border=YEL)


def sc_c3_band(ctx, t):
    band_card(ctx, t, 170, 880)
    t_s = Sk("c3_dead", 0.2)

    def fn(i, f):
        if f < FC:
            return ("egg" if f < FE else "chick", 0.28)
        return ("bird", faded(t, f, [(FC, FS, t_s)]))
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FS), BX1, 460, C_L, fade(t, Sk("c3_band", 0.5), 0.4))
    Cd(ctx, t, "c3_band", 0.5, vrows("1年を越えた", "2,088", ""), 1500, 660, pad=(40, 18), border=YEL)
    bracket(ctx, px_of(FC), px_of(FS), 460, C_S, fade(t, t_s, 0.4))
    Cd(ctx, t, "c3_dead", 0.2, vrows("海に出て1年以内に一生を終えた", "3,233", ""), 880, 660, pad=(40, 18), border=YEL)


def sc_c3_bars(ctx, t):
    band_card(ctx, t, 90, 600)
    rows = [("卵のうち", N_EGGD, C_E, 0.25), ("ヒナのうち", N_CHD, C_C, 0.45), ("海に出て1年以内", N_SEAD, C_S, 0.65)]
    x0, wmax = 640, 900
    for k, (lab, v, col, f) in enumerate(rows):
        y = 200 + k * 140
        tx(ctx, lab, 150, y, 46, align="left")
        tset(ctx, "#c3d3e3")
        rrect(ctx, x0, y - 36, wmax, 72, 20)
        ctx.fill()
        ta = Sk("c3_cmp", f)
        p = ease(seg(t, ta, ta + 0.8))
        if p > 0:
            hbar(ctx, x0, y, wmax, 72, v / N_SEAD * p, col)
            tx(ctx, f"{v:,}", x0 + wmax * v / N_SEAD + 24, y, 46, align="left", a=fade(t, ta + 0.8, 0.3))
    unit_tag(ctx, "/1万個", 1650, 130)
    tx(ctx, "一生を終えた数", 150, 130, 44, align="left")      # 2026-11-10 統括: 生き残った数に読めないように表の見出し
    glow_box(ctx, t, 130, 480 - 56, 1730, 480 + 56, fade(t, Sk("c3_cmp", 0.85), 0.4))
    Cd(ctx, t, "c3_ans", 0.3, arows(3, ("いちばん多く減るのは、", 50, WHITE), ("海に出た最初の1年", 66, WHITE)), 960, 770, pad=(48, 18), border=YEL)


def sc_c3_opts(ctx, t):
    fp_shell_view(ctx, t)
    t_c = Sk("c3_last", 0.1)
    for k, s_ in enumerate(OPTS):
        card(ctx, t, Sk("c3_again", 0.45) + 0.17 * k, t_c, [(s_, 70, WHITE)], OPT_X[k], OPT_Y, pad=(34, 14), bg="#27518a", border=YEL)
    card(ctx, t, Sk("c3_again", 0.3), t_c, [(Q_TXT, 46, WHITE)], 960, 75, pad=(30, 12), border=YEL)
    corner_card(ctx, t, t_c)


# ============================================================
# 4 誰も見ていない数年
# ============================================================
def sc_c4_a(ctx, t):
    floe_scene(ctx, t)


def sc_c4_base(ctx, t):
    band_card(ctx, t, 170, 860)

    def fn(i, f):
        if f < FS:
            return (stage_kind(f, "bird"), 0.28)
        return ("bird", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(FS), BX1, 460, C_L, fade(t, Sk("c4_base", 0.2), 0.4))
    Cd(ctx, t, "c4_base", 0.2, vrows("1年を越えた", "2,088羽", ""), 1450, 650, pad=(44, 18), border=YEL)


def sc_c4_map(ctx, t):
    chart_bg(ctx, t)
    chart_card(ctx, 110, 40, 1080, 900)
    mv = PMap(595, 470, 400)
    mv.draw(ctx, packice=1.0)
    rnd = random.Random(9)
    t0 = SC_START["c4_map"]
    for j in range(26):
        dl = rnd.uniform(-180, 180)
        r = rnd.uniform(27, 38)
        a = fade(t, t0 + 0.3 + 0.05 * j, 0.4)
        x, y = mv.pr_xy(r + 1.5 * math.sin(t * 0.6 + j), dl + 4 * t * (1 if j % 2 else -1))
        disc(ctx, x, y, 11, "#ffffff", a)
        disc(ctx, x, y, 7.5, "#1f2d44", a)
    colony_mark(ctx, mv, t)
    map_label(ctx, "南極", *mv.xy(110.0, -85.0))
    Cd(ctx, t, "c4_sea", 0.3, [("1〜4歳は", 48, WHITE), ("海の上", 86, YEL)], 1450, 430, pad=(44, 20), border=YEL)


def sc_c4_colony(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 960, 860, 1300, 20, seed=21)
    Cd(ctx, t, "c4_noreturn", 0.3, R("群れの氷に、若い鳥はいない", sz=50), 960, 220, pad=(40, 16), border=YEL)


AGE_X0, AGE_DX = 245, 245


def sc_c4_dark(ctx, t):
    chart_bg(ctx, t)
    dim = fade(t, Sk("c4_nobody", 0.1), 1.0)
    chart_card(ctx, 110, 170, 1810, 860, col=mix(CARDC, "#8d9db0", 0.45 * dim))
    y = 430
    for k in range(6):
        dark = 1 <= k <= 4
        tset(ctx, "#2b3550" if dark else "#eef4fa")
        rrect(ctx, AGE_X0 + k * AGE_DX, y - 70, AGE_DX - 20, 140, 18)
        ctx.fill()
        tx(ctx, f"{k}歳", AGE_X0 + k * AGE_DX + (AGE_DX - 20) / 2, y, 52, "#ffffff" if dark else DARKTXT)
    bracket(ctx, AGE_X0 + AGE_DX, AGE_X0 + 5 * AGE_DX - 20, y + 110, "#2b3550", 1.0)
    tx(ctx, "1〜4歳　4年間", AGE_X0 + 3 * AGE_DX - 10, y + 165, 50)
    tx(ctx, "記録", 960, 255, 46, a=1.0 - dim)
    Cd(ctx, t, "c4_4y", 0.4, R("誰も数えられていない", sz=52), 960, 760, t1=Sk("c4_nobody", 0.0) - 0.35, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c4_nobody", 0.0, R("この数年は、誰も見ていない", sz=56), 960, 760, pad=(40, 16), border=YEL)


def sc_c4_same(ctx, t):
    band_card(ctx, t, 150, 880)
    for k, (lab, kind) in enumerate((("1歳〜4歳", "bird"), ("大人", "bird"))):
        x = 620 + k * 680
        tset(ctx, "#eef4fa")
        rrect(ctx, x - 230, 260, 460, 330, 22)
        ctx.fill()
        icon(ctx, kind, x, 400 + bob(t, 4, 1.5, k), 150 if k else 110)
        tx(ctx, lab, x, 540, 50)
    tx(ctx, "＝", 960, 420, 110)
    Cd(ctx, t, "c4_same", 0.4, R("1歳〜4歳＝大人と同じ", sz=50), 960, 190, pad=(36, 12), border=YEL)
    Cd(ctx, t, "c4_9", 0.25, [("大人の1年の生き残り", 46, WHITE), ("約9割（0.907）", 72, YEL)], 960, 730, pad=(44, 18), border=YEL)


def sc_c4_guess(ctx, t):
    floe_scene(ctx, t)
    Cd(ctx, t, "c4_guess", 0.1, R("見えない4年で、何羽残る？", sz=72), 960, 260, pad=(50, 24), border=YEL)


def sc_c4_band(ctx, t):
    band_card(ctx, t, 170, 880)
    t_5 = Sk("c4_band", 0.5)

    def fn(i, f):
        if f < FS:
            return (stage_kind(f, "bird"), 0.28)
        return ("bird", faded(t, f, [(FS, F5, t_5)]))
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 225)
    bracket(ctx, px_of(F5), BX1, 460, C_L, fade(t, t_5, 0.4))
    Cd(ctx, t, "c4_band", 0.5, vrows("5歳まで", "1,368", ""), 1560, 660, pad=(40, 18), border=YEL)
    Cd(ctx, t, "c4_age5", 0.2, R("5歳＝子育てを始める年ごろ", sz=48), *BAND_Q, pad=(34, 12))
    Cd(ctx, t, "c4_23", 0.25, [("2,088 → 1,368", 64, YEL), ("約3分の2が残る", 40, WHITE)], 700, 660, pad=(40, 18), border=YEL)


def sc_c4_cmp(ctx, t):
    band_card(ctx, t, 90, 640)
    rows = [("海に出て1年", N_1Y / N_FLEDGE, f"{N_FLEDGE:,}→{N_1Y:,}　約4割が残る", C_S, 0.3),
            ("1〜4歳", N_5Y / N_1Y, f"{N_1Y:,}→{N_5Y:,}　約3分の2が残る", C_L, 0.65)]
    x0, wmax = 560, 1150
    for k, (lab, v, sub, col, f) in enumerate(rows):
        y = 210 + k * 210
        tx(ctx, lab, 150, y, 48, align="left")
        tset(ctx, "#c3d3e3")
        rrect(ctx, x0, y - 36, wmax, 72, 20)
        ctx.fill()
        ta = Sk("c4_cmp", f)
        p = ease(seg(t, ta, ta + 0.8))
        if p > 0:
            hbar(ctx, x0, y, wmax, 72, v * p, col)
            tx(ctx, sub, x0, y + 72, 44, align="left", a=fade(t, ta + 0.5, 0.3))
    Cd(ctx, t, "c4_ans", 0.3, arows(4, ("5歳まで 1,368羽", 70, WHITE)), 960, 810, pad=(48, 16), border=YEL)


# ============================================================
# 5 大人になったペンギン
# ============================================================
def adults_scene(ctx, t, n=3):
    ice_bg(ctx, t)
    huddle(ctx, 960, 680, 1500, 18, seed=31)
    for k, (x, h, fc) in enumerate(((330, 560, 1), (1600, 600, -1), (960, 520, 1))[:n]):
        draw_emperor(ctx, x, 905 + bob(t, 2, 1.0, k), h, facing=fc)


def sc_c5_a(ctx, t):
    adults_scene(ctx, t, n=2)
    Cd(ctx, t, "c5_first5", 0.25, [("その年に初めて子育てする確率", 46, WHITE), ("5歳 約2割・6歳 約3割", 64, YEL)], 960, 230, pad=(44, 18), border=YEL)


def sc_c5_pair(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1500, 640, 600, 10, seed=33)
    draw_father_with_egg(ctx, 560, 905 + bob(t, 2, 1.0), 600, facing=1)
    draw_emperor(ctx, 1080, 905 + bob(t, 2, 1.2, 1.0), 590, facing=-1)
    Cd(ctx, t, "c5_pair", 0.3, R("子育てをした鳥＝大人", sz=60), 1400, 230, pad=(40, 18), border=YEL)


def sc_c5_pull(ctx, t):
    band_card(ctx, t, 170, 880)
    t0 = Sk("c5_pull", 0.45)
    lift = ease(seg(t, t0, t0 + 1.2))

    def fn(i, f):
        if f >= 1 - FA:
            return ("bird", 1.0 - 0.72 * lift)
        if f < FS:
            return (stage_kind(f, "bird"), 0.28)
        return ("bird", 0.28 + 0.72 * (1 - fade(t, t0, 0.6)))
    eband(ctx, BX0, BX1, BAND_Y, fn)
    if lift > 0.003:                       # 右端の 1,081羽ぶんを下へ抜き出す
        pitch, rp, ytop = band_geom(BX0, BX1, BAND_Y)
        ncol = int(round(FA * BAND_COLS))
        for i in range(BAND_COLS - ncol, BAND_COLS):
            cx = BX0 + pitch * (i + 0.5)
            for r_ in range(BAND_ROWS):
                y = ytop + rp * r_ + 250 * lift
                if i >= BAND_COLS - ncol:
                    tset(ctx, GOLD, 0.5 * lift)
                    ctx.arc(cx, y, pitch * 0.5, 0, 2 * math.pi)
                    ctx.fill()
                icon(ctx, "bird", cx, y, pitch, lift)
    ta = Sk("c5_base", 0.3)
    unit_tag(ctx, "/1万個", 1650, 225, a=1 - fade(t, ta, 0.4))
    unit_tag(ctx, "/1,081羽", 1630, 225, a=fade(t, ta + 0.3, 0.4))
    Cd(ctx, t, "c5_pull", 0.45, [("大人になった", 46, WHITE), ("1,081羽", 90, YEL), ("1万個のうち 約1割", 44, WHITE)], 720, 690, pad=(44, 18), border=YEL)


FIRST_X = (560, 960, 1360)


def sc_c5_first(ctx, t):
    band_card(ctx, t, 120, 880)
    base, hmax = 720, 380
    vals = [FIRST_AGE[5], FIRST_AGE[6], FIRST_AGE[7]]
    keys = [("c5_ages", 0.3), ("c5_ages", 0.65), ("c5_7", 0.3)]
    vmax = max(vals)
    rect(ctx, "#5b6f93", 380, base, 1560, base + 6)
    for k, (x, v) in enumerate(zip(FIRST_X, vals)):
        tx(ctx, f"{5 + k}歳", x, base + 55, 50)
        ta = Sk(*keys[k])
        p = ease(seg(t, ta, ta + 0.8))
        if p > 0:
            hh = hmax * v / vmax * p
            tset(ctx, C_A)
            rrect(ctx, x - 100, base - hh, 200, hh + 6, 20)
            ctx.fill()
            tx(ctx, f"{v}羽", x, base - hmax * v / vmax - 40, 52, a=fade(t, ta + 0.6, 0.3))
    unit_tag(ctx, "/1,081羽", 300, 200)
    tx(ctx, "初めての子育ての年齢", 960, 190, 46)
    gm = fade(t, Sk("c5_medage", 0.3), 0.4)
    glow_box(ctx, t, FIRST_X[1] - 135, base - hmax - 95, FIRST_X[1] + 135, base + 95, gm)
    Cd(ctx, t, "c5_medage", 0.35, [("中央値", 44, WHITE), ("6歳", 80, YEL)], 1560, 360, pad=(40, 16), border=YEL)


AD_COLS, AD_ROWS = 18, 6


def adult_band(ctx, x0, x1, yc, a_fn=None):
    """大人の1,081羽（1つの絵＝約10羽・18列×6段）。左から生きた日数の短い順"""
    pitch = (x1 - x0) / AD_COLS
    rp = 58
    top = yc - rp * (AD_ROWS - 1) / 2
    for c_ in range(AD_COLS):
        for r_ in range(AD_ROWS):
            a = 1.0 if a_fn is None else a_fn(c_)
            icon(ctx, "bird", x0 + pitch * (c_ + 0.5), top + rp * r_, 44, a)


def sc_c5_sorted(ctx, t):
    band_card(ctx, t, 120, 900)
    t0 = Sk("c5_sort", 0.1)
    adult_band(ctx, BX0, BX1, 370, a_fn=lambda c_: fade(t, t0 + 0.05 * c_, 0.3))
    tx(ctx, "短い", BX0 + 50, 570, 44)
    tx(ctx, "長い", BX1 - 50, 570, 44)
    tx(ctx, "生きた日数", 960, 570, 44)
    arrow2(ctx, (BX0 + 150, 570), (BX0 + 300, 570), "#5b6f93", 7, 1.0, head=22)
    arrow2(ctx, (BX1 - 300, 570), (BX1 - 150, 570), "#5b6f93", 7, 1.0, head=22)
    unit_tag(ctx, "/1,081羽", 1630, 165)
    m = fade(t, Sk("c5_life", 0.1), 0.4)
    if m > 0.003:
        line2(ctx, (960, 210), (960, 530), GOLD, 8, m)
    Cd(ctx, t, "c5_life", 0.25, [("寿命の中央値", 46, WHITE), ("約15年", 86, YEL), ("（14.6年）", 40, WHITE)], 620, 755, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c5_brood", 0.3, [("子育ての回数の中央値", 46, WHITE), ("7回", 86, YEL)], 1320, 755, pad=(40, 16), border=YEL)


def sc_c5_return(ctx, t):
    pa.sky(ctx, 0, 600)
    pa.ice_shelf(ctx, 560, H_)
    rect(ctx, pa.SEA_T, 1300, 548, 1920, 566)
    light_snow(ctx, t, 0.5)
    huddle(ctx, 520, 700, 700, 12, seed=35)
    t0 = SC_START["c5_return"]
    for k in range(3):
        u_raw = (t - t0) / 7.0 - 0.18 * k
        if u_raw <= 0:
            continue
        u = clamp01(u_raw)
        x, y, h = lerp(1650, 1500 - 300 * k, u), lerp(700, 900 - 50 * k, u), lerp(130, 420 - 60 * k, u)
        if u < 1.0:
            walker(ctx, t, x, y, h, facing=-1, ph=k)
        else:
            draw_emperor(ctx, x, y, h, facing=-1)
    Cd(ctx, t, "c5_return", 0.3, R("毎年、氷へ戻る", sz=60), 1400, 220, t1=Sk("c5_kids", 0.0) - 0.3, pad=(40, 18), border=YEL)
    Cd(ctx, t, "c5_kids", 0.2, [("巣立たせたヒナの中央値", 46, WHITE), ("4羽", 90, YEL)], 1400, 280, pad=(44, 18), border=YEL)


HIST_X = (470, 820, 1170, 1520)


def sc_c5_hist(ctx, t):
    band_card(ctx, t, 120, 880)
    base, hmax = 700, 360
    vmax = max(KID_COUNTS)
    rect(ctx, "#5b6f93", 330, base, 1660, base + 6)
    tx(ctx, "巣立たせたヒナの数", 520, 175, 46)
    unit_tag(ctx, "/1,081羽", 1630, 175)
    tb = Sk("c5_vary", 0.3)
    for k, (lab, _lo, _hi) in enumerate(KID_BINS):
        x = HIST_X[k]
        tx(ctx, lab, x, base + 50, 46)
        p = ease(seg(t, tb + 0.15 * k, tb + 0.15 * k + 0.8))
        if p > 0:
            hh = hmax * KID_COUNTS[k] / vmax * p
            tset(ctx, C_A if k else "#8a6bc2")
            rrect(ctx, x - 110, base - hh, 220, hh + 6, 20)
            ctx.fill()
    top = lambda k: base - hmax * KID_COUNTS[k] / vmax
    tx(ctx, f"{N_KID0}羽", HIST_X[0], top(0) - 40, 52, a=fade(t, Sk("c5_zero", 0.5), 0.3))
    a5 = fade(t, Sk("c5_five", 0.2), 0.4)
    yb = top(2) - 70
    bracket(ctx, HIST_X[2] - 110, HIST_X[3] + 110, yb, C_A, a5)
    tx(ctx, f"5羽以上 {N_KID5}羽（約半分）", (HIST_X[2] + HIST_X[3]) / 2, yb - 48, 46, a=a5)
    tx(ctx, f"{N_KID10}羽（約2割）", HIST_X[3], top(3) - 40, 46, a=fade(t, Sk("c5_ten", 0.3), 0.3))
    ag = fade(t, Sk("c5_gap", 0.2), 0.4)
    if ag > 0.003:
        arrow2(ctx, (HIST_X[0] - 60, 830), (HIST_X[3] + 80, 830), REDC, 10, ag, head=32)


def sc_c5_old(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 1400, 650, 700, 10, seed=37)
    draw_emperor(ctx, 520, 905 + bob(t, 2, 1.0), 640, facing=1)
    Cd(ctx, t, "c5_20", 0.3, vrows("20年以上", "326羽", ""), 1350, 230, pad=(44, 18), border=YEL)
    Cd(ctx, t, "c5_nomax", 0.2, R("最高齢の記録は残っていない", sz=48), 1350, 420, pad=(36, 16))   # 2026-11-10 統括: 群れに重ねない


def sc_c5_ans(ctx, t):
    adults_scene(ctx, t, n=2)
    Cd(ctx, t, "c5_ans", 0.3, arows(5, ("大人になれば 中央値で約15年", 60, WHITE)), 960, 240, pad=(48, 18), border=YEL)
    Cd(ctx, t, "c5_tenth", 0.2, vrows("大人になれる", "約1割", "1万個のうち"), 960, 560, pad=(44, 18), border=YEL)


# ============================================================
# 6 中央値の1羽の一生
# ============================================================
def egg_room(ctx, t):
    ctx.set_source(lin(0, 0, 0, H_, [(0, "#d7e5f1", 1), (1, "#eef4f9", 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    light_snow(ctx, t, 0.4)


def sc_c6_a(ctx, t):
    egg_room(ctx, t)
    disc(ctx, 700, 520, 330, "#f6f9fc")
    big_egg(ctx, t, 700, 760, 150)
    ta = Sk("c6_base1", 0.3)
    card(ctx, t, ta + 0.3, None, [("数える基準", 44, WHITE), ("1万個の卵", 60, YEL)], 1450, 420, pad=(40, 16), border=YEL)   # 2026-11-10 統括: 分母だけの札は意味が分からない


def sc_c6_sel(ctx, t):
    band_card(ctx, t, 150, 880)
    mid = fade(t, Sk("c6_sel", 0.5), 0.3)
    eband(ctx, BX0, BX1, BAND_Y, lambda i, f: ("egg", 1.0))
    unit_tag(ctx, "/1万個", 1650, 205)
    tx(ctx, "短い", BX0 + 50, 500, 44)
    tx(ctx, "長い", BX1 - 50, 500, 44)
    tx(ctx, "生きた日数", 960, 500, 44)
    arrow2(ctx, (BX0 + 150, 500), (BX0 + 300, 500), "#5b6f93", 7, 1.0, head=22)
    arrow2(ctx, (BX1 - 300, 500), (BX1 - 150, 500), "#5b6f93", 7, 1.0, head=22)
    if mid > 0.003:
        band_mark(ctx, BX0, BX1, BAND_Y, 0.5, a=mid, up=30, down=40)
        ctx.push_group()
        big_egg(ctx, t, 960, 820, 62, ring=1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(mid)
    Cd(ctx, t, "c6_sel", 0.55, R("中央値にいちばん近い卵", sz=48), 1450, 700, pad=(36, 16), border=YEL)


def sc_c6_avg(ctx, t):
    band_card(ctx, t, 150, 880)

    def fn(i, f):
        return ("egg", 1.0)
    eband(ctx, BX0, BX1, BAND_Y, fn)
    unit_tag(ctx, "/1万個", 1650, 205)
    a = fade(t, Sk("c6_avg", 0.3), 0.4)
    if a > 0.003:
        glow_box(ctx, t, px_of(0.94) - 8, BAND_Y - 100, BX1 + 12, BAND_Y + 100, a, col=REDC)
        arrow2(ctx, (1300, 560), (px_of(0.96), BAND_Y + 110), REDC, 9, a, head=28)
        tx(ctx, "少数の長生き", 1150, 590, 46, "#8a2530", a=a)
    band_mark(ctx, BX0, BX1, BAND_Y, 0.5, a=1.0, up=30, down=40)
    Cd(ctx, t, "c6_avg", 0.45, R("少数の長生きに引っ張られない", sz=52), 960, 760, pad=(40, 16), border=YEL)


def sc_c6_you(ctx, t):
    tz = Sk("c6_you", 0.25)
    u = ease(seg(t, tz, tz + 1.6))
    if u < 1.0:
        egg_room(ctx, t)
        r = 150 + 900 * u
        big_egg(ctx, t, 960, 540 + 1.3 * r, r)
    if u > 0.003:
        ctx.push_group()
        ctx_t[0] = t
        fp_shell_view(ctx, t, extra=_mother_leaving(Sk("c6_mother", 0.1)) if t >= Sk("c6_mother", 0.0) - 0.5 else None)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp01((u - 0.5) * 2))
    Cd(ctx, t, "c6_father", 0.2, R("産卵", sz=60), 960, 110, pad=(40, 14), border=YEL)


def sc_c6_crack(ctx, t):
    p = ease(seg(t, Sk("c6_crack", 0.1), Ek("c6_crack") + 0.3))
    pa.fp_in_egg_under_father(ctx, t, view="shell", crack=p)
    Cd(ctx, t, "c6_crack", 0.25, [("約2か月", 64, YEL), ("（約70日）", 46, WHITE)], 520, 160, pad=(40, 14), border=YEL)


def sc_c6_gap(ctx, t):
    pa.fp_in_egg_under_father(ctx, t, view="gap")
    Cd(ctx, t, "c6_chick", 0.2, R("ふ化", sz=60), 960, 110, pad=(40, 14), border=YEL)


def sc_c6_pouch(ctx, t):
    pa.fp_from_pouch(ctx, t)
    Cd(ctx, t, "c6_50", 0.25, [("袋の中で", 48, WHITE), ("約50日", 76, YEL)], 960, 150, t1=Sk("c6_fast", 0.0) - 0.3, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_fast", 0.15, [("父親は繁殖地に来てから", 44, WHITE), ("約4か月食べていない", 76, YEL)], 960, 150, pad=(40, 16), border=YEL)


def sc_c6_creche(ctx, t):
    with chick_age_cap():
        pa.fp_in_creche(ctx, t)
    w = fade(t, Sk("c6_huddle", 0.1), 1.2)
    if w > 0.003:                                   # ヒナどうしの体温でぼんやり明るい（親の後ろに）
        g = cairo.RadialGradient(960, 620, 50, 960, 620, 1100)
        g.add_color_stop_rgba(0, 1.0, 0.95, 0.82, 0.40 * w)
        g.add_color_stop_rgba(1, 1.0, 0.95, 0.82, 0.0)
        ctx.set_source(g)
        ctx.rectangle(0, 0, W_, H_)
        ctx.fill()
    tf = Sk("c6_feed", 0.0)
    if t >= tf - 0.3:
        u = ease(seg(t, tf - 0.3, tf + 2.5))
        draw_emperor_front(ctx, 960, 925, 640 + 260 * u, a=fade(t, tf - 0.3, 0.6))
    Cd(ctx, t, "c6_creche", 0.3, R("ヒナの群れの中", sz=54), 330, 90, pad=(40, 14), border=YEL)


def sc_c6_edge(ctx, t):
    u = ease(seg(t, Sk("c6_dive", 0.5), Ek("c6_dive") + 0.5))
    ctx.save()
    ctx.translate(0, -700 * u)
    pa.fp_ice_edge(ctx, t)
    ctx.restore()
    if u > 0.003:
        ctx.push_group()
        pa.fp_underwater(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp01((u - 0.35) / 0.65))
    Cd(ctx, t, "c6_dec", 0.2, [("産卵から約7か月", 60, YEL), ("12月末", 48, WHITE)], 960, 140, t1=Sk("c6_dive", 0.5), pad=(40, 16), border=YEL)


def sc_c6_under(ctx, t):
    pa.fp_underwater(ctx, t)


def swim_view(ctx, t, t0):
    """一人称: 水の中を北へ泳ぐ（まわりの粒が後ろへ流れる）"""
    ctx.set_source(lin(0, 0, 0, H_, [(0, "#2f7fae", 1), (0.5, "#17507a", 1), (1, "#06192e", 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    rnd = random.Random(17)
    for i in range(70):
        ang = rnd.uniform(0, 2 * math.pi)
        ph = rnd.uniform(0, 1)
        u = ((t - t0) * 0.35 + ph) % 1.0
        r = 40 + 1100 * u * u
        x, y = 960 + math.cos(ang) * r, 470 + math.sin(ang) * r * 0.62
        disc(ctx, x, y, 2 + 9 * u, "#cfeeff", 0.15 + 0.4 * u)


def sc_c6_sea(ctx, t):
    t_turn = Sk("c6_turn", 0.0) - 0.2
    swim_view(ctx, t, SC_START["c6_sea"])
    if t >= t_turn:
        receding_ice(ctx, t, ease(seg(t, t_turn, Ek("c6_turn") + 1.0)), fade(t, t_turn, 0.6))
    wh = ease(seg(t, Sk("c6_end", 0.25), Ek("c6_end") + 1.2))          # 2026-11-10 統括: 0.97 だと札の上に下の文字が透けた
    whiten(ctx, wh)
    Cd(ctx, t, "c6_north", 0.3, R("北へ", sz=60), 960, 110, t1=Sk("c6_end", 0.0) - 0.3, pad=(40, 14), border=YEL)
    Cd(ctx, t, "c6_end", 0.1, R("海に出て約1か月", sz=56), 960, 110, t1=Sk("c6_8m", 0.0) - 0.3, pad=(40, 14), border=YEL)
    Cd(ctx, t, "c6_8m", 0.02, [("中央値の1羽", 48, WHITE), ("産卵から約8か月", 90, YEL)], 960, 330, pad=(50, 22), border=YEL)
    # 2026-11-10 初見チェック: 答えの場面が2行に割れて弱い → 同じ白い画面で、選択肢と赤丸まで続けて見せる
    t0 = Sk("c6_8m", 0.3)
    xs = (520, 960, 1400)
    for k, s_ in enumerate(OPTS):
        card(ctx, t, t0 + 0.12 * k, None, [(s_, 84, WHITE)], xs[k], 700, pad=(40, 18), bg="#27518a")
    g = fade(t, Sk("c6_ansopt", 0.75), 0.4)
    if g > 0.003:
        tset(ctx, REDC, g)
        ctx.set_line_width(12)
        ell(ctx, xs[0], 700, 230, 110)
        ctx.stroke()


def receding_ice(ctx, t, u, a):
    """振り向いた目線: 育った氷の縁（水の中から見た氷の裏）が、上の奥へ小さく遠ざかる"""
    if a <= 0.003:
        return
    sc_ = 1.0 - 0.78 * u
    cx, top = 960, -30 + 210 * u
    w, h = 1150 * sc_, 300 * sc_
    rnd = random.Random(5)
    ctx.move_to(cx - w, top - 10)
    n = 12                                   # 2026-11-10 Fable: 三角のギザギザ→不ぞろいな丸い凸凹（c6_under にそろえる）
    pts = [(cx - w + 2 * w * i / n, top + h * (0.55 + 0.35 * math.sin(i * 1.7) ** 2) + rnd.uniform(-14, 14) * sc_) for i in range(n + 1)]
    ctx.line_to(*pts[0])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx = (x0 + x1) / 2
        ctx.curve_to(x0 + (x1 - x0) * 0.25, y0 + h * 0.18, mx, max(y0, y1) + h * 0.16, x1, y1)
    ctx.line_to(cx + w, top - 10)
    ctx.close_path()
    ctx.set_source(lin(0, top, 0, top + h, [(0, mix("#ffffff", "#5f9cc4", 0.6 * u), a), (1, mix("#cfe8f5", "#4a86b0", 0.6 * u), a)]))
    ctx.fill()
    for i in range(4):                      # 氷のふちから差す光
        sx = cx - w * 0.6 + i * w * 0.4
        ctx.move_to(sx, top + h * 0.6)
        ctx.line_to(sx + 40 * sc_, top + h * 0.6)
        ctx.line_to(sx - 160 + 60 * i, H_)
        ctx.line_to(sx - 220 + 60 * i, H_)
        ctx.close_path()
        ctx.set_source(lin(0, top, 0, H_, [(0, "#e4f7ff", 0.18 * a * (1 - 0.6 * u)), (1, "#e4f7ff", 0.0)]))
        ctx.fill()


def swim_view_particles(ctx, t, a):
    rnd = random.Random(23)
    for i in range(40):
        x0, y0 = rnd.uniform(0, W_), rnd.uniform(0, H_)
        disc(ctx, (x0 - 60 * t) % W_, (y0 + 10 * math.sin(t + i)) % H_, rnd.uniform(2, 6), "#cfeeff", 0.3 * a)


def soft_light(ctx, t, k):
    ctx.set_source(lin(0, 0, 0, H_, [(0, mix("#eef3f8", "#fffaf0", k), 1), (1, mix("#dfe8f1", "#fff3dc", k), 1)]))
    ctx.rectangle(0, 0, W_, H_)
    ctx.fill()
    for i in range(18):
        x = (i * 113 + 20 * t) % W_
        y = 160 + 60 * math.sin(t * 0.5 + i) + (i % 5) * 150
        disc(ctx, x, y, 30 + 10 * (i % 3), "#ffffff", 0.35)


def sc_c6_answer(ctx, t):
    soft_light(ctx, t, fade(t, Sk("c6_luck", 0.1), 1.5))
    t0 = SC_START["c6_answer"] + 0.3
    xs = (520, 960, 1400)
    for k, s_ in enumerate(OPTS):
        card(ctx, t, t0 + 0.12 * k, None, [(s_, 84, WHITE)], xs[k], 330, pad=(40, 18), bg="#27518a")
    g = fade(t, Sk("c6_ansopt", 0.5), 0.4)
    if g > 0.003:
        tset(ctx, REDC, g)
        ctx.set_line_width(12)
        ell(ctx, xs[0], 330, 230, 110)
        ctx.stroke()
    tx(ctx, "冒頭の問い", 960, 160, 50, a=fade(t, t0, 0.3))
    Cd(ctx, t, "c6_3233", 0.3, vrows("海に出て1年以内に一生を終えた", "3,233羽", ""), 960, 680, pad=(44, 18), border=YEL)


def sc_c6_band2(ctx, t):
    band_card(ctx, t, 130, 880)
    yc = 300

    def fn(i, f):
        return (stage_kind(f, "bird"), 1.0)
    eband(ctx, BX0, BX1, yc, fn)
    for f0, f1, col, lab in ((0, FE, C_E, "卵のうち"), (FE, FC, C_C, "ヒナのうち"), (FC, FS, C_S, "海に出て1年以内"), (FS, 1, C_L, "1年を越えた")):
        rect(ctx, col, px_of(f0) + 2, 395, px_of(f1) - 2, 412)
        tx(ctx, lab, (px_of(f0) + px_of(f1)) / 2, 445, 40, STAGE_TXT[col])
    unit_tag(ctx, "/1万個", 1650, 185)
    tx(ctx, "色は、一生を終えた時期", BX0, 185, 40, align="left")   # 2026-11-10 統括: 帯の下の見出しが生き残りに読めないように
    mx = band_mark(ctx, BX0, BX1, yc, 0.5, a=fade(t, Sk("c6_ending", 0.2), 0.3), up=40, down=40)
    Cd(ctx, t, "c6_ending", 0.3, R("中央値の1羽　海に出て約1か月", sz=46), mx, 80, pad=(34, 12), border=YEL)
    a1 = fade(t, Sk("c6_6044", 0.4), 0.4)
    bracket(ctx, BX0, px_of(FN1), 510, REDC, a1)
    Cd(ctx, t, "c6_6044", 0.4, [("1歳になれず 6,044", 56, YEL)], 560, 640, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_6wari", 0.3, [("1歳までに 約6割", 56, YEL), ("1万個のうち", 40, WHITE)], 1300, 640, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_half", 0.3, R("1万個の半分以上は、1歳になれない", sz=46), 960, 810, pad=(34, 12), border=YEL)
    glow_box(ctx, t, px_of(FC) - 4, yc - 90, px_of(FS) + 4, 425, fade(t, Sk("c6_in3233", 0.3), 0.4))


THREE_X = (420, 960, 1500)


def sc_c6_three(ctx, t):
    band_card(ctx, t, 130, 880)
    for k, head in enumerate(("最悪", "中央値", "最良")):
        tset(ctx, "#eef4fa")
        rrect(ctx, THREE_X[k] - 235, 200, 470, 600, 24)
        ctx.fill()
        tx(ctx, head, THREE_X[k], 270, 60)
    Cd(ctx, t, "c6_worst", 0.4, vrows("ふ化せず", "1,774個", "1万個のうち", vs=80), THREE_X[0], 540, pad=(36, 18), border=YEL)
    Cd(ctx, t, "c6_best", 0.6, vrows("中央値の1羽", "約8か月", "", vs=80), THREE_X[1], 540, pad=(36, 18), border=YEL)
    Cd(ctx, t, "c6_best", 0.45, vrows("ヒナ10羽以上", "約2割", "大人1,081羽のうち", vs=80), THREE_X[2], 540, pad=(36, 18), border=YEL)


def sc_c6_b2(ctx, t):
    fp_adult_view(ctx, t)
    Cd(ctx, t, "c6_b2", 0.3, [("大人になった1,081羽の", 46, WHITE), ("中央値の1羽", 64, YEL)], 960, 150, pad=(40, 16), border=YEL)
    ta = Sk("c6_base2", 0.3)
    card(ctx, t, ta + 0.3, None, [("数える基準", 40, WHITE), ("大人になった1,081羽", 50, YEL)], 960, 330, pad=(36, 14), border=YEL)


def sc_c6_brood(ctx, t):
    fp_adult_view(ctx, t, egg=True)
    Cd(ctx, t, "c6_7y", 0.3, [("7歳", 76, YEL), ("初めての子育て", 48, WHITE)], 960, 160, t1=Sk("c6_may", 0.0) - 0.3, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_may", 0.2, R("毎年5〜6月", sz=60), 960, 120, t1=Sk("c6_kids", 0.0) - 0.3, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c6_kids", 0.2, [("子育て7回・ヒナ4羽", 64, YEL), ("どちらも中央値", 40, WHITE)], 960, 150, pad=(40, 16), border=YEL)


def sc_c6_end2(ctx, t):
    wh = ease(seg(t, Sk("c6_end2", 0.3), Ek("c6_end2") + 1.2)) * 0.97
    fp_adult_view(ctx, t, egg=False, white=wh)
    Cd(ctx, t, "c6_cmp", 0.2, [("14.4年", 90, YEL), ("大人1,081羽の寿命の中央値 14.6年", 46, WHITE)], 960, 440, pad=(50, 22), border=YEL)


def sc_c6_two(ctx, t):
    band_card(ctx, t, 150, 880)
    x0, wmax = 640, 1080
    rows = [("中央値の1羽", MED_DAYS / YEAR, "約8か月", C_S), ("大人の中央値の1羽", MED2_YEARS, "約14年", C_L)]
    t0 = SC_START["c6_two"] + 0.3
    for k, (lab, yrs, val, col) in enumerate(rows):
        y = 330 + k * 250
        tx(ctx, lab, 150, y, 44, align="left")
        p = ease(seg(t, t0 + 0.4 * k, t0 + 0.4 * k + 1.2))
        w = wmax * yrs / MED2_YEARS
        hbar(ctx, x0, y, w, 60, p, col)
        tx(ctx, val, x0 + max(w, 40) * p + (24 if k == 0 else -10), y + (0 if k == 0 else 75), 52, align="left" if k == 0 else "right",
           a=fade(t, t0 + 0.4 * k + 1.0, 0.3))
        g = fade(t, Sk("c6_both", 0.2), 0.3)
        if g > 0.003:
            disc(ctx, x0 + max(w, 40), y, 20 + 4 * math.sin(t * 5), GOLD, g)
    unit_tag(ctx, "/1万個", 1650, 205)
    Cd(ctx, t, "c6_two", 0.3, R("1万個の卵から、2つの一生", sz=50), 960, 780, pad=(36, 16), border=YEL)


# ============================================================
# 7 まとめ
# ============================================================
C7_X = (215, 590, 965, 1340, 1715)
C7_ROWS = [vrows("ふ化", "8,226", "", hs=44, vs=64), vrows("巣立ち", "5,321", "", hs=44, vs=64),
           vrows("1年を越えた", "2,088", "", hs=44, vs=64), vrows("5歳まで", "1,368", "", hs=44, vs=64),
           [("大人になった", 44, WHITE), ("1,081羽", 64, YEL), ("中央値約15年", 40, WHITE)]]


def sc_c7_answers(ctx, t):
    ice_bg(ctx, t)
    huddle(ctx, 960, 920, 1500, 32, seed=41)
    t0 = ch_start(7) + T_TITLE[7]
    for k, rows in enumerate(C7_ROWS):
        a = fade(t, t0 + 0.2 + 0.3 * k)
        if a > 0.003:
            panel(ctx, rows, C7_X[k], 210, a=a, pad=(22, 16))
    Cd(ctx, t, "c7_half", 0.3, [("中央値の1羽", 44, WHITE), ("約8か月", 76, YEL)], 560, 430, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c7_15", 0.2, [("大人になれば", 44, WHITE), ("約15年", 76, YEL)], 1360, 400, pad=(40, 16), border=YEL)
    Cd(ctx, t, "c7_15", 0.55, R("いちばん多く減るのは、最初の1年", sz=46), 1360, 540, pad=(34, 14))


def sc_c7_close(ctx, t):
    fp_shell_view(ctx, t)
    t0 = SC_START["c7_close"] + 0.3
    for k, s_ in enumerate(OPTS):
        card(ctx, t, t0 + 0.12 * k, None, [(s_, 70, WHITE)], OPT_X[k], OPT_Y, pad=(34, 14), bg="#27518a", border=YEL)
    card(ctx, t, t0, None, [(Q_TXT, 46, WHITE)], 960, 75, pad=(30, 12), border=YEL)
    Cd(ctx, t, "c7_last", 0.55, R("チャンネル登録・高評価", sz=40), 1600, 860, pad=(26, 10))


END_SUB = ["よければ", "チャンネル登録・高評価", "お願いします"]


def end_rows():
    return [("中央値の1羽", "約8か月"), ("大人になれば", "中央値 約15年"), ("大人になれる", "約1割")]


def sc_end(ctx, t):
    ice_bg(ctx, t, hor=600)
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    panel(ctx, [("答え", 80, YEL)], 490, 95, a=b, pad=(44, 8), r=20)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 46, WHITE), (val, 70, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        a = fade(t, t9 + 0.1, 0.4)
        draw_emperor(ctx, 1250, 905, 520, facing=1, a=a)
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1500, 300, a=fade(t, t9 + 0.3, 0.4))


# ============================================================
# 区切り（ここまで／ここから・小さなペンギンが氷の上を歩く）
# ============================================================
EC_LEFT = (f"ふ化 {N_HATCH:,}", f"巣立ち {N_FLEDGE:,}", f"1年を越えた {N_1Y:,}")
EC_RIGHT = ("1〜4歳の見えない数年", "大人になった鳥")
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
        pr_ = clamp01((t - self.t0 - 0.1) / 0.4)
        x0, x1 = (cx + 210, cx - 230) if back else (cx - 210, cx + 230)
        if pr_ > 0:
            arrow2(ctx, (x0, 340), (lerp(x0, x1, pr_), 340), REDC, 9, a, head=26)
        for i, s_ in enumerate(lines):
            text(ctx, s_, cx, 470 + i * 92, self._sizes[s_], WHITE, alpha=a)

    def _scene(self, ctx, t):
        paint_bg(ctx, EC_BG)
        fill(ctx, hexrgb("#ffffff", 0.18))
        ctx.rectangle(958, 60, 4, 760)
        ctx.fill()
        self._page(ctx, t, self.lx, "ここまで", self.left, True)
        self._page(ctx, t, self.rx, "ここから", self.right, False)
        rect(ctx, "#dfeaf3", 0, 905, W_, 918)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:                                      # 足あと（氷の上の小さな点）
                ctx.set_source_rgba(1, 1, 1, 0.35 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, 895 + (6 if i % 2 else -6), 6, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        pose = "walk" if int((t - self.t0) * 6) % 2 else "stand"
        draw_emperor(ctx, x, 905, 150, facing=1, pose=pose)


EC = FlatEyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None

# ============================================================
# 場面を並べる
# ============================================================
LAST_BEFORE_REST = "c3_opts"


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
        if Sk("c0_ans", 0.0) <= t < SC_END["c0_med"] + SC_OUT:
            grp(ctx, 1.0 - clamp01((t - SC_END["c0_med"]) / SC_OUT), lambda c, tt: corner_card(c, tt, Sk("c0_ans", 0.0)), t)
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


BELLS = [Sk("c1_ans", 0.3), Sk("c2_ans", 0.3), Sk("c3_ans", 0.3), Sk("c4_ans", 0.3), Sk("c5_ans", 0.3), Sk("c6_8m", 0.2)]


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
        ("1_open", "0:02 問い（殻の内側）", 2.0),
        ("2_opts", "選択肢の札", Ek("c0_pick") - 0.1),
        ("3_c1_ans", "問い1の答え ふ化 約8割", Sk("c1_ans2", 0.95)),
        ("4_c3_bars", "問い3 3本の棒・答え", Ek("c3_ans") + 0.4),
        ("5_rest", "区切り", T_RS0 + 2.0),
        ("6_c4_dark", "問い4 誰も見ていない数年", Ek("c4_nobody") + 0.3),
        ("7_c5_hist", "問い5 ヒナの数", Ek("c5_gap") + 0.3),
        ("8_c6_8m", "中央値の1羽 約8か月", Ek("c6_8m") + 0.3),
        ("9_c6_cmp", "大人の中央値の1羽 14.4年", Ek("c6_cmp") + 0.3),
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
    """本編の静止画一覧: 全場面（8秒ごとに途中のコマも）を 480px 幅で並べる。body_stills_480.png と12枚割りの p1〜"""
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
    rows = ["## 0 声に渡した文（読みの補正つき。sims/penguin-long.py --voicemd が出力）"]
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


WATCH = ["コウテイペンギン", "中央値", "何年", "1羽", "4羽", "5羽", "10羽", "3分の2", "約2割", "約4割", "約6割", "約9割", "約8割", "ふ化", "巣立ち",
         "巣立って", "縁", "間", "海氷", "流氷", "オオフルマカモメ", "14.4年", "14.6年", "1,081羽", "三つ目", "次", "殻", "袋"]


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


def _val(name, key, frac, off=0.0):
    t0 = Sk(key, frac) + off
    return lk.Cue(name, "value", t0, t0 + 0.3, ID[key])


ALL_CUES = [
    _fr("卵の山のカード(1万個)", "c0_egg", "c0_egg"), _fr("帯の枠(中央値)", "c0_med", "c0_med"), _fr("地図の枠(約3,000つがい)", "c1_map", "c1_map"),
    _fr("年表の枠(何十年)", "c1_rec", "c1_rec"), _fr("帯の枠(ふ化)", "c1_band", "c1_band"), _fr("雪のカード", "c1_snow", "c1_snow"),
    _fr("帯の枠(？)", "c1_unk", "c1_unk"), _fr("帯の枠(答え1)", "c1_ans", "c1_ans"), _fr("帯の枠(ヒナで数える)", "c2_base", "c2_base"),
    _fr("月の帯の枠", "c2_months", "c2_months"), _fr("年ごとの棒の枠", "c2_years", "c2_years"), _fr("海氷の道のりの枠", "c2_far", "c2_far"),
    _fr("帯の枠(巣立ち)", "c2_band", "c2_band"), _fr("帯の枠(海に出る前)", "c2_sum", "c2_sum"), _fr("帯の枠(若い鳥で数える)", "c3_base", "c3_base"),
    _fr("地図の枠(北へ)", "c3_map", "c3_north"), _fr("材料のカード", "c3_data", "c3_data"), _fr("帯の枠(1年を越えた)", "c3_band", "c3_band"),
    _fr("3本の棒の枠", "c3_bars", "c3_cmp"), _fr("帯の枠(2,088羽で数える)", "c4_base", "c4_base"), _fr("地図の枠(海の上)", "c4_map", "c4_sea"),
    _fr("年齢の帯の枠(1〜4歳)", "c4_dark", "c4_4y"), _fr("1歳〜4歳＝大人の枠", "c4_same", "c4_same"), _fr("帯の枠(5歳まで)", "c4_band", "c4_band"),
    _fr("2本の棒の枠(割合)", "c4_cmp", "c4_cmp"), _fr("帯の枠(大人を抜き出す)", "c5_pull", "c5_pull"), _fr("初めての子育ての棒の枠", "c5_first", "c5_ages"),
    _fr("大人の帯の枠", "c5_sorted", "c5_sort"), _fr("ヒナの数の棒グラフの枠", "c5_hist", "c5_vary"), _fr("帯の枠(中央値の卵)", "c6_sel", "c6_sel"),
    _fr("帯の枠(平均)", "c6_avg", "c6_avg"), _fr("帯の枠(段階の色)", "c6_band2", "c6_ending"), _fr("3つの枠(最悪・中央値・最良)", "c6_three", "c6_worst0"),
    _fr("2本の帯の枠", "c6_two", "c6_two"),
    _val("札「8,226」", "c1_band", 0.45), _val("札「1,774個」", "c1_nohatch", 0.2), _val("札「約2割」", "c1_2wari", 0.2), _val("札「ふ化 約8割」", "c1_ans", 0.3),
    _val("札「5,321」", "c2_band", 0.5), _val("札「2,905」", "c2_dead", 0.2), _val("札「巣立ち 約3分の2」", "c2_ans", 0.3), _val("札「4,679」", "c2_sum", 0.4),
    _val("札「2,088」", "c3_band", 0.5), _val("札「3,233」", "c3_dead", 0.2), _val("札「海に出た最初の1年」", "c3_ans", 0.3), _val("札「1,368」", "c4_band", 0.5),
    _val("札「5歳まで 1,368羽」", "c4_ans", 0.3), _val("札「1,081羽」", "c5_pull", 0.45), _val("札「約15年」", "c5_life", 0.25), _val("札「4羽」", "c5_kids", 0.2),
    _val("札「99羽」", "c5_zero", 0.5), _val("札「326羽」", "c5_20", 0.3), _val("札「産卵から約8か月」", "c6_8m", 0.2), _val("札「6,044」", "c6_6044", 0.4),
    _val("札「14.4年」", "c6_cmp", 0.2),
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
    ok |= {float(NB), float(N_HATCH), float(N_FLEDGE), float(N_1Y), float(N_5Y), float(N_AD), float(N_EGGD), float(N_CHD), float(N_SEAD),
           float(N_PRESEA), float(N_NOT1), float(N_KID0), float(N_KID5), float(N_KID10), float(N_20Y)}
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
    A(f"台本: 章は{len(CHAPS)}つ（0〜{LAST_CH}）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 8 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕（ ）が1つも混ざらない・読みの補正は空（台本の {表記|よみ} を使う）",
      not any(any(ch_ in v[1] for ch_ in "〔〕（）") for v in LINES.values()) and not READ_FIX)
    A("台本: 「守った決まり」「概要欄に書く前提」は声にしない",
      not any(("Labrousse" in v[1] or "Abadi" in v[1] or "前提" in v[1]) for v in LINES.values()))
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
    A(f"区切り: 小さなペンギンは左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ進む・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    # ---- 冒頭 ----
    nums0 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and it.id.startswith("c0_"):
            nums0 |= set(_re.findall(r"\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭（第0章）の声の数字は「1万」の1つだけ（{sorted(nums0)}）", nums0 == {"1"})
    # ---- 声の数字 = 試算（sims/penguin_rough.py）----
    exp = [("c1_band", f"{N_HATCH:,}羽"), ("c1_nohatch", f"{N_EGGD:,}個"), ("c1_2wari", f"約{ihalf(10 * N_EGGD / NB)}割"), ("c1_ans", f"約{ihalf(10 * N_HATCH / NB)}割"),
           ("c2_base", f"{N_HATCH:,}羽"), ("c2_band", f"{N_FLEDGE:,}羽"), ("c2_dead", f"{N_CHD:,}羽"), ("c2_sum", f"{N_PRESEA:,}個"),
           ("c3_base", f"{N_FLEDGE:,}羽"), ("c3_guess", f"{N_FLEDGE:,}羽"), ("c3_band", f"{N_1Y:,}羽"), ("c3_dead", f"{N_SEAD:,}羽"),
           ("c4_q", f"{N_1Y:,}羽"), ("c4_base", f"{N_1Y:,}羽"), ("c4_band", f"{N_5Y:,}羽"), ("c4_23", f"{N_1Y:,}羽"), ("c4_ans", f"{N_5Y:,}羽"),
           ("c5_pull", f"{N_AD:,}羽"), ("c5_base", f"{N_AD:,}羽"), ("c5_ages", f"5歳が{FIRST_AGE[5]}羽、6歳が{FIRST_AGE[6]}羽"), ("c5_7", f"{FIRST_AGE[7]}羽"),
           ("c5_medage", f"{int(FIRST_MED)}歳"), ("c5_life", f"約{ihalf(AD_LIFE)}年"), ("c5_brood", f"{int(AD_BROODS)}回"), ("c5_zero", f"{N_KID0}羽"),
           ("c5_five", f"{N_KID5}羽"), ("c5_ten", f"{N_KID10}羽"), ("c5_20", f"{N_20Y}羽"), ("c6_3233", f"{N_SEAD:,}羽"), ("c6_6044", f"{N_NOT1:,}羽"),
           ("c6_in3233", f"{N_SEAD:,}羽"), ("c6_worst", f"{N_EGGD:,}個"), ("c6_8m", f"約{ihalf(MED_DAYS / 30.4)}か月"), ("c6_end", f"約{ihalf(MED1_SEA_DAYS / 30.4)}か月"),
           ("c6_7y", f"{MED2[4]}歳"), ("c6_kids", f"{MED2[2]}回の子育てで"), ("c6_end2", f"{MED2_YEARS:.1f}年"), ("c6_cmp", f"{AD_LIFE:.1f}年")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が試算（penguin_rough.py）の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A(f"試算: 卵 {NB}・ふ化 {N_HATCH}・巣立ち {N_FLEDGE}・1年を越えた {N_1Y}・5歳 {N_5Y}・大人 {N_AD}・1歳になれず {N_NOT1}",
      (NB, N_HATCH, N_FLEDGE, N_1Y, N_5Y, N_AD, N_NOT1, N_EGGD, N_CHD, N_SEAD, N_PRESEA) == (10000, 8226, 5321, 2088, 1368, 1081, 6044, 1774, 2905, 3233, 4679))
    A(f"試算: 中央値の1羽 #{MED1_I} {MED1[1]}・{MED1[0]:.0f}日（海に出て{MED1_SEA_DAYS:.0f}日）／大人の中央値の1羽 #{MED2_I} {MED2_YEARS:.1f}年・子育て{MED2[2]}回・ヒナ{MED2[3]}羽・初めて{MED2[4]}歳",
      MED1_I == 751 and MED1[1] == "海に出て1年以内" and ihalf(MED_DAYS) == 247 and MED2_I == 5785 and (MED2[2], MED2[3], MED2[4]) == (7, 4, 7))
    A(f"試算: 大人の寿命の中央値 {AD_LIFE:.1f}年・子育て {AD_BROODS}回・ヒナ {AD_KIDS}羽・ヒナ0羽 {N_KID0}・5羽以上 {N_KID5}・10羽以上 {N_KID10}・20年以上 {N_20Y}・ヒナの数の合計 {sum(KID_COUNTS)}",
      f"{AD_LIFE:.1f}" == "14.6" and (AD_BROODS, AD_KIDS, N_KID0, N_KID5, N_KID10, N_20Y) == (7, 4, 99, 507, 208, 326) and sum(KID_COUNTS) == N_AD)
    A(f"試算: 帯の割合は小さい順（卵 {FE:.3f} < ヒナ {FC:.3f} < 中央値 0.5 < 海に出て1年 {FS:.3f}）・中央値の1羽は「海に出て1年以内」に入る", FE < FC < 0.5 < FS)
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
        qf = [(t_, e) for t_, e in allt if e[0] == Q_TXT]
        q_first = min((t_ for t_, _e in qf), default=99.0)
        q_ok = bool(qf) and all(e[5] >= 40 and e[4] < 130 for _t, e in qf)
        A(f"冒頭: 上の小さな札「{Q_TXT}」が {q_first:.2f}秒から出る（40px 以上・画面の上 y<130）", 0.9 <= q_first <= 1.3 and q_ok)
        A(f"冒頭: 声は0.5秒から「あなた」（{S('c0_0'):.1f}秒）・最初の文は5秒以内に終わる（{E('c0_0'):.1f}秒）",
          txt("c0_you").startswith("あなた") and ID["c0_you"] == "c0_0" and E("c0_0") < 6.5)
        o_first = min((t_ for t_, e in allt if e[0] in OPTS), default=0.0)
        A(f"冒頭: 選択肢の札「1年未満」「5年」「15年」は2文目（{_ts(S(ID['c0_q']))}）から出る（初出 {o_first:.1f}秒）・声では言わない",
          o_first >= S(ID["c0_q"]) - 1e-6 and not any(o in split_reading(LINES[i][1])[0] for i in LINES if LINES[i][0] == 0 for o in OPTS))
        tokens = [("8,226", "c1_band"), ("1,774個", "c1_nohatch"), ("約2割", "c1_2wari"), ("ふ化 約8割", "c1_ans"), ("5,321", "c2_band"), ("2,905", "c2_dead"),
                  ("巣立ち 約3分の2", "c2_ans"), ("4,679", "c2_sum"), ("2,088", "c3_band"), ("3,233", "c3_dead"), ("海に出た最初の1年", "c3_ans"),
                  ("1,368", "c4_band"), ("5歳まで 1,368羽", "c4_ans"), ("1,081羽", "c5_pull"), (f"{FIRST_AGE[5]}羽", "c5_ages"), (f"{FIRST_AGE[7]}羽", "c5_7"),
                  ("約15年", "c5_life"), ("7回", "c5_brood"), ("4羽", "c5_kids"), (f"{N_KID0}羽", "c5_zero"), (f"5羽以上 {N_KID5}羽（約半分）", "c5_five"),
                  (f"{N_KID10}羽（約2割）", "c5_ten"), ("326羽", "c5_20"), ("産卵から約8か月", "c6_8m"), ("1歳になれず 6,044", "c6_6044"), ("14.4年", "c6_cmp")]
        for tok, key in tokens:
            n_ = LINES[ID[key]][0]
            fr_ch = [f for f in frames if S(f"ch{n_}") <= f[0]]
            ft = first_seen(fr_ch, lambda s_, e, tok=tok: s_ == tok)
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        # 答えの前に、答えの向き（何割・何羽）を出さない: 各章の「答えです」の前に、その章の答えの数の札が出ていない
        for n_, key, toks in ((1, "c1_band", ("8,226", "約8割", "1,774個", "約2割")), (2, "c2_band", ("5,321", "2,905", "約3分の2")),
                              (3, "c3_band", ("2,088", "3,233")), (4, "c4_band", ("1,368",)), (5, "c5_pull", ("1,081羽", "約15年"))):
            early = sorted({e[0] for t_, e in allt if S(f"ch{n_}") <= t_ < S(ID[key]) - 0.3 and any(tk in e[0] for tk in toks)})
            A(f"答えの前（問い{n_}の数え始め {_ts(S(ID[key]))} より前）に、答えの数の札を出さない: {early}", not early)
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
        units = sorted({e[0] for t_, e in allt if e[0] in ("/1万個", "/1,081羽")})
        A(f"分母の札（/1万個・/1,081羽）が出る: {units}", units == ["/1,081羽", "/1万個"])
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
          6.0 <= DUR - T_ES <= 8.0 and T_ES > Ek(LAST_KEY) - 1e-6)
        end_t = min(DUR - 0.2, T_ES + 2.0)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A("終了画面に 答え3つ・登録の札が出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
    flat_ = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat_)
    print(f"場面の照合 {len(flat_)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat_)


def contrast_audit_run(min_ratio=4.5):
    """文字と、そのすぐ後ろの色のコントラスト（sims/contrast_audit.py の測り方。mp4 を使わず draw から直接描く）。out/penguin-long/contrast_audit.md"""
    import importlib.util
    import pickle
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


# ============================================================
# 字幕と足もとのかぶり
# ============================================================
def fig_check(step=0.25):
    """字幕が出ているコマで、字幕の帯の上端より下にペンギンの足（左右は身長の±18%）が来ていないかを全コマで数える"""
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
    lines_ = ["# 字幕の帯とペンギンの足もと", "", f"かぶり {len(rows)} か所（場面・位置ごと）", ""]
    for (nm, fx, fy), (t, top) in rows:
        lines_.append(f"- {_ts(t)} {nm} x≈{fx} 足 y={fy}（字幕の帯の上端 {top:.0f}）")
    out.write_text(chr(10).join(lines_) + chr(10), encoding="utf-8")
    print(f"字幕の帯とペンギンの足もと: かぶり {len(rows)} か所（立っているペンギン・群れを {n_fig} 件ぶん測定） → {out}")
    for r_ in lines_[4:30]:
        print(" ", r_)
    return len(rows)


def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if "--motion" in args:
        sp_ = still_spans()
        print("同じ絵の長い区間: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:14]))
        return
    if not any(a in args for a in ("--anchors", "--readings", "--scenecheck", "--stills", "--sheet", "--voicemd", "--figcheck", "--contrast",
                                     "--docs", "--render")):
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
            stills_sheet(OUT / "stills", still_list(), cols=3, sheet_name="stills_key_480.png")
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
