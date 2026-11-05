"""長篠の戦い、鉄砲の三段撃ちは本当に強かった？【1万回シミュレーション】（横型ロング・チャンネル「めでたしかめ」）

このファイルは公開日まで非公開（答えが書いてある）。公開 11/9（月）19:00。
前半はモデル（数字の計算・照合・数字の書き出し）。後半（「# ここから下は場面」から）が場面（描画・音・照合・書き出し。chikyu-long.py と同じ並び）。
モデルの計算は下絵 sims/nagashino-long.draft.py と同じ（同じ種・同じ順番で乱数を引く＝出力の数字が一致する。--numbers が下絵を実際に走らせて1行ずつ突き合わせる）。

■ モデル（下絵のとおり。値は【仮定】または資料の値。動画で「〜と置きます」と言う）
  置き方   : 柵のひと区切りに、武田の1つの隊（1,000人）が攻めかかる。鉄砲は全体の5分の1がこの区切りを受け持つ。
             撃たれた駒は数から外す。測るのは「柵を越える時間が終わるまでに、隊の何割が撃たれて止められたか」（1万回の中央値）
  1回ごとの : 込め直し 18〜25秒（1発約20秒）／50m で1発が人に当たる確率 5〜15%（仮定）／走る速さ（馬 秒速4〜7m・歩き 1.5〜2.5m）／
             走り出す距離 150〜250m（仮定）／柵を越える時間（柵あり 30〜90秒・柵なし 3〜8秒・仮定）／撃ち始める距離 60〜100m
  撃ち方   : 三段（3組が順に撃つ）／めいめい（込め終わったら撃つ）／一斉（全員同時に撃ち、全員同時に込め直す）
  梯子     : 3,000丁・三段撃ち・馬・柵あり → ＋鉄砲を1,000丁に → ＋三段撃ちをやめる → ＋馬を下りて歩く ／点線で分かれて ＋柵を取ると
  章4 撃ち方の比べ・章7 参考（当たりやすさ）は梯子の本線に入れない
  入れていないもの: 弓・槍／柵から打って出ること／何度もくり返された攻め／鉄砲の不発／天気

使い方
  python -X utf8 sims/nagashino-long.py --numbers                 計算 → 下絵と突き合わせ → 照合 → out/nagashino-long/data.json・numbers.md
  python -X utf8 sims/nagashino-long.py --check                   data.json を読んで照合だけ
  python -X utf8 sims/nagashino-long.py --scenecheck --fake-voice 場面の照合（音声なし・長さは見積もり）
  python -X utf8 sims/nagashino-long.py --stills --fake-voice     要所の静止画と sheet_480.png（out/nagashino-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
  python -X utf8 sims/nagashino-long.py --wraps | --readings | --docs | --anchors --fake-voice
  python -X utf8 sims/nagashino-long.py --preview                 960×540 の確認用動画（AivisSpeech の音声）
  （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLUG = "nagashino-long"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "out" / SLUG
DRAFT = ROOT / "sims" / "nagashino-long.draft.py"

# ============================================================
# 0. 置いた値（下絵と同じ）
# ============================================================
N_RUN = 10_000
DT = 0.5
SEED = 1575


def U(rng, lo, hi):
    return rng.uniform(lo, hi, N_RUN)


def battle(seed, guns_total, mode, mounted, fence=True, W=1000, sector=1 / 5, p50_range=(0.05, 0.15)):
    """1万回の「止められた割合」（0〜1 の配列）を返す（下絵の battle と同じ順番で乱数を引く）"""
    rng = np.random.default_rng(seed)
    G = guns_total * sector                         # その区切りの鉄砲
    T = U(rng, 18, 25)                              # 込め直し 秒（1発約20秒・事実確認 2026-10-25）
    p50 = U(rng, *p50_range)                        # 50m で1発が人に当たる確率（戦場の煙・あわてを含む・仮定）
    v = U(rng, 4.0, 7.0) if mounted else U(rng, 1.5, 2.5)     # 走る速さ m/s（川・ぬかるみを含む・仮定）
    D0 = U(rng, 150, 250)                           # 走り出す位置（柵までの距離・仮定）
    T_fence = U(rng, 30, 90) if fence else U(rng, 3, 8)       # 柵を越える（壊す）時間 秒
    K = U(rng, 0.25, 0.45)                          # （下絵と同じ順に引く。使わない）
    R_open = U(rng, 60, 100)                        # 撃ち始める距離 m
    phase = U(rng, 0, 1)                            # （使わない）
    alive = np.full(N_RUN, float(W))
    t_arrive = D0 / v
    t_end = t_arrive + T_fence
    t = 0.0
    t_open = np.maximum(0, (D0 - R_open) / v)
    while True:
        if np.all(t > t_end):
            break
        r = np.clip(D0 - v * t, 5.0, None)
        in_play = (t <= t_end) & (D0 - v * t <= R_open)
        p = np.clip(p50 * np.exp(-(r - 50) / 40), 0, 0.6)
        if mode == "kakuji":
            shots = rng.poisson(np.where(in_play, G * DT / T, 0))
        else:
            k = 1 if mode == "issei" else 3
            since = t - t_open
            n_fire = np.zeros(N_RUN)
            for j in range(k):
                off = since - j * T / k
                fire = (off >= 0) & (np.floor(off / T) != np.floor((off - DT) / T))
                fire |= (off >= 0) & (off < DT)
                n_fire += np.where(fire, G / k, 0)
            shots = np.where(in_play, n_fire, 0)
        frac = 1 - np.exp(-shots * p / np.maximum(alive, 1))
        hit = rng.binomial(alive.astype(int), np.clip(frac, 0, 1))
        alive = np.maximum(alive - hit, 0)
        t += DT
    return 1 - alive / W


def stats_of(stopped):
    return dict(med=float(np.median(stopped)), p10=float(np.percentile(stopped, 10)), p90=float(np.percentile(stopped, 90)),
                quant=[round(float(v), 5) for v in np.percentile(stopped, np.arange(0, 101))])


def row_text(name, s):
    """下絵の show() が出す1行と同じ書式"""
    return f"{name:<40} 止められた割合 真ん中 {s['med']:5.1%}（1〜9割 {s['p10']:5.1%}〜{s['p90']:5.1%}）"


# (id, 下絵の行の名前, battle の引数)
CONFIGS = [
    ("A1", "鉄砲3,000・三段撃ち・騎馬で突撃・柵あり", dict(guns_total=3000, mode="sandan", mounted=True)),
    ("A2", "＋鉄砲を1,000に（信長公記）", dict(guns_total=1000, mode="sandan", mounted=True)),
    ("A3", "＋三段撃ちをやめ、各自で撃つ", dict(guns_total=1000, mode="kakuji", mounted=True)),
    ("A4", "＋馬を下りて歩いて攻める", dict(guns_total=1000, mode="kakuji", mounted=False)),
    ("B_issei", "  一斉", dict(guns_total=1000, mode="issei", mounted=True)),
    ("B_sandan", "  三段", dict(guns_total=1000, mode="sandan", mounted=True)),
    ("B_kakuji", "  各自", dict(guns_total=1000, mode="kakuji", mounted=True)),
    ("C_issei", "  一斉", dict(guns_total=1000, mode="issei", mounted=True, fence=False)),
    ("C_sandan", "  三段", dict(guns_total=1000, mode="sandan", mounted=True, fence=False)),
    ("C_kakuji", "  各自", dict(guns_total=1000, mode="kakuji", mounted=True, fence=False)),
    ("D1", "鉄砲1,000・各自・歩いて・柵あり", dict(guns_total=1000, mode="kakuji", mounted=False, p50_range=(0.7, 0.9))),
    ("D2", "鉄砲1,000・各自・歩いて・柵なし", dict(guns_total=1000, mode="kakuji", mounted=False, fence=False, p50_range=(0.7, 0.9))),
    ("E1", "鉄砲1,000・各自・歩いて・柵なし", dict(guns_total=1000, mode="kakuji", mounted=False, fence=False)),
    ("E2", "鉄砲3,000・三段・騎馬・柵なし", dict(guns_total=3000, mode="sandan", mounted=True, fence=False)),
]


def compute():
    """下絵の main() と同じ順番・同じ種で計算する（各行 seed=1575）"""
    rows = {}
    for cid, name, kw in CONFIGS:
        rows[cid] = dict(id=cid, name=name, **stats_of(battle(SEED, **kw)))
    return dict(slug=SLUG, n=N_RUN, seed=SEED, rows=rows,
                consts=dict(sector=0.2, w=1000, guns_conv=3000, guns_nobu=1000, sector_conv=600, sector_nobu=200, reload=20,
                            shots_per_min=200 * 60 / 20, fence_lo=30, fence_hi=90, d0=200, p50_hit="10発に1発"))


# ============================================================
# 1. 台本の数字を読む（モデルの照合用。場面の部分とは別に、文字だけ読む）
# ============================================================
NARR_PATH = ROOT / "publish" / SLUG / "narration_B.md"


def narration_text():
    """「## 0」より後の「- 」の行から、〔 〕と（ ）だけの行を除いた声の文を、章ごとに結ぶ"""
    txt = []
    on = False
    for raw in NARR_PATH.read_text(encoding="utf-8").splitlines():
        if re.match(r"##\s*0\s", raw):
            on = True
            continue
        if not on or not raw.startswith("- "):
            continue
        body = raw[2:].strip()
        if body.startswith("（") or body.startswith("〔"):
            continue
        body = re.sub(r"(?:〔[^〕]*〕\s*)+$", "", body).strip()
        txt.append(body)
    return "\n".join(txt)


def _int(x):
    return int(math.floor(float(x) + 0.5))


def check(res):
    """照合。名前と OK/NG の一覧を返す。1つでも NG なら止める"""
    out = []

    def A(name, ok):
        out.append((name, bool(ok)))
    R = res["rows"]
    c = res["consts"]
    pc = lambda cid: _int(R[cid]["med"] * 100)
    # ---- 下絵と1行ずつ突き合わせる ----
    cp = subprocess.run([sys.executable, "-X", "utf8", str(DRAFT)], capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    draft = [ln.rstrip() for ln in cp.stdout.splitlines()]
    A("下絵が最後まで走る（sims/nagashino-long.draft.py）", cp.returncode == 0 and len(draft) >= 20)
    data_rows = [ln for ln in draft if "止められた割合" in ln]
    A(f"下絵の数字の行は {len(CONFIGS)} 行・こちらの計算も {len(CONFIGS)} 行", len(data_rows) == len(CONFIGS) == len(R))
    for cid, name, _kw in CONFIGS:
        line = row_text(name, R[cid])
        A(f"下絵と同じ行: {line.strip()}", line in draft)
    A("下絵の行を並べた順も同じ（1行ずつ・順番まで）", [row_text(n, R[i]) for i, n, _k in CONFIGS] == data_rows)
    # ---- 台本の数字 = data.json ----
    A(f"章1 よく語られる形 {R['A1']['med']:.1%} → 台本「100人のうち、53人」", pc("A1") == 53)
    A(f"章2 鉄砲1,000丁 {R['A2']['med']:.1%} → 「18人」・3分の1ほど（{R['A2']['med'] / R['A1']['med']:.2f}）", pc("A2") == 18 and 0.30 < R["A2"]["med"] / R["A1"]["med"] < 0.38)
    A(f"章3 三段撃ちをやめる {R['A3']['med']:.1%} → 「18人」・三段撃ちのときとほとんど同じ（差 {abs(R['A3']['med'] - R['A2']['med']) * 100:.2f}ポイント）", pc("A3") == 18 and abs(R["A3"]["med"] - R["A2"]["med"]) < 0.005)
    A(f"章4 柵あり 一斉 {R['B_issei']['med']:.1%}・三段 {R['B_sandan']['med']:.1%}・めいめい {R['B_kakuji']['med']:.1%} → どれも「18人」",
      pc("B_issei") == pc("B_sandan") == pc("B_kakuji") == 18)
    A(f"章4 柵なし 一斉 {R['C_issei']['med']:.1%} →「1人か2人」（1.5%）・三段 {R['C_sandan']['med']:.1%}・めいめい {R['C_kakuji']['med']:.1%} →「4人ほど」",
      abs(R["C_issei"]["med"] * 100 - 1.5) < 0.5 and pc("C_sandan") == 4 and pc("C_kakuji") == 4)
    A(f"章4 空白のない撃ち方は一斉の2倍あまり（{R['C_kakuji']['med'] / R['C_issei']['med']:.2f}倍・{R['C_sandan']['med'] / R['C_issei']['med']:.2f}倍）",
      R["C_kakuji"]["med"] / R["C_issei"]["med"] > 2 and R["C_sandan"]["med"] / R["C_issei"]["med"] > 2)
    A(f"章5 歩いて攻める {R['A4']['med']:.1%} →「22人」・馬より少し増える（18→22）・答えを大きく変えるほどではない", pc("A4") == 22 and R["A4"]["med"] > R["A3"]["med"] and R["A4"]["med"] - R["A3"]["med"] < 0.06)
    A(f"章6 柵を取る {R['E1']['med']:.1%} →「7人」（22→7）", pc("E1") == 7 and pc("A4") == 22)
    A(f"章6 よく語られる形から柵だけ取る {R['E2']['med']:.1%} →「11人」・隊の1割ほど", pc("E2") == 11 and 0.09 < R["E2"]["med"] < 0.12)
    A(f"章7 参考 柵あり {R['D1']['med']:.1%} →「55人」・柵なし {R['D2']['med']:.1%} →「24人」・22→55・7→24・柵ありのほうが多いまま",
      pc("D1") == 55 and pc("D2") == 24 and R["D1"]["med"] > R["D2"]["med"] > R["E1"]["med"])
    A("章1 半分あまり（53人は50人より多い）・章6 柵の効き（柵ありの方が多い）・章2 鉄砲が減ると下がる", R["A1"]["med"] > 0.5 and R["A4"]["med"] > R["E1"]["med"] and R["A1"]["med"] > R["A2"]["med"])
    A("三段撃ち・めいめいは同じ（柵あり 18=18、柵なし 4=4）・一斉は柵ありで17.6（18に丸まる）", abs(R["B_sandan"]["med"] - R["B_kakuji"]["med"]) < 0.005 and abs(R["B_issei"]["med"] - R["B_kakuji"]["med"]) < 0.01)
    A("1万回の分位（0〜100%の101点）が各行にある・単調に増える", all(len(r["quant"]) == 101 and all(a <= b + 1e-12 for a, b in zip(r["quant"], r["quant"][1:])) for r in R.values()))
    A("1万回の中央値 ＝ 分位の50番目（少ない順に並べたちょうど真ん中の値）", all(abs(r["quant"][50] - r["med"]) < 0.002 for r in R.values()))
    # ---- 置いた値（章3 の計算） ----
    A(f"鉄砲1,000丁 × 5分の1 ＝ {1000 * c['sector']:.0f}丁・3,000丁 × 5分の1 ＝ {3000 * c['sector']:.0f}丁", _int(1000 * c["sector"]) == 200 and _int(3000 * c["sector"]) == 600)
    A(f"1丁は20秒に1発 → 1分3発・200丁なら1分で {c['shots_per_min']:.0f}発（台本「およそ600発」）", c["shots_per_min"] == 600 and 60 / c["reload"] == 3)
    A("込め直し 18〜25秒（下絵）の真ん中 21.5秒 ≒ 「20秒ほど」", abs((18 + 25) / 2 - c["reload"]) < 2.0)
    # ---- 台本（文字）に書いてある数字が data.json と合っている ----
    nt = narration_text()
    want = [
        f"100人のうち、{pc('A1')}人でした", f"100人のうち18人でした", "1575年", "1万回", "1,000人", "5分の1", "100人あたりに直して言います",
        "3,000丁", "600丁", "1,000丁", "200丁", "1発につき、20秒ほど", "200メートルほど", "30秒から90秒かかる", "10発に1発ほど",
        "1分では、3発", "1分でおよそ600発", "1人か2人でした", "4人ほどでした", "2倍あまり", "22人でした", "7人に減りました",
        "100人のうち11人です", "22人から55人に", "7人から24人に", "5発のうち、4発が当たりました", "100人のうち18人のまま",
        "3分の1ほどになりました", "半分あまり", "1,000丁ほど", "100人のうち7人でした",
    ]
    miss = [w for w in want if w not in nt]
    A(f"台本（narration_B.md）に、data.json から出る言葉が{len(want)}個そろっている: 足りないもの {miss}", not miss)
    A("台本: 本文に「勝率」「完全なウソ」「6月29日」「死者」を書いていない（言わない決まり）", not any(w in nt for w in ("勝率", "完全なウソ", "6月29日", "死者")))
    bad = [name for name, ok in out if not ok]
    for name, ok in out:
        print(("  OK  " if ok else "  NG  ") + name)
    if bad:
        raise SystemExit(f"照合に失敗: {len(bad)}件")
    print(f"照合 {len(out)} 件 OK")
    return out


def write_numbers(res, checks):
    R = res["rows"]
    rows = ["# 数字（長篠 ロング・sims/nagashino-long.py --numbers が書く。手で直さない）", "",
            f"{res['n']:,} 回・乱数の種 {res['seed']}（各行で同じ種）・計算は sims/nagashino-long.draft.py と同じ（出力を1行ずつ突き合わせ済み）", "",
            "## 止められた割合（柵を越える時間が終わるまでに撃たれて止められた、武田の隊1,000人の割合。1万回の少ない順の中央値・1〜9割の幅）", "",
            "| 行 | 条件 | 中央値 | 1割〜9割 | 100人あたり（声） |", "|---|---|---|---|---|"]
    voice = {"A1": "53人", "A2": "18人", "A3": "18人", "A4": "22人", "B_issei": "18人", "B_sandan": "18人", "B_kakuji": "18人", "C_issei": "1人か2人",
             "C_sandan": "4人ほど", "C_kakuji": "4人ほど", "D1": "55人", "D2": "24人", "E1": "7人", "E2": "11人"}
    for cid, name, _kw in CONFIGS:
        r = R[cid]
        rows.append(f"| {cid} | {name.strip()} | {r['med']:.1%} | {r['p10']:.1%}〜{r['p90']:.1%} | {voice[cid]} |")
    c = res["consts"]
    rows += ["", "## 置いた値", "",
             "- 柵のひと区切り: 武田の1つの隊 1,000人。鉄砲は全体の5分の1（1,000丁なら200丁・3,000丁なら600丁）",
             f"- 1分の弾数: 200丁 × 60秒 ÷ 20秒 ＝ {c['shots_per_min']:.0f}発（三段撃ちでもめいめいでも同じ）",
             "- 込め直し 18〜25秒／走り出す位置 150〜250m／撃ち始める 60〜100m／馬 秒速4〜7m・歩き 秒速1.5〜2.5m／柵を越える 30〜90秒（柵なし 3〜8秒）／50mで1発が当たる 5〜15%（参考の実験値は 70〜90%）",
             "", "## 照合", ""] + [f"- {'OK' if ok else 'NG'} {name}" for name, ok in checks]
    rows += ["", f"照合 {len(checks)} 件 OK"]
    (OUT / "numbers.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("numbers.md:", OUT / "numbers.md")


def save(res):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print("data.json:", OUT / "data.json")


def load():
    return json.loads((OUT / "data.json").read_text(encoding="utf-8"))


_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers"))
if __name__ == "__main__" and _MODEL_CLI:
    if "--numbers" in sys.argv:
        print("計算します…", flush=True)
        _res = compute()
        save(_res)
        _res = load()
    else:
        _res = load()
    _chk = check(_res)
    if "--numbers" in sys.argv:
        write_numbers(_res, _chk)
    raise SystemExit


# ==== 場面 ====

# ####################################################################################################
# ここから下は場面（描画・音・照合・書き出し。chikyu-long.py と同じ並び・同じ部品: 見開きノート・付せん・章カード・終了画面・照合）。
# 台本: publish/nagashino-long/narration_B.md の「## 0」より後の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 人は駒（人型）で描く。撃たれた駒は「消える」（血・倒れる絵は描かない）。
# 部品: engine/longkit.py（LadderPanel を縦積みにした StackLadder・OpeningTeaser・scan_frames・text_box_overlaps・visual_lag・value_spoilers・min_text_size・small）。
#
# 使い方
#   python -X utf8 sims/nagashino-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/nagashino-long.py --stills --fake-voice        要所の静止画と sheet_480.png（out/nagashino-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
#   python -X utf8 sims/nagashino-long.py --wraps | --readings | --docs | --anchors --fake-voice
#   python -X utf8 sims/nagashino-long.py --preview                    960×540 の確認用動画（AivisSpeech の音声）
#   （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
# ####################################################################################################
import re as _re
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine import longkit as lk
from engine.core import (beat, bell, blip, check_answers, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh)
from engine.note import INK, MARKER, PAPER, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

FAKE = "--fake-voice" in sys.argv
VOICE_DIR = OUT / "voice"
WORK = OUT / "scene_work"


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本の読み込み（narration_B.md の「## 0」より後の「- 」の行。文言は一字も変えない）
#   「- （無音 3秒・…）」＝声のない区間（Gap） ／ 「- （…）」「- 〔…〕」だけの行＝画面の指示（声にしない）
#   行の終わりの〔…〕＝その文のときの画面の絵（声にしない）
# ============================================================
GAP_FAST = 3.0                                   # 「（無音・早回し。…）」に秒数が書いていないときの長さ（4秒以内）


def parse_narration(path=NARR_PATH):
    chaps, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _re.match(r"##\s*(\d+)\s+(.+)$", raw)
        if m:
            cur = dict(n=int(m.group(1)), title=m.group(2).strip(), items=[])
            chaps.append(cur)
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
            mn = _re.search(r"(?:〔[^〕]*〕\s*)+$", body)           # 行の終わりの〔…〕は2つ以上並ぶこともある（全部、声にしない）
            txt = (body[:mn.start()] if mn else body).strip()
            notes = _re.findall(r"〔([^〕]*)〕", mn.group(0)) if mn else []
            cur["items"].append(("line", txt, "／".join(notes)))
    return chaps


CHAPS = parse_narration()
CH_TITLES = [c["title"] for c in CHAPS]
CARD_BREAK = {"全員で一斉に撃ったら？": "全員で一斉に\n撃ったら？", "当たりやすさが実験どおりなら？": "当たりやすさが\n実験どおりなら？"}   # 長い題は2行に（左ページの幅に収める。表示だけで台本は変えない）
CARD_TITLES = [CARD_BREAK.get(t_, t_).replace("　", "\n") for t_ in CH_TITLES]       # 章カードに出す題（全角空白で2行に）
LINES = {}                         # 文の id -> (章, 文)
LINE_NOTE = {}                     # 文の id -> 〔画面の絵〕
GAP_NOTE = {}                      # 無音の id -> 注
GAP_SEC = {}
CH_NOTE0 = {}                      # 章の最初の画面指示（（…）〔…〕のみの行）
SPEED_V = 1.0

SUB_MAX2 = 2 * lf.SUB_MAX                      # 字幕は2行まで（1行 28字）


def split_long(txt):
    """2行（56字）に収まらない文だけ、「。」の切れ目で分ける（文言は変えない）"""
    if len(txt) <= SUB_MAX2:
        return [txt]
    sents = [x + "。" for x in txt.split("。") if x]
    out, cur = [], ""
    for x in sents:
        if cur and len(cur) + len(x) > SUB_MAX2:
            out.append(cur)
            cur = x
        else:
            cur += x
    if cur:
        out.append(cur)
    res = []
    for p in out:                                  # それでも2行に収まらない1文だけ、真ん中に近い「、」で分ける（文言は変えない）
        if len(p) <= SUB_MAX2:
            res.append(p)
            continue
        cuts = [i + 1 for i, ch in enumerate(p) if ch == "、"]
        k = min(cuts, key=lambda i: abs(i - len(p) / 2))
        res += [p[:k], p[k:]]
    return res


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
                for j, part in enumerate(parts):          # 字幕が2行に収まらない文は、文言を変えずに「。」で2つの Line に分ける
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and j == len(parts) - 1
                    out.append(lf.Line(lid, part, pause=0.3 if n == 0 else (0.6 if last else 0.35), speed=SPEED_V))      # 0章は、どの文のあとも約0.3秒
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


VOICE_PAUSES = (0.10, 0.22)
NUM_BREATH = 0.35                                    # 数字を言った文のあとは +0.35秒
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
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# ============================================================
# 小さな道具（inoh-long・okehazama-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"
GREEN = "#3f9a6a"
ORANGE = "#e0892a"


def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


def window(t, t0, t1, fi=0.3, fo=0.3):
    """t0〜t1 の間だけ 1（出入りのフェード付き）"""
    return fade(t, t0, fi) * (1 - clamp01((t - t1) / fo))


def prog(t, t0, s, cps=9.0):
    return clamp01((t - t0) / lf.write_dur(s, cps))


def wr(ctx, s, x, y, size, color, t0, t, cps=9.0, align="left", alpha=1.0, bold=True):
    if alpha <= 0.003 or t < t0:
        return
    lf.write_on(ctx, s, x, y, size, color, prog(t, t0, s, cps), align=align, alpha=alpha, bold=bold)


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


def tag(ctx, s, x, y, size, col, a=1.0, progress=1.0, align="center"):
    """白い下地つきの札。align='left' なら x は左端"""
    if a <= 0.003 or progress <= 0:
        return 0
    w = text_width(s, size) + 26
    cx = x + w / 2 - 13 if align == "left" else x
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, cx - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, cx, y, size, col, progress, align="center", alpha=a)
    return w


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """余白の小さい付箋。(x, y) は中心（align='left' なら左端）。戻り値は (幅, 高さ)"""
    if a <= 0.003:
        return 0, 0
    lines = s.split("\n")
    w = max(text_width(l, size) for l in lines) + 44
    h = size * 1.25 * len(lines) + 24
    cx = x + w / 2 if align == "left" else x
    bg = STICKY.get(color, color)
    ctx.save()
    ctx.translate(cx, y)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, -w / 2 + 5, -h / 2 + 7, w, h, 5)
    ctx.fill()
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, -w / 2, -h / 2, w, h, 5)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(-w / 2, -h / 2, w, 10)
    ctx.fill()
    text(ctx, s, 0, 3, size, fg, alpha=a)
    ctx.restore()
    return w, h


