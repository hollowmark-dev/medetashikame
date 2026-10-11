"""平均10分おきのバスで、なぜ平均10分も待つのか【1万人で確かめた】（横型ロング）。

台本: publish/bus-matsu-long/script.md（v2）。このファイルは公開日まで非公開（答えが書いてある）。
この部分はモデル（数字の計算・種の選び方・照合・アニメ用のデータ）。場面（描画）は同じファイルに後から足す。

モデル
1. バスの間隔: 平均 MU 分、乱れ（標準偏差）SD 分。SD=0 なら時刻表どおり（一定）、SD=MU ならでたらめ（指数分布）、
   その間はガンマ分布（平均 MU、標準偏差 SD）。人はでたらめな時刻（一様）にバス停へ着き、次のバスまで待つ。
2. 直感の外れ: 「平均10分おきなら、待つのはその半分の5分」。正解は、間隔がでたらめなら平均10分。
   理由は、長いすき間ほど、そこに着く人が多く（すき間の長さに比例）、しかも長く待つから。
   平均の待ち ＝ E[L²]/(2E[L]) ＝ (MU² ＋ SD²)/(2 MU) ＝ 5 ×（1 ＋（SD/MU）²）。
   人が落ちたすき間の平均 ＝ E[L²]/E[L] ＝ 2 MU ＝ 20分（待つ人から見たすき間）。待ちはその半分の10分。
3. 団子運転: 環状の路線（S 停留所・NB 台）。各停留所に毎分 LAM 人がやって来て、バスが来ると前のバスからの経過時間に
   比例した人数が並んでいる。乗る人数に比例して停車が延びる（1人 BOARD 分）→ 遅れたバスはさらに遅れ、後ろのバスは追いつく。
   時間調整: 決まった停留所に、予定より早く着いたら予定の時刻まで待つ（一周に6分のゆとりを持たせる）。
   平均の待ち ＝（間隔の2乗の合計）÷ 2 ÷（間隔の合計）。停留所ごとの「前のバスからの間隔」から数える。

台本の章と、ここで作るもの（数字は台本の「数字の根拠」と同じ）
0章: でたらめな間隔のバスと、でたらめな時刻に来た1人。ちょうど14分待つ見本（SEED_ONE）
2章: 1万人（N）が T_ALL 分の間に着く（SEED_MAIN）。1万人の平均の待ち 10.0 ／ バスの間隔の平均 10.0 ／ 人が落ちたすき間の平均 20.0
     別の日の3本（SEED_DAYS）: 9.8 ／ 10.1 ／ 10.0
3章: Aさん（長さ24分前後のすき間に着いて18分前後待った人）と、2つのすき間（2分と18分）の例 8.2
4-1: 同じ1万人で、時刻表どおり（10分ぴったり）なら 5.0
4-2: 乱れ SD ＝ 0, 2, 4, 6, 8, 10 → 5.0 ／ 5.2 ／ 5.8 ／ 6.8 ／ 8.2 ／ 10.0（各100万人）
4-3・5章: 団子運転（時間調整なし）と時間調整あり。6台は時間できっちり10分おきに出す（START_EVEN）。200回の平均で、
     1時間ごとの平均の待ち。なし: 5.1（1時間目）→ 7.1 → 10.1 → 12.8（4時間目）→ … → 26.4（10時間目）。あり: 4.8〜4.9 のまま（10時間目 4.85）。
     台本 v3 は「はじめの5分ほど → 13分ほど」「あり: 10時間たっても5分ほど」。
     画面で見せる1回ぶん（SEED_OFF: 1時間目4.9・4時間目13.9、SEED_ON: 4.8〜4.9）。後ろのバスは前のバスを追い越さない（2026-10-04）。
     アニメ用: bus_angles(log, t)、wait_now(log, t)
"""
import heapq
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers
from engine.parts import r1

# ============================================================
# 数字を変えると、あなたの路線に近づく（動画の6章）
# ============================================================
MU = 10.0           # バスの間隔の平均（分）
SD = 10.0           # 間隔の乱れ（分）。0 なら時刻表どおり、MU と同じなら完全にでたらめ（指数分布）
N = 10000           # バス停に着く人の数
T_ALL = 600.0       # その人たちが着く時間帯（分）

# 団子運転（環状の路線）
STOPS = 20          # 停留所の数
BUSES = 6           # バスの台数
LAM = 0.5           # 1つの停留所に1分あたりにやって来る人数（人／分）
BOARD = 0.055       # 1人が乗るのにかかる時間（分）。3.3秒（追い越しなしの規則を入れたので 0.08 から下げた。2026-10-04）
NOISE = 0.15        # 走行時間のゆらぎ（±15%）
CYCLE = 60.0        # 時刻表で一周にかかる時間（分）。6台なら10分おき
RUN_OFF = 2.6       # 次の停留所までの走行時間（分）。時間調整なしのとき（乗車0.4分を足して3.0分 ＝ 一周60分）
RUN_ON = 2.3        # 同。時間調整ありのとき（一周に6分のゆとり）
HOLD_STOPS = (0, 5, 10, 15)   # 予定より早く着いたら待つ停留所（時間調整）
T_END = 600         # 団子運転の長さ（分 ＝ 10時間）
START_EVEN = True   # 6台を時間できっちり10分おきに出す（False なら、停留所0・3・6・10・13・16 から出す旧設定。間隔は 9・9・12 分）

# ============================================================
# 画面に出す数字（照合の相手）。台本 script.md の「数字の根拠」と同じ
# ============================================================
ONE_WAIT = 14.0                       # 0章の1人が待つ分
SHOW_MAIN = (10.0, 10.0, 20.0)        # 1万人の平均の待ち／バスの間隔の平均／人が落ちたすき間の平均
SHOW_DAYS = (9.8, 10.1, 10.0)         # 別の日の3本の「1万人の平均の待ち」
SHOW_SCHED = 5.0                      # 時刻表どおり
SD_LIST = (0, 2, 4, 6, 8, 10)         # 4-2 の乱れ（分）
SHOW_SD = (5.0, 5.2, 5.8, 6.8, 8.2, 10.0)
GAP_SHORT, GAP_LONG = 2.0, 18.0       # 3章の2つのすき間（分）
SHOW_EXAMPLE = 8.2                    # (2×1 ＋ 18×9) ÷ 20
SHOW_OFF = (4.9, 13.0, 48.6)          # 団子運転（なし）200回平均の、1時間目・4時間目・10時間目（台本 v3: 「5分ほど」「13分ほど」）
SHOW_ON_10H = 5.0                     # 時間調整あり・10時間目は「5分ほど」（4.5〜5.5 に入ればよい。実測 4.85）
SCREEN_OFF_H1 = 4.9                   # 画面の「なし」の1回の1時間目（小数1桁）
RUNS = 200                            # 団子運転の平均をとる回数

# ============================================================
# 選んだ種（探し方は下の find_* と --search。条件を満たす最初の種）
# ============================================================
SEED_ONE = 1739        # 0章の1人
SEED_MAIN = 25263        # 2章の1万人
SEED_DAYS = (5005, 5024, 5055)  # 2章の別の日の3本
SEED_OFF = 2265       # 団子運転・時間調整なしの回
SEED_ON = 2232        # 団子運転・時間調整ありの回

ROW_MIN = 100         # 場面で時間の帯を何分ずつ折り返すか（Aさんの居るすき間が折り返しをまたがないように）


# ============================================================
# 1. バスの間隔と待ち時間
# ============================================================
def draw_gaps(r, n, mu=MU, sd=SD):
    """バスの間隔を n 個。sd=0 は一定、sd=mu は指数分布、その間はガンマ分布（平均 mu、標準偏差 sd）"""
    if sd <= 0:
        return np.full(n, float(mu))
    if abs(sd - mu) < 1e-9:
        return r.exponential(mu, n)
    return r.gamma((mu / sd) ** 2, sd * sd / mu, n)


def theory_wait(mu=MU, sd=SD):
    """平均の待ち ＝ (mu² ＋ sd²) / (2 mu) ＝ mu/2 ×（1 ＋（sd/mu）²）"""
    return (mu * mu + sd * sd) / (2 * mu)


def bus_times(r, t_all=T_ALL, mu=MU, sd=SD, start=0.0):
    """0 分から、最後のバスが t_all 以降になるまでのバスの時刻"""
    n = int(t_all / mu * 2) + 50
    bus = start + np.concatenate([[0.0], np.cumsum(draw_gaps(r, n, mu, sd))])
    assert bus[-1] > t_all
    return bus[:np.searchsorted(bus, t_all) + 1]


# ---------- 0章: でたらめな時刻に来た1人 ----------
def one_person(seed):
    """バスの時刻と、でたらめな時刻に来た1人。→ (バスの時刻, 着いた時刻, 待ち, 直前のバス, 次のバス)"""
    r = np.random.default_rng(seed)
    bus = bus_times(r, 150.0)
    arr = float(r.uniform(15, 45))
    k = int(np.searchsorted(bus, arr, side="right"))
    return bus, arr, float(bus[k] - arr), float(bus[k - 1]), float(bus[k])


def ok_one(seed):
    bus, arr, wait, prev, nxt = one_person(seed)
    gaps = np.diff(bus[bus <= nxt + 1e-9])
    # 14.0±0.2 分待つ（台本は14.0±0.4でよい）。その人が落ちたすき間は18〜24分（「20分来ないこともある」）。それ以前に2分台の短いすき間がある
    return (abs(wait - ONE_WAIT) <= 0.2 and 18 <= nxt - prev <= 24 and prev - bus[0] > 5
            and gaps[:-1].min() <= 3.5)


def find_one(start=1):
    return next(s for s in range(start, 200000) if ok_one(s))


# ---------- 2章: 1万人 ----------
def crowd(seed, n=N, t_all=T_ALL):
    """1万人の見本。→ (バスの時刻, 着いた時刻, 待ち, 次のバスの番号)"""
    r = np.random.default_rng(seed)
    bus = bus_times(r, t_all)
    arr = r.uniform(0, t_all, n)
    k = np.searchsorted(bus, arr, side="right")
    return bus, arr, bus[k] - arr, k


def pick_a(bus, arr, wait, k):
    """3章の Aさん: 長さ23〜25分のすき間に着いて17.5〜18.5分待った人（すき間の折り返しをまたがない）。
    条件を満たす人のうち、すき間24分・待ち18分にいちばん近い人。なければ None"""
    glen = bus[k] - bus[k - 1]
    m = ((glen >= 23) & (glen <= 25) & (wait >= 17.5) & (wait <= 18.5)
         & (np.floor(bus[k - 1] / ROW_MIN) == np.floor((bus[k] - 1e-9) / ROW_MIN)))
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return None
    return int(idx[np.argmin((glen[idx] - 24) ** 2 + (wait[idx] - 18) ** 2)])


def sched_wait(arr, mu=MU):
    """同じ人たちが、時刻表どおり（mu 分ぴったり）のバスに乗るなら"""
    return mu - np.mod(arr, mu)


def ok_main(seed):
    bus, arr, wait, k = crowd(seed)
    glen = bus[k] - bus[k - 1]
    return (r1(wait.mean()) == SHOW_MAIN[0] and r1(np.diff(bus).mean()) == SHOW_MAIN[1]
            and r1(glen.mean()) == SHOW_MAIN[2] and r1(sched_wait(arr).mean()) == SHOW_SCHED
            and pick_a(bus, arr, wait, k) is not None)


def find_main(start=1):
    return next(s for s in range(start, 500000) if ok_main(s))


def find_days(start=5000):
    """別の日の3本: 1万人の平均の待ちが、画面の値（SHOW_DAYS）になる最初の種"""
    out = []
    for target in SHOW_DAYS:
        s = start
        while True:
            s += 1
            if s != SEED_MAIN and s not in out and r1(crowd(s)[2].mean()) == target:
                break
        out.append(s)
    return tuple(out)


# ---------- 4-2: 乱れを変えて、各100万人 ----------
def mean_wait_big(sd, seed=1, n_people=1_000_000, n_gaps=2_000_000, mu=MU):
    """間隔の乱れ sd で、100万人の平均の待ち。→ (平均の待ち, 人が落ちたすき間の平均)"""
    r = np.random.default_rng(seed)
    bus = np.concatenate([[0.0], np.cumsum(draw_gaps(r, n_gaps, mu, sd))])
    arr = r.uniform(0, bus[-1] * 0.99, n_people)
    k = np.searchsorted(bus, arr, side="right")
    return float((bus[k] - arr).mean()), float((bus[k] - bus[k - 1]).mean())


# ============================================================
# 4-3・5章: 団子運転（環状の路線）
# ============================================================
# ログの列（1行 ＝ 1台が1つの停留所に着いたとき）
C_T, C_K, C_S, C_GAP, C_N, C_DEP, C_ARR = range(7)
#   C_T   乗り降りを始める時刻（分）。時間調整で待ったあとの時刻（間隔の計算の基準）
#   C_K   バスの番号（0〜BUSES-1）
#   C_S   停留所の番号（0〜STOPS-1）
#   C_GAP 前のバスが出てからの間隔（分）。待つ人から見た「すき間」
#   C_N   そのとき乗った人数
#   C_DEP 発車時刻（分）。C_ARR から C_DEP までは停車（時間調整の待ちと乗車）
#   C_ARR 停留所に着いた時刻（分）
OVERTAKE_GAP = 0.05   # 後ろのバスは、前のバスより（出発も到着も）これだけ後（分）。追い越しを防ぐ
NO_OVERTAKE = True    # 後ろのバスは前のバスを追い越さない（出発も到着も前のバスより後）。BOARD=0.08 のままだと200回平均の4時間目が18.7分になり「13分ほど」を外れたので BOARD を下げた
_LOG_EXTRA = 30.0     # アニメ用に、T_END のあと30分ぶんも持つ（集計は C_ARR <= T_END の行だけ）


