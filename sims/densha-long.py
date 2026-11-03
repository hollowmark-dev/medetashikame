"""電車の空席（横型ロング）— v2（2026-10-21）。v1 は out/densha-long/v1/densha-long.v1.py に退避してある。

題名案: 満員電車、座っている人の前に立てば、何駅で座れる？【1万回でためした】
構成案: research/longform_densha_outline_2026-10-21.md（ユーザー OK 済み）

v2 で変えたこと（v1 との違い）
  1. 乗った駅ごとの「降りる駅」を、国土交通省 大都市交通センサス第12回(2015)「線別駅間移動人員」(001179095.xlsx)の
     中央本線(路線コード002)・上り向き・快速の停車駅24駅どうしの駅対の人数に比例させる（v1 は降車の多さに比例）。
     表の人数が少ない駅は v1 の降車比例と混ぜる（人数 n に対し 擬似人数 K=1,000 を足す）。
  2. 席は「空の電車」から自然に埋める。高尾で空の1両。乗った人は空いた席があれば座る（端→端の隣→…の順に好む【仮定】）。
     席が埋まったら立つ。立つ人は区画の前の7か所から先に埋める【仮定】。区画に入る人数は 1両の人数 × f（区画の割合）。
  3. 「あなた」は指定の駅で乗り、他の乗る人と同じ順番の中に混ざる（乗る人の中でランダムな順）。座席が空いていれば座れる。
     席がすべて埋まっていた回だけを数える（埋まっていなければ座れたとして別に数える）。
  4. 席が空いたときのルールは v1 と同じ（真ん前の人が確率 a、残りは両隣が等分）。

モデルの手順（1駅ごと）
  (1) 降りる人が降りる（席・前の立ち位置・はみ出して立つ人）
  (2) 前の立ち位置の空きを、はみ出して立っていた人が埋める
  (3) 空いた席は、前に立つ人がルールどおり座る（同じ駅で複数空いたら順番はランダム）。座った人の立ち位置はまたはみ出した人が埋める
  (4) 乗ってくる人（ポアソン。その駅の乗車×k×f）が、降りる駅を表から引いて、ランダムな順に乗る。空いた席があれば座る、なければ前のランダムな空き位置に立つ、
      前もいっぱいならはみ出して立つ
  「あなた」: 乗る駅 B で上の(4)の中に混ざり、席が空いていなければ席 j の前に立つ。降りるのは東京（比べるときは新宿）。

使い方
  python -X utf8 sims/densha-long.py --numbers          照合 → out/densha-long/numbers.md・data.json（1万回ずつ）
  python -X utf8 sims/densha-long.py --numbers --quick  試し（回数を減らして out/densha-long/trial/ に書く）
"""
import bisect
import csv
import itertools
import json
import math
import random
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers  # noqa: E402

SLUG = "densha-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
SRC = OUT / "src"
QUICK = "--quick" in sys.argv

# ---------- 公表の数字（令和7年度の混雑率・国土交通省。src/mlit_kondo_r7_002015141.pdf の1ページ目「中央(快速) 中野→新宿」） ----------
CAP_PER_CAR = 148                       # 41,440人 ÷ (10両 × 28本) ＝ 148人/両
CAP_TOTAL, RIDERS_TOTAL, CARS, TRAINS, RATE = 41440, 65330, 10, 28, 158
LOAD_PER_CAR = RIDERS_TOTAL / (CARS * TRAINS)       # 233.3人/両（中野→新宿の1時間の平均）

# ---------- このモデルの値 ----------
N = 1500 if QUICK else 10000
NSEAT = 7
F_BASE = 7 / 54                         # 【仮定・要確認】1両の人のうち、この区画（席7＋前7）に入る割合。7人掛け÷1両の座席54（二次情報）
F_LIST = (0.12, F_BASE, 0.15)
A_MAIN = 0.6
A_LIST = (0.5, 0.6, 0.8, 1.0)
Q_LIST = (0.2, 0.5, 1.0)
K_PRIOR = 1000                          # 【仮定】降りる駅: 表の人数 n に 擬似人数 K（降車比例ぶん）を足して混ぜる。n/(n+K) が表の重み
SEED = 20261021
E_TOKYO, E_SHINJUKU = 23, 19
I_NAKANO = 18
B_ALL = tuple(range(0, 19))             # 乗る駅: 高尾〜中野
B_SET = (2, 4, 5, 8, 12, 13, 15, 18)    # 八王子・日野・立川・国分寺・三鷹・吉祥寺・荻窪・中野
B_Q = (5, 8, 12, 13, 18)                # 降りそうな人の分析
POS = (0, 1, 2, 3)                      # 席1〜席4の前（左右対称なので 5〜7 は 3〜1 と同じ）
POS_W = (2, 2, 2, 1)                    # 7か所のうち、席1・7(2)／席2・6(2)／席3・5(2)／席4(1)
SEAT_CLASS = {"端(席1・7)": (0, 6), "端の隣(席2・6)": (1, 5), "席3・5": (2, 4), "真ん中(席4)": (3,)}
MIN_FULL = 300                          # 席が埋まった回がこれより少ない乗る駅は、分布を出さない
MAX_TRIALS = 30 * N                     # 席が埋まる回が少ない乗る駅のための打ち切り
MAIN_DM = "od"