def nolog(fn, *args, **kw):
    """飾りの字（重なりの検査に入れない）"""
    saved = core._LOG
    core._LOG = None
    try:
        return fn(*args, **kw)
    finally:
        core._LOG = saved


# ============================================================
# 準備（データ・時間割）
# ============================================================
lf.use()
RES = load()
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)




# ---- 場面の合図: 文の一部（手がかり）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    # 0 冒頭
    "c0_q": (0, "本当に強かったのでしょうか"), "c0_1575": (0, "1575年"), "c0_oda": (0, "織田と徳川の鉄砲隊が"), "c0_said": (0, "そう語られてきました"),
    "c0_doubt": (0, "疑われています"), "c0_10k": (0, "1万回くり返します"), "c0_first": (0, "先に言うと"), "c0_what": (0, "では、何が決めたのか"),
    "c0_cond": (0, "条件をそろえます"), "c0_where": (0, "戦いの場所は"), "c0_river": (0, "小さな川をはさんで"), "c0_fence": (0, "を築きました"),
    "c0_sanju": (0, "柵は3本並んで"), "c0_seg": (0, "ひと区切りだけを見ます"), "c0_1000": (0, "1,000人と置きます"),
    "c0_fifth": (0, "5分の1と置きます"), "c0_measure": (0, "測るのは、止められた人数"), "c0_notblock": (0, "柵が通せんぼする"), "c0_shot": (0, "撃たれて、戦えなくなる"),
    "c0_per100": (0, "100人あたりに直して"), "c0_luck": (0, "運なので"), "c0_mid": (0, "ちょうど真ん中の"),
    "c0_eff": (0, "効いていたのは"), "c0_next": (0, "その中身を"),
    # 1 よく語られる長篠
    "c1_four": (1, "4つの特徴"), "c1_g1": (1, "1つ目"), "c1_600": (1, "受け持つのは、5分の1"), "c1_hoan": (1, "3,000丁という数は"),
    "c1_shin": (1, "という読み物に出てきます"), "c1_g2": (1, "2つ目"), "c1_3sets": (1, "3つの組に分けます"), "c1_swap": (1, "後ろに下がって"),
    "c1_komi": (1, "込め直しとは"), "c1_20": (1, "20秒ほどです"), "c1_g3": (1, "3つ目"), "c1_allhorse": (1, "全員が馬に乗っている"),
    "c1_g4": (1, "4つ目"), "c1_200": (1, "200メートルほど手前"), "c1_fence30": (1, "30秒から90秒"),
    "c1_p50": (1, "10発に1発ほど"), "c1_smoke": (1, "煙が出て"), "c1_ans": (1, "53人でした"), "c1_strong": (1, "強そうです"),
    "c1_end": (1, "分かったことです"),
    # 2 鉄砲1,000丁
    "c2_prev": (2, "前の章では"), "c2_ushi": (2, "信長に仕えた"), "c2_1000": (2, "1,000丁ほどとあります"), "c2_hoan": (2, "のほうに出てきます"),
    "c2_undec": (2, "決着していません"), "c2_use": (2, "の記録の数を使います"), "c2_200": (2, "このひと区切りは、200丁"), "c2_add": (2, "鉄砲を1,000丁に減らすと"),
    "c2_ans": (2, "18人でした"), "c2_third": (2, "3分の1になると"), "c2_end": (2, "分かったことです"),
    # 3 三段撃ちをやめたら
    "c3_prev": (3, "前の章では"), "c3_add": (3, "三段撃ちをやめる、を足します"), "c3_nosup": (3, "今は支持されていません"), "c3_unk": (3, "まだ決まっていません"),
    "c3_either": (3, "結果が変わるかを見ます"), "c3_meimei": (3, "めいめい撃ちと呼びます"), "c3_q": (3, "増えるでしょうか"), "c3_ans": (3, "三段撃ちのときと"),
    "c3_why": (3, "なぜ、変わらないのか"), "c3_200": (3, "200丁でした"), "c3_3shots": (3, "1分では、3発"), "c3_600": (3, "およそ600発"), "c3_same": (3, "この数は同じです"),
    "c3_end": (3, "分かったことです"),
    # 4 全員で一斉に
    "c4_prev": (4, "前の章では"), "c4_cmp": (4, "足し算ではなく"), "c4_issei": (4, "もう1つ、一斉撃ちを見ます"), "c4_empty": (4, "からっぽです"),
    "c4_idea": (4, "なくす工夫です"), "c4_fence": (4, "まず、柵がある場合です"), "c4_ans1": (4, "三段撃ちでも、めいめい撃ちでも"), "c4_30": (4, "30秒以上"),
    "c4_nofence": (4, "次に、柵がない場合です"), "c4_run": (4, "一気に走り抜けます"), "c4_issei2": (4, "1人か2人でした"), "c4_4": (4, "4人ほどでした"),
    "c4_x2": (4, "2倍あまり"), "c4_end": (4, "分かったことです"),
    # 5 馬を下りて
    "c5_prev": (5, "前の章では"), "c5_add": (5, "歩いて攻める、を足します"), "c5_rec": (5, "柵まで攻めかかった"), "c5_doubt": (5, "疑われています"), "c5_habit": (5, "戦う習慣"),
    "c5_all": (5, "全員が歩いて攻めた場合"), "c5_ans": (5, "22人でした"), "c5_slow": (5, "歩くほうが遅い"), "c5_end": (5, "分かったことです"),
    # 6 柵がなかったら
    "c6_prev": (6, "前の章では"), "c6_take": (6, "柵を取ります"), "c6_sec": (6, "数秒しか"), "c6_q": (6, "どれくらい減るでしょう"), "c6_ans": (6, "7人でした"),
    "c6_22to7": (6, "22人が、7人に減りました"), "c6_long": (6, "ずっと撃たれる"), "c6_other": (6, "もう1つ、見ます"), "c6_11": (6, "100人のうち11人です"),
    "c6_expert": (6, "決め手は柵だった"), "c6_caveat": (6, "この動画で置いた値"), "c6_end": (6, "分かったことです"),
    # 7 参考
    "c7_prev": (7, "前の章では"), "c7_ref": (7, "参考です"), "c7_exp": (7, "火縄銃を撃った実験"), "c7_4of5": (7, "5発のうち、4発"), "c7_calm": (7, "落ち着いて"),
    "c7_redo": (7, "計算し直します"), "c7_cond": (7, "さっき22人だったとき"), 
    "c7_arrow": (7, "22人から55人に"), "c7_still": (7, "それでも"), "c7_end": (7, "分かったことです"),
    # 8 まとめ
    "c8_0": (8, "三段撃ちをやめても"), "c8_1": (8, "特別に強かったわけではなく"), "c8_2": (8, "どう攻めますか"), "c8_note": (8, "数字は、この動画で置いた条件"),
    "c8_ch": (8, "このチャンネルでは"), "c8_sub": (8, "よければ"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


# ---- データ ----
R = RES["rows"]


def pcv(cid):
    return ihalf(R[cid]["med"] * 100)


CNT = {k: pcv(k) for k in R}                     # 100人あたりの人数（四捨五入）
FR = {k: R[k]["med"] for k in R}                 # 割合
VMAX = 0.6                                       # 棒の枠いっぱいの割合（どの棒も同じ尺度）


# ============================================================
# 駒・馬・柵・鉄砲の絵（人は駒で描く。撃たれた駒は「消える」。血・倒れる絵は描かない）
# ============================================================
OD_F, OD_L = "#a9c8f2", "#3a73c8"            # 織田・徳川（青）
TK_F, TK_L = "#f6b0a8", "#d8434e"            # 武田（赤）
HORSE_F = "#dcc194"
FENCE_C = "#8a5a2b"
GROUND_C = "#e4eed7"
GUN_C = "#3b3b45"
FX = 360                                     # 柵の x（左ページの図）
GUN_X = [FX - 60, FX - 135, FX - 210]        # 鉄砲の列（前列 → 後列）


def clip_left(ctx):
    ctx.rectangle(45, 36, 890, 900)
    ctx.clip()


def label(ctx, s, x, y, size, col=INK, a=1.0, align="center", bg=True):
    """白い下地つきの文字ラベル（図の上に置く）"""
    if a <= 0.003:
        return
    if bg:
        w = max(text_width(l_, size) for l_ in s.split("\n")) + 22
        h = size * 1.3 * len(s.split("\n"))
        x0 = x - w / 2 if align == "center" else (x - w + 11 if align == "right" else x - 11)
        ctx.set_source_rgba(1, 1, 1, 0.78 * a)
        rrect(ctx, x0, y - h / 2, w, h, 10)
        ctx.fill()
    text(ctx, s, x, y, size, col, align=align, alpha=a)


def line2(ctx, p, q, col, w, a=1.0, dash=None, cap=cairo.LINE_CAP_ROUND):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_dash(dash or [])
    ctx.move_to(*p)
    ctx.line_to(*q)
    ctx.stroke()
    ctx.set_dash([])


def arrowhead(ctx, tip, d, col, size=22.0, a=1.0, w=5.0):
    ang = math.atan2(d[1], d[0])
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for s_ in (-1, 1):
        ctx.move_to(tip[0] - size * math.cos(ang + s_ * 0.45), tip[1] - size * math.sin(ang + s_ * 0.45))
        ctx.line_to(*tip)
    ctx.stroke()


def arrow2(ctx, p, q, col, w=6.0, a=1.0, both=False, head=22.0):
    line2(ctx, p, q, col, w, a)
    d = (q[0] - p[0], q[1] - p[1])
    n = math.hypot(*d) or 1.0
    d = (d[0] / n, d[1] / n)
    arrowhead(ctx, q, d, col, head, a, w)
    if both:
        arrowhead(ctx, p, (-d[0], -d[1]), col, head, a, w)


def koma(ctx, x, y, s=1.0, team="T", a=1.0, face=1, gun=False, flag=False):
    """駒（人型）。(x, y) は足元の中心。高さは約 56*s。face=+1 は右向き（鉄砲は右へ向ける）"""
    if a <= 0.003:
        return
    fc, lc = (OD_F, OD_L) if team == "O" else (TK_F, TK_L)
    lw = max(1.5, 2.3 * s)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(1, 0.28)
    ctx.arc(0, 0, 17 * s, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.2, 0.17, 0.1, 0.16 * a)
    ctx.fill()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if flag:                                                     # 背に旗（向きと反対側へなびく）
        px = x - face * 11 * s
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(max(1.6, 2.2 * s))
        ctx.move_to(px, y - 30 * s)
        ctx.line_to(px, y - 100 * s)
        ctx.stroke()
        ctx.move_to(px, y - 98 * s)
        ctx.line_to(px - face * 30 * s, y - 91 * s)
        ctx.line_to(px, y - 80 * s)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(lc, 0.95 * a))
        ctx.fill()
    ctx.move_to(x - 15 * s, y)
    ctx.line_to(x + 15 * s, y)
    ctx.line_to(x + 8 * s, y - 34 * s)
    ctx.line_to(x - 8 * s, y - 34 * s)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(fc, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(lw)
    ctx.stroke()
    ctx.arc(x, y - 45 * s, 10.5 * s, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#fff0d8", a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.stroke()
    ctx.move_to(x - 11 * s, y - 49 * s)                           # 笠（頭の上の三角）
    ctx.line_to(x + 11 * s, y - 49 * s)
    ctx.line_to(x, y - 63 * s)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(lc, 0.9 * a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(lw * 0.8)
    ctx.stroke()
    if gun:
        ctx.set_source_rgba(*hexrgb(INK, 0.95 * a))
        ctx.set_line_width(5.6 * s + 1.5)
        ctx.move_to(x + face * 3 * s, y - 22 * s)
        ctx.line_to(x + face * 42 * s, y - 30 * s)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(GUN_C, a))
        ctx.set_line_width(3.8 * s + 0.6)
        ctx.move_to(x + face * 3 * s, y - 22 * s)
        ctx.line_to(x + face * 42 * s, y - 30 * s)
        ctx.stroke()


def horse(ctx, x, y, s=1.0, a=1.0, face=-1, ph=0.0, rider=True):
    """馬と乗り手の駒（足元の中心が (x, y)）。face=-1 は左向き（頭が左）、face=+1 は右向き。ph は脚のふり（0〜1 で1周）
    2026-10-25: 向きが逆だった（face=-1 で右向きに描いていた）→ scale を face * s に直した。武田の騎馬は face=-1＝左の柵・鉄砲隊のほうへ走る"""
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(face * s, s)                                        # 以下は「右向き」で描く（face=-1 → 左向きに反転）
    ink = hexrgb(INK, 0.9 * a)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for lx, sg in ((-20, 0.0), (-12, 0.5), (16, 0.25), (24, 0.75)):         # 脚
        sw = math.sin((ph + sg) * 2 * math.pi) * 9
        ctx.set_source_rgba(*ink)
        ctx.set_line_width(8.5)
        ctx.move_to(lx, -22)
        ctx.line_to(lx + sw, 0)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(HORSE_F, a))
        ctx.set_line_width(5.2)
        ctx.move_to(lx, -22)
        ctx.line_to(lx + sw, 0)
        ctx.stroke()
    ctx.save()                                                    # 胴
    ctx.translate(0, -30)
    ctx.scale(36, 15)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(HORSE_F, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(2.2)
    ctx.stroke()
    ctx.move_to(26, -38)                                          # 首と頭
    ctx.line_to(46, -64)
    ctx.line_to(66, -56)
    ctx.line_to(62, -46)
    ctx.line_to(46, -48)
    ctx.line_to(30, -22)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(HORSE_F, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(2.2)
    ctx.stroke()
    ctx.move_to(-34, -36)                                         # しっぽ
    ctx.curve_to(-52, -34, -54, -18, -48, -8)
    ctx.set_line_width(4.0)
    ctx.stroke()
    ctx.restore()
    if rider:
        koma(ctx, x, y - 36 * s, s * 0.82, "T", a, face=face)


def flash(ctx, x, y, u, s=1.0):
    """発砲の光と煙。u は撃ってからの 0〜1（0.6秒）"""
    if u < 0 or u >= 1:
        return
    r = (10 + 20 * u) * s
    ctx.set_source_rgba(0.62, 0.62, 0.66, 0.40 * (1 - u))
    ctx.arc(x + 10 * s * u, y - 6 * s * u, (12 + 24 * u) * s, 0, 2 * math.pi)
    ctx.fill()
    if u < 0.55:
        k = 1 - u / 0.55
        ctx.set_source_rgba(*hexrgb("#ffb21c", 0.95 * k))
        for i in range(8):
            ang = i * math.pi / 4 + 0.3
            rr = r if i % 2 == 0 else r * 0.45
            ctx.line_to(x + rr * math.cos(ang), y + rr * math.sin(ang))
        ctx.close_path()
        ctx.fill()


def poof(ctx, x, y, u, s=1.0):
    """駒が消えるときの輪（u は 0〜1）"""
    if u <= 0 or u >= 1:
        return
    ctx.set_source_rgba(*hexrgb(TK_L, 0.75 * (1 - u)))
    ctx.set_line_width(3.2)
    ctx.arc(x, y - 28 * s, (10 + 26 * u) * s, 0, 2 * math.pi)
    ctx.stroke()


def fence_v(ctx, x, y0, y1, a=1.0, prog=1.0, rows=3, dx=17, gap=44):
    """柵（上から見た図。縦に3本）。prog で上から伸びる"""
    if a <= 0.003 or prog <= 0:
        return
    ye = y0 + (y1 - y0) * prog
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for col, w, al in ((INK, 11, 0.85), (FENCE_C, 7, 1.0)):
        ctx.set_source_rgba(*hexrgb(col, al * a))
        ctx.set_line_width(w)
        for k in range(rows):
            xx = x + (k - (rows - 1) / 2) * dx
            ctx.move_to(xx, y0)
            ctx.line_to(xx, ye)
        ctx.stroke()
    n = int((ye - y0) / gap)
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
    ctx.set_line_width(4)
    for i in range(n + 1):
        yy = y0 + i * gap
        ctx.move_to(x - (rows - 1) / 2 * dx - 4, yy)
        ctx.line_to(x + (rows - 1) / 2 * dx + 4, yy)
    ctx.stroke()


def gun_icon(ctx, x, y, size=44, col=OD_L, a=1.0):
    """鉄砲1丁の印（横向きの細い棒＋台）。(x, y) は中心"""
    if a <= 0.003:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(size * 0.20)
    ctx.move_to(x - size * 0.5, y + size * 0.12)
    ctx.line_to(x + size * 0.5, y - size * 0.12)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(size * 0.11)
    ctx.move_to(x - size * 0.5, y + size * 0.12)
    ctx.line_to(x + size * 0.5, y - size * 0.12)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(size * 0.17)
    ctx.move_to(x - size * 0.5, y + size * 0.12)
    ctx.line_to(x - size * 0.34, y + size * 0.30)
    ctx.stroke()


def ground(ctx, a=1.0, box=(72, 112, 912, 884)):
    """野の下地（うすい緑）と草の印"""
    if a <= 0.003:
        return
    x0, y0, x1, y1 = box
    ctx.set_source_rgba(*hexrgb(GROUND_C, 0.80 * a))
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 34)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#6b8f6b", 0.55 * a))
    ctx.set_line_width(2.6)
    rng = np.random.default_rng(5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(26):
        gx, gy = rng.uniform(x0 + 30, x1 - 30), rng.uniform(y0 + 30, y1 - 30)
        for dx in (-5, 0, 5):
            ctx.move_to(gx + dx, gy)
            ctx.line_to(gx + dx * 1.6, gy - 11)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#6b8f6b", 0.75 * a))
    ctx.set_line_width(4)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 34)
    ctx.stroke()


# ---- 冒頭の戦いの動き（0秒目から動き続ける。6秒で1周） ----
WAVE_P = 6.0
WAVE_T0 = 1.0                                                       # 0秒目は1周の1秒目（もう駒が近づいていて、すぐ最初の一斉が来る）
WAVE_COLS, WAVE_ROWS = 6, 6
WAVE_YS = [250 + 100 * r for r in range(WAVE_ROWS)]
VOLLEYS = [(1.4, 0), (2.3, 1), (3.2, 2), (4.1, 0), (5.0, 1)]       # (周の中の時刻, 撃つ列) 前列 → 中 → 後 → 前 → 中
VOLLEY_PER = 4                                                      # 1回の一斉で消える駒


def wave_xfront(tau):
    return 860 - 62 * tau


def _wave_plan():
    rng = np.random.default_rng(11)
    dead, death = set(), {}
    for tau, col in VOLLEYS:
        cand = [(c, r) for c in range(WAVE_COLS) for r in range(WAVE_ROWS) if (c, r) not in dead and wave_xfront(tau) + c * 38 <= 915]
        cand.sort(key=lambda cr: (cr[0], rng.random()))
        for p in cand[:VOLLEY_PER]:
            death[p] = tau + 0.32
            dead.add(p)
    jit = rng.uniform(0, 0.12, (len(VOLLEYS), WAVE_ROWS))
    return death, jit


WAVE_DEATH, WAVE_JIT = _wave_plan()
WAVE_TOTAL = WAVE_COLS * WAVE_ROWS


def wave_killed_frac(t):
    tau = (t + WAVE_T0) % WAVE_P
    return sum(1 for d in WAVE_DEATH.values() if d <= tau) / WAVE_TOTAL


def L_wave(ctx, t, labels=True, a_labels=1.0):
    """柵の内側の3列の鉄砲隊が順に撃ち、近づく武田の駒が消える（6秒で1周）"""
    tau = (t + WAVE_T0) % WAVE_P
    ground(ctx)
    fence_v(ctx, FX, 168, 836)
    for ci in (2, 1, 0):
        for ri, gy in enumerate(WAVE_YS):
            koma(ctx, GUN_X[ci], gy + 18, 0.86, "O", 1.0, face=1, gun=True)
    for k, (vt, col) in enumerate(VOLLEYS):
        for ri, gy in enumerate(WAVE_YS):
            u = (tau - vt - WAVE_JIT[k][ri]) / 0.6
            flash(ctx, GUN_X[col] + 40 * 0.86, gy + 18 - 30 * 0.86, u, 1.0)
    fade_in = clamp01(tau / 0.3) if tau < 0.3 else 1.0
    fade_out = clamp01((WAVE_P - tau) / 0.4)
    items = []
    for c in range(WAVE_COLS):
        for r in range(WAVE_ROWS):
            items.append((WAVE_YS[r] + 14 * ((c + r) % 2), c, r))
    items.sort()
    for yy, c, r in items:
        x = wave_xfront(tau) + c * 38
        if x > 960:
            continue
        d = WAVE_DEATH.get((c, r))
        al = fade_in * fade_out
        sc = 0.86
        if d is not None and tau >= d:
            u = (tau - d) / 0.35
            if u >= 1:
                continue
            poof(ctx, x, yy + 18, u, 0.9)
            al *= (1 - u)
            sc *= (1 - 0.25 * u)
        koma(ctx, x, yy + 18, sc, "T", al, face=-1, flag=(c == WAVE_COLS - 1 and r % 2 == 0))
    if labels and a_labels > 0.003:
        label(ctx, "織田・徳川", 190, 150, 44, OD_L, a_labels)
        label(ctx, "武田", 740, 150, 44, TK_L, a_labels)
        label(ctx, "柵", FX, 150, 44, FENCE_C, a_labels)


# ============================================================
# 100人あたりの駒の絵（駒が消える）・早回しの1,000駒
# ============================================================
class HGrid:
    """武田の駒 100体（10×10）。止められた人数ぶんだけ、順に消える（n は小数も可。0.5 は半分薄くなる）。
    caption（上）は frame（声より前に出す）・count（下の人数）は value（声に合わせる）。消えたあとは小さな点が残る"""

    def __init__(self, n, cx, y0, sp_x, sp_y, s, t0, t1, seed=1, cap=None, t_cap=0.0, cap_y=120.0, cap_size=52, cnt=None, t_cnt=None, cnt_y=840.0,
                 cnt_size=64, line_cap=None, line_cnt=None, cnt_col=RED, cap_col=INK, preset=False, team="T"):
        self.n, self.cx, self.y0, self.sp_x, self.sp_y, self.s = float(n), cx, y0, sp_x, sp_y, s
        self.t0, self.t1, self.cap, self.t_cap, self.cap_y, self.cap_size = t0, t1, cap, t_cap, cap_y, cap_size
        self.cnt, self.t_cnt, self.cnt_y, self.cnt_size = cnt, (t1 if t_cnt is None else t_cnt), cnt_y, cnt_size
        self.line_cap, self.line_cnt, self.cnt_col, self.cap_col, self.preset, self.team = line_cap, line_cnt, cnt_col, cap_col, preset, team
        self.rank = np.random.default_rng(seed).permutation(100)       # 各マスが何番目に消えるか
        self.x0 = cx - 9 * sp_x / 2
        self.m = int(math.ceil(self.n)) or 1

    def pos(self, k):
        return self.x0 + (k % 10) * self.sp_x, self.y0 + (k // 10) * self.sp_y

    def vanish_time(self, rank):
        return self.t0 + (self.t1 - self.t0) * (rank + 1) / self.m

    def draw(self, ctx, t, a=1.0):
        ac = a * fade(t, self.t_cap, 0.4)
        if ac <= 0.003:
            return
        if self.cap:
            text(ctx, self.cap, self.cx, self.cap_y, self.cap_size, self.cap_col, alpha=ac)
        for k in range(100):
            x, y = self.pos(k)
            rk = int(self.rank[k])
            tv = -1e9 if self.preset else self.vanish_time(rk)
            full_gone = (rk + 1) <= self.n + 1e-9
            half = (not full_gone) and (rk < self.n - 1e-9)
            if full_gone:
                if t >= tv:
                    ctx.set_source_rgba(*hexrgb(PENCIL, 0.28 * ac))
                    ctx.arc(x, y - 22 * self.s, max(2.2, 3.4 * self.s), 0, 2 * math.pi)
                    ctx.fill()
                    if 0 <= t - tv < 0.35:
                        poof(ctx, x, y, (t - tv) / 0.35, self.s * 1.1)
                    continue
                koma(ctx, x, y, self.s, self.team, ac * (1 - clamp01((t - (tv - 0.2)) / 0.2)), face=-1)
            elif half:
                koma(ctx, x, y, self.s, self.team, ac * (1 - (self.n - rk) * clamp01((t - (tv - 0.2)) / 0.2)), face=-1)
            else:
                koma(ctx, x, y, self.s, self.team, ac, face=-1)
        if self.cnt and t >= self.t_cnt - 0.0:
            q = a * fade(t, self.t_cnt, 0.4)
            text(ctx, self.cnt, self.cx, self.cnt_y, self.cnt_size, self.cnt_col, alpha=q)

    def cues(self):
        out = []
        if self.line_cap:
            out.append(lk.Cue(f"駒の絵 見出し「{self.cap}」", "frame", self.t_cap, self.t_cap + 0.4, self.line_cap))
        if self.line_cnt and self.cnt:
            out.append(lk.Cue(f"駒の絵 人数「{self.cnt}」", "value", self.t_cnt, self.t_cnt + 0.4, self.line_cnt))
        return out


def mini_tk(ctx, x, y, s=1.0):
    """1,000駒用の小さな駒（路だけ。まとめて塗る）"""
    ctx.move_to(x - 4.8 * s, y)
    ctx.line_to(x + 4.8 * s, y)
    ctx.line_to(x, y - 12 * s)
    ctx.close_path()
    ctx.new_sub_path()
    ctx.arc(x, y - 15 * s, 3.4 * s, 0, 2 * math.pi)


class FastForward:
    """早回し: 武田の隊 1,000駒が、前（柵に近いほう）から順に消えていき、「N回」の数が増えていく"""

    def __init__(self, frac, seed, t0, t1, label="武田の隊 1,000人"):
        rng = np.random.default_rng(seed)
        self.cols, self.rows = 40, 25
        self.frac, self.t0, self.t1, self.label = frac, t0, t1, label
        cx = [(c, r) for c in range(self.cols) for r in range(self.rows)]
        key = [c + rng.uniform(-9, 9) for c, r in cx]
        self.order = [cx[i] for i in np.argsort(key)]                   # 前（左）から消える
        self.rank = {p: i for i, p in enumerate(self.order)}

    def n_gone(self, t):
        u = clamp01((t - self.t0) / max(self.t1 - self.t0, 1e-6))
        return int(round(1000 * self.frac * ease_in_out(u)))

    def draw(self, ctx, t, a=1.0):
        ground(ctx, a)
        fence_v(ctx, 108, 178, 722, a)
        ng = self.n_gone(t)
        ctx.set_source_rgba(*hexrgb(TK_L, 0.92 * a))
        for (c, r), rk in self.rank.items():
            if rk < ng:
                continue
            mini_tk(ctx, 150 + c * 18, 232 + r * 19)
        ctx.fill()
        label(ctx, self.label, 492, 852, 44, TK_L, a)
        u = clamp01((t - self.t0) / max(self.t1 - self.t0, 1e-6))
        cnt = int(round(10000 * u / 100.0) * 100)
        label(ctx, f"{cnt:,}回", 492, 765, 72, INK, a)


# ============================================================
# 絵: 鉄砲の数（1つ＝100丁）・本・距離・時計・10発・実験
# ============================================================
def L_guncount(ctx, t, total, hl, title, t_title, t_hl, hl_label, t_hl_label, cols=10, y_rows=(350, 470, 590), sub="1つ ＝ 100丁"):
    """鉄砲の印（1つ＝100丁）を並べ、このひと区切りが受け持つぶん（5分の1）を青く"""
    ground(ctx)
    a_t = fade(t, t_title, 0.4)
    text(ctx, title, 492, 185, 64, INK, alpha=a_t)
    if total <= 10:
        y_rows = (470,)
    sp = 76
    for i in range(total):
        r, c = divmod(i, cols)
        x = 130 + c * sp
        y = y_rows[r]
        hlon = i < hl
        a_hl = fade(t, t_hl, 0.4) if hlon else 0.0
        gun_icon(ctx, x, y, 66, OD_L if (hlon and a_hl > 0.5) else "#9aa3b5", a_t)
    a_h = fade(t, t_hl, 0.4)
    if a_h > 0.003:
        n_hl_r = (hl + cols - 1) // cols
        ctx.set_source_rgba(*hexrgb(OD_L, 0.9 * a_h))
        ctx.set_line_width(5)
        ctx.set_dash([12, 9])
        w = min(hl, cols) * sp - 8
        rrect(ctx, 130 - 40, y_rows[0] - 52, w, 104 + (n_hl_r - 1) * 120, 14)
        ctx.stroke()
        ctx.set_dash([])
    label(ctx, sub, 492, (y_rows[-1] + 105), 44, PENCIL_T, a_t)
    label(ctx, hl_label, 492, (y_rows[-1] + 200), 56, OD_L, fade(t, t_hl_label, 0.4))


def L_book(ctx, x, y, w, h, title, a=1.0, col="#f3e2a8"):
    if a <= 0.003:
        return
    ctx.set_source_rgba(0.2, 0.17, 0.1, 0.16 * a)
    rrect(ctx, x - w / 2 + 6, y - h / 2 + 8, w, h, 10)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(col, a))
    rrect(ctx, x - w / 2, y - h / 2, w, h, 10)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(FENCE_C, 0.8 * a))
    ctx.rectangle(x - w / 2, y - h / 2, 30, h)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(3)
    ctx.move_to(x - w / 2 + 30, y - h / 2)
    ctx.line_to(x - w / 2 + 30, y + h / 2)
    ctx.stroke()
    text(ctx, title, x + 14, y, 56, INK, alpha=a)


def L_books(ctx, t):
    ground(ctx)
    t1, t2 = Sk("c2_ushi", 0.0) - 0.3, Sk("c2_hoan", 0.0) - 0.3
    a1, a2 = fade(t, t1, 0.4), fade(t, t2, 0.4)
    L_book(ctx, 290, 340, 270, 300, "信長公記", a1)
    L_book(ctx, 690, 340, 270, 300, "信長記", a2, col="#d9e6f6")
    label(ctx, "太田牛一\n同じ時代", 290, 580, 44, INK, a1)
    label(ctx, "小瀬甫庵\n江戸時代の初め", 690, 580, 44, INK, a2)
    label(ctx, "1,000丁ほど", 290, 740, 56, OD_L, fade(t, Sk("c2_1000", 0.3), 0.4))
    label(ctx, "3,000丁", 690, 740, 56, TK_L, fade(t, Sk("c2_hoan", 0.45), 0.4))
    label(ctx, "どちらが正しいか 決着していない", 492, 850, 44, PENCIL_T, fade(t, Sk("c2_undec", 0.2), 0.4))


def L_dist(ctx, t):
    """柵から武田の隊までの距離（たとえば200m・仮定）"""
    ground(ctx)
    fence_v(ctx, 300, 250, 740)
    for k in range(3):
        horse(ctx, 700 + 30 * (k % 2), 360 + 150 * k, 0.9, 1.0, face=-1, ph=(t * 1.6 + 0.3 * k) % 1)
    label(ctx, "柵", 300, 200, 44, FENCE_C, 1.0)
    label(ctx, "武田", 720, 200, 44, TK_L, 1.0)
    a = fade(t, Sk("c1_g4", 0.5), 0.4)
    if a > 0.003:
        line2(ctx, (330, 830), (680, 830), "#9aa3b5", 3, a, dash=[8, 7])
        arrow2(ctx, (332, 830), (676, 830), RED, 6, a, both=True)
        if t < Sk("c1_200", 0.42):
            label(ctx, "どれくらい手前？", 506, 772, 50, RED, a)
        else:
            label(ctx, "200m ・仮定", 506, 772, 56, RED, fade(t, Sk("c1_200", 0.42), 0.4))


def L_fence30(ctx, t):
    """柵に着いた駒は、柵を壊す間（30〜90秒）も撃たれ続ける。ストップウォッチの扇が回る"""
    ground(ctx)
    fence_v(ctx, FX + 60, 230, 780)
    for r in range(3):
        for c in range(2):
            koma(ctx, FX + 150 + c * 50, 340 + r * 150, 0.9, "T", 1.0, face=-1)
        for c in range(2):
            koma(ctx, FX - 30 - c * 62, 350 + r * 150, 0.9, "O", 1.0, face=1, gun=True)
    tau = (t * 0.5) % 1.0
    for r in range(3):
        for c in range(2):
            k = (t * 0.7 + 0.31 * r + 0.17 * c) % 1.0
            flash(ctx, FX - 30 - c * 62 + 38, 350 + r * 150 - 28, k / 0.4 if k < 0.4 else 9, 1.0)
    cx, cy, r = 700, 430, 100
    ctx.set_source_rgba(1, 1, 1, 0.85)
    ctx.arc(cx, cy, r + 8, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(RED, 0.8))
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * tau)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(7)
    ctx.arc(cx, cy, r + 8, 0, 2 * math.pi)
    ctx.stroke()
    ctx.rectangle(cx - 14, cy - r - 36, 28, 22)
    ctx.fill()
    label(ctx, "柵を壊す間も 撃たれる", 640, 650, 48, INK, fade(t, Sk("c1_fence30", 0.5), 0.4))