def sim(seed, run=RUN_OFF, t_end=T_END, sched=False, ctrl=HOLD_STOPS):
    """団子運転1回。→ ログ（行 ＝ 1台が1停留所に着いたとき、列は C_*）"""
    r = np.random.default_rng(seed)
    h = CYCLE / BUSES
    step = CYCLE / STOPS
    q, prev = [], {}
    if START_EVEN:
        for k in range(BUSES):                          # 6台を、路線上の位置 k×STOPS/BUSES（時間できっちり10分おき）から出す
            s0 = -(-k * STOPS // BUSES)                 # 最初に着く停留所（位置の次の停留所）
            t0 = (s0 * BUSES - k * STOPS) / BUSES * step    # そこに着く時刻（予定の時刻でもある）
            heapq.heappush(q, (t0, k, s0 % STOPS, t0))
        for s in range(STOPS):                          # 各停留所の「前のバスが出た時刻」の初期値（等間隔の運行と合わせる）
            prev[s] = (s * step) % h - h
    else:
        for k in range(BUSES):                          # 旧設定: 停留所から同時に出す（予定の時刻 0）
            heapq.heappush(q, (0.0, k, (k * STOPS // BUSES) % STOPS, 0.0))
        for s in range(STOPS):
            d = min((s - (k * STOPS // BUSES)) % STOPS for k in range(BUSES)) * step
            prev[s] = d - h
    last_arr = {s: prev[s] - 0.1 for s in range(STOPS)}   # 各停留所に最後に着く（予定の）バスの時刻。追い越さないための基準
    log = []
    while q:
        t, k, s, ts = heapq.heappop(q)
        if t > t_end + _LOG_EXTRA:
            break
        arrive = t
        if sched and s in ctrl and t < ts:
            t = ts                                      # 予定より早ければ、予定の時刻まで待つ（時間調整）
        if NO_OVERTAKE:
            t = max(t, prev[s] + OVERTAKE_GAP)          # 前のバスが出るまで乗り降りを始めない（先に出発して追い越さない）
        gap = max(t - prev[s], 0.0)
        n = r.poisson(LAM * gap)
        dep = t + n * BOARD
        prev[s] = dep
        log.append((t, k, s, gap, n, dep, arrive))
        move = run * (1 + NOISE * r.standard_normal())
        s2 = (s + 1) % STOPS
        nxt = dep + max(move, 0.3)
        if NO_OVERTAKE:
            nxt = max(nxt, last_arr[s2] + OVERTAKE_GAP)     # 次の停留所に、前のバスより先に着かない
            last_arr[s2] = nxt
        heapq.heappush(q, (nxt, k, s2, ts + step))
    return np.array(log)


def overtakes(log, dt=0.1, t1=None):
    """追い越しの回数（6台の並び順が変わった時刻の数）。バスの位置は bus_angles と同じ折れ線（周回しても戻らない角度）で調べる"""
    knots = _prep(log)["knots"]
    t1 = T_END if t1 is None else t1
    tg = np.arange(0.0, t1, dt)
    u = np.array([np.interp(tg, tt, aa) for tt, aa in knots])        # BUSES × 時刻
    d = np.vstack([u[1:] - u[:-1], (u[0] + 2 * math.pi - u[-1])[None, :]])   # 前のバスとの距離（バス k+1 が k の前、0 が 5 の前）
    return int((d < -1e-9).any(axis=0).sum())



def wait_by_hour(log, hours=T_END // 60):
    """1時間ごとの、平均の待ち（その時間に停留所で見えたすき間 g から ΣG²/2 ÷ Σg）"""
    log = log[log[:, C_ARR] <= T_END]
    out = []
    for h in range(hours):
        m = (log[:, C_T] >= h * 60) & (log[:, C_T] < (h + 1) * 60)
        g = log[m, C_GAP]
        out.append(float((g ** 2).sum() / 2 / g.sum()))
    return out


def bunch_hours(runs=RUNS):
    """RUNS 回の平均。→ (時間調整なし, あり) それぞれ長さ10の配列（1〜10時間目）"""
    off = np.array([wait_by_hour(sim(s, RUN_OFF)) for s in range(runs)]).mean(0)
    on = np.array([wait_by_hour(sim(s, RUN_ON, sched=True)) for s in range(runs)]).mean(0)
    return off, on


# ---------- アニメ用 ----------
_CACHE = {}


def _prep(log):
    """ログごとに1回だけ作る補助（時刻順の並び・累積和・バスごとの位置の折れ線）"""
    c = _CACHE.get(id(log))
    if c is not None and c["log"] is log:
        return c
    order = np.argsort(log[:, C_T], kind="stable")
    g = log[order, C_GAP]
    knots = []
    for k in range(BUSES):
        rows = log[log[:, C_K] == k]
        rows = rows[np.argsort(rows[:, C_ARR], kind="stable")]
        n = len(rows)
        tt = np.empty(2 * n)
        aa = np.empty(2 * n)
        tt[0::2], tt[1::2] = rows[:, C_ARR], rows[:, C_DEP]          # 着く → 発つ（間は停車）
        ang = 2 * math.pi * (rows[0, C_S] + np.arange(n)) / STOPS    # 周回しても戻らない角度（あとで 2π で割る）
        aa[0::2] = aa[1::2] = ang
        if tt[0] > 0:                                                # 最初の停留所の手前（t=0 では位置 k×STOPS/BUSES）
            tt = np.concatenate([[0.0], tt])
            aa = np.concatenate([[2 * math.pi * k / BUSES], aa])
        knots.append((tt, aa))
    c = {"log": log, "t": log[order, C_T], "cg": np.concatenate([[0.0], np.cumsum(g)]),
         "cg2": np.concatenate([[0.0], np.cumsum(g * g)]), "knots": knots}
    _CACHE[id(log)] = c
    return c


def bus_angles(log, t):
    """時刻 t（分）での、バスの位置。→ 長さ BUSES の配列（0〜2π の角度、停留所 s は 2π s/STOPS）。
    停留所の間は直線で補間、停車中（時間調整・乗車）は止まる"""
    knots = _prep(log)["knots"]
    return np.fromiter((np.interp(t, tt, aa) for tt, aa in knots), float, BUSES) % (2 * math.pi)


def wait_now(log, t, window=60.0):
    """直近 window 分の、平均の待ち（分）。画面のカウンター用。t が小さいうちは 0 分からの分"""
    c = _prep(log)
    hi = int(np.searchsorted(c["t"], t, side="right"))
    lo = int(np.searchsorted(c["t"], t - window, side="right"))
    if hi - lo < 1:
        hi = min(lo + 1, len(c["t"]))
        lo = max(hi - 1, 0)
    sg = c["cg"][hi] - c["cg"][lo]
    return float((c["cg2"][hi] - c["cg2"][lo]) / 2 / sg) if sg > 0 else 0.0


def bus_groups(angles, thr_stops=1.6):
    """バスの固まり。thr_stops 停留所ぶん未満しか離れていないバスを1つの固まりとして、台数を大きい順に返す"""
    a = np.sort(np.asarray(angles))
    d = np.diff(np.concatenate([a, [a[0] + 2 * math.pi]]))
    br = np.flatnonzero(d >= 2 * math.pi / STOPS * thr_stops)
    if len(br) == 0:
        return [len(a)]
    return sorted(np.diff(np.concatenate([br, [br[0] + len(a)]])).tolist(), reverse=True)


def spacing_dev(log, t0=60, t1=T_END, dt=5):
    """バスの間隔（分）が、等間隔（CYCLE/BUSES 分）から外れる最大の分（t0〜t1 を dt 分刻みで見た）"""
    dev = 0.0
    for t in np.arange(t0, t1, dt):
        a = np.sort(bus_angles(log, t))
        d = np.diff(np.concatenate([a, [a[0] + 2 * math.pi]])) * CYCLE / (2 * math.pi)
        dev = max(dev, float(np.abs(d - CYCLE / BUSES).max()))
    return dev


def ok_off(seed):
    """画面の「なし」の回: 1時間目が5.3、4時間目が13.3以上（〜14.6）、3〜4時間後に6台が 3台・2台・1台 の固まり"""
    log = sim(seed, RUN_OFF)
    wh = wait_by_hour(log)
    if not (r1(wh[0]) == SCREEN_OFF_H1 and 13.3 <= wh[3] < 14.6 and wh[1] > wh[0] and wh[2] > wh[1] - 0.5):
        return False
    gs = [bus_groups(bus_angles(log, t)) for t in (180, 210, 240)]
    return all(len(g) <= 3 for g in gs) and all(3 in g and 2 in g for g in gs[1:])


def ok_on(seed):
    """画面の「あり」の回: 10時間ずっと平均の待ちが 4.75〜5.0 分（等間隔の運行だと 4.85 前後で一定）"""
    log = sim(seed, RUN_ON, sched=True)
    wh = np.array(wait_by_hour(log))
    return wh.min() > 4.75 and wh.max() < 5.0


def find_off(start=1000):
    return next(s for s in range(start, 200000) if ok_off(s))


def find_on(start=1000):
    """間隔の外れが最小の回を、start から 2500 個のなかから選ぶ"""
    best = min((spacing_dev(sim(s, RUN_ON, sched=True)), s) for s in range(start, start + 2500) if ok_on(s))
    return best[1]


if __name__ == "__main__" and "--search" in sys.argv:
    print("種の探し直し（MU・SD などを変えたあとに使う）")
    print(" SEED_ONE =", find_one())
    print(" SEED_MAIN =", find_main())
    print(" SEED_DAYS =", find_days())
    print(" SEED_OFF =", find_off())
    print(" SEED_ON =", find_on())
    raise SystemExit

# ============================================================
# 画面で使うデータ（import すると作られる。重いのは 1万人の1回ぶんだけ）
# ============================================================
BUS0, ARR0, WAIT0, PREV0, NEXT0 = one_person(SEED_ONE)
BUS, ARR, WAIT, KNEXT = crowd(SEED_MAIN)
GAPS = np.diff(BUS)
GAP_OF = BUS[KNEXT] - BUS[KNEXT - 1]                    # 各人が落ちたすき間の長さ
SCHED_WAIT = sched_wait(ARR)                            # 時刻表どおりなら
ORDER = np.random.default_rng(SEED_MAIN + 5).permutation(N)   # 1万人が画面に現れる順
A_I = pick_a(BUS, ARR, WAIT, KNEXT)                     # Aさん（0〜N-1 の番号）
A_ARR, A_WAIT, A_GAP = float(ARR[A_I]), float(WAIT[A_I]), float(GAP_OF[A_I])
A_PREV, A_NEXT = float(BUS[KNEXT[A_I] - 1]), float(BUS[KNEXT[A_I]])
DAYS = [crowd(s) for s in SEED_DAYS]                    # 別の日の3本（それぞれ BUS, ARR, WAIT, KNEXT）
LOG_OFF = sim(SEED_OFF, RUN_OFF)                        # 画面の団子運転（時間調整なし）
LOG_ON = sim(SEED_ON, RUN_ON, sched=True)               # 画面の団子運転（時間調整あり）


# ============================================================
# 場面（描画）は、この下に足す
# ============================================================

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, shimmer, text,
                         text_width, thump, tick, whoosh, riser, beat)
from engine.note import INK, PENCIL, RED, MARKER, PAPER, pen_circle, pen_line, sticky

lf.use()
SLUG = "bus-matsu-long"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
VOICE_DIR = OUT / "voice"
COLD, HOT = "#5aa0d8", RED                          # 待ちが短い／長い（ショートと同じ）
LX0_, LY0_, LX1_, LY1_ = lf.LEFT                    # 左ページの箱
RX0_, RY0_, RX1_, RY1_ = lf.RIGHT                   # 右ページの箱


# ============================================================
# 台本 → 時間割（ナレーションの文言は publish/bus-matsu-long/script.md v3 のまま）
# ============================================================
CH_TITLES = ["バス停で何分待つ？", "1万人で確かめる", "長く待った人に寄る", "では、時刻表どおりなら？",
             "では、少しだけ乱れたら？", "では、時刻表どおりに出発したら？", "時間調整", "実際のバスでは？", "まとめ"]
(CH_STOP, CH_CROWD, CH_ONE, CH_SCHED, CH_NOISE, CH_BUNCH, CH_FIX, CH_REAL, CH_END) = range(9)


SPEED = 1.0   # 声の速さ。2026-10-04 既定の1.05だと1秒に6.6字で、数字の多い説明には少し速いので落とした


def _items():
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        L("c0_1", "バス停に、1人の人がやってきました。この人は、何分待つことになるでしょう。"),
        L("c0_2", "このバス停には、平均すると10分おきにバスが来ます。"),
        L("c0_3", "ただし、間隔はバラバラです。2分で次が来ることもあれば、20分来ないこともあります。"),
        L("c0_4", "この人は時刻表を見ずに、でたらめな時刻に来ました。"),
        L("c0_5", "時計を進めてみます。", pause=1.4),
        L("c0_6", "14分。少し運が悪かったのかもしれません。", pause=0.7),
        L("c1_1", "では、たくさんの人が同じように来たら、平均で何分待つのでしょう。"),
        L("c1_2", "ふつうに考えると、こうなりそうです。"),
        L("c1_3", "バスとバスの間は、平均10分。その間のどこかに着くのだから、待つのは平均してその半分。"),
        L("c1_4", "つまり、5分。", pause=0.8),
        L("c1_5", "確かめてみます。", pause=0.6),
        C(CH_TITLES[1], id="ch1", gap=2.7),
        L("c2_1", "このバス停を、10時間見てみます。その間に、1万人が、時刻表を見ずに、思い思いの時刻にやって来ます。", pause=0.3),
        L("c2_1b", "まずは最初の1時間だけ。1人を1つの点で描き、点から次のバスまでの線を、その人の待ち時間とします。", pause=0.3),
        L("c2_1c", "バスが行ったすぐ後に着いた人ほど、長く待ちます。長く待った人ほど、赤い点にしています。", pause=0.3),
        L("c2_1d", "これを10時間ぶん、1万人まで続けます。", pause=0.2),
        G("g2", 10.0),
        L("c2_2", "1万人の平均の待ち時間は、10.0分。"),
        L("c2_3", "5分ではなく、バスの間隔と同じ、10分でした。", pause=0.5),
        L("c2_4", "別の日のバス停でも、試してみます。", pause=0.5),
        L("c2_5", "どの日も、ほぼ10分です。", pause=0.9),
        C(CH_TITLES[2], id="ch2", gap=1.6),
        L("c3_1", "この人を見てみます。この人は18分待ちました。"),
        L("c3_2", "着いたのは、25分近くもバスが来なかった、長いすき間の中でした。"),
        L("c3_3", "ここにヒントがあります。", pause=0.6),
        L("c3_4", "話を簡単にして、すき間が2分と18分の、2種類だけだとします。平均はちょうど10分です。"),
        L("c3_5", "18分のほうが9倍長いので、そのすき間の中に来てしまう人も、9倍多くなります。"),
        L("c3_6", "しかも、長いすき間の中に来た人は平均9分、短いほうは平均1分待ちます。"),
        L("c3_7", "人数で平均すると、8.2分。", pause=0.6),
        L("c3_7b", "すき間の長さがもっとバラバラなら、この数字はさらに大きくなります。", pause=0.6),
        L("c3_8", "長いすき間は、たくさんの人を集めて、しかも長く待たせるのです。"),
        L("c3_9", "1万人の場合も見てみます。1人1人が来たときのすき間の長さを平均すると、20分でした。"),
        L("c3_10", "バスの間隔は平均10分。でも、待つ人から見たすき間は、平均20分。"),
        L("c3_11", "その半分の10分を待つことになります。"),
        L("c3_12", "平均の間隔と同じだけ待たされる。これは「待ち時間のパラドックス」と呼ばれています。", pause=0.8),
        C(CH_TITLES[3], id="ch3", gap=1.6),
        L("c4a_1", "では、バスが時刻表どおり、きっちり10分おきに来たら？"),
        L("c4a_2", "平均は5.0分。今度はちゃんと半分になりました。"),
        L("c4a_3", "半分になるのは、すき間がそろっているときだけだったのです。", pause=0.6),
        C(CH_TITLES[4], id="ch4", gap=1.6),
        L("c4b_1", "現実のバスは、きっちりでも、でたらめでもありません。その中間です。"),
        L("c4b_2", "乱れの大きさを、少しずつ変えてみます。"),
        L("c4b_3", "間隔が前後に2分ほどばらつくなら、5.2分。4分なら、5.8分。"),
        L("c4b_4", "乱れが大きくなるほど、待ち時間の伸び方も大きくなっていきます。", pause=0.3),
        G("g4b", 3.6),
        C(CH_TITLES[5], id="ch5", gap=1.6),
        L("c4c_1", "では、時刻表どおりに出発したバスは、ずっと時刻表どおりでいられるでしょうか。"),
        L("c4c_2", "20の停留所をぐるっと回る路線に、6台のバスを、きっちり10分おきに出してみます。"),
        L("c4c_3", "ルールを1つだけ足します。待っている人が多いほど、乗るのに時間がかかる。"),
        L("c4c_4", "1台が少し遅れると、前のバスから時間が空くので、次の停留所には人が多くたまっています。"),
        L("c4c_5", "乗る人が多いので、さらに遅れます。"),
        L("c4c_6", "後ろのバスは、乗る人が少ないので、どんどん追いついていきます。", pause=0.5),
        G("g4c", 22.0),
        L("c4c_7", "3時間後。6台のバスは、2台、3台と固まって走るようになりました。"),
        L("c4c_8", "平均の待ち時間は、はじめの5分ほどから、13分ほどまで伸びました。"),
        L("c4c_9", "誰も悪くないのに、バスはひとりでに固まってしまうのです。これは「団子運転」と呼ばれています。", pause=0.6),
        C(CH_TITLES[6], id="ch6", gap=1.6),
        L("c5_1", "では、団子運転は防げないのでしょうか。"),
        L("c5_2", "バスに乗っていて、こんな放送を聞いたことはありませんか。「時間調整のため、しばらく停車します」。"),
        L("c5_3", "予定より早く着いたら、決まった停留所で待つ。それだけです。"),
        L("c5_4", "時刻表を少しゆるめに作って、早く着いたバスを待たせると、10時間たっても、平均の待ち時間は5分ほどのままでした。",
          pause=0.3),
        G("g5", 7.0),
        L("c5_5", "あの時間調整は、バスとバスの間をそろえるための待ち時間だったのです。", pause=0.6),
        C(CH_TITLES[7], id="ch7", gap=1.6),
        L("c6_1", "最初に見た、でたらめに来るバス停は、いちばん単純な形です。"),
        L("c6_2a", "実際のバスは時刻表に沿って走りますし、時刻表を見てから家を出る人もいます。", pause=0.25),
        L("c6_2b", "そういう人の待ち時間は、もっと短くなります。", pause=0.6),
        C(CH_TITLES[8], id="ch8", gap=1.6),
        L("c7_1", "自分が待つときに限って、バスが来ない。"),
        L("c7_2", "そう感じるのは、バスがなかなか来ない長い時間ほど、そこに着いてしまう人が多いからでした。"),
        L("c7_2b", "あなたも、その1人になりやすいのです。"),
        L("c7_3", "あなたの使うバスでは、時間調整、ありますか？", pause=0.5),
        L("c7_4", "このチャンネルでは、こんなふうにシミュレーションで確かめる動画を上げていきます。", pause=0.3),   # 字幕が2行に収まるよう、2文に分けた（文言は同じ）
        L("c7_5", "よければ、チャンネル登録と高評価をお願いします。", pause=0.0),
        G("g_end", 2.0),   # 登録・高評価のお願いを言い終わってから約2秒で終わる（2026-10-04 ユーザー指示。終了画面の要素は重ねない）
    ]


def _timeline():
    try:
        return lf.Timeline(_items(), VOICE_DIR)
    except SystemExit:
        raise


tl = _timeline()
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


# ============================================================
# 小さな道具
# ============================================================
def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    """t0 から d 秒でふわっと 0→1"""
    return ease_out(clamp01((t - t0) / d))


def prog(t, t0, s, cps=9.0):
    """t0 から s を書き進む進み具合（0→1）"""
    return clamp01((t - t0) / lf.write_dur(s, cps))


def wr(ctx, s, x, y, size, color, t0, t, cps=9.0, align="left", alpha=1.0):
    """t0 から手書きで書き進む文字（書き終わったらそのまま残る）"""
    lf.write_on(ctx, s, x, y, size, color, prog(t, t0, s, cps), align=align, alpha=alpha)


def grp(ctx, a, fn, *args):
    """fn(ctx, *args) をまとめて濃さ a で描く"""
    if a <= 0.003:
        return
    if a >= 0.997:
        fn(ctx, *args)
        return
    ctx.push_group()
    fn(ctx, *args)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def fit(s, size, maxw, bold=True):
    """maxw に収まるように大きさを縮める（26 未満にはしない）"""
    w = text_width(s, size, bold)
    return size if w <= maxw else max(26.0, size * maxw / w)


def clock_str(m):
    return f"{int(m // 60)}:{int(m % 60):02d}"


def legend_at(ctx, items, cx, y, size=28, gap=44, alpha=1.0):
    """色の見本と説明を cx を中心に並べる。items = [(色, 説明)]"""
    ws = [44 + text_width(lab, size, False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    if alpha <= 0.01:
        return
    for (col, lab), w in zip(items, ws):
        c = hexrgb(col)
        ctx.set_source_rgba(c[0], c[1], c[2], alpha)
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * alpha))
        ctx.set_line_width(2)
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.stroke()
        text(ctx, lab, x + 42, y, size, INK, align="left", bold=False, alpha=alpha)
        x += w + gap


# ============================================================
# 絵（バス・待つ人・バス停）。画像が無いときは線画
# ============================================================
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "bus"


def _load(name):
    from PIL import Image
    im = np.asarray(Image.open(ASSETS / name).convert("RGBA")).astype(np.float32) / 255
    pm = im[..., :3] * im[..., 3:4]
    out = np.empty(im.shape[:2] + (4,), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = pm[..., 2] * 255, pm[..., 1] * 255, pm[..., 0] * 255
    out[..., 3] = im[..., 3] * 255
    out = np.ascontiguousarray(out)
    return cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, out.shape[1], out.shape[0],
                                              out.shape[1] * 4), out


_KEYS = ("bus", "waiter")
IMG = {k: _load(f"{k}.png") for k in _KEYS} if all((ASSETS / f"{k}.png").exists() for k in _KEYS) else None


def sprite(ctx, key, cx, by, h, a=1.0):
    """下端の中央 (cx, by) を基準に高さ h で描く"""
    surf = IMG[key][0]
    k = h / surf.get_height()
    ctx.save()
    ctx.translate(cx, by)
    ctx.scale(k, k)
    ctx.set_source_surface(surf, -surf.get_width() / 2, -surf.get_height())
    ctx.get_source().set_filter(cairo.FILTER_BEST)
    ctx.paint_with_alpha(a)
    ctx.restore()


def bus_shape(ctx, cx, by, h, a=1.0):
    """バス（画像が無いときは線画）。下端の中央 (cx, by)、高さ h"""
    if IMG is not None:
        sprite(ctx, "bus", cx, by, h, a)
        return
    w = h * 3.0
    ctx.set_source_rgba(*hexrgb(COLD, a))
    rrect(ctx, cx - w / 2, by - h, w, h * 0.82, h * 0.18)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a * 0.9)
    for i in range(4):
        ctx.rectangle(cx - w / 2 + w * (0.08 + 0.22 * i), by - h * 0.9, w * 0.16, h * 0.32)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, a))
    for x in (cx - w * 0.3, cx + w * 0.3):
        ctx.arc(x, by - h * 0.15, h * 0.15, 0, 2 * math.pi)
        ctx.fill()


def waiter(ctx, cx, by, h, a=1.0):
    """待つ人（画像が無いときは棒人間）"""
    if IMG is not None:
        sprite(ctx, "waiter", cx, by, h, a)
        return
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(h * 0.05)
    ctx.arc(cx, by - h * 0.88, h * 0.1, 0, 2 * math.pi)
    ctx.stroke()
    ctx.move_to(cx, by - h * 0.78)
    ctx.line_to(cx, by - h * 0.4)
    ctx.line_to(cx - h * 0.12, by)
    ctx.move_to(cx, by - h * 0.4)
    ctx.line_to(cx + h * 0.12, by)
    ctx.stroke()


def stop_sign(ctx, x, by, a=1.0):
    """バス停の標識（どこの会社でもない、丸い板と柱）"""
    ctx.set_source_rgba(*hexrgb("#7a7f8a", a))
    ctx.rectangle(x - 5, by - 300, 10, 300)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#e9edf2", a))
    ctx.arc(x, by - 300, 48, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb("#2f62c9", a))
    ctx.set_line_width(8)
    ctx.stroke()
    bus_icon(ctx, x, by - 288, 26, a)


def bus_icon(ctx, cx, by, h, a=1.0, col="#2f62c9"):
    """小さいバスの印（横から見た四角いバス）。下端 by"""
    w = h * 1.6
    ctx.set_source_rgba(*hexrgb(col, a))
    rrect(ctx, cx - w / 2, by - h, w, h * 0.8, h * 0.2)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a)
    ctx.rectangle(cx - w * 0.38, by - h * 0.9, w * 0.76, h * 0.3)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(col, a))
    for x in (cx - w * 0.28, cx + w * 0.28):
        ctx.arc(x, by - h * 0.12, h * 0.13, 0, 2 * math.pi)
        ctx.fill()


def brake(dur_=0.5):
    """バスが止まる「プシュー」"""
    t = core._t(dur_)
    n = np.random.default_rng(3).standard_normal(len(t))
    n = n - np.convolve(n, np.ones(6) / 6, mode="same")
    return n * np.exp(-t * 5) * 0.6


def clip_left(ctx):
    ctx.rectangle(LX0_ - 10, LY0_ - 10, LX1_ - LX0_ + 20, LY1_ - LY0_ + 20)
    ctx.clip()


def person_color(w):
    v = float(np.clip(w / 25, 0, 1))
    return tuple(a * (1 - v) + b * v for a, b in zip(hexrgb(COLD)[:3], hexrgb(HOT)[:3]))


# ============================================================
# 左ページ: 0〜1章（バス停の場面）
# ============================================================
GROUND = 862
SIGN_X = 205
P_X = 355                                           # 待つ人が立つ位置
CROWD = [(330, 322), (432, 300), (524, 316), (612, 292), (702, 310), (792, 298)]
SX0, SX1, SY = 150, 880, 250                        # バスが来た時刻の帯（0〜62分）
SMAX = 62.0
_BUS0_SHOWN = [b for b in BUS0 if b <= SMAX]
_SHORT_I = int(np.argmin(np.diff(BUS0[BUS0 <= NEXT0])))     # 0章の範囲で、いちばん短いすき間の番号


def sx(m):
    return SX0 + (SX1 - SX0) * m / SMAX


def road(ctx):
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.5))
    ctx.set_line_width(4)
    ctx.move_to(LX0_ + 5, GROUND + 4)
    ctx.line_to(LX1_ - 5, GROUND + 4)
    ctx.stroke()
    stop_sign(ctx, SIGN_X, GROUND)


