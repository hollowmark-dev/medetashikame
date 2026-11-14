"""江戸から手紙を出したら、あなたの手紙は何日で着く？（横型ロング・飛脚）— 2026-10-28 作成。モデル部分だけ（数字の計算・照合）。場面は未作成。

構成案: research/longform_hikyaku_outline_2026-10-28.md ／ 史料: research/longform_hikyaku_sources_2026-10-28.md

問い: 江戸から伊勢へ、飛脚問屋の「日限」つきの便で手紙を出したとき、(1) 約束の日に間に合うか (2) 賃を2.4〜2.9倍払って日限を2日縮めると何日得か
      (3) 返事が来るまで何日待つか。

モデル
  1万通      : 1通ずつ、次の順でくじを引く（乱数の種は固定。main_seed。基準・少なめ・多めの3本は同じ種・同じくじで、川止めの分布だけ変える）。
                1. 出す日 : 1781〜1868年の日記の全日（31,875日。天気が「不明」の日も含む）から一様に1日。使うのは月日（新暦）だけ。
                2. 便の日限 : 五日限・六日限・八日限を同じ確率（1/3ずつ・仮定。表1は値段と日数の表で、便ごとの利用の多さは書かれていない）。
                3. ふだんの遅れ、4. 大井川の川止め、5. 返事の書く時間（問い3のみ）
  日限        : 日限＝約束の日数。ちょうどなら N日目に着く（T＝N）。到着日数 T ＝ 日限 ＋ ふだんの遅れ ＋ 川止めの待ち。
                「約束の日までに着いた」＝ T ≤ 日限。「遅れ」＝ T − 日限。
  ふだんの遅れ : 【遅れ方の形の仮定】紀州藩の送金33件（紀要14号 表16 №148〜180）の形を借りる。ちょうど24件（73%）・1日遅れ9件（27%）・
                早着0・2日以上0。これは松坂→江戸の金荷の実績で、江戸発の手紙の実績ではない。使うのは「遅れ方の形」だけ。
                → 手紙ごとに 0日（24/33）か +1日（9/33）をくじで引く。便・月によらず同じ（33件では便ごと・月ごとの差を言えない）。
  川止め      : 【すべて仮定。資料は「大井川は年に十数回・延べ50日前後・最長28日（慶応4年）」の1文と実例の断片だけ】
                (a) 大井川に着く日 : 出発日 ＋ round(日限 × 0.5)（五日限3日目・六日限3日目・八日限4日目。江戸〜伊勢のほぼ中間）。
                    大井川より前・後の川（酒匂川・天竜川など）の川止めは入れない（足さない）。
                (b) 川止め中の確率（月ごと） : p_m ＝ （年間日数 ÷ 365）× 雨の重み_m ÷ 年平均の重み。
                    雨の重み_m ＝ 日記の月ごとの「雨雪の日の割合」（天気が分かる日のうち。1月8%・6月26%・9月25%…冬の約3倍）。
                    日数で重みを付けて正規化するので、年間の川止め日数がぴったり基準（50日）になる。江戸の雨と大井川の増水は別の天気なので、
                    日付の対応づけはせず、月の重み（季節のかたち）にだけ使う。
                (c) 川止めの長さ L（日）: 1〜7日は切り詰めた幾何分布、8〜28日は一様（まれな長い尾）の混合。平均は基準 3.5日（年間50日÷十数回）、
                    尾の割合（8〜28日になる川止めの割合）は基準 4%。
                (d) 到着時の残り日数 : 川止めの途中で着くので、長い川止めほど当たりやすい（長さ偏り）。
                    川止め中に着いたとき、長さは L に比例する確率で選び（長さ偏り）、着いた日はその L 日のうちの k 日目（一様）、
                    待ち ＝ L − k + 1 日（川明けの翌日までに渡る。最長で L ＝ 28 日）。
                    待ちの分布は P(待ち＝w) ＝ P(L ≥ w) ÷ 平均L（正確に同じ式。--check で確かめる）。
                (e) 3本の幅 : 少なめ ＝ 年25日・平均2.5日・尾2%／基準 ＝ 年50日・平均3.5日・尾4%／多め ＝ 年80日・平均4.5日・尾6%（最長28日は共通）。
  問い2 急ぎ便 : 同じ手紙を速い便と八日限で、同じ日に同時に出したとして比べる（賃の比は表1: 六日限7.2匁÷八日限3匁＝2.4倍・山田12匁÷4.2匁＝約2.9倍。
                五日限の比は津の 4.8匁÷3匁＝1.6倍 の1つだけ）。大井川は1本で、同じ川止めを2通が共有する（速い便が先に着き、遅い便は1日後に着く）。
                川止めは速い便の着く日に始まっていれば続きを遅い便も受ける。まだ始まっていなければ、翌日までに始まる確率（開始のハザード）で遅い便だけが当たる。
                ふだんの遅れは2通別々にくじを引く。
                【2つの読み】 A（基本）: 川明けのあとも、速い便の速さの得は残りの道のりの分だけ残る。→ 同じ川止めを待つと、得は2日から1日に縮む。
                           B（滞貨の仮定・強め）: 川止めを2通とも待ったときは、川明けの宿の人馬の取り合いで、速い便の得は残らない（残りの日数は同じ）。
                           → 2通が同じ川明けを待ったとき、差はふだんの遅れの差だけになる。資料に直接の根拠はない。「差が消える」の上限を見るための仮定。
  問い3 返事  : 往き（上と同じ）＋ 相手が書く時間（1〜3日の整数・一様・仮定）＋ 帰り（同じ便・同じ分布の別のくじ）。
                帰りは伊勢から江戸へ。帰りの出発日は往きの出発日 ＋ 往きの日数 ＋ 書く時間。大井川へは帰りの道のりの半分で着く（往きと対称）。
                帰りの川止めは往きとは別にくじを引く（往きの川止めが帰りに残っているとは考えない）。
  代表の手紙   : いちばん遅かった手紙＝（T − 日限）が最大の手紙（同点は日数が大きく、番号が若いほう）。
                いちばん早かった手紙＝T が最小の手紙（五日限・遅れなし）の最初の1通。中央値の手紙＝T が中央値に等しい最初の1通。
  厳密計算    : くじを引かず、全日付×全便を数え上げた値（シミュとは別の経路）。1万通の主要な数字は標準誤差の4倍以内で一致するかを --check で見る。
  頑健さ      : 種を5つ変えて1万通をやり直し、主要な数字のばらつきを見る。

照合（--check）
  - 日記の表（31,875日・全月がそろう）と、33件の形（表の転記が24/9/0/0・集計が24/33になる）
  - 川止めなしなら全部が日限どおりか+1日（問い2の2通も、問い3の往復も同様）。+1日の割合は 9/33 と標準誤差の4倍以内で一致
  - 年間の川止め日数が基準の約50日（月の重みから数えた値、およびカレンダー上で川止めの始まりと終わりを1日ずつ動かした別経路のシミュ）
  - 川止めの長さ（平均3.5日・最長28日）と、到着時の待ちの分布（式 ＝ カレンダーのシミュ）
  - 1万通の結果 ≒ 厳密計算（標準誤差の4倍以内）／速い便の川止めの待ち ≒ 厳密計算
  - 同じ種で2回やって同じ結果になる

使い方
  python -X utf8 sims/hikyaku-long.py --compute    計算 → out/hikyaku-long/data.json（照合も実行）
  python -X utf8 sims/hikyaku-long.py --check      照合だけ
  python -X utf8 sims/hikyaku-long.py --numbers    data.json → out/hikyaku-long/numbers.md（data.json が無ければ先に --compute）

天気の表: data/edo_weather/hirosaki_edo_1781_1868.csv（月の重みにだけ使う。出典は同じフォルダの SOURCE.md）
"""
import csv
import datetime as dt
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SLUG = "hikyaku-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
WEATHER_CSV = ROOT / "data" / "edo_weather" / "hirosaki_edo_1781_1868.csv"

N = 10000
MAIN_SEED = 2026
ROB_SEEDS = [2027, 2028, 2029, 2030, 2031]
KINDS = [5, 6, 8]                          # 五日限・六日限・八日限
KNAME = ["五日限", "六日限", "八日限"]
RIVER_FRAC = 0.5                            # 大井川は道のりの半分あたり（仮定）
WRITE_RANGE = (1, 3)                        # 相手が書く時間（日・仮定）
MDAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
TAIL_MEAN = 18.0                            # 8〜28日の一様の平均
LMAX = 28
SCEN = [("少なめ", 25, 2.5, 0.02), ("基準", 50, 3.5, 0.04), ("多め", 80, 4.5, 0.06)]
BASE = 1                                    # 基準のインデックス

# 紀要14号 表16 №148〜180（宝暦12〜14年・松坂→江戸の金荷）の（約束日数, 実日数）。出発日を含めて数えた値。
KISHU33 = [(6, 7), (6, 6), (7, 8), (7, 8), (8, 9), (8, 8), (8, 8), (8, 9), (6, 7), (6, 6), (6, 6), (5, 5), (7, 7), (7, 8), (6, 7),
           (5, 5), (5, 5), (5, 5), (5, 6), (5, 5), (8, 8), (8, 8), (8, 8), (8, 8), (8, 8), (8, 8), (6, 6), (6, 6), (6, 6), (6, 6),
           (6, 6), (5, 5), (7, 7)]
N_EXACT = sum(1 for a, b in KISHU33 if b == a)
N_PLUS1 = sum(1 for a, b in KISHU33 if b == a + 1)
P_LATE1 = N_PLUS1 / len(KISHU33)           # ふだんの遅れ: +1日の確率 9/33
OFF = np.array([int(math.floor(RIVER_FRAC * d + 0.5)) for d in KINDS])     # 大井川に着く日 5→3, 6→3, 8→4


def offset_of(D):
    return int(math.floor(RIVER_FRAC * D + 0.5))


# ============================================================
# 日記の表（日付の一様なくじと、月の雨の重み）
# ============================================================
class Diary:
    def __init__(self):
        rows = list(csv.DictReader(open(WEATHER_CSV, encoding="utf-8", newline="")))
        self.n = len(rows)
        self.ords = np.array([dt.date.fromisoformat(r["date"]).toordinal() for r in rows])
        self.month = np.array([int(r["date"][5:7]) for r in rows])
        known = np.array([r["day_class"] != "不明" for r in rows])
        rain = np.array([r["day_class"] == "雨雪" for r in rows])
        self.rain_share = np.zeros(13)
        self.known_n = np.zeros(13, int)
        for m in range(1, 13):
            sel = (self.month == m) & known
            self.known_n[m] = int(sel.sum())
            self.rain_share[m] = rain[sel].sum() / sel.sum()
        self.m_count = np.array([0] + [int((self.month == m).sum()) for m in range(1, 13)])
        # 序数 → 月 の引き出し（出発日 + 最大数か月ぶん）
        self.o0 = int(self.ords.min())
        span = int(self.ords.max()) - self.o0 + 200
        d64 = np.datetime64("0001-01-01", "D") + (np.arange(self.o0, self.o0 + span) - 1)
        self.mtab = (d64.astype("datetime64[M]").astype(int) % 12 + 1).astype(int)

    def month_of(self, ordv):
        return self.mtab[np.asarray(ordv) - self.o0]

    def md(self, ordv):
        d = dt.date.fromordinal(int(ordv))
        return f"{d.month}月{d.day}日"


# ============================================================
# 川止めの型
# ============================================================
def len_pmf(mean_len, tail_p):
    """川止めの長さ L（日）の確率。index＝日数 0..28。1〜7日は切り詰めた幾何分布、8〜28日は一様。"""
    tail = np.zeros(LMAX + 1)
    tail[8:] = 1 / 21
    mo = (mean_len - tail_p * TAIL_MEAN) / (1 - tail_p)         # 通常の川止めの平均
    l = np.arange(1, 8)

    def m(r):
        w = r ** (l - 1)
        return float((w * l).sum() / w.sum())

    lo, hi = 1e-9, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if m(mid) < mo:
            lo = mid
        else:
            hi = mid
    w = np.zeros(LMAX + 1)
    w[1:8] = ((lo + hi) / 2) ** (l - 1)
    w /= w.sum()
    return (1 - tail_p) * w + tail_p * tail


class River:
    def __init__(self, diary, days_year, mean_len, tail_p):
        self.days_year, self.mean_len, self.tail_p = days_year, mean_len, tail_p
        self.f = len_pmf(mean_len, tail_p)
        ls = np.arange(LMAX + 1)
        self.EL = float((ls * self.f).sum())
        self.surv = np.array([self.f[w:].sum() for w in range(LMAX + 2)])        # P(L ≥ w)
        self.g = self.surv[1:LMAX + 1] / self.EL if self.EL > 0 else np.zeros(LMAX)   # P(待ち＝w), w＝1..28（川止め中に着いたとき）
        self.G = np.concatenate([[1.0], [self.g[x - 1:].sum() for x in range(1, LMAX + 2)]])   # P(待ち ≥ x)
        self.EW = float((np.arange(1, LMAX + 1) * self.g).sum())
        self.lb_cdf = np.cumsum(ls * self.f / self.EL)[1:] if self.EL > 0 else np.ones(LMAX)   # 長さ偏り・長さ1..28
        self.f_cdf = np.cumsum(self.f)[1:]
        w = diary.rain_share
        wbar = float((MDAYS * w[1:]).sum() / 365)
        p = np.zeros(13)
        p[1:] = np.minimum(days_year / 365 * w[1:] / wbar, 0.6) if days_year > 0 else 0.0
        self.p = p
        self.h = np.where(p > 0, p / (self.EL * (1 - p) + p), 0.0)     # 川止めが開いている日に始まる確率（始まった日も閉じた日に数える）。定常で閉じている割合がちょうど p になる
        self.annual = float((MDAYS * p[1:]).sum())


def inv_lb(rv, u):
    return 1 + np.minimum(np.searchsorted(rv.lb_cdf, u, side="right"), LMAX - 1)


def inv_f(rv, u):
    return 1 + np.minimum(np.searchsorted(rv.f_cdf, u, side="right"), LMAX - 1)


def river_single(rv, month, us, uL, uk):
    """手紙が大井川に着いた日が川止め中か。戻り値: 待ち日数, 川止めの長さ, 着いたのが何日目か。"""
    p = rv.p[month]
    inn = us < p
    L = inv_lb(rv, uL)
    k = 1 + np.floor(uk * L).astype(int)
    return np.where(inn, L - k + 1, 0), np.where(inn, L, 0), np.where(inn, k, 0)


# ============================================================
# 1万通（問い1・3）
# ============================================================
def draw_letters(seed, n=N):
    rng = np.random.default_rng([seed, 1])
    return dict(n=n, di=rng.integers(0, 0 + 10 ** 9, n), kind=rng.integers(0, 3, n), ud=rng.random(n), us=rng.random(n),
                uL=rng.random(n), uk=rng.random(n), write=rng.integers(WRITE_RANGE[0], WRITE_RANGE[1] + 1, n),
                ud2=rng.random(n), us2=rng.random(n), uL2=rng.random(n), uk2=rng.random(n))


def run_letters(rv, diary, X):
    di = X["di"] % diary.n
    kind = X["kind"]
    D = np.array(KINDS)[kind]
    off = OFF[kind]
    ords = diary.ords[di]
    d1 = (X["ud"] >= 1 - P_LATE1).astype(int)
    w1, L1, k1 = river_single(rv, diary.month_of(ords + off), X["us"], X["uL"], X["uk"])
    T = D + d1 + w1
    start2 = ords + T + X["write"]
    d2 = (X["ud2"] >= 1 - P_LATE1).astype(int)
    w2, L2, k2 = river_single(rv, diary.month_of(start2 + off), X["us2"], X["uL2"], X["uk2"])
    T2 = D + d2 + w2
    return dict(di=di, kind=kind, D=D, month=diary.month[di], ords=ords, d1=d1, w1=w1, L1=L1, k1=k1, T=T, delay=T - D,
                write=X["write"], d2=d2, w2=w2, L2=L2, k2=k2, T2=T2, delay2=T2 - D, reply=T + X["write"] + T2, start2=start2)


def card_out(R, i, diary):
    return dict(i=int(i), date=diary.md(R["ords"][i]), month=int(R["month"][i]), kind=KNAME[int(R["kind"][i])], D=int(R["D"][i]),
                T=int(R["T"][i]), delay=int(R["delay"][i]), normal_delay=int(R["d1"][i]), river_wait=int(R["w1"][i]),
                river_len=int(R["L1"][i]), river_day=int(R["k1"][i]))


def card_reply(R, i, diary):
    c = card_out(R, i, diary)
    c.update(write=int(R["write"][i]), back_date=diary.md(R["start2"][i]), back_normal_delay=int(R["d2"][i]), back_river_wait=int(R["w2"][i]),
             back_river_len=int(R["L2"][i]), back_river_day=int(R["k2"][i]), T2=int(R["T2"][i]), reply=int(R["reply"][i]))
    return c


def first_idx(mask_or_idx):
    a = np.nonzero(mask_or_idx)[0]
    return int(a[0])


def q1_stats(R, diary):
    n = len(R["T"])
    dl = R["delay"]
    T = R["T"]
    out = dict(n=n, on_time=100 * float((dl == 0).mean()), d0=100 * float((dl == 0).mean()), d1=100 * float((dl == 1).mean()),
               d2_5=100 * float(((dl >= 2) & (dl <= 5)).mean()), d6=100 * float((dl >= 6).mean()), d10=100 * float((dl >= 10).mean()),
               d20=100 * float((dl >= 20).mean()),
               T_median=float(np.median(T)), T_mean=float(T.mean()), delay_median=float(np.median(dl)), delay_mean=float(dl.mean()),
               delay_max=int(dl.max()), T_max=int(T.max()), T_min=int(T.min()), river_hit=100 * float((R["w1"] > 0).mean()),
               share_days_from_d6=100 * float(dl[dl >= 6].sum() / dl.sum()) if dl.sum() > 0 else 0.0)
    out["by_kind"] = []
    for k in range(3):
        m = R["kind"] == k
        out["by_kind"].append(dict(kind=KNAME[k], n=int(m.sum()), on_time=100 * float((dl[m] == 0).mean()), T_median=float(np.median(T[m])),
                                   T_mean=float(T[m].mean()), d1=100 * float((dl[m] == 1).mean()), d6=100 * float((dl[m] >= 6).mean()),
                                   delay_max=int(dl[m].max())))
    out["by_month"] = []
    for mo in range(1, 13):
        m = R["month"] == mo
        out["by_month"].append(dict(month=mo, n=int(m.sum()), on_time=100 * float((dl[m] == 0).mean()), d6=100 * float((dl[m] >= 6).mean()),
                                    river_hit=100 * float((R["w1"][m] > 0).mean()), delay_mean=float(dl[m].mean())))
    mx = int(dl.max())
    worst = first_idx((dl == mx) & (T == T[dl == mx].max()))
    best = first_idx(T == T.min())
    med = first_idx(T == int(np.median(T)))
    out["cards"] = dict(worst=card_out(R, worst, diary), best=card_out(R, best, diary), median=card_out(R, med, diary),
                        best_n=int((T == T.min()).sum()), worst_n=int((dl == mx).sum()))
    return out


def q3_stats(R, diary):
    rep = R["reply"]
    out = dict(n=len(rep), median=float(np.median(rep)), mean=float(rep.mean()), p90=float(np.percentile(rep, 90)), max=int(rep.max()),
               min=int(rep.min()), ge14=100 * float((rep >= 14).mean()), ge21=100 * float((rep >= 21).mean()), ge28=100 * float((rep >= 28).mean()),
               both_river=100 * float(((R["w1"] > 0) & (R["w2"] > 0)).mean()), any_river=100 * float(((R["w1"] > 0) | (R["w2"] > 0)).mean()),
               plan_median=float(np.median(2 * R["D"] + R["write"])))
    out["by_kind"] = []
    for k in range(3):
        m = R["kind"] == k
        out["by_kind"].append(dict(kind=KNAME[k], n=int(m.sum()), median=float(np.median(rep[m])), mean=float(rep[m].mean()),
                                   p90=float(np.percentile(rep[m], 90)), max=int(rep[m].max()), min=int(rep[m].min()),
                                   ge14=100 * float((rep[m] >= 14).mean()), ge21=100 * float((rep[m] >= 21).mean()),
                                   plan_median=float(np.median(2 * R["D"][m] + R["write"][m]))))
    mx = int(rep.max())
    worst = first_idx(rep == mx)
    best = first_idx(rep == rep.min())
    med = first_idx(rep == int(np.median(rep)))
    out["cards"] = dict(worst=card_reply(R, worst, diary), best=card_reply(R, best, diary), median=card_reply(R, med, diary),
                        worst_n=int((rep == mx).sum()))
    return out


