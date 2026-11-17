"""団地の抽選ロング: 本番の模型（2026-11-02）

  python -X utf8 sims/danchi_model.py          → out/danchi-long/numbers.md と data.json
出典と仮定: research/longform_danchi_outline_2026-11-02.md（第2版）

問い1  51.4倍のくじを、当たるまで1回に1つ引き続ける（この倍率が続いたら）。1万人。
問い2  選び方: 人気の団地（51.4倍）／倍率の低めの団地（16倍）／家賃の高い団地（0.4倍＝抽選なし）／
       倍率が下がる線（昭和41年 51.4倍 → 昭和45年 20倍へまっすぐ・以後20倍・年4回）で
       「すぐ申し込み続ける人」と「4年待って昭和45年から申し込む人」。
問い3  部屋の数を決めた回し方（毎回 U 部屋・毎回 U 人が新しく申し込む・申込みの山は 51.4×U 人）。
       決まり A なし／B 15回落ちた人を先に入れる／C 10回落ちたら10倍・20回落ちたら優先（昭和63年の規定）。
       優先の人が部屋より多いときは、落ちた回数の多い順。
       線: 優先に回す部屋の上限（なし／半分／3割）、あきらめる人（毎回1%・2%）。
"""
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "danchi-long"
SEED = 2026
N = 10000
RATIO = 51.4
SUBURB = 16.0      # 倍率の低めの団地: 15.6倍・17.1倍の例（昭和41〜42年・会議録の議員質問）
PRICEY = 0.4       # 家賃の高い団地: 0.2〜0.4倍（抽選なしで入れた例）
R45 = 20.0         # 昭和45年の総裁答弁「東京の都心近く約20倍」（全国平均10倍とは比べない・事実確認3）
PER_YEAR = 4       # 年4回（仮定）


def geometric(rng, ratio, n=N):
    p = min(1.0, 1.0 / ratio)
    return rng.geometric(p, size=n)


def declining(rng, start_round, n=N, max_rounds=400):
    """倍率が昭和41年の51.4倍から昭和45年（16回目）の20倍（東京の都心近く）へまっすぐ下がり、以後20倍。
    start_round 回目（1始まり、昭和41年の最初の募集＝1）から申し込み始める。戻り値は申し込んだ回数。"""
    def ratio_at(t):
        if t >= 1 + 4 * PER_YEAR:
            return R45
        return RATIO + (R45 - RATIO) * (t - 1) / (4 * PER_YEAR)
    out = np.zeros(n, int)
    alive = np.ones(n, bool)
    for k in range(max_rounds):
        t = start_round + k
        p = 1.0 / ratio_at(t)
        hit = alive & (rng.random(n) < p)
        out[hit] = k + 1
        alive &= ~hit
        if not alive.any():
            break
    out[alive] = max_rounds
    return out


def pool(rng, rule="A", U=100, ratio=RATIO, cap=None, drop=0.0, rounds=1400, burn=400, track=N):
    """部屋の数を決めた回し方。burn 回目以降に申し込んだ人を先着 track 人ぶん追い、当たるまでの回数を返す。
    あきらめた人は give_up に数える。"""
    P = int(round(ratio * U))
    A = U + int(round(drop * P))  # 毎回の新しい申込み（あきらめる人のぶんを足して、倍率を保つ）
    losses = rng.geometric(1 / ratio, size=P) - 1  # 始めの山（だいたい定常の形）
    born = -losses
    ids = np.full(P, -1)
    next_id = 0
    waits, gave = {}, 0
    pri_len = []
    for t in range(rounds):
        n = len(losses)
        win = np.zeros(n, bool)
        slots = U
        if rule == "B":
            pri = np.where(losses >= 15)[0]
        elif rule == "C":
            pri = np.where(losses >= 20)[0]
        else:
            pri = np.array([], int)
        if t >= burn:
            pri_len.append(len(pri))
        if len(pri):
            pri = pri[np.argsort(-losses[pri], kind="stable")]
            k = slots if cap is None else min(slots, int(round(U * cap)))
            take = pri[:k]
            win[take] = True
            slots -= len(take)
        cand = np.where(~win)[0]
        if rule == "B":
            cand = cand[losses[cand] < 15]
        elif rule == "C":
            cand = cand[losses[cand] < 20]
        if slots > 0 and len(cand):
            w = np.where(losses[cand] >= 10, 10.0, 1.0) if rule == "C" else np.ones(len(cand))
            pick = rng.choice(cand, size=min(slots, len(cand)), replace=False, p=w / w.sum())
            win[pick] = True
        for i in np.where(win & (ids >= 0))[0]:
            waits[ids[i]] = t - born[i] + 1
        keep = ~win
        if drop > 0:
            quit_ = keep & (rng.random(n) < drop)
            gave += int((quit_ & (ids >= 0)).sum())
            keep &= ~quit_
        losses = losses[keep] + 1
        born = born[keep]
        ids = ids[keep]
        new_ids = np.full(A, -1)
        if t >= burn and next_id < track:
            m = min(A, track - next_id)
            new_ids[:m] = np.arange(next_id, next_id + m)
            next_id += m
        losses = np.concatenate([losses, np.zeros(A, int)])
        born = np.concatenate([born, np.full(A, t + 1)])
        ids = np.concatenate([ids, new_ids])
    w = np.array([waits[i] for i in sorted(waits)])
    still = next_id - len(w) - gave
    pool.last_P = len(losses)
    return w, gave, still, (int(np.median(pri_len)) if pri_len else 0, int(max(pri_len)) if pri_len else 0)