def walker(ctx, x, h, t, moving, a=1.0):
    """歩いている（上下にはずむ）／立って待っている（ゆっくり息をする）"""
    if moving:
        by = GROUND - abs(math.sin(t * 9.5)) * 8
    else:
        by = GROUND - 2.0 * (1 + math.sin(t * 2.0))
    waiter(ctx, x, by, h, a)


def bus_strip(ctx, t, a):
    """0章: このバス停にバスが来た時刻の帯。バス＝青い丸。2分と20分のすき間・着いた人・待ちの線"""
    if a <= 0:
        return
    t3, d3 = S("c0_3"), dur("c0_3")
    text(ctx, "このバス停にバスが来た時刻", (SX0 + SX1) / 2, 130, 30, PENCIL, bold=False, alpha=a)
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.move_to(SX0 - 10, SY)
    ctx.line_to(SX1 + 10, SY)
    ctx.stroke()
    for i, b in enumerate(_BUS0_SHOWN):                       # バスが1台ずつ現れる
        q = fade(t, t3 + 0.2 + 0.16 * i, 0.2)
        if q <= 0:
            continue
        ctx.set_source_rgba(1, 1, 1, a * q)
        ctx.arc(sx(b), SY, 13 + 2 * (1 - q), 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(COLD, a * q))
        ctx.arc(sx(b), SY, 10 + 3 * (1 - q), 0, 2 * math.pi)
        ctx.fill()
    # 2分／20分のすき間（ナレーションの順）
    t_s, t_l = t3 + 0.42 * d3, t3 + 0.72 * d3
    gaps = [(BUS0[_SHORT_I], BUS0[_SHORT_I + 1], "約2分", t_s, 0), (PREV0, NEXT0, "約20分", t_l, 1)]
    for b0, b1, lab, tt, k in gaps:
        q = fade(t, tt, 0.3)
        if q <= 0:
            continue
        y = SY + 38
        ctx.set_source_rgba(*hexrgb(RED, a * q))
        ctx.set_line_width(5)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        pw = clamp01((t - tt) / 0.4)
        ctx.move_to(sx(b0), y - 12)
        ctx.line_to(sx(b0), y + 4)
        ctx.line_to(sx(b0) + (sx(b1) - sx(b0)) * pw, y + 4)
        if pw >= 1:
            ctx.line_to(sx(b1), y - 12)
        ctx.stroke()
        xl = (sx(b0) + sx(b1)) / 2
        text(ctx, lab, xl + (44 if k == 0 else 0), y + 46, 34, RED, alpha=a * q)
    # この人が着いた時刻
    t4 = S("c0_4") + 0.7
    q = fade(t, t4, 0.3)
    if q > 0:
        x = sx(ARR0)
        ctx.set_source_rgba(*hexrgb(INK, a * q))
        ctx.move_to(x, SY - 20)
        ctx.line_to(x - 13, SY - 46)
        ctx.line_to(x + 13, SY - 46)
        ctx.close_path()
        ctx.fill()
        text(ctx, "この人が着いた", x, SY - 76, 30, INK, alpha=a * q)
    # 待つ線（カウンターと同じ速さで伸びる）
    w = counter_minutes(t)
    if w > 0:
        ctx.set_source_rgba(*hexrgb(HOT, 0.9 * a))
        ctx.set_line_width(9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(sx(ARR0), SY)
        ctx.line_to(sx(ARR0 + w), SY)
        ctx.stroke()


T_CNT0 = S("c0_5") + 0.35
T_CNT1 = S("c0_6") - 0.12
T_BUS_IN = T_CNT1 - 1.7


def counter_minutes(t):
    """待っている時間（分）。c0_5 のあいだに早回しで 0→14"""
    u = clamp01((t - T_CNT0) / (T_CNT1 - T_CNT0))
    return WAIT0 * (u * u * (3 - 2 * u)) if t >= T_CNT0 else 0.0


def L_stop(ctx, t):
    """0章・1章の左ページ"""
    ctx.save()
    clip_left(ctx)
    road(ctx)
    t_board = S("c0_6") + 1.7
    t_leave = S("c1_1") - 0.25
    # 最初のバスが走り去る（0秒から動く）
    if t < 2.1:
        bus_shape(ctx, 660 - 210 * t - 250 * t * t, GROUND, 140)
    # 次のバス（14分後に来て止まる）
    if T_BUS_IN <= t:
        if t < t_leave:
            x = 650 + 560 * (1 - ease_out((t - T_BUS_IN) / (T_CNT1 - T_BUS_IN)))
        else:
            d = t - t_leave
            x = 650 - 230 * d - 260 * d * d
        bus_shape(ctx, x, GROUND, 140)
    # 待つ人（歩いて来る → 待つ → バスに乗る）
    if t < t_board + 1.3:
        w = clamp01((t - 0.15) / 2.2)
        x = P_X + 560 * (1 - ease_out(w))
        a = 1.0
        if t >= t_board:
            u = ease((t - t_board) / 1.2)
            x, a = lerp(P_X, 480, u), 1 - u
        walker(ctx, x, 330, t, moving=(w < 1.0 and t < t_board) or t >= t_board, a=a)
    # たくさんの人（1章）
    t1 = S("c1_1")
    for k, (fx, h) in enumerate(CROWD):
        tk = t1 + 0.15 + 0.32 * k
        if t < tk:
            continue
        w = clamp01((t - tk) / 1.3)
        walker(ctx, lerp(990, fx, ease_out(w)), h, t + k, moving=w < 1.0)
    ctx.restore()
    # カウンター（c0_5〜）
    if t >= S("c0_5"):
        a = fade(t, S("c0_5"), 0.3) * (1 - clamp01((t - (t1 - 0.2)) / 0.4))
        if a > 0:
            m = counter_minutes(t)
            text(ctx, "待っている時間", 730, 400, 30, PENCIL, bold=False, alpha=a)
            text(ctx, f"{m:.0f}分", 730, 485, 100, INK, alpha=a)
            q = clamp01((t - (S("c0_6") + 0.15)) / 0.5)
            pen_circle(ctx, 730, 485, 128, 66, RED, seed=4, width=7, progress=q, alpha=a)
    bus_strip(ctx, t, clamp01(1 - (t - (t1 - 0.2)) / 0.4) if t >= t1 - 0.2 else 1.0)
    # 1章: バスとバスの間のどこかに着く図
    if t >= S("c1_3"):
        half_diagram(ctx, t)


def half_diagram(ctx, t):
    t0, d = S("c1_3"), dur("c1_3")
    a = fade(t, t0, 0.3)
    x0, x1, ly = 175, 855, 335
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.move_to(x0 - 40, ly)
    ctx.line_to(x1 + 40, ly)
    ctx.stroke()
    for x in (x0, x1):
        bus_icon(ctx, x, ly + 8, 54, a)
    # 平均10分（両矢印）
    ya = 205
    pen_line(ctx, x0, ya, x1, ya, INK, seed=2, width=4, progress=clamp01((t - t0 - 0.15) / 0.5), alpha=a)
    for xx, s in ((x0, 1), (x1, -1)):
        if t > t0 + 0.4:
            ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
            ctx.set_line_width(4)
            ctx.move_to(xx + s * 22, ya - 12)
            ctx.line_to(xx, ya)
            ctx.line_to(xx + s * 22, ya + 12)
            ctx.stroke()
    text(ctx, "平均10分", (x0 + x1) / 2, 165, 40, INK, alpha=a * fade(t, t0 + 0.4, 0.3))
    # 人が、でたらめな場所に着く（最後は真ん中）
    hops = [(0.40, 330), (0.50, 640), (0.60, 440), (0.70, 515)]
    xp, tp = None, None
    for f, x in hops:
        if t >= t0 + f * d:
            xp, tp = x, t0 + f * d
    if xp is not None:
        q = ease_out((t - tp) / 0.25)
        waiter(ctx, xp, ly - 3 - 18 * (1 - q), 150)
    # 待ちは、その半分
    tb = t0 + 0.78 * d
    if t >= tb:
        p = clamp01((t - tb) / 0.5)
        pen_line(ctx, 515, ly + 52, x1, ly + 52, RED, seed=8, width=6, progress=p)
        text(ctx, "待ちは、その半分？", 690, ly + 100, 36, RED, alpha=fade(t, tb + 0.2, 0.3))



# ============================================================
# 左ページ: 1万人の時間の帯（2章・3章・4-1）
# ============================================================
ROWS = 6
BX0, BX1 = 150, 880
RY0, RGAP, BAND = 370, 100, 62                      # 1段目の線の y、段の間、人が落ちる帯の高さ
OX, OY, OW, OH = 100, 80, 820, 880                  # 点を貼るキャッシュ面の範囲（左ページ全体）


def pos(m):
    """時刻（分）→ (x, 線の y)"""
    m = np.asarray(m, float)
    row = np.minimum((m // ROW_MIN).astype(int), ROWS - 1)
    return BX0 + (BX1 - BX0) * (m - row * ROW_MIN) / ROW_MIN, RY0 + row * RGAP


_px, _py = pos(ARR)
JIT = np.random.default_rng(SEED_MAIN + 9).uniform(0, BAND, N)
PX, PY = _px, _py - 8 - JIT
_c0, _c1 = np.array(hexrgb(COLD)[:3]), np.array(hexrgb(HOT)[:3])


def _colors(w):
    v = np.clip(w / 25, 0, 1)
    return _c0[None, :] * (1 - v[:, None]) + _c1[None, :] * v[:, None]


# ---------- 2章: 最初の60分だけを1本の線で見せる → 1段目に折りたたんで、10時間ぶん（6段）へ ----------
LN_Y = 650                                          # 1本の線の y
LN_MAX = 75.0                                       # 線が表す時間（分）。最初の60分の人が待つ次のバスまで入る
LANES = (172, 128, 84, 40)                          # 最初の4人の高さ（線からの上向きの px）。待ち時間の数字を付ける人
FIRST4 = (2764, 1286, 8103, 1997)                   # 待ち 3・12・7・1.5 分の人（BUS・ARR の最初の60分から。12分の人はバスが行った直後に着いた）
assert [int(round(float(WAIT[j]))) for j in FIRST4] == [3, 12, 7, 1] and all(ARR[j] < 60 for j in FIRST4), \
    "2章の最初の4人（FIRST4）が今の種のデータと合いません。待ち 3・12・7・1分 の人を選び直してください"
SLOW = 12                                           # 1人ずつゆっくり出す人数（最初の4人＋あと8人）
_set4 = set(FIRST4)
_in60 = [int(j) for j in ORDER if ARR[j] < 60 and int(j) not in _set4]
ORDER2 = np.array(list(FIRST4) + _in60 + [int(j) for j in ORDER if ARR[j] >= 60], dtype=int)    # 2章で人が現れる順
K60 = len(_in60) + len(FIRST4)                      # 最初の60分に着いた人数（約1000人）


def lnx(m):
    """1本の線の上の時刻（分）→ x"""
    return BX0 + (BX1 - BX0) * np.asarray(m, float) / LN_MAX


LNX = lnx(ARR)                                      # 各人の x（1本の線）
LNH = 8 + JIT * 3.1                                 # 各人の、線からの高さ（px）。約200pxの帯に散らして、色と数の差を見せる
NEXTX = lnx(BUS[KNEXT])                             # 各人が乗る次のバスの x（点から次のバスまでの線の右端）
PCOL = _colors(WAIT)                                # 待った時間の色（青→赤）
PCOL_S = _colors(SCHED_WAIT)                        # 時刻表どおりなら

T_A, D_A = S("c2_1b"), dur("c2_1b")                 # 2a: 1人ずつ・点から次のバスまでの線
T_B, D_B = S("c2_1c"), dur("c2_1c")                 # 2b: 赤と青・人がどんどん増える
T_C, D_C = S("c2_1d"), dur("c2_1d")                 # 2c: 1段目に折りたたむ
APP = [T_A + 0.24 * D_A, T_A + 0.62 * D_A, T_A + 0.78 * D_A, T_A + 0.90 * D_A] + \
      [T_B + 0.15 + 0.17 * i for i in range(SLOW - 4)]               # ゆっくり出す12人が現れる時刻
BAR0 = [T_A + 0.47 * D_A] + [APP[i] + 0.3 for i in range(1, 4)] + [APP[i] + 0.1 for i in range(4, SLOW)]    # 線が伸び始める時刻
BAR_DUR = [0.8] * 4 + [0.35] * (SLOW - 4)
CT0 = T_B + 0.5 * D_B                               # 「長く待った人ほど、赤い点」。点の色が変わり始める
RAMP0, RAMP1 = CT0 + 0.3, E("c2_1c") + 0.5          # 人がどんどん増える（12人 → 約1000人）
FOLD0 = T_C + 0.3                                   # 1本の線 → 1段目（折りたたむ）
FOLD1 = FOLD0 + 1.8
M_T0 = CT0                                          # 1万人モードの音（beat・shimmer）が始まる
M_T1 = E("g2") - 0.5                                # 全員が落ちた


def m_count(t):
    """2章で画面に出ている人数"""
    if t < RAMP0:
        return sum(1 for a in APP if t >= a)
    if t < RAMP1:
        return int(SLOW + (K60 - SLOW) * ease(clamp01((t - RAMP0) / (RAMP1 - RAMP0))))
    if t < FOLD1:
        return K60
    return int(K60 + (N - K60) * clamp01((t - FOLD1) / (M_T1 - FOLD1)) ** 1.5)


class PeopleLayer:
    """点を貼る面。毎コマ描かず、増えた分だけ足す（ORDER2 の順）。skip 人目までは描かない（別に1人ずつ描く人）"""

    def __init__(self, cols, rad=2.2, xs=None, ys=None, skip=0):
        self.cols, self.rad, self.skip = cols, rad, skip
        self.xs, self.ys = (PX if xs is None else xs), (PY if ys is None else ys)
        self.n, self.surf = skip, None

    def get(self, n):
        if self.surf is None or n < self.n:
            self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, OW, OH)
            self.n = self.skip
        if n > self.n:
            c = cairo.Context(self.surf)
            for j in ORDER2[self.n:n]:
                c.set_source_rgba(self.cols[j, 0], self.cols[j, 1], self.cols[j, 2], 0.85)
                c.arc(self.xs[j] - OX, self.ys[j] - OY, self.rad, 0, 2 * math.pi)
                c.fill()
            self.n = n
        return self.surf


LAYER_W, LAYER_S = PeopleLayer(PCOL), PeopleLayer(PCOL_S)
LAYER_L = PeopleLayer(PCOL, 3.0, xs=LNX, ys=LN_Y - LNH, skip=SLOW)       # 2b: 1本の線の上の点


def paint_layer(ctx, layer, n, a=1.0):
    if a <= 0.003 or n <= 0:
        return
    ctx.set_source_surface(layer.get(n), OX, OY)
    ctx.paint_with_alpha(a)


def band_lines(ctx, a=1.0):
    for r in range(ROWS):
        y = RY0 + r * RGAP
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(3)
        ctx.move_to(BX0, y)
        ctx.line_to(BX1, y)
        ctx.stroke()


def bus_marks(ctx, times, a=1.0, alpha_each=None):
    bx, by = pos(times)
    for i, (x, y) in enumerate(zip(bx, by)):
        q = a if alpha_each is None else a * alpha_each[i]
        if q > 0.01:
            bus_icon(ctx, float(x), float(y) + 30, 24, q)


def band_header(ctx, line1, a=1.0):
    text(ctx, line1, (LX0_ + LX1_) / 2, 140, 30, PENCIL, bold=False, alpha=a)


def sched_u(t):
    """4-1: バスの印が等間隔に並び替わる 0→1 と、点の色が変わる 0→1"""
    t0 = S("c4a_1") + 0.9
    return ease(clamp01((t - t0) / 1.6)), ease(clamp01((t - (t0 + 1.6)) / 1.3))


_BUS_N = len(BUS) - 1                                # 画面に出すバスの数（最後の1台は帯の外）
_BUS_EVEN = np.arange(0, T_ALL, MU)                  # 時刻表どおりのバス（0, 10, 20 … 590）


def _dot(ctx, x, y, r, col, a=1.0):
    ctx.set_source_rgba(col[0], col[1], col[2], a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def _bus_dot(ctx, x, y, a):
    """0章と同じ、線の上のバスの印（青い丸）"""
    _dot(ctx, x, y, 14, (1, 1, 1), a)
    _dot(ctx, x, y, 10.5, hexrgb(COLD)[:3], a)


_INK3 = hexrgb(INK)[:3]
_BUS60 = BUS[BUS <= LN_MAX]


def _slow_height(i, t):
    """ゆっくり出す12人の、線からの高さ。最初は4人が階段状（待ち時間の線を見分けるため）、色が変わるころ普通の高さへ"""
    base = LANES[i] if i < 4 else LNH[ORDER2[i]]
    return lerp(base, LNH[ORDER2[i]], ease(clamp01((t - CT0) / 1.2)))


def _line_people(ctx, t, a):
    """2a・2b: 1本の線（最初の60分）。点が1人ずつ現れ、点から次のバスまで待ち時間の線が伸びる"""
    cu = ease(clamp01((t - CT0) / 0.9))                       # 点の色が変わる 0→1
    bf = 1 - clamp01((t - (CT0 + 0.4)) / 2.0)                 # 待ち時間の線が薄れていく 1→0
    n = m_count(t)
    # 追加の人（2b）。毎コマ描かず貼る
    if n > SLOW:
        ctx.set_source_surface(LAYER_L.get(n), OX, OY)
        ctx.paint_with_alpha(a)
    # ゆっくり出す12人
    for i in range(SLOW):
        j = int(ORDER2[i])
        q = fade(t, APP[i], 0.25)
        if q <= 0:
            continue
        x, y = LNX[j], LN_Y - _slow_height(i, t)
        col = [lerp(_INK3[c], PCOL[j, c], cu) for c in range(3)]
        # 点から次のバスまでの線（待ち時間）
        p = ease(clamp01((t - BAR0[i]) / BAR_DUR[i]))
        if p > 0 and bf > 0:
            wide = 8 if i < 4 else 3.2
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_source_rgba(*hexrgb(HOT)[:3], 0.85 * bf * a)
            ctx.set_line_width(wide)
            ctx.move_to(x, y)
            ctx.line_to(x + (NEXTX[j] - x) * p, y)
            ctx.stroke()
            if i < 4 and p >= 1:
                # バスの印へ、細い点線でつなぐ
                ctx.set_source_rgba(*hexrgb(PENCIL)[:3], 0.55 * bf * a)
                ctx.set_line_width(2)
                ctx.set_dash([5, 6])
                ctx.move_to(NEXTX[j], y)
                ctx.line_to(NEXTX[j], LN_Y - 14)
                ctx.stroke()
                ctx.set_dash([])
        if i < 4:
            _dot(ctx, x, y, 9.5 * (1.6 - 0.6 * q) * (1 - 0.55 * cu), (1, 1, 1), a * q)
        _dot(ctx, x, y, (7.0 * (1.6 - 0.6 * q) * (1 - 0.55 * cu)) if i < 4 else 3.0, col, a * q)
        if i < 4:
            lab_a = fade(t, BAR0[i] + BAR_DUR[i], 0.3) * bf
            if lab_a > 0:
                text(ctx, f"{int(round(float(WAIT[j])))}分", NEXTX[j] + 14, y, 34, RED, align="left", alpha=lab_a * a)
    # 「この人が着いた」（最初の1人だけ。0章と同じ描き方）
    j0 = int(ORDER2[0])
    qm = fade(t, APP[0] + 0.1, 0.3) * (1 - fade(t, APP[1] - 0.15, 0.25))
    if qm > 0:
        x, y = LNX[j0], LN_Y - LANES[0]
        _tri = [(x, y - 16), (x - 13, y - 42), (x + 13, y - 42)]
        ctx.set_source_rgba(*_INK3, qm * a)
        ctx.move_to(*_tri[0])
        ctx.line_to(*_tri[1])
        ctx.line_to(*_tri[2])
        ctx.close_path()
        ctx.fill()
        text(ctx, "この人が着いた", x, y - 72, 30, INK, alpha=qm * a)


def _fold_dots(ctx, e):
    """2c: 最初の60分の約1000人が、1本の線から1段目へ移る（位置・大きさが少しずつ変わる）"""
    idx = ORDER2[:K60]
    x = LNX[idx] * (1 - e) + PX[idx] * e
    y = (LN_Y - LNH[idx]) * (1 - e) + PY[idx] * e
    r = lerp(3.0, 2.2, e)
    for xi, yi, ci in zip(x, y, PCOL[idx]):
        ctx.set_source_rgba(ci[0], ci[1], ci[2], 0.85)
        ctx.arc(xi, yi, r, 0, 2 * math.pi)
        ctx.fill()


def _bracket(ctx, x0, x1, y, down, a, col=RED):
    """赤ペンの括弧（すき間の幅）。down=True なら下向きの括弧（線の下に置く）"""
    d = 12 if down else -12
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y - d)
    ctx.line_to(x0, y)
    ctx.line_to(x1, y)
    ctx.line_to(x1, y - d)
    ctx.stroke()


T_BR1 = E("c2_1c") - 2.6                            # 「長いすき間」の書き込み
T_BR2 = E("c2_1c") - 1.2                            # 「短いすき間」の書き込み
_LONG_G = max(((BUS[i + 1] - BUS[i], i) for i in range(len(BUS) - 1) if BUS[i + 1] <= LN_MAX))[1]     # 最初の60分でいちばん長いすき間
_gl = [(BUS[i + 1] - BUS[i], i) for i in range(len(BUS) - 1) if BUS[i + 1] <= LN_MAX and BUS[i + 1] - BUS[i] > 5]
_SHORT_G = min(_gl)[1]                              # いちばん短い（0.3分など）は見えないので、5分より長いなかで最短


def _notes(ctx, t, a):
    """2b の後半: 長いすき間は人が多く赤い、短いすき間は人が少なく青い（3章の予告）"""
    x0, x1 = float(lnx(BUS[_LONG_G])) + 5, float(lnx(BUS[_LONG_G + 1])) - 5
    q = fade(t, T_BR1, 0.4) * a
    if q > 0:
        _bracket(ctx, x0, x0 + (x1 - x0) * clamp01((t - T_BR1) / 0.5), LN_Y - 225, False, q)
        text(ctx, "長いすき間：人が多く、赤い", (x0 + x1) / 2 + 40, LN_Y - 270, 34, RED, alpha=q * fade(t, T_BR1 + 0.3, 0.3))
    x0, x1 = float(lnx(BUS[_SHORT_G])) + 5, float(lnx(BUS[_SHORT_G + 1])) - 5
    q = fade(t, T_BR2, 0.4) * a
    if q > 0:
        _bracket(ctx, x0, x0 + (x1 - x0) * clamp01((t - T_BR2) / 0.5), LN_Y + 66, True, q, INK)
        text(ctx, "短いすき間：人が少なく、青い", x0 - 15, LN_Y + 112, 34, INK, align="left", alpha=q * fade(t, T_BR2 + 0.3, 0.3))


def L_crowd(ctx, t):
    """2章: 最初の60分の1本の線（2a・2b）→ 1段目の位置へ縮みながら移る（2c）→ 他の5段が現れ、10時間ぶん（6段）に1万人"""
    ctx.save()
    clip_left(ctx)
    a0 = fade(t, S("c2_1") + 0.2, 0.5)
    e = ease(clamp01((t - FOLD0) / (FOLD1 - FOLD0)))          # 1本の線 → 1段目 0→1
    r2 = ease(clamp01((t - (FOLD1 - 0.1)) / 0.7))             # 2〜6段目・残りのバスの印のフェードイン 0→1
    n = m_count(t)
    # 見出し
    h1 = a0 * (1 - clamp01(e * 3))
    text(ctx, "時間 →", 505, 140, 30, PENCIL, bold=False, alpha=h1 * (1 - fade(t, T_A, 0.3)))
    text(ctx, "最初の60分だけ", 505, 140, 30, PENCIL, bold=False, alpha=h1 * fade(t, T_A, 0.3))
    text(ctx, "時間 →（1段で100分。6段で10時間）", 505, 140, 30, PENCIL, bold=False, alpha=clamp01((e - 0.6) / 0.4))
    # 線
    ly = lerp(LN_Y, RY0, e)
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a0))
    ctx.set_line_width(4 if e < 0.5 else 3)
    ctx.move_to(BX0 - 10, ly)
    ctx.line_to(BX1 + 10, ly)
    ctx.stroke()
    for r in range(1, ROWS):                                  # 2〜6段目の線は、移り終わってから
        yy = RY0 + r * RGAP
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * r2))
        ctx.set_line_width(3)
        ctx.move_to(BX0, yy)
        ctx.line_to(BX1, yy)
        ctx.stroke()
    # バスの印（0章と同じ印）。1本の線のバスは線と一緒に1段目へ。残りは移り終わってからフェードイン
    for i, b in enumerate(BUS[:-1]):
        if b <= LN_MAX:
            qa = fade(t, S("c2_1") + (0.3 + 0.5 * min(i, 8) / 8.0) * dur("c2_1"), 0.25)
            bx = lerp(float(lnx(b)), float(pos(b)[0]), e)
            h = lerp(40, 24, e)
            bus_icon(ctx, bx, ly + lerp(40, 30, e), h, a0 * qa)
        elif r2 > 0:
            bx, by = pos(b)
            bus_icon(ctx, float(bx), float(by) + 30, 24, r2)
    # 「バスが来た時刻」（最初だけ）
    ql = fade(t, T_A + 0.2, 0.3) * (1 - fade(t, CT0 - 0.4, 0.3))
    if ql > 0:
        text(ctx, "↑ バスが来た時刻", 135, LN_Y + 85, 32, INK, align="left", alpha=ql * a0)
    # 人
    if t < FOLD0:
        _line_people(ctx, t, a0)
        _notes(ctx, t, a0)
    elif t < FOLD1:
        _fold_dots(ctx, e)
    else:
        paint_layer(ctx, LAYER_W, n)
    # 人数・凡例
    if n > 0:
        text(ctx, "着いた人", 340, 207, 30, PENCIL, bold=False, alpha=a0)
        text(ctx, f"{n:,}人", 600, 205, 60, INK, alpha=a0)
    lg = fade(t, CT0, 0.4)
    if lg > 0:
        legend_at(ctx, [(COLD, "すぐ乗れた"), (HOT, "長く待った")], 505, 285, 28, alpha=lg)
    ctx.restore()