# ============================================================
# 問い2 急ぎ便（同じ手紙を速い便と八日限で同時に出す）
# ============================================================
def run_pairs(rv, diary, seed, fast_i, slow_i=2, n=N):
    rng = np.random.default_rng([seed, 2 + fast_i])
    di = rng.integers(0, diary.n, n)
    udf, uds, us, uL, uk, uh, uL2 = [rng.random(n) for _ in range(7)]
    Df, Ds = KINDS[fast_i], KINDS[slow_i]
    af, as_ = int(OFF[fast_i]), int(OFF[slow_i])
    gap = as_ - af
    ords = diary.ords[di]
    t0 = ords + af
    mo = diary.month_of(t0)
    p = rv.p[mo]
    h = rv.h[mo]
    closed = us < p
    L = inv_lb(rv, uL)
    k = 1 + np.floor(uk * L).astype(int)
    wf = np.where(closed, L - k + 1, 0)
    ws_c = np.maximum(wf - gap, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        jstar = np.where(h > 0, 1 + np.floor(np.log1p(-uh) / np.log1p(-np.where(h > 0, h, 0.5))), 10 ** 6)
    started = (~closed) & (jstar <= gap)
    Lord = inv_f(rv, uL2)
    ws_o = np.where(started, jstar + Lord - gap, 0).astype(int)
    ws = np.where(closed, ws_c, ws_o)
    df = (udf >= 1 - P_LATE1).astype(int)
    ds = (uds >= 1 - P_LATE1).astype(int)
    Ts = Ds + ds + ws
    Tf_A = Df + df + wf
    both = (wf > 0) & (ws > 0)
    Tf_B = np.where(both, Ts - ds + df, Tf_A)
    return dict(di=di, ords=ords, month=diary.month[di], Df=Df, Ds=Ds, wf=wf, ws=ws, df=df, ds=ds, Ts=Ts, Tf_A=Tf_A, Tf_B=Tf_B, both=both,
                L=np.where(closed, L, np.where(started, Lord, 0)))


def card_pair(P, i, diary, which):
    Tf = P["Tf_A"] if which == "A" else P["Tf_B"]
    return dict(i=int(i), date=diary.md(P["ords"][i]), month=int(P["month"][i]), fast_normal_delay=int(P["df"][i]), slow_normal_delay=int(P["ds"][i]),
                fast_river_wait=int(P["wf"][i]), slow_river_wait=int(P["ws"][i]), river_len=int(P["L"][i]), T_fast=int(Tf[i]), T_slow=int(P["Ts"][i]),
                gain=int(P["Ts"][i] - Tf[i]))


def dist_gain(g):
    keys = [("-1日以下(高い便のほうが遅い)", g <= -1), ("0日(同じ日)", g == 0), ("1日", g == 1), ("2日", g == 2), ("3日", g == 3), ("4日以上", g >= 4)]
    return [dict(label=a, pct=100 * float(b.mean())) for a, b in keys]


def q2_stats(P, diary):
    out = dict(Df=P["Df"], Ds=P["Ds"], nominal=P["Ds"] - P["Df"], river_hit_any=100 * float(((P["wf"] > 0) | (P["ws"] > 0)).mean()),
               river_hit_both=100 * float(P["both"].mean()), river_hit_fast=100 * float((P["wf"] > 0).mean()))
    hit = (P["wf"] > 0) | (P["ws"] > 0)
    for w in ("A", "B"):
        Tf = P["Tf_A"] if w == "A" else P["Tf_B"]
        g = P["Ts"] - Tf
        d = dict(median=float(np.median(g)), mean=float(g.mean()), same=100 * float((g == 0).mean()), reversed=100 * float((g < 0).mean()),
                 le0=100 * float((g <= 0).mean()), le1=100 * float((g <= 1).mean()), ge2=100 * float((g >= 2).mean()), dist=dist_gain(g),
                 hit_median=float(np.median(g[hit])) if hit.any() else None, hit_le0=100 * float((g[hit] <= 0).mean()) if hit.any() else 0.0,
                 both_le0=100 * float((g[P["both"]] <= 0).mean()) if P["both"].any() else 0.0,
                 both_median=float(np.median(g[P["both"]])) if P["both"].any() else None,
                 clear_median=float(np.median(g[~hit])) if (~hit).any() else None)
        gmin = g.min()
        cand = np.nonzero(g == gmin)[0]
        gmax = g.max()
        d["cards"] = dict(worst=card_pair(P, int(cand[np.argmax(P["wf"][cand])]), diary, w), best=card_pair(P, first_idx(g == gmax), diary, w),
                          worst_n=int(len(cand)), gmin=int(gmin), gmax=int(gmax),
                          typical=card_pair(P, first_idx((g == int(np.median(g))) & ~hit), diary, w))
        out[w] = d
    return out


# ============================================================
# 厳密計算（日付×便の数え上げ）
# ============================================================
def exact_stats(rv, diary):
    dayidx = np.arange(diary.n)
    on, ge6, md = [], [], []
    for k in range(3):
        p = rv.p[diary.month_of(diary.ords + OFF[k])]
        on.append((1 - P_LATE1) * (1 - p))
        ge6.append((1 - P_LATE1) * p * rv.G[6] + P_LATE1 * p * rv.G[5])
        md.append(P_LATE1 + p * rv.EW)
    return dict(on_time=100 * float(np.mean(on)), d6=100 * float(np.mean(ge6)), delay_mean=float(np.mean(md)),
                river_hit=100 * float(np.mean([rv.p[diary.month_of(diary.ords + OFF[k])] for k in range(3)])))


# ============================================================
# まとめて1本ぶん
# ============================================================
def summarize(rv, diary, seed):
    X = draw_letters(seed)
    R = run_letters(rv, diary, X)
    q1 = q1_stats(R, diary)
    q3 = q3_stats(R, diary)
    q2 = {}
    for fast_i in (1, 0):
        q2[f"{KNAME[fast_i]}v八日限"] = q2_stats(run_pairs(rv, diary, seed, fast_i), diary)
    return dict(seed=seed, q1=q1, q2=q2, q3=q3, exact=exact_stats(rv, diary))


def flat_numbers(S):
    q1, q3 = S["q1"], S["q3"]
    q2 = S["q2"]["六日限v八日限"]
    return {"約束どおりに着いた%": q1["on_time"], "日数の中央値": q1["T_median"], "日数の平均": q1["T_mean"], "6日以上遅れ%": q1["d6"],
            "いちばん遅れた日数": q1["delay_max"], "急ぎ便の得(A)中央値": q2["A"]["median"], "差が消えた%(A)": q2["A"]["same"],
            "差が消えた%(B)": q2["B"]["same"], "返事の中央値": q3["median"], "返事2週間以上%": q3["ge14"], "返事の最長": q3["max"],
            "六日限の返事の中央値": q3["by_kind"][1]["median"], "六日限の返事2週間以上%": q3["by_kind"][1]["ge14"]}


def stable_flat(S):
    return {k: round(v, 6) for k, v in flat_numbers(S).items()}


# ============================================================
# 照合
# ============================================================
def calendar_sim(rv, years=3000, seed=11):
    """カレンダー上で川止めの始まり・終わりを1日ずつ動かす別経路のシミュ。戻り値: 年間日数の平均と標準誤差、到着時の待ちの分布の指標。"""
    rng = np.random.default_rng(seed)
    warm = 60
    mlist = np.concatenate([np.repeat(np.arange(1, 13), MDAYS)] * 1)
    ndays = 365
    total = warm + ndays + 40
    mon = np.array([mlist[(d - warm) % 365] for d in range(total)])
    rem = np.zeros(years, int)
    closed = np.zeros((total, years), bool)
    for d in range(total):
        is_closed = rem > 0
        closed[d] = is_closed
        rem = np.where(is_closed, rem - 1, rem)
        h = rv.h[mon[d]]
        start = (~is_closed) & (rng.random(years) < h)
        L = inv_f(rv, rng.random(years))
        rem = np.where(start, L - 1, rem)     # 始まった日は閉じた日1日目（その日の closed は次の日から数える方式を避けるため、その日も閉じ扱い）
        closed[d] |= start
    wait = np.zeros((total, years), int)
    for d in range(total - 2, -1, -1):
        wait[d] = np.where(closed[d], wait[d + 1] + 1, 0)
    sl = slice(warm, warm + ndays)
    ann = closed[sl].sum(0)
    wd = wait[sl]
    per_year_mean_wait = wd.mean(0)
    return dict(annual=float(ann.mean()), annual_se=float(ann.std(ddof=1) / math.sqrt(years)), hit=float((wd > 0).mean()), mean_wait=float(wd.mean()),
                mean_wait_se=float(per_year_mean_wait.std(ddof=1) / math.sqrt(years)), ge8=float((wd >= 8).mean()),
                ge8_se=float(((wd >= 8).mean(0)).std(ddof=1) / math.sqrt(years)), max_wait=int(wd.max()))


def run_checks(diary, quiet=False):
    res = {}
    allok = True

    def rec(name, ok, detail):
        nonlocal allok
        allok &= bool(ok)
        res[name] = dict(ok=bool(ok), detail=detail)
        if not quiet:
            print(("OK  " if ok else "NG  ") + name + " : " + detail)

    rvs = [River(diary, a, b, c) for _, a, b, c in SCEN]
    rv = rvs[BASE]
    # 1. 日記の表
    cont = bool(np.all(np.diff(diary.ords) == 1))
    rec("日記の表", cont and diary.n == 31875 and all(diary.m_count[1:] > 2000) and all(diary.known_n[1:] > 1000),
        f"{diary.n}日・連続={cont}・月ごとの日数 {int(diary.m_count[1:].min())}〜{int(diary.m_count[1:].max())}・天気が分かる日 月ごと {int(diary.known_n[1:].min())}〜{int(diary.known_n[1:].max())}")
    # 2. 33件
    ok33 = (len(KISHU33) == 33 and N_EXACT == 24 and N_PLUS1 == 9 and all(b >= a for a, b in KISHU33) and all(b - a <= 1 for a, b in KISHU33))
    rec("33件の形", ok33, f"転記: 33件・ちょうど {N_EXACT}（{100 * N_EXACT / 33:.1f}%）・+1日 {N_PLUS1}（{100 * N_PLUS1 / 33:.1f}%）・早着 0・+2日以上 0")
    # 3. 川止めなし
    rv0 = River(diary, 0, 3.5, 0.04)
    X = draw_letters(MAIN_SEED)
    R0 = run_letters(rv0, diary, X)
    dl = R0["delay"]
    f1 = float((dl == 1).mean())
    se = math.sqrt(P_LATE1 * (1 - P_LATE1) / N)
    cond_ok = bool(np.all((dl == 0) | (dl == 1)) and np.all((R0["delay2"] == 0) | (R0["delay2"] == 1)) and abs(f1 - P_LATE1) < 4 * se)
    rec("川止めなし(往き)", cond_ok, f"遅れは0日か1日だけ・+1日 {100 * f1:.1f}%（33件の {100 * P_LATE1:.1f}%・標準誤差 {100 * se:.1f}。4倍以内）・川止めに当たった {int((R0['w1'] > 0).sum())}通")
    gaps = []
    for fi in (1, 0):
        P0 = run_pairs(rv0, diary, MAIN_SEED, fi)
        g = P0["Ts"] - P0["Tf_A"]
        gaps.append((int(g.min()), int(g.max()), bool(np.all(P0["Tf_A"] == P0["Tf_B"])), KINDS[2] - KINDS[fi]))
    ok = all(a >= nom - 1 and b <= nom + 1 and c for a, b, c, nom in gaps)
    rec("川止めなし(急ぎ便の差)", ok, f"六日限vs八日限: 差 {gaps[0][0]}〜{gaps[0][1]}日・五日限vs八日限: 差 {gaps[1][0]}〜{gaps[1][1]}日（日限の差±ふだんの遅れの差だけ・AとBは同じ）")
    rep0 = R0["reply"]
    okr = bool(np.all(rep0 >= 2 * R0["D"] + R0["write"]) and np.all(rep0 <= 2 * R0["D"] + R0["write"] + 2))
    rec("川止めなし(返事)", okr, f"返事は 往復の日限＋書く時間 に 0〜2日足しただけ（最小 {int(rep0.min())}日・最大 {int(rep0.max())}日）")
    # 4. 長さ
    rows = []
    okL = True
    for (nm, a, b, c), r in zip(SCEN, rvs):
        okL &= abs(r.EL - b) < 1e-6 and r.f[LMAX] > 0 and r.f[LMAX + 0:].sum() > 0 and abs(r.f.sum() - 1) < 1e-9 and abs(r.g.sum() - 1) < 1e-9
        okL &= abs(r.f[8:].sum() - c) < 1e-9
        rows.append(f"{nm}: 平均{r.EL:.2f}日・尾{100 * r.f[8:].sum():.0f}%・最長{int(np.nonzero(r.f)[0].max())}日")
    rec("川止めの長さ", okL, " ／ ".join(rows))
    # 5. 年間日数
    rows = []
    ok5 = True
    for (nm, a, b, c), r in zip(SCEN, rvs):
        ok5 &= abs(r.annual - a) < 0.5
        rows.append(f"{nm}: 月の重みから {r.annual:.1f}日（目標{a}）")
    cs = [calendar_sim(r) for r in rvs]
    for (nm, a, b, c), r, s in zip(SCEN, rvs, cs):
        ok5 &= abs(s["annual"] - a) < max(0.05 * a, 4 * s["annual_se"])
        rows.append(f"{nm}: カレンダーのシミュ {s['annual']:.1f}日（±{s['annual_se']:.2f}）")
    pm = rv.p
    rec("川止めの年間日数", ok5, " ／ ".join(rows))
    rec("月の重み", pm[6] / pm[1] > 2.5 and pm[9] / pm[1] > 2.5 and pm[12] < pm[6] / 2,
        "基準の川止め中の確率 " + "・".join(f"{m}月{100 * pm[m]:.1f}%" for m in range(1, 13)) + f"（6月/1月＝{pm[6] / pm[1]:.1f}倍・9月/1月＝{pm[9] / pm[1]:.1f}倍）")
    # 6. 到着時の待ち：式 ＝ カレンダーのシミュ
    s = cs[BASE]
    ex_hit = float(np.sum(MDAYS * rv.p[1:]) / 365)
    ex_mw = ex_hit * rv.EW
    ex_ge8 = ex_hit * rv.G[8]
    ok6 = (abs(s["hit"] - ex_hit) < 0.005 and abs(s["mean_wait"] - ex_mw) < 4 * s["mean_wait_se"] + 0.08 * ex_mw
           and abs(s["ge8"] - ex_ge8) < 4 * s["ge8_se"] + 0.15 * ex_ge8)   # シミュでは、終わった翌日にすぐ次の川止めが始まると1つの長い待ちに数えるので、式より数%長く出る
    rec("到着時の待ち(式＝シミュ)", ok6,
        f"川止め中に着く確率 式{100 * ex_hit:.2f}% sim{100 * s['hit']:.2f}% ／ 待ちの平均 式{ex_mw:.3f}日 sim{s['mean_wait']:.3f}日(±{s['mean_wait_se']:.3f}) ／ "
        f"待ち8日以上 式{100 * ex_ge8:.2f}% sim{100 * s['ge8']:.2f}%(±{100 * s['ge8_se']:.2f}) ／ 川止め中に着いたときの待ちの平均 {rv.EW:.2f}日（平均の長さ{rv.EL:.1f}日の約{rv.EW / rv.EL:.2f}倍＝長さ偏りで長い川止めに当たりやすい）。シミュが式より数%長いのは、終わった翌日に次の川止めが始まると1つの長い待ちに数えるため")
    # 7. MC ≒ 厳密
    R = run_letters(rv, diary, X)
    ex = exact_stats(rv, diary)
    mc_on = 100 * float((R["delay"] == 0).mean())
    mc_6 = 100 * float((R["delay"] >= 6).mean())
    mc_md = float(R["delay"].mean())
    se_on = 100 * math.sqrt(ex["on_time"] / 100 * (1 - ex["on_time"] / 100) / N)
    se_6 = 100 * math.sqrt(ex["d6"] / 100 * (1 - ex["d6"] / 100) / N)
    se_md = float(R["delay"].std(ddof=1) / math.sqrt(N))
    ok7 = abs(mc_on - ex["on_time"]) < 4 * se_on and abs(mc_6 - ex["d6"]) < 4 * se_6 and abs(mc_md - ex["delay_mean"]) < 4 * se_md
    rec("1万通 ≒ 厳密計算", ok7, f"約束どおり {mc_on:.2f}% / 厳密 {ex['on_time']:.2f}%（±{se_on:.2f}）・6日以上遅れ {mc_6:.2f}% / {ex['d6']:.2f}%（±{se_6:.2f}）・"
        f"遅れの平均 {mc_md:.3f}日 / {ex['delay_mean']:.3f}日（±{se_md:.3f}）")
    P = run_pairs(rv, diary, MAIN_SEED, 1)
    mw = float(P["wf"].mean())
    exw = float(np.mean([np.mean(rv.p[diary.month_of(diary.ords + OFF[1])] * rv.EW)]))
    se_w = float(P["wf"].std(ddof=1) / math.sqrt(N))
    rec("速い便の川止めの待ち ≒ 厳密", abs(mw - exw) < 4 * se_w, f"sim {mw:.3f}日 / 厳密 {exw:.3f}日（±{se_w:.3f}）")
    # 8. 再現
    a = stable_flat(summarize(rv, diary, MAIN_SEED))
    b = stable_flat(summarize(rv, diary, MAIN_SEED))
    rec("同じ種で同じ結果", a == b, f"主な数字13個が2回で一致={a == b}")
    return res, allok


# ============================================================
# 計算
# ============================================================
def compute():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    diary = Diary()
    print(f"日記 {diary.n}日")
    rvs = [River(diary, a, b, c) for _, a, b, c in SCEN]
    main = summarize(rvs[BASE], diary, MAIN_SEED)
    scen = []
    for (nm, a, b, c), rv in zip(SCEN, rvs):
        S = main if nm == "基準" else summarize(rv, diary, MAIN_SEED)
        scen.append(dict(name=nm, days_year=a, mean_len=b, tail_p=c, annual=rv.annual, EL=rv.EL, EW=rv.EW, p=[float(x) for x in rv.p[1:]],
                         flat=flat_numbers(S), q1_cards=S["q1"]["cards"], q1=dict(on_time=S["q1"]["on_time"], d0=S["q1"]["d0"], d1=S["q1"]["d1"],
                         d2_5=S["q1"]["d2_5"], d6=S["q1"]["d6"], d10=S["q1"]["d10"], T_median=S["q1"]["T_median"], T_mean=S["q1"]["T_mean"],
                         delay_max=S["q1"]["delay_max"], river_hit=S["q1"]["river_hit"]),
                         q2=S["q2"], q3=dict(median=S["q3"]["median"], mean=S["q3"]["mean"], p90=S["q3"]["p90"], max=S["q3"]["max"],
                         ge14=S["q3"]["ge14"], ge21=S["q3"]["ge21"], by_kind=S["q3"]["by_kind"]), exact=S["exact"]))
    rob = []
    for sd in [MAIN_SEED] + ROB_SEEDS:
        S = main if sd == MAIN_SEED else summarize(rvs[BASE], diary, sd)
        d = flat_numbers(S)
        d["seed"] = sd
        rob.append(d)
    checks, ok = run_checks(diary)
    data = dict(slug=SLUG, made=time.strftime("%Y-%m-%d %H:%M"), n=N, main_seed=MAIN_SEED, rob_seeds=ROB_SEEDS, kinds=KNAME,
                p_late1=P_LATE1, river_frac=RIVER_FRAC, off=[int(x) for x in OFF], write_range=list(WRITE_RANGE), diary_days=diary.n,
                rain_share=[float(x) for x in diary.rain_share[1:]], known_days=[int(x) for x in diary.known_n[1:]],
                main=main, scenarios=scen, robustness=rob, checks=checks, checks_all_ok=bool(ok), seconds=round(time.time() - t0, 1))
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1, default=_js), encoding="utf-8")
    print("書き出し:", OUT / "data.json", f"（{time.time() - t0:.0f}秒）")
    return data


def _js(o):
    if hasattr(o, "item"):
        return o.item()
    return str(o)


# ============================================================
# numbers.md
# ============================================================
def pc(x, d=1):
    return f"{x:.{d}f}%"


def fm(x, d=1):
    return f"{x:.{d}f}"


def river_txt(c, back=False):
    pre = "帰り: " if back else ""
    w = c["back_river_wait"] if back else c["river_wait"]
    L = c["back_river_len"] if back else c["river_len"]
    k = c["back_river_day"] if back else c["river_day"]
    if w == 0:
        return pre + "川止めなし"
    return pre + f"大井川が川止め（全部で{L}日・着いたのは{k}日目・待ち{w}日）"


def card_line(c, label):
    return (f"- {label}: {c['date']}出し・{c['kind']}・ふだんの遅れ+{c['normal_delay']}日・{river_txt(c)} → **{c['T']}日で着いた**"
            f"（約束{c['D']}日・遅れ{c['delay']}日）")


