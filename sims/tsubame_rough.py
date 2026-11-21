"""ツバメの一生を1万回（粗い試算・2026-11-08）。数字の出どころは research/longform_tsubame_outline_2026-11-08.md の表。
  python -X utf8 sims/tsubame_rough.py
中央値の1羽の選び方は、この試算を回す前にアウトラインに書いて固定した（関所: 結果を見てから選ばない）。
"""
import random
import statistics as st
from collections import Counter

N = 10_000
SEED = 20261108

# ---- 数字（出どころ）----
NEST_PLACE = [("一戸建ての家・お店", 0.60), ("そのほかの建物（駅・工場・牛舎など）", 0.39), ("建物でない所", 0.01)]   # 環境省1997 日本
UNDER_EAVES = 0.70          # 建物の巣のうち軒・ひさしの下（環境省1997 日本）
CLUTCH_MEAN, CLUTCH_SD, CLUTCH_MIN, CLUTCH_MAX = 4.55, 0.76, 2, 9   # BTO 英国
NEST_FAIL = 0.214           # 日本野鳥の会 2013-15 都市23.0%・郊外農村19.8% のおよその間（「失敗」の定義は不明→巣ごと全滅として扱う）
EGG_TO_FLEDGE_OK = 0.88     # 失敗しなかった巣で、卵1個が巣立つ割合 = 日本の巣立ち数 約4（野鳥の会）÷ 英国の産卵数 4.55（混ぜた値）
POST_FLEDGE_3W = 0.32       # スイス
FIRST_NONBREED = 0.507      # スイス（渡り中は著者の仮定）
ADULT_NONBREED = 0.490      # スイス
ADULT_BREED = 0.475 / 0.490 # スイスの成鳥の年間生存率 0.475 から（繁殖期の生存）
TWO_BROODS = 0.80           # スイス
INCUB, NESTLING = 14, 20    # 抱卵13〜14日・巣立ちまで17〜22日（北海道 大樹町）
YEAR = 365


def clutch(rng):
    while True:
        k = round(rng.gauss(CLUTCH_MEAN, CLUTCH_SD))
        if CLUTCH_MIN <= k <= CLUTCH_MAX:
            return k


def pick(rng, table):
    u, acc = rng.random(), 0.0
    for name, p in table:
        acc += p
        if u < acc:
            return name
    return table[-1][0]


def brood_fledged(rng):
    """成鳥の1回の子育てで巣立つヒナの数"""
    k = clutch(rng)
    if rng.random() < NEST_FAIL:
        return 0
    return sum(rng.random() < EGG_TO_FLEDGE_OK for _ in range(k))


def one(rng):
    b = {"place": pick(rng, NEST_PLACE), "eaves": rng.random() < UNDER_EAVES, "sex": rng.choice("オス メス".split()),
         "clutch": clutch(rng)}
    b["order"] = rng.randint(1, b["clutch"])
    b["broods"], b["kids"], b["stage"], b["log"] = 0, 0, "", []
    egg_period = INCUB + NESTLING
    if rng.random() < NEST_FAIL:
        b.update(days=rng.uniform(0, egg_period), stage="巣ごと失敗（卵・ヒナ）")
        return b
    if rng.random() >= EGG_TO_FLEDGE_OK:
        b.update(days=rng.uniform(0, egg_period), stage="巣立てず（卵・ヒナ）")
        return b
    t = egg_period
    if rng.random() >= POST_FLEDGE_3W:
        b.update(days=t + rng.uniform(0, 21), stage="巣立って3週間以内")
        return b
    t += 21
    nonbreed_len = 300   # 8月〜翌4月ごろ（渡り・冬・渡り）をおよそ300日
    if rng.random() >= FIRST_NONBREED:
        b.update(days=t + rng.uniform(0, nonbreed_len), stage="最初の渡り・冬（1年目）")
        return b
    t += nonbreed_len
    age = 1
    while True:
        # 繁殖期（約4か月）
        if rng.random() >= ADULT_BREED:
            b.update(days=t + rng.uniform(0, 120), stage=f"{age}歳の子育ての季節")
            return b
        n = 2 if rng.random() < TWO_BROODS else 1
        b["broods"] += n
        ks = [brood_fledged(rng) for _ in range(n)]
        b["kids"] += sum(ks)
        b["log"].append((age, ks))
        t += 120
        if rng.random() >= ADULT_NONBREED:
            b.update(days=t + rng.uniform(0, YEAR - 120), stage=f"{age}歳の渡り・冬")
            return b
        t += YEAR - 120
        age += 1