def L_p50(ctx, t):
    """50mで10発のうち1発が当たる"""
    ground(ctx)
    koma(ctx, 110, 560, 1.1, "O", 1.0, face=1, gun=True)
    koma(ctx, 850, 560, 1.1, "T", 1.0, face=-1)
    text(ctx, "50m先の的に 10発", 492, 335, 52, INK, alpha=fade(t, Sk("c1_p50", 0.0) - 0.3, 0.4))
    a_d = fade(t, Sk("c1_p50", 0.5), 0.4)
    for i in range(10):
        x = 215 + i * 62
        hit = i == 6
        ctx.set_line_width(4)
        if hit:
            ctx.set_source_rgba(*hexrgb(RED, 0.95 * a_d))
            ctx.arc(x, 520, 22, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.9 * a_d))
            ctx.arc(x, 520, 22, 0, 2 * math.pi)
            ctx.stroke()
        else:
            ctx.set_source_rgba(1, 1, 1, 0.85 * a_d)
            ctx.arc(x, 520, 22, 0, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb("#9aa3b5", a_d))
            ctx.stroke()
    label(ctx, "当たるのは 1発ほど", 492, 640, 56, RED, a_d)
    label(ctx, "煙・動く的", 492, 750, 44, PENCIL_T, fade(t, Sk("c1_smoke", 0.2), 0.4))


