"""高速道路の合流で、1台がちょっとブレーキ。後ろで何台止まる？（自然渋滞）— 2026-10-06 に「高速道路の合流」の設定で作り直した版

モデル: IDM（Intelligent Driver Model, Treiber, Hennecke & Helbing 2000）。1車線のまっすぐな長い道（長さ約11kmの周期境界。
  1回の観察は150秒＝車は約3.3km進むだけなので、同じ車がもう一度渋滞に入ることはなく、無限に続く道と同じ）。
  各車の加速度  a_i = a [ 1 − (v/v0)^4 − (s*/s)^2 ]   s* = s0 + v T + v Δv / (2√(a b))
    v0=140km/h（希望速度）  T=0.6秒（車間時間）  a=0.5 m/s²  b=2.2 m/s²  s0=2m  車の長さ 5m
  車ごとに v0 は ±2.5%、T は ±4% の個人差（車ごとに固定）、加速度に小さな揺らぎ（標準偏差0.08 m/s²、相関時間2秒）。
  はじめは全車が等間隔（車間16.4m＝時速81kmで走るときの釣り合いの車間）で、平均時速約80km。合流がなければ150秒のあいだ渋滞しない。
  時間刻みは 0.1 秒。
  ※標準のIDM（v0=120, T=1.6, a=0.73, b=1.67）は時速80kmのままだと「ちょっとブレーキ」を与えても渋滞が育たない（車間が広く、安定）。
    車間を詰めた（T=0.6秒）ぶんだけ不安定になり、1回のブレーキが後ろへ伝わるうちに増幅して止まる車が出る。
きっかけ: 時刻 0 に合流車が本線に入り、そのすぐ後ろの車（F）が「ちょっとブレーキ」。2秒間、一定の減速（2.78 m/s²）で
  時速81km → 約61km まで落とし、その後は他の車と同じIDMにもどる。ブレーキはこれ1回だけ（合流車は本線の1台として走る。
  合流前は合流車線を、本線の同じ位置・同じ速さで併走している扱い）。
  対照（合流なし）は同じ道・同じ個人差で、このブレーキだけをなくしたもの。
止まった = 時速5km以下になった車。数える範囲は ブレーキから150秒（2分30秒）のあいだ、道全体で、1台は1回だけ数える。
1万回 = 乱数（個人差・揺らぎ）だけを変えた1万本の道。

問い: 「ブレーキ1回で、何台止まる？」 A 0台 ／ B 数台（1〜9台）／ C 数十台（10〜99台）。答えは C（結果は画面と概要欄に）。
見せ方:
  （2026-10-06 見た目だけ修正 v4: 冒頭は車の長さ5m：車間16mの実比率で描く縮尺7px/m。道を引いた場面は車の絵をやめて実比率の短い角丸線で描く。モデル・数字・台本・時間割は不変）
  （2026-10-07 v5: ユーザー「さらに寄る」。冒頭の縮尺 7→13px/m（画面に約4台）、寄りの道の太さ 44→80px）
  冒頭  … 高速道路（左→右）。合流車線から1台が本線に入り、すぐ後ろの車がブレーキ。カウントダウンのあいだ早送りで何台かが減速するが、止まる車は出ない。
  答え合わせ1 … 同じ道で早送りの続き。後ろで車が止まり始め、止まった車の列が左へ伸びる。
  答え合わせ2 … 100×100 のグリッド。1マス＝1回。止まった台数で水色→赤。
  驚き  … 道を引いて長く見せる。車は前へ、渋滞の先頭は後ろへ（時速はモデルから測る）。
  ひねり … 車間を広げた（T=1.6秒＝標準のIDM。車間41m）同じ合流・同じブレーキ。1万回でも止まる車は0台。
  名前  … 「自然渋滞」。締め … ブレーキは1回なのに、なんで止まる車が増えていくの？ → 答えは概要欄。

照合（check_answers）— 閉じた式がない回なので、別の方法・別の乱数で同じ値が出ることを確かめる:
 (1) 合流なし（対照）1万本で、止まった車の合計が 0 台。
 (2) 時間刻みを 0.1 秒 → 0.05 秒にしても、止まった台数の平均がほぼ同じ。
 (3) 車どうしが衝突しない（最小の車間が 0.5m 以上）。
 (4) 渋滞の先頭が後ろへ進む速さを2通りで測って一致する。
     A: 止まっている車のいちばん前の位置を時間に対して直線で当てはめた傾き（300本）。
     B: 先頭の車が動き出してから次の車が動き出すまでの間隔と、止まっているときの車の間隔から出す速さ（300本）。
 (5) 画面に出す数字（平均の台数など）が、別の乱数で1万本やり直した結果と同じ丸めになる。
乱数の種は、冒頭の見本（カウントダウンのあいだ止まらず、そのあと止まり始める道）を選ぶために選んでよい。
画面の統計は、1万本すべて（見本の道は別）から正直に出している。
"""
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import core, note
from engine.note import INK, PENCIL, RED, MARKER, PAPER
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, _t)
from engine.parts import loop_back, r1, stills, grid_image

note.use()
note.DATE = "10.8"                                # 日付欄（公開予定日）

SLUG = "shizen-jutai"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
KMH = 3.6
N_TRIALS = 10000
WINDOW = 150                                      # 数える範囲: ブレーキから150秒
STOP_KMH = 5.0                                    # 止まった = 時速5km以下
T_WIDE = 1.6                                      # ひねり: 車間時間（標準のIDM）
BLUE = "#2f62c9"
CAR_RED = "#e8564e"                               # 止まっている車
CELL_BLUE = "#a9c9ec"

P0 = dict(v0=140 / 3.6, T=0.6, a=0.5, b=2.2, s0=2.0, ell=5.0, v_eq=81 / 3.6, n=220, dt=0.1, warm=20.0,
          sig_v0=0.025, sig_T=0.04, sig_a=0.08, tau_n=2.0, brake_dv=20 / 3.6, brake_t=2.0)


# ---------- モデル（IDM） ----------

def eq_gap(P, T=None):
    """時速 v_eq で走るときの釣り合いの車間（バンパーからバンパー）"""
    T = P["T"] if T is None else T
    v = P["v_eq"]
    return (P["s0"] + v * T) / math.sqrt(1 - (v / P["v0"]) ** 4)


