"""サケの卵ロング: 本番の模型（2026-11-05・事実確認の反映後）

  python -X utf8 sims/salmon_model.py          → out/salmon-long/numbers.md と data.json
出典と仮定: research/longform_salmon_outline_2026-11-05.md・research/longform_salmon_FACTCHECK_2026-11-05.md

1粒の関門（すべて北海道の回帰率・生まれた年は実際の29年分からくじ）
  関門1 生まれられるか        卵 → 川を下り始める稚魚。川 20%（千歳川の推定。幅5〜20%）／ふ化場 87.5%
  関門2 最初の冬を越えられるか  回帰率 ÷ 海の生残（回帰率からの逆算。川を下る間もここに入れる）
  関門3 海から帰ってこられるか  SEA（資料の推定値からの計算。幅51〜69%）
  ここまでが「帰ってくる」＝資料の来遊に当たる数（沿岸の漁獲＋川の捕獲。捕まらず川を上った魚は入らない）
  関門4 網を抜けて川の捕獲場へ  RIVER（数えられた魚のうち川の捕獲の割合。2022〜2024年の全国 12.0〜15.3%）
回帰率は公式の図9（国際漁業資源の現況 令和6年度 61 サケ）からの読み取り。分母は放流稚魚。
川生まれにも同じ回帰率を使う（千歳川の2006〜2011年に生まれた魚で「同程度」という報告による仮定）。
1粒ずつ独立に計算する。同じ産卵床の卵は運命を共にしやすいと考えられるので、0匹の割合は少なめに出る可能性がある。
"""
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "salmon-long"
SEED = 2026
N = 10000           # 1万回（1万粒の組・1万匹のお母さん）
EGGS = 10000        # 1組の卵
MOTHER = 3000       # お母さん1匹の卵（資料は約2,000〜3,000粒。多めに置く）
NEED = 2            # オスとメスが1匹ずつ

P_RIVER = 0.20      # 自然産卵の卵→降下稚魚（千歳川の推定: 死亡率約80%）
P_RIVER_LOW = (0.05, 0.10)   # 支流の実験 約5%・カナダの天然の平均 7.9%
P_HATCH = 0.875     # ふ化場の卵→放流（死亡率約10〜15%）
SEA = 0.62          # 最初の冬のあと、帰ってくるまでの生残（0.994×0.763×0.821）
SEA_RANGE = (0.51, 0.69)
RIVER = 0.135       # 数えられた魚のうち川の捕獲（12.0〜15.3%）

YEARS = list(range(1989, 2018))
HK = [4.35, 5.65, 4.61, 4.68, 4.98, 4.59, 2.68, 4.23, 4.85, 4.52, 7.15, 4.79, 6.70, 3.85, 5.77, 3.64, 4.61,
      3.41, 4.44, 3.83, 3.83, 3.09, 3.92, 1.83, 1.12, 2.65, 1.14, 2.05, 1.70]
REGION_2017 = {"北海道": 1.70, "本州の日本海": 0.37, "本州の太平洋": 0.08}      # 2017年級（公的資料の本文）

R = np.array(HK) / 100
OLD = np.array([YEARS.index(y) for y in YEARS if y <= 2005])
NEW = np.array([YEARS.index(y) for y in YEARS if y >= 2013])


def chain(rng, p, n=EGGS, trials=N, sea=SEA, table=R):
    """1万粒の組を trials 回。生まれた年を組ごとにくじ。各関門のあとに残った数を返す。"""
    r = rng.choice(table, trials)
    a = rng.binomial(n, p, trials)
    b = rng.binomial(a, np.minimum(1.0, r / sea))
    c = rng.binomial(b, sea)
    d = rng.binomial(c, RIVER)
    return a, b, c, d


def summ(x):
    return {"median": float(np.median(x)), "mean": round(float(np.mean(x)), 2), "min": int(np.min(x)), "max": int(np.max(x)),
            "p10": float(np.percentile(x, 10)), "p90": float(np.percentile(x, 90))}