# ====================================================================================================
# データの読み込み
# ====================================================================================================
def load_stations():
    rows = []
    with open(SRC / "chuo_kaisoku_up_24.csv", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append(dict(order=int(r["order"]), name=r["station"], row=int(r["xlsx_row"]), board=int(r["up_board"]),
                         alight=int(r["up_alight"]), through=int(r["up_pass"])))
    assert [r["order"] for r in rows] == list(range(24))
    return rows


def load_all_rows():
    with open(SRC / "chuo_up_all_rows.csv", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    return [dict(row=int(r["xlsx_row"]), name=r["station"], board=int(r["up_board_total"]), alight=int(r["up_alight_total"]),
                 through=int(r["up_pass_total"])) for r in csv.DictReader(lines)]


def load_od_fast24():
    with open(SRC / "chuo_od_fast24.csv", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    rows = list(csv.reader(lines))
    return [[int(x) for x in r[2:]] for r in rows[1:]]


def load_codes():
    with open(SRC / "chuo_station_codes.csv", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    return list(csv.DictReader(lines))


# --- 検証用：xlsx を直接読む（標準ライブラリだけ。ダウンロードしたファイルは信頼せず -I で動かす前提） ---
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col2n(c):
    n = 0
    for ch in c:
        n = n * 26 + ord(ch) - 64
    return n


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", _NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % _NS["m"])))
    rows = {}
    for _, el in ET.iterparse(z.open("xl/worksheets/sheet1.xml")):
        if el.tag.endswith("}row"):
            d = {}
            for c in el.findall("m:c", _NS):
                m = re.match(r"([A-Z]+)(\d+)", c.get("r"))
                v = c.find("m:v", _NS)
                if v is None:
                    continue
                d[_col2n(m.group(1))] = ss[int(v.text)] if c.get("t") == "s" else v.text
            rows[int(el.get("r"))] = d
            el.clear()
    return rows


def _num(s):
    return int(str(s).replace(",", "").strip())


# ====================================================================================================
# モデル
# ====================================================================================================
class Model:
    """lam[s] = その駅で区画に乗ってくる人数の平均（ポアソン）、P[s] = (降りる駅の並び, 確率) 。nseat = 席の数 ＝ 前の立ち位置の数"""

    def __init__(self, names, lam, P, nseat=NSEAT):
        n = len(names)
        self.n, self.ns, self.names, self.lam, self.P = n, nseat, list(names), list(lam), P
        self.expl = [math.exp(-x) for x in lam]
        self.cum = [None if P[s] is None else list(itertools.accumulate(P[s][1])) for s in range(n)]
        self.rank = [min(i, nseat - 1 - i) for i in range(nseat)]
        self.rank_order = sorted(set(self.rank))
        self.byrank = {r: [i for i in range(nseat) if self.rank[i] == r] for r in self.rank_order}
        self.k = None
        self.unit_load = None

    def draw_dest(self, s, rng):
        i = bisect.bisect_right(self.cum[s], rng.random() * self.cum[s][-1])
        ds = self.P[s][0]
        return ds[min(i, len(ds) - 1)]

    def poisson(self, s, rng):
        lam = self.lam[s]
        if lam <= 0:
            return 0
        u, p = rng.random(), self.expl[s]
        cum, k = p, 0
        while u > cum and k < 400:
            k += 1
            p *= lam / k
            cum += p
        return k


def dest_probs(M24, A, t, K, mode):
    """t で乗った人の降りる駅の確率。mode: 'v1'＝降車比例（v1）／'od'＝表の駅対の人数と降車比例を n:K で混ぜる"""
    n = len(A)
    ds = list(range(t + 1, n))
    tot = float(sum(A[d] for d in ds))
    q = [A[d] / tot for d in ds]
    if mode == "v1":
        return ds, q
    row = [M24[t][d] for d in ds]
    nt = sum(row)
    if nt + K <= 0:
        return ds, q
    return ds, [(row[x] + K * q[x]) / (nt + K) for x in range(len(ds))]


_MODELS = {}


def get_model(dm=MAIN_DM, f=F_BASE):
    key = (dm, round(f, 6))
    if key not in _MODELS:
        st = load_stations()
        M24 = load_od_fast24()
        b = [r["board"] for r in st]
        A = [r["alight"] for r in st]
        n = 24
        if dm == "v1":
            mode, K = "v1", 0
        elif dm == "od0":
            mode, K = "od", 0
        elif dm == "od5000":
            mode, K = "od", 5000
        else:
            mode, K = "od", K_PRIOR
        P = [dest_probs(M24, A, t, K, mode) if t < n - 1 else None for t in range(n)]
        unit = [sum(b[t] * sum(p for d, p in zip(*P[t]) if d > i) for t in range(i + 1) if b[t] > 0) for i in range(n - 1)]
        k = LOAD_PER_CAR / unit[I_NAKANO]
        lam = [f * k * b[s] for s in range(n)]
        m = Model([r["name"] for r in st], lam, P)
        m.k, m.unit_load, m.b, m.A, m.f = k, unit, b, A, f
        _MODELS[key] = m
    return _MODELS[key]


# ====================================================================================================
# 1回ぶんの電車
# ====================================================================================================
def pick_taker(fd, i, a, rng, ns):
    """席 i が空いたとき、座る人の立ち位置を返す（fd<0 は誰もいない位置）。v1 と同じルール"""
    nb = [k for k in (i - 1, i + 1) if 0 <= k < ns and fd[k] >= 0]
    if fd[i] >= 0:
        if nb and rng.random() >= a:
            return nb[0] if len(nb) == 1 else (nb[0] if rng.random() < 0.5 else nb[1])
        return i
    if nb:
        return nb[0] if len(nb) == 1 else (nb[0] if rng.random() < 0.5 else nb[1])
    cand = [k for k in range(ns) if fd[k] >= 0]
    best = min(abs(k - i) for k in cand)
    return rng.choice([k for k in cand if abs(k - i) == best])


ONCE, FULL = 0, 1


def trial(M, rng, B, j, a, E, q=0.0, probe=None):
    """1回ぶん。B 駅で乗り、E 駅で降りる「あなた」(B=None なら「あなた」なし)。席 j の前に立つ。
    返り値: (ONCE/FULL, 座った駅 or -1, スナップ(席の人の乗った駅, 降りる駅) or None)"""
    ns = M.ns
    sd, so = [-1] * ns, [-1] * ns          # 席の人の降りる駅・乗った駅
    fd, fo = [-1] * ns, [-1] * ns          # 前の立ち位置
    ov = []                                # はみ出して立つ人 (乗った駅, 降りる駅)
    S = dict(yp=-1, sat=-1, snap=None, over=False)

    def refill():
        while ov:
            emp = [p for p in range(ns) if fd[p] < 0]
            if not emp:
                return
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            o, d = ov.pop(int(rng.random() * len(ov)))
            fd[p], fo[p] = d, o

    def stand(o, d):
        emp = [p for p in range(ns) if fd[p] < 0]
        if emp:
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            fd[p], fo[p] = d, o
        else:
            ov.append((o, d))

    def free_seat():
        for r in M.rank_order:
            cand = [i for i in M.byrank[r] if sd[i] < 0]
            if cand:
                return cand[0] if len(cand) == 1 else cand[int(rng.random() * len(cand))]
        return -1

    def watch(s):
        flagged = [i for i in range(ns) if sd[i] == s + 1 and rng.random() < q]
        if not flagged:
            return
        p = S["yp"]
        best = min(abs(i - p) for i in flagged)
        i = rng.choice([x for x in flagged if abs(x - p) == best])
        if i != p:
            fd[i], fd[p] = fd[p], fd[i]
            fo[i], fo[p] = fo[p], fo[i]
            S["yp"] = i

    for s in range(E):
        if s >= 1:
            freed = []
            for i in range(ns):
                if sd[i] == s:
                    sd[i], so[i] = -1, -1
                    freed.append(i)
            for p in range(ns):
                if fd[p] == s and p != S["yp"]:
                    fd[p], fo[p] = -1, -1
            if ov:
                ov[:] = [x for x in ov if x[1] != s]
            refill()
            if len(freed) > 1:
                rng.shuffle(freed)
            for i in freed:
                if all(x < 0 for x in fd):
                    break
                p = pick_taker(fd, i, a, rng, ns)
                if p == S["yp"]:
                    return FULL, s, S["snap"]
                sd[i], so[i] = fd[p], fo[p]
                fd[p], fo[p] = -1, -1
                refill()
        nb = M.poisson(s, rng)
        people = [M.draw_dest(s, rng) for _ in range(nb)]
        if s == B:
            people.insert(int(rng.random() * (nb + 1)), -1)
        for d in people:
            if d == -1:
                i = free_seat()
                if i >= 0:
                    return ONCE, s, None
                S["snap"] = (list(so), list(sd))
                if fd[j] >= 0:
                    ov.append((fo[j], fd[j]))
                fd[j], fo[j], S["yp"] = E, B, j
                continue
            i = free_seat()
            if i >= 0:
                sd[i], so[i] = d, s
            else:
                stand(s, d)
        if probe is not None:
            probe(s, nb, sd, so, fd, fo, ov)
        if B is not None and s >= B and q > 0 and s + 1 < E and S["yp"] >= 0:
            watch(s)
    return FULL, -1, S["snap"]


def trial3(M, rng, B, j, a, E, q=0.0, probe=None, info=None):
    """章4 v3 の1回ぶん。trial と同じ電車で、「降りそうな人が分かる」の決めごとだけが違う。
      ・あなたは席 j の前から動かない（立っている人と入れ替わらない・遠くの席の前へ移らない）
      ・手を出せるのは 目の前の席 j と すぐ隣の席 j-1・j+1 だけ（端の前なら隣は1席）
      ・その3席に座っている人のうち 次の駅で降りる人を、1人ずつ確率 q で前もって見抜ける（見間違いなし）
      ・見抜いた人の席が空いたら あなたが先に座る（真ん前に別の人が立っていても）。見抜けなかった席は いまのルール(a)のまま
    q=0 のときは乱数を1つも使わないので、trial と同じ結果になる。
    info（任意の dict）: 照合用の記録。draws/flags=見抜く判定の回数と成功数、prio_seat=先に座った席、first_dep=手の届く席の人が最初に降りる駅"""
    ns = M.ns
    sd, so = [-1] * ns, [-1] * ns
    fd, fo = [-1] * ns, [-1] * ns
    ov = []
    S = dict(yp=-1, snap=None)
    reach = [k for k in (j - 1, j, j + 1) if 0 <= k < ns]

    def refill():
        while ov:
            emp = [p for p in range(ns) if fd[p] < 0]
            if not emp:
                return
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            o, d = ov.pop(int(rng.random() * len(ov)))
            fd[p], fo[p] = d, o

    def stand(o, d):
        emp = [p for p in range(ns) if fd[p] < 0]
        if emp:
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            fd[p], fo[p] = d, o
        else:
            ov.append((o, d))

    def free_seat():
        for r in M.rank_order:
            cand = [i for i in M.byrank[r] if sd[i] < 0]
            if cand:
                return cand[0] if len(cand) == 1 else cand[int(rng.random() * len(cand))]
        return -1

    for s in range(E):
        if s >= 1:
            freed = []
            for i in range(ns):
                if sd[i] == s:
                    sd[i], so[i] = -1, -1
                    freed.append(i)
            for p in range(ns):
                if fd[p] == s and p != S["yp"]:
                    fd[p], fo[p] = -1, -1
            if ov:
                ov[:] = [x for x in ov if x[1] != s]
            # 見抜いていた席が空いたら、あなたが先に座る。見抜く判定は 手の届く席で今この駅で降りる人ごとに1回（前の駅を出るときに見抜いたのと同じこと）
            if q > 0 and S["yp"] >= 0:
                got = [i for i in freed if abs(i - j) <= 1 and rng.random() < q]
                if info is not None:
                    info["draws"] = info.get("draws", 0) + sum(1 for i in freed if abs(i - j) <= 1)
                    info["flags"] = info.get("flags", 0) + len(got)
                if got:
                    if info is not None:
                        info["prio_seat"] = got[0]
                    return FULL, s, S["snap"]
            refill()
            if len(freed) > 1:
                rng.shuffle(freed)
            for i in freed:
                if all(x < 0 for x in fd):
                    break
                p = pick_taker(fd, i, a, rng, ns)
                if p == S["yp"]:
                    return FULL, s, S["snap"]
                sd[i], so[i] = fd[p], fo[p]
                fd[p], fo[p] = -1, -1
                refill()
        nb = M.poisson(s, rng)
        people = [M.draw_dest(s, rng) for _ in range(nb)]
        if s == B:
            people.insert(int(rng.random() * (nb + 1)), -1)
        for d in people:
            if d == -1:
                i = free_seat()
                if i >= 0:
                    return ONCE, s, None
                S["snap"] = (list(so), list(sd))
                if fd[j] >= 0:
                    ov.append((fo[j], fd[j]))
                fd[j], fo[j], S["yp"] = E, B, j
                continue
            i = free_seat()
            if i >= 0:
                sd[i], so[i] = d, s
            else:
                stand(s, d)
        if probe is not None:
            probe(s, nb, sd, so, fd, fo, ov)
        if info is not None and S["yp"] >= 0 and s + 1 < E and "first_dep" not in info:
            if any(sd[i] == s + 1 for i in reach):
                info["first_dep"] = s + 1
    return FULL, -1, S["snap"]


# ====================================================================================================
# 1万回ずつの計算（並列）
# ====================================================================================================
def run_cell(spec):
    dm, f, B, j, a, q, E, tag = spec
    M = get_model(dm, f)
    rng = random.Random(f"{SEED}|{tag}|{dm}|{round(f, 6)}|{B}|{j}|{a}|{q}|{E}")
    sits, org, dst = [], [], []
    n_tr = n_once = 0
    while len(sits) < N and n_tr < MAX_TRIALS:
        if len(sits) == 0 and n_tr >= max(20000, N):
            break
        n_tr += 1
        code, sat, snap = (trial3 if tag == "ch4v3" else trial)(M, rng, B, j, a, E, q)
        if code == ONCE:
            n_once += 1
        else:
            sits.append(sat)
            org.append(snap[0])
            dst.append(snap[1])
    return spec, dict(n_trials=n_tr, n_once=n_once, sits=np.array(sits, dtype=np.int16),
                      org=np.array(org, dtype=np.int8).reshape(-1, NSEAT), dst=np.array(dst, dtype=np.int8).reshape(-1, NSEAT))


def key_of(dm, f, B, j, a, q, E, tag):
    return f"{tag}|{dm}|f{round(f, 4)}|B{B}|j{j + 1}|a{a}|q{q}|E{E}"


def summarize(sits, B, n_trials, n_once):
    sits = np.asarray(sits)
    nf = len(sits)
    d = dict(n_trials=int(n_trials), n_once=int(n_once), n_full=int(nf), p_free=n_once / n_trials, p_full=nf / n_trials)
    if nf == 0:
        return d
    sat = sits >= 0
    ns_ = int(sat.sum())
    off = np.sort(sits[sat].astype(int) - B)
    d.update(p_sat=ns_ / nf, p_never=1 - ns_ / nf,
             p_before_shinjuku=float(np.mean(sat & (sits < E_SHINJUKU))), p_at_shinjuku=float(np.mean(sits == E_SHINJUKU)),
             p_after_shinjuku=float(np.mean(sits > E_SHINJUKU)),
             mean_n=float(off.mean()) if ns_ else float("nan"), sd_n=float(off.std()) if ns_ else float("nan"))
    cnt = np.bincount(np.where(sat, sits, 24), minlength=25)[:24]
    d["pmf_station"] = [float(x) / nf for x in cnt]
    d["cdf_n"] = {str(k): float(np.mean(sat & ((sits - B) <= k))) for k in (1, 2, 3, 4, 5, 6, 8, 10)}
    # 全員（座れない回も含む）の中での真ん中の値: 累積が 0.5 に届く最初の駅数
    cum, med = 0.0, None
    for k in range(1, 24 - B):
        cum += float(np.mean(sat & ((sits - B) == k)))
        if cum >= 0.5:
            med = k
            break
    d["median_n"] = med
    d["median_station"] = None if med is None else B + med
    # 新宿で降りる人（同じ試行の 新宿の手前まで）の平均
    sb = sat & (sits < E_SHINJUKU)
    d["mean_n_shinjuku"] = float((sits[sb] - B).mean()) if sb.any() else float("nan")
    return d


def cell(R, B, j, dm=MAIN_DM, f=F_BASE, a=A_MAIN, q=0.0, E=E_TOKYO, tag="main"):
    return R["cells"][key_of(dm, f, B, j, a, q, E, tag)]


def build_specs():
    S = []

    def add(dm, f, B, j, a, q, E, tag):
        S.append((dm, f, B, j, a, q, E, tag))

    for B in B_ALL:
        for j in POS:
            add(MAIN_DM, F_BASE, B, j, A_MAIN, 0.0, E_TOKYO, "main")
    for B in (5, 12):
        add(MAIN_DM, F_BASE, B, 6, A_MAIN, 0.0, E_TOKYO, "main")                    # 席7の前（席1の前と鏡）
    for a in A_LIST:
        if a != A_MAIN:
            for B in B_SET:
                for j in POS:
                    add(MAIN_DM, F_BASE, B, j, a, 0.0, E_TOKYO, "main")
    for f in F_LIST:
        if round(f, 6) != round(F_BASE, 6):
            for B in B_SET:
                for j in POS:
                    add(MAIN_DM, f, B, j, A_MAIN, 0.0, E_TOKYO, "main")
    for dm in ("v1", "od0", "od5000"):
        for B in B_SET:
            for j in POS:
                add(dm, F_BASE, B, j, A_MAIN, 0.0, E_TOKYO, "main")
    for B in B_SET:
        for j in POS:
            add(MAIN_DM, F_BASE, B, j, A_MAIN, 0.0, E_TOKYO, "again")               # 別の乱数
    for q in Q_LIST:
        for E in (E_TOKYO, E_SHINJUKU):
            for B in B_Q:
                for j in (0, 1, 3):
                    add(MAIN_DM, F_BASE, B, j, A_MAIN, q, E, "main")
    return list(dict.fromkeys(S))


B_V3 = (5, 12, 13)                      # 章4 v3: 立川・三鷹・吉祥寺
J_V3 = (0, 1, 3)                        # 席1(端)・席2(端の隣)・席4(真ん中)の前
Q_V3 = (0.0,) + Q_LIST                  # q=0 は main の章4(q=0)のセルをそのまま使う


def build_specs_v3():
    S = []
    for q in Q_LIST:
        for E in (E_TOKYO, E_SHINJUKU):
            for B in B_V3:
                for j in J_V3:
                    S.append((MAIN_DM, F_BASE, B, j, A_MAIN, q, E, "ch4v3"))
    return S


def cell3(R, B, j, q, E):
    """章4 v3 のセル。q=0 は main の q=0（同じ電車・何もしない）"""
    if q == 0:
        return cell(R, B, j, a=A_MAIN, q=0.0, E=E_TOKYO)
    return R["v3"][key_of(MAIN_DM, F_BASE, B, j, A_MAIN, q, E, "ch4v3")]


def compute():
    M = get_model()
    specs = build_specs()
    print(f"  計算: {len(specs)} 条件 × 最大 {N:,} 回（席が埋まった回）")
    with Pool(min(16, len(specs))) as pool:
        res = pool.map(run_cell, specs, chunksize=1)
    cells = {}
    for spec, r in res:
        dm, f, B, j, a, q, E, tag = spec
        k_ = key_of(dm, f, B, j, a, q, E, tag)
        c = dict(spec=list(spec), n_trials=r["n_trials"], n_once=r["n_once"], n_full=len(r["sits"]),
                 tokyo=None, shinjuku=None)
        sm = summarize(r["sits"], B, r["n_trials"], r["n_once"])
        if q == 0:
            c["tokyo"] = sm
            sh = r["sits"].copy()
            sh[sh >= E_SHINJUKU] = -1                     # 新宿で降りる人：新宿の手前で座れなければ座れない
            c["shinjuku"] = summarize(sh, B, r["n_trials"], r["n_once"])
        elif E == E_SHINJUKU:
            c["shinjuku"] = sm
        else:
            c["tokyo"] = sm
        c["_sits"], c["_org"], c["_dst"] = r["sits"], r["org"], r["dst"]
        cells[k_] = c
    specs3 = build_specs_v3()
    print(f"  章4 v3: {len(specs3)} 条件")
    with Pool(min(16, len(specs3))) as pool:
        res3 = pool.map(run_cell, specs3, chunksize=1)
    v3 = {}
    for spec, r in res3:
        dm, f, B, j, a, q, E, tag = spec
        sm = summarize(r["sits"], B, r["n_trials"], r["n_once"])
        c = dict(spec=list(spec), n_trials=r["n_trials"], n_once=r["n_once"], n_full=len(r["sits"]),
                 tokyo=sm if E == E_TOKYO else None, shinjuku=sm if E == E_SHINJUKU else None)
        c["_sits"] = r["sits"]
        v3[key_of(dm, f, B, j, a, q, E, tag)] = c
    return dict(cells=cells, v3=v3)


def pos_avg(R, B, field, dest="tokyo", **kw):
    """7か所の立ち位置（席1〜7の前）の平均。席5〜7は席3〜1と同じとして重みをかける"""
    vals = [(w, cell(R, B, j, **kw)[dest]) for j, w in zip(POS, POS_W)]
    vals = [(w, v[field]) for w, v in vals if field in v]
    if not vals:
        return float("nan")
    return sum(w * x for w, x in vals) / sum(w for w, _ in vals)


# ====================================================================================================
# 席の人の顔ぶれ（章2）
# ====================================================================================================
def seat_class_stats(R, B, **kw):
    """乗った瞬間（席がすべて埋まっている）の席の人。位置 j を混ぜる。席の種類ごとに、乗った駅・降りる駅の特徴"""
    org = np.concatenate([cell(R, B, j, **kw)["_org"] for j in POS]).astype(int)
    dst = np.concatenate([cell(R, B, j, **kw)["_dst"] for j in POS]).astype(int)
    out = dict(n=int(len(org)))
    if len(org) == 0:
        return out
    pc_ = {}
    for nm, seats in SEAT_CLASS.items():
        o, d = org[:, list(seats)], dst[:, list(seats)]
        pc_[nm] = dict(
            mean_origin=float(o.mean()), p_origin_le_hachioji=float((o <= 2).mean()), p_origin_takao=float((o == 0).mean()),
            p_dest_ge_shinjuku=float((d >= E_SHINJUKU).mean()), p_dest_gt_shinjuku=float((d > E_SHINJUKU).mean()),
            p_dest_tokyo=float((d == E_TOKYO).mean()), p_next=float((d == B + 1).mean()),
            mean_remaining=float((d - B).mean()), mean_trip=float((d - o).mean()),
            dest_pmf=[float((d == x).mean()) for x in range(24)], origin_pmf=[float((o == x).mean()) for x in range(24)])
        pc_[nm]["_tr_ge"] = (d >= E_SHINJUKU).mean(axis=1)
        pc_[nm]["_tr_gt"] = (d > E_SHINJUKU).mean(axis=1)
        pc_[nm]["_tr_rem"] = (d - B).mean(axis=1)
        pc_[nm]["_tr_org"] = o.mean(axis=1)
    out["classes"] = pc_
    e, m = pc_["端(席1・7)"], pc_["真ん中(席4)"]
    for fld, nm in (("_tr_ge", "ge_shinjuku"), ("_tr_gt", "gt_shinjuku"), ("_tr_rem", "remaining"), ("_tr_org", "origin")):
        diff = e[fld] - m[fld]
        se = diff.std() / math.sqrt(len(diff))
        out["diff_" + nm] = dict(diff=float(diff.mean()), se=float(se), z=float(diff.mean() / se) if se > 0 else 0.0)
    return out


# ====================================================================================================
# 厳密な答え（照合用）— 小さい場合（席3・5駅）の全通り数え上げ（状態の確率を1駅ずつ進める DP）。engine とは別の書き方
# ====================================================================================================
def exact_small(lam, P, ns, a, j, B, E, cutoff=8, q3=0.0):
    """lam[s]: 駅 s の乗る人数の平均、P[s]=(ds, probs)。B 駅で「あなた」が乗り、席 j の前に立つ。
    q3>0 なら章4 v3: あなたは席 j の前から動かず、手の届く席(j-1,j,j+1)で今この駅で降りる人を それぞれ確率 q3 で見抜いていて、
    1人でも見抜いていたらあなたが先に座る（見抜く判定は席ごとに独立なので『1人でも』の確率は 1-(1-q3)^(その席の数)）。
    返り値: (座れた駅ごとの確率 {s: p}, 乗った時に座れた確率, 座れない確率, 打ち切りで落とした確率の上限)"""
    n = len(lam)
    EMPTY = -1

    def rank(i):
        return min(i, ns - 1 - i)

    def taker_dist(fd, i):
        nb = [k for k in (i - 1, i + 1) if 0 <= k < ns and fd[k] >= 0]
        if fd[i] >= 0:
            if nb and a < 1.0:
                out = {i: a}
                for k in nb:
                    out[k] = out.get(k, 0.0) + (1 - a) / len(nb)
                return out
            return {i: 1.0}
        if nb:
            return {k: 1.0 / len(nb) for k in nb}
        cand = [k for k in range(ns) if fd[k] >= 0]
        best = min(abs(k - i) for k in cand)
        c2 = [k for k in cand if abs(k - i) == best]
        return {k: 1.0 / len(c2) for k in c2}

    rcache, bcache = {}, {}

    def refill(state):
        """はみ出した人が空いた前の位置を埋める。返り値 [(state, prob)]"""
        if state not in rcache:
            rcache[state] = refill0(state)
        return rcache[state]

    def refill0(state):
        sd, fd, ov, yp = state
        if not ov or all(x >= 0 for x in fd):
            return [(state, 1.0)]
        emp = [p for p in range(ns) if fd[p] < 0]
        out = {}
        for p in emp:
            for idx in range(len(ov)):
                fd2 = list(fd)
                fd2[p] = ov[idx]
                ov2 = tuple(sorted(ov[:idx] + ov[idx + 1:]))
                for st2, p2 in refill((sd, tuple(fd2), ov2, yp)):
                    out[st2] = out.get(st2, 0.0) + p2 / (len(emp) * len(ov))
        return list(out.items())

    def free_choices(sd):
        for r in sorted(set(rank(i) for i in range(ns))):
            cand = [i for i in range(ns) if rank(i) == r and sd[i] == EMPTY]
            if cand:
                return cand
        return []

    def board(state, d, you):
        key = (state, d, you)
        if key not in bcache:
            bcache[key] = board0(state, d, you)
        return bcache[key]

    def board0(state, d, you):
        """1人乗る。d=降りる駅。you=True なら「あなた」。返り値 [(state, prob, 結果)] 結果: None / 'once'"""
        sd, fd, ov, yp = state
        cand = free_choices(sd)
        if cand:
            if you:
                return [(state, 1.0, "once")]
            out = []
            for i in cand:
                sd2 = list(sd)
                sd2[i] = d
                out.append(((tuple(sd2), fd, ov, yp), 1.0 / len(cand), None))
            return out
        if you:
            fd2, ov2 = list(fd), list(ov)
            if fd2[j] >= 0:
                ov2.append(fd2[j])
            fd2[j] = E
            return [((sd, tuple(fd2), tuple(sorted(ov2)), j), 1.0, None)]
        emp = [p for p in range(ns) if fd[p] < 0]
        if emp:
            out = []
            for p in emp:
                fd2 = list(fd)
                fd2[p] = d
                out.append(((sd, tuple(fd2), ov, yp), 1.0 / len(emp), None))
            return out
        return [((sd, fd, tuple(sorted(ov + (d,))), yp), 1.0, None)]

    def merge(dist):
        out = {}
        for st, p in dist:
            out[st] = out.get(st, 0.0) + p
        return out

    states = {(tuple([EMPTY] * ns), tuple([EMPTY] * ns), tuple(), -1): 1.0}
    sit = {}
    once = 0.0
    tail = 0.0
    for s in range(E):
        if s >= 1:
            # (1) 降りる (2) はみ出しが前を埋める (3) 空いた席に前の人が座る
            nxt = {}
            for (sd, fd, ov, yp), pr in states.items():
                freed = [i for i in range(ns) if sd[i] == s]
                if q3 > 0 and yp >= 0:
                    m_ = sum(1 for i in freed if abs(i - j) <= 1)
                    pf = 1.0 - (1.0 - q3) ** m_
                    if pf > 0:
                        sit[s] = sit.get(s, 0.0) + pr * pf
                        pr = pr * (1.0 - pf)
                        if pr <= 0:
                            continue
                sd1 = tuple(EMPTY if x == s else x for x in sd)
                fd1 = tuple(EMPTY if (x == s and p != yp) else x for p, x in enumerate(fd))
                ov1 = tuple(x for x in ov if x != s)
                cur = {}
                for st2, p2 in refill((sd1, fd1, ov1, yp)):
                    cur[st2] = cur.get(st2, 0.0) + pr * p2
                perms = list(itertools.permutations(freed)) or [()]
                for perm in perms:
                    cur2 = {st: p / len(perms) for st, p in cur.items()}
                    for i in perm:
                        nx = {}
                        for st, p in cur2.items():
                            sd_, fd_, ov_, yp_ = st
                            if all(x < 0 for x in fd_):
                                nx[st] = nx.get(st, 0.0) + p
                                continue
                            for tk, w in taker_dist(fd_, i).items():
                                if tk == yp_:
                                    sit[s] = sit.get(s, 0.0) + p * w
                                    continue
                                sdn, fdn = list(sd_), list(fd_)
                                sdn[i] = fdn[tk]
                                fdn[tk] = EMPTY
                                for st3, p3 in refill((tuple(sdn), tuple(fdn), ov_, yp_)):
                                    nx[st3] = nx.get(st3, 0.0) + p * w * p3
                        cur2 = nx
                    for st, p in cur2.items():
                        nxt[st] = nxt.get(st, 0.0) + p
            states = nxt
        # (4) 乗ってくる人（人数はポアソン。『あなた』は B 駅で、乗る人の中のランダムな順番に混ざる）
        ds, pd_ = P[s] if P[s] is not None else ([], [])
        pois = [math.exp(-lam[s]) * lam[s] ** k / math.factorial(k) for k in range(cutoff + 1)]
        tail += (1.0 - sum(pois)) * sum(states.values())
        newstates = {}
        for Nn in range(cutoff + 1):
            if pois[Nn] <= 0:
                continue
            for m in (range(Nn + 1) if s == B else [None]):
                weight = pois[Nn] / (Nn + 1) if s == B else pois[Nn]
                cur = dict(states)
                for pos in range(Nn + (1 if s == B else 0)):
                    nx = {}
                    for st, p in cur.items():
                        if s == B and pos == m:
                            for st2, p2, res in board(st, 0, True):
                                if res == "once":
                                    once += p * p2 * weight
                                else:
                                    nx[st2] = nx.get(st2, 0.0) + p * p2
                        else:
                            for dd, pdv in zip(ds, pd_):
                                for st2, p2, _ in board(st, dd, False):
                                    nx[st2] = nx.get(st2, 0.0) + p * pdv * p2
                    cur = nx
                for st, p in cur.items():
                    newstates[st] = newstates.get(st, 0.0) + p * weight
        states = newstates
    never = sum(states.values())
    return sit, once, never, tail


# ====================================================================================================
# 照合
# ====================================================================================================
def prop_tol(p, n, z=4.0, floor=0.002):
    return z * math.sqrt(max(p * (1 - p), 1e-12) / n) + floor


def small_model():
    """席3・5駅（0〜4）の小さい模型。乗る人数の平均と降りる駅の確率は適当に決めた値"""
    lam = [1.8, 1.5, 1.1, 0.8, 0.0]
    P = [([1, 2, 3, 4], [0.1, 0.2, 0.3, 0.4]), ([2, 3, 4], [0.3, 0.3, 0.4]), ([3, 4], [0.4, 0.6]), ([4], [1.0]), None]
    return Model(["s0", "s1", "s2", "s3", "s4"], lam, P, nseat=3)


def run_checks(R):
    M = get_model()
    c = []
    st = load_stations()
    allr = load_all_rows()
    M24 = load_od_fast24()
    codes = load_codes()
    # --- 表（駅別発着・駅間通過人員表 001178992）の読み取り（v1 から引き継ぎ） ---
    c.append(("表992: 中央本線の節 上りの乗車合計 ＝ 降車合計（合計 1,128,668）", float(sum(r["board"] for r in allr)), float(sum(r["alight"] for r in allr)), 0.5))
    c.append(("表992: 上りの乗車合計は 合計行の 1,128,668", float(sum(r["board"] for r in allr)), 1128668.0, 0.5))
    err = max(abs(allr[i]["through"] - (allr[i + 1]["through"] + allr[i + 1]["board"] - allr[i + 1]["alight"])) for i in range(len(allr) - 1))
    c.append(("表992: 通過人員の保存則（全41区間のずれの最大 人）", float(err), 0.0, 1.5))
    c.append(("表992: 快速の停車駅 24駅", float(len(st)), 24.0, 0.0))
    c.append(("表992: 東京は上りの乗車0・高尾は上りの降車が乗車より少ない", float(st[23]["board"] == 0 and st[0]["alight"] < st[0]["board"]), 1.0, 0.0))
    # --- 移動人員表（線別駅間移動人員 001179095）を xlsx から直接読み直して照合 ---
    rt = read_xlsx(SRC / "001179688.xlsx")
    chuo = [r for r in rt.values() if r.get(1) == "002"]
    c.append(("移動人員表: 路線コード 002 が『東日本旅客鉄道 中央本線』ちょうど1件（路線コード表 001179688）",
              float(len(chuo) == 1 and chuo[0][3] == "中央本線" and chuo[0][2] == "東日本旅客鉄道"), 1.0, 0.0))
    stn = read_xlsx(SRC / "001179689.xlsx")
    code2name = {r[1]: r[4] for k, r in stn.items() if k > 1 and r.get(6) == "002" and r.get(5) == "01"}
    c.append(("移動人員表: 駅コード表で 路線002 の駅が 00201〜00242 の42駅", float(sorted(code2name) == [f"00{x}" for x in range(201, 243)]), 1.0, 0.0))
    ok_names = all(code2name[r["station_code"]] == r["station_in_code_table"] for r in codes)
    c.append(("移動人員表: 快速24駅の駅コード（csv）が 駅コード表の駅名と全部一致", float(ok_names and len(codes) == 24), 1.0, 0.0))
    fc = [int(r["station_code"]) for r in codes]
    c.append(("移動人員表: 快速24駅の駅コードは 高尾232→東京201 の順に減る（上り向き＝コードが小さくなる向き）", float(fc == sorted(fc, reverse=True) and fc[0] == 232 and fc[-1] == 201), 1.0, 0.0))
    od = read_xlsx(SRC / "001179095.xlsx")
    pairs = {}
    tot2 = 0
    for k, r in od.items():
        if k == 1 or _num(r[1]) != 2:
            continue
        b_, a_, n_ = _num(r[2]), _num(r[4]), _num(r[6])
        pairs[(b_, a_)] = pairs.get((b_, a_), 0) + n_
        tot2 += n_
    t992 = read_xlsx(SRC / "001178992.xlsx")
    c.append(("移動人員表: 路線002の全行の合計 ＝ 駅別発着表(001178992)の 定期券・上りの乗車の合計 743,313", float(tot2), float(_num(t992[72][5])), 0.5))
    up = {k: v for k, v in pairs.items() if k[0] > k[1]}
    dn = {k: v for k, v in pairs.items() if k[0] < k[1]}
    c.append(("移動人員表: 上り向き＋下り向き ＝ 全行の合計（同じ駅どうしの行はない）", float(sum(up.values()) + sum(dn.values())), float(tot2), 0.5))
    worst = 0
    for row in range(30, 72):
        code = 200 + (row - 29)
        e1 = sum(v for (b_, a_), v in up.items() if b_ == code) + sum(v for (b_, a_), v in dn.items() if a_ == code)
        e2 = sum(v for (b_, a_), v in up.items() if a_ == code) + sum(v for (b_, a_), v in dn.items() if b_ == code)
        worst = max(worst, abs(_num(t992[row][5]) - e1), abs(_num(t992[row][6]) - e2))
    c.append(("移動人員表: 全42駅で 定期の上り乗車(駅i)＝上り向きでiから乗る＋下り向きでiで降りる、上り降車も同様（ずれの最大 人）", float(worst), 0.0, 0.5))
    idx = {code: i for i, code in enumerate(fc)}
    S_ = sum(v for (b_, a_), v in up.items() if b_ in idx and a_ in idx)
    c.append(("移動人員表: 快速24駅どうしの上り向きの駅対の合計 ＝ 行列(csv)の合計（xlsx から直接読み直し）", float(S_), float(sum(map(sum, M24))), 0.5))
    ok_cells = all(M24[idx[b_]][idx[a_]] == v for (b_, a_), v in up.items() if b_ in idx and a_ in idx)
    c.append(("移動人員表: 行列(csv)の全セルが xlsx と一致", float(ok_cells), 1.0, 0.0))
    c.append(("移動人員表: 行列は上三角（降りる駅は必ず東京側）", float(all(M24[i][j_] == 0 for i in range(24) for j_ in range(i + 1))), 1.0, 0.0))
    # --- 降りる駅の分布 ---
    mxerr = max(abs(sum(M.P[t][1]) - 1.0) for t in range(23))
    c.append(("降りる駅: 23駅すべてで 確率の合計が1（最大のずれ）", mxerr, 0.0, 1e-12))
    Ap = [r["alight"] for r in st]
    for t, d in ((0, 19), (5, 19), (12, 23), (18, 19)):
        ds, pr = M.P[t]
        tot = float(sum(Ap[x] for x in range(t + 1, 24)))
        n_t = sum(M24[t][x] for x in range(t + 1, 24))
        exp = (M24[t][d] + K_PRIOR * Ap[d] / tot) / (n_t + K_PRIOR)
        c.append((f"降りる駅: {M.names[t]}で乗った人が{M.names[d]}で降りる確率 ＝ (表{M24[t][d]:,}＋K×降車比例)÷(表{n_t:,}＋K)", dict(zip(ds, pr))[d], exp, 1e-12))
    ds, pr = M.P[5]
    c.append(("降りる駅: 立川で乗った人が新宿で降りる表の割合（K=0）が 27%台（表 70,376 人中の新宿ぶんから式）", dict(zip(*dest_probs(M24, Ap, 5, 0, "od")))[19],
              M24[5][19] / sum(M24[5]), 1e-12))
    rng2 = random.Random(SEED + 2)
    for t, d in ((0, 19), (5, 19), (12, 23)):
        TT = 40000
        cnt = sum(1 for _ in range(TT) if M.draw_dest(t, rng2) == d)
        p = dict(zip(*M.P[t]))[d]
        c.append((f"降りる駅: {M.names[t]}で乗った人の引いた降りる駅が {M.names[d]} になる割合（{TT:,}回・4σ 以内）", cnt / TT, p, prop_tol(p, TT)))
    # --- 合わせ込み ---
    k = M.k
    c.append(("合わせ込み: 中野→新宿の1両の平均の人数 ＝ 65,330÷(10×28)＝233.3人", k * M.unit_load[I_NAKANO], LOAD_PER_CAR, 1e-9))
    c.append(("合わせ込み: 41,440÷(10×28)＝1両の輸送力 148人", CAP_TOTAL / (CARS * TRAINS), float(CAP_PER_CAR), 1e-9))
    c.append(("合わせ込み: 65,330÷41,440 → 混雑率 158%", RIDERS_TOTAL / CAP_TOTAL * 100, float(RATE), 0.5))
    rng = np.random.default_rng(SEED + 1)
    n = M.n
    lam = np.zeros((n, n))
    for t in range(n - 1):
        for d, p in zip(*M.P[t]):
            lam[t, d] = k * M.b[t] * p
    T = 20000
    X = rng.poisson(lam, size=(T, n, n))
    load = np.array([X[:, :i + 1, i + 1:].sum(axis=(1, 2)) for i in range(n - 1)])
    se = load[I_NAKANO].std() / math.sqrt(T)
    c.append(("合わせ込み: 1両を別の書き方（ポアソンを駅の組ごとに）で2万回走らせた 中野→新宿の平均の人数が 233.3人（4σ 以内）", float(load[I_NAKANO].mean()), LOAD_PER_CAR, 4 * se))
    brd = X.sum(axis=2)
    c.append(("合わせ込み: 高尾で乗る人数の平均が k×(高尾の乗車)（4σ 以内）", float(brd[:, 0].mean()), k * M.b[0], 4 * math.sqrt(k * M.b[0] / T)))
    c.append(("合わせ込み: 乗った人の合計 ＝ 降りた人の合計（2万回すべて）", float(np.all(brd.sum(axis=1) == X.sum(axis=1).sum(axis=1))), 1.0, 0.0))
    # --- エンジン: 区画の人数（空の電車から）---
    Mf = get_model()
    nsim = 4000 if not QUICK else 1200
    totals = np.zeros((nsim, 23))
    boards = np.zeros((nsim, 23))
    viol = dict(empty_seat_stander=0, front_gap=0, past_dest=0, n=0, seat_over=0)

    def probe(s, nb, sd, so, fd, fo, ov):
        viol["n"] += 1
        totals[probe.i, s] = sum(1 for x in sd if x >= 0) + sum(1 for x in fd if x >= 0) + len(ov)
        boards[probe.i, s] = nb
        if any(x < 0 for x in sd) and (any(x >= 0 for x in fd) or ov):
            viol["empty_seat_stander"] += 1                    # 空いた席があるのに立つ人がいる
        if ov and any(x < 0 for x in fd):
            viol["front_gap"] += 1                             # 前が空いているのにはみ出して立つ人がいる
        if any(0 <= x <= s for x in sd) or any(0 <= x <= s for x in fd) or any(d <= s for _, d in ov):
            viol["past_dest"] += 1                             # 降りるはずの駅を過ぎてまだ乗っている
        if any(x >= 0 and (so[i] < 0 or so[i] > s) for i, x in enumerate(sd)):
            viol["seat_over"] += 1

    rng3 = random.Random(SEED + 3)
    for i in range(nsim):
        probe.i = i
        trial(Mf, rng3, None, 0, rng3.choice(A_LIST), 23, probe=probe)
    for s_ in (1, 2, 5, 12, 18, 19, 21):
        exp = Mf.f * k * Mf.unit_load[s_]
        c.append((f"エンジン: 空の電車から走らせた {Mf.names[s_]} を出るときの区画の人数の平均 ＝ f×k×(その区間の乗車の積み上げ)（4σ 以内）",
                  float(totals[:, s_].mean()), exp, 4 * totals[:, s_].std() / math.sqrt(nsim)))
    for s_ in (0, 5, 12):
        c.append((f"エンジン: {Mf.names[s_]}で乗る人数の平均 ＝ f×k×乗車（ポアソン・4σ 以内）", float(boards[:, s_].mean()), Mf.lam[s_], 4 * math.sqrt(Mf.lam[s_] / nsim)))
    c.append(("エンジン: 乗る人数の分散 ≒ 平均（ポアソン）立川（比 0.9〜1.1）", float(boards[:, 5].var() / boards[:, 5].mean()), 1.0, 0.1))
    c.append((f"決めごと: 空の電車から走らせた毎駅（{viol['n']}駅ぶん）で、空いた席があるのに立つ人がいた回数", float(viol["empty_seat_stander"]), 0.0, 0.0))
    c.append(("決めごと: 前の立ち位置が空いているのにはみ出して立つ人がいた回数", float(viol["front_gap"]), 0.0, 0.0))
    c.append(("決めごと: 降りる駅を過ぎても乗っている人がいた回数", float(viol["past_dest"]), 0.0, 0.0))
    c.append(("決めごと: 席の人の乗った駅が今の駅より先になっている回数", float(viol["seat_over"]), 0.0, 0.0))
    # --- 決めごと: 席は端から先（エンジンそのものを、高尾で多めに乗る小さな模型で走らせて、乗った直後の席を見る）---
    rng4 = random.Random(SEED + 4)
    order_group = [(0, 6), (1, 5), (2, 4), (3,)]
    Mx = Model(["a", "b"], [5.5, 0.0], [([1], [1.0]), None], nseat=7)
    recs = []

    def pr_(s, nb, sd, so, fd, fo, ov):
        recs.append((nb, list(sd), list(fd), len(ov)))
    ends_ok, count_ok, stand_ok = True, True, True
    left1 = cnt1 = 0
    for _ in range(6000):
        recs.clear()
        trial(Mx, rng4, None, 0, A_MAIN, 1, probe=pr_)
        nb_, sd0, fd0, nov = recs[0]
        occ = [i for i in range(7) if sd0[i] >= 0]
        full_groups = 0
        for g in order_group:
            if all(sd0[i] >= 0 for i in g):
                full_groups += 1
            else:
                break
        ends_ok = ends_ok and all(sd0[i] < 0 for g in order_group[full_groups + 1:] for i in g)
        count_ok = count_ok and len(occ) == min(nb_, 7)
        nstand = sum(1 for x in fd0 if x >= 0) + nov
        stand_ok = stand_ok and nstand == max(0, nb_ - 7) and (nov == max(0, nb_ - 14))
        if nb_ == 1:
            cnt1 += 1
            left1 += occ[0] == 0
    c.append(("決めごと: 空の電車で乗った人は 端(席1・7)→席2・6→席3・5→席4 の順に座る（グループが埋まる前に次のグループには座らない・6000回）", float(ends_ok), 1.0, 0.0))
    c.append(("決めごと: 空の電車で乗った人の数 ＝ 座った人 min(人数,7)（人数 0〜14超・6000回）", float(count_ok), 1.0, 0.0))
    c.append(("決めごと: 席が埋まってから立つ（7人を超えた分が前の7か所に立ち、14人を超えた分だけがはみ出す）", float(stand_ok), 1.0, 0.0))
    c.append((f"決めごと: 1人だけ乗ったとき 端のどちら(席1か席7)に座るかは五分五分（{cnt1}回・4σ）", left1 / cnt1, 0.5, 4 * math.sqrt(0.25 / cnt1)))
    recs2 = []

    def pr2(s, nb, sd, so, fd, fo, ov):
        if s == 0:
            recs2.append(list(sd))
    ok2 = True
    for _ in range(4000):
        trial(Mf, rng4, None, 0, A_MAIN, 1, probe=pr2)
    for sd0 in recs2:
        fg = 0
        for g in order_group:
            if all(sd0[i] >= 0 for i in g):
                fg += 1
            else:
                break
        ok2 = ok2 and all(sd0[i] < 0 for g in order_group[fg + 1:] for i in g)
    c.append(("決めごと: 本物の高尾（空の電車・平均1.65人）でも 席の埋まり方は端から先（4000回）", float(ok2 and len(recs2) == 4000), 1.0, 0.0))
    # --- 空席のルール（v1 と同じ）---
    ntest = 200000
    rng6 = random.Random(SEED + 6)
    full = [0] * 7
    for a_ in (0.6, 0.8):
        for seat in (3, 0, 1):
            cntp = {}
            for _ in range(ntest):
                p = pick_taker(full, seat, a_, rng6, 7)
                cntp[p] = cntp.get(p, 0) + 1
            exp = {seat: a_}
            nbs = [x for x in (seat - 1, seat + 1) if 0 <= x < 7]
            for x in nbs:
                exp[x] = (1 - a_) / len(nbs)
            for p, e in exp.items():
                c.append((f"空席のルール a={a_}: 席{seat + 1}が空いたとき 席{p + 1}の前の人が座る確率（満員）", cntp.get(p, 0) / ntest, e, prop_tol(e, ntest)))
    fd_ = [0, 0, 0, -1, 0, 0, 0]
    cnt3 = sum(1 for _ in range(ntest) if pick_taker(fd_, 3, 0.6, rng6, 7) == 2)
    c.append(("空席のルール: 席4の前が空のとき 席3の前・席5の前が半々（席3の前の確率）", cnt3 / ntest, 0.5, prop_tol(0.5, ntest)))
    fd_ = [-1, -1, -1, -1, 0, -1, -1]
    c.append(("空席のルール: 隣にもいないとき 近くで立っている人（席5の前だけ立っている→席5の前）", float(pick_taker(fd_, 1, 0.6, rng6, 7)), 4.0, 0.0))
    # --- 全通り数え上げ(DP)との一致 ---
    Ms = small_model()
    NN = 120000 if not QUICK else 30000
    Bs, Es = 1, 4
    for a_ in (0.6, 1.0):
        for j_ in (0, 1):
            sit, once, never, tail = exact_small(Ms.lam, Ms.P, 3, a_, j_, Bs, Es, cutoff=7)
            rng7 = random.Random(f"{SEED}|small|{a_}|{j_}")
            hist = {}
            n_once = 0
            for _ in range(NN):
                code, sat, _ = trial(Ms, rng7, Bs, j_, a_, Es)
                if code == ONCE:
                    n_once += 1
                else:
                    hist[sat] = hist.get(sat, 0) + 1
            c.append((f"全通り(席3・駅5つ) a={a_} 席{j_ + 1}の前: 乗った時に座れる確率", n_once / NN, once, prop_tol(once, NN) + tail))
            for s_ in sorted(sit):
                c.append((f"全通り(席3・駅5つ) a={a_} 席{j_ + 1}の前: {s_}駅目で座る確率", hist.get(s_, 0) / NN, sit[s_], prop_tol(sit[s_], NN) + tail))
            c.append((f"全通り(席3・駅5つ) a={a_} 席{j_ + 1}の前: 座れない確率", hist.get(-1, 0) / NN, never, prop_tol(never, NN) + tail))
            c.append((f"全通り(席3・駅5つ) a={a_} 席{j_ + 1}の前: 確率の合計が1（打ち切りで落ちた分 {tail:.1e} まで）", once + sum(sit.values()) + never, 1.0, tail + 1e-9))
    # --- 乱数の固定 ---
    rr1 = run_cell((MAIN_DM, F_BASE, 5, 0, A_MAIN, 0.0, E_TOKYO, "main"))[1]
    key = key_of(MAIN_DM, F_BASE, 5, 0, A_MAIN, 0.0, E_TOKYO, "main")
    c.append(("seed: 同じ条件(立川乗り・席1)をもう一度走らせると 1万回ぶんの座った駅・席の人が全部同じ", float(np.array_equal(rr1["sits"], R["cells"][key]["_sits"]) and np.array_equal(rr1["dst"], R["cells"][key]["_dst"])), 1.0, 0.0))
    # --- 位置・a・別の乱数・関係 ---
    for B in (5, 12):
        e1, e7 = cell(R, B, 0)["tokyo"]["p_sat"], cell(R, B, 6)["tokyo"]["p_sat"]
        c.append((f"対称: {M.names[B]}乗り 席1の前と席7の前の座れる割合が同じ（4σ 以内）", e1, e7, 4 * math.sqrt(0.5 / N) + 0.002))
    for B in B_SET:
        for j_ in (0, 3):
            a1, a2 = cell(R, B, j_)["tokyo"]["p_sat"], cell(R, B, j_, tag="again")["tokyo"]["p_sat"]
            c.append((f"別の乱数: {M.names[B]}乗り 席{j_ + 1}の前の座れる割合（4σ×√2 以内）", a2, a1, 4 * math.sqrt(0.5 / N) + 0.002))
    ok = True
    for B in B_ALL:
        for j_ in POS:
            if cell(R, B, j_)["n_full"] >= MIN_FULL:
                ok = ok and cell(R, B, j_)["shinjuku"]["p_sat"] <= cell(R, B, j_)["tokyo"]["p_sat"] + 1e-12
    c.append(("関係: 新宿で降りる人が座れる割合 ≤ 東京まで乗る人（どの乗る駅・位置でも）", float(ok), 1.0, 0.0))
    # a が大きいほど…: a=1.0 では席1の前でも席4の前でも同じ（席の離れ方に依らず真ん前の人だけが座る）→ 違いは席の人の乗り降りの違いだけ。ここでは単調性だけ見る
    for B in B_Q:
        for E, nm in ((E_TOKYO, "東京"), (E_SHINJUKU, "新宿")):
            if B + 1 >= E:
                continue
            fld = "tokyo" if E == E_TOKYO else "shinjuku"
            seq = [cell(R, B, 3, a=A_MAIN, q=0.0, E=E_TOKYO)[fld]["p_sat"]] + [cell(R, B, 3, a=A_MAIN, q=q, E=E)[fld]["p_sat"] for q in Q_LIST]
            c.append((f"章4: {M.names[B]}乗り→{nm} 席4の前: 見分けられる割合が大きいほど座れる割合が増える（q=0→0.2→0.5→1.0）",
                      float(all(x <= y + 2 * math.sqrt(0.5 / N) for x, y in zip(seq, seq[1:]))), 1.0, 0.0))
    # --- 対照実験: 降りる駅が『降車比例』だけのとき(v1)、端と真ん中の席の人は降りる駅が同じ分布になる ---
    for B in (5, 12, 18):
        sc = seat_class_stats(R, B, dm="v1")
        for fld, nm in (("diff_ge_shinjuku", "新宿以降まで乗る割合"), ("diff_remaining", "あと何駅乗るか")):
            dd = sc[fld]
            c.append((f"対照(降りる駅=降車比例): {M.names[B]}乗り 端と真ん中の席の人の『{nm}』の差が誤差の範囲（4σ）", abs(dd["diff"]), 0.0, 4 * dd["se"] + 1e-9))
    # --- 章4 v3（手の届く3席・先に座る）---
    Mm = get_model()
    n_same = 1500 if not QUICK else 500
    for B_, j_ in ((5, 0), (5, 3), (12, 0), (12, 1)):
        r1, r2 = random.Random(f"v3same|{B_}|{j_}"), random.Random(f"v3same|{B_}|{j_}")
        same = True
        for _ in range(n_same):
            same = same and trial(Mm, r1, B_, j_, A_MAIN, E_TOKYO, 0.0) == trial3(Mm, r2, B_, j_, A_MAIN, E_TOKYO, 0.0)
        c.append((f"章4 v3: q=0 は いまの章4の q=0 と同じ（{Mm.names[B_]}乗り 席{j_ + 1}の前・同じ種で{n_same}回、座った駅も席の人の顔ぶれも全部同じ）", float(same), 1.0, 0.0))
    Ms3 = small_model()
    NN3 = 100000 if not QUICK else 30000
    for j_, q_ in ((0, 0.5), (1, 0.5), (1, 1.0)):
        sit, once, never, tail = exact_small(Ms3.lam, Ms3.P, 3, A_MAIN, j_, 1, 4, cutoff=6, q3=q_)
        rng8 = random.Random(f"{SEED}|small3|{j_}|{q_}")
        hist, n_once3 = {}, 0
        for _ in range(NN3):
            code, sat, _ = trial3(Ms3, rng8, 1, j_, A_MAIN, 4, q_)
            if code == ONCE:
                n_once3 += 1
            else:
                hist[sat] = hist.get(sat, 0) + 1
        c.append((f"全通り・章4 v3(席3・駅5つ) 席{j_ + 1}の前 q={q_}: 乗った時に座れる確率", n_once3 / NN3, once, prop_tol(once, NN3) + tail))
        for s_ in sorted(sit):
            c.append((f"全通り・章4 v3(席3・駅5つ) 席{j_ + 1}の前 q={q_}: {s_}駅目で座る確率", hist.get(s_, 0) / NN3, sit[s_], prop_tol(sit[s_], NN3) + tail))
        c.append((f"全通り・章4 v3(席3・駅5つ) 席{j_ + 1}の前 q={q_}: 座れない確率", hist.get(-1, 0) / NN3, never, prop_tol(never, NN3) + tail))
        c.append((f"全通り・章4 v3(席3・駅5つ) 席{j_ + 1}の前 q={q_}: 確率の合計が1（打ち切りで落ちた分 {tail:.1e} まで）", once + sum(sit.values()) + never, 1.0, tail + 1e-9))
    NI = 3000 if not QUICK else 800
    viol_reach = viol_first = n_prio0 = 0
    for j_ in J_V3:
        reach_ = [k for k in (j_ - 1, j_, j_ + 1) if 0 <= k < 7]
        for q_ in (0.0, 0.2, 0.5, 1.0):
            rng9 = random.Random(f"{SEED}|v3info|{j_}|{q_}")
            draws = flags = 0
            for _ in range(NI):
                info = {}
                code, sat, _ = trial3(Mm, rng9, 12, j_, A_MAIN, E_TOKYO, q_, info=info)
                if code == ONCE:
                    continue
                draws += info.get("draws", 0)
                flags += info.get("flags", 0)
                if "prio_seat" in info:
                    if info["prio_seat"] not in reach_:
                        viol_reach += 1
                    if q_ == 0.0:
                        n_prio0 += 1
                if q_ == 1.0 and "first_dep" in info and (sat < 0 or sat > info["first_dep"]):
                    viol_first += 1
            if q_ in (0.2, 0.5):
                c.append((f"章4 v3: 見抜く判定の成功率 ＝ q（三鷹乗り 席{j_ + 1}の前 q={q_}・判定 {draws} 回・4σ）", flags / draws, q_, 4 * math.sqrt(q_ * (1 - q_) / draws)))
    c.append(("章4 v3: 先に座った席は 必ず 目の前の席か すぐ隣の席（端の前なら2席）の中（q=0〜1.0・席1/2/4の前・違反の数）", float(viol_reach), 0.0, 0.0))
    c.append(("章4 v3: q=0 では 先に座ることが1回もない", float(n_prio0), 0.0, 0.0))
    c.append(("章4 v3: q=1.0 なら 手の届く席の人が最初に降りる駅までには必ず座る（違反の数）", float(viol_first), 0.0, 0.0))
    for B_ in B_V3:
        for E_, nm_ in ((E_TOKYO, "東京"), (E_SHINJUKU, "新宿")):
            fld = "tokyo" if E_ == E_TOKYO else "shinjuku"
            ok = True
            for j_ in J_V3:
                seq = [cell3(R, B_, j_, q_, E_)[fld]["p_sat"] for q_ in Q_V3]
                ok = ok and all(x <= y + 2 * math.sqrt(0.5 / N) for x, y in zip(seq, seq[1:]))
            c.append((f"章4 v3: {M.names[B_]}乗り→{nm_} 席1・2・4の前すべてで q が大きいほど座れる割合が増える（q=0→0.2→0.5→1.0）", float(ok), 1.0, 0.0))
    check_answers(c)
    print(f"  照合 {len(c)} 件 すべて OK")
    return len(c), c


# ====================================================================================================
# 書き出し
# ====================================================================================================
def pc(x, d=1):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.{d}f}%"


def fnum(x, d=1):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def st_name(M, B, n_):
    return "—" if n_ is None else M.names[B + n_]


def sig_diff(R, B, j1=0, j2=3, **kw):
    """席 j1 の前 − 席 j2 の前 の座れる割合の差と、誤差（4σ）を超えているか"""
    a, b = cell(R, B, j1, **kw)["tokyo"], cell(R, B, j2, **kw)["tokyo"]
    if "p_sat" not in a or "p_sat" not in b:
        return None
    d = a["p_sat"] - b["p_sat"]
    se = math.sqrt(a["p_sat"] * (1 - a["p_sat"]) / a["n_full"] + b["p_sat"] * (1 - b["p_sat"]) / b["n_full"])
    return dict(diff=d, se=se, sig=abs(d) > 4 * se)


def worst_pos(R, B, dest="tokyo", **kw):
    ps = {j: cell(R, B, j, **kw)[dest].get("p_sat") for j in POS}
    if any(v is None for v in ps.values()):
        return None
    return min(POS, key=lambda j: ps[j]) + 1


def best_pos(R, B, dest="tokyo", **kw):
    ps = {j: cell(R, B, j, **kw)[dest].get("p_sat") for j in POS}
    if any(v is None for v in ps.values()):
        return None
    return max(POS, key=lambda j: ps[j]) + 1


def write(R, n_checks, checks):
    M = get_model()
    names = M.names
    OUTD = OUT / "trial" if QUICK else OUT
    OUTD.mkdir(parents=True, exist_ok=True)
    st = load_stations()
    M24 = load_od_fast24()
    # ---------------- data.json ----------------
    cells_out = {}
    for k_, v in R["cells"].items():
        cells_out[k_] = {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
    seat_stats = {}
    for B in B_SET:
        for dm in (MAIN_DM, "v1", "od0", "od5000"):
            sc = seat_class_stats(R, B, dm=dm)
            if "classes" in sc:
                for nm in sc["classes"]:
                    for kk in [x for x in sc["classes"][nm] if x.startswith("_")]:
                        del sc["classes"][nm][kk]
            seat_stats[f"{dm}|B{B}"] = sc
    for B in (0, 1, 3, 6, 7, 9, 10, 11, 14, 16, 17):
        sc = seat_class_stats(R, B)
        if "classes" in sc:
            for nm in sc["classes"]:
                for kk in [x for x in sc["classes"][nm] if x.startswith("_")]:
                    del sc["classes"][nm][kk]
        seat_stats[f"{MAIN_DM}|B{B}"] = sc
    byB = {}
    for B in B_ALL:
        cs = [cell(R, B, j) for j in POS]
        n_tr, n_once = cs[0]["n_trials"], cs[0]["n_once"]
        byB[names[B]] = dict(B=B, p_free_at_boarding=n_once / n_tr if n_tr else None, p_full=1 - n_once / n_tr if n_tr else None, n_trials=n_tr,
                             n_full_each_position=[x["n_full"] for x in cs],
                             avg7={fld: pos_avg(R, B, fld) for fld in ("p_sat", "p_never", "p_before_shinjuku", "p_at_shinjuku", "p_after_shinjuku", "mean_n", "mean_n_shinjuku")},
                             avg7_shinjuku={fld: pos_avg(R, B, fld, "shinjuku") for fld in ("p_sat", "p_never", "mean_n")},
                             cdf_avg={kk: sum(w * cell(R, B, j)["tokyo"]["cdf_n"][kk] for j, w in zip(POS, POS_W) if "cdf_n" in cell(R, B, j)["tokyo"]) / 7 for kk in ("1", "2", "3", "4", "6")}
                             if all("cdf_n" in cell(R, B, j)["tokyo"] for j in POS) else None,
                             pmf_station_avg7=[sum(w * cell(R, B, j)["tokyo"]["pmf_station"][x] for j, w in zip(POS, POS_W) if "pmf_station" in cell(R, B, j)["tokyo"]) / 7 for x in range(24)]
                             if all("pmf_station" in cell(R, B, j)["tokyo"] for j in POS) else None,
                             median_n_by_pos=[cell(R, B, j)["tokyo"].get("median_n") for j in POS])
    thumb = build_thumb(R)
    ch4v3 = build_ch4v3(R)
    js = dict(meta=dict(slug=SLUG, version="v2", n=N, seed=SEED, stations=names, a_main=A_MAIN, a_list=list(A_LIST), q_list=list(Q_LIST), f_base=F_BASE,
                        f_list=list(F_LIST), k_prior=K_PRIOR, load_per_car=LOAD_PER_CAR, checks=n_checks, quick=QUICK),
              load=dict(k=M.k, names=names, board_per_car=[M.k * x for x in M.b], load_after_per_car=[M.k * x for x in M.unit_load] + [0.0],
                        compartment_board=M.lam, compartment_load_after=[M.f * M.k * x for x in M.unit_load] + [0.0]),
              by_boarding_station=byB, cells=cells_out, seat_stats=seat_stats, thumb=thumb, ch4v3=ch4v3)
    (OUTD / "data.json").write_text(json.dumps(clean(js), ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------- numbers.md ----------------
    L = [f"# 電車の空席（ロング）v2 の数字（2026-10-21・照合 {n_checks} 件 OK・各条件 席が埋まった回を {N:,} 回・seed {SEED}）", "",
         "公表の数字にもとづく模型。出典と仮定は下に全部書く。会社や路線への評価はしない。v1 は `out/densha-long/v1/` に退避してある。", ""]
    L += ["## 出典（実際に開いて確かめたもの）",
          "- 乗った駅から降りる駅への移動人員（1日）: 国土交通省「大都市交通センサス」第12回(2015年)「線別駅間移動人員」`001179095.xlsx`（首都圏・**定期券の利用区間**・初乗り/乗継ぎ/最終降車の区分は足し合わせ）。"
          "ページ https://www.mlit.go.jp/sogoseisaku/transport/sosei_transport_tk_000035.html ／ ファイル https://www.mlit.go.jp/common/001179095.xlsx （`out/densha-long/src/001179095.xlsx`）。",
          "- 路線・駅コード: 同じページの「コードデータ」の `001179688.xlsx`（鉄道路線コード・首都圏）で 路線コード **002＝東日本旅客鉄道 中央本線**、`001179689.xlsx`（鉄道駅コード・首都圏）で 駅コード 00201(東京)〜00242(笹子)の42駅を確かめた。"
          "快速24駅の駅コードは駅名で引き直した（`src/chuo_station_codes.csv`。高尾=00232、東京=00201）。",
          "- 駅ごとの上りの乗車・降車（1日・乗る人数の大きさ）: 国土交通省「大都市交通センサス」第12回 駅別発着・駅間通過人員表 `001178992.xlsx`（鉄道定期券+普通券 合計・上り。v1 と同じ）。",
          "- 朝の混み具合: 国土交通省 令和7年度の混雑率（資料2-1）https://www.mlit.go.jp/report/press/content/002015141.pdf （`src/mlit_kondo_r7_002015141.pdf` 1ページ目）。"
          "中央(快速) 中野→新宿 7:35〜8:35・10両×28本・輸送力41,440人・輸送人員65,330人・混雑率158%。1両あたり 65,330÷(10×28)＝233.3人。",
          "- 座席数: 動画ではドア間の7人がけとだけ言う。**1両の座席54席は二次情報で公式の資料では確かめられていない（要確認）**。区画の割合 f を決めるためだけに使う（下の仮定）。", ""]
    L += ["## 移動人員表の読み取り方（コードの確かめ方・結果）", "",
          "1. 路線コード表で `002` ＝ 中央本線（東日本旅客鉄道・事業者コード01）が1件だけあることを確かめた。",
          "2. 駅コード表で 路線002 の駅は 00201〜00242 の42駅。快速24駅の名前（表の綴りは 阿佐ヶ谷・四ッ谷）から駅コードを引いた。コードは東京=201 から西へ増え、高尾=232。**上り（東京へ向かう）＝乗車駅コード＞降車駅コード**。",
          "3. 移動人員表は 6列（路線コード・乗車駅コード・初乗り乗継の区分・降車駅コード・最終降車乗継の区分・人員）。路線コード2の行は 1,223行・合計 743,313 人/日。"
          "区分の1〜3は足し合わせた（その駅間を電車に乗っていることは同じ）。",
          "4. **突き合わせ**: 駅別発着表(001178992)の『定期券・上り』の乗車は、移動人員表の『上り向きの駅対で i から乗る人 ＋ 下り向きの駅対で i で降りる人』と、全42駅で1人も違わず一致した（降車も同様）。"
          "全行の合計 743,313 は駅別発着表の定期の上り乗車の合計と同じ。コードと向きの読み方は正しい。",
          f"5. 上りの駅対は {len(_od_up_all())}組・合計 {sum(_od_up_all().values()):,} 人/日、下り向きは 269組・254,083 人/日（東京側に住み西側で働く人など）。**朝の上りの電車に乗るのは上り向きの側**として、下り向きの駅対は使わない。",
          f"6. 快速24駅どうしの上り向きの駅対は {sum(map(sum, M24)):,} 人/日（上り向き全体の {sum(map(sum, M24)) / sum(_od_up_all().values()) * 100:.1f}%）。総武線各駅停車は別の路線コード008（千葉〜三鷹の39駅）で、この表（路線002）には入っていない。",
          ""]
    L += ["### 快速の停車駅でない駅の扱い（決めごと）", "",
          "- 乗る駅も降りる駅も **快速の停車駅24駅どうしの駅対だけ**使う。片方でも快速が停まらない駅（東中野・大久保・代々木・信濃町・千駄ヶ谷・市ヶ谷・飯田橋・水道橋・相模湖より西）がかかる駅対は、"
          "その人は快速に乗らないと見なして落とす（残った人数で割り直す＝快速の駅だけで確率を作り直す）。",
          "- 落とした割合は乗る駅ごとに次の表のとおり。多くの駅は 0〜10%、新宿から乗る人は約11%、四ツ谷から乗る人は約56%。四ツ谷・新宿から乗る人の降りる先には代々木・信濃町・市ヶ谷など快速が停まらない駅が多いため。",
          ""]
    L += ["| 乗る駅 | 上り向きで乗る人(全駅対) | うち快速24駅どうし | 落とした割合 | 表の重み n/(n+K) (K=1,000) |", "|---|---|---|---|---|"]
    allup = {}
    for (b_, a_), v in _od_up_all().items():
        allup[b_] = allup.get(b_, 0) + v
    codes = load_codes()
    for i in range(23):
        code = int(codes[i]["station_code"])
        tot = allup.get(code, 0)
        ff = sum(M24[i])
        w = ff / (ff + K_PRIOR) if ff + K_PRIOR > 0 else 0
        L.append(f"| {names[i]} | {tot:,} | {ff:,} | {pc(1 - ff / tot) if tot else '—'} | {pc(w, 0)} |")
    L += ["", "表が薄い駅（上の『n』が小さい）は、降車比例（v1）と **n : K = 表の人数 : 1,000人** の比で混ぜる（K は【仮定】）。"
          "神田（表に上りで乗る人がいない）は降車比例だけ。感度として K=0（表だけ）・K=5,000・降車比例だけ（v1）でも出す。", ""]
    L += ["### 乗った駅ごとの降りる駅の割合（主な駅・混ぜたあと・%）", "",
          "| 乗る駅＼降りる駅 | " + " | ".join(names[d] for d in (5, 8, 12, 13, 15, 18, 19, 20, 21, 22, 23)) + " | 新宿以降まで(新宿を含む) | 新宿より先 |", "|---|" + "---|" * 13]
    for t in (0, 2, 5, 8, 12, 13, 15, 18):
        dm = dict(zip(*M.P[t]))
        L.append(f"| {names[t]} | " + " | ".join((f"{dm[d] * 100:.0f}" if d in dm else "") for d in (5, 8, 12, 13, 15, 18, 19, 20, 21, 22, 23)) + " | "
                 + f"{sum(p for d, p in dm.items() if d >= 19) * 100:.0f} | {sum(p for d, p in dm.items() if d > 19) * 100:.0f} |")
    L.append("")
    L += ["## 抜き出した駅ごとの数字（上り・1日・人。乗る人数の大きさに使う）", "", "| order | 駅 | 乗車 | 降車 | 通過(その駅に入る区間) |", "|---|---|---|---|---|"]
    for r in st:
        L.append(f"| {r['order']} | {r['name']} | {r['board']:,} | {r['alight']:,} | {r['through']:,} |")
    L += ["", "注意:",
          "- 乗る人数の大きさは 駅別発着表の『上りの乗車』（定期券+普通券の合計。下り向きに通勤する人の帰りの上りも含む）。降りる駅の割合は 移動人員表の定期券。券種と時間帯が違う二つの表を組み合わせている。",
          "- 快速の停車駅24駅は依頼者の指定。停車パターンは列車・時間帯で違う可能性があり、検証していない。",
          "- 1日（終日）の数字を朝の1本の代わりに使っている。朝のピークは郊外側から都心へ偏るので、実際の朝の形とは違う。", ""]
    L += ["## 合わせ込み（中野→新宿で1両 233.3人）と区画の人数", "",
          f"- 倍率 k ＝ {M.k:.6f}（降りる駅の割合が決まったあと、中野→新宿の1両が233.3人になるように決めた。1日の乗車1人あたり1両に乗る人数）。",
          f"- 区画の割合 f ＝ 7/54 ＝ {F_BASE:.4f}【仮定・要確認】: 1両の人のうち、このドア間7人掛けの区画（席7＋前に立つ7か所）に入る人の割合。区画に乗る人数 ＝ 1両に乗る人数 × f（ポアソン）。f=0.12・0.15 でも出す。",
          "- 区画の人数は、席7＋前の立ち位置7＝14人を超えると、残りは『はみ出して立つ人』になる（前の7か所が空くと先に埋める）。", "",
          "| 駅 | 1両に乗る人（平均） | 駅を出るときの1両の人数 | 区画に乗る人（平均） | 駅を出るときの区画の人数 | 席7が埋まる目安 |", "|---|---|---|---|---|---|"]
    for i in range(23):
        la = M.f * M.k * M.unit_load[i]
        L.append(f"| {names[i]} | {M.k * M.b[i]:.1f} | {M.k * M.unit_load[i]:.1f} | {M.lam[i]:.2f} | {la:.1f} | {'席が埋まる(7以上)' if la >= 7 else ''} |")
    L.append("")

    # ---------------- 章1・3 ----------------
    L += ["## 章1・3 乗る駅ごとに: 座れる？ 座れないとき何駅で座れる？（a=0.6・7か所の平均・東京まで乗る）", "",
          "『座席が空いていた』＝ 乗った瞬間に座れた回。『埋まっていた』回だけ、立って座れるまで何駅かを数える（下の表は埋まっていた回の中の割合）。", "",
          "| 乗る駅 | 乗った瞬間に座れる | 席が埋まっている | 座れた人の平均(駅) | 真ん中の値 | 東京まで座れない | 新宿の手前までに座る | 新宿で座る | 新宿までに座る(新宿を含む) | 新宿より先で座る | 3駅以内に座る |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for B in B_ALL:
        d_ = byB[names[B]]
        a7 = d_["avg7"]
        if d_["n_full_each_position"][0] < MIN_FULL:
            L.append(f"| {names[B]} | {pc(d_['p_free_at_boarding'])} | {pc(d_['p_full'], 2)}（{d_['n_trials']:,}回中 {d_['n_full_each_position'][0]:,}回。少なすぎて分布は出さない） | | | | | | | | |")
            continue
        meds = d_["median_n_by_pos"]
        med7 = _median_n_avg(R, B)
        L.append(f"| {names[B]} | {pc(d_['p_free_at_boarding'])} | {pc(d_['p_full'])} | {fnum(a7['mean_n'])}駅 | {med7} | **{pc(a7['p_never'])}** | {pc(a7['p_before_shinjuku'])} | {pc(a7['p_at_shinjuku'])} | {pc(a7['p_before_shinjuku'] + a7['p_at_shinjuku'])} | {pc(a7['p_after_shinjuku'])} | "
                 f"{pc(d_['cdf_avg']['3']) if d_['cdf_avg'] else '—'} |")
    L += ["", "（『真ん中の値』＝埋まっていた回を座れた早い順に並べて半分に届くのが何駅目か。届かないときは『座れない側が半数以上』。4つの立ち位置（席1〜4の前）を 2:2:2:1 で平均して7か所の値にしてある。）", ""]
    L += ["### 新宿で降りる場合（a=0.6・7か所の平均・埋まっていた回の中）", "", "| 乗る駅 | 新宿まで座れない | 座れた人の平均(駅) |", "|---|---|---|"]
    for B in B_ALL[:-1]:
        d_ = byB[names[B]]
        if d_["n_full_each_position"][0] < MIN_FULL:
            continue
        a7 = d_["avg7_shinjuku"]
        L.append(f"| {names[B]} | {pc(a7['p_never'])} | {fnum(a7['mean_n'])}駅 |")
    L.append("")
    for B in (5, 12, 13):
        d_ = byB[names[B]]
        if d_["pmf_station_avg7"] is None:
            continue
        L += [f"### {names[B]}で乗って席が埋まっていたときに、座る駅の分布（7か所平均・東京まで乗る・埋まっていた回の中の%）", "",
              "| 座る駅 | " + " | ".join(names[x] for x in range(B + 1, 23)) + " | 座れない |", "|---|" + "---|" * (23 - B),
              "| 確率 | " + " | ".join(f"{d_['pmf_station_avg7'][x] * 100:.1f}" for x in range(B + 1, 23)) + f" | {d_['avg7']['p_never'] * 100:.1f} |", ""]
    # ---------------- 章2 ----------------
    L += ["## 章2 立つ位置で比べる: 端の前・端の隣の前・真ん中の前（a=0.6・席が埋まっていた回の中で、東京までに座れる割合）", "",
          "| 乗る駅 | 席1の前(端) | 席2の前(端の隣) | 席3の前 | 席4の前(真ん中) | 端−真ん中 | 端−端の隣 | 一番高い位置 |", "|---|---|---|---|---|---|---|---|"]
    for B in B_ALL:
        if cell(R, B, 0)["n_full"] < MIN_FULL:
            continue
        ps = [cell(R, B, j)["tokyo"] for j in POS]
        d14, d12 = sig_diff(R, B, 0, 3), sig_diff(R, B, 0, 1)
        L.append(f"| {names[B]} | " + " | ".join(f"{pc(p['p_sat'])}（{fnum(p['mean_n'])}駅）" for p in ps)
                 + f" | {d14['diff'] * 100:+.1f}点{'（差あり）' if d14['sig'] else '（誤差内）'} | {d12['diff'] * 100:+.1f}点{'（差あり）' if d12['sig'] else '（誤差内）'} | 席{best_pos(R, B)} |")
    L += ["", "（『差あり』は 差が 4σ を超えるとき。付かない所は誤差の範囲。席が埋まっていた回の数は各位置で約1万。）", ""]
    nb_ = [B for B in B_ALL if cell(R, B, 0)["n_full"] >= MIN_FULL]
    n_worse = sum(1 for B in nb_ if sig_diff(R, B, 0, 3)["sig"] and sig_diff(R, B, 0, 3)["diff"] < 0)
    n_better = sum(1 for B in nb_ if sig_diff(R, B, 0, 3)["sig"] and sig_diff(R, B, 0, 3)["diff"] > 0)
    L.append(f"- 乗る駅 {len(nb_)} か所のうち、端の前(席1)が真ん中の前(席4)より **座れる割合が低いと言える駅 {n_worse}、高いと言える駅 {n_better}**（残りは誤差の範囲）。")
    L.append("")
    # ---------------- 仮説 ----------------
    L += ["## 章2 ユーザーの仮説: 『端には長く乗る人が座っている（始発に近い駅から乗った人が端を取るので、遠くまで乗る）』", "",
          "あなたが乗って席がすべて埋まっていた瞬間の、各席の人の顔ぶれ（a=0.6・位置を混ぜた約4万回）。端＝席1・7、端の隣＝席2・6、真ん中＝席4。", "",
          "| 乗る駅 | 席 | 乗った駅の平均 | 八王子以西から乗った人 | 新宿以降まで乗る(新宿含む) | **新宿より先まで乗る** | 東京まで乗る | 次の駅で降りる | あと平均(駅) | 端−真ん中の差(新宿以降) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for B in B_SET:
        sc = seat_class_stats(R, B)
        if "classes" not in sc:
            continue
        for ci, (nm, v) in enumerate(sc["classes"].items()):
            if nm == "席3・5":
                continue
            ex = ""
            if nm.startswith("端("):
                z = sc["diff_ge_shinjuku"]
                ex = f"{z['diff'] * 100:+.1f}点 (z={z['z']:+.1f})"
            L.append(f"| {names[B] if ci == 0 else ''} | {nm} | {names[int(round(v['mean_origin']))]}（{v['mean_origin']:.1f}） | {pc(v['p_origin_le_hachioji'])} | {pc(v['p_dest_ge_shinjuku'])} | {pc(v['p_dest_gt_shinjuku'])} | "
                     f"{pc(v['p_dest_tokyo'])} | {pc(v['p_next'])} | {v['mean_remaining']:.1f} | {ex} |")
    L += ["", "（『乗った駅の平均』は駅の番号（高尾0〜東京23）の平均を四捨五入した駅名。差の z は 席ごとでなく 1回ごとに『端の席の人の平均−真ん中の席の人』を取った平均÷標準誤差。|z|>4 なら差あり。）", ""]
    L += ["### 仮説に当たる/外れる、そのままの要約", ""]
    for B in B_SET:
        sc = seat_class_stats(R, B)
        if "classes" not in sc:
            continue
        e, m = sc["classes"]["端(席1・7)"], sc["classes"]["真ん中(席4)"]
        zz = sc["diff_ge_shinjuku"]
        zr = sc["diff_remaining"]
        zo = sc["diff_origin"]
        L.append(f"- {names[B]}乗り: 端の席の人は 新宿以降まで乗る {pc(e['p_dest_ge_shinjuku'])}／真ん中の席の人は {pc(m['p_dest_ge_shinjuku'])}（差 {zz['diff'] * 100:+.1f}点・z={zz['z']:+.1f}）。"
                 f"あと乗る駅数は 端 {e['mean_remaining']:.1f} ／ 真ん中 {m['mean_remaining']:.1f}（差 {zr['diff']:+.2f}駅・z={zr['z']:+.1f}）。"
                 f"乗った駅の番号の平均は 端 {e['mean_origin']:.1f} ／ 真ん中 {m['mean_origin']:.1f}（差 {zo['diff']:+.2f}・z={zo['z']:+.1f}）。")
    L += ["", "対照: 降りる駅を『降車の多さに比例（v1）』にしたとき（降りる駅が乗った駅と無関係に決まるので、端でも真ん中でも同じになるはず）:", ""]
    for B in B_SET:
        sc = seat_class_stats(R, B, dm="v1")
        if "classes" not in sc:
            continue
        e, m = sc["classes"]["端(席1・7)"], sc["classes"]["真ん中(席4)"]
        zz, zr = sc["diff_ge_shinjuku"], sc["diff_remaining"]
        L.append(f"- (v1型) {names[B]}乗り: 新宿以降まで乗る 端 {pc(e['p_dest_ge_shinjuku'])} ／ 真ん中 {pc(m['p_dest_ge_shinjuku'])}（差 {zz['diff'] * 100:+.1f}点・z={zz['z']:+.1f}）／ あと乗る駅数 端 {e['mean_remaining']:.2f} 真ん中 {m['mean_remaining']:.2f}（z={zr['z']:+.1f}）")
    L.append("")
    L += ["### 降りる駅の分布（席の種類別・埋まっていた回の席の人。%）", ""]
    for B in (5, 12):
        sc = seat_class_stats(R, B)
        if "classes" not in sc:
            continue
        L += [f"**{names[B]}で乗ったとき**", "", "| 席 | " + " | ".join(names[x] for x in range(B + 1, 24)) + " |", "|---|" + "---|" * (23 - B)]
        for nm in ("端(席1・7)", "端の隣(席2・6)", "真ん中(席4)"):
            v = sc["classes"][nm]
            L.append(f"| {nm} | " + " | ".join(f"{v['dest_pmf'][x] * 100:.0f}" for x in range(B + 1, 24)) + " |")
        L += ["", "| 席 | 乗った駅の割合（%） |", "|---|---|"]
        for nm in ("端(席1・7)", "端の隣(席2・6)", "真ん中(席4)"):
            v = sc["classes"][nm]
            L.append(f"| {nm} | " + "　".join(f"{names[x]}{v['origin_pmf'][x] * 100:.0f}" for x in range(0, B + 1) if v['origin_pmf'][x] > 0.004) + " |")
        L.append("")
    # ---------------- 感度 ----------------
    L += ["## a の感度（東京まで乗る・埋まっていた回の中の座れる割合）", "",
          "| a | 乗る駅 | 席1の前 | 席2の前 | 席3の前 | 席4の前 | 端−真ん中 | 一番高い位置 |", "|---|---|---|---|---|---|---|---|"]
    for a_ in A_LIST:
        for B in B_SET:
            if cell(R, B, 0, a=a_)["n_full"] < MIN_FULL:
                continue
            ps = [cell(R, B, j, a=a_)["tokyo"]["p_sat"] for j in POS]
            sd_ = sig_diff(R, B, 0, 3, a=a_)
            L.append(f"| {a_} | {names[B]} | " + " | ".join(pc(p) for p in ps) + f" | {sd_['diff'] * 100:+.1f}点{'*' if sd_['sig'] else ''} | 席{best_pos(R, B, a=a_)} |")
    L += ["", "（*は差が 4σ より大きい。）", ""]
    L += ["## 区画の割合 f の感度（a=0.6・東京まで乗る）", "",
          "| f | 乗る駅 | 席が埋まっている | 席1の前 | 席2の前 | 席3の前 | 席4の前 | 端−真ん中 | 一番高い位置 | 7か所平均の東京まで座れない |", "|---|---|---|---|---|---|---|---|---|---|"]
    for f in F_LIST:
        for B in B_SET:
            c0 = cell(R, B, 0, f=f)
            if c0["n_full"] < MIN_FULL:
                continue
            ps = [cell(R, B, j, f=f)["tokyo"]["p_sat"] for j in POS]
            sd_ = sig_diff(R, B, 0, 3, f=f)
            L.append(f"| {f:.4f} | {names[B]} | {pc(1 - c0['n_once'] / c0['n_trials'])} | " + " | ".join(pc(p) for p in ps)
                     + f" | {sd_['diff'] * 100:+.1f}点{'*' if sd_['sig'] else ''} | 席{best_pos(R, B, f=f)} | {pc(pos_avg(R, B, 'p_never', f=f))} |")
    L.append("")
    L += ["## 降りる駅の決めかたの感度（a=0.6・f=7/54・東京まで乗る）: 表＋降車比例(K=1,000, 主) ／ 表だけ(K=0) ／ K=5,000 ／ 降車比例だけ(v1型)", "",
          "| 乗る駅 | 決めかた | 席1の前 | 席2の前 | 席3の前 | 席4の前 | 端−真ん中 | 一番高い位置 | 7か所平均の東京まで座れない | 7か所平均の新宿の手前までに座る |", "|---|---|---|---|---|---|---|---|---|---|"]
    for B in B_SET:
        for dm, lab in ((MAIN_DM, "表+降車比例(主)"), ("od0", "表だけ"), ("od5000", "K=5,000"), ("v1", "降車比例だけ")):
            if cell(R, B, 0, dm=dm)["n_full"] < MIN_FULL:
                continue
            ps = [cell(R, B, j, dm=dm)["tokyo"]["p_sat"] for j in POS]
            sd_ = sig_diff(R, B, 0, 3, dm=dm)
            L.append(f"| {names[B]} | {lab} | " + " | ".join(pc(p) for p in ps) + f" | {sd_['diff'] * 100:+.1f}点{'*' if sd_['sig'] else ''} | 席{best_pos(R, B, dm=dm)} | "
                     f"{pc(pos_avg(R, B, 'p_never', dm=dm))} | {pc(pos_avg(R, B, 'p_before_shinjuku', dm=dm))} |")
    L.append("")
    # 答えが変わるか
    L += ["### 『いちばん座れる位置』は感度で変わるか", ""]
    bests = {}
    for lab, kw in (("主", {}), ("a=0.5", dict(a=0.5)), ("a=0.8", dict(a=0.8)), ("a=1.0", dict(a=1.0)), ("f=0.12", dict(f=0.12)), ("f=0.15", dict(f=0.15)),
                    ("表だけ", dict(dm="od0")), ("K=5000", dict(dm="od5000")), ("降車比例だけ", dict(dm="v1"))):
        row = []
        for B in B_SET:
            if cell(R, B, 0, **kw)["n_full"] < MIN_FULL:
                row.append("—")
                continue
            bp = best_pos(R, B, **kw)
            sd_ = sig_diff(R, B, 0, 3, **kw)
            row.append(f"席{bp}{'*' if sd_['sig'] else ''}")
            bests.setdefault(B, []).append(bp)
        L.append(f"- {lab}: " + "／".join(f"{names[B]} {x}" for B, x in zip(B_SET, row)))
    L += ["", "いちばん座りにくい位置（席1〜4の前のうち最も低い）:", ""]
    for lab, kw in (("主", {}), ("a=0.5", dict(a=0.5)), ("a=0.8", dict(a=0.8)), ("a=1.0", dict(a=1.0)), ("f=0.12", dict(f=0.12)), ("f=0.15", dict(f=0.15)),
                    ("表だけ", dict(dm="od0")), ("K=5000", dict(dm="od5000")), ("降車比例だけ", dict(dm="v1"))):
        row = [("席%d" % worst_pos(R, B, **kw)) if cell(R, B, 0, **kw)["n_full"] >= MIN_FULL else "—" for B in B_SET]
        L.append(f"- {lab}: " + "／".join(f"{names[B]} {x}" for B, x in zip(B_SET, row)))
    L += ["", "（*＝端−真ん中が 4σ を超えて差あり。席2の前・席3の前・席1の前などの順位は誤差で入れ替わりうる。）", ""]

    # ---------------- 章4 ----------------
    L += ["## 章4 降りそうな人が分かるとき（席4の前・席2の前・席1の前から始める。見分けた席の前へ移る）", "",
          "q ＝ 『次の駅で降りる人』を、座っている人のうちそれぞれ確率 q で見分けられる（見間違いはなし）。a=0.6。埋まっていた回の中の割合。", "",
          "| 乗る駅 | 降りる駅 | 立つ位置 | q=0 座れる割合(平均駅数) | q=0.2 | q=0.5 | q=1.0 |", "|---|---|---|---|---|---|---|"]
    for B in B_Q:
        for E, nm, fld in ((E_TOKYO, "東京", "tokyo"), (E_SHINJUKU, "新宿", "shinjuku")):
            if B + 1 >= E:
                continue
            for j in (3, 1, 0):
                row = [cell(R, B, j, a=A_MAIN, q=0.0, E=E_TOKYO)[fld]]
                row += [cell(R, B, j, a=A_MAIN, q=q, E=E)[fld] for q in Q_LIST]
                L.append(f"| {names[B]} | {nm} | 席{j + 1}の前 | " + " | ".join(f"{pc(x['p_sat'])}（{fnum(x['mean_n'])}駅）" for x in row) + " |")
    L.append("")
    # ---------------- 章4 v3 ----------------
    L += ["## 章4 v3 降りそうな人が分かるとき（手が届くのは目の前と隣の席だけ・見抜いたら先に座る）【上の章4とは別の決めごと。上の章4はそのまま残してある】", "",
          "決めごと:",
          "- あなたが手を出せるのは **目の前の席と、すぐ隣の2席だけ**（端の前なら隣は1席）。遠くの席の前へは移らない。立っている人と入れ替わることもしない。",
          "- その3席（端の前なら2席）に座っている人のうち、**次の駅で降りる人**を、1人ずつ確率 q で前もって見抜ける（見間違いなし）。上の3席より遠くの席の人は見抜けない。",
          "- **見抜いた人の席が空いたら、あなたが先に座る**（その席の真ん前に別の人が立っていても、あなたが先に動けたとする）。見抜けなかった席は、いまのルール（真ん前の人が a=0.6、残りは両隣で分ける）のまま。",
          "- q=0 は 上の章4の q=0 と同じ電車（何もしない）。ほかの部分（乗る人・降りる駅・席の埋まり方・a）は上と同じ。席がすべて埋まっていた回だけを数え、各条件 約1万回。", "",
          "| 乗る駅 | 降りる駅 | 立つ位置 | q=0 座れる割合(平均駅数) | q=0.2 | q=0.5 | q=1.0 |", "|---|---|---|---|---|---|---|"]
    for r_ in [x for x in ch4v3["table"] if x["q"] == 0.0]:
        qs = [y for y in ch4v3["table"] if y["B"] == r_["B"] and y["E"] == r_["E"] and y["j"] == r_["j"]]
        L.append(f"| {r_['station']} | {r_['dest']} | {r_['pos']} | " + " | ".join(f"{pc(y['p_sat'])}（{fnum(y['mean_n'])}駅）" for y in qs) + " |")
    L += ["", "### 端の前で q=0.2 は、端の隣の前で何もしない(q=0)を上回るか", "",
          "| 乗る駅 | 降りる駅 | 比べるもの | 左 | 右 | 差（左−右） | 判定（4σ） |", "|---|---|---|---|---|---|---|"]
    for d_ in ch4v3["compare"]:
        L.append(f"| {d_['station']} | {d_['dest']} | {d_['label']} | {pc(d_['a']['p_sat'])}（{fnum(d_['a']['mean_n'])}駅） | {pc(d_['b']['p_sat'])}（{fnum(d_['b']['mean_n'])}駅） | "
                 f"{d_['diff'] * 100:+.1f}点 | {d_['verdict']} |")
    L += ["", "（判定＝差が 4σ を超えるとき『上回る／下回る』、それ以外は『誤差の範囲』。左右とも席が埋まっていた回の中の割合。）", ""]
    # ---------------- サムネ ----------------
    L += ["## サムネの数字の候補（「新宿」「2割」の根拠。data.json の thumb にも入れた）", ""]
    for s_ in thumb["notes"]:
        L.append(f"- {s_}")
    L.append("")
    # ---------------- 仮定 ----------------
    L += ["## 仮定の一覧（動画内と概要欄で明記する）", "",
          "1. 区間・停車駅: 中央線快速の上り 高尾→東京の快速停車駅24駅（依頼者の指定）。時間帯は朝の上りだけを想定。",
          "2. 乗る人数の大きさ: 国土交通省センサス(2015)の1日の上りの乗車の比（券種・時間帯が違う二つの表の組み合わせ）。各駅で ポアソン(f×k×その駅の乗車)。k は中野→新宿の1両の平均が 233.3人になるように決めた。",
          "3. 降りる駅【公表の数字＋仮定】: 乗った駅 i から降りる駅 j（東京側）は、センサスの『線別駅間移動人員』（中央本線・上り向き・定期券・快速24駅どうし）の人数に比例。"
          f"表の人数 n が少ない駅は 降車比例（v1）と n : K（K={K_PRIOR:,}人）で混ぜる【K は仮定】。快速が停まらない駅がかかる駅対は落とす。定期券の利用区間であり、普通券の人・時間帯別の乗り降りは含まない。",
          "4. 区画の割合 f【仮定・要確認】: 1両の人のうち区画（席7＋前7）に入る割合 ＝ 7/54（ドア間7人掛け÷1両の座席54の二次情報）。0.12・0.15 でも出して答えが変わるか確かめた。",
          "5. 区画: ドア間7人掛けの1区画。席1・席7が端、席4が真ん中。前の立ち位置は席ごとに1か所の7か所。前がいっぱいになったら、はみ出して立つ（席の割り当てには関与しないが、前が空いたら先に入る）。",
          "6. 席の埋まり方【仮定】: 高尾で空の1両。乗った人は空いた席があれば座る。端(席1・7)→端の隣(席2・6)→席3・5→席4の順に好む（同じ順位が空いていれば五分五分）。席が埋まったら立つ。立つ人は前の7か所のうちランダムな空きから先に埋める。",
          "7. 席が空いたとき【仮定・v1と同じ】: 真ん前の人が確率 a で座る。残りは両隣の席の前の人が等分（端の席は隣が1つだけ）。前に誰もいなければ隣、隣もいなければ近くで立っている人。同じ駅で複数空いたら順番はランダム。座った人の立ち位置は、はみ出していた人が埋める。a の既定値は 0.6、0.5・0.8・1.0 でも出す。",
          "8. 駅での順番: 降りる→前が埋まる→空いた席に前の人が座る→乗ってくる人（ランダムな順で、空席があれば座る）。すでに立っている人が、同じ駅で乗ってくる人より先に空席を取る。",
          "9. 座った人は降りるまで席を空けない。",
          "10. あなた: 指定した駅で乗る。その駅で乗ってくる人の中にランダムな順番で混ざり、空いた席があれば座る（座れた回は『乗った瞬間に座れた』として別に数える）。座れなければ席 j の前に立つ（そこにいた人ははみ出して立つ人になる）。席がすべて埋まっていた回だけを数える。降りるのは東京（比べるときは新宿）。",
          "11. 降りそうな人(章4): 座っている人のうち次の駅で降りる人を、それぞれ確率 q で見分けられ、見分けたら（複数なら近い席を選んで）その席の前に移る（そこにいる人と入れ替わる）。移るのに時間や邪魔はなし。",
          "11b. 降りそうな人(章4 v3・別の結果): 手が届くのは目の前の席と隣の席だけで、その席の人のうち次の駅で降りる人を確率 q で見抜き、見抜いた席が空いたらあなたが先に座る。立っている人と入れ替わらず、遠くの席の前へも移らない。見抜けなかった席は a のルールのまま。",
          "12. 『1回』は 1本の電車の区画1つを高尾から走らせた1回。席が埋まっていた回を、乗る駅・位置・a・f ごとに1万回集める（seed 固定）。埋まる回が少ない乗る駅は、試行 30万回で打ち切る。",
          "13. 座席数54席: 公式の資料で確認できなかった（要確認）。f の値の根拠にだけ使い、動画では『ドア間の7人がけ』とだけ言う。", ""]
    L += ["## 照合した内容（すべて OK）", ""]
    for name, sim, exact, tol in checks:
        L.append(f"- {name}: シミュ {sim:.4g} ／ 理論 {exact:.4g} ／ 許容 ±{tol:.3g}")
    (OUTD / "numbers.md").write_text("\n".join(L), encoding="utf-8")



CH4V3_RULE = ("章4 v3 の決めごと: あなたが手を出せるのは 目の前の席と すぐ隣の2席だけ（端の前なら隣は1席）。遠くの席の前へは移らず、立っている人とも入れ替わらない。"
              "その3席（端の前なら2席）に座っている人のうち 次の駅で降りる人を、1人ずつ確率 q で前もって見抜ける（見間違いなし）。"
              "見抜いた人の席が空いたら あなたが先に座る（真ん前に別の人が立っていても）。見抜けなかった席は いまのルール（真ん前の人が a=0.6、残りは両隣で分ける）のまま。")


def build_ch4v3(R):
    """章4 v3 の結果（data.json の ch4v3）。table＝乗る駅×降りる駅×位置×q、compare＝端の前(q) と 端の隣の前(q=0) など"""
    M = get_model()
    rows, cells = [], {}
    for B in B_V3:
        for E, nm, fld in ((E_SHINJUKU, "新宿", "shinjuku"), (E_TOKYO, "東京", "tokyo")):
            for j in J_V3:
                for q in Q_V3:
                    c = cell3(R, B, j, q, E)
                    x = c[fld]
                    r = dict(station=M.names[B], B=B, dest=nm, E=E, pos=f"席{j + 1}の前", j=j + 1, q=q, p_sat=x["p_sat"], mean_n=x["mean_n"], n_full=c["n_full"],
                             p_free_at_boarding=c["n_once"] / c["n_trials"])
                    rows.append(r)
                    cells[f"B{B}|E{E}|j{j + 1}|q{q}"] = r

    def cmp_(B, E, fld, ja, qa, jb, qb):
        a, b = cell3(R, B, ja, qa, E), cell3(R, B, jb, qb, E)
        pa, pb = a[fld]["p_sat"], b[fld]["p_sat"]
        se = math.sqrt(pa * (1 - pa) / a["n_full"] + pb * (1 - pb) / b["n_full"])
        d = pa - pb
        return dict(a=dict(pos=f"席{ja + 1}の前", q=qa, p_sat=pa, mean_n=a[fld]["mean_n"]), b=dict(pos=f"席{jb + 1}の前", q=qb, p_sat=pb, mean_n=b[fld]["mean_n"]),
                    diff=d, se=se, z=d / se if se > 0 else 0.0, verdict="上回る" if d > 4 * se else ("下回る" if d < -4 * se else "誤差の範囲"))
    compare = []
    for B in B_V3:
        for E, nm, fld in ((E_SHINJUKU, "新宿", "shinjuku"), (E_TOKYO, "東京", "tokyo")):
            for (ja, qa, jb, qb, lab) in ((0, 0.2, 1, 0.0, "端の前 q=0.2 対 端の隣の前 q=0"), (0, 0.5, 1, 0.0, "端の前 q=0.5 対 端の隣の前 q=0"),
                                          (0, 0.2, 3, 0.0, "端の前 q=0.2 対 真ん中の前 q=0"), (0, 0.2, 1, 0.2, "端の前 q=0.2 対 端の隣の前 q=0.2"),
                                          (0, 0.0, 1, 0.0, "端の前 q=0 対 端の隣の前 q=0（何もしないとき）")):
                d = cmp_(B, E, fld, ja, qa, jb, qb)
                d.update(station=M.names[B], dest=nm, label=lab)
                compare.append(d)
    return dict(rule=CH4V3_RULE, q_list=list(Q_V3), stations=[M.names[b] for b in B_V3], positions=[f"席{j + 1}の前" for j in J_V3], n=N, seed=SEED, a=A_MAIN,
                note="q=0 は main の章4(q=0)のセル。座れる割合は『席がすべて埋まっていた回』の中。mean_n は座れた人の平均駅数。",
                table=rows, cells=cells, compare=compare)


def _median_n_avg(R, B):
    """7か所平均の累積が 0.5 に届く最初の駅数（座れた回の割合を、埋まっていた回全体に対して数える）"""
    M = get_model()
    sat = [cell(R, B, j)["_sits"].astype(int) for j in POS]
    for k in range(1, 23 - B):
        cum = sum(w * float(np.mean((x >= 0) & ((x - B) <= k))) for x, w in zip(sat, POS_W)) / 7
        if cum >= 0.5:
            return f"{k}駅目（{M.names[B + k]}）"
    return "座れない側が半数以上"


_ODUP = None


def _od_up_all():
    global _ODUP
    if _ODUP is None:
        with open(SRC / "chuo_od_up_all.csv", encoding="utf-8") as f:
            lines = [ln for ln in f if not ln.startswith("#")]
        _ODUP = {(int(r["board_code"]), int(r["alight_code"])): int(r["people"]) for r in csv.DictReader(lines)}
    return _ODUP


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def build_thumb(R):
    """サムネの数字の候補（『新宿』『2割』）の根拠"""
    M = get_model()
    notes = []
    rows = {}
    for B in B_ALL:
        if cell(R, B, 0)["n_full"] < MIN_FULL:
            continue
        d = dict(
            p_full=1 - cell(R, B, 0)["n_once"] / cell(R, B, 0)["n_trials"],
            p_before_shinjuku=pos_avg(R, B, "p_before_shinjuku"), p_at_shinjuku=pos_avg(R, B, "p_at_shinjuku"), p_after_shinjuku=pos_avg(R, B, "p_after_shinjuku"),
            p_never=pos_avg(R, B, "p_never"), p_by_shinjuku_inclusive=pos_avg(R, B, "p_before_shinjuku") + pos_avg(R, B, "p_at_shinjuku"),
            p_never_shinjuku=pos_avg(R, B, "p_never", "shinjuku"))
        pm = [sum(w * cell(R, B, j)["tokyo"]["pmf_station"][x] for j, w in zip(POS, POS_W)) / 7 for x in range(24)]
        d["pmf_station"] = pm
        d["mode_station"] = max(range(24), key=lambda x: pm[x])
        d["mode_station_name"] = M.names[d["mode_station"]]
        d["p_mode"] = pm[d["mode_station"]]
        d["p_shinjuku_given_sat"] = pm[E_SHINJUKU] / max(1e-12, sum(pm))
        rows[M.names[B]] = d
    for nm in ("立川", "三鷹", "吉祥寺", "荻窪", "中野"):
        if nm in rows:
            d = rows[nm]
            notes.append(f"{nm}で乗って席が埋まっていた回（7か所平均・a=0.6）: 座る駅でいちばん多いのは **{d['mode_station_name']}**（全体の {pc(d['p_mode'])}）。"
                         f"新宿の手前までに座る {pc(d['p_before_shinjuku'])}／新宿で座る {pc(d['p_at_shinjuku'])}／新宿より先で座る {pc(d['p_after_shinjuku'])}／東京まで座れない {pc(d['p_never'])}。"
                         f"座れた人のうち新宿で座る割合 {pc(d['p_shinjuku_given_sat'])}。")
    near = []
    for nm, d in rows.items():
        for fld, lab in (("p_at_shinjuku", "新宿で座る"), ("p_after_shinjuku", "新宿より先で座る"), ("p_never", "東京まで座れない"), ("p_before_shinjuku", "新宿の手前までに座る")):
            if 0.17 <= d[fld] <= 0.23:
                near.append(f"{nm}乗り『{lab}』{pc(d[fld])}")
    notes.append("『2割』（17〜23%）に当たる値: " + ("／".join(near) if near else "なし"))
    return dict(by_station=rows, notes=notes)


if __name__ == "__main__" and "--numbers" in sys.argv:
    R = compute()
    n, checks = run_checks(R)
    write(R, n, checks)
    print(f"  書き出し: {(OUT / 'trial' if QUICK else OUT) / 'numbers.md'}")
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・音・書き出し）。2026-10-21 追加（モデルの計算は変えていない）。
# 台本: publish/densha-long/narration_v1.md ／ 形と部品は sims/kaidan-long.py の場面部分（見開きノート・付箋・数字の欄・区切り・終了画面・照合・時間割）。
#
# 使い方
#   python -X utf8 sims/densha-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/densha-long.py --stills --fake-voice        要所の静止画6枚と sheet_480.png（out/densha-long/stills_preview/）。--at 12.3,40.5 なら指定した秒だけ
#   python -X utf8 sims/densha-long.py --wraps --fake-voice         字幕の折り返しを全部表示
#   （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
# ####################################################################################################
import re as _re
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (beat, bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh)
from engine.note import INK, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

FAKE = "--fake-voice" in sys.argv
VOICE_DIR = OUT / "voice"


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ====================================================================================================
# 1回ぶんの記録（見本）。trial() と同じ手順・同じ乱数の使い方で、人に番号をつけて、駅ごとの席と立ち位置を記録する。
#   モデルの trial() は変えていない。同じ seed で trial() と同じ結果（座った駅・席の人）になることを scene_checks で照合する
# ====================================================================================================
def trial_rec(M, rng, B, j, a, E, q=0.0):
    """返り値: (code, 座った駅, snap, rec)。rec = dict(frames=[...], you=0, sit_seat, sit_from)
    frame = dict(s, kind('board'|'watch'|'sit'), seat[7](人の番号 or -1), stand[7], nover, marks[席], org/dst は rec['info'])"""
    ns = M.ns
    sd, so = [-1] * ns, [-1] * ns
    fd, fo = [-1] * ns, [-1] * ns
    sp, fp = [-1] * ns, [-1] * ns
    ov = []                                 # (乗った駅, 降りる駅, 番号)
    S = dict(yp=-1, sat=-1, snap=None, over=False)
    nid = [0]
    info = {}
    frames = []
    rec = dict(frames=frames, info=info, you=0, sit_seat=-1, sit_from=-1, watch=[])

    def shot(s, kind, marks=()):
        frames.append(dict(s=s, kind=kind, seat=list(sp), stand=list(fp), nover=len(ov), marks=list(marks)))

    def refill():
        while ov:
            emp = [p for p in range(ns) if fd[p] < 0]
            if not emp:
                return
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            o, d, pid = ov.pop(int(rng.random() * len(ov)))
            fd[p], fo[p], fp[p] = d, o, pid

    def stand(o, d, pid):
        emp = [p for p in range(ns) if fd[p] < 0]
        if emp:
            p = emp[0] if len(emp) == 1 else emp[int(rng.random() * len(emp))]
            fd[p], fo[p], fp[p] = d, o, pid
        else:
            ov.append((o, d, pid))

    def free_seat():
        for r in M.rank_order:
            cand = [i for i in M.byrank[r] if sd[i] < 0]
            if cand:
                return cand[0] if len(cand) == 1 else cand[int(rng.random() * len(cand))]
        return -1

    def watch(s):
        flagged = [i for i in range(ns) if sd[i] == s + 1 and rng.random() < q]
        if not flagged:
            return
        p = S["yp"]
        best = min(abs(i - p) for i in flagged)
        i = rng.choice([x for x in flagged if abs(x - p) == best])
        rec["watch"].append((s, list(flagged), i, p))
        if i != p:
            fd[i], fd[p] = fd[p], fd[i]
            fo[i], fo[p] = fo[p], fo[i]
            fp[i], fp[p] = fp[p], fp[i]
            S["yp"] = i
        shot(s, "watch", marks=flagged)

    for s in range(E):
        if s >= 1:
            freed = []
            for i in range(ns):
                if sd[i] == s:
                    sd[i], so[i], sp[i] = -1, -1, -1
                    freed.append(i)
            for p in range(ns):
                if fd[p] == s and p != S["yp"]:
                    fd[p], fo[p], fp[p] = -1, -1, -1
            if ov:
                ov[:] = [x for x in ov if x[1] != s]
            refill()
            if len(freed) > 1:
                rng.shuffle(freed)
            for i in freed:
                if all(x < 0 for x in fd):
                    break
                p = pick_taker(fd, i, a, rng, ns)
                if p == S["yp"]:
                    sp[i] = 0
                    fp[p] = -1
                    rec["sit_seat"], rec["sit_from"] = i, p
                    shot(s, "sit")
                    return FULL, s, S["snap"], rec
                sd[i], so[i], sp[i] = fd[p], fo[p], fp[p]
                fd[p], fo[p], fp[p] = -1, -1, -1
                refill()
        nb = M.poisson(s, rng)
        people = [M.draw_dest(s, rng) for _ in range(nb)]
        if s == B:
            people.insert(int(rng.random() * (nb + 1)), -1)
        for d in people:
            if d == -1:
                i = free_seat()
                if i >= 0:
                    return ONCE, s, None, rec
                S["snap"] = (list(so), list(sd))
                if fd[j] >= 0:
                    ov.append((fo[j], fd[j], fp[j]))
                fd[j], fo[j], fp[j], S["yp"] = E, B, 0, j
                info[0] = (B, E)
                continue
            nid[0] += 1
            pid = nid[0]
            info[pid] = (s, d)
            i = free_seat()
            if i >= 0:
                sd[i], so[i], sp[i] = d, s, pid
            else:
                stand(s, d, pid)
        shot(s, "board")
        if B is not None and s >= B and q > 0 and s + 1 < E and S["yp"] >= 0:
            watch(s)
    return FULL, -1, S["snap"], rec


def rec_equal_check(M, specs, n_each=60):
    """trial() と trial_rec() を同じ seed で走らせて、結果（ONCE/FULL・座った駅・席の人の乗った駅と降りる駅）が1回も違わないか。違った回数を返す"""
    bad = 0
    for (B, j, a, E, q) in specs:
        for k in range(n_each):
            r1, r2 = random.Random(f"rec|{B}|{j}|{k}"), random.Random(f"rec|{B}|{j}|{k}")
            x = trial(M, r1, B, j, a, E, q)
            y = trial_rec(M, r2, B, j, a, E, q)[:3]
            if x != y or r1.random() != r2.random():
                bad += 1
    return bad


# 台本に使う見本（find_samples で探した seed。同じ seed なら必ず同じ記録）
SAMPLE_SPECS = dict(
    open=dict(key="open|72", B=12, j=1, E=23, q=0.0),        # 冒頭: 三鷹乗り・端の隣(席2)の前の「あなた」。端(席1)の前の人は、あなたが座るときまだ立っている
    ch1=dict(key="ch1|16", B=12, j=3, E=23, q=0.0),          # 1章: 三鷹乗り・真ん中(席4)の前。新宿で座る。ほかの人が5回座る・座った瞬間に空き席がない
)


def make_sample(name):
    sp = SAMPLE_SPECS[name]
    M = get_model()
    rec = trial_rec(M, random.Random(sp["key"]), sp["B"], sp["j"], A_MAIN, sp["E"], sp["q"])
    return dict(code=rec[0], sat=rec[1], rec=rec[3], spec=sp)


# ============================================================
# 台本 → 時間割（ナレーションは publish/densha-long/narration_v1.md の「- 」の行。文言は変えていない）
#   間: 数字を言う文のあとは 0.5秒（_breathe）。章の境目は +0.35秒。冒頭・各章の「（無音）」は Gap
#   区切り（アイキャッチ）は 2章の終わりと 3章の章カードの間（約4秒・声なし・足音）
# ============================================================
CH_TITLES = ["満員電車、どこに立つ？", "何駅で座れる？", "端・端の隣・真ん中", "乗る駅で変わる？", "まとめ"]
SPEED_V = 1.0
EYE_GAP = 4.0
G_SEC = dict(g0=14.0, g1=14.0, g2=9.0, g3=8.0)


def _items(g_q=0.0, g_end_extra=0.0):
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED_V)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        L("c0_0", "朝の満員電車で、座っている人の前に立つとき、あなたは、どの人の前を選びますか？", pause=0.5),
        L("c0_1", "端の人の前ですか。それとも、真ん中の人の前ですか。", pause=0.6),
        L("c0_2", "「この人なら、すぐ降りそう」と思って立ったのに、ずっと座ったまま、ということもありますよね。", pause=0.2),
        G("g0", G_SEC["g0"]),
        L("c0_3", "立つ場所や乗る駅で、座りやすさはちがう。なんとなく、そう感じていますよね。", pause=0.5),
        L("c0_4", "この動画では、例えば中央線の朝の電車を、コンピューターの中に作ります。", pause=0.5),
        L("c0_5", "そこで、座っている人の前に立ったら何駅で座れるかを、1万回ためします。", pause=0.5),
        L("c0_6", "なんとなく、こうかなと思っていることを、数字にしてみます。", pause=0.5),
        L("c0_6b", "どの駅で座れることが多いのか。どこに立てば座りやすいのか。乗る駅で、どう変わるのか。順番に見ていきます。", pause=0.8),
        L("c0b_0", "中央線を、あまり知らない人もいると思います。少しだけ、紹介します。", pause=0.5),
        L("c0b_1", "中央線の快速は、東京の西のはしの高尾から、都心の東京駅まで走る電車です。", pause=0.5),
        L("c0b_2", "朝は、都心へ向かう、東京行きの電車が混みます。", pause=0.5),
        L("c0b_3", "丸の大きさは、その駅で乗り降りする人の多さです。", pause=0.5),
        L("c0b_4", "立川や吉祥寺でも、たくさんの人が乗り降りします。", pause=0.5),
        L("c0b_5", "でも、とびぬけて大きいのは、新宿です。", pause=1.0),
        C(CH_TITLES[1], id="ch1", gap=1.4),
        L("c1_0", "この章では、座っている人の前に立ったら、何駅で座れるかを確かめます。", pause=0.4),
        L("c1_1", "電車は、さっきの中央線の快速の、朝の東京行きです。", pause=0.5),
        L("c1_2", "どの駅で何人が乗って、どの駅で降りるかは、国の調査の数字をもとにしています。", pause=0.5),
        L("c1_3", "ただし、この動画の電車は、その数字をもとに、コンピューターの中で作った電車です。", pause=0.5),
        L("c1_4", "始発の高尾で乗れば、ほとんどの回で、すぐに座れます。", pause=0.5),
        L("c1_5", "席は、八王子や立川のあたりで、うまっていきます。", pause=0.5),
        L("c1_6", "あなたは、三鷹で乗ります。席は、もう全部うまっています。", pause=0.5),
        L("c1_7", "あなたは、ドアとドアのあいだにある、7人がけの席の前に立って、東京まで乗ります。", pause=0.5),
        L("c1_8", "7人のうち、誰の前に立つかは、毎回ばらばらにします。", pause=0.5),
        L("c1_9", "空いた席には、たいてい、その真ん前に立っている人が座ります。", pause=0.5),
        L("c1_10", "ときどき、目の前の席が空いても、隣に立っている人が、あなたより先に座ります。", pause=0.1),
        G("g1", G_SEC["g1"]),
        L("c1_11", "東京に着くまでには、およそ9割が座れました。", pause=0.5),
        L("c1_12", "では、どの駅で座れたのでしょうか。", pause=0.5),
        L("c1_13", "新宿に着く前に座れたのは、3割ほどです。", pause=0.5),
        L("c1_14", "新宿で座れたのも、3割ほどでした。", pause=0.5),
        L("c1_15", "やっぱり、駅ごとに見ると、新宿がいちばん多い駅です。", pause=0.5),
        L("c1_16", "新宿では、座っている人がたくさん降りるからです。", pause=0.5),
        L("c1_17", "新宿まで、ずっと立ったまま、という朝も多いですよね。あなたは、どうですか？", pause=0.5),
        L("c1_18", "この章で分かったことを、まとめます。", pause=0.3),
        L("c1_19", "途中の駅で乗っても、東京までに、およそ9割が座れます。", pause=0.3),
        L("c1_20", "新宿で座れた分も入れると、新宿までに、6割ほどが座れます。", pause=0.8),
        C(CH_TITLES[2], id="ch2", gap=1.2),
        L("c2_0", "この章では、どの人の前に立つと座りやすいかを確かめます。", pause=0.4),
        L("c2_1", "端の席の前、端の隣の前、真ん中の前の、3か所で比べます。左右は同じなので、片側だけで比べます。", pause=0.5),
        L("c2_2", "端の前で座れるのは、目の前の席か、片側の隣の席が空いたときです。", pause=0.5),
        L("c2_3", "真ん中の前なら、目の前の席と、両側の隣の席で、チャンスがあります。", pause=0.5),
        L("c2_4", "もう一つ、気になることがあります。", pause=0.5),
        L("c2_5", "端の席には、高尾に近い駅から乗って、長く乗る人が座っていそうですよね。", pause=0.5),
        L("c2_6", "この見方が本当かも、あわせて確かめます。", pause=0.1),
        G("g2", G_SEC["g2"]),
        L("c2_7", "今度は、新宿に着く前に座れたかで比べます。", pause=0.5),
        L("c2_8", "端の前は、2割ちょっとでした。", pause=0.5),
        L("c2_9", "端の隣の前と、真ん中の前は、どちらも3割ほどでした。", pause=0.5),
        L("c2_10", "端の前は、なんとなく座りにくい気がしますよね。やっぱり、いちばん座りにくい場所でした。", pause=0.5),
        L("c2_10b", "数字にすると、端の隣の前で座れた回は、端の前の、およそ1.5倍です。", pause=0.5),
        L("c2_11", "端の隣の前は、真ん中の前より、ほんの少しだけ座りやすい場所でした。", pause=0.5),
        L("c2_12", "端の席が空いて、端の前の人が座らなかったとき、その席をねらえるのは、端の隣の前に立つ人だけだからです。", pause=0.5),
        L("c2_12x1", "ドアの前に立っている人も、位置だけなら、端の席をねらえます。", pause=0.5),
        L("c2_12x2", "でも、席を立った人はドアへ向かうので、その流れとぶつかって、座りにくいのです。", pause=0.5),
        L("c2_12x3", "この動画では、ドアの前の人は、端の席には座らない、と決めています。", pause=0.5),
        L("c2_12b", "真ん中の前だと、隣の席には、反対側からもねらう人がいます。", pause=0.5),
        L("c2_12c", "同じ三鷹乗りで、今度は、新宿で座れた分も入れて、駅ごとに見ます。", pause=0.3),
        G("g2t", 5.0),
        L("c2_12d", "新宿で座れた分も入れると、端の隣の前なら、6割を超えます。", pause=0.5),
        L("c2_12e", "端の前だと、半分ほどです。", pause=0.5),
        L("c2_12f", "東京まで乗れば、いちばん座りにくい端の前でも、8割を超えます。", pause=0.5),
        L("c2_13", "では、端の席の人は、本当に長く乗っていたのでしょうか。", pause=0.5),
        L("c2_14", "三鷹に着いたとき、端の席の人は、真ん中の席の人より、1駅ほど早くから乗っていました。", pause=0.5),
        L("c2_14b", "端の席の人は八王子のあたりから、真ん中の席の人は日野のあたりからです。", pause=0.5),
        L("c2_15", "新宿かその先まで乗る人も、端の席のほうが、少し多くいました。", pause=0.5),
        L("c2_16", "端には長く乗る人が座っている、という見方は、少しだけ当たっていました。", pause=0.5),
        L("c2_17", "これも、端の前が座りにくい理由のひとつです。", pause=0.5),
        L("c2_18", "この章で分かったことを、まとめます。", pause=0.3),
        L("c2_19", "立つなら、端の前より、端の隣の前です。", pause=0.8),
        G("eye", EYE_GAP),                           # 区切り（アイキャッチ。声なし・約4秒。章ではない。chapters.txt に入れない）
        C(CH_TITLES[3], id="ch3", gap=1.2),
        L("c3_0", "この章では、乗る駅で、座りやすさがどう変わるかを確かめます。", pause=0.4),
        L("c3_1", "立川、三鷹、吉祥寺、荻窪と、乗る駅を、東京に近づけていきます。", pause=0.1),
        G("g3", G_SEC["g3"]),
        L("c3_1b", "始発に近い駅で乗るほど座りやすいのは、思っていたとおりです。", pause=0.5),
        L("c3_2", "新宿に着く前に座れたのは、立川で乗ると、半分を超えました。", pause=0.5),
        L("c3_2b", "三鷹で乗ると、3割ほどです。", pause=0.5),
        L("c3_2c", "数字にすると、立川と三鷹では、2倍ほどちがいます。", pause=0.5),
        L("c3_3", "荻窪で乗ると、1割ほどしかありません。", pause=0.5),
        L("c3_4", "立川で乗ると、新宿までのあいだに、国分寺や吉祥寺など、降りる人の多い駅をいくつも通るからです。", pause=0.5),
        L("c3_5", "この章で分かったことを、まとめます。", pause=0.3),
        L("c3_6", "乗る駅が数駅ちがうだけで、新宿に着く前に座れる割合は、2倍ほどちがいます。", pause=0.5),
        L("c3_7", "あなたの路線でも、始発に近い駅で乗るほど、座りやすいはずです。", pause=0.8),
        C(CH_TITLES[4], id="ch4", gap=1.2),
        L("c4_0", "最後に、数字にして分かったことを、まとめます。", pause=0.4),
        L("c4_1", "途中の駅で乗っても、東京までに、およそ9割が座れます。", pause=0.4),
        L("c4_2", "新宿で座れた分も入れると、新宿までに、6割ほどが座れます。", pause=0.4),
        L("c4_3", "立つなら、端の前より、端の隣の前です。", pause=0.4),
        L("c4_4", "乗る駅が数駅ちがうだけで、新宿に着く前に座れる割合は、2倍ほどちがいます。", pause=0.5),
        L("c4_4a", "どれも、なんとなく分かっていたことかもしれません。", pause=0.5),
        L("c4_4b", "でも、数字にすると、ちがいの大きさが見えてきます。", pause=0.5),
        L("c4_5", "もちろん、この動画の電車は、国の調査の数字をもとに、コンピューターの中で作った電車です。", pause=0.3),
        L("c4_6", "空いた席に誰が座るかなどは、この動画で決めたルールです。", pause=0.4),
    ] + ([G("g_q", g_q)] if g_q > 0 else []) + [
        L("c4_7", "あなたは明日から、どこに立ちますか？", pause=1.0),
        L("c4_8", "このチャンネルでは、身近な疑問を、シミュレーションで確かめる動画をあげています。"),
        L("c4_9", "チャンネル登録してもらえると、うれしいです。", pause=0),
        G("g_end", 2.0 + g_end_extra),
    ]


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


# 字幕の折り返しを指定する文（自動だと語の途中で折れるもの。--wraps で見て足す）
_SUB_BREAK = {
    "中央線を、あまり知らない人もいると思います。少しだけ、紹介します。": ["中央線を、あまり知らない人もいると思います。", "少しだけ、紹介します。"],
    "東京まで乗れば、いちばん座りにくい端の前でも、8割を超えます。": ["東京まで乗れば、", "いちばん座りにくい端の前でも、8割を超えます。"],
    "始発に近い駅で乗るほど座りやすいのは、思っていたとおりです。": ["始発に近い駅で乗るほど座りやすいのは、", "思っていたとおりです。"],
    "ドアの前に立っている人も、位置だけなら、端の席をねらえます。": ["ドアの前に立っている人も、", "位置だけなら、端の席をねらえます。"],
    "でも、席を立った人はドアへ向かうので、その流れとぶつかって、座りにくいのです。": ["でも、席を立った人はドアへ向かうので、", "その流れとぶつかって、座りにくいのです。"],
    "この動画では、ドアの前の人は、端の席には座らない、と決めています。": ["この動画では、ドアの前の人は、", "端の席には座らない、と決めています。"],
    "どの駅で座れることが多いのか。どこに立てば座りやすいのか。乗る駅で、どう変わるのか。順番に見ていきます。": ["どの駅で座れることが多いのか。どこに立てば座りやすいのか。", "乗る駅で、どう変わるのか。順番に見ていきます。"],
    "端の前は、なんとなく座りにくい気がしますよね。やっぱり、いちばん座りにくい場所でした。": ["端の前は、なんとなく座りにくい気がしますよね。", "やっぱり、いちばん座りにくい場所でした。"],
    "同じ三鷹乗りで、今度は、新宿で座れた分も入れて、駅ごとに見ます。": ["同じ三鷹乗りで、今度は、", "新宿で座れた分も入れて、駅ごとに見ます。"],
    "三鷹に着いたとき、端の席の人は、真ん中の席の人より、1駅ほど早くから乗っていました。": ["三鷹に着いたとき、端の席の人は、", "真ん中の席の人より、1駅ほど早くから乗っていました。"],
    "立川で乗ると、新宿までのあいだに、国分寺や吉祥寺など、降りる人の多い駅をいくつも通るからです。": ["立川で乗ると、新宿までのあいだに、", "国分寺や吉祥寺など、降りる人の多い駅をいくつも通るからです。"],
    "乗る駅が数駅ちがうだけで、新宿に着く前に座れる割合は、2倍ほどちがいます。": ["乗る駅が数駅ちがうだけで、", "新宿に着く前に座れる割合は、2倍ほどちがいます。"],
    "端の席が空いて、端の前の人が座らなかったとき、その席をねらえるのは、端の隣の前に立つ人だけだからです。": ["端の席が空いて、端の前の人が座らなかったとき、", "その席をねらえるのは、端の隣の前に立つ人だけだからです。"],
    "新宿で座れた分も入れると、新宿までに、6割ほどが座れます。": ["新宿で座れた分も入れると、", "新宿までに、6割ほどが座れます。"],
    "途中の駅で乗ると、座れる駅でいちばん多いのは、降りる人がいちばん多い、大きな乗り換え駅です。": ["途中の駅で乗ると、座れる駅でいちばん多いのは、", "降りる人がいちばん多い、大きな乗り換え駅です。"],
    "途中の駅で乗るなら、座れる駅でいちばん多いのは、降りる人がいちばん多い、大きな乗り換え駅です。": ["途中の駅で乗るなら、座れる駅でいちばん多いのは、", "降りる人がいちばん多い、大きな乗り換え駅です。"],
    "三鷹に着いたとき、端の席の人は、真ん中の席の人より、高尾に近い駅から乗っていました。": ["三鷹に着いたとき、端の席の人は、", "真ん中の席の人より、高尾に近い駅から乗っていました。"],
    "新宿まで、ずっと立ったまま、という朝も多いですよね。あなたは、どうですか？": ["新宿まで、ずっと立ったまま、という朝も多いですよね。", "あなたは、どうですか？"],
    "もちろん、この動画の電車は、国の調査の数字をもとに、コンピューターの中で作った電車です。": ["もちろん、この動画の電車は、", "国の調査の数字をもとに、コンピューターの中で作った電車です。"],
}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)

VOICE_PAUSES = (0.10, 0.22)
NUM_BREATH = 0.5                                     # 数字を言った文のあとは 0.5秒
CH_BREATH = 0.35


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and any(ch.isdigit() for ch in split_reading(it.text)[0]):
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# ============================================================
# 小さな道具（kaidan-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3f78d0"
BLUE_L = "#6a93cf"
GREEN = "#3f9a6a"
ORANGE = "#e0892a"


def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


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
    """白い下地つきの札"""
    if a <= 0.003 or progress <= 0:
        return
    w = text_width(s, size) + 26
    cx = x + w / 2 - 13 if align == "left" else x
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, cx - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, cx, y, size, col, progress, align="center", alpha=a)


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """余白の小さい付箋。(x, y) は中心（align='left' なら左端）"""
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


def hand_title(ctx, s, x, y, size, seed, alpha=1.0, color=INK):
    """1字ずつ少し傾けた手書きの見出し。重なりの検査には1行として記録する"""
    saved = core._LOG
    core._LOG = None
    w = note.hand_text(ctx, s, x, y, size, color, seed=seed, alpha=alpha)
    core._LOG = saved
    if saved is not None and alpha > 0.1:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((x, y - size / 2), (x + w, y + size / 2))))
        saved.append((core._CUR_T, s, min(xs), min(ys), max(xs), max(ys), abs(ctx.user_to_device_distance(0, size)[1])))
    return w


def nolog(fn, *args, **kw):
    """飾りの字（重なりの検査に入れない）"""
    saved = core._LOG
    core._LOG = None
    try:
        return fn(*args, **kw)
    finally:
        core._LOG = saved


# ============================================================
# 準備（データ・時間割）
# ============================================================
lf.use()
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items(0.5, 0.0)), VOICE_DIR, lead=2.0, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ============================================================
# 絵: ドアとドアのあいだの7人がけの席（向かいから見た図）・人・路線の図
#   左ページ（x 45〜940）の下に 席7人＋その前に立つ7人。人は人型で大きく: 座る人 約 215px・立つ人 約 262px（頭の直径 約 50px）。
#   立つ人は席の前の床に、座る人は席に。立つ人の頭は座る人の足元より下に置き、人どうしを重ねない。
# ============================================================
NSEATS = 7
SEAT_PITCH = 118.0
SEAT_CX = [138.0 + SEAT_PITCH * i for i in range(NSEATS)]
BAY_X0, BAY_X1 = 46.0, 940.0
Y_CEIL0, Y_CEIL1 = 262.0, 296.0
Y_WIN0, Y_WIN1 = 346.0, 440.0
Y_SEAT_FLOOR = 580.0                  # 座る人の足元（席の下の床）
Y_FEET = 888.0                        # 立つ人の足元
Y_RING = 584.0                        # 吊り革の輪の中心
STAND_H = 262.0
SIT_H = 215.0
SIT_COLS = ["#8ab6d6", "#e7a8b8", "#9ccaa7", "#e2c978", "#b9a6d8", "#c5c8cf", "#86c5c0"]
STAND_COLS = ["#7f8aa3", "#8f9a86", "#a58f8f", "#8798ae", "#9b8fb0", "#8aa09a", "#a89a7a"]
HAIRS = ["#3a2f2a", "#5a4a3a", "#2c2c34", "#6a5a4a", "#4a3a3a"]
SKIN = "#fff3df"
DRAWN = [0]                           # 描いた人の数（検査用）
PEOPLE_LOG = []                       # (種類, x0, y0, x1, y1, 濃さ, 拡大率)。座標は画面の位置
BAY_XF = [1.0, 940.0, 935.0]          # 車内の絵を縮めて描くとき (拡大率, 基準x, 基準y)


def _plog(kind, x0, y0, x1, y1, a):
    k, ax, ay = BAY_XF
    PEOPLE_LOG.append((kind, ax - (ax - x0) * k, ay - (ay - y0) * k, ax - (ax - x1) * k, ay - (ay - y1) * k, a, k))


def _dark(col, k=0.8):
    c = hexrgb(col)
    return (c[0] * k, c[1] * k, c[2] * k, 1.0)


def _rr(ctx, x, y, w, h, r, col, a=1.0, ink=True, lw=3.0):
    """色つきの角丸（INK の縁つき）"""
    rrect(ctx, x, y, w, h, r)
    c = hexrgb(col, a) if isinstance(col, str) else (col[0], col[1], col[2], a)
    ctx.set_source_rgba(*c)
    if ink:
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def _disc(ctx, x, y, r, col, a=1.0, ink=True, lw=3.0):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    c = hexrgb(col, a) if isinstance(col, str) else (col[0], col[1], col[2], a)
    ctx.set_source_rgba(*c)
    if ink:
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def draw_sitter(ctx, cx, col, hair, a=1.0, pop=0.0, face=True):
    """席に座る人（向かいから見た正面）。頭の中心は y=392・足元は y=580。cx は席の中心"""
    if a <= 0.01:
        return
    DRAWN[0] += 1
    _plog("sit", cx - 44, 365, cx + 44, Y_SEAT_FLOOR, a)
    ctx.save()
    ctx.translate(cx, Y_SEAT_FLOOR)
    s = 1.0 + 0.10 * math.sin(math.pi * clamp01(pop))
    ctx.scale(s, s)
    ctx.translate(-cx, -Y_SEAT_FLOOR)
    ctx.push_group()
    dark = _dark(col)
    # 脚（ひざから下）と靴
    for dx in (-17, 17):
        _rr(ctx, cx + dx - 13, 524, 26, 44, 9, dark, 1.0)
        _rr(ctx, cx + dx - 17, 564, 34, 16, 8, "#3b3f4a", 1.0, lw=2.5)
    # 腰からひざ（正面から見ると短く見える）
    _rr(ctx, cx - 38, 498, 76, 34, 13, dark, 1.0)
    # 胴
    _rr(ctx, cx - 42, 420, 84, 88, 22, col, 1.0)
    # 腕
    for dx in (-52, 36):
        _rr(ctx, cx + dx, 432, 18, 66, 9, col, 1.0, lw=2.5)
    # 首と頭
    _rr(ctx, cx - 9, 410, 18, 18, 5, SKIN, 1.0, lw=2.5)
    _disc(ctx, cx, 392, 27, SKIN)
    ctx.set_source_rgba(*hexrgb(hair))                          # 髪
    ctx.arc(cx, 390, 28.5, math.pi * 0.98, math.pi * 2.02)
    ctx.close_path()
    ctx.fill()
    if face:
        ctx.set_source_rgba(*hexrgb(INK))
        for dx in (-9, 9):
            ctx.arc(cx + dx, 396, 2.8, 0, 2 * math.pi)
            ctx.fill()
        ctx.set_line_width(2.4)
        ctx.arc(cx, 402, 7, 0.25 * math.pi, 0.75 * math.pi)
        ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_stander(ctx, cx, col, hair, a=1.0, arm=True, you=False, pop=0.0):
    """立つ人（席のほうを向いているので、後ろから見た形）。頭の中心は y=650・足元は y=888・吊り革をつかむ手は y=596"""
    if a <= 0.01:
        return
    DRAWN[0] += 1
    _plog("stand", cx - 50, 590, cx + 56, Y_FEET, a)
    ctx.save()
    if you:                                                       # 「あなた」: 足元のうすい赤い輪
        ctx.save()
        ctx.translate(cx, Y_FEET - 2)
        ctx.scale(1, 0.16)
        ctx.arc(0, 0, 66, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(RED, 0.32 * a))
        ctx.fill()
    dark = _dark(col, 0.72)
    ctx.push_group()
    # 脚
    for dx in (-19, 19):
        _rr(ctx, cx + dx - 15, 780, 30, 100, 10, dark, 1.0)
        _rr(ctx, cx + dx - 19, 872, 38, 17, 8, "#3b3f4a", 1.0, lw=2.5)
    # 下ろしている腕（左）
    _rr(ctx, cx - 60, 690, 18, 86, 9, col, 1.0, lw=2.5)
    # 胴
    _rr(ctx, cx - 49, 676, 98, 112, 26, col, 1.0)
    # 上げている腕（右）と手。吊り革をつかむ
    if arm:
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(24)
        ctx.move_to(cx + 44, 700)
        ctx.line_to(cx + 56, 604)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.set_line_width(18)
        ctx.move_to(cx + 44, 700)
        ctx.line_to(cx + 56, 604)
        ctx.stroke()
        _disc(ctx, cx + 56, 596, 11, SKIN, lw=2.5)
    else:
        _rr(ctx, cx + 44, 690, 20, 86, 10, col, 1.0, lw=2.5)
    # 首と頭（後頭部）
    _rr(ctx, cx - 10, 664, 20, 20, 5, SKIN, 1.0, lw=2.5)
    _disc(ctx, cx, 650, 26, hair)
    ctx.set_source_rgba(*hexrgb(SKIN))                           # 耳
    for dx in (-26, 26):
        ctx.arc(cx + dx, 654, 5, 0, 2 * math.pi)
        ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_bay_bg(ctx, a=1.0):
    """向かいから見た車内: 天井・網棚・窓・ドアの端・席・床・吊り革の棒。人は含まない"""
    x0, x1 = BAY_X0, BAY_X1
    ctx.save()
    if a < 0.997:
        ctx.push_group()
    # 壁
    _rr(ctx, x0, Y_CEIL0, x1 - x0, Y_SEAT_FLOOR - Y_CEIL0, 4, "#e9eef2", 1.0, lw=3.5)
    # 天井の帯
    ctx.set_source_rgba(*hexrgb("#c3ccd6"))
    ctx.rectangle(x0 + 2, Y_CEIL0 + 2, x1 - x0 - 4, Y_CEIL1 - Y_CEIL0 - 2)
    ctx.fill()
    # 吊り革のレール
    ctx.set_source_rgba(*hexrgb("#8b94a3"))
    ctx.set_line_width(7)
    ctx.move_to(x0 + 36, Y_CEIL1 - 6)
    ctx.line_to(x1 - 36, Y_CEIL1 - 6)
    ctx.stroke()
    # 網棚（2本のパイプ＋あみ）
    yr0, yr1 = 304.0, 336.0
    ctx.set_source_rgba(*hexrgb("#98a2b0", 0.9))
    ctx.set_line_width(3)
    for k in range(int((x1 - x0 - 90) / 22) + 1):
        xx = x0 + 45 + k * 22
        ctx.move_to(xx, yr0)
        ctx.line_to(xx, yr1)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#6f7b8c"))
    ctx.set_line_width(7)
    for yy in (yr0, yr1):
        ctx.move_to(x0 + 40, yy)
        ctx.line_to(x1 - 40, yy)
        ctx.stroke()
    # 窓（3枚。間に柱）
    wins = [(x0 + 52, 262.0), (x0 + 52 + 296, 262.0), (x0 + 52 + 592, 262.0)]
    for wx, _ in wins:
        _rr(ctx, wx, Y_WIN0, 250, Y_WIN1 - Y_WIN0, 8, "#cfe6f5", 1.0, lw=3.5)
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.move_to(wx + 24, Y_WIN1 - 8)
        ctx.line_to(wx + 70, Y_WIN0 + 8)
        ctx.line_to(wx + 96, Y_WIN0 + 8)
        ctx.line_to(wx + 50, Y_WIN1 - 8)
        ctx.close_path()
        ctx.fill()
    # ドアの端（左右）
    for dx0, dx1 in ((x0, x0 + 34), (x1 - 34, x1)):
        _rr(ctx, dx0, Y_CEIL1, dx1 - dx0, Y_SEAT_FLOOR - Y_CEIL1, 3, "#b4bec9", 1.0, lw=3.5)
        _rr(ctx, dx0 + 6, 346, dx1 - dx0 - 12, 150, 5, "#d9eaf6", 1.0, lw=2.5)
    # 席の背もたれ・座面・席の下
    _rr(ctx, 79, 408, 826, 100, 14, "#8aa4c6", 1.0, lw=3.5)
    _rr(ctx, 79, 504, 826, 36, 10, "#6a86ad", 1.0, lw=3.5)
    _rr(ctx, 79, 538, 826, 42, 4, "#566f93", 1.0, lw=3.5)
    ctx.set_source_rgba(*hexrgb(INK, 0.22))
    ctx.set_line_width(2)
    for k in range(1, NSEATS):
        xx = 79 + SEAT_PITCH * k
        ctx.move_to(xx, 414)
        ctx.line_to(xx, 534)
        ctx.stroke()
    # 床（立つ人の足元）
    ctx.set_source_rgba(*hexrgb("#d9d3c4"))
    ctx.rectangle(x0 + 1.5, Y_SEAT_FLOOR + 1.5, x1 - x0 - 3, 935 - Y_SEAT_FLOOR - 1.5)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#bdb6a4", 0.8))
    ctx.set_line_width(2)
    for yy in (650, 770, 892):
        ctx.move_to(x0 + 2, yy)
        ctx.line_to(x1 - 2, yy)
        ctx.stroke()
    # 床と席の境の線
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(3.5)
    ctx.move_to(x0, Y_SEAT_FLOOR)
    ctx.line_to(x1, Y_SEAT_FLOOR)
    ctx.stroke()
    # 吊り革（レールから輪まで。席と席のあいだに下ろす）
    for i in range(NSEATS):
        xx = SEAT_CX[i] + 59
        ctx.set_source_rgba(*hexrgb("#6f7b8c"))
        ctx.set_line_width(4)
        ctx.move_to(xx, Y_CEIL1 - 4)
        ctx.line_to(xx, Y_RING - 14)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK, 0.75))
        ctx.set_line_width(5)
        ctx.arc(xx, Y_RING, 13, 0, 2 * math.pi)
        ctx.stroke()
    if a < 0.997:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# 人の見た目（番号 pid から決める。同じ人は同じ色・同じ髪）