# ============================================================
# 鉄砲隊の動き: 三段撃ち・めいめい撃ち・馬と歩き
# ============================================================
SAN_X = [700, 530, 360]                                   # 前 → 中 → 後
SAN_Y = [330, 470, 610, 750]
SAN_P = 2.7


def L_sandan(ctx, t, t0, a_labels=1.0, t_label=None, title="三段撃ち", a_title=1.0):
    """3つの組が順に撃ち、撃った組は後ろへ下がって込め直す（2.7秒で1回り）"""
    ground(ctx)
    fence_v(ctx, 790, 250, 800)
    for r in range(4):
        koma(ctx, 870, SAN_Y[r] + 20, 0.9, "T", 1.0, face=-1)
    q = (t - t0) / SAN_P
    k = int(math.floor(q)) if q >= 0 else 0
    p = (q - k) if q >= 0 else 0.0
    mv = ease_in_out(clamp01((p - 0.30) / 0.50))
    groups = []
    for g in range(3):
        s0, s1 = (g - k) % 3, (g - k - 1) % 3
        x = SAN_X[s0] + (SAN_X[s1] - SAN_X[s0]) * mv
        dy = 70 * math.sin(math.pi * mv) if s0 == 0 else 0.0
        groups.append((g, x, dy, s0))
    for g, x, dy, s0 in sorted(groups, key=lambda e: -e[1]):
        for r in range(4):
            koma(ctx, x, SAN_Y[r] + 20 + dy, 0.9, "O", 1.0, face=1, gun=True)
    # 前列の組の発砲
    for g, x, dy, s0 in groups:
        if s0 == 0 and q >= 0:
            for r in range(4):
                flash(ctx, x + 38 * 0.9, SAN_Y[r] + 20 - 30 * 0.9, (p - 0.04) / 0.22, 1.0)
    if t_label is not None:
        al = a_labels * fade(t, t_label, 0.4)
        label(ctx, "撃つ", SAN_X[0], 850, 44, RED, al)
        label(ctx, "待つ", SAN_X[1], 850, 44, INK, al)
        label(ctx, "込め直し", SAN_X[2], 850, 44, OD_L, al)
    label(ctx, title, 492, 160, 56, INK, a_title)


MEI = [(x, y) for x in (430, 560, 690) for y in SAN_Y]


def L_scatter(ctx, t, title="めいめい撃ち", a_title=1.0):
    ground(ctx)
    fence_v(ctx, 790, 250, 800)
    for r in range(4):
        koma(ctx, 870, SAN_Y[r] + 20, 0.9, "T", 1.0, face=-1)
    rng = np.random.default_rng(23)
    ph = rng.uniform(0, 1, len(MEI))
    for (x, y) in MEI:
        koma(ctx, x, y + 20, 0.9, "O", 1.0, face=1, gun=True)
    for i, (x, y) in enumerate(MEI):
        q = ((t / SAN_P) + ph[i]) % 1.0
        flash(ctx, x + 38 * 0.9, y + 20 - 30 * 0.9, q / 0.22, 1.0)
    label(ctx, title, 492, 160, 56, INK, a_title)


# ---- 1分間の弾の帯 ----
def band_times(kind):
    """1分間（60秒）の発射を、1つ＝10発の点で。200丁・込め直し20秒 → 60点（600発）"""
    if kind == "sandan":
        n = [7, 7, 7, 6, 7, 7, 7, 6, 6]
        out = []
        for i, c in enumerate(n):
            tt = i * 20 / 3
            out += [(tt + 0.0, j) for j in range(c)]
        return out
    if kind == "issei":
        return [(tt, j) for tt in (0.0, 20.0, 40.0) for j in range(20)]
    rng = np.random.default_rng(7)
    return [((i + 0.5) * 1.0, int(rng.integers(0, 7))) for i in range(60)]


BAND_X0, BAND_W = 150.0, 730.0


def draw_band(ctx, t, y, name, kind, t_frame, t_sweep0, t_sweep1, a=1.0, col=OD_L, mark_gap=None):
    """帯1本。名札と枠（t_frame）→ 点が左から右へ（t_sweep0〜t_sweep1。声に合わせる）。y は帯の中心"""
    af = a * fade(t, t_frame, 0.4)
    if af <= 0.003:
        return
    text(ctx, name, BAND_X0 - 20, y - 68, 44, INK, align="left", alpha=af)
    ctx.set_source_rgba(1, 1, 1, 0.8 * af)
    rrect(ctx, BAND_X0 - 20, y - 46, BAND_W + 40, 100, 10)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * af))
    ctx.set_line_width(2.6)
    rrect(ctx, BAND_X0 - 20, y - 46, BAND_W + 40, 100, 10)
    ctx.stroke()
    prog = clamp01((t - t_sweep0) / max(t_sweep1 - t_sweep0, 1e-6))
    tm = prog * 60.0
    px = BAND_W / 60.0
    pts = band_times(kind)
    ctx.set_source_rgba(*hexrgb(col, 0.92 * af))
    for tt, j in pts:
        if tt > tm:
            continue
        if kind == "issei":
            cx = BAND_X0 + tt * px + (j % 4) * 11
            cy = y - 36 + (j // 4) * 15
        elif kind == "sandan":
            cx = BAND_X0 + tt * px + 4
            cy = y - 36 + j * 11.5
        else:
            cx = BAND_X0 + tt * px
            cy = y - 36 + j * 11.5
        ctx.new_sub_path()
        ctx.arc(cx, cy, 4.6, 0, 2 * math.pi)
    ctx.fill()
    if 0 < prog < 1:
        line2(ctx, (BAND_X0 + tm * px, y - 46), (BAND_X0 + tm * px, y + 54), RED, 3, af)
    if mark_gap is not None:
        ag = af * fade(t, mark_gap, 0.4)
        x0g, x1g = BAND_X0 + 4.0 * px, BAND_X0 + 19.0 * px
        arrow2(ctx, (x0g, y + 76), (x1g, y + 76), RED, 4, ag, both=True, head=14)
        label(ctx, "からっぽ 20秒", (x0g + x1g) / 2, y + 120, 44, RED, ag)


def axis_labels(ctx, y, a):
    text(ctx, "0秒", BAND_X0 - 20, y, 40, PENCIL_T, align="left", alpha=a)
    text(ctx, "1分", BAND_X0 + BAND_W + 20, y, 40, PENCIL_T, align="right", alpha=a)


# ---- 進む武田の隊（馬・歩き） ----
def L_march(ctx, t, mounted=True, speed=120.0, fence=True, a_fence=1.0, a_labels=1.0, t0=0.0, label_text=None, a_label=1.0):
    """柵の内側の鉄砲隊と、近づく武田の隊（馬か歩き）。ふちで繰り返す"""
    ground(ctx)
    if fence:
        fence_v(ctx, FX, 168, 836, a_fence)
    for ci in (2, 1, 0):
        for ri, gy in enumerate(WAVE_YS):
            koma(ctx, GUN_X[ci], gy + 18, 0.86, "O", 1.0, face=1, gun=True)
    rng = np.random.default_rng(31)
    ph = rng.uniform(0, 1, 18)
    for ci in range(3):
        for ri, gy in enumerate(WAVE_YS):
            q = ((t / 3.0) + ph[ci * 6 + ri]) % 1.0
            flash(ctx, GUN_X[ci] + 36, gy + 18 - 26, q / 0.2, 1.0)
    span = 440.0
    for c in range(2):
        for r in range(WAVE_ROWS):
            q = ((t - t0) * speed / span + 0.37 * c + 0.11 * r) % 1.0
            x = 900 - q * span + c * 6
            al = clamp01(q / 0.08) * clamp01((1 - q) / 0.08)
            y = WAVE_YS[r] + 18
            if mounted:
                horse(ctx, x + 12, y, 0.86, al, face=-1, ph=(t * 2.2 + 0.2 * r) % 1)
            else:
                koma(ctx, x, y, 0.86, "T", al, face=-1)
    if a_labels > 0.003:
        label(ctx, "織田・徳川", 190, 150, 44, OD_L, a_labels)
        label(ctx, "武田", 740, 150, 44, TK_L, a_labels)
    if label_text:
        label(ctx, label_text, 640, 880 - 20, 52, RED, a_label)


# ---- 参考: 実験 ----
def L_exp(ctx, t):
    ground(ctx)
    koma(ctx, 130, 700, 1.7, "O", 1.0, face=1, gun=True)
    koma(ctx, 800, 700, 1.7, "T", 1.0, face=-1)
    label(ctx, "身長 160cm", 690, 560, 44, INK, fade(t, Sk("c7_exp", 0.5), 0.4))
    a = fade(t, Sk("c7_exp", 0.35), 0.4)
    arrow2(ctx, (200, 470), (770, 470), RED, 5, a, both=True)
    label(ctx, "50m", 485, 410, 56, RED, a)
    a5 = fade(t, Sk("c7_4of5", 0.15), 0.4)
    for i in range(5):
        x = 265 + i * 100
        hit = i < 4
        ctx.set_line_width(4)
        if hit:
            ctx.set_source_rgba(*hexrgb(RED, 0.95 * a5))
            ctx.arc(x, 800, 30, 0, 2 * math.pi)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK if hit else "#9aa3b5", 0.9 * a5))
        ctx.arc(x, 800, 30, 0, 2 * math.pi)
        ctx.stroke()
    label(ctx, "5発のうち 4発 当たり", 492, 860, 52, RED, a5)
    label(ctx, "落ち着いて 動かない的", 492, 250, 48, PENCIL_T, fade(t, Sk("c7_calm", 0.0), 0.4))


# ============================================================
# 0章 左ページ（設楽原・柵・ひと区切り・止められたの意味・1万回の中央値）
# ============================================================
def river(ctx, x, y0, y1, a=1.0):
    if a <= 0.003:
        return
    ys = list(range(int(y0), int(y1) + 1, 12))
    for w, col, al in ((64, "#bcd6f2", 0.95), (70, INK, 0.0)):
        ctx.set_source_rgba(*hexrgb(col, al * a))
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i, yy in enumerate(ys):
            xx = x + 16 * math.sin(yy / 55.0)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(OD_L, 0.6 * a))
    ctx.set_line_width(3)
    for off in (-32, 32):
        for i, yy in enumerate(ys):
            xx = x + off + 16 * math.sin(yy / 55.0)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()


def army(ctx, x0, y0, team, a=1.0, face=1, cols=3, rows=3, flag=True):
    for r in range(rows):
        for c in range(cols):
            koma(ctx, x0 + c * 48, y0 + r * 62, 0.85, team, a, face=face, flag=(flag and c == cols - 1 and r == 0) if face == 1 else (flag and c == 0 and r == 0) or False)


def L_map(ctx, t):
    ground(ctx)
    text(ctx, "設楽原", 205, 175, 64, INK, alpha=fade(t, Sk("c0_where", 0.0) - 0.2, 0.4))
    a_r = fade(t, Sk("c0_river", 0.12), 0.5)
    river(ctx, 580, 215, 850, a_r)
    label(ctx, "連吾川", 580, 258, 44, OD_L, a_r)
    a_a = fade(t, Sk("c0_river", 0.3), 0.5)
    army(ctx, 130, 480, "O", a_a, face=1)
    army(ctx, 700, 480, "T", a_a, face=-1)
    label(ctx, "織田・徳川", 190, 372, 44, OD_L, a_a)
    label(ctx, "武田勝頼", 760, 372, 44, TK_L, a_a)
    u = ease_out(clamp01((t - Sk("c0_fence", 0.05)) / 0.9))
    ext = ease_in_out(clamp01((t - Sk("c0_seg", 0.05)) / 1.5))
    y0, y1 = lerp(485, 205, ext), lerp(660, 840, ext)
    fence_v(ctx, 420, y0, y1, 1.0, prog=u)
    label(ctx, "馬防柵", 420, 392 if ext < 0.5 else 175, 44, FENCE_C, fade(t, Sk("c0_fence", 0.2), 0.4))
    a_s = fade(t, Sk("c0_seg", 0.55), 0.5)
    if a_s > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, 0.95 * a_s))
        ctx.set_line_width(6)
        ctx.set_dash([14, 10])
        rrect(ctx, 345, 440, 150, 200, 16)
        ctx.stroke()
        ctx.set_dash([])
        label(ctx, "ひと区切り", 420, 700, 48, RED, a_s)


def L_seg(ctx, t):
    """柵のひと区切り: 武田の1つの隊（1,000人）と、この区切りを受け持つ鉄砲（全体の5分の1）"""
    ground(ctx)
    fence_v(ctx, 330, 170, 850)
    ys = [200 + 40 * i for i in range(17)]
    a5 = fade(t, Sk("c0_fifth", 0.2), 0.5)
    for y in ys:
        inside = 440 <= y <= 580
        koma(ctx, 262, y + 12, 0.5, "O", 1.0 if inside else 1 - 0.6 * a5, face=1, gun=True)
    ctx.set_source_rgba(*hexrgb(RED, 0.95))
    ctx.set_line_width(5)
    ctx.set_dash([14, 10])
    rrect(ctx, 215, 420, 160, 180, 14)
    ctx.stroke()
    ctx.set_dash([])
    for r in range(3):
        for c in range(5):
            koma(ctx, 620 + c * 50, 480 + r * 48, 0.7, "T", fade(t, Sk("c0_1000", 0.0) - 0.2, 0.4), face=-1)
    label(ctx, "武田の1つの隊", 740, 392, 44, TK_L, fade(t, Sk("c0_1000", 0.0) - 0.1, 0.4))
    label(ctx, "1,000人", 745, 650, 56, TK_L, fade(t, Sk("c0_1000", 0.45), 0.4))
    label(ctx, "鉄砲 全体の5分の1", 300, 372, 44, OD_L, a5)


def L_def(ctx, t):
    """止められた ＝ 柵が通せんぼ ではなく、撃たれて戦えなくなる"""
    ground(ctx)
    fence_v(ctx, 300, 330, 790)
    GY = (540, 700)
    for y in GY:
        koma(ctx, 170, y + 20, 1.1, "O", 1.0, face=1, gun=True)
    text(ctx, "止められた", 492, 168, 72, INK, alpha=fade(t, Sk("c0_measure", 0.1), 0.4))
    a_n = fade(t, Sk("c0_notblock", 0.1), 0.4)
    if a_n > 0.003:
        label(ctx, "柵で 通せんぼ", 300, 285, 48, INK, a_n)
        pen_line(ctx, 205, 270, 395, 300, RED, seed=3, width=8, progress=clamp01((t - Sk("c0_notblock", 0.5)) / 0.5), alpha=a_n)
        pc_ = clamp01((t - Sk("c0_notblock", 0.65)) / 0.6)
        pen_line(ctx, 245, 470, 355, 650, RED, seed=4, width=11, progress=pc_, alpha=a_n)
        pen_line(ctx, 355, 470, 245, 650, RED, seed=5, width=11, progress=clamp01((pc_ - 0.4) / 0.6), alpha=a_n)
    ts = Sk("c0_shot", 0.0)
    ty = 700
    if t < ts:
        koma(ctx, 620, ty + 20, 1.5, "T", 1.0, face=-1)
    else:
        tau = (t - ts) % 3.2
        x = 840 - 160 * clamp01(tau / 1.4)
        al = clamp01(tau / 0.25)
        if tau < 1.9:
            koma(ctx, x, ty + 20, 1.5, "T", al, face=-1)
        elif tau < 2.25:
            u = (tau - 1.9) / 0.35
            koma(ctx, x, ty + 20, 1.5 * (1 - 0.25 * u), "T", 1 - u, face=-1)
            poof(ctx, x, ty + 20, u, 1.7)
        if 1.4 <= tau < 1.9:
            for y in GY:
                flash(ctx, 170 + 46, y + 20 - 33, (tau - 1.4) / 0.5, 1.0)
            bx = lerp(240, x, clamp01((tau - 1.5) / 0.35))
            if 1.5 <= tau < 1.9:
                ctx.set_source_rgba(*hexrgb(INK, 0.9))
                ctx.arc(bx, ty - 10 + 20 - 20, 7, 0, 2 * math.pi)
                ctx.fill()
        label(ctx, "撃たれて\n消える", 700, 520, 52, TK_L, fade(t, Sk("c0_shot", 0.15), 0.4))