def zoom_u(t):
    """3章: 帯からAさんの段へ寄る（0→1）。c3_9 で帯に戻る（1→0）"""
    u = ease(clamp01((t - S("c3_1")) / 1.3))
    return u * (1 - ease(clamp01((t - S("c3_9")) / 1.3)))


ZROW = int(A_ARR // ROW_MIN)
ZW0, ZW1 = A_PREV - 9.0, A_NEXT + 9.0
ZX0, ZX1, ZY = 150, 880, 560
ZBAND = 124
IDX_A = np.flatnonzero((ARR >= ZROW * ROW_MIN) & (ARR < (ZROW + 1) * ROW_MIN))
_ZX = ZX0 + (ZX1 - ZX0) * (ARR[IDX_A] - ZW0) / (ZW1 - ZW0)
_ZY = ZY - 8 - JIT[IDX_A] * (ZBAND / BAND)


def zx(m):
    return ZX0 + (ZX1 - ZX0) * (m - ZW0) / (ZW1 - ZW0)


def L_one(ctx, t):
    """3章: Aさんに寄る → すき間24.8分 → 帯に戻って 10分 と 20分 の棒"""
    ctx.save()
    clip_left(ctx)
    u = zoom_u(t)
    t_back = S("c3_9")
    if u < 0.999:                                    # 帯（寄っていくあいだ、薄れていく）
        a = 1 - u
        hd = 1 - fade(t, S("c3_9") + 0.8, 0.25)         # 10分と20分の棒を出すあいだは、見出しと凡例をしまう
        band_header(ctx, "時間 →（1段で100分。6段で10時間）", a * hd)
        band_lines(ctx, a)
        bus_marks(ctx, BUS[:-1], a)
        paint_layer(ctx, LAYER_W, N, a)
        if t >= S("c3_9") - 0.1 or t < S("c3_1") + 5:
            legend_at(ctx, [(COLD, "すぐ乗れた"), (HOT, "長く待った")], 505, 285, 28, alpha=hd)
    if u > 0.003:
        # Aさんの段の点が、段の並びから拡大した並びへ動く
        x = _px[IDX_A] * (1 - u) + _ZX * u
        y = PY[IDX_A] * (1 - u) + _ZY * u
        c = PCOL[IDX_A]
        r = lerp(2.2, 5.2, u)
        for xi, yi, ci in zip(x, y, c):
            if (LX0_ - 20 < xi < LX1_ + 20) and (xi > lerp(LX0_ - 20, ZX0 - 30, u)) and (xi < lerp(LX1_ + 20, ZX1 + 20, u)):
                ctx.set_source_rgba(ci[0], ci[1], ci[2], 0.85)
                ctx.arc(xi, yi, r, 0, 2 * math.pi)
                ctx.fill()
        # 拡大した時間の線とバス
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * u))
        ctx.set_line_width(4)
        ctx.move_to(ZX0 - 30, ZY)
        ctx.line_to(ZX1 + 20, ZY)
        ctx.stroke()
        for b in BUS:
            if ZW0 + 1 < b < ZW1 - 1:
                bus_icon(ctx, zx(b), ZY + 68, 58, u, col="#2f62c9")
        text(ctx, "この時間帯だけを大きく", (LX0_ + LX1_) / 2, 150, 32, PENCIL, bold=False, alpha=u)
        # Aさん
        t1, d1 = S("c3_1"), dur("c3_1")
        ax = zx(A_ARR)
        s = fade(t, t1 + 1.1, 0.5) * u
        if s > 0:
            g = cairo.RadialGradient(ax, ZY - 100, 10, ax, ZY - 100, 190)
            g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.7 * s)
            g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
            ctx.set_source(g)
            ctx.arc(ax, ZY - 100, 190, 0, 2 * math.pi)
            ctx.fill()
            waiter(ctx, ax, ZY - 6, 178, s)
            pen_circle(ctx, ax, ZY - 95, 52, 105, RED, seed=11, width=6,
                       progress=clamp01((t - t1 - 1.3) / 0.5), alpha=u)
        # 待った線（c3_1 の2文目に合わせて伸びる）
        tl0 = t1 + 0.42 * d1
        p = clamp01((t - tl0) / (0.5 * d1))
        if p > 0:
            ya = ZY + 118
            ctx.set_source_rgba(*hexrgb(HOT, 0.95 * u))
            ctx.set_line_width(12)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(ax, ya)
            ctx.line_to(ax + (zx(A_NEXT) - ax) * p, ya)
            ctx.stroke()
            text(ctx, f"Aさん {A_WAIT * p:.0f}分待ち", (ax + zx(A_NEXT)) / 2, ya + 52, 44, RED, alpha=u)
        # すき間24.8分の寸法線（c3_2）
        t2 = S("c3_2")
        if t >= t2:
            q = fade(t, t2 + 0.6, 0.4)
            for b in (A_PREV, A_NEXT):
                pen_circle(ctx, zx(b), ZY + 40, 34, 40, RED, seed=13 + int(b) % 5, width=5,
                           progress=clamp01((t - t2 - 0.5) / 0.5), alpha=u)
            yd = ZY + 255
            p2 = clamp01((t - t2 - 1.3) / 0.6)
            if p2 > 0:
                xa, xb = zx(A_PREV), zx(A_PREV) + (zx(A_NEXT) - zx(A_PREV)) * p2
                pen_line(ctx, xa, yd, xb, yd, INK, seed=17, width=5, alpha=u)
                for xx in (xa, zx(A_NEXT) if p2 >= 1 else None):
                    if xx is not None:
                        pen_line(ctx, xx, yd - 14, xx, yd + 14, INK, seed=19, width=5, alpha=u)
                text(ctx, f"{A_GAP:.1f}分", (zx(A_PREV) + zx(A_NEXT)) / 2, yd + 52, 50, INK,
                     alpha=u * fade(t, t2 + 1.8, 0.3))
    # 10分 と 20分 の棒（c3_9〜）。帯の上に白い紙を貼って、その上に描く
    tb = S("c3_9")
    if t >= tb + 0.9:
        a = fade(t, tb + 0.9, 0.3)
        ctx.set_source_rgba(1, 1, 0.98, 0.94 * a)
        rrect(ctx, 125, 108, 770, 170, 10)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(2.5)
        rrect(ctx, 125, 108, 770, 170, 10)
        ctx.stroke()
        unit = 20.0
        bx0 = 160
        t10 = S("c3_10")
        text(ctx, "バスの間隔の平均", bx0, 138, 28, PENCIL, align="left", bold=False, alpha=a)
        bar(ctx, bx0, 172, 10 * unit, COLD, a * fade(t, t10, 0.2), clamp01((t - t10) / 0.5))
        text(ctx, "10分", bx0 + 10 * unit + 16, 172, 34, INK, align="left", alpha=a * fade(t, t10 + 0.5, 0.2))
        text(ctx, "待つ人から見たすき間の平均", bx0, 212, 28, PENCIL, align="left", bold=False, alpha=a)
        t20 = S("c3_10") + 0.55 * dur("c3_10")
        bar(ctx, bx0, 246, 20 * unit, HOT, a * fade(t, t20, 0.2), clamp01((t - t20) / 0.6))
        text(ctx, "20分", bx0 + 20 * unit + 16, 246, 34, INK, align="left", alpha=a * fade(t, t20 + 0.6, 0.2))
        t11 = S("c3_11")
        if t >= t11:
            p = clamp01((t - t11 - 0.2) / 0.5)
            xm = bx0 + 10 * unit
            pen_line(ctx, xm, 226, xm, 268, RED, seed=23, width=5, progress=p)
            text(ctx, "半分 ＝ 10分", bx0 + 20 * unit + 112, 246, 30, RED, align="left",
                 alpha=fade(t, t11 + 0.5, 0.3))
    ctx.restore()


