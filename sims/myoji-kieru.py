"""1,000の名字は、何年で1つになる？ 名字の「でたらめな引き継ぎ」を1万回。— 2026-10-31 作成（公開予定 11.12・ナレーションなし・45秒前後）

くらべるのは「1,000の名字が、たった1つの名字になるまでにかかる年数 T」。

【計算の前に固定した条件】（この下の数字は 1万回を回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  始まり  : 1,000の家。1家＝1つの名字（すべて別の名字。A家・B家…の記号）。
  家の数  : 世代がかわっても 1,000 のまま（一定）。
  引き継ぎ: 次の世代の1,000家は、それぞれ 前の世代の1,000家のどれか1つを でたらめに（同じ確率で・たがいに独立に）えらび、その家の名字を引き継ぐ。
           （Wright–Fisher 型。遺伝的浮動の「中立モデル」と同じ。どの名字も 有利・不利はない）
           名字ごとの家の数 (c1..ck) から次の世代の家の数を作るには、多項分布 Multinomial(1000, c/1000) を1回ひく（家を1つずつ数えるのと同じ結果）。
  1代     : 30年（仮定。Wang ほか 2023 の推定は 全期間の平均 26.9年・父30.7年／母23.2年。日本の近代以降の平均とは限らない）。
  終わり  : 名字が 1つだけ になった世代 = T 代。年数 = T × 30。
  しないこと: 結婚での改姓・養子・婿養子・新しい名字の誕生（改名・分家・帰化など）・家ごとの子の数のちがい・移住は モデルに入れない。
           （入れない理由: 出典で確かめられる値がなく、置き方で答えが決まってしまうため。画面では「計算での見立て」と言う）

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  1万回の T（年数）の中央値（1万回を小さい順に並べた ちょうど5,000番目と5,001番目の平均）を T_med とする。
  T_med < 1,000年 → 数百年で ／ 1,000年 ≤ T_med < 10,000年 → 数千年で ／ T_med ≥ 10,000年 → 数万年以上かかる

【あわせて出す数字】
  ・いちばん早い回・いちばん遅い回の T（年数）
  ・理論の見込み: 1つになるまでの平均は 約 2N 代（N=1,000 → 約2,000代 ≒ 6万年）。Kingman の合祖（coalescent）の近似 2N(1−1/N)。
    別の書き方（合祖の独立な計算 = 「2本の系統が1代で出会う確率 1/N」から作る待ち時間の合計）で 中央値を 照合する。
  ・ひねり: 「では、300年後（10代後）には、いくつ残る？」＝ 1・3・10・30・100代後に残っている名字の数（1万回の中央値）。
    10代後の いちばん大きい名字の家の数（中央値）も出す。

問い: 「1,000の名字は、/ 何年で / 1つになる？」
      選択肢: 数百年で ／ 数千年で ／ 数万年以上かかる（この順・並びは崩さない。見込みの答えは C）
見せ方: 見本の1回（1万回の中の1回そのもの）→ 1万回の T をヒストグラムに積む →「中央値は○年・いちばん早い回は・遅い回は」
ひねり: 「では、300年後（10代後）には、いくつ残る？」
締め: 「あなたの名字は、身近に何人いますか？」
言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。画面に「計算での見立て」を小さく1回。実在の名字は出さない（A家・B家…）。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "myoji-kieru"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_RUN = 10000
SEED_MAIN = 20261112
N_FAM = 1000                                          # 家の数（一定）= 最初の名字の数
GEN_YEARS = 30                                        # 1代 = 30年（仮定）
Y_HUNDRED, Y_TENTHOUSAND = 1000, 10000                # 答えの決め方のしきい値（年）
CK_GENS = (1, 2, 3, 5, 10, 20, 30, 50, 100, 200, 300, 500, 1000)    # 残っている名字の数を記録する世代
CK10 = CK_GENS.index(10)


def answer_by_rule(t_med_years):
    """T（年数）の中央値 → 'hundreds'（数百年で）/'thousands'（数千年で）/'tenthousands'（数万年以上かかる）"""
    if t_med_years < Y_HUNDRED:
        return "hundreds"
    if t_med_years < Y_TENTHOUSAND:
        return "thousands"
    return "tenthousands"


def step(rng, ids, cnt, n):
    """1世代すすめる。ids=残っている名字の番号, cnt=その名字の家の数（合計 n）。戻り値は 新しい (ids, cnt)"""
    k = len(ids)
    if k == 2:
        a = int(rng.binomial(n, cnt[0] / n))
        if a == 0:
            return ids[1:], np.array([n], np.int64)
        if a == n:
            return ids[:1], np.array([n], np.int64)
        return ids, np.array([a, n - a], np.int64)
    c = rng.multinomial(n, cnt / n)
    keep = c > 0
    return ids[keep], c[keep].astype(np.int64)


def run_one(rng, rec_gens=None):
    """1回: 1,000の名字から 1つになるまで。戻り値: T（代）, 記録した世代の名字の数 (CK_GENS), 10代後のいちばん大きい名字の家の数,
    rec_gens を渡せば その世代の状態 {世代: (ids, cnt)}（見本の絵用。同じ乱数なので 数え方は同じ）"""
    ids = np.arange(N_FAM)
    cnt = np.ones(N_FAM, np.int64)
    names = np.ones(len(CK_GENS), np.int16)
    max10 = 1
    states = {}
    if rec_gens is not None and 0 in rec_gens:
        states[0] = (ids.copy(), cnt.copy())
    g = 0
    while len(ids) > 1:
        ids, cnt = step(rng, ids, cnt, N_FAM)
        g += 1
        if g in CK_GENS:
            j = CK_GENS.index(g)
            names[j] = len(ids)
            if j == CK10:
                max10 = int(cnt.max())
        if rec_gens is not None and g in rec_gens:
            states[g] = (ids.copy(), cnt.copy())
    return g, names, max10, states


def run_many(seed, n):
    T = np.zeros(n, np.int32)
    names = np.zeros((n, len(CK_GENS)), np.int16)
    max10 = np.zeros(n, np.int16)
    for h in range(n):
        T[h], names[h], max10[h], _ = run_one(np.random.default_rng([seed, h]))
    return dict(T=T, names=names, max10=max10)


def coalescent_T(seed, n, big_n=N_FAM):
    """別の書き方（Kingman の合祖・連続時間の近似）: k本の系統が 1本減る（どれか2本が同じ親を持つ）までの待ち時間は
    平均 N / (k(k−1)/2) 代の指数分布。k = N, N−1, …, 2 の待ち時間をたして T を作る。WF の 1代ごとの多項分布は使わない"""
    rng = np.random.default_rng(seed)
    ks = np.arange(2, big_n + 1)
    rate = ks * (ks - 1) / 2.0 / big_n                  # 1代あたり 合流が起こる率
    T = np.zeros(n)
    for i in range(n):
        T[i] = rng.exponential(1.0 / rate).sum()
    return T


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万回。計算には数分かかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"runs_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        main = {k: z[k] for k in z.files}
    else:
        import time
        t0 = time.time()
        main = run_many(SEED_MAIN, N_RUN)
        print(f"  1万回 {time.time() - t0:.0f}秒")
        np.savez_compressed(f, **main)
    years = main["T"].astype(np.int64) * GEN_YEARS
    med_years = float(np.median(years))
    _RES["m"] = dict(main=main, years=years, med_years=med_years, med_gen=float(np.median(main["T"])),
                     nm_med=np.median(main["names"], axis=0), max10_med=float(np.median(main["max10"])))
    return _RES["m"]


def sensitivity():
    """置き方を変えたとき 答えが動くか（情報）。名字の数（=家の数）N と 1代の年数を変える"""
    rows = []
    global N_FAM
    keep = N_FAM
    try:
        for n_ in (100, 300, 1000):
            N_FAM = n_
            nn = 800 if n_ == 1000 else 1500
            rr = [run_one(np.random.default_rng([SEED_MAIN + 5, h]))[0] for h in range(nn)]
            rows.append((n_, float(np.median(rr)), float(np.mean(rr))))
    finally:
        N_FAM = keep
    return rows


def report():
    r = results()
    m, yrs = r["main"], r["years"]
    key = answer_by_rule(r["med_years"])
    T = m["T"]
    print(f"乱数の種 {SEED_MAIN}  {N_RUN}回  名字 {N_FAM}  1代 {GEN_YEARS}年")
    print(f"  T（代）: 中央値 {r['med_gen']:.0f}  平均 {T.mean():.1f}  最小 {T.min()}  最大 {T.max()}  標準偏差 {T.std():.0f}")
    print(f"  年数: 中央値 {r['med_years']:,.0f}年 → {key}   最小 {yrs.min():,}年  最大 {yrs.max():,}年")
    qs = np.percentile(yrs, [1, 5, 25, 50, 75, 95, 99])
    print("  年数の分位 1/5/25/50/75/95/99%: " + " / ".join(f"{q:,.0f}" for q in qs))
    print(f"  1万年未満の回: {int((yrs < Y_TENTHOUSAND).sum())}回  1,000年未満の回: {int((yrs < Y_HUNDRED).sum())}回")
    print(f"  理論の見込み: 平均 2N(1−1/N) = {2 * N_FAM * (1 - 1 / N_FAM):.0f}代 ≒ {2 * N_FAM * (1 - 1 / N_FAM) * GEN_YEARS:,.0f}年  1万回の平均 {T.mean():.0f}代 = {T.mean() * GEN_YEARS:,.0f}年")
    print("  残っている名字の数（1万回の中央値 / 平均）:")
    for g_, a_, b_ in zip(CK_GENS, r["nm_med"], m["names"].mean(axis=0)):
        print(f"    {g_:>5}代後（{g_ * GEN_YEARS:>6,}年後）: {a_:6.0f} / {b_:7.1f}")
    print(f"  10代後のいちばん大きい名字の家の数: 中央値 {r['max10_med']:.0f}  最大 {int(m['max10'].max())}")


def report_sensitivity():
    print("感度（名字の数 N を変える。情報）:")
    for n_, med, mean in sensitivity():
        print(f"  N={n_:>5}: T 中央値 {med:7.0f}代 = {med * GEN_YEARS:9,.0f}年  平均 {mean:7.0f}代  → {answer_by_rule(med * GEN_YEARS)}")
    r = results()
    print("  1代の年数を変えたとき（同じ T で年数だけ）:")
    for gy in (20, 25, 30, 35):
        print(f"    1代={gy}年: 中央値 {r['med_gen'] * gy:,.0f}年  → {answer_by_rule(r['med_gen'] * gy)}   いちばん早い回 {int(r['main']['T'].min()) * gy:,}年")


# ---- MODEL END ----


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--timing" in sys.argv:
        import time
        t0 = time.time()
        run_many(SEED_MAIN, 200)
        print(f"200回 {time.time() - t0:.1f}秒")
        sys.exit(0)
    report()
    if "--nosens" not in sys.argv:
        report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す1回）を、1万回の中から選ぶ
# =====================================================================
GENS_SHOW = (0, 1, 2, 3, 5, 8, 10, 16, 25, 40, 70, 120, 200, 350, 600, 1000, 1500)   # 見本の絵で 順に見せる世代（T より前のもの。最後に T）
_SAMPLE = {}


def samples():
    """T（代）が 1万回の中央値にいちばん近い 1回。1万回の中の1回そのもの（同じ乱数でやり直して、見せる世代の状態を記録する）"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    T = r["main"]["T"]
    h = int(np.argmin(np.abs(T.astype(np.float64) - r["med_gen"])))
    Tg = int(T[h])
    gens = [g for g in GENS_SHOW if g < Tg] + [Tg]
    g_end, names, max10, states = run_one(np.random.default_rng([SEED_MAIN, h]), rec_gens=set(gens))
    _SAMPLE.update(h=h, T=Tg, gens=gens, states=states, g_end=g_end, names=names, max10=max10, med_gen=r["med_gen"])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    S = samples()
    print(f"見本: 第{S['h']}回  T={S['T']}代 = {S['T'] * GEN_YEARS:,}年（中央値 {S['med_gen']:.0f}代）  見せる世代 {S['gens']}")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import colorsys  # noqa: E402

