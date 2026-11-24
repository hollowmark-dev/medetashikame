"""コウテイペンギンの一生を1万回（粗い試算・2026-11-09）

数字の出どころ: research/longform_penguin_outline_2026-11-09.md の2章。選び方は0章（計算の前に固定）。
  python -X utf8 sims/penguin_rough.py
"""
import random
import statistics as st

SEED = 20261109
N = 10000
HATCH = 0.82               # 卵がふ化する割合（Labrousse et al. 2021 Biol Lett 3(a)・1983-2017 平均。本文確認済み）
CHICK = 0.65                # ふ化したヒナが巣立つ割合（同上）
FLEDGE_ALL = HATCH * CHICK  # 卵から巣立ちまで 0.533（同論文の繁殖成功 0.53 と一致。Abadi 2017 は 0.458）
JUV = 0.401                 # 巣立ち〜1年（Abadi 2017）
ADULT = 0.907               # 1歳以降の年間生存（Abadi 2017・1〜4歳も同じと仮定）
FIRST = {5: 0.22, 6: 0.32}  # その年まだ子育てしていない鳥のうち、初めて子育てする割合（7歳以降は0.32と置く）
D_HATCH, D_SEA = 70, 210    # 産卵→ふ化 約70日、産卵→海へ 約210日（12月末）


def life(rnd):
    """戻り値: (生きた日数, 死んだ段階, 子育て回数, 巣立たせたヒナ, 初めての子育ての歳)"""
    if rnd.random() > HATCH:
        return rnd.uniform(0, D_HATCH), "卵", 0, 0, None
    if rnd.random() > CHICK:
        return rnd.uniform(D_HATCH, D_SEA), "ヒナ", 0, 0, None
    if rnd.random() > JUV:
        return D_SEA + rnd.uniform(0, 365), "海に出て1年以内", 0, 0, None
    day = D_SEA + 365
    age = 1
    broods = chicks = 0
    first = None
    while True:
        # age 歳の1年（この年に子育てするかを先に決める）
        if first is None and age >= 5 and rnd.random() < FIRST.get(age, 0.32):
            first = age
        if first is not None:
            broods += 1
            chicks += rnd.random() < FLEDGE_ALL
        if rnd.random() > ADULT:
            stage = "大人" if first is not None else f"{age}歳（まだ子育て前）"
            return day + rnd.uniform(0, 365), stage, broods, chicks, first
        day += 365
        age += 1


def main():
    rnd = random.Random(SEED)
    L = [life(rnd) for _ in range(N)]
    days = [x[0] for x in L]
    med = st.median(days)
    print(f"中央値の寿命 {med:.0f}日（{med / 365:.2f}年）")
    from collections import Counter
    c = Counter(x[1] if not x[1].endswith("子育て前）") else "未成熟（1〜）" for x in L)
    for k, v in c.most_common():
        print(" ", k, v)
    print("ふ化", sum(1 for x in L if x[1] != "卵"), "海へ", sum(1 for x in L if x[1] not in ("卵", "ヒナ")),
          "1年越え", sum(1 for x in L if x[0] >= D_SEA + 365), "5歳まで", sum(1 for x in L if x[0] >= D_SEA + 365 * 5),
          "子育てした", sum(1 for x in L if x[2] > 0))
    i = min(range(N), key=lambda k: (abs(L[k][0] - med), k))
    print("中央値の1羽:", L[i][1], f"{L[i][0]:.0f}日")
    ad = [x for x in L if x[2] > 0]
    if ad:
        mb = st.median([x[2] for x in ad]); mc = st.median([x[3] for x in ad]); ml = st.median([x[0] for x in ad])
        print(f"子育てした{len(ad)}羽: 寿命中央値 {ml / 365:.1f}年・子育て {mb}回・ヒナ {mc}羽")
        print(" ヒナ0羽", sum(1 for x in ad if x[3] == 0), "最多", max(x[3] for x in ad), "初子育て歳", Counter(x[4] for x in ad).most_common(6))
    yrs = sorted(d / 365 for d in days)
    print("最長", f"{yrs[-1]:.1f}年", "20年以上", sum(1 for y in yrs if y >= 20), "30年以上", sum(1 for y in yrs if y >= 30), "40年以上", sum(1 for y in yrs if y >= 40))


if __name__ == "__main__":
    main()


def picks():
    """0章 5・6 の選び方（計算の前に固定したもの）"""
    rnd = random.Random(SEED)
    L = [life(rnd) for _ in range(N)]
    ad = [(k, x) for k, x in enumerate(L) if x[2] > 0]
    mb = st.median([x[2] for _, x in ad]); mc = st.median([x[3] for _, x in ad]); ml = st.median([x[0] for _, x in ad])
    cand = [(k, x) for k, x in ad if x[2] == mb and x[3] == mc] or [(k, x) for k, x in ad if x[2] == mb]
    k, x = min(cand, key=lambda kx: (abs(kx[1][0] - ml), kx[0]))
    print(f"大人の中央値の1羽: #{k} 候補{len(cand)}羽 寿命{x[0] / 365:.1f}年 子育て{x[2]}回 ヒナ{x[3]}羽 初子育て{x[4]}歳")
    k, x = max(ad, key=lambda kx: (kx[1][3], -kx[0]))
    print(f"ヒナ最多の1羽: #{k} 寿命{x[0] / 365:.1f}年 子育て{x[2]}回 ヒナ{x[3]}羽 初子育て{x[4]}歳")
    yrs = sorted(x[0] / 365 for x in L)
    print("上から10番目・100番目の寿命", f"{yrs[-10]:.1f}", f"{yrs[-100]:.1f}")
    # 卵から数えた中央値まわり
    for t in (D_HATCH, D_SEA, D_SEA + 365):
        print(f"産卵{t}日で生きている", sum(1 for x in L if x[0] >= t))


if __name__ == "__main__":
    picks()