def _look(pid):
    return SIT_COLS[(pid * 5 + 2) % len(SIT_COLS)], STAND_COLS[(pid * 3 + 1) % len(STAND_COLS)], HAIRS[(pid * 7 + 3) % len(HAIRS)]


def draw_people_list(ctx, plist):
    """plist の要素: dict(kind='sit'|'stand', idx, pid, a, pop, col(上書き), you)。座る人を先に、立つ人を後に描く"""
    for p in sorted(plist, key=lambda p: (p["kind"] == "stand", p["idx"])):
        sc, tc, hc = _look(p["pid"])
        if p["kind"] == "sit":
            draw_sitter(ctx, SEAT_CX[p["idx"]], p.get("col") or sc, hc, a=p["a"], pop=p.get("pop", 0.0))
        else:
            draw_stander(ctx, SEAT_CX[p["idx"]], p.get("col") or tc, hc, a=p["a"], you=p.get("you", False), pop=p.get("pop", 0.0))


# ---------- 記録（見本）から、ある時刻の人の並びを作る ----------
def occupancy(frame):
    d = {}
    for i, p in enumerate(frame["seat"]):
        if p >= 0:
            d[p] = ("sit", i)
    for i, p in enumerate(frame["stand"]):
        if p >= 0:
            d[p] = ("stand", i)
    return d