def bar(ctx, x, y, w, col, a, p):
    if a <= 0.01 or p <= 0:
        return
    ctx.set_source_rgba(*hexrgb(col, 0.9 * a))
    rrect(ctx, x, y - 14, max(1, w * p), 28, 6)
    ctx.fill()


# ---------- 4-1: 時刻表どおり ----------
def L_sched(ctx, t):
    ctx.save()
    clip_left(ctx)
    ub, uc = sched_u(t)
    a = fade(t, S("ch3") - 0.1, 0.4)
    band_header(ctx, "同じ1万人。バスだけ時刻表どおり", a)
    band_lines(ctx, a)
    n = len(BUS) - 1
    k = min(n, len(_BUS_EVEN))
    times = np.concatenate([lerp(BUS[:k], _BUS_EVEN[:k], ub), BUS[k:n]])
    al = np.concatenate([np.ones(k), 1 - ub * np.ones(n - k)])
    bus_marks(ctx, times, a, al)
    if len(_BUS_EVEN) > k:
        bus_marks(ctx, _BUS_EVEN[k:], a, np.full(len(_BUS_EVEN) - k, ub))
    paint_layer(ctx, LAYER_W, N, a * (1 - uc))
    paint_layer(ctx, LAYER_S, N, a * uc)
    legend_at(ctx, [(COLD, "すぐ乗れた"), (HOT, "長く待った")], 505, 285, 28)
    ctx.restore()


# ---------- 4-2: 乱れと平均の待ち ----------
GX0, GX1, GY0, GY1 = 235, 860, 215, 770             # 横軸（乱れ 0〜10）・縦軸（待ち 10〜5）
SD_T = []                                           # 点が打たれる時刻


def _sd_times():
    t3, d3 = S("c4b_3"), dur("c4b_3")
    t4, d4 = S("c4b_4"), dur("c4b_4")
    return [S("c4b_2") + 0.7 * dur("c4b_2"), t3 + 0.40 * d3, t3 + 0.86 * d3, t4 + 0.05 * d4, t4 + 0.30 * d4,
            t4 + 0.55 * d4]


SD_T = _sd_times()
T_CURVE = E("c4b_4") - 0.3


def gx(sd):
    return GX0 + (GX1 - GX0) * sd / 10.0


def gy(w):
    return GY1 - (GY1 - GY0) * (w - 5.0) / 5.0


def L_noise(ctx, t):
    ctx.save()
    clip_left(ctx)
    a = fade(t, S("ch4") + 0.3, 0.5)
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(4)
    ctx.move_to(GX0, GY0 - 20)
    ctx.line_to(GX0, GY1)
    ctx.line_to(GX1 + 15, GY1)
    ctx.stroke()
    for sd in SD_LIST:
        text(ctx, f"{sd}", gx(sd), GY1 + 32, 28, PENCIL, bold=False, alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(2)
        ctx.move_to(gx(sd), GY1)
        ctx.line_to(gx(sd), GY1 + 9)
        ctx.stroke()
    for w in (5, 6, 7, 8, 9, 10):
        text(ctx, f"{w}", GX0 - 24, gy(w), 28, PENCIL, align="right", bold=False, alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.3 * a))
        ctx.set_line_width(1.5)
        ctx.move_to(GX0, gy(w))
        ctx.line_to(GX1, gy(w))
        ctx.stroke()
    text(ctx, "乱れの大きさ（分）  0＝時刻表どおり、10＝でたらめ", (GX0 + GX1) / 2 - 25, GY1 + 82, 28, INK, bold=False, alpha=a)
    text(ctx, "平均の待ち（分）", GX0 - 85, GY0 - 55, 30, INK, align="left", alpha=a)
    # 曲線（最後に、ペンでなぞる）
    p = clamp01((t - T_CURVE) / 1.5)
    if p > 0:
        ctx.set_source_rgba(*hexrgb(RED, 0.85))
        ctx.set_line_width(7)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        n = max(2, int(60 * p))
        for i in range(n + 1):
            sd = 10.0 * i / 60
            (ctx.move_to if i == 0 else ctx.line_to)(gx(sd), gy(5 * (1 + (sd / 10) ** 2)))
        ctx.stroke()
    # 点
    for i, (sd, w) in enumerate(zip(SD_LIST, SHOW_SD)):
        q = fade(t, SD_T[i], 0.25)
        if q <= 0:
            continue
        sc = 1 + 0.8 * (1 - q)
        ctx.set_source_rgba(1, 1, 1, q)
        ctx.arc(gx(sd), gy(w), 14 * sc, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, q))
        ctx.arc(gx(sd), gy(w), 10 * sc, 0, 2 * math.pi)
        ctx.fill()
        dx, dy = (28, -4) if i < 5 else (-58, 6)
        if i in (1, 2, 3, 4):
            dx, dy = -48, -26
        if i == 0:
            dx, dy = 30, -42
        if i == 1:
            dx, dy = -2, -46
        text(ctx, f"{w:.1f}", gx(sd) + dx, gy(w) + dy, 32, RED, alpha=q)
    ctx.restore()



# ============================================================
# 左ページ: 団子運転（円い路線）
# ============================================================
RC = (505, 548)                                      # 路線の中心
RR = 232                                             # 路線の半径
BUS_COL = ["#5aa0d8", "#e8943a", "#5fae6b", "#a06ac9", "#d8434e", "#2fa9a0"]
_STOPTAB = {}


def stop_tables(log):
    """停留所ごとの（バスが乗り始めた時刻・発車時刻・待っていた人数・初期の「前のバスが出た時刻」）"""
    hit = _STOPTAB.get(id(log))
    if hit is not None and hit[0] is log:
        return hit[1]
    h, step = CYCLE / BUSES, CYCLE / STOPS
    out = []
    for s in range(STOPS):
        rows = log[log[:, C_S] == s]
        rows = rows[np.argsort(rows[:, C_T], kind="stable")]
        out.append((rows[:, C_T], rows[:, C_DEP], LAM * rows[:, C_GAP], (s * step) % h - h))
    _STOPTAB[id(log)] = (log, out)
    return out


def queues(log, m):
    """時刻 m（分）に各停留所で待っている人数（期待値）"""
    q = np.empty(STOPS)
    for s, (T, D, Nn, p0) in enumerate(stop_tables(log)):
        i = int(np.searchsorted(T, m, side="right")) - 1
        if i < 0:
            q[s] = LAM * (m - p0)
        elif m < D[i]:
            q[s] = Nn[i] * (1 - (m - T[i]) / max(D[i] - T[i], 1e-6))
        else:
            q[s] = LAM * (m - D[i])
    return np.maximum(q, 0)


def ring_xy(ang, r=RR):
    return RC[0] + r * math.sin(ang), RC[1] - r * math.cos(ang)


def draw_ring(ctx, log, m, n_show=6, a=1.0, flags=False, ring_a=1.0):
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a * ring_a))
    ctx.set_line_width(6)
    ctx.arc(RC[0], RC[1], RR, 0, 2 * math.pi)
    ctx.stroke()
    q = queues(log, m)
    for s in range(STOPS):
        ang = 2 * math.pi * s / STOPS
        ux, uy = math.sin(ang), -math.cos(ang)
        tx, ty = math.cos(ang), math.sin(ang)
        n = int(min(round(q[s]), 24))
        ctx.set_source_rgba(*hexrgb(INK, 0.72 * a))
        for i in range(n):
            row, col = divmod(i, 2)
            r = RR + 28 + row * 10.5
            lat = (col - 0.5) * 11
            ctx.arc(RC[0] + ux * r + tx * lat, RC[1] + uy * r + ty * lat, 4.4, 0, 2 * math.pi)
            ctx.fill()
        px, py = ring_xy(ang)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.arc(px, py, 9, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(3)
        ctx.arc(px, py, 9, 0, 2 * math.pi)
        ctx.stroke()
        if flags and s in HOLD_STOPS:
            ax, ay = RC[0] + ux * (RR - 13), RC[1] + uy * (RR - 13)
            bx, by = RC[0] + ux * (RR - 52), RC[1] + uy * (RR - 52)
            ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
            ctx.set_line_width(4)
            ctx.move_to(ax, ay)
            ctx.line_to(bx, by)
            ctx.stroke()
            ctx.set_source_rgba(*hexrgb(RED, a))
            ctx.move_to(bx, by)
            ctx.line_to(bx + tx * 28 - ux * 8, by + ty * 28 - uy * 8)
            ctx.line_to(bx - ux * 19, by - uy * 19)
            ctx.close_path()
            ctx.fill()
    angs = bus_angles(log, m)
    for k in range(n_show):
        x, y = ring_xy(angs[k], RR + ((k % 3) - 1) * 14)
        ctx.set_source_rgba(1, 1, 1, 0.9 * a)
        rrect(ctx, x - 24, y - 17, 48, 34, 9)
        ctx.fill()
        bus_icon(ctx, x, y + 13, 26, a, BUS_COL[k])
    return angs


def clusters(angs, thr=1.6):
    """バスの固まり（番号のリスト）。thr 停留所ぶん未満しか離れていないバスを1つの固まりに"""
    n = len(angs)
    order = np.argsort(angs)
    a = np.asarray(angs)[order]
    d = np.diff(np.concatenate([a, [a[0] + 2 * math.pi]]))
    br = np.flatnonzero(d >= 2 * math.pi / STOPS * thr)
    if len(br) == 0:
        return [list(order)]
    out = []
    for j in range(len(br)):
        i, e, idx = (br[j] + 1) % n, br[(j + 1) % len(br)], []
        while True:
            idx.append(int(order[i]))
            if i == e:
                break
            i = (i + 1) % n
        out.append(idx)
    return out


def circle_group(ctx, angs, idx, p, seed, a=1.0):
    sa, ca = float(np.mean(np.sin(angs[idx]))), float(np.mean(np.cos(angs[idx])))
    c = math.atan2(sa, ca)
    span = max(abs(math.atan2(math.sin(angs[i] - c), math.cos(angs[i] - c))) for i in idx)
    x, y = ring_xy(c, RR)
    r = 34 + RR * span
    pen_circle(ctx, x, y, r, r * 0.8, RED, seed=seed, width=6, progress=p, alpha=a)


def ring_label(ctx, ang, s, size=32, col=RED, a=1.0, r=112):
    x, y = ring_xy(ang, r)
    text(ctx, s, x, y, size, col, alpha=a)


def clock_face(ctx, m, a=1.0):
    """左上の時計（早回しの合図）。長い針が1時間で1周する"""
    cx, cy, r = 190, 200, 54
    ctx.set_source_rgba(1, 1, 1, 0.85 * a)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(4)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.stroke()
    for k in range(12):
        ang = k * math.pi / 6
        ctx.move_to(cx + (r - 9) * math.sin(ang), cy - (r - 9) * math.cos(ang))
        ctx.line_to(cx + (r - 2) * math.sin(ang), cy - (r - 2) * math.cos(ang))
    ctx.stroke()
    for ln, rate, w in ((r - 12, 1 / 60, 4), (r - 28, 1 / 720, 6)):
        ang = 2 * math.pi * m * rate
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(cx, cy)
        ctx.line_to(cx + ln * math.sin(ang), cy - ln * math.cos(ang))
        ctx.stroke()
    text(ctx, "早回し", 340, 200, 38, RED, alpha=a)
    for i in range(2):                              # ▶▶
        x0 = 410 + i * 26
        ctx.set_source_rgba(*hexrgb(RED, a))
        ctx.move_to(x0, 184)
        ctx.line_to(x0 + 22, 200)
        ctx.line_to(x0, 216)
        ctx.close_path()
        ctx.fill()


# ---------- 時間の進み方 ----------
TOY_V = 5.5                                          # 「少し遅れる」を見せる場面は、1秒で5.5分ぶん
TOY_T0 = E("c4c_2") - 1.0
TOY_DELAY = 5.0
M_DELAY = (S("c4c_4") + 0.3 - TOY_T0) * TOY_V
FF0, FF1 = S("g4c"), E("g4c")                        # 団子運転の早回し（0→180分）
T8 = E("c4c_8") - 0.3                                # 180→240分（4時間目）


def toy_sim(m_delay, delay, t_end):
    """見せ方用の小さな版: 平均で動かし（人数は期待値）、バス0だけ1か所で delay 分遅らせる。
    団子運転のしくみ（人が多い → 乗車が延びる → 後ろが追いつく）を、数十分で見えるようにするための絵"""
    h, step = CYCLE / BUSES, CYCLE / STOPS
    q, prev = [], {}
    for k in range(BUSES):
        s0 = -(-k * STOPS // BUSES)
        t0 = (s0 * BUSES - k * STOPS) / BUSES * step
        heapq.heappush(q, (t0, k, s0 % STOPS, t0))
    for s in range(STOPS):
        prev[s] = (s * step) % h - h
    last_arr = {s: prev[s] - 0.1 for s in range(STOPS)}
    log, delayed = [], False
    while q:
        t, k, s, ts = heapq.heappop(q)
        if t > t_end:
            break
        t = max(t, prev[s] + OVERTAKE_GAP)             # 見せ方用の版は、いつも追い越さない
        gap = max(t - prev[s], 0.0)
        n = LAM * gap
        dep = t + n * BOARD
        if k == 0 and not delayed and t >= m_delay:
            dep += delay
            delayed = True
        prev[s] = dep
        log.append((t, k, s, gap, n, dep, t))
        s2 = (s + 1) % STOPS
        nxt = max(dep + RUN_OFF, last_arr[s2] + OVERTAKE_GAP)
        last_arr[s2] = nxt
        heapq.heappush(q, (nxt, k, s2, ts + step))
    return np.array(log)


TOY_LOG = toy_sim(M_DELAY, TOY_DELAY, (FF0 - TOY_T0) * TOY_V + 15)


def toy_m(t):
    return max(0.0, t - TOY_T0) * TOY_V


def m_off(t):
    """団子運転（なし）の画面の時刻（分）"""
    if t < FF0:
        return 0.0
    if t < FF1:
        return 180.0 * (t - FF0) / (FF1 - FF0)
    if t < T8:
        return 180.0 + 60.0 * (t - FF1) / (T8 - FF1)
    return min(240.0 + 2.0 * (t - T8), 262.0)


T5_A, T5_B, T5_END = S("c5_3"), S("c5_4"), E("g5")
_V1, _R = 4.0, 1.0
_M1 = _V1 * (T5_B - T5_A)
_VF = (T_END - _M1 - _V1 * _R / 2) / ((T5_END - T5_B) - _R / 2)


def m_on(t):
    """時間調整あり: 最初はゆっくり、c5_4 から 10時間ぶんを早回し"""
    if t < T5_A:
        return 0.0
    if t < T5_B:
        return _V1 * (t - T5_A)
    d = t - T5_B
    if d < _R:
        return _M1 + _V1 * d + (_VF - _V1) * d * d / (2 * _R)
    if t < T5_END:
        return _M1 + _V1 * _R + (_VF - _V1) * _R / 2 + _VF * (d - _R)
    return min(float(T_END) + 1.5 * (t - T5_END), T_END + 28.0)


def clock_on(t):
    """左上の時計を出している間"""
    return (FF0 - 0.2 <= t <= S("c4c_9") + 0.5) or (T5_A <= t <= E("c5_5") + 0.3)


def L_bunch(ctx, t):
    """4-3: 円い路線と6台のバス（前半は「遅れる → 人がたまる → 追いつく」の絵、後半は200回の1回ぶんの早回し）"""
    ctx.save()
    clip_left(ctx)
    t1, t2 = S("c4c_1"), S("c4c_2")
    # 時刻表（c4c_1）
    ca = fade(t, t1 + 0.2, 0.4) * (1 - clamp01((t - (t2 - 0.1)) / 0.4))
    if ca > 0:
        ctx.save()
        ctx.translate(505, 470)
        ctx.rotate(-0.02)
        ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * ca)
        rrect(ctx, -300 + 8, -230 + 12, 600, 460, 8)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 0.98, ca)
        rrect(ctx, -300, -230, 600, 460, 8)
        ctx.fill()
        ctx.restore()
        text(ctx, "時刻表", 505, 300, 50, INK, alpha=ca)
        for i, row in enumerate(("6:00　6:10　6:20", "6:30　6:40　6:50", "7:00　7:10　7:20")):
            text(ctx, row, 505, 395 + i * 72, 44, INK, alpha=ca * fade(t, t1 + 0.7 + 0.35 * i, 0.3))
        wr(ctx, "ずっと、このとおり？", 505, 640, 42, RED, t1 + 0.5 * dur("c4c_1"), t, align="center", alpha=ca) \
            if False else None
        q = fade(t, t1 + 0.55 * dur("c4c_1"), 0.4) * ca
        text(ctx, "ずっと、このとおり？", 505, 640, 42, RED, alpha=q)
    # 路線
    ra = fade(t, t2 + 0.2, 0.5)
    if ra > 0:
        n_show = min(BUSES, int(max(0.0, t - (t2 + 0.5)) / 0.55) + 1)
        if t < FF0:
            m = toy_m(t)
            angs = draw_ring(ctx, TOY_LOG, m, n_show, ra)
            _toy_labels(ctx, t, angs)
        else:
            m = m_off(t)
            angs = draw_ring(ctx, LOG_OFF, m, 6, 1.0)
            tc = S("c4c_7") + 0.55 * dur("c4c_7")
            if t >= tc:
                for gi, idx in enumerate(clusters(angs)):
                    if len(idx) >= 2:
                        circle_group(ctx, angs, idx, clamp01((t - tc - 0.3 * gi) / 0.5), 21 + gi)
            ts = S("c4c_9") + 0.5 * dur("c4c_9")
            if t >= ts:
                q = ease_out((t - ts) / 0.3)
                sticky(ctx, "団子運転", RC[0] + 62, RC[1], 54, "pink", fg=RED, a=q, tilt=-0.03)
    if clock_on(t) and t >= FF0 - 0.2:
        clock_face(ctx, m_off(t), fade(t, FF0 - 0.2, 0.3))
    ctx.restore()