def main():
    rng = random.Random(SEED)
    birds = [one(rng) for _ in range(N)]
    days = sorted(b["days"] for b in birds)
    med_days = (days[N // 2 - 1] + days[N // 2]) / 2
    stage_ct = Counter(b["stage"] for b in birds)
    print(f"1万個の卵: 巣立った {sum(b['days'] > 34 for b in birds)}・3週間を越えた {sum(b['days'] > 55 for b in birds)}・翌春戻った {sum(b['days'] > 355 for b in birds)}")
    print(f"寿命の中央値 {med_days:.1f}日（産卵から）・最長 {days[-1] / YEAR:.1f}年")
    for s_, c in stage_ct.most_common():
        print(f"  {s_}: {c}")
    # 中央値の1羽（選び方はアウトラインで固定）: 寿命が中央値に最も近い段階の鳥の中から、属性の最頻・中央値に合う1羽
    med_stage = min(birds, key=lambda b: abs(b["days"] - med_days))["stage"]
    pool = [b for b in birds if b["stage"] == med_stage]
    mode = lambda key: Counter(b[key] for b in birds).most_common(1)[0][0]
    want = {"place": mode("place"), "eaves": mode("eaves"), "sex": mode("sex"), "clutch": mode("clutch")}
    pool2 = [b for b in pool if all(b[k] == v for k, v in want.items())]
    med_order = st.median_low([b["order"] for b in birds])
    pool3 = [b for b in pool2 if b["order"] == med_order] or pool2
    one_ = min(pool3, key=lambda b: abs(b["days"] - med_days))
    print("中央値の1羽:", want, "何番目", med_order, "→", one_["stage"], f"{one_['days']:.0f}日")
    # 翌春戻った鳥だけの中央値（これも事前に固定した2つ目の物差し）
    back = [b for b in birds if b["days"] > 355]
    if back:
        bd = sorted(b["days"] for b in back)
        print(f"戻った {len(back)} 羽: 寿命の中央値 {st.median(bd) / YEAR:.2f}年・子育て回数の中央値 {st.median(b['broods'] for b in back)}・巣立たせたヒナの中央値 {st.median(b['kids'] for b in back)}・最多 {max(b['kids'] for b in back)}羽・最長 {bd[-1] / YEAR:.1f}年")
        # 春まで生きた鳥の中央値の1羽（アウトライン8章で固定した選び方）
        mb, mk, ml = st.median(b["broods"] for b in back), st.median(b["kids"] for b in back), st.median(bd)
        cand = [b for b in back if b["broods"] == mb and b["kids"] == mk] or [b for b in back if b["broods"] == mb]
        o = min(cand, key=lambda b: abs(b["days"] - ml))
        print(f"  春まで生きた中央値の1羽: {o['place']}・軒下={o['eaves']}・{o['sex']}・{o['clutch']}個の{o['order']}番目・子育て {o['log']}・{o['stage']}・{o['days'] / YEAR:.2f}年（{o['days']:.0f}日）・候補 {len(cand)} 羽")
        kc = Counter(min(b["kids"], 20) for b in back)
        print("  巣立たせたヒナの数の分布（20以上はまとめ）:", sorted(kc.items()))
    allk = [b["kids"] for b in birds]
    print(f"1万個の卵から、次の世代のヒナ: 合計 {sum(allk)}（1個あたり {sum(allk) / N:.2f}）")
    # 確かめ: 成鳥1羽あたり年の巣立ち数（スイス 3.06）
    rng2 = random.Random(1)
    per_pair = st.mean(sum(brood_fledged(rng2) for _ in range(2 if rng2.random() < TWO_BROODS else 1)) for _ in range(20000))
    print(f"確かめ: つがい1組の年の巣立ち数 約{per_pair:.2f}（スイス 6.12）")


if __name__ == "__main__":
    main()