def _sm(x):
    return ease(clamp01(x))


def rec_people(rec, x, colors=None, you_red=True):
    """記録の frames[x]（x は小数。a=floor, b=a+1 のあいだを補間）の人の並び。
    降りる人は薄れて消え、立っていた人が席に座るときは「立つ人が薄れ・座る人が現れる」、乗ってくる人は薄れて現れる。
    1駅ぶんの中の順番: 降りる(0〜0.4) → 座る・立ち位置が変わる(0.25〜0.65) → 乗ってくる(0.6〜1.0)"""
    frames = rec["frames"]
    colors = colors or {}
    n = len(frames)
    x = max(0.0, min(n - 1.0, x))
    a_ = min(int(math.floor(x)), n - 1)
    b_ = min(a_ + 1, n - 1)
    u = x - a_ if b_ > a_ else 0.0
    oa, ob = rec["occ"][a_], rec["occ"][b_]
    w_out, w_sit, w_in = _sm(u / 0.4), _sm((u - 0.25) / 0.4), _sm((u - 0.6) / 0.4)
    out = []

    def add(kind, idx, pid, al, pop=0.0):
        if al <= 0.01:
            return
        d = dict(kind=kind, idx=idx, pid=pid, a=al, pop=pop)
        if pid == rec["you"] and you_red:
            d["col"], d["you"] = RED, True
        if pid in colors:
            d["col"] = colors[pid]
        out.append(d)

    for pid in set(oa) | set(ob):
        pa, pb = oa.get(pid), ob.get(pid)
        if pa and pb:
            if pa == pb:
                add(pa[0], pa[1], pid, 1.0)
            elif pa[0] == "stand" and pb[0] == "sit":
                add("stand", pa[1], pid, 1 - w_sit)
                add("sit", pb[1], pid, w_sit, pop=w_sit)
            else:                                                       # 立ち位置が入れ替わる（クロスフェード）
                add(pa[0], pa[1], pid, 1 - w_sit)
                add(pb[0], pb[1], pid, w_sit)
        elif pa:
            add(pa[0], pa[1], pid, 1 - w_out)
        else:
            add(pb[0], pb[1], pid, w_in)
    return out


def prep_rec(sample):
    rec = sample["rec"]
    rec["occ"] = [occupancy(f) for f in rec["frames"]]
    return sample


def station_at(x):
    """記録の位置 x（小数）の、電車の位置（駅の番号を小数で）。1駅ぶんの最初の 0.4 で進み、あとは駅にとまっている"""
    k = int(math.floor(x))
    u = x - k
    return k + _sm(u / 0.4)


# ---------- 路線の図（高尾 → 東京・24駅を1本の線で） ----------
ST_NAMES = ["高尾", "西八王子", "八王子", "豊田", "日野", "立川", "国立", "西国分寺", "国分寺", "武蔵小金井", "東小金井", "武蔵境",
            "三鷹", "吉祥寺", "西荻窪", "荻窪", "阿佐ケ谷", "高円寺", "中野", "新宿", "四ツ谷", "御茶ノ水", "神田", "東京"]
RT_X0, RT_DX, RT_Y = 86.0, 35.4, 160.0
LABELS_MAIN = {0: ("高尾", "b"), 2: ("八王子", "a"), 5: ("立川", "b"), 8: ("国分寺", "a"), 12: ("三鷹", "b"), 15: ("荻窪", "a"),
               18: ("中野", "b"), 19: ("新宿", "a"), 20: ("四ツ谷", "c"), 23: ("東京", "a")}
TIER_Y = {"a": 96.0, "b": 196.0, "c": 240.0}


def rx(i):
    return RT_X0 + RT_DX * i