def summ(a):
    a = np.asarray(a)
    return {
        "n": int(len(a)),
        "first": round(float((a == 1).mean()) * 100, 1),
        "median": float(np.median(a)),
        "mean": round(float(a.mean()), 1),
        "p90": float(np.percentile(a, 90)),
        "p99": float(np.percentile(a, 99)),
        "max": int(a.max()),
        "over80": round(float((a > 80).mean()) * 100, 1),
        "over30": round(float((a > 30).mean()) * 100, 1),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    d = {}
    # 問い1
    q1 = geometric(rng, RATIO)
    d["q1"] = summ(q1)
    d["q1_hist20"] = [int(((q1 >= a) & (q1 <= b)).sum()) for a, b in
                      [(1, 20), (21, 40), (41, 60), (61, 80), (81, 100), (101, 120), (121, 10 ** 9)]]
    d["q1_max_by_seed"] = [int(geometric(np.random.default_rng(s), RATIO).max()) for s in range(10)]
    # 問い2
    d["q2"] = {
        "popular": summ(q1),  # 問い1と同じ1万人（数字をそろえる）
        "suburb": summ(geometric(rng, SUBURB)),
        "pricey": summ(geometric(rng, PRICEY)),
    }
    now = declining(rng, 1)
    later = declining(rng, 1 + 4 * PER_YEAR)
    d["q2"]["decline_now"] = summ(now)
    d["q2"]["decline_wait4y"] = summ(later)
    d["q2"]["decline_wait4y_total_rounds_median"] = float(np.median(later + 4 * PER_YEAR))
    # 問い3
    q3 = {}
    for rule in "ABC":
        w, g, s, pl = pool(np.random.default_rng(SEED + 1), rule)
        q3[rule] = summ(w) | {"gave_up": g, "still": s, "pri_queue_med": pl[0], "pri_queue_max": pl[1]}
    for cap in (0.5, 0.3):
        for rule in "BC":
            w, g, s, pl = pool(np.random.default_rng(SEED + 2), rule, cap=cap)
            q3[f"{rule}_cap{int(cap * 100)}"] = summ(w) | {"gave_up": g, "still": s,
                                                          "pri_queue_med": pl[0], "pri_queue_max": pl[1]}
    for drop in (0.01, 0.02):
        for rule in "AC":
            w, g, s, pl = pool(np.random.default_rng(SEED + 3), rule, drop=drop)
            q3[f"{rule}_drop{int(drop * 100)}"] = summ(w) | {"gave_up": g, "still": s}
    d["q3"] = q3
    (OUT / "data.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    L = ["# 団地の抽選ロング 本番の数字（sims/danchi_model.py・種 %d・1万人）" % SEED, ""]
    q = d["q1"]
    L += ["## 問い1 51.4倍のくじを引き続けたら（この倍率が続いたら・回で数える）",
          f"- 1回目で当たった: 100人に{q['first']}人（約50人に1人）",
          f"- 中央値: {q['median']:.0f}回目　平均: {q['mean']}回",
          f"- 10人に1人は {q['p90']:.0f}回以上／100人に1人は {q['p99']:.0f}回以上",
          f"- 80回を超えた人: 100人に{q['over80']}人（5人に1人）／30回を超えた人: 100人に{q['over30']}人",
          f"- いちばん運の悪い人: {q['max']}回（種0〜9で {min(d['q1_max_by_seed'])}〜{max(d['q1_max_by_seed'])}回と動く。声では言わない）",
          f"- 20回ごとの人数（1万人）: {d['q1_hist20']}（1〜20・21〜40・…・101〜120・121〜）", ""]
    q2 = d["q2"]
    L += ["## 問い2 どこに・いつ申し込む？",
          f"- 人気の団地（51.4倍）: 中央値 {q2['popular']['median']:.0f}回／10人に1人は {q2['popular']['p90']:.0f}回以上／1回目 100人に{q2['popular']['first']}人",
          f"- 倍率の低めの団地（16倍）: 中央値 {q2['suburb']['median']:.0f}回／10人に1人は {q2['suburb']['p90']:.0f}回以上／1回目 100人に{q2['suburb']['first']}人",
          f"- 家賃の高い団地（仮定: 1倍未満で抽選なし・大阪などの例）: 全員1回目",
          f"- 倍率が下がる線（51.4倍→昭和45年 東京の都心近く20倍へまっすぐ・年4回と仮定）で、昭和41年からすぐ申し込み続ける: 中央値 {q2['decline_now']['median']:.0f}回（年4回なら約{q2['decline_now']['median'] / 4:.1f}年）／10人に1人は {q2['decline_now']['p90']:.0f}回以上",
          f"- 4年待って昭和45年から申し込む: 申し込んでから中央値 {q2['decline_wait4y']['median']:.0f}回／昭和41年から数えると中央値 {q2['decline_wait4y_total_rounds_median']:.0f}回ぶん（約{q2['decline_wait4y_total_rounds_median'] / 4:.1f}年）", ""]
    L += ["## 問い3 部屋の数を決めて回す（毎回100部屋・申込み5,140人・51.4倍のまま）",
          "| 決まり | 1回目で当たる | 中央値 | 平均 | 10人に1人は | 100人に1人は | 最長 | 優先の列（中央値/最大） | あきらめ |",
          "|---|---|---|---|---|---|---|---|---|"]
    names = {"A": "A なし", "B": "B 15回で先に入れる", "C": "C 10回で10倍・20回で優先",
             "B_cap50": "B・優先は部屋の半分まで", "C_cap50": "C・優先は部屋の半分まで",
             "B_cap30": "B・優先は部屋の3割まで", "C_cap30": "C・優先は部屋の3割まで",
             "A_drop1": "A・毎回1%があきらめる", "C_drop1": "C・毎回1%があきらめる",
             "A_drop2": "A・毎回2%があきらめる", "C_drop2": "C・毎回2%があきらめる"}
    for k, v in d["q3"].items():
        pq = f"{v.get('pri_queue_med', '')}/{v.get('pri_queue_max', '')}" if "pri_queue_med" in v else "-"
        L.append(f"| {names[k]} | 100人に{v['first']}人 | {v['median']:.0f}回 | {v['mean']}回 | {v['p90']:.0f}回 | "
                 f"{v['p99']:.0f}回 | {v['max']}回 | {pq} | {v['gave_up']}人 |")
    L += ["", "（あきらめた人は、当たるまでの回数に入らない。平均・中央値は当たった人だけ。上限ありの線で「まだ待っている人」がいれば still に出る）"]
    L += [f"- 申込みの山の大きさ（計算の終わり）は、どの線も 5,140人前後（倍率51.4倍を保つ）"]
    L += [f"- still（追った1万人のうち、計算の終わりにまだ当たっていない人）: " +
          ", ".join(f"{names[k]} {v['still']}人" for k, v in d["q3"].items())]
    L += ["", "## 問い3で言い切ってよいこと（どの線でも崩れない）",
          "- 部屋の数は決まりで増えない。毎回100部屋なら、毎回100人しか入れない（当たる人の数はどの決まりでも同じ）。",
          "- あきらめる人がいなければ、平均の待ちはどの決まりでも約51回（51.1〜51.5回）。",
          "- あきらめる人を混ぜても、あきらめる人の数は決まりでほとんど変わらない（毎回1%: A 3,419人・C 3,447人）。",
          "- 決まりが変えるのは「誰が、いつ入るか」だけ。",
          "## 線しだいで動くので、声で言い切らないこと",
          "- 優遇の決まりのもとでの中央値（上限なし51回、上限つきで9〜88回）。札で「決まりの細かさで大きく変わる」と1回だけ。",
          "- 「1回目で当たる人がいなくなる」は、優遇に部屋を全部回せる場合だけ。言うなら条件を付ける。",
          "- いちばん運の悪い人の回数（種で動く）。"]
    (OUT / "numbers.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