def _toy_labels(ctx, t, angs):
    t4, t5, t6 = S("c4c_4"), S("c4c_5"), S("c4c_6")
    d4 = dur("c4c_4")
    if t4 + 0.5 <= t < t4 + 0.55 * d4:
        a = fade(t, t4 + 0.5, 0.3)
        pen_circle(ctx, *ring_xy(angs[0], RR), 40, 30, RED, seed=31, width=6, alpha=a)
        ring_label(ctx, angs[0], "遅れた1台", 32, RED, a)
    elif t4 + 0.55 * d4 <= t < t5:
        ang = angs[0] + 0.22
        ring_label(ctx, ang, "人がたまる", 32, RED, fade(t, t4 + 0.55 * d4, 0.3))
    elif t5 <= t < t6:
        a = fade(t, t5, 0.3)
        pen_circle(ctx, *ring_xy(angs[0], RR), 40, 30, RED, seed=31, width=6, alpha=a)
        ring_label(ctx, angs[0], "さらに遅れる", 32, RED, a)
    elif t6 <= t < FF0:
        a = fade(t, t6, 0.3)
        pen_circle(ctx, *ring_xy(angs[5], RR + 14), 40, 30, INK, seed=33, width=6, alpha=a)
        ring_label(ctx, angs[5], "後ろのバス", 32, INK, a)


# ---------- 5章: 時間調整 ----------
def L_fix(ctx, t):
    ctx.save()
    clip_left(ctx)
    tc = T5_A
    a_on = fade(t, tc, 0.5)
    if a_on < 1:                                     # 団子になったままの路線
        grp(ctx, 1 - a_on, draw_ring, LOG_OFF, m_off(t), 6, 1.0)
    if a_on > 0:
        grp(ctx, a_on, draw_ring, LOG_ON, m_on(t), 6, 1.0, True)
    # 放送（c5_2）
    t2 = S("c5_2")
    q = fade(t, t2 + 0.35 * dur("c5_2"), 0.3) * (1 - clamp01((t - (T5_A - 0.1)) / 0.3))
    if q > 0:
        sticky(ctx, "「時間調整のため、\nしばらく停車します」", RC[0], RC[1], 40, "blue", a=q, tilt=-0.02)
    # 旗の説明（c5_3〜）
    q = fade(t, T5_A + 0.5, 0.4)
    if q > 0:
        text(ctx, "旗の停留所で、\n早く着いたら待つ", RC[0], RC[1], 32, INK, alpha=q * (1 - clamp01((t - T5_B - 2.0) / 0.4)))
    q = fade(t, E("g5") - 0.5, 0.5)
    if q > 0:
        text(ctx, "6台とも、\n等間隔のまま", RC[0], RC[1], 36, RED, alpha=q)
    if T5_A <= t <= E("c5_5") + 0.3 or t < FF1 + 40 and clock_on(t):
        clock_face(ctx, m_on(t) if t >= T5_A else m_off(t), 1.0 if t >= T5_A else 0.0)
    ctx.restore()


# ---------- 6章: 実際のバスでは？（コードは動画では見せない。概要欄だけ） ----------
def L_real(ctx, t):
    """6章: 最初に見た、いちばん単純なバス停（バス停・待つ人・バス1台）"""
    ctx.save()
    clip_left(ctx)
    ctx.push_group()
    road(ctx)
    walker(ctx, P_X + 20, 330, t, moving=False)
    bus_shape(ctx, 670, GROUND, 128)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(fade(t, S("ch7") + 0.1, 0.4))
    ctx.restore()


# ---------- 7章: まとめ ----------
def two_gap(ctx, t, x0, x1, ly, t_dots, a=1.0, t_counts=None, bus_h=34):
    """すき間が 2分 と 18分 の2つだけ。人を1分に1人ずつ、でたらめに落とす（点は待った時間で青→赤）"""
    ppm = (x1 - x0) / (GAP_SHORT + GAP_LONG)
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.move_to(x0 - 25, ly)
    ctx.line_to(x1 + 25, ly)
    ctx.stroke()
    for m in (0.0, GAP_SHORT, GAP_SHORT + GAP_LONG):
        bus_icon(ctx, x0 + m * ppm, ly + bus_h + 8, bus_h, a)
    n = int(GAP_SHORT + GAP_LONG)
    for i in range(n):
        q = fade(t, t_dots + 0.07 * i, 0.2)
        if q <= 0:
            continue
        m = i + 0.5
        wait = (GAP_SHORT - m) if m < GAP_SHORT else (GAP_SHORT + GAP_LONG - m)
        c = person_color(wait)
        ctx.set_source_rgba(c[0], c[1], c[2], 0.95 * a * q)
        ctx.arc(x0 + m * ppm, ly - 30 - 14 * (1 - q), 7.5, 0, 2 * math.pi)
        ctx.fill()
    if t_counts is not None and t >= t_counts:
        q = fade(t, t_counts, 0.3) * a
        for g0, g1, lab in ((0.0, GAP_SHORT, "2人"), (GAP_SHORT, GAP_SHORT + GAP_LONG, "18人")):
            pen_line(ctx, x0 + g0 * ppm + 4, ly - 62, x0 + g1 * ppm - 4, ly - 62, PENCIL, seed=7, width=4,
                     progress=clamp01((t - t_counts) / 0.4), alpha=a)
            text(ctx, lab, x0 + (g0 + g1) / 2 * ppm, ly - 94, 32, INK, alpha=q)


def L_end(ctx, t):
    ctx.save()
    clip_left(ctx)
    road(ctx)
    walker(ctx, P_X + 40, 330, t, moving=False)
    t2 = S("c7_2")
    if t >= t2:
        a = fade(t, t2, 0.3)
        text(ctx, "すき間が 2分 と 18分 のとき", 505, 150, 32, PENCIL, bold=False, alpha=a)
        two_gap(ctx, t, 150, 860, 330, t2 + 0.3, a, t_counts=t2 + 0.3 + 0.07 * 20 + 0.2)
    ctx.restore()



# ============================================================
# 右ページ（手書きの見出し・式・グラフ）
# ============================================================
RX = 1050


def R_stop(ctx, t):
    """0章・1章"""
    tc1 = S("c1_1")
    a = 1 - clamp01((t - (tc1 - 0.15)) / 0.4)
    if a > 0:
        rules = (("c0_2", "バスは平均10分おき"), ("c0_3", "間隔はバラバラ"), ("c0_4", "人はでたらめな時刻に来る"))
        for i, (cid, s) in enumerate(rules):
            y = 200 + 125 * i
            t0 = S(cid) + 0.3
            if t >= t0:
                pen_circle(ctx, RX + 26, y, 27, 27, INK, seed=60 + i, width=4, progress=clamp01((t - t0) / 0.3), alpha=a)
                text(ctx, "123"[i], RX + 26, y, 34, INK, alpha=a * fade(t, t0 + 0.1, 0.2))
            wr(ctx, s, RX + 78, y, 46, INK, t0 + 0.15, t, alpha=a)
    if t >= tc1:
        s = "平均10分おきのバス、\n平均何分待つ？"
        t0 = tc1 + 0.2
        wr(ctx, s, RX, 215, 52, INK, t0, t, cps=8)
        pen_line(ctx, RX - 4, 292, RX + 530, 288, RED, seed=5, width=7,
                 progress=clamp01((t - t0 - lf.write_dur(s, 8)) / 0.4))
    t3 = S("c1_3")
    if t >= t3:
        wr(ctx, "バスとバスの間は 平均10分", RX, 385, 40, INK, t3 + 0.2, t)
        wr(ctx, "待つのは、その半分？", RX, 445, 40, INK, t3 + 0.55 * dur("c1_3"), t)
    t4 = S("c1_4")
    if t >= t4:
        pre = "10 ÷ 2 ＝ "
        wr(ctx, pre + "5 ？", RX, 580, 74, INK, t4 + 0.05, t, cps=8)
        w0, w5 = text_width(pre, 74), text_width("5", 74)
        pen_circle(ctx, RX + w0 + w5 / 2, 580, 50, 54, RED, seed=15, width=7,
                   progress=clamp01((t - (t4 + 0.05 + lf.write_dur(pre + "5 ？", 8) - 0.2)) / 0.4))


# ---------- 2章 ----------
MINI_X0, MINI_X1, MINI_H = 1060, 1430, 42
_MINI = {}


def mini_surface(k):
    s = _MINI.get(k)
    if s is None:
        bus, arr, wait, _kn = DAYS[k]
        w = MINI_X1 - MINI_X0
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w + 10, MINI_H + 14)
        c = cairo.Context(s)
        jit = np.random.default_rng(SEED_DAYS[k]).uniform(0, MINI_H, len(arr))
        cols = _colors(wait)
        for i in range(len(arr)):
            c.set_source_rgba(cols[i, 0], cols[i, 1], cols[i, 2], 0.75)
            c.arc(5 + arr[i] / T_ALL * w, MINI_H + 5 - jit[i], 1.3, 0, 2 * math.pi)
            c.fill()
        _MINI[k] = s
    return s


_RUN_MEAN = np.cumsum(WAIT[ORDER2]) / np.arange(1, N + 1)   # 落ちた順の「ここまでの平均」


def R_crowd(ctx, t):
    t1 = S("c2_1")
    wr(ctx, "10時間の間に、1万人が\n思い思いの時刻に来る", RX, 190, 48, INK, t1 + 0.3, t, cps=8)
    # 2026-10-04 初見チェック「声のない20秒がいちばん離脱しそう」→ 落ちている間、右ページで途中の平均を動かす
    n = m_count(t)
    q = fade(t, RAMP0, 0.4) * (1 - fade(t, S("c2_2") - 0.2, 0.3))
    if n > 0 and q > 0:
        text(ctx, "ここまでの平均の待ち", 1400, 420, 30, PENCIL, bold=False, alpha=q)
        text(ctx, f"{_RUN_MEAN[n - 1]:.1f}分", 1400, 500, 84, RED, alpha=q)
        text(ctx, "予想は 5分", 1400, 590, 30, PENCIL, bold=False, alpha=q)
    t4, t5 = S("c2_4"), S("c2_5")
    if t >= t4:
        wr(ctx, "別の日のバス停", RX, 335, 36, INK, t4 + 0.1, t)
    starts = [t4 + 0.8, t4 + 1.9, t5 + 0.1]
    for k in range(3):
        ts = starts[k]
        if t < ts:
            continue
        y = 440 + 92 * k
        p = clamp01((t - ts) / 0.8)
        ctx.save()
        ctx.rectangle(MINI_X0 - 6, y - 80, (MINI_X1 - MINI_X0 + 12) * p, 100)
        ctx.clip()
        ctx.set_source_surface(mini_surface(k), MINI_X0 - 5, y - (MINI_H + 8))
        ctx.paint()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(3)
        ctx.move_to(MINI_X0, y)
        ctx.line_to(MINI_X1, y)
        ctx.stroke()
        ctx.restore()
        q = fade(t, ts + 0.85, 0.3)
        if q > 0:
            text(ctx, "平均の待ち", 1580, y - 48, 26, PENCIL, bold=False, alpha=q)
            text(ctx, f"{float(DAYS[k][2].mean()):.1f}分", 1675, y - 12, 52, INK, alpha=q)


# ---------- 3章 ----------
def R_one(ctx, t):
    t1 = S("c3_1")
    wr(ctx, "長く待つ人は、\nどこに着いた？", RX, 180, 46, INK, t1 + 0.3, t)
    t4, t5, t6, t7 = S("c3_4"), S("c3_5"), S("c3_6"), S("c3_7")
    if t >= t4:
        wr(ctx, "すき間が 2分と18分だけなら", RX, 292, 36, INK, t4 + 0.2, t)
        t_dots = t5 + 0.5
        t_cnt = t_dots + 0.07 * 20 + 0.2
        two_gap(ctx, t, 1070, 1780, 450, t_dots, fade(t, t4 + 0.9, 0.3), t_counts=t_cnt)
        if t >= t_cnt + 0.5:
            text(ctx, "9倍", 1580, 356, 38, RED, alpha=fade(t, t_cnt + 0.5, 0.3))
    ppm = (1780 - 1070) / 20.0
    if t >= t6:
        # 平均の待ち（それぞれのすき間の真ん中から、次のバスまで）
        yd = 535
        for (m0, m1, lab, x_lab, al, k) in ((1.0, 2.0, "短いすき間\n平均1分待ち", 1030, "left", 0),
                                              (11.0, 20.0, "長いすき間\n平均9分待ち", 1620, "center", 1)):
            tt = t6 + (0.55 if k == 0 else 0.0) * dur("c3_6") + (0.1 if k == 1 else 0.0)
            if t >= tt:
                pen_line(ctx, 1070 + m0 * ppm, yd, 1070 + m0 * ppm + (m1 - m0) * ppm * clamp01((t - tt) / 0.5), yd,
                         RED, seed=30 + k, width=6)
                wr(ctx, lab, x_lab, 585, 28, RED if k == 1 else INK, tt + 0.2, t, align=al)
    if t >= t7:
        f = "(2×1 ＋ 18×9) ÷ 20 ＝ 8.2"
        wr(ctx, f, RX, 668, 44, INK, t7 + 0.05, t, cps=8)
        pre = "(2×1 ＋ 18×9) ÷ 20 ＝ "
        w0, w8 = text_width(pre, 44), text_width("8.2", 44)
        pen_circle(ctx, RX + w0 + w8 / 2, 668, 52, 34, RED, seed=17, width=6,
                   progress=clamp01((t - (t7 + 0.05 + lf.write_dur(f, 8) - 0.1)) / 0.4))


# ---------- 4-1 ----------
def R_sched(ctx, t):
    t1, t2, t3 = S("c4a_1"), S("c4a_2"), S("c4a_3")
    wr(ctx, "バスが時刻表どおり\n10分おきなら？", RX, 180, 46, INK, t1 + 0.3, t)
    ppm = (1780 - 1070) / 20.0
    ly = 440
    a = fade(t, t1 + 0.6, 0.3)
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.move_to(1045, ly)
    ctx.line_to(1805, ly)
    ctx.stroke()
    for m in (0, 10, 20):
        bus_icon(ctx, 1070 + m * ppm, ly + 42, 34, a)
    for i in range(20):
        q = fade(t, t1 + 1.0 + 0.05 * i, 0.2)
        if q > 0:
            c = person_color(10 - (i % 10 + 0.5))
            ctx.set_source_rgba(c[0], c[1], c[2], 0.95 * q)
            ctx.arc(1070 + (i + 0.5) * ppm, ly - 30 - 12 * (1 - q), 7.5, 0, 2 * math.pi)
            ctx.fill()
    if t >= t2 + 0.5:
        for k in range(2):
            x0 = 1070 + (10 * k + 5) * ppm
            pen_line(ctx, x0, ly + 85, x0 + 5 * ppm * clamp01((t - t2 - 0.5) / 0.5), ly + 85, RED, seed=40 + k, width=6)
            text(ctx, "平均5分", x0 + 2.5 * ppm, ly + 125, 32, RED, alpha=fade(t, t2 + 0.9, 0.3))
    wr(ctx, "半分になるのは、\nすき間がそろっているときだけ", RX, 625, 38, INK, t3 + 0.15, t)