def mothers(rng, p, table, n=MOTHER, trials=N):
    """お母さん1匹の卵から、帰ってくる数。"""
    r = rng.choice(table, trials)
    k = rng.binomial(n, p * r)
    return {"mean": round(float(k.mean()), 1), "median": float(np.median(k)), "min": int(k.min()), "max": int(k.max()),
            "zero": round(float((k == 0).mean() * 100), 2), "under2": round(float((k < NEED).mean() * 100), 2)}


def end_share(p, sea=SEA):
    """1粒の終点の割合（%）。年のくじの平均"""
    s2 = float(np.mean(np.minimum(1.0, R / sea)))
    return {"関門1で": round((1 - p) * 100, 2), "関門2で": round(p * (1 - s2) * 100, 2), "関門3で": round(p * s2 * (1 - sea) * 100, 2),
            "帰ってくる": round(p * s2 * sea * 100, 3), "うち川の捕獲場": round(p * s2 * sea * RIVER * 100, 3)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    d = {"years": dict(zip(YEARS, HK)), "params": {"P_RIVER": P_RIVER, "P_HATCH": P_HATCH, "SEA": SEA, "RIVER": RIVER, "MOTHER": MOTHER}}
    d["table"] = {"mean": round(float(R.mean() * 100), 2), "median": round(float(np.median(R) * 100), 2),
                  "min": float(R.min() * 100), "max": float(R.max() * 100), "ratio": round(float(R.max() / R.min()), 1),
                  "old_mean": round(float(R[OLD].mean() * 100), 2), "new_mean": round(float(R[NEW].mean() * 100), 2),
                  "best_year": YEARS[int(R.argmax())], "worst_year": YEARS[int(R.argmin())]}

    # 問い1: 川生まれ
    q1 = {}
    for nm, p in (("20", P_RIVER), ("10", P_RIVER_LOW[1]), ("5", P_RIVER_LOW[0])):
        a, b, c, e = chain(rng, p)
        q1[nm] = {"fry": summ(a), "winter": summ(b), "back": summ(c), "trap": summ(e), "ends": end_share(p)}
    d["q1"] = q1
    d["gate2_keep"] = {str(s): round(float(np.mean(np.minimum(1.0, R / s))) * 100, 2) for s in (SEA, *SEA_RANGE)}

    # 問い2: ふ化場
    a, b, c, e = chain(rng, P_HATCH)
    d["q2"] = {"fry": summ(a), "winter": summ(b), "back": summ(c), "trap": summ(e), "ends": end_share(P_HATCH),
               "x_low": round(P_HATCH / P_RIVER, 1), "x_high": round(P_HATCH / P_RIVER_LOW[0], 1)}

    # 問い3: 生まれた年（1万粒から帰ってくる数の期待値）
    d["q3"] = {"per_year": {y: {"r": h, "river": round(EGGS * P_RIVER * h / 100), "hatch": round(EGGS * P_HATCH * h / 100)} for y, h in zip(YEARS, HK)},
               "region_2017": REGION_2017}

    # 問い4: お母さん1匹の3,000粒（帰ってくる数と、産卵までたどりつく必要のある割合）
    q4 = {}
    for nm, p in (("20", P_RIVER), ("10", P_RIVER_LOW[1]), ("5", P_RIVER_LOW[0])):
        q4[nm] = {"all": mothers(rng, p, R), "old": mothers(rng, p, R[OLD]), "new": mothers(rng, p, R[NEW])}
        q4[nm]["need_pct"] = {t: round(NEED / (MOTHER * p * float(v.mean())) * 100, 1) for t, v in (("all", R), ("old", R[OLD]), ("new", R[NEW]))}
    q4["hatch"] = {"all": mothers(rng, P_HATCH, R), "new": mothers(rng, P_HATCH, R[NEW]),
                   "need_pct": {t: round(NEED / (MOTHER * P_HATCH * float(v.mean())) * 100, 1) for t, v in (("all", R), ("new", R[NEW]))}}
    q4["egg2000_20"] = {"all": mothers(rng, P_RIVER, R, n=2000), "old": mothers(rng, P_RIVER, R[OLD], n=2000), "new": mothers(rng, P_RIVER, R[NEW], n=2000)}
    q4["need_by_year_20"] = {y: round(NEED / (MOTHER * P_RIVER * h / 100) * 100, 1) for y, h in zip(YEARS, HK)}
    q4["back_by_year_20"] = {y: round(MOTHER * P_RIVER * h / 100, 1) for y, h in zip(YEARS, HK)}
    q4["cross_years"] = [y for y, h in zip(YEARS, HK) if NEED / (MOTHER * P_RIVER * h / 100) > RIVER]
    d["q4"] = q4
    (OUT / "data.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    t = d["table"]
    L = ["# サケの卵ロング 本番の数字（sims/salmon_model.py・種2026）", "",
         "1万回＝1万粒の組を1万回（生まれた年は組ごとに29年分からくじ）。お母さんは1万匹。すべて計算で、1粒ずつ独立。",
         f"回帰率（北海道・公式の図9の読み取り）: 平均{t['mean']}%・中央値{t['median']}%・最低{t['min']:.2f}%（{t['worst_year']}年級）・最高{t['max']:.2f}%（{t['best_year']}年級）・差{t['ratio']}倍。"
         f"1989〜2005年級の平均{t['old_mean']}%／2013〜2017年級の平均{t['new_mean']}%。", "",
         "## 問い1 川で生まれた1万粒", "",
         "| 卵の生残 | 稚魚 | 最初の冬のあと | **帰ってくる 中央値** | 帰ってくる 10%点〜90%点 | 最少〜最多 | 川の捕獲場まで 中央値 |", "|---|---|---|---|---|---|---|"]
    for k in ("20", "10", "5"):
        v = q1[k]
        L.append(f"| {k}% | {v['fry']['median']:.0f} | {v['winter']['median']:.0f} | **{v['back']['median']:.0f}匹** | {v['back']['p10']:.0f}〜{v['back']['p90']:.0f} | {v['back']['min']}〜{v['back']['max']} | {v['trap']['median']:.0f}匹 |")
    L += ["", "1粒の終点（%・卵の生残20%）: " + "／".join(f"{a} {b}" for a, b in q1["20"]["ends"].items()),
          "関門2を越える割合（平均・逆算）: " + "／".join(f"海の生残{a}なら{b}%" for a, b in d["gate2_keep"].items()) + "。どの場合も9割以上が関門2で減る。",
          f"最初の冬を越えたら帰ってくる: 10匹に5〜7匹（中心{SEA * 10:.0f}匹。計算）。", "",
          "## 問い2 ふ化場の1万粒", "",
          f"稚魚 {d['q2']['fry']['median']:.0f}・最初の冬のあと {d['q2']['winter']['median']:.0f}・帰ってくる 中央値 **{d['q2']['back']['median']:.0f}匹**（10%点〜90%点 {d['q2']['back']['p10']:.0f}〜{d['q2']['back']['p90']:.0f}、最少〜最多 {d['q2']['back']['min']}〜{d['q2']['back']['max']}）・川の捕獲場まで 中央値 {d['q2']['trap']['median']:.0f}匹。",
          "1粒の終点（%）: " + "／".join(f"{a} {b}" for a, b in d["q2"]["ends"].items()),
          f"川生まれとの差: 約{d['q2']['x_low']}〜{d['q2']['x_high']}倍（川の卵の生残20%〜5%）。", "",
          "## 問い3 生まれた年", "",
          f"1万粒から帰ってくる数（川生まれ20%の期待値／ふ化場）: 最高の{t['best_year']}年級 {d['q3']['per_year'][t['best_year']]['river']}／{d['q3']['per_year'][t['best_year']]['hatch']}匹、最低の{t['worst_year']}年級 {d['q3']['per_year'][t['worst_year']]['river']}／{d['q3']['per_year'][t['worst_year']]['hatch']}匹。",
          "場所の差（2017年級・本文）: " + "／".join(f"{a} {b}%" for a, b in REGION_2017.items()) + "。", "",
          "## 問い4 お母さん1匹の3,000粒（1万匹・帰ってくる数）", "",
          "| 卵の生残 | 29年分のくじ 平均（中央値） | 1989〜2005年級 | 2013〜2017年級 | 産卵までたどりつく必要のある割合（29年分／1989〜2005／2013〜2017） | 2匹未満のお母さん（2013〜2017） |", "|---|---|---|---|---|---|"]
    for k in ("20", "10", "5"):
        v = q4[k]
        L.append(f"| {k}% | {v['all']['mean']}匹（{v['all']['median']:.0f}） | {v['old']['mean']}匹 | {v['new']['mean']}匹 | {v['need_pct']['all']}%／{v['need_pct']['old']}%／{v['need_pct']['new']}% | {v['new']['under2']}% |")
    e2 = q4["egg2000_20"]
    L += ["", f"ふ化場の卵3,000粒: 29年分 平均{q4['hatch']['all']['mean']}匹（必要な割合{q4['hatch']['need_pct']['all']}%）／2013〜2017 平均{q4['hatch']['new']['mean']}匹（{q4['hatch']['need_pct']['new']}%）。"]
    L += ["", f"2,000粒にした場合（生残20%）: 29年分 {e2['all']['mean']}匹／1989〜2005 {e2['old']['mean']}匹／2013〜2017 {e2['new']['mean']}匹。",
          f"年ごと（生残20%・3,000粒）: 帰ってくる数は最高{q4['back_by_year_20'][t['best_year']]}匹（{t['best_year']}年級）、最低{q4['back_by_year_20'][t['worst_year']]}匹（{t['worst_year']}年級）。必要な割合は{q4['need_by_year_20'][t['best_year']]}%〜{q4['need_by_year_20'][t['worst_year']]}%。",
          f"必要な割合が、川の捕獲の割合{RIVER * 100:.1f}%を超える年: " + "、".join(str(y) for y in q4["cross_years"]) + f"（生残20%のとき。29年中{len(q4['cross_years'])}年）。",
          "", "## 言い切ってよいこと（事実確認のうえ）",
          "- 最初の関門（砂利を出て川を下り始めるまで）で、千歳川の推定なら10粒に8粒が残れない。5〜20%のどれでも、中央値のあなたはここで終わる。",
          "- 川を下って最初の冬を越えるまで（約1年）で、帰ってくる魚の元になる稚魚の9割以上が減る（逆算。海の生残の幅でも変わらない）。",
          "- 川生まれの卵なら、最初の冬のあとの海の旅（10匹に5〜7匹が帰る）は、前の2つの関門より減り方が小さい。",
          "- 北海道の回帰率は、生まれた年で約6.4倍違う。",
          "- 帰ってくる数が減ると、産卵までたどりつく必要のある割合は上がる（向きは卵の生残に関係なく同じ）。",
          "## 言い切らないこと",
          "- 「帰ってくるのは約80匹」を幅なしで言わない（卵の生残5〜20%で約20〜80匹）。",
          "- 「帰ってきた魚の86%が網に入る」とは言わない。「数えられた魚のうち約85〜88%は沿岸で獲られた魚。捕まらず川を上った魚はこの数に入らない」と言う。",
          "- 「数が足りる／足りない」と断定しない。捕まらず川を上った魚の数は分からない。",
          "- 川の捕獲場の数（関門4）を「川へ戻れた数」と呼ばない。",
          "- 0匹や2匹未満の割合には「この計算では」を付ける（1粒ずつ独立に計算しているため）。",
          "- 大きさの効果の倍率を、北海道全体の年に当てはめない。大きさと年の順位を言わない。"]
    (OUT / "numbers.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