def L_sorted(ctx, t):
    """1万回の結果を、少ない順に並べる（101本＝1本が100回ぶん）。中央値（ちょうど真ん中）の1本を赤く"""
    ground(ctx)
    q = R["A1"]["quant"]
    hmax = max(q)
    n = len(q)
    x0, x1, base = 112.0, 872.0, 720.0
    step = (x1 - x0) / (n - 1)
    rng = np.random.default_rng(13)
    perm = rng.permutation(n)
    ts = Sk("c0_mid", 0.0) - 0.8
    u = ease_in_out(clamp01((t - ts) / 1.8))
    a_f = fade(t, Sk("c0_luck", 0.0) - 0.3, 0.4)
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    for i in range(n):
        xs = x0 + i * step
        xr = x0 + perm[i] * step
        x = xr + (xs - xr) * u
        h = 450 * q[i] / hmax
        mid = i == 50
        col = RED if (mid and t >= Sk("c0_mid", 0.5)) else OD_L
        ctx.set_source_rgba(*hexrgb(col, 0.9 * a_f))
        ctx.rectangle(x - step * 0.36, base - h, step * 0.72, h)
        ctx.fill()
    line2(ctx, (x0 - 20, base + 4), (x1 + 20, base + 4), INK, 4, a_f)
    a_t = fade(t, ts - 0.2, 0.4)
    if t < ts - 0.2:
        text(ctx, "1万回の結果", 492, 172, 56, INK, alpha=a_f)
    else:
        text(ctx, "1万回の結果を 少ない順に", 492, 172, 56, INK, alpha=fade(t, ts - 0.2, 0.4))
    label(ctx, "少ない", x0 + 40, base + 62, 44, PENCIL_T, a_t)
    label(ctx, "多い", x1 - 40, base + 62, 44, PENCIL_T, a_t)
    am = fade(t, Sk("c0_mid", 0.5), 0.4)
    if am > 0.003:
        xm = x0 + 50 * step
        hm = 450 * q[50] / hmax
        arrow2(ctx, (xm, base - hm - 110), (xm, base - hm - 12), RED, 5, am)
        label(ctx, "中央値", xm, base - hm - 150, 48, RED, am)
    label(ctx, "1本 ＝ 100回ぶん", 492, 850, 40, PENCIL_T, a_t)


def L_key(ctx, t):
    """効いていたのは、柵と、鉄砲の数"""
    ground(ctx)
    fence_v(ctx, FX, 168, 836)
    for ci in (2, 1, 0):
        for ri, gy in enumerate(WAVE_YS):
            koma(ctx, GUN_X[ci], gy + 18, 0.86, "O", 1.0, face=1, gun=True)
    for ri, gy in enumerate(WAVE_YS):
        koma(ctx, 700, gy + 18, 0.86, "T", 1.0, face=-1)
        koma(ctx, 770, gy + 18 + 14 * (ri % 2), 0.86, "T", 1.0, face=-1)
    pr = clamp01((t - Sk("c0_eff", 0.2)) / 0.9)
    pen_circle(ctx, 225, 500, 150, 365, RED, seed=2, width=7, progress=pr)
    pen_circle(ctx, FX + 4, 500, 62, 375, RED, seed=4, width=7, progress=clamp01((pr - 0.2) / 0.8))
    label(ctx, "鉄砲の数", 225, 135, 52, RED, fade(t, Sk("c0_eff", 0.35), 0.4))
    label(ctx, "柵", FX + 104, 135, 52, RED, fade(t, Sk("c0_eff", 0.6), 0.4))
    label(ctx, "撃つ順番", 640, 135, 44, PENCIL_T, fade(t, Sk("c0_eff", 0.1), 0.4))


# ============================================================
# 章4 左ページ（撃ち方の比べ）
# ============================================================
G4_X = [185, 490, 795]
G4_NAMES = ["一斉", "三段", "めいめい"]


def _g4(n_list, t_van, key_prefix):
    return [HGrid(n_list[i], G4_X[i], 268, 29, 28, 0.46, t_van[i], t_van[i] + 1.1, seed=20 + i) for i in range(3)]


H4F = _g4([FR["B_issei"] * 100, FR["B_sandan"] * 100, FR["B_kakuji"] * 100], [Sk("c4_ans1", 0.45) + 0.3 * i for i in range(3)], "f")
H4N = _g4([FR["C_issei"] * 100, FR["C_sandan"] * 100, FR["C_kakuji"] * 100], [Sk("c4_issei2", 0.4), Sk("c4_4", 0.3), Sk("c4_4", 0.3) + 0.3], "n")
for _h in H4F:
    _h.n = float(round(_h.n))
    _h.m = int(math.ceil(_h.n)) or 1
H4N[0].n, H4N[0].m = 1.5, 2
for _h in H4N[1:]:
    _h.n = float(round(_h.n))
    _h.m = int(math.ceil(_h.n)) or 1
C4F = ["18人", "18人", "18人"]
C4N = ["1〜2人", "4人", "4人"]
T4F_CNT = [Sk("c4_ans1", 0.55) + 0.3 * i for i in range(3)]
T4N_CNT = [Sk("c4_issei2", 0.45), Sk("c4_4", 0.4), Sk("c4_4", 0.4) + 0.3]


def L_c4(ctx, t, fence):
    ground(ctx)
    t_on = Sk("c4_fence", 0.0) - 0.4 if fence else Sk("c4_nofence", 0.0) - 0.4
    a = fade(t, t_on + 0.2, 0.4)
    text(ctx, "柵あり" if fence else "柵なし", 492, 160, 60, INK, alpha=a)
    hs, cs, tc = (H4F, C4F, T4F_CNT) if fence else (H4N, C4N, T4N_CNT)
    for i in range(3):
        h = hs[i]
        ctx.set_source_rgba(1, 1, 1, 0.55 * a)
        rrect(ctx, G4_X[i] - 140, 196, 280, 400, 14)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
        ctx.set_line_width(2.5)
        rrect(ctx, G4_X[i] - 140, 196, 280, 400, 14)
        ctx.stroke()
        h.t_cap = t_on + 0.2
        h.draw(ctx, t)
        label(ctx, G4_NAMES[i], G4_X[i], 565, 44, INK, a)
        text(ctx, cs[i], G4_X[i], 630, 60, RED, alpha=fade(t, tc[i], 0.4))
    # 弾が途切れる20秒と、柵を壊す（越える）時間
    key = Sk("c4_30", 0.0) if fence else Sk("c4_run", 0.0)
    ab = fade(t, key - 0.6, 0.4)
    label(ctx, "弾が途切れる 20秒", 110, 700, 44, INK, ab, align="left")
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * ab))
    ctx.set_line_width(3)
    rrect(ctx, 110, 735, 20 * 18, 26, 6)
    ctx.set_source_rgba(*hexrgb(OD_L, 0.9 * ab))
    ctx.fill()
    if fence:
        label(ctx, "柵を壊す 30秒以上", 110, 797, 44, INK, ab, align="left")
        ctx.set_source_rgba(*hexrgb(TK_L, 0.9 * ab))
        rrect(ctx, 110, 832, 30 * 18, 26, 6)
        ctx.fill()
        text(ctx, "→", 110 + 30 * 18 + 28, 845, 44, TK_L, alpha=ab)
    else:
        label(ctx, "柵を越える 数秒", 110, 797, 44, INK, ab, align="left")
        ctx.set_source_rgba(*hexrgb(TK_L, 0.9 * ab))
        rrect(ctx, 110, 832, 5 * 18, 26, 6)
        ctx.fill()


# ============================================================
# 右ページ: 付せん・棒（止められた人数）の梯子
# ============================================================
def stk(ctx, t, key, s, y, color="yellow", fg=INK, a=1.0, size=44, tilt=-0.012, off=0.3, x=RX, frac=0.0, until=None):
    """右ページの付せん。台本の文（手がかり key）から現れる。until を過ぎると消える"""
    t0 = Sk(key, frac) + off
    if t < t0:
        return 0, 0
    al = a * fade(t, t0)
    if until is not None:
        al *= out_fade(t, until, 0.3)
    return mini_sticky(ctx, s, x, y, size, color, fg=fg, a=al, align="left", tilt=tilt)


def row_sticky(ctx, t, x, y_top, w, title, rows, t_show, until=None, color="yellow", size=42, step=52, grow=True, title_col=RED, a=1.0):
    """見出しと行が順に書かれていく付せん。rows=[(文字, その行が現れる時刻), …]。grow=True なら見えている行の数に合わせて高さが伸びる"""
    al = a * fade(t, t_show, 0.4)
    if until is not None:
        al *= out_fade(t, until, 0.3)
    if al <= 0.003:
        return
    shown = sum(clamp01((t - tr) / 0.35) for _s, tr in rows) if grow else float(len(rows))
    h = 22 + 56 + step * shown + 14
    ctx.save()
    ctx.translate(x + w / 2, y_top + h / 2)
    ctx.rotate(-0.006)
    ctx.translate(-(x + w / 2), -(y_top + h / 2))
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * al)
    rrect(ctx, x + 5, y_top + 8, w, h, 6)
    ctx.fill()
    fill(ctx, hexrgb(STICKY[color], al))
    rrect(ctx, x, y_top, w, h, 6)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * al)
    ctx.rectangle(x, y_top, w, 12)
    ctx.fill()
    text(ctx, title, x + 28, y_top + 40, 44, title_col, align="left", alpha=al)
    for i, (s_, tr) in enumerate(rows):
        wr(ctx, s_, x + 28, y_top + 22 + 56 + step * (i + 0.5), size, INK, tr, t, align="left", alpha=al)
    ctx.restore()


T_LAD = Sk("c0_next", 0.0) - 1.2                         # 梯子の枠が出る（その中身を、の声の1.2秒前）
T_BOX_OUT = T_LAD - 0.3                                  # 冒頭の答えの箱が消える
T_SHRINK = Sk("c0_oda", 0.0)
T_ES = Sk("c8_note", 0.0) - 0.3                          # 終了画面の始まり（注意書きの文の頭の少し前から最後の約15秒）

QLINES = ["長篠の戦い、", "鉄砲の三段撃ちは", "本当に強かった？"]
QTXT = "".join(QLINES)                                   # 題名・サムネと同じ言葉
QSMALL = "長篠の戦い、鉄砲の三段撃ちは\n本当に強かった？"
HIDE_AT = 3.2
PEAK = wave_killed_frac(HIDE_AT)

class WaveTeaser(lk.OpeningTeaser):
    """冒頭の答えの箱「止められた割合 ？」: 数字は出さず、棒だけが（消えた駒の割合に合わせて）伸び、3.2秒で止まる。ずっと「？」"""

    def draw_box(self, ctx, t, a=1.0):
        al = a * (lk._out_fade(t, self.t_out, 0.4) if self.t_out is not None else 1.0)
        if al <= 0.003:
            return
        x0, y0, x1, y1 = self.box
        ctx.set_source_rgba(1, 1, 1, 0.6 * al)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * al))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        cy = (y0 + y1) / 2
        text(ctx, self.box_title, x0 + 32, cy, self.title_size, INK, align="left", alpha=al)
        tx = x0 + 32 + text_width(self.box_title, self.title_size) + 28
        tw = max(80.0, x1 - 32 - (text_width("？", self.val_size) + 20) - tx)
        bh = 36
        ctx.set_source_rgba(1, 1, 1, 0.7 * al)
        rrect(ctx, tx, cy - bh / 2, tw, bh, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * al))
        ctx.set_line_width(2.5)
        rrect(ctx, tx, cy - bh / 2, tw, bh, 6)
        ctx.stroke()
        wd = tw * clamp01(self.value_at(min(t, HIDE_AT)) / self.vmax)
        if wd > 1:
            ctx.set_source_rgba(*hexrgb(self.color, 0.92 * al))
            rrect(ctx, tx, cy - bh / 2, max(4.0, wd), bh, 6)
            ctx.fill()
        text(ctx, "？", tx + tw + 14, cy, self.val_size, RED, align="left", alpha=al)


teaser = WaveTeaser(QLINES, left=None, thumb_text=QTXT, q_pos=(1050, 285), q_size=96, box=(1030, 560, 1830, 704), box_title="止められた割合", unit="",
                    peak=PEAK, vmax=1.0, t_up0=0.0, t_up1=HIDE_AT, hide_at=None, t_out=T_BOX_OUT,
                    value_fn=lambda t_: wave_killed_frac(min(t_, HIDE_AT)), title_size=52, val_size=64, color=BLUE)


def R_ch0(ctx, t):
    big = out_fade(t, T_SHRINK - 0.2, 0.2)
    teaser.draw_question(ctx, t, big)
    small = fade(t, T_SHRINK + 0.05, 0.2) * out_fade(t, S("ch1") - 0.2, 0.2)
    if small > 0.003:
        text(ctx, QSMALL, RX, 100, 56, INK, align="left", alpha=small)
    teaser.draw_box(ctx, t)
    t_off = Sk("c0_first", 0.0) - 0.1
    if Sk("c0_10k", 0.35) <= t < t_off + 0.4:
        a = fade(t, Sk("c0_10k", 0.35), 0.3) * out_fade(t, t_off, 0.3)
        sticky(ctx, "1万回", RX + 135, 275, 64, "pink", fg=RED, a=a, tilt=-0.02)
    t_off2 = Sk("c0_cond", 0.0) - 0.1
    if Sk("c0_first", 0.3) <= t < t_off2 + 0.4:
        a = fade(t, Sk("c0_first", 0.3), 0.3) * out_fade(t, t_off2, 0.3)
        sticky(ctx, "撃つ順番", RX + 170, 285, 64, "yellow", a=a, tilt=-0.015)
        pr = clamp01((t - Sk("c0_first", 0.75)) / 0.5)
        pen_line(ctx, RX + 20, 235, RX + 330, 340, RED, seed=3, width=11, progress=pr, alpha=a)
        pen_line(ctx, RX + 330, 235, RX + 20, 340, RED, seed=5, width=11, progress=clamp01((pr - 0.4) / 0.6), alpha=a)
    t_out = T_BOX_OUT - 0.2
    row_sticky(ctx, t, RX - 12, 200, 790, "条件",
               [("武田の1つの隊 1,000人・仮定", Sk("c0_1000", 0.2)), ("鉄砲は全体の5分の1・仮定", Sk("c0_fifth", 0.2)), ("止められた人数", Sk("c0_measure", 0.2))],
               Sk("c0_cond", 0.3), until=t_out)
    stk(ctx, t, "c0_sanju", "三重・およそ2km", 500, "mint", size=46, tilt=-0.01, off=0.3, frac=0.35, until=Sk("c0_measure", 0.0) - 0.2)
    stk(ctx, t, "c0_per100", "100人のうち", 500, "yellow", size=48, tilt=-0.01, off=0.3, until=Sk("c0_mid", 0.0) - 0.2)
    stk(ctx, t, "c0_mid", "1万回の中央値", 500, "pink", fg=RED, size=48, tilt=0.01, off=0.2, until=t_out)


def slot(ctx, t, key, s, until_key, size=42, color="mint", frac=0.3, fg=INK, until=None, tilt=-0.01):
    """ 4行の付せんの下の1行の枠（y=418）。次の付せんが出る前に消える"""
    return stk(ctx, t, key, s, 418, color, fg=fg, size=size, tilt=tilt, off=0.0, frac=frac, x=1008,
               until=(Sk(until_key, 0.0) - 0.3 if until_key else until))


def R_ch1(ctx, t):
    row_sticky(ctx, t, 1008, 72, 520, "よく語られる形",
               [("鉄砲 3,000丁", Sk("c1_g1", 0.1)), ("三段撃ち", Sk("c1_g2", 0.1)), ("馬で攻める", Sk("c1_g3", 0.1)), ("柵あり", Sk("c1_g4", 0.1))],
               Sk("c1_four", 0.1), until=S("ch2") - 0.3, grow=False)
    slot(ctx, t, "c1_600", "この区切り 600丁", "c1_hoan", 44, "pink", 0.35, RED)
    slot(ctx, t, "c1_hoan", "甫庵の読み物・信長記", "c1_g2", 40, "mint", 0.2)
    slot(ctx, t, "c1_komi", "込め直し", "c1_20", 44, "yellow", 0.3)
    slot(ctx, t, "c1_20", "1発 約20秒", "c1_g3", 46, "pink", 0.3, RED)
    slot(ctx, t, "c1_200", "たとえば200m・仮定", "c1_fence30", 44, "mint", 0.3)
    slot(ctx, t, "c1_fence30", "柵を越える 30〜90秒・仮定", "c1_p50", 42, "mint", 0.3)
    slot(ctx, t, "c1_p50", "50mで 10発に1発・仮定", None, 42, "mint", 0.3, until=S("ch2") - 0.3)


def R_ch2(ctx, t):
    u = S("ch3") - 0.3
    stk(ctx, t, "c2_ushi", "牛一の記録・信長公記", 150, "mint", size=44, tilt=-0.01, off=0.5, until=u)
    stk(ctx, t, "c2_1000", "鉄砲 1,000丁ほど（信長公記）", 240, "yellow", size=46, tilt=0.01, off=0.3, frac=0.3, until=u)
    w_, _h = stk(ctx, t, "c2_hoan", "江戸時代の読み物", 330, "pink", size=46, tilt=-0.01, off=0.2, until=u)
    ac = fade(t, Sk("c2_hoan", 0.8), 0.4) * out_fade(t, u, 0.3)
    if ac > 0.003:
        pen_circle(ctx, 1050 + w_ / 2, 330, w_ / 2 + 30, 48, RED, seed=7, width=6, progress=clamp01((t - Sk("c2_hoan", 0.8)) / 0.6), alpha=ac)
    stk(ctx, t, "c2_200", "この区切り 200丁", 415, "yellow", size=46, tilt=-0.01, off=0.3, until=u)


def R_ch3(ctx, t):
    u = S("ch4") - 0.3
    stk(ctx, t, "c3_meimei", "めいめい撃ち", 150, "yellow", size=52, tilt=-0.012, off=0.5, until=u)
    stk(ctx, t, "c3_200", "200丁", 250, "mint", size=52, tilt=0.01, off=0.3, until=u)
    stk(ctx, t, "c3_600", "1分で およそ600発", 350, "pink", fg=RED, size=48, tilt=-0.012, off=0.3, frac=0.3, until=u)


def R_ch4(ctx, t):
    stk(ctx, t, "c4_issei", "一斉撃ち", 140, "yellow", size=52, tilt=-0.012, off=0.7, until=S(REST_G) - 0.3)
    stk(ctx, t, "c4_idea", "三段撃ち ＝ 弾が途切れない工夫", 240, "mint", size=42, tilt=0.008, off=0.2, until=S(REST_G) - 0.3)


def R_ch5(ctx, t):
    stk(ctx, t, "c5_all", "全員が歩いて攻めた場合", 150, "yellow", size=46, tilt=-0.012, off=0.3, until=S("ch6") - 0.3)
    stk(ctx, t, "c5_slow", "遅い ＝ 撃たれる時間が長い", 250, "pink", fg=RED, size=42, tilt=0.01, off=0.2, until=S("ch6") - 0.3)


def R_ch6(ctx, t):
    stk(ctx, t, "c6_sec", "柵を越える 数秒・仮定", 150, "mint", size=46, tilt=-0.012, off=0.3, until=min(Sk("c6_other", 0.0) - 1.4, T_P6 - 0.4))


def R_ch7(ctx, t):
    u = S("ch8") - 0.3
    stk(ctx, t, "c7_exp", "実験: 50m先の的", 150, "mint", size=46, tilt=-0.012, off=0.5, until=u)
    stk(ctx, t, "c7_4of5", "5発中4発", 245, "pink", fg=RED, size=52, tilt=0.01, off=0.3, until=u)
    stk(ctx, t, "c7_calm", "戦場とはちがう", 335, "yellow", size=46, tilt=-0.01, off=0.3, until=u)


def R_ch8(ctx, t):
    pass


