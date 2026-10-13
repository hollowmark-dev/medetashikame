"""砂時計、砂が減ると速く落ちているように感じる？ 砂1万粒の砂時計と水時計をくらべる。— 2026-10-11 作成（公開予定 10/13）

モデル（2次元）
  砂: 円板の粒1万個の DEM（離散要素法）。粒どうし・粒と壁は、重なった分だけ押し返すばね＋ダンパー（法線）と、
      クーロン摩擦つきの接線ばね（Cundall & Strack 1979 の形。摩擦係数 0.5）。粒は回転もする。重力だけで動く。
      粒の直径は 0.8〜1.2（平均1）の一様乱数（そろえると結晶のように並んでしまうため）。単位は 平均の直径 d・重さ・g。
      砂時計の形: 首の幅 8d（壁の粒の内側どうし）、胴の幅 110d、首の近くは水平から50°のじょうご、胴の高さ 160d。
      壁は直径1の動かない粒を 0.5d おきに並べたもの（でこぼこの壁なので、壁との摩擦がはたらく）。
      はじめは首に栓をして粒を上の胴にためて落ち着かせ、t=0 で栓を抜く。
      実際の長さに直すときは d=1mm とする（時間の単位 √(d/g) = 0.0101 秒）。
  水: トリチェリの法則。首から流れ出る速さ √(2gh)（h＝首から水面まで）、流量 = 縮流係数 0.61 × 穴の幅 × √(2gh)。
      容器は砂時計と同じ形（2次元・奥行き1cm として ml に直す）。水は砂と同じ高さまで入れ、
      穴の幅は「はじめの1秒に落ちる割合」が砂と同じになるように決める（同じ速さでスタートさせて、その後をくらべる）。

問い: 「砂時計、砂が減ると 速く落ちているように感じる？」（2行） A 本当に速くなる ／ B 気のせい ／ C 本当は遅くなる。
      答えは計算の前に決めた規則（answer_by_rule: 後半÷前半が ±6% の内なら B）で決める。結果は B（0.958）。水は 0.71 で遅くなる。
ひねり: 「砂を半分にしたら、時間は？」 砂5千粒の DEM を別に流す → 砂はちょうど半分。水は半分にならない。
締め: 「なんで砂は、減っても速くならないの？ → 答えは概要欄に」。

照合（check_answers）: 本体の下の run_checks を参照。
"""
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "sand-dokei"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- 砂時計の形（単位 d） ----------
D_NECK = 8.0                                      # 首の幅（内側）
B_BODY = 110.0                                    # 胴の幅（内側）
CONE = math.radians(50)                           # 首の近くのじょうごの傾き（水平から）
H_BULB = 160.0                                    # 片側の胴の高さ（首の上端から天井まで）
NECK_L = 2.0                                      # 首のまっすぐな部分の長さ
R_SHOULDER = 18.0                                 # じょうごから胴へ移る角の丸み
R_TOP = 14.0                                      # 天井の角の丸み
Y_NECK_TOP = NECK_L / 2


def profile():
    """上の胴の内側の輪郭（右半分）。首の下端 → 首の上端 → じょうご → 丸み → 胴 → 天井の丸み → 天井の真ん中"""
    pts = [(D_NECK / 2, -Y_NECK_TOP), (D_NECK / 2, Y_NECK_TOP)]
    cot = 1 / math.tan(CONE)
    yc = Y_NECK_TOP + (B_BODY / 2 - D_NECK / 2) / cot          # じょうごの線が胴の線とまじわる高さ
    pa = (B_BODY / 2 - R_SHOULDER * math.cos(CONE), yc - R_SHOULDER * math.sin(CONE))
    pc = (B_BODY / 2, yc + R_SHOULDER)
    for k in range(1, 40):
        y = Y_NECK_TOP + (pa[1] - Y_NECK_TOP) * k / 39
        pts.append((D_NECK / 2 + (y - Y_NECK_TOP) * cot, y))
    for k in range(1, 31):
        u = k / 30
        pts.append(((1 - u) ** 2 * pa[0] + 2 * u * (1 - u) * B_BODY / 2 + u * u * pc[0],
                    (1 - u) ** 2 * pa[1] + 2 * u * (1 - u) * yc + u * u * pc[1]))
    ytop = Y_NECK_TOP + H_BULB
    for k in range(1, 30):
        pts.append((B_BODY / 2, pc[1] + (ytop - R_TOP - pc[1]) * k / 29))
    for k in range(1, 16):
        a = k / 15 * math.pi / 2
        pts.append((B_BODY / 2 - R_TOP + R_TOP * math.cos(a), ytop - R_TOP + R_TOP * math.sin(a)))
    for k in range(1, 30):
        pts.append((B_BODY / 2 - R_TOP - (B_BODY / 2 - R_TOP) * k / 29, ytop))
    return np.array(pts)


def half_width(y):
    """上の胴の、高さ y（首の中心が0）での内側の半幅。天井より上は0"""
    p = profile()
    k = np.nonzero(np.diff(p[:, 1]) > 0)[0]
    ys = np.concatenate([[p[0, 1]], p[k + 1, 1]])
    xs = np.concatenate([[p[0, 0]], p[k + 1, 0]])
    return np.where(np.asarray(y) > ys[-1], 0.0, np.interp(y, ys, xs))


def _resample(poly, step):
    seg = np.diff(poly, axis=0)
    s = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
    ss = np.arange(0, s[-1] + 1e-9, step)
    return np.stack([np.interp(ss, s, poly[:, 0]), np.interp(ss, s, poly[:, 1])], 1)


