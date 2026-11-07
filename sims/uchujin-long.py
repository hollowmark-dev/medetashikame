"""宇宙人に出会える確率は？【ドレイクの式を1万回シミュレーション】（横型ロング・チャンネル「めでたしかめ」）

このファイルは公開日まで非公開（答えが書いてある）。公開 11/14（土）19:00。
前半はモデル（数字の計算・照合・数字の書き出し）。後半（「# ここから下は場面」から）が場面（描画・音・照合・書き出し。chikyu-long.py と同じ並び）。
モデルの計算は下絵 sims/uchujin-long.draft.py と同じ（同じ種・同じ順番で乱数を引く＝出力の数字が一致する。--numbers が下絵を実際に走らせて1行ずつ突き合わせる）。

■ モデル（下絵のとおり。値は【仮定】。動画で「〜と置きます」と言う。幅は Sandberg・Drexler・Ord 2018 の表1と同じ）
  式       : N ＝ R* × fp × ne × fl × fi × fc × L  （天の川銀河で、いま電波などで話しかけられる文明の数）
  幅       : R* 1〜100（対数一様）／fp 0.1〜1／ne 0.1〜1／fl ＝ 1−exp(−λVt)（λVt の桁は 真ん中1・標準偏差50桁の正規分布）／fi 0.001〜1／fc 0.01〜1／L 100〜100億年
  第1章    : 「中央値」（論文の幅の真ん中）は下絵の標本の中央値ではなく【理論の値】（10倍ずつで見た真ん中）: R 10・fp 10^-0.5・ne 10^-0.5・fl 1−e^-1・fi 10^-1.5・fc 0.1・L 100万 → 積 約1,999
  私たちだけ: N < 1 の回
  出会える : 文明が直径10万光年・厚さ1,000光年の円盤にばらばらにいるとして、いちばん近い文明が40光年以内の回（1,000光年以内は第6章）
  入れていないもの: 銀河の中心ほど星が多いこと・住める場所の偏り・文明が生まれた時期のずれ

使い方
  python -X utf8 sims/uchujin-long.py --numbers                 計算 → 下絵と突き合わせ → 照合 → out/uchujin-long/data.json・numbers.md
  python -X utf8 sims/uchujin-long.py --check                   data.json を読んで照合だけ
  python -X utf8 sims/uchujin-long.py --scenecheck --fake-voice 場面の照合（音声なし・長さは見積もり）
  python -X utf8 sims/uchujin-long.py --stills --fake-voice     要所の静止画と sheet_480.png（out/uchujin-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
  python -X utf8 sims/uchujin-long.py --wraps | --readings | --docs | --anchors --fake-voice
  python -X utf8 sims/uchujin-long.py --preview                 960×540 の確認用動画（AivisSpeech の音声）
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

SLUG = "uchujin-long"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "out" / SLUG
DRAFT = ROOT / "sims" / "uchujin-long.draft.py"

# ============================================================
# 0. 置いた値（下絵と同じ）
# ============================================================
N_RUN = 10_000
SEED = 20261114
DISC_D, DISC_T = 100_000.0, 1_000.0                    # 円盤の直径・厚さ（光年）
YEAR_DRAKE = 1961


def _logu(rng, lo, hi, n=N_RUN):
    return 10 ** rng.uniform(np.log10(lo), np.log10(hi), n)


def draw_values(rng):
    """下絵の draw() と同じ順番で乱数を引く"""
    R = _logu(rng, 1, 100)
    fp = _logu(rng, 0.1, 1)
    ne = _logu(rng, 0.1, 1)
    lam = 10 ** np.clip(rng.normal(0, 50, N_RUN), -300, 300)
    fl = -np.expm1(-lam * 1.0)
    fi = _logu(rng, 1e-3, 1)
    fc = _logu(rng, 1e-2, 1)
    L = _logu(rng, 1e2, 1e10)
    return dict(R=R, fp=fp, ne=ne, fl=fl, fi=fi, fc=fc, L=L)


def nearest_ly(N):
    V = np.pi * 50_000 ** 2 * 1_000
    return np.where(N >= 1, (V / np.maximum(N, 1e-300)) ** (1 / 3) * 0.55, np.inf)


# 第1章の「中央値」（理論の値。10倍ずつで見た真ん中）
THEORY = dict(R=10.0, fp=10 ** -0.5, ne=10 ** -0.5, fl=1 - math.exp(-1), fi=10 ** -1.5, fc=0.1, L=1.0e6)
TERM_NAMES = dict(R="R*（1年に生まれる星の数）", fp="fp（惑星を持つ星の割合）", ne="ne（住めそうな惑星の数）", fl="fl（生命が生まれる確率）",
                  fi="fi（知的な生命になる割合）", fc="fc（電波を出す文明になる割合）", L="L（電波を出し続ける年数）")


def _ball(r):
    return 4.0 / 3.0 * math.pi * r ** 3


def geometry():
    V = math.pi * (DISC_D / 2) ** 2 * DISC_T
    r = 1000.0
    h = DISC_T / 2
    cut = math.pi * (r * r * 2 * h - 2 * h ** 3 / 3)         # 半径1,000光年の球を、厚さ1,000光年の円盤で切った体積
    return dict(v_disc=V, v40=_ball(40.0), v1000_full=_ball(1000.0), v1000_cut=cut, r40=V / _ball(40.0), r1000=V / cut)


def compute():
    rng = np.random.default_rng(SEED)
    d = draw_values(rng)
    N = d["R"] * d["fp"] * d["ne"] * d["fl"] * d["fi"] * d["fc"] * d["L"]
    Nfl = d["R"] * d["fp"] * d["ne"] * d["fi"] * d["fc"] * d["L"]
    near, near_fl = nearest_ly(N), nearest_ly(Nfl)
    mids = {k: float(np.median(v)) for k, v in d.items()}
    N1_sample = float(np.prod(list(mids.values())))
    logs = {k: np.log10(np.maximum(v, 1e-300)) for k, v in d.items()}
    tot = sum(np.var(v) for v in logs.values())
    shares = {k: float(np.var(v) / tot) for k, v in logs.items()}
    pr = {str(q): float(np.percentile(N, q)) for q in (10, 25, 50, 75, 90)}
    th_prod = float(np.prod(list(THEORY.values())))
    ranges = dict(R=(1, 100), fp=(0.1, 1), ne=(0.1, 1), fi=(1e-3, 1), fc=(1e-2, 1), L=(1e2, 1e10))
    res = dict(
        slug=SLUG, n=N_RUN, seed=SEED, theory=THEORY, theory_prod=th_prod, sample_mids=mids, sample_prod=N1_sample,
        n_alone=int(np.sum(N < 1)), p_alone=float(np.mean(N < 1)), med=float(np.median(N)), pr=pr, ge1000=float(np.mean(N >= 1000)),
        shares=shares, ranges={k: list(v) for k, v in ranges.items()},
        fl1_alone=int(np.sum(Nfl < 1)), fl1_p_alone=float(np.mean(Nfl < 1)), fl1_med=float(np.median(Nfl)),
        n40_all=int(np.sum(near <= 40)), p40_all=float(np.mean(near <= 40)), n40_fl1=int(np.sum(near_fl <= 40)), p40_fl1=float(np.mean(near_fl <= 40)),
        n1000_all=int(np.sum(near <= 1000)), p1000_all=float(np.mean(near <= 1000)), n1000_fl1=int(np.sum(near_fl <= 1000)), p1000_fl1=float(np.mean(near_fl <= 1000)),
        fl1_p_any=float(np.mean(Nfl >= 1)),
        geo=geometry(),
        logN_all=[round(float(x), 2) for x in np.clip(np.log10(np.maximum(N, 1e-300)), -300, 30)],
        logN_fl1=[round(float(x), 2) for x in np.clip(np.log10(np.maximum(Nfl, 1e-300)), -300, 30)],
        near_all=[round(float(x), 3) if np.isfinite(x) else None for x in np.log10(np.where(np.isfinite(near), near, 1.0))],
        near_all_ok=[bool(np.isfinite(x)) for x in near],
    )
    return res


def draft_lines(res):
    """下絵の print と同じ書式で、同じ値の行を作る（下絵の出力と1行ずつ突き合わせる）"""
    rng = np.random.default_rng(SEED)
    d = draw_values(rng)
    N = d["R"] * d["fp"] * d["ne"] * d["fl"] * d["fi"] * d["fc"] * d["L"]
    Nfl = d["R"] * d["fp"] * d["ne"] * d["fi"] * d["fc"] * d["L"]
    near, near_fl = nearest_ly(N), nearest_ly(Nfl)
    mids = {k: float(np.median(v)) for k, v in d.items()}
    N1 = float(np.prod(list(mids.values())))
    out = ["幅の真ん中: " + "  ".join(f"{k}={v:.3g}" for k, v in mids.items()), f"真ん中どうしで1回かけ算: N = {N1:,.0f}",
           f"1万回の真ん中 N = {np.median(N):.3g}", f"N < 1（この銀河で、いま通信できるのは私たちだけ）: {np.mean(N < 1):.1%}",
           f"N >= 1000: {np.mean(N >= 1000):.1%}"]
    for q in (10, 25, 50, 75, 90):
        out.append(f"  {q}% 点: {np.percentile(N, q):.3g}")
    logs = {k: np.log10(np.maximum(v, 1e-300)) for k, v in d.items()}
    tot = sum(np.var(v) for v in logs.values())
    for k, v in logs.items():
        out.append(f"  {k:<3} {np.var(v)/tot:6.1%}  （5〜95%の幅 {np.percentile(d[k],5):.2g}〜{np.percentile(d[k],95):.2g}）")
    out.append(f"もし生命が必ず生まれるなら（fl=1）: N<1 {np.mean(Nfl < 1):.1%}  真ん中 {np.median(Nfl):.3g}")
    out.append(f"いちばん近い文明が40光年以内: {np.mean(near <= 40):.2%}")
    out.append(f"  1,000光年以内: {np.mean(near <= 1000):.1%}")
    out.append(f"  （fl=1 なら）40光年以内: {np.mean(near_fl <= 40):.2%}  1,000光年以内: {np.mean(near_fl <= 1000):.1%}")
    return out


# ============================================================
# 1. 台本の数字を読む（モデルの照合用）
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
        body = re.sub(r"(〔[^〕]*〕\s*)+$", "", body).strip()
        txt.append(body)
    return "\n".join(txt)


def _int(x):
    return int(math.floor(float(x) + 0.5))


def check(res):
    """照合。名前と OK/NG の一覧を返す。1つでも NG なら止める"""
    out = []

    def A(name, ok):
        out.append((name, bool(ok)))
    pc = lambda v: _int(v * 100)
    th = res["theory"]
    sh = res["shares"]
    g = res["geo"]
    # ---- 下絵と1行ずつ突き合わせる ----
    cp = subprocess.run([sys.executable, "-X", "utf8", "-W", "ignore", str(DRAFT)], capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    draft = [ln.rstrip() for ln in cp.stdout.splitlines()]
    A("下絵が最後まで走る（sims/uchujin-long.draft.py）", cp.returncode == 0 and len(draft) > 20)
    mine = draft_lines(res)
    for ln in mine:
        A(f"下絵と同じ行: {ln.strip()}", ln in draft)
    A(f"data.json の値と下絵の行が同じ元（私たちだけ {res['p_alone']:.1%}・40光年 {res['p40_all']:.2%}・fl=1 で {res['p40_fl1']:.2%}／{res['p1000_fl1']:.1%}）",
      f"N < 1（この銀河で、いま通信できるのは私たちだけ）: {res['p_alone']:.1%}" in draft and f"いちばん近い文明が40光年以内: {res['p40_all']:.2%}" in draft
      and f"  （fl=1 なら）40光年以内: {res['p40_fl1']:.2%}  1,000光年以内: {res['p1000_fl1']:.1%}" in draft)
    # ---- 第1章: 中央値（理論の値）----
    A(f"第1章の中央値: R {th['R']:g}・fp {th['fp']:.3f}（10^-0.5）・ne {th['ne']:.3f}・fl {th['fl']:.3f}（1−e^-1）・fi {th['fi']:.4f}（10^-1.5）・fc {th['fc']:g}・L {th['L']:,.0f}",
      th["R"] == 10 and abs(th["fp"] - 10 ** -0.5) < 1e-12 and abs(th["ne"] - 10 ** -0.5) < 1e-12 and abs(th["fl"] - (1 - math.exp(-1))) < 1e-12
      and abs(th["fi"] - 10 ** -1.5) < 1e-12 and th["fc"] == 0.1 and th["L"] == 1e6)
    A(f"7つの積 {res['theory_prod']:,.1f} ＝ 約1,999（声は「2,000ほど」: 100の位に丸めて 2,000）", abs(res["theory_prod"] - 1999) < 1.0 and _int(res["theory_prod"] / 100) * 100 == 2000)
    A(f"札「約3割」＝ fp {th['fp'] * 10:.2f}割・「約0.3個」＝ ne {th['ne']:.3f}個・「約6割」＝ fl {th['fl'] * 10:.2f}割・「100に3ほど」＝ fi {th['fi'] * 100:.2f}・「10に1ほど」＝ fc {th['fc'] * 10:g}",
      _int(th["fp"] * 10) == 3 and round(th["ne"], 1) == 0.3 and _int(th["fl"] * 10) == 6 and _int(th["fi"] * 100) == 3 and _int(th["fc"] * 10) == 1)
    prod_cards = 10 * 0.3 * 0.3 * 0.6 * 0.03 * 0.1 * 1e6
    A(f"丸めた札どうしをかけると {prod_cards:,.0f}（約1,700）・丸める前は {res['theory_prod']:,.0f}（台本の注記どおり）", abs(prod_cards - 1620) < 120 or abs(prod_cards - 1700) < 150)
    A(f"下絵の標本の中央値の積 {res['sample_prod']:,.0f} は動画では使わない（fl の標本の中央値 {res['sample_mids']['fl']:.2f} は ±0.6桁ゆれる）", f"真ん中どうしで1回かけ算: N = {res['sample_prod']:,.0f}" in draft)
    # ---- 第2章 ----
    A(f"私たちだけ: 100回に{pc(res['p_alone'])}回（{res['p_alone']:.1%}・{res['n_alone']:,}回）＝ 台本の52・半分を超えている", pc(res["p_alone"]) == 52 and res["p_alone"] > 0.5)
    A(f"1万回の答えの中央値 {res['med']:.3g} は1に届かない（台本「ちょうど半分のところ、つまり中央値は、1にも届きません」）", res["med"] < 1)
    A(f"小さい側の1割の点 {res['pr']['10']:.3g} ＝ 「ほぼゼロ」（1e-30 より小さい）・大きい側の1割の点 {res['pr']['90']:,.0f} ＝ 「およそ100万」（50万〜200万）",
      res["pr"]["10"] < 1e-30 and 5e5 < res["pr"]["90"] < 2e6)
    A(f"1,000以上の回は {res['ge1000']:.1%}（答えが大きく割れる）", 0.2 < res["ge1000"] < 0.4)
    # ---- 第3章 ----
    six = sum(v for k, v in sh.items() if k != "fl")
    A(f"どの値が効くか: 生命が生まれる確率 {sh['fl']:.1%} ＝ 「100のうち99」・ほかの6つの合計 {six:.1%} ＝ 「100のうち1ほど」", pc(sh["fl"]) == 99 and 0.005 < six < 0.015)
    spans = {k: math.log10(hi / lo) for k, (lo, hi) in res["ranges"].items()}
    A(f"ほかの値の幅は広くても1億倍（L が 10^{spans['L']:.0f}・ほかは {sorted(round(v) for k, v in spans.items() if k != 'L')} 桁）", spans["L"] == 8 and max(v for k, v in spans.items() if k != "L") <= 3)
    # ---- 第4章 ----
    A(f"生命が必ず生まれるなら: 私たちだけ 100回に{pc(res['fl1_p_alone'])}回（台本10）・中央値 {res['fl1_med']:,.0f} → 100の位 {_int(res['fl1_med'] / 100) * 100:,}（台本 3,500）",
      pc(res["fl1_p_alone"]) == 10 and _int(res["fl1_med"] / 100) * 100 == 3500)
    A(f"第1章の約2,000と第4章の3,500は同じ大きさ（比 {res['fl1_med'] / res['theory_prod']:.2f}・2倍以内）", 0.5 < res["fl1_med"] / res["theory_prod"] < 2.0)
    # ---- 第5章 ----
    A(f"40光年以内: 全部を幅で選ぶ 100回に{pc(res['p40_all'])}回（台本4）・生命が必ず生まれるなら {pc(res['p40_fl1'])}回（台本8）", pc(res["p40_all"]) == 4 and pc(res["p40_fl1"]) == 8)
    A(f"生命が必ず生まれるとき、どこかに文明がいる回: 100回に{pc(res['fl1_p_any'])}回（台本90）", pc(res["fl1_p_any"]) == 90)
    A(f"円盤の体積 ÷ 40光年の球 ＝ {g['r40']:,.0f}（約{g['r40'] / 1e4:,.0f}万）＝ 台本の「数千万」（1,000万〜1億の間・約2,930万）", 1e7 <= g["r40"] < 1e8 and _int(g["r40"] / 1e4) == 2930)
    A(f"円盤の体積 ÷ 半径1,000光年の球（厚さ1,000光年の円盤で切れる）＝ {g['r1000']:,.0f}（約2,700）＝ 台本の「数千」（切れない完全な球なら {g['v_disc'] / g['v1000_full']:,.0f}）", 1e3 <= g["r1000"] < 1e4 and _int(g["r1000"] / 100) * 100 == 2700)
    A("往復の年数: 40光年 × 2 ＝ 80年・1,000光年 × 2 ＝ 2,000年（台本）", 40 * 2 == 80 and 1000 * 2 == 2000)
    A(f"円盤: 直径 {DISC_D:,.0f}光年（台本「約10万光年」）・厚さ {DISC_T:,.0f}光年（「約1,000光年」）", DISC_D == 100_000 and DISC_T == 1_000)
    # ---- 第6章 ----
    A(f"1,000光年以内: 全部を幅で選ぶ 100回に{pc(res['p1000_all'])}回（台本29）・生命が必ず生まれるなら {res['p1000_fl1'] * 100:.2f} → 100回に{pc(res['p1000_fl1'])}回ほど（台本56ほど）", pc(res["p1000_all"]) == 29 and pc(res["p1000_fl1"]) == 56)
    A(f"「数千」の文明（円盤÷球 {g['r1000']:,.0f}）は生命が必ず生まれるときの中央値 {res['fl1_med']:,.0f} と同じくらい（比 {res['fl1_med'] / g['r1000']:.2f}・2倍以内）", 0.5 < res["fl1_med"] / g["r1000"] < 2.0)
    # ---- 梯子の単調 ----
    A("梯子: 私たちだけ 52 → 10（下がる）／40光年以内 4 → 8（上がる）／1,000光年以内 29 → 56（上がる）", res["p_alone"] > res["fl1_p_alone"] and res["p40_all"] < res["p40_fl1"] and res["p1000_all"] < res["p1000_fl1"])
    A("data.json の1万回: logN_all・logN_fl1・near_all は1万個", len(res["logN_all"]) == N_RUN and len(res["logN_fl1"]) == N_RUN and len(res["near_all"]) == N_RUN)
    # ---- 台本（文字）に書いてある数字が data.json と合っている ----
    nt = narration_text()
    want = [f"100回に{pc(res['p_alone'])}回でした", f"100回に{pc(res['fl1_p_alone'])}回まで", "3,500ほど", f"100回に{pc(res['p40_all'])}回でした", f"100回に{pc(res['p40_fl1'])}回です",
            f"100回に{pc(res['fl1_p_any'])}回もあります", f"100回に{pc(res['p1000_all'])}回でした", f"100回に{pc(res['p1000_fl1'])}回ほどです", "100のうち99です", "100のうち1ほど",
            "1億倍", "2,000ほど", "60年以上前", "1万回", "往復に、80年", "往復で、2,000年", "{数千万|すうせんまん}", "{数千|すうせん}",
            "10個です", "6割ほど", "100万年とします", "約10万光年", "約1,000光年", "40光年以内", "1,000光年"]
    miss = [w for w in want if w not in nt]
    A(f"台本（narration_B.md）に、data.json から出る言葉が{len(want)}個そろっている: 足りないもの {miss}", not miss)
    A(f"台本: 60年以上前 ＝ 2026 − {YEAR_DRAKE} ＝ {2026 - YEAR_DRAKE}年（本文に「{YEAR_DRAKE}年」あり）", 2026 - YEAR_DRAKE >= 60 and f"{YEAR_DRAKE}年" in nt)
    A("台本: 言わない決まり（FACTCHECK）の言葉を本文に書いていない（1,000〜1億・会議の人数・参加者名・いないと証明・今の観測値・気づいている・年にちょうど1個・UFO）",
      not any(w in nt for w in ("1,000〜1億", "12人", "セーガン", "カルヴィン", "証明した", "今の観測値", "気づいている", "ちょうど1個", "UFO", "ＵＦＯ")))
    bad = [name for name, ok in out if not ok]
    for name, ok in out:
        print(("  OK  " if ok else "  NG  ") + name)
    if bad:
        raise SystemExit(f"照合に失敗: {len(bad)}件")
    print(f"照合 {len(out)} 件 OK")
    return out


def write_numbers(res, checks):
    th, g, sh = res["theory"], res["geo"], res["shares"]
    pc = lambda v: _int(v * 100)
    rows = ["# 数字（宇宙人に出会える確率 ロング・sims/uchujin-long.py --numbers が書く。手で直さない）", "",
            f"{res['n']:,} 回・乱数の種 {res['seed']}・計算は sims/uchujin-long.draft.py と同じ（出力を1行ずつ突き合わせ済み）", "",
            "## 第1章: 中央値（理論の値・10倍ずつで見た真ん中。下絵の標本の中央値ではない）", "",
            "| 項 | 理論の値 | 札・声 | 下絵の標本の中央値（参考・動画では使わない） |", "|---|---|---|---|"]
    lab = dict(R="10個（声）", fp="約3割（札）", ne="約0.3個（札）", fl="約6割（札）", fi="100に3ほど（札）", fc="10に1ほど（札）", L="100万年（声）")
    for k in ("R", "fp", "ne", "fl", "fi", "fc", "L"):
        rows.append(f"| {TERM_NAMES[k]} | {th[k]:.6g} | {lab[k]} | {res['sample_mids'][k]:.3g} |")
    rows += ["", f"- 7つの積（理論の値）＝ **{res['theory_prod']:,.1f}** → 声は「2,000ほど」",
             f"- 丸めた札どうしをかけると 約1,700（10 × 0.3 × 0.3 × 0.6 × 0.03 × 0.1 × 100万 ＝ {10 * 0.3 * 0.3 * 0.6 * 0.03 * 0.1 * 1e6:,.0f}）。札は「約・ほど」つき",
             f"- 下絵の標本の中央値の積 ＝ {res['sample_prod']:,.0f}（台本の古い版は 2,750・8割。fl の標本の中央値は ±0.6桁ゆれる）", "",
             "## 第2章: 7つとも幅から選ぶ（1万回）", "",
             f"- 「私たちだけ」（N < 1）: **{res['n_alone']:,}回 ＝ {res['p_alone']:.1%}** → 100回に{pc(res['p_alone'])}回",
             f"- 答えの中央値 {res['med']:.3g}（1にも届かない）／小さい側の1割の点 {res['pr']['10']:.3g}（ほぼゼロ）／大きい側の1割の点 {res['pr']['90']:,.0f}（およそ100万）／1,000以上 {res['ge1000']:.1%}", "",
             "## 第3章: どの値が効くか（答えの桁のばらつきのうち）", ""]
    for k in ("R", "fp", "ne", "fi", "fc", "L", "fl"):
        rows.append(f"- {TERM_NAMES[k]}: {sh[k]:.1%}")
    rows += [f"- ほかの6つの合計: {sum(v for k, v in sh.items() if k != 'fl'):.1%}", "",
             "## 第4章: 生命が必ず生まれる（fl = 1）", "",
             f"- 「私たちだけ」: {res['fl1_alone']:,}回 ＝ {res['fl1_p_alone']:.1%} → 100回に{pc(res['fl1_p_alone'])}回／答えの中央値 {res['fl1_med']:,.0f} → 3,500ほど", "",
             "## 第5・6章: 出会える（いちばん近い文明までの距離）", "",
             "| | 全部を幅で選ぶ | 生命が必ず生まれる |", "|---|---|---|",
             f"| 40光年以内 | {res['p40_all']:.2%}（{res['n40_all']:,}回）→ 100回に{pc(res['p40_all'])}回 | {res['p40_fl1']:.2%}（{res['n40_fl1']:,}回）→ 100回に{pc(res['p40_fl1'])}回 |",
             f"| 1,000光年以内 | {res['p1000_all']:.1%}（{res['n1000_all']:,}回）→ 100回に{pc(res['p1000_all'])}回 | {res['p1000_fl1']:.2%}（{res['n1000_fl1']:,}回）→ 100回に{pc(res['p1000_fl1'])}回（ほど） |",
             f"| どこかに文明がいる（N ≥ 1） | {1 - res['p_alone']:.1%} | {res['fl1_p_any']:.1%} → 100回に{pc(res['fl1_p_any'])}回 |", "",
             "## 「数千万」「数千」（円盤の体積の比・シミュレーションの出力ではなく置いた形からの算数）", "",
             f"- 円盤（直径 {DISC_D:,.0f} 光年・厚さ {DISC_T:,.0f} 光年）の体積 ＝ {g['v_disc']:.4g} 立方光年",
             f"- 半径40光年の球 ＝ {g['v40']:.4g} → 円盤 ÷ 球 ＝ **{g['r40']:,.0f}**（約{g['r40'] / 1e4:,.0f}万）→ 声は「数千万」",
             f"- 半径1,000光年の球は円盤の厚さ（1,000光年）で上下が切れる ＝ {g['v1000_cut']:.4g}（切れない完全な球なら {g['v1000_full']:.4g}）→ 円盤 ÷ 切れた球 ＝ **{g['r1000']:,.0f}**（約2,700）→ 声は「数千」",
             f"- 参考: 切れない完全な球なら円盤 ÷ 球 ＝ {g['v_disc'] / g['v1000_full']:,.0f}", "",
             "## 照合", ""] + [f"- {'OK' if ok else 'NG'} {name}" for name, ok in checks]
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





# ####################################################################################################
# ここから下は場面（描画・音・照合・書き出し）。chikyu-long.py と同じ並び・同じ部品（見開きノート・付せん・章カード・終了画面・照合）。
# 台本: publish/uchujin-long/narration_B.md の「## 0」より後の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 部品: engine/longkit.py（LadderPanel の「＋」「↓」・枠は声の0.5秒前・OpeningTeaser・scan_frames・text_box_overlaps・visual_lag・value_spoilers・min_text_size・small）。
#   1万マスは3色（灰＝私たちだけ／青＝いる／橙＝近くにいる）にするため、longkit.GridPanel の作りをそのまま3色に広げた Grid3 を使う。
#
# 使い方
#   python -X utf8 sims/uchujin-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/uchujin-long.py --stills --fake-voice        要所の静止画と sheet_480.png（out/uchujin-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
#   python -X utf8 sims/uchujin-long.py --wraps --fake-voice         字幕の折り返しを全部表示
#   python -X utf8 sims/uchujin-long.py --readings --fake-voice      読みの確認（scene_work/readings.log）
#   python -X utf8 sims/uchujin-long.py --docs --fake-voice          文字起こし・チャプター（scene_work/）
#   python -X utf8 sims/uchujin-long.py --anchors --fake-voice       場面の合図の時刻
#   python -X utf8 sims/uchujin-long.py --preview                    960×540 の確認用動画（AivisSpeech の音声）
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
            # 行の終わりに〔 〕が何個並んでいても、全部を声と字幕から外す（画面の指示は「／」でつなぐ）
            mt = _re.search(r"(〔[^〕]*〕\s*)+$", body)
            txt = (body[:mt.start()] if mt else body).strip()
            notes_ = _re.findall(r"〔([^〕]*)〕", mt.group(0)) if mt else []
            cur["items"].append(("line", txt, "／".join(notes_)))
    return chaps


CHAPS = parse_narration()
CH_TITLES = [c["title"] for c in CHAPS]
CARD_TITLES = [t_.replace("　", "\n") for t_ in CH_TITLES]       # 章カードに出す題（全角空白で2行に）
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


VOICE_PAUSES = (0.0, 0.10)    # 2026-11-06 読点は元の声の間のまま。文の間だけ少し足す。v3 で語の途中には入らない
NUM_BREATH = 0.35                                    # 数字を言った文のあとは +0.35秒
CH_BREATH = 0.35


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and not it.id.startswith("c0_") and any(ch.isdigit() for ch in split_reading(it.text)[0]):
            extra = 0.4 if it.text.startswith("7つ全部を幅で選ぶと、1,000光年以内") else (0.9 if it.text.startswith("生命が必ず生まれるなら、100回に56回") else 0.0)   # 2026-11-07 札を読みきれるように
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH + extra, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, safe_pauses=True, **kw)





# ============================================================
# 小さな道具（chikyu-long・inoh-long・okehazama-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"                                     # いる
ORANGE = "#e0892a"                                   # 近くにいる（出会える）
GREEN = "#3f9a6a"
ALONE_C = "#8f95a6"                                  # 私たちだけ（灰）
GOLD = "#f2c14e"


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
    """tip に向かう矢じり。d は進む向きの単位ベクトル"""
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


def label(ctx, s, x, y, size, col=INK, a=1.0, align="center", bg=True):
    """白い下地つきの文字ラベル（図の上に置く）"""
    if a <= 0.003:
        return
    if bg:
        w = text_width(s, size) + 22
        h = size * 1.3
        x0 = x - w / 2 if align == "center" else (x - w + 11 if align == "right" else x - 11)
        ctx.set_source_rgba(1, 1, 1, 0.78 * a)
        rrect(ctx, x0, y - h / 2, w, h, 10)
        ctx.fill()
    text(ctx, s, x, y, size, col, align=align, alpha=a)





# ============================================================
# 準備（データ・時間割）
# ============================================================
GAP_FAST = 3.0                                   # 「（無音・早回し。…）」は4秒（4秒以内の上限）
lf.use()
RES = load()
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration

CARD_BY_N = {1: "7つの数をかけると？", 2: "決まっていない数を、\n1万回選んだら？", 3: "どの値がいちばん\n効いている？", 4: "もし、生命が必ず\n生まれるとしたら？",
             5: "では、出会える？", 6: "1,000光年まで\n待てるなら？", 7: "まとめ"}
CH_TITLES = [c["title"] for c in CHAPS]
CARD_TITLES = [CARD_BY_N.get(c["n"], c["title"]) for c in CHAPS]       # 章カードに出す題（長い題は2行に）


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
    "c0_q": (0, "どれくらいなのでしょうか"), "c0_form": (0, "60年以上前"), "c0_unk": (0, "式に入れる数の多くは"), "c0_10k": (0, "1万回計算しました"),
    "c0_first": (0, "先に言うと"), "c0_cond": (0, "条件をそろえます"), "c0_gal": (0, "銀河の中だけです"), "c0_galdef": (0, "星の集まりです"),
    "c0_civ": (0, "電波などを出している文明だけ"), "c0_civdef": (0, "文明とは"), "c0_range": (0, "これくらいから"), "c0_rangeb": (0, "この範囲を、幅と呼びます"),
    "c0_meet": (0, "「出会える」とは"), "c0_shake": (0, "大きく揺れました"),
    "c0_small": (0, "小さいままでした"), "c0_next": (0, "順番に確かめます"),
    # 1 7つの数
    "c1_this": (1, "この章では、まず"), "c1_name": (1, "式の名前は"), "c1_1961": (1, "1961年"), "c1_purpose": (1, "話し合いの出発点"), "c1_seven": (1, "式は、7つの数のかけ算です"),
    "c1_paper": (1, "2018年に発表された論文"), "c1_q1": (1, "1つ目の問い"), "c1_obs": (1, "今の観測では"), "c1_rng1": (1, "1個から100個まで"), "c1_mid1": (1, "真ん中は、10個です"), "c1_def": (1, "と呼びます"),
    "c1_q2": (1, "2つ目の問い"), "c1_q3": (1, "3つ目の問い"), "c1_mid23": (1, "この2つの中央値は"), "c1_q4": (1, "4つ目の問い"), "c1_flw": (1, "幅がとてつもなく広く"),
    "c1_fl6": (1, "中央値は、6割ほどです"), "c1_q5": (1, "5つ目の問い"), "c1_q6": (1, "6つ目の問い"), "c1_mid56": (1, "この2つも、画面の"), "c1_q7": (1, "7つ目の問い"),
    "c1_mid7": (1, "100万年とします"), "c1_mult": (1, "1年に生まれる星の数から始めて"), "c1_all": (1, "7つの中央値を、全部かけます"), "c1_ans": (1, "答えは、2,000ほどです"),
    "c1_seem": (1, "いそうに思えます"), "c1_only": (1, "7つの数は、どれも"), "c1_end": (1, "分かったことです"),
    # 2 選び直す
    "c2_prev": (2, "前の章では"), "c2_this": (2, "この章では、7つの値を"), "c2_how": (2, "選び方は、こうです"), "c2_flw": (2, "生命が生まれる確率だけは"), "c2_zero": (2, "ゼロが何十個も並ぶほどの小ささ"),
    "c2_why": (2, "なぜ、こんなに広いのか"), "c2_cnt": (2, "1に届かない回は"), "c2_a52": (2, "100回に52回でした"), "c2_half": (2, "半分を超えています"),
    "c2_sort": (2, "小さい順に並べると"), "c2_pap": (2, "この52回は"), "c2_end": (2, "分かったことです"),
    # 3 どの値が効くか
    "c3_prev": (3, "前の章では"), "c3_this": (3, "答えを大きく揺らしているのは"), "c3_share": (3, "答えのばらつきを100とします"), "c3_list": (3, "星の生まれる数、惑星を持つ星"),
    "c3_six": (3, "この6つの取り分を"), "c3_fl99": (3, "100のうち99です"), "c3_reason": (3, "理由は、幅です"), "c3_flr": (3, "生命の確率の幅は"), "c3_earth": (3, "生命が確認されている惑星は"),
    "c3_one": (3, "1つだけでは"), "c3_end": (3, "分かったことです"),
    # 4 生命が必ず
    "c4_prev": (4, "前の章では"), "c4_add": (4, "生命が必ず生まれることを足すと"), "c4_fix": (4, "1に固定します"),
    "c4_a10": (4, "100回に10回まで下がりました"), "c4_med": (4, "ちょうど半分のところ、つまり中央値は、3,500ほど"), "c4_same": (4, "第1章で、中央値どうしを"), "c4_why": (4, "いそうに思えたのは"),
    "c4_end": (4, "分かったことです"),
    # 5 出会える
    "c5_prev": (5, "前の章では"), "c5_close": (5, "どれくらい近ければ"), "c5_ly": (5, "光年とは"), "c5_f40": (5, "40光年先の文明なら"),
    "c5_life": (5, "人の一生のうちに、返事が来るかどうか"), "c5_def": (5, "40光年以内の回を"), "c5_disc": (5, "円盤の直径は"), "c5_thick": (5, "厚さは、約1,000光年です"),
    "c5_dot": (5, "ほとんど点です"), "c5_add": (5, "40光年以内を足すと"), "c5_a4": (5, "100回に4回でした"), "c5_a8": (5, "生命が必ず生まれるとしても"),
    "c5_a90": (5, "100回に90回もあります"), "c5_a8b": (5, "100回に8回だけです"), "c5_why": (5, "理由は、広さです"), "c5_many": (5, "とびきり多かった回です"), "c5_end": (5, "分かったことです"),
    # 6 1,000光年
    "c6_prev": (6, "前の章では"), "c6_here": (6, "人の一生では、間に合わない場合です"), "c6_add": (6, "1,000光年に広げると"),
    "c6_rt": (6, "往復で、2,000年かかります"), "c6_letter": (6, "2,000年前に手紙を出して"), "c6_a29": (6, "100回に29回でした"), "c6_a56": (6, "100回に56回ほど"),
    "c6_few": (6, "文明がいれば足ります"), "c6_same": (6, "3,500ほどと、同じくらいです"), "c6_end": (6, "分かったことです"),
    # 7 まとめ
    "c7_0": (7, "100回に4回から8回でした"), "c7_1": (7, "出会えるほど近くにいるとは"), "c7_2": (7, "出会える日が来ると思いますか"), "c7_3": (7, "数字は、この動画の条件"),
    "c7_ch": (7, "このチャンネルでは"), "c7_sub": (7, "チャンネル登録と高評価"),
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


# ---- 区切り（第3章と第4章のあいだ。声なし約4秒。engine/longkit.py の Eyecatch: 左ページ「ここまで」・右ページ「ここから」・亀が左から右へ歩く）----
#   台本の「（無音 4秒・区切り。…）」の行。早回しではない（早回しの数・長さの照合からは外す）。章ではない。
REST = [g_ for g_ in GAP_NOTE if "区切り" in GAP_NOTE[g_]]
T_RS0 = S(REST[0]) if len(REST) == 1 else 0.0
T_RS1 = E(REST[0]) if len(REST) == 1 else 0.0


# ---- データ ----
P_ALONE, P_FL1 = ihalf(RES["p_alone"] * 100), ihalf(RES["fl1_p_alone"] * 100)
P40, P40F = ihalf(RES["p40_all"] * 100), ihalf(RES["p40_fl1"] * 100)
P1K, P1KF = ihalf(RES["p1000_all"] * 100), ihalf(RES["p1000_fl1"] * 100)
P_ANY_F = ihalf(RES["fl1_p_any"] * 100)
N_ALONE, N_ALONE_F = RES["n_alone"], RES["fl1_alone"]
N40, N40F, N1K, N1KF = RES["n40_all"], RES["n40_fl1"], RES["n1000_all"], RES["n1000_fl1"]
TH = RES["theory"]
GEO = RES["geo"]
SHARES = RES["shares"]




# ============================================================
# 左ページの層の仕組み（chikyu-long と同じ）
# ============================================================
def clip_left(ctx):
    ctx.rectangle(45, 36, 890, 900)
    ctx.clip()


LAYERS = []
LT0 = {}
LAYER_OUT, LAYER_IN, LAYER_DELAY = 0.2, 0.25, 0.2


def layer(name, t0, t1, fn, fi=0.4, fo=0.4):
    LAYERS.append((name, t0, t1, fn, fi, fo))
    LT0[name] = t0


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


def lready(name, t_own, d):
    """層 name の中の絵（自分の出る時刻 t_own・フェード d 秒）が読めるようになる時刻（層のフェードインとのおそいほう）"""
    return max(LT0[name] + LAYER_DELAY + LAYER_IN, t_own + d)


def cue(name, kind, start, ready, key):
    return lk.Cue(name, kind, start, ready, ID[key] if key in ID else key)


# ============================================================
# 夜空（0秒目から動く）
# ============================================================
SKY = (60, 52, 805, 270)
_MILKY = None
_STARS = None
METEORS = [(1.1, 790, 80, 600, 170), (2.9, 330, 70, 150, 150), (4.6, 760, 120, 560, 215)]


def _sky_init():
    global _MILKY, _STARS
    if _MILKY is not None:
        return
    W_, H_ = 2200, 900
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_, H_)
    c = cairo.Context(surf)
    rng = np.random.default_rng(3)
    cx, cy = W_ / 2, H_ / 2
    ang = -0.30
    ca, sa = math.cos(ang), math.sin(ang)
    for k in range(46):
        u = rng.uniform(-1000, 1000)
        px, py = cx + u * ca, cy + u * sa
        g = cairo.RadialGradient(px, py, 0, px, py, 120)
        g.add_color_stop_rgba(0, 0.72, 0.78, 1.0, 0.10)
        g.add_color_stop_rgba(1, 0.72, 0.78, 1.0, 0.0)
        c.set_source(g)
        c.paint()
    for k in range(3600):
        u = rng.uniform(-1000, 1000)
        v = rng.normal(0, 42)
        x, y = cx + u * ca - v * sa, cy + u * sa + v * ca
        warm = rng.uniform() < 0.25
        c.set_source_rgba(1.0 if warm else 0.88, 0.9 if warm else 0.93, 0.75 if warm else 1.0, rng.uniform(0.12, 0.6))
        c.arc(x, y, rng.uniform(0.7, 2.3), 0, 2 * math.pi)
        c.fill()
    _MILKY = surf
    _STARS = [(rng.uniform(0, 1), rng.uniform(0.04, 0.96), rng.uniform(0.9, 2.8), rng.uniform(0, 6.28), rng.uniform(0.7, 2.4)) for _ in range(190)]


def draw_sky(ctx, t, a=1.0):
    _sky_init()
    x0, y0, w, h = SKY
    ctx.save()
    rrect(ctx, x0, y0, w, h, 22)
    ctx.clip()
    g = cairo.LinearGradient(0, y0, 0, y0 + h)
    g.add_color_stop_rgb(0, 0.04, 0.07, 0.17)
    g.add_color_stop_rgb(1, 0.12, 0.17, 0.36)
    ctx.set_source(g)
    ctx.paint_with_alpha(a)
    off = min(12.0 * t, 580.0)
    ctx.save()
    ctx.translate(x0 + w / 2 - off, y0 + h / 2)
    ctx.rotate(0.012 * min(t, 60.0))
    ctx.set_source_surface(_MILKY, -1100, -450)
    ctx.paint_with_alpha(a)
    ctx.restore()
    for sx, sy, r, ph, sp in _STARS:
        x = x0 + (sx * w - 16.0 * t * (0.5 + r / 3.0)) % w
        y = y0 + sy * h
        al = (0.5 + 0.5 * math.sin(ph + sp * t)) * 0.7 + 0.3
        ctx.set_source_rgba(1.0, 1.0, 0.93, al * a)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()
    for tm, xa, ya, xb, yb in METEORS:
        u = (t - tm) / 0.7
        if 0 <= u <= 1:
            hx, hy = xa + (xb - xa) * u, ya + (yb - ya) * u
            tx, ty = xa + (xb - xa) * max(0.0, u - 0.25), ya + (yb - ya) * max(0.0, u - 0.25)
            ctx.set_source_rgba(1, 1, 1, 0.9 * (1 - u) * a)
            ctx.set_line_width(3)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(tx, ty)
            ctx.line_to(hx, hy)
            ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, w, h, 22)
    ctx.stroke()


# ============================================================
# 天の川銀河（上から見た円盤）
# ============================================================
GCX, GCY, GR = 492.0, 500.0, 330.0
_GAL = None


def _galaxy_surf():
    global _GAL
    if _GAL is not None:
        return _GAL
    R = GR
    sz = int(2 * R + 30)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sz, sz)
    c = cairo.Context(surf)
    cx = cy = sz / 2
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, R)
    g.add_color_stop_rgb(0, 0.20, 0.22, 0.40)
    g.add_color_stop_rgb(1, 0.05, 0.07, 0.16)
    c.set_source(g)
    c.arc(cx, cy, R, 0, 2 * math.pi)
    c.fill()
    rng = np.random.default_rng(5)
    n = 4400
    r = R * (0.06 + 0.9 * np.sqrt(rng.uniform(0, 1, n)))
    arm = rng.integers(0, 2, n)
    th = 3.0 * np.log(r / (0.06 * R)) + arm * math.pi + rng.normal(0, 0.28, n)
    for i in range(n):
        tt = r[i] / R
        c.set_source_rgba(1.0 - 0.35 * tt, 0.88 - 0.05 * tt, 0.62 + 0.38 * tt, rng.uniform(0.35, 0.8))
        c.arc(cx + r[i] * math.cos(th[i]), cy + r[i] * math.sin(th[i]), rng.uniform(0.9, 2.4), 0, 2 * math.pi)
        c.fill()
    for i in range(700):
        rr, aa = abs(rng.normal(0, 0.09 * R)), rng.uniform(0, 2 * math.pi)
        c.set_source_rgba(1.0, 0.9, 0.6, rng.uniform(0.3, 0.6))
        c.arc(cx + rr * math.cos(aa), cy + rr * math.sin(aa), rng.uniform(1.0, 2.2), 0, 2 * math.pi)
        c.fill()
    for i in range(1300):
        rr, aa = R * 0.97 * math.sqrt(rng.uniform()), rng.uniform(0, 2 * math.pi)
        c.set_source_rgba(0.9, 0.93, 1.0, rng.uniform(0.1, 0.3))
        c.arc(cx + rr * math.cos(aa), cy + rr * math.sin(aa), rng.uniform(0.7, 1.4), 0, 2 * math.pi)
        c.fill()
    g2 = cairo.RadialGradient(cx, cy, 0, cx, cy, 0.16 * R)
    g2.add_color_stop_rgba(0, 1.0, 0.9, 0.55, 0.6)
    g2.add_color_stop_rgba(1, 1.0, 0.9, 0.55, 0.0)
    c.set_source(g2)
    c.arc(cx, cy, 0.16 * R, 0, 2 * math.pi)
    c.fill()
    c.set_source_rgba(0.55, 0.65, 0.95, 0.55)
    c.set_line_width(2.5)
    c.arc(cx, cy, R - 1, 0, 2 * math.pi)
    c.stroke()
    _GAL = surf
    return surf


SUN_FRAC = (0.62 * math.cos(0.6), 0.62 * math.sin(0.6))        # 銀河の中心から見た太陽の位置（半径に対する割合）


def gal_pos(cx, cy, sc):
    return cx + SUN_FRAC[0] * GR * sc, cy + SUN_FRAC[1] * GR * sc


def galaxy(ctx, cx=GCX, cy=GCY, sc=1.0, a=1.0):
    s = _galaxy_surf()
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(sc, sc)
    ctx.set_source_surface(s, -s.get_width() / 2, -s.get_height() / 2)
    ctx.paint_with_alpha(a)
    ctx.restore()


def sun_mark(ctx, x, y, a=1.0, r=7.0):
    ctx.set_source_rgba(1.0, 0.95, 0.6, 0.35 * a)
    ctx.arc(x, y, r * 2.4, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(1.0, 0.92, 0.45, a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def ring(ctx, x, y, r, col, a=1.0, w=4.0, dash=None):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_dash(dash or [])
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.stroke()
    ctx.set_dash([])


# ============================================================
# 小さな絵（7つの項）
# ============================================================
def icon_star(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb(GOLD, a))
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        ang = -math.pi / 2 + k * math.pi / 5
        (ctx.move_to if k == 0 else ctx.line_to)(cx + rr * math.cos(ang), cy + rr * math.sin(ang))
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb("#b8861a", a))
    ctx.set_line_width(3)
    ctx.stroke()


def icon_planet(ctx, cx, cy, r, a=1.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-0.4)
    ctx.set_source_rgba(*hexrgb("#d9a066", a))
    ctx.arc(0, 0, r * 0.62, 0, 2 * math.pi)
    ctx.fill()
    ctx.save()
    ctx.scale(1.0, 0.32)
    ctx.set_source_rgba(*hexrgb("#8a6a43", a))
    ctx.set_line_width(5)
    ctx.arc(0, 0, r * 1.0, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()
    ctx.restore()


def icon_ocean(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb("#3f86d6", a))
    ctx.arc(cx, cy, r * 0.8, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#5fae78", a))
    ctx.arc(cx - r * 0.2, cy - r * 0.15, r * 0.28, 0, 2 * math.pi)
    ctx.fill()
    ctx.arc(cx + r * 0.3, cy + r * 0.25, r * 0.2, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.85 * a)
    ctx.set_line_width(3)
    for dy in (0.45, 0.62):
        ctx.move_to(cx - r * 0.45, cy + r * dy)
        ctx.curve_to(cx - r * 0.2, cy + r * (dy - 0.12), cx + r * 0.1, cy + r * (dy + 0.1), cx + r * 0.4, cy + r * dy)
        ctx.stroke()


def icon_cell(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb("#bfe6c3", a))
    ctx.arc(cx, cy, r * 0.82, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb("#4d9a5e", a))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#2f6d44", a))
    ctx.arc(cx - r * 0.12, cy - r * 0.08, r * 0.28, 0, 2 * math.pi)
    ctx.fill()
    for dx, dy in ((0.42, 0.25), (0.3, -0.42), (-0.4, 0.38)):
        ctx.set_source_rgba(*hexrgb("#6fb882", a))
        ctx.arc(cx + r * dx, cy + r * dy, r * 0.1, 0, 2 * math.pi)
        ctx.fill()


def icon_brain(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb("#f4b6c4", a))
    for dx, dy, rr in ((-0.3, 0.0, 0.52), (0.3, 0.0, 0.52), (0.0, -0.3, 0.5), (0.0, 0.28, 0.46)):
        ctx.arc(cx + r * dx, cy + r * dy, r * rr, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb("#c46a85", a))
    ctx.set_line_width(3.5)
    ctx.move_to(cx, cy - r * 0.7)
    ctx.curve_to(cx - r * 0.15, cy - r * 0.2, cx + r * 0.15, cy + r * 0.2, cx, cy + r * 0.72)
    ctx.stroke()
    for dx in (-0.45, 0.45):
        ctx.move_to(cx + r * dx - r * 0.18, cy - r * 0.1)
        ctx.curve_to(cx + r * dx, cy - r * 0.35, cx + r * dx + r * 0.1, cy + r * 0.1, cx + r * dx + r * 0.2, cy - r * 0.05)
        ctx.stroke()


def icon_tower(ctx, cx, cy, r, a=1.0, t=0.0):
    ctx.set_source_rgba(*hexrgb("#55607a", a))
    ctx.set_line_width(max(3.0, r * 0.07))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(cx - r * 0.42, cy + r * 0.85)
    ctx.line_to(cx, cy - r * 0.35)
    ctx.line_to(cx + r * 0.42, cy + r * 0.85)
    ctx.stroke()
    for k in (0.15, 0.45, 0.72):
        w = 0.42 * (1 - (0.85 - k) / 1.2) * 1.0
        ctx.move_to(cx - r * 0.42 * (0.85 - k + 0.35) / 1.2, cy + r * k)
        ctx.line_to(cx + r * 0.42 * (0.85 - k + 0.35) / 1.2, cy + r * k)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.arc(cx, cy - r * 0.45, r * 0.1, 0, 2 * math.pi)
    ctx.fill()
    for i in range(3):
        ph = (t * 0.9 + i / 3.0) % 1.0
        rr = r * (0.22 + 0.7 * ph)
        ctx.set_source_rgba(*hexrgb(RED, a * (1 - ph) * 0.9))
        ctx.set_line_width(max(3.0, r * 0.05))
        ctx.arc(cx, cy - r * 0.45, rr, -math.pi * 0.85, -math.pi * 0.15)
        ctx.stroke()


def icon_glass(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb("#a8864f", a))
    ctx.set_line_width(max(4.0, r * 0.1))
    for yy in (-0.8, 0.8):
        ctx.move_to(cx - r * 0.55, cy + r * yy)
        ctx.line_to(cx + r * 0.55, cy + r * yy)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#6b7285", a))
    ctx.set_line_width(max(3.0, r * 0.07))
    ctx.move_to(cx - r * 0.45, cy - r * 0.8)
    ctx.line_to(cx - r * 0.06, cy)
    ctx.line_to(cx - r * 0.45, cy + r * 0.8)
    ctx.move_to(cx + r * 0.45, cy - r * 0.8)
    ctx.line_to(cx + r * 0.06, cy)
    ctx.line_to(cx + r * 0.45, cy + r * 0.8)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#e5b85a", a))
    ctx.move_to(cx - r * 0.36, cy - r * 0.78)
    ctx.line_to(cx + r * 0.36, cy - r * 0.78)
    ctx.line_to(cx, cy - r * 0.05)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(cx - r * 0.38, cy + r * 0.78)
    ctx.line_to(cx + r * 0.38, cy + r * 0.78)
    ctx.line_to(cx, cy + r * 0.3)
    ctx.close_path()
    ctx.fill()


def icon_earth(ctx, cx, cy, r, a=1.0):
    ctx.set_source_rgba(*hexrgb("#3f86d6", a))
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#5fae78", a))
    for dx, dy, rx, ry in ((-0.3, -0.25, 0.35, 0.28), (0.35, 0.1, 0.28, 0.4), (-0.15, 0.5, 0.25, 0.16)):
        ctx.save()
        ctx.translate(cx + r * dx, cy + r * dy)
        ctx.scale(rx * r, ry * r)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    ctx.set_source_rgba(*hexrgb("#1e4f8f", a))
    ctx.set_line_width(5)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.stroke()




# ============================================================
# 1万マス（longkit.GridPanel を3色に広げたもの）／1万回の答えの山（早回し）
# ============================================================
class Grid3:
    """100×100 のマス目。counts=色ごとのマスの数（足して1万）、colors=その色。1マス＝1回。埋まる順番はばらばら（seed）。
    n_stop を渡すと、そのマス数で埋まるのを止める（冒頭のちら見せ）。caption は複数行でよい。文字は40px以上"""

    def __init__(self, counts, colors, caption="", n=10000, side=100, seed=30, cx=492, y0=130.0, cell=4.4, t0=0.0, t1=8.0, t_cap=None,
                 t_count=None, count_text="", cap_size=42, count_size=58, cap_y=None, count_y=None, count_color=INK, power=1.7, n_stop=None):
        for nm, sz in (("cap_size", cap_size), ("count_size", count_size)):
            if sz < 40:
                raise ValueError(f"Grid3.{nm}={sz} は小さすぎる（40px 以上）")
        assert sum(counts) == n, (counts, n)
        self.counts, self.n, self.side, self.cell, self.cx, self.y0 = list(counts), n, side, cell, cx, y0
        self.px = int(round(side * cell))
        self.x0 = cx - self.px / 2
        self.t0, self.t1 = t0, t1
        self.t_cap = t0 - 0.4 if t_cap is None else t_cap
        self.t_count = t1 + 0.1 if t_count is None else t_count
        self.caption, self.count_text = caption, count_text
        self.cap_size, self.count_size = cap_size, count_size
        self.cap_y = y0 - 44 if cap_y is None else cap_y
        self.count_y = y0 + self.px + 100 if count_y is None else count_y
        self.count_color, self.power, self.n_stop = count_color, power, n_stop
        cat = np.repeat(np.arange(len(counts)), counts)
        self.cat = np.random.default_rng(seed).permutation(cat)
        c, px = cell, self.px
        self.full = np.zeros((px, px, 4), np.uint8)
        self.idx = np.full((px, px), 10 ** 9, np.int64)
        cols = [hexrgb(x) for x in colors]
        for i in range(n):
            r_, q_ = i // side, i % side
            ya, yb = int(round(r_ * c)), int(round((r_ + 1) * c)) - 1
            xa, xb = int(round(q_ * c)), int(round((q_ + 1) * c)) - 1
            col = cols[self.cat[i]]
            self.full[ya:yb, xa:xb, 0] = int(col[2] * 255)             # cairo は BGRA
            self.full[ya:yb, xa:xb, 1] = int(col[1] * 255)
            self.full[ya:yb, xa:xb, 2] = int(col[0] * 255)
            self.full[ya:yb, xa:xb, 3] = 255
            self.idx[ya:yb, xa:xb] = i
        em = hexrgb(lk.EMPTY_C)
        self.empty = np.zeros_like(self.full)
        m = self.full[..., 3] > 0
        self.empty[m] = (int(em[2] * 255), int(em[1] * 255), int(em[0] * 255), 255)
        self._buf = None

    def filled(self, t):
        top = self.n if self.n_stop is None else self.n_stop
        return int(round(top * clamp01((t - self.t0) / max(self.t1 - self.t0, 1e-6)) ** self.power))

    def draw(self, ctx, t, a=1.0):
        ac = a * lk._fade(t, self.t_cap, 0.4)
        if ac > 0.003 and self.caption:
            text(ctx, self.caption, self.cx, self.cap_y, self.cap_size, INK, alpha=ac)
        if t >= self.t0 - 0.4:
            n = self.filled(t)
            mask = (self.idx < n)[..., None]
            self._buf = np.ascontiguousarray(np.where(mask, self.full, self.empty))
            s = cairo.ImageSurface.create_for_data(memoryview(self._buf), cairo.FORMAT_ARGB32, self.px, self.px, self.px * 4)
            ctx.set_source_surface(s, self.x0, self.y0)
            ctx.paint_with_alpha(a * lk._fade(t, self.t0 - 0.4, 0.4))
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.rectangle(self.x0 - 4, self.y0 - 4, self.px + 6, self.px + 6)
            ctx.stroke()
        q = a * lk._fade(t, self.t_count, 0.4)
        if q > 0.003 and self.count_text:
            text(ctx, self.count_text, self.cx, self.count_y, self.count_size, self.count_color, alpha=q)

    def cues(self, name, line_cap=None, line_count=None):
        out = []
        if line_cap:
            out.append(lk.Cue(f"{name} 読み方の行", "frame", self.t_cap, self.t_cap + 0.4, line_cap))
        if line_count:
            out.append(lk.Cue(f"{name} 下の数の行", "value", self.t_count, self.t_count + 0.4, line_count))
        return out

    def check(self):
        probs = []
        got = [int((self.cat == k).sum()) for k in range(len(self.counts))]
        if got != self.counts:
            probs.append(f"色ごとのマス {got} ≠ {self.counts}")
        if self.side * self.side != self.n:
            probs.append(f"{self.side}×{self.side} ≠ {self.n}")
        return probs


class Race:
    """1万回の答えが積み上がる山（早回し）。x=横軸の値（数の対数・距離の対数）、marker=境目、左側 left_col・右側 right_col。
    横軸には指数を出さない（ふつうの数の目もりだけ）。frame と bars を別々に描く（枠は声の前・山は早回しのあいだ）"""

    def __init__(self, x, lo, hi, nb, marker, marker_label, left_col, right_col, ticks, caption, legend, x0=130.0, x1=880.0, by=720.0, hmax=380.0, sub=None,
                 peak_cap=None):
        self.x = np.clip(np.asarray(x, float), lo, hi - 1e-9)
        self.lo, self.hi, self.nb = float(lo), float(hi), nb
        self.edges = np.linspace(lo, hi, nb + 1)
        self.marker, self.marker_label, self.left_col, self.right_col = marker, marker_label, left_col, right_col
        self.ticks, self.caption, self.legend, self.sub = ticks, caption, legend, sub
        self.x0, self.x1, self.by, self.hmax = x0, x1, by, hmax
        full = np.histogram(self.x, bins=self.edges)[0]
        self.peak = float(peak_cap or full.max())
        self.n_full = len(self.x)

    def X(self, v):
        return self.x0 + (v - self.lo) / (self.hi - self.lo) * (self.x1 - self.x0)

    def frame(self, ctx, a=1.0):
        if a <= 0.003:
            return
        text(ctx, self.caption, 110, 72, 46, INK, align="left", alpha=a)
        line2(ctx, (self.x0 - 10, self.by), (self.x1 + 10, self.by), INK, 5, a)
        for v, s_ in self.ticks:
            line2(ctx, (self.X(v), self.by), (self.X(v), self.by + 14), INK, 4, a)
            text(ctx, s_, self.X(v), self.by + 50, 40, INK, alpha=a)
        xm = self.X(self.marker)
        line2(ctx, (xm, self.by - self.hmax - 8), (xm, self.by), RED, 5, 0.95 * a, dash=[14, 9])
        if self.marker_label:
            label(ctx, self.marker_label, min(max(xm, 190), 800), self.by - self.hmax - 44, 42, RED, a)
        if self.legend:
            text(ctx, self.legend, 492, self.by + 128, 40, INK, alpha=a)
        if self.sub:
            text(ctx, self.sub, 492, self.by + 180, 40, PENCIL_T, alpha=a, bold=False)

    def bars(self, ctx, k, a=1.0):
        if k <= 0 or a <= 0.003:
            return
        c = np.histogram(self.x[:k], bins=self.edges)[0] / self.peak
        bw = (self.x1 - self.x0) / self.nb
        for i in range(self.nb):
            hh = min(1.0, c[i]) * self.hmax
            if hh < 0.5:
                continue
            centre = (self.edges[i] + self.edges[i + 1]) / 2
            col = self.left_col if centre <= self.marker else self.right_col
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            ctx.rectangle(self.x0 + i * bw + 0.5, self.by - hh, bw - 1.0, hh)
            ctx.fill()


def ff(t, gid):
    """早回しの区間 gid で 0→1（ゆっくり始まって速くなって止まる）"""
    return ease_in_out(clamp01((t - S(gid)) / max(dur(gid), 1e-6)))


def race_draw(ctx, t, R_, gid, t_frame, n_cap=None):
    af = fade(t, t_frame, 0.5)
    f = ease_in_out(clamp01((t - S(gid)) / max(dur(gid) - 1.4, 0.5)))        # 層が終わる前に山が出そろう
    k = int(round(f * R_.n_full))
    R_.frame(ctx, af)
    R_.bars(ctx, k, af)


LN_ALL = np.array(RES["logN_all"])
LN_FL1 = np.array(RES["logN_fl1"])
NEAR_OK = np.array(RES["near_all_ok"])
NEAR_LOG = np.array([x if x is not None else 0.0 for x in RES["near_all"]])
NEAR_ONLY = NEAR_LOG[NEAR_OK]                          # 文明が1つ以上いる回だけの、いちばん近い文明までの距離（桁）

RACE2 = Race(LN_ALL, -125.0, 15.0, 56, 0.0, "", ALONE_C, BLUE, [], "1万回の答え（文明の数）", "灰＝私たちだけ　青＝いる")
RACE4 = Race(LN_FL1, -6.0, 14.0, 40, 0.0, "", ALONE_C, BLUE, [], "1万回の答え（文明の数）", "灰＝私たちだけ　青＝いる")
DIST_TICKS = [(0.0, "1"), (1.0, "10"), (2.0, "100"), (3.0, "1,000"), (4.0, "1万")]
RACE5 = Race(NEAR_ONLY, 0.0, 4.2, 21, math.log10(40), "40光年", ORANGE, BLUE, DIST_TICKS, "いちばん近い文明までの距離", "橙＝40光年以内　青＝それより遠い",
             sub="（光年・文明が1つ以上いる回だけ）")
RACE6 = Race(NEAR_ONLY, 0.0, 4.2, 21, 3.0, "1,000光年", ORANGE, BLUE, DIST_TICKS, "いちばん近い文明までの距離", "橙＝1,000光年以内　青＝それより遠い",
             sub="（光年・文明が1つ以上いる回だけ）")




# ============================================================
# 0章 左ページ: 夜空と1万マス → 天の川銀河 → 文明 → 幅 → 出会える
# ============================================================
GRID_OPEN = Grid3([N_ALONE, 10000 - N_ALONE], [ALONE_C, BLUE], caption="灰＝私たちだけ　青＝いる", cap_y=362, cap_size=42, y0=400.0, cell=4.2,
                  t0=0.0, t1=4.2, t_cap=-0.4, t_count=1e9, power=1.15, n_stop=6300, seed=40)


def L_open(ctx, t):
    draw_sky(ctx, t)
    GRID_OPEN.draw(ctx, t)


def label_top(ctx, t, t0, s="天の川銀河"):
    label(ctx, s, GCX, 105, 56, INK, fade(t, t0, 0.4))


_RC = np.random.default_rng(21)
CIV_DOTS = [(_RC.uniform(0, 2 * math.pi), GR * _RC.uniform(0.22, 0.9)) for _ in range(16)]


def civ_dots(ctx, t, t0, cx=GCX, cy=GCY, sc=1.0, a=1.0):
    for i, (ang, r) in enumerate(CIV_DOTS):
        ai = fade(t, t0 + 0.12 * i, 0.3) * a
        if ai <= 0.003:
            continue
        x, y = cx + r * sc * math.cos(ang), cy + r * sc * math.sin(ang)
        ph = (t * 0.8 + i * 0.17) % 1.0
        ring(ctx, x, y, (8 + 26 * ph) * sc, "#ff7a8a", 0.5 * (1 - ph) * ai, 3.0)
        ctx.set_source_rgba(1.0, 0.45, 0.55, ai)
        ctx.arc(x, y, 6.0 * sc, 0, 2 * math.pi)
        ctx.fill()


def L_gal(ctx, t):
    galaxy(ctx)
    label_top(ctx, t, Sk("c0_gal", 0.1))
    sx, sy = gal_pos(GCX, GCY, 1.0)
    a_s = fade(t, Sk("c0_galdef", 0.1), 0.4)
    if a_s > 0.003:
        sun_mark(ctx, sx, sy, a_s)
        arrow2(ctx, (722, 706), (sx + 12, sy + 14), INK, 4, a_s, head=14)
        label(ctx, "私たちの太陽", 770, 735, 44, INK, a_s)
    a_n = fade(t, Sk("c0_galdef", 0.55), 0.4) * out_fade(t, Sk("c0_civ", 0.0) - 0.05, 0.2)
    label(ctx, "星は 1,000億個以上", GCX, 900, 52, INK, a_n)
    civ_dots(ctx, t, Sk("c0_civ", 0.15))
    label(ctx, "いま電波を出している文明", GCX, 900, 48, "#c2394a", fade(t, Sk("c0_civ", 0.1) + 0.1, 0.4))


def L_civdef(ctx, t):
    a = fade(t, Sk("c0_civdef", 0.0), 0.4)
    text(ctx, "文明", GCX, 120, 84, INK, alpha=a)
    icon_tower(ctx, GCX, 520, 230, a, t)
    a2 = fade(t, Sk("c0_civdef", 0.2), 0.4)
    text(ctx, "宇宙に信号を出せる", GCX, 800, 56, INK, alpha=a2)
    text(ctx, "技術を持った社会", GCX, 868, 56, INK, alpha=a2)


_RR = np.random.default_rng(9)
PICKS = _RR.uniform(0.08, 0.92, 40)


def L_range(ctx, t):
    x0, x1, y0, y1 = 110.0, 880.0, 470.0, 540.0
    a = fade(t, Sk("c0_range", 0.0) - 0.2, 0.4)
    ctx.set_source_rgba(1, 1, 1, 0.75 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 10)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 10)
    ctx.stroke()
    for x_ in (x0, x1):
        line2(ctx, (x_, y0 - 28), (x_, y1 + 28), INK, 6, a)
    a1 = fade(t, Sk("c0_range", 0.3), 0.4)
    a2 = fade(t, Sk("c0_range", 0.5), 0.4)
    label(ctx, "これくらい", x0 + 80, y1 + 95, 52, INK, a1)
    label(ctx, "これくらい", x1 - 80, y1 + 95, 52, INK, a2)
    arrow2(ctx, (x0 + 40, y1 + 66), (x0 + 6, y1 + 36), INK, 4, a1, head=14)
    arrow2(ctx, (x1 - 40, y1 + 66), (x1 - 6, y1 + 36), INK, 4, a2, head=14)
    t0 = Sk("c0_range", 0.62)
    if t >= t0:
        k = int((t - t0) / 0.45)
        px = x0 + (x1 - x0) * PICKS[k % len(PICKS)]
        ai = fade(t, t0, 0.3)
        ctx.set_source_rgba(*hexrgb(RED, ai))
        ctx.arc(px, (y0 + y1) / 2, 17, 0, 2 * math.pi)
        ctx.fill()
        label(ctx, "この中から選ぶ", GCX, 740, 52, RED, ai)
    ab = fade(t, Sk("c0_rangeb", 0.05), 0.4)
    if ab > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, ab))
        ctx.set_line_width(7)
        ctx.move_to(x0, y0 - 38)
        ctx.line_to(x0, y0 - 56)
        ctx.line_to(x1, y0 - 56)
        ctx.line_to(x1, y0 - 38)
        ctx.stroke()
        text(ctx, "幅", GCX, y0 - 140, 96, RED, alpha=ab)


def L_meet(ctx, t):
    galaxy(ctx)
    label_top(ctx, t, Sk("c0_meet", 0.0) - 0.2)
    sx, sy = gal_pos(GCX, GCY, 1.0)
    sun_mark(ctx, sx, sy)
    a = fade(t, Sk("c0_meet", 0.45), 0.4)
    if a > 0.003:
        ring(ctx, sx, sy, 20, ORANGE, a, 6)
        arrow2(ctx, (700, 724), (sx + 14, sy + 26), ORANGE, 4, a, head=14)
        label(ctx, "返事が来るほど近く", 700, 760, 46, ORANGE, a)


# ============================================================
# 1章 左ページ: 黒板 → 7つの項の表
# ============================================================
def L_board(ctx, t):
    x0, y0, w, h = 80.0, 125.0, 825.0, 520.0
    a = fade(t, Sk("c1_name", 0.0) - 0.6, 0.5)
    ctx.set_source_rgba(*hexrgb("#9b7b4f", a))
    rrect(ctx, x0 - 14, y0 - 14, w + 28, h + 28, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#2f5d46", a))
    rrect(ctx, x0, y0, w, h, 8)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#e9e1c8", 0.8 * a))
    ctx.rectangle(x0 + 30, y0 + h + 14, 160, 12)
    ctx.fill()
    chalk = "#f6f2e7"
    wr(ctx, "ドレイクの式", GCX, y0 + 70, 56, chalk, Sk("c1_name", 0.15), t, align="center", alpha=a)
    wr(ctx, "N ＝ R* × fp × ne", GCX, y0 + 220, 62, chalk, Sk("c1_name", 0.5), t, cps=7.0, align="center", alpha=a)
    wr(ctx, "× fl × fi × fc × L", GCX, y0 + 330, 62, chalk, Sk("c1_name", 0.9), t, cps=7.0, align="center", alpha=a)
    label(ctx, "1961年　会議の黒板", GCX, 730, 46, INK, fade(t, Sk("c1_1961", 0.1), 0.4))
    mini_sticky(ctx, "話し合いの出発点", GCX, 830, 50, "mint", a=fade(t, Sk("c1_purpose", 0.6), 0.4), tilt=-0.01)


TERMS = [("星が生まれる数（1年）", icon_star), ("惑星を持つ星の割合", icon_planet), ("住めそうな惑星の数", icon_ocean), ("生命が生まれる確率", icon_cell),
         ("知的な生命になる割合", icon_brain), ("電波を出す割合", icon_tower), ("電波を出し続ける年数", icon_glass)]
ROW_Y = [112.0 + 120.0 * i for i in range(7)]
# (カードの文字, 色, 出る時刻, 消える時刻, 文の id)
CARDS = {
    0: [("1〜100個", INK, Sk("c1_rng1", 0.6), Sk("c1_def", 0.35), "c1_rng1"), ("1〜100個／中央値 10個", INK, Sk("c1_def", 0.75), None, "c1_def")],
    1: [("中央値 約3割", INK, Sk("c1_q2", 0.55), None, "c1_q2")],
    2: [("中央値 約0.3個", INK, Sk("c1_q3", 0.55), None, "c1_q3")],
    3: [("幅は とてつもなく広い", RED, Sk("c1_flw", 0.3), Sk("c1_fl6", 0.1), "c1_flw"), ("中央値 約6割", INK, Sk("c1_fl6", 0.4), None, "c1_fl6")],
    4: [("中央値 100に3ほど", INK, Sk("c1_q5", 0.55), None, "c1_q5")],
    5: [("中央値 10に1ほど", INK, Sk("c1_q6", 0.55), None, "c1_q6")],
    6: [("中央値 100万年", INK, Sk("c1_mid7", 0.3), None, "c1_mid7")],
}
ICON_T = [Sk("c1_q1", 0.0) - 0.3, Sk("c1_q2", 0.0) - 0.3, Sk("c1_q3", 0.0) - 0.3, Sk("c1_q4", 0.0) - 0.3, Sk("c1_q5", 0.0) - 0.3, Sk("c1_q6", 0.0) - 0.3, Sk("c1_q7", 0.0) - 0.3]


def L_table(ctx, t):
    for i, (nm, icon) in enumerate(TERMS):
        yc = ROW_Y[i]
        tr = LT0["table"] + 0.2 + 0.1 * i
        ar = fade(t, tr, 0.3)
        if ar <= 0.003:
            continue
        ctx.set_source_rgba(1, 1, 1, 0.62 * ar)
        rrect(ctx, 70, yc - 54, 835, 108, 14)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * ar))
        ctx.set_line_width(3)
        rrect(ctx, 70, yc - 54, 835, 108, 14)
        ctx.stroke()
        text(ctx, nm, 190, yc - 20, 42, INK, align="left", alpha=ar)
        ai = fade(t, ICON_T[i], 0.3) * ar
        if ai > 0.003:
            draw_icon(ctx, i, 125, yc, ai, t)
        for j, (s_, col, t_on, t_off, key) in enumerate(CARDS[i]):
            ac = fade(t, t_on, 0.25) * ar
            if t_off is not None:
                ac *= out_fade(t, t_off, 0.15)
            if ac > 0.003:
                text(ctx, s_, 190, yc + 27, 40, col, align="left", alpha=ac)


def draw_icon(ctx, i, cx, cy, a, t):
    fn = TERMS[i][1]
    if fn is icon_tower:
        fn(ctx, cx, cy, 36, a, t)
    else:
        fn(ctx, cx, cy, 36, a)


# ============================================================
# 2章 左ページ: 10倍ずつの区切り → 早回し → 1万マス → 小さい順の帯
# ============================================================
def L_pick(ctx, t):
    a = fade(t, Sk("c2_how", 0.0) - 1.1, 0.4)
    text(ctx, "星が生まれる数（1年）", GCX, 108, 50, INK, alpha=a)
    bx = [(100.0, 470.0, "1〜10個"), (515.0, 885.0, "10〜100個")]
    for k, (xa, xb, s_) in enumerate(bx):
        ctx.set_source_rgba(1, 1, 1, 0.75 * a)
        rrect(ctx, xa, 170, xb - xa, 150, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * a))
        ctx.set_line_width(3)
        rrect(ctx, xa, 170, xb - xa, 150, 12)
        ctx.stroke()
        text(ctx, s_, (xa + xb) / 2, 215, 52, INK, alpha=a)
    t0 = Sk("c2_how", 0.45)
    if t >= t0:
        kk = int((t - t0) / 0.55)
        xa, xb, _s = bx[kk % 2]
        px = xa + 40 + (xb - xa - 80) * PICKS[(kk * 3) % len(PICKS)]
        ai = fade(t, t0, 0.3)
        ctx.set_source_rgba(*hexrgb(RED, ai))
        ctx.arc(px, 280, 14, 0, 2 * math.pi)
        ctx.fill()
        label(ctx, "どちらも 同じ確率", GCX, 395, 54, RED, ai)
    # 生命が生まれる確率（けた違いの幅）
    b = fade(t, Sk("c2_flw", 0.0) - 1.0, 0.4)
    if b > 0.003:
        text(ctx, "生命が生まれる確率", GCX, 540, 50, INK, alpha=b)
        n = 18
        for i in range(n):
            xa = 100.0 + i * (785.0 / n)
            ctx.set_source_rgba(*hexrgb(BLUE, b * (0.10 + 0.80 * i / (n - 1))))
            rrect(ctx, xa + 2, 590, 785.0 / n - 4, 90, 6)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * b))
        ctx.set_line_width(3)
        rrect(ctx, 100, 590, 785, 90, 8)
        ctx.stroke()
        text(ctx, "1", 885, 735, 52, INK, align="right", alpha=b)
        bz = fade(t, Sk("c2_zero", 0.1), 0.4)
        text(ctx, "0.00000…01", 100, 735, 46, INK, align="left", alpha=bz)
        label(ctx, "けた違いに広い", GCX, 840, 60, RED, fade(t, Sk("c2_flw", 0.35), 0.4))


def L_sorted(ctx, t):
    x0, x1, y0, y1 = 100.0, 890.0, 330.0, 420.0
    a = fade(t, LT0["sorted"] + 0.2, 0.4)
    text(ctx, "1万回の答えを 小さい順に並べた帯", GCX, 150, 46, INK, alpha=a)
    xs = x0 + (x1 - x0) * RES["p_alone"]
    ctx.set_source_rgba(*hexrgb(ALONE_C, 0.95 * a))
    ctx.rectangle(x0, y0, xs - x0, y1 - y0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(BLUE, 0.92 * a))
    ctx.rectangle(xs, y0, x1 - xs, y1 - y0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * a))
    ctx.set_line_width(3)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.stroke()
    text(ctx, "私たちだけ", (x0 + xs) / 2, (y0 + y1) / 2, 44, "#ffffff", alpha=a)
    text(ctx, "いる", (xs + x1) / 2, (y0 + y1) / 2, 44, "#ffffff", alpha=a)
    text(ctx, "小さい", x0, y1 + 50, 44, PENCIL_T, align="left", alpha=a)
    text(ctx, "大きい", x1, y1 + 50, 44, PENCIL_T, align="right", alpha=a)
    xm = (x0 + x1) / 2
    am = fade(t, Sk("c2_sort", 0.2), 0.4)
    if am > 0.003:
        line2(ctx, (xm, y0 - 24), (xm, y1 + 24), RED, 6, am)
        label(ctx, "ちょうど半分", xm, 262, 50, RED, am)
        label(ctx, "1にも届かない", xm, 500, 48, RED, fade(t, Sk("c2_sort", 0.55), 0.4))


# ============================================================
# 3章 左ページ: 100を分け合う → 幅の広さ → 地球1つ
# ============================================================
def L_share(ctx, t):
    a = fade(t, LT0["share"] + 0.2, 0.4)
    text(ctx, "答えのばらつき 100", GCX, 90, 56, INK, alpha=a)
    cs, g = 56.0, 4.0
    gx0, gy0 = GCX - (10 * cs + 9 * g) / 2, 140.0
    tf = Sk("c3_fl99", 0.45)
    ts = Sk("c3_six", 0.3)
    for k in range(100):
        r_, c_ = k // 10, k % 10
        x, y = gx0 + c_ * (cs + g), gy0 + r_ * (cs + g)
        if k == 99:
            col, al = ORANGE, fade(t, ts, 0.3)
        else:
            u = clamp01((t - tf - 0.012 * k) / 0.2)
            col, al = BLUE, u
        ctx.set_source_rgba(1, 1, 1, 0.7 * a)
        rrect(ctx, x, y, cs, cs, 5)
        ctx.fill()
        if al > 0.003:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * al * a))
            rrect(ctx, x, y, cs, cs, 5)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(2)
        rrect(ctx, x, y, cs, cs, 5)
        ctx.stroke()
    label(ctx, "ほかの6つ 合わせて 1ほど", GCX, 800, 48, ORANGE, fade(t, Sk("c3_six", 0.3), 0.4))
    label(ctx, "生命が生まれる確率 99", GCX, 870, 52, BLUE, fade(t, Sk("c3_fl99", 0.15), 0.4))


WIDTH_ROWS = [("星の生まれる数", 2, "100倍", "R"), ("惑星を持つ星の割合", 1, "10倍", "fp"), ("住めそうな惑星の数", 1, "10倍", "ne"),
              ("知的になる割合", 3, "1,000倍", "fi"), ("電波を出す割合", 2, "100倍", "fc"), ("文明が続く年数", 8, "1億倍", "L")]
W_Y = [130.0 + 118.0 * i for i in range(7)]
W_UNIT = 50.0                                          # 1桁（10倍）あたりの長さ


def L_widths(ctx, t):
    a = fade(t, LT0["widths"] + 0.2, 0.4)
    text(ctx, "幅の広さ（何倍から何倍まで）", GCX, 62, 46, INK, alpha=a)
    for i, (nm, orders, txt, key) in enumerate(WIDTH_ROWS):
        y = W_Y[i]
        text(ctx, nm, 70, y, 42, INK, align="left", alpha=a)
        tb = Sk("c3_reason", 0.25) + 0.3 * i
        u = ease_out(clamp01((t - tb) / 0.7))
        ctx.set_source_rgba(1, 1, 1, 0.7 * a)
        rrect(ctx, 70, y + 29, 404, 34, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(2)
        rrect(ctx, 70, y + 29, 404, 34, 6)
        ctx.stroke()
        if u > 0.003:
            ctx.set_source_rgba(*hexrgb(BLUE, 0.92 * a))
            rrect(ctx, 70, y + 29, max(4.0, W_UNIT * orders * u), 34, 6)
            ctx.fill()
            if u > 0.6:
                text(ctx, txt, 70 + W_UNIT * orders + 14, y + 46, 44, BLUE, align="left", alpha=a * clamp01((u - 0.6) / 0.3))
    y = W_Y[6]
    text(ctx, "生命が生まれる確率", 70, y, 42, INK, align="left", alpha=a)
    ctx.set_source_rgba(1, 1, 1, 0.7 * a)
    rrect(ctx, 70, y + 29, 800, 34, 6)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(2)
    rrect(ctx, 70, y + 29, 800, 34, 6)
    ctx.stroke()
    tf = Sk("c3_flr", 0.25)
    u = ease_out(clamp01((t - tf) / 1.0))
    if u > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, 0.92 * a))
        rrect(ctx, 70, y + 29, 800 * u, 34, 6)
        ctx.fill()
        if u > 0.9:
            arrowhead(ctx, (888, y + 46), (1, 0), RED, 24, a, 6)
            text(ctx, "ゼロが何十個も並ぶ", 880, y - 4, 46, RED, align="right", alpha=a * clamp01((u - 0.9) / 0.1))


def L_earth1(ctx, t):
    a = fade(t, Sk("c3_earth", 0.0) + 0.1, 0.5)
    icon_earth(ctx, GCX, 330, 125, a)
    label(ctx, "生命が確認された惑星は 地球だけ", GCX, 520, 46, INK, a)
    a1 = fade(t, Sk("c3_one", 0.15), 0.4)
    label(ctx, "生まれやすい？", GCX, 640, 52, BLUE, a1)
    label(ctx, "奇跡のような偶然？", GCX, 730, 52, ORANGE, fade(t, Sk("c3_one", 0.4), 0.4))
    label(ctx, "1つだけでは 見分けられない", GCX, 840, 54, RED, fade(t, Sk("c3_one", 0.7), 0.4))


# ============================================================
# 4章 左ページ: 生命だけ1に固定
# ============================================================
FIX_NAMES = ["星が生まれる数", "惑星を持つ星の割合", "住めそうな惑星の数", "生命が生まれる確率", "知的な生命になる割合", "電波を出す割合", "電波を出し続ける年数"]
FIX_Y = [130.0 + 110.0 * i for i in range(7)]


def L_fix(ctx, t):
    a = fade(t, LT0["fix"] + 0.2, 0.4)
    text(ctx, "7つの値", GCX, 62, 46, INK, alpha=a)
    for i, nm in enumerate(FIX_NAMES):
        y = FIX_Y[i]
        hl = i == 3
        ctx.set_source_rgba(*hexrgb("#fff0a0" if hl else "#ffffff", (0.9 if hl else 0.62) * a))
        rrect(ctx, 70, y - 44, 835, 88, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * a))
        ctx.set_line_width(3)
        rrect(ctx, 70, y - 44, 835, 88, 12)
        ctx.stroke()
        text(ctx, nm, 100, y, 44, INK, align="left", alpha=a)
        if hl:
            t_sw = Sk("c4_fix", 0.2)
            text(ctx, "幅で選ぶ", 880, y, 44, PENCIL_T, align="right", alpha=a * out_fade(t, t_sw, 0.15))
            text(ctx, "1 に固定", 880, y, 52, RED, align="right", alpha=a * fade(t, t_sw + 0.3, 0.25))
        else:
            text(ctx, "幅で選ぶ", 880, y, 44, PENCIL_T, align="right", alpha=a)


# ============================================================
# 5・6章 左ページ: 往復・円盤・距離の円・手紙
# ============================================================
def L_ly(ctx, t):
    ex, sx_, y = 190.0, 760.0, 430.0
    a = fade(t, LT0["ly"] + 0.2, 0.4)
    icon_earth(ctx, ex, y, 40, a)
    ctx.set_source_rgba(1, 0.95, 0.6, 0.35 * a)
    ctx.arc(sx_, y, 40, 0, 2 * math.pi)
    ctx.fill()
    icon_star(ctx, sx_, y, 34, a)
    line2(ctx, (ex + 56, y), (sx_ - 56, y), PENCIL_T, 4, 0.8 * a, dash=[12, 9])
    text(ctx, "私たち", ex, 490, 44, INK, alpha=a)
    text(ctx, "40光年先の文明", sx_ - 10, 490, 42, INK, alpha=a)
    ar = fade(t, Sk("c5_f40", 0.0) - 0.2, 0.4)
    if ar > 0.003:
        arrow2(ctx, (ex + 60, 340), (sx_ - 60, 340), BLUE, 7, ar, head=22)
        label(ctx, "信号 40年", GCX, 275, 48, BLUE, ar)
        ar2 = fade(t, Sk("c5_f40", 0.3), 0.4)
        arrow2(ctx, (sx_ - 60, 530), (ex + 60, 530), ORANGE, 7, ar2, head=22)
        label(ctx, "返事 40年", GCX, 595, 48, ORANGE, ar2)
        label(ctx, "往復 80年", GCX, 675, 84, RED, fade(t, Sk("c5_f40", 0.6), 0.4))
    al = fade(t, Sk("c5_life", 0.1), 0.4)
    if al > 0.003:
        label(ctx, "人の一生くらい", GCX, 790, 52, GREEN, al)
        arrow2(ctx, (130, 842), (860, 842), GREEN, 7, al, both=True, head=20)
        text(ctx, "今", 130, 895, 44, INK, align="left", alpha=al)
        text(ctx, "80年後", 860, 895, 44, INK, align="right", alpha=al)


def L_disc(ctx, t):
    cx, cy, sc = GCX, 360.0, 200.0 / GR
    a = fade(t, Sk("c5_disc", 0.0) - 0.3, 0.5)
    galaxy(ctx, cx, cy, sc, a)
    ad = fade(t, Sk("c5_disc", 0.45), 0.4)
    if ad > 0.003:
        arrow2(ctx, (cx - 200, 600), (cx + 200, 600), INK, 5, ad, both=True, head=18)
        label(ctx, "直径 約10万光年", GCX, 658, 48, INK, ad)
    at = fade(t, Sk("c5_thick", 0.1), 0.4)
    if at > 0.003:
        ctx.set_source_rgba(*hexrgb("#44507c", at))
        rrect(ctx, cx - 200, 752, 400, 14, 7)
        ctx.fill()
        arrow2(ctx, (GCX, 806), (GCX, 774), INK, 4, at, head=14)
        label(ctx, "厚さ 約1,000光年", GCX, 840, 48, INK, at)
        text(ctx, "※ 厚さと円は大きく描いてあります", GCX, 900, 40, PENCIL_T, alpha=at, bold=False)
    ac = fade(t, Sk("c5_dot", 0.1), 0.4)
    if ac > 0.003:
        sx, sy = gal_pos(cx, cy, sc)
        sun_mark(ctx, sx, sy, ac, 4.0)
        ring(ctx, sx, sy, 10, ORANGE, ac, 4)
        arrow2(ctx, (752, 450), (sx + 14, sy + 8), ORANGE, 4, ac, head=12)
        label(ctx, "40光年", 790, 470, 46, ORANGE, ac)


def L_galdots(ctx, t, key, r_circ, big1, big2, circ_label, a_ex=1.0):
    cx, cy, sc = GCX, 400.0, 0.78
    a = fade(t, Sk(key, 0.0) - 0.75, 0.5)
    galaxy(ctx, cx, cy, sc, a)
    sx, sy = gal_pos(cx, cy, sc)
    rr = np.random.default_rng(13)
    for i in range(520):
        rad, ang = GR * sc * 0.95 * math.sqrt(rr.uniform()), rr.uniform(0, 2 * math.pi)
        x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
        if math.hypot(x - sx, y - sy) < r_circ + 3:
            continue
        ctx.set_source_rgba(1.0, 0.55, 0.6, 0.85 * a * fade(t, Sk(key, 0.1), 0.6))
        ctx.arc(x, y, 2.2, 0, 2 * math.pi)
        ctx.fill()
    ac = fade(t, Sk(key, 0.25), 0.4)
    if ac > 0.003:
        ring(ctx, sx, sy, r_circ, ORANGE, ac, 5)
        ctx.set_source_rgba(*hexrgb("#ff3b4e", ac))
        ctx.arc(sx - 2, sy - 1, 4.0, 0, 2 * math.pi)
        ctx.fill()
        arrow2(ctx, (762, 676), (sx + r_circ * 0.7 + 4, sy + r_circ * 0.7 + 6), ORANGE, 4, ac, head=12)
        label(ctx, circ_label, 770, 700, 44, ORANGE, ac)
    label(ctx, big1, GCX, 790, 50, INK, fade(t, Sk(key, 0.35), 0.4))
    label(ctx, big2, GCX, 868, 58, RED, fade(t, Sk(key, 0.6), 0.4))


def L_why5(ctx, t):
    L_galdots(ctx, t, "c5_why", 14, "円の中に 平均して1つ入るには", "銀河全体で 数千万の文明", "40光年")


def L_why6(ctx, t):
    L_galdots(ctx, t, "c6_few", 40, "円の中に 平均して1つ入るには", "銀河全体で 数千の文明", "1,000光年")


def L_circ(ctx, t):
    """天の川の円盤に、40光年と1,000光年の円"""
    cx, cy, sc = GCX, 420.0, 0.8
    a = fade(t, Sk("c6_add", 0.0) - 0.75, 0.5)
    galaxy(ctx, cx, cy, sc, a)
    sx, sy = gal_pos(cx, cy, sc)
    sun_mark(ctx, sx, sy, a, 5.0)
    ring(ctx, sx, sy, 10, ORANGE, a, 4)
    ac = fade(t, Sk("c6_add", 0.3), 0.4)
    ring(ctx, sx, sy, 44, BLUE, ac, 5)
    label(ctx, "天の川銀河", GCX, 105, 56, INK, a)
    arrow2(ctx, (770, 712), (sx + 30, sy + 40), BLUE, 4, ac, head=12)
    label(ctx, "1,000光年", 780, 740, 46, BLUE, ac)
    arrow2(ctx, (230, 712), (sx - 10, sy + 12), ORANGE, 4, a, head=12)
    label(ctx, "40光年", 200, 740, 46, ORANGE, a)
    text(ctx, "※ 円は大きく描いてあります", GCX, 905, 40, PENCIL_T, alpha=a, bold=False)


def L_letter(ctx, t):
    a = fade(t, Sk("c6_letter", 0.0) - 0.6, 0.5)
    y = 430.0
    arrow2(ctx, (200, y), (810, y), GREEN, 8, a, head=24)
    for x_, nm in ((200.0, "2,000年前"), (810.0, "今日")):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(x_, y, 14, 0, 2 * math.pi)
        ctx.fill()
        text(ctx, nm, x_, y + 70, 52, INK, alpha=a)
    ae = fade(t, Sk("c6_letter", 0.15), 0.4)
    label(ctx, "手紙を出す", 250, 300, 50, BLUE, ae)
    label(ctx, "返事が来る", 750, 300, 50, ORANGE, fade(t, Sk("c6_letter", 0.55), 0.4))
    label(ctx, "往復 2,000年", GCX, 640, 84, RED, fade(t, Sk("c6_rt", 0.1), 0.4))


def L_summ(ctx, t):
    cx, cy, sc = GCX, 360.0, 0.7
    a = fade(t, S("ch7") + 0.4, 0.5)
    galaxy(ctx, cx, cy, sc, a)
    sx, sy = gal_pos(cx, cy, sc)
    sun_mark(ctx, sx, sy, a, 5.0)
    ring(ctx, sx, sy, 9, ORANGE, a, 4)
    ring(ctx, sx, sy, 36, BLUE, a, 4)
    label(ctx, "小さい円 ＝ 40光年（往復80年）", GCX, 655, 44, ORANGE, a)
    label(ctx, "大きい円 ＝ 1,000光年（往復2,000年）", GCX, 715, 44, BLUE, a)
    a4 = fade(t, Sk("c7_2", 0.05), 0.4) * out_fade(t, T_ES - 0.1, 0.3)
    mini_sticky(ctx, "あなたは、宇宙人に出会える日が\n来ると思いますか？", GCX, 845, 44, "yellow", a=a4, tilt=-0.01)




# ============================================================
# 1万マス・層の時刻表（左ページ）
# ============================================================
T_ES = Sk("c7_3", 0.0) - 0.3            # 終了画面の始まり（注意書きの文の頭の少し前から最後の約15秒）


def _g(counts, colors, cap, line, cap_y, y0, count_text, count_color, seed, cell=4.4, count_y=None):
    t0 = Sk(line, 0.15)
    return Grid3(counts, colors, caption=cap, t_cap=Sk(line, 0.0) - 1.05, t0=t0, t1=t0 + 2.0, t_count=Sk(line, 0.55), count_text=count_text,
                 count_color=count_color, seed=seed, cap_y=cap_y, y0=y0, cell=cell, count_y=count_y)


GRID2 = _g([N_ALONE, 10000 - N_ALONE], [ALONE_C, BLUE], "灰＝私たちだけ　青＝いる　1マス＝1回", "c2_a52", 86, 130.0, f"1万回のうち 灰 {N_ALONE:,}回", INK, 31)
GRID4 = _g([N_ALONE_F, 10000 - N_ALONE_F], [ALONE_C, BLUE], "灰＝私たちだけ　青＝いる　1マス＝1回", "c4_a10", 86, 130.0, f"1万回のうち 灰 {N_ALONE_F:,}回", INK, 32)
CAP5 = "灰＝私たちだけ　青＝いるが遠い\n橙＝40光年以内"
CAP6 = "灰＝私たちだけ　青＝いるが遠い\n橙＝1,000光年以内"
GRID5A = _g([N_ALONE, 10000 - N_ALONE - N40, N40], [ALONE_C, BLUE, ORANGE], CAP5, "c5_a4", 104, 180.0, f"1万回のうち 橙 {N40:,}回", ORANGE, 33, count_y=720.0)
GRID5B = _g([N_ALONE_F, 10000 - N_ALONE_F - N40F, N40F], [ALONE_C, BLUE, ORANGE], CAP5, "c5_a8", 104, 180.0, f"1万回のうち 橙 {N40F:,}回", ORANGE, 34, count_y=720.0)
GRID6A = _g([N_ALONE, 10000 - N_ALONE - N1K, N1K], [ALONE_C, BLUE, ORANGE], CAP6, "c6_a29", 104, 180.0, f"1万回のうち 橙 {N1K:,}回", ORANGE, 35, count_y=720.0)
GRID6B = _g([N_ALONE_F, 10000 - N_ALONE_F - N1KF, N1KF], [ALONE_C, BLUE, ORANGE], CAP6, "c6_a56", 104, 180.0, f"1万回のうち 橙 {N1KF:,}回", ORANGE, 36, count_y=720.0)

layer("open", 0.0, Sk("c0_gal") - 1.3, L_open, fi=0.0)
layer("gal", Sk("c0_gal") - 1.3, Sk("c0_civdef") - 1.3, L_gal)
layer("civdef", Sk("c0_civdef") - 1.3, Sk("c0_range") - 1.3, L_civdef)
layer("range", Sk("c0_range") - 1.3, Sk("c0_meet") - 1.3, L_range)
layer("meet", Sk("c0_meet") - 1.3, Sk("c1_name") - 0.9, L_meet)
layer("board", Sk("c1_name") - 0.9, Sk("c1_seven") - 1.9, L_board)
layer("table", Sk("c1_seven") - 1.9, Sk("c2_how") - 1.8, L_table)
layer("pick", Sk("c2_how") - 1.8, S("g2_1") - 1.4, L_pick)
layer("race2", S("g2_1") - 1.4, Sk("c2_a52") - 1.2, lambda ctx, t: race_draw(ctx, t, RACE2, "g2_1", LT0["race2"] + 0.2))
layer("grid2", Sk("c2_a52") - 1.2, Sk("c2_sort") - 1.3, lambda ctx, t: GRID2.draw(ctx, t))
layer("sorted", Sk("c2_sort") - 1.3, Sk("c3_share") - 1.3, L_sorted)
layer("share", Sk("c3_share") - 1.3, Sk("c3_reason") - 1.3, L_share)
layer("widths", Sk("c3_reason") - 1.3, Sk("c3_earth") - 1.0, L_widths)
layer("earth1", Sk("c3_earth") - 1.0, Sk("c4_fix") - 1.9, L_earth1)
layer("fix", Sk("c4_fix") - 1.9, S("g4_1") - 1.4, L_fix)
layer("race4", S("g4_1") - 1.4, Sk("c4_a10") - 1.2, lambda ctx, t: race_draw(ctx, t, RACE4, "g4_1", LT0["race4"] + 0.2))
layer("grid4", Sk("c4_a10") - 1.2, Sk("c5_ly") - 1.3, lambda ctx, t: GRID4.draw(ctx, t))
layer("ly", Sk("c5_ly") - 1.3, Sk("c5_disc") - 1.3, L_ly)
layer("disc", Sk("c5_disc") - 1.3, S("g5_1") - 1.4, L_disc)
layer("race5", S("g5_1") - 1.4, Sk("c5_a4") - 1.2, lambda ctx, t: race_draw(ctx, t, RACE5, "g5_1", LT0["race5"] + 0.2))
layer("grid5a", Sk("c5_a4") - 1.2, Sk("c5_a8") - 1.3, lambda ctx, t: GRID5A.draw(ctx, t))
layer("grid5b", Sk("c5_a8") - 1.2, Sk("c5_why") - 0.8, lambda ctx, t: GRID5B.draw(ctx, t))
layer("why5", Sk("c5_why") - 0.8, Sk("c6_add") - 0.8, L_why5)
layer("circ", Sk("c6_add") - 0.8, Sk("c6_rt") - 0.8, L_circ)
layer("letter", Sk("c6_rt") - 0.8, S("g6_1") - 1.4, L_letter)
layer("race6", S("g6_1") - 1.4, Sk("c6_a29") - 1.2, lambda ctx, t: race_draw(ctx, t, RACE6, "g6_1", LT0["race6"] + 0.2))
layer("grid6a", Sk("c6_a29") - 1.2, Sk("c6_a56") - 1.3, lambda ctx, t: GRID6A.draw(ctx, t))
layer("grid6b", Sk("c6_a56") - 1.2, Sk("c6_few") - 0.8, lambda ctx, t: GRID6B.draw(ctx, t))
layer("why6", Sk("c6_few") - 0.8, S("ch7") - 0.25, L_why6)          # 章カード「まとめ」が出る前に消す
layer("summ", S("ch7") + 0.1, T_ES + 0.8, L_summ)


# ============================================================
# 右ページ
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


QLINES = ["宇宙人に出会える", "確率は？"]
QTXT = "".join(QLINES)                                   # 題名・サムネと同じ言葉
T_SHRINK = Sk("c0_cond", 0.0) - 0.05
T_BOX_OUT = Sk("c0_shake", 0.0) - 1.95
teaser = lk.OpeningTeaser(QLINES, left=None, thumb_text=QTXT, q_pos=(1050, 270), q_size=96, box=(1030, 700, 1830, 844), box_title="私たちだけ", unit="%",
                          peak=0.0, hide_at=None, t_out=T_BOX_OUT, title_size=56, val_size=76, color=ALONE_C)

COND_ROWS = [("天の川銀河の中だけ", "c0_gal", 0.1, 300), ("いま電波を出している文明だけ", "c0_civ", 0.1, 352), ("決まっていない数は 幅の中から", "c0_range", 0.1, 404),
             ("「出会える」＝ 人の一生のうちに\n返事が来るほど近く", "c0_meet", 0.1, 475)]


def cond_sticky(ctx, t):
    t0 = T_SHRINK + 0.25
    a = fade(t, t0, 0.4)
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(RX - 12 + 395, 205 + 167)
    ctx.rotate(-0.006)
    ctx.translate(-(RX - 12 + 395), -(205 + 167))
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, RX - 12 + 5, 205 + 8, 790, 335, 6)
    ctx.fill()
    fill(ctx, hexrgb(STICKY["yellow"], a))
    rrect(ctx, RX - 12, 205, 790, 335, 6)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(RX - 12, 205, 790, 12)
    ctx.fill()
    text(ctx, "条件", RX + 20, 245, 44, RED, align="left", alpha=a)
    for s_, key, fr, yy in COND_ROWS:
        wr(ctx, s_, RX + 20, yy, 42, INK, Sk(key, fr), t, align="left", alpha=a)
    ctx.restore()


def R_ch0(ctx, t):
    big = out_fade(t, T_SHRINK - 0.2, 0.2)
    teaser.draw_question(ctx, t, big)
    small = fade(t, T_SHRINK + 0.05, 0.2)
    if small > 0.003:
        text(ctx, QTXT, RX, 100, 56, INK, align="left", alpha=small)
    teaser.draw_box(ctx, t)
    a_f = fade(t, Sk("c0_form", 0.35), 0.5) * out_fade(t, Sk("c0_10k", 0.0) + 0.5, 0.3) * 0.5
    text(ctx, "R* × fp × ne × fl × fi × fc × L", RX, 500, 44, INK, align="left", alpha=a_f)
    a_k = fade(t, Sk("c0_10k", 0.35), 0.3) * out_fade(t, Sk("c0_first", 0.0) + 0.1, 0.3)
    sticky(ctx, "1万回", RX + 135, 500, 64, "pink", fg=RED, a=a_k, tilt=-0.02)
    a_q = fade(t, Sk("c0_first", 0.35), 0.3) * out_fade(t, T_SHRINK - 0.25, 0.2)
    mini_sticky(ctx, "いる？", RX, 500, 64, "yellow", a=a_q, align="left", tilt=-0.015)
    mini_sticky(ctx, "出会える？", RX + 300, 500, 64, "pink", fg=RED, a=fade(t, Sk("c0_first", 0.6), 0.3) * out_fade(t, T_SHRINK - 0.25, 0.2), align="left", tilt=0.015)
    cond_sticky(ctx, t)


def R_ch1(ctx, t):
    a = fade(t, Sk("c1_name", 0.1), 0.4)
    text(ctx, "ドレイクの式", RX, 150, 84, INK, align="left", alpha=a)
    stk(ctx, t, "c1_1961", "天文学者\nフランク・ドレイク", 285, "mint", size=52, tilt=-0.01, off=0.3, until=Sk("c1_paper", 0.0) - 0.1)
    stk(ctx, t, "c1_paper", "2018年の論文と同じ幅", 285, "yellow", size=48, tilt=-0.012, off=0.2)
    stk(ctx, t, "c1_all", "10個 × 約3割 × 約0.3個\n× 約6割 × 100に3ほど\n× 10に1ほど × 100万年", 480, "mint", size=44, tilt=0.008, off=0.2)
    # 答えの箱（枠は「7つの中央値を、全部かけます」の頭から・数字は声に合わせる）
    af = fade(t, T1_BOX, 0.4)
    if af > 0.003:
        ctx.set_source_rgba(1, 1, 1, 0.6 * af)
        rrect(ctx, 1000, 660, 860, 210, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * af))
        ctx.set_line_width(3)
        rrect(ctx, 1000, 660, 860, 210, 16)
        ctx.stroke()
        text(ctx, "いま電波を出している文明", 1032, 712, 44, INK, align="left", alpha=af)
        text(ctx, "2,000ほど", 1830, 804, 92, RED, align="right", alpha=af * fade(t, T1_ANS, 0.35))
        text(ctx, "？", 1830, 804, 92, RED, align="right", alpha=af * out_fade(t, T1_ANS - 0.05, 0.1) * 0.9)


T1_BOX = Sk("c1_this", 0.6)
T1_ANS = Sk("c1_ans", 0.45)


def R_ch2(ctx, t):
    stk(ctx, t, "c2_flw", "生命の幅は、けた違い", 150, "pink", fg=RED, size=50, tilt=-0.012, off=0.3)
    stk(ctx, t, "c2_cnt", "1に届かない ＝ 私たちだけ", 270, "yellow", size=48, tilt=0.01, off=0.3)
    stk(ctx, t, "c2_pap", "2018年の論文とほぼ同じ", 390, "mint", size=48, tilt=-0.01, off=0.3)


def R_ch3(ctx, t):
    pass


def R_ch4(ctx, t):
    stk(ctx, t, "c4_fix", "生命が生まれる確率 ＝ 1", 135, "pink", fg=RED, size=52, tilt=-0.012, off=0.3, until=Sk("c4_why", 0.0) - 0.1)
    stk(ctx, t, "c4_why", "第1章は 生命が約6割", 135, "mint", size=52, tilt=0.01, off=0.3)


def R_ch5(ctx, t):
    stk(ctx, t, "c5_ly", "1光年 ＝ 光が1年で進む距離", 140, "yellow", size=46, tilt=-0.012, off=0.3)
    stk(ctx, t, "c5_def", "出会える ＝ 40光年以内", 240, "pink", fg=RED, size=50, tilt=0.01, off=0.3)


def R_ch6(ctx, t):
    stk(ctx, t, "c6_rt", "往復 2,000年", 135, "pink", fg=RED, size=52, tilt=-0.012, off=0.3)
    stk(ctx, t, "c6_few", "半径1,000光年に1つ入るには\n銀河全体で 数千の文明", 270, "yellow", size=44, tilt=0.008, off=0.3, until=Sk("c6_same", 0.0) - 0.1)
    stk(ctx, t, "c6_same", "生命が必ず生まれるときの\n中央値 3,500ほどと同じくらい", 270, "mint", size=44, tilt=-0.008, off=0.3)


def R_ch7(ctx, t):
    pass


R_CH = [R_ch0, R_ch1, R_ch2, R_ch3, R_ch4, R_ch5, R_ch6, R_ch7]


def draw_right(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    if idx >= len(R_CH):
        return
    # 前の章の付せんは、次の章の始まり（章カードが出る）の前に消す（章カードと重ならないように。2026-10-25）
    nxt = S(f"ch{idx + 1}") if idx + 1 < len(R_CH) else None
    if nxt is not None and t > nxt - 0.3:
        grp(ctx, clamp01((nxt - t) / 0.3), R_CH[idx], t)
        return
    R_CH[idx](ctx, t)


# ============================================================
# 梯子・棒の枠（右ページ）
# ============================================================
T_A = Sk("c0_shake") - 1.3
A_ROWS = [lk.Row("全部を幅で選ぶ", RES["p_alone"], t_label=T_A + 0.1, t_value=Sk("c2_a52", 0.55), color=ALONE_C, line=ID["c2_a52"], text=f"{P_ALONE}%"),
          lk.Row("生命は必ず生まれる", RES["fl1_p_alone"], t_label=Sk("c4_add", 0.0) - 1.2, t_value=Sk("c4_a10", 0.55), color=ALONE_C, line=ID["c4_a10"], text=f"{P_FL1}%")]
LAD_A = lk.LadderPanel("「私たちだけ」の割合", A_ROWS, box=(1000, 560, 1860, 920), t_frame=T_A, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4,
                       title_line=ID["c0_shake"])


def a_A(t):
    if t < S("ch1"):
        return out_fade(t, S("ch1") - 0.15, 0.2)
    if t < S("ch2"):
        return 0.0
    if t < S("ch3"):
        return fade(t, S("ch2") + 0.1, 0.3) * out_fade(t, S("ch3") - 0.15, 0.2)
    if t < S("ch4"):
        return 0.0
    return fade(t, S("ch4") + 0.1, 0.3) * out_fade(t, S("ch5") - 0.1, 0.2)


def qmark(ctx, t, panel, i, t_from, t_to, a=1.0):
    g = panel.layout()
    al = a * fade(t, t_from, 0.3) * out_fade(t, t_to - 0.05, 0.1)
    if al > 0.003:
        text(ctx, "？%", g["val_x"], g["ys"][i], panel.val_size, RED, align="left", alpha=al)


def draw_A(ctx, t):
    LAD_A.draw(ctx, t, 1.0)
    qmark(ctx, t, LAD_A, 0, T_A + 0.45, A_ROWS[0].t_value)
    qmark(ctx, t, LAD_A, 1, A_ROWS[1].t_label + 0.3, A_ROWS[1].t_value)


# 第3章: 答えのばらつき 100 の取り分
C3_ORDER = ["R", "fp", "ne", "fi", "fc", "L", "fl"]
C3_NAMES = ["星の生まれる数", "惑星を持つ星の割合", "住めそうな惑星の数", "知的になる割合", "電波を出す割合", "文明が続く年数", "生命が生まれる確率"]
T_C3 = Sk("c3_share") - 1.5
C3_ROWS = []
for _i, (_k, _nm) in enumerate(zip(C3_ORDER, C3_NAMES)):
    _six = _k != "fl"
    C3_ROWS.append(lk.Row(_nm, SHARES[_k] * 100, t_label=T_C3 + 0.1 + 0.1 * _i, t_value=(Sk("c3_six", 0.25) + 0.12 * _i) if _six else Sk("c3_fl99", 0.45),
                          color=BLUE if _six else RED, line=ID["c3_six"] if _six else ID["c3_fl99"], text=f"{ihalf(SHARES[_k] * 100)}"))
C3 = lk.LadderPanel("答えのばらつき100の取り分", C3_ROWS, box=(1000, 100, 1860, 900), t_frame=T_C3, vmax=100.0, label_size=40, val_size=52, title_size=44, fade=0.4,
                    title_line=ID["c3_share"], plus=False, arrows=False)

# 第4章: ちょうど半分の回の答え
T_B4 = Sk("c4_med") - 1.3
B4_ROWS = [lk.Row("半分の回の答え", RES["fl1_med"], t_label=T_B4 + 0.1, t_value=Sk("c4_med", 0.5), color=BLUE, line=ID["c4_med"], text="3,500ほど"),
           lk.Row("第1章のかけ算", RES["theory_prod"], t_label=T_B4 + 0.2, t_value=Sk("c4_same", 0.55), color=ORANGE, line=ID["c4_same"], text="2,000ほど")]
BOX4 = lk.LadderPanel("文明の数（いま電波を出している）", B4_ROWS, box=(1000, 200, 1860, 520), t_frame=T_B4, vmax=4000.0, label_size=40, val_size=48, title_size=44, fade=0.4,
                      title_line=ID["c4_med"], plus=False, arrows=False)

# 第5章: ＋40光年以内
T_B5 = Sk("c5_add") - 1.2
B5_ROWS = [lk.Row("全部を幅で選ぶ", RES["p40_all"], t_label=T_B5 + 0.1, t_value=Sk("c5_a4", 0.55), color=ORANGE, line=ID["c5_a4"], text=f"{P40}%"),
           lk.Row("生命は必ず生まれる", RES["p40_fl1"], t_label=T_B5 + 0.2, t_value=Sk("c5_a8", 0.55), color=ORANGE, line=ID["c5_a8"], text=f"{P40F}%"),
           lk.Row("どこかに文明がいる", RES["fl1_p_any"], t_label=Sk("c5_a90", 0.0) - 1.2, t_value=Sk("c5_a90", 0.8), color=BLUE, line=ID["c5_a90"], text=f"{P_ANY_F}%",
                  branch=True, sub="生命が必ず生まれるとき"),
           lk.Row("40光年以内にいる", RES["p40_fl1"], t_label=Sk("c5_a8b", 0.0) - 1.2, t_value=Sk("c5_a8b", 0.55), color=ORANGE, line=ID["c5_a8b"], text=f"{P40F}%", plain=True)]
B5 = lk.LadderPanel("＋40光年以内", B5_ROWS, box=(1000, 320, 1860, 910), t_frame=T_B5, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4, title_line=ID["c5_add"])

# 第6章: 距離を1,000光年に
T_P6 = Sk("c6_add") - 1.2
P6_ROWS = [lk.Row("全部を幅で選ぶ", RES["p1000_all"], t_label=T_P6 + 0.1, t_value=Sk("c6_a29", 0.55), color=ORANGE, line=ID["c6_a29"], text=f"{P1K}%"),
           lk.Row("生命は必ず生まれる", RES["p1000_fl1"], t_label=T_P6 + 0.2, t_value=Sk("c6_a56", 0.55), color=ORANGE, line=ID["c6_a56"], text=f"{P1KF}%ほど")]
P6 = lk.LadderPanel("距離を1,000光年に", P6_ROWS, box=(1000, 350, 1860, 910), t_frame=T_P6, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4,
                    title_line=ID["c6_add"], plus=True)

# まとめ: 3つの梯子
T7 = S("ch7") + 0.1
SUM_BOX = [(1000, 100, 1860, 355), (1000, 375, 1860, 630), (1000, 650, 1860, 905)]
SUM_P = []
for _j, (_ttl, _a, _b, _ta, _tb, _ln) in enumerate([
        ("「私たちだけ」の割合", RES["p_alone"], RES["fl1_p_alone"], f"{P_ALONE}%", f"{P_FL1}%", None),
        ("40光年以内（出会える）", RES["p40_all"], RES["p40_fl1"], f"{P40}%", f"{P40F}%", ID["c7_0"]),
        ("1,000光年以内（2,000年待つ）", RES["p1000_all"], RES["p1000_fl1"], f"{P1K}%", f"{P1KF}%ほど", None)]):
    _t1 = (Sk("c7_0", 0.25) if _j == 1 else S("ch7") + 0.9 + 0.3 * _j)
    _rows = [lk.Row("全部を幅で選ぶ", _a, t_label=T7 + 0.05 + 0.04 * _j, t_value=_t1, color=ALONE_C if _j == 0 else ORANGE, line=_ln, text=_ta),
             lk.Row("生命は必ず生まれる", _b, t_label=T7 + 0.1 + 0.04 * _j, t_value=_t1 + 0.55, color=ALONE_C if _j == 0 else ORANGE, line=_ln, text=_tb)]
    SUM_P.append(lk.LadderPanel(_ttl, _rows, box=SUM_BOX[_j], t_frame=T7 + 0.04 * _j, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.3,
                                title_line=ID["c7_0"] if _j == 1 else None))
BELLS = [A_ROWS[0].t_value, A_ROWS[1].t_value, C3_ROWS[-1].t_value, B4_ROWS[0].t_value, B5_ROWS[0].t_value, B5_ROWS[1].t_value, P6_ROWS[0].t_value, P6_ROWS[1].t_value]


def draw_panel(ctx, t):
    a_all = out_fade(t, T_ES, 0.4)
    grp(ctx, a_all * a_A(t), draw_A, t)
    grp(ctx, a_all * out_fade(t, T_RS0 - 0.1, 0.2), lambda c, t_: C3.draw(c, t_), t)           # 第3章の棒は、区切りの前に片づける
    grp(ctx, a_all * out_fade(t, S("ch5") - 0.6, 0.2), lambda c, t_: BOX4.draw(c, t_), t)
    grp(ctx, a_all * out_fade(t, S("ch6") - 0.6, 0.2), lambda c, t_: B5.draw(c, t_), t)
    grp(ctx, a_all * out_fade(t, S("ch7") - 0.1, 0.2), lambda c, t_: P6.draw(c, t_), t)
    for p_ in SUM_P:
        grp(ctx, a_all, lambda c, t_, p_=p_: p_.draw(c, t_), t)




# 絵の出る時刻の記録（visual_lag 用）: 枠は声の0.5秒前までに・答えの数字は声に合わせる
TAB_T0 = LT0["table"]
TAB_CUES = [lk.Cue("表(7つの項)の枠", "frame", TAB_T0 + 0.2, lready("table", TAB_T0 + 0.2 + 0.6, 0.3), ID["c1_seven"])]
for _i in range(7):
    for _s, _c, _on, _off, _key in CARDS[_i]:
        TAB_CUES.append(lk.Cue(f"表 札「{_s}」", "value", _on, _on + 0.25, ID[_key]))
BOX1_CUES = [lk.Cue("箱「いま電波を出している文明」枠", "frame", T1_BOX, T1_BOX + 0.4, ID["c1_ans"]),
             lk.Cue("箱「2,000ほど」", "value", T1_ANS, T1_ANS + 0.35, ID["c1_ans"])]
RACE_CUES = [lk.Cue(f"早回しの山 {nm} の枠", "frame", LT0[nm] + 0.2, lready(nm, LT0[nm] + 0.2, 0.5), gid) for nm, gid in
             (("race2", "g2_1"), ("race4", "g4_1"), ("race5", "g5_1"), ("race6", "g6_1"))]
FIG_CUES = [lk.Cue("小さい順の帯の枠", "frame", LT0["sorted"] + 0.2, lready("sorted", LT0["sorted"] + 0.2, 0.4), ID["c2_sort"]),
            lk.Cue("100を分け合う枠", "frame", LT0["share"] + 0.2, lready("share", LT0["share"] + 0.2, 0.4), ID["c3_share"]),
            lk.Cue("幅の広さの枠", "frame", LT0["widths"] + 0.2, lready("widths", LT0["widths"] + 0.2, 0.4), ID["c3_reason"]),
            lk.Cue("星が生まれる数の枠（10倍ずつの区切り）", "frame", LT0["pick"] + 0.2, lready("pick", Sk("c2_how", 0.0) - 1.1, 0.4), ID["c2_how"]),
            lk.Cue("7つの値の枠（1に固定）", "frame", LT0["fix"] + 0.2, lready("fix", LT0["fix"] + 0.2, 0.4), ID["c4_fix"])]
ALL_CUES = (LAD_A.cues() + C3.cues() + BOX4.cues() + B5.cues() + P6.cues() + [c for p in SUM_P for c in p.cues()] + TAB_CUES + BOX1_CUES + RACE_CUES + FIG_CUES
            + GRID2.cues("1万マス(灰52)", ID["c2_a52"], ID["c2_a52"]) + GRID4.cues("1万マス(灰10)", ID["c4_a10"], ID["c4_a10"])
            + GRID5A.cues("1万マス(橙4)", ID["c5_a4"], ID["c5_a4"]) + GRID5B.cues("1万マス(橙8)", ID["c5_a8"], ID["c5_a8"])
            + GRID6A.cues("1万マス(橙29)", ID["c6_a29"], ID["c6_a29"]) + GRID6B.cues("1万マス(橙56)", ID["c6_a56"], ID["c6_a56"]))


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
    return [("「私たちだけ」の回は", f"100回に{P_ALONE}回 → {P_FL1}回", "yellow", INK, -0.010),
            ("人の一生で「出会える」回は", f"100回に{P40}回 〜 {P40F}回", "pink", RED, 0.008),
            ("1,000光年まで待てるなら", f"100回に{P1K}回 〜 {P1KF}回ほど", "mint", INK, -0.008)]


def end_screen(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "ドレイクの式を、1万回 選び直したら", LCX_E, 162, 40, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=60)
    t9 = Sk("c7_ch", 0.0)
    q = fade(t, t0 + 0.6, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
    if q > 0.003:
        sticky(ctx, "あなたは、宇宙人に\n出会える日が\n来ると思いますか？", RCX_E, 480, 52, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


CARD_POS = {**{n_: (1420, 300) for n_ in range(1, 7)}, 7: (480, 810)}      # 章カードの位置（x, y）。見開きの真ん中ではなく、空いている所へ（付せん・表・図の文字と重ならないように）


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, CARD_TITLES[ch[0]], a, x=CARD_POS.get(ch[0], (lf.GUTTER, 470))[0], y=CARD_POS.get(ch[0], (lf.GUTTER, 470))[1], size=60)


def pages(ctx, t):
    draw_left(ctx, t)
    draw_right(ctx, t)
    draw_panel(ctx, t)
    overlays(ctx, t)


# ---- 区切りの絵（見本: sims/kaidan-long.py の区切り）。EC は P_ALONE を使うので、データのあとで作る ----
EC_LEFT = ("「私たちだけ」は", f"100回に{P_ALONE}回")
EC_RIGHT = ("必ず生まれたら？", "出会えるのは？")
EC_FADE = 0.35                                          # Eyecatch は t1 から 0.35秒で消える。次の章（章カード・絵）と文字が重ならないよう、消え終わりを第4章の始まりにそろえる
EC = lk.Eyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None


def draw(ctx, t):
    lf.spread(ctx)
    ea = EC.alpha(t) if EC and t < T_RS1 else 0.0
    pg = (1 - fade(t, T_ES, 0.5)) * (out_fade(t, T_RS0 - 0.3, 0.3) if t < T_RS0 else (0.0 if t < T_RS1 else 1.0))      # 前の章の絵は区切りの前に片づける
    if t < T_ES + 0.6:
        grp(ctx, pg, pages, t)
    if ea > 0.003:
        EC.draw(ctx, t)
    if t >= T_ES:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・早回し）
# ============================================================
def turtle_step(seed=0, high=False):
    """亀の足音（ぽてっ・とこっ）。短い下がり調子の丸い音＋ごく小さな擦れ（kaidan-long.py と同じ）"""
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    n = np.random.default_rng(seed + 50).standard_normal(len(tt))
    n = np.convolve(n, np.ones(12) / 12, mode="same") * np.exp(-tt * 120) * 0.35
    return (tone * env + n) * 0.8


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    from long_bgm import bgm_track      # 2026-11-06 カスミソウ（甘茶の音楽工房）
    mx.add(0, bgm_track(DUR, lf.SR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 8):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for g in sorted(GAP_NOTE):
        if g in REST:
            continue                                                    # 区切りは早回しではない（下で足音だけ）
        if GAP_SEC[g] >= 2.0:
            beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
            mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
        else:
            mx.add(S(g) + 0.05, tick(1400, 0.05), 0.3)
    for i_, ts_ in enumerate(EC.step_times()):
        mx.add(ts_, turtle_step(seed=i_, high=bool(i_ % 2)), 0.32)      # 亀の足音（足あとの点が出る時刻）
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(T1_ANS + 0.1, chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(Sk("c7_2", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(Sk("c7_ch", 0.0) + 0.2, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
REST_STILLS = tuple(EC.still_times()) if EC else (0.0, 0.0, 0.0)       # 区切りの 始め・途中・終わり


def still_list():
    return [
        ("01_0.0s", "① 0.0秒: 問い（サムネと同じ言葉）・動く夜空・1万マス（灰と青）・割合は「？」", 0.0),
        ("02_2.5s", "② 2.5秒: 1万マスが埋まっていく・夜空が動く", 2.5),
        ("03_5.0s", "③ 5.0秒: 灰がみるみる増えて止まる・割合は「？」のまま", 5.0),
        ("04_ch0_cond", "④ 第0章: 条件の付せん・銀河・梯子の枠", Ek("c0_meet") + 0.4),
        ("05_ch1_board", "⑤ 第1章: 黒板のドレイクの式", Sk("c1_1961", 0.5)),
        ("06_ch1_ans", "⑥ 第1章の答え: 7つの項の表・札・2,000ほど", Ek("c1_ans") + 0.6),
        ("07_ch2_race", "⑦ 第2章: 1万回の答えの山（早回し）", S("g2_1") + 1.5),
        ("08_ch2_ans", "⑧ 第2章の答え: 100回に52回（1万マスの灰）", Ek("c2_a52") + 0.6),
        ("09_ch2_sorted", "⑨ 第2章: 小さい順の帯", Sk("c2_sort", 0.9) + 1.5),
        ("10_ch3_ans", "⑩ 第3章の答え: 7本の棒（6本は短い・生命が99）", Sk("c3_fl99") + 2.4),
        ("11_ch3_wid", "⑪ 第3章: 幅の広さの棒", Sk("c3_flr") + 2.5),
        ("11a_ec_start", "⑪a 区切り: 「ここまで」「ここから」・亀が左ページを歩き出す（始め）", REST_STILLS[0]),
        ("11b_ec_mid", "⑪b 区切り: 亀が見開きの真ん中・足あと", REST_STILLS[1]),
        ("11c_ec_end", "⑪c 区切り: 亀が右ページへ着く（終わり）", REST_STILLS[2]),
        ("12_ch4_ans", "⑫ 第4章の答え: 梯子に2本目（10）・3,500ほど", Ek("c4_same") + 0.9),
        ("13_ch5_disc", "⑬ 第5章: 円盤の中の40光年は点", Ek("c5_dot") + 0.5),
        ("14_ch5_ans", "⑭ 第5章の答え: 4 → 8・どこかにいる90と40光年の8", Sk("c5_a8b") + 0.8),
        ("15_ch5_why", "⑮ 第5章: 円の中に1つ入るには数千万", Ek("c5_why") + 0.5),
        ("16_ch6_ans", "⑯ 第6章の答え: 距離を1,000光年に 29 → 56ほど", Sk("c6_a56") + 3.0),
        ("17_summary", "⑰ まとめ: 3つの梯子", Sk("c7_2") + 1.5),
        ("18_end", "⑱ 終了画面", min(DUR - 0.5, Sk("c7_sub", 0.0) + 1.0)),
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


def eyecatch_sheet(out_dir):
    """区切りの 始め・途中・終わり の3枚を 480px にして1枚の一覧に（eyecatch_480.png）"""
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    labs = ["始め", "途中", "終わり"]
    W_, H_, lab_h, pad = 480, 270, 34, 10
    sheet = Image.new("RGB", (pad + 3 * (W_ + pad), pad + H_ + lab_h + pad), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, (tt, lab) in enumerate(zip(REST_STILLS, labs)):
        pth = WORK / f"eyecatch_{k}.png"
        lf.still(draw, tt, pth)
        im = Image.open(pth).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x = pad + k * (W_ + pad)
        sheet.paste(im, (x, pad))
        dr.text((x + 4, pad + H_ + 3), f"{k + 1} {_ts(tt)} {lab}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "eyecatch_480.png")
    print("区切りの一覧:", out_dir / "eyecatch_480.png")


def median_sheet(out_dir):
    """「中央値」の言い換えの確認: 定義の文（札「中央値 10個」）・7つの札がそろった所・第4章の箱（median_480.png）"""
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    items = [("定義の文: 札「1〜100個／中央値 10個」", Ek("c1_def") - 0.4), ("惑星の札: 中央値 約3割", Sk("c1_q2", 1.6)), ("生命の札: 中央値 約6割", Sk("c1_fl6", 0.9)),
             ("続く年数の札: 中央値 100万年", Sk("c1_mid7", 0.9)), ("7つの札がそろう", Ek("c1_all") + 0.3), ("第1章の答え: 2,000ほど", Ek("c1_ans") + 0.6)]
    W_, H_, lab_h, pad, cols = 480, 270, 34, 10, 3
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 22)
    except Exception:
        fnt = ImageFont.load_default()
    for k, (lab, tt) in enumerate(items):
        pth = WORK / f"median_{k}.png"
        lf.still(draw, tt, pth)
        im = Image.open(pth).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + H_ + 3), f"{_ts(tt)} {lab}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "median_480.png")
    print("中央値の一覧:", out_dir / "median_480.png")


def stills_preview(out_dir):
    stills_sheet(out_dir, still_list())
    eyecatch_sheet(out_dir)
    median_sheet(out_dir)


# ============================================================


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字の問い・夜空・1万マス・割合の箱）]")
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
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
CARD_LINES = {ln for t_ in CARD_TITLES for ln in t_.split("\n")}


def _allowed_nums():
    ok = set(range(0, 13)) | {20, 29, 40, 52, 56, 80, 90, 99, 100, 1000, 2000, 3500, 2018, 1961, 0.3, 4, 8, 10000}
    ok |= {float(P_ALONE), float(P_FL1), float(P40), float(P40F), float(P_ANY_F), float(P1K), float(P1KF)}
    ok |= {float(N_ALONE), float(N_ALONE_F), float(N40), float(N40F), float(N1K), float(N1KF)}
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
    txt = lambda k: tl.clip(ID[k]).text
    checks = []

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本の読み込み ----
    A(f"台本: 章は8つ（0〜7）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 8 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（声の文を並べ直すと台本の行と同じ。長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない（行の終わりに〔 〕が2つ並ぶ行も全部外れている）", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()))
    nar_head = NARR_PATH.read_text(encoding="utf-8").splitlines()
    title_line = next(ln for ln in nar_head if ln.startswith("題名:"))
    A(f"題名「{QTXT}…」の言葉が台本の題名の行と画面の問いで同じ（サムネと同じ言葉にそろえる）", QTXT in title_line)
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:]) if S(b) < 70]
    A(f"台本: 冒頭（0〜70秒）の文と文の間は 0.3秒前後（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし（最初の無音は第2章: {min(S(g) for g in GAP_NOTE):.1f}秒）",
      all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch2"))
    fast = [g for g in GAP_NOTE if GAP_SEC[g] >= 2.0 and g not in REST]
    A(f"台本: 無音の早回し {len(fast)} か所（台本には4か所。冒頭の注記の「5か所」とは1つ違う）はどれも4秒以内（{[GAP_SEC[g] for g in fast]}）", len(fast) == 4 and all(GAP_SEC[g] <= 4.0 for g in fast))
    # 区切り: 早回しとは別に「1か所・約4秒」を確かめる
    n_rest = len(REST)
    A(f"区切り: 台本の「（無音 4秒・区切り。…）」は {n_rest} か所（1か所）・長さ {T_RS1 - T_RS0:.1f}秒（約4秒）・ほかの無音（早回し）と数えが別",
      n_rest == 1 and abs((T_RS1 - T_RS0) - 4.0) < 0.01 and all(g_ not in REST for g_ in fast))
    A(f"区切り: 第3章のあと・第4章の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・章は8つのまま（{len(CHAPS)}章・chapters {len(tl.chapters)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(ID["c3_end"]) - 1e-6 and abs(T_RS1 - S("ch4")) < 1e-6 and len(CHAPS) == 8 and len(tl.chapters) == 8
      and not any("区切り" in t_ or "ここまで" in t_ for t_ in CH_TITLES) and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    A(f"区切り: 動画の真ん中あたり（{_ts(T_RS0)}〜{_ts(T_RS1)} ／ 全体 {_ts(DUR)} の {(T_RS0 + T_RS1) / 2 / DUR:.0%} のところ）・声の行なし",
      0.35 <= (T_RS0 + T_RS1) / 2 / DUR <= 0.65 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋「{EC_LEFT[0]}」「{EC_LEFT[1]}」（{P_ALONE} は data.json の 100回に{RES['p_alone'] * 100:.1f}回（{RES['p_alone']:.1%}）と同じ）・右は「ここから」＋「{EC_RIGHT[0]}」「{EC_RIGHT[1]}」・付せん「ひと休み」なし",
      EC_LEFT[1] == f"100回に{P_ALONE}回" and abs(RES["p_alone"] * 100 - 52) < 0.5 and P_ALONE == 52 and EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT} and "ひと休み" not in EC.texts())
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 亀は左ページ（x {xs_[0]:.0f}）から右ページ（x {xs_[-1]:.0f}）へ歩く・足あと・足音 {len(EC.step_times())} 個（すべて区切りの中）",
      xs_[0] < 400 and xs_[-1] > 1500 and all(b_ >= a_ - 1e-6 for a_, b_ in zip(xs_, xs_[1:])) and len(EC.step_times()) >= 10
      and all(T_RS0 <= x_ <= T_RS1 for x_ in EC.step_times()))
    nums40 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and E(it.id) < 40:
            nums40 |= set(_re.findall(r"\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭40秒（言い終わる文）の声の数字は3個以内（{sorted(nums40)}）", len(nums40) <= 3)
    A(f"台本: 「先に言うと〜」は 0:20〜0:30（{Sk('c0_first'):.1f}秒）・「条件をそろえます」は 0:30 より後（{Sk('c0_cond'):.1f}秒）・結論の向き（「いる」かどうかの答えは〜）は 2分以内（{Sk('c0_shake'):.1f}秒）",
      20 <= Sk("c0_first") <= 30 and Sk("c0_cond") > 30 and Sk("c0_shake") < 120)
    # ---- 声の数字 = data.json ----
    exp = [("c0_form", "60年以上前"), ("c1_mid1", "10個"), ("c1_fl6", "6割ほど"), ("c1_mid7", "100万年"), ("c1_ans", "2,000ほど"), ("c2_a52", f"100回に{P_ALONE}回"),
           ("c3_six", "100のうち1ほど"), ("c3_fl99", "100のうち99"), ("c4_a10", f"100回に{P_FL1}回"), ("c4_med", "3,500ほど"), ("c5_a4", f"100回に{P40}回"),
           ("c5_a8", f"100回に{P40F}回"), ("c5_a90", f"100回に{P_ANY_F}回"), ("c5_a8b", f"100回に{P40F}回"), ("c6_a29", f"100回に{P1K}回"), ("c6_a56", f"100回に{P1KF}回ほど"),
           ("c7_0", f"100回に{P40}回から{P40F}回"), ("c3_reason", "1億倍"), ("c5_f40", "80年"), ("c6_rt", "2,000年")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    A("声の「数千万」「数千」は円盤の体積比（約2,930万・約2,700）と合う", "数千万" in txt("c5_why") and "数千" in txt("c6_few") and 1e7 <= GEO["r40"] < 1e8 and 1e3 <= GEO["r1000"] < 1e4)
    # ---- 冒頭 0〜5秒 ----
    A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
    A(f"冒頭: 1万マスは 0秒目から埋まりはじめ（0.3秒で {GRID_OPEN.filled(0.3):,}マス）、5秒までに {GRID_OPEN.filled(5.0):,}マスで止まる（全体の 63%）。灰＝私たちだけ {N_ALONE:,}・青＝いる {10000 - N_ALONE:,}",
      GRID_OPEN.filled(0.3) > 100 and GRID_OPEN.filled(5.0) == GRID_OPEN.n_stop and GRID_OPEN.counts == [N_ALONE, 10000 - N_ALONE])
    # ---- 梯子 ----
    A("梯子の名札は台本どおり: 「全部を幅で選ぶ」「＋生命は必ず生まれる」（梯子・40光年・1,000光年・まとめ）／章の名札「＋40光年以内」「距離を1,000光年に」（＋なし）",
      [LAD_A.label_of(i) for i in range(2)] == ["全部を幅で選ぶ", "＋生命は必ず生まれる"] and [B5.label_of(i) for i in range(2)] == ["全部を幅で選ぶ", "＋生命は必ず生まれる"]
      and [P6.label_of(i) for i in range(2)] == ["全部を幅で選ぶ", "＋生命は必ず生まれる"] and B5.title == "＋40光年以内" and P6.title == "距離を1,000光年に" and not P6.title.startswith("＋"))
    sx = [C3.value_text(r) for r in C3.rows]
    A(f"第3章は7本の棒（6本は短い・7本目が 99 まで伸びる）: {sx}", len(C3.rows) == 7 and sx[:6] == ["0", "0", "0", "0", "0", "1"] and sx[6] == "99"
      and max(r.value for r in C3.rows[:6]) < 1.5 and C3.rows[6].value > 99)
    A("梯子の値の文字は data.json（52・10・4・8・90・29・56ほど）", [r.text for r in A_ROWS] == [f"{P_ALONE}%", f"{P_FL1}%"] and [r.text for r in B5_ROWS] == [f"{P40}%", f"{P40F}%", f"{P_ANY_F}%", f"{P40F}%"]
      and [r.text for r in P6_ROWS] == [f"{P1K}%", f"{P1KF}%ほど"])
    A("梯子の棒の長さ ＝ 値（0〜100%）: 私たちだけ 52 > 10／40光年 4 < 8／1,000光年 29 < 56", A_ROWS[0].value > A_ROWS[1].value and B5_ROWS[0].value < B5_ROWS[1].value < B5_ROWS[2].value and P6_ROWS[0].value < P6_ROWS[1].value)
    probs = LAD_A.layout_problems() + C3.layout_problems() + BOX4.layout_problems() + B5.layout_problems() + P6.layout_problems() + [x for p in SUM_P for x in p.layout_problems()]
    A(f"梯子の配置の問題: {probs}", not probs)
    pb = GRID2.check() + GRID4.check() + GRID5A.check() + GRID5B.check() + GRID6A.check() + GRID6B.check() + GRID_OPEN.check()
    A(f"1万マス: 色ごとのマスの数がデータと同じ（7枚）: {pb}", not pb)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件（最も先: {min(r[3] for r in rows_):+.1f}秒）{[b[0] for b in bad[:3]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]
        # 文字の箱の交わり
        # 章カードは付せんの下地（文字の外に約45px・約30px）ごと調べる
        def _pad_card(fr_):
            cd_ = [e for e in fr_[1] if e[0] in CARD_LINES]
            if not cd_:
                return fr_
            box_ = ("章カード", min(e[1] for e in cd_) - 50, min(e[2] for e in cd_) - 40, max(e[3] for e in cd_) + 50, max(e[4] for e in cd_) + 40, cd_[0][5])
            return (fr_[0], [e for e in fr_[1] if e[0] not in CARD_LINES] + [box_], *fr_[2:])
        pairs = lk.text_box_overlaps([_pad_card(f_) for f_ in frames], skip=[(T_ES, T_ES + 0.6)])
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）。章カード（章の頭の2秒だけ出る題の付せん）も数えた",
                                                                                  "字幕の行（「字幕: …」）の箱を含めて調べた"])
        for a_, b_, x, y in spans[:10]:
            print(f"  文字の交わり {_ts(a_)}〜{_ts(b_)} 「{x}」と「{y}」")
        A(f"文字の箱の交わり（章カード・字幕・付せん・札・棒の枠・図の文字・全コマ）: {len(spans)} 組・{len(pairs)} コマ（期待 0）", not spans)
        small = lk.min_text_size(frames, 40, exempt=lambda s_: s_ in CARD_LINES or s_.startswith("字幕: "))
        for t_, lab, sz in small[:6]:
            print(f"  40px未満 {_ts(t_)} 「{lab}」 {sz:.0f}px")
        A(f"文字の大きさ: 40px 未満 {len(small)} 種（スマホで読める。幅480pxに縮めても約10px）", not small)
        edge = lk.outside_area(frames, skip=[(T_ES, T_ES + 0.6)])
        for t_, lab, bx in edge[:6]:
            print(f"  画面の端 {_ts(t_)} 「{lab}」 {bx}")
        A(f"画面の端（x 48〜1872・y 36〜1044）に近い文字: {len(edge)} 件", not edge)
        # 左ページの文字が、のど（x 945 付近）をまたがない・右ページの文字が右端の紙の外へ出ない
        left_txt = [(t_, e) for t_, e in allt if e[1] < 940 and e[3] > 945 and e[0] not in CARD_LINES and not e[0].startswith("字幕: ") and t_ < T_ES]
        A(f"左ページの文字がのど（x 945）をまたぐ: {len(left_txt)} 件 {[e[0] for t_, e in left_txt[:3]]}", not left_txt)
        tp = teaser.check([f for f in frames if f[0] <= 5.0 + 1e-9])
        A(f"OpeningTeaser.check（0秒目に問いの全行・伏せ忘れなし）: {tp or 'OK'}", not tp)
        q0 = [e for f in frames if f[0] == 0.0 for e in f[1] if e[0] in QLINES]
        A(f"冒頭の問い: 0秒目に{len(QLINES)}行そろって {min(e[5] for e in q0):.0f}px（90px 以上）・サムネと同じ言葉「{QTXT}」", len(q0) == len(QLINES) and min(e[5] for e in q0) >= 90 and QTXT == "宇宙人に出会える確率は？")
        qm = [(t_, e[0]) for t_, e in allt if t_ <= 5.0 and e[0] == "？%"]
        dg = [(t_, e[0]) for t_, e in allt if t_ <= 5.0 and e[1] > 1030 and 650 <= e[2] <= 850 and _re.search(r"\d", e[0])]
        A(f"冒頭: 割合の箱は「？%」のまま（0〜5秒の全コマ {len(qm)} 回出る）・箱の中に数字なし {dg}", len({t_ for t_, _ in qm}) == len({f[0] for f in frames if f[0] <= 5.0}) and not dg)
        # 巨大・極小の数は指数を画面に出さない
        expo = sorted({e[0] for t_, e in allt if _re.search(r"10\^|\d[eE][+\-]?\d|×\s*10\s*\^|乗|\d{8,}", e[0]) and not e[0].startswith("字幕: ")})
        A(f"巨大・極小の数に指数を出さない（e+・10^・乗・8けた以上の数字）: {expo}", not expo)
        # 答えの数字（文字）が声より先に出ていないか
        tokens = [(f"{P_ALONE}%", "c2_a52"), (f"{P_FL1}%", "c4_a10"), (f"{P40}%", "c5_a4"), (f"{P40F}%", "c5_a8"), (f"{P_ANY_F}%", "c5_a90"), (f"{P1K}%", "c6_a29"),
                  (f"{P1KF}%ほど", "c6_a56"), ("2,000ほど", "c1_ans"), ("3,500ほど", "c4_med"), ("99", "c3_fl99"), (f"1万回のうち 灰 {N_ALONE:,}回", "c2_a52"),
                  (f"1万回のうち 灰 {N_ALONE_F:,}回", "c4_a10"), (f"1万回のうち 橙 {N40:,}回", "c5_a4"), (f"1万回のうち 橙 {N40F:,}回", "c5_a8"),
                  (f"1万回のうち 橙 {N1K:,}回", "c6_a29"), (f"1万回のうち 橙 {N1KF:,}回", "c6_a56"),
                  ("100倍", "c3_reason"), ("1億倍", "c3_reason"), ("往復 80年", "c5_f40"), ("往復 2,000年", "c6_rt")]
        for tok, key in tokens:
            ft = first_seen(frames, lambda s_, e, tok=tok: s_ == tok)
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        # 画面の数字は data.json の値（か閉じた目もりなど）
        ok_ = _allowed_nums()
        extra = {}
        for t_, e in allt:
            lab = e[0]
            if lab.startswith("字幕: ") or lab in CARD_LINES:
                continue
            if _re.match(r"^\d[\d,]*回$", lab):
                continue                                                 # 早回しの「N回」
            for m in _re.finditer(NUM_RE, lab):
                v = float(m.group(0).replace(",", ""))
                if v not in ok_:
                    extra.setdefault(m.group(0), (lab, t_))
        for v, (s_, t_) in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて data.json の値（の四捨五入）か、目もりなどの閉じた値: 余分 {len(extra)}個 {list(extra)[:5]}", not extra)
        neg_txt = [e[0] for t_, e in allt if _re.search(r"-\d|−\d", e[0])]
        A(f"画面に負の数は出ない: {neg_txt[:3]}", not neg_txt)
        # 章ごとに画面に出るもの
        def has(a_, b_, keys, exact=True):
            fr = [f for f in frames if a_ <= f[0] < b_]
            return all(first_seen(fr, (lambda s_, e, k=k: s_ == k) if exact else (lambda s_, e, k=k: k in s_)) is not None for k in keys)
        A("0章: 付せん「1万回」「いる？」「出会える？」・条件の付せん（天の川銀河の中だけ…）・銀河の絵の名札「天の川銀河」「私たちの太陽」・梯子の枠「「私たちだけ」の割合」「全部を幅で選ぶ」",
          has(0, S("ch1"), ["1万回", "いる？", "出会える？", "条件", "天の川銀河の中だけ", "天の川銀河", "私たちの太陽", "「私たちだけ」の割合", "全部を幅で選ぶ", "幅", "文明"]))
        A("1章: 題字「ドレイクの式」・表の7つの名前と札・付せん「2,000年…」「2018年の論文と同じ幅」・箱「いま電波を出している文明」2,000ほど",
          has(S("ch1"), S("ch2"), ["ドレイクの式", "星が生まれる数（1年）", "惑星を持つ星の割合", "住めそうな惑星の数", "生命が生まれる確率", "知的な生命になる割合", "電波を出す割合", "電波を出し続ける年数",
                                  "1〜100個／中央値 10個", "中央値 約3割", "中央値 約0.3個", "幅は とてつもなく広い", "中央値 約6割", "中央値 100に3ほど", "中央値 10に1ほど", "中央値 100万年",
                                  "2018年の論文と同じ幅", "いま電波を出している文明", "2,000ほど"]))
        A("2章: 付せん「生命の幅は、けた違い」「1に届かない ＝ 私たちだけ」・図「1〜10個」「10〜100個」「0.00000…01」・早回しの山（数字・札なし）・1万マス・帯「私たちだけ」「ちょうど半分」",
          has(S("ch2"), S("ch3"), ["生命の幅は、けた違い", "1に届かない ＝ 私たちだけ", "1〜10個", "10〜100個", "0.00000…01", "ちょうど半分",
                                  f"{P_ALONE}%", "2018年の論文とほぼ同じ"]))
        A("3章: 7本の棒の名札（星の生まれる数…生命が生まれる確率）・100のうち99・幅の広さ（100倍…1億倍・ゼロが何十個も並ぶ）・地球1つ",
          has(S("ch3"), S("ch4"), C3_NAMES + ["99", "1億倍", "ゼロが何十個も並ぶ", "生まれやすい？", "奇跡のような偶然？", "1つだけでは 見分けられない"]))
        A("4章: 付せん「生命が生まれる確率 ＝ 1」・左の7つの値（1 に固定）・梯子の2本目・箱「半分の回の答え」3,500ほど・「第1章のかけ算」2,000ほど",
          has(S("ch4"), S("ch5"), ["生命が生まれる確率 ＝ 1", "1 に固定", "＋生命は必ず生まれる", f"{P_FL1}%", "半分の回の答え", "3,500ほど", "第1章のかけ算", "2,000ほど"]))
        A("5章: 付せん「1光年 ＝ …」「出会える ＝ 40光年以内」・往復の絵（信号 40年・返事 40年・往復 80年）・円盤（直径・厚さ・40光年）・名札「＋40光年以内」・棒4・8・90・8",
          has(S("ch5"), S("ch6"), ["1光年 ＝ 光が1年で進む距離", "出会える ＝ 40光年以内", "信号 40年", "返事 40年", "往復 80年", "人の一生くらい", "直径 約10万光年", "厚さ 約1,000光年", "40光年",
                                  "＋40光年以内", f"{P40}%", f"{P40F}%", f"{P_ANY_F}%", "どこかに文明がいる", "40光年以内にいる", "銀河全体で 数千万の文明"]))
        A("6章: 名札「距離を1,000光年に」・付せん「往復 2,000年」・図（2,000年前・今日・1,000光年）・棒29・56%ほど・「銀河全体で 数千の文明」",
          has(S("ch6"), S("ch7"), ["距離を1,000光年に", "往復 2,000年", "2,000年前", "今日", "1,000光年", f"{P1K}%", f"{P1KF}%ほど", "銀河全体で 数千の文明"]))
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、EC.texts() の文字だけが出ている（前の章の棒・付せん・図の文字・字幕・章カードなし）: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        A("区切りの間は、0.5秒すぎから最後まで 左「ここまで」＋2行・右「ここから」＋2行 がそろっている",
          bool(rs_in) and all(EC.texts() <= {e[0] for e in f[1]} for f in rs_in))
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980（のどをまたがない）",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        # 区切りの出入り（t1 から 0.35秒で消える）と第4章の章カードが重なっても、文字の箱は交わらない（下の「文字の箱の交わり」が全コマを数える）
        ec_out = [f for f in frames if T_RS1 < f[0] <= T_RS1 + 0.4]
        ec_card = sorted({e[0] for f in ec_out for e in f[1] if e[0] in EC.texts() or e[0] in CARD_LINES})
        print("  第4章の始まり（区切りが消えた直後 t1〜+0.4秒）に出ている文字（区切りの文字は含まれない）:", ec_card)
        f7 = min(frames, key=lambda f: abs(f[0] - (T_ES - 0.3)))
        n7 = {e[0] for e in f7[1]}
        A("まとめ: 3つの梯子（名札3つ・52 → 10／4 → 8／29 → 56%ほど）・左ページに2つの円", {"「私たちだけ」の割合", "40光年以内（出会える）", "1,000光年以内（2,000年待つ）", f"{P_ALONE}%", f"{P_FL1}%", f"{P40}%", f"{P40F}%", f"{P1K}%", f"{P1KF}%ほど",
                                                                       "小さい円 ＝ 40光年（往復80年）", "大きい円 ＝ 1,000光年（往復2,000年）"} <= n7)
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
        es_last = [e for f in frames if f[0] >= Sk("c7_ch", 0.0) + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        A("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5)
        A(f"終了画面: 最後の約15秒（{DUR - T_ES:.1f}秒）・定型2行は最後の文だけ（「このチャンネルでは」{Sk('c7_ch'):.1f}秒〜）", 10.0 <= DUR - T_ES <= 20.0 and Sk("c7_ch") > T_ES)
        A("まとめの締め: 結果 → 持ち帰る一言 → 問い（3文）→ 注意書き1文 → 定型2行の順", S(ID["c7_0"]) < S(ID["c7_1"]) < S(ID["c7_2"]) < S(ID["c7_3"]) < S(ID["c7_ch"]) < S(ID["c7_sub"]))
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