R_CH = [R_ch0, R_ch1, R_ch2, R_ch3, R_ch4, R_ch5, R_ch6, R_ch7, R_ch8]


def draw_right(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    if idx >= len(R_CH):
        return
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, R_CH[idx - 1], t)
    R_CH[idx](ctx, t)


# ---- 棒の梯子（名札の下に棒を置く縦積み。名札が長いので横並びにしない） ----
class StackLadder(lk.LadderPanel):
    """LadderPanel の縦積み版。名札（左）と人数（右）を1行に、棒を2行目に置く。点線・「＋」・枠と値の時刻は LadderPanel と同じ。値は 100人あたりの人数（割合 → 四捨五入）"""

    def __init__(self, title, rows, box, t_frame, vmax=VMAX, plus=True, label_size=40, val_size=44, title_size=40, bar_h=18, unit_max=110.0,
                 fade=0.4, grow=0.9, title_line=None):
        lk.LadderPanel.__init__(self, title, rows, box=box, t_frame=t_frame, vmax=vmax, fmt=lambda v: f"{ihalf(v * 100)}人", plus=plus, arrows=False,
                                title_size=title_size, label_size=label_size, val_size=val_size, sub_size=40, fade=fade, grow=grow, title_line=title_line)
        self.bar_h2, self.unit_max = bar_h, unit_max

    def layout(self):
        if self._geo is not None:
            return self._geo
        x0, y0, x1, y1 = self.box
        n = len(self.rows)
        top = y0 + 72
        nb = sum(1 for i, r in enumerate(self.rows) if i and r.branch)
        unit = min(self.unit_max, (y1 - 14 - top) / (n + 0.45 * nb))
        ys, yb, extra = [], [], 0.0
        for i, r in enumerate(self.rows):
            if i and r.branch:
                extra += 0.45
            yt = top + unit * (i + extra)
            ys.append(yt + self.label_size * 0.6)
            yb.append(yt + self.label_size * 1.2 + self.bar_h2 * 0.5 + 2)
        self._geo = dict(title_cy=y0 + 36, ys=ys, yb=yb, unit=unit, label_x=x0 + 32, track_x=x0 + 32, track_w=(x1 - 28) - (x0 + 32), bar_h=self.bar_h2, val_x=x1 - 28)
        return self._geo

    def layout_problems(self):
        g = self.layout()
        out = []
        if g["unit"] < self.label_size * 1.15 + self.bar_h2 + 2:
            out.append(f"{self.title}: 行間 {g['unit']:.0f}px が名札 {self.label_size}px ＋棒に対して詰まる")
        wmax = max(text_width(self.label_of(i), self.label_size) for i in range(len(self.rows)))
        if wmax + 150 > g["track_w"]:
            out.append(f"{self.title}: 名札 {wmax:.0f}px と人数が1行に入らない")
        return out

    def draw(self, ctx, t, a=1.0):
        g = self.layout()
        x0, y0, x1, y1 = self.box
        af = a * lk._fade(t, self.t_frame, self.fade)
        if af <= 0.003:
            return
        ctx.set_source_rgba(1, 1, 1, 0.6 * af)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * af))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        text(ctx, self.title, x0 + 32, g["title_cy"], self.title_size, INK, align="left", alpha=af)
        tx, tw, bh = g["track_x"], g["track_w"], g["bar_h"]
        for i, r in enumerate(self.rows):
            la = a * lk._fade(t, r.t_label, self.fade)
            if la <= 0.003:
                continue
            y, yb_ = g["ys"][i], g["yb"][i]
            if i and r.branch:
                mid = (g["yb"][i - 1] + bh / 2 + (y - self.label_size * 0.6)) / 2
                ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * la))
                ctx.set_line_width(3)
                ctx.set_dash([10, 8])
                ctx.move_to(x0 + 24, mid)
                ctx.line_to(x1 - 24, mid)
                ctx.stroke()
                ctx.set_dash([])
            text(ctx, self.label_of(i), g["label_x"], y, self.label_size, INK, align="left", alpha=la)
            ctx.set_source_rgba(1, 1, 1, 0.7 * la)
            rrect(ctx, tx, yb_ - bh / 2, tw, bh, 5)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * la))
            ctx.set_line_width(2.5)
            rrect(ctx, tx, yb_ - bh / 2, tw, bh, 5)
            ctx.stroke()
            if r.value is None and r.text is None:
                continue
            bu = ease_out(clamp01((t - r.t_value) / self.grow))
            if bu <= 0.003:
                continue
            frac = 0.0 if r.value is None else clamp01(r.value / self.vmax)
            wd = max(4.0, tw * frac) * bu
            ctx.set_source_rgba(*hexrgb(r.color, 0.92 * la))
            rrect(ctx, tx, yb_ - bh / 2, wd, bh, 5)
            ctx.fill()
            vt = self.value_text(r)
            if vt and bu > 0.15:
                text(ctx, vt, g["val_x"], y, self.val_size, r.color, align="right", alpha=la * clamp01((bu - 0.15) / 0.3))


LAD_LABELS = ["3,000丁・三段撃ち・馬・柵あり", "鉄砲を1,000丁に", "三段撃ちをやめる", "馬を下りて歩く", "＋柵を取ると"]
LAD_NAMES = ["3,000丁・三段撃ち・馬・柵あり", "＋鉄砲を1,000丁に", "＋三段撃ちをやめる", "＋馬を下りて歩く", "＋柵を取ると"]
LAD_KEYS = ["A1", "A2", "A3", "A4", "E1"]
LAD_COL = [BLUE, BLUE, BLUE, BLUE, ORANGE]
LAD_ANN = ["c0_next", "c2_add", "c3_add", "c5_add", "c6_take"]                      # その名札を言う声
LAD_ANS = ["c1_ans", "c2_ans", "c3_ans", "c5_ans", "c6_ans"]                         # その答えを言う声
LAD_TL = [T_LAD + 0.05] + [Sk(LAD_ANN[i], 0.0) - 1.2 for i in range(1, 5)]
LAD_TV = [Sk(LAD_ANS[i], 0.5) for i in range(5)]
MAIN_ROWS = [lk.Row(LAD_LABELS[i], FR[LAD_KEYS[i]], t_label=LAD_TL[i], t_value=LAD_TV[i], color=LAD_COL[i], line=ID[LAD_ANS[i]], text=f"{CNT[LAD_KEYS[i]]}人", branch=(i == 4))
             for i in range(5)]
MAIN = StackLadder("止められた人数（100人あたり）", MAIN_ROWS, box=(1000, 462, 1860, 925), t_frame=T_LAD, title_line=ID["c0_next"])
MAIN_NAME_CUES = [lk.Cue(f"主な梯子 名札「{LAD_NAMES[i]}」", "frame", LAD_TL[i], LAD_TL[i] + 0.4, ID[LAD_ANN[i]]) for i in range(5)]
BELLS = list(LAD_TV)

# 章4: 撃ち方を並べて比べる（梯子の本線には入れない）
P4_ROWS = [
    lk.Row("柵あり・一斉撃ち", FR["B_issei"], t_label=Sk("c4_fence", 0.0) - 1.2, t_value=Sk("c4_ans1", 0.5), color=BLUE, line=ID["c4_ans1"], text="18人"),
    lk.Row("柵あり・三段撃ち", FR["B_sandan"], t_label=Sk("c4_fence", 0.0) - 1.1, t_value=Sk("c4_ans1", 0.5) + 0.3, color=BLUE, line=ID["c4_ans1"], text="18人"),
    lk.Row("柵あり・めいめい撃ち", FR["B_kakuji"], t_label=Sk("c4_fence", 0.0) - 1.0, t_value=Sk("c4_ans1", 0.5) + 0.6, color=BLUE, line=ID["c4_ans1"], text="18人"),
    lk.Row("柵なし・一斉撃ち", FR["C_issei"], t_label=Sk("c4_nofence", 0.0) - 1.2, t_value=Sk("c4_issei2", 0.5), color=ORANGE, line=ID["c4_issei2"], text="1〜2人", branch=True),
    lk.Row("柵なし・三段撃ち", FR["C_sandan"], t_label=Sk("c4_nofence", 0.0) - 1.1, t_value=Sk("c4_4", 0.4), color=ORANGE, line=ID["c4_4"], text="4人"),
    lk.Row("柵なし・めいめい撃ち", FR["C_kakuji"], t_label=Sk("c4_nofence", 0.0) - 1.0, t_value=Sk("c4_4", 0.4) + 0.3, color=ORANGE, line=ID["c4_4"], text="4人")]
T_P4 = Sk("c4_cmp", 0.0) - 1.2
P4 = StackLadder("撃ち方を比べる（鉄砲1,000丁・馬）", P4_ROWS, box=(1000, 380, 1860, 925), t_frame=T_P4, plus=False, title_line=ID["c4_cmp"])
BELLS += [Sk("c4_ans1", 0.5), Sk("c4_issei2", 0.5), Sk("c4_4", 0.4)]

# 章6: よく語られる形から柵だけを取る（最初の棒 53 の隣に 柵なしの棒 11）
T_P6 = Sk("c6_other", 0.0) - 1.2
P6_ROWS = [lk.Row("3,000丁・三段撃ち・馬・柵あり", FR["A1"], t_label=T_P6 + 0.1, t_value=T_P6 + 0.5, color=BLUE, plain=True, text=f"{CNT['A1']}人"),
           lk.Row("3,000丁・三段撃ち・馬・柵なし", FR["E2"], t_label=Sk("c6_11", 0.0) - 1.2, t_value=Sk("c6_11", 0.5), color=ORANGE, line=ID["c6_11"], text=f"{CNT['E2']}人", plain=True)]
P6 = StackLadder("よく語られる形から 柵だけを取ると", P6_ROWS, box=(1000, 110, 1860, 405), t_frame=T_P6, plus=False, unit_max=100.0, title_line=ID["c6_other"])
BELLS += [Sk("c6_11", 0.5)]

# 章7: 参考（当たりやすさだけを変える）
T_P7 = Sk("c7_redo", 0.0) - 1.2
P7_ROWS = [lk.Row("柵あり・置いた値", FR["A4"], t_label=Sk("c7_cond", 0.0) - 1.2, t_value=Sk("c7_cond", 0.0) - 0.7, color=BLUE, text=f"{CNT['A4']}人"),
           lk.Row("柵あり・実験の値に近づける", FR["D1"], t_label=Sk("c7_cond", 0.0) - 1.1, t_value=Sk("c7_arrow", 0.35), color=BLUE, line=ID["c7_arrow"], text=f"{CNT['D1']}人"),
           lk.Row("柵なし・置いた値", FR["E1"], t_label=Sk("c7_arrow", 0.0) - 1.2, t_value=Sk("c7_arrow", 0.0) - 0.7, color=ORANGE, branch=True, text=f"{CNT['E1']}人"),
           lk.Row("柵なし・実験の値に近づける", FR["D2"], t_label=Sk("c7_arrow", 0.0) - 1.1, t_value=Sk("c7_arrow", 0.75), color=ORANGE, line=ID["c7_arrow"], text=f"{CNT['D2']}人")]
P7 = StackLadder("参考: 当たりやすさだけを変える", P7_ROWS, box=(1000, 440, 1860, 925), t_frame=T_P7, plus=False, title_line=ID["c7_redo"])
BELLS += [Sk("c7_arrow", 0.35), Sk("c7_arrow", 0.75)]

# まとめ: 本線の5本を右ページいっぱいに（棒は声に合わせず、最初から全部見える）
T8 = S("ch8") + 0.15
SUM_ROWS = [lk.Row(LAD_LABELS[i], FR[LAD_KEYS[i]], t_label=T8 + 0.05 + 0.03 * i, t_value=T8 + 0.3 + 0.06 * i, color=LAD_COL[i], text=f"{CNT[LAD_KEYS[i]]}人", branch=(i == 4))
            for i in range(5)]
SUMP = StackLadder("止められた人数（100人あたり）", SUM_ROWS, box=(1000, 100, 1860, 900), t_frame=T8, label_size=44, val_size=52, title_size=48, bar_h=36, unit_max=140.0,
                   fade=0.3, title_line=ID["c8_0"])


def vis(t, t0, t1, fi=0.2, fo=0.2):
    return clamp01((t - t0) / fi) * (1 - clamp01((t - t1) / fo))


def draw_panel(ctx, t):
    a_all = out_fade(t, T_ES, 0.4)
    a_main = (1 - vis(t, S("ch4") - 0.15, S("ch5") + 0.15)) * (1 - vis(t, S("ch7") - 0.15, 1e9))
    grp(ctx, a_all * a_main, lambda c, t_: MAIN.draw(c, t_), t)
    grp(ctx, a_all * vis(t, S("ch4") - 0.15, S(REST_G)), lambda c, t_: P4.draw(c, t_), t)
    grp(ctx, a_all * vis(t, S("ch6") - 0.0, S("ch7") - 0.15), lambda c, t_: P6.draw(c, t_), t)
    grp(ctx, a_all * vis(t, S("ch7") - 0.15, S("ch8") - 0.25), lambda c, t_: P7.draw(c, t_), t)
    grp(ctx, a_all, lambda c, t_: SUMP.draw(c, t_), t)


ALL_CUES = (MAIN.cues() + MAIN_NAME_CUES + P4.cues() + P6.cues() + P7.cues() + SUMP.cues())


# ============================================================
# 左ページ: 100人の駒・早回し・場面の並び（層）
# ============================================================
def ans_grid(cid, key_gap, key_ans, seed):
    return HGrid(CNT[cid], 492, 245, 64, 56, 0.76, Sk(key_ans, 0.4), Sk(key_ans, 0.4) + 1.6, seed=seed, cap="100人のうち", t_cap=S(key_gap) + 1.9, cap_y=162,
                 cnt=f"止められた {CNT[cid]}人", t_cnt=Sk(key_ans, 0.45), cnt_y=830, line_cap=ID[key_ans], line_cnt=ID[key_ans])


G0 = HGrid(50, 492, 245, 64, 56, 0.76, Sk("c0_per100", 0.5), Sk("c0_per100", 0.5) + 1.4, seed=1, cap="100人のうち", t_cap=Sk("c0_per100", 0.0) - 1.0, cap_y=162,
           cnt=None, t_cnt=Sk("c0_per100", 0.55), cnt_y=830, line_cap=ID["c0_per100"], line_cnt=ID["c0_per100"])
G1 = ans_grid("A1", "g1_1", "c1_ans", 2)
G2 = ans_grid("A2", "g2_1", "c2_ans", 3)
G3 = ans_grid("A3", "g3_1", "c3_ans", 4)
G5 = ans_grid("A4", "g5_1", "c5_ans", 5)
G6 = ans_grid("E1", "g6_1", "c6_ans", 6)
FFS = {k: FastForward(FR[c], sd, S(k), S(k) + 2.2) for k, c, sd in (("g1_1", "A1", 1), ("g2_1", "A2", 2), ("g3_1", "A3", 3), ("g5_1", "A4", 4), ("g6_1", "E1", 5))}

G6A = HGrid(CNT["A1"], 270, 300, 36, 34, 0.52, 0, 0, seed=40, cap="柵あり", t_cap=Sk("c6_other", 0.0) - 0.3, cap_y=240, cnt=f"{CNT['A1']}人", t_cnt=Sk("c6_other", 0.0) - 0.3,
            cnt_y=690, preset=True)
G6B = HGrid(CNT["E2"], 700, 300, 36, 34, 0.52, Sk("c6_11", 0.4), Sk("c6_11", 0.4) + 1.3, seed=41, cap="柵なし", t_cap=Sk("c6_other", 0.0) - 0.3, cap_y=240, cnt=f"{CNT['E2']}人",
            t_cnt=Sk("c6_11", 0.45), cnt_y=690, line_cap=ID["c6_11"], line_cnt=ID["c6_11"])
G7A = HGrid(CNT["D1"], 270, 300, 36, 34, 0.52, Sk("c7_arrow", 0.35), Sk("c7_arrow", 0.35) + 1.4, seed=42, cap="柵あり", t_cap=Sk("c7_redo", 0.0) - 0.6, cap_y=240, cnt=f"{CNT['D1']}人",
            t_cnt=Sk("c7_arrow", 0.4), cnt_y=690, line_cap=ID["c7_arrow"], line_cnt=ID["c7_arrow"])
G7B = HGrid(CNT["D2"], 700, 300, 36, 34, 0.52, Sk("c7_arrow", 0.75), Sk("c7_arrow", 0.75) + 1.2, seed=43, cap="柵なし", t_cap=Sk("c7_redo", 0.0) - 0.6, cap_y=240, cnt=f"{CNT['D2']}人",
            t_cnt=Sk("c7_arrow", 0.8), cnt_y=690, line_cap=ID["c7_arrow"], line_cnt=ID["c7_arrow"])
T8L = S("ch8") + 0.25
G8A = HGrid(CNT["A2"], 270, 300, 36, 34, 0.52, 0, 0, seed=44, cap="三段撃ち", t_cap=T8L, cap_y=240, cnt=f"{CNT['A2']}人", t_cnt=T8L + 0.1, cnt_y=690, preset=True)
G8B = HGrid(CNT["A3"], 700, 300, 36, 34, 0.52, 0, 0, seed=45, cap="めいめい撃ち", t_cap=T8L, cap_y=240, cnt=f"{CNT['A3']}人", t_cnt=T8L + 0.1, cnt_y=690, preset=True)


def paint(fn, *a_, **k_):
    def f(ctx, t):
        fn(ctx, t, *a_, **k_)
    return f


def with_ground(grid):
    def f(ctx, t):
        ground(ctx)
        grid.draw(ctx, t)
    return f


def L_grids6(ctx, t):
    ground(ctx)
    text(ctx, "3,000丁・三段撃ち・馬", 492, 160, 52, INK, alpha=fade(t, Sk("c6_other", 0.0) - 0.3, 0.4))
    G6A.draw(ctx, t)
    G6B.draw(ctx, t)


def L_grids7(ctx, t):
    ground(ctx)
    G7A.draw(ctx, t)
    G7B.draw(ctx, t)
    label(ctx, "当たりやすさだけ 実験の値に", 492, 800, 44, PENCIL_T, fade(t, Sk("c7_redo", 0.0) - 0.5, 0.4))


def L_grids8(ctx, t):
    ground(ctx)
    text(ctx, f"どちらも 100人のうち{CNT['A3']}人", 492, 160, 52, INK, alpha=fade(t, T8L, 0.4))
    G8A.draw(ctx, t)
    G8B.draw(ctx, t)


def L_bands3(ctx, t):
    ground(ctx)
    t_f = Sk("c3_why", 0.0) - 0.2
    s0, s1 = Sk("c3_200", 0.0), Sk("c3_600", 0.9)
    draw_band(ctx, t, 340, "三段撃ち", "sandan", t_f, s0, s1)
    draw_band(ctx, t, 570, "めいめい撃ち", "kakuji", t_f, s0, s1)
    axis_labels(ctx, 700, fade(t, t_f, 0.4))
    label(ctx, "1分で およそ600発", 492, 800, 56, RED, fade(t, Sk("c3_600", 0.2), 0.4))
    text(ctx, "＝", 492, 455, 72, RED, alpha=fade(t, Sk("c3_same", 0.2), 0.4))


