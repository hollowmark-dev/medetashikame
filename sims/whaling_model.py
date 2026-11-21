"""捕鯨船ロングの構成案用の計算（2026-11-06・ショート担当）。本番の前の確かめで、映像は作らない。

使い方: python -I -X utf8 sims/whaling_model.py  （sim_channel から）
読むもの: research/whaling_data/ の表（CC BY 4.0）。表として読むだけで、中のものは実行しない。
書くもの: research/whaling_numbers_2026-11-06.md

【置き方】
- 港と年: ニューベッドフォードを1840〜58年に出た船（Davis, Gallman & Gleiter 1997 と同じ範囲）。
- 値段: 同書 表9A.1〜9A.3 の CATCHVAL 列（当時の金額。Starbuck の表と同じ系列。ページの画像で読んだ）。帰港した年の値を使う。1バレル＝31.5ガロン。
- 月給: 持ち帰った油とひげの値打ち × 取り分 ÷ 航海の月数。諸費用と前借りの利子は引いていない（同書の Own Vessel と同じ考え方）。
- 月数: 帰港の月まで分かる6か月以上の航海だけ（3.3か月で大量の油という記録 AV08206 などを除く）。読み方の確かめでは「年の差×12」も使う。
- 新米の取り分: 1/100〜1/400 だけを使う（1/65 などは階級か取り分の記録違いとみなす）。
- 陸の賃金: Abbott の未熟練の工場労働者（Davis ほか1990 の表 Panel C。日給×25日）。同書 表5.8 Panel D の比で確かめる。
- 北の海: 漁場の欄に N Pacific・Arctic・Okhotsk・Bering などが入る航海。
- 外す記録（2026-11-06 事実確認のあと・統括の判断。理由は記録そのものの問題）: 獲れ高の計算から EXCLUDE の2航海を外す。
  AV00256 Adeline 1850-53 はサイトの航海の項に "on freight" の注記。AV02776 Charleston Packet 1853-54 は廃船の記号でサイトに獲れ高の数がない。
  帰らない船の数（1,666航海が分母）には残す。外しても北の海の順位は読み方4通りとも同じ。
- 食事の値打ち: 同書 p.200 注47 の各年の金額（月 $3.50〜6.00＝1840〜43年、$4.70〜8.00＝1855〜58年）を年で直線につなぐ（つなぎ方はこの計算の置き方）。

【結論の決め方】（読み方を変えても残るものだけを言う）
- 読み方4通り（月数2通り×値段2通り）のすべてで、北の海の平均と中央値が比べる相手より高いときだけ「北の海が高い」と言う。
- 同じ年の範囲で比べる。大西洋は航海数が少なく、同じ年で比べると中央値が逆になるので、逆転の話には使わない。
"""
import collections
import csv
import json
import re
from pathlib import Path

import numpy as np

csv.field_size_limit(10 ** 9)
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "research" / "whaling_data"
OUT = ROOT / "research" / "whaling_numbers_2026-11-06.md"
SEED = 20261106
N = 10000
# 当時の金額。マッコウ油と鯨油は1ガロン、ひげは1ポンド（表9A.1〜9A.3 の CATCHVAL 列）
SPERM = {1839: 1.03, 1840: 1.00, 1841: .94, 1842: .73, 1843: .63, 1844: .905, 1845: .88, 1846: .87875, 1847: 1.002548, 1848: 1.0033,
         1849: 1.089, 1850: 1.207, 1851: 1.2725, 1852: 1.2375, 1853: 1.2475, 1854: 1.4875, 1855: 1.772, 1856: 1.62, 1857: 1.2833,
         1858: 1.21, 1859: 1.3625, 1860: 1.415, 1861: 1.315, 1862: 1.425, 1863: 1.61, 1864: 1.78, 1865: 2.25, 1866: 2.55}
WHALE = {1839: .345, 1840: .30, 1841: .3175, 1842: .3375, 1843: .345, 1844: .365, 1845: .32875, 1846: .3375, 1847: .36, 1848: .33,
         1849: .399, 1850: .491, 1851: .453125, 1852: .68167, 1853: .58125, 1854: .59625, 1855: .713, 1856: .795, 1857: .7325,
         1858: .54, 1859: .485, 1860: .495, 1861: .4425, 1862: .5933, 1863: .9525, 1864: 1.28, 1865: 1.45, 1866: 1.21}