def write_numbers(D):
    M = D["main"]
    q1, q2, q3 = M["q1"], M["q2"], M["q3"]
    ex = M["exact"]
    n = D["n"]
    L = []
    a = L.append
    a(f"# 飛脚の手紙 — 数字（{D['made']} 作成）")
    a("")
    a(f"江戸→伊勢（東海道・大井川を渡る）。1万通（種 {D['main_seed']}・基準の川止め）。出す日＝日記{D['diary_days']}日から一様（新暦の月日だけ使う）。"
      f"便＝五日限・六日限・八日限を1/3ずつ（仮定）。")
    a(f"ふだんの遅れ＝紀州藩33件の形（ちょうど24件=73%・+1日9件=27%）を借りた仮定。川止めは**すべて仮定**（大井川1本・下の置き方）。")
    a("")
    sc = D["scenarios"][BASE]
    a("## 川止めの仮定（基準）")
    a(f"- 年間の川止め日数 {sc['days_year']}日（÷365＝{100 * sc['days_year'] / 365:.1f}%）。月の重み＝日記の雨雪の日の割合。")
    a("- 月ごとの川止め中の確率（基準）: " + "・".join(f"{m + 1}月{100 * p:.1f}%" for m, p in enumerate(sc["p"])))
    a("- 月の雨雪の日の割合（日記・天気が分かる日のうち）: " + "・".join(f"{m + 1}月{100 * p:.1f}%" for m, p in enumerate(D["rain_share"])))
    a(f"- 川止め1回の長さ: 平均{sc['EL']:.1f}日（1〜7日の幾何分布96%＋8〜28日の一様4%）。最長28日。")
    a(f"- 川止め中に着いたときの待ち: 平均{sc['EW']:.2f}日（平均の長さ{sc['EL']:.1f}日より長い。長い川止めほど当たりやすい偏りが、途中で着いて残りだけ待つ効果を上回る）。")
    a(f"- 大井川に着く日: 五日限は出発の{D['off'][0]}日目・六日限{D['off'][1]}日目・八日限{D['off'][2]}日目（道のりのほぼ半分）。")
    a(f"- 川止めに当たった（着いた日が川止め中）手紙: **{pc(q1['river_hit'])}**")
    a("")
    a("## 全体（問い1）")
    a(f"- **約束の日までに着いた: {pc(q1['on_time'])}（100通に{q1['on_time']:.0f}通）** — 厳密計算 {pc(ex['on_time'], 2)}")
    a(f"- 日数: **中央値 {fm(q1['T_median'], 0)}日**、平均 {fm(q1['T_mean'], 2)}日。遅れ（約束との差）: 中央値 {fm(q1['delay_median'], 0)}日・平均 {fm(q1['delay_mean'], 2)}日")
    a("")
    a("| 便 | 通数 | 約束どおり | +1日 | 日数中央値 | 日数平均 | 6日以上遅れ | 最大の遅れ |")
    a("|---|---|---|---|---|---|---|---|")
    for b in q1["by_kind"]:
        a(f"| {b['kind']} | {b['n']} | {pc(b['on_time'])} | {pc(b['d1'])} | {fm(b['T_median'], 0)}日 | {fm(b['T_mean'], 2)}日 | {pc(b['d6'])} | {b['delay_max']}日 |")
    a("")
    c = q1["cards"]
    a("### いちばん遅かった手紙・いちばん早かった手紙・中央値の手紙")
    a(card_line(c["worst"], f"いちばん遅かった（遅れ{c['worst']['delay']}日。同じ遅れの手紙 {c['worst_n']}通）"))
    a(card_line(c["best"], f"いちばん早かった（{c['best_n']}通が同じ。五日限でふだんの遅れなし・川止めなし）"))
    a(card_line(c["median"], "中央値の手紙（日数が中央値の最初の1通）"))
    a("")
    a("## 問い1 約束の日に、間に合う？")
    a("### 遅れの分布")
    a("")
    a("| 遅れ | 0日(約束どおり) | 1日 | 2〜5日 | 6日以上 | （参考）10日以上 | 20日以上 |")
    a("|---|---|---|---|---|---|---|")
    a(f"| 割合 | {pc(q1['d0'])} | {pc(q1['d1'])} | {pc(q1['d2_5'])} | {pc(q1['d6'], 2)} | {pc(q1['d10'], 2)} | {pc(q1['d20'], 2)} |")
    a("")
    a(f"- 遅れ日数の合計のうち、**6日以上遅れた手紙が占める割合 {pc(q1['share_days_from_d6'])}**（遅れの平均は小さいが、尾が日数の大半を占める）")
    a(f"- 遅れの最大 {q1['delay_max']}日（日数 {q1['T_max']}日）")
    a("")
    a("### 月ごとの「6日以上遅れた割合」（出した月）")
    a("")
    a("| 月 | 通数 | 約束どおり | 6日以上遅れ | 川止めに当たった | 遅れの平均 |")
    a("|---|---|---|---|---|---|")
    for b in q1["by_month"]:
        a(f"| {b['month']}月 | {b['n']} | {pc(b['on_time'])} | **{pc(b['d6'])}** | {pc(b['river_hit'])} | {fm(b['delay_mean'], 2)}日 |")
    a("")
    a("※ 月ごとの通数は約830通なので、6日以上遅れの割合の標準誤差は±0.5〜1.0ポイント程度。月の並び（6・9月が多く冬が少ない）は仮定した重みの反映であって、結果で確かめたものではない。")
    a("")
    for key, nm in (("六日限v八日限", "六日限 と 八日限"), ("五日限v八日限", "五日限 と 八日限")):
        Q = q2[key]
        a(f"## 問い2 急ぎ便（{nm} を同じ日に同時に出す）")
        if key.startswith("六日"):
            a("- 賃の比（表1）: 松坂 7.2匁÷3匁＝**2.4倍**、山田 12匁÷4.2匁＝**約2.9倍**。日限を2日縮める。")
        else:
            a("- 賃の比（表1）: 津 4.8匁÷3匁＝**1.6倍**（五日限と八日限が両方ある行き先は津だけ）。日限を3日縮める。")
        a(f"- 日限の差 {Q['nominal']}日。川止めに当たった（どちらかが待った）: {pc(Q['river_hit_any'])}・2通とも待った: {pc(Q['river_hit_both'])}・速い便が待った: {pc(Q['river_hit_fast'])}")
        a("")
        a("| 読み | 得した日数の中央値 | 平均 | 差が消えた(同じ日に着いた) | 高い便のほうが遅かった | 川止めに当たった手紙のうち差が消えた(逆転含む) | 2通とも待った手紙のうち差が消えた |")
        a("|---|---|---|---|---|---|---|")
        for w, lab in (("A", "A 川明けのあとも速さの得は残る（基本）"), ("B", "B 川明けは同じ日数で着く（強めの仮定）")):
            d = Q[w]
            a(f"| {lab} | {fm(d['median'], 0)}日 | {fm(d['mean'], 2)}日 | **{pc(d['same'], 2)}** | {pc(d['reversed'], 2)} | {pc(d['hit_le0'])} | {pc(d['both_le0'])} |")
        a("")
        a("得した日数の分布（%）:")
        a("")
        a("| 読み | " + " | ".join(x["label"] for x in Q["A"]["dist"]) + " |")
        a("|---|" + "---|" * len(Q["A"]["dist"]))
        for w in ("A", "B"):
            a(f"| {w} | " + " | ".join(pc(x["pct"], 2) for x in Q[w]["dist"]) + " |")
        a("")
        a(f"- 川止めに当たらなかった手紙の得の中央値: {fm(Q['A']['clear_median'], 0)}日／2通とも待った手紙の得の中央値: A {fm(Q['A']['both_median'], 0)}日・B {fm(Q['B']['both_median'], 0)}日")
        for w in ("A", "B"):
            cd = Q[w]["cards"]
            lab = "A" if w == "A" else "B"

            def pl(c, t):
                bits = (f"{c['date']}出し・ふだんの遅れ 速い便+{c['fast_normal_delay']}/八日限+{c['slow_normal_delay']}・川止めの待ち 速い便{c['fast_river_wait']}日/八日限{c['slow_river_wait']}日"
                        f"（川止め全部で{c['river_len']}日）→ 速い便{c['T_fast']}日・八日限{c['T_slow']}日（得{c['gain']}日）")
                return f"- [{lab}] {t}: " + bits
            a(pl(cd["best"], f"いちばん得した手紙（得{cd['gmax']}日）"))
            a(pl(cd["worst"], f"いちばん得しなかった手紙（得{cd['gmin']}日・同じ得の手紙{cd['worst_n']}通）"))
            a(pl(cd["typical"], "ふつうの手紙（川止めなし・得が中央値）"))
        a("")
    a("## 問い3 返事が来るまで、何日待つ？")
    a(f"往き ＋ 相手が書く時間（{D['write_range'][0]}〜{D['write_range'][1]}日・一様・仮定）＋ 帰り（同じ便・別のくじ）。")
    a("")
    a(f"- **全体（三つの便が1/3ずつ）: 中央値 {fm(q3['median'], 0)}日**、平均 {fm(q3['mean'], 1)}日、上位10%は{fm(q3['p90'], 0)}日以上。**いちばん長かった人 {q3['max']}日**（最短 {q3['min']}日）")
    a(f"- **2週間（14日）以上待った人: {pc(q3['ge14'])}**（3週間以上 {pc(q3['ge21'])}・4週間以上 {pc(q3['ge28'], 2)}）。往復とも川止め中に着いた人 {pc(q3['both_river'], 2)}・どちらかで当たった人 {pc(q3['any_river'])}")
    a("- 約束どおりなら（往復の日限＋書く時間の中央値）: 全体 " + f"{fm(q3['plan_median'], 0)}日")
    a("")
    a("| 便 | 約束どおりなら(中央値) | 返事の中央値 | 平均 | 上位10% | 最長 | 2週間以上 | 3週間以上 |")
    a("|---|---|---|---|---|---|---|---|")
    for b in q3["by_kind"]:
        a(f"| {b['kind']} | {fm(b['plan_median'], 0)}日 | {fm(b['median'], 0)}日 | {fm(b['mean'], 1)}日 | {fm(b['p90'], 0)}日 | {b['max']}日 | {pc(b['ge14'])} | {pc(b['ge21'])} |")
    a("")
    a("※ 八日限は往復の約束だけで16日＋書く時間なので、必ず2週間を超える。「6日＋6日で2週間かからない」と言えるのは六日限の話。")
    a("")
    cr = q3["cards"]

    def rl(c, t):
        return (f"- {t}: 往き {c['date']}出し・{c['kind']}・ふだんの遅れ+{c['normal_delay']}日・{river_txt(c)}→{c['T']}日 ／ 書く{c['write']}日 ／ 帰り {c['back_date']}出し・ふだんの遅れ+{c['back_normal_delay']}日・"
                f"{river_txt(c, True)}→{c['T2']}日 → **返事まで{c['reply']}日**")
    a(rl(cr["worst"], f"いちばん長かった人（同じ長さの人 {cr['worst_n']}人）"))
    a(rl(cr["best"], "いちばん短かった人"))
    a(rl(cr["median"], "中央値の人（全体の中央値に等しい最初の1通）"))
    a("")
    a("## 幅：川止めの3本（少なめ・基準・多め）で、主な数字がどう動くか")
    a("")
    a("| 川止め | 年間日数 | 平均の長さ | 尾(8〜28日) | 川止めに当たった | 約束どおり | 日数の中央値 | 日数の平均 | 6日以上遅れ | 最大の遅れ |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for s in D["scenarios"]:
        f = s["flat"]
        a(f"| {s['name']} | {s['days_year']}日 | {s['mean_len']}日 | {pc(100 * s['tail_p'], 0)} | {pc(s['q1']['river_hit'])} | {pc(f['約束どおりに着いた%'])} | {fm(f['日数の中央値'], 0)}日 | {fm(f['日数の平均'], 2)}日 | {pc(f['6日以上遅れ%'], 2)} | {f['いちばん遅れた日数']}日 |")
    a("")
    a("| 川止め | 急ぎ便(六日限vs八日限)の得の中央値 | 差が消えた A | 差が消えた B | 返事の中央値(全体) | 返事2週間以上 | 返事の最長 | 六日限の返事 中央値 | 六日限で2週間以上 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for s in D["scenarios"]:
        f = s["flat"]
        a(f"| {s['name']} | {fm(f['急ぎ便の得(A)中央値'], 0)}日 | {pc(f['差が消えた%(A)'], 2)} | {pc(f['差が消えた%(B)'], 2)} | {fm(f['返事の中央値'], 0)}日 | {pc(f['返事2週間以上%'])} | {f['返事の最長']}日 | {fm(f['六日限の返事の中央値'], 0)}日 | {pc(f['六日限の返事2週間以上%'])} |")
    a("")
    a("## 頑健さ：種を5つ変えたとき（基準・1万通ずつ）")
    a("")
    keys = [k for k in D["robustness"][0] if k != "seed"]
    a("| 数字 | 主の種 | " + " | ".join(str(s) for s in D["rob_seeds"]) + " | 最小〜最大 |")
    a("|---|---|" + "---|" * len(D["rob_seeds"]) + "---|")
    for k in keys:
        vals = [r[k] for r in D["robustness"]]
        fmtv = (lambda v: fm(v, 0)) if k in ("日数の中央値", "急ぎ便の得(A)中央値", "返事の中央値", "六日限の返事の中央値") else \
            ((lambda v: f"{int(v)}") if k in ("いちばん遅れた日数", "返事の最長") else (lambda v: fm(v, 2)))
        a(f"| {k} | " + " | ".join(fmtv(v) for v in vals) + f" | {fmtv(min(vals))}〜{fmtv(max(vals))} |")
    a("")
    a("## 照合（--check）")
    for k, v in D["checks"].items():
        a(f"- {'OK' if v['ok'] else 'NG'} {k}: {v['detail']}")
    a("")
    (OUT / "numbers.md").write_text("\n".join(L), encoding="utf-8")
    print("書き出し:", OUT / "numbers.md")


def main():
    args = sys.argv[1:]
    if "--compute" in args:
        compute()
        return
    if "--check" in args:
        _, ok = run_checks(Diary())
        print("照合:", "すべて通った" if ok else "通らないものがある")
        return
    if "--numbers" in args:
        p = OUT / "data.json"
        if not p.exists():
            compute()
        write_numbers(json.loads(p.read_text(encoding="utf-8")))
        return
    print(__doc__)


_MODEL_CLI = any(a in sys.argv for a in ("--compute", "--check", "--numbers"))
if __name__ == "__main__" and _MODEL_CLI:
    main()
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・声の並び・照合・静止画）。sims/yomichi-long.py と同じ並び・同じ部品（2026-10-28 作成）
# （見開きノート・付せん・章カード・終了画面・区切り lk.Eyecatch・照合・静止画）。モデル（上の計算）には触らない。
# 台本: publish/hikyaku-long/narration_B.md の「## 0」より後の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 絵の方針: 見開きのノートの手描き風。地図（江戸・大井川・伊勢）・川の水位と「川止め」の札・暦（×が増える）・1万マス・棒グラフ・2通の駒。
#   人（あなた・飛脚）は画面の高さの3分の1以上（sims/edo_people.py の町人）。
# 本番の声での書き出しは、この段階ではしない（--fake-voice で確認）。
# ####################################################################################################
import re as _re
from dataclasses import dataclass

import cairo

sys.path.insert(0, str(ROOT))
from engine import core, note
from engine import longform as lf
from engine import longkit as lk
from engine.core import (beat, bell, blip, check_answers, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, shimmer, text, text_width, tick,
                         whoosh)
from engine.note import INK, PAPER, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading
sys.path.insert(0, str(Path(__file__).resolve().parent))
import edo_people  # noqa: E402  町人の絵

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FAKE = "--fake-voice" in sys.argv
NARR_PATH = ROOT / "publish" / SLUG / "narration_B.md"
VOICE_DIR = OUT / "voice"
WORK = OUT / "scene_work"


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本の読み込み（narration_B.md の「## 0」より後の「- 」の行。文言は一字も変えない）
#   「- （無音 4秒・…）」＝声のない区間（Gap） ／ 「- （…）」「- 〔…〕」だけの行＝画面の指示（声にしない）
#   行の終わりの〔…〕＝その文のときの画面の絵（声にしない）
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
    return chaps


CHAPS = parse_narration()
LINES = {}                         # 文の id -> (章, 文)
LINE_NOTE = {}                     # 文の id -> 〔画面の絵〕
GAP_NOTE = {}                      # 無音の id -> 注
GAP_SEC = {}
CH_NOTE0 = {}                      # 章の最初の画面指示（（…）〔…〕のみの行）
SPEED_V = 1.0
END_HOLD = 2.7                                  # 最後の文（登録のお願い）のあとの間（秒）。終了画面を YouTube の最低5秒より長い6〜8秒にする
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
    for p in out:
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
                for j, part in enumerate(parts):
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and j == len(parts) - 1
                    out.append(lf.Line(lid, part, pause=0.3 if n == 0 else ((END_HOLD if n == 4 else 0.6) if last else 0.35), speed=SPEED_V))      # 0章は、どの文のあとも約0.3秒
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
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, safe_pauses=True, **kw)


lf.use()
_syn = _fake_synth if FAKE else _voice_synth
_ITEMS = _breathe(_items())
tl = lf.Timeline(_ITEMS, VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


# ============================================================
# 小さな道具（yomichi-long・chikyu-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"                                     # 約束どおり・短い
GRAY = "#9aa0b6"                                     # 長い・遅れ
DIM = "#cdd0dc"                                      # まだ区分けされていない
FASTC = "#d9553d"                                    # 急ぎ便の駒
SLOWC = "#3a73c8"                                    # ふつうの便の駒
WATER, WATER_D = "#7fb4e0", "#3f7fbf"                # 川の水
GREEN, BROWN = "#a9c98f", "#a9744a"
PERSON_H = 400                                       # 町人の身長（画面の高さの 37%・3分の1 は 360px）


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


def window(t, t0, t1, fi=0.3, fo=0.3):
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


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """付せん。(x, y) は中心（align='left' なら左端）。戻り値は (幅, 高さ)"""
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
    ang = math.atan2(d[1], d[0])
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for s_ in (-1, 1):
        ctx.move_to(tip[0] - size * math.cos(ang + s_ * 0.45), tip[1] - size * math.sin(ang + s_ * 0.45))
        ctx.line_to(*tip)
    ctx.stroke()


def arrow2(ctx, p, q, col, w=6.0, a=1.0, head=22.0):
    line2(ctx, p, q, col, w, a)
    d = (q[0] - p[0], q[1] - p[1])
    n = math.hypot(*d) or 1.0
    arrowhead(ctx, q, (d[0] / n, d[1] / n), col, head, a, w)


def lerp(a, b, u):
    return a + (b - a) * u


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def cross_mark(ctx, cx, cy, r, a=1.0, p=1.0, col=RED, width=11, seed=31):
    """赤ペンの×（外れの印・暦の日付の印）"""
    if p <= 0:
        return
    pen_line(ctx, cx - r, cy - r, cx + r, cy + r, col, seed=seed, width=width, progress=clamp01(p * 2), alpha=a)
    if p > 0.5:
        pen_line(ctx, cx + r, cy - r, cx - r, cy + r, col, seed=seed + 2, width=width, progress=clamp01(p * 2 - 1), alpha=a)


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


def kv(pts, x):
    """折れ線のキーフレーム [(x, y), ...] を x で補間"""
    xs = [p_[0] for p_ in pts]
    ys = [p_[1] for p_ in pts]
    return float(np.interp(x, xs, ys))


# ============================================================
# 準備（データ・時間割）
# ============================================================
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
MQ1, MQ2, MQ3 = RES["main"]["q1"], RES["main"]["q2"], RES["main"]["q3"]
PA = MQ2["六日限v八日限"]["A"]                              # 問い2（急ぎ便 六日限 と ふつうの便 八日限・川明けのあとも速さの得は残る）

# 1万通（モデルと同じ関数・同じ種で取り出す。data.json の数字は変えない。照合で data.json と同じことを確かめる）
_DIARY = Diary()
_RV = River(_DIARY, *SCEN[BASE][1:])
R = run_letters(_RV, _DIARY, draw_letters(MAIN_SEED))


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ---- 場面の合図: 文の一部（手がかり。画面に出る字の側で探す）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    # 0 冒頭
    "c0_q": (0, "何日後に来るでしょうか"), "c0_hand": (0, "に預けます"), "c0_riv": (0, "川止めに当たりました"), "c0_def": (0, "川を渡れなくなること"),
    "c0_cal": (0, "×が増えていきます"), "c0_10k": (0, "1万人が"), "c0_res": (0, "4人に3人は"), "c0_cond": (0, "条件は、画面の"),
    "c0_assume": (0, "仮に置いています"), "c0_next": (0, "確かめます"),
    # 1 約束の日に、間に合う？
    "c1_intro": (1, "最初の問いです"), "c1_yoso": (1, "あなたの予想は"), "c1_10k": (1, "手紙を1万通、出します"), "c1_def": (1, "遅れは、約束の日数との差"),
    "c1_noearly": (1, "早く着く手紙は、ありません"), "c1_kuji": (1, "出す日は、くじで決めます"), "c1_kinds": (1, "約束の日数は、"), "c1_same": (1, "同じ数ずつ分けます"),
    "c1_late1": (1, "約束より1日遅れる手紙があります"), "c1_kishu": (1, "紀州藩が"), "c1_k27": (1, "100件に27件"), "c1_src": (1, "大きな遅れのもとは"),
    "c1_12": (1, "年に十数回"), "c1_50": (1, "あわせて、50日ほどです"), "c1_28d": (1, "28日間という記録"), "c1_rain": (1, "雨の多い月ほど"),
    "c1_diary": (1, "藩屋敷"), "c1_x3": (1, "1月の3倍ほど"), "c1_half": (1, "道のりのほぼ半分"), "c1_moved": (1, "1万通を動かしました"),
    "c1_p64": (1, "100通に64通でした"), "c1_p26": (1, "100通に26通でした"), "c1_p7": (1, "100通に7通です"), "c1_p3": (1, "100通に3通ほどでした"),
    "c1_p10": (1, "10日以上遅れたのは"), "c1_sort": (1, "小さい順に並べた、ちょうど真ん中の"), "c1_medname": (1, "と呼びます"), "c1_tmed": (1, "着くまでの日数の中央値は"),
    "c1_dmed": (1, "約束との差の中央値は"), "c1_each": (1, "1通ずつ見ていきます"), "c1_m1": (1, "中央値と同じ6日だった手紙です"), "c1_m2": (1, "約束より、1日の遅れです"),
    "c1_b1": (1, "いちばん早く着いた手紙です"), "c1_b2": (1, "ちょうどで着きました"), "c1_w1": (1, "いちばん遅れた手紙です"), "c1_w2": (1, "長い川止めが始まりました"),
    "c1_w3": (1, "28日続きました"), "c1_w4": (1, "36日目でした"), "c1_most": (1, "ほとんどの手紙は、約束どおりか"), "c1_avg": (1, "遅れの平均は"),
    "c1_share": (1, "4割ほど"), "c1_only": (1, "川止めに当たった手紙だけです"), "c1_month": (1, "出した月でも"), "c1_apr": (1, "雨の多い季節に出した手紙"),
    "c1_assume": (1, "確かめた結果ではありません"), "c1_ans": (1, "答えです"),
    # 2 2倍以上払って急ぎ便にしたら、得をする？
    "c2_intro": (2, "二つ目の問いです"), "c2_price": (2, "約束が2日短い便"), "c2_3x": (2, "3倍近くになります"), "c2_yen": (2, "円には直さず"),
    "c2_gain": (2, "何日分なのでしょうか"), "c2_yoso": (2, "あなたの予想は"), "c2_how": (2, "比べ方は"), "c2_fast": (2, "1通は、約束が短い"),
    "c2_10k": (2, "1万組"), "c2_hit": (2, "100組に18組"), "c2_both": (2, "100組に10組です"), "c2_clear": (2, "川止めに当たらなかった組では"),
    "c2_ge3": (2, "100組に20組ほど"), "c2_same": (2, "100組に3組だけ"), "c2_paid": (2, "高く払ったのに"), "c2_nrev": (2, "遅く着く組は、ありませんでした"),
    "c2_each": (2, "組を1つずつ"), "c2_t1": (2, "まず、ふつうの組です"), "c2_t2": (2, "急ぎ便は、7日で"), "c2_t3": (2, "得は、2日です"),
    "c2_b1": (2, "いちばん得をした組"), "c2_b2": (2, "川止めが始まる前に川を渡り"), "c2_b3": (2, "長い川止めに捕まり"), "c2_b4": (2, "得は、29日です"),
    "c2_w1": (2, "いちばん得をしなかった組"), "c2_w2": (2, "足止めされました"), "c2_w3": (2, "どちらも31日目"), "c2_w4": (2, "得は0日です"),
    "c2_s1": (2, "2通とも川止めを待った組"), "c2_s2": (2, "得の中央値は、1日"), "c2_s3": (2, "ふだんの2日の得が"), "c2_s4": (2, "待ち時間です"),
    "c2_s5": (2, "得が縮むのです"), "c2_ans": (2, "答えです"),
    # 3 返事が来るまで、何日待つ？
    "c3_intro": (3, "三つ目の問いです"), "c3_sum": (3, "三つを足した日数"), "c3_late": (3, "往きの手紙の遅れは"), "c3_names": (3, "帰りの手紙です"),
    "c3_write": (3, "くじで決めます"), "c3_ise": (3, "伊勢の実家の人"), "c3_back": (3, "帰りの手紙も"), "c3_yoso": (3, "あなたの予想は"),
    "c3_10k": (3, "1万人で数えます"), "c3_med": (3, "中央値は、15日"), "c3_86": (3, "100人に86人"), "c3_wrong": (3, "予想は、外れたということです"),
    "c3_25": (3, "100人に25人"), "c3_9": (3, "100人に9人"), "c3_2": (3, "100人に2人ほど"), "c3_each": (3, "1人ずつ見ていきます"),
    "c3_m1": (3, "まず、中央値の人です"), "c3_m2": (3, "往きは、川止めに少し当たり"), "c3_m3": (3, "返事を書くのに、1日"), "c3_m4": (3, "帰りは、6日で戻りました"),
    "c3_m5": (3, "あわせて、15日です"), "c3_b1": (3, "いちばん短く済んだ人"), "c3_b2": (3, "5日ずつでした"), "c3_b3": (3, "あわせて、11日です"),
    "c3_w1": (3, "いちばん長く待った人"), "c3_w2": (3, "さっきの長い川止め"), "c3_w3": (3, "往きに、36日かかりました"), "c3_w4": (3, "返事を書くのに、2日"),
    "c3_w5": (3, "帰りは、9日で戻りました"), "c3_w6": (3, "1か月半以上"), "c3_w7": (3, "47日目まで"), "c3_w8": (3, "待つことだけです"),
    "c3_ans": (3, "答えです"),
    # 4 まとめ
    "c4_0": (4, "100通に64通が"), "c4_1": (4, "雨の少ない冬"), "c4_2": (4, "待てますか"), "c4_3": (4, "実際の飛脚の遅れを"), "c4_sub": (4, "チャンネル登録"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in split_reading(txt)[0]]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の切りかえの間（2026-10-29 ユーザー指摘「映像の切り替わりが早すぎる」。yomichi-long.py と同じ）----
#   場面は、その場面で話している文の終わりまで消さない。次の場面は、その最初の文の頭の 1.05秒前（＝前の文の終わり）に出す。
#   そのため、第1章からは、場面の切りかえの前の文のあとの間を SCENE_GAP 秒以上にする（声の文は変えない。間だけ）。
#   冒頭（第0章）は間を足さない（結果の数字を30秒以内に言うため。0章の間は 0.3秒のまま）→ 0章の場面は前の文の終わりで切りかえる。
SCENE_GAP = 1.05
SCENE_KEYS = ["c1_10k", "c1_def", "c1_kuji", "c1_kinds", "c1_late1", "c1_src", "c1_rain", "c1_half", "c1_moved", "c1_p64", "c1_sort", "c1_each", "c1_m1",
              "c1_b1", "c1_w1", "c1_most", "c1_month", "c1_ans",
              "c2_price", "c2_gain", "c2_how", "c2_hit", "c2_paid", "c2_each", "c2_t1", "c2_b1", "c2_w1", "c2_s1", "c2_s4", "c2_ans",
              "c3_sum", "c3_ise", "c3_yoso", "c3_10k", "c3_each", "c3_m1", "c3_b1", "c3_w1", "c3_ans", "c4_1", "c4_2"]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {"c1_moved": 2.1, "c1_b2": 1.5, "c1_w4": 1.7, "c1_assume": 6.55, "c3_2": 1.5, "c3_b3": 2.0}


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


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


# ---- 区切り（問い2と問い3のあいだ。声なし約4秒。lk.Eyecatch: 左ページ「ここまで」・右ページ「ここから」・亀が左から右へ歩く）----
REST = [g_ for g_ in GAP_NOTE if "区切り" in GAP_NOTE[g_]]
T_RS0 = S(REST[0]) if len(REST) == 1 else 0.0
T_RS1 = E(REST[0]) if len(REST) == 1 else 0.0
T_ES = Sk("c4_sub") - 0.3                                  # 終了画面の始まり（登録のお願いの文の頭の少し前から）



# ============================================================
# 絵の部品（人・駒・地図・川・暦・1万マス）。見開きのノートの手描き風
# ============================================================
HIK_KIMONO = "#b4503c"
ANATA_KIMONO = "#4d6fb3"
AITE_KIMONO = "#a8567f"


def person(ctx, cx, fy, h, t=0.0, pose="stand", face=1, kimono=ANATA_KIMONO, a=1.0, lookup=False, lean=None, speed=1.1):
    """町人（sims/edo_people.py の横向きの町人）。(cx, fy)=足もと中央、h=身長、face=+1 右向き。pose: stand／walk／grope（片手を前へ）"""
    if a <= 0.003:
        return
    ph = (t * speed) % 1.0 if pose in ("walk", "grope") else 0.0
    edo_people.draw_townsman(ctx, cx, fy, h, pose=pose, phase=ph, facing=face, kimono=kimono, a=a, lookup=lookup, lean=lean)


def hand_pos(cx, fy, h, face=1):
    """差し出した手（grope）の位置。手紙を持たせる所"""
    u = h / 100.0
    return cx + face * 31.0 * u, fy - 68.0 * u


def hikyaku(ctx, cx, fy, h, t=0.0, run=True, face=1, a=1.0, speed=1.9, reach=False):
    """飛脚（町人の走る形＋肩に担ぎ棒と状箱）。reach=True なら手を前に差し出して立つ（手紙を受け取る）"""
    if a <= 0.003:
        return
    ph = (t * speed) % 1.0 if run else 0.0
    edo_people.draw_townsman(ctx, cx, fy, h, pose="walk" if run else ("grope" if reach else "stand"), phase=ph, facing=face, kimono=HIK_KIMONO, a=a,
                             lean=0.17 if run else (0.04 if reach else 0.0))
    u = h / 100.0
    ctx.save()
    ctx.translate(cx, fy)
    ctx.scale(face * u, u)
    ctx.translate(0, -0.8 * abs(math.sin(2 * math.pi * ph)) if run else 0.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb("#8a6a45", a))                       # 担ぎ棒
    ctx.set_line_width(1.9)
    ctx.move_to(30, -64)
    ctx.line_to(-26, -92)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, a))                             # 状箱（棒の後ろに下げる）
    ctx.set_line_width(0.9)
    ctx.move_to(-26, -92)
    ctx.line_to(-26, -80)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#2b2b35", a))
    rrect(ctx, -35, -80, 18, 15, 1.5)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb("#c9a44a", a))
    ctx.set_line_width(1.1)
    ctx.stroke()
    ctx.arc(-26, -72.5, 1.5, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def koma(ctx, cx, cy, s, col=FASTC, a=1.0, tilt=0.0):
    """手紙の駒（封筒＋色の印）。(cx, cy)=中心、s=大きさ"""
    if a <= 0.003:
        return
    w, h = 1.7 * s, 1.15 * s
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(tilt)
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.2 * a)
    rrect(ctx, -w / 2 + s * 0.08, -h / 2 + s * 0.12, w, h, s * 0.12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#fffaf0", a))
    rrect(ctx, -w / 2, -h / 2, w, h, s * 0.12)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(2.0, s * 0.07))
    ctx.stroke()
    ctx.move_to(-w / 2, -h / 2)
    ctx.line_to(0, h * 0.05)
    ctx.line_to(w / 2, -h / 2)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.arc(0, h * 0.1, s * 0.2, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def house(ctx, cx, fy, w, a=1.0):
    """小さな家。(cx, fy)=足もとの中心"""
    if a <= 0.003:
        return
    h = 0.62 * w
    ctx.save()
    ctx.translate(cx, fy)
    ctx.set_source_rgba(*hexrgb("#d8c9a4", a))
    ctx.rectangle(-w / 2, -h, w, h)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#4a3a2a", a))
    ctx.move_to(-w * 0.6, -h)
    ctx.line_to(w * 0.6, -h)
    ctx.line_to(w * 0.4, -h - w * 0.3)
    ctx.line_to(-w * 0.4, -h - w * 0.3)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#6b4f33", a))
    ctx.rectangle(-w * 0.12, -h * 0.62, w * 0.24, h * 0.62)
    ctx.fill()
    ctx.restore()


def torii(ctx, cx, fy, w, a=1.0):
    """鳥居（伊勢）"""
    if a <= 0.003:
        return
    h = 0.95 * w
    ctx.save()
    ctx.translate(cx, fy)
    ctx.set_source_rgba(*hexrgb("#c2412f", a))
    ctx.rectangle(-w * 0.36, -h, w * 0.1, h)
    ctx.rectangle(w * 0.26, -h, w * 0.1, h)
    ctx.fill()
    ctx.rectangle(-w * 0.5, -h * 1.02, w, h * 0.11)
    ctx.rectangle(-w * 0.42, -h * 0.8, w * 0.84, h * 0.07)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(2.5)
    ctx.rectangle(-w * 0.5, -h * 1.02, w, h * 0.11)
    ctx.stroke()
    ctx.restore()


class RouteMap:
    """東海道の簡単な地図（江戸 ─ 大井川 ─ 伊勢）。f = 道のりの割合（0=江戸・1=伊勢）。川は道のりの真ん中。
    (x0,y0)-(x1,y1) が地図の枠。lanes=2 なら道を広く取り、駒を上下2段に置く"""
    WR = 110.0                                           # 川の幅（水位0のとき）

    def __init__(self, x0, y0, x1, y1, lanes=1, label_size=44):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.xr0, self.xr1 = x0 + 190.0, x1 - 190.0
        self.L = self.xr1 - self.xr0
        self.xc = (self.xr0 + self.xr1) / 2
        self.lanes = lanes
        self.ls = label_size
        self.ymid = y0 + (y1 - y0) * 0.56
        self.fb = 0.5 - (self.WR / 2 + 36) / self.L        # 川の手前の岸
        self.fa = 0.5 + (self.WR / 2 + 36) / self.L        # 川の向こうの岸

    def x_at(self, f):
        return self.xr0 + f * self.L

    def road_y(self, x):
        return self.ymid + 9.0 * math.sin((x - self.xr0) / self.L * 2 * math.pi * 1.25)

    def draw(self, ctx, a=1.0, level=0.0, sign=0.0):
        if a <= 0.003:
            return
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        ctx.set_source_rgba(*hexrgb("#f1f0db", 0.8 * a))
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * a))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#c7dcb0", 0.55 * a))                  # 野原と山
        ctx.rectangle(x0 + 6, y1 - (y1 - y0) * 0.30, x1 - x0 - 12, (y1 - y0) * 0.30 - 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb("#b9c6ad", 0.7 * a))
        base = y0 + (y1 - y0) * 0.30
        for mx, mh in ((0.22, 0.20), (0.34, 0.14), (0.66, 0.19), (0.80, 0.15)):
            cx = x0 + (x1 - x0) * mx
            ctx.move_to(cx - 90, base + 22)
            ctx.line_to(cx, base + 22 - (y1 - y0) * mh)
            ctx.line_to(cx + 90, base + 22)
            ctx.close_path()
            ctx.fill()
        rw = 26 + 30 * (self.lanes - 1)                                   # 道
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*hexrgb("#dcc79a", a))
        ctx.set_line_width(rw)
        for k in range(61):
            x = self.xr0 + self.L * k / 60
            (ctx.move_to if k == 0 else ctx.line_to)(x, self.road_y(x))
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#a98d5a", 0.8 * a))
        ctx.set_line_width(3)
        ctx.set_dash([14, 12])
        for k in range(61):
            x = self.xr0 + self.L * k / 60
            (ctx.move_to if k == 0 else ctx.line_to)(x, self.road_y(x))
        ctx.stroke()
        ctx.set_dash([])
        wr_ = self.WR * (1.0 + 0.55 * level)                              # 川（水位で広がる）
        xa = self.xc - wr_ / 2
        ctx.set_source_rgba(*hexrgb(WATER_D if level > 0.5 else WATER, 0.92 * a))
        ctx.rectangle(xa, y0 + 6, wr_, y1 - y0 - 12)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.55 * a)
        ctx.set_line_width(3)
        for k in range(5):
            yy = y0 + 76 + k * (y1 - y0 - 110) / 4
            ctx.move_to(xa + 12, yy)
            for j in range(1, 5):
                ctx.curve_to(xa + 12 + (j - 0.5) * (wr_ - 24) / 4, yy + (-9 if (j + k) % 2 else 9), xa + 12 + (j - 0.5) * (wr_ - 24) / 4, yy,
                             xa + 12 + j * (wr_ - 24) / 4, yy)
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#dcc79a", 0.55 * a))                 # 川の上の道（渡し）
        ctx.set_line_width(rw)
        ctx.move_to(xa, self.road_y(xa))
        ctx.line_to(xa + wr_, self.road_y(xa + wr_))
        ctx.stroke()
        for k, dx in enumerate((-52, 0, 52)):                             # 江戸と伊勢
            house(ctx, self.xr0 + dx - 14, self.road_y(self.xr0) - 20, 52, a=a)
        torii(ctx, self.xr1 + 20, self.road_y(self.xr1) - 18, 92, a=a)
        text(ctx, "江戸", self.xr0 - 18, y1 - 30, self.ls, INK, alpha=a)
        text(ctx, "伊勢", self.xr1 + 24, y1 - 30, self.ls, INK, alpha=a)
        text(ctx, "大井川", self.xc, y0 + 30, self.ls, INK, alpha=a)
        if sign > 0.003:                                                  # 川止めの札
            sx, sy = self.xc, y1 - 62
            ctx.save()
            ctx.translate(sx, sy)
            ctx.set_source_rgba(*hexrgb("#7a5a38", a * sign))
            ctx.rectangle(-5, 0, 10, 46)
            ctx.fill()
            w_ = text_width("川止め", self.ls) + 28
            ctx.set_source_rgba(*hexrgb("#fff4cf", a * sign))
            rrect(ctx, -w_ / 2, -34, w_, 56, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(RED, a * sign))
            ctx.set_line_width(4)
            ctx.stroke()
            ctx.restore()
            text(ctx, "川止め", sx, sy - 6, self.ls, RED, alpha=a * sign)

    def piece(self, ctx, f, lane=0, col=FASTC, s=34, a=1.0, tilt=0.0):
        x = self.x_at(f)
        off = 0.0 if self.lanes == 1 else (-34.0 if lane == 0 else 22.0)
        koma(ctx, x, self.road_y(x) + off - s * 0.9, s, col, a=a, tilt=tilt)


def kf_go(off, wait, T, t0=0.0, fb=0.5, fa=0.5, back=False):
    """片道のキーフレーム [(日, 道のりの割合)]。off=大井川に着く日・wait=川止めの待ち・T=着くまでの日数（t0 日目に出る）。
    back=True なら伊勢→江戸（向こう岸から来る）"""
    if not back:
        pts = [(t0, 0.0), (t0 + off, fb)]
        if wait > 0:
            pts.append((t0 + off + wait, fb))
        pts += [(t0 + off + wait + 0.6, fa), (t0 + T, 1.0)]
    else:
        pts = [(t0, 1.0), (t0 + off, fa)]
        if wait > 0:
            pts.append((t0 + off + wait, fa))
        pts += [(t0 + off + wait + 0.6, fb), (t0 + T, 0.0)]
    return pts


def draw_cross(ctx, cx, cy, r, a=1.0, col=RED, width=9):
    """暦の×（直線2本）"""
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - r, cy - r)
    ctx.line_to(cx + r, cy + r)
    ctx.move_to(cx + r, cy - r)
    ctx.line_to(cx - r, cy + r)
    ctx.stroke()


def calendar(ctx, x0, y0, w, h, n, marks=0.0, promise=None, a=1.0, cols=10, row_cap=92, tint=None, wait=None, num_size=40):
    """暦（日付の格子）。1日目〜n日目。marks=×を付けた日数（小数は書いている途中）、promise=約束の日（赤丸）、
    tint=[((日の範囲 d0, d1 両端含む), 色)]（往き・書く・帰りの色分け）、wait=(d0, d1) 川止めの待ちの日（水色がけ）"""
    if a <= 0.003:
        return 0.0
    rows = int(math.ceil(n / cols))
    cw = w / cols
    chh = min(h / rows, row_cap)
    for d in range(1, n + 1):
        r_, c_ = divmod(d - 1, cols)
        cx, cy = x0 + c_ * cw, y0 + r_ * chh
        col = "#ffffff"
        if tint:
            for (da, db), tc in tint:
                if da <= d <= db:
                    col = tc
        ctx.set_source_rgba(*hexrgb(col, 0.82 * a))
        rrect(ctx, cx + 3, cy + 3, cw - 6, chh - 6, 8)
        ctx.fill()
        if wait and wait[0] < d <= wait[1]:
            ctx.set_source_rgba(*hexrgb(WATER_D, 0.30 * a))
            rrect(ctx, cx + 3, cy + 3, cw - 6, chh - 6, 8)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(2.2)
        rrect(ctx, cx + 3, cy + 3, cw - 6, chh - 6, 8)
        ctx.stroke()
        text(ctx, str(d), cx + 9, cy + 25, num_size, PENCIL_T, align="left", bold=False, alpha=0.85 * a)
    full = int(math.floor(marks + 1e-9))
    for d in range(1, min(full, n) + 1):
        r_, c_ = divmod(d - 1, cols)
        draw_cross(ctx, x0 + c_ * cw + cw / 2 + 12, y0 + r_ * chh + chh / 2 + 10, min(cw, chh) * 0.27, a=a)
    frac = marks - full
    if 0 < frac < 1 and full + 1 <= n:
        r_, c_ = divmod(full, cols)
        draw_cross(ctx, x0 + c_ * cw + cw / 2 + 12, y0 + r_ * chh + chh / 2 + 10, min(cw, chh) * 0.27, a=a * ease_out(frac))
    if promise:
        r_, c_ = divmod(promise - 1, cols)
        pen_circle(ctx, x0 + c_ * cw + cw / 2, y0 + r_ * chh + chh / 2, cw * 0.46, chh * 0.46, RED, seed=5 + promise, width=6, progress=1.0, alpha=a)
    return chh * rows