def L_bands4(ctx, t):
    ground(ctx)
    draw_band(ctx, t, 250, "三段撃ち", "sandan", -50, -100, -90)
    draw_band(ctx, t, 420, "めいめい撃ち", "kakuji", -50, -100, -90)
    draw_band(ctx, t, 590, "一斉撃ち", "issei", Sk("c4_issei", 0.0) - 0.7, Sk("c4_issei", 0.5), Sk("c4_empty", 0.9), mark_gap=Sk("c4_empty", 0.2))


def L_sandan3(ctx, t):
    L_sandan(ctx, t, Sk("c3_nosup", 0.0) - 0.4, a_labels=1.0, t_label=None, title="三段撃ち")
    label(ctx, "あった？ なかった？", 492, 245, 52, RED, fade(t, Sk("c3_unk", 0.1), 0.4))


LAYERS = []


def layer(name, t0, t1, fn, fi=0.4, fo=0.4):
    LAYERS.append((name, t0, t1, fn, fi, fo))


# ---- 区切り（第4章と第5章のあいだ・声なし約4秒・章ではない・早回しでもない）。左ページ「ここまで」・右ページ「ここから」。亀が左から右へ歩く ----
# engine/longkit.py の Eyecatch を使う。区切りの間はこの部品だけが見える（前の章の絵は draw() 側で消す）
REST_G = next(g_ for g_ in sorted(GAP_NOTE) if "区切り" in GAP_NOTE[g_])
EYE_LEFT = ("撃ち方を変えても", f"{CNT['B_issei']}人のまま")       # 18 は data.json の値（柵あり・一斉撃ち＝三段撃ち＝めいめい撃ち）
EYE_RIGHT = ("馬を下りたら？", "柵がなかったら？")
EYE = lk.Eyecatch(S(REST_G), EYE_LEFT, EYE_RIGHT, dur=dur(REST_G))


def rest_alpha(t):
    """見開きの本体（前の章の絵）をどれだけ隠すか。区切りの始まる0.25秒前から先に消し（区切りの紙と前の章の文字が重ならないように）、区切りの間は全部隠す"""
    pre = clamp01((t - (EYE.t0 - 0.25)) / 0.25) if t < EYE.t1 else 0.0
    if EYE.t0 <= t < EYE.t1 + 0.36:          # 区切りが消えきるまでは前後の章の絵を出さない（本番の声で 8:09 に重なった）
        return 1.0
    return max(pre, EYE.alpha(t))


G_SB = Sk("c0_where", 0.0) - 0.25
layer("wave", 0.0, G_SB, lambda ctx, t: L_wave(ctx, t), fi=0.0)
layer("map", G_SB, Sk("c0_1000", 0.0) - 0.3, L_map)
layer("seg", Sk("c0_1000", 0.0) - 0.3, Sk("c0_measure", 0.0) - 0.3, L_seg)
layer("def", Sk("c0_measure", 0.0) - 0.3, Sk("c0_per100", 0.0) - 1.2, L_def)
layer("per100", Sk("c0_per100", 0.0) - 1.2, Sk("c0_luck", 0.0) - 0.3, with_ground(G0))
layer("sorted", Sk("c0_luck", 0.0) - 0.3, Sk("c0_eff", 0.0) - 0.3, L_sorted)
layer("key", Sk("c0_eff", 0.0) - 0.3, S("ch1") + 0.1, L_key)
# 1 よく語られる形
layer("c1_intro", S("ch1") + 0.1, Sk("c1_g1", 0.0) - 0.3, lambda ctx, t: L_march(ctx, t, True, 120.0, label_text="よく語られる形", a_label=fade(t, S("ch1") + 0.4, 0.4)))
layer("c1_gun", Sk("c1_g1", 0.0) - 0.3, Sk("c1_g2", 0.0) - 0.4,
      lambda ctx, t: L_guncount(ctx, t, 30, 6, "鉄砲 3,000丁", Sk("c1_g1", 0.0) - 0.2, Sk("c1_600", 0.1), "このひと区切り 600丁", Sk("c1_600", 0.35)))
layer("c1_san", Sk("c1_g2", 0.0) - 0.4, Sk("c1_g3", 0.0) - 0.4,
      lambda ctx, t: L_sandan(ctx, t, Sk("c1_3sets", 0.3), 1.0, Sk("c1_3sets", 0.1)))
layer("c1_horse", Sk("c1_g3", 0.0) - 0.4, Sk("c1_g4", 0.0) - 0.4,
      lambda ctx, t: L_march(ctx, t, True, 120.0, label_text="全員 馬に乗る", a_label=fade(t, Sk("c1_allhorse", 0.2), 0.4)))
layer("c1_dist", Sk("c1_g4", 0.0) - 0.4, Sk("c1_fence30", 0.0) - 0.4, L_dist)
layer("c1_f30", Sk("c1_fence30", 0.0) - 0.4, Sk("c1_p50", 0.0) - 0.4, L_fence30)
layer("c1_p50", Sk("c1_p50", 0.0) - 0.4, S("g1_1"), L_p50)
layer("c1_ff", S("g1_1"), S("g1_1") + 2.3, lambda ctx, t: FFS["g1_1"].draw(ctx, t))
layer("c1_ans", S("g1_1") + 1.7, Sk("c2_ushi", 0.0) - 0.4, with_ground(G1))
# 2 鉄砲1,000丁
layer("c2_book", Sk("c2_ushi", 0.0) - 0.4, Sk("c2_use", 0.0) - 0.3, L_books)
layer("c2_gun", Sk("c2_use", 0.0) - 0.3, S("g2_1"),
      lambda ctx, t: L_guncount(ctx, t, 10, 2, "鉄砲 1,000丁", Sk("c2_use", 0.0) - 0.1, Sk("c2_200", 0.1), "このひと区切り 200丁", Sk("c2_200", 0.35)))
layer("c2_ff", S("g2_1"), S("g2_1") + 2.3, lambda ctx, t: FFS["g2_1"].draw(ctx, t))
layer("c2_ans", S("g2_1") + 1.7, Sk("c3_nosup", 0.0) - 0.4, with_ground(G2))
# 3 三段撃ちをやめたら
layer("c3_san", Sk("c3_nosup", 0.0) - 0.4, Sk("c3_meimei", 0.0) - 0.4, L_sandan3)
layer("c3_sc", Sk("c3_meimei", 0.0) - 0.4, S("g3_1"), lambda ctx, t: L_scatter(ctx, t))
layer("c3_ff", S("g3_1"), S("g3_1") + 2.3, lambda ctx, t: FFS["g3_1"].draw(ctx, t))
layer("c3_ans", S("g3_1") + 1.7, Sk("c3_why", 0.0) - 0.3, with_ground(G3))
layer("c3_band", Sk("c3_why", 0.0) - 0.3, S("ch4") + 0.1, L_bands3)
# 4 全員で一斉に撃ったら
layer("c4_band", S("ch4") + 0.1, Sk("c4_fence", 0.0) - 0.4, L_bands4)
layer("c4_f", Sk("c4_fence", 0.0) - 0.4, Sk("c4_nofence", 0.0) - 0.4, lambda ctx, t: L_c4(ctx, t, True))
layer("c4_n", Sk("c4_nofence", 0.0) - 0.4, S(REST_G), lambda ctx, t: L_c4(ctx, t, False))
# 5 馬を下りて
layer("c5_m", S("ch5") + 0.1, Sk("c5_all", 0.0) - 0.2, lambda ctx, t: L_march(ctx, t, True, 120.0, label_text="馬で攻める", a_label=fade(t, S("ch5") + 0.5, 0.4)))
layer("c5_w", Sk("c5_all", 0.0) - 0.2, S("g5_1"), lambda ctx, t: L_march(ctx, t, False, 45.0, label_text="全員 歩いて攻める", a_label=fade(t, Sk("c5_all", 0.0), 0.4)))
layer("c5_ff", S("g5_1"), S("g5_1") + 2.3, lambda ctx, t: FFS["g5_1"].draw(ctx, t))
layer("c5_ans", S("g5_1") + 1.7, Sk("c6_take", 0.0) - 0.4, with_ground(G5))
# 6 柵がなかったら
layer("c6_m", Sk("c6_take", 0.0) - 0.4, S("g6_1"),
      lambda ctx, t: L_march(ctx, t, False, 45.0, a_fence=1 - fade(t, Sk("c6_take", 0.4), 1.2), label_text="柵なし", a_label=fade(t, Sk("c6_take", 0.4) + 0.8, 0.4)))
layer("c6_ff", S("g6_1"), S("g6_1") + 2.3, lambda ctx, t: FFS["g6_1"].draw(ctx, t))
layer("c6_ans", S("g6_1") + 1.7, Sk("c6_other", 0.0) - 0.4, with_ground(G6))
layer("c6_g", Sk("c6_other", 0.0) - 0.4, Sk("c7_exp", 0.0) - 0.4, L_grids6)
# 7 参考
layer("c7_exp", Sk("c7_exp", 0.0) - 0.4, Sk("c7_redo", 0.0) - 0.4, L_exp)
layer("c7_g", Sk("c7_redo", 0.0) - 0.4, S("ch8") + 0.1, L_grids7)
# 8 まとめ
layer("c8_g", S("ch8") + 0.1, T_ES + 0.8, L_grids8)

LAYER_OUT, LAYER_IN, LAYER_DELAY = 0.2, 0.25, 0.2


def draw_left(ctx, t):
    for name, t0, t1, fn, fi, fo in LAYERS:
        fo = min(fo, LAYER_OUT)
        if t < t0 - 1e-6 or t > t1 + fo:
            continue
        a_in = 1.0 if fi <= 0 else ease_out(clamp01((t - t0 - LAYER_DELAY) / LAYER_IN))
        a = a_in * (1.0 if fo <= 0 else 1 - clamp01((t - t1) / fo))
        ctx.save()
        clip_left(ctx)
        grp(ctx, a, fn, t)
        ctx.restore()


ALL_CUES += (G0.cues() + G1.cues() + G2.cues() + G3.cues() + G5.cues() + G6.cues() + G6B.cues() + G7A.cues() + G7B.cues())


# ============================================================
# 章カード・終了画面・全体
# ============================================================
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"
LCX_E, RCX_E = 490, 1430


def big_sticky(ctx, label_, value, cx, cy, w, h, color, fg=INK, a=1.0, tilt=0.0, lsz=46, vsz=64):
    """終了画面の答えの付せん。上に名前（lsz）、下に答え（vsz）。(cx, cy) は中心"""
    if a <= 0.003:
        return
    bg = STICKY.get(color, color)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, -w / 2 + 6, -h / 2 + 9, w, h, 8)
    ctx.fill()
    fill(ctx, hexrgb(bg, a))
    rrect(ctx, -w / 2, -h / 2, w, h, 8)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(-w / 2, -h / 2, w, 12)
    ctx.fill()
    text(ctx, label_, 0, -h * 0.22, lsz, INK, alpha=a)
    text(ctx, value, 0, h * 0.2, vsz, fg, alpha=a)
    ctx.restore()


def end_rows():
    return [("三段撃ちをやめても", f"100人のうち{CNT['A3']}人のまま", "yellow", INK, -0.010),
            ("柵を取ると", f"{CNT['A4']}人 → {CNT['E1']}人", "pink", RED, 0.008),
            ("効いていたのは", "柵と、鉄砲の数", "mint", INK, -0.008)]


def end_screen(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "長篠の鉄砲隊と武田の隊を、1万回 戦わせたら", LCX_E, 162, 40, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=60)
    t9 = Sk("c8_ch", 0.0)
    q = fade(t, t0 + 0.6, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
    if q > 0.003:
        sticky(ctx, "あなたが武田勝頼なら、\nどう攻めますか？", RCX_E, 480, 52, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


CARD_DELAY = 0.35
CARD_X, CARD_Y = LCX, 500          # 章カードは左ページ（右ページの表・付せんと重ならない所）に出す。見開きの中央だと右ページの表の見出しにかかった


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1] - CARD_DELAY            # 前の章の左の絵が消え終わってから出す（重ならない）
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, CARD_TITLES[ch[0]], a, x=CARD_X, y=CARD_Y, size=60)