def draw_route(ctx, a=1.0, labels=None, reveal=1.0, hi=(), mark=None, train=None, red=(), y=RT_Y):
    """高尾が左・東京が右の1本の線。reveal 0→1 で左から駅が現れる。hi=強調する駅の番号。mark=赤い丸で囲む駅。train=電車の位置（駅の番号・小数）"""
    if a <= 0.003:
        return
    labels = LABELS_MAIN if labels is None else labels
    ctx.save()
    if a < 0.997:
        ctx.push_group()
    n_show = reveal * (len(ST_NAMES) - 1)
    # 線
    xe = rx(min(n_show, 23))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(9)
    ctx.move_to(rx(0), y)
    ctx.line_to(xe, y)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#8aa4c6"))
    ctx.set_line_width(5)
    ctx.move_to(rx(0), y)
    ctx.line_to(xe, y)
    ctx.stroke()
    for i in range(len(ST_NAMES)):
        if i > n_show + 1e-6:
            break
        xx = rx(i)
        named = i in labels
        col = RED if i in red else INK
        _disc(ctx, xx, y, 9.5 if named else 6.5, "#ffffff" if i not in hi else RED, lw=3.0 if named else 2.4)
        if named:
            nm, tier = labels[i]
            ty = TIER_Y[tier]
            ctx.set_source_rgba(*hexrgb(INK, 0.6))
            ctx.set_line_width(2.5)
            if tier == "a":
                ctx.move_to(xx, y - 11)
                ctx.line_to(xx, ty + 22)
            else:
                ctx.move_to(xx, y + 11)
                ctx.line_to(xx, ty - 22)
            ctx.stroke()
            text(ctx, nm, xx, ty, 36, col)
    if mark is not None:
        pen_circle(ctx, rx(mark), y - 2, 19, 19, RED, seed=31, width=5)
    if train is not None:
        tx = rx(max(0.0, min(23.0, train)))
        ctx.save()
        ctx.translate(tx, y - 3)
        _rr(ctx, -21, -15, 42, 26, 8, "#ffffff", 1.0, lw=3.0)
        ctx.set_source_rgba(*hexrgb("#8aa4c6"))
        for dx in (-13, 1):
            ctx.rectangle(dx, -10, 11, 9)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.arc(-11, 14, 4.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.arc(11, 14, 4.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
    if a < 0.997:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ============================================================
# 画面と声に出す数字（すべて data.json から。四捨五入。細かい数字は付箋と欄だけ）
# ============================================================
BS = RES["by_boarding_station"]
B_MITAKA, B_TACHIKAWA, B_KICHIJOJI, B_OGIKUBO = 12, 5, 13, 15
A7 = {nm: BS[nm]["avg7"] for nm in ("立川", "三鷹", "吉祥寺", "荻窪")}
PMF_MITAKA = BS["三鷹"]["pmf_station_avg7"]
CELLS = RES["cells"]
_ck = lambda j, q=0.0, E=23: f"main|od|f0.1296|B12|j{j + 1}|a0.6|q{q}|E{E}"
C_END, C_NEXT, C_MID = (CELLS[_ck(j)] for j in (0, 1, 3))                # 端の前・端の隣の前・真ん中の前
C_Q0, C_Q2 = CELLS[_ck(3, 0.0, 19)] if _ck(3, 0.0, 19) in CELLS else None, CELLS[_ck(3, 0.2, 19)]
SEAT_STATS = RES["seat_stats"]["od|B12"]["classes"]
PC = lambda v: ihalf(v * 100)
SH = dict(
    P_SAT=PC(A7["三鷹"]["p_sat"]), P_SAT9=ihalf(A7["三鷹"]["p_sat"] * 10),                         # 座れた 90%・「9割」
    P_BEF=PC(A7["三鷹"]["p_before_shinjuku"]), P_BEF3=ihalf(A7["三鷹"]["p_before_shinjuku"] * 10),   # 新宿に着く前 29%・「3割」
    P_AT=PC(A7["三鷹"]["p_at_shinjuku"]), P_AT3=ihalf(A7["三鷹"]["p_at_shinjuku"] * 10),             # 新宿で 29%・「3割」
    E_END=PC(C_END["shinjuku"]["p_sat"]), E_END2=ihalf(C_END["shinjuku"]["p_sat"] * 10),            # 端の前 23%・「2割」
    E_NEXT=PC(C_NEXT["shinjuku"]["p_sat"]), E_NEXT3=ihalf(C_NEXT["shinjuku"]["p_sat"] * 10),         # 端の隣の前 34%・「3割」
    E_MID=PC(C_MID["shinjuku"]["p_sat"]), E_MID3=ihalf(C_MID["shinjuku"]["p_sat"] * 10),             # 真ん中の前 31%・「3割」
    O_END=PC(SEAT_STATS["端(席1・7)"]["p_dest_ge_shinjuku"]), O_MID=PC(SEAT_STATS["真ん中(席4)"]["p_dest_ge_shinjuku"]),   # 新宿かその先まで 72%・68%
    T_TACH=PC(A7["立川"]["p_before_shinjuku"]), T_MITA=PC(A7["三鷹"]["p_before_shinjuku"]), T_KICH=PC(A7["吉祥寺"]["p_before_shinjuku"]),
    T_OGI=PC(A7["荻窪"]["p_before_shinjuku"]), T_OGI1=ihalf(A7["荻窪"]["p_before_shinjuku"] * 10),    # 荻窪 12%・「1割」
    RATIO=ihalf(C_NEXT["shinjuku"]["p_sat"] / C_END["shinjuku"]["p_sat"] * 10) / 10,     # 端の隣の前 ÷ 端の前 ＝ 0.342 ÷ 0.228 ＝ 1.5倍
)
SH["SIX"] = ihalf((A7["三鷹"]["p_before_shinjuku"] + A7["三鷹"]["p_at_shinjuku"]) * 10)            # 新宿までに（新宿で座るのも含む）0.583 → 「6割」
SH["R3"] = ihalf(A7["立川"]["p_before_shinjuku"] / A7["三鷹"]["p_before_shinjuku"])                 # 立川 ÷ 三鷹 ＝ 0.546 ÷ 0.295 ＝ 1.85 → 「2倍」
SH["EARLY"] = ihalf(RES["seat_stats"]["od|B12"]["classes"]["真ん中(席4)"]["mean_origin"] - RES["seat_stats"]["od|B12"]["classes"]["端(席1・7)"]["mean_origin"])   # 乗った駅の平均の差 1.2 → 「1駅」
TBL_COLS = [("吉祥寺", 13), ("中野", 18), ("新宿", 19), ("東京", 23)]            # 列: 乗った三鷹のあと、その駅までに座れた割合（その駅で座るのも含む）
TBL_ROWS = [("端の前", 0), ("端の隣の前", 1), ("真ん中の前", 3)]                  # 行: 席1・席2・席4の前
TBL_V = [[float(sum(CELLS[_ck(j)]["tokyo"]["pmf_station"][:st + 1])) for _n, st in TBL_COLS] for _n, j in TBL_ROWS]
TBL_P = [[PC(v) for v in row] for row in TBL_V]
TBL_FLAT = {v for row in TBL_P for v in row}
SHINJUKU_TOP_STATION = max(range(24), key=lambda x: PMF_MITAKA[x])      # 座れた駅の最頻 ＝ 新宿（19）

# 声に出す数字（文ごと）。scene_checks で、台本の文の数字がこれと1つ残らず一致するかを見る
SPOKEN = {
    "c0_5": ["1万回"],
    "c1_7": ["7人"], "c1_8": ["7人"],
    "c1_11": [f"{SH['P_SAT9']}割"], "c1_13": [f"{SH['P_BEF3']}割"], "c1_14": [f"{SH['P_AT3']}割"],
    "c2_1": ["3"], "c2_12d": ["6割"], "c2_12f": ["8割"], "c2_10b": [f"{SH['RATIO']}倍"], "c2_8": [f"{SH['E_END2']}割"], "c2_9": [f"{SH['E_NEXT3']}割"],
    "c1_19": [f"{SH['P_SAT9']}割"], "c1_20": [f"{SH['SIX']}割"], "c2_14": [f"{SH['EARLY']}駅"],
    "c3_2b": [f"{SH['P_BEF3']}割"], "c3_2c": [f"{SH['R3']}倍"], "c3_3": [f"{SH['T_OGI1']}割"], "c3_6": [f"{SH['R3']}倍"],
    "c4_1": [f"{SH['P_SAT9']}割"], "c4_2": [f"{SH['SIX']}割"], "c4_4": [f"{SH['R3']}倍"],
}
PCT_OK = {SH[k] for k in ("P_SAT", "P_BEF", "P_AT", "E_END", "E_NEXT", "E_MID", "O_END", "O_MID", "T_TACH", "T_MITA", "T_KICH", "T_OGI")} | {0, 50, 100} | TBL_FLAT
MANY_OK = set()                                            # 1文に声の数字が2つ以上の文は、いまの台本にはない
NUM_RE = r"\d+回に\d+回|\d[\d,]*万回|\d+\.\d+倍|\d+[台列点秒分割倍つ個%階人駅]|\d+"


# ============================================================
# 見本の記録と、1万回のマス目
# ============================================================
SM = {nm: prep_rec(make_sample(nm)) for nm in SAMPLE_SPECS}


def _cells_sits():
    """章1・2のマス目に使う、三鷹乗り・席1〜4の前・1万回ずつ（models の run_cell と同じ seed・data.json と同じ乱数）"""
    cache = OUT / "scene_work" / "cells_cache.npz"
    if cache.exists():
        d = np.load(cache)
        return {j: d[f"j{j}"] for j in range(4)}
    out = {}
    for j in range(4):
        _spec, r = run_cell((MAIN_DM, F_BASE, 12, j, A_MAIN, 0.0, E_TOKYO, "main"))
        out[j] = r["sits"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, **{f"j{j}": v for j, v in out.items()})
    return out


CELL_SITS = _cells_sits()
_n1 = [2857, 2857, 2857, 1429]                                # 7か所の平均（席1・2・3の前が2か所ずつ・席4の前が1か所）の重み
SITS_AVG = np.concatenate([CELL_SITS[j][:n] for j, n in enumerate(_n1)])          # 10000回（三鷹・東京まで）
SAT_AVG = SITS_AVG >= 0
RNG_G = np.random.default_rng(SEED + 4)

from engine.parts import bgra  # noqa: E402

# ---- 1章のマス目: 100×100（10×10ごとにすきま）。右ページ ----
CELL1, BGAP1 = 5, 1
GW1 = 100 * CELL1 + 9 * BGAP1
_ix = np.arange(N)
_gx = (_ix % 100) * CELL1 + (_ix % 100) // 10 * BGAP1
_gy = (_ix // 100) * CELL1 + (_ix // 100) // 10 * BGAP1
_perm1 = np.random.default_rng(SEED + 5).permutation(N)
POS1_X, POS1_Y = _gx[_perm1], _gy[_perm1]
ORDER1 = np.random.default_rng(SEED + 6).permutation(N)
G1X, G1Y = 1161, 192
C_SAT, C_NO, C_EMPTY = (np.array(bgra(c), np.uint8) for c in (BLUE, "#b9b4a5", "#e6dfcf"))


def _grid1(shown):
    img = np.zeros((GW1, GW1, 4), np.uint8)
    cols = np.where(SAT_AVG[:, None], C_SAT, C_NO)
    cols = np.where(shown[:, None], cols, C_EMPTY)
    for k in range(CELL1 - 1):
        for j in range(CELL1 - 1):
            img[POS1_Y + k, POS1_X + j] = cols
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW1, GW1, GW1 * 4), img


_G1C = {}


def draw_grid1(ctx, a, n):
    if a <= 0.003:
        return
    n = int(max(0, min(N, n)))
    if n >= N:
        if "full" not in _G1C:
            _G1C["full"] = _grid1(np.ones(N, bool))
        surf = _G1C["full"][0]
    else:
        shown = np.zeros(N, bool)
        shown[ORDER1[:n]] = True
        surf, _ = _grid1(shown)
    ctx.set_source_surface(surf, G1X, G1Y)
    ctx.paint_with_alpha(a)


# ---- 2章のマス目: 3つ（端の前・端の隣の前・真ん中の前）。200列×50行・1マス2px（新宿に着くまでに座れた回） ----
CELL2, BGAP2, G2COLS, G2ROWS = 2, 1, 200, 50
GW2, GH2 = G2COLS * CELL2 + 19 * BGAP2, G2ROWS * CELL2 + 4 * BGAP2
_ix2 = np.arange(N)
_g2x = (_ix2 % G2COLS) * CELL2 + (_ix2 % G2COLS) // 10 * BGAP2
_g2y = (_ix2 // G2COLS) * CELL2 + (_ix2 // G2COLS) // 10 * BGAP2
G2X, G2YS = 1060, (214, 400, 586)                                # 3つのマス目の左端・上端
_perm2 = [np.random.default_rng(SEED + 7 + k).permutation(N) for k in range(3)]
ORDER2 = np.random.default_rng(SEED + 10).permutation(N)
SAT_NEXT = [((CELL_SITS[j] >= 0) & (CELL_SITS[j] < E_SHINJUKU)) for j in (0, 1, 3)]       # 新宿に着くまでに座れた回


def _grid2(k, shown):
    img = np.zeros((GH2, GW2, 4), np.uint8)
    cols = np.where(SAT_NEXT[k][:, None], C_SAT, C_NO)
    cols = np.where(shown[:, None], cols, C_EMPTY)
    px, py = _g2x[_perm2[k]], _g2y[_perm2[k]]
    for dy in range(CELL2):
        for dx in range(CELL2):
            img[py + dy, px + dx] = cols
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW2, GH2, GW2 * 4), img


_G2C = {}


def draw_grid2(ctx, k, a, n):
    if a <= 0.003:
        return
    n = int(max(0, min(N, n)))
    if n >= N:
        if k not in _G2C:
            _G2C[k] = _grid2(k, np.ones(N, bool))
        surf = _G2C[k][0]
    else:
        shown = np.zeros(N, bool)
        shown[ORDER2[:n]] = True
        surf, _ = _grid2(k, shown)
    ctx.set_source_surface(surf, G2X, G2YS[k])
    ctx.paint_with_alpha(a)


# ============================================================
# 左ページ
# ============================================================
def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 905)
    ctx.clip()


def title_mark(ctx, t, t0, a=1.0):
    """題字「満員電車の空席」＋赤い下線（0秒目から。下線は書くように引く）"""
    w = hand_title(ctx, "満員電車の空席", 112, 84, 76, seed=77, alpha=a)
    pen_line(ctx, 106, 130, 106 + w + 14, 126, RED, seed=5, width=8, progress=clamp01((t - t0) / 0.3), alpha=a)


def tag_under(ctx, slot, s, col, a=1.0, y=910.0, size=36, dx=0.0):
    """立つ人の足元の札（あなた・もう一人・番号）。となりの札とぶつかるときは dx でずらす"""
    tag(ctx, s, SEAT_CX[slot] + dx, y, size, col, a)


def tag_over_seat(ctx, i, s, col, a=1.0, y=328.0, size=36):
    x = max(45 + (text_width(s, size) + 26) / 2, min(SEAT_CX[i], 940 - (text_width(s, size) + 26) / 2))
    tag(ctx, s, x, y, size, col, a)


def ring_person(ctx, kind, i, a, progress=1.0, seed=7, col=RED):
    """人のまわりの赤い丸（ペン）"""
    cx = SEAT_CX[i]
    if kind == "seat":
        pen_circle(ctx, cx, 470, 66, 118, col, seed=seed, width=6, progress=progress, alpha=a)
    else:
        pen_circle(ctx, cx, 738, 70, 150, col, seed=seed, width=6, progress=progress, alpha=a)


def pen_box(ctx, x0, y0, x1, y1, color=RED, seed=1, progress=1.0, alpha=1.0, width=6):
    """手で囲んだ四角（4本のペンの線。progress 0→1 で順に引く）"""
    segs = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    for k, ((ax, ay), (bx, by)) in enumerate(segs):
        pg = clamp01(progress * 4 - k)
        if pg > 0:
            pen_line(ctx, ax, ay, bx, by, color, seed=seed + k, width=width, progress=pg, alpha=alpha)


def arrow_to(ctx, x0, y0, x1, y1, color=RED, progress=1.0, bend=0.0, width=7, a=1.0):
    """少し曲がった矢印（ペン）。(x0,y0) → (x1,y1)"""
    if progress <= 0 or a <= 0.003:
        return
    n = max(2, int(30 * progress))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    ln = math.hypot(nx, ny) or 1.0
    cx_, cy_ = mx + nx / ln * bend, my + ny / ln * bend
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(color, 0.92 * a))
    ctx.set_line_width(width)
    pts = []
    for i in range(n + 1):
        u = i / 30
        u = min(u, 1.0)
        pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx_ + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy_ + u * u * y1))
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    if progress >= 1:
        ex, ey = pts[-1]
        bx, by = pts[-3]
        ang = math.atan2(ey - by, ex - bx)
        for da in (2.6, -2.6):
            ctx.move_to(ex, ey)
            ctx.line_to(ex + 30 * math.cos(ang + da), ey + 30 * math.sin(ang + da))
            ctx.stroke()


def bay_people_static(rec, f, you_set=(), colors=None, you_ring=True):
    """記録の frames[f]（整数）の人の並び。you_set の人を赤くして輪をつける"""
    d = rec_people(rec, float(f), colors=colors, you_red=False)
    for p in d:
        if p["pid"] in you_set:
            p["col"] = RED
            p["you"] = you_ring and p["kind"] == "stand"
    return d


def set_alpha(plist, pid, kind, mul):
    for p in plist:
        if p["pid"] == pid and p["kind"] == kind:
            p["a"] *= mul


def add_person(plist, kind, idx, pid, a, col=None, you=False, pop=0.0):
    if a > 0.01:
        d = dict(kind=kind, idx=idx, pid=pid, a=a, pop=pop)
        if col:
            d["col"] = col
        if you:
            d["you"] = True
        plist.append(d)


def demo_sit(plist, rec, f, seat_i, slot_j, t, t_leave, t_sit, t_back):
    """降りた席に、前に立つ人が座る小さな実演。seat_i の人が降り(t_leave)→ slot_j の人が座る(t_sit)→ もとにもどす(t_back)"""
    fr = rec["frames"][f]
    p_seat, p_stand = fr["seat"][seat_i], fr["stand"][slot_j]
    a_l = clamp01((t - t_leave) / 0.45) * (1 - clamp01((t - t_back) / 0.45))
    a_s = clamp01((t - t_sit) / 0.55) * (1 - clamp01((t - t_back) / 0.45))
    set_alpha(plist, p_seat, "sit", 1 - a_l)
    if p_stand >= 0:
        set_alpha(plist, p_stand, "stand", 1 - a_s)
        sc = _look(p_stand)[0]
        add_person(plist, "sit", seat_i, p_stand, a_s, pop=a_s if a_s < 1 else 0.0)
    return a_l, a_s


def station_text(ctx, s_idx, a=1.0, y=190.0):
    text(ctx, f"いま　{ST_NAMES[int(max(0, min(23, s_idx)))]}", 492, y, 56, INK, alpha=a)


# ---------- 0章 ----------
def L_open(ctx, t):
    rec = SM["open"]["rec"]
    f12 = rec["frames"][12]
    tg0, tg1 = S("g0"), E("g0")
    title_mark(ctx, t, 0.0, 1.0)
    draw_bay_bg(ctx)
    # ふだん: 赤い人（あなた）を選ぶ。端 → 真ん中 → 降りそうな人の前
    t_split = S("c0_1") + 0.42 * dur("c0_1")
    pid_slot = lambda k: f12["stand"][k]
    you_slot = 3
    if S("c0_1") <= t < t_split:
        you_slot = 0
    elif t >= S("c0_2") + 0.5:
        you_slot = 5
    running = t >= tg0 + 0.1
    t_run0, t_run1 = tg0 + 1.3, tg1 - 3.6
    x = 12.0 + 4.0 * ease(clamp01((t - t_run0) / (t_run1 - t_run0)))
    if running:
        you_set = {0, 12}
        plist = rec_people(rec, x, colors={12: BLUE}, you_red=False)
        for p in plist:
            if p["pid"] == 0:
                p["col"], p["you"] = RED, p["kind"] == "stand"
    else:
        plist = rec_people(rec, 12.0, you_red=False)
        for p in plist:
            if p["pid"] == pid_slot(you_slot) and p["kind"] == "stand":
                p["col"], p["you"] = RED, True
    draw_people_list(ctx, plist)
    # 札
    if not running:
        a_in = fade(t, S("c0_0") + 0.4, 0.4)
        tag_under(ctx, you_slot, "あなた", RED, a_in)
        # c0_1: 端・真ん中 の矢印
        if S("c0_1") - 0.2 <= t < S("c0_2") - 0.1:
            a1 = fade(t, S("c0_1") - 0.1, 0.3) * out_fade(t, S("c0_2") - 0.4, 0.3)
            for slot, nm, pr in ((0, "端", 0.0), (3, "真ん中", 0.45)):
                pg = clamp01((t - (S("c0_1") + pr * dur("c0_1") * 0.9)) / 0.35)
                text(ctx, nm, SEAT_CX[slot], 222, 56, RED, alpha=a1 * clamp01(pg * 3))
                arrow_to(ctx, SEAT_CX[slot], 252, SEAT_CX[slot], 338, RED, progress=pg, a=a1)
        if t >= S("c0_2") + 0.4:
            a2 = fade(t, S("c0_2") + 0.4, 0.35)
            tag_over_seat(ctx, 5, "すぐ降りそう？", RED, a2, y=222.0, size=44)
            arrow_to(ctx, SEAT_CX[5], 252, SEAT_CX[5], 338, RED, progress=clamp01((t - S("c0_2") - 0.7) / 0.4), a=a2)
    else:
        a_g = fade(t, tg0 + 0.1, 0.4)
        s_now = station_at(x)
        station_text(ctx, round(s_now), a_g, y=176)
        if x < 15.5:
            tag_under(ctx, 1, "あなた", RED, a_g, dx=58.0)
        tag_under(ctx, 0, "もう一人", BLUE, a_g, dx=-8.0)
        if x >= 15.5:                                                   # あなたが座った: 座った席の上に札
            seat_i = rec["sit_seat"]
            tag_over_seat(ctx, seat_i, "あなた", RED, fade(t, t_run1 - 0.2, 0.3), y=328.0)
    return


def station_x(i):
    return rx(i)


# ---------- 1章 ----------
FIRST_FREE0 = [i for i, p in enumerate(SM["ch1"]["rec"]["frames"][0]["seat"]) if p < 0]


def L_ch1(ctx, t):
    sm = SM["ch1"]
    rec = sm["rec"]
    tg1 = S("g1")
    # 時間 → 記録の位置 x
    ta, tb = S("c1_5") + 0.1, E("c1_6") - 0.2
    if t < ta:
        x = 0.0
    elif t < tg1 + 0.6:
        x = 12.0 * clamp01((t - ta) / (tb - ta))
    else:
        x = 12.0 + 7.0 * clamp01((t - tg1 - 0.6) / 9.0)
    plist = rec_people(rec, x)
    # 路線の図
    show_strip = not (S("c1_7") - 0.2 <= t < tg1 - 0.2)
    a_strip = fade(t, S("c1_1") + 0.1, 0.3) * (1.0 if t < S("c1_7") - 0.2 else (fade(t, tg1 - 0.2, 0.4) if t >= tg1 - 0.2 else 0.0))
    if t >= S("c1_7") - 0.2 and t < tg1 - 0.2:
        a_strip = 0.0
    rv = clamp01((t - S("c1_1") - 0.2) / (dur("c1_1") - 0.6))
    train = station_at(x) if x > 0 or t >= S("c1_4") else 0.0
    mark = None
    if t >= S("c1_14") + 0.3 and t < S("ch2"):
        mark = 19
    if a_strip > 0.003:
        draw_route(ctx, a_strip, reveal=ease(rv), hi=(0, 12) if t >= S("c1_4") else (), train=train if rv > 0.99 else None, mark=mark)
        # 新宿の手前まで（かっこ）
        if S("c1_13") <= t < S("c1_14") + 0.3:
            pg = clamp01((t - S("c1_13") - 0.3) / 0.5)
            ba = a_strip * out_fade(t, S("c1_14") + 0.1, 0.2)
            pen_line(ctx, rx(12), 138, rx(19) - 14, 138, RED, seed=41, width=6, progress=pg, alpha=ba)
            if pg >= 1:
                pen_line(ctx, rx(12), 138, rx(12), 150, RED, seed=42, width=6, alpha=ba)
                pen_line(ctx, rx(19) - 14, 138, rx(19) - 14, 150, RED, seed=43, width=6, alpha=ba)
    draw_bay_bg(ctx)
    # c1_4: 高尾で乗る赤い人（あなた）が、空いた席にすぐ座る
    if S("c1_4") <= t < S("c1_5") + 0.3:
        a_y = fade(t, S("c1_4") + 0.5, 0.5) * out_fade(t, S("c1_5"), 0.3)
        add_person(plist, "sit", FIRST_FREE0[1], 0, a_y, col=RED, pop=a_y if a_y < 1 else 0.0)
    # c1_7: あなたは 7人がけの前
    t7, t8, t9, t10 = S("c1_7"), S("c1_8"), S("c1_9"), S("c1_10")
    pid_you = 0
    if t8 <= t < t9:                                                  # c1_8: 立つ場所は毎回ばらばら（赤い人が次々に変わる）
        order = [0, 5, 2, 6, 1, 4, 3]
        k = min(len(order) - 1, int((t - t8) / (dur("c1_8") / len(order))))
        for p in plist:
            if p["kind"] == "stand":
                p["col"], p["you"] = (RED, True) if p["idx"] == order[k] else (None, False)
                if p["col"] is None:
                    del p["col"]
    if t9 - 0.1 <= t < tg1 + 0.4:                                      # c1_9・c1_10: 空いた席に座る実演（降りるのは あなたの席以外 / あなたの席）
        for p in plist:
            pass
    if t9 <= t < t10:
        demo_sit(plist, rec, 12, 5, 5, t, t9 + 0.5, t9 + 1.5, E("c1_9") + 0.3)
    if t10 <= t < tg1 + 0.45:
        demo_sit(plist, rec, 12, 3, 4, t, t10 + 0.5, t10 + 1.5, tg1 + 0.0)
    draw_people_list(ctx, plist)
    # 札・かこみ
    if t >= S("c1_6") + 0.3 and t < tg1 + 14.0 and x < 18.7:
        a_you = fade(t, S("c1_6") + 0.5, 0.4) if x >= 11.7 else 0.0
        if t8 <= t < t9:
            pass
        else:
            tag_under(ctx, 3, "あなた", RED, a_you)
    if t8 <= t < t9:
        k = min(6, int((t - t8) / (dur("c1_8") / 7)))
        tag_under(ctx, [0, 5, 2, 6, 1, 4, 3][k], "あなた", RED, fade(t, t8, 0.3))
    if x >= 18.95 and t >= tg1:                                       # 座れた
        seat_i = rec["sit_seat"]
        tag_over_seat(ctx, seat_i, "あなた", RED, fade(t, tg1 + 9.6, 0.3), y=328.0)
    # c1_7: 7人がけの席のかっこ
    if t7 <= t < t8 + 0.2:
        a7 = fade(t, t7 + 0.3, 0.4) * out_fade(t, t8 + 0.1, 0.2)
        text(ctx, "7人がけの席", 492, 218, 48, INK, alpha=a7)
        pen_line(ctx, 82, 252, 902, 252, RED, seed=51, width=6, progress=clamp01((t - t7 - 0.5) / 0.6), alpha=a7)
        for xx in (82, 902):
            pen_line(ctx, xx, 252, xx, 266, RED, seed=52 + xx % 7, width=6, alpha=a7 * clamp01((t - t7 - 1.0) / 0.2))
    if t8 <= t < t9:
        text(ctx, "立つ場所は 毎回ばらばら", 492, 218, 48, INK, alpha=fade(t, t8 + 0.1, 0.3) * out_fade(t, t9 - 0.2, 0.2))
    if t9 <= t < t10:
        a9 = fade(t, t9 + 0.1, 0.3) * out_fade(t, t10 - 0.2, 0.2)
        text(ctx, "席が空くと 真ん前の人が座る", 492, 218, 46, INK, alpha=a9)
        ring_person(ctx, "seat", 5, a9 * fade(t, t9 + 0.6, 0.3), progress=clamp01((t - t9 - 0.6) / 0.5), seed=61)
    if t10 <= t < tg1:
        a10 = fade(t, t10 + 0.1, 0.3) * out_fade(t, tg1 - 0.4, 0.3)
        text(ctx, "隣の前の人が 先に座ることも", 492, 218, 46, INK, alpha=a10)
        ring_person(ctx, "seat", 3, a10 * fade(t, t10 + 0.6, 0.3), progress=clamp01((t - t10 - 0.6) / 0.5), seed=62)
        arrow_to(ctx, SEAT_CX[4], 636, SEAT_CX[3] + 30, 548, RED, progress=clamp01((t - t10 - 1.3) / 0.5), bend=-40, a=a10)


# ---------- 2章 ----------
REC1 = SM["ch1"]["rec"]
F12 = REC1["frames"][12]
SLOTS3 = (0, 1, 3)                                                    # 3か所の立ち位置（席1・席2・席4の前）
YOU3 = {F12["stand"][s_] for s_ in SLOTS3}
NAMES3 = ("端の前", "端の隣の前", "真ん中の前")


def door_k(t):
    """ドアの前の人の場面（c2_12x1〜c2_12x3）だけ、車内の絵を 0.8 倍に縮めて、左にドアのあたりを見せる"""
    up = ease(clamp01((t - (S("c2_12x1") - 0.6)) / 0.6))
    down = ease(clamp01((t - S("c2_12b")) / 0.6))
    return 1 - 0.2 * up * (1 - down)


DOOR_X = -110.0                                                    # ドアの前に立つ人の位置（車内の絵の座標。席1の中心 138 より左）


def draw_door_ext(ctx):
    """車内の絵の左の外（x −200〜46）: 壁・床・ドア（ガラスの窓つき）。席の端の外側"""
    xa, xb = -200.0, BAY_X0
    ctx.set_source_rgba(*hexrgb("#e9eef2"))
    ctx.rectangle(xa, Y_CEIL0, xb - xa, Y_SEAT_FLOOR - Y_CEIL0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#c3ccd6"))
    ctx.rectangle(xa, Y_CEIL0, xb - xa, Y_CEIL1 - Y_CEIL0)
    ctx.fill()
    _rr(ctx, -180, Y_CEIL1, 112, Y_SEAT_FLOOR - Y_CEIL1, 3, "#b4bec9", 1.0, lw=3.5)
    _rr(ctx, -170, 346, 42, 170, 5, "#d9eaf6", 1.0, lw=2.5)
    _rr(ctx, -120, 346, 42, 170, 5, "#d9eaf6", 1.0, lw=2.5)
    ctx.set_source_rgba(*hexrgb("#d9d3c4"))
    ctx.rectangle(xa, Y_SEAT_FLOOR + 1.5, xb - xa, 935 - Y_SEAT_FLOOR - 1.5)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#bdb6a4", 0.8))
    ctx.set_line_width(2)
    for yy in (650, 770, 892):
        ctx.move_to(xa, yy)
        ctx.line_to(xb, yy)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(3.5)
    ctx.move_to(xa, Y_SEAT_FLOOR)
    ctx.line_to(xb, Y_SEAT_FLOOR)
    ctx.stroke()


def L_c2(ctx, t):
    plist = bay_people_static(REC1, 12, you_set=YOU3, you_ring=True)
    t1, t2, t3 = S("c2_1"), S("c2_2"), S("c2_3")
    t13, t18 = S("c2_13"), S("c2_18")
    # c2_12: 端の席が空いて、端の前の人が座らなかったとき… 端の席の人が降りる実演
    t12 = S("c2_12")
    dk = door_k(t)
    ctx.save()
    if dk < 0.999:
        ctx.translate(940, 935)
        ctx.scale(dk, dk)
        ctx.translate(-940, -935)
        BAY_XF[:] = [dk, 940.0, 935.0]
    draw_bay_bg(ctx)
    if dk < 0.999:
        draw_door_ext(ctx)
    if t12 + 0.3 <= t < S("c2_13"):
        set_alpha(plist, F12["seat"][0], "sit", 1 - clamp01((t - t12 - 0.4) / 0.45) * (1 - clamp01((t - E("c2_12") - 0.1) / 0.4)))
    if S("c2_12x2") <= t < S("c2_12b") + 0.3:                       # 席を立つ人
        set_alpha(plist, F12["seat"][0], "sit", 1 - 0.7 * clamp01((t - S("c2_12x2") - 0.3) / 0.4) * (1 - clamp01((t - S("c2_12x3") - 0.5) / 0.4)))
    draw_people_list(ctx, plist)
    if S("c2_12x1") - 0.3 <= t < S("c2_12b") + 0.3:                 # ドアの前に立つ人・印・席の端からドアへの矢印
        a_d = fade(t, S("c2_12x1") + 0.1, 0.4) * out_fade(t, S("c2_12b") - 0.5, 0.3)
        draw_stander(ctx, DOOR_X, STAND_COLS[2], HAIRS[1], a=a_d, arm=False)
        if a_d > 0.003 and t >= S("c2_12x1") + 0.8:
            pen_circle(ctx, DOOR_X, 745, 70, 158, RED, seed=281, width=6, progress=clamp01((t - S("c2_12x1") - 0.8) / 0.5), alpha=a_d)
        if a_d > 0.003 and t >= S("c2_12x2") + 0.2:
            arrow_to(ctx, 92, 470, DOOR_X + 62, 470, RED, progress=clamp01((t - S("c2_12x2") - 0.2) / 0.6), bend=-26, width=8, a=a_d)
    ctx.restore()
    BAY_XF[:] = [1.0, 940.0, 935.0]
    if S("c2_12x1") + 0.3 <= t < S("c2_12x2") + 0.5:                # 札「ドアの前」
        a_t = fade(t, S("c2_12x1") + 0.3, 0.3) * out_fade(t, S("c2_12x2") + 0.2, 0.3)
        tag(ctx, "ドアの前", max(50 + (text_width("ドアの前", 36) + 26) / 2, 940 - (940 - DOOR_X) * dk), 935 - 25 * dk, 36, RED, a_t)
    if S("c2_12x3") <= t < S("c2_12b") + 0.2:                       # 付せん（この動画の決めごと）
        mini_sticky(ctx, "ドアの前の人は 端の席に座らない\n（この動画の決めごと）", 60, 140, 38, "yellow",
                    a=fade(t, S("c2_12x3") + 0.3, 0.3) * out_fade(t, S("c2_12b") - 0.1, 0.3), align="left", tilt=-0.012)
    # 番号の札
    for k, sl in enumerate(SLOTS3):
        a_k = fade(t, t1 + 0.9 + 1.3 * k, 0.35) * (1.0 if dk >= 0.999 else 0.0)
        if a_k > 0.003:
            cx = SEAT_CX[sl]
            ctx.set_source_rgba(*hexrgb(RED, a_k))
            ctx.arc(cx, 912, 25, 0, 2 * math.pi)
            ctx.fill()
            text(ctx, str(k + 1), cx, 913, 40, "#ffffff", alpha=a_k)
    # c2_1: 左右は同じ（中央の点線）
    if t1 + 3.6 <= t < t2 + 0.5:
        a_s = fade(t, t1 + 3.6, 0.4) * out_fade(t, t2 + 0.2, 0.3)
        ctx.set_source_rgba(*hexrgb(INK, 0.55 * a_s))
        ctx.set_line_width(4)
        ctx.set_dash([14, 10])
        ctx.move_to(SEAT_CX[3], 262)
        ctx.line_to(SEAT_CX[3], 884)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "片側だけで比べる", 280, 226, 44, RED, alpha=a_s)
        text(ctx, "こちらも同じ", 712, 226, 44, INK, alpha=a_s)
    # c2_2: 端の前 → 目の前の席と 片側の隣の席
    if t2 <= t < t3:
        a = fade(t, t2 + 0.2, 0.3) * out_fade(t, t3 - 0.2, 0.2)
        text(ctx, "端の前: 目の前の席・隣の席", 492, 222, 44, INK, alpha=a)
        for i, nm in ((0, "目の前"), (1, "隣")):
            ring_person(ctx, "seat", i, a, progress=clamp01((t - t2 - 0.5 - 0.5 * i) / 0.5), seed=71 + i)
    if t3 <= t < S("c2_4"):
        a = fade(t, t3 + 0.2, 0.3) * out_fade(t, S("c2_4") - 0.2, 0.2)
        text(ctx, "真ん中の前: 目の前の席・両側の隣の席", 492, 222, 40, INK, alpha=a)
        for k, i in enumerate((3, 2, 4)):
            ring_person(ctx, "seat", i, a, progress=clamp01((t - t3 - 0.5 - 0.4 * k) / 0.5), seed=74 + i)
    # c2_5〜c2_6: 端の席の人は 長く乗っている？
    if S("c2_5") <= t < S("g2"):
        a = fade(t, S("c2_5") + 0.2, 0.3)
        text(ctx, "端の席の人は 長く乗っている？", 492, 222, 44, INK, alpha=a * out_fade(t, S("g2") - 0.2, 0.2))
        ring_person(ctx, "seat", 0, a * out_fade(t, S("g2") - 0.2, 0.2), progress=clamp01((t - S("c2_5") - 0.5) / 0.5), seed=78)
    # g2〜c2_11: 比べる3か所をゆっくり光らせる
    if S("g2") <= t < S("c2_13"):
        pass
    k_hi, t_ring = (), 0.0
    for ta_, tb_, ks_ in ((S("c2_8"), S("c2_9"), (0,)), (S("c2_9"), S("c2_10"), (1, 2)), (S("c2_10"), S("c2_10b"), (0,)),
                          (S("c2_10b"), S("c2_11"), (0, 1)), (S("c2_11"), S("c2_12"), (1,))):
        if ta_ <= t < tb_:
            k_hi, t_ring = ks_, ta_
    for k_ in k_hi:
        ring_person(ctx, "stand", SLOTS3[k_], 1.0, progress=clamp01((t - t_ring - 0.2) / 0.5), seed=91 + k_)
    for ta_, tb_ in ((t12, S("c2_12x1") - 0.6), (S("c2_12b") + 0.6, S("c2_12c"))):
        if ta_ <= t < tb_:
            a = fade(t, ta_ + 0.2, 0.3) * out_fade(t, tb_ - 0.3, 0.3)
            text(ctx, "端の席が空いたら、ねらえるのは…", 492, 222, 42, INK, alpha=a)
            ring_person(ctx, "seat", 0, a * clamp01((t - ta_ - 0.7) / 0.3), progress=clamp01((t - ta_ - 0.8) / 0.5), seed=95)
            arrow_to(ctx, SEAT_CX[1] - 20, 636, SEAT_CX[0] + 40, 548, RED, progress=clamp01((t - ta_ - 1.8) / 0.5), bend=-36, a=a)
    # c2_13〜c2_17: 左上に路線図（八王子と日野に印）
    a_rt = fade(t, S("c2_13") + 0.2, 0.4) * out_fade(t, S("c2_18") - 0.2, 0.3)
    if a_rt > 0.003:
        draw_route(ctx, a_rt, labels=LABELS_C2, hi=(2, 4), red=(2,))
        if t >= S("c2_14") + 0.3:
            pg_ = clamp01((t - S("c2_14") - 0.3) / 0.4)
            pen_circle(ctx, rx(2), RT_Y, 19, 19, RED, seed=261, width=5, progress=pg_, alpha=a_rt)
            pen_circle(ctx, rx(4), RT_Y, 19, 19, BLUE, seed=262, width=5, progress=clamp01((t - S("c2_14") - 1.0) / 0.4), alpha=a_rt)
    # c2_13〜c2_17: 端の席の人・真ん中の席の人 は どこから乗った？
    if S("c2_14") <= t < S("c2_18"):
        a = fade(t, S("c2_14") + 0.2, 0.4) * out_fade(t, S("c2_18") - 0.2, 0.3)
        ring_person(ctx, "seat", 0, a, progress=clamp01((t - S("c2_14") - 0.4) / 0.4), seed=81)
        ring_person(ctx, "seat", 3, a, progress=clamp01((t - S("c2_14") - 1.0) / 0.4), seed=83, col=BLUE)
        tag_over_seat(ctx, 0, "端＝八王子のあたり", RED, a, y=328.0)
        a_b = a * fade(t, S("c2_14") + 1.0, 0.3)
        w_b = text_width("真ん中＝日野のあたり", 36) + 26
        tag(ctx, "真ん中＝日野のあたり", 430 + w_b / 2, 328.0, 36, BLUE, a_b)


# ---------- 3章 ----------
STAT_PICK = (5, 12, 13, 15)                                            # 立川・三鷹・吉祥寺・荻窪
LABELS_C2 = dict(LABELS_MAIN)
LABELS_C2[4] = ("日野", "c")
LABELS_C3 = dict(LABELS_MAIN)
LABELS_C3[13] = ("吉祥寺", "c")


def L_ch3(ctx, t):
    tg3 = S("g3")
    rv = fade(t, S("ch3") + 0.1, 0.35)
    # 乗る駅の番号 → 記録の frame
    t0, t1 = tg3 + 0.2, E("g3") - 0.3
    u = clamp01((t - t0) / (t1 - t0))
    k = min(3, int(u * 4)) if t >= tg1_ch3() else None
    cur = STAT_PICK[k] if k is not None else 12
    if t >= E("g3"):
        cur = 15
    plist = bay_people_static(REC1, cur, you_set=(), you_ring=False)
    # frame の人のうち、席4の前に立つ人を赤く（いなければ赤い人を足す）
    pid3 = REC1["frames"][cur]["stand"][3]
    if pid3 >= 0:
        for p in plist:
            if p["pid"] == pid3 and p["kind"] == "stand":
                p["col"], p["you"] = RED, True
    else:
        add_person(plist, "stand", 3, 999, 1.0, col=RED, you=True)
    # 路線
    red_st = [s_ for i_, s_ in enumerate(STAT_PICK) if t >= S("c3_1") + 0.6 + 0.9 * i_]
    draw_route(ctx, rv, labels=LABELS_C3, hi=tuple(red_st), mark=19 if t >= S("c3_2") else None,
               train=cur if t >= tg3 - 0.3 and t < S("c3_2") else None, red=tuple(red_st))
    draw_bay_bg(ctx)
    draw_people_list(ctx, plist)
    a_y = fade(t, S("ch3") + 0.4, 0.3)
    tag_under(ctx, 3, "あなた", RED, a_y)
    # c3_4: 立川から新宿までに、国分寺・吉祥寺など降りる人の多い駅をいくつも通る
    if S("c3_4") <= t < S("c3_5"):
        a = fade(t, S("c3_4") + 0.1, 0.3) * out_fade(t, S("c3_5") - 0.2, 0.3)
        text(ctx, "降りる人の多い駅を いくつも通る", 492, 56, 36, RED, alpha=a)
        pen_line(ctx, rx(5), 132, rx(19) - 14, 132, RED, seed=33, width=6, progress=clamp01((t - S("c3_4") - 0.3) / 0.8), alpha=a)
        for i_ in (8, 13):
            pen_circle(ctx, rx(i_), RT_Y, 17, 17, RED, seed=240 + i_, width=5, progress=clamp01((t - S("c3_4") - 1.0 - 0.5 * (i_ == 13)) / 0.4), alpha=a)