class Grid10k:
    """100×100 のマスに1万。cls=マスごとの区分（0..K-1。行の左から右・上から下の順）。pal=区分ごとの色。
    base=まだ区分けされていないときの色。n_fill 個までのマスが現れ、n_split 個（ランダムな順）が区分の色に変わる。1マス＝1通（1人・1組）"""

    def __init__(self, cls, pal, base=DIM, cx=492, y0=170.0, cell=5.0, side=100, seed=11):
        self.n = side * side
        self.side, self.cell, self.cx, self.y0 = side, cell, cx, y0
        self.px = int(round(side * cell))
        self.x0 = cx - self.px / 2
        self.cls = np.asarray(cls)
        assert len(self.cls) == self.n
        px = self.px
        idx = np.full((px, px), 10 ** 9, np.int64)
        for i in range(self.n):
            r_, q_ = i // side, i % side
            ya, yb = int(round(r_ * cell)), int(round((r_ + 1) * cell)) - 1
            xa, xb = int(round(q_ * cell)), int(round((q_ + 1) * cell)) - 1
            idx[ya:yb, xa:xb] = i
        self.idx = idx
        valid = idx < 10 ** 9
        safe = np.where(valid, idx, 0)

        def bgra(h):
            r, g, b = hexrgb(h)[:3]
            return np.array([int(b * 255), int(g * 255), int(r * 255), 255], np.uint8)
        self.img_base = np.zeros((px, px, 4), np.uint8)
        self.img_base[valid] = bgra(base)
        self.img_cls = np.zeros((px, px, 4), np.uint8)
        pc_ = np.where(valid, self.cls[safe], -1)
        for k, h in enumerate(pal):
            self.img_cls[pc_ == k] = bgra(h)
        self.img_empty = np.zeros((px, px, 4), np.uint8)
        self.img_empty[valid] = bgra("#e9e3d3")
        order = np.random.default_rng(seed).permutation(self.n)
        self.rank = np.where(valid, order[safe], 10 ** 9)

    def draw(self, ctx, n_fill, n_split=0, a=1.0):
        if a <= 0.003:
            return
        n_fill = int(max(0, min(self.n, n_fill)))
        img = np.where((self.idx < n_fill)[..., None], self.img_base, self.img_empty)
        if n_split > 0:
            img = np.where(((self.rank < int(n_split)) & (self.idx < n_fill))[..., None], self.img_cls, img)
        buf = np.ascontiguousarray(img)
        s = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, self.px, self.px, self.px * 4)
        ctx.set_source_surface(s, self.x0, self.y0)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(self.x0 - 4, self.y0 - 4, self.px + 6, self.px + 6)
        ctx.stroke()


def cells100(ctx, x0, y0, cell, groups, a=1.0, gap=6):
    """100マス（10×10）。groups=[(個数, 色), …] を左上から順に塗る（残りは薄い灰）"""
    k = 0
    for r_ in range(10):
        for c_ in range(10):
            col = "#dfe2ea"
            m = k
            for n_, cc in groups:
                if m < n_:
                    col = cc
                    break
                m -= n_
            ctx.set_source_rgba(*hexrgb(col, a))
            rrect(ctx, x0 + c_ * cell, y0 + r_ * cell, cell - gap, cell - gap, 7)
            ctx.fill()
            k += 1
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(x0 - 8, y0 - 8, 10 * cell + 4, 10 * cell + 4)
    ctx.stroke()


def river_close(ctx, x0, y0, x1, y1, level, a=1.0, t=0.0, sign=0.0):
    """川ばたの拡大（断面）。level 0→1 で水位が上がる。左に岸（人が立つ）、真ん中が川、右に向こう岸。
    杭に赤い線（川止めの水位）。sign>0 で「川止め」の札が岸に立つ"""
    if a <= 0.003:
        return
    W_, H_ = x1 - x0, y1 - y0
    top = y0 + 0.26 * H_
    bot = y1 - 14
    xl, xr = x0 + 0.30 * W_, x1 - 0.12 * W_
    ctx.save()
    ctx.set_source_rgba(*hexrgb("#f1f0db", 0.7 * a))
    rrect(ctx, x0, y0, W_, H_, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, W_, H_, 16)
    ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb("#c9b48a", a))                           # 岸
    ctx.move_to(x0 + 4, top)
    ctx.line_to(xl, top)
    ctx.line_to(xl + 70, bot)
    ctx.line_to(xr - 70, bot)
    ctx.line_to(xr, top)
    ctx.line_to(x1 - 4, top)
    ctx.line_to(x1 - 4, bot)
    ctx.line_to(x0 + 4, bot)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#a9c98f", a))                           # 草
    ctx.rectangle(x0 + 4, top - 12, xl - x0 - 4, 14)
    ctx.rectangle(xr, top - 12, x1 - xr - 4, 14)
    ctx.fill()
    wy = bot - level * (bot - top + 8) * 0.96                            # 水面
    ctx.set_source_rgba(*hexrgb(WATER, 0.95 * a))
    ctx.move_to(xl + 70 - (bot - wy) * 70 / (bot - top), wy)
    ctx.line_to(xr - 70 + (bot - wy) * 70 / (bot - top), wy)
    ctx.line_to(xr - 70, bot)
    ctx.line_to(xl + 70, bot)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    ctx.set_line_width(4)
    xa, xb = xl + 70 - (bot - wy) * 70 / (bot - top), xr - 70 + (bot - wy) * 70 / (bot - top)
    ctx.move_to(xa, wy)
    n_w = 9
    for k in range(n_w):
        ctx.curve_to(xa + (k + 0.3) * (xb - xa) / n_w, wy - 9 + 3 * math.sin(t * 3 + k), xa + (k + 0.7) * (xb - xa) / n_w, wy + 9 + 3 * math.sin(t * 3 + k),
                     xa + (k + 1) * (xb - xa) / n_w, wy)
    ctx.stroke()
    px = xl + 24                                                         # 杭（水位の目もり）
    ctx.set_source_rgba(*hexrgb("#7a5a38", a))
    ctx.rectangle(px - 6, top - 30, 12, bot - top + 24)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(3)
    for k in range(7):
        yy = bot - 6 - k * (bot - top - 10) / 7
        ctx.move_to(px - 6, yy)
        ctx.line_to(px - 22, yy)
    ctx.stroke()
    ry = top + 26                                                        # 川止めの水位の赤い線
    ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))
    ctx.set_line_width(5)
    ctx.set_dash([16, 12])
    ctx.move_to(px - 28, ry)
    ctx.line_to(xr - 40, ry)
    ctx.stroke()
    ctx.set_dash([])
    if sign > 0.003:                                                     # 川止めの札
        sx, sy = x0 + 0.17 * W_, top - 20
        ctx.set_source_rgba(*hexrgb("#7a5a38", a * sign))
        ctx.rectangle(sx - 6, sy - 6, 12, 80)
        ctx.fill()
        w_ = text_width("川止め", 56) + 36
        ctx.set_source_rgba(*hexrgb("#fff4cf", a * sign))
        rrect(ctx, sx - w_ / 2, sy - 86, w_, 78, 8)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(RED, a * sign))
        ctx.set_line_width(5)
        ctx.stroke()
        text(ctx, "川止め", sx, sy - 47, 56, RED, alpha=a * sign)
    return top


# ============================================================
# 場面の仕組み: 場面 = (名前, 始め, 終わり, 描く関数)。前の場面が消えきってから（0.2秒）次が出る＝文字が重ならない
#   場面の始めは、その場面の最初の文の頭の約1秒前（絵は声より先に。枠は声の0.5秒前までにそろう）
# ============================================================
SCENES = []
SC_IN, SC_OUT, SC_DELAY = 0.25, 0.2, 0.2


def scene(name, t0, t1, fn, first=False):
    SCENES.append((name, t0, t1, fn, first))


def draw_scenes(ctx, t):
    for name, t0, t1, fn, first in SCENES:
        if t < t0 - 1e-6 or t > t1 + SC_OUT:
            continue
        a_in = 1.0 if first else ease_out(clamp01((t - t0 - SC_DELAY) / SC_IN))
        a = a_in * (1.0 - clamp01((t - t1) / SC_OUT))
        grp(ctx, a, fn, t)


def bd(key, lead=1.05):
    """場面の始め（その文の頭の lead 秒前）"""
    return Sk(key) - lead


def bz(key):
    """第0章の場面の始め（前の文を言い終えた時刻＝声の頭の 0.3秒前。0章は間を足せない）"""
    return Sk(key) - 0.3


def stk(ctx, t, key, s, x, y, color="yellow", fg=INK, a=1.0, size=44, tilt=-0.012, off=0.3, frac=0.0, until=None, align="left"):
    """付せん。台本の文（手がかり key）の頭から off 秒あとに現れる。until を過ぎると消える。(x, y)＝align='left' なら左端・中心の高さ"""
    t0 = Sk(key, frac) + off
    if t < t0:
        return 0, 0
    al = a * fade(t, t0)
    if until is not None:
        al *= out_fade(t, until, 0.3)
    return mini_sticky(ctx, s, x, y, size, color, fg=fg, a=al, align=align, tilt=tilt)


def title_hand(ctx, s, x, y, size, seed, a=1.0):
    lk._hand_title(ctx, s, x, y, size, seed, alpha=a)


def seq(t, s, e, fi=0.25, fo=0.15):
    return fade(t, s, fi) * out_fade(t, e, fo)


def dmap(pts):
    """時刻→日数の対応（折れ線）。pts=[(時刻, 日数), …]。戻り値は t を受ける関数（範囲の外は端の値）"""
    ts = [p_[0] for p_ in pts]
    ds = [p_[1] for p_ in pts]
    return lambda t: float(np.interp(t, ts, ds))


# ============================================================
# データ（data.json と、モデルと同じ関数・同じ種で取り出した1万通。数字は data.json の値を四捨五入）
# ============================================================
OFFS = {k: int(OFF[i]) for i, k in enumerate(KNAME)}          # 五日限3・六日限3・八日限4（大井川に着く日）
DLIM = {k: KINDS[i] for i, k in enumerate(KNAME)}
CARDS1 = MQ1["cards"]
CARDS3 = MQ3["cards"]
CARDS2 = PA["cards"]
GE14 = MQ3["ge14"]
N_GRAY = int((R["reply"] >= 14).sum())                         # 2週間以上待った1万人のうちの数（4人に3人）
N_PAIR = {k: int(v) for k, v in zip(("hit", "both"), (round(MQ2["六日限v八日限"]["river_hit_any"]), round(MQ2["六日限v八日限"]["river_hit_both"])))}
SCEN_ON = {s["name"]: s["q1"]["on_time"] for s in RES["scenarios"]}
T_COUNT = np.bincount(R["T"], minlength=40)                     # 着いた日数ごとの通数
REPLY_COUNT = np.bincount(R["reply"], minlength=60)             # 返事が来るまでの日数ごとの人数
RAIN = [100 * x for x in RES["rain_share"]]                     # 月ごとの雨の日の割合（%）
D6_MONTH = [b["d6"] for b in MQ1["by_month"]]                   # 月ごとの「6日以上遅れ」の割合（%）
RAINY = [m_ + 1 for m_, v_ in enumerate(D6_MONTH) if v_ >= 3.5]                    # 雨の多い月（6日以上遅れが100通に4通から5通）
_P6 = run_pairs(_RV, _DIARY, MAIN_SEED, 1)                                          # 六日限v八日限の1万組（モデルと同じ関数・同じ種）
_G6 = _P6["Ts"] - _P6["Tf_A"]
_HIT6 = (_P6["wf"] > 0) | (_P6["ws"] > 0)
CLEAR_GE3 = 100 * float((_G6[~_HIT6] >= 3).mean())                                   # 川止めに当たらなかった組のうち、得が3日以上
GAIN = PA["dist"][1:]                                               # 急ぎ便の得の分布（0日・1日・2日・3日・4日以上）


def pct_txt(v, unit="通"):
    return f"100{unit}に{ihalf(v)}{unit}"


# ============================================================
# 0 冒頭（0秒目から。左にあなた・右に飛脚。声は0.5秒から）
# ============================================================
QLINES = ["返事は 何日後？"]
QTXT = "".join(QLINES)                                  # 題名・サムネと同じ言葉
H0 = PERSON_H
FY = 905                                                 # 足もとの高さ（地面）


def kuji_box(ctx, cx, cy, w, slip=0.0, a=1.0, label=True):
    """くじの箱（上の穴から札が1枚出る）。(cx, cy)=箱の上面の中心。slip=0〜1 で札が出てくる"""
    if a <= 0.003:
        return
    bh = 0.62 * w
    ctx.save()
    ctx.translate(cx, cy)
    if slip > 0:
        sy = -0.10 * w - slip * 0.42 * w
        ctx.save()
        ctx.rotate(-0.08)
        rrect(ctx, -0.13 * w, sy, 0.26 * w, 0.36 * w, 5)
        ctx.set_source_rgba(1, 1, 0.97, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(max(2.5, w * 0.012))
        ctx.stroke()
        ctx.restore()
    ctx.set_source_rgba(*hexrgb("#b98550", a))
    rrect(ctx, -w / 2, 0, w, bh, 8)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(3.0, w * 0.014))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#8a5c33", 0.6 * a))
    ctx.set_line_width(max(2.0, w * 0.007))
    for k in (0.28, 0.5, 0.74):
        ctx.move_to(-w / 2 + 14, bh * k)
        ctx.line_to(w / 2 - 14, bh * k)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#d7a56c", a))
    ctx.move_to(-w / 2, 0)
    ctx.line_to(w / 2, 0)
    ctx.line_to(w / 2 - 0.08 * w, -0.14 * w)
    ctx.line_to(-w / 2 + 0.08 * w, -0.14 * w)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(3.0, w * 0.014))
    ctx.stroke()
    ctx.save()
    ctx.translate(0, -0.07 * w)
    ctx.scale(1, 0.22)
    ctx.arc(0, 0, 0.17 * w, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb("#2a1c10", a))
    ctx.fill()
    if label:
        text(ctx, "くじ", 0, bh * 0.52, w * 0.2, "#fff6df", alpha=a)
    ctx.restore()


def backdrop(ctx, t, a=1.0, y_top=250, y_ground=640):
    """奥の景色（山・遠い川・雲・足もとの野原）。雲はゆっくり流れる"""
    ctx.set_source_rgba(*hexrgb("#dfe8cf", 0.55 * a))
    rrect(ctx, 70, y_ground, 1780, 295, 24)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#b9c6ad", 0.75 * a))
    for cx, mh in ((260, 150), (520, 100), (1000, 130), (1330, 170), (1640, 110)):
        ctx.move_to(cx - 170, y_ground - 8)
        ctx.line_to(cx, y_ground - 8 - mh)
        ctx.line_to(cx + 170, y_ground - 8)
        ctx.close_path()
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(WATER, 0.9 * a))                       # 遠い川
    ctx.rectangle(70, y_ground + 8, 1780, 46)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    ctx.set_line_width(3)
    for k in range(12):
        x = 130 + k * 150 + 12 * math.sin(t * 1.5 + k)
        ctx.move_to(x, y_ground + 31)
        ctx.curve_to(x + 30, y_ground + 22, x + 60, y_ground + 40, x + 90, y_ground + 31)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#dcc79a", 0.9 * a))                   # 遠い道
    ctx.rectangle(70, y_ground + 62, 1780, 22)
    ctx.fill()
    for k, (cx, cy, w) in enumerate(((300, y_top + 30, 150), (900, y_top + 80, 190), (1500, y_top + 10, 160))):
        x = (cx + t * (14 + 5 * k)) % 1900 - 40
        ctx.set_source_rgba(1, 1, 1, 0.8 * a)
        for dx, dy, r in ((0, 0, 0.30), (0.34, -0.12, 0.38), (0.72, 0, 0.30)):
            ctx.arc(x + dx * w, cy + dy * w, r * w * 0.55, 0, 2 * math.pi)
            ctx.fill()


def sc_open(ctx, t):
    text(ctx, QTXT, 960, 108, 104, INK)
    pen_line(ctx, 372, 168, 1572, 162, RED, seed=5, width=8, progress=clamp01(t / 0.7), alpha=0.9)
    backdrop(ctx, t)
    # 東海道と川の札（奥）
    text(ctx, "東海道", 1560, 600, 44, INK, alpha=0.9)
    text(ctx, "大井川", 1290, 628, 44, "#1e3f72", alpha=0.95)
    x_a, x_b = 520, 1010                                  # あなた・飛脚の立つ位置
    t_h = Sk("c0_hand")
    t_go = t_h + 1.3                                      # 手紙を箱に入れて、飛脚が走り出す
    ha = hand_pos(x_a, FY, H0, 1)
    hb = hand_pos(x_b, FY, H0, -1)
    run_u = clamp01((t - t_go) / 2.2)
    xb_now = x_b + (1260 - x_b) * ease_in_out(run_u) if t >= t_go else x_b
    if t < t_go + 0.2:
        person(ctx, x_a, FY, H0, t, "grope", 1, speed=0.0)
    else:
        person(ctx, x_a, FY, H0, t, "stand", 1)
    if t < t_go:
        hikyaku(ctx, x_b, FY, H0, t, run=False, face=-1, reach=True)
    else:
        hikyaku(ctx, xb_now, FY, H0, t, run=run_u < 1.0, face=1)
    # 手紙の動き: あなたの手 → 飛脚の手（2〜4秒）→ 状箱（預けます）
    u1 = ease_in_out(clamp01((t - 2.0) / 1.9))
    if t < t_h + 0.5:
        lx = lerp(ha[0], hb[0], u1)
        ly = ha[1] - 90 * math.sin(math.pi * u1) * 0.35 + 3 * math.sin(t * 5.0)
        koma(ctx, lx, ly, 52, FASTC, tilt=-0.1 + 0.2 * u1)
    elif t < t_go:
        u2 = ease_in_out(clamp01((t - (t_h + 0.5)) / 0.8))
        bx, by = x_b + 26 * H0 / 100.0, FY - 72 * H0 / 100.0
        koma(ctx, lerp(hb[0], bx, u2), lerp(hb[1], by, u2) - 40 * math.sin(math.pi * u2), 52 * (1 - 0.35 * u2), FASTC)
    stk(ctx, t, "c0_hand", "約束の日数\n六日（六日限）", 1330, 345, "yellow", size=52, off=0.5, tilt=0.012, align="center")


# ---- 川止めの場面（地図と川ばた）----
MAP0 = RouteMap(110, 150, 1810, 450)
T_MAP0 = Sk("c0_riv") - 0.4
T_MAP1 = Ek("c0_riv") - 0.6


def sc_c0_river(ctx, t):
    f_end = MAP0.fb
    u = ease_in_out(clamp01((t - T_MAP0) / (T_MAP1 - T_MAP0)))
    sg = fade(t, Ek("c0_riv") - 0.7, 0.4)
    lv = clamp01((t - Sk("c0_def", 0.25)) / (Dk("c0_def") * 0.55))
    MAP0.draw(ctx, level=0.9 * ease_in_out(lv), sign=sg)
    MAP0.piece(ctx, u * f_end, 0, FASTC, s=38)
    # 川ばたの拡大（右）と、立ち止まる飛脚（左）
    river_close(ctx, 640, 490, 1810, 925, level=0.25 + 0.7 * ease_in_out(lv), t=t, sign=fade(t, Sk("c0_def", 0.8), 0.4))
    hikyaku(ctx, 330, 925, 380, t, run=False, face=1)
    stk(ctx, t, "c0_riv", "大井川", 1010, 580, "yellow", size=52, off=-1.4, tilt=-0.01, align="center", until=Sk("c0_def") - 0.3)
    mini_sticky(ctx, "水が増えて、\n渡れない", 1225, 560, 48, "mint", a=fade(t, Sk("c0_def", 0.05), 0.4), tilt=0.012)


# ---- 暦（あなたの暦に×が増える）----
CAL0 = (770, 290, 1040, 460)


def sc_c0_cal(ctx, t):
    t0, t1 = Sk("c0_cal", 0.15), Ek("c0_cal") - 0.15
    day = 15.0 * clamp01((t - t0) / (t1 - t0))
    person(ctx, 360, FY, H0, t, "stand", 1, lookup=False)
    mini_sticky(ctx, "あなたの暦", 1290, 220, 56, "yellow", a=fade(t, bz("c0_cal") + 0.3, 0.4), tilt=-0.012)
    x0, y0, w, h = CAL0
    calendar(ctx, x0 - 20, y0 + 10, w + 40, h, 21, marks=day, promise=6, cols=7, row_cap=150)
    la = fade(t, Sk("c0_cal", 0.4), 0.4)
    mini_sticky(ctx, "約束の日", 1210, 840, 48, "pink", a=la, tilt=0.01)
    pa = clamp01((t - Sk("c0_cal", 0.4)) / 0.6)
    arrow2(ctx, (1290, 806), (1415 - 150 + 330 - 20, 650), RED, w=5, a=pa * 0.9, head=18)


# ---- 1万マス・結果の数字・条件 ----
GRID0 = Grid10k((R["reply"] >= 14).astype(int), [BLUE, GRAY], base=DIM, cx=LCX, y0=190.0, cell=5.0, seed=11)
T_GRID0 = bz("c0_10k")
T_GFILL = (Sk("c0_10k", 0.1), Ek("c0_10k") - 0.4)
T_SPLIT0 = Sk("c0_res", 0.3)
T_SPLIT1 = T_SPLIT0 + 1.4
COND_ROWS = [("江戸→伊勢・東海道", 0.0), ("料金と約束の日数は飛脚屋（京屋）の表", 0.6), ("出す日はくじ", 1.2), ("川止めの起きやすさは仮定", 1.8)]


def cond_sheet(ctx, t):
    t0 = Sk("c0_cond") - 0.2
    a = fade(t, t0, 0.4)
    if a <= 0.003:
        return
    x0, y0, w, h = RX - 12, 530, 830, 400
    ctx.save()
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, x0 + 5, y0 + 8, w, h, 6)
    ctx.fill()
    fill(ctx, hexrgb(STICKY["yellow"], a))
    rrect(ctx, x0, y0, w, h, 6)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(x0, y0, w, 12)
    ctx.fill()
    text(ctx, "条件", RX + 20, y0 + 40, 44, RED, align="left", alpha=a)
    yc = y0 + 96
    last = None
    for s_, off in COND_ROWS:
        wr(ctx, s_, RX + 20, yc + 30, 42, INK, Sk("c0_cond") + off, t, cps=16.0, align="left", alpha=a)
        last = yc + 30
        yc += 68
    ctx.restore()
    pa = clamp01((t - Sk("c0_assume", 0.62)) / 0.8)
    if pa > 0:
        pen_circle(ctx, RX + 20 + text_width(COND_ROWS[-1][0], 42) / 2, last, text_width(COND_ROWS[-1][0], 42) / 2 + 40, 44, RED, seed=7, width=6, progress=pa, alpha=a)


def sc_c0_grid(ctx, t):
    cap_a = fade(t, T_GRID0, 0.25)
    text(ctx, "1マス＝1人", LCX, GRID0.y0 - 46, 56, INK, alpha=cap_a)
    f0, f1 = T_GFILL
    nf = int(N * clamp01((t - f0) / (f1 - f0)) ** 1.5) if t >= T_GRID0 + 0.3 else 0
    ns = int(N * ease_in_out(clamp01((t - T_SPLIT0) / (T_SPLIT1 - T_SPLIT0))))
    GRID0.draw(ctx, nf, ns, a=fade(t, T_GRID0, 0.25))
    la = fade(t, T_SPLIT1 - 0.2, 0.4)
    text(ctx, "灰色＝2週間以上　青＝それより短い", LCX, GRID0.y0 + GRID0.px + 56, 46, INK, alpha=la)
    # くじの箱（右ページ。1万人の文のあいだだけ）
    ka = fade(t, T_GRID0 + 0.2, 0.3) * out_fade(t, Sk("c0_res") - 0.5, 0.3)
    if ka > 0.003:
        kuji_box(ctx, RCX, 430, 380, slip=ease_in_out(clamp01((t - (Sk("c0_10k") + 0.6)) / 1.2)), a=ka)
        mini_sticky(ctx, "便を、くじで選ぶ", RCX, 760, 56, "yellow", a=ka, tilt=-0.012)
    # 結果の数字（声に合わせて）
    ra = fade(t, Sk("c0_res", 0.18), 0.4)
    if ra > 0.003:
        mini_sticky(ctx, "4人に3人が\n2週間以上", RCX, 200, 80, "pink", fg=RED, a=ra, tilt=-0.012)
    ma = fade(t, Sk("c0_res", 0.75), 0.4)
    if ma > 0.003:
        mini_sticky(ctx, "中央値 15日\n（小さい順に並べた、\nちょうど真ん中）", RCX, 425, 44, "yellow", a=ma, tilt=0.01)
    cond_sheet(ctx, t)


# ---- 3つの問いの札 ----
TAGS = [("問い1\n約束の日に、\n間に合う？", 330, "yellow"), ("問い2\n2倍以上払って急ぎ便に\nしたら、得をする？", 960, "mint"),
        ("問い3\n返事が来るまで、\n何日待つ？", 1590, "pink")]


def sc_c0_tags(ctx, t):
    t_all = Sk("c0_next") - 0.6
    for k, (s_, x_, col) in enumerate(TAGS):
        a = fade(t, t_all + 0.3 * k, 0.4)
        on = fade(t, Sk("c0_next", 0.55), 0.3) if k == 0 else 0.0
        mini_sticky(ctx, s_, x_, 470, 46, col, a=a * (0.6 + 0.4 * on), tilt=-0.015 + 0.015 * k)
        koma(ctx, x_, 300, 46, (FASTC, "#e8b04a", BLUE)[k], a=a, tilt=(-0.15, 0.1, -0.08)[k])
        if on > 0.003:
            pen_circle(ctx, x_, 470, 240, 125, RED, seed=3, width=6, progress=clamp01((t - Sk("c0_next", 0.55)) / 0.7), alpha=on * a)
    person(ctx, 330, 905, 330, t, "stand", 1, a=fade(t, t_all + 0.9, 0.4))
    hikyaku(ctx, 1590, 905, 330, t, run=False, face=-1, a=fade(t, t_all + 0.9, 0.4))
    text(ctx, "3つ、確かめます", 960, 760, 64, INK, alpha=fade(t, t_all + 0.9, 0.4))


# ============================================================
# 1 約束の日に、間に合う？
# ============================================================
def sc_c1_title(ctx, t):
    t_ti = S("ch1") + 2.2
    title_hand(ctx, "問い1", RX, 150, 110, 6, fade(t, t_ti, 0.4))
    stk(ctx, t, "c1_intro", "飛脚は、約束の日に、\n手紙を届けてくれる？", RX, 350, "yellow", size=52, off=1.8, tilt=-0.012)
    person(ctx, 280, 905, H0, t, "stand", 1)
    hikyaku(ctx, 700, 905, H0, t, run=False, face=-1)
    stk(ctx, t, "c1_yoso", "予想\nたいてい着く", RX, 620, "pink", size=56, off=0.9, tilt=0.01)


def sc_c1_10k(ctx, t):
    cap_a = fade(t, bd("c1_10k") + 0.3, 0.4)
    text(ctx, "1マス＝1通", LCX, GRID1.y0 - 46, 56, INK, alpha=cap_a)
    nf = int(N * clamp01((t - (Sk("c1_10k", 0.05) + 0.1)) / (Dk("c1_10k") - 0.7)) ** 1.4)
    GRID1.draw(ctx, nf, 0, a=fade(t, bd("c1_10k") + 0.3, 0.4))
    stk(ctx, t, "c1_10k", "1万通", RCX, 330, "yellow", size=120, off=0.5, tilt=-0.012, align="center")
    for k in range(5):
        koma(ctx, RCX - 280 + k * 140, 560 + 18 * math.sin(t * 2.0 + k), 46, (FASTC, "#e8b04a", BLUE, FASTC, "#e8b04a")[k], a=fade(t, Sk("c1_10k", 0.2) + 0.15 * k, 0.3), tilt=0.1 * (k - 2))
    hikyaku(ctx, RCX, 905, 330, t, run=True, face=1, a=fade(t, Sk("c1_10k", 0.3), 0.4))


GRID1 = Grid10k(np.zeros(N, int), ["#e8b04a"], base="#e8b04a", cx=LCX, y0=190.0, cell=5.0, seed=12)


def ruler(ctx, x0, x1, y, dmax, a=1.0, label_step=1, tick=18):
    """日数の目もり（0〜dmax日）。目もりの数字は 44px"""
    sx = (x1 - x0) / dmax
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(5)
    ctx.move_to(x0, y)
    ctx.line_to(x1, y)
    ctx.stroke()
    for d in range(0, dmax + 1):
        x = x0 + d * sx
        ctx.set_line_width(4)
        ctx.move_to(x, y - tick)
        ctx.line_to(x, y + tick)
        ctx.stroke()
        if d % label_step == 0:
            text(ctx, str(d), x, y + 52, 44, INK, alpha=a)
    return sx