# ---------- 4-2 ----------
def R_noise(ctx, t):
    t1 = S("c4b_1")
    wr(ctx, "現実のバスは、\nきっちりと でたらめの中間", RX, 180, 42, INK, t1 + 0.3, t)
    for i, (sd, w) in enumerate(zip(SD_LIST, SHOW_SD)):
        q = fade(t, SD_T[i] + 0.1, 0.25)
        y = 280 + 46 * i
        text(ctx, f"乱れ {sd}分", RX, y, 38, INK, align="left", alpha=q)
        text(ctx, f"→ {w:.1f}分", RX + 290, y, 38, RED, align="left", alpha=q)
    tf = S("g4b") + 0.1
    if t >= tf:
        wr(ctx, "平均の待ち ＝\n5 ×（1 ＋（乱れ÷10）²）", RX, 612, 40, INK, tf, t, cps=9)


# ---------- 4-3 ----------
CH_BASE, CH_TOP, CH_MAX = 650, 440, 30.0
CH_X0, CH_DX = 1075, 70


def set_scale(vmax):
    """棒グラフの縦軸の最大（4-3 は 20分、5章は 10時間ぶんなので 60分）"""
    global CH_MAX
    CH_MAX = vmax


def chart_axes(ctx, a, title):
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(4)
    ctx.move_to(1050, CH_BASE)
    ctx.line_to(1795, CH_BASE)
    ctx.stroke()
    for h in range(1, 11):
        text(ctx, f"{h}", CH_X0 + (h - 0.5) * CH_DX, CH_BASE + 28, 26, PENCIL, bold=False, alpha=a)
    for v in (CH_MAX / 3, CH_MAX * 2 / 3, CH_MAX):
        y = CH_BASE - v / CH_MAX * (CH_BASE - CH_TOP)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.3 * a))
        ctx.set_line_width(1.5)
        ctx.move_to(1050, y)
        ctx.line_to(1795, y)
        ctx.stroke()
    text(ctx, title, RX, 410, 28, INK, align="left", bold=False, alpha=a)


def chart_bar(ctx, h, v, col, a, off=0.0, w=44.0, label=False, lab_dx=0.0):
    if a <= 0.003 or v <= 0:
        return
    x = CH_X0 + (h - 0.5) * CH_DX + off
    hg = v / CH_MAX * (CH_BASE - CH_TOP)
    ctx.set_source_rgba(*hexrgb(col, 0.9))
    rrect(ctx, x - w / 2, CH_BASE - hg, w, hg, 4)
    ctx.fill()
    if label:
        text(ctx, f"{v:.1f}", x + lab_dx, CH_BASE - hg - 20, 26, INK, alpha=a)


def t_reach(fn, m, lo, hi):
    for _ in range(40):
        mid = (lo + hi) / 2
        if fn(mid) >= m:
            hi = mid
        else:
            lo = mid
    return hi


WO = wait_by_hour(LOG_OFF)                           # 画面の1回（なし）の1〜10時間目
WN = wait_by_hour(LOG_ON)                            # 画面の1回（あり）
T_BAR_OFF = [t_reach(m_off, 60.0 * h, FF0, T8 + 0.01) for h in range(1, 5)]
T_BAR_ON = [t_reach(m_on, 60.0 * h, T5_A, T5_END) for h in range(1, 11)]


def R_bunch(ctx, t):
    set_scale(20.0)
    t1, t2, t3 = S("c4c_1"), S("c4c_2"), S("c4c_3")
    wr(ctx, "時刻表どおりに出したバスは？", RX, 160, 44, INK, t1 + 0.3, t, cps=8)
    wr(ctx, "20停留所・6台・10分おき", RX, 222, 34, INK, t2 + 0.5, t)
    if t >= t3:
        a = fade(t, t3, 0.3)
        ctx.save()
        ctx.translate(0, 0)
        text(ctx, "ルール", RX + 5, 275, 28, RED, align="left", alpha=a)
        wr(ctx, "待っている人が多いほど、\n乗るのに時間がかかる", RX + 20, 340, 38, INK, t3 + 0.2, t)
        p = clamp01((t - t3 - 0.2) / 0.8)
        x0, x1, y0, y1 = 1038, 1560, 295, 388
        for (xa, ya, xb, yb, sd) in ((x0, y0, x1, y0, 51), (x1, y0, x1, y1, 52), (x1, y1, x0, y1, 53), (x0, y1, x0, y0, 54)):
            pen_line(ctx, xa, ya, xb, yb, PENCIL, seed=sd, width=3, progress=p, alpha=a)
        ctx.restore()
    if t >= FF0 - 0.3:
        a = fade(t, FF0 - 0.3, 0.4)
        chart_axes(ctx, a, "1時間ごとの平均の待ち（分）")
        for h in range(1, 5):
            g = ease_out(clamp01((t - T_BAR_OFF[h - 1]) / 0.6))
            chart_bar(ctx, h, WO[h - 1] * g, RED, g, label=(g > 0.95))


# ---------- 5章 ----------
def R_fix(ctx, t):
    set_scale(60.0)
    t1, t3, t5 = S("c5_1"), S("c5_3"), S("c5_5")
    wr(ctx, "時間調整をすると？", RX, 160, 46, INK, t1 + 0.3, t)
    a3 = 1 - clamp01((t - (t5 - 0.1)) / 0.3)
    if t >= t3:
        wr(ctx, "予定より早く着いたら、\n決まった停留所で待つ", RX, 262, 38, INK, t3 + 0.2, t, alpha=a3)
    if t >= t5:
        wr(ctx, "後ろのバスとの間を\n守るための待ち時間", RX, 262, 38, RED, t5 + 0.2, t)
    tb = T5_B - 0.2
    if t >= tb:
        a = fade(t, tb, 0.4)
        legend_at(ctx, [(RED, "時間調整なし"), (COLD, "あり")], 1415, 365, 28)
        chart_axes(ctx, a, "1時間ごとの平均の待ち（分）")
        for h in range(1, 11):
            ga = ease_out(clamp01((t - (T_BAR_ON[h - 1])) / 0.6))
            go = 1.0 if h <= 4 else ga
            chart_bar(ctx, h, WO[h - 1] * go * a, RED, go * a, off=-17, w=30, label=(h == 4 or h == 10) and go > 0.95)
            chart_bar(ctx, h, WN[h - 1] * ga, COLD, ga, off=17, w=30, label=(h == 10) and ga > 0.95, lab_dx=14)


# ---------- 6章 ----------
def R_real(ctx, t):
    t1, t2a, t2b = S("c6_1"), S("c6_2a"), S("c6_2b")
    wr(ctx, "いちばん単純な形のバス停", RX, 165, 46, INK, t1 + 0.3, t)
    wr(ctx, "・実際のバスは、時刻表に沿って走る", RX, 270, 38, INK, t2a + 0.2, t)
    wr(ctx, "・時刻表を見て来る人は、もっと短い", RX, 335, 38, INK, t2b + 0.1, t)


# ---------- 7章 ----------
def R_end(ctx, t):
    t1, t2 = S("c7_1"), S("c7_2")
    # 2026-10-04 ユーザー「長いすき間ほど、その中に来る人が多い」の意味が分からない → 「あなた」を主語に言い直した
    wr(ctx, "待つときに限って、バスが来ない？", RX, 180, 46, INK, t1 + 0.3, t)
    wr(ctx, "バスが来ない長い時間ほど、\nそこに着く人が多い", RX, 330, 44, INK, t2 + 0.2, t)
    t3 = S("c7_2b")
    wr(ctx, "→ あなたも、そこに着きやすい", RX, 428, 44, RED, t3 + 0.1, t)
    p = clamp01((t - t3 - 0.1 - lf.write_dur("→ あなたも、そこに着きやすい")) / 0.4)
    pen_line(ctx, RX - 4, 462, RX + 640, 458, RED, seed=71, width=7, progress=p)


# ============================================================
# 右ページ下の「2つの数字」（2章で出てから最後まで）
# ============================================================
NB = (1030, 712, 1800, 905)
CELLX = (1222, 1608)
LBL_Y, VAL_Y = 750, 842
_MEAN_W, _MEAN_G, _MEAN_GO = float(WAIT.mean()), float(GAPS.mean()), float(GAP_OF.mean())


def _sd_i(t):
    return max(0, sum(1 for x in SD_T if x <= t) - 1)


def _v_main(t):
    return f"{_MEAN_W * ease_out(clamp01((t - S('c2_2') - 0.25) / 0.8)):.1f}分"


def _v_gap(t):
    return f"{_MEAN_G * ease_out(clamp01((t - S('c2_3') - 0.25) / 0.8)):.1f}分"


def _v_wait_ring(t):
    if t < FF0:
        return "5.0分"
    w240 = wait_now(LOG_OFF, 240.0)
    if t < T5_A:
        return f"{wait_now(LOG_OFF, min(m_off(t), 240.0)):.1f}分"
    u = ease(clamp01((t - T5_A) / 0.8))
    return f"{lerp(w240, wait_now(LOG_ON, min(m_on(t), float(T_END))), u):.1f}分"


def _v_gap2(t):
    if t < S("c4a_1") + 2.6:
        return f"{_MEAN_GO:.1f}分"
    if t < SD_T[0]:
        return "10.0分"
    return f"{2 * SHOW_SD[_sd_i(t)]:.1f}分"


def _v_clock(t):
    if t < FF0:
        return "0:00"
    if t < T5_A:
        return clock_str(min(m_off(t), 240.0))
    return clock_str(min(m_on(t), float(T_END)))


LEFT_STATES = [
    (S("c2_2"), "1万人の平均の待ち", _v_main),
    (S("c4a_2") + 0.1, "時刻表どおりの平均の待ち", lambda t: "5.0分"),
    (SD_T[0] - 0.4, lambda t: f"平均の待ち（乱れ {SD_LIST[_sd_i(t)]}分）", lambda t: f"{SHOW_SD[_sd_i(t)]:.1f}分"),
    (S("c4c_2") + 1.0, "平均の待ち（直近60分）", _v_wait_ring),
    (S("c7_1") + 0.3, "1万人の平均の待ち", lambda t: "10.0分"),
]
RIGHT_STATES = [
    (S("c2_3"), "バスの間隔の平均", _v_gap),
    (S("c3_9") + 0.55 * dur("c3_9"), "待つ人から見たすき間の平均", _v_gap2),
    (S("c4a_1") + 2.6, "待つ人から見たすき間の平均", _v_gap2),
    (S("c4c_2") + 1.0, "経過時間", _v_clock),
    (S("c7_1") + 0.3, "バスの間隔の平均", lambda t: "10.0分"),
]


def draw_cell(ctx, cx, states, t, a, col):
    idx = -1
    for i, st in enumerate(states):
        if t >= st[0]:
            idx = i
    if idx < 0:
        return
    t0, lab, val = states[idx]
    age = t - t0
    ls = lab(t) if callable(lab) else lab
    swap = idx > 0
    if swap and age < 1.0:
        _p0, plab, pval = states[idx - 1]
        pl = plab(t0 - 0.01) if callable(plab) else plab
        pv = pval(t0 - 0.01)
        fo = 1 - clamp01((age - 0.35) / 0.45)
        text(ctx, pl, cx, LBL_Y, 28, PENCIL, bold=False, alpha=a * fo)
        text(ctx, pv, cx, VAL_Y, 84, INK, alpha=a * fo)
        pen_line(ctx, cx - 150, VAL_Y + 2, cx + 150, VAL_Y - 8, RED, seed=7 + idx, width=7,
                 progress=clamp01(age / 0.3), alpha=a * fo)
    ag = age - (0.85 if swap else 0.0)
    if ag > 0:
        lf.write_on(ctx, ls, cx, LBL_Y, 28, PENCIL, clamp01(ag / (len(ls) / 12.0)), align="center", bold=False, alpha=a)
        text(ctx, val(t), cx, VAL_Y, 84, col, alpha=a * ease_out((ag - 0.1) / 0.3))


def draw_numbers(ctx, t):
    t0 = S("c2_2")
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3)
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.5 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to((x0 + x1) / 2, y0 + 20)
    ctx.line_to((x0 + x1) / 2, y1 - 20)
    ctx.stroke()
    draw_cell(ctx, CELLX[0], LEFT_STATES, t, a, RED)
    draw_cell(ctx, CELLX[1], RIGHT_STATES, t, a, INK)


# ============================================================
# 付箋・章カード・終了画面・全体
# ============================================================
def overlays(ctx, t, idx):
    # 章の始まり: 付箋（1章は「1万人モード」の亀つきの合図）
    if idx == CH_CROWD:
        t0 = S("ch1")
        a = fade(t, t0 + 0.15, 0.3) * (1 - clamp01((t - (S("c2_1") + 0.5)) / 0.4))
        if a > 0:
            note.banner(ctx, "1万人で待ってみる", lf.GUTTER, 470, a=a, t_rel=t - t0)
    elif idx != CH_STOP:
        lf.chapter_card_at(ctx, t, tl, hold=2.0, size=60)
    # 待ち時間のパラドックス
    ts = S("c3_12") + 0.45 * dur("c3_12")
    if ts <= t < S("ch3") + 0.1:
        a = fade(t, ts, 0.3) * (1 - clamp01((t - (E("c3_12") + 0.6)) / 0.4))
        if a > 0:
            sticky(ctx, "待ち時間のパラドックス", lf.GUTTER, 540, 60, "mint", a=a, tilt=-0.02)
    # 締めの問いかけ
    tq = S("c7_3") + 0.05
    t4 = S("c7_4")
    if t >= tq:
        a = fade(t, tq, 0.35) * (1 - fade(t, t4 - 0.1, 0.3))
        if a > 0:
            sticky(ctx, "あなたの使うバスでは、\n時間調整、ありますか？", lf.GUTTER, 575, 56, "yellow", a=a, tilt=-0.02)
    # チャンネル登録・高評価のお願い（亀と付箋。言い終わって約2秒で終わる）
    if t >= t4:
        from engine.brand import turtle
        a = fade(t, t4 + 0.1, 0.4)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.82 * fade(t, t4 - 0.1, 0.4)))      # 後ろの絵をうすく沈めて、亀と付箋を見せる
        ctx.rectangle(0, 0, lf.W, lf.H)
        ctx.fill()
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t4) % 3.2 < 0.45 else 0.0
        turtle(ctx, lf.GUTTER - 5, 545, 0.62, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        sticky(ctx, "チャンネル登録・高評価 よろしくお願いします", lf.GUTTER, 640, 46, "pink", fg=INK,
               a=fade(t, t4 + 0.3, 0.4), tilt=-0.015)


LEFTS = [L_stop, L_crowd, L_one, L_sched, L_noise, L_bunch, L_fix, L_real, L_end]
RIGHTS = [R_stop, R_crowd, R_one, R_sched, R_noise, R_bunch, R_fix, R_real, R_end]


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:                       # 前の章の絵が、すっと消える
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    ea = 1.0
    if ea > 0.003:
        grp(ctx, ea, page, LEFTS, idx, t0) if False else None
        ctx.push_group()
        page(ctx, t, LEFTS, idx, t0)
        page(ctx, t, RIGHTS, idx, t0)
        draw_numbers(ctx, t)
        overlays(ctx, t, idx)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ea)
    lf.subtitle(ctx, t, tl)