def tg1_ch3():
    return S("g3") + 0.2


# ---------- 4章（まとめ） ----------
def L_c4(ctx, t):
    rec = SM["ch1"]["rec"]
    t1, t2, t3, t4 = S("c4_1"), S("c4_2"), S("c4_3"), S("c4_4")
    red_ = (12,) + ((5,) if t >= t4 else ())
    draw_route(ctx, 1.0, hi=red_, mark=19, train=19.0, red=red_)
    draw_bay_bg(ctx)
    plist = rec_people(rec, 19.0)
    draw_people_list(ctx, plist)
    tag_over_seat(ctx, rec["sit_seat"], "あなた", RED, 1.0, y=328.0)
    if t1 <= t < t2:                                                     # 東京までに 約9割
        a = fade(t, t1 + 0.2, 0.3) * out_fade(t, t2 - 0.2, 0.2)
        pen_line(ctx, rx(12), 132, rx(23), 132, RED, seed=34, width=6, progress=clamp01((t - t1 - 0.3) / 0.6), alpha=a)
        text(ctx, "三鷹 → 東京までに 座れる", 492, 56, 36, RED, alpha=a)
    if t2 <= t < t3:                                                     # 新宿までに 約6割
        a = fade(t, t2 + 0.2, 0.3) * out_fade(t, t3 - 0.2, 0.2)
        pen_line(ctx, rx(12), 132, rx(19) - 14, 132, RED, seed=35, width=6, progress=clamp01((t - t2 - 0.3) / 0.6), alpha=a)
        text(ctx, "三鷹 → 新宿までに 座れる", 492, 56, 36, RED, alpha=a)
    if t3 <= t < t4:                                                     # 端の前より 端の隣の前
        a = fade(t, t3 + 0.2, 0.3) * out_fade(t, t4 - 0.2, 0.2)
        ring_person(ctx, "stand", 0, a * 0.8, progress=clamp01((t - t3 - 0.3) / 0.5), seed=131, col=PENCIL_T)
        ring_person(ctx, "stand", 1, a, progress=clamp01((t - t3 - 0.9) / 0.5), seed=132)
        tag_under(ctx, 0, "端の前", PENCIL_T, a, dx=-8.0)
        tag_under(ctx, 1, "端の隣の前", RED, a * fade(t, t3 + 0.9, 0.3), dx=62.0)
    if t4 <= t < S("c4_4a"):                                             # 乗る駅で 2倍ちがう（立川と三鷹）
        a = fade(t, t4 + 0.2, 0.3) * out_fade(t, S("c4_4a") - 0.2, 0.2)
        text(ctx, "立川と三鷹で 新宿に着く前に座れる割合が 2倍ほど", 492, 56, 36, RED, alpha=a)


# ---------- 0章の後ろ「中央線の紹介」（0b）: 東京都の輪郭（Natural Earth 10m admin-1・public domain）を手書き風に描き、
#            駅の緯度経度（Wikidata P625・CC0）を同じ投影で置く。丸の面積は 1日の上りの乗車＋降車（センサス2015）に比例 ----------
INTRO_NAMES = ["高尾", "八王子", "立川", "国分寺", "三鷹", "吉祥寺", "荻窪", "中野", "新宿", "御茶ノ水", "東京"]
CIRCLE_LOG = []                                                     # 描いた丸・点・棒（種類:名前, 値1, 値2）
CLOG_BY_T = {}


def _load_stations():
    with open(SRC / "stations_latlon.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(ln for ln in f if not ln.startswith("#")))
    return {r["station"]: (int(r["order"]), float(r["lon"]), float(r["lat"])) for r in rows}


_STN = _load_stations()
INTRO_ST = [(nm, _STN[nm][0], _STN[nm][1], _STN[nm][2]) for nm in INTRO_NAMES]        # (名前, order, 経度, 緯度)
INTRO_R_MAX, INTRO_R_FLOOR = 80.0, 10.0


def _intro_values():
    with open(SRC / "chuo_kaisoku_up_24.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(ln for ln in f if not ln.startswith("#")))
    by = {int(r["order"]): int(r["up_board"]) + int(r["up_alight"]) for r in rows}
    return [by[o] for _n, o, *_r in INTRO_ST]


INTRO_V = _intro_values()
INTRO_R = [INTRO_R_MAX * math.sqrt(v / max(INTRO_V)) for v in INTRO_V]            # 面積が人数に比例（最大＝新宿 80px）
BAR_X0, BAR_LEN = 1215.0, 580.0
INTRO_BAR = [BAR_LEN * v / max(INTRO_V) for v in INTRO_V]                          # 横棒の長さが人数に比例

_TK = json.loads((SRC / "tokyo_outline.json").read_text(encoding="utf-8"))
RING = [tuple(p) for p in max(_TK["rings"]["Tokyo"], key=len)]                      # 東京都の本土側（島しょ部をのぞく最大の輪）
if RING[0] == RING[-1]:
    RING = RING[:-1]
LAT0 = 35.69                                                                       # 投影: 正距円筒図法（緯度35.69度で経度を縮める）
COSL = math.cos(math.radians(LAT0))
CAM_WIDE = (139.4045, 35.684, 1120.0)                                              # (中心の経度, 中心の緯度, 1度あたりの px)  全体
CAM_ZOOM = (139.525, 35.692, 2030.0)                                               # 駅のあたりを拡大
MAP_YC, MAP_XC = 640.0, 490.0


def to_screen(lon, lat, cam):
    clon, clat, sc = cam
    return MAP_XC + (lon - clon) * COSL * sc, MAP_YC - (lat - clat) * sc


def from_screen(x, y, cam):
    clon, clat, sc = cam
    return clon + (x - MAP_XC) / (COSL * sc), clat - (y - MAP_YC) / sc


def _smooth_ll(pts, seed, n=3, jit=0.0026):
    """東京都の頂点（経度・緯度）を通る、なめらかな手書き風の線（頂点から 0.0026度（約290m）以内のゆれ）"""
    rng = np.random.default_rng(seed)
    m = len(pts)
    out, dev = [], 0.0
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            u = k / n
            q = []
            for a in (0, 1):
                q.append(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * u + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * u * u + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * u ** 3))
            if k == 0:
                q = [p1[0], p1[1]]
                dx, dy = rng.normal(0, jit / 2, 2)
            else:
                dx, dy = rng.normal(0, jit / 2, 2)
            dx, dy = max(-jit, min(jit, dx)), max(-jit, min(jit, dy))
            dev = max(dev, abs(dx), abs(dy))
            out.append((q[0] + dx, q[1] + dy))
    return out, dev


MAP_LL, MAP_DEV = _smooth_ll(RING, 5)
INTRO_OY = 0.0


def draw_map(ctx, cam, a, prog_, ring=None):
    """東京都の輪郭（手書き風）。prog_ 0→1 で輪郭を引き、そのあと薄い緑を塗る"""
    if a <= 0.003:
        return
    pts = [to_screen(lo, la, cam) for lo, la in (ring or MAP_LL)]
    n = len(pts)
    k = max(2, int(n * clamp01(prog_ / 0.8)))
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if prog_ > 0.8:
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb("#dfe9cf", 0.85 * a * clamp01((prog_ - 0.8) / 0.2)))
        ctx.fill()
    for dx, dy, wd, al in ((0.0, 0.0, 5.0, 0.85), (2.0, -1.5, 2.5, 0.4)):          # 2本重ねた、ペンの線
        ctx.set_source_rgba(*hexrgb(INK, al * a))
        ctx.set_line_width(wd)
        ctx.move_to(pts[0][0] + dx, pts[0][1] + dy)
        for q in pts[1:k]:
            ctx.line_to(q[0] + dx, q[1] + dy)
        if k >= n:
            ctx.close_path()
        ctx.stroke()
    ctx.restore()


def cam_at(t):
    zp = ease(clamp01((t - (S("c0b_1") - 0.1)) / 1.6))
    return tuple(lerp(a, b, zp) for a, b in zip(CAM_WIDE, CAM_ZOOM))


STN_XY = [to_screen(lo, la, CAM_ZOOM) for _n, _o, lo, la in INTRO_ST]                # 拡大したあとの駅の位置
LABEL_ABOVE = {"八王子", "国分寺", "吉祥寺", "中野", "御茶ノ水"}
INTRO_INK = "#24324a"


def title_mark_intro(ctx, t):
    w = hand_title(ctx, "中央線の紹介", 112, 84, 76, seed=78)
    pen_line(ctx, 106, 130, 106 + w + 14, 126, RED, seed=6, width=8, progress=clamp01((t - S("c0b_0") - 0.2) / 0.4))


def L_intro(ctx, t):
    t0, t1, t2, t3, t4, t5 = (S(f"c0b_{k}") for k in range(6))
    title_mark_intro(ctx, t)
    a_we = fade(t, t0 + 0.3, 0.4)
    text(ctx, "← 西", 118, 345, 44, PENCIL_T, alpha=a_we)
    text(ctx, "東 →", 872, 345, 44, PENCIL_T, alpha=a_we)
    cam = cam_at(t)
    draw_map(ctx, cam, 1.0, clamp01((t - t0 - 0.2) / max(1.0, dur("c0b_0") - 0.6)))
    xs = STN_XY
    t_line = t1 + 1.8                                                                # 拡大が終わってから、高尾 → 東京の線を引く
    pr = clamp01((t - t_line) / max(1.0, E("c0b_1") - t_line - 0.3))
    if pr > 0:
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        pos = pr * (len(xs) - 1 + 0.5)
        for col, w in ((INTRO_INK, 11), ("#8aa4c6", 6)):
            ctx.set_source_rgba(*hexrgb(col, 0.95))
            ctx.set_line_width(w)
            ctx.move_to(*xs[0])
            for i in range(1, len(xs)):
                if i - 1 >= pos:
                    break
                f_ = min(1.0, pos - (i - 1))
                ctx.line_to(xs[i - 1][0] + (xs[i][0] - xs[i - 1][0]) * f_, xs[i - 1][1] + (xs[i][1] - xs[i - 1][1]) * f_)
            ctx.stroke()
        ctx.restore()
    # 丸（c0b_3 のあいだに左から順に大きくなる。大きい丸を先に描いて、小さい丸が上に見えるようにする）
    t_c0 = t3 + 0.2
    span = max(1.0, dur("c0b_3") - 0.8)
    for i in sorted(range(len(INTRO_ST)), key=lambda k: -INTRO_R[k]):
        nm = INTRO_ST[i][0]
        x, y = xs[i]
        u = ease(clamp01((t - t_c0 - span * i / len(INTRO_ST)) / 0.5))
        if u <= 0.003:
            continue
        r = INTRO_R[i] * u
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(RED if (nm == "新宿" and t >= t5 + 0.3) else BLUE_L, 0.5))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(3)
        ctx.stroke()
        if u >= 0.999:
            CIRCLE_LOG.append(("circle:" + nm, INTRO_R[i], 1.0))
    # 駅の点と名前（路線が届いた駅から）
    for i, (nm, _o, lo, la) in enumerate(INTRO_ST):
        x, y = xs[i]
        a_i = ease(clamp01((pr * (len(xs) - 1 + 0.5) - i + 0.3) / 0.5)) if pr > 0 else 0.0
        if a_i <= 0.003:
            continue
        ctx.arc(x, y, 7, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#ffffff", a_i))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a_i))
        ctx.set_line_width(3)
        ctx.stroke()
        if a_i >= 0.999:
            CIRCLE_LOG.append(("dot:" + nm, x, y))
        w_ = text_width(nm, 36)
        lx = max(46 + w_ / 2, min(940 - w_ / 2, x))
        off = INTRO_R[i] + 34
        ty = y - off if nm in LABEL_ABOVE else y + off
        col = RED if (nm == "新宿" and t >= t5 + 0.3) else INK
        if abs(lx - x) > 2:
            ctx.set_source_rgba(*hexrgb(INK, 0.6 * a_i))
            ctx.set_line_width(2.5)
            ctx.move_to(x, y + (-12 if nm in LABEL_ABOVE else 12))
            ctx.line_to(lx, ty + (18 if nm in LABEL_ABOVE else -18))
            ctx.stroke()
        text(ctx, nm, lx, ty, 36, col, alpha=a_i)
    if t >= t5 + 0.3:                                                               # 新宿に赤丸
        i = 8
        pen_circle(ctx, xs[i][0], xs[i][1], INTRO_R[i] + 14, INTRO_R[i] + 14, RED, seed=211, width=7, progress=clamp01((t - t5 - 0.3) / 0.6))
    if t4 <= t < t5 + 0.5:                                                          # 立川・吉祥寺
        a4 = fade(t, t4 + 0.2, 0.3) * out_fade(t, t5 + 0.1, 0.3)
        for k, i in enumerate((2, 5)):
            pen_circle(ctx, xs[i][0], xs[i][1], INTRO_R[i] + 9, INTRO_R[i] + 9, PENCIL_T, seed=221 + k, width=5,
                       progress=clamp01((t - t4 - 0.4 - 0.9 * k) / 0.5), alpha=a4)
    # 朝の向き: 東京向きの矢印（地図の上）
    if t >= t2 + 0.1:
        a2 = fade(t, t2 + 0.1, 0.3)
        text(ctx, "朝は 東京行きが混む", 480, 262, 46, RED, alpha=a2)
        arrow_to(ctx, 200, 345, 790, 345, RED, progress=clamp01((t - t2 - 0.5) / 0.9), width=9, a=a2)


def L_ch0(ctx, t):
    a_in = fade(t, S("c0b_0") - 0.15, 0.5)
    if a_in < 0.997:
        grp(ctx, 1 - a_in, L_open, t)
    grp(ctx, a_in, L_intro, t)


def map_compare(path):
    """確認用: 左＝境界データをそのまま描いた図（東京都の本土側・隣の県・駅）／右＝動画で描く手書き風。同じ投影・同じ拡大"""
    W_, H_ = 1920, 1000
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_, H_)
    ctx = cairo.Context(surf)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.paint()
    text(ctx, "境界データ（Natural Earth 10m・そのまま）", 480, 40, 36, INK)
    text(ctx, "動画で描く手書き風の輪郭", 1440, 40, 36, INK)
    for panel, ox in ((0, 0), (1, 960)):
        ctx.save()
        ctx.rectangle(ox + 10, 70, 940, 920)
        ctx.clip()
        ctx.translate(ox - 0.0, 0)
        cam = (139.4045, 35.62, 1120.0)
        sx = lambda lo, la: (to_screen(lo, la, cam)[0], to_screen(lo, la, cam)[1] - 100 + 60)
        if panel == 0:
            for nm, col in (("Saitama", "#f3d9d9"), ("Kanagawa", "#d9e5f3"), ("Yamanashi", "#e6f0d0"), ("Chiba", "#f3ecd0")):
                ring = max(_TK["rings"][nm], key=len)
                pts = [sx(*p) for p in ring]
                ctx.move_to(*pts[0])
                for q in pts[1:]:
                    ctx.line_to(*q)
                ctx.close_path()
                ctx.set_source_rgba(*hexrgb(col, 1.0))
                ctx.fill_preserve()
                ctx.set_source_rgba(*hexrgb(INK, 0.6))
                ctx.set_line_width(2)
                ctx.stroke()
                cx_ = sum(p[0] for p in pts) / len(pts)
                cy_ = sum(p[1] for p in pts) / len(pts)
                jp = {"Saitama": "埼玉県", "Kanagawa": "神奈川県", "Yamanashi": "山梨県", "Chiba": "千葉県"}[nm]
                text(ctx, jp, cx_, cy_, 36, PENCIL_T)
            pts = [sx(*p) for p in RING]
            ctx.move_to(*pts[0])
            for q in pts[1:]:
                ctx.line_to(*q)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb("#dfe9cf", 1.0))
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.95))
            ctx.set_line_width(3)
            ctx.stroke()
        else:
            pts = [sx(lo, la) for lo, la in MAP_LL]
            ctx.move_to(*pts[0])
            for q in pts[1:]:
                ctx.line_to(*q)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb("#dfe9cf", 0.85))
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.85))
            ctx.set_line_width(5)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
        # 駅（点）と名前
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(5)
        ps = [sx(lo, la) for _n, _o, lo, la in INTRO_ST]
        ctx.move_to(*ps[0])
        for q in ps[1:]:
            ctx.line_to(*q)
        ctx.stroke()
        for (nm, _o, lo, la), (x, y) in zip(INTRO_ST, ps):
            ctx.arc(x, y, 5, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb(RED if nm in ("高尾", "東京", "新宿") else INK, 1.0))
            ctx.fill()
            if nm in ("高尾", "東京", "新宿", "立川"):
                text(ctx, nm, x, y - 34 if nm == "新宿" else y + 34, 36, RED)
        # 方角
        text(ctx, "北", 880, 110, 40, INK)
        text(ctx, "↑", 880, 150, 40, INK)
        text(ctx, "西（奥多摩・山梨）", 170, 420, 36, INK)
        text(ctx, "東京湾", 870, 690, 36, INK)
        ctx.restore()
    surf.write_to_png(str(path))
    print("地図の比べ用:", path)


LEFTS = [L_ch0, L_ch1, L_c2, L_ch3, L_c4]


# ============================================================
# 右ページ（付箋・マス目・棒グラフ・欄。細かい数字は付箋と欄だけ。声は台本どおり）
# ============================================================
def legend_sq(ctx, items, cx, y, size=36, gap=40, a=1.0):
    ws = [46 + text_width(lab, size, bold=False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.fill()
        text(ctx, lab, x + 42, y, size, INK, align="left", bold=False, alpha=a)
        x += w + gap


def stk(ctx, t, tid, s, y, color="yellow", fg=INK, a=1.0, size=38, tilt=-0.012, off=0.3):
    """右ページの付箋。時刻 tid（台本の文の id）から現れる"""
    t0 = S(tid) + off
    if t >= t0:
        mini_sticky(ctx, s, RX, y, size, color, fg=fg, a=a * fade(t, t0), align="left", tilt=tilt)


def R_intro(ctx, t):
    a = fade(t, S("c0b_0") - 0.1, 0.4)
    if a <= 0.003:
        return
    a_st = a * out_fade(t, S("c0b_3") - 0.1, 0.35)
    stk(ctx, t, "c0b_0", "中央線を 少しだけ紹介", 380, "yellow", a=a_st)
    stk(ctx, t, "c0b_1", "中央線の快速　高尾 → 東京", 466, "blue", a=a_st, tilt=0.012)
    stk(ctx, t, "c0b_2", "朝は 東京行きが混む", 552, "pink", fg=RED, a=a_st)
    # c0b_3 から: 丸の大きさ ＝ 乗り降りする人の多さ。駅ごとの横棒（長さが人数に比例・数字は出さない）
    if t >= S("c0b_3") + 0.1:
        mini_sticky(ctx, "丸の大きさ ＝ 乗り降りする人の多さ", RX, 352, 38, "mint", a=a * fade(t, S("c0b_3") + 0.1), align="left", tilt=0.01)
        t_c0, span = S("c0b_3") + 0.2, max(1.0, dur("c0b_3") - 0.8)
        for i, (nm, *_r) in enumerate(INTRO_ST):
            y = 432 + 44 * i
            u = ease(clamp01((t - t_c0 - span * i / len(INTRO_ST)) / 0.5))
            hi = nm == "新宿" and t >= S("c0b_5") + 0.3
            text(ctx, nm, RX, y, 36, RED if hi else INK, align="left", alpha=a * fade(t, t_c0 + span * i / len(INTRO_ST), 0.3))
            if u > 0.003:
                ctx.set_source_rgba(*hexrgb(RED if hi else BLUE_L, 0.9 * a))
                rrect(ctx, BAR_X0, y - 15, max(2.0, INTRO_BAR[i] * u), 30, 5)
                ctx.fill()
                if u >= 0.999:
                    CIRCLE_LOG.append(("bar:" + nm, INTRO_BAR[i], 1.0))
        if t >= S("c0b_5") + 0.3:
            i = 8
            pen_box(ctx, RX - 14, 432 + 44 * i - 26, BAR_X0 + INTRO_BAR[i] + 24, 432 + 44 * i + 26, RED, seed=231,
                    progress=clamp01((t - S("c0b_5") - 0.3) / 0.6), alpha=a)


def R_ch0(ctx, t):
    R_open_title(ctx, t)
    grp(ctx, out_fade(t, S("c0b_0") - 0.3, 0.4), R_open_body, t)
    R_intro(ctx, t)


def R_open_title(ctx, t):
    text(ctx, "満員電車、", RX, 175, 54, INK, align="left")
    s2 = "どこに立つ？"
    text(ctx, s2, RX, 255, 60, INK, align="left")
    if t >= S("c0_6") + 0.2:
        pen_line(ctx, RX - 4, 298, RX + text_width(s2, 60) + 4, 294, RED, seed=7, width=6, progress=clamp01((t - S("c0_6") - 0.2) / 0.5))


def R_open_body(ctx, t):
    g_a = out_fade(t, S("c0_3") - 0.1, 0.35)                              # 冒頭〜早回しの説明
    if g_a > 0.003:
        wr(ctx, "端の前？　真ん中の前？", RX, 352, 44, INK, S("c0_1") + 0.2, t, cps=8, alpha=g_a)
        if t >= S("c0_2") + 0.3:
            mini_sticky(ctx, "「すぐ降りそう」と思ったのに\nずっと座ったまま", RX, 460, 38, "pink", a=g_a * fade(t, S("c0_2") + 0.3), align="left", tilt=-0.012)
        ff = fade(t, S("g0") + 0.1, 0.25) * out_fade(t, E("g0") - 0.2, 0.3)
        if ff > 0.003:
            text(ctx, "▶▶ 早回し（三鷹から乗る）", RX, 580, 40, PENCIL_T, align="left", bold=False, alpha=ff)
            for k, (col, lab) in enumerate(((RED, "あなた"), (BLUE, "もう一人"))):
                xx = RX + k * 250
                ctx.set_source_rgba(*hexrgb(col, ff))
                ctx.arc(xx + 14, 650, 14, 0, 2 * math.pi)
                ctx.fill()
                text(ctx, lab, xx + 40, 650, 38, INK, align="left", alpha=ff)
    p2 = out_fade(t, S("c0_5") - 0.1, 0.35)                               # 早回しのあと〜中央線の説明
    if p2 > 0.003:
        wr(ctx, "→ 端の隣の前の人が先に座った", RX, 352, 40, RED, E("g0") + 0.1, t, cps=11, alpha=p2)
        stk(ctx, t, "c0_3", "立つ場所や乗る駅で 座りやすさはちがう", 450, "yellow", a=p2)
        stk(ctx, t, "c0_4", "中央線の朝の電車を\nコンピューターの中に作る", 580, "mint", tilt=0.01, a=p2)
    if t >= S("c0_5") + 0.2:
        sticky(ctx, "1万回", RCX, 380, 72, "pink", fg=RED, a=fade(t, S("c0_5") + 0.2, 0.3), tilt=-0.02)
    if t >= S("c0_6") + 0.5:
        mini_sticky(ctx, "数字にしてみる\n・どの駅で座れるか\n・どこに立てば座りやすいか\n・乗る駅でどう変わるか", RX, 690, 38, "blue", a=fade(t, S("c0_6") + 0.5), align="left", tilt=0.01)


# ---- 1章 ----
BAR_Y0 = 540.0
BAR_X = [1100.0 + 68.0 * i for i in range(11)]
BAR_ST = list(range(13, 23)) + [None]                                    # 吉祥寺〜神田 と「東京まで座れず」
BAR_V = [PMF_MITAKA[s_] if s_ is not None else A7["三鷹"]["p_never"] for s_ in BAR_ST]
BAR_H = 880.0                                                            # 値 × この px（0.288 → 253px）


def bar_col(i):
    s_ = BAR_ST[i]
    if s_ is None:
        return "#b9b4a5"
    if s_ < 19:
        return BLUE_L
    if s_ == 19:
        return RED
    return "#8a9bb8"


def draw_bars_ch1(ctx, t, a):
    t0 = S("c1_12") + 0.3
    for i, v in enumerate(BAR_V):
        u = ease(clamp01((t - t0 - 0.09 * i) / 0.45))
        if u <= 0.003:
            continue
        h = v * BAR_H * u
        ctx.set_source_rgba(*hexrgb(bar_col(i), 0.95 * a))
        rrect(ctx, BAR_X[i] - 25, BAR_Y0 - h, 50, h, 5)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.move_to(BAR_X[0] - 40, BAR_Y0 + 2)
    ctx.line_to(BAR_X[-1] + 40, BAR_Y0 + 2)
    ctx.stroke()
    la = a * fade(t, t0 + 0.5, 0.3)
    text(ctx, "吉祥寺", BAR_X[0], BAR_Y0 + 38, 36, INK, alpha=la)
    text(ctx, "新宿", BAR_X[6], BAR_Y0 + 38, 36, RED, alpha=la)
    text(ctx, "座れず", BAR_X[10], BAR_Y0 + 38, 36, INK, alpha=la)


def R_ch1(ctx, t):
    tg1 = S("g1")
    a_st = out_fade(t, tg1 - 0.1, 0.35)
    if a_st > 0.003:
        stk(ctx, t, "c1_1", "中央線の快速　高尾 → 東京", 150, "yellow", a=a_st)
        stk(ctx, t, "c1_2", "国土交通省 大都市交通センサス", 226, "blue", a=a_st, tilt=0.012)
        stk(ctx, t, "c1_3", "コンピューターの中で作った電車", 302, "pink", fg=RED, a=a_st)
        stk(ctx, t, "c1_4", "高尾から乗れば ほとんどすぐ座れる", 378, "mint", a=a_st, tilt=0.01)
        stk(ctx, t, "c1_6", "三鷹で乗る　席は全部うまっている", 454, "yellow", a=a_st)
        stk(ctx, t, "c1_7", "赤い人 ＝ あなた（7人がけの前）", 530, "blue", a=a_st, tilt=0.012)
        stk(ctx, t, "c1_8", "立つ場所は 毎回ばらばら", 606, "pink", fg=RED, a=a_st)
        stk(ctx, t, "c1_9", "空いた席には たいてい真ん前の人が座る", 682, "mint", a=a_st, tilt=0.01, size=36)
        stk(ctx, t, "c1_10", "ときどき 隣の前の人が先に座る", 758, "yellow", a=a_st)
    # g1: 1万回のマス目
    a_gr = fade(t, tg1 + 0.1, 0.4) * out_fade(t, S("c1_12") - 0.05, 0.4)
    if a_gr > 0.003:
        text(ctx, "三鷹から東京まで 1万回", RCX, 125, 42, INK, alpha=a_gr)
        legend_sq(ctx, [(BLUE, "座れた"), ("#b9b4a5", "東京まで座れず")], RCX, 166, a=a_gr)
        n = int(N * clamp01((t - tg1 - 0.3) / (dur("g1") - 0.9)) ** 1.25)
        draw_grid1(ctx, a_gr, n)
    # 棒グラフ
    a_bar = fade(t, S("c1_12") + 0.1, 0.4) * out_fade(t, S("c1_19") - 0.1, 0.4)
    if a_bar > 0.003:
        text(ctx, "座れた駅（三鷹から乗る）", RX, 135, 42, INK, align="left", alpha=a_bar)
        draw_bars_ch1(ctx, t, a_bar)
        # 新宿に着く前（かっこ）
        if t >= S("c1_13") + 0.2:
            pg = clamp01((t - S("c1_13") - 0.2) / 0.6)
            ba = fade(t, S("c1_13") + 0.2, 0.3) * out_fade(t, S("c1_15") + 0.2, 0.3)
            pen_line(ctx, BAR_X[0] - 28, BAR_Y0 + 80, BAR_X[5] + 28, BAR_Y0 + 80, RED, seed=61, width=6, progress=pg, alpha=ba)
            text(ctx, "新宿に着く前", (BAR_X[0] + BAR_X[5]) / 2, BAR_Y0 + 126, 36, RED, alpha=ba * clamp01(pg * 2 - 0.6))
        if t >= S("c1_14") + 0.3:
            pen_circle(ctx, BAR_X[6], BAR_Y0 - BAR_V[6] * BAR_H * 0.5, 54, BAR_V[6] * BAR_H * 0.5 + 24, RED, seed=63, width=6,
                       progress=clamp01((t - S("c1_14") - 0.3) / 0.5), alpha=a_bar)
        if t >= S("c1_15") + 0.2:
            text(ctx, "いちばん多い駅", BAR_X[6] - 40, BAR_Y0 - BAR_V[6] * BAR_H - 58, 38, RED, alpha=fade(t, S("c1_15") + 0.2, 0.3))
    if t >= S("c1_19") + 0.4:
        sticky(ctx, "途中の駅で乗っても\n東京までに 約9割", RCX, 330, 52, "pink", fg=RED, a=fade(t, S("c1_19") + 0.4), tilt=-0.015)
    if t >= S("c1_20") + 0.3:
        sticky(ctx, "新宿までに 約6割", RCX, 560, 64, "yellow", fg=RED, a=fade(t, S("c1_20") + 0.3), tilt=0.012)


# ---- 2章 ----
TB_X = [1330.0, 1480.0, 1630.0, 1780.0]
TB_Y = [430.0, 550.0, 670.0]
TB_HEAD_Y = 330.0


def table_alpha(t):
    """表の場面（c2_12c〜c2_12f）の間は、右ページの欄・付せん・マス目を隠す"""
    return fade(t, S("c2_12c") - 0.1, 0.4) * out_fade(t, S("c2_13") - 0.1, 0.4)


def R_table(ctx, t):
    """2章の表: 三鷹から乗った場合の、駅までに座れた割合（その駅で座るのも含む）。左の列から順に埋まる"""
    a = table_alpha(t)
    if a <= 0.003:
        return
    text(ctx, "三鷹から乗った場合", RX, 150, 46, INK, align="left", alpha=a)
    text(ctx, "新宿で座れた分も入れて（その駅までに）", RX, 212, 38, PENCIL_T, align="left", bold=False, alpha=a)
    t_g = S("g2t") + 0.3
    # 東京の列を強調（c2_12f）
    a_c = fade(t, S("c2_12f") + 0.2, 0.4)
    if a_c > 0.003:
        ctx.set_source_rgba(*hexrgb("#fff0a0", 0.6 * a * a_c))
        rrect(ctx, TB_X[3] - 72, TB_HEAD_Y - 40, 144, TB_Y[2] - TB_HEAD_Y + 100, 14)
        ctx.fill()
    for r_, (rn, _j) in enumerate(TBL_ROWS):
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
        ctx.set_line_width(2)
        ctx.move_to(RX - 10, TB_Y[r_] + 60)
        ctx.line_to(1850, TB_Y[r_] + 60)
        ctx.stroke()
        text(ctx, rn, RX, TB_Y[r_], 36, RED if r_ == 0 else INK, align="left", alpha=a * fade(t, t_g - 0.2, 0.3))
    for k, (cn, _st) in enumerate(TBL_COLS):
        tk = t_g + 1.1 * k
        ak = fade(t, tk, 0.35)
        if ak <= 0.003:
            continue
        text(ctx, cn, TB_X[k], TB_HEAD_Y, 36, RED if cn == "新宿" and t >= S("c2_12d") else INK, alpha=a * ak)
        for r_ in range(3):
            ar = fade(t, tk + 0.12 * r_, 0.3)
            text(ctx, f"{TBL_P[r_][k]}%", TB_X[k], TB_Y[r_], 56, INK, alpha=a * ar)
    if t >= S("c2_12d") + 0.4:                                       # 新宿の列の 端の隣の前 に赤丸
        pen_circle(ctx, TB_X[2], TB_Y[1], 80, 46, RED, seed=271, width=6, progress=clamp01((t - S("c2_12d") - 0.4) / 0.5), alpha=a)
    if t >= S("c2_12e") + 0.4:                                       # 端の前 に丸
        pen_circle(ctx, TB_X[2], TB_Y[0], 80, 46, BLUE, seed=272, width=6, progress=clamp01((t - S("c2_12e") - 0.4) / 0.5), alpha=a)
    if t >= S("c2_12f") + 0.5:                                       # 東京の列
        pen_box(ctx, TB_X[3] - 76, TB_HEAD_Y - 44, TB_X[3] + 76, TB_Y[2] + 62, RED, seed=273, progress=clamp01((t - S("c2_12f") - 0.5) / 0.6), alpha=a)


def R_c2(ctx, t):
    tg2 = S("g2")
    a_h = out_fade(t, tg2 - 0.1, 0.35)
    if a_h > 0.003:
        stk(ctx, t, "c2_1", "3か所で比べる（片側だけ）", 150, "yellow", a=a_h)
        for k, nm in enumerate(NAMES3):
            t_k = S("c2_1") + 0.9 + 1.3 * k
            if t >= t_k:
                mini_sticky(ctx, f"{k + 1}　{nm}", RX, 240 + 82 * k, 40, ("pink", "blue", "mint")[k], fg=RED if k == 0 else INK,
                            a=a_h * fade(t, t_k), align="left", tilt=(-0.012, 0.012, -0.008)[k])
        stk(ctx, t, "c2_5", "端の席の人は 長く乗っている？", 530, "yellow", a=a_h)
        stk(ctx, t, "c2_6", "それも あわせて確かめる", 616, "blue", a=a_h, tilt=0.012)
    a_gr = fade(t, tg2 + 0.1, 0.4) * out_fade(t, S("c2_12") - 0.1, 0.4)
    if a_gr > 0.003:
        legend_sq(ctx, [(BLUE, "座れた"), ("#b9b4a5", "座れなかった")], G2X + GW2 / 2, 112, a=a_gr)
        n = int(N * clamp01((t - tg2 - 0.3) / (dur("g2") - 0.9)) ** 1.25)
        for k in range(3):
            text(ctx, f"{k + 1}　{NAMES3[k]}", G2X, G2YS[k] - 44, 38, RED if k == 0 else INK, align="left", alpha=a_gr)
            draw_grid2(ctx, k, a_gr, n)
        segs = {0: [(S("c2_8"), S("c2_9")), (S("c2_10b"), S("c2_11"))], 1: [(S("c2_9"), S("c2_10")), (S("c2_10b"), S("c2_11"))], 2: [(S("c2_9"), S("c2_10"))]}
        for k, lst in segs.items():
            for ts, te in lst:
                if ts <= t < te + 0.2:
                    pen_box(ctx, G2X - 12, G2YS[k] - 10, G2X + GW2 + 12, G2YS[k] + GH2 + 10, RED, seed=140 + 5 * k,
                            progress=clamp01((t - ts - 0.3 - (0.0 if k < 2 else 0.4)) / 0.6), alpha=a_gr * out_fade(t, te, 0.2))
    if S("c2_10b") <= t < S("c2_12"):                                     # 欄の上に「1.5倍」
        a15 = fade(t, S("c2_10b") + 0.3, 0.3) * out_fade(t, S("c2_12") - 0.1, 0.3)
        text(ctx, "端の隣の前は", 1668, 468, 38, INK, alpha=a15)
        text(ctx, "端の前の", 1668, 510, 38, INK, alpha=a15)
        sticky(ctx, f"{SH['RATIO']}倍", 1668, 612, 64, "pink", fg=RED, a=a15, tilt=-0.02)
    a_x = fade(t, S("c2_12") + 0.3, 0.4) * out_fade(t, S("c2_18") - 0.1, 0.4)
    if a_x > 0.003:
        stk(ctx, t, "c2_12", "端の席が空いて\n端の前の人が座らなければ…", 185, "yellow", a=a_x * out_fade(t, S("c2_12c") - 0.1, 0.3), size=38)
        stk(ctx, t, "c2_12", "ねらえるのは\n端の隣の前の人だけ", 315, "pink", fg=RED, a=a_x * fade(t, S("c2_12") + 3.0, 0.3) * out_fade(t, S("c2_12c") - 0.1, 0.3), size=38, off=3.0)
        stk(ctx, t, "c2_14", "端の席の人: 八王子のあたりから", 430, "blue", a=a_x, size=36)
        stk(ctx, t, "c2_14", "真ん中の席の人: 日野のあたりから", 505, "mint", a=a_x, size=36, off=1.6)
        stk(ctx, t, "c2_14", "端のほうが 1駅ほど早くから", 580, "yellow", fg=RED, a=a_x, size=36, off=3.2)
        stk(ctx, t, "c2_16", "端には長く乗る人 → 少しだけ当たり", 655, "pink", a=a_x * out_fade(t, S("c2_17") - 0.1, 0.3), size=36, off=0.2)
        stk(ctx, t, "c2_17", "→ 端の前が座りにくい理由のひとつ", 655, "pink", fg=RED, a=a_x, size=36, off=0.2)
    R_table(ctx, t)
    if t >= S("c2_19") + 0.3:
        sticky(ctx, "立つなら\n端の前より 端の隣の前", RCX, 380, 48, "pink", fg=RED, a=fade(t, S("c2_19") + 0.3), tilt=-0.015)


# ---- 3章 ----
BARS3_X = [1170.0, 1360.0, 1550.0, 1740.0]
BARS3_Y0 = 600.0
BARS3_V = [A7[nm]["p_before_shinjuku"] for nm in ("立川", "三鷹", "吉祥寺", "荻窪")]
BARS3_H = 310.0
BARS3_COL = (BLUE, BLUE_L, "#8a9bb8", "#9aa2b2")


def R_ch3(ctx, t):
    a_h = fade(t, S("ch3") + 0.3, 0.4)
    text(ctx, "新宿に着く前に座れた割合（乗る駅ごと）", RX, 125, 40, INK, align="left", alpha=a_h)
    tg3 = S("g3")
    for k, nm in enumerate(("立川", "三鷹", "吉祥寺", "荻窪")):
        t_k = tg3 + 0.3 + 2.0 * k
        u = ease(clamp01((t - t_k) / 0.7))
        ctx.set_source_rgba(*hexrgb("#ffffff", 0.55 * a_h))
        if u > 0.003:
            h = BARS3_V[k] * BARS3_H * u
            ctx.set_source_rgba(*hexrgb(BARS3_COL[k], 0.95))
            rrect(ctx, BARS3_X[k] - 52, BARS3S_y0(k) - h, 104, h, 6)
            ctx.fill()
            text(ctx, f"{PC(BARS3_V[k])}%", BARS3_X[k], BARS3S_y0(k) - h - 34, 52, RED if k in (0, 3) else INK, alpha=u)
        text(ctx, nm, BARS3_X[k], BARS3_Y0 + 42, 40, INK, alpha=a_h)
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a_h))
    ctx.set_line_width(4)
    ctx.move_to(BARS3_X[0] - 90, BARS3_Y0 + 2)
    ctx.line_to(BARS3_X[-1] + 90, BARS3_Y0 + 2)
    ctx.stroke()
    if t >= S("c3_2") + 0.5:
        pen_circle(ctx, BARS3_X[0], BARS3_Y0 - BARS3_V[0] * BARS3_H * 0.5, 84, BARS3_V[0] * BARS3_H * 0.5 + 54, RED, seed=151, width=6,
                   progress=clamp01((t - S("c3_2") - 0.5) / 0.5), alpha=out_fade(t, S("c3_4"), 0.3))
    if t >= S("c3_3") + 0.4:
        pen_circle(ctx, BARS3_X[3], BARS3_Y0 - BARS3_V[3] * BARS3_H * 0.5 - 14, 84, BARS3_V[3] * BARS3_H * 0.5 + 48, RED, seed=153, width=6,
                   progress=clamp01((t - S("c3_3") - 0.4) / 0.5), alpha=out_fade(t, S("c3_4"), 0.3))
    # 立川と三鷹のあいだに「2倍」
    if t >= S("c3_2c") + 0.3:
        a2 = fade(t, S("c3_2c") + 0.3, 0.3) * out_fade(t, S("c3_6") - 0.2, 0.3)
        text(ctx, f"{SH['R3']}倍", 1318, 372, 64, RED, alpha=a2)
        pg2 = clamp01((t - S("c3_2c") - 0.6) / 0.5)
        pen_line(ctx, 1226, BARS3_Y0 - BARS3_V[0] * BARS3_H, 1300, BARS3_Y0 - BARS3_V[0] * BARS3_H, RED, seed=251, width=5, progress=pg2, alpha=a2)
        arrow_to(ctx, 1268, BARS3_Y0 - BARS3_V[0] * BARS3_H + 4, 1268, BARS3_Y0 - BARS3_V[1] * BARS3_H - 4, RED, progress=pg2, width=6, a=a2)
    a4 = out_fade(t, S("c3_6") - 0.2, 0.3)
    if t >= S("c3_4") + 0.3:
        mini_sticky(ctx, "国分寺や吉祥寺など\n降りる人の多い駅を いくつも通る", RX + 100, 232, 38, "mint", a=a4 * fade(t, S("c3_4") + 0.3), align="left", tilt=-0.012)
    if t >= S("c3_6") + 0.3:
        sticky(ctx, "乗る駅が数駅ちがうだけで\n新宿に着く前に座れる割合は 2倍ほど", RCX, 232, 38, "pink", fg=RED, a=fade(t, S("c3_6") + 0.3), tilt=-0.015)
    if t >= S("c3_7") + 0.3:
        mini_sticky(ctx, "始発に近い駅で乗るほど 座りやすいはず", RX + 40, 332, 36, "yellow", a=fade(t, S("c3_7") + 0.3), align="left", tilt=0.01)