def sc_c1_def(ctx, t):
    x0, x1, y, dm = 270, 1650, 690, 10
    t0 = bd("c1_def")
    a = fade(t, t0 + 0.2, 0.4)
    text(ctx, "遅れ ＝ 着いた日数 − 約束の日数", 960, 200, 64, INK, alpha=fade(t, Sk("c1_def", 0.1), 0.4))
    sx = ruler(ctx, x0, x1, y, dm, a=a)
    text(ctx, "日", x1 + 54, y, 44, INK, alpha=a)
    xp = x0 + 6 * sx
    line2(ctx, (xp, y - 150), (xp, y + 20), RED, 7, a=a)
    mini_sticky(ctx, "約束の日", xp - 130, y - 235, 52, "pink", a=a, tilt=0.01)
    # 例: 8日で着いた手紙（遅れ2日）
    u = ease_in_out(clamp01((t - Sk("c1_def", 0.3)) / 2.0))
    koma(ctx, x0 + 8 * sx * u, y - 70, 52, FASTC, a=fade(t, Sk("c1_def", 0.25), 0.3))
    if u >= 1:
        ba = fade(t, Sk("c1_def", 0.3) + 2.0, 0.3)
        line2(ctx, (xp, y - 120), (x0 + 8 * sx, y - 120), RED, 6, a=ba)
        text(ctx, "遅れ 2日", (xp + x0 + 8 * sx) / 2, y - 154, 50, RED, alpha=ba)
    text(ctx, "（例）", 1500, 330, 44, PENCIL_T, alpha=a)
    # 約束より早い手紙は、ありません
    na = fade(t, Sk("c1_noearly", 0.1), 0.4)
    if na > 0.003:
        koma(ctx, x0 + 3.6 * sx, y - 70, 52, "#8a8fa6", a=na, tilt=-0.1)
        cross_mark(ctx, x0 + 3.6 * sx, y - 70, 52, a=na, p=clamp01((t - Sk("c1_noearly", 0.35)) / 0.7))
        mini_sticky(ctx, "約束より早い手紙は 0通", 640, 340, 48, "mint", a=na, tilt=-0.01)


def sc_c1_kuji(ctx, t):
    ka = fade(t, bd("c1_kuji"), 0.3)
    kuji_box(ctx, 960, 470, 440, slip=ease_in_out(clamp01((t - (Sk("c1_kuji") + 0.6)) / 1.4)), a=ka)
    stk(ctx, t, "c1_kuji", "出す日は、くじ", 430, 330, "yellow", size=64, off=0.2, tilt=-0.012, align="center")
    stk(ctx, t, "c1_kuji", "1年のどの日も、\n同じ確率", 1490, 360, "mint", size=56, off=2.0, tilt=0.012, align="center")
    for k in range(12):                                         # 1年の12か月
        xx = 215 + k * 135
        a = fade(t, Sk("c1_kuji", 0.5) + 0.07 * k, 0.3)
        ctx.set_source_rgba(*hexrgb("#cfe0f7", a))
        rrect(ctx, xx - 52, 780, 108, 100, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(2.5)
        rrect(ctx, xx - 52, 780, 108, 100, 12)
        ctx.stroke()
        text(ctx, f"{k + 1}月", xx, 830, 44, INK, alpha=a)


KIND_COL = {"五日限": "#d9553d", "六日限": "#e8b04a", "八日限": "#3a73c8"}


def sc_c1_kinds(ctx, t):
    a = fade(t, bd("c1_kinds"), 0.3)
    text(ctx, "便", 250, 190, 52, PENCIL_T, alpha=a)
    text(ctx, "約束の日数", 760, 190, 52, PENCIL_T, alpha=a)
    text(ctx, "料金（円には直さない）", 1490, 190, 52, PENCIL_T, alpha=a)
    for k, nm in enumerate(KNAME):
        y = 330 + k * 150
        c = KIND_COL[nm]
        text(ctx, nm, 250, y, 64, INK, alpha=a)
        wlen = 70 * KINDS[k]
        ctx.set_source_rgba(*hexrgb(c, 0.9 * a))
        rrect(ctx, 520, y - 34, wlen * ease_out(clamp01((t - bd("c1_kinds") - 0.4 - 0.15 * k) / 0.7)), 68, 8)
        ctx.fill()
        text(ctx, f"{KINDS[k]}日", 520 + wlen + 70, y, 52, INK, alpha=a * fade(t, bd("c1_kinds") + 1.2 + 0.15 * k, 0.3))
        pl = (480, 330, 180)[k]
        ctx.set_source_rgba(*hexrgb("#d7a56c", 0.9 * a))
        rrect(ctx, 1250, y - 34, pl * ease_out(clamp01((t - Sk("c1_kinds", 0.35) - 0.2 * k) / 0.7)), 68, 8)
        ctx.fill()
    pa = fade(t, Sk("c1_kinds", 0.4), 0.4)
    arrow2(ctx, (1240, 830), (1740, 830), RED, w=6, a=pa, head=22)
    mini_sticky(ctx, "短い約束ほど、料金が高い", 1490, 745, 52, "yellow", a=pa, tilt=-0.01)
    # 同じ数ずつ分ける
    sa = fade(t, Sk("c1_same", 0.0) - 0.3, 0.4)
    if sa > 0.003:
        mini_sticky(ctx, "1万通を、3つの便に\n同じ数ずつ", 470, 800, 52, "mint", a=sa, tilt=0.01)
        for k in range(3):
            ctx.set_source_rgba(*hexrgb(KIND_COL[KNAME[k]], 0.9 * sa))
            rrect(ctx, 780 + k * 110, 745, 90, 90, 10)
            ctx.fill()
            koma(ctx, 825 + k * 110, 790, 34, "#fffaf0", a=sa, tilt=0.0)


def sc_c1_kishu(ctx, t):
    a = fade(t, bd("c1_late1"), 0.3)
    # 1日遅れの例（左）
    x0, x1, y, dm = 160, 880, 640, 8
    sx = ruler(ctx, x0, x1, y, dm, a=a)
    xp = x0 + 5 * sx
    line2(ctx, (xp, y - 130), (xp, y + 20), RED, 6, a=a)
    text(ctx, "約束の日", xp - 30, y - 168, 46, RED, alpha=a)
    u = ease_in_out(clamp01((t - Sk("c1_late1", 0.2)) / 1.6))
    koma(ctx, x0 + 6 * sx * u, y - 62, 46, FASTC, a=fade(t, Sk("c1_late1", 0.1), 0.3))
    la = fade(t, Sk("c1_late1", 0.2) + 1.6, 0.3)
    if la > 0.003:
        mini_sticky(ctx, "1日遅れ", 520, 330, 56, "pink", fg=RED, a=la, tilt=-0.01)
    # 紀州藩の記録（右）
    stk(ctx, t, "c1_kishu", "紀州藩の送金33件\n（向きは松坂→江戸で逆。\n遅れ方の形だけを借りた）", 940, 200, "yellow", size=44, off=0.2, tilt=-0.008)
    ta = fade(t, Sk("c1_k27", 0.0) - 0.4, 0.4)
    text(ctx, "33件中", 1110, 450, 50, INK, align="left", alpha=fade(t, Sk("c1_k27", 0.0) - 0.4, 0.4))
    rows = (("ちょうど", N_EXACT, BLUE), ("1日遅れ", N_PLUS1, FASTC), ("早く着いた", 0, "#5aa469"))
    for k, (nm, v, c) in enumerate(rows):
        yy = 520 + k * 110
        text(ctx, nm, 1080, yy, 50, INK, align="right", alpha=ta)
        bu = ease_out(clamp01((t - Sk("c1_k27", 0.1 + 0.2 * k)) / 0.7))
        ctx.set_source_rgba(*hexrgb(c, 0.92 * ta))
        if v > 0:
            rrect(ctx, 1110, yy - 36, 22 * v * bu, 72, 8)
            ctx.fill()
        text(ctx, f"{v}件", 1110 + 22 * v + 70 if v > 0 else 1180, yy, 52, INK, alpha=ta * fade(t, Sk("c1_k27", 0.2 + 0.2 * k), 0.3))
    stk(ctx, t, "c1_k27", "100件に27件が、1日遅れ", 1380, 880, "pink", fg=RED, size=48, off=0.4, tilt=-0.01, align="center")


def sc_c1_src(ctx, t):
    t0 = bd("c1_src")
    river_close(ctx, 110, 200, 880, 640, level=0.9, a=fade(t, t0 + 0.2, 0.4), t=t, sign=fade(t, Sk("c1_src", 0.3), 0.4))
    stk(ctx, t, "c1_src", "大きな遅れのもと\n＝川止め", 495, 780, "yellow", size=52, off=0.3, tilt=-0.01, align="center")
    # 年に十数回
    ya = fade(t, Sk("c1_12", 0.0) - 0.4, 0.4)
    text(ctx, "1年", 980, 220, 48, INK, align="left", alpha=ya)
    ctx.set_source_rgba(*hexrgb("#e6e8ef", 0.95 * ya))
    rrect(ctx, 1060, 190, 740, 60, 10)
    ctx.fill()
    for k in range(13):
        xx = 1085 + k * 54 + (9 if k % 3 == 1 else 0)
        ctx.set_source_rgba(*hexrgb(WATER_D, 0.92 * ya * fade(t, Sk("c1_12", 0.25) + 0.12 * k, 0.2)))
        rrect(ctx, xx, 190, 22, 60, 4)
        ctx.fill()
    stk(ctx, t, "c1_12", "年に十数回", 1430, 330, "mint", size=56, off=0.3, tilt=0.01, align="center")
    # あわせて50日ほど／いちばん長い28日
    ba = fade(t, Sk("c1_50", 0.0) - 0.4, 0.4)
    text(ctx, "あわせて", 1020, 500, 50, INK, align="left", alpha=ba)
    ctx.set_source_rgba(*hexrgb(WATER_D, 0.92 * ba))
    rrect(ctx, 1260, 466, 12.0 * 50 * ease_out(clamp01((t - Sk("c1_50", 0.2)) / 0.8)), 68, 8)
    ctx.fill()
    stk(ctx, t, "c1_50", "50日ほど", 1500, 580, "yellow", size=56, off=0.3, tilt=-0.01, align="center")
    ca = fade(t, Sk("c1_28d", 0.0) - 0.4, 0.4)
    text(ctx, "いちばん長い", 1020, 700, 50, INK, align="left", alpha=ca)
    ctx.set_source_rgba(*hexrgb("#1e5f9f", 0.92 * ca))
    rrect(ctx, 1320, 666, 12.0 * 28 * ease_out(clamp01((t - Sk("c1_28d", 0.2)) / 0.8)), 68, 8)
    ctx.fill()
    stk(ctx, t, "c1_28d", "28日間", 1660, 770, "yellow", size=56, off=0.3, tilt=-0.01, align="center")
    sa = stk(ctx, t, "c1_28d", "川止めの起きやすさと長さは仮定", 1370, 880, "pink", size=44, off=1.5, tilt=0.008, align="center")
    pa = clamp01((t - Sk("c1_28d", 0.0) - 2.4) / 0.8)
    if pa > 0 and sa[0] > 0:
        pen_circle(ctx, 1370, 880, sa[0] / 2 + 14, 50, RED, seed=9, width=6, progress=pa)


BAR_STEP = 0.3                                             # 棒は1本ずつ、0.3秒おき（目で追える速さ）


def sc_c1_rain(ctx, t):
    cx0, cx1, cy0, cy1, ymax = 190, 1760, 330, 790, 30.0
    pitch = (cx1 - cx0) / 12
    fa = fade(t, bd("c1_rain"), 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, cx0 - 30, cy0 - 30, cx1 - cx0 + 60, cy1 - cy0 + 100, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(cx0 - 20, cy1)
    ctx.line_to(cx1 + 20, cy1)
    ctx.stroke()
    text(ctx, "月", cx1 + 60, cy1 + 36, 44, INK, alpha=fa)
    for m in range(12):
        text(ctx, str(m + 1), cx0 + (m + 0.5) * pitch, cy1 + 36, 46, INK, alpha=fa)
    stk(ctx, t, "c1_rain", "川止めは年に50日ほど（仮定）", 1180, 190, "yellow", size=46, off=0.3, tilt=-0.008, align="left")
    ta = fade(t, Sk("c1_diary", 0.0) - 0.3, 0.4)
    text(ctx, "雨の日の割合（江戸の藩屋敷の日記）", 110, 190, 46, INK, align="left", alpha=ta)
    for m in range(12):
        bu = ease_out(clamp01((t - (Sk("c1_diary", 0.35) + BAR_STEP * m)) / 0.5))
        hh = (cy1 - cy0) * RAIN[m] / ymax * bu
        col = {0: BLUE, 5: FASTC, 8: FASTC}.get(m, "#8bb0e0")
        ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
        rrect(ctx, cx0 + (m + 0.5) * pitch - 36, cy1 - hh, 72, hh, 6)
        ctx.fill()
    ga = fade(t, Sk("c1_x3", 0.2), 0.4)
    if ga > 0.003:
        mini_sticky(ctx, "6月と9月は、\n1月の3倍ほど", 1160, 292, 46, "pink", fg=RED, a=ga, tilt=0.01)
        line2(ctx, (cx0 + 0.5 * pitch, cy1 - (cy1 - cy0) * RAIN[0] / ymax - 16), (cx0 + 5.5 * pitch, cy1 - (cy1 - cy0) * RAIN[5] / ymax - 16), RED, 4, a=ga * 0.8, dash=[12, 10])


def sc_c1_half(ctx, t):
    MAP1.draw(ctx, level=0.0, sign=0.0)
    u = ease_in_out(clamp01((t - Sk("c1_half", 0.15)) / (Dk("c1_half") - 2.2)))
    MAP1.piece(ctx, u * MAP1.fb, 0, FASTC, s=38)
    hikyaku(ctx, 330, 925, 380, t, run=u < 1.0, face=1)
    stk(ctx, t, "c1_half", "道のりの半分で、\n大井川に着く", 920, 600, "yellow", size=56, off=0.6, tilt=-0.01)
    stk(ctx, t, "c1_half", "着いた日が川止めなら、\nそのぶん待つ", 1240, 800, "mint", size=52, off=3.4, tilt=0.01)


MAP1 = RouteMap(110, 150, 1810, 450)


HIST_BINS = [(5, 5), (6, 6), (7, 7), (8, 9), (10, 14), (15, 24), (25, 36)]      # 着いた日数のまとめ方（7本。1本ずつ0.4秒おきに積む）
HIST_BIN_STEP = 0.4


def sc_c1_hist(ctx, t):
    x0, x1, y0, y1 = 220, 1770, 250, 790
    fa = fade(t, bd("c1_moved"), 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, x0 - 40, y0 - 30, x1 - x0 + 80, y1 - y0 + 130, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(x0 - 20, y1)
    ctx.line_to(x1 + 20, y1)
    ctx.stroke()
    pitch = (x1 - x0) / len(HIST_BINS)
    counts = [int(T_COUNT[a_:b_ + 1].sum()) for a_, b_ in HIST_BINS]
    mx = max(counts)
    text(ctx, "着いた日数（日）", 960, y1 + 90, 44, INK, alpha=fa)
    text(ctx, "着いた日ごとの通数", 480, 160, 52, INK, alpha=fa)
    cols = [BLUE, "#6a97d8", "#9ab6e2", "#d9c27a", "#e8b04a", "#e07a52", "#c0392b"]
    for k, (a_, b_) in enumerate(HIST_BINS):
        cx = x0 + (k + 0.5) * pitch
        text(ctx, str(a_) if a_ == b_ else f"{a_}〜{b_}", cx, y1 + 40, 44, INK, alpha=fa)
        bu = ease_out(clamp01((t - (Sk("c1_moved", 0.0) + HIST_BIN_STEP * k)) / 0.5))
        hh = (y1 - y0) * counts[k] / mx * bu
        if counts[k] > 0:
            hh = max(hh, 6.0 * bu)
        ctx.set_source_rgba(*hexrgb(cols[k], 0.95 * fa))
        rrect(ctx, cx - 70, y1 - hh, 140, hh, 6)
        ctx.fill()
    stk(ctx, t, "c1_moved", "1万通を動かした", 1450, 220, "yellow", size=56, off=0.5, tilt=-0.01, align="center")


def sc_c1_dist(ctx, t):
    x0, x1, y0, y1 = 190, 1770, 250, 790
    fa = fade(t, bd("c1_p64"), 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, x0 - 40, y0 - 30, x1 - x0 + 80, y1 - y0 + 150, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(x0 - 20, y1)
    ctx.line_to(x1 + 20, y1)
    ctx.stroke()
    text(ctx, "遅れの分布（1万通）", 560, 170, 56, INK, alpha=fa)
    cats = [("約束どおり", MQ1["d0"], BLUE, "c1_p64", 380), ("1日遅れ", MQ1["d1"], "#8bb0e0", "c1_p26", 760), ("2〜5日遅れ", MQ1["d2_5"], "#e8b04a", "c1_p7", 1140),
            ("6日以上遅れ", MQ1["d6"], FASTC, "c1_p3", 1500)]
    for nm, v, col, key, cx in cats:
        text(ctx, nm, cx, y1 + 50, 48, INK, alpha=fa)
        bu = ease_out(clamp01((t - Sk(key, 0.25)) / 0.8))
        hh = (y1 - y0) * v / 70.0 * bu
        ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
        rrect(ctx, cx - 85, y1 - hh, 170, hh, 8)
        ctx.fill()
        stk(ctx, t, key, pct_txt(v) + ("ほど" if key == "c1_p3" else ""), cx, y1 - hh - 70, "yellow", size=46, off=0.5, tilt=-0.01, align="center")
    # うち10日以上
    bu = ease_out(clamp01((t - Sk("c1_p10", 0.3)) / 0.8))
    hh = (y1 - y0) * MQ1["d10"] / 70.0 * bu
    ctx.set_source_rgba(*hexrgb("#8f2d1f", 0.95 * fa))
    rrect(ctx, 1650, y1 - hh, 100, hh, 6)
    ctx.fill()
    text(ctx, "うち10日以上", 1620, y1 + 100 - 4, 44, "#8f2d1f", alpha=fa * fade(t, Sk("c1_p10", 0.2), 0.3))
    stk(ctx, t, "c1_p10", "100通に1〜2通", 1590, 470, "pink", fg=RED, size=46, off=0.9, tilt=0.01, align="center")


def _band_img(w, h):
    Ts = np.sort(R["T"])
    idx = np.minimum(((np.arange(w) + 0.5) / w * N).astype(int), N - 1)
    pal = {5: "#3a73c8", 6: "#6a97d8", 7: "#9ab6e2", 8: "#d9c27a", 9: "#e8b04a", 10: "#e98f52"}

    def col(d):
        if d in pal:
            return pal[d]
        return "#e07a52" if d <= 14 else "#c0392b"
    arr = np.zeros((h, w, 4), np.uint8)
    for x in range(w):
        r, g, b = hexrgb(col(int(Ts[idx[x]])))[:3]
        arr[:, x] = (int(b * 255), int(g * 255), int(r * 255), 255)
    return arr, Ts


BAND_W, BAND_H = 1500, 100
BAND_ARR, T_SORTED = _band_img(BAND_W, BAND_H)
BAND_X0, BAND_Y0 = 210, 400


def sc_c1_median(ctx, t):
    fa = fade(t, bd("c1_sort"), 0.3)
    buf = np.ascontiguousarray(BAND_ARR)
    s_ = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, BAND_W, BAND_H, BAND_W * 4)
    ctx.save()
    ctx.set_source_surface(s_, BAND_X0, BAND_Y0)
    ctx.paint_with_alpha(fa)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * fa))
    ctx.set_line_width(3)
    ctx.rectangle(BAND_X0 - 3, BAND_Y0 - 3, BAND_W + 6, BAND_H + 6)
    ctx.stroke()
    text(ctx, "1万通を、着くまでの日数が短い順に並べた", 960, 300, 56, INK, alpha=fa)
    text(ctx, "短い", BAND_X0 + 40, BAND_Y0 + BAND_H + 50, 46, INK, alpha=fa)
    text(ctx, "長い", BAND_X0 + BAND_W - 40, BAND_Y0 + BAND_H + 50, 46, INK, alpha=fa)
    # 日数ごとの区間の名札
    for d in (5, 6, 7, 8, 9, 10):
        xs = np.nonzero(T_SORTED == d)[0]
        if len(xs):
            xa, xb = BAND_X0 + xs[0] / N * BAND_W, BAND_X0 + (xs[-1] + 1) / N * BAND_W
            if xb - xa >= 90:
                text(ctx, f"{d}日", (xa + xb) / 2, BAND_Y0 + BAND_H / 2, 46, "#1a2336", alpha=fa)
    # ちょうど真ん中
    pa = fade(t, Sk("c1_sort", 0.55), 0.4)
    xm = BAND_X0 + BAND_W / 2
    if pa > 0.003:
        arrow2(ctx, (xm, BAND_Y0 + BAND_H + 150), (xm, BAND_Y0 + BAND_H + 12), RED, w=7, a=pa, head=26)
        mini_sticky(ctx, "ちょうど真ん中", xm, BAND_Y0 + BAND_H + 200, 52, "yellow", a=pa, tilt=-0.01)
    stk(ctx, t, "c1_medname", "中央値", 1480, 610, "pink", fg=RED, size=84, off=0.1, tilt=-0.012, align="center", until=Sk("c1_tmed") - 0.1)
    stk(ctx, t, "c1_tmed", "着くまでの日数の\n中央値 6日", 430, 800, "yellow", size=56, off=0.5, tilt=-0.012, align="center")
    stk(ctx, t, "c1_dmed", "約束との差の\n中央値 0日＝約束どおり", 1500, 800, "mint", size=52, off=0.5, tilt=0.01, align="center")


def sc_c1_each(ctx, t):
    t0 = bd("c1_each") + 0.3
    for k, (s_, x_, col) in enumerate((("中央値の手紙", 330, "yellow"), ("いちばん早く着いた手紙", 960, "mint"), ("いちばん遅れた手紙", 1590, "pink"))):
        a = fade(t, t0 + 0.9 * k + 1.4, 0.4)
        mini_sticky(ctx, s_, x_, 480, 50, col, a=a, tilt=-0.015 + 0.015 * k)
        koma(ctx, x_, 330, 58, (BLUE, "#5aa469", FASTC)[k], a=a, tilt=(-0.1, 0.05, 0.12)[k])
    person(ctx, 250, 905, 330, t, "stand", 1, a=fade(t, t0 + 1.0, 0.4))
    text(ctx, "何が起きたか、1通ずつ見ていく", 960, 640, 60, INK, alpha=fade(t, t0 + 0.4, 0.4))


# ============================================================
# 1通ずつの場面（問い1・問い3）: 上＝地図と駒、左下＝あなた、右下＝暦（×が増える）。約束の日は赤丸、川止めで待った日は水色
# ============================================================
MAPC = RouteMap(110, 170, 1810, 450)
CAL_X, CAL_Y, CAL_W, CAL_H = 560, 590, 1250, 335
TINT_GO, TINT_WRITE, TINT_BACK = "#cfe0f7", "#f6e3a1", "#cfe9d0"


def kf_pos(pts, day):
    return kv(pts, day)


def river_state(day, off, wait, t0=0.0):
    """川の水位（待っている間 1）。day は出してからの通し日数"""
    if wait <= 0:
        return 0.0
    a = ease_in_out((day - (t0 + off) + 0.4) / 0.8)
    b = ease_in_out((day - (t0 + off + wait) + 0.1) / 0.6)
    return clamp01(a) * (1.0 - clamp01(b))


def card1(ctx, t, sp):
    """問い1の1通。sp: date(札)・key_date・date_frac・dayf・D・T・off・wait・n・cols・col・delay_key・delay_frac・delay_txt"""
    day = sp["dayf"](t)
    pts = kf_go(sp["off"], sp["wait"], sp["T"], 0.0, MAPC.fb, MAPC.fa)
    lv = river_state(day, sp["off"], sp["wait"])
    MAPC.draw(ctx, level=0.9 * lv, sign=lv if sp["wait"] >= 3 else 0.0)
    MAPC.piece(ctx, kf_pos(pts, day), 0, sp.get("col", FASTC), s=40)
    stk(ctx, t, sp["key_date"], sp["date"], 110, 108, "yellow", size=48, off=0.1, frac=sp["date_frac"], tilt=-0.008, align="left")
    person(ctx, 300, 925, 380, t, "stand", 1, a=fade(t, sp["t_in"], 0.4))
    wait_rng = (sp["off"], sp["off"] + sp["wait"]) if sp["wait"] > 0 else None
    la = fade(t, sp["t_in"] + 0.3, 0.4)
    text(ctx, "赤丸＝約束の日" + ("　水色＝川止めの待ち" if wait_rng else ""), 560, 515, 44, INK, align="left", alpha=la)
    calendar(ctx, CAL_X, CAL_Y, CAL_W, CAL_H, sp["n"], marks=day, promise=sp["D"], a=la, cols=sp["cols"], wait=wait_rng)
    if day >= sp["T"] - 1e-6:
        mini_sticky(ctx, f"{sp['T']}日目に着く", 1620, 515, 56, "yellow", a=la * fade(t, sp["t_arrive"], 0.3), tilt=-0.01)
    stk(ctx, t, sp["delay_key"], sp["delay_txt"], 1650, 108, "pink", fg=RED, size=52, off=0.0, frac=sp["delay_frac"], tilt=0.01, align="center")


def _t1(key, off=0.0):
    return Sk(key, 0.0) + off


# 1通目: 中央値（4月23日出し・五日限・6日で着く・1日の遅れ）
_C1M, _C1B, _C1W = CARDS1["median"], CARDS1["best"], CARDS1["worst"]
SP_M = dict(date=f"{_C1M['date']}出し・{_C1M['kind']}", key_date="c1_m1", date_frac=0.55, D=_C1M["D"], T=_C1M["T"], off=OFFS[_C1M["kind"]], wait=_C1M["river_wait"],
            n=14, cols=7, delay_key="c1_m2", delay_frac=0.62, delay_txt=f"遅れ {_C1M['delay']}日", t_in=bd("c1_m1") + 0.3,
            dayf=dmap([(Sk("c1_m2", 0.0), 0.0), (Sk("c1_m2", 0.0) + 2.4, float(_C1M["T"]))]))
SP_B = dict(date=f"{_C1B['date']}出し・{_C1B['kind']}", key_date="c1_b1", date_frac=0.45, D=_C1B["D"], T=_C1B["T"], off=OFFS[_C1B["kind"]], wait=_C1B["river_wait"],
            n=14, cols=7, delay_key="c1_b2", delay_frac=0.66, delay_txt=f"遅れ {_C1B['delay']}日", t_in=bd("c1_b1") + 0.3,
            dayf=dmap([(Sk("c1_b2", 0.0), 0.0), (Sk("c1_b2", 0.62), float(_C1B["T"]))]))
SP_W = dict(date=f"{_C1W['date']}出し・{_C1W['kind']}", key_date="c1_w1", date_frac=0.5, D=_C1W["D"], T=_C1W["T"], off=OFFS[_C1W["kind"]], wait=_C1W["river_wait"],
            n=40, cols=10, delay_key="c1_w4", delay_frac=0.72, delay_txt=f"遅れ {_C1W['delay']}日", t_in=bd("c1_w1") + 0.3,
            dayf=dmap([(Sk("c1_w2", 0.05), 0.0), (Sk("c1_w2", 0.05) + 2.4, float(OFFS[_C1W["kind"]])), (Ek("c1_w3") - 0.1, float(OFFS[_C1W["kind"]] + _C1W["river_wait"])),
                       (Sk("c1_w4", 0.0) + 1.9, float(_C1W["T"]))]))


def sc_c1_card_m(ctx, t):
    card1(ctx, t, SP_M)


def sc_c1_card_b(ctx, t):
    card1(ctx, t, SP_B)


def sc_c1_card_w(ctx, t):
    card1(ctx, t, SP_W)
    # 川止めの札・「28日」は、声に合わせて（暦の水色が28日ぶん）
    stk(ctx, t, "c1_w3", "川止め 28日", 1000, 108, "pink", fg=RED, size=52, off=0.2, tilt=0.01, align="center")


def sc_c1_tail(ctx, t):
    fa = fade(t, bd("c1_most"), 0.3)
    bx0, bw = 560, 1200
    y1, y2 = 440, 650
    segs = [(MQ1["d0"], BLUE), (MQ1["d1"], "#8bb0e0"), (MQ1["d2_5"], "#e8b04a"), (MQ1["d6"], FASTC)]
    tot = sum(v for v, _c in segs)
    text(ctx, "手紙の数", bx0 - 30, y1, 50, INK, align="right", alpha=fa)
    x = bx0
    for v, c in segs:
        w = bw * v / tot
        ctx.set_source_rgba(*hexrgb(c, 0.95 * fa))
        ctx.rectangle(x, y1 - 38, w, 76)
        ctx.fill()
        x += w
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * fa))
    ctx.set_line_width(3)
    ctx.rectangle(bx0, y1 - 38, bw, 76)
    ctx.stroke()
    mini_sticky(ctx, "約束どおりか、1日遅れ", 640, 250, 52, "yellow", a=fade(t, Sk("c1_most", 0.3), 0.4), tilt=-0.01)
    xa, xb = bx0, bx0 + bw * (MQ1["d0"] + MQ1["d1"]) / tot
    pa = fade(t, Sk("c1_most", 0.5), 0.4)
    line2(ctx, (xa, y1 - 56), (xb, y1 - 56), "#1f4f9a", 6, a=pa)
    # 遅れの平均
    stk(ctx, t, "c1_avg", "遅れの平均は\n1日にもならない（0.8日）", 800, 830, "mint", size=52, off=0.4, tilt=0.008, align="center")
    # 6日以上の手紙: 100通に3通ほど（細い赤）
    xr = bx0 + bw * (1 - MQ1["d6"] / tot)
    ra = fade(t, Sk("c1_share", -0.55), 0.4)
    if ra > 0.003:
        stk(ctx, t, "c1_share", "6日以上遅れた手紙\n100通に3通ほど", 1530, 548, "pink", fg=RED, size=44, off=-0.6, tilt=0.008, align="center")
        line2(ctx, (xr + 20, y1 + 40), (1530 - 40, 500), RED, 4, a=ra * 0.8)
    # 遅れた日数の合計
    ba = fade(t, Sk("c1_share", -0.75), 0.4)
    text(ctx, "遅れた日数の合計", bx0 - 30, y2, 50, INK, align="right", alpha=ba)
    sh = MQ1["share_days_from_d6"] / 100.0
    ctx.set_source_rgba(*hexrgb("#9aa0b6", 0.95 * ba))
    ctx.rectangle(bx0, y2 - 38, bw * (1 - sh), 76)
    ctx.fill()
    ru = ease_out(clamp01((t - Sk("c1_share", -0.1)) / 0.9))
    ctx.set_source_rgba(*hexrgb(FASTC, 0.95 * ba))
    ctx.rectangle(bx0 + bw * (1 - sh * ru), y2 - 38, bw * sh * ru, 76)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * ba))
    ctx.rectangle(bx0, y2 - 38, bw, 76)
    ctx.stroke()
    stk(ctx, t, "c1_share", "4割ほど", bx0 + bw * (1 - sh / 2), 760, "pink", fg=RED, size=64, off=0.2, tilt=-0.01, align="center")
    stk(ctx, t, "c1_only", "大きく遅れるのは、川止めに\n当たった手紙だけ", 1380, 250, "yellow", size=48, off=0.5, tilt=0.01, align="center")