# ============================================================
# 音（BGM は 0秒から。効果音は控えめ）
# ============================================================
def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.2), 1.0, bgm=True)
    for i in range(2, 9):                                           # 章の始まり
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    # 0〜1章
    for cid in ("c0_2", "c0_3", "c0_4"):
        mx.add(S(cid) + 0.3, blip(659.3, 0.12), 0.4)
    mx.add(T_CNT0, whoosh(T_CNT1 - T_CNT0, np.random.default_rng(5)), 0.15)
    mx.add(T_CNT1 - 0.1, brake(), 0.5)
    mx.add(S("c0_6") + 0.2, bell(523.3, 0.9), 0.4)
    mx.add(S("c1_3") + 0.78 * dur("c1_3"), blip(659.3, 0.12), 0.4)
    mx.add(S("c1_4") + 0.9, bell(392.0, 0.9), 0.4)
    # 2章（1万人モード）
    mx.add(S("ch1") + 0.15, riser(0.9), 0.5)
    beat(mx, M_T0, M_T1, bpm=124, vol=0.22, accel=True)
    mx.add(M_T0, shimmer(400, M_T1 - M_T0, seed=2), 0.35)
    mx.add(M_T1, thump(), 0.7)
    mx.add(M_T1 + 0.2, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(S("c2_2") + 0.3, bell(880.0, 1.2), 0.45)
    mx.add(S("c2_3") + 0.3, bell(659.3, 1.0), 0.4)
    for ts in (S("c2_4") + 0.8, S("c2_4") + 1.9, S("c2_5") + 0.1):
        mx.add(ts, blip(784.0, 0.12), 0.4)
    # 3章
    t1 = S("c3_1")
    mx.add(t1, whoosh(1.2), 0.3)
    mx.add(t1 + 1.3, bell(880.0, 1.2), 0.45)
    mx.add(S("c3_2") + 0.5, blip(523.3, 0.12), 0.4)
    mx.add(S("c3_2") + 1.8, bell(659.3, 1.0), 0.35)
    mx.add(S("c3_5") + 0.5 + 0.07 * 20, blip(784.0, 0.12), 0.4)
    mx.add(S("c3_6") + 0.1, blip(659.3, 0.12), 0.4)
    mx.add(S("c3_7") + 0.9, bell(880.0, 1.2), 0.45)
    mx.add(S("c3_9"), whoosh(1.2), 0.25)
    mx.add(S("c3_9") + 0.55 * dur("c3_9"), bell(784.0, 1.2), 0.4)
    mx.add(S("c3_12") + 0.45 * dur("c3_12"), chord([392.0, 493.9, 587.3], 1.2), 0.45)
    # 4-1・4-2
    mx.add(S("c4a_1") + 0.9, whoosh(1.6), 0.25)
    mx.add(S("c4a_2") + 0.1, bell(880.0, 1.2), 0.45)
    for i, ts in enumerate(SD_T):
        mx.add(ts, blip(523.3 * 2 ** (i / 12 * 2), 0.12), 0.4)
    mx.add(T_CURVE, whoosh(1.5), 0.25)
    # 4-3
    for k in range(BUSES):
        mx.add(S("c4c_2") + 0.5 + 0.55 * k, blip(523.3 * 2 ** (k / 12 * 2), 0.1), 0.3)
    mx.add(S("c4c_4") + 0.3, thump(), 0.4)
    mx.add(FF0 - 0.3, riser(1.0), 0.45)
    mx.add(FF0, whoosh(FF1 - FF0, np.random.default_rng(7)), 0.12)
    mx.add(S("c4c_7") + 0.55 * dur("c4c_7"), chord([261.6, 311.1, 392.0], 1.4), 0.4)
    mx.add(S("c4c_9") + 0.5 * dur("c4c_9"), chord([392.0, 493.9, 587.3], 1.2), 0.45)
    # 5章
    t2 = S("c5_2") + 0.35 * dur("c5_2")
    mx.add(t2, bell(784.0, 1.0), 0.4)
    mx.add(t2 + 0.25, bell(659.3, 1.0), 0.4)
    mx.add(T5_A + 0.3, blip(659.3, 0.12), 0.4)
    mx.add(T5_B - 0.2, riser(1.0), 0.4)
    mx.add(T5_B, whoosh(T5_END - T5_B, np.random.default_rng(9)), 0.12)
    mx.add(T5_END, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    # 6章
    mx.add(S("c6_2a") + 0.2, blip(659.3, 0.12), 0.4)
    mx.add(S("c6_2b") + 0.1, blip(784.0, 0.12), 0.4)
    # 7章
    mx.add(S("c7_3") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S("c7_4") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻（章ごとに要所を2枚以上）
# ============================================================
def still_times():
    ts = [0.0, 0.3, 1.0, S("c0_3") + 4.0, S("c0_4") + 2.0, S("c0_5") + 1.8, S("c0_6") + 1.0,
          S("c1_1") + 3.5, S("c1_3") + 0.78 * dur("c1_3") + 0.8, S("c1_4") + 2.6,
          S("ch1") + 1.2, S("c2_1") + 5.0, APP[0] + 0.5, BAR0[0] + 1.2, APP[2] + 1.8, APP[3] + 1.8, T_B + 0.2 * D_B, CT0 + 1.0, RAMP0 + 1.5, RAMP1 + 0.2, FOLD0 + 1.0, FOLD1 + 0.3, FOLD1 + 4.0, M_T1 - 1.0, E("g2") - 0.2, S("c2_2") + 1.8, S("c2_3") + 1.6,
          S("c2_4") + 2.8, S("c2_5") + 1.8,
          S("c3_1") + 2.0, S("c3_1") + 0.9 * dur("c3_1"), S("c3_2") + 0.9 * dur("c3_2"), S("c3_4") + 3.0,
          S("c3_5") + 0.9 * dur("c3_5"), S("c3_6") + 0.9 * dur("c3_6"), S("c3_7") + 0.9 * dur("c3_7"),
          S("c3_9") + 0.9 * dur("c3_9"), S("c3_11") + 1.8, S("c3_12") + 0.8 * dur("c3_12"),
          S("ch3") + 0.8, S("c4a_1") + 2.0, S("c4a_2") + 1.6, S("c4a_3") + 0.9 * dur("c4a_3"),
          S("ch4") + 0.8, S("c4b_3") + 0.9 * dur("c4b_3"), E("c4b_4") + 0.2, E("g4b") - 0.2,
          S("ch5") + 0.8, S("c4c_1") + 2.5, S("c4c_2") + 3.5, S("c4c_3") + 0.9 * dur("c4c_3"),
          S("c4c_4") + 0.8, S("c4c_4") + 0.9 * dur("c4c_4"), S("c4c_5") + 0.9 * dur("c4c_5"),
          S("c4c_6") + 0.9 * dur("c4c_6"), FF0 + 6.0, FF0 + 14.0, FF1 - 0.2, S("c4c_7") + 0.9 * dur("c4c_7"),
          S("c4c_8") + 0.9 * dur("c4c_8"), S("c4c_9") + 0.9 * dur("c4c_9"),
          S("ch6") + 0.8, S("c5_2") + 0.9 * dur("c5_2"), S("c5_3") + 0.9 * dur("c5_3"), S("c5_4") + 4.0,
          E("g5") - 3.0, E("g5") - 0.2, S("c5_5") + 0.8 * dur("c5_5"),
          S("ch7") + 0.8, S("c6_2a") + 0.9 * dur("c6_2a"), S("c6_2b") + 0.9 * dur("c6_2b"),
          S("ch8") + 0.8, S("c7_1") + 1.0, S("c7_2") + 0.9 * dur("c7_2"), S("c7_3") + 1.5,
          S("c7_4") + 1.5, S("c7_5") + 0.9 * dur("c7_5") + 1.0]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


_QUICK = any(a in sys.argv for a in ("--stills", "--preview"))   # 静止画・確認用の動画のときは、数字の照合を飛ばす（本番は先に照合する）
if __name__ == "__main__" and not _QUICK:
    t_start = time.time()
    print(f"0章の1人: seed={SEED_ONE} 着いた={ARR0:.1f}分 待ち={WAIT0:.2f}分 直前のバス={PREV0:.1f} 次のバス={NEXT0:.1f} "
          f"（すき間 {NEXT0 - PREV0:.1f}分、バス {len(BUS0)}台）")
    print(f"2章: seed={SEED_MAIN} 1万人の平均の待ち={WAIT.mean():.3f} バスの間隔の平均={GAPS.mean():.3f}（{len(GAPS)}本） "
          f"人が落ちたすき間の平均={GAP_OF.mean():.3f}")
    day_means = [float(d[2].mean()) for d in DAYS]
    print("別の日の3本:", ", ".join(f"seed={s} {m:.3f}（間隔の平均 {np.diff(d[0]).mean():.2f}）"
                              for s, m, d in zip(SEED_DAYS, day_means, DAYS)))
    print(f"3章: Aさん（番号 {A_I}）着いた={A_ARR:.1f}分 待ち={A_WAIT:.2f}分 すき間={A_GAP:.2f}分"
          f"（前のバス {A_PREV:.1f}・次のバス {A_NEXT:.1f}、着いたのはすき間の {A_ARR - A_PREV:.1f}分目）")
    print(f"4-1: 同じ1万人・時刻表どおりの平均の待ち={SCHED_WAIT.mean():.3f}")

    # ---- 大きな照合（100万人） ----
    big_wait, big_gap = mean_wait_big(SD)
    # 2つのすき間（2分と18分）の例: 長いほうに9倍多く落ち、待ちは長いほう平均9分・短いほう平均1分
    rr = np.random.default_rng(3)
    ex_bus = np.arange(0, 20 * 100000 + 1, GAP_SHORT + GAP_LONG, dtype=float)    # 20分ごとの周期の頭
    ex_bus = np.sort(np.concatenate([ex_bus, ex_bus[:-1] + GAP_SHORT]))
    ex_arr = rr.uniform(0, ex_bus[-1], 1_000_000)
    ex_k = np.searchsorted(ex_bus, ex_arr, side="right")
    ex_wait, ex_len = ex_bus[ex_k] - ex_arr, ex_bus[ex_k] - ex_bus[ex_k - 1]
    ex_long = ex_len > 10
    example = (GAP_SHORT * (GAP_SHORT / 2) + GAP_LONG * (GAP_LONG / 2)) / (GAP_SHORT + GAP_LONG)
    print(f"2つのすき間: 長いすき間に落ちた人の割合 {ex_long.mean():.3f}（長:短 ＝ {ex_long.sum() / (~ex_long).sum():.2f} : 1）"
          f"、待ち 長 {ex_wait[ex_long].mean():.2f}分・短 {ex_wait[~ex_long].mean():.2f}分、全体 {ex_wait.mean():.3f}分")

    checks = [
        # 0章
        ("0章の1人の待ち（14.0±0.4）", WAIT0, ONE_WAIT, 0.4),
        # 2章
        ("2章 画面の「1万人の平均」（小数1桁）", r1(WAIT.mean()), SHOW_MAIN[0], 0),
        ("2章 画面の「バスの間隔の平均」（小数1桁）", r1(GAPS.mean()), SHOW_MAIN[1], 0),
        ("2章 画面の「人が落ちたすき間の平均」（小数1桁）", r1(GAP_OF.mean()), SHOW_MAIN[2], 0),
        ("2章 100万人の平均の待ち（でたらめな間隔）", big_wait, theory_wait(MU, SD), 0.05),
        ("2章 100万人が落ちたすき間の平均（理論 2×MU）", big_gap, 2 * MU, 0.15),
    ]
    for i, (m, s) in enumerate(zip(day_means, SEED_DAYS)):
        checks.append((f"2章 別の日{i + 1}（seed={s}）の平均の待ち 9.6〜10.4", m, 10.0, 0.4))
        checks.append((f"2章 別の日{i + 1} 画面の値（小数1桁）", r1(m), SHOW_DAYS[i], 0))
    checks.append(("2章 別の日3本の値の種類数（3つとも同じではない）", len({r1(m) for m in day_means}), 3, 0))
    checks += [
        # 3章
        ("3章 Aさんのいるすき間の長さ（23〜25分）", A_GAP, 24.0, 1.0),
        ("3章 Aさんの待ち（17.5〜18.5分）", A_WAIT, 18.0, 0.5),
        ("3章 Aさんが着いたのはすき間の端から離れている（前のバスから4.5分以上）", A_ARR - A_PREV, 6.0, 1.5),
        ("3章 2つのすき間の例 (2×1＋18×9)÷20（式）", example, SHOW_EXAMPLE, 1e-9),
        ("3章 2つのすき間の例（100万人のシミュレーション）", float(ex_wait.mean()), SHOW_EXAMPLE, 0.05),
        ("3章 長いすき間に落ちる人は 9倍", float(ex_long.sum() / (~ex_long).sum()), 9.0, 0.1),
        ("3章 長いすき間の人の平均の待ち（9分）", float(ex_wait[ex_long].mean()), 9.0, 0.05),
        ("3章 短いすき間の人の平均の待ち（1分）", float(ex_wait[~ex_long].mean()), 1.0, 0.05),
        # 4-1
        ("4-1 同じ1万人・時刻表どおり（小数1桁）", r1(SCHED_WAIT.mean()), SHOW_SCHED, 0),
        ("4-1 時刻表どおりの平均の待ち（理論 MU/2）", float(SCHED_WAIT.mean()), MU / 2, 0.1),
    ]

    # ---- 4-2: 乱れ ----
    print("4-2 乱れ（標準偏差）と、100万人の平均の待ち:")
    for sd, show in zip(SD_LIST, SHOW_SD):
        w, _ = mean_wait_big(sd)
        th = 5 * (1 + (sd / 10) ** 2)
        print(f"  乱れ {sd:>2}分 → シミュレーション {w:.3f}分 理論 {th:.2f}分 画面 {show:.1f}分")
        checks.append((f"4-2 乱れ{sd}分 vs 理論 5×(1＋(乱れ÷10)²)", w, th, 0.05))
        checks.append((f"4-2 乱れ{sd}分 画面の値（小数1桁）", r1(w), show, 0))

    # ---- 4-3・5章: 団子運転 ----
    off, on = bunch_hours()
    over200 = sum(overtakes(sim(sd, RUN_OFF)) + overtakes(sim(sd, RUN_ON, sched=True)) for sd in range(RUNS))
    print("団子運転（%d回の平均）1〜10時間目の平均の待ち（分）:" % RUNS)
    print("  時間調整なし:", " ".join(f"{v:.1f}" for v in off))
    print("  時間調整あり:", " ".join(f"{v:.1f}" for v in on))
    wo = wait_by_hour(LOG_OFF)
    wn = wait_by_hour(LOG_ON)
    print(f"画面の1回（なし seed={SEED_OFF}）:", " ".join(f"{v:.1f}" for v in wo))
    print(f"画面の1回（あり seed={SEED_ON}）:", " ".join(f"{v:.1f}" for v in wn))
    for t in (0, 60, 120, 180, 210, 240, 360, 600):
        print(f"  t={t:>3}分 なし: 待ち{wait_now(LOG_OFF, t):5.1f} 固まり{bus_groups(bus_angles(LOG_OFF, t))}"
              f" / あり: 待ち{wait_now(LOG_ON, t):5.1f} 固まり{bus_groups(bus_angles(LOG_ON, t))}")
    checks += [
        ("4-3 200回平均 1時間目（なし）（小数1桁）", r1(off[0]), SHOW_OFF[0], 0),
        ("4-3 200回平均 4時間目（なし）（小数1桁）", r1(off[3]), SHOW_OFF[1], 0),
        ("4-3 200回平均 10時間目（なし）（小数1桁）", r1(off[9]), SHOW_OFF[2], 0),
        ("4-3 200回平均 1時間目（なし）が「5分ほど」（4.5〜5.5）", float(off[0]), 5.0, 0.5),
        ("4-3 200回平均 4時間目（なし）が「13分ほど」（12.5〜13.5）", float(off[3]), 13.0, 0.5),
        ("4-3 200回平均 10時間目（なし）が 4時間目より大きい", float(off[9] > off[3]), 1.0, 0),
        ("5章 200回平均 10時間目（あり）が「5分ほど」（4.5〜5.5）", float(on[9]), SHOW_ON_10H, 0.5),
        ("5章 200回平均 1〜10時間目（あり）の最大と最小の差（0.3以下＝伸びていない）", float(on.max() - on.min()), 0.0, 0.3),
        ("4-3 画面の回（なし）1時間目", r1(wo[0]), SCREEN_OFF_H1, 0),
        ("4-3 画面の回（なし）4時間目が13分超", float(wo[3] > 13.0), 1.0, 0),
        ("4-3 画面の回（なし）3〜4時間後に 3台・2台 の固まり（210分・240分）",
         float(all(3 in bus_groups(bus_angles(LOG_OFF, t)) and 2 in bus_groups(bus_angles(LOG_OFF, t))
                   for t in (210, 240))), 1.0, 0),
        ("5章 画面の回（あり）10時間ずっと 4.75〜5.0分", float(min(wn) > 4.75 and max(wn) < 5.0), 1.0, 0),
        ("4-3 t=0 で6台が60度おき（両方の回。角度の差 60度±1度）",
         float(max(abs(np.degrees(np.diff(np.concatenate([np.sort(bus_angles(lg, 0.0)),
                                                          [2 * math.pi + np.sort(bus_angles(lg, 0.0))[0]]]))) - 60).max()
                   for lg in (LOG_OFF, LOG_ON))), 0.0, 1.0),
        ("5章 画面の回（あり）バスの間隔が 10分から外れる最大（分）", spacing_dev(LOG_ON), 0.0, 5.0),
        ("4-3・5章 画面の回で、全時刻で6台の並び順が変わらない（追い越し0回。なし）", float(overtakes(LOG_OFF)), 0.0, 0),
        ("4-3・5章 画面の回で、全時刻で6台の並び順が変わらない（追い越し0回。あり）", float(overtakes(LOG_ON)), 0.0, 0),
        ("4-3 見せ方用の小さな版（toy_sim）で追い越し0回", float(overtakes(TOY_LOG, t1=TOY_LOG[-1, 0])), 0.0, 0),
        ("4-3・5章 200回の全部で追い越し0回（なし・あり）", float(over200), 0.0, 0),
    ]
    # アニメ用の関数の速さ（場面がフレームごとに呼ぶ）
    t0 = time.time()
    for i in range(1000):
        bus_angles(LOG_OFF, 0.6 * i)
        wait_now(LOG_OFF, 0.6 * i)
    per_call_ms = (time.time() - t0) / 1000 * 1000
    print(f"bus_angles＋wait_now を1回呼ぶ時間: {per_call_ms:.3f}ミリ秒")
    checks.append(("アニメ用 bus_angles＋wait_now 1回 ≦ 1ミリ秒（2つ合わせて）", per_call_ms, 0.0, 1.0))
    check_answers(checks)
    print(f"全部の照合 OK（{time.time() - t_start:.1f}秒）")


# ============================================================
# 書き出し
#   python sims/bus-matsu-long.py --check     数字の照合だけ
#   python sims/bus-matsu-long.py --stills    要所の静止画と sheet.png（out/bus-matsu-long/stills/）。--at 12.3,40.5 なら指定した秒だけ out/bus-matsu-long/at_*.png
#   python sims/bus-matsu-long.py --preview   960×540・15fps の確認用
#   python sims/bus-matsu-long.py             数字の照合 → 本番（out/bus-matsu-long/bus-matsu-long.mp4 と chapters.txt）
# ============================================================
if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）")
    if "--stills" in sys.argv:
        if "--at" in sys.argv:                          # --at 12.3,40.5 …  指定した秒だけ（直したところの確認用）
            ts = [float(x) for x in sys.argv[sys.argv.index("--at") + 1].split(",")]
            for tt in ts:
                lf.still(draw, tt, OUT / f"at_{tt:06.1f}.png")
        else:
            lf.stills(draw, still_times(), OUT / "stills")
    elif "--preview" in sys.argv:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
    else:
        lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
        print("完成:", OUT / f"{SLUG}.mp4")