def BARS3S_y0(k):
    return BARS3_Y0


# ---- 4章（まとめ） ----
def R_c4(ctx, t):
    sticky_y = {"c4_1": 175, "c4_2": 272, "c4_3": 357, "c4_4": 442}
    stk(ctx, t, "c4_1", "途中の駅で乗っても\n東京までに 約9割", 175, "yellow", size=40)
    stk(ctx, t, "c4_2", "新宿までに 約6割", 272, "mint", fg=RED, size=40, tilt=0.01)
    stk(ctx, t, "c4_3", "端の前より 端の隣の前", 357, "pink", fg=RED)
    stk(ctx, t, "c4_4", "乗る駅で 2倍ちがう", 442, "blue", fg=RED, tilt=0.012)
    stk(ctx, t, "c4_5", "国の調査の数字をもとに\nコンピューターの中で作った電車", 545, "mint", tilt=0.01)
    stk(ctx, t, "c4_6", "空いた席に誰が座るか など\nこの動画で決めたルール", 645, "yellow", tilt=-0.01)


RIGHTS = [R_ch0, R_ch1, R_c2, R_ch3, R_c4]


# ============================================================
# 右ページ下の欄（最初の答えから終了画面まで出しっぱなし。区切りの4秒だけ消える）
# ============================================================
NB = (1030, 706, 1830, 916)
BOX_DIM = 0.4


def box_keys():
    p = lambda v: f"{v}%"
    K = lambda t, cap, cells, dim=False, circle=None: dict(t=t, cap=cap, cells=cells, dim=dim, circle=circle)
    M = lambda lab, val, col=INK, rev=None: (lab, val, col, rev)
    c1 = "三鷹から東京まで・1万回"
    a1 = M("座れた", p(SH["P_SAT"]), RED)
    c1b = "三鷹から乗って座れた駅"
    b_bef, b_at = M("新宿に着く前", p(SH["P_BEF"]), INK), M("新宿で座れた", p(SH["P_AT"]), RED)
    c2 = "三鷹から・新宿に着く前に座れた"
    e1, e2, e3 = M("端の前", p(SH["E_END"]), RED), M("端の隣の前", p(SH["E_NEXT"]), INK, mid("c2_9", 0.4)), M("真ん中の前", p(SH["E_MID"]), INK, mid("c2_9", 0.8))
    c2b = "新宿かその先まで乗る人"
    o1, o2 = M("端の席の人", p(SH["O_END"]), RED), M("真ん中の席の人", p(SH["O_MID"]), INK)
    c3 = "新宿に着く前に座れた（乗る駅ごと）"
    t1, t2_, t4 = M("立川", p(SH["T_TACH"]), INK), M("三鷹", p(SH["T_MITA"]), INK), M("荻窪", p(SH["T_OGI"]), RED)
    return [
        K(mid("c1_11", 0.6), c1, [a1], circle=0),
        K(mid("c1_13", 0.6), c1b, [b_bef], circle=0),
        K(mid("c1_14", 0.6), c1b, [b_at], circle=0),
        K(S("ch2") + 0.5, c1b, [b_at], dim=True),
        K(mid("c2_8", 0.6), c2, [e1], circle=0),
        K(mid("c2_9", 0.3), c2, [M("端の前", p(SH["E_END"]), INK), e2, e3]),
        K(mid("c2_15", 0.6), c2b, [o1, o2], circle=0),
        K(S("ch3") + 0.5, c2b, [o1, o2], dim=True),
        K(mid("c3_2", 0.6), c3, [M("立川", p(SH["T_TACH"]), RED)], circle=0),
        K(mid("c3_2b", 0.6), c3, [t1, M("三鷹", p(SH["T_MITA"]), RED)], circle=1),
        K(mid("c3_3", 0.6), c3, [t1, t2_, t4], circle=2),
        K(S("ch4") + 0.5, c3, [t1, t2_, t4], dim=True),
    ]

def _cell_xs(n):
    x0, x1 = NB[0], NB[2]
    return [x0 + (x1 - x0) * (i + 0.5) / n for i in range(n)]


def _key_cells(ctx, key, a, t, tk, pop):
    x0, y0, x1, y1 = NB
    n = len(key["cells"])
    for (lab, val, col, rev), cx in zip(key["cells"], _cell_xs(n)):
        ra = 1.0 if rev is None else fade(t, rev, 0.4)
        if ra <= 0.003:
            continue
        text(ctx, lab, cx, y0 + 98, 36, col, alpha=a * ra)
        sc = 1 + (0.25 * (1 - ease_out(clamp01((t - tk) / 0.3))) if pop else 0.0)
        ctx.save()
        ctx.translate(cx, y0 + 162)
        ctx.scale(sc, sc)
        text(ctx, val, 0, 0, 68, col, alpha=a * ra)
        ctx.restore()