def month_bars(ctx, t, vals, ymax, t_grow, fa, hi=(), title=None, hi_col=FASTC, ylab_fmt=None):
    cx0, cx1, cy0, cy1 = 190, 1760, 330, 790
    pitch = (cx1 - cx0) / 12
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, cx0 - 30, cy0 - 30, cx1 - cx0 + 60, cy1 - cy0 + 100, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(cx0 - 20, cy1)
    ctx.line_to(cx1 + 20, cy1)
    ctx.stroke()
    text(ctx, "月", cx1 + 60, cy1 + 36, 44, INK, alpha=fa)
    for m in range(12):
        text(ctx, str(m + 1), cx0 + (m + 0.5) * pitch, cy1 + 36, 46, INK, alpha=fa)
    if title:
        text(ctx, title, 110, 190, 46, INK, align="left", alpha=fa)
    for m in range(12):
        bu = ease_out(clamp01((t - (t_grow + BAR_STEP * m)) / 0.5))
        hh = (cy1 - cy0) * vals[m] / ymax * bu
        col = hi_col if m in hi else "#8bb0e0"
        ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
        rrect(ctx, cx0 + (m + 0.5) * pitch - 36, cy1 - hh, 72, hh, 6)
        ctx.fill()
    return cx0, pitch, cy0, cy1


def sc_c1_month(ctx, t):
    fa = fade(t, bd("c1_month"), 0.3)
    cx0, pitch, cy0, cy1 = month_bars(ctx, t, D6_MONTH, 6.0, Sk("c1_month", 0.3), fa, hi=(0,) + tuple(m_ - 1 for m_ in RAINY), title="6日以上遅れた手紙の割合（出した月ごと）", hi_col="#d9553d")
    hh = (cy1 - cy0) * D6_MONTH[0] / 6.0
    stk(ctx, t, "c1_month", "1月 100通に1通ほど", cx0 + 0.5 * pitch + 60, cy1 - hh - 200, "yellow", size=46, off=0.7, frac=0.45, tilt=-0.01, align="center")
    stk(ctx, t, "c1_apr", "雨の多い月（4・6・7・9月）\n100通に4通から5通ほど", 880, 330, "yellow", size=46, off=0.5, frac=0.0, tilt=-0.01, align="center")
    sa = stk(ctx, t, "c1_assume", "月の並びは、仮定した\n雨の重みの反映", 1520, 290, "pink", size=46, off=0.3, tilt=0.008, align="center")
    pa = clamp01((t - Sk("c1_assume", 0.0) - 1.4) / 0.8)
    if pa > 0 and sa[0] > 0:
        pen_circle(ctx, 1520, 290, sa[0] / 2 + 12, 70, RED, seed=11, width=6, progress=pa)


SCEN_CARD = f"川止めが少ない仮定なら100通に{ihalf(SCEN_ON['少なめ'])}通、\n多い仮定なら{ihalf(SCEN_ON['多め'])}通"
T_SCEN0 = Ek("c1_assume")                       # 川止めの幅の札（声なし）。月の並びの仮定の文を言い終えてから、次の「答えです」の 1.05秒前まで
T_SCEN1 = bd("c1_ans")


def sc_c1_scen(ctx, t):
    """川止めが少ない仮定・基準・多い仮定の3本。幅は札で1回だけ出す（声では言わない）。棒は1本ずつ 0.5秒おき"""
    y1, y0 = 790, 440
    fa = fade(t, T_SCEN0, 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, 130, 190, 1660, 700, 14)
    ctx.fill()
    mini_sticky(ctx, SCEN_CARD, 960, 285, 48, "yellow", a=fade(t, T_SCEN0 + 0.3, 0.4), tilt=-0.008)
    items = [("川止めが少ない仮定", SCEN_ON["少なめ"], "#8bb0e0"), ("基準", SCEN_ON["基準"], BLUE), ("多い仮定", SCEN_ON["多め"], FASTC)]
    for k, (nm, v, c) in enumerate(items):
        cx = 480 + k * 480
        text(ctx, nm, cx, y1 + 52, 46, INK, alpha=fa)
        bu = ease_out(clamp01((t - (T_SCEN0 + 0.6 + 0.5 * k)) / 0.6))
        hh = (y1 - y0) * v / 70.0 * bu
        ctx.set_source_rgba(*hexrgb(c, 0.95 * fa))
        rrect(ctx, cx - 110, y1 - hh, 220, hh, 8)
        ctx.fill()


def sc_c1_ans(ctx, t):
    person(ctx, 360, 905, H0, t, "stand", 1)
    koma(ctx, 640, 520, 56, FASTC, a=fade(t, bd("c1_ans") + 0.4, 0.4), tilt=0.1)
    title_hand(ctx, "答え", RX, 160, 120, 8, fade(t, bd("c1_ans") + 0.4, 0.4))
    stk(ctx, t, "c1_ans", "たいていは、約束どおりか、\n1日遅れ", RX, 400, "yellow", size=56, off=0.8, frac=0.1, tilt=-0.01)
    stk(ctx, t, "c1_ans", "ごくまれに、長い川止めで\n1か月近く遅れる", RX, 650, "pink", size=56, off=0.0, frac=0.55, tilt=0.01)


# ============================================================
# 2 2倍以上払って急ぎ便にしたら、得をする？
# ============================================================
def sc_c2_title(ctx, t):
    t_ti = S("ch2") + 2.2
    title_hand(ctx, "問い2", RX, 150, 110, 7, fade(t, t_ti, 0.4))
    stk(ctx, t, "c2_intro", "料金を2倍以上払って、\n急ぎの便にしたら、得をする？", RX, 360, "yellow", size=52, off=1.8, tilt=-0.012)
    person(ctx, 360, 905, H0, t, "stand", 1)
    koma(ctx, 700, 560 + 14 * math.sin(t * 2), 56, FASTC, a=fade(t, S("ch2") + 2.4, 0.4), tilt=-0.1)
    koma(ctx, 790, 640 + 14 * math.sin(t * 2 + 1), 56, SLOWC, a=fade(t, S("ch2") + 2.7, 0.4), tilt=0.1)


def sc_c2_price(ctx, t):
    fa = fade(t, bd("c2_price"), 0.3)
    yb, unit = 760, 110.0
    groups = [("伊勢の松坂", 560, 2.4, "c2_price"), ("伊勢の山田", 1360, 2.9, "c2_3x")]
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, 150, 180, 1620, 700, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(200, yb)
    ctx.line_to(1720, yb)
    ctx.stroke()
    text(ctx, "料金（八日限を1とした比）", 560, 215, 46, INK, alpha=fa)
    for nm, cx, rat, key in groups:
        text(ctx, nm, cx, yb + 40, 56, INK, alpha=fa)
        for j, (kn, hv, col) in enumerate((("八日限", 1.0, SLOWC), ("六日限", rat, FASTC))):
            bx = cx - 110 + j * 220
            bu = ease_out(clamp01((t - (Sk(key, 0.15) if j else bd("c2_price") + 0.5)) / 0.8))
            hh = unit * hv * bu
            ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
            rrect(ctx, bx - 70, yb - hh, 140, hh, 8)
            ctx.fill()
            text(ctx, kn, bx, yb - 40 if False else yb + 98, 44, INK, alpha=fa)
        stk(ctx, t, key, f"約{rat}倍", cx + 110, yb - unit * rat - 70, "pink", fg=RED, size=56, off=0.5, tilt=-0.01, align="center")
    stk(ctx, t, "c2_yen", "円には直さず、倍率だけ", 1320, 255, "yellow", size=48, off=0.4, tilt=0.008, align="center")


def sc_c2_yoso(ctx, t):
    person(ctx, 360, 905, H0, t, "stand", 1)
    stk(ctx, t, "c2_gain", "急ぎ便の得は、\n何日分？", RX, 280, "yellow", size=64, off=0.2, tilt=-0.01)
    stk(ctx, t, "c2_yoso", "予想\n高い便なら、必ず早く着く", RX, 600, "pink", size=52, off=0.9, tilt=0.01)
    koma(ctx, 700, 560, 56, FASTC, a=fade(t, Sk("c2_gain", 0.3), 0.4), tilt=-0.1)


MAPP = RouteMap(110, 170, 1810, 450, lanes=2)


def sc_c2_setup(ctx, t):
    MAPP.draw(ctx)
    u = clamp01((t - bd("c2_how") - 0.3) / (Ek("c2_10k") - bd("c2_how") - 0.8))
    MAPP.piece(ctx, 0.02 + 0.40 * ease_in_out(u), 0, FASTC, s=38)
    MAPP.piece(ctx, 0.02 + 0.33 * ease_in_out(u), 1, SLOWC, s=38)
    person(ctx, 300, 925, 380, t, "stand", 1, a=fade(t, bd("c2_how") + 0.3, 0.4))
    stk(ctx, t, "c2_how", "同じ日に、同じ手紙を、2通", 600, 540, "yellow", size=56, off=0.5, tilt=-0.008)
    stk(ctx, t, "c2_fast", "急ぎの便（六日限）", 560, 690, "pink", fg=RED, size=52, off=0.3, tilt=0.008)
    stk(ctx, t, "c2_fast", "ふつうの便（八日限）", 560, 820, "mint", size=52, off=2.6, tilt=-0.008)
    stk(ctx, t, "c2_10k", "1万組", 1560, 700, "yellow", size=110, off=0.4, tilt=-0.012, align="center")


GRIDP_X0, GRIDP_Y0, GRIDP_C = 150, 235, 48


def sc_c2_stats(ctx, t):
    fa = fade(t, bd("c2_hit"), 0.3)
    text(ctx, "100組のうち", 400, 190, 52, INK, alpha=fa)
    # 100組のマス（どちらかが川止め18・2通とも10）
    n_hit = int(round(N_PAIR["hit"] * ease_out(clamp01((t - Sk("c2_hit", 0.35)) / 0.8))))
    both_on = t >= Sk("c2_both", 0.4)
    groups = [(N_PAIR["both"], "#c0392b"), (N_PAIR["hit"] - N_PAIR["both"], "#e8b04a")] if both_on else [(N_PAIR["hit"], "#e8b04a")]
    if n_hit < N_PAIR["hit"]:
        groups = [(n_hit, "#e8b04a")]
    cells100(ctx, GRIDP_X0, GRIDP_Y0, GRIDP_C, groups, a=fa)
    stk(ctx, t, "c2_hit", "どちらかが川止めに\n当たった 100組に18組", 400, 830, "yellow", size=44, off=0.3, tilt=-0.008, until=Sk("c2_both", 0.0) - 0.4, align="center")
    stk(ctx, t, "c2_both", "2通とも待たされた\n100組に10組", 400, 830, "pink", fg=RED, size=44, off=0.1, tilt=0.008, align="center")
    # 急ぎ便の得（1万組）
    gx0, pitch, gy1, gmax = 1010, 170, 770, 60.0
    ga = fa
    ctx.set_source_rgba(1, 1, 1, 0.55 * ga)
    rrect(ctx, 900, 150, 900, 780, 14)
    ctx.fill()
    text(ctx, "急ぎ便の得（1万組）", 1350, 180, 52, INK, alpha=ga)
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * ga))
    ctx.set_line_width(3)
    ctx.move_to(940, gy1)
    ctx.line_to(1780, gy1)
    ctx.stroke()
    labs = ["同じ日", "1日", "2日", "3日", "4日以上"]
    hi3 = fade(t, Sk("c2_ge3", 0.3), 0.3)
    hi0 = fade(t, Sk("c2_same", 0.3), 0.3)
    for k, d in enumerate(GAIN):
        cx = gx0 + k * pitch
        text(ctx, labs[k], cx, gy1 + 50, 44, INK, alpha=ga)
        bu = ease_out(clamp01((t - (Sk("c2_clear", 0.3) + BAR_STEP * k)) / 0.5))
        hh = (gy1 - 330) * d["pct"] / gmax * bu
        col = BLUE
        if k >= 3:
            col = _mix(BLUE, "#c0392b", hi3)
        if k == 0:
            col = _mix(BLUE, "#e8b04a", hi0)
        ctx.set_source_rgba(*hexrgb(col, 0.95 * ga))
        rrect(ctx, cx - 60, gy1 - max(hh, 4 * bu), 120, max(hh, 4 * bu), 6)
        ctx.fill()
    stk(ctx, t, "c2_clear", "中央値 2日", 1350, 275, "yellow", size=48, off=1.3, tilt=-0.01, align="center")
    stk(ctx, t, "c2_ge3", "川止めなしの組のうち\n3日以上 100組に20組ほど", 1580, 470, "pink", fg=RED, size=44, off=0.4, tilt=0.01, align="center")
    stk(ctx, t, "c2_same", "同じ日\n100組に3組だけ", 1090, 430, "yellow", size=44, off=0.4, tilt=-0.01, align="center")


def _mix(c0, c1, u):
    a = hexrgb(c0)
    b = hexrgb(c1)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * u) + 0.5) for i in range(3))


def sc_c2_paid(ctx, t):
    x0, x1, y, dm = 700, 1700, 700, 10
    a = fade(t, bd("c2_paid"), 0.3)
    sx = ruler(ctx, x0, x1, y, dm, a=a)
    text(ctx, "日", x1 + 50, y, 44, INK, alpha=a)
    xp = x0 + 9 * sx
    line2(ctx, (xp, y - 250), (xp, y + 20), RED, 6, a=a, dash=[14, 10])
    person(ctx, 330, 905, 380, t, "stand", 1, a=a)
    u = ease_in_out(clamp01((t - Sk("c2_paid", 0.1)) / 2.2))
    koma(ctx, x0 + 9 * sx * u, y - 70, 52, FASTC, a=a)
    koma(ctx, x0 + 9 * sx * u, y - 160, 52, SLOWC, a=a)
    stk(ctx, t, "c2_paid", "同じ日に着いた", xp - 40, 330, "pink", fg=RED, size=56, off=1.8, tilt=-0.01, align="center")
    stk(ctx, t, "c2_nrev", "急ぎ便のほうが\n遅い組は 0組", 1040, 330, "mint", size=48, off=0.6, tilt=0.01, align="center")


def sc_c2_each(ctx, t):
    t0 = bd("c2_each") + 0.3
    for k, (s_, x_, col) in enumerate((("ふつうの組", 330, "yellow"), ("いちばん得をした組", 960, "mint"), ("いちばん得を\nしなかった組", 1590, "pink"))):
        a = fade(t, t0 + 0.7 * k + 0.6, 0.4)
        mini_sticky(ctx, s_, x_, 480, 50, col, a=a, tilt=-0.015 + 0.015 * k)
        koma(ctx, x_ - 50, 330, 54, FASTC, a=a, tilt=-0.1)
        koma(ctx, x_ + 60, 345, 54, SLOWC, a=a, tilt=0.1)
    person(ctx, 250, 905, 330, t, "stand", 1, a=fade(t, t0 + 0.8, 0.4))
    text(ctx, "組を、1つずつ見る", 960, 640, 60, INK, alpha=fade(t, t0 + 0.4, 0.4))


def pair_scene(ctx, t, sp):
    """問い2の1組。上＝2段の地図（急ぎ便・ふつうの便）、左下＝あなた、右下＝2本の棒（着くまでの日数が伸びる）"""
    day = sp["dayf"](t)
    c = sp["card"]
    ptsf = kf_go(OFFS["六日限"], c["fast_river_wait"], c["T_fast"], 0.0, MAPP.fb, MAPP.fa)
    ptss = kf_go(OFFS["八日限"], c["slow_river_wait"], c["T_slow"], 0.0, MAPP.fb, MAPP.fa)
    lv = max(river_state(day, OFFS["六日限"], c["fast_river_wait"]), river_state(day, OFFS["八日限"], c["slow_river_wait"]))
    MAPP.draw(ctx, level=0.9 * lv, sign=lv if max(c["fast_river_wait"], c["slow_river_wait"]) >= 3 else 0.0)
    MAPP.piece(ctx, kv(ptsf, day), 0, FASTC, s=38)
    MAPP.piece(ctx, kv(ptss, day), 1, SLOWC, s=38)
    stk(ctx, t, sp["key_date"], sp["date"], 110, 108, "yellow", size=48, off=0.1, frac=sp["date_frac"], tilt=-0.008, align="left")
    la = fade(t, sp["t_in"], 0.4)
    person(ctx, 300, 925, 380, t, "stand", 1, a=la)
    dmax = max(c["T_fast"], c["T_slow"])
    unit = 780.0 / max(dmax, 9)
    bx0 = 880
    for k, (nm, T_, col) in enumerate((("急ぎ便", c["T_fast"], FASTC), ("ふつうの便", c["T_slow"], SLOWC))):
        yy = 610 + k * 120
        text(ctx, nm, bx0 - 24, yy, 50, INK, align="right", alpha=la)
        ln = min(day, T_) * unit
        if ln > 0.5:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * la))
            rrect(ctx, bx0, yy - 36, ln, 72, 8)
            ctx.fill()
        if day >= T_:
            text(ctx, f"{T_}日", bx0 + T_ * unit + 20, yy, 56, INK, align="left", alpha=la)
    text(ctx, "着くまでの日数", 980, 520, 44, PENCIL_T, align="left", alpha=la)
    stk(ctx, t, sp["gain_key"], sp["gain_txt"], 1380, 850, "pink", fg=RED, size=72, off=0.0, frac=sp["gain_frac"], tilt=-0.01, align="center")


_P1, _P2, _P3 = CARDS2["typical"], CARDS2["best"], CARDS2["worst"]
SP_PT = dict(card=_P1, date=f"{_P1['date']}出し", key_date="c2_t1", date_frac=0.4, t_in=bd("c2_t1") + 0.3, gain_key="c2_t3", gain_frac=0.0,
             gain_txt=f"得 {_P1['gain']}日", dayf=dmap([(Sk("c2_t2", 0.0), 0.0), (Sk("c2_t2", 0.0) + Dk("c2_t2") * 0.9, float(_P1["T_slow"]))]))
SP_PB = dict(card=_P2, date=f"{_P2['date']}出し", key_date="c2_b1", date_frac=0.5, t_in=bd("c2_b1") + 0.3, gain_key="c2_b4", gain_frac=0.0,
             gain_txt=f"得 {_P2['gain']}日",
             dayf=dmap([(Sk("c2_b2", 0.0), 0.0), (Sk("c2_b2", 0.0) + Dk("c2_b2") * 0.8, float(_P2["T_fast"])), (Ek("c2_b3") - 0.3, float(_P2["T_slow"]))]))
SP_PW = dict(card=_P3, date=f"{_P3['date']}出し", key_date="c2_w1", date_frac=0.55, t_in=bd("c2_w1") + 0.3, gain_key="c2_w4", gain_frac=0.0,
             gain_txt=f"得 {_P3['gain']}日",
             dayf=dmap([(Sk("c2_w2", 0.0), 0.0), (Sk("c2_w2", 0.0) + Dk("c2_w2") * 0.9, float(OFFS["八日限"] + 3)), (Sk("c2_w3", 0.0) + Dk("c2_w3") * 0.75, float(_P3["T_slow"]))]))


def sc_c2_card_t(ctx, t):
    pair_scene(ctx, t, SP_PT)


def sc_c2_card_b(ctx, t):
    pair_scene(ctx, t, SP_PB)
    stk(ctx, t, "c2_b2", "川止めの前に渡る", 1180, 108, "mint", size=46, off=0.2, tilt=0.01, align="center", until=Sk("c2_b3") - 0.2)
    stk(ctx, t, "c2_b3", "大井川で長い川止め", 1180, 108, "pink", size=46, off=0.2, tilt=0.01, align="center")


def sc_c2_card_w(ctx, t):
    pair_scene(ctx, t, SP_PW)
    stk(ctx, t, "c2_w2", "2通とも、同じ川止めで足止め", 1330, 108, "pink", size=46, off=0.2, tilt=0.01, align="center")


def sc_c2_shrink(ctx, t):
    fa = fade(t, bd("c2_s1"), 0.3)
    text(ctx, "100組のうち", 400, 190, 52, INK, alpha=fa)
    cells100(ctx, GRIDP_X0, GRIDP_Y0, GRIDP_C, [(N_PAIR["both"], "#c0392b")], a=fa)
    mini_sticky(ctx, "2通とも川止めを\n待った組 100組に10組", 400, 830, 44, "pink", fg=RED, a=fa, tilt=-0.008)
    # ふだんの得（2日）と、待った組の得（1日）
    yb, unit = 790, 230.0
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, 900, 150, 900, 780, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(940, yb)
    ctx.line_to(1760, yb)
    ctx.stroke()
    text(ctx, "ふだんの得", 1180, yb + 46, 46, INK, alpha=fa)
    text(ctx, "待った組の得", 1600, yb + 46, 46, INK, alpha=fa)
    h2, h1 = unit * 2, unit * 1
    shr = ease_in_out(clamp01((t - Sk("c2_s3", 0.1)) / 1.0))
    hh = h2 + (h1 - h2) * shr
    ctx.set_source_rgba(*hexrgb(BLUE, 0.95 * fa))
    rrect(ctx, 1110, yb - hh, 140, hh, 8)
    ctx.fill()
    if shr > 0.02:
        ctx.set_source_rgba(*hexrgb(RED, 0.8 * fa))
        ctx.set_line_width(4)
        ctx.set_dash([12, 10])
        ctx.rectangle(1110, yb - h2, 140, h2 - hh)
        ctx.stroke()
        ctx.set_dash([])
        arrow2(ctx, (1330, yb - h2 + 30), (1330, yb - h1 + 20), RED, w=6, a=shr, head=20)
    b1 = ease_out(clamp01((t - Sk("c2_s2", 0.35)) / 0.8))
    ctx.set_source_rgba(*hexrgb("#c0392b", 0.95 * fa))
    rrect(ctx, 1530, yb - h1 * b1, 140, h1 * b1, 8)
    ctx.fill()
    stk(ctx, t, "c2_s2", "得の中央値 1日", 1600, yb - h1 - 70, "pink", fg=RED, size=46, off=0.5, tilt=-0.01, align="center")
    stk(ctx, t, "c2_s3", "ふだんの2日", 1180, yb - h2 - 70, "yellow", size=46, off=-0.8, tilt=0.01, align="center")


def sc_c2_wait(ctx, t):
    fa = fade(t, bd("c2_s4"), 0.3)
    x0, unit = 520, 80.0
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, 130, 160, 1670, 760, 14)
    ctx.fill()
    text(ctx, "（図は一例）", 1630, 215, 44, PENCIL_T, alpha=fa)
    # 目もり
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(x0, 820)
    ctx.line_to(x0 + 15 * unit, 820)
    ctx.stroke()
    text(ctx, "日", x0 + 15 * unit + 40, 820, 44, INK, alpha=fa)
    rows = (("急ぎ便", 3, 13, 400, FASTC), ("ふつうの便", 4, 14, 560, SLOWC))
    u = clamp01((t - Sk("c2_s4", 0.0)) / 3.5)
    for nm, arr, fin, yy, col in rows:
        text(ctx, nm, x0 - 24, yy, 50, INK, align="right", alpha=fa)
        d = 10 * ease_in_out(u) * 1.5
        d = min(d, fin)
        run1 = min(d, arr)
        ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
        rrect(ctx, x0, yy - 34, run1 * unit, 68, 6)
        ctx.fill()
        if d > arr:
            wait_e = min(d, 10)
            ctx.set_source_rgba(*hexrgb(WATER_D, 0.85 * fa))
            rrect(ctx, x0 + arr * unit, yy - 34, (wait_e - arr) * unit, 68, 6)
            ctx.fill()
        if d > 10:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
            rrect(ctx, x0 + 10 * unit, yy - 34, (d - 10) * unit, 68, 6)
            ctx.fill()
    # 川明けの線
    ja = fade(t, Sk("c2_s4", 0.3) + 1.8, 0.4)
    line2(ctx, (x0 + 10 * unit, 300), (x0 + 10 * unit, 820), RED, 5, a=ja, dash=[14, 10])
    text(ctx, "川明け", x0 + 10 * unit, 270, 48, RED, alpha=ja)
    # 先に川に着くぶん、長く待つ
    stk(ctx, t, "c2_s4", "先に川に着いたぶん\n長く待たされる", 1250, 700, "yellow", size=52, off=1.0, tilt=-0.01, align="center")
    stk(ctx, t, "c2_s5", "だから、得が縮む", 760, 700, "pink", fg=RED, size=56, off=0.2, tilt=0.01, align="center")
    ya = fade(t, Sk("c2_s4", 0.0) + 0.4, 0.4)
    mini_sticky(ctx, "走る", 330, 270, 44, "yellow", a=ya, tilt=-0.01)
    mini_sticky(ctx, "川止めで待つ", 330, 345, 44, "mint", a=ya, tilt=0.01)


def sc_c2_ans(ctx, t):
    person(ctx, 360, 905, H0, t, "stand", 1)
    koma(ctx, 640, 520, 56, FASTC, a=fade(t, bd("c2_ans") + 0.4, 0.4), tilt=0.1)
    title_hand(ctx, "答え", RX, 160, 120, 8, fade(t, bd("c2_ans") + 0.4, 0.4))
    stk(ctx, t, "c2_ans", "急ぎ便は、ふつう\n2日 得をする", RX, 400, "yellow", size=56, off=0.8, frac=0.1, tilt=-0.01)
    stk(ctx, t, "c2_ans", "同じ川止めに当たると\n得は半分（1日）に縮む", RX, 650, "pink", size=56, off=0.0, frac=0.55, tilt=0.01)


SP_M["t_arrive"] = Sk("c1_m2", 0.0) + 2.4
SP_B["t_arrive"] = Sk("c1_b2", 0.62)
SP_W["t_arrive"] = Sk("c1_w4", 0.0) + 1.9

# ============================================================
# 3 返事が来るまで、何日待つ？
# ============================================================