BONE = {1839: .1825, 1840: .19, 1841: .1967, 1842: .24909, 1843: .3575, 1844: .40, 1845: .33625, 1846: .34, 1847: .30875, 1848: .254,
        1849: .318, 1850: .344, 1851: .345, 1852: .5075, 1853: .345, 1854: .392, 1855: .4525, 1856: .58, 1857: .9675, 1858: .9225,
        1859: .88, 1860: .802, 1861: .66, 1862: .82, 1863: 1.53, 1864: 1.80, 1865: 1.71, 1866: 1.37}
GAL = 31.5
# 1848〜58年に帰った船で値段をそろえるときの固定の値（1851〜55年の平均）
FIXED = tuple(float(np.mean([d[y] for y in range(1851, 1856)])) for d in (SPERM, WHALE, BONE))
# Abbott の未熟練の工場労働者（月の賃金。日給×25日。Davis ほか1990 の65〜67ページの表の Panel C をページの画像で確認）
FACTORY = {1840: 16.00, 1841: 15.75, 1842: 17.25, 1843: 16.25, 1844: 16.00, 1845: 15.50, 1846: 19.00, 1847: 16.88, 1848: 17.50, 1849: 18.75,
           1850: 20.00, 1851: 18.75, 1852: 18.88, 1853: 19.25, 1854: 19.50, 1855: 19.75, 1856: 21.25, 1857: 21.25, 1858: 20.38}
# 同書 表5.8 Panel D（未熟練の船員＝食事の下限つき ÷ 陸。1840〜56年）の平均
RATIO = {"未熟練（北東部）": 49, "繊維工場": 79, "未熟練の工場": 68, "日雇い": 54}
LOSS = {"L", "M", "A", "B", "C", "S"}
MON = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
NAMES = ["北の海", "太平洋", "インド洋", "大西洋"]
EXCLUDE = {"AV00256", "AV02776"}


def food_month(y, hi):
    """その年の金額での船の食事の値打ち（月）。p.200 注47 の2つの時期を年で直線につなぐ"""
    a, b = (6.0, 8.0) if hi else (3.5, 4.7)
    return float(np.interp(y, [1841.5, 1856.5], [a, b]))