def draw_box(ctx, t):
    keys = box_keys()
    t0 = keys[0]["t"]
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3) * (1 - table_alpha(t))
    if a <= 0.003:
        return
    i = max([k for k, kk in enumerate(keys) if kk["t"] <= t + 0.1] or [0])
    cur = keys[i]
    prev = keys[i - 1] if i > 0 else None
    tk = cur["t"]
    u = fade(t, tk, 0.35)
    dimv = lambda k: BOX_DIM if k["dim"] else 1.0
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    ctx.set_line_width(2)
    for kk, vis in ((cur, u), (prev, 1 - u)):
        if kk is None or vis <= 0.01:
            continue
        n = len(kk["cells"])
        if n >= 2:
            for j in range(1, n):
                xx = x0 + (x1 - x0) * j / n
                ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a * (1.0 if kk is cur else vis)))
                ctx.move_to(xx, y0 + 70)
                ctx.line_to(xx, y1 - 18)
                ctx.stroke()
    cy_cap = y0 + 34
    va_a = dimv(cur) * u + (dimv(prev) if prev else 1.0) * (1 - u)
    if prev is None or prev["cap"] == cur["cap"]:
        text(ctx, cur["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * va_a)
    else:
        text(ctx, cur["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * u * dimv(cur))
        text(ctx, prev["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * (1 - u) * dimv(prev))
    same = prev is not None and prev["cells"] == cur["cells"]
    if prev is None or same:
        _key_cells(ctx, cur, a * va_a, t, tk, False)
    else:
        _key_cells(ctx, prev, a * (1 - u) * dimv(prev), t, tk, False)
        _key_cells(ctx, cur, a * u * dimv(cur), t, tk, True)
    if cur["circle"] is not None and not cur["dim"]:
        n = len(cur["cells"])
        cx = _cell_xs(n)[cur["circle"]]
        pen_circle(ctx, cx, y0 + 162, 118 if n == 1 else 100, 44, RED, seed=121, width=6, progress=clamp01((t - tk - 0.3) / 0.5), alpha=a)


# ============================================================
# 章の付箋・1万回の合図・終了画面・全体
# ============================================================
def T_ES():
    """終了画面の始まり（c4_6 を言い終わって 0.3秒後）"""
    return E("c4_6") + 0.3


BANNERS = lambda: [S("c0_5") + 0.1]
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"       # 終了画面の付せん（kaidan-long の最新の形）
LCX_E, RCX_E = 490, 1430                              # 終了画面: 左ページ・右ページの中央


def big_sticky(ctx, label, value, cx, cy, w, h, color, fg=INK, a=1.0, tilt=0.0, lsz=46, vsz=64, sub=None, ssz=38):
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
    if sub:                                           # 小さい添え書きがあるときは3段
        text(ctx, label, 0, -h * 0.31, lsz, INK, alpha=a)
        text(ctx, value, 0, -h * 0.01, vsz, fg, alpha=a)
        text(ctx, sub, 0, h * 0.31, ssz, PENCIL_T, bold=False, alpha=a)
    else:
        text(ctx, label, 0, -h * 0.22, lsz, INK, alpha=a)
        text(ctx, value, 0, h * 0.2, vsz, fg, alpha=a)
    ctx.restore()


def end_screen(ctx, t):
    """終了画面（kaidan-long の最新の形）。左ページ: 答えの付せん（大きく）。右ページ: 問いかけの付せん → 亀＋チャンネル登録の付せん"""
    t0 = T_ES()
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "満員電車の席を、1万回ためしたら", LCX_E, 162, 38, INK, bold=False, alpha=b)
    rows = [("途中の駅で乗っても", "東京までに 約9割", "yellow", INK, -0.010, "新宿までに 約6割"),
            ("立つなら", "端の前より 端の隣の前", "pink", RED, 0.008, None),
            ("新宿に着く前に座れる割合は", "乗る駅で 2倍ちがう", "mint", INK, -0.008, None)]
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt, sub) in enumerate(rows):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=46, vsz=66, sub=sub, ssz=40)
    tq, t9 = S("c4_7") + 0.05, S("c4_8")
    if t >= tq:
        q = fade(t, tq, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
        if q > 0.003:
            sticky(ctx, "あなたは明日から、\nどこに立ちますか？", RCX_E, 480, 68, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, ch[2], a, size=60)
    for tb in BANNERS():
        a = fade(t, tb - 0.1, 0.25) * out_fade(t, tb + 1.5, 0.35)
        if a > 0.003:
            note.banner(ctx, "1万回ためす", lf.GUTTER, 470, a=a, t_rel=t - tb)


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def pages(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    ctx.save()
    clip_left(ctx)
    page(ctx, t, LEFTS, idx, t0)
    ctx.restore()
    page(ctx, t, RIGHTS, idx, t0)
    draw_box(ctx, t)
    overlays(ctx, t)


# ============================================================
# 区切り（アイキャッチ。2章と3章の間・約4秒・声なし）。kaidan-long と同じ形
#   左ページに「ここまで」＋左向きの赤い矢印＋ここまでのまとめ、右ページに「ここから」＋右向きの赤い矢印＋これから確かめること2行。
#   下で亀が左ページから右ページへ歩き、足あとの点が順に出る（点が出るたびに足音）。数字の欄はこの間は出さない
# ============================================================
EYE_LEFT = ("端の前は、", "座りにくい")
EYE_RIGHT = ("乗る駅が違ったら？",)
EYE_LX, EYE_RX = 480, 1440
EYE_Y = 860
EYE_X0, EYE_X1 = 330.0, 1590.0
FOOT_X0, FOOT_DX, FOOT_BEHIND = 260.0, 64.0, 70.0


def EYE0():
    return S("eye")


def EYE1():
    return E("eye")                                  # ＝ 3章の始まり


def eye_alpha(t):
    return fade(t, EYE0(), 0.3) * out_fade(t, EYE1(), 0.35)


def eye_x(t):
    return lerp(EYE_X0, EYE_X1, clamp01((t - EYE0()) / (EYE1() - EYE0())))


def foot_times():
    out = []
    i = 0
    while True:
        px = FOOT_X0 + i * FOOT_DX
        u = (px + FOOT_BEHIND - EYE_X0) / (EYE_X1 - EYE_X0)
        if u > 1.0:
            break
        out.append((px, EYE0() + max(0.0, u) * (EYE1() - EYE0())))
        i += 1
    return out


def eye_arrow(ctx, x0, x1, y, color, seed, progress):
    pen_line(ctx, x0, y, x1, y, color, seed=seed, width=7, progress=progress)
    if progress >= 1:
        d = 1 if x1 > x0 else -1
        pen_line(ctx, x1, y, x1 - d * 34, y - 24, color, seed=seed + 1, width=7)
        pen_line(ctx, x1, y, x1 - d * 34, y + 24, color, seed=seed + 2, width=7)


def eye_page(ctx, t, cx, head, lines, back):
    a = fade(t, EYE0(), 0.5)
    w = text_width(head, 104)
    hand_title(ctx, head, cx - w / 2, 250, 104, seed=4 if back else 6, alpha=a)
    pr = clamp01((t - EYE0() - 0.1) / 0.4)
    if back:
        eye_arrow(ctx, cx + 210, cx - 230, 345, RED, 11, pr)
    else:
        eye_arrow(ctx, cx - 210, cx + 230, 345, RED, 21, pr)
    for i, s_ in enumerate(lines):
        text(ctx, s_, cx, 520 + i * 96, min(66, int(66 * 820 / text_width(s_, 66))), INK, alpha=a)


def eyecatch(ctx, t):
    from engine.brand import turtle
    lf.spread(ctx)
    eye_page(ctx, t, EYE_LX, "ここまで", EYE_LEFT, True)
    eye_page(ctx, t, EYE_RX, "ここから", EYE_RIGHT, False)
    for i, (px, tf) in enumerate(foot_times()):
        if t >= tf:
            ctx.set_source_rgba(0.25, 0.25, 0.3, 0.30 * fade(t, tf, 0.12))
            ctx.arc(px, EYE_Y + 18 + (7 if i % 2 else -7), 6, 0, 2 * math.pi)
            ctx.fill()
    blink = 1.0 if 0.35 < (t - EYE0()) % 1.8 < 0.47 else 0.0
    turtle(ctx, eye_x(t), EYE_Y - 3 * abs(math.sin((t - EYE0()) * 6.0)), 0.5, blink=blink)


def draw(ctx, t):
    lf.spread(ctx)
    tes = T_ES()
    ea = eye_alpha(t)
    if t < tes + 0.6 and ea < 0.997:
        grp(ctx, 1 - fade(t, tes, 0.5), pages, t)
    if t >= tes:
        end_screen(ctx, t)
    grp(ctx, ea, eyecatch, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。足音・効果音は kaidan-long と同じ作り方）
# ============================================================
def turtle_step(seed=0, high=False):
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
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 5):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for k, kk in enumerate(box_keys()):
        if k > 0 and not kk["dim"]:
            mx.add(kk["t"], bell(659.3 if k % 2 else 784.0, 1.0), 0.3)
    for tb in BANNERS():
        mx.add(tb - 0.4, riser(0.9), 0.45)
    for g in ("g0", "g1", "g2", "g3"):
        beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
        mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
    for cid in ("c1_18", "c2_18", "c3_5"):
        mx.add(S(cid) + 0.4, chord([392.0, 493.9, 587.3], 1.2), 0.3)
    mx.add(S("c4_7") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    for i, (_px, tf) in enumerate(foot_times()):
        mx.add(tf, turtle_step(seed=i, high=bool(i % 2)), 0.32)
    _i0, _i1 = int(EYE0() * core.SR), int(EYE1() * core.SR)
    _r = int(0.3 * core.SR)
    _g = np.ones(len(mx.bgm_buf))
    _g[_i0:_i1] = 0.55
    _g[max(0, _i0 - _r):_i0] = np.linspace(1, 0.55, _i0 - max(0, _i0 - _r))
    _g[_i1:_i1 + _r] = np.linspace(0.55, 1, len(_g[_i1:_i1 + _r]))
    mx.bgm_buf *= _g
    mx.add(S("c4_8") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻（--fake-voice の時刻で。6枚）
# ============================================================
STILL_NAMES = ["① 冒頭: 7人がけの席と「あなた」・端と真ん中の矢印", "② 1章の頭: 路線の図（高尾 → 東京・24駅）", "③ 1章の答え: 座れた駅の棒グラフ（新宿に赤丸）",
               "④ 2章: 3か所の前に立つ人とマス目・欄", "⑤ 3章: 乗る駅ごとの棒グラフ", "⑥ まとめ: 終了画面（答えの付せん・亀と登録の付せん）"]


def still_times6():
    return [mid("c0_1", 0.97), E("c1_1") + 0.1, mid("c1_15", 0.97), mid("c2_15", 0.97), mid("c3_2c", 0.97), S("c4_8") + 2.0, mid("c0b_5", 0.97), mid("c2_12f", 0.97), mid("c2_14", 0.9), mid("c2_12x2", 0.95)]


def still_times():
    ts = list(still_times6())
    ts += [0.6, mid("c0_1", 0.3), S("g0") + 4.0, S("g0") + 8.0, E("g0") - 0.3, mid("c0_4", 0.9), mid("c0_6", 0.95),
           S("ch1") + 0.8, mid("c1_3", 0.9), mid("c1_4", 0.95), mid("c1_5", 0.9), mid("c1_6", 0.95), mid("c1_7", 0.95), mid("c1_8", 0.5),
           mid("c1_9", 0.95), mid("c1_10", 0.95), S("g1") + 2.0, S("g1") + 5.0, S("g1") + 8.0, E("g1") - 0.3, mid("c1_11", 0.95), mid("c1_13", 0.95),
           mid("c1_14", 0.95), mid("c1_19", 0.95),
           S("ch2") + 0.8, mid("c2_1", 0.95), mid("c2_2", 0.95), mid("c2_3", 0.95), mid("c2_5", 0.95), S("g2") + 3.0, E("g2") - 0.3, mid("c2_8", 0.95),
           mid("c2_12", 0.95), mid("c2_14", 0.95), mid("c2_15", 0.95), mid("c2_19", 0.95),
           EYE0() + 0.6, EYE0() + 2.0, EYE1() - 0.3,
           S("ch3") + 0.8, mid("c3_1", 0.95), S("g3") + 3.0, mid("c3_2", 0.95), mid("c3_3", 0.95), mid("c3_5", 0.95), mid("c3_7", 0.95),
           S("ch4") + 0.8, mid("c4_1", 0.95), mid("c4_2", 0.95), mid("c4_3", 0.95), mid("c4_4", 0.95), mid("c4_6", 0.95),
           T_ES() + 1.0, mid("c4_7", 0.9), DUR - 0.1]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


# ============================================================
# 文字起こし・読み・画面の文字
# ============================================================
def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_keep(draw_, times, out_dir, cols=4, thumb=(480, 270)):
    """静止画と sheet.png。前の still_*.png を消さない（このプロジェクトは削除しない決まり）"""
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for tt in times:
        pth = out_dir / f"still_{tt:06.1f}.png"
        lf.still(draw_, tt, pth)
        paths.append(pth)
    ims = [Image.open(q).convert("RGB").resize(thumb, Image.LANCZOS) for q in paths]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (thumb[0] + 8), (i // cols) * (thumb[1] + 8)))
    sheet.save(out_dir / "sheet.png")
    print("一覧:", out_dir / "sheet.png")


GAP_NOTE = {
    "g0": "三鷹乗り・早回し（見本 open: あなた＝端の隣の前・もう一人＝端の前。席が空くたびに前の人が座る。あなたが先に座る）",
    "g1": "三鷹から東京まで・早回し（見本 ch1: 席4の前。席が空くたびに前の人が座る）。右ページで1万回のマス目が埋まる",
    "g2": "3か所（端の前・端の隣の前・真ん中の前）1万回ずつ: 右ページに3つのマス目が埋まる。左ページは3人が立っている",
    "g3": "乗る駅を 立川→三鷹→吉祥寺→荻窪 と東京に近づける。右ページに棒が1本ずつ立つ（新宿に着く前に座れた割合）",
}


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字「満員電車の空席」と問い）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            if it.id == "eye":
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・区切り。左「ここまで ← {''.join(EYE_LEFT)}」・"
                            f"右「ここから → {''.join(EYE_RIGHT)}」。亀が左ページから右ページへ歩く・足音。章ではない）")
            elif it.id in GAP_NOTE:
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE[it.id]}）")
            else:
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・映像だけ）")
        else:
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}")
    rows.append("")
    rows.append(f"{_ts(T_ES())}〜{_ts(DUR)} 終了画面の区間（左ページに答えの付せん・右ページに問いかけ、亀と「チャンネル登録よろしく」）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            rows.append(f"{it.id}: {shown_}\n    → {voice.read_aloud(spoken)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


def scan(step=0.25, scale=0.25):
    """0.25秒ごとに描いて、画面の文字（字幕を除く）の位置と、描いた人の数・人の位置を集める"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int(DUR / step)
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        DRAWN[0] = 0
        PEOPLE_LOG.clear()
        CIRCLE_LOG.clear()
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale, e[6] / scale) for e in core._LOG]
        frames.append((t, ents, DRAWN[0], [tuple(p) for p in PEOPLE_LOG]))
        CLOG_BY_T[t] = list(CIRCLE_LOG)
        core._LOG = None
    return frames


def write_screen_text(path, frames, step=0.25):
    seen = {}
    for t, ents, *_r in frames:
        for e in ents:
            seen.setdefault(e[0], []).append(t)
    spans = []
    for s_, ts in seen.items():
        a = b = ts[0]
        for x in ts[1:] + [1e9]:
            if x - b > step * 1.5:
                spans.append((a, b + step, s_))
                a = x
            b = x
    spans.sort()
    rows = ["# 画面の文字（字幕を除く）と、見えている区間。0.25秒ごとに描いて調べた", ""]
    for a, b, s_ in spans:
        mark = "  ←短い" if b - a < 1.5 and not any(ch.isdigit() for ch in s_) else ""
        rows.append(f"{_ts(a)}〜{_ts(b)}（{b - a:4.1f}秒） {s_}{mark}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("画面の文字:", path)


OVERLAY_OK = set(CH_TITLES) | {"1万回ためす"}


def overlaps(frames, step=0.25, need=3, shrink=3.0):
    """文字どうしの重なり（同じ2つの文字が need 回続けて＝0.5秒以上重なったら）"""
    runs, bad = {}, {}
    for t, ents, *_r in frames:
        boxes = [(s_, x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink) for s_, x0, y0, x1, y1, *_q in ents if s_ not in OVERLAY_OK]
        hit = set()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] == b[0]:
                    continue
                w_ = min(a[3], b[3]) - max(a[1], b[1])
                h_ = min(a[4], b[4]) - max(a[2], b[2])
                if w_ > 0 and h_ > 0:
                    area = min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2]))
                    if w_ * h_ > 0.08 * area:
                        hit.add(tuple(sorted((a[0], b[0]))))
        for k in list(runs):
            if k not in hit:
                runs.pop(k)
        for k in hit:
            runs[k] = runs.get(k, 0) + 1
            if runs[k] >= need and k not in bad:
                bad[k] = t
    return bad


# ============================================================
# 場面の照合（見本の記録・声の数字・画面の数字・人の大きさと重なり・早回し・文字の重なり・字幕・終了画面・長さ）
# ============================================================
def other_sits(rec):
    """記録の中で、あなた以外の人が「立つ → 座る」になった回数"""
    fr, n = rec["frames"], 0
    for a, b in zip(fr, fr[1:]):
        for pid in a["stand"]:
            if pid > 0 and pid in b["seat"]:
                n += 1
    return n


def rec_bad_frames(rec):
    bad = 0
    for f in rec["frames"]:
        ids = [p for p in f["seat"] + f["stand"] if p >= 0]
        if len(ids) != len(set(ids)) or len(f["seat"]) != NSEATS or len(f["stand"]) != NSEATS:
            bad += 1
    return bad


def person_boxes(frames):
    """人の大きさと重なりの検査。(コマ数, 重なったコマ, 小さい人, はみ出した人)"""
    n_ov, small, out_of = 0, 0, 0
    starts = [c[0] for c in tl.chapters]
    for t, _ents, _n, plog in frames:
        if t >= T_ES() or EYE0() <= t < EYE1() + 0.2 or any(0 <= t - c0 < 0.4 for c0 in starts):     # 章のはじめの 0.35秒は前のページとの重ね（クロスフェード）
            continue
        vis = [p for p in plog if p[5] >= 0.5]
        hit = False
        for i in range(len(vis)):
            for j in range(i + 1, len(vis)):
                a, b = vis[i], vis[j]
                w_ = min(a[3], b[3]) - max(a[1], b[1])
                h_ = min(a[4], b[4]) - max(a[2], b[2])
                if w_ > 1.0 and h_ > 1.0:
                    hit = True
        n_ov += int(hit)
        for kind, x0, y0, x1, y1, al, k_ in plog:
            if al >= 0.99:
                if (kind == "sit" and (y1 - y0) / k_ < 200) or (kind == "stand" and (y1 - y0) / k_ < 250) or k_ < 0.75:
                    small += 1
            if al >= 0.5 and (x0 < 44 or x1 > 941 or y1 > 936 or y0 < 262):
                out_of += 1
    return n_ov, small, out_of


def scene_checks(frames=None):
    txt = lambda i: tl.clip(i).text
    M = get_model()
    sm_o, sm_1 = SM["open"], SM["ch1"]
    ro, r1 = sm_o["rec"], sm_1["rec"]
    A_ = M.A
    checks = [
        # ---- 見本（1回ぶんの記録）----
        ("見本の記録: trial_rec は trial と同じ seed で結果（座った駅・席の人の乗った駅と降りる駅）が1回も違わない（4条件×40回）",
         float(rec_equal_check(M, [(12, 1, A_MAIN, 23, 0.0), (12, 3, A_MAIN, 19, 0.2), (12, 3, A_MAIN, 23, 0.0), (5, 0, A_MAIN, 23, 0.0)], 40)), 0, 0),
        ("見本の記録: 2つの見本とも どの駅のコマも 人が重複せず・席7・立ち位置7", float(rec_bad_frames(ro) + rec_bad_frames(r1)), 0, 0),
        ("見本 open（冒頭）: 三鷹乗り・席2の前のあなた（番号0）・席1の前に もう一人（番号12）。あなたが先に座る（もう一人はそのときまだ立っている）",
         float(sm_o["code"] == FULL and ro["frames"][12]["stand"][1] == 0 and ro["frames"][12]["stand"][0] == 12 and 12 in ro["frames"][-1]["stand"]
               and ro["frames"][-1]["kind"] == "sit" and 2 <= sm_o["sat"] - 12 <= 6), 1, 0),
        ("見本 open: 座った瞬間に空いている席がない（あなたが座った席以外は全部うまっている）", float(-1 not in ro["frames"][-1]["seat"]), 1, 0),
        ("見本 ch1（1章・早回し）: 三鷹乗り・席4の前・新宿（駅19）で座る・ほかの人が3回以上座る・座った瞬間に空き席なし",
         float(sm_1["code"] == FULL and sm_1["sat"] == E_SHINJUKU and r1["frames"][12]["stand"][3] == 0 and other_sits(r1) >= 3 and -1 not in r1["frames"][-1]["seat"]), 1, 0),
        ("見本 ch1: 高尾（コマ0）に空いた席がある（c1_4 で あなたが座る席）。data.json: 高尾で乗って座れた割合 99%超", float(len(FIRST_FREE0) >= 2 and BS["高尾"]["p_free_at_boarding"] > 0.99), 1, 0),
        # ---- マス目 = data.json（同じ乱数） ----
        ("1・2章のマス目: 三鷹・席1〜4の前の1万回（run_cell と同じ seed）の座れた割合 ＝ data.json（東京まで・4つとも）",
         max(abs(float(np.mean(CELL_SITS[j] >= 0)) - CELLS[_ck(j)]["tokyo"]["p_sat"]) for j in range(4)), 0.0, 1e-12),
        ("2章のマス目: 新宿に着く前に座れた割合 ＝ data.json（端の前・端の隣の前・真ん中の前）",
         max(abs(float(np.mean(SAT_NEXT[k])) - CELLS[_ck(j)]["shinjuku"]["p_sat"]) for k, j in enumerate((0, 1, 3))), 0.0, 1e-12),
        ("1章のマス目: 7か所の重みで並べた1万回の座れた割合 ＝ data.json avg7.p_sat（±1%）・マスは1万個", float(np.mean(SAT_AVG)), A7["三鷹"]["p_sat"], 0.01),
        ("1章のマス目は 1万個（100×100）・2章は3つとも 1万個（200×50）", float(len(SAT_AVG) == N == RES["meta"]["n"] == 10000 and all(len(x) == N for x in SAT_NEXT)), 1, 0),
        # ---- 声・画面の数字 = data.json ----
        ("1章「およそ9割」・欄「90%」＝ 三鷹 avg7.p_sat（0.905）の四捨五入", float(SH["P_SAT9"] == 9 and SH["P_SAT"] == 90 and 0.85 <= A7["三鷹"]["p_sat"] < 0.95), 1, 0),
        ("1章「新宿に着く前に3割ほど」「新宿で3割ほど」・欄「29%」「29%」＝ p_before_shinjuku・p_at_shinjuku の四捨五入",
         float(SH["P_BEF3"] == 3 and SH["P_AT3"] == 3 and SH["P_BEF"] == 29 and SH["P_AT"] == 29), 1, 0),
        ("1章「1つの駅で見ると、新宿がいちばん多い駅」: 座れた駅の分布（三鷹・avg7）の最頻は新宿（駅19）・2位との差 ＞ 3ポイント・棒グラフの赤い棒 ＝ 新宿",
         float(SHINJUKU_TOP_STATION == 19 and sorted(PMF_MITAKA)[-1] - sorted(PMF_MITAKA)[-2] > 0.03 and BAR_ST[6] == 19), 1, 0),
        ("1章「新宿では、座っている人がたくさん降りる」: 新宿の降車（駅別発着表・上り）が24駅のうちいちばん多い・手前の6駅（吉祥寺〜中野）の平均の2割未満",
         float(max(range(24), key=lambda i: A_[i]) == 19 and np.mean(A_[13:19]) < 0.2 * A_[19]), 1, 0),
        ("1章「三鷹で乗ると席はもう全部うまっている」: 三鷹の p_full ＝ 1.0", float(BS["三鷹"]["p_full"] > 0.999), 1, 0),
        ("1章「席は、八王子や立川のあたりでうまっていく」: 区画の人数（駅を出るとき）が席7を超えるのは 八王子〜立川の間の駅",
         float(2 <= min(i for i, v in enumerate(RES["load"]["compartment_load_after"]) if v >= 7) <= 5), 1, 0),
        ("2章「端の前は2割ちょっと」「端の隣の前・真ん中の前は3割ほど」・欄 23%・34%・31% ＝ cells shinjuku.p_sat の四捨五入",
         float(0.20 <= C_END["shinjuku"]["p_sat"] < 0.25 and 0.28 <= C_NEXT["shinjuku"]["p_sat"] < 0.36 and 0.28 <= C_MID["shinjuku"]["p_sat"] < 0.36
               and (SH["E_END"], SH["E_NEXT"], SH["E_MID"]) == (23, 34, 31) and (SH["E_END2"], SH["E_NEXT3"], SH["E_MID3"]) == (2, 3, 3)), 1, 0),
        ("2章「端の前は いちばん座りにくい」「端の隣の前は真ん中の前より ほんの少しだけ座りやすい」: 端 ＜ 真ん中 ＜ 端の隣（隣と真ん中の差は5ポイント未満）",
         float(C_END["shinjuku"]["p_sat"] < C_MID["shinjuku"]["p_sat"] < C_NEXT["shinjuku"]["p_sat"] and C_NEXT["shinjuku"]["p_sat"] - C_MID["shinjuku"]["p_sat"] < 0.05), 1, 0),
        ("2章「端の席の人は、真ん中の席の人より高尾に近い駅から乗っていた」: 乗った駅の平均 端 2.78（八王子〜豊田）＜ 真ん中 4.00（日野）。札「八王子のあたり」「日野のあたり」",
         float(2.0 <= SEAT_STATS["端(席1・7)"]["mean_origin"] <= 3.2 and 3.6 <= SEAT_STATS["真ん中(席4)"]["mean_origin"] <= 4.4), 1, 0),
        ("2章「新宿かその先まで乗る人も、端の席のほうが少し多い」・欄 72%・68%: 端 ＞ 真ん中（差は10ポイント未満）",
         float(SH["O_END"] == 72 and SH["O_MID"] == 68 and 0 < SEAT_STATS["端(席1・7)"]["p_dest_ge_shinjuku"] - SEAT_STATS["真ん中(席4)"]["p_dest_ge_shinjuku"] < 0.10), 1, 0),
        ("3章「立川で乗ると半分を超えた」「荻窪で乗ると1割ほど」・欄 55%・12%: 立川 ＞ 50%・荻窪 5〜15%",
         float(A7["立川"]["p_before_shinjuku"] > 0.5 and 0.05 <= A7["荻窪"]["p_before_shinjuku"] < 0.15 and SH["T_TACH"] == 55 and SH["T_OGI"] == 12 and SH["T_OGI1"] == 1), 1, 0),
        ("3章「東京に近い駅で乗るほど、新宿までは座りにくい」: 立川 ＞ 三鷹 ＞ 吉祥寺 ＞ 荻窪（新宿の手前で座る割合）・「座れる駅は新宿やその先に移る」: 新宿以降で座る割合は反対にふえる",
         float(BARS3_V[0] > BARS3_V[1] > BARS3_V[2] > BARS3_V[3]
               and all(A7[a]["p_at_shinjuku"] + A7[a]["p_after_shinjuku"] < A7[b]["p_at_shinjuku"] + A7[b]["p_after_shinjuku"] for a, b in (("立川", "三鷹"), ("三鷹", "吉祥寺"), ("吉祥寺", "荻窪")))), 1, 0),
        ("1章まとめ「途中の駅で乗っても東京までにおよそ9割」: 立川〜中野の14の駅で乗っても 東京までに座れる割合は 8割5分以上（三鷹 0.905）",
         float(all(BS[M.names[B]]["avg7"]["p_sat"] >= 0.85 for B in range(5, 19)) and SH["P_SAT9"] == 9), 1, 0),
        ("1章まとめ「6割ほどは、新宿までに座れます」・付せん「新宿までに 約6割」＝ 新宿に着く前 0.295 ＋ 新宿で 0.288 ＝ 0.583（0.55〜0.65）",
         float(SH["SIX"] == 6 and 0.55 <= A7["三鷹"]["p_before_shinjuku"] + A7["三鷹"]["p_at_shinjuku"] < 0.65), 1, 0),
        ("2章「端の席の人は、真ん中の席の人より、1駅ほど早くから乗っていた」: 乗った駅の平均の差 ＝ 4.00 − 2.78 ＝ 1.2（0.8〜1.6）",
         float(SH["EARLY"] == 1 and 0.8 <= SEAT_STATS["真ん中(席4)"]["mean_origin"] - SEAT_STATS["端(席1・7)"]["mean_origin"] < 1.6), 1, 0),
        ("3章「三鷹で乗ると3割ほど」「立川と三鷹では2倍ほど」: 三鷹 0.295（3割）・立川 ÷ 三鷹 ＝ 1.85（1.7〜2.3）・棒のあいだの「2倍」",
         float(SH["P_BEF3"] == 3 and SH["R3"] == 2 and 1.7 <= A7["立川"]["p_before_shinjuku"] / A7["三鷹"]["p_before_shinjuku"] < 2.3), 1, 0),
        ("3章「立川で乗ると、新宿までに、国分寺や吉祥寺など降りる人の多い駅をいくつも通る」: 立川〜新宿の手前（国立〜中野）の降車で、国分寺・吉祥寺が上位4駅に入る",
         float({8, 13} <= set(sorted(range(6, 19), key=lambda i: -A_[i])[:4])), 1, 0),
        ("「7人がけ」＝ モデルの席の数（NSEAT=7）・絵の席の数 ＝ 7・立つ位置 ＝ 7", float(NSEAT == 7 == NSEATS == len(SEAT_CX)), 1, 0),
        ("あなたの立つ席: 3か所（端・端の隣・真ん中）＝ 席1・席2・席4（モデルの POS の 0・1・3）", float(SLOTS3 == (0, 1, 3) and POS == (0, 1, 2, 3)), 1, 0),
    ]
    # ---- 中央線の紹介（0b）----
    mx_i = max(INTRO_V)
    ratios = [math.pi * r * r / v for r, v in zip(INTRO_R, INTRO_V)]
    bratio = [b / v for b, v in zip(INTRO_BAR, INTRO_V)]
    ring_lon = [p[0] for p in RING]
    ring_lat = [p[1] for p in RING]
    allring = max(_TK["rings"]["Tokyo"], key=len)
    cen = lambda nm: (sum(p[0] for p in max(_TK["rings"][nm], key=len)) / len(max(_TK["rings"][nm], key=len)),
                      sum(p[1] for p in max(_TK["rings"][nm], key=len)) / len(max(_TK["rings"][nm], key=len)))
    tk_c = (sum(ring_lon) / len(ring_lon), sum(ring_lat) / len(ring_lat))

    def inside(pt, poly):
        x, y, c = pt[0], pt[1], False
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c

    checks += [
        ("0b 丸: 面積（π r²）÷ 人数（CSV の up_board＋up_alight）が11駅すべて同じ（面積が人数に比例）", (max(ratios) - min(ratios)) / ratios[0], 0.0, 1e-9),
        ("0b 横棒: 長さ ÷ 人数 が11駅すべて同じ（長さが人数に比例）", (max(bratio) - min(bratio)) / bratio[0], 0.0, 1e-9),
        ("0b 丸: 11駅の人数は chuo_kaisoku_up_24.csv の値（新宿 375,845）・新宿が最大・2位の1.5倍以上の面積",
         float(INTRO_V[8] == 375845 == mx_i and INTRO_V[8] >= 1.5 * sorted(INTRO_V)[-2]), 1, 0),
        (f"0b 丸: 最大（新宿）{INTRO_R[8]:.0f}px（75〜90px）・最小 {min(INTRO_R):.0f}px（10px以上）・新宿と2位の半径の比 {INTRO_R[8] / sorted(INTRO_R)[-2]:.2f}（1.3以上）",
         float(75 <= INTRO_R[8] <= 90 and min(INTRO_R) >= INTRO_R_FLOOR and INTRO_R[8] / sorted(INTRO_R)[-2] >= 1.3), 1, 0),
        ("0b 紹介: 立川は2位・吉祥寺は11駅の上位半分", float(INTRO_V[2] == sorted(INTRO_V)[-2] and INTRO_V[5] >= sorted(INTRO_V)[len(INTRO_V) // 2]), 1, 0),
        ("0b 駅の座標: 11駅とも stations_latlon.csv（Wikidata・CC0）の値で、すべて 東京都の輪郭の中（点が多角形の内側）",
         float(len(INTRO_ST) == 11 and all(inside((lo, la), RING) for _n, _o, lo, la in INTRO_ST)), 1, 0),
        ("0b 駅の並び: 経度が 高尾（西）＜ … ＜ 東京（東）の順・高尾が最も西・東京が最も東",
         float([n_ for n_, *_r in INTRO_ST] == INTRO_NAMES and all(INTRO_ST[i][2] < INTRO_ST[i + 1][2] for i in range(10))
               and min(INTRO_ST, key=lambda r_: r_[2])[0] == "高尾" and max(INTRO_ST, key=lambda r_: r_[2])[0] == "東京"), 1, 0),
        ("0b 輪郭: Natural Earth 10m admin-1 の東京都の本土側（最大の輪・104点）・西端は奥多摩（経度138.9）・東端は東京湾（139.9）・南端 35.49度（羽田のあたり）・北端 35.88度",
         float(len(RING) == len(allring) - (1 if allring[0] == allring[-1] else 0) and 138.9 < min(ring_lon) < 138.95 and 139.85 < max(ring_lon) < 139.92
               and 35.47 < min(ring_lat) < 35.52 and 35.85 < max(ring_lat) < 35.9), 1, 0),
        ("0b 輪郭の向き: 神奈川の中心は東京の南西・埼玉は北・山梨は西（データから）・東京湾側（東端の点）は東京の中心より南",
         float(cen("Kanagawa")[0] < tk_c[0] and cen("Kanagawa")[1] < tk_c[1] and cen("Saitama")[1] > tk_c[1] and cen("Yamanashi")[0] < tk_c[0]
               and max(RING, key=lambda p: p[0])[1] < tk_c[1] + 0.05), 1, 0),
        (f"0b 手書き風のゆれは 頂点から 0.003度（約300m・全体の幅の0.3%）以内（実際の形から外れない）: {MAP_DEV:.5f}度", float(MAP_DEV <= 0.003), 1, 0),
        ("0b 紹介は0章の中（1章の章カードの前）・章は5つのまま", float(E("c0b_5") <= S("ch1") and S("c0b_0") >= E("c0_6b") and len(tl.chapters) == 5), 1, 0),
        ("0b 紹介の20〜30秒（声の部分）", E("c0b_5") - S("c0b_0"), 25.0, 7.0),
    ]
    # ---- 結論の言い直し（2026-10-21）----
    mode_ok = all(max(range(24), key=lambda i: BS[M.names[B]]["pmf_station_avg7"][i]) == 19 == max(range(B + 1, 24), key=lambda i: A_[i]) for B in range(5, 19))
    checks += [
        ("1章・5章「途中の駅で乗ると、座れる駅でいちばん多いのは、降りる人がいちばん多い大きな乗り換え駅」: 立川〜中野の14の駅で乗ると、座れる駅の最頻 ＝ 乗った駅より先で降りる人がいちばん多い駅 ＝ 新宿（駅19）",
         float(mode_ok), 1, 0),
        ("「中央線なら新宿」: 新宿の降車（上り）は24駅でいちばん多い・駅19が新宿", float(max(range(24), key=lambda i: A_[i]) == 19 and M.names[19] == "新宿"), 1, 0),
        ("2章「端の隣の前で座れた回は、端の前の、およそ1.5倍」・欄の上「1.5倍」＝ 0.342 ÷ 0.228（1.45〜1.55）・声「1.5倍」は1つ",
         float(1.45 <= C_NEXT["shinjuku"]["p_sat"] / C_END["shinjuku"]["p_sat"] < 1.55 and SH["RATIO"] == 1.5), 1, 0),
        ("2章・4章「立つなら、端の前より、端の隣の前」: 新宿に着く前に座れた割合 端の隣の前 ＞ 端の前", float(C_NEXT["shinjuku"]["p_sat"] > C_END["shinjuku"]["p_sat"]), 1, 0),
        ("1章の欄は「新宿で座れた 29%」の1つだけ（同じ数字を2つ並べない）: 欄の数字の組", float(all(len(set(c[1] for c in kk["cells"])) == len(kk["cells"]) for kk in box_keys())), 1, 0),
    ]
    # ---- 字幕の折り返し: 言葉の途中で切れていない ----
    WORDS = ["座りにくい", "座りやすい", "座れる", "座れた", "座れます", "降りそう", "降りる", "立っている", "乗っている", "いちばん", "コンピューター",
             "シミュレーション", "チャンネル", "新宿", "吉祥寺", "国分寺", "荻窪", "立川", "三鷹", "八王子", "日野", "東京", "中央線", "ドアの前", "端の隣の前",
             "真ん中の前", "ねらえる", "ちがいます", "超えます", "超えて", "確かめ", "見ていき", "なんとなく", "やっぱり", "数字にする", "思っていた", "割合",
             "という", "ことも", "ありますよね", "思います", "紹介", "ください", "ほとんど"]
    bad_wrap = []
    for it in tl.items:
        if isinstance(it, lf.Line):
            br = lf.wrap_subtitle(txt(it.id))
            full = "".join(br)
            cuts, pos_ = [], 0
            for ln_ in br[:-1]:
                pos_ += len(ln_)
                cuts.append(pos_)
            for c_ in cuts:
                for w_ in WORDS:
                    st_ = full.find(w_)
                    while st_ >= 0:
                        if st_ < c_ < st_ + len(w_):
                            bad_wrap.append(f"{it.id}: 「{full[:c_]}／{full[c_:]}」（{w_}）")
                        st_ = full.find(w_, st_ + 1)
    for b_ in bad_wrap[:10]:
        print("  言葉の途中の改行:", b_)
    checks.append((f"字幕の折り返し: どの文も 言葉の途中（座りにくい・座りやすい・駅名・「ドアの前」など {len(WORDS)}語）で改行していない: {len(bad_wrap)}件", float(not bad_wrap), 1, 0))
    # ---- ドアの前に立つ人 ----
    rd = door_k(mid("c2_12x2", 0.9))
    checks += [
        ("ドアの前の人: 台本の3文（c2_12x1〜x3）は c2_12 のあと・c2_12b のまえ。ドアの場面だけ車内を0.8倍に縮める（人の高さ 立つ 210px・座る 172px。縮めても 0.75倍より小さくしない）",
         float(E("c2_12") <= S("c2_12x1") < S("c2_12x2") < S("c2_12x3") <= S("c2_12b") and abs(rd - 0.8) < 1e-6 and door_k(S("c2_12") + 0.1) == 1.0), 1, 0),
        ("ドアの前の人: ドアの前（車内の外側・席1の中心より左）に立つ。モデルの決めごと＝ドアの前の人は 端の席の候補に入らない（trial の席の候補は 前の7か所の立ち位置の人だけ）",
         float(DOOR_X < BAY_X0 and DOOR_X < SEAT_CX[0] - 118 and NSEATS == 7), 1, 0),
    ]
    # ---- 2章の表（三鷹から乗った場合）----
    exp_tbl = [[7, 23, 50, 86], [11, 34, 65, 93], [8, 31, 59, 92]]
    indep = [[PC(sum(RES["cells"][f"main|od|f0.1296|B12|j{j}|a0.6|q0.0|E23"]["tokyo"]["pmf_station"][:st + 1])) for _n, st in TBL_COLS] for j in (1, 2, 4)]
    checks += [
        ("2章の表: 12個の値 ＝ data.json（cells main|od|f0.1296|B12|j1/j2/j4|a0.6|q0.0|E23 の tokyo.pmf_station を 吉祥寺・中野・新宿・東京の駅番号まで足し、四捨五入）。見込み 端の前 7・23・50・86／端の隣の前 11・34・65・93／真ん中の前 8・31・59・92",
         float(TBL_P == indep == exp_tbl), 1, 0),
        ("2章の表: 中野の列（新宿に着く前）＝ 2章の欄の 23%・34%・31%（同じ値）・東京の列 ＝ 東京まで座れた割合（cells の tokyo.p_sat 0.858・0.932・0.915）",
         float([TBL_P[r_][1] for r_ in range(3)] == [SH["E_END"], SH["E_NEXT"], SH["E_MID"]]
               and all(abs(TBL_V[r_][3] - CELLS[_ck(j_)]["tokyo"]["p_sat"]) < 1e-9 for r_, j_ in enumerate((0, 1, 3)))), 1, 0),
        ("2章の表: 声「新宿までに、端の隣の前なら 6割を超える」＝ 0.649（0.6〜0.7）・「端の前だと 半分ほど」＝ 0.502（0.45〜0.55）・「東京まで乗れば いちばん座りにくい端の前でも 8割を超える」＝ 端の前の東京 0.858（最小・0.8超）",
         float(0.6 < TBL_V[1][2] < 0.7 and 0.45 <= TBL_V[0][2] <= 0.55 and min(TBL_V[r_][3] for r_ in range(3)) > 0.8 and abs(TBL_V[1][2] - 0.649) < 0.001
               and TBL_V[0][3] == min(TBL_V[r_][3] for r_ in range(3)) and abs(TBL_V[0][3] - 0.858) < 0.001), 1, 0),
        ("2章の表: 無音の約5秒のうちに4つの列が順に埋まる（g2t）・声の文が表の列を言う順（c2_12d 新宿 → c2_12e 端の前 → c2_12f 東京）",
         float(abs(dur("g2t") - 5.0) < 0.01 and S("g2t") + 0.3 + 1.1 * 3 + 0.6 <= E("g2t") and E("g2t") <= S("c2_12d") < S("c2_12e") < S("c2_12f")), 1, 0),
    ]
    # ---- 言い方の統一: 「新宿に着く前」(0.295 など)と「新宿までに」(新宿で座るのを含む 0.583)を取り違えない ----
    spoken_all = " ".join(txt(it.id) for it in tl.items if isinstance(it, lf.Line))
    sixty = [it.id for it in tl.items if isinstance(it, lf.Line) and "6割" in txt(it.id)]
    twice = [it.id for it in tl.items if isinstance(it, lf.Line) and "2倍" in txt(it.id)]
    checks += [
        ("言い方の統一: 「6割」の文は すべて「新宿で座れた分も入れると、新宿までに」（0.583＝新宿で座るのを含む）・「2倍」の文は すべて「新宿に着く前」（0.546÷0.295）か「立川と三鷹」の話",
         float(len(sixty) == 3 and all("新宿で座れた分も入れると" in txt(i_) for i_ in sixty)
               and all("新宿までに" in txt(i_) for i_ in sixty if i_ != "c2_12d")
               and all(("新宿に着く前" in txt(i_) or "立川と三鷹" in txt(i_)) for i_ in twice) and "新宿までに座れる割合" not in spoken_all), 1, 0),
        ("言い方の統一: 2章の見出し・欄・声は「新宿に着く前」（0.228/0.342/0.310 は新宿で座るのを含まない・E=新宿のとき 新宿で降りる前に座れた回）",
         float("新宿に着く前に座れたかで比べます" in txt("c2_7") and "新宿に着くまで" not in spoken_all and box_keys()[4]["cap"] == "三鷹から・新宿に着く前に座れた"), 1, 0),
    ]
    # ---- 画面の%の丸め（同じ決まり）----
    r_bef, r_at, r_t = A7["三鷹"]["p_before_shinjuku"], A7["三鷹"]["p_at_shinjuku"], BARS3_V[1]
    checks += [
        ("画面の%は 四捨五入（0.5を切り上げ・ihalf）の1つの決まり: 1章の欄「新宿に着く前」0.295→29%・「新宿で座れた」0.288→29%・3章の棒「三鷹」0.295→29%・欄「三鷹」29%が同じ値から出る（切り捨て・切り上げでは 29/29/30 のように割れる値）",
         float(r_t == r_bef and SH["P_BEF"] == SH["T_MITA"] == ihalf(r_bef * 100) == 29 and SH["P_AT"] == ihalf(r_at * 100) == 29
               and f"{PC(BARS3_V[1])}%" == f"{SH['T_MITA']}%" == f"{SH['P_BEF']}%" and math.floor(r_bef * 100) == 29 and 0.2945 <= r_bef < 0.2955), 1, 0),
        ("声は「3割ほど」＝ 三鷹 0.295 の 1桁の四捨五入（3）・声と画面（29%）の食い違いなし", float(SH["P_BEF3"] == 3 == ihalf(r_bef * 10) and SH["P_AT3"] == ihalf(r_at * 10) == 3), 1, 0),
    ]
    # ---- 人の大きさ（絵）----
    checks += [
        (f"人の大きさ: 座る人 {SIT_H:.0f}px・立つ人 {STAND_H:.0f}px（頭の直径 約50px）。座る人200px以上・立つ人250px以上・立つ人÷座る人 が 1.1〜1.5（席の高さとくらべて自然）",
         float(SIT_H >= 200 and STAND_H >= 250 and 1.1 <= STAND_H / SIT_H <= 1.5), 1, 0),
        ("人: 7つの席は 1つ118px間隔・立つ人の足元の幅 106px で、となりの人と重ならない", float(SEAT_PITCH >= 110 and 56 + 50 <= SEAT_PITCH), 1, 0),
        ("席は左ページ（x 45〜940）に収まる", float(min(SEAT_CX) - 60 >= 45 and max(SEAT_CX) + 60 <= 940), 1, 0),
    ]
    # ---- 声の数字: 台本のどの文も、言う数字が SPOKEN（data.json から作った値）と1つ残らず一致する ----
    bad_lines, many = [], []
    for it in tl.items:
        if isinstance(it, lf.Line):
            got = sorted(_re.findall(NUM_RE, txt(it.id)))
            if got != sorted(SPOKEN.get(it.id, [])):
                bad_lines.append(f"{it.id}: {got} ≠ {sorted(SPOKEN.get(it.id, []))}")
            if len(got) > 1:
                many.append(it.id)
    for s_ in bad_lines:
        print("  声の数字が違う:", s_)
    checks.append((f"声の数字が data.json の値と一致（文ごと・{len(SPOKEN)}文）: 食い違い {len(bad_lines)}", float(not bad_lines), 1, 0))
    new_many = [i for i in many if i not in MANY_OK]
    checks.append((f"1文の声の数字は1つまで: 例外 {new_many}", float(not new_many), 1, 0))
    # ---- 時間割 ----
    ch = tl.chapters
    ends = [c[0] for c in ch[1:]] + [DUR]
    checks.append(("章は5つ・最初は0秒", float(len(ch) == 5 and ch[0][0] == 0), 1, 0))
    for (t0_, title), e_ in zip(ch, ends):
        checks.append((f"章「{title}」が10秒以上", float(e_ - t0_ >= 10), 1, 0))
    checks.append(("長さ 7分〜9分半（--fake-voice の見積もり。本番の声の長さで変わる）", DUR, 495.0, 75.0))
    first40 = []
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            first40 += _re.findall(NUM_RE, txt(it.id))
    checks.append((f"冒頭40秒で声に出す数字は3つまで: {first40}", float(len(first40) <= 3), 1, 0))
    keys = box_keys()
    gaps_ = [b["t"] - a["t"] for a, b in zip(keys, keys[1:])]
    checks.append((f"数字の欄: 答えの数字は3秒以上見せる（変わるまでの最短 {min(gaps_):.1f}秒）", float(min(gaps_) >= 3.0), 1, 0))
    checks += [
        ("欄「90%」の赤丸は3秒以上", float(mid("c1_13", 0.6) - (mid("c1_11", 0.6) + 0.3) >= 3), 1, 0),
        ("欄「23%」の赤丸は3秒以上", float(mid("c2_9", 0.3) - (mid("c2_8", 0.6) + 0.3) >= 3), 1, 0),
        ("欄「72%」の赤丸は3秒以上", float(S("ch3") - (mid("c2_15", 0.6) + 0.3) >= 3), 1, 0),
        ("欄「55%」「29%」「12%」の赤丸は3秒以上", float(S("ch4") - (mid("c3_3", 0.6) + 0.3) >= 3), 1, 0),
        ("終了画面は まとめ の章の中", float(T_ES() > S("ch4") + 3), 1, 0),
        (f"区切りは約4秒（{EYE1() - EYE0():.1f}秒）", EYE1() - EYE0(), 4.0, 0.2),
        ("区切りは2章の終わりと3章の章カードの間", float(E("c2_19") <= EYE0() and EYE1() == S("ch3")), 1, 0),
        ("区切りは章ではない（chapters に入らない・章は5つのまま）", float(len(tl.chapters) == 5 and all(t0_ != EYE0() for t0_, _ in tl.chapters)), 1, 0),
        ("区切りは声なし（区切りの間に声の文がない）", float(not any(S(it.id) < EYE1() and E(it.id) > EYE0() for it in tl.items if isinstance(it, lf.Line))), 1, 0),
        (f"区切りの足あとと足音は {len(foot_times())} 回・すべて区切りの中", float(len(foot_times()) >= 10 and all(EYE0() <= tf <= EYE1() for _p, tf in foot_times())), 1, 0),
        ("区切りの文言 ＝ 左「ここまで／端の前は、座りにくい」・右「ここから／乗る駅が違ったら？」",
         float(EYE_LEFT == ("端の前は、", "座りにくい") and EYE_RIGHT == ("乗る駅が違ったら？",)), 1, 0),
        ("亀は左ページから右ページへ渡る（始め x<960・終わり x>960）", float(eye_x(EYE0()) < lf.GUTTER < eye_x(EYE1())), 1, 0),
        ("まとめの最後の説明の文（c4_6）は終了画面の前に言い終わる", float(E("c4_6") <= T_ES()), 1, 0),
        ("冒頭の早回しは無音の区間のうちに終わる（g0: 見本 open が座るまで）", float(S("g0") + 1.3 + 4 * 0 + (dur("g0") - 1.3 - 3.6) <= E("g0")), 1, 0),
        ("1章の早回し＋マス目は無音の区間のうちに終わる（g1）", float(S("g1") + 0.6 + 9.0 <= E("g1") and S("g1") + 0.3 + (dur("g1") - 0.9) <= E("g1")), 1, 0),
        ("2章のマス目は無音の区間のうちに埋まる（g2）", float(S("g2") + 0.3 + (dur("g2") - 0.9) <= E("g2")), 1, 0),
        ("3章の棒は無音の区間のうちに4本そろう（g3）", float(S("g3") + 0.3 + 2.0 * 3 + 0.7 <= E("g3")), 1, 0),
    ]
    # ---- 字幕 ----
    worst_cps, worst_vis, worst_lines = 0.0, 1e9, 0
    for s_, e_, pause, ln, clip in tl._lines:
        vis = e_ - s_ + min(pause, lf.SUB_HOLD)
        worst_cps = max(worst_cps, len(clip.text) / vis)
        worst_vis = min(worst_vis, vis)
        worst_lines = max(worst_lines, len(lf.wrap_subtitle(clip.text)))
    checks += [
        (f"字幕: 1秒あたりの字数が12字以下（最大 {worst_cps:.1f}字）", float(worst_cps <= 12), 1, 0),
        (f"字幕: どの行も1秒以上出る（最短 {worst_vis:.1f}秒）", float(worst_vis >= 1.0), 1, 0),
        (f"字幕: 2行以内（最大 {worst_lines}行）", float(worst_lines <= 2), 1, 0),
    ]
    # ---- 画面の文字・人（0.25秒ごとに描いて調べる） ----
    if frames is not None:
        bad = overlaps(frames)
        for k, t in list(bad.items())[:12]:
            print(f"  重なり: {_ts(t)} 「{k[0]}」と「{k[1]}」")
        checks.append((f"文字どうしの重なりなし（0.5秒以上続くもの。章の付箋・1万回の合図は除く）: {len(bad)}組", float(len(bad) == 0), 1, 0))
        f0 = next(f for f in frames if f[0] == 0.5)
        names0 = {e[0] for e in f0[1]}
        checks.append(("0.5秒目までに 題字「満員電車の空席」と右ページの問いが出ている", float({"満員電車の空席", "満員電車、", "どこに立つ？"} <= names0), 1, 0))
        dig40 = sorted({e[0] for f in frames if f[0] < 40 for e in f[1] if any(c.isdigit() for c in e[0])})
        checks.append((f"冒頭40秒に、画面に出る数字（を含む文字）は3つまで: {dig40}", float(len(dig40) <= 3), 1, 0))
        tes = T_ES() + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1]
                  if e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936]
        for t, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        checks.append((f"終了画面の文字はページの中（左 x 40〜940・右 x 980〜1880）・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", float(not out_es), 1, 0))
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        checks.append((f"終了画面の文字は すべて 38px 以上（付せんの答えは 68px・名前は 46px・問いかけは 68px・登録は 52px）: {es_small}", float(not es_small), 1, 0))
        es_last = [e for f in frames if f[0] >= T_ES() + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        checks.append(("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", float(len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5), 1, 0))
        es_ans = {e[0]: e[5] for f in frames if f[0] >= T_ES() + 1.0 for e in f[1] if e[0] in ("東京までに 約9割", "端の前より 端の隣の前", "乗る駅で 2倍ちがう")}
        checks.append((f"終了画面の答えの付せん（左ページ）の答えの文字は 64px 以上: {es_ans}", float(len(es_ans) == 3 and min(es_ans.values()) >= 63.5), 1, 0))
        small = {}
        for f in frames:
            for e in f[1]:
                if e[5] < 35.5:
                    small.setdefault((e[0], round(e[5])), f[0])
        for (s_, sz), t_ in list(small.items())[:12]:
            print(f"  36px未満の文字: {_ts(t_)} 「{s_}」 {sz}px")
        checks.append((f"画面の文字（字幕を除く）は すべて 36px 以上（幅480pxに縮めても読める）: 36px未満 {len(small)}種", float(not small), 1, 0))
        br = [(f[0], e[0]) for f in frames for e in f[1] if e[3] > 1660 and e[4] > 930]
        for t, s_ in br[:5]:
            print(f"  右下に文字: {_ts(t)} 「{s_}」")
        checks.append((f"右下（x>1660・y>930）に文字を置かない: {len(br)}件", float(not br), 1, 0))
        k0 = box_keys()[0]["t"]
        in_box = lambda e: 1030 < e[1] and e[3] < 1800 and e[2] > 712
        box_units = ("%",)
        miss = [f[0] for f in frames if k0 + 0.8 <= f[0] < T_ES() - 0.1 and not (EYE0() - 0.1 <= f[0] < EYE1() + 0.6) and not (S("c2_12c") - 0.2 <= f[0] < S("c2_13") + 0.6)
                and not any(in_box(e) and e[0].endswith(box_units) for e in f[1])]
        checks.append((f"数字の欄は 最初の答えから終了画面まで出しっぱなし（区切りの4秒は除く。欠けたコマ {len(miss)}）", float(not miss), 1, 0))
        fe = [f for f in frames if EYE0() + 0.4 <= f[0] < EYE1() - 0.05]
        checks.append(("区切りの間は、数字の欄を出さない", float(bool(fe) and not any(in_box(e) and e[0].endswith(box_units) for f in fe for e in f[1])), 1, 0))
        checks.append(("区切りの間は、左「ここまで」＋2行・右「ここから」＋2行が出ている（0.5秒すぎから最後まで）",
                       float(all({"ここまで", "ここから", *EYE_LEFT, *EYE_RIGHT} <= {e[0] for e in f[1]} for f in fe if f[0] >= EYE0() + 0.5)), 1, 0))
        checks.append(("区切りの左右の文字はページの中（左は x<940・右は x>980）",
                       float(all((e[3] < 940 if e[0] in ("ここまで", *EYE_LEFT) else e[1] > 980) for f in fe for e in f[1]
                                 if e[0] in ("ここまで", "ここから", *EYE_LEFT, *EYE_RIGHT))), 1, 0))
        # 左ページの文字は x<945、右ページの文字は x>1030 に収まる（区切り・終了画面・章カードを除く）
        stray = [(f[0], e[0]) for f in frames for e in f[1]
                 if not (EYE0() <= f[0] < EYE1() + 0.4) and f[0] < T_ES() and e[0] not in OVERLAY_OK and (945 < e[3] and e[1] < 1030)]
        for t, s_ in stray[:5]:
            print(f"  のどにかかる文字: {_ts(t)} 「{s_}」")
        checks.append((f"見開きののど（x 945〜1030）に文字をまたがせない: {len(stray)}件", float(not stray), 1, 0))
        # 左ページ（x<945）の文字が、左ページの外（x<40）に出ない
        left_out = [(f[0], e[0]) for f in frames for e in f[1] if f[0] < T_ES() and not (EYE0() <= f[0] < EYE1() + 0.4) and e[0] not in OVERLAY_OK and e[3] < 945 and e[1] < 42]
        for t, s_ in left_out[:5]:
            print(f"  左ページの左はしにかかる文字: {_ts(t)} 「{s_}」")
        checks.append((f"左ページの文字は ページの左はし（x<42）にかからない: {len(left_out)}件", float(not left_out), 1, 0))
        # 画面に出る数字は、data.json（の四捨五入）か閉じた式の値だけ
        allowed = set(range(0, 11)) | {10000, SH["RATIO"]}
        allowed |= {SH[k] for k in ("P_SAT", "P_BEF", "P_AT", "E_END", "E_NEXT", "E_MID", "O_END", "O_MID", "T_TACH", "T_MITA", "T_KICH", "T_OGI")} | TBL_FLAT
        shown_nums = {}
        for f in frames:
            for e in f[1]:
                if e[0] in OVERLAY_OK or e[0] in EYE_LEFT + EYE_RIGHT or e[0] in ("ここまで", "ここから"):
                    continue
                for m in _re.findall(r"\d+(?:\.\d+)?", e[0]):
                    shown_nums.setdefault(float(m), e[0])
        extra = sorted((v, s_) for v, s_ in shown_nums.items() if v not in allowed)
        for v, s_ in extra[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」")
        checks.append((f"画面に出る数字は、すべて data.json の値（の四捨五入）か、席の数・番号札などの閉じた値: 余分 {len(extra)}個", float(not extra), 1, 0))
        pcts = {int(m) for f in frames for e in f[1] for m in _re.findall(r"(\d+)%", e[0])}
        extra2 = sorted(pcts - PCT_OK)
        checks.append((f"画面に出る「N%」は、すべて data.json から作った値: 余分 {extra2}", float(not extra2), 1, 0))
        box_vals = {c[1] for kk in box_keys() for c in kk["cells"]}
        shown_box = {e[0] for f in frames for e in f[1] if in_box(e) and e[0].endswith("%")}
        extra3 = sorted(shown_box - box_vals)
        checks.append((f"数字の欄の数字は data.json の値だけ: 余分 {extra3}", float(not extra3), 1, 0))
        # 実在の会社・車両・色の話を出さない。「仮定」「決めごと」は台本の言い方（この動画で決めたルール）に合わせる
        bad_words = ("東日本旅客鉄道", "JR", "東京メトロ", "オレンジ", "混雑率", "満員率", "np.", "seed", "仮定", "決めごと", "ガラガラ", "ひどい", "最悪")
        all_txt = " ".join(e[0] for f in frames for e in f[1]).replace("（この動画の決めごと）", "") + " ".join(tl.clip(it.id).text for it in tl.items if isinstance(it, lf.Line))
        hit_w = [w for w in bad_words if w in all_txt]
        checks.append((f"実在の会社名・混雑や会社の評価の言葉・「仮定」「決めごと」を画面と声に出さない: {hit_w}", float(not hit_w), 1, 0))
        rule_txt = {e[0] for f in frames for e in f[1] if "ルール" in e[0]}
        checks.append((f"画面の「ルール」は台本の言い方（この動画で決めたルール）: {sorted(rule_txt)}", float(rule_txt <= {"空いた席に誰が座るか など", "この動画で決めたルール"}), 1, 0))
        # 人: 大きさ・重なり・はみ出し
        n_ov, n_small, n_out = person_boxes(frames)
        checks.append((f"人が重ならない（0.25秒ごとに、濃さ0.5以上の人の外枠どうしが重なったコマ）: {n_ov}コマ", float(n_ov == 0), 1, 0))
        checks.append((f"人の大きさ（濃さ0.99以上の人が 座る200px・立つ250px 以上）: 小さい人 {n_small}", float(n_small == 0), 1, 0))
        checks.append((f"人は左ページの中（x 44〜941・y 262〜936）に収まる: はみ出し {n_out}", float(n_out == 0), 1, 0))
        # 早回し・マス目のコマに人が描かれている
        run_frames = [f for f in frames if (S("g0") + 1.3 <= f[0] < E("g0") - 3.0) or (S("g1") + 0.6 <= f[0] < S("g1") + 9.6)]
        checks.append((f"早回しのコマ（{len(run_frames)}コマ）には、座る人・立つ人が合わせて 9人以上描かれている", float(all(f[2] >= 9 for f in run_frames)), 1, 0))
        ch2_frames = [f for f in frames if S("c2_1") + 4 <= f[0] < S("c2_12")]
        checks.append((f"2章（3か所の説明）のコマでは、7人がけの席の座る人7人＋立つ人7人 ＝ 14人が描かれている（{len(ch2_frames)}コマ）", float(all(f[2] >= 14 for f in ch2_frames)), 1, 0))
        # ドアの前の人: 描かれた人の位置・矢印の時刻・付せん
        t_dr = mid("c2_12x2", 0.95)
        f_dr = min(frames, key=lambda f: abs(f[0] - t_dr))
        door_people = [q_ for q_ in f_dr[3] if q_[0] == "stand" and q_[3] < 300]
        checks.append((f"ドアの前の人: 2文目のコマに、席の左（x<300）に立つ人が1人描かれていて、小さくしすぎない（高さ {max([(q_[4] - q_[2]) for q_ in door_people] or [0]):.0f}px ≧ 205）・重ならない",
                       float(len(door_people) == 1 and (door_people[0][4] - door_people[0][2]) >= 205), 1, 0))
        t_st = mid("c2_12x3", 0.9)
        f_st = min(frames, key=lambda f: abs(f[0] - t_st))
        checks.append(("ドアの前の人: 3文目のコマに付せん「ドアの前の人は 端の席に座らない」「（この動画の決めごと）」が出ている（36px以上）",
                       float({"ドアの前の人は 端の席に座らない", "（この動画の決めごと）"} <= {e[0] for e in f_st[1] if e[5] >= 35.5}), 1, 0))
        # 2章の表: 12個の値が画面に出ていて、48px以上
        f_tb = min(frames, key=lambda f: abs(f[0] - (E("c2_12f") - 0.3)))
        tb_txt = sorted(e[0] for e in f_tb[1] if e[0].endswith("%") and e[1] > 1260 and 360 < e[2] < 760)
        tb_small = [e for e in f_tb[1] if e[0].endswith("%") and e[1] > 1260 and 360 < e[2] < 760 and e[5] < 47.5]
        checks.append((f"2章の表: 画面に12個の値が出ている（{len(tb_txt)}個）・どれも 48px 以上（スマホで読める）: 小さいもの {len(tb_small)}",
                       float(tb_txt == sorted(f"{v}%" for row in TBL_P for v in row) and not tb_small), 1, 0))
        # 画面に出た「29%」: 3章の棒の上（三鷹）と欄・1章の欄が、同じ29%
        t_b3 = mid("c3_2c", 0.97)
        f_b3 = min(frames, key=lambda f: abs(f[0] - t_b3))
        p29 = [e for e in f_b3[1] if e[0] == "29%"]
        checks.append((f"画面の「29%」が 3章の棒（x 1300〜1420）と欄の両方に出ている: {len(p29)}個", float(any(1300 < (e[1] + e[3]) / 2 < 1420 and e[4] < 600 for e in p29) and any(e[2] > 700 for e in p29)), 1, 0))
        # 0b: 描いた丸・棒・点
        t_full = min(CLOG_BY_T, key=lambda x: abs(x - (E("c0b_5") - 0.3)))
        cl = CLOG_BY_T[t_full]
        gc = {nm[7:]: v1 for nm, v1, _v2 in cl if nm.startswith("circle:")}
        gb = {nm[4:]: v1 for nm, v1, _v2 in cl if nm.startswith("bar:")}
        gd = {nm[4:]: (v1, _v2) for nm, v1, _v2 in cl if nm.startswith("dot:")}
        okc = len(gc) == 11 and all(abs(math.pi * gc[n_] ** 2 / INTRO_V[i] - ratios[0]) < 1e-9 * ratios[0] for i, (n_, *_r) in enumerate(INTRO_ST))
        okb = len(gb) == 11 and all(abs(gb[n_] / INTRO_V[i] - bratio[0]) < 1e-9 * bratio[0] for i, (n_, *_r) in enumerate(INTRO_ST))
        checks.append((f"0b 描いた丸（{_ts(t_full)} のコマ・{len(gc)}個）の面積・描いた横棒（{len(gb)}本）の長さが CSV の人数に比例・新宿が最大",
                       float(okc and okb and max(gc, key=gc.get) == "新宿" and max(gb, key=gb.get) == "新宿"), 1, 0))
        dev_ll = 0.0
        for (n_, _o, lo, la) in INTRO_ST:
            if n_ in gd:
                lo2, la2 = from_screen(gd[n_][0], gd[n_][1], CAM_ZOOM)
                dev_ll = max(dev_ll, abs(lo2 - lo), abs(la2 - la))
        checks.append((f"0b 描いた駅の点（{len(gd)}個）を 画面の位置から緯度経度に戻すと CSV と一致（同じ投影）: 最大の差 {dev_ll:.2e}度", float(len(gd) == 11 and dev_ll < 1e-6), 1, 0))
        f_int = [f for f in frames if S("c0b_5") + 1.0 <= f[0] < S("c0b_5") + 2.0]
        names_i = {e[0] for e in f_int[0][1]} if f_int else set()
        checks.append(("0b 紹介の最後のコマに、駅名11個と 西・東 が出ている（数字は出ない）", float({n_ for n_, *_r in INTRO_ST} <= names_i and not any(any(c.isdigit() for c in nm) for nm in names_i)), 1, 0))
        # 1章の路線の図: 24駅の点が出ていて、名前の札が主な駅に出ている
        st_names = {"高尾", "八王子", "立川", "三鷹", "新宿", "東京"}
        f_route = next(f for f in frames if f[0] >= E("c1_1") + 0.1)
        checks.append((f"1章の路線の図に 主な駅の名前（高尾・八王子・立川・三鷹・新宿・東京）が出ている", float(st_names <= {e[0] for e in f_route[1]}), 1, 0))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 要所の静止画6枚と一覧（幅480px・2列×3段・各枚の下に番号）
# ============================================================
def stills_final(out_dir):
    """本番の時刻で 静止画（冒頭・紹介・1章の答え・2章・3章・終了画面）と一覧 sheet_480.png"""
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    names = ["still_1_open", "still_2_route", "still_3_answer_bars", "still_4_three_spots", "still_5_boarding_stations", "still_6_end_screen", "still_7_chuo_intro", "still_8_table", "still_9_ch2_route", "still_10_doorside"]
    order = [0, 6, 2, 3, 9, 7, 8, 4, 5]
    paths = []
    for nm, tt in zip(names, still_times6()):
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}")
    W_, H_, lab_h, pad = 480, 270, 34, 10
    sheet = Image.new("RGB", (pad + 2 * (W_ + pad), pad + ((len(order) + 1) // 2) * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, i in enumerate(order):
        im = Image.open(paths[i]).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % 2) * (W_ + pad), pad + (k // 2) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + H_ + 3), f"{i + 1}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")


def stills_preview(out_dir):
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    names = ["still_1_open", "still_2_route", "still_3_answer_bars", "still_4_three_spots", "still_5_boarding_stations", "still_6_end_screen", "still_7_chuo_intro", "still_8_table", "still_9_ch2_route", "still_10_doorside"]
    order = [0, 6, 2, 3, 9, 7, 8, 4, 5]                                  # 一覧: 冒頭・中央線の紹介・1章の答え・2章・3章・終了画面（番号は静止画の番号）
    ts = still_times6()
    paths = []
    for nm, tt in zip(names, ts):
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}")
    W_, H_ = 480, 270
    lab_h = 34
    pad = 10
    sheet = Image.new("RGB", (pad + 2 * (W_ + pad), pad + ((len(order) + 1) // 2) * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, i in enumerate(order):
        im = Image.open(paths[i]).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x = pad + (k % 2) * (W_ + pad)
        y = pad + (k // 2) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + H_ + 3), f"{i + 1}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--readings" in args:
        write_readings(OUT / "readings.log")
        return
    if "--wraps" in args:
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        return
    if "--scenecheck" in args:
        frames = scan()
        scene_checks(frames)
        return
    if "--mapcompare" in args:
        map_compare(OUT / "scene_work" / "map_compare.png")
        return
    if "--stills-all" in args:
        stills_keep(draw, still_times(), OUT / "scene_work" / "stills_all")
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, OUT / "scene_work" / f"at_{tt:06.1f}.png")
        else:
            stills_preview(OUT / "stills_preview")
        return
    if "--preview" in args:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
        return
    if FAKE:
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    # ---- 本番 ----
    frames = scan()
    scene_checks(frames)
    write_screen_text(OUT / "screen_text.txt", frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    stills_final(OUT / "stills_final")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