def pages(ctx, t):
    draw_left(ctx, t)
    draw_right(ctx, t)
    draw_panel(ctx, t)
    overlays(ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    ra = rest_alpha(t)
    if t < T_ES + 0.6 and ra < 0.997:
        grp(ctx, (1 - fade(t, T_ES, 0.5)) * (1 - ra), pages, t)
    EYE.draw(ctx, t)
    if t >= T_ES:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・早回し）
# ============================================================
def footstep(freq, dur_=0.11):
    """亀の足音（ぽてっ）: 少し下がる短い音＋やわらかい当たり（escalator-long.py と同じ）"""
    t_ = core._t(dur_)
    f = freq * (1 + 0.5 * np.exp(-t_ * 55))
    body = np.sin(2 * np.pi * np.cumsum(f) / core.SR) * np.exp(-t_ * 38) * np.minimum(1, t_ * 900)
    rng = np.random.default_rng(int(freq))
    tap = np.convolve(rng.standard_normal(len(t_)), np.ones(12) / 12, mode="same") * np.exp(-t_ * 160) * 0.6
    return body + tap


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 9):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for k_, tt in enumerate(EYE.step_times()):                  # 亀の足音（区切りの歩き）
        mx.add(tt, footstep(300 + 40 * (k_ % 2)), 0.30)
    for g in sorted(GAP_NOTE):
        if g == REST_G:
            continue
        if GAP_SEC[g] >= 2.0:
            beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
            mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
        else:
            mx.add(S(g) + 0.05, tick(1400, 0.05), 0.3)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.3, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.3)
    mx.add(Sk("c0_first", 0.4), chord([293.7, 370.0, 440.0], 1.6), 0.4)
    mx.add(Sk("c8_2", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(Sk("c8_ch", 0.0) + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
def still_list():
    return [
        ("01_0.0s", "① 0.0秒: 問い（サムネと同じ言葉）・柵の内側の鉄砲隊と近づく武田の駒・答えの棒", 0.0),
        ("02_2.5s", "② 2.5秒: 鉄砲隊が順に撃ち、近づく駒が消える・棒が伸びる", 2.5),
        ("03_5.0s", "③ 5.0秒: 数字は「？」に伏せる", 5.0),
        ("04_ch0_map", "④ 第0章: 設楽原・連吾川・柵（ひと区切りを囲む）", Sk("c0_seg", 0.8)),
        ("05_ch0_cond", "⑤ 第0章: 条件の付せん・ひと区切り（1,000人・5分の1）", Sk("c0_measure", 0.0) - 0.8),
        ("06_ch0_50", "⑥ 第0章: 100人あたりに直して言う（50駒が消える）", Ek("c0_per100") - 0.2),
        ("08_ch1_san", "⑧ 第1章: 三段撃ち（3つの組が順に撃ち、後ろで込め直し）", Sk("c1_komi", 0.0) - 0.3),
        ("09_ch1_ans", "⑨ 第1章の答え: 100人のうち53人", Ek("c1_ans") + 0.6),
        ("10_ch2_ans", "⑩ 第2章の答え: 鉄砲1,000丁 → 18人", Ek("c2_ans") + 0.6),
        ("11_ch3_ans", "⑪ 第3章の答え: 三段撃ちをやめても18人", Ek("c3_ans") - 0.6),
        ("13_ch4_fence", "⑬ 第4章: 柵あり 一斉・三段・めいめい（18人）", Ek("c4_ans1") + 0.8),
        ("14_ch4_nofence", "⑭ 第4章: 柵なし 1〜2人・4人・4人", Ek("c4_4") + 0.8),
        ("21_eye_start", "㉑ 区切り（第4章と第5章のあいだ）: 左ページ「ここまで」・右ページ「ここから」・亀が歩き出す", EYE.still_times()[0]),
        ("22_eye_mid", "㉒ 区切り: 亀が真ん中を歩く・足あと", EYE.still_times()[1]),
        ("23_eye_end", "㉓ 区切り: 亀が右ページへ着く", EYE.still_times()[2]),
        ("15_ch5_ans", "⑮ 第5章の答え: 馬を下りて歩く 22人", Ek("c5_ans") + 0.6),
        ("16_ch6_ans", "⑯ 第6章の答え: 柵を取ると 7人", Ek("c6_ans") + 0.6),
        ("17_ch6_11", "⑰ 第6章: よく語られる形から柵だけ取ると 11人（53の隣）", Ek("c6_11") + 0.8),
        ("18_ch7", "⑱ 第7章（参考）: 22→55・7→24", Ek("c7_arrow") - 0.3),
        ("19_summary", "⑲ まとめ: 梯子の5本・三段撃ちも めいめいも18人", Sk("c8_1", 0.5)),
        ("20_end", "⑳ 終了画面", min(DUR - 0.5, Sk("c8_sub", 0.0) + 1.0)),
    ]


def _ts(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_sheet(out_dir, items, thumb=(480, 270), cols=4):
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    paths = []
    for nm, _lab, tt in items:
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}  {_lab}")
    W_, H_ = thumb
    lab_h, pad = 34, 10
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + H_ + 3), f"{k + 1}  {_ts(items[k][2])}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")


def stills_preview(out_dir):
    stills_sheet(out_dir, still_list())
    from PIL import Image
    ims = []
    for k_, tt in enumerate(EYE.still_times()):
        p_ = WORK / f"_eye_{k_}.png"
        lf.still(draw, tt, p_)
        ims.append(Image.open(p_).convert("RGB").resize((480, 270), Image.LANCZOS))
        p_.unlink()
    sh = Image.new("RGB", (480 * len(ims) + 8 * (len(ims) - 1), 270), "white")
    for k_, im in enumerate(ims):
        sh.paste(im, (k_ * 488, 0))
    sh.save(out_dir / "eyecatch_480.png")
    print("区切り:", out_dir / "eyecatch_480.png", [round(x, 1) for x in EYE.still_times()])
    med_ts = [Sk("c0_mid", 0.0) + 0.3, Sk("c0_mid", 0.5) + 1.0, Ek("c0_mid") - 0.8]       # 「中央値」の付せん・赤い矢印と札が出た所・「中央値と呼びます」の終わり
    ims = []
    for k_, tt in enumerate(med_ts):
        p_ = WORK / f"_med_{k_}.png"
        lf.still(draw, tt, p_)
        ims.append(Image.open(p_).convert("RGB").resize((480, 270), Image.LANCZOS))
        p_.unlink()
    sh = Image.new("RGB", (480 * len(ims) + 8 * (len(ims) - 1), 270), "white")
    for k_, im in enumerate(ims):
        sh.paste(im, (k_ * 488, 0))
    sh.save(out_dir / "median_480.png")
    print("中央値:", out_dir / "median_480.png", [round(x, 1) for x in med_ts])


# ============================================================
# 文字起こし・読み
# ============================================================
def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字の問い・柵の内側の鉄砲隊と近づく武田の駒・答えの棒）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE.get(it.id, '映像だけ')}）")
        else:
            nt = LINE_NOTE.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間（左ページに答えの付せん・右ページに問いかけ、亀と「チャンネル登録よろしく」）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    """読みの確認。read_aloud が AivisSpeech を起動するので、--fake-voice のときは読みを作らず、文だけ並べる"""
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            reading = "" if FAKE else "\n    → " + voice.read_aloud(spoken)
            rows.append(f"{it.id}: {shown_}{reading}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


# ============================================================
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
CARD_LINES = {ln for t_ in CARD_TITLES for ln in t_.split("\n")}


def _allowed_nums():
    ok = set(range(0, 13)) | {18, 20, 22, 24, 30, 40, 50, 53, 55, 60, 90, 100, 160, 200, 600, 1000, 3000, 10000, 1575}
    ok |= {float(CNT[k]) for k in CNT}
    return ok


def first_seen(frames, pred):
    for f in frames:
        if any(pred(e[0], e) for e in f[1]):
            return f[0]
    return None


def motion_first_03():
    """0〜0.3秒で画面が動いているか（公開前チェックと同じ基準）"""
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


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text.replace("、", "")
    checks = []

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本の読み込み ----
    A(f"台本: 章は9つ（0〜8）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 9 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（声の文を並べ直すと台本の行と同じ。長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    nar_head = NARR_PATH.read_text(encoding="utf-8").splitlines()
    title_line = next(ln for ln in nar_head if ln.startswith("題名:"))
    A(f"題名「{QTXT}…」の言葉が台本の題名の行と画面の問いで同じ（サムネと同じ言葉にそろえる）", QTXT in title_line)
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:]) if S(b) < 70]
    A(f"台本: 冒頭（0〜70秒）の文と文の間は 0.3秒前後（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし（最初の無音は第1章: {min(S(g) for g in GAP_NOTE):.1f}秒）",
      all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch1"))
    fast = [g for g in GAP_NOTE if GAP_SEC[g] >= 2.0 and g != REST_G]
    A(f"台本: 無音の早回し {len(fast)} か所はどれも4秒以内（{[GAP_SEC[g] for g in fast]}）", len(fast) == 5 and all(GAP_SEC[g] <= 4.0 for g in fast))
    rests = [g for g in GAP_NOTE if "区切り" in GAP_NOTE[g]]
    A(f"台本: 区切り（ここまで／ここから・亀が歩く・声なし）は1か所・約4秒（{[GAP_SEC[g] for g in rests]}）・第4章のあと第5章の前・章は9つのまま",
      len(rests) == 1 and abs(GAP_SEC[rests[0]] - 4.0) < 1e-6 and E(REST_G) == S("ch5") and S(REST_G) > Ek("c4_fence") and len(tl.chapters) == 9
      and abs(EYE.t0 - S(REST_G)) < 1e-9 and abs(EYE.t1 - E(REST_G)) < 1e-9 and not any("ひと休み" in n_ for n_ in GAP_NOTE.values()))
    nums40 = []
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            nums40 += _re.findall(r"\d+(?:\.\d+)?", split_reading(it.text)[0])
    A(f"台本: 冒頭40秒の声の数字は 1575・1（1万回）・3（3つの列）の3個以内（{sorted(set(nums40))}）", len(set(nums40)) <= 3 and "1575" in nums40)
    first_q = tl.clip(ID["c0_q"]).text
    A("台本: 0〜5秒の声は題名の問いだけ（最初の文が題名の問い）・0:20〜0:30 に「先に言うと」（約0:29）・「条件をそろえます」は0:30より後",
      "強かった" in first_q and 20 <= S(ID["c0_first"]) <= 30 and S(ID["c0_cond"]) > 30)
    # ---- 声の数字 = data.json ----
    exp = [("c1_ans", f"100人のうち{CNT['A1']}人でした"), ("c2_ans", f"100人のうち{CNT['A2']}人でした"), ("c3_ans", f"100人のうち{CNT['A3']}人でした"),
           ("c4_ans1", f"100人のうち{CNT['B_issei']}人でした"), ("c4_issei2", "1人か2人でした"), ("c4_4", "4人ほどでした"), ("c5_ans", f"100人のうち{CNT['A4']}人でした"),
           ("c6_ans", f"100人のうち{CNT['E1']}人でした"), ("c6_11", f"100人のうち{CNT['E2']}人です"), ("c7_arrow", f"{CNT['A4']}人から{CNT['D1']}人に"),
           ("c7_arrow", f"{CNT['E1']}人から{CNT['D2']}人に"), ("c8_0", f"100人のうち{CNT['A3']}人のまま"), ("c0_per100", "100人あたりに直して"),
           ("c0_1000", "1,000人"), ("c1_hoan", "3,000丁"), ("c2_1000", "1,000丁"), ("c3_600", "およそ600発"), ("c1_p50", "10発に1発")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    # ---- 冒頭 0〜5秒 ----
    vs = [(vt - WAVE_T0, col) for vt, col in VOLLEYS if 0 <= vt - WAVE_T0 <= 5.0]
    A(f"冒頭: 0〜5秒に鉄砲隊の3つの列が順に撃つ（前列→2列目→3列目: 列 {[c for _t, c in vs]}・時刻 {[round(t_, 1) for t_, _c in vs]}）", [c for _t, c in vs][:3] == [0, 1, 2] and len(vs) >= 3)
    kk = [wave_killed_frac(k * 0.25) for k in range(0, 14)]
    A(f"冒頭: 近づく武田の駒が消えていく（0.25秒ごと・0秒目の消えた割合 {kk[0]:.0%} → 3.2秒 {kk[-1]:.0%}・単調に増える・0.8秒までに最初の駒が消える）",
      all(a <= b + 1e-12 for a, b in zip(kk, kk[1:])) and kk[0] == 0 and kk[-1] > 0.2 and wave_killed_frac(0.9) > 0)
    A(f"冒頭: 右下の棒は消えた割合に合わせて伸び、3.2秒で止まる（棒の長さ {PEAK:.0%}・数字は出さず、ずっと「？」）", abs(PEAK - wave_killed_frac(HIDE_AT)) < 1e-12)
    A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
    # ---- 梯子 ----
    A("梯子の名札は台本どおり: " + "・".join(f"「{MAIN.label_of(i)}」" for i in range(5)), [MAIN.label_of(i) for i in range(5)] == LAD_NAMES)
    A("梯子の値の文字は data.json（53・18・18・22・7）", [MAIN.value_text(r) for r in MAIN_ROWS] == [f"{ihalf(R[k]['med'] * 100)}人" for k in LAD_KEYS])
    A("梯子の本線は5本（第4章の撃ち方の比べ・第7章の参考は本線に入れず、別の枠）・5本目だけ点線で分かれる",
      len(MAIN_ROWS) == 5 and [r.branch for r in MAIN_ROWS] == [False] * 4 + [True]
      and not any(w in r.label for r in MAIN_ROWS for w in ("一斉", "実験", "当たりやすさ")) and P4 is not MAIN and P7 is not MAIN)
    A("梯子の棒の長さ ＝ 値（同じ尺度 0〜0.6）・本線の棒: 53 > 18 = 18 < 22 > 7", all(0 < r.value <= VMAX for r in MAIN_ROWS) and MAIN_ROWS[0].value > MAIN_ROWS[1].value
      and abs(MAIN_ROWS[1].value - MAIN_ROWS[2].value) < 0.005 and MAIN_ROWS[3].value > MAIN_ROWS[2].value > MAIN_ROWS[4].value)
    probs = MAIN.layout_problems() + P4.layout_problems() + P6.layout_problems() + P7.layout_problems() + SUMP.layout_problems()
    A(f"梯子の配置の問題: {probs}", not probs)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件（最も先: {min(r[3] for r in rows_):+.1f}秒）{[b[0] for b in bad[:3]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]
        pairs = lk.text_box_overlaps(frames, skip=[(T_ES, T_ES + 0.6)])        # 章カードも含めて数える（2026-10-25 外すのをやめた）
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）（章カードは数えた）",
                                                                                  "字幕の行（「字幕: …」）の箱を含めて調べた"])
        for a_, b_, x, y in spans[:10]:
            print(f"  文字の交わり {_ts(a_)}〜{_ts(b_)} 「{x}」と「{y}」")
        A(f"文字の箱の交わり（字幕・付せん・札・棒の枠・図の文字・全コマ）: {len(spans)} 組・{len(pairs)} コマ（期待 0）", not spans)
        small = lk.min_text_size(frames, 40, exempt=lambda s_: s_.startswith("字幕: "))
        for t_, lab, sz in small[:6]:
            print(f"  40px未満 {_ts(t_)} 「{lab}」 {sz:.0f}px")
        A(f"文字の大きさ: 40px 未満 {len(small)} 種（スマホで読める。幅480pxに縮めても約10px）", not small)
        edge = lk.outside_area(frames, skip=[(T_ES, T_ES + 0.6)])
        for t_, lab, bx in edge[:6]:
            print(f"  画面の端 {_ts(t_)} 「{lab}」 {bx}")
        A(f"画面の端（x 48〜1872・y 36〜1044）に近い文字: {len(edge)} 件", not edge)
        ey_in = [f for f in frames if EYE.t0 + 0.4 <= f[0] <= EYE.t1]
        ey_seen = {e[0] for f in ey_in for e in f[1]}
        ey_other = sorted(ey_seen - EYE.texts())
        A(f"区切り（{_ts(EYE.t0)}〜{_ts(EYE.t1)}）: Eyecatch.texts() の文字 {sorted(EYE.texts())} がそろって出る・前の章の絵は片づいていて、ほかの文字は出ない（余分 {ey_other}）",
          EYE.texts() <= ey_seen and not ey_other)
        ey_out = sorted({e[0] for f in frames if not (EYE.t0 - 1e-6 <= f[0] <= EYE.t1 + 0.35 + 1e-6) for e in f[1] if e[0] in EYE.texts() and e[0] in ("ここまで", "ここから")})
        A(f"区切りの文字「ここまで」「ここから」は区切りの外に出ない: {ey_out}", not ey_out)
        tp = teaser.check([f for f in frames if f[0] <= 5.0 + 1e-9])
        A(f"OpeningTeaser.check（0秒目に問いの全行・伏せ忘れなし）: {tp or 'OK'}", not tp)
        q0 = [e for f in frames if f[0] == 0.0 for e in f[1] if e[0] in QLINES]
        A(f"冒頭の問い: 0秒目に3行そろって {min(e[5] for e in q0):.0f}px（90px 以上）・サムネと同じ言葉「{QTXT}」", len(q0) == 3 and min(e[5] for e in q0) >= 90 and QTXT == "長篠の戦い、鉄砲の三段撃ちは本当に強かった？")
        digs = sorted({e[0] for t_, e in allt if HIDE_AT + 0.1 <= t_ <= T_BOX_OUT - 0.1 and e[1] > 1030 and 560 <= e[2] <= 704 and _re.search(r"\d", e[0])})
        A(f"答えの箱: 3.2秒から梯子の枠が出るまで、数字を伏せている（箱の中の数字 {digs}）", not digs)
        # 答えの数字（文字）が声より先に出ていないか（章ごとの窓の中で、その章で初めて出る文字）
        def win(n):
            return [f for f in frames if S(f"ch{n}") + 0.5 <= f[0] < (S(f"ch{n + 1}") if n < 8 else 1e9)]
        tokens = [("53人", "c1_ans", 1), ("止められた 53人", "c1_ans", 1), ("18人", "c2_ans", 2), ("止められた 18人", "c2_ans", 2), ("18人", "c4_ans1", 4), ("1〜2人", "c4_issei2", 4),
                  ("4人", "c4_4", 4), ("22人", "c5_ans", 5), ("止められた 22人", "c5_ans", 5), ("7人", "c6_ans", 6), ("止められた 7人", "c6_ans", 6), ("11人", "c6_11", 6),
                  ("55人", "c7_arrow", 7), ("24人", "c7_arrow", 7), ("1,000人", "c0_1000", 0)]
        for tok, key, n in tokens:
            ft = first_seen(win(n) if n else frames, lambda s_, e, tok=tok: s_ == tok and (n or e[1] < 935))
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        ok_ = _allowed_nums()
        extra = {}
        for t_, e in allt:
            lab = e[0]
            if lab.startswith("字幕: ") or lab in CARD_LINES:
                continue
            if _re.match(r"^\d[\d,]*回$", lab):
                continue                                                 # 早回しの「N回」
            if _re.match(r"^\d+%$", lab) and t_ < HIDE_AT + 0.05:
                continue                                                 # 冒頭の数字の上がり
            for m in _re.finditer(NUM_RE, lab):
                v = float(m.group(0).replace(",", ""))
                if v not in ok_:
                    extra.setdefault(m.group(0), (lab, t_))
        for v, (s_, t_) in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて data.json の値（の四捨五入）か、置いた値・閉じた値: 余分 {len(extra)}個", not extra)
        has = lambda n, ks, m=None: all(first_seen([f for f in frames if S(f"ch{n}") <= f[0] < (S(f"ch{n + 1}") if n < 8 else 1e9)], lambda s_, e, k=k: k in s_) is not None for k in ks)
        A("0章: 付せん「1万回」「撃つ順番」「条件」「武田の1つの隊 1,000人・仮定」「鉄砲は全体の5分の1・仮定」「止められた人数」「三重・およそ2km」「100人のうち」「1万回の中央値」・図の「設楽原」「連吾川」「馬防柵」「ひと区切り」「撃たれて」",
          has(0, ["1万回", "撃つ順番", "条件", "武田の1つの隊 1,000人・仮定", "鉄砲は全体の5分の1・仮定", "止められた人数", "三重・およそ2km", "100人のうち", "1万回の中央値", "設楽原", "連吾川", "馬防柵", "ひと区切り", "撃たれて", "中央値"]))
        A("1章: 付せん「よく語られる形」「鉄砲 3,000丁」「三段撃ち」「馬で攻める」「柵あり」「この区切り 600丁」「甫庵の読み物・信長記」「込め直し」「1発 約20秒」「たとえば200m・仮定」「柵を越える 30〜90秒・仮定」「50mで 10発に1発・仮定」",
          has(1, ["よく語られる形", "鉄砲 3,000丁", "三段撃ち", "馬で攻める", "柵あり", "この区切り 600丁", "甫庵の読み物・信長記", "込め直し", "1発 約20秒", "たとえば200m・仮定", "柵を越える 30〜90秒・仮定", "50mで 10発に1発・仮定"]))
        A("2章: 付せん「牛一の記録・信長公記」「鉄砲 1,000丁ほど（信長公記）」「江戸時代の読み物」「この区切り 200丁」・図の本・棒の名札「＋鉄砲を1,000丁に」",
          has(2, ["牛一の記録・信長公記", "鉄砲 1,000丁ほど（信長公記）", "江戸時代の読み物", "この区切り 200丁", "信長公記", "信長記", "＋鉄砲を1,000丁に"]))
        A("3章: 付せん「めいめい撃ち」「200丁」「1分で およそ600発」・棒の名札「＋三段撃ちをやめる」・図の2本の帯", has(3, ["めいめい撃ち", "200丁", "1分で およそ600発", "＋三段撃ちをやめる", "三段撃ち", "1分"]))
        A("4章: 付せん「一斉撃ち」・並べて比べる棒6本（柵あり・柵なし × 一斉・三段・めいめい）・「からっぽ 20秒」「弾が途切れる 20秒」「柵を壊す 30秒以上」「柵を越える 数秒」",
          has(4, ["一斉撃ち", "柵あり・一斉撃ち", "柵あり・三段撃ち", "柵あり・めいめい撃ち", "柵なし・一斉撃ち", "柵なし・三段撃ち", "柵なし・めいめい撃ち", "からっぽ 20秒", "弾が途切れる 20秒", "柵を壊す 30秒以上", "柵を越える 数秒"]))
        A("5章: 付せん「全員が歩いて攻めた場合」・棒の名札「＋馬を下りて歩く」", has(5, ["全員が歩いて攻めた場合", "＋馬を下りて歩く", "全員 歩いて攻める"]))
        A("6章: 付せん「柵を越える 数秒・仮定」・棒の名札「＋柵を取ると」・柵だけ取る棒（3,000丁・三段撃ち・馬・柵なし 11人）", has(6, ["柵を越える 数秒・仮定", "＋柵を取ると", "3,000丁・三段撃ち・馬・柵なし", "11人", "柵なし"]))
        A("7章: 付せん「実験: 50m先の的」「5発中4発」・表（柵あり・置いた値 22 → 実験の値に近づける 55・柵なし 7 → 24）・図の「身長 160cm」「5発のうち 4発 当たり」",
          has(7, ["実験: 50m先の的", "5発中4発", "柵あり・置いた値", "柵あり・実験の値に近づける", "柵なし・置いた値", "柵なし・実験の値に近づける", "身長 160cm", "5発のうち 4発 当たり"]))
        f8 = min(frames, key=lambda f: abs(f[0] - (T_ES - 0.3)))
        n8 = {e[0] for e in f8[1]}
        A("まとめ: 梯子の棒5本（名札5つ・53 → 18 → 18 → 22・点線で分かれて 7）が最初から全部見える・左ページに「三段撃ち」「めいめい撃ち」の駒が18人ずつ",
          {"3,000丁・三段撃ち・馬・柵あり", "＋鉄砲を1,000丁に", "＋三段撃ちをやめる", "＋馬を下りて歩く", "＋柵を取ると", "53人", "18人", "22人", "7人", "三段撃ち", "めいめい撃ち"} <= n8)
        f8a = min(frames, key=lambda f: abs(f[0] - (S("ch8") + 1.8)))
        A("まとめ: 棒の数字は声に合わせず、章の始まりから全部見える（章の頭1.8秒で5本とも値が出ている）", {"53人", "18人", "22人", "7人"} <= {e[0] for e in f8a[1]})
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if not e[0].startswith("字幕: ") and (e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936)]
        for t_, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t_)} 「{s_}」")
        A(f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", not out_es)
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        ans = [r[1] for r in end_rows()]
        es_ans = {e[0]: e[5] for f in frames if f[0] >= T_ES + 1.0 for e in f[1] if e[0] in ans}
        A(f"終了画面の答えの付せん（左ページ）の答えの文字は 60px 以上: {es_ans}", len(es_ans) == 3 and min(es_ans.values()) >= 59.5)
        es_last = [e for f in frames if f[0] >= Sk("c8_ch", 0.0) + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        A("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5)
        A(f"終了画面: 最後の約15秒（{DUR - T_ES:.1f}秒）・定型2行は最後の文だけ（「このチャンネルでは」{Sk('c8_ch'):.1f}秒〜）", 10.0 <= DUR - T_ES <= 20.0 and Sk("c8_ch") > T_ES)
        A("まとめの締め: 結果 → 持ち帰る一言 → 問い（3文）→ 注意書き1文 → 定型2行の順", S(ID["c8_0"]) < S(ID["c8_1"]) < S(ID["c8_2"]) < S(ID["c8_note"]) < S(ID["c8_ch"]) < S(ID["c8_sub"]))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--anchors" in args:
        for k_ in ID:
            print(k_, f"{Sk(k_):.1f}-{Ek(k_):.1f}")
        for g_ in sorted(GAP_NOTE):
            print(g_, f"{S(g_):.1f}-{E(g_):.1f}")
        return
    if "--readings" in args:
        write_readings((WORK if FAKE else OUT) / "readings.log")
        return
    if "--wraps" in args:
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        return
    if "--scenecheck" in args:
        import pickle
        pk = WORK / "frames.pkl"
        if "--cached" in args and pk.exists():
            frames = pickle.loads(pk.read_bytes())
        else:
            frames = lk.scan_frames(draw, DUR, timeline=tl)
            pk.write_bytes(pickle.dumps(frames))
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, WORK / f"at_{tt:06.1f}.png")
                print("  ", WORK / f"at_{tt:06.1f}.png")
        else:
            stills_preview(OUT / "stills_preview")
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
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    # ---- 本番（AivisSpeech の声つき。この段階ではまだ実行しない）----
    frames = lk.scan_frames(draw, DUR, timeline=tl)
    scene_checks(frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