def card3(ctx, t, sp):
    """問い3の1人。往き（青）・相手が書く（黄）・帰り（緑）の日を暦の色で見せ、×が1日ずつ増える"""
    day = sp["dayf"](t)
    off = OFFS[sp["kind"]]
    T1, w, T2 = sp["T1"], sp["w"], sp["T2"]
    go = kf_go(off, sp["wait1"], T1, 0.0, MAPC.fb, MAPC.fa)
    back = kf_go(off, sp["wait2"], T2, T1 + w, MAPC.fb, MAPC.fa, back=True)
    pts = go + [(T1 + w, 1.0)] + back[1:]
    total = T1 + w + T2
    lv = max(river_state(day, off, sp["wait1"]), river_state(day, off, sp["wait2"], t0=T1 + w))
    MAPC.draw(ctx, level=0.9 * lv, sign=lv if max(sp["wait1"], sp["wait2"]) >= 3 else 0.0)
    MAPC.piece(ctx, kv(pts, day), 0, FASTC, s=40)
    stk(ctx, t, sp["key_date"], sp["date"], 110, 108, "yellow", size=48, off=0.1, frac=sp["date_frac"], tilt=-0.008, align="left")
    la = fade(t, sp["t_in"], 0.4)
    person(ctx, 300, 925, 380, t, "stand", 1, a=la)
    for k, (nm, col) in enumerate((("往き", TINT_GO), ("書く", TINT_WRITE), ("帰り", TINT_BACK))):
        mini_sticky(ctx, nm, 640 + k * 170, 515, 44, col, a=la, tilt=0.0)
    wait_rng = (off, off + sp["wait1"]) if sp["wait1"] > 0 else None
    tint = [((1, T1), TINT_GO), ((T1 + 1, T1 + w), TINT_WRITE), ((T1 + w + 1, total), TINT_BACK)]
    calendar(ctx, CAL_X, CAL_Y, CAL_W, CAL_H, sp["n"], marks=day, a=la, cols=sp["cols"], tint=tint, wait=wait_rng)
    if day >= total - 1e-6:
        mini_sticky(ctx, f"{total}日目に返事", 1640, 515, 52, "yellow", a=la * fade(t, sp["t_arrive"], 0.3), tilt=-0.01)
    return total


_Q3M, _Q3B, _Q3W = CARDS3["median"], CARDS3["best"], CARDS3["worst"]
SP3_M = dict(kind=_Q3M["kind"], T1=_Q3M["T"], w=_Q3M["write"], T2=_Q3M["T2"], wait1=_Q3M["river_wait"], wait2=_Q3M["back_river_wait"], n=21, cols=7,
             key_date="c3_m1", date_frac=0.0, date=f"往き {_Q3M['date']}出し・{_Q3M['kind']}", t_in=bd("c3_m1") + 0.3,
             dayf=dmap([(Sk("c3_m2", 0.0), 0.0), (Sk("c3_m2", 0.0) + 3.6, float(_Q3M["T"])), (Sk("c3_m3", 0.2), float(_Q3M["T"])),
                        (Sk("c3_m3", 0.2) + 1.6, float(_Q3M["T"] + _Q3M["write"])), (Sk("c3_m4", 0.0), float(_Q3M["T"] + _Q3M["write"])),
                        (Sk("c3_m4", 0.0) + 2.3, float(_Q3M["reply"]))]))
SP3_M["t_arrive"] = Sk("c3_m4", 0.0) + 2.3
SP3_B = dict(kind=_Q3B["kind"], T1=_Q3B["T"], w=_Q3B["write"], T2=_Q3B["T2"], wait1=_Q3B["river_wait"], wait2=_Q3B["back_river_wait"], n=21, cols=7,
             key_date="c3_b1", date_frac=0.4, date=f"往き {_Q3B['date']}出し・{_Q3B['kind']}", t_in=bd("c3_b1") + 0.3,
             dayf=dmap([(Sk("c3_b2", 0.0), 0.0), (Sk("c3_b2", 0.0) + 2.6, float(_Q3B["T"])), (Sk("c3_b3", 0.0), float(_Q3B["T"] + _Q3B["write"])),
                        (Sk("c3_b3", 0.0) + 3.4, float(_Q3B["reply"]))]))
SP3_B["t_arrive"] = Sk("c3_b3", 0.0) + 3.4
SP3_W = dict(kind=_Q3W["kind"], T1=_Q3W["T"], w=_Q3W["write"], T2=_Q3W["T2"], wait1=_Q3W["river_wait"], wait2=_Q3W["back_river_wait"], n=50, cols=10,
             key_date="c3_w1", date_frac=0.0, date=f"往き {_Q3W['date']}出し・{_Q3W['kind']}", t_in=bd("c3_w1") + 0.3,
             dayf=dmap([(Sk("c3_w2", 0.0), 0.0), (Sk("c3_w2", 0.0) + 1.2, float(OFFS[_Q3W["kind"]])), (Ek("c3_w3") + 0.3, float(_Q3W["T"])),
                        (Sk("c3_w4", 0.0) + 0.3, float(_Q3W["T"])), (Sk("c3_w4", 0.0) + 3.0, float(_Q3W["T"] + _Q3W["write"])),
                        (Sk("c3_w5", 0.0), float(_Q3W["T"] + _Q3W["write"])), (Ek("c3_w5") + 0.2, float(_Q3W["reply"]))]))
SP3_W["t_arrive"] = Ek("c3_w5") + 0.2


def sc_c3_title(ctx, t):
    t_ti = S("ch3") + T_TITLE + 0.3
    title_hand(ctx, "問い3", RX, 150, 110, 9, fade(t, t_ti, 0.4))
    stk(ctx, t, "c3_intro", "手紙を出してから、\n返事が来るまで、何日待つ？", RX, 360, "yellow", size=52, off=1.8, tilt=-0.012)
    person(ctx, 360, 905, H0, t, "stand", 1)
    la = fade(t, S("ch3") + T_TITLE + 0.8, 0.4)
    t0 = S("ch3") + T_TITLE + 1.2
    calendar(ctx, 1020, 580, 780, 190, 14, marks=min(10.0, max(0.0, (t - t0) / 0.5)), a=la, cols=7, row_cap=95)


def sc_c3_sum(ctx, t):
    fa = fade(t, bd("c3_sum"), 0.3)
    xs = [(230, 560, TINT_GO), (810, 340, TINT_WRITE), (1170, 560, TINT_BACK)]
    for k, (x_, w_, col) in enumerate(xs):
        ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
        rrect(ctx, x_, 250, w_, 110, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * fa))
        ctx.set_line_width(3)
        rrect(ctx, x_, 250, w_, 110, 12)
        ctx.stroke()
    text(ctx, "＋", 800, 195, 56, INK, alpha=fa)
    text(ctx, "＋", 1160, 195, 56, INK, alpha=fa)
    na = fade(t, Sk("c3_names", 0.0), 0.3)
    for (x_, w_, col), nm in zip(xs, ("往きの手紙", "相手が書く時間", "帰りの手紙")):
        text(ctx, nm, x_ + w_ / 2, 305, 46, INK, alpha=na)
    person(ctx, 330, 925, 380, t, "stand", 1, a=fa)
    stk(ctx, t, "c3_sum", "返事が来るまで ＝\n三つを足した日数", 1000, 500, "yellow", size=52, off=0.3, tilt=-0.01, align="center")
    la = fade(t, Sk("c3_late", 0.3), 0.4)
    if la > 0.003:
        arrow2(ctx, (510, 372), (700, 610), RED, w=6, a=la, head=22)
        mini_sticky(ctx, "往きの遅れは、そのまま\n返事の遅れになる", 1000, 680, 50, "pink", a=la, tilt=0.008)
    stk(ctx, t, "c3_write", "書く時間は 1〜3日のくじ（仮定）", 1180, 850, "mint", size=48, off=0.4, tilt=-0.008, align="center")


def sc_c3_ise(ctx, t):
    MAPC.draw(ctx, level=0.0, sign=0.0)
    u = ease_in_out(clamp01((t - Sk("c3_back", 0.15)) / (Dk("c3_back") - 1.2)))
    MAPC.piece(ctx, 1.0 - u * (1.0 - MAPC.fa), 0, FASTC, s=40)
    person(ctx, 330, 925, 380, t, "stand", 1, kimono=AITE_KIMONO, a=fade(t, bd("c3_ise"), 0.3))
    stk(ctx, t, "c3_ise", "返事を書くのは、\n伊勢の実家の人", 900, 600, "yellow", size=56, off=0.3, tilt=-0.01, align="left")
    stk(ctx, t, "c3_back", "帰りも、往きと同じ便\n別のくじを引く", 1250, 820, "mint", size=52, off=0.6, tilt=0.01, align="center")


def sc_c3_yoso(ctx, t):
    person(ctx, 330, 905, H0, t, "stand", 1)
    stk(ctx, t, "c3_yoso", "予想\n六日の約束の便なら、\n往復12日と少しで、\n2週間はかからない", RX, 300, "pink", size=48, off=0.9, tilt=0.01)
    la = fade(t, bd("c3_yoso") + 0.4, 0.4)
    calendar(ctx, 1020, 600, 780, 190, 14, marks=12.0 * clamp01((t - Sk("c3_yoso", 0.5)) / 2.0), promise=14, a=la, cols=7, row_cap=95)
    text(ctx, "赤い丸＝2週間", 1410, 560, 44, INK, alpha=la)


BINS3 = [(0, 13, "〜13"), (14, 20, "14〜20"), (21, 27, "21〜27"), (28, 99, "28〜")]
COUNTS3 = [int(REPLY_COUNT[a_:min(b_, 59) + 1].sum()) for a_, b_, _l in BINS3]
BIN3_COL = [BLUE, "#8f95ab", "#e8b04a", "#c0392b"]
GRID3_X0, GRID3_Y0, GRID3_C = 1180, 245, 50


def sc_c3_dist(ctx, t):
    fa = fade(t, bd("c3_10k"), 0.3)
    # 左: 返事が来るまでの日数（まとめた棒）
    x0, pitch, y1, ytop = 150, 190, 790, 360
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, 110, 180, 840, 740, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(130, y1)
    ctx.line_to(930, y1)
    ctx.stroke()
    text(ctx, "返事が来るまでの日数（1万人）", 520, 215, 46, INK, alpha=fa)
    text(ctx, "日", 925, y1 + 50, 44, INK, alpha=fa)
    mx = max(COUNTS3)
    for k, (a_, b_, lab_) in enumerate(BINS3):
        cx = x0 + (k + 0.5) * pitch
        text(ctx, lab_, cx, y1 + 50, 44, INK, alpha=fa)
        bu = ease_out(clamp01((t - (Sk("c3_10k", 0.2) + BAR_STEP * k)) / 0.5))
        hh = (y1 - ytop) * COUNTS3[k] / mx * bu
        ctx.set_source_rgba(*hexrgb(BIN3_COL[k], 0.95 * fa))
        rrect(ctx, cx - 70, y1 - hh, 140, hh, 6)
        ctx.fill()
    ma = stk(ctx, t, "c3_med", "中央値 15日", x0 + 1.5 * pitch, 300, "yellow", size=52, off=0.5, tilt=-0.01, align="center")
    if ma[0] > 0:
        arrow2(ctx, (x0 + 1.5 * pitch, 350), (x0 + 1.5 * pitch, y1 - (y1 - ytop) * COUNTS3[1] / mx - 14), RED, w=5, a=fade(t, Sk("c3_med", 0.5) + 0.3, 0.3), head=18)
    # 右: 100人（マス）
    stk(ctx, t, "c3_yoso" if False else "c3_10k", "予想\n2週間はかからない", 1450, 165, "pink", size=44, off=0.3, tilt=0.008, align="center")
    cw = clamp01((t - Sk("c3_wrong", 0.35)) / 0.7)
    if cw > 0:
        cross_mark(ctx, 1725, 165, 46, a=1.0, p=cw, width=9)
    ph = [(Sk("c3_86", 0.0), ihalf(GE14), "#8f95ab", "全体で、2週間以上待った人", Sk("c3_86", 0.22), "4人に3人"),
          (Sk("c3_86", 0.47), ihalf(MQ3["by_kind"][1]["ge14"]), "#8f95ab", "六日の約束の便の人のうち\n2週間以上待った人", Sk("c3_86", 0.86), f"100人に{ihalf(MQ3['by_kind'][1]['ge14'])}人"),
          (Sk("c3_25", 0.0), ihalf(MQ3["any_river"]), "#d9553d", "往きか帰りで川止めに\n当たった人", Sk("c3_25", 0.65), f"100人に{ihalf(MQ3['any_river'])}人"),
          (Sk("c3_9", 0.0), ihalf(MQ3["ge21"]), "#c0392b", "3週間以上待った人", Sk("c3_9", 0.55), f"100人に{ihalf(MQ3['ge21'])}人"),
          (Sk("c3_2", 0.0), ihalf(MQ3["ge28"]), "#7a1f14", "4週間以上待った人", Sk("c3_2", 0.6), f"100人に{ihalf(MQ3['ge28'])}人ほど")]
    cur = None
    for k, ph_ in enumerate(ph):
        if t >= ph_[0]:
            cur = k
    if cur is not None:
        t0_, n_, col, cap, tv, vtxt = ph[cur]
        n_show = int(round(n_ * ease_out(clamp01((t - (tv - 0.3)) / 0.9))))
        cells100(ctx, GRID3_X0, GRID3_Y0, GRID3_C, [(n_show, col)], a=fade(t, Sk("c3_86", 0.0) - 0.4, 0.3))
        text(ctx, cap, 1430, 800, 44, INK, alpha=fade(t, t0_, 0.3))
        if t >= tv:
            mini_sticky(ctx, vtxt, 1430, 890, 56, "yellow", fg=RED, a=fade(t, tv, 0.3), tilt=-0.01)
    else:
        cells100(ctx, GRID3_X0, GRID3_Y0, GRID3_C, [], a=fade(t, Sk("c3_10k", 0.0), 0.4) * 0.5)
        text(ctx, "100人のうち", 1430, 800, 44, INK, alpha=fade(t, Sk("c3_10k", 0.0), 0.4))


def sc_c3_each(ctx, t):
    t0 = bd("c3_each") + 0.3
    for k, (s_, x_, col) in enumerate((("中央値の人", 330, "yellow"), ("いちばん短く済んだ人", 960, "mint"), ("いちばん長く待った人", 1590, "pink"))):
        a = fade(t, t0 + 0.7 * k + 0.6, 0.4)
        mini_sticky(ctx, s_, x_, 480, 50, col, a=a, tilt=-0.015 + 0.015 * k)
        koma(ctx, x_, 330, 58, (BLUE, "#5aa469", FASTC)[k], a=a, tilt=(-0.1, 0.05, 0.12)[k])
    person(ctx, 250, 905, 330, t, "stand", 1, a=fade(t, t0 + 0.6, 0.4))
    text(ctx, "待った人を、1人ずつ見る", 960, 640, 60, INK, alpha=fade(t, t0 + 0.3, 0.4))


def sc_c3_card_m(ctx, t):
    card3(ctx, t, SP3_M)


def sc_c3_card_b(ctx, t):
    card3(ctx, t, SP3_B)


def sc_c3_card_w(ctx, t):
    card3(ctx, t, SP3_W)
    stk(ctx, t, "c3_w7", "47日、待った", 330, 500, "pink", fg=RED, size=44, off=0.3, tilt=-0.01, align="center", until=Sk("c3_w8", 0.0) - 0.1)
    stk(ctx, t, "c3_w8", "待つだけ", 330, 500, "yellow", size=44, off=0.1, tilt=0.01, align="center")
    stk(ctx, t, "c3_w6", "最長 47日\n（くじを引き直すと47〜69日で動く）", 1300, 108, "pink", size=44, off=0.3, tilt=0.008, align="center")


def sc_c3_ans(ctx, t):
    person(ctx, 360, 905, H0, t, "stand", 1)
    koma(ctx, 640, 520, 56, FASTC, a=fade(t, bd("c3_ans") + 0.4, 0.4), tilt=0.1)
    title_hand(ctx, "答え", RX, 160, 120, 8, fade(t, bd("c3_ans") + 0.4, 0.4))
    stk(ctx, t, "c3_ans", "返事が来るまでの\n中央値は 15日", RX, 400, "yellow", size=56, off=0.8, frac=0.15, tilt=-0.01)
    sa = stk(ctx, t, "c3_ans", "「2週間はかからない」\nという予想は、外れた", RX, 650, "pink", size=52, off=0.0, frac=0.55, tilt=0.01)
    cw = clamp01((t - Sk("c3_ans", 0.55) - 1.2) / 0.7)
    if cw > 0 and sa[0] > 0:
        cross_mark(ctx, RX + sa[0] + 40, 650, 48, a=1.0, p=cw, width=9)


# ============================================================
# 4 まとめ
# ============================================================
def sc_c4_answers(ctx, t):
    for k, (s_, x_, col, fr) in enumerate((("約束の日に着く\n100通に64通", 330, "yellow", 0.1), ("急ぎ便の得は\n2日 → 1日", 960, "mint", 0.42), ("返事が来るまで\n中央値 15日", 1590, "pink", 0.72))):
        stk(ctx, t, "c4_0", s_, x_, 420, col, size=56, off=0.0, frac=fr, tilt=-0.015 + 0.015 * k, align="center")
    person(ctx, 960, 905, 330, t, "stand", 1, a=fade(t, S("ch4") + T_TITLE + 0.4, 0.4))


def sc_c4_winter(ctx, t):
    fa = fade(t, bd("c4_1"), 0.3)
    month_bars(ctx, t, D6_MONTH, 6.0, Sk("c4_1", 0.0) + 0.1, fa, hi=(11, 0, 1), title="6日以上遅れた手紙の割合（出した月ごと）", hi_col=BLUE)
    stk(ctx, t, "c4_1", "雨の少ない冬に出すのが、\nいちばん安全", 1420, 270, "yellow", size=52, off=0.5, tilt=-0.01, align="center")


def sc_c4_close(ctx, t):
    q = fade(t, bd("c4_2") + 0.1, 0.4)
    person(ctx, 360, 905, 420, t, "stand", 1, a=q)
    mini_sticky(ctx, "あなたなら、\n返事を何日、待てますか？", 1360, 250, 56, "yellow", a=q, tilt=-0.02)
    calendar(ctx, 900, 430, 900, 190, 14, marks=min(14.0, max(0.0, (t - Sk("c4_2", 0.3)) / 0.6)), a=q, cols=7, row_cap=95)
    mini_sticky(ctx, "数字は、この動画の仮定で計算した結果。\n実際の飛脚の遅れを、言い当てるものではない", 1280, 780, 44, "pink", a=fade(t, Sk("c4_3", 0.05), 0.4), tilt=0.01)


# ============================================================
# 終了画面（最後の約7秒）・区切り・全体
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
    return [("約束の日に着いたのは", f"100通に{ihalf(MQ1['on_time'])}通ほど", "yellow", INK, -0.010),
            ("急ぎ便の得は、ふつう", f"{ihalf(PA['median'])}日（同じ川止めで1日）", "pink", RED, 0.008),
            ("返事が来るまでの中央値は", f"{ihalf(MQ3['median'])}日", "mint", INK, -0.008)]


def sc_end(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "江戸から、手紙を1万通出したら", LCX_E, 162, 44, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=54)
    t9 = T_ES + 0.5
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


CARD_BY_N = {1: "約束の日に、間に合う？", 2: "急ぎ便は、得をする？", 3: "何日、待つ？", 4: "まとめ"}
CH_TITLES = [c["title"] for c in CHAPS]
CARD_TITLES = [CARD_BY_N.get(c["n"], c["title"]) for c in CHAPS]
CARD_POS = {1: (960, 300), 2: (960, 300), 3: (960, 300), 4: (960, 560)}
CARD_HOLD = {1: 3.0, 2: 3.0, 3: 3.0, 4: 2.4}              # 章カードを出す秒数（問いのカードは 11字 → 文字数÷8＋1秒 ＝ 2.4秒以上読める）
T_TITLE = 3.2                                             # 章の題字の場面は、章カードが消えてから


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        hold = CARD_HOLD.get(ch[0], 2.0)
        if 0 <= age <= hold:
            a = clamp01(age / 0.35) * clamp01((hold - age) / 0.4)
            x_, y_ = CARD_POS.get(ch[0], (lf.GUTTER, 470))
            lf.chapter_card(ctx, CARD_TITLES[ch[0]], a, x=x_, y=y_, size=60)


# ---- 区切り（問い2と問い3のあいだ）----
EC_LEFT = ("約束の日に着くのは100通に64通", "急ぎ便の得は2日、待つと1日")
EC_RIGHT = ("返事は", "何日後に来る？")
EC_FADE = 0.35                                          # Eyecatch は t1 から 0.35秒で消える。次の章カードと文字が重ならないよう、消え終わりを問い3の始まりにそろえる
EC = lk.Eyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None

# ---- 場面の並び ----
SC_START = {}


def _sc(name, t0, t1, fn, first=False):
    SC_START[name] = t0
    scene(name, t0, t1, fn, first)


_sc("open", 0.0, bz("c0_riv"), sc_open, first=True)
_sc("c0_river", bz("c0_riv"), bz("c0_cal"), sc_c0_river)
_sc("c0_cal", bz("c0_cal"), bz("c0_10k"), sc_c0_cal)
_sc("c0_grid", bz("c0_10k"), bz("c0_next"), sc_c0_grid, first=True)
_sc("c0_tags", bz("c0_next"), S("ch1") - 0.3, sc_c0_tags)
_sc("c1_title", S("ch1") + T_TITLE, bd("c1_10k"), sc_c1_title)
_sc("c1_10k", bd("c1_10k"), bd("c1_def"), sc_c1_10k)
_sc("c1_def", bd("c1_def"), bd("c1_kuji"), sc_c1_def)
_sc("c1_kuji", bd("c1_kuji"), bd("c1_kinds"), sc_c1_kuji)
_sc("c1_kinds", bd("c1_kinds"), bd("c1_late1"), sc_c1_kinds)
_sc("c1_kishu", bd("c1_late1"), bd("c1_src"), sc_c1_kishu)
_sc("c1_src", bd("c1_src"), bd("c1_rain"), sc_c1_src)
_sc("c1_rain", bd("c1_rain"), bd("c1_half"), sc_c1_rain)
_sc("c1_half", bd("c1_half"), bd("c1_moved"), sc_c1_half)
_sc("c1_hist", bd("c1_moved"), bd("c1_p64"), sc_c1_hist)
_sc("c1_dist", bd("c1_p64"), bd("c1_sort"), sc_c1_dist)
_sc("c1_median", bd("c1_sort"), bd("c1_each"), sc_c1_median)
_sc("c1_each", bd("c1_each"), bd("c1_m1"), sc_c1_each)
_sc("c1_card_m", bd("c1_m1"), bd("c1_b1"), sc_c1_card_m)
_sc("c1_card_b", bd("c1_b1"), bd("c1_w1"), sc_c1_card_b)
_sc("c1_card_w", bd("c1_w1"), bd("c1_most"), sc_c1_card_w)
_sc("c1_tail", bd("c1_most"), bd("c1_month"), sc_c1_tail)
_sc("c1_month", bd("c1_month"), T_SCEN0, sc_c1_month)
_sc("c1_scen", T_SCEN0, T_SCEN1, sc_c1_scen)
_sc("c1_ans", bd("c1_ans"), S("ch2") - 0.3, sc_c1_ans)
_sc("c2_title", S("ch2") + T_TITLE, bd("c2_price"), sc_c2_title)
_sc("c2_price", bd("c2_price"), bd("c2_gain"), sc_c2_price)
_sc("c2_yoso", bd("c2_gain"), bd("c2_how"), sc_c2_yoso)
_sc("c2_setup", bd("c2_how"), bd("c2_hit"), sc_c2_setup)
_sc("c2_stats", bd("c2_hit"), bd("c2_paid"), sc_c2_stats)
_sc("c2_paid", bd("c2_paid"), bd("c2_each"), sc_c2_paid)
_sc("c2_each", bd("c2_each"), bd("c2_t1"), sc_c2_each)
_sc("c2_card_t", bd("c2_t1"), bd("c2_b1"), sc_c2_card_t)
_sc("c2_card_b", bd("c2_b1"), bd("c2_w1"), sc_c2_card_b)
_sc("c2_card_w", bd("c2_w1"), bd("c2_s1"), sc_c2_card_w)
_sc("c2_shrink", bd("c2_s1"), bd("c2_s4"), sc_c2_shrink)
_sc("c2_wait", bd("c2_s4"), bd("c2_ans"), sc_c2_wait)
_sc("c2_ans", bd("c2_ans"), (T_RS0 - 0.3) if EC else DUR, sc_c2_ans)
_sc("c3_title", S("ch3") + T_TITLE, bd("c3_sum"), sc_c3_title)
_sc("c3_sum", bd("c3_sum"), bd("c3_ise"), sc_c3_sum)
_sc("c3_ise", bd("c3_ise"), bd("c3_yoso"), sc_c3_ise)
_sc("c3_yoso", bd("c3_yoso"), bd("c3_10k"), sc_c3_yoso)
_sc("c3_dist", bd("c3_10k"), bd("c3_each"), sc_c3_dist)
_sc("c3_each", bd("c3_each"), bd("c3_m1"), sc_c3_each)
_sc("c3_card_m", bd("c3_m1"), bd("c3_b1"), sc_c3_card_m)
_sc("c3_card_b", bd("c3_b1"), bd("c3_w1"), sc_c3_card_b)
_sc("c3_card_w", bd("c3_w1"), bd("c3_ans"), sc_c3_card_w)
_sc("c3_ans", bd("c3_ans"), S("ch4") - 0.3, sc_c3_ans)
_sc("c4_answers", S("ch4") + T_TITLE, bd("c4_1"), sc_c4_answers)
_sc("c4_winter", bd("c4_1"), bd("c4_2"), sc_c4_winter)
_sc("c4_close", bd("c4_2"), T_ES, sc_c4_close)
_sc("end", T_ES, DUR + 2.0, sc_end)


def draw(ctx, t, sub=True):
    lf.spread(ctx)
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
    """亀の足音（ぽてっ・とこっ）。短い下がり調子の丸い音＋ごく小さな擦れ（kaidan-long.py と同じ）"""
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    n = np.random.default_rng(seed + 50).standard_normal(len(tt))
    n = np.convolve(n, np.ones(12) / 12, mode="same") * np.exp(-tt * 120) * 0.35
    return (tone * env + n) * 0.8


