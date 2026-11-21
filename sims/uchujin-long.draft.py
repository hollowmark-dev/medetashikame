"""uchujin-long（宇宙人に出会える確率は？）の計算の試し（下書き・2026-10-25）。

前工程のための試算。絵や声は作らない。幅はすべて仮定（事実確認で置き直す）。
ドレイクの式 N = R* × fp × ne × fl × fi × fc × L を、値の幅の中で1万回選び直す。
幅の取り方は、2018年の Sandberg・Drexler・Ord「Dissolving the Fermi Paradox」の表1と同じ（事実確認 2026-10-25）。
実行: python -X utf8 sims/uchujin-long.draft.py
"""
import numpy as np

N_RUN = 10_000
rng = np.random.default_rng(20261114)


def logu(lo, hi, n=N_RUN):
    return 10 ** rng.uniform(np.log10(lo), np.log10(hi), n)


def draw():
    R = logu(1, 100)            # 星が1年に生まれる数
    fp = logu(0.1, 1)           # 惑星を持つ星の割合
    ne = logu(0.1, 1)           # 1つの星のまわりで、生命が住めそうな惑星の数
    # 生命が生まれる確率: fl = 1 - exp(-λVt)。λVt は Sandberg ほか(2018)と同じく、桁（log10）が標準偏差50の正規分布（真ん中は1）
    lam = 10 ** np.clip(rng.normal(0, 50, N_RUN), -300, 300)
    fl = -np.expm1(-lam * 1.0)       # 1 - exp(-λt)。小さい λ でも 0 に丸めない
    fi = logu(1e-3, 1)          # 知的な生命になる割合
    fc = logu(1e-2, 1)          # 電波などで通信できる文明になる割合
    L = logu(1e2, 1e10)         # 通信できる文明が続く年数
    return dict(R=R, fp=fp, ne=ne, fl=fl, fi=fi, fc=fc, L=L)


def nearest_ly(N):
    """銀河を直径10万光年・厚さ1000光年の円盤とみなし、N個がばらばらにいるときの、いちばん近い文明までのおよその距離"""
    V = np.pi * 50_000 ** 2 * 1_000
    return np.where(N >= 1, (V / np.maximum(N, 1e-300)) ** (1 / 3) * 0.55, np.inf)


def main():
    d = draw()
    # 章1: それぞれの値の「幅の真ん中」で1回だけかけ算（ドレイク本人の値は一次資料で確かめられないので使わない）
    mids = {k: float(np.median(v)) for k, v in d.items()}
    N1 = float(np.prod(list(mids.values())))
    print("幅の真ん中: " + "  ".join(f"{k}={v:.3g}" for k, v in mids.items()))
    print(f"真ん中どうしで1回かけ算: N = {N1:,.0f}")
    N = d["R"] * d["fp"] * d["ne"] * d["fl"] * d["fi"] * d["fc"] * d["L"]
    print(f"1万回の真ん中 N = {np.median(N):.3g}")
    print(f"N < 1（この銀河で、いま通信できるのは私たちだけ）: {np.mean(N < 1):.1%}")
    print(f"N >= 1000: {np.mean(N >= 1000):.1%}")
    for q in (10, 25, 50, 75, 90):
        print(f"  {q}% 点: {np.percentile(N, q):.3g}")
    # どれが効くか: 答えの桁（log10 N）のばらつきのうち、その値が占める割合
    print("\nどの値がいちばん効く？（答えの桁のばらつきのうち、その値が占める割合）")
    logs = {k: np.log10(np.maximum(v, 1e-300)) for k, v in d.items()}
    tot = sum(np.var(v) for v in logs.values())
    for k, v in logs.items():
        print(f"  {k:<3} {np.var(v)/tot:6.1%}  （5〜95%の幅 {np.percentile(d[k],5):.2g}〜{np.percentile(d[k],95):.2g}）")
    # 生命が生まれやすい（fl=1）としたら
    Nfl = d["R"] * d["fp"] * d["ne"] * d["fi"] * d["fc"] * d["L"]
    print(f"\nもし生命が必ず生まれるなら（fl=1）: N<1 {np.mean(Nfl < 1):.1%}  真ん中 {np.median(Nfl):.3g}")
    # 出会える＝返事が人の一生（往復80年）のうちに来る＝40光年以内に文明がいる
    near = nearest_ly(N)
    print(f"\nいちばん近い文明が40光年以内: {np.mean(near <= 40):.2%}")
    print(f"  1,000光年以内: {np.mean(near <= 1000):.1%}")
    near_fl = nearest_ly(Nfl)
    print(f"  （fl=1 なら）40光年以内: {np.mean(near_fl <= 40):.2%}  1,000光年以内: {np.mean(near_fl <= 1000):.1%}")


if __name__ == "__main__":
    main()
