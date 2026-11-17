"""昭和の団地の抽選（横型ロング）— 2026-11-02 作成。場面（描画・声の並び・照合・静止画）。

  python -X utf8 sims/danchi-long.py --fake-voice --scenecheck     場面の照合（偽の声の長さで）
  python -X utf8 sims/danchi-long.py --fake-voice --stills         要所の静止画6枚と 480px の一覧（out/danchi-long/stills/・stills_480.png）
  python -X utf8 sims/danchi-long.py --fake-voice --stills --at 12.5,40   好きな時刻の静止画（out/danchi-long/scene_work/）
  python -X utf8 sims/danchi-long.py --fake-voice --readings       読みの一覧（scene_work/readings.log。--real-readings で AivisSpeech の読みも）
  python -X utf8 sims/danchi-long.py --fake-voice --anchors        合図の時刻・場面の一覧
  python -X utf8 sims/danchi-long.py --scenecheck                  本番の声で照合（frames_real.pkl を保存。check-long が読む）
  python -X utf8 sims/danchi-long.py                               本番の書き出し（第2段階。AivisSpeech を起動してから）

台本: publish/danchi-long/narration_B.md（統括が決定。文は変えない）。「## 0」より後の「- 」の行をそのまま読む。
数字: out/danchi-long/data.json（sims/danchi_model.py が出したもの）。1万人の並びは danchi_model.geometric を同じ種で呼んで取り出す
      （data.json と同じになることを照合で確かめる。模型は作り直さない）。
人と団地の絵: sims/danchi_people.py（平塗り・輪郭線なし。うすい青＝まだ当たっていない人、オレンジ＝当たった人・あなた）。
見た目の手本: out/danchi-long/samples/（単色の地の平たい絵）。地は章ごとに1色。文字は太いゴシック（メイリオ太字）で白か黄色。
土台（台本の読み込み・声の時間割・--fake-voice・--scenecheck・--stills・--readings・場面の切りかえの間・frames_real.pkl）は
sims/hikyaku-long.py をまねた。区切り（ここまで／ここから・カメが歩く）は engine/longkit.py の Eyecatch を平たい地に描き直したもの。
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

SLUG = "danchi-long"
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

import danchi_model as dm  # noqa: E402  模型（作り直さない）
from danchi_people import KINDS as P_KINDS, draw_danchi, draw_person, draw_person_reach, mix  # noqa: E402

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
# 台本の読み込み（hikyaku-long.py と同じ）
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
            cur = None                     # 番号のない見出し（「字数と区切りの位置」など）から先は台本ではない
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
    # 「## 守った決まり」などの番号のない見出しは章にしない。番号つきの章だけ
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


# ---- 読みの補正（AivisSpeech が読み違えた所。--real-readings で確かめた 2026-11-02）----
#   台本（narration_B.md）は統括の決定なので書きかえない。声に渡すときだけ {表記|よみ} を足す（画面・字幕の字は変わらない）。
#   ひらがなの読みは助詞とまちがえて切られる（「で・は・いれた」）ので、そういう所はカタカナで渡す。
#   (台本の字, 置きかえ, 台本に出る回数)。回数が合わなければ止める（台本が変わったら見直す）
READ_FIX = [
    ("1万人で試すと", "{1万人|イチマンニン}で試すと", 1),               # イチバンニン → いちまんにん
    ("年のわりに", "{年|とし}のわりに", 1),                               # ネンノワリニ → としのわりに
    ("人を積みます", "{人|ひと}を積みます", 1),                           # ニンオ → ひとを
    ("100人ぶんです", "{100人|ひゃくにん}ぶんです", 1),                   # ヒャクジンブン → ひゃくにんぶん
    ("並べて比べます", "{並べて|ならべて}比べます", 1),                   # ナベテ → ならべて
    ("約7年半です", "{約7年半|やくななねんはん}です", 1),                 # ヤクナナトシナカ → やくななねんはん
    ("同じくじです", "{同じ|おなじ}くじです", 1),                         # ドオジクジ → おなじくじ
    ("早く入れるのでしょうか", "早く{入れる|ハイレル}のでしょうか", 2),   # 以下「入れる（はいれる）」をイレルと読む所
    ("抽選なしで入れた例", "抽選なしで{入れた|ハイレタ}例", 1),
    ("最初の募集で入れます", "最初の募集で{入れます|ハイレマス}", 1),
    ("優先して入れます", "優先して{入れます|ハイレマス}", 1),
    ("みんな早く入れる、と", "みんな早く{入れる|ハイレル}、と", 1),
    ("52回で入れました", "52回で{入れました|ハイレマシタ}", 1),
    ("募集は年4回", "募集は{年4回|ネンヨンカイ}", 1),                     # トシヨンカイ → ねんよんかい
    ("何と引きかえにしたのでしょうか", "{何と|ナニト}引きかえにしたのでしょうか", 1),   # ナント → なにと
    ("半分の人が入れるまで", "半分の人が{入れる|ハイレル}まで", 1),         # イレル → はいれる
    ("問い1と同じくじなので", "問い1と{同じ|おなじ}くじなので", 1),         # ドオジクジ → おなじくじ
    ("毎回入れる人の数は", "毎回{入れる人|ハイレルヒト}の数は", 1),         # イレル → はいれる
    ("{51.4倍|ごじゅういってんよんばい}", "{51.4倍|ゴジュウイッテンヨンバイ}", 1),   # 台本のよみ（ひらがな）だと「ヨンバ/イノママ」と切れる
]
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


VOICE_PAUSES = (0.0, 0.10)    # 2026-11-06 読点は元の声の間のまま。文の間だけ少し足す。v3 で語の途中には入らない
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
# 文字は太いゴシック（手本と同じメイリオの太字）。手書き体（Klee One）は使わない
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
    # 0 何回目で当たる？
    "c0_q": (0, "何回目で当たりますか"), "c0_51": (0, "ひと部屋に、51人"), "c0_you": (0, "あなたも、申し込みました"), "c0_lose1": (0, "結果は、落選です"),
    "c0_next": (0, "次の募集に"), "c0_lose2": (0, "また、落選です"), "c0_lose3": (0, "その次も、落選です"), "c0_10k": (0, "1万人で試すと"),
    "c0_cond": (0, "条件は、画面の"), "c0_pre": (0, "問いに入る前に"),
    # 1 当時の団地
    "c1_old": (1, "古い建物"), "c1_ako": (1, "あこがれの住まい"), "c1_dk": (1, "ダイニングキッチンです"), "c1_sep": (1, "寝る部屋が、分かれました"),
    "c1_bath": (1, "水洗トイレ"), "c1_zoku": (1, "と呼ばれました"), "c1_work": (1, "働き盛り"), "c1_window": (1, "押し寄せました"),
    "c1_51": (1, "51人が集まりました"), "c1_freq": (1, "どのくらいの間隔で"), "c1_4": (1, "年4回でした"), "c1_unk": (1, "分かっていません"),
    "c1_set": (1, "と置きます"),
    # 2 運だけなら
    "c2_intro": (2, "最初の問いです"), "c2_ratio": (2, "部屋の数の何倍か"), "c2_cont": (2, "のまま、続くとします"), "c2_kuji": (2, "51人に1人が当たるくじ"),
    "c2_yoso": (2, "51回くらいで当たる"), "c2_10k": (2, "1万人が、当たるまで"), "c2_each51": (2, "まだ残っている人の"), "c2_first": (2, "最初のうちは"),
    "c2_shrink": (2, "群れが小さくなるほど"), "c2_sort": (2, "小さい順に並べた"), "c2_med": (2, "中央値は、37回目でした"), "c2_fast": (2, "予想の51回より"),
    "c2_hist": (2, "20回ごとに分けて"), "c2_h1": (2, "最初の20回までに"), "c2_h2": (2, "右へ行くほど"), "c2_h3": (2, "また人の山があります"),
    "c2_p90": (2, "122回以上"), "c2_80": (2, "80回申し込んでも"), "c2_mean": (2, "平均すると"), "c2_why": (2, "ごく一部の人が"),
    "c2_each": (2, "1人ずつ見ていきます"), "c2_b1": (2, "いちばん運のよかった人"), "c2_b2": (2, "最初の募集で、当たりました"), "c2_b3": (2, "50人に1人ほど"),
    "c2_m1": (2, "次に、中央値の人です"), "c2_m2": (2, "37回目に当たりました"), "c2_w1": (2, "いちばん運の悪かった人"), "c2_w2": (2, "一生のうちに"),
    "c2_three": (2, "差が開くのでしょうか"), "c2_mem": (2, "前の回を覚えていません"), "c2_same": (2, "51人に1人のままです"), "c2_help": (2, "少しも助けてくれない"),
    "c2_rec": (2, "実際の記録と比べます"), "c2_rec2": (2, "聞いた記録があります"), "c2_15": (2, "100人に15人ほど"), "c2_56": (2, "100人に56人です"),
    "c2_less": (2, "ずっと少ないのです"), "c2_who": (2, "もう入居できた人で"), "c2_notin": (2, "まだ当たっていない人は"), "c2_q": (2, "説明できるでしょうか"), "c2_hint": (2, "手がかりは"),
    "c2_next": (2, "続きは、次の問いで"),
    "c2_ans": (2, "答えです"),
    # 3 どの団地に
    "c3_intro": (3, "二つ目の問いです"), "c3_diff": (3, "団地によって"), "c3_pop": (3, "50倍を超える例"), "c3_low": (3, "15倍から17倍"),
    "c3_hi": (3, "抽選なしで入れた例"), "c3_area": (3, "住む地方でも"), "c3_where": (3, "どこに住むかでも"), "c3_dec": (3, "年々減ってきている"),
    "c3_yoso": (3, "結局は運しだい"), "c3_four": (3, "4人の申し込み方"), "c3_p1": (3, "1人目は"), "c3_p2": (3, "2人目は"), "c3_p3": (3, "3人目は"),
    "c3_p4": (3, "4人目は、倍率が下がるのを"), "c3_10k": (3, "1万人ずつ回しました"), "c3_r1": (3, "問い1と同じ37回です"), "c3_r2": (3, "中央値は11回でした"),
    "c3_lm": (3, "中央値の人を見ます"), "c3_l11": (3, "11回目に当たりました"), "c3_pm": (3, "まだ群れの中にいます"), "c3_p37": (3, "当たるのは、37回目です"),
    "c3_tail": (3, "運の悪い側も"), "c3_all": (3, "全員が最初の募集で"), "c3_add": (3, "もう1人を足します"), "c3_keep": (3, "すぐに申し込み、出し続けます"),
    "c3_21": (3, "中央値は、21回でした"), "c3_5y": (3, "約5年にあたります"), "c3_w4": (3, "4年待ってから"), "c3_14": (3, "中央値は、14回でした"),
    "c3_75": (3, "約7年半です"), "c3_none": (3, "1回も引いていません"), "c3_chance": (3, "少しずつありました"), "c3_faster": (3, "待つより、出し続けたほうが早いのです"),
    "c3_why": (3, "くじは引けるからです"), "c3_trade": (3, "何と引きかえにしたのでしょうか"), "c3_t1": (3, "長い待ちです"), "c3_t2": (3, "人気の団地をあきらめました"),
    "c3_t3": (3, "高い家賃を払い続けます"), "c3_t4": (3, "くじを引かなかった4年です"), "c3_rec": (3, "問い1で見た記録で"), "c3_ans": (3, "答えです"),
    "c3_you": (3, "あなたなら、どれを選びますか"),
    # 4 何度も落ちた人を先に入れたら
    "c4_intro": (4, "三つ目の問いです"), "c4_story": (4, "15回以上落ちた人の枠"), "c4_unk": (4, "その中身は分かっていません"), "c4_if": (4, "もしもの話です"),
    "c4_three": (4, "比べる決まりは、3つです"), "c4_A": (4, "Aは、決まりなし"), "c4_B": (4, "Bは、15回落ちた人を"), "c4_C": (4, "の決まりです。"),
    "c4_C10": (4, "10回落ちると"), "c4_10x": (4, "当たりやすさは、10倍です"), "c4_C20": (4, "20回落ちると"), "c4_yoso": (4, "みんな早く入れる、と思いませんか"),
    "c4_rooms": (4, "毎回の部屋の数を決めて"), "c4_new": (4, "新しく申し込む人も、群れに加わります"), "c4_Aon": (4, "Aの決まりなし、から見ます"),
    "c4_Asame": (4, "これは、問い1と同じくじです"), "c4_A37": (4, "半分の人が当たるまで、37回でした"), "c4_BC": (4, "次に、BとCです"), "c4_mean": (4, "約51回でした"),
    "c4_nope": (4, "縮まなかったのです"), "c4_m0": (4, "中央値はどうでしょう"), "c4_mA": (4, "問い1と同じくじなので"), "c4_mBC": (4, "回るので、51回"), "c4_nobi": (4, "むしろ、のびた"),
    "c4_why": (4, "平均が変わらない理由は"), "c4_noinc": (4, "決まりを変えても、増えません"), "c4_same": (4, "毎回入れる人の数は"),
    "c4_swap": (4, "誰かが早く入れば"), "c4_chair": (4, "椅子取りゲームと同じです"), "c4_seat": (4, "座る順番を変えても"), "c4_giveup": (4, "あきらめずに"),
    "c4_what": (4, "何を変えたのでしょうか"), "c4_who": (4, "変えたのは、運の差です"), "c4_all": (4, "BとCの中を"), "c4_line": (4, "列に並び替わりました"),
    "c4_52": (4, "52回で入れました"), "c4_saved": (4, "救われたのです"), "c4_none": (4, "最初の募集で当たる人は、いなくなります"), "c4_closed": (4, "部屋が残らないのです"),
    "c4_you": (4, "Bの決まりで申し込んだとします"), "c4_keep": (4, "落ち続けます"), "c4_15": (4, "やっと列に並びます"), "c4_wait": (4, "列の順番が来るのを待ちます"),
    "c4_lucky": (4, "運のいい人は、いなくなりました"), "c4_queue": (4, "順番待ちの列に変わりました"), "c4_split": (4, "早い人と遅い人に"), "c4_same2": (4, "ほぼ同じだけ待ちます"),
    "c4_detail": (4, "決まりの細かさで"), "c4_half": (4, "部屋の半分までにすると"), "c4_rooms2": (4, "変わらないのは、平均の待ちだけでした"), "c4_help": (4, "助けたい"), "c4_someone": (4, "どこかの誰かが引き受けます"),
    "c4_ans": (4, "答えです"), "c4_ans2": (4, "運の悪い人が救われて"),
    # 5 まとめ
    "c5_0": (5, "37回かかり"), "c5_1": (5, "平均の待ちは変わらず"), "c5_q": (5, "何回まで申し込みますか"), "c5_note": (5, "当時の一人ひとり"), "c5_sub": (5, "チャンネル登録"),
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
    ("c1_title", "ch:1", "sc_c1_title"), ("c1_plan", "c1_dk", "sc_c1_plan"), ("c1_zoku", "c1_zoku", "sc_c1_zoku"),
    ("c1_window", "c1_window", "sc_c1_window"), ("c1_freq", "c1_freq", "sc_c1_freq"), ("c1_unk", "c1_unk", "sc_c1_unk"),
    ("c2_title", "ch:2", "sc_c2_title"), ("c2_ratio", "c2_ratio", "sc_c2_ratio"), ("c2_kuji", "c2_kuji", "sc_c2_kuji"),
    ("c2_10k", "c2_10k", "sc_c2_10k"), ("c2_sort", "c2_sort", "sc_c2_sort"), ("c2_hist", "c2_hist", "sc_c2_hist"),
    ("c2_each", "c2_each", "sc_c2_each"), ("c2_best", "c2_b1", "sc_c2_best"), ("c2_medp", "c2_m1", "sc_c2_medp"),
    ("c2_worst", "c2_w1", "sc_c2_worst"), ("c2_three", "c2_three", "sc_c2_three"), ("c2_mem", "c2_mem", "sc_c2_mem"),
    ("c2_rec", "c2_rec", "sc_c2_rec"), ("c2_cmp", "c2_56", "sc_c2_cmp"), ("c2_ans", "c2_ans", "sc_c2_ans"),
    ("c3_title", "ch:3", "sc_c3_title"), ("c3_kinds", "c3_diff", "sc_c3_kinds"), ("c3_map", "c3_area", "sc_c3_map"),
    ("c3_dec", "c3_dec", "sc_c3_dec"), ("c3_yoso", "c3_yoso", "sc_c3_yoso"), ("c3_four", "c3_four", "sc_c3_four"),
    ("c3_10k", "c3_10k", "sc_c3_10k"), ("c3_low", "c3_lm", "sc_c3_low"), ("c3_tail", "c3_tail", "sc_c3_tail"),
    ("c3_all", "c3_all", "sc_c3_all"), ("c3_add", "c3_add", "sc_c3_add"), ("c3_five", "c3_keep", "sc_c3_five"), ("c3_race", "c3_w4", "sc_c3_race"),
    ("c3_trade", "c3_trade", "sc_c3_trade"), ("c3_ans", "c3_ans", "sc_c3_ans"),
    ("c4_title", "ch:4", "sc_c4_title"), ("c4_story", "c4_story", "sc_c4_story"), ("c4_rules", "c4_three", "sc_c4_rules"),
    ("c4_yoso", "c4_yoso", "sc_c4_yoso"), ("c4_setup", "c4_rooms", "sc_c4_setup"), ("c4_A", "c4_Aon", "sc_c4_A"),
    ("c4_mean", "c4_BC", "sc_c4_mean"), ("c4_rooms", "c4_why", "sc_c4_rooms"), ("c4_swap", "c4_swap", "sc_c4_swap"),
    ("c4_chair", "c4_chair", "sc_c4_chair"), ("c4_order", "c4_what", "sc_c4_order"), ("c4_line", "c4_all", "sc_c4_line"),
    ("c4_saved", "c4_saved", "sc_c4_saved"), ("c4_none", "c4_none", "sc_c4_none"), ("c4_you", "c4_you", "sc_c4_you"),
    ("c4_lucky", "c4_lucky", "sc_c4_lucky"), ("c4_split", "c4_split", "sc_c4_split"), ("c4_detail", "c4_detail", "sc_c4_detail"),
    ("c4_end0", "c4_rooms2", "sc_c4_end0"), ("c4_end", "c4_help", "sc_c4_end"), ("c4_ans", "c4_ans", "sc_c4_ans"),
    ("c5_answers", "ch:5", "sc_c5_answers"), ("c5_close", "c5_q", "sc_c5_close"), ("end", "end", "sc_end"),
]

# ---- 場面の切りかえの間（hikyaku-long.py と同じ）: 場面の最初の文の前の間を 1.05秒以上にする（0章は足さない）----
SCENE_GAP = 1.05
SCENE_KEYS = [k for _n, k, _f in SC_TABLE if k in ANCH]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c1_bath": 1.2, "c1_set": 1.6, "c2_m2": 2.4, "c3_p4": 2.2, "c3_r2": 1.4, "c3_tail": 1.6, "c3_5y": 1.9, "c4_C20": 1.4, "c4_A37": 1.8,
              "c4_who": 1.9, "c4_nope": 1.0, "c4_rooms2": 1.4, "c4_nobi": 1.3, "c4_saved": 1.9, "c4_queue": 1.5, "c2_b3": 1.5, "c3_where": 1.4, "c2_b2": 1.2, "c3_l11": 1.0, "c3_p37": 1.2, "c3_all": 1.0,
              "c3_faster": 1.2, "c4_52": 1.5, "c4_15": 0.8, "c4_wait": 0.8, "c4_half": 1.6, "c4_closed": 0.6, "c1_window": 0.6}


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
T_ES = Sk("c5_sub") - 0.3
T_IF = Sk("c4_if", 0.3)                         # 「もしもの話」で地の色が少し変わる

# ============================================================
# データ（data.json と、模型と同じ関数・同じ種で取り出した1万人）
# ============================================================
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
Q1 = dm.geometric(np.random.default_rng(dm.SEED), dm.RATIO)       # danchi_model.main と同じ最初のくじ ＝ 問い1の1万人
Q1S = np.sort(Q1)
D1, D2, D3 = RES["q1"], RES["q2"], RES["q3"]
HIST20 = RES["q1_hist20"]


def per100(counts):
    """1人＝100人の絵の人数（合計100になるよう最大剰余で丸める）"""
    raw = [c / 100 for c in counts]
    k = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - k[i], reverse=True)[:100 - sum(k)]:
        k[i] += 1
    return k


HIST_N = per100(HIST20)                      # [32, 22, 15, 10, 7, 4, 10]
ROUND_WIN = np.bincount(Q1, minlength=60)    # 回ごとに当たった人数


# ============================================================
# 見た目（平たい単色の地・太いゴシックの白と黄色）
# ============================================================
W_, H_ = lf.W, lf.H
WHITE, YEL, PALE, REDC = "#ffffff", "#ffe14a", "#d6e2f5", "#e8505b"
WAIT, WIN, BLDG, GRAYB = "#9db7df", "#f39a4a", "#e9dcc0", "#a3a39b"
GLOW = "#e6eefb"
PANEL = "#10284a"
SLIP = "#e7646c"
FY = 905                                       # 主役の足もと
PH = 380                                       # 主役の身長（画面の高さの 35%・3分の1 は 360px）
BGS = {0: "#1f4e8c", 1: "#2a6658", 2: "#1f4e8c", 3: "#4a3d7a", 4: "#22566a", 5: "#1f4e8c"}
BG_IF = "#3b3a6e"


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


def bg_color(t):
    ch = tl.chapter_at(t)
    n = CHAPS[ch[0]]["n"] if ch else 0
    col = BGS[n]
    if n == 4 and t >= T_IF:
        col = mix(BGS[4], BG_IF, clamp01((t - T_IF) / 0.8))
    if ch and n > 0 and t - ch[1] < 0.6:
        prev = BGS[CHAPS[ch[0] - 1]["n"]]
        if CHAPS[ch[0] - 1]["n"] == 4:
            prev = BG_IF
        col = mix(prev, col, clamp01((t - ch[1]) / 0.6))
    return col


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


def tri_down(ctx, x, y, s, col, a=1.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.move_to(x - s, y - s * 1.1)
    ctx.line_to(x + s, y - s * 1.1)
    ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill()


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


def cross(ctx, cx, cy, r, a=1.0, p=1.0, col=REDC, w=16):
    if p <= 0:
        return
    line2(ctx, (cx - r, cy - r), (cx - r + 2 * r * clamp01(p * 2), cy - r + 2 * r * clamp01(p * 2)), col, w, a)
    if p > 0.5:
        u = clamp01(p * 2 - 1)
        line2(ctx, (cx + r, cy - r), (cx + r - 2 * r * u, cy - r + 2 * r * u), col, w, a)


# ---------- 人（sims/danchi_people.py の draw_person を画像にして使い回す。見た目は同じ）----------
_SPR = {}


def person(ctx, x, y, h, kind="man", color=WAIT, phase=0.0, facing=1, pose="walk", a=1.0):
    if a <= 0.003:
        return
    hq = max(8, int(round(h)))
    ph = int(round((phase % 1.0) * 12)) % 12 if pose == "walk" else 0
    key = (kind, color, hq, facing, pose, ph)
    sp = _SPR.get(key)
    if sp is None:
        w, hh = int(hq * 0.9) + 12, int(hq * 1.16) + 12
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, hh)
        c = cairo.Context(surf)
        ox, oy = w / 2, hq * 1.09 + 6
        draw_person(c, ox, oy, hq, kind, color, phase=ph / 12, facing=facing, pose=pose)
        if len(_SPR) > 6000:
            _SPR.clear()
        _SPR[key] = sp = (surf, ox, oy)
    surf, ox, oy = sp
    sc = h / hq
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    ctx.set_source_surface(surf, -ox, -oy)
    ctx.paint_with_alpha(a)
    ctx.restore()


def walker(ctx, t, t0, t1, p0, p1, h, kind="man", c0=WAIT, c1=None, facing=None, a=1.0, vanish=False, appear=False):
    """p0 から p1 へ歩く人（t0〜t1）。歩く前は p0 で立ち、着いたら p1 で立つ（vanish=True なら着いたら入口に消える）。
    c1 を渡すと歩き出した時から c1 の色（当たった人はオレンジ）"""
    if t < t0 and appear:
        return
    u = seg(t, t0, t1)
    x, y = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
    fc = facing if facing is not None else (1 if p1[0] >= p0[0] else -1)
    col = c1 if (c1 and t >= t0) else c0
    al = a
    if vanish:
        al *= 1 - clamp01((t - t1) / 0.35)
        if t > t1 + 0.4:
            return
    if t0 <= t <= t1:
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        rate = (d / max(1e-6, t1 - t0)) / (0.62 * h)
        person(ctx, x, y, h, kind, col, phase=(t - t0) * rate, facing=fc, pose="walk", a=al)
    else:
        person(ctx, x, y, h, kind, col, phase=0.25, facing=fc, pose="walk" if t < t0 else "stand", a=al)


class Crowd:
    """群れ（draw_crowd と同じ並べ方）。spots は奥から手前の順。draw で色・隠す人・歩きを選べる"""

    def __init__(self, box_, n, size, seed=1, facing=1, kinds=P_KINDS):
        x0, y0, x1, y1 = box_
        rnd = random.Random(seed)
        w, hgt = x1 - x0, y1 - y0
        ratio = w / max(hgt, 1)
        rows = max(1, round(math.sqrt(n / ratio * 1.6)))
        cols = math.ceil(n / rows)
        dx, dy = w / max(cols, 1), hgt / max(rows, 1)
        spots, k = [], 0
        for r in range(rows):
            for c in range(cols):
                if k >= n:
                    break
                off = (dx / 2) * (r % 2)
                spots.append((x0 + c * dx + off + rnd.uniform(-dx * 0.12, dx * 0.12), y0 + (r + 1) * dy + rnd.uniform(-dy * 0.08, dy * 0.08), kinds[k % len(kinds)]))
                k += 1
        spots.sort(key=lambda s_: s_[1])
        self.spots = spots
        self.n = len(spots)
        self.size = size
        self.facing = facing
        prn = random.Random(seed + 77)
        self.phase = [prn.random() for _ in spots]

    def draw(self, ctx, t=0.0, color=WAIT, colors=None, hide=(), dx=0.0, dy=0.0, walk=False, a=1.0, facing=None, rate=1.6, alpha=None, size=None):
        fc = self.facing if facing is None else facing
        sz = self.size if size is None else size
        for i, (x, y, kd) in enumerate(self.spots):
            if i in hide:
                continue
            col = colors.get(i, color) if colors else color
            al = a * (alpha(i) if alpha else 1.0)
            ph = self.phase[i] + (t * rate if walk else 0.0)
            person(ctx, x + dx, y + dy, sz, kd, col, phase=ph, facing=fc, pose="walk", a=al)

    def right_order(self):
        return sorted(range(self.n), key=lambda i: -self.spots[i][0])


# ---------- 団地（draw_danchi を画像にして使い回す）----------
_DAN = {}


def danchi(ctx, x, y, w, h, color=BLDG, floors=5, units=8, a=1.0, door=True):
    """(x, y) は左下。入口（ドア）を1階の真ん中に描く。戻り値は入口の (x, y)"""
    if a > 0.003:
        key = (int(w), int(h), color, floors, units)
        sp = _DAN.get(key)
        if sp is None:
            pad = int(h * 0.08) + 4
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w * 1.04) + 2 * pad, int(h * 1.06) + 2 * pad)
            c = cairo.Context(surf)
            draw_danchi(c, pad + w * 0.02, pad + h * 1.06, w, h, color, floors=floors, units=units)
            _DAN[key] = sp = (surf, pad + w * 0.02, pad + h * 1.06)
        surf, ox, oy = sp
        ctx.set_source_surface(surf, x - ox, y - oy)
        ctx.paint_with_alpha(a)
        if door:
            fh = h * 0.92 / floors
            dw = min(w / units * 0.7, 70)
            box(ctx, x + w / 2 - dw / 2, y - fh * 0.78, x + w / 2 + dw / 2, y, mix(color, "#000000", 0.55), a, r=4)
    return (x + w / 2, y)


def win_rect(x, y, w, h, floors, units, f, i):
    fh = h * 0.92 / floors
    uw = w / units
    fy = y - h * 0.96 + f * fh
    ux = x + i * uw
    return (ux + uw * 0.18, fy + fh * 0.18, uw * 0.64, fh * 0.42)


def slips(ctx, x, ybase, n, a=1.0, w=96, step=11, col=SLIP, seed=5, sway=0.0):
    """落選の札の山（文字なしの赤い札を積む）。(x, ybase) は山の下の真ん中"""
    if n <= 0 or a <= 0.003:
        return
    rnd = random.Random(seed)
    for k in range(int(n)):
        off = rnd.uniform(-9, 9) + sway * math.sin(k * 0.7)
        yy = ybase - k * step
        box(ctx, x - w / 2 + off, yy - step + 1, x + w / 2 + off, yy, mix(col, "#000000", 0.1 * (k % 2)), a, r=3)
        fill(ctx, hexrgb("#ffffff", 0.55 * a))
        ctx.rectangle(x - w / 2 + off + 10, yy - step * 0.6, w * 0.45, 2.5)
        ctx.fill()


def lose_card(ctx, x, y, n_back=0, a=1.0, size=56):
    """赤い札「落選」。n_back 枚ぶん、文字なしの札を後ろに重ねる"""
    for k in range(n_back, 0, -1):
        box(ctx, x - 92 + 16 * k, y - 46 - 12 * k, x + 92 + 16 * k, y + 46 - 12 * k, mix(REDC, "#000000", 0.18 + 0.08 * k), a, r=12)
    panel(ctx, [("落選", size, WHITE)], x, y, a=a, bg=REDC, pad=(42, 14))


def kuji_box(ctx, cx, cy, w, a=1.0):
    """くじの箱（文字なし）。丸い穴から玉が出る"""
    h = w * 0.8
    box(ctx, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, "#b8473f", a, r=18)
    box(ctx, cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2 + 22, "#d9655a", a, r=12)
    fill(ctx, hexrgb("#5a1f1b", a))
    ctx.arc(cx, cy - h * 0.05, w * 0.16, 0, 2 * math.pi)
    ctx.fill()


def ball(ctx, x, y, r, col, a=1.0):
    fill(ctx, hexrgb(col, a))
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, hexrgb("#ffffff", 0.35 * a))
    ctx.arc(x - r * 0.3, y - r * 0.3, r * 0.3, 0, 2 * math.pi)
    ctx.fill()


def grid100(ctx, x0, y0, n_on, a=1.0, step=56, size=70, stepx=48, on=WIN, off=WAIT, t_on=None, t=0.0, cols=13):
    """100人の絵（13列×8段のかたまり）。n_on 人に色。t_on を渡すと、その時刻から1人ずつ色が付く"""
    for k in range(100):
        r, c = divmod(k, cols)
        lit = k < n_on and (t_on is None or t >= t_on + k * 0.04)
        person(ctx, x0 + c * stepx, y0 + r * step, size, P_KINDS[(k * 3) % 5], on if lit else off, phase=0.3 + 0.1 * (k % 4), facing=1, pose="walk", a=a)


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


# ---- 章カード（平たい板・問いの番号は黄色）----
CARD_BY_N = {1: ["当時の団地は、", "どんな場所？"], 2: ["問い1", "運だけなら、", "何回目で当たる？"],
             3: ["問い2", "どの団地に申し込むと、", "早く入れる？"], 4: ["問い3", "何度も落ちた人を先に入れたら、", "みんな早く入れる？"], 5: ["まとめ"]}
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


# ============================================================
# 0 何回目で当たる？
# ============================================================
QTXT = "何回目で 当たる？"
OPEN_CROWD = Crowd((430, 390, 1290, 830), 51, 112, seed=11, facing=1)
D_X, D_W, D_Y, D_H = 1400, 460, 660, 330            # 冒頭の団地（左下 x・幅・地面・高さ）
YOU_X = 385
PAN1 = (T("c0_next", 0.0, -0.05), 1.9)
PAN2 = (T("c0_lose3", 0.0, -0.1), 0.85)
W1 = OPEN_CROWD.right_order()[1]                     # 1回目に当たる人（群れの右の手前寄り）
W2 = OPEN_CROWD.right_order()[4]
T_W1 = (T("c0_lose1", 0.0, 0.15), T("c0_lose1", 0.0, 1.65))
T_W2 = (PAN2[0] + PAN2[1] + 0.05, PAN2[0] + PAN2[1] + 1.25)


def pan_x(t):
    return 1920 * (ease(seg(t, PAN1[0], PAN1[0] + PAN1[1])) + ease(seg(t, PAN2[0], PAN2[0] + PAN2[1])))


def panning(t):
    return PAN1[0] <= t <= PAN1[0] + PAN1[1] or PAN2[0] <= t <= PAN2[0] + PAN2[1]


def sc_open(ctx, t):
    px = pan_x(t)
    # 団地（1回目・2回目・3回目の募集）。それぞれに札「部屋 1」
    for k in range(3):
        dx = D_X + 1920 * k - px
        if -600 < dx < 2000:
            danchi(ctx, dx, D_Y, D_W, D_H, BLDG, floors=4, units=6)
    # 札「部屋 1」は受付（いまの募集）の札。画面に止めておき、団地だけが流れる
    panel(ctx, [("部屋 1", 52, YEL)], D_X + D_W / 2, 270, a=fade(t, 0.05, 0.3))
    # 当たった人（群れから歩き出して団地へ・オレンジに変わる）
    hide = set()
    if t >= T_W1[0]:
        hide.add(W1)
    if t >= T_W2[0]:
        hide.add(W2)
    walk_now = panning(t)
    # 1人ずつ数える光（ひと部屋に、51人）
    t_g0, t_g1 = T("c0_51", 0.05), T("c0_51", 0.92)
    cols = {}
    order = sorted(range(OPEN_CROWD.n), key=lambda i: (OPEN_CROWD.spots[i][0] // 120, OPEN_CROWD.spots[i][1]))
    for j, i in enumerate(order):
        tg = t_g0 + j * (t_g1 - t_g0) / OPEN_CROWD.n
        if tg <= t < tg + 0.45:
            cols[i] = "#fff3b8"
        elif t >= tg:
            cols[i] = GLOW if t < t_g1 + 1.2 else WAIT
    OPEN_CROWD.draw(ctx, t, colors=cols, hide=hide, walk=walk_now)
    p_spot = OPEN_CROWD.spots[W1]
    door = (D_X + D_W / 2, D_Y)
    if T_W1[0] <= t:
        walker(ctx, t, T_W1[0], T_W1[1], p_spot[:2], (door[0] - pan_x(t) if t > PAN1[0] else door[0], door[1]), 112, p_spot[2], c0=WAIT, c1=WIN, vanish=True)
    p2 = OPEN_CROWD.spots[W2]
    if T_W2[0] <= t:
        walker(ctx, t, T_W2[0], T_W2[1], p2[:2], (D_X + 3840 + D_W / 2 - pan_x(T_W2[0]), D_Y), 112, p2[2], c0=WAIT, c1=WIN, vanish=True)
    label(ctx, "申込み 51人", 860, 312, 56, WHITE, a=fade(t, 0.3, 0.4))
    # あなた（オレンジ・画面の高さの3分の1以上）が群れに歩いて混ざる
    ty0, ty1 = T("c0_you", 0.0), T("c0_you", 0.0) + min(Dk("c0_you") + 0.2, 2.0)
    if t >= ty0:
        if t <= ty1:
            walker(ctx, t, ty0, ty1, (-220, FY), (YOU_X, FY), PH, "man", c0=WIN)
        else:
            person(ctx, YOU_X, FY, PH, "man", WIN, phase=(t * 1.5) if walk_now else 0.25, facing=1, pose="walk" if walk_now else "stand")
    # 落選の札（1枚・2枚・3枚）
    tl1, tl2, tl3 = T("c0_lose1", 0.35), T("c0_lose2", 0.3), T("c0_lose3", 0.55)
    if t >= tl1:
        nb = (1 if t >= tl2 else 0) + (1 if t >= tl3 else 0)
        lose_card(ctx, YOU_X, 455, nb, a=fade(t, tl1, 0.25))
    tn = T("c0_next", 0.15)
    if t >= tn:
        panel(ctx, [("次の募集", 46, WHITE)], 760, 884, a=fade(t, tn))
    # 左上に赤く「昭和41年」、右に問い
    panel(ctx, [("昭和41年", 84, WHITE)], 70, 112, align="left", bg=REDC, pad=(30, 12))
    label(ctx, QTXT, 1385, 112, 100, YEL)


C10K = Crowd((60, 380, 1300, 900), 230, 64, seed=21, facing=1)
T_COND0 = max(T("c0_cond", 0.0, 0.25), 30.3, T("c0_10k", 0.62) + 3.3)   # 条件の札は 0:30 のあと・37回の札を読みきってから
D10 = (1420, 780, 440, 400)
_r10 = C10K.right_order()
STREAM = []                                          # (人, 歩き出す時刻, 着く時刻)


def _stream():
    t0, t1 = bz("c0_10k") + 0.6, T_COND0 - 1.8
    k, tt = 0, t0
    rnd = random.Random(4)
    pool_ = _r10[:120]
    rnd.shuffle(pool_)
    while tt < t1 and k < len(pool_):
        i = pool_[k]
        x, y, _kd = C10K.spots[i]
        d = math.hypot(D10[0] + D10[2] / 2 - x, D10[1] - y)
        STREAM.append((i, tt, tt + max(0.9, d / 420)))
        k += 1
        tt += 0.16


_stream()


def sc_c0_10k(ctx, t):
    hide = {i for i, a_, _b in STREAM if t >= a_}
    dim = 1 - 0.78 * fade(t, T_COND0 - 0.45, 0.5)           # 条件の札が出るとき、群れをうすくする
    danchi(ctx, D10[0], D10[1], D10[2], D10[3], BLDG, floors=5, units=6, a=dim)
    C10K.draw(ctx, t, hide=hide, a=dim)
    door = (D10[0] + D10[2] / 2, D10[1])
    for i, a_, b_ in STREAM:
        if a_ <= t <= b_ + 0.4:
            x, y, kd = C10K.spots[i]
            walker(ctx, t, a_, b_, (x, y), door, 64, kd, c0=WAIT, c1=WIN, vanish=True)
    t_off = T_COND0 - 0.35
    panel(ctx, [("1万人", 64, YEL)], 70, 125, align="left", pad=(30, 12), a=out_fade(t, t_off, 0.3))
    tv = T("c0_10k", 0.62)
    if t >= tv:
        panel(ctx, [("半分の人が当たるまで 37回", 74, YEL)], 1010, 130, a=fade(t, tv, 0.3) * out_fade(t, t_off, 0.3), border=YEL)
    tv2 = tv + 0.7
    if t >= tv2:
        panel(ctx, [("中央値 37回目", 48, WHITE)], 1010, 262, a=fade(t, tv2, 0.3) * out_fade(t, t_off, 0.3))
    sc_c0_cond(ctx, t)


COND_ROWS = ["倍率は昭和41年の東日本の公団の新規賃貸の平均 51.4倍", "この倍率のまま、1回に1つ申し込むと仮定", "当たるまであきらめないと仮定"]
T_COND = [T_COND0 + 0.6 * k for k in range(3)]
TAGS = [(["問い1", "運だけなら、", "何回目で当たる？"], 330), (["問い2", "どの団地に申し込むと、", "早く入れる？"], 960),
        (["問い3", "何度も落ちた人を", "先に入れたら？"], 1590)]


def sc_c0_cond(ctx, t):
    for k, s_ in enumerate(COND_ROWS):
        if t >= T_COND[k]:
            panel(ctx, [(s_, 50, WHITE if k else YEL)], 100, 140 + 104 * k, align="left", a=fade(t, T_COND[k]))
    tp = T("c0_pre", 0.0)
    for k, (rows, x) in enumerate(TAGS):
        tk = tp + 0.5 + 0.35 * k
        if t >= tk:
            panel(ctx, [(rows[0], 52, YEL)] + [(r_, 44, WHITE) for r_ in rows[1:]], x, 590, a=fade(t, tk))
    if t >= tp + 0.1:
        panel(ctx, [("当時の団地", 60, PANEL)], 960, 815, a=fade(t, tp + 0.1), bg=YEL, pad=(40, 14))


# ============================================================
# 1 当時の団地は、どんな場所？
# ============================================================
BIG_D = (560, 870, 800, 560)


def sc_c1_title(ctx, t):
    x, y, w, h = BIG_D
    danchi(ctx, x, y, w, h, GRAYB, floors=5, units=10)
    u = ease(seg(t, T("c1_ako", 0.1), T("c1_ako", 0.1) + 1.4))
    if u > 0:
        ctx.save()
        ctx.rectangle(0, y - (h * 1.1) * u, W_, h * 1.1 * u + 40)
        ctx.clip()
        danchi(ctx, x, y, w, h, "#f6e7c4", floors=5, units=10)
        ctx.restore()
    tc = T("c1_ako", 0.35)
    if t >= tc:
        panel(ctx, [("あこがれの住まい", 72, YEL)], 960, 160, a=fade(t, tc))


PLAN = dict(x0=90, y0=150, x1=880, y1=880)
ROOMS = {"dk": (90, 150, 560, 560, "#d98b3a", "DK"), "bed1": (560, 150, 880, 515, "#5b8fd1", "寝室"), "bed2": (560, 515, 880, 880, "#5b8fd1", "寝室"),
         "bath": (90, 560, 330, 880, "#3fa7bd", "浴室"), "wc": (330, 560, 470, 880, "#3fa7bd", "トイレ")}


def sc_c1_plan(ctx, t):
    # 2DK を上から見た図（壁は白い線）
    label(ctx, "2DK を上から見た図", 485, 100, 46, PALE)
    box(ctx, 90, 150, 880, 880, mix(bg_color(t), "#000000", 0.25), r=6)
    td, ts, tb = T("c1_dk", 0.1), T("c1_sep", 0.15), T("c1_bath", 0.2)
    for k, (x0, y0, x1, y1, col, nm) in ROOMS.items():
        tt = td if k == "dk" else (ts if k.startswith("bed") else tb)
        if t >= tt:
            a = fade(t, tt, 0.4)
            box(ctx, x0 + 6, y0 + 6, x1 - 6, y1 - 6, col, a, r=4)
            label(ctx, nm, (x0 + x1) / 2, (y0 + y1) / 2 - (0 if k != "dk" else 120), 48 if k != "wc" else 40, WHITE, a=a)
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_line_width(10)
    ctx.rectangle(90, 150, 790, 730)
    ctx.stroke()
    if t >= td:
        # 食卓（上から見た丸いテーブル）
        a = fade(t, td, 0.4)
        fill(ctx, hexrgb("#8a5a2e", a))
        ctx.arc(330, 400, 85, 0, 2 * math.pi)
        ctx.fill()
    # 右: 家族が食卓につく
    tf = T("c1_sep", 0.2)
    fam = [("man", 1180, PH), ("woman", 1430, 360), ("kid", 1660, 270)]
    for k, (kd, x, h) in enumerate(fam):
        t0 = tf + 0.25 * k
        if t >= t0:
            walker(ctx, t, t0, t0 + 1.5, (x + 420, FY - 20), (x, FY - 20), h, kd, c0=WIN, facing=-1 if t < t0 + 1.5 else 1)
    if t >= tf:
        a = fade(t, tf, 0.4)
        box(ctx, 1040, 735, 1840, 790, "#8a5a2e", a, r=8)
        box(ctx, 1080, 790, 1110, 905, "#6e4523", a, r=4)
        box(ctx, 1770, 790, 1800, 905, "#6e4523", a, r=4)
        for x_ in (1150, 1420, 1650):
            fill(ctx, hexrgb("#ffffff", a))
            ctx.save()
            ctx.translate(x_ + 40, 725)
            ctx.scale(1.0, 0.35)
            ctx.arc(0, 0, 38, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()
    if t >= tb:
        panel(ctx, [("建設省の住宅局長の説明（昭和34年）", 42, YEL), ("公団は 寝室2つ＋DK＋浴室", 42, WHITE), ("公営は 原則お風呂なし", 42, WHITE)],
              1440, 240, a=fade(t, tb))


def sc_c1_zoku(ctx, t):
    door = danchi(ctx, 80, 800, 640, 500, BLDG, floors=5, units=8)
    for k, x in enumerate((900, 1200, 1500)):
        for j, (kd, h) in enumerate((("man", 220), ("woman", 205), ("kid", 150))):
            person(ctx, x + j * 80, 820, h, kd, WIN, phase=0.3, facing=-1, pose="stand", a=fade(t, bd("c1_zoku") + 0.4 + 0.2 * k))
    tc = T("c1_zoku", 0.3)
    if t >= tc:
        panel(ctx, [("団地族", 96, YEL)], 1340, 200, a=fade(t, tc), border=YEL)
    tw = T("c1_work", 0.15)
    if t >= tw:
        walker(ctx, t, tw, tw + 3.4, (door[0], FY), (1650, FY), PH, "man", c0="#e07f35", facing=1)
        x = lerp(door[0], 1650, seg(t, tw, tw + 3.4))
        box(ctx, x + 18, FY - 150, x + 78, FY - 105, "#5a3a22", r=6)
        panel(ctx, [("会社員の家族が多い", 46, WHITE)], 1340, 340, a=fade(t, tw + 0.4))


WIN_CROWD_L = Crowd((80, 470, 640, 880), 26, 110, seed=31, facing=1)
WIN_CROWD_R = Crowd((1280, 470, 1840, 880), 26, 110, seed=32, facing=-1)
WIN_MORE = Crowd((560, 760, 1360, 905), 16, 110, seed=33, facing=1)


def sc_c1_window(ctx, t):
    # 申し込みの窓口
    box(ctx, 760, 470, 1160, 780, "#d9c9a3", r=12)
    box(ctx, 800, 520, 1120, 660, "#6b5a3a", r=8)
    panel(ctx, [("申込みの窓口", 48, PANEL)], 960, 420, bg="#f4efe2", pad=(26, 8))
    tw0 = bd("c1_window") + 0.5
    u = ease(seg(t, tw0, tw0 + 2.6))
    walking = tw0 < t < tw0 + 2.6
    WIN_CROWD_L.draw(ctx, t, dx=-700 * (1 - u), walk=walking)
    WIN_CROWD_R.draw(ctx, t, dx=700 * (1 - u), walk=walking)
    t51 = T("c1_51", 0.1)
    if t >= t51:
        u2 = ease(seg(t, t51, t51 + 1.6))
        WIN_MORE.draw(ctx, t, dy=260 * (1 - u2), a=u2, walk=t < t51 + 1.6)
        panel(ctx, [("ひと部屋に 51人", 60, YEL)], 960, 280, a=fade(t, t51 + 0.4))
    tc = T("c1_window", 0.45)
    if t >= tc:
        panel(ctx, [("申し込めるのは、月収が家賃の4〜6倍ある人（政府の答弁）", 42, WHITE)], 960, 130, a=fade(t, tc))


def calendar12(ctx, x0, y0, cw, ch, marks=(), t=0.0, t_mark=0.0, a=1.0):
    for m in range(12):
        r, c = divmod(m, 3)
        x, y = x0 + c * cw, y0 + r * ch
        box(ctx, x + 6, y + 6, x + cw - 6, y + ch - 6, "#f4efe2", a, r=8)
        box(ctx, x + 6, y + 6, x + cw - 6, y + 34, REDC, a, r=8)
        label(ctx, f"{m + 1}月", x + cw / 2, y + ch / 2 + 18, 44, PANEL, a=a)
    for k, m in enumerate(marks):
        tt = t_mark + 0.35 * k
        if t >= tt:
            r, c = divmod(m, 3)
            x, y = x0 + c * cw + cw / 2, y0 + r * ch + ch / 2 + 18
            ctx.set_source_rgba(*hexrgb(REDC, a * fade(t, tt, 0.25)))
            ctx.set_line_width(9)
            ctx.arc(x, y, min(cw, ch) * 0.36, 0, 2 * math.pi)
            ctx.stroke()


def sc_c1_freq(ctx, t):
    calendar12(ctx, 100, 150, 250, 180, marks=(2, 5, 8, 11), t=t, t_mark=T("c1_4", 0.45))
    tc = T("c1_freq", 0.2)
    if t >= tc:
        panel(ctx, [("抽選の頻度", 80, YEL)], 1400, 300, a=fade(t, tc), border=YEL)
    t4 = T("c1_4", 0.4)
    if t >= t4:
        panel(ctx, [("空き家の募集は年4回", 56, WHITE), ("（昭和50年代の公団の答弁）", 44, PALE)], 1400, 560, a=fade(t, t4))
    tk = T("c1_4", 0.3)
    if t >= tk:
        panel(ctx, [("公団＝国がつくった、住まいを建てて貸す組織", 40, WHITE)], 1400, 730, a=fade(t, tk), pad=(22, 10))


UNK = ["新しい団地の募集の回数", "1人がいくつ出せたか", "抽選のやり方"]


def sc_c1_unk(ctx, t):
    label(ctx, "確かめられなかったこと", 120, 150, 60, YEL, align="left")
    for k, s_ in enumerate(UNK):
        tk = T("c1_unk", 0.15 + 0.2 * k)
        if t >= tk:
            a = fade(t, tk)
            ball(ctx, 160, 270 + 95 * k, 32, REDC, a)
            label(ctx, "？", 160, 270 + 95 * k, 44, WHITE, a=a)
            label(ctx, s_, 220, 270 + 95 * k, 52, WHITE, a=a, align="left")
    calendar12(ctx, 1240, 120, 190, 120, marks=(2, 5, 8, 11), t=t, t_mark=T("c1_set", 0.4), a=fade(t, T("c1_set", 0.2)))
    ts = T("c1_set", 0.3)
    if t >= ts:
        panel(ctx, [("この動画では、募集は年4回、", 56, YEL), ("1回に1つ申し込むと仮定します", 56, YEL)], 700, 720, a=fade(t, ts), border=YEL)


# ============================================================
# 2 運だけなら、何回目で当たる？
# ============================================================
C2_CROWD = Crowd((80, 360, 1320, 860), 70, 104, seed=41, facing=1)


def sc_c2_title(ctx, t):
    C2_CROWD.draw(ctx, t)
    person(ctx, 1560, FY, PH, "man", WIN, phase=0.25, facing=-1, pose="stand")
    panel(ctx, [("あなた", 52, PANEL)], 1560, 470, bg=WIN, pad=(30, 10))


Q51 = Crowd((760, 440, 1840, 830), 51, 82, seed=51, facing=-1)


def sc_c2_ratio(ctx, t):
    door = danchi(ctx, 110, 800, 420, 330, BLDG, floors=4, units=5)
    panel(ctx, [("部屋 1", 52, YEL)], door[0], 410)
    Q51.draw(ctx, t)
    tf = bd("c2_ratio") + 0.45
    panel(ctx, [("申し込んだ人の数 ÷ 部屋の数 ＝ 倍率", 60, WHITE)], 960, 130, a=fade(t, tf))
    t5 = T("c2_cont", 0.5)
    if t >= t5:
        panel(ctx, [("51.4倍", 96, YEL)], 1300, 300, a=fade(t, t5), border=YEL)
    tc = T("c2_cont", 0.25)
    if t >= tc:
        panel(ctx, [("この倍率が続いたら、の回数です", 44, WHITE)], 960, 900 - 40, a=fade(t, tc))


BALLS = 51
ORANGE_BALL = 23


def sc_c2_kuji(ctx, t):
    kuji_box(ctx, 420, 430, 420)
    label(ctx, "くじ", 420, 540, 64, WHITE)
    t0 = T("c2_kuji", 0.05)
    for k in range(BALLS):
        tk = t0 + k * 0.05
        if t < tk:
            continue
        r_, c_ = divmod(k, 17)
        tx, ty = 820 + c_ * 60, 380 + r_ * 62
        u = ease_out(seg(t, tk, tk + 0.35))
        x, y = lerp(420, tx, u), lerp(410, ty, u) - 80 * math.sin(math.pi * u)
        ball(ctx, x, y, 24, WIN if k == ORANGE_BALL else WAIT)
    tv = T("c2_kuji", 0.3)
    if t >= tv:
        panel(ctx, [("当たりは 51個に1個", 56, YEL)], 1300, 200, a=fade(t, tv))
    ty = T("c2_yoso", 0.55)
    if t >= ty:
        panel(ctx, [("予想", 44, PANEL), ("51回くらいで当たる", 60, PANEL)], 1300, 760, a=fade(t, ty), bg=YEL)


C10B = Crowd((470, 380, 1000, 880), 120, 68, seed=61, facing=-1)
_rem_order = list(range(C10B.n))
random.Random(9).shuffle(_rem_order)
BAR_T0 = None
BAR_STEP = 0.3
N_BARS = 50
CH_X0, CH_X1, CH_Y0, CH_Y1 = 1100, 1840, 420, 840


def _bar_t0():
    return T("c2_each51", 0.0, 0.2)


def bars_shown(t):
    return int(clamp01((t - _bar_t0()) / (BAR_STEP * N_BARS)) * N_BARS + (1 if t >= _bar_t0() else 0)) if t >= _bar_t0() else 0


def sc_c2_10k(ctx, t):
    door = danchi(ctx, 60, 880, 360, 420, BLDG, floors=5, units=4)
    nb = min(N_BARS, bars_shown(t))
    remain = (Q1 > nb).sum() / 1e4
    nvis = int(round(C10B.n * remain))
    gone = _rem_order[:C10B.n - nvis]
    gone_t = {}
    for j, i in enumerate(gone):
        k_ = next(k for k in range(1, N_BARS + 1) if C10B.n - int(round(C10B.n * (Q1 > k).sum() / 1e4)) > j)
        gone_t[i] = _bar_t0() + (k_ - 1) * BAR_STEP
    hide = set(gone)
    # 1万人の群れ（はじめは全員・回ごとに少しずつ抜けて団地へ歩く）
    tw0 = T("c2_10k", 0.25)
    early = [i for i in _rem_order[-12:]]
    early_t = {i: tw0 + 0.35 * k for k, i in enumerate(early)} if True else {}
    for i in early:
        if t >= early_t[i]:
            hide.add(i)
    C10B.draw(ctx, t, hide=hide)
    for i, ts in list(gone_t.items()) + [(i, early_t[i]) for i in early]:
        if ts <= t <= ts + 2.0:
            x, y, kd = C10B.spots[i]
            walker(ctx, t, ts, ts + 1.4, (x, y), door, 68, kd, c0=WAIT, c1=WIN, vanish=True)
    label(ctx, "まだ当たっていない人", 735, 330, 44, PALE)
    # 右: 回ごとに当たった人の数（枠は場面の始まりから）
    label(ctx, "その回に当たった人の数", (CH_X0 + CH_X1) / 2, 190, 46, WHITE)
    line2(ctx, (CH_X0, CH_Y1), (CH_X1, CH_Y1), WHITE, 4)
    line2(ctx, (CH_X0, CH_Y0), (CH_X0, CH_Y1), WHITE, 4)
    label(ctx, "1回目", CH_X0 + 20, CH_Y1 + 42, 40, PALE)
    label(ctx, "50回目", CH_X1 - 70, CH_Y1 + 42, 40, PALE)
    bw = (CH_X1 - CH_X0 - 20) / N_BARS
    vmax = float(ROUND_WIN[1:N_BARS + 1].max()) * 1.05
    for k in range(1, nb + 1):
        tk = _bar_t0() + (k - 1) * BAR_STEP
        g = ease_out(seg(t, tk, tk + 0.25))
        hh = (CH_Y1 - CH_Y0) * ROUND_WIN[k] / vmax * g
        x = CH_X0 + 10 + (k - 1) * bw
        hi = (k == 1 and t >= T("c2_first", 0.2))
        box(ctx, x + 1, CH_Y1 - hh, x + bw - 2, CH_Y1, YEL if hi else WIN, r=2)
    tfh = T("c2_first", 0.3)
    if t >= tfh:
        panel(ctx, [("最初の回が いちばん多い", 44, YEL)], 1470, 275, a=fade(t, tfh))
    tsh = T("c2_shrink", 0.3)
    if t >= tsh:
        panel(ctx, [("群れが小さいと、当たる人も少ない", 44, WHITE)], 1470, 355, a=fade(t, tsh))


def band_color(r):
    stops = [(1, WIN), (40, "#f5b06e"), (80, "#e5cdb0"), (130, WAIT)]
    for (a_, ca), (b_, cb) in zip(stops, stops[1:]):
        if r <= b_:
            return mix(ca, cb, (r - a_) / (b_ - a_))
    return WAIT


BAND = (120, 330, 1800, 420)
NL = (380, 1580, 800)                       # 数直線 0〜60回（x0, x1, y）


def nlx(r):
    return NL[0] + (NL[1] - NL[0]) * r / 60


def sc_c2_sort(ctx, t):
    label(ctx, "1万人を、当たるまでの回数の順に並べる", 960, 160, 54, WHITE)
    x0, y0, x1, y1 = BAND
    u = ease(seg(t, bd("c2_sort") + 0.45, bd("c2_sort") + 1.6))
    n = int(100 * u)
    gw = (x1 - x0) / 100
    for g in range(n):
        r = float(np.median(Q1S[g * 100:(g + 1) * 100]))
        box(ctx, x0 + g * gw, y0, x0 + (g + 1) * gw - 1, y1, band_color(r), r=0)
    label(ctx, "早く当たった人", x0, 270, 44, PALE, align="left")
    label(ctx, "遅く当たった人", x1, 270, 44, PALE, align="right")
    tm = T("c2_sort", 0.55)
    if t >= tm:
        a = fade(t, tm)
        tri_down(ctx, 960, 470, 22, YEL, a)
        line2(ctx, (960, 425), (960, 470), YEL, 5, a)
        label(ctx, "ちょうど真ん中", 960, 520, 46, YEL, a=a)
    tv = T("c2_med", 0.55)
    if t >= tv:
        panel(ctx, [("中央値 37回目", 66, YEL)], 960, 630, a=fade(t, tv), border=YEL)
    tf = T("c2_fast", 0.0)
    if t >= tf:
        a = fade(t, tf)
        line2(ctx, (NL[0], NL[2]), (NL[1], NL[2]), WHITE, 5, a)
        for r in (0, 60):
            line2(ctx, (nlx(r), NL[2] - 14), (nlx(r), NL[2] + 14), WHITE, 4, a)
        label(ctx, "0回", nlx(0) - 70, NL[2], 40, PALE, a=a)
        label(ctx, "60回", nlx(60) + 80, NL[2], 40, PALE, a=a)
        tri_down(ctx, nlx(51), NL[2] - 6, 18, WHITE, a)
        panel(ctx, [("予想 51回", 44, WHITE)], nlx(51), NL[2] - 70, a=a)
        mv = ease(seg(t, T("c2_fast", 0.35), T("c2_fast", 0.35) + 1.0))
        xm = lerp(nlx(51), nlx(37), mv)
        ctx.set_source_rgba(*hexrgb(YEL, a))
        ctx.move_to(xm - 18, NL[2] + 40)
        ctx.line_to(xm + 18, NL[2] + 40)
        ctx.line_to(xm, NL[2] + 6)
        ctx.close_path()
        ctx.fill()
        label(ctx, "37回", xm, NL[2] + 74, 44, YEL, a=a)


# ---- 1万人の分布（1人＝100人で人を積む）----
HX0, HCOLW, HGAP, HBASE = 130, 200, 40, 845
HPER, HSZ, HSTEP = 4, 92, 54
HLABS = ["1〜20回", "21〜40回", "41〜60回", "61〜80回", "81〜100回", "101〜120回", "121回〜"]
HTONE = [WIN, WIN, "#f5b06e", "#f2c391", "#e5cdb0", "#cfc9c0", WAIT]
PERSON_STEP = 0.05


def hx(r):
    """回数 r の x（柱は20回ずつ）"""
    return HX0 + (r - 1) / 20 * (HCOLW + HGAP)


def col_start(i):
    if i == 0:
        return T("c2_h1", 0.0, 0.3)
    if i == 6:
        return T("c2_h3", 0.0, 0.3)
    return T("c2_h2", 0.0, 0.3) + (i - 1) * 0.55


def col_top(i):
    rows = math.ceil(HIST_N[i] / HPER)
    return HBASE - (rows - 1) * HSTEP - HSZ


def sc_c2_hist(ctx, t):
    label(ctx, "1万人の、当たるまでの回数", 80, 125, 56, WHITE, align="left")
    label(ctx, "1人 ＝ 100人", 1840, 125, 46, PALE, align="right")
    t80 = T("c2_80", 0.3)
    glow6 = t >= T("c2_p90", 0.2)
    for i, lab in enumerate(HLABS):
        cx = HX0 + i * (HCOLW + HGAP)
        label(ctx, lab, cx + HCOLW / 2, HBASE + 42, 40, WHITE)
        if glow6 and i == 6:
            box(ctx, cx - 10, col_top(6) - 20, cx + HCOLW + 10, HBASE + 10, "#ffffff", 0.18 * fade(t, T("c2_p90", 0.2)), r=12)
        k = HIST_N[i]
        rows = math.ceil(k / HPER)
        t0 = col_start(i)
        cnt = 0
        for r in range(rows - 1, -1, -1):
            m = min(HPER, k - r * HPER)
            for j in range(m):
                idx = r * HPER + j
                if t < t0 + idx * PERSON_STEP:
                    continue
                cnt += 1
                px = cx + 22 + j * (HCOLW - 44) / (HPER - 1) + (8 if r % 2 else 0)
                py = HBASE - r * HSTEP
                col = HTONE[i]
                if t >= t80 and i >= 4:
                    col = mix(col, "#ffffff", 0.55 * fade(t, t80 + 0.3 * (i - 4)))
                person(ctx, px, py, HSZ, ("man", "woman")[(i + j + r) % 2], col, phase=0.0, pose="stand")
    for i, s_ in ((0, f"{HIST20[0]:,}人"), (6, f"{HIST20[6]:,}人")):
        tt = col_start(i) + HIST_N[i] * PERSON_STEP + 0.1
        if t >= tt:
            label(ctx, s_, HX0 + i * (HCOLW + HGAP) + HCOLW / 2, col_top(i) - 38, 42, YEL, a=fade(t, tt))
    # 中央値の印（ここまでで言った値。場面の始まりから）
    xm = hx(37)
    a = 1.0
    line2(ctx, (xm, 270), (xm, HBASE), YEL, 4, a, dash=[12, 10])
    panel(ctx, [("中央値 37回目", 46, YEL)], xm, 225, a=a)
    if t >= t80:
        a8 = fade(t, t80)
        x8 = HX0 + 4 * (HCOLW + HGAP) - HGAP / 2
        line2(ctx, (x8, 290), (x8, HBASE + 10), WHITE, 5, a8, dash=[14, 10])
        label(ctx, "80回", x8, 255, 42, WHITE, a=a8)
        tv = T("c2_80", 0.62)
        if t >= tv:
            panel(ctx, [("100人に21人", 50, YEL)], 1330, 420, a=fade(t, tv))
    tp = T("c2_p90", 0.25)
    if t >= tp:
        panel(ctx, [("10人に1人は", 42, WHITE), ("122回以上", 50, YEL)], HX0 + 6 * (HCOLW + HGAP) + HCOLW / 2 - 20, 500, a=fade(t, tp))
    tmn = T("c2_mean", 0.3)
    if t >= tmn:
        u = ease(seg(t, tmn, tmn + 1.2))
        xa = lerp(xm, hx(52.4), u)
        line2(ctx, (xa, 345), (xa, HBASE), WHITE, 4, fade(t, tmn), dash=[6, 8])
        tri_down(ctx, xa, 345, 16, WHITE, fade(t, tmn))
        tv2 = T("c2_mean", 0.62)
        if t >= tv2:
            panel(ctx, [("平均 50回あまり", 46, WHITE)], hx(52.4) + 60, 300, a=fade(t, tv2))
    twy = T("c2_why", 0.3)
    if t >= twy:
        u = ease(seg(t, twy, twy + 1.0))
        arrow2(ctx, (hx(52.4) + 275, 300), (lerp(hx(52.4) + 285, 1500, u), 300), YEL, 10, fade(t, twy))


C_EACH = Crowd((100, 380, 1820, 880), 54, 112, seed=71, facing=1)
SPOT3 = [C_EACH.n - 3, C_EACH.n - 12, C_EACH.n - 26]


def sc_c2_each(ctx, t):
    cols = {}
    for k, i in enumerate(SPOT3):
        tk = T("c2_each", 0.2 + 0.2 * k)
        if t >= tk:
            x, y, _kd = C_EACH.spots[i]
            fill(ctx, hexrgb("#fff6c0", 0.35 * fade(t, tk)))
            ctx.save()
            ctx.translate(x, y - 2)
            ctx.scale(1.0, 0.3)
            ctx.arc(0, 0, 80, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()
            cols[i] = GLOW
    C_EACH.draw(ctx, t, colors=cols)


BG_CROWD = Crowd((80, 420, 1040, 800), 40, 90, seed=81, facing=1)
DOOR_R = (1380, 820, 470, 420)


def sc_c2_best(ctx, t):
    door = danchi(ctx, *DOOR_R, BLDG, floors=5, units=6)
    BG_CROWD.draw(ctx, t, a=0.55)
    t0 = bd("c2_b1") + 0.6
    tw = T("c2_b2", 0.35)
    if t < tw:
        walker(ctx, t, t0, t0 + 1.4, (500, 760), (720, FY), PH, "woman", c0=GLOW)
    else:
        walker(ctx, t, tw, tw + 2.6, (720, FY), (door[0], DOOR_R[1]), PH, "woman", c0=WIN, c1=WIN, vanish=True)
    tc = T("c2_b2", 0.2)
    if t >= tc:
        panel(ctx, [("1回目で当選", 56, PANEL)], 720, 470, a=fade(t, tc) * out_fade(t, tw + 2.8, 0.3), bg=YEL)
    tv = T("c2_b3", 0.4)
    if t >= tv:
        panel(ctx, [("100人に1.7人", 64, YEL)], 640, 170, a=fade(t, tv), border=YEL)


def _counter(ctx, t, x, y, n, a=1.0):
    panel(ctx, [(f"落選 {int(n)}枚", 48, WHITE)], x, y, a=a, bg=REDC)


def sc_c2_medp(ctx, t):
    door = danchi(ctx, *DOOR_R, BLDG, floors=5, units=6)
    BG_CROWD.draw(ctx, t, a=0.55)
    t0 = bd("c2_m1") + 0.6
    ts = T("c2_m1", 0.2)
    n = int(clamp01((t - ts) / (36 * 0.11)) * 36) if t >= ts else 0
    t37 = ts + 36 * 0.11 + 0.25
    tv = max(t37, T("c2_m2", 0.45))
    if t < tv:
        walker(ctx, t, t0, t0 + 1.4, (500, 760), (560, FY), PH, "man", c0=GLOW)
    else:
        walker(ctx, t, tv + 0.3, tv + 2.9, (560, FY), (door[0], DOOR_R[1]), PH, "man", c0=WIN, c1=WIN, vanish=True)
    slips(ctx, 820, FY, n, seed=7)
    if t >= ts:
        _counter(ctx, t, 820, 420, n)
    if t >= tv:
        panel(ctx, [("37回目で当選", 60, PANEL)], 560, 300, a=fade(t, tv), bg=YEL)


WCROWD = Crowd((1060, 420, 1860, 860), 44, 96, seed=91, facing=-1)


def sc_c2_worst(ctx, t):
    # 群れがどんどん入れ替わる中、1人だけが残り続ける
    t0 = bd("c2_w1")

    def al(i):
        ph_ = ((t - t0) * 0.45 + WCROWD.phase[i]) % 1.0
        return clamp01(min(ph_, 1 - ph_) * 8)
    WCROWD.draw(ctx, t, alpha=al)
    person(ctx, 520, FY, PH, "woman", WAIT, phase=0.25, pose="stand")
    ts = bd("c2_w1") + 0.5
    n = int(min(68, (t - ts) / 0.07)) if t >= ts else 0
    slips(ctx, 760, FY, n, step=11, seed=8, w=100)
    tv = T("c2_w2", 0.6)
    if t >= tv:
        panel(ctx, [("最長 520回", 64, YEL)], 1140, 230, a=fade(t, tv), border=YEL)


def sc_c2_three(ctx, t):
    a = fade(t, bd("c2_three") + 0.4)
    for k, (x, kd, col, n, lab) in enumerate(((330, "woman", WIN, 0, "落選 0枚"), (930, "man", WIN, 36, "落選 36枚"), (1440, "woman", WAIT, 68, "落選の山"))):
        person(ctx, x, FY, PH, kd, col, phase=0.25, pose="stand", a=a)
        slips(ctx, x + 230, FY, n, seed=7 + k, a=a)
        panel(ctx, [(lab, 46, WHITE)], x, 470, a=a, bg=REDC)


def sc_c2_mem(ctx, t):
    person(ctx, 380, FY, PH, "woman", WAIT, phase=0.25, pose="stand")
    ts = bd("c2_mem") + 0.4
    n = 40 + int(clamp01((t - T("c2_same", 0.1)) / 3.0) * 28) if t >= T("c2_same", 0.1) else 40
    sway = 14 * math.sin((t - T("c2_help", 0.0)) * 9) * fade(t, T("c2_help", 0.1)) * out_fade(t, T("c2_help", 0.1) + 2.0, 0.5) if t >= T("c2_help", 0.0) else 0.0
    slips(ctx, 640, FY, n, seed=8, sway=sway)
    kuji_box(ctx, 1380, 560, 380, a=fade(t, ts))
    label(ctx, "くじ", 1380, 660, 60, WHITE, a=fade(t, ts))
    tc = T("c2_mem", 0.3)
    if t >= tc:
        panel(ctx, [("次に当たる見込み", 48, WHITE), ("51人に1人", 64, YEL)], 1380, 230, a=fade(t, tc), border=YEL)


def doc(ctx, x0, y0, w, h, a=1.0):
    box(ctx, x0, y0, x0 + w, y0 + h, "#f4efe2", a, r=8)
    for k in range(9):
        fill(ctx, hexrgb("#9a927f", a))
        ctx.rectangle(x0 + 40, y0 + 60 + k * (h - 100) / 9, w - 80 - (60 if k % 3 == 2 else 0), 10)
        ctx.fill()


def sc_c2_rec(ctx, t):
    doc(ctx, 130, 290, 380, 400, a=1.0)
    tc = T("c2_rec", 0.2)
    if t >= tc:
        panel(ctx, [("昭和45年・ある団地の入居者へのアンケート", 44, YEL), ("（国会で議員が読み上げ）", 40, PALE)], 960, 140, a=fade(t, tc))
    t2 = T("c2_rec2", 0.2)
    for k in range(4):
        if t >= t2:
            walker(ctx, t, t2 + 0.15 * k, t2 + 0.15 * k + 1.2, (620 + 70 * k, 905), (560 + 90 * k, 900), 170, P_KINDS[k], c0=WIN, appear=True)
    t15 = T("c2_15", 0.2)
    if t >= t15:
        panel(ctx, [("公団と公社あわせて", 40, WHITE), ("入居できた人への聞き取り", 40, WHITE), ("家賃が高めの団地", 40, WHITE)], 330, 780, a=fade(t, t15))
        panel(ctx, [("公社＝都道府県や市がつくった住まいの組織", 40, WHITE)], 1290, 840, a=fade(t, t15), pad=(22, 10))
        grid100(ctx, 1094, 375, 15, a=fade(t, t15), t_on=T("c2_15", 0.5), t=t)
        tv = T("c2_15", 0.7)
        if t >= tv:
            panel(ctx, [("100人に15人", 56, YEL)], 1382, 265, a=fade(t, tv))


def sc_c2_cmp(ctx, t):
    a = 1.0
    label(ctx, "記録（アンケート）", 460, 165, 48, WHITE, a=a)
    label(ctx, "この計算", 1420, 165, 48, WHITE, a=a)
    label(ctx, "30回以上", 960, 165, 44, PALE, a=a)
    panel(ctx, [("100人に15人", 52, YEL)], 460, 240, a=a)
    grid100(ctx, 172, 360, 15, a=a)
    grid100(ctx, 1132, 360, 56, a=a, t_on=T("c2_56", 0.4), t=t)
    tv = T("c2_56", 0.55)
    if t >= tv:
        panel(ctx, [("100人に56人", 52, YEL)], 1420, 240, a=fade(t, tv))
    tw = T("c2_who", 0.2)
    th = T("c2_hint", 0.15)
    if tw <= t:
        panel(ctx, [("入居できた人への聞き取り／家賃が高めの団地", 42, YEL if t < T("c2_notin", 0.0) else WHITE)], 960, 868, a=fade(t, tw) * out_fade(t, th - 0.3, 0.3), pad=(26, 8))
    tni = T("c2_notin", 0.15)
    if t >= tni:
        panel(ctx, [("まだ待っている人は 数に入らない", 44, YEL)], 960, 795, a=fade(t, tni) * out_fade(t, th - 0.3, 0.3), pad=(26, 8))
    tq = T("c2_q", 0.3)
    if t >= tq:
        label(ctx, "？", 960, 560, 180, YEL, a=fade(t, tq) * out_fade(t, th - 0.3, 0.3))
    if t >= th:
        panel(ctx, [("実際には、倍率は年々下がりました", 48, YEL), ("（昭和45年には、東京の都心に近い所でも20倍ぐらい）", 40, WHITE)], 960, 820, a=fade(t, th))


def answer_scene(ctx, t, key, rows, you=True):
    tc = T(key, 0.1)
    label(ctx, "答え", 960, 140, 72, YEL, a=1.0)
    panel(ctx, rows, 960, 330, a=fade(t, tc), border=YEL, pad=(60, 30))
    if you:
        danchi(ctx, 1260, 905, 520, 360, BLDG, floors=4, units=6)
        person(ctx, 760, FY, PH, "man", WIN, phase=0.25, pose="stand", a=fade(t, bd(key) + 0.5))


def sc_c2_ans(ctx, t):
    answer_scene(ctx, t, "c2_ans", [("運だけなら", 64, WHITE), ("中央値 37回", 96, YEL)])


# ============================================================
# 3 どの団地に申し込むと、早く入れる？
# ============================================================
def sc_c3_title(ctx, t):
    # あなたの前に、道が分かれる
    for k, x in enumerate((360, 960, 1560)):
        fill(ctx, hexrgb("#d8cfe6", 0.55))
        ctx.move_to(900, 905)
        ctx.line_to(1020, 905)
        ctx.line_to(x + 70, 560)
        ctx.line_to(x - 70, 560)
        ctx.close_path()
        ctx.fill()
        danchi(ctx, x - 150, 560, 300, 230, BLDG, floors=4, units=5, door=False)
    person(ctx, 960, FY, PH, "man", WIN, phase=0.25, pose="stand")


KCOL = [330, 960, 1590]
KCROWD = [Crowd((x - 250, 700, x + 250, 900), n, 66, seed=101 + k, facing=1) for k, (x, n) in enumerate(zip(KCOL, (40, 13, 2)))]
KCARD = [["人気の団地", "50倍前後", "（53.6倍の例）"], ["倍率の低めの団地", "15〜17倍", "（15.6倍・17.1倍の例）"], ["家賃の高い団地", "1倍を切った例", "（大阪など）"]]
KKEY = ["c3_pop", "c3_low", "c3_hi"]


def sc_c3_kinds(ctx, t):
    a = 1.0
    panel(ctx, [("昭和41〜48年・国会で議員が挙げた例", 46, PALE)], 960, 105, a=a)
    for k, x in enumerate(KCOL):
        danchi(ctx, x - 190, 450, 380, 260, BLDG, floors=4, units=5, a=a)
        tk = T(KKEY[k], 0.2)
        if t >= tk:
            ak = fade(t, tk)
            rr = KCARD[k]
            panel(ctx, [(rr[0], 44, YEL), (rr[1], 44, WHITE), (rr[2], 40, PALE)], x, 560, a=ak)
            KCROWD[k].draw(ctx, t, a=ak)


# 昭和45年の総裁答弁（東京の都心近く 約20倍／大阪 約10倍／名古屋 約5倍／福岡 約2倍）。群れの人数は 20:10:5:2 の比（2倍して 40・20・10・4人）
CITY_RATIO = [("東京の都心近く", 20), ("大阪", 10), ("名古屋", 5), ("福岡", 2)]
CITY_X = [270, 730, 1190, 1650]
CITY_SIZE, CITY_DY, CITY_W = 88, 62, 420


def _city_crowd(k, ratio):
    n = ratio * 2
    rows = math.ceil(n / 5)
    return Crowd((CITY_X[k] - CITY_W / 2, 900 - rows * CITY_DY, CITY_X[k] + CITY_W / 2, 900), n, CITY_SIZE, seed=111 + k, facing=1)


CITY_CROWD = [_city_crowd(k, r) for k, (_n, r) in enumerate(CITY_RATIO)]


def sc_c3_map(ctx, t):
    panel(ctx, [("昭和45年（総裁の答弁）", 46, PALE)], 500, 95)
    for k, (nm, r) in enumerate(CITY_RATIO):
        tk = T("c3_area", 0.05) + 0.35 * k
        if t < tk:
            continue
        ak = fade(t, tk)
        panel(ctx, [(nm, 44, WHITE), (f"約{r}倍", 62, YEL)], CITY_X[k], 250, a=ak)
        n_on = int(clamp01((t - tk) / 0.8) * CITY_CROWD[k].n + 0.999)       # 人は少しずつ増える
        CITY_CROWD[k].draw(ctx, t, hide=set(range(n_on, CITY_CROWD[k].n)), a=ak)
    tw = T("c3_where", 0.15)
    if t >= tw:
        panel(ctx, [("住む所で、待ちが変わる", 50, PANEL)], 1400, 95, a=fade(t, tw), bg=YEL)


DEC_P0, DEC_P1 = (400, 330), (1500, 800)


def sc_c3_dec(ctx, t):
    # 間の年の数字はないので棒にしない。右下がりの矢印と札だけ（数字も足さない）
    t0 = T("c3_dec", 0.0)
    u = ease(seg(t, t0 - 0.4, t0 + 2.6))
    arrow2(ctx, DEC_P0, (lerp(DEC_P0[0], DEC_P1[0], max(u, 0.02)), lerp(DEC_P0[1], DEC_P1[1], max(u, 0.02))), YEL, 22, 1.0, head=74)
    label(ctx, "昭和41年", DEC_P0[0] - 60, DEC_P0[1] - 70, 60, WHITE)
    label(ctx, "昭和45年", DEC_P1[0] + 80, DEC_P1[1] + 62, 60, WHITE, a=fade(t, t0 + 2.2))
    tc = T("c3_dec", 0.3)
    if t >= tc:
        panel(ctx, [("年々減ってきている（総裁の答弁）", 56, YEL)], 1130, 160, a=fade(t, tc), border=YEL)


def sc_c3_yoso(ctx, t):
    person(ctx, 380, FY, PH, "man", WIN, phase=0.25, pose="stand")
    for k, x in enumerate((900, 1250, 1600)):
        danchi(ctx, x - 140, 905, 280, 220, BLDG, floors=4, units=4)
    ty = T("c3_yoso", 0.55)
    if t >= ty:
        panel(ctx, [("予想", 44, PANEL), ("どこに出しても運しだい", 60, PANEL)], 1180, 300, a=fade(t, ty), bg=YEL)


FOUR_X = [250, 710, 1170, 1630]
FOUR_KD = ["man", "woman", "man", "woman"]
FOUR_NAME = ["人気の団地", "倍率の低めの団地", "家賃の高い団地", "数年待つ"]
FOUR_CARD = [["51.4倍"], ["16倍と仮定"], ["1倍未満で抽選なし", "と仮定（大阪などの例）"], ["年4回と仮定"]]
FOUR_KEY = ["c3_p1", "c3_p2", "c3_p3", "c3_p4"]


def name_tag(ctx, s, x, a=1.0, y=470, size=50):
    panel(ctx, [(s, size, PANEL)], x, y, a=a, bg=YEL, pad=(20, 8))


def sc_c3_four(ctx, t):
    a = 1.0
    for k, x in enumerate(FOUR_X):
        person(ctx, x, FY, PH, FOUR_KD[k], WAIT, phase=0.25, pose="stand", a=a)
        tk = T(FOUR_KEY[k], 0.2)
        if t >= tk:
            ak = fade(t, tk)
            name_tag(ctx, FOUR_NAME[k], x, ak)
            panel(ctx, [(s_, 40, WHITE) for s_ in FOUR_CARD[k]], x, 345, a=fade(t, tk + 0.4))
        else:
            box(ctx, x - 110, 446, x + 110, 494, YEL, 0.35 * a, r=10)
    tb = T("c3_p4", 0.15)
    if t >= tb:
        panel(ctx, [("昭和41年の51.4倍から、昭和45年の20倍（東京の都心近く）へ、", 40, WHITE), ("まっすぐ下がると仮定", 40, WHITE)], 960, 140, a=fade(t, tb))


TEN_X = [250, 710, 1170, 1630]
TEN_CROWD = [Crowd((x - 200, 620, x + 200, 900), 24, 60, seed=131 + k, facing=-1) for k, x in enumerate(TEN_X)]


def sc_c3_10k(ctx, t):
    a = 1.0
    t2 = T("c3_r2", 0.3)
    for k, x in enumerate(TEN_X):
        label(ctx, FOUR_NAME[k], x, 130, 42, YEL, a=a)
        door = danchi(ctx, x - 120, 400, 240, 190, BLDG, floors=4, units=4, a=a)
        hide = set()
        # 人気の団地はぽつりぽつり、低めの団地は声のあとで次々に歩き出す
        order = TEN_CROWD[k].right_order()
        if k == 0:
            starts = [bd("c3_10k") + 0.8 + 1.6 * j for j in range(8)]
        elif k == 1:
            starts = [bd("c3_10k") + 1.4 + 1.2 * j for j in range(3)] + [t2 + 0.2 * j for j in range(14)]
        else:
            starts = []
        if starts:
            for j, (i, ts) in enumerate(zip(order, starts)):
                if t >= ts:
                    hide.add(i)
                    xx, yy, kd = TEN_CROWD[1].spots[i]
                    walker(ctx, t, ts, ts + 1.3, (xx, yy), door, 60, kd, c0=WAIT, c1=WIN, vanish=True)
        TEN_CROWD[k].draw(ctx, t, hide=hide, a=a)
        if k < 2:
            box(ctx, x - 150, 445, x + 150, 545, PANEL, a, r=12)
    for k, key, s_ in ((0, "c3_r1", "中央値 37回"), (1, "c3_r2", "中央値 11回")):
        tv = T(key, 0.55)
        if t >= tv:
            label(ctx, s_, TEN_X[k], 495, 44, YEL, a=fade(t, tv))


BAND_X0, BAND_PX = 360, 36


def sc_c3_low(ctx, t):
    door = danchi(ctx, 800, 905, 340, 300, BLDG, floors=4, units=4)
    # 左: 倍率の低めの団地の中央値の人
    tl0 = T("c3_lm", 0.1)
    ts = tl0 + 1.3
    n1 = int(clamp01((t - ts) / (10 * 0.2)) * 10) if t >= ts else 0
    tw1 = max(ts + 10 * 0.2 + 0.2, T("c3_l11", 0.4))
    if t < tw1:
        walker(ctx, t, tl0, tl0 + 1.2, (-200, FY), (330, FY), PH, "woman", c0=WAIT)
    else:
        walker(ctx, t, tw1, tw1 + 2.0, (330, FY), door, PH, "woman", c0=WIN, c1=WIN, vanish=True)
    slips(ctx, 560, FY, n1, seed=21)
    if t >= ts and t < tw1 + 2.5:
        _counter(ctx, t, 600, 330, n1, a=out_fade(t, tw1 + 2.0))
    name_tag(ctx, "倍率の低めの団地", 330, fade(t, tl0), y=470)
    # 右: 人気の団地の中央値の人（落選の札が増え続ける）
    tp0 = bd("c3_lm") + 0.4
    rate = 36 / max(1.0, (T("c3_p37", 0.3) - tp0))
    n2 = int(min(36, (t - tp0) * rate)) if t >= tp0 else 0
    tw2 = T("c3_p37", 0.45)
    if t < tw2:
        person(ctx, 1500, FY, PH, "man", WAIT, phase=0.25, pose="stand")
    else:
        walker(ctx, t, tw2, tw2 + 2.0, (1500, FY), door, PH, "man", c0=WIN, c1=WIN, vanish=True)
    slips(ctx, 1730, FY, n2, seed=22)
    _counter(ctx, t, 1640, 330, n2, a=out_fade(t, tw2 + 2.0))
    name_tag(ctx, "人気の団地", 1500, 1.0, y=470)
    # 2本の帯（11回・37回）
    t11 = T("c3_l11", 0.4)
    if t >= t11:
        a = fade(t, t11)
        label(ctx, "低めの団地", 330, 150, 42, WHITE, a=a, align="right")
        box(ctx, BAND_X0, 125, BAND_X0 + 11 * BAND_PX, 175, WIN, a, r=6)
        label(ctx, "11回", BAND_X0 + 11 * BAND_PX + 60, 150, 42, YEL, a=a)
    if t >= tw2:
        a = fade(t, tw2)
        label(ctx, "人気の団地", 330, 240, 42, WHITE, a=a, align="right")
        box(ctx, BAND_X0, 215, BAND_X0 + 37 * BAND_PX, 265, WIN, a, r=6)
        box(ctx, BAND_X0 + 11 * BAND_PX, 215, BAND_X0 + 37 * BAND_PX, 265, YEL, a * 0.85, r=6)
        label(ctx, "37回", BAND_X0 + 37 * BAND_PX + 60, 240, 42, YEL, a=a)


def sc_c3_tail(ctx, t):
    a = 1.0
    panel(ctx, [("10人に1人は", 56, WHITE)], 960, 160, a=a)
    px = 1240 / 122
    for k, (nm, v, key) in enumerate((("人気の団地", 122, 0), ("低めの団地", 36, 1))):
        y = 420 + 220 * k
        tk = T("c3_tail", 0.15 + 0.2 * k)
        if t < tk:
            continue
        g = ease(seg(t, tk, tk + 0.8))
        label(ctx, nm, 400, y, 46, WHITE, a=a, align="right")
        box(ctx, 430, y - 40, 430 + v * px * g, y + 40, WAIT if k == 0 else WIN, a, r=8)
        label(ctx, f"{v}回以上", 430 + v * px * g - 20, y + 85, 46, YEL, a=a * fade(t, tk + 0.6), align="right")


ALL_CROWD = Crowd((120, 520, 900, 900), 30, 90, seed=141, facing=1)


def sc_c3_all(ctx, t):
    door = danchi(ctx, 1300, 905, 520, 460, BLDG, floors=5, units=6)
    name_tag(ctx, "家賃の高い団地", 510, 1.0, y=400)
    tw = T("c3_all", 0.3)
    u = ease(seg(t, tw, tw + 2.6))
    walking = tw < t < tw + 2.6

    def al(i):
        x, _y, _k = ALL_CROWD.spots[i]
        xx = x + (door[0] - x) * u
        return clamp01((door[0] - 40 - xx) / 120)
    cols = {i: WIN for i in range(ALL_CROWD.n)} if t >= tw else None
    ALL_CROWD.draw(ctx, t, colors=cols, dx=0, walk=walking, alpha=lambda i: 1.0)
    if t >= tw:
        pass
    tc = T("c3_all", 0.5)
    if t >= tc:
        panel(ctx, [("全員 1回目で入居（仮定）", 50, YEL)], 960, 200, a=fade(t, tc))


def _all_offsets(t):
    return 0


# 「家賃の高い団地」の群れは、歩き出してから団地に入るまでを1人ずつ動かす（上の draw は止まった絵に使わないよう、ここで描き直す）
def sc_c3_all(ctx, t):  # noqa: F811
    door = danchi(ctx, 1300, 905, 520, 460, BLDG, floors=5, units=6)
    name_tag(ctx, "家賃の高い団地", 510, 1.0, y=400)
    tw = T("c3_all", 0.3)
    for j, (x, y, kd) in enumerate(ALL_CROWD.spots):
        ts = tw + 0.04 * j
        if t < ts:
            person(ctx, x, y, 90, kd, WAIT, phase=ALL_CROWD.phase[j], facing=1, pose="walk")
        else:
            walker(ctx, t, ts, ts + 2.4, (x, y), (door[0], door[1] - 10), 90, kd, c0=WIN, c1=WIN, vanish=True)
    tc = T("c3_all", 0.5)
    if t >= tc:
        panel(ctx, [("全員 1回目で入居（仮定）", 50, YEL)], 960, 200, a=fade(t, tc))


# ---- 5人目（すぐ出し続ける）と倍率が下がる線 ----
LINE_X0, LINE_PX, LINE_Y0, LINE_Y1 = 780, 42, 160, 430


def rx(r):
    return LINE_X0 + r * LINE_PX


def ry(r):
    return LINE_Y0 + (LINE_Y1 - LINE_Y0) * min(1.0, r / 16)


FIVE_X = [210, 570, 925, 1280, 1640]


def sc_c3_add(ctx, t):
    # 4人の隣に、5人目（すぐ出し続ける人）を足す。名札は高さを交互にずらす
    ta = T("c3_add", 0.25)
    for k in range(5):
        x = FIVE_X[k]
        if k < 4:
            person(ctx, x, FY, PH, FOUR_KD[k], WAIT, phase=0.25, pose="stand")
            name_tag(ctx, FOUR_NAME[k], x, 1.0, y=470 if k % 2 == 0 else 385, size=56)
        elif t >= ta:
            walker(ctx, t, ta, ta + 1.5, (2100, FY), (x, FY), PH, "man", c0=WAIT, facing=-1)
            name_tag(ctx, "すぐ出し続ける", x, fade(t, ta + 1.2), y=470, size=56)
    if t >= ta:
        panel(ctx, [("もう1人", 64, YEL)], 1640, 270, a=fade(t, ta + 0.3), border=YEL)


def sc_c3_five(ctx, t):
    # 文の前半「1人目の倍率は、51倍のままでした」＝まっすぐの線。後半「倍率が年々下がる中で」＝下がる線の上を進む
    t1st = T("c3_keep", 0.05)
    tk = T("c3_keep", 0.42)
    t21 = T("c3_21", 0.4)
    walker(ctx, t, tk, t21, (440, FY), (rx(21), FY), PH, "man", c0=WAIT)
    name_tag(ctx, "すぐ出し続ける", lerp(440, rx(21), ease(seg(t, tk, t21))) if t >= tk else 440, 1.0)
    a1 = fade(t, t1st)
    u1 = ease(seg(t, t1st, t1st + 0.9))
    line2(ctx, (rx(0), LINE_Y0), (rx(0) + (rx(24) - rx(0)) * u1, LINE_Y0), WHITE, 6, a1, dash=[16, 12])
    label(ctx, "1人目は 51倍のまま", rx(24), LINE_Y0 - 42, 44, WHITE, a=a1, align="right")
    label(ctx, "倍率 51.4倍", rx(0) - 30, LINE_Y0, 40, WHITE, a=a1, align="right")
    label(ctx, "昭和41年", rx(0), LINE_Y0 - 55, 40, PALE, a=a1)
    a = fade(t, tk - 0.3)
    u = ease(seg(t, tk - 0.3, tk + 0.9))
    pts = [(rx(r), ry(r)) for r in np.linspace(0, 24 * u, 40)]
    ctx.set_source_rgba(*hexrgb(YEL, a))
    ctx.set_line_width(8)
    for k, p_ in enumerate(pts):
        (ctx.move_to if k == 0 else ctx.line_to)(*p_)
    ctx.stroke()
    label(ctx, "昭和45年", rx(16), LINE_Y1 - 50, 40, PALE, a=a)
    label(ctx, "20倍", rx(24), LINE_Y1 - 50, 40, YEL, a=a)
    rr = 21 * clamp01((t - tk) / max(0.5, t21 - tk))
    if t >= tk:
        ball(ctx, rx(rr), ry(rr), 16, WIN if t >= t21 else WHITE, a)
    if t >= t21:
        panel(ctx, [("中央値 21回", 56, YEL)], 420, 600, a=fade(t, t21), border=YEL)
    t5 = T("c3_5y", 0.3)
    if t >= t5:
        panel(ctx, [("年4回なら 約5.2年", 50, WHITE)], 420, 730, a=fade(t, t5))


RX0, RPX = 600, 30


def flip_calendar(ctx, x, y, t, a=1.0, period=1.0):
    """めくれる暦（文字なし）。待つあいだ、ずっと1枚ずつめくれる"""
    box(ctx, x - 60, y - 70, x + 60, y + 70, "#f4efe2", a, r=8)
    box(ctx, x - 60, y - 70, x + 60, y - 40, REDC, a, r=8)
    for k in range(3):
        box(ctx, x - 40, y - 20 + 25 * k, x + 40, y - 10 + 25 * k, "#9a927f", a, r=3)
    u = (t % period) / period
    if u < 0.5:
        hh = 140 * (1 - u * 2)
        box(ctx, x - 60, y - 70, x + 60, y - 70 + max(4, hh), mix("#f4efe2", "#000000", 0.08), a, r=8)
LANE_Y = (300, 720)


def lane_x(r):
    return RX0 + r * RPX


def sc_c3_race(ctx, t):
    # 上: すぐ出し続ける人 ／ 下: 数年待つ人。帯は回（1目もり＝1回）
    ty, by = LANE_Y
    a0 = 1.0
    danchi(ctx, 1630, 470, 250, 270, BLDG, floors=4, units=4, a=a0)
    label(ctx, "すぐ出し続ける", 630, 190, 44, YEL, a=a0, align="left")
    label(ctx, "数年待つ", 630, 612, 44, YEL, a=a0, align="left")
    tf = T("c3_faster", 0.3)
    twy = T("c3_why", 0.1)
    replay = t >= twy
    # 上の帯（落選の札が1回ずつ。21回目で当たり）
    k_top = 21
    if replay:
        k_top = int(clamp01((t - twy - 0.2) / 3.0) * 21)
    for r in range(1, k_top + 1):
        col = WIN if r == 21 else SLIP
        if t >= T("c3_chance", 0.1) and r < 21 and not replay and (int((t - T("c3_chance", 0.1)) * 4) + r) % 7 == 0:
            col = mix(SLIP, WIN, 0.85)
        box(ctx, lane_x(r - 1) + 2, ty - 30, lane_x(r) - 2, ty + 30, col, a0, r=3)
    # 下の帯: 16回ぶん待つ（くじなし）→ 14回引いて30回目で当たり
    tw = bd("c3_w4") + 0.6
    nwait = int(clamp01((t - tw) / 2.4) * 16) if not replay else int(clamp01((t - twy - 0.2) / 3.0) * 21)
    nwait = min(16, nwait)
    for r in range(1, nwait + 1):
        box(ctx, lane_x(r - 1) + 2, by - 30, lane_x(r) - 2, by + 30, "#8b8aa0", a0, r=3)
    t14 = T("c3_14", 0.0)
    if not replay:
        n14 = int(clamp01((t - t14) / 2.2) * 14) if t >= t14 else 0
    else:
        n14 = max(0, int(clamp01((t - twy - 0.2) / 3.0) * 21) - 16)
    for r in range(17, 17 + n14):
        box(ctx, lane_x(r - 1) + 2, by - 30, lane_x(r) - 2, by + 30, WIN if r == 30 else SLIP, a0, r=3)
    if nwait > 0:
        label(ctx, "待つ（くじなし）", lane_x(8), by + 70, 40, PALE, a=a0)
    # 人
    if t < tf:
        person(ctx, 300, 470, 360, "man", WIN, phase=0.25, pose="stand", a=a0)
    else:
        walker(ctx, t, tf, tf + 2.8, (300, 470), (1755, 470), 360, "man", c0=WIN, vanish=True)
    person(ctx, 300, FY, 360, "woman", WAIT if n14 < 14 else WIN, phase=0.25, pose="stand", a=a0)
    flip_calendar(ctx, 500, 820, t, a0)
    # 札
    tv = T("c3_14", 0.55)
    if t >= tv:
        panel(ctx, [("申し込んでから 中央値 14回", 44, YEL)], 1400, 845, a=fade(t, tv))
    t75 = T("c3_75", 0.3)
    if t >= t75:
        panel(ctx, [("昭和41年から数えて 30回ぶん（約7.5年）", 44, YEL)], 1180, 530, a=fade(t, t75))
    tn = T("c3_none", 0.3)
    if t >= tn and not replay:
        panel(ctx, [("くじを1回も引いていない", 44, WHITE)], 1450, 612, a=fade(t, tn) * out_fade(t, tf - 0.3, 0.3))


def sc_c3_trade(ctx, t):
    a = 1.0
    keys = ["c3_t1", "c3_t2", "c3_t3", "c3_t4", "c3_rec"]
    for k, x in enumerate(FOUR_X):
        on = T(keys[k], 0.0) <= t < T(keys[k + 1], 0.0)
        hop = -18 * math.sin(math.pi * seg(t, T(keys[k], 0.0), T(keys[k], 0.0) + 0.5)) if on else 0.0
        person(ctx, x, FY + hop, PH, FOUR_KD[k], GLOW if on else WAIT, phase=0.25, pose="stand", a=a)
        name_tag(ctx, FOUR_NAME[k], x, a)
        key = keys[k]
        val = ["待つ回数", "人気の団地", "高い家賃", "くじを引かなかった4年"][k]
        tk = T(key, 0.4)
        hw = 235 if k == 3 else 200
        box(ctx, x - hw, 285, x + hw, 400, PANEL, a, r=12)
        label(ctx, "引きかえ", x, 315, 40, PALE, a=a)
        if t >= tk:
            label(ctx, val, x, 365, 40 if len(val) > 6 else 44, YEL, a=fade(t, tk))
    tr = T("c3_rec", 0.2)
    if t >= tr:
        ar = fade(t, tr)
        for k, (x, n, lab) in enumerate(((560, 15, "記録 15人"), (1060, 56, "計算 56人"))):
            for j in range(100):
                r_, c_ = divmod(j, 10)
                ball(ctx, x - 90 + c_ * 20, 110 + r_ * 14, 6, WIN if j < n else WAIT, ar)
            label(ctx, lab, x + 200, 175, 42, WHITE, a=ar, align="left")
        panel(ctx, [("推測", 46, WHITE)], 1640, 170, a=ar, bg=REDC)


def sc_c3_ans(ctx, t):
    tc = T("c3_ans", 0.1)
    label(ctx, "答え", 960, 130, 72, YEL, a=1.0)
    panel(ctx, [("早く入る道はあった。", 64, WHITE), ("ただし、何かと引きかえ", 64, YEL)], 960, 320, a=fade(t, tc), border=YEL, pad=(60, 26))
    ty = T("c3_you", 0.1)
    if t >= ty:
        a = fade(t, ty)
        for k, x in enumerate((260, 560, 1360, 1660)):
            person(ctx, x, 880, 270, FOUR_KD[k], WAIT, phase=0.25, pose="stand", a=a)
        person(ctx, 960, FY, PH, "man", WIN, phase=0.25, pose="stand", a=a)


# ============================================================
# 4 何度も落ちた人を先に入れたら、みんな早く入れる？
# ============================================================
C4_CROWD = Crowd((80, 380, 1180, 860), 60, 104, seed=151, facing=1)


def sc_c4_title(ctx, t):
    C4_CROWD.draw(ctx, t)
    person(ctx, 1400, FY, PH, "woman", WAIT, phase=0.25, pose="stand")
    slips(ctx, 1650, FY, 50, seed=31)


def sc_c4_story(ctx, t):
    tc = T("c4_story", 0.2)
    if t >= tc:
        panel(ctx, [("体験談（公式の記事）", 50, PALE)], 960, 120, a=fade(t, tc))
        a = fade(t, tc + 0.3)
        box(ctx, 460, 220, 1460, 660, PANEL, a, r=18)
        label(ctx, "15回以上落ちた人の枠（昭和41年）", 960, 290, 48, YEL, a=a)
        box(ctx, 560, 350, 1360, 620, "#2c4366", a, r=12)
    tu = T("c4_unk", 0.3)
    if t >= tu:
        label(ctx, "中身は？", 960, 485, 96, WHITE, a=fade(t, tu))
    ti = T("c4_if", 0.3)
    if t >= ti:
        panel(ctx, [("もしもの話", 80, PANEL)], 960, 800, a=fade(t, ti), bg=YEL)


RULES = [("A", "なし（運だけ）", "c4_A"), ("B", "15回落ちた人を、先に入れる（仮定）", "c4_B"), ("C", "昭和63年の公団の決まり", "c4_C")]


def rule_cards(ctx, t, ys=(150, 300, 450), lit=None, a=1.0, x0=160, w=1600, size=50, show_text=None):
    for k, (ab, s_, key) in enumerate(RULES):
        y = ys[k]
        on = (lit is None) or (k in lit)
        box(ctx, x0, y - 55, x0 + w, y + 55, PANEL, a * (1.0 if on else 0.45), r=14)
        label(ctx, ab, x0 + 60, y, 64, YEL if on else PALE, a=a)
        if show_text is None or t >= show_text[k]:
            label(ctx, s_, x0 + 130, y, size, WHITE if on else PALE, a=a * (fade(t, show_text[k]) if show_text else 1.0), align="left")


def sc_c4_rules(ctx, t):
    a = 1.0
    rule_cards(ctx, t, ys=(150, 290, 430), a=a, show_text=[T("c4_A", 0.2), T("c4_B", 0.2), T("c4_C", 0.2)])
    t10 = T("c4_C10", 0.3)
    if t >= t10:
        label(ctx, "10回落ちたら 当たりやすさ", 290, 600, 50, WHITE, a=fade(t, t10), align="left")
        g = ease_out(seg(t, T("c4_10x", 0.2), T("c4_10x", 0.2) + 0.6))
        label(ctx, "10倍", 1200, 600, 60 + 50 * g, YEL, a=fade(t, t10), align="left")
    t20 = T("c4_C20", 0.15)
    if t >= t20:
        label(ctx, "20回落ちたら 優先して入居（首都圏）", 290, 760, 50, WHITE, a=fade(t, t20), align="left")


def sc_c4_yoso(ctx, t):
    C4_CROWD.draw(ctx, t, a=0.6)
    person(ctx, 1400, FY, PH, "woman", WAIT, phase=0.25, pose="stand")
    slips(ctx, 1650, FY, 50, seed=31)
    ty = T("c4_yoso", 0.55)
    if t >= ty:
        panel(ctx, [("予想", 44, PANEL), ("みんな早く入れる", 64, PANEL)], 700, 220, a=fade(t, ty), bg=YEL)


D100 = (260, 540, 1400, 380)               # 100部屋（5階×20戸）


def danchi100(ctx, t, lit_n=0, a=1.0, lit_col=YEL, y=None):
    x, yy, w, h = D100
    if y is not None:
        yy = y
    door = danchi(ctx, x, yy, w, h, BLDG, floors=5, units=20, a=a)
    for k in range(int(lit_n)):
        f, i = divmod(k, 20)
        rx_, ry_, rw, rh = win_rect(x, yy, w, h, 5, 20, f, i)
        box(ctx, rx_, ry_, rx_ + rw, ry_ + rh, lit_col, a, r=2)
    return door


NEW_CROWD = Crowd((200, 640, 1700, 900), 56, 76, seed=161, facing=1)


def sc_c4_setup(ctx, t):
    tr = T("c4_rooms", 0.2)
    danchi100(ctx, t, lit_n=int(clamp01((t - tr) / 1.5) * 100) if t >= tr else 0)
    if t >= tr:
        panel(ctx, [("毎回100部屋・申込み5,140人（51.4倍のまま）", 46, YEL)], 960, 100, a=fade(t, tr))
    NEW_CROWD.draw(ctx, t)
    tn = T("c4_new", 0.1)
    if t >= tn:
        for k in range(6):
            ts = tn + 0.45 * k
            walker(ctx, t, ts, ts + 1.6, (-80, 860 + (k % 2) * 30), (180 - 20 * k, 860 + (k % 2) * 30), 76, P_KINDS[k % 5], c0=WAIT, appear=True)
        panel(ctx, [("新しく申し込む人", 44, WHITE)], 300, 600, a=fade(t, tn + 0.3))


def sc_c4_A(ctx, t):
    door = danchi100(ctx, t, lit_n=0, y=560)
    panel(ctx, [("A なし（運だけ）", 50, YEL)], 70, 105, align="left", a=1.0, border=YEL)
    tw = T("c4_Asame", 0.1)
    hide = set()
    if t >= tw:
        rnd = random.Random(5)
        idx = list(range(NEW_CROWD.n))
        rnd.shuffle(idx)
        for j, i in enumerate(idx[:16]):
            ts = tw + 0.25 * j
            if t >= ts:
                hide.add(i)
                x, y, kd = NEW_CROWD.spots[i]
                walker(ctx, t, ts, ts + 1.4, (x, y), door, 76, kd, c0=WAIT, c1=WIN, vanish=True)
    NEW_CROWD.draw(ctx, t, hide=hide)
    tv = T("c4_A37", 0.55)
    if t >= tv:
        panel(ctx, [("A 中央値 37回", 56, YEL)], 1500, 105, a=fade(t, tv), border=YEL)


TB_X = (560, 1060, 1560)                   # 表の列 A・B・C
TB_R1, TB_R2 = (205, 415), (425, 635)      # 段の上下（平均・中央値）
TB_HEAD = (("A", "なし"), ("B", "15回で優先"), ("C", "昭和63年の決まり"))
TB_MEAN = [f"{D3[k]['mean']}回" for k in "ABC"]
TB_MED = [f"{ihalf(D1['median'])}回", f"{ihalf(D3['B']['median'])}回", f"{ihalf(D3['C']['median'])}回"]      # A は問い1と同じくじなので問い1の中央値（台本どおり）


def stat_table(ctx, t, lit=(0, 1, 2), t_mean=(0.0, 0.0, 0.0), t_frame2=0.0, t_med=(0.0, 0.0, 0.0), glow=0.0):
    """平均と中央値の2段の表。t_mean・t_med は各マスの数字が出る時刻、t_frame2 は下の段が開く時刻"""
    for k, (ab, s_) in enumerate(TB_HEAD):
        on = k in lit
        panel(ctx, [(f"{ab} {s_}", 46, YEL if on else PALE)], TB_X[k], 140, a=1.0 if on else 0.6, border=YEL if on else None)
    box(ctx, 70, TB_R1[0], 1850, TB_R1[1], PANEL, 1.0, r=14)
    label(ctx, "平均", 190, sum(TB_R1) / 2, 64, WHITE)
    for k in range(3):
        if t >= t_mean[k]:
            label(ctx, TB_MEAN[k], TB_X[k], sum(TB_R1) / 2, 96, YEL, a=fade(t, t_mean[k], 0.25))
    if glow > 0:
        ctx.set_source_rgba(*hexrgb(YEL, glow))
        ctx.set_line_width(9)
        rrect(ctx, 66, TB_R1[0] - 4, 1788, TB_R1[1] - TB_R1[0] + 8, 16)
        ctx.stroke()
    if t >= t_frame2:
        a2 = fade(t, t_frame2)
        box(ctx, 70, TB_R2[0], 1850, TB_R2[1], PANEL, a2, r=14)
        label(ctx, "中央値", 190, sum(TB_R2) / 2, 64, WHITE, a=a2)
        for k in range(3):
            if t >= t_med[k]:
                label(ctx, TB_MED[k], TB_X[k], sum(TB_R2) / 2, 96, YEL, a=fade(t, t_med[k], 0.25))


def _t_mean():
    return tuple(T("c4_mean", 0.72, 0.25 * k) for k in range(3))


def _t_med():
    return (T("c4_mA", 0.6), T("c4_mBC", 0.75), T("c4_mBC", 0.75, 0.3))


def sc_c4_mean(ctx, t):
    lit = (0, 1, 2) if t >= T("c4_BC", 0.2) else (0,)
    t0 = T("c4_m0", 0.0, -0.9)
    stat_table(ctx, t, lit=lit, t_mean=_t_mean(), t_frame2=t0, t_med=_t_med())
    # 予想の札に×（中央値の段が開くまで）
    tn = T("c4_nope", 0.2)
    if tn <= t < t0 + 0.4:
        al = fade(t, tn) * out_fade(t, t0, 0.3)
        panel(ctx, [("みんな早く入れる", 56, PANEL)], 960, 720, a=al, bg=YEL)
        cross(ctx, 960, 720, 60, a=al, p=seg(t, tn + 0.3, tn + 0.9))
    # 中央値の段の小さな札
    ta = T("c4_mA", 0.2)
    if t >= ta:
        panel(ctx, [("問い1と同じくじ", 42, WHITE)], TB_X[0], 705, a=fade(t, ta), pad=(24, 10))
    tb = T("c4_mBC", 0.35)
    if t >= tb:
        panel(ctx, [("部屋を全部回したら", 42, WHITE)], (TB_X[1] + TB_X[2]) / 2, 705, a=fade(t, tb), pad=(24, 10))
    # 37 → 51 の矢印と「のびた」
    tu = T("c4_nobi", 0.2)
    if t >= tu:
        al = fade(t, tu)
        yy = sum(TB_R2) / 2 + 55
        arrow2(ctx, (735, yy), (lerp(735, 900, ease(seg(t, tu, tu + 0.6))), yy), YEL, 12, al, head=34)
        panel(ctx, [("のびた", 56, PANEL)], 815, sum(TB_R2) / 2 - 40, a=al, bg=YEL, pad=(24, 6))


def sc_c4_rooms(ctx, t):
    tw = T("c4_why", 0.2)
    door = danchi100(ctx, t, lit_n=int(clamp01((t - tw) / 2.5) * 100) if t >= tw else 0, y=520)
    panel(ctx, [("部屋 100", 52, YEL)], 960, 90, a=fade(t, tw))
    tn = T("c4_noinc", 0.2)
    if t >= tn:
        k = min(2, int((t - tn) / 2.0))
        panel(ctx, [(f"決まり {'ABC'[k]}", 52, WHITE)], 420, 620, a=fade(t, tn))
        label(ctx, "部屋の数は そのまま", 1350, 620, 50, YEL, a=fade(t, tn + 0.3))
    ts = T("c4_same", 0.2)
    if t >= ts:
        for k in range(3):
            x = 420 + 540 * k
            label(ctx, f"{'ABC'[k]}: 毎回100人", x, 740, 44, WHITE, a=fade(t, ts))
            for j in range(4):
                tj = ts + 0.3 + 0.35 * j
                walker(ctx, t, tj, tj + 1.3, (x - 120 + 80 * j, 900), (door[0] - 300 + 300 * k, 520), 70, P_KINDS[j], c0=WIN, c1=WIN, vanish=True, appear=True)


QUEUE9 = [1560 - 165 * k for k in range(9)]


def sc_c4_swap(ctx, t):
    door = danchi(ctx, 1640, 905, 260, 560, BLDG, floors=6, units=3)
    ts = T("c4_swap", 0.2)
    u = ease(seg(t, ts, ts + 1.4))
    for k, x in enumerate(QUEUE9):
        y = FY
        kd = P_KINDS[k % 5]
        col = WAIT
        if k == 6:          # 前へ出る人
            x = lerp(x, QUEUE9[0] + 60, u)
            y = FY + 20 * math.sin(math.pi * u)
            col = WIN
        elif k == 1:        # 後ろへ下がる人
            x = lerp(x, QUEUE9[8] - 165, u)
            col = "#7c8fb0"
        elif k > 1 and k < 6:
            pass
        moving = ts < t < ts + 1.4 and k in (1, 6)
        person(ctx, x, y, 200, kd, col, phase=(t * 1.6) if moving else 0.25, facing=1 if k == 6 else (-1 if k == 1 and moving else 1), pose="walk" if moving else "stand")
    if t >= ts + 0.6:
        panel(ctx, [("早く入る", 48, PANEL)], QUEUE9[0] - 40, 560, a=fade(t, ts + 0.6), bg=WIN)
        panel(ctx, [("遅くなる", 48, WHITE)], 300, 560, a=fade(t, ts + 0.8), bg="#5a6b8a")


def chair(ctx, x, y, s, a=1.0, col="#c08a52"):
    """横から見た椅子。(x, y) は脚の下の真ん中、s は高さ（背もたれの上まで）"""
    box(ctx, x - s * 0.22, y - s * 0.5, x + s * 0.22, y - s * 0.43, col, a, r=4)
    box(ctx, x - s * 0.22, y - s * 1.0, x - s * 0.15, y - s * 0.45, col, a, r=4)
    box(ctx, x - s * 0.2, y - s * 0.45, x - s * 0.15, y, mix(col, "#000000", 0.2), a, r=2)
    box(ctx, x + s * 0.15, y - s * 0.45, x + s * 0.2, y, mix(col, "#000000", 0.2), a, r=2)


def sitter(ctx, x, y, s, kind, col, a=1.0):
    """椅子に座った人（draw_person の上半身＋折った脚）。(x, y) は椅子の脚の下"""
    h = s * 1.55
    seat = y - s * 0.5
    ctx.save()
    ctx.rectangle(x - h, seat - h * 1.2, 2 * h, h * 1.2 + 2)
    ctx.clip()
    person(ctx, x - s * 0.02, seat + h * 0.34, h, kind, col, phase=0.25, pose="stand", a=a)
    ctx.restore()
    from danchi_people import palette
    P = palette(col)
    bottom = P["darkest"] if kind != "woman" else P["mid"]
    line2(ctx, (x, seat - h * 0.03), (x + h * 0.25, seat - h * 0.03), bottom, h * 0.12, a)
    line2(ctx, (x + h * 0.25, seat - h * 0.03), (x + h * 0.25, y - 6), P["skin"] if kind == "woman" else bottom, h * 0.1, a)


CHAIRS = [285 + 270 * k for k in range(6)]     # 座った人どうしが重ならない間隔（1人の幅＋ひざで約230）


def sc_c4_chair(ctx, t):
    tc = T("c4_chair", 0.15)
    u = ease(seg(t, tc, tc + 1.2))
    if u < 1:
        danchi100(ctx, t, lit_n=100, a=1 - u, y=520)
    a = u
    for k, x in enumerate(CHAIRS):
        chair(ctx, x, 900, 240, a=a)
    label(ctx, "椅子＝部屋", 960, 160, 60, YEL, a=a)
    ts = T("c4_seat", 0.1)
    for k, x in enumerate(CHAIRS):
        if t < tc + 1.2:
            continue
        swap = t >= ts and ((k + int((t - ts) / 0.9)) % 3 == 0)
        col = WIN if not swap else "#f7bf86"
        sitter(ctx, x, 900, 240, P_KINDS[(k + (1 if swap else 0)) % 5], col, a=a)
    if t >= ts:
        for k in range(5):
            person(ctx, 300 + 300 * k, 520, 150, P_KINDS[k], WAIT, phase=(t * 1.2 + k * 0.3), facing=1, pose="walk", a=fade(t, ts))
        tsum = T("c4_seat", 0.45)
        if t >= tsum:
            panel(ctx, [("待った回数の合計は 同じ", 52, YEL)], 1500, 300, a=fade(t, tsum))
    tg = T("c4_giveup", 0.3)
    if t >= tg:
        panel(ctx, [("当たるまであきらめないと仮定", 50, WHITE)], 700, 300, a=fade(t, tg))


ORDER_RNG = np.random.default_rng(3)
ORDER_A = ORDER_RNG.permutation(60)
ORDER_B = np.arange(60)[::-1]


def sc_c4_order(ctx, t):
    a = 1.0
    label(ctx, "入った順（左から）・色＝待った回数", 960, 140, 46, PALE, a=a)
    tw = T("c4_who", 0.2)
    for k, ab in enumerate("ABC"):
        y = 330 + 190 * k
        label(ctx, ab, 160, y, 72, YEL, a=a)
        order = ORDER_A if k == 0 else ORDER_B
        u = ease(seg(t, tw, tw + 1.4)) if k > 0 else 1.0
        for j in range(60):
            v = order[j] if k == 0 else (ORDER_A[j] * (1 - u) + ORDER_B[j] * u)
            col = mix(WIN, "#6d5bd0", v / 59)
            box(ctx, 240 + j * 26, y - 55, 240 + j * 26 + 22, y + 55, col, a, r=3)
    if t >= tw:
        panel(ctx, [("変えたのは、運の差", 56, YEL)], 960, 860, a=fade(t, tw + 0.4))


QSIZE = 190                     # 列の人（480px でも人と分かる大きさ）
QN, QGAP = 16, 90               # 列の人数・間隔。詰めすぎず、1本の列と一目で分かるように
L_CROWD = Crowd((110, 480, 1330, 900), QN, QSIZE, seed=171, facing=1)
Q_ORDER = sorted(range(L_CROWD.n), key=lambda i: random.Random(i * 7 + 1).random())
DQ = (1510, 900, 370, 440)
Q_STAG, Q_MOVE = 0.05, 1.6


def qpos(j, adv=0.0):
    return (DQ[0] - 60 - (j - adv) * QGAP, 900)


def q_done():
    """群れが1本の列に並び終わる時刻"""
    return T("c4_line", 0.1) + Q_STAG * (QN - 1) + Q_MOVE


def sc_c4_line(ctx, t):
    door = danchi(ctx, *DQ, BLDG, floors=5, units=5)
    ta = T("c4_all", 0.2)
    if t >= ta:
        panel(ctx, [("部屋を全部、優遇の人に回せる場合", 50, YEL)], 760, 110, a=fade(t, ta))
    tl0 = T("c4_line", 0.1)
    t52 = T("c4_52", 0.2)
    td = q_done()
    adv = clamp01((t - t52) / 2.5) * 5 if t >= t52 else 0.0
    if t >= td - 0.8:
        al = fade(t, td - 0.8, 0.5)
        box(ctx, 30, 888, door[0] + 40, 922, "#ffffff", 0.16 * al, r=10)
    # 列の後ろから、まだ画面の外にいた人も入ってくる（前の人が入るぶん、列が進む）
    for j in range(QN + 6):
        qx, qy = qpos(j, adv)
        if qx > door[0] + 30 or qx < -120:
            continue
        al = clamp01((door[0] + 30 - qx) / 70)
        if j < QN:
            i = Q_ORDER[j]
            x, y, kd = L_CROWD.spots[i]
            u = ease(seg(t, tl0 + Q_STAG * j, tl0 + Q_STAG * j + Q_MOVE))
            px_, py_ = lerp(x, qx, u), lerp(y, qy, u)
            moving = (0 < u < 1) or (t >= t52 and adv < 5)
        else:
            if t < td - 0.6:                       # 列の後ろの人は、列ができるころに入ってくる
                continue
            al *= fade(t, td - 0.6, 0.4)
            kd = P_KINDS[j % 5]
            px_, py_ = qx, qy
            moving = t >= t52 and adv < 5
        person(ctx, px_, py_, QSIZE, kd, WAIT, phase=t * 1.4 + j * 0.1, facing=1, pose="walk" if moving else "stand", a=al)
    if t >= td:
        al = fade(t, td, 0.3)
        arrow2(ctx, (260, 665), (1400, 665), YEL, 10, al)
        panel(ctx, [("1本の列", 64, PANEL)], 640, 575, a=al, bg=YEL, pad=(36, 10))
    tv = T("c4_52", 0.55)
    if t >= tv:
        panel(ctx, [("最長 B・C 52回", 56, YEL)], 1280, 260, a=fade(t, tv), border=YEL)


SAVED_Q = [1500 - 260 * k for k in range(6)]


def sc_c4_saved(ctx, t):
    door = danchi(ctx, 1580, 905, 320, 600, BLDG, floors=6, units=3)
    ts = bd("c4_saved") + 0.4
    steps = (t - ts) / 0.9 if t >= ts else 0.0
    for k in range(6):
        pos = k - steps
        x = 1500 - 260 * pos
        if pos < 0:
            if pos < -0.6:
                continue
        a = clamp01(1 + pos / 0.6) if pos < 0 else 1.0
        moving = (steps % 1) < 0.6 and t >= ts
        kd = "woman" if k == 3 else P_KINDS[k % 5]
        col = WIN if (k == 3 and pos < 0.2) else WAIT
        person(ctx, x, FY, PH, kd, col, phase=t * 1.4, facing=1, pose="walk" if moving else "stand", a=a)
        if k == 3:
            slips(ctx, x - 170, FY, 46, seed=31, a=a)
    tc = T("c4_saved", 0.3)
    if t >= tc:
        panel(ctx, [("運の悪かった人も、順番が来る", 50, YEL)], 760, 180, a=fade(t, tc))


def sc_c4_none(ctx, t):
    door = danchi100(ctx, t, lit_n=100, y=540)
    tn = T("c4_none", 0.4)
    if t >= tn:
        panel(ctx, [("1回目で当たる人: B・C 100人に0人", 50, YEL)], 960, 90, a=fade(t, tn), border=YEL)
    tcl = T("c4_closed", 0.3)
    nx = lerp(-200, 560, ease(seg(t, bd("c4_none") + 0.5, bd("c4_none") + 2.3)))
    walker(ctx, t, bd("c4_none") + 0.5, bd("c4_none") + 2.3, (-200, FY), (560, FY), PH, "man", c0=WAIT)
    # 扉が閉まる（入口の前）
    if t >= tcl:
        u = ease(seg(t, tcl, tcl + 0.9))
        box(ctx, 780, 590, 1180, 905, "#3a3048", 1.0, r=6)
        box(ctx, 800, 610, 800 + 180 * u, 905, "#8a6a44", 1.0, r=4)
        box(ctx, 1160 - 180 * u, 610, 1160, 905, "#8a6a44", 1.0, r=4)
        if u > 0.9:
            ball(ctx, 960 - 18, 760, 8, YEL)
            ball(ctx, 960 + 18, 760, 8, YEL)
        label(ctx, "部屋は残らない", 1500, 700, 52, WHITE, a=fade(t, tcl + 0.5))


Y_CROWD = Crowd((60, 420, 640, 770), 20, 110, seed=181, facing=1)
YQ_GAP, YQ_SZ = 70, 130
YQ = [1420 - YQ_GAP * k for k in range(10)]


def sc_c4_you(ctx, t):
    door = danchi(ctx, 1460, 770, 420, 440, BLDG, floors=5, units=5)
    tw = T("c4_wait", 0.1)
    adv = clamp01((t - tw) / 2.0) * 3 if t >= tw else 0.0
    for k, x in enumerate(YQ):
        xx = x + YQ_GAP * adv
        if xx > 1450:
            continue
        person(ctx, xx, 770, YQ_SZ, P_KINDS[k % 5], WAIT, phase=t * 1.5, facing=1, pose="walk" if 0 < adv < 3 else "stand")
    Y_CROWD.draw(ctx, t)
    ty = bd("c4_you") + 0.4
    tk = T("c4_keep", 0.1)
    n = int(clamp01((t - tk) / 2.4) * 15) if t >= tk else 0
    t15 = T("c4_15", 0.3)
    if t < t15:
        walker(ctx, t, ty, ty + 1.6, (-200, FY), (330, FY), PH, "man", c0=WIN)
    elif t < tw:
        walker(ctx, t, t15, t15 + 1.6, (330, FY), (820, FY), PH, "man", c0=WIN)
    else:
        walker(ctx, t, tw, tw + 2.0, (820, FY), (1060, FY), PH, "man", c0=WIN)
    if t >= tk and t < t15 + 0.5:
        slips(ctx, 560, FY, n, seed=41, a=out_fade(t, t15))
        _counter(ctx, t, 640, 420, n, a=out_fade(t, t15))
    if t >= t15:
        panel(ctx, [("15回落ちて、列へ", 48, YEL)], 820, 330, a=fade(t, t15 + 0.2))


def sc_c4_lucky(ctx, t):
    door = danchi(ctx, 1460, 770, 420, 440, BLDG, floors=5, units=5)
    for k, x in enumerate(YQ):
        person(ctx, x, 770, YQ_SZ, P_KINDS[k % 5], WAIT, phase=0.25, facing=1, pose="stand")
    tl0 = bd("c4_lucky") + 0.4
    walker(ctx, t, tl0, tl0 + 1.8, (-200, FY), (420, FY), PH, "woman", c0=WIN)
    tc = T("c4_lucky", 0.4)
    if t >= tc:
        panel(ctx, [("問い1なら", 44, WHITE), ("1回目で当たった人", 50, YEL)], 420, 330, a=fade(t, tc))
    tq = T("c4_queue", 0.5)
    if t >= tq:
        panel(ctx, [("B・C 中央値 51回", 56, YEL)], 1200, 200, a=fade(t, tq), border=YEL)


SPLIT_A = Crowd((70, 560, 890, 890), 22, 104, seed=191, facing=1)


def sc_c4_split(ctx, t):
    ts, t2 = T("c4_split", 0.0), T("c4_same2", 0.0)
    aA = 1.0 if t < t2 else 0.55
    aB = 0.55 if t < t2 else 1.0
    doorA = danchi(ctx, 330, 470, 300, 260, BLDG, floors=4, units=4, a=aA)
    panel(ctx, [("A 運だけ", 50, YEL)], 480, 110, a=aA)
    hide = set()
    rnd = random.Random(11)
    picks = list(range(SPLIT_A.n))
    rnd.shuffle(picks)
    for j, i in enumerate(picks[:10]):
        tj = ts + 0.3 + rnd.uniform(0, 4.5)
        if t >= tj:
            hide.add(i)
            x, y, kd = SPLIT_A.spots[i]
            walker(ctx, t, tj, tj + 1.3, (x, y), doorA, 104, kd, c0=WAIT, c1=WIN, vanish=True, a=aA)
    SPLIT_A.draw(ctx, t, hide=hide, a=aA)
    doorB = danchi(ctx, 1520, 880, 330, 400, BLDG, floors=5, units=4, a=aB)
    panel(ctx, [("B 順番待ちの列", 50, YEL)], 1440, 110, a=aB)
    adv = ((t - t2) / 0.7) if t >= t2 else 0.0
    for k in range(8):
        pos = k - adv % 1 if t >= t2 else k
        x = 1460 - pos * 66
        person(ctx, x, 880, 120, P_KINDS[k % 5], WAIT, phase=t * 1.6, facing=1, pose="walk" if t >= t2 else "stand", a=aB * clamp01(1 + pos))
    line2(ctx, (960, 180), (960, 900), "#ffffff", 3, 0.5)


DETAIL = [("上限なし", D3["B"]), ("優先は部屋の半分まで", D3["B_cap50"]), ("3割まで", D3["B_cap30"]), ("あきらめる人を混ぜた線", D3["C_drop1"])]


def sc_c4_detail(ctx, t):
    tc = T("c4_detail", 0.1)
    panel(ctx, [("待ちの散らばり方は、決まりの細かさで大きく変わる", 54, YEL)], 960, 120, a=fade(t, tc), border=YEL)
    px = 1100 / 160
    th = T("c4_half", 0.05)
    x0 = 680
    for k, (nm, d) in enumerate(DETAIL):
        y = 290 + 135 * k
        tk = tc + 0.4 + 0.3 * k
        if t < tk:
            continue
        a = fade(t, tk)
        on = k == 1 and t >= th
        dim = 0.45 if (t >= th and k != 1) else 1.0
        if on:
            glow = 0.7 + 0.3 * math.cos((t - th) * 2 * math.pi / 1.1)
            box(ctx, 70, y - 50, 1800, y + 50, "#ffffff", 0.14 * glow, r=12)
            ctx.set_source_rgba(*hexrgb(YEL, glow))
            ctx.set_line_width(6)
            rrect(ctx, 70, y - 50, 1730, 100, 12)
            ctx.stroke()
        label(ctx, nm, 640, y, 42, YEL if on else WHITE, a=a * dim, align="right")
        box(ctx, x0, y - 26, x0 + 160 * px, y + 26, "#2c4366", a * dim, r=6)
        box(ctx, x0 + 1 * px, y - 26, x0 + min(160, d["p90"]) * px, y + 26, WIN, a * 0.85 * dim, r=6)
        tri_down(ctx, x0 + d["median"] * px, y - 30, 14, YEL, a * dim)
    tv = T("c4_half", 0.3)
    if t >= tv:
        c5 = D3["B_cap50"]
        panel(ctx, [(f"Bの場合  1回目で当たる人 100人に{D3['B']['first']:.0f}人 → {c5['first']}人", 42, WHITE), (f"いちばん長い人 {D3['B']['max']}回 → {c5['max']}回", 42, YEL)], 950, 830, a=fade(t, tv), pad=(24, 10))


HELP_X, HELPER_X = 330, 590


def sc_c4_end0(ctx, t):
    tr = T("c4_rooms2", 0.1)
    g = 0.0
    if t >= tr:
        g = 0.55 + 0.45 * math.cos((t - tr) * 2 * math.pi / 0.9)
    stat_table(ctx, t, glow=g)
    if t >= tr:
        panel(ctx, [("変わらないのは 平均", 60, YEL)], 960, 730, a=fade(t, tr))


def sc_c4_end(ctx, t):
    danchi100(ctx, t, lit_n=100, a=1.0, y=520)
    th = T("c4_help", 0.1)
    if t >= th:
        a = fade(t, th)
        slips(ctx, HELP_X - 190, FY, 40, seed=31, a=a)
        person(ctx, HELP_X, FY, PH, "woman", WAIT, phase=0.25, pose="stand", a=a)
        tw, ta = th + 0.1, th + 1.4                       # 歩いてきて、止まってから手を差し出す
        if t < ta:
            walker(ctx, t, tw, ta, (1120, FY), (HELPER_X, FY), PH, "man", c0=WIN, facing=-1, a=a)
        else:
            draw_person_reach(ctx, HELPER_X, FY, PH, "man", WIN, facing=-1, reach=ease(seg(t, ta, ta + 0.6)))
    tsm = T("c4_someone", 0.1)
    if t >= tsm:
        for k in range(6):
            ts = tsm + 0.5 * k
            walker(ctx, t, ts, ts + 1.6, (2000, 880), (1800 - 70 * k, 880), 110, P_KINDS[k % 5], c0=WAIT, appear=True)


# 運だけ（問い1のくじ）の待ちの分かれ方と、部屋を全部回したときの待ち。線は平均（どちらも約51回）
WAIT_A8 = [float(np.quantile(Q1, (i + 0.5) / 8)) for i in range(8)]
WAIT_A5 = [float(np.quantile(Q1, q_)) for q_ in (0.1, 0.3, 0.5, 0.7, 0.9)]
WAIT_B = float(D3["B"]["mean"])


def wait_bars(ctx, x0, y0, vals, px, bh, step, col=WIN, u=1.0, a=1.0):
    for k, v in enumerate(vals):
        uu = ease(clamp01(u * (len(vals) + 2) - k * 0.6))
        box(ctx, x0, y0 + k * step, x0 + v * px * uu, y0 + k * step + bh, col, a, r=4)


def mean_line(ctx, x0, px, y0, y1, a=1.0):
    xm = x0 + WAIT_B * px
    line2(ctx, (xm, y0), (xm, y1), WHITE, 5, a, dash=[12, 9])
    return xm


def sc_c4_ans(ctx, t):
    tc = T("c4_ans", 0.1)
    label(ctx, "答え", 960, 85, 64, YEL)
    panel(ctx, [("平均は同じ。運の差が消える", 76, YEL), ("部屋を全部回したら", 48, WHITE)], 960, 235, a=fade(t, tc), border=YEL, pad=(60, 20))
    px = 4.0
    # 左: 運だけ（ばらばら）→ 右: 部屋を全部回したら（そろう）。平均の線は同じ所
    for k, (x0, nm, vals, t0) in enumerate(((130, "A 運だけ", WAIT_A8, T("c4_ans", 0.45)), (1040, "B・C 部屋を全部回したら", [WAIT_B] * 8, T("c4_ans2", 0.0)))):
        if t < t0:
            continue
        a = fade(t, t0)
        label(ctx, nm, x0, 385, 46, WHITE, a=a, align="left")
        wait_bars(ctx, x0, 430, vals, px, 30, 42, u=seg(t, t0, t0 + 1.4), a=a)
        xm = mean_line(ctx, x0, px, 420, 775 + 40, a)
        label(ctx, "平均 約51回", xm, 860, 44, WHITE, a=a)


# ============================================================
# 5 まとめ・終了画面
# ============================================================
ANS3 = [["運だけなら", "中央値37回"], ["早く入る道は、", "何かと引きかえ"], ["平均は同じ。", "運の差が消える"]]


C5_X, C5_W, C5_TOP, C5_BOT = (330, 960, 1590), 590, 44, 918
C5_ROWS = [[("運だけなら", 84, WHITE, 125), ("中央値", 84, WHITE, 235), ("37回", 170, YEL, 385)],
           [("早く入る道は、", 74, WHITE, 125), ("何かと", 96, WHITE, 235), ("引きかえ", 124, YEL, 385)],
           [("平均は同じ。", 84, WHITE, 125), ("運の差が消える", 74, YEL, 235)]]


def sc_c5_answers(ctx, t):
    # 答えの札3枚を、画面の上から字幕の上まで使って大きく出す。下半分はそれぞれの答えの絵
    t0 = ch_start(5) + T_TITLE[5]
    for k, rows in enumerate(C5_ROWS):
        x = C5_X[k]
        a = fade(t, t0 + 0.2 + 0.4 * k)
        if a <= 0.003:
            continue
        hl = (k <= 1 and T("c5_0", 0.0) <= t < T("c5_1", 0.0)) or (k == 2 and t >= T("c5_1", 0.0))
        box(ctx, x - C5_W / 2, C5_TOP, x + C5_W / 2, C5_BOT, PANEL, a, r=26)
        if hl:
            ctx.set_source_rgba(*hexrgb(YEL, a))
            ctx.set_line_width(7)
            rrect(ctx, x - C5_W / 2 + 4, C5_TOP + 4, C5_W - 8, C5_BOT - C5_TOP - 8, 22)
            ctx.stroke()
        for s_, sz, col, yy in rows:
            label(ctx, s_, x, yy, sz, col, a=a)
        if k == 0:
            slips(ctx, x + 150, 898, 30, a=a, seed=7)
            person(ctx, x - 90, 898, PH - 20, "man", WIN, phase=0.25, pose="stand", a=a)
        elif k == 1:
            danchi(ctx, x + 10, 898, 250, 300, BLDG, floors=4, units=3, a=a)
            person(ctx, x - 150, 898, PH - 20, "woman", WIN, phase=0.25, pose="stand", a=a)
        else:
            # 上「運だけ」＝ばらばら ／ 下「部屋を全部回したら」＝そろう。線は同じ平均
            x0, px = x - 250, 2.75
            label(ctx, "運だけ", x0, 345, 44, WHITE, a=a, align="left")
            wait_bars(ctx, x0, 385, WAIT_A5, px, 30, 42, a=a)
            label(ctx, "部屋を全部回したら", x0, 635, 44, WHITE, a=a, align="left")
            wait_bars(ctx, x0, 672, [WAIT_B] * 5, px, 30, 42, a=a)
            xm = mean_line(ctx, x0, px, 375, 605, a)         # 線は「部屋を全部回したら」の字をまたがない
            mean_line(ctx, x0, px, 664, 885, a)
            label(ctx, "平均", xm + 80, 345, 44, YEL, a=a)


C5_CROWD = Crowd((80, 560, 900, 890), 30, 84, seed=201, facing=1)


def sc_c5_close(ctx, t):
    tq = T("c5_q", 0.0)
    C5_CROWD.draw(ctx, t)
    danchi(ctx, 1300, 760, 520, 420, BLDG, floors=5, units=6)
    person(ctx, 1000, FY, PH, "man", WIN, phase=0.25, pose="stand")
    panel(ctx, [("あなたなら、", 56, WHITE), ("何回まで申し込みますか？", 64, YEL)], 80, 175, a=fade(t, tq), border=YEL, align="left")
    tn = T("c5_note", 0.05)
    if t >= tn:
        panel(ctx, [("数字は、この動画の仮定で計算した結果。", 42, WHITE), ("当時の一人ひとりの待ちを、言い当てるものではない", 42, WHITE)], 80, 380, a=fade(t, tn), align="left")


END_SUB = ["面白かったと思ってもらえたら", "チャンネル登録・高評価", "よろしくお願いします"]


def end_rows():
    return [("運だけなら、半分が当たるまで", f"{ihalf(D1['median'])}回"), ("早く入る道は", "何かと引きかえ"), ("部屋を全部回したら", "平均は同じ。運の差が消える")]


def sc_end(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    label(ctx, "答え", 490, 90, 80, YEL, a=b)
    for k, (lab, val) in enumerate(end_rows()):
        panel(ctx, [(lab, 52, WHITE), (val, 70 if len(val) <= 10 else 60, YEL)], 490, 265 + 245 * k, a=b, pad=(40, 24))
    t9 = T_ES + 0.5
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, 1400, 480, 1.25, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        panel(ctx, [(s_, 56, YEL if k == 1 else WHITE) for k, s_ in enumerate(END_SUB)], 1430, 720, a=fade(t, t9 + 0.3, 0.4))


# ============================================================
# 区切り（ここまで／ここから・カメが歩く）。engine/longkit.py の Eyecatch を、平たい地・白と黄色の文字で描き直したもの
# ============================================================
EC_LEFT = ("運だけなら中央値37回", "倍率の低めの団地なら11回", "待つより出し続けたほうが早い")
EC_RIGHT = ("何度も落ちた人を、", "先に入れたら？")
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
        from engine.brand import turtle
        paint_bg(ctx, EC_BG)
        fill(ctx, hexrgb("#ffffff", 0.18))
        ctx.rectangle(958, 60, 4, 820)
        ctx.fill()
        self._page(ctx, t, self.lx, "ここまで", self.left, True)
        self._page(ctx, t, self.rx, "ここから", self.right, False)
        for i, (px, tf) in enumerate(self._foots()):
            if t >= tf:
                ctx.set_source_rgba(1, 1, 1, 0.35 * ease_out(clamp01((t - tf) / 0.12)))
                ctx.arc(px, self.Y + 18 + (7 if i % 2 else -7), 6, 0, 2 * math.pi)
                ctx.fill()
        u = self._u(t)
        x = self.X0 + (self.X1 - self.X0) * u
        tr = t - self.t0
        blink = 1.0 if 0.35 < tr % 1.8 < 0.47 else 0.0
        bob = 3 * abs(math.sin(tr * 6.0))
        turtle(ctx, x, self.Y - bob, self.TURTLE_S, blink=blink)


EC = FlatEyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None


# ============================================================
# 場面を並べる
# ============================================================
def _start_of(spec):
    if spec == "zero":
        return 0.0
    if spec == "end":
        return T_ES
    if spec.startswith("ch:"):
        n = int(spec[3:])
        # 問いの章は、章カードの後ろで絵を先に出す（絵に文字を置くのはカードの外か、カードが消えてから）。まとめはカードのあと
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
    scene(_nm, _start_of(_spec), _end_of(_j), globals()[_fn], first=(_nm == "open"))


def draw(ctx, t, sub=True):
    paint_bg(ctx, bg_color(t))
    ea = EC.alpha(t) if (EC and T_RS0 <= t < T_RS1) else 0.0
    if ea < 0.5:
        draw_scenes(ctx, t)
        overlays(ctx, t)
    if ea > 0.003:
        EC.draw(ctx, t)
    if sub:
        lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・結果の数字・区切りの足音）
# ============================================================
def turtle_step(seed=0, high=False):
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    n = np.random.default_rng(seed + 50).standard_normal(len(tt))
    n = np.convolve(n, np.ones(12) / 12, mode="same") * np.exp(-tt * 120) * 0.35
    return (tone * env + n) * 0.8


BELLS = [T("c0_10k", 0.62), T("c2_med", 0.55), T("c2_b3", 0.5), T("c3_r2", 0.55), T("c3_21", 0.4), T("c4_mean", 0.72), T("c4_nobi", 0.2), T("c4_52", 0.55)]


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    from long_bgm import bgm_track      # 2026-11-06 カスミソウ（甘茶の音楽工房）
    mx.add(0, bgm_track(DUR, lf.SR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for n in range(1, LAST_CH + 1):
        mx.add(S(f"ch{n}"), whoosh(0.6), 0.3)
    if EC:
        for i_, ts_ in enumerate(EC.step_times()):
            mx.add(ts_, turtle_step(seed=i_, high=bool(i_ % 2)), 0.32)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(T("c5_q", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(T("c5_sub", 0.0) + 0.2, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（要所6枚）
# ============================================================
def still_list():
    return [
        ("1_open", "① 冒頭: 昭和41年・群れと部屋1・あなた", T("c0_lose1", 0.0) + 1.0),
        ("2_c1_plan", "② 1章: 2DKと食卓につく家族", T("c1_bath", 0.0) + 2.4),
        ("3_c2_hist", "③ 2章: 1万人の分布（1人＝100人）", T("c2_80", 0.0) + Dk("c2_80") + 0.5),
        ("4_c3_add", "④ 3章: 4人＋すぐ出し続ける人", T("c3_add", 0.25) + 2.2),
        ("5_c4_line", "⑤ 4章: 1本の列ができきったところ", q_done() + 0.5),
        ("6_c5_answers", "⑥ まとめ: 3つの答えの札", T("c5_0", 0.5)),
    ]


def _ts(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def end2_list():
    return [
        ("c2_hist", "2章: 札「平均 50回あまり」", T("c2_why", 1.0, -0.1)),
        ("c4_rules", "4章: 3つの決まり（B 先に入れる）", T("c4_C20", 1.0, 0.2)),
        ("c4_mean", "4章: 2段の表（B 15回で優先）", T("c4_nobi", 1.0, 0.2)),
        ("c4_chair", "4章: 待った回数の合計は同じ", T("c4_seat", 1.0, -0.1)),
        ("c4_line", "4章: BとCの中を見る", T("c4_all", 1.0, -0.1)),
        ("c4_lucky", "4章: 運のいい人はいなくなった", T("c4_lucky", 1.0, -0.1)),
        ("c4_detail_a", "4章: 帯の図", T("c4_detail", 1.0, -0.1)),
        ("c4_detail_b", "4章: 部屋の半分までの帯が光る", T("c4_half", 1.0, 0.2)),
    ]


def end_list():
    return [
        ("c4_mean_a", "c4_mean: 平均の段と×", T("c4_nope", 1.0, -0.1)),
        ("c4_mean_b", "c4_mean: 中央値 A", T("c4_mA", 1.0, -0.1)),
        ("c4_mean_c", "c4_mean: 2段の表と「のびた」", T("c4_nobi", 1.0, 0.2)),
        ("c4_order", "c4_order: 変えたのは運の差", T("c4_who", 1.0, 0.5)),
        ("c4_end0", "c4_end0: 平均の段が光る", T("c4_rooms2", 1.0, 0.2)),
        ("c4_ans", "問い3の答え", T("c4_ans2", 1.0, 0.2)),
        ("c5_answers", "まとめの札3枚", T("c5_1", 0.6)),
        ("end", "最後の画面", DUR - 1.0),
    ]


def fix_list():
    return [
        ("c3_map", "3章 c3_map: 4つの札と倍率に合わせた群れ", T("c3_where", 1.0, -0.1)),
        ("c3_dec_a", "3章 c3_dec: 矢印が伸びるところ", T("c3_dec", 0.0, 1.0)),
        ("c3_dec_b", "3章 c3_dec: 矢印と札", T("c3_dec", 1.0, -0.1)),
        ("c4_end_a", "4章 c4_end: 歩いてくるところ", T("c4_help", 0.1, 0.8)),
        ("c4_end_b", "4章 c4_end: 手を差し出す", T("c4_help", 1.0, -0.1)),
        ("c4_end_c", "4章 c4_end: 列に新しい人が並ぶ", T("c4_someone", 1.0, -0.1)),
    ]


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


def body_extra():
    """場面の終わりだけでは人が団地に入ったあとになる場面の、見せたいコマ（場面の名前: 時刻）"""
    return {"c2_best": T("c2_b2", 0.35) + 1.0, "c3_all": T("c3_all", 0.3) + 0.8, "c4_line": q_done() + 0.5, "c4_saved": bd("c4_saved") + 2.0,
            "c2_medp": T("c2_m1", 0.2) + 2.5, "c4_you": T("c4_keep", 0.1) + 2.0, "c3_low": T("c3_l11", 0.1)}



def body_sheet():
    """本編の静止画一覧: 全場面（30秒を超える場面は途中のコマも）を 480px 幅で並べる。out/danchi-long/body_stills_480.png と4枚割りの p1〜"""
    from PIL import Image, ImageDraw, ImageFont
    d = WORK / "body"
    d.mkdir(parents=True, exist_ok=True)
    items = []
    extra = body_extra()
    for nm, t0, t1, *_r in SCENES:
        if nm == "end":
            items.append((nm, DUR - 1.0))
            continue
        if nm in extra:
            items.append((nm + "・途中", extra[nm]))
        elif t1 - t0 > 20:
            items.append((nm + "・途中", t0 + (t1 - t0) * 0.5))
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
    for p_i, i0 in enumerate(range(0, len(cells), 16)):
        sheet(cells[i0:i0 + 16], OUT / f"body_stills_480_p{p_i + 1}.png")


def write_voice_md(path):
    """check-long の句読点の間の点検に渡す台本（読みの補正つき＝実際に声に渡した文）。「- 」の行だけ"""
    rows = ["## 0 声に渡した文（読みの補正つき。sims/danchi-long.py --voicemd が出力）"]
    for it in tl.items:
        if isinstance(it, lf.Line):
            rows.append("- " + it.text)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("声に渡した文:", path)


def _screen_texts():
    """frames_real.pkl（本番の声の文字の箱）から、文ごとに新しく画面に出た文字を集める。{文の id: [文字, …]}"""
    import pickle
    pk = (WORK / "frames.pkl") if FAKE else (OUT / "frames_real.pkl")
    if not pk.exists():
        return {}
    frames = pickle.loads(pk.read_bytes())
    ids = [it.id for it in tl.items if isinstance(it, (lf.Line, lf.Gap))]
    starts = [S(i) for i in ids]
    out, seen, where = {}, set(), {}
    for t, ents in frames:
        cur = set()
        for e in ents:
            s_ = e[0]
            if s_.startswith("字幕: ") or s_ == "":
                continue
            g = _re.sub(r"\d+", "#", s_) if s_.startswith("落選 ") else s_
            cur.add(g)
            if g not in seen:
                seen.add(g)
                k = max(0, np.searchsorted(starts, t, side="right") - 1)
                if t > E(ids[k]) and k + 1 < len(ids):            # 文と文の間に出た字は、次の文の欄に書く
                    k += 1
                out.setdefault(ids[k], []).append(s_)
                where[g] = (ids[k], len(out[ids[k]]) - 1, s_)
            elif s_.startswith("落選 ") and g in where:
                i_, j_, first = where[g]
                if first != s_:
                    out[i_][j_] = f"{first}→{s_}"
        seen &= cur
    return out


ACTUAL_NOTE = {
    "c1_work": "父の絵が、かばんを持って団地から歩いていく",
    "c2_10k": "左に団地と1万人の群れ。人が少しずつ歩き出して団地へ入る（オレンジに変わる）。右は回ごとの棒の枠",
    "c2_each51": "右に棒が1本ずつ増える。群れは少しずつ減る",
    "c2_mean": "柱の上で、平均の印が中央値の印より右へ動く。札「平均 50回あまり」",
    "c2_why": "平均の札から右へ黄色い矢印",
    "c3_keep": "前半: 点線「1人目は 51倍のまま」。後半: 下がる黄色い線が引かれ、5人目が地面を右へ歩く",
    "c3_w4": "下の段に数年待つ人と、めくれ続ける暦。灰色の帯（待つ・くじなし）が伸びる。上の段はすぐ出し続ける人と21回の帯",
    "c3_faster": "すぐ出し続ける人が歩いて右上の団地へ入る。数年待つ人はその場に立ったまま",
    "c4_same": "団地の窓は全部光ったまま。札「A: 毎回100人」「B: 毎回100人」「C: 毎回100人」。人が団地へ歩いていく",
    "c4_none": "窓がすべて光った団地。新しく来た人が左から歩いてくる。札「1回目で当たる人: B・C 100人に0人」",
    "c4_you": "左に群れ、右に団地と列。オレンジのあなたが左から歩いてくる",
    "c4_keep": "あなたの足もとに落選の札が増える。札「落選 N枚」",
    "c4_detail": "札「待ちの散らばり方は、決まりの細かさで大きく変わる」と、小さな帯の図4本（上限なし／優先は部屋の半分まで／3割まで／あきらめる人を混ぜた線）。中央値の数字は出さない",
    "c4_ans": "札「平均は同じ。運の差が消える」「部屋を全部回したら」。左に「A 運だけ」の帯（ばらばら）。線は平均",
    "c4_ans2": "右に「B・C 部屋を全部回したら」の帯（そろう）。線は左と同じ平均",
    "c4_seat": "椅子に座る人が入れ替わる。札「待った回数の合計は 同じ」",
    "c4_lucky": "オレンジの人が左から歩いてくる。札「問い1なら 1回目で当たった人」。奥に列と団地",
}


def write_transcript(path):
    scr = _screen_texts()
    actual = {ID[k]: v for k, v in ACTUAL_NOTE.items()}
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
            nt = actual.get(it.id, LINE_NOTE.get(it.id))
            txts = scr.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else "")
                        + (f"  〔画面の文字: {'／'.join(txts)}〕" if txts else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


WATCH = ["昭和41年", "51倍", "51.4倍", "空き家", "団地族", "公団", "公社", "中央値", "倍率", "昭和63年", "1万人", "37回", "一生", "約7年半", "約5年", "2DK"]


def write_readings(path):
    """読みの確認。read_aloud は AivisSpeech を起動するので、--fake-voice のときは --real-readings を付けない限り、文だけ並べる"""
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
    _val("札「半分の人が当たるまで 37回」", "c0_10k", 0.62),
    _fr("回ごとの棒の枠", "c2_10k", "c2_each51"),
    _val("札「51.4倍」", "c2_cont", 0.5), _val("箱「中央値 37回目」", "c2_med", 0.55),
    _fr("1万人の分布の枠（柱の名前・1人＝100人）", "c2_hist", "c2_hist"),
    _val("札「10人に1人は 122回以上」", "c2_p90", 0.25), _val("札「100人に21人」", "c2_80", 0.62), _val("札「平均 50回あまり」", "c2_mean", 0.62),
    _val("札「100人に1.7人」", "c2_b3", 0.4), _val("札「37回目で当選」", "c2_m2", 0.45), _val("札「最長 520回」", "c2_w2", 0.6),
    _val("札「100人に15人」", "c2_15", 0.7),
    _fr("記録と計算の100人の枠", "c2_cmp", "c2_56"), _val("札「100人に56人」", "c2_56", 0.55),
    _fr("3つの団地の枠", "c3_kinds", "c3_diff"),
    _fr("4つの群れの枠", "c3_10k", "c3_10k"), _val("箱「中央値 37回」", "c3_r1", 0.55), _val("箱「中央値 11回」", "c3_r2", 0.55),
    _val("札「中央値 21回」", "c3_21", 0.4), _val("札「年4回なら 約5.2年」", "c3_5y", 0.3), _val("札「中央値 14回」", "c3_14", 0.55),
    _val("札「30回ぶん（約7.5年）」", "c3_75", 0.3),
    _fr("3つの決まりの枠", "c4_rules", "c4_three"), _val("箱「A 中央値 37回」", "c4_A37", 0.55),
    _fr("平均と中央値の表の枠", "c4_mean", "c4_mean"), _val("表「平均 51.3回」", "c4_mean", 0.72),
    lk.Cue("表の中央値の段の枠", "frame", T("c4_m0", 0.0, -0.9), T("c4_m0", 0.0, -0.6), ID["c4_m0"]),
    _val("表「中央値 37回」", "c4_mA", 0.6), _val("表「中央値 51回」", "c4_mBC", 0.75), _val("札「最長 B・C 52回」", "c4_52", 0.55), _val("札「B・C 中央値 51回」", "c4_queue", 0.5),
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
    ok |= set(float(x) for x in range(0, 61))                  # 月・落選の札の枚数（数えるカウンター）
    ok |= {float(D3["B_cap50"]["first"]), float(D3["B_cap50"]["max"]), float(D3["B"]["max"])}   # 帯の図のBの札
    ok |= {61.0, 80.0, 81.0, 100.0, 101.0, 120.0, 121.0}         # 20回ごとの柱の名前
    ok |= {float(v) for v in (D3["A"]["mean"], D3["B"]["mean"], D3["C"]["mean"], 60.0, 50.0)}
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


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))
    # ---- 台本 ----
    A(f"台本: 章は6つ（0〜5）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 6 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A(f"読みの補正 {len(READ_FIX)} 種が台本どおりの回数だけ当たり、字幕の字は台本のまま: {[(a, READ_HITS.get(a, 0), n) for a, _b, n in READ_FIX if READ_HITS.get(a, 0) != n]}",
      all(READ_HITS.get(a, 0) == n for a, _b, n in READ_FIX) and all(split_reading(tl.clip(i).text if False else fix_reading_shown(i))[0] == split_reading(LINES[i][1])[0] for i in LINES))
    A("台本: 声と字幕に〔 〕が1つも混ざらない", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()))
    A(f"題字「{QTXT}」は第0章の題名「{CH_TITLES[0]}」と同じ言葉（空白をのぞく）", QTXT.replace(" ", "") == CH_TITLES[0].replace("、", "").replace(" ", ""))
    V = lambda name, val, exp, tol: checks.append((name, float(val), float(exp), tol))
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
    n_rest = len(REST)
    A(f"区切り: 「（無音 4秒・区切り。…）」は {n_rest} か所・長さ {T_RS1 - T_RS0:.1f}秒", n_rest == 1 and abs((T_RS1 - T_RS0) - 4.0) < 0.01)
    last3 = [i for i in LINES if LINES[i][0] == 3][-1]
    A(f"区切り: 問い2（第3章）のあと・問い3（第4章）の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(last3) - 1e-6 and abs(T_RS1 - S("ch4")) < 1e-6 and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    pos = (T_RS0 + T_RS1) / 2 / DUR
    A(f"区切り: 動画の {pos:.1%} のところ（35〜75%）・声の行なし", 0.35 <= pos <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: カメは左（x {xs_[0]:.0f}）から右（x {xs_[-1]:.0f}）へ歩く・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    nums40 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and E(it.id) < 40:
            s0 = _re.sub(r"\d+年", "", split_reading(it.text)[0])
            nums40 |= set(_re.findall(r"\d+人に\d+人|\d[\d,]*", s0))
    A(f"台本: 冒頭40秒（言い終わる文）の声の数字は3個以内・年の名前は数えない（{sorted(nums40)}）", len(nums40) <= 3)
    t_res0, t_res1 = Sk("c0_10k"), Ek("c0_10k")
    t37 = Sk("c0_10k", 0.62)
    A(f"冒頭の結果の数字（37回）を言うのは約 {t37:.1f}秒（文の頭 {t_res0:.1f}秒。本番の声は30秒以内・偽の声は29.5秒以内）", t37 <= (29.5 if FAKE else 30.0))
    A(f"条件の札は 0:30 のあと（最初の札 {T_COND[0]:.1f}秒）", T_COND[0] >= 30.0)
    # ---- 声の数字 = data.json ----
    exp = [("c0_q", "51倍"), ("c3_keep", "51倍"), ("c3_t4", "4年"), ("c0_10k", f"{ihalf(D1['median'])}回"), ("c2_cont", "51.4倍"), ("c2_med", f"{ihalf(D1['median'])}回目"),
           ("c2_p90", f"{ihalf(D1['p90'])}回以上"), ("c2_80", f"100人に{ihalf(D1['over80'])}人"), ("c2_m2", f"{ihalf(D1['median'])}回目"),
           ("c2_56", f"100人に{ihalf(D1['over30'])}人"), ("c2_b3", "50人に1人"), ("c2_ans", f"{ihalf(D1['median'])}回"),
           ("c3_r1", f"{ihalf(D2['popular']['median'])}回"), ("c3_r2", f"{ihalf(D2['suburb']['median'])}回"), ("c3_l11", f"{ihalf(D2['suburb']['median'])}回目"),
           ("c3_21", f"{ihalf(D2['decline_now']['median'])}回"), ("c3_14", f"{ihalf(D2['decline_wait4y']['median'])}回"), ("c4_mean", "約51回"),
           ("c4_52", f"{D3['B']['max']}回"), ("c4_mA", f"{ihalf(D1['median'])}回"), ("c4_mBC", f"{ihalf(D3['B']['median'])}回"), ("c4_A37", f"{ihalf(D1['median'])}回"), ("c5_0", f"{ihalf(D1['median'])}回")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in split_reading(txt(k))[0]]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A(f"data.json: 1回目で当たる人 100人に{D1['first']}人（約50人に1人）・平均 {D1['mean']}回（50回あまり）・B と C の最長 {D3['B']['max']}・{D3['C']['max']}回・1回目 {D3['B']['first']}・{D3['C']['first']}",
      abs(100 / D1["first"] - 50) < 10 and 50 < D1["mean"] < 55 and D3["B"]["max"] == D3["C"]["max"] == 52 and D3["B"]["first"] == D3["C"]["first"] == 0.0)
    A(f"data.json: 声の「約5年」「約7年半」は 中央値 {D2['decline_now']['median']}回÷4＝{D2['decline_now']['median'] / 4}年・{D2['decline_wait4y_total_rounds_median']}回÷4＝{D2['decline_wait4y_total_rounds_median'] / 4}年",
      abs(D2["decline_now"]["median"] / 4 - 5) < 0.5 and abs(D2["decline_wait4y_total_rounds_median"] / 4 - 7.5) < 0.01)
    A(f"data.json: 平均はどの決まりでも約51回（A {D3['A']['mean']}・B {D3['B']['mean']}・C {D3['C']['mean']}）", all(51.0 <= D3[k]["mean"] <= 51.5 for k in "ABC"))
    # ---- 場面のデータ（模型と同じ関数・同じ種）----
    A(f"1万人の再現: 中央値 {np.median(Q1):.0f}・平均 {Q1.mean():.1f}・最長 {Q1.max()}・20回ごと {[int(((Q1 >= a) & (Q1 <= b)).sum()) for a, b in [(1, 20), (21, 40), (41, 60), (61, 80), (81, 100), (101, 120), (121, 10 ** 9)]]} が data.json と同じ",
      np.median(Q1) == D1["median"] and round(float(Q1.mean()), 1) == D1["mean"] and int(Q1.max()) == D1["max"]
      and [int(((Q1 >= a) & (Q1 <= b)).sum()) for a, b in [(1, 20), (21, 40), (41, 60), (61, 80), (81, 100), (101, 120), (121, 10 ** 9)]] == HIST20)
    A(f"人を積む分布: 1人＝100人で {HIST_N}（合計 {sum(HIST_N)}）", sum(HIST_N) == 100 and HIST_N == [32, 22, 15, 10, 7, 4, 10])
    A(f"列: 群れが1本の列に並び終わる（{_ts(q_done())}）のは、次の文（52回）の頭 {_ts(Sk('c4_52'))} より前", q_done() <= Sk("c4_52"))
    A(f"表の数字: 平均 {TB_MEAN}・中央値 {TB_MED} が data.json（Aの中央値は問い1と同じくじの値。B・C は {D3['B']['median']}・{D3['C']['median']}）", TB_MEAN == ["51.3回", "51.4回", "51.4回"] and TB_MED == ["37回", "51回", "51回"] and D3["B"]["median"] == D3["C"]["median"] == 51.0)
    A(f"地方ごとの群れの人数 {[c_.n for c_ in CITY_CROWD]} は倍率 {[r_ for _n, r_ in CITY_RATIO]} と同じ比（2倍）", [c_.n for c_ in CITY_CROWD] == [2 * r_ for _n, r_ in CITY_RATIO])
    A(f"主役の人の身長 {PH}px ＝ 画面の高さの {PH / lf.H:.0%}（3分の1 {lf.H / 3:.0f}px 以上）", PH >= lf.H / 3)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件 {[b[0] for b in bad[:4]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面の切りかえ: 文の途中で場面が替わらない（{mid_sc[:3]}）", not mid_sc)
    A(f"グラフ・人を積む分布: 棒は 1本ずつ {BAR_STEP}秒おき・柱は {min(col_start(i + 1) - col_start(i) for i in range(1, 5)):.2f}秒以上おき（0.25秒以上）",
      BAR_STEP >= 0.25 and all(col_start(i + 1) - col_start(i) >= 0.25 for i in range(6)))
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
        f0 = next(f for f in frames if abs(f[0]) < 1e-6)
        q0 = [e for e in f0[1] if e[0] == QTXT]
        A(f"冒頭: 0秒目に問い「{QTXT}」が {min((e[5] for e in q0), default=0):.0f}px（90px 以上）で出ている", len(q0) == 1 and q0[0][5] >= 90)
        A(f"冒頭: 0秒目に「昭和41年」が出ている", any(e[0] == "昭和41年" for e in f0[1]))
        A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
        tokens = [("半分の人が当たるまで 37回", "c0_10k"), ("51.4倍", "c2_cont"), ("中央値 37回目", "c2_med"), ("122回以上", "c2_p90"), ("100人に21人", "c2_80"),
                  ("平均 50回あまり", "c2_mean"), ("100人に1.7人", "c2_b3"), ("最長 520回", "c2_w2"), ("100人に15人", "c2_15"), ("100人に56人", "c2_56"),
                  ("中央値 11回", "c3_r2"), ("中央値 21回", "c3_21"), ("年4回なら 約5.2年", "c3_5y"), ("申し込んでから 中央値 14回", "c3_14"),
                  ("A 中央値 37回", "c4_A37"), ("のびた", "c4_nobi"), ("平均は同じ。運の差が消える", "c4_ans"), ("最長 B・C 52回", "c4_52"), ("B・C 中央値 51回", "c4_queue")]
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
        bad_words = sorted({e[0] for t_, e in allt if any(w in e[0] for w in ("円", "UR", "住宅公団"))})
        A(f"画面に円・実在の組織名（UR・住宅公団）を出さない: {bad_words}", not bad_words)
        dec_txt = {e[0] for t_, e in allt if SC_START["c3_dec"] + 0.3 <= t_ <= SC_START["c3_yoso"]}
        A(f"倍率が下がる場面（c3_dec）の文字は、年の名前と札だけ。棒の数字・添え書きなし: {sorted(s_ for s_ in dec_txt if not s_.startswith('字幕: '))}",
          {s_ for s_ in dec_txt if not s_.startswith("字幕: ")} <= {"昭和41年", "昭和45年", "年々減ってきている（総裁の答弁）"})
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
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat)


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
    if not any(a in args for a in ("--anchors", "--readings", "--scenecheck", "--stills", "--preview", "--docs", "--lines", "--sheet", "--voicemd", "--fixstills", "--endstills", "--end2stills")) and FAKE:
        print(__doc__)
        return
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    print(f"  37回を言う: {Sk('c0_10k', 0.62):.1f}秒（文 {Sk('c0_10k'):.1f}〜{Ek('c0_10k'):.1f}秒）・区切り {_ts(T_RS0)}〜{_ts(T_RS1)}（{(T_RS0 + T_RS1) / 2 / DUR:.1%}）")
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
    if "--end2stills" in args:
        stills_sheet(OUT / "stills_end2", end2_list(), sheet_name="stills_end2_480.png")
        return
    if "--endstills" in args:
        stills_sheet(OUT / "stills_end", end_list(), sheet_name="stills_end_480.png")
        return
    if "--fixstills" in args:
        stills_sheet(OUT / "stills_fix", fix_list(), sheet_name="stills_fix_480.png")
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