import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, whoosh)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.12"                                  # 日付欄（公開予定日）

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は C（3番目）
LABELS = ["数百年で", "数千年で", "数万年以上かかる"]
KEY_LABEL = {"hundreds": "数百年で", "thousands": "数千年で", "tenthousands": "数万年以上かかる"}
CORRECT = 2                                          # answer_by_rule の結果の位置（C）

BIG_Q3 = ["1,000の名字は、", "何年で", "1つになる？"]          # 1コマ目の3行（同じ大きさ）
BIG_Q = ["1,000の名字は、", "何年で1つになる？"]               # 定位置（上）の2行
DETAIL_RULE = "1家＝1つの名字　1代＝30年と置く"
DETAIL = "次の代は前の代のどれかの家から引き継ぐ、という計算での見立て"

SKIN, SKIN_D = "#f4cfae", "#d9a47f"
WALL_T, WALL_B, FLOOR = "#fdf4e2", "#f6e5c6", "#dcc298"
WOOD, WOOD_D = "#d9b27c", "#a67c46"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 860.0, 620.0
CARD_X = 110.0
CARD_Y_INTRO, CARD_Y_FINAL = 850.0, 625.0
CD_X, CD_Y = 790.0, 970.0
T_FADE = 0.5                                        # 家族の絵 → 点の絵へ
HOLD0, STEP_D, XF = 1.3, 0.42, 0.2                  # 0代の見せる時間・1つの世代の見せる時間・色が変わる時間

COLS, ROWS = 40, 25
PITCH, DOT_R = 20.2, 8.2
GRID_X0, GRID_Y0 = 26.0, 64.0                       # カード内の、点の格子の左上

HB, HMAX = 1260.0, 420.0                            # ヒストグラムの底の y と 最大の高さ
HX0, HX1 = 130.0, 950.0                             # 横軸（対数）の左端と右端
Y_LO, Y_HI = 300.0, 400000.0                        # 横軸の年数の範囲
N_BIN = 36
TW_X = (215.0, 425.0, 635.0, 845.0)                  # 棒グラフの中心 x
TW_BASE, TW_H = 1085.0, 330.0
TW_GENS = (1, 10, 30, 100)