def rows(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def when(s):
    m = re.match(r"^(\d{4}) ([A-Z][a-z]{2})(?: (\d{1,2}))?", s.strip())
    if not m or m.group(2) not in MON:
        return None
    return int(m.group(1)) * 12 + MON[m.group(2)] - 1 + (int(m.group(3)) - 1 if m.group(3) else 14) / 30.44


def num(s):
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return None


def ground(s):
    s = s.lower()
    if any(w in s for w in ["arctic", "bering", "okhotsk", "ochotsk", "kamchatka", "n pacific", "north pacific"]):
        return "北の海"
    if any(w in s for w in ["indian", "desolation", "kerguelen", "crozet"]):
        return "インド洋"
    if any(w in s for w in ["pacific", "south sea", "japan", "off shore", "new zealand"]):
        return "太平洋"
    if any(w in s for w in ["atlantic", "western islands", "brazil", "patagonia", "hatteras", "cape verde"]):
        return "大西洋"
    return ""


def price(y):
    y = min(max(int(y), 1839), 1866)
    return SPERM[y], WHALE[y], BONE[y]


def load():
    seen = {}
    for r in rows(DATA / "voyages/AmericanOffshoreWhalingVoyages/voyages_20260619.txt"):
        k = r["voyageID"]
        if k not in seen or int(r["voyageRank"] or 9) < int(seen[k]["voyageRank"] or 9):
            seen[k] = r
    voy = {}
    for k, r in seen.items():
        y = num(r["yearOut"])
        yi = num(r["yearIn"])
        a, b = when(r["dayOut"]), when(r["dayIn"])
        m = b - a if a is not None and b is not None and b > a else None
        s, o, w = num(r["sperm"]), num(r["oil"]), num(r["bone"])
        voy[k] = dict(id=k, y=y, yi=yi, m=m if m and 6 <= m <= 120 else None, g=ground(r["ground"]), s=s, o=o, w=w,
                      nb="New Bedford" in r["port"], rc=r["returnCode"].strip().replace("?", "").replace("prob", "").strip(),
                      has=(s is not None or o is not None) and k not in EXCLUDE)
    return voy


def value(v, fixed=False):
    p = FIXED if fixed else price(int(v["yi"]) if v["yi"] else int(v["y"]) + 3)
    return (v["s"] or 0) * GAL * p[0] + (v["o"] or 0) * GAL * p[1] + (v["w"] or 0) * p[2]


def months(v, approx):
    if v["m"]:
        return v["m"]
    if approx and v["yi"] and v["yi"] > v["y"]:
        return 12 * (v["yi"] - v["y"])
    return None


def q(x, ps=(0, 10, 50, 90, 100)):
    return [round(float(np.percentile(x, p)), 2) for p in ps]


def main():
    rng = np.random.default_rng(SEED)
    voy = load()
    mid = [v for v in voy.values() if v["nb"] and v["y"] and 1840 <= v["y"] <= 1858]
    L = ["# 捕鯨船ロングの数字（sims/whaling_model.py の出力・2026-11-06）", "",
         f"乱数の種 {SEED}。金額はすべて当時の金額（Davis, Gallman & Gleiter 1997 表9A の CATCHVAL 列）。", ""]
    L += ["## データの大きさ", f"- 航海の記録 {len(voy):,}件（重複を除く）。ニューベッドフォード1840〜58年に出た船 {len(mid):,}航海。",
          f"- 帰港の月まで分かる6か月以上の航海（同じ範囲） {sum(1 for v in mid if v['m']):,}航海。", ""]

    # 船の最後
    rc = collections.Counter(v["rc"] for v in mid)
    lm = sum(v["rc"] in {"L", "M"} for v in mid)
    lost = sum(v["rc"] in LOSS for v in mid)
    idx = rng.integers(0, len(mid), N)
    draw = sum(mid[i]["rc"] in LOSS for i in idx)
    L += ["## 帰らない船（分母は航海の数）", f"- 分母 {len(mid):,}航海。記号の内訳 {dict(rc)}",
          f"- 沈没・行方不明だけ {lm}航海（{lm / len(mid):.1%}）。廃船・焼失・放棄・拿捕を足すと {lost}航海（{lost / len(mid):.1%}）。",
          f"- 1万回引くと帰らない船に当たるのは {draw:,}回。", ""]

    # 新米の契約を引く
    gh = []
    for c in rows(DATA / "crew/AmericanOffshoreWhalingCrewlists/crewlists_20260619.txt"):
        if "green" not in c["rank"].lower():
            continue
        mm = re.match(r"^\s*1\s*[/-]\s*(\d+(?:\.\d+)?)", c["lay"])
        v = voy.get(c["voyageID"])
        if mm and v and v["nb"] and v["y"] and 1840 <= v["y"] <= 1858 and 100 <= float(mm.group(1)) <= 400:
            gh.append((float(mm.group(1)), v))
    use = [(a, v) for a, v in gh if v["m"] and v["has"]]
    idx = rng.integers(0, len(use), N)
    W = np.array([value(use[i][1]) / use[i][0] / use[i][1]["m"] for i in idx])
    T = np.array([value(use[i][1]) / use[i][0] for i in idx])
    M = np.array([use[i][1]["m"] for i in idx])
    lay_all = np.array([a for a, _ in gh])
    L += ["## 新米の1万回（実際の新米の契約を引く）",
          f"- 取り分が読める新米 {len(gh):,}人。月数と獲れ高もそろうのは {len(use):,}人・{len({v['id'] for _, v in use})}航海。",
          f"- 取り分の分母 10%・中央・90%: {q(lay_all, (10, 50, 90))}",
          f"- 航海の月数 最短/10%/中央/90%/最長: {q(M)}", f"- 手にする額（ドル）: {q(T)}", f"- 月給（ドル）: {q(W)}",
          f"- 手にする額が0ドルの回 {int((T == 0).sum())}回（/1万回）。", ""]

    # 読み方を変える
    F = np.array([np.mean([FACTORY[min(max(int(use[i][1]["y"]) + k, 1840), 1858)] for k in range(int(use[i][1]["m"] // 12) + 1)]) for i in idx])
    LAND = F * M
    Y = np.array([use[i][1]["y"] + use[i][1]["m"] / 24 for i in idx])
    FOOD_LOW = np.array([food_month(y, False) for y in Y]) * M
    FOOD_HIGH = np.array([food_month(y, True) for y in Y]) * M
    L += ["## 陸と比べる（当時の金額・同じ月数・同じ出港年）",
          f"- 新米の同じ月数を、未熟練の工場で働いた場合（日給×25日）の中央値 ${np.median(LAND):.0f}、新米の手取りの中央値 ${np.median(T):.0f}。",
          f"- 新米の手取りが工場を上回った回 {int((T > LAND).sum()):,}回（/1万回）。",
          f"- 船の食事の値打ち（同書 p.200 注47 の各年の金額）の中央値 ${np.median(FOOD_LOW):.0f}〜${np.median(FOOD_HIGH):.0f}。足した手取りの中央値 ${np.median(T + FOOD_LOW):.0f}〜${np.median(T + FOOD_HIGH):.0f}。",
          f"- 食事の下限を足しても工場を上回った回 {int((T + FOOD_LOW > LAND).sum()):,}回、上限を足すと {int((T + FOOD_HIGH > LAND).sum()):,}回（/1万回）。",
          f"- 同書 表5.8 の比（新米の階級＝食事の下限つき ÷ 陸、1840〜56年の平均）: {RATIO}。どの年も100未満。", ""]
    L += ["## 取り分と月給（1848〜58年に出た船・読み方4通り）", "読み方ごとに 航海数／平均／中央値。", ""]
    period = [v for v in mid if 1848 <= v["y"] <= 1858 and v["has"]]
    lays = {}
    for name in NAMES:
        x = [a for a, v in gh if v["g"] == name and 1848 <= v["y"] <= 1858]
        lays[name] = float(np.mean(x)) if x else None
    L.append(f"- 新米の取り分の平均（分母） {[(n, round(lays[n], 1) if lays[n] else None, sum(1 for a, v in gh if v['g'] == n and 1848 <= v['y'] <= 1858)) for n in NAMES]}")
    keep = True
    for approx, fixed, label in [(False, False, "月まで分かる船・その頃の値段"), (False, True, "月まで分かる船・同じ値段"),
                                 (True, False, "年の差で補う・その頃の値段"), (True, True, "年の差で補う・同じ値段")]:
        res = {}
        for name in NAMES:
            ws = [value(v, fixed) / lays[name] / months(v, approx) for v in period if v["g"] == name and months(v, approx)]
            res[name] = (len(ws), round(float(np.mean(ws)), 2), round(float(np.median(ws)), 2))
        L.append(f"- {label}: {res}")
        for other in ("太平洋", "インド洋"):
            keep = keep and res["北の海"][1] > res[other][1] and res["北の海"][2] > res[other][2]
        A = [value(v, fixed) / lays["北の海"] / months(v, approx) for v in period if v["g"] == "北の海" and months(v, approx)]
        B = [value(v, fixed) / lays["太平洋"] / months(v, approx) for v in period if v["g"] == "太平洋" and months(v, approx)]
        a = np.array(A)[rng.integers(0, len(A), N)]
        b = np.array(B)[rng.integers(0, len(B), N)]
        L.append(f"  - 1隻ずつ引いて北の海が太平洋より高い回 {int((a > b).sum()):,}回（/1万回）")
    L += ["", f"**読み方4通りのすべてで、北の海の平均と中央値が太平洋・インド洋より高いか: {keep}**", "",
          "- 大西洋は1848〜58年の航海が少なく（上の航海数）、順番が読み方で変わるので、逆転の話には使わない。", ""]

    # 漁場ごとの帰らない船
    L += ["## 漁場ごとの帰らない船（1848〜58年に出た船・分母は航海の数）"]
    for name in NAMES:
        d = [v for v in mid if v["g"] == name and 1848 <= v["y"] <= 1858]
        n = sum(v["rc"] in LOSS for v in d)
        L.append(f"- {name}: {n}/{len(d)}航海（{n / len(d):.1%}）")
    L.append("")

    # 出港年
    L += ["## 同書 表5.6（当時の金額・未熟練の船員の月給の平均 $8.22）との照合と、出港の時期ごと（年の差で補う・その頃の値段・取り分1/185）"]
    for a, b in [(1840, 1843), (1844, 1847), (1848, 1851), (1852, 1855), (1856, 1858)]:
        ws = [value(v) / 185 / months(v, True) for v in mid if v["has"] and a <= v["y"] <= b and months(v, True)]
        L.append(f"- {a}〜{b}年: {len(ws)}航海 平均{np.mean(ws):.2f} 中央{np.median(ws):.2f}")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