BELLS = [Sk("c0_res", 0.18), Sk("c1_p64", 0.3), Sk("c1_tmed", 0.5), Sk("c2_t3", 0.1), Sk("c2_b4", 0.1), Sk("c2_s2", 0.4), Sk("c3_med", 0.4), Sk("c3_86", 0.55)]


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    from long_bgm import bgm_track      # 2026-11-06 カスミソウ（甘茶の音楽工房）
    mx.add(0, bgm_track(DUR, lf.SR), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 5):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for i_, ts_ in enumerate(EC.step_times()):
        mx.add(ts_, turtle_step(seed=i_, high=bool(i_ % 2)), 0.32)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.1, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.09)   # 声に重なるので小さく
    mx.add(Sk("c4_2", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.2)
    mx.add(Sk("c4_sub", 0.0) + 0.2, bell(523.3, 1.6), 0.12)
    return mx


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
REST_STILLS = tuple(EC.still_times()) if EC else (0.0, 0.0, 0.0)


def still_list():
    return [
        ("01_0.0s", "① 0.0秒: 問い・あなたと飛脚", 0.0),
        ("02_2.5s", "② 2.5秒: 手紙を渡す", 2.5),
        ("03_5.0s", "③ 5.0秒", 5.0),
        ("04_c0_river", "④ 川止め（地図と川ばた）", Sk("c0_def", 0.8) + 0.2),
        ("05_c0_cal", "⑤ 暦に×が増える", Ek("c0_cal") - 0.3),
        ("06_result", "⑥ 結果の数字（4人に3人）", Sk("c0_res", 0.18) + 2.6),
        ("07_conditions", "⑦ 条件の札（4行・仮定を囲む）", Sk("c0_assume", 0.88)),
        ("08_tags", "⑧ 3つの問い", Sk("c0_next") + 1.5),
        ("09_c1_hist", "⑨ 問い1: 着いた日ごとの棒", Sk("c1_moved", 0.0) + 2.9),
        ("10_c1_dist", "⑩ 問い1: 遅れの分布", Sk("c1_p10") + 2.0),
        ("11_c1_median", "⑪ 問い1: 並べた1万通と中央値", Sk("c1_dmed") + 2.0),
        ("12_c1_card_m", "⑫ 問い1: 中央値の手紙（4月23日・6日で着く）", SP_M["t_arrive"] + 1.2),
        ("13_c1_card_b", "⑬ 問い1: いちばん早い手紙（12月9日）", SP_B["t_arrive"] + 1.2),
        ("14_c1_card_w", "⑭ 問い1: いちばん遅れた手紙（川止め28日）", SP_W["t_arrive"] + 2.0),
        ("15_c1_tail", "⑮ 問い1: 遅れた日数の4割", Sk("c1_share", 0.5) + 2.2),
        ("16_c1_month", "⑯ 問い1: 月ごとの遅れ", Sk("c1_apr") + 2.0),
        ("16b_c1_scen", "⑯b 問い1: 川止めの幅（札だけ・声なし）", T_SCEN0 + 3.2),
        ("17_c2_stats", "⑰ 問い2: 100組と得の棒", Sk("c2_same", 0.4) + 2.2),
        ("18_c2_pair_t", "⑱ 問い2: 2通並び（ふつうの組）", Sk("c2_t3") + 1.5),
        ("19_c2_pair_b", "⑲ 問い2: 2通並び（いちばん得）", Sk("c2_b4") + 1.5),
        ("20_c2_pair_w", "⑳ 問い2: 2通並び（得0日）", Sk("c2_w4") + 1.5),
        ("21_c2_shrink", "㉑ 問い2: 得が半分に縮む", Sk("c2_s3") + 2.0),
        ("22a_ec_start", "㉒a 区切り: 始め", REST_STILLS[0]),
        ("22b_ec_mid", "㉒b 区切り: 亀が真ん中", REST_STILLS[1]),
        ("22c_ec_end", "㉒c 区切り: 終わり", REST_STILLS[2]),
        ("23_c3_dist", "㉓ 問い3: 返事の日数と100人", Sk("c3_25") + 3.0),
        ("24_c3_card_m", "㉔ 問い3: 暦（中央値の人・15日）", SP3_M["t_arrive"] + 2.0),
        ("25_c3_card_w", "㉕ 問い3: 暦（いちばん長く待った人・47日）", SP3_W["t_arrive"] + 2.0),
        ("26_summary", "㉖ まとめ: 3つの答え", Sk("c4_0", 0.9) - 0.2),
        ("27_end", "㉗ 終了画面", min(DUR - 0.5, Sk("c4_sub", 0.0) + 1.5)),
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
    lab_h, pad = 62, 10
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 20)
    except Exception:
        fnt = ImageFont.load_default()
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        lab = items[k][1]
        dr.text((x + 4, y + H_ + 2), f"{_ts(items[k][2])}", fill=(255, 220, 120), font=fnt)
        dr.text((x + 4, y + H_ + 28), lab[:24], fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir.parent / "stills_480.png")
    print("一覧:", out_dir.parent / "stills_480.png")


def stills_preview():
    stills_sheet(OUT / "stills", still_list())


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            rows.append(f"[章「{it.title}」]" if it.id == "ch0" else f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE.get(it.id, '映像だけ')}）")
        else:
            nt = LINE_NOTE.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    """読みの確認。read_aloud が AivisSpeech を起動するので、--fake-voice のときは --real-readings を付けない限り、文だけ並べる"""
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            reading = "" if (FAKE and "--real-readings" not in sys.argv) else "\n    → " + voice.read_aloud(spoken)
            rows.append(f"{it.id}: {shown_}{reading}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


# ============================================================
# 絵の出る時刻の記録（visual_lag 用）: 枠は声の0.5秒前までに・答えの数字は声に合わせる
# ============================================================
def rd(scene_name, own_t, d):
    """場面 scene_name の中の絵（自分の出る時刻 own_t・フェード d 秒）が読めるようになる時刻（場面のフェードインとのおそいほう）"""
    return max(SC_START[scene_name] + SC_DELAY + SC_IN, own_t + d)


def _fr(name, scene_nm, key, d=0.3):
    t0 = bd(key)
    return lk.Cue(name, "frame", t0, rd(scene_nm, t0, d), ID[key])


def _val(name, key, frac, off):
    t0 = Sk(key, frac) + off
    return lk.Cue(name, "value", t0, t0 + 0.4, ID[key])


CUE_GRID0 = lk.Cue("1万マスの枠（読み方・マス）", "frame", T_GRID0, T_GRID0 + 0.25, ID["c0_10k"])
ALL_CUES = [
    _val("箱「4人に3人が 2週間以上」", "c0_res", 0.18, 0.0),
    _fr("棒の枠（着いた日ごと）", "c1_hist", "c1_moved"),
    _fr("棒の枠（遅れの分布）", "c1_dist", "c1_p64"),
    _val("棒「100通に64通」", "c1_p64", 0.25, 0.5), _val("棒「100通に26通」", "c1_p26", 0.25, 0.5), _val("棒「100通に7通」", "c1_p7", 0.25, 0.5),
    _val("棒「100通に3通ほど」", "c1_p3", 0.25, 0.5),
    _fr("並べた1万通の帯の枠", "c1_median", "c1_sort"),
    _val("箱「中央値 6日」", "c1_tmed", 0.0, 0.5),
    _fr("雨の日の割合の棒の枠", "c1_rain", "c1_rain"),
    _fr("月ごとの遅れの棒の枠", "c1_month", "c1_month"),
    _fr("料金の比の棒の枠", "c2_price", "c2_price"),
    _val("札「約2.4倍」", "c2_price", 0.15, 0.5), _val("札「約2.9倍」", "c2_3x", 0.15, 0.5),
    _fr("100組のマス・得の棒の枠", "c2_stats", "c2_hit"),
    _val("札「100組に3組だけ」", "c2_same", 0.0, 0.4),
    _fr("得が縮む棒の枠", "c2_shrink", "c2_s1"),
    _fr("待ち時間の図の枠", "c2_wait", "c2_s4"),
    _fr("三つを足した帯の枠", "c3_sum", "c3_sum"),
    _fr("返事の日数の棒・100人のマスの枠", "c3_dist", "c3_10k"),
    _val("札「100人に86人」", "c3_86", 0.55, 0.0), _val("札「100人に25人」", "c3_25", 0.65, 0.0),
]

# ============================================================
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
CARD_LINES = {ln for t_ in CARD_TITLES for ln in t_.split("\n")}
WARNS = []
SCENE_MIN = 3.0                 # 場面・グラフは最低3秒出す（2026-10-29 ユーザー指摘「映像の切り替わりが早すぎる」）


def _allowed_nums():
    ok = set(float(x) for x in range(0, 61)) | {100.0, 10000.0, 64.0, 68.0, 86.0, 69.0, 0.8, 2.4, 2.9, 14.0}
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
    """sims/check-long.py（札の表示時間の点検 short_texts をロングどうしで共用する）"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_long", Path(__file__).resolve().parent / "check-long.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pace_problems():
    """場面の長さ（3秒未満）と、文の途中で場面が替わる所"""
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


STILL_MAX = 15.0                 # 同じ絵は15秒まで（2026-10-31 ユーザーOK。yomichi-long.py と同じ照合）
STILL_THR = 0.005                # 画面の0.5%以上が変わったら「動いた」


def still_spans(step=0.5, scale=0.25, thr=STILL_THR):
    """字幕なしの絵を step 秒ごとに描き、最後に動いたコマから画面の thr 以上が変わるまでを「同じ絵」の区間とする。[(始め, 終わり), …]（長い順）"""
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
    # ---- 台本の読み込み ----
    A(f"台本: 章は5つ（0〜4）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 5 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()))
    A(f"題字「{QTXT}」は第0章の題名「{CH_TITLES[0]}」と同じ言葉（句読点・空白をのぞく。サムネと同じ問い）", QTXT.replace(" ", "") == CH_TITLES[0].replace("、", "").replace(" ", ""))
    V = lambda name, val, exp, tol: checks.append((name, float(val), float(exp), tol))
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]) if False else S("c0_0"), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:])]
    A(f"台本: 冒頭（第0章）の文と文の間は 0.3秒前後（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし", all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch2"))
    sil = [(g, GAP_SEC[g]) for g in GAP_NOTE]
    A(f"台本: 無音はどこも10秒以内（{sil}）・最初の無音は第2章の終わり（{min(S(g) for g in GAP_NOTE):.1f}秒）", all(v <= 10 for _g, v in sil))
    n_rest = len(REST)
    A(f"区切り: 台本の「（無音 4秒・区切り。…）」は {n_rest} か所・長さ {T_RS1 - T_RS0:.1f}秒（約4秒）", n_rest == 1 and abs((T_RS1 - T_RS0) - 4.0) < 0.01)
    A(f"区切り: 問い2のあと・問い3の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・章は5つのまま（{len(CHAPS)}章・chapters {len(tl.chapters)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E("c2_33") - 1e-6 and abs(T_RS1 - S("ch3")) < 1e-6 and len(CHAPS) == 5 and len(tl.chapters) == 5
      and not any("区切り" in t_ or "ここまで" in t_ for t_ in CH_TITLES) and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    A(f"区切り: 動画の真ん中あたり（{(T_RS0 + T_RS1) / 2 / DUR:.1%} のところ・35〜75%）・声の行なし", 0.35 <= (T_RS0 + T_RS1) / 2 / DUR <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋{EC_LEFT}・右は「ここから」＋{EC_RIGHT}", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 亀は左ページ（x {xs_[0]:.0f}）から右ページ（x {xs_[-1]:.0f}）へ歩く・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    nums40 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and E(it.id) < 40:
            nums40 |= set(_re.findall(r"\d+人に\d+人|\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭40秒（言い終わる文）の声の数字は3個以内（{sorted(nums40)}）", len(nums40) <= 3)
    t_res0, t_res1 = Sk("c0_res"), Ek("c0_res")
    A(f"冒頭の結果の数字（4人に3人）の声の始まりは {t_res0:.1f}秒（本番の声は30秒以内・偽の声は余裕を見て29.5秒以内）", t_res0 <= (29.5 if FAKE else 30.0))
    A(f"冒頭の結果の数字の文は 0:{t_res0:04.1f}〜0:{t_res1:04.1f}（40秒以内には収まる）・問い1より前", t_res1 <= 40.0 and t_res1 < S("ch1"))
    # ---- 声の数字 = data.json ----
    q1, q3 = MQ1, MQ3
    exp = [("c0_res", f"4人に{ihalf(GE14 / 25)}人"), ("c1_p64", f"100通に{ihalf(q1['on_time'])}通"), ("c1_p26", f"100通に{ihalf(q1['d1'])}通"),
           ("c1_p7", f"100通に{ihalf(q1['d2_5'])}通"), ("c1_p3", f"100通に{ihalf(q1['d6'])}通"), ("c1_tmed", f"{ihalf(q1['T_median'])}日"),
           ("c1_dmed", f"{ihalf(q1['delay_median'])}日"), ("c1_w3", f"{_C1W['river_wait']}日"), ("c1_w4", f"{_C1W['T']}日目"),
           ("c1_share", f"{ihalf(q1['share_days_from_d6'] / 10)}割"), ("c1_month", f"100通に{ihalf(D6_MONTH[0])}通"), ("c1_apr", "100通に4通から5通"),
           ("c1_k27", f"100件に{ihalf(100 * P_LATE1)}件"), ("c1_m2", f"{_C1M['T']}日で"),
           ("c1_b2", f"{_C1B['T']}日ちょうど"), ("c2_hit", f"100組に{ihalf(MQ2['六日限v八日限']['river_hit_any'])}組"), ("c2_both", f"100組に{ihalf(MQ2['六日限v八日限']['river_hit_both'])}組"),
           ("c2_clear", f"中央値で{ihalf(PA['clear_median'])}日"), ("c2_ge3", f"100組に{ihalf(GAIN[3]['pct'] + GAIN[4]['pct'])}組"), ("c2_same", f"100組に{ihalf(GAIN[1 - 1]['pct'])}組"),
           ("c2_t2", f"{_P1['T_fast']}日で"), ("c2_b2", f"{_P2['T_fast']}日で"), ("c2_b3", f"{_P2['T_slow']}日かかり"), ("c2_b4", f"{_P2['gain']}日です"), ("c2_w3", f"{_P3['T_slow']}日目"),
           ("c2_w4", f"{_P3['gain']}日です"), ("c2_s2", f"{ihalf(PA['both_median'])}日"), ("c2_s3", f"ふだんの{ihalf(PA['median'])}日"),
           ("c3_med", f"{ihalf(q3['median'])}日"), ("c3_86", f"100人に{ihalf(q3['by_kind'][1]['ge14'])}人"), ("c3_25", f"100人に{ihalf(q3['any_river'])}人"),
           ("c3_9", f"100人に{ihalf(q3['ge21'])}人"), ("c3_2", f"100人に{ihalf(q3['ge28'])}人"), ("c3_m2", f"{_Q3M['T']}日"), ("c3_m3", f"{_Q3M['write']}日"),
           ("c3_m4", f"{_Q3M['T2']}日"), ("c3_m5", f"{_Q3M['reply']}日"), ("c3_b2", f"{_Q3B['T']}日ずつ"), ("c3_b3", f"{_Q3B['reply']}日"), ("c3_w3", f"{_Q3W['T']}日"),
           ("c3_w4", f"{_Q3W['write']}日"), ("c3_w5", f"{_Q3W['T2']}日"), ("c3_ans", f"{ihalf(q3['median'])}日"), ("c4_0", f"100通に{ihalf(q1['on_time'])}通")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    md_ = NARR_PATH.read_text(encoding="utf-8")
    A(f"川止めの幅は札だけ（声に出さない）: 台本は〔 〕だけの行・声の文に「68」「58」が無い・札の数字は data.json の少なめ {ihalf(SCEN_ON['少なめ'])}・多め {ihalf(SCEN_ON['多め'])}",
      f"〔札「川止めが少ない仮定なら100通に{ihalf(SCEN_ON['少なめ'])}通、多い仮定なら{ihalf(SCEN_ON['多め'])}通」を1回だけ出す。声では言わない〕" in md_
      and not any(("68" in tx_ or "58" in tx_ or "68通" in tx_) for _n, tx_ in LINES.values()))
    A(f"川止めの幅の札の場面: {_ts(T_SCEN0)}〜{_ts(T_SCEN1)}（{T_SCEN1 - T_SCEN0:.1f}秒）は声なし・札は文字数÷8＋1秒（{len(SCEN_CARD.replace(chr(10), '')) / 8 + 1:.1f}秒）以上読める",
      T_SCEN1 - T_SCEN0 - 0.3 >= len(SCEN_CARD.replace(chr(10), "")) / 8 + 1 and not any(T_SCEN0 + 0.01 < S(i_) < T_SCEN1 for i_ in LINES))
    A(f"声の「川止めに当たらなかった組のうち、得が3日以上の組は100組に{ihalf(CLEAR_GE3)}組」は、川止めなしの組だけで数えた値 {CLEAR_GE3:.2f}%（1万組全体 {GAIN[3]['pct'] + GAIN[4]['pct']:.2f}%）と同じ",
      f"100組に{ihalf(CLEAR_GE3)}組" in txt("c2_ge3") and "川止めに当たらなかった組のうち" in txt("c2_ge3"))
    A(f"声の「雨の多い季節…100通に4通から5通」: 強調した月 {RAINY}（6日以上遅れ {[round(D6_MONTH[m_ - 1], 2) for m_ in RAINY]}）はどれも四捨五入で4か5・両方出る",
      RAINY and {ihalf(D6_MONTH[m_ - 1]) for m_ in RAINY} == {4, 5} and "4通から5通" in txt("c1_apr"))
    A(f"声の「中央値と同じ6日」は日数の中央値 {ihalf(q1['T_median'])}日・「47日目まで」は返事の最長 {q3['max']}日・「全体では、4人に3人」は 2週間以上 {q3['ge14']:.1f}%",
      f"中央値と同じ{ihalf(q1['T_median'])}日" in txt("c1_m1") and f"{q3['max']}日目まで" in txt("c3_w7") and "4人に3人" in txt("c3_86") and ihalf(q3["ge14"] / 25) == 3)
    A(f"声の「1か月半以上」は最長 {q3['max']}日（45日以上）・「1か月近く」は最長の遅れ {q1['delay_max']}日（28日）", q3["max"] >= 45 and 25 <= q1["delay_max"] <= 30 and "1か月半以上" in txt("c3_w6"))
    # ---- 場面のデータ（モデルと同じ関数・同じ種で取り出したものが data.json と同じ）----
    A(f"1万通の再現: 約束どおり {100 * float((R['delay'] == 0).mean()):.2f}%・日数の中央値 {np.median(R['T']):.0f}・返事の中央値 {np.median(R['reply']):.0f} が data.json と同じ",
      abs(100 * float((R["delay"] == 0).mean()) - q1["on_time"]) < 1e-9 and np.median(R["T"]) == q1["T_median"] and np.median(R["reply"]) == q3["median"])
    A(f"1万マス: 灰色（2週間以上）{N_GRAY:,}／1万 ＝ data.json の {GE14:.2f}%・100×100 ＝ 1万", abs(100 * N_GRAY / N - GE14) < 1e-9 and GRID0.n == N)
    pp = SC_PEOPLE_CHECK
    A(f"人の絵: sims/edo_people.py の draw_townsman（あなた・飛脚・伊勢の人）・身長 {PERSON_H}px ＝ 画面の高さの {PERSON_H / lf.H:.0%}（3分の1 {lf.H / 3:.0f}px 以上）・地図の下の人も 380px",
      pp and PERSON_H >= lf.H / 3 and 380 >= lf.H / 3)
    A(f"暦・棒グラフの値: 雨の日 {len(RAIN)}か月・月ごとの6日以上遅れ {len(D6_MONTH)}か月・得の分布 {len(GAIN)}本・返事の4つの棒 {COUNTS3}（合計 {sum(COUNTS3)}）", len(RAIN) == 12 and len(D6_MONTH) == 12 and sum(COUNTS3) == N)
    A(f"着いた日数の棒 {len(HIST_BINS)}本の合計 {sum(int(T_COUNT[a_:b_ + 1].sum()) for a_, b_ in HIST_BINS):,} ＝ 1万", sum(int(T_COUNT[a_:b_ + 1].sum()) for a_, b_ in HIST_BINS) == N)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件（最も先: {min(r[3] for r in rows_):+.1f}秒）{[b[0] for b in bad[:4]]}", not bad)
    A(f"冒頭の1万マスの枠は、前の文を言い終えてから出て、声の文の頭 {Sk('c0_10k'):.2f}秒までにそろう（{CUE_GRID0.ready:.2f}秒。第0章は間を足さないので 0.5秒前の例外）",
      E(ID["c0_5"] if "c0_5" in ID else "c0_4") - 1e-6 <= T_GRID0 and CUE_GRID0.ready <= Sk("c0_10k") + 1e-6)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    # ---- 映像の切り替わり（2026-10-29 ユーザー指摘）----
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面の切りかえ: 文の途中で場面が替わらない（{mid_sc[:3]}）", not mid_sc)
    A(f"棒グラフ: 棒は 1本ずつ {BAR_STEP}秒おき・着いた日の棒は {HIST_BIN_STEP}秒おき（0.25秒以上）", BAR_STEP >= 0.25 and HIST_BIN_STEP >= 0.25)
    A(f"章カード: 文字数÷8＋1秒 以上出る（{[(c_, round(len(CARD_TITLES[i_].replace(chr(10), '')) / 8 + 1, 1), CARD_HOLD.get(i_, 2.0)) for i_, c_ in enumerate(CARD_TITLES) if i_ > 0]}）",
      all(CARD_HOLD.get(i_, 2.0) >= len(CARD_TITLES[i_].replace("\n", "")) / 8 + 1 for i_ in range(1, len(CARD_TITLES))))
    if frames is not None:
        sp_ = still_spans()
        long_ = [f"{_ts(a_)}〜{_ts(b_)}（{b_ - a_:.1f}秒）" for a_, b_ in sp_ if b_ - a_ > STILL_MAX + 1e-6]
        print(f"  同じ絵の長い区間（字幕なし・0.5秒ごと・{STILL_THR:.1%}以上で動いた）: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:6]))
        A(f"同じ絵は{STILL_MAX:.0f}秒まで（最長 {sp_[0][1] - sp_[0][0]:.1f}秒）: 超える区間 {long_}", not long_)
        allt = [(f[0], e) for f in frames for e in f[1]]

        def _pad_card(fr_):
            cd_ = [e for e in fr_[1] if e[0] in CARD_LINES]
            if not cd_:
                return fr_
            box_ = ("章カード", min(e[1] for e in cd_) - 50, min(e[2] for e in cd_) - 40, max(e[3] for e in cd_) + 50, max(e[4] for e in cd_) + 40, cd_[0][5])
            return (fr_[0], [e for e in fr_[1] if e[0] not in CARD_LINES] + [box_], *fr_[2:])
        pairs = lk.text_box_overlaps([_pad_card(f_) for f_ in frames], skip=[(T_ES, T_ES + 0.6)])
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）。章カードも付せんの下地ごと数えた"])
        for a_, b_, x, y in spans[:12]:
            print(f"  文字の交わり {_ts(a_)}〜{_ts(b_)} 「{x}」と「{y}」")
        A(f"文字の箱の交わり（章カード・字幕・付せん・札・棒の枠・図の文字・全コマ）: {len(spans)} 組・{len(pairs)} コマ（期待 0）", not spans)
        small = lk.min_text_size(frames, 40, exempt=lambda s_: s_ in CARD_LINES or s_.startswith("字幕: "))
        for t_, lab, sz in small[:8]:
            print(f"  40px未満 {_ts(t_)} 「{lab}」 {sz:.0f}px")
        A(f"文字の大きさ: 40px 未満 {len(small)} 種（スマホで読める。幅480pxに縮めても約10px）", not small)
        edge = lk.outside_area(frames, skip=[(T_ES, T_ES + 0.6)])
        for t_, lab, bx in edge[:8]:
            print(f"  画面の端 {_ts(t_)} 「{lab}」 {bx}")
        A(f"画面の端（x 48〜1872・y 36〜1044）に近い文字: {len(edge)} 件", not edge)
        f0 = next(f for f in frames if abs(f[0]) < 1e-6)
        q0 = [e for e in f0[1] if e[0] == QTXT]
        A(f"冒頭: 0秒目に問い「{QTXT}」が {min((e[5] for e in q0), default=0):.0f}px（90px 以上）で出ている・サムネと同じ言葉", len(q0) == 1 and q0[0][5] >= 90)
        A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
        t_big = first_seen(frames, lambda s_, e: s_ == "4人に3人が")
        A(f"画面の「4人に3人が」は声の文の頭 {t_res0:.1f}秒の後（初出 {t_big}秒）・文の終わり {t_res1:.1f}秒より前", t_big is not None and t_res0 <= t_big <= t_res1 + 0.5)
        tokens = [("4人に3人が", "c0_res"), ("100通に64通", "c1_p64"), ("100通に26通", "c1_p26"), ("100通に7通", "c1_p7"), ("100通に3通ほど", "c1_p3"), ("約2.4倍", "c2_price"),
                  ("約2.9倍", "c2_3x"), ("3日以上 100組に20組ほど", "c2_ge3"), ("100組に3組だけ", "c2_same"), ("得 2日", "c2_t3"), ("得 29日", "c2_b4"), ("得 0日", "c2_w4"),
                  ("得の中央値 1日", "c2_s2"), ("100人に86人", "c3_86"), ("100人に25人", "c3_25"), ("100人に9人", "c3_9"), ("100人に2人ほど", "c3_2")]
        for tok, key in tokens:
            ft = first_seen(frames, lambda s_, e, tok=tok: s_ == tok)
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
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて data.json の値（の四捨五入）か、日付・目もり・暦などの閉じた値: 余分 {len(extra)}個 {list(extra)[:5]}", not extra)
        short_t = _check_long_mod().short_texts(frames)
        for a_, b_, s_, need_ in short_t[:14]:
            print(f"  札の表示時間 {_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒／要 {need_:.1f}秒 「{s_[:30]}」")
        A(f"札の表示時間: 画面の文字は「文字数÷8＋1秒」以上出る（字幕・カウンターは除く）: 足りない {len(short_t)} 件", not short_t)
        expo = sorted({e[0] for t_, e in allt if _re.search(r"10\^|\d[eE][+\-]?\d|乗", e[0]) and not e[0].startswith("字幕: ")})
        A(f"指数表記を画面に出さない: {expo}", not expo)

        def has(a_, b_, keys):
            fr = [f for f in frames if a_ <= f[0] < b_]
            miss = [k for k in keys if first_seen(fr, lambda s_, e, k=k: s_ == k) is None]
            return not miss, miss
        okk, miss = has(0, S("ch1"), ["東海道", "大井川", "江戸", "伊勢", "川止め", "あなたの暦", "約束の日", "1マス＝1人", "4人に3人が", "条件", "江戸→伊勢・東海道", "川止めの起きやすさは仮定", "問い1"])
        A(f"0章: 地図・川止めの札・暦・1万マス・結果の札・条件・3つの問いの札が出る（欠け {miss}）", okk)
        okk, miss = has(S("ch1"), S("ch2"), ["問い1", "着いた日ごとの通数", "遅れの分布（1万通）", "約束どおり", "うち10日以上", "ちょうど真ん中", "雨の日の割合（江戸の藩屋敷の日記）", "赤丸＝約束の日",
                                              "手紙の数", "遅れた日数の合計", "川止めが少ない仮定なら100通に68通、", "答え"])
        A(f"1章: 題字・棒グラフ・並べた帯・暦（約束の日）・地図・答えが出る（欠け {miss}）", okk)
        okk, miss = has(S("ch2"), S("ch3"), ["問い2", "急ぎ便の得（1万組）", "100組のうち", "ふだんの得", "待った組の得", "川明け", "着くまでの日数", "料金（八日限を1とした比）", "答え"])
        A(f"2章: 題字・料金の比・100組のマス・得の棒・2通の棒・川明けの図・答えが出る（欠け {miss}）", okk)
        okk, miss = has(S("ch3"), S("ch4"), ["問い3", "往きの手紙", "相手が書く時間", "帰りの手紙", "返事が来るまでの日数（1万人）", "往き", "書く", "帰り", "答え"])
        A(f"3章: 題字・三つを足した帯・返事の日数の棒と100人・暦（往き・書く・帰り）・答えが出る（欠け {miss}）", okk)
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、EC.texts() の文字だけが出ている: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980（のどをまたがない）",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if not e[0].startswith("字幕: ") and (e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936)]
        for t_, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t_)} 「{s_}」")
        A(f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", not out_es)
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        A(f"終了画面: 登録のお願い（{Sk('c4_sub'):.1f}秒〜）の{Sk('c4_sub') - T_ES:.1f}秒前から最後まで（{DUR - T_ES:.1f}秒・YouTube の終了画面は最低5秒なので6〜8秒）。締めの問い・注意書きの文は、その前に言い終わる",
          0.2 <= Sk("c4_sub") - T_ES <= 1.0 and 6.0 <= DUR - T_ES <= 8.0 and T_ES > E(ID["c4_3"]) - 1e-6)
        pre = [e[0] for f in frames if Sk("c4_2") <= f[0] < T_ES for e in f[1]]
        A("まとめ: 締めの問い「あなたなら、返事を何日、待てますか？」と注意書きの札が、終了画面の前に読める",
          all(x in pre for x in ("あなたなら、", "返事を何日、待てますか？", "数字は、この動画の仮定で計算した結果。", "実際の飛脚の遅れを、言い当てるものではない")))
        end_t = min(DUR - 0.2, Sk("c4_sub", 0.0) + 1.5)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A(f"終了画面に 答え3つ（{[r[1] for r in end_rows()]}）・登録の付せんが出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
    return len(flat)


SC_PEOPLE_CHECK = hasattr(edo_people, "draw_townsman") and callable(edo_people.draw_townsman)


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
    if not any(a in args for a in ("--anchors", "--readings", "--wraps", "--scenecheck", "--stills", "--preview", "--docs", "--lines")) and FAKE:
        print(__doc__)
        return
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    if "--anchors" in args or "--lines" in args:
        for k_ in ID:
            print(k_, f"{Sk(k_):.1f}-{Ek(k_):.1f}")
        for g_ in sorted(GAP_NOTE):
            print(g_, f"{S(g_):.1f}-{E(g_):.1f}")
        for nm_, t0_, t1_, *_r in SCENES:
            print(f"場面 {nm_}: {t0_:.1f}-{t1_:.1f}（{t1_ - t0_:.1f}秒）")
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
                (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))      # 本番の声の文字の箱（check-long の札の表示時間の点検が読む）
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, WORK / f"at_{tt:06.1f}.png")
                print("  ", WORK / f"at_{tt:06.1f}.png")
        else:
            stills_preview()
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
    (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))              # 本番の声の文字の箱（check-long の札の表示時間の点検が読む）
    scene_checks(frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