def wall_disks():
    """壁の粒（直径1）の中心。輪郭から外へ 0.5 ずらした線の上に 0.5 おき。上下の胴で鏡うつし"""
    p = profile()
    g = np.gradient(p, axis=0)
    nrm = np.stack([g[:, 1], -g[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    q = _resample(p + 0.5 * nrm, 0.5)
    q = q[q[:, 0] > 0.1]                                       # 天井の真ん中は左右で重ねない
    upper = np.concatenate([q, q * [-1, 1], [[0.0, Y_NECK_TOP + H_BULB + 0.5]]])
    lower = upper * [1, -1]
    both = np.concatenate([upper, lower])
    # 首の中の重なり（上下で同じ点）を1つに
    _, u = np.unique(np.round(both, 3), axis=0, return_index=True)
    return both[np.sort(u)]


# ---------- DEM ----------
KN = 20000.0                                      # 法線のばね（重さ×g/d の 2万倍。首の上で重なりは直径の 0.1〜0.3%）
E_REST = 0.3                                      # はね返り係数
MU = 0.5                                          # すべり摩擦係数（粒どうし・粒と壁）
MU_ROLL = 0.1                                     # ころがり抵抗（砂粒は角ばっていて転がりにくい。円板にこれを足して表す）
DT_FRAC = 15                                      # 時間の刻み = ぶつかっている時間 ÷ 15
SKIN = 0.5
# 2026-10-12 1回目は KN=2000・ころがり抵抗なしで計算した。そのときは砂が減るにつれて少しずつ遅くなり、
# 1万粒のほうが5千粒より速く落ちた。やわらかい粒・すべりやすい粒では流れが高さに左右される（Pongó ら 2021）ので、
# 砂に近づけて固く・転がりにくくした


class DEM:
    """2次元の円板の DEM。粒 N 個＋動かない壁の粒。半陰的オイラー法で時間を進める。
    下の胴で止まった粒は「凍らせて」壁と同じ扱いにする（計算を軽くするため。止まった山の粒は動かないので結果は変わらない）"""

    def __init__(self, pos, rad, wall_pos, wall_rad=0.5, kn=KN, e=E_REST, mu=MU, mu_r=MU_ROLL, skin=SKIN,
                 dt_frac=DT_FRAC):
        from scipy.spatial import cKDTree       # noqa: F401（使えるか先に確かめる）
        self.N = len(pos)
        self.Nw = len(wall_pos)
        self.pos = np.concatenate([pos, wall_pos]).astype(float)
        self.vel = np.zeros_like(self.pos)
        self.w = np.zeros(len(self.pos))
        self.r = np.concatenate([rad, np.full(self.Nw, wall_rad)])
        self.m = (2 * rad) ** 2                                  # 2次元なので重さは面積（直径²）に比例
        self.I = 0.5 * self.m * rad ** 2
        self.kn, self.kt = kn, kn * 2 / 7
        lne = math.log(e)
        self.zeta = -lne / math.sqrt(math.pi ** 2 + lne ** 2)
        self.mu, self.mu_r = mu, mu_r
        self.skin = skin
        tc = math.pi / math.sqrt(kn / (self.m.min() / 2))       # いちばん軽い2粒がぶつかっている時間
        self.dt = tc / dt_frac
        self.t = 0.0
        self.active = np.ones(len(self.pos), bool)               # False ＝ 計算から外す（抜いた栓）
        self.mob = np.ones(self.N, bool)                         # False ＝ 凍らせた粒
        self.slow = np.zeros(self.N, int)
        self.freeze_below = None                                 # この高さより下で止まった粒を凍らせる（None なら凍らせない）
        self.keys = np.zeros(0, np.int64)
        self.xi = np.zeros(0)
        self.nbuild = 0
        self.ncont = np.zeros(self.N, int)
        self.rebuild()

    def rebuild(self):
        from scipy.spatial import cKDTree
        N = self.N
        if self.freeze_below is not None:
            sp = np.hypot(self.vel[:N, 0], self.vel[:N, 1])
            slow = self.mob & (sp < 0.02) & (np.abs(self.w[:N]) < 0.05) & (self.pos[:N, 1] < self.freeze_below) \
                & (self.ncont >= 2)
            self.slow = np.where(slow, self.slow + 1, 0)
            fr = self.slow >= 5
            if fr.any():
                self.mob &= ~fr
                self.vel[:N][fr] = 0.0
                self.w[:N][fr] = 0.0
        rc = 2 * self.r.max() + self.skin
        idx = np.nonzero(self.active)[0]
        pr = cKDTree(self.pos[idx]).query_pairs(rc, output_type="ndarray")
        i, j = idx[pr[:, 0]], idx[pr[:, 1]]
        i, j = np.minimum(i, j), np.maximum(i, j)
        mob_all = np.concatenate([self.mob, np.zeros(len(self.pos) - N, bool)])
        keep = mob_all[i] | mob_all[j]                           # 動かないものどうしは数えない
        i, j = i[keep], j[keep]
        keys = i.astype(np.int64) * len(self.pos) + j
        o = np.argsort(keys)
        i, j, keys = i[o], j[o], keys[o]
        xi = np.zeros(len(keys))
        if len(self.keys):                                      # 接線ばねの伸び（摩擦の履歴）を引きつぐ
            k = np.minimum(np.searchsorted(self.keys, keys), len(self.keys) - 1)
            hit = self.keys[k] == keys
            xi[hit] = self.xi[k[hit]]
        self.i, self.j, self.keys, self.xi = i, j, keys, xi
        im = np.concatenate([np.where(self.mob, 1 / self.m, 0.0), np.zeros(len(self.pos) - N)])
        meff = 1 / np.maximum(im[i] + im[j], 1e-12)
        self.gn = 2 * self.zeta * np.sqrt(self.kn * meff)
        self.gt = 0.5 * self.gn
        self.rsum = self.r[i] + self.r[j]
        self.ri, self.rj = self.r[i], self.r[j]
        self.rr = self.ri * self.rj / self.rsum                  # ころがり抵抗の腕の長さ
        self.pos0 = self.pos[:N].copy()
        self.nbuild += 1

    def forces(self):
        i, j = self.i, self.j
        P, V, Wv = self.pos, self.vel, self.w
        n = len(P)
        dx = P[j, 0] - P[i, 0]
        dy = P[j, 1] - P[i, 1]
        dist = np.sqrt(dx * dx + dy * dy)
        ov = self.rsum - dist
        c = np.nonzero(ov > 0)[0]                                # 触れている組だけ計算する
        i, j, ov, d = i[c], j[c], ov[c], dist[c]
        nx, ny = dx[c] / d, dy[c] / d
        dvx = V[j, 0] - V[i, 0]
        dvy = V[j, 1] - V[i, 1]
        ri, rj = self.ri[c], self.rj[c]
        vn = dvx * nx + dvy * ny
        vt = -dvx * ny + dvy * nx - (Wv[j] * rj + Wv[i] * ri)
        fn = np.maximum(self.kn * ov - self.gn[c] * vn, 0.0)
        xi = self.xi[c] + vt * self.dt
        ft = -self.kt * xi - self.gt[c] * vt
        lim = self.mu * fn
        slip = np.abs(ft) > lim
        ft = np.where(slip, np.sign(ft) * lim, ft)
        xi = np.where(slip, -ft / self.kt, xi)
        xin = np.zeros(len(self.xi))
        xin[c] = xi
        self.xi = xin                                            # 離れた組の履歴は0に戻す
        fx = fn * nx - ft * ny
        fy = fn * ny + ft * nx
        Fx = np.bincount(j, fx, n) - np.bincount(i, fx, n)
        Fy = np.bincount(j, fy, n) - np.bincount(i, fy, n)
        # ころがり抵抗: 相対的な回転を止める向きのトルク（大きさ μr × 腕 × 押す力。ゆっくりな回転は tanh でなめらかに0へ）
        mr = self.mu_r * self.rr[c] * fn * np.tanh((Wv[i] - Wv[j]) / 0.05)
        T = -(np.bincount(i, ft * ri + mr, n) + np.bincount(j, ft * rj - mr, n))
        self._fn, self._fi, self._fj = fn, i, j          # 力の記録用（このあと組を作り直しても使えるように）
        return Fx, Fy, T

    def step(self, drag=0.0):
        N = self.N
        Fx, Fy, T = self.forces()
        dt = self.dt
        mob = self.mob
        v = self.vel[:N]
        v[:, 0] += (Fx[:N] / self.m - drag * v[:, 0]) * dt * mob
        v[:, 1] += (Fy[:N] / self.m - 1.0 - drag * v[:, 1]) * dt * mob
        self.w[:N] += (T[:N] / self.I - drag * self.w[:N]) * dt * mob
        self.pos[:N] += v * dt
        self.t += dt
        d = self.pos[:N] - self.pos0
        if (d[:, 0] ** 2 + d[:, 1] ** 2).max() > (self.skin / 2) ** 2:
            if self.freeze_below is not None:
                self.ncont = (np.bincount(self._fi, minlength=len(self.pos)) +
                              np.bincount(self._fj, minlength=len(self.pos)))[:N]
            self.rebuild()

    def contact_load(self):
        """粒ごとの、受けている法線の力の合計（重さ g×m で割る前）"""
        n = len(self.pos)
        return np.bincount(self._fi, self._fn, n) + np.bincount(self._fj, self._fn, n)


# ---------- 計算 ----------
N_SAND = 10000
N_HALF = 5000
SNAP_DT = 0.5                                      # 粒の位置を残す間隔（√(d/g)）
REC_DT = 1.0                                       # 首の上の力などを残す間隔
PLUG_Y = Y_NECK_TOP + 0.5
FREEZE_Y = -30.0                                   # 下の胴のこの高さより下で止まった粒を凍らせる
RUNS = {"full": (N_SAND, {}), "half": (N_HALF, {}),
        "half_noroll": (N_HALF, {"mu_r": 0.0})}   # 比べるための計算（ころがり抵抗なし）


def initial(n, seed=7):
    """上の胴に、少しすき間をあけた三角格子で並べる（下から n 個）。直径は 0.8〜1.2"""
    rng = np.random.default_rng(seed)
    sp = 1.22
    pts = []
    y, row = PLUG_Y + 1.2, 0
    while y < Y_NECK_TOP + H_BULB - 1.0:
        hw = float(half_width(y)) - 0.95
        if hw > 0:
            xs = np.arange(-hw + (sp / 2 if row % 2 else 0.0), hw, sp)
            pts += [(x, y) for x in xs]
        y += sp * 0.87
        row += 1
    pts = np.array(pts)
    assert len(pts) >= n, f"胴に {len(pts)} 個しか並ばない"
    pts = pts[np.argsort(pts[:, 1], kind="stable")][:n]
    pts = pts + rng.uniform(-0.04, 0.04, pts.shape)
    rad = rng.uniform(0.4, 0.6, n)
    return pts, rad


def settle(n, tag, opts, log=print):
    """栓をした上の胴に粒を入れて、止まるまで待つ（結果は out/ に残し、2回目からは読むだけ）"""
    import pickle
    cache = OUT / f"settled2_{tag}.pkl"
    if cache.exists() and cache.stat().st_size > 0:
        sim = DEM.__new__(DEM)
        with open(cache, "rb") as f:
            sim.__dict__.update(pickle.load(f))
        return sim
    pts, rad = initial(n)
    plug = np.stack([np.arange(-D_NECK / 2 - 0.5, D_NECK / 2 + 0.51, 0.5), np.full(int(D_NECK * 2) + 3, PLUG_Y)], 1)
    wall = wall_disks()
    sim = DEM(pts, rad, np.concatenate([wall, plug]), **opts)
    sim.plug = np.arange(sim.N + len(wall), len(sim.pos))
    k = 0
    while sim.t < 80.0:
        sim.step(drag=1.0 if sim.t < 60 else 0.0)
        k += 1
        if k % 20000 == 0:
            vmax = np.abs(sim.vel[:sim.N]).max()
            log(f"  落ち着かせ {tag} t={sim.t:.1f} vmax={vmax:.3f} 組={len(sim.i)}")
    with open(cache, "wb") as f:
        pickle.dump(sim.__dict__, f)
    return sim


def discharge(tag, log=print):
    n, opts = RUNS[tag]
    sim = settle(n, tag, opts, log)
    surf0 = float(np.percentile(sim.pos[:sim.N, 1], 99.5))     # 砂の面の高さ（上の 0.5% の粒）
    # 栓を抜く
    sim.active[sim.plug] = False
    sim.pos[sim.plug] = 1e6
    sim.keys = np.zeros(0, np.int64)
    sim.freeze_below = FREEZE_Y
    sim.rebuild()
    t0 = sim.t
    sim.t = 0.0
    N = sim.N
    cross = np.full(N, np.nan)
    snaps, snap_t = [], []
    rec = []                                          # (t, 上の胴の粒の数, 首の上の粒の力の平均, 首の上の粒の数)
    next_snap, next_rec = 0.0, 0.0
    t_wall = time.time()
    last_cross = 0.0
    while True:
        if sim.t >= next_snap:
            snaps.append(np.round(sim.pos[:N] * 100).astype(np.int16))
            snap_t.append(sim.t)
            next_snap += SNAP_DT
        sim.step()
        y = sim.pos[:N, 1]
        new = np.isnan(cross) & (y < 0)
        if new.any():
            cross[new] = sim.t
            last_cross = sim.t
        if sim.t >= next_rec:
            load = sim.contact_load()[:N]
            x = sim.pos[:N, 0]
            reg = (np.abs(x) < 12) & (y > 2) & (y < 14)
            rec.append((sim.t, int((y > 0).sum()), float(load[reg].mean() / sim.m[reg].mean()) if reg.any() else 0.0,
                        int(reg.sum())))
            next_rec += REC_DT
            if len(rec) % 25 == 0:
                done = int((~np.isnan(cross)).sum())
                log(f"  {tag} t={sim.t:.0f} 通過 {done}/{N} 経過 {time.time() - t_wall:.0f}秒 組={len(sim.i)} "
                    f"作り直し={sim.nbuild} 凍結={int((~sim.mob).sum())}")
            if np.isnan(cross).any() and sim.t - last_cross > 40:
                log(f"  {tag} 詰まった t={sim.t:.0f}")
                break
        if not np.isnan(cross).any() and sim.t > last_cross + 25:
            break
        if sim.t > 3000:
            break
    np.savez_compressed(OUT / f"dem_{tag}.npz", cross=cross, snaps=np.array(snaps), snap_t=np.array(snap_t),
                        rec=np.array(rec), rad=sim.r[:N], wall=sim.pos[N:N + len(wall_disks())], surf0=surf0,
                        dt=sim.dt, settle_t=t0, kn=sim.kn, mu=sim.mu, mu_r=sim.mu_r)
    log(f"  {tag} おわり t={sim.t:.0f} 計算 {time.time() - t_wall:.0f}秒")


def _job(tag):
    logf = OUT / f"log2_{tag}.txt"

    def log(s):
        with open(logf, "a", encoding="utf-8") as f:
            f.write(s + "\n")
    discharge(tag, log)
    return tag


def compute(which=("full", "half")):
    from concurrent.futures import ProcessPoolExecutor
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=len(which)) as ex:
        for tag in ex.map(_job, which):
            print("できた:", tag)


if __name__ == "__main__" and "--compute" in sys.argv:
    which = [a for a in sys.argv[1:] if a in RUNS] or ["full", "half"]
    t0 = time.time()
    compute(which)
    print(f"計算 {time.time() - t0:.0f}秒")
    sys.exit(0)


# =====================================================================
# ここから下は絵と音（計算の結果 out/sand-dokei/dem_*.npz を読むだけ）
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "10.13"                               # 日付欄（公開予定日）

TAU = math.sqrt(1e-3 / 9.81)                      # 時間の単位 √(d/g)（d=1mm のとき、秒）
THICK_MM = 10.0                                   # 水の容器の奥行き（ml に直すため。2次元の面積 mm² × 10mm）
CD = 0.61                                         # 縮流係数（とがった縁の穴）
Y_OUT = -Y_NECK_TOP                               # 水が出ていく所（首の下端）
Y_TOP = Y_NECK_TOP + H_BULB

# ---------- 計算結果の読み込み ----------
_DEM = {}


def dem(tag):
    if tag not in _DEM:
        f = OUT / f"dem_{tag}.npz"
        if not f.exists():
            raise SystemExit(f"{f} がありません。先に python sims/{SLUG}.py --compute を実行してください")
        z = np.load(f)
        d = {k: z[k] for k in z.files}
        d["cross_s"] = np.sort(d["cross"]) * TAU             # 首を通った時刻（秒・早い順）
        d["snap_s"] = d["snap_t"] * TAU
        _DEM[tag] = d
    return _DEM[tag]


def passed(tag, s):
    """s 秒までに首を通った粒の数"""
    return np.searchsorted(dem(tag)["cross_s"], s, side="right")


def sand_stats(tag):
    d = dem(tag)
    c = d["cross_s"]
    n = len(c)
    t10, t90 = c[int(0.1 * n)], c[int(0.9 * n) - 1]
    return dict(n=n, t_empty=float(c[-1]), rate=0.8 * n / (t90 - t10), t10=float(t10), t90=float(t90))


def rate_window(tag, s0, s1):
    if s1 <= s0:
        return 0.0
    return float(passed(tag, s1) - passed(tag, s0)) / (s1 - s0)


# ---------- 水（トリチェリ） ----------
_WATER = {}


def _area_y():
    ys = np.linspace(Y_OUT, Y_TOP, 6001)
    return ys, 2 * half_width(ys)


def vol_upto(y):
    """上の胴の、首の下端から高さ y までの面積（mm²）"""
    ys, A = _area_y()
    V = np.concatenate([[0], np.cumsum((A[1:] + A[:-1]) / 2 * np.diff(ys))])
    return np.interp(y, ys, V)


def level_of_vol(v):
    ys, A = _area_y()
    V = np.concatenate([[0], np.cumsum((A[1:] + A[:-1]) / 2 * np.diff(ys))])
    return np.interp(v, V, ys)


def torricelli(A_of_y, h0, a):
    """水面が h0 から穴（Y_OUT）まで下がる時刻表。dV/dt = −CD·a·√(2g(y−Y_OUT))、V' = A(y)。
    t(y) = ∫ A/(CD a √(2(y'−Y_OUT))) dy' を u = √(y'−Y_OUT) で置きかえて（特異点が消える）台形則で積分。
    返り値: 水面の高さ（u の順＝低い順）と、その高さになる時刻（秒）"""
    u = np.linspace(0, math.sqrt(h0 - Y_OUT), 4001)
    yy = Y_OUT + u * u
    f = 2 * A_of_y(yy) / (CD * a * math.sqrt(2))
    tu = np.concatenate([[0], np.cumsum((f[1:] + f[:-1]) / 2 * np.diff(u))])
    return yy, (tu[-1] - tu) * TAU


def water(fill_frac=1.0):
    """水時計。砂と同じ高さまで入れた量 ×fill_frac。穴の幅は「はじめの1秒に落ちる割合」が砂（1万粒）と同じになる幅。
    返り値: 穴の幅（d）、はじめの量（mm²）、水位の時刻表（秒）"""
    if fill_frac in _WATER:
        return _WATER[fill_frac]
    st = sand_stats("full")
    h_full = float(dem("full")["surf0"])
    V_full = float(vol_upto(h_full))
    frac_rate = st["rate"] / st["n"]                         # 砂が1秒に落ちる割合（はじめの量に対して）
    a = frac_rate * V_full * TAU / (CD * math.sqrt(2 * (h_full - Y_OUT)))   # d 単位（1τ あたりの量で合わせる）
    V0 = V_full * fill_frac
    h0 = float(level_of_vol(V0))
    yy, t_of_y = torricelli(lambda y: 2 * half_width(y), h0, a)
    out = dict(a=a, V0=V0, h0=h0, t_empty=float(t_of_y[0]), y=yy[::-1], t=t_of_y[::-1])
    _WATER[fill_frac] = out
    return out


def water_level(s, fill_frac=1.0):
    w = water(fill_frac)
    return float(np.interp(s, w["t"], w["y"]))


def water_flow(y, fill_frac=1.0):
    """水面が y のときの流量（mm²/秒）"""
    w = water(fill_frac)
    return CD * w["a"] * math.sqrt(2 * max(0.0, y - Y_OUT)) / TAU


def ml(area_mm2):
    return area_mm2 * THICK_MM / 1000


# ---------- 照合に使う値 ----------

_SHOWN = None


def shown():
    global _SHOWN
    if _SHOWN is None:
        _SHOWN = _shown()
    return _SHOWN


def _shown():
    st = sand_stats("full")
    sh = sand_stats("half")
    w1, w2 = water(1.0), water(0.5)
    c = dem("full")["cross_s"]
    n = len(c)
    # 砂: 前半（10〜40%が落ちたころ）と後半（60〜90%）の速さ
    r_a = 0.3 * n / (c[int(0.4 * n)] - c[int(0.1 * n)])
    r_b = 0.3 * n / (c[int(0.9 * n)] - c[int(0.6 * n)])
    # 水: 同じ区間（量の 10〜40% と 60〜90% が出ていく間）
    def t_water_frac(fr):
        y = level_of_vol(w1["V0"] * (1 - fr))
        return float(np.interp(y, w1["y"][::-1], w1["t"][::-1]))
    wr_a = 0.3 / (t_water_frac(0.4) - t_water_frac(0.1))
    wr_b = 0.3 / (t_water_frac(0.9) - t_water_frac(0.6))
    return dict(n=n, rate=st["rate"], t_sand=st["t_empty"], t_sand_half=sh["t_empty"], n_half=sh["n"],
                t_water=w1["t_empty"], t_water_half=w2["t_empty"], sand_ratio_ab=r_b / r_a, water_ratio_ab=wr_b / wr_a,
                half_sand=sh["t_empty"] / st["t_empty"], half_water=w2["t_empty"] / w1["t_empty"],
                ml0=ml(w1["V0"]), a_w=w1["a"], q0=water_flow(w1["h0"]), rate_half=sh["rate"])


# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_FLIP = 0.75                                     # 0秒目から、砂時計をひっくり返す
T_FALL = 0.28                                     # ひっくり返したあと、天井側の砂が首まで落ちる（絵）
T_START = T_FLIP + T_FALL                         # ここから計算の t=0（栓を抜いた瞬間）
SLOW = 0.10                                       # 冒頭（カウントの間）はゆっくり（0.1倍）
RACE = 0.6                                        # くらべる間（0.6倍。実際の速さだと砂は6秒ほどで落ちきる）
FAST = 1.6                                        # 砂が空になったあと、水の残りを早送り
BIG_Q = ["砂時計、砂が減ると", "速く落ちているように感じる？"]   # 2026-10-12 v3 ユーザー案（2行）
DETAIL = "砂1万粒の砂時計と、水時計でくらべる"
LABELS = ["本当に速くなる", "気のせい", "本当は遅くなる"]   # B は「気のせい（同じ速さ）」だと1列に収まらないので短く
CORRECT = 1                                       # 下の answer_by_rule() で計算結果から決め、ずれたら止める
ANSWER_TOL = 0.06                                 # 答えを決める規則（計算する前に決めた）: 砂の後半（6〜9割が落ちる間）の速さ÷前半（1〜4割）が
                                                  # 1.06 より大きければ A 本当に速くなる、0.94 より小さければ C 本当は遅くなる、その間なら B 気のせい（同じ速さ）


def answer_by_rule(ratio):
    if ratio > 1 + ANSWER_TOL:
        return 0
    if ratio < 1 - ANSWER_TOL:
        return 2
    return 1

TL = None                                         # 再生の時刻表（setup で作る）


def setup():
    """データから時間割を決める"""
    global TL, T_RACE_END, T_G0, T_REV, T_ST2, T_TW, T_TW_RUN, T_TW_END, T_VAL, T_Q, DURATION, TW_SPEED
    sh = shown()
    t_s, t_w = sh["t_sand"], sh["t_water"]
    ts = np.arange(0, 40, 1 / 600)
    S = np.zeros_like(ts)
    s = 0.0
    phase_fast = None
    for k in range(1, len(ts)):
        t = ts[k]
        if t < T_START:
            sp = 0.0
        elif t < T_GO:
            sp = SLOW
        elif s < t_s + 0.25:
            sp = SLOW + (RACE - SLOW) * ease((t - T_GO) / 0.6)
        else:
            if phase_fast is None:
                phase_fast = t
            sp = RACE + (FAST - RACE) * ease((t - phase_fast) / 0.3)
        if s >= t_w:
            sp = 0.0
        s = min(t_w, s + sp / 600)
        S[k] = s
    t_end = ts[np.argmax(S >= t_w - 1e-9)]
    TL = dict(t=ts, S=S, t_fast=phase_fast, t_end=float(t_end))
    T_RACE_END = float(t_end) + 0.6
    T_G0 = T_RACE_END                             # グラフ
    T_REV = T_G0 + 2.0                            # 三択の答え
    T_ST2 = T_REV + 0.3
    T_TW = T_ST2 + 2.6                            # ひねり
    T_TW_RUN = T_TW + 2.95
    TW_SPEED = t_w / 2.4                          # 棒は 2.4秒で伸びきる（早送り）
    T_TW_END = T_TW_RUN + 2.4
    T_VAL = T_TW_END + 0.3
    T_Q = T_VAL + 3.4                             # 締め
    DURATION = T_Q + 4.0


def S_of(t):
    return float(np.interp(t, TL["t"], TL["S"]))


# ---------- 絵: 砂時計 ----------
SAND_COLS = ["#e3b65c", "#d9a64a", "#efcd85", "#c99a45", "#f2d999"]
WATER_COL = "#8ec5ee"
WATER_D = "#4f8fc6"
WOOD, WOOD_D = "#c99a66", "#a87a48"
GLASS_TINT = "#d9ecf7"

_POLY = {}


def polys():
    """砂時計の内側（全体）・上の胴・下の胴の多角形（砂時計の座標、上が正）"""
    if not _POLY:
        P = profile()
        lowR = (P * [1, -1])[::-1]                         # 下の胴の右半分（底の中央 → 首）
        right = np.concatenate([lowR[:-2], P])              # 底の中央 → 首 → 天井の中央
        full = np.concatenate([right, (right * [-1, 1])[::-1][1:-1]])
        upper = np.concatenate([P, (P * [-1, 1])[::-1][1:-1]])
        _POLY["full"] = full
        _POLY["upper"] = upper
        _POLY["lower"] = upper * [1, -1]
        # 外側のガラスの線（法線の向きに 2.2 ずらす）
        g = np.gradient(np.concatenate([full[-1:], full, full[:1]]), axis=0)[1:-1]
        nrm = np.stack([g[:, 1], -g[:, 0]], 1)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        # 向き（時計回りか）をそろえて外へ
        cx = full[:, 0].mean()
        sgn = 1.0 if np.mean((full[:, 0] - cx) * nrm[:, 0]) > 0 else -1.0
        _POLY["outer"] = full + 2.2 * sgn * nrm
    return _POLY


class Glass:
    """砂時計1つの置き場所。(cx, cy) は首の中心の画面座標、s は 1d あたりの px、ang は回転（0＝正立）"""

    def __init__(self, cx, cy, s, ang=0.0):
        self.cx, self.cy, self.s, self.ang = cx, cy, s, ang

    def xy(self, x, y):
        c, sn = math.cos(self.ang), math.sin(self.ang)
        X = x * c - y * sn
        Y = x * sn + y * c
        return self.cx + X * self.s, self.cy - Y * self.s

    def path(self, ctx, pts, close=True):
        X, Y = self.xy(pts[:, 0], pts[:, 1])
        ctx.move_to(X[0], Y[0])
        for x, y in zip(X[1:], Y[1:]):
            ctx.line_to(x, y)
        if close:
            ctx.close_path()


def draw_frame(ctx, g, a=1.0, back=True):
    """木の台・柱・ガラス（ペン描き）。back=True はガラスの地（中身より先に描く）、False は線（中身のあと）"""
    if a <= 0:
        return
    p = polys()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if back:
        # ガラスの地（外の線の内側をうすい水色）
        g.path(ctx, p["outer"])
        ctx.set_source_rgba(*hexrgb(GLASS_TINT, 0.55 * a))
        ctx.fill()
        g.path(ctx, p["full"])
        ctx.set_source_rgba(*hexrgb("#fbfdff", 0.75 * a))
        ctx.fill()
        return
    # ガラスの線
    for key, wdt, al in (("outer", 3.2, 0.95), ("full", 2.2, 0.55)):
        g.path(ctx, p[key])
        ctx.set_source_rgba(*hexrgb(INK, al * a))
        ctx.set_line_width(wdt)
        ctx.stroke()
    # 光の筋
    hl = np.array([(-B_BODY / 2 + 9, Y_TOP - 22), (-B_BODY / 2 + 9, Y_TOP - 62)])
    for sy in (1, -1):
        g.path(ctx, hl * [1, sy], close=False)
        ctx.set_source_rgba(1, 1, 1, 0.9 * a)
        ctx.set_line_width(max(2.0, g.s * 1.6))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # 柱
    for sx in (-1, 1):
        x0 = sx * (B_BODY / 2 + 7)
        post = np.array([(x0 - 1.6, -Y_TOP - 3), (x0 + 1.6, -Y_TOP - 3), (x0 + 1.6, Y_TOP + 3), (x0 - 1.6, Y_TOP + 3)])
        g.path(ctx, post)
        ctx.set_source_rgba(*hexrgb(WOOD_D, a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(2.2)
        ctx.stroke()
    # 上下の台
    for sy in (1, -1):
        y0, y1 = sy * (Y_TOP + 2.5), sy * (Y_TOP + 11)
        plate = np.array([(-B_BODY / 2 - 12, y0), (B_BODY / 2 + 12, y0), (B_BODY / 2 + 12, y1), (-B_BODY / 2 - 12, y1)])
        g.path(ctx, plate)
        ctx.set_source_rgba(*hexrgb(WOOD, a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.95 * a))
        ctx.set_line_width(3.0)
        ctx.stroke()


_SAND_IDX = None


def snap_pos(tag, s):
    """s 秒の粒の位置（砂時計の座標）。残した位置のあいだは直線でつなぐ"""
    d = dem(tag)
    k = s / TAU / SNAP_DT
    n = len(d["snaps"])
    if k >= n - 1:
        return d["snaps"][-1].astype(float) / 100
    i = int(k)
    f = k - i
    p0 = d["snaps"][i].astype(float)
    if f < 1e-6:
        return p0 / 100
    return (p0 * (1 - f) + d["snaps"][i + 1].astype(float) * f) / 100


def draw_sand(ctx, g, pos, rad, a=1.0):
    global _SAND_IDX
    if a <= 0:
        return
    if _SAND_IDX is None or len(_SAND_IDX) != len(rad):
        rng = np.random.default_rng(11)
        _SAND_IDX = rng.integers(0, len(SAND_COLS), len(rad))
    X, Y = g.xy(pos[:, 0], pos[:, 1])
    R = np.maximum(0.9, rad * g.s * 1.05)
    for ci, col in enumerate(SAND_COLS):
        sel = np.nonzero(_SAND_IDX == ci)[0]
        ctx.set_source_rgba(*hexrgb(col, a))
        for x, y, r in zip(X[sel], Y[sel], R[sel]):
            ctx.move_to(x + r, y)
            ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()


def clip_poly(poly, nx, ny, c):
    """多角形のうち nx*x + ny*y <= c の側（サザーランド・ホジマン）"""
    out = []
    n = len(poly)
    for k in range(n):
        p, q = poly[k], poly[(k + 1) % n]
        dp, dq = nx * p[0] + ny * p[1] - c, nx * q[0] + ny * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp <= 0) != (dq <= 0):
            u = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u))
    return np.array(out) if out else np.zeros((0, 2))


def area(poly):
    if len(poly) < 3:
        return 0.0
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def draw_water_poly(ctx, g, poly, a):
    if len(poly) < 3 or a <= 0:
        return
    g.path(ctx, poly)
    ctx.set_source_rgba(*hexrgb(WATER_COL, 0.9 * a))
    ctx.fill()


def draw_water(ctx, g, s, a=1.0, fill_frac=1.0):
    """水時計の中身。回っている間（冒頭）は、水面が画面の水平を保つように面積を合わせて切る"""
    if a <= 0:
        return
    p = polys()
    w = water(fill_frac)
    if abs(g.ang) > 1e-4:
        # 重力の向き（画面の下）を砂時計の座標に直す: 画面の下 = (sin ang, -cos ang)・・・ 水は「下」側にたまる
        c, sn = math.cos(g.ang), math.sin(g.ang)
        nx, ny = sn, c                                   # 上向き（画面の上）の単位ベクトルを砂時計の座標で
        up = p["upper"]
        proj = up[:, 0] * nx + up[:, 1] * ny
        lo, hi = proj.min(), proj.max()
        for _ in range(40):
            mid = (lo + hi) / 2
            if area(clip_poly(up, nx, ny, mid)) < w["V0"]:
                lo = mid
            else:
                hi = mid
        draw_water_poly(ctx, g, clip_poly(up, nx, ny, hi), a)
        return
    y = water_level(s, fill_frac)
    draw_water_poly(ctx, g, clip_poly(p["upper"], 0.0, 1.0, y), a)
    # 下の胴にたまった分
    out = w["V0"] - float(vol_upto(y))
    if out > 1:
        lo_poly = p["lower"]
        ylo, yhi = -Y_TOP, -Y_NECK_TOP
        for _ in range(40):
            mid = (ylo + yhi) / 2
            if area(clip_poly(lo_poly, 0.0, 1.0, mid)) < out:
                ylo = mid
            else:
                yhi = mid
        yl = yhi
        draw_water_poly(ctx, g, clip_poly(lo_poly, 0.0, 1.0, yl), a)
        # 水面の線（ペン）
        hw = float(half_width(-yl))
        x0, y0 = g.xy(-hw + 0.5, yl)
        x1, y1 = g.xy(hw - 0.5, yl)
        ctx.set_source_rgba(*hexrgb(WATER_D, 0.8 * a))
        ctx.set_line_width(2.0)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.stroke()
    else:
        yl = -Y_TOP
    if y > Y_OUT + 0.05:
        # 上の水面の線
        hw = float(half_width(y))
        x0, y0 = g.xy(-hw + 0.5, y)
        x1, y1 = g.xy(hw - 0.5, y)
        ctx.set_source_rgba(*hexrgb(WATER_D, 0.8 * a))
        ctx.set_line_width(2.0)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.stroke()
        # 落ちる水の筋（太さは流量に合わせる。細すぎると見えないので最低2px）
        q = water_flow(y, fill_frac)
        q0 = water_flow(w["h0"], fill_frac)
        wpx = 1.6 + 4.0 * q / max(q0, 1e-9)
        xa, ya = g.xy(0.0, Y_OUT)
        xb, yb = g.xy(0.0, yl)
        ctx.set_source_rgba(*hexrgb(WATER_D, 0.85 * a))
        ctx.set_line_width(wpx)
        ctx.move_to(xa, ya)
        ctx.line_to(xb, yb)
        ctx.stroke()


def draw_orifice(ctx, g, a=1.0):
    """水時計の首の板（穴を細くしてある）"""
    if a <= 0:
        return
    aw = water(1.0)["a"]
    for sx in (-1, 1):
        x_in, x_out = sx * aw / 2, sx * (D_NECK / 2 + 0.6)
        plate = np.array([(x_in, -0.6), (x_out, -0.6), (x_out, 0.6), (x_in, 0.6)])
        g.path(ctx, plate)
        ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
        ctx.fill()


# ---------- 置き場所 ----------
L_INTRO = dict(sand=(310.0, 1067.0, 2.2), water=(850.0, 1067.0, 2.2))   # 問いが2行なので少し小さく下げた
L_RACE = dict(sand=(330.0, 925.0, 1.95), water=(810.0, 925.0, 1.95))


def flip_angle(t):
    if t >= T_FLIP:
        return 0.0
    return math.pi * (1 - ease_out(t / T_FLIP))


def glass_at(kind, t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    (x0, y0, s0), (x1, y1, s1) = L_INTRO[kind], L_RACE[kind]
    bounce = 0.0
    if T_FLIP <= t < T_FLIP + 0.45:                 # 置いたときに少しはねる
        u = (t - T_FLIP) / 0.45
        bounce = -10 * math.sin(math.pi * u) * (1 - u)
    return Glass(x0 + (x1 - x0) * m, y0 + (y1 - y0) * m + bounce, s0 + (s1 - s0) * m, flip_angle(t))


def glasses_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


_PRE = None


def intro_sand(t):
    """冒頭の0〜T_START秒の砂（絵。計算ではない）。0秒目は「落ちきった砂時計」＝計算の最後の山を上下さかさまに置き、
    ひっくり返すあいだは砂ごと回す。回り終えたら、天井側にある砂を、計算のはじめの形（首の上にたまった形）へ落とす。
    落とすときは、低い順に並べた粒どうしを結ぶ（かたまりのまま下がって見える）"""
    global _PRE
    d = dem("full")
    if _PRE is None:
        fin = d["snaps"][-1].astype(float) / 100
        pre = -fin                                           # 180°回す（砂時計の座標で）
        start = d["snaps"][0].astype(float) / 100
        o_pre, o_st = np.argsort(pre[:, 1]), np.argsort(start[:, 1])
        src = np.empty_like(start)
        src[o_st] = pre[o_pre]                               # 粒 o_st[k] は、さかさまの山の下から k 番目の場所から落ちる
        _PRE = (src, start)
    src, start = _PRE
    if t < T_FLIP:
        return src
    u = clamp01((t - T_FLIP) / T_FALL) ** 2                  # 重力で落ちるように、だんだん速く
    return src + (start - src) * u


def draw_glasses(ctx, t, a=1.0):
    if a <= 0:
        return
    s = S_of(t)
    d = dem("full")
    gs = glass_at("sand", t)
    gw = glass_at("water", t)
    for g in (gs, gw):
        draw_frame(ctx, g, a, back=True)
    draw_sand(ctx, gs, intro_sand(t) if t < T_START else snap_pos("full", s), d["rad"], a)
    draw_water(ctx, gw, s, a)
    draw_orifice(ctx, gw, a)
    for g in (gs, gw):
        draw_frame(ctx, g, a, back=False)
    # 冒頭: 下の胴に名前（ひっくり返したあと）
    if t < T_GO:
        la = ease_out((t - T_FLIP - 0.15) / 0.3) * (1 - ease((t - T_MOVE + 0.2) / 0.3))
        if la > 0:
            for g, big, small in ((gs, "砂", "1万粒"), (gw, "水", "")):
                x, y = g.xy(-30.0, -95.0)
                text(ctx, big, x, y, 50, INK, alpha=la)
                if small:
                    text(ctx, small, x, y + 52, 32, INK, bold=False, alpha=la)


# ---------- 読み取り（シミュの間） ----------

def sand_rate_live(s):
    if s <= 0.05:
        return 0.0
    w = min(0.4, s)
    return rate_window("full", s - w, s)


def fmt(n):
    return f"{int(round(n)):,}"


def draw_readouts(ctx, t, a):
    if a <= 0 or t < T_GO - 0.1:
        return
    s = S_of(t)
    sh = shown()
    b = a * ease_out((t - T_GO + 0.1) / 0.4)
    gs, gw = glass_at("sand", t), glass_at("water", t)
    xs, xw = gs.cx, gw.cx
    n_left = sh["n"] - int(passed("full", s))
    r = sand_rate_live(s) if n_left > 0 else 0.0
    w = water(1.0)
    y = water_level(s)
    left_ml = ml(max(0.0, float(vol_upto(y))))
    q = ml(water_flow(y)) if y > Y_OUT + 0.01 else 0.0
    for x, head, rate_s, left_s, col in ((xs, "砂 1万粒", f"{fmt(round(r, -1))}粒", f"残り {fmt(n_left)}粒", "#a0701c"),
                                         (xw, f"水 {ml(w['V0']):.0f}ml", f"{q:.1f}ml", f"残り {left_ml:.1f}ml", WATER_D)):
        text(ctx, head, x, 1282, 34, INK, alpha=b)
        text(ctx, "1秒に落ちる量", x, 1324, 26, PENCIL, bold=False, alpha=b)
        text(ctx, rate_s, x, 1368, 46, col, alpha=b)
        text(ctx, left_s, x, 1420, 28, INK, bold=False, alpha=b)
    # 真ん中: 経過時間
    xm = (xs + xw) / 2
    text(ctx, "経過", xm, 760, 30, PENCIL, bold=False, alpha=b)
    text(ctx, f"{s:.1f}秒", xm, 808, 46, INK, alpha=b)
    if t >= T_GO and t < T_G0:
        fast = TL["t_fast"] is not None and t >= TL["t_fast"]
        text(ctx, f"再生 {FAST if fast else RACE:.1f}倍", xm, 858, 28, RED if fast else PENCIL, bold=False,
             alpha=b * ease_out((t - T_GO) / 0.3))
    if s >= sh["t_sand"] and t < T_G0 + 0.3:
        fa = b * ease_out((t - t_of_S(sh["t_sand"])) / 0.25)
        note.sticky(ctx, "砂は空に", xm, 990, 30, "yellow", a=fa, tilt=-0.03)
    if s >= sh["t_water"] - 1e-6 and t < T_G0 + 0.3:
        fa = b * ease_out((t - TL["t_end"]) / 0.25)
        note.sticky(ctx, "水も空に", xm, 1090, 30, "blue", a=fa, tilt=0.03)


def t_of_S(s):
    return float(np.interp(s, TL["S"], TL["t"]))


# ---------- 1秒ごとの棒: 落ちる速さ ----------
# 2026-10-12 v2: 折れ線（はじめ＝100）は、砂が空になった所で線が縦に0へ落ち、ぱっと見「急に遅くなった」に見えた（ユーザー指摘）。
# 1秒ごとの棒に置きかえる。砂は空になるまでの「まるまる1秒」だけ棒にし、最後の半端な1秒は棒にせず「空」と書く。
# 砂・水とも、1本目の棒を同じ高さにそろえる（くらべやすいように）。
BAR_X0 = 205.0                                    # 1本目の棒の中心
BAR_DX = 82.0                                     # 棒の間隔（1秒ぶん）
BAR_W = 56.0
BAR_H1 = 190.0                                    # 1本目の棒の高さ
PANELS = (("sand", 890.0), ("water", 1255.0))     # 棒の下端の y
BAR_STEP = 0.18                                   # 棒を1本ずつ出す間隔（動画の秒）
BAR_T0 = 0.45


def per_second():
    """1秒ごとの落ちた量: 砂（粒）と水（ml）。空になる前の、まるまる1秒だけ"""
    sh = shown()
    sand = [int(passed("full", k + 1) - passed("full", k)) for k in range(int(sh["t_sand"]))]
    w = water(1.0)
    left = lambda s: ml(float(vol_upto(water_level(s))))
    wat = [left(k) - left(k + 1) for k in range(int(w["t_empty"]))]
    return sand, wat


def bar_cx(k):
    return BAR_X0 + k * BAR_DX


def draw_rate_bars(ctx, t, a):
    if a <= 0:
        return
    sand, wat = per_second()
    for kind, base in PANELS:
        vals = sand if kind == "sand" else wat
        col, ink = ("#e3b65c", "#a0701c") if kind == "sand" else (WATER_COL, WATER_D)
        head = "砂　1秒に落ちた粒" if kind == "sand" else "水　1秒に落ちた量（ml）"
        text(ctx, head, BAR_X0 - BAR_W / 2, base - BAR_H1 - 78, 32, ink, align="left", alpha=a)
        # 1本目の高さのうすい点線（同じ高さか、低くなっていくかが一目で分かるように）
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
        ctx.set_line_width(2.0)
        ctx.set_dash([8, 8])
        ctx.move_to(BAR_X0 - BAR_W / 2 - 6, base - BAR_H1)
        ctx.line_to(bar_cx(8) + BAR_W / 2 + 4, base - BAR_H1)
        ctx.stroke()
        ctx.set_dash([])
        note.pen_line(ctx, BAR_X0 - BAR_W / 2 - 12, base + 2, bar_cx(8) + BAR_W / 2 + 8, base + 2, INK, seed=4,
                      width=4, alpha=0.85 * a)
        for k in range(9):
            tk = T_G0 + BAR_T0 + k * BAR_STEP
            if t < tk:
                break
            g = ease_out((t - tk) / 0.25)
            x = bar_cx(k)
            if k < len(vals):
                h = BAR_H1 * vals[k] / vals[0] * g
                ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
                core.rrect(ctx, x - BAR_W / 2, base - h, BAR_W, h, 5)
                ctx.fill_preserve()
                ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
                ctx.set_line_width(2.5)
                ctx.stroke()
                lab = f"{vals[k]:,}" if kind == "sand" else f"{vals[k]:.1f}"
                text(ctx, lab, x, base - h - 22, 25, ink, alpha=a * g)
            elif k == len(vals):
                text(ctx, "空", x, base - 34, 34, PENCIL, alpha=a * g)
            text(ctx, f"{k + 1}", x, base + 26, 24, PENCIL, bold=False, alpha=a)


# ---------- ひねり: 半分にしたら ----------
BX0 = 300.0
BX_LEN = 560.0                                    # いちばん長い棒（水 100ml）の長さ


def bx(sec):
    return BX0 + sec / shown()["t_water"] * BX_LEN


def draw_bars(ctx, t, a, dim=1.0):
    if a <= 0:
        return
    sh = shown()
    tl = max(0.0, t - T_TW_RUN) * TW_SPEED            # 早送りの時計（秒）
    rows = [("砂", [("1万粒", sh["t_sand"]), ("5千粒", sh["t_sand_half"])], 790, "#e3b65c", "#a0701c"),
            ("水", [(f"{sh['ml0']:.0f}ml", sh["t_water"]), (f"{sh['ml0'] / 2:.0f}ml", sh["t_water_half"])], 1050,
             WATER_COL, WATER_D)]
    for head, bars, y0, col, ink in rows:
        text(ctx, head, 150, y0 - 70, 46, ink, alpha=a)
        for k, (lab, T) in enumerate(bars):
            y = y0 + k * 82
            text(ctx, lab, BX0 - 20, y, 34, INK, align="right", alpha=a)
            cur = min(tl, T)
            if cur > 0:
                ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
                core.rrect(ctx, BX0, y - 24, bx(cur) - BX0, 48, 6)
                ctx.fill_preserve()
                ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
                ctx.set_line_width(2.5)
                ctx.stroke()
                done = tl >= T
                text(ctx, f"{cur:.1f}秒", bx(cur) - 12, y, 32, INK if not done else ink, align="right", alpha=a)
        # 半分の線
        if t >= T_VAL:
            b = ease_out((t - T_VAL) / 0.3) * a
            xh = bx(bars[0][1] / 2)
            ctx.set_source_rgba(*hexrgb(RED, 0.8 * b))
            ctx.set_line_width(3)
            ctx.set_dash([9, 8])
            ctx.move_to(xh, y0 - 40)
            ctx.line_to(xh, y0 + 82 + 40)
            ctx.stroke()
            ctx.set_dash([])
            text(ctx, "半分", xh, y0 + 82 + 64, 28, RED, alpha=b)


def draw_bar_notes(ctx, t, a):
    if a <= 0 or t < T_VAL:
        return
    sh = shown()
    b1 = ease_out((t - T_VAL - 0.4) / 0.3) * a
    b2 = ease_out((t - T_VAL - 1.3) / 0.3) * a
    word = "ちょうど半分" if abs(sh["half_sand"] - 0.5) < 0.015 else "ほぼ半分"
    note.sticky(ctx, f"砂は {word}（{sh['half_sand'] * 100:.0f}%）", 600, 650, 36, "yellow", a=b1, tilt=-0.02)
    note.sticky(ctx, f"水は 半分にならない（{sh['half_water'] * 100:.0f}%）", 590, 1290, 36, "blue", a=b2, tilt=0.02)


# ---------- 冒頭・上のブロック ----------

def choice_row(labels, size, cx, max_w, gap=72):
    """三択を横1列に並べる位置: [(中身, 左端の x, 字の大きさ)]。全体の幅が max_w を超えたら字を小さくする"""
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


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問いの1行・前提・三択（横1列）。その下いっぱいに、砂時計と水時計を0秒目からひっくり返す。
    予想して！とカウントは2つのあいだ"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 60
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for k, (line, y) in enumerate(zip(BIG_Q, (408, 480))):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 522, 575 + w2 / 2 + 6, 516, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 562, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 38, 575, 860, gap=48)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 626, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 626, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 626, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            note.hand_text(ctx, "予想して！", cx, cy - 128, 42, RED, seed=41, alpha=a2, align="center")
            fill(ctx, (*hexrgb(PAPER)[:3], 0.92 * a))
            ctx.arc(cx, cy, 64, 0, 2 * math.pi)
            ctx.fill()
            note.pen_circle(ctx, cx, cy, 62, 60, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 92, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        """冒頭が終わったあと、上に小さく: 問い2行・下線・三択を横1列。答えは赤丸、ほかは取り消し線"""
        sz = 44
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 850:
            sz *= 850 / w
        text(ctx, BIG_Q[0], 540, 400, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 452, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 483, 540 + w2 / 2 + 6, 480, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 534
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840, gap=48)):
            ok = i == self.correct
            al = m * (1 - 0.55 * rev * (not ok))
            vw = core.text_width(v, vs)
            note.pen_circle(ctx, x0 + 25, y, 25, 25, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 25, y, 33, INK, alpha=al)
            text(ctx, v, x0 + 58, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
            if ok:
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7, progress=rev)
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


CD_X, CD_Y = 580.0, 1050.0
INTRO = SIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    sh = shown()
    ga = glasses_alpha(t)
    draw_glasses(ctx, t, ga)
    draw_readouts(ctx, t, ga)
    if T_GO - 0.1 <= t < T_GO + 1.6:                 # シミュの合図
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.2) / 0.4))
        note.sticky(ctx, "スタート", 570, 640, 34, "yellow", a=b, tilt=-0.03)
    # グラフ
    if t >= T_G0:
        a = ease((t - T_G0 - 0.2) / 0.4) * (1 - ease((t - T_TW) / 0.35))
        draw_rate_bars(ctx, t, a)
        if t >= T_ST2:
            b = ease_out((t - T_ST2) / 0.3) * (1 - ease((t - T_TW) / 0.3))
            note.sticky(ctx, "砂は ずっと同じ速さ", 580, 1378, 38, "pink", fg=RED, a=b, tilt=-0.02)
    # ひねり
    if t >= T_TW:
        if t < T_TW_RUN:
            ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.2) / 0.2))
            note.banner(ctx, "砂を半分にしたら、時間は？", 575, 800, a=ba, t_rel=t - T_TW, size=48)
        else:
            a = ease_out((t - T_TW_RUN) / 0.3)
            if t >= T_Q:
                a *= 1 - 0.75 * ease_out((t - T_Q) / 0.35)
            draw_bars(ctx, t, a)
            if t < T_Q + 0.35:
                draw_bar_notes(ctx, t, a * (1 - ease_out((t - T_Q) / 0.35)) if t >= T_Q else a)
    # 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで砂は、減っても\n速くならないの？", 580, 780, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 580, 990, 48, "pink", fg=RED, a=r, tilt=0.025)
        if t >= T_Q + 1.8:
            text(ctx, "（ベバルーの法則）", 580, 1110, 32, PENCIL, bold=False, alpha=ease_out((t - T_Q - 1.8) / 0.3))


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    body(ctx, t)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def band_noise(dur, lo, hi, seed, rms, edge_lo=400.0, edge_hi=1500.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def build_audio():
    sh = shown()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 293.7, 349.2)), 1.0, bgm=True)
    # 砂の「さー」と水の「ちょろちょろ」。強さは、動画の1秒あたりに落ちる量に合わせる
    tt = np.arange(int(SR * DURATION)) / SR
    Sv = np.interp(tt, TL["t"], TL["S"])
    spd = np.gradient(Sv, tt)
    sand_on = (Sv > 0) & (Sv < sh["t_sand"]) & (tt < T_G0 + 0.3)
    hiss = band_noise(DURATION, 2500.0, 9000.0, 3, 0.022)
    env_s = np.where(sand_on, np.clip(0.35 + 0.65 * spd, 0, 1.2), 0.0)
    env_s = np.convolve(env_s, np.ones(2400) / 2400, mode="same")
    mx.add(0, hiss * env_s, 1.0, bgm=True)
    wl = np.array([water_level(s) for s in Sv[::480]])
    qn = np.array([water_flow(y) for y in wl]) / max(1e-9, water_flow(water(1.0)["h0"]))
    qn = np.interp(tt, tt[::480], qn) * (tt < T_G0 + 0.3) * (Sv > 0)
    trick = band_noise(DURATION, 300.0, 1800.0, 4, 0.02, 200.0, 600.0)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 7.3 * tt) * np.sin(2 * np.pi * 2.1 * tt)
    env_w = np.convolve(np.clip(qn * (0.4 + 0.6 * np.minimum(spd, 1.5)), 0, 1.3), np.ones(2400) / 2400, mode="same")
    mx.add(0, trick * mod * env_w, 1.0, bgm=True)
    # ひっくり返す
    mx.add(0.0, whoosh(0.7), 0.35)
    mx.add(T_FLIP, thump(), 0.55)
    mx.add(T_START - 0.02, thump(), 0.3)                    # 砂が首に落ちた
    INTRO.audio(mx)
    # シミュ
    mx.add(T_GO - 0.6, riser(0.8), 0.45)
    t_sand_end = t_of_S(sh["t_sand"])
    beat(mx, T_GO, t_sand_end, bpm=120, vol=0.45)
    s = 1.0
    while s < sh["t_water"]:
        mx.add(t_of_S(s), tick(2400.0, 0.03), 0.08)        # 1秒ごとに時計の音
        s += 1.0
    mx.add(t_sand_end, bell(784.0, 1.2), 0.45)
    mx.add(TL["t_end"], blip(659.3, 0.2), 0.4)
    # グラフと答え
    for k in range(9):                                       # 棒が1本出るごとに（砂・水そろって）
        mx.add(T_G0 + BAR_T0 + k * BAR_STEP, blip(523.3 + 40 * k, 0.1), 0.25)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST2, blip(659.3, 0.15), 0.35)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.45)
    beat(mx, T_TW_RUN, T_TW_END, bpm=140, vol=0.45)
    for T, f0 in ((sh["t_sand_half"], 880.0), (sh["t_sand"], 784.0), (sh["t_water_half"], 698.5), (sh["t_water"], 587.3)):
        mx.add(T_TW_RUN + T / TW_SPEED, blip(f0, 0.18), 0.4)
    mx.add(T_VAL, thump(), 0.6)
    mx.add(T_VAL + 0.4, bell(1046.5, 1.4), 0.45)
    mx.add(T_VAL + 1.3, bell(880.0, 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def beverloo_2d(D, k=1.4, C=1.0):
    """2次元のベバルーの式の形（流量 ∝ (D − k d)^{3/2}）。比をとって使う"""
    return C * (D - k) ** 1.5


def run_checks():
    sh = shown()
    d, dh = dem("full"), dem("half")
    checks = []
    # (1) 全粒が首を通った（詰まらずに落ちきった）
    checks.append(("1万粒がすべて首を通った", float(np.isfinite(d["cross"]).sum()), float(N_SAND), 0.0))
    checks.append(("5千粒がすべて首を通った", float(np.isfinite(dh["cross"]).sum()), float(N_HALF), 0.0))
    # (2) 砂の速さは前半と後半で同じ（答え B）
    checks.append(("砂: 後半（60〜90%）の速さ ÷ 前半（10〜40%）", sh["sand_ratio_ab"], 1.0, 0.06))
    # (3) 水は遅くなる（同じ区間で比べる）。トリチェリの式なので後半はかなり遅い
    checks.append(("水: 後半の速さ ÷ 前半 が 0.85 より小さい（はっきり遅くなる）", float(sh["water_ratio_ab"] < 0.85), 1.0, 0.0))
    # (4) 1万粒と5千粒で、落ちる速さ（1秒あたりの粒数）が同じ（高さによらない）
    checks.append(("砂: 5千粒の速さ ÷ 1万粒の速さ", sh["rate_half"] / sh["rate"], 1.0, 0.06))
    # (5) ひねり: 砂を半分 → 時間もほぼ半分。水は半分にならない（6割以上）
    checks.append(("ひねり: 砂の時間の比（5千粒 ÷ 1万粒）", sh["half_sand"], 0.5, 0.04))
    checks.append(("ひねり: 水の時間の比 が 0.6 より大きい", float(sh["half_water"] > 0.6), 1.0, 0.0))
    # (6) 水の式: まっすぐな胴（幅一定）なら閉じた式 T = A/(CD a)·√(2h0)。同じ積分の関数がこれと一致する
    for h0 in (40.0, 120.0):
        _, tt = torricelli(lambda y: np.full_like(y, 100.0), h0, 2.0)
        exact = 100.0 / (CD * 2.0) * math.sqrt(2 * (h0 - Y_OUT)) * TAU
        checks.append((f"トリチェリの積分（幅一定・高さ{h0:.0f}）が閉じた式と一致（秒）", float(tt[0]), exact, 1e-6))
    # (7) 水の「はじめの1秒に落ちる割合」が砂と同じ（そうなるように穴の幅を決めた）
    w1 = water(1.0)
    checks.append(("水のはじめの割合 ÷ 砂の割合", water_flow(w1["h0"]) / w1["V0"] / (sh["rate"] / sh["n"]), 1.0, 1e-6))
    checks.append(("画面の答え（三択の番号）が、決めておいた規則で計算結果から出した答えと同じ",
                   float(answer_by_rule(sh["sand_ratio_ab"])), float(INTRO.correct), 0.0))
    check_answers(checks)


def report():
    sh = shown()
    d = dem("full")
    rec = d["rec"]
    print(f"長さ={DURATION:.1f}秒  砂の速さ {sh['rate']:.0f}粒/秒  空になる {sh['t_sand']:.2f}秒  5千粒 {sh['t_sand_half']:.2f}秒"
          f"（比 {sh['half_sand']:.3f}、速さ {sh['rate_half']:.0f}粒/秒）")
    print(f"砂 後半÷前半 {sh['sand_ratio_ab']:.3f}   水 後半÷前半 {sh['water_ratio_ab']:.3f}")
    print(f"水 {sh['ml0']:.1f}ml 穴の幅 {sh['a_w']:.2f}mm  空になる {sh['t_water']:.2f}秒  半分 {sh['t_water_half']:.2f}秒（比 {sh['half_water']:.3f}）")
    print(f"砂の面の高さ {float(d['surf0']):.1f}  dt={float(d['dt']):.5f}")
    if len(rec):
        for frac in (0.9, 0.7, 0.5, 0.3, 0.15):
            k = int(np.argmin(np.abs(rec[:, 1] - frac * sh["n"])))
            print(f"  上の胴に {rec[k, 1]:.0f}粒 のとき: 首の上の粒が受ける力の平均 = 重さの {rec[k, 2]:.2f}倍（{rec[k, 3]:.0f}粒）")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.6, 0.85, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 15.5, T_G0 + 0.8, T_G0 + 1.6, T_G0 + 2.5, T_REV + 1.0,
              T_TW + 1.0, T_TW_RUN + 1.2, T_VAL + 1.5, T_Q + 0.5, T_Q + 2.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