def setup():
    global T_ST, T_SEND, T_RES, T_D0, T_D1, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TS1, T_TW2, T_Q, DURATION, SCENES, N_STEP
    S = samples()
    N_STEP = len(S["gens"])
    t0 = T_GO + T_FADE
    T_ST = [t0, t0 + HOLD0]
    for _ in range(N_STEP - 2):
        T_ST.append(T_ST[-1] + STEP_D)
    T_RES = T_ST[-1] + 0.7                          # 結果の付箋
    T_SEND = T_ST[-1] + 3.4                         # 見本の場面が終わる
    T_D0 = T_SEND                                   # ヒストグラムへ
    T_D1 = T_D0 + 0.8 + 3.6                         # 棒が積み終わる
    T_DN = T_D1 + 0.1                               # 数字1（中央値）
    T_DN2 = T_DN + 3.0                              # 数字2（いちばん早い・遅い）
    T_REV = T_DN2 + 3.0                             # 答え
    T_ANS2 = T_REV + 2.8                            # 理由
    T_TW = T_ANS2 + 3.4                             # ひねり
    T_TS1 = T_TW + 0.8 + 1.8                        # 棒が伸び終わる
    T_TW2 = T_TW + 4.2                              # ひねりの答え
    T_Q = T_TW2 + 3.6                               # 締め
    DURATION = T_Q + 4.8
    SCENES = [("見本の1回（家族→点が減る）", T_GO, T_D0), ("1万回の年数（ヒストグラム・答え・理由）", T_D0, T_TW),
              ("ひねり（10代後に残る名字）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def years_jp(y):
    """51234 → '約5万1千年'（千年の位に四捨五入）"""
    y = int(round(y / 1000.0)) * 1000
    man, sen = divmod(y, 10000)
    if man == 0:
        return f"約{sen // 1000}千年"
    return f"約{man}万年" if sen == 0 else f"約{man}万{sen // 1000}千年"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, width, col, ow=2.4, a=1.0):
    """太い線（輪郭つき）。腕・脚に"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.new_path()
    for i, (px, py) in enumerate(pts):
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    ctx.set_source_rgba(*hexrgb(INK, 0.92 * a))
    ctx.set_line_width(width + 2 * ow)
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.stroke()


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ---------- 絵: 人（正面・家族。頭身と服をつけた、棒人間でない人） ----------
FAM = {
    "grandpa": dict(h=92, hair="#cfd2d8", style="bald", top="#7e9a6a", bottom="#5b6073", skirt=False, glasses=True, head=1.0, extra="vest"),
    "grandma": dict(h=86, hair="#d9dbe0", style="bun", top="#c9788d", bottom="#6c7089", skirt=True, glasses=False, head=1.0, extra="brooch"),
    "father": dict(h=100, hair="#2b2b33", style="short", top="#5b8cc7", bottom="#3d4560", skirt=False, glasses=False, head=1.0, extra="tie"),
    "mother": dict(h=95, hair="#5a3d2b", style="pony", top="#ecab55", bottom="#4f6b66", skirt=True, glasses=False, head=1.0, extra="collar"),
    "child": dict(h=66, hair="#2f2a33", style="child", top="#e8645a", bottom="#3f4a64", skirt=False, glasses=False, head=1.3, extra="star"),
}
SHOE = "#2a2f3d"


def person(ctx, x, fy, s, kind, t, look=0, wave=False, ph=0.0):
    """正面向きの人。(x, fy) は足もとの中心。100·s px が身長100の人（kind ごとに身長が違う）。look=+1 なら右（内側）、−1 なら左を見る"""
    S = FAM[kind]
    k = s * S["h"] / 100.0
    hs = S["head"]
    P = lambda dx, dy: (x + dx * k, fy + dy * k)    # noqa: E731
    lw = max(2.2, 0.75 * k)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def poly(pts, col, w=None):
        ctx.new_path()
        for i, (px, py) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(*P(px, py))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, w or lw, INK, 0.9)

    bob = 0.35 * math.sin(2.1 * t + ph)
    cy = -80.0 - 9.6 * hs + bob
    r = 9.1 * hs
    # ポニーテール（うしろ）
    if S["style"] == "pony":
        sw = 2.0 * math.sin(2.6 * t + ph)
        thick(ctx, [P(r * 0.7, cy - r * 0.5), P(r * 1.9 + sw, cy - r * 0.2), P(r * 1.9 + sw * 1.6, cy + r * 1.7)], r * 0.62 * k, S["hair"], lw)
    # 脚と くつ
    for dx in (-7.0, 7.0):
        if S["skirt"]:
            thick(ctx, [P(dx, -30), P(dx, -7)], 6.6 * k, SKIN, 2.2)
            thick(ctx, [P(dx, -13), P(dx, -6.5)], 7.6 * k, "#f6f3ea", 2.2)
        else:
            thick(ctx, [P(dx, -46), P(dx, -6)], 12.8 * k, S["bottom"], 2.4)
        sx, sy = P(dx + look * 1.4, -2.6)
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1.0, 0.52)
        ctx.arc(0, 0, 6.8 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(SHOE))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    # 胴
    ctx.new_path()
    ctx.move_to(*P(-9, -80.5))
    ctx.curve_to(*P(-14, -79.5), *P(-18.5, -78.5), *P(-18.3, -71))
    ctx.line_to(*P(-15.6, -43))
    ctx.line_to(*P(15.6, -43))
    ctx.line_to(*P(18.3, -71))
    ctx.curve_to(*P(18.5, -78.5), *P(14, -79.5), *P(9, -80.5))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(S["top"]))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    if S["skirt"]:                                                             # スカート
        bot = -22 if kind == "grandma" else -27
        poly([(-15.6, -46), (15.6, -46), (21.0, bot), (-21.0, bot)], S["bottom"], lw)
        for dx in (-9, -3, 3, 9):
            ctx.move_to(*P(dx * 0.8, -45))
            ctx.line_to(*P(dx * 1.3, bot + 0.5))
            _stroke(ctx, lw * 0.5, INK, 0.3)
    ex_ = S["extra"]
    if ex_ == "tie":
        poly([(-5.8, -80.5), (0, -66), (5.8, -80.5)], "#f6f3ea", lw * 0.8)
        poly([(-1.6, -75), (1.6, -75), (2.1, -57), (0, -54.5), (-2.1, -57)], "#c4414b", lw * 0.7)
    elif ex_ == "vest":
        poly([(-5.8, -80.5), (0, -62), (5.8, -80.5)], "#f6f3ea", lw * 0.8)
        poly([(-10, -77), (-2.5, -61), (-2.5, -43.5), (-15.6, -43.5), (-17.5, -70)], "#566b49", lw * 0.8)
        poly([(10, -77), (2.5, -61), (2.5, -43.5), (15.6, -43.5), (17.5, -70)], "#566b49", lw * 0.8)
        for by_ in (-56.0, -50.0):
            ctx.new_path()
            ctx.arc(*P(0, by_), 0.95 * k, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#e6c35a"))
            ctx.fill()
    elif ex_ == "brooch":
        poly([(-5.8, -80.5), (0, -66), (5.8, -80.5)], "#f6f3ea", lw * 0.8)
        ctx.new_path()
        ctx.arc(*P(-8.0, -70), 1.7 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#f4e29a"))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.7, INK, 0.9)
    elif ex_ == "collar":
        poly([(-7, -80.5), (0, -64), (7, -80.5)], "#fff7e6", lw * 0.8)
        poly([(-10, -77), (-3, -66), (-6.5, -61)], "#fff7e6", lw * 0.7)
        poly([(10, -77), (3, -66), (6.5, -61)], "#fff7e6", lw * 0.7)
    elif ex_ == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = 7.0 if i % 2 == 0 else 3.0
            pts.append((rr * math.cos(ang), -62 + rr * math.sin(ang)))
        poly(pts, "#ffe27a", lw * 0.7)
    # うで（そでは服の色・手は肌）
    for sg in (-1, 1):
        shx, shy = P(sg * 15.8, -74.0)
        if wave and sg == 1:
            sw = math.sin(7.0 * t + ph)
            elx, ely = P(25.0, -72.0)
            wx, wy = P(27.0 + 3.5 * sw, -90.0)
        else:
            elx, ely = P(sg * 19.8, -62.0)
            wx, wy = P(sg * 19.0, -49.5)
        thick(ctx, [(shx, shy), (elx, ely), (wx, wy)], 7.4 * k, S["top"], 2.3)
        ctx.new_path()
        ctx.arc(wx, wy, 4.0 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    # 首
    core.rrect(ctx, *P(-3.5, -83.5 + bob), 7.0 * k, 6.5 * k, 2 * k)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    # 頭（内側へ少し傾ける）
    ctx.save()
    nx, ny = P(0, -80)
    ctx.translate(nx, ny)
    ctx.rotate(look * 0.06)
    ctx.translate(-nx, -ny)
    hx, hy = P(0, cy)
    rr_ = r * k
    for sg in (-1, 1):                                                          # 耳
        ctx.new_path()
        ctx.arc(hx + sg * rr_ * 1.0, hy + rr_ * 0.1, rr_ * 0.24, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.save()                                                                  # 顔
    ctx.translate(hx, hy)
    ctx.scale(1.0, 1.08)
    ctx.arc(0, 0, rr_, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    hair = S["hair"]
    st = S["style"]
    if st == "bald":                                                            # 横だけ髪（頭のてっぺんは つるつる）
        for sg in (-1, 1):
            ctx.new_path()
            ctx.move_to(hx + sg * rr_ * 0.98, hy - rr_ * 0.55)
            ctx.curve_to(hx + sg * rr_ * 1.22, hy - rr_ * 0.45, hx + sg * rr_ * 1.2, hy + rr_ * 0.2, hx + sg * rr_ * 1.0, hy + rr_ * 0.28)
            ctx.curve_to(hx + sg * rr_ * 0.92, hy - rr_ * 0.1, hx + sg * rr_ * 0.9, hy - rr_ * 0.3, hx + sg * rr_ * 0.98, hy - rr_ * 0.55)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(hair))
            ctx.fill_preserve()
            _stroke(ctx, lw * 0.8, INK, 0.9)
        ctx.new_path()                                                          # つやのしるし
        ctx.arc(hx - rr_ * 0.3, hy - rr_ * 0.78, rr_ * 0.2, 1.1 * math.pi, 1.7 * math.pi)
        _stroke(ctx, lw * 0.7, "#ffffff", 0.8)
    else:
        low = {"short": 0.45, "pony": 0.5, "bun": 0.5, "child": 0.28}[st]       # 前髪の下がり（顔の上端からの割合）
        ctx.new_path()
        ctx.move_to(hx - rr_ * 1.06, hy - rr_ * 0.05)
        ctx.curve_to(hx - rr_ * 1.2, hy - rr_ * 1.55, hx + rr_ * 1.2, hy - rr_ * 1.55, hx + rr_ * 1.06, hy - rr_ * 0.05)
        ctx.line_to(hx + rr_ * 0.98, hy - rr_ * low)
        ctx.line_to(hx + rr_ * 0.6, hy - rr_ * (low + 0.3))
        ctx.line_to(hx + rr_ * 0.2, hy - rr_ * low)
        ctx.line_to(hx - rr_ * 0.2, hy - rr_ * (low + 0.3))
        ctx.line_to(hx - rr_ * 0.6, hy - rr_ * low)
        ctx.line_to(hx - rr_ * 0.98, hy - rr_ * (low + 0.25))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(hair))
        ctx.fill_preserve()
        _stroke(ctx, lw, INK, 0.92)
        if st == "bun":
            ctx.new_path()
            ctx.arc(hx, hy - rr_ * 1.42, rr_ * 0.4, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(hair))
            ctx.fill_preserve()
            _stroke(ctx, lw, INK, 0.92)
        if st == "child":
            poly_pts = [(hx - rr_ * 0.2, hy - rr_ * 1.28), (hx + rr_ * 0.05, hy - rr_ * 1.62), (hx + rr_ * 0.3, hy - rr_ * 1.26)]
            ctx.new_path()
            for i, (px, py) in enumerate(poly_pts):
                (ctx.move_to if i == 0 else ctx.line_to)(px, py)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(hair))
            ctx.fill_preserve()
            _stroke(ctx, lw * 0.9, INK, 0.9)
    # 目・まゆ・ほお・口
    blink = (t * 0.9 + ph) % 3.4 < 0.12
    for sg in (-1, 1):
        ex, ey = hx + sg * rr_ * 0.4 + look * rr_ * 0.15, hy + rr_ * 0.06
        if blink:
            ctx.move_to(ex - rr_ * 0.2, ey)
            ctx.line_to(ex + rr_ * 0.2, ey)
            _stroke(ctx, lw * 0.9, INK, 0.95)
        else:
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(0.78, 1.0)
            ctx.arc(0, 0, rr_ * 0.21, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()
            ctx.new_path()
            ctx.arc(ex + look * rr_ * 0.05 + rr_ * 0.05, ey - rr_ * 0.06, rr_ * 0.06, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.fill()
        brow_col = "#9aa0aa" if kind in ("grandpa", "grandma") else INK
        bx, by = ex, hy - rr_ * 0.33
        ctx.move_to(bx - rr_ * 0.22, by + rr_ * 0.04)
        ctx.line_to(bx + rr_ * 0.22, by - rr_ * 0.04)
        _stroke(ctx, lw * (1.1 if kind == "grandpa" else 0.8), brow_col, 0.85)
        ctx.new_path()
        ctx.arc(hx + sg * rr_ * 0.68 + look * rr_ * 0.12, hy + rr_ * 0.4, rr_ * 0.16, 0, 2 * math.pi)
        ctx.set_source_rgba(1.0, 0.55, 0.55, 0.34)
        ctx.fill()
    if S["glasses"]:
        for sg in (-1, 1):
            ctx.new_path()
            ctx.arc(hx + sg * rr_ * 0.4 + look * rr_ * 0.15, hy + rr_ * 0.06, rr_ * 0.31, 0, 2 * math.pi)
            _stroke(ctx, lw * 0.9, INK, 0.9)
        ctx.move_to(hx - rr_ * 0.09 + look * rr_ * 0.15, hy + rr_ * 0.03)
        ctx.line_to(hx + rr_ * 0.09 + look * rr_ * 0.15, hy + rr_ * 0.03)
        _stroke(ctx, lw * 0.8, INK, 0.9)
    mx_, my_ = hx + look * rr_ * 0.12, hy + rr_ * 0.5
    ctx.new_path()
    ctx.arc(mx_, my_ - rr_ * 0.14, rr_ * (0.3 if kind == "child" else 0.24), 0.2 * math.pi, 0.8 * math.pi)
    _stroke(ctx, lw * 0.85, INK, 0.9)
    ctx.restore()
    ctx.restore()


def plaque(ctx, cx, cy, label, size=56):
    """表札（木の板）。ひもで つるす"""
    w = core.text_width(label, size) + 64
    h = size + 40
    for sx in (-0.28, 0.28):
        ctx.move_to(cx + sx * w, cy - h / 2)
        ctx.line_to(cx + sx * 0.5 * w * 0.55, cy - h / 2 - 34)
    _stroke(ctx, 3, INK, 0.7)
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, 10)
    ctx.set_source_rgba(*hexrgb(WOOD))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    for yy in (-0.22, 0.26):
        ctx.move_to(cx - w / 2 + 14, cy + h * yy)
        ctx.curve_to(cx - w * 0.15, cy + h * yy - 4, cx + w * 0.15, cy + h * yy + 4, cx + w / 2 - 14, cy + h * yy)
        _stroke(ctx, 1.8, WOOD_D, 0.45)
    text(ctx, label, cx, cy + 2, size, INK)


def room_bg(ctx, w, h, floor_y, window=True):
    g = cairo.LinearGradient(0, 0, 0, floor_y)
    g.add_color_stop_rgb(0, *hexrgb(WALL_T)[:3])
    g.add_color_stop_rgb(1, *hexrgb(WALL_B)[:3])
    ctx.set_source(g)
    ctx.rectangle(0, 0, w, floor_y)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(FLOOR))
    ctx.rectangle(0, floor_y, w, h - floor_y)
    ctx.fill()
    ctx.move_to(0, floor_y)
    ctx.line_to(w, floor_y)
    _stroke(ctx, 3, INK, 0.45)
    for x_ in range(0, int(w), 120):                                 # 壁紙のもよう
        for y_ in range(40, int(floor_y) - 20, 90):
            ctx.arc(x_ + 60 + (45 if (y_ // 90) % 2 else 0), y_, 3.2, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#e9cfa0", 0.55))
            ctx.fill()
    if window:
        rrect(ctx, 38, 48, 120, 128, 8)
        ctx.set_source_rgba(*hexrgb("#bfe6f2"))
        ctx.fill_preserve()
        _stroke(ctx, 4, INK, 0.7)
        ctx.move_to(98, 48)
        ctx.line_to(98, 176)
        ctx.move_to(38, 112)
        ctx.line_to(158, 112)
        _stroke(ctx, 3, INK, 0.6)


def draw_family(ctx, t, x0, y0, w, h, fy, s, people, plaque_label):
    """家族の部屋。(x0, y0) は左上。people = [(kind, x, look, wave)]"""
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, w, h, 14)
    ctx.clip()
    room_bg(ctx, w, h, fy - 26, window=(plaque_label is not None))
    for kind, px, look, wave in people:
        ctx.save()
        ctx.translate(px, fy + 2)
        ctx.scale(1.0, 0.16)
        ctx.arc(0, 0, 50 if kind != "child" else 34, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0.2, 0.15, 0.08, 0.18)
        ctx.fill()
    for i, (kind, px, look, wave) in enumerate(people):
        person(ctx, px, fy, s, kind, t, look=look, wave=wave, ph=0.9 * i)
    if plaque_label:
        plaque(ctx, w / 2, 112, plaque_label)
    ctx.restore()


FAM_PEOPLE = [("grandpa", 110.0, 1, False), ("grandma", 225.0, 1, False), ("father", 420.0, 0, False),
              ("mother", 535.0, 0, False), ("child", 705.0, -1, True)]


def draw_family_card(ctx, t):
    """冒頭の家族: 祖父母 → 親 → 子。同じ名字（A家）を引き継ぐ。1代 ≒ 30年"""
    draw_family(ctx, t, 12, 12, CARD_W - 24, CARD_H - 24, 515.0, 3.3, [(k, x - 12, lk, wv) for k, x, lk, wv in FAM_PEOPLE], "A家")
    for cx_, lab in ((168.0, "祖父母"), (478.0, "親"), (705.0, "子")):
        text(ctx, lab, cx_, 570, 32, INK)
    for ax in (322.0, 620.0):                                    # 代がわりの矢印
        y_ = 432.0
        ctx.move_to(ax - 36, y_)
        ctx.line_to(ax + 36, y_)
        ctx.move_to(ax + 22, y_ - 13)
        ctx.line_to(ax + 36, y_)
        ctx.line_to(ax + 22, y_ + 13)
        _stroke(ctx, 5, RED, 0.9)
        text(ctx, "30年", ax, y_ - 30, 28, RED)
    rrect(ctx, 24, 22, 350, 60, 12)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    text(ctx, "同じ名字を引き継ぐ", 44, 52, 30, INK, align="left")


# ---------- 絵: 点の格子（1点＝1家・色＝名字） ----------
NAME_RGB = np.zeros((N_FAM, 3), np.float64)
for _j in range(N_FAM):
    _hue = (_j * 0.61803398875) % 1.0
    _sat = (0.52, 0.68, 0.84)[(_j * 7) % 3]
    _val = (0.97, 0.88, 0.78)[(_j * 5) % 3]
    NAME_RGB[_j] = colorsys.hsv_to_rgb(_hue, _sat, _val)


def slot_colors(ids, cnt):
    """名字の番号順に並べて、家の数だけ同じ色をつなぐ（1,000個の色 (1000, 3)）。名字ごとの色の かたまり"""
    order = np.argsort(ids)
    return NAME_RGB[np.repeat(ids[order], cnt[order])]


_SLOTS = {}


def slots():
    if "s" not in _SLOTS:
        S = samples()
        _SLOTS["s"] = [slot_colors(*S["states"][g]) for g in S["gens"]]
    return _SLOTS["s"]


def sample_state(t):
    """時刻 t の見本: (いまの世代の番号 i, 色 (1000,3), 残った名字の数)"""
    S = samples()
    sl = slots()
    i = 0
    while i + 1 < N_STEP and T_ST[i + 1] <= t:
        i += 1
    if i >= 1:
        u = float(smooth((t - T_ST[i]) / XF))
        col = sl[i - 1] * (1 - u) + sl[i] * u
    else:
        col = sl[0]
    ids, _ = S["states"][S["gens"][i]]
    return i, col, len(ids)


def draw_dots(ctx, col, a=1.0):
    ctx.save()
    for j in range(N_FAM):
        rr_, cc = divmod(j, COLS)
        cx, cy = GRID_X0 + (cc + 0.5) * PITCH, GRID_Y0 + (rr_ + 0.5) * PITCH
        ctx.new_path()
        ctx.arc(cx, cy, DOT_R, 0, 2 * math.pi)
        ctx.set_source_rgba(col[j, 0], col[j, 1], col[j, 2], a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.42 * a))
        ctx.set_line_width(1.4)
        ctx.stroke()
    ctx.restore()


def draw_grid_card(ctx, t, a):
    """点の格子のカード中身（カード座標）"""
    if a <= 0:
        return
    i, col, n_now = sample_state(t)
    ctx.push_group()
    fill(ctx, (*hexrgb(PAPER)[:3], 1.0))
    ctx.rectangle(0, 0, CARD_W, CARD_H)
    ctx.fill()
    text(ctx, "たとえば、この1回では", 24, 34, 32, INK, align="left")
    text(ctx, "点1つ＝1家　色＝名字", CARD_W - 44, 34, 26, PENCIL, align="right", bold=False)
    ctx.set_source_rgba(*hexrgb(INK, 0.06))
    rrect(ctx, 10, GRID_Y0 - 8, CARD_W - 20, ROWS * PITCH + 16, 10)
    ctx.fill()
    draw_dots(ctx, col)
    ly = CARD_H - 28                                     # 凡例（A家・B家…）
    x_ = 26.0
    for j, nm in enumerate(("A家", "B家", "C家")):
        ctx.new_path()
        ctx.arc(x_ + 10, ly, DOT_R + 1.5, 0, 2 * math.pi)
        ctx.set_source_rgba(*NAME_RGB[j], 1)
        ctx.fill_preserve()
        _stroke(ctx, 1.6, INK, 0.5)
        text(ctx, nm, x_ + 30, ly, 26, INK, align="left", bold=False)
        x_ += 120.0
    text(ctx, "…… 1,000の名字（家）", x_ + 4, ly, 26, PENCIL, align="left", bold=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    ctx.clip()
    fa = 1 - ease(clamp01((t - T_GO) / T_FADE))
    if fa > 0:
        ctx.push_group()
        draw_family_card(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fa)
    if t >= T_GO:
        draw_grid_card(ctx, t, ease(clamp01((t - T_GO) / T_FADE)))
    ctx.restore()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    _stroke(ctx, 3.2, INK, 0.85)
    ctx.restore()


def scene_alpha(t):
    if t < T_D0:
        return 1.0
    return 1 - ease((t - T_D0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.20 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: 場面が寄ったところから引く（下端を基準に）
    ctx.save()
    if z > 1.0:
        ctx.translate(540, 1440)
        ctx.scale(z, z)
        ctx.translate(-540, -1440)
    ctx.push_group()
    draw_card(ctx, t, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()
    if T_GO + T_FADE <= t < T_D0:                       # 数え（カードの下）
        S = samples()
        i, _col, n_now = sample_state(t)
        g_now = S["gens"][i]
        s_ = ease_out((t - T_GO - T_FADE) / 0.25)
        fade = 1 - ease((t - T_RES) / 0.3) if t >= T_RES else 1.0
        o = s_ * fade * a
        note.sticky(ctx, f"{fmt(g_now)}代目\n{fmt(g_now * GEN_YEARS)}年後", 330, 1385, 42, "mint", a=o, tilt=0.02)
        text(ctx, "残った名字", 755, 1318, 34, INK, alpha=o)
        text(ctx, fmt(n_now), 755, 1388, 100, RED, alpha=o)
        if t >= T_RES:
            c = ease_out((t - T_RES - 0.1) / 0.3) * a
            note.sticky(ctx, f"この1回では\n{fmt(S['T'])}代目（{fmt(S['T'] * GEN_YEARS)}年後）に\n名字が1つになった", 570, 1368, 36, "yellow", fg=INK, a=c, tilt=-0.015)


# ---------- ヒストグラム（1つになるまでの年数・1万回ぶん） ----------

def xpos(y):
    return HX0 + (HX1 - HX0) * (math.log10(max(y, 1.0)) - math.log10(Y_LO)) / (math.log10(Y_HI) - math.log10(Y_LO))


def hist_bins():
    r = results()
    yrs = r["years"].astype(np.float64)
    edges = np.logspace(math.log10(Y_LO), math.log10(Y_HI), N_BIN + 1)
    idx = np.clip(np.digitize(yrs, edges) - 1, 0, N_BIN - 1)
    return edges, idx


_HIST = {}


def hist_counts(m):
    """最初の m 回ぶんの棒"""
    if "i" not in _HIST:
        _HIST["e"], _HIST["i"] = hist_bins()
        _HIST["max"] = int(np.bincount(_HIST["i"], minlength=N_BIN).max())
    return np.bincount(_HIST["i"][:m], minlength=N_BIN), _HIST["max"]


def hist_alpha(t):
    if t < T_D0:
        return 0.0
    return ease((t - T_D0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    text(ctx, "1つになるまでの年数（1万回ぶん）", 560, 645, 38, INK, alpha=a)
    pr = clamp01((t - T_D0 - 0.8) / (T_D1 - T_D0 - 0.8))
    m_rev = N_RUN if pr >= 1 else int(N_RUN * ease(pr))
    text(ctx, f"棒＝その年数になった回の数　{m_rev:,} / 10,000 回目", 560, 690, 26, PENCIL, bold=False, alpha=a)
    xb1, xb2 = xpos(Y_HUNDRED), xpos(Y_TENTHOUSAND)
    zone = ((HX0, xb1, "数百年で", "#ffe9e3"), (xb1, xb2, "数千年で", "#fff6d6"), (xb2, HX1, "数万年以上かかる", "#e2f1e4"))
    for xa, xb, lab, colr in zone:                                  # 3つの区分（選択肢と同じ）
        ctx.rectangle(xa, 722, xb - xa, HB - 722)
        ctx.set_source_rgba(*hexrgb(colr, 0.7 * a))
        ctx.fill()
        text(ctx, lab, (xa + xb) / 2, 744, 26, INK, bold=False, alpha=a)
    for xb in (xb1, xb2):
        ctx.move_to(xb, 722)
        ctx.line_to(xb, HB)
        ctx.set_dash([8, 6])
        _stroke(ctx, 2.2, PENCIL, 0.7 * a)
        ctx.set_dash([])
    ctx.move_to(HX0, HB)
    ctx.line_to(HX1, HB)
    _stroke(ctx, 3, INK, 0.75 * a)
    for y_, lab in ((1000, "1,000年"), (10000, "1万年"), (100000, "10万年")):
        xt = xpos(y_)
        ctx.move_to(xt, HB)
        ctx.line_to(xt, HB + 9)
        _stroke(ctx, 3, INK, 0.75 * a)
        text(ctx, lab, xt, HB + 36, 26, INK, bold=False, alpha=a)
    cnt, mx = hist_counts(m_rev)
    edges = _HIST["e"]
    for b in range(N_BIN):
        if cnt[b] <= 0:
            continue
        hgt = HMAX * cnt[b] / mx
        xa, xb = xpos(edges[b]), xpos(edges[b + 1])
        rrect(ctx, xa + 1, HB - hgt, xb - xa - 2, hgt, 3)
        ctx.set_source_rgba(*hexrgb("#3f7fb5", 0.92 * a))
        ctx.fill()
    if t >= T_DN:                                                   # 中央値の印（赤い線）
        u = ease_out((t - T_DN) / 0.3) * a
        xm = xpos(r["med_years"])
        ctx.move_to(xm, HB)
        ctx.line_to(xm, HB - HMAX - 14)
        _stroke(ctx, 4.5, RED, 0.95 * u)
        text(ctx, "中央値", xm, HB - HMAX - 34, 28, RED, alpha=u)
        cx2 = 330.0
        text(ctx, "1つになる年数の中央値", cx2, 782, 30, INK, bold=False, alpha=u)
        text(ctx, years_jp(r["med_years"]), cx2, 845, 72, RED, alpha=u)
        text(ctx, "（1万回のちょうど真ん中の値）", cx2, 900, 24, PENCIL, bold=False, alpha=u)
    if t >= T_DN2:
        u = ease_out((t - T_DN2) / 0.3) * a
        yr = r["years"]
        text(ctx, "いちばん早い回", 145, 955, 28, INK, bold=False, align="left", alpha=u)
        text(ctx, years_jp(yr.min()), 345, 955, 38, RED, align="left", alpha=u)
        text(ctx, "いちばん遅い回", 145, 1010, 28, INK, bold=False, align="left", alpha=u)
        text(ctx, years_jp(yr.max()), 345, 1010, 38, RED, align="left", alpha=u)


# ---------- ひねり（10代後に残る名字の数） ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    r = results()
    text(ctx, "世代ごとに残った名字の数", 560, 636, 38, INK, alpha=a)
    text(ctx, "はじめは 1,000（1万回の中央値）", 560, 674, 26, PENCIL, bold=False, alpha=a)
    ctx.move_to(130, TW_BASE)
    ctx.line_to(990, TW_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    pr = ease(clamp01((t - T_TW - 0.8) / (T_TS1 - T_TW - 0.8)))
    for i, g in enumerate(TW_GENS):
        val = float(r["nm_med"][CK_GENS.index(g)])
        shown = N_FAM + (val - N_FAM) * pr
        x = TW_X[i]
        hgt = TW_H * shown / N_FAM
        hl = (g == 10)
        rrect(ctx, x - 70, TW_BASE - hgt, 140, max(hgt, 1.5), 8)
        ctx.set_source_rgba(*hexrgb(RED if hl else "#3f7fb5", 0.9 * a))
        ctx.fill()
        text(ctx, fmt(shown), x, TW_BASE - hgt - 40, 54, RED if hl else INK, alpha=a)
        text(ctx, f"{g}代後", x, TW_BASE + 40, 40, INK, alpha=a)
        text(ctx, f"{fmt(g * GEN_YEARS)}年後", x, TW_BASE + 84, 30, PENCIL, bold=False, alpha=a)


# ---------- 答え ----------

def answer_key():
    return answer_by_rule(results()["med_years"])


def reason_text():
    r = results()
    th = 2 * N_FAM * (1 - 1 / N_FAM)
    mean = r["main"]["T"].mean()
    # 2026-11-08 統括の指示: 付箋は中央値の話だけ（平均・理屈の値は説明欄へ）。左上の大きな数字と同じなので1文に絞る
    return "\n".join(["いちばん早い回でも、", f"{years_jp(r['years'].min())}かかる。"])


TW_Q = "では、300年後（10代後）\nには、いくつ残る？"


def tw_a():
    r = results()
    return f"10代後には、1,000が{fmt(r['nm_med'][CK10])}に減る。"


def tw_b():
    r = results()
    return f"いちばん大きい名字は 1家から {fmt(r['max10_med'])}家に増える"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 570, 1385, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 345, 1160, 28, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 570, 1288, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        text(ctx, tw_a(), 570, 1398, 40, RED, alpha=e)
        text(ctx, tw_b(), 570, 1437, 26, INK, bold=False, alpha=e)


# ---------- 冒頭・上のブロック ----------

def choice_row(labels, size, cx, max_w, gap=40):
    vs = size
    while True:
        ws = [58 + core.text_width(v, vs) for v in labels]
        tot = sum(ws) + gap * (len(labels) - 1)
        if tot <= max_w or vs < 26:
            break
        vs -= 1
    x = cx - tot / 2
    out = []
    for v, w in zip(labels, ws):
        out.append((v, x, vs))
        x += w + gap
    return out


def big3_size(max_w=820.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に家族の部屋（0秒目から動き、場面が寄った所から引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(820.0), 92.0)
        ys = (432, 530, 628)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.05 * (1 - ease_out(t / 0.5))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w3 = core.text_width(BIG_Q3[-1], sz)
        note.pen_line(ctx, 565 - w3 / 2 - 6, 682, 565 + w3 / 2 + 6, 678, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL_RULE, 565, 720, 30, INK, bold=False, alpha=a1)
            text(ctx, DETAIL, 565, 756, 26, PENCIL, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 806
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.96 * a2))
            core.rrect(ctx, cx - 120, cy - 130, 240, 200, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 130, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 80, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy + 4, 50, 48, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy + 4)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) + 1 - n), 0, 0, 78, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
        sz = min(56.0, 100.0 * 850.0 / wmax)
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 464, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 498, 540 + w2 / 2 + 6, 495, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 548
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 860)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7,
                                progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 66 + vw, y - 2, PENCIL, seed=i + 40, width=4,
                              progress=rev, alpha=0.8)

    def draw(self, ctx, t, reveal_t=None):
        m = self.moved(t)
        if m < 1:
            self._intro(ctx, t, 1 - clamp01(m * 2.2))
        if m > 0:
            ctx.save()
            ctx.translate(note.PAGE_DX, 0)
            self._top(ctx, t, m, reveal_t)
            ctx.restore()


INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 締め（3人） ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたの名字は、\n身近に何人いますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 972, 36, INK, bold=False, alpha=r)
    ctx.save()
    ctx.push_group()
    draw_family(ctx, t, 150, 1060, 840, 360, 330.0, 2.95,
                [("child", 190.0, 1, True), ("mother", 420.0, 0, False), ("grandpa", 650.0, -1, False)], None)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    rrect(ctx, 150, 1060, 840, 360, 14)
    _stroke(ctx, 3.5, INK, 0.75 * q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_hist(ctx, t)
        draw_twist(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    draw_closing(ctx, t)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 174.6, 220.0, 293.7)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(4):                                      # 冒頭: ぽん・ぽん（家族）
        mx.add(0.1 + 0.5 * i, blip(520 + 70 * i, 0.07), 0.3)
    for i in range(1, N_STEP):                              # 世代がすすむたびに ちいさな音（だんだん高く）
        mx.add(T_ST[i], blip(440 + 22 * i, 0.07), 0.22)
    mx.add(T_ST[-1], bell(1318.5, 0.9), 0.40)               # 1つになった
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # ヒストグラム
    beat(mx, T_D0 + 0.8, T_D1, bpm=132, vol=0.5, accel=True)
    mx.add(T_DN, bell(784.0, 0.9), 0.45)
    mx.add(T_DN2, bell(880.0, 0.9), 0.45)
    mx.add(T_D1, thump(), 0.5)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    beat(mx, T_TW + 0.8, T_TS1, bpm=132, vol=0.4, accel=True)
    for i in range(4):
        mx.add(T_TS1 + 0.1 * i, bell([784.0, 880.0, 988.0, 1046.5][i], 0.8), 0.35)
    mx.add(T_TW2, blip(659.3, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def change_fraction(t0, t1):
    """画面全体のうち、2つの時刻でちがう画素の割合（preflight と同じ測り方）"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    arrs = []
    for t in (t0, t1):
        core._CUR_T = t
        ctx = cairo.Context(surf)
        draw(ctx, t)
        surf.flush()
        arrs.append(np.frombuffer(bytes(surf.get_data()), np.uint8).astype(np.int16))
    core._CUR_T = 0.0
    return float(np.mean(np.abs(arrs[0] - arrs[1]) > 8))


def run_checks():
    r = results()
    m = r["main"]
    T = m["T"]
    checks = []
    # (1) 条件
    checks.append(("名字の数 = 家の数 = 1,000", float(N_FAM), 1000.0, 0.0))
    checks.append(("1万回", float(len(T)), float(N_RUN), 0.0))
    checks.append(("1代 = 30年", float(GEN_YEARS), 30.0, 0.0))
    checks.append(("どの回も 1つになっている（T ≥ 1）", float((T >= 1).all()), 1.0, 0.0))
    checks.append(("年数 = T × 30（中央値）", r["med_years"], float(np.median(T)) * GEN_YEARS, 0.0))
    # (2) 理論との照合
    th = 2 * N_FAM * (1 - 1 / N_FAM)
    checks.append(("平均の T: 理論 2N(1−1/N) = 1,998代 の 3%以内（1万回の平均）", float(T.mean()), th, 0.03 * th))
    ct = coalescent_T(77, 3000)
    med_c = float(np.median(ct))
    checks.append(("中央値の T: 別の書き方（合祖）の中央値と 5%以内", r["med_gen"], med_c, 0.05 * med_c))
    checks.append(("平均の T: 別の書き方（合祖）の平均と 4%以内", float(T.mean()), float(ct.mean()), 0.04 * th))
    exp1 = N_FAM * (1 - (1 - 1 / N_FAM) ** N_FAM)             # 1代で 家を1つ以上もつ名字の数（期待値）
    checks.append(("1代後に残る名字の数の平均: 理論 N(1−(1−1/N)^N) ≒ 632.3", float(m["names"][:, 0].mean()), exp1, 0.8))
    n_ = float(N_FAM)
    for _ in range(10):                                        # 10代後: 系統をさかのぼる漸化式 n' = N(1−(1−1/N)^n)
        n_ = N_FAM * (1 - (1 - 1 / N_FAM) ** n_)
    checks.append(("10代後に残る名字の数の平均: 漸化式（さかのぼり）と 3%以内", float(m["names"][:, CK10].mean()), n_, 0.03 * n_))
    checks.append(("残る名字の数は 世代が進むほど 減る（中央値）", float(all(r["nm_med"][i] >= r["nm_med"][i + 1] for i in range(len(CK_GENS) - 1))), 1.0, 0.0))
    checks.append(("最初のうちは N に近い（1代後 < 1,000）", float(m["names"][:, 0].max() < N_FAM), 1.0, 0.0))
    checks.append(("10代後にいちばん大きい名字は 1家より多い（中央値）", float(r["max10_med"] > 1), 1.0, 0.0))
    # (3) 答え
    key = answer_by_rule(r["med_years"])
    checks.append(("規則の答え = tenthousands（数万年以上かかる）", float(key == "tenthousands"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が C（3番目）", float(INTRO.correct), 2.0, 0.0))
    checks.append(("記号の並び: 数百年で・数千年で・数万年以上かかる の順", float(LABELS == ["数百年で", "数千年で", "数万年以上かかる"]), 1.0, 0.0))
    for v_, k_ in ((500, "hundreds"), (999, "hundreds"), (1000, "thousands"), (9999, "thousands"), (10000, "tenthousands"), (60000, "tenthousands")):
        checks.append((f"規則の道具: T={v_}年 → {k_}", float(answer_by_rule(v_) == k_), 1.0, 0.0))
    yr = r["years"]
    checks.append(("画面に出す年数の幅が横軸に収まる（最大の回 < 40万年・最小 > 300年）", float(yr.max() < Y_HI and yr.min() > Y_LO), 1.0, 0.0))
    checks.append(("ヒストグラムの棒の合計 = 1万", float(np.bincount(hist_bins()[1], minlength=N_BIN).sum()), float(N_RUN), 0.0))
    # (4) 見本は1万回の中の1回そのもの
    S = samples()
    h = S["h"]
    checks.append(("見本: やり直した T = 1万回の記録の T", float(S["g_end"]), float(T[h]), 0.0))
    checks.append(("見本: やり直した名字の数（記録した世代）= 1万回の記録", float(np.array_equal(S["names"], m["names"][h])), 1.0, 0.0))
    checks.append(("見本: 10代後のいちばん大きい名字 = 1万回の記録", float(S["max10"]), float(m["max10"][h]), 0.0))
    checks.append(("見本: T が中央値にいちばん近い回（中央値との差が 全体の中で最小）", float(abs(T[h] - r["med_gen"]) <= np.abs(T - r["med_gen"]).min()), 1.0, 0.0))
    ok_sum = all(int(S["states"][g][1].sum()) == N_FAM for g in S["gens"])
    checks.append(("見本: どの世代も 家の合計 = 1,000", float(ok_sum), 1.0, 0.0))
    checks.append(("見本: 0代は 1,000の名字・各1家", float(len(S["states"][0][0]) == N_FAM and int(S["states"][0][1].max()) == 1), 1.0, 0.0))
    checks.append(("見本: 最後の世代は 名字が1つ（画面の「残った名字」= 1）", float(len(S["states"][S["T"]][0])), 1.0, 0.0))
    checks.append(("見本: 見せる世代ごとの名字の数は 減る一方", float(all(len(S["states"][a][0]) >= len(S["states"][b][0]) for a, b in zip(S["gens"], S["gens"][1:]))), 1.0, 0.0))
    i_end, _c, n_end = sample_state(T_ST[-1] + 0.5)
    checks.append(("見本: 画面の最後の「残った名字」= 1", float(n_end), 1.0, 0.0))
    checks.append(("見本: 画面の最後の世代 = T", float(S["gens"][i_end]), float(S["T"]), 0.0))
    sl = slots()
    checks.append(("見本: 点の色の数 = 最後は1色", float(len(np.unique(sl[-1], axis=0))), 1.0, 0.0))
    checks.append(("見本: 点の色の数 = 0代は 1,000色", float(len(np.unique(sl[0], axis=0))), 1000.0, 0.0))
    checks.append(("見本: 点の色の数 = 残った名字の数（途中の世代）", float(len(np.unique(sl[7], axis=0))), float(len(S["states"][S["gens"][7]][0])), 0.0))
    checks.append(("点の格子 = 40×25 = 1,000", float(COLS * ROWS), 1000.0, 0.0))
    # (5) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (6) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本: 0代を見せる時間が 1秒以上（初見で点の意味を読む）", float(HOLD0 >= 1.0), 1.0, 0.0))
    checks.append(("見本: 最後の結果が見える時間 3秒以上", float(T_SEND - T_ST[-1] >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 中央値の数字 3秒以上", float(T_DN2 - T_DN >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: いちばん早い・遅い 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 棒グラフの数字 3秒以上", float(T_Q - T_TS1 >= 3.0), 1.0, 0.0))
    checks.append(("世代の切り替えは 1つあたり 0.4秒以上", float(STEP_D >= 0.4), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (7) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


def lint():
    """mp4 は書かずに、全コマの文字を記録して 公開前チェックと同じ点検（位置・大きさ・読み切れる長さ・0秒目の動き・長さ・冒頭の音）をする"""
    n = int(round(DURATION * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    core._LOG = []
    first = probe = None
    for i in range(n):
        core._CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        if i == 0:
            surf.flush()
            first = np.frombuffer(bytes(surf.get_data()), np.uint8)
        elif i == int(0.3 * FPS):
            surf.flush()
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
    log, core._LOG = core._LOG, None
    problems = core.preflight(log, first, probe, DURATION, build_audio())
    if problems:
        print("公開前チェック相当: 要対応")
        for p_ in problems:
            print("  -", p_)
    else:
        print("公開前チェック相当: OK")
    return problems


def report_full():
    S = samples()
    print(f"長さ {DURATION:.1f}秒  見本 {T_GO:.1f}〜{T_SEND:.1f}（世代{N_STEP}段・最後 {T_ST[-1]:.1f}）  ヒストグラム {T_D0:.1f}-{T_D1:.1f}  数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: 第{S['h']}回  T={S['T']}代（{S['T'] * GEN_YEARS:,}年）  見せる世代 {S['gens']}")
    print(f"  問い3行の文字 {min(big3_size(820.0), 92.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(820.0), 92.0)) for l in BIG_Q3):.0f}px")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a(), "|", tw_b())
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, T_GO + 0.3, T_ST[0] + 0.5, T_ST[2] + 0.35, T_ST[5] + 0.35, T_ST[7] + 0.35, T_ST[9] + 0.35, T_ST[11] + 0.35,
              T_ST[13] + 0.35, T_ST[-1] + 0.3, T_ST[-1] + 1.5, T_D0 + 1.5, T_D1 - 0.2, T_DN + 1.2, T_DN2 + 1.2, T_REV + 0.9, T_ANS2 + 0.6,
              T_TW + 0.8, T_TW + 2.4, T_TS1 + 1.2, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