def sim(R, seed, P=None, dur=float(WINDOW), brake=True, rec_from=None, track=False, T=None, dt=None):
    """R 本の環状の道を同時に回す。車 fi が 時刻0 に「ちょっとブレーキ」（brake=False で対照）。
    返り値: first（各車が最初に止まった時刻・止まらなければ inf）、cnt_sec（その秒までに止まった台数）、
    head_sec（止まっている車のいちばん前の位置[m]・合流位置から）、速さの記録など"""
    P = dict(P0, **(P or {}))
    if T is not None:
        P["T"] = T
    if dt is not None:
        P["dt"] = dt
    n, dt, ell, s0, a, b = P["n"], P["dt"], P["ell"], P["s0"], P["a"], P["b"]
    rng = np.random.default_rng(seed)
    s_e = eq_gap(P)
    head = s_e + ell
    Lr = head * n
    fi = n // 2                                   # ブレーキする車（合流車の1つ後ろ）。合流車は fi+1
    x = np.tile(np.arange(n) * head, (R, 1))
    v = np.full((R, n), P["v_eq"])
    V0 = P["v0"] * (1 + P["sig_v0"] * rng.standard_normal((R, n)))
    TT = P["T"] * (1 + P["sig_T"] * rng.standard_normal((R, n)))
    eta = np.zeros((R, n))
    sq = 2 * math.sqrt(a * b)
    ed = math.exp(-dt / P["tau_n"])
    es = P["sig_a"] * math.sqrt(1 - ed * ed)
    nw, nd, nbt = int(round(P["warm"] / dt)), int(round(dur / dt)), int(round(P["brake_t"] / dt))
    per_sec = int(round(1 / dt))
    first = np.full((R, n), np.inf)
    sthr = STOP_KMH / 3.6
    nsec = int(dur)
    cnt_sec = np.zeros((R, nsec + 1), np.int16)
    head_sec = np.full((R, nsec + 1), np.nan, np.float32)
    nst_sec = np.zeros((R, nsec + 1), np.int16)
    nvf = int(round(12 / dt)) + 1
    vF = np.zeros((R, nvf), np.float32)
    vmean_pre = np.zeros(R)
    npre = 0
    mingap = 1e9
    xm = None
    if track:
        was = np.zeros((R, n), bool)
        rt = np.full((R, n), np.inf)
        rx = np.zeros((R, n))
    recX, recV, recT = [], [], []
    for k in range(-nw, nd + 1):
        t = k * dt
        if k == 0:
            xm = x[:, fi + 1].copy()
        eta = eta * ed + es * rng.standard_normal((R, n))
        xl = np.roll(x, -1, axis=1)
        xl[:, -1] += Lr
        vl = np.roll(v, -1, axis=1)
        sgap = xl - x - ell
        if k >= 0:
            mingap = min(mingap, float(sgap.min()))
        s = np.maximum(sgap, 0.1)
        sstar = np.maximum(s0 + v * TT + v * (v - vl) / sq, 0)
        acc = a * (1 - (v / V0) ** 4 - (sstar / s) ** 2) + eta
        if brake and 0 <= k < nbt:
            acc[:, fi] = -P["brake_dv"] / P["brake_t"]
        if 0 <= k < nvf:
            vF[:, k] = v[:, fi]
        vnew = np.maximum(v + acc * dt, 0)
        x = x + (v + vnew) / 2 * dt
        v = vnew
        if rec_from is not None and t >= rec_from - 1e-9:
            recX.append(x.copy())
            recV.append(v.astype(np.float32))
            recT.append(t)
        if k >= 0:
            m = v <= sthr
            first[m & np.isinf(first)] = t
            if track:
                was |= m
                rs = was & ~m & np.isinf(rt)
                rt[rs] = t
                rx[rs] = x[rs]
            if k % per_sec == 0:
                sec = int(round(t))
                if sec <= nsec:
                    cnt_sec[:, sec] = np.isfinite(first).sum(1)
                    nst_sec[:, sec] = m.sum(1)
                    rel = ((x - xm[:, None] + Lr / 2) % Lr) - Lr / 2
                    hx = np.where(m & (rel <= 500), rel, -np.inf).max(1)     # 合流位置より500mより前の渋滞は数えない（別のところにできた渋滞を拾わない）
                    head_sec[:, sec] = np.where(np.isfinite(hx), hx, np.nan)
            if t <= 100:
                vmean_pre += v.mean(1)
                npre += 1
    out = dict(first=first, cnt_sec=cnt_sec, head_sec=head_sec, nst_sec=nst_sec, vF=vF, mingap=mingap,
               vmean_pre=vmean_pre / max(npre, 1), s_e=s_e, head=head, Lr=Lr, fi=fi, dt=dt)
    if track:
        out.update(rt=rt, rx=rx)
    if rec_from is not None:
        X = np.array(recX)                       # 合流位置（時刻0の合流車の位置）からの距離。巻き戻さない
        out.update(X=(X - xm[None, :, None]).astype(np.float32), V=np.array(recV), Tt=np.array(recT))
    return out


def _wide(P, kind):
    return dict(P, n=110) if kind == "wide" else P


def _w_trials(args):
    """1万回のうちの一部（別プロセスで）。kind: merge（合流＋ブレーキ）/ control（合流なし）/ wide（車間を広げた合流）"""
    kind, seed, R = args
    P = _wide(P0, kind)
    r = sim(R, seed, P, dur=float(WINDOW), brake=(kind != "control"), T=T_WIDE if kind == "wide" else None)
    f = r["first"]
    vF = r["vF"]
    return dict(t1=f.min(1).astype(np.float32), cnt_sec=r["cnt_sec"].astype(np.uint8),
                vF0=vF[:, 0], vF2=vF[:, int(round(P["brake_t"] / P["dt"]))],
                vFmin=vF.min(1), vmean_pre=r["vmean_pre"].astype(np.float32), mingap=np.full(R, r["mingap"], np.float32))


def _pool():
    return ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2)))


def run_set(kind, seed, R=N_TRIALS, chunk=500):
    """R 本を chunk ずつ別プロセスで回して、まとめる"""
    jobs = [(kind, seed * 1000 + i, min(chunk, R - i * chunk)) for i in range((R + chunk - 1) // chunk)]
    with _pool() as ex:
        parts = list(ex.map(_w_trials, jobs))
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


# ---------- 渋滞の先頭が後ろへ進む速さ（2通り） ----------

def _w_wave(args):
    seed, R = args
    P = dict(P0, n=500)
    r = sim(R, seed, P, dur=330.0, track=True)
    hs, ns, f = r["head_sec"], r["nst_sec"], r["first"].min(1)
    A = []
    for i in range(R):
        ok = np.where((ns[i] >= 3) & ~np.isnan(hs[i]) & (np.arange(hs.shape[1]) >= f[i] + 30) & (np.arange(hs.shape[1]) <= f[i] + 130))[0]
        if len(ok) >= 60:
            A.append(float(np.polyfit(ok, hs[i, ok], 1)[0]))
    rt, rx = r["rt"], r["rx"]
    dts, sps = [], []
    for i in range(R):
        ok = np.isfinite(rt[i, :-1]) & np.isfinite(rt[i, 1:])
        dt_ = rt[i, :-1] - rt[i, 1:]                 # 車 j（フォロワー）と車 j+1（前の車）が動き出す時刻の差
        sp_ = rx[i, 1:] - rx[i, :-1]                 # そのときの2台の位置の差（止まっているときの車の間隔）
        good = ok & (dt_ > 0) & (dt_ < 10) & (sp_ > 0) & (sp_ < 15)
        dts.append(dt_[good])
        sps.append(sp_[good])
    return dict(A=np.array(A), dts=np.concatenate(dts), sps=np.concatenate(sps))


def run_wave(seed=5000, R=300, chunk=60):
    jobs = [(seed + i, min(chunk, R - i * chunk)) for i in range((R + chunk - 1) // chunk)]
    with _pool() as ex:
        parts = list(ex.map(_w_wave, jobs))
    A = np.concatenate([p["A"] for p in parts])
    dts = np.concatenate([p["dts"] for p in parts])
    sps = np.concatenate([p["sps"] for p in parts])
    return dict(A=A, dt_mean=float(dts.mean()), sp_mean=float(sps.mean()), nB=len(dts))


# ---------- 見本の道（冒頭〜答え合わせ1・驚き・名前・締め）の種を探す ----------
N_SAMPLE = 520                                    # 見本の道は長め（約11km）にして、300秒以上たっても同じ車が戻ってこないように


class Smp:
    """見本の道の記録（時刻 s ごとの全車の位置・速さ）。合流位置（時刻0の合流車の位置）からの距離で持つ"""

    def __init__(self, rec, n):
        self.n = n
        self.X, self.V, self.T = rec["X"], rec["V"], rec["Tt"]
        self.dt = float(self.T[1] - self.T[0])
        self.T0 = float(self.T[0])
        self.Lr, self.fi = float(rec["Lr"]), int(rec["fi"])
        self.head, self.s_e = float(rec["head"]), float(rec["s_e"])
        self.K = len(self.T)
        thr = STOP_KMH / 3.6
        k0 = int(round(-self.T0 / self.dt))
        stopped = self.V <= thr
        self.FS = np.full(n, np.inf)                # 各車が最初に止まった時刻
        for j in range(n):
            w = np.where(stopped[k0:, j])[0]
            if len(w):
                self.FS[j] = w[0] * self.dt
        self.founder = int(np.argmin(self.FS))
        self.t1 = float(self.FS[self.founder])
        # 止まった車の最前・最後尾（秒ごと、合流位置から。500mより前のものだけ）
        ns = int((self.T[-1]) )
        self.H = np.full(ns + 1, np.nan)
        self.Tl = np.full(ns + 1, np.nan)
        for sec in range(ns + 1):
            k = k0 + int(round(sec / self.dt))
            if k >= self.K:
                break
            rel = self.wrap(self.X[k])
            m = stopped[k] & (rel <= 500)
            if m.any():
                self.H[sec] = rel[m].max()
                self.Tl[sec] = rel[m].min()
        # 動き出した時刻（止まったあと、初めて時速5kmを超えた時刻）
        self.RT = np.full(n, np.inf)
        for j in np.where(np.isfinite(self.FS))[0]:
            kk = k0 + int(round(self.FS[j] / self.dt))
            w = np.where(~stopped[kk:, j])[0]
            if len(w):
                self.RT[j] = (kk - k0 + w[0]) * self.dt

    def wrap(self, x):
        return ((x + self.Lr / 2) % self.Lr) - self.Lr / 2

    def k_of(self, s):
        return (s - self.T0) / self.dt

    def state(self, s):
        """時刻 s（秒、合流が0）の全車の位置[m]（巻き戻さない）、速さ[m/s]、ブレーキランプ"""
        kf = min(max(self.k_of(s), 0.0), self.K - 1.001)
        k = int(kf)
        f = kf - k
        x = self.X[k] * (1 - f) + self.X[k + 1] * f
        v = self.V[k] * (1 - f) + self.V[k + 1] * f
        k_old = max(k - int(round(1.0 / self.dt)), 0)
        decel = (self.V[k_old] - self.V[k]) / 1.0
        lamp = (decel > 0.7) | (v < 1.0)
        return x, v, lamp

    def count_at(self, s):
        return int((self.FS <= s).sum())

    def x_first(self):
        """最初に止まった車の、止まった瞬間の位置（合流位置から）"""
        k = int(round(self.k_of(self.t1)))
        return float(self.wrap(self.X[k])[self.founder])

    def head_at(self, s, smooth=6.0):
        """時刻 s での渋滞の先頭（止まっている車のいちばん前）の位置。前後 smooth 秒をならす。無ければ None"""
        lo, hi = int(max(0, math.floor(s - smooth))), int(min(len(self.H) - 1, math.ceil(s + smooth)))
        v = self.H[lo:hi + 1]
        v = v[~np.isnan(v)]
        return float(v.mean()) if len(v) else None


def make_sample(seed, n=N_SAMPLE, dur=400.0, T=None):
    r = sim(1, seed, dict(P0, n=n), dur=dur, rec_from=-6.0, T=T)
    rec = dict(X=r["X"][:, 0, :], V=r["V"][:, 0, :], Tt=r["Tt"], Lr=r["Lr"], fi=r["fi"], head=r["head"], s_e=r["s_e"])
    return rec


def _w_sample2(seed):
    rec = make_sample(seed)
    sm = Smp(rec, N_SAMPLE)
    hi_ok = not np.isnan(sm.H[int(sm.t1) + 3:331]).any() if np.isfinite(sm.t1) else False
    rts = np.sort(sm.RT[np.isfinite(sm.RT)])
    return seed, round(sm.t1, 1), round(sm.x_first(), 0), sm.count_at(WINDOW), bool(hi_ok), \
        round(float(sm.head_at(150.0) or 0), 0), round(float(sm.head_at(250.0) or 0), 0), int((sm.H > -9999).sum())


if __name__ == "__main__" and "--search-sample2" in sys.argv:
    a, b = int(sys.argv[sys.argv.index("--search-sample2") + 1]), int(sys.argv[sys.argv.index("--search-sample2") + 2])
    with _pool() as ex:
        res = list(ex.map(_w_sample2, range(a, b)))
    for r_ in sorted(res, key=lambda z: (not z[4], abs(z[1] - 99))):
        print(r_)


# ---------- 1万回・見本・測定の結果（out/ に取っておく） ----------
SAMPLE_SEED = 148                                 # 見本の種（探索で選んだもの: 最初に止まるのが101秒目、合流位置の約42m後ろ、150秒で72台）
WIDE_SEED = 7
SEED_REF = 777                                    # 画面の数字と同じ丸めになるかを確かめる、別の乱数の1万本


def _w_dt(args):
    seed, R, dt = args
    r = sim(R, seed, dur=float(WINDOW), dt=dt)
    return r["cnt_sec"][:, WINDOW].astype(np.float64)


def _stats(m):
    c = m["cnt_sec"][:, WINDOW].astype(int)
    return dict(mean=float(c.mean()), zero=int((c == 0).sum()), p10=float((c >= 10).mean() * 100), mn=int(c.min()),
                mx=int(c.max()))


def _rounded(st):
    return (int(math.floor(st["mean"] + 0.5)), int(math.floor(st["p10"] + 0.5)))


def compute_data():
    """画面に出す1万本（別の乱数の1万本と同じ丸めになる種を選ぶ）、対照、車間を広げた1万本、波の速さ、時間刻みの確認"""
    ref = run_set("merge", SEED_REF)
    st_ref = _stats(ref)
    for seed in range(1, 30):
        m = run_set("merge", seed)
        st = _stats(m)
        if _rounded(st) == _rounded(st_ref):
            break
    else:
        raise SystemExit("丸めが別の乱数の1万本と一致する種が見つからない")
    ctl = run_set("control", 2)
    wid = run_set("wide", 3)
    wave = run_wave()
    with _pool() as ex:
        c1 = np.concatenate(list(ex.map(_w_dt, [(900 + i, 100, 0.1) for i in range(3)])))
        c2 = np.concatenate(list(ex.map(_w_dt, [(900 + i, 100, 0.05) for i in range(3)])))
    d = dict(seed=seed, ref_mean=st_ref["mean"], ref_p10=st_ref["p10"], ref_zero=st_ref["zero"],
             dt_a=float(c1.mean()), dt_b=float(c2.mean()), wave_A=wave["A"], wave_dt=wave["dt_mean"], wave_sp=wave["sp_mean"],
             wave_nB=wave["nB"])
    for k, v in m.items():
        d["m_" + k] = v
    for k, v in ctl.items():
        d["c_" + k] = v
    for k, v in wid.items():
        d["w_" + k] = v
    np.savez(OUT / "v3_data.npz", **d)
    return d


DATA = None


def data():
    global DATA
    if DATA is None:
        OUT.mkdir(parents=True, exist_ok=True)
        f = OUT / "v3_data.npz"
        if not f.exists():
            compute_data()
        z = np.load(f)
        DATA = {k: z[k] for k in z.files}
        DATA["cnt"] = DATA["m_cnt_sec"][:, WINDOW].astype(int)
    return DATA


def _sample_file(name):
    return OUT / f"v3_sample_{name}.npz"


def _load_sample(name, seed, n, dur, T):
    f = _sample_file(name)
    if not f.exists():
        rec = make_sample(seed, n=n, dur=dur, T=T)
        np.savez(f, **rec)
    z = np.load(f)
    return Smp({k: z[k] for k in z.files}, n)


_SM = {}


def SM(name="main"):
    if name not in _SM:
        _SM[name] = _load_sample("main", SAMPLE_SEED, N_SAMPLE, 400.0, None) if name == "main" else \
            _load_sample("wide", WIDE_SEED, 240, 160.0, T_WIDE)
    return _SM[name]


def kmh(x):
    return int(math.floor(abs(x) * KMH + 0.5))


def head_speed():
    """渋滞の先頭が後ろへ進む速さ（m/s、負）。A: 先頭の位置の傾き  B: 動き出しの間隔と車の間隔"""
    d = data()
    return float(np.mean(d["wave_A"])), -float(d["wave_sp"]) / float(d["wave_dt"])


def car_speed():
    """平常時（合流なし）の車の平均の速さ（m/s）"""
    return float(np.mean(data()["c_vmean_pre"]))


if __name__ == "__main__" and "--compute" in sys.argv:
    import time
    t0 = time.time()
    d = data()
    c = d["cnt"]
    print(f"計算 {time.time() - t0:.0f}秒  種={int(d['seed'])}  平均 {c.mean():.2f}台  0台 {(c == 0).sum()}本  最少 {c.min()} 最多 {c.max()}  別の乱数: 平均 {float(d['ref_mean']):.2f}")
    print("車の平均時速(対照)", car_speed() * KMH, " 先頭の速さ A/B", [x * KMH for x in head_speed()])
    print("ブレーキ: ", d["m_vF0"].mean() * KMH, "→", d["m_vF2"].mean() * KMH, "最低", d["m_vFmin"].mean() * KMH)
    print("対照 止まった車の合計", int(d["c_cnt_sec"][:, WINDOW].sum()), " 広い車間", int(d["w_cnt_sec"][:, WINDOW].sum()))
    print("dt", d["dt_a"], d["dt_b"], "mingap", d["m_mingap"].min(), d["c_mingap"].min(), d["w_mingap"].min())
    sm = SM()
    print("見本 t1", sm.t1, "x1", sm.x_first(), "台数", sm.count_at(WINDOW))


# ---------- 時間割（表示の秒） ----------
T_MERGE = 2.6                                     # 合流（シミュレーションの時刻 0）
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_FS_D = 11.0                                     # 見本で最初に止まる車が出る（表示の秒）
T_G0 = 14.0                                       # 1万本のグリッドへ
T_GC0 = T_G0 + 0.5
GRID_DUR = 4.6                                    # グリッドは 150秒ぶんを 4.6 秒で（1秒に約33秒）
T_G_END = T_GC0 + GRID_DUR
T_G_RES = T_G_END + 0.3
T_S0 = T_G_RES + 3.0                              # 驚き: 道を引く
S_DUR = 5.6
T_TW = T_S0 + S_DUR                               # ひねり「車間を広くしたら？」
TW_BANNER = 2.4
T_TW_RUN = T_TW + TW_BANNER
TW_DUR = 3.4
T_TW_RES = T_TW_RUN + 1.3
T_NAME = T_TW_RUN + TW_DUR + 0.1
T_Q = T_NAME + 2.5
DURATION = T_Q + 3.6

BIG_Q = "ブレーキ1回で、何台止まる？"
DETAIL = "高速の合流。1台がちょっとブレーキ"
LABELS = ["0台", "数台", "数十台"]


# ---------- 早送り（表示の秒 → シミュレーションの秒） ----------
_WARP = {}


def _warp_main():
    if "m" not in _WARP:
        from scipy.interpolate import PchipInterpolator
        t1 = SM().t1
        _WARP["m"] = PchipInterpolator([0.0, T_MERGE, 5.0, T_GO, T_FS_D, T_G0], [-4.0, 0.0, 5.0, 30.0, t1, float(WINDOW)])
        _WARP["w"] = PchipInterpolator([0.0, 1.0, TW_DUR + 0.3], [-4.0, 2.0, float(WINDOW)])
    return _WARP["m"], _WARP["w"]


S_SUR_END = 290.0


def sim_time(d):
    wm, ww = _warp_main()
    if d < T_S0:
        return float(wm(min(max(d, 0.0), T_G0)))
    if d < T_TW_RUN:
        return float(WINDOW + (S_SUR_END - WINDOW) * clamp01((d - T_S0) / S_DUR))
    if d < T_NAME:
        return float(ww(min(max(d - T_TW_RUN, 0.0), TW_DUR + 0.3)))
    return S_SUR_END + 12.0 * (d - T_NAME)


def sim_speed(d):
    return abs(sim_time(d + 0.02) - sim_time(d - 0.02)) / 0.04


# ---------- カメラ（地面に固定。合流位置が基準） ----------
CAM_FAR = (0.55, 830.0, 790.0)                    # 驚き・名前・締め: 道を引いて長く（約1.8km）
CAM_WIDE = (3.2, 640.0, 790.0)                    # ひねり: 車間が広い
ROAD_NEAR, ROAD_MAIN = 640.0, 790.0


S_NEAR = 13.0                                     # 冒頭の縮尺（px/m）。車5m=65px・車間16m=208px の実比率。画面に約4台（2026-10-07 ユーザー「さらに寄る」）
PX_NEAR = 760.0                                   # 冒頭の合流位置のx（左に約58m・右に約25m映す）
S_MID = 1.6                                       # 答え合わせ1で引いたあとの縮尺


def cam_main(d):
    e = ease((d - (T_GO - 0.2)) / 1.4)
    return S_NEAR * (S_MID / S_NEAR) ** e, PX_NEAR + (760.0 - PX_NEAR) * e, ROAD_NEAR + (ROAD_MAIN - ROAD_NEAR) * ease((d - T_MOVE) / 0.4)


def world_params(d):
    """この時刻に出す道: (見本, sim の秒, カメラ, 不透明度, 種類) か None"""
    if d < T_G0 + 0.3:
        return SM(), sim_time(d), cam_main(d), 1 - ease((d - T_G0) / 0.3), "main"
    if d < T_S0:
        return None
    if d < T_TW:
        return SM(), sim_time(d), CAM_FAR, ease_out((d - T_S0) / 0.3), "far"
    if d < T_TW_RUN:
        return SM(), S_SUR_END, CAM_FAR, 1 - 0.65 * ease((d - T_TW) / 0.3), "far"
    if d < T_NAME:
        return SM("wide"), sim_time(d), CAM_WIDE, ease_out((d - T_TW_RUN) / 0.3), "wide"
    q = ease_out((d - T_Q) / 0.35) if d >= T_Q else 0.0
    return SM(), sim_time(d), CAM_FAR, ease_out((d - T_NAME) / 0.3) * (1 - 0.65 * q), "far"


# ---------- 絵: 車・道 ----------
CAR_COLS = ["#bcd6f3", "#cfe8bd", "#fbf3d0", "#f6d3b3", "#d9cdee"]
MERGE_COL = "#f7c873"
LC, WC = 29.0, 16.0                               # 車の絵の大きさ（ローカル座標）
RAMP_LEN = 80.0                                   # 合流車線が本線に入っていく長さ（m）
_JIT = np.random.default_rng(7).normal(0, 0.6, (700, 12))


def car_scale(scale):
    """ペンの丸などの大きさの基準（絵の車の大きさではない）"""
    return float(min(2.2, max(0.7, 2.2 * (scale / 4.0) ** 0.45)))


def car_cs(scale):
    """車の絵の拡大率。車の長さ5mをそのまま px にする（LC=29 が5m）"""
    return 5.0 * scale / LC


def lane_w(scale):
    """道（1車線）の太さ。寄りでは車の絵に合わせ、引くと一定"""
    return 34.0 + (10.0 + 36.0 * clamp01((scale - 7.0) / 6.0)) * w_car(scale)   # 寄り（13px/m）では約2倍の太さ 80px


def w_car(scale):
    """車の絵（car_h）の濃さ。寄り＝1、引き＝0（短い線で描く）。間は交差させる"""
    return clamp01((scale - 3.6) / 1.6)


def car_h(ctx, x, y, col, lamp, j, cs, a=1.0, stop_w=0.0, ang=0.0):
    """横から見た車（ペンの少し揺れた線＋うすい塗り）。右向き。止まっている車は赤く塗る。大きさは実際の比率（長さ5m）"""
    jt = _JIT[j % len(_JIT)]
    Lc, Wc = LC, WC
    ctx.save()
    ctx.translate(x, y)
    if ang:
        ctx.rotate(ang)
    ctx.scale(cs, cs)
    pts = [(-Lc / 2 + jt[0], -Wc / 2 + jt[1]), (Lc / 2 - 6 + jt[2], -Wc / 2 + jt[3]), (Lc / 2 + jt[4], -Wc / 2 + 3.5),
           (Lc / 2 + jt[5], Wc / 2 - 3.5), (Lc / 2 - 6 + jt[6], Wc / 2 + jt[7]), (-Lc / 2 + jt[8], Wc / 2 + jt[9])]
    ctx.move_to(*pts[0])
    for p_ in pts[1:]:
        ctx.line_to(*p_)
    ctx.close_path()
    c0, c1 = hexrgb(col), hexrgb(CAR_RED)
    cc = [c0[i] * (1 - stop_w) + c1[i] * stop_w for i in range(3)]
    ctx.set_source_rgba(cc[0], cc[1], cc[2], a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(2.3 / max(cs, 0.9))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    if Lc * cs > 24:
        ctx.set_source_rgba(*hexrgb("#8fb4de", a))                      # フロントガラス・リアガラス
        core.rrect(ctx, Lc / 2 - 12, -Wc / 2 + 2.6, 6, Wc - 5.2, 1.5)
        ctx.fill()
        core.rrect(ctx, -Lc / 2 + 3.5, -Wc / 2 + 3, 4.2, Wc - 6, 1.2)
        ctx.fill()
    if lamp:                                                              # ブレーキランプ（後ろが赤く光る）
        if cs >= 1.0:                                                     # 光のにじみは近くで見るときだけ
            g = cairo.RadialGradient(-Lc / 2 - 2, 0, 1, -Lc / 2 - 2, 0, 24)
            g.add_color_stop_rgba(0, *hexrgb("#ff3b30")[:3], 0.8 * a)
            g.add_color_stop_rgba(1, *hexrgb("#ff3b30")[:3], 0.0)
            ctx.set_source(g)
            ctx.arc(-Lc / 2 - 2, 0, 24, 0, 2 * math.pi)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb("#e5322d", a))
        for sy in (-1, 1):
            ctx.rectangle(-Lc / 2 - 0.5, sy * (Wc / 2 - 3.6) - 1.8, 3.6, 3.6)
            ctx.fill()
    ctx.restore()


def draw_road(ctx, y, rw, a, scale, px0, ramp_a, mark_a, hr):
    def band(yc, wd, col, al):
        ctx.rectangle(-10, yc - wd / 2, W + 20, wd)
        ctx.set_source_rgba(*hexrgb(col, al * a))
        ctx.fill()
    if ramp_a > 0:                                                        # 合流車線（本線の下から斜めに入る）
        xs = np.arange(-900.0, 1.0, 4.0)
        off = hr * (1 - np.array([ease((x_ + RAMP_LEN) / RAMP_LEN) for x_ in xs]))
        for wd, col, al in ((rw + 6, "#5b6a86", 0.75), (rw, "#e6ecf4", 1.0)):
            ctx.set_line_width(wd)
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.move_to(px0 + scale * xs[0], y + off[0])
            for x_, o_ in zip(xs[1:], off[1:]):
                ctx.line_to(px0 + scale * x_, y + o_)
            ctx.set_source_rgba(*hexrgb(col, al * a * ramp_a))
            ctx.stroke()
    band(y, rw + 6, "#5b6a86", 0.75)
    band(y, rw, "#e6ecf4", 1.0)
    step = 100.0 if scale >= 1.2 else 200.0                              # 地面の目印（キロポスト）。道が動いていないことが分かるように
    k0 = int(math.floor((0 - px0) / scale / step)) - 1
    k1 = int(math.ceil((W - px0) / scale / step)) + 1
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
    ctx.set_line_width(2.5)
    for k in range(k0, k1 + 1):
        xx = px0 + scale * k * step
        ctx.move_to(xx, y + rw / 2 + 6)
        ctx.line_to(xx, y + rw / 2 + 15)
        ctx.stroke()
    if mark_a > 0:                                                        # 合流地点の目印
        ctx.set_source_rgba(*hexrgb(RED, 0.85 * a * mark_a))
        ctx.set_line_width(3)
        ctx.set_dash([9, 8])
        ctx.move_to(px0, y - rw / 2 - 30)
        ctx.line_to(px0, y + rw / 2 + 30)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "合流地点", px0, y + rw / 2 + 48, 28, RED, alpha=a * mark_a, bold=False)


LINE_RUN = ("#2b3f78", "#79b4e8")                 # 走っている車（紺／水色）
LINE_H = 14.0                                     # 線の太さ（px）


def line_cars(ctx, smp, s, cam, y, hi=None, ramp=False, hr=100.0, a=1.0, spd=1.0):
    """引いた縮尺用。車を実際の比率（長さ5m）の短い角丸の線で描く。走っている車は紺／水色、止まっている車（時速5km以下）は赤"""
    scale, px0, _ = cam
    x, v, lamp = smp.state(s)
    xw = smp.wrap(x)
    px = px0 + scale * (xw - 2.5)                                         # x は車の先頭。車の中心は2.5m後ろ
    L = max(5.0 * scale, 3.0)
    stopw = np.clip((1.9 - v) / (1.9 - STOP_KMH / 3.6), 0, 1)
    idx = np.where((px > -40) & (px < W + 40))[0]
    idx = idx[np.argsort(px[idx])]
    M = smp.fi + 1
    for j in idx:
        yy, ang, hh = y, 0.0, LINE_H
        base = LINE_RUN[j % 2]
        if j == M and ramp:
            base = MERGE_COL
            u = min(max((xw[j] + RAMP_LEN) / RAMP_LEN, 0.0), 1.0)
            yy = y + hr * (1 - ease(u))
            ang = math.atan2(-hr * 6 * u * (1 - u) / RAMP_LEN, scale) if 0 < u < 1 else 0.0
        ll = L
        if hi is not None and j == hi:
            base, hh, ll = BLUE, LINE_H + 8, max(L, 8.0)
            rg = 40.0
            g = cairo.RadialGradient(px[j], y, 5, px[j], y, rg)
            g.add_color_stop_rgba(0, *hexrgb(MARKER)[:3], 0.9 * a)
            g.add_color_stop_rgba(1, *hexrgb(MARKER)[:3], 0.0)
            ctx.set_source(g)
            ctx.arc(px[j], y, rg, 0, 2 * math.pi)
            ctx.fill()
            sw = 0.0
        else:
            sw = float(stopw[j])
        c0, c1 = hexrgb(base), hexrgb(CAR_RED)
        cc = [c0[i] * (1 - sw) + c1[i] * sw for i in range(3)]
        sm_ = min(0.8 * float(v[j]) * spd * scale / FPS, 26.0)           # 早送り中は進んだぶんだけ後ろへ尾を引く（コマごとの点にならないように）
        if sm_ < 1.5 or hi is not None and j == hi:
            sm_ = 0.0 if sm_ < 1.5 else min(sm_, 14.0)
        ctx.save()
        ctx.translate(px[j], yy)
        if ang:
            ctx.rotate(ang)
        if sm_ > 0:
            g = cairo.LinearGradient(-ll / 2 - sm_, 0, ll / 2, 0)
            g.add_color_stop_rgba(0, cc[0], cc[1], cc[2], 0.0)
            g.add_color_stop_rgba(1, cc[0], cc[1], cc[2], a)
            ctx.set_source(g)
            core.rrect(ctx, -ll / 2 - sm_, -hh / 2, ll + sm_, hh, min(ll, hh) / 2)
        else:
            core.rrect(ctx, -ll / 2, -hh / 2, ll, hh, min(ll, hh) / 2)
            ctx.set_source_rgba(cc[0], cc[1], cc[2], a)
        ctx.fill()
        ctx.restore()


def cars_layer(ctx, smp, s, cam, y, hi=None, ramp=False, hr=100.0, spd=1.0):
    scale, px0, _ = cam
    wc = w_car(scale)
    if wc < 1.0:
        line_cars(ctx, smp, s, cam, y, hi, ramp, hr, 1.0 - wc, spd)
    if wc <= 0.0:
        return
    x, v, lamp = smp.state(s)
    xw = smp.wrap(x)
    cs = car_cs(scale)
    px = px0 + scale * (xw - 2.5)
    stopw = np.clip((2.5 - v) / (2.5 - STOP_KMH / 3.6), 0, 1)
    idx = np.where((px > -70) & (px < W + 70))[0]
    idx = idx[np.argsort(px[idx])]
    M = smp.fi + 1
    for j in idx:
        yy, ang = y, 0.0
        col = CAR_COLS[j % 5]
        if j == M:
            col = MERGE_COL
            if ramp:
                u = min(max((xw[j] + RAMP_LEN) / RAMP_LEN, 0.0), 1.0)
                yy = y + hr * (1 - ease(u))
                ang = math.atan2(-hr * 6 * u * (1 - u) / RAMP_LEN, scale) if 0 < u < 1 else 0.0
        if hi is not None and j == hi:
            col = BLUE
        car_h(ctx, px[j], yy, col, bool(lamp[j]), int(j), cs, wc, 0.0 if (hi is not None and j == hi) else float(stopw[j]), ang)


def pen_arrow(ctx, x0, y0, x1, y1, color, seed, width=6, alpha=1.0):
    note.pen_line(ctx, x0, y0, x1, y1, color, seed=seed, width=width, alpha=alpha)
    ang = math.atan2(y1 - y0, x1 - x0)
    for sgn in (-1, 1):
        a2 = ang + math.pi + sgn * 0.5
        note.pen_line(ctx, x1, y1, x1 + 24 * math.cos(a2), y1 + 24 * math.sin(a2), color, seed=seed + 3 * sgn, width=width,
                      alpha=alpha)


_HI = {}


def hi_car():
    """驚きの場面で追う1台（青）: 止まっていて、150秒のあと最初に動き出す車"""
    if "hi" not in _HI:
        sm = SM()
        cand = [j for j in range(sm.n) if sm.FS[j] <= WINDOW and sm.RT[j] > WINDOW + 2]
        _HI["hi"] = min(cand, key=lambda j: sm.RT[j])
    return _HI["hi"]


def draw_world(ctx, d):
    wp = world_params(d)
    if wp is None:
        return
    smp, s, cam, al, kind = wp
    if al <= 0:
        return
    scale, px0, y = cam
    cs = car_scale(scale)
    rw = lane_w(scale)
    hr = 1.45 * rw
    ramp_a = clamp01((scale - 2.0) / 1.2) * (clamp01(1 - (s - 3.0) / 3.0) if kind == "wide" else 1.0)
    mark_a = clamp01((2.2 - scale) / 0.6) if kind in ("main", "far") else 0.0
    draw_road(ctx, y, rw, al, scale, px0, ramp_a, mark_a, hr)
    spd = sim_speed(d)
    nsub = 1 if spd < 6 else (2 if spd < 15 else (3 if spd < 30 else 4))
    nsub = max(nsub, min(5, int(math.ceil(spd * 22.0 * scale * 0.6 / FPS / 9.0))))   # 寄りで速く流れるときも、にじみをなめらかに
    if w_car(scale) <= 0.0:
        nsub = 1                                                          # 引いた絵（線）は尾を引く形でにじませる（コマを重ねない）
    span = spd * 0.6 / FPS
    hi = hi_car() if (kind == "far" and T_S0 <= d < T_TW + 0.3) else None
    ctx.push_group()
    for i in range(nsub):
        si = s + (((i / (nsub - 1)) - 0.5) * span if nsub > 1 else 0.0)
        ctx.push_group()
        cars_layer(ctx, smp, si, cam, y, hi, ramp=ramp_a > 0, hr=hr, spd=spd)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1.0 / (i + 1))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(al)
    # --- 重ねる丸（ペン）
    if kind == "main" and d >= T_FS_D - 0.05:
        px = px0 + scale * smp.x_first()                                  # 最初に止まった場所（地面に固定）
        pr = clamp01((d - T_FS_D) / 0.8)
        fa = al * (1 - ease((d - T_FS_D - 2.3) / 0.7))
        note.pen_circle(ctx, px, y, 34 * cs + 14, 18 * cs + 16, RED, seed=9, width=5, progress=pr, alpha=fa)
    if kind == "far" and T_S0 <= d < T_TW + 0.3:
        jam = ease_out((d - T_S0) / 0.5) * al
        for g_ in range(3, -1, -1):
            hh = smp.head_at(s - 14.0 * g_)
            if hh is None:
                continue
            a_ = jam * (1.0 if g_ == 0 else 0.42 / g_)
            note.pen_circle(ctx, px0 + scale * hh, y, 34, 36, INK, seed=5, width=6 if g_ == 0 else 3.5, alpha=a_)
    if kind == "far" and T_NAME <= d:
        q = ease_out((d - T_Q) / 0.35) if d >= T_Q else 0.0
        hh = smp.head_at(s)
        if hh is not None:
            note.pen_circle(ctx, px0 + scale * hh, y, 34, 36, INK, seed=5, width=6,
                            alpha=al * ease_out((d - T_NAME) / 0.5) * (1 - q))


# ---------- 冒頭・上のブロック ----------

class SIntro(note.Intro):
    """この回だけの冒頭。上半分に高速道路（0秒目から走る）、下に大きな問い。カウントダウンの間に止まる車は出ない"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL                              # 音（ベル）を前提の行に合わせる
    T_CD = T_CD
    T_MOVE = T_GO - 0.4
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 64
        w = core.text_width(BIG_Q, sz)
        if w > 860:
            sz *= 860 / w
            w = 860
        text(ctx, BIG_Q, 570, 950, sz, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 997, 570 + w / 2 + 6, 991, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 1060, 36, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1150 + i * 88
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 56, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 775, 1145, 52, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 785, 1262, 72, 68, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(785, 1262)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 106, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        """冒頭が終わったあと、上に小さく: 問い1行・下線・三択を横1列。答えは赤丸、ほかは取り消し線"""
        sz = 54
        w = core.text_width(BIG_Q, sz)
        if w > 850:
            sz *= 850 / w
            w = 850
        text(ctx, BIG_Q, 540, 425, sz, INK, alpha=m)
        note.pen_line(ctx, 540 - w / 2 - 6, 462, 540 + w / 2 + 6, 458, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        for i, v in enumerate(self.labels):
            cx, y = 540 + (i - 1) * 300, 520
            ok = i == self.correct
            a = m * (1 - 0.55 * rev * (not ok))
            vs = 46
            vw = core.text_width(v, vs)
            if 64 + vw > 270:
                vs *= (270 - 64) / vw
                vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=a)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=a)
            text(ctx, v, x0 + 64, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=a)
            if ok:
                note.pen_circle(ctx, cx, y, (64 + vw) / 2 + 30, 42, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 72 + vw, y - 2, PENCIL, seed=i + 40, width=4,
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


INTRO = SIntro(["ブレーキ1回で、", "何台止まる？"], LABELS, correct=2, msg="", rule=None)


# ---------- 1万本のグリッド ----------
CELL, GGAP = 7, 1
GW = 100 * CELL
GX0, GY0 = 540 - GW // 2, 585
_PERM = np.random.default_rng(11).permutation(N_TRIALS)           # 回が画面に並ぶ位置（ばらばらに）
_LUT_PTS = [(0, CELL_BLUE), (1, "#f6e3bc"), (20, "#f5b66e"), (45, "#ee6a3c"), (80, "#d92b2b")]
_LUT = None


def lut():
    """止まった台数 → 色（BGRA）。0台＝水色、多いほど赤"""
    global _LUT
    if _LUT is None:
        out = np.zeros((256, 4), np.uint8)
        pts = [(c, hexrgb(col)) for c, col in _LUT_PTS]
        for c in range(256):
            for (c0, k0), (c1, k1) in zip(pts[:-1], pts[1:]):
                if c0 <= c <= c1:
                    u = (c - c0) / (c1 - c0)
                    rgb = [k0[i] * (1 - u) + k1[i] * u for i in range(3)]
                    break
            else:
                rgb = pts[-1][1][:3]
            out[c] = [int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255), 255]
        _LUT = out
    return _LUT


def lut_rgb(c):
    z = lut()[min(max(int(c), 0), 255)]
    return "#%02x%02x%02x" % (z[2], z[1], z[0])


def draw_grid(ctx, t, cnt_sec, dim=0.0):
    """100×100 のマス。1マス＝1回。止まった台数で色が濃くなる（0台＝水色、多いほど赤）"""
    u = clamp01((t - T_GC0) / GRID_DUR)
    sec = int(u * WINDOW)
    cells = np.empty((N_TRIALS, 4), np.uint8)
    cells[_PERM] = lut()[cnt_sec[:, sec]]
    grid = cells.reshape(100, 100, 4)
    wipe = clamp01((t - T_G0) / 0.45)
    surf, _keep = grid_image(grid, cell=CELL, gap_color=(0, 0, 0, 0), gap=GGAP)
    ctx.save()
    ctx.rectangle(GX0, GY0, GW, GW * wipe)
    ctx.clip()
    ctx.set_source_surface(surf, GX0, GY0)
    ctx.paint_with_alpha(1 - 0.55 * dim)
    ctx.restore()
    return sec, float(cnt_sec[:, sec].mean())


def number_row(ctx, parts, y, a, size=44, cx=540):
    """[(字, 色), ...] を1行に並べて中央にそろえる。数字だけ色を変える"""
    ws = [core.text_width(s, size) for s, _ in parts]
    x = cx - sum(ws) / 2
    for (s, col), w in zip(parts, ws):
        text(ctx, s, x, y, size, col, align="left", alpha=a)
        x += w


def fmt_n(n):
    return f"{n:,}"


# ---------- 本体 ----------
GREEN = "#1f9d55"


def shown():
    """画面に出す数字（1万本すべてから）"""
    d = data()
    c = d["cnt"]
    kA, kB = kmh(car_speed()), kmh(head_speed()[0])
    return dict(mean=int(math.floor(c.mean() + 0.5)), zero=int((c == 0).sum()), kA=kA, kB=kB,
                gap0=int(math.floor(eq_gap(P0) + 0.5)), gap1=int(math.floor(eq_gap(P0, T_WIDE) + 0.5)),
                wide_zero=int((d["w_cnt_sec"][:, WINDOW] == 0).sum()), wide_n=len(d["w_cnt_sec"]))


def clock(ctx, d, a=1.0):
    """「ブレーキから ○秒」。早送りをしているので、いまが合流から何秒後かを出す"""
    s = sim_time(d)
    if s < 0:
        return
    e = ease((d - T_MOVE) / 0.4)
    y = 855 + 70 * e
    number_row(ctx, [("ブレーキから ", INK), (f"{int(s)}", BLUE), ("秒", INK)], y, a, size=36)


def body(ctx, t):
    sh = shown()
    sm = SM()
    # --- 冒頭: 合流して後ろの車がブレーキ
    if t < T_G0 + 0.3:
        if T_MERGE - 0.1 <= t < T_GO + 0.4:
            k = ease_out((t - T_MERGE + 0.1) / 0.25) * (1 - ease((t - T_MERGE - 2.5) / 0.4)) * (1 - ease((t - T_GO + 0.4) / 0.3))
            note.sticky(ctx, "1台が ちょっとブレーキ", 580, 520, 40, "yellow", fg=RED, a=k, tilt=0.01)
        if t >= T_MERGE and t < T_G0:
            clock(ctx, t, 1 - ease((t - T_G0 + 0.3) / 0.3))
    # --- 答え合わせ1: その場で止まる車が出て、列が左へ伸びる
    if T_FS_D - 0.05 <= t < T_G0 + 0.3:
        out = 1 - ease((t - T_G0) / 0.3)
        k = ease_out((t - T_FS_D) / 0.3) * out
        note.sticky(ctx, "誰もぶつかって\nいないのに止まった", 520, 645, 42, "pink", fg=RED, a=k, tilt=-0.01)
        n = sm.count_at(sim_time(t))
        number_row(ctx, [("止まった車 ", INK), (f"{n}", RED), ("台", INK)], 1010, k, size=44)
        note.legend(ctx, [(CAR_RED, "赤＝止まっている車（時速5km以下）")], 1285, 30)
    # --- 答え合わせ2: 1万回
    if T_G0 <= t < T_S0 + 0.3:
        dim = clamp01((t - T_G_RES) / 0.4)
        out = 1 - ease((t - T_S0) / 0.3)
        ctx.push_group()
        sec, mean_t = draw_grid(ctx, t, data()["m_cnt_sec"], dim)
        number_row(ctx, [("ブレーキから ", INK), (f"{sec}", BLUE), (f"秒 / {WINDOW}秒", INK)], 1330, 1.0, size=40)
        number_row(ctx, [("止まった車 平均 ", INK), (f"{int(math.floor(mean_t + 0.5))}", RED), ("台", INK)], 1383, 1.0, size=44)
        note.legend(ctx, [(lut_rgb(0), "0台"), (lut_rgb(20), "20台"), (lut_rgb(45), "45台"), (lut_rgb(80), "80台")], 1428, 26, gap=36)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(out)
        if t >= T_G_RES:
            k = ease_out((t - T_G_RES) / 0.3) * out
            note.sticky(ctx, f"平均 {sh['mean']}台が止まった", 540, 830, 54, "pink", fg=RED, a=k, tilt=-0.015)
            k2 = ease_out((t - T_G_RES - 0.4) / 0.3) * out
            note.sticky(ctx, f"1万本のうち 0台は {sh['zero']}本", 540, 965, 44, "yellow", a=k2, tilt=0.012)
        return
    # --- 驚き: 車は前へ、渋滞は後ろへ
    if T_S0 <= t < T_TW + 0.3:
        out = 1 - ease((t - T_TW) / 0.3)
        k = ease_out((t - T_S0 - 0.8) / 0.3) * out
        note.sticky(ctx, "車は前へ、渋滞は後ろへ", 520, 645, 46, "pink", fg=RED, a=k, tilt=-0.015)
        clock(ctx, t, out)
        t1, t2 = T_S0 + 2.0, T_S0 + 3.2
        if t >= t1:
            number_row(ctx, [("車 → 時速", INK), (f"{sh['kA']}", BLUE), ("km", INK)], 1100,
                       ease_out((t - t1) / 0.3) * out)
        if t >= t2:
            number_row(ctx, [("渋滞 ← 時速", INK), (f"{sh['kB']}", RED), ("km", INK)], 1170,
                       ease_out((t - t2) / 0.3) * out)
        note.legend(ctx, [(BLUE, "追う1台"), (CAR_RED, "止まっている車")], 1285, 28)
        return
    # --- ひねり: 車間を広くしたら？
    if T_TW <= t < T_NAME:
        if t < T_TW_RUN:
            a = ease_out((t - T_TW) / 0.25)
            note.banner(ctx, "車間を広くしたら？", 520, 645, a=a, t_rel=t - T_TW, size=56)
            return
        clock(ctx, t, 1.0)
        number_row(ctx, [("車間 ", INK), (f"{sh['gap0']}m", BLUE), (" → ", INK), (f"{sh['gap1']}m", GREEN)], 1020, 1.0, size=44)
        if t >= T_TW_RES:
            b = ease_out((t - T_TW_RES) / 0.3)
            note.sticky(ctx, "止まる車は0台", 520, 645, 50, "mint", a=b, tilt=-0.015)
            number_row(ctx, [("止まった車 平均 ", INK), (f"{sh['mean']}台", "#8a93a6"), (" → ", INK), ("0台", GREEN)], 1100, b, size=38)
            number_row(ctx, [("1万回のうち ", INK), (f"{fmt_n(sh['wide_n'] - sh['wide_zero'])}", GREEN), ("回が止まった", INK)], 1165, b, size=38)
        note.legend(ctx, [(CAR_RED, "止まっている車")], 1285, 28)
        return
    # --- 名前・締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if t >= T_NAME and q < 1:
        b = ease_out((t - T_NAME) / 0.3) * (1 - q)
        note.sticky(ctx, "これを「自然渋滞」と呼ぶ", 520, 645, 50, "mint", a=b, tilt=-0.015)
        text(ctx, "（渋滞の波、とも言う）", 540, 1000, 34, INK, bold=False, alpha=b)
    if q > 0:
        note.sticky(ctx, "ブレーキは1回なのに、\nなんで止まる車が増えていくの？", 520, 700, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 520, 880, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    draw_world(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_G_RES + 0.3)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def engine_hum(dur, f0=70.0):
    t = _t(dur)
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.01 * t)) * 0.25 * np.minimum(1, t * 8)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(110.0, 164.8, 220.0, 277.2)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, engine_hum(T_GO), 0.25, bgm=True)
    mx.add(T_MERGE, blip(330.0, 0.25), 0.3)                          # 合流・ブレーキランプ
    mx.add(T_FS_D, blip(262.0, 0.3), 0.4)                            # 1台が止まった
    mx.add(T_FS_D + 0.1, bell(659.3, 1.2), 0.4)
    mx.add(T_G0 - 0.6, riser(0.9), 0.5)
    beat(mx, T_GC0, T_G_END, bpm=124, vol=0.5, accel=True)
    cs = data()["m_cnt_sec"]
    t10 = np.argmax(cs >= 10, axis=1).astype(float)                  # 各回が10台を超えた秒（マスが赤みを帯びる）
    rng = np.random.default_rng(3)
    for b in range(int(WINDOW * 2)):                                 # かすかなクリック（赤みを帯びる回の数に応じて）
        n = int(((t10 > b / 2) & (t10 <= (b + 1) / 2)).sum())
        if n:
            mx.add(T_GC0 + (b / 2) / WINDOW * GRID_DUR, tick(float(rng.uniform(1600, 3200)), 0.03), 0.04 + 0.1 * min(1.0, n / 400))
    mx.add(T_G_RES, thump(), 0.7)
    mx.add(T_G_RES + 0.15, chord([261.6, 329.6, 392.0], 1.6), 0.5)
    mx.add(T_S0 + 2.0, blip(784.0, 0.15), 0.35)
    mx.add(T_S0 + 3.2, blip(659.3, 0.15), 0.35)
    mx.add(T_S0 + 0.8, bell(880.0, 1.0), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)
    mx.add(T_TW_RES, bell(1046.5), 0.5)
    mx.add(T_NAME, chord([392.0, 493.9, 587.3], 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    d = data()
    c = d["cnt"]
    cc = d["c_cnt_sec"][:, WINDOW].astype(int)
    cw = d["w_cnt_sec"][:, WINDOW].astype(int)
    hA, hB = head_speed()
    sm = SM()
    sw = SM("wide")
    ref = (int(math.floor(float(d["ref_mean"]) + 0.5)), int(math.floor(float(d["ref_p10"]) + 0.5)))
    me = (int(math.floor(c.mean() + 0.5)), int(math.floor((c >= 10).mean() * 100 + 0.5)))
    rank = float((c < sm.count_at(WINDOW)).mean())
    t_first_d = T_FS_D
    checks = [
        ("合流なし（対照）1万本で止まった車の合計（台）", float(cc.sum()), 0.0, 0.0),
        ("対照: 平均時速が約80km（km/h）", car_speed() * KMH, 80.0, 1.0),
        ("時間刻み 0.1秒 と 0.05秒 で、止まった台数の平均が近い", float(d["dt_a"]), float(d["dt_b"]), 6.0),
        ("最小の車間が 0.5m 以上（衝突しない。合流・対照・広い車間）", float(min(d["m_mingap"].min(), d["c_mingap"].min(), d["w_mingap"].min()) >= 0.5), 1.0, 0.0),
        ("渋滞の先頭が後ろへ進む速さ（測り方A vs B、km/h）", hA * KMH, hB * KMH, 1.5),
        ("渋滞の先頭の向きは後ろ（負）", float(hA < 0 and hB < 0), 1.0, 0.0),
        ("画面の「平均○台」と「10台以上の割合%」（別の乱数の1万本と同じ丸め）", float(me[0] * 1000 + me[1]), float(ref[0] * 1000 + ref[1]), 0.0),
        ("答えは C（数十台＝10〜99台が99.9%以上）", float(((c >= 10) & (c <= 99)).mean() >= 0.999), 1.0, 0.0),
        ("A（0台）・B（数台）は1%未満", float(((c <= 9).mean()) < 0.01), 1.0, 0.0),
        ("車間を広げると 1万本すべてで止まった車が0台", float(cw.sum()), 0.0, 0.0),
        ("ブレーキ: 時速が約20km下がる（km/h）", float((d["m_vF0"] - d["m_vF2"]).mean() * KMH), 20.0, 0.5),
        ("見本: 最初に止まる車が出るのは、カウントダウン（0）が終わったあと（表示の秒）", float(t_first_d > T_GO + 0.3), 1.0, 0.0),
        ("見本: 最初に止まるまで、止まっている車が1台もない", float(sm.t1 > sim_time(T_GO)), 1.0, 0.0),
        ("見本: 合流位置より後ろで最初の車が止まる（m）", float(sm.x_first() < 0), 1.0, 0.0),
        ("見本: 150秒の台数が1万本の中で極端でない（10〜90%点の内側）", float(0.1 <= rank <= 0.9), 1.0, 0.0),
        ("見本: 驚きの場面のあいだ渋滞の先頭が見える", float(all(sm.head_at(s_) is not None for s_ in np.linspace(WINDOW, S_SUR_END, 30))), 1.0, 0.0),
        ("見本（広い車間）: 止まる車が1台も出ない", float(np.isinf(sw.FS).all()), 1.0, 0.0),
    ]
    check_answers(checks)


if __name__ == "__main__" and "--compute" not in sys.argv and "--search-sample2" not in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    d = data()
    c = d["cnt"]
    sh = shown()
    sm = SM()
    hA, hB = head_speed()
    print(f"種={int(d['seed'])} 見本の道 種={SAMPLE_SEED}（最初の停止 {sm.t1:.1f}秒後・合流位置の {sm.x_first():.0f}m、"
          f"表示 {T_FS_D:.2f}秒、カウントダウン終了 {T_GO:.2f}秒、見本の台数 {sm.count_at(WINDOW)}）/ 長さ={DURATION:.1f}秒")
    print(f"1万回（{WINDOW}秒・時速5km以下）: 平均 {c.mean():.2f}台（中央値 {np.median(c):.0f}、最少 {c.min()}、最多 {c.max()}）、0台 {sh['zero']}本、"
          f"1〜9台 {int(((c >= 1) & (c <= 9)).sum())}本、10〜99台 {int(((c >= 10) & (c <= 99)).sum())}本")
    print(f"  別の乱数の1万本: 平均 {float(d['ref_mean']):.2f}台 / 車 {car_speed() * KMH:.1f}km/h / 渋滞の先頭 A={hA * KMH:.2f} B={hB * KMH:.2f}km/h")
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__" and "--test-ctrl" in sys.argv:
    r = sim(200, 31, dur=500.0, brake=False)
    f = r["first"].min(1)
    print("対照 500秒 最初に止まる秒:", np.percentile(np.where(np.isfinite(f), f, 999), [0, 10, 50, 90, 100]))
